# -*- coding: utf-8 -*-
"""
Exports backend API responses to static JSON files in frontend/public/api
so that the Netlify deployment is 100% functional standalone.
"""
import os
import urllib.request
import json

base_url = "http://127.0.0.1:8000"
public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "public")
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
    ("/api/self-evaluate", "self_evaluate.json"),
    ("/api/submission.json", "submission.json"),
]

for endpoint, filename in endpoints:
    url = base_url + endpoint
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            # Save as both filename and without extension
            target_file = os.path.join(api_dir, filename)
            with open(target_file, "wb") as f:
                f.write(data)
            # Save as exact endpoint name without .json if not a directory
            base_name = os.path.splitext(filename)[0]
            target_noext = os.path.join(api_dir, base_name)
            if not os.path.isdir(target_noext):
                with open(target_noext, "wb") as f:
                    f.write(data)
            print(f"Exported {endpoint} -> {target_file}")
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")

# Fetch all email details for sample emails
try:
    with open(os.path.join(api_dir, "emails.json"), "r", encoding="utf-8") as f:
        emails = json.load(f)
    print(f"Exporting details for {len(emails)} emails...")
    for e in emails:
        eid = e["id"]
        detail_url = f"{base_url}/api/emails/{eid}"
        try:
            req = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp:
                detail_data = resp.read()
                with open(os.path.join(emails_dir, f"{eid}.json"), "wb") as df:
                    df.write(detail_data)
                with open(os.path.join(emails_dir, eid), "wb") as df:
                    df.write(detail_data)
        except Exception as err:
            pass
    print("Email details exported successfully!")
except Exception as e:
    print(f"Error exporting email details: {e}")

# Copy presentation deck to frontend/public
presentation_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation.html")
presentation_dest = os.path.join(public_dir, "presentation.html")
if os.path.exists(presentation_src):
    with open(presentation_src, "r", encoding="utf-8") as src, open(presentation_dest, "w", encoding="utf-8") as dst:
        dst.write(src.read())
    print("Copied presentation.html to frontend/public/presentation.html")

print("All static API exports complete!")
