"""Contract sensor — persona wiring nos orquestradores (caminho DEFAULT do chat).

2026-06-02: o fix ghost-setting de 2026-05-24 (8b3ef6f44) cobriu 7 callers REST
mas omitiu os 3 orquestradores que montam o system prompt da conversa principal:
- app/orchestrator/execution/main_orchestrator.py (Phase 1.5 agentic loop)
- app/orchestrator/services/fallback_react_service.py (_invoke_llm)
- app/orchestrator/legacy/orchestrator.py (_handle_directly)

Estes testes pinam que a persona (nome+tom custom por tenant) chega ao
SystemPromptBuilder.build via build_system_prompt_with_persona quando há
company_id no contexto.

Foco no fallback_react (mais isolável): _invoke_llm é chamável diretamente
com um llm_service fake. Assert: build() recebe ai_persona={...} do tenant.

TDD canonical (lia-testing): Red→Green. Antes do fix, fallback_react chamava
SystemPromptBuilder.build direto sem ai_persona → este teste FALHA (Red).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.prompts import persona_aware_prompt


@pytest.mark.asyncio
async def test_fallback_react_applies_tenant_persona():
    """fallback_react._invoke_llm passa ai_persona do tenant ao builder."""
    from app.orchestrator.services.fallback_react_service import (
        FallbackReActService,
    )

    persona = {"name": "Sofia", "tone": "amigavel"}

    # Modelo LLM fake — chain (prompt | llm).ainvoke() retorna AIMessage-like.
    fake_response = MagicMock()
    fake_response.content = "resposta fake"
    fake_response.tool_calls = []
    fake_llm = MagicMock()
    fake_llm.ainvoke = AsyncMock(return_value=fake_response)
    # ChatPromptTemplate.__or__ produz um Runnable; mockamos o operador para
    # devolver nosso fake_llm como chain final.
    fake_llm.__ror__ = lambda self, other: fake_llm  # prompt | llm → fake_llm

    fake_llm_service = MagicMock()
    fake_llm_service.get_audited_model.return_value = fake_llm

    service = FallbackReActService(llm_service=fake_llm_service)

    fake_get_persona = AsyncMock(return_value=persona)
    fake_build = MagicMock(return_value="prompt_with_sofia")

    ctx = {
        "company_id": "co-test",
        "user_name": "Paulo",
        "user_role": "Recrutador",
        "conversation_summary": "",
        "conversation_history": [],
        "context_page": "general",
        "entity_type": None,
    }

    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        fake_get_persona,
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build,
    ):
        await service._invoke_llm(
            intent="general",
            message="olá",
            entities={},
            ctx=ctx,
        )

    fake_get_persona.assert_awaited_once()
    fake_build.assert_called_once()
    _, build_kwargs = fake_build.call_args
    assert build_kwargs["ai_persona"] == persona, (
        "fallback_react deve passar ai_persona do tenant ao builder "
        f"(recebeu: {build_kwargs.get('ai_persona')!r})"
    )
    # Kwargs originais preservados intactos.
    assert build_kwargs["agent_type"] == "orchestrator"
    assert build_kwargs["user_name"] == "Paulo"
    assert build_kwargs["intent"] == "general"


def test_orchestrators_pass_sensor_ast_check():
    """Os 3 orquestradores não chamam SystemPromptBuilder.build sem ai_persona=.

    Espelha o checker AST do sensor canonical para garantir wiring estático
    (defesa-em-profundidade ao teste de comportamento acima).
    """
    import ast
    from pathlib import Path

    root = Path(persona_aware_prompt.__file__).resolve().parents[3]
    targets = [
        "app/orchestrator/execution/main_orchestrator.py",
        "app/orchestrator/services/fallback_react_service.py",
        "app/orchestrator/legacy/orchestrator.py",
    ]
    violations: list[str] = []
    for rel in targets:
        path = root / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_build = (
                isinstance(func, ast.Attribute)
                and func.attr == "build"
                and isinstance(func.value, ast.Name)
                and func.value.id == "SystemPromptBuilder"
            )
            if not is_build:
                continue
            if not any(kw.arg == "ai_persona" for kw in node.keywords):
                violations.append(f"{rel}:{node.lineno}")
    assert not violations, (
        "SystemPromptBuilder.build() sem ai_persona= nos orquestradores: "
        + ", ".join(violations)
    )
