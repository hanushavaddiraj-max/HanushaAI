# Investigation Report Writing SOP

## Purpose

Produce a human-readable draft for analyst review. The draft is not an enforcement action.

## Required sections

1. **Transaction identity** — `transaction_id`, amount, MCC, channel, time.
2. **ML prediction** — `fraud_score`, `prediction`, `model_version`, `scored_at`.
3. **Customer context** — short history summary and risk profile aggregates when available.
4. **Risk indicators** — list heuristics returned by tools; label each as indicator, not proof.
5. **Policy context** — cite checklist / HITL / typology passages when retrieved.
6. **Recommended next steps** — contact customer, escalate, clear, or confirm only as suggestions.
7. **Disclaimer** — agent-generated draft pending human decision.

## Tone

- Neutral, factual, cite tool outputs.
- Prefer bullets over long prose.
- If tools returned no rows, say so and stop inventing details.
