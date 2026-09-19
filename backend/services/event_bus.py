"""
CloudEvents Event Bus & Webhook Dispatcher (Tech Desk v4 — Section 6)

Emits each verification result as a CloudEvents v1.0 JSON envelope.
Supports:
  - In-memory webhook subscriber registry
  - Fire-and-forget webhook dispatch (3s timeout)
  - SSE (Server-Sent Events) endpoint for real-time streaming
"""
import uuid
import json
import time
import threading
import queue
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    import requests as _requests
except ImportError:
    _requests = None


class EventBus:
    """
    CloudEvents v1.0 compatible event bus with webhook dispatch and SSE streaming.
    """

    def __init__(self):
        self._webhooks: Dict[str, Dict[str, Any]] = {}  # id -> { url, created_at, events_sent }
        self._event_history: List[Dict[str, Any]] = []   # recent events for SSE replay
        self._sse_queues: List[queue.Queue] = []          # connected SSE clients
        self._max_history = 500

    # ── Webhook Registry ──────────────────────────────────────────────

    def register_webhook(self, url: str, label: Optional[str] = None) -> Dict[str, Any]:
        """Register a new webhook subscriber URL."""
        webhook_id = str(uuid.uuid4())[:8]
        entry = {
            "id": webhook_id,
            "url": url,
            "label": label or url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "events_sent": 0,
            "last_error": None
        }
        self._webhooks[webhook_id] = entry
        return entry

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook by ID."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks."""
        return list(self._webhooks.values())

    # ── CloudEvents Envelope ──────────────────────────────────────────

    def _build_cloud_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a CloudEvents v1.0 JSON envelope."""
        return {
            "specversion": "1.0",
            "type": "io.maritime.verification.completed",
            "source": "/averish/verification-engine",
            "id": str(uuid.uuid4()),
            "time": datetime.now(timezone.utc).isoformat(),
            "datacontenttype": "application/json",
            "data": event_data
        }

    # ── Event Emission ────────────────────────────────────────────────

    def emit(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Emit a verification result event.
        - Wraps in CloudEvents envelope
        - Dispatches to all registered webhooks (fire-and-forget)
        - Pushes to SSE queues
        - Stores in event history
        """
        cloud_event = self._build_cloud_event(event_data)

        # Store in history (capped)
        self._event_history.append(cloud_event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Dispatch to webhooks in background thread
        if self._webhooks:
            t = threading.Thread(
                target=self._dispatch_webhooks,
                args=(cloud_event,),
                daemon=True
            )
            t.start()

        # Push to SSE clients
        event_json = json.dumps(cloud_event, default=str)
        dead_queues = []
        for q in self._sse_queues:
            try:
                q.put_nowait(event_json)
            except queue.Full:
                dead_queues.append(q)
        for dq in dead_queues:
            self._sse_queues.remove(dq)

        return cloud_event

    def _dispatch_webhooks(self, cloud_event: Dict[str, Any]):
        """Fire-and-forget dispatch to all registered webhook URLs."""
        if _requests is None:
            return

        payload = json.dumps(cloud_event, default=str)
        headers = {
            "Content-Type": "application/cloudevents+json",
            "Ce-Specversion": "1.0",
            "Ce-Type": cloud_event["type"],
            "Ce-Source": cloud_event["source"],
            "Ce-Id": cloud_event["id"]
        }

        for wh_id, wh in list(self._webhooks.items()):
            try:
                resp = _requests.post(
                    wh["url"],
                    data=payload,
                    headers=headers,
                    timeout=3.0
                )
                wh["events_sent"] += 1
                if resp.status_code >= 400:
                    wh["last_error"] = f"HTTP {resp.status_code}"
            except Exception as ex:
                wh["last_error"] = str(ex)[:200]

    # ── SSE Streaming ─────────────────────────────────────────────────

    def subscribe_sse(self) -> queue.Queue:
        """Create a new SSE subscription queue."""
        q = queue.Queue(maxsize=100)
        self._sse_queues.append(q)
        return q

    def unsubscribe_sse(self, q: queue.Queue):
        """Remove an SSE subscription queue."""
        if q in self._sse_queues:
            self._sse_queues.remove(q)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events from history."""
        return self._event_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "total_events_emitted": len(self._event_history),
            "registered_webhooks": len(self._webhooks),
            "active_sse_clients": len(self._sse_queues),
            "max_history": self._max_history
        }


event_bus = EventBus()
