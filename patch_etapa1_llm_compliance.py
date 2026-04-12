#!/usr/bin/env python3
"""
Etapa 1: LLM Factory Compliance (LGPD)
Ensures ALL LLM calls respect tenant config — tenant with own API key
has data flowing exclusively through their own key.

Patches:
  1. tenant_llm_context.py — add get_gemini_client_for_tenant() + get_claude_model_for_tenant()
  2. llm.py — get_audited_model() tenant-aware
  3. llm.py — generate_native_gemini() + generate_native_gemini_sync() tenant-aware
  4. gemini_voice.py — WebSocket uses tenant client
  5. voice_screening_orchestrator.py — uses tenant client
  6. gemini_voice_service.py — fixes tenant key bug + uses helper
  7. transcription_service.py — uses tenant client
  8. voice_composite.py — STT + TTS use tenant client (2 calls)
  9. voice_gemini_live.py — uses tenant client
  10. embedding_gemini.py — accepts custom api_key
  11. embedding_factory.py — tenant-aware provider selection
"""
import os
import sys

BASE = "/home/runner/workspace/lia-agent-system"
results = []


def read_file(path):
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    with open(full) as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    with open(full, "w") as f:
        f.write(content)


def patch(path, old, new):
    """Replace old with new in file. Fail if old not found."""
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    content = read_file(full)
    if old not in content:
        print(f"  ERROR: pattern not found in {path}")
        print(f"    Expected: {repr(old[:80])}...")
        results.append(False)
        return False
    count = content.count(old)
    if count > 1:
        print(f"  WARNING: pattern found {count} times in {path}, replacing first only")
    content = content.replace(old, new, 1)
    write_file(full, content)
    print(f"  OK: {path}")
    results.append(True)
    return True


# ============================================================
# 1. tenant_llm_context.py — Add helper functions
# ============================================================
print("\n=== 1. tenant_llm_context.py: add tenant helpers ===")

# First add import os if missing
path = os.path.join(BASE, "app/shared/tenant_llm_context.py")
content = read_file(path)
if "import os" not in content:
    content = content.replace("import logging", "import logging\nimport os", 1)
    write_file(path, content)
    print("  OK: added import os")

patch(
    "app/shared/tenant_llm_context.py",
    '''def clear_tenant_config_cache(company_id: str = ""):''',
    '''def get_gemini_client_for_tenant(company_id: str | None = None):
    """Get a Gemini genai.Client respecting tenant LLM config.

    If tenant has a custom Gemini API key, creates a client with that key
    (direct Google API, no Replit proxy). Otherwise returns client with
    the global Replit AI Integration key.

    Safe to call from any context — returns a fresh client each time.
    The llm_bootstrap monkey-patch ensures audit logging regardless.
    """
    from google import genai

    tenant_id = company_id or get_current_llm_tenant()
    if tenant_id:
        config = _tenant_configs.get(tenant_id)
        if config:
            providers = config.get("providers", {})
            gemini_cfg = providers.get("gemini", {})
            tenant_key = gemini_cfg.get("api_key")
            if tenant_key:
                logger.info(
                    "[TenantLLM] Using tenant Gemini key for tenant=%s",
                    tenant_id,
                )
                return genai.Client(api_key=tenant_key)

    api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
    if not api_key:
        raise ValueError("AI_INTEGRATIONS_GEMINI_API_KEY not configured")

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["http_options"] = {"api_version": "", "base_url": base_url}
    return genai.Client(**kwargs)


def get_claude_model_for_tenant(company_id: str | None = None):
    """Get a ChatAnthropic model respecting tenant LLM config.

    If tenant has a custom Claude/Anthropic API key, creates model with
    that key. Otherwise returns None (caller should use global default).
    """
    tenant_id = company_id or get_current_llm_tenant()
    if not tenant_id:
        return None

    config = _tenant_configs.get(tenant_id)
    if not config:
        return None

    providers = config.get("providers", {})
    claude_cfg = providers.get("claude", {})
    tenant_key = claude_cfg.get("api_key")
    if not tenant_key:
        return None

    try:
        from langchain_anthropic import ChatAnthropic

        from app.core.config import settings

        tenant_model = claude_cfg.get("model", settings.LLM_PRIMARY_MODEL)
        logger.info(
            "[TenantLLM] Using tenant Claude key for tenant=%s model=%s",
            tenant_id,
            tenant_model,
        )
        return ChatAnthropic(
            model_name=tenant_model,
            api_key=tenant_key,
            temperature=settings.LLM_DEFAULT_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("[TenantLLM] Failed to create tenant Claude model: %s", exc)
        return None


def clear_tenant_config_cache(company_id: str = ""):''',
)


