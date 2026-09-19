import unittest
from fastapi.testclient import TestClient
from backend.main import app, HUMAN_OVERRIDES
from backend.services.event_logger import event_logger


class TestShipmentTimeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_shipments_endpoint(self):
        """GET /shipments returns one row per shipment_id with required metadata."""
        # Both /shipments and /api/shipments should respond identically
        res = self.client.get("/shipments")
        self.assertEqual(res.status_code, 200)
        shipments = res.json()
        self.assertIsInstance(shipments, list)
        self.assertGreater(len(shipments), 0)

        # Check fields of the first shipment
        first = shipments[0]
        required_fields = [
            "shipment_id", "latest_stage", "latest_stage_timestamp",
            "needs_review", "title", "port", "carrier", "consignee"
        ]
        for field in required_fields:
            self.assertIn(field, first, f"Missing field '{field}' in shipment summary")

        # Confirm 5RSG-79970 exists in the list
        s_79970 = next((s for s in shipments if s["shipment_id"] == "5RSG-79970"), None)
        self.assertIsNotNone(s_79970, "Shipment 5RSG-79970 not found in /shipments")
        self.assertIn("APAPA", s_79970["title"])
        self.assertIn("CMA", s_79970["title"])
        self.assertIn("CLIFFORD PAPER", s_79970["title"])

    def test_timeline_isolation_5rsg_79970(self):
        """Acceptance Criteria: Selecting 5RSG-79970 shows ONLY that shipment's records, never 5RAE-20163."""
        res = self.client.get("/shipments/5RSG-79970/timeline")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["shipment_id"], "5RSG-79970")
        self.assertIn("history", data)
        self.assertIn("documents", data)

        # Ensure NO data from AFEMY / 5RAE-20163 appears
        data_str = str(data)
        self.assertNotIn("5RAE-20163", data_str, "5RAE-20163 found in 5RSG-79970 timeline!")
        self.assertNotIn("AFEMY", data_str, "AFEMY found in 5RSG-79970 timeline!")
        self.assertNotIn("TOAN LUC", data_str, "TOAN LUC consignee found in 5RSG-79970 timeline!")

        # Check documents for 5RSG-79970
        doc_names = [d["name"] for d in data["documents"]]
        self.assertIn("email_111_SI.txt", doc_names)
        self.assertIn("email_111_BL.txt", doc_names)
        for doc in data["documents"]:
            self.assertIn("name", doc)
            self.assertIn("type", doc)
            self.assertIn("status", doc)
            self.assertIn(doc["status"], ["verified", "mismatch", "pending"])
            self.assertIn("file_url", doc)

    def test_timeline_events_actor_and_schema(self):
        """Verify history events adhere to { actor: 'system' | 'ai' | 'human', actor_name, action_text, timestamp, related_field }."""
        res = self.client.get("/shipments/5RSG-79970/timeline")
        self.assertEqual(res.status_code, 200)
        history = res.json()["history"]
        self.assertGreater(len(history), 0)

        valid_actors = {"system", "ai", "human"}
        for event in history:
            self.assertIn(event["actor"], valid_actors, f"Invalid actor: {event['actor']}")
            self.assertIsInstance(event["actor_name"], str)
            self.assertIsInstance(event["action_text"], str)
            self.assertIn("timestamp", event)
            self.assertIn("related_field", event)

    def test_human_correction_links_back_to_ai_action(self):
        """Acceptance Criteria: Human correction event visibly links back to AI action it corrected."""
        res = self.client.get("/shipments/5RSG-79970/timeline")
        self.assertEqual(res.status_code, 200)
        history = res.json()["history"]

        # Find the human correction event
        human_events = [e for e in history if e["actor"] == "human"]
        self.assertGreater(len(human_events), 0, "No human correction event found in 5RSG-79970 timeline")

        correction = human_events[0]
        self.assertEqual(correction["actor_name"], "Pohyi Chong")
        self.assertEqual(correction["related_field"], "container_count")
        self.assertIn("Pohyi Chong corrected container_count: 4 → 3, flagged by AI comparison", correction["action_text"])
        self.assertIn("linked_ai_event_id", correction)
        self.assertTrue(correction["linked_ai_event_id"].endswith("ai-mismatch"))

    def test_duckdb_event_logger_has_shipment_id(self):
        """Backend Change 1: DuckDB event logger confirms shipment_id foreign key on events."""
        event_id = event_logger.log_event(
            email_id="email_111",
            category="BL_COMPARISON",
            shipment_id="5RSG-79970",
            comparison_status="MISMATCH",
            defect_fields=["container_count"]
        )
        self.assertIsNotNone(event_id)

        # Retrieve events and verify shipment_id is present
        events = event_logger.get_events(limit=5)
        logged = next((e for e in events if e.get("event_id") == event_id), None)
        self.assertIsNotNone(logged)
        self.assertEqual(logged["shipment_id"], "5RSG-79970")

        # Test log_timeline_event
        tl_id = event_logger.log_timeline_event(
            shipment_id="5RSG-79970",
            actor="human",
            actor_name="Pohyi Chong",
            action_text="Pohyi Chong corrected container_count: 4 → 3, flagged by AI comparison",
            stage="review",
            related_field="container_count"
        )
        self.assertIsNotNone(tl_id)
        shipment_events = event_logger.get_shipment_events("5RSG-79970")
        self.assertGreater(len(shipment_events), 0)
        self.assertEqual(shipment_events[-1]["shipment_id"], "5RSG-79970")


if __name__ == "__main__":
    unittest.main()
