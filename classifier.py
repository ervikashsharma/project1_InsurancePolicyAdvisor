from llmHelper import askllm
import json

TOPIC_FILTER_PROMPT = """You are a insurance and policy input classifier. Your job is to determine
whether a customer query is within the allowed scope of a insurance and policy assistant.

ALLOWED TOPICS:
- Insurance types (life, health, auto, home, travel, term, group policies)
- Policy details (coverage, benefits, exclusions, riders, maturity, surrender value)
- Premiums (payment options, due dates, grace period, late fees)
- Claims (filing process, required documents, claim status, settlement timelines)
- Renewals and cancellations
- Nominee and beneficiary updates
- Policy loans (eligibility, interest rates, repayment terms)
- KYC and documentation for insurance
- Branch/office locator and customer support
- Grievance/complaint filing related to insurance services
- General regulatory compliance (IRDAI guidelines, solvency norms, etc.)

BLOCKED TOPICS:
- Stock market tips or investment advice on specific securities
- Tax filing advice (beyond basic info on deductions related to insurance premiums)
- Medical diagnosis or treatment advice
- Legal advice outside of insurance contracts
- Political opinions or campaign-related queries
- Cryptocurrency trading or unrelated financial speculation
- Anything unrelated to insurance and policy services

Respond ONLY with a JSON object:
{"allowed": true/false, "category": "<topic>", "reason": "<brief reason>"}
"""

def classify_topic(user_input: str) -> dict:
    
    messages = [
        {"role": "system", "content": TOPIC_FILTER_PROMPT},
        {"role": "user", "content": user_input}
    ]
    result = askllm(messages)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"allowed": False, "category": "parse_error", "reason": "Could not parse classifier output"}


# --- TEST ---
test_queries = [
    "What is the premium amount for my health insurance policy?",
    "Should I buy Tesla stock right now?",
    "How do I apply for a home loan?",
    "What's the best treatment for diabetes?",
    "I want to file a complaint about a failed UPI transaction.",
]

print("=" * 70)
print("TOPIC CLASSIFICATION DEMO")
print("=" * 70)

for q in test_queries:
    result = classify_topic(q)
    status = "✅ ALLOWED" if result.get("allowed") else "🚫 BLOCKED"
    print(f"\n📥 Query   : {q}")
    print(f"   {status} | Category: {result.get('category')} | Reason: {result.get('reason')}")