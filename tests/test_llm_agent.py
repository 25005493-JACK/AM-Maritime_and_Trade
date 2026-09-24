"""
Unit tests for DocuMatch Opt-in LLM Agent Layer (Phase 4).
Runs 100% offline using FakeTransport (zero external network calls).
"""
import os
import unittest
from unittest.mock import patch

from llm_agent.client import (
    LLMClient,
    FakeTransport,
    LLMDisabledError,
    LLMSchemaValidationError,
)
from llm_agent.schemas import (
    ClassificationOutput,
    ExtractFieldsOutput,
    FieldExtraction,
    ScanReadOutput,
    MismatchExplanation,
    DraftReply,
)
from llm_agent.validators import (
    check_verbatim_provenance,
    validate_unlocode,
    validate_iso6346,
    calculate_iso6346_check_digit,
)
from llm_agent.tasks import (
    classify_email,
    extract_fields,
    read_scan,
    explain_mismatch,
    draft_reply,
)
from backend.services.circuit_breaker import CircuitBreaker


class TestLLMClientAndSchemas(unittest.TestCase):
    """Tests for LLMClient, FakeTransport, and Pydantic schema validation."""

    def setUp(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "assist"
        self.client = LLMClient(mode="assist", timeout=5, retries=1)

    def tearDown(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "off"

    def test_disabled_when_mode_is_off(self):
        client = LLMClient(mode="off")
        self.assertFalse(client.is_enabled)
        with self.assertRaises(LLMDisabledError):
            client.generate_json("test prompt", ClassificationOutput)

    def test_fake_transport_success(self):
        transport = FakeTransport(
            lambda prompt, schema: {
                "category": "BL_COMPARISON",
                "confidence": 0.95,
                "reasoning": "Clear SI and BL attachments detected.",
            }
        )
        self.client.set_transport(transport)
        self.assertTrue(self.client.is_enabled)

        res: ClassificationOutput = self.client.generate_json("classify email", ClassificationOutput)
        self.assertIsInstance(res, ClassificationOutput)
        self.assertEqual(res.category, "BL_COMPARISON")
        self.assertAlmostEqual(res.confidence, 0.95)
        self.assertEqual(transport.call_count, 1)

    def test_malformed_json_rejection_and_retries(self):
        # Transport returns invalid json/schema
        transport = FakeTransport(lambda prompt, schema: {"invalid_field": 123})
        self.client.set_transport(transport)

        with self.assertRaises(LLMSchemaValidationError):
            self.client.generate_json("prompt", ClassificationOutput)
        # 1 initial + 1 retry = 2 calls
        self.assertEqual(transport.call_count, 2)

    def test_schema_rejects_out_of_bounds_confidence(self):
        # confidence > 1.0 violates Field(le=1.0)
        transport = FakeTransport(
            lambda prompt, schema: {
                "category": "SPAM",
                "confidence": 1.5,
                "reasoning": "Invalid confidence score",
            }
        )
        self.client.set_transport(transport)
        with self.assertRaises(LLMSchemaValidationError):
            self.client.generate_json("prompt", ClassificationOutput)


class TestValidators(unittest.TestCase):
    """Tests for verbatim provenance, UN/LOCODE, and ISO 6346."""

    def test_strict_verbatim_provenance(self):
        doc = "SHIPPER: ACME EXPORTS SDN BHD\nCONSIGNEE: GLOBAL LOGISTICS INC\nPORT OF DISCHARGE: SINGAPORE (SGSIN)"
        self.assertTrue(check_verbatim_provenance("ACME EXPORTS SDN BHD", doc))
        self.assertTrue(check_verbatim_provenance("GLOBAL LOGISTICS INC", doc))
        self.assertTrue(check_verbatim_provenance("SINGAPORE (SGSIN)", doc))

        # Fabricated or hallucinated strings must fail
        self.assertFalse(check_verbatim_provenance("PACIFIC TIMBER CORP", doc))
        self.assertFalse(check_verbatim_provenance("ROTTERDAM PORT", doc))

    def test_unlocode_validator(self):
        # Explicit 5-letter code
        ok, code = validate_unlocode("PORT KLANG (MYPKG)")
        self.assertTrue(ok)
        self.assertEqual(code, "MYPKG")

        ok, code = validate_unlocode("SINGAPORE (SGSIN)")
        self.assertTrue(ok)
        self.assertEqual(code, "SGSIN")

        # Port keyword match
        ok, code = validate_unlocode("Shanghai Terminal Pier 4")
        self.assertTrue(ok)

        # Invalid port description
        ok, code = validate_unlocode("John Doe")
        self.assertFalse(ok)

    def test_iso6346_validator(self):
        # Tally expressions
        self.assertTrue(validate_iso6346("1 x 40'HC")[0])
        self.assertTrue(validate_iso6346("3 x 20'GP")[0])
        self.assertTrue(validate_iso6346("2 UNITS")[0])
        self.assertTrue(validate_iso6346("4")[0])

        # Standard container format (4 letters + 6 or 7 digits)
        self.assertTrue(validate_iso6346("CSQU3054383")[0])
        self.assertTrue(validate_iso6346("MSCU1234567")[0])

        # Invalid container value
        self.assertFalse(validate_iso6346("General Cargo Dry Pack")[0])


class TestLLMTasks(unittest.TestCase):
    """Tests for specialized tasks with guardrails, fallback, and circuit breaker."""

    def setUp(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "assist"

    def tearDown(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "off"

    def test_classify_email_skips_when_rule_confidence_high(self):
        email = {"subject": "Test SI", "body": "Please find attached SI"}
        # Rule confidence 0.95 >= 0.90 -> LLM must not be called
        res = classify_email(email, rule_category="SI_REQUEST", rule_confidence=0.95)
        self.assertEqual(res["category"], "SI_REQUEST")
        self.assertEqual(res["source"], "rules")

    def test_classify_email_invoked_when_rule_confidence_low(self):
        from llm_agent.client import llm_client

        transport = FakeTransport(
            lambda prompt, schema: {
                "category": "BL_COMPARISON",
                "confidence": 0.88,
                "reasoning": "Re-classified by assistant as BL comparison based on attachments.",
            }
        )
        llm_client.set_transport(transport)

        email = {"subject": "FW: Documents for shipment", "body": "See attached"}
        # Rule confidence 0.65 < 0.90 -> LLM invoked
        res = classify_email(email, rule_category="GENERAL", rule_confidence=0.65)
        self.assertEqual(res["category"], "BL_COMPARISON")
        self.assertEqual(res["source"], "ai")
        self.assertEqual(transport.call_count, 1)

    def test_extract_fields_validates_provenance_and_increments_circuit_breaker(self):
        from llm_agent.client import llm_client

        cb = CircuitBreaker(threshold=3)
        doc_key = "test_shipment:doc_001"
        doc_text = "PORT OF LOADING: PORT KLANG (MYPKG)\nWEIGHT: 25000 KG"

        # AI proposes a hallucinated shipper not in the document
        transport = FakeTransport(
            lambda prompt, schema: {
                "fields": {
                    "shipper": {
                        "value": "FABRICATED SHIPPER LTD",
                        "evidence_quote": "SHIPPER: FABRICATED SHIPPER LTD",
                        "confidence": 0.90,
                    }
                }
            }
        )
        llm_client.set_transport(transport)

        with patch("llm_agent.tasks.circuit_breaker", cb):
            res = extract_fields(["shipper"], doc_text, doc_key)
            # Shipper should NOT be accepted because provenance failed
            self.assertNotIn("shipper", res["proposals"])
            self.assertEqual(len(res["receipt_entries"]), 1)
            self.assertFalse(res["receipt_entries"][0]["accepted"])
            self.assertEqual(res["circuit_breaker"]["consecutive_ai_failures"], 1)

            # Second hallucination
            res2 = extract_fields(["shipper"], doc_text, doc_key)
            self.assertEqual(res2["circuit_breaker"]["consecutive_ai_failures"], 2)

            # Third hallucination -> Breaker trips
            res3 = extract_fields(["shipper"], doc_text, doc_key)
            self.assertEqual(res3["circuit_breaker"]["consecutive_ai_failures"], 3)
            self.assertTrue(res3["circuit_breaker"]["tripped"])
            self.assertTrue(cb.is_tripped(doc_key))

    def test_extract_fields_accepts_valid_provenance(self):
        from llm_agent.client import llm_client

        cb = CircuitBreaker(threshold=3)
        doc_key = "test_shipment:doc_002"
        doc_text = "PORT OF LOADING: PORT KLANG (MYPKG)\nCONTAINERS: 2 x 40'HC"

        transport = FakeTransport(
            lambda prompt, schema: {
                "fields": {
                    "port_of_loading": {
                        "value": "PORT KLANG (MYPKG)",
                        "evidence_quote": "PORT OF LOADING: PORT KLANG (MYPKG)",
                        "confidence": 0.98,
                    }
                }
            }
        )
        llm_client.set_transport(transport)

        with patch("llm_agent.tasks.circuit_breaker", cb):
            res = extract_fields(["port_of_loading"], doc_text, doc_key)
            self.assertIn("port_of_loading", res["proposals"])
            self.assertEqual(res["proposals"]["port_of_loading"]["value"], "MYPKG")
            self.assertEqual(res["circuit_breaker"]["consecutive_ai_failures"], 0)

    def test_read_scan_always_marked_unverified(self):
        from llm_agent.client import llm_client

        transport = FakeTransport(
            lambda prompt, schema: {
                "extracted_text": "BILL OF LADING SCAN CONTENT",
                "confidence": 0.85,
                "is_image_scan": True,
                "verification_status": "unverified",
                "notes": "Legible header, blurred stamps",
            }
        )
        llm_client.set_transport(transport)

        scan_out = read_scan({"filename": "scan.pdf"}, ocr_raw_text="blurred OCR text")
        self.assertIsInstance(scan_out, ScanReadOutput)
        self.assertEqual(scan_out.verification_status, "unverified")
        self.assertTrue(scan_out.is_image_scan)

    def test_advisory_tools(self):
        from llm_agent.client import llm_client

        transport_exp = FakeTransport(
            lambda prompt, schema: {
                "field_name": "consignee",
                "summary": "Consignee mismatch: SI says Acme Ltd, BL says Acme Global.",
                "recommended_action": "Request updated BL with correct legal name.",
                "advisory": True,
            }
        )
        llm_client.set_transport(transport_exp)
        exp = explain_mismatch("consignee", "Acme Ltd", "Acme Global")
        self.assertTrue(exp.advisory)
        self.assertEqual(exp.field_name, "consignee")

        transport_draft = FakeTransport(
            lambda prompt, schema: {
                "recipient": "agent@shipping.com",
                "subject": "Re: B/L Revision Needed",
                "body": "Please amend consignee to Acme Ltd.",
                "advisory": True,
            }
        )
        llm_client.set_transport(transport_draft)
        draft = draft_reply(
            {"sender": "agent@shipping.com", "subject": "B/L Draft"},
            [{"field": "consignee", "si": "Acme Ltd", "bl": "Acme Global"}],
        )
        self.assertTrue(draft.advisory)
        self.assertEqual(draft.recipient, "agent@shipping.com")


if __name__ == "__main__":
    unittest.main()
