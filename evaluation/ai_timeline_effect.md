# Demonstrated AI timeline effect

Request: `request_15` (request date `2026-01-06`)

## Source → fact → application

- Source: `message_11` (`2026-01-03T09:30:00Z`, linked to `request_15`)
- Source text: A quick update from the payroll team at Riverline Retail. Your first salary will be EUR 1661. The confirmed credit date is 2026-01-15. The money will appear after the bank posts the credit. Payroll ref EMP-0011.
- Extracted fact: `{"action": "confirmation", "ambiguities": [], "amount": "1661", "conflicts": [], "currency": "EUR", "dates": [{"date": "2026-01-15", "meaning": "payment_date"}], "missing_fields": [], "recurrence_scope": "once", "source_id": "message_11", "source_kind": "message", "supplied_event_id": null, "supplied_request_id": "request_15", "supplied_user_id": "user_15", "supporting_text": "Your first salary will be EUR 1661. The confirmed credit date is 2026-01-15.", "transaction_type": "salary", "update_status": "confirmed"}`
- Validated application: state=`applied`, cash_effect=`timeline_amendment`, reason=`validated salary timeline fact`

## Forecast change

- Deterministic projected-event count: 50
- AI-enabled projected-event count: 51
- Added events: `[["2026-01-15", "1661", "credit", "salary", "message_payroll", ""]]`
- Removed events: `[]`
- Deterministic safe amount: `0`
- AI-enabled safe amount: `0`
- Deterministic earliest full-payment date: `None`
- AI-enabled earliest full-payment date: `None`

The added 2026-01-15 salary credit is source-linked, converted through the deterministic currency/rate path, and does not create a refund or duplicate an existing event. The recommendation remained unchanged for this request.
