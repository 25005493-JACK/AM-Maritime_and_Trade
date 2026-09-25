# DocuMatch Project Directory Structure & Classification Guide

This document outlines the professional file organization of the **DocuMatch** platform, detailing the folder tree hierarchy and providing precise architectural rationales for why every file and directory is positioned where it is.

---

## 🌳 Project Directory Tree

```
AverishMonash/
├── backend/                        # FastAPI Service & Server Core
│   ├── main.py                     # Primary REST API application router & endpoints
│   ├── database/                   # Relational database schemas & security policies
│   │   ├── tighten_rls.sql         # Supabase Row-Level Security policy definitions
│   │   └── supabase_schema.sql     # Database table DDL & schema migrations
│   ├── data/                       # Dynamic runtime storage (overrides & processing jobs)
│   │   ├── human_overrides.json    # Human review resolution audit log
│   │   ├── inbox.json              # Runtime inbox dataset cache
│   │   ├── processing_jobs.json    # Async job status & task tracking
│   │   └── attachments/            # PDF and TXT document attachments
│   ├── services/                   # Modular domain logic & core processing engines
│   │   ├── ai_agent.py             # Opt-in LLM hybrid routing & fallback logic
│   │   ├── anchors.py              # Regex rules for weight & container count parsing
│   │   ├── anchor_triage.py        # Triage rules for deterministic field extraction
│   │   ├── auth.py                 # JWT token authentication & reviewer RBAC
│   │   ├── automation.py           # Automation threshold policy & slider controls
│   │   ├── calendar_service.py     # Vessel schedule & timeline tracking
│   │   ├── circuit_breaker.py      # Error rate monitoring & system trip logic
│   │   ├── classifier.py           # 5-Category email classifier engine
│   │   ├── comparator.py           # SI vs BL document discrepancy comparison
│   │   ├── correction_flow.py      # End-to-end human review & override handler
│   │   ├── corrections_log.py      # Reflexion memory logger & dispute analytics
│   │   ├── dataset_loader.py       # Dataset ingestion & attachment loader
│   │   ├── dcsa_mapping.py         # DCSA Standard (eBL v3.0) payload transformer
│   │   ├── document_validator.py   # Intent & document decoupling validator
│   │   ├── evaluator.py            # Evaluation metric calculator & scoreboard generator
│   │   ├── event_bus.py            # Event-driven pub/sub event distribution
│   │   ├── event_logger.py         # Structured event audit logger
│   │   ├── extractor.py            # Rules-first text & field extractor
│   │   ├── field_bank.py           # Field value historical tracking & lookup
│   │   ├── field_evidence.py       # Verbatim string character-offset locator
│   │   ├── hash_cache.py           # Document content hashing & de-duplication
│   │   ├── job_store.py            # Background job queue state persistence
│   │   ├── ocr_dashboard.py        # OCR quality metrics & binarization inspector
│   │   ├── pdf_inspector.py        # Layout structure & text layer inspector
│   │   ├── pdf_ocr.py              # Tesseract OCR wrapper for scanned PDFs
│   │   ├── port_lookup.py          # UN/LOCODE ocean port code validator
│   │   ├── reasoning_receipt.py    # Transparent execution audit receipt generator
│   │   ├── red_team.py             # Security sanitizer & prompt injection detector
│   │   ├── reflection.py           # Episodic reflexion memory retriever
│   │   ├── routing_policy.py       # Rule-first vs LLM routing rule manager
│   │   └── supabase_service.py     # Supabase cloud synchronization connector
│   └── tessdata/                   # Optical Character Recognition assets
│       └── eng.traineddata         # Tesseract English language training dictionary
├── frontend/                       # React 19 + Vite + Tailwind Desktop UI
│   ├── public/                     # Static assets & pre-generated API caches
│   │   ├── index.html              # HTML template entry point
│   │   └── api/                    # Cached static API endpoints for web deployment
│   ├── src/                        # React frontend source code
│   │   ├── main.jsx                # React root renderer
│   │   ├── App.jsx                 # Master application component & layout manager
│   │   ├── api.js                  # Frontend HTTP client & backend API bindings
│   │   ├── index.css               # Global styles & Tailwind CSS configuration
│   │   └── components/             # Reusable UI widgets & functional views
│   │       ├── AdminDashboard.jsx          # Admin control & security settings
│   │       ├── AgentLearningDashboard.jsx  # Reflexion memory & rule dispute dashboard
│   │       ├── AnalyticsDashboard.jsx      # System accuracy & throughput metrics
│   │       ├── AutomationSlider.jsx        # Confidence threshold slider control
│   │       ├── ConflictEvidencePanel.jsx   # Side-by-side evidence comparison view
│   │       ├── GmailComposeModal.jsx       # Email composition modal
│   │       ├── GmailHeader.jsx             # Top search bar & global action header
│   │       ├── GmailInbox.jsx              # Main inbox feed with status filters
│   │       ├── GmailSettingsModal.jsx      # Settings configuration modal
│   │       ├── GmailSidebar.jsx            # Main navigation sidebar
│   │       ├── GoogleAppsMenu.jsx          # Workspace app navigation menu
│   │       ├── HumanReviewModal.jsx        # Interactive document review modal
│   │       ├── HumanReviewQueue.jsx        # Pending review items queue
│   │       ├── InboxFeed.jsx               # Filterable email message list
│   │       ├── InboxWorkspace.jsx          # Integrated inbox workspace container
│   │       ├── OcrDashboard.jsx            # OCR text extraction inspection panel
│   │       ├── ReasoningReceipt.jsx        # Detailed audit receipt breakdown widget
│   │       ├── RedTeamPanel.jsx            # Security threat simulation panel
│   │       ├── SelfEvaluationView.jsx      # Live evaluation scoreboard view
│   │       ├── ShipmentTimeline.jsx        # Shipment event sequence visualizer
│   │       ├── ShipmentWorkspace.jsx       # Full split-screen document inspector
│   │       ├── Sidebar.jsx                 # Secondary navigation sidebar
│   │       ├── SplitScreenInspector.jsx    # SI vs BL split document comparison view
│   │       ├── TimelineWheel.jsx           # Circular shipment timeline widget
│   │       ├── UploadDocsModal.jsx         # Custom document pair upload modal
│   │       ├── UploadModal.jsx             # Quick file upload dialog
│   │       └── VesselCalendar.jsx          # Vessel arrival & schedule calendar
│   ├── package.json                # Frontend dependencies & npm scripts
│   ├── vite.config.js              # Vite build tool setup & dev server config
│   ├── tailwind.config.js          # Tailwind CSS styling framework configuration
│   └── postcss.config.js           # PostCSS plugin options
├── llm_agent/                      # Opt-in LLM Layer (Standalone Python Package)
│   ├── __init__.py                 # Package initializer & public exported API
│   ├── client.py                   # OpenAI / Gemini / FakeTransport client wrapper
│   ├── schemas.py                  # Pydantic v2 strict output schemas
│   ├── tasks.py                    # LLM tasks (field extraction, scanning, replies)
│   └── validators.py               # UN/LOCODE, ISO 6346, & verbatim provenance checks
├── data/                           # Core Reference Datasets & Terminology Dictionaries
│   ├── field_terms.json            # Deterministic dictionary of shipping terms
│   ├── synonyms.json               # Synonym mappings for field normalization
│   ├── synthetic_dataset.json      # Benchmark dataset metadata
│   ├── emails/                     # Sample email text files
│   └── attachments/                # Test attachment files
├── mock data/                      # Mock Datasets for Standalone Testing
│   ├── mock_emails.json            # Simulated email payload fixtures
│   ├── mock_bl.pdf                 # Sample mock Bill of Lading PDF
│   └── mock_si.txt                 # Sample mock Shipping Instruction text
├── test data/                      # Benchmark Inbox Dataset (520 Emails)
│   ├── inbox/                      # 520 JSON email files (email_001 to email_520)
│   ├── attachments/                # Associated PDF and text attachments
│   └── loader.py                   # Ingest loader for test dataset
├── tests/                          # Automated Pytest Suite (138 Test Cases)
│   ├── test_correction_memory.py   # Reflexion memory integration tests
│   ├── test_dcsa_alignment.py      # DCSA eBL standard schema transformation tests
│   ├── test_intent_document_decoupling.py # Document decoupling verification tests
│   ├── test_learning_features.py   # Self-learning dispute resolution tests
│   ├── test_live_e2e_pipeline.py   # Full live pipeline integration test
│   ├── test_live_workflow.py       # End-to-end workflow execution tests
│   ├── test_llm_agent.py           # LLM agent schema validation & mock tests
│   ├── test_mismatch_regression_fixes.py # Regression test suite for mismatch edge cases
│   ├── test_pdf_ocr_dashboard.py   # PDF text extraction & OCR dashboard tests
│   ├── test_rebuilt_workflow.py    # Rebuilt shipping workflow & evaluator tests
│   ├── test_rules_first_pipeline.py# Rules-first deterministic pipeline tests
│   ├── test_security_and_jobs.py   # Circuit breaker & job store security tests
│   ├── test_shipment_timeline.py   # Shipment event tracking tests
│   ├── test_strict_provenance.py   # Verbatim provenance verification tests
│   ├── test_trust_features.py      # Reasoning receipts & trust feature tests
│   └── test_verification_pipeline.py # Core document verification pipeline tests
├── eval/                           # Rigorous Evaluation & Benchmark Suite
│   ├── evaluate.py                 # Ground-truth metric evaluator (F1 & Precision)
│   ├── evaluate_memory.py          # Memory learning speed benchmark
│   ├── eval_transport.py           # Transport layer evaluation runner
│   ├── run_self_eval.py            # Self-evaluation dataset runner
│   ├── build_ground_truth.py       # Ground truth label consolidator
│   ├── generate_template.py        # Labelling template generator
│   ├── generate_labelling_template.py # Annotation template builder
│   ├── split.py                    # Dataset train/dev/heldout splitter
│   ├── results.md                  # Evaluation benchmark summary report
│   ├── memory_results.md           # Reflexion memory evaluation report
│   └── labels/                     # Annotated ground truth CSV files
├── scripts/                        # Utility & Developer Demonstration Scripts
│   ├── check_data_classification.py# Data classification auditor script
│   ├── demo_dcsa_conflict.py       # DCSA conflict resolution demo
│   ├── demo_self_learning.py       # Interactive reflexion memory demo
│   ├── demo_trust_features.py      # Trust & circuit breaker interactive demo
│   ├── export_static_api_data.py   # Pre-renderer for static public deployment
│   └── export_via_http.py          # HTTP export utility script
├── presentation/                   # Presentation & Pitch Deck Assets
│   ├── index.html                  # Interactive HTML Pitch Deck
│   ├── build_deck.py               # Slide deck build script
│   └── assets/                     # Slide visual assets & screenshots
├── docs/                           # Architecture Specifications & Manuals
│   ├── tech_desk_v4_architecture.md# Full technical architecture specification
│   └── Shipping Document Verification Use Case.pdf # Original hackathon problem brief
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git repository exclusion rules
├── .vercelignore                   # Vercel static deployment exclusion file
├── Dockerfile                      # Container build manifest
├── docker-compose.yml              # Multi-container orchestration config
├── netlify.toml                    # Netlify deployment settings
├── README.md                       # Master project overview & quickstart guide
├── requirements.txt                # Python backend dependencies
├── run_app.py                      # One-click dual-server launcher script
├── submission.json                 # Pre-computed evaluation submission file
├── vercel.json                     # Vercel serverless routing configuration
├── folder tree.md                  # Project directory tree & classification guide (This File)
├── self learning model explaination.md # Self-learning model & Reflexion architecture guide
└── USER_MANUAL.md                  # Detailed User Manual & Backend Tech Stack Guide
```

