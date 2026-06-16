# PLATFORM_HEALTH_AUDIT.md — PX01: Auditoria de Saúde da Plataforma
**Protocolo:** PX01  
**Data:** 2026-04-14  
**Auditores:** PX01-Rails Agent + PX01-Python Agent  
**Escopo:** Rails (`ats-api-copia`) + Python AI (`lia-agent-system`)  
**Cenário:** Frontend + IA no Replit · Backend Rails no GCP · Integração em andamento (não 100% completa)  
**Alimenta:** P32 MIGRATION_PLAN · PX07 DEPENDENCY_MAP

---

## Sumário Executivo

A plataforma WeDOTalent/LIA opera em dois layers distintos que ainda não estão plenamente integrados. O Rails (`ats-api-copia` no GCP) é o **backend CRUD oficial** com 12 tabelas ativas. O Python (`lia-agent-system` no Replit) é a **camada de IA** com agentes, WebSocket, Celery e RabbitMQ. A integração está bloqueada por **11 problemas críticos/altos** nos dois layers.

O maior risco atual não é técnico — é de **dados divergentes**: enquanto `RAILS_API_URL` não estiver configurado, o Python opera com seu próprio banco local e o Rails opera com o banco GCP. Candidatos criados pela IA não chegam ao Rails. Jobs importados no Rails ficam no tenant 1. Eventos de screening, interview e pipeline gerados pelo Python são silenciosamente descartados pelo worker Rails.

**Score Composto:**
| Layer | Score | Status |
|-------|-------|--------|
| Rails (ats-api-copia) | 56/100 | 🔴 |
| Python AI (lia-agent-system) | 63/100 | 🟠 |
| **Integração Cross-Layer** | **31/100** | 🔴 CRÍTICO |
| **Plataforma (Média Ponderada)** | **50/100** | 🔴 |

---

## PARTE I — Rails Backend (ats-api-copia)

*Score: 56/100 🔴 — 6 P0 Blockers*

### 1.1 Achados Críticos Rails

| ID | Sev | Descrição | Arquivo:Linha | Bloqueador? |
|----|-----|-----------|---------------|-------------|
| R01 | 🔴 P0 | `MagicLinksController` existe mas **não está roteado** — `/v1/auth/magic-link/verify` retorna 404 | `app/controllers/v1/auth/magic_links_controller.rb` | SIM |
| R02 | 🔴 P0 | `OnboardingController` existe mas **não está roteado** — `/v1/onboarding/progress`, `/v1/users/invite` retornam 404 | `app/controllers/v1/users/onboarding_controller.rb` | SIM |
| M01 | 🔴 P0 | `candidates` table **sem `account_id`** — único modelo de PII sem isolamento de tenant. Violação LGPD direta. | `db/schema.rb:37-89` | SIM |
| M02 | 🔴 P0 | `belongs_to :account` declarado em `candidate.rb` mas coluna não existe → `ActiveRecord::StatementInvalid` em qualquer eager-load | `app/models/candidate.rb:5` | SIM |
| T01 | 🔴 P0 | `ResourceLoader#set_resource` usa `klass.find_by(id:)` sem scope de tenant; `TenantScoped` silenciosamente ignora models sem `account_id` | `app/controllers/concerns/resource_loader.rb:8`, `tenant_scoped.rb:18` | SIM |
| CORS | 🔴 P0 | `origins 'http://localhost:3000'` hardcoded — API Rails **inacessível** de qualquer ambiente não-local | `config/initializers/cors.rb:3` | SIM |
| E01 | 🔴 P0 | JWT decodificado em 3 locais com lógicas divergentes (`rescue StandardError` vs `rescue JWT::DecodeError`) | 3 controllers | SIM |
| W01 | 🟠 P1 | 6 handlers `LiaEventsWorker` são stubs (`Rails.logger.info` apenas): screening, interview, offer, enrichment, pipeline | `app/workers/lia_events_worker.rb:71-96` | SIM |
| M03 | 🟠 P1 | `JobImportWorker` hardcoda `user_id: 1, account_id: 1` — todos os jobs importados ficam no tenant 1 | `app/workers/job_import_worker.rb:35-36` | SIM |
| P01 | 🟠 P1 | `MessageService::EventPublisher` abre conexão TCP Bunny nova a cada request HTTP — sem pool | `app/services/message_service/event_publisher.rb` | SIM |
| T02 | 🟠 P1 | Apartment gem configurado mas **todos os elevators comentados** — schema switching nunca ocorre | `config/initializers/apartment.rb:27-34` | SIM |
| T03 | 🟠 P1 | `perform_search` em `SearchRenderer` sem `where: { account_id: }` — Elasticsearch retorna candidatos de todos os tenants | `app/controllers/concerns/search_renderer.rb:14-21` | SIM |
| A01 | 🟠 P1 | RBAC implementado (5 tabelas + `User#can?`) mas **zero controllers usam `authorize`** | todos os controllers | NÃO (feature completa ausente) |
| M06 | 🟡 P2 | 100+ modelos `.rb` sem tabela no schema — `AuditLog`, `TalentPool`, `Interview`, `Webhook` etc. | `app/models/` | NÃO* |

