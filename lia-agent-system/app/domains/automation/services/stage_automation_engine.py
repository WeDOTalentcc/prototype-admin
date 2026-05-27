"""
Stage Automation Engine
Central engine that processes automation triggers based on stage transitions and events.
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.shared.automation.trigger_types_canonical import TriggerType

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.automation.repositories.communication_automation_repository import (
    CommunicationAutomationRepository,
)

logger = logging.getLogger(__name__)



@dataclass
class AutomationEvent:
    """Represents an automation event to be processed."""
    trigger_type: TriggerType
    candidate_id: str
    vacancy_id: str
    company_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.payload is None:
            self.payload = {}


class StageAutomationEngine:
    """
    Central engine for processing automation triggers.
    
    Features:
    - Event routing to appropriate handlers
    - Company-specific rule evaluation
    - Confidence scoring for AI suggestions
    - Audit logging
    - Batch processing support
    """
    
    def __init__(self):
        self._handlers: dict[TriggerType, Callable] = {}
        self._initialized = False
    
    def register_handler(self, trigger_type: TriggerType, handler: Callable):
        """Register a handler for a specific trigger type."""
        self._handlers[trigger_type] = handler
        logger.info(f"[ENGINE] Registered handler for {trigger_type.value}")
    
    def unregister_handler(self, trigger_type: TriggerType):
        """Unregister a handler for a trigger type."""
        if trigger_type in self._handlers:
            del self._handlers[trigger_type]
            logger.info(f"[ENGINE] Unregistered handler for {trigger_type.value}")
    
    def get_registered_handlers(self) -> list[str]:
        """Get list of registered trigger types."""
        return [t.value for t in self._handlers.keys()]
    
    async def process_event(
        self,
        event: AutomationEvent,
        db: AsyncSession,
        auto_execute: bool = False
    ) -> dict[str, Any]:
        """
        Process a single automation event.
        
        Args:
            event: The automation event to process
            db: Database session
            auto_execute: If True, execute actions automatically. 
                         If False, create AI suggestions for recruiter approval.
        
        Returns:
            Result dictionary with actions taken or suggestions created
        """
        logger.info(f"[ENGINE] Processing {event.trigger_type.value} for candidate {event.candidate_id}")
        
        is_valid = await self._validate_multi_tenancy(db, event)
        if not is_valid:
            logger.warning(f"[ENGINE] Multi-tenancy validation FAILED for company {event.company_id}")
            return {"success": False, "error": "Multi-tenancy validation failed"}
        
        rules = await self._get_automation_rules(db, event.company_id, event.trigger_type)
        
        should_execute = await self._evaluate_conditions(event, rules)
        
        if not should_execute:
            logger.info(f"[ENGINE] Conditions not met for {event.trigger_type.value}")
            return {"success": True, "skipped": True, "reason": "Conditions not met"}
        
        handler = self._handlers.get(event.trigger_type)
        if not handler:
            logger.warning(f"[ENGINE] No handler registered for {event.trigger_type.value}")
            return {"success": False, "error": f"No handler for {event.trigger_type.value}"}
        
        if auto_execute or rules.get("auto_execute", False):
            result = await self._execute_handler(handler, event, db)
        else:
            result = await self._create_suggestion(event, db, rules)
        
        await self._log_audit(event, result)
        
        return result
    
    async def process_batch(
        self,
        events: list[AutomationEvent],
        db: AsyncSession,
        auto_execute: bool = False
    ) -> list[dict[str, Any]]:
        """Process multiple events in batch."""
        results = []
        for event in events:
            try:
                result = await self.process_event(event, db, auto_execute)
                results.append(result)
            except Exception as e:
                logger.error(f"[ENGINE] Batch processing error for {event.trigger_type.value}: {e}")
                results.append({"success": False, "error": str(e)})
        return results
    
    async def _validate_multi_tenancy(self, db: AsyncSession, event: AutomationEvent) -> bool:
        """Validate that candidate/vacancy belong to company. FAIL CLOSED on errors."""
        try:
            from app.domains.automation.services.automation_handlers import validate_multi_tenancy
            result, error_msg = await validate_multi_tenancy(
                db, 
                event.candidate_id, 
                event.vacancy_id, 
                event.company_id
            )
            if not result:
                logger.warning(f"[ENGINE] Multi-tenancy validation FAILED for company {event.company_id}: {error_msg}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Multi-tenancy validation ERROR (failing closed): {e}")
            return False
    
    async def _get_automation_rules(
        self, 
        db: AsyncSession, 
        company_id: str, 
        trigger_type: TriggerType
    ) -> dict[str, Any]:
        """Get company-specific automation rules for a trigger type."""
        trigger_type_mapping = {
            TriggerType.SCREENING_COMPLETED: "screening_completed",
            TriggerType.INTERVIEW_SCHEDULED: "interview_scheduled",
            TriggerType.INTERVIEW_COMPLETED: "interview_completed",
            TriggerType.CANDIDATE_INACTIVE: "no_response_48h",
            TriggerType.CANDIDATE_NO_SHOW: "candidate_no_show",
            TriggerType.OFFER_SENT: "offer_sent",
            TriggerType.CANDIDATE_HIRED: "candidate_hired",
            TriggerType.CANDIDATE_REJECTED: "candidate_rejected",
            TriggerType.STAGE_CHANGED: "candidate_stage_changed",
            TriggerType.CANDIDATE_APPLIED: "candidate_applied",
            TriggerType.ATS_SYNC: "ats_sync",
            TriggerType.JOB_PUBLISHED: "job_published",
            TriggerType.CANDIDATES_SOURCED: "candidates_sourced",
            TriggerType.SLOT_OPENED: "slot_opened",
        }
        
        db_trigger_type = trigger_type_mapping.get(trigger_type, trigger_type.value)
        
        try:
            repo = CommunicationAutomationRepository(db)
            rule = await repo.find_first_active_for_trigger(
                company_id, db_trigger_type
            )
            
            if rule:
                trigger_config = rule.trigger_config or {}
                return {
                    "auto_execute": trigger_config.get("auto_execute", False),
                    "conditions": rule.conditions or [],
                    "actions": [rule.action_type] if rule.action_type else [],
                    "action_config": rule.action_config or {},
                    "confidence_threshold": trigger_config.get("confidence_threshold", 0.8),
                    "priority": rule.priority or "normal"
                }
        except Exception as e:
            logger.warning(f"[ENGINE] Error fetching automation rules: {e}")
        
        return {
            "auto_execute": False,
            "conditions": [],
            "actions": [],
            "action_config": {},
            "confidence_threshold": 0.8,
            "priority": "normal"
        }
    
    async def _evaluate_conditions(
        self, 
        event: AutomationEvent, 
        rules: dict[str, Any]
    ) -> bool:
        """Evaluate if conditions are met for automation."""
        conditions = rules.get("conditions", {})
        
        if not conditions:
            return True
        
        payload = event.payload
        
        if isinstance(conditions, list):
            for condition in conditions:
                if isinstance(condition, dict):
                    field = condition.get("field")
                    operator = condition.get("operator")
                    value = condition.get("value")
                    
                    if field and operator and value is not None:
                        event_value = payload.get(field)
                        if not self._evaluate_single_condition(event_value, operator, value):
                            logger.info(f"[ENGINE] Condition failed: {field} {operator} {value}")
                            return False
            return True
        
        for condition_key, condition_value in conditions.items():
            if condition_key == "min_wsi_score":
                wsi_score = payload.get("wsi_score") or payload.get("wsi_scores", {}).get("overall", 0)
                if wsi_score < condition_value:
                    logger.info(f"[ENGINE] Condition failed: wsi_score {wsi_score} < {condition_value}")
                    return False
            
            elif condition_key == "stages":
                current_stage = payload.get("current_stage") or payload.get("stage")
                if current_stage and current_stage not in condition_value:
                    logger.info(f"[ENGINE] Condition failed: stage {current_stage} not in {condition_value}")
                    return False
            
            elif condition_key == "min_confidence":
                confidence = payload.get("confidence", 1.0)
                if confidence < condition_value:
                    logger.info(f"[ENGINE] Condition failed: confidence {confidence} < {condition_value}")
                    return False
            
            elif condition_key == "source_types":
                source = event.source
                if source not in condition_value:
                    logger.info(f"[ENGINE] Condition failed: source {source} not in {condition_value}")
                    return False
            
            elif condition_key == "min_cv_score":
                cv_score = payload.get("cv_score") or payload.get("cv_scores", {}).get("overall", 0)
                if cv_score < condition_value:
                    logger.info(f"[ENGINE] Condition failed: cv_score {cv_score} < {condition_value}")
                    return False
            
            elif condition_key == "passed":
                passed = payload.get("passed", True)
                if passed != condition_value:
                    logger.info(f"[ENGINE] Condition failed: passed {passed} != {condition_value}")
                    return False
        
        return True
    
    def _evaluate_single_condition(self, event_value: Any, operator: str, expected: Any) -> bool:
        """Evaluate a single condition."""
        if event_value is None:
            return False
        
        if operator == "equals":
            return event_value == expected
        elif operator == "not_equals":
            return event_value != expected
        elif operator == "greater_than":
            return event_value > expected
        elif operator == "less_than":
            return event_value < expected
        elif operator == "greater_than_or_equal":
            return event_value >= expected
        elif operator == "less_than_or_equal":
            return event_value <= expected
        elif operator == "contains":
            return expected in event_value
        elif operator == "in":
            return event_value in expected
        elif operator == "not_in":
            return event_value not in expected
        
        return True
    
    async def _execute_handler(
        self, 
        handler: Callable, 
        event: AutomationEvent,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute the handler for the event."""
        try:
            result = await handler(
                candidate_id=event.candidate_id,
                vacancy_id=event.vacancy_id,
                company_id=event.company_id,
                db=db,
                **event.payload
            )
            return {"success": True, "executed": True, "result": result}
        except Exception as e:
            logger.error(f"[ENGINE] Handler execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_suggestion(
        self,
        event: AutomationEvent,
        db: AsyncSession,
        rules: dict[str, Any]
    ) -> dict[str, Any]:
        """Create an AI suggestion for recruiter approval."""
        from lia_models.automation import AISuggestion
        
        suggested_action = self._get_suggested_action(event.trigger_type)
        
        suggestion = AISuggestion(
            company_id=event.company_id,
            candidate_id=event.candidate_id,
            vacancy_id=event.vacancy_id,
            suggestion_type=event.trigger_type.value,
            action_type=suggested_action,
            action_config=event.payload,
            title=f"Sugestão: {self._get_action_title(event.trigger_type)}",
            description=self._get_action_description(event.trigger_type, event.payload),
            confidence_score="0.85",
            reasoning=f"Trigger automático: {event.trigger_type.value}",
            status="pending",
            extra_data={
                "source": event.source,
                "trigger_timestamp": event.timestamp.isoformat(),
                "rules_applied": rules
            }
        )
        
        db.add(suggestion)
        await db.commit()
        await db.refresh(suggestion)
        
        return {
            "success": True,
            "suggestion_created": True,
            "suggestion_id": str(suggestion.id)
        }
    
    def _get_suggested_action(self, trigger_type: TriggerType) -> str:
        """Get the default suggested action for a trigger type."""
        actions = {
            TriggerType.SCREENING_COMPLETED: "move_to_interview",
            TriggerType.INTERVIEW_COMPLETED: "generate_parecer",
            TriggerType.CANDIDATE_INACTIVE: "send_followup",
            TriggerType.CANDIDATE_NO_SHOW: "reschedule_or_reject",
            TriggerType.OFFER_SENT: "monitor_response",
            TriggerType.CANDIDATE_HIRED: "sync_ats_onboarding",
            TriggerType.CANDIDATE_REJECTED: "send_feedback_talent_pool",
            TriggerType.INTERVIEW_SCHEDULED: "send_confirmation",
            TriggerType.STAGE_CHANGED: "notify_stakeholders",
            TriggerType.CANDIDATE_APPLIED: "start_screening",
            TriggerType.ATS_SYNC: "sync_status",
            TriggerType.JOB_PUBLISHED: "activate_sourcing",
            TriggerType.CANDIDATES_SOURCED: "start_screening_pipeline",
            TriggerType.SLOT_OPENED: "process_screening_queue",
        }
        return actions.get(trigger_type, "notify_recruiter")
    
    def _get_action_title(self, trigger_type: TriggerType) -> str:
        """Get a human-readable title for the action."""
        titles = {
            TriggerType.SCREENING_COMPLETED: "Mover candidato para entrevista",
            TriggerType.INTERVIEW_COMPLETED: "Gerar parecer da entrevista",
            TriggerType.CANDIDATE_INACTIVE: "Enviar follow-up ao candidato",
            TriggerType.CANDIDATE_NO_SHOW: "Reagendar ou rejeitar candidato",
            TriggerType.OFFER_SENT: "Monitorar resposta da proposta",
            TriggerType.CANDIDATE_HIRED: "Sincronizar contratação com ATS",
            TriggerType.CANDIDATE_REJECTED: "Enviar feedback e adicionar ao banco",
            TriggerType.INTERVIEW_SCHEDULED: "Enviar confirmação de entrevista",
            TriggerType.STAGE_CHANGED: "Notificar stakeholders",
            TriggerType.CANDIDATE_APPLIED: "Iniciar triagem",
            TriggerType.ATS_SYNC: "Sincronizar status com ATS",
            TriggerType.JOB_PUBLISHED: "Ativar sourcing para a vaga",
            TriggerType.CANDIDATES_SOURCED: "Iniciar pipeline de triagem",
            TriggerType.SLOT_OPENED: "Processar fila de triagem",
        }
        return titles.get(trigger_type, "Ação automatizada")
    
    def _get_action_description(self, trigger_type: TriggerType, payload: dict[str, Any]) -> str:
        """Get a description for the suggested action."""
        descriptions = {
            TriggerType.SCREENING_COMPLETED: "O candidato completou a triagem e pode ser movido para a próxima etapa.",
            TriggerType.INTERVIEW_COMPLETED: "A entrevista foi concluída. Gerar parecer para avaliação.",
            TriggerType.CANDIDATE_INACTIVE: f"Candidato inativo há {payload.get('days_inactive', 'N/A')} dias.",
            TriggerType.CANDIDATE_NO_SHOW: "Candidato não compareceu à entrevista agendada.",
            TriggerType.OFFER_SENT: "Proposta enviada. Acompanhar resposta do candidato.",
            TriggerType.CANDIDATE_HIRED: "Candidato contratado. Sincronizar com sistema de onboarding.",
            TriggerType.CANDIDATE_REJECTED: "Candidato rejeitado. Enviar feedback e avaliar para banco de talentos.",
            TriggerType.JOB_PUBLISHED: f"Vaga '{payload.get('job_title', 'N/A')}' publicada. Ativar busca de candidatos.",
            TriggerType.CANDIDATES_SOURCED: f"Encontrados {payload.get('candidates_added', 0)} candidatos. Iniciar triagem.",
            TriggerType.SLOT_OPENED: f"Slot aberto na vaga. {payload.get('slots_available', 0)} vagas disponíveis na fila de triagem.",
        }
        return descriptions.get(trigger_type, "Ação sugerida pelo sistema de automação.")
    
    async def _log_audit(
        self, 
        event: AutomationEvent, 
        result: dict[str, Any]
    ):
        """Log automation event to audit trail."""
        try:
            from app.shared.services.audit_service import audit_service
            
            await audit_service.log_decision(
                company_id=event.company_id,
                agent_name="stage_automation_engine",
                decision_type=f"automation_{event.trigger_type.value}",
                action=event.trigger_type.value,
                decision="executed" if result.get("executed") else "suggestion_created" if result.get("suggestion_created") else "skipped",
                reasoning=[
                    f"Trigger: {event.trigger_type.value}",
                    f"Source: {event.source}",
                    f"Result: {result.get('success', False)}"
                ],
                criteria_used=["trigger_type", "company_rules", "conditions"],
                candidate_id=event.candidate_id,
                job_vacancy_id=event.vacancy_id,
                confidence=0.85 if result.get("success") else 0.5,
                human_review_required=not result.get("executed", False),
                demographic_proxies={},
            )
        except Exception as e:
            logger.warning(f"[ENGINE] Failed to log audit: {e}")


stage_automation_engine = StageAutomationEngine()
