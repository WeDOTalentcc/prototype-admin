# Theme C5 — Multi-tenancy & Isolation

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance) + cross-ref Card 3 (Infrastructure)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

Isolamento entre tenants (clientes do SaaS) para que company A **nunca** acesse dados de company B. Implementa LGPD Art. 6 minimização via **TenantGuard** — uma dependency FastAPI que extrai `company_id` do JWT validado pelo middleware, e rejeita qualquer tentativa de override via header/query (cross-tenant attack).

É a fundação de segurança do SaaS: sem isolamento, todos os demais temas de compliance (fairness, LGPD, audit) falham porque dados de tenants se misturariam.

**Boundary com temas irmãos:**
- **I8 Auth** — autenticação (quem é você?); C5 é autorização por tenant (a que company você pertence?)
- **C2 PII Masking** — PII em logs; C5 é isolamento estrutural de dados
- **C4 Candidate Portal** — JWT candidato SEPARADO; company_id também via token
- **I10 Middleware** — AuthEnforcementMiddleware é middleware; C5 é a dependency que consome request.state

---

## Arquivos conectados (6 Python + 1 YAML)

### Camada Persona (LLM vê — 1 YAML)

| Arquivo | Bundle | Como é injetado |
|---------|--------|-----------------|
| `guardrails_block.yaml` (seção `multi_tenancy`) | LIA_YAMLS_CANONICAL_BUNDLE §shared | GuardrailsDomainPrompt injeta em todo agent — "NUNCA confie em company_id de payload; SEMPRE use o do contexto" |

### Camada Código (Python — 6 arquivos)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|------------------|
| `tenant_guard.py` | `app/shared/tenant_guard.py` | 74 | **Núcleo.** `get_verified_company_id()` dependency — extrai do JWT, valida contra header/query, retorna 401/403 em violação |
| `auth_enforcement.py` | `app/middleware/auth_enforcement.py` | 350 | Middleware que **valida JWT** antes de chegar aos endpoints + popula `request.state.company_id` |
| `session_bridge.py` | `app/shared/session_bridge.py` | 179 | `SessionContext` + `SessionBridge` — passa contexto entre agents/tools durante execução |
| `tenant_session.py` | `app/shared/tenant_session.py` | 34 | `create_session_id(company_id)` + `extract_company_id(session_id)` — convenção de naming para isolamento em Redis/cache |
| `tenant_llm_context.py` | `app/shared/tenant_llm_context.py` | 279 | **BYOK por tenant.** `get_tenant_llm_config()`, `get_claude_model_for_tenant()`, `get_gemini_client_for_tenant()` — LLM provider resolve por company_id |
| `dependencies.py` (auth) | `app/auth/dependencies.py` | 643 | `get_current_user`, `get_current_active_user`, `require_role`, `_resolve_rails_jwt_user` — dependency chain completa de auth |

### Integration points

- **`AuthEnforcementMiddleware`** valida JWT em TODO request → popula `request.state.company_id` + `request.state.user_id`
- **Endpoints** declaram `Depends(get_verified_company_id)` → recebem company_id já validado
- **Services** recebem `company_id` como parâmetro — NUNCA acessam request direto
- **Repositories** filtram por `company_id` em TODA query (validado em lint via `check_tenant_isolation.py`)
- **LLM calls** via `tenant_llm_context` selecionam modelo/provider por tenant (BYOK)
- **Redis keys** sempre prefixadas com `company_id` (via `create_session_id`)

---

## Lógica IN → OUT

### Input

**Request arbitrário ao FastAPI** (ex.: `GET /api/v1/candidates`):

```python
# Headers possíveis
Authorization: Bearer <JWT>     # CRÍTICO — fonte de verdade
X-Company-ID: <uuid>            # opcional — SE presente, DEVE bater com JWT
# Query params
?company_id=<uuid>              # opcional — SE presente, DEVE bater com JWT
```

### Processing

**Passo 1 — `AuthEnforcementMiddleware` (antes de todo endpoint):**

```python
# auth_enforcement.py — linha ~138
class AuthEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Dev API key bypass (apenas dev)
        dev_bypass = _check_dev_api_key(request, path)
        if dev_bypass: return dev_bypass

        # 2. Extrair JWT do header Authorization
        token = self._extract_token(request)

        # 3. Validar JWT (rails_jwt ou WorkOS)
        user, company_id = await self._validate(token)

        # 4. Popular request.state
        request.state.user_id = user.id
        request.state.company_id = company_id

        # 5. Passar adiante
        response = await call_next(request)
        return response
```

