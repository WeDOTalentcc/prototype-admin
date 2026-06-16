"""Persist revealed contact route: POST /candidates/persist-revealed"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CVParserService,
    CandidateProfile,
    CandidateSearchResultDTO,
    EducationDTO,
    EvaluateForJobRequest,
    EvaluateForJobResponse,
    EvaluateForJobResult,
    ExperienceDTO,
    HybridSearchRequest,
    IdMapping,
    ImportCandidateDTO,
    ImportCandidateExperienceDTO,
    ImportCandidatesRequest,
    ImportCandidatesResponse,
    ImportUser,
    JobRequirement,
    JobRequirementCreate,
    LanguageDTO,
    PearchService,
    PearchSearchRequest,
    RubricEvaluationService,
    SearchRequestDTO,
    SearchResponseDTO,
    SearchType,
    User,
    _build_candidate_data_from_dto,
    _evaluate_candidates_with_rubrics,
    _generate_fingerprint,
    _get_job_requirements,
    _get_match_label,
    _normalize_name,
    _normalize_priority,
    assert_resource_ownership,
    get_current_user_or_demo,
    get_cv_parser_service,
    get_db,
    get_pearch_service,
    get_rubric_evaluation_service,
    get_user_company_id,
    logger,
    rubric_evaluation_service,
)
from app.domains.credits.services.credit_service import CreditService, get_credit_service
from app.shared.security.require_company_id import require_company_id

router = APIRouter()

class RevealedContactDTO(BaseModel):
    """Dados de contato revelado para persistência."""
    pearch_id: str = Field(..., description="ID do candidato na Pearch")
    candidate_name: str = Field(..., description="Nome do candidato")
    email: str | None = Field(None, description="Email revelado")
    phone: str | None = Field(None, description="Telefone revelado")
    linkedin_url: str | None = Field(None, description="URL do LinkedIn")
    current_title: str | None = Field(None, description="Cargo atual")
    current_company: str | None = Field(None, description="Empresa atual")
    avatar_url: str | None = Field(None, description="URL do avatar")


class RevealedContactResponse(BaseModel):
    """Response da persistência de contato revelado."""
    success: bool
    message: str
    candidate_id: str | None = None
    is_new: bool = False


@router.post("/candidates/persist-revealed", response_model=RevealedContactResponse)
async def persist_revealed_contact(
    request: RevealedContactDTO,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Persiste dados de contato revelados de candidatos Pearch.
    
    Quando o recrutador paga créditos para revelar email ou telefone,
    este endpoint salva automaticamente os dados no banco local.
    
    - Se o candidato já existe (por pearch_id): atualiza os dados de contato
    - Se não existe: cria um novo registro com os dados revelados
    """
    import uuid as uuid_lib

    from sqlalchemy import select

    from app.models.candidate import Candidate
from app.shared.errors import LIAError
    
    try:
        # Check if candidate already exists by pearch_id
        existing = await db.execute(
            select(Candidate).where(Candidate.pearch_profile_id == request.pearch_id, Candidate.company_id == company_id)
        )
        candidate = existing.scalar_one_or_none()
        
        if candidate:
            # Update existing candidate with revealed contact
            updated = False
            if request.email and not candidate.email:
                candidate.email = request.email
                updated = True
            if request.phone and not candidate.phone:
                candidate.phone = request.phone
                updated = True
            
            if updated:
                return RevealedContactResponse(
                    success=True,
                    message="Dados de contato atualizados no cadastro existente",
                    candidate_id=str(candidate.id),
                    is_new=False
                )
            else:
                return RevealedContactResponse(
                    success=True,
                    message="Candidato já possui os dados de contato",
                    candidate_id=str(candidate.id),
                    is_new=False
                )
        else:
            # Create new candidate with basic info + revealed contact
            name_parts = request.candidate_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
            
            new_id = uuid_lib.uuid4()
            candidate = Candidate(
                id=new_id,
                name=request.candidate_name,
                first_name=first_name,
                last_name=last_name,
                email=request.email,
                phone=request.phone,
                linkedin_url=request.linkedin_url,
                avatar_url=request.avatar_url,
                current_title=request.current_title,
                current_company=request.current_company,
                source="pearch",
                pearch_profile_id=request.pearch_id,
                status="new",
                is_active=True,
                additional_data={
                    "imported_via": "reveal_contact",
                    "has_revealed_email": request.email is not None,
                    "has_revealed_phone": request.phone is not None
                }
            )
            db.add(candidate)
            
            return RevealedContactResponse(
                success=True,
                message="Candidato salvo na base local com dados de contato",
                candidate_id=str(new_id),
                is_new=True
            )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error persisting revealed contact: {e}")
        raise LIAError(message="Erro interno do servidor")


