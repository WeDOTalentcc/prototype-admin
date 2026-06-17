# Theme: O2 — Configuration & Feature Flags — Operational Layer

## O que é este tema

O tema cobre dois sistemas complementares de controle de comportamento da plataforma:

1. **Configuração estática** — `libs/config/lia_config/config.py`: settings via `pydantic-settings` lidos de variáveis de ambiente (`.env` ou Doppler em produção), acessíveis via singleton `settings.<FIELD>`. Controlam infraestrutura, modelos LLM, limites e integrações.

2. **Feature flags runtime** — `app/shared/governance/feature_flag_service.py`: toggles persistidos em banco de dados com prioridade por empresa, rollout gradual por percentual e expiração. Controlam comportamento de produto por tenant sem redeploy.

3. **Secrets Provider** — `app/core/secrets_provider.py`: abstração com dois backends (`env` dev, `doppler` produção) que isola acesso a credentials da lógica de negócio.

4. **Module gating** — `app/shared/module_gating.py`: controla acesso a ferramentas premium/TASTING com degraded responses e CTAs para módulos inativos.

**Boundary com temas irmãos:** I4 (LLM Providers) consome `LLMSettings` do `config.py`. R3 (Messaging) usa `BROKER_BACKEND` e `RABBITMQ_URL`. C5 (Multi-tenancy) usa `FeatureFlagService` com `company_id`. O tema O2 documenta como configurar e fazer toggle; os temas consumidores documentam o que cada config controla.

---

## Arquivos conectados (7 total)

### Camada Código (7 arquivos Python)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|----------------|
| `config.py` | `libs/config/lia_config/config.py` | Settings Pydantic com 8 subclasses + singleton `settings` |
| `feature_flag_service.py` | `app/shared/governance/feature_flag_service.py` | Flags DB-backed com 3-tier priority + rollout % |
| `secrets_provider.py` | `app/core/secrets_provider.py` | ABC SecretsProvider + EnvProvider + DopplerProvider |
| `module_gating.py` | `app/shared/module_gating.py` | TOOL_MODULE_MAP + PREMIUM/TASTING tools + degraded responses |
| `feature_flag_service.py` (app/shared) | `app/shared/governance/feature_flag_service.py` | Runtime flags por tenant |
| `.env.example` | `.env.example` (213 linhas) | Template de variáveis de ambiente |
| `.env.production.example` | `.env.production.example` | Template de variáveis de produção |

### Integration points

- **I4 LLM Providers** → consome `LLMSettings` (API keys, model names, temperatures, cascade thresholds)
- **R3 Messaging** → `MessagingSettings.BROKER_BACKEND` (redis/rabbitmq/pubsub)
- **R4 Background Jobs** → `AppSettings.ENABLE_SCHEDULED_REPORTS` + Celery broker URLs
- **C5 Multi-tenancy** → `FeatureFlagService.is_enabled(db, flag_key, company_id)` por tenant
- **C7 Audit Trail** → `AuditSettings.AUDIT_STORAGE_TYPE` (file/s3) + S3 config
- **I5 Observability** → `AppSettings.SENTRY_DSN` + `LLMSettings.OTEL_*`
- **AS1 Agent Studio** → `PLAN_LIMITS_ENFORCE` + plan limits por tier

---

## Lógica IN → OUT

### Input (config estático)

```bash
# 1. Arquivo .env na raiz do projeto (carregado pelo pydantic-settings)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
ANTHROPIC_API_KEY=sk-ant-...
APP_ENV=production
SECRET_KEY=<valor-seguro>
SECRETS_PROVIDER=doppler
DOPPLER_TOKEN=dp.st....

# 2. Variáveis de ambiente do processo (sobrescrevem .env)
export FAIRNESS_LAYER3_ENABLED=true
```

### Input (feature flag runtime)

```python
# Verificar flag para tenant específico
enabled = await feature_flag_service.is_enabled(
    db=db,
    flag_key="ENABLE_AUTO_SCREENING",
    company_id="company-uuid-123"
)
```

### Processing (config)

