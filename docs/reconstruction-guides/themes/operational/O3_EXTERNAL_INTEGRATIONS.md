# Theme: O3 — External Integrations — Operational Layer

## O que é este tema

O tema cobre todas as integrações do LIA com sistemas externos — tanto de entrada (Rails ATS como source of truth) quanto de saída (canais de comunicação com candidatos e recrutadores, APIs de sourcing externo). São três subsistemas:

1. **Rails Client** — proxy HTTP para o backend Rails WeDOTalent (`app/shared/rails_client.py`): wrappers fail-safe para leitura/escrita de dados CRUD que migraram para o Rails
2. **Multi-Channel Messaging** — roteamento de mensagens para candidatos via Email, WhatsApp, SMS, In-App, MS Teams (`app/shared/channels/` + `libs/messaging/lia_messaging/`)
3. **Sourcing APIs** — integrações de busca externa (Pearch AI, Apify, Merge/LinkedIn, Gupy, Pandapé) documentadas em `docs/integrations/apis/sourcing/sourcing_apis_catalog.yaml`

Contexto crítico: o LIA está em **processo de migração CRUD para o Rails** (MIGRATION_PLAN items 7.1/7.2). Python é a camada de IA; Rails é source of truth para jobs/candidates. O `rails_client.py` é o elo de ligação enquanto a migração não está completa. Endpoints Python CRUD legados são marcados com `deprecated_in_favor_of_rails()` (HTTP `Deprecation` + `Sunset` headers, kill switch via `STRICT_RAILS_ONLY=true`).

**Boundary com temas irmãos:** R3 (Messaging & Events) cobre o broker de eventos (BrokerInterface, UnifiedEventPublisher). O3 cobre a camada de *entrega de mensagens a humanos* (candidate/recruiter outreach). I8 (Auth) cobre o JWT compartilhado com Rails. I6 (API Layer) cobre as rotas FastAPI internas.

---

## Arquivos conectados (14 total)

### Camada Config (1 YAML)

| Arquivo | Bundle/Guide | Quando é consumido |
|---------|-------------|-------------------|
| `docs/integrations/apis/sourcing/sourcing_apis_catalog.yaml` | Infrastructure Bundle | Documentação/referência para agentes de sourcing; define SLOs, circuit breakers e fallbacks por API |

### Camada Código — Rails Client (2 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|----------------|
| `rails_client.py` | `app/shared/rails_client.py` | Wrappers fail-safe: `rails_get()`, `rails_patch()`, `rails_post()` |
| `deprecation.py` | `app/shared/rails_migration/deprecation.py` | FastAPI dependency para marcar endpoints Python legados como deprecated em favor do Rails |

### Camada Código — Multi-Channel (7 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|----------------|
| `channel_adapter.py` | `app/shared/channels/channel_adapter.py` | ABC `ChannelAdapter` + `ChannelType` + `ChannelMessage` + `DeliveryResult` dataclasses |
| `channel_router.py` | `app/shared/channels/channel_router.py` | `ChannelRouter.route()` — tenta canais preferidos + fallback para disponíveis |
| `multi_channel_service.py` | `app/shared/channels/multi_channel_service.py` | Singleton `MultiChannelService` — registra 5 adapters automaticamente |
| `email_adapter.py` | `app/shared/channels/adapters/email_adapter.py` | `EmailChannelAdapter` + `AI_GENERATED_FOOTER` obrigatório + opt-out LGPD |
| `whatsapp_adapter.py` | `app/shared/channels/adapters/whatsapp_adapter.py` | `WhatsAppChannelAdapter` — delega para `lia_messaging.whatsapp` |
| `teams_adapter.py` | `app/shared/channels/adapters/teams_adapter.py` | `MSTeamsChannelAdapter` |
| `sms_adapter.py` + `in_app_adapter.py` | `app/shared/channels/adapters/` | SMS + notificação in-app |

