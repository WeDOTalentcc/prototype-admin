"""
AI Transparency API — T-18 EU AI Act Annex III canonical (Wave 1 Agent #1).

Endpoints canonical para suportar transparência obrigatória do EU AI Act
(Annex III high-risk AI systems — recrutamento item 4):

- GET  /api/v1/ai-transparency/explainability-statement
    Art. 13 EU AI Act — instruções de uso + transparência ao deployer.
- GET  /api/v1/ai-transparency/automated-decisions
    Art. 22 LGPD + Art. 13 EU AI Act — lista decisões automatizadas com
    explicação (AutomatedDecisionExplanation canonical, T-20).
- POST /api/v1/ai-transparency/human-oversight/{decision_id}/override
    Art. 14 EU AI Act — recrutador exerce supervisão humana sobre decisão IA.
- GET  /api/v1/ai-transparency/technical-documentation
    Annex III §1 + Art. 11 — ModelCard + intended use + limitations + fairness.

Compliance:
  - EU AI Act 2024/1689 (Art. 13, 14, 22 — high-risk AI obligations).
  - LGPD Lei 13.709/2018 Art. 20 (direito a revisão de decisão automatizada).
  - ADR-035 (audit demographic markers).
  - ADR-AI-TRANSPARENCY-001 (canonical structure novo).

Multi-tenancy: canonical via `Depends(require_company_id)` + JWT.
Audit log: cada operação gera entrada com `demographic_proxies={}` explicit.
"""
from __future__ import annotations
import os

import logging
from datetime import datetime, UTC
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import ConfigDict, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-transparency", tags=["ai-transparency"])


# ────────────────────────────────────────────────────────────────────────────
# Canonical constants — EU AI Act Annex III recruitment + ModelCard
# ────────────────────────────────────────────────────────────────────────────

EXPLAINABILITY_STATEMENT_VERSION = "1.0.0-2026-05-21"
TECHNICAL_DOCUMENTATION_VERSION = "1.0.0-2026-05-21"

# Annex III item 4 — Employment / workers management / access to self-employment
ANNEX_III_CATEGORY = "annex_iii_item_4_employment"

# Protected criteria canonical (mirror of decision_explanation.py + LGPD Art. 11)
PROTECTED_CRITERIA_PT = [
    "Idade",
    "Gênero",
    "Etnia/raça",
    "Estado civil",
    "Foto/aparência",
    "Instituição de ensino",
    "Endereço",
    "Religião",
    "Condição de deficiência",
    "Nacionalidade",
    "Orientação sexual",
    "Status parental/gravidez",
]


# ────────────────────────────────────────────────────────────────────────────
# Response schemas (canonical — WeDoBaseModel extra='forbid' enforced)
# ────────────────────────────────────────────────────────────────────────────


class ExplainabilityStatementSection(WeDoBaseModel):
    """Single section of the AI Explainability Statement (Art. 13)."""

    title: str = Field(..., description="Section heading (PT-BR)")
    content: str = Field(..., description="Plain-language explanation")
    examples: list[str] = Field(default_factory=list, description="Concrete examples")


class ExplainabilityStatementResponse(WeDoBaseModel):
    """AI Explainability Statement — EU AI Act Art. 13 deployer transparency."""

    sections: list[ExplainabilityStatementSection]
    last_updated: datetime
    version: str
    lawful_basis: list[str] = Field(
        ...,
        description="Lawful bases for processing (LGPD Art. 7 + GDPR Art. 6 mapping)",
    )
    annex_iii_category: str = Field(default=ANNEX_III_CATEGORY)
    company_id: str


class AutomatedDecisionItem(WeDoBaseModel):
    """Single automated decision (canonical projection of AutomatedDecisionExplanation)."""

    decision_id: str
    decision_type: str
    candidate_id: str | None = None
    vacancy_id: str | None = None
    ai_model_used: str | None = None
    explanation_text: str | None = None
    explanation_requested_at: datetime | None = None
    explanation_provided_at: datetime | None = None
    human_review_requested: bool = False
    human_review_completed_at: datetime | None = None
    human_review_decision: str | None = None
    created_at: datetime | None = None


