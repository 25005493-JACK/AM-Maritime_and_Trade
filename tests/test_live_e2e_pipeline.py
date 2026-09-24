import unittest
import os
import json
import glob
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app, HUMAN_OVERRIDES, save_persisted_overrides, load_persisted_overrides, OVERRIDES_FILE
from backend.services.dataset_loader import loader

class TestLiveEndToEndPipeline(unittest.TestCase):
    """
    PHASE 3 Integration Test:
    Upload -> Process -> Correct -> Reload -> Persisted
    """

    def setUp(self):
        self.client = TestClient(app)
        self.created_email_ids = []
        self.auth_headers = {"Authorization": "Bearer documatch-reviewer-dev-key-2026"}

    def tearDown(self):
        # Clean up any created test files
        for eid in self.created_email_ids:
            # Clean up overrides
            if eid in HUMAN_OVERRIDES:
                del HUMAN_OVERRIDES[eid]
            # Remove email files
            email_pattern = os.path.join(loader.inbox_dir, f"{eid}*.json")
            for f in glob.glob(email_pattern):
                try:
                    os.remove(f)
                except OSError:
                    pass
            # Remove attachment files
            att_pattern = os.path.join(loader.attachments_dir, f"{eid}*")
            for f in glob.glob(att_pattern):
                try:
                    os.remove(f)
                except OSError:
                    pass
        save_persisted_overrides()
        loader.load_inbox(force_reload=True)

    def test_e2e_upload_process_correct_reload_persisted(self):
        """
        Full lifecycle test:
        1. Upload: Post newly uploaded SI + BL pair with intentional container count discrepancy
        2. Process: Verified through real pipeline: classified as BL_COMPARISON, mismatch detected
        3. Correct: Reviewer submits correction to reconcile container count
        4. Reload: Wipe in-memory state, reload from disk/file storage
        5. Persisted: Confirm reviewer correction and verified state survive reload
        """
        si_content = """SHIPPING INSTRUCTION
========================================
Shipper: EAST ASIA TRADING CORP
  88 SHENTON WAY, SINGAPORE 068811
Consignee: PACIFIC LOGISTICS LLC
  1200 BRICKELL AVENUE, MIAMI, FL, US
Notify Party: SAME AS CONSIGNEE
Port of Loading: SINGAPORE (SGSIN)
Port of Discharge: HOUSTON, US (USHOU)
Container Count: 3 x 40'HC
Gross Weight: 50,000 KG
Commodity: TEXTILE FABRIC MATERIALS
Vessel & Voyage: MSC ISABELLA V.2026W
Booking No: BKG-LIVE-9001
"""

        bl_content = """BILL OF LADING (DRAFT)
========================================
Shipper: EAST ASIA TRADING CORP
  88 SHENTON WAY, SINGAPORE 068811
Consignee: PACIFIC LOGISTICS LLC
  1200 BRICKELL AVENUE, MIAMI, FL, US
Notify Party: SAME AS CONSIGNEE
Port of Loading: SINGAPORE (SGSIN)
Port of Discharge: HOUSTON, US (USHOU)
Container Count: 4 x 40'HC
Gross Weight: 50,000 KG
Commodity: TEXTILE FABRIC MATERIALS
Vessel & Voyage: MSC ISABELLA V.2026W
B/L Reference: BL-LIVE-9001
"""

        # ── 1. UPLOAD (With Reviewer Auth) ──────────────────────────────────
        upload_payload = {
            "subject": "RE: TO CONFIRM DOCS _ LIVE PIPELINE DEMO _ USHOU _ EAST ASIA TRADING",
            "sender": "export@eastasiatrading.com",
            "vessel": "MSC ISABELLA",
            "voyage": "V.2026W",
            "company": "East Asia Trading",
            "si_text": si_content,
            "bl_text": bl_content
        }

        # Verify anonymous request is rejected
        res_anon = self.client.post("/api/upload", json=upload_payload)
        self.assertEqual(res_anon.status_code, 401, "Anonymous upload must be rejected with 401")

        # Authenticated upload
        res_upload = self.client.post("/api/upload", json=upload_payload, headers=self.auth_headers)
        self.assertEqual(res_upload.status_code, 200, f"Upload failed: {res_upload.text}")
        data_upload = res_upload.json()

        self.assertEqual(data_upload.get("status"), "success")
        email_id = data_upload.get("email_id")
        job_id = data_upload.get("job_id")
        self.assertIsNotNone(email_id)
        self.assertIsNotNone(job_id)
        self.created_email_ids.append(email_id)

        # Verify durable job exists
        res_job = self.client.get(f"/api/jobs/{job_id}", headers=self.auth_headers)
        self.assertEqual(res_job.status_code, 200)
        self.assertEqual(res_job.json().get("status"), "completed")

        # ── 2. PROCESS (Real Pipeline Validation) ───────────────────────────
        classification = data_upload.get("classification") or {}
        self.assertEqual(classification.get("category"), "BL_COMPARISON")
        self.assertTrue(classification.get("is_comparison_request"))

        verification = data_upload.get("verification") or {}
        # Container count 3 in SI vs 4 in BL must trigger discrepancy
        self.assertIn(verification.get("status"), ["MISMATCH", "MISMATCH_DETECTED", "NEEDS_REVIEW"])
        defect_fields = verification.get("defect_fields") or []
        self.assertIn("container_count", defect_fields, f"Expected container_count in defects: {defect_fields}")

        # Verify the newly uploaded email appears in GET /api/emails
        res_emails = self.client.get("/api/emails")
        self.assertEqual(res_emails.status_code, 200)
        emails_list = res_emails.json()
        matching_emails = [e for e in emails_list if e.get("id") == email_id]
        self.assertEqual(len(matching_emails), 1, f"Uploaded email {email_id} not found in /api/emails inbox feed")

        # Verify detail endpoint returns complete verification
        res_detail = self.client.get(f"/api/emails/{email_id}")
        self.assertEqual(res_detail.status_code, 200)
        detail_data = res_detail.json()
        self.assertEqual(detail_data.get("email", {}).get("id"), email_id)
        self.assertEqual(detail_data.get("verification", {}).get("si_extracted", {}).get("container_count"), 3)
        self.assertEqual(detail_data.get("verification", {}).get("bl_extracted", {}).get("container_count"), 4)

        # ── 3. CORRECT (Reviewer Correction) ─────────────────────────────────
        override_payload = {
            "email_id": email_id,
            "reviewer_name": "Pohyi Chong",
            "timestamp": "2026-09-24T12:00:00Z",
            "si_overrides": {},
            "bl_overrides": {"container_count": 3},
            "corrections": [
                {
                    "field": "container_count",
                    "original_ai_value": "4",
                    "corrected_value": "3",
                    "flagged_by": "AI comparison",
                    "linked_event_id": f"{email_id}:ai-mismatch"
                }
            ]
        }

        # Verify anonymous override is rejected
        res_override_anon = self.client.post("/api/override", json=override_payload)
        self.assertEqual(res_override_anon.status_code, 401, "Anonymous override must be rejected with 401")

        # Authenticated override
        res_override = self.client.post("/api/override", json=override_payload, headers=self.auth_headers)
        self.assertEqual(res_override.status_code, 200, f"Override failed: {res_override.text}")
        override_data = res_override.json()
        self.assertEqual(override_data.get("status"), "success")
        updated_verif = override_data.get("updated_verification") or {}
        self.assertIn(updated_verif.get("status"), ["OK", "NO_MISMATCH_DETECTED"])
        self.assertNotIn("container_count", updated_verif.get("defect_fields") or [])

        # ── 4. RELOAD (Simulate complete restart & cache wipe) ────────────────
        import backend.main as main_mod

        # Wipe in-memory caches and overrides completely
        main_mod.HUMAN_OVERRIDES.clear()
        main_mod.PROCESSED_SUMMARY_CACHE = None

        # Re-hydrate state from persistent storage file exactly like startup
        persisted = load_persisted_overrides()
        main_mod.HUMAN_OVERRIDES.update(persisted)
        loader.load_inbox(force_reload=True)

        # ── 5. PERSISTED (Verify corrections survive reload) ─────────────────
        # Check /api/overrides/{email_id}
        res_check_override = self.client.get(f"/api/overrides/{email_id}", headers=self.auth_headers)
        self.assertEqual(res_check_override.status_code, 200)
        saved_override = res_check_override.json()
        self.assertEqual(saved_override.get("bl_overrides", {}).get("container_count"), 3)
        self.assertEqual(saved_override.get("reviewer_name"), "Pohyi Chong")

        # Check detail endpoint reflects the persisted correction
        res_reloaded_detail = self.client.get(f"/api/emails/{email_id}")
        self.assertEqual(res_reloaded_detail.status_code, 200)
        reloaded_data = res_reloaded_detail.json()

        self.assertIsNotNone(reloaded_data.get("overrides"), "Overrides must be present after reload")
        self.assertEqual(reloaded_data["overrides"]["bl_overrides"].get("container_count"), 3)
        self.assertEqual(reloaded_data["verification"]["bl_extracted"].get("container_count"), 3)
        self.assertIn(reloaded_data["verification"]["status"], ["OK", "NO_MISMATCH_DETECTED"])

        # Check raw disk file contains the entry
        self.assertTrue(os.path.exists(OVERRIDES_FILE))
        with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertIn(email_id, disk_data)
        self.assertEqual(disk_data[email_id]["bl_overrides"]["container_count"], 3)

if __name__ == "__main__":
    unittest.main()
