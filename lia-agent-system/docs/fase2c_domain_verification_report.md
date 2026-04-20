# Fase 2C — Relatório Estratégico de Capabilities (Auditoria 20/abr/2026)

**Data:** 20 de abril de 2026  
**Auditor:** `scripts/audit_chat_capabilities.py` (introspecção ao vivo do registry)  
**Status:** ✅ Fonte única da verdade — substitui versões de Fev/2026 e 19/abr/2026  
**Fonte programática:** [`chat_capabilities_audit.json`](./chat_capabilities_audit.json)  
**Referência complementar:** [`chat_capabilities_audit.md`](./chat_capabilities_audit.md) (análise de padrões de bug)

> **Nota de supersedência:** o conteúdo original deste arquivo (Fev/2026) afirmava "all domains properly implement execute_action()". A auditoria de 19/abr revelou 13/17 domínios com gaps críticos. Este documento, gerado em 20/abr/2026, mostra o estado **real e atual** após os saneamentos das semanas seguintes.

---

## TL;DR Executivo

| Métrica | Fev/2026 | 19/abr/2026 | **20/abr/2026 (hoje)** |
|---|---|---|---|
| Domínios registrados | 6 auditados | 17 | **18** |
| Domínios com gaps críticos | 1 (sourcing) | 13/17 | **0/18** |
| Mapeamentos `_ACTION_TOOL_MAP` quebrados | — | 6 | **0** |
| Handlers com import quebrado | — | 81 | **0** |
| Actions não-executáveis | — | 146 | **0** |
| Tools órfãs (sem action mapeada) | — | 93 | **0** |
| Agent-types órfãos no roteador | — | 10 | **0** |
| Total de actions declaradas | ~145 | 263 | **281** |
| Total de tools registradas | ~73 | 93 | **94** |

**Veredito atual (análise estática):** a camada de execução de capabilities está **estruturalmente íntegra**. Todos os 18 domínios registrados passam na auditoria programática com zero gaps detectados. Esta auditoria é estática (introspecção do registry, resolução de handlers) — não valida latência, disponibilidade de serviços externos ou confiabilidade de runtime em produção. O risco principal mudou de "cadeia quebrada" para "cobertura de testes insuficiente" e "dirs não-registrados que podem conter lógica viva".

---

## 1. Fluxo do Chat Unificado (ground truth — 20/abr)

```
Recrutador digita no chat
        ↓
POST /api/v1/chat/message  (app/api/v1/chat.py → ChatAdapter)
        ↓
MainOrchestrator (app/orchestrator/main_orchestrator.py)
        ↓
CascadedRouter — 7 tiers (custo crescente):
  Tier 0: MemoryResolver       — pronomes/referências de contexto
  Tier 1: LRU in-process       — hash MD5 em memória (O(1))
  Tier 2: Redis hash cache      — distribuído, exato
  Tier 3: VectorSemanticCache   — pgvector, cosine >= 0.85
  Tier 4: FastRouter            — regex/keyword
  Tier 5: LLM Cascade           — Haiku→Sonnet→Opus
  Tier 6: AutonomousReActAgent  — agente cross-domain (fallback final)
  Fallback: clarification_needed — pergunta ao usuário
        ↓
RouteResult{ domain_id } → resolve_domain(domain_id) via AGENT_TYPE_TO_DOMAIN
        ↓
DomainRegistry().get_instance(domain_id).execute_action(action_id, params, context)
        ↓
  1. _ACTION_TOOL_MAP[action_id] → tool_id
  2. execute_<domain>_tool(tool_id, params, tenant_id, user_id)
  3. app.shared.tool_handler.resolve_handler_path(handler) → callable
  4. handler(**params) → resultado
        ↓
DomainResponse → ChatAdapter → SSE/WebSocket → UI
```

**Estado dos tiers (20/abr/2026):**

