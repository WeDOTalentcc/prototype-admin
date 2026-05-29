# WeDO Talent — Monorepo

ATS B2B multi-tenant com IA. Empresa: **WeDOTalent** (sempre escrito assim). Idioma de comunicação: **Português**.

---

> ## ⚠️ CANONICAL DE PRODUÇÃO — REPLIT É O CÓDIGO QUE VIRA PRODUÇÃO
>
> **Decisão Paulo 2026-05-23:** Replit (`lia-agent-system` + `plataforma-lia`) é o código canonical de produção. **NÃO é legacy. NÃO está em desativação.**
>
> - ✅ **Edits aqui = código que vira produção** (Paulo push manual para GitHub canonical)
> - ✅ **Fonte de verdade** para Estúdio de Agentes, triagem candidato, chat, voice, WhatsApp
> - ❌ **NÃO existe migração ativa** para `recruiter_agent_v5` no contexto UI/triagem/chat candidato
> - ❌ Conflicting statements em outros docs ("lia-agent-system está em desativação" / "IA canonical = recruiter_agent_v5") são **OUTDATED** — ignorar
>
> **Quando agente Claude lê isso:** trate `lia-agent-system/` + `plataforma-lia/` como **produção viva** que recebe fixes, features e refactors canonical. Apenas Anderson + equipe têm autoridade pra mudar essa premissa via decisão explícita.
>
> **Refs:** memory `project_replit_canonical_production.md` (sessão 2026-05-23) + commits Sprint 4 B.1 (`ca62339cb`, `497e30429`) que destravaram triagem candidato em PRODUÇÃO.

---

> ## 🚫 RECRUITER_AGENT_V5 — FORA DE ESCOPO (reforçado 2026-05-24)
>
> **Decisão Paulo 2026-05-24 (literal):** _"recruiter agent v5 nao é foco nosso. somente replit. anotar isso claude.md. esquecer recruiter agent v5"_
>
> **Tradução operacional:**
> - 🚫 **NÃO citar** `recruiter_agent_v5` como destino, ground truth, ou referência em nenhuma análise, plano, ADR, PR ou commit
> - 🚫 **NÃO auditar** arquivos em `~/Documents/Python/recruiter_agent_v5/` (mesmo que o clone exista)
> - 🚫 **NÃO sugerir** migração de qualquer feature pro v5
> - 🚫 **NÃO comparar** implementação Replit com v5 ("o v5 faz assim...") — irrelevante
> - 🚫 **NÃO propor** sincronização ou bridge entre lia-agent-system e v5
> - ✅ **Foco único:** Replit (`/home/runner/workspace/` — `lia-agent-system/` + `plataforma-lia/` + qualquer outro subdir)
> - ✅ Se docs antigos (CLAUDE.md do monorepo GitHub, memory files antigos) mencionarem v5 como canonical: tratar como **outdated** e ignorar
>
> **Por quê (contexto):** v5 existe no GitHub (Anderson + equipe), mas Paulo não itera nele, não testa lá, não decide sobre ele. Citá-lo introduz ruído arquitetural e dispersa foco. O canonical do Paulo é Replit, ponto.
>
> **Refs:** memory `feedback_no_recruiter_agent_v5.md` (reforçado 2026-05-24).

---


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

## Replit dev workflow (Sprint R.3)

`uvicorn` em dev tem `--reload` ativo (config em `.replit`, workflow
`lia-backend`). Mudanças em arquivos `.py` dentro de `lia-agent-system/`
auto-disparam restart do processo — não precisa mais kill + nohup
manual. Watchfiles monitora apenas `lia-agent-system/` via
`--reload-dir lia-agent-system` para evitar trigger por outros
artifacts do monorepo.

Prod (deploy via GitHub canonical, responsabilidade do Anderson/time)
NÃO usa `--reload`. Workflow `.replit` é dev-only.

Sensor: `lia-agent-system/tests/sensors/test_replit_workflow_uvicorn_reload.py`
trava a presença das flags no `.replit`.

## Princípios de trabalho

