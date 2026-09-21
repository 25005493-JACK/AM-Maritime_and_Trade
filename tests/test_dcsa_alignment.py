"""DCSA alignment + propose-and-confirm correction flow tests.

Covers the acceptance criteria:
  * every internal field (data/field_terms.json) has a mapping entry;
  * the most common fields carry *real* DCSA Bill of Lading field names with the
    DCSA document they were verified from, and Incoterm is flagged internal_only
    instead of being force-mapped;
  * a conflicting field is never auto-resolved - a human decision is required, and
    the resolved record is structured by DCSA field names.
"""
import csv
import json
import os
import tempfile
import unittest
from unittest import mock

from backend.services import correction_flow, dcsa_mapping, field_evidence
from backend.services.comparator import comparator
from backend.services.dataset_loader import loader

#: Fields called out by the acceptance criteria that must map to a real DCSA field.
ACCEPTANCE_MAPPED_FIELDS = [
    "shipper",
    "consignee",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
    "hs_code",
    "carrier_reference",
]

EXPECTED_DCSA_FIELDS = {
    "shipper": "documentParties.shipper",
    "consignee": "documentParties.consignee",
    "notify_party": "documentParties.notifyParty",
    "port_of_loading": "portOfLoading",
    "port_of_discharge": "portOfDischarge",
    "container_count": "utilizedTransportEquipments",
    "gross_weight_kg": "consignmentItems[].cargoItems[].cargoGrossWeight",
    "hs_code": "consignmentItems[].extendedHSCodes",
    "carrier_reference": "carrierBookingReference",
}


def _doc_texts(email):
    si_text = bl_text = ""
    for att in email.get("attachments", []):
        path = att["path"] if isinstance(att, dict) else str(att)
        if "_si." in path.lower():
            si_text = loader.read_attachment_text(path)
        elif "_bl." in path.lower():
            bl_text = loader.read_attachment_text(path)
    return si_text, bl_text


class TestDcsaMapping(unittest.TestCase):
    """The mapping layer must be complete and verifiable, not invented."""

    def test_every_field_terms_field_has_a_mapping_entry(self):
        internal = dcsa_mapping.internal_field_keys()
        self.assertIn("shipper", internal)
        self.assertEqual(dcsa_mapping.unmapped_internal_fields(), [],
                         "every field in field_terms.json needs a mapping entry")

    def test_acceptance_fields_map_to_real_dcsa_names(self):
        for field in ACCEPTANCE_MAPPED_FIELDS:
            mapping = dcsa_mapping.mapping_for(field)
            self.assertFalse(mapping.get("internal_only"), f"{field} should map to DCSA")
            self.assertEqual(mapping.get("dcsa_field"), EXPECTED_DCSA_FIELDS[field], field)

    def test_mapping_entries_cite_dcsa_documentation(self):
        for field in ACCEPTANCE_MAPPED_FIELDS:
            mapping = dcsa_mapping.mapping_for(field)
            self.assertIn("dcsaorg", mapping.get("verified_from", ""),
                          f"{field} must cite the DCSA spec it was verified from")
            self.assertTrue(mapping.get("verified_quote"), f"{field} needs the DCSA wording")
            self.assertIn("DCSA Bill of Lading", mapping.get("dcsa_standard", ""))

    def test_incoterm_is_internal_only_not_force_mapped(self):
        mapping = dcsa_mapping.mapping_for("incoterm")
        self.assertTrue(mapping["internal_only"])
        self.assertIsNone(mapping["dcsa_field"])
        self.assertEqual(mapping["related_dcsa_field"], "incoTerms")
        # ... and the related field is flagged as coming from another DCSA standard
        self.assertIn("Booking", mapping["related_dcsa_standard"])
        self.assertIsNone(dcsa_mapping.dcsa_field_name("incoterm"))

    def test_coverage_report(self):
        report = dcsa_mapping.coverage_report()
        self.assertEqual(report["coverage_pct"], 100.0)
        self.assertGreaterEqual(report["catalog_size"], 15)


