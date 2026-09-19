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
    return _conn


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
