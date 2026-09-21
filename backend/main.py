import sys
import os
import re
import csv
import io
from pathlib import Path
from typing import Dict, Any, Optional, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.services.dataset_loader import loader
from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator
from backend.services.calendar_service import calendar_service
from backend.services.event_logger import event_logger
from backend.services import dcsa_mapping, correction_flow, field_evidence
from backend.services import reasoning_receipt, red_team
from backend.services.automation import automation
from backend.services.circuit_breaker import circuit_breaker
from backend.services.corrections_log import (
    append_corrections,
    dcsa_field_dispute_counts,
    read_corrections,
)
from backend.services import supabase_service

app = FastAPI(
    title="Intelligent Shipping Document & Inbox Management API",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for manual overrides (pre-seeded with acceptance criteria correction)
HUMAN_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "email_111": {
        "reviewer_name": "Pohyi Chong",
        "timestamp": "2026-01-20T08:35:00Z",
        "si_overrides": {},
        "bl_overrides": {"container_count": 3},
        "corrections": [
            {
                "field": "container_count",
                "original_ai_value": "4",
                "corrected_value": "3",
                "flagged_by": "AI comparison",
                "linked_event_id": "email_111:ai-mismatch"
            }
        ]
    }
}
PROCESSED_SUMMARY_CACHE: Optional[List[Dict[str, Any]]] = None

@app.on_event("startup")
def startup_sync_from_cloud():
    """Hydrate in-memory overrides from Supabase cloud if connected."""
    try:
        if supabase_service.is_supabase_enabled():
            cloud_overrides = supabase_service.fetch_all_human_overrides()
            if cloud_overrides:
                HUMAN_OVERRIDES.update(cloud_overrides)
    except Exception as e:
        print(f"[Supabase] Startup sync notice: {e}")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Maritime Shipping Verification Engine Running",
        "dataset_size": len(loader.load_inbox()),
        "cloud_database": "supabase" if supabase_service.is_supabase_enabled() else "local"
    }

@app.get("/api/supabase/status")
def supabase_status():
    enabled = supabase_service.is_supabase_enabled()
    return {
        "configured": enabled,
        "supabase_url": os.getenv("SUPABASE_URL", "") if enabled else None,
        "message": "Connected to Supabase Cloud Infrastructure" if enabled else "Supabase credentials not configured yet. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
    }

@app.get("/api/emails")
def get_emails(
    search: Optional[str] = Query(None, description="Search by ID, subject, sender, company, or vessel"),
    category: Optional[str] = Query(None, description="Filter by category (BL_COMPARISON, SI_REQUEST, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (OK, MISMATCH, NEEDS_REVIEW)"),
    limit: Optional[int] = Query(None, description="Pagination limit"),
    offset: Optional[int] = Query(0, description="Pagination offset")
):
    global PROCESSED_SUMMARY_CACHE
    emails = loader.load_inbox()

    # Build or retrieve cached processed summary
    if PROCESSED_SUMMARY_CACHE is None or len(PROCESSED_SUMMARY_CACHE) != len(emails):
        summary_list = []
        for email in emails:
            email_id = email["id"]
            class_res = classifier.classify(email)

            verification_summary = None
            if class_res["is_comparison_request"]:
                si_text, bl_text = _get_email_doc_texts(email)
                override = HUMAN_OVERRIDES.get(email_id)
                verification_summary = comparator.compare_documents(
                    si_text, bl_text, overrides=override, email_metadata=email
                )

            summary_list.append({
                "id": email_id,
                "email_id": email_id,
                "sender": email.get("sender"),
                "recipient": email.get("recipient"),
                "subject": email.get("subject"),
                "timestamp": email.get("timestamp"),
                "body": email.get("body"),
                "vessel": email.get("vessel"),
                "voyage": email.get("voyage"),
                "company": email.get("company"),
                "attachments": email.get("attachments", []),
                "has_attachments": len(email.get("attachments", [])) > 0,
                "classification": class_res,
                "verification": verification_summary
            })
        PROCESSED_SUMMARY_CACHE = summary_list

    filtered = PROCESSED_SUMMARY_CACHE

    # Search filter
    if search:
        s_lower = search.lower().strip()
        filtered = [
            e for e in filtered
            if s_lower in e["id"].lower()
            or s_lower in (e.get("subject") or "").lower()
            or s_lower in (e.get("sender") or "").lower()
            or s_lower in (e.get("vessel") or "").lower()
            or s_lower in (e.get("company") or "").lower()
            or s_lower in (e.get("body") or "").lower()
        ]

    # Category filter
    if category and category.upper() != "ALL":
        cat_upper = category.upper().strip()
        filtered = [
            e for e in filtered
            if e.get("classification", {}).get("category") == cat_upper
            or cat_upper in e.get("classification", {}).get("super_category", "").upper()
        ]

    # Status filter
    if status and status.upper() != "ALL":
        stat_upper = status.upper().strip()
        filtered = [
            e for e in filtered
            if e.get("verification") and e["verification"].get("status") == stat_upper
        ]

    # Attach the live automation decision for the current level - this is what
    # flips inbox cards between "Needs You" and "Auto-processed".
    filtered = [
        {**entry, "automation": automation.apply(entry.get("verification"))}
        for entry in filtered
    ]

    total_filtered = len(filtered)
    if limit is not None:
        paginated = filtered[offset : offset + limit]
        return {
            "total": total_filtered,
            "offset": offset,
            "limit": limit,
            "emails": paginated
        }

    # Return array directly for straightforward frontend mapping
    return filtered

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
        verification_detail = comparator.compare_documents(
            si_text, bl_text, overrides=override, email_metadata=email
        )

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
    res = comparator.compare_documents(si_text, bl_text, overrides=override, email_metadata=email)
    return res