| Tier | Componente | Estado |
|---|---|---|
| 0 | MemoryResolver | ✅ Operacional |
| 1 | LRU in-process | ✅ Operacional |
| 2 | Redis hash cache | ✅ Operacional (depende de Redis em produção) |
| 3 | VectorSemanticCache | ✅ Operacional (depende de PGVector em produção) |
| 4 | FastRouter | ✅ Operacional |
| 5 | LLM Cascade | ✅ Operacional (Haiku→Sonnet→Opus) |
| 6 | AutonomousReActAgent | ✅ Operacional |
| — | Clarification fallback | ✅ Operacional |

---

## 2. Inventário dos 18 Domínios Registrados

### Legenda: ✅ íntegro / ⚠️ parcial / 🔴 quebrado

| # | Domain ID | Classe | Actions | Tools | Mapeamentos | Handlers OK | Testes | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `agent_studio` | AgentStudioDomain | 20 | 0 | 0 | — | ❌ | ✅ |
| 2 | `analytics` | AnalyticsDomain | 18 | 10 | 18 | 10/10 | ❌ | ✅ |
| 3 | `ats_integration` | ATSIntegrationDomain | 18 | 10 | 18 | 10/10 | ❌ | ✅ |
| 4 | `automation` | AutomationDomain | 20 | 10 | 20 | 10/10 | ❌ | ✅ |
| 5 | `candidate_self_service` | CandidateSelfServiceDomain | 4 | 0 | 0 | — | ❌ | ✅ |
| 6 | `communication` | CommunicationDomain | 20 | 10 | 10 | 10/10 | ❌ | ✅ |
| 7 | `company_settings` | CompanySettingsDomain | 7 | 0 | 0 | — | ❌ | ✅ |
| 8 | `cv_screening` | CVScreeningDomain | 24 | 10 | 10 | 10/10 | ✅ | ✅ |
| 9 | `digital_twin` | DigitalTwinDomain | 5 | 0 | 0 | — | ❌ | ✅ |
| 10 | `hiring_policy` | HiringPolicyDomain | 9 | 0 | 0 | — | ✅ | ✅ |
| 11 | `interview_scheduling` | InterviewSchedulingDomain | 20 | 10 | 10 | 10/10 | ✅ | ✅ |
| 12 | `job_creation` | JobCreationDomain | 11 | 0 | 0 (intent-routed) | — | ❌ | ✅ |
| 13 | `job_management` | JobManagementDomain | 30 | 14 | 30 | 14/14 | ✅ | ✅ |
| 14 | `pipeline_transition` | PipelineTransitionDomain | 5 | 0 | 0 | — | ✅ | ✅ |
| 15 | `recruiter_assistant` | RecruiterAssistantDomain | 24 | 10 | 10 | 10/10 | ❌ | ✅ |
| 16 | `recruitment_campaign` | RecruitmentCampaignDomain | 4 | 0 | 0 | — | ❌ | ✅ |
| 17 | `sourcing` | SourcingDomain | 36 | 10 | 12 | 10/10 | ✅ | ✅ |
| 18 | `talent_pool` | TalentPoolDomain | 6 | 0 | 0 | — | ✅ | ✅ |
| **Σ** | | | **281** | **94** | **148** | **94/94** | | **18/18 ✅** |

> **Nota `job_creation`:** usa `process_intent + _route_by_stage` em vez de `_ACTION_TOOL_MAP`. É intent-routed por design — não é um gap.

### Detalhe por domínio

#### `agent_studio` — AgentStudioDomain
- **20 actions**, 0 tools — execução 100% via agent delegation.
- Actions funcionais: `create_sourcing_agent`, `calibrate_agent`, `get_agent_status`, `list_agents`, `run_multi_strategy`, `create_custom_agent`, `list_custom_agents`, `test_custom_agent`, `execute_custom_agent`, `publish_to_marketplace`, `browse_marketplace`, `install_from_marketplace`, `assign_to_crew`, `get_studio_consumption`, `deactivate_agent`, `uninstall_agent`, `explain_agent_studio` + 3 delegadas.
- ⚠️ Sem testes de domínio dedicados.

