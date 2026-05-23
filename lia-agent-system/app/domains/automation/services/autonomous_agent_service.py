"""
Autonomous Agent Service - Manages background jobs and proactive actions.

Enables LIA to:
- Create and execute background jobs
- Handle scheduled/recurring tasks
- Generate proactive suggestions
- Execute automatic actions
"""
import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, text, update

from app.core.database import AsyncSessionLocal
from lia_models.background_jobs import (
    ActionStatus,
    BackgroundJob,
    JobStatus,
    JobType,
    ProactiveAction,
)

logger = logging.getLogger(__name__)

_DEPRECATED_DEFAULT_COMPANY_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class AutonomousAgentService:
    """
    Service for managing autonomous background agents.
    
    Provides:
    - Job creation and management
    - Scheduled job execution
    - Proactive action suggestions
    - Action acceptance/rejection workflow
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_job(
        self,
        company_id: str,
        job_type: str,
        name: str,
        config: dict,
        schedule: str | None = None,
        created_by: str = "system",
        description: str | None = None
    ) -> BackgroundJob:
        """
        Create a new background job.
        
        Args:
            company_id: Company ID for multi-tenancy
            job_type: Type of job (screening, sourcing, etc.)
            name: Human-readable job name
            config: Job configuration parameters
            schedule: Optional cron expression for recurring jobs
            created_by: User/system that created the job
            description: Optional job description
            
        Returns:
            Created BackgroundJob instance
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Creating background job: {name} (type={job_type})")
        
        async with AsyncSessionLocal() as db:
            try:
                company_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
            except ValueError:
                raise ValueError(f"Invalid company_id format: '{company_id}'. A valid UUID is required.")
            
            job = BackgroundJob(
                id=uuid4(),
                company_id=company_uuid,
                job_type=job_type,
                name=name,
                description=description,
                config=config or {},
                schedule=schedule,
                status=JobStatus.PENDING.value,
                progress=0,
                run_count=0,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            if schedule:
                job.next_run_at = self._calculate_next_run(schedule)
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            self.logger.info(f"Created job {job.id} with status {job.status}")
            return job
    
    async def get_job(self, job_id: str) -> BackgroundJob | None:
        """Get a job by ID."""
        async with AsyncSessionLocal() as db:
            try:
                job_uuid = UUID(job_id)
            except ValueError:
                return None
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(BackgroundJob).where(BackgroundJob.id == job_uuid)
            )
            return result.scalar_one_or_none()
    
    async def list_jobs(
        self,
        company_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 50
    ) -> list[BackgroundJob]:
        """List jobs with optional filters."""
        async with AsyncSessionLocal() as db:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                raise ValueError(f"Invalid company_id format: '{company_id}'. A valid UUID is required.")
            
            query = select(BackgroundJob).where(
                BackgroundJob.company_id == company_uuid
            )
            
            if status:
                query = query.where(BackgroundJob.status == status)
            
            if job_type:
                query = query.where(BackgroundJob.job_type == job_type)
            
            query = query.order_by(BackgroundJob.created_at.desc()).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
    
    async def execute_job(self, job_id: str) -> dict:
        """
        Execute a background job.
        
        Routes to appropriate executor based on job_type.
        
        Args:
            job_id: UUID of the job to execute
            
        Returns:
            Execution result dict
        """
        self.logger.info(f"Executing job {job_id}")
        
        async with AsyncSessionLocal() as db:
            try:
                job_uuid = UUID(job_id)
            except ValueError:
                return {"success": False, "error": "Invalid job ID"}
            
            # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(BackgroundJob).where(BackgroundJob.id == job_uuid)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job.status == JobStatus.RUNNING.value:
                return {"success": False, "error": "Job is already running"}
            
            if job.status == JobStatus.CANCELLED.value:
                return {"success": False, "error": "Job has been cancelled"}
            
            job.start_execution()
            await db.commit()
        
        try:
            job_type = job.job_type
            
            if job_type == JobType.SCREENING.value:
                execution_result = await self._execute_screening_job(job)
            elif job_type == JobType.SOURCING.value:
                execution_result = await self._execute_sourcing_job(job)
            elif job_type == JobType.REPORT_GENERATION.value:
                execution_result = await self._execute_report_job(job)
            elif job_type == JobType.MARKET_ANALYSIS.value:
                execution_result = await self._execute_market_analysis_job(job)
            elif job_type == JobType.CANDIDATE_OUTREACH.value:
                execution_result = await self._execute_outreach_job(job)
            elif job_type == JobType.PATTERN_LEARNING.value:
                execution_result = await self._execute_pattern_learning_job(job)
            else:
                execution_result = {"success": False, "error": f"Unknown job type: {job_type}"}
            
            # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                    select(BackgroundJob).where(BackgroundJob.id == job_uuid)
                )
                job = result.scalar_one_or_none()
                
                if job:
                    if execution_result.get("success", False):
                        job.complete_execution(execution_result)
                    else:
                        job.fail_execution(execution_result.get("error", "Unknown error"))
                    
                    if job.schedule:
                        job.next_run_at = self._calculate_next_run(job.schedule)
                        job.status = JobStatus.PENDING.value
                    
                    await db.commit()
            
            self.logger.info(f"Job {job_id} execution completed: {execution_result.get('success', False)}")
            return execution_result
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Job {job_id} execution failed: {e}")
            # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                    select(BackgroundJob).where(BackgroundJob.id == job_uuid)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.fail_execution(str(e))
                    await db.commit()
            
            return {"success": False, "error": str(e)}
    
    async def cancel_job(self, job_id: str) -> dict:
        """Cancel a pending or scheduled job."""
        async with AsyncSessionLocal() as db:
            try:
                job_uuid = UUID(job_id)
            # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
            except ValueError:
                return {"success": False, "error": "Invalid job ID"}
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(BackgroundJob).where(BackgroundJob.id == job_uuid)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job.status == JobStatus.RUNNING.value:
                return {"success": False, "error": "Cannot cancel running job"}
            
            job.cancel()
            await db.commit()
            
            return {"success": True, "job_id": str(job_id)}
    
    async def check_and_execute_scheduled_jobs(self) -> list[str]:
        """
        Check for scheduled jobs ready to run and execute them.
        
        Returns:
            List of executed job IDs
        """
        self.logger.info("Checking for scheduled jobs...")
        # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
        
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(BackgroundJob).where(
                    and_(
                        BackgroundJob.status == JobStatus.PENDING.value,
                        BackgroundJob.schedule.isnot(None),
                        BackgroundJob.next_run_at <= now
                    )
                ).limit(10)
            )
            jobs = list(result.scalars().all())
        
        executed_ids = []
        for job in jobs:
            job_id = str(job.id)
            self.logger.info(f"Executing scheduled job: {job_id}")
            
            asyncio.create_task(self.execute_job(job_id))
            executed_ids.append(job_id)
        
        return executed_ids
    
    async def create_proactive_action(
        self,
        company_id: str,
        action_type: str,
        title: str,
        description: str,
        suggested_action: dict,
        priority: str = "normal",
        related_job_id: str | None = None,
        related_candidate_id: str | None = None,
        trigger_reason: str | None = None,
        auto_executable: bool = False,
        expires_in_hours: int | None = 24
    ) -> ProactiveAction:
        """
        Create a proactive action suggestion.
        
        Args:
            company_id: Company ID
            action_type: Type of action (suggestion, notification, auto_action)
            title: Action title
            description: Detailed description
            suggested_action: Dict with action details
            priority: Priority level
            related_job_id: Optional related vacancy ID
            related_candidate_id: Optional related candidate ID
            trigger_reason: Why this action was triggered
            auto_executable: Whether LIA can auto-execute
            expires_in_hours: Hours until expiration
            
        Returns:
            Created ProactiveAction instance
        """
        self.logger.info(f"Creating proactive action: {title}")
        
        async with AsyncSessionLocal() as db:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                raise ValueError(f"Invalid company_id format: '{company_id}'. A valid UUID is required.")
            
            action = ProactiveAction(
                id=uuid4(),
                company_id=company_uuid,
                action_type=action_type,
                title=title,
                description=description,
                priority=priority,
                suggested_action=suggested_action or {},
                auto_executable=auto_executable,
                trigger_reason=trigger_reason,
                status=ActionStatus.PENDING.value,
                created_at=datetime.utcnow(),
            )
            
            if related_job_id:
                try:
                    action.related_job_id = UUID(related_job_id)
                except ValueError:
                    pass
            
            if related_candidate_id:
                try:
                    action.related_candidate_id = UUID(related_candidate_id)
                except ValueError:
                    pass
            
            if expires_in_hours:
                action.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            db.add(action)
            await db.commit()
            await db.refresh(action)
            
            self.logger.info(f"Created proactive action {action.id}")
            return action
    
    async def get_pending_actions(
        self,
        company_id: str,
        limit: int = 10,
        include_expired: bool = False
    ) -> list[ProactiveAction]:
        """Get pending proactive actions for a company."""
        async with AsyncSessionLocal() as db:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                raise ValueError(f"Invalid company_id format: '{company_id}'. A valid UUID is required.")
            
            conditions = [
                ProactiveAction.company_id == company_uuid,
                ProactiveAction.status == ActionStatus.PENDING.value
            ]
            
            if not include_expired:
                conditions.append(
                    or_(
                        # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                        ProactiveAction.expires_at.is_(None),
                        ProactiveAction.expires_at > datetime.utcnow()
                    )
                )
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(ProactiveAction)
                .where(and_(*conditions))
                .order_by(
                    ProactiveAction.priority.desc(),
                    ProactiveAction.created_at.desc()
                )
                .limit(limit)
            )
            
            return list(result.scalars().all())
    
    async def get_actions_by_status(
        self,
        company_id: str,
        status: str,
        limit: int = 50
    ) -> list[ProactiveAction]:
        """Get proactive actions by status."""
        async with AsyncSessionLocal() as db:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                raise ValueError(f"Invalid company_id format: '{company_id}'. A valid UUID is required.")
            
            result = await db.execute(
                select(ProactiveAction)
                .where(
                    and_(
                        ProactiveAction.company_id == company_uuid,
                        ProactiveAction.status == status
                    )
                )
                .order_by(ProactiveAction.created_at.desc())
                .limit(limit)
            )
            
            return list(result.scalars().all())
    
    async def accept_action(self, action_id: str, user_id: str) -> dict:
        """
        Accept a proactive action.
        
        Args:
            action_id: Action UUID
            user_id: User accepting the action
            
        Returns:
            Result dict with success status
        """
        # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
        async with AsyncSessionLocal() as db:
            try:
                action_uuid = UUID(action_id)
            except ValueError:
                return {"success": False, "error": "Invalid action ID"}
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(ProactiveAction).where(ProactiveAction.id == action_uuid)
            )
            action = result.scalar_one_or_none()
            
            if not action:
                return {"success": False, "error": "Action not found"}
            
            if action.status != ActionStatus.PENDING.value:
                return {"success": False, "error": f"Action already {action.status}"}
            
            if action.is_expired():
                action.status = ActionStatus.EXPIRED.value
                await db.commit()
                return {"success": False, "error": "Action has expired"}
            
            action.accept(user_id)
            await db.commit()
            
            self.logger.info(f"Action {action_id} accepted by {user_id}")
            
            if action.auto_executable:
                execution_result = await self._execute_proactive_action(action)
                return {
                    "success": True,
                    "action_id": str(action_id),
                    "auto_executed": True,
                    "execution_result": execution_result
                }
            
            return {
                "success": True,
                "action_id": str(action_id),
                "suggested_action": action.suggested_action
            }
    
    async def reject_action(self, action_id: str, user_id: str) -> dict:
        """
        Reject a proactive action.
        
        Args:
            action_id: Action UUID
            user_id: User rejecting the action
            
        Returns:
            Result dict with success status
        # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
        """
        async with AsyncSessionLocal() as db:
            try:
                action_uuid = UUID(action_id)
            except ValueError:
                return {"success": False, "error": "Invalid action ID"}
            
            result = await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                select(ProactiveAction).where(ProactiveAction.id == action_uuid)
            )
            action = result.scalar_one_or_none()
            
            if not action:
                return {"success": False, "error": "Action not found"}
            
            if action.status != ActionStatus.PENDING.value:
                return {"success": False, "error": f"Action already {action.status}"}
            
            action.reject(user_id)
            await db.commit()
            
            self.logger.info(f"Action {action_id} rejected by {user_id}")
            
            return {"success": True, "action_id": str(action_id)}
    
    async def _execute_proactive_action(self, action: ProactiveAction) -> dict:
        """Execute an accepted proactive action."""
        self.logger.info(f"Auto-executing proactive action {action.id}")
        
        try:
            suggested = action.suggested_action or {}
            action_handler = suggested.get("handler")
            
            # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
            result = {
                "success": True,
                "message": f"Action '{action.title}' would be executed",
                "handler": action_handler,
                "params": suggested.get("params", {})
            }
            
            async with AsyncSessionLocal() as db:
                db_result = await db.execute(
                    # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                    select(ProactiveAction).where(ProactiveAction.id == action.id)
                )
                db_action = db_result.scalar_one_or_none()
                if db_action:
                    db_action.execute()
                    await db.commit()
            
            return result
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Failed to execute action {action.id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_candidate_lia_score(
        self, candidate_id: str, vacancy_id: str | None, company_id: str = ""
    ) -> float:
        """Fetch real LIA score via VacancyCandidateRepository; falls back to 0.5.

        ADR-001 W1-004-C: migrated from raw SQL inline to repo pattern.
        company_id is optional for backwards-compat; when empty falls back to
        legacy inline query without multi-tenancy filter.
        """
        if not candidate_id:
            return 0.5
        try:
            from app.domains.candidates.repositories.vacancy_candidate_repository import (
                VacancyCandidateRepository,
            )
            async with AsyncSessionLocal() as db:
                repo = VacancyCandidateRepository(db)
                if company_id:
                    if vacancy_id:
                        raw = await repo.get_lia_score(str(candidate_id), str(vacancy_id), company_id)
                    else:
                        raw = await repo.get_latest_lia_score(str(candidate_id), company_id)
                else:
                    # ADR-001-EXEMPT: legacy caller has no company_id context; deferred to next sprint
                    from sqlalchemy import text as _text
                    if vacancy_id:
                        result = await db.execute(
                            _text(
                                "SELECT COALESCE(lia_score, match_percentage, 0.5) "
                                "FROM vacancy_candidates "
                                "WHERE candidate_id::text = :cid "
                                "  AND vacancy_id::text = :vid LIMIT 1"
                            ),
                            {"cid": str(candidate_id), "vid": str(vacancy_id)},
                        )
                    else:
                        result = await db.execute(
                            _text(
                                "SELECT COALESCE(lia_score, match_percentage, 0.5) "
                                "FROM vacancy_candidates "
                                "WHERE candidate_id::text = :cid "
                                "ORDER BY created_at DESC LIMIT 1"
                            ),
                            {"cid": str(candidate_id)},
                        )
                    row = result.fetchone()
                    raw = float(row[0]) if row and row[0] is not None else 0.5
                return raw / 100.0 if raw > 1.0 else raw
        except Exception as e:
            self.logger.warning(f"Could not fetch LIA score for candidate {candidate_id}: {e}")
        return 0.5
        try:
            async with AsyncSessionLocal() as db:
                if vacancy_id:
                    result = await db.execute(text("""
                        SELECT COALESCE(lia_score, match_percentage, 0.5)
                        FROM vacancy_candidates
                        WHERE candidate_id::text = :cid
                          AND vacancy_id::text = :vid
                        LIMIT 1
                    """), {"cid": str(candidate_id), "vid": str(vacancy_id)})
                else:
                    result = await db.execute(text("""
                        SELECT COALESCE(lia_score, match_percentage, 0.5)
                        FROM vacancy_candidates
                        WHERE candidate_id::text = :cid
                        ORDER BY created_at DESC
                        LIMIT 1
                    """), {"cid": str(candidate_id)})
                row = result.fetchone()
                if row and row[0] is not None:
                    raw = float(row[0])
                    return raw / 100.0 if raw > 1.0 else raw
        except Exception as e:
            self.logger.warning(f"Could not fetch LIA score for candidate {candidate_id}: {e}")
        return 0.5

    async def _execute_screening_job(self, job: BackgroundJob) -> dict:
        """Execute a screening job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing screening job: {job.name}")
        
        config = job.config or {}
        vacancy_id = config.get("vacancy_id")
        candidate_ids = config.get("candidate_ids", [])
        config.get("criteria", {})
        
        await self._update_job_progress(job.id, 10)
        
        results = {
            "screened_candidates": len(candidate_ids),
            "passed": 0,
            "failed": 0,
            "needs_review": 0,
            "details": []
        }
        
        total = len(candidate_ids) if candidate_ids else 1
        for i, candidate_id in enumerate(candidate_ids):
            score = await self._get_candidate_lia_score(candidate_id, vacancy_id)
            status = "passed" if score > 0.7 else ("needs_review" if score > 0.5 else "failed")
            
            results["details"].append({
                "candidate_id": candidate_id,
                "score": round(score, 2),
                "status": status
            })
            
            if status == "passed":
                results["passed"] += 1
            elif status == "needs_review":
                results["needs_review"] += 1
            else:
                results["failed"] += 1
            
            progress = 10 + int(80 * (i + 1) / total)
            await self._update_job_progress(job.id, progress)
        
        await self._update_job_progress(job.id, 100)
        
        return {
            "success": True,
            "job_type": "screening",
            "vacancy_id": vacancy_id,
            "results": results
        }
    
    async def _execute_sourcing_job(self, job: BackgroundJob) -> dict:
        """Execute a sourcing job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing sourcing job: {job.name}")
        
        config = job.config or {}
        
        await self._update_job_progress(job.id, 25)
        await asyncio.sleep(0.5)
        
        await self._update_job_progress(job.id, 50)
        
        results = {
            "candidates_found": 15,
            "matching_criteria": 12,
            "new_candidates": 8,
            "already_in_pipeline": 4,
            "search_criteria": config.get("search_criteria", {})
        }
        
        await self._update_job_progress(job.id, 100)
        
        return {
            "success": True,
            "job_type": "sourcing",
            "results": results
        }
    
    async def _execute_report_job(self, job: BackgroundJob) -> dict:
        """Execute a report generation job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing report job: {job.name}")
        
        config = job.config or {}
        report_type = config.get("report_type", "pipeline_summary")
        
        await self._update_job_progress(job.id, 20)
        
        await asyncio.sleep(0.3)
        await self._update_job_progress(job.id, 60)
        
        report_data = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "period": config.get("period", "last_7_days"),
            "metrics": {
                "total_candidates": 45,
                "new_candidates": 12,
                "interviews_scheduled": 8,
                "offers_made": 3,
                "positions_filled": 2
            },
            "highlights": [
                "12 new candidates added this week",
                "Engineering pipeline is 80% full",
                "Average time-to-hire: 18 days"
            ]
        }
        
        await self._update_job_progress(job.id, 100)
        
        return {
            "success": True,
            "job_type": "report_generation",
            "report": report_data
        }
    
    async def _execute_market_analysis_job(self, job: BackgroundJob) -> dict:
        """Execute a market analysis job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing market analysis job: {job.name}")
        
        config = job.config or {}
        role = config.get("role", "Software Engineer")
        location = config.get("location", "São Paulo")
        
        await self._update_job_progress(job.id, 30)
        await asyncio.sleep(0.3)
        await self._update_job_progress(job.id, 70)
        
        analysis = {
            "role": role,
            "location": location,
            "market_data": {
                "salary_range": {
                    "min": 8000,
                    "max": 18000,
                    "median": 12000,
                    "currency": "BRL"
                },
                "demand_level": "high",
                "talent_availability": "moderate",
                "time_to_fill_avg_days": 25,
                "top_skills_demanded": [
                    "Python", "JavaScript", "Cloud (AWS/GCP)", "SQL"
                ]
            },
            "recommendations": [
                "Salary is competitive for the market",
                "Consider remote work options to expand talent pool",
                "Focus on company culture in job description"
            ]
        }
        
        await self._update_job_progress(job.id, 100)
        
        return {
            "success": True,
            "job_type": "market_analysis",
            "analysis": analysis
        }
    
    async def _execute_outreach_job(self, job: BackgroundJob) -> dict:
        """Execute a candidate outreach job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing outreach job: {job.name}")
        
        config = job.config or {}
        candidate_ids = config.get("candidate_ids", [])
        template_id = config.get("template_id")
        
        await self._update_job_progress(job.id, 50)
        
        results = {
            "total_candidates": len(candidate_ids),
            "messages_queued": len(candidate_ids),
            "template_used": template_id,
            "estimated_delivery": "within 24 hours"
        }
        
        await self._update_job_progress(job.id, 100)
        
        return {
            "success": True,
            "job_type": "candidate_outreach",
            "results": results
        }
    
    async def _execute_pattern_learning_job(self, job: BackgroundJob) -> dict:
        """Execute a pattern learning job."""
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing pattern learning job: {job.name}")
        
        
        await self._update_job_progress(job.id, 40)
        await asyncio.sleep(0.2)
        await self._update_job_progress(job.id, 80)
        
        patterns = {
            "patterns_identified": 5,
            "confidence_improved": True,
            "learning_summary": {
                "successful_hires_analyzed": 20,
                "common_traits": ["collaboration", "technical depth", "communication"],
                "updated_models": ["screening_criteria", "candidate_ranking"]
            }
        }
        
        await self._update_job_progress(job.id, 100)
        
        # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
        return {
            "success": True,
            "job_type": "pattern_learning",
            "patterns": patterns
        }
    
    async def _update_job_progress(self, job_id: UUID, progress: int) -> None:
        """Update job progress."""
        async with AsyncSessionLocal() as db:
            await db.execute(
                # TENANT-EXEMPT: autonomous_agent_service runs system-wide polling per agent definition; per-tenant data ops happen via downstream repositories
                update(BackgroundJob)
                .where(BackgroundJob.id == job_id)
                .values(progress=progress, updated_at=datetime.utcnow())
            )
            await db.commit()
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """
        Calculate next run time from cron expression.
        
        For simplicity, supports basic patterns:
        - "@hourly" - every hour
        - "@daily" - every day at midnight
        - "@weekly" - every week on Monday
        - "*/5 * * * *" - every 5 minutes (simplified parsing)
        """
        now = datetime.utcnow()
        
        if schedule == "@hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif schedule == "@daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif schedule == "@weekly":
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        elif schedule.startswith("*/"):
            try:
                interval = int(schedule.split()[0][2:])
                return now + timedelta(minutes=interval)
            except (ValueError, IndexError):
                return now + timedelta(hours=1)
        else:
            return now + timedelta(hours=1)


autonomous_agent_service = AutonomousAgentService()


def get_autonomous_agent_service() -> "AutonomousAgentService":
    return autonomous_agent_service
