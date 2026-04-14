# MATURITY_ASSESSMENT.md — Diagnóstico de Maturidade Agêntica
**Protocolo:** P04
**Data:** 2026-04-14
**Depende de:** P01 (PLATFORM_MAP), P02 (FLOW_TRACES), P03 (PROMPT_AUDIT)
**Alimenta:** P07, P21

---

## RESUMO EXECUTIVO

**Score médio:** 2.7/5
**Classificação:** Assistente com potencial — infraestrutura agêntica presente mas execução end-to-end sistematicamente quebrada

| Dimensão | Score Atual | Score Alvo | Gap |
|---|---|---|---|
| D1 Agência | 2.5/5 | 4.0/5 | −1.5 |
| D2 Orquestração | 3.5/5 | 4.5/5 | −1.0 |
| D3 Intelligence Depth | 2.5/5 | 4.0/5 | −1.5 |
| D4 Tool Orchestration | 2.5/5 | 4.0/5 | −1.5 |
| D5 Cross-cutting | 3.0/5 | 4.5/5 | −1.5 |
| D6 Resiliência | 2.0/5 | 4.0/5 | −2.0 |

**Nota metodológica:** Os scores refletem comportamento end-to-end observável via FLOW_TRACES — não intenção arquitetural de PLATFORM_MAP. Um sistema que tem LangGraph mas não persiste resultados recebe score inferior a um que persiste sem LangGraph. A regra central é: se o fluxo é BLOQUEADO ou PARCIALMENTE FUNCIONAL com falhas críticas, o score da dimensão é penalizado proporcionalmente à severidade dos gaps.

---

## DIMENSÃO 1 — NÍVEL DE AGÊNCIA
**Score Atual: 2.5/5**
**Score Alvo: 4.0/5**

### Evidências do Código

- `app/orchestrator/agentic_loop.py:20` — `AgenticLoop` implementa ReAct puro (LLM → Tool → Result → LLM) com `MAX_TOOL_ITERATIONS = int(os.getenv("LIA_MAX_TOOL_ITERATIONS", "3"))`. Limite padrão conservador de 3 iterações.
- `app/orchestrator/cascaded_router.py` — `AUTONOMOUS_REACT_MAX_STEPS` (env var, padrão 10) — AutonomousReActAgent com 40+ tools mas prompt score de 14/33 (PROMPT_AUDIT, pior agente).
- `app/domains/interview_scheduling/agents/interview_graph.py:42` — `MAX_ITERATIONS = 8` no InterviewGraph (StateGraph determinístico) — loop controlado para coleta de campos.
- `app/domains/job_management/agents/wizard_react_agent.py` — `max_iterations: 5` — agente com melhor prompt do sistema (27/33) mas bloqueado por `WSManager singleton em-processo` (C-01) que impede panel_update de chegar a outros workers Uvicorn.
- FLOW 5 (Agendamento): `_check_availability_node` → `GET /v1/users/scheduling/availability` → ROTA NÃO EXISTE no Rails; `_execute_node` → `POST /v1/users/calendar_events` → ROTA NÃO EXISTE. Fluxo BLOQUEADO (F5-G1, gap C-11).
- FLOW 4: `communication_tools.py` retorna `mock success dict` sem chamar `CommunicationDispatcher` (C-09). Agente conversa sobre enviar email mas nunca envia — comportamento fantasma.
- FLOW 3: `complete_session` apenas marca Redis como "completed" sem disparar scoring (C-08); `WSISession` model ausente lança `ImportError` silenciado (C-07). Fluxo de avaliação assíncrona estruturalmente quebrado.
- `app/orchestrator/agentic_loop.py` — `HubPlanner` e `HubExecutor` implementados para decomposição multi-intent, mas `USE_SUPERVISOR = False` hardcoded (`hub/orchestrator.py:18`) — supervisor LangGraph desabilitado em produção.
- HITL implementado em 3 fluxos críticos (`interrupt_before` em WizardGraph, PipelineTransitionAgent, WSI) via `app/domains/cv_screening/services/hitl_service.py` — **este é o ponto mais maduro da dimensão de agência**.

### Justificativa do Score

A LIA possui a arquitetura técnica de um agente: LangGraph `create_react_agent` em 13 arquivos, `StateGraph` em 4 fluxos, `AgenticLoop` próprio, `HubPlanner/HubExecutor` para decomposição multi-intent. Em termos de intenção arquitetural, isso corresponderia a um score 3.5-4.0/5. Contudo, o comportamento end-to-end observado em FLOW_TRACES conta história diferente: de 8 fluxos, 7 são PARCIALMENTE FUNCIONAL e 1 é BLOQUEADO. O fluxo de agendamento (F5) está completamente bloqueado por 4 rotas Rails ausentes — o agente planeja, executa nós, faz parsing, mas nunca agenda nada. A comunicação via agente (Path A, F4) retorna mocks silenciosos há meses. A avaliação assíncrona (F3) tem o modelo de persistência ausente.

O nível de agência real é limitado por três padrões sistêmicos: (1) outputs de agentes não persistem em banco de dados permanente — resultados WSI são perdidos ao restart, sessões in-memory não sobrevivem a falhas; (2) ações críticas dos agentes (envio de email, agendamento) são simuladas mas não executadas end-to-end; (3) o agente autônomo (Tier 6), que deveria cobrir casos edge, possui o pior prompt do sistema (14/33) com 40+ tools e zero guidance. O HITL funcional em 3 fluxos eleva parcialmente o score — é evidência de autonomia controlada genuína onde funciona.

### Gap Analysis

- **Gap principal**: Tool stubs não conectados ao real dispatch. O agente "age" mas as consequências reais não ocorrem.
- Agência real requer que ações sejam consequentes: `send_email` deve enviar, `schedule_interview` deve criar evento de calendário.
- Supervisor LangGraph (`USE_SUPERVISOR = False`) hardcoded bloqueia decomposição autônoma de tarefas complexas.
- Limite de iterações conservador (3 por padrão no AgenticLoop) limita comportamentos multi-step.
- AutonomousReActAgent sem guidance de tool selection entre 40+ opções gera comportamento não-determinístico.

