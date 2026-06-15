"""

# ADR-001-EXEMPT: Pipeline stage service handles CandidateStageHistory
# transitions + ATSStageMapping resolution (multi-source pipeline state
# machine). Tenant scope established by caller via vacancy_id ownership.
# TODO Sprint 6: extract to CandidateStageHistoryRepository +  # R-048: needs owner + ticket
# ATSStageMappingRepository.

Pipeline Stage Service - Centralized stage/sub-status management.

This service handles all stage transitions for candidates:
- Validates transitions against allowed rules
- Records history for auditing
- Triggers ATS synchronization
- Updates Kanban/UI state

All agents and UI components should use this service for stage changes.
Never update stage/sub-status directly in the database.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import derive_company_from_context
from app.core.database import AsyncSessionLocal
from app.domains.ats_integration.services.ats_sync_service import ats_sync_service
from lia_models.candidate import VacancyCandidate
from lia_models.recruitment_stages import (
    DEFAULT_RECRUITMENT_STAGES,
    DEFAULT_SUB_STATUSES,
    ATSStageMapping,
    CandidateStageHistory,
    RecruitmentStage,
    RecruitmentSubStatus,
)

logger = logging.getLogger(__name__)

_event_dispatcher = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


class TransitionError(Exception):
    """Raised when a stage transition is not allowed."""
    pass


class PipelineStageService:
    """
    Central service for managing candidate stage transitions.
    
    Usage by agents:
    ```python
    service = PipelineStageService()
    result = await service.transition_candidate(
        vacancy_candidate_id="...",
        to_stage="interview_hr",
        to_sub_status="scheduled",
        triggered_by="scheduling_agent",
        reason="Entrevista agendada para 15/12"
    )
    ```
    
    The service will:
    1. Validate the transition is allowed
    2. Update the VacancyCandidate record
    3. Record history in CandidateStageHistory
    4. Trigger ATS sync if configured
    5. Trigger automations based on stage change
    6. Return result with sync status
    """
    
    def __init__(self):
        self._stage_cache: dict[str, list[RecruitmentStage]] = {}
        self._sub_status_cache: dict[str, list[RecruitmentSubStatus]] = {}
        self._automation_service = None
        self._data_request_service = None
    
    @property
    def data_request_service(self):
        """Lazy load DataRequestService to avoid circular imports."""
        if self._data_request_service is None:
            from app.domains.communication.services.data_request_service import data_request_service
            self._data_request_service = data_request_service
        return self._data_request_service
    
    @property
    def automation_service(self):
        """Lazy load AutomationService to avoid circular imports."""
        if self._automation_service is None:
            from app.domains.automation.services.automation_service import AutomationService
            self._automation_service = AutomationService()
        return self._automation_service
    
    async def transition_candidate(
        self,
        vacancy_candidate_id: str,
        to_stage: str,
        to_sub_status: str | None = None,
        triggered_by: str = "system",
        triggered_by_user_id: str | None = None,
        source_agent: str | None = None,
        reason: str | None = None,
        notes: str | None = None,
        context: dict[str, Any] | None = None,
        force: bool = False,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Transition a candidate to a new stage/sub-status.
        
        Args:
            vacancy_candidate_id: ID of the VacancyCandidate record
            to_stage: Target stage name (e.g., "interview_hr")
            to_sub_status: Target sub-status name (optional)
            triggered_by: Who triggered the transition (agent name, "user", "ats_sync")
            triggered_by_user_id: User ID if triggered by a user
            source_agent: Agent name if triggered by an agent
            reason: Reason for the transition
            notes: Additional notes
            context: Additional context data
            force: Skip validation (use with caution)
            db: Database session (optional, will create if not provided)
            
        Returns:
            Dict with transition result, history entry, and sync status
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            vacancy_candidate = await db.get(VacancyCandidate, uuid.UUID(vacancy_candidate_id))
            if not vacancy_candidate:
                raise ValueError(f"VacancyCandidate not found: {vacancy_candidate_id}")
            
            if context is None:
                context = {}
            
            company_id = await derive_company_from_context(context, db, fallback=None)
            
            candidate_company = vacancy_candidate.company_id
            if candidate_company != company_id:
                raise PermissionError(
                    f"Access denied: Candidate belongs to company '{candidate_company}', "
                    f"but request is for company '{company_id}'"
                )
            
            stages = await self._get_company_stages(db, company_id)
            to_stage_obj = next((s for s in stages if s.name == to_stage), None)
            if not to_stage_obj:
                raise ValueError(f"Stage not found: {to_stage}")
            
            from_stage = vacancy_candidate.stage
            from_sub_status = vacancy_candidate.status
            
            if not force:
                is_valid, error_msg = await self._validate_transition(
                    db, company_id, from_stage, to_stage
                )
                if not is_valid:
                    raise TransitionError(error_msg)

                # P1-BLOCKING: bloquear transicao se existe DataRequest obrigatorio pendente
                # na etapa de origem. force=True bypass (usado por agentes com permissao).
                blocking_req = await self.data_request_service.find_blocking_pending_request(
                    db=db,
                    candidate_id=vacancy_candidate.candidate_id,
                    vacancy_id=vacancy_candidate.vacancy_id,
                    stage=from_stage,
                )
                if blocking_req:
                    pct = int(blocking_req.get_completion_percentage())
                    raise TransitionError(
                        f"Transicao bloqueada: solicitacao de dados obrigatoria pendente "
                        f"na etapa {from_stage} "
                        f"(request_id={blocking_req.id}, {pct}% preenchido). "
                        "O candidato deve preencher os dados solicitados antes de avancar."
                    )

            to_sub_status_obj = None
            if to_sub_status:
                sub_statuses = await self._get_stage_sub_statuses(db, str(to_stage_obj.id))
                to_sub_status_obj = next((s for s in sub_statuses if s.name == to_sub_status), None)
            
            if not to_sub_status_obj:
                sub_statuses = await self._get_stage_sub_statuses(db, str(to_stage_obj.id))
                to_sub_status_obj = next((s for s in sub_statuses if s.is_default), None)
            
            vacancy_candidate.stage = to_stage
            # Task #1303: persist the structural stage link so the SLA detector
            # can join by id instead of fragile name matching.
            vacancy_candidate.recruitment_stage_id = to_stage_obj.id
            vacancy_candidate.status = to_sub_status or (to_sub_status_obj.name if to_sub_status_obj else "default")
            vacancy_candidate.updated_at = datetime.utcnow()
            if from_stage != to_stage:
                vacancy_candidate.stage_entered_at = datetime.utcnow()
            
            from_stage_obj = next((s for s in stages if s.name == from_stage), None) if from_stage else None
            from_sub_status_obj = None
            if from_stage_obj and from_sub_status:
                from_sub_statuses = await self._get_stage_sub_statuses(db, str(from_stage_obj.id))
                from_sub_status_obj = next((s for s in from_sub_statuses if s.name == from_sub_status), None)
            
            time_in_previous = None
            if from_stage:
                last_transition = await db.execute(
                    select(CandidateStageHistory)
                    .where(CandidateStageHistory.vacancy_candidate_id == uuid.UUID(vacancy_candidate_id))
                    .order_by(CandidateStageHistory.created_at.desc())
                    .limit(1)
                )
                last_entry = last_transition.scalar_one_or_none()
                if last_entry:
                    time_in_previous = (datetime.utcnow() - last_entry.created_at).total_seconds() / 3600
            
            history_entry = CandidateStageHistory(
                vacancy_candidate_id=uuid.UUID(vacancy_candidate_id),
                vacancy_id=vacancy_candidate.vacancy_id,
                candidate_id=vacancy_candidate.candidate_id,
                company_id=company_id,
                from_stage_id=from_stage_obj.id if from_stage_obj else None,
                from_stage_name=from_stage,
                from_sub_status_id=from_sub_status_obj.id if from_sub_status_obj else None,
                from_sub_status_name=from_sub_status,
                to_stage_id=to_stage_obj.id,
                to_stage_name=to_stage,
                to_sub_status_id=to_sub_status_obj.id if to_sub_status_obj else None,
                to_sub_status_name=to_sub_status_obj.name if to_sub_status_obj else None,
                transition_type="agent" if source_agent else ("user" if triggered_by_user_id else "system"),
                triggered_by=triggered_by,
                triggered_by_user_id=triggered_by_user_id,
                source_agent=source_agent,
                reason=reason,
                notes=notes,
                time_in_previous_stage_hours=time_in_previous,
                context=context or {},
            )
            
            db.add(history_entry)
            
            ats_sync_result = None
            ats_type = context.get("ats_type")
            if not ats_type:
                logger.debug(
                    f"ATS sync skipped: no ats_type in context for transition "
                    f"{from_stage} → {to_stage} (candidate={vacancy_candidate.candidate_id})"
                )
            else:
                try:
                    ats_sync_result = await ats_sync_service.trigger_status_change(
                        source_agent=source_agent or triggered_by,
                        ats_type=ats_type,
                        candidate_id=str(vacancy_candidate.candidate_id),
                        job_id=str(vacancy_candidate.vacancy_id),
                        old_status=from_stage or "",
                        new_status=to_stage,
                        reason=reason
                    )
                    
                    history_entry.ats_sync_triggered = True
                    history_entry.ats_sync_result = ats_sync_result.get("result", "unknown")
                    history_entry.ats_sync_details = ats_sync_result
                    
                except Exception as e:
                    logger.error(f"ATS sync failed: {e}")
                    history_entry.ats_sync_triggered = True
                    history_entry.ats_sync_result = "error"
                    history_entry.ats_sync_details = {"error": str(e)}
            
            await db.commit()
            
            logger.info(
                f"✅ Stage transition: {from_stage} → {to_stage} "
                f"(candidate={vacancy_candidate.candidate_id}, agent={source_agent})"
            )
            
            automation_result = None
            try:
                trigger_data = {
                    "candidate_id": str(vacancy_candidate.candidate_id),
                    "vacancy_id": str(vacancy_candidate.vacancy_id),
                    "vacancy_candidate_id": vacancy_candidate_id,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "from_sub_status": from_sub_status,
                    "to_sub_status": to_sub_status_obj.name if to_sub_status_obj else None,
                    "triggered_by": triggered_by,
                    "triggered_by_user_id": triggered_by_user_id,
                    "source_agent": source_agent,
                    "reason": reason,
                }
                
                automation_result = await self.automation_service.trigger_automation(
                    trigger_type="candidate_stage_changed",
                    trigger_data=trigger_data,
                    company_id=company_id,
                    db=None
                )
                
                if automation_result.get("automations_executed", 0) > 0:
                    logger.info(
                        f"🤖 Automations triggered: {automation_result['automations_executed']} executed "
                        f"for transition {from_stage} → {to_stage}"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Failed to trigger automations for stage transition: {e}")
            
            event_dispatch_result = None
            try:
                dispatcher = get_event_dispatcher()
                event_dispatch_result = await dispatcher.on_stage_changed(
                    candidate_id=str(vacancy_candidate.candidate_id),
                    vacancy_id=str(vacancy_candidate.vacancy_id),
                    company_id=company_id,
                    new_stage=to_stage,
                    previous_stage=from_stage,
                    triggered_by=triggered_by,
                    source_agent=source_agent,
                    sync_to_ats=ats_type is not None
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to dispatch stage change event: {e}")
            
            data_request_trigger_result = None
            if from_stage != to_stage:
                try:
                    data_request_trigger_result = await self.check_data_request_triggers(
                        candidate_id=str(vacancy_candidate.candidate_id),
                        new_stage=to_stage,
                        vacancy_id=str(vacancy_candidate.vacancy_id),
                        company_id=company_id,
                        triggered_by=triggered_by,
                        db=db,
                    )
                    
                    if data_request_trigger_result and data_request_trigger_result.get("triggered"):
                        logger.info(
                            f"📋 Data request auto-triggered for stage '{to_stage}': "
                            f"request_id={data_request_trigger_result.get('data_request_id')}"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to check data request triggers: {e}")
                    data_request_trigger_result = {"triggered": False, "error": str(e)}
            
            return {
                "success": True,
                "vacancy_candidate_id": vacancy_candidate_id,
                "transition": {
                    "from_stage": from_stage,
                    "from_sub_status": from_sub_status,
                    "to_stage": to_stage,
                    "to_sub_status": to_sub_status_obj.name if to_sub_status_obj else None,
                },
                "history_id": str(history_entry.id),
                "time_in_previous_stage_hours": time_in_previous,
                "ats_sync": ats_sync_result,
                "automation_result": automation_result,
                "event_dispatch_result": event_dispatch_result,
                "data_request_trigger": data_request_trigger_result,
                "display_status": self._format_display_status(to_stage_obj, to_sub_status_obj),
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Stage transition failed: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    async def update_sub_status(
        self,
        vacancy_candidate_id: str,
        to_sub_status: str,
        triggered_by: str = "system",
        source_agent: str | None = None,
        reason: str | None = None,
        context: dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Update only the sub-status without changing the main stage.
        
        Use this for granular updates like:
        - "Triagem" → "Aguardando Retorno"
        - "Entrevista RH" → "Confirmada"
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            vacancy_candidate = await db.get(VacancyCandidate, uuid.UUID(vacancy_candidate_id))
            if not vacancy_candidate:
                raise ValueError(f"VacancyCandidate not found: {vacancy_candidate_id}")
            
            current_stage = vacancy_candidate.stage
            
            return await self.transition_candidate(
                vacancy_candidate_id=vacancy_candidate_id,
                to_stage=current_stage,
                to_sub_status=to_sub_status,
                triggered_by=triggered_by,
                source_agent=source_agent,
                reason=reason,
                context=context,
                force=True,
                db=db
            )
        finally:
            if should_close:
                await db.close()
    
    async def get_candidate_stage_info(
        self,
        vacancy_candidate_id: str,
        company_id: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get current stage/sub-status info for a candidate.
        
        Returns display-ready information for UI rendering.
        If company_id is provided, validates the candidate belongs to that company.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            vacancy_candidate = await db.get(VacancyCandidate, uuid.UUID(vacancy_candidate_id))
            if not vacancy_candidate:
                return None
            
            effective_company_id = company_id
            
            candidate_company = vacancy_candidate.company_id
            if candidate_company != effective_company_id:
                return None
            
            stages = await self._get_company_stages(db, effective_company_id)
            current_stage_obj = next((s for s in stages if s.name == vacancy_candidate.stage), None)
            
            current_sub_status_obj = None
            if current_stage_obj:
                sub_statuses = await self._get_stage_sub_statuses(db, str(current_stage_obj.id))
                current_sub_status_obj = next(
                    (s for s in sub_statuses if s.name == vacancy_candidate.status), None
                )
            
            return {
                "stage": {
                    "name": vacancy_candidate.stage,
                    "display_name": current_stage_obj.display_name if current_stage_obj else vacancy_candidate.stage,
                    "color": current_stage_obj.color if current_stage_obj else "#6B7280",
                    "icon": current_stage_obj.icon if current_stage_obj else "circle",
                    "is_final": current_stage_obj.is_final if current_stage_obj else False,
                },
                "sub_status": {
                    "name": vacancy_candidate.status,
                    "display_name": current_sub_status_obj.display_name if current_sub_status_obj else vacancy_candidate.status,
                    "is_waiting": current_sub_status_obj.is_waiting if current_sub_status_obj else False,
                    "waiting_for": current_sub_status_obj.waiting_for if current_sub_status_obj else None,
                } if current_sub_status_obj else None,
                "display_status": self._format_display_status(current_stage_obj, current_sub_status_obj),
                "action_behavior": current_stage_obj.action_behavior if current_stage_obj else "passive",
                "next_stages": [],  # DEPRECATED: Free movement enabled
            }
        finally:
            if should_close:
                await db.close()
    
    async def get_candidate_history(
        self,
        vacancy_candidate_id: str,
        company_id: str | None = None,
        limit: int = 50,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Get stage transition history for a candidate.
        
        If company_id is provided, filters by company to ensure tenant isolation.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            if company_id:
                vacancy_candidate = await db.get(VacancyCandidate, uuid.UUID(vacancy_candidate_id))
                if not vacancy_candidate:
                    return []
                candidate_company = vacancy_candidate.company_id
                if candidate_company != company_id:
                    return []
            
            query = select(CandidateStageHistory).where(
                CandidateStageHistory.vacancy_candidate_id == uuid.UUID(vacancy_candidate_id)
            )
            
            if company_id:
                query = query.where(CandidateStageHistory.company_id == company_id)
            
            result = await db.execute(
                query.order_by(CandidateStageHistory.created_at.desc()).limit(limit)
            )
            entries = result.scalars().all()
            return [e.to_dict() for e in entries]
        finally:
            if should_close:
                await db.close()
    
    async def map_ats_stage_to_wedotalent(
        self,
        company_id: str,
        ats_type: str,
        ats_stage_name: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """
        Map an ATS stage to the corresponding WedoTalent stage.
        
        Used when syncing candidates from ATS to WedoTalent.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(ATSStageMapping)
                .where(and_(
                    ATSStageMapping.company_id == company_id,
                    ATSStageMapping.ats_type == ats_type,
                    ATSStageMapping.ats_stage_name == ats_stage_name,
                    ATSStageMapping.is_active
                ))
            )
            mapping = result.scalar_one_or_none()
            
            if mapping:
                return {
                    "wedotalent_stage_id": str(mapping.wedotalent_stage_id),
                    "wedotalent_sub_status_id": str(mapping.wedotalent_sub_status_id) if mapping.wedotalent_sub_status_id else None,
                }
            
            return None
        finally:
            if should_close:
                await db.close()
    
    async def map_wedotalent_stage_to_ats(
        self,
        company_id: str,
        ats_type: str,
        wedotalent_stage: str,
        db: AsyncSession | None = None
    ) -> str | None:
        """
        Map a WedoTalent stage to the corresponding ATS stage for sync.
        
        Returns the default ATS stage name if multiple mappings exist.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            stages = await self._get_company_stages(db, company_id)
            stage_obj = next((s for s in stages if s.name == wedotalent_stage), None)
            if not stage_obj:
                return None
            
            result = await db.execute(
                select(ATSStageMapping)
                .where(and_(
                    ATSStageMapping.company_id == company_id,
                    ATSStageMapping.ats_type == ats_type,
                    ATSStageMapping.wedotalent_stage_id == stage_obj.id,
                    ATSStageMapping.is_active,
                    ATSStageMapping.is_default_for_sync
                ))
            )
            mapping = result.scalar_one_or_none()
            
            if mapping:
                return mapping.ats_stage_name
            
            result = await db.execute(
                select(ATSStageMapping)
                .where(and_(
                    ATSStageMapping.company_id == company_id,
                    ATSStageMapping.ats_type == ats_type,
                    ATSStageMapping.wedotalent_stage_id == stage_obj.id,
                    ATSStageMapping.is_active
                ))
                .order_by(ATSStageMapping.priority.desc())
                .limit(1)
            )
            mapping = result.scalar_one_or_none()
            
            return mapping.ats_stage_name if mapping else None
        finally:
            if should_close:
                await db.close()
    
    async def initialize_company_stages(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Initialize default stages for a new company.
        
        Called during company setup (Phase 0).
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            existing = await db.execute(
                select(RecruitmentStage).where(RecruitmentStage.company_id == company_id)
            )
            if existing.scalars().first():
                logger.info(f"Company {company_id} already has stages configured")
                return []
            
            created_stages = []
            for stage_data in DEFAULT_RECRUITMENT_STAGES:
                data = {k: v for k, v in stage_data.items() if k != 'is_system'}
                stage = RecruitmentStage(
                    company_id=company_id,
                    is_system=stage_data.get('is_system', True),
                    **data
                )
                db.add(stage)
                await db.flush()
                created_stages.append(stage)
                
                stage_name = stage_data["name"]
                if stage_name in DEFAULT_SUB_STATUSES:
                    for i, sub_data in enumerate(DEFAULT_SUB_STATUSES[stage_name]):
                        sub_status = RecruitmentSubStatus(
                            stage_id=stage.id,
                            company_id=company_id,
                            sub_status_order=i,
                            **sub_data
                        )
                        db.add(sub_status)
            
            await db.commit()
            logger.info(f"Initialized {len(created_stages)} stages for company {company_id}")
            
            return [s.to_dict() for s in created_stages]
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to initialize stages: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    async def _get_company_stages(
        self,
        db: AsyncSession,
        company_id: str
    ) -> list[RecruitmentStage]:
        """Get stages for a company, with caching."""
        result = await db.execute(
            select(RecruitmentStage)
            .where(and_(
                RecruitmentStage.company_id == company_id,
                RecruitmentStage.is_active
            ))
            .order_by(RecruitmentStage.stage_order)
        )
        return result.scalars().all()
    
    async def _get_stage_sub_statuses(
        self,
        db: AsyncSession,
        stage_id: str
    ) -> list[RecruitmentSubStatus]:
        """Get sub-statuses for a stage."""
        result = await db.execute(
            select(RecruitmentSubStatus)
            .where(and_(
                RecruitmentSubStatus.stage_id == uuid.UUID(stage_id),
                RecruitmentSubStatus.is_active
            ))
            .order_by(RecruitmentSubStatus.sub_status_order)
        )
        return result.scalars().all()
    
    async def _validate_transition(
        self,
        db: AsyncSession,
        company_id: str,
        from_stage: str | None,
        to_stage: str
    ) -> tuple[bool, str | None]:
        """
        Validate if a stage transition is allowed.
        
        UPDATED: Free movement enabled. Any stage can transition to any other stage.
        The action_behavior of the destination stage determines what actions are triggered.
        Validation only checks that the target stage exists.
        
        Returns (is_valid, error_message).
        """
        if not from_stage:
            return (True, None)
        
        stages = await self._get_company_stages(db, company_id)
        to_stage_obj = next((s for s in stages if s.name == to_stage), None)
        
        if not to_stage_obj:
            return (False, f"Etapa destino não encontrada: {to_stage}")
        
        return (True, None)
    
    def _format_display_status(
        self,
        stage: RecruitmentStage | None,
        sub_status: RecruitmentSubStatus | None
    ) -> str:
        """Format display status for UI (e.g., "Triagem › Aguardando Retorno")."""
        if not stage:
            return "Desconhecido"
        
        if sub_status:
            return f"{stage.display_name} › {sub_status.display_name}"
        
        return stage.display_name
    
    async def check_data_request_triggers(
        self,
        candidate_id: str,
        new_stage: str,
        vacancy_id: str | None,
        company_id: str,
        triggered_by: str = "system",
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """
        Check if the new stage has automatic data request triggers configured.
        
        Creates a DataRequest automatically if:
        1. The stage has a trigger configured (VacancyDataRequestConfig or company template)
        2. No pending request already exists for this candidate/stage
        
        Priority order:
        1. VacancyDataRequestConfig.stage_configs (vacancy-specific)
        2. DataRequestTemplate with trigger_stage (company default)
        3. DEFAULT_STAGE_FIELD_MAPPINGS (system fallback, not auto-created)
        
        Args:
            candidate_id: Candidate ID
            new_stage: The stage the candidate is entering
            vacancy_id: Optional vacancy ID
            company_id: Company ID
            triggered_by: Who triggered this (for audit)
            db: Database session
            
        Returns:
            Dict with created data request info, or None if no trigger
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            trigger_config = await self.data_request_service.get_trigger_fields_for_stage(
                db=db,
                vacancy_id=uuid.UUID(vacancy_id) if vacancy_id else None,
                company_id=uuid.UUID(company_id) if isinstance(company_id, str) else company_id,
                stage=new_stage,
            )
            
            if not trigger_config:
                # P2-FASE4: fallback para data_fields.auto_collect na etapa
                try:
                    stages = await self._get_company_stages(db, company_id)
                    stage_obj = next((s for s in stages if s.name == new_stage), None)
                    raw_fields = (stage_obj.data_fields or []) if stage_obj else []
                    auto_fields = [f for f in raw_fields if f.get('auto_collect', False)]
                    if not auto_fields:
                        logger.debug(f"No data request trigger for stage '{new_stage}'")
                        return None
                    trigger_config = {
                        'source': 'data_fields_auto_collect',
                        'fields': [f['id'] for f in auto_fields],
                        'is_blocking': any(f.get('required', False) for f in auto_fields),
                        'trigger_type': 'stage_entry',
                        'template_id': None,
                    }
                    logger.info(f"P2-FASE4: {len(auto_fields)} auto_collect fields for '{new_stage}'")
                except Exception as _fa4_err:
                    logger.warning(f"Fase4 auto_collect fallback failed: {_fa4_err}")
                    return None
            
            if trigger_config.get("source") == "default_mapping":
                logger.debug(
                    f"Stage '{new_stage}' has default field mapping but no active trigger. "
                    "Skipping automatic data request creation."
                )
                return None
            
            candidate_uuid = uuid.UUID(candidate_id) if isinstance(candidate_id, str) else candidate_id
            vacancy_uuid = uuid.UUID(vacancy_id) if vacancy_id else None
            
            has_pending = await self.data_request_service.check_existing_pending_request(
                db=db,
                candidate_id=candidate_uuid,
                vacancy_id=vacancy_uuid,
                stage=new_stage,
            )
            
            if has_pending:
                logger.info(
                    f"Skipping data request trigger: pending request already exists "
                    f"for candidate {candidate_id} at stage '{new_stage}'"
                )
                return {
                    "triggered": False,
                    "reason": "pending_request_exists",
                    "stage": new_stage,
                }
            
            from lia_models.data_request import TriggerType
            
            trigger_type_str = trigger_config.get("trigger_type", "stage_entry")
            try:
                trigger_type = TriggerType(trigger_type_str)
            except ValueError:
                trigger_type = TriggerType.STAGE_ENTRY
            
            template_id = trigger_config.get("template_id")
            
            data_request = await self.data_request_service.create_data_request(
                db=db,
                company_id=uuid.UUID(company_id) if isinstance(company_id, str) else company_id,
                candidate_id=candidate_uuid,
                vacancy_id=vacancy_uuid,
                template_id=uuid.UUID(template_id) if template_id else None,
                fields=trigger_config.get("fields", []),
                trigger_type=trigger_type,
                trigger_stage=new_stage,
                is_blocking=trigger_config.get("is_blocking", False),
            )
            
            try:
                # P2-CANAL: ler canal preferido da empresa (preferred_data_channel)
                # em vez de hardcodar "email" — mesmo padrão de data_request.py:413
                _channels = ["email"]
                try:
                    from app.domains.hiring_policy.repositories.hiring_policy_repository import (
                        HiringPolicyRepository,
                    )
                    _hp_auto = await HiringPolicyRepository(db).get_by_company(
                        uuid.UUID(company_id) if isinstance(company_id, str) else company_id
                    )
                    _pref_auto = (
                        (_hp_auto.communication_rules or {}).get("preferred_data_channel")
                        if _hp_auto and _hp_auto.communication_rules
                        else None
                    )
                    _valid = frozenset({"email", "whatsapp", "voice", "web"})
                    if _pref_auto and _pref_auto in _valid:
                        _channels = [_pref_auto]
                except Exception as _chan_err:
                    logger.debug("Falha ao carregar canal preferido para auto-trigger: %s", _chan_err)
                await self.data_request_service.send_notification(
                    db=db,
                    data_request_id=data_request.id,
                    channels=_channels,
                )
            except Exception as e:
                logger.warning(f"Failed to send data request notification: {e}")
            
            logger.info(
                f"✅ Data request triggered: candidate={candidate_id}, "
                f"stage='{new_stage}', request_id={data_request.id}, "
                f"source={trigger_config.get('source')}"
            )
            
            return {
                "triggered": True,
                "data_request_id": str(data_request.id),
                "token": data_request.token,
                "stage": new_stage,
                "source": trigger_config.get("source"),
                "template_id": template_id,
                "is_blocking": trigger_config.get("is_blocking", False),
                "fields_count": len(trigger_config.get("fields", [])),
            }
            
        except Exception as e:
            logger.error(f"Error checking data request triggers: {e}", exc_info=True)
            return {
                "triggered": False,
                "error": str(e),
                "stage": new_stage,
            }
        finally:
            if should_close:
                await db.close()


pipeline_stage_service = PipelineStageService()


def get_pipeline_stage_service() -> "PipelineStageService":
    return pipeline_stage_service
