from typing import Optional, List
from backend.app.parsers.protocol import RawTransaction, StatementParser
from backend.app.parsers.hdfc import HDFCSavingsParser
from backend.app.parsers.icici import ICICISavingsParser
from backend.app.parsers.sbi import SBISavingsParser
from backend.app.parsers.generic import GenericCSVParser

def parse_statement(file_path: str, bank_hint: Optional[str] = None) -> List[RawTransaction]:
    # Select parser
    parser: Optional[StatementParser] = None
    
    if bank_hint:
        hint_lower = bank_hint.lower()
        if "hdfc" in hint_lower:
            parser = HDFCSavingsParser()
        elif "icici" in hint_lower:
            parser = ICICISavingsParser()
        elif "sbi" in hint_lower:
            parser = SBISavingsParser()
            
    if not parser:
        # Auto-detect format
        preview = ""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                preview = f.read(2048)
        except Exception:
            pass
            
        parsers = [
            HDFCSavingsParser(),
            ICICISavingsParser(),
            SBISavingsParser()
        ]
        
        for p in parsers:
            if p.can_parse(file_path, preview):
                parser = p
                break
                
    if not parser:
        # Fallback
        parser = GenericCSVParser()
        
    return parser.parse(file_path)
