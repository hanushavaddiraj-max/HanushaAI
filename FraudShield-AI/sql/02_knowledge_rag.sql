-- FraudShield knowledge RAG objects (run after 01_investigation_views.sql)
-- Chunk rows are written by rag/ingest_knowledge.py; CDF is required for Vector Search Delta Sync.

CREATE SCHEMA IF NOT EXISTS dev.fraudshield
COMMENT 'FraudShield AI investigation objects (agent + HITL + RAG)';

CREATE TABLE IF NOT EXISTS dev.fraudshield.knowledge_chunks (
  id STRING NOT NULL,
  source STRING NOT NULL,
  title STRING,
  text STRING NOT NULL
)
USING DELTA
TBLPROPERTIES (delta.enableChangeDataFeed = true)
COMMENT 'Chunked investigation playbooks for FraudShield RAG (managed embeddings via Vector Search)';

-- If the table already existed without CDF, enable it:
ALTER TABLE dev.fraudshield.knowledge_chunks
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
