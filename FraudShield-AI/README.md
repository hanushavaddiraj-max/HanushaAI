# FraudShield AI

End-to-end **Lakehouse MLOps + Agentic fraud investigation** platform on Azure Databricks.

This folder **wraps** two completed projects:

| Component | Location | Role |
|-----------|----------|------|
| MLOps plane | `../databricks-mlops-workshop` (+ `mlops/README.md`) | Data → features → train → `fraud_predictions` → monitor |
| Investigation agent | `apps/investigator` | FastAPI + React chat agent with fraud SQL tools |
| SQL objects | `sql/01_investigation_views.sql` | Investigation view + HITL reviews table |

Upstream inspirations (MIT): Microsoft MLOps workshop + Databricks agent monitoring demo.

## Architecture (short)

```
Analyst chat (FraudShield UI)
  → LangChain tools
       ├─ parameterized SQL → SQL Warehouse → fraud_gold / fraud_predictions
       └─ RAG knowledge tool → playbooks (local bundle or Vector Search)
  → MLflow GenAI traces (+ rag_hit tags)
```

RAG docs live in `knowledge/` (also bundled under `apps/investigator/knowledge/`).
Optional cloud ingest: `rag/ingest_knowledge.py` + `sql/02_knowledge_rag.sql`.

## Prerequisites

1. MLOps workshop already produced:
   - `dev.fraud_gold.transactions_enriched`
   - `dev.fraud_ml.fraud_predictions` (rows present)
2. A **Databricks SQL Warehouse** (Serverless SQL is fine)
3. LLM serving access (e.g. `databricks-llama-4-maverick`)

## Setup (investigator app)

```powershell
cd apps\investigator
copy .env.example .env.local
# Edit .env.local: HOST, TOKEN, MLFLOW_EXPERIMENT_ID, DATABRICKS_SQL_WAREHOUSE_ID

# Create investigation SQL objects (Databricks SQL Editor):
# run ../../sql/01_investigation_views.sql

# Python env
py -3 -m pip install uv
uv sync

# Run API + built UI
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

## Example prompts

- Show the highest-risk transactions with fraud probability above 0.9
- Investigate transaction `<id from results>`
- What evidence makes this transaction suspicious?
- What steps should I take before marking confirmed_fraud?
- Generate an investigation report for that transaction
- Record review status `in_review` with my notes

## RAG (local first)

Bundled playbooks work without Vector Search. To enable Databricks Vector Search later (costs while the endpoint is up):

1. Run `sql/02_knowledge_rag.sql`
2. On a cluster: `python rag/ingest_knowledge.py --knowledge-dir knowledge`
3. Set `FRAUDSHIELD_VS_ENDPOINT` + `FRAUDSHIELD_VS_INDEX` in `app.yaml` / `.env.local`

Offline eval: `python evals/test_rag_local.py` from `apps/investigator`.

## Security defaults

- No free-form SQL from the LLM
- Agent never auto-blocks cards
- Secrets only in `.env.local`

## Phased status

- [x] Phase 1 — wrapper repo + architecture docs
- [x] Phase 3 foundation — fraud tools + investigation prompt
- [x] RAG knowledge tool + agent citations / memory / guardrails
- [ ] Phase 4 — richer UI (search/list panels)
- [x] Phase 5 foundation — golden questions + local RAG eval
- [ ] Phase 6 — Azure DevOps CI/CD + deploy runbook polish

See `docs/architecture.md` and `docs/implementation-plan.md`.
