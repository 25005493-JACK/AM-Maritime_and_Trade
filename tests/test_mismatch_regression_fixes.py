"""Regression tests for the SI/BL false-positive fixes.

Covers the three reported defects:
  1. Parenthetical header variants (``Shipper (Principal or Seller):``,
     ``Consignee (Non-Negotiable):``) must extract, so email_043's shipper and
     consignee compare OK instead of being reported as MISMATCH.
  2. ``notify_party`` values that only differ by a ``P.O. BOX`` line must be
     reported as OK with note ``formatting_only``.
  3. A value missing on one side must route to NEEDS_REVIEW with reason code
     ``extraction_missing`` and must never be counted as a defect.
"""
import unittest

from backend.services.comparator import comparator
from backend.services.comparator import (
    ADDRESS_TAIL_PATTERN,
    compare_company_field,
    is_safe_prefix_match,
)
from backend.services.dataset_loader import loader
from backend.services.extractor import extract_attachment
from backend.services.field_bank import (
    COMPANY_NAME_FIELDS,
    FIELD_HEADER_PATTERNS,
    company_name_normalizer,
    compare_company_name,
    match_header_label,
)


class TestHeaderVariants(unittest.TestCase):
    """Problem 1: bracketed / bilingual header variants resolve to canonical fields."""

    def test_documented_header_variants(self):
        cases = {
            "Shipper (Principal or Seller)": "shipper",
            "Shipper:": "shipper",
            "发货人": "shipper",
            "Consignor": "shipper",
            "Consignee (Non-Negotiable)": "consignee",
            "Consignee:": "consignee",
            "收货人": "consignee",
            "Notify Party": "notify_party",
            "Notify Address": "notify_party",
            "通知方": "notify_party",
            "通知人": "notify_party",
        }
        for label, expected in cases.items():
            self.assertEqual(match_header_label(label), expected, f"{label!r} -> {expected}")
            self.assertIn(expected, FIELD_HEADER_PATTERNS)
        self.assertEqual(COMPANY_NAME_FIELDS, {"shipper", "consignee", "notify_party"})

    def test_email_043_bracketed_party_blocks_extract(self):
        """SI has 'Shipper (Principal or Seller):', BL has 'Consignee (Non-Negotiable):'."""
        si = extract_attachment(
            loader.resolve_attachment_path("attachments/email_043_SI.txt"), doc_type_hint="SI"
        )
        bl = extract_attachment(
            loader.resolve_attachment_path("attachments/email_043_BL.txt"), doc_type_hint="BL"
        )
        for field in sorted(COMPANY_NAME_FIELDS):
            self.assertIsNotNone(si[field], f"SI {field} failed to extract")
            self.assertIsNotNone(bl[field], f"BL {field} failed to extract")
        self.assertEqual(si["shipper"], bl["shipper"])
        self.assertEqual(si["consignee"], bl["consignee"])

    def test_email_043_shipper_and_consignee_compare_ok(self):
        """email_043 must not report shipper / consignee as defects."""
        email = loader.get_email("email_043")
        si_text = loader.read_attachment_text("attachments/email_043_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_043_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=email)
        rows = {row["field_key"]: row for row in res["field_matrix"]}

        for field in ("shipper", "consignee"):
            self.assertTrue(rows[field]["is_match"], f"{field} is a false positive")
            self.assertEqual(rows[field]["status"], "OK")
            self.assertNotIn(field, res["defect_fields"])

        # Field-level verdicts use the documented OK contract.
        si = extract_attachment(loader.resolve_attachment_path("attachments/email_043_SI.txt"), doc_type_hint="SI")
        bl = extract_attachment(loader.resolve_attachment_path("attachments/email_043_BL.txt"), doc_type_hint="BL")
        for field in ("shipper", "consignee"):
            verdict = compare_company_name(si[field], bl[field], field)
            self.assertEqual(verdict["status"], "OK")
            self.assertEqual(verdict["note"], "exact_match")

        # The only genuine difference in email_043 remains the container count (3 vs 5).
        self.assertEqual(res["defect_fields"], ["container_count"])


class TestNotifyPartyPoBoxFormatting(unittest.TestCase):
    """Problem 2: a P.O. BOX difference is formatting, not a discrepancy."""

    def test_normalizer_removes_po_box_variants(self):
        expected = "AL GURG STATIONERY LLC"
        for variant in (
            "AL GURG STATIONERY LLC P.O. BOX 12345",
            "AL GURG STATIONERY LLC P.O.BOX 12345",
            "AL GURG STATIONERY LLC PO BOX 12345",
            "AL GURG STATIONERY LLC POST OFFICE BOX 12345",
            "AL GURG STATIONERY LLC P.O. BOX: 12345",
            "al gurg stationery llc",
        ):
            self.assertEqual(company_name_normalizer(variant, "notify_party"), expected, variant)

    def test_normalizer_is_scoped_to_party_fields(self):
        # Party fields drop the P.O. BOX; other fields keep every token.
        value = "AL GURG STATIONERY LLC P.O. BOX 12345"
        self.assertEqual(company_name_normalizer(value, "notify_party"), "AL GURG STATIONERY LLC")
        self.assertIn("P O BOX 12345", company_name_normalizer(value, "gross_weight_kg"))
        self.assertEqual(
            company_name_normalizer(value, strip_po_box=False),
            "AL GURG STATIONERY LLC P O BOX 12345",
        )

    def test_po_box_vs_plain_is_formatting_only(self):
        verdict = compare_company_name(
            "PACIFIC OFFICE (M) SDN BHD P.O. BOX 12345",
            "PACIFIC OFFICE (M) SDN BHD",
            "notify_party",
        )
        self.assertEqual(verdict["status"], "OK")
        self.assertEqual(verdict["note"], "formatting_only")

    def test_po_box_documents_are_not_flagged(self):
        """SI '... P.O. BOX 5069; DUBAI, UAE' vs BL without the box -> OK."""
        for email_id in ("email_055", "email_435", "email_462"):
            email = loader.get_email(email_id)
            si_doc = bl_doc = None
            for att in email["attachments"]:
                extracted = extract_attachment(
                    loader.resolve_attachment_path(att["path"]),
                    doc_type_hint=att["doc_type"],
                    email_id=email_id,
                )
                if att["doc_type"] == "SI":
                    si_doc = extracted
                elif att["doc_type"] == "BL":
                    bl_doc = extracted

            self.assertIsNotNone(si_doc, f"{email_id}: SI not extracted")
            self.assertIsNotNone(bl_doc, f"{email_id}: BL not extracted")
            self.assertIn("P.O. BOX", si_doc["notify_party"].upper(), email_id)
            self.assertNotIn("P.O. BOX", bl_doc["notify_party"].upper(), email_id)

            res = comparator.compare_documents(si_doc.raw_text, bl_doc.raw_text, email_metadata=email)
            row = {r["field_key"]: r for r in res["field_matrix"]}["notify_party"]

            self.assertTrue(row["is_match"], f"{email_id}: notify_party is a false positive")
            self.assertEqual(row["note"], "formatting_only", email_id)
            self.assertTrue(row["is_formatting_difference"], email_id)
            self.assertEqual(row["status"], "OK", email_id)
            self.assertNotIn("notify_party", res["defect_fields"], email_id)


class TestMissingValueRouting(unittest.TestCase):
    """Problem 3: a one-sided value is a review item, never a MISMATCH defect."""

    def test_field_comparator_routes_missing_to_review(self):
        for si_val, bl_val in (
            (None, "ACME LTD"),
            ("ACME LTD", None),
            ("", "ACME LTD"),
            ("N/A", "ACME LTD"),
        ):
            verdict = compare_company_name(si_val, bl_val, "notify_party")
            self.assertEqual(verdict["status"], "NEEDS_REVIEW", f"{si_val!r}/{bl_val!r}")
            self.assertEqual(verdict["reason"], "extraction_missing")

    def test_single_field_meta_carries_extraction_missing(self):
        is_match, si_str, _bl_str, meta = comparator._compare_single_field(
            "notify_party", None, "ACME LTD"
        )
        self.assertFalse(is_match)
        self.assertEqual(meta["match_type"], "NEEDS_REVIEW")
        self.assertEqual(meta["status"], "NEEDS_REVIEW")
        self.assertEqual(meta["reason"], "extraction_missing")
        self.assertEqual(si_str, "MISSING")

    def test_blank_override_value_routes_document_to_review(self):
        text = (
            "SHIPPING INSTRUCTION\n"
            "Shipper: AL GURG STATIONERY LLC\n"
            "Consignee: PACIFIC OFFICE (M) SDN BHD\n"
            "Notify Party: PACIFIC OFFICE (M) SDN BHD\n"
            "Port of Loading: SINGAPORE (SGSIN)\n"
            "Port of Discharge: ROTTERDAM (NLRTM)\n"
            "Container Count: 3 x 20'GP\n"
            "Gross Weight: 22,000 KG\n"
        )
        res = comparator.compare_documents(
            text,
            text,
            overrides={"bl_overrides": {"notify_party": ""}},
        )
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["review_reason"], "extraction_missing")
        self.assertFalse(res["has_defect"])
        self.assertEqual(res["defect_fields"], [])
        self.assertIn("notify_party", res["review_fields"])
        row = {r["field_key"]: r for r in res["field_matrix"]}["notify_party"]
        self.assertEqual(row["match_type"], "NEEDS_REVIEW")
        self.assertEqual(row["reason"], "extraction_missing")

    def test_document_missing_value_is_review_not_defect(self):
        """email_520 (missing consignee in the SI) escalates, it does not accuse."""
        email = loader.get_email("email_520")
        si_text = loader.read_attachment_text("attachments/email_520_SI.txt")
        bl_text = loader.read_attachment_text("attachments/email_520_BL.txt")

        res = comparator.compare_documents(si_text, bl_text, email_metadata=email)
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        # Document-level enum is kept for the submission contract (backend/main.py maps it);
        # the per-field reason code is the reviewer-facing `extraction_missing`.
        self.assertEqual(res["review_reason"], "missing_value")
        self.assertFalse(res["has_defect"])
        self.assertNotIn("consignee", res["defect_fields"])
        self.assertEqual(res["field_review_reasons"].get("consignee"), "extraction_missing")
        row = {r["field_key"]: r for r in res["field_matrix"]}["consignee"]
        self.assertEqual(row["reason"], "extraction_missing")


