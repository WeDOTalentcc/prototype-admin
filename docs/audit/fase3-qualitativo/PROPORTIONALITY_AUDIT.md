# P14 — Inventário de Over-Engineering e Under-Engineering
**Protocolo:** P14  
**Data:** 2026-04-14  
**Plataforma:** WeDOTalent / LIA AI Platform  
**Escopo:** lia-agent-system (Python/FastAPI), plataforma-lia (Next.js), ats-api-copia (Rails 7.1)  
**Auditor:** Claude Sonnet 4.6 — análise estática via SSH  
**Método:** Line count, class/function scan, complexity grep, pattern detection

---

## Sumário Executivo

| Classificação | Count | % |
|---|---|---|
| PROPORCIONAL | 17 | 47% |
| OVER-ENGINEERED | 13 | 36% |
| UNDER-ENGINEERED | 6 | 17% |
| **Total auditado** | **36** | **100%** |

**Veredicto geral:** A plataforma está **moderadamente over-engineered** na camada de agentes/orquestração e **under-engineered** em tratamento de erros e rastreabilidade. O padrão típico de "vibe-coded AI platform": abstrações ricas sem disciplina de execução nos cortes transversais críticos.

---

## Métricas Agregadas

| Classificação | Count | % | Exemplos Representativos |
|---|---|---|---|
| PROPORCIONAL | 17 | 47% | FairnessGuard, LangGraph StateGraphs, LLM Providers, Compliance/LGPD schemas, Rails models, Frontend stores |
| OVER-ENGINEERED | 13 | 36% | Orchestrator (2 paralelos + deprecated), 31 Tool Registries, Dual SemanticCache, Pipeline 4-agent split, Kanban 4-agent split, TastingEngine, WizardStepService duplicado |
| UNDER-ENGINEERED | 6 | 17% | Error handling (4064 bare excepts), audit shims, PII em logs, TODO repositórios acumulados, database.py monolítico |

---

## Top 5 Mais Over-Engineered (simplificar primeiro)

### 1. Orquestrador Triplicado — CRÍTICO
**Evidência:** Três implementações paralelas ativas:
- `app/orchestrator/main_orchestrator.py` — 1188 linhas (canonical)
- `app/orchestrator/orchestrator.py` — 624 linhas (deprecated, ainda em uso via `app/api/orchestrator_routes.py`)
- `app/orchestrator/cascaded_router.py` — 792 linhas com 8 tiers

O `orchestrator.py` carrega `conversation_memory`, `tool_registry`, `DomainWorkflow`, `StateManager`, `TaskPlanner` em paralelo com `main_orchestrator.py`. Comment no topo: "DO NOT use this class in new code" — mas ainda é chamado em produção.

**Ação:** Migrar `orchestrator_routes.py` para `main_orchestrator`, deletar `orchestrator.py`.  
**Esforço:** M

### 2. 31 Tool Registries sem abstração comum — ALTO
**Evidência:**
```
find app -name "*tool_registry*" → 31 arquivos
autonomous_tool_registry.py: 1614 linhas
sourcing_tool_registry.py: 1423 linhas
kanban_tool_registry.py: 1381 linhas
pipeline_tool_registry.py: 1359 linhas
```
Cada registry é um módulo independente com lista de `ToolDefinition` sem base class compartilhada. O `app/tools/registry.py` (169 linhas) e `app/shared/global_tool_registry.py` existem como infraestrutura separada. Zero reutilização de definições comuns (ex: `get_candidate`, `list_jobs` aparece em múltiplos registries com definições separadas).

**Ação:** Centralizar tools comuns em `shared_tool_registry.py`, herdar nos domínios.  
**Esforço:** L

### 3. WizardStepService Duplicado — ALTO
**Evidência:**
```
app/domains/job_management/services/wizard_step_service.py: 2068 linhas
app/domains/job_management/services/wizard_step_service/service.py: 1271 linhas
```
Dois arquivos com o mesmo nome (`wizard_step_service`), um como módulo file e outro como pacote `__init__`-like. Total: 3339 linhas para um único serviço de criação de vagas. Ambos contêm `class WizardStepService:`.

