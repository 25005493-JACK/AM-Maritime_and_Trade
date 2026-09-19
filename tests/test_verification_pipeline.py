import unittest
from backend.services.classifier import classifier
from backend.services.extractor import extractor
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator
from backend.services.calendar_service import calendar_service

class TestVerificationPipeline(unittest.TestCase):

    def test_email_classification(self):
        spam_email = {
            "subject": "Discount on office stationery!",
            "body": "Click here to claim coupon for special sale",
            "attachments": []
        }
        res_spam = classifier.classify(spam_email)
        self.assertEqual(res_spam["category"], "SPAM")
        self.assertFalse(res_spam["is_comparison_request"])

        doc_email = {
            "subject": "Draft BL check for SI #8801",
            "body": "Please cross check SI and draft BL",
            "attachments": [
                {"filename": "SI.txt", "path": "attachments/SI.txt", "doc_type": "SI"},
                {"filename": "BL.txt", "path": "attachments/BL.txt", "doc_type": "BL"}
            ]
        }
        res_doc = classifier.classify(doc_email)
        self.assertEqual(res_doc["category"], "BL_COMPARISON")
        self.assertTrue(res_doc["is_comparison_request"])

    def test_field_extraction_and_alias_normalization(self):
        sample_text = """
        SHIPPING INSTRUCTION
        Shipper: Global Traders Inc, Singapore
        Consignee: European Distribution Ltd
        Notify Party: Euro Logistics BV
        Load Port: Singapore (SGSIN)
        Discharge Port: Rotterdam (NLRTM)
        Container Summary: 3 containers
        Gross Weight: 22.0 Metric Tons
        """
        fields = extractor.extract_fields(sample_text, doc_type_hint="SI")
        self.assertIn("Global Traders Inc", fields["shipper"])
        self.assertIn("European Distribution Ltd", fields["consignee"])
        self.assertIn("Euro Logistics BV", fields["notify_party"])
        self.assertIn("Singapore", fields["port_of_loading"])
        self.assertIn("Rotterdam", fields["port_of_discharge"])
        self.assertEqual(fields["container_count"], 3)
        self.assertEqual(fields["gross_weight_kg"], 22000.0)

    def test_document_comparator_mismatch(self):
        si_text = """
        Shipper: Global Traders Inc
        Consignee: European Distribution Ltd
        Notify Party: Euro Logistics BV
        Port of Loading: Singapore (SGSIN)
        Port of Discharge: Rotterdam (NLRTM)
        Container Count: 3 containers
        Gross Weight: 22000 kg
        """
        bl_text = """
        Shipper: Global Traders Inc
        Consignee: European Distribution Ltd
        Notify Party: Euro Logistics BV
        Load Port: Singapore (SGSIN)
        Discharge Port: Rotterdam (NLRTM)
        Container Count: 4 containers
        Gross Weight: 22000 kg
        """
        comp = comparator.compare_documents(si_text, bl_text)
        self.assertEqual(comp["status"], "MISMATCH")
        self.assertTrue(comp["has_defect"])
        self.assertIn("container_count", comp["defect_fields"])

    def test_document_comparator_human_review(self):
        si_text = """
        Shipper: Fast Freight GmbH
        Consignee: Tokyo Import Corp
        Notify Party: Nippon Logistics KK
        Port of Loading: Hamburg
        Port of Discharge: Tokyo
        Container Count: 1 container
        Gross Weight: 12400 kg
        """
        bl_text_damaged = """
        [OCR SCAN RESULT - QUALITY SCORE: 0.34]
        Shipper: Fast Freight GmbH
        Consignee: Tokyo Import Corp
        Notify Party: Nippon Logistics KK
        Port of Loading: Hamburg
        Port of Discharge: Tokyo
        Container Count: 1 container
        GROSS WEIGHT: [ERROR: OCR_CORRUPTED_STREAM_UNCERTAIN_WEIGHT_VALUE_0x99A?] kg
        """
        comp = comparator.compare_documents(si_text, bl_text_damaged)
        self.assertEqual(comp["status"], "NEEDS_REVIEW")
        self.assertTrue(comp["requires_human_review"])
        self.assertEqual(comp["review_reason"], "unreadable")

    def test_self_evaluation_endpoint(self):
        ground_truth = evaluator.process_all_emails()
        self.assertEqual(len(ground_truth), 520)
        score_report = evaluator.evaluate_submission(ground_truth)
        self.assertGreater(score_report["overall_score"], 90.0)
        self.assertEqual(score_report["total_emails_processed"], 520)

    def test_vessel_calendar_port_filtering(self):
        # Global view (ALL)
        all_vessels = calendar_service.get_calendar("ALL")
        self.assertGreaterEqual(len(all_vessels), 5)

        # Filter by Rotterdam
        rotterdam_vessels = calendar_service.get_calendar("Rotterdam (NLRTM)")
        self.assertGreaterEqual(len(rotterdam_vessels), 1)
        self.assertTrue(all("Rotterdam" in v["destination_port"] for v in rotterdam_vessels))

        # Filter by Hamburg
        hamburg_vessels = calendar_service.get_calendar("Hamburg (DEHAM)")
        self.assertGreaterEqual(len(hamburg_vessels), 1)
        self.assertTrue(all("Hamburg" in v["destination_port"] for v in hamburg_vessels))
        self.assertFalse(any(v["vessel_name"] == "MSC ISABELLA" for v in hamburg_vessels))

if __name__ == "__main__":
    unittest.main()
