# Theme: Messaging & Events — Resilience Layer

## O que é este tema

Messaging & Events é a camada de **comunicação assíncrona** da LIA: abstração de broker (Redis/RabbitMQ/Pub/Sub), publicação de eventos inter-sistema (FastAPI → Rails), dispatcher de agentes para filas Celery, e envio de mensagens externas (email/WhatsApp/Teams).

**4 sub-sistemas:**
1. **BrokerInterface** — abstração de broker com 3 backends, trocável por env var `BROKER_BACKEND`
2. **UnifiedEventPublisher + PlatformEvents + RailsEventPublisher** — publicação de eventos inter-API com retry, DLQ, audit
3. **DomainDispatcher + MessageSchemas** — despacho de mensagens de chat para filas Celery de agentes
4. **lia_messaging** — envio externo: email (Mailgun/Resend), WhatsApp (Meta/Twilio), Teams (Webhook)

**Boundary com temas irmãos:**
- **R4 Background Jobs**: DomainDispatcher enfileira tasks que os workers Celery (R4) processam
- **I6 API Layer/WebSocket**: WebSocket endpoint chama `DomainDispatcher.dispatch()` para domínios assíncronos (sourcing, screening)
- **R1 Circuit Breakers**: `MAILGUN_CIRCUIT`, `RESEND_CIRCUIT`, `TWILIO_VOICE_CIRCUIT` protegem envios externos

---

## Arquivos conectados (11 total)

### Camada Código — app/shared/messaging (7 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `broker_interface.py` | `app/shared/messaging/broker_interface.py` | BrokerInterface ABC + 3 backends + factory `get_broker()` + singleton |
| `unified_event_publisher.py` | `app/shared/messaging/unified_event_publisher.py` | Single entry point, retry exponencial (1s/2s/4s), fail-safe |
| `platform_events.py` | `app/shared/messaging/platform_events.py` | PlatformEvent Pydantic + 5 eventos específicos + publisher async |
| `rails_event_publisher.py` | `app/shared/messaging/rails_event_publisher.py` | `publish_rails_event()` via EVENT_REGISTRY + BaseRailsEvent |
| `rails_event_schemas.py` | `app/shared/messaging/rails_event_schemas.py` | RAILS_EVENT_EXCHANGE + BaseRailsEvent dataclass + EVENT_REGISTRY |
| `message_schemas.py` | `app/shared/messaging/message_schemas.py` | AgentChatMessage + AgentResponseMessage (Pydantic) |
| `dispatchers.py` | `app/shared/messaging/dispatchers.py` | DomainDispatcher + `_DOMAIN_QUEUE_MAP` (13 domínios → 4 filas) |
| `celery_config.py` | `app/shared/messaging/celery_config.py` | DOMAIN_QUEUES dict — prioridades por domínio |
| `rabbitmq_producer.py` | `app/shared/messaging/rabbitmq_producer.py` | `publish_to_exchange()` usado por PlatformEvents + RailsEventPublisher |
| `rabbitmq_consumer.py` | `app/shared/messaging/rabbitmq_consumer.py` | Consumer para filas de resposta de agentes |

### Camada Código — libs/messaging/lia_messaging (4 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `email.py` | `libs/messaging/lia_messaging/email.py` | `send_email()` provider-agnostic (Mailgun > Resend via env) |
| `whatsapp.py` | `libs/messaging/lia_messaging/whatsapp.py` | `send_whatsapp_message()` Meta Graph API ou Twilio |
| `teams.py` | `libs/messaging/lia_messaging/teams.py` | `send_teams_message()` via Incoming Webhook + Adaptive Card |
| `notification_service.py` | `libs/messaging/lia_messaging/notification_service.py` | NotificationService multi-canal + 14 ProactiveNotificationTypes |

### Integration points

