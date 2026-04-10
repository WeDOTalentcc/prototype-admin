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
from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# 1. Database
# ---------------------------------------------------------------------------

class DatabaseSettings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    ELASTICSEARCH_URL: Optional[str] = None
    # Search backend selector: "postgres" (padrão) | "elasticsearch" (alto volume)
    SEARCH_BACKEND: str = "postgres"


# ---------------------------------------------------------------------------
# 2. Cache (Redis)
# ---------------------------------------------------------------------------

class CacheSettings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    ROUTER_CACHE_TTL: int = 3600          # Tier 1 cache TTL (segundos)
    SEMANTIC_CACHE_TTL: int = 86400       # Semantic cache TTL (segundos)
    ROUTER_CACHE_MAX_SIZE: int = 1000     # Max entries in-process LRU cache
    # Z5-03: threshold semântico configurável (Tier 3 — VectorSemanticCache)
    ROUTER_VECTOR_SIMILARITY_THRESHOLD: float = 0.85  # Cosine similarity floor para cache hit (reduzido de 0.92 para capturar queries semanticamente similares)
    ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN: float = 0.05  # Loga near-misses dentro de threshold-margin
    ROUTER_VECTOR_CACHE_ENABLED: bool = True           # A/B flag: False desabilita Tier 3 completamente


# ---------------------------------------------------------------------------
# 3. Messaging (RabbitMQ / Celery)
# ---------------------------------------------------------------------------

