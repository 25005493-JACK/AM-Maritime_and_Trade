from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import os

from backend.services.dataset_loader import loader
from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator
from backend.services.calendar_service import calendar_service

app = FastAPI(
    title="Intelligent Shipping Document & Inbox Management API",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for manual overrides
HUMAN_OVERRIDES: Dict[str, Dict[str, Any]] = {}

@app.get("/")
def read_root():
    return {"status": "online", "message": "Maritime Shipping Verification Engine Running"}

@app.get("/api/emails")
def get_emails():
    emails = loader.load_inbox()
    result = []
    for email in emails:
        email_id = email["id"]
        class_res = classifier.classify(email)

        # Check document comparison status if applicable
        verification_summary = None
        if class_res["is_comparison_request"]:
            si_text, bl_text = _get_email_doc_texts(email)
            override = HUMAN_OVERRIDES.get(email_id)
            verification_summary = comparator.compare_documents(si_text, bl_text, override)

        result.append({
            "id": email_id,
            "sender": email.get("sender"),
            "recipient": email.get("recipient"),
            "subject": email.get("subject"),
            "timestamp": email.get("timestamp"),
            "body": email.get("body"),
            "vessel": email.get("vessel"),
            "voyage": email.get("voyage"),
            "company": email.get("company"),
            "has_attachments": len(email.get("attachments", [])) > 0,
            "classification": class_res,
            "verification": verification_summary
        })
    return result

@app.get("/api/emails/{email_id}")
def get_email_detail(email_id: str):
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    class_res = classifier.classify(email)
    si_text, bl_text = _get_email_doc_texts(email)
    override = HUMAN_OVERRIDES.get(email_id)

    verification_detail = None
    if class_res["is_comparison_request"]:
        verification_detail = comparator.compare_documents(si_text, bl_text, override)

    return {
        "email": email,
        "classification": class_res,
        "si_text": si_text,
        "bl_text": bl_text,
        "verification": verification_detail,
        "overrides": override
    }

@app.get("/api/verify/{email_id}")
def verify_document(email_id: str):
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    si_text, bl_text = _get_email_doc_texts(email)
    override = HUMAN_OVERRIDES.get(email_id)
    res = comparator.compare_documents(si_text, bl_text, override)
    return res

@app.post("/api/override")
def apply_human_override(payload: Dict[str, Any] = Body(...)):
    email_id = payload.get("email_id")
    if not email_id:
        raise HTTPException(status_code=400, detail="Missing email_id")

    HUMAN_OVERRIDES[email_id] = {
        "si_overrides": payload.get("si_overrides", {}),
        "bl_overrides": payload.get("bl_overrides", {})
    }

    email = loader.get_email(email_id)
    si_text, bl_text = _get_email_doc_texts(email) if email else ("", "")
    res = comparator.compare_documents(si_text, bl_text, HUMAN_OVERRIDES[email_id])
    return {"status": "success", "updated_verification": res}

@app.get("/api/analytics")
def get_analytics():
    emails = loader.load_inbox()

    vessels = {}
    companies = {}
    stats = {
        "total_emails": len(emails),
        "comparison_requests": 0,
        "matched_count": 0,
        "mismatch_count": 0,
        "human_review_count": 0,
        "spam_count": 0
    }

    for email in emails:
        class_res = classifier.classify(email)
        vessel_name = email.get("vessel", "Unknown Vessel")
        company_name = email.get("company", "Unknown Company")

        if vessel_name not in vessels:
            vessels[vessel_name] = {"total_shipments": 0, "matched": 0, "mismatched": 0, "human_review": 0}
        if company_name not in companies:
            companies[company_name] = {"total_orders": 0, "status": "Active", "last_activity": email.get("timestamp")}

        vessels[vessel_name]["total_shipments"] += 1
        companies[company_name]["total_orders"] += 1

        if class_res["is_comparison_request"]:
            stats["comparison_requests"] += 1
            si_text, bl_text = _get_email_doc_texts(email)
            override = HUMAN_OVERRIDES.get(email["id"])
            verif = comparator.compare_documents(si_text, bl_text, override)

            if verif["status"] == "NO_MISMATCH_DETECTED":
                stats["matched_count"] += 1
                vessels[vessel_name]["matched"] += 1
            elif verif["status"] == "MISMATCH_DETECTED":
                stats["mismatch_count"] += 1
                vessels[vessel_name]["mismatched"] += 1
            elif verif["status"] == "HUMAN_REVIEW_REQUIRED":
                stats["human_review_count"] += 1
                vessels[vessel_name]["human_review"] += 1
        elif class_res["super_category"] == "Spam / General":
            stats["spam_count"] += 1

    return {
        "summary_stats": stats,
        "vessel_manifests": [{"vessel": k, **v} for k, v in vessels.items()],
        "company_orders": [{"company": k, **v} for k, v in companies.items()]
    }

@app.post("/submit")
def submit_evaluation(payload: Dict[str, Any] = Body(...)):
    """Compliant self-evaluation endpoint as per page 4 of specification."""
    score_report = evaluator.evaluate_submission(payload)
    return score_report

@app.get("/api/calendar")
def get_vessel_calendar(port: Optional[str] = None):
    """
    Returns vessel schedules with destination port filtering support.
    """
    return {
        "schedule": calendar_service.get_calendar(destination_port=port),
        "pending_bookings": calendar_service.pending_auto_bookings,
        "available_ports": [
            "ALL",
            "Rotterdam (NLRTM)",
            "Hamburg (DEHAM)",
            "Los Angeles (USLAX)",
            "Tokyo (JPTYO)",
            "Hong Kong (HKHKG)",
            "Singapore (SGSIN)"
        ]
    }

@app.post("/api/calendar/assign")
def assign_container_slot(payload: Dict[str, Any] = Body(...)):
    res = calendar_service.assign_container(payload)
    return res

@app.post("/api/calendar/auto-book")
def auto_confirm_booking(payload: Dict[str, Any] = Body(...)):
    email_id = payload.get("email_id")
    if not email_id:
        raise HTTPException(status_code=400, detail="Missing email_id")
    res = calendar_service.confirm_auto_booking(email_id)
    return res

@app.get("/api/self-evaluate")
def run_self_evaluate():
    ground_truth_payload = evaluator.process_all_emails()
    score_report = evaluator.evaluate_submission(ground_truth_payload)
    return {
        "payload_generated": ground_truth_payload,
        "score_report": score_report
    }

def _get_email_doc_texts(email: Dict[str, Any]) -> tuple:
    si_text = ""
    bl_text = ""
    for att in email.get("attachments", []):
        if att.get("doc_type") == "SI" or "si" in att.get("filename", "").lower():
            si_text = loader.read_attachment_text(att["path"])
        elif att.get("doc_type") == "BL" or "bl" in att.get("filename", "").lower():
            bl_text = loader.read_attachment_text(att["path"])
    return (si_text, bl_text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