```
1. Na inicialização do processo: Settings() instanciado como singleton
2. pydantic-settings lê: .env file → env vars → defaults
3. model_config: env_file=".env", case_sensitive=True, extra="ignore"
4. @model_validator validate_secret_key() roda:
   - Se APP_ENV=production E SECRET_KEY="change-this-in-production" → ValueError (startup falha)
5. settings = Settings() exportado como singleton de módulo
```

### Processing (feature flag)

```
1. is_enabled(db, flag_key, company_id):
   a. Busca FeatureFlag WHERE flag_key=X AND company_id=Y → flag por empresa
   b. Busca FeatureFlag WHERE flag_key=X AND company_id IS NULL → flag global
   c. Fallback para DEFAULT_FLAGS[flag_key]["default"]
2. _evaluate_flag(flag):
   a. expires_at < now() → False (expirado)
   b. is_enabled=False → False
   c. rollout_percentage < 100 → random.randint(1,100) <= rollout_percentage
   d. rollout_percentage=100 → True
3. Em caso de exceção: retorna DEFAULT_FLAGS default (fail-safe)
```

### Output (config)

```python
# Acesso via singleton — qualquer módulo
from lia_config.config import settings

settings.DATABASE_URL         # str
settings.ANTHROPIC_API_KEY    # Optional[str]
settings.FAIRNESS_LAYER3_ENABLED  # bool
settings.PLAN_LIMITS_ENFORCE  # bool
```

### Output (feature flag)

```python
# Bool — fail-safe (nunca lança exceção para chamador)
enabled: bool = await feature_flag_service.is_enabled(db, "ENABLE_AUTO_SCREENING", company_id)
```

---

## Componentes críticos

### Settings — 8 subclasses

**1. DatabaseSettings**
```python
DATABASE_URL: str = "postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db"
DATABASE_POOL_SIZE: int = 20
DATABASE_MAX_OVERFLOW: int = 10
ELASTICSEARCH_URL: Optional[str] = None
SEARCH_BACKEND: str = "postgres"  # "postgres" | "elasticsearch"
```

**2. CacheSettings**
```python
REDIS_URL: str = "redis://localhost:6379/0"
ROUTER_CACHE_TTL: int = 3600           # Tier 1 LRU cache TTL (s)
SEMANTIC_CACHE_TTL: int = 86400        # Tier 3 vector cache TTL (s)
ROUTER_CACHE_MAX_SIZE: int = 1000      # Max entries in-process LRU
ROUTER_VECTOR_SIMILARITY_THRESHOLD: float = 0.85  # Cosine sim floor
ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN: float = 0.05
ROUTER_VECTOR_CACHE_ENABLED: bool = True  # A/B: False desabilita Tier 3
```

**3. MessagingSettings**
```python
RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
RABBITMQ_EXCHANGE: str = "rh_platform"
RABBITMQ_PREFETCH: int = 1
CELERY_BROKER_URL: Optional[str] = None    # fallback: REDIS_URL
CELERY_RESULT_BACKEND: Optional[str] = None  # fallback: REDIS_URL
BROKER_BACKEND: str = "redis"  # "redis" | "rabbitmq" | "pubsub"
```

