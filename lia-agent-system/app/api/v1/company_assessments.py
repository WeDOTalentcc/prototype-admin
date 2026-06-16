"""Company assessments (Big Five + Technical) API.

Onda 4.2c-G-C (2026-05-23): big_five_questions e technical_questions
sao pools GLOBAIS (sem coluna company_id) usados por TODAS empresas.
Mutacoes (PUT/DELETE) sao restritas a UserRole.wedotalent_admin via
require_wedotalent_admin_role helper.

Decisao produto pendente: migrar pra per-tenant ou manter global
staff-only (default atual).
"""
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.domains.company.dependencies import (
    get_big_five_repo,
    get_technical_test_repo,
)


def require_wedotalent_admin_role(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Onda 4.2c-G-C (2026-05-23): role gate pra mutacoes em pools globais.

    big_five_questions e technical_questions sao tabelas GLOBAIS sem
    coluna company_id. Qualquer mutacao afeta TODAS as empresas. Apenas
    staff WeDOTalent (wedotalent_admin) pode mutar.

    Tenant admin/recruiter/viewer: 403 Forbidden.
    """
    if current_user.role != UserRole.wedotalent_admin:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only WeDOTalent staff can modify global assessment question pools. "
                "Contact WeDOTalent support to request changes."
            ),
        )
    return current_user
from app.domains.company.repositories.big_five_repository import BigFiveRepository
from app.domains.company.repositories.technical_test_repository import TechnicalTestRepository
from app.schemas.company import (
    BigFiveQuestionCreate,
    BigFiveQuestionResponse,
    BigFiveQuestionUpdate,
    BigFiveRoleProfileCreate,
    BigFiveRoleProfileResponse,
    BigFiveRoleProfileUpdate,
    TechnicalQuestionCreate,
    TechnicalQuestionResponse,
    TechnicalQuestionUpdate,
    TechnicalTestTemplateCreate,
    TechnicalTestTemplateResponse,
    TechnicalTestTemplateUpdate,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])

@router.get("/big-five/questions", response_model=list[BigFiveQuestionResponse])
async def list_big_five_questions(
    trait: str | None = Query(None),
    category: str | None = Query(None),
    is_core: bool | None = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List Big Five personality questions."""
    try:
        questions = await bf_repo.list_questions(trait=trait)
        if category:
            questions = [q for q in questions if q.category == category]
        if is_core is not None:
            questions = [q for q in questions if q.is_core == is_core]
        if not include_inactive:
            questions = [q for q in questions if q.is_active]
        return questions[skip: skip + limit]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Big Five questions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/big-five/questions", response_model=BigFiveQuestionResponse)
async def create_big_five_question(
    data: BigFiveQuestionCreate,
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new Big Five question."""
    try:
        question = await bf_repo.create_question(data.model_dump())
        logger.info(f"Created Big Five question for trait: {question.trait}")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Big Five question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/big-five/questions/{question_id}", response_model=BigFiveQuestionResponse)
async def update_big_five_question(
    question_id: uuid.UUID,
    data: BigFiveQuestionUpdate,
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
    # Onda 4.2c-P0-8 (2026-05-23): role gate — pool global, so staff WeDOTalent.
    _staff: User = Depends(require_wedotalent_admin_role),
    company_id: str = Depends(require_company_id),
):
    """Update a Big Five question (global pool, staff-only)."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        question = await bf_repo.update_question(question_id, update_data)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Big Five question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/big-five/questions/{question_id}", response_model=None)
async def delete_big_five_question(
    question_id: uuid.UUID,
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
    # Onda 4.2c-P0-8 (2026-05-23): role gate — pool global, so staff WeDOTalent.
    _staff: User = Depends(require_wedotalent_admin_role),
    company_id: str = Depends(require_company_id),
):
    """Soft delete a Big Five question (global pool, staff-only)."""
    try:
        deleted = await bf_repo.delete_question(question_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Question not found")
        return {"success": True, "message": "Question deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Big Five question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/big-five/role-profiles", response_model=list[BigFiveRoleProfileResponse])
async def list_big_five_role_profiles(
    company_id: uuid.UUID | None = Query(None),
    role_category: str | None = Query(None),
    include_templates: bool = Query(True),
    include_inactive: bool = Query(False),
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List Big Five role profiles."""
    try:
        if not company_id:
            return []
        profiles = await bf_repo.list_role_profiles(company_id)
        if role_category:
            profiles = [p for p in profiles if p.role_category == role_category]
        if not include_templates:
            profiles = [p for p in profiles if not p.is_template]
        if not include_inactive:
            profiles = [p for p in profiles if p.is_active]
        return profiles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Big Five role profiles: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/big-five/role-profiles", response_model=BigFiveRoleProfileResponse)
async def create_big_five_role_profile(
    data: BigFiveRoleProfileCreate,
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new Big Five role profile."""
    try:
        profile = await bf_repo.create_role_profile(data.model_dump())
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created Big Five role profile: {profile.name}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Big Five role profile: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/big-five/role-profiles/{profile_id}", response_model=BigFiveRoleProfileResponse)
async def update_big_five_role_profile(
    profile_id: uuid.UUID,
    data: BigFiveRoleProfileUpdate,
    bf_repo: BigFiveRepository = Depends(get_big_five_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a Big Five role profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        profile = await bf_repo.update_role_profile(profile_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Role profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Big Five role profile: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/technical/questions", response_model=list[TechnicalQuestionResponse])
async def list_technical_questions(
    area: str | None = Query(None),
    difficulty: str | None = Query(None),
    question_type: str | None = Query(None),
    tag: str | None = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List technical assessment questions."""
    try:
        questions = await tt_repo.list_questions()
        if area:
            questions = [q for q in questions if q.area == area]
        if difficulty:
            questions = [q for q in questions if q.difficulty == difficulty]
        if question_type:
            questions = [q for q in questions if q.question_type == question_type]
        if tag:
            questions = [q for q in questions if tag in (q.tags or [])]
        if not include_inactive:
            questions = [q for q in questions if q.is_active]
        return questions[skip: skip + limit]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing technical questions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/technical/questions", response_model=TechnicalQuestionResponse)
async def create_technical_question(
    data: TechnicalQuestionCreate,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new technical question."""
    try:
        question = await tt_repo.create_question(data.model_dump())
        logger.info(f"Created technical question: {question.title}")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating technical question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/technical/questions/{question_id}", response_model=TechnicalQuestionResponse)
async def update_technical_question(
    question_id: uuid.UUID,
    data: TechnicalQuestionUpdate,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
    # Onda 4.2c-P0-9 (2026-05-23): role gate — pool global, so staff WeDOTalent.
    _staff: User = Depends(require_wedotalent_admin_role),
    company_id: str = Depends(require_company_id),
):
    """Update a technical question (global pool, staff-only)."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        question = await tt_repo.update_question(question_id, update_data)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating technical question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/technical/questions/{question_id}", response_model=None)
async def delete_technical_question(
    question_id: uuid.UUID,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
    # Onda 4.2c-P0-9 (2026-05-23): role gate — pool global, so staff WeDOTalent.
    _staff: User = Depends(require_wedotalent_admin_role),
    company_id: str = Depends(require_company_id),
):
    """Soft delete a technical question (global pool, staff-only)."""
    try:
        deleted = await tt_repo.delete_question(question_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Question not found")
        return {"success": True, "message": "Question deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting technical question: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/technical/templates", response_model=list[TechnicalTestTemplateResponse])
async def list_technical_templates(
    company_id: uuid.UUID | None = Query(None),
    area: str | None = Query(None),
    role_type: str | None = Query(None),
    include_public: bool = Query(True),
    include_inactive: bool = Query(False),
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List technical test templates."""
    try:
        if not company_id:
            return []
        templates = await tt_repo.list_templates(company_id)
        if area:
            templates = [t for t in templates if t.area == area]
        if role_type:
            templates = [t for t in templates if t.role_type == role_type]
        if not include_inactive:
            templates = [t for t in templates if t.is_active]
        return templates
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing technical templates: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/technical/templates", response_model=TechnicalTestTemplateResponse)
async def create_technical_template(
    data: TechnicalTestTemplateCreate,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new technical test template."""
    try:
        template = await tt_repo.create_template(data.model_dump())
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created technical template: {template.name}")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating technical template: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/technical/templates/{template_id}", response_model=TechnicalTestTemplateResponse)
async def update_technical_template(
    template_id: uuid.UUID,
    data: TechnicalTestTemplateUpdate,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a technical test template."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        template = await tt_repo.update_template(template_id, update_data)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating technical template: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/technical/templates/{template_id}", response_model=None)
async def delete_technical_template(
    template_id: uuid.UUID,
    tt_repo: TechnicalTestRepository = Depends(get_technical_test_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Soft delete a technical test template."""
    try:
        deleted = await tt_repo.delete_template(template_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"success": True, "message": "Template deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting technical template: {e}")
        raise LIAError(message="Erro interno do servidor")


