#!/usr/bin/env python3
"""
split.py — Deterministic stratified split of labelled data into dev and held-out.

Reads:   eval/labels/ground_truth.csv
Writes:  eval/labels/dev_split.csv
         eval/labels/heldout_split.csv

Stratification key: (category, expected_status)
Split ratio: 70 % dev, 30 % held-out
Fixed seed: 42  (NEVER change this after the first run)

Held-out is NEVER used to change rules, prompts, or thresholds.
Only dev may be used for iterative improvement.

Usage:
    python eval/split.py
"""

import csv
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

SEED = 42
DEV_FRACTION = 0.70

ROOT = Path(__file__).resolve().parent.parent
LABELS_DIR = ROOT / "eval" / "labels"
GT_PATH = LABELS_DIR / "ground_truth.csv"
DEV_PATH = LABELS_DIR / "dev_split.csv"
HELDOUT_PATH = LABELS_DIR / "heldout_split.csv"


def main():
    if not GT_PATH.exists():
        print(f"ERROR: Ground truth file not found: {GT_PATH}")
        print("Run 'python eval/generate_labelling_template.py' first, then fill in labels.")
        sys.exit(1)

    with open(GT_PATH, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        print("ERROR: ground_truth.csv is empty.")
        sys.exit(1)

    # Validate required columns
    required = {"email_id", "category", "expected_status"}
    missing = required - set(fieldnames or [])
    if missing:
        print(f"ERROR: Missing required columns: {missing}")
        sys.exit(1)

    # Validate all rows have category and expected_status filled
    incomplete = [
        r["email_id"]
        for r in rows
        if not r.get("category", "").strip() or not r.get("expected_status", "").strip()
    ]
    if incomplete:
        print(f"ERROR: {len(incomplete)} rows have empty category or expected_status.")
        print(f"  First few: {incomplete[:5]}")
        sys.exit(1)

    # Stratify by (category, expected_status)
    strata = defaultdict(list)
    for row in rows:
        key = (row["category"].strip(), row["expected_status"].strip())
        strata[key].append(row)

    dev_rows = []
    heldout_rows = []
    rng = random.Random(SEED)

    for key in sorted(strata.keys()):
        group = strata[key]
        rng.shuffle(group)
        n_dev = max(1, int(len(group) * DEV_FRACTION))  # at least 1 in dev
        # If only 1 sample in stratum, put it in dev (can't evaluate held-out anyway)
        if len(group) == 1:
            dev_rows.extend(group)
            continue
        dev_rows.extend(group[:n_dev])
        heldout_rows.extend(group[n_dev:])

    # Sort by email_id for reproducibility
    dev_rows.sort(key=lambda r: r["email_id"])
    heldout_rows.sort(key=lambda r: r["email_id"])

    # Write dev split
    with open(DEV_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dev_rows)

    # Write held-out split
    with open(HELDOUT_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(heldout_rows)

    # Summary
    print(f"[OK] Stratified split complete (seed={SEED}, dev={DEV_FRACTION*100:.0f}%)")
    print(f"    Total:    {len(rows)}")
    print(f"    Dev:      {len(dev_rows)}  ->  {DEV_PATH}")
    print(f"    Held-out: {len(heldout_rows)}  ->  {HELDOUT_PATH}")
    print()
    print("Stratum distribution:")
    for key in sorted(strata.keys()):
        n = len(strata[key])
        n_dev = len([r for r in dev_rows if (r["category"].strip(), r["expected_status"].strip()) == key])
        n_ho = len([r for r in heldout_rows if (r["category"].strip(), r["expected_status"].strip()) == key])
        print(f"  {key[0]:20s} / {key[1]:14s} : {n:>4} total  ({n_dev} dev, {n_ho} held-out)")


if __name__ == "__main__":
    main()