@app.post("/api/override")
def apply_human_override(payload: Dict[str, Any] = Body(...)):
    global PROCESSED_SUMMARY_CACHE
    email_id = payload.get("email_id")
    if not email_id:
        raise HTTPException(status_code=400, detail="Missing email_id")

    reviewer = payload.get("reviewer_name") or "Pohyi Chong"
    ts = payload.get("timestamp") or "2026-01-20T08:35:00Z"
    si_overrides = payload.get("si_overrides", {})
    bl_overrides = payload.get("bl_overrides", {})
    corrections = payload.get("corrections", [])

    email = loader.get_email(email_id)
    shipment_id = _derive_shipment_id_from_email(email) if email else email_id

    # Auto-build corrections if not explicitly provided
    if not corrections and email:
        si_text, bl_text = _get_email_doc_texts(email)
        orig_comp = comparator.compare_documents(si_text, bl_text, email_metadata=email)
        for f, v in {**si_overrides, **bl_overrides}.items():
            orig_v = (orig_comp.get("bl_extracted") or {}).get(f) or (orig_comp.get("si_extracted") or {}).get(f) or ""
            corrections.append({
                "field": f,
                "original_ai_value": str(orig_v),
                "corrected_value": str(v),
                "flagged_by": "AI comparison",
                "linked_event_id": f"{email_id}:ai-mismatch"
            })

    HUMAN_OVERRIDES[email_id] = {
        "reviewer_name": reviewer,
        "timestamp": ts,
        "si_overrides": si_overrides,
        "bl_overrides": bl_overrides,
        "corrections": corrections
    }

    # Invalidate cached processed summaries to reflect update
    PROCESSED_SUMMARY_CACHE = None

    si_text, bl_text = _get_email_doc_texts(email) if email else ("", "")
    res = comparator.compare_documents(
        si_text, bl_text, overrides=HUMAN_OVERRIDES[email_id], email_metadata=email
    )

    # Write event log with shipment_id foreign key
    for corr in corrections:
        event_logger.log_timeline_event(
            shipment_id=shipment_id,
            actor="human",
            actor_name=reviewer,
            action_text=f"{reviewer} corrected {corr['field']}: {corr.get('original_ai_value', '')} \u2192 {corr.get('corrected_value', '')}, flagged by AI comparison",
            stage="review",
            email_id=email_id,
            related_field=corr["field"],
            linked_event_id=corr.get("linked_event_id") or f"{email_id}:ai-mismatch",
            metadata=corr
        )

    # Append to data/corrections.csv (append-only flat CSV). The DCSA field
    # column is filled from the mapping catalog so analytics can group
    # corrections by DCSA-standard field.
    try:
        append_corrections([
            {
                "timestamp": ts,
                "email_id": email_id,
                "field": corr.get("field", ""),
                "dcsa_field": dcsa_mapping.dcsa_field_name(corr.get("field", "")) or "",
                "original_value": corr.get("original_ai_value", ""),
                "corrected_value": corr.get("corrected_value", ""),
                "resolution": "human_selected:legacy_override",
                "reviewer": reviewer,
                "evidence_summary": "",
            }
            for corr in corrections
        ])
    except Exception as ex:
        print(f"Failed to append to corrections.csv: {ex}")

    return {"status": "success", "updated_verification": res}


# ─────────────────────────────────────────────────────────────────────────────
# DCSA alignment: mapping catalog, propose-and-confirm corrections, DCSA export
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/dcsa/mapping")
def get_dcsa_mapping():
    """DCSA Bill of Lading field mapping catalog, coverage and provenance."""
    return {
        "standard": dcsa_mapping.DCSA_STANDARD,
        "information_model": dcsa_mapping.DCSA_INFORMATION_MODEL,
        "sources": dcsa_mapping.DCSA_SOURCES,
        "coverage": dcsa_mapping.coverage_report(),
        "mappings": dcsa_mapping.all_mappings(),
    }

