"""
LangGraph nodes for interview scheduling conversational workflow.
"""
from typing import Dict, Any
from datetime import datetime, date, timedelta
import logging
from anthropic import AsyncAnthropic
import json

from app.schemas.interview_scheduling_state import InterviewSchedulingState
from app.services.calendar_service import calendar_service
from app.core.database import get_db
from app.models.interview import Interview
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# =============================================
# SERVICE LAYER
# =============================================

class InterviewSchedulingService:
    """Service for managing interview scheduling state."""
    
    @staticmethod
    def load_from_workflow_data(workflow_data: Dict[str, Any]) -> InterviewSchedulingState:
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
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        except:
            # Default to 14:00
            logger.warning(f"Failed to parse time '{preferred_time}', defaulting to 14:00")
            return datetime.combine(preferred_date, datetime.min.time()).replace(hour=14, minute=0)


interview_service = InterviewSchedulingService()


# =============================================
# STATE LOADER
# =============================================

async def interview_state_loader(state: Dict[str, Any]) -> Dict[str, Any]:
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

async def interview_router(state: Dict[str, Any]) -> Dict[str, Any]:
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

async def interview_details_collector(state: Dict[str, Any]) -> Dict[str, Any]:
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
    entities = state.get("entities", {})
    
    # Use LLM to extract interview details
    anthropic = AsyncAnthropic()
    
    extraction_prompt = f"""Extraia informações de agendamento de entrevista da mensagem do usuário.

MENSAGEM DO USUÁRIO:
{last_message}

CAMPOS ATUAIS:
{json.dumps(interview_state.model_dump(), indent=2, default=str)}

CAMPOS PENDENTES:
{interview_state.get_next_pending_field()}

Retorne JSON com os campos que conseguir extrair:
{{
    "candidate_name": "...",
    "candidate_email": "...",
    "job_title": "...",
    "interview_type": "tecnica|comportamental|cultural|rh|gerencial",
    "interviewer_email": "...",
    "preferred_date": "YYYY-MM-DD",
    "preferred_time": "HH:MM ou manhã|tarde|noite",
    "duration_minutes": 60,
    "interview_mode": "presencial|remoto|hibrido",
    "notes": "..."
}}

RETORNE APENAS OS CAMPOS MENCIONADOS. Se nada foi mencionado, retorne {{}}.
"""
    
    try:
        response = await anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        extracted_json = response.content[0].text
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
                    except:
                        logger.warning(f"Failed to parse date: {value}")
                        continue
                
                setattr(interview_state, field, value)
                interview_state.mark_field_collected(field)
                logger.info(f"✅ Collected interview field: {field} = {value}")
        
    except Exception as e:
        logger.error(f"Failed to extract interview details: {e}")
    
    # Save updated state
    state["workflow_data"] = interview_service.save_to_workflow_data(interview_state, workflow_data)
    
    return state


# =============================================
# VALIDATOR
# =============================================

async def interview_validator(state: Dict[str, Any]) -> Dict[str, Any]:
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

async def interview_scheduler_executor(state: Dict[str, Any]) -> Dict[str, Any]:
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
        interview_request = interview_state.to_interview_request()
        
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
        state["workflow_data"] = interview_service.save_to_workflow_data(interview_state, workflow_data)
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule interview: {e}")
        workflow_data["interview_scheduling_error"] = str(e)
        state["workflow_data"] = workflow_data
    
    return state


# =============================================
# RESPONSE PLANNER
# =============================================

async def interview_response_planner(state: Dict[str, Any]) -> Dict[str, Any]:
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
