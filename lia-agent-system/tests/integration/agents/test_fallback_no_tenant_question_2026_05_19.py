"""Sentinela offline — `_generate_fallback_reply` NUNCA pode pedir dados do tenant.

Harness sensor (2026-05-19) criado para travar a regressão "B1" documentada em
``docs/architecture/wizard-flow.md`` §9 e ``docs/runbooks/missing_tenant_context.md``.

Sintoma original (reportado por Paulo, 2026-05-19): após 2-3 rodadas no wizard
de criação de vagas, a LIA pedia ao recrutador "id da empresa" e "nome do
consultor". Diagnóstico forense localizou a fonte em
``WizardSessionService._generate_fallback_reply`` — o system prompt do Haiku
de fallback proibia inventar conteúdo da vaga e canned approvals, mas não
proibia perguntar dados do tenant. Quando o estado ficava inconsistente
(``LIA_AGENT_TENANT_STRICT=false`` + ``company_id=""`` fail-OPEN em dev), o
Haiku "preenchia o vazio" pedindo identificação.

Esta sentinela impõe duas invariantes via AST + behavior teste, sem
depender de backend rodando:

1. **AST guard:** o system prompt do fallback DEVE conter a proibição
   explícita de pedir tenant data (lista de chaves: company_id, empresa,
   consultor, gestor, etc.).
2. **Behavior guard:** quando o LLM Haiku é mockado pra produzir uma
   resposta que pede tenant data, a função DEVE rejeitar e cair em
   ``_build_hard_fallback_message``.

Sentinela é fail-CLOSED — qualquer regressão na lista de proibições ou no
guard de pós-processamento quebra este teste.
"""
from __future__ import annotations

import ast
import asyncio
import inspect
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# Lista canônica de termos que NÃO podem aparecer como pergunta do fallback
# (regressão B1 — `wizard_no_tenant_leak.jsonl`).
TENANT_QUESTION_PATTERNS = (
    "company_id",
    "id da empresa",
    "nome da empresa",
    "qual o setor",
    "qual a empresa",
    "qual sua empresa",
    "qual seu plano",
    "nome do consultor",
    "nome do gestor",
    "nome do recrutador",
    "qual o seu nome",
    "informe a empresa",
)


def _service_source() -> str:
    """Read wizard_session_service.py from disk (AST-friendly, no import)."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # tests/integration/agents/ -> repo
    fp = repo_root / "app" / "domains" / "job_creation" / "services" / "wizard_session_service.py"
    assert fp.exists(), f"wizard_session_service.py not found at {fp}"
    return fp.read_text(encoding="utf-8")


def _extract_function_source(src: str, fn_name: str) -> str:
    """Return the source code of a top-level function from the module text."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
            return ast.get_source_segment(src, node) or ""
    raise AssertionError(f"Function {fn_name!r} not found in wizard_session_service.py")


# ────────────────────────────────────────────────────────────────────────
# AST GUARDS (offline — não precisa importar app)
# ────────────────────────────────────────────────────────────────────────

def test_fallback_system_prompt_forbids_tenant_questions():
    """The system prompt MUST explicitly forbid asking for tenant data.

    Regression B1 — wizard_no_tenant_leak.jsonl (Task #1052).
    """
    src = _service_source()
    fn_src = _extract_function_source(src, "_generate_fallback_reply")
    fn_low = fn_src.lower()
    # Cada termo canônico deve estar mencionado na proibição.
    forbidden_present = [p for p in ("company_id", "id da empresa", "nome do consultor",
                                     "nome do gestor", "nome da empresa", "setor")
                         if p in fn_low]
    assert len(forbidden_present) >= 5, (
        f"_generate_fallback_reply system prompt must explicitly forbid tenant-data "
        f"questions. Found only: {forbidden_present}. "
        f"Required: company_id, id da empresa, nome do consultor, nome do gestor, "
        f"nome da empresa, setor. See "
        f"docs/architecture/wizard-flow.md §9 + docs/runbooks/missing_tenant_context.md."
    )


def test_fallback_has_post_llm_tenant_question_guard():
    """After receiving the LLM text, _generate_fallback_reply MUST screen for
    tenant-question anti-patterns and degrade to hard-prefix if found.

    The guard is a defense-in-depth — even if Haiku ignores the system prompt,
    the function must not return tenant-question text to the user.
    """
    src = _service_source()
    fn_src = _extract_function_source(src, "_generate_fallback_reply")
    # Must reference _asks_tenant guard or equivalent rejection of tenant
    # questions in the returned text.
    assert "_asks_tenant" in fn_src or "tenant_question" in fn_src.lower(), (
        "_generate_fallback_reply must include a post-LLM guard that rejects "
        "tenant-data questions (regressão B1 defense-in-depth). Expected "
        "variable name `_asks_tenant` or a `_tenant_question_patterns` tuple."
    )
    assert "company_id" in fn_src, (
        "_generate_fallback_reply guard must include 'company_id' in its "
        "rejection patterns (regressão B1)."
    )


def test_fallback_returns_hard_prefix_when_tenant_question_pattern_found():
    """Behavior guard: if the LLM tries to return tenant-data question text,
    _generate_fallback_reply must reject it and return the hard-prefix message.

    Mocks ChatAnthropic / get_chat_anthropic so the test runs offline.
    """
    # Lazy import — needs the path to be available
    import os
    # Make sure fallback LLM is NOT disabled for this test (it's the flow we test)
    prev = os.environ.pop("LIA_WIZARD_FALLBACK_LLM_DISABLED", None)
    try:
        from app.domains.job_creation.services import wizard_session_service as wss
    except Exception as exc:  # pragma: no cover — import path drift
        pytest.skip(f"Could not import wizard_session_service: {exc}")
    finally:
        if prev is not None:
            os.environ["LIA_WIZARD_FALLBACK_LLM_DISABLED"] = prev

    for pattern in TENANT_QUESTION_PATTERNS[:3]:  # test first 3, all should be rejected
        # Craft a malicious LLM reply that includes the pattern
        evil_reply = f"Para continuar, preciso que você me diga: {pattern}?"
        mock_msg = type("MockMsg", (), {"content": evil_reply})()
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_msg)

        with patch.object(wss, "get_chat_anthropic", return_value=mock_llm):
            result = asyncio.run(wss._generate_fallback_reply(
                stage="intake",
                conversation_tail=[{"role": "user", "content": "olá"}],
                tenant_snippet=None,
            ))
        # Hard prefix message — see _build_hard_fallback_message
        assert "Não consegui interpretar" in result or "tentar novamente" in result, (
            f"_generate_fallback_reply should have rejected tenant-question pattern "
            f"{pattern!r} and returned the hard-prefix message. Got: {result!r}"
        )
