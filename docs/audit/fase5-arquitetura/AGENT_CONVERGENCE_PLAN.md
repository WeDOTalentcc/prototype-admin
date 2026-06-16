# AGENT_CONVERGENCE_PLAN.md — Convergencia de Agentes
**Protocolo:** P23  
**Data:** 2026-04-14  
**Arquiteto:** Claude Opus 4.6  
**Baseado em:** P01 (PLATFORM_MAP), P13 (DUPLICATION_DIVERGENCE), P21 (TARGET_ARCHITECTURE)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. Integracao via RabbitMQ.

**Depende de:** P13, P21  
**Alimenta:** P27, P28, P33, P35

---

## ACHADO PRINCIPAL: CONVERGENCIA JA ALTA (85%)

Ao contrario do esperado para um codebase de "vibe coding", os agentes do lia-agent-system ja convergem significativamente. Isso e resultado de uma migracao sistematica anterior que unificou todos os agentes em LangGraph nativo.

---

## PASSO 1: INVENTARIO DE PADROES

### 1.1 Agentes ReAct (LangGraphReActBase + EnhancedAgentMixin)

**TODOS usam o mesmo stack.** 15 agentes primarios + 11 sub-agentes sourcing.

| Agente | Arquivo | Base | Mixin | Tools | Prompt | Domain |
|--------|---------|------|-------|-------|--------|--------|
| **SourcingReAct** | sourcing/agents/sourcing_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_sourcing_tools() | SOURCING_DOMAIN_SPECIFIC (inline) | SourcingDomain(Compliance) |
| **WizardReAct** | job_management/agents/wizard_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_wizard_tools() | WIZARD_DOMAIN_SPECIFIC (inline) | JobManagementDomain(Compliance) |
| **PipelineReAct** | cv_screening/agents/pipeline_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_pipeline_tools() | PIPELINE_DOMAIN_SPECIFIC (inline) | CVScreeningDomain(Compliance) |
| **CommunicationReAct** | communication/agents/communication_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_communication_tools() | COMMUNICATION_DOMAIN_SPECIFIC (inline) | CommunicationDomain(Compliance) |
| **AnalyticsReAct** | analytics/agents/analytics_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_analytics_tools() | ANALYTICS_DOMAIN_SPECIFIC (inline) | AnalyticsDomain(Compliance) |
| **AutomationReAct** | automation/agents/automation_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_automation_tools() | AUTOMATION_DOMAIN_SPECIFIC (inline) | AutomationDomain(Compliance) |
| **ATSIntegrationReAct** | ats_integration/agents/ats_integration_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_ats_integration_tools() | ATS_INTEGRATION_DOMAIN_SPECIFIC (inline) | ATSIntegrationDomain(Compliance) |
| **PolicyReAct** | hiring_policy/agents/policy_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_policy_tools() | POLICY_DOMAIN_SPECIFIC (inline) | HiringPolicyDomain(Compliance) |
| **CompanyReAct** | company_settings/agents/company_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_company_settings_tools() | COMPANY_DOMAIN_SPECIFIC (inline) | CompanySettingsDomain(Compliance) |
| **KanbanReAct** | recruiter_assistant/agents/kanban_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_kanban_tools() | KANBAN_DOMAIN_SPECIFIC (inline) | RecruiterAssistantDomain(Compliance) |
| **TalentReAct** | recruiter_assistant/agents/talent_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_talent_tools() | TALENT_DOMAIN_SPECIFIC (inline) | RecruiterAssistantDomain(Compliance) |
| **JobsMgmtReAct** | recruiter_assistant/agents/jobs_mgmt_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_jobs_mgmt_tools() | JOBS_MGMT_DOMAIN_SPECIFIC (inline) | RecruiterAssistantDomain(Compliance) |
| **AutonomousReAct** | autonomous/agents/autonomous_react_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_autonomous_tools() (40+) | DOMAIN_INSTRUCTIONS (inline) | Fallback (Tier 6) |
| **CustomAgentRuntime** | agent_studio/custom_agent_runtime.py | LangGraphReActBase | EnhancedAgentMixin | Filtered pool (allowed_tools) | Tenant-defined template | AgentStudioDomain(Compliance) |
| **PipelineTransition** | pipeline/agents/pipeline_transition_agent.py | LangGraphReActBase | EnhancedAgentMixin | get_pipeline_tools() | Inline | PipelineDomain(Compliance) |

