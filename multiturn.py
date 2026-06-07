from llmHelper import askllm
from pydantic import BaseModel
from dataclasses import dataclass,field
from typing import List, Dict
import time
import json
import re

KNOWLEDGE_BASE = {

    # ── PRODUCTS ──────────────────────────────────────────────────────────
    "products": {
        "life_insurance": {
            "name": "SecureLife Term Insurance",
            "coverage": "₹50 lakh – ₹5 crore",
            "premium_modes": ["Monthly", "Quarterly", "Annual"],
            "policy_term": "10 – 40 years",
            "features": ["Tax benefit under 80C", "Nominee protection", "Optional riders (critical illness, accidental death)"],
            "claim_settlement_ratio": "97.5% (FY 2025)"
        },
        "health_insurance": {
            "name": "SecureHealth Mediclaim",
            "coverage": "₹3 lakh – ₹25 lakh",
            "network_hospitals": "5,000+ across India",
            "waiting_period": "30 days (general), 2 years (pre-existing)",
            "features": ["Cashless hospitalization", "No-claim bonus up to 50%", "Free annual health check-up"],
            "tax_benefit": "Section 80D — up to ₹25,000 (₹50,000 for senior citizens)"
        },
        "auto_insurance": {
            "name": "SecureAuto Motor Policy",
            "coverage": ["Third-party liability", "Own damage", "Personal accident cover"],
            "premium_factors": ["Car age", "IDV", "Location", "Add-ons"],
            "add_ons": ["Zero depreciation", "Engine protection", "Roadside assistance"],
            "claim_process": "Intimate claim → Surveyor inspection → Repair authorization → Settlement"
        },
        "home_insurance": {
            "name": "SecureHome Property Cover",
            "coverage": "Structure + contents against fire, theft, natural calamities",
            "sum_insured": "₹5 lakh – ₹2 crore",
            "tenure": "1 – 10 years",
            "features": ["Alternate accommodation cover", "Jewelry protection", "Tenant liability"]
        },
        "travel_insurance": {
            "name": "SecureTravel International Plan",
            "coverage": ["Medical emergencies", "Trip cancellation", "Lost baggage", "Passport loss"],
            "regions": ["Worldwide", "Asia-only", "Schengen-compliant"],
            "claim_support": "24x7 global helpline",
            "features": ["Cashless hospitalization abroad", "Emergency evacuation", "Flight delay compensation"]
        }
    },

    # ── POLICIES ──────────────────────────────────────────────────────────
    "policies": {
        "claim_settlement": {
            "intimation_window": "Within 30 days of incident",
            "documents_required": ["Claim form", "Policy copy", "Medical/hospital bills", "Death certificate (for life claims)"],
            "settlement_sla": "30 days post document submission (IRDAI mandate)",
            "escalation": "Grievance redressal → IRDAI IGMS → Insurance Ombudsman"
        },
        "renewal_policy": {
            "grace_period": "30 days post due date",
            "continuity_benefit": "No-claim bonus preserved if renewed within grace",
            "late_fee": "Applicable after grace period",
            "auto_debit": "Available via ECS/UPI mandate"
        },
        "policy_cancellation": {
            "free_look_period": "15 days from policy issuance",
            "refund_basis": "Pro-rata premium refund (if no claim filed)",
            "surrender_value": "Applicable for traditional life policies after 3 years"
        },
        "kyc_norms": {
            "documents": ["Aadhaar", "PAN", "Passport/Voter ID"],
            "video_kyc": "Available for online policy issuance",
            "re_kyc": "Every 10 years or on regulator mandate",
            "irda_ref": "IRDAI KYC Guidelines 2024"
        },
        "grievance_redressal": {
            "level1": "Insurer Grievance Cell — resolve within 15 days",
            "level2": "IRDAI IGMS portal",
            "level3": "Insurance Ombudsman — if unresolved after 30 days",
            "ombudsman_portal": "www.cioins.co.in",
            "irda_ref": "IRDAI Grievance Redressal Guidelines 2023"
        }
    },

    # ── RATES & LIMITS ────────────────────────────────────────────────────
    "rates": {
        "life_insurance_premium": "₹500/month for ₹50 lakh cover (30-year-old, non-smoker)",
        "health_insurance_premium": "₹12,000/year for ₹5 lakh cover (individual, age 35)",
        "auto_insurance_tp_rate": "₹2,094/year for cars <1000cc (IRDAI FY 2025)",
        "claim_settlement_ratio": "Industry average 96.2% (FY 2025)",
        "tax_benefits": {
            "life": "Section 80C — up to ₹1.5 lakh",
            "health": "Section 80D — up to ₹25,000 (₹50,000 for senior citizens)"
        }
    }
}

