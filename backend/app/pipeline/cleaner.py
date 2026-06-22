import re
from typing import Dict, Any, Tuple

# Common Indian Merchants Dictionary
MERCHANT_MAP = {
    "swiggy": "Swiggy",
    "zomato": "Zomato",
    "amazon": "Amazon",
    "uber": "Uber",
    "ola": "Ola Cabs",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "zepto": "Zepto",
    "blinkit": "Blinkit",
    "blink commerce": "Blinkit",
    "rent": "Rent Payment",
    "salary": "Salary Credit",
    "zerodha": "Zerodha",
    "groww": "Groww",
    "netflix": "Netflix",
    "google play": "Google Play",
    "jio": "Jio Infocomm",
    "airtel": "Airtel",
    "tataplay": "Tata Play",
    "tata sky": "Tata Play",
    "bsnl": "BSNL",
    "electricity": "Electricity Bill",
    "bescom": "BESCOM Bill",
    "actcorp": "ACT Fibernet",
    "make my trip": "MakeMyTrip",
    "makemytrip": "MakeMyTrip",
    "irctc": "IRCTC",
    "lic": "LIC Premium",
    "paytm": "Paytm Wallet",
    "phonepe": "PhonePe Wallet",
    "gpay": "GPay Wallet",
}

def clean_transaction(description_raw: str, amount: float, tx_type: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Cleans the raw bank narration description, extracts the payment mode, merchant, 
    and standardizes amount sign (negative for debits, positive for credits).
    
    Returns:
        (description_clean, payment_mode, metadata)
    """
    desc_upper = description_raw.upper().strip()
    
    # 1. Detect payment mode
    payment_mode = "Other"
    if "UPI" in desc_upper:
        payment_mode = "UPI"
    elif "IMPS" in desc_upper:
        payment_mode = "IMPS"
    elif "NEFT" in desc_upper:
        payment_mode = "NEFT"
    elif "RTGS" in desc_upper:
        payment_mode = "RTGS"
    elif "CASH" in desc_upper or "CHQ" in desc_upper or "CHEQUE" in desc_upper or "ATM" in desc_upper:
        payment_mode = "Cash"
    elif any(term in desc_upper for term in ["CARD", "POS", "VISA", "MAST", "MSD"]):
        payment_mode = "Card"
    elif "ACH" in desc_upper or "ECS" in desc_upper:
        payment_mode = "Auto-Debit (ACH)"
    elif "INT." in desc_upper or "INTEREST" in desc_upper:
        payment_mode = "Interest"
    elif any(term in desc_upper for term in ["TRANSFER", "IFT", "OWN-TRANSFER", "INB"]):
        payment_mode = "Transfer"
        
    # 2. Scrub description using Regex
    cleaned = description_raw
    
    # Strip UPI tags and transaction numbers
    # e.g., UPI/DR/123456789012/Merchant/UPIRef -> Merchant
    cleaned = re.sub(r'UPI/(?:DR|CR)/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'UPI/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'UPI-[^-]+-\d+-', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'IMPS/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'NEFT\s+CR\s+-\s+\w+\s+-', '', cleaned, flags=re.IGNORECASE)
    
    # Strip UPI VPA handles (e.g. user@bank, phone@upi)
    cleaned = re.sub(r'\b[\w.\-_]+@[a-zA-Z0-9.\-_]+\b', '', cleaned)
    
    # Strip timestamps (e.g. 12:34:56 or 12:34)
    cleaned = re.sub(r'\b\d{2}:\d{2}(:\d{2})?\b', '', cleaned)
    
    # Strip alphanumeric transaction IDs (e.g. REF-123 or TXN123456)
    cleaned = re.sub(r'\b(?:REF|TXN|ID|NO)\d+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:REF|TXN|ID|NO)-\d+\b', '', cleaned, flags=re.IGNORECASE)
    
    # Strip random 10-to-12 digit references, phone numbers, or dates (e.g. 2026-06-21)
    cleaned = re.sub(r'\b\d{10,12}\b', '', cleaned)
    cleaned = re.sub(r'\b\d{2}-\d{2}-\d{4}\b', '', cleaned)
    cleaned = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', '', cleaned)
    
    # Strip common transaction headers and city noise
    cleaned = re.sub(r'\b(?:DR|CR|POS|ACH|NEFT|IMPS|RTGS|UPI|OWN-TRANSFER|INB|TRANSFER|FT|INF|ATM)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:MUMBAI|DELHI|BANGALORE|CHENNAI|KOLKATA|HYDERABAD|PUNE|NOIDA|GURGAON|BLR|MUM|DEL)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Strip trailing punctuation, slashes, dashes, extra spaces
    cleaned = re.sub(r'[/\\_\-*+:]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 3. Match against known merchant dictionary
    description_clean = cleaned
    matched_merchant = None
    
    for kw, label in MERCHANT_MAP.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned.lower()):
            description_clean = label
            matched_merchant = label
            break
            
    # Default to formatted cleaned string if no merchant matched
    if not matched_merchant:
        # Title case the cleaned description for readability
        description_clean = cleaned.title()
        # Fallback if cleaning stripped too much
        if not description_clean:
            description_clean = description_raw.strip()
            
    # Formulate metadata
    metadata = {
        "payment_mode": payment_mode,
        "raw_narration": description_raw
    }
    if matched_merchant:
        metadata["merchant_matched"] = matched_merchant
        
    return description_clean, payment_mode, metadata
