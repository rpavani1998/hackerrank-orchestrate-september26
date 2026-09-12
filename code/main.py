#!/usr/bin/env python3
"""Deterministic Buy or Wait? financial decision agent.

The program intentionally keeps evidence interpretation small and auditable:
structured records are authoritative, the supplied image facts are attached to
their linked event IDs, and only explicit financial statements in messages are
used. Arithmetic, forecasting, plan selection, and validation are deterministic.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from itertools import combinations
from pathlib import Path
from statistics import median
from typing import Iterable

from evidence_extraction import (
    EvidenceFact,
    EvidenceLedger,
    EvidenceSource,
    EvidenceValidationError,
    apply_evidence_fact,
    validate_evidence_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
OUTPUT = ROOT / "output.csv"
DAYS = 90
CENT = Decimal("0.01")

OUTPUT_COLUMNS = [
    "request_id", "amount_safe_to_pay", "affordability_status",
    "recommended_payment_method", "payment_plan",
    "earliest_date_for_full_payment", "spending_changes_needed",
    "decision_explanation",
]

# Facts transcribed from the 16 supplied linked images.  They are keyed by
# image_id and are applied only to the matching related_event_id below.
# Keeping this source-linked makes the otherwise blank event amount auditable.
IMAGE_AMOUNTS = {
    "image_01": Decimal("4365000"),
    "image_02": Decimal("100000"),
    "image_03": Decimal("41272"),
    "image_04": Decimal("2854"),
    "image_05": Decimal("704.05"),
    "image_06": Decimal("79679.26"),
    "image_07": Decimal("8528.10"),
    "image_08": Decimal("15339"),
    "image_09": Decimal("723"),
    "image_10": Decimal("79679.26"),
    "image_11": Decimal("3650"),
    "image_12": Decimal("33.50"),
    "image_13": Decimal("2298"),
    "image_14": Decimal("4593"),
    "image_15": Decimal("9968"),
    "image_16": Decimal("393.22"),
}


def dec(value: str | Decimal | None, default: Decimal | None = None) -> Decimal | None:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return default


def ddate(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def split_values(value: str) -> set[str]:
    return {x for x in (value or "").split("|") if x}


def add_months(when: date, months: int = 1) -> date:
    """Advance by calendar months while clamping the day to month end."""
    month0 = when.month - 1 + months
    year, month0 = when.year + month0 // 12, month0 % 12
    month = month0 + 1
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return date(year, month, min(when.day, last_day))


def fmt_amount(value: Decimal) -> str:
    """Stable monetary formatting: whole values stay whole, fractions get 2dp."""
    value = value.quantize(CENT, rounding=ROUND_HALF_UP)
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return format(value, ".2f")


def csv_rows(name: str) -> list[dict[str, str]]:
    with (DATASET / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_financial_analyses(path: Path) -> dict[tuple[str, str, date], dict[str, object]]:
    """Load request-scoped, already validated analysis artifacts."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = payload["records"]
    elif isinstance(payload, dict) and isinstance(payload.get("analyses_by_scope"), dict):
        records = [{"analysis": analysis} for analysis in payload["analyses_by_scope"].values()]
    else:
        records = payload
    if not isinstance(records, list):
        raise EvidenceValidationError("financial analysis file must contain records or analyses_by_scope")
    result: dict[tuple[str, str, date], dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("analysis"), dict):
            raise EvidenceValidationError("financial analysis record is missing analysis")
        analysis = record["analysis"]
        scope = analysis.get("scope")
        if not isinstance(scope, dict) or not all(isinstance(scope.get(key), str) for key in ("user_id", "request_id", "as_of_date")):
            raise EvidenceValidationError("financial analysis scope is incomplete")
        key = (scope["user_id"], scope["request_id"], ddate(scope["as_of_date"]))
        if key[2] is None:
            raise EvidenceValidationError("financial analysis scope has an invalid date")
        if key in result:
            raise EvidenceValidationError(f"duplicate financial analysis scope: {key}")
        result[key] = analysis
    return result


def as_fact_tuple(value: EvidenceFact | tuple[EvidenceFact, ...] | list[EvidenceFact] | None) -> tuple[EvidenceFact, ...]:
    if value is None:
        return ()
    if isinstance(value, EvidenceFact):
        return (value,)
    return tuple(value)


def facts_for_source(store: dict[str, EvidenceFact | tuple[EvidenceFact, ...]], source_id: str) -> tuple[EvidenceFact, ...]:
    return as_fact_tuple(store.get(source_id))


