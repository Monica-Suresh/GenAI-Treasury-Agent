# Architecture

## Four Stages

### Stage 1 - LLM Extraction
Input: natural language. Output: PaymentIntentList. Model: Qwen3 0.6B via Ollama.

### Stage 2 - RAG + LLM-as-Judge
Input: extracted intent. Output: safety score 0-10. Advisory only.

### Stage 3 - Deterministic Guardrail
Input: SpendRequest. Output: ALLOW / REQUIRE_APPROVAL / DENY.
No LLM. Pure Python. This is the trust boundary.

### Stage 4 - LLM Synthesis
Input: all prior outputs. Output: natural language summary. No authority.

## Trust Boundary

The LLM can produce any output. The guardrail still enforces policy.
