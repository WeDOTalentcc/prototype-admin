"""
Sourcing & Engagement Nodes for LangGraph workflow (Steps 14-27).
Handles automated sourcing, calibration, outreach, screening, and feedback.
"""
from typing import Dict, Any, Optional, List
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from datetime import datetime, timedelta
import logging
import uuid

from app.domains.ai.services.llm import llm_service
from app.schemas.sourcing_engagement_state import (
    SourcingEngagementState,
    PipelineCandidate,
    CandidateMatchScore,
    CandidateStatus,
    CalibrationSession,
    VolumeAssessment,
    GlobalSearchRequest,
    OutreachCampaign,
    ScreeningSession,
    CandidateFeedback,
    RecruiterNotification
)

logger = logging.getLogger(__name__)


def _load_sourcing_state(workflow_data: Dict[str, Any]) -> Optional[SourcingEngagementState]:
    """Load SourcingEngagementState from workflow_data."""
    state_data = workflow_data.get("sourcing_state")
    if state_data:
        return SourcingEngagementState.model_validate(state_data)
    return None


def _save_sourcing_state(state: SourcingEngagementState, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save SourcingEngagementState to workflow_data."""
    workflow_data["sourcing_state"] = state.model_dump()
    return workflow_data


async def sourcing_state_initializer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize SourcingEngagementState when transitioning from job creation.
    Called after step 13 (Publication).
    """
    workflow_data = state.get("workflow_data", {})
    
    job_state_data = workflow_data.get("job_vacancy_state", {})
    job_id = job_state_data.get("job_id") or str(uuid.uuid4())
    job_title = job_state_data.get("job_title", "Vaga não especificada")
    company_name = job_state_data.get("company_name")
    is_confidential = job_state_data.get("is_confidential", False)
    
    governance = job_state_data.get("governance_rules", {})
    auto_schedule = governance.get("auto_schedule_interviews", False)
    auto_feedback = governance.get("auto_send_negative_feedback", False)
    requires_approval = governance.get("requires_validation_before_shortlist", True)
    
    sourcing_state = SourcingEngagementState(
        job_id=job_id,
        job_title=job_title,
        company_name=company_name,
        is_confidential=is_confidential,
        current_phase="sourcing",
        current_step=14,
        governance_auto_schedule=auto_schedule,
        governance_auto_feedback=auto_feedback,
        governance_requires_approval=requires_approval
    )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    state["current_workflow"] = "sourcing_engagement"
    
    logger.info(f"📦 Initialized SourcingEngagementState for job: {job_title}")
    
    return state


async def local_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 14: Local Search Node
    - Searches local database for candidates
    - Analyzes CVs and calculates match scores
    - Auto-adds high-match candidates to pipeline
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    
    if not sourcing_state:
        logger.error("❌ SourcingEngagementState not found")
        return state
    
    sourcing_state.current_step = 14
    sourcing_state.current_phase = "sourcing"
    
    job_state_data = workflow_data.get("job_vacancy_state", {})
    search_criteria = {
        "job_title": sourcing_state.job_title,
        "technical_requirements": job_state_data.get("technical_requirements", []),
        "seniority": job_state_data.get("seniority"),
        "location": job_state_data.get("location"),
        "sourcing_strategy": job_state_data.get("sourcing_strategy", {})
    }
    
    local_candidates = await _search_local_database(search_criteria)
    
    high_match_count = 0
    medium_match_count = 0
    low_match_count = 0
    
    for candidate_data in local_candidates:
        match_score = CandidateMatchScore(
            overall_score=candidate_data.get("match_score", 50),
            technical_score=candidate_data.get("technical_score", 50),
            behavioral_score=candidate_data.get("behavioral_score", 50),
            experience_score=candidate_data.get("experience_score", 50)
        )
        
        candidate = sourcing_state.add_candidate(
            candidate_id=candidate_data["id"],
            name=candidate_data["name"],
            source="local",
            match_score=match_score,
            email=candidate_data.get("email"),
            phone=candidate_data.get("phone"),
            whatsapp=candidate_data.get("whatsapp"),
            current_role=candidate_data.get("current_role"),
            current_company=candidate_data.get("current_company"),
            linkedin_url=candidate_data.get("linkedin_url")
        )
        
        if match_score.overall_score >= sourcing_state.score_threshold_high:
            high_match_count += 1
        elif match_score.overall_score >= sourcing_state.score_threshold_medium:
            medium_match_count += 1
        else:
            low_match_count += 1
    
    sourcing_state.volume_assessment = VolumeAssessment(
        total_local=len(local_candidates),
        total_in_pipeline=len(sourcing_state.candidates),
        high_match_count=high_match_count,
        medium_match_count=medium_match_count,
        low_match_count=low_match_count,
        is_satisfactory=high_match_count >= 5,
        recommendation=_generate_volume_recommendation(high_match_count, medium_match_count),
        suggested_action="proceed" if high_match_count >= 5 else "expand_local"
    )
    
    notification = sourcing_state.send_notification_to_recruiter(
        notification_type="approval_needed",
        title=f"🔍 Busca Local Concluída - {sourcing_state.job_title}",
        message=f"Encontrei {len(local_candidates)} candidatos no banco local.\n"
                f"• {high_match_count} com alta compatibilidade (≥80%)\n"
                f"• {medium_match_count} com média compatibilidade (60-79%)\n"
                f"• {low_match_count} com baixa compatibilidade (<60%)\n\n"
                f"Recomendação: {sourcing_state.volume_assessment.recommendation}",
        action_required=True,
        action_type="review",
        data={
            "step": 14,
            "candidates_found": len(local_candidates),
            "high_match": high_match_count,
            "medium_match": medium_match_count,
            "low_match": low_match_count
        }
    )
    
    render_frame = {
        "type": "sourcing_results",
        "title": "Resultados da Busca Local",
        "step": 14,
        "data": {
            "total_found": len(local_candidates),
            "high_match_count": high_match_count,
            "medium_match_count": medium_match_count,
            "low_match_count": low_match_count,
            "recommendation": sourcing_state.volume_assessment.recommendation,
            "next_action": "Vou apresentar os melhores perfis para calibração"
        }
    }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"🔍 Local search completed: {len(local_candidates)} candidates found")
    
    return state


