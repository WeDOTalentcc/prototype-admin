"""
Semantic Search API Endpoints

Provides semantic expansion for advanced filters modal fields.
Supports 8 domains with LLM-powered suggestions and Redis caching.
"""


from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.shared.services.semantic_search_service import (
    SemanticDomain,
    SemanticExpansionResult,
    semantic_search_service,
)
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/semantic-search", tags=["Semantic Search"])


class SemanticSearchRequest(WeDoBaseModel):
    query: str = Field(..., min_length=2, max_length=200, description="Search query to expand")
    existing: list[str] = Field(default=[], description="Already selected items to exclude")
    

class SemanticSearchResponse(BaseModel):
    success: bool = True
    data: SemanticExpansionResult
    

@router.post("/skills", response_model=SemanticSearchResponse)
async def expand_skills(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand skill search with semantic suggestions.
    
    Examples:
    - "React" → ReactJS, Next.js, Redux, TypeScript
    - "Python" → Django, FastAPI, Flask, NumPy
    - "AWS" → EC2, Lambda, S3, CloudFormation
    """
    result = await semantic_search_service.expand_skills(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/job-titles", response_model=SemanticSearchResponse)
async def expand_job_titles(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand job title search with semantic suggestions.
    
    Examples:
    - "Backend Developer" → Desenvolvedor Backend, Back-End Engineer, Software Engineer
    - "Product Manager" → PM, Gerente de Produto, Product Owner
    - "Data Scientist" → ML Engineer, Data Analyst, AI Researcher
    """
    result = await semantic_search_service.expand_job_titles(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/roles", response_model=SemanticSearchResponse)
async def expand_roles(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand function/role search with semantic suggestions.
    
    Examples:
    - "Engineering" → Development, Architecture, DevOps
    - "Product" → PM, Product Management, UX
    - "Data" → Analytics, Data Science, BI
    """
    result = await semantic_search_service.expand_roles(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/industries", response_model=SemanticSearchResponse)
async def expand_industries(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand industry/sector search with semantic suggestions.
    
    Examples:
    - "Fintech" → Banking, Payments, Insurtech, Financial Services
    - "Tech" → SaaS, E-commerce, AI, Cloud
    - "Saúde" → Healthcare, Healthtech, Pharma, Biotech
    """
    result = await semantic_search_service.expand_industries(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/expertise", response_model=SemanticSearchResponse)
async def expand_expertise(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand expertise area search with semantic suggestions.
    
    Examples:
    - "Machine Learning" → Data Science, AI, Deep Learning, NLP
    - "DevOps" → SRE, Cloud, Infrastructure, Platform Engineering
    - "Full Stack" → Frontend, Backend, Web Development
    """
    result = await semantic_search_service.expand_expertise(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/fields-of-study", response_model=SemanticSearchResponse)
async def expand_fields_of_study(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand field of study search with semantic suggestions.
    
    Examples:
    - "Computer Science" → Software Engineering, Information Systems
    - "Administração" → Business Administration, MBA, Management
    - "Engineering" → Civil, Electrical, Mechanical, Software
    """
    result = await semantic_search_service.expand_fields_of_study(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/companies", response_model=SemanticSearchResponse)
async def expand_company_competitors(request: SemanticSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Expand company search with competitors and similar companies.
    
    Examples:
    - "Nubank" → Inter, C6 Bank, PicPay, Banco Original
    - "iFood" → Rappi, Uber Eats, 99Food
    - "TOTVS" → Linx, Senior, Sankhya
    """
    result = await semantic_search_service.expand_company_competitors(
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)


@router.post("/expand/{domain}", response_model=SemanticSearchResponse)
async def expand_generic(
    domain: SemanticDomain,
    request: SemanticSearchRequest, 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (semantic_search) — no tenant data
    """
    Generic endpoint to expand any domain.
    
    Domains: skills, job_titles, roles, industries, expertise, fields_of_study, companies
    """
    result = await semantic_search_service.expand_query(
        domain=domain,
        query=request.query,
        existing=request.existing
    )
    return SemanticSearchResponse(data=result)