class MessagingSettings(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "rh_platform"
    RABBITMQ_PREFETCH: int = 1
    # Celery uses REDIS_URL as broker by default; these allow override
    CELERY_BROKER_URL: Optional[str] = None   # Falls back to REDIS_URL if not set
    CELERY_RESULT_BACKEND: Optional[str] = None  # Falls back to REDIS_URL if not set
    # Broker abstraction layer — see app/shared/messaging/broker_interface.py
    # Valores: "redis" (padrão), "rabbitmq" (on-prem), "pubsub" (stub GCP)
    # Para migração GCP: setar BROKER_BACKEND=pubsub e implementar PubSubBroker real
    BROKER_BACKEND: str = "redis"


# ---------------------------------------------------------------------------
# 4. LLM / AI Settings
# ---------------------------------------------------------------------------

class LLMSettings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_REGION: str = "us-east1"

    # Replit AI Integrations
    AI_INTEGRATIONS_GEMINI_API_KEY: Optional[str] = None
    AI_INTEGRATIONS_GEMINI_BASE_URL: Optional[str] = None
    AI_INTEGRATIONS_ANTHROPIC_API_KEY: Optional[str] = None
    AI_INTEGRATIONS_ANTHROPIC_BASE_URL: Optional[str] = None
    AI_INTEGRATIONS_OPENAI_API_KEY: Optional[str] = None
    AI_INTEGRATIONS_OPENAI_BASE_URL: Optional[str] = None

    # Model Names
    LLM_PRIMARY_MODEL: str = "claude-sonnet-4-6"
    LLM_FAST_MODEL: str = "gemini-2.5-flash"              # Tier rápido — Gemini Flash (padrão)
    LLM_POWERFUL_MODEL: str = "claude-opus-4-6"
    LLM_GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_ROUTER_MODEL: str = "gemini-2.5-flash"            # Roteamento barato (Tier 3) — Gemini Flash
    LLM_AGENT_MODEL: str = "claude-sonnet-4-6"            # Execução de agentes (Claude mantido para profundidade)
    LLM_DEFAULT_PROVIDER: str = "gemini"                  # Provider padrão — Gemini 2.5 Flash

    # Generation parameters
    LLM_DEFAULT_TEMPERATURE: float = 0.7
    LLM_AGENT_TEMPERATURE: float = 0.3
    LLM_ROUTER_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: float = 120.0

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
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "lia-agent-system"

    # Z6-02: OpenTelemetry / OTLP
    OTEL_SERVICE_NAME: str = "lia-agent-system"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # ex: http://jaeger:4318 — vazio = desabilitado
    OTEL_TRACES_ENABLED: bool = True


# ---------------------------------------------------------------------------
# 5. Audit Storage (Phase 1)
# ---------------------------------------------------------------------------

class AuditSettings(BaseSettings):
    AUDIT_STORAGE_TYPE: str = "file"         # "file" (dev) | "s3" (prod)
    AUDIT_STORAGE_BUCKET: str = ""           # S3 bucket — obrigatório quando type=s3
    AUDIT_STORAGE_PREFIX: str = "audit"      # Prefixo de path no S3
    AUDIT_LOCAL_DIR: str = "./audit_logs"    # Diretório local (dev)
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"


# ---------------------------------------------------------------------------
# 6. Auth (JWT, WorkOS, Azure)
# ---------------------------------------------------------------------------

class AuthSettings(BaseSettings):
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # WorkOS
    # Rails JWT shared secret (same as Rails secret_key_base)
    RAILS_JWT_SECRET_KEY: Optional[str] = None
    WORKOS_CLIENT_ID: Optional[str] = None
    WORKOS_API_KEY: Optional[str] = None
    WORKOS_WEBHOOK_SECRET: Optional[str] = None

    # Azure AD / Microsoft Graph (client credentials — service-to-service)
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None

    # Microsoft Calendar OAuth 2.0 delegated flow (user-level calendar access per company)
    # If absent, falls back to client-credentials app-level access.
    MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI: Optional[str] = None
    MICROSOFT_CALENDAR_DEFAULT_TIMEZONE: str = "America/Sao_Paulo"

    # Microsoft Teams
    MICROSOFT_APP_ID: Optional[str] = None
    MICROSOFT_APP_PASSWORD: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_SECRET: Optional[str] = None
    # Home tenant of the Bot App Registration (used for outbound token acquisition)
    # Separate from AZURE_TENANT_ID which is used for Graph API
    TEAMS_APP_TENANT_ID: Optional[str] = None

    # Secrets provider (Phase 5)
    SECRETS_PROVIDER: str = "env"            # "env" (dev) | "doppler" (prod)
    DOPPLER_TOKEN: Optional[str] = None

    # Admin API key (for internal endpoints)
    ADMIN_API_KEY: Optional[str] = None


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
    CORS_ORIGINS: List[str] = ["http://localhost:5000", "http://localhost:3000", "http://127.0.0.1:5000"]

    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    _DEPRECATED_DEFAULT_COMPANY_UUID: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    # Feature Flags
    ENABLE_PEARCH_AI: bool = False
    ENABLE_TWILIO: bool = False
    ENABLE_MICROSOFT_GRAPH: bool = True
    ENABLE_GOOGLE_CALENDAR: bool = False
    FAIRNESS_LAYER3_ENABLED: bool = False
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
    PEARCH_API_KEY: Optional[str] = None
    PEARCH_API_URL: str = "https://api.pearch.ai"

    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    TWILIO_VOICE_NUMBER: Optional[str] = None
    TWILIO_WEBHOOK_BASE_URL: Optional[str] = None

    # Google Calendar
    GOOGLE_CALENDAR_CLIENT_ID: Optional[str] = None
    GOOGLE_CALENDAR_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: Optional[str] = None
    GOOGLE_CALENDAR_DEFAULT_TIMEZONE: str = "America/Sao_Paulo"
    GOOGLE_CALENDAR_OAUTH_REDIRECT_URI: Optional[str] = None

    # Email (Mailgun primary, Resend fallback)
    MAILGUN_API_KEY: Optional[str] = None     # Required for email sending
    MAILGUN_DOMAIN: Optional[str] = None      # Required for email sending (ex: mg.wedotalent.com)
    MAILGUN_API_BASE: str = "https://api.mailgun.net/v3"
    RESEND_API_KEY: Optional[str] = None      # Fallback when Mailgun is unavailable
    EMAIL_FROM_ADDRESS: str = "noreply@wedotalent.com"
    EMAIL_FROM_NAME: str = "WeDOTalent"

    # HubSpot CRM
    HUBSPOT_API_KEY: Optional[str] = None
    HUBSPOT_PORTAL_ID: Optional[str] = None

    # Stripe Billing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    # Apify (web scraping)
    APIFY_API_KEY: Optional[str] = None

    # Merge.dev (multi-ATS)
    MERGE_API_KEY: Optional[str] = None

    # Gupy / Pandapé ATS
    GUPY_API_KEY: Optional[str] = None
    PANDAPE_API_KEY: Optional[str] = None


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

    @model_validator(mode='after')
    def validate_secret_key(self):
        if self.APP_ENV == "production" and (
            not self.SECRET_KEY or self.SECRET_KEY == "change-this-in-production"
        ):
            raise ValueError(
                "SECRET_KEY deve ser configurado via variável de ambiente em produção. "
                "Defina SECRET_KEY=<valor seguro> no seu .env ou nas variáveis de ambiente."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
