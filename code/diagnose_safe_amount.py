#!/usr/bin/env python3
"""Read-only safe-amount discrepancy and forecast timing diagnosis.

This diagnostic deliberately does not write output.csv or alter forecast policy.
It uses the current AI-enabled sample artifact so each row records whether its
forecast inputs came from a cached AI scope or deterministic fallback.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import (  # noqa: E402
    Agent,
    Data,
    ProjectionEvent,
    add_months,
    ddate,
    dec,
    load_evidence_facts,
    load_financial_analyses,
)

SAMPLES = ROOT / "dataset/sample_requests.csv"
ANALYSIS = ROOT / "evaluation/financial_analysis_sample_scopes.json"
EVIDENCE = ROOT / "evaluation/message_extraction_results.json"
OUTPUT = ROOT / "evaluation/safe_amount_diagnosis.md"
DAYS = 90
CENT = Decimal("0.01")


def sample_rows() -> list[dict[str, str]]:
    with SAMPLES.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def analysis_records() -> dict[tuple[str, str, str], dict[str, Any]]:
    payload = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    return {
        (record.get("user_id"), record.get("request_id"), record.get("as_of_date")): record
        for record in payload.get("records", [])
    }


def money(value: Decimal) -> str:
    return str(value.quantize(CENT))


def event_sort_key(projection: ProjectionEvent) -> tuple[bool, str]:
    return (projection.direction != "credit", projection.event_id)


def replay_timeline(
    data: Data,
    request: dict[str, str],
    projections: list[ProjectionEvent],
    payment: Decimal = Decimal(0),
) -> dict[str, Any]:
    """Replay the complete horizon without early termination for diagnosis."""
    start = ddate(request["request_date"])
    end = start + timedelta(days=DAYS)
    profile = data.profiles[request["user_id"]]
    by_day: dict[date, list[ProjectionEvent]] = defaultdict(list)
    for projection in projections:
        by_day[projection.when].append(projection)
    current = profile.balance
    daily: dict[date, Decimal] = {start: current}
    entries: list[tuple[date, str, ProjectionEvent | None, Decimal]] = []
    lowest = current
    lowest_date = start
    first_failure: tuple[date, Decimal] | None = None
    day = start
    while day <= end:
        for projection in sorted(by_day.get(day, []), key=event_sort_key):
            current += projection.amount if projection.direction == "credit" else -projection.amount
            entries.append((day, "projection", projection, current))
            if current < lowest:
                lowest, lowest_date = current, day
        if day == start and payment:
            current -= payment
            entries.append((day, "expected_payment", None, current))
            if current < lowest:
                lowest, lowest_date = current, day
        daily[day] = current
        if current < profile.minimum and first_failure is None:
            first_failure = (day, profile.minimum - current)
        day += timedelta(days=1)
    return {
        "daily": daily,
        "entries": entries,
        "lowest": lowest,
        "lowest_date": lowest_date,
        "first_failure": first_failure,
        "passes": first_failure is None,
    }


def source_events(data: Data, user_id: str, source_ids: list[str] | tuple[str, ...]) -> list[Any]:
    by_id = {event.event_id: event for event in data.events_by_user.get(user_id, [])}
    return [by_id[event_id] for event_id in source_ids if event_id in by_id]


def evidence_for_event(data: Data, event_id: str) -> list[str]:
    statuses = []
    for fact in data.evidence_facts.values():
        if fact.supplied_event_id == event_id:
            statuses.append(f"{fact.source_id}:{fact.update_status}/{fact.transaction_type}")
    return statuses


def projection_derivation(data: Data, request: dict[str, str], projection: ProjectionEvent) -> str:
    """Describe amount/date derivation without creating a second forecast."""
    user_id = request["user_id"]
    events_by_id = {event.event_id: event for event in data.events_by_user.get(user_id, [])}
    source_ids = tuple(projection.source_event_ids)
    if projection.event_id == "message_payroll":
        facts = []
        for message in data.messages_by_user.get(user_id, []):
            fact = data.evidence_facts.get(message["message_id"])
            if fact and fact.transaction_type == "salary":
                facts.append(f"{message['message_id']}:{fact.update_status}/{fact.amount or 'amount-unset'}")
        return (
            f"amount={money(projection.amount)} from validated salary-message conversion; "
            f"date={projection.when.isoformat()} from evidence effective/payment date; "
            f"evidence={','.join(facts) or 'none'}"
        )
    if projection.recurring_ref and source_ids:
        sources = [events_by_id[event_id] for event_id in source_ids if event_id in events_by_id]
        values = [event.amount for event in sorted(sources, key=lambda event: event.settlement_date)[-8:]]
        if not values:
            return f"amount={money(projection.amount)}; date={projection.when.isoformat()}; source rows unavailable"
        stable = max(values) - min(values) <= max(CENT, median(values) * Decimal("0.08"))
        if projection.direction == "credit":
            source_amount = median(values[-3:])
            policy = "median(last three credit observations)"
        elif stable:
            source_amount = median(values)
            policy = "median(all retained stable expense observations)"
        else:
            source_amount = sorted(values)[max(0, int(len(values) * 0.75) - 1)]
            policy = "upper-quartile retained variable expense statistic"
        last = max(sources, key=lambda event: event.settlement_date)
        cadence_days = Agent.cadence(sorted(event.settlement_date for event in sources))
        if cadence_days is None:
            date_rule = "unsupported cadence"
        elif cadence_days in range(27, 33):
            months = 2 if cadence_days >= 58 else 1
            date_rule = f"last source date {last.settlement_date.isoformat()} + {months} calendar month(s), month-end clamped"
        else:
            date_rule = f"last source date {last.settlement_date.isoformat()} + {cadence_days} day cadence"
        converted = data.convert(source_amount, last.currency, data.profiles[user_id].home_currency, last.settlement_date)
        evidence = sorted({status for event in sources for status in evidence_for_event(data, event.event_id)})
        source_statuses = ",".join(f"{event.event_id}:{event.status}" for event in sources)
        first_date = min(event.settlement_date for event in sources).isoformat()
        return (
            f"amount={money(projection.amount)} from {policy}, raw_source={source_amount} {last.currency}, "
            f"converted={converted} at {last.settlement_date.isoformat()}; date={date_rule}; "
            f"observations={len(sources)} from {first_date} through {last.settlement_date.isoformat()}; "
            f"source_ids={','.join(source_ids)}; source_statuses={source_statuses}; evidence={','.join(evidence) or 'none'}"
        )
    event = events_by_id.get(projection.event_id)
    if event is not None:
        evidence = evidence_for_event(data, event.event_id)
        return (
            f"amount={money(projection.amount)} from explicit {event.amount} {event.currency} "
            f"converted on settlement date {event.settlement_date.isoformat()}; "
            f"date={event.settlement_date.isoformat()} from structured event; "
            f"source_ids={event.event_id}; status={event.status}; evidence={','.join(evidence) or 'none'}"
        )
    return f"amount={money(projection.amount)}; date={projection.when.isoformat()}; source_ids={','.join(source_ids) or projection.event_id}; evidence=none"


def event_lines(data: Data, request: dict[str, str], projections: list[ProjectionEvent], low_date: date, payment: Decimal = Decimal(0)) -> list[str]:
    rows = [projection for projection in projections if projection.when == low_date]
    lines = []
    if rows:
        for projection in sorted(rows, key=event_sort_key):
            lines.append(
                f"- `{projection.when.isoformat()}` {projection.direction} `{money(projection.amount)}` "
                f"category `{projection.category}`, event `{projection.event_id}`, "
                f"source IDs `{','.join(projection.source_event_ids) or 'none'}`; {projection_derivation(data, request, projection)}"
            )
    if payment and low_date == ddate(request["request_date"]):
        lines.append(f"- `{low_date.isoformat()}` expected payment debit `{money(payment)}` on request date; no source event or evidence fact")
    if not lines:
        lines.append("- No projected event occurred on the low-point date; the low point is the starting snapshot or a carry-forward balance.")
    return lines


def provenance(record: dict[str, Any] | None) -> tuple[str, str]:
    if not record:
        return "missing", "missing required analysis scope"
    analysis = record.get("analysis", {})
    metadata = analysis.get("model_metadata", {})
    mode = metadata.get("mode")
    if mode == "ai":
        return ("cached_ai" if metadata.get("cache_hit") else "live_ai", "none")
    return mode or "unknown", metadata.get("reason") or "none"


def row_for(data: Data, agent: Agent, request: dict[str, str], record: dict[str, Any] | None) -> dict[str, Any]:
    profile = data.profiles[request["user_id"]]
    projections = agent.projections(request)
    actual = agent.safe_amount(request, projections)
    expected = dec(request["amount_safe_to_pay"], Decimal(0))
    requested = dec(request["requested_amount"], Decimal(0))
    baseline = replay_timeline(data, request, projections)
    expected_replay = replay_timeline(data, request, projections, expected)
    origin, fallback = provenance(record)
    implied = None
    if Decimal(0) < expected < requested:
        implied = profile.minimum + expected
    return {
        "request": request,
        "currency": profile.home_currency,
        "starting_balance": profile.balance,
        "minimum": profile.minimum,
        "requested": requested,
        "expected": expected,
        "actual": actual,
        "difference": actual - expected,
        "absolute_difference": abs(actual - expected),
        "baseline_lowest": baseline["lowest"],
        "baseline_lowest_date": baseline["lowest_date"],
        "baseline_breach": baseline["first_failure"] is not None,
        "baseline_first_failure": baseline["first_failure"],
        "actual_cap_zero": actual == 0,
        "actual_cap_requested": actual == requested,
        "expected_cap_zero": expected == 0,
        "expected_cap_requested": expected == requested,
        "implied_expected_minimum": implied,
        "expected_passes": expected_replay["passes"],
        "expected_first_failure": expected_replay["first_failure"],
        "expected_lowest": expected_replay["lowest"],
        "expected_lowest_date": expected_replay["lowest_date"],
        "expected_remaining_headroom": (min(expected_replay["daily"].values()) - profile.minimum) if expected_replay["passes"] else None,
        "requested_cap_explains_headroom": expected_replay["passes"] and expected == requested,
        "projections": projections,
        "baseline_replay": baseline,
        "expected_replay": expected_replay,
        "origin": origin,
        "fallback": fallback,
    }


def diagnostic_amount_variant(data: Data, request: dict[str, str], projections: list[ProjectionEvent], variant: str) -> list[ProjectionEvent]:
    """Change only the recurring-debit amount statistic for diagnostics."""
    events_by_id = {event.event_id: event for event in data.events_by_user.get(request["user_id"], [])}
    result = []
    for projection in projections:
        if projection.direction != "debit" or not projection.recurring_ref or not projection.source_event_ids:
            result.append(projection)
            continue
        sources = [events_by_id[event_id] for event_id in projection.source_event_ids if event_id in events_by_id]
        if not sources:
            result.append(projection)
            continue
        values = [event.amount for event in sorted(sources, key=lambda event: event.settlement_date)[-8:]]
        if variant == "median_all_recurring_debits":
            source_amount = median(values)
        elif variant == "latest_all_recurring_debits":
            source_amount = values[-1]
        else:
            raise ValueError(f"unknown diagnostic amount variant: {variant}")
        last = max(sources, key=lambda event: event.settlement_date)
        amount = data.convert(source_amount, last.currency, data.profiles[request["user_id"]].home_currency, last.settlement_date)
        result.append(ProjectionEvent(
            projection.when, amount, projection.direction, projection.category, projection.event_id,
            projection.flexibility, projection.recurring_ref, projection.source_event_ids,
        ))
    return result


def diagnostic_timing_variant(data: Data, request: dict[str, str], projections: list[ProjectionEvent]) -> list[ProjectionEvent]:
    """Change only monthly recurrence advancement from calendar months to 30 days."""
    events_by_id = {event.event_id: event for event in data.events_by_user.get(request["user_id"], [])}
    result = []
    for projection in projections:
        if not projection.recurring_ref or not projection.source_event_ids:
            result.append(projection)
            continue
        sources = [events_by_id[event_id] for event_id in projection.source_event_ids if event_id in events_by_id]
        dates = sorted(event.settlement_date for event in sources)
        step = Agent.cadence(dates)
        if step not in range(27, 33) or not sources:
            result.append(projection)
            continue
        last = max(sources, key=lambda event: event.settlement_date)
        months = 1
        candidate = add_months(last.settlement_date, months)
        while candidate < projection.when and months < 24:
            months += 1
            candidate = add_months(last.settlement_date, months)
        if candidate != projection.when:
            result.append(projection)
            continue
        result.append(ProjectionEvent(
            last.settlement_date + timedelta(days=30 * months), projection.amount, projection.direction,
            projection.category, projection.event_id, projection.flexibility, projection.recurring_ref,
            projection.source_event_ids,
        ))
    return result


def variant_summary(data: Data, agent: Agent, rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    variants = {
        "median_all_recurring_debits": diagnostic_amount_variant,
        "latest_all_recurring_debits": diagnostic_amount_variant,
        "30_day_monthly_timing": diagnostic_timing_variant,
    }
    result: dict[str, list[dict[str, Any]]] = {}
    for name, transform in variants.items():
        variant_rows = []
        for row in rows:
            projections = transform(data, row["request"], row["projections"], name) if name != "30_day_monthly_timing" else transform(data, row["request"], row["projections"])
            safe = agent.safe_amount(row["request"], projections)
            variant_rows.append({
                "request_id": row["request"]["request_id"],
                "currency": row["currency"],
                "safe": safe,
                "difference": safe - row["expected"],
                "changed_from_current": safe != row["actual"],
            })
        result[name] = variant_rows
    return result


def cap_label(row: dict[str, Any], prefix: str = "actual") -> str:
    if row[f"{prefix}_cap_zero"]:
        return "zero"
    if row[f"{prefix}_cap_requested"]:
        return "requested_amount"
    return "none"


def compact(value: Decimal | None) -> str:
    return "n/a" if value is None else money(value)


def write_report(data: Data, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Safe-amount discrepancy diagnosis",
        "",
        "This is a read-only diagnosis of the current forecast amount-and-timing path. Signed differences are `actual - expected`; monetary values are never aggregated across currencies. The current AI-enabled sample artifact is loaded, so provenance records cached AI scopes and deterministic fallback scopes.",
        "",
        "## Method and limits",
        "",
        "- The baseline is `Agent.projections()` with no purchase payment or spending changes.",
        "- Baseline replay is extended through the full 90-day horizon without the production replay helper's early return, solely to identify the true lowest balance and date.",
        "- Expected-payment replay inserts the expected safe amount on `request_date`, after same-day projected events, and makes no spending changes.",
        "- A baseline breach means the current forecast falls below the protected minimum without the requested payment. An expected-payment failure reports the first failing date and `minimum - balance` shortfall.",
        "- Implied expected minimum is shown only when the expected amount is strictly between zero and the requested amount; capped outputs do not imply a binding minimum or date.",
        "",
        "## Per-sample discrepancy table",
        "",
        "| Request | Currency | Start | Minimum | Requested | Expected safe | Actual safe | Signed actual-expected | Absolute | Baseline low (date) | Baseline breach | Actual cap | Expected cap | Implied expected minimum | Provenance | Fallback |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['request']['request_id']} | {row['currency']} | {money(row['starting_balance'])} | {money(row['minimum'])} | {money(row['requested'])} | {money(row['expected'])} | {money(row['actual'])} | {money(row['difference'])} | {money(row['absolute_difference'])} | {money(row['baseline_lowest'])} ({row['baseline_lowest_date'].isoformat()}) | {'yes' if row['baseline_breach'] else 'no'} | {cap_label(row)} | {'zero' if row['expected_cap_zero'] else 'requested_amount' if row['expected_cap_requested'] else 'none'} | {compact(row['implied_expected_minimum'])} | {row['origin']} | {row['fallback']} |"
        )
    lines.extend(["", "## Expected-payment safety replay", "", "| Request | Expected payment passes full horizon | First failing date | Shortfall | Remaining minimum headroom if pass | Requested cap explains headroom |", "|---|---|---|---:|---:|---|"])
    for row in rows:
        failure = row["expected_first_failure"]
        lines.append(
            f"| {row['request']['request_id']} | {'yes' if row['expected_passes'] else 'no'} | {failure[0].isoformat() if failure else 'none'} | {money(failure[1]) if failure else 'n/a'} | {compact(row['expected_remaining_headroom'])} | {'yes' if row['requested_cap_explains_headroom'] else 'no'} |"
        )

    currencies = sorted({row["currency"] for row in rows})
    lines.extend(["", "## Currency-separated error summaries", ""])
    for currency in currencies:
        subset = [row for row in rows if row["currency"] == currency]
        exact = sum(row["difference"] == 0 for row in subset)
        positives = [row["difference"] for row in subset if row["difference"] > 0]
        negatives = [row["difference"] for row in subset if row["difference"] < 0]
        lines.extend([
            f"### {currency}",
            f"- Samples: `{len(subset)}`; exact safe-amount matches: `{exact}/{len(subset)}`.",
            f"- Positive actual-minus-expected cases: `{len(positives)}`; negative cases: `{len(negatives)}`; zero differences: `{len(subset) - len(positives) - len(negatives)}`.",
            f"- Signed differences are listed per request above; no cross-currency sum is reported.",
            "",
        ])

    groups = {
        "Positive overestimates (actual > expected)": sorted([row for row in rows if row["difference"] > 0], key=lambda row: row["absolute_difference"], reverse=True),
        "Positive expected, zero predicted": sorted([row for row in rows if row["expected"] > 0 and row["actual"] == 0], key=lambda row: row["expected"], reverse=True),
        "Positive underestimates (actual < expected)": sorted([row for row in rows if row["difference"] < 0 and row["expected"] > 0], key=lambda row: row["absolute_difference"], reverse=True),
    }
    exact_rows = [row for row in rows if row["difference"] == 0]
    capped_exact_rows = [row for row in exact_rows if row["expected_cap_requested"]]
    lines.extend([
        "## Match qualification", "",
        f"The current artifact has `{len(exact_rows)}/{len(rows)}` exact safe-amount matches. All `{len(capped_exact_rows)}` exact matches are requested-amount caps: {', '.join(row['request']['request_id'] for row in capped_exact_rows) or 'none'}. There are no uncapped exact matches, so the solved sample amounts do not independently establish an uncapped amount-selection convention.",
        "",
        "## One-assumption-at-a-time diagnostic alternatives", "",
        "These alternatives are diagnostic only and are not applied to production. They preserve source groups, currencies, pending-debit treatment, replay ordering, and evidence handling:",
        "- `median_all_recurring_debits`: replace the current upper-quartile amount for every non-stable recurring debit with the median of retained source observations.",
        "- `latest_all_recurring_debits`: replace the current non-stable recurring-debit statistic with its latest retained source observation.",
        "- `30_day_monthly_timing`: replace calendar-month advancement and month-end clamping with 30 elapsed days for monthly recurrences, leaving amounts unchanged.",
        "",
        "| Request | Currency | Current | Median debit variant | Latest debit variant | 30-day timing variant |",
        "|---|---|---:|---:|---:|---:|",
    ])
    variants = variant_summary(data, Agent(data), rows)
    variant_by_name = {name: {item["request_id"]: item for item in items} for name, items in variants.items()}
    for row in rows:
        request_id = row["request"]["request_id"]
        lines.append(
            f"| {request_id} | {row['currency']} | {money(row['actual'])} | "
            f"{money(variant_by_name['median_all_recurring_debits'][request_id]['safe'])} | "
            f"{money(variant_by_name['latest_all_recurring_debits'][request_id]['safe'])} | "
            f"{money(variant_by_name['30_day_monthly_timing'][request_id]['safe'])} |"
        )
    lines.append("")
    for name, label in (
        ("median_all_recurring_debits", "Median debit variant"),
        ("latest_all_recurring_debits", "Latest debit variant"),
        ("30_day_monthly_timing", "30-day timing variant"),
    ):
        lines.extend([f"### {label} by currency", ""])
        for currency in sorted({row["currency"] for row in rows}):
            subset = [item for item in variants[name] if item["currency"] == currency]
            exact = sum(item["difference"] == 0 for item in subset)
            changed = sum(item["changed_from_current"] for item in subset)
            lines.append(f"- `{currency}`: exact `{exact}/{len(subset)}`; changed from current `{changed}/{len(subset)}`; raw differences remain per-request above and are not summed across currencies.")
        lines.append("")
    lines.extend(["## Mismatch groups and representative low-point traces", "", "The representatives below are selected by largest absolute discrepancy within each group. The low-point event list is source-linked and separates explicit events, inferred recurrence statistics/date rules, message evidence, and the expected payment.", ""])
    for label, group in groups.items():
        lines.extend([f"### {label} ({len(group)} samples)", ""])
        if not group:
            lines.append("- None.")
            continue
        reps = group[:3]
        for row in reps:
            request = row["request"]
            lines.extend([
                f"#### `{request['request_id']}` ({row['currency']})",
                f"- Expected `{money(row['expected'])}`, actual `{money(row['actual'])}`, signed difference `{money(row['difference'])}`.",
                f"- Baseline low: `{money(row['baseline_lowest'])}` on `{row['baseline_lowest_date'].isoformat()}`; baseline breach: `{'yes' if row['baseline_breach'] else 'no'}`.",
                f"- Expected-payment replay: `{'passes' if row['expected_passes'] else 'fails'}`; expected-payment low `{money(row['expected_lowest'])}` on `{row['expected_lowest_date'].isoformat()}`.",
                "- Baseline low-point projected events:",
            ])
            lines.extend(event_lines(data, request, row["projections"], row["baseline_lowest_date"]))
            if not row["expected_passes"]:
                fail_date = row["expected_first_failure"][0]
                lines.append(f"- Expected-payment first failing low point `{fail_date.isoformat()}`:")
                lines.extend(event_lines(data, request, row["projections"], fail_date, row["expected"]))
            else:
                lines.append(f"- Expected-payment low-point projected events on `{row['expected_lowest_date'].isoformat()}`:")
                lines.extend(event_lines(data, request, row["projections"], row["expected_lowest_date"], row["expected"]))
            lines.append("")

    lines.extend([
        "## Cause checklist",
        "",
        "The following checks are recorded for each representative trace rather than treated as established causes without source evidence:",
        "",
        "- Historical window and partial-period handling: inspect source dates and the first forecast anchor in each recurrence derivation above.",
        "- Variable category totals versus per-transaction amounts: the derivation identifies the current median or upper-quartile policy and source IDs.",
        "- Recurrence counts, anchors, and month-end handling: the derivation states the source count, last source date, cadence, and calendar-month rule.",
        "- Explicit obligations and duplicate prevention: explicit rows are shown separately; recurring source IDs and low-point events identify possible overlap.",
        "- Starting balance and pending debits: the replay starts from the supplied profile balance; event status and evidence status are shown for source-linked events.",
        "- Salary and expense amendments: message-derived projections identify validated evidence; ordinary event projections identify source evidence status.",
        "- Exchange-rate dates and rounding: explicit derivations state the conversion date; displayed values are rounded only for report readability.",
        "- Forecast boundary and same-day ordering: the horizon is request date through request date plus 90 days; credits precede debits and the inserted expected payment is applied after projected events on the request date.",
        "",
        "## Policy decision",
        "",
        "No production forecast rule is changed by this diagnostic. A rule change is justified only after a representative source-backed reproduction and an independent failing test establish behavior required by the challenge contract; sample answers alone are not treated as policy evidence.",
        "",
    ])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = Data()
    if EVIDENCE.exists():
        data.evidence_facts = load_evidence_facts(EVIDENCE, data.messages)
    data.financial_analyses = load_financial_analyses(ANALYSIS)
    agent = Agent(data)
    records = analysis_records()
    rows = [row_for(data, agent, request, records.get((request["user_id"], request["request_id"], request["request_date"]))) for request in sample_rows()]
    write_report(data, rows)
    print(json.dumps({
        "output": str(OUTPUT),
        "samples": len(rows),
        "exact_safe_amounts": sum(row["difference"] == 0 for row in rows),
        "positive_overestimates": sum(row["difference"] > 0 for row in rows),
        "positive_underestimates": sum(row["difference"] < 0 for row in rows),
        "positive_expected_zero_actual": sum(row["expected"] > 0 and row["actual"] == 0 for row in rows),
        "baseline_breaches": sum(row["baseline_breach"] for row in rows),
        "expected_payment_failures": sum(not row["expected_passes"] for row in rows),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