**Sub-agentes sourcing** (herdam de SourcingReActAgent):
SourcingSearch, SourcingEnrich, SourcingPlanner, SourcingEngagement, DiversitySourcing, GithubSourcing, StackOverflowSourcing, PassivePipeline, NurtureSequence, Referral

### 1.2 Agentes StateGraph (Maquinas de Estado)

| Agente | Arquivo | Framework | Nodes | Checkpointer | Compliance |
|--------|---------|-----------|-------|-------------|------------|
| **InterviewGraph** | interview_scheduling/agents/interview_graph.py | LangGraph StateGraph | 6 (loader→collector→router→validator→executor→response) | PostgresSaver | ComplianceDomainPrompt (via domain) |
| **WSIInterviewGraph** | cv_screening/agents/wsi_interview_graph.py | LangGraph StateGraph | Pergunta→Avaliacao→Score→Resultado | PostgresSaver | ComplianceDomainPrompt (via domain) |
| **JobCreationGraph** | job_creation/graph.py | LangGraph StateGraph | HITL points (JD enrichment, WSI questions) | Sessao | ComplianceDomainPrompt (via domain) |
| **JobWizardGraph** | job_management/agents/job_wizard_graph.py | Custom StateGraph | Intent→Collect→Validate→Execute | Local state | ComplianceDomainPrompt (via domain) |

### 1.3 Servicos De-Agentificados

| Servico | Arquivo | Pattern | Motivo |
|---------|---------|---------|--------|
| **CVScreeningBatchService** | cv_screening/services/cv_screening_batch_service.py | Service (Celery task) | Migrado de agent para service (Sprint 5) — batch nao precisa ReAct |
| **TwinInferenceService** | services/twin_inference_service.py | Service (RAG + LLM) | Nao e agente — e servico de inferencia |

### 1.4 Agentes Especialistas (Pipeline sub-agents)

| Agente | Arquivo | Base | Herda de |
|--------|---------|------|----------|
| KanbanAction | recruiter_assistant/agents/kanban_action_agent.py | KanbanReActAgent | Subclasse |
| KanbanInsight | recruiter_assistant/agents/kanban_insight_agent.py | KanbanReActAgent | Subclasse |
| KanbanSearch | recruiter_assistant/agents/kanban_search_agent.py | KanbanReActAgent | Subclasse |
| PipelineAction | pipeline/agents/pipeline_action_agent.py | LangGraphReActBase | Direto |
| PipelineContext | pipeline/agents/pipeline_context_agent.py | LangGraphReActBase | Direto |
| PipelineDecision | pipeline/agents/pipeline_decision_agent.py | LangGraphReActBase | Direto |

---

## PASSO 2: ANALISE DE DIVERGENCIA

### A. FRAMEWORK DIVERGENCE

| Framework | Agentes | % |
|-----------|---------|---|
| LangGraph ReAct (create_react_agent) | 26 agentes (15 primarios + 11 sourcing) | **76%** |
| LangGraph StateGraph | 4 agentes (Interview, WSI, JobCreation, JobWizard) | **12%** |
| Subclasse de ReAct | 6 agentes (Kanban sub, Pipeline sub) | **9%** |
| Service (nao agente) | 2 (CVScreeningBatch, TwinInference) | **6%** |
| Custom/Legacy | 0 | **0%** |

**Veredicto: 1 framework (LangGraph) com 2 patterns validos (ReAct para raciocinio, StateGraph para fluxos deterministicos). ZERO frameworks divergentes. EXCELENTE.**

### B. STATE MANAGEMENT DIVERGENCE

| Pattern | Agentes | Tipado? |
|---------|---------|---------|
| MessagesState (LangGraph prebuilt) | 26 ReAct | SIM (via LangGraph) |
| TypedDict custom state | 4 StateGraph | SIM (dataclass/TypedDict) |
| PostgresSaver (checkpointer) | 30 (todos) | SIM |

**Veredicto: State management convergido. Todos usam LangGraph state + PostgresSaver.**

### C. TOOL INTEGRATION DIVERGENCE

| Pattern | Agentes | Consistente? |
|---------|---------|-------------|
| `get_{domain}_tools()` function → ToolDefinition list | TODOS | SIM |
| ToolRegistry central + YAML metadata | TODOS | SIM |
| Tool schemas (to_claude_schema/to_gemini_schema) | TODOS | SIM |

