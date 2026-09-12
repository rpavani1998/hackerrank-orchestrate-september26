# Buy or Wait? — Progress and Correctness Baseline

Generated from the current repository state on branch `main`.

## Traceability

- Branch: `main`
- Current tracked production file: `code/main.py`
- Sample-comparison checkpoint: `5fcccc1` (`test: add sample comparison harness and baseline`)
- No tracked production diff was present before the checkpoint commits.
- Remaining unrelated/uncommitted paths are listed in [Change inventory](#change-inventory).

This report records the state after the initial implementation, architecture review, and sample-comparison baseline. No correction factor or forecasting-policy change was made. The harness/baseline and this report are intentionally separate local checkpoints; no push was performed.

## Current implementation

The solution is a deterministic, dependency-free Python engine. It does not call an LLM, vision API, hosted model, network service, or external banking service.

### Entry points

The production entry point is:

```text
code/main.py:main()
```

It loads `dataset/requests.csv`, evaluates every request with `Agent.decide()`, validates the generated rows, and writes the root-level `output.csv`.

The diagnostic entry point is:

```text
code/compare_samples.py:main()
```

It loads all rows from `dataset/sample_requests.csv`, calls the existing engine directly, prints comparisons, and traces `request_02`. It deliberately does not call production `main()` and does not write `output.csv`.

### Architecture and execution flow

```mermaid
flowchart LR
    csv["dataset CSV files"] --> data["Data loader"]
    images["IMAGE_AMOUNTS map"] --> data
    data --> typed["Profile / Event / Option structures"]
    typed --> evidence["Payroll message + image evidence"]
    typed --> projection["Explicit + recurring projection"]
    evidence --> projection
    projection --> replay["Daily balance replay"]
    replay --> safe["Safe amount + earliest full date"]
    safe --> plans["Plan generation and spending changes"]
    projection --> plans
    plans --> rank["Plan ranking"]
    rank --> decide["Agent.decide"]
    decide --> validate["validate"]
    validate --> output["output.csv"]
```

Major components in `code/main.py`:

- `Data.__init__()` loads profiles, requests, events, messages, options, and exchange rates, then builds indexes by user and request.
- `Data._profiles()` parses user balances, minimums, protected categories, flexible categories, accepted payment methods, and installment limits.
- `Data._events()` parses financial events and fills blank amounts from the hardcoded image facts below.
- `Data._options()` parses provider payment options.
- `Data.convert()` applies direct, inverse, or fallback dated exchange rates.
- `Agent.relevant_messages()` filters messages relevant to a user/request and request date.
- `Agent.message_facts()` uses a narrow regular expression to extract dated payroll amounts.
- `Agent.explicit_projection()` includes future settled, pending, and scheduled cash events while excluding failed, cancelled, unrealized, and pending-credit events.
- `Agent.recurring_projection()` infers approximate weekly, biweekly, monthly, or two-month recurrences from historical settled events.
- `Agent.projections()` combines explicit events, inferred events, and payroll-message facts while removing some same-key/same-date duplicates.
- `Agent.replay()` applies cash events day by day, credits before debits, then proposed payments, stopping at the first minimum-balance violation.
- `Agent.safe_amount()` calculates unchanged-baseline headroom above the minimum balance.
- `Agent.earliest_full()` tries a full payment on each day of the 90-day window.
- `Agent.eligible_changes()` finds permitted flexible recurring events.
- `Agent.plans()` generates full, partial, installment, wait, and changed-spending plans.
- `Agent.rank()` applies the implemented plan ordering.
- `Agent.decide()` selects a plan and formats all required output fields.
- `validate()` checks output shape, bounds, enums, payment totals, installment schedule equality, and basic spending-change syntax.

### Hardcoded image facts

Runtime image extraction is not implemented. The 16 supplied image amounts were manually transcribed into `IMAGE_AMOUNTS` in `code/main.py` and joined to events using `images.csv.related_event_id`:

```text
image_01: 4365000
image_02: 100000
image_03: 41272
image_04: 2854
image_05: 704.05
image_06: 79679.26
image_07: 8528.10
image_08: 15339
image_09: 723
image_10: 79679.26
image_11: 3650
image_12: 33.50
image_13: 2298
image_14: 4593
image_15: 9968
image_16: 393.22
```

If an amount is blank and there is no mapped image fact, `_events()` skips the event rather than treating it as zero or failing the run.

### Limited message parsing

Only explicit, dated payroll-like messages are parsed. `message_facts()` recognizes a limited set of English/Indonesian payroll words and extracts one amount and one ISO date. It does not fully interpret cancellations, rent amendments, provider notices, refunds, bank disputes, or foreign-currency message amounts. The stated currency is not retained in the extracted tuple, so the parser effectively treats the extracted value as a home-currency amount.

### Known implementation limitations

- `linked_event_id` is loaded but no full lifecycle graph is reconciled. Status filtering exists, but linked duplicates, replacement events, failed retries, amendments, and settlement precedence are not comprehensively resolved.
- `request_text`, `request_type`, and profile `financial_priorities` are loaded or available but do not materially influence the final decision.
- Exchange-rate fallback uses the latest rate on or before the settlement date when an exact rate is unavailable, rather than failing or proving that the challenge permits the fallback.
- Historical recurring expenses are grouped mostly by category and use a heuristic recent median or upper-quartile amount. This is not proven to match the organizer's reserve policy.
- Recurring income is restricted to descriptions containing salary/payroll-like terms, while commission and gig-like streams are excluded by keyword.
- `max_installment_months` is approximated by comparing the number of payments to the maximum months; this is not the same as measuring schedule duration.
- The validator uses Python `assert` statements, which can be disabled with optimization flags, and it does not fully validate spending-change targets or every provider-option invariant.
- Decision explanations are deterministic but may omit the selected spending changes.
- Existing tests do not cover all lifecycle, recurrence, message, currency, boundary, ranking, and validation cases.

## Completed work

### Initial implementation

Implemented the deterministic engine in `code/main.py` with:

- Decimal monetary parsing and output formatting
- Profile/event/message/option/rate loading
- Source-linked manual image amounts
- Pending debit and pending credit treatment
- Explicit future-event projection
- Heuristic recurrence projection
- Payroll-message extraction
- Daily minimum-balance replay
- Safe-amount and earliest-full-payment calculations
- Full, partial, installment, wait, and not-recommended plans
- Flexible spending changes limited by profile permissions
- Output validation and CSV generation

### Architecture review

Inspected the implementation in execution order and identified the distinction between:

- implemented deterministic arithmetic and planning
- manually transcribed image evidence
- limited payroll-only message parsing
- heuristic recurrence forecasting
- missing linked-event reconciliation
- missing AI/model integration
- incomplete independent validation

### Diagnostic harness

Added `code/compare_samples.py` without changing production financial logic. It:

- evaluates all 25 solved samples using the existing engine
- compares Decimal amounts numerically
- compares payment plans as ordered date/amount schedules
- records exceptions rather than skipping failures
- checks explanation consistency independently of exact wording
- traces `request_02` with a full diagnostic ledger

The reproducible output from the baseline run is saved at:

```text
evaluation/sample_baseline.txt
```

## Baseline results

The diagnostic run processed all 25 samples with no exceptions.

| Field | Matches |
|---|---:|
| `amount_safe_to_pay` | 3/25 |
| `affordability_status` | 19/25 |
| `recommended_payment_method` | 21/25 |
| `payment_plan` | 21/25 |
| `earliest_date_for_full_payment` | 17/25 |
| `spending_changes_needed` | 20/25 |
| explanation consistency | 25/25 |

The exactly matching requests across the compared fields were:

```text
request_09
request_12
request_16
```

### Complete mismatch table

For monetary rows, `difference` is `actual - expected`. Payment-plan comparisons are structural, so harmless decimal formatting differences are not counted as mismatches.

| Request | Mismatched fields | Expected amount | Actual amount | Difference |
|---|---|---:|---:|---:|
| request_01 | amount, status, method, plan, earliest date | 25256 | 6242.62 | -19013.38 |
| request_02 | amount | 17229139.2 | 17864721.20 | +635582.00 |
| request_03 | amount | 873000 | 1089018.06 | +216018.06 |
| request_04 | amount | 8401800 | 10132985.41 | +1731185.41 |
| request_05 | amount | 737 | 0 | -737 |
| request_06 | amount, status, earliest date, changes | 603.3 | 620.40 | +17.10 |
| request_07 | amount | 87170.56 | 94391.34 | +7220.78 |
| request_08 | amount, status, method, plan, earliest date | 284.57 | 369.70 | +85.13 |
| request_10 | amount | 12700 | 0 | -12700 |
| request_11 | amount, status, earliest date, changes | 12510645 | 13110000 | +599355 |
| request_13 | amount, status, method, plan, earliest date | 433.4 | 325.23 | -108.17 |
| request_14 | amount | 597.74 | 0 | -597.74 |
| request_15 | amount | 83.05 | 0 | -83.05 |
| request_17 | amount, earliest date, changes | 243849.58 | 237498.83 | -6350.75 |
| request_18 | amount | 462 | 646.65 | +184.65 |
| request_19 | amount, method, plan, earliest date | 28820 | 39660 | +10840 |
| request_20 | amount | 5400 | 17006.40 | +11606.40 |
| request_21 | amount, status, earliest date, changes | 1543.35 | 1574.40 | +31.05 |
| request_22 | amount, changes | 475.46 | 469.81 | -5.65 |
| request_23 | amount | 9152 | 10113.63 | +961.63 |
| request_24 | amount | 13420 | 13080.61 | -339.39 |
| request_25 | amount | 1425000 | 2388502.63 | +963502.63 |

## Request-02 investigation

The diagnostic used solved sample row `request_02` directly with the existing `Agent`, without invoking production `main()`.

### Starting state

```text
request date: 2025-08-05
forecast end: 2025-11-03
home currency: IDR
starting balance: 60,383,889.20 IDR
protected minimum: 29,158,400 IDR
requested amount: 46,018,000 IDR
desired completion date: 2025-10-10
accepted methods: partial_payment, installments
max installment months: 7
```

### Observed low point

The current engine's full baseline replay observed:

```text
lowest baseline balance: 47,023,121.20 IDR
lowest balance date: 2025-08-13
actual safe amount: 17,864,721.20 IDR
sample expected safe amount: 17,229,139.20 IDR
difference: +635,582.00 IDR
```

The sample's expected safe amount implies a balance of:

```text
29,158,400 + 17,229,139.20 = 46,387,539.20 IDR
```

That arithmetic does not establish that the expected low point occurred on 2025-08-13; the expected low-point date is unknown from the sample output alone.

### Cash-flow events leading to the observed low point

These are the eight projected debits through 2025-08-13. Inferred events retain their historical source ID; `event_185` is an explicit pending debit.

| Date | Direction | Category | Amount | Source ID | Source description/status |
|---|---|---|---:|---|---|
| 2025-08-07 | debit | utilities | 2,081,730.85 | inferred from `event_138` | Municipal utilities / settled |
| 2025-08-08 | debit | insurance | 1,132,400 | inferred from `event_139` | Household insurance / settled |
| 2025-08-08 | debit | shopping | 1,651,100 | explicit `event_185` | Pending merchant debit / pending |
| 2025-08-09 | debit | education | 3,040,000 | inferred from `event_140` | Course tuition / settled |
| 2025-08-09 | debit | groceries | 2,218,141.61 | inferred from `event_162` | Supermarket basket / settled |
| 2025-08-11 | debit | healthcare | 1,538,498.10 | inferred from `event_141` | Clinic payment / settled |
| 2025-08-12 | debit | transport | 1,329,347.44 | inferred from `event_175` | Metro and bus fares / settled |
| 2025-08-13 | debit | cloud storage | 369,550 | inferred from `event_143` | Shared storage plan / settled |

Total depletion through the observed low point:

```text
13,360,768.00 IDR
```

The calculation is:

```text
60,383,889.20 - 13,360,768.00 = 47,023,121.20 IDR
```

### Salary amendment

The relevant evidence is `message_01`, sent on 2025-07-29 by the employer. It states that monthly salary increased to:

```text
42,750,000 IDR effective 2025-08-15
```

`Agent.message_facts()` extracted:

```text
2025-08-15: 42,750,000 IDR
```

The salary amendment does not affect the observed low point because the low point occurs on August 13. The engine generated one message salary and removed one same-date inferred salary projection so the amendment was not double-counted.

### Conversions, duplicates, and recurrence handling in this trace

- All request-02 events are already in IDR; no currency conversion occurred.
- There were 1 explicit future projection and 38 inferred recurring projections before final combination.
- No recurring projection was removed for an explicit same-date/category/direction collision.
- One same-date inferred salary was removed because of the employer message amendment.
- No linked-event graph reconciliation occurred. `linked_event_id` is loaded by the engine, but no linked event was resolved in this trace.
- The pending debit was included; pending credits would be excluded by `status_counts_as_cash()`.

## Evidence versus hypotheses

### Confirmed by code and diagnostic output

1. The current engine uses the eight listed cash-flow events to reach its observed 2025-08-13 low point.
2. The current engine's safe amount is the observed low balance minus the protected minimum.
3. The current engine uses a recent upper-quartile-like value for variable expense recurrences in `Agent.recurring_projection()`.
4. The salary message is parsed as a dated IDR credit on 2025-08-15.
5. The salary message replaces one same-date inferred salary projection.
6. No currency conversion or linked-event reconciliation occurs for request 02.
7. The current engine does not use an AI model or external service.

### Possible explanations, not established facts

Historical maxima are an unverified hypothesis. If the current projected values are replaced by historical category maxima for early variable categories, the additional reserve would be:

| Category | Current projected amount | Historical maximum | Difference |
|---|---:|---:|---:|
| utilities | 2,081,730.85 | 2,143,659.02 | +61,928.17 |
| groceries | 2,218,141.61 | 2,477,697.53 | +259,555.92 |
| healthcare | 1,538,498.10 | 1,641,668.72 | +103,170.62 |
| transport | 1,329,347.44 | 1,440,242.94 | +110,895.50 |
| **total** |  |  | **+535,550.21** |

This explains much of the 635,582 IDR discrepancy, but it does not prove that the organizer uses historical maxima. The remaining:

```text
635,582.00 - 535,550.21 = 100,031.79 IDR
```

has no single obvious source event in the current trace and remains unexplained. No multiplier or hardcoded correction was applied.

The expected safe amount does not reveal the expected low-point date. It is not valid to assume that the expected reserve was accumulated by exactly the same August 13 event sequence.

## Verification

### Checks run during this documentation step

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/compare_samples.py > evaluation/sample_baseline.txt
```

Observed result:

```text
exit status: 0
samples: 25
exceptions: 0
report lines: 112
```

The diagnostic did not invoke `code/main.py:main()` and did not overwrite `output.csv`.

Git state was also inspected before checkpointing:

```text
starting commit: 044845a8befe36a01248311dc03db351632f5135
sample-comparison checkpoint: 5fcccc1
branch: main
tracked production diff: none
```

### Previously reported checks, not rerun during this step

The following checks were reported as passing before this documentation step:

```bash
python3 code/main.py
python3 -m unittest discover -s code -p 'test_*.py'
unzip -tq code.zip
```

Previously reported results included:

- 250 output rows generated
- required eight-column output header
- amount bounds valid
- 7 unit tests passing
- `code.zip` archive valid

### Existing test coverage

`code/test_main.py` currently covers:

- selected image-only amounts are nonzero
- direct and inverse exchange conversion
- pending debit inclusion
- one installment schedule match
- partial-payment shape if the engine happens to select partial payment
- below-floor replay rejection
- output row count, bounds, and enum membership

Important untested behavior includes:

- linked lifecycle reconciliation and duplicate settlement handling
- failed debit followed by retry
- cancellation/amendment precedence
- exact settlement-date exchange-rate enforcement
- unresolved image facts
- foreign-currency message amounts
- non-payroll message interpretation
- recurrence amount policy across representative users
- 90-day and same-day boundary semantics
- installment duration versus maximum months
- exact spending-change target validation
- plan ranking across all competing plan types
- explanation details when spending changes are selected

## Change inventory

### Committed checkpoint

The sample-comparison harness and its reproducible baseline were committed together:

```text
5fcccc1 test: add sample comparison harness and baseline
  code/compare_samples.py
  evaluation/sample_baseline.txt
```

### Remaining untracked/unrelated paths

After that checkpoint, the current `git status --short` reports these untracked paths:

```text
.gitignore
code.zip
code/README.md
code/test_main.py
evaluation/progress_report.md
evaluation/usage_report.md
output.csv
```

These are intentionally not part of the harness checkpoint. `log.txt` is ignored by `.gitignore` and remains the required transcript artifact.

### Production/output preservation

During the diagnostic and documentation step:

- `code/main.py` was not edited.
- No production extraction, forecasting, or payment logic was changed.
- No correction factor was added.
- No production logic commit was created and no push was performed.
- Two local, reviewable checkpoints were created: the harness/baseline checkpoint and this documentation checkpoint.
- `output.csv` was not targeted or overwritten.
- The diagnostic artifact and report were created/updated without regenerating predictions.

## Next steps

Before changing forecasting policy, audit representative failures:

1. `request_02`
   - Focus: upper-quartile recurrence amounts, the August 13 low point, and the unexplained 100,031.79 IDR residual.
   - Relevant functions: `Agent.recurring_projection()`, `Agent.replay()`, `Agent.safe_amount()`.
   - Verification: source-linked event ledger and a focused recurrence-policy test.

2. `request_01`
   - Focus: why the current forecast makes the request not recommended while the sample permits full payment.
   - Relevant functions: `Agent.recurring_projection()`, `Agent.safe_amount()`, and `Agent.earliest_full()`.
   - Verification: separate fixed commitments, essential variable spending, and flexible spending in the trace; do not change policy until the reserve difference is source-explained.

3. `request_05` and `request_20`
   - Focus: cases where the current engine returns zero or substantially different safe amounts and where pending/image-linked obligations may dominate.
   - Relevant functions: `Data._events()`, `Agent.explicit_projection()`, `Agent.recurring_projection()`, and `Agent.safe_amount()`.
   - Verification: trace pending debits, image-derived amounts, failed/cancelled records, and recurrence windows independently.

The smallest justified next action is a read-only audit report for these four requests, not a production forecast change. Once the audits identify a common source-backed rule, add a focused regression test before changing `Agent.recurring_projection()` or `Agent.safe_amount()`.
