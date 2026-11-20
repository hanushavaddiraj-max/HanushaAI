# FraudShield implementation plan

## Done in this scaffold

1. Created `FraudShield-AI/` wrapper monorepo
2. Copied investigator app from `agent-monitoring-demo-app`
3. Replaced catalog-list tools with fraud investigation tools
4. Added SQL client + schema config env vars
5. Added `sql/01_investigation_views.sql` (view + HITL table)
6. Rebranded chat UI labels to FraudShield AI

## Done — RAG + agent enhancement

- Knowledge playbooks in `knowledge/` (bundled in app)
- `retrieve_investigation_knowledge` tool + `rag_client.py` (local fallback; optional Vector Search)
- Optional ingest: `rag/ingest_knowledge.py`, `sql/02_knowledge_rag.sql`
- Agent: SQL vs RAG routing, citations, multi-turn txn memory, report policy grounding, `rag_hit` MLflow tags
- Evals: `apps/investigator/evals/golden_questions.json` + `test_rag_local.py`
- Redeployed Databricks App with slim requirements (VS endpoint left unset to avoid cost)

## Next development slices

### Slice B — UI investigation panel
- High-risk table beside chat
- Transaction detail drawer
- Review status form calling `record_investigation_review`
- Rebuild client (`npm run build`) so source chips ship in `client/build`

### Slice C — AgentOps eval (extend)
- Live agent tool-routing evals against Databricks
- Groundedness checks on report draft

### Slice D — Enterprise
- Turn on Vector Search only when ready to pay for the endpoint
- Azure DevOps pipeline outline
- Cost/runbook docs
