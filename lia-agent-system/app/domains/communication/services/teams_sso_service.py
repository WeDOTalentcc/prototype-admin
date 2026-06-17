"""
Teams SSO Service — Azure AD identity resolution.

Flow:
1. User sends first message → bot checks if mapping exists in TeamsConversation.user_aad_object_id
2. If not mapped → send Sign-in card (Action.OpenUrl to OAuth page)
3. User clicks → goes to /api/v1/teams/auth/sso-page?conversation_id=xxx
4. Azure AD redirects back to /api/v1/teams/auth/callback with auth code
5. We exchange code for token, get user profile, map AAD ID → WeDOTalent user
6. Future messages route to correct company/user context
"""
import logging
import os
from typing import Any

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")
PLATFORM_URL = os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com").rstrip("/")


class TeamsSSOService:
    """
    Handles Azure AD SSO for Teams bot users.
    Maps Teams/AAD identities to WeDOTalent internal users.
    """

    def is_configured(self) -> bool:
        return bool(AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and AZURE_TENANT_ID)

    def get_sign_in_card(self, conversation_id: str) -> dict[str, Any]:
        """
        Adaptive Card with a Sign-in button.
        Sent to users who haven't authenticated yet.
        """
        sso_url = (
            f"{PLATFORM_URL}/api/v1/teams/auth/sso-page"
            f"?conversation_id={conversation_id}"
            f"&client_id={AZURE_CLIENT_ID}"
            f"&tenant_id={AZURE_TENANT_ID}"
        )
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🔐 **Autenticação necessária**",
                    "weight": "Bolder",
                    "size": "Medium",
                },
                {
                    "type": "TextBlock",
                    "text": "Para usar a LIA no Teams, conecte sua conta WeDOTalent.",
                    "wrap": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "🔗 Conectar conta WeDOTalent",
                    "url": sso_url,
                }
            ],
            "msteams": {"width": "Full"},
        }

    async def exchange_auth_code(
        self, auth_code: str, redirect_uri: str
    ) -> dict[str, Any] | None:
        """
        Exchange OAuth authorization code for user profile via Microsoft Graph.
        Returns dict with: aad_object_id, email, display_name, tenant_id
        """
        if not self.is_configured():
            logger.warning("[TeamsSSOService] Azure not configured")
            return None
        try:
            token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
            async with httpx.AsyncClient() as client:
                resp = await client.post(token_url, data={
                    "client_id": AZURE_CLIENT_ID,
                    "client_secret": AZURE_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": redirect_uri,
                    "scope": "openid profile email User.Read",
                })
                token_data = resp.json()

            access_token = token_data.get("access_token")
            if not access_token:
                logger.error(f"[TeamsSSOService] No access_token in response: {token_data}")
                return None

            # Get user profile from Graph
            async with httpx.AsyncClient() as client:
                profile_resp = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                profile = profile_resp.json()

            return {
                "aad_object_id": profile.get("id"),
                "email": profile.get("mail") or profile.get("userPrincipalName"),
                "display_name": profile.get("displayName"),
                "tenant_id": AZURE_TENANT_ID,
                "access_token": access_token,
            }
        except Exception as e:
            logger.error(f"[TeamsSSOService] exchange_auth_code error: {e}", exc_info=True)
            return None

    async def resolve_user(
        self,
        teams_user_id: str,
        aad_object_id: str | None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Resolve WeDOTalent user from Teams/AAD identity.
        Returns: {company_id, user_id, email, is_authenticated}
        """
        if not db:
            return {"company_id": None, "user_id": teams_user_id, "is_authenticated": False}

        try:
            from app.domains.communication.repositories.teams_repository import TeamsRepository

            # Find conversation record
            repo = TeamsRepository(db)
            conv = await repo.get_any_conversation_by_user_id(teams_user_id)

            if conv:
                # Try to find WeDOTalent user by AAD object ID or stored email
                aad_id = aad_object_id or getattr(conv, "user_aad_object_id", None)
                if aad_id:
                    # Look up by aad_object_id in users table (if column exists)
                    try:
                        user = await repo.get_user_by_aad_object_id(aad_id)
                        if user:
                            return {
                                "company_id": str(user.company_id) if user.company_id else None,
                                "user_id": str(user.id),
                                "email": user.email,
                                "is_authenticated": True,
                            }
                    except Exception:
                        pass  # Column may not exist yet

                # Fallback: use company from stored conv reference
                # TENANT-FALLBACK-OK: conv is TeamsConversation from upstream RLS-validated auth gate
                company_id = getattr(conv, "company_id", None)
                if company_id:
                    return {
                        "company_id": company_id,
                        "user_id": teams_user_id,
                        "is_authenticated": bool(aad_id),
                    }

        except Exception as e:
            logger.warning(f"[TeamsSSOService] resolve_user error: {e}")

        return {"company_id": None, "user_id": teams_user_id, "is_authenticated": False}

    async def save_user_mapping(
        self,
        teams_user_id: str,
        aad_object_id: str,
        email: str,
        company_id: str,
        db: AsyncSession,
    ) -> bool:
        """Store the AAD ↔ WeDOTalent mapping for future requests."""
        try:
            from lia_models.teams import TeamsConversation
            # Multi-tenancy fail-closed: scope update to current tenant.
            stmt = (
                update(TeamsConversation)
                .where(
                    TeamsConversation.user_id == teams_user_id,
                    TeamsConversation.company_id == company_id,
                )
                .values(user_aad_object_id=aad_object_id)
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(f"[TeamsSSOService] Mapped Teams user {teams_user_id} → AAD {aad_object_id}")
            return True
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"[TeamsSSOService] save_user_mapping error: {e}")
            return False


teams_sso_service = TeamsSSOService()
