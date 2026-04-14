# MATURITY_ASSESSMENT.md — LIA Agent System
**Data:** 2026-04-13  
**Protocolo:** P03 — Diagnóstico de Maturidade  
**Auditor:** Senior Consultant, Agentic AI Systems  
**Sistema:** LIA Agent System — WeDOTalent  
**Escopo:** 6 dimensões de maturidade agentica × evidências de código × benchmark de mercado  
**Fontes:** PLATFORM_MAP.md (1445 linhas), FLOW_TRACES.md (1011 linhas), PROMPT_AUDIT.md (572 linhas) + inspeção direta de código

---

## RESUMO EXECUTIVO

O LIA Agent System é uma plataforma de recrutamento multi-agente construída sobre LangGraph ReAct. Em termos de **volume de arquitetura**, supera a maioria dos produtos HR-AI de mercado: 35 classes de agente, 120+ tools, 3 LangGraph StateGraphs com HITL, camada de fairness com 60+ termos bloqueados, e infraestrutura de compliance LGPD/BCB 498/SOX genuinamente implementada. Isso é real, não cosmético.

O problema é a **profundidade de execução**. O diagnóstico identificou 8 gaps críticos (severidade vermelha) e 22 gaps de alto impacto que comprometem funcionalidades core: emails enviados como `simulated=True`, agendamento de entrevistas sem `company_id` no registro, HITL fail-open em triagem de candidatos, e dashboard servindo mock data. Em outras palavras: o sistema parece mais capaz do que de fato é quando executado em produção.

**Classificação:** Agente Funcional com Supervisão (3.2/5) — acima de assistentes conversacionais, mas com gaps de execução que impedem classificação como Agente Maduro.

---

## DIMENSÃO 1 — AGÊNCIA

**Score Atual: 3/5**  
**Score Alvo: 4/5**

### Evidências (código)

- `app/shared/agents/agent_registry.py` — `create_react_agent()` (LangGraph prebuilt) como base de todos os 17 agentes ReAct registrados via `@register_agent`
- `app/domains/cv_screening/agents/wsi_interview_graph.py:972` — `interrupt_before=["lg_generate_feedback"]` implementado como gate HITL real com `hitl_service.request_approval()`
- `app/domains/job_management/agents/job_wizard_graph.py:176–177` — `interrupt_before=["stage_transition"]` no JobWizardGraph
- `app/orchestrator/main_orchestrator.py:52–58` — Phase 0 (pending actions), Phase 1 (action executor), Phase 2 (cascaded routing) — pipeline de 3 fases antes de delegar ao agente
- `app/orchestrator/agentic_loop.py:21` — `MAX_TOOL_ITERATIONS=3` (via `LIA_MAX_TOOL_ITERATIONS`)
- `app/domains/autonomous/agents/autonomous_react_agent.py` — `AUTONOMOUS_REACT_MAX_STEPS` default 10, circuit breaker próprio (threshold=3, recovery=30s)
- `app/domains/sourcing/agents/sourcing_react_agent.py` — 5 estágios, 10 sub-agentes especializados com handoff
- `libs/agents-core/lia_agents_core/checkpointer.py` — `PostgresSaver` em produção com `thread_id=session_id` para persistência de estado entre turnos

### Justificativa do Score

O sistema demonstra agência genuína em múltiplas camadas. Os agentes operam no padrão ReAct (Raciocinar→Agir→Observar) com até 10 iterações no caso do AutonomousReActAgent, e com decomposição hierárquica real: o SourcingReActAgent, por exemplo, delega para 10 sub-agentes especializados (Planner, Search, Enrich, Engagement, GitHub, StackOverflow, Diversity, Passive, Referral, Nurture), cada um com toolset específico e modelo LLM apropriado (haiku-4-5 para tarefas simples, sonnet-4-6 para raciocínio complexo). O HITL está implementado como interrupção real do grafo LangGraph (`interrupt_before`), não como mock — o grafo pausa, armazena estado no PostgresSaver, e retoma após aprovação humana.

O que impede o score 4 é a inconsistência de execução real em relação ao que a arquitetura promete. O HITL é fail-open em dois locais críticos: `wsi_interview_graph.py:1057` — se `request_approval()` falhar, o grafo prossegue sem revisão humana. A comunicação via agente retorna `simulated=True` (`communication_tools.py:104,195`) sem acionar dispatch real. O `schedule_interview` tool em `scheduling_tools.py:87` é um stub que retorna URL falsa sem DB write. Esses não são casos de borda: são os flows mais executados em produção.

A presença simultânea de dois sistemas para o mesmo workflow (WizardReActAgent para acesso WS, JobWizardGraph para acesso REST via `USE_REACT_AGENTS=false`) indica que a arquitetura tem decisão de design não resolvida, produzindo comportamento divergente dependendo do canal de entrada.

### Gap Analysis

Para atingir score 4 (Autônomo com Supervisão):
- Corrigir as 4 ferramentas críticas com implementação stub/simulada (send_email, send_whatsapp, schedule_interview, run_wsi_screening) para chamar os dispatchers reais
- Eliminar o HITL fail-open: se `request_approval()` falhar, o grafo deve pausar e notificar, não prosseguir silenciosamente
- Consolidar WizardReActAgent e JobWizardGraph num único path de execução
- Registrar `interview_scheduling` no AgentRegistry para que acesso via WS não caia no fallback "talent"

### Quick Wins (alto impacto, baixo esforço — dias)