### Camada Código — lia_messaging (4 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|----------------|
| `email.py` | `libs/messaging/lia_messaging/email.py` | `send_email()` — auto-detect Mailgun > Resend > none |
| `whatsapp.py` | `libs/messaging/lia_messaging/whatsapp.py` | `send_whatsapp_message()` — Meta Graph API v19.0 ou Twilio |
| `teams.py` | `libs/messaging/lia_messaging/teams.py` | `send_teams_message()` — Adaptive Card via Incoming Webhook |
| `notification_service.py` | `libs/messaging/lia_messaging/notification_service.py` | `NotificationType` (5) + `ProactiveNotificationType` (14) |

### Integration points

- **R3 Messaging** → `UnifiedEventPublisher` dispara eventos que podem acionar `MultiChannelService` para notificações
- **R4 Background Jobs** → `webhook_tasks.py` usa `rails_client` para callbacks; `followup_service.py` usa multi-channel para follow-ups
- **C2 LGPD** → `EmailChannelAdapter._is_opted_out()` verifica consent antes de enviar; AI footer obrigatório
- **R1 Circuit Breakers** → Pearch AI, Apify, Gupy, Pandapé, Merge têm circuit breakers nomeados no catalog
- **I4 LLM Providers** → sourcing agents consomem Pearch + Apify via circuit breaker + fallback para RAG interno
- **I8 Auth** → `RAILS_JWT_SECRET_KEY` para validação cruzada de JWT entre Python e Rails

---

## Lógica IN → OUT

### Input (Rails Client)

```python
# Leitura via Rails
data = await rails_get("/v1/companies/123/candidate-portal/lgpd-requests")

# Escrita via Rails
result = await rails_patch("/v1/companies/123/candidates/42/status", data={"status": "approved"})

# Criação via Rails
record = await rails_post("/v1/companies/123/jobs", data={"title": "Eng SR"})
```

### Input (Multi-Channel)

```python
# Via MultiChannelService (recomendado)
service = MultiChannelService.get_instance()
message = ChannelMessage(
    recipient_id="candidate-uuid",
    recipient_name="Maria Silva",
    recipient_contact="maria@email.com",  # email ou phone (+5511...)
    subject="Seu processo seletivo",
    body_text="Olá Maria...",
    company_id=company_id,  # do JWT — nunca do payload
    vacancy_id="job-42",
)
result = await service.send(message, preferred_channels=[ChannelType.EMAIL, ChannelType.WHATSAPP])

# Via lia_messaging diretamente (para casos simples)
from lia_messaging.email import send_email
result = await send_email(to="maria@email.com", subject="...", body="...")
```

### Processing (Rails Client)

```
1. _get_client() → lazy singleton WeDOTalentATSClient()
2. client.get/patch/post(path, ...)
3. resp.data if resp and resp.data else {}
4. Em exceção: logger.warning + return {}  ← fail-safe
```

### Processing (Multi-Channel)

```
1. MultiChannelService.get_instance() → singleton (auto-registra 5 adapters no __init__)
2. ChannelRouter.route(message, preferred_channels, fallback=True):
   a. Tenta canais preferidos na ordem
   b. adapter.is_available() → verifica se canal está configurado
   c. adapter.send(message) → DeliveryResult
   d. Se FAILED e fallback=True → próximo canal disponível
3. EmailChannelAdapter.send(message):
   a. _is_opted_out(email, company_id) → LGPD check
   b. _add_ai_footer(body_text, body_html) → F7 compliance
   c. lia_messaging.email.send_email() → Mailgun ou Resend
4. WhatsAppChannelAdapter → lia_messaging.whatsapp.send_whatsapp_message() → Meta ou Twilio
5. MSTeamsChannelAdapter → lia_messaging.teams.send_teams_message() → Adaptive Card
```

### Processing (Sourcing APIs)

```
1. Sourcing agents verificam settings.ENABLE_PEARCH_AI / ENABLE_TWILIO
2. Circuit breaker verificado ANTES da chamada (ver R1)
3. API call com timeout do SLO
4. On success: return data
5. On failure: fallback definido no catalog (RAGPipelineService, internal_ats_cache, etc.)
```

