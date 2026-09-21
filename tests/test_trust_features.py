"""Trust-feature tests: reasoning receipt, circuit breaker, red team, automation level.

These features are additive observers/wrappers around the existing pipeline, so the
tests check two things at once: the new behaviour works, and the numbers it reports
come from real pipeline signals (extraction audit trail, validator outcomes,
comparison results) rather than being invented.
"""
import json
import unittest

from backend.services import reasoning_receipt, red_team
from backend.services.automation import AutomationController, field_confidence
from backend.services.circuit_breaker import CircuitBreaker, suggest_recipient
from backend.services.comparator import comparator
from backend.services.dataset_loader import loader

EMAIL_ID = "email_004"


def _doc_texts(email):
    si_text = bl_text = ""
    for att in email.get("attachments", []):
        path = att["path"] if isinstance(att, dict) else str(att)
        if "_si." in path.lower():
            si_text = loader.read_attachment_text(path)
        elif "_bl." in path.lower():
            bl_text = loader.read_attachment_text(path)
    return si_text, bl_text


PASS = {"name": "source_match", "status": "pass"}
FAIL = {"name": "source_match", "status": "fail"}

#: Metadata for passing *mutated* document text through the comparator: it must not
#: contain attachment paths, otherwise the comparator re-extracts from the original
#: files and ignores the text under test.
PIPELINE_METADATA = {"subject": "redteam rehearsal", "body": "redteam rehearsal"}


class TestReasoningReceipt(unittest.TestCase):
    """Feature 1: every field decision is auditable, with real aggregates."""

    def setUp(self):
        self.email = loader.get_email(EMAIL_ID)
        self.si_text, self.bl_text = _doc_texts(self.email)
        self.receipt = reasoning_receipt.build_receipt(
            "TEST-SHIPMENT",
            [{"email_id": EMAIL_ID, "si_text": self.si_text, "bl_text": self.bl_text,
              "names": {"si": "test_SI.txt", "bl": "test_BL.txt"}, "email": self.email}],
            persist=False,
        )

    def test_receipt_row_schema(self):
        self.assertEqual(len(self.receipt["fields"]), len(comparator.FIELDS))
        required = {
            "email_id", "field_name", "decision_path", "rule_matched", "ai_fields_read",
            "ai_fields_skipped", "source_evidence", "validators", "final_decision_by",
            "token_cost", "latency_ms",
        }
        for row in self.receipt["fields"]:
            self.assertTrue(required.issubset(row.keys()), row.get("field_name"))
            self.assertIn(row["decision_path"], ("rule", "ai", "human"))
            self.assertIn(row["final_decision_by"], ("rule_engine", "ai_agent", "human_reviewer"))
            self.assertEqual(len(row["validators"]), 3)
            self.assertEqual({v["name"] for v in row["validators"]},
                             {"source_match", "whitelist", "dcsa_mapping"})

    def test_rule_rows_cite_the_real_rule_that_matched(self):
        rule_rows = [r for r in self.receipt["fields"] if r["decision_path"] == "rule"]
        self.assertTrue(rule_rows)
        for row in rule_rows:
            # Rule ids come from the existing extractor audit trail / anchors.
            self.assertRegex(row["rule_matched"], r"^(field_bank|anchors):")
            self.assertEqual(row["ai_fields_read"], [])

    def test_source_evidence_quotes_the_document(self):
        for row in self.receipt["fields"]:
            evidence = row["source_evidence"]
            if evidence:
                self.assertIn("document", evidence)
                self.assertIsInstance(evidence["char_offset"], int)
                self.assertTrue(evidence["exact_text"])
                # text-extracted docs carry line offsets, not page numbers
                self.assertIsNone(evidence["page"])

    def test_summary_reports_rules_vs_ai_without_fake_tokens(self):
        summary = self.receipt["summary"]
        self.assertEqual(summary["total_fields"], len(comparator.FIELDS))
        self.assertEqual(summary["resolved_by_rules"] + summary["resolved_by_ai"]
                         + summary["resolved_by_human"], summary["total_fields"])
        self.assertEqual(summary["total_ai_calls"], summary["resolved_by_ai"])
        self.assertFalse(summary["tokens_reported"])
        self.assertEqual(summary["total_tokens"], 0)
        self.assertIn("No LLM provider configured", summary["tokens_note"])
        self.assertIn("fields resolved by rules", summary["summary_line"])

    def test_ai_path_is_recorded_with_skipped_rule_fields(self):
        si2, bl2, _notes = red_team.apply_transform(self.si_text, self.bl_text, "reword")
        receipt = reasoning_receipt.build_receipt(
            "TEST-REWORD",
            [{"email_id": EMAIL_ID, "si_text": si2, "bl_text": bl2,
              "names": {"si": "test_SI.txt", "bl": "test_BL.txt"}, "email": PIPELINE_METADATA}],
            persist=False,
        )
        ai_rows = [r for r in receipt["fields"] if r["decision_path"] == "ai"]
        self.assertTrue(ai_rows, "reworded labels must reach the AI fallback")
        for row in ai_rows:
            self.assertEqual(row["final_decision_by"], "ai_agent")
            self.assertIsNone(row["rule_matched"])
            self.assertTrue(row["ai_fields_read"])
            self.assertTrue(row["ai_fields_skipped"],
                            "the receipt must show which fields the rules already handled")
            self.assertIsNone(row["token_cost"])

    def test_human_decisions_are_marked(self):
        overrides = {"reviewer_name": "Pohyi Chong", "si_overrides": {}, "bl_overrides": {"consignee": "ACME LTD"}}
        receipt = reasoning_receipt.build_receipt(
            "TEST-HUMAN",
            [{"email_id": EMAIL_ID, "si_text": self.si_text, "bl_text": self.bl_text,
              "names": {"si": "test_SI.txt", "bl": "test_BL.txt"}, "email": self.email}],
            overrides_by_email={EMAIL_ID: overrides},
            persist=False,
        )
        row = next(r for r in receipt["fields"] if r["field_name"] == "consignee")
        self.assertEqual(row["decision_path"], "human")
        self.assertEqual(row["final_decision_by"], "human_reviewer")



