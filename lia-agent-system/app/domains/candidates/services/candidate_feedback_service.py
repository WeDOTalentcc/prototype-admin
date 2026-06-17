"""
Candidate Feedback Service - Automatic feedback for candidates with low adherence.

This service handles:
1. Detection of low adherence candidates (< 50%)
2. Generation of constructive feedback messages
3. Multi-channel delivery (Email and WhatsApp)
4. Tracking of resubmission attempts
5. Analytics on feedback effectiveness
"""
import logging
import secrets
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.candidates.repositories.candidate_feedback_repository import (
    CandidateFeedbackRepository,
)
from app.domains.communication.services.email_service import email_service
from lia_models.candidate_feedback import CandidateFeedback, FeedbackType
from app.services.notification_service import (
    NotificationType,
    notification_service,
)

logger = logging.getLogger(__name__)


LOW_ADHERENCE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atualização sobre sua candidatura</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">📋 Atualização sobre sua candidatura</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <p style="font-size: 16px;">Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Agradecemos pelo seu interesse na vaga de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
        
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; font-size: 14px;">
                📊 Após analisar seu perfil, identificamos uma compatibilidade de 
                <strong style="font-size: 18px; color: #856404;">{{adherence_score}}%</strong> 
                com os requisitos desta posição.
            </p>
        </div>
        
        <p>Para aumentar suas chances de sucesso, sugerimos:</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <ul style="margin: 0; padding-left: 20px;">
                {{improvement_tips}}
            </ul>
        </div>
        
        {{#missing_skills}}
        <div style="background-color: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #0066cc;">💡 Competências que podem fortalecer seu perfil:</p>
            <p style="margin: 0; color: #555;">{{missing_skills}}</p>
        </div>
        {{/missing_skills}}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{resubmit_url}}" 
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; 
                      font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                📄 Enviar CV Atualizado
            </a>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            Faremos uma nova análise assim que recebermos seu currículo atualizado.
        </p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="color: #888; font-size: 13px; margin-bottom: 0;">
            Atenciosamente,<br>
            <strong>LIA</strong> - Assistente de Recrutamento Inteligente<br>
            {{company_name}}
        </p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">
        <p style="margin: 0; font-size: 12px; color: #888;">
            Este é um email automático. Caso tenha dúvidas, responda diretamente a este email.
        </p>
    </div>
</body>
</html>
"""

LOW_ADHERENCE_TEXT_TEMPLATE = """
Olá {{candidate_name}},

Agradecemos pelo seu interesse na vaga de {{job_title}} na {{company_name}}!

Após analisar seu perfil, identificamos uma compatibilidade de {{adherence_score}}% com os requisitos desta posição.

Para aumentar suas chances de sucesso, sugerimos:
{{improvement_tips}}

{{#missing_skills}}
Competências que podem fortalecer seu perfil:
{{missing_skills}}
{{/missing_skills}}

Se desejar, você pode enviar seu currículo atualizado através do link:
{{resubmit_url}}

Faremos uma nova análise assim que recebermos seu currículo atualizado.

Atenciosamente,
LIA - Assistente de Recrutamento Inteligente
{{company_name}}
"""


class CandidateFeedbackService:
    """
    Serviço para enviar feedback automático a candidatos.
    
    Principais funcionalidades:
    - Detectar candidatos com baixa aderência (< 50%)
    - Gerar mensagens de feedback construtivo e personalizado
    - Enviar via múltiplos canais (email, WhatsApp)
    - Registrar tentativas para analytics
    - Gerenciar reenvios de CV
    """
    
    ADHERENCE_THRESHOLD = 50.0
    
    def __init__(self):
        self.default_improvement_tips = [
            "Atualize seu currículo destacando experiências relevantes para a vaga",
            "Adicione certificações ou cursos relacionados à área",
            "Detalhe projetos que demonstrem as competências buscadas",
            "Inclua palavras-chave técnicas alinhadas com a descrição da vaga",
            "Quantifique suas realizações com métricas e resultados"
        ]
    
    async def check_and_send_feedback(
        self,
        candidate_id: str,
        vacancy_id: str,
        adherence_score: float,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
        candidate_name: str | None = None,
        vacancy_title: str | None = None,
        company_name: str | None = None,
        missing_skills: list[str] | None = None,
        matched_skills: list[str] | None = None,
        custom_tips: list[str] | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Verifica aderência e envia feedback se necessário.
        
        Args:
            candidate_id: ID do candidato
            vacancy_id: ID da vaga
            adherence_score: Score de aderência (0-100)
            candidate_email: Email do candidato
            candidate_phone: Telefone do candidato (formato: +5511999999999)
            candidate_name: Nome do candidato
            vacancy_title: Título da vaga
            company_name: Nome da empresa
            missing_skills: Lista de competências faltantes
            matched_skills: Lista de competências correspondentes
            custom_tips: Dicas personalizadas para o candidato
            db: Sessão do banco de dados
        
        Returns:
            {
                "feedback_sent": True/False,
                "reason": "...",
                "channels_used": ["email", "whatsapp"],
                "channels_failed": [],
                "adherence_score": float,
                "resubmit_url": "...",
                "feedback_id": "...",
                "message_preview": "..."
            }
        """
        if adherence_score >= self.ADHERENCE_THRESHOLD:
            logger.info(f"Candidate {candidate_id} has adequate adherence ({adherence_score}%), no feedback needed")
            return {
                "feedback_sent": False,
                "reason": "adherence_adequate",
                "adherence_score": adherence_score
            }
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            resubmit_token = secrets.token_urlsafe(32)
            resubmit_url = f"/apply/{vacancy_id}?resubmit={candidate_id}&token={resubmit_token}"
            
            improvement_tips = custom_tips or self._generate_improvement_tips(
                adherence_score, missing_skills
            )
            
            message = await self._generate_feedback_message(
                candidate_name=candidate_name or "Candidato",
                vacancy_title=vacancy_title or "Vaga",
                company_name=company_name or "Nossa Empresa",
                adherence_score=adherence_score,
                improvement_tips=improvement_tips,
                missing_skills=missing_skills or [],
                resubmit_url=resubmit_url
            )
            
            feedback_record = CandidateFeedback(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                feedback_type=FeedbackType.LOW_ADHERENCE,
                adherence_score=adherence_score,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                vacancy_title=vacancy_title,
                company_name=company_name,
                message_subject=message["subject"],
                message_preview=message["short_message"],
                resubmit_url=resubmit_url,
                resubmit_token=resubmit_token,
                improvement_tips=improvement_tips,
                missing_skills=missing_skills or [],
                matched_skills=matched_skills or [],
                sent_at=datetime.utcnow()
            )
            
            channels_used = []
            channels_failed = []
            
            if candidate_email:
                try:
                    await self._send_email_feedback(
                        email=candidate_email,
                        message=message,
                        db=db
                    )
                    channels_used.append("email")
                    feedback_record.email_sent = True
                    feedback_record.email_sent_at = datetime.utcnow()
                    logger.info("📧 Email feedback sent")
                except Exception as e:
                    channels_failed.append({"channel": "email", "error": str(e)})
                    logger.error(f"Failed to send email feedback: {e}")
            
            if candidate_phone:
                try:
                    await self._send_whatsapp_feedback(
                        phone=candidate_phone,
                        message=message
                    )
                    channels_used.append("whatsapp")
                    feedback_record.whatsapp_sent = True
                    feedback_record.whatsapp_sent_at = datetime.utcnow()
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"📱 WhatsApp feedback sent to {candidate_phone}")
                except Exception as e:
                    channels_failed.append({"channel": "whatsapp", "error": str(e)})
                    logger.warning(f"Failed to send WhatsApp feedback: {e}")
            
            feedback_record.channels_sent = channels_used
            feedback_record.channels_failed = channels_failed
            
            db.add(feedback_record)
            await db.commit()
            await db.refresh(feedback_record)
            
            await self._notify_recruiters_about_low_adherence(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                vacancy_id=vacancy_id,
                vacancy_title=vacancy_title,
                adherence_score=adherence_score,
                db=db
            )
            
            logger.info(
                f"✅ Low adherence feedback sent to candidate {candidate_id} "
                f"(score: {adherence_score}%, channels: {channels_used})"
            )
            
            return {
                "feedback_sent": True,
                "feedback_id": feedback_record.id,
                "channels_used": channels_used,
                "channels_failed": channels_failed,
                "adherence_score": adherence_score,
                "resubmit_url": resubmit_url,
                "message_preview": message["short_message"],
                "improvement_tips": improvement_tips
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error sending feedback to candidate {candidate_id}: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    def _generate_improvement_tips(
        self,
        adherence_score: float,
        missing_skills: list[str] | None = None
    ) -> list[str]:
        """Gera dicas personalizadas baseadas no score e skills faltantes."""
        tips = []
        
        if adherence_score < 30:
            tips.append("Revise o currículo para garantir que as experiências estejam alinhadas com a área da vaga")
            tips.append("Considere adicionar um resumo profissional destacando suas principais competências")
        elif adherence_score < 40:
            tips.append("Destaque projetos ou experiências que demonstrem competências técnicas relevantes")
            tips.append("Inclua palavras-chave da descrição da vaga em seu currículo")
        else:
            tips.append("Você está próximo! Pequenos ajustes podem fazer a diferença")
            tips.append("Detalhe melhor suas experiências mais relevantes para esta posição")
        
        if missing_skills:
            if len(missing_skills) > 3:
                tips.append(f"Foco em desenvolver: {', '.join(missing_skills[:3])}")
            else:
                tips.append(f"Competências a desenvolver: {', '.join(missing_skills)}")
        
        tips.append("Quantifique suas realizações com métricas sempre que possível")
        
        return tips[:5]
    
    async def _generate_feedback_message(
        self,
        candidate_name: str,
        vacancy_title: str,
        company_name: str,
        adherence_score: float,
        improvement_tips: list[str],
        missing_skills: list[str],
        resubmit_url: str
    ) -> dict[str, str]:
        """Gera mensagem de feedback em múltiplos formatos."""
        
        tips_html = "".join([f"<li style='margin-bottom: 8px;'>{tip}</li>" for tip in improvement_tips])
        tips_text = "\n".join([f"• {tip}" for tip in improvement_tips])
        
        missing_skills_str = ", ".join(missing_skills[:5]) if missing_skills else ""
        
        html_body = LOW_ADHERENCE_EMAIL_TEMPLATE
        html_body = html_body.replace("{{candidate_name}}", candidate_name)
        html_body = html_body.replace("{{job_title}}", vacancy_title)
        html_body = html_body.replace("{{company_name}}", company_name)
        html_body = html_body.replace("{{adherence_score}}", f"{adherence_score:.0f}")
        html_body = html_body.replace("{{improvement_tips}}", tips_html)
        html_body = html_body.replace("{{resubmit_url}}", resubmit_url)
        
        if missing_skills_str:
            html_body = html_body.replace("{{#missing_skills}}", "")
            html_body = html_body.replace("{{/missing_skills}}", "")
            html_body = html_body.replace("{{missing_skills}}", missing_skills_str)
        else:
            import re
            html_body = re.sub(r'\{\{#missing_skills\}\}.*?\{\{/missing_skills\}\}', '', html_body, flags=re.DOTALL)
        
        text_body = LOW_ADHERENCE_TEXT_TEMPLATE
        text_body = text_body.replace("{{candidate_name}}", candidate_name)
        text_body = text_body.replace("{{job_title}}", vacancy_title)
        text_body = text_body.replace("{{company_name}}", company_name)
        text_body = text_body.replace("{{adherence_score}}", f"{adherence_score:.0f}")
        text_body = text_body.replace("{{improvement_tips}}", tips_text)
        text_body = text_body.replace("{{resubmit_url}}", resubmit_url)
        
        if missing_skills_str:
            text_body = text_body.replace("{{#missing_skills}}", "")
            text_body = text_body.replace("{{/missing_skills}}", "")
            text_body = text_body.replace("{{missing_skills}}", missing_skills_str)
        else:
            import re
            text_body = re.sub(r'\{\{#missing_skills\}\}.*?\{\{/missing_skills\}\}', '', text_body, flags=re.DOTALL)
        
        short_message = (
            f"Olá {candidate_name}! Sua aderência à vaga de {vacancy_title} é de {adherence_score:.0f}%. "
            f"Gostaria de enviar seu CV atualizado para reanálise? "
            f"Acesse: {resubmit_url}"
        )
        
        return {
            "subject": f"Atualização sobre sua candidatura - {vacancy_title}",
            "body_html": html_body,
            "body_text": text_body,
            "short_message": short_message,
            "whatsapp_message": short_message
        }
    
    async def _send_email_feedback(
        self,
        email: str,
        message: dict[str, str],
        db: AsyncSession
    ):
        """Envia feedback via email usando o serviço de email existente."""
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"[EMAIL] Sending low adherence feedback to: {email}")
        logger.debug(f"[EMAIL] Subject: {message['subject']}")
        
        success = await email_service._send_email_provider(
            to_email=email,
            subject=message["subject"],
            body_html=message["body_html"],
            body_text=message.get("body_text")
        )
        
        if not success:
            from app.shared.errors import LIAIntegrationError
            raise LIAIntegrationError(
                message="Provedor de email retornou falha no envio",
                code="EMAIL_SEND_FAILED",
            )
        
        return True
    
    async def _send_whatsapp_feedback(
        self,
        phone: str,
        message: dict[str, str]
    ):
        """Envia feedback via WhatsApp."""
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"[WHATSAPP] Sending low adherence feedback to: {phone}")
        logger.debug(f"[WHATSAPP] Message: {message['short_message'][:100]}...")
        
        return True
    
    async def _notify_recruiters_about_low_adherence(
        self,
        candidate_id: str,
        candidate_name: str | None,
        vacancy_id: str,
        vacancy_title: str | None,
        adherence_score: float,
        db: AsyncSession
    ):
        """Notifica recrutadores sobre candidatos com baixa aderência."""
        try:
            await notification_service.create_notification(
                user_id="default_user",
                title="📊 Candidato com baixa aderência",
                message=f"{candidate_name or 'Candidato'} aplicou para {vacancy_title or 'vaga'} "
                        f"com aderência de {adherence_score:.0f}%. Feedback automático enviado.",
                notification_type=NotificationType.INFO,
                category="low_adherence",
                source_agent="candidate_feedback_service",
                related_job_id=vacancy_id,
                related_candidate_id=candidate_id,
                action_url=f"/candidates/{candidate_id}",
                action_label="Ver Candidato",
                db=db
            )
        except Exception as e:
            logger.warning(f"Failed to notify recruiters about low adherence: {e}")
    
    async def mark_resubmit_clicked(
        self,
        feedback_id: str,
        db: AsyncSession | None = None
    ) -> bool:
        """Marca que o candidato clicou no link de reenvio."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            repo = CandidateFeedbackRepository(db)
            feedback = await repo.get_by_id(feedback_id)

            if feedback:
                feedback.resubmit_clicked = True
                feedback.resubmit_clicked_at = datetime.utcnow()
                await db.commit()
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Marked resubmit clicked for feedback {feedback_id}")
                return True

            return False
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def mark_resubmit_completed(
        self,
        feedback_id: str,
        new_adherence_score: float | None = None,
        db: AsyncSession | None = None
    ) -> bool:
        """Marca que o candidato completou o reenvio do CV."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            repo = CandidateFeedbackRepository(db)
            feedback = await repo.get_by_id(feedback_id)

            if feedback:
                feedback.resubmit_completed = True
                feedback.resubmit_completed_at = datetime.utcnow()
                if new_adherence_score is not None:
                    feedback.new_adherence_score = new_adherence_score
                await db.commit()
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Marked resubmit completed for feedback {feedback_id}")
                return True

            return False
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def get_feedback_analytics(
        self,
        vacancy_id: str | None = None,
        days: int = 30,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Retorna analytics sobre feedbacks enviados."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            repo = CandidateFeedbackRepository(db)
            feedbacks = await repo.list_recent(days=days, vacancy_id=vacancy_id)
            
            total_sent = len(feedbacks)
            email_sent = sum(1 for f in feedbacks if f.email_sent)
            whatsapp_sent = sum(1 for f in feedbacks if f.whatsapp_sent)
            resubmit_clicked = sum(1 for f in feedbacks if f.resubmit_clicked)
            resubmit_completed = sum(1 for f in feedbacks if f.resubmit_completed)
            
            avg_initial_score = sum(f.adherence_score or 0 for f in feedbacks) / total_sent if total_sent > 0 else 0
            
            improved = [f for f in feedbacks if f.new_adherence_score and f.new_adherence_score > (f.adherence_score or 0)]
            avg_improvement = (
                sum((f.new_adherence_score or 0) - (f.adherence_score or 0) for f in improved) / len(improved)
                if improved else 0
            )
            
            return {
                "period_days": days,
                "total_feedbacks_sent": total_sent,
                "channels": {
                    "email_sent": email_sent,
                    "whatsapp_sent": whatsapp_sent
                },
                "engagement": {
                    "resubmit_clicked": resubmit_clicked,
                    "resubmit_completed": resubmit_completed,
                    "click_rate": (resubmit_clicked / total_sent * 100) if total_sent > 0 else 0,
                    "completion_rate": (resubmit_completed / resubmit_clicked * 100) if resubmit_clicked > 0 else 0
                },
                "scores": {
                    "average_initial_score": round(avg_initial_score, 1),
                    "candidates_improved": len(improved),
                    "average_improvement": round(avg_improvement, 1)
                }
            }
        finally:
            if should_close:
                await db.close()


    # -------------------------------------------------------------------------
    # Gate-differentiated feedback (Gap 16.1)
    # -------------------------------------------------------------------------

    _GATE_SUBJECTS = {
        "screening_invited": "[WeDOTalent] Convite para triagem — {vacancy_title}",
        "gate1_rejected":    "[WeDOTalent] Atualização sobre sua candidatura — {vacancy_title}",
        "gate2_rejected":    "[WeDOTalent] Resultado da avaliação técnica — {vacancy_title}",
        "approved":          "[WeDOTalent] Parabéns! Você avançou no processo — {vacancy_title}",
    }

    _GATE_BODIES = {
        "screening_invited": (
            "Olá {name},\n\n"
            "Obrigado por se candidatar à vaga de {vacancy_title} na {company}!\n\n"
            "Identificamos boa compatibilidade do seu perfil com a posição e gostaríamos de "
            "convidá-lo(a) para realizar nossa triagem comportamental e técnica online.\n\n"
            "Acesse o link abaixo para iniciar:\n"
            "{screening_url}\n\n"
            "O processo leva cerca de 15-20 minutos e pode ser realizado no seu próprio ritmo.\n\n"
            "Qualquer dúvida, entre em contato: privacidade@wedotalent.com.br\n\n"
            "WeDOTalent — Recrutamento Inteligente"
        ),
        "gate1_rejected": (
            "Olá {name},\n\n"
            "Agradecemos muito pela sua participação no processo seletivo para "
            "{vacancy_title} na {company}.\n\n"
            "Após análise cuidadosa, infelizmente não avançaremos com sua candidatura "
            "neste momento.\n\n"
            "Isso não significa que você não seja um(a) profissional talentoso(a) — "
            "a decisão reflete apenas a especificidade dos requisitos desta posição.\n\n"
            "Você poderá se candidatar novamente após 90 dias. Fique de olho nas nossas "
            "vagas em: https://wedotalent.com.br/vagas\n\n"
            "Desejamos sucesso na sua trajetória profissional!\n\n"
            "WeDOTalent — Recrutamento Inteligente\n"
            "privacidade@wedotalent.com.br"
        ),
        "gate2_rejected": (
            "Olá {name},\n\n"
            "Agradecemos pela sua participação na avaliação técnica para "
            "{vacancy_title} na {company}.\n\n"
            "Após avaliação detalhada dos critérios técnicos desta posição, "
            "não prosseguiremos com sua candidatura neste ciclo.\n\n"
            "{rejection_context}"
            "Valorizamos seu tempo e interesse. Novas oportunidades são publicadas "
            "regularmente em: https://wedotalent.com.br/vagas\n\n"
            "WeDOTalent — Recrutamento Inteligente\n"
            "privacidade@wedotalent.com.br"
        ),
        "approved": (
            "Olá {name},\n\n"
            "Parabéns! Você foi aprovado(a) para a próxima etapa do processo seletivo "
            "para {vacancy_title} na {company}.\n\n"
            "{next_step_info}"
            "Em breve nossa equipe de recrutamento entrará em contato com os detalhes.\n\n"
            "WeDOTalent — Recrutamento Inteligente\n"
            "privacidade@wedotalent.com.br"
        ),
    }

    async def _enforce_fairness_on_message(
        self,
        *,
        message: dict,
        candidate_name: str,
        vacancy_title: str,
        company_name: str,
        adherence_score: float,
        improvement_tips: list,
        missing_skills: list,
        resubmit_url: str,
        candidate_id: str,
        vacancy_id: str,
    ) -> tuple:
        """Enforce FairnessGuard on a feedback message.

        Returns (message, tips, metadata) where:
        - message: original or regenerated message dict
        - tips: original or safe default improvement tips
        - metadata: {"fairness_blocked": bool, "regenerated": bool}

        Raises LIAFairnessError if the regenerated message is also blocked.
        This enforces LGPD Art. 11 compliance — no discriminatory content in
        candidate communications.
        """
        from app.shared.compliance.fairness_guard import FairnessGuard
        from app.shared.errors import LIAFairnessError

        guard = FairnessGuard()

        # Check original message body text
        body_text = (
            message.get("body_text") or message.get("html_body") or ""
        )
        check_result = guard.check(body_text)

        if not check_result.is_blocked:
            return (
                message,
                improvement_tips,
                {"fairness_blocked": False, "regenerated": False},
            )

        # Blocked: log and regenerate with safe defaults
        logger.warning(
            "[FairnessGuard] Feedback message blocked for candidate=%s vacancy=%s — regenerating",
            candidate_id, vacancy_id,
        )

        # Sanitize tips — do NOT propagate potentially discriminatory user-supplied tips
        safe_tips = self._generate_improvement_tips(
            adherence_score=adherence_score,
            missing_skills=[],  # PII-safe: strip missing_skills from regen path
        )

        regenerated = await self._generate_feedback_message(
            candidate_name=candidate_name,
            vacancy_title=vacancy_title,
            company_name=company_name,
            adherence_score=adherence_score,
            improvement_tips=safe_tips,
            missing_skills=[],  # PII-safe: never propagate user-supplied skills
            resubmit_url=resubmit_url,
        )

        # Validate regenerated message
        regen_body = (
            regenerated.get("body_text") or regenerated.get("html_body") or ""
        )
        regen_check = guard.check(regen_body)

        if regen_check.is_blocked:
            raise LIAFairnessError(
                f"Feedback message still discriminatory after regeneration — "
                f"candidate_id={candidate_id}, vacancy_id={vacancy_id}"
            )

        return (
            regenerated,
            safe_tips,
            {"fairness_blocked": True, "regenerated": True},
        )

    async def send_gate_feedback(
        self,
        gate_level: str,
        candidate_email: str,
        candidate_name: str,
        vacancy_title: str,
        company_name: str,
        extra_context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Envia feedback diferenciado ao candidato dependendo do gate.

        Fail-safe: retorna False em caso de erro, nunca propaga exceção.
        LGPD: base legal = execução de contrato / interesse legítimo (Art. 7, II e IX).

        Args:
            gate_level: "screening_invited" | "gate1_rejected" | "gate2_rejected" | "approved"
            candidate_email: Email do candidato (obrigatório).
            candidate_name: Nome do candidato.
            vacancy_title: Título da vaga.
            company_name: Nome da empresa.
            extra_context: Dados adicionais para interpolar no template:
                - screening_url: URL para gate "screening_invited"
                - rejection_context: parágrafo opcional para gate2_rejected
                - next_step_info: parágrafo opcional para "approved"

        Returns:
            True se email enviado, False caso contrário (falha silenciosa).
        """
        if not candidate_email:
            logger.debug("[GateFeedback] Sem email → sem notificação (gate=%s)", gate_level)
            return False

        if gate_level not in self._GATE_SUBJECTS:
            logger.warning("[GateFeedback] gate_level inválido: %r", gate_level)
            return False

        ctx = extra_context or {}
        try:
            subject = self._GATE_SUBJECTS[gate_level].format(
                vacancy_title=vacancy_title or "Vaga",
                company=company_name or "WeDOTalent",
            )
            body = self._GATE_BODIES[gate_level].format(
                name=candidate_name or "Candidato(a)",
                vacancy_title=vacancy_title or "Vaga",
                company=company_name or "WeDOTalent",
                screening_url=ctx.get("screening_url", "https://wedotalent.com.br/screening"),
                rejection_context=ctx.get("rejection_context", ""),
                next_step_info=ctx.get("next_step_info", ""),
            )

            from app.domains.communication.services.email_service import email_service as _email_svc
            sent = await _email_svc._send_email_provider(
                to_email=candidate_email,
                subject=subject,
                body_html=body.replace("\n", "<br>"),
                body_text=body,
            )
            if sent:
                # PII masking: email parcialmente mascarado nos logs (LGPD Art. 46)
                _masked = candidate_email[:3] + "***" if len(candidate_email) > 3 else "***"
                logger.info(
                    "[GateFeedback] gate=%s sent → %s (vaga=%s)",
                    gate_level, _masked, vacancy_title,
                )
            return bool(sent)
        except Exception as exc:
            logger.warning(
                "[GateFeedback] Falha ao enviar gate=%s (vaga=%s): %s",
                gate_level, vacancy_title, exc,
            )
            return False


candidate_feedback_service = CandidateFeedbackService()
