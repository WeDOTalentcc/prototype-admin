"""
Configuration management using Pydantic Settings — subcategorized for clarity.

All fields remain accessible as `settings.<FIELD_NAME>` (backward compatible).
Subclasses group related settings for documentation and future library extraction.

Hierarchy:
  DatabaseSettings  → DB URL, pool sizes
  CacheSettings     → Redis, router cache TTLs
  MessagingSettings → RabbitMQ, Celery brokers
  LLMSettings       → API keys, model names, temperatures
  AuditSettings     → Audit storage (S3/file) config
  AuthSettings      → JWT, WorkOS, Azure
  AppSettings       → ENV, logging, CORS, feature flags
  Settings          → inherits all + validators
"""

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Dev guard de quota de Redis remoto (ex.: Upstash free 500k cmd/mes).
# Em desenvolvimento, REDIS_URL remoto e redirecionado para o redis-server
# local (que o workflow `lia-backend` ja sobe) para nao consumir a quota
# do Redis gerenciado. Fix no produtor: cobre app + Celery + consumidores.
# ---------------------------------------------------------------------------
_LOCAL_REDIS_HOSTS = {"localhost", "127.0.0.1", "::1", ""}


def _redis_host_is_local(url: str) -> bool:
    """True se a URL Redis aponta para um host local (nao consome quota remota)."""
    try:
        from urllib.parse import urlparse

        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in _LOCAL_REDIS_HOSTS

# ---------------------------------------------------------------------------
# 1. Database
# ---------------------------------------------------------------------------


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    # Task #1060: SQLAlchemy `echo` was previously bound to `DEBUG`, so dev
    # (DEBUG=True default) emitted every statement at INFO level. During long
    # Playwright runs this storm of SQL log lines was enough to OOM/derrubar o
    # workflow `lia-backend` no Replit. Echo is now opt-in via this dedicated
    # flag (default OFF, even em dev). Set DATABASE_ECHO=1 only quando estiver
    # ativamente debugando query plans.
    DATABASE_ECHO: bool = False
    ELASTICSEARCH_URL: str | None = None
    # Search backend selector: "postgres" (padrão) | "elasticsearch" (alto volume)
    SEARCH_BACKEND: str = "postgres"


# ---------------------------------------------------------------------------
# 2. Cache (Redis)
# ---------------------------------------------------------------------------


class CacheSettings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    ROUTER_CACHE_TTL: int = 3600  # Tier 1 cache TTL (segundos)
    SEMANTIC_CACHE_TTL: int = 86400  # Semantic cache TTL (segundos)
    ROUTER_CACHE_MAX_SIZE: int = 1000  # Max entries in-process LRU cache
    # Z5-03: threshold semântico configurável (Tier 3 — VectorSemanticCache)
    ROUTER_VECTOR_SIMILARITY_THRESHOLD: float = (
        0.85  # Cosine similarity floor para cache hit (reduzido de 0.92 para capturar queries semanticamente similares)
    )
    ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN: float = 0.05  # Loga near-misses dentro de threshold-margin
    ROUTER_VECTOR_CACHE_ENABLED: bool = True  # A/B flag: False desabilita Tier 3 completamente


# ---------------------------------------------------------------------------
# 3. Messaging (RabbitMQ / Celery)
# ---------------------------------------------------------------------------


