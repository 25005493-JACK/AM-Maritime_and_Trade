# Averish Shipping AI

An inbox-to-discrepancy-report prototype for shipping operations. It finds emails asking for a document check, compares a Shipping Instruction (SI) with a draft Bill of Lading (BL), and shows the evidence a reviewer needs to act.

## Problem statement

Shipping teams receive document checks, new SI requests, invoice questions, operational updates, and spam in the same inbox. Staff must first find the requests that need verification, then compare the SI (the reference) against the draft BL. Manual checks are repetitive, and a missed difference in a name, port, container count, or weight can cause corrections and delays. The same field may also have different labels or formatting in the two documents. The supplied use case asks for classification, seven-field comparison, a clear discrepancy report, and human review when the evidence is incomplete or unreliable.

## Solution

The application provides a searchable operations inbox and a verification pipeline:

- A rule-based classifier sorts emails into `BL_COMPARISON`, `SI_REQUEST`, `INVOICE_QUERY`, `GENERAL`, and `SPAM`. Only comparison requests proceed to SI/BL checking.
- The attachment reader supports TXT, PDF, DOCX, and XLSX. PyMuPDF reads searchable PDF text and calls Tesseract OCR through PyMuPDF for pages with too little text. The repository includes an English OCR language model.
- A field extractor maps varied document labels to seven shipment fields: shipper, consignee, notify party, port of loading, port of discharge, container count, and gross weight in kilograms.
- The comparator uses the SI as the reference and reports `OK`, `MISMATCH`, or `NEEDS_REVIEW`. Its field matrix shows SI and BL values side by side and identifies exact, normalized, or fuzzy matches.
- Cases with missing attachments, unreadable files, wrong document types, or missing required values go to human review. A reviewer can correct extracted fields and rerun the comparison.

The React interface includes the inbox, SI/BL inspector, human review queue, shipment timeline, vessel calendar, analytics, a self-evaluation view, and a PDF OCR dashboard at `/dashboard`. It has light and dark themes.

## Project flow

1. Load email JSON records and referenced attachments from `test data/` (or the bundled fallback data).
2. Classify each email using its subject, body, and attachment metadata.
3. For a comparison request, identify the SI and draft BL, read their text, and extract the seven fields.
4. Check attachment and field completeness before comparing values. Escalate uncertain cases with a reason.
5. Compare each BL field against its SI counterpart. Show the outcome, differing fields, source text, and suggested next step in the inspector.
6. Let a reviewer correct a value when needed; recompute the result and record a correction event when DuckDB is available.

## System architecture

```mermaid
flowchart LR
    A[Email JSON and attachments] --> B[DatasetLoader]
    B --> C[EmailClassifier]
    C -->|BL comparison| D[Attachment reader]
    D --> E[TXT / DOCX / XLSX text]
    D --> F[PyMuPDF text layer or OCR]
    E --> G[Seven-field extractor]
    F --> G
    G --> H[SI vs BL comparator]
    H --> I[OK / MISMATCH / NEEDS_REVIEW]
    I --> J[FastAPI]
    C --> J
    J --> K[React operations UI]
    K -->|review correction| L[In-memory override]
    L --> H
    L --> M[DuckDB review event log]
    B --> N[PDF OCR dashboard service]
    N --> J
```

The backend is Python/FastAPI; the frontend is React, Vite, and Tailwind CSS. Original attachments remain on disk. Extracted attachment text and PDF results are cached in the backend process, while reviewer overrides are held in memory. These caches and overrides reset on restart. The optional DuckDB event log supports timeline and review history; it is not the store for extracted text.

## Wow factor

- **Evidence-first discrepancy view:** Each of the seven checks shows the SI reference, BL value, and match type, so a reviewer can see exactly what differed.
- **Useful escalation:** Missing or unreadable evidence becomes `NEEDS_REVIEW` with a reason, rather than an ungrounded match decision.
- **Mixed-format intake:** The same pipeline handles text files, office documents, searchable PDFs, and scanned PDF pages.
- **OCR observability:** `/dashboard` lists PDF attachments by email number, the extracted text, processing method, field coverage, and an OCR agreement benchmark where a searchable text layer exists.
- **Operations context:** The inbox, review queue, timeline, calendar, and analytics connect document checks to day-to-day shipment work.

## DCSA Bill of Lading alignment

