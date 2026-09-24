"""
Supabase Cloud Infrastructure Service
Provides persistence and cloud storage integration for:
- Pipeline events (audit log)
- Human overrides (manual reviewer corrections across restarts)
- DCSA shipment corrections (carrier discrepancy analytics)
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("supabase_service")

_supabase_client = None

def get_supabase_client():
    """Lazy initialize the Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    # Prefer service role key for backend operations if provided; fallback to anon key
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key or "your-project" in supabase_url:
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase Cloud: %s", supabase_url)
        return _supabase_client
    except Exception as e:
        logger.warning(f"Could not initialize Supabase client: {e}")
        return None


def is_supabase_enabled() -> bool:
    """Return True if Supabase credentials are configured and client is available."""
    return get_supabase_client() is not None


def save_pipeline_event(event_data: Dict[str, Any]) -> bool:
    """Insert pipeline event into Supabase pipeline_events table."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        # Sanitize data for Supabase table schema
        payload = {
            "event_id": event_data.get("event_id"),
            "shipment_id": event_data.get("shipment_id"),
            "email_id": event_data.get("email_id"),
            "category": event_data.get("category"),
            "classification_confidence": event_data.get("classification_confidence"),
            "extraction_tier": event_data.get("extraction_tier"),
            "anchor_triage_outcome": event_data.get("anchor_triage_outcome"),
            "anchor_triage_reason": event_data.get("anchor_triage_reason"),
            "comparison_status": event_data.get("comparison_status"),
            "review_reason": str(event_data.get("review_reason") or ""),
            "defect_fields": str(event_data.get("defect_fields") or ""),
            "cache_hit_si": bool(event_data.get("cache_hit_si", False)),
            "cache_hit_bl": bool(event_data.get("cache_hit_bl", False)),
            "processing_time_ms": int(event_data.get("processing_time_ms") or 0),
        }
        client.table("pipeline_events").insert(payload).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save event to Supabase: {e}")
        return False


def save_human_override(email_id: str, override_data: Dict[str, Any]) -> bool:
    """Upsert human override into Supabase human_overrides table."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        payload = {
            "email_id": email_id,
            "reviewer_name": override_data.get("reviewer_name", "Reviewer"),
            "si_overrides": override_data.get("si_overrides", {}),
            "bl_overrides": override_data.get("bl_overrides", {}),
            "corrections": override_data.get("corrections", []),
        }
        client.table("human_overrides").upsert(payload).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to upsert override to Supabase: {e}")
        return False


def fetch_all_human_overrides() -> Dict[str, Dict[str, Any]]:
    """Fetch all human overrides from Supabase to hydrate local state."""
    client = get_supabase_client()
    if not client:
        return {}
    try:
        res = client.table("human_overrides").select("*").execute()
        overrides = {}
        for row in (res.data or []):
            overrides[row["email_id"]] = {
                "reviewer_name": row.get("reviewer_name"),
                "timestamp": row.get("timestamp"),
                "si_overrides": row.get("si_overrides") or {},
                "bl_overrides": row.get("bl_overrides") or {},
                "corrections": row.get("corrections") or [],
            }
        return overrides
    except Exception as e:
        logger.error(f"Failed to fetch overrides from Supabase: {e}")
        return {}


def append_shipment_correction(correction_data: Dict[str, Any]) -> bool:
    """Insert a DCSA correction entry into Supabase shipment_corrections table."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("shipment_corrections").insert(correction_data).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save correction to Supabase: {e}")
        return False


def save_processing_job(job_data: Dict[str, Any]) -> bool:
    """Insert or update a processing job into Supabase processing_jobs table."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        payload = {
            "job_id": job_data.get("job_id"),
            "task_type": job_data.get("task_type", "document_verification"),
            "status": job_data.get("status", "processing"),
            "progress": int(job_data.get("progress", 0)),
            "email_id": job_data.get("email_id"),
            "shipment_id": job_data.get("shipment_id"),
            "reviewer_id": job_data.get("reviewer_id"),
            "created_at": job_data.get("created_at"),
            "updated_at": job_data.get("updated_at"),
            "completed_at": job_data.get("completed_at"),
            "result_summary": job_data.get("result_summary") or {},
            "error_message": job_data.get("error_message"),
        }
        client.table("processing_jobs").upsert(payload).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save job to Supabase: {e}")
        return False


def fetch_processing_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single processing job from Supabase by job_id."""
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("processing_jobs").select("*").eq("job_id", job_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to fetch job from Supabase: {e}")
        return None

