# Project Context: RupeeRadar

RupeeRadar is an AI-powered personal finance assistant designed to help working professionals make sense of their monthly transactions by analyzing bank statement data. 

---

## 1. Project Overview & Objective
Working professionals make hundreds of monthly transactions across various channels (UPI, cards, bank transfers, etc.). Although bank statements capture all this data, the transaction descriptions are often messy, inconsistent, and difficult to categorize manually.

**Objective:**
Build an end-to-end working prototype that converts raw financial transaction data into structured, readable, and meaningful personal finance insights, presenting them in a simple dashboard or report.

---

## 2. Core Features & Functional Requirements

### 1. Data Input & Extraction
- **Input:** Accept raw bank statement data (e.g., CSV, Excel, PDF, or copy-pasted text).
- **Extraction:** Clean and parse raw records into a structured transaction list.
- **Tolerance:** Prioritize a robust parsing mechanism for a few common formats rather than perfect support for all bank formats.

### 2. Transaction Cleaning & Normalization
- Handle real-world messy description strings (e.g., resolving merchant names from cryptic UPI handles or card transaction codes).
- Standardize description text for display.

### 3. Expense & Income Categorization
Classify all transactions into relevant categories, including but not limited to:
- **Food**
- **Travel**
- **Shopping**
- **Bills**
- **EMI**
- **Subscriptions**
- **Salary**
- **Rent**
- **Investments**
- **Other**

### 4. Recurring Payment Detection
Identify recurring transactions automatically to help users track fixed costs:
- Subscriptions (e.g., Netflix, Spotify)
- EMIs
- Rent payments
- SIPs (Systematic Investment Plans)
- Insurance premiums

### 5. Financial Metrics & Summary
Calculate key metrics to answer core financial questions:
- **Total Income**
- **Total Spend**
- **Net Savings**
- **Top Spending Categories**
- **Largest Transactions**

### 6. Personalized Financial Insights
Generate at least **three** clear, human-readable, data-backed insights based on actual transaction behavior (e.g., "Your dining expenses increased by 15% this week," or "You have 4 active subscriptions costing ₹1,200/month").

### 7. Spend Summary Dashboard / UI
Present the finalized data and insights in a clean, simple, and intuitive user interface or report that can be exported or shared.

---

## 3. Implementation Details & Guidelines

### Technology Stack
- **Frontend/Core UI:** Vanilla HTML, CSS, JavaScript (or a modern framework if requested, keeping interactions smooth and responsive).
- **Backend/Logic:** Suitable parser and categorization logic (rules-based or leveraging AI/LLM for advanced descriptions).
- **Privacy:** Implement local or secure handling of sensitive financial data (avoid unnecessary uploads or storage of unencrypted PII).

### Evaluation & Quality Checklist
- [ ] **Data Cleaning:** Messy descriptions are parsed and normalized.
- [ ] **Categorization Accuracy:** Transactions are correctly assigned to their respective classes.
- [ ] **Recurring Detection:** Fixed and recurring costs are successfully flagged.
- [ ] **Aesthetics & UX:** Interface is modern, clean, and visually pleasing.
- [ ] **Complete End-to-End Flow:** Seamless transition from uploading a statement to displaying the dashboard metrics.
