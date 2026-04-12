# Auditoria de Chaves de API, URLs e Secrets da Plataforma LIA

> **Data da auditoria:** Abril de 2026  
> **Escopo:** `lia-agent-system` (backend Python/FastAPI) + `plataforma-lia` (frontend Next.js)  
> **Metodologia:** Análise estática dos arquivos relevantes listados na task #175.  
> **Limitações:** Este documento é baseado exclusivamente em leitura estática do repositório. Afirmações sobre comportamento em runtime (ex.: se um CLI está instalado, se um endpoint é acessível sem autenticação completa) estão marcadas como hipóteses e devem ser validadas em ambiente real antes de serem tratadas como fatos. Números de linha referenciados podem apresentar drift com futuras alterações de código — recomenda-se revalidação após mudanças significativas nos arquivos citados.

---

## Seção 1 — Inventário Completo de Secrets e Conexões

### 1.1 Banco de Dados

| Variável | Tipo | Valor Padrão / Default |
|---|---|---|
| `DATABASE_URL` | String (DSN PostgreSQL) | `postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db` |
| `DATABASE_POOL_SIZE` | Int | `20` |
| `DATABASE_MAX_OVERFLOW` | Int | `10` |
| `ELASTICSEARCH_URL` | String (URL) | `None` (opcional) |
| `SEARCH_BACKEND` | String | `"postgres"` |

**Arquivo principal:** `lia-agent-system/libs/config/lia_config/config.py` (linhas 26–33), com leitura dupla em `lia-agent-system/libs/config/lia_config/database.py` (linha 33).

---

### 1.2 Cache / Broker

| Variável | Tipo | Valor Padrão |
|---|---|---|
| `REDIS_URL` | String (URL) | `redis://localhost:6379/0` |
| `RABBITMQ_URL` | String (URL AMQP) | `amqp://guest:guest@localhost:5672/` |
| `RABBITMQ_EXCHANGE` | String | `"rh_platform"` |
| `CELERY_BROKER_URL` | String (URL) | `None` — deriva de `BROKER_BACKEND` |
| `CELERY_RESULT_BACKEND` | String (URL) | `None` — cai para `REDIS_URL` |
| `BROKER_BACKEND` | String | `"redis"` |
| `ROUTER_CACHE_TTL` | Int | `3600` |
| `SEMANTIC_CACHE_TTL` | Int | `86400` |

**Arquivo principal:** `lia-agent-system/libs/config/lia_config/config.py` (linhas 39–64); resolução do broker em `lia-agent-system/libs/config/lia_config/celery_app.py` (linhas 44–86).

---

### 1.3 LLM / Inteligência Artificial

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | String | Sim (se Claude for primário) | `None` |
| `OPENAI_API_KEY` | String | Sim (se OpenAI for primário) | `None` |
| `GOOGLE_APPLICATION_CREDENTIALS` | String (path JSON) | Sim (Vertex AI) | `None` |
| `GOOGLE_CLOUD_PROJECT` | String | Sim (Vertex AI) | `None` |
| `GOOGLE_CLOUD_REGION` | String | Não | `"us-east1"` |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | String | Sim (Gemini primário) | `None` |
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | String | Não | `None` |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | String | Sim (Claude via Replit integration) | `None` |
| `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` | String | Não | `None` |
| `AI_INTEGRATIONS_OPENAI_API_KEY` | String | Não | `None` |
| `AI_INTEGRATIONS_OPENAI_BASE_URL` | String | Não | `None` |
| `LANGCHAIN_API_KEY` | String | Não | `None` |
| `LANGSMITH_API_KEY` | String | Não | `None` (lido em `langsmith.py` linha 28) |
| `LANGCHAIN_TRACING_V2` | Bool | Não | `False` |
| `LANGCHAIN_PROJECT` | String | Não | `"lia-agent-system"` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | String | Não | `""` (desabilitado) |
| `OTEL_SERVICE_NAME` | String | Não | `"lia-agent-system"` |

**Arquivo principal:** `lia-agent-system/libs/config/lia_config/config.py` (linhas 71–124); providers: `app/shared/providers/llm_gemini.py` (linha 40), `app/shared/providers/llm_claude.py` (linha 46), `app/shared/providers/llm_openai.py` (linha 32); bootstrap: `app/shared/llm_bootstrap.py` (linhas 116–120); observabilidade: `app/config/langsmith.py` (linha 28).

---

