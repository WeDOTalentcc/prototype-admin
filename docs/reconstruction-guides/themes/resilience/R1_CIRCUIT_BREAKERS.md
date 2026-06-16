# Theme: Circuit Breakers — Resilience Layer

## O que é este tema

Circuit Breakers são o mecanismo de **falha rápida** da LIA: quando um serviço externo começa a falhar, o circuit abre e rejeita chamadas imediatamente, devolvendo respostas de modo degradado em vez de deixar o sistema travar aguardando timeouts.

O padrão previne **cascading failures** — uma API lenta não bloqueia threads, não consume rate limits e não propaga latência para o usuário final. A implementação é dupla: **class-based** (`CircuitBreaker`) para os 18 serviços externos pré-definidos em `ALL_CIRCUITS`, e **functional** (decorator `circuit_breaker`) para uso ad-hoc em código novo.

**Boundary com temas irmãos:**
- **I4 LLM Providers**: `ANTHROPIC_CIRCUIT`, `OPENAI_CIRCUIT`, `GEMINI_CIRCUIT` protegem os providers do LLM cascade. `validate_llm_circuit_configs()` é chamado no startup (I10 lifespan step 15)
- **R3 Messaging**: `MAILGUN_CIRCUIT`, `RESEND_CIRCUIT`, `TWILIO_VOICE_CIRCUIT` protegem canais de mensagem
- **O3 Integrations**: `PEARCH_CIRCUIT`, `APIFY_CIRCUIT`, `MERGE_CIRCUIT`, `GUPY_CIRCUIT` etc protegem integrações externas
- **C1 Fairness**: Adendo B do RESILIENCE_LEARNING documenta o fallback do FairnessGuard L3 quando o circuit de LLM está OPEN

---

## Arquivos conectados (3 total)

### Camada Código (3 arquivos Python)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `circuit_breaker.py` | `app/shared/resilience/circuit_breaker.py` | Implementação completa: CircuitBreaker class + functional decorator + ALL_CIRCUITS + SLOs + degraded responses |
| `circuit_breaker.py` (service) | `app/shared/services/circuit_breaker.py` | Re-export de backward compatibility: `from app.shared.resilience.circuit_breaker import *` |
| `admin_circuit_breakers.py` | `app/api/v1/admin_circuit_breakers.py` | Admin REST API para monitorar e resetar circuits (require_admin) |

### Integration points

- `app/main.py` lifespan → chama `validate_llm_circuit_configs()` no startup
- `app/shared/providers/llm_provider.py` → wraps chamadas com `ANTHROPIC_CIRCUIT.call()`, `OPENAI_CIRCUIT.call()` etc.
- `app/shared/rails_client.py` → usa `RAILS_CIRCUIT`
- `app/api/routes.py` → registra `admin_circuit_breakers.router`
- `app/services/notification_service.py` → chamado por `_notify_circuit_open()` para Bell + Teams

---

## Lógica IN → OUT

### Input

| Fonte | Tipo |
|-------|------|
| Chamada de API externa | `async def minha_func(*args) → Any` |
| Excepção lançada | `Exception` subclass ou `TimeoutError` |
| `time.time()` passado | Trigger automático OPEN→HALF_OPEN |

### 3 Estados e Transições

```
         failure_count >= threshold
CLOSED ─────────────────────────────► OPEN
  ▲                                     │
  │ success_count >= success_threshold  │ recovery_timeout elapsed
  │                                     ▼
  └─────────────────────────── HALF_OPEN
         (any failure)→ OPEN
```

**CLOSED → OPEN:** `failure_count >= config.failure_threshold` (default 5)
- Dispara `_notify_circuit_open()` async (Bell + Teams, Redis dedup TTL 1h)
- `_METRICS_AVAILABLE=True` → Prometheus metric atualizado

**OPEN → HALF_OPEN:** Automático na propriedade `state` quando `time.time() - last_failure_time >= recovery_timeout`
- Não requer chamada externa — ocorre na próxima leitura de `circuit.state`

