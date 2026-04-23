# WeDO Talent — Monorepo

ATS B2B multi-tenant com IA. Empresa: **WeDOTalent** (sempre escrito assim). Idioma de comunicação: **Português**.

## Arquitetura

```
wedotalent02202026/
├── ats_api/              ← Rails 7 — ATS core (vagas, candidatos, pipelines)
├── lia-agent-system/     ← FastAPI + LangGraph — agentes de IA (Sourcing, Pipeline, Wizard, ...)
├── plataforma-lia/       ← Next.js 15 + React 19 — frontend único, consome ambos backends
├── .github/
│   ├── instructions/     ← regras por tipo de arquivo (aplicadas por Copilot/Claude Code)
│   └── workflows/        ← CI
└── docker-compose.yml    ← postgres (pgvector), redis, rabbitmq + serviços
```

Cada subprojeto é autônomo (seu próprio deploy, seu próprio README). O monorepo existe para sincronia de ambiente dev + CI conjunta.

## Subprojetos

### `ats_api/` — Rails (backend ATS)

- Rails 7.1, PostgreSQL + Apartment (multi-tenant), Searchkick + Elasticsearch, Sidekiq.
- Auth: JWT via `Authenticable` concern; endpoints autenticados em `V1::Users::*`.
- Respostas JSON:API: `{ data: [...], meta: {...} }`; erros: `{ errors: [...] }`.
- Sem CLAUDE.md próprio — as regras ficam em `.github/instructions/rails-*.instructions.md`.
- Dev: `docker-compose up ats_api` (porta 8080).

### `lia-agent-system/` — FastAPI (agentes de IA)

- Python 3.11, FastAPI, LangGraph + LangChain, Claude Sonnet 4.5 como LLM primário.
- Orquestra 7 agentes ReAct: Wizard, Pipeline, Sourcing, Talent, JobsManagement, Kanban, Policy.
- Auth: mesmo JWT do Rails (tenant-aware); proxy de sessão via WorkOS.
- Dev: `docker-compose up lia-agent-system` (porta 8001).
- Observabilidade canônica: **exclusivamente** em `app/shared/observability/` (ADR-017). Ver seção Observabilidade abaixo.

### `plataforma-lia/` — Next.js (frontend)

- Next.js 15 App Router, React 19, TypeScript, Tailwind + shadcn/ui.
- Consome ambos backends via **proxy Next** (`src/app/api/backend-proxy/*`) — JWT em cookie httpOnly nunca vai pro browser.
- Dev **nativo** (fora do Docker): `cd plataforma-lia && npm run dev` (porta 5000 ou 3000).
- Tem seu próprio `plataforma-lia/CLAUDE.md` com detalhes do **Design System v4.2.1** (tokens, sombras, z-index, motion). **Consulte-o** antes de criar UI.

## Regras por tipo de arquivo — `.github/instructions/`

Os arquivos abaixo são carregados automaticamente por Copilot/Claude Code conforme o glob `applyTo:`. Leia o relevante **antes** de editar arquivos do tipo correspondente.

**Backend Rails** (`ats_api/`):

| Arquivo | applyTo |
|---|---|
| `rails-controllers.instructions.md` | `app/controllers/**/*.rb` |
| `rails-models.instructions.md` | `app/models/**/*.rb` |
| `rails-services.instructions.md` | `app/services/**/*.rb` |
| `rails-serializers.instructions.md` | `app/serializer/**/*.rb` |
| `rails-sidekiq.instructions.md` | jobs Sidekiq |
| `rails-migrations.instructions.md` | migrations |
| `rails-searchkick.instructions.md` | integrações Searchkick |
| `rails-apartment.instructions.md` | código multi-tenant |
| `rails-specs.instructions.md` | specs RSpec |

**Frontend Next.js** (`plataforma-lia/`):

| Arquivo | applyTo |
|---|---|
| `frontend-overview.instructions.md` | todo `*.{ts,tsx}` sob `plataforma-lia/src/` |
| `next-app-router.instructions.md` | `src/app/**/*.{ts,tsx}` |
| `react-components.instructions.md` | `src/components/**/*.tsx` |
| `styling-tailwind.instructions.md` | `*.tsx` (regras de Tailwind/DS) |
| `forms-and-validation.instructions.md` | formulários com RHF + Zod |
| `data-fetching.instructions.md` | `src/{lib/api,hooks,services,app/api}/**` — SWR + proxy |
| `state-management.instructions.md` | `src/stores/**/*.ts` — Zustand |
| `typescript-conventions.instructions.md` | todo `*.{ts,tsx}` |

