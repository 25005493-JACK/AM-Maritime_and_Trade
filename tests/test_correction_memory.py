"""
Unit tests proving Phase 5: Correction Memory & Bayesian Trust Routing.
Tests reflection generation, retrieval, prompt injection, and review gating.
"""
import os
import unittest
from unittest.mock import patch

from backend.services.reflection import (
    extract_domain,
    generate_reflection,
    retrieve_reflections,
)
from backend.services.routing_policy import (
    get_policy,
    sample_trust,
    update_routing_policy,
)
from llm_agent.client import LLMClient, FakeTransport
from llm_agent.tasks import extract_fields, classify_email


class TestCorrectionMemory(unittest.TestCase):
    """Tests for Reflexion episodic memory and Bayesian trust posteriors."""

    def setUp(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "assist"
        self.test_domain = "carrier-test-line.com"

    def tearDown(self):
        os.environ["DOCUMATCH_LLM_MODE"] = "off"

    def test_reflection_generation_and_retrieval(self):
        correction = {
            "field": "container_count",
            "original_ai_value": "1",
            "corrected_value": "3 x 40'HC",
            "sender": f"docs@{self.test_domain}",
            "doc_type": "BL",
            "email_id": "dev_test_001",
        }
        rec = generate_reflection(correction)
        self.assertEqual(rec["sender_domain"], self.test_domain)
        self.assertEqual(rec["field_name"], "container_count")
        self.assertIn("3 x 40'HC", rec["reflection_text"])

        # Retrieve reflection
        retrieved = retrieve_reflections(self.test_domain, doc_type="BL", limit=5)
        self.assertTrue(any(r["id"] == rec["id"] for r in retrieved))

    def test_bayesian_trust_posterior_update(self):
        # Initial policy for new domain has uniform prior Beta(1, 1) -> mean 0.5
        pol_init = get_policy(self.test_domain)
        init_alpha = pol_init["alpha"]
        init_beta = pol_init["beta"]

        # Record human corrections / AI errors -> increments beta
        update_routing_policy(self.test_domain, ai_was_correct=False)
        update_routing_policy(self.test_domain, ai_was_correct=False)
        update_routing_policy(self.test_domain, ai_was_correct=False)

        pol_after = get_policy(self.test_domain)
        self.assertEqual(pol_after["beta"], init_beta + 3.0)
        self.assertLess(pol_after["mean_trust"], 0.5)

        # Record verified correct outcomes -> increments alpha
        update_routing_policy(self.test_domain, ai_was_correct=True)
        pol_after2 = get_policy(self.test_domain)
        self.assertEqual(pol_after2["alpha"], init_alpha + 1.0)

    def test_prompt_injection_memory_on_vs_off(self):
        from llm_agent.client import llm_client

        # Seed a reflection for domain
        domain = "prompt-test-carrier.com"
        generate_reflection({
            "field": "port_of_loading",
            "original_ai_value": "PORT_A",
            "corrected_value": "SINGAPORE (SGSIN)",
            "sender": f"ops@{domain}",
            "doc_type": "BL",
            "email_id": "dev_test_002",
        })

        prompts_seen = []
        transport = FakeTransport(
            lambda prompt, schema: (
                prompts_seen.append(prompt) or {
                    "fields": {
                        "port_of_loading": {
                            "value": "SINGAPORE (SGSIN)",
                            "evidence_quote": "PORT OF LOADING: SINGAPORE (SGSIN)",
                            "confidence": 0.95,
                        }
                    }
                }
            )
        )
        llm_client.set_transport(transport)

        doc_text = "PORT OF LOADING: SINGAPORE (SGSIN)"

        # Memory OFF: prompt must NOT contain reflection header
        prompts_seen.clear()
        with patch("backend.services.routing_policy.sample_trust", return_value={"route_to_ai": True, "mean_trust": 0.8}):
            extract_fields(["port_of_loading"], doc_text, "doc_001", sender_domain=domain, memory_enabled=False)
        self.assertEqual(len(prompts_seen), 1)
        self.assertNotIn("Lessons from past reviewer corrections", prompts_seen[0])

        # Memory ON: prompt MUST contain reflection header
        prompts_seen.clear()
        with patch("backend.services.routing_policy.sample_trust", return_value={"route_to_ai": True, "mean_trust": 0.8}):
            extract_fields(["port_of_loading"], doc_text, "doc_002", sender_domain=domain, memory_enabled=True)
        self.assertEqual(len(prompts_seen), 1)
        self.assertIn("Lessons from past reviewer corrections", prompts_seen[0])
        self.assertIn(domain, prompts_seen[0])

    def test_review_gating_memory_on_vs_off(self):
        from llm_agent.client import llm_client

        transport = FakeTransport(
            lambda prompt, schema: {
                "fields": {
                    "container_count": {
                        "value": "3",
                        "evidence_quote": "3 UNITS",
                        "confidence": 0.9,
                    }
                }
            }
        )
        llm_client.set_transport(transport)
        doc_text = "CONTAINERS: 3 UNITS"

        # Simulate low trust for a defect-prone carrier (e.g., trust=0.35 < 0.60)
        low_trust_res = {
            "sender_domain": "risky-carrier.com",
            "route_to_ai": False,
            "mean_trust": 0.35,
            "sampled_trust": 0.30,
            "threshold": 0.60,
        }

        with patch("backend.services.routing_policy.sample_trust", return_value=low_trust_res):
            # Memory OFF: bypasses policy, calls AI
            res_off = extract_fields(["container_count"], doc_text, "doc_003", sender_domain="risky-carrier.com", memory_enabled=False)
            self.assertFalse(res_off.get("routed_to_human_by_policy", False))
            self.assertIn("container_count", res_off["proposals"])

            # Memory ON: gates to human review, skips AI
            res_on = extract_fields(["container_count"], doc_text, "doc_004", sender_domain="risky-carrier.com", memory_enabled=True)
            self.assertTrue(res_on.get("routed_to_human_by_policy", False))
            self.assertEqual(res_on["proposals"], {})


if __name__ == "__main__":
    unittest.main()