- **Separação total FE/BE.** Frontend consome API REST via proxy. Sem código misto.
- **Multi-tenant obrigatório.** Todo modelo Rails tem `account_id`; toda query passa por `Apartment::Tenant.switch!` via `Authenticable`.
- **Segurança first.** JWT nunca no browser. Tokens em cookies httpOnly. Secrets nunca no código.
- **Portabilidade FE futura (Vue).** Código novo segue padrões que mapeiam limpo para Pinia + Vue — ver `frontend-overview.instructions.md`.
- **Idioma:** Português em toda comunicação e copy. Código pode ser em inglês; comentários quando existirem, em qualquer dos dois.
- **Marca:** sempre **WeDOTalent** (nunca "Wedo Talent", "WeDo Talent" etc).

## Endpoints + RLS canonical (F11, 2026-05-24)

**REGRA:** endpoints que escrevem em tabelas RLS-protected (150 tabelas Postgres com `rowsecurity=true` + `forcerowsecurity=true`) DEVEM usar `Depends(get_tenant_db)`, NÃO `Depends(get_db)`.

**Por quê:** RLS policies declaram `WITH CHECK (company_id)::text = app_current_company_id()`. A função `app_current_company_id()` retorna `NULLIF(current_setting('app.company_id', true), '')`. Quando o GUC não está setado, retorna NULL → bloqueio silencioso ("new row violates row-level security policy"). `get_db` NÃO seta o GUC; `get_tenant_db` faz via `set_tenant_context` que executa `SELECT set_config('app.company_id', :cid, true)`.

**Tabelas afetadas (lista canônica):** ver `lia-agent-system/scripts/check_get_db_rls_safety.py:RLS_TABLES` — `candidates`, `vacancy_candidates`, `job_vacancies`, `interviews`, `candidate_*`, `communication_*`, `agent_*`, `audit_logs`, `ai_consumption`, etc.

**Pitfalls operacionais:**
1. **Rollback transactional drop GUC.** `set_config('app.company_id', x, true)` é `is_local=true` (transaction-scoped). Qualquer `db.rollback()` ou `db.commit()` ends the transaction → GUC drops. Helpers canonical: `commit_keeping_tenant(db)` (em `app/core/database.py`) re-injeta após commit. Se chamar `db.rollback()` manualmente (ex: dentro de `ensure_table` defensive), DEVE re-chamar `set_tenant_context(db, company_id)` após.
2. **AsyncSessionLocal() local não herda GUC.** Abrir nova session local com `async with AsyncSessionLocal() as db` NUNCA herda o GUC da request. Use a session injetada (`Depends(get_tenant_db)`) ou chame `set_tenant_context` manualmente.
3. **`ensure_table()` defensive antiquado.** Tables hoje são alembic-managed. `CREATE TABLE IF NOT EXISTS` sob role `lia_app` raise `InsufficientPrivilegeError` → rollback → drop GUC → INSERT subsequente falha. Remova `ensure_table()` calls.

**Sensores canonical:**
- `lia-agent-system/scripts/check_get_db_rls_safety.py` — AST detecta `Depends(get_db)` em handlers que escrevem em RLS tables. Modes: `--blocking` (CI), default warn.
- `lia-agent-system/scripts/check_no_duplicate_routes.py` — sensor FastAPI dup routes.
- `lia-agent-system/scripts/check_no_company_id_uuid_cast.py` — sensor `CAST(:co AS uuid)` em tables varchar.

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

## Regras de organização de branch e BRANCH_MAP

### Guide 1 — Branch por tema (feedforward, computacional)

Todo novo tema/feature/épico abre branch própria a partir de `main`:
- Padrão: `feat/<tema>-<descricao-curta>` ou `fix/<tema>-<descricao-curta>`
- **Proibido acumular temas distintos** em uma única branch de sprint
- Exceção: bug fix dentro do tema atual da branch ativa
- Após merge: branch de feature pode ser deletada; tag `milestone/<descricao>` preserva o ponto

Exemplos válidos: `feat/teams-integration`, `feat/pr-a-rail-a-metadata`, `fix/wsi-scoring-cast`

