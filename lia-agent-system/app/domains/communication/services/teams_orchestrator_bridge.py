"""
Teams <-> Orchestrator bridge.
Connects incoming Teams messages to the full LIA orchestrator (same as floating chat).
"""
from app.shared.llm_models import CANONICAL_GEMINI_FLASH_MODEL
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
        from app.orchestrator.execution.registry import get_orchestrator_instance

        text = (activity.get("text") or "").strip()
        if not text:
            return {"message": "Não entendi sua mensagem. Pode repetir?", "success": False}

        # ── W7.2 PromptInjectionGuard — defense-in-depth antes do orchestrator ──
        # Recovery #7 (2026-05-23): bloco de segurança removido pelo merge
        # incident 02361f41c restaurado. Sem ele, Teams aceitava prompt
        # injection sem block (P0 security gap).
        try:
            from app.shared.robustness.security_patterns import (
                check_input_security,
                get_block_response,
            )
            _sec = check_input_security(text)
            if _sec.is_blocked:
                logger.warning(
                    "[TeamsOrchestratorBridge] SecurityPatterns blocked: risk=%s categories=%s",
                    _sec.risk_level, _sec.threat_categories,
                )
                return {
                    "message": get_block_response(_sec, language="pt"),
                    "success": False,
                    "blocked_reason": "security_patterns",
                }
        except Exception as _sec_exc:
            logger.debug("[TeamsOrchestratorBridge] security check skipped: %s", _sec_exc)
        # ─────────────────────────────────────────────────────────────────────

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

    # -----------------------------------------------------------------------
    # Recovery #7 (2026-05-23) — 3 métodos attachment restaurados.
    #
    # Perdidos pelo merge incident 02361f41c em 2026-05-01. Sem eles, Teams
    # bot não conseguia processar imagens (Gemini Vision), documentos genéricos
    # (.txt/.csv) nem áudio (STT). Tests integration
    # ``tests/integration/test_teams_w9_3_multimedia.py`` +
    # ``test_teams_w9_2_voice_stt.py`` quebrados em CI desde maio.
    # -----------------------------------------------------------------------
    async def process_image_attachment(
        self,
        activity: dict[str, Any],
        attachment: dict[str, Any],
        db: "AsyncSession | None" = None,
    ) -> dict[str, Any]:
        """W9.3: Process image attachment via Gemini Vision for recruitment context."""
        import httpx

        content_url = attachment.get("contentUrl", "")
        content_type = (attachment.get("contentType") or "image/jpeg").lower()
        filename = attachment.get("name", "image.jpg")

        try:
            from app.domains.communication.services.teams_simple import simple_teams_bot
            token = await simple_teams_bot.get_access_token()

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    content_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                image_bytes = resp.content

            if not image_bytes:
                return {"success": False, "message": "Imagem vazia ou inacessivel."}

            try:
                from google.genai import types as _gtypes  # W3-027-EXEMPT: google.genai.types for Part.from_bytes type building only — llm call via llm_service
                from app.domains.ai.services.llm import llm_service

                prompt = (
                    "Descreva esta imagem no contexto de recrutamento e RH. "
                    "O que a imagem mostra? Como poderia ser usada num processo seletivo? "
                    "Seja objetivo, em portugues, maximo 3 linhas."
                )
                contents = [
                    _gtypes.Part.from_bytes(data=image_bytes, mime_type=content_type),
                    prompt,
                ]
                response = await llm_service.generate_native_gemini(
                    contents=contents,
                    model=CANONICAL_GEMINI_FLASH_MODEL,
                )
                description = response.text if hasattr(response, "text") else str(response)
                msg = f"Imagem recebida: {filename}\n\n{description}\n\nPara usar na plataforma, acesse o painel web."
                return {"success": True, "message": msg}
            except Exception as vision_err:
                logger.warning("[TeamsOrchestratorBridge] Gemini Vision error: %s", vision_err)
                img_size_kb = len(image_bytes) // 1024
                msg = f"Imagem recebida: {filename} ({img_size_kb} KB). Para usar na plataforma, acesse o painel web."
                return {"success": True, "message": msg}

        except Exception as e:
            logger.error("[TeamsOrchestratorBridge] process_image_attachment error: %s", e)
            return {"success": False, "message": "Erro ao processar a imagem. Tente novamente."}

    async def process_general_document(
        self,
        activity: dict[str, Any],
        attachment: dict[str, Any],
        db: "AsyncSession | None" = None,
    ) -> dict[str, Any]:
        """W9.3: Process generic documents (txt, csv) — extract text and route via orchestrator."""
        import httpx

        content_url = attachment.get("contentUrl", "")
        filename = attachment.get("name", "document")
        content_type = (attachment.get("contentType") or "").lower()

        try:
            from app.domains.communication.services.teams_simple import simple_teams_bot
            token = await simple_teams_bot.get_access_token()

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    content_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                raw_bytes = resp.content

            if content_type in ("text/plain", "text/csv") or filename.endswith((".txt", ".csv")):
                doc_text = raw_bytes.decode("utf-8", errors="ignore")
                if doc_text.strip():
                    excerpt = doc_text[:1000]
                    fake_activity = {**activity, "text": f"[Documento: {filename}]\n\n{excerpt}"}
                    return await self.process_message(fake_activity, db=db)

            doc_size_kb = len(raw_bytes) // 1024
            msg = (
                f"Documento recebido: {filename} ({doc_size_kb} KB). "
                "Para formatos .docx/.xlsx, use a plataforma web para importar dados."
            )
            return {"success": True, "message": msg}

        except Exception as e:
            logger.error("[TeamsOrchestratorBridge] process_general_document error: %s", e)
            return {"success": False, "message": "Erro ao processar o documento."}

    async def process_voice_attachment(
        self,
        activity: dict[str, Any],
        attachment: dict[str, Any],
        db: "AsyncSession | None" = None,
    ) -> dict[str, Any]:
        """W9.2: Process voice attachment via Gemini native STT for transcription."""
        import httpx

        content_url = attachment.get("contentUrl", "")
        content_type = (attachment.get("contentType") or "audio/ogg").lower()
        filename = attachment.get("name", "audio.ogg")

        try:
            from app.domains.communication.services.teams_simple import simple_teams_bot
            token = await simple_teams_bot.get_access_token()

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    content_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                audio_bytes = resp.content

            if not audio_bytes:
                return {
                    "success": False,
                    "message": (
                        f"Audio recebido: {filename}. "
                        "Nao foi possivel baixar o conteudo do audio."
                    ),
                }

            try:
                from google.genai import types as _gtypes  # W3-027-EXEMPT: google.genai.types for Part.from_bytes type building only — llm call via llm_service
                from app.domains.ai.services.llm import llm_service

                prompt = (
                    "Transcreva este audio em portugues com precisao. "
                    "Forneca apenas a transcricao, sem introducao ou explicacoes. "
                    "Se for uma mensagem de voz de candidato ou recrutador em contexto de RH, "
                    "mantenha o conteudo original fiel."
                )
                contents = [
                    _gtypes.Part.from_bytes(data=audio_bytes, mime_type=content_type),
                    prompt,
                ]
                response = await llm_service.generate_native_gemini(
                    contents=contents,
                    model=CANONICAL_GEMINI_FLASH_MODEL,
                )
                transcription = response.text.strip() if (hasattr(response, "text") and response.text) else ""

                if transcription:
                    fake_activity = {**activity, "text": f"[Audio: {filename}]\n\n{transcription}"}
                    return await self.process_message(fake_activity, db=db)
                else:
                    return {
                        "success": True,
                        "message": f"Audio recebido: {filename}. Nao foi possivel transcrever o conteudo.",
                    }

            except Exception as stt_err:
                logger.warning("[TeamsOrchestratorBridge] STT error for %s: %s", filename, stt_err)
                size_kb = len(audio_bytes) // 1024
                return {
                    "success": True,
                    "message": (
                        f"Audio recebido: {filename} ({size_kb} KB). "
                        "A transcricao automatica nao esta disponivel no momento. "
                        "Envie a mensagem em texto para continuar."
                    ),
                }

        except Exception as e:
            logger.error("[TeamsOrchestratorBridge] process_voice_attachment error: %s", e)
            return {"success": False, "message": "Erro ao processar o audio. Tente novamente."}

    async def _resolve_company_id(
        self,
        teams_user_id: str,
        tenant_id: str,
        db: AsyncSession | None = None,
    ) -> str | None:
        """
        Resolve company_id from Teams user/tenant.

        Priority:
        1. Stored conversation reference (fastest, cached after first message)
        2. TEAMS_DEFAULT_COMPANY_ID env var (set by admin for single-tenant deployments)
        3. First active company in DB (single-company fallback)
        """
        if db:
            try:
                from app.domains.communication.repositories.teams_repository import TeamsRepository
                row = await TeamsRepository(db).get_any_conversation_by_user_id(teams_user_id)
                if row and getattr(row, "company_id", None):
                    return row.company_id
            except Exception:
                pass

        # Fallback: admin-configured default company for Teams bot
        import os
        default_company_id = os.environ.get("TEAMS_DEFAULT_COMPANY_ID")
        if default_company_id:
            logger.info(f"[Teams] Using TEAMS_DEFAULT_COMPANY_ID={default_company_id} for user {teams_user_id}")
            return default_company_id

        # Last resort: first active company in DB (single-company deployment)
        if db:
            try:
                from sqlalchemy import text as _text
                result = await db.execute(
                    _text("SELECT id FROM companies WHERE is_active = true ORDER BY created_at ASC LIMIT 1")
                )
                row = result.fetchone()
                if row:
                    logger.info(f"[Teams] Resolved company_id={row[0]} from DB fallback for user {teams_user_id}")
                    return str(row[0])
            except Exception as e:
                logger.warning(f"[Teams] DB company fallback failed: {e}")

        logger.warning(f"[Teams] Could not resolve company_id for user {teams_user_id} tenant {tenant_id}. Set TEAMS_DEFAULT_COMPANY_ID.")
        return None


teams_orchestrator_bridge = TeamsOrchestratorBridge()
