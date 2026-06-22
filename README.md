# RupeeRadar

An AI-powered personal finance assistant designed to ingest, clean, and visualize transaction records from bank statements.

---

## Architecture Overview
RupeeRadar is built as a modular application with a decoupled client-server structure:
- **Backend:** FastAPI (Python) web framework, SQLAlchemy ORM (SQLite database), Pandas parse filters, and Groq SDK (Llama 3 classification model).
- **Frontend:** Vite React (TypeScript) dashboard, Vanilla CSS design theme, and Lucide Icons.

---

## Repository Structure
```text
rupee-radar/
├── docs/                   # Specifications, architecture plans, and edge-cases
├── backend/                # FastAPI application, database schemas, and classifiers
│   ├── app/
│   │   ├── api/            # API endpoints (v1 routes)
│   │   ├── models.py       # SQLAlchemy DB schemas
│   │   ├── database.py     # SQLite session connection manager
│   │   └── services/       # Groq categorization service helper
│   ├── requirements.txt    # Python backend package requirements
│   └── README.md
├── frontend/               # Vite React + TypeScript web application
│   ├── src/
│   │   ├── App.tsx         # Dashboard views and components
│   │   ├── index.css       # App theme styling variables and design systems
│   │   └── main.tsx        # React client entry point
│   ├── index.html          # HTML entry point and Google Fonts configurations
│   └── package.json
└── README.md               # Main instructions
```

---

## Running the Application

### 1. Running the Backend Server
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install backend requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   # Set your Groq API Key
   set GROQ_API_KEY=your-groq-api-key-here
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
   *The interactive Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

### 2. Running the React Dashboard Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
   *The dashboard will be running at [http://localhost:5173](http://localhost:5173).*