- `app/api/v1/platform_event_handlers.py` → handlers de eventos recebidos via RabbitMQ
- `app/shared/resilience/circuit_breaker.py` → `_notify_circuit_open()` usa `notification_service.send_system_alert(channels=["bell","teams"])`
- `app/shared/websocket/ws_manager.py` → chama `DomainDispatcher.dispatch()` para domínios async
- Celery workers em `app/jobs/celery_tasks.py` → consomem das 4 filas via `DOMAIN_QUEUES`
- Rails (Sneakers worker `LiaEventsWorker`) → consome do `RAILS_EVENT_EXCHANGE = "lia_rails_events"`

---

## Lógica IN → OUT

### 1. BrokerInterface — abstração de broker

**3 backends, trocável por env var:**

| Env var `BROKER_BACKEND` | Classe | Mecanismo |
|--------------------------|--------|-----------|
| `redis` (default) | `RedisBroker` | `LPUSH broker:{topic}` (publish) / `BRPOP broker:{topic}` timeout=1s (consume) |
| `rabbitmq` | `RabbitMQBroker` | `aio_pika`, delivery_mode=PERSISTENT, durable queue |
| `pubsub` | `PubSubBroker` | **Stub GCP** — todos métodos levantam `NotImplementedError` (migração futura) |

**Factory:**
```python
def get_broker(backend: str | None = None) -> BrokerInterface:
    resolved = (backend or os.getenv("BROKER_BACKEND", "redis")).lower()
    if resolved == "redis":    return RedisBroker()
    if resolved == "rabbitmq": return RabbitMQBroker()
    if resolved == "pubsub":   return PubSubBroker()
    # fallback: RedisBroker (log warning)
```

**Singleton:** `get_default_broker()` — lazy init, global `_broker_instance`. Thread-safe via GIL.

**Publish response:**
```python
{"message_id": str}  # correlation_id do payload ou uuid4()
```

**RedisBroker key pattern:** `broker:{topic}` — prefixo fixo para evitar colisões com outras chaves Redis.

**RabbitMQBroker:** usa `connect_robust()` — reconnect automático. Delivery mode `PERSISTENT` (sobrevive restart do broker).

**PubSubBroker:** health_check() retorna `{"status": "stub", "note": "..."}` em vez de NotImplementedError — permite monitoring sem crash.

### 2. UnifiedEventPublisher — publicação de eventos para Rails

```python
unified_event_publisher.publish(
    event_type="screening.completed",
    payload={"apply_id": 42, "score": 8.5},
    company_id="...",
    max_retries=3,        # default
    timeout_seconds=10.0, # default
) → bool  # True = publicado, False = todos tentativas falharam (fail-safe)
```

**Fluxo interno:**
1. Busca `event_version = EVENT_VERSIONS.get(event_type, "1.0")`
2. Monta envelope: `{event_type, event_version, company_id, payload}`
3. Loop de retry com exponential backoff: `sleep(2**attempt)` = 1s, 2s, 4s
4. Cada attempt: `asyncio.wait_for(_publish_once(envelope), timeout=10.0)`
5. `_publish_once()` delega para `RailsAdapter.publish_event()`
6. Se todos os attempts falharem → `logger.warning + return False` (never raise)

**Módulo singleton:** `unified_event_publisher = UnifiedEventPublisher()` no final do arquivo.

### 3. PlatformEvents — eventos inter-API

**Exchange:** `"platform.events"` (RabbitMQ topic exchange)
**Routing key pattern:** `"{dominio}.{entidade}.{acao}"` — ex: `"vagas.job.published"`, `"funil.candidate.moved"`

**PlatformEvent schema (Pydantic):**
```python
class PlatformEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str      # routing key
    occurred_at: datetime  # UTC, auto-set
    company_id: str       # OBRIGATÓRIO — sempre presente
    payload: dict[str, Any]
    source_api: str       # "api-vagas" | "api-funil" | "api-onboarding"
    version: str = "1.0"
```

**5 eventos específicos:**

