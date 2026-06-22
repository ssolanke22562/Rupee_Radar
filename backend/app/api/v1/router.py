from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
import os
import shutil
import PyPDF2
from io import BytesIO
import logging

from backend.app.database import get_db, SessionLocal
from backend.app.models import UploadSession, Transaction, RecurringGroup, AnalysisResult
from backend.app.pipeline.manager import process_upload_session

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Directory for temporary file uploads
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

def run_pipeline_bg(session_id: str, file_path: str, bank_hint: str):
    db = SessionLocal()
    try:
        process_upload_session(session_id, file_path, bank_hint, db)
    finally:
        db.close()

# 1. Upload Statement
@api_router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    bank_hint: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Validate file size (under 10MB)
    max_size = 10 * 1024 * 1024  # 10 MB
    try:
        contents = file.file.read(max_size + 1)
        if len(contents) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the 10 MB limit."
            )
        # Reset file cursor after reading
        file.file.seek(0)
        
        # Check for password-protected PDF
        if file.filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(contents))
                if pdf_reader.is_encrypted:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="File is password protected. Please decrypt before uploading."
                    )
            except Exception as pdf_e:
                if isinstance(pdf_e, HTTPException):
                    raise pdf_e
                # If it's another parsing error, we just continue and let the pipeline handle it
                pass
                
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read upload file: {str(e)}"
        )

    # Generate a new session
    session_id = str(uuid.uuid4())
    ttl_hours = 24  # Configure via settings/env
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    new_session = UploadSession(
        id=session_id,
        filename=file.filename,
        file_type=file.content_type,
        bank_hint=bank_hint,
        status="pending",
        uploaded_at=datetime.utcnow(),
        expires_at=expires_at
    )
    db.add(new_session)
    db.commit()

    # Save uploaded file to temp path
    safe_filename = f"{session_id}_{secure_filename(file.filename)}"
    temp_file_path = os.path.join(TEMP_DIR, safe_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        new_session.status = "failed"
        new_session.error_message = f"Failed to save temporary upload: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save statement upload on server."
        )

    # Trigger background parsing & categorization task
    background_tasks.add_task(
        run_pipeline_bg, 
        session_id, 
        temp_file_path, 
        bank_hint or "auto"
    )

    return {
        "session_id": session_id,
        "status": "pending",
        "message": "File uploaded successfully. Processing started."
    }

def secure_filename(filename: str) -> str:
    # Basic filename cleaning helper
    return "".join(c for c in filename if c.isalnum() or c in "._-")


