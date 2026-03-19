"""
Interview Notes API endpoints.
Endpoints for generating interview questions, pareceres, and saving interview notes.

Question generation uses REAL data from:
- JobVacancy: requirements, technical_requirements, behavioral_competencies, screening_questions
- Candidate: resume_text, technical_skills, soft_skills, work_history
- VacancyCandidate: lia_score, match_percentage, stage
- LiaOpinion: previous screening results, strengths, concerns, gaps
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.services.llm import llm_service
from app.services.interview_notes_service import (
    create_interview_note as db_create_interview_note,
    get_interview_note as db_get_interview_note,
    get_notes_for_candidate,
    update_interview_note as db_update_interview_note,
)
from app.auth.dependencies import get_current_active_user, get_user_company_id
from app.auth.models import User
from app.models.job_vacancy import JobVacancy
from app.models.candidate import Candidate, VacancyCandidate
from app.models.lia_opinion import LiaOpinion
from app.shared.compliance.fairness_guard import FairnessGuard
from app.domains.cv_screening.constants.wsi_constants import (
    WSI_DIMENSION_LABELS,
    WSI_DIMENSION_WEIGHTS_DEFAULT,
)

logger = logging.getLogger(__name__)
fairness_guard = FairnessGuard()

router = APIRouter(prefix="/interview-notes", tags=["interview-notes"])

WSI_WEIGHTS = WSI_DIMENSION_WEIGHTS_DEFAULT

WSI_THRESHOLDS = {
    "approved": 4.2,
    "human_review": 3.8
}

# Labels canônicos das dimensões WSI — importados de wsi_constants
WSI_BLOCK_LABELS = WSI_DIMENSION_LABELS


class QuestionBlockType(str, Enum):
    technical = "technical"
    behavioral = "behavioral"
    gap_analysis = "gap_analysis"
    contextual = "contextual"


class GenerateQuestionsRequest(BaseModel):
    """Request for generating interview questions.
    
    If jobId is provided, questions are generated based on job requirements + candidate profile.
    If jobId is None, questions are generated based only on candidate CV (exploratory interview).
    """
    jobId: Optional[UUID] = Field(None, description="ID of the job vacancy (optional - if None, generates CV-based questions)")
    candidateId: UUID = Field(..., description="ID of the candidate")
    includeVagaQuestions: bool = Field(True, description="Include job-specific questions")
    includeGapQuestions: bool = Field(True, description="Include questions about experience gaps")
    includeFitCultural: bool = Field(True, description="Include cultural fit questions")
    wsiLevel: Optional[str] = Field("intermediate", description="WSI complexity level")


class InterviewQuestion(BaseModel):
    """Individual interview question."""
    id: str
    text: str
    category: str
    subcategory: Optional[str] = None
    rationale: Optional[str] = None
    expectedResponse: Optional[str] = None
    wsiLevel: Optional[str] = None
    blockType: Optional[str] = None
    skillId: Optional[str] = None
    skillName: Optional[str] = None


class QuestionBlock(BaseModel):
    """Block of questions for WSI Score Card."""
    type: QuestionBlockType
    label: str
    weight: float
    questions: Union[List[InterviewQuestion], List[dict]]
    subtotalScore: Optional[float] = None


class WSIScore(BaseModel):
    """WSI Score calculation result."""
    technicalScore: float
    behavioralScore: float
    gapAnalysisScore: float
    contextualScore: float
    totalWSI: float
    decision: str
    decisionLabel: str


class GenerateQuestionsResponse(BaseModel):
    """Response with generated interview questions."""
    questions: List[InterviewQuestion]
    blocks: List[QuestionBlock]
    totalCount: int
    generatedAt: datetime


class QuestionWithAnswer(BaseModel):
    """Question with the candidate's response and notes.
    
    Accepts both backend format (questionId, questionText, rating) and
    frontend format (id, text, starRating, likertRating, skipped).
    """
    questionId: Optional[str] = Field(None, alias="id", description="Question ID")
    questionText: Optional[str] = Field(None, alias="text", description="Question text")
    answer: Optional[str] = None
    notes: Optional[str] = Field(None, description="Interviewer notes")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating 1-5")
    category: Optional[str] = None
    starRating: Optional[int] = Field(None, ge=1, le=5, description="Frontend star rating")
    likertRating: Optional[str] = Field(None, description="Likert scale rating")
    skipped: Optional[bool] = Field(False, description="Whether question was skipped")
    source: Optional[str] = Field(None, description="Source of the question")
    blockType: Optional[str] = Field(None, description="WSI block type")
    skillId: Optional[str] = Field(None, description="Skill ID")
    skillName: Optional[str] = Field(None, description="Skill name")
    
    class Config:
        populate_by_name = True
    
    @property
    def effective_id(self) -> str:
        """Get the question ID from either field."""
        return self.questionId or ""
    
    @property
    def effective_text(self) -> str:
        """Get the question text from either field."""
        return self.questionText or ""
    
    @property
    def effective_rating(self) -> Optional[int]:
        """Get the rating from either field."""
        return self.rating or self.starRating


class CalculateWSIRequest(BaseModel):
    """Request for calculating WSI score."""
    blocks: List[QuestionBlock]


class GenerateParecerRequest(BaseModel):
    """Request for generating interview parecer."""
    interviewNoteId: UUID = Field(..., description="ID of the interview note")
    questions: List[QuestionWithAnswer] = Field(..., description="Questions with answers and notes")
    generalNotes: Optional[str] = Field(None, description="General notes from the interview")
    transcription: Optional[str] = Field(None, description="Interview transcription")
    candidateId: Optional[UUID] = None
    jobId: Optional[UUID] = None


class GenerateParecerResponse(BaseModel):
    """Response with generated parecer."""
    parecer: str
    recommendation: str
    strengths: List[str]
    concerns: List[str]
    overallScore: Optional[float] = None
    generatedAt: datetime
    fairness_warnings: List[str] = Field(default_factory=list, description="Alertas de possível viés detectado no parecer")


class InterviewNoteCreate(BaseModel):
    """Full interview note data for saving.
    
    Accepts the rich frontend format with additional metadata fields.
    """
    candidateId: UUID
    jobId: Optional[UUID] = None
    candidateName: Optional[str] = Field(None, description="Candidate name")
    jobTitle: Optional[str] = Field(None, description="Job title")
    interviewerId: Optional[UUID] = None
    recruiterId: Optional[str] = Field(None, description="Recruiter ID")
    recruiterName: Optional[str] = Field(None, description="Recruiter name")
    scheduledInterviewId: Optional[str] = Field(None, description="Scheduled interview ID")
    interviewDate: Optional[datetime] = None
    interviewType: Optional[str] = Field("structured", description="Type of interview")
    questions: Optional[List[QuestionWithAnswer]] = None
    generalNotes: Optional[str] = None
    transcription: Optional[str] = None
    transcriptionSource: Optional[str] = Field(None, description="Source: teams, meet, manual")
    parecer: Optional[str] = Field(None, alias="liaParecer", description="LIA generated parecer")
    liaParecerEditado: Optional[bool] = Field(False, description="Whether parecer was edited")
    recommendation: Optional[str] = None
    nextStage: Optional[str] = Field(None, description="Suggested next stage")
    feedbackSent: Optional[bool] = Field(False, description="Whether feedback was sent")
    feedbackScheduledFor: Optional[datetime] = Field(None, description="Scheduled feedback date")
    status: Optional[str] = Field("draft", description="Status: draft or completed")
    
    class Config:
        populate_by_name = True


class InterviewNoteCreateResponse(BaseModel):
    """Response after saving interview note."""
    id: UUID
    status: str
    createdAt: datetime


class InterviewNoteResponse(BaseModel):
    """Full interview note detail response."""
    id: str
    candidateId: str
    candidateName: Optional[str] = None
    jobId: Optional[str] = None
    jobTitle: Optional[str] = None
    scheduledInterviewId: Optional[str] = None
    interviewType: Optional[str] = None
    interviewDate: Optional[str] = None
    recruiterId: Optional[str] = None
    recruiterName: Optional[str] = None
    questions: list = []
    blocks: list = []
    generalNotes: Optional[str] = None
    transcription: Optional[str] = None
    transcriptionSource: Optional[str] = None
    liaParecer: Optional[str] = None
    liaParecerEditado: Optional[bool] = None
    wsiScore: Optional[dict] = None
    recommendation: Optional[str] = None
    nextStage: Optional[str] = None
    feedbackSent: Optional[bool] = None
    feedbackScheduledFor: Optional[str] = None
    status: str
    createdAt: str
    updatedAt: str


class InterviewNoteSummary(BaseModel):
    """Summary of an interview note for list endpoints."""
    id: str
    candidateId: str
    jobId: Optional[str] = None
    jobTitle: Optional[str] = None
    status: str
    recommendation: Optional[str] = None
    wsiScore: Optional[dict] = None
    interviewDate: Optional[str] = None
    createdAt: str


class InterviewNoteUpdateResponse(BaseModel):
    """Response after partially updating an interview note."""
    id: str
    status: str
    updatedAt: str


# in-memory dict removed — persistence moved to interview_notes table via interview_notes_service.py


def _calculate_block_subtotal(questions: Union[List[dict], List]) -> Optional[float]:
    """Calculate the average score for a block of questions.
    
    Args:
        questions: List of questions that may be InterviewQuestion or QuestionWithAnswer objects/dicts
        
    Returns:
        Average rating of answered questions, or None if no valid ratings
    """
    if not questions:
        return None
    
    valid_scores = []
    for q in questions:
        rating = None
        skipped = False
        
        if isinstance(q, dict):
            rating = q.get('rating') or q.get('starRating')
            skipped = q.get('skipped', False)
        else:
            if hasattr(q, 'effective_rating'):
                rating = q.effective_rating
            elif hasattr(q, 'rating'):
                rating = q.rating
            elif hasattr(q, 'starRating'):
                rating = q.starRating
            skipped = getattr(q, 'skipped', False)
        
        if rating is not None and not skipped:
            valid_scores.append(rating)
    
    if not valid_scores:
        return None
    
    return sum(valid_scores) / len(valid_scores)


def _get_wsi_decision(total_wsi: float) -> tuple[str, str]:
    """Determine WSI decision based on thresholds."""
    if total_wsi >= WSI_THRESHOLDS["approved"]:
        return "approved", "Aprovado"
    elif total_wsi >= WSI_THRESHOLDS["human_review"]:
        return "human_review", "Revisão Humana"
    else:
        return "rejected", "Reprovado"


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_interview_questions(
    request: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> GenerateQuestionsResponse:
    """
    Generate interview questions based on REAL job profile and candidate data.
    
    Uses LIA (LLM) to generate personalized interview questions organized
    in 4 WSI Score Card blocks, using actual data from:
    - JobVacancy: requirements, technical_requirements, behavioral_competencies, screening_questions
    - Candidate: resume_text, technical_skills, soft_skills, work_history
    - VacancyCandidate: lia_score, match_percentage (if linked)
    - LiaOpinion: previous screening results, strengths, concerns, gaps
    
    If no job vacancy is provided, generates questions based only on candidate CV.
    
    Args:
        request: Job and candidate context for question generation
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Questions organized by WSI blocks
    """
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Generating interview questions for job {request.jobId}, "
                   f"candidate {request.candidateId} - company: {company_id}")
        
        # SECURITY: First validate tenant access to candidate
        # Candidate must be linked to at least one vacancy in the user's company
        candidate_access_check = await db.execute(
            select(VacancyCandidate).where(
                and_(
                    VacancyCandidate.candidate_id == request.candidateId,
                    VacancyCandidate.company_id == company_id
                )
            ).limit(1)
        )
        has_tenant_access = candidate_access_check.scalar_one_or_none()
        
        if not has_tenant_access:
            raise HTTPException(
                status_code=403,
                detail="Candidate not accessible - not linked to any vacancy in your company"
            )
        
        # Fetch candidate data (now validated for tenant access)
        candidate_result = await db.execute(
            select(Candidate).where(Candidate.id == request.candidateId)
        )
        candidate = candidate_result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Build candidate context
        candidate_context = f"""
