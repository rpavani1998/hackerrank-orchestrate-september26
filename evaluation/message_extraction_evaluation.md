# Message extraction evaluation

Model: `google/gemini-3.8-flash`
Messages: 19

Expected facts were recorded in `evaluation/message_extraction_expectations.json` before extraction.
The evaluator compares source references, transaction type, update status, legacy action, amount, currency, date values, recurrence scope, and application state.

## Field-level results

| Field | Correct | Total |
|---|---:|---:|
| source_references | 19 | 19 |
| transaction_type | 18 | 19 |
| update_status | 18 | 19 |
| action | 12 | 19 |
| amount | 19 | 19 |
| currency | 19 | 19 |
| dates | 19 | 19 |
| recurrence_scope | 19 | 19 |
| application | 19 | 19 |

## Usage

- Provider calls: 19
- Cache hits: 0
- Input tokens: 5483
- Output tokens: 15623
- Total tokens: 21106
- Total reported/estimated cost: USD 0.06269850
- Average cost per selected message: USD 0.003299921052631578947368421053

## Unresolved/application cases

- `message_02`: unresolved — no linked event was supplied
- `message_03`: unresolved — no linked event was supplied
- `message_07`: unresolved — transaction update lacks confirmed settlement
- `message_106`: unresolved — transaction update lacks confirmed settlement
- `message_12`: unresolved — no linked event was supplied
- `message_13`: unresolved — no linked event was supplied
- `message_14`: unresolved — transaction update lacks confirmed settlement
- `message_16`: unresolved — transaction update lacks confirmed settlement
