"""FraudShield schema / warehouse configuration."""

from __future__ import annotations

import os


def catalog() -> str:
  return os.getenv('FRAUD_CATALOG', 'dev')


def gold_schema() -> str:
  return os.getenv('GOLD_SCHEMA', 'fraud_gold')


def ml_schema() -> str:
  return os.getenv('ML_SCHEMA', 'fraud_ml')


def fraudshield_schema() -> str:
  return os.getenv('FRAUDSHIELD_SCHEMA', 'fraudshield')


def gold_table() -> str:
  return f'{catalog()}.{gold_schema()}.transactions_enriched'


def predictions_table() -> str:
  return f'{catalog()}.{ml_schema()}.fraud_predictions'


def investigation_view() -> str:
  """Prefer curated view; tools fall back to join if view missing."""
  return f'{catalog()}.{fraudshield_schema()}.v_investigation_cases'


def warehouse_id() -> str | None:
  return os.getenv('DATABRICKS_SQL_WAREHOUSE_ID') or None


def max_rows() -> int:
  try:
    return max(1, min(int(os.getenv('FRAUD_TOOL_MAX_ROWS', '50')), 200))
  except ValueError:
    return 50


def knowledge_chunks_table() -> str:
  return f'{catalog()}.{fraudshield_schema()}.knowledge_chunks'


def vs_endpoint() -> str | None:
  return os.getenv('FRAUDSHIELD_VS_ENDPOINT') or None


def vs_index() -> str | None:
  return os.getenv('FRAUDSHIELD_VS_INDEX') or None


def embedding_endpoint() -> str:
  return os.getenv('FRAUDSHIELD_EMBEDDING_ENDPOINT', 'databricks-gte-large-en')
