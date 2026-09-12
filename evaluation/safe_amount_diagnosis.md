# Safe-amount discrepancy diagnosis

This is a read-only diagnosis of the current forecast amount-and-timing path. Signed differences are `actual - expected`; monetary values are never aggregated across currencies. The current AI-enabled sample artifact is loaded, so provenance records cached AI scopes and deterministic fallback scopes.

## Method and limits

- The baseline is `Agent.projections()` with no purchase payment or spending changes.
- Baseline replay is extended through the full 90-day horizon without the production replay helper's early return, solely to identify the true lowest balance and date.
- Expected-payment replay inserts the expected safe amount on `request_date`, after same-day projected events, and makes no spending changes.
- A baseline breach means the current forecast falls below the protected minimum without the requested payment. An expected-payment failure reports the first failing date and `minimum - balance` shortfall.
- Implied expected minimum is shown only when the expected amount is strictly between zero and the requested amount; capped outputs do not imply a binding minimum or date.

## Per-sample discrepancy table

| Request | Currency | Start | Minimum | Requested | Expected safe | Actual safe | Signed actual-expected | Absolute | Baseline low (date) | Baseline breach | Actual cap | Expected cap | Implied expected minimum | Provenance | Fallback |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---:|---|---|
| request_01 | ZAR | 58481.10 | 18000.00 | 25256.00 | 25256.00 | 6084.01 | -19171.99 | 19171.99 | 24084.01 (2024-06-01) | no | none | requested_amount | n/a | cached_ai | none |
| request_02 | IDR | 60383889.20 | 29158400.00 | 46018000.00 | 17229139.20 | 17864721.20 | 635582.00 | 635582.00 | 47023121.20 (2025-08-13) | no | none | none | 46387539.20 | cached_ai | none |
| request_03 | IDR | 5810300.00 | 2668700.00 | 5491000.00 | 873000.00 | 1089018.06 | 216018.06 | 216018.06 | 3757718.06 (2019-09-14) | no | none | none | 3541700.00 | deterministic_fallback | no live representative AI scope |
| request_04 | IDR | 52206950.00 | 30686600.00 | 12693000.00 | 8401800.00 | 10132985.41 | 1731185.41 | 1731185.41 | 40819585.41 (2024-06-13) | no | none | none | 39088400.00 | deterministic_fallback | no live representative AI scope |
| request_05 | ZAR | 46475.10 | 13100.00 | 15488.00 | 737.00 | 0.00 | -737.00 | 737.00 | 8757.30 (2026-02-04) | yes | zero | none | 13837.00 | cached_ai | none |
| request_06 | EUR | 1942.40 | 800.00 | 620.40 | 603.30 | 620.40 | 17.10 | 17.10 | 1575.12 (2026-01-13) | no | requested_amount | none | 1403.30 | deterministic_fallback | no live representative AI scope |
| request_07 | INR | 218945.56 | 93000.00 | 197400.00 | 87170.56 | 94391.34 | 7220.78 | 7220.78 | 187391.34 (2024-09-13) | no | none | none | 180170.56 | deterministic_fallback | no live representative AI scope |
| request_08 | EUR | 1536.57 | 800.00 | 996.60 | 284.57 | 369.70 | 85.13 | 85.13 | 1169.70 (2025-02-13) | no | none | none | 1084.57 | deterministic_fallback | no live representative AI scope |
| request_09 | EUR | 2231.10 | 600.00 | 166.61 | 166.61 | 166.61 | 0.00 | 0.00 | 795.69 (2026-10-02) | no | requested_amount | requested_amount | n/a | deterministic_fallback | no live representative AI scope |
| request_10 | INR | 750155.00 | 225400.00 | 266700.00 | 12700.00 | 0.00 | -12700.00 | 12700.00 | 154851.09 (2025-03-06) | yes | zero | none | 238100.00 | deterministic_fallback | no live representative AI scope |
| request_11 | IDR | 63531795.00 | 34140600.00 | 13110000.00 | 12510645.00 | 13110000.00 | 599355.00 | 599355.00 | 47379744.89 (2025-05-14) | no | requested_amount | none | 46651245.00 | deterministic_fallback | no live representative AI scope |
| request_12 | ZAR | 193089.89 | 43200.00 | 65164.00 | 65164.00 | 65164.00 | 0.00 | 0.00 | 118864.42 (2026-07-01) | no | requested_amount | requested_amount | n/a | deterministic_fallback | no live representative AI scope |
| request_13 | EUR | 2789.52 | 1300.00 | 941.60 | 433.40 | 941.60 | 508.20 | 508.20 | 2420.76 (2024-03-14) | no | requested_amount | none | 1733.40 | deterministic_fallback | no live representative AI scope |
| request_14 | EUR | 3931.74 | 2200.00 | 5414.20 | 597.74 | 0.00 | -597.74 | 597.74 | 613.64 (2025-11-02) | yes | zero | none | 2797.74 | deterministic_fallback | no live representative AI scope |
| request_15 | EUR | 1770.05 | 1200.00 | 3685.00 | 83.05 | 0.00 | -83.05 | 83.05 | -496.22 (2026-04-04) | yes | zero | none | 1283.05 | deterministic_fallback | no live representative AI scope |
| request_16 | INR | 362370.00 | 122400.00 | 122500.00 | 122500.00 | 122500.00 | 0.00 | 0.00 | 262905.59 (2023-09-14) | no | requested_amount | requested_amount | n/a | deterministic_fallback | no live representative AI scope |
| request_17 | INR | 550379.58 | 166100.00 | 274600.00 | 243849.58 | 237498.83 | -6350.75 | 6350.75 | 403598.83 (2026-03-14) | no | none | none | 409949.58 | deterministic_fallback | no live representative AI scope |
| request_18 | EUR | 2486.00 | 1400.00 | 3246.10 | 462.00 | 646.65 | 184.65 | 184.65 | 2046.65 (2026-07-14) | no | none | none | 1862.00 | deterministic_fallback | no live representative AI scope |
| request_19 | INR | 199545.00 | 92800.00 | 39660.00 | 28820.00 | 39660.00 | 10840.00 | 10840.00 | 158646.11 (2024-09-14) | no | requested_amount | none | 121620.00 | deterministic_fallback | no live representative AI scope |
| request_20 | INR | 102609.05 | 64500.00 | 303700.00 | 5400.00 | 17006.40 | 11606.40 | 11606.40 | 81506.40 (2026-02-13) | no | none | none | 69900.00 | cached_ai | none |
| request_21 | USD | 3911.35 | 1800.00 | 1574.40 | 1543.35 | 1574.40 | 31.05 | 31.05 | 3471.53 (2026-04-12) | no | requested_amount | none | 3343.35 | deterministic_fallback | no live representative AI scope |
| request_22 | EUR | 1132.46 | 500.00 | 731.50 | 475.46 | 469.81 | -5.65 | 5.65 | 969.81 (2024-12-14) | no | none | none | 975.46 | deterministic_fallback | no live representative AI scope |
| request_23 | ZAR | 51957.90 | 27000.00 | 38016.00 | 9152.00 | 10113.63 | 961.63 | 961.63 | 37113.63 (2025-05-14) | no | none | none | 36152.00 | deterministic_fallback | no live representative AI scope |
| request_24 | INR | 85045.00 | 51000.00 | 109600.00 | 13420.00 | 13080.61 | -339.39 | 339.39 | 64080.61 (2026-01-13) | no | none | none | 64420.00 | deterministic_fallback | no live representative AI scope |
| request_25 | IDR | 32063050.00 | 23379100.00 | 60496000.00 | 1425000.00 | 2388502.63 | 963502.63 | 963502.63 | 25767602.63 (2024-03-14) | no | none | none | 24804100.00 | deterministic_fallback | no live representative AI scope |