### 1.4 Autenticação / JWT / WorkOS / Azure

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `SECRET_KEY` | String | **Sim** (validator bloqueia) | `"change-this-in-production"` |
| `ALGORITHM` | String | Não | `"HS256"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Int | Não | `30` |
| `RAILS_JWT_SECRET_KEY` | String | Sim (Rails SSO) | `None` |
| `WORKOS_CLIENT_ID` | String | Sim (SSO WorkOS) | `None` |
| `WORKOS_API_KEY` | String | Sim (SSO WorkOS) | `None` |
| `WORKOS_WEBHOOK_SECRET` | String | Sim (webhooks WorkOS) | `None` |
| `AZURE_TENANT_ID` | String | Sim (Graph / Teams) | `None` |
| `AZURE_CLIENT_ID` | String | Sim (Graph / Teams) | `None` |
| `AZURE_CLIENT_SECRET` | String | Sim (Graph / Teams) | `None` |
| `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` | String | Não | `None` |
| `MICROSOFT_CALENDAR_DEFAULT_TIMEZONE` | String | Não | `"America/Sao_Paulo"` |
| `MICROSOFT_APP_ID` | String | Sim (Bot Framework) | `None` |
| `MICROSOFT_APP_PASSWORD` | String | Sim (Bot Framework) | `None` |
| `TEAMS_WEBHOOK_URL` | String | Não | `None` |
| `TEAMS_WEBHOOK_SECRET` | String | Não | `None` |
| `TEAMS_APP_TENANT_ID` | String | Não | `None` |
| `DOPPLER_TOKEN` | String | Sim (se `SECRETS_PROVIDER=doppler`) | `None` |
| `SECRETS_PROVIDER` | String | Não | `"env"` |
| `ADMIN_API_KEY` | String | Sim (endpoints internos) | `None` |

**Arquivo principal:** `lia-agent-system/libs/config/lia_config/config.py` (linhas 145–181); leitura do WorkOS no frontend: `plataforma-lia/src/lib/workos.ts` (linha 8); acesso direto ao `os.environ` em Teams: `app/api/v1/teams.py` (linhas 968–1305).

---

### 1.5 Comunicação (Twilio, Email)

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `TWILIO_ACCOUNT_SID` | String | Sim (voz/WhatsApp via Twilio) | `None` |
| `TWILIO_AUTH_TOKEN` | String | Sim (voz/WhatsApp via Twilio) | `None` |
| `TWILIO_WHATSAPP_NUMBER` | String | Sim (WhatsApp Twilio) | `None` |
| `TWILIO_VOICE_NUMBER` | String | Sim (voz Twilio) | `None` |
| `TWILIO_WEBHOOK_BASE_URL` | String | Sim (callbacks TwiML) | `None` |
| `MAILGUN_API_KEY` | String | Sim (envio de email) | `None` |
| `MAILGUN_DOMAIN` | String | Sim (envio de email) | `None` |
| `MAILGUN_API_BASE` | String | Não | `"https://api.mailgun.net/v3"` |
| `RESEND_API_KEY` | String | Não (fallback) | `None` |
| `EMAIL_FROM_ADDRESS` | String | Não | `"noreply@wedotalent.com"` |
| `EMAIL_FROM_NAME` | String | Não | `"WeDOTalent"` |
| `WHATSAPP_PROVIDER` | String | Não | `"meta"` |
| `WHATSAPP_PHONE_NUMBER_ID` | String | Sim (Meta WhatsApp) | `None` |
| `WHATSAPP_API_TOKEN` | String | Sim (Meta WhatsApp) | `None` |

**Arquivos:** `app/services/email_providers/mailgun_provider.py` (linhas 48–61); `app/domains/communication/services/twilio_voice_service.py`; `libs/messaging/lia_messaging/whatsapp.py` (linhas 84–85); `libs/messaging/lia_messaging/teams.py` (linha 39).

---

### 1.6 Integrações Externas

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `PEARCH_API_KEY` | String | Sim (sourcing Pearch) | `None` |
| `PEARCH_API_URL` | String | Não | `"https://api.pearch.ai"` |
| `APIFY_API_KEY` | String | Sim (web scraping) | `None` |
| `MERGE_API_KEY` | String | Não | `None` |
| `GUPY_API_KEY` | String | Não | `None` |
| `PANDAPE_API_KEY` | String | Não | `None` |
| `HUBSPOT_API_KEY` | String | Não | `None` |
| `HUBSPOT_PORTAL_ID` | String | Não | `None` |
| `STRIPE_SECRET_KEY` | String | Sim (billing) | `None` |
| `STRIPE_WEBHOOK_SECRET` | String | Sim (billing) | `None` |
| `STRIPE_PUBLISHABLE_KEY` | String | Sim (billing frontend) | `None` |

**Arquivos:** `app/domains/sourcing/services/apify_service.py` (linha 17 — lê diretamente `os.environ.get`); `app/domains/sourcing/services/pearch_service.py`; `libs/config/lia_config/config.py` (linhas 274–318).

---

### 1.7 Calendários

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `GOOGLE_CALENDAR_CLIENT_ID` | String | Não | `None` |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | String | Não | `None` |
| `GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON` | String (JSON) | Não | `None` |
| `GOOGLE_CALENDAR_DEFAULT_TIMEZONE` | String | Não | `"America/Sao_Paulo"` |
| `GOOGLE_CALENDAR_OAUTH_REDIRECT_URI` | String | Não | `None` |

**Arquivo principal:** `libs/config/lia_config/config.py` (linhas 287–291).

---

### 1.8 Storage / S3

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `AUDIT_STORAGE_TYPE` | String | Não | `"file"` |
| `AUDIT_STORAGE_BUCKET` | String | Sim (quando `type=s3`) | `""` |
| `AUDIT_STORAGE_PREFIX` | String | Não | `"audit"` |
| `AUDIT_LOCAL_DIR` | String | Não | `"./audit_logs"` |
| `S3_ACCESS_KEY` | String | Sim (quando `type=s3`) | `None` |
| `S3_SECRET_KEY` | String | Sim (quando `type=s3`) | `None` |
| `S3_REGION` | String | Não | `"us-east-1"` |

**Arquivo principal:** `libs/config/lia_config/config.py` (linhas 131–138).

---

### 1.9 Observabilidade

| Variável | Tipo | Obrigatória em Prod | Valor Padrão |
|---|---|---|---|
| `SENTRY_DSN` | String | Não | `None` |
| `SENTRY_TRACES_SAMPLE_RATE` | Float | Não | `0.1` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | String | Não | `""` (desabilitado) |

**Arquivo principal:** `libs/config/lia_config/config.py` (linhas 200–201, 123).

---

### 1.10 Criptografia de Campos PII

| Variável | Tipo | Obrigatória em Prod |
|---|---|---|
| `FIELD_ENCRYPTION_KEY` | String (Fernet base64) | **Sim** (falha fechada em prod) |
| `ENCRYPTION_KEY` | String (Fernet base64) | Sim (legado — `__init__.py` shim) |
| `IS_DEVELOPMENT` | String (`"true"`) | Não — suprime erros de key ausente em dev |
| `ENVIRONMENT` | String | Não — gate de prod em `__init__.py` |

**Arquivos:** `app/shared/encryption/encrypted_field_mixin.py` (linhas 59, 75); `app/shared/encryption/__init__.py` (linhas 17–26).

---

### 1.11 Frontend (Next.js / `plataforma-lia`)

| Variável | Contexto de Uso |
|---|---|
| `WORKOS_API_KEY` | Server-side — `src/lib/workos.ts` linha 8 |
| `WORKOS_CLIENT_ID` | Server-side — `src/lib/workos.ts` linha 25 |
| `WORKOS_REDIRECT_URI` | Server-side — `src/lib/workos.ts` linha 26 |
| `BACKEND_URL` | Server-side — `src/lib/api/proxy-handler.ts` linha 4 (default `http://127.0.0.1:8001`) |
| `RAILS_BACKEND_URL` | Server-side — `src/lib/api/proxy-handler.ts` linha 5 |
| `REPLIT_DEV_DOMAIN` | Server-side — redirect URI dinâmico em `workos.ts` linha 28 |
| `APP_DOMAIN` | Server-side — fallback de domínio em `workos.ts` linha 30 |
| `DEV_AUTO_LOGIN_EMAIL` | Server-side — `src/app/api/auth/auto-login/route.ts` linha 12 |
| `DEV_AUTO_LOGIN_PASSWORD` | Server-side — `src/app/api/auth/auto-login/route.ts` linha 13 (default `"demo123"`) |
| `NODE_ENV` | Padrão Next.js — gate de produção para rotas de dev |
| `NEXT_PUBLIC_*` | Variáveis públicas expostas ao browser — cada componente as importa individualmente |

