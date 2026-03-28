"""
Stage Transition Automation API Endpoints

Provides endpoints for:
1. Predicting sub-status based on candidate context
2. Generating personalized messages
3. Regenerating messages when sub-status changes
4. Getting available actions for transitions

Part of LIA Automation System v1.0
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import os

from app.services.stage_transition_automation import stage_transition_service
from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Stage Transition Automation"])


async def get_db_session():
    """Get database session for DB-backed predictions."""
    try:
        from app.core.database import get_session
        async for session in get_session():
            yield session
    except Exception:
        yield None


class WSIScore(BaseModel):
    overall: Optional[float] = None
    technical: Optional[float] = None
    behavioral: Optional[float] = None
    cultural: Optional[float] = None


class InterviewNote(BaseModel):
    stage: str
    interviewer: Optional[str] = None
    rating: Optional[float] = None
    strengths: List[str] = []
    gaps: List[str] = []
    recommendation: Optional[str] = None
    notes: Optional[str] = None


class LiaParecer(BaseModel):
    summary: Optional[str] = None
    strengths: List[str] = []
    development_areas: List[str] = []
    cultural_fit: Optional[float] = None
    recommendation: Optional[str] = None


class CandidateContext(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    wsi_score: Optional[WSIScore] = None
    interview_notes: List[InterviewNote] = []
    lia_parecer: Optional[LiaParecer] = None


class JobContext(BaseModel):
    id: str
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    requirements: List[str] = []
    has_hired_candidate: bool = False


class PredictSubStatusRequest(BaseModel):
    candidate_context: CandidateContext
    from_stage: str
    to_stage: str
    job_context: Optional[JobContext] = None


class PredictSubStatusResponse(BaseModel):
    predicted_substatus: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]] = []


class GenerateMessageRequest(BaseModel):
    candidate_context: CandidateContext
    job_context: JobContext
    to_stage: str
    substatus: str
    message_type: str = Field(default="feedback_construtivo")
    channel: str = Field(default="email", pattern="^(email|whatsapp)$")


class GenerateMessageResponse(BaseModel):
    subject: Optional[str] = None
    body: str
    metadata: Dict[str, Any] = {}


class RegenerateMessageRequest(BaseModel):
    original_message: str
    old_substatus: str
    new_substatus: str
    candidate_context: CandidateContext
    job_context: JobContext
    channel: str = Field(default="email", pattern="^(email|whatsapp)$")


class RegenerateMessageResponse(BaseModel):
    subject: Optional[str] = None
    body: str
    changes_made: List[str] = []
    metadata: Dict[str, Any] = {}


class TransitionAction(BaseModel):
    id: str
    name: str
    description: str
    recommended: bool = False
    template_category: Optional[str] = None


class GetActionsRequest(BaseModel):
    from_stage: str
    to_stage: str


class GetActionsResponse(BaseModel):
    actions: List[TransitionAction]


@router.post("/predict-substatus", response_model=PredictSubStatusResponse)
async def predict_substatus(request: PredictSubStatusRequest):
    """
    Predict the most appropriate sub-status for a stage transition.
    
    Uses candidate context (scores, notes, parecer) to intelligently
    suggest the sub-status that best reflects the reason for the transition.
    
    For rejections, analyzes:
    - WSI scores (technical, behavioral, cultural)
    - Interview notes and gaps identified
    - LIA parecer and recommendations
    - Current stage in the process
    - Job requirements and seniority
    """
    try:
        candidate_dict = request.candidate_context.model_dump()
        
        if request.job_context:
            candidate_dict['job'] = request.job_context.model_dump()
        
        result = await stage_transition_service.predict_substatus(
            candidate_context=candidate_dict,
            from_stage=request.from_stage,
            to_stage=request.to_stage
        )
        
        return PredictSubStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error predicting substatus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-message", response_model=GenerateMessageResponse)
async def generate_message(request: GenerateMessageRequest):
    """
    Generate a personalized message for a stage transition.
    
    Uses LIA (Claude) to create contextually relevant, personalized
    communication based on:
    - Candidate's journey through the process
    - Specific sub-status/reason for transition
    - WSI scores and interview feedback
    - Channel-specific formatting (email vs WhatsApp)
    
    Follows WeDoTalent Do's and Don'ts for professional communication.
    """
    try:
        result = await stage_transition_service.generate_message(
            candidate_context=request.candidate_context.model_dump(),
            to_stage=request.to_stage,
            substatus=request.substatus,
            job_context=request.job_context.model_dump(),
            message_type=request.message_type,
            channel=request.channel
        )
        
        return GenerateMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-for-substatus", response_model=RegenerateMessageResponse)
async def regenerate_for_substatus(request: RegenerateMessageRequest):
    """
    Regenerate a message when the sub-status changes.
    
    When a recruiter changes the sub-status (e.g., from 
    'insufficient_technical_skills' to 'another_candidate_selected'),
    this endpoint adjusts the message to reflect the new reason
    while preserving:
    - Overall structure and tone
    - Personalization elements (name, job title)
    - Professional formatting
    
    Only the feedback/reason portions are modified.
    """
    try:
        result = await stage_transition_service.regenerate_for_substatus_change(
            original_message=request.original_message,
            old_substatus=request.old_substatus,
            new_substatus=request.new_substatus,
            candidate_context=request.candidate_context.model_dump(),
            job_context=request.job_context.model_dump(),
            channel=request.channel
        )
        
        changes_made = []
        if result.get('metadata', {}).get('adjustment_type') == 'substatus_change':
            changes_made = [
                f"Motivo alterado de '{request.old_substatus}' para '{request.new_substatus}'",
                "Feedback ajustado para refletir novo motivo"
            ]
        
        return RegenerateMessageResponse(
            subject=result.get('subject'),
            body=result.get('body', ''),
            changes_made=changes_made,
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Error regenerating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-actions", response_model=GetActionsResponse)
async def get_available_actions(request: GetActionsRequest):
    """
    Get available actions for a stage transition.
    
    Returns contextually relevant actions based on:
    - Source stage (from_stage)
    - Target stage (to_stage)
    
    Each action includes:
    - ID for execution
    - Human-readable name and description
    - Whether it's recommended for this transition
    - Associated template category
    """
    try:
        actions = stage_transition_service.get_available_actions(
            from_stage=request.from_stage,
            to_stage=request.to_stage
        )
        
        return GetActionsResponse(
            actions=[TransitionAction(**action) for action in actions]
        )
        
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/substatus-options/{stage}")
async def get_substatus_options(stage: str):
    """
    Get available sub-status options for a given stage.
    
    Returns the list of valid sub-statuses with display names
    for use in the transition modal dropdown.
    """
    from app.models.recruitment_stages import SUB_STATUSES, REJECTION_REASONS, OFFER_DECLINE_REASONS
    
    try:
        if stage == 'rejected':
            return {
                "stage": stage,
                "options": [
                    {"code": r['code'], "display_name": r['display_name'], "category": r.get('category')}
                    for r in REJECTION_REASONS
                ]
            }
        
        if stage == 'offer_declined':
            return {
                "stage": stage,
                "options": [
                    {"code": r['code'], "display_name": r['display_name']}
                    for r in OFFER_DECLINE_REASONS
                ]
            }
        
        stage_substatus = SUB_STATUSES.get(stage, [])
        return {
            "stage": stage,
            "options": [
                {"code": s['name'], "display_name": s['display_name'], "is_default": s.get('is_default', False)}
                for s in stage_substatus
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting substatus options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BulkPredictSubStatusRequest(BaseModel):
    candidates: List[CandidateContext]
    from_stage: str
    to_stage: str
    job_context: Optional[JobContext] = None


class CandidatePrediction(BaseModel):
    candidate_id: str
    predicted_substatus: str
    confidence: float
    reasoning: str


class BulkPredictSubStatusResponse(BaseModel):
    predictions: List[CandidatePrediction]
    ai_powered: bool = False


class BulkGenerateMessagesRequest(BaseModel):
    candidates: List[CandidateContext]
    job_context: JobContext
    to_stage: str
    substatus_map: Dict[str, str]
    message_type: str = "feedback_construtivo"
    channel: str = Field(default="email", pattern="^(email|whatsapp)$")


class CandidateMessage(BaseModel):
    candidate_id: str
    subject: Optional[str] = None
    body: str
    ai_personalized: bool = False


class BulkGenerateMessagesResponse(BaseModel):
    messages: List[CandidateMessage]


@router.post("/bulk-predict-substatus", response_model=BulkPredictSubStatusResponse)
async def bulk_predict_substatus(request: BulkPredictSubStatusRequest):
    """
    Predict sub-status for multiple candidates in a single request.

    Loops through each candidate and returns per-candidate predictions.
    Uses LLM-powered prediction when the feature flag is enabled,
    otherwise falls back to the deterministic SubStatusPredictor.
    """
    use_llm = os.getenv('ENABLE_LLM_SUBSTATUS_PREDICTION', 'true').lower() == 'true'
    predictions: List[CandidatePrediction] = []

    for candidate in request.candidates:
        try:
            candidate_dict = candidate.model_dump()
            if request.job_context:
                candidate_dict['job'] = request.job_context.model_dump()

            if use_llm:
                result = await stage_transition_service.predict_substatus(
                    candidate_context=candidate_dict,
                    from_stage=request.from_stage,
                    to_stage=request.to_stage
                )
            else:
                result = SubStatusPredictor.predict(
                    candidate_context=candidate_dict,
                    from_stage=request.from_stage,
                    to_stage=request.to_stage
                )

            predictions.append(CandidatePrediction(
                candidate_id=candidate.id,
                predicted_substatus=result.get('predicted_substatus', 'profile_not_aligned'),
                confidence=result.get('confidence', 0.0),
                reasoning=result.get('reasoning', '')
            ))
        except Exception as e:
            logger.error(f"Error predicting substatus for candidate {candidate.id}: {e}")
            predictions.append(CandidatePrediction(
                candidate_id=candidate.id,
                predicted_substatus='profile_not_aligned',
                confidence=0.0,
                reasoning=f'Fallback: erro na predição ({str(e)})'
            ))

    return BulkPredictSubStatusResponse(
        predictions=predictions,
        ai_powered=use_llm
    )


@router.post("/bulk-generate-messages", response_model=BulkGenerateMessagesResponse)
async def bulk_generate_messages(request: BulkGenerateMessagesRequest):
    """
    Generate personalized messages for multiple candidates.

    Uses each candidate's specific substatus from the substatus_map
    to produce individualized communication.
    """
    messages: List[CandidateMessage] = []

    for candidate in request.candidates:
        substatus = request.substatus_map.get(candidate.id, 'profile_not_aligned')
        try:
            result = await stage_transition_service.generate_message(
                candidate_context=candidate.model_dump(),
                to_stage=request.to_stage,
                substatus=substatus,
                job_context=request.job_context.model_dump(),
                message_type=request.message_type,
                channel=request.channel
            )

            ai_personalized = result.get('metadata', {}).get('generated_by', '') == 'lia_claude'

            messages.append(CandidateMessage(
                candidate_id=candidate.id,
                subject=result.get('subject'),
                body=result.get('body', ''),
                ai_personalized=ai_personalized
            ))
        except Exception as e:
            logger.error(f"Error generating message for candidate {candidate.id}: {e}")
            candidate_name = candidate.name.split()[0] if candidate.name else 'Candidato'
            job_title = request.job_context.title
            messages.append(CandidateMessage(
                candidate_id=candidate.id,
                subject=f'Retorno sobre sua candidatura - {job_title}' if request.channel == 'email' else None,
                body=f'Olá {candidate_name},\n\nAgradecemos sua participação no processo seletivo para {job_title}. Entraremos em contato em breve.\n\nAtenciosamente,\nEquipe WeDoTalent',
                ai_personalized=False
            ))

    return BulkGenerateMessagesResponse(messages=messages)


class DbPredictSubStatusRequest(BaseModel):
    vacancy_candidate_ids: List[str]
    from_stage: str
    to_stage: str


class DbCandidatePrediction(BaseModel):
    vacancy_candidate_id: str
    predicted_substatus: str
    confidence: float
    reasoning: str


class DbPredictSubStatusResponse(BaseModel):
    predictions: List[DbCandidatePrediction]
    ai_powered: bool = False
    data_source: str = "database"


@router.post("/bulk-predict-substatus-from-db", response_model=DbPredictSubStatusResponse)
async def bulk_predict_substatus_from_db(
    request: DbPredictSubStatusRequest,
    db = Depends(get_db_session),
):
    """
    Predict sub-status for multiple candidates using real data from database.
    
    Unlike /bulk-predict-substatus which uses frontend-supplied context,
    this endpoint queries the database directly for candidate data (WSI scores,
    interview notes, stage history).
    """
    use_llm = os.getenv('ENABLE_LLM_SUBSTATUS_PREDICTION', 'true').lower() == 'true'
    
    if not db:
        return DbPredictSubStatusResponse(
            predictions=[
                DbCandidatePrediction(
                    vacancy_candidate_id=vc_id,
                    predicted_substatus='profile_not_aligned',
                    confidence=0.0,
                    reasoning='Database session not available'
                )
                for vc_id in request.vacancy_candidate_ids
            ],
            ai_powered=False,
            data_source="fallback"
        )
    
    try:
        from app.domains.automation.services.stage_transition_automation import stage_transition_service as domain_service
        results = await domain_service.predict_substatus_bulk_from_db(
            vacancy_candidate_ids=request.vacancy_candidate_ids,
            from_stage=request.from_stage,
            to_stage=request.to_stage,
            db=db,
        )
        
        predictions = []
        for r in results:
            predictions.append(DbCandidatePrediction(
                vacancy_candidate_id=r.get('vacancy_candidate_id', ''),
                predicted_substatus=r.get('predicted_substatus', 'profile_not_aligned'),
                confidence=r.get('confidence', 0.0),
                reasoning=r.get('reasoning', ''),
            ))
        
        return DbPredictSubStatusResponse(
            predictions=predictions,
            ai_powered=use_llm,
            data_source="database"
        )
    except Exception as e:
        logger.error(f"Error in bulk predict from DB: {e}")
        return DbPredictSubStatusResponse(
            predictions=[
                DbCandidatePrediction(
                    vacancy_candidate_id=vc_id,
                    predicted_substatus='profile_not_aligned',
                    confidence=0.0,
                    reasoning=f'Fallback: {str(e)}'
                )
                for vc_id in request.vacancy_candidate_ids
            ],
            ai_powered=False,
            data_source="fallback"
        )
