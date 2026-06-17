# Theme I6 — API Layer / Routes / ChatResponse (inclui WebSocket)

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/app/api/` + `app/schemas/` no Replit

---

## O que é este tema

A camada de **API** da LIA cobre todos os endpoints REST e WebSocket expostos ao frontend e a integrações externas. Inclui:

1. **APIResponse envelope** (`api_envelope.py`) — `APIResponse[T]` é o shape padrão de todos os responses (LIA-E01)
2. **ChatResponse** (`chat.py`) — schema de mensagem de chat com `tool_calls` para eval/judge (LIA-LCF-01)
3. **Path patterns** (`_path_patterns.py`) — `DUAL_ID_PATH_PATTERN` previne route shadowing (ADR-003)
4. **WebSocket Manager** (`ws_manager.py`) — gerencia conexões WS com Redis Pub/Sub para broadcast entre workers
5. **Error hierarchy** (`errors.py`) — `LIAError` + subclasses para erros cross-cutting com `code`, `message`, `recoverable`
6. **Streaming** (`chat_event_serializer.py`, `streaming_callback.py`) — serialização de chunks para SSE/WS

**Boundary com temas irmãos:**
- **I3 Orchestration** — endpoints de chat chamam `MainOrchestrator.process()` e recebem `ChatResponse`
- **I10 Middleware** — todo request passa pelos middlewares antes de chegar nos endpoints
- **C5 Multi-tenancy** — `get_verified_company_id()` (I10/C5) é dependency injetada em endpoints
- **I8 Auth** — `get_current_user()` é dependency injetada em endpoints protegidos

---

## Arquivos conectados (8 Python)

### Camada Código (8 arquivos Python)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `api_envelope.py` | `app/schemas/api_envelope.py` | 126 | `APIResponse[T]`, `APIMetadata`, `APIError`, `@api_envelope` decorator — shape padrão LIA-E01/E02 |
| `chat.py` | `app/schemas/chat.py` | — | `MessageCreate`, `MessageResponse` (+ `tool_calls`), `ConversationResponse`, `ChatResponse` |
| `_path_patterns.py` | `app/api/v1/_path_patterns.py` | 72 | `DUAL_ID_PATH_PATTERN` (UUID v4 | bigint), `reorder_collection_before_item()` — anti-shadowing ADR-003 |
| `ws_manager.py` | `app/shared/websocket/ws_manager.py` | 186 | `WSManager` — Redis Pub/Sub broadcast entre workers Uvicorn |
| `ws_message_schemas.py` | `app/shared/websocket/ws_message_schemas.py` | 106 | Schemas de mensagens WebSocket |
| `chat_event_serializer.py` | `app/shared/chat_event_serializer.py` | 145 | Serialização de eventos de chat para SSE/WS |
| `streaming_callback.py` | `libs/agents-core/lia_agents_core/streaming_callback.py` | — | LangGraph streaming callback para chunks em tempo real |
| `errors.py` | `app/shared/errors.py` | 154 | `LIAError` + subclasses: `LIAToolError`, `LIAComplianceError`, `LIATenantError`, etc. |

### Integration points

- **Orchestrator** (I3) recebe `UniversalContext` + retorna `ChatResponse`; endpoint de chat converte para `APIResponse`
- **Middleware stack** (I10) processa cada request antes de chegar nos endpoints
- **TenantGuard** (C5) é `Depends()` em todos os endpoints que leem/escrevem dados
- **Auth** (I8) é `Depends(get_current_user)` em endpoints protegidos
- **WSManager** usa Redis (I9) para Pub/Sub entre workers
- **StreamingCallback** é passado para `MainOrchestrator.process(streaming_callback=cb)` em endpoints SSE

---

## Lógica IN → OUT

### APIResponse[T] — envelope padrão (LIA-E01)

```python
# app/schemas/api_envelope.py (126L) — LIA-E01

class APIMetadata(BaseModel):
    request_id: str | None = None
    timestamp: datetime                  # UTC
    api_version: str = "v1"
    duration_ms: float | None = None
    pagination: dict | None = None

