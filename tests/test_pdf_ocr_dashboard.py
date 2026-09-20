import unittest
from concurrent.futures import ThreadPoolExecutor

from backend.services.dataset_loader import loader
from backend.services.ocr_dashboard import build_ocr_dashboard
from backend.services.pdf_ocr import _extract_cached, benchmark_pdf, extract_pdf


class TestPdfOcrDashboard(unittest.TestCase):
    def test_searchable_pdf_keeps_its_text_layer(self):
        path = loader.resolve_attachment_path("attachments/email_059_SI.pdf")
        result = extract_pdf(path)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["text_page_count"], 1)
        self.assertEqual(result["ocr_page_count"], 0)
        self.assertIn("APRIL FINE PAPER TRADING", result["text"])

        benchmark = benchmark_pdf(path)
        self.assertEqual(benchmark["benchmark_pages"], 1)
        self.assertIsNotNone(benchmark["accuracy_pct"])

    def test_scanned_pdf_uses_pymupdf_ocr(self):
        path = loader.resolve_attachment_path("attachments/email_512_SI.pdf")
        result = extract_pdf(path)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["ocr_page_count"], 1)
        self.assertIn("SHIPPING INSTRUCTION", result["text"])
        self.assertIn("APRIL FAR EAST", result["text"])
        self.assertIsNone(benchmark_pdf(path)["accuracy_pct"])

    def test_corrupt_pdf_is_visible_as_unreadable(self):
        path = loader.resolve_attachment_path("attachments/email_511_BL.pdf")
        result = extract_pdf(path)

        self.assertEqual(result["status"], "unreadable")
        self.assertEqual(result["text"], "")
        self.assertIn("could not be opened", result["error"])

    def test_concurrent_scan_requests_both_extract_text(self):
        _extract_cached.cache_clear()
        paths = [
            loader.resolve_attachment_path("attachments/email_512_SI.pdf"),
            loader.resolve_attachment_path("attachments/email_513_SI.pdf"),
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(extract_pdf, paths))

        self.assertTrue(all(result["status"] == "ready" for result in results))
        self.assertTrue(all(result["ocr_page_count"] == 1 for result in results))

    def test_dashboard_includes_every_pdf_and_email_number(self):
        dashboard = build_ocr_dashboard(loader)
        self.assertEqual(dashboard["summary"]["total_pdfs"], 28)
        self.assertGreater(dashboard["summary"]["benchmark_pages"], 0)
        self.assertIsNotNone(dashboard["summary"]["ocr_accuracy_pct"])

        scanned = next(doc for doc in dashboard["documents"] if doc["filename"] == "email_512_SI.pdf")
        self.assertEqual(scanned["email_number"], 512)
        self.assertEqual(scanned["method"], "OCR")
        self.assertTrue(scanned["text"])


if __name__ == "__main__":
    unittest.main()
