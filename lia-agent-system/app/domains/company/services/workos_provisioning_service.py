"""
WorkOS Organization Provisioning Service.

Automatically provisions WorkOS Organizations when new clients are created.
"""
import logging
import os

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from workos import WorkOSClient

from app.auth.workos_models import CompanyWorkOSConfig
from app.domains.company.repositories.tenant_repository import TenantRepository
from lia_models.client_account import ClientAccount

logger = logging.getLogger(__name__)


def extract_domain_from_email(email: str | None) -> str | None:
    """
    Extract domain from an email address.
    
    Args:
        email: Email address (e.g., "admin@empresa.com")
    
    Returns:
        Domain string (e.g., "empresa.com") or None if invalid
    """
    if not email or "@" not in email:
        return None
    
    try:
        domain = email.split("@")[1].strip().lower()
        if domain and "." in domain:
            return domain
        return None
    except Exception:
        return None


async def provision_workos_organization(
    client: ClientAccount,
    db: AsyncSession
) -> str | None:
    """
    Provision a WorkOS Organization for a new client.
    
    Creates an Organization in WorkOS and updates the CompanyWorkOSConfig
    with the organization_id.
    
    Args:
        client: The ClientAccount that was just created
        db: Database session
    
    Returns:
        organization_id if successful, None otherwise
    
    Note:
        This function handles errors gracefully - if WorkOS fails,
        the client is still created successfully.
    """
    api_key = os.getenv("WORKOS_API_KEY")
    
    if not api_key:
        logger.warning("⚠️ WORKOS_API_KEY not configured - skipping WorkOS Organization provisioning")
        return None
    
    try:
        workos = WorkOSClient(api_key=api_key)
        
        domains = []
        domain = extract_domain_from_email(client.primary_email)
        if domain:
            domains.append(domain)
        
        org_name = client.name or client.trade_name or f"Client-{client.id}"
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"🔄 Creating WorkOS Organization for client: {org_name}")
        
        if domains:
            org = workos.organizations.create_organization(
                name=org_name,
                domains=domains
            )
        else:
            org = workos.organizations.create_organization(
                name=org_name
            )
        
        organization_id = org.id
        
        client_id_str = str(client.id)
        
        stmt = (
            update(CompanyWorkOSConfig)
            .where(CompanyWorkOSConfig.company_id == client_id_str)
            .values(workos_organization_id=organization_id)
        )
        await db.execute(stmt)
        await db.commit()
        
        config = await TenantRepository(db).get_workos_config_by_company(
            client_id_str
        )
        
        if config:
            await db.refresh(config)
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ CompanyWorkOSConfig updated with organization_id: {config.workos_organization_id}")
        else:
            logger.warning(f"⚠️ CompanyWorkOSConfig not found for client_id: {client_id_str}")
        
        from datetime import datetime
        client.workos_organization_created = True
        client.workos_organization_created_at = datetime.utcnow()
        await db.commit()
        await db.refresh(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Updated workos_organization_created tracking for client {client.id}")
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ WorkOS Organization created: {organization_id} for client {client.name} (ID: {client.id})")
        
        return organization_id
        
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"❌ Failed to provision WorkOS Organization for client {client.id}: {str(e)}", exc_info=True)
        return None