@app.get("/api/dcsa/analytics")
def get_dcsa_analytics():
    """Dispute counts grouped by DCSA-standard field (corrections.csv)."""
    rows = dcsa_field_dispute_counts()
    recent = read_corrections()[-10:]
    return {
        "question": "Which DCSA-standard fields cause the most carrier disputes?",
        "standard": dcsa_mapping.DCSA_STANDARD,
        "total_corrections": sum(row["count"] for row in rows),
        "by_dcsa_field": rows,
        "recent_corrections": recent,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Online Self-Learning: Reflexion Episodic Memory & Bayesian Routing Policy
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/routing-policy")
@app.get("/api/routing-policy")
def get_routing_policy_endpoint():
    """Returns all sender_domain rows with their current alpha, beta, and derived mean trust."""
    from backend.services.routing_policy import get_all_policies
    policies = get_all_policies()
    return {
        "count": len(policies),
        "policies": policies,
        "description": "Beta-Bernoulli Thompson Sampling posteriors per sender domain"
    }


@app.get("/api/reflections")
def get_reflections_endpoint(sender: Optional[str] = Query(None, description="Filter by sender domain")):
    """Returns stored Reflexion episodic lessons grouped by sender domain."""
    from backend.services.reflection import get_all_reflections
    reflections = get_all_reflections(sender_domain=sender)
    
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in reflections:
        dom = r.get("sender_domain", "unknown")
        grouped.setdefault(dom, []).append(r)

    return {
        "total": len(reflections),
        "senders_count": len(grouped),
        "reflections": reflections,
        "by_sender": grouped,
    }


@app.get("/api/shipments/{email_id}/corrections")
@app.get("/api/verify/{email_id}/corrections")
def get_conflict_proposals(email_id: str):
    """Side-by-side evidence for conflicting fields.

    Returns proposals only - the endpoint never resolves a conflict, because the
    SI and the draft BL are treated as equal-weight sources until a reviewer
    decides.
    """
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Unknown email {email_id}")
    si_text, bl_text = _get_email_doc_texts(email)
    verification = comparator.compare_documents(
        si_text, bl_text, overrides=HUMAN_OVERRIDES.get(email_id), email_metadata=email
    )
    return correction_flow.build_conflict_proposals(email_id, verification, si_text, bl_text, email)

@app.post("/api/corrections/resolve")
def resolve_conflicts(payload: Dict[str, Any] = Body(...)):
    """Apply explicit human decisions and emit a DCSA-structured resolved record."""
    global PROCESSED_SUMMARY_CACHE
    email_id = (payload.get("email_id") or "").strip()
    if not email_id:
        raise HTTPException(status_code=400, detail="email_id is required")
    decisions = payload.get("decisions") or []
    reviewer = payload.get("reviewer_name") or payload.get("reviewer")

    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Unknown email {email_id}")
    si_text, bl_text = _get_email_doc_texts(email)
    verification = comparator.compare_documents(
        si_text, bl_text, overrides=HUMAN_OVERRIDES.get(email_id), email_metadata=email
    )

    try:
        result = correction_flow.apply_human_resolution(
            email_id,
            decisions,
            reviewer,
            verification=verification,
            si_text=si_text,
            bl_text=bl_text,
            email=email,
            timestamp=payload.get("timestamp"),
        )
    except correction_flow.HumanDecisionRequired as ex:
        # 409: the request tried to let the pipeline decide. That is not allowed.
        raise HTTPException(status_code=409, detail=str(ex))

    shipment_id = _derive_shipment_id_from_email(email)
    for decision in result["resolved_bl"]["review_decisions"]:
        event_logger.log_timeline_event(
            shipment_id=shipment_id,
            actor="human",
            actor_name=result["reviewer"],
            action_text=(
                f"{result['reviewer']} resolved {decision['field_key']} "
                f"({decision['dcsa_field'] or 'internal-only'}) to "
                f"{decision['value']!r} from {decision['origin']}"
            ),
            stage="review",
            email_id=email_id,
            related_field=decision["field_key"],
            linked_event_id=f"{email_id}:ai-mismatch",
            metadata={
                "dcsa_field": decision["dcsa_field"],
                "chosen": decision["chosen"],
                "rejected_values": decision["rejected_values"],
            },
        )

    if supabase_service.is_supabase_enabled():
        try:
            supabase_service.save_human_override(email_id, {
                "reviewer_name": reviewer,
                "corrections": decisions,
            })
        except Exception as ex:
            print(f"[Supabase] Could not save override: {ex}")

    PROCESSED_SUMMARY_CACHE = None
    return result

@app.get("/api/shipments/{email_id}/resolved")
def get_resolved_record(email_id: str, download: bool = Query(False, description="Download as a .dcsa.json file")):
    """The reviewer-confirmed record, structured by DCSA field names."""
    record = correction_flow.load_resolved_record(email_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No resolved record for {email_id}. Resolve the conflicts first (POST /api/corrections/resolve).",
        )
    if download:
        return Response(
            content=correction_flow.export_dcsa_json(record),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={email_id}.dcsa.json"},
        )
    return record


# ─────────────────────────────────────────────────────────────────────────────
# Reasoning receipt, refusal certificate, red team, automation level
# ─────────────────────────────────────────────────────────────────────────────

def _shipment_documents(shipment_id: str) -> List[Dict[str, Any]]:
    """SI/BL documents belonging to a shipment, ready for the receipt builder."""
    documents: List[Dict[str, Any]] = []
    for entry in _ensure_processed_cache():
        email = loader.get_email(entry["id"]) or entry
        if _derive_shipment_id_from_email(email) != shipment_id:
            continue
        if not (entry.get("classification") or {}).get("is_comparison_request"):
            continue
        si_text, bl_text = _get_email_doc_texts(email)
        verification = entry.get("verification") or {}
        validity = verification.get("document_validity") or {}
        scan_notes = []
        if validity.get("doc_type_guess") == "unreadable":
            scan_notes.append("attachment flagged as low-quality/unreadable by the document validity check")
        documents.append({
            "email_id": entry["id"],
            "si_text": si_text,
            "bl_text": bl_text,
            "names": field_evidence.attachment_names(email),
            "email": email,
            "scan_notes": scan_notes,
        })
    return documents

@app.get("/shipments/{shipment_id}/receipt")
@app.get("/api/shipments/{shipment_id}/receipt")
def get_shipment_receipt(shipment_id: str, persist: bool = Query(True, description="Persist rows to DuckDB")):
    """Ordered field-level decision receipt for the shipment's document set."""
    documents = _shipment_documents(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail=f"No comparable documents found for shipment {shipment_id}")
    return reasoning_receipt.build_receipt(
        shipment_id, documents, overrides_by_email=HUMAN_OVERRIDES, persist=persist
    )

@app.get("/api/verify/{email_id}/receipt")
def get_email_receipt(email_id: str, persist: bool = Query(False, description="Persist rows to DuckDB")):
    """Convenience alias: receipt for the shipment the given email belongs to."""
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Unknown email {email_id}")
    shipment_id = _derive_shipment_id_from_email(email)
    documents = _shipment_documents(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail=f"No comparable documents found for email {email_id}")
    return reasoning_receipt.build_receipt(
        shipment_id, documents, overrides_by_email=HUMAN_OVERRIDES, persist=persist
    )

@app.get("/shipments/{shipment_id}/refusal-certificate")
@app.get("/api/shipments/{shipment_id}/refusal-certificate")
def get_refusal_certificate(shipment_id: str):
    """Structured refusal produced when the AI circuit breaker tripped."""
    documents = _shipment_documents(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail=f"No comparable documents found for shipment {shipment_id}")
    receipt = reasoning_receipt.build_receipt(
        shipment_id, documents, overrides_by_email=HUMAN_OVERRIDES, persist=False
    )
    certificate = receipt.get("refusal_certificate")
    if not certificate:
        return {
            "certificate": None,
            "circuit_breaker": receipt.get("circuit_breaker"),
            "note": "Circuit breaker did not trip: no AI field failed validation consecutively.",
        }
    return {"certificate": certificate, "circuit_breaker": receipt.get("circuit_breaker")}

@app.get("/api/red-team/transforms")
@app.get("/red-team/transforms")
def red_team_transforms():
    """The adversarial transforms the demo can rehearse."""
    return {"transforms": red_team.transform_catalog()}

@app.post("/api/shipments/{email_id}/red-team")
@app.post("/shipments/{email_id}/red-team")
def run_red_team(email_id: str, payload: Dict[str, Any] = Body(...)):
    """Apply an adversarial transform and run it through the unchanged pipeline."""
    transform = (payload.get("transform") or "").strip()
    if not transform:
        raise HTTPException(status_code=400, detail="transform is required")
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Unknown email {email_id}")

    si_text, bl_text = _get_email_doc_texts(email)
    override = HUMAN_OVERRIDES.get(email_id)

    # Deliberately NO attachment paths / email id here: the comparator would
    # otherwise re-extract from the original attachments and ignore the mutated
    # text, and it would overwrite the stored result for this email. Subject/body
    # are kept only for the shipment-reference helper.
    pipeline_metadata = {"subject": email.get("subject"), "body": email.get("body")}

    before = comparator.compare_documents(si_text, bl_text, overrides=override, email_metadata=pipeline_metadata)

    try:
        mutated_si, mutated_bl, notes = red_team.apply_transform(si_text, bl_text, transform)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    shipment_id = _derive_shipment_id_from_email(email)
    receipt = reasoning_receipt.build_receipt(
        f"{shipment_id}#redteam:{transform}",
        [{
            "email_id": email_id,
            "si_text": mutated_si,
            "bl_text": mutated_bl,
            "names": field_evidence.attachment_names(email),
            "email": pipeline_metadata,
        }],
        overrides_by_email=HUMAN_OVERRIDES,
        persist=False,
    )
    mutated_verification = comparator.compare_documents(
        mutated_si, mutated_bl, overrides=override, email_metadata=pipeline_metadata
    )
    ai_attempts = receipt["documents"][0]["ai_attempts"] if receipt.get("documents") else []

    return {
        "email_id": email_id,
        "shipment_id": shipment_id,
        "transform": transform,
        "notes": notes,
        "before": {
            "status": before.get("status"),
            "defect_fields": before.get("defect_fields"),
            "review_reason": before.get("review_reason"),
        },
        "after": {
            "status": mutated_verification.get("status"),
            "defect_fields": mutated_verification.get("defect_fields"),
            "review_reason": mutated_verification.get("review_reason"),
            "document_validity": mutated_verification.get("document_validity"),
        },
        "triggered": {
            "ai_invoked": bool(ai_attempts),
            "ai_fields_attempted": [a["field_key"] for a in ai_attempts],
            "ai_accepted": [a["field_key"] for a in ai_attempts if a.get("accepted")],
            "circuit_breaker_tripped": bool(receipt.get("refusal_certificate")),
        },
        "verification": mutated_verification,
        "receipt": receipt,
        "refusal_certificate": receipt.get("refusal_certificate"),
    }

@app.get("/settings/automation-level")
@app.get("/api/settings/automation-level")
def get_automation_level():
    return automation.level_info()

@app.post("/settings/automation-level")
@app.post("/api/settings/automation-level")
def set_automation_level(payload: Dict[str, Any] = Body(...)):
    """Set the session automation level (in-memory; no persistence by design)."""
    raw_level = payload.get("level")
    try:
        level = int(raw_level)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="level must be an integer 0-3")
    try:
        result = automation.set_level(level)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    return {**result, "preview": automation.preview(_ensure_processed_cache(), level)}

