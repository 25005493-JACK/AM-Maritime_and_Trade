import csv
import json
import os
import sys
sys.path.insert(0, ".")
from collections import defaultdict
from backend.services.reflection import extract_domain

for split in ['dev', 'heldout']:
    path = f'eval/labels/{split}_split.csv'
    with open(path, 'r', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    senders = defaultdict(list)
    for r in rows:
        eid = r['email_id']
        with open(f'test data/inbox/{eid}.json', 'r', encoding='utf-8') as ef:
            email = json.load(ef)
        s = email.get('sender') or email.get('from') or 'unknown'
        d = extract_domain(s)
        senders[d].append((r['email_id'], r['category'], r['expected_status'], r['defect_fields']))
    print(f'=== {split} ({len(rows)} emails, {len(senders)} domains) ===')
    for d, items in sorted(senders.items(), key=lambda x: -len(x[1]))[:12]:
        statuses = set(x[2] for x in items)
        defects = set(x[3] for x in items if x[3])
        print(f'  {d:32s}: {len(items):2d} emails | statuses: {statuses} | defects: {defects}')
