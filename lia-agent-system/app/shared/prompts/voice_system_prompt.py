"""Canonical voice system prompt builder.

F-10 + F-11 fix (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):

Voice orchestrator construía system_prompt manualmente em
`generate_lia_response` + `_build_job_presentation_instruction`,
bypassing canonical infra:

- SystemPromptBuilder.build (E2.3 — per-tenant persona override)
- build_company_agent_context (lia_field_toggles canonical filter)
- get_ai_persona (AI Persona per-tenant: name + tone)

Sintoma: cliente customizava nome/tom da LIA em Configurações → afetava
chat (mensagem outbound + chat lateral) mas NÃO afetava voz. Ghost
setting parcial. Os mesmos toggles `lia_field_toggles` (CompanyCultureProfile)
não eram consumidos pelo voice → ghost setting completo em voice.

Fix: este helper é o entry-point canonical para qualquer build de prompt
em voice. Consome os 3 canonicals e injeta voice-specific guidance
(frases curtas, sem markdown — porque LLM output vira TTS).

Failure mode: nenhum dos 3 canonicals deve crashar voz. Se persona
service ou context builder lançar, log + fallback estático preservado.

Refs canonical:
- app/shared/prompts/system_prompt_builder.py (E2.3 SystemPromptBuilder)
- app/shared/services/lia_agent_context_builder.py (lia_field_toggles canonical)
- app/domains/persona/services/ai_persona_service.py:get_ai_persona
- CLAUDE.md: "Per-tenant AI persona canonical pattern (E2, registrado 2026-05-21)"
- CLAUDE.md: "lia_field_toggles canonical pattern"
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.persona.services.ai_persona_service import get_ai_persona
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
from app.shared.services.lia_agent_context_builder import build_company_agent_context

logger = logging.getLogger(__name__)


# Voice-specific guidance appended to every voice system prompt.
# Reason: LIA output in voice path becomes TTS audio. LLM defaults to
# Markdown / bullet lists / long sentences which sound robotic on phone.
# This instruction overrides default register for voice channel.
_VOICE_SPECIFIC_INSTRUCTIONS = """
## INSTRUÇÕES DE VOZ (canal: audio/telefone)

A sua resposta será sintetizada em áudio e tocada para o candidato no
telefone. Por isso:

- Use frases CURTAS (max 25 palavras por frase).
- Sem listas com numeração (1, 2, 3...) ou bullets — vira sopa em áudio.
- Sem markdown (**, *, _, `, #) — TTS lê o caractere literal.
- Tom conversacional natural, como uma recrutadora ao telefone.
- Não cite URLs nem documentos (candidato não pode clicar).
- Faça UMA pergunta por vez — não empilhe múltiplas perguntas na mesma fala.
- Use transições naturais ("Entendi", "Ótimo", "Faz sentido") em vez de
  validações forçadas tipo "Excelente resposta!".
""".strip()


# Fallback persona (used when both AI Persona lookup and SystemPromptBuilder
# fail — degraded but functional voice path).
_FALLBACK_VOICE_PROMPT = (
    "Você é a LIA, recrutadora IA da WeDOTalent em chamada de voz.\n"
    "Use frases curtas, tom natural, uma pergunta por vez.\n"
    "Não use markdown nem listas numeradas — sua resposta virá em áudio."
)


async def build_voice_system_prompt(
    *,
    company_id: str,
    db: AsyncSession,
    job_context: dict[str, Any] | None = None,
) -> str:
    """Canonical voice system prompt — consumes the 3 canonical surfaces.

    Args:
        company_id: tenant UUID (caller MUST validate from JWT, never from LLM).
        db: AsyncSession bound to the tenant.
        job_context: optional {"title", "department", "seniority", ...} used
            by ``build_company_agent_context`` to scope role-specific filter
            in ``lia_field_toggles``. Omit for non-job-specific voice (e.g.,
            offboarding survey, future use cases).

    Returns:
        Full system prompt string ready to feed to Gemini/LLM. Always non-empty
        — degrades to a static fallback if all 3 canonicals raise.

    Never raises. All canonical lookups are wrapped in try/except so a
    transient infra failure (DB hiccup, persona service down) cannot block
    an in-flight voice call.
    """
    # 1) AI Persona per-tenant (E2.3 canonical)
    try:
        persona = await get_ai_persona(company_id, db)
        ai_persona_kwarg: dict[str, str] | None = persona
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[voice_system_prompt] get_ai_persona failed for company_id=%s; "
            "voice will use canonical defaults. Reason: %s",
            company_id,
            exc,
            exc_info=True,
        )
        ai_persona_kwarg = None

    # 2) lia_field_toggles filter (canonical)
    try:
        tenant_context_snippet = await build_company_agent_context(
            company_id=company_id,
            db=db,
            job_context=job_context,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[voice_system_prompt] build_company_agent_context failed for "
            "company_id=%s; voice will run without recruiter-filtered context. "
            "Reason: %s",
            company_id,
            exc,
            exc_info=True,
        )
        tenant_context_snippet = ""

    # 3) Compose via canonical SystemPromptBuilder
    try:
        full_prompt = SystemPromptBuilder.build(
            agent_type="voice_screening",
            tenant_context_snippet=tenant_context_snippet,
            extra_instructions=_VOICE_SPECIFIC_INSTRUCTIONS,
            ai_persona=ai_persona_kwarg,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[voice_system_prompt] SystemPromptBuilder.build failed for "
            "company_id=%s; falling back to static voice prompt. Reason: %s",
            company_id,
            exc,
            exc_info=True,
        )
        return _FALLBACK_VOICE_PROMPT

    return full_prompt


__all__ = ["build_voice_system_prompt"]
