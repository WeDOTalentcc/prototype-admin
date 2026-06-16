import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.ai.services.jd_parser_service import jd_parser_service
from app.domains.job_management.services.jd_generator_service import jd_generator_service
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.compliance.fairness_guard_middleware import check_fairness
from app.core.database import AsyncSessionLocal
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jd", tags=["jd-generation"])


class ExtractJDRequest(WeDoBaseModel):
    """T-1167 (Bug #3) — extrai responsabilidades/skills/comp.comp. de um JD colado em texto livre.
    company_id vem do JWT via Depends(require_company_id) — body NÃO carrega tenant."""
    text: str


class ExtractJDResponse(BaseModel):
    success: bool
    job_title: str | None = None
    responsibilities: list[str] = []
    technical_skills: list[str] = []
    behavioral_competencies: list[str] = []


@router.post("/extract", response_model=ExtractJDResponse)
async def extract_jd(
    request: ExtractJDRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """T-1167 (Bug #3) — endpoint REST que expõe JDParserService.extract_requirements
    para a aba "Descrição do Cargo" preencher automaticamente responsabilidades/skills/
    competências a partir do JD colado pelo recrutador no campo DESCRIÇÃO/SUMÁRIO.
    Antes, o recrutador tinha que digitar tudo de novo manualmente."""
    text = (request.text or "").strip()
    if len(text) < 50:
        raise HTTPException(
            status_code=422,
            detail={"error": "text_too_short", "message": "Cole um JD com pelo menos 50 caracteres."},
        )
    # T-1167 (Bug #3) — usa SEMPRE o company_id resolvido do JWT pelo Depends.
    # Ignora qualquer company_id vindo no body (anti tenant-spoofing — code review
    # do architect achou que company_id era usado direto, abrindo
    # broken tenant isolation contract; require_company_id NÃO faz strict match).
    tenant_id = company_id
    # Reutiliza FairnessGuard input antes de mandar pro LLM.
    fg = check_fairness({"description": text}, context="jd_extract_input", company_id=tenant_id)
    if fg.is_blocked:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "fairness_blocked",
                "field": fg.blocked_field,
                "message": fg.blocked_result.educational_message if fg.blocked_result else "Viés detectado.",
                "category": fg.blocked_result.category if fg.blocked_result else None,
            },
        )
    try:
        extracted = await jd_parser_service.extract_requirements(text, company_id=tenant_id)
    except HTTPException:
        raise
    except Exception as exc:
        # Log técnico só no servidor; resposta genérica para não vazar internals.
        logger.exception("[extract_jd] parser failed")
        raise HTTPException(
            status_code=500,
            detail={"error": "extract_failed", "message": "Não foi possível extrair os campos agora. Tente novamente."},
        ) from exc

    responsibilities: list[str] = []
    technical_skills: list[str] = []
    behavioral_competencies: list[str] = []
    for req in extracted.get("requirements", []) or []:
        text_val = (req.get("requirement") or "").strip()
        if not text_val:
            continue
        category = (req.get("category") or "").lower()
        if category == "technical":
            technical_skills.append(text_val)
        elif category in ("soft_skill", "soft", "behavioral"):
            behavioral_competencies.append(text_val)
        elif category in ("experience", "responsibility", "responsibilities"):
            responsibilities.append(text_val)
        else:
            # Heurística leve: itens que começam com verbo no infinitivo ("Desenvolver",
            # "Coordenar", "Liderar"...) provavelmente são responsabilidades, e não skills.
            if re.match(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(ar|er|ir)\b", text_val):
                responsibilities.append(text_val)
    return ExtractJDResponse(
        success=True,
        job_title=extracted.get("job_title"),
        responsibilities=responsibilities,
        technical_skills=technical_skills,
        behavioral_competencies=behavioral_competencies,
    )


class GenerateJDRequest(WeDoBaseModel):
    job_title: str
    department: str | None = None
    seniority: str | None = None
    description: str | None = None
    responsibilities: list[str] = []
    technical_skills: list[str] = []
    behavioral_competencies: list[str] = []
    salary_range: str | None = None
    work_model: str | None = None
    location: str | None = None
    company_name: str | None = None
    company_description: str | None = None
    company_industry: str | None = None
    benefits: list[str] = []
    interview_stages: list[str] = []
    # Cultura & EVP --- opcionais, injetados no prompt quando presentes
    mission: str | None = None
    vision: str | None = None
    evp_bullets: list[str] | None = None


def _build_tags(request: GenerateJDRequest) -> list[str]:
    enforced_tags = []
    if request.job_title:
        enforced_tags.append(request.job_title.lower())
    if request.department:
        enforced_tags.append(request.department.lower())
    for skill in request.technical_skills:
        enforced_tags.append(skill.lower())
    for comp in request.behavioral_competencies:
        enforced_tags.append(comp.lower())
    seen: set = set()
    unique_tags: list[str] = []
    for tag in enforced_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    return unique_tags


def _fg_check_input(request: GenerateJDRequest, company_id: str):
    """A1/G1: FairnessGuard on JD input fields before generation."""
    input_texts: dict[str, str] = {}
    if request.description:
        input_texts["description"] = request.description
    combined_responsibilities = " ".join(request.responsibilities) if request.responsibilities else ""
    if combined_responsibilities:
        input_texts["responsibilities"] = combined_responsibilities
    if input_texts:
        fg_input = check_fairness(input_texts, context="jd_generation_input", company_id=company_id)
        if fg_input.is_blocked:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "fairness_blocked",
                    "field": fg_input.blocked_field,
                    "message": fg_input.blocked_result.educational_message if fg_input.blocked_result else "Viés detectado.",
                    "category": fg_input.blocked_result.category if fg_input.blocked_result else None,
                },
            )
        return fg_input
    return None


