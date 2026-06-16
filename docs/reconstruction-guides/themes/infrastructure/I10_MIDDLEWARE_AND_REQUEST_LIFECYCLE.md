# Theme: I10 — Middleware & Request Lifecycle — Infrastructure Layer

## O que é este tema

O middleware stack do LIA é a camada transversal que envolve **toda requisição HTTP** antes de atingir um route handler. É composto por 5 classes Starlette `BaseHTTPMiddleware` (mais uma FastAPI dependency) que adicionam: logging estruturado, request ID rastreável, rate limiting por tenant, envelope de resposta padronizado, e enforcement de autenticação.

O lifecycle de uma requisição atravessa os middlewares em ordem de "cebola" (onion pattern): do mais externo (StructuredLogging) ao mais interno (AuthEnforcement) no request, e volta na ordem inversa no response. O FastAPI processa `add_middleware` em **LIFO** — o último `add_middleware` chamado = outermost (primeiro a executar).

Este tema não inclui AuthEnforcement (documentado em I8) nem a lógica de rate limiting aplicada por agent (documentada em I3/Orchestration). Inclui o lifecycle completo de startup via `lifespan` async context manager em `app/main.py`.

---

## Arquivos conectados (7 total)

### Camada Código (7 arquivos Python)

| Arquivo | Path Canônico | Responsabilidade |
|---------|---------------|------------------|
| `rate_limiter.py` | `app/middleware/rate_limiter.py` | Rate limiting por user + company via Redis ZSET sliding window |
| `request_id.py` | `app/middleware/request_id.py` | UUID4 por requisição; passa X-Request-ID ao response |
| `response_envelope.py` | `app/middleware/response_envelope.py` | Encapsula 2xx JSON em `{ok, data, meta}` |
| `trial_enforcement.py` | `app/middleware/trial_enforcement.py` | FastAPI dependency; bloqueia trials expirados com 402 |
| `auth_enforcement.py` | `app/middleware/auth_enforcement.py` | 7-step JWT pipeline (ver I8) |
| `logging_middleware.py` | `app/core/logging_middleware.py` | StructuredLoggingMiddleware; classifica tier; loga em JSON |
| `logging_config.py` | `app/core/logging_config.py` | `configure_logging()`: JSONFormatter (prod), PIIMaskingFilter |

### Integration points

- **I8 Auth**: `AuthEnforcementMiddleware` é innermost; injeta `request.state.company_id`, `request.state.user_id`
- **I9 Data Layer**: `ContextVar _current_company_id` propagado pelo Auth middleware → consumido por `get_db()` para RLS
- **I6 API Layer**: Routes registradas em `app/api/routes.py`; response envelope aplica-se a todas as rotas não-excluídas
- **C5 Multi-tenancy**: `get_verified_company_id()` depende de `request.state.company_id` injetado pelo Auth middleware
- **I4 LLM Providers**: startup lifespan valida providers antes de aceitar tráfego

---

## Lógica IN → OUT

### Execution Order (Request Processing)

```
HTTP Request
    │
    ▼
[1] StructuredLoggingMiddleware   ← OUTERMOST (add_middleware chamado por ÚLTIMO)
    │   - captura t0, method, path
    ▼
[2] RequestIdMiddleware
    │   - lê X-Request-ID header ou gera uuid4()
    │   - disponível em request.state.request_id
    ▼
[3] CORSMiddleware (starlette.middleware.cors)
    │   - allow_origins = settings.CORS_ORIGINS (list)
    │   - allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    ▼
[4] RateLimitMiddleware
    │   - extrai user_id e company_id do header (lidos do request.state após Auth? — não)
    │   - usa Redis ZSET sliding window
    │   - 429 se exceder limite
    ▼
[5] ResponseEnvelopeMiddleware
    │   - processa APENAS no response path
    │   - envolve JSON 2xx em {ok, data, meta}
    ▼
[6] AuthEnforcementMiddleware   ← INNERMOST (add_middleware chamado PRIMEIRO)
    │   - 7-step JWT validation (ver I8)
    │   - injeta request.state.{company_id, user_id, user_role}
    ▼
Route Handler
    │
    ▼
[Response traversal: reverse order]
    AuthEnforcement → ResponseEnvelope → RateLimit → CORS → RequestId → StructuredLogging
```

