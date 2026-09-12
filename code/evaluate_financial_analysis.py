#!/usr/bin/env python3
"""Run bounded AI financial-history analysis for representative sample requests."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_extraction import (  # noqa: E402
    OpenRouterConfig,
    OpenRouterError,
    load_env_file,
)
from financial_analysis import (  # noqa: E402
    ANALYSIS_SCHEMA_VERSION,
    AnalysisCache,
    AnalysisExtractor,
    AnalysisValidationError,
    OpenRouterAnalysisProvider,
    _build_ai_scope,
    build_financial_analysis,
    profile_markdown,
    validate_proposals,
)
from main import Data, load_evidence_facts  # noqa: E402

RESULTS = ROOT / "evaluation/financial_analysis_results.json"
PROFILES = ROOT / "evaluation/financial_analysis_profiles.md"
CACHE = ROOT / ".analysis_cache"
REPRESENTATIVE_REQUESTS = ("request_02", "request_01", "request_05", "request_20")


def sample_requests() -> dict[str, dict[str, str]]:
    import csv
    with (ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8") as fh:
        return {row["request_id"]: row for row in csv.DictReader(fh)}


def run() -> int:
    samples = sample_requests()
    data = Data()
    evidence_path = ROOT / "evaluation/message_extraction_results.json"
    if evidence_path.exists():
        data.evidence_facts = load_evidence_facts(evidence_path, data.messages)
    config = OpenRouterConfig.from_environment(ROOT / ".env")
    if not config.api_key:
        raise RuntimeError("OPENROUTER_API_KEY is empty")
    extractor = AnalysisExtractor(
        OpenRouterAnalysisProvider(config),
        AnalysisCache(CACHE),
    )
    analyses = []
    usage = {
        "model": config.model,
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "provider_calls": 0,
        "cache_hits": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost_usd": Decimal(0),
        "retries": 0,
    }
    profile_documents = []
    for request_id in REPRESENTATIVE_REQUESTS:
        request = samples[request_id]
        user_id = request["user_id"]
        as_of = date.fromisoformat(request["request_date"])
        scope, _source_rows = _build_ai_scope(data, user_id, request_id, as_of)
        event_map = {
            event.event_id: event
            for event in data.events_by_user.get(user_id, [])
            if event.settlement_date <= as_of + timedelta(days=90)
            and event.direction != "non_cash"
        }
        try:
            outcome = extractor.extract(scope, event_map, user_id, config.model)
            usage["cache_hits"] += int(outcome.cache_hit)
            usage["provider_calls"] += int(not outcome.cache_hit)
            usage["input_tokens"] += outcome.input_tokens or 0
            usage["output_tokens"] += outcome.output_tokens or 0
            usage["retries"] += outcome.retries
            usage["total_cost_usd"] += outcome.reported_cost_usd or outcome.estimated_cost_usd or Decimal(0)
            historical_events = {
                event.event_id: event
                for event in data.events_by_user.get(user_id, [])
                if event.status == "settled" and event.settlement_date <= as_of and event.direction != "non_cash"
            }
            validation = validate_proposals(outcome.raw_proposals, historical_events, user_id)
            metadata = {
                "mode": "ai",
                "model": outcome.model_name,
                "cache_hit": outcome.cache_hit,
                "input_tokens": outcome.input_tokens,
                "output_tokens": outcome.output_tokens,
                "retries": outcome.retries,
                "reported_cost_usd": str(outcome.reported_cost_usd) if outcome.reported_cost_usd is not None else None,
                "estimated_cost_usd": str(outcome.estimated_cost_usd) if outcome.estimated_cost_usd is not None else None,
                "accepted_patterns": len(validation.accepted),
                "rejected_patterns": len(validation.rejected),
            }
            analysis = build_financial_analysis(data, user_id, as_of, request_id, validation, metadata)
            record = {
                "request_id": request_id,
                "user_id": user_id,
                "as_of_date": as_of.isoformat(),
                "status": "validated",
                "raw_proposals": outcome.raw_proposals,
                "accepted_patterns": [proposal.to_mapping() for proposal in validation.accepted],
                "rejected_patterns": list(validation.rejected),
                "analysis": analysis,
            }
        except (AnalysisValidationError, OpenRouterError, RuntimeError) as exc:
            usage["provider_calls"] += 1
            analysis = build_financial_analysis(
                data, user_id, as_of, request_id,
                model_metadata={"mode": "ai", "status": "provider_or_validation_rejected", "reason": str(exc)},
            )
            record = {
                "request_id": request_id,
                "user_id": user_id,
                "as_of_date": as_of.isoformat(),
                "status": "provider_or_validation_rejected",
                "rejection_reason": str(exc),
                "analysis": analysis,
            }
        analyses.append(record)
        profile_documents.append(profile_markdown(analysis))
    payload = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scope_count": len(analyses),
        "records": analyses,
        "analyses_by_scope": {
            f"{record['user_id']}|{record['as_of_date']}": record["analysis"]
            for record in analyses
        },
        "usage": {
            **usage,
            "total_cost_usd": str(usage["total_cost_usd"]),
            "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            "average_tokens_per_scope": (usage["input_tokens"] + usage["output_tokens"]) / len(analyses),
            "average_cost_usd_per_scope": str(usage["total_cost_usd"] / len(analyses)),
        },
    }
    RESULTS.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    PROFILES.write_text("\n\n---\n\n".join(profile_documents), encoding="utf-8")
    print(json.dumps(payload["usage"], indent=2, sort_keys=True, default=str))
    for record in analyses:
        print(f"{record['request_id']}: {record['status']} patterns={len(record['analysis']['inferred_patterns'])} forecast_inputs={len(record['analysis']['forecast_inputs'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (OpenRouterError, RuntimeError) as exc:
        print(f"financial analysis evaluation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