class APIError(BaseModel):
    code: str       # "VALIDATION_ERROR", "TENANT_NOT_FOUND", etc.
    message: str    # human-readable (PT-BR)
    field: str | None = None
    details: dict | None = None

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = ""
    data: T | None = None
    metadata: APIMetadata
    errors: list[APIError] | None = None
    
    # Factory methods:
    @classmethod
    def ok(cls, data=None, message="", metadata=None) -> "APIResponse": ...
    @classmethod
    def fail(cls, message, errors=None, metadata=None) -> "APIResponse": ...

# Decorator LIA-E02 — opt-in para migração gradual:
@api_envelope
async def my_endpoint(...) -> dict:
    return {"key": "value"}
# → automaticamente envolto em APIResponse.ok(data={"key": "value"})

APIEnvelope = APIResponse  # alias de compatibilidade
```

**Shapes:**
```json
// Sucesso:
{"success": true, "message": "...", "data": {...}, "metadata": {...}, "errors": null}

// Erro:
{"success": false, "message": "...", "data": null, "metadata": {...}, "errors": [...]}
```

### ChatResponse — schema de chat (LIA-LCF-01)

> **Arquitetura dual:** Existem **dois** `ChatResponse` distintos no codebase:
> 1. **`app/schemas/chat.py`** (descrito abaixo) — shape externo da API, enviado ao frontend
> 2. **`app/orchestrator/main_orchestrator.py`** — shape interno do orquestrador, 20 campos (ver I3 §ChatResponse). O endpoint de chat converte o interno para o externo.
> Ao replicar: implemente ambos — o orquestrador retorna seu `ChatResponse` de 20 campos, e o endpoint converte para o schema externo `app/schemas/chat.py::ChatResponse`.

```python
# app/schemas/chat.py

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None
    context: dict[str, Any] | None = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    message_metadata: dict[str, Any] = {}
    # LIA-LCF-01 (Task #620): tool calls surfaced for eval/judge consumers
    tool_calls: list[dict[str, Any]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    user_role: str
    title: str | None
    intent: str | None
    workflow_type: str | None
    workflow_step: int
    workflow_data: dict[str, Any] = {}
    status: str
    created_at: datetime
    updated_at: datetime

class ChatResponse(BaseModel):
    message: MessageResponse
    conversation: ConversationResponse
```

### DUAL_ID_PATH_PATTERN — anti-shadowing (ADR-003)

```python
# app/api/v1/_path_patterns.py (72L)

# UUID v4 OR Rails bigint — previne que item handlers capturem rotas coleção
DUAL_ID_PATH_PATTERN = (
    r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+)$"
)

# Uso em endpoints:
from typing import Annotated
from fastapi import Path
DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: DualId): ...
# → "search" não casa com o pattern → não shadowed por este handler

# Anti-shadowing helper:
def reorder_collection_before_item(router) -> None:
    # Move collection routes (sem {}) antes de item routes (com {})
    # Previne Task #455-class bugs sem depender de ordem de declaração

# Structural test:
# tests/api/test_dual_id_route_shadowing.py → falha o build se {*_id} sem constraint
```

**ADRs relacionados:**
- ADR-003: Dual-ID strategy (UUID v4 LIA | bigint Rails)
- ADR-005: `response_model` obrigatório em todos os endpoints FastAPI
- ADR-006: no PII in logs (via observability middleware)
- ADR-008: `APIResponse` envelope em novos endpoints (LIA-E01)
- ADR-014: All routes under `/api/v1/` prefix

### WSManager — Redis Pub/Sub multi-worker

```python
# app/shared/websocket/ws_manager.py (186L)

class WSManager:
    # _sessions: dict[session_id → WebSocket]  ← local a cada worker Uvicorn
    # _user_sessions: dict[user_id → set[session_id]]
    # _pubsub: Redis Pub/Sub subscriber
    # _redis: Redis client
    
    # Channel prefix: "ws:session:{session_id}"
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        company_id: str,
        user_id: str = "anonymous",
    ) -> bool:
        # accept() + registra em _sessions + subscreve no Redis channel
    
    async def send_to_session(self, session_id: str, data: dict):
        # Publica no Redis channel → todos os workers recebem → entrega à WS local
    
    # Fallback: se Redis indisponível → entrega apenas para conexões locais do worker
    # (single-worker mode — sem Pub/Sub)