### 1.2 Integration Readiness: Endpoints Rails (visão do Python)

| Endpoint | Existe? | Roteado? | Tenant OK? | Status |
|----------|---------|---------|-----------|--------|
| `POST /v1/sessions` | SIM | SIM | N/A | ✅ FUNCIONA |
| `GET /v1/me` | SIM | SIM | N/A | ✅ FUNCIONA |
| `GET /v1/users/jobs` | SIM | SIM | PARCIAL | ⚠️ RISCO |
| `GET /v1/users/jobs/:id` | SIM | SIM | NÃO | ⚠️ CROSS-TENANT |
| `GET /v1/users/candidates` | SIM | SIM | QUEBRADO | 🔴 BLOQUEADO |
| `GET /v1/users/candidates/:id` | SIM | SIM | QUEBRADO | 🔴 BLOQUEADO |
| `POST /v1/users/candidates` | SIM | SIM | QUEBRADO | 🔴 QUEBRADO |
| `GET /v1/auth/magic-link/verify` | SIM | **NÃO** | N/A | 🔴 404 |
| `GET /v1/users/applies` | SIM | SIM | NÃO | ⚠️ RISCO |
| `GET /v1/users/messages` | SIM | SIM | SIM | ✅ FUNCIONA |
| `/v1/onboarding/progress` | SIM | **NÃO** | N/A | 🔴 404 |
| `/v1/users/edit/:id` | SIM (manual) | NÃO confiável | N/A | 🔴 RISCO |

### 1.3 RabbitMQ: Python → Rails (queues)

| Queue | Consumer Rails | Implementado? | Status |
|-------|--------------|--------------|--------|
| `messages_processed` | `MessageWorker::ProcessWorker` | SIM | ✅ FUNCIONA |
| `lia_events_queue` (screening.completed) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `lia_events_queue` (interview.scheduled) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `lia_events_queue` (interview.completed) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `lia_events_queue` (offer.sent) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `lia_events_queue` (candidate.enriched) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `lia_events_queue` (pipeline.moved) | `LiaEventsWorker` | **STUB** | 🔴 DESCARTADO |
| `jobs_import` | `JobImportWorker` | SIM (tenant errado) | ⚠️ DADO ERRADO |
| `onboarding_events` | NENHUM | NÃO | 🔴 NÃO PROCESSADO |

---

## PARTE II — Python AI Layer (lia-agent-system)

*Score: 63/100 🟠 — 3 P0 Blockers, 5 P1*

### 2.1 Route Classification: AI-KEEP vs CRUD-MOVE-TO-RAILS

De acordo com a decisão arquitetural ([Rails Migration Context](memory/project_rails_migration.md)), CRUD deve migrar para Rails e IA fica no Python.

| Arquivo | Tipo | Classificação | Ação |
|---------|------|---------------|------|
| `app/api/v1/job_vacancies/crud.py` | CRUD completo (GET/POST/PUT/DELETE) | CRUD-MOVE | Migrar para Rails `jobs` controller |
| `app/api/v1/candidates/candidates_crud.py` | CRUD completo | CRUD-MOVE | Migrar para Rails `candidates` controller |
| `app/api/v1/agent_chat_ws.py` | WebSocket + LLM orchestration | AI-KEEP | Manter em Python |
| `app/api/v1/agent_chat_sse.py` | SSE + LLM streaming | AI-KEEP | Manter em Python |
| `app/api/v1/voice.py` | Transcrição + análise de voz (Whisper/Claude) | AI-KEEP | Manter em Python |
| `app/api/v1/async_endpoints.py` | Celery task dispatch (triagem, email em massa) | AI-KEEP | Manter em Python |
| `app/api/v1/rails_sync.py` | Bridge AI insights → Rails | AI-KEEP | Interface de integração |
| `app/api/v1/rails_health.py` | Circuit breaker probe | AI-KEEP | Infraestrutura |
| `app/api/v1/ats.py` | Integração Merge.dev ATS | AI-KEEP | Manter (integração externa) |
| `app/api/v1/drift.py` | Drift/divergência tracking | AI-KEEP | Observabilidade |
| `app/domains/*/` | Domain AI agents (screening, enrichment, etc.) | AI-KEEP | Core IA |

