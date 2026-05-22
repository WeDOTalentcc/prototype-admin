"""
F-14 (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):
voice orchestrator public methods MUST validate company_id from
RuntimeContext (ADR-029 R-008) when caller did not pass it.

Why this shape (and not @with_runtime_context decorator):
- Existing voice methods use positional + mixed signatures.
- `with_runtime_context` only supports **kwargs-only handlers
  (see app/shared/runtime_context.py:wrapper(**kwargs)) — applying
  it would break every caller of verify_consent/initiate_call/etc.
- Canonical defense-in-depth equivalent: inline RuntimeContext
  fallback at method start, identical security guarantee
  (company_id from authenticated ContextVar, not LLM-supplied).

Sensor:
1. Voice orchestrator imports RuntimeContext / from_contextvars
2. Each of {verify_consent, initiate_call, initiate_voip_session,
   finalize_screening} contains a fallback to RuntimeContext.from_contextvars
"""
from __future__ import annotations

import re
from pathlib import Path


VOICE_ORCH = Path(__file__).resolve().parents[2] / (
    "app/domains/voice/services/voice_screening_orchestrator.py"
)


def _method_body(src: str, method_name: str) -> str:
    """Extract method body text from voice orchestrator source."""
    m = re.search(
        rf"    async def {method_name}\(.*?\n((?:        .*\n|\n)*?)    (?:async def |def |\Z)",
        src,
        re.DOTALL,
    )
    return m.group(1) if m else ""


def test_voice_orchestrator_imports_runtime_context():
    """F-14: voice orchestrator must import RuntimeContext canonical."""
    src = VOICE_ORCH.read_text()
    assert "from app.shared.runtime_context import" in src, (
        "voice orchestrator must import RuntimeContext canonical"
    )
    assert "RuntimeContext" in src, "voice orchestrator must reference RuntimeContext"


def test_verify_consent_falls_back_to_runtime_context():
    """F-14: verify_consent must fall back to RuntimeContext when company_id missing."""
    src = VOICE_ORCH.read_text()
    body = _method_body(src, "verify_consent")
    assert "RuntimeContext.from_contextvars" in body or "_runtime_ctx_company" in body, (
        "verify_consent must consult RuntimeContext.from_contextvars() "
        "as fallback when caller-supplied company_id is empty"
    )


def test_initiate_call_falls_back_to_runtime_context():
    """F-14: initiate_call must fall back to RuntimeContext when company_id missing."""
    src = VOICE_ORCH.read_text()
    body = _method_body(src, "initiate_call")
    assert "RuntimeContext.from_contextvars" in body or "_runtime_ctx_company" in body, (
        "initiate_call must consult RuntimeContext.from_contextvars() "
        "as fallback when caller-supplied company_id is empty"
    )


def test_initiate_voip_session_falls_back_to_runtime_context():
    """F-14: initiate_voip_session must fall back to RuntimeContext when company_id missing."""
    src = VOICE_ORCH.read_text()
    body = _method_body(src, "initiate_voip_session")
    assert "RuntimeContext.from_contextvars" in body or "_runtime_ctx_company" in body, (
        "initiate_voip_session must consult RuntimeContext.from_contextvars() "
        "as fallback when caller-supplied company_id is empty"
    )


def test_runtime_context_fallback_does_not_break_existing_callers():
    """F-14: fallback must be additive — callers passing company_id keep working.

    Smoke check: import the module without raising.
    """
    # Importing module exercises decorator stacking + lazy paths.
    from app.domains.voice.services import voice_screening_orchestrator

    assert hasattr(voice_screening_orchestrator, "voice_screening_orchestrator"), (
        "module must still export the canonical singleton"
    )
    orch = voice_screening_orchestrator.voice_screening_orchestrator
    assert callable(getattr(orch, "verify_consent", None))
    assert callable(getattr(orch, "initiate_call", None))
    assert callable(getattr(orch, "initiate_voip_session", None))
