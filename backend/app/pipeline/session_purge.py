import os
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
from backend.app.database import SessionLocal
from backend.app.models import UploadSession

logger = logging.getLogger(__name__)

# Configurable TTL (default 24 hours, can be overridden via env)
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))

# Temp uploads directory
TEMP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "temp_uploads"
)

def purge_expired_sessions():
    """
    Phase 6.1: Deletes database sessions and physical uploaded files older than SESSION_TTL_HOURS.
    Uses ON DELETE CASCADE to clean up transactions, recurring_groups, and analysis_results.
    """
    db: DBSession = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
        
        # Find expired sessions
        expired_sessions = db.query(UploadSession).filter(
            UploadSession.expires_at < cutoff_time
        ).all()
        
        if not expired_sessions:
            return  # Nothing to purge
        
        logger.info(f"Purging {len(expired_sessions)} expired session(s)...")
        
        for session in expired_sessions:
            session_id = session.id
            
            # Delete physical uploaded files if they still exist
            temp_dir = TEMP_DIR
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    if filename.startswith(session_id):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted temp file: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete temp file {file_path}: {e}")
            
            # Delete the session (cascades to transactions, recurring_groups, analysis_results)
            db.delete(session)
            logger.info(f"Purged session {session_id} (expired at {session.expires_at})")
        
        db.commit()
        logger.info(f"Successfully purged {len(expired_sessions)} expired session(s).")
        
    except Exception as e:
        logger.error(f"Error during session purge: {str(e)}")
        db.rollback()
    finally:
        db.close()

def start_purge_worker():
    """
    Background worker that runs purge_expired_sessions every 30 minutes.
    Runs as a daemon thread.
    """
    while True:
        try:
            purge_expired_sessions()
        except Exception as e:
            logger.error(f"Purge worker error: {str(e)}")
        
        # Sleep for 30 minutes before next check
        time.sleep(1800)  # 30 minutes