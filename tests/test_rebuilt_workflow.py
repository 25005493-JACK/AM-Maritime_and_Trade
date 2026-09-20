import unittest
import os
import json
from backend.services.dataset_loader import loader
from backend.services.classifier import classifier
from backend.services.extractor import extractor
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator

class TestRebuiltShippingWorkflow(unittest.TestCase):

    def test_dataset_loader_520_emails(self):
        """Verify loader loads all 520 emails from the test dataset."""
        emails = loader.load_inbox()
        self.assertEqual(len(emails), 520, f"Expected 520 emails, found {len(emails)}")
        self.assertEqual(emails[0]["id"], "email_001")
        self.assertEqual(emails[-1]["id"], "email_520")

    def test_multi_format_attachment_reading(self):
        """Verify reading across txt, pdf, docx, and xlsx attachments."""
        # TXT
        txt_content = loader.read_attachment_text("attachments/email_001_SI.txt")
        self.assertIn("SHIPPING INSTRUCTION", txt_content)
        self.assertIn("APRIL FAR EAST", txt_content)

        # XLSX
        xlsx_content = loader.read_attachment_text("attachments/email_005_SI.xlsx")
        self.assertIn("ASIA PACIFIC PAPERBOARD", xlsx_content)

        # DOCX
        docx_content = loader.read_attachment_text("attachments/email_055_BL.docx")
        self.assertIn("BILL OF LADING", docx_content)
        self.assertIn("AL GURG STATIONERY", docx_content)

        # PDF
        pdf_content = loader.read_attachment_text("attachments/email_059_SI.pdf")
        self.assertIn("Shipper", pdf_content)
        self.assertIn("APRIL FINE PAPER TRADING", pdf_content)

    def test_classifier_5_categories(self):
        """Verify classification into 5 hackathon categories: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM."""
        # BL_COMPARISON
        e1 = loader.get_email("email_001")
        c1 = classifier.classify(e1)
        self.assertEqual(c1["category"], "BL_COMPARISON")
        self.assertTrue(c1["is_comparison_request"])

        # Dropped attachment comparison request
        e506 = loader.get_email("email_506")
        c506 = classifier.classify(e506)
        self.assertEqual(c506["category"], "BL_COMPARISON")

        # SI_REQUEST
        e7 = loader.get_email("email_007")
        c7 = classifier.classify(e7)
        self.assertEqual(c7["category"], "SI_REQUEST")

        # INVOICE_QUERY
        e2 = loader.get_email("email_002")
        c2 = classifier.classify(e2)
        self.assertEqual(c2["category"], "INVOICE_QUERY")

        # GENERAL
        e11 = loader.get_email("email_011")
        c11 = classifier.classify(e11)
        self.assertEqual(c11["category"], "GENERAL")

        # SPAM
        e15 = loader.get_email("email_015")
        c15 = classifier.classify(e15)
        self.assertEqual(c15["category"], "SPAM")

        e417 = loader.get_email("email_417")
        c417 = classifier.classify(e417)
        self.assertEqual(c417["category"], "SPAM")

    def test_7_field_extraction(self):
        """Verify extraction of the 7 shipping fields and normalization."""
        raw_si = loader.read_attachment_text("attachments/email_001_SI.txt")
        fields = extractor.extract_fields(raw_si, doc_type_hint="SI")
        
        self.assertIn("APRIL FAR EAST", fields["shipper"])
        self.assertIn("MOORIM SP", fields["consignee"])
        self.assertIn("UAB NOVAKOPA", fields["notify_party"])
        self.assertIn("PORT KLANG", fields["port_of_loading"])
        self.assertIn("CALLAO", fields["port_of_discharge"])
        self.assertEqual(fields["container_count"], 1)
        self.assertEqual(fields["gross_weight_kg"], 21577.0)

    def test_document_comparator_ok(self):
        """Verify OK outcome when all 7 fields match (email_001)."""
        e1 = loader.get_email("email_001")
        si_text = loader.read_attachment_text("attachments/email_001_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_001_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=e1)
        self.assertEqual(res["status"], "OK")
        self.assertFalse(res["has_defect"])
        self.assertEqual(res["defect_fields"], [])
        self.assertIsNone(res["review_reason"])

    def test_document_comparator_mismatch(self):
        """Verify MISMATCH outcome with defect_fields (email_004)."""
        e4 = loader.get_email("email_004")
        si_text = loader.read_attachment_text("attachments/email_004_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_004_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=e4)
        self.assertEqual(res["status"], "MISMATCH")
        self.assertTrue(res["has_defect"])
        self.assertIn("consignee", res["defect_fields"])
        self.assertIsNone(res["review_reason"])

    def test_needs_review_wrong_doc_type(self):
        """Verify NEEDS_REVIEW with wrong_doc_type (email_501: Commercial Invoice)."""
        e501 = loader.get_email("email_501")
        si_text = loader.read_attachment_text("attachments/email_501_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_501_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=e501)
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "wrong_doc_type")

    def test_needs_review_missing_attachment(self):
        """Verify Pre-Comparison Gate halts comparison and escalates missing_attachment."""
        # Test email_510 (0 attachments: dropped documents)
        e510 = loader.get_email("email_510")
        res510 = comparator.compare_documents("", "", email_metadata=e510)
        self.assertEqual(res510["status"], "NEEDS_REVIEW")
        self.assertEqual(res510["review_reason"], "missing_attachment")
        self.assertIn("pre_comparison_gate", res510)
        gate510 = res510["pre_comparison_gate"]
        self.assertFalse(gate510["passed"])
        self.assertFalse(gate510["comparison_possible"])
        self.assertFalse(gate510["si_attached"])
        self.assertFalse(gate510["bl_attached"])
        self.assertEqual(gate510["reference_no"], "PSGSE8356691")
        self.assertIn("Please resend the SI and draft BL for PSGSE8356691", gate510["operational_response_draft"])

        # Test email_507 (1 attachment: draft BL dropped)
        e507 = loader.get_email("email_507")
        si_text = loader.read_attachment_text("attachments/email_507_SI.txt")
        res507 = comparator.compare_documents(si_text, "", email_metadata=e507)
        self.assertEqual(res507["status"], "NEEDS_REVIEW")
        self.assertEqual(res507["review_reason"], "missing_attachment")
        gate507 = res507["pre_comparison_gate"]
        self.assertFalse(gate507["passed"])
        self.assertTrue(gate507["si_attached"])
        self.assertFalse(gate507["bl_attached"])
        self.assertIn("Please provide the draft Bill of Lading for I756178688", gate507["operational_response_draft"])

    def test_needs_review_unreadable(self):
        """Verify NEEDS_REVIEW with unreadable (email_511: corrupted PDF bytes)."""
        e511 = loader.get_email("email_511")
        si_text = loader.read_attachment_text("attachments/email_511_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_511_BL.pdf")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=e511)
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertIn(res["review_reason"], ("corrupted_file", "unreadable"))

    def test_needs_review_missing_value(self):
        """Verify NEEDS_REVIEW with missing_value (email_520: missing consignee in SI)."""
        e520 = loader.get_email("email_520")
        si_text = loader.read_attachment_text("attachments/email_520_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_520_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=e520)
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "missing_value")

    def test_evaluator_submission_format(self):
        """Verify submission format matches sample_submission.json for all 520 emails."""
        sub = evaluator.process_all_emails()
        self.assertEqual(len(sub), 520)

        # Compare sample shape
        e1_sub = sub["email_001"]
        self.assertIn("category", e1_sub)
        self.assertIn("status", e1_sub)
        self.assertIn("review_reason", e1_sub)
        self.assertIn("has_defect", e1_sub)
        self.assertIn("defect_fields", e1_sub)

        report = evaluator.evaluate_submission(sub)
        self.assertGreater(report["overall_score"], 90.0)
        self.assertEqual(report["total_emails_processed"], 520)
        self.assertEqual(report["bl_comparison_total"], 129)

if __name__ == "__main__":
    unittest.main()
