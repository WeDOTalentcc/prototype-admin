# Langfuse Integration Decision — Item 10.5 (PX08-070)

**Date:** 2026-04-14
**Decision:** NOT IMPLEMENTED — covered by existing LangSmith + AuditCallback

## Why Not Langfuse

The platform already has TWO LLM observability mechanisms:

### 1. LangSmith (Active)
- **Config:** `app/config/langsmith.py`
- **Dependency:** `langsmith>=0.7.25` in requirements.txt
- **What it captures:** Full trace of every LLM call via `LANGCHAIN_TRACING_V2=true`
- **Automatic:** No code changes needed — LangChain/LangGraph traces auto-capture
- **UI:** https://smith.langchain.com for debugging
- **Cost:** Included with LangChain ecosystem

### 2. AuditCallback (Active)
- **Config:** `libs/audit/lia_audit/audit_callback.py`
- **What it captures:** LLM calls (model, tokens, latency, cost), tool calls, state transitions
- **Persistence:** PostgreSQL (audit_execution_metadata) + S3/file (full payload)
- **PII:** Masking applied before storage
- **request_id:** Correlates events across system

## Adding Langfuse Would:
- Duplicate traces already captured by LangSmith
- Add another external dependency (langfuse SDK)
- Require another set of API keys (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
- Not add capabilities beyond what exists

## If Langfuse Is Needed Later:
- Install: `pip install langfuse`
- Add CallbackHandler in `langgraph_react_base.py` alongside AuditCallback
- PII masking already handled by `_sanitize_messages_pii()`
- trace_id propagation already in AuditCallback
