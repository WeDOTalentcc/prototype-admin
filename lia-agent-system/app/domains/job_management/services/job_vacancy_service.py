"""
Job Vacancy Service - Persistence and utilities for job vacancy creation.

Integrates:
- Manager inference from company structure
- Deadline calculation from pipeline SLAs
- Automatic recruiter/created_by population
"""
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    pass
import logging
from datetime import datetime, timedelta

from app.schemas.job_vacancy_state import (
    InterviewStage,
    JobVacancyState,
    SalaryRange,
    ScreeningQuestion,
    TechnicalRequirement,
    Timeline,
    WeeklyBreakdown,
)

logger = logging.getLogger(__name__)


async def infer_manager_email_if_missing(
    manager_name: str | None,
    manager_email: str | None,
    company_id: str,
    department: str | None = None
) -> str | None:
    """
    Infer manager email if not provided but name is available.
    Uses the manager_inference_service to search company structure.
    """
    if manager_email:
        return manager_email
    
    if not manager_name:
        return None
    
    try:
        from app.shared.services.manager_inference_service import manager_inference_service
        result = await manager_inference_service.get_manager_by_name(
            manager_name=manager_name,
            company_id=company_id,
            department=department
        )
        if result and result.get("email"):
            logger.info("Inferred manager email for job (identity redacted)")
            return result["email"]
    except Exception as e:
        logger.warning(f"Failed to infer manager email: {e}")
    
    return None


async def calculate_job_deadlines(
    company_id: str,
    pipeline_template_id: str | None = None,
    start_date: datetime | None = None
) -> dict[str, Any]:
    """
    Calculate job deadlines from pipeline SLAs.
    Returns dict with deadline_screening, deadline_shortlist, deadline_closing, deadline.
    """
    try:
        from app.shared.services.deadline_calculator_service import deadline_calculator_service
        return await deadline_calculator_service.calculate_deadlines_from_pipeline(
            pipeline_template_id=pipeline_template_id,
            company_id=company_id,
            start_date=start_date
        )
    except Exception as e:
        logger.warning(f"Failed to calculate deadlines: {e}")
        return {}


def infer_whatsapp_template_type(
    is_confidential: bool = False,
    visibility: str | None = None
) -> str:
    """
    Infer WhatsApp template type based on confidentiality settings.
    """
    if is_confidential or visibility == "confidential":
        return "confidential"
    return "cold"


