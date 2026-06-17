"""
HubSpot CRM Integration Service.

Syncs client accounts to HubSpot CRM for sales and onboarding tracking.
"""
import logging
import os
from datetime import datetime
from typing import Any

from hubspot import HubSpot
from hubspot.crm.companies import SimplePublicObjectInputForCreate as CompanyInput
from hubspot.crm.companies.exceptions import ApiException as CompanyApiException
from hubspot.crm.contacts import SimplePublicObjectInputForCreate as ContactInput
from hubspot.crm.contacts.exceptions import ApiException as ContactApiException
from hubspot.crm.deals import SimplePublicObjectInputForCreate as DealInput
from hubspot.crm.deals.exceptions import ApiException as DealApiException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.client_account_repository import (
    ClientAccountRepository,
)
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


class HubSpotService:
    """
    Service for syncing client data to HubSpot CRM.
    
    Handles creation and updates of Companies, Contacts, and Deals in HubSpot.
    """
    
    def __init__(self):
        """Initialize the HubSpot service."""
        self.access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        self._client: HubSpot | None = None
        
        if not self.access_token:
            logger.warning("⚠️ HUBSPOT_ACCESS_TOKEN not configured - HubSpot sync will be skipped")
    
    @property
    def client(self) -> HubSpot | None:
        """Get or create HubSpot client instance."""
        if not self.access_token:
            return None
        
        if self._client is None:
            self._client = HubSpot(access_token=self.access_token)
        
        return self._client
    
    @property
    def is_configured(self) -> bool:
        """Check if HubSpot is properly configured."""
        return self.access_token is not None
    
    async def sync_client_to_hubspot(
        self,
        client: ClientAccount,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Sync a client account to HubSpot CRM.
        
        Creates or updates:
        - A Company record with client information
        - A Contact for the primary admin
        - A Deal associated with the Company
        
        Args:
            client: The ClientAccount to sync
            db: Database session
        
        Returns:
            Dict with success status and HubSpot IDs
        """
        if not self.is_configured or self.client is None:
            logger.warning("⚠️ HUBSPOT_ACCESS_TOKEN not configured - skipping HubSpot sync")
            return {
                "success": False,
                "error": "HubSpot not configured",
                "hubspot_company_id": None,
                "hubspot_contact_id": None,
                "hubspot_deal_id": None
            }
        
        result = {
            "success": False,
            "hubspot_company_id": None,
            "hubspot_contact_id": None,
            "hubspot_deal_id": None,
            "error": None
        }
        
        try:
            company_id = await self._create_or_update_company(client)
            result["hubspot_company_id"] = company_id
            
            if client.primary_email:
                contact_id = await self._create_or_update_contact(client, company_id)
                result["hubspot_contact_id"] = contact_id
            
            deal_id = await self._create_deal(client, company_id)
            result["hubspot_deal_id"] = deal_id
            
            await self._update_client_hubspot_info(
                client_id=str(client.id),
                hubspot_company_id=company_id,
                hubspot_deal_id=deal_id,
                db=db
            )
            
            result["success"] = True
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Successfully synced client {client.name} to HubSpot (Company: {company_id}, Deal: {deal_id})")
            
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"❌ Failed to sync client {client.id} to HubSpot: {error_msg}", exc_info=True)
        
        return result
    
    async def _create_or_update_company(self, client: ClientAccount) -> str | None:
        """
        Create or update a Company in HubSpot.
        
        Args:
            client: The ClientAccount data
        
        Returns:
            HubSpot Company ID or None
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        primary_email = str(client.primary_email) if client.primary_email else None
        domain = extract_domain_from_email(primary_email)
        
        client_name = str(client.name) if client.name else None
        trade_name = str(client.trade_name) if client.trade_name else None
        primary_phone = str(client.primary_phone) if client.primary_phone else ""
        industry = str(client.industry) if client.industry else ""
        plan_id = str(client.plan_id) if client.plan_id else ""
        status = str(client.status) if client.status else ""
        company_size = str(client.company_size) if client.company_size else ""
        website = str(client.website) if client.website else None
        created_at = client.created_at
        
        properties = {
            "name": client_name or trade_name or f"Client-{client.id}",
            "phone": primary_phone,
            "industry": industry,
            "lia_plan": plan_id,
            "lia_client_id": str(client.id),
            "lia_status": status,
            "lia_company_size": company_size,
        }
        
        if domain:
            properties["domain"] = domain
        
        if website:
            properties["website"] = website
        
        if created_at:
            properties["createdate"] = created_at.strftime("%Y-%m-%d")
        
        try:
            existing_company = await self._find_company_by_domain(domain) if domain else None
            
            if existing_company:
                response = self.client.crm.companies.basic_api.update(
                    company_id=existing_company,
                    simple_public_object_input={"properties": properties}
                )
                logger.info(f"🔄 Updated existing HubSpot Company: {existing_company}")
                return existing_company
            else:
                company_input = CompanyInput(properties=properties)
                response = self.client.crm.companies.basic_api.create(
                    simple_public_object_input_for_create=company_input
                )
                company_id = getattr(response, 'id', None)
                logger.info(f"✅ Created HubSpot Company: {company_id}")
                return company_id
                
        except CompanyApiException as e:
            logger.error(f"❌ HubSpot Company API error: {e.body}", exc_info=True)
            raise
    
    async def _find_company_by_domain(self, domain: str) -> str | None:
        """
        Search for an existing company by domain.
        
        Args:
            domain: Company domain to search for
        
        Returns:
            Company ID if found, None otherwise
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        if not domain:
            return None
        
        try:
            filter_group = {
                "filters": [
                    {
                        "propertyName": "domain",
                        "operator": "EQ",
                        "value": domain
                    }
                ]
            }
            
            search_request = {
                "filterGroups": [filter_group],
                "limit": 1
            }
            
            response = self.client.crm.companies.search_api.do_search(
                public_object_search_request=search_request
            )
            
            if response.results and len(response.results) > 0:
                return response.results[0].id
            
            return None
            
        except CompanyApiException as e:
            logger.warning(f"⚠️ Error searching for company by domain: {e.body}")
            return None
    
    async def _create_or_update_contact(
        self,
        client: ClientAccount,
        company_id: str | None
    ) -> str | None:
        """
        Create or update a Contact for the primary admin.
        
        Args:
            client: The ClientAccount data
            company_id: Associated HubSpot Company ID
        
        Returns:
            HubSpot Contact ID or None
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        if not client.primary_email:
            return None
        
        primary_email = str(client.primary_email) if client.primary_email else ""
        client_name = str(client.name) if client.name else None
        trade_name = str(client.trade_name) if client.trade_name else None
        primary_phone = str(client.primary_phone) if client.primary_phone else ""
        
        properties = {
            "email": primary_email,
            "company": client_name or trade_name or "",
            "phone": primary_phone,
            "lia_client_id": str(client.id),
            "lia_role": "primary_admin"
        }
        
        try:
            existing_contact = await self._find_contact_by_email(primary_email)
            
            if existing_contact:
                response = self.client.crm.contacts.basic_api.update(
                    contact_id=existing_contact,
                    simple_public_object_input={"properties": properties}
                )
                contact_id = existing_contact
                logger.info(f"🔄 Updated existing HubSpot Contact: {contact_id}")
            else:
                contact_input = ContactInput(properties=properties)
                response = self.client.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=contact_input
                )
                contact_id = getattr(response, 'id', None)
                logger.info(f"✅ Created HubSpot Contact: {contact_id}")
            
            if company_id and contact_id:
                await self._associate_contact_to_company(contact_id, company_id)
            
            return contact_id
            
        except ContactApiException as e:
            logger.error(f"❌ HubSpot Contact API error: {e.body}", exc_info=True)
            return None
    
    async def _find_contact_by_email(self, email: str) -> str | None:
        """
        Search for an existing contact by email.
        
        Args:
            email: Contact email to search for
        
        Returns:
            Contact ID if found, None otherwise
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        if not email:
            return None
        
        try:
            filter_group = {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }
                ]
            }
            
            search_request = {
                "filterGroups": [filter_group],
                "limit": 1
            }
            
            response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )
            
            if response.results and len(response.results) > 0:
                return response.results[0].id
            
            return None
            
        except ContactApiException as e:
            logger.warning(f"⚠️ Error searching for contact by email: {e.body}")
            return None
    
    async def _associate_contact_to_company(
        self,
        contact_id: str,
        company_id: str
    ) -> bool:
        """
        Associate a Contact with a Company in HubSpot.
        
        Args:
            contact_id: HubSpot Contact ID
            company_id: HubSpot Company ID
        
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        try:
            self.client.crm.contacts.associations_api.create(
                contact_id=contact_id,
                to_object_type="companies",
                to_object_id=company_id,
                association_type="contact_to_company"
            )
            logger.info(f"✅ Associated Contact {contact_id} with Company {company_id}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to associate contact to company: {str(e)}")
            return False
    
    async def _create_deal(
        self,
        client: ClientAccount,
        company_id: str | None
    ) -> str | None:
        """
        Create a Deal in HubSpot associated with the Company.
        
        Args:
            client: The ClientAccount data
            company_id: Associated HubSpot Company ID
        
        Returns:
            HubSpot Deal ID or None
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        client_name = str(client.name) if client.name else None
        trade_name = str(client.trade_name) if client.trade_name else None
        plan_id = str(client.plan_id) if client.plan_id else ""
        created_at = client.created_at
        
        deal_name = f"LIA Platform - {client_name or trade_name}"
        
        properties = {
            "dealname": deal_name,
            "dealstage": "qualifiedtobuy",
            "pipeline": "default",
            "lia_client_id": str(client.id),
            "lia_plan": plan_id,
        }
        
        if created_at:
            properties["createdate"] = created_at.strftime("%Y-%m-%d")
        
        # Check for existing deal first
        existing_deal = await self._find_deal_by_client_id(str(client.id))
        if existing_deal:
            # Update existing deal
            try:
                self.client.crm.deals.basic_api.update(
                    deal_id=existing_deal,
                    simple_public_object_input={"properties": properties}
                )
                logger.info(f"🔄 Updated existing HubSpot Deal: {existing_deal}")
                return existing_deal
            except DealApiException as e:
                logger.error(f"❌ HubSpot Deal update error: {e.body}", exc_info=True)
        
        try:
            deal_input = DealInput(properties=properties)
            response = self.client.crm.deals.basic_api.create(
                simple_public_object_input_for_create=deal_input
            )
            deal_id = getattr(response, 'id', None)
            logger.info(f"✅ Created HubSpot Deal: {deal_id}")
            
            if company_id and deal_id:
                await self._associate_deal_to_company(deal_id, company_id)
            
            return deal_id
            
        except DealApiException as e:
            logger.error(f"❌ HubSpot Deal API error: {e.body}", exc_info=True)
            return None
    
    async def _associate_deal_to_company(
        self,
        deal_id: str,
        company_id: str
    ) -> bool:
        """
        Associate a Deal with a Company in HubSpot.
        
        Args:
            deal_id: HubSpot Deal ID
            company_id: HubSpot Company ID
        
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        try:
            self.client.crm.deals.associations_api.create(
                deal_id=deal_id,
                to_object_type="companies",
                to_object_id=company_id,
                association_type="deal_to_company"
            )
            logger.info(f"✅ Associated Deal {deal_id} with Company {company_id}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to associate deal to company: {str(e)}")
            return False
    
    async def _find_deal_by_client_id(self, client_id: str) -> str | None:
        """
        Search for an existing deal by lia_client_id property.
        
        Args:
            client_id: Client ID to search for
        
        Returns:
            Deal ID if found, None otherwise
        """
        if self.client is None:
            raise RuntimeError("HubSpot client not initialized")
        
        try:
            filter_group = {
                "filters": [
                    {
                        "propertyName": "lia_client_id",
                        "operator": "EQ",
                        "value": client_id
                    }
                ]
            }
            
            search_request = {
                "filterGroups": [filter_group],
                "limit": 1
            }
            
            response = self.client.crm.deals.search_api.do_search(
                public_object_search_request=search_request
            )
            
            if response.results and len(response.results) > 0:
                return getattr(response.results[0], 'id', None)
            
            return None
            
        except DealApiException as e:
            logger.warning(f"⚠️ Error searching for deal by client_id: {e.body}")
            return None
    
    async def _update_client_hubspot_info(
        self,
        client_id: str,
        hubspot_company_id: str | None,
        hubspot_deal_id: str | None,
        db: AsyncSession
    ) -> None:
        """
        Update client record with HubSpot sync information.
        
        Args:
            client_id: Client account ID
            hubspot_company_id: HubSpot Company ID
            hubspot_deal_id: HubSpot Deal ID
            db: Database session
        """
        try:
            import uuid
            client_uuid = uuid.UUID(client_id)
            
            client = await ClientAccountRepository(db).get_by_id(client_uuid)
            
            if client:
                new_settings = dict(client.settings) if client.settings else {}
                new_settings["hubspot"] = {
                    "company_id": hubspot_company_id,
                    "deal_id": hubspot_deal_id,
                    "last_synced_at": datetime.utcnow().isoformat()
                }
                client.settings = new_settings
                client.updated_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(client)
                logger.info(f"✅ Updated client {client_id} with HubSpot sync info")
                
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ Failed to update client HubSpot info: {str(e)}", exc_info=True)
    
    async def update_onboarding_status(
        self,
        client_id: str,
        status: dict[str, Any],
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Update onboarding status on HubSpot Company/Deal.
        
        Tracks:
        - welcome_email_sent
        - workos_configured
        - sso_enabled
        - users_count
        
        Args:
            client_id: Client account ID
            status: Dict with onboarding status fields
            db: Database session
        
        Returns:
            Dict with success status
        """
        if not self.is_configured:
            logger.warning("⚠️ HUBSPOT_ACCESS_TOKEN not configured - skipping onboarding status update")
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            import uuid
            client_uuid = uuid.UUID(client_id)
            
            client = await ClientAccountRepository(db).get_by_id(client_uuid)
            
            if not client:
                return {"success": False, "error": "Client not found"}
            
            hubspot_info = client.settings.get("hubspot", {}) if client.settings else {}
            company_id = hubspot_info.get("company_id")
            deal_id = hubspot_info.get("deal_id")
            
            if not company_id:
                return {"success": False, "error": "HubSpot Company not found for client"}
            
            if self.client is None:
                raise RuntimeError("HubSpot client not initialized")
            
            properties = {}
            
            if "welcome_email_sent" in status:
                properties["lia_welcome_email_sent"] = str(status["welcome_email_sent"]).lower()
            
            if "workos_configured" in status:
                properties["lia_workos_configured"] = str(status["workos_configured"]).lower()
            
            if "sso_enabled" in status:
                properties["lia_sso_enabled"] = str(status["sso_enabled"]).lower()
            
            if "users_count" in status:
                properties["lia_users_count"] = str(status["users_count"])
            
            if properties:
                try:
                    self.client.crm.companies.basic_api.update(
                        company_id=company_id,
                        simple_public_object_input={"properties": properties}
                    )
                    logger.info(f"✅ Updated HubSpot Company {company_id} onboarding status")
                except CompanyApiException as e:
                    logger.error(f"❌ Failed to update HubSpot Company: {e.body}")
                
                if deal_id:
                    try:
                        self.client.crm.deals.basic_api.update(
                            deal_id=deal_id,
                            simple_public_object_input={"properties": properties}
                        )
                        logger.info(f"✅ Updated HubSpot Deal {deal_id} onboarding status")
                    except DealApiException as e:
                        logger.warning(f"⚠️ Failed to update HubSpot Deal: {e.body}")
            
            hubspot_info["last_synced_at"] = datetime.utcnow().isoformat()
            new_settings = dict(client.settings) if client.settings else {}
            new_settings["hubspot"] = hubspot_info
            client.settings = new_settings
            await db.commit()
            
            return {"success": True}
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            error_msg = str(e)
            logger.error(f"❌ Failed to update onboarding status: {error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def get_sync_status(
        self,
        client_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Get HubSpot sync status for a client.
        
        Args:
            client_id: Client account ID
            db: Database session
        
        Returns:
            Dict with sync status (last_synced_at, hubspot_company_id, hubspot_deal_id)
        """
        try:
            import uuid
            client_uuid = uuid.UUID(client_id)
            
            client = await ClientAccountRepository(db).get_by_id(client_uuid)
            
            if not client:
                return {
                    "synced": False,
                    "error": "Client not found",
                    "last_synced_at": None,
                    "hubspot_company_id": None,
                    "hubspot_deal_id": None
                }
            
            settings = client.settings if client.settings is not None else {}
            hubspot_info = settings.get("hubspot", {}) if isinstance(settings, dict) else {}
            
            return {
                "synced": bool(hubspot_info.get("company_id")),
                "last_synced_at": hubspot_info.get("last_synced_at"),
                "hubspot_company_id": hubspot_info.get("company_id"),
                "hubspot_deal_id": hubspot_info.get("deal_id"),
                "hubspot_configured": self.is_configured
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Failed to get sync status: {error_msg}", exc_info=True)
            return {
                "synced": False,
                "error": error_msg,
                "last_synced_at": None,
                "hubspot_company_id": None,
                "hubspot_deal_id": None
            }


hubspot_service = HubSpotService()


async def sync_client_to_hubspot(
    client: ClientAccount,
    db: AsyncSession
) -> dict[str, Any]:
    """
    Convenience function to sync a client to HubSpot.
    
    Args:
        client: The ClientAccount to sync
        db: Database session
    
    Returns:
        Dict with success status and HubSpot IDs
    """
    return await hubspot_service.sync_client_to_hubspot(client, db)