async def calibration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 15: Calibration Node
    - Presents top 5-10 candidates to recruiter
    - Learns from approvals/rejections
    - Calibrates understanding of ideal profile
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    
    if not sourcing_state:
        logger.error("❌ SourcingEngagementState not found")
        return state
    
    sourcing_state.current_step = 15
    
    calibration_candidates = sorted(
        [c for c in sourcing_state.candidates if c.status == CandidateStatus.IDENTIFIED],
        key=lambda x: x.match_score.overall_score if x.match_score else 0,
        reverse=True
    )[:10]
    
    for candidate in calibration_candidates:
        sourcing_state.update_candidate_status(candidate.candidate_id, CandidateStatus.CALIBRATION)
    
    session = CalibrationSession(
        session_id=str(uuid.uuid4()),
        candidates_presented=[c.candidate_id for c in calibration_candidates]
    )
    sourcing_state.calibration_sessions.append(session)
    
    notification = sourcing_state.send_notification_to_recruiter(
        notification_type="approval_needed",
        title=f"👥 Calibração de Perfil - {sourcing_state.job_title}",
        message=f"Selecionei {len(calibration_candidates)} candidatos para você avaliar.\n\n"
                "Para cada perfil, me diga se está alinhado com o que busca.\n"
                "Isso me ajuda a calibrar a busca e encontrar candidatos ainda melhores!",
        action_required=True,
        action_type="approve",
        candidate_ids=[c.candidate_id for c in calibration_candidates],
        data={
            "step": 15,
            "session_id": session.session_id,
            "candidates": [
                {
                    "id": c.candidate_id,
                    "name": c.name,
                    "current_role": c.current_role,
                    "current_company": c.current_company,
                    "match_score": c.match_score.overall_score if c.match_score else 0,
                    "score_breakdown": {
                        "technical": c.match_score.technical_score if c.match_score else 0,
                        "behavioral": c.match_score.behavioral_score if c.match_score else 0,
                        "experience": c.match_score.experience_score if c.match_score else 0
                    }
                }
                for c in calibration_candidates
            ]
        }
    )
    
    render_frame = {
        "type": "calibration_panel",
        "title": "Calibração de Perfil",
        "step": 15,
        "data": {
            "session_id": session.session_id,
            "candidates": [
                {
                    "id": c.candidate_id,
                    "name": c.name,
                    "current_role": c.current_role,
                    "current_company": c.current_company,
                    "match_score": c.match_score.overall_score if c.match_score else 0,
                    "linkedin_url": c.linkedin_url
                }
                for c in calibration_candidates
            ],
            "instructions": "Aprove ou rejeite cada perfil para calibrar a busca"
        }
    }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"👥 Calibration session started with {len(calibration_candidates)} candidates")
    
    return state


async def process_calibration_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process recruiter's calibration feedback.
    Updates candidate statuses and learns preferences.
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    session_id = entities.get("session_id")
    approvals = entities.get("approved_candidates", [])
    rejections = entities.get("rejected_candidates", [])
    feedback_notes = entities.get("feedback_notes", {})
    
    session = next(
        (s for s in sourcing_state.calibration_sessions if s.session_id == session_id),
        None
    )
    
    if session:
        session.approvals = approvals
        session.rejections = rejections
        session.feedback_notes = feedback_notes
        session.completed = True
        
        learned_preferences = await _learn_from_calibration(
            sourcing_state, approvals, rejections, feedback_notes
        )
        session.learned_preferences = learned_preferences
    
    for candidate_id in approvals:
        sourcing_state.update_candidate_status(candidate_id, CandidateStatus.APPROVED)
    
    for candidate_id in rejections:
        sourcing_state.update_candidate_status(candidate_id, CandidateStatus.REJECTED_CALIBRATION)
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"✅ Calibration feedback processed: {len(approvals)} approved, {len(rejections)} rejected")
    
    return state