class JobVacancyService:
    """Service for job vacancy creation workflow."""
    
    @staticmethod
    def load_from_workflow_data(workflow_data: dict[str, Any]) -> JobVacancyState | None:
        """
        Load JobVacancyState from conversation workflow_data.
        """
        if "job_vacancy_state" not in workflow_data:
            return None
        
        try:
            return JobVacancyState(**workflow_data["job_vacancy_state"])
        except Exception as e:
            logger.error(f"Failed to load JobVacancyState: {e}")
            return None
    
    @staticmethod
    def save_to_workflow_data(state: JobVacancyState, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """
        Save JobVacancyState to conversation workflow_data.
        """
        workflow_data["job_vacancy_state"] = state.model_dump(mode="json")
        return workflow_data
    
    @staticmethod
    def normalize_seniority(seniority: str) -> str | None:
        """Normalize seniority level."""
        mapping = {
            "junior": "Júnior",
            "júnior": "Júnior",
            "jr": "Júnior",
            "pleno": "Pleno",
            "senior": "Sênior",
            "sênior": "Sênior",
            "sr": "Sênior",
            "especialista": "Especialista",
            "staff": "Especialista",
            "principal": "Especialista",
        }
        return mapping.get(seniority.lower())
    
    @staticmethod
    def normalize_work_model(work_model: str) -> str | None:
        """Normalize work model."""
        mapping = {
            "presencial": "presencial",
            "híbrido": "híbrido",
            "hibrido": "híbrido",
            "remoto": "remoto",
            "100% remoto": "remoto",
            "home office": "remoto",
        }
        return mapping.get(work_model.lower())
    
    @staticmethod
    def parse_salary_range(salary_text: str) -> SalaryRange | None:
        """
        Parse salary range from text.
        Examples: "R$ 12.000 a R$ 18.000", "12k-18k", "15000"
        """
        import re
        
        # Remove R$, k suffix, dots, and clean
        cleaned = salary_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        
        # Handle "k" multiplier
        if "k" in cleaned.lower():
            cleaned = cleaned.lower().replace("k", "000")
        
        # Try to find two numbers (range)
        numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
        
        if len(numbers) >= 2:
            return SalaryRange(min=float(numbers[0]), max=float(numbers[1]))
        elif len(numbers) == 1:
            # Single value - use as min, estimate max as +20%
            base = float(numbers[0])
            return SalaryRange(min=base, max=base * 1.2)
        
        return None
    
    @staticmethod
    def calculate_timeline(
        interview_stages: list[InterviewStage],
        target_weeks: int = 4
    ) -> Timeline:
        """
        Calculate timeline based on interview stages.
        """
        # Calculate shortlist deadline (week 1)
        shortlist_date = datetime.utcnow() + timedelta(weeks=1)
        
        # Create weekly breakdown
        weekly_breakdown = []
        
        # Week 1: Sourcing & Screening
        weekly_breakdown.append(WeeklyBreakdown(
            week=1,
            focus="Sourcing, Triagem e Screening",
            deadline=(datetime.utcnow() + timedelta(weeks=1)).strftime("%d/%m/%Y"),
            status="pending"
        ))
        
        # Weeks 2-(N-1): Interviews
        interview_weeks = target_weeks - 2 if target_weeks > 2 else 1
        for i in range(interview_weeks):
            weekly_breakdown.append(WeeklyBreakdown(
                week=2 + i,
                focus=f"Entrevistas ({', '.join([s.stage_name for s in interview_stages[:2]])})" if interview_stages else "Entrevistas",
                deadline=(datetime.utcnow() + timedelta(weeks=2 + i)).strftime("%d/%m/%Y"),
                status="pending"
            ))
        
        # Last week: Decision & Offer
        weekly_breakdown.append(WeeklyBreakdown(
            week=target_weeks,
            focus="Decisão, Oferta e Exames",
            deadline=(datetime.utcnow() + timedelta(weeks=target_weeks)).strftime("%d/%m/%Y"),
            status="pending"
        ))
        
        return Timeline(
            shortlist_deadline=shortlist_date.strftime("%d/%m/%Y"),
            total_weeks=target_weeks,
            weekly_breakdown=weekly_breakdown
        )
    
    @staticmethod
    def select_whatsapp_template(
        is_confidential: bool,
        candidate_in_database: bool = False
    ) -> str:
        """
        Select WhatsApp template based on confidentiality and candidate status.
        
        Logic from documents:
        1. If confidential → "confidential"
        2. If not confidential + candidate in DB → "reengagement"
        3. If not confidential + new candidate → "cold"
        """
        if is_confidential:
            return "confidential"
        elif candidate_in_database:
            return "reengagement"
        else:
            return "cold"
    
    @staticmethod
    def suggest_screening_questions(
        job_title: str,
        technical_requirements: list[TechnicalRequirement],
        target_sector: str | None = None
    ) -> list[ScreeningQuestion]:
        """
        Suggest screening questions based on job requirements.
        """
        questions = []
        
        # Question 1: Experience alignment
        questions.append(ScreeningQuestion(
            id="sq_1",
            question=f"Você tem experiência prévia como {job_title}? Se sim, por quanto tempo?",
            type="text",
            weight=5
        ))
        
        # Question 2: Technical skills (if available)
        if technical_requirements:
            main_techs = [tr.technology for tr in technical_requirements if tr.required][:3]
            if main_techs:
                questions.append(ScreeningQuestion(
                    id="sq_2",
                    question=f"Qual é o seu nível de experiência com {', '.join(main_techs)}?",
                    type="text",
                    weight=5
                ))
        
        # Question 3: Sector experience (if specified)
        if target_sector:
            questions.append(ScreeningQuestion(
                id="sq_3",
                question=f"Você já trabalhou no setor de {target_sector}? Descreva brevemente sua experiência.",
                type="text",
                weight=4
            ))
        
        # Question 4: Availability
        questions.append(ScreeningQuestion(
            id="sq_4",
            question="Qual é a sua disponibilidade para iniciar em uma nova posição?",
            type="text",
            weight=3
        ))
        
        return questions
    
    @staticmethod
    def generate_frame(
        frame_type: str,
        state: JobVacancyState
    ) -> str:
        """
        Generate visual frame (Markdown table) for validation.
        """
        if frame_type == "matriz_tecnica":
            return JobVacancyService._generate_technical_matrix_frame(state)
        elif frame_type == "cronograma":
            return JobVacancyService._generate_timeline_frame(state)
        elif frame_type == "estrutura_organizacional":
            return JobVacancyService._generate_org_structure_frame(state)
        elif frame_type == "fluxo_entrevistas":
            return JobVacancyService._generate_interview_flow_frame(state)
        else:
            return ""
    
    @staticmethod
    def _generate_technical_matrix_frame(state: JobVacancyState) -> str:
        """Generate technical requirements matrix."""
        if not state.technical_requirements:
            return "Nenhum requisito técnico definido ainda."
        
        frame = "\n**📊 MATRIZ DE REQUISITOS TÉCNICOS**\n\n"
        frame += "| Categoria | Tecnologia | Nível Mínimo | Obrigatório |\n"
        frame += "|-----------|------------|--------------|-------------|\n"
        
        for req in state.technical_requirements:
            required = "✅ Sim" if req.required else "⚪ Desejável"
            frame += f"| {req.category} | {req.technology} | {req.level} | {required} |\n"
        
        return frame
    
    @staticmethod
    def _generate_timeline_frame(state: JobVacancyState) -> str:
        """Generate timeline/chronogram."""
        if not state.timeline:
            return "Timeline ainda não calculado."
        
        frame = "\n**📅 CRONOGRAMA INTELIGENTE**\n\n"
        frame += "| Semana | Foco Principal | Data Limite | Status |\n"
        frame += "|--------|----------------|-------------|--------|\n"
        
        for week in state.timeline.weekly_breakdown:
            status_emoji = "⏳" if week.status == "pending" else "✅" if week.status == "completed" else "🔄"
            frame += f"| Semana {week.week} | {week.focus} | {week.deadline} | {status_emoji} |\n"
        
        frame += f"\n**Previsão de Conclusão:** {state.timeline.weekly_breakdown[-1].deadline}\n"
        frame += f"**Duração Total:** {state.timeline.total_weeks} semanas\n"
        
        return frame
    
    @staticmethod
    def _generate_org_structure_frame(state: JobVacancyState) -> str:
        """Generate organizational structure frame."""
        if not state.organizational_structure:
            return "Estrutura organizacional ainda não definida."
        
        org = state.organizational_structure
        frame = "\n**🏢 ESTRUTURA ORGANIZACIONAL**\n\n"
        frame += f"```\n[Gestor Direto: {org.direct_manager}]\n"
        frame += "    |\n"
        frame += f"    +-- [Equipe de Produto ({org.team_size} pessoas)]\n"
        frame += "        |\n"
        frame += f"        +-- (Você) {state.job_title or 'Nova Vaga'}\n"
        
        for member in org.team_composition:
            frame += f"        +-- {member.count}x {member.role} ({member.level})\n"
        
        frame += "```\n"
        
        return frame
    
    @staticmethod
    def _generate_interview_flow_frame(state: JobVacancyState) -> str:
        """Generate interview flow frame."""
        if not state.interview_stages:
            return "Fluxo de entrevistas ainda não definido."
        
        frame = "\n**🎯 FLUXO DE ENTREVISTAS**\n\n"
        frame += "| Etapa | Entrevistador(es) | Formato | Duração | Janela de Agendamento |\n"
        frame += "|-------|-------------------|---------|---------|----------------------|\n"
        
        for i, stage in enumerate(state.interview_stages, 1):
            interviewers = ", ".join(stage.interviewers[:2])
            if len(stage.interviewers) > 2:
                interviewers += f" +{len(stage.interviewers) - 2}"
            
            frame += f"| {i}. {stage.stage_name} | {interviewers} | {stage.format} | {stage.duration} min | {stage.scheduling_window} |\n"
        
        return frame


    @staticmethod
    async def _populate_default_interview_stages(
        state: JobVacancyState,
        company_id: str,
        db,
    ) -> JobVacancyState:
        """Populate interview stages from company pipeline if not set by user.

        Falls back to canonical defaults derived from DEFAULT_RECRUITMENT_STAGES.
        """
        from app.domains.job_management.services.interview_stage_defaults import (
            get_default_vacancy_interview_stages,
            map_pipeline_to_vacancy_stages,
        )

        try:
            from app.domains.recruiter_assistant.services.pipeline_stage_service import pipeline_stage_service

            stages = await pipeline_stage_service._get_company_stages(db, company_id)
            if stages:
                interview_stages = map_pipeline_to_vacancy_stages(stages)
                if interview_stages:
                    state.interview_stages = interview_stages
                    logger.info(
                        f"Populated {len(interview_stages)} default interview stages from company pipeline"
                    )
                    return state
        except Exception as e:
            logger.warning(f"Failed to load company pipeline for interview stages: {e}", exc_info=True)

        state.interview_stages = get_default_vacancy_interview_stages()
        logger.info("Populated interview stages from canonical DEFAULT_RECRUITMENT_STAGES")

        return state

    @staticmethod
    async def finalize_job_vacancy(
        state: JobVacancyState,
        conversation_id: str,
        created_by: str,
        db,
        company_id: str,
        current_user: Any | None = None,
        pipeline_template_id: str | None = None
    ):
        """
        Finalize job vacancy creation and persist to PostgreSQL.
        
        Integrates:
        - Manager email inference from company structure
        - Deadline calculation from pipeline SLAs
        - Automatic recruiter population from logged-in user
        - WhatsApp template type inference from confidentiality
        
        Args:
            state: JobVacancyState with all collected data
            conversation_id: UUID of the conversation
            created_by: User who created the vacancy
            db: Database session
            company_id: Company ID for multi-tenancy
            current_user: Currently logged-in user (for recruiter auto-fill)
            pipeline_template_id: Pipeline template ID for deadline calculation
        
        Returns:
            JobVacancy ORM object
        """
        import uuid
        from datetime import datetime

        from lia_models.job_vacancy import JobVacancy

        if not state.interview_stages:
            state = await JobVacancyService._populate_default_interview_stages(state, company_id, db)

        # === PEOPLE INFERENCE ===
        # Infer manager email if name provided but email missing
        manager_email = await infer_manager_email_if_missing(
            manager_name=state.manager_name,
            manager_email=state.manager_email,
            company_id=company_id,
            department=state.department
        )
        
        # Auto-fill recruiter from current user if not provided
        recruiter_name = state.recruiter_name
        recruiter_email = state.recruiter_email
        if current_user and not recruiter_email:
            recruiter_email = getattr(current_user, 'email', None)
            if not recruiter_name:
                recruiter_name = getattr(current_user, 'name', None) or getattr(current_user, 'full_name', None)
            logger.info("Auto-filled recruiter from current user (email redacted)")
        
        # === DEADLINE CALCULATION ===
        # Calculate deadlines from pipeline SLAs
        deadlines = await calculate_job_deadlines(
            company_id=company_id,
            pipeline_template_id=pipeline_template_id,
            start_date=datetime.utcnow()
        )
        
        # === WHATSAPP TEMPLATE INFERENCE ===
        whatsapp_template_type = state.whatsapp_template_type
        if not whatsapp_template_type:
            whatsapp_template_type = infer_whatsapp_template_type(
                is_confidential=state.is_confidential or False,
                visibility=getattr(state, 'visibility', None)
            )
        
        job_vacancy = JobVacancy(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id) if conversation_id else None,
            company_id=company_id,
            
            # Basic information
            title=state.job_title,
            department=state.department,
            location=state.location,
            work_model=state.work_model,
            employment_type=state.employment_type,
            seniority_level=state.seniority,
            
            # Description
            description=state.description,

            # T-1166 — responsibilities (job duties) persisted separately from
            # requirements. IntakeExtractor emits `responsibilities` in the
            # JobIntakePayload; the wizard state forwards it via `responsibilities`
            # (falls back to the legacy attribute or empty list defensively, since
            # not every state mutation path populates it yet).
            responsibilities=list(getattr(state, "responsibilities", None) or []),

            # Technical requirements
            technical_requirements=[req.model_dump() for req in state.technical_requirements],
            languages=[lang.model_dump() for lang in state.languages],
            behavioral_competencies=[comp.model_dump() for comp in state.behavioral_competencies],
            
            # Salary & benefits
            salary_range=state.salary_range.model_dump() if state.salary_range else None,
            benefits=state.benefits,
            
            # Organizational structure
            organizational_structure=state.organizational_structure.model_dump() if state.organizational_structure else None,
            
            # Interview process
            interview_stages=[stage.model_dump() for stage in state.interview_stages],
            screening_questions=[q.model_dump() for q in state.screening_questions],
            
            # Timeline
            timeline=state.timeline.model_dump() if state.timeline else None,
            
            # Governance
            governance_rules=state.governance_rules.model_dump() if state.governance_rules else None,
            
            # WhatsApp template (inferred from confidentiality)
            whatsapp_template_type=whatsapp_template_type,
            
            # Targeting
            target_sector=state.target_sector,
            target_segment=state.target_segment,
            target_audience=state.target_audience,
            
            # People (with inference)
            manager=state.manager_name,
            manager_email=manager_email,
            recruiter=recruiter_name,
            recruiter_email=recruiter_email,
            created_by=created_by,
            
            # Confidentiality
            is_confidential=state.is_confidential or False,
            
            # Deadlines (calculated from pipeline SLAs)
            deadline_screening=deadlines.get("deadline_screening"),
            deadline_shortlist=deadlines.get("deadline_shortlist"),
            deadline_closing=deadlines.get("deadline_closing"),
            deadline=deadlines.get("deadline"),
            
            # Status
            status="Rascunho",  # Will be Ativa after approval
            stage="Planejamento",
            approval_status="pendente",
            
            # Timestamps
            created_at=state.created_at,
            updated_at=datetime.utcnow(),
            published_at=state.published_at
        )
        
        db.add(job_vacancy)
        await db.commit()
        await db.refresh(job_vacancy)
        
        logger.info(f"✅ Job vacancy finalized: {job_vacancy.id} - {job_vacancy.title}")
        logger.info("Manager assigned (identity redacted)", extra={"job_id": str(job_vacancy.id)})
        logger.info("Recruiter assigned (identity redacted)", extra={"job_id": str(job_vacancy.id)})
        logger.info(f"   Deadline: {deadlines.get('deadline')}")
        
        return job_vacancy


    @staticmethod
    def _normalize_skills_to_objects(skills: Any) -> list[dict[str, Any]]:
        """Convert skills list to proper object format for database."""
        if not skills:
            return []
        
        normalized = []
        for skill in skills:
            if isinstance(skill, str):
                normalized.append({
                    "name": skill,
                    "level": "intermediate",
                    "required": True,
                    "years_experience": None
                })
            elif isinstance(skill, dict):
                normalized.append(skill)
        
        return normalized
    
    @staticmethod
    def _normalize_salary_range(salary_range: Any) -> dict[str, Any] | None:
        """Normalize salary range to proper format."""
        if not salary_range:
            return None
        
        if isinstance(salary_range, dict):
            return {
                "min": salary_range.get("min", 0),
                "max": salary_range.get("max", 0),
                "currency": salary_range.get("currency", "BRL"),
                "type": salary_range.get("type", "monthly"),
            }
        
        return None
    
    @staticmethod
    def _normalize_questions(questions: Any) -> list[dict[str, Any]]:
        """Normalize screening questions to proper format."""
        if not questions:
            return []
        
        normalized = []
        for i, q in enumerate(questions):
            if isinstance(q, str):
                normalized.append({
                    "id": str(i + 1),
                    "question": q,
                    "type": "text",
                    "required": True,
                })
            elif isinstance(q, dict):
                normalized.append(q)
        
        return normalized

    @staticmethod
    async def create_from_wizard_draft(
        draft: dict[str, Any],
        conversation_id: str,
        created_by: str,
        company_id: str,
        db,
        use_session_for_idempotency: bool = False,
    ):
        """
        Create job vacancy directly from wizard draft dictionary.
        
        Includes field normalization to ensure proper database schema compliance.
        
        Args:
            draft: Dictionary with job fields from wizard
            conversation_id: UUID of the conversation or session ID
            created_by: User who created the vacancy
            company_id: Company ID for multi-tenancy
            db: Database session
            use_session_for_idempotency: If True, store session_id in additional_data only (not as FK)
        
        Returns:
            JobVacancy ORM object
        """
        import uuid

        from lia_models.job_vacancy import JobVacancy
        
        title = draft.get("title") or draft.get("job_title") or "Vaga sem título"
        
        raw_skills = draft.get("technical_skills") or draft.get("required_skills") or []
        technical_requirements = JobVacancyService._normalize_skills_to_objects(raw_skills)
        
        raw_behavioral = draft.get("behavioral_competencies") or []
        behavioral_competencies = JobVacancyService._normalize_skills_to_objects(raw_behavioral)
        
        raw_salary = draft.get("salary_range") or draft.get("salaryRange")
        salary_range = JobVacancyService._normalize_salary_range(raw_salary)
        
        raw_questions = draft.get("screening_questions") or draft.get("wsi_questions") or []
        screening_questions = JobVacancyService._normalize_questions(raw_questions)
        
        conv_uuid = None
        if conversation_id and not use_session_for_idempotency:
            try:
                conv_uuid = uuid.UUID(conversation_id)
            except (ValueError, TypeError):
                pass
        
        job_vacancy = JobVacancy(
            id=uuid.uuid4(),
            conversation_id=conv_uuid,
            company_id=company_id,
            
            title=title,
            department=draft.get("department"),
            location=draft.get("location"),
            work_model=draft.get("work_model") or draft.get("workModel"),
            employment_type=draft.get("employment_type") or draft.get("employmentType") or "CLT",
            seniority_level=draft.get("seniority") or draft.get("seniority_level"),
            
            description=draft.get("description") or draft.get("job_description"),

            # T-1166 — accept responsibilities from wizard draft when present.
            # JobDraft model currently lacks a dedicated column, so the wizard
            # passes it via the draft dict (e.g. from IntakeExtractor payload).
            responsibilities=list(
                draft.get("responsibilities")
                or draft.get("job_responsibilities")
                or []
            ),

            technical_requirements=technical_requirements,
            behavioral_competencies=behavioral_competencies,
            
            salary_range=salary_range,
            salary=draft.get("salary"),
            benefits=draft.get("benefits") or [],
            
            manager=draft.get("manager") or draft.get("hiring_manager"),
            manager_email=draft.get("manager_email"),
            recruiter=draft.get("recruiter"),
            recruiter_email=draft.get("recruiter_email"),
            
            screening_questions=screening_questions,
            
            is_confidential=draft.get("is_confidential", False),
            
            status="Rascunho",
            stage="Planejamento",
            approval_status="pendente",
            
            additional_data={"wizard_session_id": conversation_id} if conversation_id else {},
            
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(job_vacancy)
        
        logger.info(f"✅ Job vacancy created from wizard draft: {job_vacancy.id} - {title}")
        
        return job_vacancy


# Global service instance
job_vacancy_service = JobVacancyService()
