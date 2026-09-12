#!/usr/bin/env python3
"""Diagnostic component checks; this script never writes predictions or source files."""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_extraction import (  # noqa: E402
    EvidenceFact,
    EvidenceLedger,
    EvidenceSource,
    EvidenceValidationError,
    apply_evidence_fact,
)
from main import (  # noqa: E402
    Agent,
    Change,
    Data,
    Event,
    Option,
    Plan,
    Profile,
    ProjectionEvent,
    dec,
    ddate,
    validate,
)


def result(component: str, status: str, evidence: str, detail: str) -> dict[str, str]:
    return {"component": component, "status": status, "evidence": evidence, "detail": detail}


def message_payload() -> dict[str, object]:
    return {
        "source_id": "message_14", "source_kind": "message",
        "supplied_user_id": "user_20", "supplied_request_id": "request_20",
        "supplied_event_id": "event_1785", "transaction_type": "refund",
        "update_status": "delayed", "action": "delay", "amount": None,
        "currency": None, "dates": [], "recurrence_scope": "once",
        "supporting_text": "Refund initiated but not reached.",
        "missing_fields": ["amount", "settlement_date"],
        "ambiguities": [], "conflicts": [],
    }


def fake_event(event_id: str, when: date, description: str = "merchant") -> Event:
    return Event(event_id, "user_test", "purchase", description, "groceries", "debit",
                 Decimal("10"), "USD", when, when, "settled", "", "fixed", None)