class TestCircuitBreaker(unittest.TestCase):
    """Feature 2: repeated AI validation failures stop the agent."""

    def test_three_consecutive_failures_trip_and_a_pass_resets(self):
        breaker = CircuitBreaker(threshold=3)
        key = "doc-1"
        for i in range(2):
            state = breaker.record(key, "consignee", "X", [FAIL])
            self.assertFalse(state["tripped"], f"tripped too early at {i + 1}")
        state = breaker.record(key, "notify_party", "Y", [FAIL])
        self.assertTrue(state["tripped"])
        self.assertEqual(state["consecutive_ai_failures"], 3)
        self.assertEqual(len(state["failed_fields"]), 3)

        other = CircuitBreaker(threshold=3)
        other.record("doc-2", "shipper", "Z", [FAIL])
        reset = other.record("doc-2", "consignee", "ACME", [PASS])
        self.assertEqual(reset["consecutive_ai_failures"], 0)
        self.assertFalse(reset["tripped"])

    def test_certificate_is_actionable(self):
        breaker = CircuitBreaker(threshold=2)
        key = "doc-3"
        breaker.record(key, "port_of_discharge", None, [FAIL])
        breaker.record(key, "container_count", None, [FAIL])
        certificate = breaker.build_certificate(key, "5ABC-1", email_id="email_004",
                                                missing_or_unclear=["gross_weight_kg"])
        self.assertEqual(certificate["certificate_type"], "ai_refusal")
        self.assertEqual(certificate["consecutive_ai_failures"], 2)
        self.assertIn("port_of_discharge", certificate["missing_or_unclear"])
        self.assertIn("gross_weight_kg", certificate["missing_or_unclear"])
        self.assertEqual(certificate["suggested_recipient"], "carrier")
        self.assertGreater(certificate["estimated_delay_minutes"], 0)
        self.assertIn("documented constant", certificate["estimated_delay_basis"])
        self.assertTrue(certificate["what_would_unblock"])
        self.assertIn("stopped", certificate["notice"].lower())

    def test_recipient_inference(self):
        self.assertEqual(suggest_recipient(["container_count"])["recipient"], "carrier")
        self.assertEqual(suggest_recipient(["consignee"])["recipient"], "shipper")
        self.assertEqual(suggest_recipient(["unknown_field"])["recipient"], "internal_ops")

    def test_missing_fields_trip_the_breaker_through_the_pipeline(self):
        email = loader.get_email(EMAIL_ID)
        si_text, bl_text = _doc_texts(email)
        si2, bl2, notes = red_team.apply_transform(si_text, bl_text, "remove_field")
        receipt = reasoning_receipt.build_receipt(
            "TEST-REMOVE",
            [{"email_id": EMAIL_ID, "si_text": si2, "bl_text": bl2,
              "names": {"si": "test_SI.txt", "bl": "test_BL.txt"}, "email": PIPELINE_METADATA}],
            breaker=CircuitBreaker(threshold=3),
            persist=False,
        )
        self.assertIn("Removed", notes[0])
        self.assertIsNotNone(receipt["refusal_certificate"])
        certificate = receipt["refusal_certificate"]
        self.assertGreaterEqual(certificate["consecutive_ai_failures"], 3)
        self.assertTrue(certificate["failed_fields"])



