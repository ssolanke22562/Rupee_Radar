import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import Base
from backend.app.models import UploadSession, Transaction, AnalysisResult
from backend.app.parsers.detector import parse_statement
from backend.app.pipeline.cleaner import clean_transaction
from backend.app.pipeline.manager import process_upload_session

HDFC_CSV_CONTENT = """HDFC Bank Savings Account Statement
Date,Narration,Chq./Ref.No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance
18/06/26,UPI/920193021/ZOMATO-DELHI,920193021,18/06/26,650.00,0.00,15000.00
15/06/26,ACH/NETFLIX-MEMBER-CARD,ACH9102,15/06/26,649.00,0.00,14351.00
10/06/26,SALARY/ACME-CORP/DIR-DEP,SAL101,10/06/26,0.00,85000.00,99351.00
"""

ICICI_CSV_CONTENT = """ICICI Bank Statement
S No.,Value Date,Transaction Date,Cheque Number,Transaction Remarks,Withdrawal Amount (INR ),Deposit Amount (INR ),Balance (INR )
1,18/06/2026,18/06/2026,CHQ1,UPI/382019283/AMAZON-RETAIL,4500.00,0.00,10500.00
2,02/06/2026,02/06/2026,CHQ2,UPI/OLA-CABS-RIDE-PAY,380.00,0.00,10120.00
"""

SBI_CSV_CONTENT = """SBI Bank Statement
Txn Date,Value Date,Description,Ref No./Cheque No.,Debit,Credit,Balance
10 Jun 2026,10 Jun 2026,TRANSFER FROM SBI TO HDFC,REF992,15000.00,,5000.00
"""

class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Create SQLite in-memory database for testing
        self.engine = create_engine("sqlite:///:memory:")
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_hdfc_parser(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(HDFC_CSV_CONTENT)
            temp_path = f.name

        try:
            txs = parse_statement(temp_path, "hdfc")
            self.assertEqual(len(txs), 3)
            self.assertEqual(txs[0].description_raw, "UPI/920193021/ZOMATO-DELHI")
            self.assertEqual(txs[0].amount, -650.00)
            self.assertEqual(txs[0].type, "debit")
            self.assertEqual(txs[2].amount, 85000.00)
            self.assertEqual(txs[2].type, "credit")
        finally:
            os.remove(temp_path)

    def test_icici_parser(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(ICICI_CSV_CONTENT)
            temp_path = f.name

        try:
            txs = parse_statement(temp_path, "icici")
            self.assertEqual(len(txs), 2)
            self.assertEqual(txs[0].description_raw, "UPI/382019283/AMAZON-RETAIL")
            self.assertEqual(txs[0].amount, -4500.00)
            self.assertEqual(txs[1].amount, -380.00)
        finally:
            os.remove(temp_path)

    def test_sbi_parser(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(SBI_CSV_CONTENT)
            temp_path = f.name

        try:
            txs = parse_statement(temp_path, "sbi")
            self.assertEqual(len(txs), 1)
            self.assertEqual(txs[0].description_raw, "TRANSFER FROM SBI TO HDFC")
            self.assertEqual(txs[0].amount, -15000.00)
        finally:
            os.remove(temp_path)

    def test_cleaner(self):
        # Test Swiggy UPI regex cleaning
        clean_desc, mode, meta = clean_transaction("UPI/DR/2026/SWIGGY/BANGALORE", -450.00, "debit")
        self.assertEqual(clean_desc, "Swiggy")
        self.assertEqual(mode, "UPI")

        # Test Zomato card cleaning
        clean_desc, mode, meta = clean_transaction("CARD POS ZOMATO DELHI", -650.00, "debit")
        self.assertEqual(clean_desc, "Zomato")
        self.assertEqual(mode, "Card")

    def test_manager_pipeline_end_to_end(self):
        # Create a mock session
        session = UploadSession(
            id="test-session-123",
            filename="hdfc_mock.csv",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(session)
        self.db.commit()

        # Write statement file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(HDFC_CSV_CONTENT)
            temp_path = f.name

        try:
            process_upload_session("test-session-123", temp_path, "hdfc", self.db)
            
            # Verify database changes
            updated_session = self.db.query(UploadSession).filter(UploadSession.id == "test-session-123").first()
            self.assertEqual(updated_session.status, "ready")
            
            txs = self.db.query(Transaction).filter(Transaction.session_id == "test-session-123").all()
            self.assertEqual(len(txs), 3)
            
            # Zomato categorizes as Food
            zomato_tx = next(t for t in txs if "Zomato" in t.description_clean)
            self.assertEqual(zomato_tx.category, "Food")
            
            # Verify AnalysisResult
            analysis = self.db.query(AnalysisResult).filter(AnalysisResult.session_id == "test-session-123").first()
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis.metrics["total_income"], 85000.00)
            self.assertEqual(analysis.metrics["total_spend"], 1299.00)
            self.assertEqual(len(analysis.insights), 4)
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