1. **Corrigir `communication_tools.py:104,195`** — conectar `send_email()` e `send_whatsapp()` ao `CommunicationDispatcher` real. Mudança de ~20 linhas. Elimina o bug crítico F4-G1 onde o agente reporta sucesso de envio mas nenhum email/WhatsApp é despachado.
2. **Transformar HITL fail-open em fail-closed**: `wsi_interview_graph.py:1057` — capturar exceção de `request_approval()` e setar `state.stage = "PAUSED"` em vez de continuar. Protege integridade do processo de triagem.
3. **Registrar `interview_scheduling` no AgentRegistry** — 1 linha de `@register_agent("interview_scheduling")` no `interview_graph.py`, evitando queda silenciosa para TalentReActAgent quando usuário agenda pelo chat.

### Investimentos Estruturais (semanas/meses)

1. **Unificação de implementações paralelas** — Decidir entre WizardReActAgent e JobWizardGraph como implementação canônica. Deprecar o outro com migration path claro. Isso resolve F7-G1 e reduz superfície de manutenção.
2. **Camada de tool validation pre-dispatch** — Implementar contrato de interface para todas as tools: cada tool deve declarar se é `simulated=False` e ter teste de integração automatizado que valide a chamada end-to-end. Previne regressão do problema de tools stub.

---

## DIMENSÃO 2 — ORQUESTRAÇÃO

**Score Atual: 4/5**  
**Score Alvo: 5/5**

### Evidências (código)

- `app/orchestrator/cascaded_router.py` — 8-tier cascade: MemoryResolver → LRU in-process → Redis hash → VectorSemanticCache (pgvector cosine ≥0.85) → FastRouter (regex/keyword) → LLM Cascade (Flash→Sonnet→Opus) → AutonomousReActAgent → clarification
- `app/domains/job_management/agents/job_wizard_graph.py:176–177` — `StateGraph` com `add_conditional_edges`, cycle protection `MAX_ITERATIONS=10`, HITL `interrupt_before`
- `app/domains/cv_screening/agents/wsi_interview_graph.py:871–872` — StateGraph com 9 nós, ciclo controlado (lg_advance → lg_generate_question)
- `app/domains/interview_scheduling/agents/interview_graph.py:129–130` — StateGraph, `MAX_ITERATIONS=8`
- `libs/agents-core/lia_agents_core/checkpointer.py` — `PostgresSaver` (prod) / `MemorySaver` (dev) com `RuntimeError` se PostgresSaver indisponível em prod
- `app/shared/resilience/circuit_breaker.py` — CircuitBreaker CLOSED/OPEN/HALF_OPEN com notificação Bell+Teams via Redis dedup (1 alerta/hora)
- `app/shared/resilience/dlq_service.py` — DLQ Redis list `dlq:{queue}` com TTL 7d, cap 1000/queue, admin endpoints inspect/requeue/clear
- `libs/config/lia_config/celery_app.py` — 5 priority queues, 16 Celery Beat jobs, retry policies por task type
- `app/orchestrator/llm_cascade.py` — LLMCascadeRouter: Gemini Flash (conf≥0.80) → Claude Sonnet (conf≥0.70) → Claude Opus (fallback)

### Justificativa do Score

A orquestração é o ponto mais maduro do sistema e provavelmente o diferencial técnico mais relevante. O CascadedRouter com 8 tiers resolve o problema de routing econômico de forma elegante: regex O(1) antes de LLM, cache semântico pgvector antes de nova chamada, autonomous agent como fallback antes de pedir clarificação ao usuário. O custo médio por routing query cai dramaticamente em relação a sistemas que chamam LLM para cada roteamento. O uso de `PostgresSaver` como checkpointer para todos os StateGraphs garante que o estado conversacional sobrevive a reinicializações de worker — algo que a maioria dos tutoriais LangGraph ignora.

O pipeline de Celery com 5 filas de prioridade e 16 jobs de beat é sofisticado: a fila `sourcing_high` (prioridade 8, concorrência 4) garante que buscas de candidato não bloqueiam por avaliações WSI (fila `evaluation_normal`, prioridade 5). A DLQ com Redis e admin endpoints para inspect/requeue/clear é observability operacional real.

O score 4 em vez de 5 reflete dois problemas estruturais: (1) 3 registries de agentes coexistindo (`AgentRegistry`, `ReactAgentRegistry`, `DomainRegistry`) sem canônico declarado — risco de divergência quando um agente é atualizado num registry mas não nos outros; (2) `APScheduler` usando `MemoryJobStore` (`automation_scheduler.py`) em vez de Redis — impossibilita escalonamento horizontal e torna o sistema single-instance para automações time-based, uma limitação não documentada que surpreende em produção.

### Gap Analysis

