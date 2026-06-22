import re
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models import Transaction
from backend.app.services.llm import GroqCategorizationService

logger = logging.getLogger(__name__)

# Strict categories supported by the engine
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "EMI", "Subscriptions", "Salary", "Rent", "Investments", "Other"]

# Comprehensive keyword boundaries for Tier 1 matching
CATEGORY_RULES = {
    "Food": ["swiggy", "zomato", "restaurant", "dominos", "kfc", "diner", "eats", "starbucks", "subway", "burger", "cafe", "pizza", "hotel food"],
    "Travel": ["uber", "ola", "cabs", "irctc", "makemytrip", "flight", "railway", "metro", "bus", "ixigo", "redbus", "airline", "auto", "petrol", "fuel", "shell", "hpcl", "bpcl", "indianoil"],
    "Shopping": ["amazon", "flipkart", "myntra", "retail", "zepto", "blinkit", "groceries", "supermarket", "dmart", "reliance", "nykaa", "meesho", "mart", "decathlon", "store", "mall"],
    "Subscriptions": ["netflix", "spotify", "youtube", "prime", "hotstar", "disney", "apple", "google", "premium", "cloud", "saas", "github"],
    "Bills": ["electricity", "bescom", "airtel", "jio", "bsnl", "broadband", "mobile", "recharge", "tata play", "utility", "water", "gas", "insurance", "lic", "postpaid"],
    "EMI": ["emi", "loan", "hdfc bank loan", "sbi loan", "home loan", "car loan", "finance emi"],
    "Salary": ["salary", "acme corp", "payroll", "dividend", "interest", "refund", "credit interest", "csh deposit"],
    "Rent": ["rent", "house rent", "maintenance", "landlord", "flat rent", "pg rent"],
    "Investments": ["zerodha", "groww", "mutual fund", "sip", "investment", "bonds", "stock", "etf", "indmoney", "coindcx", "upstox"]
}

def match_rules(desc: str) -> Optional[str]:
    """Matches a transaction clean description against rules-based categories."""
    desc_lower = desc.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', desc_lower) for kw in keywords):
            return category
    return None

def sanitize_for_llm(desc: str) -> str:
    """Masks card details, account numbers, and email IDs to guard user privacy."""
    if not desc:
        return ""
    # Mask card numbers (e.g., 4111-2222-3333-4444 or 4111 2222 3333 4444)
    desc = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX', desc)
    # Mask sequences of 4-18 digits (account/reference codes) with 'XXXX'
    desc = re.sub(r'\b\d{4,18}\b', 'XXXX', desc)
    # Mask emails
    desc = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b', 'XXXX@XXXX.XXX', desc)
    return desc

def categorize_transactions(transactions: List[Transaction], db: Session):
    """
    Categorizes all transactions in a session. First applies deterministic rules (Tier 1),
    then batches unmatched transactions to Groq (Tier 2) with a fallback to 'Other'.
    """
    llm_service = GroqCategorizationService()
    unmatched_txs: List[Transaction] = []

    # Tier 1: Rules-Based Matching
    for tx in transactions:
        rule_cat = match_rules(tx.description_clean or tx.description_raw)
        if rule_cat:
            tx.category = rule_cat
            tx.category_confidence = 1.0
        else:
            unmatched_txs.append(tx)

    # Tier 2: Batch LLM Categorization
    if unmatched_txs:
        batch_size = 30
        for i in range(0, len(unmatched_txs), batch_size):
            batch = unmatched_txs[i:i+batch_size]
            
            # Formulate payload using sanitized/masked text
            batch_payload = []
            for tx in batch:
                sanitized_desc = sanitize_for_llm(tx.description_clean or tx.description_raw)
                batch_payload.append({
                    "id": tx.id,
                    "description_clean": sanitized_desc,
                    "type": tx.type,
                    "amount": tx.amount
                })

            try:
                # Call Groq API service
                results = llm_service.categorize_batch(batch_payload, CATEGORIES)
                results_map = {res["id"]: res for res in results if isinstance(res, dict) and "id" in res}

                # Map classifications back to transactions
                for tx in batch:
                    res = results_map.get(tx.id)
                    if res:
                        category = res.get("category")
                        confidence = res.get("confidence", 0.8)
                        
                        # Validate the category value and confidence score
                        if category in CATEGORIES and confidence >= 0.6:
                            tx.category = category
                            tx.category_confidence = confidence
                        else:
                            tx.category = "Other"
                            tx.category_confidence = confidence
                    else:
                        tx.category = "Other"
                        tx.category_confidence = 0.5
            except Exception as e:
                logger.error(f"Error during batch LLM categorization: {str(e)}")
                # Fallback to "Other" for this batch so processing doesn't crash
                for tx in batch:
                    tx.category = "Other"
                    tx.category_confidence = 0.5

    # Persist categorizations
    db.commit()
