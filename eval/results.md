# Evaluation Results

- **Mode**: `rules_only`
- **Split**: `all`
- **Total evaluated**: 520

## 1. Classification (5-category Macro-F1)

**Macro-F1: 0.9984**

| Category | Precision | Recall | F1 | Support |
|----------|-----------|--------|-----|---------|
| BL_COMPARISON | 0.9923 | 1.0000 | 0.9961 | 129 |
| GENERAL | 1.0000 | 0.9923 | 0.9961 | 130 |
| INVOICE_QUERY | 1.0000 | 1.0000 | 1.0000 | 83 |
| SI_REQUEST | 1.0000 | 1.0000 | 1.0000 | 141 |
| SPAM | 1.0000 | 1.0000 | 1.0000 | 37 |

## 2. Status Accuracy (OK / MISMATCH / NEEDS_REVIEW)

**Accuracy: 0.9981** | **Macro-F1: 0.9886**

| Status | Precision | Recall | F1 | Support |
|--------|-----------|--------|-----|---------|
| MISMATCH | 0.9787 | 1.0000 | 0.9892 | 46 |
| NEEDS_REVIEW | 1.0000 | 0.9545 | 0.9767 | 22 |
| OK | 1.0000 | 1.0000 | 1.0000 | 452 |

## 3. Field-Level Defect Detection

**Aggregate — Precision: 0.8649 | Recall: 0.2963 | F1: 0.4414**

| Field | TP | FP | FN | TN | Precision | Recall | F1 |
|-------|----|----|----|----|-----------|--------|-----|
| shipper | 7 | 0 | 22 | 100 | 1.0000 | 0.2414 | 0.3889 |
| consignee | 7 | 0 | 21 | 101 | 1.0000 | 0.2500 | 0.4000 |
| notify_party | 11 | 0 | 22 | 96 | 1.0000 | 0.3333 | 0.5000 |
| port_of_loading | 4 | 2 | 22 | 101 | 0.6667 | 0.1538 | 0.2500 |
| port_of_discharge | 5 | 8 | 22 | 94 | 0.3846 | 0.1852 | 0.2500 |
| container_count | 19 | 0 | 21 | 89 | 1.0000 | 0.4750 | 0.6441 |
| gross_weight_kg | 11 | 0 | 22 | 96 | 1.0000 | 0.3333 | 0.5000 |

## 4. Critical Errors

- **Missed discrepancies** (predicted OK, truly MISMATCH): **0**
- **Incorrect auto-approvals** (predicted OK, truly defective): **0**

## 5. Human Review & Escalation

- **Human review rate**: 16.28% (21/129 BL comparisons)
- **Escalation reason accuracy**: 95.45% (22 evaluated)