Exemplo proibido: commitar Teams + LIA Maturity + Rail features na mesma branch de sprint (caso histórico de `feat/orch-migration-sprint-I` — não repetir).

### Guide 2 — `docs/BRANCH_MAP.md` é canônico (feedforward, computacional)

`docs/BRANCH_MAP.md` é o **mapa canônico do repositório**. Toda mudança que adiciona tema novo OU milestone significativo OBRIGA atualização do mapa antes do commit final do tema.

Para cada nova entrega:
1. Adicionar nova seção §N em `docs/BRANCH_MAP.md` (se for tema novo)
2. Criar tag `milestone/<descricao>` se a entrega fechar um marco
3. Atualizar tabela de Cross-references se um doc canônico novo foi criado em `docs/`
4. Commit message do mapa: `docs(nav): BRANCH_MAP — <descrição>`

Antes de propor qualquer mudança não-trivial, agentes IA DEVEM ler `docs/BRANCH_MAP.md` para identificar tema, milestones e docs canônicos cruzados (templates de prompt no Apêndice A do mapa).

### Sensor — branch-map-theme-check (ativo, computacional)

Implementado como hook commit-msg via pre-commit framework. Bloqueia commits
em branches genéricas (sprint accumulators) cujo tema declarado no commit
prefix não aparece em `docs/BRANCH_MAP.md`.

- **Script:** `scripts/check_branch_map.py`
- **Config:** `.pre-commit-config.yaml`
- **Doc:** `scripts/README_HOOKS.md`
- **Instalação (1x por dev):** `pip install pre-commit && pre-commit install --hook-type commit-msg`

Bypass intencional (apenas em urgência): `git commit --no-verify`.


## Regras globais (do usuário)

- **Sem comentários desnecessários.** Comente só o *porquê* quando não-trivial. Código bem nomeado dispensa `// faz X`.
- **SOLID, DRY, clean code, TDD** sempre que couber.
- **Antes de adicionar CRUD novo**, veja como o projeto já resolve o mesmo domínio — siga o padrão existente.
- **Branch de trabalho: `develop`.** Nunca commitar direto em `main`.

---

**Fonte de verdade para IA = o código.** Os instructions são a sinalização; a referência canônica está em `ats_api/app/`, `lia-agent-system/app/` e `plataforma-lia/src/`.

---

### Learning Loops toggles canonical consumption (registrado 2026-05-24)

Todo consumer de toggles `learning_loops` (Sprint B P3 D2 — gate de aprendizado
contínuo) em `app/domains/**` DEVE usar `load_learning_loops_toggles(company_id, db)`
do canonical helper `app/shared/services/learning_loops_toggles.py`.

**Padrão proibido:**
- `select(CompanyHiringPolicy).where(...)` direto em services para ler `automation_rules.learning_loops` (duplicação de produtor).
- `toggles.get("<key>", <literal>)` com default literal — helper canonical já garante presença de TODAS as 5 chaves canonical com tipo bool, default literal só causa drift (F2.1 audit 2026-05-24).

**Pattern canonical:**

```python
from app.shared.services.learning_loops_toggles import load_learning_loops_toggles

toggles = await load_learning_loops_toggles(company_id, self.db)
if not toggles.get("enabled"):
    return  # master switch off
if not toggles.get("wsi_question_effectiveness"):
    return  # specific loop off
```

**Decisão LGPD 2026-05-24 (F2.1 fix):** `bigfive_department_history` default = `False` (era `True` desde D2 2026-05-10). ADR-LGPD-001 conservative defaults preserva opt-in canonical via UI disclosure modal. Frontend `LearningLoopsPanel.tsx` já mostra `requiresDisclosure: true`; backend agora alinhado.

**Sensor canonical:** `lia-agent-system/scripts/check_learning_loops_canonical_helper.py` (AST + grep checker). Baseline 2026-05-24: **0 violations** em 3 consumers (`bigfive_service.py`, `jd_similar_service.py`, `transition_dispatch_service.py`). `EXEMPT_FILES` documentadas inline (helper + model + endpoint REST).

