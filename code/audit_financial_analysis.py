#!/usr/bin/env python3
"""Strict coverage and source-quality audit for scoped financial analysis."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from financial_analysis import (  # noqa: E402
    VARIABLE_CATEGORIES,
    _deterministic_patterns,
    cadence,
    supported_income_forecast,
)
from main import Agent, Data, load_evidence_facts, load_financial_analyses  # noqa: E402



def samples() -> list[dict[str, str]]:
    with (ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def scope_key(user_id: str, request_id: str, as_of: str) -> str:
    return f"{user_id}|{as_of}"


def record_index(payload: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    result = {}
    for record in payload.get("records", []):
        analysis = record.get("analysis", {})
        scope = analysis.get("scope", {})
        key = (scope.get("user_id"), scope.get("request_id"), scope.get("as_of_date"))
        result[key] = record
    return result


def source_event_map(data: Data, user_id: str, as_of: date) -> dict[str, Any]:
    return {
        event.event_id: event
        for event in data.events_by_user.get(user_id, [])
        if event.status == "settled" and event.settlement_date <= as_of and event.direction != "non_cash"
    }


def consumed_patterns(agent: Agent, request: dict[str, str], analysis: dict[str, Any]) -> list[dict[str, Any]]:
    pattern_by_source: dict[str, list[dict[str, Any]]] = {}
    for item in analysis.get("forecast_inputs", []):
        for event_id in item.get("source_event_ids", []):
            pattern_by_source.setdefault(event_id, []).append(item)
    projections = agent.projections(request)
    consumed: dict[str, dict[str, Any]] = {}
    for projection in projections:
        ids = set(projection.source_event_ids)
        if not ids and projection.recurring_ref:
            ids = {projection.recurring_ref}
        for item in pattern_by_source.get(next(iter(ids), ""), []):
            pattern_id = item["pattern_id"]
            row = consumed.setdefault(pattern_id, {
                "pattern_id": pattern_id,
                "pattern_type": item.get("pattern_type"),
                "category": item.get("category"),
                "source_event_ids": item.get("source_event_ids", []),
                "projection_count": 0,
                "projection_rows": [],
            })
            if ids.intersection(item.get("source_event_ids", [])):
                row["projection_count"] += 1
                row["projection_rows"].append({
                    "when": projection.when.isoformat(),
                    "amount": str(projection.amount),
                    "direction": projection.direction,
                    "event_id": projection.event_id,
                    "source_event_ids": list(projection.source_event_ids),
                })
    return sorted(consumed.values(), key=lambda row: row["pattern_id"])


def accepted_quality(record: dict[str, Any], data: Data, user_id: str, as_of: date) -> list[dict[str, Any]]:
    events = source_event_map(data, user_id, as_of)
    findings = []
    for proposal in record.get("accepted_patterns", []):
        ids = proposal.get("source_event_ids", [])
        source = [events.get(event_id) for event_id in ids]
        issues = []
        if not ids or any(item is None for item in source):
            issues.append("unknown_or_nonhistorical_source_id")
        else:
            if any(event.user_id != user_id for event in source):
                issues.append("cross_user_source")
            if any(event.category != proposal.get("category") for event in source):
                issues.append("category_contradiction")
            if proposal.get("pattern_type") in {"recurring_commitment", "variable_spending"}:
                if any(event.status != "settled" for event in source):
                    issues.append("not_settled_history")
                if proposal.get("pattern_type") == "variable_spending":
                    if any(event.direction != "debit" for event in source):
                        issues.append("variable_pattern_contains_credit")
                    if proposal.get("category") not in VARIABLE_CATEGORIES:
                        issues.append("non_variable_category")
                if proposal.get("pattern_type") == "recurring_commitment" and cadence([event.settlement_date for event in source]) is None:
                    issues.append("unsupported_cadence")
        findings.append({
            "label": proposal.get("label"),
            "pattern_type": proposal.get("pattern_type"),
            "source_event_ids": ids,
            "issues": issues,
            "classification": "incorrect_accepted" if issues else "source_compatible_not_proof",
        })
    return findings


def rejected_quality(record: dict[str, Any], data: Data, user_id: str, as_of: date) -> list[dict[str, Any]]:
    events = source_event_map(data, user_id, as_of)
    findings = []
    for rejected in record.get("rejected_patterns", []):
        proposal = rejected.get("proposal", {})
        ids = proposal.get("source_event_ids", []) if isinstance(proposal, dict) else []
        source = [events.get(event_id) for event_id in ids]
        useful = False
        reason = "unknown_or_cross_scope_or_unsupported"
        if ids and all(item is not None for item in source):
            category_ok = all(event.category == proposal.get("category") for event in source)
            if proposal.get("pattern_type") == "recurring_commitment":
                useful = category_ok and all(event.direction == "debit" and event.status == "settled" for event in source) and cadence([event.settlement_date for event in source]) is not None
            elif proposal.get("pattern_type") == "variable_spending":
                useful = category_ok and proposal.get("category") in VARIABLE_CATEGORIES and all(event.direction == "debit" and event.status == "settled" for event in source)
            reason = "source_compatible_candidate_rejected" if useful else "source_records_support_rejection"
        findings.append({
            "label": proposal.get("label") if isinstance(proposal, dict) else None,
            "source_event_ids": ids,
            "validator_reason": rejected.get("reason"),
            "classification": "correct_pattern_rejected" if useful else "correct_rejection_or_review",
            "review_reason": reason,
        })
    return findings


def quality_report(data: Data, payload: dict[str, Any], records: dict[tuple[str, str, str], dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    aggregate = {
        "incorrect_accepted": [],
        "correct_pattern_rejected": [],
        "ai_missed_supported_streams": [],
        "variable_omissions": [],
        "double_counting": [],
        "unsupported_future_income": [],
        "unresolved": [],
    }
    for request in samples():
        user_id, request_id, as_of_text = request["user_id"], request["request_id"], request["request_date"]
        record = records.get((user_id, request_id, as_of_text))
        if record is None:
            continue
        as_of = date.fromisoformat(as_of_text)
        accepted = accepted_quality(record, data, user_id, as_of)
        rejected = rejected_quality(record, data, user_id, as_of)
        incorrect = [item for item in accepted if item["classification"] == "incorrect_accepted"]
        useful_rejected = [item for item in rejected if item["classification"] == "correct_pattern_rejected"]
        historical = source_event_map(data, user_id, as_of)
        deterministic = _deterministic_patterns(list(historical.values()), data.profiles[user_id].home_currency, data.convert)
        ai_ids = {event_id for proposal in record.get("accepted_patterns", []) for event_id in proposal.get("source_event_ids", [])}
        is_live_ai = record.get("analysis", {}).get("model_metadata", {}).get("mode") == "ai"
        missed = [
            {"pattern_id": pattern["pattern_id"], "label": pattern["label"], "source_event_ids": pattern["source_event_ids"]}
            for pattern in deterministic
            if is_live_ai
            and pattern["pattern_type"] == "recurring_commitment"
            and not ai_ids.intersection(pattern["source_event_ids"])
        ]
        inferred = record.get("analysis", {}).get("inferred_patterns", [])
        claims = [event_id for pattern in inferred for event_id in pattern.get("source_event_ids", [])]
        duplicates = sorted({event_id for event_id in claims if claims.count(event_id) > 1})
        variable_categories = {
            pattern.get("category") for pattern in deterministic
            if pattern.get("pattern_type") == "variable_spending"
        }
        inferred_variable_categories = {
            pattern.get("category") for pattern in inferred if pattern.get("pattern_type") == "variable_spending"
        }
        variable_omitted = sorted(variable_categories - inferred_variable_categories)
        forecast_income = []
        for item in record.get("analysis", {}).get("forecast_inputs", []):
            ids = item.get("source_event_ids", [])
            source = [historical.get(event_id) for event_id in ids]
            if source and any(event is not None and event.direction == "credit" for event in source):
                if item.get("income_eligibility") not in {"recurring_salary_supported", "confirmed_future_credit"}:
                    forecast_income.append({"pattern_id": item.get("pattern_id"), "source_event_ids": ids, "eligibility": item.get("income_eligibility")})
        unresolved = record.get("analysis", {}).get("unresolved_evidence_and_assumptions", [])
        row = {
            "request_id": request_id,
            "user_id": user_id,
            "as_of_date": as_of_text,
            "accepted_count": len(record.get("accepted_patterns", [])),
            "rejected_count": len(record.get("rejected_patterns", [])),
            "incorrect_accepted": incorrect,
            "correct_pattern_rejected": useful_rejected,
            "ai_missed_supported_streams": missed,
            "variable_omitted_source_event_ids": variable_omitted,
            "double_counted_source_event_ids": duplicates,
            "unsupported_future_income": forecast_income,
            "unresolved": unresolved,
        }
        rows.append(row)
        aggregate["incorrect_accepted"].extend([{**item, "request_id": request_id} for item in incorrect])
        aggregate["correct_pattern_rejected"].extend([{**item, "request_id": request_id} for item in useful_rejected])
        aggregate["ai_missed_supported_streams"].extend([{**item, "request_id": request_id} for item in missed])
        aggregate["variable_omissions"].extend([{ "request_id": request_id, "source_event_ids": variable_omitted }] if variable_omitted else [])
        aggregate["double_counting"].extend([{ "request_id": request_id, "source_event_ids": duplicates }] if duplicates else [])
        aggregate["unsupported_future_income"].extend([{**item, "request_id": request_id} for item in forecast_income])
        aggregate["unresolved"].extend([{**item, "request_id": request_id} for item in unresolved])
    return rows, aggregate


def write_report(path: Path, artifact_path: Path, all_artifact_path: Path, rows: list[dict[str, Any]], aggregate: dict[str, Any], coverage_errors: list[str], all_intersection: list[str]) -> None:
    lines = [
        "# Financial-analysis coverage and source-quality audit",
        "",
        f"Sample artifact: `{artifact_path}`",
        f"250-request artifact checked: `{all_artifact_path}`",
        "",
        "## Coverage summary",
        "",
        f"- Required sample scopes: `{len(rows)}`",
        f"- Missing sample scopes: `{len(coverage_errors)}`",
        f"- Sample scopes present in the 250-request artifact: `{len(all_intersection)}/{len(rows)}`",
        f"- Accepted-pattern rows: `{sum(row['accepted_count'] for row in rows)}`",
        f"- Rejected-pattern rows: `{sum(row['rejected_count'] for row in rows)}`",
        "",
        "The 250-request artifact is not assumed to cover samples based on file size; "
        "the intersection is checked by exact `(user_id, as_of_date)` keys.",
        "",
        "## Per-sample exact scope and consumption",
        "",
        "| Request | User | As of | Artifact loaded | Origin | Accepted | Rejected | Forecast patterns consumed | Fallback/reason |",
        "|---|---|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        origin = row.get("origin", "unknown")
        consumed = ", ".join(item["pattern_id"] for item in row.get("consumed_patterns", [])) or "none"
        lines.append(
            f"| {row['request_id']} | {row['user_id']} | {row['as_of_date']} | {row['artifact_loaded']} | {origin} | "
            f"{row['accepted_count']} | {row['rejected_count']} | {consumed} | {row.get('fallback_reason') or 'none'} |"
        )
    lines.extend(["", "## Analysis-quality findings independent of acceptance", ""])
    labels = {
        "incorrect_accepted": "Incorrect accepted patterns",
        "correct_pattern_rejected": "Correct patterns rejected by validator review",
        "ai_missed_supported_streams": "Supported recurring commitments missed by live AI proposals",
        "variable_omissions": "Variable-spending omissions",
        "double_counting": "Double-counted source events",
        "unsupported_future_income": "Unsupported future income",
        "unresolved": "Unresolved evidence/assumptions",
    }
    for key, label in labels.items():
        lines.append(f"### {label} ({len(aggregate[key])})")
        if not aggregate[key]:
            lines.append("- None detected by the independent source checks.")
        else:
            for item in aggregate[key][:80]:
                lines.append(f"- `{json.dumps(item, sort_keys=True, default=str)}`")
        lines.append("")
    lines.extend(["## Strict-mode result", "", "- PASS" if not coverage_errors else "- FAIL: " + "; ".join(coverage_errors)])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit financial-analysis coverage and source quality")
    parser.add_argument("--analysis-file", type=Path, default=ROOT / "evaluation/financial_analysis_sample_scopes.json")
    parser.add_argument("--all-requests-artifact", type=Path, default=ROOT / "evaluation/financial_analysis_all_requests.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/analysis_coverage_report.md")
    parser.add_argument("--strict", action="store_true", help="fail if any required sample scope is absent")
    args = parser.parse_args()
    payload = json.loads(args.analysis_file.read_text(encoding="utf-8"))
    records = record_index(payload)
    data = Data()
    evidence = ROOT / "evaluation/message_extraction_results.json"
    if evidence.exists():
        data.evidence_facts = load_evidence_facts(evidence, data.messages)
    data.financial_analyses = load_financial_analyses(args.analysis_file)
    agent = Agent(data)
    rows = []
    coverage_errors = []
    for request in samples():
        key = (request["user_id"], request["request_id"], request["request_date"])
        record = records.get(key)
        loaded = key in records and (request["user_id"], request["request_id"], date.fromisoformat(request["request_date"])) in data.financial_analyses
        if record is None or not loaded:
            coverage_errors.append(f"missing exact scope {key}")
            rows.append({"request_id": request["request_id"], "user_id": request["user_id"], "as_of_date": request["request_date"], "artifact_loaded": False, "origin": "missing", "accepted_count": 0, "rejected_count": 0, "consumed_patterns": [], "fallback_reason": "missing_required_scope"})
            continue
        analysis = record.get("analysis", {})
        metadata = analysis.get("model_metadata", {})
        mode = metadata.get("mode")
        if mode == "ai":
            origin = "cached_ai" if metadata.get("cache_hit") else "live_ai"
        else:
            origin = "deterministic_construction"
        fallback_reason = metadata.get("reason") if mode == "deterministic_fallback" else None
        consumed = consumed_patterns(agent, request, analysis)
        rows.append({
            "request_id": request["request_id"], "user_id": request["user_id"], "as_of_date": request["request_date"],
            "artifact_loaded": True, "origin": origin,
            "accepted_count": len(record.get("accepted_patterns", [])),
            "rejected_count": len(record.get("rejected_patterns", [])),
            "consumed_patterns": consumed, "fallback_reason": fallback_reason,
        })
    all_intersection = []
    if args.all_requests_artifact.exists():
        all_payload = json.loads(args.all_requests_artifact.read_text(encoding="utf-8"))
        all_keys = set(all_payload.get("analyses_by_scope", {}))
        all_intersection = [
            request["request_id"] for request in samples()
            if scope_key(request["user_id"], request["request_id"], request["request_date"]) in all_keys
        ]
    quality_rows, aggregate = quality_report(data, payload, records)
    by_id = {row["request_id"]: row for row in quality_rows}
    for row in rows:
        row.update({
            "incorrect_accepted": by_id.get(row["request_id"], {}).get("incorrect_accepted", []),
        })
    write_report(args.output, args.analysis_file, args.all_requests_artifact, rows, aggregate, coverage_errors, all_intersection)
    print(json.dumps({
        "required_scopes": len(rows),
        "missing_scopes": len(coverage_errors),
        "all_requests_intersection": len(all_intersection),
        "incorrect_accepted": len(aggregate["incorrect_accepted"]),
        "correct_pattern_rejected": len(aggregate["correct_pattern_rejected"]),
        "ai_missed_supported_streams": len(aggregate["ai_missed_supported_streams"]),
        "variable_omissions": len(aggregate["variable_omissions"]),
        "double_counting": len(aggregate["double_counting"]),
        "unsupported_future_income": len(aggregate["unsupported_future_income"]),
    }, indent=2, sort_keys=True))
    return 2 if args.strict and coverage_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