**HALF_OPEN → CLOSED (class-based):** `success_count >= config.success_threshold` (default 2)
**HALF_OPEN → CLOSED (functional):** `half_open_calls >= half_open_max_calls` (default 3)
**HALF_OPEN → OPEN:** qualquer falha durante teste de recuperação

**record_success() bonus (CLOSED):** `failure_count = max(0, failure_count - 1)` — decrementa gradualmente após sucesso

### Processing (class-based)

```python
# CircuitBreaker.call() — fluxo completo
async def call(func, *args, **kwargs):
    async with self._lock:          # asyncio.Lock — thread-safe
        current_state = self.state  # OPEN→HALF_OPEN automático aqui
        self._stats.total_calls += 1
        if current_state == CircuitState.OPEN:
            self._stats.rejected_calls += 1
            raise CircuitBreakerError(self.name, retry_after)
    
    # Executa fora do lock
    result = await asyncio.wait_for(func(*args, **kwargs), timeout=config.timeout)
    await self.record_success()
    return result
    # TimeoutError → record_failure()
    # Exception in exclude_exceptions → record_success() mas re-raise
    # Outros → record_failure() + re-raise
```

### Processing (functional decorator)

```python
@circuit_breaker("pearch", failure_threshold=3, recovery_timeout=60.0, fallback=my_fallback)
async def search_candidates(query: str):
    ...

# Interno:
# cb = _get_circuit("pearch", ...)   ← _circuits dict global
# if not _should_allow_call(cb): raise CircuitBreakerError ou retorna fallback
# _record_success(cb) ou _record_failure(cb, exc)
```

### Output

| Cenário | Output |
|---------|--------|
| Circuit CLOSED, chamada OK | Resultado da função normalmente |
| Circuit CLOSED, falha n < threshold | Exception re-raised, failure_count++ |
| Circuit OPEN | `CircuitBreakerError(name, retry_after)` ou fallback se definido |
| Circuit HALF_OPEN, sucesso | Resultado normal, contagem de recuperação avança |
| Modo degradado (API call) | `get_degraded_response(service_name)` → string humanizada em PT-BR |

### Escalation / HITL

- `_notify_circuit_open()`: quando circuit abre → notificação Bell (frontend) + Teams (ops) via `notification_service.send_system_alert(severity="warning", channels=["bell","teams"])`
- Redis dedup key: `cb_alert:{service_name}`, TTL 3600s — no máximo 1 alerta/circuit/hora
- Admin endpoint `POST /api/v1/admin/circuit-breakers/{name}/reset`: permite reset manual durante incident response

---

## 18 Circuits pré-definidos (ALL_CIRCUITS)

| Nome | failure_threshold | recovery_timeout | timeout | SLO tier |
|------|:-:|:-:|:-:|:-:|
| `anthropic` | 5 | 30.0s | 60.0s | **critical** (99.9%) |
| `openai` | 5 | 30.0s | 60.0s | **critical** (99.9%) |
| `gemini` | 5 | 30.0s | 60.0s | high (99.5%) |
| `pearch` | 3 | 60.0s | 30.0s | high (99%) |
| `apify` | 3 | 60.0s | 30.0s | medium (99%) |
| `apify_search` | 3 | 120.0s | 300.0s | low (95%) |
| `workos` | 5 | 30.0s | 15.0s | **critical** (99.9%) |
| `merge` | 5 | 45.0s | 30.0s | high (99%) |
| `google_calendar` | 5 | 60.0s | 30.0s | medium (99.5%) |
| `gupy` | 5 | 45.0s | 30.0s | high (99%) |
| `pandape` | 5 | 45.0s | 30.0s | high (99%) |
| `mailgun` | 5 | 30.0s | 30.0s | **critical** (99.9%) |
| `resend` | 5 | 30.0s | 30.0s | high (99.9%) |
| `iugu` | 3 | 60.0s | 30.0s | medium (99.5%) |
| `vindi` | 3 | 60.0s | 30.0s | medium (99.5%) |
| `twilio_voice` | 3 | 60.0s | 30.0s | high (99%) |
| `gemini_live` | 3 | 30.0s | 60.0s | **critical** (99.9%) |
| `rails_api` | 5 | 30.0s | 15.0s | **critical** (99.9%) |