class TestRedTeam(unittest.TestCase):
    """Feature 3: adversarial input handled by the existing pipeline."""

    def setUp(self):
        self.email = loader.get_email(EMAIL_ID)
        self.si_text, self.bl_text = _doc_texts(self.email)

    def test_catalog_and_determinism(self):
        catalog = {t["id"] for t in red_team.transform_catalog()}
        self.assertEqual(catalog, {"blur", "reword", "remove_field", "conflict"})
        for transform in catalog:
            first = red_team.apply_transform(self.si_text, self.bl_text, transform)
            second = red_team.apply_transform(self.si_text, self.bl_text, transform)
            self.assertEqual(first, second, f"{transform} must be deterministic")
            self.assertEqual(first[0], self.si_text, f"{transform} must only mutate the BL")

    def test_unknown_transform_rejected(self):
        with self.assertRaises(ValueError):
            red_team.apply_transform(self.si_text, self.bl_text, "nope")

    def test_blur_is_rejected_by_the_existing_unreadable_gate(self):
        _si2, bl2, _notes = red_team.apply_transform(self.si_text, self.bl_text, "blur")
        verification = comparator.compare_documents(
            self.si_text, bl2, email_metadata=PIPELINE_METADATA
        )
        # The blurred BL is caught (extractor unreadable gate and/or document validity).
        self.assertEqual(verification["status"], "NEEDS_REVIEW")
        validity = verification.get("document_validity") or {}
        self.assertIn(validity.get("doc_type_guess"), (None, "unreadable"))
        self.assertTrue(
            validity.get("doc_type_guess") == "unreadable"
            or verification.get("review_reason") in ("unreadable", "missing_value", "intent_document_mismatch")
        )

    def test_reword_triggers_evidence_backed_ai_fallback(self):
        si2, bl2, notes = red_team.apply_transform(self.si_text, self.bl_text, "reword")
        receipt = reasoning_receipt.build_receipt(
            "TEST-REWORD2",
            [{"email_id": EMAIL_ID, "si_text": si2, "bl_text": bl2,
              "names": {"si": "test_SI.txt", "bl": "test_BL.txt"}, "email": PIPELINE_METADATA}],
            persist=False,
        )
        attempts = receipt["documents"][0]["ai_attempts"]
        self.assertTrue(attempts, "reworded labels should reach the AI agent")
        self.assertIn("Renamed", notes[0])
        accepted = [a for a in attempts if a["accepted"]]
        self.assertTrue(accepted, "rule-compatible synonyms should be recovered with evidence")
        for attempt in accepted:
            self.assertTrue(attempt["evidence"]["exact_text"])
            self.assertTrue(all(v["status"] == "pass" for v in attempt["validators"]))
        # the comparison itself is still not silently "fixed"
        self.assertNotEqual(receipt["documents"][0]["status"], "OK")

    def test_conflict_is_surfaced_not_auto_resolved(self):
        _si2, bl2, notes = red_team.apply_transform(self.si_text, self.bl_text, "conflict")
        verification = comparator.compare_documents(
            self.si_text, bl2, email_metadata={"subject": "x", "body": "y"}
        )
        self.assertIn("container count", notes[0])
        self.assertEqual(verification["status"], "MISMATCH")
        self.assertIn("container_count", verification["defect_fields"])
        rows = {r["field_key"]: r for r in verification["field_matrix"]}
        self.assertNotEqual(rows["container_count"]["si_value"], rows["container_count"]["bl_value"])


