# INTEGRATIONS_INFRASTRUCTURE_AUDIT.md
**Protocolo:** PX03 — Auditoria de Integrações e Infraestrutura  
**Data:** 2026-04-14  
**Executado por:** SRE / Claude Agent  
**Repositórios auditados:** `lia-agent-system` (Python/FastAPI, Replit) + `ats-api-copia` (Rails 7.1, GCP)  

---

## SEÇÃO 1: SUMÁRIO EXECUTIVO

### Scores por Área

| Área | Score | Status |
|------|-------|--------|
| Serviços Externos | 3/10 | CRITICO — maioria em modo SIMULADO ou sem credenciais |
| Secrets Management | 5/10 | RISCO — SECRET_KEY tem default hardcoded ("change-this-in-production") |
| Redis | 6/10 | FUNCIONAL mas SPOF não-mitigado; sem autenticação configurada |
| Workers (Celery/Sidekiq/Sneakers) | 5/10 | Arquitetura sólida no docker-compose, mas Sneakers COMENTADO no Rails |
| Banco de Dados | 7/10 | Dois PostgreSQL separados (ok por design), SSL apenas no Rails prod |
| CI/CD | 6/10 | Pipeline existe para ambos; deploy Python→GCP configurado; Rails sem deploy automatizado |
| Monitoramento | 4/10 | Sentry e OTEL configurados mas sem DSN/endpoint definidos |

### Top 5 Findings Críticos

| # | Finding | Impacto |
|---|---------|---------|
| F-01 | Email em modo SIMULADO: nenhum email real é enviado — sistema retorna `smtp_configured=False`, status="queued" | Nenhuma comunicação com candidatos funciona em produção |
| F-02 | WhatsApp (Twilio) apenas chamado na lib; shared_searches usa `send_whatsapp_simulated()` — não envia mensagens reais | Triagem e convites WSI via WhatsApp não chegam aos candidatos |
| F-03 | Billing/Stripe em "simulation mode" — `/my-invoices/{id}/pay` é explicitamente marcado como simulação; STRIPE_SECRET_KEY opcional | Cobranças não são processadas |
| F-04 | SECRET_KEY default "change-this-in-production" — se variável não for setada, validator lança ValueError, mas o risco de misconfiguration é alto | Tokens JWT inválidos / falha em startup em produção |
| F-05 | Sneakers (RabbitMQ consumer Rails) está COMENTADO no docker-compose.yml e não tem confirmação de estar rodando em GCP | Canal Rails→Python via RabbitMQ pode estar inativo |

---

## SEÇÃO 2: SERVIÇOS EXTERNOS — STATUS REAL