## Expected-payment safety replay

| Request | Expected payment passes full horizon | First failing date | Shortfall | Remaining minimum headroom if pass | Requested cap explains headroom |
|---|---|---|---:|---:|---|
| request_01 | no | 2024-05-02 | 2654.04 | n/a | no |
| request_02 | yes | none | n/a | 635582.00 | no |
| request_03 | yes | none | n/a | 216018.06 | no |
| request_04 | yes | none | n/a | 1731185.41 | no |
| request_05 | no | 2026-02-02 | 3947.72 | n/a | no |
| request_06 | yes | none | n/a | 171.82 | no |
| request_07 | yes | none | n/a | 7220.78 | no |
| request_08 | yes | none | n/a | 85.13 | no |
| request_09 | yes | none | n/a | 29.08 | yes |
| request_10 | no | 2025-02-28 | 2056.67 | n/a | no |
| request_11 | yes | none | n/a | 728499.89 | no |
| request_12 | yes | none | n/a | 10500.42 | yes |
| request_13 | yes | none | n/a | 687.36 | no |
| request_14 | no | 2025-10-03 | 556.32 | n/a | no |
| request_15 | no | 2026-01-14 | 29.41 | n/a | no |
| request_16 | yes | none | n/a | 18005.59 | yes |
| request_17 | no | 2026-03-13 | 591.86 | n/a | no |
| request_18 | yes | none | n/a | 184.65 | no |
| request_19 | yes | none | n/a | 37026.11 | no |
| request_20 | yes | none | n/a | 11606.40 | no |
| request_21 | yes | none | n/a | 128.18 | no |
| request_22 | no | 2024-12-13 | 0.65 | n/a | no |
| request_23 | yes | none | n/a | 961.63 | no |
| request_24 | no | 2026-01-13 | 339.39 | n/a | no |
| request_25 | yes | none | n/a | 963502.63 | no |

## Currency-separated error summaries

