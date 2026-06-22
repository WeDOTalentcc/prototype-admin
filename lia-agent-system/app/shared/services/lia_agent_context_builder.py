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


async def build_focused_job_context(
    focused_job_id: str | None,
    company_id: str,
    db: AsyncSession,
) -> str:
    """Build a context block for the focused job to inject into LIA system prompt.

    Multi-tenancy: validates job belongs to company_id before injecting.
    The company_id MUST come from the authenticated JWT context — never from
    the request payload — so the caller is responsible for that contract.

    Returns:
        Markdown prompt fragment with a "## Vaga em foco" section, or empty
        string if the job is not found, company mismatch, or on any error
        (fail-open so a stale focused_job_id never breaks chat).
    """
    if not focused_job_id or not company_id:
        return ""
    try:
        from uuid import UUID

        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCrudRepository,
        )

        repo = JobVacancyCrudRepository(db)
        job = await repo.get_vacancy_by_id_and_company(
            UUID(focused_job_id), company_id
        )
        if not job:
            return ""
        return (
            "\n\n## Vaga em foco\n"
            f'O recrutador está trabalhando na vaga: "{job.title}" (ID: {job.id})\n'
            "Priorize contexto, perguntas e ações relacionadas a essa vaga quando relevante."
        )
    except Exception as exc:
        logger.debug(
            "[lia_agent_context_builder] build_focused_job_context skipped "
            "for focused_job_id=%s company_id=%s: %s",
            focused_job_id,
            company_id,
            exc,
        )
        return ""




async def build_operational_config_context(
    company_id: str,
    db: AsyncSession,
) -> str:
    """Return a prompt fragment with hiring operational config (offer_rules + screening_defaults).

    These are the settings from Configuracoes → Minha Empresa → Contratacao & Triagem.
    Agents use this to respect company-specific rules for offers, salary negotiation,
    screening score thresholds, channels, and scheduling.

    Returns empty string on any error (fail-open, same contract as build_company_agent_context).
    """
    if not company_id:
        return ""
    try:
        from app.domains.hiring_policy.repositories.hiring_policy_repository import (
            HiringPolicyRepository,
        )

        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if not policy:
            return ""

        sections: list[str] = []

        offer_rules = getattr(policy, "offer_rules", None) or {}
        if offer_rules:
            lines = ["## Regras de Contratação da Empresa"]
            if offer_rules.get("allowed_start_day_of_month"):
                lines.append(f"- Dias de início permitidos: {offer_rules['allowed_start_day_of_month']}")
            if offer_rules.get("min_notice_days") is not None:
                lines.append(f"- Aviso prévio mínimo: {offer_rules['min_notice_days']} dias")
            if offer_rules.get("negotiation_enabled") is not None:
                lines.append(f"- Negociação salarial: {'habilitada' if offer_rules['negotiation_enabled'] else 'desabilitada'}")
            if offer_rules.get("salary_flex_pct_max") is not None:
                lines.append(f"- Flexibilidade salarial máxima: {offer_rules['salary_flex_pct_max']}%")
            if offer_rules.get("counter_proposal_max_rounds") is not None:
                lines.append(f"- Máximo de rodadas de contraproposta: {offer_rules['counter_proposal_max_rounds']}")
            if offer_rules.get("negotiation_hitl_threshold_pct") is not None:
                lines.append(f"- Threshold HITL negociação: {offer_rules['negotiation_hitl_threshold_pct']}%")
            if len(lines) > 1:
                sections.append("\n".join(lines))

        screening = getattr(policy, "screening_config_defaults", None) or {}
        if screening:
            lines = ["## Configuração Padrão de Triagem"]
            settings = screening.get("settings", {}) or {}
            if settings.get("min_score") is not None:
                lines.append(f"- Score mínimo WSI: {settings['min_score']}")
            if settings.get("response_timeout_hours") is not None:
                lines.append(f"- Timeout de resposta: {settings['response_timeout_hours']}h")
            if settings.get("auto_approval_limit") is not None:
                lines.append(f"- Limite aprovação automática: {settings['auto_approval_limit']} candidatos")
            channels = screening.get("channels", {}) or {}
            enabled_channels = [k for k, v in channels.items() if isinstance(v, dict) and v.get("enabled")]
            if enabled_channels:
                lines.append(f"- Canais habilitados: {', '.join(enabled_channels)}")
            sched = screening.get("scheduling", {}) or {}
            if sched.get("auto_enabled") is not None:
                lines.append(f"- Agendamento automático: {'sim' if sched['auto_enabled'] else 'não'}")
            if sched.get("min_score_for_auto") is not None:
                lines.append(f"- Score mínimo para auto-agendamento: {sched['min_score_for_auto']}")
            if len(lines) > 1:
                sections.append("\n".join(lines))

        return "\n\n".join(sections)
    except Exception as exc:
        logger.warning(
            "[lia_agent_context_builder] Failed to build operational config for company_id=%s: %s",
            company_id, exc, exc_info=True,
        )
        return ""

__all__ = ["build_company_agent_context", "build_focused_job_context", "build_operational_config_context"]