async def volume_assessment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 16: Volume Assessment Node
    - Evaluates if candidate volume is satisfactory
    - Emits recommendation to recruiter
    - Suggests expansion if needed
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 16
    
    approved_count = len(sourcing_state.get_candidates_by_status(CandidateStatus.APPROVED))
    high_match = len(sourcing_state.get_high_match_candidates())
    
    is_satisfactory = approved_count >= 5 or high_match >= 3
    
    if sourcing_state.volume_assessment:
        sourcing_state.volume_assessment.is_satisfactory = is_satisfactory
        sourcing_state.volume_assessment.total_in_pipeline = len(sourcing_state.candidates)
        
        if is_satisfactory:
            sourcing_state.volume_assessment.suggested_action = "proceed"
            sourcing_state.volume_assessment.recommendation = (
                f"Volume satisfatório! {approved_count} candidatos aprovados para contato."
            )
        else:
            sourcing_state.volume_assessment.suggested_action = "expand_global"
            sourcing_state.volume_assessment.recommendation = (
                f"Volume insuficiente. Apenas {approved_count} candidatos aprovados. "
                "Recomendo expandir para busca global (Pearch)."
            )
    
    recommendation_message = ""
    if sourcing_state.volume_assessment and sourcing_state.volume_assessment.recommendation:
        recommendation_message = sourcing_state.volume_assessment.recommendation
    
    notification = sourcing_state.send_notification_to_recruiter(
        notification_type="approval_needed" if not is_satisfactory else "alert",
        title=f"📊 Avaliação de Volume - {sourcing_state.job_title}",
        message=recommendation_message,
        action_required=not is_satisfactory,
        action_type="approve" if not is_satisfactory else None,
        data={
            "step": 16,
            "approved_count": approved_count,
            "high_match_count": high_match,
            "is_satisfactory": is_satisfactory,
            "suggested_action": sourcing_state.volume_assessment.suggested_action if sourcing_state.volume_assessment else "proceed"
        }
    )
    
    render_frame = {
        "type": "volume_assessment",
        "title": "Avaliação de Volume",
        "step": 16,
        "data": {
            "approved_count": approved_count,
            "high_match_count": high_match,
            "is_satisfactory": is_satisfactory,
            "recommendation": sourcing_state.volume_assessment.recommendation if sourcing_state.volume_assessment else "",
            "show_expand_option": not is_satisfactory
        }
    }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📊 Volume assessment: {'satisfactory' if is_satisfactory else 'needs expansion'}")
    
    return state


async def global_expansion_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 17: Global Expansion Node
    - If recruiter approves, searches Pearch
    - Estimates credit cost before search
    - Adds new candidates to pipeline
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 17
    
    if entities.get("approved_global_search"):
        estimated_credits, estimated_candidates = await _estimate_pearch_credits(sourcing_state)
        
        sourcing_state.global_search = GlobalSearchRequest(
            requested=True,
            approved=True,
            estimated_credits=estimated_credits,
            estimated_candidates=estimated_candidates,
            approved_at=datetime.utcnow()
        )
        
        pearch_candidates = await _search_pearch(sourcing_state)
        
        for candidate_data in pearch_candidates:
            match_score = CandidateMatchScore(
                overall_score=candidate_data.get("match_score", 50),
                technical_score=candidate_data.get("technical_score", 50),
                behavioral_score=candidate_data.get("behavioral_score", 50),
                experience_score=candidate_data.get("experience_score", 50)
            )
            
            sourcing_state.add_candidate(
                candidate_id=candidate_data["id"],
                name=candidate_data["name"],
                source="pearch",
                match_score=match_score,
                email=candidate_data.get("email"),
                phone=candidate_data.get("phone"),
                linkedin_url=candidate_data.get("linkedin_url"),
                current_role=candidate_data.get("current_role"),
                current_company=candidate_data.get("current_company")
            )
        
        sourcing_state.global_search.actual_candidates_found = len(pearch_candidates)
        sourcing_state.global_search.completed_at = datetime.utcnow()
        
        render_frame = {
            "type": "global_search_results",
            "title": "Resultados da Busca Global",
            "step": 17,
            "data": {
                "candidates_found": len(pearch_candidates),
                "credits_used": sourcing_state.global_search.actual_credits_used,
                "total_in_pipeline": len(sourcing_state.candidates),
                "message": f"Adicionei {len(pearch_candidates)} candidatos do Pearch ao pipeline!"
            }
        }
    else:
        estimated_credits, estimated_candidates = await _estimate_pearch_credits(sourcing_state)
        
        sourcing_state.global_search = GlobalSearchRequest(
            requested=True,
            approved=False,
            estimated_credits=estimated_credits,
            estimated_candidates=estimated_candidates,
            requested_at=datetime.utcnow()
        )
        
        notification = sourcing_state.send_notification_to_recruiter(
            notification_type="approval_needed",
            title=f"🌍 Expandir Busca Global? - {sourcing_state.job_title}",
            message=f"Posso buscar no Pearch (800M+ perfis) e estimo encontrar "
                    f"aproximadamente {estimated_candidates} candidatos compatíveis.\n\n"
                    f"💳 Custo estimado: {estimated_credits:.2f} créditos\n\n"
                    "Deseja aprovar a busca global?",
            action_required=True,
            action_type="approve",
            data={
                "step": 17,
                "estimated_credits": estimated_credits,
                "estimated_candidates": estimated_candidates
            }
        )
        
        render_frame = {
            "type": "global_search_confirmation",
            "title": "Confirmar Busca Global",
            "step": 17,
            "data": {
                "estimated_candidates": estimated_candidates,
                "estimated_credits": estimated_credits,
                "awaiting_approval": True
            }
        }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"🌍 Global expansion node processed")
    
    return state


