"""TDD — _invoke_llm não deve mascarar o erro real do LLM (REGRA 4).

Bug: a branch langchain (hasattr invoke) tinha `except: pass`, engolindo o erro
real (ex: AuthenticationError 401) e caindo no enganoso "Unknown LLM client
interface". O erro real DEVE propagar para o caller logar a causa.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


class _LangchainLikeThatRaises:
    """Tem .invoke (interface langchain) mas a chamada falha — simula 401."""
    def invoke(self, _messages):
        raise RuntimeError("BOOM_REAL_LLM_ERROR (ex: 401 invalid x-api-key)")


class _UnknownClient:
    """Sem invoke / messages.create / não-callable — interface genuinamente desconhecida."""
    pass


def test_invoke_propagates_real_error_not_masked():
    from app.domains.job_creation.services.intake_extractor import IntakeExtractor
    ex = IntakeExtractor()
    with pytest.raises(Exception) as exc_info:
        ex._invoke_llm(_LangchainLikeThatRaises(), "texto")
    # O erro real deve aparecer, NÃO o "Unknown LLM client interface"
    assert "BOOM_REAL_LLM_ERROR" in str(exc_info.value)
    assert "Unknown LLM client interface" not in str(exc_info.value)


def test_genuinely_unknown_interface_still_raises_unknown():
    from app.domains.job_creation.services.intake_extractor import IntakeExtractor
    ex = IntakeExtractor()
    with pytest.raises(RuntimeError, match="Unknown LLM client interface"):
        ex._invoke_llm(_UnknownClient(), "texto")