INTENT_CONTEXT_MAP = {
    "life_insurance_inquiry":    ["products.life_insurance", "rates.life_insurance_premium"],
    "health_insurance_inquiry":  ["products.health_insurance", "rates.health_insurance_premium"],
    "auto_insurance_inquiry":    ["products.auto_insurance", "rates.auto_insurance_tp_rate"],
    "home_insurance_inquiry":    ["products.home_insurance"],
    "travel_insurance_inquiry":  ["products.travel_insurance"],
    "claim_query":               ["policies.claim_settlement"],
    "renewal_query":             ["policies.renewal_policy"],
    "cancellation_query":        ["policies.policy_cancellation"],
    "kyc_query":                 ["policies.kyc_norms"],
    "grievance_escalation":      ["policies.grievance_redressal"],
    "general_insurance":         ["rates", "policies.grievance_redressal"],
    "investment_redirect":       [],  # Out of scope — redirect
    "banking_redirect":          [],  # Out of scope — redirect
}

def parse_json(raw: str) -> dict:
    """Safely parse JSON from LLM output."""
    clean = re.sub(r"```json|```", "", raw).strip()
    return json.loads(clean)

def divider(title: str = "", char: str = "─", width: int = 65):
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{char*pad} {title} {char*pad}")
    else:
        print(char * width)

def retrieve_context(intent_type: str, entities: dict) -> dict:
    context_keys = INTENT_CONTEXT_MAP.get(intent_type, ["rates"])
    context_package = {"intent": intent_type, "entities": entities, "retrieved": {}}

    for key_path in context_keys:
        parts = key_path.split(".")
        data = KNOWLEDGE_BASE
        for part in parts:
            data = data.get(part, {})
        context_package["retrieved"][key_path] = data

    return context_package

@dataclass
class ConversationMemory:
    
    session_id    : str = field(default_factory=lambda: f"SESSION-{int(time.time())}")
    history       : List[Dict] = field(default_factory=list)   # Full chat history
    intent_log    : List[Dict] = field(default_factory=list)   # Per-turn intent
    context_log   : List[Dict] = field(default_factory=list)   # Per-turn context
    turn_count    : int = 0

    def add_user(self, message: str):
        self.history.append({"role": "user", "content": message})
        self.turn_count += 1

    def add_assistant(self, message: str):
        self.history.append({"role": "assistant", "content": message})

    def get_history_text(self) -> str:
        """Return conversation history as readable text for context injection."""
        if len(self.history) <= 1:
            return "No prior conversation."
        lines = []
        for msg in self.history[:-1]:  # exclude current message
            role = "Customer" if msg["role"] == "user" else "FinAdvisor"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
#  STEP 1 — INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────

STEP1_SYSTEM = """You are a insurance and policy intent classifier in India.

Analyse the customer's latest message (and conversation history) and return ONLY JSON:
{
  "intent_type": "<one of the valid intents below>",
  "confidence": "High" | "Medium" | "Low",
  "entities": {
    "amount": "<if mentioned, e.g. ₹5,00,000 or null>",
    "product": "<specific product mentioned or null>",
    "timeframe": "<tenure/duration if mentioned or null>",
    "utr_number": "<UTR if mentioned or null>",
    "urgency_amount": "<amount at risk in fraud/complaint or null>"
  },
  "urgency": "Critical" | "High" | "Medium" | "Low",
  "sentiment": "Distressed" | "Angry" | "Neutral" | "Positive",
  "is_follow_up": true | false,
  "follow_up_refers_to": "<what prior topic this follows up on, or null>",
  "language": "English" | "Hindi" | "Mixed"
}

VALID INTENT TYPES:
savings_account_inquiry | fixed_deposit_inquiry | home_loan_inquiry |
personal_loan_inquiry | credit_card_inquiry | car_loan_inquiry |
education_loan_inquiry | upi_complaint | fraud_report | kyc_query |
loan_closure_query | grievance_escalation | nri_banking | general_banking |
investment_redirect | insurance_redirect

Return ONLY the JSON. No extra text."""


