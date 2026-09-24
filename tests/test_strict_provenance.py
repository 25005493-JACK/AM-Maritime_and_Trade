"""
Unit tests for Strict Provenance Check and Partial-Match Rejection.

Enforces Judge Feedback #4:
- The FULL normalised extracted value must appear in the source text with start_char/end_char.
- Partial matches (matching only first token, line partial, or arbitrary prefix) are rejected.
- Rejected provenance counts as a validator failure toward the circuit breaker.
- Consecutive failures trip the circuit breaker and issue a Refusal Certificate.
"""
import unittest
from backend.services import field_evidence
from backend.services.ai_agent import AIAgent
from backend.services.circuit_breaker import CircuitBreaker

SAMPLE_TEXT = """
SHIPPING INSTRUCTION
Shipper: GLOBAL PAPER SOLUTIONS PTE LTD
Consignee: EAST BRIGHT LOGISTICS FZ-LLC
Port of Loading: SINGAPORE (SGSIN)
Port of Discharge: ROTTERDAM (NLRTM)
Total Containers: 4 x 40'HC
Gross Weight: 84,200 KG
"""

class TestStrictProvenance(unittest.TestCase):

    def test_full_verbatim_match_accepted(self):
        """Full normalized value is present verbatim in the text."""
        span = field_evidence.locate_span(SAMPLE_TEXT, "GLOBAL PAPER SOLUTIONS PTE LTD", allow_partial=False)
        self.assertIsNotNone(span)
        self.assertEqual(span["start_char"], span["char_offset"])
        self.assertEqual(span["end_char"], span["start_char"] + len("GLOBAL PAPER SOLUTIONS PTE LTD"))
        self.assertEqual(SAMPLE_TEXT[span["start_char"]:span["end_char"]], "GLOBAL PAPER SOLUTIONS PTE LTD")
        self.assertIn("exact", span["match_type"])

    def test_whitespace_and_case_tolerant_full_match_accepted(self):
        """Multi-token value with differing whitespace/case is grounded across full span."""
        span = field_evidence.locate_span(SAMPLE_TEXT, "east   bright   logistics   fz-llc", allow_partial=False)
        self.assertIsNotNone(span)
        matched_text = SAMPLE_TEXT[span["start_char"]:span["end_char"]]
        self.assertEqual(matched_text, "EAST BRIGHT LOGISTICS FZ-LLC")

    def test_single_token_partial_match_rejected(self):
        """When extracted value has extra words not in source, single-token match is rejected."""
        # Source text has "GLOBAL PAPER SOLUTIONS PTE LTD", but proposed value is "GLOBAL PAPER SOLUTIONS DUBAI WAREHOUSE"
        proposed = "GLOBAL PAPER SOLUTIONS DUBAI WAREHOUSE"
        span_strict = field_evidence.locate_span(SAMPLE_TEXT, proposed, allow_partial=False)
        self.assertIsNone(span_strict, "Strict provenance must reject partial match when tail tokens do not exist in document")

        # Opt-in partial mode would have matched the prefix or first token
        span_permissive = field_evidence.locate_span(SAMPLE_TEXT, proposed, allow_partial=True)
        self.assertIsNotNone(span_permissive)
        self.assertEqual(span_permissive["match_type"], "token_prefix")

    def test_prefix_partial_match_rejected(self):
        """When only the prefix appears in the document, strict provenance rejects it."""
        proposed = "EAST BRIGHT LOGISTICS FZ-LLC RAKEZ FREE ZONE RAS AL KHAIMAH"
        span_strict = field_evidence.locate_span(SAMPLE_TEXT, proposed, allow_partial=False)
        self.assertIsNone(span_strict, "Strict provenance must reject when value extends beyond document text")

    def test_ai_agent_validator_rejects_partial_match(self):
        """AIAgent validate_proposal marks source_match as 'fail' for partial matches."""
        agent = AIAgent()
        proposal = {
            "attempted_value": "SINGAPORE (SGSIN) TERMINAL 5 EXTENSION",
            "source_document": "SI",
        }
        validators = agent.validate_proposal("port_of_loading", proposal, SAMPLE_TEXT)
        source_val = next((v for v in validators if v["name"] == "source_match"), None)
        self.assertIsNotNone(source_val)
        self.assertEqual(source_val["status"], "fail")
        self.assertIn("partial match rejected", source_val["detail"].lower())

    def test_circuit_breaker_trips_on_consecutive_provenance_failures(self):
        """Failed strict provenance feeds the circuit breaker and trips at threshold (3)."""
        cb = CircuitBreaker(threshold=3)
        doc_key = "test_doc:001"
        agent = AIAgent()

        proposals = [
            ("consignee", "EAST BRIGHT LOGISTICS DUBAI INC"),
            ("port_of_loading", "SINGAPORE TERMINAL BERTH 99"),
            ("port_of_discharge", "ROTTERDAM DEEPWATER BASIN 4"),
        ]

        for idx, (field, val) in enumerate(proposals, start=1):
            proposal = {"attempted_value": val, "source_document": "BL"}
            validators = agent.validate_proposal(field, proposal, SAMPLE_TEXT)
            state = cb.record(doc_key, field, val, validators)
            self.assertEqual(state["consecutive_ai_failures"], idx)

        self.assertTrue(cb.is_tripped(doc_key))
        cert = cb.build_certificate(doc_key=doc_key, shipment_id="TEST-SHIPMENT", email_id="test_001")
        self.assertIsNotNone(cert)
        self.assertEqual(cert["consecutive_ai_failures"], 3)
        self.assertEqual(len(cert["failed_fields"]), 3)
        for failure in cert["failed_fields"]:
            self.assertIn("source_match", failure["why_failed"])

if __name__ == "__main__":
    unittest.main()