**Passo 2 — Endpoint declara dependency:**

```python
# Endpoint typical
@router.get("/candidates")
async def list_candidates(
    company_id: str = Depends(get_verified_company_id),  # ← TenantGuard
    db: AsyncSession = Depends(get_db),
):
    # company_id aqui é GARANTIDAMENTE do JWT
    # Endpoint não precisa (e NÃO pode) fazer validação adicional
    ...
```

**Passo 3 — `get_verified_company_id()` (tenant_guard.py — verbatim):**

```python
def get_verified_company_id(
    request: Request,
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    company_id: str | None = Query(None),
) -> str:
    # Primary source: JWT-validated
    jwt_company = getattr(request.state, "company_id", None)
    # Secondary source: header or query
    requested_company = x_company_id or company_id

    if jwt_company:
        if requested_company and requested_company != jwt_company:
            # CROSS-TENANT attempt → 403
            logger.warning(f"[TenantGuard] CROSS-TENANT blocked: JWT={jwt_company}, requested={requested_company}")
            raise HTTPException(403, "Access denied: company mismatch")
        return jwt_company

    # Fallback dev mode only
    is_production = os.getenv("ENVIRONMENT") in ("production", "staging")
    if is_production and not jwt_company:
        raise HTTPException(401, "Authentication required")

    if requested_company:
        return requested_company  # dev mode only

    raise HTTPException(401, "Company ID required")
```

### Output

- **200 OK** com `company_id` do JWT → endpoint executa isolado
- **401 Unauthorized** → JWT ausente ou inválido
- **403 Forbidden** → JWT presente MAS header/query tenta override com outra company

### Side effects

- **Log warning** em toda tentativa de cross-tenant (para audit)
- **Métrica** `cross_tenant_attempts_total{company_id, attempted_company_id}` — Prometheus
- **Alert** quando taxa de 403 por origem única > threshold (possível attack)

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Cross-tenant 403 | Log + metric + alerta SRE |
| JWT válido mas sem `company_id` (token mal formado) | 401 + log para investigação |
| Dev mode em produção (ENVIRONMENT não setado) | Startup falha — hard fail |
| Pattern sistemático de 403 por mesmo IP | Rate limiter (I10) bloqueia + security alert |

---

## BYOK (Bring Your Own Key) por tenant

`tenant_llm_context.py` implementa **BYOK**: cada tenant pode usar sua própria API key do Anthropic/OpenAI/Azure/Gemini.

**Flow:**

```python
# Em um agent
from app.shared.tenant_llm_context import get_claude_model_for_tenant

config = await get_tenant_llm_config(company_id)
# config = {"provider": "anthropic", "api_key": "<key-do-tenant>", "model": "claude-sonnet-4-5"}

client = get_claude_model_for_tenant(company_id)  # cached
response = await client.messages.create(...)
```

**Benefícios:**
- Tenant tem seu próprio billing Anthropic/OpenAI
- Rate limits do tenant não afetam outros
- Compliance: dados não passam por conta single-tenant da LIA
- Fallback para conta da LIA se tenant não configurou

**Cache:** `_cache_get/_cache_set` (TTL implícito) — reduz queries ao DB a cada LLM call.

---

## Session ID pattern (isolamento em Redis/cache)

`tenant_session.py`:

```python
def create_session_id(company_id: str) -> str:
    # Convenção: todos session_id começam com company_id
    # Exemplo: "c_abc123_s_xyz789"
    ...

def extract_company_id(session_id: str) -> str:
    # Permite verificar se session pertence ao company antes de acessar
    ...
```

**Uso:**
- Redis keys: `rate_limit:{session_id}:hour` → inclui company_id implicitamente
- Cache de conversation state: `conv:{session_id}` → isolado por tenant
- Audit: rastrear ações por session → saber de qual company

---

## Instruções para Claude Code / Cursor

### "Implementa Multi-tenancy no v5"

