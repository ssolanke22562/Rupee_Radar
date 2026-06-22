import pandas as pd
from datetime import datetime
from typing import List
from backend.app.parsers.protocol import RawTransaction

class ICICISavingsParser:
    def can_parse(self, file_path: str, preview_content: str) -> bool:
        content_lower = preview_content.lower()
        if "icici bank" in content_lower:
            return True
        if "transaction remarks" in content_lower and ("withdrawal amount" in content_lower or "deposit amount" in content_lower):
            return True
        return False

    def parse(self, file_path: str) -> List[RawTransaction]:
        header_row_index = -1
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                line_lower = line.lower()
                if "transaction remarks" in line_lower:
                    header_row_index = idx
                    break
        
        if header_row_index == -1:
            raise ValueError("Could not find ICICI header row containing 'Transaction Remarks'.")
            
        df = pd.read_csv(file_path, skiprows=header_row_index)
        df.columns = [col.strip() for col in df.columns]
        
        # Determine active date column
        date_col = 'Transaction Date' if 'Transaction Date' in df.columns else 'Value Date'
        if date_col not in df.columns:
            # Fallback to the first column containing 'date'
            date_cols = [c for c in df.columns if 'date' in c.lower()]
            if date_cols:
                date_col = date_cols[0]
            else:
                raise ValueError("Could not locate Date column in ICICI statement.")
                
        df = df.dropna(subset=[date_col, 'Transaction Remarks'])
        
        transactions: List[RawTransaction] = []
        
        for _, row in df.iterrows():
            date_str = str(row[date_col]).strip()
            parsed_date = None
            for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y'):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
                    
            if not parsed_date:
                continue
                
            remarks = str(row['Transaction Remarks']).strip()
            if not remarks or "total" in remarks.lower() or "balance" in remarks.lower():
                continue
                
            # Parse amounts (handles spaces/INR tags in ICICI header name)
            withdrawal_col = [c for c in df.columns if 'withdrawal' in c.lower()]
            deposit_col = [c for c in df.columns if 'deposit' in c.lower()]
            balance_col = [c for c in df.columns if 'balance' in c.lower()]
            
            withdrawal_val = str(row[withdrawal_col[0]]).strip().replace(',', '') if withdrawal_col else '0'
            deposit_val = str(row[deposit_col[0]]).strip().replace(',', '') if deposit_col else '0'
            
            withdrawal = 0.0
            deposit = 0.0
            
            try:
                if withdrawal_val and withdrawal_val != 'nan' and withdrawal_val != '0' and withdrawal_val != '0.00':
                    withdrawal = float(withdrawal_val)
            except ValueError:
                pass
                
            try:
                if deposit_val and deposit_val != 'nan' and deposit_val != '0' and deposit_val != '0.00':
                    deposit = float(deposit_val)
            except ValueError:
                pass
                
            if withdrawal > 0:
                amount = -withdrawal
                tx_type = "debit"
            elif deposit > 0:
                amount = deposit
                tx_type = "credit"
            else:
                continue
                
            balance = None
            if balance_col:
                balance_val = str(row[balance_col[0]]).strip().replace(',', '')
                try:
                    if balance_val and balance_val != 'nan':
                        balance = float(balance_val)
                except ValueError:
                    pass
                    
            transactions.append(
                RawTransaction(
                    date=parsed_date,
                    description_raw=remarks,
                    amount=amount,
                    type=tx_type,
                    balance=balance
                )
            )
            
        return transactions
