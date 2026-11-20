# FraudShield Investigation Checklist

Use this checklist before any HITL disposition. Predicted fraud score is a risk signal, not proof.

## Intake

1. Confirm `transaction_id`, `fraud_score`, `model_version`, and `scored_at` from ML prediction history.
2. Pull gold transaction details: amount, MCC, channel (`use_chip`), hour, merchant state, client/card ids.
3. Note whether a training/label `is_fraud` value exists; treat labels as delayed ground truth when present.

## Context gathering

4. Review customer recent transaction history for the same `client_id`.
5. Compare amount to typical spend and to income/credit-limit ratios when available.
6. Check risk evidence indicators (night-time, online, high-risk MCC, amount ratios). These are heuristics only.

## Analyst actions

7. Attempt customer contact or known-travel verification when amount/geography is unusual.
8. Document notes in the investigation review record.
9. Prefer status `in_review` while evidence is incomplete.
10. Only use `confirmed_fraud` after human verification of fraudulent activity.
11. Use `cleared` when legitimate customer activity is confirmed.
12. Use `escalated` for cases needing senior review, law enforcement, or compliance.

## Never automate

- Do not block cards, freeze accounts, or chargebacks from the agent alone.
- Do not invent merchants, scores, or history that tools did not return.