class TestSafePrefixGuard(unittest.TestCase):
    """Triple guards on the trailing-address prefix match (comparator layer)."""

    def test_short_prefix_rejected(self):
        """Guard 1: "ABC" is < 8 chars and a single word -> MISMATCH."""
        self.assertFalse(is_safe_prefix_match("ABC", "ABCDEF LOGISTICS"))
        verdict = compare_company_field("shipper", "ABC", "ABCDEF LOGISTICS")
        self.assertEqual(verdict["status"], "MISMATCH")

    def test_non_address_tail_rejected(self):
        """Guard 3: "FORMERLY XYZ" is an entity change, not address detail."""
        si = "GLOBAL LOGISTICS CO LTD"
        bl = "GLOBAL LOGISTICS CO LTD FORMERLY XYZ"
        self.assertIsNone(ADDRESS_TAIL_PATTERN.search("FORMERLY XYZ"))
        self.assertFalse(is_safe_prefix_match(si, bl))
        verdict = compare_company_field("shipper", si, bl)
        self.assertEqual(verdict["status"], "MISMATCH")

    def test_address_tail_accepted(self):
        """All three guards pass -> OK / formatting_only / trailing_address_stripped."""
        si = "GLOBAL LOGISTICS CO LTD"
        bl = "GLOBAL LOGISTICS CO LTD P O BOX 5069 DUBAI UAE"
        self.assertTrue(is_safe_prefix_match(si, bl))
        verdict = compare_company_field("notify_party", si, bl)
        self.assertEqual(verdict["status"], "OK")
        self.assertEqual(verdict["note"], "formatting_only")
        self.assertEqual(verdict["reason"], "trailing_address_stripped")

    def test_word_boundary_guard_rejects_mid_word_cut(self):
        """Guard 2: "GLOBAL LOGISTIC" cuts "LOGISTICS" mid-word."""
        self.assertFalse(is_safe_prefix_match("GLOBAL LOGISTIC", "GLOBAL LOGISTICS CO LTD DUBAI"))

    def test_postal_code_and_city_tails_accepted(self):
        self.assertTrue(is_safe_prefix_match(
            "APRIL FINE PAPER TRADING",
            "APRIL FINE PAPER TRADING 77 ROBINSON ROAD SINGAPORE 068896",
        ))
        self.assertTrue(is_safe_prefix_match(
            "ORIENT LINKS CO LLC", "ORIENT LINKS CO LLC JEBEL ALI DUBAI UAE",
        ))

    def test_document_level_guards(self):
        template = (
            "SHIPPING INSTRUCTION\n"
            "Shipper: GLOBAL LOGISTICS CO LTD\n"
            "Consignee: ACME SHIPPING PTE LTD\n"
            "Notify Party: {notify}\n"
            "Port of Loading: SINGAPORE (SGSIN)\n"
            "Port of Discharge: ROTTERDAM (NLRTM)\n"
            "Container Count: 2 x 20'GP\n"
            "Gross Weight: 10,000 KG\n"
        )
        # Address tail -> formatting only, no defect.
        accepted = comparator.compare_documents(
            template.format(notify="GLOBAL LOGISTICS CO LTD"),
            template.format(notify="GLOBAL LOGISTICS CO LTD P O BOX 5069 DUBAI UAE"),
        )
        self.assertEqual(accepted["status"], "OK")
        row = {r["field_key"]: r for r in accepted["field_matrix"]}["notify_party"]
        self.assertTrue(row["is_match"])
        self.assertEqual(row["note"], "formatting_only")
        self.assertEqual(row["reason"], "trailing_address_stripped")

        # Entity change -> MISMATCH defect.
        rejected = comparator.compare_documents(
            template.format(notify="GLOBAL LOGISTICS CO LTD"),
            template.format(notify="GLOBAL LOGISTICS CO LTD FORMERLY XYZ"),
        )
        self.assertEqual(rejected["status"], "MISMATCH")
        self.assertIn("notify_party", rejected["defect_fields"])

    def test_real_po_box_documents_still_accepted(self):
        """The guards must not reintroduce the email_055/435/462 false positives."""
        for email_id in ("email_055", "email_435", "email_462"):
            email = loader.get_email(email_id)
            si_doc = bl_doc = None
            for att in email["attachments"]:
                extracted = extract_attachment(
                    loader.resolve_attachment_path(att["path"]),
                    doc_type_hint=att["doc_type"],
                    email_id=email_id,
                )
                if att["doc_type"] == "SI":
                    si_doc = extracted
                elif att["doc_type"] == "BL":
                    bl_doc = extracted
            res = comparator.compare_documents(si_doc.raw_text, bl_doc.raw_text, email_metadata=email)
            row = {r["field_key"]: r for r in res["field_matrix"]}["notify_party"]
            self.assertTrue(row["is_match"], email_id)
            self.assertEqual(row["reason"], "trailing_address_stripped", email_id)
            self.assertNotIn("notify_party", res["defect_fields"], email_id)


if __name__ == "__main__":
    unittest.main()
