"""
LangGraph nodes for interview scheduling conversational workflow.
"""
import json
import logging
try:
    from anthropic import AsyncAnthropic  # noqa: F401 — module-level for test patching  # W3-027-EXEMPT: compat alias for test patching (noqa F401) — production LLM via get_provider_for_tenant
except ImportError:
    AsyncAnthropic = None  # type: ignore[assignment,misc]
from datetime import date, datetime, timedelta
from typing import Any

from app.core.database import get_db
# get_provider_for_tenant imported lazily inside functions to avoid circular import
# (llm_factory → token_budget_service → domains.__init__ → interview_scheduling → llm_factory)
from app.domains.interview_scheduling.agents.interview_system_prompt import get_extraction_prompt
from app.domains.interview_scheduling.services.calendar_service import calendar_service
from app.models.interview import Interview
from app.schemas.interview_scheduling_state import InterviewSchedulingState

logger = logging.getLogger(__name__)

# =============================================
# SERVICE LAYER
# =============================================

class InterviewSchedulingService:
    """Service for managing interview scheduling state."""
    
    @staticmethod
    def load_from_workflow_data(workflow_data: dict[str, Any]) -> InterviewSchedulingState:
        """Load InterviewSchedulingState from workflow_data."""
        state_dict = workflow_data.get("interview_scheduling_state")
        if state_dict:
            try:
                return InterviewSchedulingState(**state_dict)
            except Exception as e:
                logger.error(f"Failed to load InterviewSchedulingState: {e}")
                return None
        return None
    
    @staticmethod
    def save_to_workflow_data(
        state: InterviewSchedulingState, 
        workflow_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Save InterviewSchedulingState to workflow_data."""
        workflow_data["interview_scheduling_state"] = state.model_dump(mode="json")
        return workflow_data
    
    @staticmethod
    def parse_datetime(preferred_date: date, preferred_time: str) -> datetime:
        """
        Parse preferred_date + preferred_time into final datetime.
        
        Examples:
        - "14:00" -> 14:00
        - "manhã" -> 09:00
        - "tarde" -> 14:00
        - "noite" -> 19:00
        """
        time_mappings = {
            "manhã": "09:00",
            "manha": "09:00",
            "tarde": "14:00",
            "noite": "19:00"
        }
        
        # Normalize
        time_str = time_mappings.get(preferred_time.lower(), preferred_time)
        
        # Parse time
        try:
            hour, minute = map(int, time_str.split(":"))
            return datetime.combine(preferred_date, datetime.min.time()).replace(hour=hour, minute=minute)
        except Exception:
            # Default to 14:00
            logger.warning(f"Failed to parse time '{preferred_time}', defaulting to 14:00")
            return datetime.combine(preferred_date, datetime.min.time()).replace(hour=14, minute=0)


interview_service = InterviewSchedulingService()


def _compute_confidence_score(interview_state: "InterviewSchedulingState", workflow_data: dict) -> float:
    """Calcula confidence baseado em completude de campos e estado do workflow.

    Escala:
      - Agendamento completo com sucesso → 1.0
      - Erro de agendamento ou fairness block → 0.1
      - Coleta parcial → 0.10 + (coletados/total) * 0.85  (máx 0.95 durante coleta)
    """
    if workflow_data.get("interview_scheduling_complete"):
        return 1.0
    if workflow_data.get("interview_scheduling_error") or workflow_data.get("fairness_blocked"):
        return 0.1
    try:
        progress = interview_state.get_collection_progress()
        collected = progress.get("collected", 0)
        total = progress.get("total_required", 7)
        base = (collected / total) if total > 0 else 0.0
        return round(0.10 + base * 0.85, 2)
    except Exception:
        return 0.5


# =============================================
# STATE LOADER
# =============================================

async def interview_state_loader(state: dict[str, Any]) -> dict[str, Any]:
    """
    Load or initialize InterviewSchedulingState from workflow_data.
    """
    workflow_data = state.get("workflow_data", {})
    
    # Try to load existing state
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        # Initialize new state
        interview_state = InterviewSchedulingState()
        logger.info("📅 Initialized new InterviewSchedulingState")
    
    # Save back to workflow_data
    state["workflow_data"] = interview_service.save_to_workflow_data(interview_state, workflow_data)
    state["current_workflow"] = "interview_scheduling"
    
    return state


# =============================================
# INTERVIEW ROUTER
# =============================================

async def interview_router(state: dict[str, Any]) -> dict[str, Any]:
    """
    Route to appropriate collector based on pending fields.
    """
    workflow_data = state.get("workflow_data", {})
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        logger.error("❌ InterviewSchedulingState not found in workflow_data")
        return state
    
    # Determine next field to collect
    next_field = interview_state.get_next_pending_field()
    
    if next_field:
        state["workflow_data"]["next_collection_target"] = next_field
        logger.info(f"🎯 Next interview field to collect: {next_field}")
    else:
        # All fields collected - ready for scheduling
        state["workflow_data"]["next_collection_target"] = None
        logger.info("✅ All required interview fields collected")
    
    return state


# =============================================
# FIELD COLLECTOR
# =============================================

async def interview_details_collector(state: dict[str, Any]) -> dict[str, Any]:
    """
    Collect interview details from user message.
    Uses LLM to extract structured information.
    """
    workflow_data = state.get("workflow_data", {})
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        return state

    # Get last user message
    last_message = state["messages"][-1].content
    state.get("entities", {})

    # SEG-2: FairnessGuard — verificar critérios discriminatórios antes de processar
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(last_message)
        if _fg_result.is_blocked:
            logger.warning(
                "[interview_details_collector][SEG-2] FairnessGuard bloqueou mensagem "
                "category=%s terms=%s",
                _fg_result.category, _fg_result.blocked_terms,
            )
            workflow_data["fairness_blocked"] = True
            workflow_data["fairness_category"] = _fg_result.category
            workflow_data["confidence_score"] = 0.1
            workflow_data["response_data"] = {
                "message": _fg_result.educational_message or (
                    "Esta solicitação não pode ser processada pois contém critérios "
                    "discriminatórios. Por favor, reformule o agendamento com base em "
                    "requisitos objetivos do processo seletivo."
                ),
                "status": "fairness_blocked",
            }
            state["workflow_data"] = workflow_data
            return state
        _soft = _fg.check_implicit_bias(last_message)
        if _soft:
            logger.info(
                "[interview_details_collector][SEG-2] FairnessGuard soft warnings: %s", _soft
            )
    except Exception as _fg_exc:
        logger.debug("[interview_details_collector] FairnessGuard check skipped: %s", _fg_exc)

    # Use LLM to extract interview details — prompt centralizado em interview_system_prompt.py
    extraction_prompt = get_extraction_prompt(
        last_message=last_message,
        current_state=json.dumps(interview_state.model_dump(), indent=2, default=str),
        next_pending_field=interview_state.get_next_pending_field() or "",
    )
    
    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant  # lazy
        container = get_provider_for_tenant()
        extracted_json = await container.generate_with_fallback(extraction_prompt, agent_type="InterviewSchedulingAgent")
        # Clean JSON
        if "```json" in extracted_json:
            extracted_json = extracted_json.split("```json")[1].split("```")[0]
        elif "```" in extracted_json:
            extracted_json = extracted_json.split("```")[1].split("```")[0]
        
        extracted = json.loads(extracted_json.strip())
        
        # Update state with extracted fields
        for field, value in extracted.items():
            if value and field in interview_state.model_fields:
                # Parse date if needed
                if field == "preferred_date" and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                    except Exception:
                        logger.warning(f"Failed to parse date: {value}")
                        continue
                
                setattr(interview_state, field, value)
                interview_state.mark_field_collected(field)
                logger.info(f"✅ Collected interview field: {field} = {value}")
        
    except Exception as e:
        logger.error(f"Failed to extract interview details: {e}")
    
    # Save updated state
    state["workflow_data"] = interview_service.save_to_workflow_data(interview_state, workflow_data)

    # Atualizar confidence score após coleta
    try:
        state["workflow_data"]["confidence_score"] = _compute_confidence_score(
            interview_state, state["workflow_data"]
        )
    except Exception:
        pass

    return state


# =============================================
# VALIDATOR
# =============================================

async def interview_validator(state: dict[str, Any]) -> dict[str, Any]:
    """
    Validate interview scheduling state completeness.
    """
    workflow_data = state.get("workflow_data", {})
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        return state
    
    # Validate completeness
    is_complete = interview_state.validate_completeness()
    
    if is_complete:
        logger.info("✅ Interview scheduling state is complete and valid")
        workflow_data["interview_ready_for_scheduling"] = True
    else:
        logger.warning(f"❌ Interview validation failed: {interview_state.validation_errors}")
        workflow_data["interview_ready_for_scheduling"] = False
    
    state["workflow_data"] = workflow_data
    
    return state


# =============================================
# SCHEDULER EXECUTOR
# =============================================

async def interview_scheduler_executor(state: dict[str, Any]) -> dict[str, Any]:
    """
    Execute actual interview scheduling via calendar_service.
    """
    workflow_data = state.get("workflow_data", {})
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        logger.error("❌ No interview state found")
        workflow_data["interview_scheduling_error"] = "Interview state not found"
        state["workflow_data"] = workflow_data
        return state
    
    # Validate required fields before proceeding
    if not all([
        interview_state.candidate_name,
        interview_state.candidate_email,
        interview_state.job_title,
        interview_state.interview_type,
        interview_state.interviewer_email,
        interview_state.preferred_date,
        interview_state.preferred_time
    ]):
        missing_fields = [f for f in [
            "candidate_name", "candidate_email", "job_title", "interview_type",
            "interviewer_email", "preferred_date", "preferred_time"
        ] if not getattr(interview_state, f, None)]
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(f"❌ {error_msg}")
        workflow_data["interview_scheduling_error"] = error_msg
        workflow_data["interview_ready_for_scheduling"] = False
        state["workflow_data"] = workflow_data
        return state
    
    try:
        # Compute final start_time
        if interview_state.preferred_date and interview_state.preferred_time:
            interview_state.start_time = interview_service.parse_datetime(
                interview_state.preferred_date,
                interview_state.preferred_time
            )
        else:
            logger.error("❌ Missing date/time for scheduling")
            workflow_data["interview_scheduling_error"] = "Data/hora não informada"
            state["workflow_data"] = workflow_data
            return state
        
        # Prepare request
        interview_state.to_interview_request()
        
        # Schedule via calendar service
        all_interviewer_emails = [interview_state.interviewer_email]
        if interview_state.additional_interviewers:
            all_interviewer_emails.extend([p.email for p in interview_state.additional_interviewers if p.email])
        
        calendar_event = await calendar_service.schedule_interview(
            organizer_email=interview_state.interviewer_email,
            candidate_name=interview_state.candidate_name,
            candidate_email=interview_state.candidate_email,
            interviewer_emails=all_interviewer_emails,
            position=interview_state.job_title,
            start_time=interview_state.start_time,
            duration_minutes=interview_state.duration_minutes,
            location=interview_state.location or "Microsoft Teams",
            as_teams_meeting=interview_state.as_teams_meeting,
            notes=interview_state.notes
        )
        
        # Create database record
        async for db in get_db():
            interview = Interview(
                title=f"Entrevista: {interview_state.candidate_name} - {interview_state.job_title}",
                interview_type=interview_state.interview_type,
                interview_mode=interview_state.interview_mode or "remoto",
                candidate_name=interview_state.candidate_name,
                candidate_email=interview_state.candidate_email,
                interviewer_name=interview_state.interviewer_name or "Equipe WedoTalent",
                interviewer_email=interview_state.interviewer_email,
                additional_interviewers=[p.model_dump() for p in interview_state.additional_interviewers],
                start_time=interview_state.start_time,
                end_time=interview_state.start_time + timedelta(minutes=interview_state.duration_minutes),
                duration_minutes=interview_state.duration_minutes,
                location=interview_state.location or "Microsoft Teams",
                job_title=interview_state.job_title,
                graph_event_id=calendar_event.get("id"),
                graph_organizer_email=interview_state.interviewer_email,
                is_synced_to_calendar=True,
                last_synced_at=datetime.utcnow(),
                status="scheduled",
                created_by="lia_agent"
            )
            
            # Extract meeting URL
            if interview_state.as_teams_meeting and calendar_event.get("onlineMeeting"):
                interview.meeting_url = calendar_event["onlineMeeting"].get("joinUrl")
                interview.meeting_platform = "teams"
                interview_state.meeting_url = interview.meeting_url
            
            db.add(interview)
            await db.commit()
            await db.refresh(interview)
            
            # Save interview ID to state
            interview_state.created_interview_id = str(interview.id)
            
            logger.info(f"✅ Interview scheduled successfully: {interview.id}")
            
            break
        
        # Update workflow data
        workflow_data["interview_scheduling_complete"] = True
        workflow_data["created_interview_id"] = interview_state.created_interview_id
        workflow_data["meeting_url"] = interview_state.meeting_url
        workflow_data["confidence_score"] = 1.0
        state["workflow_data"] = interview_service.save_to_workflow_data(interview_state, workflow_data)
        
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Failed to schedule interview: {e}")
        workflow_data["interview_scheduling_error"] = str(e)
        state["workflow_data"] = workflow_data
    
    return state


# =============================================
# RESPONSE PLANNER
# =============================================

async def interview_response_planner(state: dict[str, Any]) -> dict[str, Any]:
    """
    Plan LIA's next response for interview scheduling workflow.
    """
    workflow_data = state.get("workflow_data", {})
    interview_state = interview_service.load_from_workflow_data(workflow_data)
    
    if not interview_state:
        return state
    
    # Determine what to show in response
    response_data = {
        "workflow_type": "interview_scheduling",
        "progress": interview_state.get_collection_progress()
    }
    
    # Check if scheduling is complete
    if workflow_data.get("interview_scheduling_complete"):
        response_data["status"] = "completed"
        response_data["interview_id"] = workflow_data.get("created_interview_id")
        response_data["meeting_url"] = workflow_data.get("meeting_url")
        response_data["message"] = f"✅ Entrevista agendada com sucesso! Confirmação enviada para {interview_state.candidate_email}"
    elif workflow_data.get("interview_scheduling_error"):
        response_data["status"] = "error"
        response_data["error"] = workflow_data.get("interview_scheduling_error")
    else:
        response_data["status"] = "collecting"
        next_field = interview_state.get_next_pending_field()
        response_data["next_field"] = next_field
    
    workflow_data["response_data"] = response_data
    state["workflow_data"] = workflow_data
    
    return state
