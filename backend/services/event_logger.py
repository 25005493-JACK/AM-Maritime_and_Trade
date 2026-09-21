"""
DuckDB Embedded Event Logger (Tech Desk v4 — Section 5)

Logs every pipeline decision as a row into an embedded DuckDB database.
Provides zero-infrastructure SQL analytics on classification scores,
extraction tiers, confidence, anchor-triage outcomes, diff results,
escalation reasons, cache hits, and processing latency.
"""
import os
import uuid
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Lazy DuckDB import — gracefully degrade if not installed
_duckdb = None
_DB_PATH = None
_conn = None


def _get_connection():
    """Lazy-initialize DuckDB connection."""
    global _duckdb, _DB_PATH, _conn
    if _conn is not None:
        return _conn

    try:
        import duckdb as _duckdb_module
        _duckdb = _duckdb_module
    except ImportError:
        return None

    # Store DB in workspace root
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _DB_PATH = os.path.join(workspace_root, "verification_events.duckdb")

    _conn = _duckdb.connect(_DB_PATH)
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_events (
            event_id         VARCHAR PRIMARY KEY,
            shipment_id      VARCHAR,
            email_id         VARCHAR,
            timestamp        TIMESTAMP,
            category         VARCHAR,
            classification_confidence FLOAT,
            extraction_tier  VARCHAR,
            anchor_triage_outcome VARCHAR,
            anchor_triage_reason VARCHAR,
            comparison_status VARCHAR,
            review_reason    VARCHAR,
            defect_fields    VARCHAR,
            cache_hit_si     BOOLEAN,
            cache_hit_bl     BOOLEAN,
            processing_time_ms INTEGER
        )
    """)
    try:
        _conn.execute("ALTER TABLE pipeline_events ADD COLUMN IF NOT EXISTS shipment_id VARCHAR")
    except Exception:
        pass

    _conn.execute("""
        CREATE TABLE IF NOT EXISTS shipment_timeline_events (
            event_id         VARCHAR PRIMARY KEY,
            shipment_id      VARCHAR NOT NULL,
            email_id         VARCHAR,
            timestamp        TIMESTAMP,
            actor            VARCHAR,
            actor_name       VARCHAR,
            action_text      VARCHAR,
            stage            VARCHAR,
            related_field    VARCHAR,
            linked_event_id  VARCHAR,
            metadata         VARCHAR
        )
    """)

    _conn.execute("""
        CREATE TABLE IF NOT EXISTS field_decisions (
            event_id          VARCHAR,
            shipment_id       VARCHAR,
            email_id          VARCHAR,
            timestamp         TIMESTAMP,
            field_name        VARCHAR,
            dcsa_field        VARCHAR,
            decision_path     VARCHAR,
            rule_matched      VARCHAR,
            ai_fields_read    VARCHAR,
            ai_fields_skipped VARCHAR,
            source_evidence   VARCHAR,
            validators        VARCHAR,
            final_decision_by VARCHAR,
            value             VARCHAR,
            agreement         VARCHAR,
            token_cost        INTEGER,
            latency_ms        INTEGER,
            ai_provider       VARCHAR
        )
    """)

    _conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_reflections (
            id VARCHAR PRIMARY KEY,
            sender_domain VARCHAR,
            doc_type VARCHAR,
            field_name VARCHAR,
            reflection_text VARCHAR,
            created_at TIMESTAMP,
            source_correction_id VARCHAR,
            times_retrieved INTEGER DEFAULT 0
        )
    """)

    _conn.execute("""
        CREATE TABLE IF NOT EXISTS routing_policy (
            sender_domain VARCHAR,
            field_name VARCHAR,
            alpha FLOAT DEFAULT 1.0,
            beta FLOAT DEFAULT 1.0,
            last_updated TIMESTAMP,
            PRIMARY KEY (sender_domain, field_name)
        )
    """)
    return _conn


def get_connection():
    """Public helper to get the initialized DuckDB connection."""
    return _get_connection()


