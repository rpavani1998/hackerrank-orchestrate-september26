# Buy or Wait? deterministic agent

## Deterministic run

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/main.py --mode deterministic
```

The program reads only `dataset/` and writes the required root-level
`output.csv`. Arithmetic, cash-flow forecasting, payment eligibility, plan
ranking, and safety validation remain deterministic. The original sample
comparison is read-only:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 code/compare_samples.py
```

## OpenRouter evidence extraction

The optional message-extraction adapter uses the standard library only. It does
not run as part of the deterministic prediction command and does not change
`output.csv`.

1. Copy `.env.example` to `.env`, or use the prepared project-root `.env`.
2. Enter the key only in `.env`:

   ```text
   OPENROUTER_API_KEY=your_key_here
   ```

   Do not paste the key into chat, source files, logs, caches, or archives.
   Existing environment variables take precedence over `.env` values.
3. The default configurable model is
   `mistralai/mistral-small-24b-instruct-2501` at
   `https://openrouter.ai/api/v1`. It is checked for structured-output support
   before a request; no fallback model is selected.
4. Run one message-only smoke test after configuring the key:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 code/openrouter_smoke.py
   ```

   It extracts only linked `message_14`, prints structured evidence and usage
   metadata, and never generates predictions. A delayed refund without a
   confirmed amount or settlement date remains unresolved and creates no cash.

The adapter has explicit timeouts, bounded retries, HTTP 401/429/5xx handling,
local schema validation, cache keys covering source content/model/prompt/schema,
provider-reported cost handling, and a documented price estimate fallback.
`code/evidence_extraction.py` never applies facts directly to balances.

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
