"""
Integration test for Phase 3 Live End-to-End Demo:
Upload new document pair -> Process through real pipeline -> Apply reviewer correction -> Reload server -> Verify persistence.
"""
import os
import json
import unittest
from fastapi.testclient import TestClient

from backend.main import app, HUMAN_OVERRIDES, startup_sync_overrides, DATA_DIR, OVERRIDES_FILE
from backend.services.auth import DEFAULT_REVIEWER_KEY
from backend.services.dataset_loader import loader

class TestLiveEndToEndWorkflow(unittest.TestCase):
    def setUp(self):
        self.test_email_id = "upload_test_live_workflow_999"
        self.test_uploads_file = os.path.join(DATA_DIR, "uploaded_emails.json")
        self.test_si_file = os.path.join(DATA_DIR, "uploads", f"{self.test_email_id}_si.txt")
        self.test_bl_file = os.path.join(DATA_DIR, "uploads", f"{self.test_email_id}_bl.txt")
        self.tearDown()
        self.client = TestClient(app)
        self.auth_headers = {"X-Reviewer-Key": DEFAULT_REVIEWER_KEY}

    def tearDown(self):
        # Clean up test artifacts
        if os.path.exists(self.test_si_file):
            try:
                os.remove(self.test_si_file)
            except OSError:
                pass
        if os.path.exists(self.test_bl_file):
            try:
                os.remove(self.test_bl_file)
            except OSError:
                pass
        inbox_file = os.path.join(loader.inbox_dir, f"{self.test_email_id}.json")
        if os.path.exists(inbox_file):
            try:
                os.remove(inbox_file)
            except OSError:
                pass
        for f in [f"{self.test_email_id}_SI.txt", f"{self.test_email_id}_BL.txt"]:
            p = os.path.join(loader.attachments_dir, f)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        if os.path.exists(self.test_uploads_file):
            try:
                with open(self.test_uploads_file, "r", encoding="utf-8") as f:
                    uploads = json.load(f)
                uploads = [u for u in uploads if u.get("id") != self.test_email_id]
                with open(self.test_uploads_file, "w", encoding="utf-8") as f:
                    json.dump(uploads, f, indent=2)
            except Exception:
                pass
        # Clean up overrides
        if self.test_email_id in HUMAN_OVERRIDES:
            del HUMAN_OVERRIDES[self.test_email_id]
        if os.path.exists(OVERRIDES_FILE):
            try:
                with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
                    ovs = json.load(f)
                if self.test_email_id in ovs:
                    del ovs[self.test_email_id]
                    with open(OVERRIDES_FILE, "w", encoding="utf-8") as f:
                        json.dump(ovs, f, indent=2)
            except Exception:
                pass
        loader._emails_cache = None

    def test_upload_process_correct_reload_persisted(self):
        si_text = (
            "SHIPPING INSTRUCTIONS\n"
            "Shipper: Oceanic Exports Ltd\n"
            "Consignee: Global Importers LLC\n"
            "Notify Party: Pacific Marine Logistics\n"
            "Port of Loading: Shanghai (CNSHA)\n"
            "Port of Discharge: Rotterdam (NLRTM)\n"
            "Container Count: 5 Units\n"
            "Gross Weight: 24500 KGS\n"
        )
        bl_text = (
            "DRAFT BILL OF LADING\n"
            "Shipper: Oceanic Exports Ltd\n"
            "Consignee: Global Importers LLC\n"
            "Notify Party: Pacific Marine Logistics\n"
            "Port of Loading: Shanghai (CNSHA)\n"
            "Port of Discharge: Rotterdam (NLRTM)\n"
            "Container Count: 4 Units\n"
            "Gross Weight: 24500 KGS\n"
        )

        # 1. Upload new SI + BL pair through the live API
        upload_payload = {
            "email_id": self.test_email_id,
            "si_text": si_text,
            "bl_text": bl_text,
            "vessel": "EVER GLORY",
            "voyage": "V.8801E",
            "company": "Oceanic Exports Ltd",
            "sender": "docs@oceanic-exports.com",
            "recipient": "booking@maritime-line.com",
            "subject": "SI vs Draft BL Verification - EVER GLORY V.8801E"
        }

        upload_res = self.client.post("/api/upload", json=upload_payload, headers=self.auth_headers)
        self.assertEqual(upload_res.status_code, 200, f"Upload failed: {upload_res.text}")
        data = upload_res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["email_id"], self.test_email_id)

        # 2. Verify processed through real pipeline
        self.assertEqual(data["classification"]["category"], "BL_COMPARISON")
        verification = data["verification"]
        self.assertEqual(verification["status"], "MISMATCH", "Expected mismatch due to container count 5 vs 4")
        field_matrix = {row["field_key"]: row for row in verification["field_matrix"]}
        self.assertFalse(field_matrix["container_count"]["is_match"])

        # Verify inbox lists the new upload
        inbox_res = self.client.get("/api/emails")
        self.assertEqual(inbox_res.status_code, 200)
        inbox_ids = [e["id"] for e in inbox_res.json()]
        self.assertIn(self.test_email_id, inbox_ids)

        # Verify detail view
        detail_res = self.client.get(f"/api/emails/{self.test_email_id}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()["verification"]["status"], "MISMATCH")

        # 3. Apply reviewer correction: accept 5 containers
        override_payload = {
            "email_id": self.test_email_id,
            "reviewer_name": "Test Reviewer",
            "bl_overrides": {"container_count": 5},
            "corrections": [
                {
                    "field": "container_count",
                    "original_ai_value": "4",
                    "corrected_value": "5",
                    "flagged_by": "Human Reviewer Verification"
                }
            ]
        }
        override_res = self.client.post("/api/override", json=override_payload, headers=self.auth_headers)
        self.assertEqual(override_res.status_code, 200)
        updated_verification = override_res.json()["updated_verification"]
        self.assertEqual(updated_verification["status"], "OK", "Status should be OK after reviewer resolves discrepancy")

        # Verify the change is reflected in verification endpoint
        verify_res = self.client.get(f"/api/verify/{self.test_email_id}")
        self.assertEqual(verify_res.status_code, 200)
        self.assertEqual(verify_res.json()["status"], "OK")

        # 4. Simulate a complete server restart / reload
        # Clear in-memory state
        HUMAN_OVERRIDES.clear()
        loader._emails_cache = None

        # Call startup routine (reloads from disk)
        startup_sync_overrides()

        # Check in-memory store hydrated from disk
        self.assertIn(self.test_email_id, HUMAN_OVERRIDES, "Override should be restored from data/human_overrides.json")
        self.assertEqual(HUMAN_OVERRIDES[self.test_email_id]["bl_overrides"]["container_count"], 5)

        # 5. Query the restarted app
        reloaded_detail = self.client.get(f"/api/emails/{self.test_email_id}")
        self.assertEqual(reloaded_detail.status_code, 200)
        reloaded_json = reloaded_detail.json()
        self.assertEqual(reloaded_json["verification"]["status"], "OK", "Corrected status must survive reload")
        self.assertEqual(reloaded_json["verification"]["bl_extracted"]["container_count"], 5)

if __name__ == "__main__":
    unittest.main()
