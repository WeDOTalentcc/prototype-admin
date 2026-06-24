"""
Data Request Service

Service for managing data request operations including:
- Creating data requests with unique tokens
- Sending notifications (email/WhatsApp/voice)
- Checking completion status
- Managing templates and fields
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.domains.communication.repositories.data_request_repository import DataRequestRepository
from app.services.notification_service import notification_service
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate
from lia_models.data_request import (
    DEFAULT_DATA_FIELDS,
    DataFieldType,
    DataRequest,
    DataRequestConfig,
    DataRequestField,
    DataRequestStatus,
    DataRequestTemplate,
    TriggerType,
    VacancyDataRequestConfig,
)

logger = logging.getLogger(__name__)


class DataRequestService:
    """Service class for data request operations."""
    
    async def create_data_request(
        self,
        db: AsyncSession,
        company_id: UUID,
        candidate_id: UUID,
        vacancy_id: UUID | None = None,
        template_id: UUID | None = None,
        fields: list[dict[str, Any]] | None = None,
        trigger_type: TriggerType = TriggerType.MANUAL,
        trigger_stage: str | None = None,
        is_blocking: bool = False,
        expiration_days: int = 7,
        created_by: UUID | None = None,
    ) -> DataRequest:
        """
        Create a new data request for a candidate.
        
        Args:
            db: Database session
            company_id: Company ID
            candidate_id: Candidate ID
            vacancy_id: Optional vacancy ID
            template_id: Optional template ID to use
            fields: List of fields to request (uses template fields if not provided)
            trigger_type: Type of trigger (manual, automatic, stage_entry, stage_exit)
            trigger_stage: Stage that triggered the request
            is_blocking: Whether this request blocks candidate progress
            expiration_days: Days until request expires
            created_by: User ID who created the request
            
        Returns:
            Created DataRequest object
        """
        fields_requested = fields or []
        
        if template_id and not fields_requested:
            template = await db.get(DataRequestTemplate, template_id)
            if template:
                fields_requested = template.fields or []
                if template.expiration_days:
                    expiration_days = template.expiration_days
                if template.is_blocking:
                    is_blocking = template.is_blocking
        
        token = DataRequest.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        
        data_request = DataRequest(
            company_id=company_id,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            template_id=template_id,
            token=token,
            status=DataRequestStatus.PENDING,
            fields_requested=fields_requested,
            fields_completed=[],
            trigger_type=trigger_type,
            trigger_stage=trigger_stage,
            is_blocking=is_blocking,
            expires_at=expires_at,
            created_by=created_by,
        )
        
        db.add(data_request)
        await db.commit()
        await db.refresh(data_request)
        
        logger.info(f"Created data request {data_request.id} for candidate {candidate_id}")
        
        return data_request
    
    async def send_notification(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        channels: list[str] = None,
    ) -> dict[str, Any]:
        """
        Send notification to candidate about data request.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            channels: List of channels to use (email, whatsapp, voice).
                Unknown channels are rejected with error="unsupported_channel".
            
        Returns:
            Dictionary with notification status for each channel
        """
        channels = channels or ["email"]
        # Canonical channel allow-list. Unknown channels are surfaced as an
        # explicit error (not silently dropped) — keeps the dispatch honest.
        _SUPPORTED_CHANNELS = {"email", "whatsapp", "voice"}
        data_request = await db.get(DataRequest, data_request_id)
        
        if not data_request:
            raise ValueError(f"Data request {data_request_id} not found")
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {data_request.candidate_id} not found")
        
        # Envio REAL via dispatcher canônico (substitui o stub que marcava "enviado"
        # sem despachar). Import lazy p/ evitar ciclo de import.
        from app.domains.communication.services.communication_dispatcher import (
            communication_dispatcher,
        )
        from app.domains.communication.services.data_request_whatsapp_service import (
            DataRequestWhatsAppService,
        )

        results = {}
        now = datetime.utcnow()

        if "email" in channels:
            candidate_email = getattr(candidate, "email", None)
            if not candidate_email:
                # Falha alta e explícita — nunca marcar como enviado sem destinatário.
                results["email"] = {"success": False, "error": "candidate_no_email"}
                logger.warning(
                    "Data request %s: candidato sem email, notificação por email pulada",
                    data_request_id,
                )
            else:
                portal_url = self._build_portal_url(data_request.token)
                subject, body_html, body_text = self._build_data_request_email(
                    candidate_name=getattr(candidate, "name", None) or "",
                    portal_url=portal_url,
                    is_blocking=bool(data_request.is_blocking),
                )
                try:
                    send_result = communication_dispatcher.send_email(
                        to_email=candidate_email,
                        subject=subject,
                        body_html=body_html,
                        body_text=body_text,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to send email for data request %s: %s",
                        data_request_id, e, exc_info=True,
                    )
                    send_result = {"success": False, "error": str(e)}
                ok = bool(send_result.get("success"))
                results["email"] = {
                    "success": ok,
                    "sent_at": now.isoformat() if ok else None,
                    "provider": send_result.get("provider"),
                    "error": send_result.get("error"),
                }
                if ok:
                    data_request.sent_via_email = True
                    data_request.email_sent_at = now

        if "whatsapp" in channels:
            candidate_phone = getattr(candidate, "phone", None)
            if not candidate_phone:
                results["whatsapp"] = {"success": False, "error": "candidate_no_phone"}
                logger.warning(
                    "Data request %s: candidato sem telefone, coleta WhatsApp pulada",
                    data_request_id,
                )
            else:
                # Delega ao fluxo canônico de coleta por WhatsApp (LGPD/consent/conversa).
                try:
                    ok = await DataRequestWhatsAppService().start_collection(
                        db, data_request_id, candidate_phone
                    )
                except Exception as e:
                    logger.error(
                        "Failed to start WhatsApp collection for data request %s: %s",
                        data_request_id, e, exc_info=True,
                    )
                    ok = False
                results["whatsapp"] = {
                    "success": bool(ok),
                    "sent_at": now.isoformat() if ok else None,
                }
                if ok:
                    data_request.sent_via_whatsapp = True
                    data_request.whatsapp_sent_at = now

        if "voice" in channels:
            candidate_phone = getattr(candidate, "phone", None)
            if not candidate_phone:
                results["voice"] = {"success": False, "error": "candidate_no_phone"}
                logger.warning(
                    "Data request %s: candidato sem telefone, coleta por voz pulada",
                    data_request_id,
                )
            else:
                # Delega ao fluxo canônico de coleta por voz. Import lazy p/ evitar
                # ciclo de import + custo de import pesado do orquestrador de voz.
                from app.domains.communication.services.data_request_voice_service import (
                    DataRequestVoiceService,
                )
                try:
                    voice_result = await DataRequestVoiceService().start_collection(
                        db, data_request_id, candidate_phone
                    )
                except Exception as e:
                    logger.error(
                        "Failed to start voice collection for data request %s: %s",
                        data_request_id, e, exc_info=True,
                    )
                    voice_result = {"status": "error", "error": str(e)}
                # success = call placed; fallback/prepared são explícitos, não fake.
                status = voice_result.get("status")
                ok = status == "voice_collection_initiated"
                results["voice"] = {
                    "success": ok,
                    "status": status,
                    "sent_at": now.isoformat() if ok else None,
                    "fields": voice_result.get("fields"),
                    "error": voice_result.get("error"),
                }

        # Reject any channel outside the canonical allow-list — surfaced as an
        # explicit error so a typo'd/unknown channel is never silently ignored.
        for _ch in channels:
            if _ch not in _SUPPORTED_CHANNELS:
                results[_ch] = {"success": False, "error": "unsupported_channel"}
                logger.warning(
                    "Data request %s: canal não suportado %r ignorado",
                    data_request_id, _ch,
                )

        await db.commit()

        # G5: Emit bell notification if any channel succeeded
        any_success = any(r.get("success") for r in results.values())
        if any_success:
            try:
                await notification_service.create_notification(
                    user_id=str(data_request.candidate_id),
                    title="Dados solicitados para seu processo seletivo",
                    message="Precisamos de algumas informações e documentos para continuar.",
                    notification_type="info",
                    category="data_request",
                    related_candidate_id=str(data_request.candidate_id),
                    related_job_id=str(data_request.vacancy_id) if data_request.vacancy_id else None,
                    channels=["bell"],
                    db=db,
                )
            except Exception as e:
                logger.error(
                    "Failed to create bell notification for data request %s: %s",
                    data_request_id, e, exc_info=True,
                )

        return results

    @staticmethod
    def _build_portal_url(token: str) -> str:
        """Monta o link público do portal de preenchimento (com token)."""
        base = (
            os.getenv("PUBLIC_APP_URL")
            or os.getenv("APP_BASE_URL")
            or "https://app.wedotalent.cc"
        ).rstrip("/")
        return f"{base}/pt/portal/data-request/{token}"

    @staticmethod
    def _build_data_request_email(
        candidate_name: str,
        portal_url: str,
        is_blocking: bool,
    ) -> tuple[str, str, str]:
        """Conteúdo canônico do email de solicitação de dados (subject, html, text)."""
        first_name = (candidate_name or "").split(" ")[0] if candidate_name else ""
        greeting = f"Olá {first_name}!" if first_name else "Olá!"
        subject = "Solicitação de informações — processo seletivo"
        body_text = (
            f"{greeting}\n\n"
            "Para dar continuidade ao seu processo seletivo, precisamos de algumas "
            "informações e documentos. Acesse o link seguro abaixo para enviar:\n\n"
            f"{portal_url}\n\n"
            "Seus dados são tratados conforme a LGPD e usados exclusivamente para este "
            "processo seletivo.\n"
        )
        body_html = (
            f"<p>{greeting}</p>"
            "<p>Para dar continuidade ao seu processo seletivo, precisamos de algumas "
            "informações e documentos. Clique no botão abaixo para enviar com segurança:</p>"
            f'<p><a href="{portal_url}" '
            'style="display:inline-block;padding:10px 18px;background:#0F62FE;color:#fff;'
            'text-decoration:none;border-radius:8px">Enviar minhas informações</a></p>'
            f'<p style="font-size:12px;color:#666">Ou copie o link: {portal_url}</p>'
            '<p style="font-size:12px;color:#666">Seus dados são tratados conforme a LGPD '
            "e usados exclusivamente para este processo seletivo.</p>"
        )
        return subject, body_html, body_text
    
    async def resend_notification(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        channels: list[str] = None,
    ) -> dict[str, Any]:
        """
        Resend notification (increment reminder count).
        
        Args:
            db: Database session
            data_request_id: Data request ID
            channels: Channels to use
            
        Returns:
            Notification results
        """
        data_request = await db.get(DataRequest, data_request_id)
        
        if not data_request:
            raise ValueError(f"Data request {data_request_id} not found")
        
        if data_request.status == DataRequestStatus.COMPLETED:
            raise ValueError("Cannot resend notification for completed request")
        
        if data_request.status == DataRequestStatus.CANCELLED:
            raise ValueError("Cannot resend notification for cancelled request")
        
        data_request.reminder_count = (data_request.reminder_count or 0) + 1
        data_request.last_reminder_at = datetime.utcnow()
        
        results = await self.send_notification(db, data_request_id, channels)
        
        return {
            "reminder_count": data_request.reminder_count,
            "channels": results,
        }
    
    async def check_completion_status(
        self,
        db: AsyncSession,
        data_request_id: UUID,
    ) -> dict[str, Any]:
        """
        Check and update completion status of a data request.
        
        Args:
            db: Database session
            data_request_id: Data request ID
            
        Returns:
            Status information
        """
        data_request = await db.get(DataRequest, data_request_id)
        
        if not data_request:
            raise ValueError(f"Data request {data_request_id} not found")
        
        if data_request.is_expired():
            if data_request.status not in [DataRequestStatus.COMPLETED, DataRequestStatus.CANCELLED]:
                data_request.status = DataRequestStatus.EXPIRED
                await db.commit()
        
        completion_percentage = data_request.get_completion_percentage()
        
        if completion_percentage == 100 and data_request.status != DataRequestStatus.COMPLETED:
            data_request.status = DataRequestStatus.COMPLETED
            data_request.completed_at = datetime.utcnow()
            await db.commit()
        elif completion_percentage > 0 and data_request.status == DataRequestStatus.PENDING:
            data_request.status = DataRequestStatus.PARTIALLY_FILLED
            await db.commit()
        
        return {
            "id": str(data_request.id),
            "status": data_request.status.value,
            "completion_percentage": completion_percentage,
            "is_expired": data_request.is_expired(),
            "fields_total": len(data_request.fields_requested or []),
            "fields_completed": len(data_request.fields_completed or []),
        }
    
    async def get_candidate_data_requests(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        status: DataRequestStatus | None = None,
        include_expired: bool = False,
    ) -> list[DataRequest]:
        """
        Get all data requests for a candidate.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            status: Optional status filter
            include_expired: Whether to include expired requests
            
        Returns:
            List of data requests
        """
        return await DataRequestRepository(db).list_for_candidate(
            candidate_id=candidate_id, status=status, include_expired=include_expired
        )
    
    async def get_vacancy_data_requests(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        status: DataRequestStatus | None = None,
    ) -> list[DataRequest]:
        """
        Get all data requests for a vacancy.
        
        Args:
            db: Database session
            vacancy_id: Vacancy ID
            status: Optional status filter
            
        Returns:
            List of data requests
        """
        return await DataRequestRepository(db).list_for_vacancy(
            vacancy_id=vacancy_id, status=status
        )
    
    async def get_data_request_by_id(
        self,
        db: AsyncSession,
        data_request_id: UUID,
    ) -> DataRequest | None:
        """Get a data request by ID."""
        return await db.get(DataRequest, data_request_id)
    
    async def get_data_request_by_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> DataRequest | None:
        """Get a data request by token."""
        return await DataRequestRepository(db).get_by_token(token)
    
    async def cancel_data_request(
        self,
        db: AsyncSession,
        data_request_id: UUID,
    ) -> DataRequest:
        """Cancel a data request."""
        data_request = await db.get(DataRequest, data_request_id)
        
        if not data_request:
            raise ValueError(f"Data request {data_request_id} not found")
        
        if data_request.status == DataRequestStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed request")
        
        data_request.status = DataRequestStatus.CANCELLED
        await db.commit()
        await db.refresh(data_request)
        
        return data_request
    
    async def get_or_create_config(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> DataRequestConfig:
        """Get or create company config."""
        repo = DataRequestRepository(db)
        config = await repo.get_config_for_company(company_id=company_id)

        if not config:
            config = DataRequestConfig(company_id=company_id)
            repo.add_config(config)
            await db.commit()
            await db.refresh(config)

        return config
    
    async def update_config(
        self,
        db: AsyncSession,
        company_id: UUID,
        updates: dict[str, Any],
    ) -> DataRequestConfig:
        """Update company config."""
        config = await self.get_or_create_config(db, company_id)
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        await db.commit()
        await db.refresh(config)
        
        return config
    
    async def list_templates(
        self,
        db: AsyncSession,
        company_id: UUID,
        active_only: bool = True,
    ) -> list[DataRequestTemplate]:
        """List templates for a company."""
        return await DataRequestRepository(db).list_templates_for_company(
            company_id=company_id, active_only=active_only
        )
    
    async def create_template(
        self,
        db: AsyncSession,
        company_id: UUID,
        name: str,
        description: str | None = None,
        fields: list[dict[str, Any]] | None = None,
        trigger_stage: str | None = None,
        trigger_type: TriggerType = TriggerType.MANUAL,
        is_blocking: bool = False,
        expiration_days: int = 7,
        created_by: UUID | None = None,
    ) -> DataRequestTemplate:
        """Create a new template."""
        template = DataRequestTemplate(
            company_id=company_id,
            name=name,
            description=description,
            fields=fields or [],
            trigger_stage=trigger_stage,
            trigger_type=trigger_type,
            is_blocking=is_blocking,
            expiration_days=expiration_days,
            created_by=created_by,
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return template
    
    async def update_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        updates: dict[str, Any],
    ) -> DataRequestTemplate:
        """Update a template."""
        template = await db.get(DataRequestTemplate, template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        for key, value in updates.items():
            if hasattr(template, key) and key not in ["id", "company_id", "created_at"]:
                setattr(template, key, value)
        
        await db.commit()
        await db.refresh(template)
        
        return template
    
    async def delete_template(
        self,
        db: AsyncSession,
        template_id: UUID,
    ) -> bool:
        """Soft delete a template."""
        template = await db.get(DataRequestTemplate, template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template.is_active = False
        await db.commit()
        
        return True
    
    async def list_fields(
        self,
        db: AsyncSession,
        company_id: UUID,
        include_defaults: bool = True,
    ) -> list[dict[str, Any]]:
        """List available fields for a company."""
        fields = []
        
        if include_defaults:
            for field in DEFAULT_DATA_FIELDS:
                field_copy = field.copy()
                if "field_type" in field_copy and isinstance(field_copy["field_type"], DataFieldType):
                    field_copy["field_type"] = field_copy["field_type"].value
                field_copy["is_default"] = True
                fields.append(field_copy)
        
        custom_fields = await DataRequestRepository(db).list_active_fields_for_company(
            company_id=company_id
        )
        
        for field in custom_fields:
            fields.append({
                "id": str(field.id),
                "name": field.name,
                "label": field.label,
                "label_en": field.label_en,
                "description": field.description,
                "field_type": field.field_type.value if field.field_type else None,
                "is_required": field.is_required,
                "validation_rules": field.validation_rules,
                "options": field.options,
                "placeholder": field.placeholder,
                "help_text": field.help_text,
                "max_file_size_mb": field.max_file_size_mb,
                "allowed_file_types": field.allowed_file_types,
                "order": field.order,
                "is_default": False,
            })
        
        return fields
    
    async def create_field(
        self,
        db: AsyncSession,
        company_id: UUID,
        name: str,
        label: str,
        field_type: DataFieldType,
        label_en: str | None = None,
        description: str | None = None,
        is_required: bool = True,
        validation_rules: dict[str, Any] | None = None,
        options: list[str] | None = None,
        placeholder: str | None = None,
        help_text: str | None = None,
        max_file_size_mb: int = 10,
        allowed_file_types: list[str] | None = None,
        order: int = 0,
    ) -> DataRequestField:
        """Create a custom field."""
        field = DataRequestField(
            company_id=company_id,
            name=name,
            label=label,
            label_en=label_en,
            description=description,
            field_type=field_type,
            is_required=is_required,
            validation_rules=validation_rules or {},
            options=options or [],
            placeholder=placeholder,
            help_text=help_text,
            max_file_size_mb=max_file_size_mb,
            allowed_file_types=allowed_file_types or [],
            order=order,
        )
        
        db.add(field)
        await db.commit()
        await db.refresh(field)
        
        return field


    async def get_vacancy_trigger_config(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        company_id: UUID,
    ) -> dict[str, Any]:
        """
        Get trigger configuration for a vacancy.
        
        Priority: VacancyDataRequestConfig > DataRequestConfig (company default)
        
        Args:
            db: Database session
            vacancy_id: Vacancy ID
            company_id: Company ID
            
        Returns:
            Dict with stage_configs and source indicator
        """
        vacancy_config = await DataRequestRepository(db).get_vacancy_config(
            vacancy_id=vacancy_id
        )
        
        if vacancy_config and not vacancy_config.use_company_defaults:
            return {
                "source": "vacancy",
                "vacancy_id": str(vacancy_id),
                "stage_configs": vacancy_config.stage_configs or {},
                "custom_template_id": str(vacancy_config.custom_template_id) if vacancy_config.custom_template_id else None,
            }
        
        templates = await self.list_templates(db, company_id, active_only=True)
        stage_configs = {}
        
        for template in templates:
            if template.trigger_stage and template.trigger_type in [TriggerType.STAGE_ENTRY, TriggerType.AUTOMATIC]:
                stage_configs[template.trigger_stage] = {
                    "template_id": str(template.id),
                    "template_name": template.name,
                    "trigger_type": template.trigger_type.value if template.trigger_type else "stage_entry",
                    "is_blocking": template.is_blocking or False,
                    "fields": template.fields or [],
                }
        
        return {
            "source": "company_default",
            "company_id": str(company_id),
            "stage_configs": stage_configs,
        }
    
    async def get_trigger_fields_for_stage(
        self,
        db: AsyncSession,
        vacancy_id: UUID | None,
        company_id: UUID,
        stage: str,
    ) -> dict[str, Any] | None:
        """
        Get the trigger configuration for a specific stage.
        
        Returns the fields to request and template info if a trigger is configured.
        
        Args:
            db: Database session
            vacancy_id: Optional vacancy ID
            company_id: Company ID
            stage: Stage name to check
            
        Returns:
            Dict with fields and trigger config, or None if no trigger
        """
        if vacancy_id:
            vacancy_config = await DataRequestRepository(db).get_vacancy_config(
                vacancy_id=vacancy_id
            )
            
            if vacancy_config and not vacancy_config.use_company_defaults:
                stage_configs = vacancy_config.stage_configs or {}
                if stage in stage_configs:
                    config = stage_configs[stage]
                    return {
                        "source": "vacancy",
                        "trigger_type": config.get("trigger_type", "stage_entry"),
                        "is_blocking": config.get("is_blocking", False),
                        "template_id": config.get("template_id"),
                        "fields": config.get("fields", []),
                    }
        
        template = await DataRequestRepository(db).find_active_template_for_stage(
            company_id=company_id, stage=stage
        )
        
        if template:
            return {
                "source": "company_template",
                "trigger_type": template.trigger_type.value if template.trigger_type else "stage_entry",
                "is_blocking": template.is_blocking or False,
                "template_id": str(template.id),
                "template_name": template.name,
                "fields": template.fields or [],
            }
        
        from lia_models.data_request import DEFAULT_STAGE_FIELD_MAPPINGS
        
        if stage in DEFAULT_STAGE_FIELD_MAPPINGS:
            default_field_names = DEFAULT_STAGE_FIELD_MAPPINGS[stage]
            fields = [
                f for f in DEFAULT_DATA_FIELDS
                if f.get("name") in default_field_names
            ]
            if fields:
                fields_with_str_type = []
                for f in fields:
                    f_copy = f.copy()
                    if "field_type" in f_copy and hasattr(f_copy["field_type"], "value"):
                        f_copy["field_type"] = f_copy["field_type"].value
                    fields_with_str_type.append(f_copy)
                
                return {
                    "source": "default_mapping",
                    "trigger_type": "stage_entry",
                    "is_blocking": False,
                    "template_id": None,
                    "fields": fields_with_str_type,
                }
        
        return None
    
    async def find_blocking_pending_request(
        self,
        db,
        candidate_id,
        vacancy_id,
        stage,
    ):
        from sqlalchemy import select, and_
        from lia_models.data_request import DataRequest, DataRequestStatus
        query = select(DataRequest).where(
            and_(
                DataRequest.candidate_id == candidate_id,
                DataRequest.trigger_stage == stage,
                DataRequest.is_blocking == True,
                DataRequest.status.in_([
                    DataRequestStatus.PENDING,
                    DataRequestStatus.PARTIALLY_FILLED
                ])
            )
        )
        if vacancy_id:
            query = query.where(DataRequest.vacancy_id == vacancy_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def check_existing_pending_request(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        vacancy_id: UUID | None,
        stage: str,
    ) -> bool:
        """
        Check if there's already a pending data request for this candidate/stage.
        
        Prevents duplicate requests for the same stage.
        """
        # ADR-001-EXEMPT: dynamic where-clause (optional vacancy_id refinement) is awkward
        # to expose via repo without leaking SQLAlchemy column references. Sprint 6 follow-up:
        # promote to repo with a kwarg-driven filter helper.
        query = select(DataRequest).where(
            and_(
                DataRequest.candidate_id == candidate_id,
                DataRequest.trigger_stage == stage,
                DataRequest.status.in_([
                    DataRequestStatus.PENDING,
                    DataRequestStatus.PARTIALLY_FILLED
                ])
            )
        )
        
        if vacancy_id:
            query = query.where(DataRequest.vacancy_id == vacancy_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


data_request_service = DataRequestService()