## DADOS DO CANDIDATO
- Nome: {candidate.name}
- Cargo atual: {candidate.current_title or 'Não informado'}
- Empresa atual: {candidate.current_company or 'Não informado'}
- Anos de experiência: {candidate.years_of_experience or 'Não informado'}
- Skills técnicas: {', '.join(candidate.technical_skills or []) or 'Não informado'}
- Soft skills: {', '.join(candidate.soft_skills or []) or 'Não informado'}
- Score LIA: {candidate.lia_score or 'Não calculado'}
"""
        
        # Add resume summary if available
        if candidate.resume_text:
            resume_summary = candidate.resume_text[:2000] + "..." if len(candidate.resume_text) > 2000 else candidate.resume_text
            candidate_context += f"\n### Resumo do CV:\n{resume_summary}\n"
        
        # Add work history if available
        if candidate.work_history:
            work_history_str = "\n".join([
                f"- {exp.get('title', '')} @ {exp.get('company', '')} ({exp.get('duration', '')})"
                for exp in (candidate.work_history or [])[:5]
            ])
            candidate_context += f"\n### Experiência Profissional:\n{work_history_str}\n"
        
        # Initialize job context (may be empty if no vacancy)
        job_context = ""
        vacancy_candidate_context = ""
        screening_context = ""
        
        # Fetch REAL job vacancy data if provided
        if request.jobId:
            job_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == request.jobId,
                        JobVacancy.company_id == company_id
                    )
                )
            )
            job_vacancy = job_result.scalar_one_or_none()
            
            if not job_vacancy:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Job vacancy {request.jobId} not found or not accessible"
                )
            
            # Validate candidate is linked to this vacancy (tenant scoping)
            vc_check = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == request.jobId,
                        VacancyCandidate.candidate_id == request.candidateId,
                        VacancyCandidate.company_id == company_id
                    )
                )
            )
            vacancy_candidate_link = vc_check.scalar_one_or_none()
            
            if not vacancy_candidate_link:
                raise HTTPException(
                    status_code=403,
                    detail=f"Candidate not linked to this job vacancy. Add candidate to the vacancy first."
                )
            
            # Build job context
            job_context = f"""