async def contact_approval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 18: Contact Approval Node
    - Recruiter reviews shortlist
    - Authorizes contact with selected candidates
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 18
    sourcing_state.current_phase = "engagement"
    
    approved_candidates = sourcing_state.get_candidates_by_status(CandidateStatus.APPROVED)
    
    for candidate in approved_candidates:
        sourcing_state.update_candidate_status(candidate.candidate_id, CandidateStatus.PENDING_CONTACT)
    
    notification = sourcing_state.send_notification_to_recruiter(
        notification_type="approval_needed",
        title=f"📧 Autorizar Contato - {sourcing_state.job_title}",
        message=f"Tenho {len(approved_candidates)} candidatos prontos para contato.\n\n"
                "Revise a lista e me diga com quais devo entrar em contato.\n"
                "Vou enviar um email personalizado apresentando a oportunidade.",
        action_required=True,
        action_type="approve",
        candidate_ids=[c.candidate_id for c in approved_candidates],
        data={
            "step": 18,
            "candidates": [
                {
                    "id": c.candidate_id,
                    "name": c.name,
                    "email": c.email,
                    "current_role": c.current_role,
                    "match_score": c.match_score.overall_score if c.match_score else 0
                }
                for c in approved_candidates
            ]
        }
    )
    
    render_frame = {
        "type": "contact_approval",
        "title": "Autorização para Contato",
        "step": 18,
        "data": {
            "candidates": [
                {
                    "id": c.candidate_id,
                    "name": c.name,
                    "email": c.email,
                    "current_role": c.current_role,
                    "current_company": c.current_company,
                    "match_score": c.match_score.overall_score if c.match_score else 0
                }
                for c in approved_candidates
            ],
            "instructions": "Selecione os candidatos para contato"
        }
    }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📧 Contact approval requested for {len(approved_candidates)} candidates")
    
    return state


async def email_outreach_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 19: Email Outreach Node
    - Sends personalized email presenting job
    - Includes company info (if not confidential)
    - Invites to screening with LIA
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 19
    
    approved_for_contact = entities.get("approved_candidates", [])
    
    if not approved_for_contact:
        approved_for_contact = [
            c.candidate_id for c in sourcing_state.candidates 
            if c.status == CandidateStatus.PENDING_CONTACT
        ]
    
    campaign = OutreachCampaign(
        campaign_id=str(uuid.uuid4()),
        candidates_targeted=approved_for_contact,
        template_used="initial_contact",
        channel="email",
        status="in_progress",
        started_at=datetime.utcnow()
    )
    
    contacted_candidates = []
    for candidate_id in approved_for_contact:
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == candidate_id),
            None
        )
        if candidate and candidate.email:
            email_sent = await _send_outreach_email(candidate, sourcing_state)
            if email_sent:
                sourcing_state.update_candidate_status(candidate_id, CandidateStatus.CONTACTED)
                candidate.outreach_attempts += 1
                candidate.last_outreach_at = datetime.utcnow()
                candidate.outreach_channel = "email"
                campaign.candidates_contacted.append(candidate_id)
                contacted_candidates.append(candidate)
    
    campaign.status = "completed"
    campaign.completed_at = datetime.utcnow()
    sourcing_state.outreach_campaigns.append(campaign)
    
    notification = sourcing_state.send_notification_to_recruiter(
        notification_type="alert",
        title=f"✉️ Emails Enviados - {sourcing_state.job_title}",
        message=f"Enviei emails para {len(contacted_candidates)} candidatos.\n\n"
                "Quando responderem, vou iniciar a triagem WSI automaticamente.\n"
                "Te aviso sobre o progresso!",
        data={
            "step": 19,
            "emails_sent": len(contacted_candidates),
            "campaign_id": campaign.campaign_id
        }
    )
    
    render_frame = {
        "type": "outreach_completed",
        "title": "Emails Enviados",
        "step": 19,
        "data": {
            "emails_sent": len(contacted_candidates),
            "candidates": [
                {
                    "id": c.candidate_id,
                    "name": c.name,
                    "email": c.email
                }
                for c in contacted_candidates
            ],
            "next_step": "Aguardando respostas para iniciar triagem"
        }
    }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"✉️ Outreach completed: {len(contacted_candidates)} emails sent")
    
    return state