**4. LLMSettings**
```python
# API Keys (todas Optional — ausência = provider desabilitado)
ANTHROPIC_API_KEY: Optional[str] = None
OPENAI_API_KEY: Optional[str] = None
GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

# AI Integrations (Replit proxy keys)
AI_INTEGRATIONS_GEMINI_API_KEY: Optional[str] = None
AI_INTEGRATIONS_ANTHROPIC_API_KEY: Optional[str] = None

# Model names
# Nota: "claude-sonnet-4-6" e "claude-opus-4-6" são os model IDs reais no
# Replit AI Integrations proxy (verificado SSH 2026-04-24). NÃO são typos de
# "claude-sonnet-4-5" etc. — o proxy Replit usa naming próprio. Em deploy
# fora do Replit, substituir pelos IDs Anthropic canônicos do ambiente.
LLM_PRIMARY_MODEL: str = "claude-sonnet-4-6"
LLM_FAST_MODEL: str = "gemini-2.5-flash"
LLM_POWERFUL_MODEL: str = "claude-opus-4-6"
LLM_ROUTER_MODEL: str = "gemini-2.5-flash"  # roteamento barato
LLM_AGENT_MODEL: str = "claude-sonnet-4-6"  # execução de agentes
LLM_DEFAULT_PROVIDER: str = "gemini"

# Generation params
LLM_DEFAULT_TEMPERATURE: float = 0.7
LLM_AGENT_TEMPERATURE: float = 0.3
LLM_ROUTER_TEMPERATURE: float = 0.1
LLM_MAX_TOKENS: int = 4096
LLM_TIMEOUT_SECONDS: float = 120.0

# Cascade thresholds
LLM_CASCADE_FAST_THRESHOLD: float = 0.80
LLM_CASCADE_MID_THRESHOLD: float = 0.70
LLM_CASCADE_FALLBACK_THRESHOLD: float = 0.60

# Router confidence
ROUTER_FAST_CONFIDENCE_THRESHOLD: float = 0.7
ROUTER_CONFIDENCE_THRESHOLD: float = 0.80

EMBEDDING_DEFAULT_PROVIDER: str = "gemini"  # "gemini" (768-dim) | "openai"

# Observabilidade
LANGCHAIN_TRACING_V2: bool = False
OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # vazio = OTEL desabilitado
OTEL_TRACES_ENABLED: bool = True
```

**5. AuditSettings**
```python
AUDIT_STORAGE_TYPE: str = "file"    # "file" (dev) | "s3" (prod)
AUDIT_STORAGE_BUCKET: str = ""      # obrigatório quando type=s3
AUDIT_LOCAL_DIR: str = "./audit_logs"
S3_ACCESS_KEY: Optional[str] = None
S3_SECRET_KEY: Optional[str] = None
S3_REGION: str = "us-east-1"
```

**6. AuthSettings**
```python
SECRET_KEY: str = "change-this-in-production"  # validator bloqueia em prod
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
RAILS_JWT_SECRET_KEY: Optional[str] = None     # shared secret Rails↔Python
WORKOS_CLIENT_ID, WORKOS_API_KEY, WORKOS_WEBHOOK_SECRET: Optional[str]
AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET: Optional[str]
MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD: Optional[str]
SECRETS_PROVIDER: str = "env"  # "env" | "doppler"
DOPPLER_TOKEN: Optional[str] = None
ADMIN_API_KEY: Optional[str] = None
```

**7. AppSettings — Feature Flags via Env**
```python
APP_ENV: str = "development"   # "development" | "staging" | "production"
DEBUG: bool = True

# Integrações externas (opt-in)
ENABLE_PEARCH_AI: bool = False
ENABLE_TWILIO: bool = False
ENABLE_MICROSOFT_GRAPH: bool = True
ENABLE_GOOGLE_CALENDAR: bool = False

# Compliance
FAIRNESS_LAYER3_ENABLED: bool = False       # FairnessGuard L3 (LLM judge)
FAIRNESS_TOOL_CHECK_ENABLED: bool = True    # Check args de tool calls
LGPD_CONSENT_ABSENT_HARD_BLOCK: bool = False  # soft=aviso | hard=bloqueia

# LLM pipeline
ENABLE_LLM_INTERPRET_CONTEXT: bool = True
ENABLE_LLM_DISPATCH_PERSONALIZATION: bool = True
ENABLE_LLM_INFER_BEHAVIOR: bool = True
ENABLE_LLM_SUBSTATUS_PREDICTION: bool = True

# Infra
USE_LANGGRAPH_NATIVE: bool = False
WS_MAX_CONNECTIONS_PER_TENANT: int = 100
PLAN_LIMITS_ENFORCE: bool = True
REACT_TOKEN_BUDGET_ENABLED: bool = False

# ReAct Loop limits
REACT_MAX_ITERATIONS_DEFAULT: int = 5
REACT_MAX_TOOL_CALLS: int = 3
REACT_OBSERVATION_MAX_CHARS: int = 5000

# Tenant Budget
TENANT_TOKEN_BUDGET_DEFAULT: int = 500000
TENANT_TOKEN_BUDGET_ALERT_THRESHOLD: float = 0.80

# Chunking (por doc type)
CHUNKING_CV_CHUNK_SIZE: int = 1500 / OVERLAP: int = 150
CHUNKING_JD_CHUNK_SIZE: int = 1200 / OVERLAP: int = 100
CHUNKING_GENERIC_CHUNK_SIZE: int = 1000 / OVERLAP: int = 100
CHUNKING_POLICY_CHUNK_SIZE: int = 1800 / OVERLAP: int = 200

# Plan Limits (3 tiers + trial)
PLAN_STARTER_ACTIVE_JOBS: int = 5  / USERS: int = 3  / CANDIDATES: int = 200
PLAN_PRO_ACTIVE_JOBS: int = 20     / USERS: int = 10 / CANDIDATES: int = 2000
PLAN_ENTERPRISE_*: int = 9999
PLAN_TRIAL_ACTIVE_JOBS: int = 3    / USERS: int = 2  / CANDIDATES: int = 50
```