---

## Seção 2 — Arquitetura de Gestão de Secrets

### 2.1 Pydantic Settings — Classe `Settings` com herança múltipla

O principal mecanismo de configuração é a classe `Settings` em `libs/config/lia_config/config.py` (linha 325), que herda de oito subclasses temáticas:

```
Settings
 ├── DatabaseSettings   (linha 26)
 ├── CacheSettings      (linha 39)
 ├── MessagingSettings  (linha 54)
 ├── LLMSettings        (linha 71)
 ├── AuditSettings      (linha 131)
 ├── AuthSettings       (linha 145)
 ├── AppSettings        (linha 188)
 └── IntegrationSettings (linha 274)
```

A instância `settings` (singleton global, linha 361) é criada em tempo de importação, carregando variáveis de ambiente e o arquivo `.env`. É acessível em toda a aplicação via `from lia_config.config import settings` ou `from app.core.config import settings`.

**Configuração:** `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")` — linha 353.

**Único validator de produção:** `validate_secret_key` (linha 342–351) bloqueia se `SECRET_KEY == "change-this-in-production"` e `APP_ENV == "production"`.

---

### 2.2 SecretsProvider — Abstração com backends plugáveis

`app/core/secrets_provider.py` define uma abstração com dois backends:

- **`EnvProvider`** (padrão, linha 36): lê `os.environ` diretamente. Usado em desenvolvimento.
- **`DopplerProvider`** (linha 43): executa `doppler secrets download --no-file --format=env` via subprocess, cacheia em memória e faz fallback para `os.environ` se o CLI não estiver disponível ou o token estiver ausente.