**Migration policy:** ao adicionar consumer novo de `learning_loops` em `app/domains/**`, (a) usar o helper, (b) adicionar caminho a `CONSUMERS_PATHS` do sensor, (c) escrever contract test em `tests/contract/test_learning_loops_defaults.py`.

---

### lia_tone PT-BR → EN translator at the boundary (registrado 2026-05-24 — F3.1)

Tab "Personalidade da IA" (`Configurações → Minha Empresa`) deixa o recrutador
escolher 1 dos 6 tons canonical PT-BR: `profissional`, `amigavel`, `formal`,
`casual`, `formal_amigavel`, `empatico`. Esses valores são gravados em:

- `communication_rules.ai_persona.tone` — **PT-BR canonical** (consumido pelo
  `SystemPromptBuilder` via `TONE_INSTRUCTIONS` no chat da LIA).
- `communication_rules.lia_tone` — **EN legacy** (consumido pelo
  `communication_dispatcher._apply_tone` em outbound email/WhatsApp).

**Audit 2026-05-24:** descoberto que service gravava PT-BR direto em ambas
as keys, mas dispatcher só reconhece `"friendly"` e `"formal"` em case explícito
(default `"professional"`). Recrutador escolhia "Empático" → backend gravava
`lia_tone="empatico"` → dispatcher caía no greeting default. **Outbound
silenciosamente ignorava a config.**

**Approach canonical (A):** translator no boundary — `ai_persona_service.update_ai_persona`
traduz PT-BR → EN via `TONE_PT_TO_EN_LEGACY` (em `ai_persona_validator.py`) ANTES
de gravar `lia_tone`. `ai_persona.tone` permanece PT-BR.

**Mapping:**

| PT-BR canonical | EN legacy (dispatcher) | Justificativa |
|---|---|---|
| `profissional` | `professional` | default safe fallthrough |
| `amigavel` | `friendly` | reconhecido pelo dispatcher |
| `formal` | `formal` | reconhecido pelo dispatcher |
| `casual` | `friendly` | closest match — bucket informal |
| `formal_amigavel` | `formal` | closest match — bucket formal |
| `empatico` | `friendly` | closest match — bucket caloroso |

**Sensor:** `lia-agent-system/scripts/check_lia_tone_mapping_complete.py` (CANONICAL_AI_TONES ⊆ TONE_PT_TO_EN_LEGACY). Baseline 2026-05-24: **0 violations**.

**Contract tests:** `tests/contract/test_lia_tone_pt_en_mapping.py` (4 testes — 1 cobertura, 1 valores safe pro dispatcher, 1 passthrough graceful, 1 parametrizado per-tone validando o write integrado).

**Approach B (backlog técnico):** migrar `_apply_tone` para consumir
`ai_persona.tone` PT-BR + `TONE_INSTRUCTIONS` direto. Mais limpo a longo prazo
mas dispatcher pode ter outros callers — preferir Approach A enquanto não há
necessidade clara.

**Single UI control = 2 backend writes coerentes** (pattern canonical reforçado).

---

## Agent Studio Architecture (registrado 2026-05-27 — Wave F)

### Stack
- Frontend: `plataforma-lia/src/components/pages-agent-studio/` (Next.js 15 + SWR)
- Backend: `lia-agent-system/app/domains/agent_studio/` (FastAPI + LangGraph ReAct)
- Runtime: `custom_agent_runtime.py` (~1088 LOC) — 4 guards: FairnessGuard (pre+post), PromptInjectionGuard, SecurityPatterns, PIIStripCallback

### REGRA — pages-agent-studio usa SWR para dados de API
Todo hook em `src/hooks/agents/` que faz fetch de API DEVE usar `useSWR` de `swr`. Anti-pattern `useState + useEffect(fetch)` inline em componente é proibido (migrar para hook com SWR). Ex canônico: `use-agent-activities.ts` + `use-custom-agents.ts`.