---

## 📂 Structural Rationales by Folder

### 1. `backend/` (FastAPI Server & Services)
* **Purpose**: Houses the entire server-side application logic, database migrations, and domain services.
* **Why Classified Here**:
  * Separates back-end processing cleanly from front-end presentation (`frontend/`).
  * `backend/main.py` serves as the single API entrypoint for REST routes.
  * `backend/services/` organizes logic into modular, single-responsibility Python files (e.g., regex extraction in `extractor.py`, UN/LOCODE matching in `port_lookup.py`, evaluation calculations in `evaluator.py`).

### 2. `frontend/` (React Desktop Web Application)
* **Purpose**: Contains the client-side user interface built with React 19, Vite, and Tailwind CSS.
* **Why Classified Here**:
  * Encapsulates all modern JavaScript UI components, stylesheets, and frontend configuration in a standard Node.js project directory.
  * Standardized sub-directories (`src/components/`, `public/`) enable modular web development and easy deployment to platforms like Netlify or Vercel.

### 3. `llm_agent/` (Opt-in LLM Integration Package)
* **Purpose**: A self-contained, opt-in Python package that governs LLM interactions (OpenAI, Gemini, or local fallback).
* **Why Classified Here**:
  * Kept as a top-level package so it can be imported cleanly across backend services and pytest suites (`from llm_agent import ...`).
  * Implements strict Pydantic v2 schemas (`schemas.py`), safety validators (`validators.py`), and tasks (`tasks.py`) independently of deterministic rule services.

