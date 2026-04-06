"""
Candidate Lists API endpoints - manage custom collections of candidates.
"""
from uuid import UUID
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.models.candidate import Candidate, VacancyCandidate
from app.models.candidate_list import CandidateList, CandidateListMember

logger = logging.getLogger(__name__)

router = APIRouter()


class CandidateListCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class CandidateListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class AddCandidatesRequest(BaseModel):
    candidate_ids: list[str]
    notes: str | None = None


class RemoveCandidatesRequest(BaseModel):
    candidate_ids: list[str]


class AssignJobsRequest(BaseModel):
    job_vacancy_ids: list[str]
    candidate_ids: list[str] | None = None


@router.get("", response_model=None)
async def list_candidate_lists(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List all candidate lists for the company.
    """
    try:
        company_id = get_user_company_id(current_user)
        query = select(CandidateList).where(
            and_(
                CandidateList.company_id == company_id,
                CandidateList.is_active == True
            )
        )
        
        if search:
            query = query.where(CandidateList.name.ilike(f"%{search}%"))
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(CandidateList.updated_at.desc())
        
        result = await db.execute(query)
        lists = result.scalars().all()
        
        items = []
        for lst in lists:
            member_count_result = await db.execute(
                select(func.count()).where(CandidateListMember.list_id == lst.id)
            )
            member_count = member_count_result.scalar() or 0
            
            items.append({
                "id": str(lst.id),
                "name": lst.name,
                "description": lst.description,
                "color": lst.color,
                "created_by": lst.created_by,
                "created_at": lst.created_at.isoformat() if lst.created_at else None,
                "updated_at": lst.updated_at.isoformat() if lst.updated_at else None,
                "candidate_count": member_count
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items
        }
        
    except Exception as e:
        logger.error(f"Error listing candidate lists: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=None)
async def create_candidate_list(
    data: CandidateListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Create a new candidate list.
    """
    try:
        company_id = get_user_company_id(current_user)
        new_list = CandidateList(
            id=uuid.uuid4(),
            company_id=company_id,
            name=data.name,
            description=data.description,
            color=data.color,
            created_by=str(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        db.add(new_list)
        await db.commit()
        await db.refresh(new_list)
        
        return {
            "id": str(new_list.id),
            "name": new_list.name,
            "description": new_list.description,
            "color": new_list.color,
            "created_by": new_list.created_by,
            "created_at": new_list.created_at.isoformat() if new_list.created_at else None,
            "updated_at": new_list.updated_at.isoformat() if new_list.updated_at else None,
            "candidate_count": 0
        }
        
    except Exception as e:
        logger.error(f"Error creating candidate list: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{list_id}", response_model=None)
async def get_candidate_list(
    list_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get a specific candidate list with its members.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")
        
        members_query = (
            select(CandidateListMember, Candidate)
            .join(Candidate, CandidateListMember.candidate_id == Candidate.id)
            .where(CandidateListMember.list_id == uuid.UUID(list_id))
            .offset(skip)
            .limit(limit)
            .order_by(CandidateListMember.added_at.desc())
        )
        
        members_result = await db.execute(members_query)
        members = members_result.all()
        
        total_result = await db.execute(
            select(func.count()).where(CandidateListMember.list_id == uuid.UUID(list_id))
        )
        total_members = total_result.scalar() or 0
        
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
                    "avatar_url": candidate.avatar_url
                }
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
                "items": candidates
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{list_id}", response_model=None)
async def update_candidate_list(
    list_id: str,
    data: CandidateListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update a candidate list (rename, description, color).
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")
        
        if data.name is not None:
            lst.name = data.name
        if data.description is not None:
            lst.description = data.description
        if data.color is not None:
            lst.color = data.color
        
        lst.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(lst)
        
        member_count_result = await db.execute(
            select(func.count()).where(CandidateListMember.list_id == lst.id)
        )
        member_count = member_count_result.scalar() or 0
        
        return {
            "id": str(lst.id),
            "name": lst.name,
            "description": lst.description,
            "color": lst.color,
            "created_by": lst.created_by,
            "created_at": lst.created_at.isoformat() if lst.created_at else None,
            "updated_at": lst.updated_at.isoformat() if lst.updated_at else None,
            "candidate_count": member_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate list: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{list_id}", response_model=None)
async def delete_candidate_list(
    list_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Delete a candidate list (soft delete).
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")
        
        lst.is_active = False
        lst.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Lista excluída com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate list: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{list_id}/candidates", response_model=None)
async def add_candidates_to_list(
    list_id: str,
    data: AddCandidatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Add one or more candidates to a list.
    Duplicates are silently ignored.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
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
            found_result = await db.execute(
                select(Candidate.id).where(Candidate.id.in_(candidate_uuids))
            )
            found_ids = {row[0] for row in found_result.fetchall()}

            # Report missing candidates
            for uid in candidate_uuids:
                if uid not in found_ids:
                    errors.append({"candidate_id": str(uid), "error": "Candidato não encontrado"})

            # 1 query: fetch already-existing members
            existing_result = await db.execute(
                select(CandidateListMember.candidate_id).where(
                    and_(
                        CandidateListMember.list_id == uuid.UUID(list_id),
                        CandidateListMember.candidate_id.in_(candidate_uuids),
                    )
                )
            )
            existing_ids = {row[0] for row in existing_result.fetchall()}
            already_exists = len(existing_ids)

            # Bulk insert new members only
            to_add = [uid for uid in found_ids if uid not in existing_ids]
            if to_add:
                now = datetime.utcnow()
                await db.execute(
                    insert(CandidateListMember).values([
                        {
                            "id": uuid.uuid4(),
                            "list_id": uuid.UUID(list_id),
                            "candidate_id": uid,
                            "added_by": str(current_user.id),
                            "added_at": now,
                            "notes": data.notes,
                            "source": "manual",
                        }
                        for uid in to_add
                    ]).on_conflict_do_nothing()
                )
                added_count = len(to_add)
        
        lst.updated_at = datetime.utcnow()
        await db.commit()
        
        member_count_result = await db.execute(
            select(func.count()).where(CandidateListMember.list_id == uuid.UUID(list_id))
        )
        member_count = member_count_result.scalar() or 0
        
        return {
            "success": True,
            "added": added_count,
            "already_exists": already_exists,
            "errors": errors,
            "total_in_list": member_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding candidates to list: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{list_id}/candidates", response_model=None)
async def remove_candidates_from_list(
    list_id: str,
    data: RemoveCandidatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Remove one or more candidates from a list.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")
        
        removed_count = 0

        # Parse UUIDs up-front — skip malformed ones silently (remove is best-effort)
        candidate_uuids = []
        for candidate_id in data.candidate_ids:
            try:
                candidate_uuids.append(uuid.UUID(candidate_id))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid candidate_id in remove request: {candidate_id} — {e}")

        if candidate_uuids:
            from sqlalchemy import delete as sa_delete
            # 1 query: delete all matching members at once
            delete_result = await db.execute(
                sa_delete(CandidateListMember).where(
                    and_(
                        CandidateListMember.list_id == uuid.UUID(list_id),
                        CandidateListMember.candidate_id.in_(candidate_uuids),
                    )
                )
            )
            removed_count = delete_result.rowcount
        
        lst.updated_at = datetime.utcnow()
        await db.commit()
        
        member_count_result = await db.execute(
            select(func.count()).where(CandidateListMember.list_id == uuid.UUID(list_id))
        )
        member_count = member_count_result.scalar() or 0
        
        return {
            "success": True,
            "removed": removed_count,
            "total_in_list": member_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing candidates from list: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{list_id}/assign-jobs", response_model=None)
async def assign_list_to_jobs(
    list_id: str,
    data: AssignJobsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Add candidates from a list to one or more job vacancies.
    Can specify candidate_ids to add only specific candidates, or add all if not specified.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == uuid.UUID(list_id),
                    CandidateList.company_id == company_id,
                    CandidateList.is_active == True
                )
            )
        )
        lst = result.scalar_one_or_none()
        
        if not lst:
            raise HTTPException(status_code=404, detail="Lista não encontrada")
        
        if data.candidate_ids:
            members_query = (
                select(CandidateListMember)
                .where(
                    and_(
                        CandidateListMember.list_id == uuid.UUID(list_id),
                        CandidateListMember.candidate_id.in_([uuid.UUID(c) for c in data.candidate_ids])
                    )
                )
            )
        else:
            members_query = select(CandidateListMember).where(
                CandidateListMember.list_id == uuid.UUID(list_id)
            )
        
        members_result = await db.execute(members_query)
        members = members_result.scalars().all()
        
        if not members:
            return {
                "success": True,
                "assigned": 0,
                "already_in_job": 0,
                "message": "Nenhum candidato na lista para adicionar"
            }
        
        assigned_count = 0
        already_in_job = 0
        
        for job_id in data.job_vacancy_ids:
            for member in members:
                try:
                    existing = await db.execute(
                        select(VacancyCandidate).where(
                            and_(
                                VacancyCandidate.job_vacancy_id == uuid.UUID(job_id),
                                VacancyCandidate.candidate_id == member.candidate_id
                            )
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        already_in_job += 1
                        continue
                    
                    new_vacancy_candidate = VacancyCandidate(
                        id=uuid.uuid4(),
                        company_id=company_id,
                        job_vacancy_id=uuid.UUID(job_id),
                        candidate_id=member.candidate_id,
                        stage="sourcing",
                        sub_status="sourced",
                        source="list",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(new_vacancy_candidate)
                    assigned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error assigning candidate to job {job_id}: {e}")
        
        await db.commit()
        
        return {
            "success": True,
            "assigned": assigned_count,
            "already_in_job": already_in_job,
            "jobs_count": len(data.job_vacancy_ids),
            "candidates_count": len(members)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning list to jobs: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