### 2.2 Achados Críticos Python

| ID | Sev | Descrição | Arquivo:Linha | Bloqueador? |
|----|-----|-----------|---------------|-------------|
| PY01 | 🔴 P0 | `RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))` — enquanto não configurado, Python opera com **banco de dados local próprio**, criando **divergência de dados** com Rails GCP. Candidatos e jobs existem em dois bancos independentes. | `app/domains/integrations_hub/services/rails_adapter.py` | SIM |
| PY02 | 🔴 P0 | Python chama `$RAILS_BACKEND_URL/v1/onboarding/progress` (linha 614) e `/v1/users/edit/{user_id}` (linha 621) — **ambas as rotas não existem no `routes.rb` do Rails**. Fallback: `http://localhost:3000` (hardcoded). | `app/services/onboarding_orchestrator.py:607,614,621` | SIM |
| PY03 | 🔴 P0 | `SECRET_KEY: str = "change-this-in-production"` default nunca substituído em dev/staging. Token gerado pelo Python com esta chave é **incompatível** com Rails (que usa `RAILS_JWT_SECRET_KEY` — env var diferente e separada). | `app/core/config.py:146-152` | SIM |
| PY04 | 🟠 P1 | `WSManager` é singleton in-memory (`_sessions: dict[str, WebSocket]`). Com múltiplos workers uvicorn/gunicorn (standard em GCP/Replit), sessões WebSocket de um worker são **invisíveis** para outros. Sessões morrem silenciosamente sob load. | `app/shared/websocket/ws_manager.py:ws_manager = WSManager()` | SIM (escala) |
| PY05 | 🟠 P1 | `global _AGENTS_LOADED` em `agent_chat_ws.py:333` — flag de inicialização de agentes é global por processo. Com múltiplos workers, cada processo carrega agentes independentemente (sem problema) mas o flag não é thread-safe para inicialização concorrente. | `app/api/v1/agent_chat_ws.py:333` | SIM (concorrência) |
| PY06 | 🟠 P1 | `_injection_guard = PromptInjectionGuard()` global singleton (linha 186) — estado de guard compartilhado entre todas as conexões. Se guard tiver estado interno (histórico de sessão), há possibilidade de **cross-session contamination**. | `app/api/v1/agent_chat_ws.py:186` | NÃO (se stateless) |
| PY07 | 🟠 P1 | Celery (`app/core/celery_app.py`) usado em `async_endpoints.py` e `jobs_ws.py` para 5 tipos de tarefas batch — sem evidência de broker Redis/RabbitMQ configurado em variáveis de ambiente. Se `CELERY_BROKER_URL` não configurado, `send_task()` falha silenciosamente. | `app/api/v1/async_endpoints.py:50,84,114,149` | SIM |
| PY08 | 🟡 P2 | `RAILS_BACKEND_URL` com default `http://localhost:3000` (hardcoded em código Python, não apenas em config). Em produção no Replit, este fallback aponta para localhost inexistente. | `app/services/onboarding_orchestrator.py:607` | NÃO* (só falha se RAILS_BACKEND_URL não setado) |
| PY09 | 🟡 P2 | CRUD routes (`job_vacancies/crud.py`, `candidates/candidates_crud.py`) ainda em Python criam **endpoints duplicados** em relação ao Rails. Writes podem ir para o banco Python em vez do Rails GCP. | `app/api/v1/job_vacancies/crud.py`, `app/api/v1/candidates/candidates_crud.py` | SIM (dados) |

### 2.3 JWT Cross-Layer Analysis

