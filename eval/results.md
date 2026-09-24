# Evaluation Results

- **Mode**: `rules_plus_llm`
- **Split**: `heldout`
- **Total evaluated**: 159

## 1. Classification (5-category Macro-F1)

**Macro-F1: 1.0000**

| Category | Precision | Recall | F1 | Support |
|----------|-----------|--------|-----|---------|
| BL_COMPARISON | 1.0000 | 1.0000 | 1.0000 | 40 |
| GENERAL | 1.0000 | 1.0000 | 1.0000 | 39 |
| INVOICE_QUERY | 1.0000 | 1.0000 | 1.0000 | 25 |
| SI_REQUEST | 1.0000 | 1.0000 | 1.0000 | 43 |
| SPAM | 1.0000 | 1.0000 | 1.0000 | 12 |

## 2. Status Accuracy (OK / MISMATCH / NEEDS_REVIEW)

**Accuracy: 1.0000** | **Macro-F1: 1.0000**

| Status | Precision | Recall | F1 | Support |
|--------|-----------|--------|-----|---------|
| MISMATCH | 1.0000 | 1.0000 | 1.0000 | 12 |
| NEEDS_REVIEW | 1.0000 | 1.0000 | 1.0000 | 7 |
| OK | 1.0000 | 1.0000 | 1.0000 | 140 |

## 3. Field-Level Defect Detection

**Aggregate — Precision: 1.0000 | Recall: 0.2462 | F1: 0.3951**

| Field | TP | FP | FN | TN | Precision | Recall | F1 |
|-------|----|----|----|----|-----------|--------|-----|
| shipper | 1 | 0 | 7 | 32 | 1.0000 | 0.1250 | 0.2222 |
| consignee | 2 | 0 | 7 | 31 | 1.0000 | 0.2222 | 0.3636 |
| notify_party | 4 | 0 | 7 | 29 | 1.0000 | 0.3636 | 0.5333 |
| port_of_loading | 0 | 0 | 7 | 33 | 0.0000 | 0.0000 | 0.0000 |
| port_of_discharge | 0 | 0 | 7 | 33 | 0.0000 | 0.0000 | 0.0000 |
| container_count | 7 | 0 | 7 | 26 | 1.0000 | 0.5000 | 0.6667 |
| gross_weight_kg | 2 | 0 | 7 | 31 | 1.0000 | 0.2222 | 0.3636 |

## 4. Critical Errors

- **Missed discrepancies** (predicted OK, truly MISMATCH): **0**
- **Incorrect auto-approvals** (predicted OK, truly defective): **0**

## 5. Human Review & Escalation

- **Human review rate**: 17.50% (7/40 BL comparisons)
- **Escalation reason accuracy**: 100.00% (7 evaluated)