**51 tool registries no total** (1 central + ~50 per-domain/per-agent). Pattern consistente — cada dominio define seu subset.

**Veredicto: Tool integration convergida. 1 pattern com variacao por dominio (valido).**

### D. PROMPT MANAGEMENT DIVERGENCE

| Pattern | Agentes | Problema? |
|---------|---------|----------|
| `{DOMAIN}_DOMAIN_SPECIFIC` constant (inline .py) | 15 ReAct primarios | SIM — deveria ser YAML |
| `get_{domain}_system_prompt()` function | 8 agentes (wizard, pipeline, kanban, talent, jobs_mgmt, policy, company, sourcing) | MELHOR — usa builder |
| `{DOMAIN}_FEW_SHOT_EXAMPLES` constant | 5 agentes | SIM — deveria ser YAML |
| `{DOMAIN}_REASONING_PROMPT` constant | 5 agentes | SIM — deveria ser YAML |
| YAML files (`app/prompts/domains/*.yaml`) | 10 dominios | BOM — fonte correta |
| Tenant-defined template (Agent Studio) | 1 (CustomAgentRuntime) | OK — by design |

**Veredicto: 2 patterns coexistem — inline constants (maioria) e YAML (minoria). Convergir para YAML. Esforco: M.**

### E. CROSS-CUTTING CONSUMPTION (CRITICO)

| Agente | Fairness Pre | Fairness Post | LGPD/PII | Audit | Memory | CalibWeight | Error Pattern |
|--------|-------------|--------------|----------|-------|--------|-------------|---------------|
| **SourcingReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **WizardReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **PipelineReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **CommunicationReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **AnalyticsReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **AutomationReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **ATSIntegrationReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **PolicyReAct** | via Compliance + direto | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **CompanyReAct** | via Compliance + direto | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **KanbanReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **TalentReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **JobsMgmtReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **AutonomousReAct** | via Compliance | NAO | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | CircuitBreaker |
| **CustomAgentRuntime** | via Compliance | SIM (tool output) | via LIA-C04 | via AuditCallback | via EnhancedMixin | NAO | try/except |
| **InterviewGraph** | via Domain | NAO | PARCIAL | PARCIAL | PostgresSaver | NAO | try/except |
| **WSIInterviewGraph** | via Domain | NAO | PARCIAL | traceable | PARCIAL | NAO | try/except |
| **JobCreationGraph** | via Domain | NAO | PARCIAL | PARCIAL | Local state | NAO | try/except |
| **JobWizardGraph** | via Domain | NAO | PARCIAL | Execution log | Local state | NAO | try/except |

**Legenda:**
- `via Compliance` = Automatico por ComplianceDomainPrompt (pre-check)
- `via LIA-C04` = Automatico por LangGraphReActBase (PII strip antes do LLM)
- `via AuditCallback` = Automatico por _process_langgraph() (audit de tool calls)
- `via EnhancedMixin` = Automatico por EnhancedAgentMixin (memory + learning)
- `NAO` = Nao implementado

### Gaps universais identificados:

| Gap | Agentes afetados | Severidade |
|-----|-----------------|-----------|
| **Fairness POST-check ausente** | 29 de 30 (todos exceto CustomAgentRuntime) | ALTO |
| **CalibrationWeight nao consumido** | 30 de 30 | ALTO |
| **StateGraph sem PII strip completo** | 4 (Interview, WSI, JobCreation, JobWizard) | MEDIO |
| **StateGraph sem AuditCallback** | 4 (mesmos) | MEDIO |
| **StateGraph sem EnhancedMixin** | 4 (mesmos) | MEDIO |

---

## PASSO 3: PADRAO ALVO UNIFICADO

### 3.1 O padrao JA EXISTE — e LangGraphReActBase + EnhancedAgentMixin

O codebase ja convergiu para um padrao. Os gaps sao INCREMENTAIS, nao estruturais.

**Pattern ReAct (raciocinio autonomo):**
```python
class {Domain}ReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    # Herda automaticamente:
    # - PII strip (LIA-C04) via LangGraphReActBase
    # - AuditCallback via _process_langgraph()
    # - Memory (working + long-term) via EnhancedAgentMixin
    # - Learning extraction via EnhancedAgentMixin
    # - FairnessGuard pre-check via ComplianceDomainPrompt (domain layer)

    # ADICIONAR:
    # - FairnessGuard post-check (via ComplianceDomainPrompt.execute_action)
    # - CalibrationWeight loading (via before_process hook)
    # - CalibrationEvent recording (via after_process hook)
```