**Ação:** Consolidar em pacote único, extrair sub-responsabilidades.  
**Esforço:** M

### 4. Pipeline Domain: 4 agentes + 4 tool registries para 1 domínio — ALTO
**Evidência:**
```
pipeline_action_agent.py: 49 linhas (subclass trivial)
pipeline_context_agent.py: 45 linhas (subclass trivial)
pipeline_decision_agent.py: 45 linhas (subclass trivial)
pipeline_transition_agent.py: 316 linhas (base real)
+ pipeline_tool_registry.py: 1359 linhas
+ pipeline_action_tool_registry.py
+ pipeline_context_tool_registry.py
+ pipeline_decision_tool_registry.py
```
Três subclasses de ~45 linhas cada apenas sobrescrevem `DOMAIN_INSTRUCTIONS`. Poderia ser parametrização, não herança.

**Ação:** Unificar em `PipelineReActAgent` com `mode: Literal["action","context","decision"]`.  
**Esforço:** S

### 5. Dual SemanticCache + TastingEngine sem frontend wired — MÉDIO
**Evidência:**
```
app/orchestrator/semantic_cache.py: 112 linhas (SemanticCache — in-memory)
app/orchestrator/vector_semantic_cache.py: 289 linhas (VectorSemanticCache — pgvector)
app/orchestrator/tasting_engine.py: 520 linhas
```
`TastingEngine` doc string explicita: "The structured tasting_insights metadata on ChatResponse is **not yet forwarded through WS to the frontend**. The frontend TastingInsightCard component is ready for when the metadata path is wired (future enhancement)." — 520 linhas de código para uma feature que não chega ao usuário.

Dois caches semânticos coexistentes sem flag explícita de qual está ativo.

**Ação:** Remover `SemanticCache` (substituído por `VectorSemanticCache`); conectar TastingEngine ao WS ou deferir.  
**Esforço:** S

---

## Top 5 Mais Under-Engineered (estruturar primeiro)

### 1. Error Handling: 4064 bare `except Exception` vs 61 typed errors — CRÍTICO
**Evidência:**
```
grep "except Exception" app --include="*.py" | wc -l → 4064
grep "AgentError|DomainError|LIAError" app --include="*.py" | wc -l → 61
```
Proporção: ~1.5% dos blocos de exceção usa erros tipados. Dois exemplos críticos confirmados por P13:
- `pipeline_policy.py:71` — `except Exception: pass` suprime falha de avaliação de política
- `wsi/evaluation.py:300` — `except Exception: pass` suprime falha de busca de pergunta WSI

`str(e)` exposto diretamente em respostas de API em múltiplos locais (stack traces para clientes).

**Ação:** Criar hierarquia `LIAException` com `AgentError`, `OrchestratorError`, `ValidationError`; substituir catches críticos.  
**Esforço:** L

### 2. Audit Compliance: 4 shims de 2-8 linhas apontando para libs não auditadas — ALTO
**Evidência:**
```
app/shared/compliance/audit_storage.py: 8 linhas (shim)
app/shared/compliance/audit_writer.py: 7 linhas (shim)
app/shared/compliance/audit_callback.py: 2 linhas (shim)
app/shared/compliance/audit_models.py: 5 linhas (shim)
```
Todos são `from lia_audit.* import *`. A lib `lia_audit` não está no escopo desta auditoria. O `audit_service.py` (461 linhas) é real mas as interfaces de storage/writer são stubs de re-export sem lógica própria. O diretório compliance aparenta ter mais coverage do que realmente tem.

**Ação:** Verificar se `lia_audit` lib está implementada; consolidar shims ou documentar dependency.  
**Esforço:** S