### EUR
- Samples: `8`; exact safe-amount matches: `1/8`.
- Positive actual-minus-expected cases: `4`; negative cases: `3`; zero differences: `1`.
- Signed differences are listed per request above; no cross-currency sum is reported.

### IDR
- Samples: `5`; exact safe-amount matches: `0/5`.
- Positive actual-minus-expected cases: `5`; negative cases: `0`; zero differences: `0`.
- Signed differences are listed per request above; no cross-currency sum is reported.

### INR
- Samples: `7`; exact safe-amount matches: `1/7`.
- Positive actual-minus-expected cases: `3`; negative cases: `3`; zero differences: `1`.
- Signed differences are listed per request above; no cross-currency sum is reported.

### USD
- Samples: `1`; exact safe-amount matches: `0/1`.
- Positive actual-minus-expected cases: `1`; negative cases: `0`; zero differences: `0`.
- Signed differences are listed per request above; no cross-currency sum is reported.

### ZAR
- Samples: `4`; exact safe-amount matches: `1/4`.
- Positive actual-minus-expected cases: `1`; negative cases: `2`; zero differences: `1`.
- Signed differences are listed per request above; no cross-currency sum is reported.

## Match qualification

The current artifact has `3/25` exact safe-amount matches. All `3` exact matches are requested-amount caps: request_09, request_12, request_16. There are no uncapped exact matches, so the solved sample amounts do not independently establish an uncapped amount-selection convention.

## One-assumption-at-a-time diagnostic alternatives

These alternatives are diagnostic only and are not applied to production. They preserve source groups, currencies, pending-debit treatment, replay ordering, and evidence handling:
- `median_all_recurring_debits`: replace the current upper-quartile amount for every non-stable recurring debit with the median of retained source observations.
- `latest_all_recurring_debits`: replace the current non-stable recurring-debit statistic with its latest retained source observation.
- `30_day_monthly_timing`: replace calendar-month advancement and month-end clamping with 30 elapsed days for monthly recurrences, leaving amounts unchanged.

| Request | Currency | Current | Median debit variant | Latest debit variant | 30-day timing variant |
|---|---|---:|---:|---:|---:|
| request_01 | ZAR | 6084.01 | 6084.01 | 6985.85 | 6084.01 |
| request_02 | IDR | 17864721.20 | 17974695.96 | 18376094.03 | 16575533.80 |
| request_03 | IDR | 1089018.06 | 1116663.31 | 1124921.44 | 1089018.06 |
| request_04 | IDR | 10132985.41 | 10461967.57 | 10283912.78 | 10132985.41 |
| request_05 | ZAR | 0.00 | 0.00 | 0.00 | 0.00 |
| request_06 | EUR | 620.40 | 620.40 | 620.40 | 620.40 |
| request_07 | INR | 94391.34 | 94935.82 | 97370.34 | 94391.34 |
| request_08 | EUR | 369.70 | 382.68 | 359.65 | 369.70 |
| request_09 | EUR | 166.61 | 166.61 | 166.61 | 166.61 |
| request_10 | INR | 0.00 | 0.00 | 0.00 | 0.00 |
| request_11 | IDR | 13110000.00 | 13110000.00 | 13110000.00 | 13110000.00 |
| request_12 | ZAR | 65164.00 | 65164.00 | 65164.00 | 65164.00 |
| request_13 | EUR | 941.60 | 941.60 | 941.60 | 941.60 |
| request_14 | EUR | 0.00 | 0.00 | 0.00 | 0.00 |
| request_15 | EUR | 0.00 | 0.00 | 0.00 | 0.00 |
| request_16 | INR | 122500.00 | 122500.00 | 122500.00 | 122500.00 |
| request_17 | INR | 237498.83 | 242443.39 | 180566.37 | 239173.83 |
| request_18 | EUR | 646.65 | 659.88 | 646.82 | 646.65 |
| request_19 | INR | 39660.00 | 39660.00 | 39660.00 | 39660.00 |
| request_20 | INR | 17006.40 | 17383.58 | 15855.46 | 17006.40 |
| request_21 | USD | 1574.40 | 1574.40 | 1574.40 | 1574.40 |
| request_22 | EUR | 469.81 | 476.20 | 473.87 | 469.81 |
| request_23 | ZAR | 10113.63 | 10223.88 | 10659.87 | 10113.63 |
| request_24 | INR | 13080.61 | 13689.71 | 12773.10 | 13080.61 |
| request_25 | IDR | 2388502.63 | 2600382.15 | 2305807.60 | 2840184.22 |

### Median debit variant by currency

- `EUR`: exact `1/8`; changed from current `3/8`; raw differences remain per-request above and are not summed across currencies.
- `IDR`: exact `0/5`; changed from current `4/5`; raw differences remain per-request above and are not summed across currencies.
- `INR`: exact `1/7`; changed from current `4/7`; raw differences remain per-request above and are not summed across currencies.
- `USD`: exact `0/1`; changed from current `0/1`; raw differences remain per-request above and are not summed across currencies.
- `ZAR`: exact `1/4`; changed from current `1/4`; raw differences remain per-request above and are not summed across currencies.