def step1_classify_intent(memory: ConversationMemory) -> dict:
    """Step 1: Classify user intent with multi-turn awareness."""
    user_prompt = f"""
Conversation history:
{memory.get_history_text()}

Latest customer message:
"{memory.history[-1]['content']}"

Classify the intent of the latest message.
"""
    raw = askllm(
        [{"role": "system", "content": STEP1_SYSTEM},
         {"role": "user",   "content": user_prompt}]
    )
    result = parse_json(raw)
    memory.intent_log.append({"turn": memory.turn_count, **result})
    return result


# ─────────────────────────────────────────────────────────────────────────
#  STEP 2 — CONTEXT RETRIEVER
# ─────────────────────────────────────────────────────────────────────────

STEP2_SYSTEM = """You are a banking knowledge curator for SecureBank India.

Given the classified intent and raw retrieved knowledge base data,
curate and structure ONLY the most relevant context needed to answer the customer.

Return ONLY JSON:
{
  "relevant_facts": ["<key fact 1>", "<key fact 2>", ...],
  "applicable_rates": {"<label>": "<rate>"},
  "applicable_policies": ["<policy rule 1>", "<policy rule 2>", ...],
  "regulatory_references": ["<RBI circular or guideline if relevant>"],
  "risk_flags": ["<any risk flag for this query, e.g. high urgency, fraud risk>"],
  "recommended_products": ["<product name if applicable>"],
  "escalation_needed": true | false,
  "escalation_reason": "<reason if escalation_needed is true, else null>"
}

Return ONLY the JSON. No extra text."""


def step2_retrieve_context(intent_result: dict, memory: ConversationMemory) -> dict:
    """Step 2: Retrieve and curate context from knowledge base."""
    # Fetch raw data from knowledge base
    raw_context = retrieve_context(
        intent_result.get("intent_type", "general_banking"),
        intent_result.get("entities", {})
    )

    # Ask LLM to curate the most relevant pieces
    user_prompt = f"""
Customer intent: {intent_result.get('intent_type')}
Entities: {json.dumps(intent_result.get('entities', {}))}
Urgency: {intent_result.get('urgency')}
Is follow-up: {intent_result.get('is_follow_up')}

Prior conversation context:
{memory.get_history_text()}

Raw knowledge base data retrieved:
{json.dumps(raw_context['retrieved'], indent=2)}

Curate only the facts, rates, and policies relevant to answering this customer query.
"""
    raw = askllm(
        [{"role": "system", "content": STEP2_SYSTEM},
         {"role": "user",   "content": user_prompt}],
    )
    result = parse_json(raw)
    memory.context_log.append({"turn": memory.turn_count, **result})
    return result


# ─────────────────────────────────────────────────────────────────────────
#  STEP 3 — RESPONSE GENERATOR
# ─────────────────────────────────────────────────────────────────────────

STEP3_SYSTEM = """You are PolicyAdvisor — SecureInsure India's senior AI insurance advisor.

IDENTITY & PERSONA:
  You are warm, knowledgeable, and professional.
  You address customers as Sir/Ma'am.
  You speak in plain English (or Hindi/English mix if customer uses Hindi).
  You have 15+ years of insurance and policy expertise.

STRICT RULES:
  1. Use ONLY information from the provided context — never hallucinate premiums, coverage, or policy rules.
  2. If the query is about banking or investments: redirect to the banking/investment desk.
  3. If escalation_needed is true: immediately offer to connect to a human agent.
  4. Maintain conversational continuity — acknowledge what was discussed previously.
  5. Never confirm policy numbers, claim IDs, or sensitive identifiers in full.
  6. Keep responses concise: 100-180 words max.
  7. Always close with one clarifying question OR next step — keep conversation flowing.

RESPONSE QUALITY:
  - Lead with acknowledgement of customer's situation.
  - State the key facts/premiums/policy rules from context.
  - Provide a clear recommended action.
  - End with an engaging follow-up question or offer."""


