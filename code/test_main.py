import csv
import sys
import unittest
from datetime import date, timedelta
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

    def synthetic_event(self, event_id, when, description, category="streaming", event_type="subscription", direction="debit"):
        return Event(
            event_id, "user_test", event_type, description, category, direction,
            Decimal("10"), "USD", when, when, "settled", "", "fixed", None,
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
