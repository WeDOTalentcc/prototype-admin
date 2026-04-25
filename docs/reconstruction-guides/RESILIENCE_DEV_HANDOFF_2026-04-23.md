# Resilience + Learning — Handoff para o time de dev (2026-04-23)

> Replicação no produto novo (IA repo separada) da camada de resiliência e
> aprendizado da LIA: `CircuitBreaker` (3 estados, 20 circuitos ativos),
> `LearningLoopService`, `BrokerInterface` (Redis/RabbitMQ/PubSub),
> `PlatformEvent`, `UnifiedEventPublisher`.
> Este documento é o ponto de entrada; o manual técnico completo é o
> `RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` (56K).

---

## O que esta camada faz

É a camada que mantém a LIA **rodando em produção 24/7** e **aprendendo com uso real**:

- **Circuit breakers:** bloqueiam chamadas em serviços que estão falhando (LLM down, ATS offline, Redis inacessível) — evita cascading failure e dá tempo para recuperação
- **Learning loop:** consome feedback do recrutador (aprovações/rejeições de sugestões da LIA) e ajusta thresholds/pesos via `CalibrationWeight`
- **Mensageria unificada:** abstrai Redis, RabbitMQ e Google Pub/Sub atrás de `BrokerInterface` (permite trocar provider sem mudar código de publisher/subscriber)
- **Eventos canônicos:** `PlatformEvent` é o schema único de eventos internos (`candidate.moved`, `vacancy.created`, `decision.made`, etc.)

Sem essa camada: LIA quebra em produção quando Anthropic/OpenAI tem outage; não aprende com uso; cada feature cria seu próprio esquema de eventos.

---

## Componentes canônicos

| Componente | Arquivo | Responsabilidade |
|-----------|---------|------------------|
| `CircuitBreaker` | `libs/resilience/circuit_breaker/breaker.py` | 3 estados (Closed/Open/Half-Open), thresholds configuráveis |
| 20 circuitos ativos | `app/shared/resilience/circuits.py` | LLM providers, ATS clients, Redis, Pearch AI, Microsoft Graph, WhatsApp, etc |
| `LearningLoopService` | `app/shared/learning/learning_loop_service.py` | Consome feedback → ajusta `CalibrationWeight` por tenant/vaga |
| `BrokerInterface` | `libs/messaging/broker_interface.py` | Protocolo abstrato (publish/subscribe) |
| Implementações de broker | `libs/messaging/providers/{redis,rabbitmq,pubsub}.py` | 3 providers plugáveis |
| `PlatformEvent` | `libs/events/platform_event.py` | Pydantic schema único de eventos |
| `UnifiedEventPublisher` | `app/shared/events/unified_publisher.py` | Facade que escolhe broker por tenant/feature |

---

## O que muda para o dev no produto novo (IA repo)

### Invariantes obrigatórias

1. **Toda chamada a provider externo vai atrás de circuit breaker:**
   ```python
   from app.shared.resilience.circuits import anthropic_circuit

   @anthropic_circuit
   async def call_claude(...):
       return await client.messages.create(...)
   ```
   Sem breaker: uma outage de 5min do Anthropic faz sua app timeout sobre todo request em paralelo → exhaustion de connections → sua DB também cai.

2. **Fallback obrigatório em breaker open:**
   ```python
   try:
       result = await call_claude(...)
   except CircuitBreakerOpenError:
       # fallback: L1+L2 only, ou response cached, ou erro gracioso ao usuário
       result = await fallback_strategy(...)
   ```
   Exemplo real canônico: `fairness_guard.py:962` retorna `is_blocked=False, confidence=0.5, soft_warnings=[...]` quando Layer 3 (Claude Haiku) falha.

3. **Eventos via `UnifiedEventPublisher`, não `redis.publish()` direto:**
   ```python
   from app.shared.events.unified_publisher import UnifiedEventPublisher
   from libs.events.platform_event import PlatformEvent

   await UnifiedEventPublisher().publish(
       PlatformEvent(
           event_type="candidate.moved",
           company_id=company_id,
           payload={...},
       )
   )
   ```
   Permite trocar Redis por RabbitMQ via config — sem refactor.

4. **Calibração por tenant via `CalibrationWeight`:** não hardcodar pesos de scoring. Ler de `calibration_weights` table; fallback para defaults se não existir.

5. **Não bloquear a main request no learning loop.** Feedback é consumido em background (broker-backed worker), não inline no endpoint do recrutador.

### O que NÃO precisa fazer

- Não implementar retry logic ad-hoc — breaker já tem
- Não criar schema de evento novo — estender `PlatformEvent.event_type`
- Não escrever publisher acoplado a Redis — usar `BrokerInterface`

---

## Arquitetura (resumo)

### Circuit breakers: 3 estados

```
       ↓ (sucessos)
CLOSED ─────────────► (requests passam)
  │  ↓ (N falhas em T segundos)
  ↓
OPEN ──────────────► (requests falham rápido com CircuitBreakerOpenError)
  │  ↓ (após timeout de recuperação)
  ↓
HALF-OPEN ──────────► (1 request teste)
  │  ├── sucesso → CLOSED
  │  └── falha   → OPEN
```

