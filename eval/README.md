# eval/ — Independent Evaluation Framework

This directory provides a **rigorous, ground-truth-based evaluation** of the
DocuMatch shipping-document verification pipeline. It replaces the old
self-referencing `run_self_eval.py` (now relabelled as a consistency check).

## ⚠️ Critical Design Principles

1. **No fabricated labels.** Ground truth must be provided by a human annotator
   who reads the original SI and BL documents. LLM-generated labels are forbidden.
2. **No fixed score components.** Every metric is computed solely by comparing
   predictions to labels. There are no hard-coded baselines or inflated numbers.
3. **Held-out data is sacred.** The held-out split (`heldout_split.csv`) must
   NEVER be used to tune rules, prompts, or thresholds. Only `dev_split.csv`
   may be used for iterative development.

## Workflow

### Step 1: Generate Labelling Template

```bash
python eval/generate_labelling_template.py
```

This creates `eval/labels/labelling_template.csv` with 520 rows (one per email).
Reference fields (shipper, consignee, etc.) are pre-populated from the raw
attachment text as visual aids.

### Step 2: Human Annotation

Open `labelling_template.csv` in Excel/Google Sheets and fill in:

| Column | Values | Notes |
|--------|--------|-------|
| `category` | `BL_COMPARISON`, `SI_REQUEST`, `INVOICE_QUERY`, `GENERAL`, `SPAM` | Required for all |
| `shipper_match` … `gross_weight_match` | `TRUE`, `FALSE`, `NA` | For BL_COMPARISON only |
| `defect_fields` | Comma-separated: `consignee,notify_party` | Empty if all match |
| `expected_status` | `OK`, `MISMATCH`, `NEEDS_REVIEW` | Required for all |
| `review_reason` | `missing_attachment`, `corrupted_file`, `wrong_doc_type`, `scanned_not_processed`, `missing_value`, `term_unresolved`, `other` | Only if NEEDS_REVIEW |

Save as `eval/labels/ground_truth.csv`.

### Step 3: Stratified Split

```bash
python eval/split.py
```

Produces:
- `eval/labels/dev_split.csv` (70% — for iterative development)
- `eval/labels/heldout_split.csv` (30% — for final reporting only)

Seed is fixed at 42. Stratified by `(category, expected_status)`.

### Step 4: Evaluate

```bash
# Evaluate on dev split (default — for iterative work)
python eval/evaluate.py --mode rules_only --split dev

# Evaluate on held-out split (final reporting only)
python eval/evaluate.py --mode rules_only --split heldout

# Evaluate with LLM augmentation
python eval/evaluate.py --mode rules_plus_llm --split dev
```

Outputs:
- `eval/results.json` — machine-readable
- `eval/results.md` — human-readable markdown table

## Metrics Reported

| Metric | Description |
|--------|-------------|
| **Classification Macro-F1** | Across all 5 email categories |
| **Status Accuracy** | OK / MISMATCH / NEEDS_REVIEW prediction accuracy |
| **Status Macro-F1** | F1 per status class |
| **Field-Level P/R/F1** | Per-field defect detection (7 fields) |
| **Aggregate Field P/R/F1** | Micro-averaged across all field comparisons |
| **Missed Discrepancies** | Predicted OK but truly MISMATCH (dangerous!) |
| **Incorrect Auto-Approvals** | Predicted OK but truly defective |
| **Human Review Rate** | Fraction of BL emails routed to NEEDS_REVIEW |
| **Escalation Reason Accuracy** | For NEEDS_REVIEW cases, was the reason correct? |

## File Structure

```
eval/
├── README.md                          ← this file
├── generate_labelling_template.py     ← creates empty template for annotation
├── split.py                           ← deterministic stratified split
├── evaluate.py                        ← main evaluation script
├── labels/
│   ├── labelling_template.csv         ← generated template (DO NOT evaluate on this)
│   ├── ground_truth.csv               ← human-filled labels (create from template)
│   ├── dev_split.csv                  ← 70% for development
│   └── heldout_split.csv              ← 30% for final reporting
├── results.json                       ← evaluation output (machine-readable)
└── results.md                         ← evaluation output (human-readable)
```

## What About `run_self_eval.py`?

The old `run_self_eval.py` at the project root has been relabelled as a
**consistency check** (renamed to `run_consistency_check.py`). It verifies that
the pipeline runs end-to-end without crashes and reports internal metrics, but
it does NOT provide independent ground-truth evaluation. It is NOT a substitute
for this framework.
