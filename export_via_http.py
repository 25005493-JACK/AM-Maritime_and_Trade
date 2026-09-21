# -*- coding: utf-8 -*-
"""
Exports API data over HTTP from running server on localhost:8000 to frontend/public/api
"""
import os
import json
import urllib.request

base_url = "http://localhost:8000"
public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "public")
api_dir = os.path.join(public_dir, "api")
emails_dir = os.path.join(api_dir, "emails")

os.makedirs(api_dir, exist_ok=True)
os.makedirs(emails_dir, exist_ok=True)

endpoints = [
    ("/api/emails", "emails.json"),
    ("/api/analytics", "analytics.json"),
    ("/api/calendar", "calendar.json"),
    ("/api/reflections", "reflections.json"),
    ("/api/dcsa/analytics", "dcsa_analytics.json"),
    ("/api/ocr/dashboard", "ocr_dashboard.json"),
    ("/api/settings/automation-level", "automation_level.json"),
    ("/api/routing-policy", "routing_policy.json"),
]

for endpoint, filename in endpoints:
    try:
        url = base_url + endpoint
        req = urllib.request.Request(url, headers={'User-Agent': 'Exporter'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(os.path.join(api_dir, filename), "wb") as f:
                f.write(data)
            print(f"Exported {endpoint} -> {filename} ({len(data)} bytes)")
    except Exception as e:
        print(f"Failed {endpoint}: {e}")

# Fetch priority emails details
with open(os.path.join(api_dir, "emails.json"), "r", encoding="utf-8") as f:
    emails = json.load(f)

# Priority: all with verification status + first 25
priority_ids = [e["id"] for e in emails if (e.get("verification") or {}).get("status")]
priority_ids.extend([e["id"] for e in emails[:25]])
priority_ids = list(dict.fromkeys(priority_ids))

print(f"Exporting details for {len(priority_ids)} emails...")
count = 0
for eid in priority_ids:
    try:
        url = f"{base_url}/api/emails/{eid}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Exporter'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            with open(os.path.join(emails_dir, f"{eid}.json"), "wb") as f:
                f.write(data)
            count += 1
    except Exception as e:
        print(f"Err {eid}: {e}")

print(f"Successfully exported {count} email details!")

# Copy presentation.html to public
presentation_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation.html")
presentation_dest = os.path.join(public_dir, "presentation.html")
if os.path.exists(presentation_src):
    with open(presentation_src, "r", encoding="utf-8") as src, open(presentation_dest, "w", encoding="utf-8") as dst:
        dst.write(src.read())
    print("Copied presentation.html to frontend/public/presentation.html")

print("Done exporting static data!")
