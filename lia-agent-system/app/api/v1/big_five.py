"""
Big Five Personality Profile API Endpoints.

Manages Big Five personality profiles for ideal candidate matching.
Profiles are stored in client.settings["big_five_profiles"].
"""
import logging
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.models.client_account import ClientAccount
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/big-five", tags=["big-five"])


# TODO(phase2): extract ClientAccount lookup to BigFiveRepository.get_client()
def get_user_from_headers(
    company_id: str = Depends(require_company_id),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    """Get user context. company_id sourced from JWT via require_company_id (canonical)."""
    return {
        "company_id": company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin",
    }


class BigFiveTraits(BaseModel):
    """Big Five personality traits (each 1-100)."""
    openness: int = Field(..., ge=1, le=100, description="Openness to experience")
    conscientiousness: int = Field(..., ge=1, le=100, description="Conscientiousness")
    extraversion: int = Field(..., ge=1, le=100, description="Extraversion")
    agreeableness: int = Field(..., ge=1, le=100, description="Agreeableness")
    neuroticism: int = Field(..., ge=1, le=100, description="Neuroticism (emotional stability inverse)")


class BigFiveWeights(BaseModel):
    """Weights for each trait in matching (0.0-1.0, should sum to 1.0)."""
    openness: float = Field(0.2, ge=0.0, le=1.0)
    conscientiousness: float = Field(0.2, ge=0.0, le=1.0)
    extraversion: float = Field(0.2, ge=0.0, le=1.0)
    agreeableness: float = Field(0.2, ge=0.0, le=1.0)
    neuroticism: float = Field(0.2, ge=0.0, le=1.0)


class BigFiveProfileCreate(WeDoBaseModel):
    """Request model for creating a Big Five profile."""
    name: str = Field(..., min_length=1, max_length=255, description="Profile name")
    job_id: str | None = Field(None, description="Associated job vacancy ID")
    traits: dict[str, int] = Field(..., description="Big Five traits (1-100)")
    weights: dict[str, float] | None = Field(None, description="Trait weights for matching")
    description: str | None = Field(None, max_length=1000, description="Profile description")


class BigFiveProfileUpdate(WeDoBaseModel):
    """Request model for updating a Big Five profile."""
    name: str | None = Field(None, min_length=1, max_length=255)
    job_id: str | None = None
    traits: dict[str, int] | None = None
    weights: dict[str, float] | None = None
    description: str | None = Field(None, max_length=1000)


class BigFiveProfileResponse(BaseModel):
    """Response model for Big Five profile."""
    id: str
    name: str
    job_id: str | None = None
    traits: dict[str, int]
    weights: dict[str, float] | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class CandidateTraitsInput(WeDoBaseModel):
    """Candidate's Big Five traits for analysis."""
    openness: int = Field(..., ge=1, le=100)
    conscientiousness: int = Field(..., ge=1, le=100)
    extraversion: int = Field(..., ge=1, le=100)
    agreeableness: int = Field(..., ge=1, le=100)
    neuroticism: int = Field(..., ge=1, le=100)


class AnalyzeRequest(WeDoBaseModel):
    """Request model for analyzing candidate against profile."""
    profile_id: str = Field(..., description="Big Five profile ID to compare against")
    candidate_traits: CandidateTraitsInput = Field(..., description="Candidate's Big Five traits")


class TraitAnalysis(BaseModel):
    """Analysis result for a single trait."""
    trait: str
    candidate_score: int
    ideal_score: int
    difference: int
    weight: float
    weighted_score: float


class AnalyzeResponse(BaseModel):
    """Response model for candidate analysis."""
    fit_score: float = Field(..., description="Overall fit score (0-100)")
    profile_name: str
    trait_analysis: list[TraitAnalysis]
    recommendation: str


async def get_client(company_id: str, db: AsyncSession) -> ClientAccount:
    """Get client by company ID."""
    try:
        client_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    query = select(ClientAccount).where(
        and_(
            ClientAccount.id == client_uuid,
            not ClientAccount.is_deleted
        )
    )
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client not found: {company_id}"
        )
    
    return client


def get_big_five_profiles(client: ClientAccount) -> list[dict[str, Any]]:
    """Get Big Five profiles from client settings."""
    settings = client.settings or {}
    return settings.get("big_five_profiles", [])


def save_big_five_profiles(client: ClientAccount, profiles: list[dict[str, Any]]):
    """Save Big Five profiles to client settings."""
    if client.settings is None:
        client.settings = {}
    client.settings["big_five_profiles"] = profiles
    flag_modified(client, "settings")


def validate_traits(traits: dict[str, int]) -> bool:
    """Validate that traits dict contains all required Big Five traits."""
    required_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    for trait in required_traits:
        if trait not in traits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required trait: {trait}"
            )
        value = traits[trait]
        if not isinstance(value, int) or value < 1 or value > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trait {trait} must be an integer between 1 and 100"
            )
    return True


