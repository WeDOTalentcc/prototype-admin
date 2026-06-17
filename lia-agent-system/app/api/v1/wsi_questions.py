"""
WSI Questions API - Endpoints for WSI question generation and regeneration.

All question generation is delegated to the canonical WSIService (F6 pipeline:
CBI + Bloom + Dreyfus + BigFive). This module handles:
- HTTP request/response mapping and validation
- FairnessGuard compliance checks (A2/G1)
- Audit logging of generation events
- Question coverage validation (3+ technical, 2+ behavioral minimums)
- Template fallback endpoint (/question-templates GET)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, get_tenant_db
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.compliance.fairness_guard_middleware import check_fairness
from app.domains.cv_screening.dependencies import WSIService, get_wsi_service
from app.shared.security.require_company_id import require_company_id
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

router = APIRouter(prefix="/wsi", tags=["WSI Questions"])
logger = logging.getLogger(__name__)

MIN_TECHNICAL_QUESTIONS = 4
MIN_BEHAVIORAL_QUESTIONS = 2
MIN_ELIGIBILITY_QUESTIONS = 2
DEFAULT_MAX_QUESTIONS = 12



# DUPLICATE_OF_INTENT: app/domains/cv_screening/services/wsi_service/models.py — API wire-format subset of canonical WSI question (Sprint Q.1 triagem I bucket)
class WSIQuestion(BaseModel):
    """WSI question structure."""
    id: str
    question: str
    type: str = "open"
    required: bool = True
    options: list[str] | None = None
    expected_answer: str | None = None
    competency_validated: str | None = None
    skill_type: str | None = None
    block_id: int | None = None


# Sprint E.1 #44: canonical GenerateQuestionsRequest lives in app/api/v1/wsi/_shared.py.
from app.api.v1.wsi._shared import GenerateQuestionsRequest  # noqa: F401
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError


class RegenerateQuestionsRequest(WeDoBaseModel):
    """Request to regenerate WSI questions based on full competency lists."""
    job_title: str
    current_questions: list[WSIQuestion] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    behavioral_competencies: list[str] = Field(default_factory=list)
    seniority: str | None = None
    max_questions: int = DEFAULT_MAX_QUESTIONS

    @validator('technical_skills', 'behavioral_competencies', pre=True, always=True)
    def filter_empty_strings(cls, v):
        if v is None:
            return []
        return [s.strip() for s in v if s and s.strip()]


class QuestionsResponse(BaseModel):
    """Response with generated questions."""
    success: bool
    questions: list[WSIQuestion]
    changes_summary: str | None = None
    questions_added: int = 0
    questions_removed: int = 0
    quality_warnings: list[str] = Field(default_factory=list)
    block_distribution: dict | None = None


ELIGIBILITY_TEMPLATES = [
    WSIQuestion(
        id="wsi-elig-availability",
        question="Qual sua disponibilidade para início? Existe algum período de aviso prévio ou compromisso atual que precisemos considerar?",
        type="eliminatory",
        required=True,
        competency_validated="Disponibilidade",
        skill_type="eligibility",
        block_id=2
    ),
    WSIQuestion(
        id="wsi-elig-work-model",
        question="Esta posição requer [modelo de trabalho]. Isso é compatível com sua situação atual? Há alguma restrição de localização?",
        type="eliminatory",
        required=True,
        competency_validated="Modelo de Trabalho",
        skill_type="eligibility",
        block_id=2
    )
]

QUESTION_TEMPLATES = {
    "technical": {
        "Python": "Descreva um projeto onde você utilizou Python para resolver um problema complexo. Quais bibliotecas você usou?",
        "JavaScript": "Como você organiza o código JavaScript em projetos grandes? Cite padrões que utiliza.",
        "React": "Explique como você gerencia estado em aplicações React. Já usou Redux, Context API ou outras soluções?",
        "Node.js": "Descreva sua experiência com Node.js em aplicações de produção. Como lida com escalabilidade?",
        "SQL": "Dê um exemplo de uma query SQL complexa que você escreveu. Como otimizou a performance?",
        "Docker": "Como você utiliza Docker no seu fluxo de trabalho? Tem experiência com orquestração?",
        "AWS": "Quais serviços AWS você já utilizou? Descreva um projeto onde aplicou arquitetura cloud.",
        "TypeScript": "Quais benefícios você vê no uso de TypeScript? Como aplica tipagem avançada?",
        "Kubernetes": "Descreva sua experiência com Kubernetes. Já configurou clusters em produção?",
        "Git": "Como você organiza branches e commits? Qual estratégia de git flow prefere?",
        "Java": "Descreva sua experiência com Java. Quais frameworks já utilizou em produção?",
        "C#": "Como você estrutura projetos em C#? Tem experiência com .NET Core?",
        "Go": "Quais são os benefícios que você vê no uso de Go? Em quais projetos aplicou?",
        "Ruby": "Descreva sua experiência com Ruby on Rails. Como lida com performance?",
        "PHP": "Como você organiza código em PHP? Quais frameworks conhece?",
    },
    "behavioral": {
        "Comunicação": "Conte sobre uma situação onde precisou explicar algo técnico para uma pessoa não-técnica.",
        "Liderança": "Descreva um momento onde liderou uma equipe ou projeto. Quais desafios enfrentou?",
        "Resolução de Problemas": "Fale sobre um problema complexo que resolveu. Qual foi sua abordagem?",
        "Trabalho em Equipe": "Como você lida com conflitos em equipe? Dê um exemplo concreto.",
        "Adaptabilidade": "Conte sobre uma mudança significativa no trabalho. Como se adaptou?",
        "Proatividade": "Descreva uma iniciativa que você tomou sem ser solicitado. Qual foi o resultado?",
        "Organização": "Como você gerencia múltiplas tarefas com prazos conflitantes?",
        "Empatia": "Conte sobre uma situação onde precisou entender o ponto de vista do outro.",
        "Resiliência": "Fale sobre um fracasso ou obstáculo significativo. Como superou?",
        "Pensamento Analítico": "Descreva uma decisão importante que tomou baseada em dados.",
        "Criatividade": "Conte sobre uma solução criativa que você propôs para um problema.",
        "Foco no Cliente": "Descreva uma situação onde foi além para atender às necessidades de um cliente.",
    }
}


def normalize_competency(comp: str) -> str:
    return comp.strip().lower()


def validate_question_coverage(
    questions: list[WSIQuestion],
    technical_skills: list[str],
    behavioral_competencies: list[str]
) -> list[str]:
    warnings = []
    tech_questions = [q for q in questions if q.skill_type == "technical"]
    behav_questions = [q for q in questions if q.skill_type == "behavioral"]
    elig_questions = [q for q in questions if q.block_id == 2 or q.skill_type == "eligibility"]

    if len(elig_questions) < MIN_ELIGIBILITY_QUESTIONS:
        warnings.append(f"Apenas {len(elig_questions)} perguntas de elegibilidade. Recomendado: {MIN_ELIGIBILITY_QUESTIONS}+")

    if len(tech_questions) < MIN_TECHNICAL_QUESTIONS and len(technical_skills) >= MIN_TECHNICAL_QUESTIONS:
        warnings.append(f"Apenas {len(tech_questions)} perguntas técnicas geradas. Recomendado: {MIN_TECHNICAL_QUESTIONS}+")

    if len(behav_questions) < MIN_BEHAVIORAL_QUESTIONS and len(behavioral_competencies) >= MIN_BEHAVIORAL_QUESTIONS:
        warnings.append(f"Apenas {len(behav_questions)} perguntas comportamentais geradas. Recomendado: {MIN_BEHAVIORAL_QUESTIONS}+")

    return warnings


@router.post("/generate-questions", response_model=QuestionsResponse)
async def generate_wsi_questions(
    request: GenerateQuestionsRequest,
    audit_svc: AuditService = Depends(get_audit_service),
    wsi_svc: WSIService = Depends(get_wsi_service),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Generate WSI questions based on job competencies using Gemini LLM.
    Falls back to template-based generation if LLM is unavailable.
    """
    try:
        _raw = await wsi_svc.generate_from_simple_inputs(
            skills=request.technical_skills,
            behavioral=request.behavioral_competencies,
            seniority=request.seniority or "pleno",
            job_description=f"{request.job_title}. " + ", ".join(request.responsibilities) if request.responsibilities else request.job_title,
            mode="full" if request.max_questions >= 10 else "compact",
        )
        questions: list[WSIQuestion] = []
        for wq in _raw:
            skill_type = "behavioral" if wq.framework == "BigFive" or wq.question_type == "situational" else "technical"
            block_id = 4 if skill_type == "behavioral" else 3
            questions.append(WSIQuestion(
                id=wq.id,
                question=wq.question_text,
                type="open",
                required=True,
                competency_validated=wq.competency,
                skill_type=skill_type,
                block_id=block_id,
            ))
        for tmpl in ELIGIBILITY_TEMPLATES:
            questions.insert(0, tmpl.model_copy())
        questions = questions[:request.max_questions]
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Generated {len(questions)} WSI questions via canonical F6 pipeline for '{request.job_title}'")

        # A2/G1: FairnessGuard check on generated question texts
        filtered_questions: list[WSIQuestion] = []
        fg_removed = 0
        for q in questions:
            fg_result = check_fairness(
                {"question": q.question},
                context="wsi_question_generation",
                company_id=company_id,
            )
            if fg_result.is_blocked:
                logger.warning(
                    "[WSI][A2] FairnessGuard blocked question id=%s category=%s",
                    q.id, fg_result.blocked_result.category if fg_result.blocked_result else "unknown",
                )
                fg_removed += 1
            else:
                filtered_questions.append(q)

        if fg_removed:
            logger.info("[WSI][A2] %d question(s) removed by FairnessGuard", fg_removed)

        warnings = validate_question_coverage(
            filtered_questions,
            request.technical_skills,
            request.behavioral_competencies
        )
        if fg_removed:
            warnings.append(f"{fg_removed} pergunta(s) removida(s) pelo FairnessGuard por conterem viés discriminatório.")

        block_distribution = {}
        for q in filtered_questions:
            bid = q.block_id or (3 if q.skill_type == "technical" else 4)
            block_distribution[bid] = block_distribution.get(bid, 0) + 1

        try:
            await audit_svc.log_decision(
                company_id=company_id or None,
                agent_name="wsi_service",
                decision_type="generate_wsi_questions",
                action="generate_questions",
                decision="generated",
                reasoning=[
                    f"WSI questions geradas para '{request.job_title}'",
                    f"Total: {len(filtered_questions)} aprovadas, {fg_removed} removidas por FairnessGuard",
                ],
                criteria_used=["technical_skills", "behavioral_competencies", "seniority", "department"],
                job_vacancy_id=None,
                confidence=1.0,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning("GOV-01: audit log failed for WSI generation: %s", audit_err)

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13 — canonical
        # AutomatedDecisionExplanation row (distinto do AuditService.log_decision
        # acima, que grava agent_decisions). AITransparencyPanel le esta tabela
        # para exibir decisao IA ao recrutador/DPO/candidato per Art. 20.
        try:
            mode = "full" if request.max_questions >= 10 else "compact"
            seniority = request.seniority or "pleno"
            await log_automated_decision(
                db=db,
                company_id=company_id,
                decision_type="wsi_legacy_questions",
                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                explanation_text=(
                    f'Gerou {len(filtered_questions)} pergunta(s) WSI para "{request.job_title}" '
                    f'(senioridade={seniority}, mode={mode}) via /api/v1/wsi/generate-questions '
                    f'(legacy endpoint). Skills tecnicos: {request.technical_skills}. '
                    f'Comportamentais: {request.behavioral_competencies}. '
                    f'{fg_removed} pergunta(s) removida(s) por FairnessGuard.'
                ),
                criteria_used=[
                    *[f"skill:{s}" for s in request.technical_skills],
                    *[f"behavioral:{b}" for b in request.behavioral_competencies],
                    f"seniority:{seniority}",
                    f"mode:{mode}",
                ],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                confidence_score=None,
                review_eligible=True,
                extra_metadata={
                    "endpoint": "/wsi/generate-questions",
                    "job_title": request.job_title,
                    "questions_count": len(filtered_questions),
                    "fairness_guard_removed": fg_removed,
                    "max_questions": request.max_questions,
                    "mode": mode,
                    "seniority": seniority,
                    "block_distribution": block_distribution,
                    "prompt_template_version": "wsi_F6_pipeline_v2",
                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                    "legacy": True,
                },
            )
        except ValueError:
            raise
        except Exception as audit_err2:
            logger.error(
                "WT-2022 P0.C wave 2: log_automated_decision falhou em /wsi/generate-questions "
                "(LGPD Art. 20 audit gap, job_title=%s, company=%s): %s",
                request.job_title, company_id, audit_err2, exc_info=True,
            )

        return QuestionsResponse(
            success=True,
            questions=filtered_questions,
            questions_added=len(filtered_questions),
            questions_removed=fg_removed,
            quality_warnings=warnings,
            block_distribution=block_distribution
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating WSI questions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/regenerate-questions", response_model=QuestionsResponse)
async def regenerate_wsi_questions(
    request: RegenerateQuestionsRequest,
    wsi_svc: WSIService = Depends(get_wsi_service),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Regenerate WSI questions when competencies change.

    Accepts full competency lists and computes diffs server-side:
    - Keeps questions for competencies still in the list
    - Removes questions for competencies no longer in the list
    - Generates new questions for new competencies via LLM
    - Ensures minimum WSI quality thresholds
    """
    try:
        current_questions = request.current_questions

        current_tech_set: set[str] = {normalize_competency(c) for c in request.technical_skills}
        current_behav_set: set[str] = {normalize_competency(c) for c in request.behavioral_competencies}
        all_current_competencies = current_tech_set | current_behav_set

        retained_questions: list[WSIQuestion] = []
        covered_competencies: set[str] = set()
        removed_count = 0

        for q in current_questions:
            if q.competency_validated:
                comp_normalized = normalize_competency(q.competency_validated)
                if comp_normalized in all_current_competencies:
                    retained_questions.append(q)
                    covered_competencies.add(comp_normalized)
                else:
                    removed_count += 1
            else:
                retained_questions.append(q)

        new_tech = [s for s in request.technical_skills if normalize_competency(s) not in covered_competencies]
        new_behav = [s for s in request.behavioral_competencies if normalize_competency(s) not in covered_competencies]

        added_count = 0
        tech_count = sum(1 for q in retained_questions if q.skill_type == "technical")
        behav_count = sum(1 for q in retained_questions if q.skill_type == "behavioral")

        tech_needed = max(0, MIN_TECHNICAL_QUESTIONS - tech_count)
        tech_to_generate = new_tech[:max(tech_needed, 2)]
        behav_needed = max(0, MIN_BEHAVIORAL_QUESTIONS - behav_count)
        behav_to_generate = new_behav[:max(behav_needed, 1)]

        if tech_to_generate or behav_to_generate:
            _raw = await wsi_svc.generate_from_simple_inputs(
                skills=tech_to_generate,
                behavioral=behav_to_generate,
                seniority=request.seniority or "pleno",
                job_description=request.job_title,
                mode="compact",
            )
            for wq in _raw:
                if len(retained_questions) >= request.max_questions:
                    break
                skill_type = "behavioral" if wq.framework == "BigFive" or wq.question_type == "situational" else "technical"
                block_id = 4 if skill_type == "behavioral" else 3
                new_q = WSIQuestion(
                    id=wq.id,
                    question=wq.question_text,
                    type="open",
                    required=True,
                    competency_validated=wq.competency,
                    skill_type=skill_type,
                    block_id=block_id,
                )
                retained_questions.append(new_q)
                covered_competencies.add(normalize_competency(wq.competency))
                added_count += 1

        changes = []
        if added_count > 0:
            changes.append(f"Adicionadas {added_count} novas perguntas")
        if removed_count > 0:
            changes.append(f"Removidas {removed_count} perguntas de competências não mais selecionadas")

        warnings = validate_question_coverage(
            retained_questions,
            request.technical_skills,
            request.behavioral_competencies
        )

        # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
        # Regenerate so chama LLM se added_count > 0; logar quando houve
        # decisao IA (added_count > 0) — quando so houve drop (added_count=0,
        # removed_count>0), nao houve IA-generated content novo, mas ainda
        # vale registrar pra auditabilidade da operacao manage.
        try:
            seniority = request.seniority or "pleno"
            await log_automated_decision(
                db=db,
                company_id=company_id,
                decision_type="wsi_legacy_questions",
                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                explanation_text=(
                    f'Regenerou pool de perguntas WSI para "{request.job_title}" '
                    f'(senioridade={seniority}). Adicionou {added_count} pergunta(s) novas via '
                    f'wsi_service, removeu {removed_count} por mudanca de competencias, '
                    f'mantendo {len(retained_questions)} perguntas no total.'
                ),
                criteria_used=[
                    *[f"skill:{s}" for s in request.technical_skills],
                    *[f"behavioral:{b}" for b in request.behavioral_competencies],
                    f"seniority:{seniority}",
                    "mode:compact",
                    "operation:regenerate",
                ],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                confidence_score=None,
                review_eligible=True,
                extra_metadata={
                    "endpoint": "/wsi/regenerate-questions",
                    "job_title": request.job_title,
                    "questions_count": len(retained_questions),
                    "added_count": added_count,
                    "removed_count": removed_count,
                    "max_questions": request.max_questions,
                    "mode": "compact",
                    "seniority": seniority,
                    "operation": "regenerate",
                    "prompt_template_version": "wsi_F6_pipeline_v2",
                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                    "legacy": True,
                    "ia_invoked": bool(added_count > 0),
                },
            )
        except ValueError:
            raise
        except Exception as audit_err:
            logger.error(
                "WT-2022 P0.C wave 2: log_automated_decision falhou em /wsi/regenerate-questions "
                "(LGPD Art. 20 audit gap, job_title=%s, company=%s): %s",
                request.job_title, company_id, audit_err, exc_info=True,
            )

        return QuestionsResponse(
            success=True,
            questions=retained_questions,
            changes_summary=". ".join(changes) if changes else "Nenhuma alteração necessária",
            questions_added=added_count,
            questions_removed=removed_count,
            quality_warnings=warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating WSI questions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/question-templates", response_model=None)
async def get_question_templates(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get available question templates for reference.
    """
    return {
        "success": True,
        "templates": QUESTION_TEMPLATES,
        "supported_technical": list(QUESTION_TEMPLATES.get("technical", {}).keys()),
        "supported_behavioral": list(QUESTION_TEMPLATES.get("behavioral", {}).keys()),
        "minimums": {
            "technical": MIN_TECHNICAL_QUESTIONS,
            "behavioral": MIN_BEHAVIORAL_QUESTIONS
        }
    }
