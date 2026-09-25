import unittest
import os
import json
from pathlib import Path

from backend.services.pdf_inspector import classify_pdf
from backend.services.extractor import extract_attachment, extractor, ExtractionResult
from backend.services.field_bank import field_bank
from backend.services.port_lookup import port_lookup
from backend.services.anchors import parse_container_count, parse_gross_weight_kg
from backend.services.comparator import comparator
from backend.services.dataset_loader import loader

class TestRulesFirstPipeline(unittest.TestCase):

    def test_pdf_classification(self):
        """Verify pdf_inspector correctly identifies scanned, text-based, and corrupted PDFs."""
        # Corrupted PDF raises exception
        corrupted_path = loader.resolve_attachment_path("attachments/email_511_BL.pdf")
        with self.assertRaises(Exception):
            classify_pdf(corrupted_path)

        # Scanned PDF identified without OCR
        scanned_path = loader.resolve_attachment_path("attachments/email_512_BL.pdf")
        self.assertEqual(classify_pdf(scanned_path), "scanned")

        # Text-based PDF identified
        text_pdf_path = loader.resolve_attachment_path("attachments/email_059_BL.pdf")
        self.assertEqual(classify_pdf(text_pdf_path), "text_based")

    def test_extractor_routed_pipeline(self):
        """Verify extract_attachment routes by extension and assigns correct reason codes."""
        # Scanned PDF returns scanned_not_processed
        scanned_res = extract_attachment(loader.resolve_attachment_path("attachments/email_512_BL.pdf"), doc_type_hint="BL")
        self.assertEqual(scanned_res.status, "NEEDS_REVIEW")
        self.assertEqual(scanned_res.reason_code, "scanned_not_processed")

        # Corrupted PDF returns corrupted_file
        corrupt_res = extract_attachment(loader.resolve_attachment_path("attachments/email_511_BL.pdf"), doc_type_hint="BL")
        self.assertEqual(corrupt_res.status, "NEEDS_REVIEW")
        self.assertEqual(corrupt_res.reason_code, "corrupted_file")

        # TXT attachment parses correctly
        txt_res = extract_attachment(loader.resolve_attachment_path("attachments/email_004_SI.txt"), doc_type_hint="SI")
        self.assertEqual(txt_res.status, "OK")
        self.assertIsNotNone(txt_res["shipper"])

    def test_field_bank_resolution(self):
        """Verify exact, fuzzy, and unresolved resolution in field_bank."""
        # Exact lookup
        exact_res = field_bank.resolve_label("Shipper (Principal or Seller)")
        self.assertEqual(exact_res["canonical"], "shipper")
        self.assertEqual(exact_res["method"], "exact")
        self.assertEqual(exact_res["confidence"], 1.0)

        # Bilingual observed variant
        bilingual_res = field_bank.resolve_label("Total Containers (箱数)")
        self.assertEqual(bilingual_res["canonical"], "container_count")
        self.assertEqual(bilingual_res["confidence"], 1.0)

        # Fuzzy match
        fuzzy_res = field_bank.resolve_label("Consignee (Non Negotiable)")
        self.assertEqual(fuzzy_res["canonical"], "consignee")
        self.assertGreaterEqual(fuzzy_res["confidence"], 0.85)

        # Unresolved term
        unknown_res = field_bank.resolve_label("Completely Random Custom Label 99")
        self.assertTrue(unknown_res["is_unresolved"])
        self.assertIsNone(unknown_res["canonical"])

    def test_port_lookup_unlocode(self):
        """Verify UN/LOCODE normalization and fallback auditing."""
        # Parenthetical code extraction
        self.assertEqual(port_lookup.resolve_port_code("SINGAPORE (SGSIN)"), "SGSIN")
        self.assertEqual(port_lookup.resolve_port_code("APAPA, NIGERIA (NGAPP)"), "NGAPP")

        # Port name resolution
        self.assertEqual(port_lookup.resolve_port_code("BUATAN, INDONESIA"), "IDBUA")
        self.assertEqual(port_lookup.resolve_port_code("BUSAN, SOUTH KOREA"), "KRPUS")

        # Port comparison by code
        matched, audit = port_lookup.compare_ports("SINGAPORE", "SINGAPORE (SGSIN)")
        self.assertTrue(matched)
        self.assertEqual(audit["method"], "unlocode")

        # Port mismatch by code
        mismatched, audit2 = port_lookup.compare_ports("BALTIMORE, US (USBAL)", "APAPA, NIGERIA (NGAPP)")
        self.assertFalse(mismatched)
        self.assertEqual(audit2["si_code"], "USBAL")
        self.assertEqual(audit2["bl_code"], "NGAPP")

    def test_anchors_value_extraction(self):
        """Verify value-shaped container count and weight extraction."""
        self.assertEqual(parse_container_count("15 x 20'GP"), 15)
        self.assertEqual(parse_container_count("12 x 20'FCL"), 12)
        self.assertEqual(parse_container_count("8 x 40'HQ"), 8)
        self.assertEqual(parse_container_count("3 containers"), 3)

        self.assertEqual(parse_gross_weight_kg("22,000.50 KGS"), 22000.50)
        self.assertEqual(parse_gross_weight_kg("22.0 MT"), 22000.0)
        self.assertEqual(parse_gross_weight_kg("22 500 kg"), 22500.0)

    def test_comparator_pre_check_low_field_count(self):
        """Verify short-circuit to wrong_doc_type when <2 fields are resolved."""
        mostly_empty_text = "Some random letter\nDate: 2026-01-01\nRegards, Ops"
        normal_si = """
        Shipper: Global Traders
        Consignee: Euro Dist
        Port of Loading: Singapore
        Port of Discharge: Rotterdam
        Container Count: 3
        Gross Weight: 20000 kg
        """
        res = comparator.compare_documents(normal_si, mostly_empty_text)
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "wrong_doc_type")

    def test_scanned_and_corrupted_classification_in_dataset(self):
        """Verify known scanned-document and corrupted emails are classified correctly."""
        e511 = loader.get_email("email_511")
        res511 = comparator.compare_documents("", "", email_metadata=e511)
        self.assertEqual(res511["status"], "NEEDS_REVIEW")
        self.assertEqual(res511["review_reason"], "corrupted_file")

        e512 = loader.get_email("email_512")
        res512 = comparator.compare_documents("", "", email_metadata=e512)
        self.assertEqual(res512["status"], "NEEDS_REVIEW")
        self.assertEqual(res512["review_reason"], "scanned_not_processed")

    def test_flat_file_results_stored(self):
        """Verify results are persisted to flat JSON files under data/results/."""
        results_path = Path("data/results/email_511.json")
        self.assertTrue(results_path.exists())
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["email_id"], "email_511")
        self.assertEqual(data["review_reason"], "corrupted_file")

if __name__ == "__main__":
    unittest.main()