async def async_screening_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 20: Async Screening Node
    - Conducts WSI screening via chat/WhatsApp
    - Candidate can respond in text or voice
    - 24-hour window for completion
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 20
    sourcing_state.current_phase = "screening"
    
    candidate_id = entities.get("candidate_id")
    channel = entities.get("channel", "web_chat")
    
    if candidate_id:
        session = sourcing_state.create_screening_session(candidate_id, channel)
        
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == candidate_id),
            None
        )
        if candidate:
            candidate.screening_started_at = datetime.utcnow()
            candidate.screening_deadline = session.deadline
            sourcing_state.update_candidate_status(candidate_id, CandidateStatus.SCREENING_IN_PROGRESS)
        
        render_frame = {
            "type": "screening_started",
            "title": "Triagem Iniciada",
            "step": 20,
            "data": {
                "session_id": session.session_id,
                "candidate_id": candidate_id,
                "candidate_name": candidate.name if candidate else "Candidato",
                "channel": channel,
                "deadline": session.deadline.isoformat(),
                "hours_remaining": sourcing_state.screening_window_hours
            }
        }
    else:
        active_screenings = [
            s for s in sourcing_state.screening_sessions 
            if s.status == "in_progress"
        ]
        
        render_frame = {
            "type": "screening_dashboard",
            "title": "Triagens em Andamento",
            "step": 20,
            "data": {
                "active_screenings": len(active_screenings),
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "candidate_id": s.candidate_id,
                        "channel": s.channel,
                        "deadline": s.deadline.isoformat()
                    }
                    for s in active_screenings
                ]
            }
        }
    
    workflow_data["response_plan"] = {"render_frame": render_frame}
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"🎯 Screening node processed")
    
    return state


async def candidate_feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 21: Candidate Feedback Node
    - Generates structured feedback after screening
    - Highlights strengths and development areas
    - Sends via WhatsApp or email
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 21
    
    session_id = entities.get("session_id")
    session = next(
        (s for s in sourcing_state.screening_sessions if s.session_id == session_id),
        None
    )
    
    if session and session.status == "completed":
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == session.candidate_id),
            None
        )
        
        if candidate:
            feedback_type = "screening_passed" if session.passed else "screening_failed"
            
            feedback_message = await _generate_candidate_feedback(
                candidate, session, sourcing_state.job_title, feedback_type
            )
            
            feedback = CandidateFeedback(
                feedback_id=str(uuid.uuid4()),
                candidate_id=candidate.candidate_id,
                type=feedback_type,
                strengths=session.strengths,
                development_areas=session.development_areas,
                message=feedback_message,
                channel="whatsapp" if candidate.whatsapp else "email"
            )
            
            sent = await _send_feedback_to_candidate(feedback, candidate)
            if sent:
                feedback.sent = True
                feedback.sent_at = datetime.utcnow()
                candidate.feedback_sent = True
                candidate.feedback_content = feedback_message
                candidate.feedback_sent_at = datetime.utcnow()
            
            sourcing_state.candidate_feedbacks.append(feedback)
            
            if session.passed:
                sourcing_state.update_candidate_status(
                    candidate.candidate_id, 
                    CandidateStatus.PENDING_RECRUITER_DECISION
                )
            else:
                sourcing_state.update_candidate_status(
                    candidate.candidate_id,
                    CandidateStatus.REJECTED
                )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📝 Candidate feedback processed")
    
    return state