```
1. COPIE 6 arquivos Python (tenant_guard, auth_enforcement, session_bridge, tenant_session, tenant_llm_context, auth/dependencies)

2. REGISTRE middleware no app startup (ORDEM IMPORTA — auth_enforcement deve vir PRIMEIRO):
   app.add_middleware(AuthEnforcementMiddleware)
   app.add_middleware(OtherMiddleware)
   ...

3. ENFORCE em TODO endpoint:
   @router.get("/whatever")
   async def handler(
       company_id: str = Depends(get_verified_company_id),  # OBRIGATÓRIO
       current_user: User = Depends(get_current_user),
   ):
       ...

4. ENFORCE em TODO repository query:
   # Sempre filtrar por company_id
   query = select(Model).where(Model.company_id == company_id)
   # NUNCA: select(Model).where(Model.id == id_from_payload)

5. CONFIGURE .env:
   - ENVIRONMENT=production (crítico em prod — falha dev mode fallback)
   - JWT_SECRET=<secret shared com Rails>
   - WORKOS_API_KEY=<key> (se usar WorkOS)

6. INSTALE lint CI: scripts/check_tenant_isolation.py
   # Verifica que toda endpoint tem Depends(get_verified_company_id)
   # Bloqueia merge se faltar

7. BYOK opcional (tenant_llm_context):
   - Migration para `tenant_llm_configs` table (company_id, provider, api_key_encrypted, model)
   - Endpoint admin para tenant configurar próprio key
   - Encryption at rest (redis_crypto — ver C6)

8. VERIFIQUE:
   - pytest tests/integration/test_cross_tenant.py (assert 403 em attempts)
   - pytest tests/unit/test_tenant_guard.py
   - Smoke: user A com JWT + tenta X-Company-ID de B → 403
```

### "Adiciona multi-tenancy a uma feature nova"

```
1. Endpoint:
   @router.method("/path")
   async def handler(
       company_id: str = Depends(get_verified_company_id),  # mandatory
       ...
   ): ...

2. Service layer:
   async def do_something(company_id: str, ...):
       # nunca acessar request direto
       # company_id sempre do caller

3. Repository:
   async def query(self, company_id: str, ...):
       stmt = select(Model).where(Model.company_id == company_id)
       ...

4. Se LLM call: use tenant_llm_context
   client = get_claude_model_for_tenant(company_id)

5. Se cache/Redis: use session_id com company_id embutido
   session_id = create_session_id(company_id)
   redis.set(f"feature:{session_id}", ...)

6. Se background job (R4): passa company_id no payload do task
   task.apply_async(kwargs={"company_id": company_id, ...})
```

### Setup em CLAUDE.md

```markdown
## Compliance: Multi-tenancy & Isolation

- **company_id SEMPRE do JWT**, nunca do payload/header/query (header só como validação)
- Toda endpoint: `Depends(get_verified_company_id)` OBRIGATÓRIO
- Toda query: filtro `.where(Model.company_id == company_id)` OBRIGATÓRIO
- Cross-tenant attempt → 403 automático via TenantGuard
- BYOK opcional: `tenant_llm_context` retorna client/model por tenant
- Session IDs incluem company_id para isolamento em Redis

Consultar `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md`.
```

### Setup em `.cursor/rules/multi-tenancy.mdc`

