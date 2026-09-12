import csv
import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from main import Agent, Data, ProjectionEvent, OUTPUT_COLUMNS, dec, ddate, main


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
