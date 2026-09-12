import csv
import sys
import unittest
from datetime import date, timedelta
from evidence_extraction import EvidenceFact
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))
from main import Agent, Data, Event, Profile, ProjectionEvent, OUTPUT_COLUMNS, dec, ddate, main


class FinancialAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = Data()
        cls.agent = Agent(cls.data)
        with (Path(__file__).parents[1] / "dataset/sample_requests.csv").open(newline="", encoding="utf-8") as fh:
            cls.samples = list(csv.DictReader(fh))

    def sample(self, request_id):
        return next(row for row in self.samples if row["request_id"] == request_id)

    def test_image_only_amounts_are_not_zero(self):
        by_id = {e.event_id: e for e in self.data.events}
        self.assertEqual(by_id["event_253"].amount, Decimal("4365000"))
        self.assertGreater(by_id["event_6033"].amount, Decimal("0"))
        self.assertEqual(by_id["event_10521"].amount, Decimal("393.22"))

    def test_conversion_uses_fixed_rate_and_inverse(self):
        (when, source, target), rate = next(
            ((when, source, target), rate) for (when, source, target), rate in self.data.rates.items()
            if source != target
        )
        value = self.data.convert(Decimal("10"), source, target, when)
        self.assertEqual(value, Decimal("10") * rate)
        self.assertAlmostEqual(float(self.data.convert(value, target, source, when)), 10.0, places=8)

    def test_pending_debit_is_reserved_and_pending_credit_is_not(self):
        request = self.sample("request_02")
        projections = self.agent.projections(request)
        pending = [p for p in projections if p.event_id == "event_185"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].direction, "debit")
        self.assertEqual(pending[0].amount, Decimal("1651100"))

    def test_salary_amendment_persists_to_later_occurrences(self):
        request = self.sample("request_02")
        projections = self.agent.projections(request)
        salaries = {
            p.when: p.amount
            for p in projections
            if p.category == "salary" and p.direction == "credit"
        }
        # message_01 says the recurring payroll became IDR 42,750,000 effective
        # 2025-08-15; the later monthly occurrences must use the same amendment.
        expected_dates = {date(2025, 8, 15), date(2025, 9, 15), date(2025, 10, 15)}
        self.assertEqual(set(salaries), expected_dates)
        self.assertEqual(
            {when: salaries[when] for when in expected_dates},
            {when: Decimal("42750000") for when in expected_dates},
        )

    def test_installment_schedule_matches_supplied_option(self):
        request = self.sample("request_02")
        row = self.agent.decide(request)
        option = next(o for o in self.data.options if o.option_id == "payment_option_05")
        expected = "|".join(f"{when.isoformat()}:{str(amount)}" for when, amount in option.dates_and_amounts())
        self.assertEqual(row["payment_plan"], expected)
        self.assertEqual(row["recommended_payment_method"], "installments")

    def test_partial_payment_shape_is_two_payments(self):
        request = self.sample("request_19")
        row = self.agent.decide(request)
        # Depending on conservative recurrence policy this may select a cheaper
        # supplied option, but whenever partial payment is selected the contract
        # must be exact.
        if row["recommended_payment_method"] == "partial_payment":
            parts = row["payment_plan"].split("|")
            self.assertEqual(len(parts), 2)
            first = dec(parts[0].split(":", 1)[1])
            second = dec(parts[1].split(":", 1)[1])
            self.assertEqual(first + second, dec(request["requested_amount"]))
            self.assertLess(ddate(parts[0].split(":", 1)[0]), ddate(parts[1].split(":", 1)[0]))

    def test_replay_never_accepts_below_floor(self):
        request = self.sample("request_03")
        profile = self.data.profiles[request["user_id"]]
        start = ddate(request["request_date"])
        projections = self.agent.projections(request)
        ok, _, balances = self.agent.replay(
            profile.balance, profile.minimum, start, start + timedelta(days=90),
            projections, [(start, dec(request["requested_amount"]))],
        )
        self.assertFalse(ok)
        self.assertTrue(any(value < profile.minimum for value in balances.values()))

    def synthetic_event(self, event_id, when, description, category="streaming", event_type="subscription", direction="debit",
                        status="settled", linked_event_id="", amount=Decimal("10")):
        return Event(
            event_id, "user_test", event_type, description, category, direction,
            amount, "USD", when, when, status, linked_event_id, "fixed", None,
        )

    def synthetic_agent(self, events):
        profile = Profile("user_test", "USD", Decimal("1000"), Decimal("100"), set(), set(), set(), set(), {"full_payment"}, None)
        data = SimpleNamespace(
            events_by_user={"user_test": events},
            profiles={"user_test": profile},
            messages_by_user={"user_test": []},
            evidence_facts={},
            financial_analyses={},
            convert=lambda amount, _source, _target, _when: amount,
        )
        return Agent(data)

    def test_two_subscriptions_in_one_category_remain_separate(self):
        events = []
        for index, description in enumerate(("Video streaming plan", "Family streaming plan")):
            for offset, when in enumerate((date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1))):
                events.append(self.synthetic_event(f"sub_{index}_{offset}", when, description))
        projection = self.synthetic_agent(events).recurring_projection("user_test", date(2025, 3, 15), date(2025, 5, 31), "USD")
        self.assertEqual(len(projection), 4)
        self.assertEqual({p.recurring_ref for p in projection}, {"sub_0_2", "sub_1_2"})
        self.assertEqual({p.source_event_ids for p in projection}, {
            ("sub_0_0", "sub_0_1", "sub_0_2"),
            ("sub_1_0", "sub_1_1", "sub_1_2"),
        })

    def test_grocery_merchants_remain_in_variable_category_stream(self):
        events = [
            self.synthetic_event("g1", date(2025, 1, 1), "Local market purchase", "groceries", "expense"),
            self.synthetic_event("g2", date(2025, 1, 8), "Supermarket basket", "groceries", "expense"),
            self.synthetic_event("g3", date(2025, 1, 15), "Fresh food shop", "groceries", "expense"),
        ]
        projection = self.synthetic_agent(events).recurring_projection("user_test", date(2025, 1, 16), date(2025, 1, 23), "USD")
        self.assertEqual(len(projection), 1)
        self.assertEqual(projection[0].category, "groceries")
        self.assertEqual(projection[0].source_event_ids, ("g1", "g2", "g3"))

    def test_explicit_one_time_expense_is_not_inferred(self):
        events = [
            self.synthetic_event(f"once_{index}", when, "Explicit one-time purchase", "shopping", "expense")
            for index, when in enumerate((date(2025, 1, 1), date(2025, 1, 8), date(2025, 1, 15)))
        ]
        self.assertEqual(self.synthetic_agent(events).recurring_projection("user_test", date(2025, 1, 16), date(2025, 2, 1), "USD"), [])

    def salary_history(self, prefix, description, amount=Decimal("100"), day=1):
        return [
            self.synthetic_event(
                f"{prefix}_{index}", date(2025, month, day), description,
                category="salary", event_type="income", direction="credit", amount=amount,
            )
            for index, month in enumerate((1, 2, 3), start=1)
        ]

    def salary_request(self, request_date="2025-03-15"):
        return {
            "user_id": "user_test", "request_id": "request_test", "request_date": request_date,
            "requested_amount": "1", "desired_completion_date": "2025-06-30",
            "allows_partial_payment": "false",
        }

    def salary_credits(self, projections):
        return sorted(
            [p for p in projections if p.direction == "credit" and p.category == "salary"],
            key=lambda p: (p.when, p.event_id),
        )

    def test_placeholder_and_named_salary_count_once(self):
        events = self.salary_history("pay", "Primary household salary") + [
            self.synthetic_event(
                "next", date(2025, 4, 1), "Next confirmed salary", "salary", "income", "credit",
                status="scheduled", amount=Decimal("100"),
            ),
        ]
        credits = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        april = [p for p in credits if p.when == date(2025, 4, 1)]
        self.assertEqual(len(april), 1)
        self.assertEqual(april[0].event_id, "next")
        self.assertEqual(april[0].amount, Decimal("100"))
        self.assertIn("pay_3", april[0].source_event_ids)
        self.assertEqual(april[0].replacement_reason, "explicit_placeholder_replaces_unique_inferred_payday")
        self.assertTrue(any(p.when == date(2025, 5, 1) and p.amount == Decimal("100") for p in credits))
        again = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        self.assertEqual([(p.when, p.event_id, p.amount, p.source_event_ids) for p in credits],
                         [(p.when, p.event_id, p.amount, p.source_event_ids) for p in again])

    def test_two_named_salaries_same_date_are_both_kept(self):
        events = (
            self.salary_history("a", "Acme employer payroll")
            + self.salary_history("b", "Beta employer payroll")
        )
        credits = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        april = [p for p in credits if p.when == date(2025, 4, 1)]
        self.assertEqual(len(april), 2)
        self.assertEqual({p.recurring_ref for p in april}, {"a_3", "b_3"})

    def test_delayed_salary_removes_superseded_inferred_payday(self):
        events = self.salary_history("pay", "Payroll credit") + [
            self.synthetic_event(
                "delayed", date(2025, 4, 8), "Delayed payroll credit", "salary", "income", "credit",
                status="scheduled", linked_event_id="pay_3", amount=Decimal("100"),
            ),
        ]
        credits = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        self.assertFalse(any(p.when == date(2025, 4, 1) for p in credits))
        self.assertTrue(any(p.when == date(2025, 5, 1) for p in credits))
        delayed = next(p for p in credits if p.event_id == "delayed")
        self.assertEqual(delayed.replacement_reason, "explicit_delayed_salary_replaces_inferred_payday")
        self.assertIn("pay_3", delayed.source_event_ids)
        self.assertFalse(any(p.when == date(2025, 4, 1) for p in credits))

    def test_one_time_salary_amount_does_not_change_later_months(self):
        events = self.salary_history("pay", "Payroll credit", amount=Decimal("100")) + [
            self.synthetic_event(
                "next", date(2025, 4, 1), "Next confirmed salary", "salary", "income", "credit",
                status="scheduled", amount=Decimal("40"),
            ),
        ]
        credits = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        by_date = {p.when: p for p in credits}
        self.assertEqual(by_date[date(2025, 4, 1)].amount, Decimal("40"))
        self.assertEqual(by_date[date(2025, 4, 1)].event_id, "next")
        self.assertEqual(by_date[date(2025, 5, 1)].amount, Decimal("100"))
        self.assertEqual(by_date[date(2025, 5, 1)].event_id, "pay_3")

    def test_permanent_salary_amendment_still_applies_to_later_occurrences(self):
        request = self.sample("request_02")
        projections = self.agent.projections(request)
        salaries = {
            p.when: p.amount
            for p in projections
            if p.category == "salary" and p.direction == "credit"
        }
        expected_dates = {date(2025, 8, 15), date(2025, 9, 15), date(2025, 10, 15)}
        self.assertEqual(set(salaries), expected_dates)
        self.assertEqual({when: salaries[when] for when in expected_dates},
                         {when: Decimal("42750000") for when in expected_dates})

    def test_ambiguous_generic_salary_does_not_invent_a_third_credit(self):
        events = (
            self.salary_history("a", "Acme employer payroll", amount=Decimal("100"))
            + self.salary_history("b", "Beta employer payroll", amount=Decimal("100"))
            + [
                self.synthetic_event(
                    "next", date(2025, 4, 1), "Next confirmed salary", "salary", "income", "credit",
                    status="scheduled", amount=Decimal("100"),
                ),
            ]
        )
        credits = self.salary_credits(self.synthetic_agent(events).projections(self.salary_request()))
        april = [p for p in credits if p.when == date(2025, 4, 1)]
        self.assertEqual(len(april), 2)
        self.assertEqual({p.recurring_ref for p in april}, {"a_3", "b_3"})
        self.assertFalse(any(p.event_id == "next" for p in april))

    def test_unrelated_subscription_is_unchanged_by_salary_reconcile(self):
        events = self.salary_history("pay", "Payroll credit") + [
            self.synthetic_event("s1", date(2025, 1, 1), "Video streaming plan"),
            self.synthetic_event("s2", date(2025, 2, 1), "Video streaming plan"),
            self.synthetic_event("s3", date(2025, 3, 1), "Video streaming plan"),
            self.synthetic_event(
                "next", date(2025, 4, 1), "Next confirmed salary", "salary", "income", "credit",
                status="scheduled", amount=Decimal("100"),
            ),
        ]
        projections = self.synthetic_agent(events).projections(self.salary_request())
        subscriptions = [p for p in projections if p.category == "streaming"]
        self.assertTrue(subscriptions)
        self.assertEqual({p.recurring_ref for p in subscriptions}, {"s3"})
        self.assertEqual(len([p for p in self.salary_credits(projections) if p.when == date(2025, 4, 1)]), 1)

    def test_request_13_next_confirmed_salary_is_one_payday(self):
        request = self.sample("request_13")
        credits = [p for p in self.agent.projections(request)
                   if p.direction == "credit" and p.when == date(2024, 3, 15)]
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0].event_id, "event_1161")
        self.assertEqual(credits[0].amount, Decimal("1343.54"))
        self.assertIn("event_1087", credits[0].source_event_ids)
        self.assertTrue(credits[0].replacement_reason)

    def test_reconcile_is_idempotent_on_explicit_inferred_pair(self):
        events = self.salary_history("pay", "Primary household salary") + [
            self.synthetic_event(
                "next", date(2025, 4, 1), "Next confirmed salary", "salary", "income", "credit",
                status="scheduled", amount=Decimal("100"),
            ),
        ]
        agent = self.synthetic_agent(events)
        request = self.salary_request()
        start = date(2025, 3, 15)
        end = date(2025, 6, 13)
        event_by_id = {event.event_id: event for event in events}
        explicit = agent.explicit_projection("user_test", start, end, "USD")
        recurring = agent.recurring_projection("user_test", start, end, "USD")
        first_e, first_r = agent.reconcile_explicit_inferred_credits(explicit, recurring, event_by_id)
        second_e, second_r = agent.reconcile_explicit_inferred_credits(first_e, first_r, event_by_id)
        self.assertEqual(first_e, second_e)
        self.assertEqual(first_r, second_r)

    def salary_fact(self, source_id, amount, when, status="resumed", scope="future_occurrences", meaning="effective_date", txn="salary"):
        return EvidenceFact.from_mapping({
            "source_id": source_id, "source_kind": "message", "supplied_user_id": None,
            "supplied_request_id": None, "supplied_event_id": None, "transaction_type": txn,
            "update_status": status,
            "action": {"resumed": "other", "amended": "amendment", "confirmed": "confirmation", "ended": "cancellation"}[status],
            "amount": amount, "currency": "USD" if amount is not None else None,
            "dates": [{"date": when, "meaning": meaning}] if when else [],
            "recurrence_scope": scope, "supporting_text": f"Salary evidence {status} {amount} {when}",
            "missing_fields": [], "ambiguities": [], "conflicts": [],
        })

    def evidence_agent(self, events, messages, facts, request_date="2025-08-04"):
        profile = Profile("user_test", "USD", Decimal("1000"), Decimal("100"), set(), set(), set(), set(), {"full_payment"}, None)
        store = {}
        for fact in facts:
            store.setdefault(fact.source_id, [])
            store[fact.source_id].append(fact)
        store = {key: tuple(value) for key, value in store.items()}
        data = SimpleNamespace(
            events_by_user={"user_test": events}, profiles={"user_test": profile},
            messages_by_user={"user_test": messages}, evidence_facts=store,
            financial_analyses={}, convert=lambda amount, _source, _target, _when: amount,
        )
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": request_date,
            "requested_amount": "1", "desired_completion_date": "2025-12-31",
            "allows_partial_payment": "false",
        }
        return Agent(data), request

    def test_resumed_salary_continues_without_three_settled_rows(self):
        events = [
            self.synthetic_event("s1", date(2025, 3, 15), "Payroll before leave", "salary", "income", "credit", amount=Decimal("2717")),
            self.synthetic_event("s2", date(2025, 4, 15), "Payroll before leave", "salary", "income", "credit", amount=Decimal("2717")),
            self.synthetic_event("s3", date(2025, 7, 15), "Payroll after returning from leave", "salary", "income", "credit", amount=Decimal("2717")),
        ]
        messages = [{"message_id": "message_10", "user_id": "user_test", "request_id": "", "sent_at": "2025-07-27", "message_text": "Regular salary of EUR 2717 resumes on 2025-08-15."}]
        fact = self.salary_fact("message_10", "2717", "2025-08-15", "resumed", "future_occurrences", "effective_date")
        agent, request = self.evidence_agent(events, messages, [fact], "2025-08-04")
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        self.assertEqual([p.when for p in credits], [date(2025, 8, 15), date(2025, 9, 15), date(2025, 10, 15)])
        self.assertTrue(all(p.amount == Decimal("2717") for p in credits))
        self.assertEqual({p.replacement_reason for p in credits}, {"salary_evidence_resumed_stream"})

    def test_one_confirmed_salary_does_not_recur(self):
        events = [self.synthetic_event("s1", date(2025, 12, 15), "First-job payroll", "salary", "income", "credit", amount=Decimal("1661"))]
        messages = [{"message_id": "message_11", "user_id": "user_test", "request_id": "request_test", "sent_at": "2026-01-03", "message_text": "Your first salary will be USD 1661 on 2026-01-15."}]
        fact = self.salary_fact("message_11", "1661", "2026-01-15", "confirmed", "once", "payment_date")
        agent, request = self.evidence_agent(events, messages, [fact], "2026-01-06")
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        self.assertEqual([p.when for p in credits], [date(2026, 1, 15)])
        self.assertEqual(credits[0].replacement_reason, "salary_evidence_once")

    def test_two_employers_only_matching_stream_is_amended(self):
        events = []
        for prefix, description, amount in (("810", "Acme employer payroll", Decimal("100")), ("820", "Beta employer payroll", Decimal("80"))):
            for index, month in enumerate((1, 2, 3), start=1):
                events.append(self.synthetic_event(
                    f"event_{prefix}{index}", date(2025, month, 1), description,
                    category="salary", event_type="income", direction="credit", amount=amount,
                ))
        messages = [{"message_id": "message_80", "user_id": "user_test", "request_id": "request_test", "sent_at": "2025-03-10", "message_text": "Acme salary is USD 120 from 2025-04-01."}]
        mapping = self.salary_fact("message_80", "120", "2025-04-01", "amended", "future_occurrences", "effective_date").to_mapping()
        mapping["supplied_event_id"] = "event_8103"
        bound = EvidenceFact.from_mapping(mapping)
        agent, request = self.evidence_agent(events, messages, [bound], "2025-03-15")
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        acme = [p for p in credits if p.recurring_ref == "event_8103" or "event_8103" in p.source_event_ids]
        beta = [p for p in credits if p.recurring_ref == "event_8203" or "event_8203" in p.source_event_ids]
        self.assertTrue(acme and all(p.amount == Decimal("120") for p in acme if p.when >= date(2025, 4, 1)))
        self.assertTrue(beta and all(p.amount == Decimal("80") for p in beta))

    def test_salary_end_then_resume_skips_gap(self):
        events = self.salary_history("pay", "Payroll credit", Decimal("50"), day=15)
        messages = [
            {"message_id": "message_70", "user_id": "user_test", "request_id": "", "sent_at": "2025-03-20", "message_text": "Employment ended 2025-03-20."},
            {"message_id": "message_71", "user_id": "user_test", "request_id": "", "sent_at": "2025-05-01", "message_text": "Salary of USD 50 resumes on 2025-05-15."},
        ]
        ended = self.salary_fact("message_70", None, "2025-03-20", "ended", "unknown", "effective_date")
        resumed = self.salary_fact("message_71", "50", "2025-05-15", "resumed", "future_occurrences", "effective_date")
        agent, request = self.evidence_agent(events, messages, [ended, resumed], "2025-05-10")
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        self.assertFalse(any(date(2025, 4, 1) <= p.when < date(2025, 5, 15) for p in credits))
        self.assertTrue(any(p.when == date(2025, 5, 15) for p in credits))

    def test_multiple_facts_in_one_message_keep_unresolved_expense(self):
        events = [
            self.synthetic_event("s1", date(2025, 3, 15), "Payroll credit", "salary", "income", "credit", amount=Decimal("2717")),
            self.synthetic_event("s2", date(2025, 4, 15), "Payroll credit", "salary", "income", "credit", amount=Decimal("2717")),
            self.synthetic_event("s3", date(2025, 7, 15), "Payroll credit", "salary", "income", "credit", amount=Decimal("2717")),
        ]
        messages = [{"message_id": "message_10", "user_id": "user_test", "request_id": "", "sent_at": "2025-07-27", "message_text": "Regular salary of EUR 2717 resumes on 2025-08-15. A new recurring childcare payment begins in the same month."}]
        salary = self.salary_fact("message_10", "2717", "2025-08-15", "resumed", "future_occurrences", "effective_date")
        childcare = EvidenceFact.from_mapping({
            "source_id": "message_10", "source_kind": "message", "supplied_user_id": None,
            "supplied_request_id": None, "supplied_event_id": None, "transaction_type": "expense",
            "update_status": "confirmed", "action": "confirmation", "amount": None, "currency": None,
            "dates": [], "recurrence_scope": "future_occurrences",
            "supporting_text": "A new recurring childcare payment begins in the same month.",
            "missing_fields": ["amount", "currency", "dates"], "ambiguities": ["childcare amount and first date are unavailable"], "conflicts": [],
        })
        agent, request = self.evidence_agent(events, messages, [salary, childcare], "2025-08-04")
        projections = agent.projections(request)
        self.assertTrue(any(p.category == "salary" and p.when == date(2025, 8, 15) for p in projections))
        self.assertFalse(any("child" in (p.category + p.event_id) for p in projections))
        unresolved = agent.unresolved_evidence(messages)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].transaction_type, "expense")
        self.assertIsNone(unresolved[0].amount)

    def test_future_salary_message_is_not_visible(self):
        events = self.salary_history("pay", "Payroll credit", Decimal("50"), day=15)
        messages = [{"message_id": "message_90", "user_id": "user_test", "request_id": "request_test", "sent_at": "2025-04-01", "message_text": "Salary resumes later."}]
        fact = self.salary_fact("message_90", "50", "2025-04-15", "resumed", "future_occurrences", "effective_date")
        agent, request = self.evidence_agent(events, messages, [fact], "2025-03-15")
        credits = [p for p in agent.projections(request) if p.event_id == "message_payroll"]
        self.assertEqual(credits, [])

    def test_request_scoped_salary_message_does_not_leak(self):
        events = self.salary_history("pay", "Payroll credit", Decimal("50"), day=15)
        messages = [{"message_id": "message_91", "user_id": "user_test", "request_id": "request_other", "sent_at": "2025-03-10", "message_text": "Salary resumes."}]
        fact = self.salary_fact("message_91", "50", "2025-04-15", "resumed", "future_occurrences", "effective_date")
        agent, request = self.evidence_agent(events, messages, [fact], "2025-03-15")
        self.assertFalse(any(p.event_id == "message_payroll" for p in agent.projections(request)))

    def test_percentage_rent_applies_to_next_regular_occurrence_not_arrears(self):
        events = [
            self.synthetic_event("event_1", date(2025, 1, 1), "Monthly rent fixed", "rent", "expense", amount=Decimal("57100")),
            self.synthetic_event("event_2", date(2025, 2, 1), "Monthly rent fixed", "rent", "expense", amount=Decimal("57100")),
            self.synthetic_event("event_3", date(2025, 3, 1), "Monthly rent fixed", "rent", "expense", amount=Decimal("57100")),
            self.synthetic_event("event_4", date(2025, 3, 16), "Outstanding rent balance", "rent", "expense",
                                 status="scheduled", amount=Decimal("100000")),
        ]
        messages = [{"message_id": "message_12", "user_id": "user_test", "request_id": "request_test",
                     "sent_at": "2025-03-01", "message_text": "The renewed lease increases monthly rent by 12%. The new amount will be used for the next rent payment."}]
        fact = EvidenceFact.from_mapping({
            "source_id": "message_12", "source_kind": "message", "supplied_user_id": None,
            "supplied_request_id": None, "supplied_event_id": None, "transaction_type": "rent",
            "update_status": "amended", "action": "amendment", "amount": None, "currency": None,
            "dates": [], "recurrence_scope": "future_occurrences",
            "supporting_text": "The renewed lease increases monthly rent by 12%. The new amount will be used for the next rent payment.",
            "missing_fields": ["amount", "currency", "dates"], "ambiguities": [], "conflicts": [],
        })
        agent, request = self.evidence_agent(events, messages, [fact], "2025-03-12")
        rents = [p for p in agent.projections(request) if p.category == "rent"]
        regular = [p for p in rents if p.when >= date(2025, 4, 1) and "outstanding" not in (p.replacement_reason or "")]
        self.assertTrue(regular)
        self.assertTrue(all(p.amount == Decimal("63952") for p in regular))
        arrears = [p for p in rents if p.event_id == "event_4"]
        self.assertEqual(arrears[0].amount, Decimal("100000"))
        again = [p for p in agent.projections(request) if p.category == "rent" and p.when >= date(2025, 4, 1) and p.event_id != "event_4"]
        self.assertEqual([p.amount for p in regular], [p.amount for p in again])

    def test_exact_21_day_variable_spending_is_forecast(self):
        events = [
            self.synthetic_event("d1", date(2025, 1, 2), "Lunch with colleagues", "dining", "expense", amount=Decimal("40")),
            self.synthetic_event("d2", date(2025, 1, 23), "Lunch with colleagues", "dining", "expense", amount=Decimal("40")),
            self.synthetic_event("d3", date(2025, 2, 13), "Lunch with colleagues", "dining", "expense", amount=Decimal("42")),
        ]
        projection = self.synthetic_agent(events).recurring_projection("user_test", date(2025, 2, 20), date(2025, 4, 10), "USD")
        dining = [p for p in projection if p.category == "dining"]
        self.assertGreaterEqual(len(dining), 2)
        gaps = [(b.when - a.when).days for a, b in zip(dining, dining[1:])]
        self.assertTrue(gaps and all(g == 21 for g in gaps))

    def test_two_isolated_transactions_are_not_recurring(self):
        events = [
            self.synthetic_event("d1", date(2025, 1, 2), "Lunch with colleagues", "dining", "expense"),
            self.synthetic_event("d2", date(2025, 1, 23), "Lunch with colleagues", "dining", "expense"),
        ]
        self.assertEqual(self.synthetic_agent(events).recurring_projection("user_test", date(2025, 1, 24), date(2025, 3, 1), "USD"), [])

    def test_sparse_helper_does_not_duplicate_recurring_salary(self):
        events = [
            self.synthetic_event("event_1055", date(2023, 10, 15), "Primary household salary", "salary", "income", "credit", amount=Decimal("1343.54")),
            self.synthetic_event("event_1063", date(2023, 11, 15), "Primary household salary", "salary", "income", "credit", amount=Decimal("1343.54")),
            self.synthetic_event("event_1071", date(2023, 12, 15), "Primary household salary", "salary", "income", "credit", amount=Decimal("1343.54")),
            self.synthetic_event("event_1079", date(2024, 1, 15), "Primary household salary", "salary", "income", "credit", amount=Decimal("1343.54")),
            self.synthetic_event("event_1087", date(2024, 2, 15), "Primary household salary", "salary", "income", "credit", amount=Decimal("1343.54")),
            self.synthetic_event("event_1161", date(2024, 3, 15), "Next confirmed salary", "salary", "income", "credit",
                                 status="scheduled", amount=Decimal("1343.54")),
        ]
        agent = self.synthetic_agent(events)
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2024-03-07",
            "requested_amount": "941.6", "desired_completion_date": "2024-05-15", "allows_partial_payment": "true",
        }
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        by_date: dict[date, list] = {}
        for projection in credits:
            by_date.setdefault(projection.when, []).append(projection)
        self.assertEqual(len(by_date[date(2024, 3, 15)]), 1)
        self.assertEqual(len(by_date[date(2024, 4, 15)]), 1)
        self.assertEqual(len(by_date[date(2024, 5, 15)]), 1)
        self.assertEqual(by_date[date(2024, 4, 15)][0].amount, Decimal("1343.54"))
        self.assertNotEqual(by_date[date(2024, 4, 15)][0].replacement_reason, "sparse_confirmed_salary_continuation")

    def test_generated_salary_does_not_drop_a_second_employer_on_same_date(self):
        events = [
            self.synthetic_event("event_1", date(2025, 1, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_2", date(2025, 2, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_3", date(2025, 3, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_4", date(2025, 1, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
            self.synthetic_event("event_5", date(2025, 2, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
            self.synthetic_event("event_6", date(2025, 3, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
        ]
        messages = [{"message_id": "message_80", "user_id": "user_test", "request_id": "request_test",
                     "sent_at": "2025-03-20", "message_text": "Acme salary is USD 120 from 2025-04-15."}]
        mapping = self.salary_fact("message_80", "120", "2025-04-15", "amended", "future_occurrences", "effective_date").to_mapping()
        mapping["supplied_event_id"] = "event_3"
        bound = EvidenceFact.from_mapping(mapping)
        agent, request = self.evidence_agent(events, messages, [bound], "2025-03-20")
        april = [p for p in agent.projections(request) if p.when == date(2025, 4, 15) and p.category == "salary"]
        self.assertEqual(len(april), 2)
        amounts = sorted(p.amount for p in april)
        self.assertEqual(amounts, [Decimal("80"), Decimal("120")])

    def test_resumed_stream_does_not_remove_other_employer_same_payday(self):
        events = [
            self.synthetic_event("event_1", date(2025, 3, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_2", date(2025, 4, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_3", date(2025, 7, 15), "Acme employer payroll", "salary", "income", "credit", amount=Decimal("100")),
            self.synthetic_event("event_4", date(2025, 5, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
            self.synthetic_event("event_5", date(2025, 6, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
            self.synthetic_event("event_6", date(2025, 7, 15), "Beta employer payroll", "salary", "income", "credit", amount=Decimal("80")),
        ]
        messages = [{"message_id": "message_10", "user_id": "user_test", "request_id": "", "sent_at": "2025-07-27",
                     "message_text": "Regular salary of USD 100 resumes on 2025-08-15."}]
        mapping = self.salary_fact("message_10", "100", "2025-08-15", "resumed", "future_occurrences", "effective_date").to_mapping()
        mapping["supplied_event_id"] = "event_3"
        fact = EvidenceFact.from_mapping(mapping)
        agent, request = self.evidence_agent(events, messages, [fact], "2025-08-04")
        august = [p for p in agent.projections(request) if p.when == date(2025, 8, 15) and p.category == "salary"]
        self.assertEqual(len(august), 2)
        self.assertEqual(sorted(p.amount for p in august), [Decimal("80"), Decimal("100")])

    def test_sparse_confirmed_salary_continues_from_next_confirmed_row(self):
        events = [
            self.synthetic_event("event_25", date(2024, 2, 15), "Prorated first salary", "salary", "income", "credit", amount=Decimal("12826")),
            self.synthetic_event("event_103", date(2024, 3, 15), "Next confirmed salary", "salary", "income", "credit",
                                 status="scheduled", amount=Decimal("23320")),
        ]
        agent = self.synthetic_agent(events)
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2024-03-03",
            "requested_amount": "1", "desired_completion_date": "2024-06-01", "allows_partial_payment": "false",
        }
        credits = [p for p in agent.projections(request) if p.direction == "credit" and p.category == "salary"]
        by_date = {p.when: p for p in credits}
        self.assertEqual(by_date[date(2024, 3, 15)].amount, Decimal("23320"))
        self.assertEqual(by_date[date(2024, 4, 15)].amount, Decimal("23320"))
        self.assertEqual(by_date[date(2024, 5, 15)].amount, Decimal("23320"))
        self.assertNotIn(date(2024, 2, 15), by_date)

    def test_one_confirmed_prize_credit_does_not_continue(self):
        events = [
            self.synthetic_event("event_1", date(2024, 2, 15), "Lottery prize", "salary", "income", "credit", amount=Decimal("5000")),
            self.synthetic_event("event_2", date(2024, 3, 15), "Next confirmed salary", "salary", "income", "credit",
                                 status="scheduled", amount=Decimal("5000")),
        ]
        agent = self.synthetic_agent(events)
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2024-03-03",
            "requested_amount": "1", "desired_completion_date": "2024-06-01", "allows_partial_payment": "false",
        }
        credits = [p for p in agent.projections(request) if p.direction == "credit"]
        self.assertEqual([p.when for p in credits], [date(2024, 3, 15)])

    def test_request_15_first_salary_message_stays_once(self):
        request = self.sample("request_15")
        data = Data()
        from main import load_evidence_facts
        from pathlib import Path
        data.evidence_facts = load_evidence_facts(Path(__file__).parents[1] / "evaluation/message_extraction_results.json", data.messages)
        credits = [p for p in Agent(data).projections(request) if p.direction == "credit" and p.category == "salary"]
        # Two historical first-job rows are not a 3-point cadence; the message is once.
        self.assertTrue(any(p.when.isoformat() == "2026-01-15" for p in credits))
        self.assertFalse(any(p.when.isoformat() in {"2026-02-15", "2026-03-15"} and p.event_id == "message_payroll" for p in credits))

    def test_explicit_event_deduplicates_same_source_series_only(self):
        events = [
            self.synthetic_event("s1", date(2025, 1, 1), "Video streaming plan"),
            self.synthetic_event("s2", date(2025, 2, 1), "Video streaming plan"),
            self.synthetic_event("s3", date(2025, 3, 1), "Video streaming plan"),
            self.synthetic_event("explicit", date(2025, 4, 1), "Video streaming plan"),
        ]
        agent = self.synthetic_agent(events)
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2025-03-15",
            "requested_amount": "1", "desired_completion_date": "2025-04-30",
            "allows_partial_payment": "false",
        }
        projections = agent.projections(request)
        april = [p for p in projections if p.when == date(2025, 4, 1)]
        self.assertEqual(len(april), 1)
        self.assertEqual(april[0].event_id, "explicit")

    def test_analysis_boundary_applies_supported_change_without_duplication_or_leakage(self):
        events = [
            self.synthetic_event(f"salary_{index}", when, "Employer salary", "salary", "income", "credit")
            for index, when in enumerate((date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)))
        ] + [
            self.synthetic_event(f"sub_{index}", when, "Video streaming plan")
            for index, when in enumerate((date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)))
        ] + [self.synthetic_event("sub_explicit", date(2025, 4, 1), "Video streaming plan")]
        profile = Profile("user_test", "USD", Decimal("1000"), Decimal("100"), set(), set(), set(), set(), {"full_payment"}, None)
        message = {"message_id": "message_999", "user_id": "user_test", "request_id": "request_test", "sent_at": "2025-03-10", "text": "Salary is 20 from April."}
        fact = EvidenceFact.from_mapping({
            "source_id": "message_999", "source_kind": "message", "supplied_user_id": None,
            "supplied_request_id": None, "supplied_event_id": None, "transaction_type": "salary",
            "update_status": "amended", "action": "amendment", "amount": "20", "currency": "USD",
            "dates": [{"date": "2025-04-01", "meaning": "effective_date"}], "recurrence_scope": "future_occurrences",
            "supporting_text": "Salary is 20 from April.", "missing_fields": [], "ambiguities": [], "conflicts": [],
        })
        data = SimpleNamespace(
            events_by_user={"user_test": events}, profiles={"user_test": profile}, messages_by_user={"user_test": [message]},
            evidence_facts={"message_999": fact}, convert=lambda amount, _source, _target, _when: amount,
            financial_analyses={("user_test", "request_test", date(2025, 3, 15)): {"forecast_inputs": [
                {"pattern_id": "salary", "pattern_type": "recurring_commitment", "category": "salary", "label": "Employer salary", "source_event_ids": ["salary_0", "salary_1", "salary_2"], "forecastable": True, "income_eligibility": "recurring_salary_supported"},
                {"pattern_id": "subscription", "pattern_type": "recurring_commitment", "category": "streaming", "label": "Video streaming plan", "source_event_ids": ["sub_0", "sub_1", "sub_2"], "forecastable": True},
            ]}},
        )
        request = {"user_id": "user_test", "request_id": "request_test", "request_date": "2025-03-15", "requested_amount": "1", "desired_completion_date": "2025-04-30", "allows_partial_payment": "false"}
        projections = Agent(data).projections(request)
        april_salary = [p for p in projections if p.when == date(2025, 4, 1) and p.category == "salary"]
        april_subscriptions = [p for p in projections if p.when == date(2025, 4, 1) and p.category == "streaming"]
        self.assertEqual(len(april_salary), 1)
        self.assertEqual(april_salary[0].amount, Decimal("20"))
        self.assertIn(april_salary[0].event_id, {"salary_2", "message_payroll"})
        self.assertEqual(len(april_subscriptions), 1)
        self.assertEqual(april_subscriptions[0].event_id, "sub_explicit")
        self.assertFalse(any(p.event_id in {"rejected", "rejected_source"} for p in projections))

    def test_validated_analysis_does_not_forecast_payout_income(self):
        events = [
            self.synthetic_event("p1", date(2025, 1, 1), "Driver platform payout", "salary", "income", "credit"),
            self.synthetic_event("p2", date(2025, 2, 1), "Driver platform payout", "salary", "income", "credit"),
            self.synthetic_event("p3", date(2025, 3, 1), "Driver platform payout", "salary", "income", "credit"),
        ]
        agent = self.synthetic_agent(events)
        agent.data.financial_analyses = {
            ("user_test", "request_test", date(2025, 3, 15)): {
                "forecast_inputs": [{
                    "pattern_id": "payout_pattern", "pattern_type": "recurring_commitment",
                    "category": "salary", "label": "Driver platform payout",
                    "source_event_ids": ["p1", "p2", "p3"], "forecastable": True,
                }]
            }
        }
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2025-03-15",
            "requested_amount": "1", "desired_completion_date": "2025-04-30", "allows_partial_payment": "false",
        }
        self.assertEqual([p for p in agent.projections(request) if p.when > date(2025, 3, 15)], [])

    def test_validated_analysis_group_reaches_projection(self):
        events = [
            self.synthetic_event("a1", date(2025, 1, 1), "Video streaming plan"),
            self.synthetic_event("a2", date(2025, 2, 1), "Video streaming plan"),
            self.synthetic_event("a3", date(2025, 3, 1), "Video streaming plan"),
        ]
        agent = self.synthetic_agent(events)
        agent.data.financial_analyses = {
            ("user_test", "request_test", date(2025, 3, 15)): {
                "forecast_inputs": [{
                    "pattern_id": "ai_pattern_1", "pattern_type": "recurring_commitment",
                    "category": "streaming", "label": "Video streaming plan",
                    "source_event_ids": ["a1", "a2", "a3"], "forecastable": True,
                }]
            }
        }
        request = {
            "user_id": "user_test", "request_id": "request_test", "request_date": "2025-03-15",
            "requested_amount": "1", "desired_completion_date": "2025-04-30", "allows_partial_payment": "false",
        }
        projections = agent.projections(request)
        self.assertEqual([p.event_id for p in projections if p.when == date(2025, 4, 1)], ["a3"])
        self.assertEqual(next(p for p in projections if p.when == date(2025, 4, 1)).source_event_ids, ("a1", "a2", "a3"))

    def test_prediction_modes_are_explicit(self):
        with self.assertRaises(ValueError):
            main("unsupported")

    def test_output_contract_enums_and_bounds(self):
        requests = self.data.requests
        rows = [self.agent.decide(r) for r in requests]
        self.assertEqual(set(rows[0]), set(OUTPUT_COLUMNS))
        self.assertEqual(len(rows), len(requests))
        for row, request in zip(rows, requests):
            value = dec(row["amount_safe_to_pay"])
            requested = dec(request["requested_amount"])
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, requested)
            self.assertIn(row["affordability_status"], {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"})
            self.assertIn(row["recommended_payment_method"], {"full_payment", "partial_payment", "installments", "wait", "not_recommended"})


if __name__ == "__main__":
    unittest.main()