O provider ativo é determinado pela variável `SECRETS_PROVIDER` (default: `"env"`, linha 177 do config). O singleton `secrets()` (linha 107) é inicializado lazily na primeira chamada.

**Observação operacional (hipótese):** O `DopplerProvider` existe como código funcional, mas `SECRETS_PROVIDER` tem valor padrão `"env"`. Com base na análise do repositório, não há documentação de setup para ativação do Doppler, e o código de `DopplerProvider._load_secrets()` (linha 81) trata `FileNotFoundError` do CLI com `logger.warning` e fallback silencioso para `os.environ` — o que sugere que o CLI pode não estar presente no ambiente de execução atual. Isso não é confirmável apenas por leitura estática, mas é um risco operacional caso o Doppler seja ativado sem o CLI instalado.

---

### 2.3 Tenant LLM Context — Chaves LLM por tenant no banco

`app/shared/tenant_llm_context.py` gerencia configuração LLM per-tenant:

1. `AuthEnforcementMiddleware` injeta `company_id` no contextvar `_current_company_id` (linha 20 de `auth_enforcement.py`).
2. `get_tenant_llm_config(company_id)` (linha 35) consulta `TenantLLMConfig` via `LlmConfigRepository`.
3. API keys por tenant ficam em `tenant_llm_configs.providers` (coluna JSON) **encriptadas via Fernet** usando `encrypt_value`/`decrypt_value` do `app/shared/encryption/__init__.py`.
4. A decriptação ocorre em `LlmConfigRepository._decrypt_provider_keys()` (linha 29 de `llm_config_repository.py`).
5. As chaves decriptadas são passadas ao `ProviderContainer` via `provider_api_keys` (linha 482 de `llm_factory.py`).

**Modelo:** `lia_models/tenant_llm_config.py` (tabela `tenant_llm_configs`) — chave primária UUID, campo `providers` JSON com estrutura `{"gemini": {"api_key": "enc:...", "model": "..."}}`.

---

### 2.4 Encrypted Fields — Mixin Fernet para PII

`app/shared/encryption/encrypted_field_mixin.py` provê `EncryptedFieldMixin` e `EncryptedField`:

- **Key:** Lida de `FIELD_ENCRYPTION_KEY` (linha 75). Fail-closed em produção (`EncryptionKeyMissingError`), mas permissivo quando `IS_DEVELOPMENT=true` (linha 59).
- **Criptografia:** Fernet (AES-128-CBC via biblioteca `cryptography`).
- **Dualidade de keys:** Existe também `ENCRYPTION_KEY` lida pelo shim legado `app/shared/encryption/__init__.py` (linha 17), que gera uma chave ephemeral aleatória em desenvolvimento se a variável não estiver presente (linha 24) — comportamento silencioso e diferente do mixin principal.

---

### 2.5 Leitura Dupla em `database.py`

`lia-agent-system/libs/config/lia_config/database.py` linha 33:

```python
database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
```

Esta leitura dupla foi introduzida para compatibilidade com Replit Secrets (que injeta `DATABASE_URL` diretamente em `os.environ`, sem passar pelo arquivo `.env`). O padrão `settings.DATABASE_URL` contém credenciais hardcoded (`lia_password`).

---