**NOTA CRÍTICA:** O comentário em `app/main.py` confirma: *"CORS must be added AFTER RateLimitMiddleware so it executes BEFORE it (FastAPI processes add_middleware in reverse order)"*. Qualquer novo middleware deve considerar a inversão LIFO.

### Registration order em `app/main.py`

```python
# Ordem dos calls add_middleware (LIFO: último = outermost)
app.add_middleware(AuthEnforcementMiddleware)          # innermost → executa por ÚLTIMO
app.add_middleware(ResponseEnvelopeMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(StructuredLoggingMiddleware)        # outermost → executa PRIMEIRO
```

---

## Middleware 1: StructuredLoggingMiddleware

**Arquivo:** `app/core/logging_middleware.py`

```python
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        tier = self._classify_tier(request.url.path)
        logger.info("request_completed", extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "company_id": getattr(request.state, "company_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "tier": tier,
        })
        return response
```

### Classificação de Tier (`_classify_tier`)

| Tier | Path keywords |
|------|---------------|
| `"agent"` | `/lia-assistant/`, `/agent/`, `/wsi/`, `/wizard/` |
| `"management"` | `/admin/`, `/compliance/`, `/audit/`, `/drift/`, `/bias/` |
| `"data"` | tudo o mais |

O campo `tier` é indexado no ElasticSearch/CloudWatch para filtrar métricas por tipo de operação.

---

## Middleware 2: RequestIdMiddleware

**Arquivo:** `app/middleware/request_id.py`

```python
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

- Se o cliente envia `X-Request-ID`, é passado adiante (idempotência)
- O ID fica disponível em `request.state.request_id` para todos os middlewares mais internos e para a rota
- O ID é ecoado no response header — client pode correlacionar com logs
- `StructuredLoggingMiddleware` lê `request.state.request_id` para logar (por isso executa DEPOIS de RequestId no request path, ANTES no response path)

---

## Middleware 3: RateLimitMiddleware

**Arquivo:** `app/middleware/rate_limiter.py`

### Limites configurados

```python
LIMITS = {
    "per_minute_per_user":    600,
    "per_hour_per_user":      20000,
    "per_minute_per_company": 3000,
    "per_hour_per_company":   60000,
}
```

### Algoritmo: Redis ZSET sliding window

```python
async def _check_rate_limit_redis(self, redis, key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)   # remove expired entries
    pipe.zadd(key, {str(now): now})                        # add current request
    pipe.zcard(key)                                        # count total in window
    pipe.expire(key, window_seconds)                       # TTL cleanup
    results = await pipe.execute()
    count = results[2]
    return count <= limit