### 3. PII em Logs de Produção — ALTO
**Evidência:**
```
handlers_lifecycle.py:185 → logger.info(f"... WhatsApp sent to {candidate_phone}: ...")
handlers_lifecycle.py:473 → logger.info(f"... Reschedule WhatsApp sent to {candidate_phone}: ...")
handlers_lifecycle.py:523 → logger.info(f"... Final notice WhatsApp sent to {candidate_phone}: ...")
```
7 locais confirmados (P13) com `email`, `phone`, `name` em `logger.info()`. LGPD Art. 46 exige medidas de segurança técnica; logs de produção com PII violam o princípio.

**Ação:** Substituir por `logger.info(f"... sent to candidate_id={candidate_id}")`.  
**Esforço:** S

### 4. Database Module God Class — MÉDIO
**Evidência:**
```
app/core/database.py: 1359 linhas
```
Contém: configuração de pool asyncpg, definição de tabelas ad-hoc, criação de índices, funções de schema migration manual, health checks, funções utilitárias de query. Inclui `async def create_agent_long_term_memory_table()` que cria tabela diretamente em vez de usar Alembic migration.

**Ação:** Separar em `database_pool.py`, `database_health.py`, migrar DDL para Alembic.  
**Esforço:** M

### 5. 25+ API files com TODO de extração de repository não feitos — MÉDIO
**Evidência:**
```
app/api/v1/pipeline_policy.py:24 → # TODO(phase2): extract to repository
app/api/v1/wsi/evaluation.py:48 → # TODO(phase2): extract to repository
app/api/v1/wsi/sessions.py:32 → # TODO(phase2): extract to repository
app/api/v1/suggestion_feedback.py:72 → # TODO(phase2): extract to repository
...25+ total
```
SQL direto em route handlers (sem camada de repository) — padrão identificado mas não resolvido. Dificulta testes unitários e aumenta duplicação entre endpoints similares.

**Ação:** Criar repositories por domínio (batch), começar pelos paths críticos (WSI evaluation, pipeline policy).  
**Esforço:** L

---

## Inventário Completo por Componente

