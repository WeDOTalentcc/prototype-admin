"""
Personalized Feedback Service - AI-powered rejection feedback for candidates.

This service generates highly personalized, constructive rejection feedback using Claude AI.
The feedback is tailored to each candidate based on their profile, strengths, development areas,
WSI evaluation results, and the specific job requirements.

Flow:
1. Recruiter requests rejection feedback for a candidate
2. System uses Claude to generate a PERSONALIZED draft based on:
   - Candidate's name, profile, and background
   - Job title and requirements
   - Candidate's strengths identified during screening
   - Development areas identified
   - WSI score and evaluation details
3. Preview is shown to recruiter for approval/editing
4. After approval, message is queued for sending
5. Analytics track personalized feedback effectiveness

Key Principles:
- Feedback should feel written by a human, not a template
- Include specific, actionable development suggestions
- Maintain professional but warm tone
- Respect the candidate's time and effort
"""
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base
from app.domains.ai.services.llm import llm_service
from app.shared.compliance.audit_service import audit_service
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.pii_masking import get_masked_logger
from app.templates.communication_templates import EmailTemplates, WhatsAppTemplates
from app.shared.types import WeDoBaseModel

_fairness_guard = FairnessGuard()

logger = get_masked_logger(__name__)


class FeedbackChannel(StrEnum):
    """Channels for sending feedback."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    BOTH = "both"


class FeedbackTone(StrEnum):
    """Tone for the feedback message."""
    WARM = "warm"
    PROFESSIONAL = "professional"
    ENCOURAGING = "encouraging"


class PersonalizedFeedbackStatus(StrEnum):
    """Status of personalized feedback."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EDITED = "edited"
    SENT = "sent"
    FAILED = "failed"


class CandidateContext(BaseModel):
    """Context about the candidate for personalization."""
    model_config = ConfigDict(extra='forbid')

    candidate_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    years_of_experience: int | None = None
    technical_skills: list[str] = Field(default_factory=list)
    seniority_level: str | None = None


class JobContext(BaseModel):
    """Context about the job position."""
    model_config = ConfigDict(extra='forbid')

    job_id: str
    title: str
    company_name: str | None = None
    is_confidential: bool = False
    required_skills: list[str] = Field(default_factory=list)
    seniority_level: str | None = None
    department: str | None = None


class WSIEvaluationContext(BaseModel):
    """WSI evaluation results for personalization."""
    model_config = ConfigDict(extra='forbid')

    overall_wsi: float = Field(ge=0, le=5)
    technical_wsi: float | None = Field(default=None, ge=0, le=5)
    behavioral_wsi: float | None = Field(default=None, ge=0, le=5)
    classification: Literal[
        "excepcional", "excelente", "alto", "medio", "abaixo_da_media", "regular"
    ] = "medio"
    seniority_label: str | None = None
    
    strengths: list[str] = Field(default_factory=list)
    development_areas: list[str] = Field(default_factory=list)
    
    technical_strengths: list[str] = Field(default_factory=list)
    behavioral_strengths: list[str] = Field(default_factory=list)
    
    skill_gaps: list[str] = Field(default_factory=list)
    competency_scores: dict[str, float] = Field(default_factory=dict)
    
    summary: str | None = None


class PersonalizedFeedbackRequest(WeDoBaseModel):
    """Request for generating personalized feedback."""
    candidate: CandidateContext
    job: JobContext
    evaluation: WSIEvaluationContext

    channel: FeedbackChannel = FeedbackChannel.EMAIL
    tone: FeedbackTone = FeedbackTone.WARM

    include_development_plan: bool = True
    include_resources: bool = True

    recruiter_notes: str | None = None
    company_id: str | None = None
    requested_by: str | None = None
    auto_send: bool = False
    # Gap #11/#12: Caminho de decisão + gates ativados para template determinístico
    decision_type: Literal["REPROVADO", "EM_AVALIACAO", "APROVADO"] = "REPROVADO"
    failed_gates: list[str] = Field(default_factory=list)


