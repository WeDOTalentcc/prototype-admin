"""

# ADR-001-EXEMPT: Conversation manager spans WhatsApp/CompanyProfile/
# JobRequirement reads for multi-channel recruiter assist. Tenant scope
# established at service entry via session/user context.
# TODO Sprint 6: extract to WhatsAppConversationRepository + reuse existing  # R-048: needs owner + ticket
# CompanyProfileRepository / JobRequirementRepository.

WhatsApp Conversation Manager

Manages the conversational flow for candidate applications via WhatsApp.
Handles state transitions, LGPD consent, CV parsing, and screening questions.

Now supports multiple WhatsApp providers (Meta, Twilio) via the factory pattern.
Integrates with CVParserService for AI-powered CV parsing.
"""

import io
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory
from app.domains.communication.services.whatsapp_provider import WhatsAppProvider
from app.domains.cv_screening.services.eligibility_verification_service import (
    EligibilityQuestion,
    ReconsiderationContext,
    ReconsiderationResult,
    eligibility_service,
)
from app.domains.cv_screening.services.pre_qualification_service import (
    PreQualificationDecision,
    PreQualificationResult,
    pre_qualification_service,
)
from lia_models.job_vacancy import JobVacancy
from lia_models.whatsapp_conversation import ConversationState, WhatsAppConversation, WhatsAppMessage

logger = logging.getLogger(__name__)


class ConversationMessages:
    """Standard messages for the conversation flow."""
    
    @staticmethod
    def lgpd_request(company_name: str = "a empresa") -> str:
        return f"""Olá! 👋 Que bom que você se interessou pela vaga!

Eu sou a *LIA*, assistente de recrutamento da {company_name}. Vou te ajudar com o processo de candidatura.

Antes de começarmos, preciso da sua autorização:

📋 *TERMO DE CONSENTIMENTO (LGPD)*
Ao continuar, você autoriza:
• Coleta e armazenamento dos seus dados pessoais e profissionais
• Análise do seu currículo por inteligência artificial
• Compartilhamento das informações com o time de recrutamento
• Contato por WhatsApp, email ou telefone sobre oportunidades

Seus dados serão tratados conforme nossa Política de Privacidade. Você pode solicitar exclusão a qualquer momento.

Para continuar, responda: *ACEITO*"""
    
    @staticmethod
    def lgpd_accepted() -> str:
        return """Perfeito! Obrigada pela autorização. ✅

Agora vou te conhecer melhor. Meu papel é:
1. Receber e analisar seu currículo
2. Avaliar sua aderência à vaga
3. Fazer algumas perguntas de triagem
4. Encaminhar sua candidatura para o recrutador

📄 Por favor, *envie seu currículo* (PDF ou Word)."""
    
    @staticmethod
    def lgpd_not_accepted() -> str:
        return """Entendo! Sem a autorização não consigo prosseguir com sua candidatura.

Se mudar de ideia, é só responder *ACEITO* a qualquer momento.

Obrigada pelo interesse! 🙏"""
    
    @staticmethod
    def cv_received_parsing() -> str:
        return """Recebi seu currículo! Estou analisando... ⏳"""
    
    @staticmethod
    def cv_parsed(name: str, summary: str) -> str:
        return f"""Analisei seu perfil, *{name}*! 📊

{summary}

Está correto? Se precisar corrigir algo, me avise.
Caso contrário, vamos para as perguntas de triagem."""
    
    @staticmethod
    def cv_parse_error() -> str:
        return """Tive dificuldade para ler seu currículo. 😕

Por favor, envie novamente em formato *PDF* ou *Word* (.docx).
Se preferir, pode também enviar como *imagem* do documento."""
    
    @staticmethod
    def screening_question(index: int, question: str) -> str:
        return f"""{index}️⃣ {question}"""
    
    @staticmethod
    def screening_complete() -> str:
        return """Ótimo! Coletei todas as informações necessárias. ✅"""
    
    @staticmethod
    def additional_info_request() -> str:
        return """Quase terminando! Mais algumas informações:

📧 Qual seu *melhor email* para contato?"""

    @staticmethod
    def confirm_email(email: str) -> str:
        return f"""Encontrei o email *{email}* no seu currículo.

Está correto? Responda *SIM* para confirmar ou envie o email correto."""

    @staticmethod
    def ask_email() -> str:
        return """Não encontrei um email no seu currículo. 📧

Por favor, informe seu *melhor email* para contato."""

    @staticmethod
    def rubric_rejection(job_title: str, score: float) -> str:
        return f"""Obrigada por se candidatar à vaga de *{job_title}*! 🙏

Após análise do seu perfil, identificamos que neste momento seu currículo não atende aos requisitos mínimos desta posição.

💡 *Dicas para melhorar sua candidatura:*
• Atualize seu currículo com experiências recentes
• Destaque habilidades relacionadas à vaga
• Adicione certificações relevantes

Seu perfil ficará em nosso banco de talentos e você será considerado para oportunidades futuras compatíveis.

Desejamos sucesso! 🍀"""

    @staticmethod
    def awaiting_screening_message(job_title: str) -> str:
        return f"""Seus dados para a vaga de *{job_title}* foram registrados com sucesso! ✅

No momento, estamos com muitos candidatos em processo de triagem para esta posição.

📋 *Próximos passos:*
Entraremos em contato em breve para continuar o processo seletivo. Fique atento ao seu WhatsApp e email!

Obrigada pela paciência! 🙏"""

    @staticmethod
    def awaiting_screening_already() -> str:
        return """Seus dados já foram registrados! Entraremos em contato em breve para continuar o processo de triagem. Fique atento! 🙏"""
    
    @staticmethod
    def completion_message(job_title: str, days: int = 5) -> str:
        return f"""Perfeito! Seu cadastro está completo. ✅

📋 *RESUMO DA SUA CANDIDATURA:*
• Vaga: {job_title}
• Status: Em análise

🔔 *Próximos passos:*
Vou encaminhar suas informações para o recrutador responsável.
Você receberá um retorno sobre o andamento do processo em até {days} dias úteis.

Obrigada pelo interesse e boa sorte! 🍀"""
    
    @staticmethod
    def feedback_approved(job_title: str, recruiter_name: str = "o recrutador") -> str:
        return f"""Olá! 👋

Tenho novidades sobre sua candidatura para *{job_title}*!

🎉 *Parabéns!* Você foi aprovado para a próxima etapa do processo seletivo.

{recruiter_name} vai entrar em contato para agendar uma conversa.
Fique atento ao seu email e WhatsApp!"""
    
    @staticmethod
    def feedback_rejected(job_title: str) -> str:
        return f"""Olá! 👋

Obrigada por participar do processo seletivo para *{job_title}*.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados aos requisitos específicos desta vaga.

Seu currículo permanece em nossa base e você será considerado para oportunidades futuras compatíveis com seu perfil.

Agradecemos seu interesse e desejamos sucesso! 🍀"""
    
    @staticmethod
    def expired_conversation() -> str:
        return """Olá! Parece que nossa conversa ficou inativa por muito tempo.

Se ainda tiver interesse na vaga, por favor inicie uma nova candidatura através do link da vaga.

Obrigada! 🙏"""
    
    @staticmethod
    def error_message() -> str:
        return """Desculpe, tive um problema técnico. 😕

Por favor, tente novamente em alguns minutos ou entre em contato com o recrutador diretamente."""


