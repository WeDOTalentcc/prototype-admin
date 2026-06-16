# Theme: I8 — Authentication & Authorization — Infrastructure Layer

## O que é este tema

Authentication & Authorization é a camada que valida quem é o usuário e qual empresa ele representa antes de qualquer lógica de negócio. A arquitetura suporta **dois tipos de token** em dual-fallback:

1. **FastAPI JWT** — gerado pelo próprio lia-agent-system, payload `{sub: UUID, type: "access", company_id, role}`
2. **Rails JWT** — gerado pelo ats_api (Rails), payload `{user_id: int, exp}`, sem company_id nativo

A resolução de company_id é a operação crítica de segurança: para tokens Rails, o company_id nunca está no payload — é resolvido via chamada a `/v1/me` no Rails API (com cache de 5 min). Para tokens FastAPI, o company_id está no payload JWT.

O sistema tem três camadas de enforcement:
- **Middleware global** (`AuthEnforcementMiddleware`) — intercepta toda requisição não-pública, injeta `request.state.company_id`
- **Dependency FastAPI** (`get_current_user`, `get_current_user_strict`) — resolve o objeto User para o endpoint
- **`get_verified_company_id()`** — dependency final que garante que o company_id usado em operações DB vem do JWT (não de headers externos)

**Boundary com C5 (Multi-tenancy):** C5 documenta o TenantGuard em detalhe e Row-Level Security. I8 foca no fluxo de autenticação, geração de tokens e diferença FastAPI vs Rails JWT.

**Boundary com C6 (Prompt Injection):** O `AuthEnforcementMiddleware` também executa o guard de prompt injection em AGENT_PATHS antes de autenticar — documentado em C6. I8 foca na parte de auth/JWT do middleware.

---

## Arquivos conectados (9 total)

### Camada Código

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `dependencies.py` | `app/auth/dependencies.py` | Dependências FastAPI: get_current_user, strict, demo, service |
| `security.py` | `app/auth/security.py` | bcrypt, JWT encode/decode, token creation |
| `models.py` | `app/auth/models.py` | User model com PII encryption + UserRole |
| `rails_jwt.py` | `app/auth/rails_jwt.py` | Validação de tokens Rails + cache /v1/me |
| `schemas.py` | `app/auth/schemas.py` | Pydantic schemas: LoginRequest, TokenResponse, etc. |
| `workos_models.py` | `app/auth/workos_models.py` | WorkOSGroup, Membership, RoleMapping, SSOAuditLog |
| `workos_schemas.py` | `app/auth/workos_schemas.py` | Pydantic schemas para SSO/SCIM events |
| `auth_enforcement.py` | `app/middleware/auth_enforcement.py` | Middleware global: JWT validation + state injection |
| `auth.py` (shim) | `app/core/auth.py` | Re-export shim → app/auth/dependencies.py |
| `tenant_guard.py` | `app/shared/tenant_guard.py` | `get_verified_company_id()` FastAPI dependency |

### Integration points

- **`AuthEnforcementMiddleware`** registrado em `app/api/routes.py` como primeiro middleware
- **`get_verified_company_id`** consumido por todos os endpoints que fazem operações DB com company_id
- **`get_current_user`** / `get_current_user_strict` consumidos por 100+ endpoints via `Depends()`
- **Rails JWT** integra com `fetch_rails_user_info()` → Rails `/v1/me` endpoint
- **`prime_tenant_llm_cache(jwt_company_id)`** chamado em `AuthEnforcementMiddleware` para pre-aquecimento do cache BYOK

---

## User Model

### Estrutura (`app/auth/models.py`)