| Serviço | Credencial Configurada? | Modo | Retry? | Webhook? | Severidade |
|---------|------------------------|------|--------|----------|------------|
| **Email (Mailgun primary)** | Opcional — `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` não no .env.example | **SIMULADO** — `smtp_configured=False`, emails ficam em fila "queued" | Resend como fallback automático | Não configurado | CRITICO |
| **Email (Resend fallback)** | `RESEND_API_KEY` — não listado no .env.example principal | **SIMULADO** (fallback de fallback) | Circuit breaker implementado | Não | CRITICO |
| **WhatsApp (Twilio)** | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` listados; `ENABLE_TWILIO=false` | **SIMULADO** — `send_whatsapp_simulated()` loga sem enviar | Não | Não | CRITICO |
| **Microsoft Teams** | `MICROSOFT_APP_ID` + `MICROSOFT_APP_PASSWORD` + `TEAMS_WEBHOOK_URL` listados | **PARCIAL** — `ENABLE_MICROSOFT_GRAPH=true` mas sem confirmação de credenciais reais | Não confirmado | `TEAMS_WEBHOOK_SECRET` opcional | ALTO |
| **Google Calendar / Outlook** | `AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET` listados | **PARCIAL** — MS Graph habilitado, mas sem scraping de calendário confirmado | Não | Não | MEDIO |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` — listado como required no .env.example; usado em CI via GitHub Secrets | **REAL** — LLM primário `claude-sonnet-4-6` | Cascade para Gemini/OpenAI | Não | BAIXO (ativo) |
| **Google Gemini** | `AI_INTEGRATIONS_GEMINI_API_KEY` — variante Replit AI Integrations | **REAL** — modelo padrão para routing (`gemini-2.5-flash`) | Cascade | Não | BAIXO (ativo) |
| **OpenAI** | `OPENAI_API_KEY` — listado como fallback | **PARCIAL** — fallback de cascade, não confirmado em produção | Sim (cascade) | Não | MEDIO |
| **LangSmith** | `LANGCHAIN_API_KEY` — `LANGCHAIN_TRACING_V2=false` por padrão | **DESABILITADO** por padrão | N/A | Não | BAIXO |
| **WorkOS (Auth)** | `WORKOS_CLIENT_ID` + `WORKOS_API_KEY` + `WORKOS_WEBHOOK_SECRET` | **PARCIAL** — schema Rails tem `company_workos_config` e `workos_user_id`; Python tem models; integração ponta-a-ponta não confirmada | Não | `WORKOS_WEBHOOK_SECRET` presente | ALTO |
| **Stripe (Billing)** | `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PUBLISHABLE_KEY` — todos Optional | **SIMULADO** — endpoint `/my-invoices/{id}/pay` explicitamente marcado "simulation mode" | Não | `STRIPE_WEBHOOK_SECRET` declarado | CRITICO |
| **Pearch AI (sourcing)** | `PEARCH_API_KEY` listado; `ENABLE_PEARCH_AI=false` | **DESABILITADO** por feature flag | Não | Não | MEDIO |
| **LinkedIn** | URL scraping via Apify (`APIFY_API_KEY` opcional) | **SCRAPING** — lê dados da URL; não é integração OAuth oficial | Não | Não | MEDIO |
| **Jira** | `JIRA_EMAIL` + `JIRA_API_TOKEN` + `JIRA_CLOUD_ID` listados | **CONFIGURADO** — inclui `JIRA_CLOUD_ID=8cf762f8-6a44-47de-8915-6b3dc0cd2715` | Não | Não | BAIXO |
| **HubSpot** | Não encontrado em Python; não encontrado em Rails (nenhum hit grep) | **NAO IMPLEMENTADO** — mencionado em docs de decisão mas não há código | N/A | N/A | INFO |
| **Elasticsearch** | `ELASTICSEARCH_URL` opcional; `SEARCH_BACKEND=postgres` por padrão | **DESABILITADO** (postgres mode) | Não | Não | BAIXO |
| **S3 / Audit Storage** | `S3_ACCESS_KEY` + `S3_SECRET_KEY` opcionais; `AUDIT_STORAGE_TYPE=file` por padrão | **SIMULADO** — gravando localmente em `./audit_logs` | Não | Não | MEDIO |
| **RabbitMQ** | `RABBITMQ_URL` listado; default `amqp://guest:guest@localhost:5672/` | **PARCIAL** — producer/consumer implementados no Python; Sneakers Rails COMENTADO no docker-compose | Sim (retry_max_times=5 Sneakers) | Não | ALTO |

### Flags de simulação identificados

```
app/api/v1/email.py:77       → "Current Status: SIMULATED/LOGGED"
app/api/v1/email.py:105      → "Status: QUEUED (SMTP not configured)"
app/api/v1/shared_searches.py:196 → def send_whatsapp_simulated(...) — "not actually sent"
app/api/v1/billing.py:1467   → "Mark invoice as paid (simulation)"
app/api/v1/communication.py:428 → "mock": True (quando Twilio não configurado)
ENABLE_TWILIO=false           → feature flag desabilitado no .env.example
ENABLE_PEARCH_AI=false        → feature flag desabilitado
```

---

## SEÇÃO 3: SECRETS MANAGEMENT

