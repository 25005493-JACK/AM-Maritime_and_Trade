import json
from pathlib import Path
from collections import defaultdict

inbox = Path('test data/inbox')
attachments_dir = Path('test data/attachments')
with open('submission.json', encoding='utf-8') as f:
    submission = json.load(f)

# Get BL_COMPARISON emails with their details
bl_emails = []
for eid, sub in submission.items():
    if sub['category'] != 'BL_COMPARISON':
        continue
    fp = inbox / f'{eid}.json'
    if fp.exists():
        with open(fp, encoding='utf-8') as f:
            email = json.load(f)
        atts = email.get('attachments', [])
        bl_emails.append({
            'id': eid,
            'from': email.get('from',''),
            'subject': email.get('subject',''),
            'status': sub.get('status',''),
            'defects': sub.get('defects', []),
            'reason': sub.get('reason',''),
            'att_count': len(atts),
            'attachments': atts
        })

# Show distribution
print('=== BL_COMPARISON STATUS BREAKDOWN ===')
status_counts = defaultdict(int)
for e in bl_emails:
    status_counts[e['status']] += 1
for s, c in sorted(status_counts.items()):
    print(f'  {s}: {c}')

# Show NEEDS_REVIEW cases
print('\n=== NEEDS_REVIEW BL_COMPARISON EMAILS ===')
for e in bl_emails:
    if e['status'] == 'NEEDS_REVIEW':
        print(f"  {e['id']}: from={e['from']}, atts={e['att_count']}, reason={e['reason']}")
        print(f"    subject: {e['subject'][:80]}")
        print(f"    defects: {e['defects']}")

# Show MISMATCH samples with defect fields
print('\n=== SAMPLE MISMATCH EMAILS (first 8) ===')
mismatch = [e for e in bl_emails if e['status'] == 'MISMATCH'][:8]
for e in mismatch:
    print(f"  {e['id']}: from={e['from']}, defects={e['defects']}")
    print(f"    subject: {e['subject'][:80]}")

# Show zero-attachment BL_COMPARISON
print('\n=== ZERO-ATTACHMENT BL_COMPARISON ===')
for e in bl_emails:
    if e['att_count'] == 0:
        print(f"  {e['id']}: from={e['from']}, status={e['status']}")
        print(f"    subject: {e['subject'][:100]}")

# Group by sender domain for client chips
print('\n=== SENDERS IN BL_COMPARISON ===')
sender_domains = defaultdict(lambda: defaultdict(int))
for e in bl_emails:
    domain = e['from'].split('@')[-1] if '@' in e['from'] else 'unknown'
    sender_domains[domain][e['status']] += 1
for domain, statuses in sorted(sender_domains.items(), key=lambda x: -sum(x[1].values()))[:8]:
    total = sum(statuses.values())
    print(f"  {domain} ({total}): {dict(statuses)}")
