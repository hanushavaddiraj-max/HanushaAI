# HITL Review Status Meanings

FraudShield records analyst dispositions in `dev.fraudshield.investigation_reviews`. Status values:

| Status | Meaning | When to use |
|--------|---------|-------------|
| `open` | Case created, not actively worked | New queue intake |
| `in_review` | Analyst actively investigating | Default while gathering evidence |
| `cleared` | Transaction judged legitimate | Customer confirmed / pattern normal |
| `confirmed_fraud` | Human confirmed fraudulent activity | Only after verification — never model-only |
| `escalated` | Needs senior / compliance / specialist | Ambiguous high-impact cases |

## Rules

- The agent may draft a report and suggest a status, but the analyst owns the final status.
- `confirmed_fraud` requires explicit analyst intent in the chat or UI.
- Changing status does not trigger card blocks or account freezes in this system.
- Always store short `analyst_notes` explaining the decision.