| Classe | event_type | source_api |
|--------|-----------|-----------|
| `JobPublishedEvent` | `vagas.job.published` | `api-vagas` |
| `JobClosedEvent` | `vagas.job.closed` | `api-vagas` |
| `CandidateMovedEvent` | `funil.candidate.moved` | `api-funil` |
| `CompanyConfiguredEvent` | `onboarding.company.configured` | `api-onboarding` |
| `ScreeningCompletedEvent` | `screening.wsi.completed` | `api-funil` |

`publish_platform_event(event)`: fail-safe — indisponibilidade do RabbitMQ não impede fluxo principal. Loga erro para análise posterior.

### 4. RailsEventPublisher — eventos FastAPI → Rails

**Exchange:** `RAILS_EVENT_EXCHANGE = "lia_rails_events"` (direct exchange)
**Consumer Rails:** Sneakers worker `LiaEventsWorker` (ats-api Rails)

```python
async def publish_rails_event(event_type: str, payload: dict, company_id: str):
    event_cls = EVENT_REGISTRY.get(event_type)
    if event_cls is None:
        # Fallback: publica raw sem schema validation
        await publish_rails_event_raw(event_type, version, payload, company_id)
        return
    event = event_cls(company_id=company_id, **payload)
    await publish_to_exchange(RAILS_EVENT_EXCHANGE, routing_key=event_type, message=event.to_dict())
```

**BaseRailsEvent (dataclass):**
```python
@dataclass
class BaseRailsEvent:
    event_type: str
    company_id: str
    timestamp: str  # UTC ISO, auto-set
    source: str = "lia-agent-system"
    version: str = "1.0"
    def to_json() → str  # json.dumps(asdict(self))
    def to_dict() → dict
```

**Eventos Rails registrados (EVENT_REGISTRY):**
- `ScreeningCompletedEvent`: `apply_id, candidate_id, job_id, score(0-10), recommendation("advance"/"hold"/"decline"), bias_flags[]`
- `InterviewScheduledEvent`: `apply_id, candidate_id` + scheduling metadata

### 5. DomainDispatcher + MessageSchemas

**Fluxo de chat para agente assíncrono:**
```
WS endpoint → DomainDispatcher.dispatch(chat_msg) → RabbitMQ → Celery worker → agent.process()
                                                  ↑
                                          cria fila de resposta
```

**_DOMAIN_QUEUE_MAP (13 mapeamentos → routing keys RabbitMQ):**

> ⚠️ **Importante — dois sistemas paralelos:** `_DOMAIN_QUEUE_MAP` em `dispatchers.py` mapeia domínios para **routing keys RabbitMQ** (formato `agent.*`). A função `celery_config.get_domain_config()` (importada na linha 19) provê o **nome de fila Celery** e a **prioridade** para cada domínio. Os dois sistemas rodam em paralelo: o dispatcher usa o map para roteamento RabbitMQ; a prioridade Celery vem do `get_domain_config()`.

| Domínio | Routing Key RabbitMQ (`_DOMAIN_QUEUE_MAP`) | Fila Celery (`get_domain_config()`) | Prioridade |
|---------|:----------------------------------------:|:-----------------------------------:|:---------:|
| `sourcing` | `agent.sourcing` | `sourcing_high` | 8 |
| `cv_screening`, `wsi_assessment` | `agent.screening` | `evaluation_normal` | 5 |
| `pipeline`, `pipeline_transition` | `agent.pipeline` | `evaluation_normal` | 5 |
| `automation` | `agent.automation` | `vagas_normal` | 5 |
| `wizard`, `job_management` | `agent.wizard` | `vagas_normal` | 4 |
| `kanban`, `talent`, `recruiter_assistant` | `agent.kanban` | `vagas_normal` | 4 |
| `policy`, `hiring_policy` | `agent.policy` | `onboarding_low` | 3 |

**Default routing key:** `"agent.wizard"` para domínios não mapeados.