```
Python layer: SECRET_KEY = settings.SECRET_KEY (HS256)
              → Tokens Python são validados APENAS pelo Python

Rails layer:  JWT decoded via ApplicationController#jwt_decode
              → Usa Rails secret_key_base

Bridge:       RAILS_JWT_SECRET_KEY: Optional[str] = None  (config.py)
              → Se configurado = Python aceita tokens Rails
              → Se NÃO configurado (atual) = tokens Rails são REJEITADOS pelo Python

Status atual: Dois sistemas com dois JWT secrets independentes.
              Um usuário autenticado no Rails NÃO pode chamar a API Python sem novo login.
              Um usuário autenticado no Python NÃO pode chamar a API Rails sem novo login.
              → AUTENTICAÇÃO UNIFICADA INEXISTENTE
```

**Fix:** `RAILS_JWT_SECRET_KEY` deve ser o mesmo `secret_key_base` do Rails. Ambos devem usar o mesmo segredo. Python deve aceitar tokens Rails via `validate_rails_token_from_env()` (implementação já existe em `app/auth/rails_jwt.py` — só falta configurar o env var).

### 2.4 RailsAdapter Integration Flow

```python
# app/domains/integrations_hub/services/rails_adapter.py
RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))  # feature flag

CANDIDATE_FORK_TO_RAILS = {
    "uuid": "id",           # UUID Python → Bigint Rails (incompatível!)
    "full_name": "name",    # campo diferente
    "email": "email",       # igual
    "phone": "phone_number",
    ...  # 50+ mapeamentos
}
```

**Problema de ID:** Python usa UUIDs, Rails usa Bigints. O `CANDIDATE_FORK_TO_RAILS` dict tenta mapear `uuid → id` — quando o Python tenta buscar um candidato no Rails via UUID, o Rails retorna 404 (Bigint vs string).

---

## PARTE III — Matriz de Integração Cross-Layer

### 3.1 Estado Atual da Integração (linha por linha)

| Funcionalidade | Python | Rails | Integrado? | Gap |
|---------------|--------|-------|-----------|-----|
| Login/Auth | ✅ JWT próprio | ✅ JWT próprio | ❌ NÃO | Secrets diferentes; 2 sessões necessárias |
| Criação de candidato | ✅ CRUD local | 🔴 sem account_id | ❌ BLOQUEADO | M01 + ID type mismatch |
| Listagem de vagas | ✅ CRUD local | ✅ Rails jobs | ⚠️ PARCIAL | RAILS_ENABLED flag; scope parcial |
| Onboarding LIA | ✅ orchestrator | 🔴 não roteado | ❌ BLOQUEADO | R02 + rotas 404 |
| Triagem de currículo | ✅ AI agent | 🔴 stub | ❌ BLOQUEADO | W01 — evento descartado |
| Agendamento entrevista | ✅ AI agent | 🔴 stub | ❌ BLOQUEADO | W01 — evento descartado |
| Envio de oferta | ✅ AI agent | 🔴 stub | ❌ BLOQUEADO | W01 — evento descartado |
| Import de vagas (RabbitMQ) | ✅ publica | ⚠️ tenant errado | ⚠️ DADO ERRADO | M03 — hardcoded account 1 |
| WebSocket chat | ✅ funciona | N/A | ✅ OK | Single process OK |
| Notificações real-time | ✅ WSManager | N/A | ⚠️ RISCO | Multi-worker: PY04 |
| Tarefas batch (Celery) | ⚠️ broker? | N/A | ⚠️ INCERTO | PY07 — broker pode não estar configurado |
| Magic link | ✅ publica evento | 🔴 não roteado | ❌ BLOQUEADO | R01 — 404 |
| LGPD/compliance | ✅ compliance audit | 🔴 candidatos sem account_id | ❌ VIOLAÇÃO | M01 — PII sem tenant scope |

### 3.2 Análise de Gaps por Criticidade

```
P0 — Bloqueiam qualquer uso em produção multi-tenant (resolver IMEDIATO)
══════════════════════════════════════════════════════════════════════════
1. candidates.account_id MISSING          → LGPD violation + all candidate ops broken
2. CORS hardcoded localhost               → Rails API inacessível de produção
3. MagicLinksController não roteado       → onboarding flow quebrado
4. OnboardingController não roteado       → invite + progress tracking quebrado
5. JWT sem shared secret                  → autenticação unificada impossível
6. RAILS_API_URL não configurado          → Python opera em banco separado do Rails
7. Python → Rails routes inexistentes     → onboarding_orchestrator.py chama 404s

P1 — Bloqueiam integração completa (resolver em 1-2 sprints)
══════════════════════════════════════════════════════════════
8.  LiaEventsWorker 6 stubs               → AI workflow data perdida no Rails
9.  JobImportWorker account hardcoded     → dados no tenant errado
10. UUID vs Bigint ID mismatch            → RailsAdapter retorna 404 em lookups
11. WSManager in-memory                   → WebSocket quebrado com múltiplos workers
12. Celery broker desconhecido            → batch tasks podem falhar silenciosamente
```

