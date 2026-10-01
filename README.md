# GenAI Treasury Agent

An autonomous, LLM-driven treasury agent with deterministic payment guardrails
demonstrating that LLMs should propose payments but never authorize them.

## What This Project Does

- LLM extraction: Qwen3 parses natural language into structured payment intents
- RAG retrieval: policy documents embedded and retrieved per payment
- LLM-as-judge: second LLM pass scores payment safety 0-10
- Deterministic guardrails: pure-Python policy engine makes final decision
- LLM synthesis: model generates a natural language summary
- Tamper-evident audit: every decision is hash-chained

## Core Thesis

Most agentic payment systems put the LLM in the authorization path. This is wrong.
MandateBench (v7) found that LLM-based payment monitors perform below random
chance (AUROC 0.377) when models suppress reasoning.

Correct architecture: LLM proposes, code disposes.

## Architecture

USER -> LLM Extraction -> RAG + LLM Judge -> Deterministic Guardrail -> LLM Synthesis

See docs/ARCHITECTURE.md for details.

## Quick Start (Local)

This project is designed to run entirely on local hardware and does not require API keys.

    git clone https://github.com/Monica-Suresh/Generative-AI-Treasury-Agent.git
    cd Generative-AI-Treasury-Agent
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen3:0.6b
    pip install -r requirements.txt
    streamlit run app.py

## Security and Secrets

- This repo is intentionally configured for local, offline execution.
- Never commit API keys, access tokens, or personal credentials to git.
- Store any future secrets only in local files such as `.env` or `.streamlit/secrets.toml`, and keep them out of version control.

## Testing

    pytest tests/ -v

| Input | Expected |
|-------|----------|
| $25 to api.openai.com | ALLOW |
| $75 to api.openai.com | DENY (cap) |
| $10 to scam-vip.com | DENY (blocked) |
| $15 to unknown.com | DENY (not allowlisted) |
| $35 to anthropic.com | REQUIRE_APPROVAL |

## GenAI Skills Demonstrated

- Prompt engineering
- Structured outputs (PydanticOutputParser)
- Function calling
- RAG
- Embeddings
- Multi-step chains
- LLM-as-judge
- Multi-agent orchestration

## License

MIT
