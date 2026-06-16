"""
Data Request WhatsApp Collection Service

Service for managing data collection via WhatsApp chat.
LIA manages the conversation asking for one field at a time.

Conversation Flow:
1. Send LGPD consent message (if requireConsent=true)
2. Wait for "SIM" from candidate
3. If candidate_choice, send choicePrompt asking portal or chat
4. If chat chosen: send chatStartMessage asking for first field
5. For each document received: save, send documentReceived, ask for next
6. When complete: send allComplete
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.whatsapp_meta_service import meta_whatsapp_service
from app.domains.communication.services.communication_service import CommunicationService
from app.enums.communication import MessageChannel
from lia_models.candidate import Candidate
from lia_models.data_request import (
    DataFieldType,
    DataRequest,
    DataRequestConfig,
    DataRequestStatus,
)
from lia_models.data_request import (
    DataRequestResponse as DataRequestResponseModel,
)

logger = logging.getLogger(__name__)


class WhatsAppConversationState:
    """Conversation state constants"""
    AWAITING_CONSENT = "awaiting_consent"
    AWAITING_CHOICE = "awaiting_choice"
    COLLECTING = "collecting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


DEFAULT_COLLECTION_MESSAGES = {
    "initialRequest": "Olá {{nome}}! 👋\n\nA {{empresa}} precisa de alguns documentos e informações para dar continuidade ao seu processo seletivo.\n\nVocê pode enviar pelo nosso portal ou diretamente por aqui no chat.\n\nPara começar, preciso do seu consentimento (LGPD):\n\n_Seus dados serão utilizados exclusivamente para fins do processo seletivo e serão tratados conforme nossa política de privacidade._\n\nVocê autoriza o uso dos seus dados? Responda *SIM* para continuar.",
    "consentReceived": "Ótimo, {{nome}}! ✅\n\nSeu consentimento foi registrado. Obrigada!",
    "choicePrompt": "Como você prefere enviar seus documentos?\n\n1️⃣ *Portal* - Acesse o link e envie tudo de uma vez\n2️⃣ *Chat* - Envie aqui pelo WhatsApp, um por um\n\nResponda *1* para Portal ou *2* para Chat.",
    "portalLink": "Perfeito! 🔗\n\nAcesse o link abaixo para enviar seus documentos:\n\n{{portal_url}}\n\nO link é válido por 7 dias. Se precisar de ajuda, é só me chamar!",
    "chatStartMessage": "Ótimo! Vamos começar a coleta pelo chat. 📱\n\nVou pedir um documento por vez. Quando terminar todos, você receberá uma confirmação.\n\n📎 *Primeiro documento:*\n{{campo}}",
    "fieldRequest": "📎 *Próximo:*\n{{campo}}\n\n{{help_text}}",
    "documentReceived": "Recebi seu {{campo}}! ✅\n\n{{status_message}}",
    "invalidDocument": "Hmm, não consegui processar esse arquivo. 🤔\n\nPor favor, envie novamente o {{campo}} em um dos formatos aceitos: {{formatos}}",
    "allComplete": "🎉 *Parabéns, {{nome}}!*\n\nRecebemos todos os documentos solicitados.\n\nAgradecemos sua colaboração! A equipe de RH da {{empresa}} entrará em contato em breve.\n\n_Campos recebidos: {{campos_recebidos}}_",
    "pendingReminder": "Olá {{nome}}! 👋\n\nVocê ainda tem {{campos_pendentes}} pendentes para enviar.\n\nDeseja continuar agora? Responda *SIM* para continuar de onde parou.",
    "consentDenied": "Entendido, {{nome}}.\n\nSem o consentimento, não podemos prosseguir com a coleta de dados. Se mudar de ideia, entre em contato com o RH da {{empresa}}.",
    "helpMessage": "Precisa de ajuda? 🤝\n\n- Responda *STATUS* para ver o que falta enviar\n- Responda *AJUDA* para falar com o RH\n- Envie um documento/foto para continuar\n\nCampos pendentes: {{campos_pendentes}}"
}



# GAP-07-005: WhatsApp opt-out commands (LGPD)
_WHATSAPP_STOP_COMMANDS = frozenset({"STOP", "PARAR", "CANCELAR", "SAIR"})
class DataRequestWhatsAppService:
    """Service for WhatsApp-based data collection."""
    
    def __init__(self):
        self.whatsapp_service = meta_whatsapp_service
    
    def _replace_variables(
        self,
        message: str,
        candidate_name: str = "",
        company_name: str = "",
        field_label: str = "",
        next_field_label: str = "",
        pending_fields: list[str] = None,
        received_fields: list[str] = None,
        portal_url: str = "",
        help_text: str = "",
        allowed_formats: str = "",
        **kwargs
    ) -> str:
        """Replace template variables in messages."""
        pending_fields = pending_fields or []
        received_fields = received_fields or []
        
        pending_count = len(pending_fields)
        pending_text = f"{pending_count} documento(s)" if pending_count > 0 else "nenhum documento"
        
        replacements = {
            "{{nome}}": candidate_name,
            "{{empresa}}": company_name,
            "{{campo}}": field_label,
            "{{proximo_campo}}": next_field_label,
            "{{campos_pendentes}}": pending_text,
            "{{campos_recebidos}}": ", ".join(received_fields) if received_fields else "nenhum",
            "{{portal_url}}": portal_url,
            "{{help_text}}": help_text,
            "{{formatos}}": allowed_formats,
            "{{status_message}}": kwargs.get("status_message", ""),
        }
        
        for var, value in replacements.items():
            message = message.replace(var, value)
        
        return message
    
    async def _get_config(self, db: AsyncSession, company_id: UUID) -> DataRequestConfig:
        """Get or create company config."""
        from app.domains.communication.repositories.data_request_repository import DataRequestRepository
        repo = DataRequestRepository(db)
        config = await repo.get_config_for_company(company_id=company_id)

        if not config:
            config = DataRequestConfig(company_id=company_id)
            repo.add_config(config)
            await db.commit()
            await db.refresh(config)

        return config
    
    def _get_message(self, config: DataRequestConfig, message_key: str) -> str:
        """Get message template from config or default."""
        messages = config.collection_messages or {}
        return messages.get(message_key, DEFAULT_COLLECTION_MESSAGES.get(message_key, ""))
    
    async def start_collection(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        candidate_phone: str,
    ) -> bool:
        """
        Start WhatsApp data collection flow.
        
        Sends initial LGPD consent message or choice prompt based on config.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            candidate_phone: Candidate's WhatsApp phone number
            
        Returns:
            True if message sent successfully
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            logger.error(f"Data request {data_request_id} not found")
            return False
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        if not candidate:
            logger.error(f"Candidate {data_request.candidate_id} not found")
            return False
        
        config = await self._get_config(db, data_request.company_id)
        
        candidate_name = candidate.name or "Candidato"
        company_name = "Empresa"
        
        require_consent = config.lgpd_require_consent if hasattr(config, 'lgpd_require_consent') else True
        collection_mode = config.collection_mode if hasattr(config, 'collection_mode') else "portal_only"
        
        if require_consent:
            message_template = self._get_message(config, "initialRequest")
            initial_state = WhatsAppConversationState.AWAITING_CONSENT
        elif collection_mode == "candidate_choice":
            message_template = self._get_message(config, "choicePrompt")
            initial_state = WhatsAppConversationState.AWAITING_CHOICE
        else:
            message_template = self._get_message(config, "chatStartMessage")
            first_field = await self.get_next_pending_field(db, data_request_id)
            field_label = first_field.get("label", "") if first_field else ""
            message_template = self._replace_variables(
                message_template,
                candidate_name=candidate_name,
                company_name=company_name,
                field_label=field_label,
            )
            initial_state = WhatsAppConversationState.COLLECTING
        
        message = self._replace_variables(
            message_template,
            candidate_name=candidate_name,
            company_name=company_name,
        )
        
        result = await self.whatsapp_service.send_text_message(candidate_phone, message)
        
        if result.success:
            data_request.sent_via_whatsapp = True
            data_request.whatsapp_sent_at = datetime.utcnow()
            data_request.whatsapp_conversation_state = {
                "state": initial_state,
                "current_field": None,
                "phone": candidate_phone,
                "started_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat(),
            }
            await db.commit()
            
            logger.info(f"Started WhatsApp collection for data request {data_request_id}")
            return True
        
        logger.error(f"Failed to send WhatsApp message: {result.error}")
        return False
    
    async def process_consent_response(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        response: str,
    ) -> dict[str, Any]:
        """
        Process consent response from candidate.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            response: Candidate's response text
            
        Returns:
            Dict with success status and next action
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return {"success": False, "error": "Data request not found"}
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        config = await self._get_config(db, data_request.company_id)
        conv_state = data_request.whatsapp_conversation_state or {}
        phone = conv_state.get("phone", "")
        
        candidate_name = candidate.name or "Candidato"
        company_name = "Empresa"
        
        response_upper = response.strip().upper()
        
        if response_upper in ["SIM", "S", "YES", "Y", "ACEITO", "CONCORDO"]:
            consent_msg = self._get_message(config, "consentReceived")
            consent_msg = self._replace_variables(consent_msg, candidate_name=candidate_name)
            await self.whatsapp_service.send_text_message(phone, consent_msg)
            
            collection_mode = config.collection_mode if hasattr(config, 'collection_mode') else "portal_only"
            
            if collection_mode == "candidate_choice":
                choice_msg = self._get_message(config, "choicePrompt")
                choice_msg = self._replace_variables(choice_msg, candidate_name=candidate_name)
                await self.whatsapp_service.send_text_message(phone, choice_msg)
                
                conv_state["state"] = WhatsAppConversationState.AWAITING_CHOICE
                conv_state["consent_given"] = True
                conv_state["consent_at"] = datetime.utcnow().isoformat()
            elif collection_mode == "chat_only":
                first_field = await self.get_next_pending_field(db, data_request_id)
                if first_field:
                    await self.send_field_request(db, data_request_id, first_field)
                    conv_state["state"] = WhatsAppConversationState.COLLECTING
                    conv_state["current_field"] = first_field.get("name")
                else:
                    conv_state["state"] = WhatsAppConversationState.COMPLETED
                conv_state["consent_given"] = True
                conv_state["consent_at"] = datetime.utcnow().isoformat()
                data_request.collection_method = "whatsapp"
            else:
                portal_url = f"https://portal.lia.com.br/data-request/{data_request.token}"
                portal_msg = self._get_message(config, "portalLink")
                portal_msg = self._replace_variables(portal_msg, portal_url=portal_url)
                await self.whatsapp_service.send_text_message(phone, portal_msg)
                
                conv_state["state"] = WhatsAppConversationState.AWAITING_CHOICE
                conv_state["consent_given"] = True
                conv_state["consent_at"] = datetime.utcnow().isoformat()
                data_request.collection_method = "portal"
            
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            await db.commit()
            
            return {"success": True, "state": conv_state["state"], "consent": True}
        
        elif response_upper in ["NAO", "NÃO", "N", "NO", "RECUSO", "NAO ACEITO"]:
            deny_msg = self._get_message(config, "consentDenied")
            deny_msg = self._replace_variables(deny_msg, candidate_name=candidate_name, company_name=company_name)
            await self.whatsapp_service.send_text_message(phone, deny_msg)
            
            conv_state["state"] = WhatsAppConversationState.CANCELLED
            conv_state["consent_given"] = False
            conv_state["consent_denied_at"] = datetime.utcnow().isoformat()
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            data_request.status = DataRequestStatus.CANCELLED
            await db.commit()
            
            return {"success": True, "state": WhatsAppConversationState.CANCELLED, "consent": False}
        
        return {"success": False, "error": "Invalid response", "expected": "SIM ou NÃO"}
    
    async def process_choice_response(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        response: str,
    ) -> dict[str, Any]:
        """
        Process collection method choice from candidate.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            response: Candidate's response (1 for portal, 2 for chat)
            
        Returns:
            Dict with success status and chosen method
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return {"success": False, "error": "Data request not found"}
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        config = await self._get_config(db, data_request.company_id)
        conv_state = data_request.whatsapp_conversation_state or {}
        phone = conv_state.get("phone", "")
        
        candidate_name = candidate.name if candidate else "Candidato"
        
        response_clean = response.strip()
        
        if response_clean in ["1", "PORTAL", "LINK"]:
            portal_url = f"https://portal.lia.com.br/data-request/{data_request.token}"
            portal_msg = self._get_message(config, "portalLink")
            portal_msg = self._replace_variables(portal_msg, portal_url=portal_url)
            await self.whatsapp_service.send_text_message(phone, portal_msg)
            
            data_request.collection_method = "portal"
            conv_state["state"] = WhatsAppConversationState.COMPLETED
            conv_state["collection_method"] = "portal"
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            await db.commit()
            
            return {"success": True, "method": "portal"}
        
        elif response_clean in ["2", "CHAT", "WHATSAPP"]:
            first_field = await self.get_next_pending_field(db, data_request_id)
            
            if first_field:
                chat_msg = self._get_message(config, "chatStartMessage")
                chat_msg = self._replace_variables(
                    chat_msg,
                    candidate_name=candidate_name,
                    field_label=first_field.get("label", ""),
                )
                await self.whatsapp_service.send_text_message(phone, chat_msg)
                
                conv_state["state"] = WhatsAppConversationState.COLLECTING
                conv_state["current_field"] = first_field.get("name")
            else:
                complete_msg = self._get_message(config, "allComplete")
                received = [f.get("name") for f in (data_request.fields_completed or [])]
                complete_msg = self._replace_variables(
                    complete_msg,
                    candidate_name=candidate_name,
                    received_fields=received,
                )
                await self.whatsapp_service.send_text_message(phone, complete_msg)
                conv_state["state"] = WhatsAppConversationState.COMPLETED
            
            data_request.collection_method = "whatsapp"
            conv_state["collection_method"] = "whatsapp"
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            await db.commit()
            
            return {"success": True, "method": "whatsapp", "current_field": conv_state.get("current_field")}
        
        return {"success": False, "error": "Invalid choice", "expected": "1 ou 2"}
    

    async def _handle_stop_command(self, db, data_request) -> dict:
        """GAP-07-005: Handle WhatsApp STOP command -- record LGPD opt-out."""
        svc = CommunicationService()
        try:
            await svc.record_opt_out(
                company_id=str(data_request.company_id),
                candidate_id=str(data_request.candidate_id),
                channel=MessageChannel.WHATSAPP,
                opted_out_via="whatsapp_stop_command",
                db=db,
            )
            logger.info(
                "[WhatsApp] STOP received -- opt-out recorded for candidate %s",
                data_request.candidate_id,
            )
        except Exception:
            logger.error(
                "[WhatsApp] Failed to record STOP opt-out for candidate %s",
                data_request.candidate_id,
                exc_info=True,
            )
        return {
            "status": "opted_out",
            "message": "Descadastro registrado. Voce nao recebera mais mensagens via WhatsApp.",
        }

    async def process_document_response(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        message_content: str,
        file_url: str | None = None,
        file_name: str | None = None,
        file_mime_type: str | None = None,
        file_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Process document/text response for current field.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            message_content: Text content or caption
            file_url: URL of uploaded file (if any)
            file_name: Original filename
            file_mime_type: MIME type of file
            file_size: File size in bytes
            
        Returns:
            Dict with success status and next field info
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return {"success": False, "error": "Data request not found"}
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        config = await self._get_config(db, data_request.company_id)
        conv_state = data_request.whatsapp_conversation_state or {}
        phone = conv_state.get("phone", "")
        current_field_name = conv_state.get("current_field")
        
        candidate_name = candidate.name if candidate else "Candidato"
        company_name = "Empresa"
        
        if conv_state.get("state") == WhatsAppConversationState.AWAITING_CONSENT:
            return await self.process_consent_response(db, data_request_id, message_content)
        
        if conv_state.get("state") == WhatsAppConversationState.AWAITING_CHOICE:
            return await self.process_choice_response(db, data_request_id, message_content)
        
        # GAP-07-005: STOP command — LGPD opt-out from WhatsApp communications
        if message_content.strip().upper() in _WHATSAPP_STOP_COMMANDS:
            return await self._handle_stop_command(db, data_request)

        if message_content.strip().upper() in ["STATUS", "ESTADO"]:
            return await self._send_status_message(db, data_request, config, phone, candidate_name)
        
        if message_content.strip().upper() in ["AJUDA", "HELP"]:
            pending = await self._get_pending_field_labels(db, data_request_id)
            help_msg = self._get_message(config, "helpMessage")
            help_msg = self._replace_variables(help_msg, pending_fields=pending)
            await self.whatsapp_service.send_text_message(phone, help_msg)
            return {"success": True, "action": "help_sent"}
        
        if not current_field_name:
            first_field = await self.get_next_pending_field(db, data_request_id)
            if first_field:
                current_field_name = first_field.get("name")
                conv_state["current_field"] = current_field_name
        
        if not current_field_name:
            return {"success": False, "error": "No pending field to fill"}
        
        current_field = None
        for field in (data_request.fields_requested or []):
            if field.get("name") == current_field_name:
                current_field = field
                break
        
        if not current_field:
            return {"success": False, "error": f"Field {current_field_name} not found in request"}
        
        field_type = current_field.get("field_type", "text")
        
        if field_type in ["file", "photo", "FILE", "PHOTO"] and not file_url:
            invalid_msg = self._get_message(config, "invalidDocument")
            allowed = current_field.get("allowed_file_types", ["PDF", "JPG", "PNG"])
            invalid_msg = self._replace_variables(
                invalid_msg,
                field_label=current_field.get("label", ""),
                allowed_formats=", ".join(allowed),
            )
            await self.whatsapp_service.send_text_message(phone, invalid_msg)
            return {"success": False, "error": "File required but not provided"}
        
        response_record = DataRequestResponseModel(
            data_request_id=data_request_id,
            field_name=current_field_name,
            field_type=DataFieldType(field_type.lower()) if isinstance(field_type, str) else field_type,
            value=message_content if not file_url else None,
            file_url=file_url,
            file_name=file_name,
            file_size_bytes=file_size,
            file_mime_type=file_mime_type,
            is_valid=True,
            submitted_at=datetime.utcnow(),
        )
        db.add(response_record)
        
        completed_fields = data_request.fields_completed or []
        completed_fields.append({
            "name": current_field_name,
            "label": current_field.get("label", ""),
            "completed_at": datetime.utcnow().isoformat(),
        })
        data_request.fields_completed = completed_fields
        
        next_field = await self.get_next_pending_field(db, data_request_id, exclude=current_field_name)
        
        if next_field:
            pending = await self._get_pending_field_labels(db, data_request_id, exclude=current_field_name)
            status_msg = f"Faltam {len(pending)} documento(s)." if pending else ""
            
            received_msg = self._get_message(config, "documentReceived")
            received_msg = self._replace_variables(
                received_msg,
                field_label=current_field.get("label", ""),
                status_message=status_msg,
            )
            await self.whatsapp_service.send_text_message(phone, received_msg)
            
            await self.send_field_request(db, data_request_id, next_field, phone=phone)
            
            conv_state["current_field"] = next_field.get("name")
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            
            if data_request.status == DataRequestStatus.PENDING:
                data_request.status = DataRequestStatus.PARTIALLY_FILLED
            
            await db.commit()
            
            return {
                "success": True,
                "field_saved": current_field_name,
                "next_field": next_field.get("name"),
                "state": WhatsAppConversationState.COLLECTING,
            }
        
        else:
            received = [f.get("label") for f in completed_fields]
            complete_msg = self._get_message(config, "allComplete")
            complete_msg = self._replace_variables(
                complete_msg,
                candidate_name=candidate_name,
                company_name=company_name,
                received_fields=received,
            )
            await self.whatsapp_service.send_text_message(phone, complete_msg)
            
            conv_state["state"] = WhatsAppConversationState.COMPLETED
            conv_state["current_field"] = None
            conv_state["completed_at"] = datetime.utcnow().isoformat()
            conv_state["last_message_at"] = datetime.utcnow().isoformat()
            data_request.whatsapp_conversation_state = conv_state
            data_request.status = DataRequestStatus.COMPLETED
            data_request.completed_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "success": True,
                "field_saved": current_field_name,
                "state": WhatsAppConversationState.COMPLETED,
                "all_complete": True,
            }
    
    async def get_next_pending_field(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        exclude: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get the next pending field to collect.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            exclude: Field name to exclude (just completed)
            
        Returns:
            Field dict or None if all complete
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return None
        
        completed_names = {f.get("name") for f in (data_request.fields_completed or [])}
        if exclude:
            completed_names.add(exclude)
        
        for field in (data_request.fields_requested or []):
            if field.get("name") not in completed_names:
                if field.get("is_required", True):
                    return field
        
        for field in (data_request.fields_requested or []):
            if field.get("name") not in completed_names:
                return field
        
        return None
    
    async def _get_pending_field_labels(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        exclude: str | None = None,
    ) -> list[str]:
        """Get labels of all pending fields."""
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return []
        
        completed_names = {f.get("name") for f in (data_request.fields_completed or [])}
        if exclude:
            completed_names.add(exclude)
        
        pending = []
        for field in (data_request.fields_requested or []):
            if field.get("name") not in completed_names:
                pending.append(field.get("label", field.get("name", "")))
        
        return pending
    
    async def send_field_request(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        field: dict[str, Any],
        phone: str | None = None,
    ) -> bool:
        """
        Send request message for a specific field.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            field: Field definition dict
            phone: Phone number (optional, uses stored if not provided)
            
        Returns:
            True if message sent successfully
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return False
        
        if not phone:
            conv_state = data_request.whatsapp_conversation_state or {}
            phone = conv_state.get("phone", "")
        
        if not phone:
            logger.error(f"No phone number for data request {data_request_id}")
            return False
        
        config = await self._get_config(db, data_request.company_id)
        
        field_label = field.get("label", field.get("name", ""))
        help_text = field.get("help_text", "")
        
        field_type = field.get("field_type", "text")
        if field_type in ["file", "photo", "FILE", "PHOTO"]:
            allowed = field.get("allowed_file_types", ["PDF", "JPG", "PNG"])
            if not help_text:
                help_text = f"Formatos aceitos: {', '.join(allowed)}"
        
        message = self._get_message(config, "fieldRequest")
        message = self._replace_variables(
            message,
            field_label=field_label,
            help_text=help_text,
        )
        
        result = await self.whatsapp_service.send_text_message(phone, message)
        
        if result.success:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.info(f"Sent field request for {field.get('name')} to {phone}")
            return True
        
        logger.error(f"Failed to send field request: {result.error}")
        return False
    
    async def _send_status_message(
        self,
        db: AsyncSession,
        data_request: DataRequest,
        config: DataRequestConfig,
        phone: str,
        candidate_name: str,
    ) -> dict[str, Any]:
        """Send status message showing pending and completed fields."""
        completed = [f.get("label", f.get("name", "")) for f in (data_request.fields_completed or [])]
        pending = await self._get_pending_field_labels(db, data_request.id)
        
        status_text = f"📊 *Status dos seus documentos, {candidate_name}:*\n\n"
        
        if completed:
            status_text += "✅ *Recebidos:*\n"
            for item in completed:
                status_text += f"  • {item}\n"
            status_text += "\n"
        
        if pending:
            status_text += "⏳ *Pendentes:*\n"
            for item in pending:
                status_text += f"  • {item}\n"
            status_text += "\nEnvie o próximo documento para continuar!"
        else:
            status_text += "🎉 Todos os documentos foram recebidos!"
        
        await self.whatsapp_service.send_text_message(phone, status_text)
        
        return {"success": True, "action": "status_sent", "pending": len(pending), "completed": len(completed)}
    
    async def get_conversation_status(
        self,
        db: AsyncSession,
        data_request_id: UUID,
    ) -> dict[str, Any]:
        """
        Get current conversation status.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            
        Returns:
            Status dict with state, progress, and field info
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return {"success": False, "error": "Data request not found"}
        
        conv_state = data_request.whatsapp_conversation_state or {}
        completed = data_request.fields_completed or []
        requested = data_request.fields_requested or []
        
        pending_labels = await self._get_pending_field_labels(db, data_request_id)
        
        return {
            "success": True,
            "state": conv_state.get("state", "not_started"),
            "collection_method": data_request.collection_method,
            "current_field": conv_state.get("current_field"),
            "consent_given": conv_state.get("consent_given", False),
            "fields_total": len(requested),
            "fields_completed": len(completed),
            "fields_pending": len(pending_labels),
            "completion_percentage": data_request.get_completion_percentage(),
            "started_at": conv_state.get("started_at"),
            "last_message_at": conv_state.get("last_message_at"),
            "completed_at": conv_state.get("completed_at"),
        }
    
    async def process_incoming_message(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        message_content: str,
        file_url: str | None = None,
        file_name: str | None = None,
        file_mime_type: str | None = None,
        file_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point for processing incoming WhatsApp messages.
        
        Routes to appropriate handler based on conversation state.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            message_content: Text content of message
            file_url: Optional file URL
            file_name: Optional file name
            file_mime_type: Optional MIME type
            file_size: Optional file size
            
        Returns:
            Processing result dict
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            return {"success": False, "error": "Data request not found"}
        
        conv_state = data_request.whatsapp_conversation_state or {}
        state = conv_state.get("state", "not_started")
        
        if state == "not_started":
            return {"success": False, "error": "Collection not started. Call start_collection first."}
        
        if state == WhatsAppConversationState.AWAITING_CONSENT:
            return await self.process_consent_response(db, data_request_id, message_content)
        
        if state == WhatsAppConversationState.AWAITING_CHOICE:
            return await self.process_choice_response(db, data_request_id, message_content)
        
        if state == WhatsAppConversationState.COLLECTING:
            return await self.process_document_response(
                db, data_request_id, message_content,
                file_url, file_name, file_mime_type, file_size
            )
        
        if state == WhatsAppConversationState.COMPLETED:
            return {"success": True, "state": "completed", "message": "All documents already received"}
        
        if state == WhatsAppConversationState.CANCELLED:
            return {"success": False, "state": "cancelled", "message": "Collection was cancelled"}
        
        return {"success": False, "error": f"Unknown state: {state}"}


data_request_whatsapp_service = DataRequestWhatsAppService()