```

### Fallback in-memory

Se o Redis estiver indisponível, usa `_local_limits: dict[str, list[float]]` com listas de timestamps. **Reconnect cooldown de 30s** — após falha Redis, tenta reconectar a cada 30s (não a cada request).

```python
_reconnect_cooldown = 30  # segundos
_last_redis_attempt: float = 0.0
```

### Identificação de user/company

O RateLimitMiddleware extrai `user_id` e `company_id` do `request.state` (populado pelo AuthEnforcement). **Inconsistência de ordem**: RateLimit executa *antes* de AuthEnforcement no request path — usa fallback de IP para user sem autenticação.

```python
user_id = getattr(request.state, "user_id", None) or request.client.host
company_id = getattr(request.state, "company_id", None) or "anonymous"
```

### Keys Redis

```
rate:user:{user_id}:minute
rate:user:{user_id}:hour
rate:company:{company_id}:minute
rate:company:{company_id}:hour
```

### Response 429

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Middleware 4: ResponseEnvelopeMiddleware

**Arquivo:** `app/middleware/response_envelope.py`

### Envelope format

```json
{
  "ok": true,
  "data": { ... },
  "meta": {
    "request_id": "uuid4-string",
    "ts": "2026-04-23T10:30:00.000Z"
  }
}
```

### Paths excluídos do envelope

```python
BYPASS_PATHS = {"/ws", "/health", "/docs", "/openapi.json", "/redoc", "/metrics"}
```

Qualquer path que comece com `/ws` (WebSocket) também é excluído.

### Condições de bypass

```python
async def dispatch(self, request: Request, call_next):
    # Bypass: env var
    if os.getenv("LIA_DISABLE_ENVELOPE_MIDDLEWARE") == "1":
        return await call_next(request)
    
    # Bypass: paths especiais
    if any(request.url.path.startswith(p) for p in BYPASS_PATHS):
        return await call_next(request)
    
    response = await call_next(request)
    
    # Só envolve 2xx JSON
    if response.status_code < 200 or response.status_code >= 300:
        return response
    if "application/json" not in response.headers.get("content-type", ""):
        return response
    
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    
    data = json.loads(body)
    
    # Idempotência: não re-envolve se já tem envelope
    if isinstance(data, dict) and "ok" in data:
        return response
    
    envelope = {
        "ok": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", None),
            "ts": datetime.utcnow().isoformat() + "Z",
        }
    }
    return JSONResponse(content=envelope, status_code=response.status_code)
```

**Env var override:** `LIA_DISABLE_ENVELOPE_MIDDLEWARE=1` desabilita globalmente. Útil para testes de integração que validam o body raw.

---

## Middleware 5: AuthEnforcementMiddleware (innermost)

Ver documentação completa em **I8 — Auth & Authorization**, seção "AuthEnforcementMiddleware — 7-step pipeline".

Resumo do que injeta em `request.state`:
- `request.state.company_id` — extraído do JWT payload
- `request.state.user_id` — extraído do JWT payload
- `request.state.user_role` — `UserRole` enum value

---

## FastAPI Dependency: require_active_subscription

**Arquivo:** `app/middleware/trial_enforcement.py`

Esta **não é uma classe de middleware Starlette** — é uma FastAPI dependency injetada nos route handlers que requerem subscription ativa.

```python
async def require_active_subscription(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    # Cache no request.state para evitar múltiplas queries por request
    if getattr(request.state, "subscription_checked", False):
        return
    
    subscription = await db.execute(
        select(Subscription).where(Subscription.company_id == current_user.company_id)
    )
    sub = subscription.scalar_one_or_none()
    
    if sub and sub.status in ("CANCELLED", "SUSPENDED"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "subscription_required",
                "message": "Trial expired or subscription cancelled",
                "upgrade_url": f"{settings.RAILS_BACKEND_URL}/billing/upgrade"
            }
        )
    
    request.state.subscription_checked = True
```

### Uso nos routes

```python
@router.post("/candidates/evaluate")
async def evaluate_candidate(
    ...,
    _: None = Depends(require_active_subscription),  # bloqueia se trial expirado
):
    ...
```

---

## Logging Configuration

**Arquivo:** `app/core/logging_config.py`

```python
def configure_logging():
    """Configura logging estruturado. Chamado em app startup (lifespan)."""
    is_production = settings.ENVIRONMENT in ("production", "staging")
    
    handler = logging.StreamHandler()
    
    if is_production:
        handler.setFormatter(JSONFormatter())  # JSON para CloudWatch/Datadog
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    
    # LGPD L7: PII masking no handler
    handler.addFilter(PIIMaskingFilter())
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Silenciar loggers ruidosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### PIIMaskingFilter