---

## PARTE IV — Dimensões de Saúde (8 dimensões obrigatórias)

| Dimensão | Rails | Python | Cross-Layer | Status |
|----------|-------|--------|-------------|--------|
| **Routes** | 55/100 (2 controllers mortos) | 70/100 (CRUD duplicado) | 40/100 (routes Python→Rails 404) | 🔴 |
| **Models/Schema** | 45/100 (candidates sem account_id) | 65/100 (UUID/Bigint gap) | 30/100 (mapeamento 50+ campos divergente) | 🔴 |
| **Tenant Isolation** | 35/100 (cross-tenant em search+candidates) | 75/100 (company_id enforced em JWT) | 25/100 (candidates LGPD violation) | 🔴 |
| **Auth/RBAC** | 50/100 (RBAC não usado) | 70/100 (JWT + compliance) | 20/100 (2 sistemas, 2 secrets, 0 SSO) | 🔴 |
| **Persistence** | 60/100 (Bunny sem pool; hardcoded tenant) | 65/100 (dual DB quando RAILS_ENABLED=false) | 35/100 (dados divergem entre bancos) | 🔴 |
| **Workers** | 55/100 (6 stubs, exchange duvidoso) | 70/100 (Celery OK se broker configurado) | 30/100 (9 de 10 queues com problema) | 🔴 |
| **Error Handling** | 60/100 (JWT triplicado; rescue bare) | 65/100 (SSE bug SecurityCheckResult.get()) | 55/100 | 🟠 |
| **Dead Code** | 50/100 (100+ modelos sem tabela) | 72/100 (CRUD routes a migrar) | 45/100 | 🟠 |
| **Score Médio** | **56/100** | **70/100** | **35/100** | 🔴 |

---

## PARTE V — Plano de Resolução Priorizado

### Sprint 0 — Desbloqueadores Imediatos (< 1 dia cada)

| # | Ação | Arquivo | Impacto |
|---|------|---------|---------|
| 1 | **Fix CORS**: `origins ENV.fetch('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')` | `config/initializers/cors.rb:3` | Desbloqueia toda requisição de produção |
| 2 | **Rotar MagicLinksController**: `get 'auth/magic-link/verify', to: 'v1/auth/magic_links#verify'` | `config/routes.rb` | Desbloqueia onboarding + magic link |
| 3 | **Rotar OnboardingController**: adicionar namespace `users/onboarding` | `config/routes.rb` | Desbloqueia invite flow |
| 4 | **Configurar env vars**: `RAILS_API_URL`, `RAILS_JWT_SECRET_KEY` (= Rails secret_key_base) no Replit | `.env` / Replit Secrets | Ativa integração real Python→Rails |

### Sprint 1 — Tenant Isolation (crítico LGPD)

| # | Ação | Arquivo | Impacto |
|---|------|---------|---------|
| 5 | **Migration**: `add_column :candidates, :account_id, :bigint; add_index :candidates, :account_id` | nova migration | Resolve M01, M02, T01 |
| 6 | **Backfill**: associar candidatos existentes ao account correto | script de data migration | LGPD compliance |
| 7 | **Fix ResourceLoader**: `klass.where(account_id: current_account_id).find_by(id: params[:id])` | `app/controllers/concerns/resource_loader.rb:8` | Fecha cross-tenant read |
| 8 | **Fix SearchRenderer**: inject `where: { account_id: @current_account_id }` em `search_default` calls | `app/controllers/concerns/search_renderer.rb:14` | Fecha Elasticsearch cross-tenant |

### Sprint 2 — JWT Unificado + Workers

| # | Ação | Arquivo | Impacto |
|---|------|---------|---------|
| 9 | **Extrair JwtConcern**: único módulo de decode/encode com `rescue JWT::DecodeError` | novo `app/controllers/concerns/jwt_authenticatable.rb` | Resolve E01 |
| 10 | **Implementar LiaEventsWorker handlers**: update Apply, Candidate, pipeline stage no DB Rails | `app/workers/lia_events_worker.rb:71-96` | 6 AI workflows passam a persistir no Rails |
| 11 | **Fix JobImportWorker**: payload RabbitMQ deve incluir `user_id` e `account_id` | `app/workers/job_import_worker.rb:35-36` + Python publisher | Jobs no tenant correto |
| 12 | **RabbitMQ connection pool**: usar variável de instância com `connection ||= Bunny.new(...)` | `app/services/message_service/event_publisher.rb` | Resolve P01 |