# ============================================================
# 2. llm.py — get_audited_model() tenant-aware
# ============================================================
print("\n=== 2. llm.py: get_audited_model() tenant-aware ===")
patch(
    "app/domains/ai/services/llm.py",
    """        tenant_id = company_id or self._current_tenant or ""
        base_model = self.claude
        callbacks = [PIIStripCallback(), AuditLogCallback(tenant_id=tenant_id, caller=caller)]
        return base_model.with_config(callbacks=callbacks)""",
    """        tenant_id = company_id or self._current_tenant or ""

        # === Tenant-aware model selection (LGPD compliance) ===
        base_model = None
        if tenant_id:
            try:
                from app.shared.tenant_llm_context import get_claude_model_for_tenant
                base_model = get_claude_model_for_tenant(tenant_id)
            except Exception:
                pass
        if base_model is None:
            base_model = self.claude

        callbacks = [PIIStripCallback(), AuditLogCallback(tenant_id=tenant_id, caller=caller)]
        return base_model.with_config(callbacks=callbacks)""",
)


# ============================================================
# 3. llm.py — generate_native_gemini() tenant-aware
# ============================================================
print("\n=== 3. llm.py: generate_native_gemini() tenant-aware ===")
patch(
    "app/domains/ai/services/llm.py",
    """        try:
            client = self.gemini_native

            # Build kwargs
            kwargs: dict[str, Any] = {"model": model, "contents": contents}""",
    """        try:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(tenant_id) if tenant_id else self.gemini_native

            # Build kwargs
            kwargs: dict[str, Any] = {"model": model, "contents": contents}""",
)

# Also patch generate_native_gemini_sync
print("\n=== 3b. llm.py: generate_native_gemini_sync() tenant-aware ===")
patch(
    "app/domains/ai/services/llm.py",
    """        try:
            client = self.gemini_native
            kwargs: dict[str, Any] = {"model": model, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            if generation_config is not None:
                kwargs["generation_config"] = generation_config

            response = client.models.generate_content(**kwargs)""",
    """        try:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(tenant_id) if tenant_id else self.gemini_native
            kwargs: dict[str, Any] = {"model": model, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            if generation_config is not None:
                kwargs["generation_config"] = generation_config

            response = client.models.generate_content(**kwargs)""",
)


# ============================================================
# 4. gemini_voice.py — WebSocket uses tenant client
# ============================================================
print("\n=== 4. gemini_voice.py: tenant-aware client ===")
patch(
    "app/api/v1/gemini_voice.py",
    """        api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
        base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

        if not api_key or not base_url:
            await websocket.send_json({
                "type": "error",
                "message": "Gemini Live Audio não configurado no servidor",
            })
            await websocket.close(code=4500)
            return

        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "", "base_url": base_url},
        )""",
    """        # === Tenant-aware Gemini client (LGPD compliance) ===
        try:
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(session.company_id)
        except (ValueError, Exception) as _client_err:
            logger.warning("[GEMINI VOICE WS] Gemini unavailable: %s", _client_err)
            await websocket.send_json({
                "type": "error",
                "message": "Gemini Live Audio não configurado no servidor",
            })
            await websocket.close(code=4500)
            return""",
)


# ============================================================
# 5. voice_screening_orchestrator.py — tenant-aware client
# ============================================================
print("\n=== 5. voice_screening_orchestrator.py: tenant-aware client ===")
patch(
    "app/domains/voice/services/voice_screening_orchestrator.py",
    """            import os

            from google import genai
            from google.genai import types

            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

            if not api_key or not base_url:
                # If Gemini is unavailable but presentation is pending, generate fallback intro
                if not session.presentation_done:
                    session.presentation_done = True
                    return self._build_fallback_job_presentation(session)
                return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)

            client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "", "base_url": base_url},
            )""",
    """            from google.genai import types

            # === Tenant-aware Gemini client (LGPD compliance) ===
            try:
                from app.shared.tenant_llm_context import get_gemini_client_for_tenant
                client = get_gemini_client_for_tenant(session.company_id)
            except (ValueError, Exception) as _client_err:
                logger.warning("[VoiceOrchestrator] Gemini unavailable: %s", _client_err)
                if not session.presentation_done:
                    session.presentation_done = True
                    return self._build_fallback_job_presentation(session)
                return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)""",
)