| Secret | Hardcoded? | Fallback Aleatório? | No .gitignore? | Risco |
|--------|-----------|--------------------|--------------| ------|
| `SECRET_KEY` (JWT Python) | SIM — default `"change-this-in-production"` | NAO — validator lança ValueError se ausente em produção | Sim (.env no .gitignore) | ALTO — deploy sem .env = crash; deploy com valor errado = tokens inválidos |
| `RAILS_JWT_SECRET_KEY` | NAO — Optional[str] = None | NAO | Sim | ALTO — sem essa chave, Python não valida tokens emitidos pelo Rails |
| `WORKOS_API_KEY` | NAO — Optional | NAO | Sim | ALTO — auth SSO pode falhar silenciosamente |
| `WORKOS_WEBHOOK_SECRET` | NAO — Optional | NAO | Sim | MEDIO |
| `ANTHROPIC_API_KEY` | NAO | NAO | Sim | ALTO — LLM primário para de funcionar |
| `STRIPE_SECRET_KEY` | NAO — Optional | NAO | Sim | ALTO — billing inativo (mas atualmente em simulação) |
| `RABBITMQ_URL` | SIM — default guest:guest em Python e Rails | NAO | Sim | MEDIO — credenciais padrão inseguras em produção |
| `REDIS_URL` | SIM — default `redis://localhost:6379/0` | NAO | Sim | MEDIO — sem auth Redis |
| `DATABASE_URL` (Python) | SIM — default `postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db` | NAO | Sim | ALTO — conexão falha se não sobrescrita |
| `database_user/pass` (Rails) | NAO — `ENV["database_user"]` em produção | NAO | Sim | ALTO |
| `RAILS_MASTER_KEY` | NAO — `config.require_master_key` está comentado | NAO | Sim | MEDIO — credentials Rails não verificadas no boot |
| `DOPPLER_TOKEN` | NAO — `SECRETS_PROVIDER=env` por padrão | NAO | Sim | INFO — Doppler não ativo |

**Conclusão sobre fallback aleatório:** Nenhum secret usa `secrets.token_hex()` ou `uuid4()` como default — boa prática. O risco é o default fixo hardcoded do `SECRET_KEY` e das URLs de infra com credenciais guest/padrão.

---

## SEÇÃO 4: REDIS / CACHE

### O que é armazenado no Redis

| Dado | Chave (padrão) | TTL | PII? |
|------|---------------|-----|------|
| Cache de roteamento (CascadedRouter Tier 2) | hash da mensagem | `ROUTER_CACHE_TTL=3600s` (1h) | NAO (apenas domain_id + confidence) |
| Cache semântico (semantic_cache) | hash SHA da mensagem | `SEMANTIC_CACHE_TTL=86400s` (24h) | POTENCIAL — contém resposta do LLM |
| TOONCard (avaliação candidato) | `toon:{candidate_id}:{job_id}:{company_id}` | `_TOON_CACHE_TTL` (1h, via toon_service.py) | SIM — scores de candidato |
| Draft Wizard WSI | `wizard_draft:{session_id}` | 86400s (24h) | SIM — dados da vaga em construção |
| Sessão WSI Async | `wsi_async:{token}` | variável (min 3600s) | SIM — estado da triagem |
| Budget de tokens por tenant | chave de budget por `company_id` | `_TTL_SECONDS` (config) | NAO |
| Requisições de tokens por tenant | chave de request por `company_id` | `_REQ_TTL_SECONDS` (config) | NAO |
| DLQ (Dead Letter Queue) das tasks Celery | via `dlq_service.push_failure()` em Redis | Não definido — risco de acúmulo | NAO |
| Celery task results | backend Redis | `result_expires=3600s` | POTENCIAL |
| Celery Beat schedule state | PersistentScheduler | Permanente (arquivo) | NAO |
| Recruiter behavior profile | key por recruiter | 24h (por endpoint) | SIM — perfil comportamental |

### O que se perde se Redis reiniciar

- Cache de roteamento (reconstrói automaticamente na próxima chamada, custo LLM)
- Cache semântico de 24h (maior impacto — perda de economia LLM)
- TOONCards em cache (re-gerados na próxima requisição)
- Drafts de Wizard em andamento (usuário perde progresso da vaga não salva em DB)
- Sessões WSI Async em andamento (triagem interrompida)
- DLQ de tasks com falha (tarefas falhas perdidas sem retentativa)
- Budget counters de tokens (reconta do zero — pode ultrapassar limite sem aviso)
- Celery tasks em execução (workers perdem conexão com broker se Celery usar Redis)

### Riscos Adicionais

