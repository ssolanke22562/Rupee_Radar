from typing import Protocol, List, Optional
from pydantic import BaseModel

class RawTransaction(BaseModel):
    date: str  # YYYY-MM-DD
    description_raw: str
    amount: float  # Signed: negative for debit, positive for credit
    type: str  # "credit" | "debit"
    balance: Optional[float] = None

class StatementParser(Protocol):
    def can_parse(self, file_path: str, preview_content: str) -> bool:
        """
        Returns True if this parser is capable of parsing the given file contents.
        """
        ...

    def parse(self, file_path: str) -> List[RawTransaction]:
        """
        Parses the statement file and returns a list of RawTransaction objects.
        """
        ...