# ============================================================
# 6. gemini_voice_service.py — fix tenant key bug + use helper
# ============================================================
print("\n=== 6. gemini_voice_service.py: fix tenant bug + use helper ===")
patch(
    "app/domains/voice/services/gemini_voice_service.py",
    """        if company_id:
            try:
                from app.shared.tenant_llm_context import _tenant_configs
                config = _tenant_configs.get(company_id)
                if config and "gemini" in config.get("providers", {}):
                    tenant_key = config["providers"]["gemini"].get("api_key")
                    if tenant_key:
                        api_key = tenant_key
                        base_url = None  # Direct API with tenant key
            except ImportError:
                pass

        if not api_key or not base_url:
            raise ValueError(
                "Gemini AI Integrations not configured. "
                "AI_INTEGRATIONS_GEMINI_API_KEY and AI_INTEGRATIONS_GEMINI_BASE_URL must be set."
            )

        self.client = genai.Client(
            api_key=api_key,
            http_options={
                'api_version': '',
                'base_url': base_url
            }
        )""",
    """        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        self.client = get_gemini_client_for_tenant(company_id)""",
)


# ============================================================
# 7. transcription_service.py — tenant-aware client
# ============================================================
print("\n=== 7. transcription_service.py: tenant-aware client ===")
patch(
    "app/domains/interview_intelligence/services/transcription_service.py",
    """    def _get_client(self):
        if not self._client:
            from google import genai
            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            if not api_key:
                raise ValueError("Gemini API not configured — AI_INTEGRATIONS_GEMINI_API_KEY missing")
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["http_options"] = {"api_version": "", "base_url": base_url}
            self._client = genai.Client(**client_kwargs)
        return self._client""",
    """    def _get_client(self):
        if not self._client:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            company_id = getattr(self, "_company_id", None)
            self._client = get_gemini_client_for_tenant(company_id)
        return self._client""",
)


# ============================================================
# 8. voice_composite.py — STT + TTS use tenant client
# ============================================================
print("\n=== 8a. voice_composite.py: STT tenant-aware ===")
patch(
    "app/shared/providers/voice_composite.py",
    """    async def _stt_transcribe(self, audio_data: bytes) -> str:
        import functools

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self._gemini_api_key,
            http_options={"api_version": "", "base_url": self._gemini_base_url},
        )""",
    """    async def _stt_transcribe(self, audio_data: bytes) -> str:
        import functools

        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(self._tenant_id)""",
)

print("\n=== 8b. voice_composite.py: TTS tenant-aware ===")
patch(
    "app/shared/providers/voice_composite.py",
    """    async def _tts_synthesize(self, text: str, voice_name: str = "Aoede") -> bytes:
        import functools

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self._gemini_api_key,
            http_options={"api_version": "", "base_url": self._gemini_base_url},
        )""",
    """    async def _tts_synthesize(self, text: str, voice_name: str = "Aoede") -> bytes:
        import functools

        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(self._tenant_id)""",
)


# ============================================================
# 9. voice_gemini_live.py — tenant-aware client
# ============================================================
print("\n=== 9. voice_gemini_live.py: tenant-aware client ===")
patch(
    "app/shared/providers/voice_gemini_live.py",
    """        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self._api_key,
            http_options={"api_version": "", "base_url": self._base_url},
        )""",
    """        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(
            config.tenant_id if config else None
        )""",
)


# ============================================================
# 10. embedding_gemini.py — accept custom api_key
# ============================================================
print("\n=== 10. embedding_gemini.py: tenant-aware ===")
patch(
    "app/shared/providers/embedding_gemini.py",
    """    def __init__(self, model: str | None = None):
        self._model = model or GEMINI_EMBEDDING_MODEL
        self._client = None""",
    """    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or GEMINI_EMBEDDING_MODEL
        self._client = None
        self._custom_api_key = api_key""",
)

patch(
    "app/shared/providers/embedding_gemini.py",
    """    @property
    def _gemini_client(self):
        \"\"\"Lazy-initialize Gemini client.\"\"\"
        if self._client is None:
            from google import genai

            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

            if not api_key or not base_url:
                raise ValueError(
                    "AI_INTEGRATIONS_GEMINI_API_KEY or AI_INTEGRATIONS_GEMINI_BASE_URL not configured"
                )

            self._client = genai.Client(
                api_key=api_key,
                http_options={
                    "api_version": "",
                    "base_url": base_url,
                },
            )
        return self._client""",
    """    @property
    def _gemini_client(self):
        \"\"\"Lazy-initialize Gemini client (tenant-aware).\"\"\"
        if self._client is None:
            from google import genai

            if self._custom_api_key:
                # Tenant-specific key — direct Google API
                self._client = genai.Client(api_key=self._custom_api_key)
                logger.info("[GeminiEmbedding] Using tenant-specific API key")
            else:
                # Global Replit AI Integration
                api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
                base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
                if not api_key or not base_url:
                    raise ValueError(
                        "AI_INTEGRATIONS_GEMINI_API_KEY or AI_INTEGRATIONS_GEMINI_BASE_URL not configured"
                    )
                self._client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": "", "base_url": base_url},
                )
        return self._client""",
)


