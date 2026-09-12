# Financial profile — user_02 as of 2025-08-05

Request scope: `request_02`. Home currency: `IDR`.
Available balance snapshot: `60383889.20`; minimum balance: `29158400.00`.

## Preferences and constraints
- Protected: education, housing, utilities
- Permitted reductions: entertainment
- Permitted stops: cloud_storage
- Accepted methods: installments, partial_payment

## Historical coverage
- Dates: `2025-02-10` through `2025-08-04`
- Settled observations: `81`
- Observed gaps (days): `[1, 1, 8, 5, 5, 2, 1, 2, 1, 1, 2, 0]`; missing buckets are not treated as zero.

## Patterns and statistics
### ai_pattern_0001 — recurring_commitment: Course tuition
- Category: `education`; forecastable: `True`; source: `validated_ai`
- Source events: `event_108, event_116, event_124, event_132, event_140`
- Dates: `2025-03-09, 2025-04-09, 2025-05-09, 2025-06-09, 2025-07-09`
- Cadence: `monthly_calendar_like` (30 days); recent median: `3040000.00` IDR
- Range: `3040000.00`–`3040000.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Exact end date of the course tuition schedule is unspecified.
### ai_pattern_0002 — recurring_commitment: Clinic payment
- Category: `healthcare`; forecastable: `True`; source: `validated_ai`
- Source events: `event_109, event_117, event_125, event_133, event_141`
- Dates: `2025-03-11, 2025-04-11, 2025-05-11, 2025-06-11, 2025-07-11`
- Cadence: `monthly_calendar_like` (30 days); recent median: `1538498.10` IDR
- Range: `1452405.16`–`1641668.72`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Amounts vary slightly each month, indicating variable expense within a recurring schedule.
### ai_pattern_0003 — recurring_commitment: Home repair reserve
- Category: `housing`; forecastable: `True`; source: `validated_ai`
- Source events: `event_105, event_113, event_121, event_129, event_137, event_144`
- Dates: `2025-03-04, 2025-04-04, 2025-05-04, 2025-06-04, 2025-07-04, 2025-08-04`
- Cadence: `monthly_calendar_like` (31 days); recent median: `3534000.00` IDR
- Range: `3534000.00`–`3534000.00`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: Reserves may fluctuate or stop based on future maintenance needs.
### ai_pattern_0004 — recurring_commitment: Household insurance
- Category: `insurance`; forecastable: `True`; source: `validated_ai`
- Source events: `event_107, event_115, event_123, event_131, event_139`
- Dates: `2025-03-08, 2025-04-08, 2025-05-08, 2025-06-08, 2025-07-08`
- Cadence: `monthly_calendar_like` (30 days); recent median: `1132400.00` IDR
- Range: `1132400.00`–`1132400.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Policy renewal terms after the current cycle are unknown.
### ai_pattern_0005 — recurring_commitment: Municipal utilities
- Category: `utilities`; forecastable: `True`; source: `validated_ai`
- Source events: `event_106, event_114, event_122, event_130, event_138`
- Dates: `2025-03-07, 2025-04-07, 2025-05-07, 2025-06-07, 2025-07-07`
- Cadence: `monthly_calendar_like` (30 days); recent median: `2081730.85` IDR
- Range: `1830311.06`–`2143659.02`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Utility consumption varies seasonally, leading to changing monthly amounts.
### ai_pattern_0006 — recurring_commitment: Payroll credit
- Category: `salary`; forecastable: `True`; source: `validated_ai`
- Source events: `event_104, event_112, event_120, event_128, event_136`
- Dates: `2025-03-15, 2025-04-15, 2025-05-15, 2025-06-15, 2025-07-15`
- Cadence: `monthly_calendar_like` (30 days); recent median: `33345000.00` IDR
- Range: `33345000.00`–`33345000.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Future salary amounts are subject to employer adjustments.
### ai_pattern_0007 — recurring_commitment: Shared storage plan
- Category: `cloud_storage`; forecastable: `True`; source: `validated_ai`
- Source events: `event_111, event_119, event_127, event_135, event_143`
- Dates: `2025-03-13, 2025-04-13, 2025-05-13, 2025-06-13, 2025-07-13`
- Cadence: `monthly_calendar_like` (30 days); recent median: `369550.00` IDR
- Range: `369550.00`–`369550.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Subscription can be cancelled at any time by the user.
### ai_pattern_0008 — variable_spending: entertainment
- Category: `entertainment`; forecastable: `True`; source: `validated_ai`
- Source events: `event_110, event_118, event_126, event_134, event_142`
- Dates: `2025-03-15, 2025-04-15, 2025-05-15, 2025-06-15, 2025-07-15`
- Cadence: `monthly_calendar_like` (30 days); recent median: `1289187.40` IDR
- Range: `1193699.10`–`1367779.89`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Discretionary nature causes unpredictable month-to-month totals.
### ai_pattern_0009 — variable_spending: groceries
- Category: `groceries`; forecastable: `True`; source: `validated_ai`
- Source events: `event_145, event_146, event_147, event_148, event_149, event_150, event_151, event_152, event_153, event_154, event_155, event_156, event_157, event_158, event_159, event_160, event_161, event_162`
- Dates: `2025-02-10, 2025-02-20, 2025-03-02, 2025-03-12, 2025-03-22, 2025-04-01, 2025-04-11, 2025-04-21, 2025-05-01, 2025-05-11, 2025-05-21, 2025-05-31, 2025-06-10, 2025-06-20, 2025-06-30, 2025-07-10, 2025-07-20, 2025-07-30`
- Cadence: `fixed_day_cadence` (10 days); recent median: `2118766.78` IDR
- Range: `1418745.34`–`2477697.53`; observed weekly buckets: `18`; monthly buckets: `6`
- Uncertainty: Basket sizes and shopping frequency fluctuate based on household needs.
### ai_pattern_0010 — variable_spending: transport
- Category: `transport`; forecastable: `True`; source: `validated_ai`
- Source events: `event_163, event_164, event_165, event_166, event_167, event_168, event_169, event_170, event_171, event_172, event_173, event_174, event_175`
- Dates: `2025-02-11, 2025-02-25, 2025-03-11, 2025-03-25, 2025-04-08, 2025-04-22, 2025-05-06, 2025-05-20, 2025-06-03, 2025-06-17, 2025-07-01, 2025-07-15, 2025-07-29`
- Cadence: `biweekly_fixed_day` (14 days); recent median: `1318747.50` IDR
- Range: `995704.83`–`1440242.94`; observed weekly buckets: `13`; monthly buckets: `6`
- Uncertainty: Travel requirements may vary depending on commuting habits.
### ai_pattern_0011 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_176`
- Dates: `2025-02-12`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1166644.88` IDR
- Range: `1166644.88`–`1166644.88`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Single instance provides insufficient data for recurrence validation.
### ai_pattern_0012 — unsupported_recurring: Coffee shop
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_177`
- Dates: `2025-03-05`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1101709.76` IDR
- Range: `1101709.76`–`1101709.76`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Only a single occurrence is recorded.
### ai_pattern_0013 — unsupported_recurring: Weekend food delivery
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_178`
- Dates: `2025-03-26`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `935929.08` IDR
- Range: `935929.08`–`935929.08`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Lacks supporting follow-up events.
### ai_pattern_0014 — unsupported_recurring: Quick-service meal
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_179`
- Dates: `2025-04-16`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1271076.93` IDR
- Range: `1271076.93`–`1271076.93`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Insufficient occurrences to project recurrence.
### ai_pattern_0015 — unsupported_recurring: Takeaway order
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_180`
- Dates: `2025-05-07`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `971169.92` IDR
- Range: `971169.92`–`971169.92`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Single data point.
### ai_pattern_0016 — unsupported_recurring: Neighbourhood restaurant
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_181`
- Dates: `2025-05-28`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1111388.15` IDR
- Range: `1111388.15`–`1111388.15`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Cannot determine regularity from one event.
### ai_pattern_0017 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_182`
- Dates: `2025-06-18`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `947892.35` IDR
- Range: `947892.35`–`947892.35`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: No secondary matching events.
### ai_pattern_0018 — unsupported_recurring: Family dinner
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_183`
- Dates: `2025-07-09`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1043758.65` IDR
- Range: `1043758.65`–`1043758.65`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Single event record.
### ai_pattern_0019 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `validated_ai`
- Source events: `event_184`
- Dates: `2025-07-30`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `1204805.34` IDR
- Range: `1204805.34`–`1204805.34`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Lacks longitudinal data.