**Pattern StateGraph (fluxos deterministicos):**
```python
class {Domain}Graph:
    # JA TEM: StateGraph + PostgresSaver + conditional edges

    # ADICIONAR:
    # - PII strip em cada node que recebe texto do usuario
    # - AuditCallback em cada node
    # - FairnessGuard pre/post nos nodes de decisao
```

### 3.2 Estrutura de Diretorio (JA IMPLEMENTADA)

```
app/domains/{domain}/
  ├── __init__.py
  ├── domain.py              # @register_domain class (ComplianceDomainPrompt)
  ├── actions.py             # DomainAction definitions
  ├── agents/
  │   ├── {domain}_react_agent.py        # ReAct agent
  │   ├── {domain}_system_prompt.py      # DOMAIN_SPECIFIC constant ← MIGRAR PARA YAML
  │   └── {domain}_tool_registry.py      # get_{domain}_tools()
  ├── services/              # Business logic
  ├── repositories/          # DB queries
  └── config/
      └── capabilities.yaml  # Intent keywords (Fase 5)
```

**Padrao alvo adicional:**
```
  └── config/
      ├── capabilities.yaml
      └── prompts.yaml  ← NOVO: system prompt + few-shot + reasoning
```

### 3.3 Pipeline de Execucao (JA IMPLEMENTADO parcialmente)

```
Request → AuthEnforcementMiddleware → RateLimitMiddleware → RequestIdMiddleware
  → MainOrchestrator
    → FairnessGuard.pre_check ← JA IMPLEMENTADO
    → TenantContext enrichment ← JA IMPLEMENTADO
    → CalibrationWeight.load() ← NOVO (P21 before_process)
    → CascadedRouter → Domain → Agent
      → PII strip (LIA-C04) ← JA IMPLEMENTADO (ReAct)
      → LLM + Tool calls ← JA IMPLEMENTADO
      → AuditCallback ← JA IMPLEMENTADO (ReAct)
      → FairnessGuard.post_check ← NOVO
      → LearningExtractor ← JA IMPLEMENTADO
      → CalibrationEvent.record() ← NOVO
  → Response
```

---

## PASSO 4: PLANO DE CONVERGENCIA POR AGENTE

### 4.1 Grupo 1: ReAct Agents (26 agentes) — Gap MINIMO

| # | Agente | Gaps para padrao alvo | Esforco | Prioridade |
|---|--------|----------------------|---------|------------|
| 1 | Todos 15 primarios | Fairness post-check + CalibWeight + prompt para YAML | S por agente | P1 |
| 2 | 11 sub-agentes sourcing | Herdam do SourcingReAct — fix no pai propaga | S (1 fix) | P1 |

**Fix centralizado (1 vez, afeta todos):**
1. Adicionar `post_check` no `ComplianceDomainPrompt.execute_action()` → afeta TODOS os 26 automaticamente
2. Adicionar `CalibrationWeight.load()` no `EnhancedAgentMixin._get_memory_context()` → afeta TODOS
3. Migrar 15 `{DOMAIN}_DOMAIN_SPECIFIC` constants para `config/prompts.yaml` → 15 moves independentes

### 4.2 Grupo 2: StateGraph Agents (4 agentes) — Gap MEDIO

| # | Agente | Gaps | Esforco | Prioridade |
|---|--------|------|---------|------------|
| 1 | InterviewGraph | PII strip nos nodes + AuditCallback | M | P2 |
| 2 | WSIInterviewGraph | PII strip + Audit | M | P2 |
| 3 | JobCreationGraph | PII strip + Audit + PostgresSaver | M | P2 |
| 4 | JobWizardGraph | PII strip + Audit + PostgresSaver | M | P2 |

**Fix proposto:** Criar `ComplianceStateGraphBase` que injeta PII strip e audit em cada node automaticamente:
```python
class ComplianceStateGraphBase:
    def _wrap_node(self, node_fn):
        """Wrapper que adiciona PII strip + audit a qualquer node."""
        async def wrapped(state):
            # Pre: PII strip
            state = self._strip_pii(state)
            # Execute
            result = await node_fn(state)
            # Post: Audit
            self._audit_node(node_fn.__name__, state, result)
            return result
        return wrapped
```

