"""Safe Databricks SQL execution for FraudShield tools."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from .auth import get_workspace_client
from .config import warehouse_id

logger = logging.getLogger(__name__)

_SAFE_IDENT = re.compile(r'^[A-Za-z0-9_\.]+$')


def _resolve_warehouse_id(w) -> str:
  env_id = warehouse_id()
  if env_id:
    return env_id

  # Prefer a running warehouse; otherwise first available.
  warehouses = list(w.warehouses.list())
  if not warehouses:
    raise RuntimeError(
      'No SQL warehouse found. Create one in Databricks SQL and set DATABRICKS_SQL_WAREHOUSE_ID.'
    )
  running = [wh for wh in warehouses if getattr(wh, 'state', None) and str(wh.state).endswith('RUNNING')]
  chosen = running[0] if running else warehouses[0]
  wid = chosen.id
  if not wid:
    raise RuntimeError('Could not resolve a SQL warehouse id.')
  return wid


def _escape_literal(value: Any) -> str:
  if value is None:
    return 'NULL'
  if isinstance(value, bool):
    return 'TRUE' if value else 'FALSE'
  if isinstance(value, (int, float)) and not isinstance(value, bool):
    return str(value)
  text = str(value)
  text = text.replace("'", "''")
  return f"'{text}'"


def validate_identifier(name: str, label: str = 'identifier') -> str:
  if not name or not _SAFE_IDENT.match(name):
    raise ValueError(f'Invalid {label}: {name!r}')
  return name


def run_sql(statement: str, *, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
  """Execute a single SQL statement with simple named parameter substitution.

  Only values in `params` are escaped as literals. Table/column identifiers must be
  validated by the caller before interpolation into the statement template.
  """
  sql = statement
  if params:
    for key, value in params.items():
      sql = sql.replace(f':{key}', _escape_literal(value))

  w = get_workspace_client()
  wid = _resolve_warehouse_id(w)
  logger.info('Executing FraudShield SQL on warehouse %s', wid)

  # wait_timeout max is 50s for sync path in many workspaces
  result = w.statement_execution.execute_statement(
    warehouse_id=wid,
    statement=sql,
    wait_timeout=os.getenv('DATABRICKS_SQL_WAIT_TIMEOUT', '50s'),
  )

  status = getattr(result, 'status', None)
  state = getattr(status, 'state', None) if status else None
  state_name = str(state) if state is not None else ''
  if state_name and 'FAILED' in state_name.upper():
    err = getattr(status, 'error', None)
    raise RuntimeError(f'SQL failed: {err or state_name}')

  manifest = getattr(result, 'manifest', None)
  schema = getattr(manifest, 'schema', None) if manifest else None
  columns = []
  if schema and getattr(schema, 'columns', None):
    columns = [c.name for c in schema.columns]

  data = getattr(result, 'result', None)
  data_array = getattr(data, 'data_array', None) if data else None
  if not data_array:
    return []

  rows: List[Dict[str, Any]] = []
  for raw in data_array:
    # SDK may return list of values or objects with .data
    values = list(raw) if not hasattr(raw, 'data') else list(raw.data)
    if columns:
      rows.append({columns[i]: values[i] if i < len(values) else None for i in range(len(columns))})
    else:
      rows.append({f'c{i}': v for i, v in enumerate(values)})
  return rows


def rows_to_json(rows: List[Dict[str, Any]], *, limit: int) -> str:
  clipped = rows[:limit]
  payload = {
    'row_count': len(clipped),
    'truncated': len(rows) > limit,
    'rows': clipped,
  }
  return json.dumps(payload, default=str, indent=2)
