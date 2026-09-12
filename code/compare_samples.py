#!/usr/bin/env python3
"""Read-only comparison of the existing engine against solved samples.

This script deliberately does not call main() and never writes output.csv.
Run it from the repository root with:

    python3 code/compare_samples.py
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

from main import Agent, Data, ProjectionEvent, dec, ddate, fmt_amount  # noqa: E402

COMPARE_FIELDS = [
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
]


def load_samples() -> list[dict[str, str]]:
    with (ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse_plan(text: str) -> list[tuple[date, Decimal]]:
    if text == "none" or not text:
        return []
    result = []
    for token in text.split("|"):
        when_text, amount_text = token.split(":", 1)
        result.append((date.fromisoformat(when_text), dec(amount_text)))
    return result


def plans_equal(expected: str, actual: str) -> bool:
    return parse_plan(expected) == parse_plan(actual)


def explanation_consistent(row: dict[str, str]) -> bool:
    """Check recommendation semantics, not wording equality."""
    text = row["decision_explanation"].lower()
    method = row["recommended_payment_method"]
    plan = row["payment_plan"]
    if method == "not_recommended":
        return plan == "none" and any(word in text for word in ("do not", "not proceed", "cannot"))
    if plan == "none":
        return False
    if method == "installments":
        return "installment" in text
    if method == "partial_payment":
        return "pay" in text and "remainder" in text
    if method == "wait":
        return "wait" in text and "full" in text
    if method == "full_payment":
        return "pay" in text
    return False


def display_plan(plan: str) -> str:
    parsed = parse_plan(plan)
    if not parsed:
        return "none"
    return "|".join(f"{when.isoformat()}:{fmt_amount(amount)}" for when, amount in parsed)


def compare_samples(data: Data, agent: Agent, samples: list[dict[str, str]]) -> None:
    matches = {field: 0 for field in COMPARE_FIELDS}
    explanation_matches = 0
    exceptions: list[tuple[str, str]] = []
    mismatches: list[dict[str, object]] = []

    for expected in samples:
        request_id = expected["request_id"]
        try:
            actual = agent.decide(expected)
        except Exception as exc:  # report, do not skip
            exceptions.append((request_id, f"{type(exc).__name__}: {exc}"))
            continue

        row_mismatch: dict[str, object] = {"request_id": request_id, "fields": []}
        for field in COMPARE_FIELDS:
            if field == "amount_safe_to_pay":
                expected_value = dec(expected[field])
                actual_value = dec(actual[field])
                equal = expected_value == actual_value
                if not equal:
                    row_mismatch["amount_expected"] = expected_value
                    row_mismatch["amount_actual"] = actual_value
                    row_mismatch["amount_difference"] = actual_value - expected_value
            elif field == "payment_plan":
                equal = plans_equal(expected[field], actual[field])
                if not equal:
                    row_mismatch["plan_expected"] = display_plan(expected[field])
                    row_mismatch["plan_actual"] = display_plan(actual[field])
            else:
                equal = expected[field] == actual[field]
                if not equal:
                    row_mismatch[f"{field}_expected"] = expected[field]
                    row_mismatch[f"{field}_actual"] = actual[field]
            if equal:
                matches[field] += 1
            else:
                row_mismatch["fields"].append(field)

        if explanation_consistent(actual):
            explanation_matches += 1
        else:
            row_mismatch["fields"].append("explanation_consistency")

        if row_mismatch["fields"]:
            mismatches.append(row_mismatch)

    print("=== SAMPLE COMPARISON ===")
    print(f"samples: {len(samples)}")
    print(f"exceptions: {len(exceptions)}")
    print("\nPer-field matches (structural payment-plan comparison):")
    for field in COMPARE_FIELDS:
        print(f"  {field}: {matches[field]}/{len(samples)}")
    print(f"  explanation_consistency: {explanation_matches}/{len(samples)}")

    if exceptions:
        print("\nExceptions:")
        for request_id, error in exceptions:
            print(f"  {request_id}: {error}")
    else:
        print("\nExceptions: none")

    print("\nMismatches:")
    if not mismatches:
        print("  none")
    else:
        for item in mismatches:
            fields = ",".join(item["fields"])
            amount_part = ""
            if "amount_difference" in item:
                amount_part = (
                    f" amount_expected={item['amount_expected']}"
                    f" amount_actual={item['amount_actual']}"
                    f" amount_difference={item['amount_difference']}"
                )
            print(f"  {item['request_id']}: fields=[{fields}]{amount_part}")
            if "plan_expected" in item:
                print(f"    plan expected: {item['plan_expected']}")
                print(f"    plan actual:   {item['plan_actual']}")
            for key in sorted(item):
                if key.endswith("_expected") and key not in {"amount_expected", "plan_expected"}:
                    base = key[:-9]
                    print(f"    {base}: expected={item[key]!r} actual={item.get(base + '_actual')!r}")


def source_description(data: Data, user_id: str, event_id: str) -> str:
    event = next((e for e in data.events_by_user[user_id] if e.event_id == event_id), None)
    if event is None:
        return "no matching historical event"
    return (
        f"{event.description}; source_status={event.status}; "
        f"source_date={event.settlement_date.isoformat()}; source_currency={event.currency}; "
        f"linked_event_id={event.linked_event_id or '-'}"
    )


def replay_full_timeline(
    data: Data,
    request: dict[str, str],
    projections: list[ProjectionEvent],
) -> tuple[Decimal, date, list[tuple[date, ProjectionEvent, Decimal]]]:
    """Replay without Agent.replay's early return, for diagnostics only."""
    start = ddate(request["request_date"])
    end = start + timedelta(days=90)
    profile = data.profiles[request["user_id"]]
    by_day: dict[date, list[ProjectionEvent]] = defaultdict(list)
    for projection in projections:
        by_day[projection.when].append(projection)

    current = profile.balance
    lowest = current
    lowest_date = start
    ledger: list[tuple[date, ProjectionEvent, Decimal]] = []
    day = start
    while day <= end:
        events = sorted(by_day.get(day, []), key=lambda p: (p.direction != "credit", p.event_id))
        for projection in events:
            current += projection.amount if projection.direction == "credit" else -projection.amount
            ledger.append((day, projection, current))
            if current < lowest:
                lowest = current
                lowest_date = day
        day += timedelta(days=1)
    return lowest, lowest_date, ledger


