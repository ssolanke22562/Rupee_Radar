import pandas as pd
from datetime import datetime
from typing import List
from backend.app.parsers.protocol import RawTransaction

class SBISavingsParser:
    def can_parse(self, file_path: str, preview_content: str) -> bool:
        content_lower = preview_content.lower()
        if "state bank of india" in content_lower or "sbi statement" in content_lower:
            return True
        if "txn date" in content_lower and "ref no./cheque no." in content_lower and "debit" in content_lower and "credit" in content_lower:
            return True
        return False

    def parse(self, file_path: str) -> List[RawTransaction]:
        header_row_index = -1
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                line_lower = line.lower()
                if "txn date" in line_lower and "description" in line_lower:
                    header_row_index = idx
                    break
                    
        if header_row_index == -1:
            raise ValueError("Could not find SBI header row containing 'Txn Date' and 'Description'.")
            
        df = pd.read_csv(file_path, skiprows=header_row_index)
        df.columns = [col.strip() for col in df.columns]
        
        df = df.dropna(subset=['Txn Date', 'Description'])
        
        transactions: List[RawTransaction] = []
        
        for _, row in df.iterrows():
            date_str = str(row['Txn Date']).strip()
            parsed_date = None
            for fmt in ('%d %b %Y', '%d-%b-%Y', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y'):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
                    
            if not parsed_date:
                continue
                
            description = str(row['Description']).strip()
            if not description or "total" in description.lower() or "balance" in description.lower():
                continue
                
            debit_str = str(row.get('Debit', '0')).strip().replace(',', '')
            credit_str = str(row.get('Credit', '0')).strip().replace(',', '')
            
            debit = 0.0
            credit = 0.0
            
            try:
                if debit_str and debit_str != 'nan' and debit_str != '0' and debit_str != '0.00' and debit_str != '':
                    debit = float(debit_str)
            except ValueError:
                pass
                
            try:
                if credit_str and credit_str != 'nan' and credit_str != '0' and credit_str != '0.00' and credit_str != '':
                    credit = float(credit_str)
            except ValueError:
                pass
                
            if debit > 0:
                amount = -debit
                tx_type = "debit"
            elif credit > 0:
                amount = credit
                tx_type = "credit"
            else:
                continue
                
            balance_str = str(row.get('Balance', '0')).strip().replace(',', '')
            balance = None
            try:
                if balance_str and balance_str != 'nan':
                    balance = float(balance_str)
            except ValueError:
                pass
                
            transactions.append(
                RawTransaction(
                    date=parsed_date,
                    description_raw=description,
                    amount=amount,
                    type=tx_type,
                    balance=balance
                )
            )
            
        return transactions