class AutomatedDecisionsListResponse(WeDoBaseModel):
    """Paginated list of automated decisions (canonical T-18)."""

    decisions: list[AutomatedDecisionItem]
    total: int
    limit: int
    offset: int
    schema_version: str = Field(default="1.0.0-2026-05-21")


class HumanOversightOverrideRequest(WeDoBaseModel):
    """Recruiter override of an AI decision (Art. 14 EU AI Act + Art. 20 LGPD)."""

    override_reason: str = Field(..., min_length=10, max_length=2000)
    new_decision: str = Field(..., min_length=1, max_length=255)
    reviewer_user_id: str | None = Field(None, description="Derived from JWT when omitted")


class HumanOversightOverrideResponse(WeDoBaseModel):
    """Result of human-oversight override."""

    success: bool
    decision_id: str
    audit_entry_id: str | None
    reviewed_at: datetime
    new_decision: str


class ModelCardSection(WeDoBaseModel):
    """Single section of the canonical ModelCard (Annex III §1)."""

    name: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class TechnicalDocumentationResponse(WeDoBaseModel):
    """Annex III §1 + Art. 11 EU AI Act — technical documentation deployer-facing."""

    model_card: list[ModelCardSection]
    training_data_summary: dict[str, Any]
    intended_use: list[str]
    limitations: list[str]
    fairness_results: dict[str, Any]
    last_updated: datetime
    version: str
    annex_iii_category: str = Field(default=ANNEX_III_CATEGORY)


# ────────────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────────────


@router.get(
    "/explainability-statement",
    response_model=ExplainabilityStatementResponse,
    summary="AI Explainability Statement (EU AI Act Art. 13)",
)
async def get_explainability_statement(
    company_id: str = Depends(require_company_id),
) -> ExplainabilityStatementResponse:
    """
    Retorna AI Explainability Statement estruturado por seção.

    Compliance: EU AI Act Art. 13 (deployer transparency obligation —
    deadline aplicável 2 Ago 2026 para high-risk AI Annex III).

    Multi-tenancy: company_id sempre via JWT (`require_company_id`).
    Audit: AUDIT-NO-DEMO — endpoint read-only public-facing transparency,
    sem decisão automatizada nem demographic processing.
    """
    # AUDIT-NO-DEMO: leitura pública de canonical statement, sem decisão IA
    sections = [
        ExplainabilityStatementSection(
            title="O que esta IA faz",
            content=(
                "A LIA é um sistema de IA de recrutamento que atua como assistente "
                "do recrutador humano: triagem de currículos, ordenação de candidatos "
                "por aderência objetiva à vaga, geração de perguntas WSI (Working "
                "Sample Interview) e suporte conversacional. Decisões finais de "
                "contratação SEMPRE cabem ao recrutador humano (Art. 14 EU AI Act)."
            ),
            examples=[
                "Triagem inicial: classifica candidatos como 'aderente / a considerar / fora do perfil' baseado em critérios objetivos da vaga.",
                "Ordenação: ranking ordenado por score multicritério com fairness check obrigatório.",
                "Perguntas WSI: gera perguntas comportamentais customizadas à vaga.",
            ],
        ),
        ExplainabilityStatementSection(
            title="Critérios que a IA considera",
            content=(
                "Apenas critérios profissionais e objetivos: experiência relevante, "
                "skills declaradas, formação técnica, disponibilidade, pretensão "
                "salarial. Critérios pesados são calibrados pelo recrutador no "
                "Hiring Policy da vaga."
            ),
            examples=[
                "Pesos default: técnico 70% + comportamental 30%.",
                "Calibração ativa: recrutador ajusta pesos por vaga.",
            ],
        ),
        ExplainabilityStatementSection(
            title="Critérios que a IA NÃO considera (PROTEGIDOS)",
            content=(
                "A IA é programaticamente bloqueada de processar atributos protegidos "
                "via FairnessGuard. Tentativa de uso desses critérios em prompts "
                "gera bloqueio + alerta de compliance."
            ),
            examples=PROTECTED_CRITERIA_PT,
        ),
        ExplainabilityStatementSection(
            title="Como contestar uma decisão",
            content=(
                "Você tem direito a (1) explicação detalhada da decisão automatizada "
                "(LGPD Art. 20 + EU AI Act Art. 86), (2) revisão humana via canal "
                "oficial de compliance, e (3) correção/exclusão dos seus dados (LGPD "
                "Art. 18). Prazo legal: 30 dias para revisão."
            ),
            examples=[
                "Endpoint candidato: GET /api/v1/candidate/decisions/explain",
                "Endpoint recrutador: GET /api/v1/decisions/candidates/{id}/explain",
            ],
        ),
        ExplainabilityStatementSection(
            title="Supervisão humana (Art. 14)",
            content=(
                "Toda decisão classificada como 'high-impact' (rejeição, shortlist, "
                "ranking) requer ou comporta revisão humana. Recrutadores podem "
                "override qualquer decisão via endpoint canonical /human-oversight."
            ),
            examples=[
                "POST /api/v1/ai-transparency/human-oversight/{decision_id}/override",
            ],
        ),
    ]

    return ExplainabilityStatementResponse(
        sections=sections,
        last_updated=datetime.now(UTC),
        version=EXPLAINABILITY_STATEMENT_VERSION,
        lawful_basis=[
            "LGPD Art. 7(V) — execução de contrato (avaliação pré-contratual de candidato)",
            "LGPD Art. 7(IX) — interesse legítimo do controlador (recrutamento)",
            "GDPR Art. 6(1)(b) — pre-contractual measures",
            "GDPR Art. 6(1)(f) — legitimate interest with safeguards",
        ],
        company_id=company_id,
    )


