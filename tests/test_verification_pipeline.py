import pytest
from backend.services.classifier import classifier
from backend.services.extractor import extractor
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator

def test_email_classification():
    spam_email = {
        "subject": "Discount on office stationery!",
        "body": "Click here to claim coupon for 50% discount",
        "attachments": []
    }
    res_spam = classifier.classify(spam_email)
    assert res_spam["super_category"] == "Spam / General"
    assert res_spam["is_comparison_request"] is False

    doc_email = {
        "subject": "Draft BL check for SI #8801",
        "body": "Please cross check SI and draft BL",
        "attachments": [
            {"filename": "SI.txt", "doc_type": "SI"},
            {"filename": "BL.txt", "doc_type": "BL"}
        ]
    }
    res_doc = classifier.classify(doc_email)
    assert res_doc["super_category"] == "Documentation (SI & BL)"
    assert res_doc["ui_tag"] == "Document Comparison Request"
    assert res_doc["is_comparison_request"] is True

def test_field_extraction_and_alias_normalization():
    sample_text = """
    SHIPPING INSTRUCTION
    Shipper: Global Traders Inc, Singapore
    Consignee: European Distribution Ltd
    Notify Party: Euro Logistics BV
    Load Port: Singapore (SGSIN)
    Discharge Port: Rotterdam (NLRTM)
    Container Summary: 3 containers
    Gross Weight: 22.0 Metric Tons
    """
    fields = extractor.extract_fields(sample_text, doc_type="SI")
    assert fields["shipper"] == "Global Traders Inc, Singapore"
    assert fields["consignee"] == "European Distribution Ltd"
    assert fields["notify_party"] == "Euro Logistics BV"
    assert fields["port_of_loading"] == "Singapore (SGSIN)"
    assert fields["port_of_discharge"] == "Rotterdam (NLRTM)"
    assert fields["container_count"] == 3
    assert fields["gross_weight_kg"] == 22000.0

def test_document_comparator_mismatch():
    si_text = """
    Shipper: Global Traders Inc
    Consignee: European Distribution Ltd
    Notify Party: Euro Logistics BV
    Port of Loading: Singapore (SGSIN)
    Port of Discharge: Rotterdam (NLRTM)
    Container Count: 3 containers
    Gross Weight: 22000 kg
    """
    bl_text = """
    Shipper: Global Traders Inc
    Consignee: European Distribution Ltd
    Notify Party: Euro Logistics BV
    Load Port: Singapore (SGSIN)
    Discharge Port: Rotterdam (NLRTM)
    Container Count: 4 containers
    Gross Weight: 22000 kg
    """
    comp = comparator.compare_documents(si_text, bl_text)
    assert comp["status"] == "MISMATCH_DETECTED"
    assert "container_count" in comp["mismatched_fields"]
    assert "SI: 3 / BL: 4" in comp["summary_message"] or "Container Count" in comp["summary_message"]

def test_document_comparator_human_review():
    si_text = """
    Shipper: Fast Freight GmbH
    Consignee: Tokyo Import Corp
    Notify Party: Nippon Logistics KK
    Port of Loading: Hamburg
    Port of Discharge: Tokyo
    Container Count: 1 container
    Gross Weight: 12400 kg
    """
    bl_text_damaged = """
    [OCR SCAN RESULT - QUALITY SCORE: 0.34]
    Shipper: Fast Freight GmbH
    Consignee: Tokyo Import Corp
    Notify Party: Nippon Logistics KK
    Port of Loading: Hamburg
    Port of Discharge: Tokyo
    Container Count: 1 container
    GROSS WEIGHT: [ERROR: OCR_CORRUPTED_STREAM_UNCERTAIN_WEIGHT_VALUE_0x99A?] kg
    """
    comp = comparator.compare_documents(si_text, bl_text_damaged)
    assert comp["status"] == "HUMAN_REVIEW_REQUIRED"
    assert comp["requires_human_review"] is True
    assert len(comp["human_review_reasons"]) > 0

def test_self_evaluation_endpoint():
    ground_truth = evaluator.process_all_emails()
    assert len(ground_truth) >= 10
    score_report = evaluator.evaluate_submission(ground_truth)
    assert score_report["overall_score"] == 100.0
    assert score_report["classification_accuracy_pct"] == 100.0

def test_vessel_calendar_port_filtering():
    from backend.services.calendar_service import calendar_service
    
    # Global view (ALL)
    all_vessels = calendar_service.get_calendar("ALL")
    assert len(all_vessels) >= 5

    # Filter by Rotterdam
    rotterdam_vessels = calendar_service.get_calendar("Rotterdam (NLRTM)")
    assert len(rotterdam_vessels) >= 1
    assert all("Rotterdam" in v["destination_port"] for v in rotterdam_vessels)

    # Filter by Hamburg
    hamburg_vessels = calendar_service.get_calendar("Hamburg (DEHAM)")
    assert len(hamburg_vessels) >= 1
    assert all("Hamburg" in v["destination_port"] for v in hamburg_vessels)
    # Ensure Rotterdam ship MSC ISABELLA is NOT in Hamburg view (Strict Port Filtering)
    assert not any(v["vessel_name"] == "MSC ISABELLA" for v in hamburg_vessels)

