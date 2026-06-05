"""
API endpoints for LIA Opinions (Pareceres).
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.opinions.dependencies import get_opinions_repo
from app.domains.opinions.repositories.opinions_repository import OpinionsRepository
from app.models.lia_opinion import LiaOpinion
from app.schemas.lia_opinion import (
    CandidateOpinionsSummary,
    LiaOpinionCompact,
    LiaOpinionCreate,
    LiaOpinionFull,
    LiaOpinionListResponse,
    LiaOpinionUpdate,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opinions", tags=["LIA Opinions"])


class ParecerGenerateRequest(WeDoBaseModel):
    """Body do POST /opinions/candidate/{id}/parecer. company_id vem do JWT, nunca aqui."""
    job_vacancy_id: str | None = None


class CriteriaMatchRequest(WeDoBaseModel):
    """Body do POST /opinions/candidate/{id}/criteria-match (matriz da busca, on-the-fly)."""
    search_criteria: dict = {}


def _build_opinion_full(op: LiaOpinion, job_title: str | None) -> LiaOpinionFull:
    return LiaOpinionFull(
        id=op.id,
        candidate_id=op.candidate_id,
        opinion_type=op.opinion_type,
        source=op.source,
        job_vacancy_id=op.job_vacancy_id,
        job_vacancy_title=job_title,
        wsi_screening_id=op.wsi_screening_id,
        score=op.score,
        wsi_score=op.wsi_score,
        recommendation=op.recommendation,
        summary=op.summary,
        archetype=op.archetype,
        archetype_match_score=op.archetype_match_score,
        score_breakdown=op.score_breakdown or {},
        technical_analysis=op.technical_analysis or {},
        behavioral_analysis=op.behavioral_analysis or {},
        cultural_fit=op.cultural_fit or {},
        strengths=op.strengths or [],
        concerns=op.concerns or [],
        gaps=op.gaps or [],
        matched_skills=op.matched_skills or [],
        missing_skills=op.missing_skills or [],
        next_steps=op.next_steps,
        recruiter_notes=op.recruiter_notes,
        recruiter_override=op.recruiter_override,
        recruiter_override_reason=op.recruiter_override_reason,
        recruiter_override_by=op.recruiter_override_by,
        recruiter_override_at=op.recruiter_override_at,
        is_current=op.is_current,
        version=op.version,
        created_at=op.created_at,
        updated_at=op.updated_at,
        created_by=op.created_by,
    )


@router.get("/candidate/{candidate_id}/summary", response_model=CandidateOpinionsSummary)
async def get_candidate_opinions_summary(
    candidate_id: UUID,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get summary of all opinions for a candidate (for preview display)."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id

    opinions = await repo.get_current_by_candidate(candidate_id, company_id)

    current_general = None
    vacancy_opinions = []
    has_pending = False

    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_title = await repo.get_job_title(op.job_vacancy_id)

        compact = LiaOpinionCompact(
            id=op.id,
            opinion_type=op.opinion_type,
            source=op.source,
            score=op.score,
            wsi_score=op.wsi_score,
            recommendation=op.recommendation,
            summary=op.summary,
            archetype=op.archetype,
            job_vacancy_id=op.job_vacancy_id,
            job_vacancy_title=job_title,
            created_at=op.created_at,
            is_current=op.is_current,
        )

        if op.opinion_type == "general" and current_general is None:
            current_general = compact
        elif op.job_vacancy_id:
            vacancy_opinions.append(compact)

        if op.recommendation == "pending_review":
            has_pending = True

    return CandidateOpinionsSummary(
        candidate_id=candidate_id,
        total_opinions=len(opinions),
        current_general_opinion=current_general,
        vacancy_opinions=vacancy_opinions,
        has_pending_review=has_pending,
    )


@router.get("/candidate/{candidate_id}/history", response_model=list[LiaOpinionFull])
async def get_candidate_opinions_history(
    candidate_id: UUID,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get full history of all opinions for a candidate (including non-current versions)."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id

    opinions = await repo.get_history_by_candidate(candidate_id, company_id)

    items = []
    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_title = await repo.get_job_title(op.job_vacancy_id)
        items.append(_build_opinion_full(op, job_title))

    return items


@router.get("/candidate/{candidate_id}", response_model=LiaOpinionListResponse)
async def list_candidate_opinions(
    candidate_id: UUID,
    opinion_type: str | None = Query(None, description="Filter by type: general or wsi"),
    job_vacancy_id: UUID | None = Query(None, description="Filter by vacancy"),
    include_history: bool = Query(False, description="Include non-current versions"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all opinions for a candidate with optional filters."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id

    opinions, total = await repo.list_with_filters(
        candidate_id=candidate_id,
        company_id=company_id,
        opinion_type=opinion_type,
        job_vacancy_id=job_vacancy_id,
        include_history=include_history,
        page=page,
        page_size=page_size,
    )

    items = []
    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_title = await repo.get_job_title(op.job_vacancy_id)
        items.append(_build_opinion_full(op, job_title))

    return LiaOpinionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{opinion_id}", response_model=LiaOpinionFull)
async def get_opinion(
    opinion_id: UUID,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific opinion by ID."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id

    opinion = await repo.get_by_id(opinion_id, company_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    job_title = None
    if opinion.job_vacancy_id:
        job_title = await repo.get_job_title(opinion.job_vacancy_id)

    return _build_opinion_full(opinion, job_title)


@router.post("/", response_model=LiaOpinionFull)
async def create_opinion(
    data: LiaOpinionCreate,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new LIA opinion."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id
    user_id = str(current_user.id)

    if data.opinion_type.value == "wsi" and not data.job_vacancy_id:
        raise HTTPException(
            status_code=400,
            detail="WSI opinions require a job_vacancy_id",
        )

    new_version = 1

    if data.job_vacancy_id:
        max_version = await repo.get_max_version_for_vacancy(
            candidate_id=data.candidate_id,
            job_vacancy_id=data.job_vacancy_id,
            opinion_type=data.opinion_type.value,
            company_id=company_id,
        )
        if max_version:
            new_version = max_version + 1

        await repo.mark_vacancy_opinions_non_current(
            candidate_id=data.candidate_id,
            job_vacancy_id=data.job_vacancy_id,
            opinion_type=data.opinion_type.value,
            company_id=company_id,
        )
    else:
        max_version = await repo.get_max_version_general(
            candidate_id=data.candidate_id,
            company_id=company_id,
        )
        if max_version:
            new_version = max_version + 1

        await repo.mark_general_opinions_non_current(
            candidate_id=data.candidate_id,
            company_id=company_id,
        )

    opinion = LiaOpinion(
        candidate_id=data.candidate_id,
        opinion_type=data.opinion_type.value,
        source=data.source.value,
        job_vacancy_id=data.job_vacancy_id,
        wsi_screening_id=data.wsi_screening_id,
        score=data.score,
        wsi_score=data.wsi_score,
        recommendation=data.recommendation.value if data.recommendation else None,
        summary=data.summary,
        archetype=data.archetype,
        archetype_match_score=data.archetype_match_score,
        score_breakdown=data.score_breakdown,
        technical_analysis=data.technical_analysis,
        behavioral_analysis=data.behavioral_analysis,
        cultural_fit=data.cultural_fit,
        strengths=data.strengths,
        concerns=data.concerns,
        gaps=data.gaps,
        matched_skills=data.matched_skills,
        missing_skills=data.missing_skills,
        next_steps=data.next_steps,
        recruiter_notes=data.recruiter_notes,
        company_id=company_id,
        created_by=user_id,
        is_current=True,
        version=new_version,
    )

    opinion = await repo.create(opinion)

    logger.info(f"Created opinion {opinion.id} for candidate {data.candidate_id}")

    job_title = None
    if opinion.job_vacancy_id:
        job_title = await repo.get_job_title(opinion.job_vacancy_id)

    return _build_opinion_full(opinion, job_title)


@router.patch("/{opinion_id}", response_model=LiaOpinionFull)
async def update_opinion(
    opinion_id: UUID,
    data: LiaOpinionUpdate,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a LIA opinion (e.g., recruiter notes or override)."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id
    user_id = str(current_user.id)

    opinion = await repo.get_by_id(opinion_id, company_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    update_data = data.model_dump(exclude_unset=True)

    if "recruiter_override" in update_data and update_data["recruiter_override"]:
        opinion.recruiter_override = (
            update_data["recruiter_override"].value
            if hasattr(update_data["recruiter_override"], "value")
            else update_data["recruiter_override"]
        )
        opinion.recruiter_override_by = user_id
        opinion.recruiter_override_at = datetime.utcnow()
        if "recruiter_override_reason" in update_data:
            opinion.recruiter_override_reason = update_data["recruiter_override_reason"]

    for field, value in update_data.items():
        if field not in ["recruiter_override", "recruiter_override_reason"]:
            if hasattr(value, "value"):
                setattr(opinion, field, value.value)
            else:
                setattr(opinion, field, value)

    opinion = await repo.update(opinion)

    logger.info(f"Updated opinion {opinion_id}")

    job_title = None
    if opinion.job_vacancy_id:
        job_title = await repo.get_job_title(opinion.job_vacancy_id)

    return _build_opinion_full(opinion, job_title)


@router.delete("/{opinion_id}", response_model=None)
async def delete_opinion(
    opinion_id: UUID,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a LIA opinion (soft delete by marking as non-current)."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
    company_id = current_user.company_id

    opinion = await repo.get_by_id(opinion_id, company_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    await repo.soft_delete(opinion)

    logger.info(f"Soft-deleted opinion {opinion_id}")

    return {"message": "Opinion deleted successfully", "id": str(opinion_id)}


@router.post("/candidate/{candidate_id}/parecer", response_model=LiaOpinionFull)
async def generate_candidate_parecer(
    candidate_id: UUID,
    payload: ParecerGenerateRequest,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Gera o parecer job-directed (matriz de qualificacao) e AUTO-SALVA versionado.

    Fail-loud: se a geracao falhar (LLM), responde 502 e NAO persiste conteudo
    degradado (CLAUDE.md REGRA 4). multi-tenancy: company_id do JWT, nunca do payload.
    """
    from app.domains.analytics.services.candidate_report_service import (
        candidate_report_service,
        ParecerGenerationError,
    )

    company_id = current_user.company_id or company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is required but not set")

    try:
        parecer = await candidate_report_service.generate_parecer(
            db=repo.db,
            candidate_id=str(candidate_id),
            job_id=payload.job_vacancy_id,
        )
    except ParecerGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    qm = parecer.get("qualification_matrix") or {}
    sections = parecer.get("sections") or {}
    resumo = sections.get("resumo_executivo") or {}
    pfa = sections.get("pontos_fortes_e_atencao") or {}
    rec_final = sections.get("recomendacao_final") or {}
    rec = parecer.get("recommendation")
    recommendation = (
        rec.get("nivel") if isinstance(rec, dict) else (rec if isinstance(rec, str) else None)
    )
    lia_score = parecer.get("lia_score")
    score = float(lia_score) if isinstance(lia_score, (int, float)) else None
    crits = qm.get("criteria") or []
    matched = [c.get("label") for c in crits if c.get("status") == "met"]
    missing = [c.get("label") for c in crits if c.get("status") == "not_met"]

    opinion_id = await repo.create_parecer_opinion(
        candidate_id=str(candidate_id),
        job_vacancy_id=payload.job_vacancy_id,
        company_id=company_id,
        score=score,
        recommendation=recommendation,
        summary=resumo.get("texto") if isinstance(resumo, dict) else None,
        score_breakdown={
            "qualification_matrix": qm,
            "sections": sections,
            "completeness_score": parecer.get("completeness_score"),
            "recommendation": rec,
            "lia_score": lia_score,
        },
        strengths=pfa.get("pontos_fortes") or [],
        concerns=pfa.get("pontos_atencao") or [],
        gaps=[],
        matched_skills=matched,
        missing_skills=missing,
        next_steps=rec_final.get("proximos_passos") or [],
    )
    await repo.db.commit()

    opinion = await repo.get_by_id(opinion_id=UUID(opinion_id), company_id=company_id)
    if not opinion:
        raise HTTPException(status_code=500, detail="Parecer persisted but not retrievable")
    job_title = (
        await repo.get_job_title(opinion.job_vacancy_id) if opinion.job_vacancy_id else None
    )
    return _build_opinion_full(opinion, job_title)


@router.post("/candidate/{candidate_id}/criteria-match", response_model=None)
async def candidate_criteria_match(
    candidate_id: UUID,
    payload: CriteriaMatchRequest,
    repo: OpinionsRepository = Depends(get_opinions_repo),
    company_id: str = Depends(require_company_id),
):
    """Matriz da BUSCA (lista plana de criterios) avaliada on-the-fly. NAO persiste.

    Explica o Match score comparando o candidato com os filtros da busca.
    multi-tenancy: leitura via tenant db (RLS) + company_id do JWT.
    """
    from app.domains.analytics.services.candidate_report_service import (
        candidate_report_service,
    )
    from app.domains.analytics.services.criteria_derivation import derive_from_search

    candidate = await candidate_report_service._get_candidate(repo.db, str(candidate_id))
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    cand_dict = candidate_report_service._build_candidate_dict(candidate)
    matrix = derive_from_search(payload.search_criteria or {}, cand_dict)
    return matrix.model_dump()