### Output (Rails Client)

```python
dict  # dados do Rails ou {} em caso de erro (nunca lança exceção)
```

### Output (Multi-Channel)

```python
@dataclass
class DeliveryResult:
    success: bool
    channel: ChannelType   # EMAIL, WHATSAPP, SMS, IN_APP, MS_TEAMS
    message_id: str
    status: DeliveryStatus  # QUEUED, SENT, DELIVERED, READ, FAILED, BOUNCED
    provider_id: str | None  # ID do provider (Mailgun message ID, Meta message ID)
    error: str | None
    metadata: dict
```

### Escalation / HITL

- `deprecated_in_favor_of_rails()` com `STRICT_RAILS_ONLY=true` → HTTP 410 Gone (flip-switch de migração)
- Opt-out LGPD detectado → email não enviado, `DeliveryResult.success=False`, `error="opted_out"`
- Canal indisponível → fallback para próximo canal se `fallback=True`
- Circuit breaker OPEN em API de sourcing → fallback para RAG interno

---

## Componentes críticos

### rails_client.py — Wrappers fail-safe

```python
# app/shared/rails_client.py
_client: WeDOTalentATSClient | None = None  # lazy singleton

async def rails_get(path: str, params: dict | None = None) -> dict:
    """GET request to Rails API. Returns {} on error."""
    try:
        resp = await _get_client().get(path, params=params)
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] GET %s failed: %s", path, exc)
        return {}

# Mesma estrutura para rails_patch() e rails_post()
```

**Regra de uso:** Código que precisa de dados CRUD (jobs, candidates, companies) deve usar `rails_get/patch/post` — **nunca** fazer chamadas HTTP manuais para o Rails. O singleton evita múltiplas instâncias de `WeDOTalentATSClient`.

### deprecation.py — Kill Switch de Migração

```python
# app/shared/rails_migration/deprecation.py

# Uso em router legado:
router = APIRouter(
    dependencies=[Depends(deprecated_in_favor_of_rails(
        resource="job-vacancies",
        rails_path="/v1/job_vacancies",
        sunset="2026-07-31",
    ))],
)

# O que acontece:
# 1. Sempre: log estruturado de deprecation
# 2. Sempre: headers RFC 8594: Deprecation: true, Sunset: ..., Link: <rails_url>
# 3. Se STRICT_RAILS_ONLY=true: HTTP 410 Gone (kill switch)
# 4. Caso contrário: passa para o handler legado Python
```

**Kill switch de produção:** setar `STRICT_RAILS_ONLY=true` em variável de ambiente → todos os endpoints Python marcados com `deprecated_in_favor_of_rails` retornam 410.

### ChannelType e fluxo de roteamento

```python
# app/shared/channels/channel_adapter.py

class ChannelType(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    IN_APP = "in_app"
    MS_TEAMS = "ms_teams"

class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"

@dataclass
class ChannelMessage:
    recipient_id: str
    recipient_name: str
    recipient_contact: str          # email ou phone E.164
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None
    template_id: str | None = None
    template_vars: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    company_id: str = ""            # OBRIGATÓRIO — do JWT, não do payload
    vacancy_id: str | None = None
```

### MultiChannelService — Singleton com 5 adapters

```python
# app/shared/channels/multi_channel_service.py
class MultiChannelService:
    _instance: Optional["MultiChannelService"] = None

    def _auto_register(self):
        default_adapters = [
            EmailChannelAdapter(),
            WhatsAppChannelAdapter(),
            SMSChannelAdapter(),
            InAppChannelAdapter(),
            MSTeamsChannelAdapter(),  # ativo apenas se TEAMS_WEBHOOK_URL configurado
        ]

    @classmethod
    def get_instance(cls) -> "MultiChannelService": ...  # singleton
```

### AI_GENERATED_FOOTER — F7 Obrigatório