# Redis channel per session:
# "ws:session:{session_id}" → cada worker inscreve + retransmite para WS local
```

### LIAError hierarchy

```python
# app/shared/errors.py (154L)

class LIAError(Exception):
    """Base error com code + message + details + recoverable."""
    def __init__(
        self,
        message: str = "Erro interno da plataforma",
        code: str = "INTERNAL_ERROR",
        details: dict | None = None,
        recoverable: bool = False,
    ):
    
    @property
    def as_dict(self) -> dict: ...  # serializa para APIError-compatible

# Subclasses cross-cutting (confirmadas em app/shared/errors.py):
class LIAToolError(LIAError): ...       # código: "TOOL_*"
class LIAComplianceError(LIAError): ... # código: "COMPLIANCE_*" (LGPD, fairness)
class LIATenantError(LIAError): ...     # código: "TENANT_*"
class LIAAgentError(LIAError): ...      # código: "AGENT_*"
class LIALLMError(LIAError): ...        # código: "LLM_*"
class LIAValidationError(LIAError): ... # código: "VALIDATION_*"
class LIAConsentError(LIAError): ...    # código: "CONSENT_*" (LGPD Art. 7)
class LIAFairnessError(LIAError): ...   # código: "FAIRNESS_*"
class LIAIntegrationError(LIAError): ...# código: "INTEGRATION_*"
```

**Uso em handlers de erro FastAPI:**
```python
@app.exception_handler(LIAError)
async def lia_error_handler(request, exc: LIAError):
    return JSONResponse(
        status_code=400,
        content=APIResponse.fail(
            message=exc.message,
            errors=[APIError(code=exc.code, message=exc.message, details=exc.details)]
        ).dict()
    )
```

### Side effects

- **Audit log** (C7): endpoints de chat persistem `conversation_id` + `user_id` via middleware
- **Rate limiter** (I10): WSManager `connect()` pode ser bloqueado pelo `RateLimiterMiddleware`
- **Métricas** (I5): `APIMetadata.duration_ms` alimenta latência de endpoint

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Route shadowing detectado em CI | `tests/api/test_dual_id_route_shadowing.py` falha o build |
| Redis indisponível para WSManager | Fallback para single-worker mode (sem broadcast) + log WARNING |
| `LIAComplianceError` em endpoint | HTTP 400 com code COMPLIANCE_* + mensagem educativa em PT-BR |
| `LIATenantError` em endpoint | HTTP 401/403 com code TENANT_* + instrução de autenticação |

---

## Instruções para Claude Code / Cursor

### "Cria novo endpoint REST no v5"

```python
# Padrão obrigatório — ADR-005 (response_model) + ADR-008 (APIResponse) + ADR-014 (/api/v1)

from fastapi import APIRouter, Depends
from app.schemas.api_envelope import APIResponse
from app.shared.tenant_guard import get_verified_company_id
from app.auth.dependencies import get_current_user
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

router = APIRouter(prefix="/api/v1/my-resource", tags=["my-resource"])

DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

