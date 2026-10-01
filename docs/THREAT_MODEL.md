# Threat Model

## Adversaries
1. Compromised LLM (prompt injection)
2. Hallucinating LLM
3. Malicious agent framework
4. Insider threat

## Mitigations
- Guardrail never sees raw LLM output
- Structured output parsing rejects malformed intents
- Agent cannot modify policy or budget
- Audit log is hash-chained

## Limitations
1. In-memory state
2. No real payment rails
3. Intent violations may slip through
4. Single-process
5. Tamper-evident, not tamper-proof
