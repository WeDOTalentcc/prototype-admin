"""
Candidate Lists API endpoints - manage custom collections of candidates.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.domains.candidate_lists.dependencies import get_candidate_list_repo
from app.domains.candidate_lists.repositories.candidate_list_repository import (
    CandidateListRepository,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter()


class CandidateListCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class CandidateListUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class AddCandidatesRequest(WeDoBaseModel):
    candidate_ids: list[str]
    notes: str | None = None


class RemoveCandidatesRequest(WeDoBaseModel):
    candidate_ids: list[str]


class AssignJobsRequest(WeDoBaseModel):
    job_vacancy_ids: list[str]
    candidate_ids: list[str] | None = None


@router.get("", response_model=None)
async def list_candidate_lists(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    List all candidate lists for the company.
    """
    try:
        company_id = get_user_company_id(current_user)
        total, lists = await repo.list_for_company(
            company_id=company_id, skip=skip, limit=limit, search=search
        )

        items = []
        for lst in lists:
            member_count = await repo.count_members(lst.id)
            items.append({
                "id": str(lst.id),
                "name": lst.name,
                "description": lst.description,
                "color": lst.color,
                "created_by": lst.created_by,
                "created_at": lst.created_at.isoformat() if lst.created_at else None,
                "updated_at": lst.updated_at.isoformat() if lst.updated_at else None,
                "candidate_count": member_count,
            })

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing candidate lists: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=None)
async def create_candidate_list(
    data: CandidateListCreate,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Create a new candidate list.
    """
    try:
        company_id = get_user_company_id(current_user)
        new_list = await repo.create_list(
            company_id=company_id,
            name=data.name,
            description=data.description,
            color=data.color,
            created_by=str(current_user.id),
        )

        return {
            "id": str(new_list.id),
            "name": new_list.name,
            "description": new_list.description,
            "color": new_list.color,
            "created_by": new_list.created_by,
            "created_at": new_list.created_at.isoformat() if new_list.created_at else None,
            "updated_at": new_list.updated_at.isoformat() if new_list.updated_at else None,
            "candidate_count": 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate list: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{list_id}", response_model=None)
async def get_candidate_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    skip: int = 0,
    limit: int = 50,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Get a specific candidate list with its members.
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        members = await repo.list_members(uuid.UUID(list_id), skip=skip, limit=limit)
        total_members = await repo.count_members(uuid.UUID(list_id))

        candidates = []
        for member, candidate in members:
            candidates.append({
                "member_id": str(member.id),
                "added_at": member.added_at.isoformat() if member.added_at else None,
                "added_by": member.added_by,
                "notes": member.notes,
                "source": member.source,
                "candidate": {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "linkedin_url": candidate.linkedin_url,
                    "current_title": candidate.current_title,
                    "current_company": candidate.current_company,
                    "seniority_level": candidate.seniority_level,
                    "years_of_experience": candidate.years_of_experience,
                    "location_city": candidate.location_city,
                    "location_state": candidate.location_state,
                    "location_country": candidate.location_country,
                    "technical_skills": candidate.technical_skills or [],
                    "lia_score": candidate.lia_score,
                    "status": candidate.status,
                    "source": candidate.source,
                    "avatar_url": candidate.avatar_url,
                },
            })

        return {
            "id": str(lst.id),
            "name": lst.name,
            "description": lst.description,
            "color": lst.color,
            "created_by": lst.created_by,
            "created_at": lst.created_at.isoformat() if lst.created_at else None,
            "updated_at": lst.updated_at.isoformat() if lst.updated_at else None,
            "candidate_count": total_members,
            "candidates": {
                "total": total_members,
                "skip": skip,
                "limit": limit,
                "items": candidates,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{list_id}", response_model=None)
async def update_candidate_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: CandidateListUpdate,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Update a candidate list (rename, description, color).
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        lst = await repo.update_list(
            lst, name=data.name, description=data.description, color=data.color
        )

        member_count = await repo.count_members(lst.id)

        return {
            "id": str(lst.id),
            "name": lst.name,
            "description": lst.description,
            "color": lst.color,
            "created_by": lst.created_by,
            "created_at": lst.created_at.isoformat() if lst.created_at else None,
            "updated_at": lst.updated_at.isoformat() if lst.updated_at else None,
            "candidate_count": member_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate list: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{list_id}", response_model=None)
async def delete_candidate_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Delete a candidate list (soft delete).
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        await repo.soft_delete_list(lst)

        return {"success": True, "message": "Lista excluída com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate list: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{list_id}/candidates", response_model=None)
async def add_candidates_to_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: AddCandidatesRequest,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Add one or more candidates to a list.
    Duplicates are silently ignored.
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        added_count = 0
        already_exists = 0
        errors = []

        # Parse UUIDs up-front — collect format errors individually
        candidate_uuids = []
        for candidate_id in data.candidate_ids:
            try:
                candidate_uuids.append(uuid.UUID(candidate_id))
            except (ValueError, AttributeError) as e:
                errors.append({"candidate_id": candidate_id, "error": f"ID inválido: {e}"})

        if candidate_uuids:
            # 1 query: fetch all candidates that exist
            found_ids = await repo.find_existing_candidate_ids(candidate_uuids)

            # Report missing candidates
            for uid in candidate_uuids:
                if uid not in found_ids:
                    errors.append({"candidate_id": str(uid), "error": "Candidato não encontrado"})

            # 1 query: fetch already-existing members
            existing_ids = await repo.find_existing_member_ids(uuid.UUID(list_id), candidate_uuids)
            already_exists = len(existing_ids)

            # Bulk insert new members only
            to_add = [uid for uid in found_ids if uid not in existing_ids]
            if to_add:
                added_count = await repo.bulk_add_members(
                    list_id=uuid.UUID(list_id),
                    candidate_uuids=to_add,
                    added_by=str(current_user.id),
                    notes=data.notes,
                    source="manual",
                )

        await repo.touch_list(lst)

        member_count = await repo.count_members(uuid.UUID(list_id))

        return {
            "success": True,
            "added": added_count,
            "already_exists": already_exists,
            "errors": errors,
            "total_in_list": member_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding candidates to list: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{list_id}/candidates", response_model=None)
async def remove_candidates_from_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: RemoveCandidatesRequest,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Remove one or more candidates from a list.
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        # Parse UUIDs up-front — skip malformed ones silently (remove is best-effort)
        candidate_uuids = []
        for candidate_id in data.candidate_ids:
            try:
                candidate_uuids.append(uuid.UUID(candidate_id))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid candidate_id in remove request: {candidate_id} — {e}")

        removed_count = await repo.bulk_remove_members(uuid.UUID(list_id), candidate_uuids)

        await repo.touch_list(lst)

        member_count = await repo.count_members(uuid.UUID(list_id))

        return {
            "success": True,
            "removed": removed_count,
            "total_in_list": member_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing candidates from list: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{list_id}/assign-jobs", response_model=None)
async def assign_list_to_jobs(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: AssignJobsRequest,
    repo: CandidateListRepository = Depends(get_candidate_list_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Add candidates from a list to one or more job vacancies.
    Can specify candidate_ids to add only specific candidates, or add all if not specified.
    """
    try:
        company_id = get_user_company_id(current_user)
        lst = await repo.get_list(uuid.UUID(list_id), company_id)

        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")

        candidate_ids = (
            [uuid.UUID(c) for c in data.candidate_ids] if data.candidate_ids else None
        )
        members = await repo.get_members_for_candidates(uuid.UUID(list_id), candidate_ids)

        if not members:
            return {
                "success": True,
                "assigned": 0,
                "already_in_job": 0,
                "message": "Nenhum candidato na lista para adicionar",
            }

        assigned_count = 0
        already_in_job = 0

        for job_id in data.job_vacancy_ids:
            for member in members:
                try:
                    existing = await repo.find_vacancy_candidate(
                        uuid.UUID(job_id), member.candidate_id
                    )

                    if existing:
                        already_in_job += 1
                        continue

                    await repo.create_vacancy_candidate(
                        company_id=company_id,
                        job_vacancy_id=uuid.UUID(job_id),
                        candidate_id=member.candidate_id,
                    )
                    assigned_count += 1

                except Exception as e:
                    logger.warning(f"Error assigning candidate to job {job_id}: {e}")

        await repo.commit()

        return {
            "success": True,
            "assigned": assigned_count,
            "already_in_job": already_in_job,
            "jobs_count": len(data.job_vacancy_ids),
            "candidates_count": len(members),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning list to jobs: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