**8. IntegrationSettings** (chaves opcionais, todas None por padrão)
```python
PEARCH_API_KEY, PEARCH_API_URL
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
GOOGLE_CALENDAR_CLIENT_ID, GOOGLE_CALENDAR_CLIENT_SECRET
MAILGUN_API_KEY, MAILGUN_DOMAIN, RESEND_API_KEY (fallback)
HUBSPOT_API_KEY, HUBSPOT_PORTAL_ID
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY
APIFY_API_KEY, APIFY_COST_PER_ENRICHMENT_USD=0.01
MERGE_API_KEY, GUPY_API_KEY, PANDAPE_API_KEY
```

### Settings — validator de produção

```python
# libs/config/lia_config/config.py
class Settings(...):
    @model_validator(mode='after')
    def validate_secret_key(self):
        if self.APP_ENV == "production" and (
            not self.SECRET_KEY or self.SECRET_KEY == "change-this-in-production"
        ):
            raise ValueError(
                "SECRET_KEY deve ser configurado via variável de ambiente em produção."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,   # DATABASE_URL != database_url
        extra="ignore",        # variáveis desconhecidas não causam erro
    )

settings = Settings()  # singleton de módulo
```

### FeatureFlagService — Runtime DB Flags

**Priority chain:**
```
company_id flag (DB) → global flag (company_id=NULL, DB) → DEFAULT_FLAGS[key]["default"]
```

**DEFAULT_FLAGS (12 flags):**

| Flag key | Category | Default |
|----------|----------|---------|
| `learning_hub_enabled` | learning | True |
| `outcome_learning_enabled` | learning | True |
| `stage_feedback_enabled` | learning | True |
| `skills_deduplication_enabled` | wizard | True |
| `analytics_dashboard_enabled` | analytics | True |
| `ai_suggestions_enhanced` | ai | True |
| `empty_field_notifications` | wizard | True |
| `field_toggles_enabled` | wizard | True |
| `ENABLE_AUTO_SCREENING` | automation | **False** |
| `ENABLE_AUTO_SCHEDULING` | automation | **False** |
| `ENABLE_AUTO_STAGE_ADVANCE` | automation | **False** |
| `CREW_DELEGATION_ENABLED` | agents | True |

**Rollout gradual:**
```python
def _evaluate_flag(self, flag: FeatureFlag) -> bool:
    if flag.expires_at and flag.expires_at < datetime.utcnow():
        return False
    if not flag.is_enabled:
        return False
    if flag.rollout_percentage < 100:
        return random.randint(1, 100) <= flag.rollout_percentage  # probabilístico
    return True
```

**Fail-safe:** exceção na consulta ao DB → retorna `DEFAULT_FLAGS.get(flag_key, {}).get("default", False)` (nunca propaga erro para o chamador).

**In-memory cache:** `_cache_ttl = 300` segundos (5 minutos). Evita N+1 no DB para verificações de flag por request.

