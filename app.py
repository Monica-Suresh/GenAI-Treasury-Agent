import os
import json
import uuid
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Literal

import streamlit as st
from pydantic import BaseModel, Field

# --- LangChain imports (Updated for Local) ---
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.vectorstores import InMemoryVectorStore

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="GenAI Treasury Agent (Local)",
    page_icon="💰",
    layout="wide",
)

# ============================================================
# SIDEBAR — Configuration
# ============================================================
with st.sidebar:
    st.header("⚙️ Local Configuration")
    st.success("✅ Running 100% Locally (No API Keys)")
    st.divider()
    st.subheader("Policy")
    st.markdown("""
    - **Max transaction:** $50
    - **Daily budget:** $100
    - **Approval threshold:** $30
    - **Allowlist:** api.openai.com, anthropic.com, aws.amazon.com
    - **Blocked:** scam-vip.com
    """)

# ============================================================
# GUARDRAIL (Pure Python - No LLM)
# ============================================================

class SpendRequest(BaseModel):
    agent_id: str
    recipient: str
    amount: float
    memo: str = ""

class SpendPolicy(BaseModel):
    max_transaction: float = 50.0
    daily_budget: float = 100.0
    approval_threshold: float = 30.0
    allowed_merchants: list = Field(default_factory=lambda: [
        "api.openai.com", "anthropic.com", "aws.amazon.com"
    ])
    blocked_merchants: list = Field(default_factory=lambda: ["scam-vip.com"])

class Guardrail:
    def __init__(self, policy: SpendPolicy):
        self.policy = policy
        self.spend_today = 0.0
        self.audit_log = []
    
    def authorize(self, request: SpendRequest) -> dict:
        audit_id = str(uuid.uuid4())[:8]
        host = request.recipient.split("/")[0]
        
        if request.amount > self.policy.max_transaction:
            return self._log(audit_id, "DENY", "MAX_TRANSACTION_EXCEEDED",
                             f"${request.amount:.2f} exceeds cap ${self.policy.max_transaction:.2f}")
        if host in self.policy.blocked_merchants:
            return self._log(audit_id, "DENY", "MERCHANT_BLOCKED", f"{host} is blocked")
        if self.policy.allowed_merchants and host not in self.policy.allowed_merchants:
            return self._log(audit_id, "DENY", "MERCHANT_NOT_ALLOWLISTED", f"{host} not allowlisted")
        if request.amount > self.policy.daily_budget - self.spend_today:
            return self._log(audit_id, "DENY", "DAILY_BUDGET_EXCEEDED", "Daily budget exhausted")
        if request.amount >= self.policy.approval_threshold:
            return self._log(audit_id, "REQUIRE_APPROVAL", "APPROVAL_THRESHOLD",
                             f"${request.amount:.2f} needs approval")
        
        self.spend_today += request.amount
        return self._log(audit_id, "ALLOW", "ALLOWED", "All checks passed")
    
    def _log(self, audit_id, decision, code, reason):
        entry = {"audit_id": audit_id, "decision": decision,
                 "reason_code": code, "reason": reason,
                 "timestamp": datetime.utcnow().isoformat()}
        self.audit_log.append(entry)
        return entry

# Persist guardrail across reruns
if "guardrail" not in st.session_state:
    st.session_state.guardrail = Guardrail(SpendPolicy())
guardrail = st.session_state.guardrail

# ============================================================
# LOCAL LLM COMPONENTS (Cached)
# ============================================================

@st.cache_resource(show_spinner=False)
def build_local_components():
    """Builds the local LLM chains and RAG store once."""
    
    # 1. Local LLM via Ollama
    llm = ChatOllama(model="qwen3:0.6b", temperature=0)
    
    # 2. Extraction Chain
    class PaymentIntent(BaseModel):
        recipient: str = Field(description="Merchant domain or person name")
        amount: float = Field(description="Dollar amount")
        memo: str = Field(description="Reason for payment")
    
    class PaymentIntentList(BaseModel):
        payments: list[PaymentIntent] = Field(description="List of payments")
    
    extraction_parser = PydanticOutputParser(pydantic_object=PaymentIntentList)
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract ALL payment intents from the user text. "
                   "If none exist, return an empty list.\n{format_instructions}"),
        ("human", "{user_input}")
    ])
    extraction_chain = extraction_prompt | llm | extraction_parser
    
    # 3. Judge Chain
    class JudgeVerdict(BaseModel):
        safety_score: int = Field(description="0-10")
        reasoning: str
        flag: bool = Field(description="True if human should review")
    
    judge_parser = PydanticOutputParser(pydantic_object=JudgeVerdict)
    judge_prompt = ChatPromptTemplate.from_messages([
        ("system", "Score this payment's safety 0-10.\n{format_instructions}"),
        ("human", "Payment: {payment}")
    ])
    judge_chain = judge_prompt | llm | judge_parser
    
    # 4. Local RAG with InMemoryVectorStore
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        policy_docs = [
            "Software subscriptions under $50 are auto-approved if the vendor is allowlisted.",
            "Cloud infrastructure (AWS, GCP, Azure) is always pre-approved.",
            "Payments over $30 require finance team approval.",
            "Any payment to an unknown vendor must go through security review.",
        ]
        vector_store = InMemoryVectorStore.from_texts(policy_docs, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    except Exception as e:
        st.warning(f"RAG init failed: {e}")
        retriever = None
    
    return {
        "llm": llm,
        "extraction_chain": extraction_chain,
        "extraction_parser": extraction_parser,
        "judge_chain": judge_chain,
        "judge_parser": judge_parser,
        "retriever": retriever,
    }

# ============================================================
# MAIN UI
# ============================================================

st.title("💰 GenAI Treasury Agent (Local)")
st.caption("Qwen3 + HuggingFace Embeddings + Deterministic Guardrails (100% Offline)")

user_input = st.text_area(
    "What do you want the agent to do?",
    value="Pay $25 to api.openai.com for API credits. Also reimburse me $15 for conference lunch.",
    height=100,
)

col1, col2 = st.columns([1, 4])
with col1:
    run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True)
