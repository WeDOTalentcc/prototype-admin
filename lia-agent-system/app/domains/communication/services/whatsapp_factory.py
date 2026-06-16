"""
WhatsApp Provider Factory

Factory for creating WhatsApp provider instances based on company configuration.
Supports multiple providers (Meta, Twilio) with company-specific settings.
"""

import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.whatsapp_meta_service import MetaWhatsAppService
from app.domains.communication.services.whatsapp_provider import ProviderType, WhatsAppProvider
from app.domains.communication.services.whatsapp_twilio_service import TwilioWhatsAppService

logger = logging.getLogger(__name__)


class WhatsAppProviderFactory:
    """
    Factory for creating WhatsApp provider instances.
    
    Determines which provider to use based on:
    1. Company-specific configuration in database
    2. Environment variable overrides
    3. Default provider setting
    
    Usage:
        provider = await WhatsAppProviderFactory.get_provider(company_id, db)
        await provider.send_text_message(to, text)
    """
    
    _provider_cache: dict[str, WhatsAppProvider] = {}
    _meta_instance: MetaWhatsAppService | None = None
    _twilio_instance: TwilioWhatsAppService | None = None
    
    @classmethod
    def get_meta_provider(cls) -> MetaWhatsAppService:
        """Get or create Meta WhatsApp provider instance."""
        if cls._meta_instance is None:
            cls._meta_instance = MetaWhatsAppService()
        return cls._meta_instance
    
    @classmethod
    def get_twilio_provider(cls) -> TwilioWhatsAppService:
        """Get or create Twilio WhatsApp provider instance."""
        if cls._twilio_instance is None:
            cls._twilio_instance = TwilioWhatsAppService()
        return cls._twilio_instance
    
    @classmethod
    async def get_provider(
        cls,
        company_id: str,
        db: AsyncSession | None = None
    ) -> WhatsAppProvider:
        """
        Get the appropriate WhatsApp provider for a company.
        
        Lookup order:
        1. Check environment variable WHATSAPP_PROVIDER_{company_id}
        2. Check company settings in database (if db provided)
        3. Check global default WHATSAPP_DEFAULT_PROVIDER
        4. Fall back to Meta provider
        
        Args:
            company_id: The company identifier
            db: Optional database session for querying company settings
            
        Returns:
            WhatsAppProvider instance (Meta or Twilio)
        """
        cache_key = f"provider_{company_id}"
        if cache_key in cls._provider_cache:
            return cls._provider_cache[cache_key]
        
        provider_type = await cls._determine_provider_type(company_id, db)
        
        if provider_type == ProviderType.TWILIO:
            provider = cls.get_twilio_provider()
            if not provider.is_configured:
                logger.warning(
                    f"[FACTORY] Twilio requested for {company_id} but not configured. "
                    "Falling back to Meta."
                )
                provider = cls.get_meta_provider()
        else:
            provider = cls.get_meta_provider()
        
        cls._provider_cache[cache_key] = provider
        logger.debug(f"[FACTORY] Using {provider.provider_type.value} provider for {company_id}")
        
        return provider
    
    @classmethod
    async def _determine_provider_type(
        cls,
        company_id: str,
        db: AsyncSession | None
    ) -> ProviderType:
        """Determine which provider type to use for a company."""
        env_override = os.getenv(f"WHATSAPP_PROVIDER_{company_id}")
        if env_override:
            try:
                return ProviderType(env_override.lower())
            except ValueError:
                logger.warning(f"[FACTORY] Invalid provider type in env: {env_override}")
        
        if db:
            try:
                provider_type = await cls._get_company_provider_setting(company_id, db)
                if provider_type:
                    return provider_type
            except Exception as e:
                logger.warning(f"[FACTORY] Error querying company settings: {e}")
        
        default_provider = os.getenv("WHATSAPP_DEFAULT_PROVIDER", "meta")
        try:
            return ProviderType(default_provider.lower())
        except ValueError:
            return ProviderType.META
    
    @classmethod
    async def _get_company_provider_setting(
        cls,
        company_id: str,
        db: AsyncSession
    ) -> ProviderType | None:
        """Query company settings for WhatsApp provider preference."""
        try:
            from lia_models.company import Company

            # ADR-001-EXEMPT: cross-domain Company lookup; foreign-domain repo would be admin/companies.
            # Single primary-key fetch — defer to Sprint 6 when CompanyRepository becomes canonical.
            result = await db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = result.scalar_one_or_none()
            
            if company:
                settings = getattr(company, 'communication_settings', None) or {}
                whatsapp_settings = settings.get('whatsapp', {})
                provider_str = whatsapp_settings.get('provider')
                
                if provider_str:
                    try:
                        return ProviderType(provider_str.lower())
                    except ValueError:
                        pass
                
        except Exception as e:
            logger.debug(f"[FACTORY] Could not query company settings: {e}")
        
        return None
    
    @classmethod
    def get_provider_by_type(cls, provider_type: ProviderType) -> WhatsAppProvider:
        """
        Get a provider instance by type directly.
        
        Args:
            provider_type: The provider type to get
            
        Returns:
            WhatsAppProvider instance
        """
        if provider_type == ProviderType.TWILIO:
            return cls.get_twilio_provider()
        return cls.get_meta_provider()
    
    @classmethod
    def clear_cache(cls):
        """Clear the provider cache (useful for testing)."""
        cls._provider_cache.clear()
        cls._meta_instance = None
        cls._twilio_instance = None
    
    @classmethod
    def set_company_provider(cls, company_id: str, provider: WhatsAppProvider):
        """
        Manually set a provider for a company (useful for testing).
        
        Args:
            company_id: The company identifier
            provider: The provider instance to use
        """
        cache_key = f"provider_{company_id}"
        cls._provider_cache[cache_key] = provider
