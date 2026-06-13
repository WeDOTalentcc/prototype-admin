"""
Metadata endpoints: viewed, favorites, hidden, and screening-decision.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ._shared import (
    AuditService,
    CandidateFavorite,
    CandidateFavoritesRepository,
    CandidateHidden,
    CandidateHiddenRepository,
    CandidateRepository,
    ScreeningDecisionRequest,
    VacancyCandidateRepository,
    ActivityService,
    check_rejection_reason,
    get_activity_service,
    get_audit_service,
    get_candidate_favorites_repo,
    get_candidate_hidden_repo,
    get_candidate_repo,
    get_current_user_or_demo,
    get_vacancy_candidate_repo,
    logger,
    User,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

router = APIRouter()


# ---------------------------------------------------------------------------
# Viewed candidates
# ---------------------------------------------------------------------------

class ViewedCandidateCreate(WeDoBaseModel):
    source: str | None = None


class ViewedCandidateResponse(BaseModel):
    id: str
    candidate_id: str
    user_id: str
    viewed_at: str
    source: str | None = None


@router.post("/{candidate_id}/viewed", response_model=None)
async def mark_candidate_viewed(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: ViewedCandidateCreate = None,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Mark a candidate as viewed by the current user."""
    try:
        user_id = "default_user"
        source = body.source if body else None
        viewed, created = await candidate_repo.upsert_viewed(
            candidate_id=candidate_id, user_id=user_id, source=source,
        )
        base = {
            "id": str(viewed.id),
            "candidate_id": viewed.candidate_id,
            "user_id": viewed.user_id,
            "viewed_at": viewed.viewed_at.isoformat() if viewed.viewed_at else None,
            "source": viewed.source,
        }
        if not created:
            base["message"] = "Viewed timestamp updated"
        else:
            base["message"] = "Candidate marked as viewed"
        return base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking candidate as viewed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/viewed/list", response_model=None)