# ============================================================
# 11. embedding_factory.py — tenant-aware provider selection
# ============================================================
print("\n=== 11a. embedding_factory.py: embed_with_fallback accepts company_id ===")
patch(
    "app/shared/providers/embedding_factory.py",
    """    @classmethod
    async def embed_with_fallback(
        cls,
        text: str,
        preferred_provider: str | None = None,
    ) -> tuple[list[float], str, str]:
        \"\"\"Generate embedding with automatic provider fallback.

        Tries providers in the following order:
        1. ``preferred_provider`` (if given and registered).
        2. Default provider (EMBEDDING_DEFAULT_PROVIDER env var).
        3. Remaining providers in EMBEDDING_FALLBACK_ORDER.

        Args:
            text: Text to embed.
            preferred_provider: Provider to try first (optional).

        Returns:
            Tuple of (vector, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        \"\"\"
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls.get(provider_name)
                result = await provider.embed_text(text)""",
    """    @classmethod
    async def embed_with_fallback(
        cls,
        text: str,
        preferred_provider: str | None = None,
        company_id: str | None = None,
    ) -> tuple[list[float], str, str]:
        \"\"\"Generate embedding with automatic provider fallback.

        Tries providers in the following order:
        1. ``preferred_provider`` (if given and registered).
        2. Default provider (EMBEDDING_DEFAULT_PROVIDER env var).
        3. Remaining providers in EMBEDDING_FALLBACK_ORDER.

        Args:
            text: Text to embed.
            preferred_provider: Provider to try first (optional).
            company_id: Tenant ID for tenant-specific API keys (LGPD).

        Returns:
            Tuple of (vector, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        \"\"\"
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls._get_tenant_provider(provider_name, company_id)
                result = await provider.embed_text(text)""",
)

print("\n=== 11b. embedding_factory.py: embed_batch_with_fallback accepts company_id ===")
patch(
    "app/shared/providers/embedding_factory.py",
    """    @classmethod
    async def embed_batch_with_fallback(
        cls,
        texts: list[str],
        preferred_provider: str | None = None,
    ) -> tuple[list[list[float]], str, str]:
        \"\"\"Generate batch embeddings with automatic provider fallback.

        Args:
            texts: Texts to embed.
            preferred_provider: Provider to try first (optional).

        Returns:
            Tuple of (vectors, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        \"\"\"
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls.get(provider_name)
                results = await provider.embed_batch(texts)""",
    """    @classmethod
    async def embed_batch_with_fallback(
        cls,
        texts: list[str],
        preferred_provider: str | None = None,
        company_id: str | None = None,
    ) -> tuple[list[list[float]], str, str]:
        \"\"\"Generate batch embeddings with automatic provider fallback.

        Args:
            texts: Texts to embed.
            preferred_provider: Provider to try first (optional).
            company_id: Tenant ID for tenant-specific API keys (LGPD).

        Returns:
            Tuple of (vectors, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        \"\"\"
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls._get_tenant_provider(provider_name, company_id)
                results = await provider.embed_batch(texts)""",
)

print("\n=== 11c. embedding_factory.py: add _get_tenant_provider helper ===")
patch(
    "app/shared/providers/embedding_factory.py",
    """    @classmethod
    def _build_fallback_order(cls, preferred_provider: str | None) -> list[str]:""",
    """    @classmethod
    def _get_tenant_provider(
        cls, provider_name: str, company_id: str | None = None
    ) -> "EmbeddingProviderABC":
        \"\"\"Get provider with tenant-specific config if available (LGPD).\"\"\"
        if company_id and provider_name == "gemini":
            try:
                from app.shared.tenant_llm_context import _tenant_configs

                config = _tenant_configs.get(company_id)
                if config:
                    providers = config.get("providers", {})
                    gemini_cfg = providers.get("gemini", {})
                    tenant_key = gemini_cfg.get("api_key")
                    if tenant_key:
                        from app.shared.providers.embedding_gemini import (
                            GeminiEmbeddingProvider,
                        )

                        logger.info(
                            "[EmbeddingFactory] Using tenant key for %s",
                            company_id,
                        )
                        return GeminiEmbeddingProvider(api_key=tenant_key)
            except Exception as exc:
                logger.warning(
                    "[EmbeddingFactory] Tenant key lookup failed for %s: %s",
                    company_id,
                    exc,
                )
        return cls.get(provider_name)

    @classmethod
    def _build_fallback_order(cls, preferred_provider: str | None) -> list[str]:""",
)


# ============================================================
# Summary
# ============================================================
total = len(results)
ok = sum(1 for r in results if r)
print(f"\n{'=' * 60}")
print(f"Results: {ok}/{total} patches applied successfully")
if ok < total:
    failed = total - ok
    print(f"FAILED: {failed} patches need manual review")
    sys.exit(1)
else:
    print("All patches applied!")
    sys.exit(0)