Config padrão (ajustar por circuito):
- `failure_threshold: 5` (abre após 5 falhas consecutivas)
- `recovery_timeout: 30s` (meio-aberto após 30s)
- `expected_exception: (TimeoutError, ConnectionError, ...)` — não abre por erro de lógica

### Learning loop

```
Recrutador no UI rejeita sugestão da LIA
       ↓
event: feedback.recruiter_rejection (via UnifiedEventPublisher)
       ↓
Worker consome da queue
       ↓
LearningLoopService.process_feedback()
  ├── Atualiza CalibrationWeight do tenant/vaga
  ├── Log em fairness_audit_log (se for padrão de rejeição por grupo)
  └── Emite métrica para dashboard
```

### Broker providers

| Provider | Quando usar |
|----------|-------------|
| Redis pubsub | Desenvolvimento, staging, volumes baixos |
| RabbitMQ | Produção com >10 msgs/s sustentado, need de ack/retry |
| Google Pub/Sub | Produção em GCP, integração com BigQuery downstream |

Troca via env var `BROKER_BACKEND=redis|rabbitmq|pubsub`. Sem refactor.

---

## Componentes a replicar (ordem sugerida)

1. **`CircuitBreaker` base class + `@decorator`** — independente
2. **Circuitos para LLM providers** (Anthropic, OpenAI) — já desbloqueia uso
3. **`PlatformEvent` schema** + `BrokerInterface` — fundação de eventos
4. **Redis provider de broker** — rápido de stand-up
5. **`UnifiedEventPublisher`** — facade
6. **`LearningLoopService` worker** — consome feedback do recrutador
7. **Circuitos para ATS (`rails_client`), Redis, Pearch AI, Microsoft Graph, WhatsApp** — conforme integrações forem feitas
8. **RabbitMQ/PubSub providers** — quando volume exigir

---

## Dependências

```
Compliance (COMPLIANCE_DEV_HANDOFF)
   ↓ FairnessGuard L3 está atrás de Anthropic circuit
Infrastructure (INFRASTRUCTURE_DEV_HANDOFF)
   ↓ LLMProviderFactory usa circuit breakers
Resilience (ESTE GUIA)  ← IMPLEMENTAR DEPOIS DE COMPLIANCE + INFRA
   ↑ consome eventos de agentes, atos em tools
```

**Não bloqueia o MVP.** Pode subir produto sem breakers no dia 1, mas risco de outage é alto. Prioridade: subir pelo menos circuitos de LLM + fallback de FairnessGuard L3 antes de ligar tráfego de produção.

---

## Validação / Testes

```bash
# Circuit breaker básico
pytest tests/resilience/test_circuit_breaker.py -x

# Learning loop
pytest tests/learning/test_learning_loop_service.py -x

# Eventos
pytest tests/events/test_platform_event.py -x

# Smoke com broker (todos 3 providers)
BROKER_BACKEND=redis pytest tests/messaging/ -x
BROKER_BACKEND=rabbitmq pytest tests/messaging/ -x  # se disponível
```

Smoke manual:
```python
# Força circuit breaker a abrir
from app.shared.resilience.circuits import anthropic_circuit
for _ in range(10):
    try:
        await anthropic_circuit(lambda: raise_timeout())()
    except: pass
# Próxima chamada deve falhar rápido com CircuitBreakerOpenError
```

---

## Diferenças do ambiente da sua empresa

| Dimensão | LIA (Replit) | Produto novo |
|----------|--------------|--------------|
| Broker default | Redis (Replit nativo) | Redis ou RabbitMQ conforme infra |
| LLM providers | Anthropic + OpenAI + Azure | Mesma stack (reutilizar factory) |
| ATS backend | `ats-api-copia` (Rails) via `rails_client` | Mesmo, integrado com FE próprio |
| Deploy | Replit workflows | Ambiente próprio — circuit config via env vars |
| Observability | Logs em `structured_logger` | Mesmo padrão; integrar com seu APM |

---

## Referências

- **Manual técnico:** `RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` (56K) — 8 blocos (A-H) com código exato
- **Mapa:** `CANONICAL_FILES_BY_THEME.md` temas 9 (Resiliência) + 11-13 (Mensageria, Learning, Events)
- **Infra dependente:** `INFRASTRUCTURE_DEV_HANDOFF_2026-04-23.md` (LLMProviderFactory é consumido aqui)

---

## Não fazer

- `git push` — commits locais
- Chamar provider externo sem circuit breaker
- Publicar evento direto no Redis (usar `UnifiedEventPublisher`)
- Bloquear request do recrutador no learning loop (sempre em background)
- Hardcode de pesos de scoring — usar `CalibrationWeight`
- Criar schema de evento ad-hoc — estender `PlatformEvent.event_type`

---

*Handoff gerado em 2026-04-23 | Próxima revisão: quando novo LLM provider, broker ou integração externa for adicionada*

---

## Receitas Executáveis — Thematic Operational Docs

Para implementar qualquer tema deste handoff no v5, consulte os docs operacionais em:

**Mac:** `/Users/paulomoraes/Documents/Python/themes/`
**Replit:** `docs/reconstruction-guides/themes/`
**Índice:** `themes/README.md`

Temas mais relevantes para este handoff: R1 (Circuit Breakers), R2 (Learning Loop + A/B), R3 (Messaging & Events), R4 (Background Jobs), O2 (Config + Flags), O3 (External Integrations)