| # | Componente | Arquivo(s) | Tamanho | Classificação | Evidência Chave | Ação Recomendada | Esforço |
|---|---|---|---|---|---|---|---|
| 1 | MainOrchestrator | `orchestrator/main_orchestrator.py` | 1188L | OVER-ENGINEERED | 104 if/elif; God class orquestrando 4 fases distintas | Extrair Phase 0/1 para módulos separados | M |
| 2 | Orchestrator (deprecated) | `orchestrator/orchestrator.py` | 624L | OVER-ENGINEERED | Marcado "DO NOT USE" mas ativo via `orchestrator_routes.py` | Migrar última rota e deletar | M |
| 3 | CascadedRouter | `orchestrator/cascaded_router.py` | 792L | PROPORCIONAL | 8 tiers com fallback progressivo — complexidade justificada pelo produto | Documentar tiers, manter | — |
| 4 | FastRouter | `orchestrator/fast_router.py` | 654L | PROPORCIONAL | Tier 1/2 rápido, separado do CascadedRouter — separação de concerns correta | — | — |
| 5 | TastingEngine | `orchestrator/tasting_engine.py` | 520L | OVER-ENGINEERED | Feature não conectada ao frontend WS (doc string explícita) | Conectar ou deferir/remover | S |
| 6 | Dual SemanticCache | `orchestrator/semantic_cache.py` (112L) + `vector_semantic_cache.py` (289L) | 401L | OVER-ENGINEERED | Dois caches semânticos, in-memory vs pgvector, sem flag clara de qual ativo | Deletar `semantic_cache.py` (obsoleto) | S |
| 7 | MemoryResolver | `orchestrator/memory_resolver.py` | 386L | PROPORCIONAL | Resolve entre 5 sistemas de memória coexistentes — necessário dado a fragmentação | — | — |
| 8 | PolicyEngine (orquestrador) | `orchestrator/policy_engine.py` | 345L | PROPORCIONAL | Wrapper correto para avaliação de políticas no pipeline de orquestração | — | — |
| 9 | TaskPlanner | `orchestrator/task_planner.py` | 236L | PROPORCIONAL | DAG de tarefas para AutomationAgent — proporcional ao domínio | — | — |
| 10 | TemporalResolver | `orchestrator/temporal_resolver.py` | 240L | PROPORCIONAL | Resolução de expressões temporais em PT-BR — complexidade linguística justifica | — | — |
| 11 | Tool Registries (31 arquivos) | `domains/*/agents/*_tool_registry.py` | 1614L máx | OVER-ENGINEERED | 31 arquivos, sem base class, tools comuns redefinidas em múltiplos registries | Centralizar tools comuns | L |
| 12 | ReAct Agents (domínios) | `domains/*/agents/*_react_agent.py` | 113-377L | PROPORCIONAL | Padrão consistente via `LangGraphReActBase + EnhancedAgentMixin`, boilerplate mínimo | — | — |
| 13 | Pipeline Domain (4 sub-agentes) | `domains/pipeline/agents/pipeline_*.py` | 49-316L | OVER-ENGINEERED | 3 subclasses de 45L que só sobrescrevem `DOMAIN_INSTRUCTIONS` | Parametrizar, não herdar | S |
| 14 | Kanban Domain (4 sub-agentes) | `domains/recruiter_assistant/agents/kanban_*.py` | 44-152L | OVER-ENGINEERED | Mesmo padrão: action/insight/search como subclasses triviais de `KanbanReActAgent` | Parametrizar | S |
| 15 | WizardStepService (duplicado) | `wizard_step_service.py` (2068L) + `wizard_step_service/service.py` (1271L) | 3339L total | OVER-ENGINEERED | Dois arquivos com mesmo nome — arquivo e pacote coexistindo | Consolidar | M |
| 16 | WSI Interview Graph | `cv_screening/agents/wsi_interview_graph.py` | 1123L, 14 edges | PROPORCIONAL | StateGraph complexo mas justificado: múltiplas etapas de entrevista com estado | — | — |
| 17 | Job Wizard Graph | `job_management/agents/job_wizard_graph.py` | 642L, 7 edges | PROPORCIONAL | StateGraph para wizard multi-step de criação de vaga | — | — |
| 18 | Interview Scheduling Graph | `interview_scheduling/agents/interview_graph.py` | 455L (nodes) | PROPORCIONAL | StateGraph discreto com proteção de loop (`MAX_ITERATIONS=8`) | — | — |
| 19 | FairnessGuard | `shared/compliance/fairness_guard.py` | 1002L | PROPORCIONAL | Single canonical implementation, 3-tier check (regex→implicit→semantic), bem conectado | — | — |
| 20 | C3B Layer | `shared/compliance/c3b_layer.py` | 126L | PROPORCIONAL | Pre/post compliance hooks simples, sem over-abstração | — | — |
| 21 | Audit Compliance Shims | 4 arquivos, 2-8L cada | 22L total | UNDER-ENGINEERED | Shims de re-export para `lia_audit` lib não visível; coverage ilusória | Verificar/implementar lib | S |
| 22 | PromptInjectionGuard | `shared/compliance/prompt_injection_guard.py` | 15L | UNDER-ENGINEERED | Arquivo existe mas tem apenas 15 linhas — proteção insuficiente para injeção de prompt | Implementar detecção real | M |
| 23 | Error Handling (sistêmico) | 4064 `except Exception` em todo o app | — | UNDER-ENGINEERED | 1.5% de erros tipados vs 98.5% genérico; silents em paths críticos | Hierarquia de exceções | L |
| 24 | LLM Providers | `shared/providers/llm_*.py` | 79-636L | PROPORCIONAL | Provider pattern correto (ABC + implementações Claude/Gemini/OpenAI), factory adequado | — | — |
| 25 | LLMService (domains/ai) | `domains/ai/services/llm.py` | ~400L (est.) | PROPORCIONAL | Wrapper com PII stripping + audit — responsabilidade clara | — | — |
| 26 | Config Library | `libs/config/lia_config/config.py` | 365L | PROPORCIONAL | Pydantic Settings subcategorizados, hierarquia clara, sem env var hardcoded | — | — |
| 27 | ConversationMemory | `recruiter_assistant/services/conversation_memory.py` | 849L | PROPORCIONAL | Única classe, responsabilidade clara (CRUD + summarize + context build), 3 instâncias no app | — | — |
| 28 | Database Module | `app/core/database.py` | 1359L | UNDER-ENGINEERED | God class: pool config + DDL direto + health + utils + migration manual | Separar responsabilidades | M |
| 29 | API Layer (>200 endpoints) | `app/api/v1/*.py`, 86965L total | — | OVER-ENGINEERED | 200+ arquivos de endpoint; 25+ com TODO de extração de repo não feitos; `billing.py` 1713L sem repository | Extração de repositories | L |
| 30 | God API Files | `billing.py` 1713L, `teams.py` 1557L, `workos.py` 1400L, `chat.py` 1023L | 5693L | OVER-ENGINEERED | Múltiplas responsabilidades por arquivo, SQL direto, sem repository pattern | Dividir por responsabilidade | M |
| 31 | PII em Logs | `handlers_lifecycle.py:185,473,523` e 4 outros | — | UNDER-ENGINEERED | `{candidate_phone}`, `{email}` direto em `logger.info()` — 7 locais confirmados | Substituir por IDs | S |
| 32 | Schemas (55 arquivos) | `app/schemas/*.py`, 10967L total | — | PROPORCIONAL | Pydantic models bem definidos, `cv_parser.py` com 51 validators — coerente com domínio | — | — |
| 33 | VoiceScreeningOrchestrator | `voice/services/voice_screening_orchestrator.py` | 1725L | OVER-ENGINEERED | 1725L para serviço de triagem por voz — múltiplas classes internas, mistura session/orchestration/consent | Separar `VoiceSession` de `VoiceOrchestrator` | M |
| 34 | Frontend Components | `plataforma-lia/src`, 2225 arquivos, 231K linhas | — | PROPORCIONAL | Organização por feature pages/components, Zustand stores bem segmentados (14 stores) | — | — |
| 35 | Rails Backend | `ats-api-copia/app`, 163 arquivos `.rb` | 1128L models | PROPORCIONAL | Modelos Rails lean (26-116L), CRUD responsibility clear, multi-tenant via Apartment | — | — |
| 36 | Autonomous Agent | `autonomous/agents/autonomous_react_agent.py` + `autonomous_tool_registry.py` | 398L + 1614L | PROPORCIONAL | Fallback cross-domain com 40+ tools — escopo justifica tamanho; CircuitBreaker correto | — | — |