Extracted and reviewer-confirmed fields are expressed with **DCSA Bill of Lading (eBL) field names** instead of a format we invented, so the output can be read by any DCSA-aware system. Field names come from DCSA's public specification repository (`dcsaorg/DCSA-OpenAPI`, eBL/Bill of Lading v3.0.3 and the eBL Issuance v3.0.3 docs); every mapping entry stores the DCSA document and the exact wording it was verified from.

| Internal field | DCSA field |
| --- | --- |
| `shipper` | `documentParties.shipper` |
| `consignee` | `documentParties.consignee` |
| `notify_party` | `documentParties.notifyParty` |
| `port_of_loading` | `portOfLoading` |
| `port_of_discharge` | `portOfDischarge` |
| `container_count` | `utilizedTransportEquipments[]` (count is a derivation; DCSA models one entry per container) |
| `gross_weight_kg` | `consignmentItems[].cargoItems[].cargoGrossWeight` |
| `hs_code` | `consignmentItems[].extendedHSCodes` |
| `carrier_reference` | `carrierBookingReference` |
| `incoterm` | *no Bill of Lading equivalent* - flagged `internal_only` (DCSA models Incoterms in the Booking standard as `incoTerms`) |

Each field's evidence record contains the value, the sources (`document`, `char_offset`, `exact_text`), mechanical validation (`source_match`, whitelist lookup against UN/LOCODE or ISO 6346) and an `agreement` of `match` or `conflict`. It is evidence, not a certificate: there is no hash, no signature, and no claim of legal validity.

**Propose and confirm:** when the SI and the draft BL disagree the pipeline never picks a winner. `GET /api/shipments/{id}/corrections` returns both candidate values with their quoted source text; `POST /api/corrections/resolve` accepts an explicit reviewer decision (`si`, `bl`, or a third value) and writes a DCSA-structured `resolved_bl` record plus a corrections row that records **which DCSA field** was involved. Undecided conflicts stay in `pending_decisions` and are never auto-filled.

```bash
python demo_dcsa_conflict.py                                   # evidence only, nothing resolved
python demo_dcsa_conflict.py --field consignee --choose si     # reviewer picks the SI value
python demo_dcsa_conflict.py --choose custom --value "..."     # reviewer supplies a third value
```

Relevant endpoints: `GET /api/dcsa/mapping` (catalog + coverage + provenance), `GET /api/dcsa/analytics` (corrections grouped by DCSA field), `GET /api/shipments/{id}/resolved` (or `?download=true` for the `.dcsa.json` export).

## Trust features: reasoning receipt, circuit breaker, red team, automation licence

Four additive layers wrap the existing rules-first pipeline (they observe or rehearse it and never duplicate extraction/validation/DCSA logic).

**1. Reasoning Receipt.** Every field-level decision is recorded as an audit row: `decision_path` (`rule` / `ai` / `human`), the rule that matched (`field_bank:exact`, `anchors:parse_container_count`, …), the fields the AI agent was given vs the fields the rules already handled, the source evidence (document, offset, exact quoted text), the validator outcomes (`source_match`, `whitelist`, `dcsa_mapping`) and the AI provider/latency. `GET /api/shipments/{id}/receipt` returns the ordered rows plus `total_ai_calls`, `total_tokens` and `total_latency_ms` — with the honest caveat that no LLM provider is configured by default, so the AI path uses a deterministic local assistant and no token cost is claimed.

**2. Circuit breaker + refusal certificate.** A per-document counter increments on every AI-extracted field that fails a validator and resets on any pass. At 3 consecutive failures (configurable via `AVERISH_CIRCUIT_BREAKER_THRESHOLD`) AI processing stops and a refusal certificate is produced: failed fields with the attempted value and why it failed, `missing_or_unclear`, a `suggested_recipient` inferred from which fields are missing (container/POD data → carrier, party data → shipper, otherwise internal ops), an `estimated_delay` with its documented basis, and what would unblock it. `GET /api/shipments/{id}/refusal-certificate`.

**3. Red team rehearsal.** `POST /api/shipments/{email_id}/red-team` with `{"transform": "blur" | "reword" | "remove_field" | "conflict"}` mutates the documents and re-runs the *existing* classifier → extractor → comparator → receipt/certificate paths, returning before/after status and which mechanism fired. `reword` renames standard labels to synonyms the rule dictionary does not cover, so the AI fallback fires and the proposals are accepted only when provenance validation finds the value verbatim in the source; `remove_field` trips the breaker; `conflict` produces a mismatch the reviewer resolves through the propose-and-confirm panel.

