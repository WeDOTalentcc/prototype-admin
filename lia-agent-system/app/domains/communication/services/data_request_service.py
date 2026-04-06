"""
Data Request Service

Service for managing data request operations including:
- Creating data requests with unique tokens
- Sending notifications (email/WhatsApp)
- Checking completion status
- Managing templates and fields
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.data_request import (
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
            channels: List of channels to use (email, whatsapp)
            
        Returns:
            Dictionary with notification status for each channel
        """
        channels = channels or ["email"]
        data_request = await db.get(DataRequest, data_request_id)
        
        if not data_request:
            raise ValueError(f"Data request {data_request_id} not found")
        
        candidate = await db.get(Candidate, data_request.candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {data_request.candidate_id} not found")
        
        results = {}
        now = datetime.utcnow()
        
        if "email" in channels:
            try:
                results["email"] = {"success": True, "sent_at": now.isoformat()}
                data_request.sent_via_email = True
                data_request.email_sent_at = now
                logger.info(f"Email notification sent for data request {data_request_id}")
            except Exception as e:
                logger.error(f"Failed to send email for data request {data_request_id}: {e}")
                results["email"] = {"success": False, "error": str(e)}
        
        if "whatsapp" in channels:
            try:
                results["whatsapp"] = {"success": True, "sent_at": now.isoformat()}
                data_request.sent_via_whatsapp = True
                data_request.whatsapp_sent_at = now
                logger.info(f"WhatsApp notification sent for data request {data_request_id}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp for data request {data_request_id}: {e}")
                results["whatsapp"] = {"success": False, "error": str(e)}
        
        await db.commit()
        
        return results
    
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
        query = select(DataRequest).where(DataRequest.candidate_id == candidate_id)
        
        if status:
            query = query.where(DataRequest.status == status)
        
        if not include_expired:
            query = query.where(
                or_(
                    DataRequest.status != DataRequestStatus.EXPIRED,
                    DataRequest.expires_at > datetime.utcnow()
                )
            )
        
        query = query.order_by(DataRequest.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
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
        query = select(DataRequest).where(DataRequest.vacancy_id == vacancy_id)
        
        if status:
            query = query.where(DataRequest.status == status)
        
        query = query.order_by(DataRequest.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
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
        query = select(DataRequest).where(DataRequest.token == token)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
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
        query = select(DataRequestConfig).where(DataRequestConfig.company_id == company_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            config = DataRequestConfig(company_id=company_id)
            db.add(config)
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
        query = select(DataRequestTemplate).where(
            DataRequestTemplate.company_id == company_id
        )
        
        if active_only:
            query = query.where(DataRequestTemplate.is_active == True)
        
        query = query.order_by(DataRequestTemplate.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
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
        
        query = select(DataRequestField).where(
            DataRequestField.company_id == company_id,
            DataRequestField.is_active == True
        ).order_by(DataRequestField.order)
        
        result = await db.execute(query)
        custom_fields = result.scalars().all()
        
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
        vacancy_config = await db.execute(
            select(VacancyDataRequestConfig).where(
                VacancyDataRequestConfig.vacancy_id == vacancy_id
            )
        )
        vacancy_config = vacancy_config.scalar_one_or_none()
        
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
            vacancy_config = await db.execute(
                select(VacancyDataRequestConfig).where(
                    VacancyDataRequestConfig.vacancy_id == vacancy_id
                )
            )
            vacancy_config = vacancy_config.scalar_one_or_none()
            
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
        
        templates_result = await db.execute(
            select(DataRequestTemplate).where(
                and_(
                    DataRequestTemplate.company_id == company_id,
                    DataRequestTemplate.trigger_stage == stage,
                    DataRequestTemplate.is_active == True,
                    DataRequestTemplate.trigger_type.in_([
                        TriggerType.STAGE_ENTRY,
                        TriggerType.AUTOMATIC
                    ])
                )
            ).order_by(DataRequestTemplate.is_default.desc())
        )
        template = templates_result.scalar_one_or_none()
        
        if template:
            return {
                "source": "company_template",
                "trigger_type": template.trigger_type.value if template.trigger_type else "stage_entry",
                "is_blocking": template.is_blocking or False,
                "template_id": str(template.id),
                "template_name": template.name,
                "fields": template.fields or [],
            }
        
        from app.models.data_request import DEFAULT_STAGE_FIELD_MAPPINGS
        
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