Aplica regex antes de emitir qualquer log line em produção. Campos mascarados:
- Email: `usuario@...` → `u***@d***.com`
- CPF: `\d{3}\.\d{3}\.\d{3}-\d{2}` → `***.***.***-**`
- Telefone: `\d{10,11}` → mascarado
- Strings que contêm "password", "token", "secret" → `[REDACTED]`

**Base legal:** LGPD Art. 46 — medidas técnicas para proteger dados pessoais nos logs.

---

## Exception Handlers

Registrados em `app/main.py` via `app.add_exception_handler()`:

```python
# HTTP 451 — usado para compliance blocks (não 403/400)
@app.exception_handler(FairnessBlockedError)
async def fairness_blocked_handler(request, exc):
    return JSONResponse(
        status_code=451,
        content={"error": "fairness_blocked", "detail": str(exc), "code": "FAIRNESS_BLOCK"}
    )

@app.exception_handler(LIAComplianceError)
async def compliance_error_handler(request, exc):
    return JSONResponse(status_code=451, content={"error": "compliance_violation", "detail": str(exc)})

# LIAError → status_code do próprio erro
@app.exception_handler(LIAError)
async def lia_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.message, "request_id": getattr(request.state, "request_id", None)}
    )

# Pydantic validation
@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(request, exc):
    return JSONResponse(status_code=422, content={"errors": exc.errors()})

@app.exception_handler(RequestValidationError)
async def request_validation_handler(request, exc):
    return JSONResponse(status_code=422, content={"errors": exc.errors()})
```

**Por que 451?** HTTP 451 "Unavailable For Legal Reasons" é semanticamente correto para bloqueios por compliance/fairness — sinaliza que não é erro técnico, é restrição legal.

---

## App Startup — lifespan sequence

O `app/main.py` define um `@asynccontextmanager` como `lifespan` do FastAPI (substitui `on_startup`/`on_shutdown`):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === STARTUP (ordem importa — não alterar) ===
    
    # 1. LLM guards — PRIMEIRO (antes de qualquer import de provider)
    install_llm_guards()           # monkey-patches SDK anthropic/openai
    
    # 2. configure_logging
    configure_logging()
    
    # 3. Provider health check
    await collect_provider_health()
    
    # 4. LLM key validation (recusa startup em produção sem ao menos 1 provider)
    await validate_llm_keys()
    
    # 5. Database init
    await init_db()
    
    # 6. Inline migration: wsi_response_analyses.transparency_extras column
    await _ensure_transparency_extras_column()
    
    # 7. LLM circuit breaker validation
    await validate_circuit_breakers()
    
    # 8. MonitoringLoop start (observability)
    await monitoring_loop.start()
    
    # 9. PolicyEngine seed (carrega políticas do banco)
    await policy_engine.seed()
    
    # 10. register_react_agents() (popula AgentRegistry)
    register_react_agents()
    
    # 11. RabbitMQ consumer start
    await rabbitmq_consumer.start()
    
    # 12. Platform Event Handlers registration
    register_platform_event_handlers()
    
    # 13. AiConsumption outbox drainer start
    await ai_consumption_drainer.start()
    
    # 14. A/B Testing seed
    await ab_testing_service.seed()
    
    # 15. OpenAPI schema validation (dev only)
    if settings.ENVIRONMENT == "development":
        validate_openapi_schema(app)
    
    yield  # app serve traffic
    
    # === SHUTDOWN ===
    await rabbitmq_consumer.stop()
    await monitoring_loop.stop()
    await close_redis()
```

**Implicação para v5:** Se qualquer passo 1-6 falhar, o app não sobe. Especialmente o passo 4 (LLM key validation) — em produção, subir sem provider configurado resulta em startup failure com mensagem clara.

---

## Instruções para Claude Code / Cursor

### "Implementa middleware stack no v5"

```
1. Crie app/middleware/ com 4 arquivos:
   - rate_limiter.py    (source: I10 seção "RateLimitMiddleware")
   - request_id.py      (source: I10 seção "RequestIdMiddleware")
   - response_envelope.py (source: I10 seção "ResponseEnvelopeMiddleware")
   - trial_enforcement.py (source: I10 seção "FastAPI Dependency")
   
