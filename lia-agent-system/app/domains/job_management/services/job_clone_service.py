"""
Job Clone Service - Handles job vacancy duplication and template-based creation.

Two modes:
1. DUPLICATE: Full clone including candidates and their statuses
2. TEMPLATE: Clone job data only (no candidates)
"""
import copy
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_clone_repository import JobCloneRepository
from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository
from lia_models.candidate import VacancyCandidate
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


class CloneMode:
    DUPLICATE = "duplicate"
    TEMPLATE = "template"


class JobCloneService:
    """
    Service for cloning/duplicating job vacancies.
    
    Supports two modes:
    - duplicate: Full clone with candidates
    - template: Clone job data only, no candidates
    """
    
    FIELDS_TO_CLONE = [
        'company_id', 'department', 'location', 'work_model', 'employment_type',
        # T-1166 — `responsibilities` MUST be cloned alongside `requirements`
        # and `technical_requirements`. Omitting it would silently empty the
        # new vacancy's RESPONSABILIDADES panel.
        'seniority_level', 'description', 'responsibilities', 'requirements',
        'technical_requirements',
        'languages', 'behavioral_competencies', 'salary', 'salary_range', 'benefits',
        'priority', 'urgency_level', 'manager', 'manager_email', 'recruiter',
        'recruiter_email', 'organizational_structure', 'interview_stages',
        'screening_questions', 'is_affirmative', 'visibility', 'whatsapp_template_type',
        'tags', 'target_audience', 'target_sector', 'target_segment',
        'governance_rules', 'screening_config'
    ]
    
    FIELDS_TO_RESET = [
        'status', 'stage', 'approval_status', 'published_linkedin',
        'published_website', 'published_indeed', 'budget_used', 'nps',
        'funnel_data', 'published_at', 'closed_at', 'approval_requested_at',
        'approval_requested_by', 'approved_by', 'approved_at', 'rejection_reason'
    ]
    
    async def get_job_by_id_or_title(
        self,
        db: AsyncSession,
        identifier: str,
        company_id: str
    ) -> JobVacancy | None:
        """
        Find a job vacancy by ID, job_id, or title (partial match).
        """
        if not identifier:
            return None
            
        identifier = identifier.strip()
        
        crud_repo = JobVacancyCRUDRepository(db)
        try:
            job_uuid = uuid.UUID(identifier)
            job = await crud_repo.get_vacancy_by_id_and_company(job_uuid, company_id)
            if job:
                return job
        except ValueError:
            pass

        job = await crud_repo.get_by_job_id_and_company(identifier, company_id)
        if job:
            return job

        jobs = await crud_repo.search_by_title_ilike(identifier, company_id)
        if len(jobs) == 1:
            return jobs[0]
        elif len(jobs) > 1:
            return jobs[0]
        
        return None
    
    async def get_vacancy_candidates(
        self,
        db: AsyncSession,
        vacancy_id: uuid.UUID
    ) -> list[VacancyCandidate]:
        """Get all candidates linked to a vacancy."""
        return await JobCloneRepository(db).list_candidates_for_vacancy(vacancy_id)
    
    def _generate_job_id(self, base_title: str, copy_number: int = 1) -> str:
        """Generate a unique job ID with timestamp to avoid collisions."""
        now = datetime.now()
        unique_suffix = str(uuid.uuid4())[:4].upper()
        return f"WDT-{now.year}-{now.strftime('%m%d')}-{now.strftime('%H%M')}-{unique_suffix}"
    
    def _generate_cloned_title(self, original_title: str, copy_number: int = 1) -> str:
        """Generate a title for the cloned job."""
        if original_title.startswith("[DEMO]"):
            base = original_title.replace("[DEMO] ", "").replace("[DEMO]", "")
        else:
            base = original_title
        
        if copy_number == 1:
            return f"{base} (Cópia)"
        else:
            return f"{base} (Cópia {copy_number})"
    
    async def duplicate_job(
        self,
        db: AsyncSession,
        source_job_id: uuid.UUID,
        company_id: str,
        copies: int = 1,
        include_candidates: bool = True,
        candidate_filter: str | None = None,
        candidate_status_override: str | None = None,
        overrides: dict[str, Any] | None = None,
        created_by: str | None = None
    ) -> dict[str, Any]:
        """
        Duplicate a job vacancy with all its data.
        
        Args:
            db: Database session
            source_job_id: UUID of the job to duplicate
            copies: Number of copies to create (default: 1)
            include_candidates: Whether to include candidates (default: True)
            candidate_filter: Filter candidates - 'all', 'approved', or None
            candidate_status_override: If set, all candidates will have this status
            overrides: Dict of fields to override in the cloned job
            created_by: User who initiated the clone
            company_id: Company ID for multi-tenant isolation
            
        Returns:
            Dict with created jobs and summary
        """
        source_job = await JobVacancyCRUDRepository(db).get_vacancy_by_id_and_company(
            source_job_id, company_id
        )

        if not source_job:
            return {
                "success": False,
                "error": f"Vaga com ID {source_job_id} não encontrada",
                "jobs_created": []
            }
        
        source_candidates = []
        if include_candidates:
            all_candidates = await self.get_vacancy_candidates(db, source_job_id)
            if candidate_filter == 'approved':
                source_candidates = [c for c in all_candidates if c.status in ('approved', 'hired', 'offer_accepted')]
            else:
                source_candidates = all_candidates
        
        created_jobs = []
        total_candidates_cloned = 0
        
        for i in range(1, copies + 1):
            new_job = JobVacancy(
                id=uuid.uuid4(),
                job_id=self._generate_job_id(source_job.title, i),
                title=self._generate_cloned_title(source_job.title, i if copies > 1 else 1),
                status="Rascunho",
                stage="Planejamento",
                approval_status="pendente",
                created_by=created_by or source_job.created_by,
                open_date=datetime.now(),
                funnel_data={"total": 0, "screening": 0, "interview": 0, "final": 0, "hired": 0},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            for field in self.FIELDS_TO_CLONE:
                value = getattr(source_job, field, None)
                if value is not None:
                    if isinstance(value, (dict, list)):
                        setattr(new_job, field, copy.deepcopy(value))
                    else:
                        setattr(new_job, field, value)
            
            if overrides:
                for field, value in overrides.items():
                    if hasattr(new_job, field):
                        setattr(new_job, field, value)
            
            if new_job.screening_config:
                config = dict(new_job.screening_config)
                status = dict(config.get("status", {}))
                status["screening_status"] = "not_started"
                status["enabled"] = False
                status["paused_at"] = None
                status["paused_by"] = None
                status["pause_reason"] = None
                status["activated_at"] = None
                status["completed_at"] = None
                status["last_updated"] = datetime.utcnow().isoformat()
                config["status"] = status
                config["metrics"] = {"screened_count": 0, "completion_rate": 0, "average_rating": 0}
                new_job.screening_config = config
            
            new_job.additional_data = {
                **(source_job.additional_data or {}),
                "cloned_from": str(source_job_id),
                "clone_mode": CloneMode.DUPLICATE,
                "cloned_at": datetime.now().isoformat(),
                "cloned_by": created_by
            }
            
            db.add(new_job)
            await db.flush()
            
            if include_candidates and source_candidates:
                from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
                for src_candidate in source_candidates:
                    cloned_stage = src_candidate.stage if not candidate_status_override else "initial"
                    # Task #1306: resolve the structural stage link for the cloned
                    # row so the SLA detector can join by id, not just by name.
                    cloned_stage_id = await resolve_recruitment_stage_id(
                        db, str(src_candidate.company_id), cloned_stage
                    )
                    new_vc = VacancyCandidate(
                        id=uuid.uuid4(),
                        vacancy_id=new_job.id,
                        candidate_id=src_candidate.candidate_id,
                        company_id=src_candidate.company_id,
                        source=src_candidate.source,
                        lia_score=src_candidate.lia_score,
                        match_percentage=src_candidate.match_percentage,
                        status=candidate_status_override or src_candidate.status,
                        stage=cloned_stage,
                        recruitment_stage_id=cloned_stage_id,
                        added_by=created_by or src_candidate.added_by,
                        notes=f"Duplicado da vaga {source_job.title}",
                        additional_data={
                            **(src_candidate.additional_data or {}),
                            "cloned_from_vacancy": str(source_job_id),
                            "original_status": src_candidate.status
                        },
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(new_vc)
                    total_candidates_cloned += 1
            
            created_jobs.append({
                "id": str(new_job.id),
                "job_id": new_job.job_id,
                "title": new_job.title,
                "status": new_job.status,
                "candidates_count": len(source_candidates) if include_candidates else 0
            })
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Created duplicate job: {new_job.title} (ID: {new_job.id})")
        
        await db.commit()
        
        return {
            "success": True,
            "source_job": {
                "id": str(source_job.id),
                "job_id": source_job.job_id,
                "title": source_job.title,
                "candidates_count": len(source_candidates)
            },
            "jobs_created": created_jobs,
            "total_jobs_created": len(created_jobs),
            "total_candidates_cloned": total_candidates_cloned,
            "include_candidates": include_candidates,
            "candidate_status_override": candidate_status_override
        }
    
    async def clone_from_template(
        self,
        db: AsyncSession,
        source_job_id: uuid.UUID,
        company_id: str,
        new_title: str | None = None,
        overrides: dict[str, Any] | None = None,
        created_by: str | None = None
    ) -> dict[str, Any]:
        """
        Create a new job using an existing job as a template.
        Does NOT clone candidates - only job data.
        
        Args:
            db: Database session
            source_job_id: UUID of the job to use as template
            new_title: Title for the new job (optional)
            overrides: Dict of fields to override
            created_by: User who initiated the creation
            company_id: Company ID for multi-tenant isolation
            
        Returns:
            Dict with created job info
        """
        source_job = await JobVacancyCRUDRepository(db).get_vacancy_by_id_and_company(
            source_job_id, company_id
        )

        if not source_job:
            return {
                "success": False,
                "error": f"Vaga com ID {source_job_id} não encontrada"
            }
        
        new_job = JobVacancy(
            id=uuid.uuid4(),
            job_id=self._generate_job_id(source_job.title),
            title=new_title or self._generate_cloned_title(source_job.title),
            status="Rascunho",
            stage="Planejamento",
            approval_status="pendente",
            created_by=created_by or source_job.created_by,
            open_date=datetime.now(),
            funnel_data={"total": 0, "screening": 0, "interview": 0, "final": 0, "hired": 0},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        for field in self.FIELDS_TO_CLONE:
            value = getattr(source_job, field, None)
            if value is not None:
                if isinstance(value, (dict, list)):
                    setattr(new_job, field, copy.deepcopy(value))
                else:
                    setattr(new_job, field, value)
        
        if overrides:
            for field, value in overrides.items():
                if hasattr(new_job, field):
                    setattr(new_job, field, value)
        
        if new_job.screening_config:
            config = dict(new_job.screening_config)
            status = dict(config.get("status", {}))
            status["screening_status"] = "not_started"
            status["enabled"] = False
            status["paused_at"] = None
            status["paused_by"] = None
            status["pause_reason"] = None
            status["activated_at"] = None
            status["completed_at"] = None
            status["last_updated"] = datetime.utcnow().isoformat()
            config["status"] = status
            config["metrics"] = {"screened_count": 0, "completion_rate": 0, "average_rating": 0}
            new_job.screening_config = config
        
        new_job.additional_data = {
            "cloned_from": str(source_job_id),
            "clone_mode": CloneMode.TEMPLATE,
            "cloned_at": datetime.now().isoformat(),
            "cloned_by": created_by
        }
        
        db.add(new_job)
        await db.commit()
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created job from template: {new_job.title} (ID: {new_job.id})")
        
        return {
            "success": True,
            "source_job": {
                "id": str(source_job.id),
                "job_id": source_job.job_id,
                "title": source_job.title
            },
            "created_job": {
                "id": str(new_job.id),
                "job_id": new_job.job_id,
                "title": new_job.title,
                "status": new_job.status,
                "department": new_job.department,
                "location": new_job.location,
                "seniority_level": new_job.seniority_level,
                "manager": new_job.manager,
                "screening_questions_count": len(new_job.screening_questions or []),
                "benefits_count": len(new_job.benefits or [])
            },
            "data_copied": {
                "description": bool(new_job.description),
                "technical_requirements": len(new_job.technical_requirements or []),
                "behavioral_competencies": len(new_job.behavioral_competencies or []),
                "screening_questions": len(new_job.screening_questions or []),
                "benefits": len(new_job.benefits or []),
                "salary_range": bool(new_job.salary_range),
                "interview_stages": len(new_job.interview_stages or [])
            }
        }
    
    async def get_job_summary_for_clone(
        self,
        db: AsyncSession,
        job_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """
        Get a summary of a job for displaying to the user before cloning.
        """
        job = await JobVacancyCRUDRepository(db).get_vacancy_by_id_only(job_id)
        
        if not job:
            return None
        
        candidates = await self.get_vacancy_candidates(db, job_id)
        
        candidate_status_breakdown = {}
        for c in candidates:
            status = c.status or "unknown"
            candidate_status_breakdown[status] = candidate_status_breakdown.get(status, 0) + 1
        
        return {
            "id": str(job.id),
            "job_id": job.job_id,
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "seniority_level": job.seniority_level,
            "work_model": job.work_model,
            "status": job.status,
            "manager": job.manager,
            "candidates_count": len(candidates),
            "candidate_status_breakdown": candidate_status_breakdown,
            "has_description": bool(job.description),
            "technical_requirements_count": len(job.technical_requirements or []),
            "behavioral_competencies_count": len(job.behavioral_competencies or []),
            "screening_questions_count": len(job.screening_questions or []),
            "benefits_count": len(job.benefits or []),
            "has_salary_range": bool(job.salary_range),
            "interview_stages_count": len(job.interview_stages or [])
        }


job_clone_service = JobCloneService()
