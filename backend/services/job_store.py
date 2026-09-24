"""
Durable Processing Job Store for DocuMatch
Persists document processing job states across server restarts and crashes.
Stores state both in a local durable JSON store (backend/data/processing_jobs.json)
and syncs to Supabase Cloud PostgreSQL (public.processing_jobs) when configured.
"""
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("documatch.job_store")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
JOBS_FILE = os.path.join(DATA_DIR, "processing_jobs.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
        except Exception as e:
            logger.error("Failed to initialize jobs file: %s", e)


def _load_jobs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not read processing_jobs.json: %s", e)
        return {}


def _save_jobs(jobs: Dict[str, Dict[str, Any]]) -> bool:
    _ensure_data_dir()
    tmp_file = f"{JOBS_FILE}.tmp.{uuid.uuid4().hex[:6]}"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, default=str)
        # Atomic replace
        os.replace(tmp_file, JOBS_FILE)
        return True
    except Exception as e:
        logger.error("Failed to write processing_jobs.json: %s", e)
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        return False


def create_job(
    task_type: str = "document_verification",
    email_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates and durably stores a new processing job with status 'queued' or 'processing'.
    """
    now = datetime.now(timezone.utc).isoformat()
    job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    job_record = {
        "job_id": job_id,
        "task_type": task_type,
        "status": "processing",
        "progress": 0,
        "email_id": email_id,
        "shipment_id": shipment_id,
        "reviewer_id": reviewer_id or "system",
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "result_summary": {},
        "error_message": None,
        "metadata": metadata or {}
    }

    jobs = _load_jobs()
    jobs[job_id] = job_record
    _save_jobs(jobs)

    # Sync to Supabase if configured
    try:
        from backend.services import supabase_service
        if supabase_service.is_supabase_enabled():
            client = supabase_service.get_supabase_client()
            if client:
                client.table("processing_jobs").insert({
                    "job_id": job_id,
                    "task_type": task_type,
                    "status": "processing",
                    "progress": 0,
                    "email_id": email_id,
                    "shipment_id": shipment_id,
                    "reviewer_id": reviewer_id,
                    "created_at": now,
                    "updated_at": now,
                    "result_summary": {},
                    "error_message": None
                }).execute()
    except Exception as e:
        logger.debug("Supabase job sync notice: %s", e)

    return job_record


def update_job(
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    result_summary: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Updates the durable state of an existing processing job.
    """
    jobs = _load_jobs()
    if job_id not in jobs:
        return None

    now = datetime.now(timezone.utc).isoformat()
    job = jobs[job_id]
    job["updated_at"] = now

    if status is not None:
        job["status"] = status
        if status in ("completed", "failed"):
            job["completed_at"] = now
            if status == "completed" and progress is None:
                job["progress"] = 100

    if progress is not None:
        job["progress"] = max(0, min(100, progress))

    if result_summary is not None:
        job["result_summary"] = result_summary

    if error_message is not None:
        job["error_message"] = str(error_message)

    jobs[job_id] = job
    _save_jobs(jobs)

    # Sync to Supabase if configured
    try:
        from backend.services import supabase_service
        if supabase_service.is_supabase_enabled():
            client = supabase_service.get_supabase_client()
            if client:
                payload = {
                    "status": job["status"],
                    "progress": job["progress"],
                    "updated_at": now,
                    "result_summary": job["result_summary"],
                    "error_message": job["error_message"]
                }
                if job.get("completed_at"):
                    payload["completed_at"] = job["completed_at"]
                client.table("processing_jobs").update(payload).eq("job_id", job_id).execute()
    except Exception as e:
        logger.debug("Supabase job update notice: %s", e)

    return job


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a durable job by its job_id.
    """
    jobs = _load_jobs()
    job = jobs.get(job_id)
    if job:
        return job

    # Fallback check from Supabase if not found locally
    try:
        from backend.services import supabase_service
        if supabase_service.is_supabase_enabled():
            client = supabase_service.get_supabase_client()
            if client:
                res = client.table("processing_jobs").select("*").eq("job_id", job_id).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
    except Exception:
        pass

    return None


def list_jobs(limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists durable processing jobs, ordered by created_at descending.
    """
    jobs = _load_jobs()
    all_jobs = list(jobs.values())

    if status:
        all_jobs = [j for j in all_jobs if j.get("status") == status]

    all_jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return all_jobs[:limit]
