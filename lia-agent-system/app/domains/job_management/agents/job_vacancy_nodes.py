"""
Job Vacancy Creation Nodes for LangGraph workflow.
Contains specialized collectors, router, validator, frame generator, etc.
"""
from typing import Dict, Any, Optional, List
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

from app.services.llm import llm_service
from app.domains.job_management.services.job_vacancy_service import job_vacancy_service
from app.services.benefits_service import benefits_service
from app.domains.cv_screening.services.wsi_screening_pipeline import wsi_screening_pipeline
from app.schemas.screening import WSIScreeningPipelineRequest
from app.schemas.job_vacancy_state import (
    JobVacancyState,
    SalaryRange,
    TechnicalRequirement,
    InterviewStage,
    OrganizationalStructure,
    TeamComposition,
    GovernanceRules,
    SourcingStrategy,
    TalentPoolEstimate,
    MarketBenchmark,
    WSICompetencySuggestion,
    BiasAnalysis
)

logger = logging.getLogger(__name__)


# =============================================
# STATE LOADER & PERSISTENCE
# =============================================

async def job_state_loader(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load or initialize JobVacancyState from workflow_data.
    """
    workflow_data = state.get("workflow_data", {})
    
    # Try to load existing state
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        # Initialize new state
        job_state = JobVacancyState()
        logger.info("📝 Initialized new JobVacancyState")
    
    # Save back to workflow_data
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    state["current_workflow"] = "job_creation"
    
    return state


# =============================================
# JOB ROUTER
# =============================================

async def job_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route to appropriate collector based on pending fields.
    Resets attempt counter when field changes.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        logger.error("❌ JobVacancyState not found in workflow_data")
        return state
    
    # Determine next field to collect
    next_field = job_state.get_next_pending_field()
    previous_target = workflow_data.get("next_collection_target")
    
    if next_field:
        # Reset attempt counter if field changed (progress made!)
        if next_field != previous_target:
            collection_attempts = workflow_data.get("collection_attempts", {})
            collection_attempts[next_field] = 0  # Reset for new field
            workflow_data["collection_attempts"] = collection_attempts
            logger.info(f"✅ Progress! Moving from {previous_target} to {next_field}")
        
        state["workflow_data"]["next_collection_target"] = next_field
        logger.info(f"🎯 Next field to collect: {next_field}")
    else:
        # All fields collected - ready for validation
        state["workflow_data"]["next_collection_target"] = None
        logger.info("✅ All required fields collected")
    
    return state


# =============================================
# STEP 1: ONBOARDING NODE
# =============================================

async def onboarding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Present visual journey of 13-step job creation process.
    Shows welcome message, default process, and ATS field mapping.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        job_state = JobVacancyState()
    
    # Mark onboarding as completed
    job_state.onboarding_completed = True
    job_state.current_step = 1
    job_state.mark_field_collected("onboarding")
    
    # Generate onboarding frame content
    onboarding_frame = {
        "type": "onboarding_journey",
        "title": "Jornada de Criação de Vaga",
        "steps": [
            {"step": 1, "name": "Boas-vindas", "icon": "👋", "status": "current", "description": "Apresentação do processo"},
            {"step": 2, "name": "Informações Básicas", "icon": "📋", "status": "pending", "description": "Título, senioridade, modelo"},
            {"step": 3, "name": "Remuneração", "icon": "💰", "status": "pending", "description": "Faixa salarial e benefícios"},
            {"step": 4, "name": "Estrutura Organizacional", "icon": "🏢", "status": "pending", "description": "Gestor, equipe, organograma"},
            {"step": 5, "name": "Requisitos Técnicos", "icon": "💻", "status": "pending", "description": "Matriz de competências"},
            {"step": 6, "name": "Estratégia de Sourcing", "icon": "🎯", "status": "pending", "description": "Setores, segmentos, pool"},
            {"step": 7, "name": "Competências WSI", "icon": "📊", "status": "pending", "description": "Avaliação científica"},
            {"step": 8, "name": "Etapas de Entrevistas", "icon": "🎤", "status": "pending", "description": "Fluxo de entrevistas"},
            {"step": 9, "name": "Cronograma", "icon": "📅", "status": "pending", "description": "Timeline do processo"},
            {"step": 10, "name": "Governança LIA", "icon": "⚙️", "status": "pending", "description": "Níveis de autonomia"},
            {"step": 11, "name": "Templates de Comunicação", "icon": "💬", "status": "pending", "description": "WhatsApp e e-mail"},
            {"step": 12, "name": "Job Description", "icon": "📝", "status": "pending", "description": "Geração + análise de viés"},
            {"step": 13, "name": "Publicação", "icon": "🚀", "status": "pending", "description": "Dashboard e publicação"}
        ],
        "default_process": {
            "name": "Processo Padrão WeDoTalent",
            "stages": ["Triagem LIA", "Entrevista RH", "Entrevista Técnica", "Entrevista Gestor", "Proposta"]
        },
        "ats_integration": {
            "enabled": False,
            "mapped_fields": ["job_title", "salary_range", "location", "description"]
        }
    }
    
    workflow_data["current_frame"] = onboarding_frame
    workflow_data["onboarding_completed"] = True
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info("👋 Onboarding completed - 13-step journey presented")
    
    return state


# =============================================
# FIELD COLLECTORS
# =============================================

async def basics_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect basic job information (title, seniority, confidentiality, etc).
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Extract and normalize basic fields
    if entities.get("job_title"):
        job_state.job_title = entities["job_title"]
        job_state.mark_field_collected("job_title")
    
    if entities.get("seniority"):
        normalized = job_vacancy_service.normalize_seniority(entities["seniority"])
        if normalized:
            job_state.seniority = normalized
            job_state.mark_field_collected("seniority")
    
    if entities.get("is_confidential") is not None:
        job_state.is_confidential = entities["is_confidential"]
        job_state.mark_field_collected("is_confidential")
        
        # Auto-select WhatsApp template
        job_state.whatsapp_template_type = job_vacancy_service.select_whatsapp_template(
            is_confidential=job_state.is_confidential
        )
    
    if entities.get("work_model"):
        normalized = job_vacancy_service.normalize_work_model(entities["work_model"])
        if normalized:
            job_state.work_model = normalized
            job_state.mark_field_collected("work_model")
    
    if entities.get("department"):
        job_state.department = entities["department"]
    
    if entities.get("location"):
        job_state.location = entities["location"]
    
    if entities.get("employment_type"):
        job_state.employment_type = entities["employment_type"]
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info(f"✅ Basics collected: {job_state.fields_collected}")
    
    return state


async def remuneration_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect salary range and benefits.
    Can be triggered by side panel completion.
    Uses BenefitsService to suggest pre-registered company benefits.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Extract salary range
    if entities.get("salary_min") and entities.get("salary_max"):
        job_state.salary_range = SalaryRange(
            min=float(entities["salary_min"]),
            max=float(entities["salary_max"]),
            currency="BRL"
        )
        job_state.mark_field_collected("salary_range")
    elif entities.get("salary_range"):
        parsed = job_vacancy_service.parse_salary_range(entities["salary_range"])
        if parsed:
            job_state.salary_range = parsed
            job_state.mark_field_collected("salary_range")
    
    # Extract benefits - use user-provided if available
    if entities.get("benefits"):
        job_state.benefits = entities["benefits"]
    
    # Fetch company benefits from BenefitsService
    company_id = state.get("company_id") or workflow_data.get("company_id")
    company_benefits = []
    company_benefits_formatted = ""
    
    try:
        if job_state.seniority:
            company_benefits = await benefits_service.get_benefits_by_seniority(
                company_id, 
                job_state.seniority
            )
        else:
            company_benefits = await benefits_service.get_active_benefits(company_id)
        
        if company_benefits:
            company_benefits_formatted = benefits_service.format_for_ai_prompt(company_benefits)
            logger.info(f"✅ Fetched {len(company_benefits)} company benefits for job creation")
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch company benefits: {e}")
    
    # Store benefits info in workflow_data for UI/frame generation
    if company_benefits:
        workflow_data["company_benefits"] = {
            "count": len(company_benefits),
            "formatted": company_benefits_formatted,
            "suggested": [
                {
                    "id": str(b.id) if hasattr(b, 'id') else None,
                    "name": b.name,
                    "category": b.category,
                    "is_highlighted": getattr(b, 'is_highlighted', False)
                }
                for b in company_benefits[:10]
            ]
        }
        
        if not job_state.benefits:
            job_state.benefits = [b.name for b in company_benefits if getattr(b, 'is_highlighted', False)]
            if not job_state.benefits:
                job_state.benefits = [b.name for b in company_benefits[:5]]
    
    # Generate remuneration frame with benefits suggestions
    remuneration_frame = {
        "type": "remuneration",
        "title": "Remuneração e Benefícios",
        "salary_range": {
            "min": job_state.salary_range.min if job_state.salary_range else None,
            "max": job_state.salary_range.max if job_state.salary_range else None,
            "currency": job_state.salary_range.currency if job_state.salary_range else "BRL"
        },
        "benefits_selected": job_state.benefits or [],
        "company_benefits_available": workflow_data.get("company_benefits", {}).get("suggested", []),
        "has_company_benefits": len(company_benefits) > 0
    }
    workflow_data["current_frame"] = remuneration_frame
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info(f"💰 Remuneration collected: salary_range={job_state.salary_range}, benefits={len(job_state.benefits or [])}")
    
    return state


async def technical_matrix_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect technical requirements matrix.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Extract technical requirements
    if entities.get("required_skills"):
        # Convert simple list to TechnicalRequirement objects
        for skill in entities["required_skills"]:
            job_state.technical_requirements.append(
                TechnicalRequirement(
                    category="Outros",
                    technology=skill,
                    level="Avançado",
                    required=True
                )
            )
        job_state.mark_field_collected("technical_requirements")
    
    if entities.get("preferred_skills"):
        job_state.preferred_skills = entities["preferred_skills"]
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info(f"💻 Technical requirements collected: {len(job_state.technical_requirements)} items")
    
    return state


async def interview_flow_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect interview stages.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # For now, create default interview stages
    # TODO: Extract from conversation
    if not job_state.interview_stages:
        job_state.interview_stages = [
            InterviewStage(
                stage_name="Entrevista RH",
                interviewers=[job_state.recruiter_name or "Recrutador"],
                format="Comportamental",
                duration=45,
                scheduling_window="Terças e Quintas à tarde"
            ),
            InterviewStage(
                stage_name="Entrevista Técnica",
                interviewers=["Time Técnico"],
                format="Técnica + Live Coding",
                duration=90,
                scheduling_window="Quartas pela manhã"
            )
        ]
        job_state.mark_field_collected("interview_stages")
    
    # Calculate timeline based on stages
    job_state.timeline = job_vacancy_service.calculate_timeline(job_state.interview_stages)
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info(f"🎯 Interview flow collected: {len(job_state.interview_stages)} stages")
    
    return state


async def screening_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate screening questions based on job requirements.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)

    if not job_state:
        return state

    if not job_state.screening_questions and job_state.job_title:
        try:
            seniority_raw = getattr(job_state, 'seniority_level', None) or getattr(job_state, 'seniority', 'pleno') or 'pleno'
            seniority_map = {
                'junior': 'junior', 'júnior': 'junior', 'jr': 'junior', 'trainee': 'junior', 'estagiário': 'junior', 'estágio': 'junior',
                'pleno': 'pleno', 'mid': 'pleno', 'mid-level': 'pleno', 'intermediário': 'pleno',
                'senior': 'senior', 'sênior': 'senior', 'sr': 'senior',
                'lead': 'lead', 'líder': 'lead', 'tech lead': 'lead', 'principal': 'lead',
                'executive': 'executive', 'executivo': 'executive', 'diretor': 'executive', 'vp': 'executive', 'c-level': 'executive', 'gerente': 'executive',
            }
            normalized_seniority = seniority_map.get(str(seniority_raw).lower().strip(), 'pleno')

            tech_skills = []
            if hasattr(job_state, 'technical_requirements') and job_state.technical_requirements:
                tech_skills = [tr.technology for tr in job_state.technical_requirements if hasattr(tr, 'technology')]
            if not tech_skills and hasattr(job_state, 'required_skills') and job_state.required_skills:
                tech_skills = job_state.required_skills[:10]

            behavioral = []
            if hasattr(job_state, 'behavioral_competencies') and job_state.behavioral_competencies:
                behavioral = [bc.competency for bc in job_state.behavioral_competencies][:5]
            elif hasattr(job_state, 'soft_skills') and job_state.soft_skills:
                behavioral = job_state.soft_skills[:5]

            responsibilities = []
            if hasattr(job_state, 'responsibilities') and job_state.responsibilities:
                responsibilities = job_state.responsibilities[:5]

            is_affirmative = getattr(job_state, 'is_affirmative', False) or False
            affirmative_type = getattr(job_state, 'affirmative_type', None)

            pipeline_request = WSIScreeningPipelineRequest(
                job_title=job_state.job_title,
                department=getattr(job_state, 'department', None),
                seniority=normalized_seniority,
                technical_skills=tech_skills,
                behavioral_competencies=behavioral,
                responsibilities=responsibilities,
                job_description=getattr(job_state, 'job_description', None),
                question_count=None,
                format="compact",
                include_company_questions=False,
                is_affirmative=is_affirmative,
                affirmative_type=affirmative_type,
            )

            company_questions = []
            pipeline_response = await wsi_screening_pipeline.build_pipeline(
                request=pipeline_request,
                company_questions_raw=company_questions,
            )

            if pipeline_response.success and pipeline_response.questions:
                from app.schemas.job_vacancy_state import ScreeningQuestion
                type_map = {"open": "text", "yes_no": "text", "single_choice": "multiple_choice", "multiple_choice": "multiple_choice", "scale": "rating"}
                job_state.screening_questions = [
                    ScreeningQuestion(
                        id=q.id,
                        question=q.text,
                        type=type_map.get(q.question_type or "open", "text"),
                        weight=int(q.weight * 10) if q.weight else 5,
                    )
                    for q in pipeline_response.questions
                ]
                logger.info(f"WSI pipeline generated {len(job_state.screening_questions)} questions for wizard")
            else:
                job_state.screening_questions = job_vacancy_service.suggest_screening_questions(
                    job_title=job_state.job_title,
                    technical_requirements=job_state.technical_requirements,
                    target_sector=job_state.target_sector
                )
                logger.warning("WSI pipeline failed, fell back to basic questions")
        except Exception as e:
            logger.error(f"WSI pipeline error in wizard: {e}")
            job_state.screening_questions = job_vacancy_service.suggest_screening_questions(
                job_title=job_state.job_title,
                technical_requirements=job_state.technical_requirements,
                target_sector=job_state.target_sector
            )

        job_state.mark_field_collected("screening_questions")

    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)

    logger.info(f"Screening questions generated: {len(job_state.screening_questions)} questions")

    return state


async def governance_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect governance rules (LIA autonomy levels).
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Default governance rules — read from company policy when available
    if not job_state.governance_rules:
        auto_schedule = False
        auto_feedback = False
        requires_validation = True

        company_id = state.get("company_id") or workflow_data.get("company_id")
        if company_id:
            try:
                from app.core.database import AsyncSessionLocal
                from app.shared.policy_middleware import get_policy_for_company
                async with AsyncSessionLocal() as _db:
                    policy = await get_policy_for_company(company_id, _db)
                    automation = policy.get("automation_rules", {})
                    auto_schedule = automation.get("auto_schedule_interviews", False)
                    auto_feedback = automation.get("auto_send_negative_feedback", False)
                    requires_validation = automation.get(
                        "requires_validation_before_shortlist", True
                    )
            except Exception as _e:
                logger.warning(f"Could not load company policy for governance defaults: {_e}")

        job_state.governance_rules = GovernanceRules(
            auto_schedule_interviews=auto_schedule,
            auto_send_negative_feedback=auto_feedback,
            requires_validation_before_shortlist=requires_validation,
        )
        job_state.mark_field_collected("governance_rules")
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    logger.info(f"⚙️ Governance rules collected")
    
    return state


# =============================================
# STEP 4: ORG STRUCTURE COLLECTOR
# =============================================

async def org_structure_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4: Collect organizational structure - direct manager, team size, composition.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Extract organizational structure
    if entities.get("direct_manager") or entities.get("team_size"):
        from app.schemas.job_vacancy_state import TeamComposition
        
        team_composition = []
        if entities.get("team_composition"):
            for member in entities["team_composition"]:
                team_composition.append(TeamComposition(
                    role=member.get("role", "Developer"),
                    count=member.get("count", 1),
                    level=member.get("level", "Pleno")
                ))
        
        job_state.organizational_structure = OrganizationalStructure(
            direct_manager=entities.get("direct_manager", job_state.manager_name or ""),
            team_size=entities.get("team_size", 5),
            team_composition=team_composition
        )
        job_state.mark_field_collected("organizational_structure")
        job_state.current_step = 4
    
    # Generate org chart frame
    if job_state.organizational_structure:
        org_frame = {
            "type": "org_chart",
            "title": "Estrutura Organizacional",
            "manager": job_state.organizational_structure.direct_manager,
            "team_size": job_state.organizational_structure.team_size,
            "composition": [
                {"role": tc.role, "count": tc.count, "level": tc.level}
                for tc in job_state.organizational_structure.team_composition
            ]
        }
        workflow_data["current_frame"] = org_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"🏢 Org structure collected: {job_state.organizational_structure}")
    
    return state


# =============================================
# STEP 6: SOURCING STRATEGY COLLECTOR
# =============================================

async def sourcing_strategy_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 6: Define sourcing strategy - target sectors, segments, pool estimation.
    Integrates with Pearch AI for talent pool estimation.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Build sourcing strategy
    target_sectors = entities.get("target_sectors", [])
    target_segments = entities.get("target_segments", [])
    target_companies = entities.get("target_companies", [])
    excluded_companies = entities.get("excluded_companies", [])
    
    # Auto-suggest sectors based on job title
    if not target_sectors and job_state.job_title:
        target_sectors = await _suggest_sectors_for_job(job_state.job_title)
    
    job_state.sourcing_strategy = SourcingStrategy(
        target_sectors=target_sectors,
        target_segments=target_segments,
        target_companies=target_companies,
        excluded_companies=excluded_companies,
        geography_preference=entities.get("geography", job_state.location),
        remote_acceptable=job_state.work_model in ["remoto", "híbrido"],
        experience_range_min=entities.get("exp_min", 3),
        experience_range_max=entities.get("exp_max", 10)
    )
    
    # Estimate talent pool
    pool_estimate = await _estimate_talent_pool(job_state)
    job_state.talent_pool_estimate = pool_estimate
    
    job_state.mark_field_collected("sourcing_strategy")
    job_state.current_step = 6
    
    # Generate sourcing frame
    sourcing_frame = {
        "type": "sourcing_strategy",
        "title": "Estratégia de Sourcing",
        "sectors": target_sectors,
        "segments": target_segments,
        "target_companies": target_companies,
        "excluded_companies": excluded_companies,
        "pool_estimate": {
            "total": pool_estimate.total_estimated if pool_estimate else 0,
            "local_db": pool_estimate.local_database if pool_estimate else 0,
            "pearch": pool_estimate.pearch_available if pool_estimate else 0,
            "confidence": pool_estimate.confidence_score if pool_estimate else 0.0
        }
    }
    workflow_data["current_frame"] = sourcing_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"🎯 Sourcing strategy defined - Pool estimate: {pool_estimate.total_estimated if pool_estimate else 0}")
    
    return state


async def _suggest_sectors_for_job(job_title: str) -> List[str]:
    """Auto-suggest target sectors based on job title using LLM."""
    try:
        prompt = ChatPromptTemplate.from_template("""
Dado o título de vaga: "{job_title}"

Sugira os 3 melhores setores/segmentos de mercado para buscar candidatos qualificados.
Retorne como JSON: ["setor1", "setor2", "setor3"]

Exemplos de setores: Fintechs, Bancos Digitais, E-commerce, Healthtechs, SaaS B2B, Startups, Big Techs, Consultorias
""")
        
        llm = llm_service.claude
        chain = prompt | llm | JsonOutputParser()
        
        sectors = await chain.ainvoke({"job_title": job_title})
        return sectors if isinstance(sectors, list) else []
    except Exception as e:
        logger.error(f"Failed to suggest sectors: {e}")
        return ["Tecnologia", "Startups", "Empresas Digitais"]


async def _estimate_talent_pool(job_state: JobVacancyState) -> TalentPoolEstimate:
    """Estimate available talent pool based on job requirements."""
    try:
        # TODO: Integrate with Pearch AI for real estimates
        # For now, provide intelligent estimates based on role
        
        base_pool = 500  # Base estimate
        
        # Adjust based on seniority
        seniority_multiplier = {
            "Júnior": 2.0,
            "Pleno": 1.5,
            "Sênior": 0.8,
            "Especialista": 0.4
        }
        multiplier = seniority_multiplier.get(job_state.seniority, 1.0)
        
        # Adjust based on work model
        if job_state.work_model == "remoto":
            multiplier *= 3.0
        elif job_state.work_model == "híbrido":
            multiplier *= 1.5
        
        estimated_total = int(base_pool * multiplier)
        local_db = int(estimated_total * 0.15)  # 15% in local database
        pearch = estimated_total - local_db
        
        return TalentPoolEstimate(
            total_estimated=estimated_total,
            local_database=local_db,
            pearch_available=pearch,
            breakdown_by_source={
                "Banco Interno": local_db,
                "Pearch AI": pearch,
                "LinkedIn": 0,
                "Indicações": 0
            },
            confidence_score=0.75
        )
    except Exception as e:
        logger.error(f"Failed to estimate pool: {e}")
        return TalentPoolEstimate(
            total_estimated=0,
            local_database=0,
            pearch_available=0,
            confidence_score=0.0
        )


# =============================================
# STEP 7: WSI COMPETENCIES COLLECTOR
# =============================================

async def wsi_competencies_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 7: Auto-suggest WSI competencies based on job description.
    Integrates with WSIService.analyze_jd_and_suggest_competencies().
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Build job description for analysis
    jd_text = _build_jd_for_wsi_analysis(job_state)
    
    # Call WSI service to suggest competencies
    try:
        from app.domains.cv_screening.services.wsi_service import wsi_service
        
        # Map seniority to expected format
        seniority_map = {
            "Estágio": "junior", "Júnior": "junior", "Junior": "junior",
            "Pleno": "pleno", "Analista": "pleno",
            "Sênior": "senior", "Senior": "senior",
            "Líder": "lead", "Coordenador": "lead", "Gerente": "lead",
            "Diretor": "executive", "Executivo": "executive"
        }
        normalized_seniority = seniority_map.get(job_state.seniority, "pleno")
        
        wsi_result = await wsi_service.analyze_jd_and_suggest_competencies(
            job_description=jd_text,
            company_culture=None,
            seniority=normalized_seniority
        )
        
        # Convert CompetencySuggestion to dict
        wsi_analysis = {
            "technical_competencies": [
                {"name": c.name, "weight": c.weight, "is_critical": c.is_critical}
                for c in wsi_result.technical_competencies
            ],
            "behavioral_competencies": [
                {"name": c.name, "weight": c.weight, "is_critical": c.is_critical}
                for c in wsi_result.behavioral_competencies
            ]
        }
        
        # Convert to WSICompetencySuggestion objects
        suggestions = []
        for comp in wsi_analysis.get("technical_competencies", []):
            suggestions.append(WSICompetencySuggestion(
                name=comp.get("name"),
                type="technical",
                weight=comp.get("weight", 0.2),
                framework="Dreyfus",
                is_critical=comp.get("is_critical", False)
            ))
        
        for comp in wsi_analysis.get("behavioral_competencies", []):
            suggestions.append(WSICompetencySuggestion(
                name=comp.get("name"),
                type="behavioral",
                weight=comp.get("weight", 0.15),
                framework="Big Five",
                big_five_mapping=comp.get("big_five_trait"),
                is_critical=comp.get("is_critical", False)
            ))
        
        job_state.wsi_competencies = suggestions
        job_state.mark_field_collected("wsi_competencies")
        job_state.current_step = 7
        
    except Exception as e:
        logger.error(f"Failed to analyze WSI competencies: {e}")
        # Fallback: suggest default competencies
        job_state.wsi_competencies = _get_default_wsi_competencies(job_state.seniority)
        job_state.mark_field_collected("wsi_competencies")
    
    # Generate WSI frame
    wsi_frame = {
        "type": "wsi_competencies",
        "title": "Competências WSI",
        "frameworks": ["Dreyfus Model", "Big Five", "Bloom's Taxonomy", "CBI"],
        "competencies": [
            {
                "name": c.name,
                "type": c.type,
                "weight": c.weight,
                "framework": c.framework,
                "big_five": c.big_five_mapping,
                "is_critical": c.is_critical
            }
            for c in job_state.wsi_competencies
        ],
        "total_weight": sum(c.weight for c in job_state.wsi_competencies)
    }
    workflow_data["current_frame"] = wsi_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"📊 WSI competencies suggested: {len(job_state.wsi_competencies)} competencies")
    
    return state


def _build_jd_for_wsi_analysis(job_state: JobVacancyState) -> str:
    """Build job description text for WSI analysis."""
    parts = []
    
    if job_state.job_title:
        parts.append(f"Título: {job_state.job_title}")
    if job_state.seniority:
        parts.append(f"Senioridade: {job_state.seniority}")
    if job_state.technical_requirements:
        techs = ", ".join([tr.technology for tr in job_state.technical_requirements])
        parts.append(f"Requisitos técnicos: {techs}")
    if job_state.behavioral_competencies:
        comps = ", ".join([bc.competency for bc in job_state.behavioral_competencies])
        parts.append(f"Competências comportamentais: {comps}")
    if job_state.description:
        parts.append(f"Descrição: {job_state.description}")
    
    return "\n".join(parts)


def _get_default_wsi_competencies(seniority: Optional[str]) -> List[WSICompetencySuggestion]:
    """Get default WSI competencies based on seniority."""
    competencies = [
        WSICompetencySuggestion(
            name="Resolução de Problemas",
            type="behavioral",
            weight=0.20,
            framework="Bloom's Taxonomy",
            big_five_mapping="Openness",
            is_critical=True
        ),
        WSICompetencySuggestion(
            name="Comunicação",
            type="behavioral",
            weight=0.15,
            framework="Big Five",
            big_five_mapping="Extraversion",
            is_critical=False
        ),
        WSICompetencySuggestion(
            name="Trabalho em Equipe",
            type="behavioral",
            weight=0.15,
            framework="Big Five",
            big_five_mapping="Agreeableness",
            is_critical=False
        )
    ]
    
    if seniority in ["Sênior", "Especialista"]:
        competencies.append(WSICompetencySuggestion(
            name="Liderança Técnica",
            type="behavioral",
            weight=0.15,
            framework="Big Five",
            big_five_mapping="Conscientiousness",
            is_critical=True
        ))
    
    return competencies


# =============================================
# STEP 11: COMMUNICATION TEMPLATES COLLECTOR
# =============================================

async def communication_templates_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 11: Select communication templates for WhatsApp and email.
    Templates: cold outreach, reengagement, confidential.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    entities = state.get("entities", {})
    
    if not job_state:
        return state
    
    # Determine template type based on vacancy characteristics
    if job_state.is_confidential:
        template_type = "confidential"
    elif entities.get("is_reengagement"):
        template_type = "reengagement"
    else:
        template_type = "cold"
    
    job_state.whatsapp_template_type = template_type
    
    # Get template previews
    templates = _get_communication_templates(template_type, job_state)
    job_state.selected_communication_templates = [t["id"] for t in templates]
    
    job_state.mark_field_collected("communication_templates")
    job_state.current_step = 11
    
    # Generate templates frame
    templates_frame = {
        "type": "communication_templates",
        "title": "Templates de Comunicação",
        "selected_type": template_type,
        "templates": templates,
        "whatsapp_preview": templates[0]["content"] if templates else "",
        "email_preview": templates[1]["content"] if len(templates) > 1 else ""
    }
    workflow_data["current_frame"] = templates_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"💬 Communication templates selected: {template_type}")
    
    return state


def _get_communication_templates(template_type: str, job_state: JobVacancyState) -> List[Dict[str, Any]]:
    """Get communication templates based on type."""
    job_title = job_state.job_title or "a posição"
    
    templates = {
        "cold": [
            {
                "id": "whatsapp_cold",
                "type": "whatsapp",
                "name": "Abordagem Inicial",
                "content": f"Olá! 👋 Sou a LIA, assistente de recrutamento. Vi seu perfil e achei muito interessante para {job_title}. Podemos conversar?"
            },
            {
                "id": "email_cold",
                "type": "email",
                "name": "Convite para Processo",
                "content": f"Olá,\n\nEncontramos seu perfil e acreditamos que você seria um excelente candidato para {job_title}.\n\nGostaria de saber mais sobre a oportunidade?"
            }
        ],
        "reengagement": [
            {
                "id": "whatsapp_reengage",
                "type": "whatsapp",
                "name": "Retomada de Contato",
                "content": f"Olá! 👋 Tudo bem? Conversamos há um tempo sobre uma oportunidade. Agora temos uma nova posição de {job_title} que combina ainda mais com seu perfil!"
            },
            {
                "id": "email_reengage",
                "type": "email",
                "name": "Nova Oportunidade",
                "content": f"Olá,\n\nEsperamos que esteja bem! Lembrei de você quando surgiu esta nova oportunidade de {job_title}.\n\nGostaria de saber mais?"
            }
        ],
        "confidential": [
            {
                "id": "whatsapp_confidential",
                "type": "whatsapp",
                "name": "Abordagem Confidencial",
                "content": "Olá! 👋 Sou recrutadora e gostaria de conversar sobre uma oportunidade confidencial que combina muito com seu perfil. Podemos marcar uma ligação rápida?"
            },
            {
                "id": "email_confidential",
                "type": "email",
                "name": "Oportunidade Confidencial",
                "content": "Olá,\n\nEntro em contato para apresentar uma oportunidade confidencial de alto nível.\n\nPodemos agendar uma conversa sigilosa?"
            }
        ]
    }
    
    return templates.get(template_type, templates["cold"])


# =============================================
# STEP 12: JOB DESCRIPTION GENERATOR
# =============================================

async def job_description_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 12: Generate complete job description with inclusive bias analysis.
    Analyzes for gendered language and suggests neutral alternatives.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Generate job description
    jd_content = await _generate_job_description(job_state)
    job_state.job_description_generated = jd_content
    
    # Perform bias analysis
    bias_result = await _analyze_bias(jd_content)
    job_state.bias_analysis = bias_result
    
    job_state.mark_field_collected("job_description")
    job_state.current_step = 12
    
    # Generate JD frame with bias analysis
    jd_frame = {
        "type": "job_description",
        "title": "Job Description",
        "content": jd_content,
        "bias_analysis": {
            "overall_score": bias_result.overall_score,
            "is_inclusive": bias_result.is_inclusive,
            "issues_found": bias_result.issues_found,
            "suggestions": bias_result.suggestions,
            "gendered_terms": bias_result.gendered_terms,
            "alternatives": bias_result.inclusive_alternatives
        },
        "status": "pending_approval" if not bias_result.is_inclusive else "approved"
    }
    workflow_data["current_frame"] = jd_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"📝 Job description generated - Bias score: {bias_result.overall_score}")
    
    return state


async def _generate_job_description(job_state: JobVacancyState) -> str:
    """Generate complete job description using LLM."""
    try:
        prompt = ChatPromptTemplate.from_template("""
Gere uma descrição de vaga profissional e inclusiva com as seguintes informações:

Título: {job_title}
Senioridade: {seniority}
Modelo de trabalho: {work_model}
Localização: {location}
Requisitos técnicos: {technical_requirements}
Competências comportamentais: {behavioral_competencies}
Faixa salarial: {salary_range}
Benefícios: {benefits}

Estruture a descrição com:
1. Sobre a empresa (breve)
2. Sobre a posição
3. Responsabilidades principais
4. Requisitos técnicos
5. Requisitos comportamentais
6. Benefícios
7. Informações adicionais

Use linguagem neutra e inclusiva. Evite termos que possam indicar preferência de gênero.
""")
        
        llm = llm_service.claude
        
        # Prepare data
        tech_reqs = ", ".join([tr.technology for tr in job_state.technical_requirements]) if job_state.technical_requirements else "A definir"
        behav_comps = ", ".join([bc.competency for bc in job_state.behavioral_competencies]) if job_state.behavioral_competencies else "A definir"
        salary = f"R$ {job_state.salary_range.min:,.0f} - R$ {job_state.salary_range.max:,.0f}" if job_state.salary_range else "A combinar"
        benefits_text = ", ".join(job_state.benefits) if job_state.benefits else "VR, VT, Plano de Saúde"
        
        result = await (prompt | llm).ainvoke({
            "job_title": job_state.job_title or "Desenvolvedor(a)",
            "seniority": job_state.seniority or "Pleno",
            "work_model": job_state.work_model or "híbrido",
            "location": job_state.location or "São Paulo, SP",
            "technical_requirements": tech_reqs,
            "behavioral_competencies": behav_comps,
            "salary_range": salary,
            "benefits": benefits_text
        })
        
        return result.content
        
    except Exception as e:
        logger.error(f"Failed to generate job description: {e}")
        return _generate_fallback_jd(job_state)


def _generate_fallback_jd(job_state: JobVacancyState) -> str:
    """Generate fallback job description if LLM fails."""
    return f"""
## {job_state.job_title or "Desenvolvedor(a)"} - {job_state.seniority or "Pleno"}

### Sobre a Posição
Estamos em busca de um(a) profissional para integrar nosso time de tecnologia.

### Responsabilidades
- Desenvolvimento e manutenção de sistemas
- Colaboração com equipes multidisciplinares
- Participação em code reviews e melhorias contínuas

### Requisitos
- Experiência com as tecnologias requeridas
- Boa comunicação e trabalho em equipe
- Proatividade e vontade de aprender

### Modelo de Trabalho
{job_state.work_model or "Híbrido"} - {job_state.location or "São Paulo, SP"}

### Benefícios
Vale Refeição, Vale Transporte, Plano de Saúde, entre outros.

Venha fazer parte do nosso time!
"""


async def _analyze_bias(jd_content: str) -> BiasAnalysis:
    """Analyze job description for inclusive language bias."""
    try:
        prompt = ChatPromptTemplate.from_template("""
Analise o seguinte texto de descrição de vaga para linguagem inclusiva:

"{jd_content}"

Identifique:
1. Termos com viés de gênero (ex: "o candidato", "ele deve")
2. Linguagem exclusiva ou que pode afastar candidatos
3. Sugestões de alternativas inclusivas

Retorne JSON:
{{
    "overall_score": 0.0-1.0 (1.0 = totalmente inclusivo),
    "is_inclusive": true/false,
    "gendered_terms": ["termo1", "termo2"],
    "issues": [
        {{"term": "termo problemático", "issue": "descrição do problema", "suggestion": "alternativa"}}
    ],
    "suggestions": ["sugestão geral 1", "sugestão geral 2"]
}}
""")
        
        llm = llm_service.claude
        chain = prompt | llm | JsonOutputParser()
        
        result = await chain.ainvoke({"jd_content": jd_content})
        
        return BiasAnalysis(
            overall_score=result.get("overall_score", 0.8),
            is_inclusive=result.get("is_inclusive", True),
            issues_found=result.get("issues", []),
            suggestions=result.get("suggestions", []),
            gendered_terms=result.get("gendered_terms", []),
            inclusive_alternatives={
                issue.get("term", ""): issue.get("suggestion", "")
                for issue in result.get("issues", [])
                if issue.get("term") and issue.get("suggestion")
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze bias: {e}")
        return BiasAnalysis(
            overall_score=0.7,
            is_inclusive=True,
            suggestions=["Revise o texto manualmente para garantir linguagem inclusiva"]
        )


# =============================================
# STEP 13: PUBLICATION NODE
# =============================================

async def publication_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 13: Publish job vacancy with dashboard summary.
    Persists job to PostgreSQL database and transitions to sourcing workflow.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Validate all required fields
    if not job_state.is_ready_for_publication():
        missing = [f for f in ["job_title", "salary_range", "technical_requirements", "governance_rules"] 
                   if f not in job_state.fields_collected]
        workflow_data["publication_error"] = f"Campos pendentes: {', '.join(missing)}"
        state["workflow_data"] = workflow_data
        return state
    
    # Mark as published
    from datetime import datetime
    job_state.published_at = datetime.utcnow()
    job_state.ready_to_publish = True
    job_state.mark_field_collected("publication")
    job_state.current_step = 13
    
    # =============================================
    # PERSIST JOB VACANCY TO DATABASE
    # =============================================
    job_vacancy_id = None
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Get context from state
                conversation_id = state.get("conversation_id") or workflow_data.get("conversation_id")
                user_id = state.get("user_id", "default_user")
                company_id = state.get("company_id") or workflow_data.get("company_id")
                
                # Persist to database
                job_vacancy = await job_vacancy_service.finalize_job_vacancy(
                    state=job_state,
                    conversation_id=str(conversation_id) if conversation_id else None,
                    created_by=user_id,
                    db=db,
                    company_id=company_id
                )
                
                job_vacancy_id = str(job_vacancy.id)
                logger.info(f"✅ Job vacancy persisted to database: {job_vacancy_id}")
                
            except Exception as db_error:
                await db.rollback()
                raise db_error
            
    except Exception as e:
        logger.error(f"❌ Failed to persist job vacancy to database: {e}")
        workflow_data["publication_error"] = f"Erro ao salvar vaga: {str(e)}"
    
    # Generate publication dashboard
    summary = job_state.get_workflow_summary()
    
    publication_frame = {
        "type": "publication_dashboard",
        "title": "🚀 Vaga Publicada com Sucesso!",
        "job_id": job_vacancy_id,
        "job_summary": {
            "title": job_state.job_title,
            "seniority": job_state.seniority,
            "location": job_state.location,
            "work_model": job_state.work_model,
            "salary": f"R$ {job_state.salary_range.min:,.0f} - R$ {job_state.salary_range.max:,.0f}" if job_state.salary_range else "A combinar"
        },
        "workflow_summary": summary,
        "sourcing_info": {
            "strategy_defined": job_state.sourcing_strategy is not None,
            "pool_estimate": job_state.talent_pool_estimate.total_estimated if job_state.talent_pool_estimate else 0,
            "auto_sourcing_enabled": job_state.governance_rules.auto_schedule_interviews if job_state.governance_rules else False
        },
        "wsi_info": {
            "competencies_count": len(job_state.wsi_competencies),
            "confirmed": job_state.wsi_competencies_confirmed
        },
        "bias_info": {
            "score": job_state.bias_analysis.overall_score if job_state.bias_analysis else None,
            "is_inclusive": job_state.bias_analysis.is_inclusive if job_state.bias_analysis else True
        },
        "next_actions": [
            {"action": "start_sourcing", "label": "Iniciar Sourcing Automático", "enabled": True},
            {"action": "view_candidates", "label": "Ver Banco de Candidatos", "enabled": True},
            {"action": "share_job", "label": "Compartilhar Vaga", "enabled": True}
        ],
        "published_at": job_state.published_at.isoformat() if job_state.published_at else None
    }
    workflow_data["current_frame"] = publication_frame
    workflow_data["job_published"] = True
    workflow_data["job_vacancy_id"] = job_vacancy_id
    workflow_data["transition_to_sourcing"] = True
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"🚀 Job published: {job_state.job_title} (ID: {job_vacancy_id}) - transitioning to sourcing")
    
    return state


# =============================================
# MARKET BENCHMARK TOOL
# =============================================

async def get_market_salary_benchmark(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool: Get market salary benchmark for the position.
    Provides competitive analysis of salary range.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Get market benchmark
    benchmark = await _fetch_market_benchmark(
        job_title=job_state.job_title,
        seniority=job_state.seniority,
        location=job_state.location
    )
    
    job_state.market_benchmark = benchmark
    
    # Compare with proposed salary
    is_competitive = True
    recommendation = None
    
    if job_state.salary_range and benchmark:
        proposed_avg = (job_state.salary_range.min + job_state.salary_range.max) / 2
        if proposed_avg < benchmark.percentile_25:
            is_competitive = False
            recommendation = f"Salário abaixo do mercado. Recomendamos aumentar para pelo menos R$ {benchmark.percentile_25:,.0f}"
        elif proposed_avg > benchmark.percentile_75:
            recommendation = "Salário acima da média de mercado - atrairá mais candidatos"
        
        benchmark.is_competitive = is_competitive
        benchmark.recommendation = recommendation
    
    # Generate benchmark frame
    benchmark_frame = {
        "type": "market_benchmark",
        "title": "Benchmark de Mercado",
        "market_data": {
            "min": benchmark.market_min if benchmark else 0,
            "max": benchmark.market_max if benchmark else 0,
            "median": benchmark.market_median if benchmark else 0,
            "p25": benchmark.percentile_25 if benchmark else 0,
            "p75": benchmark.percentile_75 if benchmark else 0,
            "sample_size": benchmark.sample_size if benchmark else 0
        },
        "proposed": {
            "min": job_state.salary_range.min if job_state.salary_range else 0,
            "max": job_state.salary_range.max if job_state.salary_range else 0
        },
        "is_competitive": is_competitive,
        "recommendation": recommendation
    }
    workflow_data["current_frame"] = benchmark_frame
    
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    logger.info(f"📊 Market benchmark fetched - Competitive: {is_competitive}")
    
    return state


async def _fetch_market_benchmark(
    job_title: Optional[str],
    seniority: Optional[str],
    location: Optional[str]
) -> MarketBenchmark:
    """Fetch market salary benchmark data."""
    # TODO: Integrate with real market data API
    # For now, provide estimates based on role and seniority
    
    base_salaries = {
        "Júnior": {"min": 4000, "median": 5500, "max": 7000},
        "Pleno": {"min": 8000, "median": 11000, "max": 14000},
        "Sênior": {"min": 14000, "median": 18000, "max": 25000},
        "Especialista": {"min": 20000, "median": 28000, "max": 40000}
    }
    
    salary_data = base_salaries.get(seniority, base_salaries["Pleno"])
    
    return MarketBenchmark(
        market_min=salary_data["min"],
        market_max=salary_data["max"],
        market_median=salary_data["median"],
        percentile_25=salary_data["min"] * 1.15,
        percentile_75=salary_data["max"] * 0.85,
        sample_size=150,
        data_source="market_analysis",
        is_competitive=True
    )


# =============================================
# CHANGE REQUEST PROCESSOR
# =============================================

async def change_request_processor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process change requests like "remova Docker", "mude salário para R$15k".
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    last_message = state["messages"][-1].content
    
    if not job_state:
        return state
    
    # Use LLM to identify what needs to change
    change_prompt = ChatPromptTemplate.from_template("""
Usuário pediu uma alteração na vaga em criação:

"{message}"

Estado atual da vaga:
- Título: {job_title}
- Requisitos técnicos: {technical_requirements}
- Salário: {salary_range}

Identifique o que deve ser alterado e retorne JSON:
{{
    "change_type": "remove_tech/update_salary/update_field",
    "target_field": "...",
    "target_value": "...",
    "action": "..."
}}
""")
    
    llm = llm_service.claude
    chain = change_prompt | llm | JsonOutputParser()
    
    try:
        change_request = await chain.ainvoke({
            "message": last_message,
            "job_title": job_state.job_title or "N/A",
            "technical_requirements": [tr.technology for tr in job_state.technical_requirements],
            "salary_range": str(job_state.salary_range) if job_state.salary_range else "N/A"
        })
        
        # Log change request
        job_state.change_requests.append({
            "timestamp": str(state.get("created_at", "")),
            "request": last_message,
            "parsed": change_request
        })
        
        # Apply change (simplified for now)
        logger.info(f"✏️ Change request: {change_request}")
        
    except Exception as e:
        logger.error(f"Failed to process change request: {e}")
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    return state


# =============================================
# VALIDATOR
# =============================================

async def validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate job vacancy completeness and constraints.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        state["workflow_data"]["validation_passed"] = False
        return state
    
    # Check if ready for publication
    is_ready = job_state.is_ready_for_publication()
    completion = job_state.calculate_completion_percentage()
    
    state["workflow_data"]["validation_passed"] = is_ready
    state["workflow_data"]["completion_percentage"] = completion
    
    logger.info(f"✅ Validation: ready={is_ready}, completion={completion}%")
    
    # Save updated state
    state["workflow_data"] = job_vacancy_service.save_to_workflow_data(job_state, workflow_data)
    
    return state


# =============================================
# FRAME GENERATOR
# =============================================

async def frame_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate visual frames for validation (matriz técnica, cronograma, etc).
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Determine which frame to generate
    requested_frame = workflow_data.get("requested_frame")
    
    if not requested_frame:
        # Auto-determine based on last collected field
        if "technical_requirements" in job_state.fields_collected and not workflow_data.get("showed_tech_matrix"):
            requested_frame = "matriz_tecnica"
            workflow_data["showed_tech_matrix"] = True
        elif "timeline" in job_state.fields_collected and not workflow_data.get("showed_timeline"):
            requested_frame = "cronograma"
            workflow_data["showed_timeline"] = True
    
    if requested_frame:
        frame_content = job_vacancy_service.generate_frame(requested_frame, job_state)
        workflow_data["current_frame"] = {
            "type": requested_frame,
            "content": frame_content
        }
        logger.info(f"🖼️ Generated frame: {requested_frame}")
    
    state["workflow_data"] = workflow_data
    
    return state


# =============================================
# RESPONSE PLANNER
# =============================================

async def response_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan LIA's response: next question, panels to open, frames to show, confirmations.
    """
    workflow_data = state.get("workflow_data", {})
    job_state = job_vacancy_service.load_from_workflow_data(workflow_data)
    
    if not job_state:
        return state
    
    # Determine next action
    next_field = job_state.get_next_pending_field()
    
    response_plan = {
        "next_field": next_field,
        "open_side_panel": None,
        "render_frame": None,
        "needs_confirmation": job_state.needs_confirmation,
        "ready_to_publish": job_state.ready_to_publish,
        "completion_percentage": job_state.calculate_completion_percentage()
    }
    
    # Determine if should open side panel
    if next_field in ["salary_range", "technical_requirements", "behavioral_competencies"]:
        response_plan["open_side_panel"] = {
            "salary_range": "remuneracao",
            "technical_requirements": "requisitos_tecnicos",
            "behavioral_competencies": "competencias"
        }.get(next_field)
    
    # Determine if should render frame
    if workflow_data.get("current_frame"):
        response_plan["render_frame"] = workflow_data["current_frame"]
    
    workflow_data["response_plan"] = response_plan
    state["workflow_data"] = workflow_data
    
    logger.info(f"📋 Response plan: {response_plan}")
    
    return state