## DADOS DA VAGA
- Título: {job_vacancy.title}
- Departamento: {job_vacancy.department or 'Não informado'}
- Modelo de trabalho: {job_vacancy.work_model or 'Não informado'}
- Nível de senioridade: {job_vacancy.seniority_level or 'Não informado'}
"""
            
            # Add job description
            if job_vacancy.description:
                desc_summary = job_vacancy.description[:1500] + "..." if len(job_vacancy.description) > 1500 else job_vacancy.description
                job_context += f"\n### Descrição:\n{desc_summary}\n"
            
            # Add requirements
            if job_vacancy.requirements:
                job_context += f"\n### Requisitos básicos:\n{', '.join(job_vacancy.requirements)}\n"
            
            # Add technical requirements (structured)
            if job_vacancy.technical_requirements:
                tech_reqs = "\n".join([
                    f"- {req.get('technology', '')} ({req.get('level', '')}) - {'Obrigatório' if req.get('required') else 'Desejável'}"
                    for req in job_vacancy.technical_requirements[:10]
                ])
                job_context += f"\n### Requisitos técnicos:\n{tech_reqs}\n"
            
            # Add behavioral competencies
            if job_vacancy.behavioral_competencies:
                behavioral_comps = "\n".join([
                    f"- {comp.get('competency', '')} ({comp.get('weight', '')})"
                    for comp in job_vacancy.behavioral_competencies[:8]
                ])
                job_context += f"\n### Competências comportamentais:\n{behavioral_comps}\n"
            
            # Add screening questions from job (WSI methodology)
            if job_vacancy.screening_questions:
                screening_qs = "\n".join([
                    f"- {q.get('question', '')}"
                    for q in job_vacancy.screening_questions[:5]
                ])
                job_context += f"\n### Perguntas de triagem WSI configuradas:\n{screening_qs}\n"
            
            # Use vacancy_candidate_link for context (already fetched above for tenant validation)
            if vacancy_candidate_link:
                vacancy_candidate_context = f"""