@app.get("/settings/automation-level/preview")
@app.get("/api/settings/automation-level/preview")
def preview_automation_level(level: Optional[int] = Query(None, description="0-3; defaults to the current level")):
    """Live metrics for the requested level, computed from the loaded inbox."""
    if level is not None and level not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="level must be 0-3")
    return automation.preview(
        _ensure_processed_cache(), level if level is not None else automation.get_level()
    )

@app.get("/api/review-decisions/export")
def export_review_decisions():
    """Export human correction events as a reviewer audit CSV."""
    decisions = event_logger.get_review_decisions()
    columns = [
        "shipment_id", "email_id", "timestamp", "reviewer_name", "field",
        "original_ai_value", "corrected_value", "flagged_by", "linked_event_id"
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(decisions)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviewer-decisions.csv"}
    )

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
        "spam_count": 0,
        "si_request_count": 0,
        "invoice_query_count": 0,
        "general_count": 0
    }

    for email in emails:
        class_res = classifier.classify(email)
        cat = class_res.get("category")
        vessel_name = email.get("vessel", "Commercial Carrier")
        company_name = email.get("company", "Maritime Shipper")

        if vessel_name not in vessels:
            vessels[vessel_name] = {"total_shipments": 0, "matched": 0, "mismatched": 0, "human_review": 0}
        if company_name not in companies:
            companies[company_name] = {"total_orders": 0, "status": "Active", "last_activity": email.get("timestamp")}

        vessels[vessel_name]["total_shipments"] += 1
        companies[company_name]["total_orders"] += 1

        if cat == "BL_COMPARISON":
            stats["comparison_requests"] += 1
            si_text, bl_text = _get_email_doc_texts(email)
            override = HUMAN_OVERRIDES.get(email["id"])
            verif = comparator.compare_documents(si_text, bl_text, overrides=override, email_metadata=email)

            if verif["status"] == "OK":
                stats["matched_count"] += 1
                vessels[vessel_name]["matched"] += 1
            elif verif["status"] == "MISMATCH":
                stats["mismatch_count"] += 1
                vessels[vessel_name]["mismatched"] += 1
            elif verif["status"] == "NEEDS_REVIEW":
                stats["human_review_count"] += 1
                vessels[vessel_name]["human_review"] += 1
        elif cat == "SPAM":
            stats["spam_count"] += 1
        elif cat == "SI_REQUEST":
            stats["si_request_count"] += 1
        elif cat == "INVOICE_QUERY":
            stats["invoice_query_count"] += 1
        elif cat == "GENERAL":
            stats["general_count"] += 1

    return {
        "summary_stats": stats,
        "vessel_manifests": [{"vessel": k, **v} for k, v in list(vessels.items())[:12]],
        "company_orders": [{"company": k, **v} for k, v in list(companies.items())[:12]]
    }


@app.get("/api/ocr/dashboard")
def get_ocr_dashboard():
    """PDF OCR results and measured agreement with searchable PDF text."""
    from backend.services.ocr_dashboard import build_ocr_dashboard

    return build_ocr_dashboard(loader)

@app.post("/submit")
def submit_evaluation(payload: Dict[str, Any] = Body(...)):
    """Compliant self-evaluation endpoint as per page 4 of specification."""
    score_report = evaluator.evaluate_submission(payload)
    return score_report

@app.get("/emails")
def get_emails_spec():
    """Compliant /emails endpoint as required by loader.py."""
    return loader.load_inbox()

@app.get("/emails/{email_id}")
def get_email_spec(email_id: str):
    """Compliant /emails/{email_id} endpoint as required by loader.py."""
    email = loader.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@app.get("/sample_submission")
