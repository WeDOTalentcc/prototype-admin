# ONBOARDING — LIA Agent System

> Guia de onboarding para novos desenvolvedores. Última atualização: 2026-06-16.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Notas |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| PostgreSQL | 15+ | Via Docker ou local |
| Redis | 7+ | Via Docker ou local |
| RabbitMQ | 3+ | Via Docker (opcional em dev inicial) |
| Docker + Compose | qualquer recente | Para serviços de infra |
| pre-commit | qualquer | `pip install pre-commit` |

**Acesso necessário:**
- Chave Anthropic API (`ANTHROPIC_API_KEY`) — solicitar ao responsável do projeto
- Credenciais de banco de dev — ver `.env.example`

---

## Setup do ambiente de desenvolvimento

### 1. Repositório

Este repo vive em Replit (`replit-wedo-0405`, `/home/runner/workspace/lia-agent-system/`).  
Branch ativa: `feat/benefits-prv-canonical`. Confirme sempre antes de operar:

```bash
git branch --show-current
git status -s
```

### 2. Ambiente virtual + dependências

```bash
python3 -m venv venv
source venv/bin/activate

# Instalar dependências de produção + dev
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Instalar hooks de pre-commit
pre-commit install
```

### 3. Variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas chaves reais
```

Variáveis obrigatórias para subir o servidor:

```
ANTHROPIC_API_KEY=...
DATABASE_URL=postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
```

> **Nunca commite `.env`** — está no `.gitignore`. Segredos sempre via variáveis de ambiente.

### 4. Serviços de infra

```bash
# Sobe PostgreSQL + Redis + RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Verifica saúde
docker-compose ps
```

### 5. Migrações de banco

```bash
# Aplica todas as migrações
alembic upgrade head

# Verifica estado
alembic current
```

> Migrations ficam em `alembic/versions/`. Numeração sequencial (ver `ls alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -5` antes de criar nova).

### 6. Subir o servidor

```bash
# Porta 8001 (padrão do sistema)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Health check
curl http://localhost:8001/health

# API docs interativa
open http://localhost:8001/docs
```

---

## Arquitetura — visão geral

```
lia-agent-system/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/v1/              # Endpoints REST (routers FastAPI)
│   ├── domains/             # Lógica de negócio por domínio
│   ├── shared/              # Código compartilhado cross-domain
│   ├── middleware/          # Auth, multi-tenancy, logging
│   ├── models/              # SQLAlchemy ORM models (legado — ver libs/)
│   ├── schemas/             # Pydantic schemas de request/response
│   ├── prompts/             # YAML de personas e system prompts
│   ├── repositories/        # Acesso a banco (padrão ADR-001)
│   └── workers/             # Celery background tasks
├── libs/                    # Pacotes internos compartilhados
│   └── models/lia_models/   # SQLAlchemy models canonical
├── alembic/                 # Migrações de banco
│   └── versions/            # Arquivos de migração numerados
├── tests/                   # Suíte de testes (unit, contract, e2e)
├── scripts/                 # Sensores de qualidade e utilitários
├── docs/                    # Documentação técnica
└── Makefile                 # Targets de dev canônicos
```

### Domínios (`app/domains/`)

Cada domínio é uma pasta autossuficiente com sua camada de services, repositories e schemas:

| Domínio | Responsabilidade |
|---|---|
| `job_creation/` | Wizard de criação de vaga (LangGraph orchestrator) |
| `job_management/` | CRUD e lifecycle de vagas |
| `cv_screening/` | Triagem de candidatos (WSI — Weighted Skills Interview) |
| `sourcing/` | Busca ativa de candidatos (Pearch AI, RAG) |
| `candidates/` | Perfis, scores, pipeline de candidatos |
| `communication/` | Email, WhatsApp, voice (Twilio/Gemini Live) |
| `offer/` | Geração e aprovação de ofertas |
| `voice/` | Plugins de coleta de dados por voz |
| `persona/` | Personalização de IA por tenant |
| `compliance/` | LGPD, fairness, audit trail |
| `analytics/` | Métricas, calibração, relatórios |
| `hiring_policy/` | Políticas de recrutamento por empresa |

### Shared (`app/shared/`)

Infraestrutura cross-domain. Principais módulos:

- `types.py` — Type aliases canônicos (`JobIdParam`, `WeDoBaseModel`)
- `tool_handler.py` — Decorador de segurança multi-tenant para ferramentas de agente
- `runtime_context.py` — `RuntimeContext` typed dataclass + ContextVars de tenant
- `tenant_guard.py` — `get_verified_company_id` (defense-in-depth header vs JWT)
- `pii_masking.py` — Mascaramento de PII para logs e prompt LLM
- `compliance/fairness_guard.py` — Gate de consultas discriminatórias
- `repositories/` — Base classes de repositório com `_require_company_id`
- `llm/` — Factory de modelos LLM (Anthropic, Google, OpenAI)
- `hitl/` — Human-in-the-loop gates para ações sensíveis

---

## Conceitos-chave

### Multi-tenancy

**Regra absoluta:** `company_id` vem SEMPRE do JWT/sessão — nunca do payload da request.

```python
# Padrão canônico em endpoints
from app.shared.tenant_guard import get_verified_company_id

@router.post("/meu-endpoint")
async def handler(
    payload: MeuSchema,
    company_id: str = Depends(get_verified_company_id),  # do JWT
    db: AsyncSession = Depends(get_tenant_db),
):
    ...
```

Todo repositório tem `_require_company_id()` que lança exceção se `company_id` estiver vazio. **Nunca** confiar no RLS do PostgreSQL — a proteção é na camada de aplicação.

### Agentes LangGraph

Os agentes são grafos de estado construídos com LangGraph. Cada nó é uma função assíncrona que processa `AgentState`.

```python
# Padrão de agente ReAct
from app.shared.agents.react_base import LangGraphReActBase

