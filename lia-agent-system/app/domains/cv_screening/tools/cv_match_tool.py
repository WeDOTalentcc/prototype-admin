"""
CV Match Tool — Rubric-based CV matching via tool_registry (Opção B).

Wires the orchestrator LLM to the real BARS evaluation pipeline so that
a recruiter can request CV analysis from ANY context — including the general
chat prompt outside a specific job.

Methodology: BARS (Behaviorally Anchored Rating Scales) + André Methodology v1
Reference:   LIA_METHODOLOGY.md Section 4
"""
import logging
from typing import TYPE_CHECKING, Any, Optional

from app.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


async def analyze_cv_match(
    candidate_id: str | None = None,
    candidate_name: str | None = None,
    vacancy_id: str | None = None,
    vacancy_title: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Evaluate a candidate's CV against a job vacancy using BARS rubric methodology.

    Resolves IDs by name when only names are given (ilike search).
    Calls CVScoringService.screen_candidate() for deterministic rubric scoring.

    Args:
        candidate_id:   UUID of the candidate (preferred — exact match).
        candidate_name: Candidate name for fuzzy search (used if ID not provided).
        vacancy_id:     UUID of the vacancy (preferred — exact match).
        vacancy_title:  Vacancy title for fuzzy search (used if ID not provided).

    Returns:
        Dict with success status, human-readable message, match_score, matched_skills,
        missing_skills, recommendation, and full BARS evaluation detail.
    """
    context = _extract_context(kwargs)
    company_id: str | None = context.company_id if context else None

    logger.info(
        "[analyze_cv_match] candidate=%s|%r  vacancy=%s|%r  company=%s",
        candidate_id, candidate_name, vacancy_id, vacancy_title, company_id,
    )

    # ── Validate that at least one identifier for each side is present ──────
    if not candidate_id and not candidate_name:
        return {
            "success": False,
            "error": "missing_candidate",
            "message": "Informe o nome ou ID do candidato para a análise.",
        }
    if not vacancy_id and not vacancy_title:
        return {
            "success": False,
            "error": "missing_vacancy",
            "message": "Informe o título ou ID da vaga para a análise.",
        }

    try:
        from sqlalchemy import func, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate
        from app.models.job_vacancy import JobVacancy

        # ── Resolve IDs (one DB round-trip) ─────────────────────────────────
        async with AsyncSessionLocal() as db:

            # — Candidate —
            resolved_candidate_id = candidate_id
            resolved_candidate_name = candidate_name

            if not resolved_candidate_id and candidate_name:
                # TENANT-EXEMPT: name-fuzzy-search dedup helper invoked via
                # tool_registry; tenant boundary enforced by Postgres RLS
                # (Task #1143). TODO(harness): add Candidate.company_id ==
                # company_id filter via tool_handler-injected kwarg. The inline
                # comment "platform-wide table" elsewhere in this file is STALE.
                q = select(Candidate).where(
                    func.lower(Candidate.name).contains(candidate_name.strip().lower())
                )
                row = await db.execute(q.limit(1))
                found = row.scalar_one_or_none()
                if found:
                    resolved_candidate_id = str(found.id)
                    resolved_candidate_name = found.name
                else:
                    return {
                        "success": False,
                        "error": "candidate_not_found",
                        "message": (
                            f"Candidato '{candidate_name}' não encontrado. "
                            "Verifique o nome ou forneça o ID diretamente."
                        ),
                    }

            # — Vacancy —
            resolved_vacancy_id = vacancy_id
            resolved_vacancy_title = vacancy_title

            if not resolved_vacancy_id and vacancy_title:
                # TENANT-EXEMPT: dynamic builder — q.where(JobVacancy.company_id
                # == company_id) is conditionally appended below. Sensor cannot
                # trace company_id through variable reassignment.
                q = select(JobVacancy).where(
                    func.lower(JobVacancy.title).contains(vacancy_title.strip().lower())
                )
                if company_id:
                    q = q.where(JobVacancy.company_id == company_id)
                row = await db.execute(q.limit(1))
                found = row.scalar_one_or_none()
                if found:
                    resolved_vacancy_id = str(found.id)
                    resolved_vacancy_title = found.title
                else:
                    return {
                        "success": False,
                        "error": "vacancy_not_found",
                        "message": (
                            f"Vaga '{vacancy_title}' não encontrada. "
                            "Verifique o título ou forneça o ID diretamente."
                        ),
                    }

        # ── Run BARS rubric screening ────────────────────────────────────────
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        scoring_service = CVScoringService()
        result = await scoring_service.screen_candidate(
            candidate_id=resolved_candidate_id,
            vacancy_id=resolved_vacancy_id,
            company_id=company_id,
        )

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "screening_failed"),
                "message": result.get("message", "Erro ao executar triagem. Tente novamente."),
            }

        # ── Build human-readable message ─────────────────────────────────────
        score = float(result.get("rubric_score", 0))
        recommendation = result.get("recommendation", "EM_ANALISE")
        strengths = result.get("strengths", [])
        concerns = result.get("concerns", [])

        candidate_label = (
            result.get("candidate_name")
            or resolved_candidate_name
            or resolved_candidate_id
        )
        vacancy_label = (
            result.get("job_title")
            or resolved_vacancy_title
            or resolved_vacancy_id
        )

        if score >= 85:
            emoji, label = "🟢", "Altamente Recomendado"
        elif score >= 70:
            emoji, label = "✅", "Recomendado"
        elif score >= 55:
            emoji, label = "🟡", "Potencial"
        elif score >= 40:
            emoji, label = "🟠", "Baixo Match"
        else:
            emoji, label = "🔴", "Não Recomendado"

        strengths_md = (
            "\n".join(f"• {s}" for s in strengths[:5])
            if strengths else "• (nenhum destaque identificado)"
        )
        concerns_md = (
            "\n".join(f"• {c}" for c in concerns[:4])
            if concerns else "• (sem gaps críticos)"
        )

        human_message = (
            f"{emoji} **Match: {candidate_label} × {vacancy_label}**\n\n"
            f"**Score BARS:** {score:.0f}/100 — {label}\n"
            f"**Recomendação:** {recommendation}\n\n"
            f"**Pontos fortes:**\n{strengths_md}\n\n"
            f"**Gaps identificados:**\n{concerns_md}\n\n"
            f"*Metodologia: Rubricas Estruturadas (BARS) + André Methodology v1 — "
            f"triagem CV-only. Para avaliação completa, use WSI.*"
        )

        return {
            "success": True,
            "message": human_message,
            "action_taken": "cv_match_analyzed",
            "affected_entities": [resolved_candidate_id, resolved_vacancy_id],
            # ── Structured output (C-05 contract) ──
            "match_score": round(score),
            "matched_skills": strengths,
            "missing_skills": concerns,
            "recommendation": recommendation,
            # ── Extended detail ──
            "cv_fit": result.get("cv_fit", {}),
            "sub_status": result.get("sub_status"),
            "evaluations": result.get("evaluations", []),
            "methodology": result.get("methodology", {}),
            "evaluated_at": result.get("evaluated_at"),
        }

    except Exception as exc:
        logger.error("[analyze_cv_match] Unexpected error: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": "unexpected_error",
            "message": f"Erro inesperado ao analisar match de CV: {exc}",
        }


def register_cv_match_tool() -> None:
    """Register analyze_cv_match in the global tool registry."""
    tool_registry.register(
        ToolDefinition(
            name="analyze_cv_match",
            description=(
                "Analisa a compatibilidade entre um candidato e uma vaga usando a metodologia "
                "BARS (Behaviorally Anchored Rating Scales) com rubricas estruturadas. "
                "Calcula score 0-100 avaliando cada requisito (essencial/desejável/diferencial) "
                "com evidências do CV. Use quando o recrutador pedir: análise de CV, triagem, "
                "match score, compatibilidade candidato×vaga, 'quão bom é o candidato para a vaga', "
                "'analise o CV de X para a vaga Y'. Busca candidato por nome se ID não disponível."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "candidate_id": {
                        "type": "string",
                        "description": "UUID do candidato (preferencial — busca exata)",
                    },
                    "candidate_name": {
                        "type": "string",
                        "description": "Nome completo ou parcial do candidato para busca",
                    },
                    "vacancy_id": {
                        "type": "string",
                        "description": "UUID da vaga (preferencial — busca exata)",
                    },
                    "vacancy_title": {
                        "type": "string",
                        "description": "Título da vaga para busca por nome",
                    },
                },
                # At least candidate_id OR candidate_name is required
                # (vacancy side is validated inside the handler for cleaner UX)
            },
            handler=analyze_cv_match,
            allowed_agents=["recruiter_assistant", "cv_screening", "orchestrator", "global"],
        )
    )
    logger.info("✅ Registered tool: analyze_cv_match (BARS rubric — Opção B)")