### 2.6 LLM Bootstrap — Injeção via monkey-patch de SDK

`app/shared/llm_bootstrap.py` instala patches nos construtores do Anthropic, Gemini e OpenAI SDKs (`install_llm_guards()`, chamado em `app/main.py`). O patch injeta a API key lendo diretamente de `os.environ`:

- Anthropic: `AI_INTEGRATIONS_ANTHROPIC_API_KEY` ou `ANTHROPIC_API_KEY` (linha 117).
- Gemini: `AI_INTEGRATIONS_GEMINI_API_KEY` + `AI_INTEGRATIONS_GEMINI_BASE_URL` (linha 40 de `llm_gemini.py`).
- OpenAI: `OPENAI_API_KEY` (linha 32 de `llm_openai.py`).

Este mecanismo opera **fora** do `settings` e **fora** do `secrets()`, lendo `os.environ` diretamente.

---

### 2.7 Frontend — Leitura Descentralizada de `process.env`

No frontend Next.js (`plataforma-lia`):

- `src/lib/workos.ts` (linha 8): `process.env.WORKOS_API_KEY` — leitura direta, lazy init com throw explícito.
- `src/lib/api/proxy-handler.ts` (linha 4): `process.env.BACKEND_URL || "http://127.0.0.1:8001"`.
- `src/app/api/auth/auto-login/route.ts` (linhas 12–13): `process.env.DEV_AUTO_LOGIN_EMAIL` e `process.env.DEV_AUTO_LOGIN_PASSWORD`.

Não há módulo central de configuração no frontend — cada route/lib importa individualmente do `process.env`.

---

## Seção 3 — Gaps e Riscos Identificados

### 3.1 Fallbacks Hardcoded Inseguros

| Localização | Código | Risco |
|---|---|---|
| `config.py` linha 27 | `DATABASE_URL: str = "postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db"` | Senha `lia_password` em texto claro como default |
| `config.py` linha 40 | `REDIS_URL: str = "redis://localhost:6379/0"` | Sem autenticação — seguro apenas em dev |
| `config.py` linha 55 | `RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"` | Credenciais default do RabbitMQ (`guest:guest`) |
| `config.py` linha 146 | `SECRET_KEY: str = "change-this-in-production"` | Validado em prod, mas o próprio valor padrão já é um risco de leak |
| `teams.py` linhas 1308–1315 | `access_token="dev-fallback-token"` | Token de acesso fictício retornado quando Azure não está configurado — não gateado por `APP_ENV` |
| `auto-login/route.ts` linha 13 | `process.env.DEV_AUTO_LOGIN_PASSWORD \|\| 'demo123'` | Senha hardcoded `demo123` — rota só ativa em não-produção (`NODE_ENV`), mas o default vaza no código |

---

### 3.2 Validação Parcial em Produção

Apenas `SECRET_KEY` tem um `@model_validator` que bloqueia em produção (`config.py` linhas 342–351). Todos os outros campos com defaults inseguros (`DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`) não possuem validators correspondentes — passam silenciosamente com valores de desenvolvimento em qualquer `APP_ENV`.

Campos que deveriam ter validators em produção mas não têm:
- `DATABASE_URL` (contém senha hardcoded)
- `RABBITMQ_URL` (credenciais `guest:guest`)
- `FIELD_ENCRYPTION_KEY` / `ENCRYPTION_KEY` (dados PII não encriptados em silêncio)
- `ADMIN_API_KEY` (endpoints internos sem proteção se ausente)
- `WORKOS_API_KEY` / `WORKOS_CLIENT_ID` (auth quebrado silencioso)

---

### 3.3 Três Mecanismos de Leitura de Secrets Coexistindo

A aplicação utiliza **três caminhos distintos** para leitura de credenciais sem contrato unificado:

1. **`settings.<FIELD>`** — via Pydantic Settings, carregado em startup. Usado pela maioria dos módulos internos.
2. **`secrets().<get(key)>`** — via `SecretsProvider` (abstração Doppler/Env). Raramente utilizado na prática.
3. **`os.environ.get(key)` / `os.getenv(key)`** direto — utilizado amplamente em módulos como:
   - `apify_service.py` linha 17: `APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")`
   - `mailgun_provider.py` linha 48: `os.getenv("MAILGUN_API_KEY")`
   - `teams.py` linhas 968, 1303–1305: `os.environ.get("AZURE_CLIENT_ID", "")`
   - `llm_gemini.py` linha 40, `llm_claude.py` linha 46: `os.environ.get("AI_INTEGRATIONS_*")`
   - `llm_bootstrap.py` linhas 117–118: `os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")`
   - `cache_config.py` linha 18: `os.environ.get("REDIS_URL")` (duplicando `settings.REDIS_URL`)
   - `langsmith.py` linha 28: `os.getenv("LANGSMITH_API_KEY")`