2. Crie app/core/logging_middleware.py (StructuredLoggingMiddleware)
3. Crie app/core/logging_config.py (configure_logging + PIIMaskingFilter)

4. Em app/main.py, registre na ORDEM EXATA (LIFO — primeiro add_middleware = innermost):
   app.add_middleware(AuthEnforcementMiddleware)
   app.add_middleware(ResponseEnvelopeMiddleware)
   app.add_middleware(RateLimitMiddleware)
   app.add_middleware(CORSMiddleware, ...)
   app.add_middleware(RequestIdMiddleware)
   app.add_middleware(StructuredLoggingMiddleware)

5. Registre exception handlers para FairnessBlockedError (451) e LIAError.

6. Implemente lifespan() com a sequência de startup — especialmente:
   - install_llm_guards() DEVE ser o step 1 (antes de qualquer import de provider)
   - validate_llm_keys() recusa startup em prod sem provider
```

### "Adiciona novo middleware ao v5"

```
1. Crie app/middleware/<nome>.py herdando de BaseHTTPMiddleware
2. Defina dispatch(self, request, call_next) — sempre retorne response
3. Em app/main.py, adicione app.add_middleware(<NovoMiddleware>) DEPOIS dos existentes
   se quiser que execute ANTES de StructuredLogging (mais externo), ou ANTES de
   app.add_middleware(AuthEnforcementMiddleware) se quiser que execute DEPOIS de Auth.
4. Documente no comentário do add_middleware call a ordem de execução esperada.
```

### "Adiciona novo endpoint que requer subscription"

```python
from app.middleware.trial_enforcement import require_active_subscription

@router.post("/minha-rota")
async def minha_rota(
    ...,
    _: None = Depends(require_active_subscription),
):
    ...
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Middleware Order (LIFO)
Execution: StructuredLogging → RequestId → CORS → RateLimit → ResponseEnvelope → AuthEnforcement → Handler
add_middleware order: Auth (first) → ResponseEnvelope → RateLimit → CORS → RequestId → StructuredLogging (last)

## Response Envelope
All 2xx JSON responses wrapped: {"ok": true, "data": {...}, "meta": {"request_id": "...", "ts": "..."}}
Bypass paths: /ws, /health, /docs, /openapi.json, /redoc, /metrics
Disable: LIA_DISABLE_ENVELOPE_MIDDLEWARE=1

## Rate Limits
Per-minute/user: 600 | Per-hour/user: 20000 | Per-minute/company: 3000 | Per-hour/company: 60000
```

### Setup em Cursor rules (snippet pronto)

```
# Infrastructure rules (middleware)
- All HTTP 451 responses MUST use FairnessBlockedError or LIAComplianceError
- New middleware MUST be added BEFORE app.add_middleware(StructuredLoggingMiddleware) call
  if it should execute after logging; AFTER if it should execute before logging
- require_active_subscription dependency is required on all paid-feature endpoints
- Never log raw email/CPF/phone — PIIMaskingFilter covers prod but don't rely on it in dev
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|---------------|
| Rate limit values (LIMITS dict) | Ajustar por plano/tier |
| BYPASS_PATHS no ResponseEnvelope | Adicionar novos paths |
| Tier classification keywords | Adaptar para paths do v5 |
| Redis key format (`rate:user:{id}:minute`) | Pode prefixar com namespace |
| `LIA_DISABLE_ENVELOPE_MIDDLEWARE` env var | Pode renomear env var |
| Logging format (JSONFormatter vs plain) | Adaptar ao sink de logs do v5 |

### NÃO pode adaptar (base legal ou arquitetural)