with col2:
    if st.button("🔄 Reset Guardrail", use_container_width=True):
        st.session_state.guardrail = Guardrail(SpendPolicy())
        st.rerun()

# ------------------------------------------------------------
# RUN PIPELINE
# ------------------------------------------------------------
if run_button:
    with st.spinner("Loading local LLM components (first run may take 30s)..."):
        components = build_local_components()
    
    if not components:
        st.error("Failed to build local components. Check if Ollama is running.")
        st.stop()
    
    llm = components["llm"]
    extraction_chain = components["extraction_chain"]
    judge_chain = components["judge_chain"]
    retriever = components["retriever"]
    
    # ============ STAGE 1: EXTRACTION ============
    st.header("Stage 1 — LLM Extraction (Qwen3)")
    with st.status("Extracting payment intents...", expanded=True) as status:
        try:
            st.write(f"**Input:** {user_input}")
            result = extraction_chain.invoke({
                "user_input": user_input,
                "format_instructions": components["extraction_parser"].get_format_instructions(),
            })
            intents = [p.model_dump() for p in result.payments]
            st.write(f"**Extracted {len(intents)} intent(s):**")
            st.json(intents)
            status.update(label=f"✅ Extracted {len(intents)} intents", state="complete")
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.exception(e)
            st.stop()
    
    if not intents:
        st.warning("No payment intents found in the input.")
        st.stop()
    
    # ============ STAGE 2: RAG + JUDGE ============
    st.header("Stage 2 — RAG + LLM-as-Judge")
    judgments = []
    for i, intent in enumerate(intents):
        with st.expander(f"Judging: ${intent['amount']} → {intent['recipient']}", expanded=True):
            policy_context = ""
            if retriever:
                docs = retriever.invoke(intent["recipient"] + " " + intent.get("memo", ""))
                policy_context = "\n".join(d.page_content for d in docs)
                st.write("**Retrieved policy:**")
                for d in docs:
                    st.caption(f"• {d.page_content}")
            
            try:
                verdict = judge_chain.invoke({
                    "payment": f"${intent['amount']} to {intent['recipient']}: {intent.get('memo','')}",
                    "format_instructions": components["judge_parser"].get_format_instructions(),
                })
                st.metric("Safety Score", f"{verdict.safety_score}/10")
                st.write(f"**Reasoning:** {verdict.reasoning}")
                if verdict.flag:
                    st.warning("⚠️ LLM flagged for human review")
                judgments.append(verdict.model_dump())
            except Exception as e:
                st.error(f"Judge failed: {e}")
                judgments.append({"safety_score": None, "reasoning": str(e), "flag": True})
    
    # ============ STAGE 3: GUARDRAIL ============
    st.header("Stage 3 — Deterministic Guardrail")
    payment_results = []
    for intent in intents:
        req = SpendRequest(
            agent_id="streamlit_agent",
            recipient=intent["recipient"],
            amount=intent["amount"],
            memo=intent.get("memo", ""),
        )
        result = guardrail.authorize(req)
        payment_results.append({**intent, **result})
        
        decision = result["decision"]
        if decision == "ALLOW":
            st.success(f"✅ ALLOW — ${intent['amount']} to {intent['recipient']} "
                       f"(audit {result['audit_id']})")
        elif decision == "REQUIRE_APPROVAL":
            st.warning(f"⏳ APPROVAL REQUIRED — ${intent['amount']} to {intent['recipient']} "
                       f"(audit {result['audit_id']})")
        else:
            st.error(f"❌ DENY — ${intent['amount']} to {intent['recipient']}: "
                     f"{result['reason']} (audit {result['audit_id']})")
    
    # ============ STAGE 4: SUMMARY ============
    st.header("Stage 4 — LLM Synthesis")
    with st.spinner("Generating summary..."):
        summary_prompt = f"""Summarize this treasury operation in 3-5 sentences.

User request: {user_input}
Extracted intents: {json.dumps(intents, indent=2)}
Judgments: {json.dumps(judgments, indent=2)}
Guardrail results: {json.dumps(payment_results, indent=2)}

Be direct. Note any denials or approvals needed."""
        try:
            summary = llm.invoke([HumanMessage(content=summary_prompt)]).content
            st.info(summary)
        except Exception as e:
            st.error(f"Summary failed: {e}")
    
    # ============ BUDGET DASHBOARD ============
    st.header("Budget Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("Spent Today", f"${guardrail.spend_today:.2f}")
    c2.metric("Remaining", f"${guardrail.policy.daily_budget - guardrail.spend_today:.2f}")
    c3.metric("Audit Entries", len(guardrail.audit_log))

# ------------------------------------------------------------
# ALWAYS SHOW: Audit log
# ------------------------------------------------------------
st.divider()
st.header("📋 Audit Log")
if guardrail.audit_log:
    st.dataframe(
        [
            {
                "Audit ID": e["audit_id"],
                "Decision": e["decision"],
                "Code": e["reason_code"],
                "Reason": e["reason"],
            }
            for e in reversed(guardrail.audit_log)
        ],
        use_container_width=True,
    )
else:
    st.caption("No entries yet. Run the agent to populate the log.")
