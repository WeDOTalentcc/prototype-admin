# Theme: I9 — Data Layer / Database / Migrations — Infrastructure Layer

## O que é este tema

O Data Layer abrange toda a infraestrutura de persistência: engine PostgreSQL assíncrona, gestão de sessão com RLS, Redis para cache/Pub-Sub, 95 migrações Alembic sequenciais, 120 modelos SQLAlchemy em `libs/models/lia_models/`, e o padrão de repositório.

**Dois componentes críticos que tornam o multi-tenancy automático:**
1. **Row-Level Security (RLS) PostgreSQL** — migration 068 ativa RLS em 80+ tabelas com `DENY BY DEFAULT`; qualquer query via `lia_app` role é automaticamente filtrada por `company_id = app_current_company_id()`
2. **ContextVar `_current_company_id`** — injetado pelo `AuthEnforcementMiddleware` a cada request; `get_db()` usa este valor para chamar `SET app.company_id` na sessão PostgreSQL antes de yield

O desenvolvedor v5 não precisa filtrar company_id manualmente nas queries — desde que use `get_db()` corretamente, o PostgreSQL faz isso na camada de banco.

**Boundary com C5 (Multi-tenancy):** C5 documenta a regra de negócio e enforcement. I9 documenta o mecanismo técnico: RLS, como as sessões injetam o company_id, e como os models são estruturados.

**Boundary com I8 (Auth):** I8 documenta como o JWT é validado e como `request.state.company_id` é preenchido. I9 documenta o que acontece depois: `_current_company_id` ContextVar → `get_db()` → `SET app.company_id`.

---

## Arquivos conectados (11 total)

### Camada Config / Engine

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `database.py` (real) | `libs/config/lia_config/database.py` | engine, Base, get_db, async_session_factory, get_tenant_aware_session |
| `database.py` (shim) | `app/core/database.py` | Re-export + helpers: set_tenant_context, get_tenant_db, migration helpers |
| `redis_client.py` | `app/core/redis_client.py` | get_redis (singleton), get_redis_connection (per-call), close_redis |
| `alembic.ini` | `alembic.ini` | Alembic config: script_location, DB URL padrão |
| `env.py` | `alembic/env.py` | Alembic runtime: async migration runner, target_metadata, get_url() |

### Camada Migrações

| Path | Quantidade | Cobertura |
|------|-----------|-----------|
| `alembic/versions/001_*.py` → `095_*.py` | 95 migrações | schema completo desde início (gaps: 036, 038, 039) |

### Camada Modelos

| Path | Quantidade | Base |
|------|-----------|------|
| `libs/models/lia_models/*.py` | 121 arquivos | `lia_config.database.Base` |

### Camada Repositórios

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `base.py` | `app/shared/repositories/base.py` | `BaseRepository` ABC (generic T) |
| `sqlalchemy_base.py` | `app/shared/repositories/sqlalchemy_base.py` | `SQLAlchemyRepository` implementation |
| Repositórios domain | `app/domains/<X>/repositories/*.py` | 40+ repositórios específicos por domain |

### Integration points

- **`AuthEnforcementMiddleware`** seta `_current_company_id` ContextVar → `get_db()` usa
- **`get_db()`** é FastAPI dependency injetada em 100+ endpoints e repositórios
- **Redis** é usado por: WSManager (Pub/Sub), CascadedRouter (cache tiers 1-3), TenantBudget, WizardState
- **Alembic** roda via `alembic upgrade head` em deployment

---

## Engine PostgreSQL e sessão

### Configuração do engine (`libs/config/lia_config/database.py`)

```python
from lia_config.config import settings

# URL: converte postgresql:// → postgresql+asyncpg:// para async
# Strip sslmode= (asyncpg não suporta)
database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

engine = create_async_engine(
    database_url,
    pool_size=settings.DATABASE_POOL_SIZE,      # de settings
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,     # detecta conexões mortas
    pool_recycle=3600,      # recicla conexões a cada 1h
    echo=settings.DEBUG,    # log SQL em DEBUG
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # não expira objetos após commit (evita lazy-load erros)
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()   # shared por todos os 120 modelos
```