- **PII em plaintext:** TOONCards (scores de candidatos), respostas de LLM no semantic_cache e draft do Wizard contêm dados sensíveis sem criptografia em repouso
- **Single Point of Failure:** Redis é used como: cache de roteamento, broker Celery (BROKER_BACKEND=redis por padrão), result backend, DLQ, rate limiting, token budget — queda do Redis paralisa a plataforma inteira
- **Sem autenticação Redis:** `REDIS_URL=redis://localhost:6379/0` sem senha por padrão
- **ActionCable Rails também usa Redis** (`config.action_cable.url = ENV.fetch("REDIS_URL", ...)`) — mesma instância potencial

---

## SEÇÃO 5: RABBITMQ / WORKERS

### Configuração Atual

#### Python (Celery + aio_pika)

```
Broker padrão: BROKER_BACKEND=redis → REDIS_URL (NÃO RabbitMQ por padrão)
Override: BROKER_BACKEND=rabbitmq → RABBITMQ_URL
Produção GCP: BROKER_BACKEND=pubsub → CELERY_BROKER_URL obrigatório (stub, cai em Redis)

Filas Celery:
  sourcing_high     (priority=8, concurrency=4) — worker-high
  evaluation_normal (priority=5, concurrency=4) — worker-high
  vagas_normal      (priority=5, concurrency=4) — worker-normal
  onboarding_low    (priority=3, concurrency=2) — worker-low
  celery            (default)

Beat Schedule (14 tarefas periódicas):
  06h BRT — drift check diário
  02h BRT — LGPD cleanup diário
  03h BRT — TTL de conversas diário
  06h BRT — briefing diário
  Todo início de hora — followup WSI
  A cada 4h — check WSI abandonados
  Semanal segunda — weekly digest
  etc.

DLQ: implementada via dlq_service.push_failure() → Redis (NÃO RabbitMQ DLX)
```

#### Rails (Sidekiq + Sneakers)

```
Sidekiq 7.0: instalado, Redis URL via ENV['REDIS_URL'] — ativo
Sneakers (RabbitMQ): gem instalada, initializer configurado
  - RABBITMQ_URL com fallback guest:guest
  - retry_max_times: 5, retry_timeout: 5000ms
  - workers: 2, prefetch: 10, threads: 4
  - CRITICO: serviço sneakers COMENTADO no docker-compose.yml
  - RISCO: não confirmado se está rodando em GCP

job_import_worker.rb: usa reject! (Sneakers nack)
DLQ Rails: nenhuma DLX configurada no initializer
```

#### Canal RabbitMQ Rails↔Python

```
Exchange: rh_platform (declarado no PLATFORM_MAP)
  Rails → Python: routing_key=messages_created
  Python → Rails: routing_key=messages_processed
  Python → Rails: routing_key=jobs_import
  Rails → Python: routing_key=onboarding_events

Status real: INCERTO
  - Python: rabbitmq_producer e rabbitmq_consumer implementados
  - Rails: Sneakers COMENTADO no docker-compose
  - RabbitMQ no GCP: sendo configurado (não confirmado)
```

### Workers resilientes a restart?

| Worker | Resiliente? | Observação |
|--------|------------|------------|
| Celery (Python) | PARCIAL — `restart: unless-stopped` no docker-compose | Sem confirmação de deployment no Replit |
| Celery Beat | PARCIAL — `restart: unless-stopped` | Estado do scheduler em arquivo local |
| Sidekiq (Rails) | PARCIAL — depende de configuração GCP | `sidekiq.yml` não encontrado — configuração padrão |
| Sneakers (Rails) | **INCERTO** — serviço comentado | Canal RabbitMQ Rails→Python em risco |
| Uvicorn (FastAPI) | INCERTO — sem Procfile identificado | Possivelmente gerenciado pelo Replit |

---

## SEÇÃO 6: BANCO DE DADOS

### Dois PostgreSQL independentes (por design)

| Parâmetro | Python (lia_db) | Rails (ats_api / land_production) |
|-----------|----------------|----------------------------------|
| ORM | SQLAlchemy async + asyncpg | ActiveRecord + Apartment (multi-tenant) |
| Pool size | `DATABASE_POOL_SIZE=20`, `MAX_OVERFLOW=10` | Produção: `pool=30`, `reaping_frequency=12` |
| SSL | Não configurado no default | `sslmode: disable` (dev), `sslmode: require` (prod) |
| Prepared statements | Default SQLAlchemy | `prepared_statements: false` (prod) |
| Advisory locks | Default | `advisory_locks: false` (prod) |
| Migrations | 76 Alembic migrations | 51+ ActiveRecord migrations |
| Extensions | pgvector habilitado | Apartment (schemas por tenant), searchkick (Elasticsearch) |
| Multi-tenancy | Sem isolamento explícito (company_id por coluna) | Apartment — schemas separados por tenant |

