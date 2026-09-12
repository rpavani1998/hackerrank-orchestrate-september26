# Validated analysis → forecast trace

This trace uses `request_02` in AI mode. The model proposes grouping only; deterministic validation, statistics, projection amounts, and replay calculate the financial effect.

## Validated pattern

- Pattern: `ai_pattern_0001` (recurring_commitment)
- Category/label: `education` / `Course tuition`
- Source event IDs: `event_108, event_116, event_124, event_132, event_140`
- Cadence: `monthly_calendar_like` (30 days)
- Deterministic amount policy: `deterministic_recent_statistic_only`; recent median description `3040000.00`

## Source records

- `event_108`: 2025-03-09 3040000 IDR, Course tuition, status `settled`
- `event_116`: 2025-04-09 3040000 IDR, Course tuition, status `settled`
- `event_124`: 2025-05-09 3040000 IDR, Course tuition, status `settled`
- `event_132`: 2025-06-09 3040000 IDR, Course tuition, status `settled`
- `event_140`: 2025-07-09 3040000 IDR, Course tuition, status `settled`

## Projected event

- Date: `2025-08-09`
- Direction/category: `debit` / `education`
- Amount: `3040000` IDR
- Projection source IDs: `event_108, event_116, event_124, event_132, event_140`

## Cash-flow effect

- Starting available-balance snapshot: `60383889.2` IDR
- Balance after the first projected event: `50260516.74` IDR
- Baseline replay safe through horizon: `True`; lowest projected balance: `47023121.20` IDR
- Historical transactions were not replayed against the supplied starting snapshot.
- No affordability, ranking, spending cut, or reserve-policy decision came from the model.