### `get_db()` — dependency FastAPI com RLS automático

```python
# libs/config/lia_config/database.py

def _get_current_company_id() -> str:
    """Lê ContextVar injetado pelo AuthEnforcementMiddleware."""
    from app.middleware.auth_enforcement import _current_company_id
    return _current_company_id.get("")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            # 1. Reset role primeiro (sessão pode estar em estado anterior)
            try:
                await session.execute(sa.text("RESET ROLE"))
            except Exception:
                pass

            # 2. Se tem company_id no ContextVar → ativa RLS
            _cid = _get_current_company_id()
            if _cid:
                # SET ROLE lia_app: ativa as políticas RLS (role não-superuser)
                try:
                    await session.execute(sa.text("SET ROLE lia_app"))
                except Exception as role_err:
                    logger.error("[RLS] SET ROLE lia_app failed — request blocked (fail-closed)")
                    raise RuntimeError("RLS role enforcement failed") from role_err

                # SET app.company_id: valor lido por app_current_company_id() function
                await session.execute(
                    sa.text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": _cid},
                )

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.execute(sa.text("RESET ROLE"))
            except Exception:
                pass
            await session.close()
```

### `get_tenant_aware_session()` — para background tasks

```python
# Quando o código não tem acesso ao request FastAPI (jobs, tools, background tasks)
# mas o company_id já está no ContextVar

@asynccontextmanager
async def get_tenant_aware_session():
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(sa.text("RESET ROLE"))
            _cid = _get_current_company_id()
            if _cid:
                await session.execute(sa.text("SET ROLE lia_app"))
                await session.execute(
                    sa.text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": _cid},
                )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Uso:**
```python
async with get_tenant_aware_session() as db:
    jobs = await db.execute(select(JobVacancy))
    # RLS filtra por company_id automaticamente
```

### `app/core/database.py` — shim + helpers

```python
# Re-exporta de lia_config.database
from lia_config.database import (
    AsyncSessionLocal, Base, async_session_factory, engine,
    get_db, get_tenant_aware_session,
)

# Funções adicionais de migration (executadas no startup)
async def set_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Injeção manual de company_id (para get_tenant_db com Request)."""
    await db.execute(sa.text("SELECT set_config('app.company_id', :cid, true)"), {"cid": str(company_id)})

async def get_tenant_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Versão alternativa de get_db que lê company_id de request.state."""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(sa.text("SET ROLE lia_app"))
            company_id = getattr(request.state, "company_id", None)
            if company_id:
                await set_tenant_context(session, company_id)
            yield session
            await session.commit()
        ...
```

---

## Row-Level Security (RLS)

### Migration 068 — `rls_deny_by_default`

**A migração mais crítica para multi-tenancy.** Executa 4 operações principais:

```sql
-- 1. Função PL/pgSQL SSoT para company_id da sessão
CREATE OR REPLACE FUNCTION app_current_company_id() RETURNS TEXT AS $$
BEGIN
    RETURN NULLIF(current_setting('app.company_id', true), '');
END;
$$ LANGUAGE plpgsql STABLE;

-- 2. Role lia_app (NOLOGIN, NOSUPERUSER) — necessário para FORCE ROW LEVEL SECURITY
CREATE ROLE lia_app NOLOGIN NOSUPERUSER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lia_app;

-- 3. Para cada tabela: ativa RLS com DENY BY DEFAULT
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;  -- superusers também ficam sujeitos

-- 4. Políticas tenant: SELECT/INSERT/UPDATE/DELETE filtram por company_id
CREATE POLICY {table}_tenant_select ON {table}
    FOR SELECT
    USING (company_id = app_current_company_id());

CREATE POLICY {table}_tenant_insert ON {table}
    FOR INSERT
    WITH CHECK (company_id = app_current_company_id());
