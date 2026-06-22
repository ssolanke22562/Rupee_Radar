from typing import List, Dict, Any

def generate_insights(transactions_count: int, metrics: Dict[str, float], top_categories: List[Dict[str, Any]], biggest_transactions: List[Dict[str, Any]]) -> List[str]:
    insights = []
    insights.append(
        f"We parsed {transactions_count} total transactions across your statement."
    )
    
    if top_categories:
        primary_cat = top_categories[0]
        insights.append(
            f"Your largest spending category was {primary_cat['category']} totaling ₹{primary_cat['amount']:,.2f}."
        )
        
    if biggest_transactions:
        top_tx = biggest_transactions[0]
        amount_abs = abs(top_tx["amount"])
        desc = top_tx["description_clean"] or top_tx["description_raw"]
        insights.append(
            f"Your biggest single spend was ₹{amount_abs:,.2f} to {desc} on {top_tx['date']}."
        )
        
    total_income = metrics.get("total_income", 0.0)
    savings_rate = metrics.get("savings_rate", 0.0)
    total_spend = metrics.get("total_spend", 0.0)
    recurring_total = metrics.get("recurring_total", 0.0)
    
    if total_income > 0:
        insights.append(
            f"Your net savings rate is {savings_rate:.1f}% of your total monthly income."
        )
    else:
        insights.append(
            f"No salary credits detected inside this statement range. Spends totaled ₹{total_spend:,.2f}."
        )
        
    if recurring_total > 0:
        insights.append(
            f"You have approximately ₹{recurring_total:,.2f} in fixed recurring payments each month."
        )
        
    return insights