async def recruiter_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 22: Recruiter Report Node
    - Notifies recruiter via Teams/Chat
    - Sends structured report with WSI score
    - Requests decision (schedule or reject)
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 22
    
    session_id = entities.get("session_id")
    session = next(
        (s for s in sourcing_state.screening_sessions if s.session_id == session_id),
        None
    )
    
    if session:
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == session.candidate_id),
            None
        )
        
        if candidate:
            report_data = {
                "candidate_name": candidate.name,
                "candidate_id": candidate.candidate_id,
                "wsi_score": session.overall_score,
                "passed": session.passed,
                "strengths": session.strengths,
                "development_areas": session.development_areas,
                "evaluation": session.wsi_evaluation
            }
            
            notification = sourcing_state.send_notification_to_recruiter(
                notification_type="screening_completed",
                title=f"🎯 Triagem Concluída - {candidate.name}",
                message=_format_screening_report(candidate, session, sourcing_state.job_title),
                action_required=True,
                action_type="approve",
                candidate_ids=[candidate.candidate_id],
                data={
                    "step": 22,
                    "session_id": session_id,
                    "report": report_data
                }
            )
            
            render_frame = {
                "type": "screening_report",
                "title": f"Parecer de Triagem - {candidate.name}",
                "step": 22,
                "data": report_data
            }
            
            workflow_data["response_plan"] = {"render_frame": render_frame}
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📋 Recruiter report sent")
    
    return state


async def recruiter_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 23: Recruiter Decision Node
    - Processes recruiter's decision
    - Routes to scheduling or rejection
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 23
    sourcing_state.current_phase = "decision"
    
    candidate_id = entities.get("candidate_id")
    decision = entities.get("decision")
    
    if candidate_id and decision:
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == candidate_id),
            None
        )
        
        if candidate:
            if decision == "schedule":
                workflow_data["next_action"] = "auto_scheduling"
                workflow_data["scheduling_candidate_id"] = candidate_id
            elif decision == "reject":
                workflow_data["next_action"] = "rejection_feedback"
                workflow_data["rejection_candidate_id"] = candidate_id
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"🤔 Recruiter decision processed: {decision}")
    
    return state


async def auto_scheduling_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 24: Auto-Scheduling Node
    - Schedules interview automatically or suggests slots
    - Uses CalendarService for availability
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 24
    
    candidate_id = workflow_data.get("scheduling_candidate_id")
    
    if candidate_id:
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == candidate_id),
            None
        )
        
        if candidate:
            if sourcing_state.governance_auto_schedule:
                scheduled_time, interview_link = await _auto_schedule_interview(candidate)
                if scheduled_time:
                    candidate.interview_scheduled_at = scheduled_time
                    candidate.interview_link = interview_link
                    sourcing_state.update_candidate_status(candidate_id, CandidateStatus.INTERVIEW_SCHEDULED)
                    
                    notification = sourcing_state.send_notification_to_recruiter(
                        notification_type="alert",
                        title=f"📅 Entrevista Agendada - {candidate.name}",
                        message=f"Agendei a entrevista para {scheduled_time.strftime('%d/%m às %H:%M')}.\n"
                                f"Link: {interview_link}",
                        candidate_ids=[candidate_id]
                    )
            else:
                available_slots = await _get_available_slots()
                
                notification = sourcing_state.send_notification_to_recruiter(
                    notification_type="approval_needed",
                    title=f"📅 Agendar Entrevista - {candidate.name}",
                    message="Escolha um horário para a entrevista:",
                    action_required=True,
                    action_type="schedule",
                    candidate_ids=[candidate_id],
                    data={
                        "available_slots": available_slots,
                        "candidate_name": candidate.name
                    }
                )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📅 Scheduling processed")
    
    return state


async def rejection_feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 25: Rejection Feedback Node
    - Sends structured negative feedback
    - Can be customized by recruiter or auto-generated
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 25
    
    candidate_id = workflow_data.get("rejection_candidate_id") or entities.get("candidate_id")
    custom_message = entities.get("custom_feedback")
    
    if candidate_id:
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == candidate_id),
            None
        )
        
        if candidate:
            if sourcing_state.governance_auto_feedback or custom_message:
                feedback_message = custom_message or await _generate_rejection_feedback(
                    candidate, sourcing_state.job_title
                )
                
                feedback = CandidateFeedback(
                    feedback_id=str(uuid.uuid4()),
                    candidate_id=candidate_id,
                    type="rejected",
                    message=feedback_message,
                    channel="whatsapp" if candidate.whatsapp else "email",
                    customized_by_recruiter=bool(custom_message)
                )
                
                sent = await _send_feedback_to_candidate(feedback, candidate)
                if sent:
                    feedback.sent = True
                    feedback.sent_at = datetime.utcnow()
                    candidate.feedback_sent = True
                    candidate.feedback_content = feedback_message
                    candidate.feedback_sent_at = datetime.utcnow()
                
                sourcing_state.candidate_feedbacks.append(feedback)
                sourcing_state.update_candidate_status(candidate_id, CandidateStatus.FEEDBACK_SENT)
            else:
                notification = sourcing_state.send_notification_to_recruiter(
                    notification_type="approval_needed",
                    title=f"📝 Feedback para {candidate.name}",
                    message="Deseja sugerir o feedback ou posso usar o padrão?",
                    action_required=True,
                    action_type="confirm",
                    candidate_ids=[candidate_id]
                )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"😔 Rejection feedback processed")
    
    return state