```

### Fluxo completo RLS por request

```
HTTP Request
    ↓ AuthEnforcementMiddleware
    → decode JWT → company_id extraído
    → _current_company_id.set(company_id)   ← ContextVar
    ↓ FastAPI endpoint
    → get_db() chamado
    → SET ROLE lia_app                        ← ativa enforcement
    → SET app.company_id = 'company-uuid'    ← valor para function
    ↓ SQL query
    → SELECT * FROM job_vacancies
    → PostgreSQL checa: WHERE company_id = app_current_company_id()
    → retorna APENAS linhas do tenant
```

### 80+ tabelas com RLS ativo (amostra)

`job_vacancies`, `job_drafts`, `candidates`, `candidate_job`, `audit_logs`, `recruitment_stages`, `pipeline_templates`, `communication_history`, `lgpd_consents`, `agent_execution_records`, `sourcing_agents`, `digital_twins`, `recruitment_campaigns`, `talent_pool_candidates`, `job_vacancies`, `fairness_audit_log` (implementado manualmente em 015 — precede 068), `company_hiring_policies`, `credit_accounts`, e mais ~60 tabelas.

---

## Redis Client

```python
# app/core/redis_client.py

# Singleton (lazy init) — para operações simples de get/set
async def get_redis():
    global _redis_client
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
    return _redis_client

# Por-chamada — para uso como async context manager
async def get_redis_connection() -> redis.Redis | None:
    url = settings.REDIS_URL
    return aioredis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=0.5,   # fail-fast
        socket_timeout=0.5,
    )

# Shutdown
async def close_redis() -> None:
    if _redis_client: await _redis_client.aclose()
```

**Formatos de URL suportados:**
- `redis://localhost:6379` — sem auth
- `redis://:password@host:6379/0` — auth com password
- `redis://user:password@host:6379/0` — user + password
- `rediss://:token@managed.host:6380/0` — TLS com auth (Cloud Memorystore)

**Consumidores de Redis no sistema:**
- `WSManager` (I6) — Pub/Sub para multi-worker broadcasting
- `CascadedRouter` (I3) — Tiers 1-2 (in-process LRU + Redis hash cache)
- `VectorSemanticCache` (I3) — Tier 3 cache de pgvector
- `TenantBudget` (I3) — contadores de uso por tenant
- `WizardState` (I3) — estado TTL=7200s
- `CircuitBreaker` (R1) — estado dos breakers

---

## Alembic — estrutura de migrações

### Configuração

```ini
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db
```

**Em runtime:** `get_url()` em `alembic/env.py` lê `DATABASE_URL` do ambiente (sobrescreve alembic.ini), converte `postgresql://` → `postgresql+asyncpg://`, e strip `sslmode=`.

### `alembic/env.py` — async migrations

```python
# Configura target_metadata importando todos os modelos
from app.core.database import Base
from lia_models.intelligence_layer import IntelligenceInsight, PatternCache, ...
from lia_models.job_vacancy import JobVacancy
from lia_models.candidate import Candidate, VacancyCandidate
# ... ~20 imports de model grupos

target_metadata = Base.metadata  # detecta todas as tabelas automaticamente

async def run_async_migrations() -> None:
    configuration = {"sqlalchemy.url": get_url()}
    connectable = async_engine_from_config(configuration, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

### Convenção de nomes

```
{NNN}_{descrição}.py
```

- 3 dígitos + underscore + snake_case descritivo
- Sequencial: 001 → 095 (95 migrações; gaps confirmados: 036, 038, 039)
- Cada arquivo tem: `revision`, `down_revision`, `upgrade()`, `downgrade()`

### Migrações críticas por tema

| Migration | Tema | O que faz |
|-----------|------|-----------|
| 015 | Compliance/Fairness | `fairness_audit_log` (EU AI Act B-3) |
| 068 | Multi-tenancy | RLS deny-by-default em 80+ tabelas |
| 080 | Multi-tenancy | Migra demo company para UUID canônico |
| 093 | Compliance/LGPD | Adiciona `dpo` ao enum UserRole (LGPD Art. 41) |
| 071 | Observability | `agent_execution_logs` |
| 060 | Compliance/LGPD | PII encryption: `email_encrypted`, `email_hash` em users |
| 005 | Compliance/Fairness | Campos de ação afirmativa em vagas |

### Comandos operacionais

```bash
# Aplicar todas as migrações pendentes
alembic upgrade head