### Quick Wins (dias/semanas)
1. Conectar `communication_tools.py` ao `CommunicationDispatcher` real (C-09) — remover mocks de `send_email`/`send_whatsapp`. Estimativa: 2-3 dias.
2. Aumentar `MAX_TOOL_ITERATIONS` default de 3 para 8 via env var já existente — sem mudança de código.
3. Reescrever prompt do `AutonomousReActAgent` (P03 recomenda reescrita total) — priority matrix de tools + persona LIA + fairness obrigatório.

### Investimentos Estruturais (semanas/meses)
1. Criar 4 rotas Rails ausentes para scheduling (C-11): `GET /v1/users/scheduling/availability`, `/availability/multi`, `POST /v1/users/calendar_events`, `POST /v1/users/scheduling/links`. Estimativa: 1-2 semanas (Rails + testes).
2. Habilitar `USE_SUPERVISOR = True` com testes de regressão do HubPlanner/HubExecutor — 2-3 semanas.
3. Persistência real de resultados WSI em banco: criar modelo `WSISession`, persistir `wsi_final_score` em `Candidate` ou tabela dedicada (C-04, C-07).

---

## DIMENSÃO 2 — ORQUESTRAÇÃO
**Score Atual: 3.5/5**
**Score Alvo: 4.5/5**

### Evidências do Código

- `app/orchestrator/cascaded_router.py` — `CascadedRouter` com 8 tiers completos: MemoryResolver → LRU → Redis → VectorSemanticCache (pgvector, threshold=0.85) → FastRouter (regex/keyword) → LLMCascadeRouter (Gemini Flash → Claude Sonnet → Opus) → AutonomousReActAgent → clarification_needed. **Esta é a arquitetura de orquestração mais sofisticada encontrada.**
- `app/orchestrator/llm_cascade.py` — `LLMCascadeRouter` com 3 modelos em cascata, thresholds de confiança configuráveis (Flash≥0.80, Sonnet≥0.70, Opus≥0.60), multi-model per tenant via `preferred_model`.
- FLOW 1 verificado end-to-end: `FastRouter` casa `r"buscar?\s+\w*\s*candidato"` → `domain="sourcing"` → `SourcingSearchAgent` → `search_candidates` → resultado retornado. Pipeline de roteamento funcional para queries simples.
- `app/orchestrator/fast_router.py` — 20+ domínios com patterns regex para ~80% das queries. Tier 4 resolve a maioria sem chamada LLM — design de custo inteligente.
- A/B testing no router: `cascade_router_system_prompt.yaml`, seleção por hash de `user_id` — experimentação integrada ao router (pouco comum mesmo em sistemas maduros).
- `hub/orchestrator.py` — `HubPlanner.create_plan()` + `HubExecutor.execute()` para multi-intent decomposition. Implementação presente mas `USE_SUPERVISOR = False` hardcoded.
- FLOW 6: `CostLadderRouter` com 5 tiers próprios (reference → cache → regex → semantic → LLM), paralelo ao `CascadedRouter` — dois sistemas de roteamento independentes sem sincronização (F6-G1, gap A-15).
- `app/shared/websocket/ws_manager.py` — `WSManager` singleton em-processo. Em deployment com múltiplos workers Uvicorn, `panel_update` de um agente não chega a clientes conectados em outros workers (C-01). Impacta F1, F2, F3, F5, F7, F8 — virtualmente todos os fluxos que usam WebSocket.
- `app/orchestrator/context_adapter.py` — `UniversalContext` com `session_id`, `user_id`, `company_id`, `page_context` — contexto compartilhado bem estruturado.
- `ROUTING_PROMPT` em `llm_cascade.py` explicitamente minimalista ("otimizado para Haiku — custo mínimo") sem guardrails de segurança (PROMPT_AUDIT, Gap 6).

### Justificativa do Score

O orquestrador é a dimensão mais madura do sistema. O `CascadedRouter` de 8 tiers com fallback gracioso em cada nível representa design sofisticado que não é visto em ferramentas como Paradox Olivia (roteamento simples por intent classifier) nem em templates LangChain básicos. O rastreamento de stats por tier (memory_hits, redis_hits, vector_hits etc.) indica maturidade operacional. A cascata multi-LLM com fallback de confiança é uma pattern avançada.

O que penaliza o score são dois gaps sistêmicos de alta severidade: (1) O `WSManager` singleton impede que o orquestrador entregue resultados em deployments com múltiplos workers — isso afeta todos os 8 fluxos. Em produção real com mais de 1 worker Uvicorn, a orquestração produz resultados que ninguém vê. (2) A existência de dois roteadores paralelos (`CascadedRouter` para path WS/agents e `CostLadderRouter` para path Hub) sem sincronização cria dual-memory divergence (A-15) e inconsistências de roteamento para o mesmo usuário dependendo do ponto de entrada.

### Gap Analysis

- `WSManager` singleton em-processo é o gap de maior impacto para orquestração. Solução: pub/sub via Redis (já disponível na stack) para broadcast de eventos de WebSocket entre workers.
- Dois sistemas de roteamento paralelos não orquestrados entre si — unificação ou sincronização de estado de sessão entre `CascadedRouter` e `CostLadderRouter`.
- `USE_SUPERVISOR = False` hardcoded impede que o `HubPlanner`/`HubExecutor` funcione em produção.
- Timeout global de 120s (`LLM_TIMEOUT_SECONDS`) mas sem timeout específico no loop ReAct para o sourcing agent (M-01).

### Quick Wins (dias/semanas)
1. Substituir `WSManager` singleton por Redis pub/sub para broadcast de WS — soluciona C-01 que afeta todos os 8 fluxos. O Redis já está na stack. Estimativa: 1 semana com testes.
2. Adicionar timeout explícito no `agent.process()` do `SourcingReActAgent` (M-01) — 1 dia.
3. Documentar e unificar o mapeamento entre `CostLadderRouter` e `CascadedRouter` — padronizar qual usar por ponto de entrada.