### Riscos de DB

- **SSL Python:** `DATABASE_URL` default sem `sslmode=require` — conexão não-criptografada em produção se não sobrescrito
- **Dois bancos sem FK cruzadas:** sincronização exclusiva via RabbitMQ — falha no broker = divergência de dados
- **Migrations pendentes:** Não é possível confirmar remotamente sem `rails db:migrate:status` / `alembic current` executados no ambiente de produção
- **Pool Python:** `pool_size=20 + max_overflow=10` = até 30 conexões; somado às instâncias de workers = risco de `too many connections` se múltiplos workers rodarem em paralelo
- **`reaping_frequency: 12` (Rails):** intervalo de reaping em segundos — protege contra conexões mortas mas adiciona overhead

---

## SEÇÃO 7: DEPLOY / CI-CD

### Python (lia-agent-system)

```yaml
Arquivo: .github/workflows/ci.yml + deploy.yml
CI: test (pytest + coverage), PostgreSQL + Redis como services
Deploy: GitHub Actions → GCP
  - Authenticate: google-github-actions/auth@v2
  - Security scan: Bandit (SAST) + pip-audit (dependências) — bloqueia em HIGH
  - Triggers: push para main ou develop
  - Secrets necessários: GCP_SA_KEY, GCP_PROJECT, GCP_REGION, ANTHROPIC_API_KEY
```

**Gaps:**
- Sem Docker image tagging explícito no trecho lido (pode estar em passos não capturados)
- Nenhuma confirmação de health check pós-deploy (readiness probe)
- Celery workers: não confirmado se deploy.yml inclui workers (apenas API FastAPI)

### Rails (ats-api-copia)

```yaml
Arquivo: .github/workflows/ci.yml (apenas CI — sem deploy.yml)
CI: scan_ruby (Brakeman), scan_js (importmap audit), lint (Rubocop)
Deploy: NENHUM PIPELINE AUTOMATIZADO encontrado
  - Sem deploy.yml
  - Sem app.yaml (GCP App Engine)
  - Sem railway.json
  - Deploy manual ou não documentado
```

**Gaps críticos:**
- **Sem CI de testes Rails** — `ci.yml` só roda linters/scanners, não roda RSpec/test suite
- **Sem deploy automatizado** — processo de deploy Rails desconhecido
- **Rollback:** sem estratégia documentada

### Health Checks

| Endpoint | Sistema | Tipo |
|----------|---------|------|
| `GET /up` | Rails | Retorna 200 se boot sem exceção (padrão Rails 7.1) |
| `GET /voice/voice/health` | Python | Endpoint específico de voice |
| `GET /api/v1/system/health` | Python | Health completo (Redis, DB, Celery, RabbitMQ) |
| `GET /api/v1/admin/platform` | Python | Status Sentry e outros serviços |

---

## SEÇÃO 8: MONITORAMENTO

### O que monitora hoje

| Ferramenta | Sistema | Status | Observação |
|-----------|---------|--------|-----------|
| **Sentry** | Python | CONFIGURADO mas inativo — `SENTRY_DSN` não está no .env.example | `app/core/sentry.py` implementado com PII scrubbing; ativa quando `SENTRY_DSN` presente |
| **Sentry** | Rails | NAO CONFIGURADO — gem não encontrada no Gemfile | Sem error tracking no Rails |
| **OpenTelemetry (OTLP)** | Python | CONFIGURADO mas inativo — `OTEL_EXPORTER_OTLP_ENDPOINT=""` por padrão | `app/shared/tracing.py` implementado; ativa quando endpoint configurado |
| **LangSmith** | Python | DESABILITADO — `LANGCHAIN_TRACING_V2=false` por padrão | Rastreamento de LLM chains disponível |
| **Flower (Celery)** | Python | CONFIGURADO no docker-compose (porta 5555) | Dashboard de workers Celery; não confirmado em produção |
| **RabbitMQ Management UI** | Infra | CONFIGURADO (porta 15672 no docker-compose) | Não confirmado em produção GCP |
| **Logging estruturado** | Python | ATIVO — `LOG_LEVEL=INFO`, PIIMaskingFilter instalado em workers | Logs para STDOUT; sem agregação centralizada confirmada |
| **Logging** | Rails | ATIVO — `ActiveSupport::TaggedLogging` para STDOUT em produção | Sem aggregação confirmada |
| **Prometheus/Datadog/Grafana** | Ambos | NAO CONFIGURADO | Mencionados apenas como skills de candidatos no ontology engine |