class MessagingSettings(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "rh_platform"
    RABBITMQ_PREFETCH: int = 1
    # Celery uses REDIS_URL as broker by default; these allow override
    CELERY_BROKER_URL: str | None = None  # Falls back to REDIS_URL if not set
    CELERY_RESULT_BACKEND: str | None = None  # Falls back to REDIS_URL if not set
    # Broker abstraction layer — see app/shared/messaging/broker_interface.py
    # Valores: "redis" (padrão), "rabbitmq" (on-prem), "pubsub" (stub GCP)
    # Para migração GCP: setar BROKER_BACKEND=pubsub e implementar PubSubBroker real
    BROKER_BACKEND: str = "redis"


# ---------------------------------------------------------------------------
# 4. LLM / AI Settings
# ---------------------------------------------------------------------------


class LLMSettings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    GOOGLE_CLOUD_PROJECT: str | None = None
    GOOGLE_CLOUD_REGION: str = "us-east1"

    # Replit AI Integrations
    AI_INTEGRATIONS_GEMINI_API_KEY: str | None = None
    AI_INTEGRATIONS_GEMINI_BASE_URL: str | None = None
    AI_INTEGRATIONS_ANTHROPIC_API_KEY: str | None = None
    AI_INTEGRATIONS_ANTHROPIC_BASE_URL: str | None = None
    AI_INTEGRATIONS_OPENAI_API_KEY: str | None = None
    AI_INTEGRATIONS_OPENAI_BASE_URL: str | None = None

    # Model Names
    LLM_PRIMARY_MODEL: str = "claude-sonnet-4-6"
    LLM_FAST_MODEL: str = "gemini-2.5-flash"  # Tier rápido — Gemini Flash (padrão)
    LLM_POWERFUL_MODEL: str = "claude-opus-4-6"
    LLM_GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_ROUTER_MODEL: str = "gemini-2.5-flash"  # Roteamento barato (Tier 3) — Gemini Flash
    LLM_AGENT_MODEL: str = "claude-sonnet-4-6"  # Execução de agentes (Claude mantido para profundidade)
    LLM_DEFAULT_PROVIDER: str = "gemini"  # Provider padrão — Gemini 2.5 Flash

    # Generation parameters
    LLM_DEFAULT_TEMPERATURE: float = 0.7
    LLM_AGENT_TEMPERATURE: float = 0.3
    LLM_ROUTER_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: float = 120.0

    # HTTP client timeouts — sourcing services (UC-P2-12)
    # All values are env-configurable via pydantic-settings (HTTP_TIMEOUT_* env vars)
    HTTP_TIMEOUT_APIFY_SECONDS: float = 180.0
    HTTP_TIMEOUT_APIFY_CONNECT_SECONDS: float = 30.0
    HTTP_TIMEOUT_GITHUB_SECONDS: float = 30.0
    HTTP_TIMEOUT_GITHUB_CONNECT_SECONDS: float = 10.0
    HTTP_TIMEOUT_STACKOVERFLOW_SECONDS: float = 30.0
    HTTP_TIMEOUT_STACKOVERFLOW_CONNECT_SECONDS: float = 10.0
    HTTP_TIMEOUT_DEFAULT_SECONDS: float = 30.0
    HTTP_TIMEOUT_PEARCH_SECONDS: float = 120.0
    HTTP_TIMEOUT_PEARCH_CONNECT_SECONDS: float = 10.0
    HTTP_TIMEOUT_PEARCH_HEALTH_SECONDS: float = 10.0

    # Cascade thresholds (Haiku → Sonnet → Opus)
    LLM_CASCADE_FAST_THRESHOLD: float = 0.80
    LLM_CASCADE_MID_THRESHOLD: float = 0.70
    LLM_CASCADE_FALLBACK_THRESHOLD: float = 0.60

    # Router confidence
    ROUTER_FAST_CONFIDENCE_THRESHOLD: float = 0.7
    ROUTER_CONFIDENCE_THRESHOLD: float = 0.80

    # Embedding provider configuration — Task #134
    # Supported values: "gemini" (default, 768-dim), "openai" (768-dim via dimensions param)
    EMBEDDING_DEFAULT_PROVIDER: str = "gemini"

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "lia-agent-system"

    # Z6-02: OpenTelemetry / OTLP
    OTEL_SERVICE_NAME: str = "lia-agent-system"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # ex: http://jaeger:4318 — vazio = desabilitado
    OTEL_TRACES_ENABLED: bool = True


# ---------------------------------------------------------------------------
# 5. Audit Storage (Phase 1)
# ---------------------------------------------------------------------------


class AuditSettings(BaseSettings):
    AUDIT_STORAGE_TYPE: str = "file"  # "file" (dev) | "s3" (prod)
    AUDIT_STORAGE_BUCKET: str = ""  # S3 bucket — obrigatório quando type=s3
    AUDIT_STORAGE_PREFIX: str = "audit"  # Prefixo de path no S3
    AUDIT_LOCAL_DIR: str = "./audit_logs"  # Diretório local (dev)
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"


# ---------------------------------------------------------------------------
# 6. Auth (JWT, WorkOS, Azure)
# ---------------------------------------------------------------------------


class AuthSettings(BaseSettings):
    SECRET_KEY: str = "change-this-in-production"
    # Sprint E.1 #26: dual-key rotation support (ADR-AUTH-001).
    # When SECRET_KEY rotates, set this to the previous value for the
    # transition window (≤7 days). decode_token() falls back to this
    # key on InvalidSignatureError so existing JWTs keep validating.
    # Unset after all old tokens have expired (refresh TTL = 7 days).
    SECRET_KEY_LEGACY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # R-007 (Sprint 1 Quick Wins): aud + iss validation no JWT.
    # Default None preserva backward compat (tokens legacy passam). Quando setados,
    # decode_token enforce aud/iss strictly e create_access_token inclui as claims.
    # Migration plan: setar em prod e invalidar tokens legacy via key rotation gradual.
    JWT_AUDIENCE: str | None = None
    JWT_ISSUER: str | None = None

    # WorkOS
    # Rails JWT shared secret (same as Rails secret_key_base)
    RAILS_JWT_SECRET_KEY: str | None = None
    # Phase 1 Auth Decoupling: enable DB-backed cache for Rails user resolution.
    # True (default): checks users.rails_user_id before calling Rails GET /v1/me.
    # False: reverts to in-memory-only cache (instant rollback if DB issues).
    FASTAPI_RAILS_DB_CACHE: bool = True
    # Phase 1b: FastAPI is the sole JWT issuer. When True, Rails JWT fallback
    # raises 401 with upgrade_required=True instead of silently accepting.
    # Default False = backward compat (Rails JWTs still accepted).
    # Flip to True only after all active users have FastAPI JWTs.
    FASTAPI_AUTH_PRIMARY: bool = False
    # Phase 2a: WorkOS SSO callback issues FastAPI JWT (lia_access_token).
    # Default False = backward compat (workos_session cookie still used).
    WORKOS_FASTAPI_JWT: bool = False
    # Phase 2b: Magic-link verification done by FastAPI instead of Rails.
    # Default False = backward compat (Rails magic-link still used).
    FASTAPI_MAGIC_LINK_PRIMARY: bool = False
    WORKOS_CLIENT_ID: str | None = None
    WORKOS_API_KEY: str | None = None
    WORKOS_WEBHOOK_SECRET: str | None = None

    # Azure AD / Microsoft Graph (client credentials — service-to-service)
    AZURE_TENANT_ID: str | None = Field(default=None, validation_alias=AliasChoices("AZURE_TENANT_ID", "MICROSOFT_TENANT_ID"))
    AZURE_CLIENT_ID: str | None = None
    AZURE_CLIENT_SECRET: str | None = None

    # Microsoft Calendar OAuth 2.0 delegated flow (user-level calendar access per company)
    # If absent, falls back to client-credentials app-level access.
    MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI: str | None = None
    MICROSOFT_CALENDAR_DEFAULT_TIMEZONE: str = "America/Sao_Paulo"

    # Microsoft Teams
    MICROSOFT_APP_ID: str | None = None
    MICROSOFT_APP_PASSWORD: str | None = None
    # TEAMS_WEBHOOK_URL — Incoming Webhook URL for proactive outbound delivery.
    # Without this, TeamsService runs in dev mode (messages logged only, not sent).
    # How to obtain: Teams channel → click channel name → Manage channel →
    #   Connectors → search "Incoming Webhook" → Configure → copy generated URL.
    # See also: Configurações → Integrações → Microsoft Teams in the LIA UI.
    TEAMS_WEBHOOK_URL: str | None = None
    TEAMS_WEBHOOK_SECRET: str | None = None
    # Home tenant of the Bot App Registration (used for outbound token acquisition)
    # Separate from AZURE_TENANT_ID which is used for Graph API
    TEAMS_APP_TENANT_ID: str | None = Field(default=None)

    # Secrets provider (Phase 5)
    SECRETS_PROVIDER: str = "env"  # "env" (dev) | "doppler" (prod)
    DOPPLER_TOKEN: str | None = None

    # Admin API key (for internal endpoints)
    ADMIN_API_KEY: str | None = None


# ---------------------------------------------------------------------------
# 7. App / Feature Flags
# ---------------------------------------------------------------------------


class AppSettings(BaseSettings):
    APP_NAME: str = "lia-agent-system"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "0.1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    APP_BASE_URL: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5000", "http://localhost:3000", "http://127.0.0.1:5000"]

    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    _DEPRECATED_DEFAULT_COMPANY_UUID: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    # Feature Flags
    ENABLE_PEARCH_AI: bool = False
    ENABLE_TWILIO: bool = False
    ENABLE_MICROSOFT_GRAPH: bool = True
    ENABLE_GOOGLE_CALENDAR: bool = False
    FAIRNESS_LAYER3_ENABLED: bool = True  # P1-3 (2026-05-10): default-on para Inegociável #3 (FairnessGuard 100% high-impact). Layer 3 só dispara em sourcing search + JD import (custo controlado via Haiku + cache 1h)
    # LIA-C03: FairnessGuard check em tool call args no TimedToolNode (env: FAIRNESS_TOOL_CHECK_ENABLED)
    FAIRNESS_TOOL_CHECK_ENABLED: bool = True
    # LGPD consent enforcement: False=soft (aviso+continua), True=hard (bloqueia ausência como revogado)
    LGPD_CONSENT_ABSENT_HARD_BLOCK: bool = False

    # Pipeline AI flags
    ENABLE_LLM_INTERPRET_CONTEXT: bool = True
    ENABLE_LLM_DISPATCH_PERSONALIZATION: bool = True
    ENABLE_LLM_INFER_BEHAVIOR: bool = True
    ENABLE_LLM_SUBSTATUS_PREDICTION: bool = True

    # LangGraph native mode flag
    USE_LANGGRAPH_NATIVE: bool = False

    # WebSocket
    WS_MAX_CONNECTIONS_PER_TENANT: int = 100

    # ReAct Loop
    REACT_MAX_ITERATIONS_DEFAULT: int = 5
    REACT_MAX_TOOL_CALLS: int = 3
    REACT_OBSERVATION_MAX_CHARS: int = 5000
    REACT_DUPLICATE_THRESHOLD: int = 2
    REACT_TOKEN_BUDGET_ENABLED: bool = False
    REACT_TOKEN_BUDGET_DEFAULT: int = 100000

    # Orchestrator
    ROUTER_SUMMARY_EVERY_N_MESSAGES: int = 10

    # Tenant Budget (Phase 2)
    TENANT_TOKEN_BUDGET_DEFAULT: int = 500000
    TENANT_TOKEN_BUDGET_ALERT_THRESHOLD: float = 0.80
    TENANT_PER_REQUEST_TOKEN_THRESHOLD: int = 50000

    # Chunking defaults (per doc type)
    CHUNKING_CV_CHUNK_SIZE: int = 1500
    CHUNKING_CV_OVERLAP: int = 150
    CHUNKING_JD_CHUNK_SIZE: int = 1200
    CHUNKING_JD_OVERLAP: int = 100
    CHUNKING_GENERIC_CHUNK_SIZE: int = 1000
    CHUNKING_GENERIC_OVERLAP: int = 100
    CHUNKING_POLICY_CHUNK_SIZE: int = 1800
    CHUNKING_POLICY_OVERLAP: int = 200

    # Plan Limits
    PLAN_LIMITS_ENFORCE: bool = True
    PLAN_STARTER_ACTIVE_JOBS: int = 5
    PLAN_STARTER_USERS: int = 3
    PLAN_STARTER_CANDIDATES_PER_JOB: int = 200
    PLAN_PRO_ACTIVE_JOBS: int = 20
    PLAN_PRO_USERS: int = 10
    PLAN_PRO_CANDIDATES_PER_JOB: int = 2000
    PLAN_ENTERPRISE_ACTIVE_JOBS: int = 9999
    PLAN_ENTERPRISE_USERS: int = 9999
    PLAN_ENTERPRISE_CANDIDATES_PER_JOB: int = 9999
    PLAN_TRIAL_ACTIVE_JOBS: int = 3
    PLAN_TRIAL_USERS: int = 2
    PLAN_TRIAL_CANDIDATES_PER_JOB: int = 50