```python
# app/shared/channels/adapters/email_adapter.py
AI_GENERATED_FOOTER = (
    "\n\n---\n"
    "*Esta mensagem foi gerada com assistência de Inteligência Artificial "
    "pela plataforma LIA (WeDOTalent).*"
)
```

**Regra:** todo email gerado por IA **deve** conter este footer. O `EmailChannelAdapter` o adiciona automaticamente via `_add_ai_footer()` se o marker "WeDOTalent" não estiver presente. Esse é o compliance F7 (LGPD + EU AI Act PL em tramitação).

### lia_messaging — Provider auto-detection

**Email:**
```python
# libs/messaging/lia_messaging/email.py
def _detect_provider() -> str:
    if os.environ.get("MAILGUN_API_KEY") and os.environ.get("MAILGUN_DOMAIN"):
        return "mailgun"  # primário
    if os.environ.get("RESEND_API_KEY"):
        return "resend"   # fallback
    return "none"         # dev sem email real

# Retorno padronizado:
# {"success": bool, "provider": str, "message_id": str|None, "error": str|None}
```

**WhatsApp:**
```python
# libs/messaging/lia_messaging/whatsapp.py
_META_API_BASE = "https://graph.facebook.com/v19.0"

def _detect_provider() -> str:
    return os.environ.get("WHATSAPP_PROVIDER", "meta").lower()  # "meta" | "twilio"

# Meta: suporta template_name + template_params (para mensagens pré-aprovadas pela Meta)
# Twilio: apenas mensagens de texto simples
# Formato do destinatário: E.164 (+5511999999999)
```

**Teams:**
```python
# libs/messaging/lia_messaging/teams.py
# Se TEAMS_WEBHOOK_URL não configurado → warning + return {"success": False, ...}
# Card: Adaptive Card com title, text (Markdown), color (default: "60BED1" WeDO cyan)
# facts: lista de {"name": ..., "value": ...} key-value pairs
```

### Sourcing APIs Catalog — 5 APIs com SLOs

| API | Propósito | Auth | Rate Limit | SLO P95 | Fallback |
|-----|-----------|------|-----------|---------|---------|
| Pearch AI | 190M+ perfis globais | PEARCH_API_KEY (Bearer) | 100 req/min | 3000ms | RAGPipelineService (busca interna) |
| Apify | Web scraping, salary data | APIFY_API_KEY (Bearer) | 60 req/min | 10000ms | static_salary_benchmark |
| Merge.dev (LinkedIn) | Sync candidatos via LinkedIn | MERGE_ACCESS_TOKEN (X-Account-Token) | 200 req/min | 2000ms | internal_talent_pool |
| Gupy ATS | Sync bidirecional vagas/candidatos | GUPY_API_KEY | 300 req/min | 1500ms | internal_ats_cache |
| Pandapé ATS | Sync bidirecional vagas/candidatos | PANDAPE_API_KEY | 200 req/min | 2000ms | internal_ats_cache |

**Mapeamento de subagentes:**
```yaml
sourcing_planner:    primary: [apify]                         # salary benchmark
sourcing_search:     primary: [pearch_ai, gupy, pandape]      # multi-source search
                     secondary: [linkedin_ats_sync]
sourcing_enrich:     primary: [pearch_ai, gupy]               # perfil enrichment
sourcing_engagement: primary: []                              # apenas banco interno
```

### NotificationService — 19 tipos de notificação

```python
# libs/messaging/lia_messaging/notification_service.py

class NotificationType(str, Enum):
    URGENT = "urgent"
    ACTION_REQUIRED = "action_required"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"

class ProactiveNotificationType(str, Enum):
    CANDIDATES_ADDED = "candidates_added"
    CALIBRATION_NEEDED = "calibration_needed"
    GOAL_REACHED = "goal_reached"
    EXPAND_TO_GLOBAL = "expand_to_global"
    LOW_ADHERENCE_APPLICANT = "low_adherence_applicant"
    MORNING_BRIEFING = "morning_briefing"
    AFTERNOON_SUMMARY = "afternoon_summary"
    APPROVAL_REQUEST = "approval_request"
    SCREENING_COMPLETED = "screening_completed"
    INTERVIEW_REMINDER = "interview_reminder"
    VACANCY_EXPIRING = "vacancy_expiring"
    NEW_APPLICATION = "new_application"
    TASK_ASSIGNED = "task_assigned"
    WEEKLY_DIGEST = "weekly_digest"
```

