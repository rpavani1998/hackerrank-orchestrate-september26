"""Run one OpenRouter message extraction without changing financial predictions."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_extraction import (  # noqa: E402
    EvidenceExtractor,
    EvidenceSource,
    JsonExtractionCache,
    ModelAccessUnavailable,
    OpenRouterAdapter,
    OpenRouterConfig,
    OpenRouterError,
)


def main() -> int:
    config = OpenRouterConfig.from_environment(ROOT / ".env")
    if not config.api_key:
        print("OPENROUTER_API_KEY is empty; set it in the project-root .env file.", file=sys.stderr)
        return 2
    message = next(
        row for row in csv.DictReader((ROOT / "dataset/messages.csv").open(newline="", encoding="utf-8"))
        if row["message_id"] == "message_14"
    )
    source = EvidenceSource(
        source_id=message["message_id"],
        source_kind="message",
        user_id=message["user_id"],
        request_id=message["request_id"] or None,
        event_id=message["related_event_id"] or None,
        content=message["message_text"],
    )
    adapter = OpenRouterAdapter(config)
    extractor = EvidenceExtractor(adapter, JsonExtractionCache(ROOT / ".evidence_cache"))
    try:
        outcome = extractor.extract(source, config.model)
    except (ModelAccessUnavailable, OpenRouterError) as exc:
        print(f"OpenRouter smoke test failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "source_id": outcome.fact.source_id,
        "action": outcome.fact.action,
        "amount": str(outcome.fact.amount) if outcome.fact.amount is not None else None,
        "currency": outcome.fact.currency,
        "dates": [item.to_mapping() for item in outcome.fact.dates],
        "missing_fields": list(outcome.fact.missing_fields),
        "cache_hit": outcome.cache_hit,
        "model": outcome.model_name,
        "input_tokens": outcome.input_tokens,
        "output_tokens": outcome.output_tokens,
        "cost_source": outcome.cost_source,
        "reported_cost_usd": str(outcome.reported_cost_usd) if outcome.reported_cost_usd is not None else None,
        "estimated_cost_usd": str(outcome.estimated_cost_usd) if outcome.estimated_cost_usd is not None else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
