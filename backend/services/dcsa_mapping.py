"""
DCSA Bill of Lading field mapping layer.

Maps every internal extraction field to its corresponding DCSA Bill of Lading
(eBL) data element, so our verification output can be expressed in an *external*
industry standard instead of a self-invented format.

Field names are NOT invented here. Every mapping was taken from DCSA's public
specification repository (github.com/dcsaorg/DCSA-OpenAPI) and carries the exact
document it was verified from:

  * ebl/v3/README.md           - DCSA Bill of Lading API v3 change log (Transport
                                 Document / Shipping Instructions objects)
  * ebl/v3/EBL_v3.0.3.yaml     - DCSA Bill of Lading OpenAPI v3.0.3 schemas/examples
  * ebl/v3/issuance/README.md  - DCSA eBL Issuance v3.0.3 (`documentParties`)
  * bkg/v2/BKG_v2.0.0.yaml     - DCSA Booking v2, the only DCSA standard modelling
                                 Incoterms (`incoTerms`) - referenced as such

Where DCSA has no equivalent attribute we do NOT force a mapping: the field is
flagged ``internal_only: True`` (optionally with a ``related_dcsa_field`` from a
*different* DCSA standard, clearly reported as not-a-BoL-field).
"""
import os
import json
from typing import Any, Dict, List, Optional

DCSA_STANDARD = "DCSA Bill of Lading (eBL) v3.0.3"
DCSA_INFORMATION_MODEL = "DCSA Information Model 3.x (UN/CEFACT Multi-Modal Transport RDM aligned)"
DCSA_SOURCES = {
    "bol_readme": "https://github.com/dcsaorg/DCSA-OpenAPI/blob/master/ebl/v3/README.md",
    "bol_spec": "https://github.com/dcsaorg/DCSA-OpenAPI/blob/master/ebl/v3/EBL_v3.0.3.yaml",
    "issuance_readme": "https://github.com/dcsaorg/DCSA-OpenAPI/blob/master/ebl/v3/issuance/README.md",
    "booking_spec": "https://github.com/dcsaorg/DCSA-OpenAPI/blob/master/bkg/v2/BKG_v2.0.0.yaml",
    "standard_page": "https://dcsa.org/standards/bill-of-lading/",
}

#: Fields whose DCSA counterpart is a collection (value is a derivation over it).
DERIVED_FIELDS = {"container_count"}