#### `analytics` — AnalyticsDomain
- **18 actions**, 10 tools, 18 mapeamentos, 0 handlers quebrados.
- Todos os handlers resolvem via `resolve_handler_path` (corrigido após 19/abr).
- ⚠️ Sem testes de domínio dedicados.

#### `ats_integration` — ATSIntegrationDomain
- **18 actions**, 10 tools, 18 mapeamentos, 0 handlers quebrados.
- ⚠️ Sem testes de domínio dedicados.

#### `automation` — AutomationDomain
- **20 actions**, 10 tools, 20 mapeamentos, 0 handlers quebrados.
- ⚠️ Sem testes de domínio dedicados.

#### `candidate_self_service` — CandidateSelfServiceDomain
- **4 actions**, 0 tools — execução via agent. Domínio de baixa complexidade.
- ⚠️ Sem testes de domínio dedicados.

#### `communication` — CommunicationDomain
- **20 actions**, 10 tools, 10 mapeamentos, 0 handlers quebrados.
- ⚠️ Sem testes de domínio dedicados.

#### `company_settings` — CompanySettingsDomain
- **7 actions**, 0 tools — execução via agent.
- ⚠️ Sem testes de domínio dedicados.

#### `cv_screening` — CVScreeningDomain
- **24 actions**, 10 tools, 10 mapeamentos, 0 handlers quebrados.
- ✅ Tem `test_cv_screening_agents.py`.

#### `digital_twin` — DigitalTwinDomain
- **5 actions**, 0 tools — domínio em desenvolvimento, execução via agent.
- ⚠️ Sem testes de domínio dedicados.

#### `hiring_policy` — HiringPolicyDomain
- **9 actions**, 0 tools — configura políticas via agent.
- ✅ Tem `test_policy_react_agent.py` e `test_policy_setup_agent_compliance.py`.

#### `interview_scheduling` — InterviewSchedulingDomain
- **20 actions**, 10 tools, 10 mapeamentos, 0 handlers quebrados.
- ✅ Tem `test_interview_scheduling.py`.

#### `job_creation` — JobCreationDomain (**NOVO desde 19/abr**)
- **11 actions**, 0 tools — roteamento via intent-state-machine (`process_intent + _route_by_stage`). Exclúído da verificação de `_ACTION_TOOL_MAP` por design.
- Actions: `start_wizard`, `approve_jd`, `set_salary`, `set_screening_mode`, `approve_questions`, `set_eligibility`, `configure_publish`, `publish_job`, `calibrate`, `wizard_status`, `help`.
- ⚠️ Sem testes de domínio dedicados.

#### `job_management` — JobManagementDomain
- **30 actions**, 14 tools, 30 mapeamentos, 0 handlers quebrados.
- Todos 14 handlers resolvem (corrigido após 19/abr — `app/tools/job_tools.py` criado ou handlers redirecionados).
- ✅ Tem `test_jobs_mgmt_react_agent.py`.

#### `pipeline_transition` — PipelineTransitionDomain
- **5 actions**, 0 tools — execução via agent.
- ✅ Tem `test_pipeline_transition_agent.py`.

#### `recruiter_assistant` — RecruiterAssistantDomain
- **24 actions**, 10 tools, 10 mapeamentos, 0 handlers quebrados.
- Funciona como DEFAULT_DOMAIN (fallback quando nenhum outro domínio corresponde).
- ⚠️ Sem testes dedicados de execute_action (apenas testes de agent: `test_kanban_react_agent.py`, `test_talent_react_agent.py`).

#### `recruitment_campaign` — RecruitmentCampaignDomain
- **4 actions**, 0 tools — execução via agent.
- ⚠️ Sem testes de domínio dedicados.