---

### 3.4 Dualidade de Keys de Criptografia

Existem **duas variáveis de chave de criptografia distintas** para campos PII:

- `FIELD_ENCRYPTION_KEY` — usada pelo mixin moderno `encrypted_field_mixin.py` (linha 75).
- `ENCRYPTION_KEY` — usada pelo shim legado `encryption/__init__.py` (linha 17), que é importado por `llm_config_repository.py` para encriptar API keys de tenant.

O shim `__init__.py` gera uma **chave ephemeral aleatória** em desenvolvimento se `ENCRYPTION_KEY` estiver ausente (linha 24), o que significa que os dados encriptados com essa chave são irrecuperáveis após restart. O arquivo de log emite um `WARNING` mas não bloqueia a aplicação.

---

### 3.5 Triple-Path para Chaves LLM

As chaves de API de LLM podem ser resolvidas por **três caminhos**, sem ordem de prioridade documentada:

1. **Global via `settings`:** `settings.ANTHROPIC_API_KEY`, `settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY` etc.
2. **Per-tenant via banco (encriptado):** `TenantLLMConfig.providers[provider]["api_key"]` → decriptado por `LlmConfigRepository` → passado ao `ProviderContainer`.
3. **Direto via `os.environ`:** Utilizado pelo `llm_bootstrap.py` e pelos providers individuais (`llm_gemini.py`, `llm_claude.py`) antes de receber uma `api_key` explícita.

Na prática, a prioridade efetiva é: chave do tenant (se configurada no DB) > `os.environ` / `settings` (equivalentes, já que Pydantic lê do ambiente). O monkey-patch do bootstrap aplica a key do ambiente para chamadas que não passam pelo `ProviderContainer`.

---

### 3.6 Doppler Não Ativo

`SECRETS_PROVIDER` tem default `"env"` (config.py linha 177). O código do `DopplerProvider` existe e é funcional, mas:
- O CLI `doppler` não está instalado no ambiente Replit.
- Não há documentação de setup para ativação.
- `DOPPLER_TOKEN` não está documentado como obrigatório quando `SECRETS_PROVIDER=doppler`.
- O fallback do `DopplerProvider` para `os.environ` (linha 89) mascara falhas de configuração silenciosamente.

---

### 3.7 Dev-fallback-token em Endpoint de Produção

`app/api/v1/teams.py` linhas 1308–1315 retorna um token fictício `"dev-fallback-token"` quando as variáveis Azure não estão configuradas. Este comportamento **não é gateado por `APP_ENV`**.

O risco real depende do fluxo de validação JWT subsequente: se o token `"dev-fallback-token"` for validado pelo `AuthEnforcementMiddleware` antes de atingir endpoints protegidos, o impacto seria contido. Entretanto, dado que `dev-fallback-token` não é um JWT válido, o middleware o rejeitaria em endpoints protegidos. O risco concreto é que a rota `/api/v1/teams/tab-auth` retorna HTTP 200 com um token inutilizável em vez de um erro explícito de configuração (HTTP 503 ou equivalente), dificultando o diagnóstico em produção e potencialmente mascarando uma configuração Azure incompleta.

---

### 3.8 Frontend sem Centralização de Variáveis de Ambiente

O frontend Next.js não possui um módulo central de configuração. Cada arquivo acessa `process.env` individualmente:
- `proxy-handler.ts` lê `BACKEND_URL` e `RAILS_BACKEND_URL`.
- `workos.ts` lê `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_REDIRECT_URI`.
- `auto-login/route.ts` lê `DEV_AUTO_LOGIN_EMAIL`, `DEV_AUTO_LOGIN_PASSWORD`, `BACKEND_URL`.

Isso torna auditoria e rotação de chaves mais trabalhosas, além de aumentar o risco de variáveis esquecidas em algum ponto.

---

## Seção 4 — Recomendações

### R-01: Consolidar leituras de secrets em `settings` ou `secrets()`
Eliminar os usos diretos de `os.getenv` / `os.environ.get` em módulos de negócio. Módulos como `apify_service.py`, `mailgun_provider.py`, `teams.py`, `cache_config.py`, `langsmith.py` e todos os providers LLM devem receber as credenciais via injeção de dependência a partir de `settings` ou do `secrets()` provider.