### REGRA — FairnessGuard é obrigatório no runtime
`FairnessGuard` (pre + post) está wired em `custom_agent_runtime.py`. Ao criar novo agent type, verificar que os guards são invocados. Sensor `check_trace_span_in_runtime.py` garante observabilidade.

### REGRA — compliance_block sempre injetado
`SystemPromptBuilder.build()` injeta `compliance_block.yaml` (14 atributos LGPD protegidos) automaticamente via `PromptComposer.compliance_blocks_for(agent_type)`. Sensor `check_compliance_block_injection.py` garante.

### Estrutura de agentes
- **Agentes de Captação (Sourcing):** calibração via `pool_agent_runs`, cron via Celery beat, métricas em `pool_agent_runs.runtime_metrics`
- **Agentes Personalizados (Custom):** runtime direto via `CustomAgentRuntime`, sem cron próprio
- **Gêmeos Digitais (Digital Twins):** avaliação LLM via `TwinInferenceService.evaluate`, indexação via `TwinKnowledgeIndexer`

### Token tracking
`pool_agent_runs.runtime_metrics` persiste: `input_tokens`, `output_tokens`, `cost_usd`, `model_used`, `latency_ms`. Fonte: `LangChain AIMessage.usage_metadata` agregado em `_state_to_output`.

### OTEL tracing
`@trace_span` decorator em `app/shared/observability/tracing.py:275`. Métodos cobertos: `CustomAgentRuntime.execute`, `_run_graph`, `_invoke_voice`, `_invoke_whatsapp`, `_invoke_chat`, `TalentPoolReActAgent.process`, `TwinInferenceService.evaluate`.

### Marketplace UX canonical (Wave F)
- Install com sucesso: `toast.success(t('installSuccess'))` + auto-switch para tab "installed"
- Search: debounce 300ms (não query a cada keystroke)
- Ambos implementados em `MarketplaceTab.tsx` via `onInstallSuccess` callback + `debouncedSearch` state

## Studio Fase 2 — onde os agentes vivem (registrado 2026-05-28)

A Fase 2 do Agent Studio distribuiu a presença dos agentes para FORA do Studio.
O recrutador encontra agentes em todos os surfaces da plataforma.

### Surfaces que mostram agentes

| Surface | O que mostra | Componente | Endpoint |
|---|---|---|---|
| **Sala de Controle** (`/agent-studio?tab=control-room`) | Live + histórico + LGPD + decision tree | `StudioControlRoom` | `/agent-monitoring/active-executions`, `/recent-executions`, `/executions/{id}/reasoning` |
| **Decidir** (`/tasks`) | AgentsCard (5º card) + banner global "N agentes trabalhando" | `AgentsCard`, `AgentRunningBanner` | `/agent-monitoring/active-summary?surface=decidir` |
| **Vagas** (`/jobs/{id}`) | Aba "Agentes" + badge "🩵 N agentes ativos" no header | `JobAgentsTab`, `JobAgentBadge` | `/jobs/{id}/agents`, `/agent-deployments?target_type=job` |
| **Banco Vivo** (`/bancos-de-talentos/{id}`) | Aba "Agentes" com pingo cyan quando running | `TalentPoolPage` | `/agent-deployments?target_type=talent_pool` |
| **Funil** (`/funil-de-talentos`) | Botão "+ Agente" no header de cada stage + pingo PULSANTE quando running | `PipelineRailNode`, `StageAgentTriggerModal` | `/agent-deployments?target_type=pipeline_stage` |
| **Candidato (kanban/preview)** | Ícone Brain canto inferior se candidato foi tocado por agente nas últimas 24h | `CandidateTouchIndicator` | `/agent-monitoring/candidate/{id}/touches` |
| **Configurações > Consumo** | Drilldown ao clicar barra do gráfico + alertas de orçamento per-agent | `ConsumptionDrilldownModal`, `BudgetAlertsList` | `/ai-consumption/by-agent/drilldown`, `/budget-alerts` |
| **Studio > KPIs por agente** (`/agent-studio/{id}/kpis`) | Cards + heatmap horário + tools breakdown + badge "aprendendo" | `AgentKpisClient` | `/custom-agents/{id}/kpis` |

