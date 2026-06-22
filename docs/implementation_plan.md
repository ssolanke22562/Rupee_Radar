# Phase-Wise Implementation Plan: RupeeRadar

This document outlines a structured, phase-wise implementation plan for building the **RupeeRadar** personal finance assistant. It is updated to match the FastAPI + React client-server system architecture specified in the updated [System Architecture](file:///c:/Users/sarth/OneDrive/Desktop/Transaction%20Tracker/docs/architecture.md).

---

## Directory Structure Reference
The codebase will follow this structured layout:
```text
rupee-radar/
├── docs/
│   ├── context.md
│   ├── Problem-Statement.txt
│   ├── architecture.md
│   └── implementation_plan.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/
│   │   ├── parsers/        # pandas / pdfplumber parser plugins
│   │   ├── pipeline/       # cleaner, categorizer, recurring, metrics, insights
│   │   ├── models/         # SQLAlchemy DB models (SQLite/Postgres)
│   │   └── services/       # DB session helper, LLM services
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # FileUpload, TransactionTable, CategoryChart, etc.
│   │   ├── pages/          # Landing, Dashboard
│   │   └── api/            # REST API hooks (React Query / SWR)
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Phase 1: Stack Setup & Database Foundation
**Goal:** Initialize the backend, database schemas, and frontend project skeletons.

### 1. Backend Setup (FastAPI & SQLite)
- Create `backend/` directory structure.
- Initialize virtual environment, setup dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pandas`, `pydantic`).
- Configure database tables using SQLAlchemy/SQLite (`backend/app/models/`):
  - **UploadSession:** `id`, `filename`, `status` (pending/parsing/processing/ready/failed), `uploaded_at`, `expires_at`.
  - **Transaction:** `id`, `session_id`, `date`, `description_raw`, `description_clean`, `amount` (debits negative), `type` (credit/debit), `category`, `is_recurring`.
  - **RecurringGroup:** `id`, `session_id`, `label`, `category`, `frequency`, `typical_amount`, `transaction_ids`.
  - **AnalysisResult:** `session_id`, `metrics` (JSON), `insights` (JSON).

### 2. Frontend Setup (React, TS, Tailwind)
- Initialize Vite React project with TypeScript and TailwindCSS in `frontend/`.
- Set up API layers, router, and global layouts.

---

## Phase 2: Ingestion, Raw Parsing & Normalization
**Goal:** Implement file upload, raw bank statement parsing, and narration string scrubbing.

### 1. Backend Ingestion Engine
- Define `POST /api/v1/upload` (accepts CSV, validates size < 10MB, creates `UploadSession` record).
- Create `StatementParser` interface protocol.
- Build sub-parsers for common Indian banks (e.g. HDFC, ICICI, SBI) using pandas to output canonical JSON.
- Add fallback column mapping parser when the header auto-detection fails.

### 2. Cleaning & Normalization Pipeline (`cleaner.py`)
- Implement Regex cleaners to strip UPI transaction codes, timestamps, and reference IDs.
- Extract merchant keys and payment mode (UPI, Card, NEFT, IMPS, Cash).
- Enforce negative numbers for debits and positive for credits.

---

## Phase 3: Hybrid Categorization Engine
**Goal:** Classify transactions using a deterministic and AI-fallback pipeline.

### 1. Tier 1: Rules-Based Regex Categorizer (`categorizer.py`)
- Define local keyword dictionary mapping patterns (e.g., Zomato -> Food, Rent -> Rent, Netflix -> Subscriptions).
- Route matching transactions to their categories instantly.

### 2. Tier 2: LLM Batch Categorization API
- Setup helper to batch unmatched transactions (20–50 rows per payload).
- Write structured prompt requesting category and confidence scores in JSON.
- Mask/sanitize transaction names to strip any potential account numbers or private identifiers before calling the API.
- Map low confidence scores ($< 0.6$) or API failures to category `Other`.

### 3. Category Override API
- Implement `PATCH /api/v1/sessions/{id}/transactions/{txn_id}` to allow users to manually re-categorize and fix erroneous assignments.

---

## Phase 4: Recurring Payments & Analytics Aggregator
**Goal:** Detect fixed recurring transactions and compute statistical summary outputs.

### 1. Recurring Payment Detection Heuristics (`recurring.py`)
- Group debits by fuzzy matching cleaning descriptions (Levenshtein distance).
- Check constraints: count $\ge 2$, amount variance within $\pm 5\%$, intervals matching regular intervals (monthly, weekly).
- Create `RecurringGroup` records.

### 2. Analytical Summary (`metrics.py` & `insights.py`)
- Aggregate metrics: Total income, total spend, net savings, savings rate, top categories, and biggest debit transactions.
- Implement the Insights engine:
  - Generate at least **three** narrative spend observations citing actual figures from the aggregates.

---

## Phase 5: Interactive React Dashboard Frontend
**Goal:** Assemble the interactive React interface and wire it to the FastAPI REST endpoints.

### 1. UI Components
- **FileUpload:** Drag-and-drop boundary showing progress indicators and format warnings.
- **SummaryCards:** Styled counters for Income, Spends, Net Savings, and Savings Rate.
- **CategoryChart:** Interactive Pie/Doughnut charts showing category shares and Bar charts for spending trends.
- **TransactionTable:** Search input, category badges, pagination, and dropdown menus to trigger Category Overrides.
- **RecurringPanel:** Flex row of cards displaying detected EMIs/Subscriptions and active total costs.
- **InsightsList:** Visual panel hosting the generated observations.

### 2. API Integration
- Connect React Query to FastAPI routes: `/upload`, `/sessions/{id}`, `/transactions`, `/recurring`, `/analytics`, `/insights`.

---

## Phase 6: Session Retention Policies, PDF Export & Deploy
**Goal:** Enable session purging, print exports, and production Docker containerization.

### 1. Retention Policy Implementation
- Implement a background task scheduler in FastAPI to delete database sessions and physical uploaded files older than 24-72 hours (`SESSION_TTL_HOURS`).

### 2. Report Export Utility
- Style custom print layouts in CSS (`@media print`) so `window.print()` outputs a pristine, single-page summary report.

### 3. Deployment & Devops
- Write a unified `docker-compose.yml` routing incoming HTTP traffic between Vite client static assets and the FastAPI server.