def _fg_check_output(full_description: str, company_id: str):
    """DEPRECATED — T-1167 / Bug #1 (vaga 200).

    Originalmente esta função rodava FairnessGuard Layer 1 (regex) sobre o
    texto enriquecido que o LLM gerou. Problema: a LIA frequentemente inclui
    boilerplate de inclusão como "Não discriminamos por orientação sexual,
    gênero, raça, religião..." — uso LEGÍTIMO E INCLUSIVO desses termos.
    O regex Layer 1 não distingue uso discriminatório vs. inclusivo, então
    bloqueava 422 com a `educational_message` da categoria (ex.: ADO 26 sobre
    orientação sexual), confundindo o recrutador.

    Decisão (usuário, 2026-05): manter `_fg_check_input` (valida o que o
    RECRUTADOR escreveu — legítimo) e remover a checagem de output. Layer 1
    regex no output é low-signal high-noise. Caso futuro precise voltar uma
    proteção semântica no output, usar `check_with_layer3` com prompt que
    distinga uso inclusivo vs. discriminatório.

    Mantida com retorno None para preservar callsites e o teste sentinela.
    """
    return None


@router.post("/generate", response_model=None)
async def generate_jd(
    request: GenerateJDRequest,
    current_user: User = Depends(get_current_user_or_demo),
    audit_svc: AuditService = Depends(get_audit_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    _fg_check_input(request, company_id)

    try:
        job_data = {
            "title": request.job_title,
            "department": request.department,
            "seniority": request.seniority,
            "description": request.description,
            "responsibilities": request.responsibilities,
            "technical_skills": request.technical_skills,
            "behavioral_competencies": request.behavioral_competencies,
            "salary_range": request.salary_range,
            "work_model": request.work_model,
            "location": request.location,
            "company_name": request.company_name,
            "company_description": request.company_description,
            "company_industry": request.company_industry,
            "benefits": request.benefits,
            "interview_stages": request.interview_stages,
        }
        # Cultura & EVP --- montar contexto se algum campo foi fornecido
        _culture_parts = []
        if request.mission:
            _culture_parts.append("Missao: " + request.mission)
        if request.vision:
            _culture_parts.append("Visao: " + request.vision)
        if request.evp_bullets:
            _culture_parts.append("EVP/Proposta de Valor: " + "; ".join(request.evp_bullets))
        if _culture_parts:
            job_data["company_culture"] = "\n".join(_culture_parts)
        # Produtor único: contexto rico de empresa filtrado por lia_field_toggles,
        # alinhando o JD standalone com o wizard. Endpoint não tem db; abre sessão.
        from app.shared.services.lia_agent_context_builder import (
            build_company_agent_context,
        )
        try:
            async with AsyncSessionLocal() as _cc_db:
                _company_ctx = await build_company_agent_context(
                    company_id=company_id, db=_cc_db, job_context=None,
                ) or ""
        except Exception as _cc_exc:
            logger.warning("[generate_jd] company_context falhou: %s", _cc_exc)
            _company_ctx = ""
        if _company_ctx:
            _existing = job_data.get("company_culture") or ""
            job_data["company_culture"] = (
                (_existing + "\n\n" + _company_ctx).strip() if _existing else _company_ctx
            )
        result = await jd_generator_service.generate_full_description(
            job_data=job_data,
            company_id=company_id,
        )
        
        result["tags"] = _build_tags(request)
        result["summary"] = ""

        # T-1167 / Bug #1 — `_fg_check_output` desativado (ver docstring).
        # Mantém a chamada (retorna None) para manter a forma do fluxo e
        # facilitar reativação futura com Layer 3 semântico se necessário.
        fg_output = _fg_check_output(result.get("full_description", ""), company_id)
        response = {"success": True, **result}
        if fg_output and getattr(fg_output, "has_warnings", False):
            response["fairness_warning"] = {
                "blocked": False,
                "warnings": fg_output.warnings,
            }

        try:
            await audit_svc.log_decision(
                company_id=company_id,
                agent_name="jd_generator",
                decision_type="generate_jd",
                action="generate_full_description",
                decision="generated",
                reasoning=[
                    f"JD gerada para '{request.job_title}'",
                    f"FairnessGuard: {'warnings' if (fg_output and fg_output.has_warnings) else 'passed'}",
                ],
                criteria_used=["job_title", "department", "seniority", "responsibilities", "technical_skills", "behavioral_competencies"],
                job_vacancy_id=None,
                confidence=1.0,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning("GOV-01: audit log failed for JD generation: %s", audit_err)

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating JD: {e}")
        try:
            job_data_sync = {
                "title": request.job_title,
                "department": request.department,
                "seniority": request.seniority,
                "responsibilities": request.responsibilities,
                "technical_skills": request.technical_skills,
                "behavioral_competencies": request.behavioral_competencies,
                "company_name": request.company_name,
                "company_description": request.company_description,
                "company_industry": request.company_industry,
                "benefits": request.benefits,
                "interview_stages": request.interview_stages,
            }
            desc = jd_generator_service.generate_description(job_data_sync)
            
            # T-1167 / Bug #1 — `_fg_check_output` desativado (retorna None,
            # ver docstring). Chamada mantida para preservar a forma do fluxo
            # e facilitar reativação futura com Layer 3 semântico.
            fg_output = _fg_check_output(desc, company_id)
            response = {
                "success": True,
                "full_description": desc,
                "sections": {},
                "summary": "",
                "seo_title": request.job_title,
                "tags": _build_tags(request),
                "from_cache": False,
            }
            if fg_output and fg_output.has_warnings:
                response["fairness_warning"] = {
                    "blocked": False,
                    "warnings": fg_output.warnings,
                }

            try:
                await audit_svc.log_decision(
                    company_id=company_id,
                    agent_name="jd_generator",
                    decision_type="generate_jd",
                    action="generate_description_fallback",
                    decision="generated",
                    reasoning=[
                        f"JD gerada (fallback sync) para '{request.job_title}'",
                        f"FairnessGuard: {'warnings' if (fg_output and fg_output.has_warnings) else 'passed'}",
                    ],
                    criteria_used=["job_title", "department", "seniority", "responsibilities", "technical_skills", "behavioral_competencies"],
                    job_vacancy_id=None,
                    confidence=0.8,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning("GOV-01: audit log failed for JD fallback generation: %s", audit_err)

            return response
        except HTTPException:
            raise
        except Exception as e2:
            logger.error(f"Fallback JD generation also failed: {e2}")
            return {"success": False, "error": str(e)}