**SLO tiers:**
- `critical`: availability_target=0.999 (43 min downtime/mês), error_budget_pct=0.1%
- `high`: availability_target=0.99 ou 0.999, error_budget_pct=0.1-1.0%
- `medium`: availability_target=0.995, error_budget_pct=0.5%
- `low`: availability_target=0.95, error_budget_pct=5.0%

---

## CIRCUIT_BREAKER_SLOS — SLOs por serviço

Estrutura por service_name:
```python
{
    "availability_target": 0.999,   # ex: anthropic
    "latency_p95_ms": 8000,
    "error_budget_pct": 0.1,
    "tier": "critical",
    "description": "LLM primário — Claude (Anthropic)",
}
```

Usado por: `_compute_slo_status()` no admin endpoint (`'ok'` | `'breached'` | `'unknown'`).

Lógica de status:
1. Se `state == 'open'` → `'breached'` (SLO de disponibilidade violado)
2. Se `error_rate = failed/total > (1 - availability_target)` → `'breached'`
3. Caso contrário → `'ok'`

---

## DEGRADED_MODE_RESPONSES

18+ mensagens em PT-BR para `get_degraded_response(service_name)`. Exemplos representativos:

```python
"anthropic": "A assistente LIA está temporariamente indisponível. O serviço de IA principal (Anthropic) está com instabilidades. Tente novamente em alguns minutos ou contate o suporte."

"pearch": "A busca de candidatos externos está temporariamente indisponível. Você pode buscar na base interna de candidatos enquanto isso."

"rails_api": "O ATS principal está temporariamente indisponível. Os dados locais em cache continuam acessíveis. Operações de escrita serão enfileiradas para sincronização assim que o serviço for restaurado."
```

Fallback genérico: `"Este serviço está temporariamente indisponível. Tente novamente em alguns minutos."` (via `_DEGRADED_FALLBACK`).

---

## `validate_llm_circuit_configs()` — startup validator

Valida os 3 LLM circuits (`anthropic`, `openai`, `gemini`) no startup:

```python
_MIN_TIMEOUT = 30.0       # LLM calls must time out in [30, 120]s
_MAX_TIMEOUT = 120.0
_MIN_THRESHOLD = 3        # Must open after [3, 10] failures
_MAX_THRESHOLD = 10

# Retorna dict per-service: {ok, timeout_s, failure_threshold, recovery_timeout_s, success_threshold, issues[]}
# results["_all_ok"] = True/False
```

Chamado em `app/main.py` lifespan. Se `_all_ok == False`, log de warning mas não impede startup (design deliberado — falha de validação não quebra o serviço).

---

## Admin API

**Base URL:** `/api/v1/admin/circuit-breakers`  
**Auth:** `require_admin` (todos os endpoints)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Status combinado (class + functional) de todos os circuits |
| `/{circuit_name}/reset` | POST | Reset manual de um circuit para CLOSED |
| `/reset-all` | POST | Reset de TODOS os circuits (operação de emergência) |

**Response de GET `/`:**
```json
{
    "total": 18,
    "open_count": 1,
    "circuits": {
        "anthropic": {
            "implementation": "class",
            "state": "open",
            "slo": {...},
            "slo_status": "breached",
            "degraded_mode_message": "A assistente LIA está...",
            ...
        }
    }
}
```

**`_get_combined_status()`:** merge de `get_all_circuit_stats()` (class-based) + `get_all_circuits_status()` (functional). Nomes que aparecem em ambos: class tem precedência.

---

## Instruções para Claude Code / Cursor

### "Implementa Circuit Breakers no v5"

