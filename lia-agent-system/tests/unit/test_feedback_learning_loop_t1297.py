"""Sentinela — ciclo de feedback → aprendizagem do chat (Task #1297).

A auditoria detectou que o ciclo estava morto: apesar de 14k+ mensagens,
`learning_patterns` estava vazia. Root causes cobertos aqui:

1. `_update_patterns_from_feedback` tinha early-return `if not feedback.intent`
   — como os polegares do chat não carregam intent, NENHUM padrão era gerado.
   Agora um padrão "general" é criado a partir do sinal real.
2. `get_relevant_patterns` ignorava padrões "general" (matching só por intent),
   então mesmo que existissem nunca eram consumidos. Agora "general" é sempre
   relevante.
3. O consumo de padrões só acontecia no wizard. Agora o helper canônico
   `build_system_prompt_with_persona` injeta o bloco de exemplos aprendidos
   em TODOS os caminhos de chat.

Tudo offline (db/repo mockados) — não toca prod-local, sem row leak.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_pattern_generated_even_without_intent():
    """Polegar sem intent DEVE gerar um padrão 'general' (não early-return)."""
    from app.domains.analytics.services import feedback_service as fs_mod
    from lia_models.feedback import InteractionFeedback

    fb = InteractionFeedback()
    fb.company_id = uuid4()
    fb.intent = None
    fb.stage = None
    fb.thumbs = "up"
    fb.rating = None
    fb.correction = None
    fb.lia_response = "Resposta excelente."
    fb.user_message = "oi"

    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    fake_repo = MagicMock()
    fake_repo.find_active_pattern = AsyncMock(return_value=None)

    with patch.object(fs_mod, "FeedbackRepository", return_value=fake_repo):
        await fs_mod.feedback_service._update_patterns_from_feedback(fb, db)

    db.add.assert_called_once()
    added = db.add.call_args.args[0]
    assert added.pattern_key == "general"
    assert added.positive_feedback_count == 1
    assert added.example_good_responses == ["Resposta excelente."]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_relevant_patterns_always_includes_general():
    """Padrões 'general' são sempre relevantes; intents específicos só com match."""
    from app.domains.analytics.services import feedback_service as fs_mod
    from lia_models.feedback import LearningPattern

    gen = LearningPattern()
    gen.pattern_key = "general"
    gen.pattern_type = "intent"
    gen.trigger_phrases = []

    other = LearningPattern()
    other.pattern_key = "sourcing_basic"
    other.pattern_type = "intent"
    other.trigger_phrases = []

    fake_repo = MagicMock()
    fake_repo.list_active_patterns_min_confidence = AsyncMock(
        return_value=[gen, other]
    )

    db = MagicMock()
    with patch.object(fs_mod, "FeedbackRepository", return_value=fake_repo):
        result = await fs_mod.feedback_service.get_relevant_patterns(
            intent="",
            user_message="qualquer coisa",
            company_id=str(uuid4()),
            db=db,
        )

    keys = [p.pattern_key for p in result]
    assert "general" in keys
    assert "sourcing_basic" not in keys


@pytest.mark.asyncio
async def test_persona_helper_injects_learned_examples():
    """O helper canônico injeta o bloco de exemplos aprendidos no build (chat geral)."""
    from app.shared.prompts import persona_aware_prompt
    from app.domains.analytics.services import feedback_service as fs_mod

    fake_build = MagicMock(return_value="prompt")
    block = "\n## Aprendizado do Feedback do Recrutador\n- exemplo bom"

    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        AsyncMock(return_value=None),
    ), patch.object(
        fs_mod.feedback_service,
        "get_learned_examples_block",
        AsyncMock(return_value=block),
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build
    ):
        await persona_aware_prompt.build_system_prompt_with_persona(
            company_id="00000000-0000-4000-a000-000000000001",
            db=MagicMock(),
            agent_type="orchestrator",
        )

    fake_build.assert_called_once()
    _, kwargs = fake_build.call_args
    assert kwargs["learned_examples"] == block


@pytest.mark.asyncio
async def test_persona_helper_respects_explicit_learned_examples_override():
    """Caller que passa learned_examples vence e NÃO causa kwarg duplicado."""
    from app.shared.prompts import persona_aware_prompt
    from app.domains.analytics.services import feedback_service as fs_mod

    fake_build = MagicMock(return_value="prompt")
    fetch = AsyncMock(return_value="bloco-do-servico")

    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        AsyncMock(return_value=None),
    ), patch.object(
        fs_mod.feedback_service, "get_learned_examples_block", fetch
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build
    ):
        await persona_aware_prompt.build_system_prompt_with_persona(
            company_id="00000000-0000-4000-a000-000000000001",
            db=MagicMock(),
            agent_type="orchestrator",
            learned_examples="override-do-caller",
        )

    fake_build.assert_called_once()
    _, kwargs = fake_build.call_args
    assert kwargs["learned_examples"] == "override-do-caller"
    # Override do caller vence: o serviço NÃO é consultado.
    fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_learned_examples_block_empty_when_no_patterns():
    """Fail-open: sem padrões, o bloco é vazio (não injeta seção ruidosa)."""
    from app.domains.analytics.services import feedback_service as fs_mod

    with patch.object(
        fs_mod.feedback_service,
        "get_pattern_context_for_response",
        AsyncMock(return_value={"has_patterns": False}),
    ):
        block = await fs_mod.feedback_service.get_learned_examples_block(
            intent="", user_message="", company_id=str(uuid4()), db=MagicMock()
        )
    assert block == ""