### SecretsProvider — Abstração de Secrets

```python
# app/core/secrets_provider.py

class SecretsProvider(ABC):
    def get(self, key: str, default: str | None = None) -> str | None: ...
    def get_required(self, key: str) -> str: ...  # ValueError se ausente

class EnvProvider(SecretsProvider):
    def get(self, key, default=None) -> str | None:
        return os.environ.get(key, default)

class DopplerProvider(SecretsProvider):
    # subprocess: doppler secrets download --no-file --format=env
    # timeout: 10s; fallback para env se CLI falhar
    # carregado no __init__; cache em self._cache

def get_secrets_provider() -> SecretsProvider:
    from app.core.config import settings
    if settings.SECRETS_PROVIDER.lower() == "doppler":
        return DopplerProvider(token=settings.DOPPLER_TOKEN)
    return EnvProvider()

# Lazy singleton
def secrets() -> SecretsProvider:
    global _provider
    if _provider is None:
        _provider = get_secrets_provider()
    return _provider
```

### Module Gating — Premium Tools

```python
# app/shared/module_gating.py

TOOL_MODULE_MAP: dict[str, str] = {
    # talent_intelligence_pro (5): infer_related_skills, get_skill_adjacencies,
    #   analyze_skill_gaps, map_candidate_skills_to_ontology, get_market_intelligence
    # internal_mobility (1): match_internal_candidates
    # interview_intelligence (5): analyze_interview_recording, detect_interview_bias,
    #   generate_interview_opinion, generate_candidate_feedback, compare_interview_performance
    # workforce_planning (1): forecast_hiring_needs
    # candidate_nurture (2): create_nurture_sequence, get_engagement_metrics, suggest_reengagement
}

PREMIUM_GATED_TOOLS: set[str]  # 8 tools — bloqueadas sem módulo ativo
TASTING_TOOLS: set[str]        # 8 tools — disponíveis gratuitamente com BETA badge

_BETA_BADGE = " ℹ️ Este recurso está disponível gratuitamente durante o período BETA."

# Degraded response para módulo inativo:
# { summary: "...teaser...", cta: "Para acesso completo, ative o módulo X" }
```

**5 módulos premium:**

| Module key | Label PT-BR |
|------------|-------------|
| `talent_intelligence_pro` | Talent Intelligence Pro |
| `internal_mobility` | Internal Mobility Suite |
| `interview_intelligence` | Interview Intelligence Pro |
| `workforce_planning` | Workforce Planning |
| `candidate_nurture` | Candidate Nurture / CRM |

---

## Instruções para Claude Code / Cursor

### "Implementa configuração no v5"

**Passo 1 — Instalar dependências**
```bash
pip install pydantic-settings python-dotenv
```

**Passo 2 — Copiar config.py**
```bash
# Copiar libs/config/lia_config/config.py para o v5
# Ajustar: renomear campos de integração não usados, manter estrutura de subclasses
# NUNCA remover: validate_secret_key validator (segurança de produção)
# NUNCA hardcodar: DEFAULT_COMPANY_UUID (deprecated) ou qualquer API key
```

**Passo 3 — Criar .env base**
```bash
cp .env.example .env
# Preencher valores mínimos para dev:
echo "DATABASE_URL=postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db" >> .env
echo "REDIS_URL=redis://localhost:6379/0" >> .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "APP_ENV=development" >> .env
# NUNCA commitar .env — está em .gitignore
```

**Passo 4 — Importar settings corretamente**
```python
# ✅ CORRETO — import do pacote canônico
from lia_config.config import settings

# ❌ ERRADO — import direto de path relativo
from libs.config.lia_config.config import settings  # ADR-012: forbidden
```

**Passo 5 — Feature flag DB**
```bash
# Criar migration para tabela feature_flags
alembic revision --autogenerate -m "add_feature_flags"
# Deve criar: flag_key, company_id (NULL=global), is_enabled, rollout_percentage,
#              expires_at, description, category, flag_metadata
```

