-- FraudShield investigation views (run in Databricks SQL Editor against catalog `dev`)
-- Prerequisite: fraud_predictions and transactions_enriched already exist from MLOps workshop.

CREATE SCHEMA IF NOT EXISTS dev.fraudshield
COMMENT 'FraudShield AI investigation objects (agent + HITL)';

-- Latest prediction per transaction joined to gold context
CREATE OR REPLACE VIEW dev.fraudshield.v_investigation_cases AS
SELECT
  p.transaction_id,
  p.fraud_score,
  p.prediction AS predicted_fraud,
  p.model_version,
  p.scored_at,
  p.is_fraud AS label_is_fraud,
  g.client_id,
  g.card_id,
  g.amount,
  g.transaction_hour,
  g.mcc,
  g.use_chip,
  g.merchant_state,
  g.credit_limit,
  g.credit_score,
  g.yearly_income,
  g.current_age,
  g.num_cards_issued
FROM (
  SELECT *
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY transaction_id
        ORDER BY scored_at DESC
      ) AS rn
    FROM dev.fraud_ml.fraud_predictions
  )
  WHERE rn = 1
) p
LEFT JOIN dev.fraud_gold.transactions_enriched g
  ON p.transaction_id = g.transaction_id;

-- Human-in-the-loop investigation outcomes (agent never auto-writes enforcement actions)
CREATE TABLE IF NOT EXISTS dev.fraudshield.investigation_reviews (
  review_id STRING NOT NULL,
  transaction_id STRING NOT NULL,
  analyst_email STRING,
  status STRING NOT NULL,           -- open | in_review | cleared | confirmed_fraud | escalated
  analyst_notes STRING,
  agent_report STRING,
  mlflow_trace_id STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Analyst HITL dispositions for FraudShield investigations';
