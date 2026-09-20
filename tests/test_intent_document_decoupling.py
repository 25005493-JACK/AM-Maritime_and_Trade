import unittest
import os
import json
from pathlib import Path

from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.document_validator import assess_document_validity, REQUIRED_SI_FIELDS
from backend.services.event_logger import event_logger

class TestIntentDocumentDecoupling(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        for p in Path("data/results").glob("email_test_*.json"):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

    def test_layer2_assess_valid_si(self):
        """Valid SI with all 7 fields should have 100% coverage and be comparable."""
        fields = {
            "shipper": "ACME SHIPPING CORP",
            "consignee": "GLOBAL IMPORTS LTD",
            "notify_party": "SAME AS CONSIGNEE",
            "port_of_loading": "SINGAPORE",
            "port_of_discharge": "ROTTERDAM",
            "container_count": 2,
            "gross_weight_kg": 45000.0
        }
        res = assess_document_validity(fields, doc_type_guess="si", raw_text="SHIPPING INSTRUCTION\nShipper: ACME...")
        self.assertTrue(res["is_comparable"])
        self.assertEqual(res["coverage_ratio"], 1.0)
        self.assertEqual(len(res["missing_fields"]), 0)
        self.assertEqual(res["doc_type_guess"], "si")

    def test_layer2_assess_booking_confirmation(self):
        """Booking confirmation signature should immediately flag as non-comparable."""
        raw_text = "CARRIER BOOKING CONFIRMATION\nBooking Ref: BKG-99214\nVessel: OCEAN STAR\nLoad Port: SINGAPORE"
        res = assess_document_validity({}, doc_type_guess="unknown", raw_text=raw_text)
        self.assertFalse(res["is_comparable"])
        self.assertEqual(res["doc_type_guess"], "booking_confirmation")
        self.assertIn("Booking Confirmation", res["reason"])

    def test_layer2_assess_low_coverage_si(self):
        """Incomplete document with only 2 of 7 fields (coverage 0.286 < 0.6) should fail comparability."""
        fields = {
            "shipper": "ACME SHIPPING CORP",
            "consignee": "GLOBAL IMPORTS LTD",
            "notify_party": None,
            "port_of_loading": None,
            "port_of_discharge": None,
            "container_count": None,
            "gross_weight_kg": None
        }
        res = assess_document_validity(fields, doc_type_guess="si", raw_text="DRAFT DOCUMENT\nShipper: ACME\nConsignee: GLOBAL")
        self.assertFalse(res["is_comparable"])
        self.assertLess(res["coverage_ratio"], 0.6)
        self.assertEqual(len(res["missing_fields"]), 5)
        self.assertIn("container_count", res["missing_fields"])

    def test_layer3_decoupling_gate_booking_confirmation_with_compare_intent(self):
        """
        Email says 'please compare', but attachment is a booking confirmation.
        Must NOT produce field-level comparison. Must return NEEDS_REVIEW with intent_document_mismatch.
        """
        email_metadata = {
            "id": "email_test_booking_mismatch",
            "subject": "Please compare SI against draft BL",
            "body": "Dear team, please check and compare the attached documents.",
            "attachments": []
        }
        si_text = "CARRIER BOOKING CONFIRMATION\nBooking No: BKG-123456\nShipper: ALPHA CORP\nLoad Port: SINGAPORE"
        bl_text = "BILL OF LADING\nB/L No: OOLU12345\nShipper: ALPHA CORP\nPort of Loading: SINGAPORE"

        res = comparator.compare_documents(
            si_text=si_text,
            bl_text=bl_text,
            email_metadata=email_metadata
        )

        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "intent_document_mismatch")
        self.assertFalse(res["can_compare"])
        self.assertIn("document_validity", res)
        self.assertEqual(res["document_validity"]["doc_type_guess"], "booking_confirmation")
        self.assertIn("does not qualify as a comparable SI", res["summary_message"])
        self.assertEqual(len(res["defect_fields"]), 0)

    def test_layer3_decoupling_gate_incomplete_doc_with_compare_intent(self):
        """
        Email says 'please check the BL matches the SI', but SI is missing container_count and weight (<0.6).
        Must return intent_document_mismatch with missing fields listed.
        """
        email_metadata = {
            "id": "email_test_incomplete_si",
            "subject": "RE: Verify BL matches SI for 5ALT-10023",
            "body": "Please verify the draft BL matches the SI.",
            "attachments": []
        }
        si_text = "SHIPPING INSTRUCTION\nShipper: ALPHA CORP\nConsignee: BETA LTD"
        bl_text = "BILL OF LADING\nShipper: ALPHA CORP\nConsignee: BETA LTD\nLoad Port: SINGAPORE"

        res = comparator.compare_documents(
            si_text=si_text,
            bl_text=bl_text,
            email_metadata=email_metadata
        )

        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "intent_document_mismatch")
        self.assertFalse(res["can_compare"])
        self.assertIn("container_count", res["document_validity"]["missing_fields"])

    def test_happy_path_valid_si_and_bl_compares_cleanly(self):
        """Valid SI with high coverage proceeds through normal comparison without friction."""
        email_metadata = {
            "id": "email_test_valid_compare",
            "subject": "Please verify the draft BL against SI",
            "body": "Please cross check SI and BL.",
            "attachments": []
        }
        si_text = """
SHIPPING INSTRUCTION
Shipper: ASIA PACIFIC PAPERBOARD TRADING PTE LTD | 80 RAFFLES PLACE
Consignee: PACIFIC OFFICE (M) SDN BHD
Notify Party: PACIFIC OFFICE (M) SDN BHD
Port of Loading: SINGAPORE
Port of Discharge: KOPER, SLOVENIA
No. of Containers: 5 x 20'GP
Gross Weight: 68,649 KG
"""
        bl_text = """
BILL OF LADING
Shipper: ASIA PACIFIC PAPERBOARD TRADING PTE LTD | 80 RAFFLES PLACE
Consignee: PACIFIC OFFICE (M) SDN BHD
Notify Party: PACIFIC OFFICE (M) SDN BHD
Port of Loading: SINGAPORE
Port of Discharge: KOPER, SLOVENIA
No. of Containers: 5 x 20'GP
Gross Weight: 68,649 KG
"""
        res = comparator.compare_documents(
            si_text=si_text,
            bl_text=bl_text,
            email_metadata=email_metadata
        )

        self.assertEqual(res["status"], "OK")
        self.assertIsNone(res["review_reason"])
        self.assertTrue(res["can_compare"])
        self.assertFalse(res["has_defect"])

    def test_duckdb_logs_intent_document_mismatch(self):
        """DuckDB event logger should record intent_document_mismatch event."""
        eid = "email_test_event_log"
        event_id = event_logger.log_intent_document_mismatch(
            email_id=eid,
            reason="Attachment is a Booking Confirmation, not an SI",
            coverage_ratio=0.14,
            missing_fields=["container_count", "gross_weight_kg"],
            doc_type_guess="booking_confirmation"
        )
        # If DuckDB is installed, event_id is returned
        if event_id is not None:
            self.assertIsInstance(event_id, str)

if __name__ == "__main__":
    unittest.main()