```
1. Criar app/shared/resilience/__init__.py (vazio)

2. Criar app/shared/resilience/circuit_breaker.py
   - Copiar CircuitState (StrEnum), CircuitBreakerConfig (dataclass), CircuitBreakerStats (dataclass)
   - Copiar CircuitBreakerError com message template
   - Copiar CircuitBreaker class (asyncio.Lock, state property com auto-transition, call(), record_success(), record_failure(), reset(), get_stats())
   - Copiar ALL_CIRCUITS dict com os 18 circuits pré-definidos
   - Copiar CIRCUIT_BREAKER_SLOS dict (4 tiers: critical/high/medium/low)
   - Copiar DEGRADED_MODE_RESPONSES dict (18+ mensagens PT-BR)
   - Copiar functional-style: CircuitBreakerState (dataclass), _circuits dict, circuit_breaker decorator
   - Copiar validate_llm_circuit_configs() — startup validator
   - Copiar _notify_circuit_open() — notificação async com Redis dedup

3. Criar app/shared/services/circuit_breaker.py
   from app.shared.resilience.circuit_breaker import *  # backward compat

4. Criar app/api/v1/admin_circuit_breakers.py
   - 3 endpoints (GET /, POST /{name}/reset, POST /reset-all)
   - _get_combined_status() + _compute_slo_status()
   - require_admin em todos

5. Registrar router em app/api/routes.py:
   from app.api.v1 import admin_circuit_breakers
   app.include_router(admin_circuit_breakers.router)

6. Wiring em app/main.py lifespan (step startup):
   from app.shared.resilience.circuit_breaker import validate_llm_circuit_configs
   results = validate_llm_circuit_configs()
   if not results["_all_ok"]:
       logger.warning("LLM circuit breaker config issues: %s", results)
```

### "Adiciona Circuit Breaker a serviço externo novo"

```python
# Opção A — class-based (adicionar ao ALL_CIRCUITS):
from app.shared.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

MEU_SERVICO_CIRCUIT = CircuitBreaker(
    "meu_servico",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=30.0,
    )
)
# Adicionar em ALL_CIRCUITS dict e CIRCUIT_BREAKER_SLOS

# Opção B — functional decorator (uso ad-hoc):
from app.shared.resilience.circuit_breaker import circuit_breaker

@circuit_breaker("meu_servico", failure_threshold=3, recovery_timeout=60.0, fallback=minha_resposta_degradada)
async def chamar_servico_externo(params):
    ...
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Circuit Breakers — R1
- 18 circuits pré-definidos: anthropic/openai/gemini/pearch/apify/workos/merge/rails_api + outros
- Todos os serviços externos DEVEM usar circuit breaker (class ou functional)
- get_degraded_response(service_name) → mensagem PT-BR humanizada quando circuit OPEN
- validate_llm_circuit_configs() chamado no startup — não remover
- Admin: GET/POST /api/v1/admin/circuit-breakers requer require_admin
- _notify_circuit_open() = Bell + Teams, Redis dedup 1h TTL
- app/shared/services/circuit_breaker.py = re-export para compat; canonical = app/shared/resilience/
```

### Setup em Cursor rules (snippet pronto)

