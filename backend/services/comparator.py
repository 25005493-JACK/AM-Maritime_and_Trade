import os
import re
import json
import datetime
from typing import Dict, Any, List, Optional
from backend.services.extractor import extractor, extract_attachment, ExtractionResult
from backend.services.port_lookup import port_lookup
from backend.services.dataset_loader import loader

class DocumentComparator:
    """
    Compares extracted SI fields (reference) against draft BL fields.
    Evaluates matches across the 7 required fields:
    - shipper, consignee, notify_party, port_of_loading, port_of_discharge, container_count, gross_weight_kg

    Outputs both the official hackathon submission contract:
    - status: 'OK' | 'MISMATCH' | 'NEEDS_REVIEW'
    - has_defect: bool
    - defect_fields: List[str]
    - review_reason: 'wrong_doc_type' | 'missing_attachment' | 'unreadable' | 'missing_value' | None

    and rich UI matrices for split-screen inspection and human-in-the-loop overrides.
    """

    FIELDS = [
        "shipper",
        "consignee",
        "notify_party",
        "port_of_loading",
        "port_of_discharge",
        "container_count",
        "gross_weight_kg"
    ]

    FIELD_LABELS = {
        "shipper": "Shipper Name & Address",
        "consignee": "Consignee",
        "notify_party": "Notify Party",
        "port_of_loading": "Port of Loading (POL)",
        "port_of_discharge": "Port of Discharge (POD)",
        "container_count": "Container Count",
        "gross_weight_kg": "Gross Weight (kg)"
    }

    def compare_documents(
        self,
        si_text: str,
        bl_text: str,
        overrides: Optional[Dict[str, Any]] = None,
        email_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        has_human_override = bool(overrides)
        # Collect the set of fields explicitly provided by the human reviewer
        overridden_fields = set()
        if has_human_override:
            for field in overrides.get("si_overrides", {}):
                if field in self.FIELDS:
                    overridden_fields.add(field)
            for field in overrides.get("bl_overrides", {}):
                if field in self.FIELDS:
                    overridden_fields.add(field)

        # Pre-Comparison Attachment Gate (Must validate required documents before comparison)
        gate = self._check_pre_comparison_gate(si_text, bl_text, email_metadata)
        if not gate["passed"] and not has_human_override:
            return self._build_needs_review_result(
                review_reason="missing_attachment",
                message=f"Pre-comparison gate failed: Expected 2 documents (SI & draft BL), but received {gate['attachment_count']} attachment(s). Comparison halted to prevent ungrounded decision.",
                recommended_action=gate["operational_response_draft"],
                pre_comparison_gate=gate
            )
        # If gate failed but human override exists, force gate to pass so comparison proceeds
        if not gate["passed"] and has_human_override:
            gate = {**gate, "passed": True, "comparison_possible": True,
                    "escalation_reason": None,
                    "recommended_action": "Human reviewer provided field values; proceeding with override-based comparison."}

        email_id = email_metadata.get("id") or email_metadata.get("email_id") or "" if email_metadata else ""

        # Extract attachments using extract_attachment if email_metadata has file paths
        si_extracted = None
        bl_extracted = None

        if email_metadata:
            for att in email_metadata.get("attachments", []):
                p = att.get("path") if isinstance(att, dict) else str(att)
                fn = att.get("filename", os.path.basename(p)) if isinstance(att, dict) else os.path.basename(p)
                dt = att.get("doc_type", "").upper() if isinstance(att, dict) else ""
                if dt == "SI" or "_si." in fn.lower() or "_si." in p.lower() or fn.lower().endswith("si.txt"):
                    resolved_si = loader.resolve_attachment_path(p)
                    if os.path.exists(resolved_si):
                        si_extracted = extract_attachment(resolved_si, doc_type_hint="SI", email_id=email_id)
                elif dt == "BL" or "_bl." in fn.lower() or "_bl." in p.lower() or fn.lower().endswith("bl.txt"):
                    resolved_bl = loader.resolve_attachment_path(p)
                    if os.path.exists(resolved_bl):
                        bl_extracted = extract_attachment(resolved_bl, doc_type_hint="BL", email_id=email_id)

        if si_extracted is None:
            si_extracted = extractor.extract_fields(si_text, doc_type_hint="SI", email_id=email_id) if si_text.strip() else {f: None for f in self.FIELDS}
        if bl_extracted is None:
            bl_extracted = extractor.extract_fields(bl_text, doc_type_hint="BL", email_id=email_id) if bl_text.strip() else {f: None for f in self.FIELDS}

        # Apply Human-in-the-loop overrides if present
        if has_human_override:
            for field, val in overrides.get("si_overrides", {}).items():
                if field in self.FIELDS:
                    si_extracted[field] = val
                    if hasattr(si_extracted, "missing_fields"):
                        si_extracted.missing_fields = [f for f in si_extracted.missing_fields if f != field]
                    elif isinstance(si_extracted, dict):
                        si_extracted["missing_fields"] = [f for f in si_extracted.get("missing_fields", []) if f != field]
            for field, val in overrides.get("bl_overrides", {}).items():
                if field in self.FIELDS:
                    bl_extracted[field] = val
                    if hasattr(bl_extracted, "missing_fields"):
                        bl_extracted.missing_fields = [f for f in bl_extracted.missing_fields if f != field]
                    elif isinstance(bl_extracted, dict):
                        bl_extracted["missing_fields"] = [f for f in bl_extracted.get("missing_fields", []) if f != field]
            # Clear structural flags when human has reviewed and overridden
            if isinstance(si_extracted, dict):
                si_extracted.pop("is_wrong_doc_type", None)
                si_extracted.pop("is_unreadable", None)
            else:
                si_extracted.is_wrong_doc_type = False
                si_extracted.is_unreadable = False
            if isinstance(bl_extracted, dict):
                bl_extracted.pop("is_wrong_doc_type", None)
                bl_extracted.pop("is_unreadable", None)
            else:
                bl_extracted.is_wrong_doc_type = False
                bl_extracted.is_unreadable = False

        # 1. Check corrupted file
        if (getattr(si_extracted, "reason_code", None) == "corrupted_file" or
            getattr(bl_extracted, "reason_code", None) == "corrupted_file" or
            (isinstance(si_extracted, dict) and si_extracted.get("reason_code") == "corrupted_file") or
            (isinstance(bl_extracted, dict) and bl_extracted.get("reason_code") == "corrupted_file")):
            return self._build_needs_review_result(
                review_reason="corrupted_file",
                message="Attachment is corrupted, damaged, or invalid file format.",
                recommended_action="Escalate to operations supervisor: request re-sent, readable document copy.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 2. Check scanned document (OCR deliberately bypassed)
        if (getattr(si_extracted, "reason_code", None) == "scanned_not_processed" or
            getattr(bl_extracted, "reason_code", None) == "scanned_not_processed" or
            (isinstance(si_extracted, dict) and si_extracted.get("reason_code") == "scanned_not_processed") or
            (isinstance(bl_extracted, dict) and bl_extracted.get("reason_code") == "scanned_not_processed")):
            return self._build_needs_review_result(
                review_reason="scanned_not_processed",
                message="Attachment is a scanned image-only PDF. OCR was not attempted per rules-first policy.",
                recommended_action="Send to Human Review desk to transcribe scanned document.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 3. Check wrong document type
        if si_extracted.get("is_wrong_doc_type") or bl_extracted.get("is_wrong_doc_type"):
            doc_kind = bl_extracted.get("doc_type") if bl_extracted.get("is_wrong_doc_type") else si_extracted.get("doc_type")
            return self._build_needs_review_result(
                review_reason="wrong_doc_type",
                message=f"Wrong document type attached: {doc_kind} was provided instead of required BL/SI.",
                recommended_action=f"Reject document. Request draft Bill of Lading from carrier instead of {doc_kind}.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 4. Check unreadable file (general unreadable text)
        if si_extracted.get("is_unreadable") or bl_extracted.get("is_unreadable"):
            return self._build_needs_review_result(
                review_reason="unreadable",
                message="Attachment text is unreadable or corrupted.",
                recommended_action="Escalate to operations supervisor: request re-sent, readable document copy.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 5. Pre-check before 7-field diff:
        # If <2 of the 7 required fields were resolved at all, short-circuit to wrong_doc_type
        si_resolved_count = sum(1 for f in self.FIELDS if si_extracted.get(f) is not None)
        bl_resolved_count = sum(1 for f in self.FIELDS if bl_extracted.get(f) is not None)
        if (si_resolved_count < 2 or bl_resolved_count < 2) and not has_human_override:
            return self._build_needs_review_result(
                review_reason="wrong_doc_type",
                message=f"Fewer than 2 of the 7 required fields resolved (SI: {si_resolved_count}/7, BL: {bl_resolved_count}/7). Likely wrong document type.",
                recommended_action="Reject document or route to human review desk to inspect document type.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 6. Check unresolved field labels
        if (getattr(si_extracted, "reason_code", None) == "term_unresolved" or
            getattr(bl_extracted, "reason_code", None) == "term_unresolved" or
            (isinstance(si_extracted, dict) and si_extracted.get("reason_code") == "term_unresolved") or
            (isinstance(bl_extracted, dict) and bl_extracted.get("reason_code") == "term_unresolved")) and not has_human_override:
            return self._build_needs_review_result(
                review_reason="term_unresolved",
                message="Attachment contains unrecognized field labels requiring human verification.",
                recommended_action="Surface raw label and value to human review queue; add alias to field bank if verified.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 7. Check missing required values
        si_miss = si_extracted.get("missing_fields", []) if isinstance(si_extracted, dict) else getattr(si_extracted, "missing_fields", [])
        bl_miss = bl_extracted.get("missing_fields", []) if isinstance(bl_extracted, dict) else getattr(bl_extracted, "missing_fields", [])
        missing_fields = set(list(si_miss) + list(bl_miss))
        for f in self.FIELDS:
            if f in overridden_fields:
                missing_fields.discard(f)
                continue
            if si_extracted.get(f) is None or bl_extracted.get(f) is None:
                missing_fields.add(f)

        if missing_fields:
            missing_labels = [self.FIELD_LABELS.get(f, f) for f in sorted(missing_fields)]
            return self._build_needs_review_result(
                review_reason="missing_value",
                message=f"Missing required shipment values for: {', '.join(missing_labels)}.",
                recommended_action="Send to Human Review desk to fill missing values or request revised SI/BL.",
                si_extracted=si_extracted,
                bl_extracted=bl_extracted,
                email_id=email_id
            )

        # 4. Compare all 7 Fields
        matrix = []
        defect_fields = []
        matching_fields = []

        for f in self.FIELDS:
            si_val = si_extracted[f]
            bl_val = bl_extracted[f]

            is_match, formatted_si, formatted_bl = self._compare_single_field(f, si_val, bl_val)

            item = {
                "field_key": f,
                "field_name": self.FIELD_LABELS[f],
                "si_value": formatted_si,
                "bl_value": formatted_bl,
                "is_match": is_match,
                "diff_summary": f"SI: {formatted_si} / BL: {formatted_bl}" if not is_match else "Matched"
            }
            matrix.append(item)

            if is_match:
                matching_fields.append(f)
            else:
                defect_fields.append(f)

        has_defect = len(defect_fields) > 0
        if has_defect:
            status = "MISMATCH"
            diff_str_list = [f"{self.FIELD_LABELS[f]}" for f in defect_fields]
            summary_message = f"Found {len(defect_fields)} field mismatch(es): {', '.join(diff_str_list)}."
            recommended_action = f"Issue discrepancy notice to carrier for {', '.join(diff_str_list)}."
        else:
            status = "OK"
            summary_message = "No mismatch detected."
            recommended_action = "Approve draft BL and confirm with shipper for document release."

        final_res = {
            "status": status,
            "has_defect": has_defect,
            "defect_fields": defect_fields,
            "review_reason": None,
            "summary_message": summary_message,
            "recommended_action": recommended_action,
            "requires_human_review": False,
            "human_review_reasons": [],
            "si_extracted": si_extracted.to_dict() if hasattr(si_extracted, "to_dict") else (si_extracted or {}),
            "bl_extracted": bl_extracted.to_dict() if hasattr(bl_extracted, "to_dict") else (bl_extracted or {}),
            "field_matrix": matrix,
            "mismatched_fields": defect_fields,
            "matching_fields": matching_fields,
            "pre_comparison_gate": gate
        }
        self._save_result_to_flat_file(email_id, final_res)
        return final_res

    def _extract_shipment_ref(self, email_metadata: Optional[Dict[str, Any]]) -> str:
        if not email_metadata:
            return "the shipment"
        body = email_metadata.get("body", "")
        subj = email_metadata.get("subject", "")
        # Check explicit reference in body like 'for 070500263211' or 'for PSGSE8356691'
        m = re.search(r'for\s+([A-Z0-9]+)', body, re.I)
        if m:
            return m.group(1).strip()
        # Check booking / BL number in subject
        m_subj = re.search(r'\b([A-Z]{3,4}[0-9]{6,12}|5[A-Z]{3}-[0-9]{5})\b', subj)
        if m_subj:
            return m_subj.group(1).strip()
        return "the shipment"

    def _check_pre_comparison_gate(
        self,
        si_text: str,
        bl_text: str,
        email_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        raw_atts = email_metadata.get("attachments", []) if email_metadata else []
        att_count = len(raw_atts)

        has_si = bool(si_text and si_text.strip())
        has_bl = bool(bl_text and bl_text.strip())

        # Inspect attachment filenames / metadata to detect SI / BL presence
        for a in raw_atts:
            fname = a if isinstance(a, str) else (a.get("filename") or a.get("path") or "")
            fname_lower = str(fname).lower()
            if "_si." in fname_lower or "si" in fname_lower:
                has_si = True
            if "_bl." in fname_lower or "bl" in fname_lower:
                has_bl = True

        ref_no = self._extract_shipment_ref(email_metadata)
        if email_metadata is None:
            passed = bool(has_si and has_bl)
            att_count = 2 if passed else (1 if (has_si or has_bl) else 0)
        else:
            passed = (att_count >= 2) and has_si and has_bl

        if not passed:
            if not has_si and not has_bl:
                action_draft = f"Action required: Please resend the SI and draft BL for {ref_no}. The attachments were not received with the email."
            elif not has_bl:
                action_draft = f"Action required: Please provide the draft Bill of Lading for {ref_no}. Only the Shipping Instruction was received; the draft BL is missing."
            else:
                action_draft = f"Action required: Please provide the Shipping Instruction (SI) for {ref_no}. Only the draft Bill of Lading was received."

            return {
                "passed": False,
                "email_classification": "BL_COMPARISON",
                "si_attached": has_si,
                "bl_attached": has_bl,
                "attachment_count": att_count,
                "comparison_possible": False,
                "escalation_reason": "MISSING_ATTACHMENT",
                "recommended_action": "Request/re-send documents",
                "operational_response_draft": action_draft,
                "reference_no": ref_no
            }

        return {
            "passed": True,
            "email_classification": "BL_COMPARISON",
            "si_attached": True,
            "bl_attached": True,
            "attachment_count": att_count,
            "comparison_possible": True,
            "escalation_reason": None,
            "recommended_action": "Proceed with automated document verification",
            "operational_response_draft": None,
            "reference_no": ref_no
        }

    def _compare_single_field(self, field_key: str, si_val: Any, bl_val: Any) -> tuple:
        if si_val is None or bl_val is None:
            return (False, str(si_val or "MISSING"), str(bl_val or "MISSING"))

        if field_key == "container_count":
            try:
                si_int = int(si_val)
                bl_int = int(bl_val)
                return (si_int == bl_int, str(si_int), str(bl_int))
            except (ValueError, TypeError):
                return (False, str(si_val), str(bl_val))

        if field_key == "gross_weight_kg":
            try:
                si_float = float(si_val)
                bl_float = float(bl_val)
                is_match = abs(si_float - bl_float) <= 0.5
                return (is_match, f"{si_float:,.2f} kg", f"{bl_float:,.2f} kg")
            except (ValueError, TypeError):
                return (False, str(si_val), str(bl_val))

        # Port comparison using UN/LOCODE resolution
        if field_key in ["port_of_loading", "port_of_discharge"]:
            is_match, port_audit = port_lookup.compare_ports(si_val, bl_val)
            formatted_si = str(si_val)
            formatted_bl = str(bl_val)
            if port_audit.get("si_code") and port_audit.get("bl_code"):
                formatted_si = f"{si_val} [{port_audit['si_code']}]"
                formatted_bl = f"{bl_val} [{port_audit['bl_code']}]"
            return (is_match, formatted_si, formatted_bl)

        # String fields: shipper, consignee, notify_party
        norm_si = self._normalize_str(str(si_val))
        norm_bl = self._normalize_str(str(bl_val))
        is_match = norm_si == norm_bl
        return (is_match, str(si_val), str(bl_val))

    def _normalize_str(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\.,\-\/\\_\(\)\:\;]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _normalize_port(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\.,\-\/\\_\(\)\:\;]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _save_result_to_flat_file(self, email_id: Optional[str], result_data: Dict[str, Any]):
        if not email_id:
            return
        try:
            results_dir = os.path.join("data", "results")
            os.makedirs(results_dir, exist_ok=True)
            out_path = os.path.join(results_dir, f"{email_id}.json")
            record = {
                "email_id": email_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "status": result_data.get("status"),
                "review_reason": result_data.get("review_reason"),
                "has_defect": result_data.get("has_defect", False),
                "defect_fields": result_data.get("defect_fields", []),
                "summary_message": result_data.get("summary_message"),
                "recommended_action": result_data.get("recommended_action"),
                "si_extracted": result_data.get("si_extracted") if isinstance(result_data.get("si_extracted"), dict) else getattr(result_data.get("si_extracted"), "to_dict", lambda: {})(),
                "bl_extracted": result_data.get("bl_extracted") if isinstance(result_data.get("bl_extracted"), dict) else getattr(result_data.get("bl_extracted"), "to_dict", lambda: {})(),
                "field_matrix": result_data.get("field_matrix", [])
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            print(f"Failed to write result to {email_id}.json: {ex}")

    def _build_needs_review_result(
        self,
        review_reason: str,
        message: str,
        recommended_action: str,
        si_extracted: Optional[Any] = None,
        bl_extracted: Optional[Any] = None,
        pre_comparison_gate: Optional[Dict[str, Any]] = None,
        email_id: Optional[str] = None
    ) -> Dict[str, Any]:
        matrix = []
        is_gate_failure = (review_reason == "missing_attachment")
        for f in self.FIELDS:
            si_v = si_extracted.get(f) if si_extracted else None
            bl_v = bl_extracted.get(f) if bl_extracted else None
            diff_label = "Comparison Halted (Missing Documents)" if is_gate_failure else f"Review Required ({review_reason})"
            matrix.append({
                "field_key": f,
                "field_name": self.FIELD_LABELS[f],
                "si_value": str(si_v or "N/A"),
                "bl_value": str(bl_v or "N/A"),
                "is_match": False,
                "diff_summary": diff_label
            })

        si_dict = si_extracted.to_dict() if hasattr(si_extracted, "to_dict") else (si_extracted or {})
        bl_dict = bl_extracted.to_dict() if hasattr(bl_extracted, "to_dict") else (bl_extracted or {})

        res = {
            "status": "NEEDS_REVIEW",
            "has_defect": False,
            "defect_fields": [],
            "review_reason": review_reason,
            "summary_message": f"Human Review Required: {message}",
            "recommended_action": recommended_action,
            "requires_human_review": True,
            "human_review_reasons": [message],
            "si_extracted": si_dict,
            "bl_extracted": bl_dict,
            "field_matrix": matrix,
            "mismatched_fields": [],
            "matching_fields": [],
            "pre_comparison_gate": pre_comparison_gate or {
                "passed": False if is_gate_failure else True,
                "email_classification": "BL_COMPARISON",
                "si_attached": True if not is_gate_failure else False,
                "bl_attached": True if not is_gate_failure else False,
                "comparison_possible": False if is_gate_failure else True,
                "escalation_reason": review_reason if is_gate_failure else None,
                "recommended_action": recommended_action,
                "operational_response_draft": recommended_action if is_gate_failure else None
            }
        }
        self._save_result_to_flat_file(email_id, res)
        return res

comparator = DocumentComparator()
