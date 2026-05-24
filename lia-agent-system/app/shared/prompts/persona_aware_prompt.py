"""Canonical helper: build SystemPromptBuilder output with per-tenant ai_persona injected.

Esta é a ÚNICA forma canonical de construir prompts da LIA em código de produção
que toca dados do tenant. Os callers principais (chat SSE, conversational,
insights, _shared, interview_notes, lia_profile_analysis, candidate_search)
DEVEM usar este helper em vez de chamar SystemPromptBuilder.build() direto.

Documentado em CLAUDE.md (per-tenant AI persona canonical wiring 2026-05-24).

Background: a feature E2 (per-tenant name+tone) foi originalmente wired apenas
em Agent Studio + voice. Auditoria 2026-05-24 detectou 7 callers principais
sem wiring — cliente customizava "LIA → Sofia", salvava (200 OK + audit log),
abria chat lateral e a IA continuava se apresentando como "LIA". Este helper
resolve em 1 site único + sensor barrar regressão futura (canonical-fix:
fix no produtor, não nos 7 consumidores).

Princípios:
- Falha do load_ai_persona NUNCA bloqueia o build (log warning + persona=None).
- Persona None = comportamento default (sem override). 100% backward-compatible.
- company_id obrigatório (ValueError explícito se ausente — multi-tenancy
  fail-closed; sub-task #978 alinhamento).
- DRY: single source of truth para load+pass.
- Anti-silent-fallback (CLAUDE.md REGRA 4): erro de load é LOGADO com exc_info,
  nunca silenciado sem trail.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

logger = logging.getLogger(__name__)


async def build_system_prompt_with_persona(
    *,
    company_id: str,
    db: AsyncSession,
    **builder_kwargs: Any,
) -> str:
    """Canonical: carrega ai_persona do tenant + chama SystemPromptBuilder.build.

    Args:
        company_id: tenant ID resolvido do JWT (NUNCA do body/path do user).
            Multi-tenancy fail-closed: ValueError se vazio.
        db: AsyncSession ativa (geralmente get_tenant_db / get_db / repo.db).
        **builder_kwargs: kwargs encaminhados para SystemPromptBuilder.build
            (agent_type, extra_instructions, tenant_context_snippet, user_name,
            user_role, conversation_history, context_page, etc.).

    Returns:
        System prompt completo já com override de persona aplicado quando
        o tenant customizou nome/tom. Comportamento backward-compatible
        quando persona é default (LIA + profissional).

    Raises:
        ValueError: company_id vazio (fail-closed multi-tenancy).
    """
    if not company_id:
        raise ValueError(
            "company_id obrigatório para build_system_prompt_with_persona "
            "(multi-tenancy fail-closed — vem do JWT, nunca do payload)."
        )

    persona: dict[str, str] | None = None
    try:
        # Lazy import para evitar ciclo persona ↔ shared.prompts
        from app.domains.persona.services.ai_persona_service import get_ai_persona
        persona = await get_ai_persona(company_id=company_id, db=db)
    except Exception as exc:
        # REGRA 4 anti-silent-fallback: logar com exc_info, prosseguir com persona=None.
        # Persona None = nenhum override aplicado = comportamento default da plataforma.
        # Falha aqui NUNCA bloqueia chat/screening/sourcing.
        logger.warning(
            "[persona_aware_prompt] Failed to load ai_persona for company=%s — "
            "proceeding with default LIA persona. err=%s",
            company_id, exc, exc_info=True,
        )
        persona = None

    return SystemPromptBuilder.build(
        ai_persona=persona,
        **builder_kwargs,
    )
