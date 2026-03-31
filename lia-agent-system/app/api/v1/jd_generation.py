from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.services.jd_generator_service import jd_generator_service
from app.shared.compliance.fairness_guard_middleware import check_fairness
from app.shared.compliance.audit_service import audit_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jd", tags=["jd-generation"])


class GenerateJDRequest(BaseModel):
    job_title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = []
    technical_skills: List[str] = []
    behavioral_competencies: List[str] = []
    salary_range: Optional[str] = None
    work_model: Optional[str] = None
    location: Optional[str] = None
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_industry: Optional[str] = None
    benefits: List[str] = []
    interview_stages: List[str] = []
    company_id: str = "default"


def _build_tags(request: GenerateJDRequest) -> List[str]:
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
    unique_tags: List[str] = []
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
    """A1/G1: FairnessGuard on generated JD output."""
    if not full_description:
        return None
    fg_output = check_fairness(
        {"full_description": full_description},
        context="jd_generation_output",
        company_id=company_id,
    )
    return fg_output


@router.post("/generate")
async def generate_jd(
    request: GenerateJDRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    _fg_check_input(request, request.company_id)

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
        result = await jd_generator_service.generate_full_description(
            job_data=job_data,
            company_id=request.company_id,
        )
        
        result["tags"] = _build_tags(request)
        result["summary"] = ""

        fg_output = _fg_check_output(result.get("full_description", ""), request.company_id)
        if fg_output and fg_output.is_blocked:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "fairness_blocked",
                    "field": "full_description",
                    "message": fg_output.blocked_result.educational_message if fg_output.blocked_result else "Viés detectado na descrição gerada.",
                    "category": fg_output.blocked_result.category if fg_output.blocked_result else None,
                },
            )
        response = {"success": True, **result}
        if fg_output and fg_output.has_warnings:
            response["fairness_warning"] = {
                "blocked": False,
                "warnings": fg_output.warnings,
            }

        try:
            await audit_service.log_decision(
                company_id=request.company_id or "default",
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
            
            fg_output = _fg_check_output(desc, request.company_id)
            if fg_output and fg_output.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "field": "full_description",
                        "message": fg_output.blocked_result.educational_message if fg_output.blocked_result else "Viés detectado na descrição gerada.",
                        "category": fg_output.blocked_result.category if fg_output.blocked_result else None,
                    },
                )
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
                await audit_service.log_decision(
                    company_id=request.company_id or "default",
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