### Latest debit variant by currency

- `EUR`: exact `1/8`; changed from current `3/8`; raw differences remain per-request above and are not summed across currencies.
- `IDR`: exact `0/5`; changed from current `4/5`; raw differences remain per-request above and are not summed across currencies.
- `INR`: exact `1/7`; changed from current `4/7`; raw differences remain per-request above and are not summed across currencies.
- `USD`: exact `0/1`; changed from current `0/1`; raw differences remain per-request above and are not summed across currencies.
- `ZAR`: exact `1/4`; changed from current `2/4`; raw differences remain per-request above and are not summed across currencies.

### 30-day timing variant by currency

- `EUR`: exact `1/8`; changed from current `0/8`; raw differences remain per-request above and are not summed across currencies.
- `IDR`: exact `0/5`; changed from current `2/5`; raw differences remain per-request above and are not summed across currencies.
- `INR`: exact `1/7`; changed from current `1/7`; raw differences remain per-request above and are not summed across currencies.
- `USD`: exact `0/1`; changed from current `0/1`; raw differences remain per-request above and are not summed across currencies.
- `ZAR`: exact `1/4`; changed from current `0/4`; raw differences remain per-request above and are not summed across currencies.

## Mismatch groups and representative low-point traces

The representatives below are selected by largest absolute discrepancy within each group. The low-point event list is source-linked and separates explicit events, inferred recurrence statistics/date rules, message evidence, and the expected payment.

### Positive overestimates (actual > expected) (14 samples)

#### `request_04` (IDR)
- Expected `8401800.00`, actual `10132985.41`, signed difference `1731185.41`.
- Baseline low: `40819585.41` on `2024-06-13`; baseline breach: `no`.
- Expected-payment replay: `passes`; expected-payment low `32417785.41` on `2024-06-13`.
- Baseline low-point projected events:
- `2024-06-13` debit `1375854.05` category `entertainment`, event `event_290`, source IDs `event_261,event_268,event_276,event_283,event_290`; amount=1375854.05 from upper-quartile retained variable expense statistic, raw_source=1375854.05 IDR, converted=1375854.05 at 2024-05-13; date=last source date 2024-05-13 + 1 calendar month(s), month-end clamped; observations=5 from 2024-01-13 through 2024-05-13; source_ids=event_261,event_268,event_276,event_283,event_290; source_statuses=event_261:settled,event_268:settled,event_276:settled,event_283:settled,event_290:settled; evidence=none
- Expected-payment low-point projected events on `2024-06-13`:
- `2024-06-13` debit `1375854.05` category `entertainment`, event `event_290`, source IDs `event_261,event_268,event_276,event_283,event_290`; amount=1375854.05 from upper-quartile retained variable expense statistic, raw_source=1375854.05 IDR, converted=1375854.05 at 2024-05-13; date=last source date 2024-05-13 + 1 calendar month(s), month-end clamped; observations=5 from 2024-01-13 through 2024-05-13; source_ids=event_261,event_268,event_276,event_283,event_290; source_statuses=event_261:settled,event_268:settled,event_276:settled,event_283:settled,event_290:settled; evidence=none

#### `request_25` (IDR)
- Expected `1425000.00`, actual `2388502.63`, signed difference `963502.63`.
- Baseline low: `25767602.63` on `2024-03-14`; baseline breach: `no`.
- Expected-payment replay: `passes`; expected-payment low `24342602.63` on `2024-03-14`.
- Baseline low-point projected events:
- `2024-03-14` debit `451681.59` category `entertainment`, event `event_2206`, source IDs `event_2174,event_2182,event_2190,event_2198,event_2206`; amount=451681.59 from upper-quartile retained variable expense statistic, raw_source=451681.59 IDR, converted=451681.59 at 2024-02-14; date=last source date 2024-02-14 + 1 calendar month(s), month-end clamped; observations=5 from 2023-10-14 through 2024-02-14; source_ids=event_2174,event_2182,event_2190,event_2198,event_2206; source_statuses=event_2174:settled,event_2182:settled,event_2190:settled,event_2198:settled,event_2206:settled; evidence=none
- Expected-payment low-point projected events on `2024-03-14`:
- `2024-03-14` debit `451681.59` category `entertainment`, event `event_2206`, source IDs `event_2174,event_2182,event_2190,event_2198,event_2206`; amount=451681.59 from upper-quartile retained variable expense statistic, raw_source=451681.59 IDR, converted=451681.59 at 2024-02-14; date=last source date 2024-02-14 + 1 calendar month(s), month-end clamped; observations=5 from 2023-10-14 through 2024-02-14; source_ids=event_2174,event_2182,event_2190,event_2198,event_2206; source_statuses=event_2174:settled,event_2182:settled,event_2190:settled,event_2198:settled,event_2206:settled; evidence=none

