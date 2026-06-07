from typing import Dict, List, Tuple, Optional
import re

PII_PATTERNS = {
    "credit_card": r"\b(?:\d[ -]*?){13,19}\b",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "pan_card": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "ifsc_code": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "account_number": r"\b\d{9,18}\b",  # Broad — tune per bank format
    "email": r"\b[\w.-]+@[\w.-]+\.\w{2,}\b",
    "phone_india": r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
}

def detect_pii(text: str) -> Dict[str, list]:
    
    found = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found[pii_type] = matches
    return found

def redact_pii(text: str) -> str:
    
    redacted = text
    for pii_type, pattern in PII_PATTERNS.items():
        redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)
    return redacted


# --- TEST ---
test_inputs = [
    "My account number is 123456789012 and my card is 4111-1111-1111-1111",
    "Transfer ₹50,000 to IFSC SBIN0001234, PAN ABCDE1234F",
    "What are your savings account interest rates?",  # Clean input
]

print("=" * 70)
print("PII DETECTION & REDACTION DEMO")
print("=" * 70)

for inp in test_inputs:
    pii = detect_pii(inp)
    print(f"\n📥 Input   : {inp}")
    print(f"🔍 PII Found: {pii if pii else 'None'}")
    if pii:
        print(f"🛡️ Redacted : {redact_pii(inp)}")
    else:
        print("✅ Input is clean — no PII detected")