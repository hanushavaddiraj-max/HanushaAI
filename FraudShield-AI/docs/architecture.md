# FraudShield AI — Architecture

## Integrated flow

```
Kaggle synthetic data
  → MLOps workshop (bronze/silver/gold)
  → feature engineering + train + register
  → batch inference → fraud_ml.fraud_predictions
  → FraudShield investigator app
       ├─ SQL tools → warehouse → gold + predictions
       └─ RAG tool → knowledge playbooks (local or Vector Search)
  → analyst chat + HITL review
  → MLflow GenAI traces (rag_hit tags)
```

## Repositories in this wrapper

| Path | Role |
|------|------|
| `apps/investigator` | FastAPI + React investigation agent (from agent-monitoring-demo-app) |
| `knowledge/` | Investigation playbooks for RAG |
| `rag/` | Optional Vector Search ingest |
| `mlops/` | Pointer + runbook for `databricks-mlops-workshop` |
| `sql/` | Investigation views + HITL + knowledge table DDL |
| `docs/` | Architecture and plans |

## Security defaults

- Parameterized / whitelisted SQL tools only (no free-form SQL from the LLM)
- Agent never blocks cards or confirms fraud without human review
- Secrets only in `.env.local` (not committed)