**AgentChatMessage (Pydantic):**
```python
session_id: str
user_id: str
company_id: str         # multi-tenant — sempre do JWT
domain: str
message: str
context: dict           # domain-specific state
conversation_history: list[dict]  # max últimas 10 mensagens
priority: int = 5       # 1-10, maior = mais urgente
reply_to: str = ""      # fila de resposta para esta session
correlation_id: str = ""  # UUID request/response
```

**AgentResponseMessage (Pydantic):**
```python
session_id: str
content: str = ""
confidence: float = 0.7   # 0.0-1.0
actions: list[dict] = []
navigation: dict | None = None
```

### 6. lia_messaging — envio externo

#### Email — `send_email()`

Auto-detecção de provider (priority): Mailgun > Resend > none.

```python
# Detecção: MAILGUN_API_KEY + MAILGUN_DOMAIN → mailgun
#           RESEND_API_KEY → resend
#           (nenhum) → none (não envia, retorna error)

send_email(
    to="candidate@email.com",
    subject="Feedback da entrevista",
    body="...",
    html_body="...",        # opcional
    from_email=None,        # default: DEFAULT_FROM_EMAIL env ou "noreply@wedotalent.com"
    provider="mailgun",     # override opcional
) → {"success": bool, "provider": str, "message_id": str|None, "error": str|None}
```

Circuit protegido por: `MAILGUN_CIRCUIT` (failover → `RESEND_CIRCUIT`) — ver R1.

#### WhatsApp — `send_whatsapp_message()`

```python
# Providers: meta (default) ou twilio
# WHATSAPP_PROVIDER env var ou override por parâmetro

send_whatsapp_message(
    to="+5511999999999",    # E.164 format obrigatório
    message="Olá, sua entrevista...",
    template_name="entrevista_confirmacao",  # Meta templates only
    template_params=["Joao", "15/05"],
) → {"success": bool, "provider": str, "message_id": str|None, "error": str|None}
```

**Meta:** `POST https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages`
**Twilio:** usar `TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_WHATSAPP_NUMBER`

#### Teams — `send_teams_message()`

```python
send_teams_message(
    title="⚡ Circuit Breaker ABERTO: anthropic",
    text="Descrição do problema...",
    webhook_url=None,       # default: TEAMS_WEBHOOK_URL env var
    color="0076D7",         # default: "60BED1" (WeDO cyan)
    facts=[{"name": "Service", "value": "anthropic"}, ...],
) → {"success": bool, "status_code": int|None, "error": str|None}
```

Se `TEAMS_WEBHOOK_URL` não configurada → retorna `{"success": False, "error": "No Teams webhook URL configured"}` sem exception.

#### NotificationService

```python
# Tipos de notificação:
class NotificationType: URGENT, ACTION_REQUIRED, INFO, SUCCESS, WARNING

# 14 tipos proativos:
class ProactiveNotificationType:
    CANDIDATES_ADDED, CALIBRATION_NEEDED, GOAL_REACHED, EXPAND_TO_GLOBAL,
    LOW_ADHERENCE_APPLICANT, MORNING_BRIEFING, AFTERNOON_SUMMARY, APPROVAL_REQUEST,
    SCREENING_COMPLETED, INTERVIEW_REMINDER, VACANCY_EXPIRING, NEW_APPLICATION,
    TASK_ASSIGNED, WEEKLY_DIGEST

# 7 canais:
class NotificationChannel: CHAT, BELL, TEAMS, EMAIL, WHATSAPP, IN_APP, PUSH
```

Modelo `Notification` na tabela `notifications` (PostgreSQL).

`send_system_alert(db, title, message, severity, channels, metadata)` — usado por `_notify_circuit_open()` com `channels=["bell", "teams"]`.

---

## Instruções para Claude Code / Cursor

### "Implementa Messaging no v5"

