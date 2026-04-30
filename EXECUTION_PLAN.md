# EXECUTION_PLAN.md — WeDO Talent · LIA Agent System

> **Baseline:** commit `41c9a76d6` (PR-K completo)
> **Criado em:** 2026-04-30
> **Repos envolvidos:** `lia-agent-system` · `plataforma-lia`
> **SSH de trabalho:** `ssh -i ~/.ssh/replit replit-wedo`
> **Convenção git:** commits atômicos no Replit via SSH — `git push` EXCLUSIVO do Paulo pelo Replit IDE (branch `replit-sync`)

---

## Índice

1. [Já implementado (não replanejar)](#já-implementado)
2. [Wave 1 — Fechamentos rápidos (1–2 dias)](#wave-1--fechamentos-rápidos)
3. [Wave 2 — PR-RAG: wire search_candidates → pgvector (2–3 dias)](#wave-2--pr-rag)
4. [Wave 3 — talent_pool_agent canonical (2 dias)](#wave-3--talent_pool_agent)
5. [Wave 4 — Pirâmide de testes Rail A (3–5 dias)](#wave-4--pirâmide-de-testes-rail-a)
6. [Wave 5 — Arquitetura FE cleanups (1–2 dias)](#wave-5--arquitetura-fe-cleanups)
7. [Harness Engineering Débito](#harness-engineering-débito)
8. [Como retomar em nova sessão](#como-retomar-em-nova-sessão)

---

## Já implementado

> Estes itens estão CONCLUÍDOS — não incluir em nenhum plano futuro.

| PR | Descrição |
|----|-----------|
| PR-A | `SUGGESTION_HINTS` + `rail_a_hint_override.py` |
| PR-B | `OfferReviewModal` + offer domain completo |
| PR-C | `register_hire` em `pipeline_tools.py` |
| PR-D | `useUIAction.ts` + `ui-action.ts` |
| PR-J | `entity_resolver_service.py` + `capability_map.yaml` (13 intents) |
| PR-K | coming-soon ai-credits + navegação talent-pool/hiring-policy |
| PR-AUTO | automations-tab com `apiFetch` real |
| PR-CAL MVP | `schedule_interview` escreve `Interview` real no DB |
| PR-Q2 | `close_job` + `generate_job_report` no `capability_map` |
| PR-Q3 | `forecast` + `start_wsi_interview` canonical |
| PR-H | `RAIL_A_SUGGESTIONS` de `canonicalFunnelStages` |
| PR-M | `active_jobs` no pulse badge Vaga |

---

## Wave 1 — Fechamentos rápidos

**Status geral:** ⏳ PENDING
**Estimativa:** 1–2 dias
**Princípio:** zero novos arquivos onde possível — modificar os existentes

---

### W1-1 · PR-Q4-FINAL: Remoção segura do domain `policy/`

**Status:** ⏳ PENDING

**Contexto:** `app/domains/policy/` existe com `agents/`, `dependencies.py`, `repositories/`, `services/`. Nenhuma referência foi encontrada em `registry.py` nem imports em `app/**/*.py`. Marcação `@deprecated` ausente nos arquivos do domínio (marker só existe em `briefing_service.py`, não em `policy/`).

**Arquivos envolvidos:**
- `lia-agent-system/app/domains/policy/` — diretório a remover
- `lia-agent-system/app/domains/registry.py` — confirmar ausência de import
- `lia-agent-system/app/api/routes.py` — confirmar ausência de router de policy
- `lia-agent-system/app/tests/test_policy_gaps_fixes.py` — avaliar se os testes testam behavior real ou apenas o domínio morto
- `lia-agent-system/app/tests/test_policy_integration.py` — idem
- `lia-agent-system/app/tests/test_hiring_policy_api.py` — idem (é `hiring_policy`, não `policy` — NÃO remover)

**Skills a aplicar:** `/feature-audit` antes de deletar (14 dimensões de impacto)

**Checklist:**
- [ ] `grep -r "domains.policy\|from.*policy" app/ --include="*.py"` — deve retornar zero hits fora do próprio diretório
- [ ] `grep -r "domains/policy\|domain_id.*policy" app/ --include="*.py" --include="*.yaml"` — zero hits
- [ ] Verificar `app/api/routes.py`: confirmar nenhum `include_router` de policy
- [ ] Verificar `app/tests/test_policy_gaps_fixes.py` e `test_policy_integration.py`: se testam só o domínio morto, deletar junto; se testam behavior de `hiring_policy`, migrar assertions para `test_hiring_policy_api.py`
- [ ] Adicionar `# @deprecated` + `# @remove-after` nos `__init__.py` do diretório (ticket tombstone) antes de deletar
- [ ] Deletar `app/domains/policy/` inteiro
- [ ] Rodar `pytest app/tests/ -x -q` — zero regressões
- [ ] Commit atômico: `chore(policy): remove deprecated policy/ domain — zero references confirmed`

**Definition of Done:**
- Diretório `app/domains/policy/` não existe
- `pytest` verde sem flags `--ignore`
- `grep` por `domains.policy` retorna zero

---

### W1-2 · PR-BRIEF-VERIFY: Validar `daily_briefing` (card 7.2) com dados reais

**Status:** ⏳ PENDING

**Contexto:** `briefing_service.py` está em `app/shared/services/briefing_service.py` com marker `@deprecated since=2026-04-17 @remove-after=2026-07-16 @replacement=integrations_hub/rails_adapter::briefing`. O serviço funciona mas opera sobre entidades Rails via SQLAlchemy direto. Card 7.2 do Rail A usa `daily_briefing` intent.

**Arquivos envolvidos:**
- `lia-agent-system/app/shared/services/briefing_service.py` — serviço legado
- `lia-agent-system/app/api/v1/briefing.py` — endpoint atual
- `lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py` — handler do intent `daily_briefing`
- `lia-agent-system/app/config/capability_map.yaml` — adicionar entry `daily_briefing` se ausente

**Skills a aplicar:** `/feature-impact` antes; `/harness-engineering` para classificar guide × sensor

**Checklist:**
- [ ] Verificar se `daily_briefing` está mapeado em `capability_map.yaml` (buscar entry `daily_briefing:`)
- [ ] Se ausente: adicionar entry com `chat_executable: true`, `navigate_fallback: /analytics`
- [ ] Em `pipeline_actions.py`: localizar handler de `daily_briefing` e confirmar que chama `briefing_service`
- [ ] Adicionar `disclaimer` no response JSON quando `source == "legacy_briefing_service"`:
  ```python
  response["_legacy_disclaimer"] = (
      "Dados gerados via serviço legado (remoção planejada 2026-07-16). "
      "Migração para integrations_hub/rails_adapter em andamento."
  )
  ```
- [ ] Validar que dados retornados não são mock/stub — testar com `company_id` real via `curl` ou pytest
- [ ] Escrever 1 teste de contrato em `app/tests/test_briefing_contract.py`:
  - Deve retornar `urgent_actions`, `pipeline_summary`, `scheduled_activities`
  - Deve incluir `_legacy_disclaimer` no response
- [ ] Rodar `pytest app/tests/test_briefing_contract.py -v`
- [ ] Commit: `fix(briefing): add legacy disclaimer + contract test for daily_briefing (card 7.2)`

**Definition of Done:**
- Card 7.2 retorna dados reais (não mock)
- Response inclui `_legacy_disclaimer` quando usar serviço legado
- 1 teste de contrato verde

---

### W1-3 · PR-Q1-NAV: Cards 1.1 (`create-job`) e 1.2 (`job-template`) com navegação direta

**Status:** ⏳ PENDING

**Contexto:** Cards 1.1 e 1.2 hoje disparam o chat. `SUGGESTION_HINTS` está em `app/orchestrator/services/rail_a_hint_override.py`. `capability_map.yaml` já tem estrutura com `navigate_fallback`. Nenhum `navigate_url` explícito para `/jobs/new` foi encontrado.

**Arquivos envolvidos:**
- `lia-agent-system/app/config/capability_map.yaml` — adicionar entries `create_job` e `job_template`
- `lia-agent-system/app/orchestrator/services/rail_a_hint_override.py` — verificar `SUGGESTION_HINTS` dict
- `plataforma-lia/src/` — verificar se modal de template existe (`JobTemplateModal` ou similar)

**Skills a aplicar:** `/feature-impact` (verificar se `create_job` já existe em outra rota)

**Checklist:**

**Card 1.1 — create-job:**
- [ ] Verificar se `create_job` já existe em `capability_map.yaml` (buscar entry)
- [ ] Se ausente, adicionar:
  ```yaml
  create_job:
    chat_executable: false   # abre wizard direto
    entity_required: []
    navigate_url: /jobs/new  # PR-Q1-NAV: abre wizard sem passar pelo chat
    navigate_fallback: /jobs/new
  ```
- [ ] Em `rail_a_hint_override.py`: verificar `SUGGESTION_HINTS["create-job"]` e confirmar `intent_hint: "create_job"`
- [ ] Verificar em `plataforma-lia/src/` se `useUIAction` já trata `navigate_url` (deve estar em `ui-action.ts` do PR-D)

**Card 1.2 — job-template:**
- [ ] Buscar em `plataforma-lia/src/` por `JobTemplate`, `TemplateModal`, `job-template` para confirmar se modal existe
- [ ] Se modal existe: adicionar em `capability_map.yaml`:
  ```yaml
  job_template:
    chat_executable: false
    entity_required: []
    modal_id: job_template_selector
    navigate_fallback: /jobs/new?from=template
  ```
- [ ] Se modal NÃO existe: marcar como `coming_soon: true` em `capability_map.yaml` e documentar em `ARCHITECTURE.md`
- [ ] Rodar `pytest app/tests/ -k "capability_map or nav" -v` para validar novo YAML
- [ ] Commit: `feat(nav): PR-Q1-NAV — create-job navegação direta /jobs/new + job-template mapping`

**Definition of Done:**
- Card 1.1 abre `/jobs/new` diretamente sem passar pelo chat
- Card 1.2 tem rota declarada (modal ou coming_soon)
- Testes do `capability_map` verdes

---

## Wave 2 — PR-RAG

**Status geral:** ⏳ PENDING
**Estimativa:** 2–3 dias
**Harness:** guide = `capability_map.yaml` + sensor = teste de contrato RAG

---

### W2-1 · Wire `search_candidates` para pgvector

**Status:** ⏳ PENDING

**Contexto:**
- Endpoint RAG existente: `app/api/v1/rag_search.py` → `GET /api/v1/candidates/rag-search`
- Endpoint possui `FairnessGuard` embutido (campo `fairness_ok` no response)
- Tool atual: `app/domains/sourcing/tools/query_tools.py::search_candidates()` — usa SQLAlchemy puro
- RAG service: `app/domains/ai/services/rag_pipeline_service.py` (canônico) e `app/shared/services/rag_pipeline_service.py` (legacy — verificar qual usar)

**Arquivos envolvidos:**
- `lia-agent-system/app/domains/sourcing/tools/query_tools.py` — modificar `search_candidates()`
- `lia-agent-system/app/domains/ai/services/rag_pipeline_service.py` — RAG service canônico
- `lia-agent-system/app/config/capability_map.yaml` — confirmar `search_candidates` entry
- `lia-agent-system/app/tests/` — criar `test_search_candidates_rag_contract.py`

**Skills a aplicar:**
1. `/feature-impact` ANTES (12 dimensões) — avaliar impacto em candidatos existentes
2. `/harness-engineering` DURANTE — classificar guide × sensor
3. `/feature-audit` DEPOIS (14 dimensões) + G7 sensor

**Checklist:**

**Fase 1 — Diagnóstico (RED):**
- [ ] Escrever teste de contrato ANTES de modificar o tool:
  ```python
  # app/tests/test_search_candidates_rag_contract.py
  # Cenário A: query linguagem natural → deve usar RAG
  # Cenário B: filtros estruturados (skills=[...]) → deve usar SQL
  # Cenário C: FairnessGuard sempre presente no response
  ```
- [ ] Confirmar qual `rag_pipeline_service.py` é canônico (domains/ai vs shared)
- [ ] Verificar assinatura de `rag_pipeline_service.search()` — parâmetros esperados

**Fase 2 — Implementação (GREEN):**
- [ ] Adicionar helper `_is_natural_language_query(kwargs: dict) -> bool`:
  - Retorna `True` quando apenas `query: str` presente sem `skills`, `seniority`, `min_score`
  - Retorna `False` quando filtros estruturados presentes
- [ ] Modificar `search_candidates()` para bifurcar:
  ```python
  if _is_natural_language_query(kwargs):
      # usa rag_pipeline_service — pgvector + BM25 hybrid
      results = await rag_pipeline_service.search(
          query=query_text,
          company_id=company_id,  # OBRIGATÓRIO — multi-tenancy
          limit=limit,
          alpha=0.5,
      )
  else:
      # fallback SQL existente (sem modificação)
      ...
  ```
- [ ] Garantir `company_id` passado em TODOS os caminhos (multi-tenancy obrigatório)
- [ ] FairnessGuard: resultado RAG já tem `fairness_ok` — propagar para response do tool
- [ ] Nunca coletar campos LGPD-proibidos (race, gender, health) no resultado

**Fase 3 — Harness (REFACTOR):**
- [ ] Adicionar ao `capability_map.yaml` sob `search_candidates`:
  ```yaml
  rag_enabled: true
  rag_fallback: sql_structured_filters
  fairness_guard: mandatory
  ```
- [ ] Sensor: `test_search_candidates_rag_contract.py` deve passar
- [ ] Sensor: `pytest app/tests/test_multi_tenancy_security.py` — zero regressões

**Definition of Done:**
- Query linguagem natural usa pgvector (resposta inclui `source: "semantic"` ou `"hybrid"`)
- Filtros estruturados continuam usando SQL (backward compatible)
- `company_id` validado em ambos os caminhos
- FairnessGuard presente em resultado de candidatos
- Testes de contrato verdes

---

## Wave 3 — talent_pool_agent

**Status geral:** ⏳ PENDING
**Estimativa:** 2 dias
**Base:** `app/domains/talent_pool/` tem `actions.py`, `domain.py`, `config/capabilities.yaml` mas `agents/` está vazio

---

### W3-1 · Criar agente ReAct canonical para `talent_pool`

**Status:** ⏳ PENDING

**Contexto:**
- `app/domains/talent_pool/config/capabilities.yaml` já declara 8 intents mapeados a tools
- `app/domains/talent_pool/actions.py` — implementações de actions existem (verificar)
- `app/domains/talent_pool/domain.py` — domain class base existe
- Skill disponível no workspace: `/create-canonical-agent`
- `high_impact: true` implícito pois envolve candidatos → FairnessGuard obrigatório

**Arquivos a criar:**
- `lia-agent-system/app/domains/talent_pool/agents/talent_pool_agent.py` — agente ReAct
- `lia-agent-system/app/domains/talent_pool/tools/pool_tools.py` — tools do agente
- `lia-agent-system/app/tests/test_talent_pool_agent_contract.py` — testes

**Arquivos a modificar:**
- `lia-agent-system/app/domains/registry.py` — registrar `talent_pool` domain
- `lia-agent-system/app/config/capability_map.yaml` — adicionar entries talent_pool

**Skills a aplicar:**
1. `/create-canonical-agent` para scaffolding do agente
2. `/feature-audit` DEPOIS para validar 14 dimensões
3. `/harness-engineering` — FairnessGuard como sensor obrigatório

**Checklist:**

**Fase 1 — Scaffolding (skill /create-canonical-agent):**
- [ ] Verificar `app/domains/talent_pool/actions.py` — listar functions disponíveis
- [ ] Invocar `/create-canonical-agent` com:
  - `domain_id: talent_pool`
  - Tools: `list_talent_pools`, `create_talent_pool`, `add_candidate_to_pool`, `create_job_from_pool`
  - `high_impact: true` (FairnessGuard obrigatório)
  - Base class: `ComplianceDomainPrompt` (LIA-C01)

**Fase 2 — Tools (TDD RED→GREEN):**
- [ ] Escrever testes ANTES:
  ```python
  # test_talent_pool_agent_contract.py
  # test_list_talent_pools_requires_company_id
  # test_create_talent_pool_validates_tenant
  # test_add_candidate_applies_fairness_guard
  # test_create_job_from_pool_multi_tenant
  ```
- [ ] Implementar `pool_tools.py`:
  - `list_talent_pools(company_id)` — SEMPRE filtrar por `company_id`
  - `create_talent_pool(name, company_id, criteria)` — validar `company_id` do JWT, não do payload
  - `add_candidate_to_pool(pool_id, candidate_id, company_id)` — FairnessGuard antes de adicionar
  - `create_job_from_pool(pool_id, job_data, company_id)` — registrar no `capability_map`

**Fase 3 — Harness:**
- [ ] Adicionar entries em `capability_map.yaml`:
  ```yaml
  list_talent_pools:
    chat_executable: true
    entity_required: []
    navigate_fallback: /talent-pool
    fairness_guard: false   # listagem não exige

  create_talent_pool:
    chat_executable: true
    entity_required: []
    navigate_fallback: /talent-pool/new

  add_candidate_to_pool:
    chat_executable: true
    entity_required:
      - type: candidate
        param: candidate_id
      - type: pool
        param: pool_id
    navigate_fallback: /talent-pool
    fairness_guard: true   # high_impact: candidatos

  create_job_from_pool:
    chat_executable: false   # abre wizard de vaga
    entity_required:
      - type: pool
        param: pool_id
    navigate_url: /jobs/new?from=pool
    navigate_fallback: /jobs/new
  ```
- [ ] Registrar domain em `registry.py`
- [ ] Rodar `/feature-audit` pós-implementação
- [ ] Rodar `pytest app/tests/test_talent_pool_agent_contract.py -v`

**Definition of Done:**
- `app/domains/talent_pool/agents/talent_pool_agent.py` existe e é importável
- 4 tools implementadas com `company_id` obrigatório
- FairnessGuard ativo em `add_candidate_to_pool`
- `capability_map.yaml` tem 4 entries novas
- Domain registrado em `registry.py`
- Testes de contrato verdes

---

## Wave 4 — Pirâmide de testes Rail A

**Status geral:** ⏳ PENDING
**Estimativa:** 3–5 dias
**Base:** hoje há `app/tests/` com ~22 arquivos pytest e `plataforma-lia/e2e/tests/` com testes Playwright

---

### W4-1 · Golden dataset + testes de routing

**Status:** ⏳ PENDING

**Arquivos envolvidos:**
- `lia-agent-system/app/tests/` — novos arquivos de teste
- `lia-agent-system/app/orchestrator/services/rail_a_hint_override.py` — sistema sob teste
- `lia-agent-system/app/config/capability_map.yaml` — fonte de verdade de routing

**Skills a aplicar:** `/harness-engineering` (sensor feedback)

**Checklist:**

**Golden Dataset (22 comandos × 5 variações):**
- [ ] Criar `app/tests/fixtures/rail_a_golden_dataset.json`:
  ```json
  {
    "commands": [
      {
        "id": "create_job",
        "variations": [
          "criar vaga", "nova vaga", "abrir posição",
          "quero contratar", "preciso de um dev"
        ],
        "expected_intent": "create_job",
        "expected_domain": "job_creation"
      }
      // ... 21 comandos mais
    ]
  }
  ```
- [ ] Cobrir todos os 22 cards funcionais (excluir `COMING_SOON`)
- [ ] 5 variações linguísticas por card (formal, informal, fragmentado, com erro de digitação, em inglês)

**Testes de routing determinístico:**
- [ ] Criar `app/tests/test_rail_a_routing_deterministic.py`:
  - `test_hint_override_bypasses_router` — com `source: "rail_a"` + `domain_hint` válido → `confidence == 0.99`
  - `test_hint_override_rejects_invalid_domain` — domain não registrado → fallback ao router
  - `test_hint_override_rejects_missing_source_flag` — sem `source: "rail_a"` → fallback
  - `test_golden_dataset_routing` — parametrizado com o JSON acima
- [ ] Todos os testes devem rodar sem chamar LLM real (mock do router)

**LLM-as-judge stub:**
- [ ] Criar `app/tests/stubs/llm_judge_stub.py`:
  - Template de prompt para avaliar qualidade de resposta (não chamar LLM agora)
  - Estrutura: `{"query": ..., "response": ..., "criteria": ["relevância", "completude", "fairness"]}`
  - Marcado com `@pytest.mark.skip(reason="LLM-as-judge real — ativar em CI premium")`

**Definition of Done:**
- `app/tests/fixtures/rail_a_golden_dataset.json` com 22 × 5 = 110 variações
- `test_rail_a_routing_deterministic.py` com ≥ 15 testes, todos verdes
- Stub LLM-as-judge commitado (mesmo que skipado)

---

### W4-2 · E2E Playwright — smoke dos 22 cards funcionais

**Status:** ⏳ PENDING

**Arquivos envolvidos:**
- `plataforma-lia/e2e/tests/` — novos arquivos Playwright
- `plataforma-lia/e2e/fixtures/` — fixtures existentes

**Skills a aplicar:** `/lia-testing` guidelines (se disponível no workspace)

**Checklist:**
- [ ] Listar os 22 cards funcionais (excluir `COMING_SOON`) a partir de `SUGGESTION_HINTS`
- [ ] Criar `plataforma-lia/e2e/tests/rail_a_smoke.spec.ts`:
  - Para cada card: verificar que clique no card dispara ação correta (navegação ou modal ou chat)
  - Não testar lógica de negócio — apenas que a UI não quebra (smoke test)
  - Usar `data-testid` existentes ou adicionar mínimos necessários
- [ ] Criar `plataforma-lia/e2e/tests/rail_a_navigation.spec.ts`:
  - Cards com `navigate_url` devem redirecionar para URL correta
  - Verificar ausência de 404 nas rotas
- [ ] Garantir que testes rodam com `COMING_SOON` cards ignorados (skip por `data-card-status`)

**Definition of Done:**
- 22 smoke tests Playwright passando localmente
- Zero testes quebrando por cards `COMING_SOON`

---

## Wave 5 — Arquitetura FE cleanups

**Status geral:** ⏳ PENDING
**Estimativa:** 1–2 dias

---

### W5-1 · FE-S03: hex hardcoded → DS tokens

**Status:** ⏳ PENDING

**Contexto:** `globals.css` e componentes usam `var(--wedo-cyan, #60BED1)` com fallback hex. Design System canônico é `00-design-system-v4.2.2.md`. Regra non-negotiable: nunca hardcoded hex.

**Arquivos envolvidos:**
- `plataforma-lia/src/app/globals.css`
- `plataforma-lia/src/app/error.tsx`
- `plataforma-lia/src/app/not-found.tsx`
- `plataforma-lia/src/app/[locale]/login/welcome/_components/WelcomeSteps.tsx`
- `plataforma-lia/src/app/[locale]/design-system/page.tsx`
- (buscar mais arquivos com `grep -r "wedo-cyan" src/`)

**Skills a aplicar:** `/production-quality:modules:frontend-quality`

**Checklist:**
- [ ] Ler `00-design-system-v4.2.2.md` para mapear tokens canônicos correspondentes a cada cor hex
- [ ] Substituir `var(--wedo-cyan, #60BED1)` → `var(--wedo-cyan)` (sem fallback hex inline)
- [ ] Garantir que `globals.css` define `--wedo-cyan` como variável CSS sem valor hex literal no consumer
- [ ] Buscar outros padrões: `#60BED1`, `#3B82F6`, `#10B981` — mapear para tokens
- [ ] Rodar build local: `bun run build` ou `npm run build` — zero erros TypeScript
- [ ] Commit: `style(tokens): FE-S03 — substituir hex hardcoded por DS tokens v4.2.2`

**Definition of Done:**
- Zero ocorrências de `#[0-9A-Fa-f]{6}` fora de `globals.css` e arquivos de definição de tokens
- Build verde sem erros

---

### W5-2 · FE-S06: compact mode — paridade com expanded

**Status:** ⏳ PENDING

**Contexto:** Compact mode não mostra pulse badge nem dock magnifier. Arquivos: `FunilDeTalentosClient.tsx` tem lógica de pulse; `KanbanCardShell.tsx` tem compact; sem dock magnifier identificado.

**Arquivos envolvidos:**
- `plataforma-lia/src/app/[locale]/(dashboard)/funil-de-talentos/FunilDeTalentosClient.tsx`
- `plataforma-lia/src/components/pages/job-kanban/KanbanCardShell.tsx`
- (buscar arquivos com `grep -r "compact" src/ --include="*.tsx" -l`)

**Skills a aplicar:** `/production-quality:modules:frontend-quality`

**Checklist:**
- [ ] Mapear onde `compact` prop/mode suprime o pulse badge
- [ ] Adicionar condição: mostrar pulse badge mesmo em compact (tamanho reduzido, ex: `size="sm"`)
- [ ] Verificar se dock magnifier existe como componente — se sim, garantir que aparece em compact
- [ ] Testar visualmente nos breakpoints: mobile (compact) e desktop (expanded)
- [ ] Commit: `fix(ux): FE-S06 — compact mode mostra pulse badge + dock magnifier`

**Definition of Done:**
- Pulse badge visível em compact mode (pode ser menor)
- Dock magnifier visível em compact mode (se componente existir)
- Nenhuma regressão em expanded mode

---

### W5-3 · INT-S02: eleger classifier canônico

**Status:** ⏳ PENDING

**Contexto:**
- `app/domains/ai/services/enhanced_intent_classifier.py` — classifier sofisticado
- `app/shared/services/keyword_intent_matcher.py` — matcher por keywords
- Coexistem sem um sendo eleito canônico — risco de drift de comportamento

**Arquivos envolvidos:**
- `lia-agent-system/app/domains/ai/services/enhanced_intent_classifier.py`
- `lia-agent-system/app/shared/services/keyword_intent_matcher.py`
- `lia-agent-system/app/orchestrator/` — verificar qual é importado no orchestrator

**Skills a aplicar:** `/harness-engineering` (guide: eleger canônico = guide computacional)

**Checklist:**
- [ ] Buscar imports de ambos no orchestrator: `grep -r "enhanced_intent_classifier\|keyword_intent_matcher" app/orchestrator/ --include="*.py"`
- [ ] Determinar qual é chamado no hot path (ProcessRequest)
- [ ] Eleger `enhanced_intent_classifier` como canônico (mais sofisticado)
- [ ] Adicionar em `keyword_intent_matcher.py`:
  ```python
  # @deprecated since=2026-04-30
  # @remove-after=2026-07-30
  # @owner=backend-platform
  # @replacement=app/domains/ai/services/enhanced_intent_classifier.py
  # Mantido apenas para backward compat — não usar em novo código.
  ```
- [ ] Verificar se algum teste depende de `keyword_intent_matcher` — se sim, migrar para usar `enhanced_intent_classifier`
- [ ] Adicionar comentário em `ARCHITECTURE.md` ou `docs/` documentando a decisão
- [ ] Commit: `refactor(classifier): INT-S02 — eleger enhanced_intent_classifier canônico, deprecate keyword_matcher`

**Definition of Done:**
- `keyword_intent_matcher.py` marcado `@deprecated` com data e replacement
- Zero novos imports de `keyword_intent_matcher` no codebase
- `pytest` verde

---

## Harness Engineering Débito

> Classificação de todos os guides e sensors pendentes por wave.
> Taxonomia: **guide** (feedforward, reduz P(erro)) × **sensor** (feedback, detecta erro)
> Subtipo: **computacional** (determinístico) × **inferencial** (LLM/heurístico)

### Wave 1

| Item | Tipo | Subtipo | Débito |
|------|------|---------|--------|
| W1-1: `policy/` ausente do registry | Guide | Computacional | Adicionar CI check: `domains/` sem entry em `registry.py` → warning |
| W1-2: `daily_briefing` sem entry no `capability_map` | Guide | Computacional | Adicionar validator: todo intent ativo deve estar em `capability_map.yaml` |
| W1-2: legacy disclaimer | Sensor | Computacional | Teste de contrato verifica presença do disclaimer |
| W1-3: `create_job` navigate_url | Guide | Computacional | `capability_map` como fonte de verdade + teste que valida `navigate_url` presente |

### Wave 2

| Item | Tipo | Subtipo | Débito |
|------|------|---------|--------|
| RAG routing bifurcation | Guide | Computacional | `_is_natural_language_query()` determinístico — sem LLM no routing |
| FairnessGuard RAG | Sensor | Computacional | `fairness_ok: bool` no response — teste verifica presença |
| `company_id` obrigatório | Guide | Computacional | Multi-tenancy rule: adicionar ao CLAUDE.md como check automático para `*tool*.py` |
| Contrato RAG | Sensor | Computacional | `test_search_candidates_rag_contract.py` em CI |

### Wave 3

| Item | Tipo | Subtipo | Débito |
|------|------|---------|--------|
| `add_candidate_to_pool` FairnessGuard | Guide | Computacional | `fairness_guard: true` em `capability_map.yaml` — sensor: teste verifica |
| talent_pool domain_id em registry | Guide | Computacional | `register_domain` decorator garante auto-discovery |
| Contrato tools | Sensor | Computacional | `test_talent_pool_agent_contract.py` em CI |

### Wave 4

| Item | Tipo | Subtipo | Débito |
|------|------|---------|--------|
| Golden dataset | Guide | Computacional | 110 variações como fixture imutável — PRs não podem remover variações |
| Routing determinístico | Sensor | Computacional | `test_rail_a_routing_deterministic.py` — zero calls LLM no teste |
| LLM-as-judge stub | Sensor | Inferencial | Template pronto — ativar em CI premium quando custo justificar |
| E2E Playwright smoke | Sensor | Computacional | 22 tests — gate de merge para PRs que tocam Rail A |

### Wave 5

| Item | Tipo | Subtipo | Débito |
|------|------|---------|--------|
| Hex hardcoded | Guide | Computacional | Linter CSS/TS que rejeita `#[0-9A-Fa-f]{6}` fora de `globals.css` |
| Classifier canônico | Guide | Computacional | `@deprecated` no `keyword_intent_matcher` + CI grep que rejeita novo import |

---

## Como retomar em nova sessão

### Arquivos para ler primeiro (em ordem de prioridade)

```
# Estado do sistema
/home/runner/workspace/lia-agent-system/ARCHITECTURE.md
/home/runner/workspace/lia-agent-system/CLAUDE.md
/home/runner/workspace/lia-agent-system/DEVELOPER_HANDOFF.md

# Fonte de verdade de capabilities e routing
/home/runner/workspace/lia-agent-system/app/config/capability_map.yaml
/home/runner/workspace/lia-agent-system/app/orchestrator/services/rail_a_hint_override.py
/home/runner/workspace/lia-agent-system/app/domains/registry.py

# Arquivos de trabalho por wave
# Wave 1:
/home/runner/workspace/lia-agent-system/app/domains/policy/   (remover)
/home/runner/workspace/lia-agent-system/app/shared/services/briefing_service.py
/home/runner/workspace/lia-agent-system/app/api/v1/briefing.py

# Wave 2:
/home/runner/workspace/lia-agent-system/app/domains/sourcing/tools/query_tools.py
/home/runner/workspace/lia-agent-system/app/domains/ai/services/rag_pipeline_service.py
/home/runner/workspace/lia-agent-system/app/api/v1/rag_search.py

# Wave 3:
/home/runner/workspace/lia-agent-system/app/domains/talent_pool/domain.py
/home/runner/workspace/lia-agent-system/app/domains/talent_pool/actions.py
/home/runner/workspace/lia-agent-system/app/domains/talent_pool/config/capabilities.yaml

# Wave 4:
/home/runner/workspace/lia-agent-system/app/tests/
/home/runner/workspace/plataforma-lia/e2e/tests/

# Wave 5:
/home/runner/workspace/plataforma-lia/src/app/globals.css
/home/runner/workspace/lia-agent-system/app/domains/ai/services/enhanced_intent_classifier.py
/home/runner/workspace/lia-agent-system/app/shared/services/keyword_intent_matcher.py
```

### Comando de verificação rápida de estado

```bash
# Ver último commit
cd /home/runner/workspace/lia-agent-system && git log --oneline -5

# Testes verdes?
cd /home/runner/workspace/lia-agent-system && python -m pytest app/tests/ -x -q --tb=short 2>&1 | tail -20

# policy/ ainda existe?
ls /home/runner/workspace/lia-agent-system/app/domains/policy/ 2>/dev/null && echo "EXISTE — Wave 1 pendente" || echo "REMOVIDO"

# capability_map intents
grep "^  [a-z]" /home/runner/workspace/lia-agent-system/app/config/capability_map.yaml
```

### Convenções obrigatórias (resumo)

| Regra | Aplicação |
|-------|-----------|
| `company_id` do JWT, nunca do payload | Todo `*tool*.py`, `*service*.py` com dados de candidatos |
| FairnessGuard | Todo tool que lê/rankeia candidatos (`high_impact: true`) |
| Sem hex hardcoded | Todo `*.tsx`, `*.css` — usar tokens do DS v4.2.2 |
| Commits atômicos, sem `git push` | Paulo faz push manualmente via Replit IDE |
| TDD red→green→refactor | Cada novo tool ou service |
| `@deprecated` antes de deletar | Tombstone + data + replacement antes de qualquer remoção |
| `/feature-impact` antes, `/feature-audit` depois | Toda wave de implementação |

---

*Gerado em: 2026-04-30 — Baseline: commit `41c9a76d6`*
