"""
Tests for Reflexion Episodic Memory (Feature A) and Bayesian Routing Policy (Feature B).
"""
import unittest
import os
import tempfile
from unittest.mock import patch

from backend.services.reflection import (
    generate_reflection,
    retrieve_reflections,
    get_all_reflections,
    extract_domain
)
from backend.services.routing_policy import (
    sample_trust,
    update_routing_policy,
    get_policy,
    get_all_policies
)
from backend.services.reasoning_receipt import build_receipt
from backend.services.dataset_loader import loader


class TestReflexionMemory(unittest.TestCase):
    """Reflexion-style episodic memory unit tests."""

    def test_extract_domain(self):
        self.assertEqual(extract_domain("shipping@pacificlogistics.sg"), "pacificlogistics.sg")
        self.assertEqual(extract_domain("<ops@fastfreight.de>"), "fastfreight.de")
        self.assertEqual(extract_domain("Maersk Line"), "maersk line")
        self.assertEqual(extract_domain(""), "unknown")

    def test_generate_and_retrieve_reflection(self):
        sender_email = "test@evergreen-marine.com"
        event = {
            "original_value": "OLD_PORT",
            "corrected_value": "PORT_KLANG",
            "field": "port_of_discharge",
            "sender": sender_email,
            "doc_type": "SI",
            "evidence_summary": "discharge at Port Klang terminal 2",
            "source_correction_id": "corr_test_01"
        }

        # Generate reflection
        ref = generate_reflection(event)
        self.assertTrue(ref["id"])
        self.assertEqual(ref["sender_domain"], "evergreen-marine.com")
        self.assertEqual(ref["field_name"], "port_of_discharge")
        self.assertIn("PORT_KLANG", ref["reflection_text"])
        self.assertEqual(ref["times_retrieved"], 0)

        # Retrieve reflection
        retrieved = retrieve_reflections("evergreen-marine.com", doc_type="SI", limit=3)
        self.assertTrue(len(retrieved) >= 1)
        first = retrieved[0]
        self.assertEqual(first["sender_domain"], "evergreen-marine.com")
        self.assertIn("PORT_KLANG", first["reflection_text"])
        self.assertGreaterEqual(first["times_retrieved"], 1)

    def test_retrieval_cap_at_three(self):
        import uuid
        domain = f"cap-test-{uuid.uuid4().hex[:8]}.com"
        for i in range(5):
            generate_reflection({
                "original_value": f"ERR_{i}",
                "corrected_value": f"CORRECT_{i}",
                "field": "consignee",
                "sender": f"agent@{domain}",
                "doc_type": "SI",
                "evidence_summary": f"Consignee line {i}"
            })

        retrieved = retrieve_reflections(domain, doc_type="SI", limit=3)
        self.assertEqual(len(retrieved), 3)


class TestBayesianRoutingPolicy(unittest.TestCase):
    """Bayesian Thompson Sampling routing policy unit tests."""

    def test_uniform_prior_and_sampling(self):
        import uuid
        domain = f"new-carrier-{uuid.uuid4().hex[:8]}.com"
        policy = get_policy(domain)
        self.assertEqual(policy["alpha"], 1.0)
        self.assertEqual(policy["beta"], 1.0)
        self.assertEqual(policy["mean_trust"], 0.5)

        # Draw a sample
        sample = sample_trust(domain, threshold=0.6)
        self.assertIn("sampled_trust", sample)
        self.assertIn("route_to_ai", sample)
        self.assertIn(sample["decision"], ("ai", "human_first"))

    def test_online_bayesian_updates(self):
        import uuid
        domain = f"adaptive-sender-{uuid.uuid4().hex[:8]}.com"
        # 1. Start at uniform (alpha=1.0, beta=1.0)
        p0 = get_policy(domain)
        self.assertEqual(p0["alpha"], 1.0)
        self.assertEqual(p0["beta"], 1.0)

        # 2. Human corrects AI -> beta increases, trust drops
        update_routing_policy(domain, ai_was_correct=False)
        p1 = get_policy(domain)
        self.assertEqual(p1["beta"], 2.0)
        self.assertEqual(p1["alpha"], 1.0)
        self.assertAlmostEqual(p1["mean_trust"], 1.0 / 3.0, places=2)

        # 3. Another failure -> beta=3.0, trust drops further
        update_routing_policy(domain, ai_was_correct=False)
        p2 = get_policy(domain)
        self.assertEqual(p2["beta"], 3.0)
        self.assertAlmostEqual(p2["mean_trust"], 1.0 / 4.0, places=2)

        # 4. Human confirms AI is correct -> alpha increases
        update_routing_policy(domain, ai_was_correct=True)
        p3 = get_policy(domain)
        self.assertEqual(p3["alpha"], 2.0)
        self.assertEqual(p3["beta"], 3.0)
        self.assertAlmostEqual(p3["mean_trust"], 2.0 / 5.0, places=2)

    def test_get_all_policies_order(self):
        policies = get_all_policies()
        self.assertIsInstance(policies, list)
        for p in policies:
            self.assertIn("sender_domain", p)
            self.assertIn("mean_trust", p)
            self.assertIn("outcomes_count", p)


class TestReceiptLearningIntegration(unittest.TestCase):
    """Reasoning receipt inline tag and learning integration tests."""

    def test_receipt_shows_policy_and_learned_reflections(self):
        email = loader.get_email("email_004")
        self.assertIsNotNone(email)
        sender_domain = extract_domain(email.get("sender"))

        # Pre-seed a reflection for this sender
        generate_reflection({
            "original_value": "WRONG_PORT",
            "corrected_value": "SINGAPORE",
            "field": "port_of_loading",
            "sender": email.get("sender"),
            "doc_type": "SI",
            "evidence_summary": "Loading port Singapore PSA",
            "email_id": "email_004"
        })

        # Build reasoning receipt
        doc = {
            "email_id": "email_004",
            "si_text": "Shipper: ACME\nPort of Loading: Singapore\n",
            "bl_text": "Port of Loading: Singapore\n",
            "names": {"si": "test_si.txt", "bl": "test_bl.txt"},
            "email": email,
            "scan_notes": []
        }
        receipt = build_receipt("TEST-LEARN-SHIPMENT", [doc], persist=False)
        self.assertTrue(receipt["fields"])

        # Check fields for policy and learning metadata
        found_policy_tag = False
        for field in receipt["fields"]:
            self.assertIn("retrieved_reflections", field)
            self.assertIn("policy_routing", field)
            if field.get("policy_tag"):
                found_policy_tag = True
                self.assertIn("Routed by policy", field["policy_tag"])

        # Senders evaluated by policy should have policy tags
        self.assertTrue(found_policy_tag or receipt["summary"]["resolved_by_rules"] == len(receipt["fields"]))


if __name__ == "__main__":
    unittest.main()
