"""
Reflexion-style Episodic Memory (Feature A).
Reference: Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning"
(NeurIPS 2023, arXiv:2303.11366).

After a failure/correction, the agent writes a natural-language reflection and stores it
in an episodic memory buffer. On future attempts, it retrieves relevant reflections and
injects them into context before acting. No weight updates — all learning happens in context.
"""
import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

from backend.services.event_logger import get_connection, event_logger
from backend.services.ai_agent import provider_status, PROVIDER_ENV, API_KEY_ENV, MODEL_ENV, DEFAULT_MODEL


def extract_domain(sender: Optional[str]) -> str:
    """Extracts a normalized domain from an email address or sender string."""
    if not sender:
        return "unknown"
    s = str(sender).strip().strip("<>\"' ")
    if "@" in s:
        domain = s.split("@")[-1].lower().strip().strip(">").strip()
        return domain
    return s.lower()


def _backup_file_path() -> str:
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(workspace_root, "data", "agent_reflections.json")


def _read_backup_reflections() -> List[Dict[str, Any]]:
    p = _backup_file_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return []
    return []


def _save_backup_reflections(rows: List[Dict[str, Any]]):
    p = _backup_file_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
    except Exception as ex:
        print(f"[Reflection] Failed to write backup: {ex}")


def _call_llm_for_reflection(
    ai_value: str,
    human_value: str,
    field_name: str,
    sender_domain: str,
    doc_type: str,
    context: str = ""
) -> Optional[str]:
    """Calls configured LLM to generate reflection if credentials are present."""
    p_status = provider_status()
    if not p_status.get("is_llm"):
        return None

    model = p_status.get("model") or DEFAULT_MODEL
    prompt = (
        f"You extracted '{ai_value}' for {field_name} in a {doc_type} document from {sender_domain}, "
        f"but the correct value was '{human_value}'. Context excerpt: {context[:200]}.\n"
        "Write a short (1-3 sentence) lesson for your future self about what to watch for next time "
        "you see a similar document from this sender, so you don't repeat this mistake. "
        "Be specific and actionable, not generic."
    )

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 150
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get(API_KEY_ENV, '')}",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
        content = payload["choices"][0]["message"]["content"].strip()
        return content
    except Exception as ex:
        print(f"[Reflection] LLM call failed, falling back to deterministic: {ex}")
        return None


def generate_reflection(correction_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a natural language reflection from a human correction event
    and stores it in agent_reflections.
    """
    ai_val = str(correction_event.get("original_value") or correction_event.get("original_ai_value") or "").strip()
    human_val = str(correction_event.get("corrected_value") or "").strip()
    field = correction_event.get("field") or correction_event.get("field_name") or ""
    sender = correction_event.get("sender") or correction_event.get("sender_domain") or ""
    sender_domain = extract_domain(sender)
    doc_type = correction_event.get("doc_type") or "SI"
    context = correction_event.get("evidence_summary") or correction_event.get("context") or ""
    source_corr_id = correction_event.get("source_correction_id") or correction_event.get("email_id") or ""
    email_id = correction_event.get("email_id") or ""
    shipment_id = correction_event.get("shipment_id") or sender_domain

    # 1. Attempt LLM generation, or use structured actionable template
    reflection_text = _call_llm_for_reflection(
        ai_val, human_val, field, sender_domain, doc_type, context
    )
    if not reflection_text:
        ai_display = f"'{ai_val}'" if ai_val else "empty/unresolved"
        reflection_text = (
            f"When extracting {field} from {sender_domain} {doc_type} documents, look for "
            f"'{human_val}' in the document context instead of accepting {ai_display}. "
            f"Verify keyword delimiters and line boundaries specific to {sender_domain}'s format."
        )

    ref_id = str(uuid.uuid4())
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_dt.isoformat()

    reflection_record = {
        "id": ref_id,
        "sender_domain": sender_domain,
        "doc_type": doc_type,
        "field_name": field if field else None,
        "reflection_text": reflection_text,
        "created_at": now_iso,
        "source_correction_id": source_corr_id,
        "times_retrieved": 0,
    }

    # 2. Persist in DuckDB
    conn = get_connection()
    if conn is not None:
        try:
            conn.execute("""
                INSERT INTO agent_reflections (
                    id, sender_domain, doc_type, field_name, reflection_text,
                    created_at, source_correction_id, times_retrieved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ref_id, sender_domain, doc_type, field if field else None,
                reflection_text, now_dt, source_corr_id, 0
            ])
        except Exception as ex:
            print(f"[Reflection] DuckDB insert failed: {ex}")

    # 3. Persist in JSON backup
    backups = _read_backup_reflections()
    backups.append(reflection_record)
    _save_backup_reflections(backups)

    # 4. Log DuckDB event
    event_logger.log_reflection_created(
        reflection_id=ref_id,
        sender_domain=sender_domain,
        doc_type=doc_type,
        field_name=field if field else None,
        reflection_text=reflection_text,
        source_correction_id=source_corr_id,
        email_id=email_id,
        shipment_id=shipment_id
    )

    return reflection_record


