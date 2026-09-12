# Component audit — diagnostic checkpoint

This is a component-first audit after commit `7c1d996`, plus a later salary
occurrence-reconciliation checkpoint in `Agent.reconcile_explicit_inferred_credits()`.
Controlled checks remain diagnostic and do not regenerate `output.csv` or
`evaluation/sample_baseline.txt`.

Salary merge coverage is in `code/test_main.py` (placeholder vs named payroll,
two employers, delayed payday, one-time amount, permanent amendment, ambiguous
placeholder, unrelated subscriptions, idempotence). The audit script itself is
unchanged; its merchant-recurrence confirmed failure still stands.

The controlled checks are executable with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/component_audit_checks.py
```

The check script uses synthetic events, messages, balances, plans, and rates for
component contracts. It does not invoke OpenRouter. Live model-quality results
are taken separately from `evaluation/message_extraction_evaluation.md`; mocked
adapter tests are not counted as model-quality evidence.

## Status definitions

- **Verified for tested cases** — an independently justified controlled case passed.
- **Confirmed failure** — a controlled or live-quality case has an expected result that the component did not meet.
- **Not implemented** — the requested capability is absent, rather than merely failing a case.
- **Insufficient coverage** — the available checks pass a narrow contract, but do not establish the full requested behavior.
- **Ambiguous requirement** — the challenge specification does not establish one expected answer; no value was invented to force a pass.

## Component map

| Component | Files/functions | Inputs | Outputs | Dependencies | Intended contract | Implementation state |
|---|---|---|---|---|---|---|
| CSV loading, parsing, and identifier joins | `code/main.py`: `csv_rows`, `Data.__init__`, `_profiles`, `_events`, `_options`, `_rates` | Dataset CSVs; `user_id`, `request_id`, `event_id`, `related_event_id` | Typed `Profile`, `Event`, `Option`, rate map; user/request indexes | CSV headers, identifier values, `IMAGE_AMOUNTS` for blank event amounts | Parse participant files without silently corrupting joins; preserve blank amounts as unresolved unless supported image evidence exists | Structural joins verified for 275 profile/request IDs, 25,342 events, 215 messages; blank amounts depend on manual image map |
| Deterministic message extraction | `code/main.py`: `Agent.message_facts` | Relevant message text and home currency | `(date, amount, source)` payroll tuples | Regex, English/Indonesian payroll keywords, ISO dates | Extract only explicit supported dated payroll facts; do not invent missing dates/currencies | Narrow dated payroll case verified; amount-only/date-only and non-payroll message classes are not implemented |
| AI message extraction | `code/evaluate_messages.py`; `code/evidence_extraction.py`: `OpenRouterAdapter`, `EvidenceExtractor` | Untrusted message content plus authoritative source metadata | Validated `EvidenceFact`, usage/cost/cache metadata | OpenRouter model, structured-output schema, cache | Return source-grounded fields without following embedded instructions; model quality is separate from adapter correctness | Live 19-message quality is measured separately; semantic misses remain |
| Image extraction / manual image lookup | `code/main.py`: `IMAGE_AMOUNTS`, `Data._events` | `images.csv`, PNG files, event IDs | Event amount from manual map | Hand-transcribed constants; no image library | Read visible amount roles from each supplied image; distinguish total, paid, and due | Automated extraction is **not implemented**; manual lookup covers 16/16 linked images only |
| Evidence schema validation | `code/evidence_extraction.py`: `EvidenceFact.from_mapping`, `EvidenceDate`, `EvidenceSource` | Structured mapping and source references | Validated fact or `EvidenceValidationError` | Identifier regexes, type/status enums, date/amount checks | Reject malformed identifiers, invalid amounts/currencies/dates, unknown enums, and extra/missing fields | Valid/invalid schema cases verified |
| Evidence semantic validation | `code/evidence_extraction.py`: `EvidenceFact.from_mapping`, `validate_evidence_semantics`, `apply_evidence_fact` | Valid schema fields, action/status/type combinations, source wording | Fact/application result | New `transaction_type`, `update_status`, legacy `action` fields | Ensure fields do not contradict one another and preserve unresolved meaning | Authoritative status-to-action mapping and pending/delayed source-wording checks are verified |
| Request-date visibility and scope | `code/main.py`: `Agent.relevant_messages`; `code/evidence_extraction.py`: `apply_evidence_fact`, `load_evidence_facts` | User/request IDs, source sent date, request date, event link | Relevant messages or `not_visible`/scope rejection | Message metadata and source links | Only evidence visible by request date and scoped to user/request may affect a request | Future-date and mismatched-request controlled cases verified |
| Conflict resolution / lifecycle reconciliation | `code/main.py`: `Event.linked_event_id`, `status_counts_as_cash`, `explicit_projection`, `reconcile_explicit_inferred_credits`; `evidence_extraction.py`: `EvidenceLedger` | Linked event rows, statuses, replacements, refunds, retries, duplicate notices, scheduled vs inferred salary | Cash projections and duplicate application decisions | Event status, links, source precedence, salary placeholder/delay markers | Resolve cancellation, settlement, amendment, replacement, duplicate, retry, and refund lifecycles by explicit precedence | Scheduled `Next confirmed salary` now replaces the matching inferred payday; a full linked-event graph is still not implemented |
| Applying evidence to events and recurring streams | `code/evidence_extraction.py`: `apply_evidence_fact`; `code/main.py`: `load_evidence_facts`, `salary_evidence_applications`, `expand_resumed_salary`, `evidence_salary_end_dates` | Validated facts, source metadata, event/series context | Status-only application or salary timeline projections including resumed streams | Ledger, visibility, deterministic currency conversion, recurrence scope | Apply supported amendments to the correct event/series without double counting; keep unresolved facts inert | Resumed monthly salary, one-off confirmed pay, two-employer amendment, end/resume, and unresolved second-fact cases are tested; generic event mutation is not implemented |
| Currency conversion | `code/main.py`: `Data._rates`, `Data.convert` | Amount, source/target currency, settlement date | Decimal amount in home currency | Fixed exchange-rate rows | Use fixed dated direct/inverse rate; do not invent live rates | Direct and inverse controlled cases verified; prior-rate fallback remains unverified/ambiguous |
| Recurrence detection and projection | `code/main.py`: `Agent.cadence`, `recurrence_series_key`, `recurring_projection`, `reconcile_explicit_inferred_credits` | Historical settled events, category, description, dates, amounts | Future `ProjectionEvent` rows with source IDs and replacement reasons | Cadence thresholds, named-stream/category grouping, median/upper-quartile policy, salary occurrence matching | Distinguish recurring commitments from one-time events and separate merchants/streams | Controlled subscription, grocery, one-time, same-description explicit/inferred, and different-description salary occurrence cases verified |
| Cash-flow replay | `code/main.py`: `Agent.replay` | Starting balance, minimum, dated credits/debits, proposed payments | Safe boolean, minimum seen, daily balances | Projection ordering, credit-before-debit rule | Replay all events/payments and reject any balance below the minimum | Hand-calculated path verified |
| Safe amount and earliest full-payment date | `code/main.py`: `safe_amount`, `earliest_full` | Explicit projection list, profile balance/minimum, request amount/date | Safe amount and earliest safe date | `replay`; no recurrence inference required by these functions | Compute headroom and first safe payment date from supplied paths | Hand-calculated path verified; broad boundary coverage insufficient |
| Payment-option generation and eligibility | `code/main.py`: `Option.dates_and_amounts`, `option_allowed`, `plans` | Provider options, profile methods/limits, desired date | Candidate payment schedules | Payment option fields, horizon, preferences | Accept only supplied/user-permitted schedules completing by deadline/horizon | Controlled option schedule and eligibility verified; full competing-plan generation coverage is insufficient |
| Spending-change generation and application | `code/main.py`: `eligible_changes`, `apply_changes` | Flexible event rows, profile protected/reduce/stop categories, projections | `Change` objects and modified projections | Event flexibility, minimum amount, category permissions | Change only permitted flexible non-protected events; stop/reduce same event mutually exclusive | Controlled reducible event verified; integrated plan combinations insufficiently covered |
| Plan ranking and affordability-status assignment | `code/main.py`: `plans`, `rank`, `decide` | Projections, safe amount, options, changes, preferences, deadline | Best `Plan`, status, method, plan text | Replay, option eligibility, rank tuple | Prefer deadline completion, fewer changes, lower cost, earlier start, fewer payments, option ID tie-break | `rank` ordering controlled case verified; full `plans`/status matrix has insufficient independent coverage |
| Output validation and explanations | `code/main.py`: `validate`, `fmt_amount`; `code/compare_samples.py`: `explanation_consistent` | Output rows, requests, options | Assertions and explanation consistency diagnostic | Output contract, option schedules, string checks | Enforce bounds, enums, payment totals/options, valid changes, and grounded concise explanations | Bounds/enums/plan checks tested; explanation grounding and spending-target existence are insufficiently validated |

## Controlled check results

The diagnostic script produced this summary:

```text
Verified for tested cases: 13
Confirmed failure: 1
Not implemented: 4
Insufficient coverage: 1
```

The “verified” count means only the specific controlled contract listed below,
not correctness of the whole component or final predictions.

### CSV loading, parsing, and joins — verified for tested cases

The check independently loads the CSVs and validates message user/request/event
references against the union of `requests.csv` and `sample_requests.csv` request
IDs and loaded event IDs. It found no invalid references:

```text
profiles=275, requests=275, events=25342, messages=215
invalid_users=[] invalid_requests=[] invalid_events=[]
```

This does not prove that every optional field is semantically interpreted.

### Message extraction — narrow deterministic contract verified; coverage gap confirmed

Independent input:

```text
Salary is USD 1000 on 2025-01-15
```

Expected and actual:

```text
[(2025-01-15, Decimal("1000"), "message payroll")]
```

Independent amount-only input:

```text
Salary is USD 1000 and continues next payroll
```

Actual result: no fact. This is not a forecast failure; it is an unimplemented
message-extraction case. The AI path covers more categories, but its live model
quality is scored separately below.

### AI extraction — confirmed rejection boundary

The live recheck used 19 source-backed expectations, no sample affordability
answers, the configured model, and the v3/v4 semantic contract. Sixteen facts
passed schema and semantic validation. Three provider responses were rejected
for malformed structured content and were not cached or included in the
validated `facts` list. The validated `message_14` result now follows the source:
`transaction_type=refund`, `update_status=delayed`, `action=delay`. The evaluator
records rejected calls, tokens, retries, and cost separately.

The remaining confirmed limitation is provider output quality/reliability, not
silent financial acceptance. Mocked OpenRouter tests verify HTTP/error/cache
behavior only and are not evidence of extraction quality.

### Evidence schema and semantic validation — verified for tested cases

Controlled fact:

```json
{
  "transaction_type": "refund",
  "update_status": "delayed",
  "action": "confirmation"
}
```

`EvidenceFact.from_mapping()` now rejects it. The authoritative mapping is
implemented for `confirmed`, `amended`, `pending`, `delayed`, `cancelled`,
`settled`, `not_cash`, `ended`, and unresolved statuses. Source wording also
rejects a `pending` label when the text only says a credit has not reached the
account, while explicit waiting/processing language remains pending.

### Visibility and scope — verified for tested cases

A `message_14` fact with visibility date `2026-02-08` was evaluated for request
date `2026-02-07` and returned `not_visible`; the ledger remained empty. A
message scoped to `request_a` was requested for `request_b` and was excluded.

### Lifecycle — status cases pass; graph reconciliation is not implemented

Controlled cases passed independently:

- cancelled original + settled replacement → only replacement projected;
- settled purchase + pending refund → only the debit projected because pending
  credits are excluded.

The code does not centrally traverse `linked_event_id` or resolve all
replacement, reversal, retry, duplicate, and source-precedence cases. The link
alone is not treated as proof of duplicate cash; this remains a missing
reconciliation component rather than an invented failure expectation.

### Recurrence — corrected and independently verified

Named commitments now use normalized event type/category/direction/flexibility/
currency/description keys, so two subscriptions in one category remain
separate. Variable categories such as groceries and transport continue to use a
category stream, so different merchants are not silently eliminated. Explicit
one-time markers are excluded, and explicit/inferred deduplication compares the
same source-defined series rather than category alone. Projection rows retain
all historical source event IDs.

Controlled tests cover separate subscriptions, grocery merchants, explicit
one-time purchases, and an explicit future event colliding with its inferred
same-series continuation. The salary amendment persistence test remains green.

### Replay, safe-date, options, and spending changes — narrow contracts pass

Controlled independent cases passed:

- replay: `100 - 40 + 20 - 30 = 50`, minimum `50`, accepted;
- safe amount: explicit path with balance 100, minimum 50, later debit 10 →
  safe amount 40;
- earliest full payment: a 60 payment first passes after a day-2 debit and
  day-3 credit, on `2025-01-03`;
- option schedule: two 40 payments at 30-day frequency are accepted when the
  profile allows installments up to two months;
- ranking: an earlier complete plan ranks ahead of a later equivalent plan;
- spending change: a permitted reducible groceries event changed from 10 to its
  independent minimum 4.

These checks do not establish all same-day, 90-day-boundary, installment-month,
plan-combination, or explanation behavior.

## Ambiguous requirements and unverified assumptions

1. **Exchange-rate fallback:** `Data.convert()` uses the latest rate on or before
   the settlement date if an exact pair/date is absent. The supplied rules say
   fixed dated rates but do not clearly authorize this fallback. No expected
   value was invented; exact direct/inverse behavior is verified and fallback is
   unverified.
2. **Installment months:** `option_allowed()` compares payment count to
   `max_installment_months`, although the field describes months. A schedule’s
   duration versus number of payments needs organizer clarification or a focused
   contract fixture.
3. **Same-day ordering:** `replay()` credits before debits and applies proposed
   payments after both. This is the implementation assumption; only a simple
   multi-day path was independently tested.
4. **Recurring expense reserve policy:** recent median/upper-quartile selection
   is implemented, but the organizer’s exact policy and expected low-point dates
   remain unresolved. No multiplier or correction was added.
5. **Message effective dates:** deterministic payroll extraction requires an ISO
   date. AI salary facts without a stated date can be validated but are not
   independently proven to have a financial effective date.

## Existing tests versus audit evidence

Existing passing tests establish useful local contracts for image lookup,
fixed-rate conversion, pending debit handling, salary-amendment persistence,
installment shape, replay floor rejection, output bounds, schema validation,
OpenRouter defensive handling, visibility, and duplicate suppression. They do
not prove lifecycle reconciliation, automated image extraction, recurrence
correctness across merchants, semantic model quality, or full plan/explanation
correctness. The unchanged final sample comparison is preserved as a regression
signal only; it is not used as proof that these components are correct.

## First repair proposal — do not apply yet

Repair **recurrence detection/projection** first, after approval, because it is a
confirmed component failure with an independent reproducible input and it sits
upstream of replay, safe amount, earliest full payment, and plan selection. The
smallest next checkpoint should:

1. Add a failing regression test using separate merchants in the same category,
   with an independent expected result of no inferred recurring stream.
2. Change only the recurrence grouping/series identity needed to distinguish
   merchants or explicit streams.
3. Re-run recurrence-focused checks, then replay/safe/planning boundary checks.
4. Compare all 25 samples and explain any changed rows by earliest divergent
   component.

Do not change production behavior until the user approves this first repair.
