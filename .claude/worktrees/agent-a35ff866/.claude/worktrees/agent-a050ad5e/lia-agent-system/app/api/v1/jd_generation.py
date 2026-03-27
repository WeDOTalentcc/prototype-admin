from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.services.jd_generator_service import jd_generator_service
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


@router.post("/generate")
async def generate_jd(
    request: GenerateJDRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
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
        
        # Enforce tags from provided data only
        enforced_tags = []
        if request.job_title:
            enforced_tags.append(request.job_title.lower())
        if request.department:
            enforced_tags.append(request.department.lower())
        for skill in request.technical_skills:
            enforced_tags.append(skill.lower())
        for comp in request.behavioral_competencies:
            enforced_tags.append(comp.lower())
        # Deduplicate while preserving order
        seen = set()
        unique_tags = []
        for tag in enforced_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        result["tags"] = unique_tags
        result["summary"] = ""
        
        return {"success": True, **result}
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
            
            # Enforce tags from provided data only
            enforced_tags = []
            if request.job_title:
                enforced_tags.append(request.job_title.lower())
            if request.department:
                enforced_tags.append(request.department.lower())
            for skill in request.technical_skills:
                enforced_tags.append(skill.lower())
            for comp in request.behavioral_competencies:
                enforced_tags.append(comp.lower())
            # Deduplicate while preserving order
            seen = set()
            unique_tags = []
            for tag in enforced_tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            
            return {
                "success": True,
                "full_description": desc,
                "sections": {},
                "summary": "",
                "seo_title": request.job_title,
                "tags": unique_tags,
                "from_cache": False,
            }
        except Exception as e2:
            logger.error(f"Fallback JD generation also failed: {e2}")
            return {"success": False, "error": str(e)}