# 2. Get Session Status
@api_router.get("/sessions/{session_id}")
def get_session_status(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found or expired")
    
    return {
        "id": session.id,
        "filename": session.filename,
        "status": session.status,
        "uploaded_at": session.uploaded_at,
        "expires_at": session.expires_at,
        "error_message": session.error_message
    }

# 3. Get Paginated Transactions
@api_router.get("/sessions/{session_id}/transactions")
def get_transactions(
    session_id: str,
    page: int = 1,
    limit: int = 50,
    category: Optional[str] = None,
    is_recurring: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(Transaction).filter(Transaction.session_id == session_id)
    
    if category:
        query = query.filter(Transaction.category == category)
    if is_recurring is not None:
        query = query.filter(Transaction.is_recurring == is_recurring)
    if search:
        query = query.filter(
            (Transaction.description_raw.ilike(f"%{search}%")) |
            (Transaction.description_clean.ilike(f"%{search}%"))
        )

    total_count = query.count()
    transactions = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "transactions": [
            {
                "id": t.id,
                "line_index": t.line_index,
                "date": t.date,
                "description_raw": t.description_raw,
                "description_clean": t.description_clean,
                "amount": t.amount,
                "type": t.type,
                "balance": t.balance,
                "category": t.category,
                "category_confidence": t.category_confidence,
                "is_recurring": t.is_recurring,
                "recurring_group_id": t.recurring_group_id,
                "metadata": t.metadata_json
            } for t in transactions
        ]
    }

# 4. Patch/Override Category
@api_router.patch("/sessions/{session_id}/transactions/{txn_id}")
def override_transaction_category(
    session_id: str,
    txn_id: str,
    category: str,
    db: Session = Depends(get_db)
):
    txn = db.query(Transaction).filter(
        Transaction.id == txn_id,
        Transaction.session_id == session_id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found in this session")

    # Update category details
    txn.category = category
    txn.category_confidence = 1.0  # Explicitly user-defined
    db.commit()

    return {
        "transaction_id": txn.id,
        "category": txn.category,
        "message": "Category updated successfully"
    }

# 5. Get Recurring Payments
@api_router.get("/sessions/{session_id}/recurring")
def get_recurring_payments(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    groups = db.query(RecurringGroup).filter(RecurringGroup.session_id == session_id).all()
    return [
        {
            "id": g.id,
            "label": g.label,
            "category": g.category,
            "frequency": g.frequency,
            "typical_amount": g.typical_amount,
            "last_seen_date": g.last_seen_date,
            "transaction_ids": g.transaction_ids,
            "confidence": g.confidence
        } for g in groups
    ]

# 6. Get Analytics & Metrics
@api_router.get("/sessions/{session_id}/analytics")
def get_analytics(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if not result:
        # Stub default values for phase 0 skeleton
        return {
            "metrics": {
                "total_income": 0.0,
                "total_spend": 0.0,
                "savings": 0.0,
                "savings_rate": 0.0,
                "recurring_total": 0.0
            },
            "top_categories": [],
            "biggest_transactions": []
        }

    return {
        "metrics": result.metrics,
        "top_categories": result.top_categories,
        "biggest_transactions": result.biggest_transactions
    }

# 7. Get Spending Insights
@api_router.get("/sessions/{session_id}/insights")
def get_insights(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if not result or not result.insights:
        return []

    return result.insights

# 8. Report Export (Phase 6.2)
@api_router.get("/sessions/{session_id}/report", response_class=HTMLResponse)
def get_report(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    analysis = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    transactions = db.query(Transaction).filter(Transaction.session_id == session_id).order_by(Transaction.date).all()
    recurring_groups = db.query(RecurringGroup).filter(RecurringGroup.session_id == session_id).all()
    
    metrics = analysis.metrics if analysis else {}
    top_categories = analysis.top_categories if analysis else []
    insights = analysis.insights if analysis else []
    
    # Generate HTML report
    title = f"RupeeRadar Financial Report - {session.filename}"
    income = metrics.get("total_income", 0)
    spend = metrics.get("total_spend", 0)
    savings = metrics.get("savings", 0)
    savings_rate = metrics.get("savings_rate", 0)
    recurring_total = metrics.get("recurring_total", 0)
    
    category_rows = ""
    for cat in top_categories[:10]:
        pct = (cat["amount"] / spend * 100) if spend > 0 else 0
        category_rows += f"""
        <tr>
            <td>{cat['category']}</td>
            <td style="text-align:right">₹{cat['amount']:,.2f}</td>
            <td style="text-align:right">{pct:.1f}%</td>
        </tr>"""
    
    insight_items = ""
    for ins in insights:
        insight_items += f"<li>{ins}</li>"
    
    recurring_rows = ""
    for rg in recurring_groups:
        recurring_rows += f"""
        <tr>
            <td>{rg.label}</td>
            <td>{rg.frequency}</td>
            <td style="text-align:right">₹{rg.typical_amount:,.2f}</td>
            <td>{rg.category}</td>
        </tr>"""
    
    txn_count = len(transactions)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #ffffff;
            color: #0f172a;
            padding: 2rem 2.5rem;
            line-height: 1.5;
        }}
        .report-header {{
            display: flex; justify-content: space-between; align-items: flex-start;
            border-bottom: 3px solid #0284c7;
            padding-bottom: 1.5rem; margin-bottom: 2rem;
        }}
        .report-header h1 {{
            font-size: 1.75rem; font-weight: 800; color: #0284c7;
        }}
        .report-header .meta {{ font-size: 0.85rem; color: #64748b; text-align: right; }}
        .report-section {{ margin-bottom: 2rem; }}
        .report-section h2 {{
            font-size: 1.15rem; font-weight: 700; color: #0f172a;
            border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5rem; margin-bottom: 1rem;
        }}
        .metrics-grid {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;
        }}
        .metric-card {{
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 1rem; text-align: center;
        }}
        .metric-card .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }}
        .metric-card .value {{ font-size: 1.5rem; font-weight: 800; margin-top: 0.25rem; }}
        .metric-card .value.income {{ color: #10b981; }}
        .metric-card .value.spend {{ color: #f43f5e; }}
        .metric-card .value.savings {{ color: #0284c7; }}
        .metric-card .value.rate {{ color: #06b6d4; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        th {{ background: #f1f5f9; text-align: left; padding: 0.6rem 0.75rem; font-weight: 600; color: #475569; }}
        td {{ padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0; }}
        tr:nth-child(even) td {{ background: #f8fafc; }}
        ul.insights {{ list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }}
        ul.insights li {{
            background: #f0f9ff; border-left: 4px solid #0284c7; padding: 1rem;
            border-radius: 4px; font-size: 0.9rem;
        }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; font-size: 0.75rem; color: #94a3b8; text-align: center; }}
        @media print {{
            body {{ padding: 0.5in; }}
            .metric-card {{ break-inside: avoid; }}
            table {{ break-inside: auto; }}
            tr {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <div>
            <h1>RupeeRadar</h1>
            <p style="font-size:0.9rem;color:#64748b;margin-top:0.25rem;">Personal Finance Statement Report</p>
        </div>
        <div class="meta">
            <p><strong>File:</strong> {session.filename}</p>
            <p><strong>Session:</strong> {session_id[:8]}...</p>
            <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
            <p><strong>Transactions:</strong> {txn_count}</p>
        </div>
    </div>
    
    <div class="report-section">
        <h2>Financial Summary</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Total Income</div>
                <div class="value income">₹{income:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="label">Total Spends</div>
                <div class="value spend">₹{spend:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="label">Net Savings</div>
                <div class="value savings">₹{savings:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="label">Savings Rate</div>
                <div class="value rate">{savings_rate:.1f}%</div>
            </div>
        </div>
        {f'<p style="font-size:0.85rem;color:#64748b;"><strong>Recurring Monthly Total:</strong> ₹{recurring_total:,.2f}</p>' if recurring_total > 0 else ''}
    </div>
    
    <div class="report-section">
        <h2>Spending by Category</h2>
        <table>
            <thead>
                <tr><th>Category</th><th style="text-align:right">Amount</th><th style="text-align:right">% of Spend</th></tr>
            </thead>
            <tbody>
                {category_rows}
            </tbody>
        </table>
    </div>
    
    <div class="report-section">
        <h2>Spending Insights</h2>
        <ul class="insights">
            {insight_items if insight_items else '<li style="background:#f8fafc;border-left-color:#94a3b8;">No insights available.</li>'}
        </ul>
    </div>
    
    {f'''
    <div class="report-section">
        <h2>Recurring Payments Detected</h2>
        <table>
            <thead>
                <tr><th>Label</th><th>Frequency</th><th style="text-align:right">Amount</th><th>Category</th></tr>
            </thead>
            <tbody>
                {recurring_rows}
            </tbody>
        </table>
    </div>
    ''' if recurring_rows else ''}
    
    <div class="footer">
        <p>© 2026 RupeeRadar Finance. This report was generated from uploaded bank statement data.</p>
        <p>All data is processed locally and session data is automatically purged within 24 hours.</p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)

# 9. Delete Session
@api_router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already deleted")

    db.delete(session)
    db.commit()
    return {"message": f"Session {session_id} successfully deleted"}
