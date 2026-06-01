"""
LIA Agent Context Builder — canonical entry-point for agents to load the
company context already filtered by ``lia_field_toggles`` and enriched with
``lia_instructions`` (the 34 per-field recruiter instructions edited in
Configurações → Minha Empresa → Instruções LIA por Campo).

Closes P0-1 (audit 2026-05-21):
The ``LiaFieldsConfigPanel`` UI exposed 34 toggles + 34 free-text instruction
strings, all persisted in ``CompanyCultureProfile.lia_field_toggles`` and
``CompanyCultureProfile.lia_instructions``. Zero agents read them. Recruiters
configured what amounted to inert JSON. This module is the single bridge
between that UI surface and every agent prompt assembly.

## Usage contract

Any LLM-facing surface in ``lia-agent-system`` that injects company data into
a system prompt — LIA chat, WSI question generator, recruiter assistant,
talent pool messaging, JD generator, etc. — should call::

    from app.shared.services.lia_agent_context_builder import (
        build_company_agent_context,
    )

    context_prompt = await build_company_agent_context(
        company_id=current_company_id,
        db=db,
        job_context={"title": job.title, "department": job.department},
    )
    system_prompt = f"{base_persona}\\n\\n{context_prompt}\\n\\n{task_instructions}"

The returned string is already:
- Filtered by ``is_active`` toggle per field (off → field not injected, fallback
  values may appear with explicit source attribution).
- Enriched with recruiter ``comment`` per field (those become "_Instrução do
  recrutador: ..._" inline annotations the LLM sees as authoritative).
- Sorted into sections: "Campos Configurados pela Empresa", "Campos com Dados
  Alternativos", "Campos Indisponíveis", "Instruções Específicas do Recrutador".

## What this helper does NOT do

- Caching. The underlying ``LiaFieldConfigService.get_field_config`` does
  one query per call; if a hot path needs caching, layer it above.
- Authentication. Caller MUST have already enforced multi-tenancy (JWT bound
  to the same ``company_id``). The service trusts the company_id argument.
- Fallback to legacy behavior. If the company has no toggles row yet,
  ``LiaFieldConfigService`` applies ``DEFAULT_FIELD_TOGGLES`` automatically.

## Why a separate module instead of putting this in LiaFieldConfigService

LiaFieldConfigService lives under ``app/domains/cv_screening/services/`` —
that namespace implies a CV-screening-specific service. Many of the agents
that need this prompt (LIA chat, JD generator, sourcing) are not in
cv_screening. A neutral shim under ``app/shared/services/`` signals that the
function is cross-domain and avoids tying every caller to the cv_screening
domain.

Audit anchor: see ``Documents/wedotalent_audit_2026-05-21/menu_configuracoes_inteligencia_agentes.md``
sections "P0 #1" + "Camada 1 #34" for the original gap description.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def build_company_agent_context(
    company_id: str,
    db: AsyncSession,
    job_context: dict[str, Any] | None = None,
) -> str:
    """Return a system-prompt fragment with company context filtered by toggles.

    Args:
        company_id: UUID string of the calling tenant. The caller is
            responsible for asserting this matches the authenticated tenant.
        db: Async DB session bound to the caller's tenant.
        job_context: Optional dict with {"title", "department", "seniority"}
            used by fallback strategies (e.g. role inference for missing
            tech_stack). Omit when the agent is not job-specific (e.g. LIA
            chat in settings context, talent pool browsing).

    Returns:
        A markdown-formatted prompt fragment ready to concatenate into a
        system prompt. Empty string if the company has no profile yet —
        callers must tolerate that gracefully (e.g. fall back to a generic
        persona, since the recruiter has not configured anything yet).

    Never raises for missing data — returns empty string on
    ``LiaFieldConfigService`` errors and logs at WARNING level so a single
    misconfigured tenant cannot blow up an agent invocation.
    """
    if not company_id:
        return ""
    try:
        # Local import to avoid widening the import graph for callers that
        # never need the cv_screening module's transitive deps.
        from app.domains.cv_screening.services.lia_field_config_service import (
            LiaFieldConfigService,
        )

        svc = LiaFieldConfigService(db)
        result = await svc.get_field_config(company_id, job_context)
        context = result.context_prompt or ""
        return context
    except Exception as exc:
        # Degraded mode: log + return empty. The agent will run with a
        # generic prompt rather than no prompt at all. ``logger.exception``
        # captures traceback for ops triage without leaking detail upstream.
        logger.warning(
            "[lia_agent_context_builder] Failed to build context for company_id=%s; "
            "agent will run without recruiter-filtered context. Reason: %s",
            company_id, exc,
            exc_info=True,
        )
        return ""


__all__ = ["build_company_agent_context"]