class EventLogger:
    """
    Logs pipeline events to DuckDB and provides SQL-driven analytics queries.
    Degrades gracefully if DuckDB is not installed (logs are silently skipped).
    """

    def log_event(
        self,
        email_id: str,
        category: str,
        shipment_id: Optional[str] = None,
        classification_confidence: float = 0.0,
        extraction_tier: str = "text_parse",
        anchor_triage_outcome: Optional[str] = None,
        anchor_triage_reason: Optional[str] = None,
        comparison_status: Optional[str] = None,
        review_reason: Optional[str] = None,
        defect_fields: Optional[List[str]] = None,
        cache_hit_si: bool = False,
        cache_hit_bl: bool = False,
        processing_time_ms: int = 0
    ) -> Optional[str]:
        """Log a single pipeline event. Returns event_id or None if DuckDB unavailable."""
        conn = _get_connection()
        if conn is None:
            return None

        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        defect_json = json.dumps(defect_fields or [])

        try:
            conn.execute("""
                INSERT INTO pipeline_events (
                    event_id, shipment_id, email_id, timestamp, category,
                    classification_confidence, extraction_tier,
                    anchor_triage_outcome, anchor_triage_reason,
                    comparison_status, review_reason, defect_fields,
                    cache_hit_si, cache_hit_bl, processing_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                event_id, shipment_id, email_id, now, category, classification_confidence,
                extraction_tier, anchor_triage_outcome, anchor_triage_reason,
                comparison_status, review_reason, defect_json,
                cache_hit_si, cache_hit_bl, processing_time_ms
            ])
            return event_id
        except Exception as ex:
            print(f"[EventLogger] Failed to log event for {email_id}: {ex}")
            return None

    def log_intent_document_mismatch(
        self,
        email_id: str,
        shipment_id: Optional[str] = None,
        reason: str = "",
        coverage_ratio: float = 0.0,
        missing_fields: Optional[List[str]] = None,
        doc_type_guess: str = "unknown"
    ) -> Optional[str]:
        """Logs an intent vs document validity mismatch to DuckDB."""
        return self.log_event(
            email_id=email_id,
            shipment_id=shipment_id,
            category="BL_COMPARISON",
            comparison_status="NEEDS_REVIEW",
            review_reason="intent_document_mismatch",
            anchor_triage_outcome="intent_document_mismatch",
            anchor_triage_reason=f"DocType: {doc_type_guess}, Cov: {coverage_ratio:.1%}, Reason: {reason}",
            defect_fields=missing_fields
        )


    def log_timeline_event(
        self,
        shipment_id: str,
        actor: str,
        actor_name: str,
        action_text: str,
        stage: str,
        timestamp: Optional[datetime] = None,
        email_id: Optional[str] = None,
        related_field: Optional[str] = None,
        linked_event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ) -> Optional[str]:
        """Log an event tied specifically to a shipment_id lifecycle."""
        conn = _get_connection()
        if conn is None:
            return None

        eid = event_id or str(uuid.uuid4())
        ts = timestamp or datetime.now(timezone.utc)
        meta_json = json.dumps(metadata or {})

        try:
            conn.execute("""
                INSERT INTO shipment_timeline_events (
                    event_id, shipment_id, email_id, timestamp,
                    actor, actor_name, action_text, stage,
                    related_field, linked_event_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                eid, shipment_id, email_id, ts,
                actor, actor_name, action_text, stage,
                related_field, linked_event_id, meta_json
            ])
            return eid
        except Exception as ex:
            print(f"[EventLogger] Failed to log timeline event for {shipment_id}: {ex}")
            return None

    def log_field_decision(self, event: Dict[str, Any]) -> Optional[str]:
        """Persist one field-level decision (reasoning receipt row).

        Idempotent per email_id: regenerating a receipt replaces that email's rows
        instead of duplicating them.
        """
        conn = _get_connection()
        if conn is None:
            return None

        email_id = event.get("email_id") or ""
        ts = event.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        ts = ts or datetime.now(timezone.utc)
        event_id = event.get("event_id") or str(uuid.uuid4())

        try:
            conn.execute("DELETE FROM field_decisions WHERE email_id = ?", [email_id])
            conn.execute("""
                INSERT INTO field_decisions (
                    event_id, shipment_id, email_id, timestamp, field_name, dcsa_field,
                    decision_path, rule_matched, ai_fields_read, ai_fields_skipped,
                    source_evidence, validators, final_decision_by, value, agreement,
                    token_cost, latency_ms, ai_provider
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                event_id,
                event.get("shipment_id"),
                email_id,
                ts,
                event.get("field_name"),
                event.get("dcsa_field"),
                event.get("decision_path"),
                event.get("rule_matched"),
                json.dumps(event.get("ai_fields_read") or []),
                json.dumps(event.get("ai_fields_skipped") or []),
                json.dumps(event.get("source_evidence")),
                json.dumps(event.get("validators") or []),
                event.get("final_decision_by"),
                event.get("value"),
                event.get("agreement"),
                event.get("token_cost"),
                event.get("latency_ms"),
                event.get("ai_provider"),
            ])
            return event_id
        except Exception as ex:
            print(f"[EventLogger] Failed to log field decision for {email_id}: {ex}")
            return None

    def log_reflection_created(
        self,
        reflection_id: str,
        sender_domain: str,
        doc_type: str,
        field_name: Optional[str],
        reflection_text: str,
        source_correction_id: Optional[str] = None,
        email_id: Optional[str] = None,
        shipment_id: Optional[str] = None
    ) -> Optional[str]:
        """Log a reflection_created event to timeline and DuckDB."""
        return self.log_timeline_event(
            shipment_id=shipment_id or sender_domain,
            actor="agent_memory",
            actor_name="ReflexionEngine",
            action_text=f"Learned reflection for {sender_domain} [{doc_type}]: {reflection_text}",
            stage="learning",
            email_id=email_id,
            related_field=field_name,
            linked_event_id=source_correction_id,
            metadata={
                "event_type": "reflection_created",
                "reflection_id": reflection_id,
                "sender_domain": sender_domain,
                "doc_type": doc_type,
                "field_name": field_name,
                "reflection_text": reflection_text,
                "source_correction_id": source_correction_id
            }
        )

    def log_reflection_retrieved(
        self,
        reflection_id: str,
        sender_domain: str,
        doc_type: str,
        field_name: Optional[str],
        times_retrieved: int,
        email_id: Optional[str] = None,
        shipment_id: Optional[str] = None
    ) -> Optional[str]:
        """Log a reflection_retrieved event to timeline and DuckDB."""
        return self.log_timeline_event(
            shipment_id=shipment_id or sender_domain,
            actor="agent_memory",
            actor_name="ReflexionEngine",
            action_text=f"Retrieved prior reflection for {sender_domain} (retrieval #{times_retrieved})",
            stage="inference",
            email_id=email_id,
            related_field=field_name,
            linked_event_id=reflection_id,
            metadata={
                "event_type": "reflection_retrieved",
                "reflection_id": reflection_id,
                "sender_domain": sender_domain,
                "doc_type": doc_type,
                "field_name": field_name,
                "times_retrieved": times_retrieved
            }
        )

    def log_routing_decision(
        self,
        sender_domain: str,
        field_name: Optional[str],
        decision: str,
        sampled_trust: float,
        mean_trust: float,
        threshold: float,
        email_id: Optional[str] = None,
        shipment_id: Optional[str] = None
    ) -> Optional[str]:
        """Log a routing_decision event to timeline and DuckDB."""
        action = (
            f"Policy routed {field_name or 'document'} to AI ({sampled_trust:.1%} sampled trust > {threshold:.1%} threshold)"
            if decision == "ai" else
            f"Policy favored human-first for {field_name or 'document'} ({sampled_trust:.1%} sampled trust <= {threshold:.1%} threshold)"
        )
        return self.log_timeline_event(
            shipment_id=shipment_id or sender_domain,
            actor="routing_policy",
            actor_name="ThompsonSamplingRouter",
            action_text=action,
            stage="routing",
            email_id=email_id,
            related_field=field_name,
            metadata={
                "event_type": "routing_decision",
                "sender_domain": sender_domain,
                "field_name": field_name,
                "decision": decision,
                "sampled_trust": sampled_trust,
                "mean_trust": mean_trust,
                "threshold": threshold
            }
        )

    def log_routing_policy_updated(
        self,
        sender_domain: str,
        field_name: Optional[str],
        alpha: float,
        beta: float,
        ai_was_correct: bool,
        email_id: Optional[str] = None,
        shipment_id: Optional[str] = None
    ) -> Optional[str]:
        """Log a routing_policy_updated event to timeline and DuckDB."""
        mean_trust = alpha / (alpha + beta)
        outcome = "AI confirmed correct (+alpha)" if ai_was_correct else "AI corrected by human (+beta)"
        return self.log_timeline_event(
            shipment_id=shipment_id or sender_domain,
            actor="routing_policy",
            actor_name="ThompsonSamplingRouter",
            action_text=f"Updated posterior for {sender_domain}: {outcome}. Mean trust now {mean_trust:.1%} (\u03b1={alpha:.1f}, \u03b2={beta:.1f})",
            stage="learning",
            email_id=email_id,
            related_field=field_name,
            metadata={
                "event_type": "routing_policy_updated",
                "sender_domain": sender_domain,
                "field_name": field_name,
                "alpha": alpha,
                "beta": beta,
                "mean_trust": mean_trust,
                "ai_was_correct": ai_was_correct
            }
        )

    def get_field_decisions(self, shipment_id: str) -> List[Dict[str, Any]]:
        """Read persisted reasoning-receipt rows for a shipment."""
        conn = _get_connection()
        if conn is None:
            return []
        try:
            rows = conn.execute("""
                SELECT event_id, shipment_id, email_id, timestamp, field_name, dcsa_field,
                       decision_path, rule_matched, ai_fields_read, ai_fields_skipped,
                       source_evidence, validators, final_decision_by, value, agreement,
                       token_cost, latency_ms, ai_provider
                FROM field_decisions
                WHERE shipment_id = ?
                ORDER BY timestamp ASC, field_name ASC
            """, [shipment_id]).fetchall()
        except Exception as ex:
            print(f"[EventLogger] Failed to fetch field decisions for {shipment_id}: {ex}")
            return []

        cols = [
            "event_id", "shipment_id", "email_id", "timestamp", "field_name", "dcsa_field",
            "decision_path", "rule_matched", "ai_fields_read", "ai_fields_skipped",
            "source_evidence", "validators", "final_decision_by", "value", "agreement",
            "token_cost", "latency_ms", "ai_provider",
        ]
        json_cols = {"ai_fields_read", "ai_fields_skipped", "source_evidence", "validators"}
        events: List[Dict[str, Any]] = []
        for row in rows:
            event: Dict[str, Any] = {}
            for i, col in enumerate(cols):
                value = row[i]
                if col == "timestamp" and value is not None:
                    value = value.isoformat() if hasattr(value, "isoformat") else str(value)
                elif col in json_cols and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                event[col] = value
            events.append(event)
        return events

    def get_shipment_events(self, shipment_id: str) -> List[Dict[str, Any]]:
        """Fetch ordered timeline events for a specific shipment."""
        conn = _get_connection()
        if conn is None:
            return []

        try:
            rows = conn.execute("""
                SELECT event_id, shipment_id, email_id, timestamp,
                       actor, actor_name, action_text, stage,
                       related_field, linked_event_id, metadata
                FROM shipment_timeline_events
                WHERE shipment_id = ?
                ORDER BY timestamp ASC
            """, [shipment_id]).fetchall()

            cols = [
                "event_id", "shipment_id", "email_id", "timestamp",
                "actor", "actor_name", "action_text", "stage",
                "related_field", "linked_event_id", "metadata"
            ]
            events = []
            for r in rows:
                ev = {}
                for i, c in enumerate(cols):
                    v = r[i]
                    if c == "timestamp" and v is not None:
                        v = v.isoformat() if hasattr(v, 'isoformat') else str(v)
                    ev[c] = v
                events.append(ev)
            return events
        except Exception as ex:
            print(f"[EventLogger] Failed to fetch events for shipment {shipment_id}: {ex}")
            return []

    def get_review_decisions(self) -> List[Dict[str, Any]]:
        """Fetch human correction events for reviewer audit exports."""
        conn = _get_connection()
        if conn is None:
            return []

        try:
            rows = conn.execute("""
                SELECT shipment_id, email_id, timestamp, actor_name,
                       related_field, linked_event_id, metadata
                FROM shipment_timeline_events
                WHERE stage = 'review' AND actor = 'human'
                ORDER BY timestamp DESC
            """).fetchall()

            decisions = []
            for shipment_id, email_id, timestamp, actor_name, related_field, linked_event_id, metadata in rows:
                try:
                    details = json.loads(metadata) if isinstance(metadata, str) else (metadata or {})
                except json.JSONDecodeError:
                    details = {}

                decisions.append({
                    "shipment_id": shipment_id,
                    "email_id": email_id,
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp or ""),
                    "reviewer_name": actor_name,
                    "field": related_field,
                    "original_ai_value": details.get("original_ai_value", ""),
                    "corrected_value": details.get("corrected_value", ""),
                    "flagged_by": details.get("flagged_by", "AI comparison"),
                    "linked_event_id": linked_event_id or ""
                })
            return decisions
        except Exception as ex:
            print(f"[EventLogger] Failed to fetch review decisions: {ex}")
            return []

    def get_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch paginated event log."""
        conn = _get_connection()
        if conn is None:
            return []

        try:
            result = conn.execute(
                "SELECT * FROM pipeline_events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                [limit, offset]
            ).fetchall()

            columns = [
                "event_id", "shipment_id", "email_id", "timestamp", "category",
                "classification_confidence", "extraction_tier",
                "anchor_triage_outcome", "anchor_triage_reason",
                "comparison_status", "review_reason", "defect_fields",
                "cache_hit_si", "cache_hit_bl", "processing_time_ms"
            ]

            events = []
            for row in result:
                event = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        val = row[i]
                        if col == "timestamp" and val is not None:
                            val = val.isoformat() if hasattr(val, 'isoformat') else str(val)
                        if col == "defect_fields" and isinstance(val, str):
                            try:
                                val = json.loads(val)
                            except json.JSONDecodeError:
                                val = []
                        event[col] = val
                events.append(event)

            return events
        except Exception as ex:
            print(f"[EventLogger] Failed to fetch events: {ex}")
            return []

    def get_total_events(self) -> int:
        """Get total count of logged events."""
        conn = _get_connection()
        if conn is None:
            return 0
        try:
            result = conn.execute("SELECT COUNT(*) FROM pipeline_events").fetchone()
            return result[0] if result else 0
        except Exception:
            return 0

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Run aggregated SQL queries for the analytics dashboard."""
        conn = _get_connection()
        if conn is None:
            return self._empty_summary()

        try:
            summary = {}

            # Total events
            r = conn.execute("SELECT COUNT(*) FROM pipeline_events").fetchone()
            summary["total_events"] = r[0] if r else 0

            if summary["total_events"] == 0:
                return self._empty_summary()

            # Category distribution
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM pipeline_events GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            summary["category_distribution"] = {r[0]: r[1] for r in rows}

            # Status distribution
            rows = conn.execute(
                "SELECT comparison_status, COUNT(*) as cnt FROM pipeline_events "
                "WHERE comparison_status IS NOT NULL GROUP BY comparison_status ORDER BY cnt DESC"
            ).fetchall()
            summary["status_distribution"] = {r[0]: r[1] for r in rows}

            # Mismatch rate by field
            rows = conn.execute(
                "SELECT defect_fields FROM pipeline_events WHERE comparison_status = 'MISMATCH'"
            ).fetchall()
            field_counts: Dict[str, int] = {}
            for row in rows:
                try:
                    fields = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or [])
                    for f in fields:
                        field_counts[f] = field_counts.get(f, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
            summary["mismatch_by_field"] = dict(sorted(field_counts.items(), key=lambda x: -x[1]))

            # Cache hit rate
            r = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN cache_hit_si THEN 1 ELSE 0 END) as si_hits,
                    SUM(CASE WHEN cache_hit_bl THEN 1 ELSE 0 END) as bl_hits
                FROM pipeline_events
            """).fetchone()
            total = r[0] or 1
            summary["cache_hit_rate"] = {
                "si_hit_rate_pct": round((r[1] or 0) / total * 100, 1),
                "bl_hit_rate_pct": round((r[2] or 0) / total * 100, 1),
                "overall_pct": round(((r[1] or 0) + (r[2] or 0)) / (total * 2) * 100, 1)
            }

            # Average processing time
            r = conn.execute(
                "SELECT AVG(processing_time_ms), MIN(processing_time_ms), MAX(processing_time_ms) "
                "FROM pipeline_events WHERE processing_time_ms > 0"
            ).fetchone()
            summary["processing_time"] = {
                "avg_ms": round(r[0], 1) if r[0] else 0,
                "min_ms": r[1] or 0,
                "max_ms": r[2] or 0
            }

            # Anchor triage stats
            rows = conn.execute(
                "SELECT anchor_triage_outcome, COUNT(*) FROM pipeline_events "
                "WHERE anchor_triage_outcome IS NOT NULL GROUP BY anchor_triage_outcome"
            ).fetchall()
            summary["anchor_triage"] = {r[0]: r[1] for r in rows}

            # Top review reasons
            rows = conn.execute(
                "SELECT review_reason, COUNT(*) as cnt FROM pipeline_events "
                "WHERE review_reason IS NOT NULL GROUP BY review_reason ORDER BY cnt DESC"
            ).fetchall()
            summary["top_review_reasons"] = {r[0]: r[1] for r in rows}

            return summary

        except Exception as ex:
            print(f"[EventLogger] Analytics query failed: {ex}")
            return self._empty_summary()

    def clear_events(self):
        """Clear all logged events (for testing)."""
        conn = _get_connection()
        if conn is None:
            return
        try:
            conn.execute("DELETE FROM pipeline_events")
        except Exception:
            pass

    def _empty_summary(self) -> Dict[str, Any]:
        return {
            "total_events": 0,
            "category_distribution": {},
            "status_distribution": {},
            "mismatch_by_field": {},
            "cache_hit_rate": {"si_hit_rate_pct": 0, "bl_hit_rate_pct": 0, "overall_pct": 0},
            "processing_time": {"avg_ms": 0, "min_ms": 0, "max_ms": 0},
            "anchor_triage": {},
            "top_review_reasons": {},
            "message": "No events logged yet. Process emails to populate the event log."
        }


event_logger = EventLogger()