Índice humano-legível dos instructions: `.github/copilot-instructions.md`.

## Comandos principais

```bash
# Infra completa (postgres, redis, rabbitmq, ats_api, lia-agent-system)
docker-compose up -d

# Frontend (nativo — cold start ~3s vs ~40s no Docker)
cd plataforma-lia && npm run dev

# Rails
docker-compose exec ats_api bundle exec rspec
docker-compose exec ats_api bundle exec rubocop

# FastAPI
cd lia-agent-system && uv run pytest
cd lia-agent-system && python3 scripts/check_forbidden_imports.py   # ADR-017 guard

# Frontend
cd plataforma-lia && npm run lint          # tsc --noEmit && next lint
cd plataforma-lia && npm test              # vitest (unit + hooks + components)
cd plataforma-lia && npm run test:e2e      # playwright
cd plataforma-lia && npm run build         # next build
```

## Princípios de trabalho

- **Separação total FE/BE.** Frontend consome API REST via proxy. Sem código misto.
- **Multi-tenant obrigatório.** Todo modelo Rails tem `account_id`; toda query passa por `Apartment::Tenant.switch!` via `Authenticable`.
- **Segurança first.** JWT nunca no browser. Tokens em cookies httpOnly. Secrets nunca no código.
- **Portabilidade FE futura (Vue).** Código novo segue padrões que mapeiam limpo para Pinia + Vue — ver `frontend-overview.instructions.md`.
- **Idioma:** Português em toda comunicação e copy. Código pode ser em inglês; comentários quando existirem, em qualquer dos dois.
- **Marca:** sempre **WeDOTalent** (nunca "Wedo Talent", "WeDo Talent" etc).

## Observabilidade (ADR-017) — `lia-agent-system/`

Tracing, structured logging, LLM callbacks, agent monitoring, drift detection (modelo + alertas), token tracking, token budget, WSI observability e configuração do LangSmith vivem **exclusivamente** em `lia-agent-system/app/shared/observability/`.

- **Detalhes:** `lia-agent-system/docs/CANONICAL_SOURCES_SPEC.md` (§1) e `ARCHITECTURE.md` ADR-017.
- **Lint enforcement:** `lia-agent-system/scripts/check_forbidden_imports.py` (pre-commit `G5` + CI).
- Importe sempre `from app.shared.observability.<modulo> import …`. Reintroduzir um dos 11 caminhos antigos quebra o build.

## ⛔ DO NOT MODIFY — Integração Microsoft Teams (Azure Bot)

Configurações abaixo são essenciais para a integração Teams via Azure Bot. **Não remover, alterar ou comentar.**

### 1. Middleware — rotas públicas

`lia-agent-system/app/middleware/auth_enforcement.py` deve manter `"/api/v1/teams/"` em `PUBLIC_PREFIXES` — essa rota é acessada diretamente pelo Azure Bot Service e não passa por autenticação de usuário.

```python
PUBLIC_PREFIXES = (
    "/api/v1/teams/",   # ← NÃO REMOVER — Azure Bot (Microsoft Teams)
    ...
)
```

### 2. Secrets — credenciais Azure Bot

| Secret | Descrição |
|--------|-----------|
| `MICROSOFT_APP_ID` | Application (client) ID do Azure Bot Registration |
| `MICROSOFT_APP_PASSWORD` | Client secret do Azure Bot Registration |
| `MICROSOFT_TENANT_ID` | Directory (tenant) ID do Azure AD |

Consumidos em `lia-agent-system/app/api/v1/teams/` — obrigatórios para autenticação com o Microsoft Bot Framework.

## Regras globais (do usuário)

- **Sem comentários desnecessários.** Comente só o *porquê* quando não-trivial. Código bem nomeado dispensa `// faz X`.
- **SOLID, DRY, clean code, TDD** sempre que couber.
- **Antes de adicionar CRUD novo**, veja como o projeto já resolve o mesmo domínio — siga o padrão existente.
- **Branch de trabalho: `develop`.** Nunca commitar direto em `main`.

---

**Fonte de verdade para IA = o código.** Os instructions são a sinalização; a referência canônica está em `ats_api/app/`, `lia-agent-system/app/` e `plataforma-lia/src/`.