### Gaps de Observabilidade

1. **Zero alerting ativo** — sem Sentry DSN, sem OTLP endpoint, sem Datadog → erros silenciosos em produção
2. **Rails sem error tracking** — falhas no backend CRUD não são capturadas
3. **Sem APM** — sem rastreamento de latência por endpoint ou por agente LLM
4. **Sem log aggregation** — logs vão para STDOUT mas sem Stackdriver/CloudLogging configurado explicitamente
5. **Celery workers sem health probe externa** — Flower previsto mas não confirmado em produção
6. **Budget de tokens sem alerta** — `TENANT_TOKEN_BUDGET_ALERT_THRESHOLD=0.80` calculado, mas sem destinatário de alerta configurado
7. **Sem SLO/SLA instrumentado** — plataforma tem conceito de SLA (sla_critical nos jobs) mas sem medição real

---

## SEÇÃO 9: TABELA COMPLETA DE FINDINGS

| ID | Severidade | Área | Descrição | Arquivo/Localização | Bloqueador? |
|----|-----------|------|-----------|---------------------|-------------|
| F-01 | CRITICO | Email | Email em modo SIMULADO — `smtp_configured=False`, nenhum email real enviado | `app/api/v1/email.py:77,105,115` | SIM |
| F-02 | CRITICO | WhatsApp | `send_whatsapp_simulated()` loga mas não envia; `ENABLE_TWILIO=false` | `app/api/v1/shared_searches.py:196` + `.env.example` | SIM |
| F-03 | CRITICO | Billing | Stripe em simulation mode; STRIPE_SECRET_KEY não configurado | `app/api/v1/billing.py:1467` + `libs/config/config.py:306` | SIM (billing) |
| F-04 | CRITICO | Workers | Sneakers (RabbitMQ consumer Rails) COMENTADO no docker-compose | `ats-api-copia/docker-compose.yml` | SIM (canal Rails→Python) |
| F-05 | ALTO | Secrets | `SECRET_KEY` tem default hardcoded `"change-this-in-production"` | `libs/config/lia_config/config.py` | ALTO |
| F-06 | ALTO | Secrets | `RABBITMQ_URL` e `REDIS_URL` com credenciais default (guest:guest, sem auth) | `.env.example` + `config/initializers/sneakers.rb` | MEDIO |
| F-07 | ALTO | Auth | `RAILS_JWT_SECRET_KEY=None` — Python não valida tokens Rails sem essa chave | `libs/config/lia_config/config.py` | SIM |
| F-08 | ALTO | Auth | WorkOS integração ponta-a-ponta não confirmada — schema Rails tem tabelas, Python tem models, mas fluxo real incerto | `app/auth/workos_models.py` + Rails migrations | ALTO |
| F-09 | ALTO | Monitoramento | Sentry sem DSN configurado — erros Python silenciosos em produção | `app/core/sentry.py:4` + `.env.example` (ausente) | NAO (mas risco alto) |
| F-10 | ALTO | Monitoramento | Rails sem Sentry ou qualquer error tracking | `ats-api-copia/Gemfile` (ausente) | NAO |
| F-11 | ALTO | Redis | Redis é SPOF total — cache, Celery broker, result backend, DLQ, rate limit na mesma instância | `libs/config/lia_config/config.py:MessagingSettings` | SIM |
| F-12 | ALTO | DB | `DATABASE_URL` Python sem `sslmode=require` no default | `.env.example` + `libs/config/config.py:DatabaseSettings` | MEDIO |
| F-13 | ALTO | CI/CD | Rails sem pipeline de deploy automatizado | `.github/workflows/` (ci.yml apenas) | NAO (mas deploy manual = risco) |
| F-14 | ALTO | CI/CD | Rails CI não roda test suite (RSpec) — apenas linters/scanners | `.github/workflows/ci.yml` (Rails) | NAO |
| F-15 | MEDIO | Workers | Celery Beat persiste schedule em arquivo local — perda de estado em restart | `libs/config/lia_config/celery_app.py:beat_schedule` | MEDIO |
| F-16 | MEDIO | RabbitMQ | DLQ implementada em Redis (não RabbitMQ DLX) — mensagens Rails perdidas sem DLQ nativa | `app/shared/resilience/dlq_service.py` + `sneakers.rb` | MEDIO |
| F-17 | MEDIO | Redis | PII em plaintext no Redis — TOONCards, respostas LLM, drafts Wizard sem criptografia em repouso | `app/services/toon_service.py` + `wizard_smart_orchestrator.py` | MEDIO |
| F-18 | MEDIO | Pearch AI | `ENABLE_PEARCH_AI=false` — sourcing externo desabilitado | `.env.example` | INFO |
| F-19 | MEDIO | OTEL | OpenTelemetry configurado mas endpoint vazio — sem rastreamento distribuído | `libs/config/config.py:LLMSettings.OTEL_EXPORTER_OTLP_ENDPOINT=""` | NAO |
| F-20 | MEDIO | Deploy | Celery workers não confirmados no deploy.yml GCP — API FastAPI pode subir sem workers | `.github/workflows/deploy.yml` (trecho parcial lido) | MEDIO |
| F-21 | MEDIO | DB | Dois PostgreSQL sem FK cruzadas — divergência de dados se RabbitMQ cair | PLATFORM_MAP.md (por design) | MEDIO |
| F-22 | MEDIO | RabbitMQ/GCP | RabbitMQ no GCP "sendo configurado" — status de produção incerto | Context arquitetural | SIM (canal de integração) |
| F-23 | BAIXO | Secrets | `RAILS_MASTER_KEY` não enforced (`config.require_master_key` comentado) | `ats-api-copia/config/environments/production.rb:14` | BAIXO |
| F-24 | BAIXO | Email | `EmailService` class marcada como `@deprecated` — callers legados ainda a usam | `app/domains/communication/services/email_service.py:44` | BAIXO |
| F-25 | BAIXO | LLM | `LANGCHAIN_TRACING_V2=false` por padrão — sem rastreamento de chains em produção | `.env.example` | INFO |