```
# Circuit Breakers (R1)
- NUNCA chamar API externa sem circuit breaker (class-based ou decorator @circuit_breaker)
- failure_threshold LLM: [3,10]; timeout LLM: [30,120]s — validate_llm_circuit_configs() valida
- Degraded responses em PT-BR em DEGRADED_MODE_RESPONSES — não inventar nova mensagem inline
- SLO crítico (99.9%): anthropic, openai, workos, mailgun, gemini_live, rails_api
- Canonical import: from app.shared.resilience.circuit_breaker import ...
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|--------------|
| `CircuitBreakerConfig` defaults | Ajustar failure_threshold/recovery_timeout por serviço |
| `DEGRADED_MODE_RESPONSES` textos | Adaptar ao produto v5 (manter PT-BR) |
| `CIRCUIT_BREAKER_SLOS` por serviço | Ajustar se v5 usa providers diferentes |
| `ALL_CIRCUITS` composição | Adicionar/remover serviços conforme integrações v5 |
| `_notify_circuit_open()` channels | Adaptar para canais de notificação do v5 (Slack, PagerDuty) |
| Prometheus metrics (`_METRICS_AVAILABLE`) | Habilitar com Prometheus client se v5 usa Prometheus |
| `half_open_max_calls` padrão | Ajustar para maior/menor tolerância de recovery |

### NÃO pode adaptar (arquitetural ou contratual)

| Item | Razão |
|------|-------|
| 3 estados (CLOSED/OPEN/HALF_OPEN) e suas transições | Contrato do padrão Circuit Breaker — alterar quebra a semântica de proteção |
| `validate_llm_circuit_configs()` no startup | Garante que LLM não pode bloquear indefinidamente; timeout < 120s e threshold < 10 são guardrails de operação |
| `asyncio.Lock()` em `record_success()/record_failure()` | Thread safety obrigatória — remover causa race condition em concurrent calls |
| `asyncio.wait_for(func, timeout=config.timeout)` | Timeout computacional que garante liberação; remover deixa threads penduradas indefinidamente |
| `exclude_exceptions` não registra como falha | Erros de negócio (ex: 404) não devem penalizar o circuit — parte do contrato |
| `require_admin` nos endpoints de reset | Segurança — admin reset sem auth é vetor de ataque (DoS via reset loop) |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** Todos os 18 serviços externos têm circuit em `ALL_CIRCUITS` — nenhum chamado diretamente sem proteção
- [ ] **(P0)** `validate_llm_circuit_configs()` chamado no startup e resultado logado
- [ ] **(P0)** `asyncio.Lock()` presente em `record_success()` e `record_failure()` — thread safety
- [ ] **(P0)** `asyncio.wait_for()` com timeout em `CircuitBreaker.call()` — evita threads penduradas
- [ ] **(P1)** Admin endpoints (`/admin/circuit-breakers`) registrados e protegidos por `require_admin`
- [ ] **(P1)** `CIRCUIT_BREAKER_SLOS` populado para todos os serviços em `ALL_CIRCUITS`
- [ ] **(P1)** `DEGRADED_MODE_RESPONSES` contém mensagem para cada serviço (ou fallback genérico cobre)
- [ ] **(P1)** `_notify_circuit_open()` com Redis dedup — sem flood de alertas (1h TTL)
- [ ] **(P1)** `app/shared/services/circuit_breaker.py` → re-export (backward compat)
- [ ] **(P2)** `_compute_slo_status()` retornando `'breached'` quando circuit OPEN
- [ ] **(P2)** `CircuitBreakerStats` (total_calls, rejected_calls, state_changes) populado
- [ ] **(P2)** `reset_all_circuits()` endpoint documentado como "operação de emergência"

---

## Gotchas e erros comuns

### 1. Race condition sem asyncio.Lock()

**Problema:** `record_success()` e `record_failure()` sem lock podem causar race condition em ambientes com múltiplas coroutines concorrentes — dois coroutines podem ler `failure_count=4` simultaneamente e ambos decrementarem ou incrementarem, pulando a transição de estado.

**Correto:** Ambos os métodos usam `async with self._lock`.

### 2. `_circuits` (functional) vs `ALL_CIRCUITS` (class) — dois registries

**Problema:** `get_all_circuit_stats()` retorna apenas `ALL_CIRCUITS`. `get_all_circuits_status()` retorna apenas `_circuits`. O admin endpoint `_get_combined_status()` faz o merge — mas se alguém monitorar apenas uma fonte, pode perder circuits do outro registry.

**Correto:** Sempre usar `_get_combined_status()` para monitoramento completo.

### 3. `CircuitBreakerError` recebe `retry_after` como `float`, não string

**Problema:** `raise CircuitBreakerError(service_name, cb.state)` no functional decorator (linha 939) passa o `CircuitState` em vez do `float retry_after`. Inconsistência entre implementações class vs functional.

**Débito técnico detectado:** Functional decorator passa `cb.state` (enum) como `retry_after` — `CircuitBreakerError.__init__` espera `float`. No class-based, é calculado via `_get_retry_after()`. Em v5, padronizar para `float`.

### 4. `_notify_circuit_open()` é best-effort — falha silenciosa

**Problema:** Toda exception em `_notify_circuit_open()` é capturada silenciosamente. Se Redis ou notification_service estiverem down, a notificação é perdida sem log.

**Comportamento correto por design:** Circuit breaker não pode falhar por causa de falha de notificação. O trade-off é intencional — apenas `logger.debug("[CircuitBreaker] Notification failed (non-blocking): %s", _e)`.

### 5. Functional circuit config não é atualizada após criação

**Problema:** `_get_circuit("pearch", failure_threshold=3)` cria o estado na primeira chamada. Se a mesma função for chamada com `failure_threshold=5` depois, o threshold não muda — a config inicial persiste no `_circuits` dict global.

**Correto:** Para mudar config de um functional circuit, chamar `reset_circuit("pearch")` antes de re-criar (ou usar class-based para maior controle).

### 6. `exclude_exceptions=()` default pode mascarar bugs

**Problema:** Se um serviço lança `ValueError` por bug no código (não por falha externa), e esse exception for adicionado a `exclude_exceptions`, o circuit nunca abre mesmo com o serviço quebrado.

**Correto:** `exclude_exceptions` deve conter apenas exceptions de "negócio esperado" (ex: `NotFoundError`, `ValidationError`) — nunca exceptions de infra (ex: `ConnectionError`, `TimeoutError`).

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| `test_circuit_opens_after_threshold` | `tests/unit/test_circuit_breaker.py` | 5 falhas consecutivas → estado OPEN |
| `test_circuit_half_open_after_timeout` | `tests/unit/test_circuit_breaker.py` | Após recovery_timeout → estado HALF_OPEN |
| `test_circuit_closes_after_successes` | `tests/unit/test_circuit_breaker.py` | 2 sucessos em HALF_OPEN → CLOSED |
| `test_circuit_rejects_when_open` | `tests/unit/test_circuit_breaker.py` | Circuit OPEN → CircuitBreakerError sem chamar o serviço |
| `test_degraded_response_all_services` | `tests/unit/test_circuit_breaker.py` | Todos os 18 serviços têm resposta degradada (ou fallback genérico) |
| `test_validate_llm_circuit_configs_pass` | `tests/unit/test_circuit_breaker.py` | LLM circuits com config válida → `_all_ok=True` |
| `test_validate_llm_circuit_configs_fail` | `tests/unit/test_circuit_breaker.py` | Circuit com timeout=200s → `issues` não vazio, `_all_ok=False` |
| `test_admin_list_requires_admin` | `tests/security/test_admin_endpoints.py` | GET /admin/circuit-breakers sem admin → 403 |
| `test_admin_reset_circuit` | `tests/integration/test_circuit_breaker_admin.py` | POST reset → circuit retorna CLOSED |
| `test_slo_status_breached_when_open` | `tests/unit/test_circuit_breaker.py` | circuit state=open → slo_status='breached' |
| `test_functional_decorator_fallback` | `tests/unit/test_circuit_breaker.py` | Circuit OPEN com fallback → retorna fallback sem exception |
| `test_lock_thread_safety` | `tests/unit/test_circuit_breaker.py` | 100 coroutines concorrentes → contador consistente (sem race) |

---

## Referências

### Código (SSoT)
- `app/shared/resilience/circuit_breaker.py` (1025 linhas) — implementação completa
- `app/shared/services/circuit_breaker.py` — re-export backward compat
- `app/api/v1/admin_circuit_breakers.py` — admin REST API

### Bundles e Guides
- Reconstruction Guide `RESILIENCE_LEARNING` Parte A — Circuit Breakers (estado inicial e integração)
- `RESILIENCE_LEARNING` Adendo B — fallback do FairnessGuard L3 quando circuit LLM OPEN
- Thematic Doc I10 (`I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md`) — startup lifespan step que chama `validate_llm_circuit_configs()`
- Thematic Doc I4 (`I4_LLM_PROVIDERS.md`) — LLM cascade usa ANTHROPIC_CIRCUIT/OPENAI_CIRCUIT/GEMINI_CIRCUIT
- Thematic Doc O3 (`O3_EXTERNAL_INTEGRATIONS.md`) — PEARCH_CIRCUIT, APIFY_CIRCUIT etc

### Handoffs
- `DEVELOPER_HANDOFF.md` — referencia circuit breakers em seção de resiliência
