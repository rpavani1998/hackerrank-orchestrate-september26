#!/usr/bin/env python3
"""Evaluate a fixed, source-backed message set with cached OpenRouter facts."""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_extraction import (  # noqa: E402
    EvidenceApplication,
    EvidenceExtractor,
    EvidenceFact,
    EvidenceValidationError,
    EvidenceLedger,
    EvidenceSource,
    JsonExtractionCache,
    ModelAccessUnavailable,
    OpenRouterAdapter,
    OpenRouterConfig,
    OpenRouterError,
    apply_evidence_fact,
)

EXPECTATIONS = ROOT / "evaluation/message_extraction_expectations.json"
RESULTS = ROOT / "evaluation/message_extraction_results.json"
REPORT = ROOT / "evaluation/message_extraction_evaluation.md"
CACHE = ROOT / ".evidence_cache"


def read_messages() -> dict[str, dict[str, str]]:
    with (ROOT / "dataset/messages.csv").open(newline="", encoding="utf-8") as fh:
        return {row["message_id"]: row for row in csv.DictReader(fh)}


def source_for(row: dict[str, str]) -> EvidenceSource:
    return EvidenceSource(
        source_id=row["message_id"],
        source_kind="message",
        user_id=row["user_id"],
        request_id=row["request_id"] or None,
        event_id=row["related_event_id"] or None,
        content=row["message_text"],
        visibility_date=date.fromisoformat(row["sent_at"][:10]),
    )


def expected_action(statuses: list[str]) -> set[str]:
    from evidence_extraction import legacy_action_for_status
    return {legacy_action_for_status(status) for status in statuses}


def date_values(fact: EvidenceFact) -> set[str]:
    return {item.value.isoformat() for item in fact.dates}


def application_mapping(application: EvidenceApplication) -> dict[str, str | None]:
    return {
        "state": application.state,
        "cash_effect": application.cash_effect,
        "reason": application.reason,
    }


def compare_fact(fact: EvidenceFact, expected: dict[str, object], source: EvidenceSource,
                 application: EvidenceApplication) -> dict[str, bool]:
    amount_expected = expected["amount"]
    amount_actual = str(fact.amount) if fact.amount is not None else None
    expected_dates = {item["date"] for item in expected["dates"]}
    fields = {
        "source_references": (
            fact.source_id == source.source_id and fact.source_kind == source.source_kind
            and fact.supplied_user_id == source.user_id
            and fact.supplied_request_id == source.request_id
            and fact.supplied_event_id == source.event_id
        ),
        "transaction_type": fact.transaction_type in expected["transaction_type"],
        "update_status": fact.update_status in expected["update_status"],
        "action": fact.action in expected_action(expected["update_status"]),
        "amount": amount_actual == amount_expected,
        "currency": fact.currency == expected["currency"],
        "dates": date_values(fact) == expected_dates,
        "recurrence_scope": fact.recurrence_scope in expected["recurrence_scope"],
        "application": application.state == expected["expected_application_state"],
    }
    return fields