---

## APÊNDICE: CONFIGURAÇÃO DE INFRA — RESUMO

### Serviços no docker-compose (Python — referência local/dev)
- PostgreSQL (pgvector:pg16) — porta 5432
- Redis 7-alpine — porta 6379
- RabbitMQ 3-management-alpine — porta 5672 + 15672
- FastAPI (porta 8000)
- api-vagas (porta 8001), api-funil (8002), api-onboarding (8003)
- Celery worker-high (sourcing_high + evaluation_normal, concurrency=4)
- Celery worker-normal (vagas_normal, concurrency=4)
- Celery worker-low (onboarding_low, concurrency=2)
- Celery Beat (PersistentScheduler)
- Flower (monitor Celery, porta 5555)

### Serviços no docker-compose (Rails — referência local/dev)
- PostgreSQL 15 — porta 5433
- Elasticsearch 7.17.20 — porta 9201
- Redis 7-alpine — porta 6380
- RabbitMQ 3-management — porta 5672 + 15672
- Sidekiq (ativo)
- **Sneakers (COMENTADO)**
- Rails web (porta 8080→3000)

### Destino de Produção
- Python/FastAPI: **Replit** (deploy contínuo pelo workspace)
- Rails: **GCP** (via GitHub Actions deploy.yml — ausente no Rails, presente no Python)
- Redis: **GCP** (sendo configurado)
- RabbitMQ: **GCP** (sendo configurado)
- PostgreSQL: **GCP** (CloudSQL presumido; `host: db` em dev → `ENV["host"]` em prod)

---

*Relatório gerado em 2026-04-14 via protocolo PX03.*
*Fonte de dados: SSH direto ao workspace Replit + análise estática de código.*