# ---------------------------------------------------------------------------
# Remaining settings (integrations, not yet categorized)
# ---------------------------------------------------------------------------


class IntegrationSettings(BaseSettings):
    # Pearch AI
    PEARCH_API_KEY: str | None = None
    PEARCH_API_URL: str = "https://api.pearch.ai"
    # Task #961 — timeouts canônicos (config-driven) para o pipeline de busca.
    # Política httpx.Timeout explícita evita stalls indefinidos quando o
    # upstream Pearch fica preso em connect/read/write/pool sem fechar o
    # socket, e os deadlines asyncio garantem hard-stop antes do proxy do
    # Next.js (90s) ou do client browser interromperem a request.
    PEARCH_HTTP_CONNECT_TIMEOUT_SECONDS: float = 5.0
    PEARCH_HTTP_READ_TIMEOUT_SECONDS: float = 10.0
    PEARCH_HTTP_WRITE_TIMEOUT_SECONDS: float = 5.0
    PEARCH_HTTP_POOL_TIMEOUT_SECONDS: float = 5.0
    # Hard deadline na chamada externa Pearch (envolve search_candidates):
    # supera read_timeout para acomodar 1 retry de tenacity (stop_after_attempt=2)
    # mas mantém-se abaixo do deadline da rota.
    # BUG-PEARCH-TIMEOUT (2026-06-09): API v2 /v2/search demora ~26s (retrieval
    # 14s + scoring 5s + insights 4s). Elevado de 12s para 35s.
    PEARCH_CALL_DEADLINE_SECONDS: float = 35.0
    # Hard deadline da rota POST /api/v1/search/candidates: cobre busca local
    # + chamada Pearch. Acima disso devolvemos resposta degradada (warning).
    # BUG-PEARCH-TIMEOUT (2026-06-09): elevado de 18s para 45s para acomodar
    # os 35s de PEARCH_CALL_DEADLINE_SECONDS + margem local + dedup.
    SEARCH_CANDIDATES_DEADLINE_SECONDS: float = 45.0
    # Reveal-sob-demanda (Paulo): por padrao NAO enriquece contato via Apify
    # durante a busca (era lento -> 504 + gasto Apify automatico) nem descarta
    # candidatos sem contato revelado. Contato vem sob demanda (botao/auto-reveal).
    SEARCH_EAGER_CONTACT_ENRICHMENT: bool = False

    # Task #1219 — busca "Híbrida com email" (require_emails=True) roda um loop de
    # completude: combina pool local + páginas adicionais da Pearch até acumular
    # o alvo (pearch_limit) de candidatos COM email, ou até esgotar fontes.
    # Guardrails: deadline interno (< deadline da rota) + teto de páginas.
    # O loop só dispara quando require_emails=True; demais modos seguem 1 lote.
    SEARCH_HYBRID_EMAIL_LOOP_DEADLINE_SECONDS: float = 38.0
    SEARCH_HYBRID_EMAIL_MAX_PAGES: int = 4

    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_WHATSAPP_NUMBER: str | None = None
    TWILIO_VOICE_NUMBER: str | None = None
    TWILIO_WEBHOOK_BASE_URL: str | None = None

    # Google Calendar
    GOOGLE_CALENDAR_CLIENT_ID: str | None = None
    GOOGLE_CALENDAR_CLIENT_SECRET: str | None = None
    GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: str | None = None
    GOOGLE_CALENDAR_DEFAULT_TIMEZONE: str = "America/Sao_Paulo"
    GOOGLE_CALENDAR_OAUTH_REDIRECT_URI: str | None = None

    # Email (Mailgun primary, Resend fallback)
    MAILGUN_API_KEY: str | None = None  # Required for email sending
    MAILGUN_DOMAIN: str | None = None  # Required for email sending (ex: mg.wedotalent.com)
    MAILGUN_API_BASE: str = "https://api.mailgun.net/v3"
    RESEND_API_KEY: str | None = None  # Fallback when Mailgun is unavailable
    EMAIL_FROM_ADDRESS: str = "noreply@wedotalent.com"
    EMAIL_FROM_NAME: str = "WeDOTalent"

    # HubSpot CRM
    HUBSPOT_API_KEY: str | None = None
    HUBSPOT_PORTAL_ID: str | None = None

    # Stripe Billing
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None

    # Apify (web scraping)
    APIFY_API_KEY: str | None = None
    APIFY_COST_PER_ENRICHMENT_USD: float = 0.01
    APIFY_ENRICHMENT_TIMEOUT_SECONDS: int = 30
    APIFY_MAX_CONCURRENT_ENRICHMENTS: int = 5
    APIFY_LEGACY_ACTOR: str = "anchor/linkedin-person-scraper"

    # Merge.dev (multi-ATS)
    MERGE_API_KEY: str | None = None

    # Gupy / Pandapé ATS
    GUPY_API_KEY: str | None = None
    PANDAPE_API_KEY: str | None = None


