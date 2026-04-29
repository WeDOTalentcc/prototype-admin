# Wizard Canonical Gap Audit — 2026-04-29

**Autor:** audit canônico via SSH `replit-wedo`
**Escopo:** matriz `feature × wizard` mapeando dois sistemas de wizard coexistentes em `lia-agent-system`
**Status:** auditoria de leitura apenas — nenhum código de produção alterado
**Origem:** Cenário A do E2E Playwright falhou porque a LIA chat usa `JobCreationGraph` (LangGraph canônico, Task #850) mas Onda 25 plugou `_suggest_template_type` apenas no `WizardStepService` (REST). Suspeita: outras features de Ondas 23–30 também foram wiradas só no REST.

**TL;DR:**
- `WizardStepService` (REST) **NÃO TEM CALLER DE PRODUÇÃO**. As 5 rotas em `app/api/v1/lia_assistant/wizard.py` retornam **HTTP 410 Gone** (Task #850, deprecated). Idem `WizardOrchestratorService.get_wizard_step` (linha 368). Idem `app.domains.ai.services.graph_runner.stream_job_wizard` (Task #857).
- Logo: **TODAS as features das Ondas 23–30 plugadas em `wizard_step_service/stage_*.py` são código morto em produção.**
- 6 features das Ondas 23–25 e 30 estão **GAP em `JobCreationGraph`**.
- Recomendação: cliff-rollback do `WizardStepService` (deprecar/deletar) + migrar 6 features ao graph como nodes/sub-services dedicados.

---

## Seção 1 — Matriz feature × wizard

Legenda: `✅` presente | `❌` ausente | `~` parcial (chama via service compartilhado mas não no fluxo dedicado) | `DEAD` exists mas sem caller

### 1.1 Tabela canônica

| # | Feature                                  | JobCreationGraph (LangGraph)                       | WizardStepService (REST, DEAD)                                       | Gap real? |
|---|------------------------------------------|----------------------------------------------------|----------------------------------------------------------------------|-----------|
| 1 | `_suggest_template_type` (Onda 25 C.5)   | ❌ ausente                                         | ✅ `stage_basic_info.py:70,178`                                      | **YES — P0** |
| 2 | WSIQuestionGenerator canonical (Onda 23) | ✅ `graph.py:30,81-86` (wsi_questions_node)        | ✅ `stage_wsi.py:54,138` (mesmo singleton)                           | NO (compartilhado) |
| 3 | JdEnrichmentService canonical (Onda 23)  | ✅ `graph.py:29,74-78` (jd_enrichment_node)        | ✅ `stage_review.py:107` (POST-processing duplo)                     | NO (compartilhado) |
| 4 | ats_job_history em stage_description (Onda 25 F.1) | ❌ ausente — graph não tem stage description    | ✅ `stage_description.py:33,42`                                      | **YES — P1** |
| 5 | seniority_resolver                       | ✅ `graph.py:25-27,545` (`resolve_seniority_full`) | ✅ `stage_wsi.py:53,68` (`resolve_seniority_simple`)                 | NO (compartilhado, granularidade diferente) |
| 6 | salary cross com ats_history (Onda 30 F.3) | ❌ `salary_node` (`graph.py:499-527`) só lê `salary_benchmark` precomputado | ✅ `stage_salary.py:21,217` (3ª fonte ats_history + cutoff LGPD 365d) | **YES — P0** |
| 7 | screening_mode persistence (Onda 25 F.2) | ✅ `state.py:150` (state field) + lido em vários nodes | ✅ `service.py:587-597` (parsing keywords)                       | **YES — P1** (gap = parsing keywords no graph) |
| 8 | seniority_confirmation < 0.7 (Onda 24 C.3) | ❌ graph não emite `requires_seniority_confirmation` flag | ✅ `stage_description.py:422`                                  | **YES — P1** |
| 9 | WSI mode selection (compact 5 vs full 12) (Onda 24 C.3) | ✅ `_get_question_distribution` (`graph.py:1411`) com modes compact/full | ✅ `stage_wsi.py:11,140` (parametrizado)                | NO (compartilhado) |
| 10 | calibração opcional pós-publish (Onda 24 C.3) | ✅ `calibration_node` (`graph.py:1146`) + `route_after_publish` (`graph.py:1389`) | ✅ `stage_publication.py:handle_calibration` | NO (compartilhado) |
| 11 | apply_learning hooks (F.1/F.2/F.3 BRANCH_MAP:618-620) | ❌ ausente                                | ✅ `stage_description.py`, `stage_basic_info.py`, `stage_wsi.py` | **YES — P2** |
| 12 | template_type field em state            | ❌ não existe em `JobCreationState` (`state.py:1-220`) | ✅ retornado em `suggestions_data.template_type`              | **YES — P0** (depende de #1) |

### 1.2 Achados-chave do reverse-trace

Search 1 (`grep -rn 'feature' /home/runner/workspace/lia-agent-system/app/domains/job_creation`) e Search 2 (`grep -rn 'feature' /home/runner/workspace/lia-agent-system/app/domains/job_management`):

- **`_suggest_template_type`**: **0 hits** em `job_creation/`, **2 hits** em `job_management/wizard_step_service/stage_basic_info.py:70,178`. Função local privada, não exposta como service.
- **`WSIQuestionGenerator`**: classe singleton em `job_creation/services/wsi_question_generator.py:192`. Importada por `graph.py:30` (wsi_questions_node) e `stage_wsi.py:54` (REST). Service compartilhado.
- **`JdEnrichmentService`**: classe singleton em `job_creation/services/jd_enrichment.py:169`. Importada por `graph.py:29` (jd_enrichment_node) e `stage_review.py:107` (REST POST-process). Service compartilhado MAS chamado em fases diferentes (graph: F1 inicial; REST: pós-geração).
- **`ats_job_history_service`**: importado em `stage_description.py:33,42` e `stage_salary.py:21,217`. **Zero referências em `job_creation/graph.py`**.
- **`seniority_resolver`**: 5 hits em `job_creation/graph.py` (linhas 25,27,545,553) chamando `resolve_seniority_full` (versão completa, 5 sinais). 2 hits em `stage_wsi.py:53,68` chamando `resolve_seniority_simple` (versão simplificada). Graph já é canonical para essa feature.
- **`screening_mode`**: 19 hits em `job_creation/` (state, graph, domain, compliance, api_client). 4 hits em `stage_wsi.py` + `service.py` (parsing). Graph **persiste o campo** corretamente, mas o **parsing de keywords ("compacta"/"completa")** vive só no REST (`service.py:587-597`).
- **`apply_learning`**: zero hits em `job_creation/`, presente apenas em `wizard_step_service/stage_*.py` via `_shared.py`.

---

## Seção 2 — Como o chat real roteia

### 2.1 Caminho da request "Quero criar uma vaga" no chat

```
┌────────────────────────────────────────────────────────────┐
│ Frontend (plataforma-lia)                                  │
│   UnifiedChat → WS /api/v1/ws/chat/{session_id}            │
│   Payload: { type:"message", domain:"wizard" | "auto",     │
│              content:"Quero criar uma vaga..." }            │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│ app/api/v1/agent_chat_ws.py:917                            │
│   active_domain = msg.get("domain", domain)                │
│   pre_compliance(content, company_id, active_domain) [934] │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│ Roteamento via CascadedRouter (Fase 2)                     │
│   agent_chat_ws.py:1059-1083                               │
│   if active_domain in ("auto","recruiter_assistant",""):   │
│       route = CascadedRouter().route(content)              │
│       active_domain = route.domain_id                      │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼ (active_domain == "wizard")
┌────────────────────────────────────────────────────────────┐
│ _get_agent("wizard") → AgentRegistry().get_or_fallback()   │
│   agent_chat_ws.py:321-376, 1097                           │
│   ⚠ NENHUM @register_agent("wizard") na codebase           │
│      (apenas em docstring de agent_registry.py:14)         │
│   ⇒ fallback "talent" agent ASSUME a request                │
│      EXCETO no resume HITL path                             │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼ (PATH A: fallback talent agent — primeira interação)
                    [não-canonical fallback]

                           │
                           ▼ (PATH B: HITL resume — após aprovação)
┌────────────────────────────────────────────────────────────┐
│ agent_chat_ws.py:719-786                                   │
│   if resume_domain == "wizard":                            │
│     _resume_wizard_canonical_streaming(thread_id,          │
│                                        resume_input,       │
│                                        on_token)           │
│   ↳ from app.domains.job_creation.graph                    │
│         import job_creation_graph as wiz_g                 │
│   ↳ wiz_g.stream_invoke(merged_state, thread_id, on_token) │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│ JobCreationGraph (Task #850 canonical)                     │
│   app/domains/job_creation/graph.py:1614-1854              │
│   intake → jd_enrichment ─HITL→ bigfive → salary           │
│       → competency → wsi_questions ─HITL→ eligibility      │
│       → review → publish → calibration → handoff → END     │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Anomalia descoberta no roteamento

Em `agent_chat_ws.py:917-1097` o caminho **inicial** (não-resume) chama `_get_agent("wizard")`, que via `AgentRegistry` deveria devolver um agente registado com `@register_agent("wizard")`. **Esse decorator não existe em código de produção** — apenas no docstring de exemplo de `app/shared/agents/agent_registry.py:14`. O comentário em `agent_chat_ws.py:515` confirma: "WizardReActAgent removed in Task #850 — JobCreationGraph replaces it." Logo:

- **Resume HITL path (após aprovação JD/WSI)**: chama `JobCreationGraph` via `_resume_wizard_canonical_streaming`. Caminho canônico. ✅
- **Caminho inicial ("Quero criar uma vaga")**: cai no `fallback="talent"` do `AgentRegistry.get_or_fallback`, ou seja, o agente talent generic absorve o pedido. **A entrada conversacional canônica do Wizard via WS está quebrada conceitualmente** — a única forma correta é forçar `domain="wizard"` no payload OU usar a chamada legada `GraphRunnerService.run_job_wizard` (`graph_runner.py:223`) que ainda existe como compatibility shim.

### 2.3 Conclusão estrutural

`JobCreationGraph` é canonical (Task #850, comentário `graph_runner.py:223-228`), MAS:

1. Não há `@register_agent("wizard")` registrado para a entrada conversacional inicial.
2. `WizardStepService` está em `app/domains/job_management/services/wizard_step_service/` mas **as únicas rotas que o expunham retornam 410 Gone** (`lia_assistant/wizard.py`, `wizard_orchestrator_service.get_wizard_step:355-372`).
3. Ondas 23–30 plugaram features novas em `wizard_step_service/stage_*.py` que **não atingem produção** — vivem em código morto.

---

## Seção 3 — Estrutura do JobCreationGraph

### 3.1 Resumo numérico

- **Arquivo:** `app/domains/job_creation/graph.py` (1860 linhas)
- **Classe pública:** `JobCreationGraph` (singleton, `graph.py:1614-1854`)
- **Builder:** `create_job_creation_graph(checkpointer=None)` (`graph.py:1486-1610`)
- **Total nodes:** 11
- **Conditional edges:** 7 (todas com fast-path `END`)
- **Linear edges:** 2 (`intake→jd_enrichment`, `eligibility→review`, `handoff→END`)
- **HITL gates:** 2 (após JD enrichment e WSI questions; padrão guide-first via conditional edge, ver Onda 30 C.4)

### 3.2 Lista de nodes

| # | Node | Função | Linhas | Lê do user (perguntas livres)? |
|---|------|--------|--------|--------------------------------|
| 1 | `intake_node` | Pre-F1: `IntakeExtractor` extrai estrutura de free-text | 109–187 | **SIM** (free text + right_panel_form + attached_file) |
| 2 | `jd_enrichment_node` | F1: `JdEnrichmentService.enrich()` — quality + fairness | 190–333 | NÃO (recebe `jd_raw` ou `raw_input`); HITL pause |
| 3 | `bigfive_node` | F2+F3: extração Big Five + ranking de traits | 335–497 | NÃO |
| 4 | `salary_node` | Validação salary range vs benchmark | 499–527 | NÃO (lê benchmark precomputado) |
| 5 | `competency_node` | F4+F5: `resolve_seniority_full` + question distribution | 530–617 | NÃO |
| 6 | `wsi_questions_node` | F6: gera perguntas via `WSIQuestionGenerator` | 620–851 | NÃO; HITL pause |
| 7 | `eligibility_node` | Pre-screening yes/no questions | 853–878 | NÃO |
| 8 | `review_node` | Readiness check + apply company defaults from Settings | 880–935 | NÃO |
| 9 | `publish_node` | Publica via Rails | 937–1144 | NÃO; HITL gate (policy_confirmed_publish) |
| 10 | `calibration_node` | Calibração 3+ profiles | 1146–1206 | NÃO |
| 11 | `handoff_node` | Navega para job page | 1208–1283 | NÃO |

### 3.3 Conditional edges

```python
# graph.py:1486-1610 (resumido)
intake → jd_enrichment                                   [linear]
jd_enrichment ─route_after_jd→ {bigfive | intake | END}  [HITL #1]
bigfive ─route_after_bigfive→ {salary | competency}      [precompletion skip]
salary ─route_after_salary→ {competency | wsi_questions} [precompletion skip]
competency ─route_after_competency→ {wsi_questions | END}[needs screening_mode]
wsi_questions ─route_after_questions→ {eligibility | wsi_questions | END} [HITL #2]
eligibility → review                                     [linear]
review ─route_after_review→ {publish | END}              [readiness]
publish ─route_after_publish→ {calibration | END}        [optional]
calibration ─route_after_calibration→ {handoff | END}    [optional]
handoff → END                                            [linear]
```

### 3.4 HITL pattern (Onda 30 C.4 já documentado)

- **Não usa `interrupt_after`**. Usa conditional edge que retorna `"end"` quando `state["jd_approved"] is None` ou `state["questions_approved"] is None`.
- Vantagem: permite branches de **rejeição** (volta para `intake` no JD) e **fairness block** (termina cleanly).
- Resume é via `JobCreationGraph.resume(thread_id, prior_state, updates)` em `graph.py:1812-1854`, chamado por `_resume_wizard_canonical*` em `agent_chat_ws.py:378-507`.

### 3.5 Que features faltam estruturalmente

- **Não há node "description"** dedicado (entre `competency` e `wsi_questions`). Todo enriquecimento de JD acontece em `jd_enrichment_node`.
- **Não há node "basic_info"** dedicado (template suggestion). `intake_node` extrai title/seniority/department mas não sugere `template_type`.
- **`salary_node` é um stub passivo** (linhas 499–527, 28 linhas) — só copia `salary_benchmark` para o ws_payload. Sem cross com ats_history, sem fontes ranqueadas (history > market). A lógica F.3 da Onda 30 vive só em `stage_salary.py:217`.

---

## Seção 4 — Gap analysis

### 4.1 Feature 1 — `_suggest_template_type` (P0)

- **WizardStepService faz:** dado job_title + department, deterministicamente mapeia para um de 5 tipos (`technical`, `executive`, `operational`, `mass_hiring`, `intern`) e devolve em `suggestions_data.template_type`. Frontend usa para renderizar `WizardPipelineTemplateCard`.
- **Onde plugar no graph:** novo node `basic_info_node` entre `intake` e `jd_enrichment` OU enriquecer `intake_node` com `template_type` no `ws_stage_payload`.
- **Custo:** ~30 linhas (função pura existente em `stage_basic_info.py:70-93` é reutilizável; só precisa ser movida para um service compartilhado).
- **Dependências:** depende apenas de `parsed_title` + `parsed_department` (já em `state`).
- **Harness classification:** **computacional / sensor estrutural** — função determinística. Idealmente vira `app/domains/job_creation/services/template_type_resolver.py` reutilizável.

### 4.2 Feature 4 — `ats_job_history` em description (P1)

- **WizardStepService faz:** `stage_description.py:42` chama `ats_job_history_service.get_similar_jobs()` para sugerir descrição baseada em vagas similares já criadas.
- **Onde plugar no graph:** dentro de `jd_enrichment_node` antes de chamar `JdEnrichmentService.enrich`, OU em novo node `ats_context_node` antes do `jd_enrichment`.
- **Custo:** ~20 linhas de wiring (service singleton já existe).
- **Dependências:** `parsed_title`, `parsed_seniority`, `company_id`/`workspace_id`.
- **Harness classification:** **computacional / guide** — recupera contexto histórico antes do LLM. Reduz P(jd ruim) por feedforward.

### 4.3 Feature 6 — salary cross com ats_history (P0)

- **WizardStepService faz:** `stage_salary.py:217-260` faz 3 fontes ranqueadas (recruiter input > market benchmark > ats_history mediana com cutoff LGPD 365 dias, fail-open).
- **Onde plugar no graph:** dentro de `salary_node` (linhas 499-527, atualmente um stub). Fica `salary_node = enrich_with_3_sources + emit ws_payload`.
- **Custo:** **~150 linhas** (função atual em stage_salary.py é pesada — cutoff LGPD, statistics.median, fail-open multi-fonte). Refatorar para `app/domains/job_creation/services/salary_resolver.py` é o caminho certo.
- **Dependências:** `parsed_title`, `seniority_resolved`, `db: AsyncSession`, `company_id`. **Atenção:** `salary_node` hoje é síncrono — precisa virar async (LangGraph suporta).
- **Harness classification:** **computacional / sensor estrutural** — fontes deterministicas com fail-open.

### 4.4 Feature 7 — screening_mode parsing keywords (P1)

- **WizardStepService faz:** `service.py:587-597` parseia "compacta"/"completa" do texto livre do recruiter e seta `job_draft["screening_mode"]`.
- **Onde plugar no graph:** dentro do `intake_node` ou no `competency_node` (que já lê `screening_mode`). Ideal: `intake_extractor.extract` retorna `screening_mode` quando detecta keyword.
- **Custo:** ~10 linhas (função simples). Já existe `IntakeExtractor` para estender.
- **Dependências:** apenas `raw_input`.
- **Harness classification:** **computacional / guide** — keyword match determinístico no extractor canônico.

### 4.5 Feature 8 — seniority_confirmation < 0.7 (P1)

- **WizardStepService faz:** `stage_description.py:422` lê confidence do seniority detection; se < 0.7 seta `requires_seniority_confirmation` flag para o frontend pedir confirmação humana.
- **Onde plugar no graph:** `competency_node` já chama `resolve_seniority_full` (que retorna `confidence`). Adicionar emit de flag em `ws_stage_payload.data` quando `seniority_resolution.confidence < 0.7`. **NÃO precisa novo node** — só extensão de payload.
- **Custo:** ~5 linhas.
- **Dependências:** `seniority_resolution.confidence` já calculado em `graph.py:545`.
- **Harness classification:** **computacional / sensor** — confidence threshold é decisão computacional.

### 4.6 Feature 11 — apply_learning hooks (P2)

- **WizardStepService faz:** chama `_shared.apply_learning` em 3 stages para personalizar sugestões com base em decisões anteriores do recrutador.
- **Onde plugar no graph:** chamadas `apply_learning` em `intake_node`, `jd_enrichment_node` e `wsi_questions_node` (após resultado, antes de emit).
- **Custo:** ~9 linhas (3 chamadas idênticas).
- **Dependências:** `learning_hub_service` já existe.
- **Harness classification:** **inferencial / guide** — learning é heurístico. Manter idempotência.

### 4.7 Feature 12 — `template_type` em state (P0, ligado a #1)

- **Adicionar:** linha em `state.py` (TypedDict): `template_type: Optional[Literal["technical","executive","operational","mass_hiring","intern"]]`.
- **Custo:** 1 linha.
- **Dependências:** Feature #1.

### 4.8 Sumário de custo

| Feature | LOC ~ | Risco | Prioridade |
|---------|-------|-------|------------|
| 1 — template suggestion | 30 | baixo (função pura) | P0 |
| 4 — ats_history em description | 20 | médio (async, db session) | P1 |
| 6 — salary cross ats_history | 150 | alto (refator salary_node + async) | P0 |
| 7 — screening_mode parsing | 10 | baixo (estender extractor) | P1 |
| 8 — seniority_confirmation flag | 5 | baixo (extensão payload) | P1 |
| 11 — apply_learning hooks | 9 | baixo (idempotente) | P2 |
| 12 — `template_type` em state | 1 | trivial | P0 (depende de #1) |
| **Total** | **~225 LOC** | | |

Tempo estimado realista: **8–12h dev sênior** (incluindo tests).

---

## Seção 5 — Recomendação canônica

### 5.1 Decisão arquitetural

**`JobCreationGraph` confirmado como canônico.** Já é assim por Task #850 (`graph_runner.py:223-228`), por todas as 5 rotas legadas retornarem 410 (`lia_assistant/wizard.py`), por `wizard_orchestrator_service.get_wizard_step:355-372` e por `agent_chat_ws.py:382-507` (resume canonical).

**`WizardStepService` é DEAD CODE em produção.** Recomendação: **deprecar + deletar até Onda 38**. Antes do delete:
1. Verificar uma última vez via `git grep` em frontend (`plataforma-lia/`) por chamadas a `/api/v1/lia/job-wizard/step` (esperado: 0).
2. Mover a função pura `_suggest_template_type` (e seu dict `_TEMPLATE_TYPE_KEYWORDS`) para `app/domains/job_creation/services/template_type_resolver.py`.
3. Mover a lógica de 3 fontes do `stage_salary.py:200-260` para `app/domains/job_creation/services/salary_resolver.py`.
4. Mover `apply_learning` wiring (já é genérico — usa `learning_hub_service`).

### 5.2 Plano de migração (Onda 37.3 — sugerido)

Ordem de prioridade (dependências top-down):

| Sprint | Feature | Block? | Justificativa |
|--------|---------|--------|---------------|
| 37.3.1 | Mover `_suggest_template_type` → `template_type_resolver.py` | NO | Função pura, sem deps externas |
| 37.3.2 | Adicionar `template_type` ao `JobCreationState` | NO | 1 linha schema |
| 37.3.3 | Plugar resolver em `intake_node` (linha ~155) | NO | Emit em `ws_stage_payload.data` |
| 37.3.4 | Estender `IntakeExtractor` para parsear `screening_mode` keyword | NO | Trivial, ~10 LOC |
| 37.3.5 | Adicionar `requires_seniority_confirmation` em `competency_node` | NO | Branch já tem `confidence` |
| 37.3.6 | Refatorar `salary_node` async + 3 fontes (mover para `salary_resolver.py`) | YES (db async) | Maior risco; precisa tests |
| 37.3.7 | Adicionar `ats_history` em `jd_enrichment_node` | NO | Optional context |
| 37.3.8 | Adicionar `apply_learning` em 3 nodes (intake, jd_enrichment, wsi_questions) | NO | Boy-scout |
| 37.3.9 | Deprecar `WizardStepService` (soft) — adicionar warning log | NO | Mark dead |
| 37.4 | Deletar `WizardStepService` + tests | NO | Após verificar zero callers |

### 5.3 Sensores que teriam pego o gap (harness engineering)

**Princípio:** cada gap é ausência de sensor estrutural. O wizard duplo viveu meses porque não havia sensor canônico que detectasse "feature plugada em só 1 wizard". Adicionar:

#### Sensor S1 — Cross-wizard linter (computacional, guide)

```bash
# tests/lint/no_orphan_wizard_features.sh
# Toda função em job_management/services/wizard_step_service/stage_*.py
# DEVE ter equivalente referenciado em job_creation/graph.py OU
# em job_creation/services/*.py.

orphans=$(comm -23 \
  <(grep -hE 'def [a-z_]+' app/domains/job_management/services/wizard_step_service/stage_*.py | grep -oE '[a-z_]+' | sort -u) \
  <(grep -rhoE '[a-z_]+' app/domains/job_creation/ --include="*.py" | sort -u))
if [ -n "$orphans" ]; then
  echo "ERROR: WizardStepService has functions not mirrored in JobCreationGraph:"
  echo "$orphans"
  echo ""
  echo "Fix: either move the feature to app/domains/job_creation/services/<name>.py"
  echo "and wire it into a graph node, OR delete from WizardStepService (DEAD CODE)."
  exit 1
fi
```

Mensagem otimizada para LLM: explica o que fazer (move OR delete), não só o que está errado.

#### Sensor S2 — Caller verification (computacional, sensor)

```python
# tests/lint/test_wizard_step_service_dead.py
# Garante que WizardStepService NÃO tem caller de produção.
# Falha se algum dia alguém ressuscitar.

import ast, pathlib

def test_wizard_step_service_has_no_callers():
    """If WizardStepService gains a caller, this test fails — forcing
    explicit decision: did we un-deprecate, or is this a regression?"""
    callers = []
    for py in pathlib.Path("app").rglob("*.py"):
        if "wizard_step_service" in str(py):
            continue  # skip the service itself
        text = py.read_text()
        if "WizardStepService" in text or "wizard_step_service" in text:
            callers.append(str(py))
    assert callers == [], (
        f"WizardStepService is DEAD CODE per Task #850 — found callers: {callers}. "
        f"If you need this functionality, plug it into JobCreationGraph instead."
    )
```

#### Sensor S3 — CLAUDE.md guide (inferencial, guide)

Adicionar ao `lia-agent-system/CLAUDE.md`:

```markdown
## Wizard de criação de vaga — REGRA CANÔNICA

A LIA tem **um único wizard canônico**: `JobCreationGraph` (LangGraph) em
`app/domains/job_creation/graph.py`.

NÃO plugue features em `app/domains/job_management/services/wizard_step_service/`
— esse módulo é DEAD CODE (Task #850, todas as rotas retornam 410).

**Antes de adicionar feature ao wizard:**
1. Identifique o stage canônico (intake / jd_enrichment / bigfive / salary /
   competency / wsi_questions / eligibility / review / publish / calibration / handoff).
2. Se a feature precisa de service compartilhado, crie em
   `app/domains/job_creation/services/<name>.py`.
3. Plugue no node correspondente em `graph.py`.
4. Adicione field ao `JobCreationState` em `state.py` se precisa persistir.
5. Atualize `intake_extractor.py` se a feature consome free-text input.

**Se você está editando `wizard_step_service/stage_*.py`, PARE.** Pergunte:
"é uma feature nova ou um fix em código morto?" Se feature nova, mude para o graph.
```

#### Sensor S4 — Onboarding test (sensor + telemetria)

Adicionar a `tests/integration/test_wizard_canonical_path.py`:

```python
@pytest.mark.integration
async def test_quero_criar_vaga_routes_to_jobcreation_graph(client):
    """E2E: 'Quero criar uma vaga' must reach JobCreationGraph,
    NEVER fallback talent agent."""
    # Captura o span 'wizard.agent_chat.get_agent' e verifica
    # que agent.resolved_id == "JobCreationGraph" (não "TalentReActAgent").
    ...
```

Esse teste é o que **teria pego o gap do Cenário A E2E** — diferente de testar Cenário A ponta-a-ponta, testa-se a invariante estrutural.

### 5.4 Rollback do WizardStepService — decisão

| Opção | Pros | Cons | Recomendação |
|-------|------|------|--------------|
| Manter como fallback REST | "Se o graph falhar, REST salva" | Reintroduz wizard duplo, contradiz Task #850 | **NÃO** |
| Deprecar (warning log) + deletar em 30 dias | Zero callers já, baixíssimo risco | Trabalho manual de mover funções puras | **SIM** — caminho recomendado |
| Deletar agora | Mais limpo | Pode ter esquecido alguma chamada | NÃO antes do S2 sensor |

**Plano:**
- Onda 37.3 → mover funções puras + adicionar S1, S2, S4 sensors + adicionar S3 guide.
- Onda 37.4 → soft deprecation (log warning ao importar).
- Onda 38 → delete.

### 5.5 Classificação harness final

| Item | Computacional × Inferencial | Guide × Sensor |
|------|-----------------------------|----------------|
| 7 features migradas como nodes/services | computacional (todas) | mistura: 4 sensor + 3 guide |
| S1 (cross-wizard linter) | computacional | guide (impede merge) |
| S2 (caller verification) | computacional | sensor (detecta regressão) |
| S3 (CLAUDE.md regra) | inferencial | guide (reduz P(erro)) |
| S4 (integration test routing) | computacional | sensor (canary CI) |

**Erro do Cenário A foi defeito de harness, não de prompt:** faltou sensor S2 + S4 que teria detectado "feature plugada só no REST" + "fallback talent absorvendo wizard inicial". Adicionando esses 4 sensores, próximas Ondas não conseguem reproduzir o gap.

---

## Apêndice — Caminhos de evidência

| Evidência | Path:linha |
|-----------|------------|
| Task #850 declara JobCreationGraph canonical | `app/domains/ai/services/graph_runner.py:223-228` |
| 5 rotas legacy retornam 410 | `app/api/v1/lia_assistant/wizard.py:81-108` |
| WizardOrchestratorService.get_wizard_step retorna 410 | `app/domains/job_management/services/wizard_orchestrator_service.py:355-372` |
| WizardReActAgent removido | `app/api/v1/agent_chat_ws.py:515` (comentário) |
| @register_agent("wizard") **não existe** em produção | `app/shared/agents/agent_registry.py:14` (apenas docstring) |
| JobCreationGraph singleton | `app/domains/job_creation/graph.py:1614-1854` |
| 11 nodes do graph | `app/domains/job_creation/graph.py:1486-1610` |
| `_suggest_template_type` (gap #1) | `app/domains/job_management/services/wizard_step_service/stage_basic_info.py:70,178` |
| Salary 3 fontes ats_history (gap #6) | `app/domains/job_management/services/wizard_step_service/stage_salary.py:21,217` |
| screening_mode keyword parsing (gap #7) | `app/domains/job_management/services/wizard_step_service/service.py:587-597` |
| ats_job_history em description (gap #4) | `app/domains/job_management/services/wizard_step_service/stage_description.py:33,42` |
| seniority_confirmation flag (gap #8) | `app/domains/job_management/services/wizard_step_service/stage_description.py:422` |
| BRANCH_MAP — Ondas 23–25 | `docs/BRANCH_MAP.md:707-732` |
| BRANCH_MAP — Onda 30 (HITL guide-first confirmado) | `docs/BRANCH_MAP.md:898-968` |