class PersonalizedFeedbackResult(BaseModel):
    """Result of personalized feedback generation."""
    feedback_id: str
    
    subject: str
    body_text: str
    body_html: str | None = None
    
    whatsapp_message: str | None = None
    
    key_points: list[str] = Field(default_factory=list)
    development_suggestions: list[str] = Field(default_factory=list)
    recommended_resources: list[str] = Field(default_factory=list)
    
    personalization_level: Literal["high", "medium", "low"] = "high"
    ai_model_used: str = "claude-sonnet"
    
    status: PersonalizedFeedbackStatus = PersonalizedFeedbackStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PersonalizedFeedbackRecord(Base):
    """Database record for tracking personalized feedback."""
    __tablename__ = "personalized_feedback_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    job_id = Column(String, nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    
    wsi_score = Column(Float, nullable=True)
    wsi_classification = Column(String(50), nullable=True)
    
    channel = Column(String(20), nullable=False, default="email")
    tone = Column(String(50), nullable=False, default="warm")
    
    subject = Column(String(500), nullable=True)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    whatsapp_message = Column(Text, nullable=True)
    
    strengths_highlighted = Column(JSON, default=list)
    development_areas_highlighted = Column(JSON, default=list)
    development_suggestions = Column(JSON, default=list)
    recommended_resources = Column(JSON, default=list)
    
    personalization_level = Column(String(20), default="high")
    ai_model_used = Column(String(100), nullable=True)
    ai_prompt_tokens = Column(Integer, nullable=True)
    ai_completion_tokens = Column(Integer, nullable=True)
    
    status = Column(String(50), default="draft", index=True)
    
    requested_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    edited_body = Column(Text, nullable=True)
    edited_subject = Column(String(500), nullable=True)
    editor_notes = Column(Text, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    sent_channel = Column(String(20), nullable=True)
    send_result = Column(JSON, default=dict)
    
    candidate_opened_at = Column(DateTime, nullable=True)
    candidate_clicked_at = Column(DateTime, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "wsi_score": self.wsi_score,
            "wsi_classification": self.wsi_classification,
            "channel": self.channel,
            "tone": self.tone,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "whatsapp_message": self.whatsapp_message,
            "strengths_highlighted": self.strengths_highlighted,
            "development_areas_highlighted": self.development_areas_highlighted,
            "development_suggestions": self.development_suggestions,
            "recommended_resources": self.recommended_resources,
            "personalization_level": self.personalization_level,
            "status": self.status,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PersonalizedFeedbackService:
    """
    AI-powered personalized rejection feedback service.
    
    This service uses Claude to generate highly personalized, constructive feedback
    for candidates who are not advancing in the recruitment process.
    
    Features:
    - AI-powered personalization based on candidate profile, job, and WSI evaluation
    - Multiple tone options (warm, professional, encouraging)
    - Multi-channel support (email, WhatsApp)
    - Approval workflow integration
    - Analytics tracking
    """
    
    PERSONALIZATION_PROMPT_TEMPLATE = """You are an empathetic HR communication specialist helping write rejection feedback for job candidates.

CONTEXT:
- Candidate: {candidate_name}
  - Current Role: {current_title} at {current_company}
  - Experience: {years_of_experience} years
  - Skills: {technical_skills}

- Position Applied: {job_title} at {company_name}
  - Required Skills: {required_skills}
  - Seniority Level: {job_seniority}

- Evaluation Results:
  - Overall WSI Score: {wsi_score}/5.0 ({wsi_classification})
  - Technical Score: {technical_wsi}/5.0
  - Behavioral Score: {behavioral_wsi}/5.0
  
- Strengths Identified:
{strengths_list}

- Development Areas:
{development_areas_list}

- Skill Gaps:
{skill_gaps_list}

{recruiter_notes_section}

TASK:
Write a personalized rejection email that:
1. Thanks the candidate genuinely for their time and interest
2. Acknowledges 2-3 SPECIFIC strengths you identified (be genuine and specific)
3. Explains the decision professionally without being harsh
4. Provides 2-3 ACTIONABLE development suggestions based on their gaps
5. Offers encouragement for their career journey
6. Maintains their dignity and leaves the door open for future opportunities

TONE: {tone}
- warm: Empathetic, caring, like a mentor giving advice
- professional: Business-appropriate, respectful, clear
- encouraging: Optimistic, motivational, growth-focused

IMPORTANT RULES:
- Be SPECIFIC - mention actual skills and experiences, not generic statements
- Be HONEST but KIND - don't sugarcoat but don't be harsh either
- Be ACTIONABLE - give concrete suggestions they can act on
- Be BRIEF - respect their time, aim for 200-300 words
- NO corporate jargon or hollow phrases like "after careful consideration"
- Write as a HUMAN would, not as an AI or template
- Use the candidate's first name naturally in the message

OUTPUT FORMAT (JSON):
{{
    "subject": "Your application for [Job Title] - Feedback",
    "greeting": "Opening greeting line",
    "appreciation": "Genuine thanks and acknowledgment paragraph",
    "strengths_paragraph": "Paragraph highlighting their specific strengths",
    "decision_paragraph": "Brief, professional explanation of the decision",
    "development_paragraph": "Actionable development suggestions",
    "closing_paragraph": "Encouraging close with well-wishes",
    "signature": "Warm sign-off",
    "key_points": ["List of 3-4 main points covered"],
    "development_suggestions": ["2-3 specific actionable suggestions"],
    "recommended_resources": ["Optional: 1-2 learning resources if applicable"]
}}"""

    WHATSAPP_PROMPT_TEMPLATE = """Based on this email rejection feedback, create a shorter WhatsApp-appropriate version.

ORIGINAL EMAIL:
{email_body}

REQUIREMENTS:
- Maximum 500 characters
- Keep the warmth and personalization
- Include 1-2 key strengths
- Include 1 actionable suggestion
- End with encouragement
- Use casual but professional tone (WhatsApp style)
- Use emojis sparingly (1-2 maximum) if appropriate for the tone

OUTPUT: Just the WhatsApp message text, nothing else."""

    def __init__(self):
        self.llm = llm_service
    
    async def generate_personalized_feedback(
        self,
        request: PersonalizedFeedbackRequest,
        db: AsyncSession | None = None
    ) -> PersonalizedFeedbackResult:
        """
        Generate personalized rejection feedback using Claude AI.
        
        Args:
            request: PersonalizedFeedbackRequest with all context
            db: Optional database session
            
        Returns:
            PersonalizedFeedbackResult with generated feedback
        """
        logger.info(
            f"Generating personalized feedback for candidate {request.candidate.candidate_id} "
            f"for job {request.job.job_id}"
        )
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            body_text, feedback_data = self._build_f851_template_body(request)
            body_html = self._compose_html_from_template(body_text, request)

            # FairnessGuard — verificar conteúdo antes de salvar para aprovação
            fairness_warnings: list[str] = []
            guard_result = _fairness_guard.check(body_text)
            if guard_result.is_blocked:
                logger.warning(
                    "FairnessGuard bloqueou feedback de rejeição",
                    extra={
                        "candidate_id": request.candidate.candidate_id,
                        "job_id": request.job.job_id,
                        "category": guard_result.category,
                        "blocked_terms": guard_result.blocked_terms,
                    },
                )
                body_text = (
                    "[Feedback em revisão — conteúdo identificado para verificação de compliance. "
                    "Por favor, revise e edite manualmente antes de enviar.]"
                )
                body_html = f"<p>{body_text}</p>"
            else:
                implicit = _fairness_guard.check_implicit_bias(body_text)
                if implicit.blocked_terms:
                    fairness_warnings.extend(implicit.blocked_terms)

            whatsapp_message = None
            if request.channel in [FeedbackChannel.WHATSAPP, FeedbackChannel.BOTH]:
                whatsapp_message = await self._generate_whatsapp_version(body_text)

            feedback_id = str(uuid.uuid4())

            record = PersonalizedFeedbackRecord(
                id=feedback_id,
                company_id=request.company_id,
                candidate_id=request.candidate.candidate_id,
                candidate_name=request.candidate.name,
                candidate_email=request.candidate.email,
                candidate_phone=request.candidate.phone,
                job_id=request.job.job_id,
                job_title=request.job.title,
                wsi_score=request.evaluation.overall_wsi,
                wsi_classification=request.evaluation.classification,
                channel=request.channel.value,
                tone=request.tone.value,
                subject=feedback_data.get("subject", f"Regarding your application - {request.job.title}"),
                body_text=body_text,
                body_html=body_html,
                whatsapp_message=whatsapp_message,
                strengths_highlighted=request.evaluation.strengths[:5],
                development_areas_highlighted=request.evaluation.development_areas[:5],
                development_suggestions=feedback_data.get("development_suggestions", []),
                recommended_resources=feedback_data.get("recommended_resources", []),
                personalization_level="high",
                ai_model_used="f851-template",
                status=PersonalizedFeedbackStatus.DRAFT.value,
                requested_by=request.requested_by,
                extra_data={
                    "include_development_plan": request.include_development_plan,
                    "include_resources": request.include_resources,
                    "recruiter_notes": request.recruiter_notes,
                    "fairness_warnings": fairness_warnings,
                }
            )
            
            db.add(record)
            await db.commit()
            await db.refresh(record)
            
            # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
            logger.info(f"Generated personalized feedback {feedback_id} for candidate {request.candidate.name}")

            if not guard_result.is_blocked and getattr(request, "auto_send", False):
                record.status = PersonalizedFeedbackStatus.APPROVED.value
                record.approved_by = "auto_send"
                record.approved_at = datetime.utcnow()
                await db.commit()
                try:
                    from app.jobs.celery_tasks import feedback_auto_send_task
                    feedback_auto_send_task.delay(feedback_id, request.company_id)
                    logger.info("feedback.auto_send dispatched post-generation id=%s", feedback_id)
                except Exception as send_exc:
                    logger.warning("feedback.auto_send dispatch failed id=%s: %s", feedback_id, send_exc)

            try:
                await audit_service.log_decision(
                    company_id=request.company_id,
                    agent_name="personalized_feedback",
                    decision_type="generate_feedback",
                    action="generate_rejection_feedback",
                    decision=request.decision_type,
                    reasoning=[
                        "Personalized feedback generated",
                        f"WSI classification: {request.evaluation.classification}",
                        f"WSI score: {request.evaluation.overall_wsi}/5.0",
                        f"Decision: {request.decision_type}",
                        "AI-generated: True",
                        f"Auto-send: {getattr(request, 'auto_send', False)}",
                    ],
                    criteria_used=["wsi_score", "strengths", "development_areas", "skill_gaps", "classification"],
                    candidate_id=request.candidate.candidate_id,
                    job_vacancy_id=request.job.job_id,
                    score=request.evaluation.overall_wsi,
                    confidence=0.9,
                    human_review_required=not getattr(request, "auto_send", False),
                    demographic_proxies={},
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for personalized_feedback: {audit_err}")

            return PersonalizedFeedbackResult(
                feedback_id=feedback_id,
                subject=record.subject,
                body_text=body_text,
                body_html=body_html,
                whatsapp_message=whatsapp_message,
                key_points=feedback_data.get("key_points", []),
                development_suggestions=feedback_data.get("development_suggestions", []),
                recommended_resources=feedback_data.get("recommended_resources", []),
                personalization_level="high",
                ai_model_used="f851-template",
                status=PersonalizedFeedbackStatus.DRAFT,
                created_at=record.created_at
            )
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error generating personalized feedback: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    def _build_f851_template_body(
        self, request: PersonalizedFeedbackRequest
    ) -> tuple:
        """Gera feedback usando template determinístico F8.5.1 (spec seção 8.5.1).

        Template com variáveis — não LLM livre. Garante previsibilidade, auditabilidade
        e equidade entre candidatos com scores equivalentes. (EU AI Act + LGPD Art. 20)
        """
        eval_ctx = request.evaluation
        cand = request.candidate
        job = request.job

        score_10 = round(eval_ctx.overall_wsi * 2, 1)
        seniority_label = getattr(eval_ctx, "seniority_label", None) or job.seniority_level or "a vaga"

        _CLASS_LABEL = {
            "excepcional":     "Excepcional",
            "excelente":       "Excelente",
            "alto":            "Alto",
            "medio":           "Médio",
            "abaixo_da_media": "Abaixo da média",
            "regular":         "Regular / Baixo",
        }
        classification_label = _CLASS_LABEL.get(eval_ctx.classification, eval_ctx.classification.title())

        subject = f"Retorno sobre sua candidatura — {job.title}"

        lines: list[str] = []
        lines.append(f"Olá, {cand.name.split()[0]},")
        lines.append("")
        lines.append(
            f"Agradecemos o seu interesse e tempo dedicado ao processo seletivo para a vaga de {job.title}."
        )
        if not job.is_confidential and job.company_name:
            lines.append(
                f"Sua candidatura foi analisada com atenção pela equipe de {job.company_name}."
            )
        lines.append("")

        strengths = eval_ctx.strengths or []
        dev_areas = eval_ctx.development_areas or []
        skill_gaps = eval_ctx.skill_gaps or []
        comp_scores: dict = eval_ctx.competency_scores or {}

        if comp_scores:
            for competency, raw_score in comp_scores.items():
                score_comp = round(float(raw_score) * 2, 1)
                lines.append("─" * 60)
                lines.append(f"Avaliação — {competency}")
                lines.append("─" * 60)
                lines.append("")
                lines.append(f"Sua resposta foi avaliada em {score_comp}/10 nesta competência.")
                lines.append("")

                if float(raw_score) >= 4.5:
                    lines.append("Pontos identificados como destaque:")
                elif float(raw_score) >= 3.5:
                    lines.append("Pontos identificados como fortes:")
                elif float(raw_score) >= 2.5:
                    lines.append("Pontos presentes na sua resposta:")

                detected = [s for s in strengths if competency.lower() in s.lower()] or (
                    strengths[:2] if float(raw_score) >= 2.5 else []
                )
                for sig in detected[:3]:
                    lines.append(f"• {sig}")

                if float(raw_score) < 4.0 or dev_areas:
                    lines.append("")
                    absent = [d for d in dev_areas if competency.lower() in d.lower()] or (
                        dev_areas[:2] if float(raw_score) < 3.5 else []
                    )
                    if absent:
                        lines.append("Pontos que poderiam enriquecer a resposta:")
                        for sig in absent[:3]:
                            lines.append(f"• {sig}")

                lines.append("")
                if float(raw_score) >= 3.5:
                    lines.append(f"Nível de maturidade esperado para {seniority_label}: atingido ✓")
                elif float(raw_score) >= 2.5:
                    lines.append(
                        f"Nível esperado para {seniority_label}: a resposta demonstrou boa base — "
                        "aprofundar exemplos com processo próprio desenvolvido fortaleceria a avaliação."
                    )
                else:
                    lines.append(
                        f"Nível esperado para {seniority_label}: a resposta apresentou experiências iniciais — "
                        "busque exemplos em que você tomou decisões de forma independente e os resultados foram mensuráveis."
                    )
                lines.append("")
        else:
            lines.append("─" * 60)
            lines.append("Avaliação Geral")
            lines.append("─" * 60)
            lines.append("")
            lines.append(f"Sua avaliação geral foi de {score_10}/10 ({classification_label}).")
            lines.append("")

            if eval_ctx.overall_wsi >= 2.5 and strengths:
                if eval_ctx.overall_wsi >= 4.5:
                    lines.append("Pontos identificados como destaque:")
                elif eval_ctx.overall_wsi >= 3.5:
                    lines.append("Pontos identificados como fortes:")
                else:
                    lines.append("Pontos presentes na sua candidatura:")
                for s in strengths[:3]:
                    lines.append(f"• {s}")
                lines.append("")

            if dev_areas or skill_gaps:
                lines.append("Pontos que poderiam enriquecer seu perfil para esta vaga:")
                for d in (dev_areas + skill_gaps)[:3]:
                    lines.append(f"• {d}")
                lines.append("")

            if eval_ctx.overall_wsi >= 3.5:
                lines.append(f"Nível de maturidade esperado para {seniority_label}: atingido ✓")
            elif eval_ctx.overall_wsi >= 2.5:
                lines.append(
                    f"Nível esperado para {seniority_label}: a resposta demonstrou boa base — "
                    "aprofundar exemplos com processo próprio desenvolvido fortaleceria a avaliação."
                )
            else:
                lines.append(
                    f"Nível esperado para {seniority_label}: a resposta apresentou experiências iniciais — "
                    "busque exemplos em que você tomou decisões de forma independente e os resultados foram mensuráveis."
                )
            lines.append("")

        # BLOCO_NIVEL — decisão final (3 caminhos: APROVADO, EM_AVALIACAO, REPROVADO)
        lines.append("─" * 60)
        decision_type = getattr(request, "decision_type", "REPROVADO")
        failed_gates = getattr(request, "failed_gates", []) or []

        _GATE_LABELS = {
            "G1": "elegibilidade",
            "G2": "injeção de prompt",
            "G3": "competência técnica mínima",
            "G4": "skill crítica",
            "G5": "engajamento insuficiente",
            "G6": "inflação sistemática",
        }

        if decision_type == "APROVADO":
            lines.append("Resultado: Parabéns! Você avançou para a próxima etapa.")
            lines.append("")
            lines.append(
                f"Sua performance na triagem para a vaga de {job.title} foi positiva e você será "
                "contatado(a) em breve com as próximas etapas do processo seletivo."
            )
        elif decision_type == "EM_AVALIACAO":
            lines.append("Resultado: Candidatura em análise.")
            lines.append("")
            lines.append(
                f"Sua candidatura para a vaga de {job.title} está sendo avaliada pela equipe responsável. "
                "Você receberá um retorno assim que o processo de análise for concluído."
            )
        else:  # REPROVADO
            lines.append("Resultado: Não seguiremos com sua candidatura neste momento.")
            lines.append("")
            lines.append(
                f"Após avaliação técnica para a vaga de {job.title}, não avançaremos com sua candidatura "
                "neste processo. Agradecemos o tempo dedicado e encorajamos novas oportunidades."
            )
            if failed_gates:
                gate_reasons = [_GATE_LABELS.get(g, g) for g in failed_gates]
                lines.append("")
                lines.append(f"Critério(s) que não foram atingidos: {', '.join(gate_reasons)}.")

        lines.append("─" * 60)
        lines.append(
            "Esta avaliação foi realizada de forma automatizada pelo sistema LIA."
        )
        lines.append(
            "A decisão final é responsabilidade do consultor responsável pelo processo."
        )
        lines.append(
            "Em caso de dúvidas sobre o processo, entre em contato pelo canal indicado no convite."
        )
        lines.append("─" * 60)

        body_text = "\n".join(lines)

        feedback_data = {
            "subject": subject,
            "key_points": strengths[:5],
            "development_suggestions": dev_areas[:5],
            "recommended_resources": [],
            "template_version": "F8.5.1",
            "decision_type": decision_type,
            "failed_gates": failed_gates,
        }
        return body_text, feedback_data

    def _compose_html_from_template(
        self, body_text: str, request: PersonalizedFeedbackRequest
    ) -> str:
        """Converte texto plano do template F8.5.1 para HTML simples."""
        lines = body_text.split("\n")
        html_lines: list[str] = [
            "<html><body style='font-family:Arial,sans-serif;font-size:14px;color:#333;max-width:600px;margin:auto;padding:20px;'>"
        ]
        for line in lines:
            if line.startswith("─"):
                html_lines.append("<hr style='border:1px solid #e0e0e0;margin:12px 0;'>")
            elif line.startswith("•"):
                html_lines.append(f"<li style='margin:4px 0;'>{line[1:].strip()}</li>")
            elif line.strip() == "":
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p style='margin:4px 0;'>{line}</p>")
        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    async def send_approval_feedback(
        self,
        candidate: CandidateContext,
        job: JobContext,
        evaluation: WSIEvaluationContext,
        company_id: str = None,
        db: AsyncSession | None = None,
    ) -> PersonalizedFeedbackResult:
        """Gap #11 — Path APROVADO: gera feedback de convite para próxima etapa."""
        request = PersonalizedFeedbackRequest(
            candidate=candidate,
            job=job,
            evaluation=evaluation,
            company_id=company_id,
            decision_type="APROVADO",
            channel=FeedbackChannel.EMAIL,
            tone=FeedbackTone.ENCOURAGING,
        )
        return await self.generate_personalized_feedback(request, db=db)

    async def send_review_feedback(
        self,
        candidate: CandidateContext,
        job: JobContext,
        evaluation: WSIEvaluationContext,
        company_id: str = None,
        db: AsyncSession | None = None,
    ) -> PersonalizedFeedbackResult:
        """Gap #11 — Path EM_AVALIACAO: gera feedback de análise em andamento."""
        request = PersonalizedFeedbackRequest(
            candidate=candidate,
            job=job,
            evaluation=evaluation,
            company_id=company_id,
            decision_type="EM_AVALIACAO",
            channel=FeedbackChannel.EMAIL,
            tone=FeedbackTone.PROFESSIONAL,
        )
        return await self.generate_personalized_feedback(request, db=db)

    def _build_personalization_prompt(self, request: PersonalizedFeedbackRequest) -> str:
        """Build the AI prompt for personalization."""
        
        strengths_list = "\n".join([f"  - {s}" for s in request.evaluation.strengths]) or "  - General professional aptitude"
        development_list = "\n".join([f"  - {d}" for d in request.evaluation.development_areas]) or "  - Areas for continued growth"
        skill_gaps_list = "\n".join([f"  - {g}" for g in request.evaluation.skill_gaps]) or "  - Some required technical skills"
        
        recruiter_notes_section = ""
        if request.recruiter_notes:
            recruiter_notes_section = f"\n- Recruiter Notes:\n  {request.recruiter_notes}\n"
        
        tone_map = {
            FeedbackTone.WARM: "warm",
            FeedbackTone.PROFESSIONAL: "professional",
            FeedbackTone.ENCOURAGING: "encouraging"
        }
        
        return self.PERSONALIZATION_PROMPT_TEMPLATE.format(
            candidate_name=request.candidate.name,
            current_title=request.candidate.current_title or "Professional",
            current_company=request.candidate.current_company or "their current company",
            years_of_experience=request.candidate.years_of_experience or "several",
            technical_skills=", ".join(request.candidate.technical_skills[:5]) if request.candidate.technical_skills else "various technical skills",
            job_title=request.job.title,
            company_name=request.job.company_name or "our company",
            required_skills=", ".join(request.job.required_skills[:5]) if request.job.required_skills else "various skills",
            job_seniority=request.job.seniority_level or "mid-level",
            wsi_score=f"{request.evaluation.overall_wsi:.1f}",
            wsi_classification=request.evaluation.classification,
            technical_wsi=f"{request.evaluation.technical_wsi:.1f}" if request.evaluation.technical_wsi else "N/A",
            behavioral_wsi=f"{request.evaluation.behavioral_wsi:.1f}" if request.evaluation.behavioral_wsi else "N/A",
            strengths_list=strengths_list,
            development_areas_list=development_list,
            skill_gaps_list=skill_gaps_list,
            recruiter_notes_section=recruiter_notes_section,
            tone=tone_map.get(request.tone, "warm")
        )
    
    def _parse_ai_response(self, content: str) -> dict[str, Any]:
        """Parse the AI response into structured data."""
        import json
        
        try:
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {
                "subject": "Regarding Your Application",
                "greeting": "Dear Candidate,",
                "appreciation": "Thank you for taking the time to apply and participate in our selection process.",
                "strengths_paragraph": "We were impressed by your professional background and dedication.",
                "decision_paragraph": "After careful evaluation, we have decided to move forward with other candidates whose profiles more closely match our current needs.",
                "development_paragraph": "We encourage you to continue developing your skills and exploring opportunities in your field.",
                "closing_paragraph": "We wish you the best in your career journey.",
                "signature": "Best regards,\nThe Recruitment Team",
                "key_points": ["Thank you for applying", "Strengths acknowledged", "Best wishes for the future"],
                "development_suggestions": ["Continue developing technical skills", "Build industry experience"],
                "recommended_resources": []
            }
    
    def _compose_email_body(self, feedback_data: dict[str, Any]) -> str:
        """Compose the plain text email body from parsed data."""
        parts = [
            feedback_data.get("greeting", ""),
            "",
            feedback_data.get("appreciation", ""),
            "",
            feedback_data.get("strengths_paragraph", ""),
            "",
            feedback_data.get("decision_paragraph", ""),
            "",
            feedback_data.get("development_paragraph", ""),
            "",
            feedback_data.get("closing_paragraph", ""),
            "",
            feedback_data.get("signature", "Best regards,\nRecruitment Team")
        ]
        return "\n".join(parts)
    
    def _compose_html_body(
        self,
        feedback_data: dict[str, Any],
        request: PersonalizedFeedbackRequest
    ) -> str:
        """Compose the HTML email body."""
        
        company_name = request.job.company_name or "Our Company"
        job_title = request.job.title
        
        development_suggestions = feedback_data.get("development_suggestions", [])
        suggestions_html = ""
        if development_suggestions:
            suggestions_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for suggestion in development_suggestions[:3]:
                suggestions_html += f"<li style='margin-bottom: 8px;'>{suggestion}</li>"
            suggestions_html += "</ul>"
        
        resources = feedback_data.get("recommended_resources", [])
        resources_html = ""
        if resources:
            resources_html = """
            <div style="background-color: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #0066cc;">📚 Recursos Recomendados:</p>
                <ul style="margin: 0; padding-left: 20px;">
            """
            for resource in resources[:2]:
                resources_html += f"<li>{resource}</li>"
            resources_html += "</ul></div>"
        
        signature = feedback_data.get("signature", "Atenciosamente,\nEquipe de Recrutamento")
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback sobre sua candidatura</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.8; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Feedback sobre sua candidatura</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">{job_title} - {company_name}</p>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <p style="font-size: 16px; margin-bottom: 20px;">{feedback_data.get("greeting", "Olá,")}</p>
        
        <p style="font-size: 15px;">{feedback_data.get("appreciation", "")}</p>
        
        <div style="background-color: #f0f9f0; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; font-size: 14px; color: #155724;">
                <strong>✨ Pontos Fortes Identificados:</strong><br/>
                {feedback_data.get("strengths_paragraph", "")}
            </p>
        </div>
        
        <p style="font-size: 15px;">{feedback_data.get("decision_paragraph", "")}</p>
        
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #856404;">💡 Sugestões de Desenvolvimento:</p>
            {suggestions_html if suggestions_html else f"<p style='margin: 0; color: #555;'>{feedback_data.get('development_paragraph', '')}</p>"}
        </div>
        
        {resources_html}
        
        <p style="font-size: 15px; margin-top: 20px;">{feedback_data.get("closing_paragraph", "")}</p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="color: #666; font-size: 14px; white-space: pre-line;">
            {signature}
        </p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">
        <p style="margin: 0; font-size: 12px; color: #888;">
            Esta mensagem foi personalizada especialmente para você pela LIA, nossa assistente de recrutamento.
        </p>
    </div>
</body>
</html>"""
        
        return html
    
    async def _generate_whatsapp_version(self, email_body: str) -> str:
        """Generate a shorter WhatsApp-appropriate version of the feedback."""
        try:
            prompt = self.WHATSAPP_PROMPT_TEMPLATE.format(email_body=email_body)
            _response = await self.llm.safe_invoke(prompt, provider="claude")
            response = type("R", (), {"content": _response})()
            content = response.content if isinstance(response.content, str) else str(response.content)
            
            if len(content) > 500:
                content = content[:497] + "..."
            
            return content.strip()
        except Exception as e:
            logger.warning(f"Failed to generate WhatsApp version: {e}")
            return email_body[:400] + "..."
    
    async def get_feedback_preview(
        self,
        feedback_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """
        Get a preview of generated feedback for recruiter review.
        
        Args:
            feedback_id: ID of the feedback record
            db: Optional database session
            
        Returns:
            Preview data or None if not found
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return None
            
            return {
                "feedback_id": record.id,
                "candidate": {
                    "id": record.candidate_id,
                    "name": record.candidate_name,
                    "email": record.candidate_email,
                    "phone": record.candidate_phone
                },
                "job": {
                    "id": record.job_id,
                    "title": record.job_title
                },
                "evaluation": {
                    "wsi_score": record.wsi_score,
                    "classification": record.wsi_classification
                },
                "content": {
                    "subject": record.subject,
                    "body_text": record.body_text,
                    "body_html": record.body_html,
                    "whatsapp_message": record.whatsapp_message
                },
                "personalization": {
                    "strengths_highlighted": record.strengths_highlighted,
                    "development_areas": record.development_areas_highlighted,
                    "development_suggestions": record.development_suggestions,
                    "recommended_resources": record.recommended_resources,
                    "level": record.personalization_level
                },
                "meta": {
                    "channel": record.channel,
                    "tone": record.tone,
                    "status": record.status,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "requested_by": record.requested_by
                }
            }
        finally:
            if should_close:
                await db.close()
    
    async def approve_feedback(
        self,
        feedback_id: str,
        approved_by: str,
        edited_subject: str | None = None,
        edited_body: str | None = None,
        editor_notes: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Approve feedback for sending (with optional edits).
        
        Args:
            feedback_id: ID of the feedback record
            approved_by: User who approved the feedback
            edited_subject: Optional edited subject
            edited_body: Optional edited body
            editor_notes: Optional notes from the editor
            db: Optional database session
            
        Returns:
            Updated feedback data
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()
            
            if not record:
                raise ValueError(f"Feedback record {feedback_id} not found")
            
            record.approved_by = approved_by
            record.approved_at = datetime.utcnow()
            
            if edited_subject or edited_body:
                record.status = PersonalizedFeedbackStatus.EDITED.value
                if edited_subject:
                    record.edited_subject = edited_subject
                if edited_body:
                    record.edited_body = edited_body
                if editor_notes:
                    record.editor_notes = editor_notes
            else:
                record.status = PersonalizedFeedbackStatus.APPROVED.value
            
            await db.commit()
            await db.refresh(record)
            
            logger.info(f"Feedback {feedback_id} approved by {approved_by}")

            try:
                from app.jobs.celery_tasks import feedback_auto_send_task
                feedback_auto_send_task.delay(feedback_id, record.company_id)
                logger.info("feedback.auto_send dispatched id=%s", feedback_id)
            except Exception as send_exc:
                logger.warning("feedback.auto_send dispatch failed id=%s: %s", feedback_id, send_exc)
            
            return {
                "feedback_id": record.id,
                "status": record.status,
                "approved_by": record.approved_by,
                "approved_at": record.approved_at.isoformat() if record.approved_at else None,
                "was_edited": bool(edited_subject or edited_body),
                "ready_to_send": True,
                "auto_send_dispatched": True,
            }
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def reject_feedback(
        self,
        feedback_id: str,
        rejected_by: str,
        rejection_reason: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Reject feedback and optionally regenerate.
        
        Args:
            feedback_id: ID of the feedback record
            rejected_by: User who rejected the feedback
            rejection_reason: Reason for rejection
            db: Optional database session
            
        Returns:
            Status update
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()
            
            if not record:
                raise ValueError(f"Feedback record {feedback_id} not found")
            
            record.status = "rejected"
            record.extra_data = {
                **(record.extra_data or {}),
                "rejected_by": rejected_by,
                "rejected_at": datetime.utcnow().isoformat(),
                "rejection_reason": rejection_reason
            }
            
            await db.commit()
            
            logger.info(f"Feedback {feedback_id} rejected by {rejected_by}: {rejection_reason}")
            
            return {
                "feedback_id": record.id,
                "status": "rejected",
                "rejected_by": rejected_by,
                "rejection_reason": rejection_reason
            }
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def mark_as_sent(
        self,
        feedback_id: str,
        channel: str,
        send_result: dict[str, Any],
        db: AsyncSession | None = None
    ) -> bool:
        """
        Mark feedback as sent after successful delivery.
        
        Args:
            feedback_id: ID of the feedback record
            channel: Channel used for sending
            send_result: Result from the sending operation
            db: Optional database session
            
        Returns:
            Success status
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return False
            
            record.status = PersonalizedFeedbackStatus.SENT.value
            record.sent_at = datetime.utcnow()
            record.sent_channel = channel
            record.send_result = send_result
            
            await db.commit()
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Feedback {feedback_id} marked as sent via {channel}")

            try:
                await audit_service.log_decision(
                    company_id=getattr(record, "company_id", None),
                    agent_name="personalized_feedback",
                    decision_type="send_message",
                    action="feedback_sent",
                    decision="sent",
                    reasoning=[
                        "Personalized feedback delivered to candidate",
                        f"Channel: {channel}",
                        f"Feedback type: {getattr(record, 'feedback_type', 'rejection')}",
                        "AI-generated: True",
                        f"Send result: {send_result.get('message_id', 'N/A') if isinstance(send_result, dict) else 'N/A'}",
                    ],
                    criteria_used=["feedback_status", "channel_availability", "approval_status"],
                    candidate_id=getattr(record, "candidate_id", None),
                    job_vacancy_id=getattr(record, "job_vacancy_id", None),
                    human_review_required=False,
                    demographic_proxies={},
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for feedback_sent: {audit_err}")

            return True
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def mark_as_failed(
        self,
        feedback_id: str,
        reason: str,
        send_result: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> bool:
        """
        Mark feedback as failed — preserves APPROVED/EDITED status so
        process_pending_sends can retry on the next run.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()

            if not record:
                return False

            is_policy_block = "FairnessGuard blocked" in reason
            record.status = PersonalizedFeedbackStatus.FAILED.value
            record.send_result = send_result or {}
            record.extra_data = {
                **(record.extra_data or {}),
                "last_failure_reason": reason,
                "last_failure_at": datetime.utcnow().isoformat(),
                "failure_type": "policy_blocked" if is_policy_block else "transient",
            }

            await db.commit()

            logger.info("Feedback %s marked as failed: %s", feedback_id, reason)
            return True
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()

    async def get_analytics(
        self,
        company_id: str,
        days: int = 30,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get analytics on personalized feedback effectiveness.
        
        Args:
            company_id: Company ID to filter by
            days: Number of days to look back
            db: Optional database session
            
        Returns:
            Analytics data
        """
        from datetime import timedelta
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            result = await db.execute(
                # ADR-001-EXEMPT: PersonalizedFeedbackRecord model is defined inline in this service module (line ~159); extracting to a repo would require relocating the model first. Tracked for Sprint 6 follow-up (move model to lia_models, then create PersonalizedFeedbackRepository).
                select(PersonalizedFeedbackRecord).where(
                    and_(
                        PersonalizedFeedbackRecord.company_id == company_id,
                        PersonalizedFeedbackRecord.created_at >= cutoff
                    )
                )
            )
            records = list(result.scalars())
            
            total = len(records)
            sent = sum(1 for r in records if r.status == "sent")
            approved = sum(1 for r in records if r.status in ["approved", "edited", "sent"])
            edited = sum(1 for r in records if r.status == "edited" or r.edited_body)
            rejected = sum(1 for r in records if r.status == "rejected")
            
            avg_wsi = sum(r.wsi_score or 0 for r in records) / total if total > 0 else 0
            
            opened = sum(1 for r in records if r.candidate_opened_at)
            clicked = sum(1 for r in records if r.candidate_clicked_at)
            
            by_channel = {}
            for r in records:
                channel = r.channel or "unknown"
                by_channel[channel] = by_channel.get(channel, 0) + 1
            
            by_tone = {}
            for r in records:
                tone = r.tone or "unknown"
                by_tone[tone] = by_tone.get(tone, 0) + 1
            
            return {
                "period_days": days,
                "total_generated": total,
                "total_sent": sent,
                "total_approved": approved,
                "total_edited": edited,
                "total_rejected": rejected,
                "approval_rate": approved / total if total > 0 else 0,
                "edit_rate": edited / total if total > 0 else 0,
                "average_wsi_score": avg_wsi,
                "engagement": {
                    "opened": opened,
                    "clicked": clicked,
                    "open_rate": opened / sent if sent > 0 else 0,
                    "click_rate": clicked / sent if sent > 0 else 0
                },
                "by_channel": by_channel,
                "by_tone": by_tone
            }
        finally:
            if should_close:
                await db.close()
    


personalized_feedback_service = PersonalizedFeedbackService()