| Item | Motivo |
|------|--------|
| HTTP 451 para FairnessBlockedError | Semântica correta por lei; 403 ou 400 seria incorreto tecnicamente |
| PIIMaskingFilter no logging handler | LGPD Art. 46 — obrigatório em produção |
| `install_llm_guards()` como step 1 do startup | Ordem crítica — deve acontecer antes de qualquer import SDK |
| LIFO order dos add_middleware | Comportamento Starlette/FastAPI — não é configurável |
| `request.state.company_id` injetado pelo Auth | Contrato com I9 RLS — qualquer middleware que leia company_id deve executar DEPOIS de Auth |
| Rate limiting em company granularity | Multi-tenancy: necessário para isolamento de consumo por cliente |

---

## Checklist de completude (P0/P1/P2)

### Middleware

- [ ] (P0) StructuredLoggingMiddleware presente e logando `company_id` por requisição
- [ ] (P0) RequestIdMiddleware gera UUID4 e retorna X-Request-ID no response
- [ ] (P0) RateLimitMiddleware com fallback in-memory quando Redis indisponível
- [ ] (P0) ResponseEnvelopeMiddleware: bypass em `/ws` e `/health`
- [ ] (P0) Exception handler para FairnessBlockedError → HTTP 451
- [ ] (P0) Exception handler para LIAError → structured JSON com request_id
- [ ] (P1) `LIA_DISABLE_ENVELOPE_MIDDLEWARE` env var funciona em testes
- [ ] (P1) PIIMaskingFilter aplicado no log handler em produção
- [ ] (P1) Rate limits distintos para user vs company (4 buckets Redis)
- [ ] (P1) Reconnect cooldown 30s no RateLimitMiddleware (não conectar a cada request)
- [ ] (P2) Tier classification em StructuredLoggingMiddleware (agent/management/data)
- [ ] (P2) `response.headers["X-Request-ID"]` presente em todas as respostas

### Startup lifecycle

- [ ] (P0) `install_llm_guards()` é o PRIMEIRO passo do lifespan
- [ ] (P0) `validate_llm_keys()` recusa startup em produção sem provider
- [ ] (P0) `init_db()` chamado antes de qualquer operação de banco
- [ ] (P1) `register_react_agents()` chamado antes de aceitar tráfego de agentes
- [ ] (P1) `policy_engine.seed()` chamado no startup
- [ ] (P2) OpenAPI schema validation ativa apenas em development

---

## Gotchas e erros comuns

### G1: LIFO inversion — mais comum ao adicionar middleware

**Problema:** Dev adiciona novo middleware DEPOIS de `StructuredLoggingMiddleware` esperando que execute antes de tudo — mas ele acaba sendo o outermost por ser o último `add_middleware`.

**Solução:** Sempre desenhar o stack como lista de `add_middleware` calls na ordem OPOSTA à execução desejada. O **último** `add_middleware` = **primeiro** a executar.

---

### G2: RateLimitMiddleware lê `request.state` antes do Auth

**Problema:** RateLimit executa ANTES de Auth no request path. Se tentar `request.state.user_id` quando o Auth não rodou ainda → `AttributeError` ou string vazia.

**Causa:** A ordem de execução é RateLimit → ResponseEnvelope → Auth. Rate limiting usa fallback para IP quando user_id não disponível.

**Solução:** Já implementado com `getattr(request.state, "user_id", None) or request.client.host`. Ao adicionar campos ao state, sempre usar `getattr(..., None)`.

---

### G3: ResponseEnvelope re-envolve respostas já envoltas

**Problema:** Em testes ou com proxy reverso, uma resposta já no formato `{ok, data, meta}` pode ser re-envolida em `{ok: true, data: {ok: true, data: ...}}`.

**Solução:** Já implementado — verifica `isinstance(data, dict) and "ok" in data` antes de envolver. Se detectado, retorna response original sem modificar.

---

