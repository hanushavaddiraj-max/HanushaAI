# MCC and Amount Risk Heuristics

These heuristics support investigation; they do not prove fraud by themselves.

## High-risk merchant categories (examples)

Treat elevated caution (not automatic fraud) for categories often associated with abuse or card-not-present risk, such as:

- Wire transfer / money services
- Cryptocurrency / digital goods (where present in MCC mapping)
- Certain travel and remote services when combined with unusual amount or geography

Always join MCC with customer history before concluding.

## Amount heuristics

- Large amount relative to yearly income or credit limit is a **risk indicator**.
- Sudden spike vs the customer's recent median spend is a **risk indicator**.
- Round amounts (e.g. exact thousands) can be suspicious online, but are common for some bill-pay merchants.

## Channel and time

- Online / card-not-present (`use_chip` indicating swipe or online) plus high amount warrants extra scrutiny.
- Night-time transactions (local hour) are weak signals alone; combine with amount and history.

## How FraudShield should use this

1. Pull score + gold details via SQL tools.
2. Retrieve this typology via knowledge search when explaining *why* something looks risky.
3. Phrase findings as indicators for the analyst, never as confirmed fraud.
