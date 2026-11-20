# MLOps plane (wrapped)

FraudShield does **not** duplicate the Microsoft Databricks MLOps workshop.

## Source of truth

Use the sibling workshop repo (already completed in this workspace):

`../databricks-mlops-workshop`

Upstream reference: https://github.com/microsoft/databricks-mlops-workshop  
Your copy: https://github.com/hanushavaddiraj-max/databricks-mlops-workshop

## What FraudShield reads from MLOps

| Object | Purpose |
|--------|---------|
| `dev.fraud_gold.transactions_enriched` | Transaction + customer/card context |
| `dev.fraud_ml.fraud_predictions` | Batch fraud scores + model version |
| `dev.fraud_ml.fraud_serving_inference` | Optional online scores |
| UC model `dev.fraud_ml.fraud_detection@champion` | Governed model metadata |

## Operator commands (run in workshop repo)

```powershell
cd ..\databricks-mlops-workshop
databricks bundle deploy -t dev
databricks bundle run batch_inference_job -t dev
```

Keep training/serving/monitoring in the workshop bundle. FraudShield only **consumes** prediction history for investigation.