def step3_generate_response(
    intent_result: dict,
    context_result: dict,
    memory: ConversationMemory
) -> str:
    """Step 3: Generate final grounded customer response."""

    # Build full conversation history for context
    messages = [{"role": "system", "content": STEP3_SYSTEM}]

    # Add conversation history (multi-turn continuity)
    for msg in memory.history[:-1]:  # all but current
        messages.append(msg)

    # Add context-enriched user message
    enriched_prompt = f"""
Customer's message: "{memory.history[-1]['content']}"

[INTERNAL CONTEXT — use this to ground your response]
Intent     : {intent_result.get('intent_type')}
Urgency    : {intent_result.get('urgency')}
Sentiment  : {intent_result.get('sentiment')}
Is follow-up: {intent_result.get('is_follow_up')}
Follow-up refers to: {intent_result.get('follow_up_refers_to')}

Relevant facts:
{json.dumps(context_result.get('relevant_facts', []), indent=2)}

Applicable rates:
{json.dumps(context_result.get('applicable_rates', {}), indent=2)}

Applicable policies:
{json.dumps(context_result.get('applicable_policies', []), indent=2)}

Regulatory references:
{json.dumps(context_result.get('regulatory_references', []), indent=2)}

Risk flags: {context_result.get('risk_flags', [])}
Escalation needed: {context_result.get('escalation_needed', False)}
Escalation reason: {context_result.get('escalation_reason')}
[END INTERNAL CONTEXT]

Respond to the customer using only the context above.
"""
    messages.append({"role": "user", "content": enriched_prompt})

    response = askllm(messages)
    memory.add_assistant(response)
    return response


# ─────────────────────────────────────────────────────────────────────────
#  MASTER CHAIN RUNNER
# ─────────────────────────────────────────────────────────────────────────

def run_chain(
    user_message: str,
    memory: ConversationMemory,
    verbose: bool = True
) -> str:
    """
    Run the full 3-step prompt chain for one turn.
    Returns the advisor's response.
    """
    # Add message to memory
    memory.add_user(user_message)

    if verbose:
        divider(f"Turn {memory.turn_count}")
        print(f"👤 Customer: {user_message}\n")

    # ── STEP 1: Classify Intent ────────────────────────────────
    intent = step1_classify_intent(memory)
    if verbose:
        print(f"🔍 STEP 1 — Intent: {intent.get('intent_type')} "
              f"[{intent.get('confidence')}] | "
              f"Urgency: {intent.get('urgency')} | "
              f"Sentiment: {intent.get('sentiment')} | "
              f"Follow-up: {intent.get('is_follow_up')}")
        if intent.get('entities'):
            ents = {k: v for k, v in intent['entities'].items() if v}
            if ents:
                print(f"   Entities: {ents}")

    # ── STEP 2: Retrieve Context ───────────────────────────────
    context = step2_retrieve_context(intent, memory)
    if verbose:
        facts_count = len(context.get('relevant_facts', []))
        escalate = context.get('escalation_needed', False)
        print(f"📚 STEP 2 — Context: {facts_count} facts retrieved | "
              f"Escalation: {escalate}")
        if escalate:
            print(f"   ⚠️  Escalation reason: {context.get('escalation_reason')}")

    # ── STEP 3: Generate Response ──────────────────────────────
    response = step3_generate_response(intent, context, memory)
    if verbose:
        print(f"\n🤖 FinAdvisor: {response}")

    return response


print("✅ 3-step chain fully defined.")
print("   Chain: Intent Classifier → Context Retriever → Response Generator")


mem1 = ConversationMemory()
run_chain("What FD rates do you offer for 2 years? I am a senior citizen.", mem1);