#### `sourcing` — SourcingDomain
- **36 actions**, 10 tools, 12 mapeamentos, 0 handlers quebrados.
- ✅ Task #579 fechou os 3 gaps: mapa corrigido, 4 pipeline tools adicionadas, assinatura do executor normalizada.
- ✅ Tem `test_sourcing_domain.py` (19 casos), `test_sourcing/`, `test_sourcing_react_agent.py`.

#### `talent_pool` — TalentPoolDomain
- **6 actions**, 0 tools — execução via agent.
- ✅ Tem `test_talent_react_agent.py`.

---

## 3. Mapeamento de Agent-Types (AGENT_TYPE_TO_DOMAIN)

**Total de agent-types mapeados:** 44  
**Apontando para domínio não-registrado:** **0** (resolvido — era 10 em 19/abr)  
**DEFAULT_DOMAIN:** `recruiter_assistant`

### Mapeamento completo (44 entradas)

| Agent-type LLM | Domínio alvo | Estado |
|---|---|---|
| `analytics`, `analyst_feedback` | `analytics` | ✅ |
| `ats_integration`, `ats_integrator` | `ats_integration` | ✅ |
| `automation`, `task_planner` | `automation` | ✅ |
| `communication` | `communication` | ✅ |
| `cv_screening`, `screening`, `wsi_evaluator` | `cv_screening` | ✅ |
| `company_settings`, `settings_config`, `company_profile`, `company_config` | `company_settings` | ✅ |
| `hiring_policy` | `hiring_policy` | ✅ |
| `interview_scheduling`, `interviewer`, `scheduling` | `interview_scheduling` | ✅ |
| `job_management`, `job_planner`, `job_intake` | `job_management` | ✅ |
| `recruiter_assistant` | `recruiter_assistant` | ✅ |
| `pipeline_transition`, `kanban_search`, `kanban_insight`, `kanban_action`, `pipeline_context`, `pipeline_decision`, `pipeline_action` | `pipeline_transition` | ✅ (resolvido — era órfão em 19/abr) |
| `sourcing`, `sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement` | `sourcing` | ✅ (resolvido — era órfão em 19/abr) |
| `talent_pool`, `voice_screening` | `talent_pool` | ✅ |
| `agent_studio`, `multi_strategy` | `agent_studio` | ✅ |
| `digital_twin` | `digital_twin` | ✅ |
| `recruitment_campaign` | `recruitment_campaign` | ✅ |
| `candidate_self_service`, `candidate_status`, `candidate_portal` | `candidate_self_service` | ✅ |
| `job_creation` | `job_creation` | ✅ |

---

## 4. Filesystem: 61 Dirs × 18 Registrados × 43 Não-Registrados

**Total de dirs em `app/domains/`:** 61  
**Registrados via `@register_domain`:** 18  
**Não-registrados:** 43

### Classificação dos 43 dirs não-registrados

| Categoria | Dirs |
|---|---|
| **Infraestrutura / API** (sem chat domain — correto) | `admin`, `admin_settings`, `auth`, `billing`, `candidates`, `chat`, `client_users`, `clients`, `company`, `credits`, `health_check`, `notifications`, `observability`, `saas_metrics`, `tasks` |
| **Compliance / LGPD** (lógica específica, sem chat domain — correto) | `compliance`, `consent`, `data_subject`, `lgpd`, `trust_center` |
| **Features laterais** (funcionalidades auxiliares, sem chat domain) | `agent_memory`, `approvals`, `bulk_actions`, `candidate_lists`, `company_culture`, `email_templates`, `goals`, `integrations_hub`, `opinions`, `shared_searches`, `triagem`, `voice` |
| **Analytics / BI** (dados, sem chat domain por agora) | `job_vacancies_analytics`, `recruitment`, `recruitment_journey`, `talent_intelligence` |
| **Domínios parcialmente desenvolvidos** (podem precisar de registro futuramente) | `ai`, `autonomous`, `interview_intelligence`, `journey_mapping`, `pipeline`, `policy`, `workforce`, `technical_tests` |