@router.get("/profiles", summary="List Big Five profiles", response_model=None)
async def list_profiles(
    job_id: str | None = Query(None, description="Filter by job ID"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all Big Five profiles for the company."""
    try:
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        if job_id:
            profiles = [p for p in profiles if p.get("job_id") == job_id]
        
        profiles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"📋 Listed {len(profiles)} Big Five profiles for company {current_user['company_id']}")
        
        return {
            "success": True,
            "data": {
                "profiles": profiles,
                "total": len(profiles)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing Big Five profiles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )


@router.post("/profiles", summary="Create Big Five profile", response_model=None)
async def create_profile(
    data: BigFiveProfileCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new Big Five profile for the company."""
    try:
        validate_traits(data.traits)
        
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        now = datetime.utcnow().isoformat()
        new_profile = {
            "id": str(uuid.uuid4()),
            "name": data.name,
            "job_id": data.job_id,
            "traits": data.traits,
            "weights": data.weights or {
                "openness": 0.2,
                "conscientiousness": 0.2,
                "extraversion": 0.2,
                "agreeableness": 0.2,
                "neuroticism": 0.2
            },
            "description": data.description,
            "created_at": now,
            "updated_at": now
        }
        
        profiles.append(new_profile)
        save_big_five_profiles(client, profiles)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created Big Five profile '{data.name}' for company {current_user['company_id']}")
        
        return {
            "success": True,
            "data": new_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating Big Five profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.get("/profiles/{profile_id}", summary="Get Big Five profile", response_model=None)
async def get_profile(
    profile_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific Big Five profile by ID."""
    try:
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        profile = next((p for p in profiles if p.get("id") == profile_id), None)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        return {
            "success": True,
            "data": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting Big Five profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.put("/profiles/{profile_id}", summary="Update Big Five profile", response_model=None)
async def update_profile(
    profile_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: BigFiveProfileUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing Big Five profile."""
    try:
        if data.traits:
            validate_traits(data.traits)
        
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        profile_index = next((i for i, p in enumerate(profiles) if p.get("id") == profile_id), None)
        
        if profile_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        profile = profiles[profile_index]
        
        if data.name is not None:
            profile["name"] = data.name
        if data.job_id is not None:
            profile["job_id"] = data.job_id
        if data.traits is not None:
            profile["traits"] = data.traits
        if data.weights is not None:
            profile["weights"] = data.weights
        if data.description is not None:
            profile["description"] = data.description
        
        profile["updated_at"] = datetime.utcnow().isoformat()
        
        profiles[profile_index] = profile
        save_big_five_profiles(client, profiles)
        
        logger.info(f"✅ Updated Big Five profile '{profile_id}' for company {current_user['company_id']}")
        
        return {
            "success": True,
            "data": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating Big Five profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/profiles/{profile_id}", summary="Delete Big Five profile", response_model=None)
async def delete_profile(
    profile_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a Big Five profile."""
    try:
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        profile_index = next((i for i, p in enumerate(profiles) if p.get("id") == profile_id), None)
        
        if profile_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        deleted_profile = profiles.pop(profile_index)
        save_big_five_profiles(client, profiles)
        
        logger.info(f"🗑️ Deleted Big Five profile '{profile_id}' for company {current_user['company_id']}")
        
        return {
            "success": True,
            "message": f"Profile '{deleted_profile.get('name')}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting Big Five profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.post("/analyze", summary="Analyze candidate against Big Five profile", response_model=None)
async def analyze_candidate(
    data: AnalyzeRequest,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Analyze a candidate's Big Five traits against an ideal profile.
    
    Returns a fit score (0-100) and detailed trait-by-trait analysis.
    """
    try:
        client = await get_client(current_user["company_id"], db)
        profiles = get_big_five_profiles(client)
        
        profile = next((p for p in profiles if p.get("id") == data.profile_id), None)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {data.profile_id}"
            )
        
        ideal_traits = profile.get("traits", {})
        weights = profile.get("weights", {
            "openness": 0.2,
            "conscientiousness": 0.2,
            "extraversion": 0.2,
            "agreeableness": 0.2,
            "neuroticism": 0.2
        })
        
        candidate_traits = {
            "openness": data.candidate_traits.openness,
            "conscientiousness": data.candidate_traits.conscientiousness,
            "extraversion": data.candidate_traits.extraversion,
            "agreeableness": data.candidate_traits.agreeableness,
            "neuroticism": data.candidate_traits.neuroticism
        }
        
        trait_analysis = []
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            candidate_score = candidate_traits.get(trait, 50)
            ideal_score = ideal_traits.get(trait, 50)
            weight = weights.get(trait, 0.2)
            
            difference = abs(candidate_score - ideal_score)
            trait_fit = max(0, 100 - difference)
            weighted_score = trait_fit * weight
            
            total_weighted_score += weighted_score
            total_weight += weight
            
            trait_analysis.append({
                "trait": trait,
                "candidate_score": candidate_score,
                "ideal_score": ideal_score,
                "difference": difference,
                "weight": weight,
                "weighted_score": round(weighted_score, 2)
            })
        
        fit_score = total_weighted_score / total_weight if total_weight > 0 else 0
        fit_score = round(fit_score, 2)
        
        if fit_score >= 80:
            recommendation = "Excelente match! O candidato demonstra alto alinhamento com o perfil ideal."
        elif fit_score >= 60:
            recommendation = "Bom match. O candidato apresenta alinhamento satisfatório com algumas áreas para desenvolvimento."
        elif fit_score >= 40:
            recommendation = "Match moderado. Considere avaliar se as diferenças são relevantes para a função."
        else:
            recommendation = "Baixo match. O perfil do candidato diverge significativamente do perfil ideal."
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📊 Analyzed candidate against profile '{profile.get('name')}': {fit_score}% fit")
        
        return {
            "success": True,
            "data": {
                "fit_score": fit_score,
                "profile_name": profile.get("name"),
                "trait_analysis": trait_analysis,
                "recommendation": recommendation
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing candidate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze candidate: {str(e)}"
        )

reorder_collection_before_item(router)
