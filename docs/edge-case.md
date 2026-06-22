# Edge Cases & Error Handling: RupeeRadar

This document outlines the detailed edge cases, error conditions, and handling strategies for the **RupeeRadar** personal finance assistant. It has been updated to reflect the full-stack FastAPI + React architecture, hybrid (Rules + LLM) categorization engine, and SQLite database storage model.

---

## 1. Ingestion & File Ingest Layer (FastAPI Backend)

| Edge Case | Impact | Handling Strategy |
| :--- | :--- | :--- |
| **Password-Protected PDFs** | PDF library (`pdfplumber` / PyPDF2) throws decryption exceptions. | Check file headers. Catch file decryption/permission errors and return a `422 Unprocessable Entity` with JSON: `{"detail": "File is password protected. Please decrypt before uploading."}` |
| **Malformed Excel/CSV Sub-headers** | Column alignment shifts or header rows are interspersed with data. | Use Pandas to detect and skip metadata blocks (e.g. account holder details at the top) by locating the main header row dynamically before parsing data. |
| **Varying Date Formats** | CSVs using `DD-MM-YYYY`, `DD/MM/YY`, or text dates like `15-Jun-25` fail parser conversion. | Apply a robust helper using Pandas `to_datetime(..., errors='coerce')` with a list of expected formats, falling back to a structured parse warning in the UI if dates cannot be parsed. |
| **Over-sized Statements (> 10MB)** | Memory exhaustion or server timeout in standard request workers. | Reject file at the API gateway or FastAPI level (`HTTP 413 Payload Too Large`). |
| **Network Interruption during Upload** | Incomplete files written to temp directory. | Use chunked uploads with size validation. Clean up partial files upon request termination or via the daily TTL purge worker. |

---

## 2. Processing Pipeline & Database Storage

| Edge Case | Impact | Handling Strategy |
| :--- | :--- | :--- |
| **SQLite DB Write Locks** | Concurrent session writes trigger `sqlite3.OperationalError: database is locked`. | Configure database session pool connection timeout (e.g. `timeout=30`) or enable Write-Ahead Logging (WAL) mode in SQLAlchemy. |
| **Cascade Purging Failures** | Deleting a session leaves orphaned transaction or analytics records, leaking PII. | Configure Foreign Key constraints with `ON DELETE CASCADE` across `upload_sessions`, `transactions`, `recurring_groups`, and `analysis_results`. |
| **Expired Session API Requests** | Clients attempt to fetch transactions or reports using an expired ID. | If UUID search returns `None` in the database, return a standard `404 Not Found` message: `{"detail": "Session has expired or does not exist."}` |
| **Duplicate In-Session Transactions** | Standard statements sometimes list identical transactions (same date, same merchant, same amount) on the same day. | Maintain an internal line counter or index sequence key in the DB instead of using only a hash of date/description/amount to prevent false-deduplication of valid, separate purchases. |

---

## 3. Hybrid Categorization & LLM Interactions

| Edge Case | Impact | Handling Strategy |
| :--- | :--- | :--- |
| **LLM API Rate Limits (429 / Exhausted Tokens)** | Pipeline freezes or crashes during batch categorization. | Implement an exponential backoff retry mechanism (using `tenacity` in Python) and fall back gracefully to the **Rules-based tagger + "Other" category** if limits persist. |
| **Malformed JSON Response from LLM** | Backend fails to parse the structured categories list. | Use Pydantic validation (or Instructor package) for structured generation. If parsing fails, retry once or assign the batch to the `Other` category and log a parsing warning. |
| **Data Leakage (PII in LLM Payload)** | Sending sensitive user data (e.g., salary transfers containing full names or account numbers) to LLM. | Pre-sanitize descriptions inside `cleaner.py` using regex to swap out numeric strings (account numbers, cards, phone numbers) with placeholders (e.g., `[REDACTED]`). |
| **LLM Classification Downtime** | Total failure of remote LLM services. | Pipeline degrades gracefully, categorizing the dataset solely with the Tier 1 regex engine, and outputs a UI warning banner: *"Using local categorization rules; advanced categorization is temporarily limited."* |

---

## 4. Recurring Payment Detection Heuristics

| Edge Case | Impact | Handling Strategy |
| :--- | :--- | :--- |
| **Irregular Billing Cycle / Calendar Drift** | Subscriptions billed on the last day of the month (28th–31st) or late payments. | Use a fuzzy calendar window (27 to 33 days) to check monthly intervals. Match items with a Levenshtein similarity score $> 0.85$ on descriptions. |
| **Variable Amount Subscriptions** | Utility bills (Power, Water) vary in cost and are missed by rigid detectors. | Relax the amount constraint to $\pm 30\%$ specifically for merchants matching utility patterns (e.g. `Electricity`, `Power Grid`), flagging them as `Recurring (Variable)`. |
| **Overlapping Subscriptions** | Multiple distinct accounts on the same merchant (e.g., two Spotify plans). | Check transactions by matching exact amount combinations if multiple intervals appear. Group them into separate recurring sequences. |

---

## 5. Client UI & Server Synchronization (React Frontend)

| Edge Case | Impact | Handling Strategy |
| :--- | :--- | :--- |
| **Stale Cache on Category Override** | User edits a transaction category, but charts and summaries show outdated metrics. | Invalidate React Query/SWR cache queries for `analytics` and `transactions` immediately upon a successful `PATCH /sessions/{id}/transactions/{txn_id}` request. |
| **Long-Running Server Parses** | UI displays loading states that may freeze if network requests time out. | Implement polling: display a detailed loader indicating current phase (`Parsing` -> `Cleaning` -> `Categorizing`) while querying status `GET /sessions/{id}` until it reports `ready`. |
| **LocalStorage Exceeded** | Storing session keys or offline flags fails. | Use sessionStorage instead of localStorage for transaction data, or compress datasets. Catch `QuotaExceededError` safely without interrupting dashboard usage. |
| **Disconnectivity / Network Loss** | Save operations fail, displaying empty tables. | Render connection warning banners in React. Queue override operations in memory or disable modification inputs until connectivity is restored. |