# ---------------------------------------------------------------------------
# Final Settings — inherits all subclasses (backward compatible)
# ---------------------------------------------------------------------------


class Settings(
    DatabaseSettings,
    CacheSettings,
    MessagingSettings,
    LLMSettings,
    AuditSettings,
    AuthSettings,
    AppSettings,
    IntegrationSettings,
):
    """
    Configuração completa da aplicação.

    Todos os campos são acessíveis diretamente em `settings.<FIELD_NAME>`.
    A herança múltipla garante retrocompatibilidade total com código existente.
    """

    @model_validator(mode="after")
    def validate_secret_key(self):
        if self.APP_ENV == "production" and (not self.SECRET_KEY or self.SECRET_KEY == "change-this-in-production"):
            raise ValueError(
                "SECRET_KEY deve ser configurado via variável de ambiente em produção. "
                "Defina SECRET_KEY=<valor seguro> no seu .env ou nas variáveis de ambiente."
            )
        return self

    @model_validator(mode="after")
    def _redirect_redis_url_in_dev(self):
        """Dev guard: impede que desenvolvimento consuma a quota do Redis remoto.

        Quando APP_ENV != "production" e REDIS_URL aponta para host remoto
        (ex.: Upstash, free tier 500k cmd/mes), redireciona para o
        redis-server local que o workflow `lia-backend` ja sobe
        (redis://localhost:6379/0). Cobre app + Celery + todos os
        consumidores de settings.REDIS_URL de uma vez (fix no produtor).

        Escape hatch: LIA_DEV_ALLOW_REMOTE_REDIS=true forca o remoto em dev.
        Producao (APP_ENV=production) nunca e afetada.
        """
        import os

        # APP_ENV nao e confiavel sozinho: o workspace Replit de DEV pode ter
        # APP_ENV=production setado como Secret. Sinal robusto de dev: estar no
        # workspace de edicao do Replit (REPLIT_DEV_DOMAIN presente) e NAO num
        # Replit Deployment. Producao real (Cloud Run) nao tem env REPLIT_*.
        on_replit_workspace = bool(os.getenv("REPLIT_DEV_DOMAIN")) and not os.getenv(
            "REPLIT_DEPLOYMENT"
        )
        if self.APP_ENV == "production" and not on_replit_workspace:
            return self
        if os.getenv("LIA_DEV_ALLOW_REMOTE_REDIS", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        ):
            return self
        if _redis_host_is_local(self.REDIS_URL):
            return self

        import logging
        from urllib.parse import urlparse

        remote_host = urlparse(self.REDIS_URL).hostname or "?"
        logging.getLogger(__name__).warning(
            "[Redis] DEV GUARD: REDIS_URL aponta p/ host remoto (%s) em APP_ENV=%s; "
            "redirecionando p/ redis://localhost:6379/0 para NAO consumir quota "
            "remota em desenvolvimento. Para forcar o remoto, set "
            "LIA_DEV_ALLOW_REMOTE_REDIS=true.",
            remote_host,
            self.APP_ENV,
        )
        local_url = "redis://localhost:6379/0"
        self.REDIS_URL = local_url
        # ~18 consumidores leem os.getenv("REDIS_URL") direto (bypass de
        # settings.REDIS_URL): get_redis, rate_limiter, response_cache_service,
        # hitl_service, etc. Reescrever o env garante que TODOS usem o Redis
        # local em dev. Seguro: so ocorre fora de producao.
        os.environ["REDIS_URL"] = local_url
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
