from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Transaction, RecurringGroup

def calculate_metrics(transactions: List[Transaction], db: Session) -> Tuple[Dict[str, float], List[Dict[str, Any]], List[Dict[str, Any]]]:
    total_income = 0.0
    total_spend = 0.0
    
    category_sums = {}
    debits = []
    
    for tx in transactions:
        amount = tx.amount
        if tx.type == "debit":
            total_spend += abs(amount)
            cat = tx.category
            category_sums[cat] = category_sums.get(cat, 0.0) + abs(amount)
            debits.append(tx)
        else:
            total_income += abs(amount)
            
    savings = total_income - total_spend
    savings_rate = 0.0
    if total_income > 0:
        savings_rate = (savings / total_income) * 100.0
        
    top_categories = [
        {"category": k, "amount": v} 
        for k, v in sorted(category_sums.items(), key=lambda x: x[1], reverse=True)
    ]
    
    biggest_txs = sorted(debits, key=lambda x: abs(x.amount), reverse=True)[:5]
    biggest_transactions_json = [
        {
            "id": t.id,
            "date": t.date,
            "description_raw": t.description_raw,
            "description_clean": t.description_clean,
            "amount": t.amount,
            "type": t.type,
            "category": t.category
        } for t in biggest_txs
    ]
    
    recurring_total = 0.0
    if transactions:
        session_id = transactions[0].session_id
        recurring_groups = db.query(RecurringGroup).filter(RecurringGroup.session_id == session_id).all()
        for rg in recurring_groups:
            if rg.frequency == "monthly":
                recurring_total += rg.typical_amount
            elif rg.frequency == "weekly":
                recurring_total += rg.typical_amount * 4.33
            elif rg.frequency == "quarterly":
                recurring_total += rg.typical_amount / 3
            elif rg.frequency == "yearly":
                recurring_total += rg.typical_amount / 12
            else:
                recurring_total += rg.typical_amount
                
    metrics = {
        "total_income": total_income,
        "total_spend": total_spend,
        "savings": savings,
        "savings_rate": savings_rate,
        "recurring_total": recurring_total
    }
    
    return metrics, top_categories, biggest_transactions_json
