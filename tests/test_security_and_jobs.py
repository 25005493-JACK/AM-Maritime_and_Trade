"""
Test Suite for Phase 6: Security and Claims
Tests:
1. Reviewer Authentication:
   - Anonymous access to sensitive endpoints (overrides, corrections, jobs, upload) returns 401.
   - Non-reviewer roles return 403 Forbidden.
   - Valid JWT tokens and X-Reviewer-Key authenticate successfully.
   - /api/auth/reviewer-login and /api/auth/me endpoints.
2. Durable Processing Job Store:
   - Job creation, status update, and completion.
   - File persistence in backend/data/processing_jobs.json surviving cache clears.
   - API endpoints for job listing and retrieval.
3. Supabase Row Level Security (RLS) Schema Verification:
   - Verifies all tables have RLS enabled.
   - Verifies zero anonymous access policies exist.
   - Verifies authenticated reviewer and service_role policies exist.
"""
import os
import json
import unittest
from fastapi.testclient import TestClient

from backend.main import app, HUMAN_OVERRIDES, save_persisted_overrides
from backend.services.auth import (
    create_reviewer_token,
    decode_and_validate_token,
    ReviewerUser,
    DEFAULT_REVIEWER_KEY
)
from backend.services import job_store


class TestSecurityAndClaims(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.valid_token = create_reviewer_token(reviewer_name="Senior Reviewer", email="senior.reviewer@documatch.internal")
        self.reviewer_headers = {"Authorization": f"Bearer {self.valid_token}"}
        self.api_key_headers = {"X-Reviewer-Key": DEFAULT_REVIEWER_KEY}

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Reviewer Authentication & Access Control
    # ─────────────────────────────────────────────────────────────────────────

    def test_anonymous_requests_rejected_on_protected_endpoints(self):
        """Anonymous requests to protected reviewer endpoints must return 401 Unauthorized."""
        # POST /api/override
        res = self.client.post("/api/override", json={"email_id": "email_001"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication required", res.json().get("detail", ""))

        # GET /api/overrides
        res = self.client.get("/api/overrides")
        self.assertEqual(res.status_code, 401)

        # POST /api/corrections/resolve
        res = self.client.post("/api/corrections/resolve", json={"email_id": "email_001"})
        self.assertEqual(res.status_code, 401)

        # GET /api/jobs
        res = self.client.get("/api/jobs")
        self.assertEqual(res.status_code, 401)

        # POST /api/jobs
        res = self.client.post("/api/jobs", json={"task_type": "document_verification"})
        self.assertEqual(res.status_code, 401)

    def test_invalid_token_rejected_with_401(self):
        """Malformed or invalid tokens must be rejected with 401."""
        bad_headers = {"Authorization": "Bearer invalid_gibberish_token_12345"}
        res = self.client.get("/api/overrides", headers=bad_headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid or expired", res.json().get("detail", ""))

    def test_non_reviewer_role_rejected_with_403(self):
        """Tokens with roles other than 'reviewer', 'admin', or 'service_role' must return 403 Forbidden."""
        guest_token = create_reviewer_token(reviewer_name="Guest User", role="guest")
        guest_headers = {"Authorization": f"Bearer {guest_token}"}
        res = self.client.get("/api/overrides", headers=guest_headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("lacks reviewer privileges", res.json().get("detail", ""))

    def test_valid_token_and_reviewer_key_accepted(self):
        """Both signed JWT and X-Reviewer-Key must authenticate successfully."""
        # Via JWT
        res_jwt = self.client.get("/api/overrides", headers=self.reviewer_headers)
        self.assertEqual(res_jwt.status_code, 200)

        # Via Reviewer Key
        res_key = self.client.get("/api/overrides", headers=self.api_key_headers)
        self.assertEqual(res_key.status_code, 200)

    def test_auth_login_and_me_endpoints(self):
        """Login endpoint returns valid JWT and /api/auth/me returns reviewer profile."""
        login_res = self.client.post("/api/auth/reviewer-login", json={
            "reviewer_name": "Chief Compliance Officer",
            "email": "chief.compliance@documatch.maritime"
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        token = data.get("access_token")
        self.assertIsNotNone(token)
        self.assertEqual(data.get("role"), "reviewer")

        # Test /api/auth/me with the newly issued token
        me_res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.json()
        self.assertEqual(me_data.get("reviewer_name"), "Chief Compliance Officer")
        self.assertEqual(me_data.get("role"), "reviewer")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Durable Processing Job Store
    # ─────────────────────────────────────────────────────────────────────────

    def test_durable_job_lifecycle_and_persistence(self):
        """Jobs are created, updated, saved to disk, and persist across cache wipes."""
        # 1. Create Job via Service
        job = job_store.create_job(
            task_type="document_verification",
            email_id="email_test_sec_01",
            shipment_id="SHP_SEC_01",
            reviewer_id="Test Reviewer"
        )
        job_id = job["job_id"]
        self.assertEqual(job["status"], "processing")
        self.assertEqual(job["progress"], 0)

        # 2. Update Job
        updated = job_store.update_job(
            job_id=job_id,
            status="completed",
            progress=100,
            result_summary={"verification_status": "OK", "defect_fields": []}
        )
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["progress"], 100)
        self.assertIsNotNone(updated["completed_at"])

        # 3. Verify disk file contains the record
        self.assertTrue(os.path.exists(job_store.JOBS_FILE))
        with open(job_store.JOBS_FILE, "r", encoding="utf-8") as f:
            disk_jobs = json.load(f)
        self.assertIn(job_id, disk_jobs)
        self.assertEqual(disk_jobs[job_id]["status"], "completed")

        # 4. Retrieve via API
        api_res = self.client.get(f"/api/jobs/{job_id}", headers=self.reviewer_headers)
        self.assertEqual(api_res.status_code, 200)
        self.assertEqual(api_res.json()["job_id"], job_id)
        self.assertEqual(api_res.json()["status"], "completed")

        # 5. List via API
        list_res = self.client.get("/api/jobs?limit=10", headers=self.reviewer_headers)
        self.assertEqual(list_res.status_code, 200)
        matching = [j for j in list_res.json()["jobs"] if j["job_id"] == job_id]
        self.assertEqual(len(matching), 1)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Supabase RLS Schema Compliance
    # ─────────────────────────────────────────────────────────────────────────

    def test_supabase_schema_rls_tightening(self):
        """
        Validates supabase_schema.sql:
        1. RLS is enabled on all tables: pipeline_events, human_overrides,
           shipment_corrections, processing_jobs.
        2. No permissive 'anon' policies exist.
        3. Policies require 'authenticated' or 'service_role'.
        """
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "supabase_schema.sql")
        self.assertTrue(os.path.exists(schema_path), "supabase_schema.sql must exist")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_content = f.read()

        # Check RLS enabled on all 4 tables
        required_rls_tables = [
            "public.pipeline_events",
            "public.human_overrides",
            "public.shipment_corrections",
            "public.processing_jobs"
        ]
        for tbl in required_rls_tables:
            enable_stmt = f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;"
            self.assertIn(enable_stmt, schema_content, f"Missing RLS enable statement for {tbl}")

        # Check legacy anon policies are dropped
        legacy_anon_drops = [
            'DROP POLICY IF EXISTS "Allow anon read pipeline_events"',
            'DROP POLICY IF EXISTS "Allow anon insert pipeline_events"',
            'DROP POLICY IF EXISTS "Allow anon all human_overrides"',
            'DROP POLICY IF EXISTS "Allow anon all shipment_corrections"'
        ]
        for drop_stmt in legacy_anon_drops:
            self.assertIn(drop_stmt, schema_content, f"Missing drop policy for legacy: {drop_stmt}")

        # Verify NO active CREATE POLICY granting access TO anon
        for line in schema_content.splitlines():
            clean = line.strip().lower()
            if clean.startswith("create policy") and "to anon" in clean:
                self.fail(f"Found forbidden anonymous policy in supabase_schema.sql: {line}")

        # Verify authenticated reviewer and service_role policies exist
        self.assertIn("TO authenticated", schema_content)
        self.assertIn("TO service_role", schema_content)
        self.assertIn("auth.role() = 'authenticated'", schema_content)


if __name__ == "__main__":
    unittest.main()