## VÍNCULO CANDIDATO-VAGA
- Score LIA para esta vaga: {vacancy_candidate_link.lia_score or 'Não calculado'}
- Match percentage: {vacancy_candidate_link.match_percentage or 'Não calculado'}%
- Etapa atual: {vacancy_candidate_link.stage or 'Inicial'}
- Fonte: {vacancy_candidate_link.source or 'Não informado'}
"""
            
            # Fetch previous LiaOpinion (screening results) - always try for vacancy-linked opinions
            opinion_result = await db.execute(
                select(LiaOpinion).where(
                    and_(
                        LiaOpinion.candidate_id == request.candidateId,
                        LiaOpinion.job_vacancy_id == request.jobId,
                        LiaOpinion.company_id == company_id,
                        LiaOpinion.is_current == True
                    )
                ).order_by(LiaOpinion.created_at.desc()).limit(1)
            )
            previous_opinion = opinion_result.scalar_one_or_none()
            
            if previous_opinion:
                screening_context = f"""
## RESULTADO DA TRIAGEM ANTERIOR
- Score da triagem: {previous_opinion.score or previous_opinion.wsi_score or 'Não disponível'}
- Recomendação: {previous_opinion.recommendation or 'Não disponível'}
- Fonte: {previous_opinion.source or 'Não disponível'}
"""
                if previous_opinion.summary:
                    screening_context += f"\n### Resumo:\n{previous_opinion.summary[:500]}\n"
                
                if previous_opinion.strengths:
                    strengths_list = previous_opinion.strengths if isinstance(previous_opinion.strengths, list) else []
                    screening_context += f"\n### Pontos fortes identificados:\n{', '.join(strengths_list[:5])}\n"
                
                if previous_opinion.concerns:
                    concerns_list = previous_opinion.concerns if isinstance(previous_opinion.concerns, list) else []
                    screening_context += f"\n### Pontos de atenção:\n{', '.join(concerns_list[:5])}\n"
                
                if previous_opinion.gaps:
                    gaps_list = previous_opinion.gaps if isinstance(previous_opinion.gaps, list) else []
                    screening_context += f"\n### Gaps identificados (EXPLORAR NA ENTREVISTA):\n{', '.join(gaps_list[:5])}\n"
                
                if previous_opinion.missing_skills:
                    missing_list = previous_opinion.missing_skills if isinstance(previous_opinion.missing_skills, list) else []
                    screening_context += f"\n### Skills faltantes (VALIDAR NA ENTREVISTA):\n{', '.join(missing_list[:5])}\n"
        
        # Build the complete prompt with REAL data
        prompt = f"""Você é a LIA, uma assistente especializada em recrutamento e seleção.

Gere perguntas de entrevista PERSONALIZADAS com base nos dados REAIS abaixo.

{candidate_context}
{job_context}
{vacancy_candidate_context}
{screening_context}

---

## INSTRUÇÕES PARA GERAÇÃO DE PERGUNTAS

Nível WSI solicitado: {request.wsiLevel}
Incluir perguntas sobre a vaga: {request.includeVagaQuestions}
Incluir perguntas sobre gaps: {request.includeGapQuestions}
Incluir perguntas de fit cultural: {request.includeFitCultural}

{"⚠️ IMPORTANTE: Candidato não está vinculado a nenhuma vaga. Gere perguntas exploratórias baseadas apenas no CV do candidato." if not job_context else ""}

Organize as perguntas nos 4 blocos do Score Card WSI:

1. **TECHNICAL (Competências Técnicas)** - Peso: 50%
   - Perguntas sobre conhecimentos técnicos específicos
   {"- BASEIE-SE NOS REQUISITOS TÉCNICOS DA VAGA" if job_context else "- BASEIE-SE NAS SKILLS DO CV"}
   {"- VALIDE OS GAPS TÉCNICOS IDENTIFICADOS NA TRIAGEM" if screening_context else ""}
   - Gere 4-5 perguntas

2. **BEHAVIORAL (Competências Comportamentais)** - Peso: 20%
   - Perguntas comportamentais usando metodologia STAR
   {"- BASEIE-SE NAS COMPETÊNCIAS COMPORTAMENTAIS DA VAGA" if job_context else "- EXPLORE SITUAÇÕES DA EXPERIÊNCIA DO CANDIDATO"}
   {"- APROFUNDE OS PONTOS DE ATENÇÃO DA TRIAGEM" if screening_context else ""}
   - Gere 2-3 perguntas