### R-02: Adicionar validators Pydantic para todos os campos sensíveis em produção
Expandir o `@model_validator` existente (`validate_secret_key`) para cobrir:
- `DATABASE_URL` (rejeitar se contiver `lia_password`)
- `RABBITMQ_URL` (rejeitar se contiver `guest:guest`)
- `FIELD_ENCRYPTION_KEY` / `ENCRYPTION_KEY` (obrigatórios quando `APP_ENV=production`)
- `ADMIN_API_KEY` (obrigatório em produção)
- Chaves LLM (pelo menos uma deve estar presente)

### R-03: Remover ou gate por `APP_ENV` todos os fallbacks hardcoded inseguros
- `teams.py` linha 1311: o retorno de `dev-fallback-token` deve ser gateado por `settings.APP_ENV != "production"` (ou simplesmente retornar 401).
- `auto-login/route.ts` linha 13: o default `'demo123'` é aceitável apenas porque a rota já está gateada por `NODE_ENV !== 'production'`, mas documentar isso explicitamente.
- Defaults do `DATABASE_URL` e `RABBITMQ_URL` devem ser `None` (campos obrigatórios em prod).

### R-04: Documentar e ativar Doppler para produção
Criar documentação em `docs/infra/` descrevendo:
- Como instalar o CLI Doppler.
- Como configurar `DOPPLER_TOKEN` e `SECRETS_PROVIDER=doppler`.
- A ordem de prioridade: Doppler > variável de ambiente > default do `settings`.

### R-05: Unificar variáveis de chave de criptografia
Consolidar `FIELD_ENCRYPTION_KEY` e `ENCRYPTION_KEY` em uma única variável. O shim `encryption/__init__.py` deve usar `FIELD_ENCRYPTION_KEY` como fonte primária, eliminando a geração de chave ephemeral silenciosa em desenvolvimento.

### R-06: Centralizar variáveis do frontend em um módulo único
Criar `plataforma-lia/src/lib/config/server-config.ts` exportando todas as variáveis de ambiente server-side com validação de presença em produção (via `z.string()` com Zod, por exemplo). Isso facilita auditoria e evita `process.env` disperso.

### R-07: Documentar prioridade de resolução de chaves LLM
Adicionar documentação explícita (no `llm_factory.py` ou em `docs/`) sobre a ordem de resolução:
`Tenant DB (decriptado) > os.environ/settings global > erro`

---

## Seção 5 — Tabela Resumo