class TestAutomationLevel(unittest.TestCase):
    """Feature 4: the L0-L3 licence, with metrics computed from real signals."""

    HIGH_CONFIDENCE = {
        "agreement": "match",
        "match_type": "EXACT",
        "validators": [
            {"name": "source_match", "status": "pass"},
            {"name": "whitelist", "status": "pass"},
            {"name": "dcsa_mapping", "status": "pass"},
        ],
    }
    WEAK = {
        "agreement": "match",
        "match_type": "FUZZY",
        "validators": [
            {"name": "source_match", "status": "pass"},
            {"name": "whitelist", "status": "n/a"},
            {"name": "dcsa_mapping", "status": "pass"},
        ],
    }
    FAILING = {
        "agreement": "conflict",
        "match_type": "MISMATCH",
        "validators": [
            {"name": "source_match", "status": "fail"},
            {"name": "whitelist", "status": "n/a"},
            {"name": "dcsa_mapping", "status": "pass"},
        ],
    }

    def test_confidence_comes_from_validator_weights(self):
        score, breakdown = field_confidence(self.HIGH_CONFIDENCE["validators"])
        self.assertEqual(score, 1.0)
        self.assertEqual(breakdown["source_match"], 0.5)
        self.assertAlmostEqual(field_confidence(self.FAILING["validators"])[0], 0.2)

    def test_l0_and_l1_never_write(self):
        controller = AutomationController(level=1)
        for level in (0, 1):
            self.assertEqual(controller.classify_field("shipper", self.HIGH_CONFIDENCE, level)["action"],
                             "review")
        self.assertEqual(controller.classify_field("shipper", self.WEAK, 1)["action"], "review")

    def test_l2_audits_and_l3_does_not(self):
        controller = AutomationController()
        self.assertEqual(controller.classify_field("shipper", self.HIGH_CONFIDENCE, 2)["action"],
                         "auto_write_audit")
        self.assertEqual(controller.classify_field("shipper", self.HIGH_CONFIDENCE, 3)["action"],
                         "auto_write")
        for level in (2, 3):
            self.assertEqual(controller.classify_field("shipper", self.FAILING, level)["action"], "review")
            self.assertEqual(controller.classify_field("shipper", self.WEAK, level)["action"], "review")

    def test_preview_is_computed_from_real_field_signals(self):
        from backend.services import automation as automation_module

        email = loader.get_email(EMAIL_ID)
        si_text, bl_text = _doc_texts(email)
        verification = comparator.compare_documents(si_text, bl_text, email_metadata=email)
        summaries = [{"id": EMAIL_ID, "verification": verification}]

        controller = AutomationController(level=1)
        l1 = controller.preview(summaries, 1, use_cache=False)
        l3 = controller.preview(summaries, 3, use_cache=False)

        fields = len(verification["field_matrix"])
        self.assertEqual(l1["sample_basis"]["fields_considered"], fields)
        self.assertEqual(l1["sample_basis"]["emails_considered"], 1)
        self.assertEqual(l1["auto_processed_pct"], 0.0)
        self.assertEqual(l1["flagged_for_review_pct"], 100.0)
        self.assertEqual(l1["counts"]["flagged_for_review"], fields)
        self.assertEqual(l1["estimated_time_saved_minutes"], 0)
        self.assertIn("validator weights", l1["formula"]["confidence"])
        self.assertIn("documented constant", l1["formula"]["estimated_time_saved_minutes"])

        raw_text = (verification.get("bl_extracted") or {}).get("raw_text", "")
        expected_auto = 0
        for row in verification["field_matrix"]:
            signals = automation_module.signals_from_matrix_row(row["field_key"], row, raw_text)
            decision = controller.classify_field(row["field_key"], signals, 3)
            if decision["action"] == "auto_write":
                expected_auto += 1
        self.assertEqual(l3["counts"]["auto_processed"], expected_auto)
        self.assertEqual(l3["counts"]["auto_processed"] + l3["counts"]["flagged_for_review"], fields)
        self.assertGreaterEqual(l3["estimated_error_exposure_pct"], 0.0)

    def test_invalid_level_rejected(self):
        with self.assertRaises(ValueError):
            AutomationController().set_level(7)