# Criar nova migração (detecta diff do schema)
alembic revision --autogenerate -m "add_my_table"

# Ver status atual
alembic current

# Reverter última migração
alembic downgrade -1

# Reverter para migration específica
alembic downgrade 015_add_fairness_audit_log
```

---

## Modelos SQLAlchemy

### Base pattern (120 modelos em `libs/models/lia_models/`)

```python
# Todos importam de lia_config.database.Base — NÃO de app.core.database.Base
from lia_config.database import Base

class JobVacancy(Base):
    __tablename__ = "job_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)   # RLS key
    
    title = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="Rascunho", index=True)
    stage = Column(String(50), default="Planejamento", index=True)
    
    # Campos estruturados em JSON
    salary_range = Column(JSON, nullable=True)         # {"min": 12000, "max": 18000}
    technical_requirements = Column(JSON, default=list)
    behavioral_competencies = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    
    # Arrays
    requirements = Column(ARRAY(String), default=list)
    benefits = Column(ARRAY(String), default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Catálogo completo por grupo

**Vagas / Recrutamento:**
`job_vacancy.py`, `job_draft.py`, `recruitment_stages.py`, `pipeline_templates.py`, `approval.py`, `candidate.py`, `candidate_job.py`, `candidate_list.py`, `candidate_attachment.py`

**Comunicação:**
`communication.py`, `communication_history.py`, `communication_settings.py`, `communication_matrix.py`

**Agentes / IA:**
`agent_execution_log.py`, `agent_checkpoint.py`, `agent_deployment.py`, `agent_template.py`, `agent_version_snapshot.py`, `agent_approval.py`, `agent_quality_evaluation.py`, `agent_quota.py`

**Compliance / LGPD:**
`audit_log.py`, `affirmative_audit.py`, `bias_audit_snapshot.py`, `consent.py` (via domains)

**Aprendizado:**
`feedback_learning.py` (WizardFeedback, JobOutcome), `calibration.py`, `ab_testing.py`

**Multi-tenancy / Auth:**
`client_account.py`, `client_user.py`, `billing.py`, `company_hiring_policy.py`, `company_benefit.py`, `company_culture.py`, `company_calendar_credentials.py`

**Observabilidade:**
`ai_consumption.py`, `background_jobs.py`, `alert.py`, `archetype.py`

**Intelligence:**
`intelligence_layer.py` (IntelligenceInsight, PatternCache, CorrectionPattern, SuccessProfile, OutcomeCorrelation)

**Sourcing / Search:**
`candidate_feedback.py`, `digital_twin.py`, `talent_pool.py`

---

## Padrão de Repositórios

### `BaseRepository` ABC (`app/shared/repositories/base.py`)

```python
class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: UUID, db) -> T | None: ...
    @abstractmethod
    async def list(self, db, filters=None, limit=50, offset=0, order_by=None) -> list[T]: ...
    @abstractmethod
    async def create(self, db, data: dict[str, Any]) -> T: ...
    @abstractmethod
    async def update(self, db, id: UUID, data: dict[str, Any]) -> T | None: ...
    @abstractmethod
    async def delete(self, db, id: UUID) -> bool: ...
    @abstractmethod
    async def count(self, db, filters=None) -> int: ...
    @abstractmethod
    async def exists(self, db, id: UUID) -> bool: ...
```

### `SQLAlchemyRepository` (`app/shared/repositories/sqlalchemy_base.py`)

```python
class SQLAlchemyRepository(BaseRepository[T]):
    model_class: type = None   # subclasse DEVE definir

    async def get_by_id(self, id: UUID, db: AsyncSession) -> T | None:
        result = await db.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    async def list(self, db, filters=None, limit=50, offset=0, order_by=None) -> list[T]:
        query = select(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).desc())
        elif hasattr(self.model_class, 'created_at'):
            query = query.order_by(self.model_class.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db, data: dict) -> T:
        instance = self.model_class(**data)
        db.add(instance)
        await db.flush()  # gera ID sem commitar — commit feito pelo get_db()
        return instance

    async def update(self, db, id: UUID, data: dict) -> T | None:
        instance = await self.get_by_id(id, db)
        if not instance: return None
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await db.flush()
        return instance

    async def delete(self, db, id: UUID) -> bool:
        instance = await self.get_by_id(id, db)
        if not instance: return False
        await db.delete(instance)
        await db.flush()
        return True
```

**Nota sobre `db.flush()` vs `db.commit()`:** Repositórios usam `flush()` (sincroniza com DB mas não commita a transação). O `commit()` é feito pelo `get_db()` dependency no `finally`. Isso permite múltiplas operações de repositório na mesma transação atomicamente.

### Repositórios compartilhados (`app/shared/repositories/`)

```
base.py              — BaseRepository ABC
sqlalchemy_base.py   — SQLAlchemyRepository implementation
candidate_repository.py  — CandidateRepository
company_repository.py    — CompanyRepository
job_repository.py        — JobRepository
notification_repository.py
```

### Repositórios de domain (`app/domains/<X>/repositories/`)

Cada domain com persistência tem `repositories/` com pelo menos:
- `<domain>_repository.py` — CRUD específico do domain
- `dependencies.py` — FastAPI dependency para injetar repositório

---

## Instruções para Claude Code / Cursor

### "Implementa data layer no v5"

**Passo 1 — Engine:**
```python
# 1. libs/config ou app/core/database.py:
engine = create_async_engine(
    DATABASE_URL,          # postgresql+asyncpg://
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,    # obrigatório para Cloud Run / serverless
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
```

**Passo 2 — get_db() com RLS:**
```python
# 2. Cria ContextVar para company_id (no middleware)
_current_company_id: ContextVar[str] = ContextVar("_current_company_id", default="")

# 3. get_db() que injeta SET ROLE + SET app.company_id
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            cid = _current_company_id.get("")
            if cid:
                await session.execute(text("SET ROLE lia_app"))
                await session.execute(text("SELECT set_config('app.company_id', :cid, true)"), {"cid": cid})
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.execute(text("RESET ROLE"))
            await session.close()
```

**Passo 3 — RLS migration:**
```python
# 4. Cria migration que replica 068_rls_deny_by_default:
#    - CREATE FUNCTION app_current_company_id()
#    - CREATE ROLE lia_app NOLOGIN NOSUPERUSER
#    - GRANT SELECT/INSERT/UPDATE/DELETE TO lia_app
#    - Para cada tabela: ENABLE RLS + FORCE RLS + 4 políticas
```

**Passo 4 — Modelos:**
```python
# 5. Todos os modelos importam de lia_config.database.Base (ou seu equivalente)
# 6. company_id obrigatório: Column(String(255), nullable=False, index=True)
# 7. Timestamps padrão: created_at, updated_at
```

**Passo 5 — Repositórios:**
```python
# 8. Cria BaseRepository ABC + SQLAlchemyRepository
# 9. Por domain: subclass SQLAlchemyRepository com model_class = MyModel
```

### "Cria nova migration"

```bash
# Usando autogenerate (detecta diff do schema)
alembic revision --autogenerate -m "add_new_table"

# Manualmente
alembic revision -m "add_specific_column"

# Convenção de nome: {NNN}_{descrição} onde NNN = próximo número sequencial
```

### "Adiciona campo em tabela existente"

```python
# Novo arquivo alembic/versions/{097}_add_my_field.py

revision = "097_add_my_field"
down_revision = "096_align_self_scheduling_links_table"

def upgrade():
    op.add_column("my_table", sa.Column("my_field", sa.String(255), nullable=True))
    # Se campo tem company_id scope: adicionar índice composto
    op.create_index("ix_my_table_company_field", "my_table", ["company_id", "my_field"])

def downgrade():
    op.drop_index("ix_my_table_company_field")
    op.drop_column("my_table", "my_field")
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Data Layer — v5

- **Engine:** `create_async_engine` com `pool_pre_ping=True, pool_recycle=3600`
- **get_db():** injeta `SET ROLE lia_app` + `SET app.company_id` automaticamente via ContextVar
- **RLS:** migration 068 — `app_current_company_id()` + `FORCE ROW LEVEL SECURITY` em 80+ tabelas
- **flush vs commit:** repositórios usam `db.flush()`, get_db() faz o commit
- **Modelos:** importar de `lia_config.database.Base` — NÃO de `app.core.database.Base`
- **Convenção migration:** `{NNN}_{descrição}.py` sequencial — próximo é 097
- **Redis:** `get_redis()` singleton / `get_redis_connection()` per-call
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| O que | Como adaptar |
|-------|-------------|
| `pool_size` / `max_overflow` | Ajustar conforme carga e provedor (Cloud Run vs VPS) |
| `pool_recycle` (3600s) | Ajustar para timeout do provedor de banco |
| URL do Redis | Qualquer URL redis:// compatível |
| Nomes de tabelas em RLS migration | Adaptar para tabelas do v5 |
| Campos JSON vs JSONB | JSONB para campos que precisam de index/query |
| Tipo de campo company_id (String vs UUID) | Consistência interna — mas manter mesma decisão em todos os modelos |

### NÃO pode adaptar (base arquitetural)

| O que | Por quê |
|-------|---------|
| **`company_id` em TODOS os modelos com dados de tenant** | RLS não funciona sem este campo. Tabela sem company_id = dados compartilhados entre tenants = vazamento. |
| **`ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`** | Sem FORCE, superusers (app user é superuser em muitos setups) bypassam RLS. O conjunto ENABLE+FORCE é inseparável. |
| **`app_current_company_id()` como função PL/pgSQL** | RLS policies precisam de uma função que lê a config de sessão. Não pode ser inline expression (PostgreSQL exige function para `current_setting`). |
| **`SET ROLE lia_app` antes das queries** | Sem o SET ROLE, o usuário da aplicação (que pode ser superuser) bypassa as políticas RLS. É o mecanismo de enforcement. |
| **`expire_on_commit=False` no sessionmaker** | Com expire=True (default), objetos Python ficam expirados após commit, causando lazy-load errors em code async. |
| **`db.flush()` nos repositórios (não commit)** | Se repositório chama commit(), transações que envolvem múltiplos repositórios perdem atomicidade. get_db() é a única fonte de commit. |
| **Importar Base de `lia_config.database`** | Se modelos importam de locais diferentes, `Base.metadata` fica fragmentado e `alembic --autogenerate` não detecta todas as tabelas. |

---

## Checklist de completude

- [ ] (P0) `app_current_company_id()` PL/pgSQL function criada
- [ ] (P0) `lia_app` role criado com grants em todas as tabelas
- [ ] (P0) RLS `ENABLE` + `FORCE` em todas as tabelas com dados de tenant
- [ ] (P0) `get_db()` faz `SET ROLE lia_app` + `SET app.company_id` antes de yield
- [ ] (P0) `RESET ROLE` no finally do get_db()
- [ ] (P0) Todos os modelos com dados de tenant têm `company_id` NOT NULL
- [ ] (P1) `pool_pre_ping=True` no engine (Cloud Run / serverless exige)
- [ ] (P1) `expire_on_commit=False` no AsyncSessionLocal
- [ ] (P1) Repositórios usam `db.flush()` — não `db.commit()`
- [ ] (P1) Alembic env.py importa todos os modelos para `target_metadata`
- [ ] (P1) `get_url()` em alembic/env.py converte `postgresql://` → `postgresql+asyncpg://`
- [ ] (P1) `get_tenant_aware_session()` para background tasks
- [ ] (P2) Redis: `socket_connect_timeout=0.5` (fail-fast)
- [ ] (P2) Migration 080: UUID canônico para demo company
- [ ] (P2) Migration 093: `dpo` no UserRole enum (LGPD Art. 41)

---

## Gotchas e erros comuns

### 1. Modelo sem company_id bypass silencioso de RLS

Se uma nova tabela for criada sem `company_id`, RLS não pode aplicar políticas a ela. A tabela torna-se um vetor de vazamento cross-tenant. **Todo model com dados de tenant deve ter `company_id` NOT NULL.**

### 2. `asyncpg` não suporta `sslmode=`

`DATABASE_URL` com `?sslmode=require` quebra a conexão asyncpg com `InvalidPasswordError` ou similar. A função `get_url()` em `alembic/env.py` e `database.py` strip esse parâmetro. Se copiar URL do provedor (Supabase, Railway, etc.), verificar se tem `sslmode`.

### 3. Import de `Base` do lugar errado

Modelos que importam de `app.core.database.Base` em vez de `lia_config.database.Base` criam tabelas em um `metadata` separado — Alembic `--autogenerate` não as detecta e pode apagar tabelas que existem no schema real.

### 4. `db.commit()` dentro de repositório quebra transações

Se um repositório chama `db.commit()`, operações subsequentes na mesma `db` session estão em uma nova transação. Se a segunda falhar, a primeira já commitou — sem rollback. Sempre use `db.flush()` nos repositórios.

### 5. RLS e migrações de schema

Durante `alembic upgrade head`, o contexto é o DB user direto (não `lia_app`). Se o DB user for superuser e `FORCE ROW LEVEL SECURITY` estiver ativo, `SET ROLE lia_app` + `SET app.company_id` podem conflitar com ALTER TABLE. A migration 068 executa com o user padrão e só depois ativa FORCE — essa ordem é crítica.

### 6. Redis singleton vs per-call

`get_redis()` é singleton — não usar para operações que precisam de `async with redis:`. Usar `get_redis_connection()` para async context managers ou múltiplas operações independentes.

### 7. Alembic não detecta modelos não importados

Se criar um novo model e não adicioná-lo ao `alembic/env.py`, `alembic --autogenerate` não cria migration para ele. Sempre adicionar novos models nos imports do `env.py`.

---

## Testes obrigatórios

```
tests/unit/database/test_get_db.py
  - test_rls_company_id_injected: confirma que SET app.company_id é chamado
  - test_rls_reset_role_on_exit: RESET ROLE no finally
  - test_commit_on_success
  - test_rollback_on_exception

tests/unit/database/test_redis_client.py
  - test_get_redis_singleton: mesma instância em chamadas repetidas
  - test_get_redis_connection_new_instance: nova instância por chamada
  - test_masked_url_log: credentials não aparecem em logs
  - test_close_redis: fecha conexão sem erro

tests/unit/repositories/test_sqlalchemy_base.py
  - test_create_uses_flush_not_commit
  - test_update_partial: apenas campos do data atualizado
  - test_delete_returns_false_if_not_found
  - test_list_applies_filters

tests/integration/test_rls_tenant_isolation.py
  - test_company_a_cannot_see_company_b_jobs
  - test_rls_without_company_id_returns_empty
  - test_admin_bypass_via_superuser_role (deve funcionar)
  - test_force_rls_blocks_superuser_without_set_role

tests/integration/test_alembic.py
  - test_migrations_run_without_error
  - test_downgrade_all_works
```

---

## Referências

- **Multi-tenancy enforcement:** `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md`
- **Auth (company_id no JWT):** `themes/infrastructure/I8_AUTH_AND_AUTHORIZATION.md`
- **Middleware (ContextVar):** `themes/infrastructure/I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md`
- **Fairness audit log migration:** Migration 015 — EU AI Act Artigo 9/13
- **RLS deny-by-default:** Migration 068 — fundação de multi-tenancy
- **DPO role migration:** Migration 093 — LGPD Art. 41
- **Reconstruction Guide:** `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §H (data layer)