def source_label(projection: ProjectionEvent) -> str:
    if projection.event_id == "message_payroll":
        return "message_payroll"
    if projection.recurring_ref:
        return f"inferred_from:{projection.recurring_ref}"
    return f"explicit:{projection.event_id}"


def trace_request_02(data: Data, agent: Agent, samples: list[dict[str, str]]) -> None:
    request = next(row for row in samples if row["request_id"] == "request_02")
    profile = data.profiles[request["user_id"]]
    start = ddate(request["request_date"])
    end = start + timedelta(days=90)

    explicit = agent.explicit_projection(request["user_id"], start, end, profile.home_currency)
    recurring = agent.recurring_projection(request["user_id"], start, end, profile.home_currency)
    explicit_keys = {(p.when, p.category, p.direction) for p in explicit}
    recurring_after_explicit = [
        p for p in recurring
        if (p.when, p.category, p.direction) not in explicit_keys
    ]
    message_salary = agent.salary_message_projection(
        request["user_id"], request["request_id"], start, end, profile.home_currency
    )
    message_dates = {p.when for p in message_salary}
    before_message = explicit + recurring_after_explicit
    removed_by_message = [
        p for p in before_message
        if p.category == "salary" and p.when in message_dates
    ]
    projections = agent.projections(request)
    lowest, lowest_date, ledger = replay_full_timeline(data, request, projections)
    safe = agent.safe_amount(request, projections)
    earliest = agent.earliest_full(request, projections)

    print("\n=== REQUEST_02 TRACE ===")
    print(f"request_date: {start.isoformat()}  forecast_end: {end.isoformat()}")
    print(f"starting_balance: {profile.balance} {profile.home_currency}")
    print(f"protected_minimum: {profile.minimum} {profile.home_currency}")
    print(f"requested_amount: {request['requested_amount']} {profile.home_currency}")
    print(f"desired_completion_date: {request['desired_completion_date']}")
    print(f"safe_amount_actual: {safe} {profile.home_currency}")
    expected_safe = dec(request["amount_safe_to_pay"])
    print(f"safe_amount_expected: {expected_safe} {profile.home_currency}")
    print(f"safe_amount_difference_actual_minus_expected: {safe - expected_safe} {profile.home_currency}")
    print(f"lowest_baseline_balance: {lowest} {profile.home_currency}")
    print(f"lowest_baseline_balance_date: {lowest_date.isoformat()}")
    print(f"explicit_projection_count: {len(explicit)}")
    print(f"recurring_projection_count_before_explicit_dedup: {len(recurring)}")
    print(f"recurring_projection_count_after_explicit_dedup: {len(recurring_after_explicit)}")
    print(f"message_salary_count: {len(message_salary)}")
    print(f"removed_by_message_same_date: {len(removed_by_message)}")
    print(f"earliest_full_actual: {earliest.isoformat() if earliest else 'none'}")

    print("\nMessages and extracted facts:")
    for message in agent.relevant_messages(request["user_id"], request["request_id"], start):
        print(f"  {message['message_id']} sent_at={message['sent_at']} source={message['source_type']}")
        print(f"    {message['message_text']}")
    print(f"  extracted_facts: {[(when.isoformat(), amount, source) for when, amount, source in agent.message_facts(agent.relevant_messages(request['user_id'], request['request_id'], start), profile.home_currency)]}")

    print("\nCurrency conversion and lifecycle notes:")
    converted = []
    for projection in projections:
        if projection.event_id in {"message_payroll"}:
            continue
        event = next((e for e in data.events_by_user[request["user_id"]] if e.event_id == projection.event_id), None)
        if event and event.currency != profile.home_currency:
            converted.append((projection.event_id, event.currency, profile.home_currency, projection.when.isoformat()))
    print(f"  converted_events: {converted or 'none; all request_02 event currencies are IDR'}")
    print("  linked_event_ids are loaded, but no linked-event graph reconciliation is performed by the current engine.")
    print("  status handling excludes failed/cancelled/unrealized events and excludes pending credits; pending debits remain.")
    print(f"  explicit-key recurrence removals: {len(recurring) - len(recurring_after_explicit)}")
    print(f"  message-date recurrence removals: {len(removed_by_message)}")

    print("\nEvery baseline cash-flow event contributing through the lowest date:")
    relevant_ledger = [entry for entry in ledger if entry[0] <= lowest_date]
    if not relevant_ledger:
        print("  none")
    for when, projection, balance_after in relevant_ledger:
        print(
            f"  {when.isoformat()} {projection.direction:6}"
            f" amount={projection.amount} {profile.home_currency}"
            f" category={projection.category}"
            f" source={source_label(projection)}"
            f" balance_after={balance_after}"
            f" ({source_description(data, request['user_id'], projection.event_id)})"
        )

    print("\nEvents on the lowest-balance date:")
    on_lowest = [entry for entry in ledger if entry[0] == lowest_date]
    if not on_lowest:
        print("  none; the lowest value is the starting balance")
    for when, projection, balance_after in on_lowest:
        print(
            f"  {when.isoformat()} {projection.direction:6}"
            f" amount={projection.amount} {profile.home_currency}"
            f" category={projection.category} source={source_label(projection)}"
            f" balance_after={balance_after}"
        )


def main() -> None:
    data = Data()
    agent = Agent(data)
    samples = load_samples()
    compare_samples(data, agent, samples)
    trace_request_02(data, agent, samples)


if __name__ == "__main__":
    main()