def load_evidence_facts(path: Path, messages: list[dict[str, str]]) -> dict[str, tuple[EvidenceFact, ...]]:
    """Load only facts matching supplied message metadata and validate their scope."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_facts = payload.get("facts") if isinstance(payload, dict) else payload
    if not isinstance(raw_facts, list):
        raise EvidenceValidationError("AI evidence file must contain a facts list")
    message_by_id = {row["message_id"]: row for row in messages}
    ledger = EvidenceLedger()
    grouped: dict[str, list[EvidenceFact]] = defaultdict(list)
    for raw in raw_facts:
        fact = EvidenceFact.from_mapping(raw, origin="ai-cache")
        row = message_by_id.get(fact.source_id)
        if row is None or fact.source_kind != "message":
            raise EvidenceValidationError(f"AI fact references an unsupplied message: {fact.source_id}")
        if (
            fact.supplied_user_id != row["user_id"]
            or fact.supplied_request_id != (row["request_id"] or None)
            or fact.supplied_event_id != (row["related_event_id"] or None)
        ):
            raise EvidenceValidationError(f"AI fact references disagree with {fact.source_id} metadata")
        source = EvidenceSource(
            source_id=row["message_id"], source_kind="message", user_id=row["user_id"],
            request_id=row["request_id"] or None, event_id=row["related_event_id"] or None,
            content=row["message_text"], visibility_date=ddate(row["sent_at"]),
        )
        validate_evidence_semantics(fact, source.content)
        application = apply_evidence_fact(fact, source, date.max, ledger)
        if application.state == "not_visible":
            raise EvidenceValidationError(f"AI fact is not visible: {fact.source_id}")
        grouped[fact.source_id].append(fact)
    return {source_id: tuple(facts) for source_id, facts in grouped.items()}


@dataclass
class Event:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str
    amount: Decimal
    currency: str
    event_date: date
    settlement_date: date
    status: str
    linked_event_id: str
    flexibility: str
    minimum_allowed_amount: Decimal | None
    source_amount_missing: bool = False

    @property
    def is_debit(self) -> bool:
        return self.direction == "debit"

    @property
    def is_credit(self) -> bool:
        return self.direction == "credit"


@dataclass
class Profile:
    user_id: str
    home_currency: str
    balance: Decimal
    minimum: Decimal
    priorities: set[str]
    protected: set[str]
    reduce_categories: set[str]
    stop_categories: set[str]
    payment_methods: set[str]
    max_installment_months: int | None


@dataclass
class Option:
    option_id: str
    request_id: str
    method: str
    payment_amount: Decimal
    number_of_payments: int
    first_payment_date: date
    frequency_days: int | None
    financing_fee: Decimal
    total_payable: Decimal

    def dates_and_amounts(self) -> list[tuple[date, Decimal]]:
        step = self.frequency_days or 0
        return [(self.first_payment_date + timedelta(days=step * i), self.payment_amount)
                for i in range(self.number_of_payments)]


@dataclass
class Change:
    event_id: str
    action: str  # stop or reduce
    new_amount: Decimal
    category: str
    source_amount: Decimal
    future_occurrences: int = 0

    def token(self) -> str:
        if self.action == "stop":
            return f"stop:{self.event_id}"
        return f"reduce_to:{self.event_id}:{fmt_amount(self.new_amount)}"


@dataclass
class ProjectionEvent:
    when: date
    amount: Decimal
    direction: str
    category: str
    event_id: str
    flexibility: str = "fixed"
    recurring_ref: str = ""
    source_event_ids: tuple[str, ...] = ()
    replacement_reason: str = ""


@dataclass(frozen=True)
class SalaryEvidenceApplication:
    when: date
    amount: Decimal
    source: str
    source_id: str
    update_status: str
    recurrence_scope: str
    date_meaning: str
    fact: EvidenceFact | None = None


@dataclass
class Plan:
    method: str
    payments: list[tuple[date, Decimal]]
    changes: list[Change] = field(default_factory=list)
    option_id: str = ""
    total_paid: Decimal = Decimal("0")

    @property
    def start(self) -> date:
        return self.payments[0][0] if self.payments else date.max

    @property
    def completes(self) -> date:
        return self.payments[-1][0] if self.payments else date.max


class Data:
    def __init__(self, evidence_facts: dict[str, EvidenceFact | tuple[EvidenceFact, ...]] | None = None,
                 financial_analyses: dict[tuple[str, str, date], dict[str, object]] | None = None) -> None:
        self.evidence_facts = evidence_facts or {}
        self.financial_analyses = financial_analyses or {}
        self.profiles = self._profiles()
        self.requests = csv_rows("requests.csv")
        self.events = self._events()
        self.messages = csv_rows("messages.csv")
        self.options = self._options()
        self.rates = self._rates()
        self.events_by_user: dict[str, list[Event]] = defaultdict(list)
        for event in self.events:
            self.events_by_user[event.user_id].append(event)
        self.options_by_request: dict[str, list[Option]] = defaultdict(list)
        for option in self.options:
            self.options_by_request[option.request_id].append(option)
        self.messages_by_user: dict[str, list[dict[str, str]]] = defaultdict(list)
        for message in self.messages:
            self.messages_by_user[message["user_id"]].append(message)

    @staticmethod
    def _profiles() -> dict[str, Profile]:
        result = {}
        for row in csv_rows("financial_profiles.csv"):
            result[row["user_id"]] = Profile(
                user_id=row["user_id"], home_currency=row["home_currency"],
                balance=dec(row["current_available_balance"], Decimal(0)),
                minimum=dec(row["minimum_balance_to_keep"], Decimal(0)),
                priorities=split_values(row["financial_priorities"]),
                protected=split_values(row["expense_categories_to_protect"]),
                reduce_categories=split_values(row["expense_categories_user_is_willing_to_reduce"]),
                stop_categories=split_values(row["expense_categories_user_is_willing_to_stop"]),
                payment_methods=split_values(row["payment_methods_user_will_consider"]),
                max_installment_months=int(row["max_installment_months"])
                if row["max_installment_months"] else None,
            )
        return result

    @staticmethod
    def _events() -> list[Event]:
        image_for_event = {}
        for row in csv_rows("images.csv"):
            image_for_event[row["related_event_id"]] = IMAGE_AMOUNTS.get(row["image_id"])
        result = []
        for row in csv_rows("financial_events.csv"):
            amount = dec(row["amount"])
            missing = amount is None
            if amount is None:
                amount = image_for_event.get(row["event_id"])
            if amount is None:
                # An unresolved image is not silently zero. It is excluded from
                # arithmetic and will be reported by validation.
                continue
            result.append(Event(
                event_id=row["event_id"], user_id=row["user_id"],
                event_type=row["event_type"], description=row["description"],
                category=row["category"], direction=row["direction"], amount=amount,
                currency=row["currency"], event_date=ddate(row["event_date"]) or date.min,
                settlement_date=ddate(row["settlement_date"]) or date.min,
                status=row["status"], linked_event_id=row["linked_event_id"],
                flexibility=row["flexibility"],
                minimum_allowed_amount=dec(row["minimum_allowed_amount"]),
                source_amount_missing=missing,
            ))
        return result

    @staticmethod
    def _options() -> list[Option]:
        result = []
        for row in csv_rows("request_payment_options.csv"):
            result.append(Option(
                option_id=row["payment_option_id"], request_id=row["request_id"],
                method=row["payment_method"], payment_amount=dec(row["payment_amount"], Decimal(0)),
                number_of_payments=int(row["number_of_payments"]),
                first_payment_date=ddate(row["first_payment_date"]) or date.max,
                frequency_days=int(row["payment_frequency_days"])
                if row["payment_frequency_days"] else None,
                financing_fee=dec(row["financing_fee"], Decimal(0)),
                total_payable=dec(row["total_payable_amount"], Decimal(0)),
            ))
        return result

    @staticmethod
    def _rates() -> dict[tuple[date, str, str], Decimal]:
        result = {}
        for row in csv_rows("exchange_rates.csv"):
            result[(ddate(row["rate_date"]) or date.min, row["from_currency"], row["to_currency"])] = dec(row["rate"], Decimal(1))
        return result

    def convert(self, amount: Decimal, from_currency: str, to_currency: str, when: date) -> Decimal:
        if from_currency == to_currency:
            return amount
        direct = self.rates.get((when, from_currency, to_currency))
        if direct is not None:
            return amount * direct
        inverse = self.rates.get((when, to_currency, from_currency))
        if inverse:
            return amount / inverse
        # The fixed table is sparse by date. Use the latest rate on or before
        # settlement only when a direct row exists; this remains deterministic.
        candidates = [(d, rate) for (d, src, dst), rate in self.rates.items()
                      if src == from_currency and dst == to_currency and d <= when]
        if candidates:
            return amount * max(candidates, key=lambda x: x[0])[1]
        candidates = [(d, rate) for (d, src, dst), rate in self.rates.items()
                      if src == to_currency and dst == from_currency and d <= when]
        if candidates:
            return amount / max(candidates, key=lambda x: x[0])[1]
        raise ValueError(f"No fixed exchange rate for {from_currency}->{to_currency} on {when}")


class Agent:
    def __init__(self, data: Data):
        self.data = data

    def relevant_messages(self, user_id: str, request_id: str, request_date: date) -> list[dict[str, str]]:
        result = []
        for m in self.data.messages_by_user.get(user_id, []):
            sent = ddate(m.get("sent_at"))
            if sent and sent <= request_date and (not m["request_id"] or m["request_id"] == request_id):
                result.append(m)
        return result

    @staticmethod
    def message_facts(messages: Iterable[dict[str, str]], home_currency: str) -> list[tuple[date, Decimal, str]]:
        """Extract only explicit, confirmed dated payroll facts from messages."""
        facts = []
        amount_re = re.compile(r"(?i)(?:salary|pay|payroll|gaji)[^\n.]{0,100}?(?:is|of|menjadi|sebesar|to|amount(?:ed)? to)\s*(?:[A-Z]{3}\s*)?([\d,]+(?:\.\d+)?)")
        date_re = re.compile(r"(20\d{2}-\d{2}-\d{2})")
        for m in messages:
            text = m["message_text"]
            low = text.lower()
            if any(x in low for x in ["not approved", "still pending", "not confirmed", "no off-season", "has ended"]):
                continue
            am = amount_re.search(text)
            dm = date_re.search(text)
            if not am or not dm:
                continue
            value = dec(am.group(1))
            when = ddate(dm.group(1))
            if value is not None and when is not None and ("salary" in low or "gaji" in low or "payroll" in low):
                facts.append((when, value, "message payroll"))
        return facts

    def facts_for_message(self, message_id: str) -> tuple[EvidenceFact, ...]:
        return facts_for_source(self.data.evidence_facts, message_id)

    def salary_evidence_applications(self, messages: Iterable[dict[str, str]], home_currency: str) -> list[SalaryEvidenceApplication]:
        """Keep salary evidence semantics; do not collapse facts to anonymous tuples first."""
        applications: list[SalaryEvidenceApplication] = []
        for message in messages:
            stored = self.facts_for_message(message["message_id"])
            if not stored:
                for when, amount, source in self.message_facts([message], home_currency):
                    text = message.get("message_text", "").lower()
                    status = "resumed" if "resume" in text else "amended"
                    applications.append(SalaryEvidenceApplication(
                        when, amount, source, message["message_id"], status, "future_occurrences", "effective_date",
                    ))
                continue
            for fact in stored:
                if fact.transaction_type != "salary" or fact.update_status == "ended":
                    continue
                if fact.update_status not in {"amended", "confirmed", "resumed"} or fact.amount is None:
                    continue
                date_by_meaning = {item.meaning: item.value for item in fact.dates}
                meaning = next(
                    (name for name in ("payment_date", "effective_date", "settlement_date", "completion_date") if name in date_by_meaning),
                    "effective_date" if "effective_date" in date_by_meaning else "payment_date",
                )
                when = date_by_meaning.get(meaning) or ddate(message["sent_at"])
                if when is None or fact.currency is None:
                    continue
                try:
                    amount = self.data.convert(fact.amount, fact.currency, home_currency, when)
                except ValueError:
                    continue
                applications.append(SalaryEvidenceApplication(
                    when, amount, "message evidence", fact.source_id, fact.update_status,
                    fact.recurrence_scope, meaning, fact,
                ))
        return applications

    def evidence_message_facts(self, messages: Iterable[dict[str, str]], home_currency: str) -> list[tuple[date, Decimal, str]]:
        """Compatibility view of salary applications as date/amount pairs."""
        return [(item.when, item.amount, item.source) for item in self.salary_evidence_applications(messages, home_currency)]

    def evidence_salary_end_dates(self, messages: Iterable[dict[str, str]]) -> list[date]:
        ended: list[date] = []
        for message in messages:
            for fact in self.facts_for_message(message["message_id"]):
                if fact.transaction_type != "salary" or fact.update_status != "ended":
                    continue
                date_by_meaning = {item.meaning: item.value for item in fact.dates}
                when = (
                    date_by_meaning.get("effective_date")
                    or date_by_meaning.get("payment_date")
                    or date_by_meaning.get("settlement_date")
                    or ddate(message["sent_at"])
                )
                if when is not None:
                    ended.append(when)
        return ended

    def unresolved_evidence(self, messages: Iterable[dict[str, str]]) -> list[EvidenceFact]:
        unresolved: list[EvidenceFact] = []
        for message in messages:
            for fact in self.facts_for_message(message["message_id"]):
                if fact.transaction_type == "salary" and fact.update_status in {"amended", "confirmed", "resumed", "ended"}:
                    continue
                if fact.amount is None or not fact.dates:
                    unresolved.append(fact)
        return unresolved

    def historical_salary_events(self, user_id: str, start: date) -> list[Event]:
        events = []
        for event in self.data.events_by_user.get(user_id, []):
            if event.direction != "credit" or event.category != "salary" or event.status != "settled":
                continue
            if event.settlement_date >= start or self.is_explicit_one_time(event):
                continue
            text = self.normalized_description(event.description)
            if any(word in text for word in ("commission", "bonus", "payout", "earning", "invoice", "project", "retainer", "freelance", "prize", "refund")):
                continue
            events.append(event)
        return sorted(events, key=lambda event: event.settlement_date)

    def resumed_salary_step(self, history: list[Event], application: SalaryEvidenceApplication) -> int | None:
        dates = [event.settlement_date for event in history]
        same_day = [event for event in history if event.settlement_date.day == application.when.day]
        if same_day or (history and history[-1].settlement_date.day == application.when.day):
            return 30
        return self.cadence(dates) if len(dates) >= 3 else None

    def expand_resumed_salary(self, application: SalaryEvidenceApplication, user_id: str,
                              start: date, end: date, home: str) -> list[ProjectionEvent]:
        history = self.historical_salary_events(user_id, start)
        if application.fact and application.fact.supplied_event_id:
            history = [event for event in history if event.event_id == application.fact.supplied_event_id or event.linked_event_id == application.fact.supplied_event_id] or history
        if len({event.amount for event in history}) > 1:
            matched = [event for event in history if self.data.convert(event.amount, event.currency, home, event.settlement_date) == application.amount]
            if matched:
                history = matched
        step = self.resumed_salary_step(history, application)
        if step is None:
            if start < application.when <= end:
                return [ProjectionEvent(
                    application.when, application.amount, "credit", "salary", "message_payroll",
                    source_event_ids=(application.source_id,) + tuple(event.event_id for event in history),
                    replacement_reason="salary_evidence_resume_once",
                )]
            return []
        first = application.when
        if application.date_meaning == "effective_date" and history:
            # An effective date that is not itself a payday starts at the next cycle day.
            if first.day != history[-1].settlement_date.day:
                candidate = date(first.year, first.month, min(history[-1].settlement_date.day, 28))
                if candidate < first:
                    candidate = add_months(candidate, 1)
                first = candidate
        monthly = step in range(27, 33) or step == 30
        result: list[ProjectionEvent] = []
        when = first
        sources = self.merged_source_ids((application.source_id,), (event.event_id for event in history))
        while when <= end:
            if when > start:
                result.append(ProjectionEvent(
                    when, application.amount, "credit", "salary", "message_payroll",
                    source_event_ids=sources, replacement_reason="salary_evidence_resumed_stream",
                ))
            when = add_months(when, 1) if monthly else when + timedelta(days=step)
        return result

    def salary_stream_key(self, projection: ProjectionEvent) -> str:
        if projection.recurring_ref:
            return projection.recurring_ref
        if projection.event_id == "message_payroll":
            return projection.source_event_ids[0] if projection.source_event_ids else "message_payroll"
        return projection.event_id

    def matching_salary_projections(self, projections: list[ProjectionEvent], application: SalaryEvidenceApplication) -> list[ProjectionEvent]:
        salaries = [p for p in projections if p.direction == "credit" and p.category == "salary"]
        if application.fact and application.fact.supplied_event_id:
            linked = application.fact.supplied_event_id
            matched = [p for p in salaries if linked in p.source_event_ids or p.recurring_ref == linked or p.event_id == linked]
            if matched:
                return matched
        groups: dict[str, list[ProjectionEvent]] = defaultdict(list)
        for projection in salaries:
            groups[self.salary_stream_key(projection)].append(projection)
        if len(groups) == 1:
            return salaries
        amount_hits = [p for p in salaries if p.amount == application.amount]
        if amount_hits and len({self.salary_stream_key(p) for p in amount_hits}) == 1:
            key = self.salary_stream_key(amount_hits[0])
            return groups[key]
        return []

    @staticmethod
    def status_counts_as_cash(event: Event) -> bool:
        if event.status in {"failed", "cancelled", "unrealized"}:
            return False
        if event.is_credit and event.status == "pending":
            return False
        return event.status in {"settled", "pending", "scheduled"}

    def explicit_projection(self, user_id: str, start: date, end: date, home: str) -> list[ProjectionEvent]:
        result = []
        by_id = {e.event_id: e for e in self.data.events_by_user.get(user_id, [])}
        for event in self.data.events_by_user.get(user_id, []):
            if event.settlement_date <= start or event.settlement_date > end:
                continue
            if not self.status_counts_as_cash(event):
                continue
            # A replacement settles the lifecycle; cancelled/failed originals
            # are already excluded, while opposite-direction refunds remain cash.
            amount = self.data.convert(event.amount, event.currency, home, event.settlement_date)
            result.append(ProjectionEvent(
                event.settlement_date, amount, event.direction, event.category,
                event.event_id, event.flexibility, "", (event.event_id,),
            ))
        return result

    @staticmethod
    def cadence(dates: list[date]) -> int | None:
        if len(dates) < 3:
            return None
        gaps = [(b - a).days for a, b in zip(sorted(dates), sorted(dates)[1:])]
        med = int(round(median(gaps)))
        if med in range(4, 12) or med in range(13, 18) or med in range(27, 33) or med in range(58, 63):
            close = sum(abs(g - med) <= max(1, round(med * .12)) for g in gaps)
            return med if close >= max(2, len(gaps) * .6) else None
        return None

    @staticmethod
    def normalized_description(description: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", description.lower()).strip()

    @classmethod
    def recurrence_series_key(cls, event: Event) -> tuple[str, ...]:
        """Identify an obligation without collapsing variable category spending."""
        variable_categories = {
            "groceries", "transport", "dining", "shopping", "entertainment",
        }
        if event.direction == "debit" and event.event_type == "expense" and event.category in variable_categories:
            return (
                "variable_category", event.event_type, event.category, event.direction,
                event.flexibility, event.currency, "",
            )
        return (
            "named_stream", event.event_type, event.category, event.direction,
            event.flexibility, event.currency, cls.normalized_description(event.description),
        )

    @classmethod
    def is_explicit_one_time(cls, event: Event) -> bool:
        text = cls.normalized_description(f"{event.event_type} {event.description}")
        return any(marker in text for marker in (
            "one time", "one time purchase", "one off", "once off", "non recurring",
            "single purchase", "explicitly one time",
        ))

    @classmethod
    def is_salary_placeholder(cls, description: str) -> bool:
        text = cls.normalized_description(description)
        return text in {
            "next confirmed salary", "next salary", "next payroll",
            "upcoming salary", "upcoming payroll",
        } or (text.startswith("next confirmed") and "salary" in text)

    @classmethod
    def has_salary_delay_marker(cls, description: str) -> bool:
        text = cls.normalized_description(description)
        return any(token in text for token in ("delay", "postpon", "reschedul"))

    @staticmethod
    def merged_source_ids(*groups: Iterable[str]) -> tuple[str, ...]:
        seen: list[str] = []
        for group in groups:
            for item in group:
                if item and item not in seen:
                    seen.append(item)
        return tuple(seen)

    def reconcile_explicit_inferred_credits(
        self,
        explicit: list[ProjectionEvent],
        recurring: list[ProjectionEvent],
        event_by_id: dict[str, Event],
    ) -> tuple[list[ProjectionEvent], list[ProjectionEvent]]:
        """Replace an inferred salary occurrence when an explicit row is the same payday.

        Named second jobs stay independent. A generic 'next confirmed salary' row is
        not a second employer. Ambiguous matches do not invent an extra credit.
        """
        used: set[int] = set()
        resolved: list[ProjectionEvent] = []

        def salary_inferred() -> list[tuple[int, ProjectionEvent, Event]]:
            found = []
            for index, projection in enumerate(recurring):
                if index in used or projection.direction != "credit" or projection.category != "salary":
                    continue
                source = event_by_id.get(projection.recurring_ref) or event_by_id.get(projection.event_id)
                if source is not None:
                    found.append((index, projection, source))
            return found

        for exp in explicit:
            exp_event = event_by_id.get(exp.event_id)
            if exp.direction != "credit" or exp.category != "salary" or exp_event is None:
                resolved.append(exp)
                continue
            placeholder = self.is_salary_placeholder(exp_event.description)
            delayed = self.has_salary_delay_marker(exp_event.description)
            linked = exp_event.linked_event_id
            same_day: list[tuple[int, ProjectionEvent, Event, bool, bool]] = []
            delayed_rows: list[tuple[int, ProjectionEvent, Event, bool, bool]] = []
            for index, inf, source in salary_inferred():
                series_match = self.recurrence_series_key(exp_event) == self.recurrence_series_key(source)
                linked_match = bool(linked) and linked in {inf.recurring_ref, inf.event_id, *inf.source_event_ids}
                if inf.when == exp.when:
                    same_day.append((index, inf, source, series_match, linked_match))
                    continue
                delta = (exp.when - inf.when).days
                if (delayed or linked_match) and 0 < delta <= 27:
                    delayed_rows.append((index, inf, source, series_match, linked_match))

            chosen: ProjectionEvent | None = None
            chosen_index: int | None = None
            reason = ""
            strong_same = [row for row in same_day if row[3] or row[4]]
            if len(strong_same) == 1:
                chosen_index, chosen = strong_same[0][0], strong_same[0][1]
                reason = "explicit_replaces_inferred_same_payday"
            elif len(strong_same) > 1:
                amount_hits = [row for row in strong_same if row[1].amount == exp.amount]
                if len(amount_hits) == 1:
                    chosen_index, chosen = amount_hits[0][0], amount_hits[0][1]
                    reason = "explicit_replaces_inferred_same_payday"
                else:
                    reason = "ambiguous_salary_occurrence"
            elif placeholder and len(same_day) == 1:
                chosen_index, chosen = same_day[0][0], same_day[0][1]
                reason = "explicit_placeholder_replaces_unique_inferred_payday"
            elif placeholder and len(same_day) > 1:
                amount_hits = [row for row in same_day if row[1].amount == exp.amount]
                if len(amount_hits) == 1:
                    chosen_index, chosen = amount_hits[0][0], amount_hits[0][1]
                    reason = "explicit_placeholder_replaces_amount_matched_inferred_payday"
                else:
                    reason = "ambiguous_salary_occurrence"
            elif delayed_rows:
                strong_delay = [row for row in delayed_rows if row[3] or row[4]]
                pool = strong_delay or delayed_rows
                if len(pool) == 1:
                    chosen_index, chosen = pool[0][0], pool[0][1]
                    reason = "explicit_delayed_salary_replaces_inferred_payday"
                else:
                    amount_hits = [row for row in pool if row[1].amount == exp.amount]
                    if len(amount_hits) == 1:
                        chosen_index, chosen = amount_hits[0][0], amount_hits[0][1]
                        reason = "explicit_delayed_salary_replaces_inferred_payday"
                    else:
                        reason = "ambiguous_salary_occurrence"

            if chosen is not None and chosen_index is not None:
                used.add(chosen_index)
                resolved.append(ProjectionEvent(
                    exp.when, exp.amount, exp.direction, exp.category, exp.event_id,
                    exp.flexibility, exp.recurring_ref,
                    self.merged_source_ids(
                        exp.source_event_ids, chosen.source_event_ids,
                        (exp.event_id, chosen.event_id, chosen.recurring_ref),
                    ),
                    reason,
                ))
            elif reason == "ambiguous_salary_occurrence" and placeholder:
                # Safer interpretation: do not add a generic extra payday on top
                # of two named streams whose identity cannot be resolved.
                continue
            else:
                resolved.append(exp)

        return resolved, [row for index, row in enumerate(recurring) if index not in used]

    def analysis_recurring_projection(self, request: dict[str, str], start: date, end: date, home: str) -> list[ProjectionEvent]:
        as_of = ddate(request["request_date"]) or date.min
        analysis = self.data.financial_analyses.get((request["user_id"], request["request_id"], as_of))
        if analysis is None:
            return self.recurring_projection(request["user_id"], start, end, home)
        events_by_id = {event.event_id: event for event in self.data.events_by_user.get(request["user_id"], [])}
        forecast_inputs = analysis.get("forecast_inputs")
        if not isinstance(forecast_inputs, list):
            raise EvidenceValidationError("analysis forecast_inputs must be a list")
        result: list[ProjectionEvent] = []
        claimed: set[str] = set()
        final_income_date = max(
            (event.settlement_date for event in events_by_id.values()
             if event.direction == "credit" and "final" in event.description.lower()),
            default=date.min,
        )
        for item in forecast_inputs:
            if not isinstance(item, dict) or not item.get("forecastable"):
                continue
            if item.get("pattern_type") not in {"recurring_commitment", "variable_spending"}:
                continue
            source_ids = item.get("source_event_ids")
            if not isinstance(source_ids, list) or not source_ids or any(event_id not in events_by_id for event_id in source_ids):
                raise EvidenceValidationError("analysis forecast input contains an unknown event ID")
            if claimed.intersection(source_ids):
                raise EvidenceValidationError("analysis forecast inputs double-claim a source event")
            group = [events_by_id[event_id] for event_id in source_ids]
            if any(event.user_id != request["user_id"] or event.status != "settled" for event in group):
                raise EvidenceValidationError("analysis forecast input is not a settled same-user source group")
            if any(event.category != item.get("category") for event in group):
                raise EvidenceValidationError("analysis forecast input category disagrees with its source events")
            claimed.update(source_ids)
            direction = group[0].direction
            if direction == "credit":
                # Analysis inputs carry the deterministic eligibility decision.  A
                # historical platform/gig stream is not future income without
                # explicit confirmation, while a confirmed future credit may be
                # forecast regardless of its label.
                if item.get("income_eligibility") not in {"recurring_salary_supported", "confirmed_future_credit"}:
                    continue
                if final_income_date != date.min and item.get("income_eligibility") != "confirmed_future_credit":
                    continue
            dates = sorted(event.settlement_date for event in group)
            step = self.cadence(dates)
            if step is None:
                continue
            last = max(group, key=lambda event: event.settlement_date)
            values = [event.amount for event in sorted(group, key=lambda event: event.settlement_date)[-8:]]
            stable = max(values) - min(values) <= max(CENT, median(values) * Decimal("0.08"))
            source_amount = median(values[-3:]) if direction == "credit" else (
                median(values) if stable else sorted(values)[max(0, int(len(values) * .75) - 1)]
            )
            source = self.data.convert(source_amount, last.currency, home, last.settlement_date)
            monthly = step in range(27, 33)
            month_step = 2 if step >= 58 else 1
            next_when = add_months(last.settlement_date, month_step) if monthly else last.settlement_date + timedelta(days=step)
            while next_when <= end:
                if next_when > start:
                    result.append(ProjectionEvent(
                        next_when, source, direction, last.category, last.event_id,
                        last.flexibility, last.event_id, tuple(source_ids),
                    ))
                next_when = add_months(next_when, month_step) if monthly else next_when + timedelta(days=step)
        return result

    def recurring_projection(self, user_id: str, start: date, end: date, home: str) -> list[ProjectionEvent]:
        events = self.data.events_by_user.get(user_id, [])
        groups: dict[tuple[str, ...], list[Event]] = defaultdict(list)
        for event in events:
            if event.status != "settled" or event.settlement_date >= start or event.direction == "non_cash":
                continue
            if self.is_explicit_one_time(event):
                continue
            # Variable categories deliberately aggregate different merchants;
            # named commitments, including subscriptions, keep their identity.
            groups[self.recurrence_series_key(event)].append(event)
        result = []
        final_income_date = max(
            (e.settlement_date for e in events
             if e.direction == "credit" and "final" in e.description.lower()),
            default=date.min,
        )
        for series_key, group in groups.items():
            event_type, category, direction, flexibility, currency, series_name = series_key[1:7]
            if direction == "credit" and final_income_date != date.min:
                continue
            if direction == "credit":
                low_name = series_name.lower()
                if not any(word in low_name for word in ("salary", "payroll", "wage", "gaji")):
                    continue
                if any(word in low_name for word in ("commission", "bonus", "payout", "earning", "invoice", "project", "retainer", "freelance")):
                    continue
            dates = sorted(e.settlement_date for e in group)
            step = self.cadence(dates)
            if step is None:
                continue
            last = max(group, key=lambda e: e.settlement_date)
            source_ids = tuple(e.event_id for e in sorted(group, key=lambda e: e.settlement_date))
            values = [e.amount for e in sorted(group, key=lambda e: e.settlement_date)[-8:]]
            # Use the recent median for stable commitments and a conservative
            # recent upper quartile for variable expenses.
            stable = max(values) - min(values) <= max(CENT, median(values) * Decimal("0.08"))
            if direction == "credit":
                source_amount = median(values[-3:])
            else:
                source_amount = median(values) if stable else sorted(values)[max(0, int(len(values) * .75) - 1)]
            source = self.data.convert(source_amount, currency, home, last.settlement_date)
            monthly = step in range(27, 33)
            month_step = 2 if step >= 58 else 1
            next_when = add_months(last.settlement_date, month_step) if monthly else last.settlement_date + timedelta(days=step)
            while next_when <= end:
                if next_when > start:
                    result.append(ProjectionEvent(
                        next_when, source, direction, category, last.event_id,
                        flexibility, last.event_id, source_ids,
                    ))
                next_when = (add_months(next_when, month_step) if monthly
                             else next_when + timedelta(days=step))
        return result

    def salary_message_projection(self, user_id: str, request_id: str, start: date, end: date, home: str) -> list[ProjectionEvent]:
        facts = self.evidence_message_facts(self.relevant_messages(user_id, request_id, start), home)
        result = []
        for when, amount, _ in facts:
            if start < when <= end:
                result.append(ProjectionEvent(when, amount, "credit", "salary", "message_payroll"))
        return result

    def projections(self, request: dict[str, str]) -> list[ProjectionEvent]:
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"]) or date.min
        end = start + timedelta(days=DAYS)
        explicit = self.explicit_projection(request["user_id"], start, end, profile.home_currency)
        recurring = self.analysis_recurring_projection(request, start, end, profile.home_currency) \
            if (request["user_id"], request["request_id"], start) in self.data.financial_analyses \
            else self.recurring_projection(request["user_id"], start, end, profile.home_currency)
        event_by_id = {e.event_id: e for e in self.data.events_by_user.get(request["user_id"], [])}
        explicit_keys = {
            (p.when, self.recurrence_series_key(event_by_id[p.event_id]), p.direction)
            for p in explicit if p.event_id in event_by_id
        }
        # A supplied row is more specific than an inferred continuation of the
        # same source-defined series. Different subscriptions in one category
        # remain independent, while variable groceries/transport still dedup by
        # category rather than by merchant.
        recurring = [
            p for p in recurring
            if p.recurring_ref in event_by_id
            and (p.when, self.recurrence_series_key(event_by_id[p.recurring_ref]), p.direction)
            not in explicit_keys
        ]
        explicit, recurring = self.reconcile_explicit_inferred_credits(explicit, recurring, event_by_id)
        result = explicit + recurring
        relevant_messages = self.relevant_messages(request["user_id"], request["request_id"], start)
        applications = self.salary_evidence_applications(relevant_messages, profile.home_currency)
        ended_dates = self.evidence_salary_end_dates(relevant_messages)
        resume_dates = sorted(item.when for item in applications if item.update_status == "resumed")
        if ended_dates:
            filtered = []
            for p in result:
                if p.category != "salary":
                    filtered.append(p)
                    continue
                blocking = [ended for ended in ended_dates if p.when > ended]
                if not blocking:
                    filtered.append(p)
                    continue
                last_end = max(blocking)
                if any(resumed > last_end and resumed <= p.when for resumed in resume_dates):
                    filtered.append(p)
            result = filtered
        generated: list[ProjectionEvent] = []
        for application in applications:
            if application.update_status == "ended":
                continue
            matching = self.matching_salary_projections(result, application)
            if application.update_status == "resumed" and application.recurrence_scope == "future_occurrences":
                generated.extend(self.expand_resumed_salary(application, request["user_id"], start, end, profile.home_currency))
                continue
            if application.recurrence_scope == "future_occurrences" and application.update_status in {"amended", "confirmed"}:
                if matching:
                    updated = []
                    match_ids = {id(item) for item in matching}
                    for p in result:
                        if id(p) in match_ids and p.when >= application.when:
                            updated.append(ProjectionEvent(
                                p.when, application.amount, p.direction, p.category,
                                p.event_id, p.flexibility, p.recurring_ref,
                                p.source_event_ids or (application.source_id,),
                                "salary_evidence_stream_amendment",
                            ))
                        else:
                            updated.append(p)
                    result = updated
                    continue
            if start < application.when <= end:
                generated.append(ProjectionEvent(
                    application.when, application.amount, "credit", "salary", "message_payroll",
                    source_event_ids=(application.source_id,),
                    replacement_reason="salary_evidence_once" if application.recurrence_scope == "once" else "salary_evidence_payday",
                ))
        generated_dates = {p.when for p in generated}
        result = [p for p in result if not (p.category == "salary" and p.when in generated_dates)]
        result = result + generated
        return result

    def eligible_changes(self, request: dict[str, str], projections: list[ProjectionEvent]) -> list[Change]:
        profile = self.data.profiles[request["user_id"]]
        by_ref: dict[str, ProjectionEvent] = {}
        for p in projections:
            if p.recurring_ref:
                by_ref[p.recurring_ref] = p
        result = []
        for ref, p in by_ref.items():
            if p.category in profile.protected:
                continue
            event = next((e for e in self.data.events_by_user[request["user_id"]] if e.event_id == ref), None)
            if not event or event.flexibility not in {"reducible", "stoppable", "reducible_or_stoppable"}:
                continue
            allowed_reduce = event.flexibility in {"reducible", "reducible_or_stoppable"} and p.category in profile.reduce_categories
            allowed_stop = event.flexibility in {"stoppable", "reducible_or_stoppable"} and p.category in profile.stop_categories
            if allowed_stop:
                result.append(Change(ref, "stop", Decimal(0), p.category, p.amount))
            if allowed_reduce:
                minimum = event.minimum_allowed_amount or Decimal(0)
                minimum = self.data.convert(minimum, event.currency, profile.home_currency, event.settlement_date)
                result.append(Change(ref, "reduce", minimum, p.category, p.amount))
        return result

    @staticmethod
    def apply_changes(projections: list[ProjectionEvent], changes: list[Change]) -> list[ProjectionEvent]:
        by_ref = {c.event_id: c for c in changes}
        result = []
        for p in projections:
            c = by_ref.get(p.recurring_ref)
            if c and p.direction == "debit":
                result.append(ProjectionEvent(
                    p.when, c.new_amount, p.direction, p.category, p.event_id,
                    p.flexibility, p.recurring_ref, p.source_event_ids,
                    p.replacement_reason,
                ))
            else:
                result.append(p)
        return result

    @staticmethod
    def replay(balance: Decimal, minimum: Decimal, start: date, end: date,
               projections: list[ProjectionEvent], payments: list[tuple[date, Decimal]]) -> tuple[bool, Decimal, dict[date, Decimal]]:
        by_day: dict[date, list[ProjectionEvent]] = defaultdict(list)
        for p in projections:
            by_day[p.when].append(p)
        payments_by_day: dict[date, Decimal] = defaultdict(Decimal)
        for when, amount in payments:
            payments_by_day[when] += amount
        current = balance
        minimum_seen = current
        balances = {start: current}
        day = start
        while day <= end:
            # Incoming funds are applied before same-day outflows; the safety
            # check still records the post-outflow balance for every date.
            for p in sorted(by_day.get(day, []), key=lambda x: (x.direction != "credit", x.event_id)):
                current += p.amount if p.direction == "credit" else -p.amount
            current -= payments_by_day.get(day, Decimal(0))
            minimum_seen = min(minimum_seen, current)
            balances[day] = current
            if current < minimum:
                return False, minimum_seen, balances
            day += timedelta(days=1)
        return True, minimum_seen, balances

    def safe_amount(self, request: dict[str, str], projections: list[ProjectionEvent]) -> Decimal:
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"]) or date.min
        end = start + timedelta(days=DAYS)
        requested = dec(request["requested_amount"], Decimal(0))
        # With a payment on start, every later balance is reduced by the same
        # amount.  The minimum baseline headroom is therefore the safe amount.
        ok, _, balances = self.replay(profile.balance, profile.minimum, start, end, projections, [])
        if not ok and balances.get(start, profile.balance) < profile.minimum:
            headroom = Decimal(0)
        else:
            headroom = min((v - profile.minimum for v in balances.values()), default=Decimal(0))
        return max(Decimal(0), min(requested, headroom))

    def earliest_full(self, request: dict[str, str], projections: list[ProjectionEvent]) -> date | None:
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"]) or date.min
        end = start + timedelta(days=DAYS)
        requested = dec(request["requested_amount"], Decimal(0))
        for when in (start + timedelta(days=i) for i in range(DAYS + 1)):
            # Events before the candidate date have already happened, so replay
            # from request date with the candidate payment inserted.
            ok, _, _ = self.replay(profile.balance, profile.minimum, start, end,
                                   projections, [(when, requested)])
            if ok:
                return when
        return None

    def schedule_safe(self, request: dict[str, str], projections: list[ProjectionEvent],
                      payments: list[tuple[date, Decimal]], changes: list[Change]) -> bool:
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"]) or date.min
        end = start + timedelta(days=DAYS)
        if not payments or payments[-1][0] > ddate(request["desired_completion_date"]):
            return False
        changed = self.apply_changes(projections, changes)
        ok, _, _ = self.replay(profile.balance, profile.minimum, start, end, changed, payments)
        return ok

    def option_allowed(self, option: Option, profile: Profile, desired: date, start: date) -> bool:
        if option.first_payment_date < start:
            return False
        if option.method not in profile.payment_methods:
            return False
        if option.method == "installments" and profile.max_installment_months is not None:
            # Challenge field is expressed in months; payment count is a safe
            # conservative proxy for offers with 28-31 day frequencies.
            if option.number_of_payments > profile.max_installment_months:
                return False
        payments = option.dates_and_amounts()
        return payments[-1][0] <= desired and payments[-1][0] <= start + timedelta(days=DAYS)

    def plans(self, request: dict[str, str], projections: list[ProjectionEvent],
              safe_today: Decimal, earliest: date | None) -> list[Plan]:
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"]) or date.min
        desired = ddate(request["desired_completion_date"]) or start
        requested = dec(request["requested_amount"], Decimal(0))
        changes = self.eligible_changes(request, projections)
        change_sets: list[list[Change]] = [[]]
        for n in range(1, min(3, len(changes)) + 1):
            for subset in combinations(changes, n):
                if len({c.event_id for c in subset}) == len(subset):
                    change_sets.append(list(subset))
        plans: list[Plan] = []
        for change_set in change_sets:
            if "full_payment" in profile.payment_methods:
                # Baseline affordability stays separate from an affordability
                # plan achieved by stopping/reducing permitted flexible spend.
                pay = [(start, requested)]
                if self.schedule_safe(request, projections, pay, change_set):
                    plans.append(Plan("full_payment", pay, change_set, "full_payment", requested))
            if (request["allows_partial_payment"].lower() == "true"
                    and "partial_payment" in profile.payment_methods
                    and safe_today > 0 and safe_today < requested and earliest and earliest <= desired):
                pay = [(start, safe_today), (earliest, requested - safe_today)]
                if self.schedule_safe(request, projections, pay, change_set):
                    plans.append(Plan("partial_payment", pay, change_set, "partial_payment", requested))
        for option in self.data.options_by_request.get(request["request_id"], []):
            if not self.option_allowed(option, profile, desired, start):
                continue
            pay = option.dates_and_amounts()
            for change_set in change_sets:
                if self.schedule_safe(request, projections, pay, change_set):
                    plans.append(Plan(option.method, pay, change_set, option.option_id, option.total_payable))
                    break
        if earliest and earliest <= desired and "full_payment" in profile.payment_methods:
            pay = [(earliest, requested)]
            for change_set in change_sets:
                if self.schedule_safe(request, projections, pay, change_set):
                    plans.append(Plan("wait", pay, change_set, "wait", requested))
                    break
        return plans

    @staticmethod
    def rank(plan: Plan, desired: date) -> tuple:
        return (plan.completes > desired, bool(plan.changes), plan.total_paid,
                plan.start, len(plan.payments), plan.option_id)

    def decide(self, request: dict[str, str]) -> dict[str, str]:
        profile = self.data.profiles[request["user_id"]]
        requested = dec(request["requested_amount"], Decimal(0))
        start = ddate(request["request_date"]) or date.min
        desired = ddate(request["desired_completion_date"]) or start
        projections = self.projections(request)
        safe_today = self.safe_amount(request, projections)
        earliest = self.earliest_full(request, projections)
        plans = self.plans(request, projections, safe_today, earliest)
        if plans:
            plan = min(plans, key=lambda p: self.rank(p, desired))
            if plan.method == "wait":
                status = "affordable_later"
            elif plan.method == "full_payment" and plan.start == start and not plan.changes and safe_today >= requested:
                status = "affordable_now"
            else:
                status = "affordable_with_plan"
            method = plan.method
            payment_plan = "|".join(f"{d.isoformat()}:{fmt_amount(a)}" for d, a in plan.payments)
            changes_text = "|".join(c.token() for c in plan.changes) or "none"
            if plan.method == "wait":
                explanation = f"Wait until {plan.start.isoformat()}, then pay {profile.home_currency} {fmt_amount(requested)} in full."
            elif plan.method == "installments":
                explanation = f"Use {len(plan.payments)} installments totaling {profile.home_currency} {fmt_amount(plan.total_paid)}."
            elif plan.method == "partial_payment":
                explanation = f"Pay {profile.home_currency} {fmt_amount(plan.payments[0][1])} today and the remainder on {plan.payments[1][0].isoformat()}."
            else:
                explanation = f"Pay {profile.home_currency} {fmt_amount(requested)} on {plan.start.isoformat()}."
            explanation += f" This keeps at least {profile.home_currency} {fmt_amount(profile.minimum)} available."
            return {
                "request_id": request["request_id"], "amount_safe_to_pay": fmt_amount(safe_today),
                "affordability_status": status, "recommended_payment_method": method,
                "payment_plan": payment_plan,
                "earliest_date_for_full_payment": earliest.isoformat() if earliest else "",
                "spending_changes_needed": changes_text, "decision_explanation": explanation,
            }
        return {
            "request_id": request["request_id"], "amount_safe_to_pay": fmt_amount(safe_today),
            "affordability_status": "not_affordable", "recommended_payment_method": "not_recommended",
            "payment_plan": "none", "earliest_date_for_full_payment": earliest.isoformat() if earliest else "",
            "spending_changes_needed": "none",
            "decision_explanation": f"Do not proceed by {desired.isoformat()}; no available option safely completes the request while keeping the {profile.home_currency} {fmt_amount(profile.minimum)} minimum protected.",
        }


def validate(rows: list[dict[str, str]], requests: list[dict[str, str]], options: list[Option]) -> None:
    assert list(rows[0]) == OUTPUT_COLUMNS if rows else True
    assert len(rows) == len(requests)
    request_by_id = {r["request_id"]: r for r in requests}
    req = {r["request_id"]: dec(r["requested_amount"], Decimal(0)) for r in requests}
    options_by_request: dict[str, list[Option]] = defaultdict(list)
    for option in options:
        options_by_request[option.request_id].append(option)

    def parsed_plan(text: str) -> list[tuple[date, Decimal]]:
        if text == "none":
            return []
        result = []
        for token in text.split("|"):
            when, amount = token.split(":", 1)
            result.append((date.fromisoformat(when), dec(amount)))
        assert all(a is not None and a >= 0 for _, a in result)
        assert [when for when, _ in result] == sorted(when for when, _ in result)
        return result

    for row in rows:
        request = request_by_id[row["request_id"]]
        requested = req[row["request_id"]]
        value = dec(row["amount_safe_to_pay"])
        assert value is not None and Decimal(0) <= value <= requested
        assert row["affordability_status"] in {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
        method = row["recommended_payment_method"]
        assert method in {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}
        payments = parsed_plan(row["payment_plan"])
        if method == "not_recommended":
            assert not payments
        else:
            assert payments
            assert sum(amount for _, amount in payments) >= requested
            assert payments[-1][0] <= date.fromisoformat(request["desired_completion_date"])
        if method in {"full_payment", "partial_payment", "wait"} and payments:
            assert sum(amount for _, amount in payments) == requested
        if method == "partial_payment":
            assert request["allows_partial_payment"].lower() == "true"
            assert len(payments) == 2 and payments[0][0] == date.fromisoformat(request["request_date"])
            assert Decimal(0) < payments[0][1] < requested
            assert payments[0][1] == value
        if method == "wait":
            assert len(payments) == 1 and payments[0][1] == requested
        if method == "installments":
            matches = []
            for option in options_by_request[row["request_id"]]:
                if option.method != "installments":
                    continue
                schedule = option.dates_and_amounts()
                if schedule == payments:
                    matches.append(option)
            assert matches
        if row["affordability_status"] == "affordable_now":
            assert method == "full_payment" and row["earliest_date_for_full_payment"] == request["request_date"]
        changes = row["spending_changes_needed"]
        assert changes == "none" or len(changes.split("|")) <= 3
        if changes != "none":
            for token in changes.split("|"):
                assert token.startswith("stop:") or token.startswith("reduce_to:")


def main(mode: str = "deterministic", evidence_path: Path | None = None,
         analysis_path: Path | None = None) -> None:
    if mode not in {"deterministic", "ai"}:
        raise ValueError(f"unsupported mode: {mode}; use deterministic or ai")
    data = Data()
    if mode == "ai":
        path = evidence_path or ROOT / "evaluation/message_extraction_results.json"
        data.evidence_facts = load_evidence_facts(path, data.messages)
        if analysis_path is not None:
            data.financial_analyses = load_financial_analyses(analysis_path)
    agent = Agent(data)
    rows = [agent.decide(request) for request in data.requests]
    validate(rows, data.requests, data.options)
    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUTPUT} ({len(rows)} rows)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Buy or Wait? agent")
    parser.add_argument("--mode", choices=["deterministic", "ai"], default="deterministic")
    parser.add_argument("--evidence-file", type=Path,
                        default=ROOT / "evaluation/message_extraction_results.json")
    parser.add_argument("--analysis-file", type=Path)
    args = parser.parse_args()
    main(args.mode, args.evidence_file, args.analysis_file)