### REGRA — Componentes canonical reutilizáveis

- **`DecisionTreeDrawer`** (`pages-agent-studio/decision-tree/`) — usado por TODOS os surfaces que mostram "por que o agente fez X". Props canonical: `{executionId, onClose}`. Sensor `check_decision_tree_drawer_uses_canonical_props.py` BLOCKING garante.
- **`useDeploymentsByTargets`** (`hooks/agents/use-deployments-by-targets.ts`) — batch endpoint, elimina N+1. Usar SEMPRE em vez de N fetches per target.
- **`useActiveAgentsSummary`** (`hooks/agents/use-active-agents-summary.ts`) — top N agentes ativos, polling 10s, surface filter.
- **`AgentDeployment`** (backend canonical) — única junction table agente↔surface. NÃO criar tabelas `job_agent_assignments`, `pipeline_agent_assignments`. Sensor `check_no_duplicate_assignment_table.py` BLOCKING garante.
- **`FirstExecutionTooltip`** (`pages-agent-studio/`) — tooltip 1x por agente quando primeira execução acontece. Wired em AgentsCard + LiveAgentsList (Onda 5.1). Storage key per-agent (`studio_first_execution_seen_{agent_id}`).
- **`ConsumptionDrilldownModal`** — modal canonical único, owned pelo `ConsumoHub` (Onda 5.2). Tabs (CreditosIaTab/AgentesTab) chamam `onOpenDrilldown` em vez de manter state local. Param URL `?filter={studio_agent_id}` auto-abre (Onda 5.3).

### REGRA — Cyan é a cor da IA

Toda surface de agente usa `lia-cyan-*` tokens. Sensor `check_cyan_token_for_agents.py` BLOCKING garante.
Pingo PULSANTE é exclusivo do Funil (decisão de produto). Em outros surfaces, pingo é static 4-6px.
Honra `prefers-reduced-motion`.

### REGRA — LGPD em todo decision tree

`AgentReasoningStep.data_fields_accessed[]` lista quais campos do candidato foram lidos.
`/agent-monitoring/executions/{id}/reasoning` sempre retorna `data_fields_NOT_accessed: ["cpf", "raca", "religiao", "genero", "estado_civil"]` (declarativo).
Helper canonical `lgpd-csv.ts` exporta trilha LGPD para CSV (DPO compliance).
Sensor `check_lgpd_data_access_logged.py` BLOCKING garante.

### REGRA — Trigger modes válidos por target_type

`VALID_TRIGGER_MODES_BY_TARGET` em `app/shared/trigger_mode_validation.py`:
- `talent_pool`: on_create, on_schedule, manual
- `job`: on_create, on_schedule, manual, on_apply
- `pipeline_stage`: on_enter_stage, on_exit_stage, on_stuck_in_stage, on_stage_change
- `candidate_list`: on_schedule, manual

Validation enforced em todos endpoints write (create, update, bulk).

### REGRA — Recharts em surfaces de Studio têm aria-label

Todo `<BarChart>`, `<LineChart>`, `<AreaChart>` em surfaces de Studio (Onda 5.5) é envolto em wrapper `<div role="img" aria-label="...">` com descrição contextual (e.g., "Heatmap de execuções 24h, pico às 14h"). Screen readers anunciam a função e contexto do chart antes do conteúdo SVG.

### Empty states e onboarding

- Studio empty: `StudioEmptyState` com persona name via `useAiPersona()`
- Badge "🩵 aprendendo" quando `is_learning=true` (< 5 execuções) — `LearningBadge`
- `FirstExecutionTooltip` mostra dica 1x por agente quando primeira execução acontece (gate via localStorage `studio_first_execution_seen_{agent_id}`)

### Sensor agregado de invariantes Fase 2

`lia-agent-system/scripts/check_phase2_invariants.py` (Onda 5.9) roda os 10 sensores BLOCKING + 3 warn-only da Fase 2 em sequência. Wired em `frontend-ci.yml` (step "Phase 2 invariants") como gate de regressão.