## Known future commitments

- `event_185` 2025-08-08 debit 1651100.00 IDR (Pending merchant debit)

## Evidence, changes, uncertainty, and assumptions

- Supported change `message_01`: `salary/amended` event `none`
- Review item: `['event_185']` — pattern contains an unknown source event ID
- Assumption: Available balance is the supplied current snapshot and historical transactions are not replayed against it.
- Assumption: Only settled historical events are used for historical statistics.
- Assumption: Pending credits, bonuses, commissions, refunds, prizes, and investment gains are not confirmed future income.
- Assumption: Historical maximum, median, and variability are descriptive statistics; none automatically establishes a reserve policy.


---

# Financial profile — user_01 as of 2024-03-03

Request scope: `request_01`. Home currency: `ZAR`.
Available balance snapshot: `58481.10`; minimum balance: `18000.00`.

## Preferences and constraints
- Protected: debt_repayment, education, groceries, rent
- Permitted reductions: dining
- Permitted stops: delivery_membership
- Accepted methods: full_payment

## Historical coverage
- Dates: `2023-09-08` through `2024-03-02`
- Settled observations: `100`
- Observed gaps (days): `[1, 1, 5, 1, 6, 1, 1, 5, 1, 2, 4, 0]`; missing buckets are not treated as zero.

