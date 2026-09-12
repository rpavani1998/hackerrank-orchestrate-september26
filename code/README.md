# Buy or Wait? deterministic and AI-enabled agent

## Deterministic run

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/main.py --mode deterministic
```

The program reads `dataset/` and writes the required root-level `output.csv`.
Arithmetic, cash-flow forecasting, payment eligibility, plan ranking, and safety
validation remain deterministic. The read-only comparison does not write
`output.csv`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/compare_samples.py --mode deterministic
```

## Message extraction and AI-enabled mode

The optional message-extraction adapter uses the standard library only. It
separates `transaction_type` (such as `refund` or `salary`) from
`update_status` (such as `delayed`, `amended`, or `settled`) while retaining the
legacy `action` field for compatibility.

1. Use the project-root `.env` or copy `.env.example` to `.env` without
   overwriting an existing configured file.
2. Keep `OPENROUTER_API_KEY` only in `.env` or the execution environment. Do not
   paste it into chat, source files, logs, caches, or archives. Existing
   environment variables take precedence over `.env` values.
3. Run the representative 19-message evaluation. It records source-backed
   expectations separately, calls the configured model, caches validated facts
   in `.evidence_cache/`, and writes evaluation/usage artifacts:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 code/evaluate_messages.py
   ```

   The evaluation does not include sample affordability answers in model
   prompts. It reports field-level correctness, unresolved application cases,
   token counts, cache hits, and provider-reported/estimated cost.
4. Run the isolated, read-only AI comparison across all 25 solved samples:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 code/compare_samples.py --mode ai --evidence-file evaluation/message_extraction_results.json
   PYTHONDONTWRITEBYTECODE=1 python3 code/compare_modes.py --evidence-file evaluation/message_extraction_results.json
   ```

   These commands consume validated cached facts and do not write `output.csv`.
5. To produce predictions using the AI-enabled pipeline, run the exact command
   below. It writes root-level `output.csv` as the normal prediction command
   does; use the read-only comparisons when preserving an existing output file:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 code/main.py --mode ai --evidence-file evaluation/message_extraction_results.json
   ```

   AI mode validates every fact against the supplied message user/request/event
   links, request-date visibility, and duplicate ledger before projection.
   Validated salary amount/date/end facts can amend the projected salary
   timeline. Pending or disputed refunds, payouts, prizes, and reversals remain
   unresolved; status-only settlement/non-cash facts do not add starting-balance
   income or duplicate event cash.

For the evaluated run, the configured model was `google/gemini-3.8-flash` from
`OPENROUTER_MODEL`; the model is not hardcoded in the pipeline. The adapter
performs structured-output capability checks, explicit timeouts, bounded
408/409/429/5xx retries, local schema validation, complete cache keys, and
provider usage/cost accounting with no model fallback.

## User financial-history analysis

`code/financial_analysis.py` implements the scoped analysis layer between
reconciled evidence and forecast construction. Deterministic code owns event
scope/lifecycle filtering, source-ID validation, recurrence grouping,
statistics, future obligations, and forecast-input amounts. OpenRouter only
proposes source-linked pattern groupings and alternatives; unknown IDs,
cross-user links, contradictory categories, duplicate claims, and unsupported
cadences remain review items.

Representative AI analysis profiles can be reproduced without writing
`output.csv`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/evaluate_financial_analysis.py
PYTHONDONTWRITEBYTECODE=1 python3 code/trace_analysis_forecast.py
```

Artifacts are written to `evaluation/financial_analysis_results.json`,
`evaluation/financial_analysis_profiles.md`, and
`evaluation/analysis_forecast_trace.md`; provider calls, tokens, retries, cache
hits, and cost are recorded. The analysis cache is scoped by user, request,
as-of date, input/prompt content, model, and schema versions and is ignored by
Git. It never receives sample answer labels.

AI-mode read-only comparisons may consume the validated analysis artifact:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/compare_samples.py --mode ai \
  --evidence-file evaluation/message_extraction_results.json \
  --analysis-file evaluation/financial_analysis_results.json
PYTHONDONTWRITEBYTECODE=1 python3 code/compare_modes.py \
  --evidence-file evaluation/message_extraction_results.json \
  --analysis-file evaluation/financial_analysis_results.json \
  --output evaluation/mode_comparison_analysis.md
```

The production command accepts the same optional interface:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/main.py --mode ai \
  --evidence-file evaluation/message_extraction_results.json \
  --analysis-file evaluation/financial_analysis_results.json
```

The analysis path is optional. Deterministic mode does not load it, and missing
request scopes fall back to the corrected deterministic recurrence engine. To
materialize keyed deterministic analyses for every evaluation request without
model calls, use:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/build_analysis_artifact.py
```

This writes the development-only `evaluation/financial_analysis_all_requests.json`
artifact (ignored because it contains the full 250-scope history expansion).

Audit exact sample scope coverage, forecast consumption, source quality, and the
intersection with the 250-request artifact with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/audit_financial_analysis.py --strict
```

Strict mode exits nonzero when any required sample scope is absent. Normal
runtime behavior is unchanged: a missing analysis scope still uses the
corrected deterministic recurrence fallback. The audit also distinguishes live,
cached, and deterministic analysis records; it does not infer coverage from
artifact size.

The focused smoke test remains available:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/openrouter_smoke.py
```

It extracts only `message_14`, prints structured evidence and usage metadata,
and never generates predictions.

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s code -p 'test_*.py'
```

## Packaging

Build a submission archive with the explicit secret exclusion rule:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/package.py code.zip
unzip -l code.zip | grep -E '(^|/)\.env($|\.)' && echo 'ERROR: secret file in archive' || true
```

`code/package.py` excludes `.env`, `.env.*` backups, bytecode, caches, and Git
metadata while allowing `.env.example`. Never stage `.env`; Git ignores it and
packaging independently excludes it.
