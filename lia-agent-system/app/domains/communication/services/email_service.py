"""
Email Service for managing email templates and sending emails.
Supports multiple email providers (Resend, SendGrid) with abstraction layer.
"""
import re
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, cast
from uuid import UUID
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate, EmailLog
from app.services.email_providers import (
    EmailProvider,
    EmailResult,
    get_email_provider,
    get_provider_for_client,
    get_all_providers_status
)

logger = logging.getLogger(__name__)

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend")
logger.info(f"Email provider configured: {EMAIL_PROVIDER}")


from .email_templates_data import DEFAULT_TEMPLATES

class EmailService:
    """
    Service for managing email templates and sending emails.

    .. deprecated::
        Legacy class — use ``SendGridEmailService`` for new code.
        This class is kept for backward compatibility with existing callers
        (clients.py, automation.py, report_service.py, etc.) and will be
        removed in a future release.
    """
    
    def __init__(self):
        import warnings
        warnings.warn(
            "EmailService is deprecated. Use SendGridEmailService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.variable_pattern = re.compile(r'\{\{(\w+)\}\}')
    
    def extract_variables(self, text: str) -> List[str]:
        """Extract variable names from a template text."""
        if not text:
            return []
        return list(set(self.variable_pattern.findall(text)))
    
    def render_template(
        self,
        template_text: str,
        variables: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Render a template with the given variables.
        Returns the rendered text and a list of missing variables.
        """
        if not template_text:
            return "", []
        
        missing_vars = []
        result = template_text
        
        for var_name in self.variable_pattern.findall(template_text):
            if var_name in variables:
                value = str(variables[var_name]) if variables[var_name] is not None else ""
                result = result.replace(f"{{{{{var_name}}}}}", value)
            else:
                missing_vars.append(var_name)
        
        return result, missing_vars
    
    async def preview_email(
        self,
        db: AsyncSession,
        template_id: Optional[UUID],
        subject: Optional[str],
        body_html: Optional[str],
        body_text: Optional[str],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Preview an email with variables substituted.
        """
        final_subject = subject
        final_body_html = body_html
        final_body_text = body_text
        
        if template_id:
            result = await db.execute(
                select(EmailTemplate).where(EmailTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Get template values with explicit string conversion for runtime safety
            # Note: SQLAlchemy ORM returns actual Python values at runtime, not Column objects
            subj = getattr(template, 'subject', None)
            html = getattr(template, 'body_html', None)
            text = getattr(template, 'body_text', None)
            template_subject = str(subj) if subj else None
            template_body_html = str(html) if html else None
            template_body_text = str(text) if text else None
            
            if not final_subject and template_subject:
                final_subject = template_subject
            if not final_body_html and template_body_html:
                final_body_html = template_body_html
            if not final_body_text and template_body_text:
                final_body_text = template_body_text
        
        if not final_subject or not final_body_html:
            raise ValueError("Subject and body_html are required")
        
        rendered_subject, subject_missing = self.render_template(str(final_subject), variables)
        rendered_html, html_missing = self.render_template(str(final_body_html), variables)
        rendered_text, text_missing = self.render_template(str(final_body_text) if final_body_text else "", variables)
        
        all_missing = list(set(subject_missing + html_missing + text_missing))
        
        return {
            "subject": rendered_subject,
            "body_html": rendered_html,
            "body_text": rendered_text if rendered_text else None,
            "variables_used": variables,
            "missing_variables": all_missing
        }
    
    async def send_email(
        self,
        db: AsyncSession,
        template_id: UUID,
        recipient_email: str,
        variables: Dict[str, Any],
        candidate_id: Optional[str] = None,
        send_immediately: bool = True,
        created_by: Optional[str] = None,
        subject_override: Optional[str] = None,
        body_override: Optional[str] = None
    ) -> EmailLog:
        """
        Send an email using a template.
        Currently simulates sending and logs the attempt.
        Prepared for future integration with SendGrid, Replit Mail, etc.
        
        Args:
            subject_override: Custom subject that overrides the template subject
            body_override: Custom body HTML that overrides the template body
        """
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Explicit runtime check for is_active
        is_active = bool(template.is_active) if template.is_active is not None else False
        if not is_active:
            raise ValueError(f"Template {template_id} is not active")
        
        # Get template values with explicit string conversion for runtime safety
        # Note: SQLAlchemy ORM returns actual Python values at runtime, not Column objects
        subj = getattr(template, 'subject', None)
        html = getattr(template, 'body_html', None)
        text = getattr(template, 'body_text', None)
        template_subject = str(subj) if subj else ""
        template_body_html = str(html) if html else ""
        template_body_text = str(text) if text else ""
        
        subject_to_use: str = subject_override if subject_override else template_subject
        body_to_use: str = body_override if body_override else template_body_html
        
        rendered_subject, subject_missing = self.render_template(subject_to_use, variables)
        rendered_html, html_missing = self.render_template(body_to_use, variables)
        rendered_text, _ = self.render_template(template_body_text, variables)
        
        all_missing = list(set(subject_missing + html_missing))
        if all_missing:
            logger.warning(f"Missing variables in email: {all_missing}")
        
        email_log = EmailLog(
            id=uuid.uuid4(),
            template_id=template_id,
            candidate_id=candidate_id,
            recipient_email=recipient_email,
            subject=rendered_subject,
            body_html=rendered_html,
            body_text=rendered_text if rendered_text else None,
            status="pending",
            variables_used=variables,
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        
        if send_immediately:
            try:
                success = await self._send_email_provider(
                    to_email=recipient_email,
                    subject=rendered_subject,
                    body_html=rendered_html,
                    body_text=rendered_text
                )
                
                if success:
                    email_log.status = "sent"  # type: ignore[assignment]
                    email_log.sent_at = datetime.utcnow()  # type: ignore[assignment]
                    logger.info(f"Email sent successfully to {recipient_email}")
                else:
                    email_log.status = "failed"  # type: ignore[assignment]
                    email_log.error_message = "Email provider returned failure"  # type: ignore[assignment]
                    logger.error(f"Failed to send email to {recipient_email}")
                    
            except Exception as e:
                email_log.status = "failed"  # type: ignore[assignment]
                email_log.error_message = str(e)  # type: ignore[assignment]
                logger.error(f"Error sending email to {recipient_email}: {e}")
        
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)
        
        return email_log
    
    async def _send_email_provider(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        client_id: Optional[str] = None,
        client_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email using configured provider (Resend or SendGrid).
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML body content
            body_text: Plain text body (optional)
            from_email: Sender email (optional, uses provider default)
            client_id: Optional client ID for per-client provider config
            client_config: Optional client configuration for email provider
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            if client_id and client_config:
                provider = get_provider_for_client(client_id, client_config)
            else:
                provider = get_email_provider()
            
            result = await provider.send_email(
                to=to_email,
                subject=subject,
                html_content=body_html,
                text_content=body_text,
                from_email=from_email
            )
            
            if result.success:
                logger.info(
                    f"Email sent via {result.provider} to {to_email}, "
                    f"ID: {result.message_id}, Status: {result.status}"
                )
                return True
            else:
                logger.error(
                    f"Failed to send email via {result.provider}: "
                    f"{result.error} (code: {result.error_code})"
                )
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
    
    async def send_user_notification(
        self,
        db: AsyncSession,
        notification_type: str,
        recipient_email: str,
        variables: Dict[str, Any]
    ) -> bool:
        """
        Convenience method for sending auth-related notification emails.
        This method sends emails directly without requiring a database template.
        
        Args:
            db: Database session
            notification_type: Type of notification ('invitation', 'password_reset', 'email_verification')
            recipient_email: Email address to send to
            variables: Template variables (user_name, link, etc.)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        NOTIFICATION_CONFIG = {
            "invitation": {
                "subject": "Você foi convidado para a Plataforma LIA",
                "template_name": "Convite de Usuário"
            },
            "password_reset": {
                "subject": "Redefinição de Senha - Plataforma LIA",
                "template_name": "Recuperação de Senha"
            },
            "email_verification": {
                "subject": "Verifique seu Email - Plataforma LIA",
                "template_name": "Verificação de Email"
            }
        }
        
        config = NOTIFICATION_CONFIG.get(notification_type)
        if not config:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        template_data = None
        for t in DEFAULT_TEMPLATES:
            if t["name"] == config["template_name"]:
                template_data = t
                break
        
        if not template_data:
            logger.error(f"Template not found for notification type: {notification_type}")
            return False
        
        rendered_subject, _ = self.render_template(template_data["subject"], variables)
        rendered_html, _ = self.render_template(template_data["body_html"], variables)
        rendered_text, _ = self.render_template(template_data.get("body_text", ""), variables)
        
        try:
            success = await self._send_email_provider(
                to_email=recipient_email,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=rendered_text if rendered_text else None
            )
            
            if success:
                logger.info(f"Notification email ({notification_type}) sent to {recipient_email}")
            else:
                logger.error(f"Failed to send notification email ({notification_type}) to {recipient_email}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending notification email ({notification_type}) to {recipient_email}: {e}")
            return False
    
    async def seed_default_templates(self, db: AsyncSession, created_by: str = "system") -> List[EmailTemplate]:
        """
        Seed the database with default email templates.
        Only creates templates that don't already exist (by name).
        """
        created_templates = []
        
        for template_data in DEFAULT_TEMPLATES:
            result = await db.execute(
                select(EmailTemplate).where(EmailTemplate.name == template_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                template = EmailTemplate(
                    id=uuid.uuid4(),
                    name=template_data["name"],
                    subject=template_data.get("subject"),
                    body_html=template_data["body_html"].strip(),
                    body_text=template_data["body_text"].strip() if template_data.get("body_text") else None,
                    category=template_data.get("category"),
                    channel=template_data.get("channel", "email"),
                    situation=template_data.get("situation"),
                    variables=template_data.get("variables", []),
                    is_active=True,
                    created_by=created_by,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(template)
                created_templates.append(template)
                logger.info(f"Created default template: {template.name}")
        
        if created_templates:
            await db.commit()
            for template in created_templates:
                await db.refresh(template)
        
        return created_templates
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of all configured email providers.
        
        Returns:
            Dictionary with status of each provider including:
            - provider name
            - configured status
            - healthy status
            - from_email
        """
        return get_all_providers_status()
    
    def get_current_provider(self) -> EmailProvider:
        """
        Get the currently configured email provider.
        
        Returns:
            Configured EmailProvider instance
        """
        return get_email_provider()
    
    async def send_welcome_email(
        self,
        client: Any,
        admin_portal_url: str,
        db: AsyncSession
    ) -> bool:
        """
        Send a welcome email to a new client.
        
        Args:
            client: Client object with company_name, primary_email, primary_contact_name attributes
            admin_portal_url: URL for the admin portal
            db: Database session
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        from datetime import datetime as dt
        
        template_data = None
        for t in DEFAULT_TEMPLATES:
            if t["name"] == "Boas-vindas ao Cliente":
                template_data = t
                break
        
        if not template_data:
            logger.error("Template 'Boas-vindas ao Cliente' not found")
            return False
        
        company_name = getattr(client, 'company_name', None) or getattr(client, 'name', 'Empresa')
        admin_name = getattr(client, 'primary_contact_name', None) or getattr(client, 'admin_name', 'Administrador')
        primary_email = getattr(client, 'primary_email', None) or getattr(client, 'email', None)
        
        if not primary_email:
            logger.error("Client does not have a primary_email defined")
            return False
        
        variables = {
            "company_name": company_name,
            "admin_name": admin_name,
            "admin_portal_url": admin_portal_url,
            "support_email": "suporte@wedotalent.com"
        }
        
        rendered_subject, _ = self.render_template(template_data["subject"], variables)
        rendered_html, _ = self.render_template(template_data["body_html"], variables)
        rendered_text, _ = self.render_template(template_data.get("body_text", ""), variables)
        
        try:
            success = await self._send_email_provider(
                to_email=primary_email,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=rendered_text if rendered_text else None
            )
            
            if success:
                logger.info(f"Welcome email sent to {primary_email} for client {company_name}")
                if hasattr(client, 'welcome_email_sent'):
                    client.welcome_email_sent = True
                    client.welcome_email_sent_at = dt.utcnow()
                    try:
                        await db.commit()
                        await db.refresh(client)
                        logger.info(f"✅ Updated welcome_email_sent tracking for client {client.id}")
                    except Exception as tracking_error:
                        logger.warning(f"⚠️ Failed to update welcome_email tracking: {tracking_error}")
            else:
                logger.error(f"Failed to send welcome email to {primary_email}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending welcome email to {primary_email}: {e}")
            return False
    
    async def send_invite_email(
        self,
        client_user: Any,
        accept_url: str,
        inviter_name: str,
        db: AsyncSession
    ) -> bool:
        """
        Send an invitation email to a new user.
        
        Args:
            client_user: ClientUser object with email, name, role, client attributes
            accept_url: URL for accepting the invitation
            inviter_name: Name of the person who sent the invitation
            db: Database session
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        template_data = None
        for t in DEFAULT_TEMPLATES:
            if t["name"] == "Convite para WeDo Talent":
                template_data = t
                break
        
        if not template_data:
            logger.error("Template 'Convite para WeDo Talent' not found")
            return False
        
        user_email = getattr(client_user, 'email', None)
        user_name = getattr(client_user, 'name', None) or getattr(client_user, 'full_name', 'Usuário')
        role_name = getattr(client_user, 'role', None) or getattr(client_user, 'role_name', 'Membro')
        
        client = getattr(client_user, 'client', None)
        company_name = "WeDo Talent"
        if client:
            company_name = getattr(client, 'company_name', None) or getattr(client, 'name', company_name)
        
        invitation = getattr(client_user, 'invitation', None)
        expires_at = "7 dias"
        if invitation:
            expires_at_dt = getattr(invitation, 'expires_at', None)
            if expires_at_dt:
                expires_at = expires_at_dt.strftime("%d/%m/%Y às %H:%M")
        
        if not user_email:
            logger.error("ClientUser does not have an email defined")
            return False
        
        variables = {
            "user_name": user_name,
            "company_name": company_name,
            "inviter_name": inviter_name,
            "accept_url": accept_url,
            "role_name": str(role_name).replace('_', ' ').title() if role_name else "Membro",
            "expires_at": expires_at
        }
        
        rendered_subject, _ = self.render_template(template_data["subject"], variables)
        rendered_html, _ = self.render_template(template_data["body_html"], variables)
        rendered_text, _ = self.render_template(template_data.get("body_text", ""), variables)
        
        try:
            success = await self._send_email_provider(
                to_email=user_email,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=rendered_text if rendered_text else None
            )
            
            if success:
                logger.info(f"Invite email sent to {user_email} for company {company_name}")
            else:
                logger.error(f"Failed to send invite email to {user_email}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending invite email to {user_email}: {e}")
            return False


email_service = EmailService()

from app.domains.communication.schemas.email_schemas import (
    SendGridEmailStatus,
    EmailRecipient,
    EmailAttachment,
    SendEmailRequest,
    SendTemplateEmailRequest,
    BulkEmailRecipient,
    SendBulkEmailRequest,
    EmailSendResult,
    BulkEmailResult,
)

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_SDK_AVAILABLE = True
except ImportError:
    SENDGRID_SDK_AVAILABLE = False
    SendGridAPIClient = None


import asyncio


class SendGridEmailService:
    """
    SendGrid-based Email Service for LIA Platform.
    
    Features:
    - Development mode: logs emails without sending
    - Production mode: sends via SendGrid API
    - Template support using EmailTemplates from communication_templates.py
    - Bulk email with personalization
    - Status tracking: sent, delivered, failed
    
    Environment Variables:
    - SENDGRID_API_KEY: SendGrid API key
    - SENDGRID_FROM_EMAIL: Sender email (default: noreply@wedotalent.com)
    - SENDGRID_FROM_NAME: Sender name (default: WeDo Talent)
    - ENVIRONMENT: 'development' for logging only, 'production' for real sending
    """
    
    def __init__(self):
        self.api_key = os.environ.get("SENDGRID_API_KEY")
        self.from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@wedotalent.com")
        self.from_name = os.environ.get("SENDGRID_FROM_NAME", "WeDo Talent")
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self._client = None
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local", "test")
    
    @property
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured."""
        return bool(self.api_key) and SENDGRID_SDK_AVAILABLE
    
    @property
    def client(self):
        """Lazy initialization of SendGrid client."""
        if self._client is None and self.is_configured:
            self._client = SendGridAPIClient(self.api_key)
        return self._client
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailSendResult:
        """
        Send a single email via SendGrid.
        
        In development mode, logs the email without actual sending.
        In production mode, sends via SendGrid API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            to_name: Optional recipient name
            body_html: Optional HTML body
            cc: Optional list of CC emails
            bcc: Optional list of BCC emails
            reply_to: Optional reply-to address
            categories: Optional SendGrid categories for tracking
            metadata: Optional custom metadata
        
        Returns:
            EmailSendResult with success status, message_id, and error details
        """
        if self.is_development:
            return await self._send_development(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=body,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                metadata=metadata
            )
        
        return await self._send_production(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            body_html=body_html,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            categories=categories,
            metadata=metadata
        )
    
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict[str, Any],
        to_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailSendResult:
        """
        Send an email using a predefined template from EmailTemplates.
        
        Args:
            to_email: Recipient email address
            template_name: Name of the template method in EmailTemplates
            template_data: Dictionary of variables for template rendering
            to_name: Optional recipient name
            cc: Optional CC recipients
            reply_to: Optional reply-to address
            categories: Optional SendGrid categories
            metadata: Optional custom metadata
        
        Returns:
            EmailSendResult with success status and message_id
        """
        from app.templates.communication_templates import EmailTemplates
        
        template_method = getattr(EmailTemplates, template_name, None)
        if not template_method:
            return EmailSendResult(
                success=False,
                status="failed",
                error=f"Template not found: {template_name}",
                error_code="TEMPLATE_NOT_FOUND"
            )
        
        try:
            template_result = template_method(**template_data)
            subject = template_result.get("subject", "")
            body = template_result.get("body", "")
        except TypeError as e:
            logger.error(f"Template {template_name} parameter error: {e}")
            return EmailSendResult(
                success=False,
                status="failed",
                error=f"Template parameter error: {str(e)}",
                error_code="TEMPLATE_PARAM_ERROR"
            )
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return EmailSendResult(
                success=False,
                status="failed",
                error=f"Template rendering error: {str(e)}",
                error_code="TEMPLATE_ERROR"
            )
        
        enriched_metadata = {
            **(metadata or {}),
            "template_name": template_name,
            "template_data": template_data
        }
        
        return await self.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            cc=cc,
            reply_to=reply_to,
            categories=categories or [template_name],
            metadata=enriched_metadata
        )
    
    async def send_bulk_email(
        self,
        recipients: List[BulkEmailRecipient],
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BulkEmailResult:
        """
        Send bulk emails to multiple recipients with optional personalization.
        
        Emails are sent sequentially with a small delay to avoid rate limits.
        In development mode, logs all emails without sending.
        
        Args:
            recipients: List of BulkEmailRecipient with email, name, and personalization
            subject: Email subject (can contain {{variable}} placeholders)
            body: Plain text body (can contain {{variable}} placeholders)
            body_html: Optional HTML body
            categories: Optional SendGrid categories
            metadata: Optional custom metadata
        
        Returns:
            BulkEmailResult with total, successful, failed counts and individual results
        """
        results: List[EmailSendResult] = []
        
        for recipient in recipients:
            personalized_subject = subject
            personalized_body = body
            personalized_html = body_html
            
            if recipient.personalization:
                for key, value in recipient.personalization.items():
                    placeholder = f"{{{{{key}}}}}"
                    personalized_subject = personalized_subject.replace(placeholder, str(value))
                    personalized_body = personalized_body.replace(placeholder, str(value))
                    if personalized_html:
                        personalized_html = personalized_html.replace(placeholder, str(value))
            
            recipient_metadata = {
                **(metadata or {}),
                "bulk_send": True,
                "personalization": recipient.personalization
            }
            
            result = await self.send_email(
                to_email=recipient.email,
                to_name=recipient.name,
                subject=personalized_subject,
                body=personalized_body,
                body_html=personalized_html,
                categories=categories,
                metadata=recipient_metadata
            )
            results.append(result)
            
            await asyncio.sleep(0.1)
        
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        return BulkEmailResult(
            total=len(recipients),
            successful=successful,
            failed=failed,
            results=results
        )
    
    async def _send_development(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailSendResult:
        """Send email in development mode (logging only, no real sending)."""
        message_id = f"dev_sg_{uuid.uuid4().hex[:12]}"
        
        logger.info("=" * 70)
        logger.info("[DEV EMAIL - SENDGRID] Email enviado (modo desenvolvimento)")
        logger.info(f"[DEV EMAIL] Message ID: {message_id}")
        logger.info(f"[DEV EMAIL] De: {self.from_name} <{self.from_email}>")
        logger.info(f"[DEV EMAIL] Para: {to_name or 'N/A'} <{to_email}>")
        if cc:
            logger.info(f"[DEV EMAIL] CC: {', '.join(cc)}")
        if bcc:
            logger.info(f"[DEV EMAIL] BCC: {', '.join(bcc)}")
        logger.info(f"[DEV EMAIL] Assunto: {subject}")
        logger.info(f"[DEV EMAIL] Corpo ({len(body)} caracteres):")
        preview = body[:500] + ("..." if len(body) > 500 else "")
        for line in preview.split('\n'):
            logger.info(f"[DEV EMAIL] {line}")
        if metadata:
            logger.info(f"[DEV EMAIL] Metadata: {metadata}")
        logger.info("=" * 70)
        
        return EmailSendResult(
            success=True,
            message_id=message_id,
            status="sent",
            provider="development",
            sent_at=datetime.utcnow(),
            metadata={
                "mode": "development",
                "to_email": to_email,
                "subject": subject
            }
        )
    
    async def _send_production(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailSendResult:
        """Send email via SendGrid API in production mode."""
        if not SENDGRID_SDK_AVAILABLE:
            logger.warning("SendGrid SDK not installed")
            return EmailSendResult(
                success=False,
                status="failed",
                error="SendGrid SDK not installed. Run: pip install sendgrid",
                error_code="SDK_NOT_AVAILABLE"
            )
        
        if not self.is_configured:
            logger.warning("SendGrid not configured - falling back to development mode")
            return await self._send_development(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=body,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                metadata=metadata
            )
        
        try:
            from_email_obj = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email, to_name)
            
            message = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            if body_html:
                message.add_content(Content("text/html", body_html))
            
            if reply_to:
                message.reply_to = Email(reply_to)
            
            if categories:
                for category in categories:
                    message.add_category(category)

            if metadata:
                from sendgrid.helpers.mail import CustomArg
                for key, value in metadata.items():
                    message.add_custom_arg(CustomArg(key=str(key), value=str(value)))

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.send(message)
            )
            
            message_id = None
            if response.headers:
                message_id = response.headers.get("X-Message-Id")
            if not message_id:
                message_id = f"sg_{uuid.uuid4().hex[:12]}"
            
            status_code = response.status_code
            
            if 200 <= status_code < 300:
                logger.info(f"[SENDGRID] Email sent to: {to_email}, ID: {message_id}")
                return EmailSendResult(
                    success=True,
                    message_id=message_id,
                    status="sent",
                    provider="sendgrid",
                    sent_at=datetime.utcnow(),
                    metadata={
                        "status_code": status_code,
                        "to_email": to_email
                    }
                )
            else:
                logger.error(f"[SENDGRID] Failed: {to_email}, status: {status_code}")
                return EmailSendResult(
                    success=False,
                    status="failed",
                    provider="sendgrid",
                    error=f"SendGrid returned status {status_code}",
                    error_code=str(status_code)
                )
        
        except Exception as e:
            logger.error(f"[SENDGRID] Error sending to {to_email}: {e}", exc_info=True)
            return EmailSendResult(
                success=False,
                status="failed",
                provider="sendgrid",
                error=str(e),
                error_code=type(e).__name__
            )
    
    async def check_status(self, message_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Check email delivery status.
        
        Note: SendGrid requires Event Webhooks for real-time delivery status.
        This method returns basic status info only.
        
        Args:
            message_id: The message ID to check
        
        Returns:
            Tuple of (status, additional_data)
        """
        if message_id.startswith("dev_"):
            return "delivered", {
                "provider": "development",
                "note": "Development emails are always marked as delivered"
            }
        
        return "sent", {
            "provider": "sendgrid",
            "message_id": message_id,
            "note": "SendGrid status tracking requires Event Webhook configuration. "
                    "Configure at: https://app.sendgrid.com/settings/mail_settings/event_webhook"
        }


sendgrid_email_service = SendGridEmailService()