class ConversationManager:
    """
    Manages WhatsApp conversation state and flow for job applications.
    
    Phase 1 (Inscription):
    1. INITIAL -> WAITING_LGPD: Candidate sends first message with job reference
    2. WAITING_LGPD -> WAITING_CV: Candidate accepts LGPD
    3. WAITING_CV -> CONFIRMING_CV: Candidate sends CV document, parsing
    4. CONFIRMING_CV -> CONFIRMING_EMAIL: CV confirmed, ask/confirm email
    5. CONFIRMING_EMAIL -> Rubric evaluation
    
    PAUSE (Saturation check):
    - Score < 55: automatic rejection with feedback -> COMPLETED
    - Saturated: candidate queued -> AWAITING_SCREENING
    - Not saturated: proceed to Phase 2
    
    Phase 2 (Screening):
    6. PRE_QUALIFICATION/SCREENING: Screening questions
    7. SCREENING -> ADDITIONAL_INFO: Screening questions answered
    8. ADDITIONAL_INFO -> COMPLETED: Contact info collected
    9. COMPLETED -> FEEDBACK_SENT: Recruiter decision communicated
    
    Now supports multiple providers via factory pattern.
    """
    
    CONVERSATION_TIMEOUT_HOURS = 72
    
    def __init__(self, db: AsyncSession, provider: WhatsAppProvider | None = None):
        """
        Initialize ConversationManager.
        
        Args:
            db: Database session
            provider: Optional WhatsApp provider (will use factory if not provided)
        """
        self.db = db
        self._provider = provider
    
    async def get_provider(self, company_id: str) -> WhatsAppProvider:
        """Get the appropriate WhatsApp provider for a company."""
        if self._provider:
            return self._provider
        return await WhatsAppProviderFactory.get_provider(company_id, self.db)
    
    async def get_or_create_conversation(
        self,
        phone_number: str,
        company_id: str,
        job_vacancy_id: UUID | None = None
    ) -> WhatsAppConversation:
        """Get existing active conversation or create a new one."""
        
        result = await self.db.execute(
            select(WhatsAppConversation)
            .where(WhatsAppConversation.phone_number == phone_number)
            .where(WhatsAppConversation.company_id == company_id)
            .where(WhatsAppConversation.state.notin_([
                ConversationState.COMPLETED,
                ConversationState.FEEDBACK_SENT,
                ConversationState.EXPIRED
            ]))
            .order_by(WhatsAppConversation.created_at.desc())
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            if conversation.created_at < datetime.utcnow() - timedelta(hours=self.CONVERSATION_TIMEOUT_HOURS):
                conversation.state = ConversationState.EXPIRED
                await self.db.commit()
            else:
                return conversation
        
        new_conversation = WhatsAppConversation(
            phone_number=phone_number,
            company_id=company_id,
            job_vacancy_id=job_vacancy_id,
            state=ConversationState.INITIAL,
            expires_at=datetime.utcnow() + timedelta(hours=self.CONVERSATION_TIMEOUT_HOURS)
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)
        
        return new_conversation
    
    async def process_incoming_message(
        self,
        phone_number: str,
        message_content: str,
        company_id: str,
        message_type: str = "text",
        media_data: dict[str, Any] | None = None
    ) -> str | None:
        """
        Process an incoming WhatsApp message and return the response.
        
        This is the main entry point for handling webhook messages.
        """
        try:
            job_vacancy_id = None
            if "Ref:" in message_content:
                import re
                ref_match = re.search(r'Ref:\s*(\S+)', message_content)
                if ref_match:
                    slug = ref_match.group(1)
                    job = await self._get_job_by_slug(slug)
                    if job:
                        job_vacancy_id = job.id
                        company_id = job.company_id
            
            conversation = await self.get_or_create_conversation(
                phone_number=phone_number,
                company_id=company_id,
                job_vacancy_id=job_vacancy_id
            )
            
            await self._log_message(
                conversation_id=conversation.id,
                direction="inbound",
                message_type=message_type,
                content=message_content,
                media_data=media_data
            )
            
            response = await self._handle_state(
                conversation=conversation,
                message_content=message_content,
                message_type=message_type,
                media_data=media_data
            )
            
            if response:
                await self._log_message(
                    conversation_id=conversation.id,
                    direction="outbound",
                    message_type="text",
                    content=response
                )
            
            return response
            
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"Error processing message from {phone_number}: {e}", exc_info=True)
            return ConversationMessages.error_message()
    
    async def _handle_state(
        self,
        conversation: WhatsAppConversation,
        message_content: str,
        message_type: str,
        media_data: dict[str, Any] | None
    ) -> str | None:
        """Handle message based on current conversation state."""
        
        state = conversation.state
        
        if state == ConversationState.INITIAL:
            return await self._handle_initial(conversation)
        
        elif state == ConversationState.WAITING_LGPD:
            return await self._handle_lgpd_response(conversation, message_content)
        
        elif state == ConversationState.WAITING_CV:
            return await self._handle_cv_submission(conversation, message_type, media_data)
        
        elif state == ConversationState.CONFIRMING_CV:
            return await self._handle_cv_confirmation(conversation, message_content)
        
        elif state == ConversationState.CONFIRMING_EMAIL:
            return await self._handle_email_confirmation(conversation, message_content)
        
        elif state == ConversationState.AWAITING_SCREENING:
            return ConversationMessages.awaiting_screening_already()
        
        elif state == ConversationState.PRE_QUALIFICATION:
            return await self._handle_pre_qualification_response(conversation, message_content)
        
        elif state == ConversationState.SCREENING:
            return await self._handle_screening_answer(conversation, message_content)
        
        elif state == ConversationState.ELIGIBILITY_CHECK:
            return await self._handle_eligibility_check(conversation, message_content)
        
        elif state == ConversationState.WAITING_RECONSIDERATION:
            return await self._handle_reconsideration_response(conversation, message_content)
        
        elif state == ConversationState.WAITING_CONFIRMATION:
            return await self._handle_confirmation_response(conversation, message_content)
        
        elif state == ConversationState.REDIRECTED_TALENT_POOL:
            return "Seu perfil está no nosso banco de talentos! Assim que surgir uma vaga adequada, entraremos em contato. 🙏"
        
        elif state == ConversationState.ADDITIONAL_INFO:
            return await self._handle_additional_info(conversation, message_content)
        
        elif state == ConversationState.COMPLETED:
            return "Sua candidatura já foi enviada! Aguarde nosso retorno. 🙏"
        
        elif state == ConversationState.EXPIRED:
            return ConversationMessages.expired_conversation()
        
        return None
    
    async def _handle_initial(self, conversation: WhatsAppConversation) -> str:
        """Handle initial message - request LGPD consent."""
        company_name = "a empresa"
        
        if conversation.job_vacancy_id:
            job = await self._get_job(conversation.job_vacancy_id)
            if job and job.masked_company_name:
                company_name = job.masked_company_name
        
        conversation.state = ConversationState.WAITING_LGPD
        await self.db.commit()
        
        return ConversationMessages.lgpd_request(company_name)
    
    async def _handle_lgpd_response(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle LGPD consent response."""
        normalized = message.strip().upper()
        
        if normalized in ["ACEITO", "ACEITAR", "SIM", "OK", "CONCORDO", "CONFIRMO"]:
            conversation.lgpd_accepted = True
            conversation.lgpd_accepted_at = datetime.utcnow()
            conversation.state = ConversationState.WAITING_CV
            await self.db.commit()
            
            return ConversationMessages.lgpd_accepted()
        
        return ConversationMessages.lgpd_not_accepted()
    
    async def _handle_cv_submission(
        self,
        conversation: WhatsAppConversation,
        message_type: str,
        media_data: dict[str, Any] | None
    ) -> str:
        """Handle CV document submission."""
        if message_type not in ["document", "image"] or not media_data:
            return "📄 Por favor, envie seu currículo em formato *PDF* ou *Word*."
        
        whatsapp = await self.get_provider(conversation.company_id)
        parsing_msg = ConversationMessages.cv_received_parsing()
        await whatsapp.send_text_message(conversation.phone_number, parsing_msg)
        
        try:
            cv_data = await self._parse_cv(media_data, company_id=conversation.company_id)
            
            if not cv_data.get("success"):
                return ConversationMessages.cv_parse_error()
            
            conversation.cv_received = True
            conversation.cv_received_at = datetime.utcnow()
            conversation.cv_parsed_data = cv_data.get("data", {})
            conversation.candidate_name = cv_data.get("data", {}).get("name", "Candidato")
            conversation.candidate_email = cv_data.get("data", {}).get("email")
            conversation.state = ConversationState.CONFIRMING_CV
            await self.db.commit()
            
            summary = self._format_cv_summary(cv_data.get("data", {}))
            
            return ConversationMessages.cv_parsed(
                name=conversation.candidate_name,
                summary=summary
            )
            
        except Exception as e:
            try:
                await self.db.rollback()
            except Exception:
                pass
            logger.error(f"Error parsing CV: {e}", exc_info=True)
            return ConversationMessages.cv_parse_error()
    
    async def _handle_cv_confirmation(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle CV data confirmation — transition to email confirmation (Phase 1)."""
        normalized = message.strip().lower()
        
        if any(word in normalized for word in ["corrigir", "errado", "incorreto", "não"]):
            return "Entendi! O que precisa ser corrigido?"
        
        cv_data = conversation.cv_parsed_data or {}
        extracted_email = cv_data.get("email")
        
        conversation.state = ConversationState.CONFIRMING_EMAIL
        await self.db.commit()
        
        if extracted_email:
            return ConversationMessages.confirm_email(extracted_email)
        else:
            return ConversationMessages.ask_email()

    async def _handle_email_confirmation(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle email confirmation/collection, then run rubric and check saturation."""
        import re
        normalized = message.strip().lower()
        
        cv_data = conversation.cv_parsed_data or {}
        extracted_email = cv_data.get("email")
        
        if extracted_email and normalized in ["sim", "yes", "ok", "confirmo", "correto", "confirmar"]:
            conversation.candidate_email = extracted_email
        else:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
            if email_match:
                conversation.candidate_email = email_match.group(0)
            else:
                return "Por favor, informe um email válido (ex: seu.email@exemplo.com)"
        
        await self.db.commit()
        
        return await self._run_rubric_and_check_saturation(conversation)

    async def _run_rubric_and_check_saturation(self, conversation: WhatsAppConversation) -> str:
        """Run rubric evaluation (pre-qualification) and check saturation before screening."""
        job = await self._get_job(conversation.job_vacancy_id) if conversation.job_vacancy_id else None
        job_title = job.title if job else "a vaga"
        
        pre_qual_result = await self._run_pre_qualification(conversation, job)
        
        score = pre_qual_result.score if pre_qual_result else 100
        
        if pre_qual_result:
            conversation.pre_qualification_result = pre_qual_result.result.value
            conversation.pre_qualification_score = pre_qual_result.score
            conversation.pre_qualification_matched = getattr(pre_qual_result, 'matched_requirements', None)
            conversation.pre_qualification_missing = getattr(pre_qual_result, 'missing_requirements', None)
            conversation.pre_qualification_at = datetime.utcnow()
        else:
            conversation.pre_qualification_result = "aligned"
            conversation.pre_qualification_score = 100
            conversation.pre_qualification_at = datetime.utcnow()
        
        if score < 55:
            conversation.pre_qualification_decision = "auto_rejected"
            conversation.state = ConversationState.COMPLETED
            conversation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            await self._create_candidate_from_conversation(conversation, status="rejected")
            
            return ConversationMessages.rubric_rejection(job_title, score)
        
        is_saturated = await self._check_saturation(conversation)
        
        if is_saturated:
            conversation.pre_qualification_decision = "queued_saturation"
            conversation.state = ConversationState.AWAITING_SCREENING
            await self.db.commit()
            
            await self._create_candidate_from_conversation(conversation, status="awaiting_screening")
            
            return ConversationMessages.awaiting_screening_message(job_title)
        
        if pre_qual_result is None or pre_qual_result.result == PreQualificationResult.ALIGNED:
            conversation.pre_qualification_decision = PreQualificationDecision.AUTO_ADVANCED.value
            conversation.state = ConversationState.SCREENING
            conversation.current_question_index = 0
            await self.db.commit()
            
            questions = await self._get_screening_questions(conversation.job_vacancy_id)
            
            if questions:
                intro = f"Seu perfil está bem alinhado com a vaga de {job_title}! Vamos para algumas perguntas.\n\n"
                return intro + ConversationMessages.screening_question(1, questions[0])
            else:
                conversation.state = ConversationState.ADDITIONAL_INFO
                await self.db.commit()
                return ConversationMessages.additional_info_request()
        
        conversation.state = ConversationState.PRE_QUALIFICATION
        await self.db.commit()
        
        return pre_qual_result.message

    async def _check_saturation(self, conversation: WhatsAppConversation) -> bool:
        """Check if the pipeline is saturated for the given job vacancy."""
        if not conversation.job_vacancy_id:
            return False
        
        try:
            job = await self._get_job(conversation.job_vacancy_id)
            if not job:
                return False
            
            from lia_models.company import CompanyProfile
            
            company_result = await self.db.execute(
                select(CompanyProfile).where(
                    CompanyProfile.is_default
                ).limit(1)
            )
            company = company_result.scalar_one_or_none()
            
            try:
                from uuid import UUID as _UUID
                company_uuid = _UUID(str(job.company_id))
                company_result2 = await self.db.execute(
                    select(CompanyProfile).where(CompanyProfile.id == company_uuid)
                )
                found = company_result2.scalar_one_or_none()
                if found:
                    company = found
            except (ValueError, AttributeError):
                pass
            
            threshold_web = 20
            if company and company.additional_data:
                sat = company.additional_data.get("saturation_settings", {})
                threshold_web = sat.get("threshold_web", 20)
            
            governance_rules = job.governance_rules or {}
            threshold_web = governance_rules.get("threshold_web", threshold_web)
            
            from sqlalchemy import and_, func, not_

            from lia_models.candidate import VacancyCandidate
            
            excluded = ('rejected', 'declined', 'withdrawn')
            organic_count_result = await self.db.execute(
                select(func.count(VacancyCandidate.id)).where(
                    and_(
                        VacancyCandidate.vacancy_id == conversation.job_vacancy_id,
                        not_(VacancyCandidate.status.in_(excluded)),
                        VacancyCandidate.origin.in_(('web', 'whatsapp', None)),
                    )
                )
            )
            organic_count = organic_count_result.scalar() or 0
            
            disabled_until_str = governance_rules.get("saturation_disabled_until")
            if disabled_until_str:
                try:
                    disabled_until = datetime.fromisoformat(disabled_until_str)
                    if disabled_until > datetime.utcnow():
                        return False
                except (ValueError, TypeError):
                    pass
            
            return organic_count >= threshold_web
            
        except Exception as e:
            logger.error(f"Error checking saturation: {e}", exc_info=True)
            return False
    
    async def _run_pre_qualification(
        self,
        conversation: WhatsAppConversation,
        job: JobVacancy | None
    ) -> Any | None:
        """Run pre-qualification evaluation using rubric service."""
        if not job or not conversation.cv_parsed_data:
            return None
        
        try:
            from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
            from lia_models.rubric import JobRequirement
            
            result = await self.db.execute(
                select(JobRequirement).where(JobRequirement.job_vacancy_id == job.id)
            )
            requirements = result.scalars().all()
            
            if not requirements:
                logger.info(f"No requirements found for job {job.id}, skipping pre-qualification")
                return None
            
            cv_data = conversation.cv_parsed_data
            cv_content = cv_data.get("raw_text", "") or cv_data.get("summary", "")
            
            if not cv_content:
                skills = cv_data.get("skills", []) or cv_data.get("technical_skills", [])
                experiences = cv_data.get("experiences", [])
                cv_content = f"Skills: {', '.join(skills)}\n"
                for exp in experiences[:3]:
                    if isinstance(exp, dict):
                        cv_content += f"Experience: {exp.get('title', '')} at {exp.get('company', '')}\n"
            
            evaluation = await rubric_evaluation_service.evaluate_candidate_cv(
                cv_content=cv_content,
                requirements=requirements,
                job_id=str(job.id)
            )
            
            matched = [
                {"requirement": e.requirement, "level": e.level.value}
                for e in evaluation.evaluations
                if e.level.value in ["EXCEEDS", "MEETS"]
            ]
            missing = [
                {"requirement": e.requirement, "level": e.level.value}
                for e in evaluation.evaluations
                if e.level.value == "MISSING"
            ]
            
            job_area = job.department if hasattr(job, 'department') and job.department else None
            
            pre_qual_output = pre_qualification_service.evaluate(
                adherence_score=evaluation.score,
                matched_requirements=matched,
                missing_requirements=missing,
                job_title=job.title,
                company_name=job.company_name or "a empresa",
                job_area=job_area
            )
            
            logger.info(
                f"Pre-qualification for conversation {conversation.id}: "
                f"score={evaluation.score:.1f}%, result={pre_qual_output.result.value}"
            )
            
            return pre_qual_output
            
        except Exception as e:
            logger.error(f"Error running pre-qualification: {e}", exc_info=True)
            return None
    
    async def _handle_pre_qualification_response(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle candidate response to pre-qualification message.
        
        Options:
        - Continuar: proceed to screening questions
        - Banco de talentos: add to talent pool and complete
        - Encerrar: decline and complete
        
        Supports both free-text responses and WhatsApp button payloads.
        Button IDs: prequal_continue, prequal_talent_pool, prequal_decline
        """
        normalized = message.strip().lower()
        
        continue_keywords = ["sim", "continuar", "quero", "prosseguir", "seguir", "ok", "vamos", "prequal_continue"]
        decline_keywords = ["não", "nao", "obrigado", "desisto", "parar", "prequal_decline", "encerrar"]
        talent_pool_keywords = ["banco", "talentos", "pool", "prequal_talent_pool", "notificar", "futuras"]
        
        job = await self._get_job(conversation.job_vacancy_id) if conversation.job_vacancy_id else None
        job_title = job.title if job else "a vaga"
        
        if any(word in normalized for word in continue_keywords):
            conversation.pre_qualification_decision = PreQualificationDecision.CONTINUE.value
            conversation.state = ConversationState.SCREENING
            conversation.current_question_index = 0
            await self.db.commit()
            
            questions = await self._get_screening_questions(conversation.job_vacancy_id)
            
            if questions:
                intro = "Ótimo! Vamos continuar com algumas perguntas para conhecer melhor sua experiência.\n\n"
                return intro + ConversationMessages.screening_question(1, questions[0])
            else:
                conversation.state = ConversationState.ADDITIONAL_INFO
                await self.db.commit()
                return ConversationMessages.additional_info_request()
        
        elif any(word in normalized for word in talent_pool_keywords):
            conversation.pre_qualification_decision = PreQualificationDecision.TALENT_POOL.value
            conversation.state = ConversationState.COMPLETED
            conversation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            await self._create_candidate_from_conversation(conversation)
            
            return (
                "Perfeito! Adicionei seu perfil ao nosso banco de talentos. ✅\n\n"
                "Quando surgirem vagas compatíveis com sua experiência, "
                "você será um dos primeiros a saber!\n\n"
                "Obrigada pelo interesse e boa sorte! 🍀"
            )
        
        elif any(word in normalized for word in decline_keywords):
            conversation.pre_qualification_decision = PreQualificationDecision.DECLINED.value
            conversation.state = ConversationState.COMPLETED
            conversation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return (
                f"Entendi! Obrigada pelo interesse na vaga de {job_title}.\n\n"
                f"Se mudar de ideia, estou por aqui! 🙏"
            )
        
        return (
            "Não entendi sua resposta. Por favor, escolha uma das opções:\n\n"
            "• *Continuar* - para seguir com a triagem\n"
            "• *Banco de talentos* - para ser notificado sobre vagas futuras\n"
            "• *Encerrar* - para finalizar"
        )
    
    async def _handle_screening_answer(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle screening question answer with eligibility verification."""
        questions_data = await self._get_screening_questions_with_metadata(conversation.job_vacancy_id)
        current_index = conversation.current_question_index or 0
        
        if current_index >= len(questions_data):
            return await self._complete_screening(conversation)
        
        current_question = questions_data[current_index]
        question_text = current_question.get("question", "")
        is_eliminatory = current_question.get("is_eliminatory", False)
        expected_answer = current_question.get("expected_answer")
        
        # Store answer
        answers = conversation.screening_answers or {}
        answers[f"q{current_index}"] = {
            "question": question_text,
            "answer": message,
            "answered_at": datetime.utcnow().isoformat(),
            "is_eliminatory": is_eliminatory,
            "expected_answer": expected_answer
        }
        conversation.screening_answers = answers
        
        # Check eliminatory question
        if is_eliminatory and expected_answer:
            # Create EligibilityQuestion object for the service
            question_obj = EligibilityQuestion(
                id=f"q{current_index}",
                question_text=question_text,
                question_type=current_question.get("type", "yes_no"),
                options=current_question.get("options"),
                is_eliminatory=True,
                expected_answer=expected_answer,
                category=current_question.get("category", "general")
            )
            
            result_status, result_message = eligibility_service.check_answer(
                question=question_obj,
                answer=message,
                reconsideration_count=conversation.reconsideration_count or 0
            )
            
            if result_status != ReconsiderationResult.PASSED:
                # Store eligibility answer for tracking
                eligibility_answers = conversation.eligibility_answers or {}
                eligibility_answers[f"q{current_index}"] = {
                    "question": question_text,
                    "answer": message,
                    "expected": expected_answer,
                    "passed": False,
                    "category": current_question.get("category", "general")
                }
                conversation.eligibility_answers = eligibility_answers
                conversation.eligibility_question_index = current_index
                
                if result_status == ReconsiderationResult.NEEDS_RECONSIDERATION:
                    # Offer reconsideration
                    conversation.state = ConversationState.WAITING_RECONSIDERATION
                    conversation.reconsideration_context = {
                        "question_index": current_index,
                        "original_answer": message,
                        "expected_answer": expected_answer,
                        "question_text": question_text,
                        "question_type": current_question.get("type", "yes_no"),
                        "category": current_question.get("category", "general")
                    }
                    await self.db.commit()
                    return result_message or "Por favor, confirme sua resposta."
                else:
                    # Max reconsiderations reached - redirect to talent pool
                    conversation.state = ConversationState.REDIRECTED_TALENT_POOL
                    conversation.had_reconsiderations = True
                    await self.db.commit()
                    return result_message or "Seu perfil foi adicionado ao nosso banco de talentos."
        
        # Continue to next question
        return await self._advance_to_next_question(conversation, questions_data)
    
    async def _advance_to_next_question(self, conversation: WhatsAppConversation, questions_data: list[dict]) -> str:
        """Advance to next screening question or complete screening."""
        current_index = conversation.current_question_index or 0
        next_index = current_index + 1
        
        if next_index < len(questions_data):
            conversation.current_question_index = next_index
            await self.db.commit()
            next_question = questions_data[next_index].get("question", "")
            return ConversationMessages.screening_question(next_index + 1, next_question)
        else:
            return await self._complete_screening(conversation)
    
    async def _complete_screening(self, conversation: WhatsAppConversation) -> str:
        """Complete screening and move to completion or additional info."""
        whatsapp = await self.get_provider(conversation.company_id)
        complete_msg = ConversationMessages.screening_complete()
        await whatsapp.send_text_message(conversation.phone_number, complete_msg)
        
        if conversation.candidate_email:
            conversation.state = ConversationState.COMPLETED
            conversation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            await self._create_candidate_from_conversation(conversation)
            
            job_title = "a vaga"
            if conversation.job_vacancy_id:
                job = await self._get_job(conversation.job_vacancy_id)
                if job:
                    job_title = job.title
            
            return ConversationMessages.completion_message(job_title)
        
        conversation.state = ConversationState.ADDITIONAL_INFO
        await self.db.commit()
        
        return ConversationMessages.additional_info_request()
    
    async def _handle_eligibility_check(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle eligibility check state - same as screening but focused on eliminatory."""
        return await self._handle_screening_answer(conversation, message)
    
    async def _handle_reconsideration_response(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle reconsideration response (candidate chooses to maintain or change answer)."""
        context = conversation.reconsideration_context or {}
        
        # Create ReconsiderationContext for the service
        recon_context = ReconsiderationContext(
            question_id=f"q{context.get('question_index', 0)}",
            original_answer=context.get("original_answer", ""),
            expected_answer=context.get("expected_answer", "Sim"),
            question_text=context.get("question_text", ""),
            attempt_count=conversation.reconsideration_count or 0
        )
        
        result_status, result_message = eligibility_service.process_reconsideration_response(
            response=message,
            context=recon_context
        )
        
        if result_status == ReconsiderationResult.KEPT_INCOMPATIBLE:
            # Candidate chose to keep answer (option 1) - redirect to talent pool
            conversation.state = ConversationState.REDIRECTED_TALENT_POOL
            conversation.had_reconsiderations = True
            await self.db.commit()
            return result_message or "Seu perfil foi adicionado ao nosso banco de talentos."
        
        elif result_status == ReconsiderationResult.RECONSIDERED_PASSED:
            # Candidate wants to reconsider (option 2) - ask for confirmation
            conversation.state = ConversationState.WAITING_CONFIRMATION
            conversation.reconsideration_count = (conversation.reconsideration_count or 0) + 1
            await self.db.commit()
            return result_message or "Por favor, confirme sua resposta."
        
        elif result_status == ReconsiderationResult.NEEDS_RECONSIDERATION:
            # Invalid response - return clarification message
            return result_message or "Por favor, responda *1* para manter sua resposta ou *2* para reconsiderar."
        
        # Fallback for any other status
        return "Por favor, responda *1* para manter sua resposta ou *2* para reconsiderar."
    
    async def _handle_confirmation_response(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle confirmation of reconsideration (candidate confirms new answer)."""
        context = conversation.reconsideration_context or {}
        question_index = context.get("question_index", 0)
        expected_answer = context.get("expected_answer", "sim")
        question_type = context.get("question_type", "yes_no")
        
        # Use process_confirmation_response from the service
        passed, talent_pool_message = eligibility_service.process_confirmation_response(
            response=message,
            expected_answer=expected_answer,
            question_type=question_type
        )
        
        if passed:
            # Update eligibility answer as passed
            eligibility_answers = conversation.eligibility_answers or {}
            if f"q{question_index}" in eligibility_answers:
                eligibility_answers[f"q{question_index}"]["passed"] = True
                eligibility_answers[f"q{question_index}"]["reconsidered"] = True
                eligibility_answers[f"q{question_index}"]["new_answer"] = message
            conversation.eligibility_answers = eligibility_answers
            
            # Continue with screening
            conversation.state = ConversationState.SCREENING
            conversation.reconsideration_context = None
            await self.db.commit()
            
            # Get questions and advance
            questions_data = await self._get_screening_questions_with_metadata(conversation.job_vacancy_id)
            return await self._advance_to_next_question(conversation, questions_data)
        
        else:
            # Answer still doesn't match expected
            reconsideration_count = conversation.reconsideration_count or 0
            
            if reconsideration_count >= 2:
                # Max reconsiderations reached - redirect to talent pool
                conversation.state = ConversationState.REDIRECTED_TALENT_POOL
                conversation.had_reconsiderations = True
                await self.db.commit()
                return talent_pool_message or "Seu perfil foi adicionado ao nosso banco de talentos."
            
            # Still can reconsider - go back to reconsideration state
            conversation.state = ConversationState.WAITING_RECONSIDERATION
            # Generate new warning message
            category = context.get("category", "default")
            warning_msg = eligibility_service._get_warning_message(
                category=category,
                original_answer=message,
                expected_answer=expected_answer,
                question_text=context.get("question_text", "")
            )
            await self.db.commit()
            return warning_msg
    
    async def _handle_additional_info(self, conversation: WhatsAppConversation, message: str) -> str:
        """Handle additional info collection (email)."""
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        
        if email_match:
            conversation.candidate_email = email_match.group(0)
            conversation.state = ConversationState.COMPLETED
            conversation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            await self._create_candidate_from_conversation(conversation)
            
            job_title = "a vaga"
            if conversation.job_vacancy_id:
                job = await self._get_job(conversation.job_vacancy_id)
                if job:
                    job_title = job.title
            
            return ConversationMessages.completion_message(job_title)
        
        return "Por favor, informe um email válido (ex: seu.email@exemplo.com)"
    
    async def send_feedback(
        self,
        conversation_id: UUID,
        approved: bool,
        recruiter_name: str | None = None
    ) -> bool:
        """Send feedback message to candidate after recruiter decision."""
        try:
            result = await self.db.execute(
                select(WhatsAppConversation).where(WhatsAppConversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return False
            
            job_title = "a vaga"
            if conversation.job_vacancy_id:
                job = await self._get_job(conversation.job_vacancy_id)
                if job:
                    job_title = job.title
            
            if approved:
                message = ConversationMessages.feedback_approved(job_title, recruiter_name or "o recrutador")
            else:
                message = ConversationMessages.feedback_rejected(job_title)
            
            whatsapp = await self.get_provider(conversation.company_id)
            result = await whatsapp.send_text_message(conversation.phone_number, message)
            
            if result.success:
                conversation.state = ConversationState.FEEDBACK_SENT
                await self._log_message(
                    conversation_id=conversation.id,
                    direction="outbound",
                    message_type="text",
                    content=message
                )
                await self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            try:
                await self.db.rollback()
            except Exception:
                pass
            logger.error(f"Error sending feedback: {e}", exc_info=True)
            return False
    
    async def _get_job_by_slug(self, slug: str) -> JobVacancy | None:
        """Get job vacancy by public slug."""
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def _get_job(self, job_id: UUID) -> JobVacancy | None:
        """Get job vacancy by ID."""
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_screening_questions(self, job_vacancy_id: UUID | None) -> list[str]:
        """
        Get screening questions for a job vacancy.
        
        Priority:
        1. Use job-specific screening_questions if configured (roteiro da vaga)
        2. Fallback to default questions
        
        Note: Não gera perguntas via LLM porque o candidato deve seguir
        o roteiro de triagem definido para a vaga.
        """
        default_questions = [
            "Qual sua pretensão salarial para esta posição?",
            "Qual sua disponibilidade para início caso seja aprovado?",
            "Você está participando de outros processos seletivos no momento?",
            "Qual seu nível de experiência na área?",
            "Por que você tem interesse nesta vaga?"
        ]
        
        if not job_vacancy_id:
            logger.info("[SCREENING] No job_vacancy_id, using default questions")
            return default_questions
        
        job = await self._get_job(job_vacancy_id)
        if not job:
            logger.info(f"[SCREENING] Job {job_vacancy_id} not found, using default questions")
            return default_questions
        
        # canonical-fix (Epico Elegibilidade Fase C, decisao Paulo #1): perguntas
        # de ELEGIBILIDADE (job.eligibility_questions) vem PRIMEIRO, como eliminatorias,
        # normalizadas pelo PRODUTOR UNICO. WhatsApp passa a ler o campo canonico
        # (antes lia apenas job.screening_questions e ignorava elegibilidade).
        eligibility_questions: list[dict[str, Any]] = []
        try:
            for _q in eligibility_service.get_eligibility_questions_from_job(
                {"eligibility_questions": getattr(job, "eligibility_questions", None) or []}
            ):
                if not _q.is_eliminatory:
                    continue
                eligibility_questions.append({
                    "question": _q.question_text,
                    "is_eliminatory": True,
                    "expected_answer": _q.expected_answer,
                    "category": _q.category,
                    "type": _q.question_type,
                    "options": _q.options,
                })
        except Exception as _exc:
            logger.warning(f"[SCREENING_META] eligibility load failed for {job_vacancy_id}: {_exc}")
        if job.screening_questions and len(job.screening_questions) > 0:
            questions = []
            for q in job.screening_questions:
                if isinstance(q, dict):
                    questions.append(q.get("question", str(q)))
                else:
                    questions.append(str(q))
            if questions:
                logger.info(f"[SCREENING] Using {len(questions)} job-configured questions for job {job_vacancy_id}")
                return questions
        
        logger.info(f"[SCREENING] No screening questions configured for job {job_vacancy_id}, using defaults")
        return default_questions
    
    async def _get_screening_questions_with_metadata(self, job_vacancy_id: UUID | None) -> list[dict[str, Any]]:
        """
        Get screening questions with full metadata including eligibility info.
        
        Returns list of dicts with:
        - question: str
        - is_eliminatory: bool
        - expected_answer: Optional[str]
        - category: Optional[str]
        - type: str (text, yes_no, multiple, scale)
        """
        default_questions = [
            {"question": "Qual sua pretensão salarial para esta posição?", "is_eliminatory": False, "type": "text"},
            {"question": "Qual sua disponibilidade para início caso seja aprovado?", "is_eliminatory": False, "type": "text"},
            {"question": "Você está participando de outros processos seletivos no momento?", "is_eliminatory": False, "type": "text"},
            {"question": "Qual seu nível de experiência na área?", "is_eliminatory": False, "type": "text"},
            {"question": "Por que você tem interesse nesta vaga?", "is_eliminatory": False, "type": "text"}
        ]
        
        if not job_vacancy_id:
            logger.info("[SCREENING_META] No job_vacancy_id, using default questions")
            return default_questions
        
        job = await self._get_job(job_vacancy_id)
        if not job:
            logger.info(f"[SCREENING_META] Job {job_vacancy_id} not found, using default questions")
            return default_questions
        
        if job.screening_questions and len(job.screening_questions) > 0:
            questions = []
            for q in job.screening_questions:
                if isinstance(q, dict):
                    questions.append({
                        "question": q.get("question", q.get("question_text", str(q))),
                        "is_eliminatory": q.get("is_eliminatory", False),
                        "expected_answer": q.get("expected_answer"),
                        "category": q.get("category", "general"),
                        "type": q.get("question_type", q.get("type", "text"))
                    })
                else:
                    questions.append({
                        "question": str(q),
                        "is_eliminatory": False,
                        "type": "text"
                    })
            if questions:
                eliminatory_count = sum(1 for q in questions if q.get("is_eliminatory"))
                logger.info(f"[SCREENING_META] Using {len(questions)} questions ({eliminatory_count} eliminatory) for job {job_vacancy_id}")
                return eligibility_questions + questions
        
        logger.info(f"[SCREENING_META] No screening questions configured for job {job_vacancy_id}, using defaults")
        if eligibility_questions:
            return eligibility_questions + default_questions
        return default_questions
    
    async def _parse_cv(self, media_data: dict[str, Any], company_id: str | None = None) -> dict[str, Any]:
        """
        Parse CV using CVParserService with real AI parsing.
        
        Downloads media from WhatsApp provider and uses CVParserService
        for intelligent CV extraction.
        
        Args:
            media_data: Dict containing media info from WhatsApp webhook
                       - For Meta: contains 'id' (media_id)
                       - For Twilio: contains 'url' (direct URL)
            company_id: Company ID for provider selection
            
        Returns:
            Dict with success status and parsed data or error
        """
        try:
            from fastapi import UploadFile

            from app.domains.cv_screening.services.cv_parser import CVParserService
            
            media_id = media_data.get("id")
            media_url = media_data.get("url")
            
            if not media_id and not media_url:
                logger.error("[CV PARSE] No media ID or URL in media_data")
                return {"success": False, "error": "Não foi possível localizar o arquivo"}
            
            provider = await self.get_provider(company_id)
            
            media_identifier = media_id or media_url
            logger.info(f"[CV PARSE] Downloading media: {media_identifier[:50] if media_identifier else 'unknown'}...")
            
            download_result = await provider.download_media(media_identifier)
            
            if not download_result.get("success"):
                error_msg = download_result.get("error", "Download failed")
                logger.error(f"[CV PARSE] Media download failed: {error_msg}")
                return {"success": False, "error": f"Erro ao baixar o arquivo: {error_msg}"}
            
            content = download_result.get("content")
            mime_type = download_result.get("mime_type", "application/octet-stream")
            
            if not content:
                logger.error("[CV PARSE] No content in download result")
                return {"success": False, "error": "Arquivo vazio ou corrompido"}
            
            filename = media_data.get("filename", "cv_whatsapp")
            if not filename.endswith(('.pdf', '.docx', '.doc', '.txt')):
                if "pdf" in mime_type:
                    filename += ".pdf"
                elif "wordprocessingml" in mime_type or "msword" in mime_type:
                    filename += ".docx"
                else:
                    filename += ".pdf"
            
            file_like = io.BytesIO(content)
            file_like.seek(0)
            
            pseudo_file = UploadFile(
                file=file_like,
                filename=filename,
                size=len(content),
            )
            pseudo_file.content_type = mime_type
            
            cv_parser = CVParserService()
            logger.info(f"[CV PARSE] Starting AI parsing for {filename} ({len(content)} bytes)")
            
            parsed_cv = await cv_parser.parse_cv(pseudo_file)
            
            logger.info("[CV PARSE] Successfully parsed CV (candidate data extracted)")
            
            experiences_summary = None
            if parsed_cv.experiences:
                total_years = 0
                for exp in parsed_cv.experiences:
                    if exp.start_date:
                        try:
                            start_year = int(exp.start_date.split()[-1]) if exp.start_date else datetime.now().year
                            end_year = datetime.now().year if exp.is_current else (int(exp.end_date.split()[-1]) if exp.end_date else datetime.now().year)
                            total_years += max(0, end_year - start_year)
                        except (ValueError, AttributeError):
                            pass
                experiences_summary = total_years if total_years > 0 else None
            
            education_summary = None
            if parsed_cv.education:
                latest_edu = parsed_cv.education[0]
                education_summary = f"{latest_edu.degree} em {latest_edu.field_of_study}" if latest_edu.field_of_study else latest_edu.degree
            
            return {
                "success": True,
                "data": {
                    "name": parsed_cv.full_name,
                    "email": parsed_cv.email,
                    "phone": parsed_cv.phone,
                    "linkedin": parsed_cv.linkedin,
                    "github": parsed_cv.github,
                    "location": parsed_cv.location,
                    "summary": parsed_cv.summary,
                    "experience_years": experiences_summary,
                    "current_position": parsed_cv.current_title,
                    "current_company": parsed_cv.experiences[0].company if parsed_cv.experiences else None,
                    "skills": parsed_cv.skills[:10] if parsed_cv.skills else [],
                    "soft_skills": parsed_cv.soft_skills[:5] if parsed_cv.soft_skills else [],
                    "education": education_summary,
                    "languages": parsed_cv.languages,
                    "certifications": parsed_cv.certifications,
                    "seniority_level": parsed_cv.seniority_level,
                    "confidence_score": parsed_cv.confidence_score,
                    "raw_experiences": [
                        {
                            "company": exp.company,
                            "title": exp.title,
                            "start_date": exp.start_date,
                            "end_date": exp.end_date,
                            "is_current": exp.is_current,
                            "description": exp.description
                        } for exp in (parsed_cv.experiences or [])
                    ],
                    "raw_education": [
                        {
                            "institution": edu.institution,
                            "degree": edu.degree,
                            "field_of_study": edu.field_of_study,
                            "end_date": edu.end_date
                        } for edu in (parsed_cv.education or [])
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"[CV PARSE] CV parsing failed: {e}", exc_info=True)
            return {
                "success": False, 
                "error": str(e),
                "user_message": "Tive dificuldade em analisar seu currículo. Por favor, tente enviar novamente em formato PDF ou Word."
            }
    
    def _format_cv_summary(self, cv_data: dict[str, Any]) -> str:
        """Format CV data as summary text."""
        lines = []
        
        if cv_data.get("experience_years"):
            lines.append(f"• Experiência: {cv_data['experience_years']} anos")
        
        if cv_data.get("current_position"):
            company = cv_data.get("current_company", "")
            if company:
                lines.append(f"• Última posição: {cv_data['current_position']} na {company}")
            else:
                lines.append(f"• Última posição: {cv_data['current_position']}")
        
        if cv_data.get("skills"):
            skills = cv_data["skills"][:5]
            lines.append(f"• Principais skills: {', '.join(skills)}")
        
        if cv_data.get("education"):
            lines.append(f"• Formação: {cv_data['education']}")
        
        return "\n".join(lines) if lines else "Dados extraídos do currículo"
    
    async def _create_candidate_from_conversation(self, conversation: WhatsAppConversation, status: str = "cv_received") -> None:
        """
        Create a candidate record from completed conversation.
        
        This method:
        1. Creates a Candidate record with parsed CV data
        2. Creates a CandidateJob record (legacy compatibility)
        3. Creates a VacancyCandidate record for pipeline integration (origin="whatsapp")
        4. Dispatches CANDIDATE_APPLIED automation event
        
        Args:
            conversation: The WhatsApp conversation
            status: VacancyCandidate status (cv_received, awaiting_screening, rejected)
        """
        try:
            from app.domains.automation.services.stage_automation_engine import (
                AutomationEvent,
                StageAutomationEngine,
                TriggerType,
            )
            from lia_models.candidate import Candidate, VacancyCandidate
            from lia_models.candidate_job import CandidateJob
            
            cv_data = conversation.cv_parsed_data or {}
            
            screening_completed = status not in ("awaiting_screening", "rejected")
            
            candidate = Candidate(
                company_id=conversation.company_id,
                name=conversation.candidate_name or cv_data.get("name", "Candidato"),
                email=conversation.candidate_email or cv_data.get("email"),
                phone=conversation.phone_number,
                linkedin_url=conversation.candidate_linkedin or cv_data.get("linkedin"),
                source="whatsapp_lia",
                status="Novo" if status != "rejected" else "Rejeitado",
                current_title=cv_data.get("current_position"),
                current_company=cv_data.get("current_company"),
                seniority_level=cv_data.get("seniority_level"),
                years_of_experience=cv_data.get("experience_years"),
                technical_skills=cv_data.get("skills", []),
                soft_skills=cv_data.get("soft_skills", []),
                languages=cv_data.get("languages", {}),
                certifications=cv_data.get("certifications", []),
                additional_data={
                    "whatsapp_conversation_id": str(conversation.id),
                    "cv_parsed_data": cv_data,
                    "screening_answers": conversation.screening_answers,
                    "applied_via": "whatsapp",
                    "applied_at": datetime.utcnow().isoformat(),
                    "pre_qualification_score": conversation.pre_qualification_score,
                    "pre_qualification_result": conversation.pre_qualification_result,
                }
            )
            
            self.db.add(candidate)
            await self.db.flush()
            
            conversation.candidate_id = candidate.id
            
            stage = "screening" if status not in ("awaiting_screening", "rejected") else "applied"
            
            vacancy_candidate = None
            if conversation.job_vacancy_id:
                candidate_job = CandidateJob(
                    candidate_id=candidate.id,
                    job_vacancy_id=conversation.job_vacancy_id,
                    status="Novo" if status != "rejected" else "Rejeitado",
                    applied_at=datetime.utcnow(),
                    source="whatsapp_lia"
                )
                self.db.add(candidate_job)
                
                from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
                vc_stage_id = await resolve_recruitment_stage_id(
                    self.db, str(conversation.company_id), stage
                )
                vacancy_candidate = VacancyCandidate(
                    vacancy_id=conversation.job_vacancy_id,
                    candidate_id=candidate.id,
                    company_id=conversation.company_id,
                    source="whatsapp_lia",
                    origin="whatsapp",
                    stage=stage,
                    recruitment_stage_id=vc_stage_id,
                    status=status,
                    added_by="whatsapp_lia",
                    notes="Candidatura realizada via WhatsApp",
                    additional_data={
                        "whatsapp_conversation_id": str(conversation.id),
                        "cv_parsed": True,
                        "screening_completed": screening_completed,
                        "screening_answers": conversation.screening_answers,
                        "pre_qualification_score": conversation.pre_qualification_score,
                    }
                )
                self.db.add(vacancy_candidate)
                await self.db.flush()
            
            await self.db.commit()
            logger.info(f"Created candidate {candidate.id} from WhatsApp conversation {conversation.id}")
            
            if conversation.job_vacancy_id and vacancy_candidate:
                try:
                    engine = StageAutomationEngine()
                    event = AutomationEvent(
                        trigger_type=TriggerType.CANDIDATE_APPLIED,
                        candidate_id=str(candidate.id),
                        vacancy_id=str(conversation.job_vacancy_id),
                        company_id=conversation.company_id,
                        payload={
                            "source": "whatsapp",
                            "cv_parsed": True,
                            "screening_completed": True,
                            "screening_answers": conversation.screening_answers,
                            "vacancy_candidate_id": str(vacancy_candidate.id),
                            "candidate_name": candidate.name,
                            "candidate_email": candidate.email
                        },
                        source="whatsapp_lia"
                    )
                    result = await engine.process_event(event, self.db)
                    logger.info(f"CANDIDATE_APPLIED event processed for candidate {candidate.id}: {result}")
                except Exception as automation_error:
                    logger.warning(f"Failed to dispatch automation event (non-blocking): {automation_error}")
            
        except Exception as e:
            logger.error(f"Error creating candidate from conversation: {e}", exc_info=True)
            await self.db.rollback()
    
    async def _log_message(
        self,
        conversation_id: UUID,
        direction: str,
        message_type: str,
        content: str,
        media_data: dict[str, Any] | None = None
    ) -> None:
        """Log a message to the conversation history."""
        try:
            message = WhatsAppMessage(
                conversation_id=conversation_id,
                direction=direction,
                message_type=message_type,
                content=content,
                media_data=media_data,
                created_at=datetime.utcnow()
            )
            self.db.add(message)
            await self.db.flush()
        except Exception as e:
            logger.error(f"Error logging message: {e}")