## Patterns and statistics
### ai_pattern_0001 — recurring_commitment: Education loan instalment
- Category: `debt_repayment`; forecastable: `True`; source: `validated_ai`
- Source events: `event_04, event_10, event_16, event_22, event_29`
- Dates: `2023-10-11, 2023-11-11, 2023-12-11, 2024-01-11, 2024-02-11`
- Cadence: `monthly_calendar_like` (31 days); recent median: `3487.00` ZAR
- Range: `3487.00`–`3487.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Future instalments depend on remaining loan balance terms.
### ai_pattern_0002 — recurring_commitment: Professional training fee
- Category: `education`; forecastable: `True`; source: `validated_ai`
- Source events: `event_03, event_09, event_15, event_21, event_28`
- Dates: `2023-10-08, 2023-11-08, 2023-12-08, 2024-01-08, 2024-02-08`
- Cadence: `monthly_calendar_like` (31 days); recent median: `1821.60` ZAR
- Range: `1821.60`–`1821.60`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Duration of the training program is bounded by course completion.
### ai_pattern_0003 — recurring_commitment: Apartment rent transfer
- Category: `rent`; forecastable: `True`; source: `validated_ai`
- Source events: `event_01, event_07, event_13, event_19, event_26, event_32`
- Dates: `2023-10-02, 2023-11-02, 2023-12-02, 2024-01-02, 2024-02-02, 2024-03-02`
- Cadence: `monthly_calendar_like` (31 days); recent median: `5148.00` ZAR
- Range: `5148.00`–`5148.00`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: Subject to lease renewal terms.
### ai_pattern_0004 — recurring_commitment: Household utility payment
- Category: `utilities`; forecastable: `True`; source: `validated_ai`
- Source events: `event_02, event_08, event_14, event_20, event_27`
- Dates: `2023-10-06, 2023-11-06, 2023-12-06, 2024-01-06, 2024-02-06`
- Cadence: `monthly_calendar_like` (31 days); recent median: `1483.81` ZAR
- Range: `1386.17`–`1651.81`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Amounts fluctuate based on consumption.
### ai_pattern_0005 — recurring_commitment: Delivery service plan
- Category: `delivery_membership`; forecastable: `True`; source: `validated_ai`
- Source events: `event_06, event_12, event_18, event_24, event_31`
- Dates: `2023-10-13, 2023-11-13, 2023-12-13, 2024-01-13, 2024-02-13`
- Cadence: `monthly_calendar_like` (31 days); recent median: `306.90` ZAR
- Range: `306.90`–`306.90`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Subscription can be cancelled at user discretion.
### ai_pattern_0006 — recurring_commitment: Music service subscription
- Category: `music_subscription`; forecastable: `True`; source: `validated_ai`
- Source events: `event_05, event_11, event_17, event_23, event_30`
- Dates: `2023-10-11, 2023-11-11, 2023-12-11, 2024-01-11, 2024-02-11`
- Cadence: `monthly_calendar_like` (31 days); recent median: `235.40` ZAR
- Range: `235.40`–`235.40`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Discretionary digital subscription subject to cancellation.
### ai_pattern_0007 — variable_spending: dining
- Category: `dining`; forecastable: `True`; source: `validated_ai`
- Source events: `event_85, event_86, event_95, event_96, event_97`
- Dates: `2023-09-10, 2023-09-24, 2024-01-28, 2024-02-11, 2024-02-25`
- Cadence: `biweekly_fixed_day` (14 days); recent median: `1216.17` ZAR
- Range: `1016.12`–`1243.56`; observed weekly buckets: `5`; monthly buckets: `3`
- Uncertainty: Discretionary category prone to behavioral shifts.
### ai_pattern_0008 — variable_spending: groceries
- Category: `groceries`; forecastable: `True`; source: `validated_ai`
- Source events: `event_33, event_34, event_56, event_57, event_58`
- Dates: `2023-09-08, 2023-09-15, 2024-02-16, 2024-02-23, 2024-03-01`
- Cadence: `weekly_fixed_day` (7 days); recent median: `925.62` ZAR
- Range: `626.01`–`964.05`; observed weekly buckets: `5`; monthly buckets: `3`
- Uncertainty: Weekly totals vary based on household consumption needs.
### ai_pattern_0009 — variable_spending: transport
- Category: `transport`; forecastable: `True`; source: `validated_ai`
- Source events: `event_59, event_60, event_82, event_83, event_84`
- Dates: `2023-09-09, 2023-09-16, 2024-02-17, 2024-02-24, 2024-03-02`
- Cadence: `weekly_fixed_day` (7 days); recent median: `424.56` ZAR
- Range: `339.29`–`549.80`; observed weekly buckets: `5`; monthly buckets: `3`
- Uncertainty: Travel frequency and mode of transit can alter weekly costs.
### ai_pattern_0010 — unsupported_recurring: Card charge later reversed
- Category: `shopping`; forecastable: `False`; source: `validated_ai`
- Source events: `event_98`
- Dates: `2024-01-26`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `583.00` ZAR
- Range: `583.00`–`583.00`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: One-off transaction with matching credit reversal.
### ai_pattern_0011 — unsupported_recurring: Settled card charge reversal
- Category: `shopping`; forecastable: `False`; source: `validated_ai`
- Source events: `event_99`
- Dates: `2024-01-29`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `583.00` ZAR
- Range: `583.00`–`583.00`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Unique refund event linked to a single purchase.
### ai_pattern_0012 — unsupported_recurring: Prorated first salary
- Category: `salary`; forecastable: `False`; source: `validated_ai`
- Source events: `event_25`
- Dates: `2024-02-15`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `12826.00` ZAR
- Range: `12826.00`–`12826.00`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Prorated amount differs from standard full-month salary.
### ai_pattern_0013 — unsupported_recurring: Settled card purchase
- Category: `shopping`; forecastable: `False`; source: `validated_ai`
- Source events: `event_101`
- Dates: `2024-02-17`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `816.20` ZAR
- Range: `816.20`–`816.20`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Discretionary retail purchase without pattern history.

## Known future commitments

- `event_102` 2024-03-05 debit 567.60 ZAR (Pending fuel authorization)

## Evidence, changes, uncertainty, and assumptions

- Assumption: Available balance is the supplied current snapshot and historical transactions are not replayed against it.
- Assumption: Only settled historical events are used for historical statistics.
- Assumption: Pending credits, bonuses, commissions, refunds, prizes, and investment gains are not confirmed future income.
- Assumption: Historical maximum, median, and variability are descriptive statistics; none automatically establishes a reserve policy.


---

# Financial profile — user_05 as of 2025-11-06

Request scope: `request_05`. Home currency: `ZAR`.
Available balance snapshot: `46475.10`; minimum balance: `13100.00`.

## Preferences and constraints
- Protected: family_support, groceries, healthcare, rent
- Permitted reductions: shopping
- Permitted stops: cloud_storage
- Accepted methods: full_payment, installments, partial_payment

## Historical coverage
- Dates: `2025-05-13` through `2025-11-04`
- Settled observations: `80`
- Observed gaps (days): `[1, 6, 7, 1, 5, 1, 3, 4, 0, 1, 0, 1]`; missing buckets are not treated as zero.

## Patterns and statistics
### ai_pattern_0001 — recurring_commitment: Vehicle loan payment
- Category: `debt_repayment`; forecastable: `True`; source: `validated_ai`
- Source events: `event_361, event_369, event_377, event_385, event_393`
- Dates: `2025-06-11, 2025-07-11, 2025-08-11, 2025-09-11, 2025-10-11`
- Cadence: `monthly_calendar_like` (30 days); recent median: `968.00` ZAR
- Range: `968.00`–`968.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Exact loan completion date is not specified in the records.
### ai_pattern_0002 — recurring_commitment: Dependent care payment
- Category: `family_support`; forecastable: `True`; source: `validated_ai`
- Source events: `event_363, event_371, event_379, event_387, event_395`
- Dates: `2025-06-13, 2025-07-13, 2025-08-13, 2025-09-13, 2025-10-13`
- Cadence: `monthly_calendar_like` (30 days); recent median: `840.40` ZAR
- Range: `840.40`–`840.40`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Support obligations may change based on external circumstances.
### ai_pattern_0003 — recurring_commitment: Therapy appointment
- Category: `healthcare`; forecastable: `True`; source: `validated_ai`
- Source events: `event_362, event_370, event_378, event_386, event_394`
- Dates: `2025-06-10, 2025-07-10, 2025-08-10, 2025-09-10, 2025-10-10`
- Cadence: `monthly_calendar_like` (30 days); recent median: `721.44` ZAR
- Range: `632.59`–`777.27`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Amounts fluctuate slightly per session.
### ai_pattern_0004 — recurring_commitment: Apartment rent transfer
- Category: `rent`; forecastable: `True`; source: `validated_ai`
- Source events: `event_359, event_367, event_375, event_383, event_391, event_398`
- Dates: `2025-06-02, 2025-07-02, 2025-08-02, 2025-09-02, 2025-10-02, 2025-11-02`
- Cadence: `monthly_calendar_like` (31 days); recent median: `4972.00` ZAR
- Range: `4972.00`–`4972.00`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: Subject to lease renewal changes upon expiration.
### ai_pattern_0005 — recurring_commitment: Municipal utilities
- Category: `utilities`; forecastable: `True`; source: `validated_ai`
- Source events: `event_360, event_368, event_376, event_384, event_392`
- Dates: `2025-06-06, 2025-07-06, 2025-08-06, 2025-09-06, 2025-10-06`
- Cadence: `monthly_calendar_like` (30 days); recent median: `706.37` ZAR
- Range: `604.15`–`750.89`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Consumption levels vary seasonally.
### ai_pattern_0006 — recurring_commitment: Payroll credit
- Category: `salary`; forecastable: `True`; source: `validated_ai`
- Source events: `event_358, event_366, event_374, event_382`
- Dates: `2025-06-15, 2025-07-15, 2025-08-15, 2025-09-15`
- Cadence: `monthly_calendar_like` (31 days); recent median: `14740.00` ZAR
- Range: `14740.00`–`14740.00`; observed weekly buckets: `4`; monthly buckets: `4`
- Uncertainty: Employment status changed as indicated by the final payroll event later.
### ai_pattern_0007 — recurring_commitment: Cloud storage plan
- Category: `cloud_storage`; forecastable: `True`; source: `validated_ai`
- Source events: `event_364, event_372, event_380, event_388, event_396`
- Dates: `2025-06-12, 2025-07-12, 2025-08-12, 2025-09-12, 2025-10-12`
- Cadence: `monthly_calendar_like` (30 days); recent median: `113.30` ZAR
- Range: `113.30`–`113.30`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Subscription can be cancelled at any time.
### ai_pattern_0008 — variable_spending: shopping
- Category: `shopping`; forecastable: `True`; source: `validated_ai`
- Source events: `event_365, event_373, event_381, event_389, event_397`
- Dates: `2025-06-12, 2025-07-12, 2025-08-12, 2025-09-12, 2025-10-12`
- Cadence: `monthly_calendar_like` (30 days); recent median: `404.24` ZAR
- Range: `362.09`–`422.67`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: Discretionary amounts vary by month.
### ai_pattern_0009 — unsupported_recurring: Final employer payroll
- Category: `salary`; forecastable: `False`; source: `validated_ai`
- Source events: `event_390`
- Dates: `2025-10-15`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `14740.00` ZAR
- Range: `14740.00`–`14740.00`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Indicates a final payment, meaning future occurrence is unsupported.
### pattern_0008 — variable_spending: groceries
- Category: `groceries`; forecastable: `True`; source: `deterministic`
- Source events: `event_399, event_400, event_401, event_402, event_403, event_404, event_405, event_406, event_407, event_408, event_409, event_410, event_411, event_412, event_413, event_414, event_415, event_416, event_417, event_418, event_419, event_420, event_421, event_422, event_423, event_424`
- Dates: `2025-05-13, 2025-05-20, 2025-05-27, 2025-06-03, 2025-06-10, 2025-06-17, 2025-06-24, 2025-07-01, 2025-07-08, 2025-07-15, 2025-07-22, 2025-07-29, 2025-08-05, 2025-08-12, 2025-08-19, 2025-08-26, 2025-09-02, 2025-09-09, 2025-09-16, 2025-09-23, 2025-09-30, 2025-10-07, 2025-10-14, 2025-10-21, 2025-10-28, 2025-11-04`
- Cadence: `weekly_fixed_day` (7 days); recent median: `697.00` ZAR
- Range: `515.40`–`853.42`; observed weekly buckets: `26`; monthly buckets: `7`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0010 — variable_spending: transport
- Category: `transport`; forecastable: `True`; source: `deterministic`
- Source events: `event_425, event_426, event_427, event_428, event_429, event_430, event_431, event_432, event_433, event_434, event_435, event_436, event_437`
- Dates: `2025-05-14, 2025-05-28, 2025-06-11, 2025-06-25, 2025-07-09, 2025-07-23, 2025-08-06, 2025-08-20, 2025-09-03, 2025-09-17, 2025-10-01, 2025-10-15, 2025-10-29`
- Cadence: `biweekly_fixed_day` (14 days); recent median: `383.00` ZAR
- Range: `311.00`–`504.23`; observed weekly buckets: `13`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations

