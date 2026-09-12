import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from evidence_extraction import EvidenceFact
from financial_analysis import (
    ANALYSIS_CADENCE_POLICY,
    ANALYSIS_SCHEMA_VERSION,
    AnalysisCache,
    AnalysisExtractor,
    AnalysisProviderResponse,
    AnalysisValidationError,
    analysis_artifact_is_current,
    build_financial_analysis,
    build_prompt,
    cadence,
    cadence_description,
    validate_proposals,
)
from main import Data, Event, load_evidence_facts, load_financial_analyses

ROOT = Path(__file__).parents[1]


class FakeProvider:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def analyze(self, prompt, schema, schema_name):
        self.calls += 1
        self.last_prompt = prompt
        return AnalysisProviderResponse(self.payload, "fake-analysis", 11, 7, 0, Decimal("0.01"), None, "provider")


def event(event_id, user_id, when, description, category="groceries", event_type="expense",
          direction="debit", amount="10", status="settled", linked=""):
    return Event(event_id, user_id, event_type, description, category, direction,
                 Decimal(amount), "USD", when, when, status, linked, "fixed", None)


class FinancialAnalysisTests(unittest.TestCase):
    def test_representative_profiles_keep_snapshot_and_scope(self):
        data = Data()
        requests = {
            "request_01": ("user_01", date(2024, 3, 3)),
            "request_02": ("user_02", date(2025, 8, 5)),
            "request_05": ("user_05", date(2025, 11, 6)),
            "request_20": ("user_20", date(2026, 2, 7)),
        }
        for request_id, (user_id, as_of) in requests.items():
            analysis = build_financial_analysis(data, user_id, as_of, request_id)
            self.assertEqual(analysis["scope"]["request_id"], request_id)
            self.assertEqual(
                Decimal(analysis["supplied_preferences_and_constraints"]["available_balance_snapshot"]),
                data.profiles[user_id].balance.quantize(Decimal("0.01")),
            )
            self.assertTrue(analysis["observed_historical_facts"]["historical_transactions_do_not_replay_against_snapshot"])
            self.assertIn("source_event_ids", analysis["historical_coverage"])
            self.assertIn("forecast_inputs", analysis)
            source_ids = [source_id for pattern in analysis["inferred_patterns"] for source_id in pattern["source_event_ids"]]
            self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_ended_employment_is_a_supported_change_not_future_income(self):
        data = Data()
        data.evidence_facts = load_evidence_facts(ROOT / "evaluation/message_extraction_results.json", data.messages)
        analysis = build_financial_analysis(data, "user_12", date(2026, 4, 5), "request_12")
        ended = [change for change in analysis["supported_changes"] if change["source_id"] == "message_09"]
        self.assertEqual(ended[0]["status"], "ended")
        self.assertFalse(any(row["event_id"] == "message_09" for row in analysis["known_future_commitments"]["confirmed_future_income"]))

    def test_request_scoped_evidence_does_not_leak(self):
        data = Data()
        payload = {
            "source_id": "message_14", "source_kind": "message", "supplied_user_id": "user_20",
            "supplied_request_id": "request_20", "supplied_event_id": "event_1785",
            "transaction_type": "refund", "update_status": "delayed", "action": "delay",
            "amount": None, "currency": None, "dates": [], "recurrence_scope": "once",
            "supporting_text": "The refund was initiated but has not reached the account yet.",
            "missing_fields": ["amount"], "ambiguities": ["settlement unknown"], "conflicts": [],
        }
        data.evidence_facts = {"message_14": EvidenceFact.from_mapping(payload)}
        included = build_financial_analysis(data, "user_20", date(2026, 2, 7), "request_20")
        excluded = build_financial_analysis(data, "user_20", date(2026, 2, 7), "request_other")
        self.assertEqual([item["source_id"] for item in included["source_evidence"]], ["message_14"])
        self.assertEqual(excluded["source_evidence"], [])

    def test_statistics_are_sparse_not_zero_filled(self):
        events = [
            event("e1", "user_test", date(2025, 1, 1), "Grocer A"),
            event("e2", "user_test", date(2025, 3, 1), "Grocer B"),
        ]
        data = SimpleNamespace(
            profiles={"user_test": SimpleNamespace(home_currency="USD", balance=Decimal("100"), minimum=Decimal("10"), priorities=set(), protected=set(), reduce_categories=set(), stop_categories=set(), payment_methods=set(), max_installment_months=None)},
            events_by_user={"user_test": events}, messages_by_user={"user_test": []}, evidence_facts={},
            convert=lambda amount, _src, _dst, _when: amount,
        )
        analysis = build_financial_analysis(data, "user_test", date(2025, 4, 1), "request_test")
        category = next(item for item in analysis["observed_historical_facts"]["category_summary"] if item["category"] == "groceries")
        self.assertEqual(category["stats"]["observed_month_count"], 2)
        self.assertTrue(category["stats"]["missing_buckets_are_not_zero"])
        self.assertEqual(set(category["stats"]["monthly_totals_observed"]), {"2025-01", "2025-03"})

    def test_proposal_validation_rejects_unknown_cross_user_and_duplicate_ids(self):
        events = {
            "event_1": event("event_1", "user_a", date(2025, 1, 1), "Plan", "streaming", "subscription"),
            "event_2": event("event_2", "user_a", date(2025, 2, 1), "Plan", "streaming", "subscription"),
            "event_3": event("event_3", "user_b", date(2025, 3, 1), "Other", "streaming", "subscription"),
        }
        valid = {
            "pattern_type": "recurring_commitment", "category": "streaming", "label": "Plan",
            "source_event_ids": ["event_1", "event_2"], "grouping_rationale": "same description and cadence",
            "supporting_observations": [
                {"source_event_id": "event_1", "observation": "January plan"},
                {"source_event_id": "event_2", "observation": "February plan"},
            ], "uncertainty": "low", "alternative_interpretations": [],
        }
        validation = validate_proposals({"patterns": [valid, dict(valid, source_event_ids=["event_1", "event_3"]), dict(valid, source_event_ids=["event_unknown", "event_2"]) ]}, events, "user_a")
        self.assertEqual(len(validation.accepted), 1)
        self.assertEqual(len(validation.rejected), 2)

    def test_stale_analysis_artifact_is_not_current(self):
        stale = {"schema_version": "financial-analysis-v1", "cadence_policy": "pre-21-day"}
        current = {"schema_version": ANALYSIS_SCHEMA_VERSION, "cadence_policy": ANALYSIS_CADENCE_POLICY}
        self.assertFalse(analysis_artifact_is_current(stale))
        self.assertTrue(analysis_artifact_is_current(current))

    def test_load_financial_analyses_skips_stale_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "analyses.json"
            path.write_text(json.dumps({
                "schema_version": "financial-analysis-v1",
                "records": [{
                    "analysis": {
                        "schema_version": "financial-analysis-v1",
                        "scope": {"user_id": "user_01", "request_id": "request_01", "as_of_date": "2024-03-03"},
                    }
                }],
            }), encoding="utf-8")
            self.assertEqual(load_financial_analyses(path), {})

    def test_cadence_accepts_supported_21_day_history(self):
        dates = [date(2025, 1, 2), date(2025, 1, 23), date(2025, 2, 13), date(2025, 3, 6)]
        self.assertEqual(cadence(dates), 21)
        self.assertEqual(cadence_description(21), "three_week_fixed_day")
        self.assertIsNone(cadence(dates[:2]))

    def test_recurring_salary_credit_is_a_valid_pattern(self):
        events = {
            "salary_1": event("salary_1", "user_a", date(2025, 1, 15), "Employer salary", "salary", "income", "credit"),
            "salary_2": event("salary_2", "user_a", date(2025, 2, 15), "Employer salary", "salary", "income", "credit"),
        }
        proposal = {
            "pattern_type": "recurring_commitment", "category": "salary", "label": "Employer salary",
            "source_event_ids": ["salary_1", "salary_2"], "grouping_rationale": "same monthly employer credit",
            "supporting_observations": [
                {"source_event_id": "salary_1", "observation": "January salary"},
                {"source_event_id": "salary_2", "observation": "February salary"},
            ], "uncertainty": "future employment is not guaranteed", "alternative_interpretations": [],
        }
        validation = validate_proposals({"patterns": [proposal]}, events, "user_a")
        self.assertEqual(len(validation.accepted), 1)
        self.assertEqual(validation.rejected, ())

    def test_confirmed_future_platform_credit_is_eligible_without_keyword_override(self):
        events = [
            event("event_991", "user_99", date(2025, 1, 1), "Driver platform payout", "platform_income", "income", "credit"),
            event("event_992", "user_99", date(2025, 2, 1), "Driver platform payout", "platform_income", "income", "credit"),
            event("event_993", "user_99", date(2025, 3, 1), "Driver platform payout", "platform_income", "income", "credit"),
        ]
        message = {"message_id": "message_998", "user_id": "user_99", "request_id": "request_99", "sent_at": "2025-03-10", "message_text": "The platform payout is confirmed for April 1."}
        fact = EvidenceFact.from_mapping({
            "source_id": "message_998", "source_kind": "message", "supplied_user_id": "user_99", "supplied_request_id": "request_99",
            "supplied_event_id": "event_993", "transaction_type": "payout", "update_status": "confirmed", "action": "confirmation",
            "amount": "10", "currency": "USD", "dates": [{"date": "2025-04-01", "meaning": "payment_date"}],
            "recurrence_scope": "future_occurrences", "supporting_text": "The platform payout is confirmed for April 1.",
            "missing_fields": [], "ambiguities": [], "conflicts": [],
        })
        data = SimpleNamespace(
            profiles={"user_99": SimpleNamespace(home_currency="USD", balance=Decimal("100"), minimum=Decimal("10"), priorities=set(), protected=set(), reduce_categories=set(), stop_categories=set(), payment_methods=set(), max_installment_months=None)},
            events_by_user={"user_99": events}, messages_by_user={"user_99": [message]}, evidence_facts={"message_998": fact},
            convert=lambda amount, _src, _dst, _when: amount,
        )
        analysis = build_financial_analysis(data, "user_99", date(2025, 3, 15), "request_99")
        eligible = next(item for item in analysis["forecast_inputs"] if item["category"] == "platform_income")
        self.assertEqual(eligible["income_eligibility"], "confirmed_future_credit")
        self.assertTrue(eligible["forecastable"])

    def test_duplicate_lifecycle_rows_do_not_create_historical_credit(self):
        data = Data()
        analysis = build_financial_analysis(data, "user_20", date(2026, 2, 7), "request_20")
        historical_ids = set(analysis["historical_coverage"]["source_event_ids"])
        pending_ids = {row["event_id"] for row in analysis["known_future_commitments"]["pending_or_scheduled_obligations"]}
        self.assertIn("event_1784", historical_ids)
        self.assertNotIn("event_1785", historical_ids)
        self.assertIn("event_1786", pending_ids)
        self.assertNotIn("event_1785", pending_ids)
        self.assertNotIn("event_1785", analysis["known_future_commitments"]["confirmed_future_income"])

    def test_analysis_cache_reuses_scope_and_model_input(self):
        payload = {"patterns": []}
        provider = FakeProvider(payload)
        with tempfile.TemporaryDirectory() as directory:
            extractor = AnalysisExtractor(provider, AnalysisCache(Path(directory)))
            scope = {"user_id": "user_a", "request_id": "request_a", "as_of_date": date(2025, 1, 1), "candidate_event_rows": []}
            first = extractor.extract(scope, {}, "user_a", "fake-analysis")
            second = extractor.extract(scope, {}, "user_a", "fake-analysis")
            self.assertFalse(first.cache_hit)
            self.assertTrue(second.cache_hit)
            self.assertEqual(provider.calls, 1)

    def test_prompt_excludes_sample_answers_and_forbids_affordability(self):
        prompt = build_prompt({"user_id": "user_a", "request_id": "request_a", "as_of_date": date(2025, 1, 1), "candidate_event_rows": []})
        self.assertIn("Do not invent transactions", prompt)
        self.assertIn("Do not authorize stopping", prompt)
        self.assertIn("reducing any category", prompt)
        self.assertNotIn("amount_safe_to_pay", prompt)
        self.assertNotIn("affordability_status", prompt)


if __name__ == "__main__":
    unittest.main()