class TestFieldEvidence(unittest.TestCase):
    """Evidence records show where a value came from - and are not certificates."""

    def setUp(self):
        self.email = loader.get_email("email_004")
        self.si_text, self.bl_text = _doc_texts(self.email)
        self.verification = comparator.compare_documents(
            self.si_text, self.bl_text, email_metadata=self.email
        )

    def test_conflicting_field_evidence_has_schema(self):
        record = field_evidence.build_field_evidence(
            "consignee",
            self.verification["si_extracted"]["consignee"],
            self.verification["bl_extracted"]["consignee"],
            self.si_text, self.bl_text, "email_004_SI.txt", "email_004_BL.txt",
        )
        for key in ("dcsa_field", "value", "sources", "validation", "agreement"):
            self.assertIn(key, record)
        self.assertEqual(record["dcsa_field"], "documentParties.consignee")
        self.assertEqual(record["agreement"], "conflict")
        self.assertEqual(len(record["sources"]), 2)
        for source in record["sources"]:
            self.assertIn("char_offset", source)
            self.assertIn("exact_text", source)
            self.assertTrue(source["found_in_document"], source["document"])
            self.assertIsInstance(source["char_offset"], int)
        self.assertEqual(record["validation"]["source_match"], "pass")
        self.assertIn(record["validation"]["whitelist"]["status"], ("pass", "fail", "n/a"))

    def test_whitelist_tables_are_applied_per_field(self):
        pod = field_evidence.check_whitelist("port_of_discharge", "NHAVA SHEVA, INDIA (INNSA)")
        self.assertEqual(pod["table"], "UN/LOCODE")
        self.assertEqual(pod["status"], "pass")
        self.assertEqual(field_evidence.check_whitelist("container_count", "3", "NARU3472484")["table"], "ISO 6346")
        self.assertIsNone(field_evidence.check_whitelist("shipper", "ACME")["table"])

    def test_no_certificate_or_legal_claim_in_evidence(self):
        record = field_evidence.build_field_evidence("consignee", "A", "B", "A", "B")
        flat = json.dumps(record).lower()
        for forbidden in ("certificate", "hash", "legally_valid", "signature"):
            self.assertNotIn(forbidden, flat)




