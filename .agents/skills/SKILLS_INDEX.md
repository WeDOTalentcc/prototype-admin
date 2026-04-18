# Skills da Plataforma LIA — Cascade-Aware Index

23 skills organizadas como sistema de auto-recrutamento (cascata). O ponto de entrada e SEMPRE `lia-orchestrator`.

> Contagem: 1 roteador + 2 planejamento + 3 qualidade por camada (NOVAS) + 5 UI/design + 1 compliance + 2 correcao/auditoria + 1 testes + 8 utilitarias = 23.

---

## REGRA #1 — Sempre comecar pelo orchestrator

> **`lia-orchestrator`** e a primeira skill a carregar em QUALQUER sessao de codigo. Ela decide quais outras skills voce precisa, em qual ordem, com base em modo (planning/build/bug fix/refactor/audit/deploy), dominio (backend/frontend/agente/integracao/compliance) e arquivo tocado.

Pular o orchestrator e a causa #1 de retrabalho. Ele nao implementa — ele convoca.

---

## Mapa rapido de cascata

| Voce vai... | Cascata convocada pelo orchestrator |
|---|---|
| Criar/editar endpoint FastAPI | `canonical-fix` > `backend-quality` > `lia-compliance` PARTE 4 > `lia-testing` > `feature-audit` |
| Criar/editar agente, node, tool, prompt | `canonical-fix` > `ai-architecture` > `lia-compliance` PARTE 1 + 3 > `lia-testing` > `feature-audit` |
| Criar/editar cliente HTTP, fila, GCS, OAuth | `canonical-fix` > `integration-patterns` > `backend-quality` > `lia-testing` > `feature-audit` |
| Criar/editar componente React (interface interna) | `design-standardize` > `vue-migration-prep` > `lia-testing` > `feature-audit` |
| Criar tela de entrada / branding | `frontend-design` > `design-standardize` > `vue-migration-prep` > `feature-audit` |
| Migrar/criar componente Vue/Vuetify | `vue-vuetify-standardize` > `vue-migration-prep` > `design-standardize` > `feature-audit` |
| Bug fix em qualquer area | `lia-planning` (Diagnosticar) > **`canonical-fix`** > skill de dominio > `lia-testing` |
| Refactor amplo | `lia-planning` (Refactor) > `feature-impact` > `canonical-fix` > skill de dominio > `lia-testing` > `feature-audit` |
| Auditar feature pronta | `feature-audit` > skills das dimensoes que falharem |
| Deploy producao | `lia-compliance` Production Readiness > `feature-audit` final |

Detalhes completos: `.agents/skills/lia-orchestrator/SKILL.md` (Tabela 4).

---

## Catalogo por categoria

### A — Roteador (sempre primeiro)

| Skill | Descricao curta |
|---|---|
| **lia-orchestrator** | Decide a cascata de skills para a tarefa atual (modo + dominio + arquivo) |

### B — Planejamento e impacto

| Skill | Descricao curta |
|---|---|
| **lia-planning** | 4 modos (Bug Fix / Feature / Refactor / Sprint) + spec-driven 4 fases |
| **feature-impact** | Mapeia impacto cross-modulo antes de implementar |

### C — Qualidade por camada (NOVO)

| Skill | Camada |
|---|---|
| **backend-quality** | FastAPI/Python: router fino, service stateless, multi-tenant, N+1, audit log |
| **ai-architecture** | LangGraph/agentes: state tipado, tool isolada, prompt versionado, fallback chain |
| **integration-patterns** | HTTP/fila/storage/OAuth: timeout, retry, circuit breaker, ContextVar, DLQ |

### D — UI / Design

| Skill | Quando |
|---|---|
| **frontend-design** | Tela nova de entrada/branding (PASSO 0 — Intencao Estetica) |
| **design-standardize** | Qualquer componente React+Tailwind (DS v4.2.1, regra 90/10, a11y, perf) |
| **design-patterns** | Refatorar arquitetura de componente (GoF + React patterns) |
| **vue-vuetify-standardize** | Componente Vue 3 + Vuetify + Nuxt (10 passos) |
| **vue-migration-prep** | Garantir portabilidade React -> Vue em todo componente novo |

### E — Compliance e governanca

| Skill | Cobertura |
|---|---|
| **lia-compliance** | PARTE 1 Governanca WeDO / PARTE 2 Screening WSI / PARTE 3 Fairness DEI / PARTE 4 LGPD PII |

### F — Correcao e auditoria

| Skill | Quando |
|---|---|
| **canonical-fix** | Antes de qualquer bug fix, refactor ou edicao com risco de duplicata |
| **feature-audit** | DEPOIS de implementar, ANTES de marcar concluido (14 dimensoes) |

### G — Testes

| Skill | Quando |
|---|---|
| **lia-testing** | TDD (Red/Green/Refactor), piramide 5 camadas, evals IA (golden dataset) |

### H — Utilitarias

| Skill | Quando |
|---|---|
| **browser-use** | Validacao funcional via browser, screenshots |
| **humanizer** | Texto soa "AI generated" |
| **agent-tools** | Rodar 150+ apps IA via inference.sh |
| **excalidraw-diagram** | Diagramas visuais de arquitetura/fluxo |
| **pdf** | Operacoes com PDF |
| **pptx** | Operacoes com apresentacoes |
| **find-skills** | Descobrir skills disponiveis |
| **skill-creator** | Criar/otimizar skills |

---

## Cenarios de validacao (cascata em acao)

### Cenario A — "Crie POST /candidates/screening"

`lia-orchestrator` -> Modo BUILD, Dominio BACKEND+MULTI_TENANT+SCREENING -> cascata:
`canonical-fix` -> `backend-quality` -> `lia-compliance` PARTE 2 + 3 + 4 -> `lia-testing` -> `feature-audit` (D1, D4, D5, D11, D12, D13).

### Cenario B — "Ajusta componente Vue de calibracao"

`lia-orchestrator` -> Modo BUILD, Dominio VUE_MIGRATION+FRONTEND_UI+SCREENING -> cascata:
`canonical-fix` -> `vue-vuetify-standardize` -> `vue-migration-prep` -> `design-standardize` -> `lia-compliance` PARTE 2 -> `lia-testing` -> `feature-audit` (D3, D5, D7).

### Cenario C — "Cria agente novo que usa Pearch como tool externa"

`lia-orchestrator` -> Modo BUILD, Dominio AI_AGENT+INTEGRATION+MULTI_TENANT -> cascata:
`canonical-fix` -> `ai-architecture` -> `integration-patterns` -> `lia-compliance` PARTE 1 + 3 -> `backend-quality` -> `lia-testing` -> `feature-audit` (D9, D10, D11, D12, D13).

Detalhes em `lia-orchestrator/SKILL.md`.

---

## Como pedir

Nao precisa lembrar nomes. O orchestrator decide. Mas se quiser sinalizar:

| Voce diz | Orchestrator entende |
|---|---|
| "vamos planejar" | Modo PLANNING |
| "cria endpoint X" | Modo BUILD + dominio BACKEND |
| "novo agente para Y" | Modo BUILD + dominio AI_AGENT |
| "esta quebrado em Z" | Modo BUG FIX |
| "refatora todo o modulo" | Modo REFACTOR |
| "esta pronto?" | Modo AUDIT |
| "vou subir para producao" | Modo DEPLOY |
