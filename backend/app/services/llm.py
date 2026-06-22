import os
import json
from typing import List, Dict, Any
# pyrefly: ignore [missing-import]
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

class GroqCategorizationService:
    def __init__(self):
        # Initialize Groq client only if key is available
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    def is_available(self) -> bool:
        return self.client is not None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def categorize_batch(self, transactions: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
        """
        Sends a batch of transaction descriptions to Groq for structured JSON categorization.
        Each transaction dict should contain: 'id', 'description_clean', 'amount', 'type'.
        """
        if not self.is_available():
            # Fallback when Groq is not configured
            return [{"id": t["id"], "category": "Other", "confidence": 0.5} for t in transactions]

        # Prepare transaction representations for prompt efficiency and user PII protection
        payload = [
            {
                "id": tx["id"],
                "description": tx.get("description_clean") or tx.get("description_raw"),
                "type": tx["type"],
                "amount": abs(tx["amount"])
            }
            for tx in transactions
        ]

        system_instruction = (
            f"You are a financial classification assistant. Categorize each transaction into one of these strict categories: {', '.join(categories)}.\n"
            "Return a JSON array containing objects matching this schema:\n"
            '[{"id": "transaction-id", "category": "CategoryName", "confidence": 0.95}]\n'
            "Return ONLY the raw JSON array. Do not include markdown code block styling or text explanations."
        )

        user_prompt = f"Categorize these transactions:\n{json.dumps(payload, indent=2)}"

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                model=GROQ_MODEL,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            # Parse the response
            data = json.loads(result_text)
            
            # Extract transactions list from JSON object if wrapped
            if isinstance(data, dict):
                for key in ["transactions", "results", "data"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # If it's a flat dict containing transactional objects or id mappings
                if "id" in data or len(data) == 0:
                    return [data]
            
            if isinstance(data, list):
                return data

            raise ValueError("LLM response did not map to expected JSON format")
            
        except Exception as e:
            # Propagate exception to trigger tenacity retry
            raise RuntimeError(f"Groq API error: {str(e)}")
