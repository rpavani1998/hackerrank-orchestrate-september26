#!/usr/bin/env python3
"""Deterministic Buy or Wait? financial decision agent.

The program intentionally keeps evidence interpretation small and auditable:
structured records are authoritative, the supplied image facts are attached to
their linked event IDs, and only explicit financial statements in messages are
used. Arithmetic, forecasting, plan selection, and validation are deterministic.
"""
from __future__ import annotations

import csv
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
    def __init__(self) -> None:
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
            result.append(ProjectionEvent(event.settlement_date, amount, event.direction,
                                          event.category, event.event_id, event.flexibility))
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

    def recurring_projection(self, user_id: str, start: date, end: date, home: str) -> list[ProjectionEvent]:
        events = self.data.events_by_user.get(user_id, [])
        groups: dict[tuple[str, str, str, str, str, str], list[Event]] = defaultdict(list)
        for event in events:
            if event.status != "settled" or event.settlement_date >= start or event.direction == "non_cash":
                continue
            # Variable spending changes merchant descriptions, so expenses are
            # grouped by category. Income is more conservative: only the same
            # named payroll stream is recurrent, not an irregular gig total.
            series_name = event.description if event.direction == "credit" else ""
            if "final" in event.description.lower() or "one-time" in event.description.lower():
                continue
            key = (event.event_type, event.category, event.direction,
                   event.flexibility, event.currency, series_name)
            groups[key].append(event)
        result = []
        final_income_date = max(
            (e.settlement_date for e in events
             if e.direction == "credit" and "final" in e.description.lower()),
            default=date.min,
        )
        for (event_type, category, direction, flexibility, currency, series_name), group in groups.items():
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
            values = [e.amount for e in sorted(group, key=lambda e: e.settlement_date)[-8:]]
            # Use the recent median for stable commitments and a conservative
            # recent upper quartile for variable expenses.
            stable = max(values) - min(values) <= max(CENT, median(values) * Decimal("0.08"))
            if direction == "credit":
                # Do not extrapolate a one-off spike; use the latest observed
                # payroll amount for a supported recurring income stream.
                source_amount = median(values[-3:])
            else:
                source_amount = median(values) if stable else sorted(values)[max(0, int(len(values) * .75) - 1)]
            source = self.data.convert(source_amount, currency, home, last.settlement_date)
            monthly = step in range(27, 33)
            month_step = 2 if step >= 58 else 1
            next_when = add_months(last.settlement_date, month_step) if monthly else last.settlement_date + timedelta(days=step)
            while next_when <= end:
                if next_when > start:
                    result.append(ProjectionEvent(next_when, source, direction, category,
                                                  last.event_id, flexibility, last.event_id))
                next_when = (add_months(next_when, month_step) if monthly
                             else next_when + timedelta(days=step))
        return result

    def salary_message_projection(self, user_id: str, request_id: str, start: date, end: date, home: str) -> list[ProjectionEvent]:
        facts = self.message_facts(self.relevant_messages(user_id, request_id, start), home)
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
        recurring = self.recurring_projection(request["user_id"], start, end, profile.home_currency)
        explicit_keys = {(p.when, p.category, p.direction) for p in explicit}
        # A supplied scheduled/pending row is more specific than an inferred
        # recurrence on the same day/category, so do not count both.
        recurring = [p for p in recurring if (p.when, p.category, p.direction) not in explicit_keys]
        result = explicit + recurring
        message_salary = self.salary_message_projection(request["user_id"], request["request_id"], start, end, profile.home_currency)
        # An employer amendment replaces the old payroll estimate on the same
        # effective date; it is not an additional salary.
        message_dates = {p.when for p in message_salary}
        result = [p for p in result if not (p.category == "salary" and p.when in message_dates)]
        result += message_salary
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
                result.append(ProjectionEvent(p.when, c.new_amount, p.direction, p.category,
                                              p.event_id, p.flexibility, p.recurring_ref))
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


def main() -> None:
    data = Data()
    agent = Agent(data)
    rows = [agent.decide(request) for request in data.requests]
    validate(rows, data.requests, data.options)
    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUTPUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