### Sprint 3 — CRUD Migration + ID Unification

| # | Ação | Impacto |
|---|------|---------|
| 13 | Remover `job_vacancies/crud.py` do Python; rotear tudo via `RAILS_API_URL` | Elimina dado duplicado |
| 14 | Remover `candidates/candidates_crud.py` do Python após Sprint 1 | CRUD unificado no Rails |
| 15 | Definir estratégia de ID: manter UUID no Python como `external_id` em tabela Rails OU gerar Bigint no Rails e propagar | Resolve UUID vs Bigint mismatch |
| 16 | Configurar Redis para WSManager (ex: `redis_ws_manager`) | Resolve multi-worker WebSocket |

---

## PARTE VI — Bugs Críticos com Fix Code

### Bug 1 — SSE Security Check (AttributeError silenciado)
```python
# QUEBRADO (agent_chat_sse.py:207):
_security_result = check_input_security(content)  # returns dataclass SecurityCheckResult
if _security_result and _security_result.get("blocked"):  # AttributeError! dataclass não tem .get()
    ...
except Exception as e:
    logger.debug("[LIA-P03] Agent SSE compliance skipped: %s", e)  # SILENCIADO!

# FIX:
if _security_result and _security_result.is_blocked:
    return ...
```

### Bug 2 — WebSocket company_id Override
```python
# QUEBRADO (agent_chat_ws.py:651):
context = msg.get("context", {})     # attacker controls this dict
context.setdefault("company_id", company_id)  # setdefault NÃO overrride se chave já existe!

# FIX:
context["company_id"] = company_id   # força overwrite com valor do JWT
```

### Bug 3 — CORS Fix Rails
```ruby
# QUEBRADO (config/initializers/cors.rb:3):
origins 'http://localhost:3000'

# FIX:
origins ENV.fetch('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
```

### Bug 4 — ResourceLoader Cross-Tenant
```ruby
# QUEBRADO (app/controllers/concerns/resource_loader.rb:8):
instance_variable_set(:"@#{resource_name}", klass.find_by(id: params[:id]))

# FIX:
scoped = klass.respond_to?(:column_names) && klass.column_names.include?("account_id") \
         ? klass.where(account_id: @current_account_id) \
         : klass
instance_variable_set(:"@#{resource_name}", scoped.find_by(id: params[:id]))
```

---

## PARTE VII — Scores Finais

| Dimensão | Rails | Python | Cross-Layer |
|----------|-------|--------|-------------|
| Routes & Controllers | 55/100 🔴 | 70/100 🟠 | 40/100 🔴 |
| Models & Schema | 45/100 🔴 | 65/100 🟠 | 30/100 🔴 |
| Tenant Isolation | 35/100 🔴 | 75/100 🟠 | 25/100 🔴 |
| Auth/RBAC | 50/100 🟠 | 70/100 🟠 | 20/100 🔴 |
| Persistence & State | 60/100 🟠 | 65/100 🟠 | 35/100 🔴 |
| Workers & Processes | 55/100 🟠 | 70/100 🟠 | 30/100 🔴 |
| Error Handling | 60/100 🟠 | 65/100 🟠 | 55/100 🟠 |
| Dead Code | 50/100 🟠 | 72/100 🟠 | 45/100 🟠 |
| **MÉDIA** | **56/100 🔴** | **70/100 🟠** | **35/100 🔴** |

**Score de Plataforma (Ponderado): 50/100 🔴**

> Plataforma funciona em modo isolado (Python sem Rails ou Rails sem Python). Integração real entre os dois layers está **bloqueada por 7 gaps críticos**. O trabalho necessário para atingir "prontidão de produção integrada" é estimado em 3-4 sprints com foco em: (1) CORS + rotas, (2) tenant isolation + LGPD, (3) JWT unificado + workers, (4) CRUD migration.

---

*Relatório gerado em 2026-04-14. Protocolo PX01.*  
*Refs: P10 AI_SECURITY_AUDIT.md · P13 DUPLICATION_DIVERGENCE_MAP.md · P14 PROPORTIONALITY_AUDIT.md*
