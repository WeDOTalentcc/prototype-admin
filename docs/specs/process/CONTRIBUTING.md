# CONTRIBUTING.md — Guia de Contribuição

**Versão:** 1.0
**Última atualização:** 2026-03-26
**Plataforma:** WeDOTalent / LIA

---

## 1. Repositórios

| Repositório | Stack | Propósito |
|-------------|-------|-----------|
| `lia-agent-system` | Python 3.11 + FastAPI + LangChain/LangGraph | Backend, agentes IA, APIs |
| `plataforma-lia` | React 18 + Next.js + Tailwind + Radix | Frontend do recrutador |
| `ats_api` | Rails 7.1 | API legada do ATS |
| `ats_front` | Vue 3 + Vuetify | Frontend legado |
| `ats_mcp` | Node.js | MCP Server |
| `wedo-nuxt` | Nuxt 3 + Vuetify | Biblioteca de componentes |

---

## 2. Branch Naming

```
<tipo>/<ticket>-<descricao-curta>
```

| Tipo | Uso | Exemplo |
|------|-----|---------|
| `feat/` | Nova funcionalidade | `feat/LIA-1234-silver-medalists` |
| `fix/` | Correção de bug | `fix/LIA-5678-consent-check-null` |
| `refactor/` | Refatoração sem mudança de comportamento | `refactor/LIA-9012-split-pipeline-service` |
| `docs/` | Documentação | `docs/LIA-3456-update-api-contracts` |
| `test/` | Adição/correção de testes | `test/LIA-7890-fairness-four-fifths` |
| `chore/` | Infra, deps, CI | `chore/LIA-1111-upgrade-langchain` |
| `hotfix/` | Fix urgente para produção | `hotfix/LIA-2222-pii-leak-logs` |

---

## 3. Commit Conventions

Formato: `<tipo>(<escopo>): <descrição>`

```
feat(wsi): add Bloom taxonomy scoring to WSI evaluator
fix(pipeline): correct stage_entered_at not updating on drag-drop
refactor(agents): extract ReActLoop from monolithic agent
docs(specs): update AI_QA_PROTOCOL with fairness checks
test(fairness): add four-fifths rule tests for region dimension
chore(deps): upgrade langchain to 0.3.9
```

**Regras:**
- Linha de título ≤ 72 caracteres
- Corpo opcional, separado por linha em branco
- Referência ao ticket Jira quando aplicável: `Refs: LIA-1234`
- Breaking changes: `feat(api)!: remove deprecated /v1/search endpoint`

---

## 4. Pull Request Rules

### 4.1 Template

```markdown
## O que muda
[Descrição clara do que foi implementado/corrigido]

## Por que
[Contexto do problema ou feature]

## Como testar
[Passos para reproduzir/validar]

## Checklist
- [ ] Testes unitários passando
- [ ] Coverage ≥ 30%
- [ ] Contract tests passando (se agente novo/modificado)
- [ ] Fairness tests passando (se impacta scoring/avaliação)
- [ ] Sem secrets hardcoded
- [ ] Spec atualizado (se mudança de API/schema)
- [ ] Anti-sycophancy verificado (se prompt novo)
```

### 4.2 Review Obrigatório

| Tipo de mudança | Reviewers mínimos | Quem |
|----------------|-------------------|------|
| Qualquer código | 1 | Peer do time |
| System prompt novo/editado | 2 | Peer + Tech Lead |
| Schema de banco (migration) | 2 | Peer + DBA/Tech Lead |
| Serviço de scoring/avaliação | 2 | Peer + responsável fairness |
| Endpoint público (sem auth) | 2 | Peer + Security |
| Mudança em FairnessGuard | 2 | Peer + responsável compliance |

### 4.3 Labels

| Label | Significado |
|-------|-----------|
| `ready-for-review` | PR pronto para review |
| `changes-requested` | Reviewer pediu alterações |
| `approved` | Aprovado para merge |
| `blocked` | Dependência externa ou decisão pendente |
| `breaking-change` | Mudança incompatível |
| `security` | Impacta segurança |
| `fairness` | Impacta bias/fairness |

---

## 5. Testes

### 5.1 Antes do Push

```bash
cd lia-agent-system

# Unit tests rápidos
python -m pytest tests/unit/ -m easy -v

# Fairness (se alterou scoring)
python -m pytest tests/fairness/ -v

# Contract (se alterou interface de agente)
python -m pytest tests/contract/ -v
```

### 5.2 No CI (push)

- Unit tests (easy + medium)
- Contract tests
- Fairness tests
- Coverage gate ≥ 30%

### 5.3 No CI (nightly)

- Unit tests completos (easy + medium + hard)
- Integration tests
- E2E tests (backend + frontend Playwright)
- Security red team tests

