"""
Sourcing Pipeline Service - Automated candidate sourcing for job vacancies.

This service handles:
- Checking jobs that need more candidates
- Running sourcing for specific jobs (local search first, then Pearch if needed)
- Running pipeline for all jobs needing candidates
- Integration with TaskService and JobAlertService
- Configurable thresholds for sourcing decisions
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.interview_scheduling.repositories.interview_repository import (
    InterviewRepository,
)
from app.domains.candidates.repositories.vacancy_candidate_repository import (
    VacancyCandidateRepository,
)
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCRUDRepository,
)
from app.repositories.alert_repository import AlertRepository
from app.domains.sourcing.services.pearch_service import pearch_service
from app.shared.compliance.audit_service import audit_service
from app.shared.compliance.fairness_guard import FairnessGuard
from app.services.notification_service import notification_service
from app.repositories.tasks_repository import TasksRepository
from lia_models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from lia_models.candidate import Candidate
from lia_models.interview import Interview
from lia_models.job_vacancy import JobVacancy
from lia_models.task import Task, TaskPriority, TaskStatus, TaskType

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the sourcing pipeline."""
    min_candidates_per_job: int = 10
    min_qualified_ratio: float = 0.3
    auto_expand_to_global: bool = False
    search_limit_local: int = 50
    search_limit_global: int = 20
    days_before_low_volume_alert: int = 7
    auto_create_tasks: bool = True
    auto_create_alerts: bool = True


@dataclass
class PipelineJobStatus:
    """Status of a job in the pipeline."""
    job_id: str
    job_title: str
    total_candidates: int
    qualified_candidates: int
    qualified_ratio: float
    needs_more_candidates: bool
    days_open: int
    last_sourcing_run: datetime | None = None
    pipeline_status: str = "idle"
    recommended_action: str | None = None


@dataclass
class PipelineRunResult:
    """Result of running the sourcing pipeline for a job."""
    job_id: str
    success: bool
    candidates_found_local: int = 0
    candidates_found_global: int = 0
    candidates_added: int = 0
    tasks_created: list[str] = field(default_factory=list)
    alerts_created: list[str] = field(default_factory=list)
    error_message: str | None = None
    expanded_to_global: bool = False
    duration_seconds: float = 0.0