### 4.3 Grupo 3: Services De-agentificados (2) — OK

CVScreeningBatchService e TwinInferenceService nao sao agentes — nao precisam convergir para o padrao de agente. Ja usam FairnessGuard diretamente.

---

## MATRIZ DE CONVERGENCIA FINAL

| Aspecto | Estado Atual | Alvo | Gap | Esforco Total |
|---------|-------------|------|-----|---------------|
| **Framework** | 100% LangGraph | 100% LangGraph | 0 | ZERO |
| **Base class** | 100% LangGraphReActBase (ReAct) ou StateGraph | Manter | 0 | ZERO |
| **EnhancedAgentMixin** | 87% (26/30 — StateGraphs nao usam) | 100% (ou equivalente) | 13% | M |
| **ComplianceDomainPrompt** | 100% domains | Manter | 0 | ZERO |
| **Fairness pre-check** | 100% (via domain) | Manter | 0 | ZERO |
| **Fairness post-check** | 3% (1/30) | 100% | 97% | S (1 fix central) |
| **PII strip** | 87% (ReAct via LIA-C04) | 100% | 13% | M (StateGraphs) |
| **Audit** | 87% (ReAct via AuditCallback) | 100% | 13% | M (StateGraphs) |
| **Memory/Learning** | 87% (via EnhancedMixin) | 100% | 13% | M (StateGraphs) |
| **CalibrationWeight** | 0% | 100% | 100% | S (1 fix no mixin) |
| **Prompts em YAML** | 40% (10 YAML, 15 inline) | 100% | 60% | M (15 migracoes) |
| **Tool registry pattern** | 100% | Manter | 0 | ZERO |
| **Tests** | ~30% dos agentes | >80% | 50% | L |

---

## ORDEM DE EXECUCAO

```
ONDA 1 — Fixes centralizados (afetam TODOS os agentes de uma vez)
  1. Fairness post-check no ComplianceDomainPrompt        (S, 1 dia)
  2. CalibrationWeight.load no EnhancedAgentMixin         (S, 1 dia)
  3. CalibrationEvent.record no EnhancedAgentMixin        (S, 1 dia)
  = 3 dias, 30 agentes beneficiados

ONDA 2 — StateGraph compliance
  4. Criar ComplianceStateGraphBase                        (M, 2-3 dias)
  5. Migrar 4 StateGraph agents para ComplianceBase        (M, 2-3 dias)
  = 5 dias, 4 agentes beneficiados

ONDA 3 — Prompt migration
  6. Migrar 15 DOMAIN_SPECIFIC para config/prompts.yaml    (M, 3-5 dias)
  7. Migrar FEW_SHOT_EXAMPLES para YAML                   (S, 1-2 dias)
  = 5 dias, consistencia de prompt

ONDA 4 — Test coverage
  8. Adicionar eval tests por agente (golden scenarios)    (L, ongoing)
  = Continuo
```

**Esforco total: ~15-20 dias** para convergencia completa.

---

## RESUMO EXECUTIVO

### Surpresa positiva
O codebase ja esta **85% convergido**. Todos os 26 ReAct agents usam exatamente o mesmo stack (LangGraphReActBase + EnhancedAgentMixin + ComplianceDomainPrompt). Os 4 StateGraph agents usam LangGraph StateGraph com PostgresSaver. ZERO frameworks divergentes. ZERO agents legacy.

### O que falta (gaps incrementais, nao estruturais)
1. **Fairness POST-check** — 97% dos agentes nao fazem (1 fix central resolve)
2. **CalibrationWeight** — 100% nao consomem (1 fix central resolve)
3. **StateGraph compliance** — 4 agentes sem PII strip + audit completo
4. **Prompts em YAML** — 60% ainda inline (migracao mecanica)
5. **Test coverage** — ~30% (evolucao continua)

### Metafora
Os agentes sao como uma frota de carros do mesmo modelo — todos tem o mesmo motor (LangGraph), mesmo chassi (ReActBase), mesmos freios (FairnessGuard pre-check). O que falta e instalar o airbag traseiro (post-check) e calibrar a suspensao (CalibrationWeight) em todos ao mesmo tempo — e como isso pode ser feito na base class, e uma unica ida a oficina para toda a frota.
