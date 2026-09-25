import os
import sys

from backend.services.automation import automation, field_confidence, signals_from_matrix_row
from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.dataset_loader import loader

emails = loader.load_inbox()
summaries = []
for e in emails:
    c = classifier.classify(e)
    if c['is_comparison_request']:
        v = comparator.compare_documents('', '', email_metadata=e)
        summaries.append({'verification': v})

print("=" * 65)
for l in range(4):
    p = automation.preview(summaries, l, use_cache=False)
    print(f"Level L{l}:")
    print(f"  Automation Rate   : {p['auto_processed_pct']}%  ({p['counts']['auto_processed']} / {p['counts']['fields']} fields)")
    print(f"  Error Exposure    : {p['estimated_error_exposure_pct']}%")
    print(f"  Time Saved        : {p['estimated_time_saved_minutes']} min")
    print(f"  Files For Review  : {p['files_for_review']} files ({p['files_for_review_pct']}%)")
print("=" * 65)