| Variável | Categoria | Obrigatória em Prod | Tem Default Inseguro | Mecanismo de Leitura | Arquivo Principal |
|---|---|---|---|---|---|
| `DATABASE_URL` | Banco de Dados | Sim | **Sim** (`lia_password`) | `os.environ.get` → `settings.DATABASE_URL` | `database.py:33` |
| `ELASTICSEARCH_URL` | Banco de Dados | Não | Não (`None`) | `settings` | `config.py:30` |
| `REDIS_URL` | Cache | Sim | Sim (localhost s/ auth) | `settings` + `os.environ.get` | `config.py:40`, `cache_config.py:18` |
| `RABBITMQ_URL` | Broker | Não | **Sim** (`guest:guest`) | `settings` | `config.py:55` |
| `CELERY_BROKER_URL` | Broker | Não | Não | `os.getenv` → `settings` | `celery_app.py:58` |
| `CELERY_RESULT_BACKEND` | Broker | Não | Não | `os.getenv` → `settings` | `celery_app.py:58` |
| `ANTHROPIC_API_KEY` | LLM/IA | Condicional | Não (`None`) | `settings` + `os.environ.get` | `config.py:73`, `llm_claude.py:46` |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | LLM/IA | Condicional | Não (`None`) | `os.environ.get` | `llm_claude.py:46`, `llm_bootstrap.py:117` |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | LLM/IA | Sim | Não (`None`) | `os.environ.get` | `llm_gemini.py:40` |
| `OPENAI_API_KEY` | LLM/IA | Condicional | Não (`None`) | `os.environ.get` | `llm_openai.py:32` |
| `LANGCHAIN_API_KEY` | Observabilidade | Não | Não (`None`) | `settings` + `os.getenv` | `config.py:118`, `langsmith.py:28` |
| `SECRET_KEY` | Auth | **Sim** | **Sim** (`change-this`) | `settings` (com validator) | `config.py:146` |
| `RAILS_JWT_SECRET_KEY` | Auth | Condicional | Não (`None`) | `settings` | `config.py:152` |
| `WORKOS_CLIENT_ID` | Auth | Sim | Não (`None`) | `settings` + `process.env` | `config.py:153`, `workos.ts:25` |
| `WORKOS_API_KEY` | Auth | Sim | Não (`None`) | `process.env` (throw explícito) | `workos.ts:8` |
| `WORKOS_WEBHOOK_SECRET` | Auth | Sim | Não (`None`) | `settings` | `config.py:155` |
| `AZURE_TENANT_ID` | Auth | Condicional | Não (`None`) | `settings` + `os.environ.get` | `config.py:159`, `teams.py:969` |
| `AZURE_CLIENT_ID` | Auth | Condicional | Não (`None`) | `settings` + `os.environ.get` | `config.py:160`, `teams.py:968` |
| `AZURE_CLIENT_SECRET` | Auth | Condicional | Não (`None`) | `settings` + `os.environ.get` | `config.py:161`, `teams.py:1304` |
| `MICROSOFT_APP_ID` | Auth | Condicional | Não (`None`) | `settings` | `config.py:168` |
| `MICROSOFT_APP_PASSWORD` | Auth | Condicional | Não (`None`) | `settings` | `config.py:169` |
| `ADMIN_API_KEY` | Auth | Sim | Não (`None`) | `settings` | `config.py:181` |
| `DOPPLER_TOKEN` | Secrets | Condicional | Não (`None`) | `settings` + `os.environ.get` | `config.py:178`, `secrets_provider.py:52` |
| `SECRETS_PROVIDER` | Secrets | Não | Não (`"env"`) | `settings` | `config.py:177` |
| `TWILIO_ACCOUNT_SID` | Comunicação | Condicional | Não (`None`) | `settings` | `config.py:280` |
| `TWILIO_AUTH_TOKEN` | Comunicação | Condicional | Não (`None`) | `settings` | `config.py:281` |
| `MAILGUN_API_KEY` | Comunicação | Sim | Não (`None`) | `os.getenv` | `mailgun_provider.py:48` |
| `MAILGUN_DOMAIN` | Comunicação | Sim | Não (`None`) | `os.getenv` | `mailgun_provider.py:49` |
| `RESEND_API_KEY` | Comunicação | Não | Não (`None`) | `settings` | `config.py:297` |
| `WHATSAPP_API_TOKEN` | Comunicação | Condicional | Não (`None`) | `os.environ.get` | `whatsapp.py:85` |
| `PEARCH_API_KEY` | Integrações | Condicional | Não (`None`) | `settings` | `config.py:276` |
| `APIFY_API_KEY` | Integrações | Condicional | Não (`None`) | `os.environ.get` | `apify_service.py:17` |
| `STRIPE_SECRET_KEY` | Integrações | Sim | Não (`None`) | `settings` | `config.py:306` |
| `STRIPE_WEBHOOK_SECRET` | Integrações | Sim | Não (`None`) | `settings` | `config.py:307` |
| `GOOGLE_CALENDAR_CLIENT_ID` | Calendários | Não | Não (`None`) | `settings` | `config.py:287` |
| `GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON` | Calendários | Não | Não (`None`) | `settings` | `config.py:289` |
| `SENTRY_DSN` | Observabilidade | Não | Não (`None`) | `settings` | `config.py:200` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Observabilidade | Não | Não (`""`) | `settings` | `config.py:123` |
| `S3_ACCESS_KEY` | Storage | Condicional | Não (`None`) | `settings` | `config.py:136` |
| `S3_SECRET_KEY` | Storage | Condicional | Não (`None`) | `settings` | `config.py:137` |
| `AUDIT_STORAGE_BUCKET` | Storage | Condicional | Não (`""`) | `settings` | `config.py:133` |
| `FIELD_ENCRYPTION_KEY` | Criptografia | **Sim** | Não (fail-closed) | `os.environ.get` | `encrypted_field_mixin.py:75` |
| `ENCRYPTION_KEY` | Criptografia | **Sim** | Não (ephemeral em dev) | `os.getenv` | `encryption/__init__.py:17` |
| `BACKEND_URL` | Frontend | Não | Sim (`127.0.0.1:8001`) | `process.env` | `proxy-handler.ts:4` |
| `DEV_AUTO_LOGIN_PASSWORD` | Frontend | Não | Sim (`demo123`) | `process.env` | `auto-login/route.ts:13` |

---

*Documento gerado com base na análise estática dos arquivos relevantes. Não foram feitas alterações de código. Implementação de correções está fora do escopo desta auditoria (ver task #175).*