### 5.4 No Release

- DeepEval (non-blocking)
- RAGAS evaluation (non-blocking)
- Load tests (Locust)

**Referência completa:** `docs/specs/qa/QA_PROTOCOL.md`

---

## 6. Spec-Driven Development (SDD)

Toda feature nova segue o ciclo SDD:

```
1. Spec (documentação) → 2. Review → 3. Implementação → 4. Testes → 5. QA → 6. Merge
```

### 6.1 Regras

- **Spec primeiro:** Antes de escrever código, escrever a spec no formato `docs/specs/process/SPEC_TEMPLATE.md`
- **Review da spec:** Spec revisada por pelo menos 1 peer antes de implementar
- **Spec atualizada:** Se a implementação divergir da spec, atualizar a spec
- **Specs vivas:** Specs são documentos vivos, não artefatos descartáveis

### 6.2 Localização de Specs

| Categoria | Diretório |
|-----------|----------|
| AI / Agentes | `docs/specs/ai/` |
| Backend / API | `docs/specs/backend/` |
| Frontend / Design | `docs/specs/frontend/` |
| QA / Testes | `docs/specs/qa/` |
| Processo | `docs/specs/process/` |

---

## 7. Padrões de Código

### 7.1 Backend (Python)

- **Formatter:** Black (line-length 120)
- **Linter:** Ruff
- **Type hints:** Obrigatórios em funções públicas
- **Async:** Preferir `async/await` (FastAPI é async-first)
- **Imports:** Agrupados (stdlib → third-party → local), com linhas em branco entre grupos
- **Models:** Um arquivo por domínio em `app/models/`, shim pattern (`from lia_models.X import *`)
- **Services:** Uma classe por serviço, métodos async, dependency injection via FastAPI

### 7.2 Frontend (React/TypeScript)

- **Formatter/Linter:** ESLint + Prettier
- **Componentes:** Functional components com hooks
- **Styling:** Tailwind CSS utility-first, design tokens em `design-tokens.css`
- **State:** React Query para server state, useState/useReducer para local state
- **Naming:** PascalCase para componentes, camelCase para funções/hooks, kebab-case para arquivos
- **Icons:** Lucide React (não usar outros icon sets)

### 7.3 Prompts (System Prompts)

- **Localização:** `app/domains/*/prompts/` ou `app/shared/agents/prompts/`
- **Idioma:** Português brasileiro (prompts em PT-BR produzem respostas em PT-BR)
- **Seções obrigatórias:** IDENTITY, CONTEXT, TOOLS, FAIRNESS_AND_COMPLIANCE, FEW_SHOT_EXAMPLES
- **Versionamento:** Nome do arquivo inclui versão ou campo `version` no docstring
- **Anti-sycophancy:** Instruções explícitas contra concordância automática

---

## 8. Migrations (Database)

```bash
cd lia-agent-system

# Criar migration
alembic revision -m "add_new_column"

# Aplicar
alembic upgrade head

# Verificar sequência
alembic current
alembic history
```

**Regras:**
- `down_revision` deve apontar para a migration anterior
- Sem gaps na sequência (010 → 011 → 012 → ...)
- Indexes para colunas usadas em WHERE/JOIN
- Migrations com backfill quando aplicável
- Nunca alterar tipo de coluna de PK existente

---

## 9. Segurança

### 9.1 Obrigatório

- Nunca commitar API keys, tokens ou senhas
- `os.getenv()` sem default para secrets (falha explícita)
- PII masking em logs (`install_global_pii_masking()`)
- Multi-tenant: `company_id` filtering em TODAS as queries
- FairnessGuard antes de outputs que impactam candidatos

### 9.2 Proibido

- `LANGCHAIN_TRACING_V2 = True` em código (opt-in via env)
- Default hardcoded para verify tokens
- Nomes de candidatos no contexto LLM (blind evaluation)
- `GEOGRAPHIC_ADJUSTMENTS` com multiplicadores por país/região
- Logs contendo CPF, email ou telefone sem masking

---

## 10. Ambientes

| Ambiente | URL | Banco | Uso |
|----------|-----|-------|-----|
| Local | `localhost:3000` (FE) + `:8000` (BE) | PostgreSQL local | Desenvolvimento |
| Staging | TBD | PostgreSQL staging | QA, testes de integração |
| Production | Replit Deploy | PostgreSQL prod | Produção |

---

## 11. Contato

| Papel | Responsabilidade |
|-------|-----------------|
| Tech Lead | Aprovação de PRs com breaking changes, prompts, schemas |
| Responsável Fairness | Review de mudanças que impactam scoring/avaliação |
| DBA | Review de migrations |
| Security | Review de endpoints públicos, handling de PII |