---

## Instruções para Claude Code / Cursor

### "Implementa Rails Client no v5"

```python
# 1. Criar app/shared/rails_client.py com os 3 wrappers fail-safe
# 2. Implementar WeDOTalentATSClient (ou adaptar para a URL do v5):
from lia_config.config import settings
RAILS_API_URL = settings.RAILS_API_URL  # ex: https://staging2.wedotalent.cc

# 3. Configurar .env:
RAILS_API_URL=https://staging2.wedotalent.cc
RAILS_JWT_SECRET_KEY=<shared-secret-rails>

# 4. NUNCA chamar Rails diretamente — sempre via rails_get/patch/post
# 5. Para endpoints Python legados (CRUD que migrou para Rails):
from app.shared.rails_migration.deprecation import deprecated_in_favor_of_rails
router = APIRouter(dependencies=[Depends(deprecated_in_favor_of_rails(
    resource="candidates", rails_path="/v1/candidates", sunset="2026-12-31"
))])
```

### "Implementa multi-channel messaging no v5"

**Passo 1 — Estrutura base**
```bash
# Copiar:
app/shared/channels/channel_adapter.py   ← ABC + dataclasses
app/shared/channels/channel_router.py    ← router com fallback
app/shared/channels/multi_channel_service.py ← singleton
app/shared/channels/adapters/            ← 5 adapters
libs/messaging/lia_messaging/{email,whatsapp,teams,notification_service}.py
```

**Passo 2 — Configurar providers**
```bash
# Email (Mailgun primário):
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=mg.wedotalent.com
# Email (Resend fallback):
RESEND_API_KEY=re_xxx

# WhatsApp (Meta primário):
WHATSAPP_PROVIDER=meta
WHATSAPP_PHONE_NUMBER_ID=1234567
WHATSAPP_API_TOKEN=EAAxxxxx

# Teams (opcional):
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Enable no settings:
ENABLE_TWILIO=false  # se usar Twilio para WhatsApp/SMS
ENABLE_MICROSOFT_GRAPH=true  # se usar Graph API
```

**Passo 3 — Uso correto**
```python
# SEMPRE usar company_id do JWT
service = MultiChannelService.get_instance()
msg = ChannelMessage(
    recipient_id=candidate_id,
    recipient_name=candidate_name,
    recipient_contact=candidate_email,
    body_text="...",
    company_id=current_user.company_id,  # JWT — NUNCA do payload
)
result = await service.send(msg, preferred_channels=[ChannelType.EMAIL])
```

**Passo 4 — AI Footer (obrigatório em produção)**
```python
# Garantir que EmailChannelAdapter._add_ai_footer() está ativo
# NUNCA remover o AI_GENERATED_FOOTER — é compliance F7
# O footer é adicionado automaticamente se "WeDOTalent" não está no body
```

### "Adiciona integração de sourcing nova"

1. Adicionar ao `sourcing_apis_catalog.yaml`:
   ```yaml
   nova_api:
     name: "Nome da API"
     purpose: "Propósito"
     base_url: "https://..."
     auth: "Bearer token (NOVA_API_KEY)"
     circuit_breaker: "NOVA_API_CIRCUIT"
     rate_limit: "N req/min"
     fallback: "descrição do fallback"
     slo:
       availability: 99.0
       latency_p95_ms: 2000
   ```
2. Adicionar `NOVA_API_KEY` em `IntegrationSettings` e `.env.example`
3. Adicionar `ENABLE_NOVA_API: bool = False` em `AppSettings` (opt-in)
4. Implementar circuit breaker com nome `NOVA_API_CIRCUIT` em `ALL_CIRCUITS` (ver R1)
5. Criar adapter se necessário (apenas para canais de mensagens)