class TestProposeAndConfirm(unittest.TestCase):
    """SI and BL are equal-weight sources; only a human decision resolves a field."""

    def setUp(self):
        self.email = loader.get_email("email_004")
        self.si_text, self.bl_text = _doc_texts(self.email)
        self.verification = comparator.compare_documents(
            self.si_text, self.bl_text, email_metadata=self.email
        )
        self.proposals = correction_flow.build_conflict_proposals(
            "email_004", self.verification, self.si_text, self.bl_text, self.email
        )

    def test_proposals_surface_both_sources_and_never_auto_resolve(self):
        self.assertEqual(self.proposals["auto_resolution"], "disabled")
        self.assertTrue(self.proposals["proposals"])
        for proposal in self.proposals["proposals"]:
            self.assertTrue(proposal["requires_human_decision"])
            self.assertFalse(proposal["auto_resolved"])
            self.assertIsNone(proposal["decision"])
            self.assertEqual(proposal["options"], ["si", "bl", "custom"])
            self.assertNotEqual(proposal["si_candidate"]["value"],
                                proposal["bl_candidate"]["value"])

    def test_resolution_requires_a_human_decision(self):
        with self.assertRaises(correction_flow.HumanDecisionRequired):
            correction_flow.apply_human_resolution("email_004", [], "Pohyi Chong")
        with self.assertRaises(correction_flow.HumanDecisionRequired):
            correction_flow.apply_human_resolution("email_004", [], None)
        with self.assertRaises(correction_flow.HumanDecisionRequired):
            correction_flow.apply_human_resolution(
                "email_004", [{"field_key": "consignee", "choice": "auto"}], "Pohyi Chong"
            )
        with self.assertRaises(correction_flow.HumanDecisionRequired):
            correction_flow.apply_human_resolution(
                "email_004", [{"field_key": "consignee", "choice": "custom"}], "Pohyi Chong"
            )

    def _apply(self, decisions):
        """Run a resolution against a temp log/record dir; return the CSV rows read inside it."""
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "corrections.csv")
            with mock.patch("backend.services.corrections_log.corrections_path", lambda: log_path), \
                 mock.patch("backend.services.correction_flow.resolved_dir", lambda: tmp):
                result = correction_flow.apply_human_resolution(
                    "email_004", decisions, "Pohyi Chong",
                    verification=self.verification, si_text=self.si_text,
                    bl_text=self.bl_text, email=self.email,
                    timestamp="2026-09-20T13:00:00+00:00",
                )
            with open(log_path, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            return result, rows

    def test_reviewer_choice_is_recorded_with_evidence_and_dcsa_field(self):
        result, rows = self._apply([{"field_key": "consignee", "choice": "si"}])
        decision = result["resolved_bl"]["review_decisions"][0]
        self.assertEqual(decision["chosen"], "si")
        self.assertEqual(decision["reviewer"], "Pohyi Chong")
        self.assertEqual(decision["dcsa_field"], "documentParties.consignee")
        self.assertEqual(decision["value"], self.verification["si_extracted"]["consignee"])
        self.assertNotEqual(decision["rejected_values"]["bl"], decision["value"])
        self.assertTrue(decision["evidence"])

        self.assertEqual(len(rows), 1)
        self.assertIn("dcsa_field", rows[0])
        self.assertEqual(rows[0]["dcsa_field"], "documentParties.consignee")
        self.assertEqual(rows[0]["reviewer"], "Pohyi Chong")
        self.assertTrue(rows[0]["resolution"].startswith("human_selected"))

    def test_resolved_bl_is_dcsa_structured(self):
        result, _rows = self._apply(
            [{"field_key": "notify_party", "choice": "custom", "value": "EAST BRIGHT FZ-LLC, DUBAI"}]
        )
        record = result["resolved_bl"]
        td = record["transportDocument"]
        self.assertEqual(record["record_type"], "resolved_transport_document")
        self.assertIn("DCSA Bill of Lading", record["standard"]["name"])
        self.assertEqual(td["documentParties"]["notifyParty"]["partyName"], "EAST BRIGHT FZ-LLC, DUBAI")
        self.assertIn("portOfDischarge", td)
        self.assertEqual(len(td["utilizedTransportEquipments"]),
                         int(self.verification["bl_extracted"]["container_count"]))
        self.assertEqual(td["consignmentItems"][0]["cargoItems"][0]["cargoGrossWeightUnit"], "KGM")
        # internal-only fields are kept out of the DCSA structure
        for field_key in record["internal_only_fields"]:
            self.assertTrue(dcsa_mapping.is_internal_only(field_key))
        # no legal/certificate claims, and a shape that is not our internal one
        self.assertIn("not a certificate", record["notice"])
        self.assertNotIn("field_matrix", record)
        # the export is keyed by DCSA paths, not by our internal field names
        self.assertIn("documentParties.shipper.partyName", result["dcsa_export"])
        self.assertIn("portOfDischarge.locationName", result["dcsa_export"])
        self.assertNotIn("gross_weight_kg", result["dcsa_export"])

    def test_pending_conflicts_are_not_silently_resolved(self):
        result, _rows = self._apply([{"field_key": "consignee", "choice": "bl"}])
        self.assertIn("notify_party", result["pending_decisions"])
        self.assertNotIn("notify_party", result["resolved_bl"]["field_mapping"],
                         "undecided conflicts must not appear in the resolved record")


if __name__ == "__main__":
    unittest.main()