```
1. Criar app/shared/messaging/__init__.py

2. Criar app/shared/messaging/broker_interface.py
   - BrokerInterface ABC (3 métodos abstract)
   - RedisBroker: LPUSH/BRPOP, key "broker:{topic}", correlation_id ou uuid4()
   - RabbitMQBroker: aio-pika, connect_robust, delivery_mode=PERSISTENT
   - PubSubBroker: stub — NotImplementedError com mensagem clara + referência docs
   - get_broker() factory: BROKER_BACKEND env var (default "redis")
   - get_default_broker() singleton lazy

3. Criar app/shared/messaging/platform_events.py
   - PlatformEvent Pydantic + 5 subclasses
   - PLATFORM_EVENTS_EXCHANGE = "platform.events"
   - publish_platform_event() fail-safe

4. Criar app/shared/messaging/rails_event_schemas.py
   - BaseRailsEvent dataclass + to_dict() + to_json()
   - RAILS_EVENT_EXCHANGE = "lia_rails_events"
   - EVENT_REGISTRY dict + EVENT_VERSIONS dict

5. Criar app/shared/messaging/rails_event_publisher.py
   - publish_rails_event() com EVENT_REGISTRY fallback
   - publish_rails_event_raw() para testing

6. Criar app/shared/messaging/unified_event_publisher.py
   - UnifiedEventPublisher: publish() com max_retries=3, timeout=10s
   - Exponential backoff: sleep(2**attempt)
   - Fail-safe: returns False, never raises
   - Module-level singleton: unified_event_publisher = UnifiedEventPublisher()

7. Criar app/shared/messaging/message_schemas.py
   - AgentChatMessage (company_id obrigatório, priority 1-10)
   - AgentResponseMessage (confidence 0.0-1.0)

8. Criar app/shared/messaging/dispatchers.py
   - DomainDispatcher com _DOMAIN_QUEUE_MAP (13 mapeamentos)
   - 4 filas: sourcing_high(8), evaluation_normal(5), vagas_normal(4-5), onboarding_low(3)

9. Criar libs/messaging/lia_messaging/{email,whatsapp,teams,notification_service}.py
   - Copiar provider-detection logic (_detect_provider()) para email e whatsapp
   - Teams: Adaptive Card via httpx, timeout=10s
   - NotificationService: 7 canais + 14 ProactiveNotificationTypes + tabela notifications
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Messaging & Events — R3
- BrokerInterface: trocável via BROKER_BACKEND (redis/rabbitmq/pubsub). Default: redis
- UnifiedEventPublisher: único entry point para eventos Rails — retry automático, fail-safe
- PlatformEvents exchange: "platform.events" (topic). RailsEvents exchange: "lia_rails_events" (direct)
- DomainDispatcher: sourcing→sourcing_high(8), pipeline/screening→evaluation(5), wizard/kanban→vagas(4-5), policy→onboarding(3)
- AgentChatMessage: company_id SEMPRE do JWT, nunca do payload
- email.py: Mailgun primário (MAILGUN_API_KEY+DOMAIN), Resend fallback (RESEND_API_KEY)
- whatsapp.py: Meta primário (WHATSAPP_PROVIDER=meta), Twilio alternativo
- Teams: TEAMS_WEBHOOK_URL env var — falha silenciosa se não configurado
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|--------------|
| `BROKER_BACKEND` default | Trocar para rabbitmq se v5 é on-prem sem Redis |
| Exchange names | Renomear `platform.events` / `lia_rails_events` |
| `_DOMAIN_QUEUE_MAP` | Adicionar novos domínios do v5 |
| Prioridades em `DOMAIN_QUEUES` | Ajustar SLA por domínio |
| `NotificationType` / `ProactiveNotificationType` | Adicionar tipos do v5 |
| `DEFAULT_FROM_EMAIL` | Adaptar domínio de email |
| Teams card color "60BED1" | Adaptar ao brand do v5 |
| `unified_event_publisher.max_retries` | Ajustar para SLA do Rails |

### NÃO pode adaptar (contrato ou multi-tenancy)

| Item | Razão |
|------|-------|
| `company_id` em `AgentChatMessage` | Multi-tenancy — worker Celery usa para particionamento; jamais do payload |
| `company_id` em `PlatformEvent` | Mesmo: eventos sem company_id cruzam tenants |
| `PubSubBroker` levanta `NotImplementedError` | Segurança — stub que parece funcionar mas silenciosamente descarta mensagens é pior que falha clara |
| `correlation_id` em mensagens broker | Rastreabilidade de auditoria — remover quebra tracing E2E |
| Fail-safe em `publish_platform_event()` e `UnifiedEventPublisher.publish()` | RabbitMQ down não pode quebrar o fluxo de triagem/screening |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `company_id` em todos os `AgentChatMessage` e `PlatformEvent` — sem mensagens cross-tenant
- [ ] **(P0)** `get_broker()` retorna `RedisBroker` por default se `BROKER_BACKEND` não definido
- [ ] **(P0)** `unified_event_publisher` (singleton) disponível como importação direta
- [ ] **(P1)** `DomainDispatcher._DOMAIN_QUEUE_MAP` cobre todos os domínios de agentes do v5
- [ ] **(P1)** `publish_platform_event()` fail-safe — loga erro mas não levanta exception
- [ ] **(P1)** `ScreeningCompletedEvent` inclui `bias_flags[]` — integração C1 Fairness
- [ ] **(P1)** `EMAIL_CIRCUIT` + `RESEND_CIRCUIT` wired em `send_email()` (ver R1)
- [ ] **(P1)** `TEAMS_WEBHOOK_URL` documentado em `.env.example`
- [ ] **(P2)** `PubSubBroker.health_check()` retorna `status: "stub"` sem exception
- [ ] **(P2)** `AgentChatMessage.conversation_history` limitado a 10 mensagens (context window)
- [ ] **(P2)** `rails_event_schemas.EVENT_REGISTRY` contém todos os event_types em uso
- [ ] **(P2)** `NotificationService` tabela `notifications` migração aplicada

---

## Gotchas e erros comuns

### 1. `company_id` de payload em vez de JWT em `AgentChatMessage`

**Problema:** Se o WS endpoint aceitar `company_id` do payload WebSocket e não do JWT, um cliente pode despachar mensagens para a fila de outro tenant.

**Correto:** `company_id` sempre do `request.state.company_id` (JWT decodificado) no momento de criar `AgentChatMessage`.

### 2. `PubSubBroker` parece funcionar mas faz nada

**Problema:** `health_check()` retorna `{"status": "stub"}` (não "unhealthy"), então um health check pode passar com PubSubBroker. Mas `publish()` levantaria `NotImplementedError` em produção.

**Correto:** Em produção, nunca usar `BROKER_BACKEND=pubsub` até implementar a integração real.

### 3. `get_default_broker()` singleton não é thread-safe em multiprocessing

**Problema:** O singleton usa `global _broker_instance` (thread-safe via GIL em CPython), mas em multiprocessing (Celery `fork`) cada worker tem sua própria cópia. Não é problema de correctness, mas cada worker cria sua própria conexão Redis.

**Comportamento esperado:** cada Celery worker tem seu próprio broker instance — correto para isolamento de conexão.

### 4. `DomainDispatcher` para domínios síncronos (wizard) não usa fila

**Problema:** `_DOMAIN_QUEUE_MAP` lista `wizard` → `vagas_normal`, mas o dispatcher despacha APENAS para domínios **assíncronos** em produção. Domínios síncronos (wizard, kanban) são processados diretamente no WebSocket handler sem passar pelo dispatcher.

**Correto:** `DomainDispatcher.dispatch()` checa `await is_available()` — se RabbitMQ indisponível, cai para processamento síncrono direto.

### 5. `send_teams_message()` sem `TEAMS_WEBHOOK_URL` → silêncio

**Problema:** Se `TEAMS_WEBHOOK_URL` não está configurado, a função retorna `{"success": False}` sem erro visível. Em produção, alertas de circuit breaker seriam silenciosamente descartados.

**Correto:** Adicionar `TEAMS_WEBHOOK_URL` ao `.env.example` com comentário "obrigatório para alertas operacionais". Monitorar `success=False` em observabilidade.

### 6. `ScreeningCompletedEvent` sem `bias_flags` quebra auditoria de fairness

**Problema:** Se `bias_flags=[]` sempre (nunca populado), o Rails não tem como detectar se o resultado veio com flags de viés — perdendo o trail de auditoria EU AI Act Art. 13.

**Correto:** `bias_flags` deve ser populado com flags do FairnessGuard (C1) antes de publicar o evento.

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| `test_redis_broker_publish_consume` | `tests/unit/test_broker.py` | LPUSH + BRPOP no Redis de test |
| `test_pubsub_broker_raises_not_implemented` | `tests/unit/test_broker.py` | `publish()` levanta `NotImplementedError` |
| `test_broker_factory_default_redis` | `tests/unit/test_broker.py` | Sem env var → retorna RedisBroker |
| `test_broker_factory_rabbitmq` | `tests/unit/test_broker.py` | BROKER_BACKEND=rabbitmq → RabbitMQBroker |
| `test_unified_publisher_retry` | `tests/unit/test_unified_event_publisher.py` | 3 falhas → return False, sem exception |
| `test_unified_publisher_backoff` | `tests/unit/test_unified_event_publisher.py` | Delays = 1s, 2s, 4s entre attempts |
| `test_platform_event_failsafe` | `tests/unit/test_platform_events.py` | RabbitMQ down → retorna False, não levanta |
| `test_rails_event_registry_fallback` | `tests/unit/test_rails_event_publisher.py` | event_type desconhecido → raw publish |
| `test_domain_dispatcher_queue_mapping` | `tests/unit/test_dispatchers.py` | sourcing → sourcing_high; policy → onboarding_low |
| `test_agent_chat_message_company_id` | `tests/unit/test_message_schemas.py` | company_id obrigatório |
| `test_send_email_mailgun_priority` | `tests/unit/test_email.py` | MAILGUN_API_KEY+DOMAIN → provider="mailgun" |
| `test_send_email_resend_fallback` | `tests/unit/test_email.py` | Sem Mailgun, com RESEND_API_KEY → provider="resend" |
| `test_teams_no_webhook_silent` | `tests/unit/test_teams.py` | Sem TEAMS_WEBHOOK_URL → success=False, sem raise |
| `test_whatsapp_meta_provider` | `tests/unit/test_whatsapp.py` | WHATSAPP_PROVIDER=meta → Meta Graph API endpoint |

---

## Referências

### Código (SSoT)
- `app/shared/messaging/broker_interface.py` — BrokerInterface + 3 backends + factory
- `app/shared/messaging/unified_event_publisher.py` — retry + fail-safe + singleton
- `app/shared/messaging/platform_events.py` — PlatformEvent + 5 eventos
- `app/shared/messaging/rails_event_publisher.py` + `rails_event_schemas.py`
- `app/shared/messaging/dispatchers.py` — DomainDispatcher + queue mapping
- `app/shared/messaging/message_schemas.py` — AgentChatMessage + AgentResponseMessage
- `app/shared/messaging/celery_config.py` — DOMAIN_QUEUES com prioridades
- `libs/messaging/lia_messaging/{email,whatsapp,teams,notification_service}.py`

### Bundles e Guides
- Reconstruction Guide `RESILIENCE_LEARNING` Parte C — BrokerInterface (overview)
- Thematic Doc R4 (`R4_BACKGROUND_JOBS_AND_SCHEDULERS.md`) — Celery workers que consomem das filas do DomainDispatcher
- Thematic Doc R1 (`R1_CIRCUIT_BREAKERS.md`) — MAILGUN_CIRCUIT/RESEND_CIRCUIT protegem send_email()
- Thematic Doc I6 (`I6_API_LAYER_AND_WEBSOCKET.md`) — WebSocket usa DomainDispatcher para async domains

### Handoffs
- `DEVELOPER_HANDOFF.md` — referencia RabbitMQ como messaging backbone para domínios assíncronos
