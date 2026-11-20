"""Chunk FraudShield knowledge Markdown into UC Delta + Vector Search (managed embeddings).

Default path:
  1) Write id/source/title/text to dev.fraudshield.knowledge_chunks (CDF on)
  2) Create/sync Delta Sync index with Databricks-managed embeddings (databricks-gte-large-en)

Examples:
  python ingest_knowledge.py --knowledge-dir ../knowledge
  python ingest_knowledge.py --knowledge-dir ../knowledge --skip-vector-search
  python ingest_knowledge.py --knowledge-dir ../knowledge --warehouse-id 852a24c1d2cc3003
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def _chunk_markdown(text: str, source: str, max_chars: int = 900) -> List[Dict[str, str]]:
  """Split markdown on headings into retrieval-sized chunks."""
  parts = re.split(r'\n(?=#{1,3}\s)', text.strip())
  chunks: List[Dict[str, str]] = []
  title = Path(source).stem.replace('_', ' ').title()
  for part in parts:
    part = part.strip()
    if not part:
      continue
    heading = title
    m = re.match(r'^(#{1,3})\s+(.+)', part)
    if m:
      heading = m.group(2).strip()
    buf = part
    while buf:
      piece = buf[:max_chars]
      if len(buf) > max_chars:
        cut = piece.rfind('\n')
        if cut > max_chars // 2:
          piece = piece[:cut]
      buf = buf[len(piece) :].lstrip()
      cid = hashlib.sha1(f'{source}:{heading}:{piece[:80]}'.encode()).hexdigest()[:16]
      chunks.append({'id': cid, 'source': source, 'title': heading, 'text': piece})
  return chunks


def _load_knowledge(knowledge_dir: Path) -> List[Dict[str, str]]:
  rows: List[Dict[str, str]] = []
  for path in sorted(knowledge_dir.glob('*.md')):
    rows.extend(_chunk_markdown(path.read_text(encoding='utf-8'), path.name))
  return rows


def _sql_escape(value: str) -> str:
  return "'" + value.replace("'", "''") + "'"


def _write_with_spark(rows: List[Dict[str, Any]], table: str) -> None:
  from pyspark.sql import SparkSession

  spark = SparkSession.builder.getOrCreate()
  schema_name = table.rsplit('.', 1)[0]
  spark.sql(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
  df = spark.createDataFrame(rows)
  (
    df.write.mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable(table)
  )
  spark.sql(
    f"ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
  )
  print(f'Wrote {len(rows)} chunks to {table} (Spark + CDF)')


def _run_sql_warehouse(w, warehouse_id: str, statement: str, wait: str = '50s') -> Any:
  result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=statement,
    wait_timeout=wait,
  )
  status = getattr(result, 'status', None)
  state = str(getattr(status, 'state', '') or '')
  if 'FAILED' in state.upper():
    err = getattr(status, 'error', None)
    raise RuntimeError(f'SQL failed: {err or state}')
  return result


def _write_with_warehouse(w, rows: List[Dict[str, str]], table: str, warehouse_id: str) -> None:
  schema_name = table.rsplit('.', 1)[0]
  _run_sql_warehouse(w, warehouse_id, f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
  _run_sql_warehouse(
    w,
    warehouse_id,
    f"""
    CREATE TABLE IF NOT EXISTS {table} (
      id STRING NOT NULL,
      source STRING NOT NULL,
      title STRING,
      text STRING NOT NULL
    ) USING DELTA
    TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """,
  )
  # Overwrite via delete + insert (small corpus)
  _run_sql_warehouse(w, warehouse_id, f'DELETE FROM {table}')
  for row in rows:
    stmt = f"""
    INSERT INTO {table} (id, source, title, text) VALUES (
      {_sql_escape(row['id'])},
      {_sql_escape(row['source'])},
      {_sql_escape(row['title'])},
      {_sql_escape(row['text'])}
    )
    """
    _run_sql_warehouse(w, warehouse_id, stmt)
  _run_sql_warehouse(
    w,
    warehouse_id,
    f'ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)',
  )
  print(f'Wrote {len(rows)} chunks to {table} (SQL warehouse + CDF)')


def _wait_endpoint_online(vsc, endpoint_name: str, timeout_s: int = 900) -> None:
  deadline = time.time() + timeout_s
  while time.time() < deadline:
    try:
      ep = vsc.get_endpoint(endpoint_name)
      # SDK object shapes vary
      raw = str(ep)
      state = ''
      if hasattr(ep, 'endpoint_status'):
        state = str(getattr(ep.endpoint_status, 'state', '') or '')
      if not state and isinstance(ep, dict):
        state = str(ep.get('endpoint_status', {}).get('state', ''))
      print(f'  endpoint state={state or raw[:120]}')
      if 'ONLINE' in (state or raw).upper():
        return
    except Exception as e:
      print(f'  waiting for endpoint: {e}')
    time.sleep(15)
  raise TimeoutError(f'Vector Search endpoint {endpoint_name} not ONLINE within {timeout_s}s')


def _vector_search_client():
  """Build VS client with PAT/host (CLI OAuth profile alone is not enough for ai-search)."""
  from databricks.sdk import WorkspaceClient
  from databricks.vector_search.client import VectorSearchClient

  w = WorkspaceClient()
  host = (w.config.host or os.getenv('DATABRICKS_HOST') or '').rstrip('/')
  token = w.config.token or os.getenv('DATABRICKS_TOKEN')
  if host and token:
    return VectorSearchClient(
      workspace_url=host if host.startswith('http') else f'https://{host}',
      personal_access_token=token,
      disable_notice=True,
    )
  # Last resort: env-only
  env_host = (os.getenv('DATABRICKS_HOST') or '').rstrip('/')
  env_token = os.getenv('DATABRICKS_TOKEN')
  if env_host and env_token:
    return VectorSearchClient(
      workspace_url=env_host if env_host.startswith('http') else f'https://{env_host}',
      personal_access_token=env_token,
      disable_notice=True,
    )
  raise RuntimeError(
    'Vector Search client needs DATABRICKS_HOST + DATABRICKS_TOKEN '
    '(databricks-cli OAuth profile is not accepted by VectorSearchClient).'
  )


def _ensure_managed_vector_search(
  *,
  endpoint_name: str,
  table: str,
  index_name: str,
  embedding_model: str,
) -> None:
  vsc = _vector_search_client()

  try:
    vsc.get_endpoint(endpoint_name)
    print(f'Vector Search endpoint exists: {endpoint_name}')
  except Exception:
    print(f'Creating Vector Search endpoint: {endpoint_name} (STANDARD — billed while online)')
    vsc.create_endpoint(name=endpoint_name, endpoint_type='STANDARD')

  _wait_endpoint_online(vsc, endpoint_name)

  try:
    idx = vsc.get_index(endpoint_name, index_name)
    print(f'Index exists, syncing: {index_name}')
    try:
      idx.sync()
    except Exception as e:
      print(f'sync note: {e}')
  except Exception:
    print(
      f'Creating managed-embedding Delta Sync index {index_name} '
      f'on {table} text via {embedding_model}'
    )
    vsc.create_delta_sync_index(
      endpoint_name=endpoint_name,
      index_name=index_name,
      source_table_name=table,
      pipeline_type='TRIGGERED',
      primary_key='id',
      embedding_source_column='text',
      embedding_model_endpoint_name=embedding_model,
    )
    # Wait briefly then sync
    time.sleep(20)
    try:
      vsc.get_index(endpoint_name, index_name).sync()
    except Exception as e:
      print(f'initial sync note: {e}')

  # Wait until index reports ready-ish
  for i in range(40):
    try:
      idx = vsc.get_index(endpoint_name, index_name)
      desc = idx.describe() if hasattr(idx, 'describe') else str(idx)
      blob = json.dumps(desc, default=str) if not isinstance(desc, str) else desc
      print(f'  index status check {i + 1}: {blob[:200]}')
      if any(s in blob.upper() for s in ('ONLINE', 'READY', 'ACTIVE')):
        break
    except Exception as e:
      print(f'  index wait: {e}')
    time.sleep(15)


def main(argv: Optional[List[str]] = None) -> int:
  parser = argparse.ArgumentParser(
    description='Ingest FraudShield knowledge into UC + managed Vector Search'
  )
  parser.add_argument(
    '--knowledge-dir',
    default=str(Path(__file__).resolve().parents[1] / 'knowledge'),
    help='Directory of .md playbooks',
  )
  parser.add_argument('--skip-vector-search', action='store_true')
  parser.add_argument(
    '--warehouse-id',
    default=os.getenv('DATABRICKS_SQL_WAREHOUSE_ID', ''),
    help='SQL warehouse id for non-Spark writes',
  )
  args = parser.parse_args(argv)

  catalog = os.getenv('FRAUD_CATALOG', 'dev')
  schema = os.getenv('FRAUDSHIELD_SCHEMA', 'fraudshield')
  table = f'{catalog}.{schema}.knowledge_chunks'
  embedding_model = os.getenv('FRAUDSHIELD_EMBEDDING_ENDPOINT', 'databricks-gte-large-en')
  vs_endpoint = os.getenv('FRAUDSHIELD_VS_ENDPOINT', 'fraudshield-vs')
  index_name = os.getenv('FRAUDSHIELD_VS_INDEX', f'{catalog}.{schema}.knowledge_vs_index')

  knowledge_dir = Path(args.knowledge_dir)
  if not knowledge_dir.is_dir():
    print(f'Knowledge dir not found: {knowledge_dir}', file=sys.stderr)
    return 1

  chunks = _load_knowledge(knowledge_dir)
  if not chunks:
    print('No markdown chunks found', file=sys.stderr)
    return 1
  print(f'Loaded {len(chunks)} chunks from {knowledge_dir}')

  from databricks.sdk import WorkspaceClient

  w = WorkspaceClient()

  rows: List[Dict[str, Any]] = list(chunks)
  wrote = False
  try:
    _write_with_spark(rows, table)
    wrote = True
  except Exception as spark_err:
    print(f'Spark write unavailable ({spark_err}); trying SQL warehouse...')
    if not args.warehouse_id:
      print(
        'Set --warehouse-id or DATABRICKS_SQL_WAREHOUSE_ID for warehouse writes.',
        file=sys.stderr,
      )
      return 1
    _write_with_warehouse(w, rows, table, args.warehouse_id)
    wrote = True

  if not wrote:
    return 1

  if args.skip_vector_search:
    print('Skipping Vector Search index creation.')
    return 0

  _ensure_managed_vector_search(
    endpoint_name=vs_endpoint,
    table=table,
    index_name=index_name,
    embedding_model=embedding_model,
  )
  print('Ingest complete.')
  print(f'  table={table}')
  print(f'  endpoint={vs_endpoint}')
  print(f'  index={index_name}')
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