### Setup em CLAUDE.md (snippet)

```markdown
## External Integrations (O3)
- Fonte: themes/operational/O3_EXTERNAL_INTEGRATIONS.md
- Rails Client: always use rails_get/patch/post (never direct HTTP to Rails)
- Multi-channel: MultiChannelService.get_instance().send() with company_id from JWT
- AI Footer: MANDATORY in all AI-generated emails (F7 compliance)
- Opt-out check: EmailChannelAdapter calls _is_opted_out() before send
- Rails migration: deprecated_in_favor_of_rails() for legacy Python CRUD endpoints
- STRICT_RAILS_ONLY=true: kill switch for all deprecated endpoints → 410 Gone
- Sourcing APIs: all have circuit breakers + fallbacks defined in catalog YAML
```

### Setup em Cursor rules (.cursor/rules/integrations.mdc)

```
---
description: External integrations rules
globs: ["*rails_client*", "*channel*", "*messaging*", "*lia_messaging*", "*whatsapp*"]
---
# Integration Rules
- rails_get/patch/post: always return {} on error (never raise)
- ChannelMessage.company_id: ALWAYS from JWT, never from payload
- AI_GENERATED_FOOTER: mandatory in all EmailChannelAdapter sends (F7)
- _is_opted_out(): must be called before sending email (LGPD)
- WhatsApp E.164 format: +5511999999999 (not 011999999999)
- WhatsApp template messages: Meta only (not Twilio)
- Teams: TEAMS_WEBHOOK_URL absent → warning only, no exception
- Sourcing APIs: check ENABLE_PEARCH_AI before calling (feature flag)
- deprecated_in_favor_of_rails(): use for all Python CRUD endpoints that moved to Rails
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexível porque |
|------|----------------|
| `WeDOTalentATSClient` URL base | `RAILS_API_URL` via settings — adaptar para URL do v5 |
| `sunset` dates em `deprecated_in_favor_of_rails()` | São datas de calendário, não contratos de API |
| Ordem de `preferred_channels` | Preferência de negócio, não arquitetural |
| `color` default em Teams messages | "60BED1" é cor WeDO; pode adaptar para branding do v5 |
| Rate limits e SLOs em `sourcing_apis_catalog.yaml` | Dependem de contrato com o provider; atualizar conforme plano |
| Número de `ProactiveNotificationType` | Pode adicionar novos tipos; não remover existentes (usados em banco) |

### NÃO pode adaptar (LGPD ou arquitetural)

| Item | Por quê é imutável |
|------|--------------------|
| `AI_GENERATED_FOOTER` em emails | Compliance F7 (LGPD + EU AI Act em tramitação) — remoção é violação regulatória |
| `_is_opted_out()` antes de enviar email | LGPD Art. 7 e 18 — enviar email a quem fez opt-out é violação |
| `company_id` no `ChannelMessage` do JWT (nunca payload) | Multi-tenancy — exploração cross-tenant via payload |
| `rails_client.py` fail-safe (return `{}`, nunca lança) | Reliability — erro na comunicação com Rails não deve derrubar o request do LIA |
| Circuit breakers para todas APIs de sourcing externo | Evita cascata de falhas quando API externa está down |
| `STRICT_RAILS_ONLY` como kill switch (não remoção direta) | Permite rollback seguro — remoção direta sem kill switch cria indisponibilidade não controlada |
| Fallbacks definidos no `sourcing_apis_catalog.yaml` | SLA agreement — sem fallback, falha de API externa para todo o fluxo de sourcing |

---

## Checklist de completude

### P0 — Críticos (bloqueiam deploy)

- [ ] (P0) `AI_GENERATED_FOOTER` presente em `email_adapter.py` e adicionado a todos os emails gerados por IA
- [ ] (P0) `_is_opted_out()` chamado em `EmailChannelAdapter.send()` antes do envio
- [ ] (P0) `company_id` no `ChannelMessage` sempre do JWT — nunca do body da requisição
- [ ] (P0) `rails_client.py` com fail-safe: todas as funções retornam `{}` em exceção
- [ ] (P0) `STRICT_RAILS_ONLY` funcional como kill switch (410 Gone quando True)
- [ ] (P0) Circuit breakers configurados para todas as sourcing APIs (R1)

### P1 — Importantes

- [ ] (P1) `MultiChannelService.get_instance()` singleton (não instanciar diretamente)
- [ ] (P1) `ChannelRouter.route()` com `fallback=True` como default — tenta próximo canal se primeiro falhar
- [ ] (P1) 5 adapters auto-registrados em `MultiChannelService._auto_register()`
- [ ] (P1) Mailgun primário + Resend fallback configurados (MAILGUN_API_KEY + MAILGUN_DOMAIN)
- [ ] (P1) WhatsApp provider detectado por env var `WHATSAPP_PROVIDER` (meta | twilio)
- [ ] (P1) Teams: `TEAMS_WEBHOOK_URL` ausente → warning, não exceção
- [ ] (P1) `sourcing_apis_catalog.yaml` com fallbacks para todas as 5 APIs
- [ ] (P1) `deprecated_in_favor_of_rails()` aplicado em todos os endpoints CRUD Python que migraram para Rails
- [ ] (P1) RAILS_API_URL configurado em `.env`

### P2 — Qualidade

- [ ] (P2) `DeliveryResult.status` propagado ao banco para rastreamento de entregas
- [ ] (P2) `ProactiveNotificationType` completo com 14 tipos
- [ ] (P2) `WHATSAPP_PROVIDER=meta` como default documentado (não Twilio)
- [ ] (P2) Formatação E.164 validada antes de envio WhatsApp
- [ ] (P2) `Deprecation`/`Sunset`/`Link` headers nos endpoints legados
- [ ] (P2) Rate limits do `sourcing_apis_catalog.yaml` respeitados (throttling por API)

---

## Gotchas e erros comuns

### 1. Chamada HTTP direta para Rails (bypass do rails_client)

```python
# ❌ ERRADO — sem fail-safe, sem singleton, sem logging padronizado
import httpx
resp = await httpx.get(f"{RAILS_URL}/v1/candidates/42")
data = resp.json()