**Passo 6 — Secrets em produção**
```bash
# Configurar Doppler:
SECRETS_PROVIDER=doppler
DOPPLER_TOKEN=dp.st.xxxxx
# ou manter "env" e usar variáveis de ambiente injetadas pelo hosting
```

### "Adiciona feature flag nova"

1. Adicionar ao `DEFAULT_FLAGS` em `FeatureFlagService`:
   ```python
   "nova_feature_enabled": {
       "description": "Descrição clara da feature",
       "category": "ai",  # learning|wizard|analytics|ai|automation|agents
       "default": False   # sempre False para features novas (safe default)
   }
   ```
2. Consumir com `await feature_flag_service.is_enabled(db, "nova_feature_enabled", company_id)`
3. Para flags de configuração global (não por empresa), adicionar em `AppSettings` como `FEATURE_X: bool = False`

### "Adiciona config nova"

1. Identificar qual subclasse corresponde (`DatabaseSettings`, `LLMSettings`, etc.)
2. Adicionar campo com tipo + default seguro:
   ```python
   NOVA_CONFIG: int = 30  # Documentar unidade e range válido
   ```
3. Se obrigatório em produção, adicionar validator como `validate_secret_key`
4. Atualizar `.env.example` com o novo campo + comentário explicativo

### Setup em CLAUDE.md (snippet)

```markdown
## Configuration (O2)
- Fonte: themes/operational/O2_CONFIGURATION_AND_FEATURE_FLAGS.md
- Config: from lia_config.config import settings (NUNCA instanciar Settings() diretamente)
- Secrets: from app.core.secrets_provider import secrets (NÃO os.environ diretamente)
- Feature flags DB: await feature_flag_service.is_enabled(db, key, company_id)
- Feature flags env: settings.FAIRNESS_LAYER3_ENABLED, ENABLE_PEARCH_AI, etc.
- NUNCA commitar .env ou hardcodar API keys
- APP_ENV=production: SECRET_KEY deve ser definido ou startup falha
- Automation flags (ENABLE_AUTO_*) = False por default — opt-in via DB flag
```

### Setup em Cursor rules (.cursor/rules/config.mdc)

