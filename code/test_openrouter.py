import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from package import excluded
from evidence_extraction import (
    EvidenceExtractor,
    EvidenceSource,
    EvidenceValidationError,
    HttpResponse,
    JsonExtractionCache,
    OpenRouterAuthenticationError,
    OpenRouterConfig,
    OpenRouterInvalidResponseError,
    OpenRouterTransientError,
    OpenRouterUnsupportedModelError,
    OpenRouterAdapter,
    load_env_file,
)

MODEL = "mistralai/mistral-small-24b-instruct-2501"
PAYLOAD = {
    "source_id": "message_14",
    "source_kind": "message",
    "supplied_user_id": "user_20",
    "supplied_request_id": "request_20",
    "supplied_event_id": "event_1785",
    "action": "delay",
    "amount": None,
    "currency": None,
    "dates": [],
    "recurrence_scope": "once",
    "supporting_text": "The refund has not reached the account yet.",
    "missing_fields": ["amount", "settlement_date"],
    "ambiguities": ["No settlement date is stated."],
    "conflicts": [],
}


def response(value, status=200, headers=None):
    return HttpResponse(status, headers or {}, json.dumps(value).encode())


class QueueTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, json.loads(body) if body else None, timeout))
        if not self.responses:
            raise AssertionError("unexpected HTTP call")
        return self.responses.pop(0)


class OpenRouterAdapterTests(unittest.TestCase):
    def source(self):
        return EvidenceSource(
            source_id="message_14", source_kind="message", user_id="user_20",
            request_id="request_20", event_id="event_1785",
            content="Your refund has been initiated but has not reached your account yet.",
            visibility_date=date(2026, 2, 6),
        )

    def config(self, retries=2, key="x"):
        return OpenRouterConfig(
            api_key=key, model=MODEL, base_url="https://router.test/api/v1",
            timeout_seconds=4, max_retries=retries,
        )

    def model_response(self):
        return response({
            "data": {
                "id": MODEL,
                "supported_parameters": ["response_format", "structured_outputs"],
                "pricing": {"prompt": "0.00000005", "completion": "0.00000008", "request": "0"},
            }
        })

    def completion_response(self, payload=PAYLOAD, cost=0.0000123):
        return response({
            "model": MODEL,
            "choices": [{"message": {"role": "assistant", "content": json.dumps(payload)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "cost": cost},
        })

    def test_success_structured_extraction_usage_and_request_controls(self):
        transport = QueueTransport([self.model_response(), self.completion_response()])
        outcome = EvidenceExtractor(OpenRouterAdapter(self.config(), transport=transport)).extract(
            self.source(), MODEL
        )
        self.assertEqual(outcome.fact.action, "delay")
        self.assertEqual(outcome.input_tokens, 100)
        self.assertEqual(outcome.output_tokens, 20)
        self.assertEqual(outcome.cost_source, "provider")
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.calls[0][2]["Authorization"], "Bearer x")
        body = transport.calls[1][3]
        self.assertEqual(body["model"], MODEL)
        self.assertEqual(body["provider"], {"require_parameters": True, "allow_fallbacks": False})
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertTrue(body["response_format"]["json_schema"]["strict"])

    def test_missing_key_makes_no_http_call(self):
        transport = QueueTransport([])
        with self.assertRaises(OpenRouterAuthenticationError):
            OpenRouterAdapter(self.config(key=""), transport=transport).extract(self.source(), "prompt")
        self.assertEqual(transport.calls, [])

    def test_http_401_is_authentication_error(self):
        transport = QueueTransport([response({"error": {"message": "unauthorized"}}, 401)])
        with self.assertRaises(OpenRouterAuthenticationError):
            OpenRouterAdapter(self.config(), transport=transport).extract(self.source(), "prompt")

    def test_rate_limit_retries_with_bounded_retry_after(self):
        sleeps = []
        transport = QueueTransport([
            self.model_response(),
            response({"error": {"message": "rate limited"}}, 429, {"Retry-After": "1"}),
            self.completion_response(),
        ])
        outcome = EvidenceExtractor(OpenRouterAdapter(
            self.config(), transport=transport, sleeper=sleeps.append
        )).extract(self.source(), MODEL)
        self.assertEqual(outcome.retries, 1)
        self.assertEqual(sleeps, [1.0])

    def test_transient_failure_after_retry_limit_is_explicit(self):
        transport = QueueTransport([
            response({"error": {"message": "temporary"}}, 503),
            response({"error": {"message": "temporary"}}, 503),
            response({"error": {"message": "temporary"}}, 503),
        ])
        with self.assertRaises(OpenRouterTransientError):
            OpenRouterAdapter(self.config(retries=2), transport=transport, sleeper=lambda _: None).extract(
                self.source(), MODEL
            )

    def test_unsupported_model_capability_is_rejected(self):
        transport = QueueTransport([response({"data": {"id": MODEL, "supported_parameters": []}})])
        with self.assertRaises(OpenRouterUnsupportedModelError):
            OpenRouterAdapter(self.config(), transport=transport).extract(self.source(), "prompt")

    def test_invalid_structured_output_is_rejected_locally(self):
        invalid = dict(PAYLOAD)
        invalid["action"] = "invented_action"
        transport = QueueTransport([self.model_response(), self.completion_response(invalid)])
        with self.assertRaises(EvidenceValidationError):
            EvidenceExtractor(OpenRouterAdapter(self.config(), transport=transport)).extract(
                self.source(), MODEL
            )

    def test_missing_usage_or_content_is_invalid(self):
        no_usage = response({"model": MODEL, "choices": [{"message": {"content": "{}"}}]})
        transport = QueueTransport([self.model_response(), no_usage])
        with self.assertRaises(OpenRouterInvalidResponseError):
            OpenRouterAdapter(self.config(), transport=transport).extract(self.source(), "prompt")

    def test_cache_reuse_makes_one_provider_call_and_preserves_fact(self):
        transport = QueueTransport([self.model_response(), self.completion_response()])
        with tempfile.TemporaryDirectory() as directory:
            extractor = EvidenceExtractor(
                OpenRouterAdapter(self.config(), transport=transport),
                JsonExtractionCache(Path(directory)),
            )
            first = extractor.extract(self.source(), MODEL)
            second = extractor.extract(self.source(), MODEL)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertEqual(first.fact.to_mapping(), second.fact.to_mapping())
        self.assertEqual(len(transport.calls), 2)

    def test_package_explicitly_excludes_secret_env_file(self):
        self.assertTrue(excluded(Path(".env")))
        self.assertTrue(excluded(Path(".env.local")))
        self.assertFalse(excluded(Path(".env.example")))

    def test_env_file_does_not_override_existing_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("OPENROUTER_MODEL=file-model\nNEW_SETTING=from-file\n", encoding="utf-8")
            values = {"OPENROUTER_MODEL": "existing-model"}
            load_env_file(env_path, values)
        self.assertEqual(values["OPENROUTER_MODEL"], "existing-model")
        self.assertEqual(values["NEW_SETTING"], "from-file")


if __name__ == "__main__":
    unittest.main()