# ✅ CORRETO
from app.shared.rails_client import rails_get
data = await rails_get("/v1/candidates/42")  # retorna {} em caso de erro
```

### 2. Enviar email sem verificar opt-out LGPD

```python
# ❌ ERRADO — envia para candidato que fez opt-out
await send_email(to=candidate_email, ...)

# ✅ CORRETO — via EmailChannelAdapter que chama _is_opted_out()
result = await email_adapter.send(ChannelMessage(
    recipient_contact=candidate_email,
    company_id=current_user.company_id,  # necessário para verificar opt-out
    ...
))
if not result.success and result.error == "opted_out":
    logger.info("Candidate opted out of email — skipping")
```

### 3. Email sem AI footer (F7 bypass)

```python
# ❌ ERRADO — footer não adicionado, viola F7
msg = ChannelMessage(body_text="Olá candidato, ...")
# Apenas envia sem footer

# ✅ CORRETO — EmailChannelAdapter adiciona automaticamente
# NÃO precisa adicionar manualmente — o adapter garante o footer
# GARANTA que o adapter está sendo usado, não lia_messaging.email diretamente
# Se usar lia_messaging.email.send_email() diretamente, adicionar footer manualmente
```

### 4. WhatsApp sem formato E.164

```python
# ❌ ERRADO — formato brasileiro sem código internacional
to = "11999999999"

# ✅ CORRETO — E.164 obrigatório
to = "+5511999999999"
```

### 5. MultiChannelService sem company_id no ChannelMessage

```python
# ❌ ERRADO — company_id vazio causa erro no opt-out check
msg = ChannelMessage(
    recipient_id=candidate_id,
    body_text="...",
    # company_id ausente!
)