async def placement_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 26: Placement Node
    - Registers hire and closes job
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 26
    sourcing_state.current_phase = "closing"
    
    hired_candidate_id = entities.get("hired_candidate_id")
    
    if hired_candidate_id:
        sourcing_state.hired_candidate_id = hired_candidate_id
        sourcing_state.update_candidate_status(hired_candidate_id, CandidateStatus.HIRED)
        sourcing_state.closed_at = datetime.utcnow()
        sourcing_state.close_reason = "hired"
        
        candidate = next(
            (c for c in sourcing_state.candidates if c.candidate_id == hired_candidate_id),
            None
        )
        
        pending_feedback = sourcing_state.get_pending_feedback_candidates()
        
        notification = sourcing_state.send_notification_to_recruiter(
            notification_type="alert",
            title=f"🎉 Vaga Fechada - {sourcing_state.job_title}",
            message=f"Parabéns! {candidate.name if candidate else 'Candidato'} foi contratado!\n\n"
                    f"Temos {len(pending_feedback)} candidatos que ainda não receberam feedback.\n"
                    "Deseja que eu envie feedback de encerramento para todos?",
            action_required=len(pending_feedback) > 0,
            action_type="confirm" if pending_feedback else None,
            data={
                "hired_candidate": candidate.name if candidate else None,
                "pending_feedback_count": len(pending_feedback)
            }
        )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"🎉 Placement registered")
    
    return state


async def mass_feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 27: Mass Feedback Node
    - Sends closing feedback to all remaining candidates
    """
    workflow_data = state.get("workflow_data", {})
    sourcing_state = _load_sourcing_state(workflow_data)
    entities = state.get("entities", {})
    
    if not sourcing_state:
        return state
    
    sourcing_state.current_step = 27
    
    if entities.get("send_mass_feedback", False):
        pending_candidates = [
            c for c in sourcing_state.candidates
            if not c.feedback_sent and c.status not in [CandidateStatus.HIRED, CandidateStatus.IDENTIFIED]
        ]
        
        feedback_count = 0
        for candidate in pending_candidates:
            feedback_message = await _generate_process_closed_feedback(
                candidate, sourcing_state.job_title
            )
            
            feedback = CandidateFeedback(
                feedback_id=str(uuid.uuid4()),
                candidate_id=candidate.candidate_id,
                type="process_closed",
                message=feedback_message,
                channel="email"
            )
            
            sent = await _send_feedback_to_candidate(feedback, candidate)
            if sent:
                feedback.sent = True
                feedback.sent_at = datetime.utcnow()
                candidate.feedback_sent = True
                candidate.feedback_content = feedback_message
                candidate.feedback_sent_at = datetime.utcnow()
                feedback_count += 1
            
            sourcing_state.candidate_feedbacks.append(feedback)
            sourcing_state.update_candidate_status(candidate.candidate_id, CandidateStatus.FEEDBACK_SENT)
        
        sourcing_state.mass_feedback_sent = True
        sourcing_state.mass_feedback_sent_at = datetime.utcnow()
        
        notification = sourcing_state.send_notification_to_recruiter(
            notification_type="alert",
            title=f"✅ Feedback Enviado - {sourcing_state.job_title}",
            message=f"Enviei feedback de encerramento para {feedback_count} candidatos.\n"
                    "O processo está oficialmente encerrado!",
            data={
                "feedback_sent_count": feedback_count
            }
        )
    
    workflow_data = _save_sourcing_state(sourcing_state, workflow_data)
    state["workflow_data"] = workflow_data
    
    logger.info(f"📨 Mass feedback sent")
    
    return state


def _generate_volume_recommendation(high_match: int, medium_match: int) -> str:
    """Generate recommendation based on candidate volume."""
    if high_match >= 10:
        return "Excelente! Volume robusto de candidatos de alta compatibilidade."
    elif high_match >= 5:
        return "Bom volume. Podemos prosseguir com a calibração."
    elif high_match >= 3:
        return "Volume aceitável, mas recomendo considerar expansão para busca global."
    elif medium_match >= 5:
        return "Poucos candidatos de alta compatibilidade. Temos alguns de média. Sugiro expandir."
    else:
        return "Volume baixo. Recomendo fortemente expandir para busca global (Pearch)."


async def _search_local_database(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search local database for candidates. Placeholder for actual implementation."""
    return []


async def _learn_from_calibration(
    state: SourcingEngagementState,
    approvals: List[str],
    rejections: List[str],
    notes: Dict[str, str]
) -> Dict[str, Any]:
    """Learn preferences from calibration feedback. Placeholder for ML implementation."""
    return {"learned": True, "approvals": len(approvals), "rejections": len(rejections)}