```
---
description: Configuration and feature flags rules
globs: ["*config*.py", "*settings*.py", "*feature_flag*.py", ".env*"]
---
# Configuration Rules
- Always import settings from lia_config.config (never from libs.* path)
- Never access os.environ directly — use secrets() from secrets_provider
- Feature flags: await feature_flag_service.is_enabled(db, key, company_id=from_jwt)
- ENABLE_AUTO_* defaults to False — never change defaults to True (safety rule)
- .env files: NEVER commit (add to .gitignore)
- Production: SECRET_KEY must be set or server won't start
- Module gating: tools in PREMIUM_GATED_TOOLS require active subscription
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexível porque |
|------|----------------|
| Nomes dos modelos LLM em `LLMSettings` | Model names mudam a cada versão; atualizar conforme disponibilidade |
| Valores default de TTLs e pool sizes | Tuning de performance, não arquiteturais |
| `DEFAULT_FLAGS` em `FeatureFlagService` | Novos flags podem ser adicionados; flags existentes não devem ter default alterado |
| Categories em `DEFAULT_FLAGS` | Naming convention, não contratos de API |
| Adição de novas subclasses ao Settings | Backward compatible se Settings herdar a nova subclasse |
| `.env.example` — comentários e organização | É documentação, não código |
| `IntegrationSettings` — adicionar integrações novas | Aditivo, sem remoção de campos existentes |

### NÃO pode adaptar (segurança ou arquitetural)

| Item | Por quê é imutável |
|------|--------------------|
| `validate_secret_key()` validator em produção | Segurança P0 — sem esse validator, deploy com SECRET_KEY padrão é vetor de ataque |
| `case_sensitive=True` no model_config | Consistency — alterar quebra todas as variáveis existentes no ambiente |
| `extra="ignore"` no model_config | Não foi `extra="forbid"` — mudança para forbid causa falha em ambientes com vars extras |
| `secrets()` via `SecretsProvider` (não `os.environ` direto) | Abstração necessária para rotação de secrets sem redeploy |
| `ENABLE_AUTO_SCREENING/SCHEDULING/STAGE_ADVANCE: False` | Flags de autonomia — default True cria risco de ações automáticas não autorizadas |
| `LGPD_CONSENT_ABSENT_HARD_BLOCK: False` por padrão | Mudança para True em produção bloqueia fluxos existentes que não coletaram consentimento explícito |
| `PLAN_LIMITS_ENFORCE: True` | Sem enforcement, todos os tenants têm acesso ilimitado (billing gap) |
| Priority chain de FeatureFlagService (company → global → default) | Multi-tenancy — inverter priority vaza configurações de uma empresa para outra |
| Fail-safe em `is_enabled()` (retorna default em caso de exceção) | Reliability — exceção propagada para a feature derruba o request inteiro |

---

## Checklist de completude

### P0 — Críticos (bloqueiam deploy)

- [ ] (P0) `validate_secret_key()` validator presente — `APP_ENV=production` com `SECRET_KEY` padrão causa `ValueError` no startup
- [ ] (P0) `model_config.case_sensitive=True` + `extra="ignore"` — não alterar
- [ ] (P0) `.env` não commitado no git (`.gitignore` contém `.env`)
- [ ] (P0) Nenhuma API key hardcoded em código (apenas em `.env` ou Doppler)
- [ ] (P0) `from lia_config.config import settings` (não `from libs.config...`) — check_forbidden_imports.py valida
- [ ] (P0) `ENABLE_AUTO_SCREENING/SCHEDULING/STAGE_ADVANCE` com default `False` em `DEFAULT_FLAGS`
- [ ] (P0) `FeatureFlagService.is_enabled()` com fail-safe (retorna default em exceção)

### P1 — Importantes

- [ ] (P1) Tabela `feature_flags` migrada com campos: flag_key, company_id, is_enabled, rollout_percentage, expires_at
- [ ] (P1) `RAILS_JWT_SECRET_KEY` configurado (usado para validação cross-system com Rails)
- [ ] (P1) `AUDIT_STORAGE_TYPE=s3` com `AUDIT_STORAGE_BUCKET` em produção
- [ ] (P1) `SECRETS_PROVIDER=doppler` em produção com `DOPPLER_TOKEN` injetado via infra
- [ ] (P1) Priority chain `is_enabled()`: company → global → default testada
- [ ] (P1) `PLAN_LIMITS_ENFORCE=True` em produção (billing enforcement)
- [ ] (P1) `_cache_ttl=300` (5 min) em FeatureFlagService — não aumentar acima de 600s (stale flags)

### P2 — Qualidade

- [ ] (P2) `.env.example` atualizado com todos os campos novos + comentários
- [ ] (P2) `OTEL_EXPORTER_OTLP_ENDPOINT` configurado em produção para observabilidade
- [ ] (P2) `LANGCHAIN_TRACING_V2=true` em staging para debugging de chains
- [ ] (P2) `ROUTER_VECTOR_CACHE_ENABLED` como A/B flag — documentado para rollback
- [ ] (P2) Module gating `TASTING_TOOLS` + `PREMIUM_GATED_TOOLS` atualizados conforme modules disponíveis
- [ ] (P2) `CHUNKING_*` defaults testados por tipo de documento antes de alterar

---

## Gotchas e erros comuns

### 1. Instanciar Settings() diretamente (em vez do singleton)

```python
# ❌ ERRADO — cria nova instância que não compartilha estado
from lia_config.config import Settings
my_settings = Settings()

# ✅ CORRETO — singleton de módulo
from lia_config.config import settings
settings.ANTHROPIC_API_KEY
```

Múltiplas instâncias causam `.env` relido múltiplas vezes e podem divergir se env vars mudaram após startup.

### 2. `os.environ` diretamente para secrets

```python
# ❌ ERRADO — bypass da abstração de secrets
import os
api_key = os.environ.get("ANTHROPIC_API_KEY")