### 4. `data/`, `mock data/`, `test data/` (Preserved Reference & Inbox Datasets)
* **Purpose**: Essential data repositories storing core dictionaries, mock document pairs, and the 520 inbox email benchmark dataset.
* **Why Classified Here**:
  * Preserved explicitly as mandated by project requirements.
  * `data/` contains runtime lookup tables (`field_terms.json`, `synonyms.json`).
  * `test data/` supplies the 520 real-world inbox JSON files required for evaluation and integration tests.

### 5. `tests/` (Pytest Verification Suite)
* **Purpose**: Contains 16 automated test modules verifying 138 test cases.
* **Why Classified Here**:
  * Grouped in a dedicated root-level `tests/` directory following standard Python open-source conventions.
  * Facilitates effortless execution via `python -m pytest` from the root directory.

### 6. `eval/` (Evaluation Framework & Ground Truth Labels)
* **Purpose**: Provides tools for computing independent Precision, Recall, and F1 metrics against ground-truth CSV annotations.
* **Why Classified Here**:
  * Keeps evaluation benchmarking separate from runtime server code.
  * Holds evaluation scripts (`evaluate.py`), dataset splitting utilities (`split.py`), and human-verified ground-truth labels (`labels/`).

### 7. `scripts/` (Utility & Developer Demonstration Tools)
* **Purpose**: Consolidates developer CLI scripts and interactive demonstration utilities.
* **Why Classified Here**:
  * Prevents clutter in the root directory by gathering auxiliary scripts (`demo_trust_features.py`, `export_static_api_data.py`, `check_data_classification.py`) into one clean location.

### 8. `docs/` & `presentation/` (Documentation & Pitch Deck)
* **Purpose**: Contains architectural design documents, specification PDFs, and the interactive HTML pitch deck.
* **Why Classified Here**:
  * Separates developer/user documentation (`docs/`) and stakeholder presentation materials (`presentation/`) from code modules.

---

## ⚡ Key Verification Guarantee
The project reorganization maintains 100% backward compatibility. All 138 test cases in `tests/` pass cleanly without modification, and running `python run_app.py` launches both backend and frontend servers seamlessly.