def get_sample_submission_spec():
    """Compliant /sample_submission endpoint as required by loader.py."""
    sample_path = os.path.join(loader.data_dir, "sample_submission.json")
    if os.path.exists(sample_path):
        import json
        with open(sample_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return evaluator.process_all_emails()

@app.get("/api/submission.json")
def get_submission_json():
    """Generates and downloads the full submission dictionary formatted identically to sample_submission.json."""
    sub = evaluator.process_all_emails()
    return JSONResponse(
        content=sub,
        headers={"Content-Disposition": "attachment; filename=submission.json"}
    )

@app.get("/api/self-evaluate")
def run_self_evaluate():
    ground_truth_payload = evaluator.process_all_emails()
    score_report = evaluator.evaluate_submission(ground_truth_payload)
    return {
        "payload_generated": ground_truth_payload,
        "score_report": score_report
    }

@app.get("/attachments/{path:path}")
@app.get("/api/attachments/{path:path}")
def get_attachment_file(path: str):
    full_path = loader.resolve_attachment_path(path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Attachment file not found")

    ext = Path(full_path).suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    with open(full_path, "rb") as f:
        data = f.read()
    return Response(content=data, media_type=media_type)

@app.get("/api/calendar")
def get_vessel_calendar(port: Optional[str] = None):
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

@app.post("/api/calendar/google-link")
def create_google_calendar_link(payload: Dict[str, Any] = Body(...)):
    vessel_id = payload.get("vessel_id")
    if not vessel_id:
        raise HTTPException(status_code=400, detail="Missing vessel_id")
    result = calendar_service.create_google_calendar_link(vessel_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result

# ── Shipment ID helpers ─────────────────────────────────────────────────────

_BOOKING_PATTERNS = [
    re.compile(r'\b(5[A-Z]{2,4}-\d+)\b'),
    re.compile(r'\b(BK-\d+)\b'),
    re.compile(r'\b(SI-\d{4}-\d+)\b'),
]

def _derive_shipment_id_from_email(email: Dict[str, Any]) -> str:
    """Returns a stable shipment_id for this email, derived from booking reference."""
    subject = email.get("subject", "")

    # 1. Structured subject: "TYPE _ BOOKING_REF _ PORT _ CONSIGNEE _ VESSEL"
    parts = [p.strip() for p in subject.split(" _ ")]
    if len(parts) >= 2:
        candidate = parts[1].upper()
        if re.match(r'^5[A-Z]{2,4}-\d+$', candidate) or re.match(r'^BK-\d+$', candidate):
            return candidate

    # 2. Regex scan in subject + body
    scan_text = subject + " " + (email.get("body") or "")
    for pat in _BOOKING_PATTERNS:
        m = pat.search(scan_text)
        if m:
            return m.group(1).upper()

    # 3. Vessel + voyage fallback
    vessel = (email.get("vessel") or "").strip()
    voyage = (email.get("voyage") or "").strip()
    if vessel and vessel not in ("Commercial Carrier", "N/A", ""):
        return "VV-" + re.sub(r'[^A-Z0-9]', '_', f"{vessel}_{voyage}".upper())

    # 4. Standalone (no grouping possible)
    return f"STANDALONE-{email.get('id', 'unknown')}"


def _parse_subject_meta(email: Dict[str, Any]) -> Dict[str, str]:
    """Parses display metadata (port, carrier, consignee) from email subject and metadata."""
    subject = email.get("subject", "")
    port = ""
    carrier = ""
    consignee = ""
    booking_ref = ""
    vessel_ref = ""

    # 1. Underscore-delimited format: TYPE _ BOOKING _ PORT _ CONSIGNEE _ VESSEL
    if " _ " in subject:
        parts = [p.strip() for p in subject.split(" _ ")]
        if len(parts) >= 2: booking_ref = parts[1]
        if len(parts) >= 3: port = parts[2].replace("_", ", ")
        if len(parts) >= 4: consignee = parts[3]
        if len(parts) >= 5:
            vessel_ref = parts[4]
            m = re.match(r'^([A-Z]{3,4})', parts[4])
            carrier = m.group(1) if m else parts[4]

    # 2. Dash-delimited format: PREFIX - PORT - CARRIER(REF) - BOOKING - NUMBER - CONSIGNEE - SUFFIX
    elif " - " in subject:
        parts = [p.strip() for p in subject.split(" - ")]
        for i, p in enumerate(parts):
            if re.match(r'^5[A-Z]{2,4}-\d+$', p) or re.match(r'^BK-\d+$', p):
                booking_ref = p
                if i >= 1 and not port:
                    port = parts[1].replace("_", ", ")
                if i >= 2 and not carrier:
                    m = re.match(r'^([A-Za-z]+)', parts[i - 1])
                    if m: carrier = m.group(1).upper()
                if i + 2 < len(parts) and not consignee:
                    consignee = parts[i + 2]
                break

    # 3. Fallbacks from email attributes
    if not carrier:
        v = (email.get("vessel") or "").strip()
        if v and v not in ("Commercial Carrier", "N/A", ""):
            carrier = v
    if not consignee:
        c = (email.get("company") or "").strip()
        if c and c not in ("Maritime Shipper", "N/A", ""):
            consignee = c

    title_parts = [p for p in [port, carrier, consignee] if p]
    title = " · ".join(title_parts) if title_parts else (consignee or port or booking_ref or email.get("id", ""))

    return {
        "port": port,
        "destination": port,
        "carrier": carrier,
        "consignee": consignee,
        "booking_ref": booking_ref,
        "vessel_ref": vessel_ref or carrier,
        "title": title
    }


_DOMAIN_TO_CLIENT: Dict[str, str] = {
    "aprilasia.com":      "April Asia",
    "april.com.my":       "April (Malaysia)",
    "fujitogrp.com":      "Fujito Group",
    "psabdp.com":         "PSA BDP",
    "ifpla.com":          "IFP LA",
    "algurg.ae":          "Al Gurg (UAE)",
    "safqa.co.ke":        "Safqa Kenya",
    "roxcel.at":          "Roxcel (Austria)",
    "vitalsolutions.sg":  "Vital Solutions SG",
    "globaltraders.com":  "Global Traders Inc",
    "pacificlogistics.sg":"Pacific Logistics Ltd",
    "fastfreight.de":     "Fast Freight GmbH",
    "transworld.co.uk":   "Transworld Shipping",
    "oceanic-trade.com":  "Oceanic Trade Corp",
    "maritime-line.com":  "Maritime Line (Internal)",
    "portauthority.sg":   "Port Authority SG",
}

def _sender_to_client(sender: str) -> str:
    if "@" in sender:
        domain = sender.split("@")[-1].lower().strip()
        return _DOMAIN_TO_CLIENT.get(domain, domain.split(".")[0].title())
    return sender or "Unknown"


def _ensure_processed_cache() -> List[Dict[str, Any]]:
    """Ensures PROCESSED_SUMMARY_CACHE is populated and returns it."""
    global PROCESSED_SUMMARY_CACHE
    emails = loader.load_inbox()
    if PROCESSED_SUMMARY_CACHE is not None and len(PROCESSED_SUMMARY_CACHE) == len(emails):
        return PROCESSED_SUMMARY_CACHE

    summary_list = []
    for email in emails:
        email_id = email["id"]
        class_res = classifier.classify(email)
        verification_summary = None
        if class_res["is_comparison_request"]:
            si_text, bl_text = _get_email_doc_texts(email)
            override = HUMAN_OVERRIDES.get(email_id)
            verification_summary = comparator.compare_documents(
                si_text, bl_text, overrides=override, email_metadata=email
            )
        summary_list.append({
            "id": email_id,
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "timestamp": email.get("timestamp"),
            "body": email.get("body"),
            "vessel": email.get("vessel"),
            "voyage": email.get("voyage"),
            "company": email.get("company"),
            "attachments": email.get("attachments", []),
            "classification": class_res,
            "verification": verification_summary,
        })
    PROCESSED_SUMMARY_CACHE = summary_list
    return PROCESSED_SUMMARY_CACHE


def _stage_from_processed(ep: Dict[str, Any]) -> str:
    """Derive stage key from a processed email entry."""
    cat = (ep.get("classification") or {}).get("category", "GENERAL")
    verif = ep.get("verification") or {}
    status = verif.get("status", "")
    review_reason = verif.get("review_reason")
    if cat == "SI_REQUEST":
        return "si"
    elif cat == "BL_COMPARISON":
        if status == "NEEDS_REVIEW" or review_reason:
            return "review"
        elif status == "MISMATCH":
            return "compare"
        return "bl"
    elif cat in ("INVOICE_QUERY", "SPAM"):
        return "sent"
    else:
        subj = (ep.get("subject") or "").lower()
        body = (ep.get("body") or "").lower()
        if "arrival" in subj or "notice" in subj or "schedule" in subj:
            return "sent"
        return "draft"


# ── GET /shipments & GET /api/shipments ──────────────────────────────────────

@app.get("/shipments")
@app.get("/api/shipments")
def get_shipments(
    stage: Optional[str] = Query(None, description="Filter by stage key (si/bl/compare/review/draft/sent)"),
    client: Optional[str] = Query(None, description="Filter by client name"),
    limit: Optional[int] = Query(None, description="Max results (omit for full list)"),
    offset: int = Query(0, description="Pagination offset"),
):
    """Returns one entry per shipment_id, sorted by latest timestamp descending."""
    processed = _ensure_processed_cache()

    # Group processed entries by shipment_id
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for ep in processed:
        raw = loader.get_email(ep["id"]) or ep
        sid = _derive_shipment_id_from_email(raw)
        groups.setdefault(sid, []).append(ep)

    summaries = []
    for sid, eps in groups.items():
        # Skip standalone emails that are purely GENERAL/INVOICE/SPAM with no doc
        has_doc = any(
            (ep.get("classification") or {}).get("category") in ("BL_COMPARISON", "SI_REQUEST")
            for ep in eps
        )
        if not has_doc and sid.startswith("STANDALONE-"):
            continue

        eps_sorted = sorted(eps, key=lambda x: x.get("timestamp") or "")
        latest = eps_sorted[-1]

        # Stage and needs_review from the BL_COMPARISON email (most informative)
        bl_ep = next(
            (ep for ep in reversed(eps_sorted)
             if (ep.get("classification") or {}).get("category") == "BL_COMPARISON"),
            latest,
        )
        stage_key = _stage_from_processed(bl_ep)

        # Check for human overrides on this shipment
        has_override = any(ep["id"] in HUMAN_OVERRIDES for ep in eps)
        has_mismatch = any(
            (ep.get("verification") or {}).get("status") in ("MISMATCH", "NEEDS_REVIEW")
            or (ep.get("verification") or {}).get("has_defect", False)
            for ep in eps
        )
        # Needs review if there's an unresolved mismatch that hasn't been corrected yet
        needs_review = has_mismatch and not has_override

        # Parse display metadata from BL email subject
        raw_bl = loader.get_email(bl_ep["id"]) or bl_ep
        meta = _parse_subject_meta(raw_bl)

        dest = meta.get("destination") or meta.get("port") or ""
        carrier = meta.get("carrier") or ""
        consignee = meta.get("consignee") or ""
        title = meta.get("title") or (f"{dest} · {carrier} · {consignee}".strip(" ·") or sid)

        client_name = _sender_to_client(latest.get("sender") or "")

        summaries.append({
            "shipment_id": sid,
            "title": title,
            "booking_ref": meta.get("booking_ref") or sid,
            "vessel_ref": meta.get("vessel_ref") or "",
            "port": dest,
            "carrier": carrier,
            "consignee": consignee,
            "destination": dest,
            "latest_stage": stage_key,
            "latest_stage_timestamp": latest.get("timestamp") or "",
            "latest_timestamp": latest.get("timestamp") or "",
            "needs_review": needs_review,
            "client": client_name,
            "event_count": len(eps),
            "automation": automation.apply(bl_ep.get("verification")),
        })

    # Sort: Shipments needing review first, then by latest timestamp descending
    summaries.sort(
        key=lambda x: (1 if x.get("needs_review") else 0, x.get("latest_timestamp") or ""),
        reverse=True
    )

    # Filters
    if stage and stage != "all":
        summaries = [s for s in summaries if s["latest_stage"] == stage]
    if client and client not in ("All", ""):
        summaries = [s for s in summaries if s["client"] == client]

    total = len(summaries)
    if limit is not None:
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "shipments": summaries[offset: offset + limit],
        }

    return summaries


# ── GET /shipments/{shipment_id}/timeline & /api/shipments/{shipment_id}/timeline ─

@app.get("/shipments/{shipment_id}/timeline")
@app.get("/api/shipments/{shipment_id}/timeline")
def get_shipment_timeline(shipment_id: str):
    """Returns ordered history and documents strictly for a single shipment."""
    processed = _ensure_processed_cache()

    # Strictly collect emails belonging to this shipment only
    matched: List[tuple] = []   # (raw_email, processed_entry)
    for ep in processed:
        raw = loader.get_email(ep["id"]) or ep
        if _derive_shipment_id_from_email(raw) == shipment_id:
            matched.append((raw, ep))

    if not matched:
        raise HTTPException(status_code=404, detail=f"Shipment '{shipment_id}' not found")

    matched.sort(key=lambda x: (x[0].get("timestamp") or ""))

    history: List[Dict[str, Any]] = []
    documents: List[Dict[str, Any]] = []
    latest_field_matrix = None
    shipment_stage = "draft"
    shipment_needs_review = False

    for raw_email, ep in matched:
        eid = ep["id"]
        ts = raw_email.get("timestamp", "")
        sender = raw_email.get("sender", "")
        actor_name = _sender_to_client(sender) or sender
        cat = (ep.get("classification") or {}).get("category", "GENERAL")
        verif = ep.get("verification") or {}
        status = verif.get("status", "")
        review_reason = verif.get("review_reason")
        defect_fields = verif.get("defect_fields") or []
        override = HUMAN_OVERRIDES.get(eid)

        meta = _parse_subject_meta(raw_email)
        carrier = meta.get("carrier") or raw_email.get("vessel") or "Carrier"

        # ── 1. Ingestion / Extraction Stage ─────────────────────────────────
        if cat in ("SI_REQUEST", "BL_COMPARISON"):
            history.append({
                "event_id": f"{eid}:si-ingest",
                "actor": "system",
                "actor_name": "SI Ingestion Service",
                "action_text": "Shipping Instruction (SI) ingested and validated (7 key fields extracted).",
                "timestamp": ts,
                "stage": "si",
                "related_field": None,
            })
            shipment_stage = "si"

        # ── 2. AI Drafting Stage ───────────────────────────────────────────
        if cat == "BL_COMPARISON":
            history.append({
                "event_id": f"{eid}:ai-draft",
                "actor": "ai",
                "actor_name": "Drafting Engine",
                "action_text": f"Draft Bill of Lading (BL) generated and aligned with booking ref {shipment_id}.",
                "timestamp": ts,
                "stage": "draft",
                "related_field": None,
            })
            shipment_stage = "bl"

            # ── 3. AI Comparison Stage ─────────────────────────────────────
            if status == "OK":
                history.append({
                    "event_id": f"{eid}:ai-ok",
                    "actor": "ai",
                    "actor_name": "Verification Engine",
                    "action_text": "Comparison complete — all 7 fields match. Document approved for release.",
                    "timestamp": ts,
                    "stage": "bl",
                    "related_field": None,
                })
                shipment_stage = "bl"
            elif status == "MISMATCH":
                diff_summary_text = ""
                if verif.get("field_matrix"):
                    latest_field_matrix = verif["field_matrix"]
                    diff_parts = [
                        f"{r['field_key']}: {r.get('diff_summary', 'diff')}"
                        for r in verif["field_matrix"] if not r.get("is_match")
                    ]
                    if diff_parts:
                        diff_summary_text = f" ({'; '.join(diff_parts)})"

                field_list = ", ".join(defect_fields) if defect_fields else "critical fields"
                primary_field = defect_fields[0] if defect_fields else None
                history.append({
                    "event_id": f"{eid}:ai-mismatch",
                    "actor": "ai",
                    "actor_name": "Verification Engine",
                    "action_text": f"Comparison completed: {field_list} mismatch detected{diff_summary_text}.",
                    "timestamp": ts,
                    "stage": "compare",
                    "related_field": primary_field,
                })
                shipment_stage = "compare"
                shipment_needs_review = True
            elif status in ("NEEDS_REVIEW", "HUMAN_REVIEW_REQUIRED"):
                reason_map = {
                    "missing_attachment": "Required document missing — both SI and BL needed for comparison.",
                    "missing_value": "Critical field values could not be extracted from the document.",
                    "unreadable": "Attachment unreadable — OCR extraction failed. Please re-send.",
                    "wrong_doc_type": "Wrong document type attached — expected SI or BL.",
                }
                reason_text = reason_map.get(review_reason or "", f"Requires human review: {review_reason}")
                history.append({
                    "event_id": f"{eid}:ai-review",
                    "actor": "ai",
                    "actor_name": "Verification Engine",
                    "action_text": reason_text,
                    "timestamp": ts,
                    "stage": "review",
                    "related_field": None,
                })
                shipment_stage = "review"
                shipment_needs_review = True

        elif cat == "INVOICE_QUERY":
            history.append({
                "event_id": f"{eid}:invoice-query",
                "actor": "system",
                "actor_name": "Billing Service",
                "action_text": f"Invoice query received from {actor_name}: {raw_email.get('subject', '')[:70]}",
                "timestamp": ts,
                "stage": "sent",
                "related_field": None,
            })
            shipment_stage = "sent"

        elif cat not in ("SI_REQUEST", "BL_COMPARISON"):  # GENERAL, SPAM
            history.append({
                "event_id": f"{eid}:ops-intake",
                "actor": "system",
                "actor_name": "Operations Intake",
                "action_text": f"Operational message received: {raw_email.get('subject', '')[:70]}",
                "timestamp": ts,
                "stage": "draft",
                "related_field": None,
            })

        # ── 4. Human Correction Stage (Links back to AI action & field) ─────
        if override:
            reviewer = override.get("reviewer_name") or "Pohyi Chong"
            override_ts = override.get("timestamp") or ts

            # Check explicit corrections list first
            corrections = override.get("corrections") or []
            if corrections:
                for corr in corrections:
                    f = corr.get("field")
                    orig_val = corr.get("original_ai_value", "")
                    corr_val = corr.get("corrected_value", "")
                    linked_ai_id = corr.get("linked_event_id") or f"{eid}:ai-mismatch"
                    history.append({
                        "event_id": f"{eid}:human-{f}",
                        "actor": "human",
                        "actor_name": reviewer,
                        "action_text": f"{reviewer} corrected {f}: {orig_val} → {corr_val}, flagged by AI comparison",
                        "timestamp": override_ts,
                        "stage": "review",
                        "related_field": f,
                        "linked_ai_event_id": linked_ai_id,
                    })
            else:
                # Fallback: derive from si_overrides / bl_overrides
                for field, val in (override.get("si_overrides") or {}).items():
                    orig = (verif.get("si_extracted") or {}).get(field, "")
                    history.append({
                        "event_id": f"{eid}:human-si-{field}",
                        "actor": "human",
                        "actor_name": reviewer,
                        "action_text": f"{reviewer} corrected {field}: {orig} → {val}, flagged by AI comparison",
                        "timestamp": override_ts,
                        "stage": "review",
                        "related_field": field,
                        "linked_ai_event_id": f"{eid}:ai-mismatch",
                    })
                for field, val in (override.get("bl_overrides") or {}).items():
                    orig = (verif.get("bl_extracted") or {}).get(field, "")
                    history.append({
                        "event_id": f"{eid}:human-bl-{field}",
                        "actor": "human",
                        "actor_name": reviewer,
                        "action_text": f"{reviewer} corrected {field}: {orig} → {val}, flagged by AI comparison",
                        "timestamp": override_ts,
                        "stage": "review",
                        "related_field": field,
                        "linked_ai_event_id": f"{eid}:ai-mismatch",
                    })

            # Human override resolved the mismatch
            shipment_needs_review = False
            shipment_stage = "sent"

        # ── 5. System Next Action (Sent / Discrepancy Notice / Escalation) ───
        if cat == "BL_COMPARISON":
            if override or status == "OK":
                history.append({
                    "event_id": f"{eid}:sys-sent",
                    "actor": "system",
                    "actor_name": "Release Dispatcher",
                    "action_text": f"Final verified BL documentation approved and dispatched to carrier ({carrier}).",
                    "timestamp": ts,
                    "stage": "sent",
                    "related_field": None,
                })
                shipment_stage = "sent"
            elif status == "MISMATCH":
                primary_field = defect_fields[0] if defect_fields else "container count"
                history.append({
                    "event_id": f"{eid}:sys-notice",
                    "actor": "system",
                    "actor_name": "Notification Service",
                    "action_text": f"Discrepancy notice issued to carrier ({carrier}) regarding {primary_field}.",
                    "timestamp": ts,
                    "stage": "compare",
                    "related_field": primary_field,
                })
            elif status in ("NEEDS_REVIEW", "HUMAN_REVIEW_REQUIRED"):
                history.append({
                    "event_id": f"{eid}:sys-escalate",
                    "actor": "system",
                    "actor_name": "Routing Engine",
                    "action_text": "Escalated to Operations Human Review Queue.",
                    "timestamp": ts,
                    "stage": "review",
                    "related_field": None,
                })

        # ── Documents for this shipment ─────────────────────────────────────
        for att in raw_email.get("attachments", []):
            if isinstance(att, dict):
                fname = att.get("filename", "")
                path = att.get("path", "")
                dtype = att.get("doc_type", "OTHER")
            else:
                path = str(att)
                fname = os.path.basename(path)
                dtype = "SI" if "_si." in fname.lower() else ("BL" if "_bl." in fname.lower() else "OTHER")

            if dtype == "SI":
                doc_status = "verified" if status == "OK" or override else ("pending" if not status else "verified")
            elif dtype == "BL":
                if override or status == "OK": doc_status = "verified"
                elif status == "MISMATCH":     doc_status = "mismatch"
                else:                          doc_status = "pending"
            else:
                doc_status = "pending"

            documents.append({
                "name": fname,
                "type": dtype,
                "status": doc_status,
                "file_url": f"/api/attachments/{path.lstrip('/')}",
                "linked_event_id": f"{eid}:si-ingest" if dtype == "SI" else f"{eid}:ai-draft",
            })

    # Build display title from the most informative email in the shipment
    meta_source = next(
        (raw for raw, ep in matched
         if (ep.get("classification") or {}).get("category") == "BL_COMPARISON"),
        matched[0][0],
    )
    meta = _parse_subject_meta(meta_source)
    dest = meta.get("destination") or meta.get("port") or ""
    carrier = meta.get("carrier") or ""
    consignee = meta.get("consignee") or ""
    title = meta.get("title") or (f"{dest} · {carrier} · {consignee}".strip(" ·") or shipment_id)

    return {
        "shipment_id": shipment_id,
        "title": title,
        "booking_ref": meta.get("booking_ref") or shipment_id,
        "vessel_ref": meta.get("vessel_ref") or "",
        "port": dest,
        "carrier": carrier,
        "consignee": consignee,
        "latest_stage": shipment_stage,
        "needs_review": shipment_needs_review,
        "history": history,
        "documents": documents,
        "field_matrix": latest_field_matrix,
    }


def get_timeline():
    """
    Returns timeline events grouped by client (company), derived from real inbox data.
    Each event maps to one of the 7 timeline stages used in the TimelineWheel component.
    """
    emails = loader.load_inbox()

    # Build processed events (reuse cache if available)
    if PROCESSED_SUMMARY_CACHE is not None and len(PROCESSED_SUMMARY_CACHE) == len(emails):
        processed = PROCESSED_SUMMARY_CACHE
    else:
        processed = []
        for email in emails:
            email_id = email["id"]
            class_res = classifier.classify(email)
            verification_summary = None
            if class_res["is_comparison_request"]:
                si_text, bl_text = _get_email_doc_texts(email)
                override = HUMAN_OVERRIDES.get(email_id)
                verification_summary = comparator.compare_documents(
                    si_text, bl_text, overrides=override, email_metadata=email
                )
            processed.append({
                "id": email_id,
                "sender": email.get("sender"),
                "subject": email.get("subject"),
                "timestamp": email.get("timestamp"),
                "body": email.get("body"),
                "vessel": email.get("vessel"),
                "voyage": email.get("voyage"),
                "company": email.get("company"),
                "attachments": email.get("attachments", []),
                "classification": class_res,
                "verification": verification_summary
            })

    # --- Map each email to a timeline stage and event shape ---
    def _map_to_stage(email_proc: Dict[str, Any]) -> str:
        cat = (email_proc.get("classification") or {}).get("category", "GENERAL")
        verif = email_proc.get("verification") or {}
        status = verif.get("status", "")
        review_reason = verif.get("review_reason")

        if cat == "SI_REQUEST":
            return "si"
        elif cat == "BL_COMPARISON":
            if status == "NEEDS_REVIEW" or review_reason:
                return "review"
            elif status == "MISMATCH":
                return "compare"
            elif status == "OK":
                return "bl"
            else:
                return "bl"
        elif cat == "INVOICE_QUERY":
            return "sent"
        elif cat == "SPAM":
            return "sent"
        else:
            # GENERAL — heuristic mapping based on subject/body keywords
            subj = (email_proc.get("subject") or "").lower()
            body = (email_proc.get("body") or "").lower()
            if "draft" in subj or "draft" in body:
                return "draft"
            elif "arrival" in subj or "notice" in subj or "schedule" in subj:
                return "sent"
            else:
                return "draft"

    def _build_event(email_proc: Dict[str, Any]) -> Dict[str, Any]:
        stage = _map_to_stage(email_proc)
        verif = email_proc.get("verification") or {}
        cat = (email_proc.get("classification") or {}).get("category", "GENERAL")
        review_reason = verif.get("review_reason")
        flag = (
            verif.get("status") in ("MISMATCH", "NEEDS_REVIEW")
            or bool(review_reason)
            or verif.get("has_defect", False)
        )

        # Build field comparison table for compare/bl events
        fields_map = None
        if cat == "BL_COMPARISON" and verif.get("field_matrix"):
            fields_map = {}
            for row in verif["field_matrix"]:
                fields_map[row["field_name"]] = {
                    "si": row.get("si_value", "—"),
                    "bl": row.get("bl_value", "—"),
                    "match": row.get("is_match", True)
                }

        # Build snippet for AI-draft-like events (general operational emails)
        snippet = None
        if stage == "draft" and email_proc.get("body"):
            snippet = (email_proc["body"] or "")[:300].strip()

        # Map review_reason to the expected enum values
        mapped_review_reason = None
        if review_reason in ("missing_attachment", "missing_value"):
            mapped_review_reason = "missing_attachment"
        elif review_reason == "unreadable":
            mapped_review_reason = "unreadable"
        elif review_reason == "wrong_doc_type":
            mapped_review_reason = "wrong_doc_type"

        # Build human-readable detail line
        defect_fields = verif.get("defect_fields") or []
        if defect_fields:
            detail = f"Field mismatch on: {', '.join(defect_fields)}. {verif.get('recommended_action', '')}"
        elif verif.get("summary_message"):
            detail = verif["summary_message"]
        else:
            ui_tag = (email_proc.get("classification") or {}).get("ui_tag", "")
            detail = ui_tag or (email_proc.get("body") or "")[:80]

        return {
            "id": email_proc["id"],
            "type": stage,
            "time": email_proc.get("timestamp", ""),
            "title": email_proc.get("subject", ""),
            "detail": detail,
            "ref": f"{email_proc.get('vessel', '')} {email_proc.get('voyage', '')}".strip() or email_proc["id"],
            "flag": flag,
            "fields": fields_map,
            "reviewReason": mapped_review_reason,
            "snippet": snippet,
            "sender": email_proc.get("sender"),
            "company": email_proc.get("company"),
            "verificationStatus": verif.get("status") if verif else None
        }

    # ── Derive a clean "client" name from sender domain ──────────────────────
    # Known domain → display name mapping drawn from actual inbox data
    KNOWN_DOMAINS: Dict[str, str] = {
        "aprilasia.com":      "April Asia",
        "april.com.my":       "April (Malaysia)",
        "fujitogrp.com":      "Fujito Group",
        "psabdp.com":         "PSA BDP",
        "ifpla.com":          "IFP LA",
        "algurg.ae":          "Al Gurg (UAE)",
        "safqa.co.ke":        "Safqa Kenya",
        "roxcel.at":          "Roxcel (Austria)",
        "vitalsolutions.sg":  "Vital Solutions SG",
        "globaltraders.com":  "Global Traders Inc",
        "pacificlogistics.sg":"Pacific Logistics Ltd",
        "fastfreight.de":     "Fast Freight GmbH",
        "transworld.co.uk":   "Transworld Shipping",
        "oceanic-trade.com":  "Oceanic Trade Corp",
        "portlogistics.com":  "Port Logistics",
        "asiapacific-export.com": "Asia Pacific Exports",
        "maritime-line.com":  "Maritime Line (Internal)",
        "portauthority.sg":   "Port Authority SG",
    }

    def _derive_client(email_proc: Dict[str, Any]) -> str:
        sender = email_proc.get("sender") or ""
        if "@" in sender:
            domain = sender.split("@")[-1].lower().strip()
            if domain in KNOWN_DOMAINS:
                return KNOWN_DOMAINS[domain]
            # Friendly fallback: capitalize the root domain name
            root = domain.split(".")[0] if domain else "unknown"
            return root.title()
        # No sender email — use vessel as grouping key
        vessel = (email_proc.get("vessel") or "").strip()
        return vessel or "Other"

    # Count events per derived client to find top clients
    client_counts: Dict[str, int] = {}
    for ep in processed:
        cl = _derive_client(ep)
        client_counts[cl] = client_counts.get(cl, 0) + 1

    # Keep top-8 clients by volume; lump the rest under "Other"
    TOP_N = 8
    top_clients = set(
        k for k, _ in sorted(client_counts.items(), key=lambda x: -x[1])[:TOP_N]
    )

    # Group events by client
    shipments: Dict[str, Any] = {}
    for ep in processed:
        client = _derive_client(ep)
        if client not in top_clients:
            client = "Other"
        if client not in shipments:
            shipments[client] = {"client": client, "events": []}
        shipments[client]["events"].append(_build_event(ep))

    # Sort clients: top-N by volume first, then "Other" last
    def _sort_key(name: str) -> tuple:
        if name == "Other":
            return (1, 0)
        return (0, -client_counts.get(name, 0))

    sorted_clients = sorted(shipments.keys(), key=_sort_key)

    return {
        "shipments": list(shipments.values()),
        "clients": ["All"] + sorted_clients
    }


def _get_email_doc_texts(email: Dict[str, Any]) -> tuple:
    si_text = ""
    bl_text = ""
    for att in email.get("attachments", []):
        path = att["path"] if isinstance(att, dict) else str(att)
        fname = att.get("filename", os.path.basename(path)) if isinstance(att, dict) else os.path.basename(path)
        dtype = att.get("doc_type", "") if isinstance(att, dict) else ""
        
        if dtype == "SI" or "_si." in fname.lower() or "_si." in path.lower():
            si_text = loader.read_attachment_text(path)
        elif dtype == "BL" or "_bl." in fname.lower() or "_bl." in path.lower():
            bl_text = loader.read_attachment_text(path)
    return (si_text, bl_text)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