# ✅ CORRETO — via abstração (suporta Doppler em prod)
from app.core.secrets_provider import secrets
api_key = secrets().get("ANTHROPIC_API_KEY")
# ou via settings (pydantic-settings já lê .env):
from lia_config.config import settings
api_key = settings.ANTHROPIC_API_KEY
```

### 3. Flag de automação habilitada por padrão

```python
# ❌ ERRADO — ação automática sem opt-in do tenant
DEFAULT_FLAGS = {
    "ENABLE_AUTO_SCREENING": {"default": True}  # PERIGOSO
}

# ✅ CORRETO — automação sempre opt-in
DEFAULT_FLAGS = {
    "ENABLE_AUTO_SCREENING": {"default": False}  # Safe default
}
```

### 4. Feature flag sem fail-safe

```python
# ❌ ERRADO — exceção propaga para o request
enabled = (await db.execute(select(FeatureFlag).where(...))).scalar_one()

# ✅ CORRETO — fail-safe
try:
    enabled = await self._query_flag(db, flag_key, company_id)
except Exception as e:
    self.logger.error(f"Error checking flag {flag_key}: {e}")
    return self.DEFAULT_FLAGS.get(flag_key, {}).get("default", False)
```

### 5. .env commitado acidentalmente

```bash
# Verificar antes do commit:
git status | grep "\.env"
# Garantir que .gitignore contém:
.env
.env.local
.env.production
# NUNCA commitar arquivos com chaves reais
```

### 6. Rollout probabilístico — sem stickiness

`rollout_percentage < 100` usa `random.randint(1, 100)` por request — não é determinístico por usuário. O mesmo usuário pode ter a flag ligada em um request e desligada no próximo. Para stickiness, usar `ABTestingService` do R2 (MD5 bucket assignment por `company_id`).

### 7. case_sensitive=True — variáveis com casing errado silenciosamente ignoradas

```bash
# ❌ ERRADO — vai ser ignorado (settings.ANTHROPIC_API_KEY continua None)
anthropic_api_key=sk-ant-...

# ✅ CORRETO — case exato conforme Settings
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Validator de produção | `tests/unit/test_config.py` | `APP_ENV=production` + `SECRET_KEY` padrão → `ValueError` no startup |
| Feature flag priority chain | `tests/unit/test_feature_flag_service.py` | company flag → global flag → default (3 cenários) |
| Feature flag fail-safe | `tests/unit/test_feature_flag_service.py` | DB falha → retorna default, não levanta exceção |
| Rollout percentage | `tests/unit/test_feature_flag_service.py` | rollout=50 → ~50% True em 1000 samples |
| Automation flags default False | `tests/unit/test_feature_flag_service.py` | ENABLE_AUTO_* default False sem DB |
| SecretsProvider factory | `tests/unit/test_secrets_provider.py` | SECRETS_PROVIDER="env" → EnvProvider; "doppler" → DopplerProvider |
| DopplerProvider fallback | `tests/unit/test_secrets_provider.py` | CLI falha → fallback para env |
| No API keys hardcoded | `python scripts/check_forbidden_imports.py` | 0 API keys em código |
| Module gating degraded response | `tests/unit/test_module_gating.py` | Tool premium sem módulo ativo → retorna CTA |
| Feature flag expirado | `tests/unit/test_feature_flag_service.py` | `expires_at` no passado → False mesmo is_enabled=True |

---

## Referências

| Recurso | Localização |
|---------|------------|
| FAIRNESS_LAYER3_RUNBOOK.md (flags de fairness) | `/Users/paulomoraes/Documents/Python/FAIRNESS_LAYER3_RUNBOOK.md` |
| COMPLIANCE guide §11.2 (feature flags) | `themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md` |
| R3 Messaging (BROKER_BACKEND) | `themes/resilience/R3_MESSAGING_AND_EVENTS.md` |
| I4 LLM Providers (LLMSettings consumers) | `themes/infrastructure/I4_LLM_PROVIDERS.md` |
| R2 Learning (ABTestingService — stickiness) | `themes/resilience/R2_LEARNING_LOOP_AND_AB_TESTING.md` |
| DEVELOPER_HANDOFF.md | Handoff LIA Partes A-F (1204 linhas) |