3. **GAP_ANALYSIS (Análise de Gaps)** - Peso: 15%
   {"- PERGUNTE SOBRE OS GAPS ESPECÍFICOS IDENTIFICADOS" if screening_context else "- IDENTIFIQUE LACUNAS NO PERFIL"}
   {"- VALIDE SKILLS FALTANTES" if screening_context else ""}
   - Gere 2-3 perguntas

4. **CONTEXTUAL (Contexto e Motivação)** - Peso: 15%
   - Perguntas sobre motivação, disponibilidade, pretensão
   {"- ALINHE COM O CONTEXTO DA VAGA" if job_context else "- EXPLORE OBJETIVOS DE CARREIRA"}
   - Gere 2-3 perguntas

Para cada pergunta, forneça:
- id: identificador único (ex: "tech_1", "behav_1", "gap_1", "ctx_1")
- text: texto da pergunta
- category: categoria específica dentro do bloco
- subcategory: subcategoria opcional
- rationale: justificativa para a pergunta
- expectedResponse: o que constitui uma boa resposta
- blockType: "technical", "behavioral", "gap_analysis" ou "contextual"
- skillId: ID da skill relacionada (ex: "skill_python", "skill_leadership")
- skillName: nome da skill relacionada (ex: "Python", "Liderança")