class MeuAgente(LangGraphReActBase):
    async def _get_tools(self) -> list:
        return [minha_tool_1, minha_tool_2]
```

Agentes se comunicam via ferramentas (`@tool_handler`). O sistema de orquestração principal é o `recruiter_copilot` federado (SSE, porta 8001).

### LGPD e Fairness

- **Dados sensíveis** (raça, religião, gênero, etnia, estado civil, saúde) são proibidos em decisões de IA
- Todo endpoint com texto livre de recrutador deve passar pelo `FairnessGuard` antes de ir ao LLM
- PII (CPF, RG, email, telefone) é mascarado em logs pelo `PIIMaskingFilter`
- Candidatos têm direito de erasure (`LgpdService`)

### Repository Pattern (ADR-001)

Services não fazem SQL direto. Toda query fica em `repositories/`:

```python
# ✅ Correto
from app.domains.candidates.repositories.candidate_repository import CandidateRepository

class MeuService:
    def __init__(self, repo: CandidateRepository):
        self.repo = repo

    async def buscar(self, company_id: str):
        return await self.repo.list_active(company_id)

# ❌ Proibido em services
result = await db.execute(select(Candidate).where(...))
```

Sensor: `scripts/check_no_select_in_services.py` (blocking).

---

## Onde encontrar as coisas

| O que você precisa | Onde encontrar |
|---|---|
| Rotas de API | `app/api/v1/` — um arquivo por recurso |
| Models SQLAlchemy | `libs/models/lia_models/` (canonical) |
| Pydantic schemas | `app/schemas/` ou `app/domains/<domain>/schemas/` |
| Repositórios | `app/domains/<domain>/repositories/` |
| Services | `app/domains/<domain>/services/` |
| Migrações | `alembic/versions/` — numeração sequencial |
| Testes unitários | `tests/unit/` |
| Testes de contrato | `tests/contract/` |
| System prompts | `app/prompts/shared/` |
| Sensores de qualidade | `scripts/check_*.py` |
| Comandos de dev | `Makefile` — `make help` lista tudo |

---

## Tarefas comuns de desenvolvimento

### Adicionar um endpoint

1. Criar/editar arquivo em `app/api/v1/<recurso>.py`
2. Usar `WeDoBaseModel` (com `extra='forbid'`) para o schema de request
3. Declarar `response_model=` obrigatório no decorator do router
4. `company_id` via `Depends(get_verified_company_id)`, nunca no body
5. Delegar lógica ao service/repository — sem SQL no controller
6. Adicionar teste de contrato em `tests/contract/`

```python
from fastapi import APIRouter, Depends
from app.shared.types import WeDoBaseModel
from app.shared.tenant_guard import get_verified_company_id

router = APIRouter()

class CriarItemSchema(WeDoBaseModel):  # extra='forbid' já incluso
    nome: str
    descricao: str | None = None

@router.post("/itens", response_model=ItemResponse, status_code=201)
async def criar_item(
    payload: CriarItemSchema,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_tenant_db),
):
    service = ItemService(db)
    return await service.criar(company_id=company_id, **payload.model_dump())
```

### Adicionar uma migração de banco

```bash
# Verificar próximo número livre
ls alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -5

# Criar migration manual (autogenerate tem limitações)
alembic revision -m "add_campo_x_to_tabela_y"

# Aplicar
alembic upgrade head

# Verificar estado
alembic current
```

> Sempre usar pathspec no commit: `git commit -m "..." -- alembic/versions/<arquivo>.py`

### Adicionar um domain service

1. Criar `app/domains/<domain>/services/meu_service.py`
2. Injetar repositório via `__init__` (não instanciar direto)
3. Toda query de banco via repositório — sem `db.execute` inline
4. Adicionar `# ADR-001-EXEMPT: <razão>` se houver exceção justificada

### Rodar os sensores de qualidade

```bash
# Tudo de uma vez (~35s)
make check-all

# Só Pydantic conventions (<1s)
make check-pydantic

# Smoke test nos endpoints (~34s, requer servidor rodando)
make smoke

# Lint (ruff)
make lint
```

---

## Troubleshooting

### `alembic upgrade head` falha com "multiple heads"

```bash
# Ver estado
alembic heads
# Criar merge migration
alembic merge heads -m "merge_heads"
alembic upgrade head
```

### Servidor não sobe — erro de import

Verifique se `ANTHROPIC_API_KEY` está no `.env`. O bootstrap LLM falha alto se a chave estiver ausente.

### Chat retorna "budget esgotado"

```bash
# Limpar contador Redis (dev only)
redis-cli DEL "token_budget:<company_id>:$(date +%Y-%m-%d)"
```

### `pytest` falha com `company_id` not set

Usar fixture `_reset_tenant_contextvar` nos testes que usam ContextVars de tenant:

```python
@pytest.fixture(autouse=True)
def reset_tenant(monkeypatch):
    from app.middleware.auth_enforcement import _current_company_id
    token = _current_company_id.set("test-company-uuid")
    yield
    _current_company_id.reset(token)
```

### Pre-commit hook falha

```bash
# Rodar manualmente para ver o erro
pre-commit run --files <arquivo-alterado>

# Pular hook pontualmente (emergência — documentar motivo no commit)
git commit --no-verify -m "..."  # use apenas se autorizado
```

---

## Referências

- `CLAUDE.md` — regras de harness para agentes IA (não pular)
- `ARCHITECTURE.md` — decisões arquiteturais
- `docs/` — ADRs e specs técnicas
- `Makefile` — `make help` para todos os comandos disponíveis
- `scripts/README.md` — documentação dos sensores de qualidade