async def _estimate_pearch_credits(state: SourcingEngagementState) -> tuple[float, int]:
    """Estimate Pearch credits for search. Placeholder."""
    return (50.0, 25)


async def _search_pearch(state: SourcingEngagementState) -> List[Dict[str, Any]]:
    """Search Pearch for candidates. Placeholder."""
    return []


async def _send_outreach_email(candidate: PipelineCandidate, state: SourcingEngagementState) -> bool:
    """Send outreach email to candidate. Placeholder."""
    return True


async def _generate_candidate_feedback(
    candidate: PipelineCandidate,
    session: ScreeningSession,
    job_title: str,
    feedback_type: str
) -> str:
    """Generate structured feedback for candidate."""
    if feedback_type == "screening_passed":
        return f"""Olá {candidate.name},

Obrigada por participar da triagem para a posição de {job_title}!

✅ PONTOS FORTES IDENTIFICADOS:
{chr(10).join(f'• {s}' for s in session.strengths[:3]) if session.strengths else '• Excelente comunicação e clareza'}

🎉 Você avançou para a próxima etapa! 
Em breve entraremos em contato para agendar sua entrevista.

Atenciosamente,
LIA - Assistente de Recrutamento"""
    else:
        return f"""Olá {candidate.name},

Obrigada por participar da triagem para a posição de {job_title}!

✅ PONTOS FORTES IDENTIFICADOS:
{chr(10).join(f'• {s}' for s in session.strengths[:3]) if session.strengths else '• Boa disposição para o processo'}

🌱 ÁREAS COM POTENCIAL DE DESENVOLVIMENTO:
{chr(10).join(f'• {a}' for a in session.development_areas[:2]) if session.development_areas else '• Aprofundamento técnico na área'}

Infelizmente, para esta posição específica, identificamos que outros candidatos têm maior aderência aos requisitos.

Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam oportunidades alinhadas.

Atenciosamente,
LIA - Assistente de Recrutamento"""


async def _send_feedback_to_candidate(feedback: CandidateFeedback, candidate: PipelineCandidate) -> bool:
    """Send feedback to candidate via email/WhatsApp. Placeholder."""
    return True


def _format_screening_report(candidate: PipelineCandidate, session: ScreeningSession, job_title: str) -> str:
    """Format screening report for recruiter."""
    status = "✅ APROVADO" if session.passed else "❌ REPROVADO"
    score = session.overall_score or 0
    
    return f"""📋 PARECER DE TRIAGEM WSI

Candidato: {candidate.name}
Vaga: {job_title}
Score WSI: {score:.0f}%
Status: {status}

PONTOS FORTES:
{chr(10).join(f'• {s}' for s in session.strengths[:3]) if session.strengths else '• A definir'}

ÁREAS DE DESENVOLVIMENTO:
{chr(10).join(f'• {a}' for a in session.development_areas[:3]) if session.development_areas else '• A definir'}

Deseja agendar entrevista ou reprovar este candidato?"""


async def _generate_rejection_feedback(candidate: PipelineCandidate, job_title: str) -> str:
    """Generate rejection feedback for candidate."""
    return f"""Olá {candidate.name},

Obrigada por seu interesse na posição de {job_title} e pelo tempo dedicado ao nosso processo seletivo.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com os requisitos específicos desta vaga.

Esta decisão não diminui suas qualificações. Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades compatíveis.

Desejamos sucesso em sua jornada profissional!

Atenciosamente,
LIA - Assistente de Recrutamento"""


async def _generate_process_closed_feedback(candidate: PipelineCandidate, job_title: str) -> str:
    """Generate process closed feedback for remaining candidates."""
    return f"""Olá {candidate.name},

Gostaríamos de informar que a posição de {job_title} foi preenchida.

Agradecemos sinceramente seu interesse e participação em nosso processo seletivo.

Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
LIA - Assistente de Recrutamento"""


async def _auto_schedule_interview(candidate: PipelineCandidate) -> tuple[Optional[datetime], Optional[str]]:
    """Auto-schedule interview. Placeholder."""
    scheduled_time = datetime.utcnow() + timedelta(days=3)
    interview_link = f"https://meet.google.com/xxx-xxxx-xxx"
    return (scheduled_time, interview_link)


async def _get_available_slots() -> List[Dict[str, Any]]:
    """Get available interview slots. Placeholder."""
    now = datetime.utcnow()
    return [
        {"date": (now + timedelta(days=2)).strftime("%Y-%m-%d"), "time": "14:00", "available": True},
        {"date": (now + timedelta(days=2)).strftime("%Y-%m-%d"), "time": "15:00", "available": True},
        {"date": (now + timedelta(days=3)).strftime("%Y-%m-%d"), "time": "10:00", "available": True},
        {"date": (now + timedelta(days=3)).strftime("%Y-%m-%d"), "time": "14:00", "available": True},
    ]