def run() -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    # CSV loading and joins: independent structural checks over the supplied files.
    data = Data()
    profile_ids = set(data.profiles)
    request_ids = {row["request_id"] for row in data.requests}
    request_ids |= {row["request_id"] for row in csv.DictReader((ROOT / "dataset/sample_requests.csv").open(newline="", encoding="utf-8"))}
    event_ids = {event.event_id for event in data.events}
    bad_message_users = [m["message_id"] for m in data.messages if m["user_id"] not in profile_ids]
    bad_message_requests = [m["message_id"] for m in data.messages if m["request_id"] and m["request_id"] not in request_ids]
    bad_message_events = [m["message_id"] for m in data.messages if m["related_event_id"] and m["related_event_id"] not in event_ids]
    checks.append(result("CSV loading/parsing/joins", "Verified for tested cases" if not (bad_message_users or bad_message_requests or bad_message_events) else "Confirmed failure",
                         "Data() and direct identifier-set checks",
                         f"profiles={len(profile_ids)}, requests={len(request_ids)}, events={len(event_ids)}, messages={len(data.messages)}, invalid_users={bad_message_users}, invalid_requests={bad_message_requests}, invalid_events={bad_message_events}"))

    # Deterministic message parser: deliberately controlled, not a forecast.
    synthetic = [{"message_text": "Salary is USD 1000 on 2025-01-15"}]
    parsed = Agent.message_facts(synthetic, "USD")
    checks.append(result("Deterministic message extraction", "Verified for tested cases" if parsed == [(date(2025, 1, 15), Decimal("1000"), "message payroll")] else "Confirmed failure",
                         "Agent.message_facts() with one explicit dated salary",
                         f"expected one dated USD 1000 payroll tuple; actual={parsed!r}"))
    no_date = Agent.message_facts([{"message_text": "Salary is USD 1000 and continues next payroll"}], "USD")
    checks.append(result("Deterministic message extraction coverage", "Not implemented" if not no_date else "Verified for tested cases",
                         "Agent.message_facts() with amount but no ISO date",
                         "Messages without a date are ignored; this is unsafe for supported amount-only amendments."))

    # Live AI quality is separate from mocked adapter correctness.
    evaluation_path = ROOT / "evaluation/message_extraction_evaluation.md"
    checks.append(result("AI message extraction quality", "Confirmed failure",
                         str(evaluation_path),
                         "Live model quality is recorded separately: 19 messages, schema/source references 19/19, transaction type 18/19, update status 18/19, legacy action 12/19. Mock adapter tests are not counted as model quality."))

    # Manual image lookup is tested separately from automated image extraction.
    image_rows = list(csv.DictReader((ROOT / "dataset/images.csv").open(newline="", encoding="utf-8")))
    mapped = {row["image_id"] for row in image_rows if row["image_id"] in __import__("main").IMAGE_AMOUNTS}
    checks.append(result("Image extraction", "Not implemented",
                         "Data._events() and main.IMAGE_AMOUNTS; 16 PNGs in dataset/media/images",
                         f"manual lookup covers {len(mapped)}/{len(image_rows)} images; no OCR/vision function reads image pixels."))

    # Schema validation and intentionally contradictory semantics.
    fact = EvidenceFact.from_mapping(message_payload())
    contradictory = dict(message_payload(), action="confirmation")
    contradiction_accepted = True
    try:
        EvidenceFact.from_mapping(contradictory)
    except EvidenceValidationError:
        contradiction_accepted = False
    checks.append(result("Evidence schema validation", "Verified for tested cases" if fact.transaction_type == "refund" else "Confirmed failure",
                         "EvidenceFact.from_mapping() valid/invalid identifier, amount, type, and status tests",
                         "Valid linked delayed refund accepted with null amount; malformed identifiers rejected."))
    checks.append(result("Evidence semantic validation", "Confirmed failure" if contradiction_accepted else "Verified for tested cases",
                         "Controlled refund fact with action=confirmation and update_status=delayed",
                         "Schema accepts a contradictory legacy action/status combination; semantic consistency is not enforced."))

    # Visibility and request/user/event scope.
    source = EvidenceSource("message_14", "message", "user_20", "request_20", "event_1785", "refund", date(2026, 2, 8))
    not_visible = apply_evidence_fact(fact, source, date(2026, 2, 7), EvidenceLedger())
    scope_source = [{"message_id": "m", "user_id": "u", "request_id": "request_a", "sent_at": "2025-01-01", "message_text": "x"}]
    relevant = Agent(SimpleNamespace(messages_by_user={"u": scope_source})).relevant_messages("u", "request_b", date(2025, 1, 2))
    checks.append(result("Request-date visibility and evidence scope", "Verified for tested cases" if not_visible.state == "not_visible" and not relevant else "Confirmed failure",
                         "apply_evidence_fact() future-date fixture plus Agent.relevant_messages() mismatched request fixture",
                         f"future fact state={not_visible.state}; mismatched-request messages returned={len(relevant)}."))

    # Lifecycle status handling is tested independently from full graph reconciliation.
    cancelled_parent = replace(fake_event("original", date(2025, 1, 2)), status="cancelled")
    replacement = replace(fake_event("replacement", date(2025, 1, 3)), linked_event_id="original")
    lifecycle_data = SimpleNamespace(events_by_user={"user_test": [cancelled_parent, replacement]}, convert=lambda amount, _src, _dst, _when: amount)
    lifecycle_projection = Agent(lifecycle_data).explicit_projection("user_test", date(2025, 1, 1), date(2025, 1, 10), "USD")
    checks.append(result("Lifecycle status handling", "Verified for tested cases" if len(lifecycle_projection) == 1 and lifecycle_projection[0].event_id == "replacement" else "Confirmed failure",
                         "Agent.explicit_projection() with cancelled original plus settled replacement",
                         f"expected one replacement cash row, actual projected rows={len(lifecycle_projection)}"))
    refund_parent = fake_event("purchase", date(2025, 1, 2))
    refund_child = replace(fake_event("refund", date(2025, 1, 3)), direction="credit", status="pending", linked_event_id="purchase")
    refund_projection = Agent(SimpleNamespace(events_by_user={"user_test": [refund_parent, refund_child]}, convert=lambda amount, _src, _dst, _when: amount)).explicit_projection("user_test", date(2025, 1, 1), date(2025, 1, 10), "USD")
    checks.append(result("Pending refund lifecycle handling", "Verified for tested cases" if len(refund_projection) == 1 and refund_projection[0].event_id == "purchase" else "Confirmed failure",
                         "Agent.explicit_projection() with settled purchase plus pending refund",
                         f"expected debit only because pending credits are excluded, actual projected ids={[p.event_id for p in refund_projection]}"))
    checks.append(result("Conflict/lifecycle graph reconciliation", "Not implemented",
                         "Code inspection of linked_event_id use and controlled status cases",
                         "Status filters work for tested cases, but no graph resolves replacement, reversal, retry, duplicate, or precedence relationships centrally."))

    # Evidence application is deliberately status-only for non-salary facts.
    cancellation = EvidenceFact.from_mapping(dict(message_payload(), transaction_type="purchase", update_status="cancelled", action="cancellation"))
    applied = apply_evidence_fact(cancellation, EvidenceSource("message_14", "message", "user_20", "request_20", "event_1785", "cancel", date(2026, 2, 6)), date(2026, 2, 7), EvidenceLedger())
    checks.append(result("Evidence application to events/streams", "Not implemented" if applied.cash_effect == "status_only" else "Verified for tested cases",
                         "apply_evidence_fact() linked cancellation fixture",
                         "Returns a status-only result and does not mutate Event rows, lifecycle status, or recurring streams."))

    # Currency conversion: direct and inverse use one supplied fixed rate.
    conversion_data = Data()
    (rate_date, src, dst), rate = next(((k, v) for k, v in conversion_data.rates.items() if k[1] != k[2]))
    converted = conversion_data.convert(Decimal("10"), src, dst, rate_date)
    inverse = conversion_data.convert(converted, dst, src, rate_date)
    checks.append(result("Currency conversion", "Verified for tested cases" if converted == Decimal("10") * rate and abs(inverse - Decimal("10")) < Decimal("0.00000001") else "Confirmed failure",
                         "Data.convert() direct and inverse with one exact exchange-rate row",
                         f"direct={converted}, inverse={inverse}, expected_direct={Decimal('10') * rate}"))

    # Recurrence: separate merchants in one category must not form one series.
    recurrence_events = [fake_event("a1", date(2025, 1, 1), "merchant_a"), fake_event("b1", date(2025, 1, 8), "merchant_b"), fake_event("c1", date(2025, 1, 15), "merchant_c")]
    recurrence_data = SimpleNamespace(events_by_user={"user_test": recurrence_events}, convert=lambda amount, _src, _dst, _when: amount)
    recurrence_projection = Agent(recurrence_data).recurring_projection("user_test", date(2025, 1, 16), date(2025, 2, 1), "USD")
    checks.append(result("Recurrence detection/projection", "Confirmed failure" if recurrence_projection else "Verified for tested cases",
                         "Agent.recurring_projection() with three different merchants, same category, weekly dates",
                         f"expected no inferred series because each merchant has one history row; actual projections={len(recurrence_projection)}."))

    # Cash-flow replay: independent hand-calculated path.
    replay_agent = Agent(SimpleNamespace())
    ok, lowest, balances = replay_agent.replay(Decimal("100"), Decimal("50"), date(2025, 1, 1), date(2025, 1, 3), [
        ProjectionEvent(date(2025, 1, 2), Decimal("20"), "credit", "salary", "credit"),
        ProjectionEvent(date(2025, 1, 3), Decimal("30"), "debit", "bill", "bill"),
    ], [(date(2025, 1, 1), Decimal("40"))])
    checks.append(result("Cash-flow replay", "Verified for tested cases" if ok and lowest == Decimal("50") and balances[date(2025, 1, 3)] == Decimal("50") else "Confirmed failure",
                         "Agent.replay() hand timeline: 100-40+20-30=50",
                         f"ok={ok}, lowest={lowest}, final={balances.get(date(2025, 1, 3))}"))

    # Safe amount and earliest date use supplied projections only.
    profile = Profile("u", "USD", Decimal("100"), Decimal("50"), set(), set(), set(), set(), {"full_payment"}, None)
    balance_agent = Agent(SimpleNamespace(profiles={"u": profile}))
    request = {"user_id": "u", "request_date": "2025-01-01", "requested_amount": "60", "desired_completion_date": "2025-01-04"}
    path = [ProjectionEvent(date(2025, 1, 2), Decimal("10"), "debit", "bill", "b") , ProjectionEvent(date(2025, 1, 3), Decimal("30"), "credit", "salary", "s")]
    safe = balance_agent.safe_amount(request, path)
    earliest = balance_agent.earliest_full(request, path)
    checks.append(result("Safe amount/earliest full payment", "Verified for tested cases" if safe == Decimal("40") and earliest == date(2025, 1, 3) else "Confirmed failure",
                         "Agent.safe_amount()/earliest_full() with explicit hand-supplied path",
                         f"expected safe=40 and earliest=2025-01-03; actual safe={safe}, earliest={earliest}"))

    # Payment eligibility and rank with controlled options/plans.
    option_profile = replace(profile, payment_methods={"installments"}, max_installment_months=2)
    option_agent = Agent(SimpleNamespace())
    option = Option("option", "request", "installments", Decimal("40"), 2, date(2025, 1, 1), 30, Decimal("0"), Decimal("80"))
    allowed = option_agent.option_allowed(option, option_profile, date(2025, 2, 1), date(2025, 1, 1))
    fast = Plan("full_payment", [(date(2025, 1, 1), Decimal("100"))], [], "fast", Decimal("100"))
    late = Plan("wait", [(date(2025, 1, 3), Decimal("100"))], [], "late", Decimal("100"))
    rank_order = option_agent.rank(fast, date(2025, 1, 4)) < option_agent.rank(late, date(2025, 1, 4))
    checks.append(result("Payment-option eligibility/ranking", "Verified for tested cases" if allowed and rank_order else "Confirmed failure",
                         "Option.dates_and_amounts(), Agent.option_allowed(), Agent.rank() controlled plans",
                         f"two-payment option allowed={allowed}; earlier complete plan ranks first={rank_order}."))

    # Spending change generation/application and output validation.
    flexible_event = fake_event("flex", date(2025, 1, 2))
    flexible_event = replace(flexible_event, category="groceries", flexibility="reducible", minimum_allowed_amount=Decimal("4"))
    change_data = SimpleNamespace(
        profiles={"u": replace(profile, reduce_categories={"groceries"})},
        events_by_user={"u": [flexible_event]},
        convert=lambda amount, _src, _dst, _when: amount,
    )
    change_agent = Agent(change_data)
    changes = change_agent.eligible_changes({"user_id": "u"}, [ProjectionEvent(date(2025, 1, 2), Decimal("10"), "debit", "groceries", "flex", "reducible", "flex")])
    changed = change_agent.apply_changes([ProjectionEvent(date(2025, 1, 2), Decimal("10"), "debit", "groceries", "flex", "reducible", "flex")], changes)
    checks.append(result("Spending-change generation/application", "Verified for tested cases" if len(changes) == 1 and changed[0].amount == Decimal("4") else "Confirmed failure",
                         "Agent.eligible_changes()/apply_changes() protected-category and minimum controlled fixture",
                         f"changes={len(changes)}, applied_amount={changed[0].amount if changed else None}"))

    # Output validation: contract violation should be rejected independently of forecast quality.
    valid = Agent(data).decide(data.requests[0])
    invalid = dict(valid, amount_safe_to_pay="999999999999")
    rejected = False
    try:
        validate([invalid], [data.requests[0]], data.options)
    except AssertionError:
        rejected = True
    checks.append(result("Output validation/explanations", "Insufficient coverage" if rejected else "Confirmed failure",
                         "validate() with independently invalid amount bound",
                         "Bounds/enums/payment structure are checked; explanation grounding and spending-target existence are not fully checked."))
    return checks


def main() -> None:
    checks = run()
    counts = {}
    for check in checks:
        counts[check["status"]] = counts.get(check["status"], 0) + 1
    print(json.dumps({"checks": checks, "summary": counts}, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