**4. Automation level ("AI license").** `POST /api/settings/automation-level {"level": 0..3}` (session-scoped, in-memory) and `GET /api/settings/automation-level/preview?level=N`. L0/L1 never write anything (L1 is the default), L2 auto-writes fields above the confidence threshold that agree and queues them for audit, L3 does the same without the audit. The preview recomputes `auto_processed_pct`, `flagged_for_review_pct`, `estimated_error_exposure_pct` (auto-written fields whose evidence is not a byte-exact match or that failed a validator) and `estimated_time_saved_minutes` from the loaded inbox's real comparison results — each metric ships with its `formula` and `sample_basis` so the number can be traced, not taken on faith.

```bash
python demo_trust_features.py            # walk the 5-minute demo (all four features)
python demo_trust_features.py --step 3   # just the circuit-breaker step
```

Open the **Trust & AI Controls** tab in the app: automation slider with live tiles, the red-team buttons, and the collapsible reasoning receipt (also shown inside the SI/BL inspector). Inbox cards carry an `AUTO-PROCESSED · Lx` / `NEEDS YOU · Lx` badge that flips when the level changes.

What these features do **not** claim: the AI path is a deterministic local assistant unless an LLM provider is configured (`AVERISH_LLM_PROVIDER` + `AVERISH_LLM_API_KEY`), the delay estimate uses a documented configurable constant, and the receipt is an audit trail — not a certificate of correctness.


Requirements: Python 3.11+ and Node.js with npm. Run these commands from the repository root.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..
python run_app.py
```

Open `http://localhost:3000` for the app, `http://localhost:3000/dashboard` for the OCR dashboard, and `http://localhost:8000/docs` for the API documentation. `run_app.py` starts FastAPI on port 8000 and Vite on port 3000; stop it with Ctrl+C. If PowerShell blocks venv activation, use `.venv\Scripts\python.exe` for the Python commands.

The repository also has a Docker Compose option for the **API only**:

```bash
docker compose up --build
```

That serves FastAPI at `http://localhost:8080`. It does not start the React frontend. To run the frontend alongside it, start the local API on port 8000 as above, or adjust the Vite proxy in `frontend/vite.config.js` to port 8080.

For a frontend build check, run `cd frontend && npm run build`. The backend tests use FastAPI's test client; depending on the installed Starlette version, they may also require the `httpx2` package before `python -m unittest discover -s tests` can run.

## Challenges faced and current limits

- **Different labels and formatting:** SI and BL documents can express the same field differently. The extractor and comparator normalize common variants, but unusual layouts can still require review.
- **Scanned pages:** OCR can read image-only PDFs, but the supplied scans have no verified transcripts. The dashboard's accuracy percentage compares OCR output with existing searchable PDF text where available; it is a proxy benchmark, not measured accuracy on scanned pages. Field coverage measures completeness, not correctness.
- **Incomplete evidence:** Missing or damaged attachments and absent required values must be surfaced clearly. The comparison gate sends these to review instead of silently marking them as matches.
- **Validation:** The local self-evaluation view summarizes the app's own output. It does not use the organizers' private answer key, and its displayed score is not an independently measured classification or defect F1 score.
- **Prototype state:** The main request path is synchronous, and reviewer overrides plus extraction caches are process-local. Restarting the backend clears them.

## Future plan

1. Persist reviewer decisions and extracted evidence in a durable store, with a traceable link to each source document and field.
2. Add verified transcripts for scanned PDFs and evaluate OCR with real character/word error rates; expand coverage to harder layouts and languages.
3. Compare the generated submission with the organizers' private evaluator when available, then tune classification and mismatch rules against actual false positives and misses.
4. Move document processing to background jobs with progress, retries, and visible failure states.
5. Expand reviewer workflows and access controls before using the system with live operational inboxes.

## Project map

| Path | Purpose |
| --- | --- |
| `backend/main.py` | FastAPI routes and workflow orchestration (incl. DCSA mapping/correction endpoints) |
| `backend/services/` | Data loading, classification, extraction, comparison, DCSA mapping/evidence, correction flow, OCR, evaluation, and timeline services |
| `frontend/src/` | React operations interface |
| `test data/` | Supplied email and attachment dataset |
| `tests/` | Backend workflow and OCR tests |