def retrieve_reflections(
    sender_domain: str,
    doc_type: Optional[str] = None,
    field_name: Optional[str] = None,
    email_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Queries agent_reflections matching sender_domain (and doc_type if available),
    ordered by recency, capped at `limit` (default 3).
    Increments times_retrieved on each row returned.
    Logs reflection_retrieved event.
    """
    domain = extract_domain(sender_domain)
    retrieved: List[Dict[str, Any]] = []

    conn = get_connection()
    if conn is not None:
        try:
            query = """
                SELECT id, sender_domain, doc_type, field_name, reflection_text,
                       created_at, source_correction_id, times_retrieved
                FROM agent_reflections
                WHERE sender_domain = ?
            """
            params = [domain]
            if doc_type:
                query += " AND (doc_type = ? OR doc_type IS NULL OR doc_type = '')"
                params.append(doc_type)
            if field_name:
                query += " AND (field_name = ? OR field_name IS NULL OR field_name = '')"
                params.append(field_name)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            for r in rows:
                ref_id = r[0]
                new_count = (r[7] or 0) + 1
                try:
                    conn.execute(
                        "UPDATE agent_reflections SET times_retrieved = ? WHERE id = ?",
                        [new_count, ref_id]
                    )
                except Exception:
                    pass

                item = {
                    "id": ref_id,
                    "sender_domain": r[1],
                    "doc_type": r[2],
                    "field_name": r[3],
                    "reflection_text": r[4],
                    "created_at": str(r[5]),
                    "source_correction_id": r[6],
                    "times_retrieved": new_count,
                }
                retrieved.append(item)
                event_logger.log_reflection_retrieved(
                    reflection_id=ref_id,
                    sender_domain=domain,
                    doc_type=r[2] or doc_type or "SI",
                    field_name=r[3],
                    times_retrieved=new_count,
                    email_id=email_id,
                    shipment_id=shipment_id
                )
        except Exception as ex:
            print(f"[Reflection] DuckDB retrieve query failed: {ex}")

    # Fallback to backup file if DuckDB empty / failed
    if not retrieved:
        all_backups = _read_backup_reflections()
        matched = [
            b for b in all_backups
            if b.get("sender_domain") == domain
            and (not doc_type or b.get("doc_type") in (doc_type, None, ""))
            and (not field_name or b.get("field_name") in (field_name, None, ""))
        ]
        matched.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        for item in matched[:limit]:
            item["times_retrieved"] = item.get("times_retrieved", 0) + 1
            retrieved.append(item)
            event_logger.log_reflection_retrieved(
                reflection_id=item.get("id", ""),
                sender_domain=domain,
                doc_type=item.get("doc_type") or doc_type or "SI",
                field_name=item.get("field_name"),
                times_retrieved=item["times_retrieved"],
                email_id=email_id,
                shipment_id=shipment_id
            )
        _save_backup_reflections(all_backups)

    return retrieved


def get_all_reflections(sender_domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all stored reflections, optionally filtered by sender_domain."""
    results: List[Dict[str, Any]] = []
    conn = get_connection()
    if conn is not None:
        try:
            if sender_domain:
                dom = extract_domain(sender_domain)
                rows = conn.execute("""
                    SELECT id, sender_domain, doc_type, field_name, reflection_text,
                           created_at, source_correction_id, times_retrieved
                    FROM agent_reflections
                    WHERE sender_domain = ?
                    ORDER BY created_at DESC
                """, [dom]).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, sender_domain, doc_type, field_name, reflection_text,
                           created_at, source_correction_id, times_retrieved
                    FROM agent_reflections
                    ORDER BY created_at DESC
                """).fetchall()

            for r in rows:
                results.append({
                    "id": r[0],
                    "sender_domain": r[1],
                    "doc_type": r[2],
                    "field_name": r[3],
                    "reflection_text": r[4],
                    "created_at": str(r[5]),
                    "source_correction_id": r[6],
                    "times_retrieved": r[7] or 0,
                })
            return results
        except Exception as ex:
            print(f"[Reflection] Failed to read from DuckDB: {ex}")

    # Fallback to backup
    all_b = _read_backup_reflections()
    if sender_domain:
        dom = extract_domain(sender_domain)
        return [b for b in all_b if b.get("sender_domain") == dom]
    return sorted(all_b, key=lambda x: x.get("created_at", ""), reverse=True)