#### `request_02` (IDR)
- Expected `17229139.20`, actual `17864721.20`, signed difference `635582.00`.
- Baseline low: `47023121.20` on `2025-08-13`; baseline breach: `no`.
- Expected-payment replay: `passes`; expected-payment low `29793982.00` on `2025-08-13`.
- Baseline low-point projected events:
- `2025-08-13` debit `369550.00` category `cloud_storage`, event `event_143`, source IDs `event_111,event_119,event_127,event_135,event_143`; amount=369550.00 from median(all retained stable expense observations), raw_source=369550 IDR, converted=369550 at 2025-07-13; date=last source date 2025-07-13 + 1 calendar month(s), month-end clamped; observations=5 from 2025-03-13 through 2025-07-13; source_ids=event_111,event_119,event_127,event_135,event_143; source_statuses=event_111:settled,event_119:settled,event_127:settled,event_135:settled,event_143:settled; evidence=none
- Expected-payment low-point projected events on `2025-08-13`:
- `2025-08-13` debit `369550.00` category `cloud_storage`, event `event_143`, source IDs `event_111,event_119,event_127,event_135,event_143`; amount=369550.00 from median(all retained stable expense observations), raw_source=369550 IDR, converted=369550 at 2025-07-13; date=last source date 2025-07-13 + 1 calendar month(s), month-end clamped; observations=5 from 2025-03-13 through 2025-07-13; source_ids=event_111,event_119,event_127,event_135,event_143; source_statuses=event_111:settled,event_119:settled,event_127:settled,event_135:settled,event_143:settled; evidence=none

### Positive expected, zero predicted (4 samples)

#### `request_10` (INR)
- Expected `12700.00`, actual `0.00`, signed difference `-12700.00`.
- Baseline low: `154851.09` on `2025-03-06`; baseline breach: `yes`.
- Expected-payment replay: `fails`; expected-payment low `142151.09` on `2025-03-06`.
- Baseline low-point projected events:
- `2025-03-06` debit `12092.24` category `groceries`, event `event_866`, source IDs `event_841,event_842,event_843,event_844,event_845,event_846,event_847,event_848,event_849,event_850,event_851,event_852,event_853,event_854,event_855,event_856,event_857,event_858,event_859,event_860,event_861,event_862,event_863,event_864,event_865,event_866`; amount=12092.24 from upper-quartile retained variable expense statistic, raw_source=12092.24 INR, converted=12092.24 at 2024-12-05; date=last source date 2024-12-05 + 7 day cadence; observations=26 from 2024-06-13 through 2024-12-05; source_ids=event_841,event_842,event_843,event_844,event_845,event_846,event_847,event_848,event_849,event_850,event_851,event_852,event_853,event_854,event_855,event_856,event_857,event_858,event_859,event_860,event_861,event_862,event_863,event_864,event_865,event_866; source_statuses=event_841:settled,event_842:settled,event_843:settled,event_844:settled,event_845:settled,event_846:settled,event_847:settled,event_848:settled,event_849:settled,event_850:settled,event_851:settled,event_852:settled,event_853:settled,event_854:settled,event_855:settled,event_856:settled,event_857:settled,event_858:settled,event_859:settled,event_860:settled,event_861:settled,event_862:settled,event_863:settled,event_864:settled,event_865:settled,event_866:settled; evidence=none
- Expected-payment first failing low point `2025-02-28`:
- `2025-02-28` debit `6245.32` category `transport`, event `event_891`, source IDs `event_867,event_868,event_869,event_870,event_871,event_872,event_873,event_874,event_875,event_876,event_877,event_878,event_879,event_880,event_881,event_882,event_883,event_884,event_885,event_886,event_887,event_888,event_889,event_890,event_891`; amount=6245.32 from upper-quartile retained variable expense statistic, raw_source=6245.32 INR, converted=6245.32 at 2024-11-29; date=last source date 2024-11-29 + 7 day cadence; observations=25 from 2024-06-14 through 2024-11-29; source_ids=event_867,event_868,event_869,event_870,event_871,event_872,event_873,event_874,event_875,event_876,event_877,event_878,event_879,event_880,event_881,event_882,event_883,event_884,event_885,event_886,event_887,event_888,event_889,event_890,event_891; source_statuses=event_867:settled,event_868:settled,event_869:settled,event_870:settled,event_871:settled,event_872:settled,event_873:settled,event_874:settled,event_875:settled,event_876:settled,event_877:settled,event_878:settled,event_879:settled,event_880:settled,event_881:settled,event_882:settled,event_883:settled,event_884:settled,event_885:settled,event_886:settled,event_887:settled,event_888:settled,event_889:settled,event_890:settled,event_891:settled; evidence=none

