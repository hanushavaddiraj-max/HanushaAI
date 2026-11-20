"""FraudShield investigation tools (parameterized SQL over UC tables)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field, field_validator

from .config import (
  gold_table,
  investigation_view,
  max_rows,
  predictions_table,
)
from .rag_client import retrieve_knowledge, retrieve_knowledge_json
from .sql_client import rows_to_json, run_sql

logger = logging.getLogger(__name__)


def _as_str(value: Any) -> str:
  """LLMs often pass numeric ids as ints; coerce to string for SQL tools."""
  if value is None:
    raise ValueError('id cannot be null')
  return str(value).strip()


class HighRiskInput(BaseModel):
  min_score: float = Field(default=0.9, description='Minimum fraud_score threshold (0-1)')
  limit: int = Field(default=20, description='Max rows to return (capped)')
  batch_hours: Optional[int] = Field(
    default=None,
    description='If set, only include scores from the last N hours',
  )


class TransactionIdInput(BaseModel):
  transaction_id: str = Field(description='Transaction id to investigate (string or number)')

  @field_validator('transaction_id', mode='before')
  @classmethod
  def _coerce_txn(cls, v: Any) -> str:
    return _as_str(v)


class CustomerHistoryInput(BaseModel):
  client_id: str = Field(description='Customer / client id (string or number)')
  limit: int = Field(default=25, description='Max historical transactions')

  @field_validator('client_id', mode='before')
  @classmethod
  def _coerce_client(cls, v: Any) -> str:
    return _as_str(v)


class ClientIdInput(BaseModel):
  client_id: str = Field(description='Customer / client id (string or number)')

  @field_validator('client_id', mode='before')
  @classmethod
  def _coerce_client(cls, v: Any) -> str:
    return _as_str(v)


class RiskEvidenceInput(BaseModel):
  transaction_id: str = Field(description='Transaction id (string or number)')

  @field_validator('transaction_id', mode='before')
  @classmethod
  def _coerce_txn(cls, v: Any) -> str:
    return _as_str(v)


class ReportInput(BaseModel):
  transaction_id: str = Field(description='Transaction id for the investigation report')
  analyst_notes: str = Field(
    default='',
    description='Optional analyst notes to include in the report draft',
  )

  @field_validator('transaction_id', mode='before')
  @classmethod
  def _coerce_txn(cls, v: Any) -> str:
    return _as_str(v)


class ReviewInput(BaseModel):
  transaction_id: str = Field(description='Transaction id')
  status: str = Field(
    description='open | in_review | cleared | confirmed_fraud | escalated',
  )
  analyst_notes: str = Field(default='', description='Analyst notes')
  agent_report: str = Field(default='', description='Optional agent summary to store')
  analyst_email: str = Field(default='analyst@example.com', description='Analyst email')

  @field_validator('transaction_id', mode='before')
  @classmethod
  def _coerce_txn(cls, v: Any) -> str:
    return _as_str(v)


class KnowledgeQueryInput(BaseModel):
  query: str = Field(
    description=(
      'Natural language question about investigation policy, HITL statuses, '
      'MCC/amount heuristics, or report-writing SOP'
    )
  )
  k: int = Field(default=5, description='Max passages to return (1-10)')


def _cap(limit: int) -> int:
  return max(1, min(int(limit), max_rows()))


def get_high_risk_transactions(
  min_score: float = 0.9,
  limit: int = 20,
  batch_hours: Optional[int] = None,
) -> str:
  """Return highest-risk scored transactions from the latest prediction history."""
  try:
    lim = _cap(limit)
    params = {'min_score': float(min_score), 'limit': lim}
    time_filter = ''
    if batch_hours is not None:
      # Literal int only (validated) — avoids INTERVAL bind issues across warehouses
      hours = max(1, min(int(batch_hours), 24 * 30))
      time_filter = f'AND scored_at >= current_timestamp() - INTERVAL {hours} HOURS'

    sql = f"""
    SELECT
      transaction_id,
      fraud_score,
      predicted_fraud,
      model_version,
      scored_at,
      client_id,
      card_id,
      amount,
      mcc,
      merchant_state
    FROM {investigation_view()}
    WHERE fraud_score >= :min_score
    {time_filter}
    ORDER BY fraud_score DESC
    LIMIT :limit
    """
    try:
      rows = run_sql(sql, params=params)
    except Exception:
      sql_fb = f"""
      SELECT transaction_id, fraud_score, prediction AS predicted_fraud,
             model_version, scored_at, amount, mcc
      FROM {predictions_table()}
      WHERE fraud_score >= :min_score
      {time_filter}
      ORDER BY fraud_score DESC
      LIMIT :limit
      """
      rows = run_sql(sql_fb, params=params)
    return rows_to_json(rows, limit=lim)
  except Exception as e:
    logger.exception('get_high_risk_transactions failed')
    return f'Error: {e}'


def get_transaction_details(transaction_id: str) -> str:
  """Get gold transaction details for a transaction id."""
  try:
    transaction_id = _as_str(transaction_id)
    sql = f"""
    SELECT *
    FROM {gold_table()}
    WHERE transaction_id = :transaction_id
    LIMIT 1
    """
    rows = run_sql(sql, params={'transaction_id': transaction_id})
    if not rows:
      return f'No gold transaction found for transaction_id={transaction_id}'
    return rows_to_json(rows, limit=1)
  except Exception as e:
    logger.exception('get_transaction_details failed')
    return f'Error: {e}'


def get_model_prediction_metadata(transaction_id: str) -> str:
  """Get ML prediction metadata (score, model version, scored_at) for a transaction."""
  try:
    transaction_id = _as_str(transaction_id)
    sql = f"""
    SELECT transaction_id, fraud_score, prediction, model_version, scored_at, is_fraud
    FROM {predictions_table()}
    WHERE transaction_id = :transaction_id
    ORDER BY scored_at DESC
    LIMIT 5
    """
    rows = run_sql(sql, params={'transaction_id': transaction_id})
    if not rows:
      return f'No predictions found for transaction_id={transaction_id}'
    return rows_to_json(rows, limit=5)
  except Exception as e:
    logger.exception('get_model_prediction_metadata failed')
    return f'Error: {e}'


def get_customer_transaction_history(client_id: str, limit: int = 25) -> str:
  """Get recent transactions for a customer from gold."""
  try:
    client_id = _as_str(client_id)
    lim = _cap(limit)
    sql = f"""
    SELECT transaction_id, card_id, amount, transaction_hour, mcc, use_chip,
           merchant_state, is_fraud
    FROM {gold_table()}
    WHERE client_id = :client_id
    ORDER BY transaction_id DESC
    LIMIT :limit
    """
    rows = run_sql(sql, params={'client_id': client_id, 'limit': lim})
    return rows_to_json(rows, limit=lim)
  except Exception as e:
    logger.exception('get_customer_transaction_history failed')
    return f'Error: {e}'


def get_customer_risk_profile(client_id: str) -> str:
  """Aggregate customer risk signals from predictions joined to gold."""
  try:
    client_id = _as_str(client_id)
    sql = f"""
    SELECT
      g.client_id,
      COUNT(*) AS scored_tx_count,
      AVG(p.fraud_score) AS avg_fraud_score,
      MAX(p.fraud_score) AS max_fraud_score,
      SUM(CASE WHEN p.prediction = 1 OR p.prediction = true THEN 1 ELSE 0 END) AS predicted_fraud_count
    FROM {predictions_table()} p
    JOIN {gold_table()} g ON p.transaction_id = g.transaction_id
    WHERE g.client_id = :client_id
    GROUP BY g.client_id
    """
    rows = run_sql(sql, params={'client_id': client_id})
    if not rows:
      return f'No risk profile found for client_id={client_id}'
    return rows_to_json(rows, limit=1)
  except Exception as e:
    logger.exception('get_customer_risk_profile failed')
    return f'Error: {e}'


def get_transaction_risk_evidence(transaction_id: str) -> str:
  """Collect evidence fields that support risk review (not proof of fraud)."""
  try:
    transaction_id = _as_str(transaction_id)
    sql = f"""
    SELECT
      COALESCE(v.transaction_id, p.transaction_id) AS transaction_id,
      p.fraud_score,
      p.prediction AS predicted_fraud,
      p.model_version,
      p.scored_at,
      g.amount,
      g.transaction_hour,
      g.mcc,
      g.use_chip,
      g.credit_limit,
      g.credit_score,
      g.yearly_income,
      g.merchant_state,
      CASE WHEN g.yearly_income > 0 THEN abs(g.amount) / g.yearly_income END AS amount_to_income_ratio,
      CASE WHEN g.credit_limit > 0 THEN abs(g.amount) / g.credit_limit END AS amount_to_credit_limit_ratio,
      CASE WHEN g.transaction_hour < 6 OR g.transaction_hour >= 22 THEN true ELSE false END AS is_night_like
    FROM {predictions_table()} p
    LEFT JOIN {gold_table()} g ON p.transaction_id = g.transaction_id
    LEFT JOIN {investigation_view()} v ON v.transaction_id = p.transaction_id
    WHERE p.transaction_id = :transaction_id
    ORDER BY p.scored_at DESC
    LIMIT 1
    """
    try:
      rows = run_sql(sql, params={'transaction_id': transaction_id})
    except Exception:
      # Simpler fallback without view
      sql_fb = f"""
      SELECT p.transaction_id, p.fraud_score, p.prediction AS predicted_fraud,
             p.model_version, p.scored_at, g.amount, g.transaction_hour, g.mcc,
             g.use_chip, g.credit_limit, g.credit_score, g.yearly_income, g.merchant_state
      FROM {predictions_table()} p
      LEFT JOIN {gold_table()} g ON p.transaction_id = g.transaction_id
      WHERE p.transaction_id = :transaction_id
      ORDER BY p.scored_at DESC
      LIMIT 1
      """
      rows = run_sql(sql_fb, params={'transaction_id': transaction_id})
    if not rows:
      return f'No evidence found for transaction_id={transaction_id}'
    note = {
      'disclaimer': (
        'These fields are risk indicators from available data and ML score only. '
        'They do not prove fraud. A human analyst must decide.'
      ),
      'evidence': rows[0],
    }
    return rows_to_json([note], limit=1)
  except Exception as e:
    logger.exception('get_transaction_risk_evidence failed')
    return f'Error: {e}'


def retrieve_investigation_knowledge(query: str, k: int = 5) -> str:
  """Retrieve investigation playbook / policy passages (RAG). Not for transaction facts."""
  try:
    return retrieve_knowledge_json(query, k=k)
  except Exception as e:
    logger.exception('retrieve_investigation_knowledge failed')
    return f'Error: {e}'


def generate_investigation_report(transaction_id: str, analyst_notes: str = '') -> str:
  """Assemble a structured investigation report draft from tools/data."""
  try:
    transaction_id = _as_str(transaction_id)
    details = get_transaction_details(transaction_id)
    pred = get_model_prediction_metadata(transaction_id)
    evidence = get_transaction_risk_evidence(transaction_id)
    policy = retrieve_knowledge(
      f'investigation checklist report writing HITL before confirmed_fraud {transaction_id}',
      k=2,
    )
    report = {
      'title': 'FraudShield Investigation Report (Draft)',
      'transaction_id': transaction_id,
      'generated_at': datetime.now(timezone.utc).isoformat(),
      'transaction_information': details,
      'ml_prediction': pred,
      'historical_risk_indicators': evidence,
      'policy_context': {
        'sources': policy.get('sources', []),
        'passages': policy.get('passages', []),
        'note': 'Policy snippets from playbooks; not proof of fraud.',
      }
      if policy.get('hit')
      else {'sources': [], 'passages': [], 'note': 'No policy passages retrieved.'},
      'analyst_notes': analyst_notes or None,
      'recommendations_for_human_review': [
        'Verify customer contact / recent travel if amount is unusual',
        'Compare against customer historical spend pattern',
        'Confirm merchant category risk and channel (online vs chip)',
        'Do not block card or mark confirmed fraud without analyst approval',
      ],
      'disclaimer': 'Agent-generated draft. Not an automated enforcement action.',
    }
    return rows_to_json([report], limit=1)
  except Exception as e:
    logger.exception('generate_investigation_report failed')
    return f'Error: {e}'


def record_investigation_review(
  transaction_id: str,
  status: str,
  analyst_notes: str = '',
  agent_report: str = '',
  analyst_email: str = 'analyst@example.com',
) -> str:
  """Record HITL investigation status. Does not perform financial enforcement."""
  allowed = {'open', 'in_review', 'cleared', 'confirmed_fraud', 'escalated'}
  status_norm = (status or '').strip().lower()
  if status_norm not in allowed:
    return f'Invalid status. Allowed: {sorted(allowed)}'
  try:
    transaction_id = _as_str(transaction_id)
    from .config import catalog, fraudshield_schema

    table = f'{catalog()}.{fraudshield_schema()}.investigation_reviews'
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    review_id = str(uuid.uuid4())
    sql = f"""
    INSERT INTO {table} (
      review_id, transaction_id, analyst_email, status, analyst_notes,
      agent_report, mlflow_trace_id, created_at, updated_at
    ) VALUES (
      :review_id, :transaction_id, :analyst_email, :status, :analyst_notes,
      :agent_report, NULL, :created_at, :updated_at
    )
    """
    run_sql(
      sql,
      params={
        'review_id': review_id,
        'transaction_id': transaction_id,
        'analyst_email': analyst_email,
        'status': status_norm,
        'analyst_notes': analyst_notes,
        'agent_report': agent_report,
        'created_at': now,
        'updated_at': now,
      },
    )
    return rows_to_json(
      [{'review_id': review_id, 'transaction_id': transaction_id, 'status': status_norm}],
      limit=1,
    )
  except Exception as e:
    logger.exception('record_investigation_review failed')
    return (
      f'Error recording review (create table via sql/01_investigation_views.sql first): {e}'
    )


def create_catalog_tools() -> List:
  """Backward-compatible factory name used by agent.py — returns fraud tools."""
  return create_fraud_tools()


def create_fraud_tools() -> List:
  """Create FraudShield investigation tools."""
  return [
    StructuredTool.from_function(
      func=get_high_risk_transactions,
      name='get_high_risk_transactions',
      description=(
        'List highest-risk transactions from ML prediction history. '
        'Use for questions about high fraud probability / latest risky batch.'
      ),
      args_schema=HighRiskInput,
    ),
    StructuredTool.from_function(
      func=get_transaction_details,
      name='get_transaction_details',
      description='Get full gold transaction details for a transaction_id.',
      args_schema=TransactionIdInput,
    ),
    StructuredTool.from_function(
      func=get_model_prediction_metadata,
      name='get_model_prediction_metadata',
      description='Get fraud score, model version, and scored_at for a transaction_id.',
      args_schema=TransactionIdInput,
    ),
    StructuredTool.from_function(
      func=get_customer_transaction_history,
      name='get_customer_transaction_history',
      description='Get recent transaction history for a client_id.',
      args_schema=CustomerHistoryInput,
    ),
    StructuredTool.from_function(
      func=get_customer_risk_profile,
      name='get_customer_risk_profile',
      description='Aggregate risk profile for a client_id from scored predictions.',
      args_schema=ClientIdInput,
    ),
    StructuredTool.from_function(
      func=get_transaction_risk_evidence,
      name='get_transaction_risk_evidence',
      description=(
        'Collect risk evidence for a transaction (score + amount/time/MCC/income ratios). '
        'Does not prove fraud.'
      ),
      args_schema=RiskEvidenceInput,
    ),
    StructuredTool.from_function(
      func=retrieve_investigation_knowledge,
      name='retrieve_investigation_knowledge',
      description=(
        'RAG over investigation playbooks: checklist, HITL status meanings, '
        'MCC/amount heuristics, report-writing SOP. '
        'Use for policy/procedure questions — NOT for live transaction scores or ids.'
      ),
      args_schema=KnowledgeQueryInput,
    ),
    StructuredTool.from_function(
      func=generate_investigation_report,
      name='generate_investigation_report',
      description='Generate a structured investigation report draft for human review.',
      args_schema=ReportInput,
    ),
    StructuredTool.from_function(
      func=record_investigation_review,
      name='record_investigation_review',
      description=(
        'Record analyst HITL decision/status for a transaction. '
        'Never use this to auto-block cards.'
      ),
      args_schema=ReviewInput,
    ),
  ]