def run() -> int:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    messages = read_messages()
    config = OpenRouterConfig.from_environment(ROOT / ".env")
    if not config.api_key:
        raise ModelAccessUnavailable("OPENROUTER_API_KEY is empty")
    extractor = EvidenceExtractor(OpenRouterAdapter(config), JsonExtractionCache(CACHE))
    ledger = EvidenceLedger()
    records = []
    totals: dict[str, int] = {}
    total_input = 0
    total_output = 0
    total_cost = Decimal(0)
    provider_calls = 0
    cache_hits = 0
    for message_id, expected in expectations.items():
        source = source_for(messages[message_id])
        try:
            outcome = extractor.extract(source, config.model)
        except (EvidenceValidationError, OpenRouterError) as exc:
            response = getattr(exc, "provider_response", None)
            input_tokens = response.input_tokens if response is not None else None
            output_tokens = response.output_tokens if response is not None else None
            retries = response.retries if response is not None else 0
            reported = response.reported_cost_usd if response is not None else None
            estimated = response.estimated_cost_usd if response is not None else None
            cost_source = response.cost_source if response is not None else "none"
            total_input += input_tokens or 0
            total_output += output_tokens or 0
            total_cost += reported or estimated or Decimal(0)
            provider_calls += 1
            records.append({
                "message_id": message_id,
                "rejected": True,
                "rejection_reason": str(exc),
                "cache_hit": False,
                "model_name": config.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "retries": retries,
                "reported_cost_usd": str(reported) if reported is not None else None,
                "estimated_cost_usd": str(estimated) if estimated is not None else None,
                "cost_source": cost_source,
            })
            continue
        provider_calls += int(not outcome.cache_hit)
        cache_hits += int(outcome.cache_hit)
        application = apply_evidence_fact(outcome.fact, source, date.max, ledger)
        fields = compare_fact(outcome.fact, expected, source, application)
        for field, matched in fields.items():
            totals[field] = totals.get(field, 0) + int(matched)
        total_input += outcome.input_tokens or 0
        total_output += outcome.output_tokens or 0
        cost = outcome.reported_cost_usd or outcome.estimated_cost_usd or Decimal(0)
        total_cost += cost
        records.append({
            "message_id": message_id,
            "fact": outcome.fact.to_mapping(),
            "cache_hit": outcome.cache_hit,
            "model_name": outcome.model_name,
            "input_tokens": outcome.input_tokens,
            "output_tokens": outcome.output_tokens,
            "retries": outcome.retries,
            "reported_cost_usd": str(outcome.reported_cost_usd) if outcome.reported_cost_usd is not None else None,
            "estimated_cost_usd": str(outcome.estimated_cost_usd) if outcome.estimated_cost_usd is not None else None,
            "cost_source": outcome.cost_source,
            "application": application_mapping(application),
            "field_matches": fields,
        })
    payload = {
        "schema_version": "message-evaluation-v1",
        "model": config.model,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "message_count": len(records),
        "records": records,
        "facts": [record["fact"] for record in records if "fact" in record],
        "usage": {
            "cache_hits": cache_hits,
            "provider_calls": provider_calls,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": str(total_cost),
            "average_cost_usd_per_message": str(total_cost / len(records)),
        },
        "field_matches": totals,
    }
    RESULTS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Message extraction evaluation",
        "",
        f"Model: `{config.model}`",
        f"Messages: {len(records)}",
        "",
        "Expected facts were recorded in `evaluation/message_extraction_expectations.json` before extraction.",
        "The evaluator compares source references, transaction type, update status, legacy action, amount, currency, date values, recurrence scope, and application state.",
        "",
        "## Field-level results",
        "",
        "| Field | Correct | Total |",
        "|---|---:|---:|",
    ]
    for field in ("source_references", "transaction_type", "update_status", "action", "amount", "currency", "dates", "recurrence_scope", "application"):
        lines.append(f"| {field} | {totals.get(field, 0)} | {len(records)} |")
    lines += [
        "",
        "## Usage",
        "",
        f"- Provider calls: {payload['usage']['provider_calls']}",
        f"- Cache hits: {payload['usage']['cache_hits']}",
        f"- Input tokens: {total_input}",
        f"- Output tokens: {total_output}",
        f"- Total tokens: {total_input + total_output}",
        f"- Total reported/estimated cost: USD {total_cost}",
        f"- Average cost per selected message: USD {payload['usage']['average_cost_usd_per_message']}",
        "",
        "## Unresolved/application cases",
        "",
    ]
    for record in records:
        if record.get("rejected"):
            lines.append(f"- `{record['message_id']}`: rejected — {record['rejection_reason']}")
        elif record["application"]["state"] != "applied":
            lines.append(f"- `{record['message_id']}`: {record['application']['state']} — {record['application']['reason']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload["usage"], indent=2, sort_keys=True))
    print(json.dumps(totals, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (ModelAccessUnavailable, OpenRouterError, KeyError) as exc:
        print(f"message evaluation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