### Investimentos Estruturais (semanas/meses)
1. Unificação dos dois roteadores em arquitetura única com estado compartilhado — 4-6 semanas.
2. Habilitar `USE_SUPERVISOR = True` com testes end-to-end do `HubPlanner` multi-intent — 2-3 semanas.
3. Prometheus/OpenMetrics exportado de novo (Task #138 removeu, `cascaded_router.py:_get_metrics()` retorna `None, None, None`) — 1 semana para reintegração.

---

## DIMENSÃO 3 — INTELLIGENCE DEPTH
**Score Atual: 2.5/5**
**Score Alvo: 4.0/5**

### Evidências do Código

- `app/domains/ai/services/ragas_evaluation_service.py` — RAGAS implementado com 4 métricas (faithfulness, answer_relevancy, context_precision, context_recall), threshold 0.70, batch Celery diário 03h UTC. **Presença de RAGAS é diferenciador positivo**. Contudo é **passivo** — `fail-safe: falha de avaliação NÃO afeta operação do agente` (PLATFORM_MAP §10.4).
- `app/domains/ai/services/model_drift_service.py` — drift detection com 4 triggers (score_drift, approval_drift, cost_drift, latency_drift) em janela deslizante de 7 dias. Presente mas não conectado a ações automáticas de correção.
- `app/shared/learning/learning_loop_service.py` — captura 7 tipos de padrão (SALARY_PREFERENCE, SKILL_PREFERENCE etc.) com thresholds de confiança (≥20 amostras para high). Silencioso, sem feedback explícito. **Feedback loop real mas sem injeção nos prompts**.
- `app/domains/analytics/services/recruiter_personalization_service.py` — `PersonalizationContext` construída com dados de recruiter. Porém `SystemPromptBuilder.build()` não recebe `recruiter_context` — **PersonalizationContext construída mas nunca injetada** (F8-G3, M-16).
- PROMPT_AUDIT score médio de 20.5/33 (62%). Apenas 1 de 13 agentes satisfatório (≥26/33). 5 agentes com prompt "problemático" (14-19). 1 com prompt "crítico" (14/33).
- Padrão CoT (Chain-of-Thought) presente em AnalyticsReActAgent, KanbanInsightAgent, InterviewGraph, PipelineAgent, ATSIntegrationAgent (PROMPT_AUDIT) — não universal.
- `app/domains/digital_twin/domain.py` — Digital Twin via RAG few-shot (clone de raciocínio SME). Status: `[⚠] profundidade do RAG few-shot não verificada` (PLATFORM_MAP §2.9).
- Few-shot exemplos em KanbanInsightAgent (8 cenários), ATSIntegrationAgent (3 cenários), AnalyticsReActAgent (8 cenários) — presente nos melhores agentes mas ausente nos piores.
- Zero modelos ML treinados: WSI scoring é determinístico (Bloom/Dreyfus rule-based), market benchmark é SerpAPI + LLM estimate, time-to-fill é heurístico (PLATFORM_MAP §9.7). **Ausência total de ML propriamente dito**.
- `app/prompts/templates.py` + `PromptVersionRegistry` + A/B experiments (`cascade_router_system_prompt.yaml`) — infraestrutura de versionamento e experimentação de prompts presente.
- `app/api/v1/finetuning_export.py` — export de dados rotulados para fine-tuning. Potencial mas não realizado.

### Justificativa do Score

A plataforma demonstra consciência de intelligence depth: RAGAS para avaliação de qualidade, feedback loop silencioso capturando padrões comportamentais, Digital Twin para clone de raciocínio especialista, drift detection para monitorar degradação. São capacidades que a maioria dos sistemas de nível "chatbot glorificado" não possui.

Entretanto, nenhuma dessas capacidades fecha o loop de melhoria automática. O RAGAS mede mas não age — resultados abaixo de 0.70 são sinalizados mas não disparam reescrita de prompt, ajuste de temperatura ou roteamento para modelo mais capaz. O `LearningLoopService` captura padrões com rigor estatístico mas a `PersonalizationContext` resultante nunca chega ao `SystemPromptBuilder`. O fine-tuning export existe mas não há evidência de que algum fine-tuning foi realizado. O drift detector identifica variações mas não tem ação automática associada.

Em termos de qualidade de raciocínio individual, o score médio de 62% nos prompts significa que a maioria dos agentes raciocina adequadamente mas com lacunas específicas: sem CoT padronizado, sem context management entre turnos, sem graceful degradation formalizado, sem awareness de plataforma (multi-tenancy, budget, LLM Factory). O agente autônomo — que por definição precisa de raciocínio mais profundo por cobrir casos que especialistas não conseguem — tem o raciocínio mais raso do sistema (14/33, sem fairness, sem persona, sem árvore de decisão para 40+ tools).

### Gap Analysis

- **Gap crítico**: O loop de inteligência adaptativa está quebrado. RAGAS avalia → nada acontece. Learning loop captura → PersonalizationContext não é injetada. Drift detection alerta → sem ação automática.
- Context management ausente em 7 dos 13 agentes (sem memória cross-turn, sem compactação, sem priorização de tokens).
- Ausência de self-correction: nenhum agente detecta quando sua própria resposta pode estar errada e re-raciocina.
- Tenant Isolation Explícita ausente em 100% dos prompts — a LLM não recebe instrução de recusar operações sem tenant válido.
- 7 agentes com dois prompts quase duplicados — ~3.000 linhas de debt de prompt que fragmentam comportamento.

### Quick Wins (dias/semanas)
1. Injetar `PersonalizationContext` no `SystemPromptBuilder.build()` — conexão entre serviço existente e builder existente (M-16). Estimativa: 1-2 dias de código mais testes.
2. Adicionar bloco padrão de `Tenant Isolation` em todos os 13 prompts (PROMPT_AUDIT Gap 1) — 5-7 dias de reescrita parcial.
3. Adicionar bloco padrão de `Budget/Token Awareness` nos prompts (PROMPT_AUDIT Gap 2) — conectar `tokens_remaining` ao sistema de prompts.

### Investimentos Estruturais (semanas/meses)
1. Fechar loop RAGAS → ação: quando score cai abaixo de threshold, disparar Celery task que (a) aumenta temperatura, (b) eleva modelo no cascade, ou (c) cria alerta para revisão humana. 3-4 semanas.
2. Eliminar duplicação de prompts: consolidar `*_SYSTEM_PROMPT` (legacy) + `*_DOMAIN_SPECIFIC` em prompt único por agente. Usar `SystemPromptBuilder` com versão controlada. 4-6 semanas.
3. Implementar context compaction padronizado: regra de prioridade universal de contexto nos prompts (PROMPT_AUDIT Gap 6) + TTL de histórico. 2-3 semanas.

---

## DIMENSÃO 4 — TOOL ORCHESTRATION
**Score Atual: 2.5/5**
**Score Alvo: 4.0/5**

### Evidências do Código

- `app/tools/registry.py` + `app/tools/tool_registry_metadata.yaml` — 83 arquivos com referências a `tool_registry`. `ToolDefinition` dataclass com schema dual (`to_claude_schema()` / `to_gemini_schema()`). YAML como fonte de verdade validado no startup — design maduro.
- `app/domains/agent_studio/custom_agent_runtime.py:22` — Pool de 40+ tools para AutonomousReActAgent; 15 ferramentas perigosas bloqueadas via `_RESTRICTED_TOOLS` (frozenset). Controle de acesso a tools implementado.
- FLOW 1 integração verificada: `SourcingSearchAgent._get_tools()` → `ToolDefinition` registradas → `tool_definition_to_langchain_tool()` → `create_react_agent` — cadeia completa funcionando para sourcing.
- FLOW 2: `WSIInterviewGraph` com `StateGraph` determinístico — `load_context → generate_question → validate → score → advance → feedback`. Orquestração de tools por nó funcional. `AuditService.log_decision` por bloco + decisão final.
- FLOW 4: `communication_tools.py` — `send_email()` e `send_whatsapp()` retornam `mock success dict` sem chamar `CommunicationDispatcher` real (C-09, A-09). **A tool mais usada no sistema não despacha nada**.
- FLOW 3: `communication_tools.py:~100` também identificado como mock para WSI async — padrão sistêmico, não falha isolada.
- `app/api/v1/agent_chat_ws.py` — `TimedToolNode` com default 15s por tool com overrides — timeout de tool implementado.
- `app/domains/cv_screening/services/hitl_service.py` — HITL via `interrupt_before` LangGraph — aprovação humana integrada ao loop de tools como nó de workflow.
- `app/domains/sourcing/agents/sourcing_react_agent.py` — sub-roteamento Z2 por sub-agente (`sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement`) — especialização de tools por intenção dentro de domínio.
- Tool isolation: FLOW 1 verifica que `search_candidates` usa `AsyncSessionLocal` direto (AI Layer DB), não chama Rails — corretamente isolado. Porém candidato pode aparecer sem gate LGPD (C-02) e sem audit trail (A-02).
- `app/tools/tool_registry_metadata.yaml` — escopos `TALENT_FUNNEL | JOB_TABLE | IN_JOB | GLOBAL` — contexto de disponibilidade de tool implementado.

### Justificativa do Score

O ecossistema de tools da LIA é estruturalmente sólido: registry com fonte de verdade em YAML, schemas duais para Claude/Gemini, scoping por contexto de página, controle de acesso por `_RESTRICTED_TOOLS`, timeout por tool, HITL integrado como nó de workflow. Esses são padrões que correspondem a sistemas de nível 3.5-4.0 em maturidade de tool orchestration.

O que derruba o score para 2.5 é um problema grave de integridade semântica: as tools mais críticas para o negócio — comunicação com candidatos — são stubs que retornam sucesso falso. Isso não é um bug menor; é uma falha que faz o agente acreditar que tomou ação quando não tomou. Em 8 meses de produto, um agente que "envia emails" sem enviar nada é um risco operacional e de confiança grave. Além disso, as tools de scheduling (check_availability, create_calendar_event) chamam endpoints Rails que não existem, bloqueando todo o fluxo F5.

A ausência de feedback loop de tools (sem retorno de `CommunicationService` para o agente após send, sem callback após `complete_session` no WSI async) impede que o agente ajuste seu comportamento baseado no resultado real de suas ações — característica central de agency.

### Gap Analysis

- **Mock tools em produção**: padrão de stub sem dispatch real precisa ser eliminado sistematicamente. Todos os tools de comunicação, scheduling e actions devem ser auditados para verificar se chamam serviços reais.
- Ausência de feedback loop de tools para o agente: agente não sabe se email foi entregue, se calendário foi criado.
- LGPD não verificada em `search_candidates` tool (C-02) — gate de consentimento ausente no path mais frequente.
- Audit trail ausente no path agent de busca (A-02) — `query_tools.py` não chama `AuditService`.

### Quick Wins (dias/semanas)
1. Reconectar `communication_tools.py` ao `CommunicationDispatcher` (C-09) — remover mocks. 2-3 dias.
2. Adicionar `ConsentCheckerService.check()` em `search_candidates` (C-02) — 1-2 dias + testes.
3. Adicionar `AuditService.log_decision()` em `query_tools.py` path agent (A-02) — 1 dia.

### Investimentos Estruturais (semanas/meses)
1. Auditoria completa de todos os tool stubs no sistema — criar test suite que verifica que cada tool registered realmente chama serviço externo ou DB. Estimativa: 2-3 semanas.
2. Implementar feedback loop de tool para agente: após `send_email`, receber status de delivery via webhook e retornar ao loop ReAct. 3-4 semanas.
3. Implementar tool calling com retry inteligente: se tool retorna erro, o agente decide se retry, escalona ou informa usuário. 2-3 semanas.

---

## DIMENSÃO 5 — CROSS-CUTTING INTEGRATION
**Score Atual: 3.0/5**
**Score Alvo: 4.5/5**

### Evidências do Código

- `app/shared/compliance/fairness_guard.py` — 3 camadas: (L1) regex compiladas para discriminação explícita em PT+EN que bloqueia queries; (L2) 40+ termos implícitos com soft warning; (L3) LLM semântico setor-aware. **Fairness de 3 camadas é diferenciador significativo**.
- `app/shared/compliance/c3b_layer.py` — pré/pós compliance: PII strip → FairnessGuard L3 para `_FAIRNESS_DOMAINS` + FactChecker + AuditService. **Nota crítica**: `sourcing` está excluído de `_FAIRNESS_DOMAINS` (FLOW_TRACES F1) — o domínio mais crítico para viés de recrutamento não passa por L3.
- FLOW 2: FairnessGuard aplicado em `validate_response` (resposta do candidato), PII masking antes de scoring, PROTECTED_CRITERIA excluídos do audit trail. **WSI é o fluxo com melhor integração cross-cutting**.
- FLOW 1: FairnessGuard aplicado no input do usuário, mas não nos resultados de ranking — WRF score sem fairness check pós-ranking (A-03). Candidatos podem ser apresentados em ordem discriminatória.
- `app/shared/compliance/audit_service.py` — 53 arquivos com referências. Loga company_id, agent_name, decision_type, criteria_used, criteria_ignored (PROTECTED_CRITERIA), score, confidence, human_review_required. Retenção: 730d scoring / 1825d messaging.
- `app/shared/pii_masking.py` — `PIIMaskingFilter` no root logger. `strip_pii_for_llm_prompt()` e `LangGraphReActBase._sanitize_messages_pii()` — 3 camadas de PII masking.
- `app/domains/lgpd/` — ConsentChecker, LGPDCleanup, DSR export, GranularConsent, DriftAlert — infraestrutura LGPD completa.
- FLOW 2: Falha silenciosa crítica — `except Exception: logger.warning() → prossegue` no `ConsentChecker` (C-06). O gate LGPD pode ser burlado por qualquer exception no serviço de consentimento.
- FLOW 4, Path A: `communication_tools.py` bypassa completamente `validate_can_send()` — candidatos com opt-out ou em quarentena poderiam receber mensagens se o tool não fosse mock (C-10, F4-G2).
- PROMPT_AUDIT Gap 1: zero prompts mencionam `company_id` como restrição obrigatória. Gap 2: zero prompts mencionam TenantBudget. Gap 3: zero prompts têm LLM Factory awareness. A LLM não recebe instrução de recusar operações de outro tenant.
- EU AI Act Art. 14 citado explicitamente apenas no PipelineAgent (PROMPT_AUDIT Gap 2 cross-cutting). Agentes de Automation, Kanban, Talent com impacto sobre candidatos não mencionam obrigação de supervisão humana.
- `app/api/v1/admin_bias_audit.py` + `admin_compliance_fairness.py` — UI admin para auditoria de viés presente.
- `app/domains/ai/services/ragas_evaluation_service.py` — avaliações RAGAS em 3 arquivos, retidas 90 dias — qualidade de respostas monitorada.

### Justificativa do Score

A LIA possui a estrutura de compliance mais sofisticada encontrada entre plataformas de recrutamento: FairnessGuard de 3 camadas, PII masking em 3 pontos, audit trail com PROTECTED_CRITERIA, ConsentChecker integrado ao WSI, portal LGPD para direito de acesso. Isso coloca o sistema bem acima de soluções como Paradox Olivia, que tipicamente não tem fairness guard integrado ao nível de tool.

O score é limitado a 3.0 por inconsistências graves na aplicação: (1) O gate mais crítico (ConsentChecker) tem falha silenciosa que pode ser burlada por qualquer exception não antecipada. (2) O domínio de sourcing — o ponto mais sensível para viés em recrutamento — está fora dos `_FAIRNESS_DOMAINS` do C3b layer. (3) Path A de comunicação bypassa validate_can_send. (4) Zero prompts LLM têm instrução de multi-tenancy obrigatório — a LLM pode raciocinar sobre dados de outros tenants sem saber que não deve. A integração cross-cutting é forte na arquitetura mas tem brechas sistemáticas na execução.

### Gap Analysis

- `sourcing` fora de `_FAIRNESS_DOMAINS` é o gap de maior risco regulatório — busca de candidatos sem L3 fairness semântica.
- ConsentChecker exception silenciosa (C-06) deve ser tornada bloqueante: falha no consent check deve resultar em abort, não em bypass.
- 100% dos prompts sem tenant isolation explícita — risco de LLM raciocinando cross-tenant.
- EU AI Act Art. 14 (supervisão humana) ausente em 12 de 13 agentes — risco de compliance EU.
- Resultados de ranking sem fairness check pós-ranking (A-03) — WRF score pode reproduzir e amplificar vieses históricos.

### Quick Wins (dias/semanas)
1. Adicionar `sourcing` aos `_FAIRNESS_DOMAINS` do C3b layer — 1-2 horas de mudança de config.
2. Tornar `ConsentChecker` exception bloqueante: transformar `except Exception: logger.warning() → prossegue` em `except Exception: raise ComplianceException("consent_check_failed")` (C-06) — 1 dia.
3. Adicionar bloco de Tenant Isolation em todos os 13 prompts (PROMPT_AUDIT Gap 1) — 5-7 dias.

### Investimentos Estruturais (semanas/meses)
1. Implementar fairness check pós-ranking nos resultados de `rank_candidates` (WRF) — adicionar `FairnessGuard.check_results(candidates)` depois do scoring (A-03). 2-3 semanas.
2. Audit trail em todos os paths de busca via agente — `query_tools.py` precisa chamar `AuditService` (A-02). 1-2 semanas.
3. Formalizar EU AI Act compliance: adicionar HITL obrigatório para todas as ações de alto impacto via `AutomationReActAgent` e `KanbanInsightAgent` (PROMPT_AUDIT Gap: EU AI Act apenas no PipelineAgent). 3-4 semanas.

---

## DIMENSÃO 6 — RESILIÊNCIA & OBSERVABILIDADE
**Score Atual: 2.0/5**
**Score Alvo: 4.0/5**

### Evidências do Código

- `app/shared/tracing.py` — OpenTelemetry com export OTLP (quando `OTEL_EXPORTER_OTLP_ENDPOINT` definido) + fallback `LightweightTracer` interno. 2 arquivos com referências a `opentelemetry`/`OTEL`. Coverage de spans: CascadedRouter, RAG pipeline, HITL, Celery, ReAct loop. **Boa cobertura de spans, mas configuração de export opcional (não obrigatória)**.
- `app/shared/structured_logging.py` — JSON estruturado com PII masking integrado.
- Sentry: `SENTRY_DSN` configurado em AI Layer + Frontend (`sentry.client.config.ts`, `sentry.server.config.ts`). **Presente mas não confirmado em uso ativo**.
- `app/orchestrator/cascaded_router.py` — `_get_metrics()` retorna `None, None, None` — Prometheus removido em Task #138. **Métricas de roteamento não exportadas**. Hit rates por tier, latências, confidence scores — tudo perdido.
- `app/shared/resilience/dlq_service.py` — Dead Letter Queue para tasks falhas — presente.
- Retry: `tenacity` no Gemini provider (`stop_after_attempt(2)`, `wait_exponential(max=3s)`). `CommunicationService` com `MAX_RETRIES=3`, exponential backoff.
- CircuitBreaker: 13 arquivos com referências. Implementado para `GEMINI_CIRCUIT`, `MAILGUN_CIRCUIT`, `RESEND_CIRCUIT`, `autonomous_react_agent`. **Mas**: circuit breakers são in-memory — perdem estado no restart (M-06). `CircuitBreaker` ausente no `HubOrchestrator` (M-09).
- `app/domains/ai/services/model_drift_service.py` — drift detection com 4 triggers em janela deslizante 7 dias. **Presente mas sem ação automática**.
- `app/domains/ai/services/ragas_evaluation_service.py` — avaliação de qualidade batch diária. **Passivo** — falha não afeta operação (gap B-03: qualidade degradada não detectada em tempo real).
- FLOW 2: `AuditService.log_decision()` em `hitl_service.py` — PostgreSQL best-effort apenas (não obrigatório). Decisões HITL podem não ser auditadas (F2-G7).
- FLOW 7: `AuditService.log_output()` non-blocking em `wizard_react_agent` — wizard decisions podem não ser auditadas sob falha de DB (A-20).
- `LLM_TIMEOUT_SECONDS=120s` global; `TimedToolNode` 15s por tool — **timeout implementado corretamente**.
- `app/shared/websocket/ws_manager.py` — singleton em-processo sem pub/sub entre workers — ponto único de falha para todas as comunicações WebSocket em produção multi-worker.
- FLOW 6: `SessionStore` usa `session_id = user_id` — dois usuários de tenants diferentes com mesmo `user_id` numérico têm sessões colidindo (M-10).
- Redis com fallback: `dict in-memory quando Redis indisponível (dev/test)` — degradação silenciosa em produção se Redis cair.
- LangSmith: `LANGCHAIN_TRACING_V2` configurável — debugging de traces de agentes disponível quando configurado.

### Justificativa do Score

A dimensão de resiliência e observabilidade é a mais fraca do sistema. Isso é particularmente preocupante porque é a base que permite detectar e corrigir todos os outros problemas. O sistema tem os componentes certos — circuit breakers, DLQ, retry com tenacity, timeouts, OpenTelemetry, Sentry, RAGAS, drift detection — mas nenhum deles fecha o loop de ação corretiva.

Os circuit breakers perdem estado no restart (M-06), o que significa que um provider que estava em OPEN antes de um deploy volta para CLOSED e receberá tráfego imediatamente. O `HubOrchestrator` — ponto central de entrada para chat — não tem circuit breaker (M-09). O Prometheus foi removido sem substituto (Task #138), deixando o sistema sem métricas exportadas de roteamento. O RAGAS avalia qualidade diariamente mas resultados abaixo do threshold não disparam ação. O AuditService em múltiplos pontos críticos é non-blocking — decisões regulatoriamente relevantes podem não ser auditadas.

O WSManager singleton em produção multi-worker é o problema de observabilidade mais grave: o sistema opera como se estivesse entregando resultados em tempo real via WebSocket quando na realidade os eventos podem estar sendo perdidos entre workers. Não há métrica que capture essa perda — o sistema parece funcionar mas não funciona.

### Gap Analysis

- **Sem observabilidade de perda de WebSocket**: nenhuma métrica captura quantos `panel_update` são descartados pelo WSManager singleton.
- Circuit breakers in-memory sem persistência Redis — resetam no deploy, bypass do estado de proteção.
- Prometheus removido sem substituto — sem métricas de roteamento, hit rates, latências por tier.
- RAGAS e drift detection sem closed-loop — observam mas não agem.
- AuditService non-blocking em pontos críticos — compliance audit pode ter gaps silenciosos.
- Redis como dict in-memory quando indisponível — degradação silenciosa em produção.
- `session_id = user_id` — colisão de sessão cross-tenant (M-10).

### Quick Wins (dias/semanas)
1. Persistir estado de circuit breakers em Redis — substituir `dict in-memory` por `Redis HSET cb:{service_name}` (M-06). 1-2 dias.
2. Adicionar circuit breaker ao `HubOrchestrator` — importar `CircuitBreaker` já existente (M-09). 1 dia.
3. Reintegrar métricas básicas ao `cascaded_router.py` usando `prometheus_client` já disponível (reverter Task #138 parcialmente). 2-3 dias.

### Investimentos Estruturais (semanas/meses)
1. Substituir WSManager singleton por Redis pub/sub para WebSocket broadcast — soluciona C-01 e elimina ponto único de falha em multi-worker. 1-2 semanas.
2. Implementar alerting automático para RAGAS abaixo de threshold e drift acima de limite — conectar `model_drift_service.py` a Celery task de remediação ou notificação. 2-3 semanas.
3. Tornar AuditService bloqueante para decisões de alto impacto (WSI final, HITL approve/reject, wizard publish) — aceitar latência adicional em troca de garantia de auditoria. 2-3 semanas.
4. Fix `session_id = user_id` → usar `f"{company_id}:{user_id}"` como chave de sessão (M-10). 1-2 dias de código, semanas de testes de regressão.

---

## RADAR CHART (Descritivo)

```
D1 Agência
  Atual  ████████████░░░░░░░░  2.5/5
  Alvo   ████████████████░░░░  4.0/5

D2 Orquestração
  Atual  ██████████████░░░░░░  3.5/5
  Alvo   ██████████████████░░  4.5/5

D3 Intelligence Depth
  Atual  ████████████░░░░░░░░  2.5/5
  Alvo   ████████████████░░░░  4.0/5

D4 Tool Orchestration
  Atual  ████████████░░░░░░░░  2.5/5
  Alvo   ████████████████░░░░  4.0/5

D5 Cross-cutting
  Atual  ████████████████░░░░  3.0/5  ← ponto mais forte
  Alvo   ██████████████████░░  4.5/5

D6 Resiliência
  Atual  ████████░░░░░░░░░░░░  2.0/5  ← ponto mais fraco
  Alvo   ████████████████░░░░  4.0/5
```

**Padrão dominante**: A plataforma tem uma dimensão de orquestração madura (D2: 3.5) sustentando dimensões de execução e resiliência imaturos (D4, D6: 2.5 e 2.0). O shape do radar revela um sistema que roteia bem mas entrega mal — o roteador sabe para onde enviar a mensagem, mas o destino não tem ação real, persistência garantida ou observabilidade confiável.

---

## BENCHMARK VS MERCADO

| Dimensão | LIA Atual | Paradox Olivia | Eightfold AI | LangChain baseline |
|---|---|---|---|---|
| D1 Agência | 2.5/5 | 2.0/5 | 3.0/5 | 2.5/5 |
| D2 Orquestração | 3.5/5 | 1.5/5 | 2.5/5 | 2.0/5 |
| D3 Intelligence Depth | 2.5/5 | 1.5/5 | 3.5/5 | 1.5/5 |
| D4 Tool Orchestration | 2.5/5 | 2.0/5 | 3.0/5 | 2.0/5 |
| D5 Cross-cutting | 3.0/5 | 1.5/5 | 2.5/5 | 1.0/5 |
| D6 Resiliência | 2.0/5 | 2.5/5 | 3.0/5 | 1.5/5 |
| **Média** | **2.7/5** | **1.8/5** | **2.9/5** | **1.8/5** |

**Notas de benchmark:**

- **Paradox Olivia**: líder em UX conversacional, mas arquitetura stateless sem orquestração multi-tier. Fairness e compliance são thin layers sem profundidade. D6 mais alto por não ter a complexidade da LIA (menos para quebrar).
- **Eightfold AI**: ponto forte em intelligence depth via modelos proprietários de matching. D6 mais alto por maturidade operacional de empresa estabelecida. D2 mais baixo por arquitetura monolítica sem CascadedRouter equivalente. D5 mais baixo por compliance não ser core da oferta.
- **LangChain baseline** (aplicação típica de referência com LangChain + LLM): sem fairness, sem multi-tenant real, sem circuit breakers, sem RAGAS.

**Conclusão do benchmark**: A LIA supera Paradox Olivia em sofisticação arquitetural (D2, D5) e está aproximadamente no mesmo nível que Eightfold em agency e tools. Perde para Eightfold em intelligence depth (modelos proprietários vs rule-based) e resiliência (empresa com mais maturidade operacional). O diferencial competitivo real da LIA é D5 (fairness + LGPD), que é superior a todos os benchmarks. O principal risco competitivo é D6 — um sistema com observabilidade fraca não escala.

---

## CLASSIFICAÇÃO FINAL

**Média:** 2.7/5
**Categoria:** Assistente com potencial
**Subcategoria:** Infraestrutura agêntica presente, execução end-to-end sistematicamente quebrada

**Justificativa:**

A LIA está no limiar entre "chatbot glorificado" e "agente funcional". A infraestrutura arquitetural claramente aponta para a segunda categoria: LangGraph, StateGraph, CascadedRouter de 8 tiers, FairnessGuard de 3 camadas, RAGAS, HITL em 3 fluxos, feedback loop silencioso, Agent Studio com runtime customizável. São capacidades que a maioria dos sistemas de recrutamento conversacional não possui.

Porém, o comportamento end-to-end observado nos FLOW_TRACES justifica o rating intermediário: de 8 fluxos testados, nenhum é completamente funcional. O fluxo mais crítico operacionalmente (F5 — agendamento) está BLOQUEADO por 4 rotas Rails ausentes. O fluxo de comunicação (F4, Path A) retorna respostas de sucesso fictícias. O fluxo de avaliação assíncrona (F3) tem o modelo de dados ausente. O WSManager singleton torna toda comunicação WebSocket em tempo real não-confiável em deployments multi-worker. Esses não são bugs de edge case — são falhas no caminho feliz dos principais fluxos do produto.

A classificação "Assistente com potencial" captura precisamente esse estado: o potencial é genuíno e a arquitetura é mais sofisticada que a maioria dos competidores, mas o gap entre intenção arquitetural e execução end-to-end é sistemático e precisa ser fechado antes que a plataforma possa ser classificada como "Agente funcional". O caminho para 4.0+ existe e está bem definido — não requer reescrita arquitetural, mas sim execução disciplinada dos gaps identificados.

---

## ROADMAP DE MATURIDADE

### Fase 1 — Quick Wins (0–30 dias)
*Objetivo: subir score médio de 2.7 para 3.2 sem mudanças arquiteturais*

| Prioridade | Ação | Gap Resolvido | Dimensão | Esforço |
|---|---|---|---|---|
| P1 | Substituir `WSManager` singleton por Redis pub/sub | C-01 | D2, D6 | 1 semana |
| P2 | Reconectar `communication_tools.py` ao `CommunicationDispatcher` real | C-09, C-10 | D1, D4 | 2-3 dias |
| P3 | Tornar `ConsentChecker` exception bloqueante (não silenciosa) | C-06 | D5 | 1 dia |
| P4 | Adicionar `sourcing` aos `_FAIRNESS_DOMAINS` do C3b | D5 gap | D5 | 2 horas |
| P5 | Persistir circuit breaker state em Redis | M-06 | D6 | 1-2 dias |
| P6 | Adicionar circuit breaker ao `HubOrchestrator` | M-09 | D6 | 1 dia |
| P7 | Reescrever prompt `AutonomousReActAgent` (priority matrix + fairness + persona) | P03 | D1, D3 | 3-5 dias |
| P8 | Injetar `PersonalizationContext` no `SystemPromptBuilder` | M-16 | D3 | 1-2 dias |
| P9 | Adicionar ConsentChecker gate em `search_candidates` tool | C-02 | D5 | 1-2 dias |
| P10 | Adicionar AuditService em `query_tools.py` path agent | A-02 | D5 | 1 dia |

**Impacto esperado**: Fechar C-01 sozinho melhora D2 de 3.5 → 4.0 e D6 de 2.0 → 2.5. Fechar C-09 melhora D1 de 2.5 → 3.0 e D4 de 2.5 → 3.0.

### Fase 2 — Investimentos Médios (30–90 dias)
*Objetivo: subir score médio de 3.2 para 3.8*

| Prioridade | Ação | Gap Resolvido | Dimensão |
|---|---|---|---|
| P11 | Criar 4 rotas Rails ausentes para scheduling | C-11 | D1, D4 |
| P12 | Habilitar `USE_SUPERVISOR = True` com testes de HubPlanner/HubExecutor | D1 gap | D1, D2 |
| P13 | Persistir `wsi_final_score` em banco + criar modelo `WSISession` | C-04, C-07 | D1, D4 |
| P14 | Implementar Tenant Isolation Explícita em todos os 13 prompts | P03 Gap 1 | D3, D5 |
| P15 | Implementar Budget/Token Awareness nos prompts | P03 Gap 2 | D3 |
| P16 | Fechar loop RAGAS → Celery task de remediação | B-03 | D3, D6 |
| P17 | Reintegrar métricas Prometheus ao `cascaded_router.py` | M-20 | D6 |
| P18 | Implementar fairness check pós-ranking no WRF | A-03 | D5 |
| P19 | AuditService bloqueante para decisões alto impacto (WSI, HITL, wizard publish) | A-20 | D5, D6 |
| P20 | Fix `session_id = user_id` → `f"{company_id}:{user_id}"` | M-10 | D6 |

### Fase 3 — Investimentos Estruturais (90–180 dias)
*Objetivo: subir score médio de 3.8 para 4.3 — classificação "Agente maduro"*

| Prioridade | Ação | Gap Resolvido | Dimensão |
|---|---|---|---|
| P21 | Unificação `CascadedRouter` + `CostLadderRouter` em sistema único | A-15 | D2 |
| P22 | Consolidação de prompts duplicados (eliminar ~3.000 linhas legacy) | P03 Gap 5 | D3 |
| P23 | Implementar context compaction padronizado em todos os agentes | P03 Gap 6 | D3 |
| P24 | Closed-loop de aprendizado: LearningLoop → SystemPromptBuilder injection | D3 gap | D3 |
| P25 | Closed-loop de drift: model_drift_service → ação automática de remediação | D6 gap | D6 |
| P26 | Auditoria completa de tool stubs + test suite automatizado | D4 gap | D4 |
| P27 | Cross-Agent Handoff Protocol (route_to_domain com contexto) | P03 Gap 5 | D1, D2 |
| P28 | Formalizar EU AI Act compliance com HITL em todos os agentes de alto impacto | P03 Gap | D5 |
| P29 | Conectar Frontend ao Rails (descomentando NEXT_PUBLIC_RAILS_URL + implementar proxies) | A-01 | D1, D4 |
| P30 | Fine-tuning pipeline: export → treino → avaliação → deploy controlado | D3 gap | D3 |

---

## SÍNTESE DE GAPS POR NÚMERO E SEVERIDADE

**Total de gaps identificados (FLOW_TRACES Appendix A):**
- 12 CRÍTICOS (C-01 a C-12)
- 22 ALTOS (A-01 a A-22)
- 20 MÉDIOS (M-01 a M-20)
- 3 BAIXOS (B-01 a B-03)
- **Total: 57 gaps**

**Top 5 gaps por impacto nas 6 dimensões:**
1. **C-01** — WSManager singleton: impacta D1, D2, D3, D4, D5, D6 simultaneamente
2. **C-09** — Tool stubs de comunicação: impacta D1, D4 com consequências em D5 (LGPD bypass)
3. **C-11** — 4 rotas Rails ausentes para scheduling: bloqueia completamente F5, impacta D1, D4
4. **M-16** — PersonalizationContext não injetada: impacta D3 (learning sem feedback)
5. **A-01** — Frontend desconectado do Rails: impacta D1, D4, D6 (dados inconsistentes entre layers)

---

*Documento gerado pelo Protocolo P04. Próximo documento: P07 (Plano de Remediação de Gaps). P21 (Prompt Rewriting Guidelines) deve ser iniciado em paralelo usando P03 e este diagnóstico como base.*