```python
class UserRole(StrEnum):
    admin = "admin"
    recruiter = "recruiter"
    viewer = "viewer"
    dpo = "dpo"   # Task #511 — LGPD Art. 41 / EU AI Act — acesso a audit trails
                  # sem privilégios admin amplos

class User(EncryptedFieldMixin, Base):
    __tablename__ = "users"

    # PII encryption: email nunca persiste em plaintext post-migration 060
    # "_email_raw" → hybrid_property "email" via EncryptedFieldMixin
    _pii_encrypt_fields = [
        ("_email_raw", "_email_encrypted", "email_hash"),
    ]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    _email_raw = Column("email", String(255), nullable=True)       # NULL em novas escritas
    _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)  # Fernet
    email_hash = Column(String(64), nullable=True, unique=True, index=True)   # SHA-256
    password_hash = Column(String(255), nullable=True)             # bcrypt
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer)
    company_id = Column(String(255), nullable=True, index=True)    # tenant identifier
    is_active = Column(Boolean, default=True)
    permissions = Column(ARRAY(String), default=[], nullable=False)
    
    # WorkOS SSO fields
    workos_id = Column(String(255), unique=True, nullable=True, index=True)
    workos_directory_id = Column(String(255), nullable=True, index=True)
    workos_organization_id = Column(String(255), nullable=True, index=True)
    sso_provider = Column(String(100), nullable=True)
    is_scim_managed = Column(Boolean, default=False)
    azure_ad_object_id = Column(String(255), nullable=True, index=True)
    last_sso_login_at = Column(DateTime, nullable=True)
    
    # Email verification + password reset
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    invitation_token = Column(String(255), nullable=True)
```

### Métodos de negócio

```python
def can_access_company(self, company_id: str) -> bool:
    """Admin bypassa verificação. Outros devem pertencer ao company."""
    if self.role == UserRole.admin:
        return True
    return self.company_id == company_id

def get(self, key: str, default=None):
    """Dict-like access para 100+ endpoints que usam current_user.get('user_id').
    Aliases: 'user_id', 'sub' → 'id'.
    """
    attr_map = {"user_id": "id", "sub": "id", "id": "id"}
    attr = attr_map.get(key, key)
    return getattr(self, attr, default)
```

### Lookup de email (transição pré/pós-migration 060)

```python
# Sempre usar OR para compatibilidade durante migração:
select(User).where(
    or_(
        User.email_hash == _sha256_hash(email),
        User._email_raw == email,      # linhas antigas (pré-migração)
    )
)
```

---

## FastAPI JWT — geração e validação

### Criação de token (`app/auth/security.py`)

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(
    subject: str,           # user.id como string (UUID)
    role: str | None = None,
    company_id: str | None = None,
    expires_delta: timedelta | None = None
) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "role": role,
        "company_id": company_id,    # ← company_id DENTRO do payload
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

**company_id está no payload JWT** — não precisa de lookup externo.

### Decodificação

```python
def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    # Lança JWTError se expirado ou assinatura inválida
```

### Senhas

```python
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

---

## Rails JWT — validação e auto-provisionamento

### Formato do token Rails (`app/auth/rails_jwt.py`)

```python
# Payload: {"user_id": 123, "exp": 1234567890}
# Algorithm: HS256
# Secret: RAILS_JWT_SECRET_KEY (compartilhado com Rails app)

@dataclass
class RailsTokenPayload:
    user_id: int
    exp: datetime
    # NÃO tem company_id — resolvido via /v1/me
    raw: dict
```

### Validação

```python
def validate_rails_token(
    token: str,
    rails_secret_key: str,
    algorithm: str = "HS256",
) -> RailsTokenPayload | None:
    payload = jwt.decode(
        token,
        rails_secret_key,
        algorithms=[algorithm],
        options={"verify_aud": False},   # Rails usa aud="wedo-agent"; não valida
    )
    # Retorna None em qualquer JWTError ou falta de user_id

def validate_rails_token_from_env(token: str) -> RailsTokenPayload | None:
    """Lê RAILS_JWT_SECRET_KEY do ambiente."""
    secret = get_rails_jwt_secret()   # settings.RAILS_JWT_SECRET_KEY
    if not secret: return None
    return validate_rails_token(token, secret)
```

### Busca de user_info via /v1/me

```python
_RAILS_ME_CACHE: dict[int, dict] = {}
_RAILS_ME_CACHE_TTL_SECONDS = 300   # 5 minutos

async def fetch_rails_user_info(token: str, user_id: int) -> dict | None:
    # Verifica cache _RAILS_ME_CACHE[user_id]
    # GET {RAILS_API_URL}/v1/me com Bearer token
    # Retorna: {email, name, account_id, is_admin}
    # None em falha
```

### Auto-provisionamento de User FastAPI

```python
# app/auth/dependencies.py — _resolve_rails_jwt_user()