## Known future commitments


## Evidence, changes, uncertainty, and assumptions

- Assumption: Available balance is the supplied current snapshot and historical transactions are not replayed against it.
- Assumption: Only settled historical events are used for historical statistics.
- Assumption: Pending credits, bonuses, commissions, refunds, prizes, and investment gains are not confirmed future income.
- Assumption: Historical maximum, median, and variability are descriptive statistics; none automatically establishes a reserve policy.


---

# Financial profile — user_20 as of 2026-02-07

Request scope: `request_20`. Home currency: `INR`.
Available balance snapshot: `102609.05`; minimum balance: `64500.00`.

## Preferences and constraints
- Protected: education, housing, utilities
- Permitted reductions: dining, entertainment
- Permitted stops: cloud_storage
- Accepted methods: full_payment, installments, partial_payment

## Historical coverage
- Dates: `2025-08-13` through `2026-02-06`
- Settled observations: `84`
- Observed gaps (days): `[1, 1, 8, 5, 5, 0, 3, 0, 1, 1, 2, 2]`; missing buckets are not treated as zero.

## Patterns and statistics
### ai_pattern_0001 — one_time: Purchase awaiting refund
- Category: `shopping`; forecastable: `False`; source: `validated_ai`
- Source events: `event_1784`
- Dates: `2026-01-15`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `8640.00` INR
- Range: `8640.00`–`8640.00`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: Refund status is pending and delayed.
### pattern_0001 — recurring_commitment: School fee payment
- Category: `education`; forecastable: `True`; source: `deterministic`
- Source events: `event_1705, event_1713, event_1721, event_1729, event_1737`
- Dates: `2025-09-07, 2025-10-07, 2025-11-07, 2025-12-07, 2026-01-07`
- Cadence: `monthly_calendar_like` (30 days); recent median: `8740.00` INR
- Range: `8740.00`–`8740.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0002 — recurring_commitment: Family healthcare expense
- Category: `healthcare`; forecastable: `True`; source: `deterministic`
- Source events: `event_1706, event_1714, event_1722, event_1730, event_1738`
- Dates: `2025-09-09, 2025-10-09, 2025-11-09, 2025-12-09, 2026-01-09`
- Cadence: `monthly_calendar_like` (30 days); recent median: `6505.49` INR
- Range: `5907.73`–`6654.33`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0003 — recurring_commitment: Home association fee
- Category: `housing`; forecastable: `True`; source: `deterministic`
- Source events: `event_1702, event_1710, event_1718, event_1726, event_1734, event_1741`
- Dates: `2025-09-02, 2025-10-02, 2025-11-02, 2025-12-02, 2026-01-02, 2026-02-02`
- Cadence: `monthly_calendar_like` (31 days); recent median: `7950.00` INR
- Range: `7950.00`–`7950.00`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0004 — recurring_commitment: Household insurance
- Category: `insurance`; forecastable: `True`; source: `deterministic`
- Source events: `event_1704, event_1712, event_1720, event_1728, event_1736, event_1743`
- Dates: `2025-09-06, 2025-10-06, 2025-11-06, 2025-12-06, 2026-01-06, 2026-02-06`
- Cadence: `monthly_calendar_like` (31 days); recent median: `3290.00` INR
- Range: `3290.00`–`3290.00`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0005 — recurring_commitment: Municipal utilities
- Category: `utilities`; forecastable: `True`; source: `deterministic`
- Source events: `event_1703, event_1711, event_1719, event_1727, event_1735, event_1742`
- Dates: `2025-09-05, 2025-10-05, 2025-11-05, 2025-12-05, 2026-01-05, 2026-02-05`
- Cadence: `monthly_calendar_like` (31 days); recent median: `7777.08` INR
- Range: `6848.62`–`8058.75`; observed weekly buckets: `6`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0006 — recurring_commitment: Payroll credit
- Category: `salary`; forecastable: `True`; source: `deterministic`
- Source events: `event_1701, event_1709, event_1717, event_1725, event_1733`
- Dates: `2025-09-15, 2025-10-15, 2025-11-15, 2025-12-15, 2026-01-15`
- Cadence: `monthly_calendar_like` (30 days); recent median: `108000.00` INR
- Range: `108000.00`–`108000.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0007 — recurring_commitment: Shared storage plan
- Category: `cloud_storage`; forecastable: `True`; source: `deterministic`
- Source events: `event_1708, event_1716, event_1724, event_1732, event_1740`
- Dates: `2025-09-11, 2025-10-11, 2025-11-11, 2025-12-11, 2026-01-11`
- Cadence: `monthly_calendar_like` (30 days); recent median: `365.00` INR
- Range: `365.00`–`365.00`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0008 — variable_spending: entertainment
- Category: `entertainment`; forecastable: `True`; source: `deterministic`
- Source events: `event_1707, event_1715, event_1723, event_1731, event_1739`
- Dates: `2025-09-13, 2025-10-13, 2025-11-13, 2025-12-13, 2026-01-13`
- Cadence: `monthly_calendar_like` (30 days); recent median: `2115.92` INR
- Range: `1949.86`–`2298.76`; observed weekly buckets: `5`; monthly buckets: `5`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0009 — variable_spending: groceries
- Category: `groceries`; forecastable: `True`; source: `deterministic`
- Source events: `event_1744, event_1745, event_1746, event_1747, event_1748, event_1749, event_1750, event_1751, event_1752, event_1753, event_1754, event_1755, event_1756, event_1757, event_1758, event_1759, event_1760, event_1761`
- Dates: `2025-08-13, 2025-08-23, 2025-09-02, 2025-09-12, 2025-09-22, 2025-10-02, 2025-10-12, 2025-10-22, 2025-11-01, 2025-11-11, 2025-11-21, 2025-12-01, 2025-12-11, 2025-12-21, 2025-12-31, 2026-01-10, 2026-01-20, 2026-01-30`
- Cadence: `fixed_day_cadence` (10 days); recent median: `3727.46` INR
- Range: `2812.26`–`4719.22`; observed weekly buckets: `18`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0010 — variable_spending: transport
- Category: `transport`; forecastable: `True`; source: `deterministic`
- Source events: `event_1762, event_1763, event_1764, event_1765, event_1766, event_1767, event_1768, event_1769, event_1770, event_1771, event_1772, event_1773, event_1774`
- Dates: `2025-08-14, 2025-08-28, 2025-09-11, 2025-09-25, 2025-10-09, 2025-10-23, 2025-11-06, 2025-11-20, 2025-12-04, 2025-12-18, 2026-01-01, 2026-01-15, 2026-01-29`
- Cadence: `biweekly_fixed_day` (14 days); recent median: `2837.54` INR
- Range: `2046.25`–`3243.84`; observed weekly buckets: `13`; monthly buckets: `6`
- Uncertainty: deterministic cadence is supported by at least three settled observations
### pattern_0011 — unsupported_recurring: Takeaway order
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1775`
- Dates: `2025-08-15`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `3150.77` INR
- Range: `3150.77`–`3150.77`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0012 — unsupported_recurring: Quick-service meal
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1776`
- Dates: `2025-09-05`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `3075.11` INR
- Range: `3075.11`–`3075.11`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0013 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1777`
- Dates: `2025-09-26`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `3365.58` INR
- Range: `3365.58`–`3365.58`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0014 — unsupported_recurring: Coffee shop
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1778`
- Dates: `2025-10-17`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `4270.04` INR
- Range: `4270.04`–`4270.04`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0015 — unsupported_recurring: Takeaway order
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1779`
- Dates: `2025-11-07`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `2857.78` INR
- Range: `2857.78`–`2857.78`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0016 — unsupported_recurring: Family dinner
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1780`
- Dates: `2025-11-28`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `4308.23` INR
- Range: `4308.23`–`4308.23`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0017 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1781`
- Dates: `2025-12-19`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `2629.91` INR
- Range: `2629.91`–`2629.91`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0018 — unsupported_recurring: Neighbourhood restaurant
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1782`
- Dates: `2026-01-09`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `3352.75` INR
- Range: `3352.75`–`3352.75`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast
### pattern_0020 — unsupported_recurring: Bakery and snacks
- Category: `dining`; forecastable: `False`; source: `deterministic`
- Source events: `event_1783`
- Dates: `2026-01-30`
- Cadence: `insufficient_or_irregular_history` (None days); recent median: `3803.95` INR
- Range: `3803.95`–`3803.95`; observed weekly buckets: `1`; monthly buckets: `1`
- Uncertainty: insufficient repeated source history for a recurring forecast

## Known future commitments

- `event_1786` 2026-02-09 debit 704.05 INR (Outstanding telecom bill)
- `event_1787` 2026-02-08 debit 4470.00 INR (Pending online order charge)

## Evidence, changes, uncertainty, and assumptions

- Review item: `message_14` — unresolved evidence status or ambiguity
- Review item: `['event_1785']` — pattern contains an unknown source event ID
- Review item: `['event_1786']` — pattern contains an unknown source event ID
- Review item: `['event_1787']` — pattern contains an unknown source event ID
- Assumption: Available balance is the supplied current snapshot and historical transactions are not replayed against it.
- Assumption: Only settled historical events are used for historical statistics.
- Assumption: Pending credits, bonuses, commissions, refunds, prizes, and investment gains are not confirmed future income.
- Assumption: Historical maximum, median, and variability are descriptive statistics; none automatically establishes a reserve policy.
