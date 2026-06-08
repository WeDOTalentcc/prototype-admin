"""
Simplified Microsoft Teams integration without Bot Framework SDK.
Handles webhooks directly from Teams.
"""
import logging
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleTeamsBot:
    """
    Simplified Teams bot that handles webhooks directly.
    No Bot Framework SDK dependencies.
    """
    
    def __init__(self):
        """Initialize Teams bot."""
        self.app_id = settings.MICROSOFT_APP_ID
        self.app_password = settings.MICROSOFT_APP_PASSWORD
        self._access_token: str | None = None
        self._token_expires: datetime | None = None
    
    async def get_access_token(self) -> str:
        """
        Get Microsoft Bot Framework access token.
        Used to send messages back to Teams.
        """
        # Require credentials
        if not self.app_id or not self.app_password:
            raise ValueError("Teams Bot credentials not configured")
        
        # Check if we have valid cached token
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token
        
        # Bot Framework Connector tokens MUST use botframework.com as the tenant endpoint.
        # AZURE_TENANT_ID is for Microsoft Graph API calls (different service).
        # TEAMS_APP_TENANT_ID can override if needed for special deployments.
        tenant_id = getattr(settings, "TEAMS_APP_TENANT_ID", None) or "botframework.com"
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        logger.info(f"[Teams] Acquiring token via {token_url}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.app_id,
                    "client_secret": self.app_password,
                    "scope": "https://api.botframework.com/.default"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get access token: {response.text}")
                from app.shared.errors import LIAIntegrationError
                raise LIAIntegrationError(
                    message="Falha ao obter token de acesso do Teams",
                    code="TEAMS_TOKEN_FAILED",
                    details={"status_code": response.status_code},
                )
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            from datetime import timedelta
            self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer

            # Decode token payload (no verification) to log key claims for debugging
            try:
                import base64
                import json as _json
                payload_b64 = self._access_token.split(".")[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                claims = _json.loads(base64.b64decode(payload_b64))
                logger.info(
                    f"[Teams] Token claims: appid={claims.get('appid')} "
                    f"tid={claims.get('tid')} aud={claims.get('aud')} "
                    f"iss={claims.get('iss', '')[:60]}"
                )
            except Exception:
                pass

            return self._access_token
    
    async def process_activity(self, activity: dict[str, Any], db=None) -> Any | None:
        """
        Process incoming activity from Teams.
        
        Args:
            activity: Activity payload from Teams
            db: Optional DB session for tenant resolution
            
        Returns:
            Response dict ({"type": "card", "card": ...} or {"type": "text", "text": ...})
            or str for conversationUpdate, or None
        """
        activity_type = activity.get("type", "")
        
        if activity_type == "message":
            return await self._handle_message(activity, db=db)
        
        elif activity_type == "conversationUpdate":
            return await self._handle_conversation_update(activity)
        
        elif activity_type == "invoke":
            return await self._handle_invoke(activity)
        
        return None
    
    # ── Slash command definitions ────────────────────────────────────────────

    _SLASH_COMMANDS = {
        "/ajuda": "Quais são todas as funcionalidades que você pode me ajudar?",
        "/help":  "Quais são todas as funcionalidades que você pode me ajudar?",
        "/buscar": "Busca os melhores candidatos para a vaga mais recente",
        "/triagem": "Quais candidatos ainda precisam de triagem WSI?",
        "/relatorio": "Gera o relatório semanal de recrutamento",
        "/pipeline": "Como está a saúde geral do pipeline de recrutamento?",
        "/vagas": "Quais são as vagas ativas e seus status?",
        "/candidatos": "Quais candidatos estão aguardando triagem ou retorno?",
        "/resumo": "Me dê um resumo das atividades e alertas de hoje",
    }

    def _parse_slash_command(self, text: str) -> str:
        """Convert slash command to a natural language prompt."""
        stripped = text.strip().lower()
        # Match /command optionally followed by args
        parts = stripped.split(None, 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        if cmd in self._SLASH_COMMANDS:
            base = self._SLASH_COMMANDS[cmd]
            return f"{base} {args}".strip() if args else base
        return text  # Not a known slash command — return as-is

    def _strip_at_mention(self, text: str) -> str:
        """Remove <at>BotName</at> tags from Teams messages in group channels."""
        import re as _re
        # Strip <at>...</at> tags
        cleaned = _re.sub(r'<at>[^<]*</at>', '', text)
        return cleaned.strip()

    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_message(self, activity: dict[str, Any], db=None) -> dict[str, Any]:
        """Handle incoming message — routes through full LIA orchestrator."""
        try:
            from app.domains.communication.services.teams_card_renderer import teams_card_renderer
            from app.domains.communication.services.teams_orchestrator_bridge import teams_orchestrator_bridge

            raw_text = activity.get("text", "").strip()
            # Strip @mention tags (e.g. <at>LIA</at> in group channels)
            text = self._strip_at_mention(raw_text)
            # Handle slash commands (/buscar, /triagem, /relatorio, etc.)
            if text.startswith("/"):
                text = self._parse_slash_command(text)
            activity = {**activity, "text": text}

            from_user = activity.get("from", {})
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"[Teams] Message from {from_user.get('name')}: {text[:80]}")

            result = await teams_orchestrator_bridge.process_message(activity, db=db)
            deep_link = result.pop("_deep_link_path", "")
            card = teams_card_renderer.render(result, source_text=text, deep_link_path=deep_link)

            if card:
                return {"type": "card", "card": card}
            else:
                message = result.get("message") or result.get("response") or result.get("content", "Processando...")
                return {"type": "text", "text": message}
        except Exception as e:
            logger.error(f"[Teams] _handle_message error: {e}", exc_info=True)
            return {"type": "text", "text": "Ocorreu um erro ao processar sua mensagem. Tente novamente."}
    
    async def _handle_conversation_update(self, activity: dict[str, Any]) -> dict[str, Any] | None:
        """Handle conversation update (bot added, user joined, etc)."""
        members_added = activity.get("membersAdded", [])
        bot_id = activity.get("recipient", {}).get("id")
        
        welcome_messages = []
        
        for member in members_added:
            if member.get("id") != bot_id:
                # New user added (not the bot)
                name = member.get("name", "")
                welcome_messages.append({
                    "text": (
                        f"Olá {name}! 👋\n\n"
                        "Sou a **LIA**, assistente de recrutamento da WedoTalent.\n\n"
                        "Posso te ajudar a:\n"
                        "- Criar vagas\n"
                        "- Buscar candidatos\n"
                        "- Agendar entrevistas\n"
                        "- Organizar sua agenda de recrutamento\n\n"
                        "Como posso te ajudar hoje?"
                    ),
                    "user": member
                })
        
        if welcome_messages:
            return {"messages": welcome_messages}
        
        return None
    
    async def _handle_invoke(self, activity: dict[str, Any]) -> str | None:
        """Handle adaptive card action."""
        action_data = activity.get("value", {})
        
        logger.info(f"Received invoke action: {action_data}")
        
        # If the invoke contains a "message" field, route through orchestrator
        if isinstance(action_data, dict) and action_data.get("message"):
            try:
                from app.domains.communication.services.teams_orchestrator_bridge import teams_orchestrator_bridge
                fake_activity = dict(activity)
                fake_activity["text"] = action_data["message"]
                result = await teams_orchestrator_bridge.process_message(fake_activity)
                return result.get("message") or "Ação processada."
            except Exception as e:
                logger.error(f"[Teams] _handle_invoke orchestrator error: {e}", exc_info=True)
        
        return "Ação recebida! Processando..."
    
    async def send_message(
        self,
        service_url: str,
        conversation_id: str,
        text: str,
        reply_to_activity_id: str | None = None
    ) -> bool:
        """
        Send message to Teams conversation.
        
        Args:
            service_url: Teams service URL from activity
            conversation_id: Conversation ID
            text: Message text to send
            reply_to_activity_id: Optional activity ID to reply to
            
        Returns:
            True if sent successfully
        """
        try:
            token = await self.get_access_token()
            
            # Build message payload
            message = {
                "type": "message",
                "from": {
                    "id": self.app_id,
                    "name": "LIA"
                },
                "conversation": {
                    "id": conversation_id
                },
                "text": text
            }
            
            if reply_to_activity_id:
                message["replyToId"] = reply_to_activity_id
            
            # Send message — strip trailing slash to avoid double-slash in URL
            base = service_url.rstrip("/")
            url = f"{base}/v3/conversations/{conversation_id}/activities"
            if reply_to_activity_id:
                url = f"{base}/v3/conversations/{conversation_id}/activities/{reply_to_activity_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=message,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(
                        f"Failed to send message: HTTP {response.status_code} | URL: {url} "
                        f"| WWW-Authenticate: {response.headers.get('WWW-Authenticate', 'none')} "
                        f"| Body: {response.text[:500]}"
                    )
                    return False
                
                logger.info("Message sent successfully to Teams")
                return True
                
        except Exception as e:
            logger.error(f"Error sending message to Teams: {e}", exc_info=True)
            return False
    
    async def send_adaptive_card(
        self,
        service_url: str,
        conversation_id: str,
        card_payload: dict[str, Any]
    ) -> bool:
        """
        Send adaptive card to Teams.
        
        Args:
            service_url: Teams service URL
            conversation_id: Conversation ID
            card_payload: Adaptive card JSON
            
        Returns:
            True if sent successfully
        """
        try:
            token = await self.get_access_token()
            
            message = {
                "type": "message",
                "from": {
                    "id": self.app_id,
                    "name": "LIA"
                },
                "conversation": {
                    "id": conversation_id
                },
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card_payload
                    }
                ]
            }
            
            # Strip trailing slash to avoid double-slash in URL
            base = service_url.rstrip("/")
            url = f"{base}/v3/conversations/{conversation_id}/activities"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=message,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(
                        f"Failed to send card: HTTP {response.status_code} | URL: {url} "
                        f"| Headers: {dict(response.headers)} | Body: {response.text[:500]}"
                    )
                    return False
                
                logger.info("Adaptive card sent successfully to Teams")
                return True
                
        except Exception as e:
            logger.error(f"Error sending card to Teams: {e}", exc_info=True)
            return False


# Global simple Teams bot instance
simple_teams_bot = SimpleTeamsBot()
