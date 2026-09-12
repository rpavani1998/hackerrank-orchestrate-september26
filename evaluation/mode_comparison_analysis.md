# Deterministic versus AI-enabled sample comparison

Both modes ran all 25 solved sample requests in memory; neither mode wrote `output.csv`.

## Per-field matches against solved sample outputs

| Field | Deterministic | AI-enabled |
|---|---:|---:|
| amount_safe_to_pay | 3/25 | 3/25 |
| affordability_status | 19/25 | 19/25 |
| recommended_payment_method | 21/25 | 21/25 |
| payment_plan | 21/25 | 21/25 |
| earliest_date_for_full_payment | 18/25 | 18/25 |
| spending_changes_needed | 21/25 | 21/25 |
| explanation_consistency | 25/25 | 25/25 |

## Mode differences

- `request_01`: amount_safe_to_pay

## Exceptions

- deterministic: 0
- ai: 0

## Source-backed interpretation

- AI mode consumed 16 validated cached message facts; 3 malformed provider responses were rejected and never entered projection.
- `message_11` added a confirmed EUR 1661 salary credit on 2026-01-15 to request_15's timeline; the recommendation stayed unchanged.
- Delayed/pending refunds, prizes, payouts, and disputed reversals were unresolved and never added cash.
- Settled/non-cash facts were status-only; they did not duplicate starting-balance or event cash.
- When supplied, the analysis artifact contributed only validated source groups; deterministic code recalculated cadence, amounts, projections, and replay.