#### `request_05` (ZAR)
- Expected `737.00`, actual `0.00`, signed difference `-737.00`.
- Baseline low: `8757.30` on `2026-02-04`; baseline breach: `yes`.
- Expected-payment replay: `fails`; expected-payment low `8020.30` on `2026-02-04`.
- Baseline low-point projected events:
- `2026-02-04` debit `411.47` category `transport`, event `event_437`, source IDs `event_425,event_426,event_427,event_428,event_429,event_430,event_431,event_432,event_433,event_434,event_435,event_436,event_437`; amount=411.47 from upper-quartile retained variable expense statistic, raw_source=411.47 ZAR, converted=411.47 at 2025-10-29; date=last source date 2025-10-29 + 14 day cadence; observations=13 from 2025-05-14 through 2025-10-29; source_ids=event_425,event_426,event_427,event_428,event_429,event_430,event_431,event_432,event_433,event_434,event_435,event_436,event_437; source_statuses=event_425:settled,event_426:settled,event_427:settled,event_428:settled,event_429:settled,event_430:settled,event_431:settled,event_432:settled,event_433:settled,event_434:settled,event_435:settled,event_436:settled,event_437:settled; evidence=none
- Expected-payment first failing low point `2026-02-02`:
- `2026-02-02` debit `4972.00` category `rent`, event `event_398`, source IDs `event_359,event_367,event_375,event_383,event_391,event_398`; amount=4972.00 from median(all retained stable expense observations), raw_source=4972 ZAR, converted=4972 at 2025-11-02; date=last source date 2025-11-02 + 1 calendar month(s), month-end clamped; observations=6 from 2025-06-02 through 2025-11-02; source_ids=event_359,event_367,event_375,event_383,event_391,event_398; source_statuses=event_359:settled,event_367:settled,event_375:settled,event_383:settled,event_391:settled,event_398:settled; evidence=none

#### `request_14` (EUR)
- Expected `597.74`, actual `0.00`, signed difference `-597.74`.
- Baseline low: `613.64` on `2025-11-02`; baseline breach: `yes`.
- Expected-payment replay: `fails`; expected-payment low `15.90` on `2025-11-02`.
- Baseline low-point projected events:
- `2025-11-02` debit `112.72` category `groceries`, event `event_1226`, source IDs `event_1201,event_1202,event_1203,event_1204,event_1205,event_1206,event_1207,event_1208,event_1209,event_1210,event_1211,event_1212,event_1213,event_1214,event_1215,event_1216,event_1217,event_1218,event_1219,event_1220,event_1221,event_1222,event_1223,event_1224,event_1225,event_1226`; amount=112.72 from upper-quartile retained variable expense statistic, raw_source=112.72 EUR, converted=112.72 at 2025-08-03; date=last source date 2025-08-03 + 7 day cadence; observations=26 from 2025-02-09 through 2025-08-03; source_ids=event_1201,event_1202,event_1203,event_1204,event_1205,event_1206,event_1207,event_1208,event_1209,event_1210,event_1211,event_1212,event_1213,event_1214,event_1215,event_1216,event_1217,event_1218,event_1219,event_1220,event_1221,event_1222,event_1223,event_1224,event_1225,event_1226; source_statuses=event_1201:settled,event_1202:settled,event_1203:settled,event_1204:settled,event_1205:settled,event_1206:settled,event_1207:settled,event_1208:settled,event_1209:settled,event_1210:settled,event_1211:settled,event_1212:settled,event_1213:settled,event_1214:settled,event_1215:settled,event_1216:settled,event_1217:settled,event_1218:settled,event_1219:settled,event_1220:settled,event_1221:settled,event_1222:settled,event_1223:settled,event_1224:settled,event_1225:settled,event_1226:settled; evidence=none
- Expected-payment first failing low point `2025-10-03`:
- `2025-10-03` debit `688.60` category `rent`, event `event_1200`, source IDs `event_1163,event_1171,event_1178,event_1185,event_1193,event_1200`; amount=688.60 from median(all retained stable expense observations), raw_source=688.6 EUR, converted=688.6 at 2025-08-03; date=last source date 2025-08-03 + 1 calendar month(s), month-end clamped; observations=6 from 2025-03-03 through 2025-08-03; source_ids=event_1163,event_1171,event_1178,event_1185,event_1193,event_1200; source_statuses=event_1163:settled,event_1171:settled,event_1178:settled,event_1185:settled,event_1193:settled,event_1200:settled; evidence=none

### Positive underestimates (actual < expected) (8 samples)

