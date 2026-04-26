"""
Teams <-> Orchestrator bridge.
Connects incoming Teams messages to the full LIA orchestrator (same as floating chat).
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Smart Routing — intents that require the full platform (browser URL)
# ------------------------------------------------------------------ #
_PLATFORM_ROUTES: list[tuple[list[str], str]] = [
    # Job creation
    (["criar vaga", "nova vaga", "abrir vaga", "criar uma vaga", "new job", "criar job",
      "cadastrar vaga", "adicionar vaga", "job description", "criar jd"],
     "/jobs/new"),
    # Job editing
    (["editar vaga", "alterar vaga", "modificar vaga", "atualizar vaga", "edit job"],
     "/jobs"),
    # Pipeline / stages
    (["editar pipeline", "configurar pipeline", "configurar etapas", "etapas do funil",
      "editar funil", "mudar etapas", "criar etapa", "nova etapa"],
     "/configuracoes/pipeline"),
    # General settings
    (["configurações", "configuracoes", "acessar configurações", "abrir configurações",
      "ir para configurações", "settings"],
     "/configuracoes"),
    # Bulk operations
    (["exportar candidatos", "exportar vagas", "baixar relatório", "download relatório"],
     "/candidatos"),
    # Integrations
    (["integrar", "configurar integração", "webhook", "api key", "conectar sistema"],
     "/configuracoes/integracoes"),
]


def _detect_platform_route(text: str) -> str:
    """
    Returns a platform deep-link path if the message contains a platform-required intent.
    Returns empty string if the request can be handled in chat.
    """
    lowered = text.lower()
    for keywords, path in _PLATFORM_ROUTES:
        if any(kw in lowered for kw in keywords):
            return path
    return ""




class TeamsOrchestratorBridge:
    """
    Routes Teams text messages through the LIA orchestrator.
    Same intelligence as the floating chat panel.
    """

    async def process_message(
        self,
        activity: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Process a text message from Teams through the LIA orchestrator.
        Returns orchestrator result dict.
        """
        # Import from shared registry -- avoids circular import (domain->api)
        from app.orchestrator.registry import get_orchestrator_instance

        text = (activity.get("text") or "").strip()
        if not text:
            return {"message": "Não entendi sua mensagem. Pode repetir?", "success": False}

        teams_user_id = activity.get("from", {}).get("id", "unknown")
        teams_user_name = activity.get("from", {}).get("name", "")
        conversation_id = activity.get("conversation", {}).get("id", "")
        tenant_id = activity.get("channelData", {}).get("tenant", {}).get("id", "")

        # Resolve company_id from stored conversation reference or tenant mapping
        company_id = await self._resolve_company_id(teams_user_id, tenant_id, db)

        # Use teams_<conversation_id> as conversation_id so state is persisted
        orch_conversation_id = f"teams_{conversation_id}"

        try:
            orchestrator = get_orchestrator_instance()
            if orchestrator is None:
                return {"message": "Orchestrator not initialized", "success": False}
            result = await orchestrator.process_request(
                user_id=teams_user_id,
                message=text,
                conversation_id=orch_conversation_id,
                context={
                    "company_id": company_id,
                    "source": "teams",
                    "teams_user_name": teams_user_name,
                    "teams_user_id": teams_user_id,
                    "teams_conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
            # Smart Routing: if the message requires a platform action, attach the
            # deep_link_path so the card renderer adds an "Abrir na plataforma →" button.
            deep_link = _detect_platform_route(text)
            if deep_link:
                result["_deep_link_path"] = deep_link
                logger.info(f"[TeamsOrchestratorBridge] Smart routing → {deep_link} for: {text[:60]}")
            return result
        except Exception as e:
            logger.error(f"[TeamsOrchestratorBridge] Error: {e}", exc_info=True)
            return {
                "success": False,
                "message": "Ocorreu um erro ao processar sua mensagem. Tente novamente.",
                "error": str(e),
            }

    async def process_cv_attachment(
        self,
        activity: dict[str, Any],
        attachment: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Process a file attachment (CV) from Teams.
        Downloads the file and runs cv screening.
        """
        import re

        import httpx

        teams_user_id = activity.get("from", {}).get("id", "unknown")
        tenant_id = activity.get("channelData", {}).get("tenant", {}).get("id", "")
        company_id = await self._resolve_company_id(teams_user_id, tenant_id, db)

        content_url = attachment.get("contentUrl", "")
        filename = attachment.get("name", "cv.pdf")

        try:
            # Get bot token to download the file
            from app.domains.communication.services.teams_simple import simple_teams_bot
            token = await simple_teams_bot.get_access_token()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    content_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                file_bytes = response.content

            # Extract text from file
            cv_text = ""
            if filename.lower().endswith(".pdf"):
                try:
                    from app.domains.cv_screening.services.cv_parser import CVParserService
                    parser = CVParserService()
                    cv_text = await parser.extract_text_from_pdf(file_bytes)
                except Exception as parse_err:
                    logger.warning(f"[TeamsOrchestratorBridge] PDF parser error: {parse_err}")
                    cv_text = ""
            else:
                cv_text = file_bytes.decode("utf-8", errors="ignore")

            if not cv_text.strip():
                return {"success": False, "message": "Não foi possível extrair texto do arquivo."}

            # Check if message has vacancy hint
            text = (activity.get("text") or "").strip()
            vacancy_title = None
            if text:
                m = re.search(r"(?:para a vaga de|vaga:?)\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
                if m:
                    vacancy_title = m.group(1).strip()

            try:
                from app.domains.cv_screening.tools.cv_upload_tool import create_and_screen_candidate

                class _Ctx:
                    pass
                ctx = _Ctx()
                ctx.company_id = company_id
                ctx.user_id = teams_user_id

                result = await create_and_screen_candidate(
                    cv_text=cv_text,
                    vacancy_title=vacancy_title,
                    run_bars=True,
                    run_wsi=False,
                    context=ctx,
                )
                return result
            except ImportError:
                # Fallback: route through orchestrator with the CV text inline
                logger.warning("[TeamsOrchestratorBridge] cv_upload_tool not available, routing via orchestrator")
                msg = f"Analise este CV e faça a triagem:\n\n{cv_text[:3000]}"
                if vacancy_title:
                    msg = f"Analise este CV para a vaga de {vacancy_title}:\n\n{cv_text[:3000]}"
                fake_activity = dict(activity)
                fake_activity["text"] = msg
                return await self.process_message(fake_activity, db=db)

        except Exception as e:
            logger.error(f"[TeamsOrchestratorBridge] CV processing error: {e}", exc_info=True)
            return {"success": False, "message": f"Erro ao processar CV: {str(e)}"}

    async def _resolve_company_id(
        self,
        teams_user_id: str,
        tenant_id: str,
        db: AsyncSession | None = None,
    ) -> str | None:
        """
        Resolve company_id for the Teams user.

        Strategy (P0-1 fix — auditoria 2026-04-26):
        1. Read stored TeamsConversation.company_id (populated at write-time
           via _store_conversation_reference → User.company_id lookup).
        2. Fallback for pre-backfill rows: lookup User by user_aad_object_id
           on the conversation row (if available).
        3. Returns None if neither path resolves a company.

        Logs an explicit warning when None is returned (harness sensor —
        helps detect drift between Teams identity and platform User mapping).

        Why direct attribute access (not defensive fallback): the previous version
        used defensive coding that masked a missing schema column silently.
        See AUDITORIA_TEAMS_2026-04-26.md (P0-1) for context. After Migration 097,
        the column always exists, so direct access fails fast if schema regresses.
        """
        if not db:
            logger.warning(
                "[TeamsOrchestratorBridge] _resolve_company_id called without db session — "
                "returning None (multi-tenant context unavailable for teams_user=%s)",
                teams_user_id,
            )
            return None

        try:
            from app.domains.communication.repositories.teams_repository import (
                TeamsRepository,
            )
            from lia_models.teams import TeamsConversation

            stmt = select(TeamsConversation).where(
                TeamsConversation.user_id == teams_user_id
            ).limit(1)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()

            if row and row.company_id:
                return row.company_id

            # Fallback: row exists but company_id not backfilled — derive from User
            if row and row.user_aad_object_id:
                repo = TeamsRepository(db)
                user = await repo.get_user_by_aad_object_id(row.user_aad_object_id)
                if user and user.company_id:
                    # Opportunistic backfill on this row (next requests skip the lookup)
                    row.company_id = user.company_id
                    logger.info(
                        "[TeamsOrchestratorBridge] backfilled company_id=%s on TeamsConversation %s "
                        "via aad_object_id lookup",
                        user.company_id, row.conversation_id,
                    )
                    return user.company_id

            # Sentinel: no resolution — log so we can spot drift in production
            logger.warning(
                "[TeamsOrchestratorBridge] could not resolve company_id for teams_user=%s "
                "(row_found=%s, aad_object_id=%s) — orchestrator will run without tenant context",
                teams_user_id, bool(row), row.user_aad_object_id if row else None,
            )
            return None

        except Exception as exc:
            logger.error(
                "[TeamsOrchestratorBridge] _resolve_company_id error for teams_user=%s: %s",
                teams_user_id, exc, exc_info=True,
            )
            return None


teams_orchestrator_bridge = TeamsOrchestratorBridge()