class SourcingPipelineService:
    """
    Service for managing the automated sourcing pipeline.
    
    The pipeline:
    1. Identifies jobs that need more candidates
    2. Runs local search first (proprietary database)
    3. Optionally expands to global search (Pearch AI) if needed
    4. Creates follow-up tasks and alerts as needed
    """
    
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self._running_jobs: dict[str, datetime] = {}
    
    def update_config(self, **kwargs) -> PipelineConfig:
        """
        Update pipeline configuration.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            Updated PipelineConfig
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Pipeline config updated: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
        
        return self.config
    
    def get_config(self) -> dict[str, Any]:
        """Get current pipeline configuration as a dictionary."""
        return {
            "min_candidates_per_job": self.config.min_candidates_per_job,
            "min_qualified_ratio": self.config.min_qualified_ratio,
            "auto_expand_to_global": self.config.auto_expand_to_global,
            "search_limit_local": self.config.search_limit_local,
            "search_limit_global": self.config.search_limit_global,
            "days_before_low_volume_alert": self.config.days_before_low_volume_alert,
            "auto_create_tasks": self.config.auto_create_tasks,
            "auto_create_alerts": self.config.auto_create_alerts,
        }
    
    async def get_job_pipeline_status(
        self,
        db: AsyncSession,
        job_id: str
    ) -> PipelineJobStatus | None:
        """
        Get the pipeline status for a specific job.
        
        Args:
            db: Database session
            job_id: Job ID to check
            
        Returns:
            PipelineJobStatus or None if job not found
        """
        job_repo = JobVacancyCRUDRepository(db)
        job = await job_repo.get_vacancy_by_id(job_id)

        if not job:
            return None

        return await self._build_job_status(db, job)
    
    async def get_jobs_needing_candidates(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> list[PipelineJobStatus]:
        """
        Get all open jobs that need more candidates.
        
        Args:
            db: Database session
            limit: Maximum number of jobs to return
            
        Returns:
            List of PipelineJobStatus for jobs needing candidates
        """
        job_repo = JobVacancyCRUDRepository(db)
        open_jobs = await job_repo.list_by_statuses(
            ["open", "Ativa", "active"], limit=limit
        )
        
        jobs_needing_candidates = []
        
        for job in open_jobs:
            status = await self._build_job_status(db, job)
            if status.needs_more_candidates:
                jobs_needing_candidates.append(status)
        
        jobs_needing_candidates.sort(
            key=lambda x: (x.qualified_ratio, -x.days_open)
        )
        
        logger.info(f"Found {len(jobs_needing_candidates)} jobs needing more candidates")
        
        return jobs_needing_candidates
    
    async def run_pipeline_for_job(
        self,
        db: AsyncSession,
        job_id: str,
        force_global_search: bool = False
    ) -> PipelineRunResult:
        """
        Run the sourcing pipeline for a specific job.
        
        This is idempotent - safe to run multiple times. It will:
        1. Check current candidate volume
        2. Search local database for matching candidates
        3. Optionally search Pearch AI if needed and configured
        4. Create follow-up tasks and alerts
        
        Args:
            db: Database session
            job_id: Job ID to run pipeline for
            force_global_search: Force expansion to global search (Pearch)
            
        Returns:
            PipelineRunResult with details of the pipeline run
        """
        start_time = datetime.utcnow()
        
        if job_id in self._running_jobs:
            last_run = self._running_jobs[job_id]
            if (datetime.utcnow() - last_run).total_seconds() < 60:
                return PipelineRunResult(
                    job_id=job_id,
                    success=False,
                    error_message="Pipeline already running for this job (rate limited)"
                )
        
        self._running_jobs[job_id] = datetime.utcnow()
        
        try:
            job_repo = JobVacancyCRUDRepository(db)
            job = await job_repo.get_vacancy_by_id(job_id)

            if not job:
                return PipelineRunResult(
                    job_id=job_id,
                    success=False,
                    error_message=f"Job {job_id} not found"
                )
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"🚀 Running sourcing pipeline for job: {job.title} ({job_id})")
            
            status = await self._build_job_status(db, job)
            
            local_candidates = await self._run_local_search(db, job)
            candidates_added_local = await self._add_candidates_to_job(
                db, job, local_candidates
            )
            
            global_candidates_found = 0
            candidates_added_global = 0
            expanded_to_global = False
            
            should_expand = (
                force_global_search or 
                (self.config.auto_expand_to_global and 
                 status.total_candidates + candidates_added_local < self.config.min_candidates_per_job)
            )
            
            if should_expand:
                try:
                    global_candidates, _g_phash = await self._run_global_search(job)
                    global_candidates_found = len(global_candidates)
                    candidates_added_global = await self._add_pearch_candidates_to_job(
                        db, job, global_candidates
                    )
                    expanded_to_global = True
                except Exception as e:
                    logger.warning(f"Global search failed: {e}")
            
            tasks_created = []
            alerts_created = []
            
            total_added = candidates_added_local + candidates_added_global
            new_total = status.total_candidates + total_added
            
            if new_total < self.config.min_candidates_per_job:
                if self.config.auto_create_tasks:
                    task = await self._create_sourcing_task(db, job, new_total)
                    if task:
                        tasks_created.append(task.id)
                
                if self.config.auto_create_alerts:
                    alert = await self._create_low_volume_alert(db, job, new_total)
                    if alert:
                        alerts_created.append(alert.id)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"✅ Pipeline completed for {job.title}: "
                f"local={candidates_added_local}, global={candidates_added_global}, "
                f"duration={duration:.2f}s"
            )
            
            return PipelineRunResult(
                job_id=job_id,
                success=True,
                candidates_found_local=len(local_candidates),
                candidates_found_global=global_candidates_found,
                candidates_added=total_added,
                tasks_created=tasks_created,
                alerts_created=alerts_created,
                expanded_to_global=expanded_to_global,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed for job {job_id}: {e}", exc_info=True)
            return PipelineRunResult(
                job_id=job_id,
                success=False,
                error_message=str(e),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
        finally:
            self._running_jobs.pop(job_id, None)
    
    async def run_pipeline_for_all_jobs(
        self,
        db: AsyncSession,
        max_jobs: int = 10
    ) -> dict[str, Any]:
        """
        Run the sourcing pipeline for all jobs that need more candidates.
        
        Args:
            db: Database session
            max_jobs: Maximum number of jobs to process in one run
            
        Returns:
            Summary of the pipeline run
        """
        start_time = datetime.utcnow()
        
        jobs_needing_candidates = await self.get_jobs_needing_candidates(db, limit=max_jobs)
        
        if not jobs_needing_candidates:
            logger.info("No jobs need more candidates at this time")
            return {
                "success": True,
                "jobs_processed": 0,
                "total_candidates_added": 0,
                "message": "No jobs need more candidates",
                "duration_seconds": 0.0
            }
        
        results = []
        total_candidates_added = 0
        total_tasks_created = 0
        total_alerts_created = 0
        jobs_succeeded = 0
        jobs_failed = 0
        
        for job_status in jobs_needing_candidates:
            result = await self.run_pipeline_for_job(db, job_status.job_id)
            results.append(result)
            
            if result.success:
                jobs_succeeded += 1
                total_candidates_added += result.candidates_added
                total_tasks_created += len(result.tasks_created)
                total_alerts_created += len(result.alerts_created)
            else:
                jobs_failed += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"🎯 Pipeline batch completed: {jobs_succeeded}/{len(jobs_needing_candidates)} jobs succeeded, "
            f"{total_candidates_added} candidates added, duration={duration:.2f}s"
        )
        
        return {
            "success": jobs_failed == 0,
            "jobs_processed": len(jobs_needing_candidates),
            "jobs_succeeded": jobs_succeeded,
            "jobs_failed": jobs_failed,
            "total_candidates_added": total_candidates_added,
            "total_tasks_created": total_tasks_created,
            "total_alerts_created": total_alerts_created,
            "duration_seconds": duration,
            "results": [
                {
                    "job_id": r.job_id,
                    "success": r.success,
                    "candidates_added": r.candidates_added,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }
    

    async def _check_fairness_on_criteria(
        self,
        job: "Any",
        tags: "list[str] | None" = None,
        context: str = "",
    ) -> "tuple[bool, str | None, str]":
        """Run FairnessGuard on job criteria and return (blocked, category, prompt_hash).

        Sends a bell notification to the job recruiter when criteria are blocked.
        Fire-and-forget: never raises — callers must not fail if this method errors.
        """
        criteria_text = _build_criteria_text(job, tags)
        phash = _prompt_hash(criteria_text)
        guard = FairnessGuard()
        result = guard.check(criteria_text)
        if result.is_blocked and getattr(job, "created_by", None):
            try:
                await notification_service.create_notification(
                    user_id=job.created_by,
                    title=f"Critérios bloqueados: {getattr(job, 'title', '')}",
                    message=(
                        f"FairnessGuard detectou critérios discriminatórios na vaga "
                        f"'{getattr(job, 'title', '')}' (categoria: {result.category}). "
                        "Revise os requisitos antes de publicar."
                    ),
                    source_trigger="fairness_block",
                    related_job_id=str(getattr(job, "id", "") or ""),
                    action_url=f"/jobs/{getattr(job, 'id', '')}",
                    channels=["bell"],
                )
            except Exception as _exc:
                logger.warning("[Fairness] Notification failed: %s", _exc)
        return (result.is_blocked, result.category, phash)

    async def _audit_sourcing_decision(
        self,
        job: "Any",
        candidate_id: "str | None",
        decision_type: str,
        decision: str,
        prompt_hash: str,
        reasoning: "list[str]",
        criteria_used: "list[str]",
        score: "float | None" = None,
    ) -> None:
        """Log a sourcing decision to the compliance audit trail."""
        await audit_service.log_decision(
            company_id=str(getattr(job, "company_id", "") or ""),
            agent_name="sourcing_pipeline",
            decision_type=decision_type,
            action=f"sourcing_decision phash:{prompt_hash[:12]}...",
            decision=decision,
            reasoning=reasoning,
            criteria_used=criteria_used,
            candidate_id=candidate_id,
            job_vacancy_id=str(getattr(job, "id", "") or ""),
            score=score,
            demographic_proxies={},
        )

    async def _build_job_status(
        self,
        db: AsyncSession,
        job: JobVacancy
    ) -> PipelineJobStatus:
        """Build a PipelineJobStatus for a job."""
        interview_repo = InterviewRepository(db)
        total_candidates = await interview_repo.count_distinct_candidates_for_job(
            job.id
        )
        qualified_candidates = await interview_repo.count_distinct_candidates_for_job(
            job.id, statuses=["scheduled", "confirmed", "completed"]
        )
        
        qualified_ratio = qualified_candidates / total_candidates if total_candidates > 0 else 0.0
        
        days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
        
        needs_more = (
            total_candidates < self.config.min_candidates_per_job or
            qualified_ratio < self.config.min_qualified_ratio
        )
        
        if needs_more:
            if total_candidates == 0:
                recommended_action = "urgent_sourcing"
                pipeline_status = "critical"
            elif total_candidates < self.config.min_candidates_per_job // 2:
                recommended_action = "expand_to_global"
                pipeline_status = "low"
            else:
                recommended_action = "local_search"
                pipeline_status = "needs_attention"
        else:
            recommended_action = None
            pipeline_status = "healthy"
        
        return PipelineJobStatus(
            job_id=str(job.id),
            job_title=job.title,
            total_candidates=total_candidates,
            qualified_candidates=qualified_candidates,
            qualified_ratio=qualified_ratio,
            needs_more_candidates=needs_more,
            days_open=days_open,
            pipeline_status=pipeline_status,
            recommended_action=recommended_action
        )
    
    async def _run_local_search(
        self,
        db: AsyncSession,
        job: JobVacancy
    ) -> list[Candidate]:
        """
        Search for matching candidates in local database.
        
        Args:
            db: Database session
            job: Job to match against
            
        Returns:
            List of matching candidates
        """
        skills = job.technical_requirements or []
        skill_names = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_names.append(skill.get("technology", ""))
            elif isinstance(skill, str):
                skill_names.append(skill)
        
        if isinstance(job.requirements, list):
            skill_names.extend(job.requirements[:5])
        
        if not skill_names:
            skill_names = [job.title]
        
        interview_repo = InterviewRepository(db)
        existing_ids = await interview_repo.get_candidate_ids_for_job(job.id)

        candidate_repo = CandidateRepository(db)
        all_candidates = await candidate_repo.list_active_not_blacklisted(
            limit=self.config.search_limit_local
        )
        
        matched_candidates = []
        for candidate in all_candidates:
            if candidate.id in existing_ids:
                continue
                
            candidate_skills = candidate.technical_skills or []
            if any(
                skill.lower() in [s.lower() for s in candidate_skills]
                for skill in skill_names
                if skill
            ):
                matched_candidates.append(candidate)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Local search found {len(matched_candidates)} matching candidates for {job.title}")
        
        return matched_candidates
    
    async def _run_global_search(self, job: JobVacancy) -> "tuple[list[dict[str, Any]], str]":
        """
        Search for candidates using Pearch AI global database.
        
        Args:
            job: Job to search for
            
        Returns:
            List of candidate profiles from Pearch
        """
        # Build criteria text (used for hash + PII-stripped query)
        criteria_text = _build_criteria_text(job)
        search_phash = _prompt_hash(criteria_text)
        # Strip PII: emails, phone numbers, CPF/CNPJ patterns
        import re as _re
        _pii_patterns = [
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",  # email
            r"(?:\+?55)?\s*\(?\d{2}\)?[\s\-]?\d{4,5}[\s\-]?\d{4}",  # phone BR
            r"\d{3}\.\d{3}\.\d{3}\-\d{2}",  # CPF
            r"\d{2}\.\d{3}\.\d{3}\/\d{4}\-\d{2}",  # CNPJ
        ]
        search_query = f"{job.title}"
        if job.location:
            search_query += f" in {job.location}"
        for _pat in _pii_patterns:
            search_query = _re.sub(_pat, "[REDACTED]", search_query, flags=_re.IGNORECASE)
        
        skills = job.technical_requirements or []
        skill_names = []
        for skill in skills[:3]:
            if isinstance(skill, dict):
                tech = skill.get("technology")
                if tech:
                    skill_names.append(tech)
            elif isinstance(skill, str):
                skill_names.append(skill)
        
        if skill_names:
            search_query += f" with {', '.join(skill_names)}"
        
        logger.info(f"Running Pearch global search: {search_query}")
        
        try:
            response = await pearch_service.search_candidates(
                query=search_query,
                search_type="fast",
                limit=self.config.search_limit_global
            )
            
            candidates = []
            for profile in response.candidates:
                candidates.append({
                    "pearch_id": profile.id,
                    "name": profile.name,
                    "email": profile.contact.email if profile.contact else None,
                    "phone": profile.contact.phone if profile.contact else None,
                    "linkedin_url": profile.contact.linkedin_url if profile.contact else None,
                    "current_title": profile.current_title,
                    "current_company": profile.current_company,
                    "location": profile.location,
                    "skills": profile.skills,
                    "match_score": profile.match_score
                })
            
            return candidates, search_phash
            
        except Exception as e:
            logger.error(f"Pearch search failed: {e}")
            raise
    
    def _calculate_local_match_score(
        self,
        candidate: Candidate,
        job: JobVacancy
    ) -> float:
        """
        Calculate match score for a local candidate against a job.
        
        Args:
            candidate: The candidate to score
            job: The job to match against
            
        Returns:
            Match score between 0-100
        """
        score = 0.0
        max_score = 100.0
        
        job_skills = []
        skills = job.technical_requirements or []
        for skill in skills:
            if isinstance(skill, dict):
                tech = skill.get("technology", "")
                if tech:
                    job_skills.append(tech.lower())
            elif isinstance(skill, str):
                job_skills.append(skill.lower())
        
        if isinstance(job.requirements, list):
            for req in job.requirements[:5]:
                if isinstance(req, str):
                    job_skills.append(req.lower())
        
        if not job_skills:
            job_skills = [job.title.lower()] if job.title else []
        
        candidate_skills = [s.lower() for s in (candidate.technical_skills or [])]
        
        if job_skills and candidate_skills:
            matching_skills = sum(1 for skill in job_skills if skill in candidate_skills)
            skill_score = (matching_skills / len(job_skills)) * 50
            score += skill_score
        
        if candidate.seniority_level:
            score += 10
        
        if candidate.years_of_experience:
            exp_score = min(candidate.years_of_experience * 2, 20)
            score += exp_score
        
        if candidate.current_title:
            job_title_lower = (job.title or "").lower()
            candidate_title_lower = candidate.current_title.lower()
            if any(word in candidate_title_lower for word in job_title_lower.split() if len(word) > 3):
                score += 15
        
        if candidate.location_city or candidate.location_state:
            score += 5
        
        return min(score, max_score)
    
    async def _add_candidates_to_job(
        self,
        db: AsyncSession,
        job: JobVacancy,
        candidates: list[Candidate],
        prompt_hash: str | None = None,
    ) -> int:
        """
        Add found candidates to the job pipeline by creating initial interview records.
        
        Args:
            db: Database session
            job: Job to add candidates to
            candidates: List of candidates to add
            
        Returns:
            Number of candidates added
        """
        added_count = 0
        interview_repo = InterviewRepository(db)

        for candidate in candidates:
            existing_interview = await interview_repo.get_for_candidate_and_job(
                candidate.id, job.id
            )
            if existing_interview:
                if prompt_hash:
                    try:
                        await audit_service.log_decision(
                            company_id=str(getattr(job, "company_id", "") or ""),
                            agent_name="sourcing_pipeline",
                            decision_type="reject_candidate",
                            action=f"skip_duplicate phash:{prompt_hash}",
                            decision="rejected",
                            reasoning=["candidate already in pipeline"],
                            criteria_used=["pipeline_dedup"],
                            candidate_id=str(candidate.id),
                            job_vacancy_id=str(getattr(job, "id", "") or ""),
                            demographic_proxies={},
                        )
                    except Exception as _exc:
                        logger.debug("[sourcing] audit skip failed: %s", _exc)
                continue

            match_score = self._calculate_local_match_score(candidate, job)
            candidate.lia_score = match_score
            
            interview = Interview(
                title=f"Pipeline: {job.title} - {candidate.name}",
                description="Candidato adicionado automaticamente ao pipeline",
                interview_type="triagem",
                interview_mode="phone",
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                candidate_email=candidate.email or "",
                interviewer_name="LIA Pipeline",
                interviewer_email="system@lia.app",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                job_vacancy_id=job.id,
                job_title=job.title,
                application_stage="triagem",
                status="pending",
                created_by="sourcing_pipeline"
            )
            
            db.add(interview)
            added_count += 1

            # P1-4: criar VacancyCandidate para retroalimentar lia_score pos-triagem.
            # Fail-soft: falha no VC nao aborta a adicao do candidato (Interview já foi feito).
            try:
                vc_repo = VacancyCandidateRepository(db)
                await vc_repo.create_sourced(
                    vacancy_id=str(job.id),
                    candidate_id=str(candidate.id),
                    company_id=str(getattr(job, "company_id", "") or ""),
                    lia_score=match_score,
                    status="sourced",
                    stage="initial",
                    source="local",
                    origin="pipeline",
                )
            except Exception as _vc_exc:
                logger.warning("[P1-4] VacancyCandidate nao criado (fail-soft): %s", _vc_exc)

            candidate.updated_at = datetime.utcnow()
        
        if added_count > 0:
            await db.commit()
        
        return added_count
    
    async def _add_pearch_candidates_to_job(
        self,
        db: AsyncSession,
        job: JobVacancy,
        pearch_candidates: list[dict[str, Any]]
    ) -> int:
        """
        Add Pearch candidates to the database and job pipeline.
        
        Args:
            db: Database session
            job: Job to add candidates to
            pearch_candidates: List of candidate data from Pearch
            
        Returns:
            Number of candidates added
        """
        added_count = 0
        candidate_repo = CandidateRepository(db)
        interview_repo = InterviewRepository(db)

        for data in pearch_candidates:
            email = data.get("email")
            existing_candidate = None

            if email:
                existing_candidate = await candidate_repo.get_by_email(email)

            if existing_candidate:
                existing_interview = await interview_repo.get_for_candidate_and_job(
                    existing_candidate.id, job.id
                )
                if existing_interview:
                    continue
                candidate = existing_candidate
            else:
                candidate = Candidate(
                    name=data.get("name", "Unknown"),
                    email=email,
                    phone=data.get("phone"),
                    linkedin_url=data.get("linkedin_url"),
                    current_title=data.get("current_title"),
                    current_company=data.get("current_company"),
                    location_city=data.get("location"),
                    technical_skills=data.get("skills", []),
                    source="pearch",
                    pearch_profile_id=data.get("pearch_id"),
                    lia_score=data.get("match_score"),
                    status="new"
                )
                db.add(candidate)
                await db.flush()
            
            interview = Interview(
                title=f"Pipeline: {job.title} - {candidate.name}",
                description="Candidato sourced via Pearch AI global search",
                interview_type="triagem",
                interview_mode="phone",
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                candidate_email=candidate.email or "",
                interviewer_name="LIA Pipeline",
                interviewer_email="system@lia.app",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                job_vacancy_id=job.id,
                job_title=job.title,
                application_stage="triagem",
                status="pending",
                created_by="sourcing_pipeline_pearch"
            )
            
            db.add(interview)
            added_count += 1

            # P1-4: criar VacancyCandidate para candidato sourced via Pearch.
            # Fail-soft: falha no VC nao aborta a adicao.
            try:
                vc_repo_pearch = VacancyCandidateRepository(db)
                _pearch_lia_score = data.get("match_score") if isinstance(data, dict) else None
                await vc_repo_pearch.create_sourced(
                    vacancy_id=str(job.id),
                    candidate_id=str(candidate.id),
                    company_id=str(getattr(job, "company_id", "") or ""),
                    lia_score=_pearch_lia_score,
                    status="sourced",
                    stage="initial",
                    source="pearch",
                    origin="pipeline",
                )
            except Exception as _vc_pearch_exc:
                logger.warning("[P1-4] VacancyCandidate pearch nao criado (fail-soft): %s", _vc_pearch_exc)

        if added_count > 0:
            await db.commit()
        
        return added_count
    
    async def _create_sourcing_task(
        self,
        db: AsyncSession,
        job: JobVacancy,
        current_count: int
    ) -> Task | None:
        """
        Create a follow-up sourcing task.
        
        Args:
            db: Database session
            job: Job that needs more candidates
            current_count: Current candidate count
            
        Returns:
            Created Task or None if task already exists
        """
        tasks_repo = TasksRepository(db)
        existing_task = await tasks_repo.get_active_task_for_job_and_type(
            company_id=str(job.company_id),
            job_id=str(job.id),
            task_type=TaskType.SOURCING,
        )
        if existing_task:
            return None
        
        needed = self.config.min_candidates_per_job - current_count
        
        task = Task(
            title=f"Buscar mais candidatos para: {job.title}",
            description=f"A vaga '{job.title}' precisa de mais {needed} candidatos. "
                       f"Atualmente tem {current_count}/{self.config.min_candidates_per_job}.",
            task_type=TaskType.SOURCING,
            priority=TaskPriority.HIGH if current_count < 5 else TaskPriority.MEDIUM,
            assigned_to_agent="sourcing",
            company_id=str(job.company_id),
            related_job_id=str(job.id),
            due_date=datetime.utcnow() + timedelta(days=3),
            context={
                "current_count": current_count,
                "target_count": self.config.min_candidates_per_job,
                "job_title": job.title,
                "pipeline_action": "source_candidates"
            },
            is_automated=True,
            requires_confirmation=False
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created sourcing task: {task.id} for job {job.title}")
        
        return task
    
    async def _create_low_volume_alert(
        self,
        db: AsyncSession,
        job: JobVacancy,
        current_count: int
    ) -> Alert | None:
        """
        Create a low volume alert for the job.
        
        Args:
            db: Database session
            job: Job with low candidate volume
            current_count: Current candidate count
            
        Returns:
            Created Alert or None if alert already exists
        """
        days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
        
        if days_open < self.config.days_before_low_volume_alert:
            return None
        
        alert_repo = AlertRepository(db)
        existing_alert = await alert_repo.get_active_alert_for_job_and_type(
            str(job.id), AlertType.JOB_LOW_VOLUME
        )
        if existing_alert:
            return None
        
        severity = AlertSeverity.CRITICAL if current_count < 3 else AlertSeverity.HIGH
        
        alert = Alert(
            alert_type=AlertType.JOB_LOW_VOLUME,
            severity=severity,
            title=f"Poucos candidatos: {job.title}",
            message=f"A vaga '{job.title}' tem apenas {current_count} candidatos após {days_open} dias. "
                   f"O mínimo recomendado é {self.config.min_candidates_per_job}.",
            job_id=str(job.id),
            context={
                "candidate_count": current_count,
                "days_open": days_open,
                "job_title": job.title,
                "threshold": self.config.min_candidates_per_job,
            },
            suggested_actions=[
                "Buscar candidatos no banco global (Pearch)",
                "Flexibilizar requisitos da vaga",
                "Publicar em mais canais",
                "Ativar programa de indicação"
            ]
        )
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created low volume alert: {alert.id} for job {job.title}")
        
        return alert
    
    async def run_post_publish_sourcing(
        self,
        db: AsyncSession,
        job_id: str,
        user_credits: int,
        expand_to_global: bool = False
    ) -> dict[str, Any]:
        """
        Run sourcing immediately after job publication.
        
        This is triggered when a job is published and should populate
        the initial candidate pipeline.
        
        Args:
            db: Database session
            job_id: Job ID that was just published
            user_credits: Available user credits for global search
            expand_to_global: Whether to immediately expand to global search
            
        Returns:
            {
                "local_candidates_found": int,
                "local_candidates_added": int,
                "global_search_available": bool,
                "credits_required": int,
                "awaiting_global_confirmation": bool,
                "pipeline_populated": bool
            }
        """
        logger.info(f"🚀 Running post-publish sourcing for job: {job_id}")

        job_repo = JobVacancyCRUDRepository(db)
        job = await job_repo.get_vacancy_by_id(job_id)

        if not job:
            logger.error(f"Job {job_id} not found for post-publish sourcing")
            return {
                "local_candidates_found": 0,
                "local_candidates_added": 0,
                "global_search_available": False,
                "credits_required": 0,
                "awaiting_global_confirmation": False,
                "pipeline_populated": False,
                "error": f"Job {job_id} not found"
            }
        
        local_candidates = await self._run_local_search(db, job)
        local_candidates_found = len(local_candidates)
        local_candidates_added = await self._add_candidates_to_job(db, job, local_candidates)
        
        global_candidates_found = 0
        global_candidates_added = 0
        
        credits_per_candidate = 1
        credits_required = self.config.search_limit_global * credits_per_candidate
        global_search_available = user_credits >= credits_required
        awaiting_global_confirmation = False
        
        if expand_to_global and global_search_available:
            try:
                global_candidates_list, _g_phash2 = await self._run_global_search(job)
                global_candidates_found = len(global_candidates_list)
                global_candidates_added = await self._add_pearch_candidates_to_job(
                    db, job, global_candidates_list
                )
            except Exception as e:
                logger.warning(f"Global search failed during post-publish: {e}")
        elif not expand_to_global and local_candidates_added < self.config.min_candidates_per_job:
            awaiting_global_confirmation = global_search_available
        
        total_added = local_candidates_added + global_candidates_added
        pipeline_populated = total_added >= self.config.min_candidates_per_job
        
        logger.info(
            f"✅ Post-publish sourcing completed for {job.title}: "
            f"local_found={local_candidates_found}, local_added={local_candidates_added}, "
            f"global_added={global_candidates_added}, pipeline_populated={pipeline_populated}"
        )
        
        return {
            "local_candidates_found": local_candidates_found,
            "local_candidates_added": local_candidates_added,
            "global_candidates_found": global_candidates_found,
            "global_candidates_added": global_candidates_added,
            "total_candidates_added": total_added,
            "global_search_available": global_search_available,
            "credits_required": credits_required,
            "awaiting_global_confirmation": awaiting_global_confirmation,
            "pipeline_populated": pipeline_populated,
            "job_title": job.title
        }
    
    async def confirm_global_search(
        self,
        db: AsyncSession,
        job_id: str,
        user_id: str,
        credits_to_use: int
    ) -> dict[str, Any]:
        """
        Confirm global search and add Pearch candidates.
        Deducts credits from user account.
        
        Args:
            db: Database session
            job_id: Job ID to search for
            user_id: User ID confirming the search (for credit deduction)
            credits_to_use: Number of credits to use for this search
            
        Returns:
            {
                "success": bool,
                "candidates_found": int,
                "candidates_added": int,
                "credits_deducted": int,
                "error": Optional[str]
            }
        """
        logger.info(f"🌍 Confirming global search for job: {job_id}, user: {user_id}, credits: {credits_to_use}")

        job_repo = JobVacancyCRUDRepository(db)
        job = await job_repo.get_vacancy_by_id(job_id)

        if not job:
            return {
                "success": False,
                "candidates_found": 0,
                "candidates_added": 0,
                "credits_deducted": 0,
                "error": f"Job {job_id} not found"
            }
        
        try:
            global_candidates, _g_phash3 = await self._run_global_search(job)
            candidates_found = len(global_candidates)
            
            candidates_added = await self._add_pearch_candidates_to_job(
                db, job, global_candidates
            )
            
            credits_per_candidate = 1
            credits_deducted = min(candidates_added * credits_per_candidate, credits_to_use)
            
            logger.info(
                f"✅ Global search confirmed for {job.title}: "
                f"found={candidates_found}, added={candidates_added}, credits_deducted={credits_deducted}"
            )
            
            return {
                "success": True,
                "candidates_found": candidates_found,
                "candidates_added": candidates_added,
                "credits_deducted": credits_deducted,
                "job_title": job.title
            }
            
        except Exception as e:
            logger.error(f"❌ Global search failed for job {job_id}: {e}", exc_info=True)
            return {
                "success": False,
                "candidates_found": 0,
                "candidates_added": 0,
                "credits_deducted": 0,
                "error": str(e)
            }
    
    async def get_sourcing_status(
        self,
        db: AsyncSession,
        job_id: str
    ) -> dict[str, Any]:
        """
        Get current sourcing progress and candidates found for a job.
        
        Args:
            db: Database session
            job_id: Job ID to check
            
        Returns:
            Sourcing status including candidate counts and pipeline status
        """
        status = await self.get_job_pipeline_status(db, job_id)
        
        if not status:
            return {
                "found": False,
                "error": f"Job {job_id} not found"
            }
        
        return {
            "found": True,
            "job_id": status.job_id,
            "job_title": status.job_title,
            "total_candidates": status.total_candidates,
            "qualified_candidates": status.qualified_candidates,
            "qualified_ratio": status.qualified_ratio,
            "needs_more_candidates": status.needs_more_candidates,
            "days_open": status.days_open,
            "pipeline_status": status.pipeline_status,
            "recommended_action": status.recommended_action,
            "min_candidates_target": self.config.min_candidates_per_job
        }


sourcing_pipeline_service = SourcingPipelineService()



# ---------------------------------------------------------------------------
# Module-level helpers used by tests and internal services (C6)
# ---------------------------------------------------------------------------

def _build_criteria_text(job, tags: "list[str] | None" = None) -> str:
    """Build a plain-text blob from job fields + extra tags for FairnessGuard.

    Combines the job title, description, location, and base requirements with
    any caller-supplied additional tags so the guard can scan all criteria in
    one pass.

    Args:
        job: A job/vacancy object with ``title``, ``description``,
            ``location``, and ``requirements`` attributes (None-safe).
        tags: Additional skill or keyword strings to include.

    Returns:
        Space-joined string of all non-empty parts.
    """
    parts: list[str] = []
    for attr in ("title", "description", "location"):
        val = getattr(job, attr, None)
        if val:
            parts.append(str(val))
    for req in (getattr(job, "requirements", None) or []):
        if req:
            parts.append(str(req))
    for tag in (tags or []):
        if tag:
            parts.append(str(tag))
    return " ".join(parts)


def _prompt_hash(text: str) -> str:
    """Return the stable SHA-256 hex digest of *text*.

    Used to fingerprint sourcing criteria prompts for audit log deduplication.
    The same input always produces the same 64-character hex string.

    Args:
        text: The string to hash.

    Returns:
        64-character lowercase hex string (SHA-256).
    """
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()
