# ADR-001-EXEMPT: information_schema metadata query (table existence check),
# not domain data — repository layer not applicable.
"""
Email Service for managing email templates and sending emails.
Supports multiple email providers (Mailgun primary, Resend fallback) with abstraction layer.
"""
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.email_providers import (
    EmailProvider,
    get_all_providers_status,
    get_email_provider,
    get_provider_for_client,
)
from app.domains.communication.services.email_providers import (
    FallbackEmailProvider as _FallbackEmailProvider,
)
from app.domains.communication.services.email_providers import (
    MailgunProvider as _DomainMailgunProvider,
)
from app.domains.communication.services.email_providers import (
    ResendProvider as _DomainResendProvider,
)
from lia_models.email_template import EmailLog, EmailTemplate

logger = logging.getLogger(__name__)

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "mailgun")
# pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
logger.info(f"Email provider configured: {EMAIL_PROVIDER}")


from .email_templates_data import DEFAULT_TEMPLATES


class EmailService:
    """
    Service for managing email templates and sending emails.

    .. deprecated::
        Legacy class — use ``MailgunProvider`` via ``get_email_provider()`` for new code.
        This class is kept for backward compatibility with existing callers
        (clients.py, automation.py, report_service.py, etc.) and will be
        removed in a future release.
    """

    def __init__(self):
        import warnings
        warnings.warn(
            "EmailService is deprecated. Use get_email_provider() with MailgunProvider instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.variable_pattern = re.compile(r'\{\{(\w+)\}\}')
    
    def extract_variables(self, text: str) -> list[str]:
        """Extract variable names from a template text."""
        if not text:
            return []
        return list(set(self.variable_pattern.findall(text)))
    
    def render_template(
        self,
        template_text: str,
        variables: dict[str, Any]
    ) -> tuple[str, list[str]]:
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
        template_id: UUID | None,
        subject: str | None,
        body_html: str | None,
        body_text: str | None,
        variables: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Preview an email with variables substituted.
        """
        final_subject = subject
        final_body_html = body_html
        final_body_text = body_text
        
        if template_id:
            # TENANT-EXEMPT: legacy preview path — template_id is UUID-unique.
            # Postgres RLS (Task #1143) enforces tenant boundary at DB level.
            # TODO(harness): migrate preview_email signature to accept company_id
            # and pass it via EmailTemplateRepository.get_active_by_id().
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
        variables: dict[str, Any],
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        send_immediately: bool = True,
        created_by: str | None = None,
        subject_override: str | None = None,
        body_override: str | None = None,
        cc: list[str] | None = None,
    ) -> EmailLog:
        """
        Send an email using a template.
        Currently simulates sending and logs the attempt.
        Prepared for future integration with Mailgun, Resend, etc.
        
        Args:
            subject_override: Custom subject that overrides the template subject
            body_override: Custom body HTML that overrides the template body
        """
        # TENANT-EXEMPT: legacy send path — template_id is UUID-unique.
        # Postgres RLS (Task #1143) enforces tenant boundary at DB level.
        # TODO(harness): migrate send_email signature to accept company_id
        # and pass it via EmailTemplateRepository.get_active_by_id().
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if template:
            is_active = bool(template.is_active) if template.is_active is not None else False
            if not is_active:
                raise ValueError(f"Template {template_id} is not active")
            subj = getattr(template, 'subject', None)
            html = getattr(template, 'body_html', None)
            text = getattr(template, 'body_text', None)
            template_subject = str(subj) if subj else ""
            template_body_html = str(html) if html else ""
            template_body_text = str(text) if text else ""
            if cc is None:
                raw_cc = getattr(template, 'cc_emails', None)
                if raw_cc:
                    cc = [str(e) for e in raw_cc if e]
        else:
            logger.warning(
                f"Template {template_id} not found — using overrides or default fallback"
            )
            template_subject = ""
            template_body_html = ""
            template_body_text = ""
        
        subject_to_use: str = subject_override if subject_override else template_subject
        body_to_use: str = body_override if body_override else template_body_html

        if not subject_to_use:
            subject_to_use = "Notificação — WeDOTalent"
        if not body_to_use:
            candidate_name = variables.get("candidate_name", "")
            body_to_use = f"<p>Olá{(' ' + candidate_name) if candidate_name else ''},</p><p>Esta é uma notificação do WeDOTalent.</p>"
        
        rendered_subject, subject_missing = self.render_template(subject_to_use, variables)
        rendered_html, html_missing = self.render_template(body_to_use, variables)
        rendered_text, _ = self.render_template(template_body_text, variables)
        
        all_missing = list(set(subject_missing + html_missing))
        if all_missing:
            logger.warning(f"Missing variables in email: {all_missing}")
            # P1-W2-02: never send {{placeholder}} literals to candidates
            if send_immediately:
                raise ValueError(
                    f"Email has {len(all_missing)} unresolved variable(s): {all_missing}. "
                    "Provide values for all template {{placeholders}} before sending. "
                    "Callers: catch ValueError and surface missing_variables to the user."
                )

        # Wave 3 P0.SIG2: append tenant signature canonical (was ghost setting — wired here).
        # Tenant comes from ContextVar (auth middleware); silent skip if unauthenticated context.
        try:
            from app.middleware.auth_enforcement import _current_company_id
            from app.shared.services.communication_settings_consumer import (
                get_company_communication_settings,
                append_signature_to_body,
            )
            _company_id = _current_company_id.get("")
            if _company_id:
                _settings = await get_company_communication_settings(db, _company_id)
                rendered_html = append_signature_to_body(rendered_html, _settings, html=True)
                if rendered_text:
                    rendered_text = append_signature_to_body(rendered_text, _settings, html=False)
        except Exception as _sig_exc:
            logger.debug("[EmailService] signature append skipped: %s", _sig_exc)

        email_log = EmailLog(
            id=uuid.uuid4(),
            template_id=template_id if template else None,
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
                # GAP-07-008: build RFC 2822 threading headers when candidate context is available
                _threading_headers: dict = {}
                if candidate_id:
                    from app.domains.communication.services.email_threading import build_threading_headers
                    _company_ctx = ""
                    try:
                        from app.middleware.auth_enforcement import _current_company_id
                        _company_ctx = _current_company_id.get("") or ""
                    except Exception:
                        pass
                    _threading_headers = build_threading_headers(
                        candidate_id=candidate_id,
                        company_id=_company_ctx or "unknown",
                        vacancy_id=vacancy_id,
                    )
                success = await self._send_email_provider(
                    to_email=recipient_email,
                    subject=rendered_subject,
                    body_html=rendered_html,
                    body_text=rendered_text,
                    cc=cc or None,
                    headers=_threading_headers or None,
                )
                
                if success:
                    email_log.status = "sent"  # type: ignore[assignment]
                    email_log.sent_at = datetime.utcnow()  # type: ignore[assignment]
                    logger.info("Email sent successfully")
                else:
                    email_log.status = "failed"  # type: ignore[assignment]
                    email_log.error_message = "Email provider returned failure"  # type: ignore[assignment]
                    logger.error("Failed to send email")
                    
            except Exception as e:
                email_log.status = "failed"  # type: ignore[assignment]
                email_log.error_message = str(e)  # type: ignore[assignment]
                logger.error(f"Error sending email: {e}")
        
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)
        
        return email_log
    
    async def _send_email_provider(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
        from_email: str | None = None,
        client_id: str | None = None,
        client_config: dict[str, Any] | None = None,
        cc: list[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bool:
        """
        Send email using Mailgun as primary provider with automatic Resend fallback.

        Uses FallbackEmailProvider to compose Mailgun+Resend into a single
        circuit-breaker-aware call. If MAILGUN_CIRCUIT opens or Mailgun returns
        a failure, FallbackEmailProvider automatically retries via Resend
        (when RESEND_CIRCUIT is closed and RESEND_API_KEY is set).

        In development/test environments, falls back to logging when no
        provider is configured or all providers fail.

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
        env = os.getenv("ENVIRONMENT", "development").lower()
        is_dev = env in ("development", "dev", "local", "test")

        try:
            if client_id and client_config:
                provider: EmailProvider = get_provider_for_client(client_id, client_config)
            else:
                mailgun = _DomainMailgunProvider()
                resend = _DomainResendProvider()
                provider = _FallbackEmailProvider(primary=mailgun, fallback=resend)

            result = await provider.send_email(
                to=to_email,
                subject=subject,
                html_content=body_html,
                text_content=body_text,
                from_email=from_email,
                cc=cc,
                headers=headers,
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
                if is_dev:
                    return self._log_dev_email(to_email, subject, body_html, body_text)
                return False

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            if is_dev:
                return self._log_dev_email(to_email, subject, body_html, body_text)
            raise

    def _log_dev_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> bool:
        logger.info("=" * 70)
        logger.info("[DEV EMAIL] Email logged (development mode fallback)")
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"[DEV EMAIL] To: {to_email}")
        logger.info(f"[DEV EMAIL] Subject: {subject}")
        logger.info(f"[DEV EMAIL] Body ({len(body_html)} chars): {body_html[:200]}")
        logger.info("=" * 70)
        return True
    
    async def send_user_notification(
        self,
        db: AsyncSession,
        notification_type: str,
        recipient_email: str,
        variables: dict[str, Any]
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
                "subject": "Você foi convidado para o WeDOTalent",
                "template_name": "Convite de Usuário"
            },
            "password_reset": {
                "subject": "Redefinição de Senha — WeDOTalent",
                "template_name": "Recuperação de Senha"
            },
            "email_verification": {
                "subject": "Verifique seu Email — WeDOTalent",
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
                logger.info(f"Notification email ({notification_type}) sent")
            else:
                logger.error(f"Failed to send notification email ({notification_type})")
            
            return success
        except Exception as e:
            logger.error(f"Error sending notification email ({notification_type}): {e}")
            return False
    
    async def seed_default_templates(self, db: AsyncSession, created_by: str = "system") -> list[EmailTemplate]:
        """
        Seed the database with default email templates.
        Only creates templates that don't already exist (by name).
        """
        created_templates = []

        for template_data in DEFAULT_TEMPLATES:
            # TENANT-EXEMPT: seed_default_templates is a platform-wide setup helper
            # that creates SYSTEM templates (cross-tenant by design — same template
            # name should exist exactly once platform-wide). Caller is admin-only
            # bootstrap script, not a user-facing flow.
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
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Created default template: {template.name}")
        
        if created_templates:
            await db.commit()
            for template in created_templates:
                await db.refresh(template)
        
        return created_templates
    
    async def create_template(
        self,
        db: AsyncSession,
        name: str,
        body_html: str,
        subject: str | None = None,
        body_text: str | None = None,
        category: str = "custom",
        channel: str = "email",
        variables: list | None = None,
        company_id: str | None = None,
        created_by: str = "system",
    ) -> EmailTemplate:
        """
        Create a new email template in the database.

        Includes DB timeout handling (5 s per operation) and table existence
        verification to prevent hangs on missing migrations.

        Args:
            db: Database session
            name: Template name (must be unique per company)
            body_html: HTML content of the template
            subject: Email subject line (optional for WhatsApp templates)
            body_text: Plain text fallback
            category: Template category (default: "custom")
            channel: Communication channel — "email" or "whatsapp"
            variables: List of variable names used in the template
            company_id: Owning company (tenant isolation)
            created_by: User ID who created the template

        Returns:
            The created EmailTemplate instance

        Raises:
            ValueError: If a template with the same name already exists
            RuntimeError: If the email_templates table does not exist
            TimeoutError: If any DB operation exceeds 5 seconds
        """
        import asyncio

        from sqlalchemy import text

        table_check = await asyncio.wait_for(
            db.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'email_templates' LIMIT 1"
            )),
            timeout=5.0,
        )
        if not table_check.fetchone():
            raise RuntimeError(
                "email_templates table does not exist. Run database migrations first."
            )

        existing = await asyncio.wait_for(
            db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.name == name,
                    EmailTemplate.company_id == company_id,
                )
            ),
            timeout=5.0,
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Template with name '{name}' already exists")

        extracted_vars = variables or []
        if not extracted_vars:
            all_text = (subject or "") + body_html + (body_text or "")
            extracted_vars = self.extract_variables(all_text)

        template = EmailTemplate(
            id=uuid.uuid4(),
            name=name,
            subject=subject,
            body_html=body_html.strip(),
            body_text=body_text.strip() if body_text else None,
            category=category,
            channel=channel,
            variables=extracted_vars,
            is_active=True,
            company_id=company_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(template)
        await asyncio.wait_for(db.commit(), timeout=5.0)
        await asyncio.wait_for(db.refresh(template), timeout=5.0)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created template: {template.name} (id={template.id}, company={company_id})")
        return template

    def get_provider_status(self) -> dict[str, Any]:
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
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Welcome email sent to {primary_email} for client {company_name}")
                if hasattr(client, 'welcome_email_sent'):
                    client.welcome_email_sent = True
                    client.welcome_email_sent_at = dt.utcnow()
                    try:
                        await db.commit()
                        await db.refresh(client)
                        logger.info(f"✅ Updated welcome_email_sent tracking for client {client.id}")
                    except Exception as tracking_error:
                        try:
                            await db.rollback()
                        except Exception as rb_err:
                            logger.debug("[email] db.rollback() also failed during tracking update: %s", rb_err)
                        logger.warning(f"⚠️ Failed to update welcome_email tracking: {tracking_error}")
            else:
                # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
                logger.error(f"Failed to send welcome email to {primary_email}")
            
            return success
        except Exception as e:
            try:
                await db.rollback()
            except Exception as rb_err:
                logger.debug("[email] db.rollback() also failed during welcome email: %s", rb_err)
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"Invite email sent to {user_email} for company {company_name}")
            else:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.error(f"Failed to send invite email to {user_email}")
            
            return success
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"Error sending invite email to {user_email}: {e}")
            return False