### G4: `install_llm_guards()` não é o primeiro passo

**Problema:** Qualquer import de `anthropic` ou `openai` antes de `install_llm_guards()` quebra o monkey-patch. Módulos importados no topo do arquivo são executados no import time.

**Solução:** `app/main.py` chama `install_llm_guards()` como primeira linha do lifespan, antes de qualquer await. Não adicionar imports de providers no topo do módulo `main.py`.

---

### G5: LIA_DISABLE_ENVELOPE_MIDDLEWARE em testes

**Problema:** Testes de integração que validam o body raw falham porque recebem o envelope em vez do JSON direto.

**Solução:** Setar `LIA_DISABLE_ENVELOPE_MIDDLEWARE=1` no ambiente de testes. Alternativa: checar `response.json()["data"]` em vez de `response.json()` diretamente.

---

### G6: PIIMaskingFilter não é suficiente como única barreira

**Problema:** `PIIMaskingFilter` aplica regex no log line final — mas dados PII já chegaram em memória. Além disso, em development o formatter é plain (não JSON) e o filter ainda aplica.

**Solução:** O filter é a **última linha de defesa**, não a primeira. A primeira é não logar PII em código (não passar `user.email` para `logger.info`). Ver LGPD Art. 46.

---

## Testes obrigatórios

| Teste | Path | Cenário coberto |
|-------|------|-----------------|
| Request ID propagation | `tests/integration/test_middleware.py` | X-Request-ID gerado + retornado no response header |
| Rate limit user bucket | `tests/unit/test_rate_limiter.py` | 601 requests/min → 429; request 602 blocked |
| Rate limit company bucket | `tests/unit/test_rate_limiter.py` | 3001 requests/min de company → 429 |
| Rate limit Redis fallback | `tests/unit/test_rate_limiter.py` | Redis down → in-memory fallback ativo |
| Response envelope 200 | `tests/integration/test_response_envelope.py` | JSON 200 → `{ok: true, data: ..., meta: ...}` |
| Response envelope bypass /health | `tests/integration/test_response_envelope.py` | GET /health → sem envelope |
| Response envelope WebSocket bypass | `tests/integration/test_response_envelope.py` | /ws path → sem envelope |
| Response envelope idempotent | `tests/integration/test_response_envelope.py` | Body já tem "ok" → não re-envolve |
| FairnessBlockedError → 451 | `tests/integration/test_exception_handlers.py` | raise FairnessBlockedError → HTTP 451 |
| LIAComplianceError → 451 | `tests/integration/test_exception_handlers.py` | raise LIAComplianceError → HTTP 451 |
| Trial enforcement 402 | `tests/integration/test_trial_enforcement.py` | Subscription CANCELLED → 402 |
| PII masking in logs | `tests/unit/test_logging_config.py` | Email em log line → mascarado |
| Startup validates LLM keys | `tests/integration/test_startup.py` | Sem provider em prod → startup failure |

---

## Referências

- **I8 — Auth & Authorization** — `AuthEnforcementMiddleware` (innermost) + `get_verified_company_id()`
- **I9 — Data Layer & Migrations** — `ContextVar _current_company_id` (set pelo Auth, lido pelo `get_db()`)
- **I4 — LLM Providers (BYOK)** — `install_llm_guards()` (step 1 do lifespan)
- **C5 — Multi-tenancy & Isolation** — `tenant_guard.py` depende de `request.state.company_id`
- **C1 — Fairness** — `FairnessBlockedError` mapeado para HTTP 451 aqui
- **I6 — API Layer & WebSocket** — `/ws` paths excluídos do envelope e do rate limiting padrão
- **LGPD Art. 46** — medidas técnicas de proteção de dados (base legal do PIIMaskingFilter)
- **ADR-005** — ResponseEnvelope como contrato de API (ver docs/architecture/)
- **RESILIENCE_LEARNING Parte A** — circuit breakers validados no step 7 do lifespan
