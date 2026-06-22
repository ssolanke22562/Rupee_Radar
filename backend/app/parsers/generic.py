import pandas as pd
import re
from datetime import datetime
from typing import List, Tuple, Optional
from backend.app.parsers.protocol import RawTransaction

class GenericCSVParser:
    def can_parse(self, file_path: str, preview_content: str) -> bool:
        # Fallback parser, returns True for any CSV
        return file_path.endswith('.csv') or file_path.endswith('.txt')

    def parse(self, file_path: str) -> List[RawTransaction]:
        # Step 1: Find the line containing the headers
        header_row_index = -1
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                # If there are common transaction keywords
                line_lower = line.lower()
                if "date" in line_lower and ("amount" in line_lower or "narration" in line_lower or "description" in line_lower or "debit" in line_lower):
                    header_row_index = idx
                    break
        
        if header_row_index != -1:
            df = pd.read_csv(file_path, skiprows=header_row_index)
            df.columns = [str(col).strip() for col in df.columns]
        else:
            # No standard headers found, read without headers
            df = pd.read_csv(file_path, header=None)
            df.columns = [str(col).strip() for col in df.columns]
        
        # Step 2: Resolve column mappings dynamically
        date_col = self._find_col(df.columns, ['date', 'txn date', 'transaction date', 'value date'])
        desc_col = self._find_col(df.columns, ['description', 'narration', 'remarks', 'particulars', 'details'])
        
        debit_col = self._find_col(df.columns, ['debit', 'withdrawal', 'dr'])
        credit_col = self._find_col(df.columns, ['credit', 'deposit', 'cr'])
        amount_col = self._find_col(df.columns, ['amount', 'txn amount', 'transaction amount'])
        type_col = self._find_col(df.columns, ['type', 'txn type', 'credit/debit', 'cr/dr'])
        balance_col = self._find_col(df.columns, ['balance', 'closing balance', 'bal'])

        # Fallback to content-based detection if essential columns are missing
        if not date_col or not desc_col:
            f_date, f_desc, f_debit, f_credit, f_amount = self._detect_columns_by_content(df)
            if f_date is not None and f_desc is not None:
                date_col = str(f_date)
                desc_col = str(f_desc)
                if f_debit is not None: debit_col = str(f_debit)
                if f_credit is not None: credit_col = str(f_credit)
                if f_amount is not None: amount_col = str(f_amount)

        if not date_col or not desc_col:
            raise ValueError(f"Could not map required columns. Detected columns: {list(df.columns)}")
            
        df = df.dropna(subset=[date_col, desc_col])
        
        transactions: List[RawTransaction] = []
        
        for _, row in df.iterrows():
            date_str = str(row[date_col]).strip()
            parsed_date = None
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%d %b %Y', '%Y/%m/%d'):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
                    
            if not parsed_date:
                continue
                
            description = str(row[desc_col]).strip()
            if not description or "total" in description.lower() or "balance" in description.lower():
                continue
                
            amount = 0.0
            tx_type = "debit"
            
            # Scenario A: Separate Debit and Credit columns
            if debit_col or credit_col:
                debit_val = 0.0
                credit_val = 0.0
                if debit_col and debit_col in df.columns:
                    try:
                        val = str(row[debit_col]).strip().replace(',', '')
                        if val and val != 'nan' and val != '0' and val != '0.00':
                            debit_val = float(val)
                    except ValueError:
                        pass
                if credit_col and credit_col in df.columns:
                    try:
                        val = str(row[credit_col]).strip().replace(',', '')
                        if val and val != 'nan' and val != '0' and val != '0.00':
                            credit_val = float(val)
                    except ValueError:
                        pass
                        
                if debit_val > 0:
                    amount = -debit_val
                    tx_type = "debit"
                elif credit_val > 0:
                    amount = credit_val
                    tx_type = "credit"
                else:
                    continue
                    
            # Scenario B: Single Amount column + Type column
            elif amount_col and amount_col in df.columns:
                try:
                    raw_amount = float(str(row[amount_col]).strip().replace(',', ''))
                except ValueError:
                    continue
                    
                if type_col and type_col in df.columns:
                    type_val = str(row[type_col]).strip().lower()
                    if 'credit' in type_val or 'cr' in type_val or type_val == 'c':
                        amount = abs(raw_amount)
                        tx_type = "credit"
                    else:
                        amount = -abs(raw_amount)
                        tx_type = "debit"
                else:
                    # Fallback to signing of amount
                    if raw_amount < 0:
                        amount = raw_amount
                        tx_type = "debit"
                    else:
                        amount = raw_amount
                        tx_type = "credit"
            else:
                continue
                
            balance = None
            if balance_col and balance_col in df.columns:
                try:
                    val = str(row[balance_col]).strip().replace(',', '')
                    if val and val != 'nan':
                        balance = float(val)
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

    def _find_col(self, columns: List[str], keywords: List[str]) -> Optional[str]:
        for kw in keywords:
            for col in columns:
                if col.lower() == kw:
                    return col
        for kw in keywords:
            for col in columns:
                if kw in col.lower():
                    return col
        return None

    def _detect_columns_by_content(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Attempts to detect Date, Description, and Amount columns by analyzing row content
        when header-based keyword matching fails.
        Returns (date_col, desc_col, debit_col, credit_col, amount_col)
        """
        date_col = None
        desc_col = None
        debit_col = None
        credit_col = None
        amount_col = None

        # Sample up to 100 rows for analysis
        sample_df = df.head(100)
        col_stats = {}

        for col in df.columns:
            non_null_series = sample_df[col].dropna()
            if non_null_series.empty:
                continue

            date_matches = 0
            float_matches = 0
            string_lengths = []
            
            for val in non_null_series:
                val_str = str(val).strip()
                if not val_str:
                    continue
                
                # Check for Date patterns
                is_date = False
                if re.match(r'^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$', val_str):
                    is_date = True
                elif re.match(r'^\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}$', val_str):
                    is_date = True
                elif re.match(r'^\d{1,2}[/\-.\s][a-zA-Z]{3,}[/\-.\s]\d{2,4}$', val_str):
                    is_date = True
                
                if is_date:
                    date_matches += 1
                
                # Check for Float patterns
                try:
                    cleaned_val = val_str.replace(',', '').replace('₹', '').strip()
                    float(cleaned_val)
                    float_matches += 1
                except ValueError:
                    pass
                
                string_lengths.append(len(val_str))

            n = len(non_null_series)
            if n == 0:
                continue
                
            col_stats[col] = {
                "date_ratio": date_matches / n,
                "float_ratio": float_matches / n,
                "avg_len": sum(string_lengths) / n if string_lengths else 0,
                "name_lower": str(col).lower()
            }

        # 1. Identify Date Column (highest date ratio > 0.5)
        date_candidates = [col for col, stats in col_stats.items() if stats["date_ratio"] > 0.5]
        if date_candidates:
            date_col = max(date_candidates, key=lambda c: col_stats[c]["date_ratio"])

        # 2. Identify Numeric Columns
        # High float ratio, not the date column
        numeric_candidates = [col for col, stats in col_stats.items() if stats["float_ratio"] > 0.6 and col != date_col]
        
        # 3. Identify Description Column
        text_candidates = [col for col, stats in col_stats.items() if col != date_col and col not in numeric_candidates]
        if text_candidates:
            prefer_keywords = ['desc', 'narrat', 'remark', 'partic', 'detail', 'payee']
            preferred = [c for c in text_candidates if any(k in col_stats[c]["name_lower"] for k in prefer_keywords)]
            if preferred:
                desc_col = preferred[0]
            else:
                desc_col = max(text_candidates, key=lambda c: col_stats[c]["avg_len"])
        elif not df.columns.empty:
            remaining = [col for col in df.columns if col != date_col and col not in numeric_candidates]
            if remaining:
                desc_col = remaining[0]

        # Distribute numeric columns
        if len(numeric_candidates) >= 2:
            debits = [c for c in numeric_candidates if any(k in col_stats[c]["name_lower"] for k in ['debit', 'withdrawal', 'dr', 'out', 'payment'])]
            credits = [c for c in numeric_candidates if any(k in col_stats[c]["name_lower"] for k in ['credit', 'deposit', 'cr', 'in', 'received'])]
            if debits:
                debit_col = debits[0]
            if credits:
                credit_col = credits[0]
            
            remaining = [c for c in numeric_candidates if c not in (debit_col, credit_col)]
            if not debit_col and remaining:
                debit_col = remaining.pop(0)
            if not credit_col and remaining:
                credit_col = remaining.pop(0)
        elif len(numeric_candidates) == 1:
            amount_col = numeric_candidates[0]

        # Convert back to original format (string or integer)
        return date_col, desc_col, debit_col, credit_col, amount_col
