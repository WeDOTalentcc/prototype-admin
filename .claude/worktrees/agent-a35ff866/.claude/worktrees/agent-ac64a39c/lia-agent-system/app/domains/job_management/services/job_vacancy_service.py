"""
Job Vacancy Service - Persistence and utilities for job vacancy creation.

Integrates:
- Manager inference from company structure
- Deadline calculation from pipeline SLAs
- Automatic recruiter/created_by population
"""
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
from datetime import datetime, timedelta
import logging
import json

from app.schemas.job_vacancy_state import (
    JobVacancyState,
    SalaryRange,
    TechnicalRequirement,
    Language,
    BehavioralCompetency,
    InterviewStage,
    ScreeningQuestion,
    OrganizationalStructure,
    TeamComposition,
    Timeline,
    WeeklyBreakdown,
    GovernanceRules
)

logger = logging.getLogger(__name__)


async def infer_manager_email_if_missing(
    manager_name: Optional[str],
    manager_email: Optional[str],
    company_id: str,
    department: Optional[str] = None
) -> Optional[str]:
    """
    Infer manager email if not provided but name is available.
    Uses the manager_inference_service to search company structure.
    """
    if manager_email:
        return manager_email
    
    if not manager_name:
        return None
    
    try:
        from app.services.manager_inference_service import manager_inference_service
        result = await manager_inference_service.get_manager_by_name(
            manager_name=manager_name,
            company_id=company_id,
            department=department
        )
        if result and result.get("email"):
            logger.info(f"✅ Inferred manager email for {manager_name}: {result['email']}")
            return result["email"]
    except Exception as e:
        logger.warning(f"Failed to infer manager email: {e}")
    
    return None


async def calculate_job_deadlines(
    company_id: str,
    pipeline_template_id: Optional[str] = None,
    start_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculate job deadlines from pipeline SLAs.
    Returns dict with deadline_screening, deadline_shortlist, deadline_closing, deadline.
    """
    try:
        from app.services.deadline_calculator_service import deadline_calculator_service
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
    visibility: Optional[str] = None
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
    def load_from_workflow_data(workflow_data: Dict[str, Any]) -> Optional[JobVacancyState]:
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
    def save_to_workflow_data(state: JobVacancyState, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save JobVacancyState to conversation workflow_data.
        """
        workflow_data["job_vacancy_state"] = state.model_dump(mode="json")
        return workflow_data
    
    @staticmethod
    def normalize_seniority(seniority: str) -> Optional[str]:
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
    def normalize_work_model(work_model: str) -> Optional[str]:
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
    def parse_salary_range(salary_text: str) -> Optional[SalaryRange]:
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
        interview_stages: List[InterviewStage],
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
        technical_requirements: List[TechnicalRequirement],
        target_sector: Optional[str] = None
    ) -> List[ScreeningQuestion]:
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
    async def finalize_job_vacancy(
        state: JobVacancyState,
        conversation_id: str,
        created_by: str,
        db,
        company_id: str = "default",
        current_user: Optional[Any] = None,
        pipeline_template_id: Optional[str] = None
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
            company_id: Company ID for multi-tenancy (defaults to "default")
            current_user: Currently logged-in user (for recruiter auto-fill)
            pipeline_template_id: Pipeline template ID for deadline calculation
        
        Returns:
            JobVacancy ORM object
        """
        from app.models.job_vacancy import JobVacancy
        from datetime import datetime
        import uuid
        
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
            logger.info(f"✅ Auto-filled recruiter from current user: {recruiter_email}")
        
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
        logger.info(f"   Manager: {state.manager_name} ({manager_email})")
        logger.info(f"   Recruiter: {recruiter_name} ({recruiter_email})")
        logger.info(f"   Deadline: {deadlines.get('deadline')}")
        
        return job_vacancy


    @staticmethod
    def _normalize_skills_to_objects(skills: Any) -> List[Dict[str, Any]]:
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
    def _normalize_salary_range(salary_range: Any) -> Optional[Dict[str, Any]]:
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
    def _normalize_questions(questions: Any) -> List[Dict[str, Any]]:
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
        draft: Dict[str, Any],
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
        from app.models.job_vacancy import JobVacancy
        import uuid
        
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