async def _resolve_rails_jwt_user(token: str, db: AsyncSession) -> User | None:
    rails_payload = validate_rails_token_from_env(token)
    if rails_payload is None: return None

    info = await fetch_rails_user_info(token, rails_payload.user_id)
    if not info or not info.get("email"): return None

    email = info["email"]
    email_hash = _sha256_hash(email)

    result = await db.execute(select(User).where(User.email_hash == email_hash))
    user = result.scalar_one_or_none()

    if user is not None:
        # Auto-heal: preenche company_id/role ausentes
        if not user.company_id and info.get("account_id"):
            user.company_id = str(info["account_id"])
        if info.get("is_admin") and user.role != UserRole.admin:
            user.role = UserRole.admin
        return user

    # Auto-provisiona: cria User FastAPI espelhando Rails
    user = User(
        id=uuid4(),
        email=info["email"],
        name=info.get("name", ""),
        password_hash="",   # SSO user — não usa password
        role=UserRole.admin if info.get("is_admin") else UserRole.recruiter,
        company_id=str(info.get("account_id") or ""),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

### Fail-closed para company_id Rails

```python
class RailsCompanyResolutionError(Exception):
    """LIA-SEC-02 (PE-9): callers DEVEM tratar e rejeitar a requisição.
    NÃO fazer fallback para company_id padrão — quebra isolamento de tenant."""

async def resolve_company_from_rails_user(user_id: int, ats_client) -> str:
    # Chama /v1/me
    # Se falhar → RailsCompanyResolutionError (nunca retorna default)
```

---

## Dependências FastAPI

### Hierarquia de 4 dependências

```python
# app/auth/dependencies.py

# 1. PADRÃO — usa em 90% dos endpoints
async def get_current_user(
    credentials = Depends(security),   # HTTPBearer
    db = Depends(get_db)
) -> User:
    # FastAPI JWT → Rails JWT fallback
    # Aceita qualquer token válido

# 2. STRICT — para endpoints sensíveis (compliance, billing, LGPD, audit)
async def get_current_user_strict(
    credentials = Depends(security),
    db = Depends(get_db)
) -> User:
    # FastAPI JWT → Rails JWT fallback
    # SEM demo fallback (ao contrário de get_current_user_or_demo)
    # Levanta HTTP 403 se user.is_active == False

# 3. DEMO — para desenvolvimento e demos
async def get_current_user_or_demo(
    credentials = Depends(optional_security),  # Bearer opcional
    db = Depends(get_db)
) -> User:
    # FastAPI JWT → Rails JWT → demo user
    # Demo user só criado em _is_dev_environment() — 403 em produção
    # ensure_demo_user() é idempotente + repara password_hash inválido

# 4. SERVICE — para chamadas server-to-server
async def get_service_or_user(
    credentials = Depends(optional_security),
    db = Depends(get_db)
) -> User:
    # Verifica credentials.credentials == SERVICE_API_TOKEN (env var)
    # Se match → retorna service account (admin role, email service@wedotalent.com)
    # Se não → get_current_user normal
```

**Uso correto por contexto:**

| Contexto | Dependency |
|---------|-----------|
| Endpoint normal (vagas, candidatos, chat) | `get_current_user` |
| Endpoint LGPD Art. 20, compliance, billing, audit | `get_current_user_strict` |
| Endpoint frontend com demo user | `get_current_user_or_demo` |
| Webhook interno / jobs / scheduler | `get_service_or_user` |

### `app/core/auth.py` (shim)

```python
# NUNCA importar de app.core.auth em código novo
# Importar diretamente de app.auth.dependencies
from app.auth.dependencies import (
    get_current_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
```

---

## AuthEnforcementMiddleware

### Fluxo completo (`app/middleware/auth_enforcement.py`)

```
Requisição entra
    ↓
1. path ∈ PUBLIC_PATHS ou path.startswith(PUBLIC_PREFIXES)?
   Sim → pass-through imediatamente
    ↓
2. method == "OPTIONS"?
   Sim → pass-through (CORS preflight)
    ↓
3. POST/PUT + path.startswith(AGENT_PATHS) + application/json?
   Sim → _check_input_security(body) para prompt injection
   Se blocked → return 400 (fail-closed)
   Reconstrói request com body consumido
    ↓
4. Authorization: Bearer <token>?
   Não e _DEV_MODE:
     → valida X-Dev-Api-Key (fail-closed se LIA_DEV_API_KEY não configurado)
     → injeta synthetic user (company_id=DEMO_COMPANY_UUID, role=admin)
   Não e não _DEV_MODE → return 401
    ↓
5. decode_token(token) → FastAPI JWT
   Falhou → validate_rails_token_from_env(token) + fetch_rails_user_info()
    ↓
6. Injeta em request.state:
   - token_payload: dict (payload JWT completo)
   - user_id: str (sub do JWT ou email para Rails)
   - company_id: str (do JWT ou de /v1/me para Rails)
   - user_role: str
   Seta ContextVar _current_company_id (usado por get_db para RLS)
    ↓
7. prime_tenant_llm_cache(jwt_company_id) — pré-aquece cache BYOK
    ↓
8. X-Company-ID header ≠ JWT company_id → 403 "company mismatch"
    ↓
9. call_next(request) → endpoint recebe request.state preenchido
```

### PUBLIC_PATHS e PUBLIC_PREFIXES

```python
PUBLIC_PATHS = {
    "/health", "/docs", "/openapi.json",
    "/api/v1/auth/login", "/api/v1/auth/register",
    "/api/v1/auth/refresh", "/api/v1/auth/forgot-password",
    "/api/v1/auth/workos-callback", "/api/v1/auth/workos/callback",
    "/api/v1/data-request",           # LGPD data request (público)
    "/api/v1/webhooks/whatsapp",
    "/api/v1/navigation-intent",      # Float chat nav (não precisa auth)
    "/api/v1/calendar/google/callback",  # OAuth callbacks (CSRF via HMAC state)
    "/api/v1/calendar/microsoft/callback",
    # ... (27 paths total)
}

PUBLIC_PREFIXES = (
    "/api/v1/teams/",      # webhooks Teams
    "/api/v1/auth/invitation-info/",
    "/api/v1/wsi/async/",  # WSI async callbacks
    "/api/public/",
    "/ws/",                # WebSocket upgrade (auth dentro do WS)
)
```

### DEV_MODE (fail-closed desde LIA-SEC-01)

```python
_DEV_MODE = os.environ.get("LIA_DEV_MODE", "").lower() in ("1", "true", "yes")
_DEV_API_KEY = os.environ.get("LIA_DEV_API_KEY", "")

# LIA-SEC-01: Se DEV_MODE ativo mas LIA_DEV_API_KEY não configurado → rejeita
# ANTES era só um warning e permitia — agora é fail-closed
if _DEV_MODE and not _DEV_API_KEY:
    # return JSONResponse({"detail": "DEV_MODE misconfigured"}, status_code=401)
```

---

## get_verified_company_id — dependency canônica

```python
# app/shared/tenant_guard.py

def get_verified_company_id(
    request: Request,
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    company_id: str | None = Query(None),
) -> str:
    """
    Uso padrão em endpoints que precisam de company_id:
    
        @router.get("/jobs")
        async def list_jobs(
            company_id: str = Depends(get_verified_company_id),
            current_user: User = Depends(get_current_user),
        ):
    """
    jwt_company = getattr(request.state, "company_id", None)
    requested_company = x_company_id or company_id

    if jwt_company:
        if requested_company and requested_company != jwt_company:
            raise HTTPException(403, "Access denied: company mismatch")
        return jwt_company   # JWT sempre vence

    # Em produção: rejeita se não tem JWT
    if is_production and not jwt_company:
        raise HTTPException(401, "JWT com company context obrigatório")

    # Dev: usa header/query como fallback
    if requested_company:
        return requested_company

    raise HTTPException(401, "Company ID required")
```

**Regra absoluta:** todo endpoint que faz operação DB com `company_id` usa `get_verified_company_id`. Nunca `request.headers.get("X-Company-ID")` diretamente.

---

## WorkOS / SSO (`app/auth/workos_models.py`)

```python
class WorkOSGroup(Base):
    """SCIM Group provisionado via WorkOS Directory Sync."""
    workos_id: str          # ID único do grupo no WorkOS
    directory_id: str       # WorkOS Directory ID
    name: str
    memberships: list[WorkOSGroupMembership]
    role_mappings: list[WorkOSGroupRoleMapping]

class WorkOSGroupMembership(Base):
    """Usuário ↔ Grupo SCIM."""
    group_id: UUID          # FK workos_groups.id
    user_id: UUID           # FK users.id
    added_at: DateTime

class WorkOSGroupRoleMapping(Base):
    """Grupo SCIM → Role na aplicação (por empresa)."""
    company_id: str         # mapeamento é por tenant
    workos_group_id: UUID
    role: str               # admin/recruiter/viewer/dpo
    permissions: list[str]  # permissões adicionais

class SSOAuditLog(Base):
    """Trilha de auditoria para eventos SSO/SCIM."""
    # Registra login, provisioning, deprovisioning de usuários SSO
```

### Campos User para SSO

```python
workos_id = Column(String(255), unique=True, nullable=True, index=True)
workos_directory_id = Column(String(255), nullable=True, index=True)
workos_organization_id = Column(String(255), nullable=True, index=True)
sso_provider = Column(String(100), nullable=True)    # "google", "microsoft", "okta", etc.
is_scim_managed = Column(Boolean, default=False)      # True = gerenciado via SCIM
azure_ad_object_id = Column(String(255), nullable=True, index=True)
```

---

## Instruções para Claude Code / Cursor

### "Implementa auth no v5"

**Passo 1 — User Model:**
```python
# 1. Cria app/auth/models.py com UserRole (admin, recruiter, viewer, dpo)
# 2. User model com company_id (multi-tenancy)
# 3. Inclui EncryptedFieldMixin se LGPD compliance é necessário:
#    _pii_encrypt_fields = [("_email_raw", "_email_encrypted", "email_hash")]
# 4. Método can_access_company(company_id) — admin bypass
# 5. Método get(key) — alias user_id/sub → id para compatibilidade
```

**Passo 2 — Security:**
```python
# 6. security.py:
#    - bcrypt para senhas
#    - create_access_token(subject, role, company_id) — INCLUI company_id no payload
#    - decode_token(token) → dict
#    - Expiração: ACCESS=30min, REFRESH=7d

# CRÍTICO: company_id NO payload JWT — não via lookup adicional
```

**Passo 3 — Rails JWT (se integração Rails necessária):**
```python
# 7. rails_jwt.py:
#    - validate_rails_token_from_env(token) → RailsTokenPayload | None
#    - fetch_rails_user_info(token, user_id) — com cache 5 min
#    - RailsCompanyResolutionError — fail-closed (não usar default company_id)
```

**Passo 4 — Dependências FastAPI:**
```python
# 8. dependencies.py:
#    - get_current_user() — FastAPI JWT → Rails JWT
#    - get_current_user_strict() — sem demo fallback (LGPD, compliance)
#    - get_service_or_user() — SERVICE_API_TOKEN
```

**Passo 5 — Middleware global:**
```python
# 9. auth_enforcement.py:
#    - AuthEnforcementMiddleware extends BaseHTTPMiddleware
#    - PUBLIC_PATHS: set de paths sem auth
#    - Inject request.state.company_id, user_id, token_payload
#    - DEV_MODE: LIA_DEV_MODE + LIA_DEV_API_KEY (fail-closed)
#    - X-Company-ID header mismatch → 403
```

**Passo 6 — TenantGuard:**
```python
# 10. tenant_guard.py:
#     - get_verified_company_id() dependency
#     - JWT sempre vence sobre header/query
#     - Produção: rejeita sem JWT
```

### "Adiciona endpoint ao v5 com auth"

```python
@router.get("/resource/{id}")
async def get_resource(
    id: str,
    company_id: str = Depends(get_verified_company_id),   # company_id do JWT
    current_user: User = Depends(get_current_user),        # usuário autenticado
    db: AsyncSession = Depends(get_db),
):
    resource = await db.get(Resource, id)
    if resource.company_id != company_id:
        raise HTTPException(403, "Access denied")
    return resource
```

### "Adiciona endpoint sensível (compliance/LGPD)"

```python
@router.get("/audit-trail")
async def get_audit_trail(
    company_id: str = Depends(get_verified_company_id),
    current_user: User = Depends(get_current_user_strict),  # ← strict, sem demo
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (UserRole.admin, UserRole.dpo):
        raise HTTPException(403, "DPO or admin required")
    ...
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Auth — v5

- **JWT payload:** inclui company_id — não fazer lookup extra
- **Dual-token:** FastAPI JWT (sub=UUID) → Rails JWT (user_id=int) fallback
- **company_id:** sempre de get_verified_company_id() — NUNCA de header direto
- **Strict endpoints:** LGPD/compliance/audit usam get_current_user_strict (sem demo)
- **Middleware:** AuthEnforcementMiddleware injeta request.state.company_id
- **User.can_access_company():** admin bypass; outros devem pertencer ao company
- **UserRole.dpo:** LGPD Art. 41 — acesso a audit sem admin amplo
- **LIA_DEV_MODE + LIA_DEV_API_KEY:** ambos necessários para dev mode (fail-closed)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| O que | Como adaptar |
|-------|-------------|
| `RAILS_JWT_SECRET_KEY` | Renomear ou remover se não há integração Rails |
| Cache TTL de 5 min (`_RAILS_ME_CACHE_TTL_SECONDS`) | Ajustar conforme latência Rails |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Ajustar para política de segurança do cliente |
| `PUBLIC_PATHS` | Adicionar/remover paths públicos do v5 |
| `AGENT_PATHS` para prompt injection | Ajustar para os endpoints LLM do v5 |
| `WorkOSGroup` / SSO | Remover se não usar WorkOS SSO |
| `UserRole.viewer` / `UserRole.dpo` | Adicionar roles do v5 |
| `ensure_demo_user()` | Trocar email/nome da conta demo |

### NÃO pode adaptar (base arquitetural)

| O que | Por quê |
|-------|---------|
| **company_id DENTRO do payload JWT** | Mudar para lookup externo cria latência + risco de race condition em multi-tenant. O payload JWT é SSoT do company_id para a vida do request. |
| **`get_verified_company_id()` como dependency canônica** | Se alguns endpoints leem company_id de header diretamente e outros de JWT, o sistema perde isolamento de tenant. TODA operação DB com company_id deve passar por esta dependency. |
| **`get_current_user_strict()` em endpoints sensíveis** | LGPD Art. 20 (direito de contestação), audit trails, billing devem rejeitar em produção se o token falhar — demo fallback cria buracos de segurança em operações que têm consequências legais. |
| **fail-closed em DEV_MODE** (LIA-SEC-01) | O fix original desta vulnerabilidade foi exatamente o oposto — antes era open. Reverter cria bypass de autenticação em staging. |
| **RailsCompanyResolutionError fail-closed** (LIA-SEC-02, PE-9) | Não usar default/fallback quando /v1/me falha. Um default "company_id vazio" ou "admin company" seria vazamento de dados cross-tenant. |
| **`UserRole.dpo`** | Task #511 — LGPD Art. 41 requer separação entre DPO e admin. Remover rompe compliance. |
| **Email PII encryption** (`EncryptedFieldMixin`) | LGPD Art. 46 — dados pessoais devem ser protegidos por medidas técnicas. `email_hash` é necessário para lookup eficiente sem expor PII. |

---

## Checklist de completude

- [ ] (P0) company_id incluído no payload do access token JWT
- [ ] (P0) `get_verified_company_id()` usado em TODOS os endpoints com company scope
- [ ] (P0) `get_current_user_strict()` em endpoints LGPD/compliance/audit
- [ ] (P0) DEV_MODE fail-closed: `LIA_DEV_API_KEY` obrigatório quando `LIA_DEV_MODE=1`
- [ ] (P0) `RailsCompanyResolutionError` — nunca retorna default company_id
- [ ] (P1) `UserRole.dpo` definido (LGPD Art. 41)
- [ ] (P1) Email com `EncryptedFieldMixin` ou equivalente (LGPD Art. 46)
- [ ] (P1) `AuthEnforcementMiddleware` registrado como primeiro middleware
- [ ] (P1) X-Company-ID header mismatch com JWT → 403
- [ ] (P1) `_RAILS_ME_CACHE` com TTL (evita flood de /v1/me)
- [ ] (P1) Auto-provisioning de User FastAPI para tokens Rails
- [ ] (P2) `app/core/auth.py` como shim (backward compat para imports legados)
- [ ] (P2) `WorkOSGroup` / SSO audit log se WorkOS SSO usado
- [ ] (P2) `prime_tenant_llm_cache(jwt_company_id)` no middleware (pre-aquece BYOK cache)
- [ ] (P2) Lookup de email com OR(email_hash, _email_raw) durante período de migração

---

## Gotchas e erros comuns

### 1. company_id de header sem validação JWT

```python
# ❌ NUNCA fazer isso
company_id = request.headers.get("X-Company-ID")  # Qualquer um pode forjar

# ✅ Sempre usar dependency
company_id: str = Depends(get_verified_company_id)
```

### 2. Usar get_current_user em endpoint de audit

```python
# ❌ Demo fallback pode criar false audit entries
current_user: User = Depends(get_current_user)

# ✅ Strict para LGPD e audit
current_user: User = Depends(get_current_user_strict)
```

### 3. Rails JWT sem RAILS_JWT_SECRET_KEY configurado

`validate_rails_token_from_env()` retorna `None` silenciosamente se `RAILS_JWT_SECRET_KEY` não estiver configurado. Isso não gera erro — apenas ignora tokens Rails. Em ambientes onde o login vem exclusivamente do Rails, isso resulta em 401 para todos os usuários.

### 4. DEV_MODE sem LIA_DEV_API_KEY

Antes do LIA-SEC-01 fix, `LIA_DEV_MODE=1` sem chave permitia qualquer requisição. Agora rejeita com 401 se chave não configurada. Em staging Replit, sempre setar `LIA_DEV_API_KEY`.

### 5. Admin cross-tenant acidental

`can_access_company()` retorna `True` para admin mesmo com company_id diferente. Ao criar recursos admin (templates globais, configs sistema), verificar explicitamente se a operação é cross-tenant intencional. Usar `assert_admin_cross_tenant_access()` para auditoria.

### 6. Email lookup pós-migration 060

Não usar `User.email == email_address` — coluna pode ser NULL pós-migration. Sempre usar `OR(email_hash, _email_raw)` ou `User.email == email_address` via hybrid_property (que internamente usa o OR).

### 7. Endpoint de WebSocket

Path `/ws/` é `PUBLIC_PREFIXES` — o WebSocket upgrade não tem Bearer token no handshake HTTP. Auth deve ser feita dentro do protocolo WS (ver I6 WSManager). Não adicionar `/ws/` ao fluxo de auth normal.

---

## Testes obrigatórios

```
tests/unit/auth/test_security.py
  - test_create_access_token_includes_company_id
  - test_decode_token_valid
  - test_decode_token_expired
  - test_verify_password_correct
  - test_verify_password_wrong

tests/unit/auth/test_rails_jwt.py
  - test_validate_rails_token_valid
  - test_validate_rails_token_expired
  - test_validate_rails_token_missing_user_id → None
  - test_validate_rails_token_from_env_no_secret → None
  - test_resolve_company_fail_closed: RailsCompanyResolutionError se /v1/me falha

tests/unit/auth/test_dependencies.py
  - test_get_current_user_fastapi_jwt
  - test_get_current_user_rails_fallback
  - test_get_current_user_strict_no_demo
  - test_get_current_user_strict_inactive_user → 403

tests/unit/shared/test_tenant_guard.py
  - test_get_verified_company_id_from_jwt
  - test_get_verified_company_id_header_mismatch → 403
  - test_get_verified_company_id_production_no_jwt → 401

tests/integration/test_auth_enforcement_middleware.py
  - test_public_path_no_auth_required
  - test_protected_path_no_token → 401
  - test_dev_mode_without_api_key → 401 (LIA-SEC-01)
  - test_cross_tenant_header_mismatch → 403
  - test_rails_jwt_accepted
  - test_user_auto_provisioned_from_rails_token
```

---

## Referências

- **Multi-tenancy enforcement:** `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md` (TenantGuard, RLS)
- **Prompt injection no middleware:** `themes/compliance/C6_PROMPT_INJECTION_AND_ENCRYPTION.md`
- **Candidate Portal auth (LGPD Art. 20):** `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md`
- **Data Layer:** `themes/infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md` (get_db + RLS)
- **Middleware lifecycle:** `themes/infrastructure/I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md`
- **LGPD Art. 46** — Segurança de dados pessoais (justifica email encryption)
- **LGPD Art. 41** — DPO como role separado
- **LIA-SEC-01:** Comentário no AuthEnforcementMiddleware — DEV_MODE fail-closed
- **LIA-SEC-02 (PE-9):** Comentário em `RailsCompanyResolutionError` — Rails company fail-closed