Responda em formato JSON com a estrutura:
{{
    "blocks": [
        {{
            "type": "technical",
            "label": "Competências Técnicas",
            "weight": 0.50,
            "questions": [
                {{
                    "id": "tech_1",
                    "text": "Pergunta técnica personalizada aqui",
                    "category": "hard_skills",
                    "subcategory": "programming",
                    "rationale": "Por que fazer essa pergunta",
                    "expectedResponse": "O que constitui uma boa resposta",
                    "blockType": "technical",
                    "skillId": "skill_python",
                    "skillName": "Python"
                }}
            ]
        }},
        {{
            "type": "behavioral",
            "label": "Competências Comportamentais",
            "weight": 0.20,
            "questions": [...]
        }},
        {{
            "type": "gap_analysis",
            "label": "Análise de Gaps",
            "weight": 0.15,
            "questions": [...]
        }},
        {{
            "type": "contextual",
            "label": "Contexto e Motivação",
            "weight": 0.15,
            "questions": [...]
        }}
    ]
}}"""

        response = await llm_service.generate(prompt, provider="gemini")
        
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        blocks: List[QuestionBlock] = []
        all_questions: List[InterviewQuestion] = []
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                for block_data in data.get("blocks", []):
                    block_type = block_data.get("type", "technical")
                    block_questions = []
                    for i, q in enumerate(block_data.get("questions", [])):
                        question = InterviewQuestion(
                            id=q.get("id", f"{block_type}_{i}"),
                            text=q.get("text", ""),
                            category=q.get("category", "general"),
                            subcategory=q.get("subcategory"),
                            rationale=q.get("rationale"),
                            expectedResponse=q.get("expectedResponse"),
                            wsiLevel=request.wsiLevel,
                            blockType=q.get("blockType", block_type),
                            skillId=q.get("skillId"),
                            skillName=q.get("skillName")
                        )
                        block_questions.append(question)
                        all_questions.append(question)
                    
                    if block_questions:
                        blocks.append(QuestionBlock(
                            type=QuestionBlockType(block_type),
                            label=block_data.get("label", WSI_BLOCK_LABELS.get(block_type, block_type)),
                            weight=block_data.get("weight", WSI_WEIGHTS.get(block_type, 0.25)),
                            questions=block_questions,
                            subtotalScore=None
                        ))
            except json.JSONDecodeError:
                pass
        
        if not blocks:
            default_blocks = _create_default_blocks(request.wsiLevel)
            blocks = default_blocks
            for block in blocks:
                for q in block.questions:
                    if isinstance(q, InterviewQuestion):
                        all_questions.append(q)
                    elif isinstance(q, dict):
                        all_questions.append(InterviewQuestion(**q))
        
        logger.info(f"Generated {len(all_questions)} interview questions in {len(blocks)} blocks")
        
        return GenerateQuestionsResponse(
            questions=all_questions,
            blocks=blocks,
            totalCount=len(all_questions),
            generatedAt=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate interview questions: {str(e)}"
        )


def _create_default_blocks(wsi_level: Optional[str] = None) -> List[QuestionBlock]:
    """Create default question blocks when LLM fails."""
    return [
        QuestionBlock(
            type=QuestionBlockType.technical,
            label="Competências Técnicas",
            weight=0.50,
            questions=[
                InterviewQuestion(
                    id="tech_1",
                    text="Descreva um desafio técnico que você superou recentemente e como o resolveu.",
                    category="technical",
                    rationale="Avaliar resolução de problemas técnicos",
                    blockType="technical",
                    skillId="skill_problem_solving",
                    skillName="Resolução de Problemas",
                    wsiLevel=wsi_level
                ),
                InterviewQuestion(
                    id="tech_2",
                    text="Quais tecnologias e ferramentas você domina que são relevantes para esta posição?",
                    category="technical",
                    rationale="Identificar competências técnicas",
                    blockType="technical",
                    skillId="skill_tech_stack",
                    skillName="Stack Tecnológico",
                    wsiLevel=wsi_level
                ),
            ],
            subtotalScore=None
        ),
        QuestionBlock(
            type=QuestionBlockType.behavioral,
            label="Competências Comportamentais",
            weight=0.20,
            questions=[
                InterviewQuestion(
                    id="behav_1",
                    text="Conte-me sobre uma situação em que você teve que liderar uma equipe sob pressão.",
                    category="behavioral",
                    rationale="Avaliar liderança e gestão de pressão",
                    blockType="behavioral",
                    skillId="skill_leadership",
                    skillName="Liderança",
                    wsiLevel=wsi_level
                ),
                InterviewQuestion(
                    id="behav_2",
                    text="Como você lida com conflitos no ambiente de trabalho?",
                    category="behavioral",
                    rationale="Avaliar inteligência emocional",
                    blockType="behavioral",
                    skillId="skill_conflict_resolution",
                    skillName="Gestão de Conflitos",
                    wsiLevel=wsi_level
                ),
            ],
            subtotalScore=None
        ),
        QuestionBlock(
            type=QuestionBlockType.gap_analysis,
            label="Análise de Gaps",
            weight=0.15,
            questions=[
                InterviewQuestion(
                    id="gap_1",
                    text="Quais áreas você identifica que precisa desenvolver para esta posição?",
                    category="gap_analysis",
                    rationale="Autoconhecimento sobre gaps",
                    blockType="gap_analysis",
                    skillId="skill_self_awareness",
                    skillName="Autoconhecimento",
                    wsiLevel=wsi_level
                ),
                InterviewQuestion(
                    id="gap_2",
                    text="Como você planeja adquirir as competências que ainda não possui?",
                    category="gap_analysis",
                    rationale="Plano de desenvolvimento",
                    blockType="gap_analysis",
                    skillId="skill_learning_agility",
                    skillName="Agilidade de Aprendizado",
                    wsiLevel=wsi_level
                ),
            ],
            subtotalScore=None
        ),
        QuestionBlock(
            type=QuestionBlockType.contextual,
            label="Contexto e Motivação",
            weight=0.15,
            questions=[
                InterviewQuestion(
                    id="ctx_1",
                    text="O que te motivou a se candidatar a esta posição?",
                    category="contextual",
                    rationale="Entender motivação",
                    blockType="contextual",
                    skillId="skill_motivation",
                    skillName="Motivação",
                    wsiLevel=wsi_level
                ),
                InterviewQuestion(
                    id="ctx_2",
                    text="Quais são suas expectativas de crescimento e desenvolvimento nesta empresa?",
                    category="contextual",
                    rationale="Alinhamento de expectativas",
                    blockType="contextual",
                    skillId="skill_career_goals",
                    skillName="Objetivos de Carreira",
                    wsiLevel=wsi_level
                ),
                InterviewQuestion(
                    id="ctx_3",
                    text="Qual sua disponibilidade para início e pretensão salarial?",
                    category="contextual",
                    rationale="Informações práticas",
                    blockType="contextual",
                    skillId="skill_availability",
                    skillName="Disponibilidade",
                    wsiLevel=wsi_level
                ),
            ],
            subtotalScore=None
        ),
    ]


@router.post("/calculate-wsi", response_model=WSIScore)
async def calculate_wsi_score(
    request: CalculateWSIRequest,
    current_user: User = Depends(get_current_active_user)
) -> WSIScore:
    """
    Calculate WSI Score based on evaluated question blocks.
    
    Weights:
    - Technical: 50%
    - Behavioral: 20%
    - Gap Analysis: 15%
    - Contextual: 15%
    
    Thresholds:
    - WSI >= 4.2: Approved
    - WSI 3.8-4.1: Human Review
    - WSI < 3.8: Rejected
    
    Args:
        request: Blocks with subtotal scores
        current_user: Authenticated user
        
    Returns:
        Complete WSI score calculation
    """
    try:
        technical_score = 0.0
        behavioral_score = 0.0
        gap_analysis_score = 0.0
        contextual_score = 0.0
        
        for block in request.blocks:
            subtotal = _calculate_block_subtotal(block.questions)
            subtotal = subtotal or 0.0
            
            if block.type == QuestionBlockType.technical:
                technical_score = subtotal
            elif block.type == QuestionBlockType.behavioral:
                behavioral_score = subtotal
            elif block.type == QuestionBlockType.gap_analysis:
                gap_analysis_score = subtotal
            elif block.type == QuestionBlockType.contextual:
                contextual_score = subtotal
        
        total_wsi = (
            technical_score * WSI_WEIGHTS["technical"] +
            behavioral_score * WSI_WEIGHTS["behavioral"] +
            gap_analysis_score * WSI_WEIGHTS["gap_analysis"] +
            contextual_score * WSI_WEIGHTS["contextual"]
        )
        
        total_wsi = round(total_wsi, 2)
        
        decision, decision_label = _get_wsi_decision(total_wsi)
        
        logger.info(f"Calculated WSI: {total_wsi} - Decision: {decision}")
        
        return WSIScore(
            technicalScore=round(technical_score, 2),
            behavioralScore=round(behavioral_score, 2),
            gapAnalysisScore=round(gap_analysis_score, 2),
            contextualScore=round(contextual_score, 2),
            totalWSI=total_wsi,
            decision=decision,
            decisionLabel=decision_label
        )
        
    except Exception as e:
        logger.error(f"Error calculating WSI score: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate WSI score: {str(e)}"
        )


@router.post("/generate-parecer", response_model=GenerateParecerResponse)
async def generate_interview_parecer(
    request: GenerateParecerRequest,
    current_user: User = Depends(get_current_active_user)
) -> GenerateParecerResponse:
    """
    Generate interview parecer (evaluation report) based on answers.
    
    Uses LIA to analyze interview responses and generate a comprehensive
    evaluation with recommendation.
    
    Args:
        request: Interview note with questions, answers, and notes
        current_user: Authenticated user
        
    Returns:
        Generated parecer with recommendation
    """
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Generating parecer for interview note {request.interviewNoteId} - company: {company_id}")
        
        questions_summary = "\n".join([
            f"Pergunta: {q.effective_text}\nResposta: {q.answer or 'Não respondida'}\nNotas: {q.notes or 'Sem notas'}\nAvaliação: {q.effective_rating or 'N/A'}/5\nLikert: {q.likertRating or 'N/A'}\nPulada: {'Sim' if q.skipped else 'Não'}\nBloco: {q.blockType or 'N/A'}\nSkill: {q.skillName or 'N/A'}"
            for q in request.questions
        ])
        
        prompt = f"""Você é a LIA, uma assistente especializada em recrutamento e seleção.