Para atingir score 5 (Totalmente Autônomo com Loops de Aprendizado):
- Consolidar os 3 registries num canônico único com deprecation path formal para `ReactAgentRegistry`
- Migrar `APScheduler` de `MemoryJobStore` para `RedisJobStore` (ou Celery Beat para todos os jobs de automação), habilitando escalonamento horizontal
- Adicionar observabilidade de routing: tracing distribuído por tier (quantas queries chegam ao T5 LLM, custo por tier) — atualmente Prometheus foi removido (Task #138, `cascaded_router.py`) sem substituto declarado

### Quick Wins

1. **Declarar AgentRegistry como canônico** em `agents_registry.yaml` com seção `deprecated_registries` — sem breaking change imediato, mas documenta o path de consolidação e evita que novos agentes sejam registrados no registry errado.
2. **Adicionar métricas de tier ao CascadedRouter** — logar `route_source` (fast_router, llm_cascade, etc.) em JSON estruturado. Dados já existem em `RouteResult.source`, falta apenas a linha de log.

### Investimentos Estruturais

1. **Consolidação dos 3 registries** — Migrar todos os agentes para `AgentRegistry` (`app/shared/agents/agent_registry.py`) e deprecar `ReactAgentRegistry`. Estimativa: 2–3 semanas de refatoração + testes.
2. **Migração APScheduler → Celery Beat** — Unificar todos os jobs periódicos em Celery Beat (já existe para 16 jobs, faltam os 11 da `automation_scheduler.py`). Habilita horizontal scaling e DLQ automática via `LIATask.on_failure`.

---

## DIMENSÃO 3 — PROFUNDIDADE DE INTELIGÊNCIA

**Score Atual: 2.5/5**  
**Score Alvo: 4/5**

### Evidências (código)

- `app/domains/ai/services/ragas_evaluation_service.py` — RAGAS implementado com 4 métricas (faithfulness, answer_relevancy, context_precision, context_recall), threshold 0.70, batch diário via Celery `ragas.evaluate_batch`. **Porém**: `_ragas_available = False` se pacote não instalado (usa heurística simplificada de comprimento/coerência), e os scores não alteram comportamento dos agentes — são observabilidade pura.
- `app/shared/prompts/templates.py` — `PromptTemplate` com `cot_enabled` (Chain-of-Thought auto-inject) e `few_shot_examples` declarativos. Porém `get_analytics_system_prompt()` e `get_communication_system_prompt()` retornam apenas `DOMAIN_SPECIFIC` sem compor com shared blocks.
- `app/domains/analytics/services/predictive_analytics_service.py:182–277` — `_load_model_weights()` retorna dict hardcoded: `{"wsi_score": 0.30, "dropout_base": 0.15, ...}`, `market_factor = 1.0 HARDCODED`
- `app/core/database.py` — tabelas `learning_patterns` e `interaction_feedback` com campos `incorporated_to_rag`, `example_good_responses`, `example_bad_responses`
- `app/domains/ai/services/model_drift_service.py` — 4 triggers de drift (score_drift ±0.5, approval_drift ±10pp, cost_drift ±20%, latency_drift ±50%) comparando janela 7d vs baseline 7d. Batch diário via `drift.run_batch`.
- Prompt scores PROMPT_AUDIT: TalentReActAgent 29/33, KanbanInsightAgent 30/33, PipelineReActAgent 27/33, CommunicationReActAgent 20/33, AnalyticsReActAgent 22/33
- `app/domains/cv_screening/agents/wsi_interview_graph.py` — Scoring 100% determinístico: BARS + Bloom taxonomy (6 níveis) + Dreyfus (5 níveis), sem LLM judge, PROTECTED_CRITERIA excluídos explicitamente

### Justificativa do Score

O sistema apresenta uma dualidade clara: a inteligência de triagem (WSI) é genuinamente sofisticada — scoring 100% determinístico baseado em Bloom/Dreyfus sem LLM judge elimina a principal fonte de viés e alucinação em sistemas concorrentes. O raciocínio dos prompts de Talent, Kanban e Pipeline é bem articulado, com Chain-of-Thought injetado, few-shot examples com 8+ cenários, e context injection dinâmica via `memory_summary` + `stage_context`.

O problema está na inteligência que não se fecha em loop. O RAGAS é implementado mas opera como observabilidade passiva — scores abaixo de 0.70 geram `logger.warning` mas não disparam correção automática de prompts, mudança de modelo ou ajuste de RAG. O `ModelDriftService` detecta drift nos 4 indicadores mas não tem path de resposta automatizado (sem re-prompt, sem model downgrade/upgrade automático). A `learning_patterns` table captura feedback positivo/negativo e injeta few-shot examples com confidence ≥0.5 — isso é funcional — mas o "loop" depende de Celery Beat diário, não de aprendizado online por inferência.

A maior lacuna de inteligência é a analítica preditiva: `market_factor = 1.0 HARDCODED` em `predictive_analytics_service.py:247` significa que as previsões de `time_to_fill` nunca consideram condições de mercado reais. O dashboard serve mock data confirmado por comentário em código (`dashboard_data.py:7`). Para uma plataforma que vende "IA preditiva", isso é uma gap de produto sério.

### Gap Analysis

Para atingir score 4:
- Fechar o loop RAGAS: scores abaixo do threshold devem disparar revisão automática do prompt ou seleção de modelo mais capaz para aquele domínio
- Substituir `market_factor = 1.0` por dado real (SerpAPI já integrado para salary benchmark — reutilizar)
- Corrigir `dashboard_data.py` para servir dados reais das queries já existentes nos services de analytics
- Estender context injection dinâmica (`REASONING_PROMPT` com `memory_summary`) para CommunicationReActAgent e AnalyticsReActAgent (atualmente retornam apenas `DOMAIN_SPECIFIC` estático)

### Quick Wins

1. **Conectar RAGAS ao logging de alertas operacionais** — Quando `overall_score < 0.70`, além do `logger.warning`, emitir notificação Bell+Teams (já existe o mecanismo em `circuit_breaker.py`). Custo: 10 linhas. Benefício: visibilidade imediata de degradação de qualidade.
2. **Corrigir `dashboard_data.py`** — Trocar retornos de mock data pelos services reais (`JobInsightsService`, `PredictiveAnalyticsService`) já implementados. Alta visibilidade de produto, baixo esforço técnico.
3. **Context injection para CommunicationReActAgent** — Adicionar `REASONING_PROMPT` com `memory_summary` + `stage_context`. Prompt score atual é 20/33; com essa mudança vai para ~26/33.

### Investimentos Estruturais

1. **Loop de feedback fechado para prompts** — Implementar pipeline onde scores RAGAS < threshold por N dias consecutivos disparam PR automático com sugestão de melhoria de prompt (ou pelo menos task no backlog com contexto detalhado). Requer ~4 semanas de engenharia.
2. **Inteligência preditiva com dados reais** — Integrar feed de dados de mercado (SerpAPI para time-to-fill benchmark, LinkedIn Trends API ou alternativa) nos modelos preditivos. `market_factor` passa de 1.0 hardcoded para variável por setor/localização/senioridade.

---

## DIMENSÃO 4 — ORQUESTRAÇÃO DE TOOLS

**Score Atual: 3.5/5**  
**Score Alvo: 4/5**

### Evidências (código)

- `app/tools/registry.py` — `ToolRegistry` + `ToolDefinition(name, description, parameters_schema, handler, allowed_agents)` — metadados declarativos com schema de parâmetros
- `app/tools/tool_registry_metadata.yaml` — definição YAML validada contra runtime (Sprint G5)
- `app/shared/tool_handler.py` — `@tool_handler("domain")` decorator async com error wrapping e context injection
- `libs/agents-core/lia_agents_core/react_loop.py` — `tool_definition_to_langchain_tool()` para integração com `create_react_agent()`
- 28 registries de tool por domínio, ~120 tools totais catalogadas
- `app/domains/kanban/tools/kanban_tool_registry.py` — 22 tools com 3 sub-agentes (Search 6 tools, Insight 8 tools, Action 8 tools) — decomposição funcional clara
- `app/domains/autonomous/agents/autonomous_react_agent.py` — 40+ tools curadas, circuit breaker próprio, max 10 steps
- `communication_tools.py:104,195` — `send_email()` e `send_whatsapp()` retornam `{simulated: True}` — **bugs críticos F4-G1**
- `scheduling_tools.py:87` — `send_interview_invitation` é stub que apenas loga — **bug F5-G6**
- `app/api/v1/agent_chat_ws.py:9.4` — 5 gaps críticos de ferramenta identificados no PLATFORM_MAP §9.4: `schedule_interview` stub, `run_wsi_screening` não existe como LLM tool, `send_email` simulated, `generate_offer` sem DB write, `get_pipeline_summary` não wired

### Justificativa do Score

A infraestrutura de tools é bem projetada: schema declarativo com `ToolDefinition`, validação YAML contra runtime, decorator de error wrapping async, conversão automática para formato LangChain. O Kanban com 22 tools decompostas em 3 sub-agentes funcionais (read/analytics/action) é um bom exemplo de separação de responsabilidades. O AutonomousReActAgent com 40+ tools curadas e circuit breaker próprio demonstra que o time pensou em resiliência para o agente cross-domain mais complexo.

O problema é a proporção de tools com implementação incompleta nas flows mais críticas. O PLATFORM_MAP §9.4 lista explicitamente 5 tools com gaps severos de implementação. O mais grave: `communication_tools.send_email()` e `send_whatsapp()` chamados pelo CommunicationReActAgent retornam `{simulated: True}` — o agente acredita ter enviado o email/WhatsApp e reporta sucesso ao recrutador, mas nenhuma mensagem é entregue ao candidato. Isso não é um bug de edge case — é o flow primário de comunicação via chat IA.

Adicionalmente, `allowed_agents` no `ToolDefinition` não está sendo aplicado como guardrail em tempo de execução — um agente pode invocar tools fora do seu domínio se o LLM alucinar o nome de uma ferramenta. Não há evidência de enforcement de `allowed_agents` nos logs ou no dispatcher.

### Gap Analysis

Para atingir score 4:
- Implementar as 5 tools críticas com lógica real (eliminar stubs e `simulated=True`)
- Adicionar enforcement de `allowed_agents` no dispatch — se `company_id` do agente atual não está em `tool.allowed_agents`, retornar `ToolError` em vez de executar
- Criar suite de testes de integração para cada tool que faz I/O externo (email, calendar, ATS) — validar que o dispatch real funciona antes de deploy

### Quick Wins

1. **Conectar `communication_tools.send_email()` ao `CommunicationDispatcher`** — 20 linhas, elimina F4-G1. Impacto imediato: emails via agente passam a ser entregues.
2. **Adicionar teste smoke para cada tool com I/O externo** — Script que verifica `simulated != True` nos retornos de cada tool crítica. Pode ser um health check endpoint existente (`/api/v1/health_check.py`).

### Investimentos Estruturais

1. **Enforcement de `allowed_agents`** no `ToolExecutor` — Adicionar verificação antes de despachar qualquer tool call, com log de auditoria quando violação é detectada. Aumenta segurança e facilita debug de comportamento inesperado.
2. **Contrato de interface de tool** — Definir protocolo formal: toda tool com I/O externo deve ter `integration_test()` e `health_check()` implementados. Previne regressão dos stubs em futuros desenvolvimentos.

---

## DIMENSÃO 5 — INTEGRAÇÃO TRANSVERSAL (FAIRNESS, COMPLIANCE, LGPD)

**Score Atual: 3.5/5**  
**Score Alvo: 5/5**

### Evidências (código)

- `app/shared/compliance/fairness_guard.py` — FairnessGuard com 60+ termos PT/EN, normalização unicode, categorias: estética, proxies socioeconômicos, religião, deficiência, família/maternidade, idade, geografia. Retorno: `FairnessCheckResult` com mensagem cita Lei 12.984/14, Lei 13.146/15, CLT Art. 373-A, CF Art. 5
- `app/shared/compliance/c3b_layer.py` — pre (PII strip + FairnessGuard) e post (FactChecker + AuditService) para 8 domínios HR: `recruitment, talent_ranking, talent_pool, job_scoring, performance, salary_benchmark, job_management, candidate_evaluation`. **[⚠] `LIA_DISABLE_C3B=1` desativa toda a camada.**
- `app/api/v1/lgpd_compliance.py` — 28+ endpoints: DPO CRUD, breach management com prazo ANPD 48h, DSR portal público (LGPD Art. 18), exclusão programada, revisão de decisão automatizada
- `app/shared/services/bias_audit_service.py` — Four-Fifths Rule (AIR ≥0.80), chi-square (scipy ou fallback Python), EEOC flag, dimensões: gender, age_group (<30/30–44/45+), disability (PCD/non-PCD), region
- `app/domains/cv_screening/agents/wsi_interview_graph.py` — Scoring 100% determinístico, `PROTECTED_CRITERIA` excluídos de cada `audit_service.log_decision()`
- `app/api/v1/admin_compliance_fairness.py` — Relatório Four-Fifths Rule assinado HMAC-SHA256 (NYC LL 144 / EU AI Act Art. 13)
- `c3b_layer.py:17–26` — `_FAIRNESS_DOMAINS` exclui "sourcing" e "cv_screening" — **gap F1-G4 e F2-G7**
- `query_tools.py:79–82` — `hasattr(Candidate,'company_id')` — tenant isolation condicional **gap crítico F1-G1**
- `wsi_interview_graph.py:350–362` — `job_screening_questions` query sem `company_id` filter — **cross-tenant exposure crítico F2-G1/F3-G1**
- `triggers.py:252–380` — PATH A de execute-action bypassa todos os checks LGPD — **gap crítico F4-G2**

### Justificativa do Score

A plataforma investiu genuinamente em compliance: o `FairnessGuard` com 60+ termos é um dos mais completos do mercado BR, com fundamento legal explícito em cada mensagem de bloqueio. O scoring WSI 100% determinístico sem LLM judge é uma decisão de design defensável que elimina a principal fonte de viés algorítmico em sistemas de triagem. O sistema de LGPD com 28+ endpoints, DSR público, breach management com timer ANPD e consent versionado com SHA256 é enterprise-grade.

O problema é a cobertura inconsistente: a camada C3b aplica FairnessGuard + PII strip apenas para 8 domínios HR listados em `_FAIRNESS_DOMAINS`, excluindo "sourcing" e "cv_screening" — os dois flows com maior volume de dados sensíveis de candidatos. O gap F1-G1 é o mais grave do sistema inteiro: `hasattr(Candidate,'company_id')` em `query_tools.py:79–82` significa que se o campo `company_id` não está no ORM por qualquer razão (migração pendente, model inconsistente), o filtro de tenant é silenciosamente omitido e todos os candidatos de todas as empresas são retornados. Isso não é hipotético — é uma vulnerabilidade estrutural de multi-tenancy.

O gap F2-G1/F3-G1 (`job_screening_questions` sem `company_id`) é igualmente crítico: qualquer `job_vacancy_id` válido expõe as perguntas de triagem de outra empresa. E o PATH A em `triggers.py:252–380` permite que qualquer automação dispare email/WhatsApp sem verificação de opt-out, consent ou quarantine — violação direta de LGPD Art. 7.

### Gap Analysis

Para atingir score 5:
- Corrigir F1-G1: substituir `hasattr()` por check explícito com `RuntimeError` se `company_id` ausente, igual ao padrão de `get_tenant_db()`
- Corrigir F2-G1/F3-G1: adicionar `AND company_id = :company_id` na query de `job_screening_questions`
- Adicionar "sourcing" e "cv_screening" ao `_FAIRNESS_DOMAINS` em `c3b_layer.py`
- Corrigir PATH A em `triggers.py` para passar por `CommunicationService.validate_can_send()`
- Chamar `BiasAuditService.audit_ranking_results()` automaticamente após cada `search_candidates` (atualmente existe mas nunca é chamado no flow conversacional)
- Bloquear `LIA_DISABLE_C3B=1` em produção via checagem no startup ou remover a feature flag

### Quick Wins

1. **Adicionar "sourcing" e "cv_screening" ao `_FAIRNESS_DOMAINS`** — 2 strings em `c3b_layer.py:17`. Imediatamente aplica PII strip + FairnessGuard aos flows de maior volume de dados sensíveis.
2. **Corrigir F2-G1**: adicionar `AND jq.company_id = :company_id` em `wsi_interview_graph.py:350–362`. Uma linha. Elimina cross-tenant exposure de perguntas WSI.
3. **Forçar `LIA_DISABLE_C3B`=False em produção** via validação em `main.py` startup — lançar `RuntimeError` se a variável está habilitada em ambiente `ENV=production`.

### Investimentos Estruturais

1. **Auditoria completa de tenant isolation** — Varrer todas as queries SQLAlchemy no codebase verificando que `company_id` está declarado como coluna não-nullable com index, e que todas as queries filtram por ele via RLS ou `WHERE` explícito. Gerar relatório de cobertura. Estimativa: 1 semana.
2. **Integração BiasAuditService no loop de busca** — Chamar `audit_ranking_results()` automaticamente após `search_candidates` e `rank_candidates`, persistindo snapshot para histórico e alertando se AIR < 0.80. Requer ~2 semanas de integração + testes.

---

## DIMENSÃO 6 — RESILIÊNCIA E OBSERVABILIDADE

**Score Atual: 3/5**  
**Score Alvo: 4/5**

### Evidências (código)

- `app/shared/resilience/circuit_breaker.py` — CircuitBreaker CLOSED/OPEN/HALF_OPEN, `failure_threshold=5`, `recovery_timeout=30s`, `success_threshold=2`, `timeout=10s`, notificação Bell+Teams com Redis dedup 1h, admin API `/api/v1/admin/circuit-breakers`
- `app/shared/resilience/dlq_service.py` — DLQ Redis com TTL 7d, cap 1000/queue, admin endpoints inspect/requeue/clear
- `app/core/sentry.py` — FastAPI/Starlette, PII scrub via `_before_send`, `send_default_pii=False`, fail-safe
- `app/core/logging_config.py` — JSON estruturado em prod: `timestamp, level, logger, message, request_id, user_id, exception?, data?`
- `app/core/logging_middleware.py` — `request_id, method, path, status_code, duration_ms, company_id, user_id, tier`
- `app/api/v1/audit_timeline.py` — `GET /api/v1/audit/executions/{id}/timeline` — step-by-step reasoning: llm_call, tool_call, node_transition com model, tokens, latency, previews
- `app/api/v1/wsi_observability.py` — Observabilidade específica para WSI
- `app/domains/ai/services/model_drift_service.py` — 4 triggers drift, comparação 7d vs 7d baseline, alertas
- `docker-compose.yml` — Flower `mher/flower:2.0` na porta 5555 para Celery monitoring
- `app/config/langsmith.py` — LangSmith tracing opcional via `@langsmith.traceable` com fallback `ImportError`
- **Ausências confirmadas**: Zero arquivos com `opentelemetry` import, zero com `prometheus_client` (removido em Task #138), zero com `structlog`
- `app/orchestrator/state_manager.py` — WARNING `LIA-M05` em prod se Redis ausente — estado volátil por worker

### Justificativa do Score

A resiliência está bem endereçada na camada de infraestrutura: circuit breakers em 5+ integrações externas com notificação automática, DLQ com retry com backoff exponencial (60/120/240s para webhooks), timeouts declarados para cada tipo de operação (LLM 30s, Redis 0.5s, WebSocket 3h), e Celery com 5 priority queues garantindo que urgências de sourcing não bloqueiam comunicações.

A observabilidade tem uma lacuna significativa: com Prometheus removido em Task #138 sem substituto declarado, não há métricas de série temporal para latência de agente, distribuição de tokens por domínio, ou taxa de hit por tier do CascadedRouter. O LangSmith é opcional e pode estar desabilitado por ausência de `LANGSMITH_API_KEY`. O `audit_timeline.py` fornece rastreabilidade por execução mas não agregados operacionais. O `model_drift_service.py` detecta drift mas não tem alertas configurados — outputs vão para logs apenas.

O problema operacional mais sério é o StateManager sem Redis em produção (`LIA-M05`): se Redis cair, o `StateManager` usa dict in-memory por worker, quebrando a consistência de estado conversacional para sessões que alternam entre workers (normal em produção com múltiplos workers Gunicorn/Uvicorn).

### Gap Analysis

Para atingir score 4:
- Implementar stack de métricas: OpenTelemetry (traces) + Prometheus/StatsD (métricas) para substituir o removido Prometheus, com dashboards Grafana por domínio de agente
- Configurar `LangSmith` como obrigatório em produção (não opcional) para tracing end-to-end de execuções de agente
- Adicionar alertas automáticos para drift detections: `ModelDriftService` deve chamar `notification_service` quando detecta `alert_level="warning"` ou `"critical"`
- Tornar `StateManager` + Redis obrigatório em produção (já existe o warning `LIA-M05` — transformar em `RuntimeError`)

### Quick Wins

1. **Ativar alertas de drift** — `model_drift_service.py`: quando `drift_status.alert_level != "ok"`, chamar `notification_service.send_system_alert()` (já existe em `circuit_breaker.py`). 10 linhas.
2. **Escalar LangSmith para obrigatório** — Adicionar `LANGSMITH_API_KEY` à lista de variáveis obrigatórias em `config.py` para `ENV=production`. Sem tracing, debugging de problemas de agente em produção é muito mais custoso.
3. **Adicionar `/metrics` endpoint** — Instrumentar com OpenTelemetry básico as 5 operações mais críticas: CascadedRouter.route(), WSIInterviewGraph.start(), create_react_agent invocation, tool dispatch, circuit breaker state changes.

### Investimentos Estruturais

1. **Stack de observabilidade completa** — Implementar OpenTelemetry SDK Python com exportação para Jaeger/Tempo (traces) e Prometheus (métricas), com dashboard Grafana com alertas por SLO: P95 latência por agente, taxa de erro por tool, custo de tokens por tenant/dia. Estimativa: 3–4 semanas.
2. **Chaos engineering básico** — Implementar testes de resiliência que validam comportamento do sistema quando Redis cai, PostgreSQL fica lento (>5s), ou Anthropic API retorna 429. Garante que circuit breakers e fallbacks funcionam como documentado.

---

## RADAR CHART (Descritivo)

| Dimensão | Atual | Alvo | Gap |
|---|---|---|---|
| D1 — Agência | 3.0 | 4.0 | -1.0 |
| D2 — Orquestração | 4.0 | 5.0 | -1.0 |
| D3 — Profundidade de Inteligência | 2.5 | 4.0 | -1.5 |
| D4 — Orquestração de Tools | 3.5 | 4.0 | -0.5 |
| D5 — Integração Transversal | 3.5 | 5.0 | -1.5 |
| D6 — Resiliência & Observabilidade | 3.0 | 4.0 | -1.0 |

```
Scores Atuais vs Alvo (escala 1–5):

D1 Agência           ████████████░░░░░░░░  3.0/5   Alvo: ████████████████░░░░  4.0
D2 Orquestração      ████████████████░░░░  4.0/5   Alvo: ████████████████████  5.0
D3 Inteligência      ██████████░░░░░░░░░░  2.5/5   Alvo: ████████████████░░░░  4.0
D4 Tools             ██████████████░░░░░░  3.5/5   Alvo: ████████████████░░░░  4.0
D5 Compliance        ██████████████░░░░░░  3.5/5   Alvo: ████████████████████  5.0
D6 Resiliência       ████████████░░░░░░░░  3.0/5   Alvo: ████████████████░░░░  4.0

Legenda: cada █ = 0.25 pontos
```

---

## CLASSIFICAÇÃO FINAL

**Média atual: 3.2/5**  
**Categoria: Agente Funcional com Supervisão**

**Justificativa:**

O sistema LIA supera claramente a categoria "Chatbot Glorificado" (1–2/5): há execução real de tools, persistência de estado multi-turn, HITL implementado como interrupção de grafo, e múltiplos sub-agentes especializados com handoff real. Também supera "Assistente com Potencial" (2–3/5) pois tem orquestração sofisticada (CascadedRouter 8-tier), scoring determinístico auditável, e infraestrutura de compliance enterprise.

O que impede classificação como "Agente Maduro" (4–5/5) é a lacuna entre arquitetura declarada e execução real. Em produção, os flows mais críticos têm falhas estruturais: comunicação via chat não envia emails reais, agendamento não registra `company_id`, HITL fail-open permite triagem sem revisão humana. O dashboard serve mock data. A inteligência preditiva usa pesos hardcoded sem dado de mercado. Essas não são limitações de roadmap — são bugs em produção que comprometem a proposta de valor core do produto.

A boa notícia: a arquitetura de base é correta. Os gaps prioritários identificados podem ser corrigidos em 2–4 semanas de engenharia focada, elevando o score para ~4.0/5.

---

## BENCHMARK vs MERCADO

| Dimensão | LIA (atual) | Eightfold AI | Paradox (Olivia) | LangChain Chatbot Genérico |
|---|---|---|---|---|
| D1 — Agência | 3.0 | 4.5 | 3.5 | 1.5 |
| D2 — Orquestração | 4.0 | 4.5 | 3.0 | 1.0 |
| D3 — Inteligência | 2.5 | 5.0 | 3.0 | 2.0 |
| D4 — Tools | 3.5 | 4.0 | 3.5 | 2.0 |
| D5 — Compliance | 3.5 | 3.5 | 2.5 | 0.5 |
| D6 — Resiliência | 3.0 | 4.5 | 4.0 | 1.5 |
| **Média** | **3.2** | **4.3** | **3.3** | **1.4** |

**Eightfold AI** é o benchmark de maturidade máxima: modelos proprietários treinados em bilhões de pontos de dados de carreira, taxonomy própria de skills, loops de feedback online com dados de hiring de milhares de empresas, e infraestrutura ML com modelos em produção (não apenas prompts LLM). A lacuna maior para o LIA está em D3 (Inteligência): Eightfold tem modelos treinados; LIA tem heurísticas ponderadas.

**Paradox (Olivia)** é o benchmark mais relevante para comparação direta — plataforma conversacional de recrutamento construída sobre LLM. O LIA supera o Paradox em orquestração (D2: 4.0 vs 3.0) e empata em tools (D4) e agência (D1). A vantagem do Paradox é resiliência e observabilidade (4.0 vs 3.0) — Paradox tem anos de operação em escala. A desvantagem do Paradox é compliance (2.5 vs 3.5) — LIA tem implementação LGPD mais robusta que qualquer produto US-first.

**LangChain Chatbot Genérico** serve como baseline: sem orquestração sofisticada, sem compliance, sem multi-agente real. O LIA está claramente acima desta baseline em todas as dimensões.

**Diferencial competitivo real do LIA**: compliance LGPD/BCB 498/SOX genuíno (não cosmético), scoring WSI 100% determinístico + auditável (diferencial vs Eightfold e Paradox que usam LLM judge), e orquestração CascadedRouter 8-tier que equilibra custo/performance melhor que implementações ingênuas.

---

## ROADMAP DE MATURIDADE

### Fase 1 — Quick Wins (0–30 dias) | Meta: 3.2 → 3.8/5

Foco: eliminar gaps críticos que comprometem funcionamento em produção.

1. **[D4/D1] Corrigir communication_tools.py:104,195** — Conectar `send_email()` e `send_whatsapp()` ao `CommunicationDispatcher`. Elimina F4-G1. **2 dias.**
2. **[D5] Corrigir query_tools.py:79–82** — Substituir `hasattr(Candidate,'company_id')` por check explícito com fallback de segurança. Elimina F1-G1. **1 dia.**
3. **[D5] Corrigir wsi_interview_graph.py:350–362** — Adicionar `company_id` filter em `job_screening_questions`. Elimina F2-G1/F3-G1. **1 dia.**
4. **[D1] Transformar HITL fail-open em fail-closed** — `wsi_interview_graph.py:1057`. **1 dia.**
5. **[D5] Adicionar "sourcing" e "cv_screening" ao `_FAIRNESS_DOMAINS`** — `c3b_layer.py:17`. **1 hora.**
6. **[D3] Corrigir dashboard_data.py** — Substituir mock data por services reais. **3–5 dias.**
7. **[D1] Registrar `interview_scheduling` no AgentRegistry** — Evita fallback silencioso para TalentReActAgent. **2 horas.**
8. **[D3] Context injection para CommunicationReActAgent e AnalyticsReActAgent** — Adicionar REASONING_PROMPT com memory_summary. **2–3 dias cada.**
9. **[D6] Ativar alertas de drift** — ModelDriftService → notification_service quando `alert_level != "ok"`. **2 horas.**
10. **[D5] Bloquear `LIA_DISABLE_C3B=1` em produção** — RuntimeError no startup. **1 hora.**

---

### Fase 2 — Investimentos Médios (30–90 dias) | Meta: 3.8 → 4.3/5

Foco: fechar loops de inteligência, consolidar arquitetura, melhorar cobertura de compliance.

1. **[D2] Consolidar os 3 registries** — Declarar AgentRegistry como canônico, deprecar ReactAgentRegistry. 2–3 semanas.
2. **[D1/D4] Unificar WizardReActAgent e JobWizardGraph** — Eliminar implementações paralelas. 2–3 semanas.
3. **[D5] Auditoria completa de tenant isolation** — Varrer todas as queries por `company_id` com cobertura de testes. 1 semana.
4. **[D5] Integrar BiasAuditService no loop de busca** — Chamar automaticamente após `search_candidates`. 2 semanas.
5. **[D6] LangSmith obrigatório em produção** — Adicionar à lista de variáveis required. 2 dias + rollout.
6. **[D4] Enforcement de `allowed_agents` no ToolExecutor** — Guardrail de runtime. 1 semana.
7. **[D3] Fechar loop RAGAS** — Scores < threshold disparam notificação operacional. 1 semana.
8. **[D2] Migrar APScheduler → Celery Beat** — Habilita horizontal scaling para automações. 2–3 semanas.
9. **[D6] Adicionar `/metrics` OpenTelemetry básico** — 5 operações críticas instrumentadas. 1 semana.
10. **[D4] Corrigir `generate_offer` e `get_pipeline_summary`** — Implementações reais com DB write e dados reais. 1 semana cada.

---

### Fase 3 — Investimentos Estruturais (90–180 dias) | Meta: 4.3 → 4.8/5

Foco: inteligência adaptativa, observabilidade full-stack, arquitetura enterprise.

1. **[D3] Inteligência preditiva com dados reais** — Substituir `market_factor=1.0` por feeds de mercado dinâmicos. `time_to_fill` benchmark por setor/localização/senioridade.
2. **[D3] Loop de feedback fechado para prompts** — RAGAS < threshold por N dias → task automática de revisão de prompt com contexto. Ou: A/B test automático de variantes de prompt baseado em scores RAGAS.
3. **[D6] Stack de observabilidade completa** — OpenTelemetry + Jaeger/Tempo + Prometheus + Grafana com alertas por SLO. P95 latência por agente, custo por tenant/dia, taxa de erro por tool.
4. **[D3] Modelo de matching além de pgvector** — Explorar fine-tuning de embedding model com dados de candidatos aceitos/rejeitados para melhorar similaridade semântica de busca. Requer coleta de ground truth.
5. **[D5] Conformidade EU AI Act Art. 9** — High-risk AI system documentation: ficha técnica por agente com accuracy, bias metrics, training data documentation. Relevante para expansão Europa.
6. **[D6] Chaos engineering** — Suite de testes de resiliência: Redis down, PG slow, Anthropic 429. Valida que circuit breakers e fallbacks funcionam como documentado.
7. **[D2] Observabilidade de routing** — Dashboard de distribuição de queries por tier do CascadedRouter, custo por tier, cache hit rate por domínio. Habilita otimização contínua de routing.

---

## APÊNDICE — GLOSSÁRIO DE SCORES

| Score | Categoria | Descrição |
|---|---|---|
| 1 | Chatbot Stateless | Sem memória entre turnos. Input → LLM → Output. Sem tools reais. |
| 2 | Assistente Context-Aware | Memória de sessão. Alguns tools básicos. Sem autonomia de decisão. |
| 3 | Semi-Autônomo com Tools | ReAct loop real. Tools com I/O externo. HITL pontual. Estado persistente. |
| 4 | Autônomo com Supervisão | Multi-agente. Loops de feedback ativos. Observabilidade. Compliance integrado. |
| 5 | Totalmente Autônomo com Aprendizado | Modelos treinados. Adaptação online. Loops fechados de qualidade. Predições com dado real de mercado. |

---

*Diagnóstico baseado em: PLATFORM_MAP.md (1445 linhas), FLOW_TRACES.md (1011 linhas), PROMPT_AUDIT.md (572 linhas), inspeção direta de 15+ arquivos de código-fonte. Data: 2026-04-13.*
