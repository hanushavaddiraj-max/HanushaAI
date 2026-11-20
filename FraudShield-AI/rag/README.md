# FraudShield RAG ingest (Vector Search)

Chunks Markdown playbooks from `../knowledge/` into Unity Catalog and a Databricks Vector Search index with **managed embeddings**.

## Objects

| Object | Purpose |
|--------|---------|
| `dev.fraudshield.knowledge_chunks` | Delta table (`id`, `source`, `title`, `text`) with **CDF enabled** |
| VS endpoint `fraudshield-vs` | Vector Search compute (**billed while online**) |
| Index `dev.fraudshield.knowledge_vs_index` | Delta Sync index; embeds `text` via `databricks-gte-large-en` |

## Run locally (warehouse write + VS create)

```powershell
cd FraudShield-AI\rag
$env:FRAUD_CATALOG="dev"
$env:FRAUDSHIELD_SCHEMA="fraudshield"
$env:FRAUDSHIELD_VS_ENDPOINT="fraudshield-vs"
$env:FRAUDSHIELD_VS_INDEX="dev.fraudshield.knowledge_vs_index"
$env:FRAUDSHIELD_EMBEDDING_ENDPOINT="databricks-gte-large-en"
$env:DATABRICKS_SQL_WAREHOUSE_ID="852a24c1d2cc3003"

# Needs databricks-sdk + databricks-vectorsearch, and CLI auth / env token
py -3 -m pip install databricks-sdk databricks-vectorsearch
py -3 ingest_knowledge.py --knowledge-dir ..\knowledge --warehouse-id $env:DATABRICKS_SQL_WAREHOUSE_ID
```

Table-only (no VS cost):

```powershell
py -3 ingest_knowledge.py --knowledge-dir ..\knowledge --warehouse-id $env:DATABRICKS_SQL_WAREHOUSE_ID --skip-vector-search
```

## App wiring

Set in `apps/investigator/app.yaml`:

- `FRAUDSHIELD_VS_ENDPOINT=fraudshield-vs`
- `FRAUDSHIELD_VS_INDEX=dev.fraudshield.knowledge_vs_index`

`rag_client` uses Vector Search when those are set; otherwise falls back to bundled local knowledge.

## Cost

Stop/delete the **Vector Search endpoint** when not demoing. Grant the FraudShield app SP `SELECT` on `dev.fraudshield` and query rights on the VS endpoint.
