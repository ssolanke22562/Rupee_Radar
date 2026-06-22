import pandas as pd
import re
from datetime import datetime
from typing import List
from backend.app.parsers.protocol import RawTransaction

class HDFCSavingsParser:
    def can_parse(self, file_path: str, preview_content: str) -> bool:
        content_lower = preview_content.lower()
        # Must contain HDFC Bank branding or specific signature columns
        if "hdfc bank" in content_lower:
            return True
        if "chq./ref.no." in content_lower and ("withdrawal amt." in content_lower or "deposit amt." in content_lower):
            return True
        return False

    def parse(self, file_path: str) -> List[RawTransaction]:
        # Step 1: Find the header line
        header_row_index = -1
        headers = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                line_lower = line.lower()
                if "narration" in line_lower and "date" in line_lower:
                    header_row_index = idx
                    # Normalize headers
                    headers = [col.strip() for col in line.split(',')]
                    break
        
        if header_row_index == -1:
            raise ValueError("Could not find HDFC header row containing 'Narration' and 'Date'.")
            
        # Step 2: Read CSV starting from the header row
        df = pd.read_csv(file_path, skiprows=header_row_index)
        
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Drop rows where Date or Narration is null
        df = df.dropna(subset=['Date', 'Narration'])
        
        transactions: List[RawTransaction] = []
        
        for _, row in df.iterrows():
            date_str = str(row['Date']).strip()
            # Try to parse date (commonly DD/MM/YY or DD/MM/YYYY)
            parsed_date = None
            for fmt in ('%d/%m/%y', '%d/%m/%Y', '%d-%m-%Y', '%d-%m-%y'):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                # If date is unparseable (e.g. footer summary row), skip it
                continue
                
            narration = str(row['Narration']).strip()
            if not narration or "statement summary" in narration.lower():
                continue
                
            # Parse Withdrawal and Deposit amounts
            withdrawal_str = str(row.get('Withdrawal Amt.', '0')).strip().replace(',', '')
            deposit_str = str(row.get('Deposit Amt.', '0')).strip().replace(',', '')
            
            withdrawal = 0.0
            deposit = 0.0
            
            try:
                if withdrawal_str and withdrawal_str != 'nan' and withdrawal_str != '0' and withdrawal_str != '0.00':
                    withdrawal = float(withdrawal_str)
            except ValueError:
                pass
                
            try:
                if deposit_str and deposit_str != 'nan' and deposit_str != '0' and deposit_str != '0.00':
                    deposit = float(deposit_str)
            except ValueError:
                pass
            
            # Amount sign convention: debits negative, credits positive
            if withdrawal > 0:
                amount = -withdrawal
                tx_type = "debit"
            elif deposit > 0:
                amount = deposit
                tx_type = "credit"
            else:
                # If both are empty or 0, check if amount is represented in a single column
                continue
                
            balance_str = str(row.get('Closing Balance', '0')).strip().replace(',', '')
            balance = None
            try:
                if balance_str and balance_str != 'nan':
                    balance = float(balance_str)
            except ValueError:
                pass
                
            transactions.append(
                RawTransaction(
                    date=parsed_date,
                    description_raw=narration,
                    amount=amount,
                    type=tx_type,
                    balance=balance
                )
            )
            
        return transactions