DCSA_FIELD_MAP: Dict[str, Dict[str, Any]] = {
    "shipper": {
        "dcsa_field": "documentParties.shipper",
        "dcsa_object": "Shipper",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Party that issues the Shipping Instructions and is named as shipper on the Transport Document.",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["issuance_readme"],
        "verified_quote": "documentParties ... an object containing a required `Shipper` and optional `Consignee`, `Endorsee` and `other` documentParties",
    },
    "consignee": {
        "dcsa_field": "documentParties.consignee",
        "dcsa_object": "Consignee",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Party to which the goods are consigned on the Transport Document.",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["issuance_readme"],
        "verified_quote": "documentParties ... optional `Consignee`, `Endorsee` and `other` documentParties",
    },
    "notify_party": {
        "dcsa_field": "documentParties.notifyParty",
        "dcsa_object": "NotifyParty",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Party to be notified of the arrival of the goods (party object supporting unstructured addressLines).",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["issuance_readme"],
        "verified_quote": "addressLines added to the following party objects: `Shipper` ... `NotifyParty`, general `Party` and `IssuingParty`",
    },
    "port_of_loading": {
        "dcsa_field": "portOfLoading",
        "dcsa_object": "PortOfLoading",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Port of loading; DCSA location object (UN/LOCODE and/or displayed name).",
        "internal_only": False,
        "code_list": "UN/LOCODE",
        "verified_from": DCSA_SOURCES["bol_spec"],
        "verified_quote": "portOfLoading: $ref: '#/components/schemas/PortOfLoading' (also displayedNameForPortOfLoad)",
    },
    "port_of_discharge": {
        "dcsa_field": "portOfDischarge",
        "dcsa_object": "PortOfDischarge",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Port of discharge; DCSA location object (UN/LOCODE and/or displayed name).",
        "internal_only": False,
        "code_list": "UN/LOCODE",
        "verified_from": DCSA_SOURCES["bol_spec"],
        "verified_quote": "portOfDischarge: $ref: '#/components/schemas/PortOfDischarge' (also displayedNameForPortOfDischarge)",
    },
    "container_count": {
        "dcsa_field": "utilizedTransportEquipments",
        "dcsa_object": "UtilizedTransportEquipment",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "DCSA models each container as one UtilizedTransportEquipment (equipment.equipmentReference, ISOEquipmentCode) - there is no scalar 'number of containers' attribute, so the count is derived.",
        "internal_only": False,
        "derived": "count(utilizedTransportEquipments[])",
        "code_list": "ISO 6346",
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "shippingMarks added to `UtilizedTransportEquipment`; equipmentReference: NARU3472484; ISOEquipmentCode: 22G1",
    },
    "gross_weight_kg": {
        "dcsa_field": "consignmentItems[].cargoItems[].cargoGrossWeight",
        "dcsa_object": "CargoItem",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Gross weight of the cargo item; carries cargoGrossWeightUnit.",
        "internal_only": False,
        "unit_field": "consignmentItems[].cargoItems[].cargoGrossWeightUnit",
        "code_list": None,
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`grossWeight` and `grossVolume` renamed to `cargoGrossWeight` and `cargoGrossVolume` on `CargoItem`",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Document attributes our pipeline surfaces that are not part of the 7 compared
# fields. They are mapped too (the acceptance criteria call out carrier ref,
# HS code and Incoterm) so downstream exports can use DCSA names throughout.
# ─────────────────────────────────────────────────────────────────────────────

DCSA_FIELD_MAP.update({
    "carrier_reference": {
        "dcsa_field": "carrierBookingReference",
        "dcsa_object": "TransportDocument",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "The booking reference assigned by the carrier.",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["bol_spec"],
        "verified_quote": "booked via `carrierBookingReference` = `CBR_123_REGULAR` (ebl/v3 example)",
    },
    "bl_reference": {
        "dcsa_field": "transportDocumentReference",
        "dcsa_object": "TransportDocument",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Unique reference of the Transport Document (B/L number).",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`transportDocumentReference` description updated to reflect `ICS2` requirements",
    },
    "hs_code": {
        "dcsa_field": "consignmentItems[].extendedHSCodes",
        "dcsa_object": "ConsignmentItem",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "HS codes for the consignment item; extendedHSCodes supports up to 12 characters (deprecates HSCodes).",
        "internal_only": False,
        "code_list": "HS",
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`HSCodes` marked as deprecated everywhere, `extendedHSCodes` to be used instead / support up to 12 character codes",
    },
    "incoterm": {
        "dcsa_field": None,
        "dcsa_object": None,
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Incoterms are commercial terms between buyer and seller; the DCSA Bill of Lading (eBL v3) Transport Document does not model an Incoterm attribute.",
        "internal_only": True,
        "related_dcsa_field": "incoTerms",
        "related_dcsa_standard": "DCSA Booking (BKG) v2.0.0 - not part of the Bill of Lading standard",
        "code_list": "ICC Incoterms",
        "verified_from": DCSA_SOURCES["booking_spec"],
        "verified_quote": "incoTerms: Transport obligations, costs and risks as agreed between buyer and seller as defined by Incoterms Rules (bkg/v2 only)",
    },
    "vessel_voyage": {
        "dcsa_field": "transports[].vesselVoyages[]",
        "dcsa_object": "VesselVoyage",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Vessel and voyage of the transport leg (role FIRST_SEA_GOING / MOTHER).",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`vesselVoyage` renamed to `vesselVoyages` in the `Transports` object; `role` added to `VesselVoyage`",
    },
    "freight_payment_term": {
        "dcsa_field": "originChargesPaymentTermCode",
        "dcsa_object": "TransportDocument",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Freight/charge payment term at origin (PRE = Prepaid, COL = Collect); v3 also offers originChargesPaymentTerm with port/haulage/other sub-terms.",
        "internal_only": False,
        "code_list": "DCSA Charge Payment Term",
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`originChargesPaymentTermCode` and `destinationChargesPaymentTermCode` ... can all be either Prepaid (`PRE`) or Collect (`COL`)",
    },
    "place_of_issue": {
        "dcsa_field": "placeOfBLIssue",
        "dcsa_object": "PlaceOfBLIssue",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Place where the Bill of Lading is issued (UN location code or country code).",
        "internal_only": False,
        "code_list": "UN/LOCODE",
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`placeOfBLIssue` structure changed ... a `oneOf` between a `UNLocationCode` and a `countryCode`",
    },
    "invoice_payable_at": {
        "dcsa_field": "invoicePayableAt.UNLocationCode",
        "dcsa_object": "InvoicePayableAt",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Location where the invoice is payable.",
        "internal_only": False,
        "code_list": "UN/LOCODE",
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "`invoicePayableAt` is now an object consisting of a single property: `UNLocationCode` which is required",
    },
    "number_of_originals": {
        "dcsa_field": "numberOfOriginalsWithCharges",
        "dcsa_object": "TransportDocument",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Number of original B/Ls issued (with charges); see also numberOfOriginalsWithoutCharges.",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["issuance_readme"],
        "verified_quote": "corrected many descriptions ... (`numberOfOriginalsWithCharges`, `numberOfOriginalsWithoutCharges` ...)",
    },
    "description_of_goods": {
        "dcsa_field": "consignmentItems[].descriptionOfGoods",
        "dcsa_object": "ConsignmentItem",
        "dcsa_standard": DCSA_STANDARD,
        "definition": "Description of the goods as declared for the consignment item.",
        "internal_only": False,
        "code_list": None,
        "verified_from": DCSA_SOURCES["bol_readme"],
        "verified_quote": "Transport Document changes ... `OuterPackaging`, `packageCode`, `numberOfPackages`",
    },
})


# ─────────────────────────────────────────────────────────────────────────────
# Lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

def _workspace_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def field_terms_path() -> str:
    return os.path.join(_workspace_root(), "data", "field_terms.json")


def internal_field_keys() -> List[str]:
    """Canonical internal field names declared in data/field_terms.json."""
    try:
        with open(field_terms_path(), "r", encoding="utf-8") as fh:
            terms = json.load(fh)
    except (OSError, ValueError):
        return []
    seen: List[str] = []
    for canonical in terms.values():
        if canonical not in seen:
            seen.append(canonical)
    return seen


def mapping_for(field_key: str) -> Dict[str, Any]:
    """Mapping entry for an internal field (or an ``internal_only`` placeholder)."""
    entry = DCSA_FIELD_MAP.get(field_key)
    if entry:
        return dict(entry)
    return {
        "dcsa_field": None,
        "dcsa_object": None,
        "dcsa_standard": DCSA_STANDARD,
        "definition": "No DCSA Bill of Lading equivalent identified for this internal field.",
        "internal_only": True,
        "code_list": None,
        "verified_from": None,
        "verified_quote": None,
    }


def dcsa_field_name(field_key: str) -> Optional[str]:
    """Official DCSA field path, or ``None`` when the field is internal-only."""
    entry = mapping_for(field_key)
    if entry.get("internal_only"):
        return None
    return entry.get("dcsa_field")


def is_internal_only(field_key: str) -> bool:
    return bool(mapping_for(field_key).get("internal_only"))


def all_mappings() -> Dict[str, Dict[str, Any]]:
    return {key: mapping_for(key) for key in DCSA_FIELD_MAP}


def unmapped_internal_fields() -> List[str]:
    """Fields present in field_terms.json with no entry in the catalog at all."""
    return [f for f in internal_field_keys() if f not in DCSA_FIELD_MAP]


def coverage_report() -> Dict[str, Any]:
    """Mapping coverage: how many internal fields map to a real DCSA element."""
    internal = internal_field_keys()
    mapped = [f for f in internal if not is_internal_only(f)]
    internal_only = [f for f in internal if is_internal_only(f)]
    return {
        "standard": DCSA_STANDARD,
        "information_model": DCSA_INFORMATION_MODEL,
        "internal_fields": internal,
        "mapped_to_dcsa": mapped,
        "internal_only": internal_only,
        "catalog_size": len(DCSA_FIELD_MAP),
        "coverage_pct": round(len(mapped) / len(internal) * 100, 1) if internal else 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DCSA-shaped document assembly
# ─────────────────────────────────────────────────────────────────────────────

def _party(value: Any) -> Optional[Dict[str, Any]]:
    """Render a party value as a DCSA party object (partyName + addressLines)."""
    if value is None or str(value).strip() == "":
        return None
    parts = [p.strip() for p in str(value).split(";") if p.strip()]
    party: Dict[str, Any] = {"partyName": parts[0]}
    if len(parts) > 1:
        party["addressLines"] = parts[1:]
    return party


def _location(value: Any, code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Render a location value as a DCSA location object."""
    if value is None or str(value).strip() == "":
        return None
    location: Dict[str, Any] = {}
    if code:
        location["UNLocationCode"] = code
    location["locationName"] = str(value).strip()
    return location


def _first(values: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if values.get(key) not in (None, ""):
            return values[key]
    return None


def to_dcsa_document(values: Dict[str, Any], port_codes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Nest internal field values under their official DCSA object/field names.

    ``values`` is ``{internal_field: value}``; ``port_codes`` may supply resolved
    UN/LOCODEs, e.g. ``{"port_of_discharge": "LTKLJ"}``.

    Only fields with a DCSA mapping are emitted. Internal-only fields (such as
    Incoterm, which the DCSA Bill of Lading standard does not model) are reported
    by the caller in a separate, clearly-labelled envelope - never smuggled into
    the DCSA structure under an invented name.
    """
    port_codes = port_codes or {}
    td: Dict[str, Any] = {}

    carrier_ref = _first(values, "carrier_reference", "booking_reference")
    if carrier_ref:
        td["carrierBookingReference"] = carrier_ref
    doc_ref = _first(values, "bl_reference", "transport_document_reference")
    if doc_ref:
        td["transportDocumentReference"] = doc_ref

    parties: Dict[str, Any] = {}
    for field_key, dcsa_key in (("shipper", "shipper"), ("consignee", "consignee"),
                               ("notify_party", "notifyParty")):
        party = _party(values.get(field_key))
        if party:
            parties[dcsa_key] = party
    if parties:
        td["documentParties"] = parties

    pol = _location(values.get("port_of_loading"), port_codes.get("port_of_loading"))
    pod = _location(values.get("port_of_discharge"), port_codes.get("port_of_discharge"))
    if pol:
        td["portOfLoading"] = pol
    if pod:
        td["portOfDischarge"] = pod

    if values.get("place_of_issue"):
        td["placeOfBLIssue"] = _location(values["place_of_issue"])
    if values.get("invoice_payable_at"):
        td["invoicePayableAt"] = _location(values["invoice_payable_at"])
    if values.get("number_of_originals") not in (None, ""):
        td["numberOfOriginalsWithCharges"] = values["number_of_originals"]

    freight = values.get("freight_payment_term")
    if freight:
        text = str(freight).strip().upper()
        if "PREPAID" in text or text == "PRE":
            td["originChargesPaymentTermCode"] = "PRE"
        elif "COLLECT" in text or text == "COL":
            td["originChargesPaymentTermCode"] = "COL"

    cargo_item: Dict[str, Any] = {}
    if values.get("gross_weight_kg") not in (None, ""):
        cargo_item["cargoGrossWeight"] = values["gross_weight_kg"]
        cargo_item["cargoGrossWeightUnit"] = "KGM"
    consignment_item: Dict[str, Any] = {}
    if cargo_item:
        consignment_item["cargoItems"] = [cargo_item]
    if values.get("hs_code"):
        consignment_item["extendedHSCodes"] = [str(values["hs_code"]).strip()]
    if values.get("description_of_goods"):
        consignment_item["descriptionOfGoods"] = values["description_of_goods"]
    if consignment_item:
        td["consignmentItems"] = [consignment_item]

    # DCSA models each container as one UtilizedTransportEquipment, so a container
    # count is expressed as that many entries (the count is the derivation).
    count = values.get("container_count")
    if count not in (None, ""):
        try:
            n = int(float(count))
        except (TypeError, ValueError):
            n = 0
        if n > 0:
            td["utilizedTransportEquipments"] = [{"equipment": {}} for _ in range(n)]

    vessel_name = values.get("vessel_name")
    voyage = values.get("voyage_number")
    vessel_voyage = values.get("vessel_voyage")
    if vessel_voyage or vessel_name or voyage:
        entry: Dict[str, Any] = {}
        if vessel_name:
            entry["vesselName"] = str(vessel_name)
        if voyage:
            entry["carrierVoyageNumber"] = str(voyage)
        if not entry and vessel_voyage:
            entry["vesselName"] = str(vessel_voyage)
        td["transports"] = [{"vesselVoyages": [entry]}]

    return {"transportDocument": td}