#### `request_01` (ZAR)
- Expected `25256.00`, actual `6084.01`, signed difference `-19171.99`.
- Baseline low: `24084.01` on `2024-06-01`; baseline breach: `no`.
- Expected-payment replay: `fails`; expected-payment low `-1171.99` on `2024-06-01`.
- Baseline low-point projected events:
- `2024-06-01` debit `424.56` category `transport`, event `event_84`, source IDs `event_59,event_60,event_82,event_83,event_84`; amount=424.56 from upper-quartile retained variable expense statistic, raw_source=424.56 ZAR, converted=424.56 at 2024-03-02; date=last source date 2024-03-02 + 7 day cadence; observations=5 from 2023-09-09 through 2024-03-02; source_ids=event_59,event_60,event_82,event_83,event_84; source_statuses=event_59:settled,event_60:settled,event_82:settled,event_83:settled,event_84:settled; evidence=none
- Expected-payment first failing low point `2024-05-02`:
- `2024-05-02` debit `5148.00` category `rent`, event `event_32`, source IDs `event_01,event_07,event_13,event_19,event_26,event_32`; amount=5148.00 from median(all retained stable expense observations), raw_source=5148 ZAR, converted=5148 at 2024-03-02; date=last source date 2024-03-02 + 1 calendar month(s), month-end clamped; observations=6 from 2023-10-02 through 2024-03-02; source_ids=event_01,event_07,event_13,event_19,event_26,event_32; source_statuses=event_01:settled,event_07:settled,event_13:settled,event_19:settled,event_26:settled,event_32:settled; evidence=none

#### `request_10` (INR)
- Expected `12700.00`, actual `0.00`, signed difference `-12700.00`.
- Baseline low: `154851.09` on `2025-03-06`; baseline breach: `yes`.
- Expected-payment replay: `fails`; expected-payment low `142151.09` on `2025-03-06`.
- Baseline low-point projected events:
- `2025-03-06` debit `12092.24` category `groceries`, event `event_866`, source IDs `event_841,event_842,event_843,event_844,event_845,event_846,event_847,event_848,event_849,event_850,event_851,event_852,event_853,event_854,event_855,event_856,event_857,event_858,event_859,event_860,event_861,event_862,event_863,event_864,event_865,event_866`; amount=12092.24 from upper-quartile retained variable expense statistic, raw_source=12092.24 INR, converted=12092.24 at 2024-12-05; date=last source date 2024-12-05 + 7 day cadence; observations=26 from 2024-06-13 through 2024-12-05; source_ids=event_841,event_842,event_843,event_844,event_845,event_846,event_847,event_848,event_849,event_850,event_851,event_852,event_853,event_854,event_855,event_856,event_857,event_858,event_859,event_860,event_861,event_862,event_863,event_864,event_865,event_866; source_statuses=event_841:settled,event_842:settled,event_843:settled,event_844:settled,event_845:settled,event_846:settled,event_847:settled,event_848:settled,event_849:settled,event_850:settled,event_851:settled,event_852:settled,event_853:settled,event_854:settled,event_855:settled,event_856:settled,event_857:settled,event_858:settled,event_859:settled,event_860:settled,event_861:settled,event_862:settled,event_863:settled,event_864:settled,event_865:settled,event_866:settled; evidence=none
- Expected-payment first failing low point `2025-02-28`:
- `2025-02-28` debit `6245.32` category `transport`, event `event_891`, source IDs `event_867,event_868,event_869,event_870,event_871,event_872,event_873,event_874,event_875,event_876,event_877,event_878,event_879,event_880,event_881,event_882,event_883,event_884,event_885,event_886,event_887,event_888,event_889,event_890,event_891`; amount=6245.32 from upper-quartile retained variable expense statistic, raw_source=6245.32 INR, converted=6245.32 at 2024-11-29; date=last source date 2024-11-29 + 7 day cadence; observations=25 from 2024-06-14 through 2024-11-29; source_ids=event_867,event_868,event_869,event_870,event_871,event_872,event_873,event_874,event_875,event_876,event_877,event_878,event_879,event_880,event_881,event_882,event_883,event_884,event_885,event_886,event_887,event_888,event_889,event_890,event_891; source_statuses=event_867:settled,event_868:settled,event_869:settled,event_870:settled,event_871:settled,event_872:settled,event_873:settled,event_874:settled,event_875:settled,event_876:settled,event_877:settled,event_878:settled,event_879:settled,event_880:settled,event_881:settled,event_882:settled,event_883:settled,event_884:settled,event_885:settled,event_886:settled,event_887:settled,event_888:settled,event_889:settled,event_890:settled,event_891:settled; evidence=none