---

## Análise por Categoria

### Over-Engineering Patterns Found

#### 1. Redundância de Implementação (4 ocorrências)
- `orchestrator.py` (deprecated) coexistindo com `main_orchestrator.py`
- `semantic_cache.py` coexistindo com `vector_semantic_cache.py`
- `wizard_step_service.py` file + `wizard_step_service/service.py` pacote
- `shared/services/graph_runner.py` (2L shim) + `domains/ai/services/graph_runner.py` (424L real)

#### 2. Herança Trivial em vez de Parametrização (2 ocorrências)
- Pipeline: 3 subclasses de 45L cada (action/context/decision) só sobrescrevem constante
- Kanban: 3 subclasses de 44-49L (action/insight/search) idem

#### 3. Features Não Conectadas ao Produto (1 ocorrência)
- `TastingEngine` (520L): doc confirma que a metadata path para o frontend "is not yet forwarded through WS"

#### 4. Tool Registries sem Abstração Comum (31 arquivos)
- Definições de tools comuns (`get_job_details`, `list_candidates`) duplicadas em múltiplos registries sem DRY

#### 5. God Classes em API Layer
- `billing.py` (1713L), `teams.py` (1557L), `workos.py` (1400L) sem separação de repository

---

### Under-Engineering Patterns Found

#### 1. Exception Monocultura (crítico)
- 4064 `except Exception` genéricos; apenas 61 erros tipados no sistema inteiro
- Ratio 1.5% tipado vs 98.5% genérico
- Silents confirmados em paths críticos: `pipeline_policy.py:71`, `wsi/evaluation.py:300`