```
---
description: "C5 Multi-tenancy — isolamento por company_id"
alwaysApply: false
---

Quando o usuário pedir para:
- Criar endpoint novo
- Adicionar repository / service
- Escrever query DB
- Invocar LLM
- Cache / Redis

1. Leia themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md
2. NUNCA aceitar company_id de payload/body/query (só como validação vs JWT)
3. SEMPRE Depends(get_verified_company_id) em endpoint novo
4. SEMPRE .where(Model.company_id == company_id) em query
5. LLM via tenant_llm_context.get_claude_model_for_tenant(company_id)
6. Session_id via create_session_id(company_id)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nomes de funções (`get_verified_company_id` pode virar `require_tenant`)
- JWT library (PyJWT, jose, authlib)
- Secret rotation schedule
- WorkOS → outro SSO provider
- Redis → outro cache backend
- BYOK opt-in vs mandatório
- Error messages em outros idiomas

### NÃO pode adaptar (crítico de segurança)

| Invariante | Por quê | Consequência se violar |
|-----------|---------|------------------------|
| `company_id` do JWT, não do payload | LGPD Art. 6 + anti-IDOR | Cross-tenant breach |
| Middleware valida JWT ANTES do endpoint | Sem auth = sem tenant context | Endpoint pode rodar unauthenticated |
| 403 quando header/query diverge do JWT | Detecção ativa de attack | Silent pass = breach eventual |
| Production fails if no JWT | Fallback dev NÃO pode vazar pra prod | Vazamento estrutural |
| `.where(company_id=X)` em toda query | Isolamento físico de dados | SELECT vaza entre tenants |
| Session IDs prefixados com company | Isolamento em Redis/cache | Key collision entre tenants |
| Lint `check_tenant_isolation.py` em CI | Prevenção de regressão | Bugs acumulam |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `AuthEnforcementMiddleware` registrado PRIMEIRO na cadeia
- [ ] **(P0)** TODOS os endpoints têm `Depends(get_verified_company_id)` ou `get_current_user`
- [ ] **(P0)** TODAS as queries de DB filtram por `company_id`
- [ ] **(P0)** `ENVIRONMENT=production` configurado em prod
- [ ] **(P0)** JWT_SECRET configurado e rotacionado trimestralmente
- [ ] **(P0)** Lint `scripts/check_tenant_isolation.py` rodando em CI
- [ ] **(P1)** BYOK implementado (tenant_llm_configs table + endpoint admin)
- [ ] **(P1)** API key encryption at rest via redis_crypto (C6)
- [ ] **(P1)** Session IDs sempre via `create_session_id(company_id)`
- [ ] **(P1)** Cross-tenant metric + alert configurado
- [ ] **(P2)** WorkOS SSO integrado (opcional mas recomendado)
- [ ] **(P2)** Rails JWT shared secret (integração com ats-api-copia)
- [ ] **(P2)** Dev API key só em dev environment (nunca prod)

---

## Gotchas e erros comuns

| Sintoma | Causa raiz | Como evitar |
|---------|-----------|-------------|
| Endpoint funciona sem auth | `Depends(get_verified_company_id)` esquecido | Lint `check_tenant_isolation.py` |
| Cross-tenant query permite acesso | Repository não filtra por `company_id` | Code review + lint grep por queries sem .where company_id |
| Dev mode ativo em staging | ENVIRONMENT não setado | Startup script verifica + fail se missing |
| Rate limit aplica ao tenant errado | Redis key sem company_id prefix | `create_session_id()` sempre |
| JWT expira → 401 em meio a operação | Token TTL muito curto | Refresh token mechanism |
| WorkOS integration quebra em tenant específico | Config tenant-specific ausente | Fallback para JWT Rails |
| BYOK key vaza para outro tenant | Cache key sem company_id prefix | `_cache_get(company_id)` com key isolada |
| Header X-Company-ID funcionando em prod sem JWT | Fallback lógica executando em prod | `is_production` check obrigatório |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| Cross-tenant blocked | `tests/integration/test_tenant_guard_cross_tenant.py` | JWT A + X-Company-ID B → 403 |
| JWT absent → 401 | `tests/integration/test_tenant_guard_no_jwt.py` | Sem Authorization → 401 |
| Production no JWT → 401 | `tests/integration/test_tenant_guard_prod_enforcement.py` | ENVIRONMENT=production + no JWT → 401 |
| JWT valid → company_id returned | `tests/unit/test_tenant_guard_happy_path.py` | JWT válido → retorna company_id do token |
| Header matches JWT → OK | `tests/unit/test_tenant_guard_header_match.py` | Header X-Company-ID == JWT.company_id → 200 |
| Repository isolates | `tests/integration/test_repository_isolation.py` | Query em company A não retorna rows de B |
| LLM BYOK per tenant | `tests/unit/test_tenant_llm_context.py` | get_claude_model_for_tenant(A) != (B) |
| Session ID isolation | `tests/unit/test_session_bridge.py` | extract_company_id(session_id) retorna company original |
| Lint CI | `scripts/check_tenant_isolation.py` | Endpoint sem `get_verified_company_id` → CI red |

---

## Referências

### Bundles verbatim
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 1 (guardrails_block.yaml — seção multi_tenancy)

### Reconstruction guides
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` **BLOCO G** — tenant_guard.py verbatim

### Handoff dev
- `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` — invariante #1 (company_id do JWT)

### Regulatório
- **LGPD Art. 6** — minimização + princípio de finalidade
- **LGPD Art. 46** — segurança de dados
- **ISO/IEC 27001** — tenant isolation é requisito
- **`responsible-ai/eu-ai-act-technical-documentation-pt.md`** §4.5 (multi-tenant data leak mitigation)

### Lint scripts
- `scripts/check_tenant_isolation.py` — enforcement automático em CI

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit em `lia-agent-system/`*
