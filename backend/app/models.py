import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    bank_hint = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | parsing | processing | ready | failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    error_message = Column(String, nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="session", cascade="all, delete-orphan")
    recurring_groups = relationship("RecurringGroup", back_populates="session", cascade="all, delete-orphan")
    analysis_result = relationship("AnalysisResult", uselist=False, back_populates="session", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    line_index = Column(Integer, default=0)  # Edge Case 2.4: Internal line counter to prevent false deduplication of identical same-day purchases
    date = Column(String, nullable=False)  # ISO Date YYYY-MM-DD
    description_raw = Column(String, nullable=False)
    description_clean = Column(String, nullable=True)
    amount = Column(Float, nullable=False)  # signed: + credit, - debit
    type = Column(String, nullable=False)   # credit | debit
    balance = Column(Float, nullable=True)
    category = Column(String, default="Other")
    category_confidence = Column(Float, default=1.0)
    is_recurring = Column(Boolean, default=False)
    recurring_group_id = Column(String, ForeignKey("recurring_groups.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    session = relationship("UploadSession", back_populates="transactions")
    recurring_group = relationship("RecurringGroup", back_populates="transactions")


class RecurringGroup(Base):
    __tablename__ = "recurring_groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)  # e.g., "Netflix", "HDFC EMI"
    category = Column(String, nullable=False)
    frequency = Column(String, default="unknown")  # weekly | monthly | quarterly | yearly | unknown
    typical_amount = Column(Float, nullable=False)
    last_seen_date = Column(String, nullable=True)
    transaction_ids = Column(JSON, default=list)  # list of transaction IDs
    confidence = Column(Float, default=1.0)

    # Relationships
    session = relationship("UploadSession", back_populates="recurring_groups")
    transactions = relationship("Transaction", back_populates="recurring_group", foreign_keys=[Transaction.recurring_group_id])


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), primary_key=True)
    metrics = Column(JSON, nullable=False)  # total income, spend, savings, savings rate, etc.
    top_categories = Column(JSON, nullable=False)  # list of {category, amount}
    biggest_transactions = Column(JSON, nullable=False)  # list of raw transactions
    insights = Column(JSON, nullable=False)  # list of strings
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("UploadSession", back_populates="analysis_result")
