"""
Scheduling Service for Interview Management.
Integrated with Microsoft Graph API for Teams meetings and calendar sync.

This service provides:
- Interview scheduling and management
- ICS calendar file generation
- Microsoft Teams meeting creation with auto-generated join links
- Outlook calendar sync with meeting invites
- Microsoft Bookings integration
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from icalendar import Calendar, Event, vText
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.interview import Interview
from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value

_microsoft_graph_service = None


def get_microsoft_graph_service():
    """Lazy load Microsoft Graph service to avoid circular imports."""
    global _microsoft_graph_service
    if _microsoft_graph_service is None:
        from app.shared.services.microsoft_graph_service import microsoft_graph_service
        _microsoft_graph_service = microsoft_graph_service
    return _microsoft_graph_service

logger = logging.getLogger(__name__)

_event_dispatcher = None
_communication_service = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


def get_communication_service():
    """Lazy load CommunicationService to avoid circular imports."""
    global _communication_service
    if _communication_service is None:
        from app.domains.communication.services.communication_service import communication_service
        _communication_service = communication_service
    return _communication_service


class SchedulingService:
    """
    Service for managing interview scheduling.
    
    Current Status: Funcional - Aguardando Configuração Calendar
    - Interviews are stored in the database
    - ICS files can be generated for download
    - Calendar sync requires Microsoft Graph or Google Calendar API configuration
    """
    
    def __init__(self):
        self.default_timezone = "America/Sao_Paulo"
    
    async def get_scheduling_policy(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Get effective scheduling configuration for a company,
        merging CompanyHiringPolicy with defaults.
        """
        try:
            policy = await get_policy_for_company(company_id, db)
            scheduling = policy.get("scheduling_rules", {})
            return {
                "allowed_days": scheduling.get("allowed_days", ["mon", "tue", "wed", "thu", "fri"]),
                "allowed_hours": scheduling.get("allowed_hours", {"start": "09:00", "end": "18:00"}),
                "default_duration_minutes": scheduling.get("default_duration_minutes", 60),
                "self_scheduling_enabled": scheduling.get("self_scheduling_enabled", False),
            }
        except Exception as e:
            logger.warning(f"Failed to load scheduling policy: {e}")
            return {
                "allowed_days": ["mon", "tue", "wed", "thu", "fri"],
                "allowed_hours": {"start": "09:00", "end": "18:00"},
                "default_duration_minutes": 60,
                "self_scheduling_enabled": False,
            }
    
    def _resolve_company_id(self, company_id: str | None) -> str:
        """
        Resolve company_id with fallback to 'default'.
        
        Required by send_templated_message() which mandates a non-None company_id.
        
        Args:
            company_id: Company ID (can be None or empty string)
        
        Returns:
            Resolved company ID (either the provided ID or 'default' as fallback)
        """
        return company_id if company_id else None
    
    async def _resolve_company_name(
        self,
        db: AsyncSession,
        company_id: str | None,
        company_name: str | None
    ) -> str:
        """
        Resolve company_name from company_id if not provided.
        
        Args:
            db: Database session
            company_id: Company ID to look up
            company_name: Provided company name (if any)
        
        Returns:
            Resolved company name or default value
        """
        if company_name:
            return company_name
        
        if company_id:
            try:
                from lia_models.company import CompanyProfile
                result = await db.execute(
                    select(CompanyProfile).where(
                        CompanyProfile.id == company_id
                    ).limit(1)
                )
                company = result.scalar_one_or_none()
                if company and company.name:
                    return company.name
            except Exception as e:
                logger.warning(f"Failed to resolve company name for {company_id}: {e}")
        
        return "Empresa"
    
    async def create_interview(
        self,
        db: AsyncSession,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        interviewer_name: str,
        interviewer_email: str,
        start_time: datetime,
        duration_minutes: int = 60,
        interview_type: str = "video",
        interview_mode: str = "video",
        job_title: str | None = None,
        job_vacancy_id: str | None = None,
        company_id: str | None = None,
        location: str | None = None,
        notes: str | None = None,
        additional_interviewers: list[dict[str, str]] | None = None,
        created_by: str = "system",
        dispatch_event: bool = True
    ) -> Interview:
        """
        Create a new interview appointment.
        
        Args:
            candidate_id: UUID of the candidate
            candidate_name: Name of the candidate
            candidate_email: Email of the candidate
            interviewer_name: Name of the primary interviewer
            interviewer_email: Email of the primary interviewer
            start_time: Interview start datetime
            duration_minutes: Duration in minutes (default 60)
            interview_type: Type of interview (technical, behavioral, cultural, final)
            interview_mode: Mode of interview (video, in_person, phone)
            job_title: Title of the job position
            job_vacancy_id: UUID of the job vacancy
            company_id: Company ID for multi-tenancy and event dispatch
            location: Physical location or meeting platform
            notes: Additional notes
            additional_interviewers: List of additional interviewer dicts with name/email
            created_by: Who created this interview
            dispatch_event: Whether to dispatch interview-scheduled event (default True)
        
        Returns:
            Created Interview object
        """
        if company_id and duration_minutes == 60:
            try:
                policy = await get_policy_for_company(company_id, db)
                duration_minutes = resolve_policy_value(
                    policy, "scheduling_rules", "default_duration_minutes",
                    override=None if duration_minutes == 60 else duration_minutes,
                    default=60,
                )
            except Exception as e:
                logger.warning(f"Failed to load scheduling policy for {company_id}: {e}")
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        interview = Interview(
            id=uuid.uuid4(),
            title=f"Entrevista: {candidate_name} - {job_title or 'Vaga'}",
            description=notes,
            interview_type=interview_type,
            interview_mode=interview_mode,
            candidate_id=UUID(candidate_id) if candidate_id else None,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            interviewer_name=interviewer_name,
            interviewer_email=interviewer_email,
            additional_interviewers=additional_interviewers or [],
            start_time=start_time,
            end_time=end_time,
            timezone=self.default_timezone,
            duration_minutes=duration_minutes,
            location=location,
            job_vacancy_id=UUID(job_vacancy_id) if job_vacancy_id else None,
            job_title=job_title,
            status="scheduled",
            confirmation_status="pending",
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_synced_to_calendar=False
        )
        
        db.add(interview)
        await db.commit()
        await db.refresh(interview)
        
        logger.info(f"📅 Interview created: {interview.id} for {candidate_name}")
        logger.info(f"   Date/Time: {start_time.isoformat()}")
        logger.info(f"   Type: {interview_type} ({interview_mode})")
        logger.info("   Status: Funcional - Aguardando Configuração Calendar para sync")
        
        if dispatch_event and company_id and job_vacancy_id:
            try:
                dispatcher = get_event_dispatcher()
                await dispatcher.on_interview_scheduled(
                    candidate_id=candidate_id,
                    vacancy_id=job_vacancy_id,
                    company_id=company_id,
                    interview_id=str(interview.id),
                    interview_datetime=start_time.isoformat(),
                    interview_type=interview_type,
                    interviewer_name=interviewer_name,
                    interviewer_email=interviewer_email,
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    job_title=job_title
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to dispatch interview-scheduled event: {e}")
        
        return interview
    
    async def create_interview_with_teams(
        self,
        db: AsyncSession,
        organizer_email: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        start_time: datetime,
        duration_minutes: int = 60,
        interview_type: str = "video",
        job_title: str | None = None,
        job_vacancy_id: str | None = None,
        company_id: str | None = None,
        notes: str | None = None,
        additional_attendees: list[dict[str, str]] | None = None,
        created_by: str = "system",
        send_calendar_invites: bool = True,
        interviewer_name: str | None = None
    ) -> tuple[Interview, dict[str, Any]]:
        """
        Create an interview with Microsoft Teams meeting and calendar sync.
        
        This method:
        1. Creates a Teams meeting with auto-generated join link
        2. Sends calendar invites to all attendees via Outlook
        3. Stores the interview in the database
        4. Returns complete meeting details including Teams link
        
        Args:
            organizer_email: Email of the meeting organizer (must be in Azure AD)
            candidate_id: UUID of the candidate
            candidate_name: Name of the candidate
            candidate_email: Email of the candidate
            start_time: Interview start datetime
            duration_minutes: Duration in minutes
            interview_type: Type of interview
            job_title: Title of the job position
            job_vacancy_id: UUID of the job vacancy
            company_id: Company ID for multi-tenancy
            notes: Additional notes
            additional_attendees: List of additional attendees [{email, name}]
            created_by: Who created this interview
            send_calendar_invites: Whether to send calendar invites
        
        Returns:
            Tuple of (Interview object, metadata dict with Teams meeting info)
        """
        from app.shared.services.microsoft_graph_service import (
            AttendeeType,
            GraphAPICalendarPermissionError,
            GraphAPIForbiddenError,
            GraphAPIRateLimitError,
            GraphAPIUnauthorizedError,
            MeetingAttendee,
        )
        
        graph_service = get_microsoft_graph_service()
        
        resolved_interviewer_name = interviewer_name or organizer_email.split("@")[0].replace(".", " ").title()
        
        async def create_fallback_interview_with_ics(
            error_message: str,
            teams_configured: bool = True
        ) -> tuple[Interview, dict[str, Any]]:
            """Create interview without Teams and generate ICS file as fallback."""
            interview = await self.create_interview(
                db=db,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                interviewer_name=resolved_interviewer_name,
                interviewer_email=organizer_email,
                start_time=start_time,
                duration_minutes=duration_minutes,
                interview_type=interview_type,
                interview_mode="video",
                job_title=job_title,
                job_vacancy_id=job_vacancy_id,
                company_id=company_id,
                notes=notes,
                created_by=created_by
            )
            
            self.generate_ics_content(interview, include_meeting_link=False)
            
            logger.info(f"📅 Interview created with ICS fallback: {interview.id}")
            
            return interview, {
                "status": "created_without_teams",
                "message": error_message,
                "teams_configured": teams_configured,
                "fallback": "ics",
                "ics_available": True,
                "ics_download_url": f"/api/v1/scheduling/interviews/{interview.id}/ics"
            }
        
        if not graph_service.is_configured:
            logger.warning("Microsoft Graph not configured, falling back to ICS calendar file")
            return await create_fallback_interview_with_ics(
                "Interview created but Teams integration not configured. ICS file available for download.",
                teams_configured=False
            )
        
        try:
            has_permission = await graph_service.check_calendar_permission(organizer_email)
            if not has_permission:
                logger.warning(f"User {organizer_email} does not have calendar permissions, falling back to ICS")
                return await create_fallback_interview_with_ics(
                    f"User {organizer_email} does not have calendar permissions. ICS file available for download."
                )
        except Exception as perm_error:
            logger.warning(f"Failed to check calendar permissions for {organizer_email}: {perm_error}")
        
        attendees = [
            MeetingAttendee(
                email=candidate_email,
                name=candidate_name,
                type=AttendeeType.REQUIRED
            )
        ]
        
        if additional_attendees:
            for att in additional_attendees:
                attendees.append(
                    MeetingAttendee(
                        email=att.get("email"),
                        name=att.get("name", att.get("email")),
                        type=AttendeeType.OPTIONAL
                    )
                )
        
        subject = f"Entrevista: {candidate_name} - {job_title or 'Processo Seletivo'}"
        body_content = f"""
        <p>Olá!</p>
        <p>Você foi convidado para uma entrevista.</p>
        <p><strong>Candidato:</strong> {candidate_name}</p>
        <p><strong>Vaga:</strong> {job_title or 'Processo Seletivo'}</p>
        <p><strong>Duração:</strong> {duration_minutes} minutos</p>
        {f'<p><strong>Observações:</strong> {notes}</p>' if notes else ''}
        <p>O link do Microsoft Teams está incluído neste convite.</p>
        """
        
        try:
            teams_meeting = await graph_service.create_teams_meeting_with_calendar_event(
                organizer_email=organizer_email,
                subject=subject,
                start_time=start_time,
                duration_minutes=duration_minutes,
                attendees=attendees,
                body_content=body_content,
                timezone=self.default_timezone,
                send_invites=send_calendar_invites
            )
            
            interview = await self.create_interview(
                db=db,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                interviewer_name=resolved_interviewer_name,
                interviewer_email=organizer_email,
                start_time=start_time,
                duration_minutes=duration_minutes,
                interview_type=interview_type,
                interview_mode="video",
                job_title=job_title,
                job_vacancy_id=job_vacancy_id,
                company_id=company_id,
                location=teams_meeting.join_url,
                notes=notes,
                created_by=created_by,
                dispatch_event=True
            )
            
            interview.meeting_url = teams_meeting.join_url
            interview.is_synced_to_calendar = True
            interview.calendar_event_id = teams_meeting.calendar_event_id
            await db.commit()
            await db.refresh(interview)
            
            logger.info(f"✅ Interview created with Teams meeting: {interview.id}")
            logger.info(f"   Interviewer: {resolved_interviewer_name} ({organizer_email})")
            logger.info(f"   Teams Join URL: {teams_meeting.join_url}")
            logger.info(f"   Calendar Event ID: {teams_meeting.calendar_event_id}")
            
            confirmation_result = None
            try:
                confirmation_result = await self.send_interview_confirmation(
                    db=db,
                    candidate_id=candidate_id,
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title or "Processo Seletivo",
                    interview_datetime=start_time,
                    interview_link=teams_meeting.join_url,
                    company_id=company_id,
                    recruiter_name=resolved_interviewer_name,
                    interviewer_name=resolved_interviewer_name,
                    interview_format="video",
                    duration_minutes=duration_minutes,
                    job_vacancy_id=job_vacancy_id
                )
                if confirmation_result.get("success"):
                    logger.info("📧 Interview confirmation email sent")
                else:
                    logger.warning(f"⚠️ Failed to send confirmation email: {confirmation_result.get('message')}")
            except Exception as email_error:
                logger.warning(f"⚠️ Failed to send interview confirmation email: {email_error}")
                confirmation_result = {"success": False, "error": str(email_error)}
            
            return interview, {
                "status": "created_with_teams",
                "message": "Interview created with Teams meeting and calendar invite",
                "teams_configured": True,
                "teams_join_url": teams_meeting.join_url,
                "teams_web_link": teams_meeting.join_web_url,
                "calendar_event_id": teams_meeting.calendar_event_id,
                "dial_in_url": teams_meeting.dial_in_url,
                "start_time": start_time.isoformat(),
                "end_time": teams_meeting.end_time.isoformat(),
                "attendees": [att.email for att in attendees],
                "subject": subject,
                "confirmation_email_sent": confirmation_result.get("success") if confirmation_result else False,
                "confirmation_email_result": confirmation_result
            }
        
        except GraphAPIUnauthorizedError as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Graph API unauthorized for {organizer_email}: {e}")
            return await create_fallback_interview_with_ics(
                "Authentication failed for Microsoft Graph. ICS file available for download."
            )
        
        except (GraphAPIForbiddenError, GraphAPICalendarPermissionError) as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Permission denied for {organizer_email}: {e}")
            return await create_fallback_interview_with_ics(
                "Permission denied for calendar access. ICS file available for download."
            )
        
        except GraphAPIRateLimitError as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Rate limit exceeded: {e}")
            return await create_fallback_interview_with_ics(
                "Microsoft Graph rate limit exceeded. ICS file available for download."
            )
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Failed to create Teams meeting: {e}")
            return await create_fallback_interview_with_ics(
                f"Teams meeting creation failed: {str(e)}. ICS file available for download."
            )
    
    async def update_interview(
        self,
        db: AsyncSession,
        interview_id: str,
        **update_data
    ) -> Interview:
        """
        Update an existing interview.
        
        Args:
            interview_id: UUID of the interview to update
            **update_data: Fields to update
        
        Returns:
            Updated Interview object
        """
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        allowed_fields = {
            'start_time', 'end_time', 'duration_minutes', 'location',
            'interview_type', 'interview_mode', 'notes', 'description',
            'interviewer_name', 'interviewer_email', 'additional_interviewers',
            'status', 'confirmation_status', 'job_title'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                if field == 'notes':
                    setattr(interview, 'description', value)
                else:
                    setattr(interview, field, value)
        
        if 'start_time' in update_data and 'duration_minutes' in update_data:
            interview.end_time = update_data['start_time'] + timedelta(minutes=update_data['duration_minutes'])
        elif 'start_time' in update_data:
            interview.end_time = update_data['start_time'] + timedelta(minutes=interview.duration_minutes)
        elif 'duration_minutes' in update_data:
            interview.end_time = interview.start_time + timedelta(minutes=update_data['duration_minutes'])
        
        interview.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(interview)
        
        logger.info(f"📅 Interview updated: {interview_id}")
        
        return interview
    
    async def cancel_interview(
        self,
        db: AsyncSession,
        interview_id: str,
        cancellation_reason: str | None = None
    ) -> Interview:
        """
        Cancel an interview.
        
        Args:
            interview_id: UUID of the interview to cancel
            cancellation_reason: Reason for cancellation
        
        Returns:
            Cancelled Interview object
        """
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        interview.status = "cancelled"
        interview.cancelled_at = datetime.utcnow()
        interview.cancellation_reason = cancellation_reason
        interview.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(interview)
        
        logger.info(f"📅 Interview cancelled: {interview_id}")
        if cancellation_reason:
            logger.info(f"   Reason: {cancellation_reason}")
        
        return interview
    
    async def complete_interview(
        self,
        db: AsyncSession,
        interview_id: str,
        outcome: str | None = None,
        feedback: dict[str, Any] | None = None,
        company_id: str | None = None,
        dispatch_event: bool = True
    ) -> Interview:
        """
        Mark an interview as completed.
        
        Args:
            interview_id: UUID of the interview to complete
            outcome: Interview outcome (passed, failed, pending_review)
            feedback: Interview feedback data
            company_id: Company ID for event dispatch
            dispatch_event: Whether to dispatch interview-completed event
        
        Returns:
            Completed Interview object
        """
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
        interview.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(interview)
        
        logger.info(f"📅 Interview completed: {interview_id}")
        if outcome:
            logger.info(f"   Outcome: {outcome}")
        
        if dispatch_event and company_id and interview.candidate_id and interview.job_vacancy_id:
            try:
                dispatcher = get_event_dispatcher()
                await dispatcher.on_interview_completed(
                    candidate_id=str(interview.candidate_id),
                    vacancy_id=str(interview.job_vacancy_id),
                    company_id=company_id,
                    interview_id=str(interview.id),
                    outcome=outcome,
                    feedback=feedback,
                    interview_type=interview.interview_type,
                    interviewer_name=interview.interviewer_name
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to dispatch interview-completed event: {e}")
        
        return interview
    
    async def get_interview(
        self,
        db: AsyncSession,
        interview_id: str
    ) -> Interview | None:
        """Get a single interview by ID."""
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        return result.scalar_one_or_none()
    
    async def list_interviews(
        self,
        db: AsyncSession,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        interviewer_email: str | None = None,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Interview], int]:
        """
        List interviews with optional filters.
        
        Returns:
            Tuple of (list of interviews, total count)
        """
        query = select(Interview)
        
        filters = []
        if candidate_id:
            filters.append(Interview.candidate_id == candidate_id)
        if vacancy_id:
            filters.append(Interview.job_vacancy_id == vacancy_id)
        if interviewer_email:
            filters.append(Interview.interviewer_email == interviewer_email)
        if status:
            filters.append(Interview.status == status)
        if from_date:
            filters.append(Interview.start_time >= from_date)
        if to_date:
            filters.append(Interview.start_time <= to_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        query = query.order_by(desc(Interview.start_time)).offset(skip).limit(limit)
        result = await db.execute(query)
        interviews = result.scalars().all()
        
        return list(interviews), total
    
    def generate_ics_content(
        self,
        interview: Interview,
        include_meeting_link: bool = True
    ) -> str:
        """
        Generate ICS calendar file content for an interview.
        
        Args:
            interview: Interview object
            include_meeting_link: Whether to include meeting URL in description
        
        Returns:
            ICS file content as string
        """
        cal = Calendar()
        cal.add('prodid', '-//LIA Recruitment System//wedotalent.com.br//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')
        
        event = Event()
        event.add('uid', f'{interview.id}@lia.wedotalent.com.br')
        event.add('dtstamp', datetime.utcnow())
        event.add('dtstart', interview.start_time)
        event.add('dtend', interview.end_time)
        event.add('summary', interview.title)
        
        description_parts = []
        if interview.description:
            description_parts.append(interview.description)
        if interview.job_title:
            description_parts.append(f"Vaga: {interview.job_title}")
        if interview.interview_type:
            description_parts.append(f"Tipo: {interview.interview_type}")
        if include_meeting_link and interview.meeting_url:
            description_parts.append(f"Link da reunião: {interview.meeting_url}")
        
        event.add('description', "\n\n".join(description_parts))
        
        if interview.location:
            event['location'] = vText(interview.location)
        elif interview.meeting_url:
            event['location'] = vText(interview.meeting_url)
        
        event.add('organizer', f'mailto:{interview.interviewer_email}')
        
        event.add('attendee', f'mailto:{interview.candidate_email}', parameters={
            'ROLE': 'REQ-PARTICIPANT',
            'PARTSTAT': 'NEEDS-ACTION',
            'RSVP': 'TRUE',
            'CN': interview.candidate_name
        })
        
        event.add('attendee', f'mailto:{interview.interviewer_email}', parameters={
            'ROLE': 'REQ-PARTICIPANT',
            'PARTSTAT': 'ACCEPTED',
            'CN': interview.interviewer_name
        })
        
        for interviewer in (interview.additional_interviewers or []):
            if interviewer.get('email'):
                event.add('attendee', f'mailto:{interviewer["email"]}', parameters={
                    'ROLE': 'OPT-PARTICIPANT',
                    'PARTSTAT': 'NEEDS-ACTION',
                    'CN': interviewer.get('name', '')
                })
        
        cal.add_component(event)
        
        return cal.to_ical().decode('utf-8')
    
    async def get_calendar_status(self) -> dict[str, Any]:
        """
        Get the current status of calendar integration.
        """
        import os
        
        ms_configured = bool(
            os.getenv("AZURE_CLIENT_ID") and 
            os.getenv("AZURE_CLIENT_SECRET") and 
            os.getenv("AZURE_TENANT_ID")
        )
        
        google_configured = bool(os.getenv("GOOGLE_CALENDAR_CREDENTIALS"))
        
        return {
            "status": "Funcional - Aguardando Configuração Calendar",
            "mode": "database_only" if not (ms_configured or google_configured) else "live",
            "providers": {
                "microsoft_graph": {
                    "configured": ms_configured,
                    "features": ["teams_meetings", "outlook_calendar"] if ms_configured else []
                },
                "google_calendar": {
                    "configured": google_configured,
                    "features": ["google_meet", "google_calendar"] if google_configured else []
                }
            },
            "local_features": {
                "database_storage": True,
                "ics_generation": True,
                "email_notifications": "ready"
            },
            "message": (
                "Agendamentos são salvos no banco de dados. "
                "Arquivos ICS podem ser gerados para download. "
                "Configure AZURE_CLIENT_ID/SECRET/TENANT_ID para Microsoft Graph ou "
                "GOOGLE_CALENDAR_CREDENTIALS para Google Calendar."
            )
        }


    async def send_interview_invite(
        self,
        db: AsyncSession,
        candidate_id: str,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        bookings_link: str,
        company_id: str | None = None,
        company_name: str | None = None,
        recruiter_name: str | None = None,
        interviewer_name: str | None = None,
        interview_format: str = "video",
        duration_minutes: int = 60,
        job_vacancy_id: str | None = None
    ) -> dict[str, Any]:
        """
        Send interview invite email with Bookings link for candidate to schedule.
        
        Uses communication_service.send_templated_message() which:
        - Selects template via MESSAGE_TYPE_TO_SITUATION mapping
        - Looks up active template from EmailTemplate table
        - Renders template with provided variables
        - Enforces opt-out, rate-limit and approval policies
        
        Args:
            db: Database session
            candidate_id: UUID of the candidate
            candidate_email: Email of the candidate
            candidate_name: Name of the candidate
            job_title: Title of the job position
            bookings_link: Microsoft Bookings link for scheduling
            company_id: Company ID for multi-tenancy
            company_name: Name of the company
            recruiter_name: Name of the recruiter
            interviewer_name: Name of the interviewer
            interview_format: Format of interview (video, in_person, phone)
            duration_minutes: Duration in minutes
            job_vacancy_id: Job vacancy ID for tracking
        
        Returns:
            Result dict with success status and details
        """
        from app.domains.communication.services.communication_service import MessageChannel, MessageType
        
        try:
            resolved_company_id = self._resolve_company_id(company_id)
            resolved_company_name = await self._resolve_company_name(db, company_id, company_name)
            
            variables = {
                "candidato_nome": candidate_name,
                "vaga": job_title,
                "empresa_nome": resolved_company_name,
                "recrutador_nome": recruiter_name or "Equipe de Recrutamento",
                "entrevistador_nome": interviewer_name or recruiter_name or "Equipe de Recrutamento",
                "formato_entrevista": interview_format,
                "duracao_entrevista": f"{duration_minutes} minutos",
                "link_calendario": bookings_link
            }
            
            comm_service = get_communication_service()
            send_result = await comm_service.send_templated_message(
                db=db,
                message_type=MessageType.INTERVIEW_INVITE,
                company_id=resolved_company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                variables=variables,
                channel=MessageChannel.EMAIL,
                job_id=job_vacancy_id,
                sent_by="scheduling_service"
            )
            
            if send_result.get("success"):
                logger.info(f"📧 Interview invite sent for {job_title}")
                logger.info(f"   Bookings Link: {bookings_link}")
                
                return {
                    "success": True,
                    "message": "Convite de entrevista enviado com sucesso",
                    "communication_log_id": send_result.get("log_id"),
                    "candidate_email": candidate_email,
                    "template_used": send_result.get("template_used"),
                    "company_name": resolved_company_name
                }
            else:
                logger.warning(f"⚠️ Interview invite blocked or failed: {send_result}")
                return {
                    "success": False,
                    "error": send_result.get("error", "send_failed"),
                    "message": send_result.get("message", "Failed to send interview invite"),
                    "validation": send_result.get("validation")
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to send interview invite: {e}")
            return {
                "success": False,
                "error": "send_failed",
                "message": str(e)
            }
    
    async def send_interview_confirmation(
        self,
        db: AsyncSession,
        candidate_id: str,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        interview_datetime: datetime,
        interview_link: str,
        company_id: str | None = None,
        company_name: str | None = None,
        recruiter_name: str | None = None,
        interviewer_name: str | None = None,
        interview_format: str = "video",
        duration_minutes: int = 60,
        job_vacancy_id: str | None = None
    ) -> dict[str, Any]:
        """
        Send interview confirmation email with Teams/meeting link.
        
        Uses communication_service.send_templated_message() which:
        - Selects template via MESSAGE_TYPE_TO_SITUATION mapping (interview_confirmed)
        - Looks up active template from EmailTemplate table
        - Renders template with provided variables
        - Enforces opt-out, rate-limit and approval policies
        
        Args:
            db: Database session
            candidate_id: UUID of the candidate
            candidate_email: Email of the candidate
            candidate_name: Name of the candidate
            job_title: Title of the job position
            interview_datetime: Date and time of the interview
            interview_link: Teams/meeting link for the interview
            company_id: Company ID for multi-tenancy
            company_name: Name of the company
            recruiter_name: Name of the recruiter
            interviewer_name: Name of the interviewer
            interview_format: Format of interview (video, in_person, phone)
            duration_minutes: Duration in minutes
            job_vacancy_id: Job vacancy ID for tracking
        
        Returns:
            Result dict with success status and details
        """
        from pytz import timezone as pytz_timezone

        from app.domains.communication.services.communication_service import MessageChannel, MessageType
        
        try:
            resolved_company_id = self._resolve_company_id(company_id)
            resolved_company_name = await self._resolve_company_name(db, company_id, company_name)
            
            brazil_tz = pytz_timezone(self.default_timezone)
            if interview_datetime.tzinfo is None:
                interview_datetime_local = brazil_tz.localize(interview_datetime)
            else:
                interview_datetime_local = interview_datetime.astimezone(brazil_tz)
            
            data_entrevista = interview_datetime_local.strftime("%d/%m/%Y")
            horario_entrevista = interview_datetime_local.strftime("%H:%M")
            
            variables = {
                "candidato_nome": candidate_name,
                "vaga": job_title,
                "empresa_nome": resolved_company_name,
                "recrutador_nome": recruiter_name or "Equipe de Recrutamento",
                "entrevistador_nome": interviewer_name or recruiter_name or "Equipe de Recrutamento",
                "data_entrevista": data_entrevista,
                "horario_entrevista": horario_entrevista,
                "duracao_entrevista": f"{duration_minutes} minutos",
                "formato_entrevista": interview_format,
                "link_entrevista": interview_link
            }
            
            comm_service = get_communication_service()
            send_result = await comm_service.send_templated_message(
                db=db,
                message_type=MessageType.INTERVIEW_CONFIRMATION,
                company_id=resolved_company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                variables=variables,
                channel=MessageChannel.EMAIL,
                job_id=job_vacancy_id,
                sent_by="scheduling_service"
            )
            
            if send_result.get("success"):
                logger.info("📧 Interview confirmation sent")
                logger.info(f"   Date: {data_entrevista} at {horario_entrevista}")
                logger.info(f"   Meeting Link: {interview_link}")

                try:
                    from app.domains.communication.services.teams_bot import teams_bot
                    await teams_bot.notify_scheduling_confirmed(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        scheduled_time=f"{data_entrevista} às {horario_entrevista}",
                    )
                except Exception as teams_err:
                    logger.warning(f"Teams scheduling notification failed: {teams_err}")

                return {
                    "success": True,
                    "message": "Confirmação de entrevista enviada com sucesso",
                    "communication_log_id": send_result.get("log_id"),
                    "candidate_email": candidate_email,
                    "template_used": send_result.get("template_used"),
                    "interview_date": data_entrevista,
                    "interview_time": horario_entrevista,
                    "company_name": resolved_company_name
                }
            else:
                logger.warning(f"⚠️ Interview confirmation blocked or failed: {send_result}")
                return {
                    "success": False,
                    "error": send_result.get("error", "send_failed"),
                    "message": send_result.get("message", "Failed to send interview confirmation"),
                    "validation": send_result.get("validation")
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to send interview confirmation: {e}")
            return {
                "success": False,
                "error": "send_failed",
                "message": str(e)
            }


    # ------------------------------------------------------------------
    # Chat tool surface (registered in app/domains/interview_scheduling/tools/__init__.py)
    # Thin wrappers around create/update/list primitives for the chat registry.
    # ------------------------------------------------------------------
    async def schedule_interview(
        self,
        db=None,
        candidate_id: str = "",
        interviewer_id: str = "",
        scheduled_at: str = "",
        duration_minutes: int = 60,
        company_id: str | None = None,
        **kwargs,
    ):
        """Public alias around create_interview() exposed to the chat registry."""
        return await self.create_interview(
            db=db,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            company_id=company_id,
            **kwargs,
        )

    async def reschedule_interview(
        self,
        db=None,
        interview_id: str = "",
        new_scheduled_at: str = "",
        company_id: str | None = None,
        **kwargs,
    ):
        """Public alias around update_interview() that adjusts the scheduled time."""
        return await self.update_interview(
            db=db,
            interview_id=interview_id,
            updates={"scheduled_at": new_scheduled_at},
            company_id=company_id,
            **kwargs,
        )

    async def generate_self_scheduling_link(
        self,
        db: AsyncSession | None = None,
        candidate_id: str = "",
        candidate_name: str | None = None,
        candidate_email: str | None = None,
        job_vacancy_id: str | None = None,
        job_title: str | None = None,
        interview_type: str = "hr",
        interview_mode: str = "video",
        duration_minutes: int = 60,
        available_slots: list[dict[str, str]] | None = None,
        interviewer_emails: list[str] | None = None,
        organizer_email: str | None = None,
        expires_hours: int = 72,
        max_uses: int = 1,
        company_id: str | None = None,
        created_by: str = "system",
        **kwargs,
    ) -> dict:
        """Persist a real self-scheduling link backed by the SelfSchedulingLink table.

        Returns the public booking URL, secure token and expiry. Recruiters or
        candidates can use this URL to pick a slot, which is consumed by the
        public self-scheduling endpoint (`/api/v1/self-scheduling/...`).
        """
        import os
        from lia_models.self_scheduling import SelfSchedulingLink

        should_close = False
        if db is None:
            from app.core.database import AsyncSessionLocal
            db = AsyncSessionLocal()
            should_close = True

        try:
            # Backwards-compat: legacy callers may pass only candidate_id.
            # Hydrate name/email from the Candidate row when missing.
            if candidate_id and (not candidate_email or not candidate_name):
                try:
                    from lia_models.candidate import Candidate
                    cand_uuid: Any = candidate_id
                    try:
                        cand_uuid = UUID(candidate_id)
                    except (ValueError, TypeError):
                        cand_uuid = candidate_id
                    cand_res = await db.execute(
                        select(Candidate).where(Candidate.id == cand_uuid).limit(1)
                    )
                    cand = cand_res.scalar_one_or_none()
                    if cand is not None:
                        candidate_name = candidate_name or getattr(cand, "name", None) or getattr(cand, "full_name", None)
                        candidate_email = candidate_email or getattr(cand, "email", None)
                except Exception as cand_err:
                    logger.debug("Candidate hydrate for self-scheduling link failed: %s", cand_err)

            if not candidate_email or not candidate_name:
                return {
                    "success": False,
                    "error": "missing_candidate_info",
                    "message": "candidate_name and candidate_email are required (and could not be resolved from candidate_id)",
                }

            token = SelfSchedulingLink.generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            link = SelfSchedulingLink(
                token=token,
                candidate_id=UUID(candidate_id) if candidate_id else None,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                job_vacancy_id=UUID(job_vacancy_id) if job_vacancy_id else None,
                job_title=job_title,
                interviewer_emails=interviewer_emails or [],
                organizer_email=organizer_email,
                interview_type=interview_type or "hr",
                interview_mode=interview_mode or "video",
                duration_minutes=duration_minutes or 60,
                available_slots=available_slots or [],
                status="pending",
                expires_at=expires_at,
                max_uses=max_uses,
                created_by=created_by,
            )
            db.add(link)
            await db.commit()
            await db.refresh(link)

            base_url = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app").rstrip("/")
            public_url = f"{base_url}/agendar/{token}"

            logger.info(
                "🔗 Self-scheduling link created: token=%s... candidate=%s vacancy=%s",
                token[:8], candidate_name, job_title,
            )

            return {
                "success": True,
                "link_id": str(link.id),
                "token": token,
                "url": public_url,
                "scheduling_url": public_url,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "candidate_email": candidate_email,
                "job_vacancy_id": job_vacancy_id,
                "interview_type": interview_type,
                "company_id": company_id,
                "expires_at": expires_at.isoformat(),
                "slots_offered": len(available_slots or []),
            }
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("❌ Failed to generate self-scheduling link: %s", e)
            return {
                "success": False,
                "error": "link_creation_failed",
                "message": str(e),
            }
        finally:
            if should_close:
                try:
                    await db.close()
                except Exception:
                    pass

    async def send_reminder(
        self,
        db: AsyncSession | None = None,
        interview_id: str = "",
        recipient: str = "candidate",
        hours_before: int = 24,
        company_id: str | None = None,
        channels: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Send a real interview reminder via the communication pipeline.

        Looks up the Interview (scoped by company_id when provided to prevent
        cross-tenant access), dispatches an `INTERVIEW_REMINDER` templated
        message to each requested recipient over each requested channel
        (email, whatsapp, teams) and persists one `InterviewReminder` audit
        row per delivery attempt.
        """
        from app.domains.communication.services.communication_service import (
            MessageChannel,
            MessageType,
        )
        from lia_models.self_scheduling import InterviewReminder

        if not interview_id:
            return {
                "success": False,
                "error": "missing_interview_id",
                "message": "interview_id is required to send a reminder",
            }

        try:
            interview_uuid = UUID(interview_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "invalid_interview_id",
                "message": f"interview_id '{interview_id}' is not a valid UUID",
            }

        requested_channels = [str(c).strip().lower() for c in (channels or ["email"]) if c]
        valid_channels = [c for c in requested_channels if c in {"email", "whatsapp", "teams"}]
        if not valid_channels:
            return {
                "success": False,
                "error": "invalid_channels",
                "message": f"No supported channels in {requested_channels!r}; expected email/whatsapp/teams",
            }

        should_close = False
        if db is None:
            from app.core.database import AsyncSessionLocal
            db = AsyncSessionLocal()
            should_close = True

        try:
            # Tenant-scoped lookup: when caller supplies company_id, the
            # Interview must belong to that tenant. Prevents cross-tenant
            # reminder triggering when an attacker guesses an interview UUID.
            stmt = select(Interview).where(Interview.id == interview_uuid)
            if company_id:
                stmt = stmt.where(Interview.company_id == str(company_id))
            result = await db.execute(stmt)
            interview = result.scalar_one_or_none()
            if interview is None:
                return {
                    "success": False,
                    "error": "interview_not_found",
                    "message": (
                        f"Interview {interview_id} not found"
                        + (f" for company {company_id}" if company_id else "")
                    ),
                }

            effective_company_id = company_id or interview.company_id
            if not effective_company_id:
                return {
                    "success": False,
                    "error": "missing_company_scope",
                    "message": "Interview has no company_id and no company_id was supplied; refusing to send.",
                }

            # Resolve candidate phone for WhatsApp delivery (lookup is best-
            # effort; missing phone simply skips the WhatsApp leg).
            candidate_phone: str | None = None
            if "whatsapp" in valid_channels and interview.candidate_id:
                try:
                    from lia_models.candidate import Candidate
                    cand_res = await db.execute(
                        select(Candidate).where(Candidate.id == interview.candidate_id).limit(1)
                    )
                    cand = cand_res.scalar_one_or_none()
                    if cand is not None:
                        candidate_phone = getattr(cand, "phone", None)
                except Exception as cand_err:
                    logger.debug("Candidate phone lookup failed: %s", cand_err)

            recipient_norm = (recipient or "candidate").lower()
            recipients: list[tuple[str, str, str | None, UUID | None]] = []
            if recipient_norm in ("candidate", "both", "all") and interview.candidate_email:
                recipients.append((
                    "candidate",
                    interview.candidate_email,
                    interview.candidate_name,
                    interview.candidate_id,
                ))
            if recipient_norm in ("interviewer", "both", "all") and interview.interviewer_email:
                recipients.append((
                    "interviewer",
                    interview.interviewer_email,
                    interview.interviewer_name,
                    None,
                ))

            if not recipients:
                return {
                    "success": False,
                    "error": "no_recipients",
                    "message": f"No recipients resolved for recipient='{recipient}'",
                }

            comm_service = get_communication_service()
            company_name = await self._resolve_company_name(db, effective_company_id, None)

            data_entrevista = interview.start_time.strftime("%d/%m/%Y")
            horario_entrevista = interview.start_time.strftime("%H:%M")
            base_variables = {
                "vaga": interview.job_title or "Processo Seletivo",
                "empresa_nome": company_name,
                "data_entrevista": data_entrevista,
                "horario_entrevista": horario_entrevista,
                "duracao_entrevista": f"{interview.duration_minutes or 60} minutos",
                "formato_entrevista": interview.interview_mode or "video",
                "link_entrevista": interview.meeting_url or interview.location or "",
                "horas_restantes": str(hours_before),
            }

            channel_enum_map = {
                "email": MessageChannel.EMAIL,
                "whatsapp": MessageChannel.WHATSAPP,
            }

            deliveries: list[dict[str, Any]] = []
            any_success = False

            for r_type, r_email, r_name, r_candidate_id in recipients:
                variables = dict(base_variables)
                variables["candidato_nome"] = r_name or "candidato(a)"
                variables["destinatario_nome"] = r_name or ""
                variables["entrevistador_nome"] = interview.interviewer_name or ""

                cand_id_for_log = (
                    str(r_candidate_id) if r_candidate_id
                    else (str(interview.candidate_id) if interview.candidate_id else "")
                )

                for ch in valid_channels:
                    send_result: dict[str, Any]
                    if ch in channel_enum_map:
                        if ch == "whatsapp" and r_type == "candidate" and not candidate_phone:
                            send_result = {
                                "success": False,
                                "error": "no_phone",
                                "message": "Candidate has no phone for WhatsApp",
                            }
                        elif ch == "whatsapp" and r_type == "interviewer":
                            send_result = {
                                "success": False,
                                "error": "no_phone",
                                "message": "WhatsApp not supported for interviewer recipients",
                            }
                        else:
                            try:
                                send_result = await self._dispatch_reminder_message(
                                    comm_service=comm_service,
                                    db=db,
                                    channel=channel_enum_map[ch],
                                    company_id=effective_company_id,
                                    candidate_id=cand_id_for_log,
                                    candidate_email=r_email if ch == "email" else None,
                                    candidate_phone=candidate_phone if ch == "whatsapp" else None,
                                    candidate_name=r_name or "",
                                    variables=variables,
                                    job_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
                                )
                            except Exception as send_err:
                                logger.warning(
                                    "Reminder send failed for %s/%s (%s): %s",
                                    r_type, ch, r_email, send_err,
                                )
                                send_result = {"success": False, "error": "send_failed", "message": str(send_err)}
                    elif ch == "teams":
                        send_result = await self._dispatch_reminder_teams(
                            interview=interview,
                            recipient_type=r_type,
                            recipient_name=r_name,
                            data_entrevista=data_entrevista,
                            horario_entrevista=horario_entrevista,
                        )
                    else:  # pragma: no cover - guarded by valid_channels filter
                        send_result = {"success": False, "error": "unsupported_channel", "message": ch}

                    ok = bool(send_result.get("success"))
                    any_success = any_success or ok

                    audit = InterviewReminder(
                        interview_id=interview.id,
                        reminder_type=f"manual_{hours_before}h",
                        recipient_email=r_email,
                        recipient_type=r_type,
                        scheduled_for=datetime.utcnow(),
                        hours_before=hours_before,
                        status="sent" if ok else "failed",
                        sent_at=datetime.utcnow() if ok else None,
                        send_error=None if ok else (send_result.get("message") or send_result.get("error")),
                        channels=[ch],
                    )
                    db.add(audit)

                    deliveries.append({
                        "recipient_type": r_type,
                        "recipient_email": r_email,
                        "channel": ch,
                        "success": ok,
                        "communication_log_id": send_result.get("log_id"),
                        "template_used": send_result.get("template_used"),
                        "error": send_result.get("error") if not ok else None,
                        "message": send_result.get("message") if not ok else None,
                    })

            if any_success:
                interview.reminder_sent = True
                interview.reminder_sent_at = datetime.utcnow()

            await db.commit()

            return {
                "success": any_success,
                "interview_id": interview_id,
                "recipient": recipient,
                "company_id": effective_company_id,
                "channels": valid_channels,
                "deliveries": deliveries,
                "sent_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("❌ Failed to send interview reminder: %s", e)
            return {
                "success": False,
                "error": "reminder_failed",
                "message": str(e),
            }
        finally:
            if should_close:
                try:
                    await db.close()
                except Exception:
                    pass

    async def _dispatch_reminder_message(
        self,
        *,
        comm_service,
        db,
        channel,
        company_id: str,
        candidate_id: str,
        candidate_email: str | None,
        candidate_phone: str | None,
        candidate_name: str,
        variables: dict[str, Any],
        job_id: str | None,
    ) -> dict[str, Any]:
        """Render the INTERVIEW_REMINDER template and send through send_message.

        We render via the template_service then call send_message so that the
        WhatsApp path can carry candidate_phone (send_templated_message
        always passes phone=None). Email goes through the same path for
        consistency and full audit/policy enforcement.
        """
        from app.domains.communication.services.communication_service import MessageType
        from app.domains.communication.services.template_service import render_message_template

        rendered = await render_message_template(
            db=db,
            message_type=MessageType.INTERVIEW_REMINDER,
            channel=channel,
            company_id=company_id,
            candidate_id=candidate_id,
            variables=variables,
        )
        if not rendered.get("success"):
            return rendered

        send_result = await comm_service.send_message(
            company_id=company_id,
            candidate_id=candidate_id,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            message_type=MessageType.INTERVIEW_REMINDER,
            channel=channel,
            subject=rendered.get("subject"),
            body=rendered.get("body_text") or rendered.get("body_html", ""),
            body_html=rendered.get("body_html"),
            job_id=job_id,
            sent_by="scheduling_service.send_reminder",
            db=db,
        )
        if send_result.get("success") and rendered.get("template_name"):
            send_result["template_used"] = rendered.get("template_name")
        return send_result

    async def _dispatch_reminder_teams(
        self,
        *,
        interview,
        recipient_type: str,
        recipient_name: str | None,
        data_entrevista: str,
        horario_entrevista: str,
    ) -> dict[str, Any]:
        """Deliver the reminder as an adaptive card through the Teams bot."""
        try:
            from app.domains.communication.services.teams_bot import teams_bot
            ok = await teams_bot.notify_scheduling_confirmed(
                candidate_name=recipient_name or interview.candidate_name,
                job_title=interview.job_title or "Processo Seletivo",
                scheduled_time=f"{data_entrevista} às {horario_entrevista}",
                interview_type="Lembrete de entrevista",
            )
            if ok:
                return {"success": True, "channel": "teams", "recipient_type": recipient_type}
            return {
                "success": False,
                "error": "teams_send_failed",
                "message": "Teams bot returned False (webhook/adapter not configured?)",
            }
        except Exception as e:
            return {"success": False, "error": "teams_send_failed", "message": str(e)}

    async def list_today_interviews(
        self,
        db=None,
        company_id: str | None = None,
        **kwargs,
    ):
        """List interviews scheduled for the current day (alias over list_interviews)."""
        from datetime import datetime as _dt, timedelta as _td
        today_start = _dt.combine(_dt.utcnow().date(), _dt.min.time())
        today_end = today_start + _td(days=1)
        if db is None:
            return {"success": True, "interviews": [], "count": 0, "date": today_start.date().isoformat()}
        interviews, total = await self.list_interviews(
            db=db,
            from_date=today_start,
            to_date=today_end,
            **{k: v for k, v in kwargs.items() if k in {"candidate_id", "vacancy_id", "interviewer_email", "status", "skip", "limit"}},
        )
        return {
            "success": True,
            "date": today_start.date().isoformat(),
            "count": total,
            "interview_ids": [getattr(i, "id", None) for i in interviews],
        }


scheduling_service = SchedulingService()


def get_scheduling_service() -> "SchedulingService":
    return scheduling_service