Analise as respostas da entrevista abaixo e gere um parecer profissional.

Perguntas e Respostas da Entrevista:
{questions_summary}

Notas Gerais do Entrevistador:
{request.generalNotes or "Nenhuma nota adicional"}

{f"Transcrição da Entrevista: {request.transcription[:2000]}..." if request.transcription else ""}

Com base nas informações acima, gere:

1. Um parecer detalhado (2-3 parágrafos) avaliando o candidato
2. Uma recomendação: "recomendado", "recomendado_com_ressalvas", "nao_recomendado", ou "avaliar_mais"
3. Lista de pontos fortes identificados
4. Lista de pontos de atenção/preocupações
5. Uma nota geral de 0 a 10

Responda em formato JSON:
{{
    "parecer": "Texto do parecer...",
    "recommendation": "recomendado|recomendado_com_ressalvas|nao_recomendado|avaliar_mais",
    "strengths": ["ponto forte 1", "ponto forte 2"],
    "concerns": ["preocupação 1", "preocupação 2"],
    "overallScore": 7.5
}}"""

        response = await llm_service.generate(prompt, provider="gemini")
        
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                parecer_text = data.get("parecer", "Parecer não disponível.")

                # B3: FairnessGuard — verificar output do LLM antes de retornar
                guard_result = fairness_guard.check(parecer_text)
                if guard_result.is_blocked:
                    logger.warning(
                        "FairnessGuard bloqueou parecer gerado: note=%s category=%s terms=%s",
                        request.interviewNoteId, guard_result.category, guard_result.blocked_terms,
                    )
                    parecer_text = "[Parecer sob revisão — conteúdo sinalizado pelo FairnessGuard para análise de possível viés discriminatório.]"

                return GenerateParecerResponse(
                    parecer=parecer_text,
                    recommendation=data.get("recommendation", "avaliar_mais"),
                    strengths=data.get("strengths", []),
                    concerns=data.get("concerns", []),
                    overallScore=data.get("overallScore"),
                    generatedAt=datetime.utcnow(),
                    fairness_warnings=guard_result.soft_warnings,
                )
            except json.JSONDecodeError:
                pass

        parecer_fallback = response if response else "Não foi possível gerar o parecer automaticamente."
        guard_result = fairness_guard.check(parecer_fallback)
        if guard_result.is_blocked:
            logger.warning(
                "FairnessGuard bloqueou parecer (fallback): note=%s category=%s",
                request.interviewNoteId, guard_result.category,
            )
            parecer_fallback = "[Parecer sob revisão — conteúdo sinalizado pelo FairnessGuard para análise de possível viés discriminatório.]"

        return GenerateParecerResponse(
            parecer=parecer_fallback,
            recommendation="avaliar_mais",
            strengths=[],
            concerns=[],
            overallScore=None,
            generatedAt=datetime.utcnow(),
            fairness_warnings=guard_result.soft_warnings,
        )
        
    except Exception as e:
        logger.error(f"Error generating interview parecer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate interview parecer: {str(e)}"
        )


@router.post("", response_model=InterviewNoteCreateResponse)
async def create_interview_note(
    data: InterviewNoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewNoteCreateResponse:
    """Save a new interview note to the database (persistent)."""
    try:
        company_id = get_user_company_id(current_user)
        created_by = str(current_user.id) if hasattr(current_user, "id") else "system"

        note = await db_create_interview_note(
            db=db,
            company_id=company_id,
            created_by=created_by,
            candidate_id=str(data.candidateId),
            candidate_name=data.candidateName,
            job_id=str(data.jobId) if data.jobId else None,
            job_title=data.jobTitle,
            scheduled_interview_id=data.scheduledInterviewId,
            interviewer_id=str(data.interviewerId) if data.interviewerId else data.recruiterId,
            recruiter_name=data.recruiterName,
            interview_date=data.interviewDate or datetime.utcnow(),
            interview_type=data.interviewType or "structured",
            questions=[q.model_dump() for q in (data.questions or [])],
            blocks=[],
            general_notes=data.generalNotes,
            transcription=data.transcription,
            transcription_source=data.transcriptionSource,
            lia_parecer=data.parecer,
            lia_parecer_editado=data.liaParecerEditado or False,
            wsi_score=None,
            recommendation=data.recommendation,
            next_stage=data.nextStage,
            feedback_sent=data.feedbackSent or False,
            feedback_scheduled_for=data.feedbackScheduledFor,
            status=data.status or "draft",
        )

        return InterviewNoteCreateResponse(
            id=note.id,
            status=note.status,
            createdAt=note.created_at,
        )

    except Exception as e:
        logger.error(f"Error creating interview note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create interview note: {str(e)}")


@router.get("/{note_id}", response_model=InterviewNoteResponse)
async def get_interview_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewNoteResponse:
    """Retrieve a single interview note by ID (company-scoped)."""
    company_id = get_user_company_id(current_user)
    note = await db_get_interview_note(db, note_id, company_id)
    if not note:
        raise HTTPException(status_code=404, detail="Interview note not found")
    return {
        "id": str(note.id),
        "candidateId": str(note.candidate_id),
        "candidateName": note.candidate_name,
        "jobId": str(note.job_id) if note.job_id else None,
        "jobTitle": note.job_title,
        "scheduledInterviewId": note.scheduled_interview_id,
        "interviewType": note.interview_type,
        "interviewDate": note.interview_date.isoformat() if note.interview_date else None,
        "recruiterId": note.interviewer_id,
        "recruiterName": note.recruiter_name,
        "questions": note.questions or [],
        "blocks": note.blocks or [],
        "generalNotes": note.general_notes,
        "transcription": note.transcription,
        "transcriptionSource": note.transcription_source,
        "liaParecer": note.lia_parecer,
        "liaParecerEditado": note.lia_parecer_editado,
        "wsiScore": note.wsi_score,
        "recommendation": note.recommendation,
        "nextStage": note.next_stage,
        "feedbackSent": note.feedback_sent,
        "feedbackScheduledFor": note.feedback_scheduled_for.isoformat() if note.feedback_scheduled_for else None,
        "status": note.status,
        "createdAt": note.created_at.isoformat(),
        "updatedAt": note.updated_at.isoformat(),
    }


@router.get("/candidate/{candidate_id}", response_model=List[InterviewNoteSummary])
async def list_notes_for_candidate(
    candidate_id: str,
    job_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[InterviewNoteSummary]:
    """List all interview notes for a candidate (optionally filtered by job)."""
    company_id = get_user_company_id(current_user)
    notes = await get_notes_for_candidate(db, candidate_id, company_id, job_id)
    return [
        {
            "id": str(n.id),
            "candidateId": str(n.candidate_id),
            "jobId": str(n.job_id) if n.job_id else None,
            "jobTitle": n.job_title,
            "status": n.status,
            "recommendation": n.recommendation,
            "wsiScore": n.wsi_score,
            "interviewDate": n.interview_date.isoformat() if n.interview_date else None,
            "createdAt": n.created_at.isoformat(),
        }
        for n in notes
    ]


class InterviewNoteUpdateRequest(BaseModel):
    questions: Optional[list] = None
    blocks: Optional[list] = None
    generalNotes: Optional[str] = None
    transcription: Optional[str] = None
    liaParecer: Optional[str] = None
    liaParecerEditado: Optional[bool] = None
    wsiScore: Optional[dict] = None
    recommendation: Optional[str] = None
    nextStage: Optional[str] = None
    feedbackSent: Optional[bool] = None
    status: Optional[str] = None


@router.patch("/{note_id}", response_model=InterviewNoteUpdateResponse)
async def update_interview_note(
    note_id: str,
    data: InterviewNoteUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewNoteUpdateResponse:
    """Partially update an interview note (e.g. save draft, add WSI score)."""
    company_id = get_user_company_id(current_user)
    fields = {
        "questions": data.questions,
        "blocks": data.blocks,
        "general_notes": data.generalNotes,
        "transcription": data.transcription,
        "lia_parecer": data.liaParecer,
        "lia_parecer_editado": data.liaParecerEditado,
        "wsi_score": data.wsiScore,
        "recommendation": data.recommendation,
        "next_stage": data.nextStage,
        "feedback_sent": data.feedbackSent,
        "status": data.status,
    }
    # remove None values so we don't overwrite existing data
    fields = {k: v for k, v in fields.items() if v is not None}

    note = await db_update_interview_note(db, note_id, company_id, **fields)
    if not note:
        raise HTTPException(status_code=404, detail="Interview note not found")

    return {"id": str(note.id), "status": note.status, "updatedAt": note.updated_at.isoformat()}