> **Conclusão:** nenhum dos 43 dirs não-registrados aparenta ser código morto crítico que bloqueia o chat. Os dirs da categoria "Domínios parcialmente desenvolvidos" merecem revisão para decidir se serão registrados ou consolidados em domínios existentes.

---

## 5. Comparativo Antes → Agora

### Fev/2026 → 19/abr/2026 (gaps abertos)

| Afirmação do doc original (Fev/2026) | Status real em 19/abr |
|---|---|
| "All domains properly implement execute_action()" | ❌ FALSO — 13/17 com handlers quebrados |
| "sourcing domain is INCOMPLETE — CRITICAL ISSUE" | ✅ AINDA VERDADEIRO (task #579 ainda não executada) |
| "automation is fully implemented" | ❌ FALSO — 10 handlers quebravam em ModuleNotFoundError |
| "communication is COMPLETE" | ❌ FALSO — 10 handlers quebravam (singleton navigation) |
| "analytics is COMPLETE" | ❌ FALSO — 10 funções não existiam em report_service |
| "interview_scheduling is COMPLETE" | ❌ FALSO — 10 handlers quebrados (padrão B) |

### 19/abr/2026 → 20/abr/2026 (gaps fechados)

| Gap de 19/abr | Resolvido como | Evidência |
|---|---|---|
| **Sourcing — 3 gaps (A/B/C)** (task #579) | Gap A: mapa corrigido (6→0 quebrados); Gap B: 4 pipeline tools adicionadas; Gap C: assinatura executor normalizada | `sourcing`: 36 actions, 12 mapeamentos, 0 gaps |
| **10 agent-types órfãos** (`kanban_*`, `pipeline_*`, `sourcing_*`) | Remapeados para domínios existentes: `pipeline_transition` e `sourcing` | `agent_types_pointing_to_unknown_domain: []` |
| **81 handlers com import quebrado** | `resolve_handler_path()` em `app/shared/tool_handler.py` substituiu o `importlib` direto + handlers corrigidos | `handlers_failing_import: 0` em todos os 18 domínios |
| **146 actions não-executáveis** | `_ACTION_TOOL_MAP` populado nos domínios afetados (analytics, communication, etc.) | `actions_no_handler: 0` |
| **93 tools órfãs** | Mapeadas para actions correspondentes | `orphan_tools: 0` |
| **Domínio `job_creation` não registrado** | Novo domínio registrado com 11 actions (intent-routed) | `job_creation` na lista dos 18 |

---

## 6. Problemas Correlatos Não Mapeados no Documento Original

### 6.1 `resolve_handler_path` — resolver canônico de handlers

O antigo código usava `importlib.import_module(path_sem_funcao)` para importar handlers, causando os 81 `ModuleNotFoundError`. O novo `app/shared/tool_handler.py` usa `resolve_handler_path()` que faz separação inteligente do último segmento do dotted path. Isto elimina o padrão B (singleton navigation) e padrão C (função não existe no módulo).

**Risco residual:** se um handler string aponta para uma função real mas com assinatura incompatível com o schema de params declarado, o erro só vai aparecer em runtime. Não há validação de schema em tempo de registro.

### 6.2 Tenant isolation — estado atual

O `tool_handler.py` implementa `require_company=True` por padrão:
1. Verifica `company_id` nos kwargs.
2. Fallback 1: `_context.company_id` (AgenticLoop/ToolExecutor).
3. Fallback 2: `get_current_llm_tenant()` (LangGraph contextvar).
4. Se nenhum resolve → retorna erro sem executar (fail-closed ✅).

**Status:** fail-closed implementado. Handlers que usam o decorator `@tool_handler` estão protegidos. Handlers que **não usam o decorator** ainda precisam de verificação manual.

### 6.3 CascadedRouter — tiers 0–6

O roteador tem 7 tiers efetivos (a doc antiga citava 8, contando o clarification como tier). Todos os tiers estão operacionais. O tier 6 (`AutonomousReActAgent`) funciona como fallback antes de pedir clarificação ao usuário.

**Risco residual:** se o LLM no Tier 5 retorna um agent-type não mapeado em `AGENT_TYPE_TO_DOMAIN`, o `resolve_domain()` retorna `DEFAULT_DOMAIN = recruiter_assistant` **silenciosamente** (sem log de warning). Isso não quebra o chat, mas pode gerar respostas fora de contexto.

### 6.4 `job_creation` domain — intent-routing vs tool-routing

Este domínio usa `process_intent + _route_by_stage` (state machine) em vez de `_ACTION_TOOL_MAP`. Está corretamente excluído da verificação de mapeamento pelo auditor. No entanto, não há testes que cubram o fluxo de criação de vaga via esse domínio especificamente.

### 6.5 Cobertura de testes por domínio

| Domínio | Teste existente | Tipo de teste |
|---|---|---|
| `cv_screening` | `test_cv_screening_agents.py` | Agent behavior |
| `hiring_policy` | `test_policy_react_agent.py`, `test_policy_setup_agent_compliance.py` | Agent + compliance |
| `interview_scheduling` | `test_interview_scheduling.py` | Domain/service |
| `job_management` | `test_jobs_mgmt_react_agent.py` | Agent behavior |
| `pipeline_transition` | `test_pipeline_transition_agent.py` | Agent behavior |
| `sourcing` | `test_sourcing_domain.py`, `test_sourcing/`, `test_sourcing_react_agent.py` | Domain + agent |
| `talent_pool` / `recruiter_assistant` | `test_talent_react_agent.py`, `test_kanban_react_agent.py` | Agent behavior |
| `agent_studio` | ❌ | — |
| `analytics` | ❌ | — |
| `ats_integration` | ❌ | — |
| `automation` | ❌ | — |
| `candidate_self_service` | ❌ | — |
| `communication` | ❌ | — |
| `company_settings` | ❌ | — |
| `digital_twin` | ❌ | — |
| `job_creation` | ❌ | — |
| `recruiter_assistant` (execute_action) | ❌ | — |
| `recruitment_campaign` | ❌ | — |

**11 dos 18 domínios não têm cobertura de execute_action.** Os testes existentes testam comportamento do agente, não o pipeline `execute_action → tool → handler`.

---

## 7. O Que Está Funcionando Hoje

> **⚠️ Importante:** as afirmações abaixo são baseadas em **análise estática** do registry (introspecção de código, resolução de handlers, integridade de mapeamentos). Elas confirmam que a cadeia estrutural `action → tool → handler` está íntegra. **Não** representam validação de runtime em produção (latência, disponibilidade de serviços externos, respostas corretas do LLM, autenticação real de tenant). Para evidência de runtime, consultar os runs de eval em `lia-agent-system/eval/`.

Fluxos end-to-end que chegam a execução de tool com sucesso (evidência: 0 gaps na auditoria estática + testes existentes):

| Fluxo | Domínio | Tool | Evidência |
|---|---|---|---|
| Criar vaga | `job_management` | `create_job_vacancy` | action_tool_map resolvido, handler ok |
| Atualizar vaga | `job_management` | `update_job_vacancy` | action_tool_map resolvido, handler ok |
| Fechar/pausar vaga | `job_management` | `close_job_vacancy`, `pause_job_vacancy` | action_tool_map resolvido |
| Wizard de criação | `job_creation` | intent-routed | domain registrado, intent-routing ativo |
| Mover candidato no pipeline (pós-#579) | `sourcing` | `sourcing_update_candidate_stage` | gap B fechado, handler ok |
| Rejeitar candidato (pós-#579) | `sourcing` | `sourcing_reject_candidate` | gap B fechado |
| Shortlist candidato (pós-#579) | `sourcing` | `sourcing_shortlist_candidate` | gap B fechado |
| Busca de candidatos | `sourcing` | `sourcing_search_candidates` | action_tool_map resolvido |
| Agendar entrevista | `interview_scheduling` | `scheduling_schedule_interview` | action_tool_map + handler ok |
| Cancelar/reagendar entrevista | `interview_scheduling` | `scheduling_cancel`, `scheduling_reschedule` | action_tool_map resolvido |
| Triagem de CV | `cv_screening` | `parse_cv`, `calculate_wsi`, `evaluate_rubric` | action_tool_map resolvido |
| Enviar email | `communication` | `communication_send_email` | handler resolvido |
| Relatório KPI | `analytics` | `analytics_generate_kpi` | handler resolvido |
| Pipeline health | `recruiter_assistant` | `assistant_pipeline_health` | action_tool_map + handler ok |
| Mover candidato (kanban) | `recruiter_assistant` | `assistant_move_candidate` | action_tool_map + handler ok |
| Sincronizar ATS | `ats_integration` | `ats_sync_candidate` | action_tool_map + handler ok |
| Criar task de automação | `automation` | `automation_create_task` | action_tool_map + handler ok |
| Configurar política | `hiring_policy` | via agent (sem tool) | domínio sem gaps |
| Transição de pipeline | `pipeline_transition` | via agent (sem tool) | domínio sem gaps |

---

## 8. Priorização Estratégica

### P0 — Bloqueia uso real ou oculta falhas silenciosas

| ID | Gap | Impacto | Esforço | Task existente |
|---|---|---|---|---|
| P0-1 | Handlers sem decorator `@tool_handler` não têm tenant isolation garantida | Cross-tenant data leak potencial | M | Verificar #329 — pode cobrir |
| P0-2 | Tier 5 LLM retorna agent-type desconhecido → fallback silencioso para `recruiter_assistant` sem log | Respostas fora de contexto sem rastreabilidade | S | ❌ sem task |

### P1 — Degrada experiência mas tem workaround

| ID | Gap | Impacto | Esforço | Task existente |
|---|---|---|---|---|
| P1-1 | 11 domínios sem teste de `execute_action` end-to-end | Regressões silenciosas em deploys | L | Parcialmente: #232, #361 |
| P1-2 | `job_creation` sem testes (domínio novo, intent-routed) | Wizard de criação pode regredir | M | ❌ sem task |
| P1-3 | 8 dirs "parcialmente desenvolvidos" não-registrados (ex.: `pipeline`, `policy`, `autonomous`, `interview_intelligence`) sem decisão explícita | Lógica viva pode estar inacessível via chat | M | ❌ sem task |
| P1-4 | `recruiter_assistant` é DEFAULT_DOMAIN — qualquer intent não-mapeado cai aqui | Dificulta debugging de roteamento | S | ❌ sem task |
| P1-5 | Schema de params dos handlers não é validado em tempo de registro | Erros aparecem só em runtime | M | ❌ sem task |

### P2 — Qualidade / dívida técnica

| ID | Gap | Impacto | Esforço | Task existente |
|---|---|---|---|---|
| P2-1 | `chat_capabilities_audit.md` data de 19/abr — precisa regenerar | Doc desatualizado | S | Coberto por esta task |
| P2-2 | Dirs não-registrados categoria "features laterais" sem inventário de responsabilidade | Confusão de ownership | S | ❌ sem task |
| P2-3 | `MAPA_CAMADA_INTELIGENCIA.md` referencia 10 domínios mas há 18 — desatualizado | Onboarding incorreto | M | ❌ sem task |
| P2-4 | Sem smoke test CI que rode `audit_chat_capabilities.py` e falhe se `gaps_total > 0` | Risco de regressão em gaps zero | S | ❌ sem task |

---

## 9. Cross-Reference com Tasks do Backlog

| Task | Título (resumido) | Gaps cobertos | Status em 20/abr |
|---|---|---|---|
| #232 | Audit all model shims for mapper conflicts | P1-1 (parcial — model layer) | ABERTO |
| #270 | Remove inline table-creation fallback | Infra/DB | ABERTO |
| #289 | Unify recent conversations saved (sidebar) | Chat UX | ABERTO |
| #329 | Tenant isolation guard | P0-1 (tenant isolation) | ABERTO |
| #335 | Retire legacy demo-tenant shim | Infra/Auth | ABERTO |
| #336 | Make demo-tenant column UUID | Infra/DB | ABERTO |
| #359 | Corrigir ID empresa demo no guarda de auth | Auth | ABERTO |
| #361 | Add automated check: new tools skip tenant isolation | P0-1, P2-4 | ABERTO |
| #579 | Sourcing domain — fechar gaps A/B/C | Gap sourcing | ✅ FECHADO |

**Gaps sem task existente:**
- P0-2: warning log quando LLM retorna agent-type desconhecido
- P1-2: testes para `job_creation` domain
- P1-3: auditoria dos 8 dirs parcialmente desenvolvidos
- P1-5: validação de schema de params em tempo de registro
- P2-3: atualizar `MAPA_CAMADA_INTELIGENCIA.md` para 18 domínios
- P2-4: CI gate que falha se `gaps_total > 0`

---

## 10. Tasks Recomendadas (não criar agora — decisão do usuário)

| Título sugerido | Descrição | Prioridade | Esforço |
|---|---|---|---|
| Adicionar warning log quando agent-type desconhecido cai no DEFAULT_DOMAIN | Em `resolve_domain()`, logar `WARNING` com o agent-type recebido quando não está em `AGENT_TYPE_TO_DOMAIN` | P0 | S |
| Audit e cobertura de tenant isolation em handlers sem `@tool_handler` | Listar todos os handlers que não usam o decorator e verificar se isolam `company_id` manualmente | P0 | M |
| Testes de execute_action para 11 domínios sem cobertura | Criar pytest parametrizado cobrindo `analytics`, `ats_integration`, `automation`, `communication`, `company_settings`, `digital_twin`, `agent_studio`, `candidate_self_service`, `recruitment_campaign`, `recruiter_assistant`, `job_creation` | P1 | L |
| Testes para `job_creation` intent-routed | Cobrir fluxo `process_intent + _route_by_stage` com casos de criação de vaga completos | P1 | M |
| Inventário e decisão sobre 8 dirs parcialmente desenvolvidos | Para cada um de `ai`, `autonomous`, `interview_intelligence`, `journey_mapping`, `pipeline`, `policy`, `workforce`, `technical_tests`: registrar como domínio, consolidar em existente, ou marcar como código morto | P1 | M |
| CI gate: `audit_chat_capabilities.py` com fail se gaps > 0 | Adicionar ao pipeline CI para prevenir regressão nos zeros conquistados | P2 | S |
| Atualizar `MAPA_CAMADA_INTELIGENCIA.md` para 18 domínios | Corrigir contagem de domínios, diagrama e organograma | P2 | S |
| Validar schema de params de handlers em tempo de registro | Na inicialização do domain, checar que cada handler aceita os campos declarados em `DomainAction.params_schema` | P2 | M |

---

## Apêndice — Como Reproduzir Esta Auditoria

```bash
cd lia-agent-system
python3 scripts/audit_chat_capabilities.py
# → docs/chat_capabilities_audit.json  (output bruto, atualizado)
# Resultado esperado: "domains_with_gaps": 0, "broken_handlers": 0
```

O auditor é determinístico (sem rede, sem DB). Ideal para CI.  
Requisito: `LIA_SKIP_DB=1`, `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` (já setados no script).

---

*Gerado em: 20/abr/2026 — auditor `scripts/audit_chat_capabilities.py` v20abr*
