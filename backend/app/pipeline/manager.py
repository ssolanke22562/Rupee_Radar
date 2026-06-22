import os
import logging
from sqlalchemy.orm import Session
from backend.app.models import UploadSession, Transaction, AnalysisResult
from backend.app.parsers.detector import parse_statement
from backend.app.pipeline.cleaner import clean_transaction
from backend.app.pipeline.categorizer import categorize_transactions

logger = logging.getLogger(__name__)

def process_upload_session(session_id: str, file_path: str, bank_hint: str, db: Session):
    session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not session:
        logger.error(f"UploadSession {session_id} not found.")
        return
        
    try:
        # Step 1: Update status to parsing
        session.status = "parsing"
        db.commit()
        
        # Step 2: Parse raw transactions
        raw_txs = parse_statement(file_path, bank_hint)
        if not raw_txs:
            raise ValueError("No valid transaction records were found in the uploaded statement.")
            
        # Step 3: Update status to processing
        session.status = "processing"
        db.commit()
        
        # Step 4: Process and save transactions
        db_transactions = []
        total_income = 0.0
        total_spend = 0.0
        
        for idx, raw_tx in enumerate(raw_txs):
            cleaned_desc, mode, meta = clean_transaction(
                raw_tx.description_raw, 
                raw_tx.amount, 
                raw_tx.type
            )
            
            # Enforce amount math: signed values
            amount = raw_tx.amount
            if raw_tx.type == "debit":
                amount = -abs(amount)
                total_spend += abs(amount)
            else:
                amount = abs(amount)
                total_income += amount
                
            db_tx = Transaction(
                session_id=session_id,
                line_index=idx,
                date=raw_tx.date,
                description_raw=raw_tx.description_raw,
                description_clean=cleaned_desc,
                amount=amount,
                type=raw_tx.type,
                balance=raw_tx.balance,
                category="Other",
                category_confidence=0.0,
                is_recurring=False,
                metadata_json=meta
            )
            db.add(db_tx)
            db_transactions.append(db_tx)
            
        db.commit()
        
        # Step 4.5: Run Hybrid Categorization Engine
        categorize_transactions(db_transactions, db)
        
        # Step 4.6: Detect Recurring Payments
        from backend.app.pipeline.recurring import detect_recurring_payments
        detect_recurring_payments(db_transactions, db)
        
        # Step 5: Calculate metrics & template-based insights
        from backend.app.pipeline.metrics import calculate_metrics
        from backend.app.pipeline.insights import generate_insights
        
        metrics, top_categories, biggest_transactions_json = calculate_metrics(db_transactions, db)
        insights = generate_insights(len(db_transactions), metrics, top_categories, biggest_transactions_json)
        
        analysis = AnalysisResult(
            session_id=session_id,
            metrics=metrics,
            top_categories=top_categories,
            biggest_transactions=biggest_transactions_json,
            insights=insights
        )
        db.add(analysis)
        
        # Transition session to ready
        session.status = "ready"
        db.commit()
        
    except Exception as e:
        logger.exception("Error processing statement session.")
        session.status = "failed"
        session.error_message = str(e)
        db.commit()
        
    finally:
        # Step 6: Delete the uploaded file from temp storage
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as ex:
                logger.error(f"Failed to delete temp file {file_path}: {ex}")