@router.get(
    "/automated-decisions",
    response_model=AutomatedDecisionsListResponse,
    summary="List automated decisions (Art. 22 LGPD + Art. 13 EU AI Act)",
)
async def list_automated_decisions(
    candidate_id: str | None = Query(None, description="Filter by candidate UUID"),
    decision_type: str | None = Query(None, description="Filter by decision type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
) -> AutomatedDecisionsListResponse:
    """
    Lista decisões automatizadas com explicação canonical (T-20).

    Reads from `AutomatedDecisionExplanation` (libs/models/lia_models/observability.py).
    Multi-tenancy: filtered by `company_id` from JWT.
    Audit: AUDIT-NO-DEMO — read-only listing, no fresh decision rendered here.
    """
    # AUDIT-NO-DEMO: leitura de explicações já persistidas, sem novo cálculo IA
    from lia_models.observability import AutomatedDecisionExplanation
    from uuid import UUID as _UUID

    try:
        company_uuid = _UUID(company_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"company_id inválido: {exc}",
        ) from exc

    conditions = [AutomatedDecisionExplanation.company_id == company_uuid]

    if candidate_id:
        try:
            conditions.append(
                AutomatedDecisionExplanation.candidate_id == _UUID(candidate_id)
            )
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"candidate_id inválido: {exc}",
            ) from exc

    if decision_type:
        conditions.append(
            AutomatedDecisionExplanation.decision_type == decision_type
        )

    # Total count
    from sqlalchemy import func as _func

    # TENANT-EXEMPT: dynamic builder — conditions[0] is always
    # AutomatedDecisionExplanation.company_id == company_uuid (composed
    # above at the start of the handler).
    count_result = await db.execute(
        select(_func.count(AutomatedDecisionExplanation.id)).where(and_(*conditions))
    )
    total = int(count_result.scalar() or 0)

    # Page
    # TENANT-EXEMPT: dynamic builder — same as count_result above.
    list_result = await db.execute(
        select(AutomatedDecisionExplanation)
        .where(and_(*conditions))
        .order_by(desc(AutomatedDecisionExplanation.created_at))
        .limit(limit)
        .offset(offset)
    )
    rows = list_result.scalars().all()

    decisions = [
        AutomatedDecisionItem(
            decision_id=str(r.id),
            decision_type=r.decision_type,
            candidate_id=str(r.candidate_id) if r.candidate_id else None,
            vacancy_id=str(r.vacancy_id) if r.vacancy_id else None,
            ai_model_used=r.ai_model_used,
            explanation_text=r.explanation_text,
            explanation_requested_at=r.explanation_requested_at,
            explanation_provided_at=r.explanation_provided_at,
            human_review_requested=bool(r.human_review_requested),
            human_review_completed_at=r.human_review_completed_at,
            human_review_decision=r.human_review_decision,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return AutomatedDecisionsListResponse(
        decisions=decisions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/human-oversight/{decision_id}/override",
    response_model=HumanOversightOverrideResponse,
    summary="Human oversight override (EU AI Act Art. 14)",
)
async def override_automated_decision(
    decision_id: Annotated[
        str,
        Path(..., pattern=r"^[0-9a-fA-F-]{36}$", description="Decision UUID"),
    ],
    payload: HumanOversightOverrideRequest,
    company_id: str = Depends(get_verified_company_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
) -> HumanOversightOverrideResponse:
    """
    Recrutador override de decisão automatizada (Art. 14 EU AI Act).

    Persiste override em `AutomatedDecisionExplanation.human_review_*` + dispara
    audit entry canonical via `audit_service.log_decision` (T-20).
    """
    from lia_models.observability import AutomatedDecisionExplanation
    from app.shared.compliance.audit_service import audit_service
    from uuid import UUID as _UUID

    try:
        decision_uuid = _UUID(decision_id)
        company_uuid = _UUID(company_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID inválido: {exc}",
        ) from exc

    # Carrega decisão + multi-tenancy fail-closed
    result = await db.execute(
        select(AutomatedDecisionExplanation).where(
            and_(
                AutomatedDecisionExplanation.id == decision_uuid,
                AutomatedDecisionExplanation.company_id == company_uuid,
            )
        )
    )
    decision = result.scalar_one_or_none()

    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decisão não encontrada ou fora do tenant.",
        )

    now = datetime.now(UTC)
    decision.human_review_requested = True
    decision.human_review_completed_at = now
    decision.human_review_decision = payload.new_decision
    effective_reviewer_id = payload.reviewer_user_id or str(current_user.id)
    try:
        decision.human_reviewer_id = _UUID(effective_reviewer_id)
    except (ValueError, TypeError):
        # reviewer_user_id pode ser string não-UUID em workspaces legados
        decision.human_reviewer_id = None

    await db.commit()
    await db.refresh(decision)

    # Audit canonical entry (T-20) — fairness/demographic markers
    audit_entry_id: str | None = None
    try:
        audit_log = await audit_service.log_decision(
            company_id=company_id,
            agent_name="human_oversight_recruiter",
            decision_type="human_override",
            action=f"override_decision_{decision.decision_type}",
            decision=payload.new_decision,
            reasoning=[
                f"Human oversight override (Art. 14 EU AI Act): {payload.override_reason}",
                f"Original decision_id: {decision_id}",
                f"Original ai_model: {decision.ai_model_used or 'unknown'}",
            ],
            criteria_used=[],
            candidate_id=str(decision.candidate_id) if decision.candidate_id else None,
            job_vacancy_id=str(decision.vacancy_id) if decision.vacancy_id else None,
            human_review_required=False,
            criteria_ignored=PROTECTED_CRITERIA_PT,
            actor_user_id=effective_reviewer_id,
        )
        audit_entry_id = str(audit_log.id) if audit_log else None
    except Exception as exc:
        logger.error(
            "[AITransparency] audit_service.log_decision failed for decision_id=%s: %s",
            decision_id, exc,
        )
        # Não falhar o override — audit é defesa em profundidade

    return HumanOversightOverrideResponse(
        success=True,
        decision_id=decision_id,
        audit_entry_id=audit_entry_id,
        reviewed_at=now,
        new_decision=payload.new_decision,
    )


@router.get(
    "/technical-documentation",
    response_model=TechnicalDocumentationResponse,
    summary="Technical documentation (EU AI Act Annex III §1 + Art. 11)",
)
async def get_technical_documentation(
    company_id: str = Depends(require_company_id),
) -> TechnicalDocumentationResponse:
    """
    Retorna ModelCard + Annex III technical documentation deployer-facing.

    Compliance: EU AI Act Art. 11 + Annex IV (technical documentation
    obligation for high-risk AI systems Annex III item 4 — recruitment).

    Audit: AUDIT-NO-DEMO — read-only canonical documentation, no decision rendered.
    """
    # AUDIT-NO-DEMO: leitura pública de model card / technical docs canonical
    model_card = [
        ModelCardSection(
            name="Model details",
            description="Sistema multi-modelo IA com fallback canonical.",
            details={
                "providers": ["anthropic", "openai", "google"],
                "primary_model": os.getenv("LLM_PRIMARY_MODEL", "claude-opus-4-7"),  # P2-W4: reads from env var
                "fallback_chain": ["claude-sonnet-4", "gpt-5", "gemini-pro"],
                "fine_tuning": "none (instruction-tuned via prompt engineering)",
            },
        ),
        ModelCardSection(
            name="Intended use",
            description="Recrutamento humano assistido por IA — Annex III item 4.",
            details={
                "primary_users": ["recruiters", "hiring_managers", "talent_acquisition"],
                "out_of_scope": ["fully autonomous hiring", "salary determination", "performance review"],
            },
        ),
        ModelCardSection(
            name="Performance metrics",
            description="Four-Fifths Rule + chi-square fairness gates em CI.",
            details={
                "fairness_threshold": "AIR >= 0.80 (EEOC Four-Fifths)",
                "chi_square_threshold": "p >= 0.05",
                "monitoring_cadence": "real-time per-decision + quarterly aggregate",
            },
        ),
        ModelCardSection(
            name="Ethical considerations",
            description="FairnessGuard + ComplianceDomainPrompt canonical enforcement.",
            details={
                "protected_attributes_blocked": PROTECTED_CRITERIA_PT,
                "lgpd_art_11_compliance": True,
                "human_in_the_loop": "always — Art. 14 EU AI Act",
            },
        ),
        ModelCardSection(
            name="Caveats and limitations",
            description="Limitações conhecidas + recomendações de uso.",
            details={
                "language_coverage": ["pt-BR primary", "en secondary"],
                "domain_specificity": "white-collar BR market — generalizar com cautela",
                "drift_monitoring": "quarterly retraining review",
            },
        ),
    ]

    training_data_summary = {
        "source": "operational data WeDoTalent platform + synthetic golden dataset",
        "demographic_balance": "synthetic balanced baseline (golden dataset)",
        "anonymization": "ADR-LGPD-001 — aggregate anonymization N >= 10",
        "retention": "operational data: ativo + 5 anos (LGPD Art. 16)",
        "consent_basis": "execução de contrato + interesse legítimo (LGPD Art. 7 V/IX)",
    }

    intended_use = [
        "Triagem inicial de currículos com critérios objetivos da vaga",
        "Ordenação ranqueada de candidatos com fairness check",
        "Geração de perguntas WSI (Working Sample Interview) por vaga",
        "Assistência conversacional ao recrutador",
        "Explicação de decisões para candidato e recrutador",
    ]

    limitations = [
        "Não substitui julgamento humano em decisão final de contratação",
        "Não avalia atributos protegidos (LGPD Art. 11) — bloqueado por FairnessGuard",
        "Performance pode degradar em vagas com amostra < 10 candidatos",
        "Drift monitorado mas modelos LLM podem ter biases residuais (ver fairness_results)",
        "Não realiza videoanálise/biometria facial (excluído por design)",
    ]

    fairness_results = {
        "last_quarterly_audit": "2026-Q2",
        "four_fifths_rule_pass_rate": "verified at job-level via /api/v1/bias-audit/job/{id}",
        "chi_square_significance": "p >= 0.05 across protected dimensions",
        "annual_report": "see /api/v1/bias-audit/annual/{report_id} (NYC LL144)",
        "ongoing_monitoring": "FairnessReportRepository real-time",
    }

    return TechnicalDocumentationResponse(
        model_card=model_card,
        training_data_summary=training_data_summary,
        intended_use=intended_use,
        limitations=limitations,
        fairness_results=fairness_results,
        last_updated=datetime.now(UTC),
        version=TECHNICAL_DOCUMENTATION_VERSION,
    )