@router.get(
    "/{item_id}",
    response_model=APIResponse[dict],  # ADR-005: obrigatório
    summary="Get item",
)
async def get_item(
    item_id: DualId,                              # anti-shadowing ADR-003
    company_id: str = Depends(get_verified_company_id),  # multi-tenancy C5
    current_user = Depends(get_current_user),            # auth I8
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    # NUNCA acessar sem company_id verificado
    data = await my_service.get(item_id=item_id, company_id=company_id, db=db)
    return APIResponse.ok(data=data, message="OK")

# SEMPRE chamar ao final do router file (anti-shadowing):
reorder_collection_before_item(router)
```

### "Cria endpoint WebSocket"

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.shared.websocket.ws_manager import ws_manager

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    company_id: str,  # validate via JWT no handshake
):
    connected = await ws_manager.connect(
        websocket=websocket,
        session_id=session_id,
        company_id=company_id,
        user_id=str(current_user.id),
    )
    if not connected:
        await websocket.close(code=1011)
        return
    
    try:
        while True:
            data = await websocket.receive_json()
            # processar...
            await ws_manager.send_to_session(session_id, {"type": "response", ...})
    except WebSocketDisconnect:
        await ws_manager.disconnect(session_id)
```

### "Adiciona erro customizado"

```python
from app.shared.errors import LIAError

# 1. Crie subclasse:
class LIAMyDomainError(LIAError):
    pass

# 2. Levante nos handlers:
raise LIAMyDomainError(
    message="Recurso indisponível em PT-BR",
    code="MY_DOMAIN_RESOURCE_UNAVAILABLE",
    details={"resource_id": resource_id, "reason": "not_found"},
    recoverable=True,
)
# → APIResponse.fail() automático via exception_handler
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: API Layer & WebSocket (I6)

- **Envelope:** `APIResponse[T]` em todos os endpoints (ADR-008) — `APIResponse.ok()` / `.fail()`
- **ADR-005:** `response_model=APIResponse[...]` obrigatório em todos os @router decorators
- **ADR-014:** Todos os endpoints sob `/api/v1/` (sem exceção)
- **ADR-003:** `DUAL_ID_PATH_PATTERN` em path params dual-ID (UUID | bigint)
- **Anti-shadowing:** `reorder_collection_before_item(router)` no final de cada router file
- **WebSocket:** `ws_manager.send_to_session()` para broadcast multi-worker (Redis Pub/Sub)
- **Erros:** Sempre `LIAError` (ou subclasses) — nunca HTTPException diretamente

Consultar `themes/infrastructure/I6_API_LAYER_AND_WEBSOCKET.md`.
```

### Setup em `.cursor/rules/api-layer.mdc`

```
---
description: "I6 API Layer & WebSocket"
alwaysApply: false
---

Quando o usuário pedir para:
- Criar novo endpoint REST ou WebSocket
- Adicionar schema de resposta
- Corrigir erro de roteamento (shadowing)
- Implementar streaming SSE ou WS

1. Leia themes/infrastructure/I6_API_LAYER_AND_WEBSOCKET.md
2. response_model=APIResponse[T] em TODOS os endpoints (ADR-005)
3. DUAL_ID_PATH_PATTERN em path params de entidades dual-ID
4. reorder_collection_before_item(router) no final de cada router file
5. company_id SEMPRE de Depends(get_verified_company_id) — nunca body
6. Erros via LIAError subclasses — nunca raise HTTPException direto
7. Rotas SEMPRE em /api/v1/ (ADR-014)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- `APIMetadata` campos adicionais (versão do api diferente de "v1")
- Subclasses de `LIAError` específicas do produto (novos códigos de erro)
- `ws_message_schemas.py` — shapes das mensagens WS (específicos do produto)
- Cache de `ChatResponse` em Redis (curta duração)
- `MessageResponse.message_metadata` (campos adicionais por produto)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| `APIResponse[T]` como envelope (ADR-008) | Consistência cross-team; frontend espera shape fixo | Frontend quebra com shapes diferentes |
| `response_model` obrigatório (ADR-005) | FastAPI não valida response sem response_model | Dados inesperados passam sem validação |
| `DUAL_ID_PATH_PATTERN` em dual-ID params | Route shadowing derruba endpoints de coleção | GET /candidates/search → 422 ou 404 inesperado |
| `reorder_collection_before_item()` | Proteção contra ordem-de-declaração regressões | Task #455-class bug reintroduzido por qualquer dev |
| `/api/v1/` prefix obrigatório (ADR-014) | Versionamento de API | Breaking change no frontend sem versionamento |
| `company_id` de `Depends(get_verified_company_id)` | Anti-IDOR + multi-tenancy | Endpoint lê dados de outro tenant |
| PII fora de logs (ADR-006) | LGPD — PII não deve aparecer em application logs | Email/CPF em logs = LGPD violation |
| `tool_calls` em `MessageResponse` (LIA-LCF-01) | Eval framework consome tool_calls para judge | Avaliadores automáticos não conseguem verificar qual tool foi chamada |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `APIResponse[T]` importado e usado em todos os novos endpoints (ADR-008)
- [ ] **(P0)** `response_model=APIResponse[...]` em todos os `@router.get/post/put/delete` (ADR-005)
- [ ] **(P0)** Todos os endpoints sob `/api/v1/` prefix (ADR-014)
- [ ] **(P0)** `get_verified_company_id` em todos os endpoints com dados de tenant
- [ ] **(P0)** `DUAL_ID_PATH_PATTERN` em path params de entidades dual-ID
- [ ] **(P0)** `reorder_collection_before_item()` no final de cada router file com item routes
- [ ] **(P1)** `WSManager` com Redis Pub/Sub configurado (fallback single-worker documentado)
- [ ] **(P1)** `LIAError` subclasses registradas como exception handlers no FastAPI app
- [ ] **(P1)** `tool_calls` em `MessageResponse` populado pelo orchestrator (LIA-LCF-01)
- [ ] **(P1)** Structural test `tests/api/test_dual_id_route_shadowing.py` passando
- [ ] **(P2)** `@api_envelope` decorator usado em endpoints legados (migração gradual LIA-E02)
- [ ] **(P2)** `APIMetadata.duration_ms` populado via middleware (I10)
- [ ] **(P2)** `streaming_callback` integrado em endpoint de chat para SSE

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| GET /candidates/search retorna 422 | Route shadowing: `{candidate_id}` sem constraint captura "search" | `DUAL_ID_PATH_PATTERN` + `reorder_collection_before_item()` |
| Response sem envelope nos novos endpoints | `response_model` omitido no decorator | Structural test + ADR-005 review no PR |
| WebSocket broadcast não chega a todos os users | Redis Pub/Sub não configurado; workers usando só memória local | Verificar `REDIS_URL` env var; log `[WS] Connected` inclui session_id |
| `LIAComplianceError` retorna 500 em vez de 400 | Exception handler não registrado para `LIAError` | Registrar `@app.exception_handler(LIAError)` em `main.py` |
| PII aparece em application logs | Handlers fazem `logger.info(str(request.body))` | Usar logging middleware estruturado (I10) que não loga body; ADR-006 |
| Endpoint com company_id do body | `company_id = request.json().get("company_id")` | Sempre `Depends(get_verified_company_id)` — NUNCA do body |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Route anti-shadowing | `tests/api/test_dual_id_route_shadowing.py` | `/candidates/search` não shadowed por `/candidates/{id}` |
| APIResponse shape | `tests/unit/test_api_envelope.py` | `APIResponse.ok(data={"k":"v"})` → JSON correto |
| APIResponse fail | `tests/unit/test_api_envelope.py` | `APIResponse.fail("err")` → success=false + errors[0] |
| Dual-ID path pattern | `tests/unit/test_path_patterns.py` | UUID v4 → match; bigint → match; "search" → no match |
| WSManager connect | `tests/unit/test_ws_manager.py` | `connect()` → session registrada em `_sessions` |
| WSManager broadcast | `tests/integration/test_ws_manager.py` | `send_to_session()` → Redis pub → message recebida em mock WS |
| WSManager Redis fallback | `tests/unit/test_ws_manager.py` | Redis down → `send_to_session()` entrega localmente sem crash |
| LIAError hierarchy | `tests/unit/test_errors.py` | `raise LIAToolError(code="T")` → `as_dict` tem code + recoverable |
| company_id from JWT only | `tests/integration/test_endpoints.py` | body.company_id ignorado — JWT.company_id usado |

---

## Referências

### Bundles verbatim
- Nenhum YAML específico (tema é 100% código).

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` BLOCO H (ChatResponse + API patterns)

### ADRs referenciados
- ADR-003: Dual-ID strategy (UUID v4 LIA | bigint Rails)
- ADR-005: response_model obrigatório
- ADR-006: no PII in application logs
- ADR-008: APIResponse envelope
- ADR-014: All routes under /api/v1

### Cross-references
- **I3 Orchestration** — endpoints de chat chamam `MainOrchestrator.process()`
- **I8 Auth** — `get_current_user()` dependency em endpoints protegidos
- **I9 Data Layer** — `get_db()` dependency injetada em todos os endpoints com DB
- **I10 Middleware** — stack de middleware processa request antes dos endpoints
- **C5 Multi-tenancy** — `get_verified_company_id()` é fundamental em todos os endpoints
- **I5 Observability** — `APIMetadata.duration_ms` + AI inference logs

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