class TestTrustApiEndpoints(unittest.TestCase):
    """The new endpoints expose the features without re-running core logic."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from backend.main import app, _derive_shipment_id_from_email

        cls.client = TestClient(app)
        cls.shipment_id = _derive_shipment_id_from_email(loader.get_email(EMAIL_ID))

    def test_receipt_endpoint_returns_ordered_rows_and_summary(self):
        res = self.client.get(f"/api/shipments/{self.shipment_id}/receipt")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body["fields"]), len(comparator.FIELDS))
        self.assertIn("summary_line", body["summary"])
        self.assertIn("total_ai_calls", body["summary"])

    def test_refusal_certificate_endpoint(self):
        res = self.client.get(f"/api/shipments/{self.shipment_id}/refusal-certificate")
        self.assertEqual(res.status_code, 200)
        self.assertIn("certificate", res.json())

    def test_red_team_endpoints(self):
        catalog = self.client.get("/api/red-team/transforms").json()["transforms"]
        self.assertEqual(len(catalog), 4)
        res = self.client.post(f"/api/shipments/{EMAIL_ID}/red-team", json={"transform": "conflict"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["after"]["status"], "MISMATCH")
        self.assertIn("receipt", body)
        bogus = self.client.post(f"/api/shipments/{EMAIL_ID}/red-team", json={"transform": "bogus"})
        self.assertEqual(bogus.status_code, 400)

    def test_automation_endpoints(self):
        info = self.client.get("/api/settings/automation-level").json()
        self.assertIn(info["level"], (0, 1, 2, 3))
        self.assertEqual(len(info["levels"]), 4)

        preview = self.client.get("/api/settings/automation-level/preview?level=2").json()
        self.assertEqual(preview["level"], 2)
        for key in ("auto_processed_pct", "flagged_for_review_pct",
                    "estimated_time_saved_minutes", "estimated_error_exposure_pct"):
            self.assertIn(key, preview)
        self.assertGreater(preview["sample_basis"]["fields_considered"], 0)
        self.assertIn("formula", preview)

        set_res = self.client.post("/api/settings/automation-level", json={"level": 3})
        self.assertEqual(set_res.status_code, 200)
        self.assertEqual(set_res.json()["level"], 3)
        self.client.post("/api/settings/automation-level", json={"level": 1})  # restore default
        self.assertEqual(self.client.post("/api/settings/automation-level", json={"level": 9}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
