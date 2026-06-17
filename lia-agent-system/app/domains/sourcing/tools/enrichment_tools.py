"""
Sourcing Enrichment Tools — D1.

LIA-callable tools that:
  - check which candidate fields are empty (decides whether to offer enrichment)
  - enrich a candidate via the Apify LinkedIn scraper (tracked via D0 gateway)

All tools receive `_context: ToolExecutionContext` for multi-tenant isolation.
Apify calls automatically track consumption via ConsumptionTrackingService
(fix in apify_service.run_apify_actor — D0.1).
"""
from __future__ import annotations

import logging
from types import SimpleNamespace
from app.domains.sourcing.services.consent_cache import has_valid_consent, record_consent
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.tools.registry import ToolDefinition, tool_registry
from app.tools.context_helpers import context_or_raise, require_company_id_from_context, require_company_id_from_obj, normalize_wrapper_kwargs

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    return kwargs.pop("_context", None)


# ───────────────────────────────────────────────────────────────────
# Tool 1 — check_candidate_completeness
# ───────────────────────────────────────────────────────────────────

CANDIDATE_CORE_FIELDS = [
    "name", "email", "phone", "linkedin_url", "location",
    "seniority_level", "years_experience", "skills",
]

async def check_candidate_completeness(
    candidate_id: str,
    **kwargs,
) -> dict[str, Any]:
    """
    Inspect which core fields of a candidate are empty.
    Used by LIA to decide whether to proactively offer enrichment.

    Args:
        candidate_id: UUID of the candidate

    Returns:
        {
            "success": bool,
            "candidate_id": str,
            "missing_fields": [str],
            "completeness_pct": float (0.0-1.0),
            "enrichment_available": bool,
            "recommendation": str,
        }
    """
    company_id = require_company_id_from_context(kwargs, "check_candidate_completeness")

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    try:
        from lia_models.candidate import Candidate
    except ImportError as e:
        return {
            "success": False,
            "error": "model_import_failed",
            "message": f"Cannot import Candidate model: {e}",
        }

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Candidate).where(
                    and_(
                        Candidate.id == UUID(candidate_id),
                        Candidate.company_id == company_id,
                    )
                )
            )
            cand = result.scalar_one_or_none()
            if not cand:
                return {
                    "success": False,
                    "error": "candidate_not_found",
                    "message": f"Candidato {candidate_id} não encontrado nesse tenant.",
                }

            missing: list[str] = []
            for field in CANDIDATE_CORE_FIELDS:
                val = getattr(cand, field, None)
                if val is None or val == "" or (isinstance(val, list) and not val):
                    missing.append(field)

            filled = len(CANDIDATE_CORE_FIELDS) - len(missing)
            pct = round(filled / len(CANDIDATE_CORE_FIELDS), 2)

            linkedin = getattr(cand, "linkedin_url", None)
            enrichment_available = bool(linkedin) and "linkedin.com" in (linkedin or "")

            if pct >= 0.9:
                reco = "Perfil completo — enriquecimento opcional."
            elif enrichment_available and missing:
                reco = (
                    f"Perfil tem {len(missing)} campo(s) vazio(s). "
                    f"LinkedIn disponível: posso enriquecer via enrich_candidate_linkedin."
                )
            elif not linkedin:
                reco = (
                    "Perfil incompleto e sem LinkedIn. "
                    "Peça a URL do LinkedIn ao recrutador para enriquecer."
                )
            else:
                reco = "Perfil completo o suficiente — sem ação necessária."

            return {
                "success": True,
                "candidate_id": candidate_id,
                "candidate_name": getattr(cand, "name", None),
                "missing_fields": missing,
                "filled_fields_count": filled,
                "total_core_fields": len(CANDIDATE_CORE_FIELDS),
                "completeness_pct": pct,
                "enrichment_available": enrichment_available,
                "linkedin_url": linkedin,
                "recommendation": reco,
            }
    except Exception as e:
        logger.error("check_candidate_completeness failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao verificar perfil: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Tool 2 — enrich_candidate_linkedin
# ───────────────────────────────────────────────────────────────────

async def enrich_candidate_linkedin(
    candidate_id: str,
    linkedin_url: str | None = None,
    include_experiences: bool = True,
    include_education: bool = True,
    include_email_discovery: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    Enrich a candidate's profile via the Apify LinkedIn scraper.

    Consumption is tracked automatically via the D0 gateway
    (CandidateEnrichmentService._scrape_linkedin_profile → ConsumptionTrackingService).
    Budget check runs inside the gateway — if tenant is over limit,
    returns error without calling Apify.

    LGPD note: candidates' LinkedIn data is public, but enrichment should
    only happen with an established recruiting relationship. Consent check
    is recorded in the audit trail.

    Args:
        candidate_id: UUID of the candidate to enrich
        linkedin_url: LinkedIn URL (optional; uses candidate's own if not provided)
        include_experiences: import work experience records
        include_education: import education records
        include_email_discovery: attempt email discovery

    Returns:
        {
            "success": bool,
            "fields_updated": [str],
            "experiences_added": int,
            "education_added": int,
            "source": str (actor used),
            "error": str | None,
        }
    """
    context = context_or_raise(kwargs, "enrich_candidate_linkedin")
    company_id = require_company_id_from_obj(context, "enrich_candidate_linkedin")
    user_id = context.user_id

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    # P2#8 LGPD consent check (90-day TTL) before any Apify enrichment
    if candidate_id:
        if not await has_valid_consent(candidate_id=str(candidate_id), company_id=str(company_id)):
            return {
                "success": False,
                "requires_consent": True,
                "message": (
                    "Para enriquecer os dados deste candidato, precisamos do consentimento explícito. "
                    "O recrutador deve confirmar que o candidato autorizou o uso de seus dados públicos "
                    "para esta finalidade (LGPD Art. 7)."
                ),
            }
        await record_consent(
            candidate_id=str(candidate_id),
            company_id=str(company_id),
            user_id=str(user_id or ""),
        )

    try:
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
    except ImportError as e:
        return {
            "success": False,
            "error": "service_unavailable",
            "message": f"CandidateEnrichmentService unavailable: {e}",
        }

    try:
        async with AsyncSessionLocal() as db:
            service = CandidateEnrichmentService()
            result = await service.enrich_candidate(
                db=db,
                candidate_id=UUID(candidate_id),
                linkedin_url=linkedin_url,
                include_experiences=include_experiences,
                include_education=include_education,
                include_email_discovery=include_email_discovery,
                company_id=company_id,
                user_id=user_id,
            )
            return result
    except Exception as e:
        logger.error("enrich_candidate_linkedin failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "enrichment_failed",
            "message": f"Erro ao enriquecer candidato: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Registration
# ───────────────────────────────────────────────────────────────────



async def _wrap_check_candidate_completeness(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await check_candidate_completeness(**normalize_wrapper_kwargs(kwargs))




async def _wrap_enrich_candidate_linkedin(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await enrich_candidate_linkedin(**normalize_wrapper_kwargs(kwargs))


def register_enrichment_tools() -> None:
    tool_registry.register(ToolDefinition(
        name="check_candidate_completeness",
        description=(
            "Inspecionar quais campos do perfil de um candidato estão vazios. "
            "LIA usa isso para decidir se deve oferecer enriquecimento proativo. "
            "Retorna missing_fields, completeness_pct e recommendation sobre próximo passo."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "UUID do candidato",
                }
            },
            "required": ["candidate_id"],
        },
        handler=_wrap_check_candidate_completeness,
        allowed_agents=[
            "sourcing", "recruiter_assistant", "cv_screening", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="enrich_candidate_linkedin",
        description=(
            "Enriquecer o perfil de um candidato via LinkedIn scraper (Apify). "
            "Preenche email, phone, experiences, education, skills e metadados sociais. "
            "Consumo é rastreado automaticamente (gateway D0). "
            "Usar após check_candidate_completeness indicar campos vazios."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "UUID do candidato a enriquecer",
                },
                "linkedin_url": {
                    "type": "string",
                    "description": "URL do LinkedIn (opcional, usa a do candidato se não passada)",
                },
                "include_experiences": {
                    "type": "boolean",
                    "default": True,
                    "description": "Importar experiências profissionais",
                },
                "include_education": {
                    "type": "boolean",
                    "default": True,
                    "description": "Importar formação acadêmica",
                },
                "include_email_discovery": {
                    "type": "boolean",
                    "default": True,
                    "description": "Tentar descobrir email via actor dev_fusion",
                },
            },
            "required": ["candidate_id"],
        },
        handler=_wrap_enrich_candidate_linkedin,
        allowed_agents=[
            "sourcing", "recruiter_assistant", "cv_screening", "orchestrator",
        ],
    ))

    logger.info("✅ Registered 2 enrichment tools (check_candidate_completeness, enrich_candidate_linkedin)")