#### `request_17` (INR)
- Expected `243849.58`, actual `237498.83`, signed difference `-6350.75`.
- Baseline low: `403598.83` on `2026-03-14`; baseline breach: `no`.
- Expected-payment replay: `fails`; expected-payment low `159749.25` on `2026-03-14`.
- Baseline low-point projected events:
- `2026-03-14` debit `5758.89` category `transport`, event `event_1529`, source IDs `event_1504,event_1505,event_1506,event_1507,event_1508,event_1509,event_1510,event_1511,event_1512,event_1513,event_1514,event_1515,event_1516,event_1517,event_1518,event_1519,event_1520,event_1521,event_1522,event_1523,event_1524,event_1525,event_1526,event_1527,event_1528,event_1529`; amount=5758.89 from upper-quartile retained variable expense statistic, raw_source=5758.89 INR, converted=5758.89 at 2026-02-28; date=last source date 2026-02-28 + 7 day cadence; observations=26 from 2025-09-06 through 2026-02-28; source_ids=event_1504,event_1505,event_1506,event_1507,event_1508,event_1509,event_1510,event_1511,event_1512,event_1513,event_1514,event_1515,event_1516,event_1517,event_1518,event_1519,event_1520,event_1521,event_1522,event_1523,event_1524,event_1525,event_1526,event_1527,event_1528,event_1529; source_statuses=event_1504:settled,event_1505:settled,event_1506:settled,event_1507:settled,event_1508:settled,event_1509:settled,event_1510:settled,event_1511:settled,event_1512:settled,event_1513:settled,event_1514:settled,event_1515:settled,event_1516:settled,event_1517:settled,event_1518:settled,event_1519:settled,event_1520:settled,event_1521:settled,event_1522:settled,event_1523:settled,event_1524:settled,event_1525:settled,event_1526:settled,event_1527:settled,event_1528:settled,event_1529:settled; evidence=none
- Expected-payment first failing low point `2026-03-13`:
- `2026-03-13` debit `1675.00` category `delivery_membership`, event `event_1477`, source IDs `event_1449,event_1456,event_1463,event_1470,event_1477`; amount=1675.00 from median(all retained stable expense observations), raw_source=1675 INR, converted=1675 at 2026-02-13; date=last source date 2026-02-13 + 1 calendar month(s), month-end clamped; observations=5 from 2025-10-13 through 2026-02-13; source_ids=event_1449,event_1456,event_1463,event_1470,event_1477; source_statuses=event_1449:settled,event_1456:settled,event_1463:settled,event_1470:settled,event_1477:settled; evidence=none
- `2026-03-13` debit `10873.47` category `groceries`, event `event_1503`, source IDs `event_1478,event_1479,event_1480,event_1481,event_1482,event_1483,event_1484,event_1485,event_1486,event_1487,event_1488,event_1489,event_1490,event_1491,event_1492,event_1493,event_1494,event_1495,event_1496,event_1497,event_1498,event_1499,event_1500,event_1501,event_1502,event_1503,event_1545`; amount=10873.47 from upper-quartile retained variable expense statistic, raw_source=10873.47 INR, converted=10873.47 at 2026-02-27; date=last source date 2026-02-27 + 7 day cadence; observations=27 from 2025-09-05 through 2026-02-27; source_ids=event_1478,event_1479,event_1480,event_1481,event_1482,event_1483,event_1484,event_1485,event_1486,event_1487,event_1488,event_1489,event_1490,event_1491,event_1492,event_1493,event_1494,event_1495,event_1496,event_1497,event_1498,event_1499,event_1500,event_1501,event_1502,event_1503,event_1545; source_statuses=event_1478:settled,event_1479:settled,event_1480:settled,event_1481:settled,event_1482:settled,event_1483:settled,event_1484:settled,event_1485:settled,event_1486:settled,event_1487:settled,event_1488:settled,event_1489:settled,event_1490:settled,event_1491:settled,event_1492:settled,event_1493:settled,event_1494:settled,event_1495:settled,event_1496:settled,event_1497:settled,event_1498:settled,event_1499:settled,event_1500:settled,event_1501:settled,event_1502:settled,event_1503:settled,event_1545:settled; evidence=none

## Cause checklist

The following checks are recorded for each representative trace rather than treated as established causes without source evidence:

- Historical window and partial-period handling: inspect source dates and the first forecast anchor in each recurrence derivation above.
- Variable category totals versus per-transaction amounts: the derivation identifies the current median or upper-quartile policy and source IDs.
- Recurrence counts, anchors, and month-end handling: the derivation states the source count, last source date, cadence, and calendar-month rule.
- Explicit obligations and duplicate prevention: explicit rows are shown separately; recurring source IDs and low-point events identify possible overlap.
- Starting balance and pending debits: the replay starts from the supplied profile balance; event status and evidence status are shown for source-linked events.
- Salary and expense amendments: message-derived projections identify validated evidence; ordinary event projections identify source evidence status.
- Exchange-rate dates and rounding: explicit derivations state the conversion date; displayed values are rounded only for report readability.
- Forecast boundary and same-day ordering: the horizon is request date through request date plus 90 days; credits precede debits and the inserted expected payment is applied after projected events on the request date.

## Policy decision

No production forecast rule is changed by this diagnostic. A rule change is justified only after a representative source-backed reproduction and an independent failing test establish behavior required by the challenge contract; sample answers alone are not treated as policy evidence.
