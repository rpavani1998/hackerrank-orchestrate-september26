# Message extraction evaluation

Model: `google/gemini-3.8-flash`
Messages: 19

Expected facts were recorded in `evaluation/message_extraction_expectations.json` before extraction.
The evaluator compares source references, transaction type, update status, legacy action, amount, currency, date values, recurrence scope, and application state.

## Field-level results

| Field | Correct | Total |
|---|---:|---:|
| source_references | 16 | 19 |
| transaction_type | 16 | 19 |
| update_status | 16 | 19 |
| action | 16 | 19 |
| amount | 16 | 19 |
| currency | 16 | 19 |
| dates | 16 | 19 |
| recurrence_scope | 16 | 19 |
| application | 16 | 19 |

## Usage

- Provider calls: 19
- Cache hits: 0
- Input tokens: 6481
- Output tokens: 11774
- Total tokens: 18255
- Total reported/estimated cost: USD 0.04901325
- Average cost per selected message: USD 0.002579644736842105263157894737

## Unresolved/application cases

- `message_02`: unresolved — no linked event was supplied
- `message_03`: unresolved — no linked event was supplied
- `message_07`: unresolved — transaction update lacks confirmed settlement
- `message_106`: rejected — structured response content was not JSON
- `message_12`: unresolved — no linked event was supplied
- `message_13`: unresolved — no linked event was supplied
- `message_14`: unresolved — transaction update lacks confirmed settlement
- `message_15`: rejected — structured response content was not JSON
- `message_16`: unresolved — transaction update lacks confirmed settlement
- `message_35`: rejected — structured response content was not JSON