# ✅ CORRETO
msg = ChannelMessage(
    recipient_id=candidate_id,
    body_text="...",
    company_id=current_user.company_id,  # SEMPRE do JWT
)
```

### 6. Remover deprecated_in_favor_of_rails antes de migração completa

```python
# ❌ ERRADO — remover sem confirmar que Rails implementou o endpoint
# Causa: clientes que usavam /api/v1/jobs/{id} ficam sem resposta

# ✅ CORRETO — sequência de migração:
# 1. Adicionar deprecated_in_favor_of_rails() ao endpoint Python
# 2. Validar que Rails tem o endpoint equivalente
# 3. Monitorar logs de deprecation por 2 semanas
# 4. Setar STRICT_RAILS_ONLY=true em staging
# 5. Se OK → setar STRICT_RAILS_ONLY=true em produção
# 6. Após grace period (Sunset date) → remover endpoint Python
```

### 7. Teams sem TEAMS_WEBHOOK_URL — exceção esperada

```python
# ❌ ERRADO — assumir que Teams está sempre disponível
await send_teams_message("Alerta", "candidato aprovado")
# Se TEAMS_WEBHOOK_URL não configurado → return {"success": False}
# NÃO levanta exceção (ver teams.py)

# ✅ CORRETO — verificar resultado
result = await send_teams_message("Alerta", "candidato aprovado")
if not result["success"]:
    logger.info("Teams not configured or failed — using fallback")
```

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Rails client fail-safe | `tests/unit/test_rails_client.py` | `WeDOTalentATSClient.get()` lança exceção → `rails_get()` retorna `{}` |
| Email opt-out LGPD | `tests/unit/test_email_adapter.py` | Candidato com opt-out → `DeliveryResult.success=False`, `error="opted_out"` |
| AI footer obrigatório | `tests/unit/test_email_adapter.py` | Todo email via adapter contém "WeDOTalent" no body |
| Channel fallback | `tests/unit/test_channel_router.py` | Email FAILED → router tenta WhatsApp automaticamente |
| Strict rails mode | `tests/unit/test_deprecation.py` | `STRICT_RAILS_ONLY=true` → endpoint retorna 410 |
| Deprecation headers | `tests/unit/test_deprecation.py` | Sem STRICT_RAILS_ONLY → headers `Deprecation: true` + `Sunset` presentes |
| WhatsApp E.164 format | `tests/unit/test_whatsapp_adapter.py` | Número sem + → erro ou normalização |
| Teams sem webhook | `tests/unit/test_teams.py` | `TEAMS_WEBHOOK_URL` não configurado → `success=False`, sem exceção |
| company_id em ChannelMessage | `tests/security/test_channel_tenant_isolation.py` | company_id do payload ignorado em favor do JWT |
| Sourcing API circuit breaker | `tests/integration/test_sourcing_integration.py` | Pearch API down → fallback para RAGPipelineService |

---

## Referências

| Recurso | Localização |
|---------|------------|
| MIGRATION_PLAN (Rails CRUD migration) | `/home/runner/workspace/docs/MIGRATION_PLAN.md` |
| R1 Circuit Breakers (sourcing API circuit breakers) | `themes/resilience/R1_CIRCUIT_BREAKERS.md` |
| R3 Messaging & Events (broker vs. multi-channel) | `themes/resilience/R3_MESSAGING_AND_EVENTS.md` |
| C2 LGPD PII (opt-out + AI footer) | `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md` |
| C4 LGPD Art.20 (candidate portal via Rails) | `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md` |
| I8 Auth (RAILS_JWT_SECRET_KEY) | `themes/infrastructure/I8_AUTH_AND_AUTHORIZATION.md` |
| O2 Config (ENABLE_PEARCH_AI, ENABLE_TWILIO, etc.) | `themes/operational/O2_CONFIGURATION_AND_FEATURE_FLAGS.md` |
| docs/integrations/apis/ | `/home/runner/workspace/lia-agent-system/docs/integrations/` |