#### 2. PII em Logs sem Mascaramento
- 7 locais com `{candidate_phone}`, `{email}`, `{name}` em `logger.info()`
- `handlers_lifecycle.py` é o arquivo mais crítico (3 ocorrências confirmadas)

#### 3. Repository Pattern Prometido mas não Implementado
- 25+ comentários `# TODO(phase2): extract to repository` espalhados em route handlers
- SQL direto em endpoints de API dificulta testes unitários

#### 4. Prompt Injection Guard Insuficiente
- `prompt_injection_guard.py`: 15 linhas — insuficiente para proteção real

#### 5. Database God Module
- `database.py` (1359L) mistura pool, DDL, health, utils, DDL manual (fora do Alembic)

---

## Recomendações Prioritizadas

| Prioridade | Ação | Arquivo(s) | Esforço | Impacto |
|---|---|---|---|---|
| CRÍTICO | Criar hierarquia de exceções `LIAException` e substituir `except Exception: pass` em paths de negócio | `pipeline_policy.py:71`, `wsi/evaluation.py:300`, + 20 mais críticos | L | Segurança, debugging |
| CRÍTICO | Remover PII dos logs: substituir `{candidate_phone}`, `{email}` por `{candidate_id}` | `handlers_lifecycle.py:185,473,523` + 4 outros | S | LGPD Art. 46 |
| HIGH | Migrar `orchestrator_routes.py` para `MainOrchestrator` e deletar `orchestrator.py` | `orchestrator/orchestrator.py`, `api/orchestrator_routes.py` | M | Débito técnico, clareza |
| HIGH | Deletar `orchestrator/semantic_cache.py` (substituído por `VectorSemanticCache`) | `orchestrator/semantic_cache.py` | S | Remoção de dead code |
| HIGH | Resolver `WizardStepService` duplicado (arquivo vs pacote) | `services/wizard_step_service.py` + `wizard_step_service/` | M | Confusão de importação |
| HIGH | Unificar sub-agentes Pipeline (action/context/decision) em `PipelineReActAgent(mode=...)` | `pipeline_action_agent.py`, `pipeline_context_agent.py`, `pipeline_decision_agent.py` | S | Simplificação imediata |
| HIGH | Idem para Kanban (action/insight/search) | `kanban_action_agent.py`, `kanban_insight_agent.py`, `kanban_search_agent.py` | S | Simplificação |
| MEDIUM | Conectar `TastingEngine` ao WebSocket ou remover até estar pronto | `orchestrator/tasting_engine.py`, `api/v1/agent_chat_ws.py` | M | Feature incompleta |
| MEDIUM | Separar `database.py` em `database_pool.py` + `database_health.py`; mover DDL para Alembic | `app/core/database.py` | M | Testabilidade |
| MEDIUM | Batch de extração de repositories para endpoints críticos (WSI, pipeline, policy) | `api/v1/wsi/evaluation.py`, `api/v1/pipeline_policy.py` + 5 outros | L | Testabilidade, DRY |

---

## Notas de Contexto

- **Over-engineering foi vibe-coded, não planejado:** os patterns de herança trivial (Pipeline 4-agents, Kanban 4-agents) sugerem geração automática sem review arquitetural. São fáceis de colapsar.
- **Under-engineering nos cortes transversais é o risco maior:** 4064 bare excepts + PII em logs representa risco LGPD real, não apenas débito técnico.
- **Rails é o componente mais saudável:** models lean, responsabilidades claras, sem over-abstração.
- **Compliance aparente vs real:** a existência de 12 arquivos em `shared/compliance/` cria impressão de robustez, mas 4 deles são shims de 2-8 linhas. O `PromptInjectionGuard` (15L) é insuficiente para produção.
- **Frontend é proporcional:** 2225 arquivos, 14 Zustand stores bem segmentados, componentes com tamanho razoável (maiores ~1071L para `sidebar.tsx` que agrega muita navegação — aceitável).