email_service = EmailService()

import asyncio

from app.domains.communication.schemas.email_schemas import (
    BulkEmailRecipient,
    BulkEmailResult,
    EmailSendResult,
)


class MailgunEmailService:
    """
    Mailgun-based Email Service for LIA Platform.

    Features:
    - Development mode: logs emails without sending
    - Production mode: sends via Mailgun HTTP API
    - Template support using EmailTemplates from communication_templates.py
    - Bulk email with personalization
    - Status tracking: sent, delivered, failed

    Environment Variables:
    - MAILGUN_API_KEY: Mailgun API key (required)
    - MAILGUN_DOMAIN: Mailgun sending domain (required)
    - MAILGUN_FROM_EMAIL: Sender email (default: noreply@wedotalent.com)
    - MAILGUN_FROM_NAME: Sender name (default: WeDo Talent)
    - MAILGUN_API_BASE: Mailgun API base URL (default: https://api.mailgun.net/v3)
    - ENVIRONMENT: 'development' for logging only, 'production' for real sending
    """

    def __init__(self):
        self.api_key = os.environ.get("MAILGUN_API_KEY")
        self.domain = os.environ.get("MAILGUN_DOMAIN")
        self.from_email = os.environ.get("MAILGUN_FROM_EMAIL", "noreply@wedotalent.com")
        self.from_name = os.environ.get("MAILGUN_FROM_NAME", "WeDo Talent")
        self.api_base = os.environ.get("MAILGUN_API_BASE", "https://api.mailgun.net/v3")
        self.environment = os.environ.get("ENVIRONMENT", "development")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local", "test")

    @property
    def is_configured(self) -> bool:
        """Check if Mailgun is properly configured."""
        return bool(self.api_key) and bool(self.domain)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: str | None = None,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> EmailSendResult:
        """
        Send a single email via Mailgun.

        In development mode, logs the email without actual sending.
        In production mode, sends via Mailgun HTTP API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            to_name: Optional recipient name
            body_html: Optional HTML body
            cc: Optional list of CC emails
            bcc: Optional list of BCC emails
            reply_to: Optional reply-to address
            categories: Optional tracking tags
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
        template_data: dict[str, Any],
        to_name: str | None = None,
        cc: list[str] | None = None,
        reply_to: str | None = None,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None
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
            categories: Optional tracking tags
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Template {template_name} parameter error: {e}")
            return EmailSendResult(
                success=False,
                status="failed",
                error=f"Template parameter error: {str(e)}",
                error_code="TEMPLATE_PARAM_ERROR"
            )
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        recipients: list[BulkEmailRecipient],
        subject: str,
        body: str,
        body_html: str | None = None,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None
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
            categories: Optional tracking tags
            metadata: Optional custom metadata

        Returns:
            BulkEmailResult with total, successful, failed counts and individual results
        """
        results: list[EmailSendResult] = []

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
        to_name: str | None = None,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> EmailSendResult:
        """Send email in development mode (logging only, no real sending)."""
        message_id = f"dev_mg_{uuid.uuid4().hex[:12]}"

        logger.info("=" * 70)
        logger.info("[DEV EMAIL - MAILGUN] Email enviado (modo desenvolvimento)")
        logger.info(f"[DEV EMAIL] Message ID: {message_id}")
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[DEV EMAIL] De: {self.from_name} <{self.from_email}>")
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
        to_name: str | None = None,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> EmailSendResult:
        """Send email via Mailgun HTTP API with automatic Resend fallback.

        If Mailgun is not configured, the MAILGUN_CIRCUIT is open, or Mailgun returns
        a failure, the service automatically retries via Resend (if RESEND_API_KEY is set).
        Only falls back to development logging as a last resort.
        """
        from app.shared.resilience.circuit_breaker import (
            MAILGUN_CIRCUIT,
            RESEND_CIRCUIT,
            CircuitState,
        )

        mailgun_circuit_open = MAILGUN_CIRCUIT.state == CircuitState.OPEN

        if mailgun_circuit_open:
            logger.warning(
                "[MAILGUN] Circuit is OPEN — routing to Resend fallback immediately"
            )
        elif not self.is_configured:
            logger.warning(
                "Mailgun not configured (MAILGUN_API_KEY/MAILGUN_DOMAIN missing) — trying Resend fallback"
            )

        mailgun_result: EmailSendResult | None = None

        if self.is_configured and not mailgun_circuit_open:
            try:
                import httpx

                sender = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
                to_addr = f"{to_name} <{to_email}>" if to_name else to_email

                data: dict[str, Any] = {
                    "from": sender,
                    "to": to_addr,
                    "subject": subject,
                    "text": body,
                }

                if body_html:
                    data["html"] = body_html
                if reply_to:
                    data["h:Reply-To"] = reply_to
                if cc:
                    data["cc"] = ",".join(cc)
                if bcc:
                    data["bcc"] = ",".join(bcc)
                if categories:
                    for tag in categories:
                        data.setdefault("o:tag", [])
                        if isinstance(data["o:tag"], list):
                            data["o:tag"].append(tag)
                if metadata:
                    for key, value in metadata.items():
                        data[f"v:{key}"] = str(value)

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{self.api_base}/{self.domain}/messages",
                        auth=("api", self.api_key),
                        data=data,
                    )

                if response.status_code == 200:
                    payload = response.json()
                    message_id = payload.get("id", f"mg_{uuid.uuid4().hex[:12]}")
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"[MAILGUN] Email sent to: {to_email}, ID: {message_id}")
                    return EmailSendResult(
                        success=True,
                        message_id=message_id,
                        status="sent",
                        provider="mailgun",
                        sent_at=datetime.utcnow(),
                        metadata={
                            "status_code": response.status_code,
                            "to_email": to_email
                        }
                    )
                else:
                    logger.error(
                        f"[MAILGUN] Failed: {to_email}, status: {response.status_code} — "
                        "will attempt Resend fallback"
                    )
                    mailgun_result = EmailSendResult(
                        success=False,
                        status="failed",
                        provider="mailgun",
                        error=f"Mailgun returned status {response.status_code}: {response.text}",
                        error_code=str(response.status_code)
                    )

            except Exception as e:
                logger.error(
                    f"[MAILGUN] Error sending to {to_email}: {e} — will attempt Resend fallback",
                    exc_info=True
                )
                mailgun_result = EmailSendResult(
                    success=False,
                    status="failed",
                    provider="mailgun",
                    error=str(e),
                    error_code=type(e).__name__
                )

        resend_circuit_open = RESEND_CIRCUIT.state == CircuitState.OPEN
        resend_api_key = os.environ.get("RESEND_API_KEY")

        if resend_api_key and not resend_circuit_open:
            try:
                resend_result = await self._send_via_resend_fallback(
                    to_email=to_email,
                    to_name=to_name,
                    subject=subject,
                    body=body,
                    body_html=body_html,
                    cc=cc,
                    bcc=bcc,
                    reply_to=reply_to,
                    metadata=metadata,
                )
                if resend_result.success:
                    logger.info(
                        f"[RESEND FALLBACK] Email delivered to {to_email}, "
                        f"ID: {resend_result.message_id}"
                    )
                    return resend_result
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.error(f"[RESEND FALLBACK] Also failed for {to_email}: {resend_result.error}")
            except Exception as exc:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.error(f"[RESEND FALLBACK] Exception for {to_email}: {exc}", exc_info=True)
        elif resend_circuit_open:
            logger.warning("[RESEND] Circuit is OPEN — both providers unavailable")
        elif not resend_api_key:
            logger.warning("[RESEND] RESEND_API_KEY not set — no fallback provider available")

        if mailgun_result is not None:
            return mailgun_result

        logger.warning(
            "All email providers unavailable — falling back to development logging for %s",
            to_email
        )
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

    async def _send_via_resend_fallback(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: str | None = None,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmailSendResult:
        """Send via Resend as automatic fallback when Mailgun is unavailable."""
        try:
            import resend as resend_sdk
        except ImportError:
            return EmailSendResult(
                success=False,
                status="failed",
                provider="resend",
                error="Resend SDK not installed",
                error_code="IMPORT_ERROR"
            )

        resend_api_key = os.environ.get("RESEND_API_KEY")
        resend_from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        resend_from_name = os.environ.get("RESEND_FROM_NAME", self.from_name)

        resend_sdk.api_key = resend_api_key

        sender = f"{resend_from_name} <{resend_from_email}>" if resend_from_name else resend_from_email

        params: dict[str, Any] = {
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": body_html or f"<pre>{body}</pre>",
        }

        if body:
            params["text"] = body
        if reply_to:
            params["reply_to"] = reply_to
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc

        import asyncio as _asyncio
        response = await _asyncio.to_thread(resend_sdk.Emails.send, params)

        if response and response.get("id"):
            return EmailSendResult(
                success=True,
                message_id=response["id"],
                status="sent",
                provider="resend_fallback",
                sent_at=datetime.utcnow(),
                metadata={"fallback": True, "primary_provider": "mailgun"}
            )

        return EmailSendResult(
            success=False,
            status="failed",
            provider="resend_fallback",
            error=f"Resend returned unexpected response: {response}",
            error_code="UNEXPECTED_RESPONSE"
        )

    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any]]:
        """
        Check email delivery status.

        Note: Mailgun requires Event Webhooks for real-time delivery status.
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
            "provider": "mailgun",
            "message_id": message_id,
            "note": "Mailgun status tracking requires Event Webhook configuration."
        }


mailgun_email_service = MailgunEmailService()


def get_email_service() -> "EmailService":
    """Returns the module-level singleton (no new DeprecationWarning emitted)."""
    return email_service


def get_mailgun_email_service() -> "MailgunEmailService":
    """Returns the MailgunEmailService singleton."""
    return mailgun_email_service