async def list_viewed_candidates(
    skip: int = 0,
    limit: int = 100,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all candidates viewed by the current user."""
    try:
        user_id = "default_user"
        viewed_list, total = await candidate_repo.list_viewed(user_id=user_id, skip=skip, limit=limit)
        return {
            "total": total, "skip": skip, "limit": limit,
            "items": [
                {
                    "id": str(v.id),
                    "candidate_id": v.candidate_id,
                    "user_id": v.user_id,
                    "viewed_at": v.viewed_at.isoformat() if v.viewed_at else None,
                    "source": v.source,
                }
                for v in viewed_list
            ],
            "candidate_ids": [v.candidate_id for v in viewed_list],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing viewed candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/viewed", response_model=None)
async def unmark_candidate_viewed(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Remove viewed status from a candidate for the current user."""
    try:
        user_id = "default_user"
        deleted = await candidate_repo.delete_viewed(candidate_id=candidate_id, user_id=user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Viewed record not found")
        return {"message": "Viewed status removed", "candidate_id": candidate_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unmarking candidate as viewed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

class FavoriteCreate(WeDoBaseModel):
    note: str | None = None
    is_pinned: bool = False
    source: str | None = None


class FavoriteUpdate(WeDoBaseModel):
    note: str | None = None
    is_pinned: bool | None = None


@router.post("/{candidate_id}/favorite", response_model=None)
async def toggle_favorite(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: FavoriteCreate = None,
    current_user: User = Depends(get_current_user_or_demo),
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Toggle favorite status for a candidate."""
    try:
        user_id = str(current_user.id)
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
        company_id = current_user.company_id
        existing = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)
        if existing:
            await favorites_repo.remove(existing)
            return {
                "action": "removed", "candidate_id": candidate_id,
                "is_favorite": False, "message": "Candidate removed from favorites",
            }
        else:
            favorite = CandidateFavorite(
                id=uuid.uuid4(), candidate_id=candidate_id, user_id=user_id,
                company_id=company_id,
                note=body.note if body else None,
                is_pinned=body.is_pinned if body else False,
                source=body.source if body else None,
            )
            favorite = await favorites_repo.add(favorite)
            return {
                "action": "added",
                "id": str(favorite.id),
                "candidate_id": favorite.candidate_id,
                "user_id": favorite.user_id,
                "note": favorite.note,
                "is_pinned": favorite.is_pinned,
                "is_favorite": True,
                "created_at": favorite.created_at.isoformat() if favorite.created_at else None,
                "message": "Candidate added to favorites",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{candidate_id}/favorite", response_model=None)
async def update_favorite(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: FavoriteUpdate,
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update favorite note or pinned status."""
    try:
        user_id = "default_user"
        favorite = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")
        if body.note is not None:
            favorite.note = body.note
        if body.is_pinned is not None:
            favorite.is_pinned = body.is_pinned
        favorite = await favorites_repo.update(favorite)
        return {
            "id": str(favorite.id),
            "candidate_id": favorite.candidate_id,
            "note": favorite.note,
            "is_pinned": favorite.is_pinned,
            "updated_at": favorite.updated_at.isoformat() if favorite.updated_at else None,
            "message": "Favorite updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites/list", response_model=None)
async def list_favorites(
    skip: int = 0,
    limit: int = 100,
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all favorited candidates for the current user."""
    try:
        user_id = "default_user"
        favorites_list, total = await favorites_repo.list_for_user(user_id=user_id, skip=skip, limit=limit)
        return {
            "total": total, "skip": skip, "limit": limit,
            "items": [
                {
                    "id": str(f.id), "candidate_id": f.candidate_id, "user_id": f.user_id,
                    "note": f.note, "is_pinned": f.is_pinned, "source": f.source,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in favorites_list
            ],
            "candidate_ids": [f.candidate_id for f in favorites_list],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing favorites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/favorite", response_model=None)
async def remove_favorite(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Remove a candidate from favorites."""
    try:
        user_id = "default_user"
        favorite = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")
        await favorites_repo.remove(favorite)
        return {"message": "Removed from favorites", "candidate_id": candidate_id, "is_favorite": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Hidden candidates
# ---------------------------------------------------------------------------

class HiddenCreate(WeDoBaseModel):
    reason: str | None = None
    source: str | None = None


@router.post("/{candidate_id}/hide", response_model=None)
async def toggle_hidden(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: HiddenCreate = None,
    current_user: User = Depends(get_current_user_or_demo),
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Toggle hidden status for a candidate."""
    try:
        user_id = str(current_user.id)
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
        company_id = current_user.company_id
        existing = await hidden_repo.get(candidate_id=candidate_id, user_id=user_id)
        if existing:
            await hidden_repo.remove(existing)
            return {
                "action": "shown", "candidate_id": candidate_id,
                "is_hidden": False, "message": "Candidate is now visible",
            }
        else:
            hidden = CandidateHidden(
                id=uuid.uuid4(), candidate_id=candidate_id, user_id=user_id,
                company_id=company_id,
                reason=body.reason if body else None,
                source=body.source if body else None,
            )
            hidden = await hidden_repo.add(hidden)
            return {
                "action": "hidden",
                "id": str(hidden.id),
                "candidate_id": hidden.candidate_id,
                "user_id": hidden.user_id,
                "reason": hidden.reason,
                "is_hidden": True,
                "created_at": hidden.created_at.isoformat() if hidden.created_at else None,
                "message": "Candidate hidden",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling hidden: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hidden/list", response_model=None)
async def list_hidden(
    skip: int = 0,
    limit: int = 100,
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all hidden candidates for the current user."""
    try:
        user_id = "default_user"
        hidden_list, total = await hidden_repo.list_for_user(user_id=user_id, skip=skip, limit=limit)
        return {
            "total": total, "skip": skip, "limit": limit,
            "items": [
                {
                    "id": str(h.id), "candidate_id": h.candidate_id, "user_id": h.user_id,
                    "reason": h.reason, "source": h.source,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in hidden_list
            ],
            "candidate_ids": [h.candidate_id for h in hidden_list],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing hidden candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/hide", response_model=None)
async def remove_hidden(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Remove a candidate from the hidden list (make visible)."""
    try:
        user_id = "default_user"
        hidden = await hidden_repo.get(candidate_id=candidate_id, user_id=user_id)
        if not hidden:
            raise HTTPException(status_code=404, detail="Hidden record not found")
        await hidden_repo.remove(hidden)
        return {"message": "Candidate is now visible", "candidate_id": candidate_id, "is_hidden": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing hidden status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Screening decision
# ---------------------------------------------------------------------------

@router.post("/{candidate_id}/screening-decision", response_model=None)
async def screening_decision(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: ScreeningDecisionRequest,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vc_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Record screening decision for a candidate (approve or reject)."""
    try:
        if request.decision not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

        if request.decision == "rejected" and not request.reviewer_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "human_review_required",
                    "message": (
                        "Rejeição na triagem requer identificação do revisor humano (reviewer_id). "
                        "Rejeições automatizadas sem revisão humana não são permitidas."
                    ),
                    "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                },
            )

        if request.decision == "rejected" and request.reason:
            fg_rejection = check_rejection_reason(reason=request.reason, company_id=request.job_id or "")
            if fg_rejection.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "message": fg_rejection.blocked_result.educational_message if fg_rejection.blocked_result else "Viés detectado no motivo da rejeição.",
                        "category": fg_rejection.blocked_result.category if fg_rejection.blocked_result else None,
                        "compliance": ["Lei 9.029/95", "CLT Art. 373-A"],
                    },
                )

        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if request.decision == "approved":
            has_valid_email = candidate.email and "@" in candidate.email
            has_valid_phone = (
                candidate.phone
                and len(
                    candidate.phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                ) >= 8
            )
            if not has_valid_email and not has_valid_phone:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "missing_contact_info",
                        "message": "Candidato não possui email ou telefone válido. É necessário ter pelo menos um contato para prosseguir com a triagem.",
                        "candidate_name": candidate.name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                    },
                )

        current_stage = None
        vacancy_candidate = None
        if request.job_id:
            vacancy_candidate = await vc_repo.get_for_candidate_and_job(
                candidate_id=candidate_id, job_vacancy_id=request.job_id,
                company_id=company_id,
            )
        if vacancy_candidate:
            current_stage = vacancy_candidate.stage

        is_awaiting_screening = (
            vacancy_candidate
            and vacancy_candidate.status == "awaiting_screening"
            and request.decision == "approved"
        )
        if is_awaiting_screening:
            try:
                from app.domains.automation.services.automation_handlers import handle_recruiter_override_approve
                override_result = await handle_recruiter_override_approve(
                    db=candidate_repo.db,
                    candidate_id=str(candidate_id),
                    vacancy_id=str(vacancy_candidate.vacancy_id),
                    company_id=vacancy_candidate.company_id,
                )
                return {
                    "success": True,
                    "message": f"Candidato {candidate.name} priorizado da fila de espera",
                    "candidate_id": str(candidate_id),
                    "candidate_name": candidate.name,
                    "decision": "approved",
                    "new_stage": "screening",
                    "new_status": "screening",
                    "override": True,
                    "override_result": override_result,
                }
            except Exception as override_error:
                logger.error(f"Override approve failed: {override_error}", exc_info=True)

        early_stages = ["Novo", "Pipeline", "Funil", "Aplicado", "novo", "pipeline", "funil", "aplicado", "new", "applied"]
        screening_stages = ["Triagem", "triagem", "screening", "Screening"]

        if request.decision == "approved":
            if current_stage and current_stage.lower() in [s.lower() for s in early_stages]:
                new_stage = "Triagem"
                activity_description = "Candidato aprovado e movido para Triagem"
            elif current_stage and current_stage.lower() in [s.lower() for s in screening_stages]:
                new_stage = "Entrevista"
                activity_description = "Candidato aprovado na triagem e movido para Entrevista"
            else:
                new_stage = "Triagem"
                activity_description = "Candidato aprovado e movido para Triagem"
            new_status = "approved_screening"
            activity_type = "screening_approved"
            activity_title = f"Candidato Aprovado - {candidate.name}"
        else:
            new_stage = "Reprovado Triagem"
            new_status = "rejected_screening"
            activity_type = "screening_rejected"
            activity_title = f"Triagem Reprovada - {candidate.name}"
            activity_description = "Candidato reprovado na triagem"
            if request.reason:
                activity_description += f". Motivo: {request.reason}"

        if vacancy_candidate:
            vacancy_candidate.stage = new_stage
            vacancy_candidate.status = new_status
            # Task #1306: also persist the structural stage link so the SLA
            # detector can join by id instead of fragile name matching.
            from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
            vacancy_candidate.recruitment_stage_id = await resolve_recruitment_stage_id(
                vc_repo.db, str(vacancy_candidate.company_id), new_stage
            )
            vacancy_candidate.updated_at = datetime.utcnow()
            if request.reason:
                vacancy_candidate.notes = (vacancy_candidate.notes or "") + f"\n[Triagem] {request.reason}"
            if request.decision == "rejected":
                vacancy_candidate.rejected_by_human = True
                vacancy_candidate.human_reviewer_id = request.reviewer_id
            await vc_repo.update(vacancy_candidate)

            # Agent Studio Fase 2.5 — Onda C1.3: emite stage_changed no
            # platform.events (decisao de triagem move o candidato de stage).
            # REGRA 4: fail-soft mas LOUD. Multi-tenancy: company_id de
            # vacancy_candidate.company_id (row do tenant), NUNCA do request.
            if current_stage != new_stage:
                try:
                    from lia_events.schemas import StageChangedEvent
                    from app.shared.messaging.events_outbox_service import get_events_outbox_service
                    _evt_company_id = str(
                        getattr(vacancy_candidate, "company_id", "") or company_id
                    )
                    _evt = StageChangedEvent(
                        company_id=_evt_company_id,
                        payload={
                            "candidate_id": str(candidate_id),
                            "vacancy_id": str(vacancy_candidate.vacancy_id),
                            "from_stage": current_stage or "unknown",
                            "to_stage": new_stage,
                        },
                        source_api="lia-agent-system",
                    )
                    await get_events_outbox_service().publish_via_outbox(_evt, candidate_repo.db)
                except Exception as _evt_err:  # noqa: BLE001
                    logger.error(
                        "[C1.3] publish stage_changed (screening) failed "
                        "(decisao prossegue): %s",
                        _evt_err,
                        exc_info=True,
                    )

        candidate.status = new_status
        await candidate_repo.update(candidate)

        try:
            await activity_svc.create_activity(
                activity_type=activity_type,
                title=activity_title,
                description=activity_description,
                summary=activity_description,
                actor_id="system",
                actor_name="LIA",
                actor_type="ai",
                target_id=str(candidate_id),
                target_name=candidate.name,
                target_type="candidate",
                extra_data={
                    "decision": request.decision, "job_id": request.job_id,
                    "reason": request.reason, "new_stage": new_stage,
                    "previous_status": candidate.status,
                },
                priority="normal",
                category="screening",
                action_url=f"/funil-de-talentos/candidato/{candidate_id}",
                action_label="Ver Candidato",
            )
        except Exception as activity_error:
            logger.warning(f"Failed to create activity: {activity_error}")

        # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
        logger.info(f"Screening decision recorded: {candidate.id} -> {request.decision}")

        try:
            _vc_company = getattr(vacancy_candidate, "company_id", None) if vacancy_candidate else None
            _vc_score = getattr(vacancy_candidate, "wsi_score", None) if vacancy_candidate else None
            _vc_ranking = getattr(vacancy_candidate, "ranking_position", None) if vacancy_candidate else None
            await audit_svc.log_decision(
                company_id=str(_vc_company) if _vc_company else None,
                agent_name="screening_module",
                decision_type="approved" if request.decision == "approved" else "rejected",
                action="screening_decision",
                decision=request.decision,
                reasoning=[
                    f"Screening decision: {request.decision}",
                    f"Stage transition: {new_stage}",
                    f"WSI score: {_vc_score}" if _vc_score else "WSI score: N/A",
                    f"Ranking: {_vc_ranking}" if _vc_ranking else "Ranking: N/A",
                    "Recruiter rationale: provided" if getattr(request, "reason", None) else "Recruiter rationale: none",
                ],
                criteria_used=["screening_evaluation", "recruiter_review", "wsi_score", "ranking_position"],
                candidate_id=str(candidate_id),
                job_vacancy_id=request.job_id,
                score=float(_vc_score) if _vc_score else None,
                human_review_required=request.decision == "rejected",
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for screening_decision: {audit_err}")

        if request.decision == "rejected" and vacancy_candidate and request.job_id:
            try:
                from app.domains.automation.services.stage_automation_engine import (
                    AutomationEvent,
                    StageAutomationEngine,
                    TriggerType,
                )
                engine = StageAutomationEngine()
                slot_event = AutomationEvent(
                    trigger_type=TriggerType.SLOT_OPENED,
                    candidate_id=str(candidate_id),
                    vacancy_id=str(request.job_id),
                    company_id=vacancy_candidate.company_id,
                    payload={"slots_available": 1, "reason": "candidate_rejected"},
                    source="screening_decision",
                )
                await engine.process_event(slot_event, candidate_repo.db, auto_execute=True)
            except Exception as slot_error:
                logger.warning(f"Failed to process screening queue after rejection: {slot_error}")

        return {
            "success": True,
            "message": f"Candidate {request.decision} successfully",
            "candidate_id": str(candidate_id),
            "candidate_name": candidate.name,
            "decision": request.decision,
            "new_stage": new_stage,
            "new_status": new_status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording screening decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
