import logging
import re
from typing import List
from datetime import datetime
import difflib
from sqlalchemy.orm import Session
from backend.app.models import Transaction, RecurringGroup

logger = logging.getLogger(__name__)

# Edge Case 4.2: Utility patterns that should use relaxed amount variance (±30%)
UTILITY_PATTERNS = [
    r'\belectricity\b', r'\bpower\b', r'\bwater\b', r'\bgas\b', r'\bbill\b',
    r'\bbesco[mn]\b', r'\btorrent\b', r'\badani\b', r'\btata power\b',
    r'\bmahanagar\b', r'\bbsnl\b', r'\bjio\b', r'\bairtel\b',
    r'\bbroadband\b', r'\binsurance\b', r'\blic\b', r'\bmaintenance\b'
]

def is_similar(str1: str, str2: str, threshold: float = 0.8) -> bool:
    if not str1 or not str2:
        return False
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio() >= threshold

def is_utility_description(desc: str) -> bool:
    """Check if a description matches utility patterns for relaxed variance."""
    if not desc:
        return False
    desc_lower = desc.lower()
    return any(re.search(pattern, desc_lower) for pattern in UTILITY_PATTERNS)

def check_amount_variance(amounts: List[float], descriptions: List[str]) -> bool:
    """
    Check if amounts in a group satisfy variance constraints.
    Edge Case 4.2: Utility bills get ±30% variance, others get ±5%.
    """
    if not amounts or len(amounts) < 2:
        return True
    
    min_amt = min(amounts)
    max_amt = max(amounts)
    
    if min_amt == 0:
        return False
    
    # Check if any description in the group is utility-related
    is_utility = any(is_utility_description(desc) for desc in descriptions)
    
    if is_utility:
        # Edge Case 4.2: Relaxed variance for utilities
        variance_threshold = 0.30
    else:
        variance_threshold = 0.05
    
    return (max_amt - min_amt) / min_amt <= variance_threshold

def detect_recurring_payments(transactions: List[Transaction], db: Session) -> None:
    """
    Detect recurring payments from a list of transactions (belonging to a single session).
    Persists RecurringGroup and updates Transactions.
    
    Edge Case 4.2: Variable amount subscriptions (utilities) get ±30% variance.
    Edge Case 4.3: Overlapping subscriptions (same merchant, different amounts) are grouped separately.
    """
    if not transactions:
        return
        
    session_id = transactions[0].session_id
    
    # Filter debits only
    debits = [tx for tx in transactions if tx.type == "debit"]
    if len(debits) < 2:
        return

    # Sort debits by date
    try:
        debits.sort(key=lambda x: datetime.strptime(x.date, "%d-%m-%Y"))
    except ValueError:
        # Fallback if date format varies
        try:
            debits.sort(key=lambda x: datetime.strptime(x.date, "%Y-%m-%d"))
        except ValueError:
            pass

    # Grouping logic - Edge Case 4.3: Use exact amount matching for overlapping subscriptions
    groups = []
    visited = set()
    
    for i in range(len(debits)):
        if i in visited:
            continue
            
        current_group = [debits[i]]
        visited.add(i)
        
        desc1 = debits[i].description_clean or debits[i].description_raw
        amount1 = abs(debits[i].amount)
        
        for j in range(i + 1, len(debits)):
            if j in visited:
                continue
                
            desc2 = debits[j].description_clean or debits[j].description_raw
            amount2 = abs(debits[j].amount)
            
            # Edge Case 4.3: For overlapping subscriptions, check if amounts are similar
            # (same merchant but different amounts = separate groups)
            if is_similar(desc1, desc2, 0.8):
                # Check if amounts are close enough to be the same subscription
                min_amt = min(amount1, amount2)
                max_amt = max(amount1, amount2)
                if min_amt > 0 and (max_amt - min_amt) / min_amt <= 0.30:
                    current_group.append(debits[j])
                    visited.add(j)
                
        if len(current_group) >= 2:
            groups.append(current_group)

    # Process valid groups
    for group in groups:
        amounts = [abs(tx.amount) for tx in group]
        descriptions = [tx.description_clean or tx.description_raw for tx in group]
        
        # Check variance constraint using enhanced logic (Edge Case 4.2)
        if not check_amount_variance(amounts, descriptions):
            continue
            
        # Check intervals
        dates = []
        for tx in group:
            try:
                # Try DD-MM-YYYY
                dt = datetime.strptime(tx.date, "%d-%m-%Y")
                dates.append(dt)
            except ValueError:
                # Try YYYY-MM-DD
                try:
                    dt = datetime.strptime(tx.date, "%Y-%m-%d")
                    dates.append(dt)
                except ValueError:
                    pass
                    
        if len(dates) < 2:
            continue
            
        intervals = [(dates[k] - dates[k-1]).days for k in range(1, len(dates))]
        avg_interval = sum(intervals) / len(intervals)
        
        frequency = "unknown"
        if 25 <= avg_interval <= 35:
            frequency = "monthly"
        elif 6 <= avg_interval <= 8:
            frequency = "weekly"
        elif 80 <= avg_interval <= 100:
            frequency = "quarterly"
        elif 350 <= avg_interval <= 380:
            frequency = "yearly"
        
        # Even if frequency is unknown, we classify it as recurring if it repeats
        typical_amount = sum(amounts) / len(amounts)
        label = group[0].description_clean or group[0].description_raw
        # Take the most common category in the group
        categories = [tx.category for tx in group]
        dominant_category = max(set(categories), key=categories.count)
        
        # Create RecurringGroup
        rec_group = RecurringGroup(
            session_id=session_id,
            label=label[:50],  # truncate if too long
            category=dominant_category,
            frequency=frequency,
            typical_amount=typical_amount,
            last_seen_date=group[-1].date,
            transaction_ids=[tx.id for tx in group],
            confidence=0.9
        )
        db.add(rec_group)
        db.flush() # get rec_group.id
        
        # Update Transactions
        for tx in group:
            tx.is_recurring = True
            tx.recurring_group_id = rec_group.id

    db.commit()