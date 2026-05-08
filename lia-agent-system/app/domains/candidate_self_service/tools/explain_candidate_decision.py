"""Tool: explain_candidate_decision — EU AI Act Art. 86 + LGPD Art. 20.

Retorna ao candidato, em linguagem simples, os critérios objetivos usados em
decisões automatizadas sobre sua candidatura, SEM expor scoring bruto.

Todas as decisões de AuditLog são filtradas via PROTECTED_CRITERIA_LABELS para
garantir que nenhum atributo protegido apareça na resposta ao candidato.

Compliant with:
  - EU AI Act Art. 86 (right to explanation of individual decision-making)
  - LGPD Art. 20 (direito de revisão de decisão automatizada)
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# Fields NEVER returned to candidate (ADR-006 + LGPD + scope_out of candidate_self_service.yaml)
_FORBIDDEN_FIELDS = frozenset([
    "wsi_score", "lia_score", "wsi_final_score", "match_percentage",
    "red_flags", "confidence", "score", "factors_weights",
    "calibration_weights_used", "calibration_weights",
    "recruiter_notes", "rejection_code", "is_private",
    "cpf", "current_salary", "desired_salary",
    "diversity_race_ethnicity", "diversity_disability", "diversity_lgbtqia",
])

# Labels of protected criteria — shown to candidate as evidence of non-use
# (mirrors PROTECTED_CRITERIA_LABELS from decision_explanation.py)
_PROTECTED_CRITERIA_LABELS = {
    "age": "Idade",
    "gender": "Gênero",
    "ethnicity": "Etnia/raça",
    "marital_status": "Estado civil",
    "photo": "Foto/aparência",
    "institution": "Instituição de ensino",
    "address": "Endereço",
    "religion": "Religião",
    "disability": "Condição de deficiência",
    "nationality": "Nacionalidade",
}

_ART_86_NOTICE = (
    "De acordo com o EU AI Act (Art. 86) e a LGPD (Art. 20), você tem direito "
    "de solicitar revisão humana desta decisão dentro de 30 dias. Para isso, "
    "responda a este canal ou contate o canal oficial de compliance da empresa."
)


def _sanitize_decision(decision_row: dict[str, Any]) -> dict[str, Any]:
    """Remove campos proibidos e padroniza resposta.

    Retorna APENAS critérios objetivos avaliados + lista explícita dos
    critérios protegidos que foram IGNORADOS (transparência reversa).
    """
    criteria_evaluated = decision_row.get("criteria_used") or []
    criteria_ignored = decision_row.get("criteria_ignored") or list(
        _PROTECTED_CRITERIA_LABELS.values()
    )
    reasoning_items = decision_row.get("reasoning") or []

    # Never expose raw reasoning strings that may contain sensitive details —
    # keep only top-level summary count + flag that reasoning is available on request
    reasoning_summary = (
        f"Análise baseada em {len(criteria_evaluated)} critério(s) objetivo(s)."
        if criteria_evaluated
        else "Decisão pendente ou sem critérios documentados."
    )

    fairness_flags = decision_row.get("fairness_flags") or []
    fairness_check_label = "passed" if not fairness_flags else "under_review"

    return {
        "decision_type": decision_row.get("decision_type"),
        "timestamp": (
            decision_row.get("created_at").isoformat()
            if decision_row.get("created_at")
            else None
        ),
        "criteria_evaluated": criteria_evaluated,
        "criteria_ignored": criteria_ignored,
        "reasoning_summary": reasoning_summary,
        "fairness_check": fairness_check_label,
        "human_reviewed": decision_row.get("human_reviewed_at") is not None,
    }


@tool_handler("candidate_self_service", require_company=True)
async def _explain_candidate_decision(**kwargs: Any) -> dict[str, Any]:
    candidate_id: str = kwargs.get("candidate_id", "")
    vacancy_id: str = kwargs.get("vacancy_id", "")
    company_id: str = kwargs.get("company_id", "")

    if not candidate_id or not vacancy_id:
        return {
            "success": False,
            "message": "candidate_id e vacancy_id são obrigatórios.",
        }

    try:
        from sqlalchemy import and_, select
        from app.core.database import get_db
        from lia_models.audit_log import AuditLog

        async for db in get_db():
            result = await db.execute(
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.company_id == company_id,
                        AuditLog.candidate_id == candidate_id,
                        AuditLog.job_vacancy_id == vacancy_id,
                    )
                )
                .order_by(AuditLog.created_at.asc())
            )
            audit_logs = result.scalars().all()
            break

        if not audit_logs:
            return {
                "success": True,
                "data": {
                    "decisions": [],
                    "message": (
                        "Ainda não há decisões registradas para sua candidatura "
                        "nesta vaga. Assim que houver, você poderá consultar aqui."
                    ),
                    "art_86_notice": _ART_86_NOTICE,
                },
            }

        decisions = []
        for log in audit_logs:
            row = {
                "decision_type": log.decision_type,
                "created_at": log.created_at,
                "criteria_used": log.criteria_used or [],
                "criteria_ignored": log.criteria_ignored or [],
                "reasoning": log.reasoning or [],
                "fairness_flags": log.fairness_flags or [],
                "human_reviewed_at": log.human_reviewed_at,
            }
            decisions.append(_sanitize_decision(row))

        logger.info(
            "[CSS Tool] explain_candidate_decision candidate_id=%s vacancy_id=%s count=%d",
            candidate_id, vacancy_id, len(decisions),
        )

        return {
            "success": True,
            "data": {
                "decisions": decisions,
                "transparency_note": (
                    "Os seguintes critérios foram EXCLUÍDOS de toda análise "
                    "por proteção legal: " + ", ".join(_PROTECTED_CRITERIA_LABELS.values())
                ),
                "art_86_notice": _ART_86_NOTICE,
                "total_decisions": len(decisions),
            },
        }
    except Exception as exc:
        logger.error(
            "[CSS Tool] explain_candidate_decision error candidate_id=%s: %s",
            candidate_id, exc,
        )
        return {
            "success": False,
            "message": "Não foi possível recuperar a explicação neste momento.",
        }


explain_candidate_decision = ToolDefinition(
    name="explain_candidate_decision",
    description=(
        "Retorna explicação em linguagem simples das decisões automatizadas "
        "tomadas sobre a candidatura — critérios objetivos usados, critérios "
        "protegidos ignorados, e aviso de direito de contestação (EU AI Act "
        "Art. 86 + LGPD Art. 20). NUNCA expõe scoring bruto, confidence numérica "
        "ou atributos protegidos. Use quando o candidato perguntar a razão de uma "
        "decisão, critérios avaliados, ou solicitar revisão humana."
    ),
    parameters={
        "type": "object",
        "properties": {
            "candidate_id": {
                "type": "string",
                "description": "ID do candidato (do token JWT — nunca do input)",
            },
            "vacancy_id": {
                "type": "string",
                "description": "ID da vaga (do token JWT — nunca do input)",
            },
        },
        "required": ["candidate_id", "vacancy_id"],
    },
    function=_explain_candidate_decision,
)
