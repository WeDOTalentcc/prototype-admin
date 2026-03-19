# Análise Comparativa: recruiter_agent_v5 vs LIA Platform

**Data:** 08/03/2026 — **Última revisão:** 19/03/2026 — Sprints A–F, G1–G7, I, J, K2, X1, X4, X5, SEG-1–5, SEG-GAPS, AUD-1–5, Y1–Y5, Z1–Z7 concluídos + AUD Audit Cards (WT-1506→WT-1512)
**Objetivo:** Documento de referência para discussão com o time sobre caminhos de evolução arquitetural da LIA, com base no diagnóstico do André e na análise do projeto recruiter_agent_v5 (projeto paralelo desenvolvido com base similar mas arquitetura de agentes diferente).

---

## Índice

0. [Tabela Mestra de Funcionalidades](#0-tabela-mestra-de-funcionalidades)
1. [Contexto e Propósito](#1-contexto-e-propósito)
2. [Visão Geral dos Dois Sistemas](#2-visão-geral-dos-dois-sistemas)
3. [Arquitetura de Entry Points](#3-arquitetura-de-entry-points)
4. [Sistema de Roteamento](#4-sistema-de-roteamento)
5. [Sistema de Domínios](#5-sistema-de-domínios)
6. [Camada de Agentes](#6-camada-de-agentes)
7. [Memória Conversacional](#7-memória-conversacional)
8. [Planos Multi-Etapa](#8-planos-multi-etapa)
9. [Sistema de Tools](#9-sistema-de-tools)
10. [Infraestrutura de Serviços](#10-infraestrutura-de-serviços)
11. [Compliance e Governança](#11-compliance-e-governança)
12. [Observabilidade e Qualidade](#12-observabilidade-e-qualidade)
13. [Gaps Críticos da LIA](#13-gaps-críticos-da-lia)
14. [Gaps Críticos do v5](#14-gaps-críticos-do-v5)
15. [Síntese Comparativa por Dimensão](#15-síntese-comparativa-por-dimensão)
16. [Análise do Fluxo Real de uma Mensagem](#16-análise-do-fluxo-real-de-uma-mensagem)
17. [Proposta: Caminho B — Main Orchestrator](#17-proposta-caminho-b--main-orchestrator)
18. [Roadmap de Implementação](#18-roadmap-de-implementação)
19. [Camada de Inteligência Completa da LIA](#19-camada-de-inteligência-completa-da-lia)
20. [Status de Implementação das Recomendações do André](#20-status-de-implementação-das-recomendações-do-andré)
21. [Itens Pendentes de Análise](#21-itens-pendentes-de-análise)
22. [Mapeamento AUD — Cards Jira de Auditoria do Agente Python V5](#22-mapeamento-aud--cards-jira-de-auditoria-do-agente-python-v5)
- [Conclusão](#conclusão)

---

## 0. Tabela Mestra de Funcionalidades

> Visão consolidada de todas as dimensões analisadas. Referência rápida para discussão com o time.
> **Legenda:** ✅ Implementado | ⚠️ Parcial | ❌ Ausente | — N/A | 🔵 André recomendou

### Prioridade: 🔴 Alta | 🟡 Média | 🟢 Baixa | ✔ Concluído

| # | Dimensão / Feature | v5 | LIA | André | Prioridade | Arquivo LIA Principal | Comentário |
|---|---|---|---|---|---|---|---|
| **ARQUITETURA CENTRAL** | | | | | | | |
| 01 | Entry point único / Main Orchestrator | ✅ MessageRouter | ✅ MainOrchestrator | 🔵 | ✔ Concluído | `app/orchestrator/main_orchestrator.py` | v5 inspirou o padrão; LIA implementou com thin adapters por canal |
| 02 | Sistema de roteamento em cascata | ⚠️ 3 estratégias | ✅ 6 tiers + VectorCache | 🔵 | ✔ Concluído | `app/orchestrator/cascaded_router.py` | LIA mais sofisticado: pgvector semântico + LLM cascade Haiku→Sonnet→Opus |
| 03 | Domínios DDD com DomainPrompt ABC | ✅ 2 domínios | ✅ 11 domínios | — | ✔ Concluído | `app/domains/base.py` | Interface padrão (ABC) que todo domínio implementa: system prompt, ações permitidas, validação de contexto e sugestões. Contrato base idêntico nos dois sistemas |
| 04 | DomainWorkflow com compliance embutido | ⚠️ 3 nós | ✅ 7 passos | — | ✔ Concluído | `app/domains/domain_workflow.py` | Pipeline de execução de uma mensagem no domínio: PRE_CHECK → RESOLVE_REFERENCES → SMART_EXTRACT → ANALYZE_INTENT → EXECUTE → FORMAT → POST_CHECK. POST_CHECK garante FairnessGuard em 100% dos paths |
| 05 | Contextos de agentes versionados (YAML) | ❌ inline em código | ✅ libs/contexts/ 9 domínios | 🔵 | ✔ Concluído | `libs/contexts/` | Prompts e configurações de agentes em arquivos YAML separados do código — mudança de prompt via PR/revisão, não deploy. André recomendou fortemente |
| **AGENTES** | | | | | | | |
| 06 | Paradigma ReAct nativo (LLM decide tools) | ❌ Classes com process() | ✅ 7 ReAct agents | 🔵 | ✔ Concluído | `app/shared/agents/langgraph_react_base.py` | Loop autônomo Thought→Action→Observation: o LLM decide qual tool usar, em que ordem e quando parar — sem código determinístico de roteamento. LIA usa `create_react_agent` do LangGraph; v5 não é ReAct real |
| 07 | Graph agents (StateGraph + PostgresSaver) | ⚠️ MemorySaver apenas | ✅ 3 graph agents | 🔵 | ✔ Concluído | `app/domains/job_management/graphs/` | Fluxos com nós e transições definidas (StateGraph) para processos previsíveis e auditáveis. Checkpoints no PostgreSQL garantem retomada após falha. Wizard, WSI, Interview |
| 08 | TimedToolNode (timeout 15s por tool) | ❌ | ✅ libs/agents-core/ | 🔵 | ✔ Concluído | `libs/agents-core/timed_tool_node.py` | Sprint A — asyncio.wait_for + ToolError("timeout") fallback |
| 09 | Agente de Automação ReAct (4-file pattern) | ❌ | ✅ domains/automation/ | — | ✔ Concluído | `app/domains/automation/agents/automation_react_agent.py` | 9 tipos de agente, DAG de tarefas, decomposição de tarefas complexas, 10+ tools |
| 10 | Agentes legacy migrados para ReAct | — | ✅ analytics, comm, ATS | — | ✔ Concluído | `app/domains/analytics/agents/` + `communication/` + `ats_integration/` | Fases 4a/4b/4c/5: analytics, communication, ats_integration wired no WS |
| **MEMÓRIA E CONTEXTO** | | | | | | | |
| 11 | Memória conversacional persistida em DB | ❌ em memória | ✅ ConversationState (PG) | — | ✔ Concluído | `app/services/conversation_memory_service.py` | LIA persiste histórico com summarização automática |
| 12 | Resolução de referências (pronomes, posição) | ✅ MemoryResolver | ✅ MemoryResolver expandido | 🔵 | ✔ Concluído | `app/orchestrator/memory_resolver.py` | "e ele?", "o terceiro", "desse grupo" — implementado na LIA (fase MainOrchestrator) |
| 13 | Paginação conversacional | ✅ get_pagination_context() | ✅ | — | ✔ Concluído | `app/orchestrator/memory_resolver.py` | Continuidade de filtros entre mensagens |
| 14 | Short Lists explícitas | ✅ shortlist em memória | ✅ short_list_service.py + DB | — | ✔ Concluído | `app/services/short_list_service.py` | Sprint F4 — CRUD completo com persistência |
| **TOOLS** | | | | | | | |
| 15 | Tool Registry com YAML metadata | ✅ YAML-first | ✅ tool_registry_metadata.yaml | — | ✔ Concluído | `app/tools/tool_registry_metadata.yaml` | Sprint G5 — 32 tools declaradas, allowed_agents, scope, validação |
| 16 | Tool handlers Python reais | ❌ HTTP ao ATS | ✅ handlers locais | — | ✔ Concluído | `app/tools/registry.py` | LIA executa lógica de negócio; v5 apenas HTTP proxy |
| 17 | PromptScope por contexto | ❌ | ✅ TALENT_FUNNEL / JOB_TABLE / IN_JOB / GLOBAL | — | ✔ Concluído | `app/tools/scope_config.py` | Evita tools de vaga no chat de candidatos |
| **COMPLIANCE E GOVERNANÇA** | | | | | | | |
| 18 | FairnessGuard (3 camadas) | ⚠️ regex básico | ✅ regex + léxico + LLM | — | ✔ Concluído | `app/shared/compliance/fairness_guard.py` | **v5.0 Sprint X1:** 62 termos explícitos (9 cat.) + 11 implícitos = **73 padrões** `_PATTERNS_VERSION=2`. Layer 3 ativa em 3 callers críticos. 11/11 agentes + Orchestrator. 0 xfails red team. |
| 19 | Bias Audit (Four-Fifths Rule) | ❌ | ✅ bias_audit_service.py | — | ✔ Concluído | `app/services/bias_audit_service.py` + `app/models/bias_audit_snapshot.py` | 4 dimensões: gênero, idade, PCD, região; snapshot histórico SOX |
| 20 | LGPD / EU AI Act / BCB 498 / SOX / ISO 27001 | ❌ | ✅ stack completo | — | ✔ Concluído | `app/services/lgpd/` + `app/services/ai_act_compliance.py` + `app/services/bcb498_compliance.py` | Portal titular, consent management, audit logs S3 lifecycle 7 anos |
| 21 | Model Drift Detection (4 triggers) | ❌ | ✅ model_drift_service.py | — | ✔ Concluído | `app/services/model_drift_service.py` + `app/services/drift_alert_service.py` | Score, aprovação, custo, latência P95 — batch diário Celery + alertas Bell+Teams |
| 22 | Anti-sycophancy (benchmark setorial) | ❌ | ✅ sector_benchmark_service.py | — | ✔ Concluído | `app/services/sector_benchmark_service.py` | Prevenção de respostas "bajuladoras": benchmarks de mercado são injetados nos prompts para ancorar sugestões de salário e perfil em dados reais — evita que o LLM concorde com qualquer pedido. 16 perfis (4 seniorities × 4 áreas) — Crença #11 |
| 23 | AuditCallback (auditoria de chamadas LLM) | ❌ → [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) | ✅ libs/audit/audit_callback.py | 🔵 | ✔ Concluído | `libs/audit/audit_callback.py` + `libs/audit/audit_storage.py` | Middleware transparente: registra cada chamada LLM (input, output, custo, latência) sem que o agente saiba que está sendo auditado. Dual storage: metadados em PG (fast query), logs completos em S3 (7 anos SOX). **v5: card [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) criado para propagar AuditCallback para ReAct Agents** |
| 24 | FactChecker (anti-alucinação) | ✅ fact_checker.py | ✅ FactChecker | — | ✔ Concluído | `app/services/fact_checker_service.py` | v5: embutido em todos os agentes. LIA: serviço dedicado |
| **HITL (Human-in-the-Loop)** | | | | | | | |
| 25 | HITL básico (interrupt_before/after LangGraph) | ❌ flag needs_confirmation | ✅ interrupt_before configurado | 🔵 | ✔ Concluído | `app/services/hitl_service.py` + `app/api/v1/hitl.py` | Sprint C — 3 fluxos críticos: email massa, mover para oferta, WSI borderline |
| 26 | HITL Persistence (DB-backed) | ❌ | ✅ hitl_service.py + models/hitl.py | — | ✔ Concluído | `app/models/hitl.py` + `alembic/versions/032_add_hitl_tables.py` | Sprint F1 — tabelas hitl_pending_actions + hitl_audit_trail |
| 27 | HITLConfirmCard (FE WebSocket streaming) | ❌ | ✅ HITLConfirmCard.tsx | — | ✔ Concluído | `plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx` + `use-float-streaming.ts` | Sprint J — card de aprovação com streaming em tempo real |
| 28 | Aprovação multi-tier (5 tipos ApprovalRequest) | ❌ | ✅ ApprovalRequest 5 tipos | — | ✔ Concluído | `libs/models/lia_models/approval.py` | Sistema estruturado de aprovação por tipo de ação: 5 tipos com fluxo multi-tier (recrutador → gestor → financeiro). Tipos: VACANCY_APPROVAL, CANDIDATE_HIRE, OFFER_APPROVAL, BUDGET_APPROVAL, CUSTOM |
| **OBSERVABILIDADE** | | | | | | | |
| 29 | Prometheus (5 métricas de roteamento/agentes) | ❌ → [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) | ✅ app/core/metrics.py | 🔵 | ✔ Concluído | `app/core/metrics.py` | router_tier_hit, latency_ms, confidence, tool_failures, llm_cost_usd. **v5: card [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) criado para implementar Prometheus** |
| 30 | Grafana dashboard | ❌ | ✅ docker-compose.yml | 🔵 | ✔ Concluído | `docker-compose.yml` + `grafana/provisioning/` | Sprint B — provisioning via JSON, alertas de custo/latência/tool failure |
| 31 | Sentry error tracking | ❌ | ✅ app/core/sentry.py | 🔵 | ✔ Concluído | `app/core/sentry.py` | Sprint B — FastAPIIntegration + CeleryIntegration + PII scrubbing LGPD |
| 32 | LangSmith tracing (AuditCallback integrado) | ❌ | ✅ + CI step (Sprint F6) | 🔵 | ✔ Concluído | `.github/workflows/ci.yml` (step Verify LangSmith) | LANGSMITH_API_KEY em CI — verifica config a cada deploy |
| 33 | LangGraph Studio | ❌ | ✅ langgraph.json | 🔵 | ✔ Concluído | `langgraph.json` | Interface visual de debug para grafos LangGraph — permite inspecionar estados, nós, transições e execuções passadas em tempo real. Essencial para debugar Wizard, WSI e Interview em dev/staging |
| 34 | Snapshot testing de agentes | ❌ | ✅ tests/snapshots/ 4 arquivos | 🔵 | ✔ Concluído | `tests/snapshots/test_remaining_agents_snapshots.py` | Sprint D — Wizard, Pipeline + remaining agents (Sourcing, Policy, Kanban, Talent, Jobs) |
| 35 | Versionamento de prompts com registry | ❌ | ✅ prompt_version_registry.py | 🔵 | ✔ Concluído | `app/services/prompt_version_registry.py` | Sprint B — campo prompt_version em ConversationLog; falta: métricas por versão |
| **INFRAESTRUTURA** | | | | | | | |
| 36 | Rate limiting por tenant (budget LLM) | ❌ sem multi-tenancy | ✅ rate_limiter.py + token_budget_service.py | 🔵 | ✔ Concluído | `app/middleware/rate_limiter.py` + `app/services/token_budget_service.py` | Sprint A — Redis middleware, HTTP 429 + Retry-After, budget por plano |
| 37 | Multi-tenancy (company_id em tudo) | ❌ | ✅ todos os modelos e queries | 🔵 | ✔ Concluído | `app/models/` (todos os modelos) | Bloqueador de produto B2B; LIA tem desde o início |
| 38 | UV Monorepo (9 libs compartilhadas) | ❌ | ✅ libs/ (config, utils, models, audit, messaging, agents-core, services, contexts, auth) | 🔵 | ✔ Concluído | `libs/` (9 módulos) + `pyproject.toml` | Código compartilhado organizado em libs independentes versionadas separadamente — permite que times diferentes deployem serviços sem depender de um monolito. Fase 6 — 9 libs, deploys independentes |
| 39 | Docker Compose multi-serviço | ⚠️ básico | ✅ 10 serviços + Celery (high/normal/low) + beat + Flower | 🔵 | ✔ Concluído | `docker-compose.yml` | Fase 6b — Flower verificado e acessível com auth básica |
| 40 | RabbitMQ como transporte de eventos | ✅ (primário) | ✅ (infraestrutura pronta) | 🔵 | 🟡 Média | `app/services/platform_events.py` + `app/services/rabbitmq_producer.py` | LIA tem infra mas ainda não ativada entre serviços; ativar quando separar APIs |
| 41 | WebSocket + streaming de tokens | ❌ síncrono | ✅ agent_chat_ws.py | — | ✔ Concluído | `app/api/v1/agent_chat_ws.py` | Sprint J migrou LiaChatPanel REST → WebSocket com streaming |
| 42 | SecretsProvider plugável (Doppler/GCP/Env) | ❌ .env direto | ✅ libs/auth/secrets_provider.py | 🔵 | ✔ Concluído | `libs/auth/secrets_provider.py` | Nunca .env em produção |
| **INTELIGÊNCIA E AUTOMAÇÃO** | | | | | | | |
| 43 | Personalização invisível por recrutador | ❌ | ✅ recruiter_personalization_service.py (555L) | — | ✔ Concluído | `app/services/recruiter_personalization_service.py` | Detecta padrões de comportamento de cada recrutador (ex: "sempre aumenta salário sugerido +15%", "prefere Pleno→Sênior") e aplica automaticamente nas próximas sugestões — sem UI, sem configuração manual. Após 10+ vagas. LGPD consent_version incluído |
| 44 | Sistema de aprendizado contínuo (7 padrões) | ❌ | ✅ learning_loop_service.py (1073L) | — | ✔ Concluído | `app/shared/learning/learning_loop_service.py` | Aprende continuamente com outcomes reais: quais sugestões foram aceitas/rejeitadas, resultados de vagas, tempos de contratação. CAPTURE → ANALYZE → APPLY. 7 padrões: salary, skill, benefit, work_model, JD style, screening, skill_suggestion |
| 45 | Motor de automação de stage transitions | ❌ | ✅ stage_automation_engine.py (460L) + automation_service.py (1234L) | — | ✔ Concluído | `app/domains/automation/services/stage_automation_engine.py` + `automation_service.py` | 15+ trigger types; sub-status prediction; mensagens personalizadas via Claude |
| 46 | Alertas proativos inteligentes (5 categorias) | ❌ | ✅ proactive_alert_service.py (779L) | — | ✔ Concluído | `app/domains/automation/services/proactive_alert_service.py` | Pipeline, Produtividade, Comunicação, Preditivo (dropout risk), Sistema |
| 47 | Autonomous agent service (background jobs) | ❌ | ✅ autonomous_agent_service.py (838L) | — | ✔ Concluído | `app/domains/automation/services/autonomous_agent_service.py` | Tarefas agendadas, recorrentes, sugestões proativas, ações automáticas |
| 48 | Predição ML (outcome predictor, time-to-fill) | ❌ | ✅ ml/outcome_predictor.py (532L) | — | ✔ Concluído | `app/services/ml/outcome_predictor.py` + `app/services/ml/feature_engineering.py` | P(filled \| job_id, pipeline), salary range, skill success likelihood |
| 49 | Ponte Predição-Ação | ❌ | ✅ prediction_action_bridge.py (176L) | — | ✔ Concluído | `app/domains/automation/services/prediction_action_bridge.py` | High success → avança; dropout risk → ações preventivas; fill risk → expande sourcing |
| 50 | Monitor de pipeline (SLA, stagnação) | ❌ | ✅ pipeline_monitor.py (385L) | — | ✔ Concluído | `app/domains/automation/services/pipeline_monitor.py` | Candidatos estagnados, WSI alto sem ação, deadlines próximas, entrevistas sem feedback |
| 51 | Inteligência semântica compartilhada (7 domínios) | ⚠️ básico | ✅ shared/intelligence/semantic_search_service.py (442L) | — | ✔ Concluído | `app/shared/intelligence/semantic_search_service.py` | Expansão semântica: skills, job titles, roles, setores, áreas de estudo — Gemini + Redis |
| 52 | Fine-tuning export (dados para melhoria do modelo) | ❌ | ✅ shared/learning/finetuning_export.py (334L) | — | 🟡 Média | `app/shared/learning/finetuning_export.py` | Exporta padrões anonimizados, mask PII, gera datasets de treinamento |
| 53 | A/B testing de prompts/versões | ❌ | ✅ ab_testing_service.py (306L) | — | ✔ Concluído | `app/shared/learning/ab_testing_service.py` | chi-square, stratification por empresa, effect_size + recomendação |
| 54 | Orquestração multi-source (7 fontes) | ❌ 1 fonte (ATS HTTP) | ✅ intelligent_data_orchestrator.py (929L) | — | ✔ Concluído | `app/services/intelligent_data_orchestrator.py` | Combina 7 fontes de dados priorizadas para gerar sugestões mais precisas, com detecção de consenso: se Learning Patterns + ATS History concordam em R$8-10k, confidence aumenta automaticamente. Prioridade: Learning Patterns > Company Skills > Config > Job Insights > ATS > Benchmark > LLM |
| **PRODUTO** | | | | | | | |
| 55 | WSI (Work Simulation Interview) | ❌ | ✅ 12+ arquivos | — | ✔ Concluído | `app/domains/cv_screening/` (wsi_screening_pipeline.py, wsi_interview_graph.py, etc.) | Bloom, scorer determinístico, voz (OpenMic.ai + Deepgram), feedback estruturado |
| 56 | Sourcing externo ativo (190M+ perfis) | ❌ ATS local | ✅ Pearch AI + Apify + 13+ serviços | — | ✔ Concluído | `app/services/pearch_service.py` + `app/services/apify_service.py` | Busca em fontes externas + enriquecimento de perfil |
| 57 | RAG Híbrido (BM25 + pgvector) | ⚠️ pgvector apenas | ✅ rag_pipeline_service.py (Sprint G6) | — | ✔ Concluído | `app/services/rag_pipeline_service.py` | alpha blend: BM25 (tsvector) + pgvector cosine; FairnessGuard top-10 |
| 58 | TOON Format (card candidato+vaga) | ❌ | ✅ toon_service.py (Sprint G7) | — | ✔ Concluído | `app/services/toon_service.py` + `app/api/v1/toon.py` | Redis TTL 1h, LGPD anonymize, chave scoped por company_id |
| 59 | Comunicação multi-canal (5 canais) | ❌ retorna para ATS | ✅ Bell + Email + Teams + WhatsApp + Chat | — | ✔ Concluído | `app/services/notification_service.py` + `app/shared/channels/adapters/` | Dispatch automático em transições de pipeline |
| 60 | Float Chat WebSocket (LiaChatPanel) | ❌ | ✅ Sprint J — REST → WebSocket | — | ✔ Concluído | `plataforma-lia/src/hooks/use-float-streaming.ts` + `navigation_intent.py` | use-float-streaming.ts, HITLConfirmCard.tsx, navigation_intent.py 4 novos grupos |
| 61 | Explicabilidade (timeline por candidato/sessão) | ❌ | ✅ explainability_service.py (322L) | — | ✔ Concluído | `app/services/explainability_service.py` + `app/api/v1/agent_explainability.py` | Critérios avaliados/ignorados, timeline ReAct, stats por agente |
| 62 | Rastreamento de tokens e budget por tenant | ❌ | ✅ token_tracking_service.py (722L) | — | ✔ Concluído | `app/services/token_tracking_service.py` | 10 modelos, alertas 80%/100%, retenção 365d LGPD |
| **PADRÃO DE PRODUÇÃO / REPLICAÇÃO DE AGENTES** | | | | | | | |
| 63 | Padrão canônico 4 arquivos por agente (agent scaffold) | ❌ (classes ad hoc) | ✅ `_react_agent.py`, `_tool_registry.py`, `_system_prompt.py`, `_stage_context.py` | 🔵 | ✔ Concluído | `app/shared/agents/agent_scaffold.py` | **Principal mecanismo de replicação.** Cada agente SEMPRE tem exatamente 4 arquivos com responsabilidades separadas — garante que novos agentes sejam criados de forma consistente, auditável e com todos os hooks (observabilidade, fairness, multi-tenancy) já conectados. 9 agentes seguem o padrão |
| 64 | ReactAgentRegistry (registro formal dos agentes) | ❌ | ✅ `app/shared/agents/react_agent_registry.py` — 8 registrados + PipelineTransitionAgent = 9 total | 🔵 | ✔ Concluído | `app/shared/agents/react_agent_registry.py` | Registry central: wizard, pipeline, sourcing, talent, jobs_management, kanban, policy, automation |
| 65 | ADR process (decisões arquiteturais documentadas) | ❌ | ✅ `docs/adr/` — ADR 001 (Python/FastAPI), ADR 002 (Graph vs ReAct), ADR 003 (Async para longas) | 🔵 | ✔ Concluído | `docs/adr/` | ADR 002 é a **regra de ouro**: Graph (previsível+auditável) / ReAct (imprevisível+conversacional) / REST (CRUD <500ms) |
| 66 | GuardrailRepository (guardrails em banco, 3-tier) | ❌ | ✅ `app/shared/compliance/guardrail_repository.py` | 🔵 | ✔ Concluído | `app/shared/compliance/guardrail_repository.py` + `app/core/seeds/guardrails_seed.py` | Guardrails editáveis via CRUD sem re-deploy. Hierarquia: global → tenant → domínio. Seed via migration |
| 67 | Prompt engineering standards (YAML + persona + compliance blocks) | ❌ inline em código | ✅ YAMLs por domínio + persona canônica "LIA" + compliance blocks imutáveis (Apêndice C) | 🔵 | ✔ Concluído | `app/domains/<domain>/prompts/*.yaml` + `docs/GUIA_ARQUITETURA_IA_v1.0.md` Apêndice C | Padrão de escrita e organização de prompts: YAML por domínio (versionado via git), persona "LIA" consistente em todos os agentes, blocos de compliance (LGPD/fairness) injetados automaticamente — nunca reescrever, sempre copiar dos apêndices |
| 68 | LLM Cascade (Haiku→Sonnet→Opus, thresholds de confiança) | ❌ Gemini único | ✅ Haiku (conf > 0.80) → Sonnet (> 0.70) → Opus (fallback) | 🔵 | ✔ Concluído | `app/orchestrator/cascaded_router.py` (LLMCascade Tier 5) | Escalada de custo: queries simples usam o modelo mais barato (Haiku), só escalam para modelos maiores se confidence estiver baixa. Economia de ~40-60% em custo de LLM. Gemini como fallback adicional |
| 69 | Checklist de reprodução em novo ambiente (Seção 37 do Guia) | ❌ | ✅ `docs/GUIA_ARQUITETURA_IA_v1.0.md` §37 | 🔵 | ✔ Concluído | `docs/GUIA_ARQUITETURA_IA_v1.0.md §37` | Guia completo para setup de ambiente, variáveis, migrations, seeds, health check |
| **AUDITORIA E RASTREAMENTO DE DECISÕES** ← *itens 7 e 8 do André — mais importantes* | | | | | | | |
| 70 | AgentExecutionLog + IterationLog (audit trail completo por iteração) | ❌ → [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) + [AUD-002/WT-1507](https://wedotalent.atlassian.net/browse/WT-1507) | ✅ `app/shared/agents/observability.py` | 🔵 | ✔ Concluído | `app/shared/agents/observability.py` | **Item 7 do André.** Registra cada ciclo do loop ReAct (Thought/Action/Observation) com reasoning COMPLETO (sem truncamento), tool_name, tool_args, observation (max 5000 chars), decision, duration_ms. Permite reconstruir exatamente por que o agente tomou cada decisão — essencial para SOX/LGPD. **v5: cards [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) (AuditCallback) + [WT-1507](https://wedotalent.atlassian.net/browse/WT-1507) (tool tracking) criados** |
| 71 | GuardrailRepository — 13 seeds obrigatórios em banco (3-tier) | ❌ hardcoded | ✅ `app/shared/compliance/guardrail_repository.py` + `app/core/seeds/guardrails_seed.py` | 🔵 | ✔ Concluído | `app/core/seeds/guardrails_seed.py` | **Item 8 do André.** 6 primary (LGPD/fairness global) + 7 secondary (por domínio). `SELECT count(*) FROM guardrails` → 13 |
| 72 | Agent Health Dashboard (4 estados por domínio) | ❌ | ✅ `GET /api/v1/agent-monitoring/domains/health` + Admin UI `/admin/monitoring/agents` | 🔵 | ✔ Concluído | `app/api/v1/agent_monitoring.py` + `app/shared/governance/agent_monitoring_service.py` | healthy / warning / degraded / stale — por domain + company_id |
| 73 | Human Review Sampling (5% determinístico MD5) | ❌ | ✅ `app/services/human_review_sampling_service.py` | 🔵 | ✔ Concluído | `app/services/human_review_sampling_service.py` | 5% das decisões de IA para revisão humana. ALWAYS_REVIEW: finalize_hiring, mass_rejection, fairness_flagged |
| 74 | AI Footer automático em emails (LGPD + EU AI Act) | ❌ | ✅ `app/shared/channels/adapters/email_adapter.py` — `AI_GENERATED_FOOTER` | 🔵 | ✔ Concluído | `app/shared/channels/adapters/email_adapter.py` | Injetado automaticamente quando `message.ai_generated=True`. Idempotente (marcador "WeDOTalent"). Obrigatório EU AI Act |
| 75 | FairnessGuard com 9 categorias + citações legislativas | ⚠️ regex básico | ✅ 9 categorias, **62 termos** explícitos (Sprint X1 — era 42) | 🔵 | ✔ Concluído | `app/shared/compliance/fairness_guard.py` | genero (8), raca_etnia (8), idade (13), deficiencia (8), maternidade (13), religiao/orientacao/civil/nac (3 cada). `_PATTERNS_VERSION=2`. |
| 76 | Implicit Bias Lexicon (Layer 2 FairnessGuard) | ❌ | ✅ `IMPLICIT_BIAS_TERMS` — 11 termos | 🔵 | ✔ Concluído | `app/shared/compliance/fairness_guard.py` (IMPLICIT_BIAS_TERMS) | Discriminação indireta: "boa aparencia", "bairros nobres", "universidades de primeira linha", "escola particular" — total 73 padrões com Camada 1 |
| 77 | Compliance Deploy Checklist (Apêndice C) | ❌ | ✅ `docs/GUIA_ARQUITETURA_IA_v1.0.md` Apêndice C | 🔵 | ✔ Concluído | `docs/GUIA_ARQUITETURA_IA_v1.0.md` Apêndice C | Checklist antes de qualquer deploy. Compliance blocks copiados EXATAMENTE (nunca reescrever) |
| 78 | Verification commands de produção (Seção 37) | ❌ | ✅ `docs/GUIA_ARQUITETURA_IA_v1.0.md` §37 | 🔵 | ✔ Concluído | `docs/GUIA_ARQUITETURA_IA_v1.0.md §37` | grep para imports legados, `SELECT count(*) FROM guardrails` → 13, `alembic current` → 022_reconcile_missing_schemas |
| 79 | Audit trail de system prompts (EU AI Act Art. 14) | ❌ | ✅ `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_2026_02.md` | 🔵 | ✔ Concluído | `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_2026_02.md` | Auditoria dos 7 agentes: fairness blocks presentes, discriminação proibida, supervisão humana verificada |
| 80 | Health endpoint unificado (prontidão para produção) | ❌ | ✅ `GET /health` + `GET /api/v1/agent-monitoring/domains/health` | 🔵 | ✔ Concluído | `app/api/v1/health.py` | Alembic na HEAD (022). Sem dados mock. Schemas versionados. Guardrails seed verificado |
| 81 | API Reference completa + OpenAPI metadata (ACH-020) | ❌ | ✅ `docs/API_REFERENCE.md` + `app/main.py` metadata | — | ✔ Concluído (Sprint X5) | `docs/API_REFERENCE.md` (342L) | 14 grupos de endpoints, auth, rate limits, changelog, 22 tags OpenAPI com desc., contact, license — 25 testes `test_ach020_api_docs.py` |
| 82 | IntentRouter few-shot T3 RH sênior (20 exemplos) | ❌ | ✅ seção `FEW-SHOT` em `_create_intent_prompt()` | — | ✔ Concluído (Sprint X4/J2) | `app/orchestrator/intent_router.py` | 10 claros (conf ≥0.93) + 10 ambíguos (conf 0.72–0.81); intents: job_planner, sourcing, cv_screening, scheduling, funnel, feedback, sync_ats, daily_briefing, wsi_evaluator, interviewer |
| 83 | Red Teaming framework (6 cenários, 0 xfails) | ❌ | ✅ `tests/security/` — 6 arquivos red team | — | ✔ Concluído (Sprint X1) | `tests/security/test_red_team_fairness.py` | Prompt injection, LGPD, PII, multi-tenant, circuit breakers, fairness — todos passando sem xfail. FairnessGuard 73 padrões. |
| **QUALIDADE E SEGURANÇA (ADR-002 Observability)** | | | | | | | |
| 84 | SonarCloud (quality gate no CI/CD) | ❌ | ⚠️ não configurado | 🔵 | 🟡 Média | `.github/workflows/ci.yml` (pendente step SonarCloud) | ADR-002 Must-Have. Cobre Python + TypeScript. Code smells, duplicação, coverage integrados ao CI |
| 85 | PostHog (product analytics + feature flags) | ❌ | ❌ não implementado | 🔵 | 🟡 Média | — | ADR-002 Must-Have. Analytics + session replay + feature flags. Alternativa ao LaunchDarkly |
| 86 | Dependabot + Snyk (supply chain security) | ❌ | ⚠️ Dependabot parcial, Snyk não | 🔵 | 🟡 Média | `.github/dependabot.yml` | ADR-002 Must-Have. Dependências vulneráveis + supply chain security |
| 87 | PIIMaskingFilter estruturado em logs (structlog) | ❌ | ✅ `install_global_pii_masking()` em workers Celery (SEG-3A) + `strip_pii_for_llm_prompt()` em 6 callers LLM + `response_filter.py` + Sentry PII scrubbing | 🔵 | ✔ Concluído | `libs/config/lia_config/celery_app.py` + `app/shared/pii_masking.py` | LGPD — masking de CPF, email, tel, RG, CNPJ em prompts e logs. Global filter root logger instalado. |
| 88 | Prompt injection guard (inputs do recrutador) | ❌ | ✅ `app/shared/robustness/input_validation.py` + `sanitize_text()` | 🔵 | ✔ Concluído | `app/shared/robustness/input_validation.py` | Guard ativo em inputs de recrutador. Detecção de linguagem (PT-BR, EN, ES, FR) |
| **SPRINTS Z + F1-02/F1-03/F2-04 — RESILIÊNCIA E ARQUITETURA AVANÇADA** | | | | | | | |
| 94 | Decomposição Kanban/Pipeline em subagentes (Z1) | ❌ classes monolíticas | ✅ supervisor + 6 workers especializados | — | ✔ Concluído | `app/domains/kanban/agents/` + `app/domains/pipeline/agents/` | Sprint Z1 — cada subagente 7–9 tools (dentro do limite seguro); padrão supervisor+workers |
| 95 | LearningSnapshotService — rollback (Z2-01) | ❌ | ✅ snapshots versionados do loop de aprendizado | — | ✔ Concluído | `app/shared/learning/learning_snapshot_service.py` | Permite rollback a snapshot anterior se padrões aprendidos causarem degradação |
| 96 | Contextos YAML versionados (Z3-02) | ❌ | ✅ `version` + `updated_at` em 9 YAMLs | — | ✔ Concluído | `libs/contexts/*.yaml` | Rastreabilidade de mudanças em prompts de contexto sem redeployar código |
| 97 | PolicySetupAgent shim + canonical (Z5-02) | ❌ | ✅ shim com DeprecationWarning | — | ✔ Concluído | `app/domains/policy/agents/agent.py` | Fonte canônica unificada; uso legado emite warning |
| 98 | Threshold semântico configurável (Z5-03) | ❌ | ✅ `ROUTER_VECTOR_SIMILARITY_THRESHOLD=0.92` + A/B flag | — | ✔ Concluído | `app/orchestrator/cascaded_router.py` | Near-miss logging + flag `ROUTER_VECTOR_CACHE_ENABLED` para A/B |
| 99 | ATS clients unificados — shims (Z6-01) | ❌ duplicação | ✅ shims re-exportando da fonte canônica | — | ✔ Concluído | `app/domains/ats_integration/services/ats_clients/` | Duplicação eliminada; domínio usa `services/ats_clients/` como fonte única |
| 100 | OpenTelemetry OTLP (Z6-02) | ❌ | ✅ `_try_init_otlp()` + `@trace_span` em 3 services críticos | — | ✔ Concluído | `app/shared/tracing.py` | Exporta spans para OTLP backend; fallback gracioso para LightweightTracer |
| 101 | Presidio NER Layer 4 PII (Z6-03) | ❌ | ✅ Layer 4 controlada por flag | — | ✔ Concluído | `app/shared/pii_masking.py` | Microsoft Presidio NER: detecta entidades nomeadas além de regex — `LLM_PROMPT_PRESIDIO_ENABLED` |
| 102 | RecruiterBehaviorService (Z7-01) | ❌ | ✅ perfil comportamental Redis + DB | — | ✔ Concluído | `app/services/recruiter_behavior_service.py` | active_hours, sourcing_channels, stage_conversion_rates, communication_style; 500 sinais TTL 7d |
| 103 | FairnessGuard no learning loop (F1-02) | ❌ | ✅ validação batch antes de aplicar padrões | — | ✔ Concluído | `app/shared/learning/learning_loop_service.py` | Bloqueia padrões com viés antes de persistir no loop de aprendizado |
| 104 | SLOs formais no circuit breaker (F1-03) | ❌ | ✅ SLO breaches + degraded mode responses | — | ✔ Concluído | `app/shared/resilience/circuit_breaker.py` | SLOs formais documentados; respostas degradadas retornam JSON padronizado |
| 105 | Dead Letter Queue Celery (F2-04) | ❌ | ✅ DLQService Redis LIST + 4 endpoints admin | — | ✔ Concluído | `app/shared/resilience/dlq_service.py` + `app/api/v1/admin_dlq.py` | Cap 1000, TTL 7d, PII masking, Bell notification para tasks críticas |
| **PENDENTES / EM ABERTO** | | | | | | | |
| 89 | Separação de APIs por domínio (api-funil first) | ❌ | ⚠️ scaffold existe | 🔵 | 🔴 Alta | `apps/api-funil/` (scaffold) | Threshold: p95 CRUD > 500ms. Comunicação via RabbitMQ events |
| 90 | tsvector FTS em CVs (antes de Elasticsearch) | ✅ pg_trgm | ⚠️ pgvector sem tsvector | 🔵 | 🟡 Média | `app/services/rag_pipeline_service.py` (decisão pendente) | PoC Sprint C documentado; decisão: adotar se cobre 80% dos casos |
| 91 | Coverage: 29%+ → 40% → 80% | — | ✅ gate 30% atendido (29%+ atual) | — | ✔ Concluído | `pytest.ini` + `lia-agent-system/tests/` | Sprints Y–Z elevaram para 4.600+ testes; gate 30% atendido com 29%+. Próximo: 40% |
| 92 | Métricas por versão de prompt | ❌ | ⚠️ registry existe, métricas não | 🔵 | 🟡 Média | `app/services/prompt_version_registry.py` | prompt_version_registry.py criado; falta: latência/custo/satisfaction por versão |
| 93 | OpenSearch/Elasticsearch para log aggregation | ❌ | ❌ não implementado | 🔵 | 🟢 Baixa | — (ADR-002 Phase 2) | ADR-002 Phase 2 — logs centralizados de todos os agentes com query por intent/agente/user_id |

---

## 1. Contexto e Propósito

O **recruiter_agent_v5** é um projeto Python desenvolvido em paralelo à LIA, como produto independente de recrutamento por IA voltado para ATS (Ruby on Rails). Apesar de diferentes em propósito e stack, compartilham conceitos fundamentais: DomainPrompt ABC, DomainRegistry, DomainWorkflow LangGraph, ConversationMemory, e integração com sistemas de recrutamento via APIs REST e RabbitMQ.

O propósito desta análise é:
- Entender o que cada sistema faz melhor
- Identificar os gaps reais de cada lado
- Definir qual arquitetura serve de referência para a evolução da LIA
- Embasar a decisão sobre a criação de um Main Orchestrator unificado
- Incorporar as recomendações do André (arquiteto sênior externo) com mapeamento de status

**Contexto da revisão do André:** André revisou o projeto como consultor de arquitetura independente. Suas recomendações foram discutidas com Victor (Tech Lead da WeDOTalent) em sessão de revisão arquitetural. Os pontos de acordo e discordância estão anotados nas seções pertinentes.

---

## 2. Visão Geral dos Dois Sistemas

### recruiter_agent_v5

| Aspecto | Detalhe |
|---------|---------|
| **Repositório** | talensestg/recruiter_agent_v5 (privado) |
| **Linguagem** | Python 3.x |
| **LLM Principal** | Google Gemini 2.5 Flash |
| **Framework** | LangGraph + LangChain |
| **Transporte** | RabbitMQ-first + CLI |
| **Domínios** | 2 (sourced_profile_sourcing + evaluation) |
| **Agentes** | 6 especializados por domínio + 6 do pipeline global |
| **Banco** | PostgreSQL (pgvector + pg_trgm) + Redis |
| **Multi-tenant** | Não implementado |
| **Compliance** | FairnessGuard básico |

### LIA Platform

| Aspecto | Detalhe |
|---------|---------|
| **Repositório** | WeDOTalent/lia-agent-system |
| **Linguagem** | Python 3.11 |
| **LLM Principal** | Claude Sonnet 4.5 (Anthropic) |
| **Framework** | LangGraph + LangChain + Celery |
| **Transporte** | REST-first + WebSocket + RabbitMQ |
| **Domínios** | 11 DDD + 10 WS domains roteados (wizard, talent, pipeline, kanban, sourcing, jobs_management, policy, analytics, communication, ats_integration) |
| **Agentes** | 10 ReAct nativos (4-file pattern, inclui AutomationReAct) + 3 graph agents + 6 subagentes Z1 (Kanban/Pipeline supervisor+workers) |
| **Banco** | PostgreSQL (Neon + pgvector) + Redis + RabbitMQ |
| **Multi-tenant** | Sim — company_id em todos os modelos e queries |
| **Compliance** | FairnessGuard 3 camadas + LGPD + SOX + ISO 27001 + BCB 498 + EU AI Act + Bias Audit + Drift Detection |
| **Monorepo** | UV workspace — 9 libs (config, utils, models, audit, messaging, agents-core, services, contexts, auth) |
| **Infra** | Docker Compose 10 serviços + Celery high/normal/low + beat + Flower + Grafana + Sentry |
| **Float Chat** | LiaChatPanel WebSocket + use-float-streaming.ts + HITLConfirmCard + navigation_intent.py — Sprint J (09/03/2026) |
| **Testes** | 4.600+ testes coletados (pytest) + Vitest FE + pirâmide 5-camadas |
| **Coverage** | 29%+ atual — gate 30% (Sprints Y–Z, 15–19/03/2026) |

> **Nota de contexto:** O André revisou apenas o v5 e um subconjunto da LIA. Algumas das recomendações do guia dele já foram implementadas na LIA antes da revisão — o mapeamento completo está na seção 20.

---

## 3. Arquitetura de Entry Points

### recruiter_agent_v5 — Entry Point Único

```
main.py
├── RecruiterAgentCLI      → WorkflowOrchestrator.process_query(question)
└── RecruiterAgentWorker   → MessageRouter.route({question, domain, context_data})
```

**Fluxo RecruiterAgentWorker:**
1. Mensagem chega via RabbitMQ
2. `handle_message()` extrai `question`, `domain`, `sourcing_id`, `context_data`
3. Chama `MessageRouter.route()` — ponto único de entrada
4. Após processamento, envia callback para Rails via `send_to_rails_callback()`

**Ponto forte:** qualquer input — CLI, RabbitMQ, futuro HTTP — passa pelo mesmo `MessageRouter`. Previsível, testável, sem duplicação de lógica de orquestração.

---

### LIA — Entry Points Fragmentados

```
app/api/v1/
├── orchestrated_job_chat.py          → wizard (job creation flow)
├── orchestrated_talent_chat.py       → talent funnel / sourcing (500+ linhas, 7 fases internas)
├── pipeline_orchestrator.py          → pipeline / CV screening
├── sourcing_orchestrator.py          → sourcing direto
├── wizard_smart_orchestrator.py      → segunda versão do wizard
└── agent_chat_ws.py                  → WebSocket (streaming)

app/api/orchestrator_routes.py        → POST /api/orchestrator/process
                                         (existe, mas não é o caminho principal)
app/orchestrator/orchestrator.py      → Orchestrator class
                                         (existe, mas é bypassed pelos endpoints acima)
```

**Problema:** cada contexto de chat tem seu próprio orquestrador parcial. O `Orchestrator` principal com `CascadedRouter` + `DomainWorkflow` existe e está bem implementado, mas o produto não o usa como caminho principal. Os endpoints orquestram diretamente, duplicando lógica e criando inconsistências.

**Exemplo real — `orchestrated_talent_chat.py`:**
```
FASE 1: pending_action check
FASE 2: actionable intent (action types específicos)
FASE 3: analytical routing (datasets/reports)
FASE 4: action executor direto
FASE 5-7: fallback para Orchestrator.process_request()
```
Resultado: lógica de roteamento espalhada em 7 fases dentro de um único endpoint de 500 linhas.

> **André recomenda:** entry point único — qualquer canal (REST, WS, RabbitMQ) deve passar pelo mesmo orquestrador central antes de chegar nos agentes.
> **Status na LIA:** ✅ Implementado — `MainOrchestrator` criado e ativo (Fase 1). Endpoints refatorados para thin adapters (Fase 2): `orchestrated_talent_chat.py`, `orchestrated_job_chat.py`, `pipeline_orchestrator.py` → 30 linhas cada, delegam para `MainOrchestrator`. WS também conectado via `agent_chat_ws.py`. 100% das mensagens passam pelo orquestrador central.
> **Status no v5:** ✅ Implementado — `MessageRouter` é o único entry point. Toda mensagem (RabbitMQ ou CLI) passa por `MessageRouter.route()` antes de qualquer agente. É o padrão que André descreve, funcionando.
> **Onde LIA:** `app/orchestrator/main_orchestrator.py`, `app/orchestrator/context_adapter.py`. **Onde v5:** `main.py → RecruiterAgentWorker → MessageRouter`.
> **Gap LIA:** nenhum gap crítico. **Gap v5:** entry point único cobre RabbitMQ/CLI mas sem REST/WS unificado.

---

## 4. Sistema de Roteamento

### recruiter_agent_v5 — MessageRouter (3 caminhos)

```python
class MessageRouter:
    def route(self, payload: dict) -> dict:
        domain = payload.get("domain")
        if domain:
            return DomainOrchestrator.process_query(domain, question, context_data)
        else:
            return WorkflowOrchestrator.process_query(question)
```

**Com domain** → `DomainOrchestrator` → `DomainWorkflow` (LangGraph 3 nós)
**Sem domain** → `WorkflowOrchestrator` → pipeline global 6 agentes

**RouterAgent interno (dentro do domínio sourcing) — 3 estratégias em cascata:**

| Estratégia | Cobertura | Tempo Médio |
|-----------|-----------|-------------|
| Memory Patterns | pronomes, posições, shortlist | 0-50ms |
| Fast Routing | keywords + regex + scoring | 50-100ms |
| LLM Routing | Gemini decide o agente | 200-500ms |

> ~80% das queries resolvidas por Fast Routing, ~15% por Memory, ~5% por LLM.

---

### LIA — CascadedRouter (6 tiers)

```
Tier 0: MemoryResolver      — pronomes/referências via WorkingMemory
Tier 1: LRU in-process      — hash MD5, O(1), sem I/O
Tier 2: Redis hash cache    — distribuído, exato, TTL configurável
Tier 3: VectorSemanticCache — pgvector cosine_similarity >= 0.92
Tier 4: FastRouter          — regex patterns 12+ domínios (DOMAIN_PATTERNS)
Tier 5: LLMCascade          — Haiku (>0.80) → Sonnet (>0.70) → Opus (fallback)
Fallback: clarification_needed → pergunta ao usuário
```

**Vantagem sobre o v5:** o roteamento da LIA é significativamente mais sofisticado:
- Cache semântico com pgvector em vez de hash MD5 por query
- Redis distribuído (funciona em múltiplos workers/pods)
- Escada de custo LLM (economiza tokens usando Haiku quando confidence alta)
- Clarification fallback explícito em vez de silently falhar

**Desvantagem:** esse roteador sofisticado não é o caminho real das requisições. Cada endpoint bypassa parte (ou toda) essa lógica.

> **André recomenda:** orquestrador com escada de custo — Tier 0 (resolução de referências, ~0 custo, cobre 15-25%), Tier 1 (cache hash), Tier 2 (regex scoring), Tier 3 (LLM cascata) + cache semântico antes do Tier LLM (embeddings, similaridade >0.95, reduz LLM 40-60%).
> **Status na LIA:** ✅ Implementado — LIA tem 6 tiers, ainda mais sofisticado que o modelo do André: Redis hash (Tier 2), VectorSemanticCache pgvector (Tier 3), LLMCascade Haiku→Sonnet→Opus.
> **Status no v5:** ⚠️ Parcial — RouterAgent tem 3 estratégias em cascata (Memory→Fast→LLM), que corresponde à estrutura básica recomendada. Mas: cache é hash MD5 (sem semântica), Redis não é usado para cache de rotas, e a escada de custo LLM não existe (usa Gemini Flash sempre).
> **Onde LIA:** `app/orchestrator/cascaded_router.py`, `app/services/vector_semantic_cache.py`. **Onde v5:** `MultiAgentOrchestrator`, `RouterAgent` (`orchestrators/router_agent.py`).
> **Gap LIA:** ✅ Resolvido — `MainOrchestrator` garante que todo tráfego passa pelo `CascadedRouter` 6 tiers (Fase 2, thin adapters). Roteador sofisticado está ativo no caminho principal. **Gap v5:** cache MD5 não cobre variações semânticas da mesma query; sem escada de custo LLM; sem Redis distribuído (não escala para múltiplos workers).

---

## 5. Sistema de Domínios

### Contrato Base — Ambos usam DomainPrompt ABC (idêntico em conceito)

**recruiter_agent_v5 — `DomainPrompt` ABC:**
```python
class DomainPrompt(ABC):
    domain_id: str
    domain_name: str
    description: str

    def get_allowed_actions(self) -> List[DomainAction]: ...
    def get_system_prompt(self) -> str: ...
    def process_intent(self, query, context) -> IntentResult: ...   # LLM → {action_id, params, confidence}
    def execute_action(self, action_id, params, context) -> DomainResponse: ...
    def validate_context(self, context) -> ValidationResult: ...
    def get_suggestions(self) -> List[str]: ...
```

**LIA — `DomainPrompt` ABC (app/domains/base.py):**
```python
class DomainPrompt(ABC):
    domain_id: str
    domain_name: str
    description: str

    def get_allowed_actions(self) -> List[DomainAction]: ...
    def get_system_prompt(self) -> str: ...
    def process_intent(self, query, context) -> IntentResult: ...
    def execute_action(self, action_id, params, context) -> DomainResponse: ...
    def validate_context(self, context) -> ValidationResult: ...
    def get_suggestions(self) -> List[str]: ...
```

**São praticamente idênticos.** Esse é o ponto de alinhamento mais importante entre os dois sistemas — a fundação está no mesmo lugar.

---

### DomainWorkflow — Diferença de Profundidade

**v5 — 3 nós (simples):**
```
analyze_intent → execute → format
```

**LIA — 7 passos (rico):**
```
PRE_CHECK → RESOLVE_REFERENCES → SMART_EXTRACT → ANALYZE_INTENT → EXECUTE → FORMAT → POST_CHECK
```

| Passo LIA | Função |
|-----------|--------|
| PRE_CHECK | Validação de context, rate limiting, policy check |
| RESOLVE_REFERENCES | Resolve pronomes e referências anteriores na query |
| SMART_EXTRACT | SmartExtractor: regex rápido + LLM fallback para params |
| ANALYZE_INTENT | process_intent() via LLM → {action_id, params, confidence} |
| EXECUTE | execute_action() → DomainResponse |
| FORMAT | TemplateFormatter / formatação específica por domínio |
| POST_CHECK | FairnessGuard, PII check, audit log |

**Vantagem LIA:** o pipeline é mais robusto, com compliance embutido (PRE_CHECK + POST_CHECK) e resolução de referências antes do intent analysis.

> **André recomenda:** contextos de agentes versionados no repositório (não em banco), separados por domínio em `libs/contexts/`, com prompts YAML e code review + rollback.
> **Status na LIA:** ✅ Implementado — `libs/contexts/` com 9 domínios (wizard, pipeline, pipeline_transition, sourcing, kanban, talent, jobs_mgmt, policy, automation). Prompts YAML por domínio, versionados via git.
> **Status no v5:** ❌ Não implementado — prompts estão em código Python hard-coded dentro dos métodos `get_system_prompt()` de cada agente e domínio. Nenhum YAML, nenhuma separação de contexto, nenhum changelog. Mudança de prompt = mudança de código = deploy.
> **Onde LIA:** `libs/contexts/` (9 módulos). **Onde v5:** inline nos arquivos de cada agente (`BaseAgent.get_system_prompt()`, `DomainPrompt.get_system_prompt()`).
> **Gap LIA:** changelog de versão e métricas por versão de prompt ainda não implementados (ver seção 21, item P3). **Gap v5:** adotar estrutura de contextos separados seria trabalho significativo de refatoração.

---

### Domínios Implementados

**v5 — 2 domínios:**
| Domínio | Ações | Agentes |
|---------|-------|---------|
| sourced_profile_sourcing | 30+ | SearchAgent, AnalyticsAgent, DetailAgent, ComparisonAgent, ReportAgent, ActionAgent |
| evaluation | LangGraph 4 nós | classify_input → evaluate → decide_flow → craft_message |

**LIA — 11 domínios:**
| Domínio | Ações | Status |
|---------|-------|--------|
| job_management | 30+ (create, wizard, enrich, publish, analytics) | ReAct |
| sourcing | 30+ (search, semantic, boolean, compare, contact, export) | ReAct |
| cv_screening | 30+ (triagem, WSI, rank, feedback) | ReAct |
| pipeline | transitions, kanban, analytics | ReAct |
| analytics | KPIs, reports, charts | Legacy |
| communication | email, teams, whatsapp | Legacy |
| interview_scheduling | agendamento, entrevistas | Legacy |
| automation | task planner, automações | Legacy |
| ats_integration | sync bidirecional | Arquivado (NotImplementedError) |
| hiring_policy | regras, compliance | ReAct |
| recruiter_assistant | fallback geral | Ativo |

---

## 6. Camada de Agentes

### recruiter_agent_v5 — BaseAgent ABC + Agentes Especializados

```python
class BaseAgent(ABC):
    llm: ChatGoogleGenerativeAI  # lazy-loaded
    validator: DataValidator
    fact_checker: FactChecker

    # Helpers compartilhados
    def get_api_client(self) -> SourcingAPIClient: ...
    def _call_llm(self, system_prompt, user_message) -> str: ...
    def _parse_json_response(self, content) -> Dict: ...
    def _fetch_candidates(self, context, limit, order, where) -> List[Dict]: ...
    def _validate_and_correct_params(self, params, context) -> Tuple: ...

    # Abstratos
    @property
    def agent_id(self) -> str: ...
    def get_system_prompt(self, context: DomainContext) -> str: ...
    def process(self, query, context, aggregated_stats, params) -> AgentResponse: ...
```

**6 agentes implementados:**

| Agente | Linhas | Especialidade |
|--------|--------|--------------|
| SearchAgent | 797 | Busca por skill, termo livre, embeddings, FairnessGuard |
| AnalyticsAgent | 592 | Contagens, médias, distribuições, diversidade |
| DetailAgent | 301 | Perfil completo, análise LIA, histórico |
| ComparisonAgent | 873 | Comparação N candidatos, tabela + recomendação LLM |
| ReportAgent | 529 | Relatório executivo, top candidatos, anonymize_for_llm |
| ActionAgent | 728 | Converter perfil, criar applies, listas, atualizar, remover |

**Modelo de decisão — MultiAgentOrchestrator:**
```
Query chega
  │
  ├─ _analyze_query_complexity() → detecta padrão QUERY_PATTERNS?
  │   ├─ SIM → ExecutionPlan multi-etapa → _execute_plan()
  │   └─ NÃO → RouterAgent.process()
  │               ├─ Memory patterns → resolve referência
  │               ├─ Fast route → keywords/patterns → agente
  │               └─ LLM route → Gemini decide agente
  └─ AgentResponse → DomainResponse
```

**Ponto forte:** agentes especializados com responsabilidade clara. O `ComparisonAgent` só compara, o `SearchAgent` só busca. Cada um tem seu `system_prompt` específico e helpers compartilhados.

---

### LIA — ReAct Agents (LangGraph Native) + Legacy

**Arquitetura ReAct (7 agentes):**
```python
class LangGraphReActBase:
    """Agente ReAct nativo com create_react_agent + streaming."""

    def _build_langgraph(self):
        tools = self._get_domain_tools()
        self._compiled_react = create_react_agent(
            self.llm,
            tools=tools,
            checkpointer=get_checkpointer()
        )

    def _invoke_react(self, state, streaming_callback=None):
        # Thought → Action → Observation loop
        # LLM decide qual tool usar e quando parar
        ...
```

**Agentes ReAct ativos:**
| Agente | Tools | Domínio |
|--------|-------|---------|
| WizardReAct | 9 tools (criar, enriquecer, salary, WSI, publicar...) | job_management |
| PipelineReAct | 14 tools (triagem, score, mover, feedback, agendar...) | cv_screening |
| SourcingReAct | 14 tools (buscar, comparar, filtrar, contatar...) | sourcing |
| PolicyReAct | 13 tools (regras, exceções, compliance...) | hiring_policy |
| KanbanReAct | tools de kanban e pipeline visual | pipeline |
| TalentReAct | tools de funil de talentos | sourcing/talent |
| JobsManagementReAct | tools de gestão de vagas | job_management |

**Graph Agents (LangGraph StateGraph):**
- `JobWizardGraph` — 6 nós, state machine para criação de vagas
- `WSIInterviewGraph` — entrevistas WSI com scoring
- `InterviewGraph` — entrevistas gerais

**Diferença fundamental entre os dois paradigmas:**

| | v5 BaseAgent | LIA ReAct Agent |
|--|-------------|-----------------|
| Decisão de tool | Código decide (if/else, RouterAgent) | LLM decide (raciocina pela descrição) |
| Loop de raciocínio | Single call por ação | Thought → Action → Observation (iterativo) |
| Flexibilidade | Previsível, limitado ao que foi programado | Autônomo, resolve queries não previstas |
| Custo | 1 chamada LLM por ação | 1-5 chamadas (dinâmico) |
| Debuggability | Alta (fluxo determinístico) | Média (depende do raciocínio do LLM) |

**Ponto forte da LIA:** os ReAct agents são genuinamente autônomos. O LLM decide qual tool chamar, em que ordem, e quando parar. Isso é uma geração acima dos "agentes" do v5, que são na prática funções com prompts.

> **André recomenda (fluxos imprevisíveis — ReAct):** create_react_agent ou custom ReAct com StateGraph para mais controle. TimedToolNode com asyncio.wait_for timeout (15s por tool). Resposta forçada se max_iterations esgota. Confiança calculada via taxa de sucesso de tools.
> **Status na LIA:** ✅ Implementado — 7 agentes ReAct nativos via `LangGraphReActBase`, `create_react_agent` do LangGraph, resposta forçada quando max_iterations esgota, streaming nativo via WebSocket.
> **Status no v5:** ❌ Não implementado como ReAct — os agentes do v5 (`BaseAgent`) são classes com `process()` e `_call_llm()`. O LLM gera uma resposta, não decide qual tool chamar. Não é ReAct: não há loop Thought→Action→Observation, sem tool selection autônoma, sem max_iterations. O `MultiAgentOrchestrator` decide qual agente invocar — não o LLM.
> **Onde LIA:** `app/shared/agents/langgraph_react_base.py`, `libs/agents-core/`. **Onde v5:** `agents/base_agent.py`, `orchestrators/multi_agent_orchestrator.py`.
> **Gap LIA:** ✅ TimedToolNode com timeout explícito implementado no Sprint A (`libs/agents-core/timed_tool_node.py` — `asyncio.wait_for(tool_call, timeout=15s)` + `ToolError("timeout")` fallback). **Gap v5:** adotar ReAct genuíno exigiria reescrever os 6 agentes especializados — mudança arquitetural significativa.

> **André recomenda (fluxos previsíveis — Graph):** StateGraph + TypedDict + PostgresSaver + conditional edges. Streaming nativo via .astream(). Human-in-the-loop com interrupt_before/after. LangGraph Studio para debug.
> **Status na LIA:** ✅ Implementado — JobWizardGraph, WSIInterviewGraph, InterviewGraph com StateGraph + TypedDict. PostgresSaver ativo (USE_LANGGRAPH_NATIVE=True). LangGraph Studio configurado via `langgraph.json`.
> **Status no v5:** ⚠️ Parcial — DomainWorkflow usa LangGraph com 3 nós (analyze_intent → execute → format), mas: sem TypedDict explícito como state, sem PostgresSaver (apenas MemorySaver), sem interrupt_before/after, sem LangGraph Studio configurado.
> **Onde LIA:** `app/domains/job_management/graphs/`, `app/domains/cv_screening/graphs/`, `langgraph.json`. **Onde v5:** `domains/sourced_profile_sourcing/workflow.py` (`DomainWorkflow`).
> **Gap LIA:** ✅ Human-in-the-loop totalmente implementado — Sprint C (interrupt_before em 3 fluxos críticos), Sprint F1 (persistência DB: `hitl_pending_actions` + `hitl_audit_trail`), Sprint J (`HITLConfirmCard.tsx` WebSocket streaming). **Gap v5:** state não tipado, checkpoints não persistidos em DB (perda de sessão em restart), sem Studio para debug.

---

## 7. Memória Conversacional

### recruiter_agent_v5 — ConversationMemory Rica

```python
@dataclass
class ConversationMemory:
    last_candidates_shown: List[int]        # última lista exibida (max 20)
    last_candidate_detailed: Optional[int]  # último candidato detalhado
    detailed_history: List[int]             # histórico de detalhamentos
    shortlist: List[int]                    # favoritos do usuário
    mentioned_candidates: Dict[str, int]    # nome → id (fuzzy match)
    active_filters: Dict[str, Any]          # filtros ativos
    last_search_term: Optional[str]
    last_action: Optional[str]
    last_job_id: Optional[int]
    last_job_name: Optional[str]
```

**Métodos de resolução de referência:**
```python
def resolve_reference(self, query: str) -> Optional[int]:
    # Tenta pronome → posição → anterior → nome
    if self._is_pronoun(query):        # "e ele?", "fale sobre ela"
        return self.last_candidate_detailed
    if self._is_position(query):       # "o primeiro", "o terceiro"
        return self._resolve_by_position(query)
    if self._is_previous(query):       # "o anterior"
        return self.detailed_history[-1] if self.detailed_history else None
    return self._fuzzy_match_name(query)  # "o João"

def should_keep_filters(self, query: str) -> bool:
    # Detecta continuação: "desse grupo", "dentre eles", "dos anteriores"
    continuity_keywords = ["desse grupo", "dentre eles", "dos anteriores", ...]
    return any(kw in query.lower() for kw in continuity_keywords)
```

**Paginação explícita:**
```python
def get_pagination_context(self) -> Optional[Dict]:
    # "próxima página", "página 3", "ver mais"
    # Retorna offset + filters da query anterior para continuidade
    ...
```

---

### LIA — ConversationState (estrutura similar, resolução menos rica)

```python
@dataclass
class ConversationState:
    last_candidates_shown: List[int]       # igual ao v5
    last_candidate_detailed: Optional[int] # igual ao v5
    detailed_history: List[int]            # max 10
    shortlist: List[int]                   # max 50
    mentioned_candidates: Dict[str, int]   # igual ao v5
    active_filters: Dict[str, Any]
    last_search_term: Optional[str]
    last_action: Optional[str]
    last_job_id: Optional[int]
    last_domain_id: Optional[str]          # + campo que v5 não tem
    last_results_count: Optional[int]      # + campo que v5 não tem
```

**O que a LIA tem que o v5 não tem:**
- `last_domain_id` — rastreia qual domínio foi usado
- `last_results_count` — conta resultados para sugestões
- Persistência em banco de dados (ConversationMemory via SQLAlchemy)
- Histórico de mensagens para LLM com summarização automática

**O que foi implementado na LIA (Fase 1 MainOrchestrator + Sprint F4):**
- ✅ Resolução de pronomes ("e ele?", "fale sobre ela") — `MemoryResolver` expandido
- ✅ Resolução por posição ("o terceiro") — implementado na Fase 1
- ✅ `should_keep_filters()` — continuidade de filtros ativa
- ✅ Paginação conversacional explícita — implementada
- ✅ Shortlist como feature explícita — `short_list_service.py` + DB (Sprint F4)

---

## 8. Planos Multi-Etapa

### recruiter_agent_v5 — QUERY_PATTERNS + ExecutionPlan

**8 padrões pré-definidos (regex):**
```python
QUERY_PATTERNS = {
    "apply_top_candidates":   r"(aplique|inscreva).*(top|melhores)",
    "convert_filtered":       r"(converta|adicione).*(filtrados|encontrados)",
    "add_filtered_to_list":   r"(adicione).*(lista)",
    "apply_filtered":         r"(inscreva).*(filtrados)",
    "report_filtered":        r"(relatório).*(filtrados)",
    "compare_filtered":       r"(compare).*(filtrados|encontrados)",
    "detail_best":            r"(detalhes|mostre).*(melhor|top 1)",
    "analyze_skill_holders":  r"(analise).*(têm|possuem|com) (?P<skill>\w+)",
}
```

**ExecutionPlan — tasks com dependências:**
```python
@dataclass
class AgentTask:
    task_id: str
    agent_type: str                  # qual agente executa
    action: str                      # qual ação
    params: Dict[str, Any]
    depends_on: List[str]            # task_ids de dependências
    status: TaskStatus               # PENDING → RUNNING → COMPLETED | FAILED
    result: Optional[AgentResponse]  # resultado para tasks dependentes
```

**Resolução de dependências:**
```
task_0: search.filter(skill="python")    → context_data["filtered_ids"]
task_1: report.generate(ids=task_0.filtered_ids)  ← usa resultado do task_0
```

---

### LIA — PlanDetector + PlanExecutor (mais robusto)

**10+ padrões com contexto de domínio:**
```python
PLAN_PATTERNS = [
    PlanPattern("buscar_e_comparar",   r"(busqu|encontr).*(compar)",   ["sourcing", "sourcing"]),
    PlanPattern("gerar_jd_e_avaliar",  r"(cri|gera).*(avali|score)",   ["job_management", "cv_screening"]),
    PlanPattern("triagem_e_agendar",   r"(triag|avali).*(agend|marqu)", ["cv_screening", "interview_scheduling"]),
    PlanPattern("buscar_e_contatar",   r"(busqu).*(contact|envi)",     ["sourcing", "communication"]),
    # ... +6 padrões
]
```

**PlanExecutor com DAG e context_mappings:**
```python
class PlanExecutor:
    async def execute(self, plan: ExecutionPlan, ...) -> ExecutionPlan:
        # Itera tasks em ordem topológica (DAG)
        # context_mappings: {"task_0.candidate_ids": "task_1.params.ids"}
        # Critical task failure → BLOCKED remaining tasks
        # Final status: COMPLETED | PARTIAL | FAILED
```

**Vantagem LIA:** o PlanExecutor usa DAG real (não sequência linear), suporta `context_mappings` explícitos entre tasks, e tem tratamento de falhas por criticidade. O v5 usa sequência linear com dependências simples.

---

## 9. Sistema de Tools

### recruiter_agent_v5 — YAML-based Tool Registry

```
src/tools/
├── registry.py           # ToolRegistry singleton, indexado por ID/entity/category
├── executor.py           # HttpExecutor + WorkflowExecutor (strategy pattern)
└── documentation/        # Definições YAML das tools
    ├── candidates.yaml
    ├── jobs.yaml
    └── applies.yaml
```

**Características:**
- Definições em YAML — fácil de adicionar sem código
- `HttpExecutor` substitui path params e faz chamadas HTTP ao ATS Rails
- `WorkflowExecutor` orquestra workflows multi-step
- Indexado por `entity_group` e `category` para busca eficiente

**Limitação:** tools são chamadas HTTP ao ATS externo. Não há execução direta de lógica de negócio — tudo passa pela API do ATS Rails. Isso é uma escolha de design (thin agent), não uma limitação técnica.

---

### LIA — ToolRegistry com Claude/Gemini Format Export

```
app/tools/
├── registry.py           # ToolRegistry singleton
├── __init__.py           # initialize_tools(), get_all_tool_schemas()
├── scope_config.py       # PromptScope (TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL)
├── job_wizard_tools.py
├── candidate_tools.py
├── communication_tools.py
├── job_tools.py
├── export_tools.py
├── query_tools.py
└── pipeline_tools.py
```

**ToolDefinition:**
```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters_schema: Dict[str, Any]  # JSON Schema
    handler: Callable[..., Awaitable[Dict[str, Any]]]
    allowed_agents: List[str]

    def to_claude_schema(self) -> Dict: ...   # formato Anthropic
    def to_gemini_schema(self) -> Dict: ...   # formato Google
```

**Vantagem LIA:**
- Tools têm handlers Python reais — executam lógica de negócio, não apenas HTTP
- Exportação em formato nativo para Claude e Gemini
- `PromptScope` filtra tools por contexto (evita tools de vaga no chat de candidatos)
- `allowed_agents` controla quais agentes podem usar cada tool

**Vantagem v5:**
- YAML desacopla definições de código — mais fácil para não-engenheiros editarem
- Estratégia de execução plugável (HttpExecutor / WorkflowExecutor)

---

## 10. Infraestrutura de Serviços

### recruiter_agent_v5

| Serviço | Implementação | Descrição |
|---------|--------------|-----------|
| `SourcingAPIClient` | httpx | HTTP client com retry, auth OTT |
| `SourcingAPIOperations` | Camada alta | search, get_by_id, get_top, aggregated_stats |
| `RAGService` | pgvector + pg_trgm | Busca semântica híbrida para documentação de APIs |
| `AuthService` | JWT + OTT | Login, token cache, one-time tokens |
| `MemoryService` | PostgreSQL | Histórico de conversas + métricas |
| `RabbitMQService` | pika | Publisher/subscriber, mensagens persistentes |
| `StatsManager` | ThreadSafeCache | Cache em memória (TTL, LRU) para aggregated_stats |
| `DataValidator` | fuzzy matching | Valida IDs, resolve nomes por similaridade |
| `FactChecker` | LLM + dados reais | Verifica claims da IA contra dados |
| `SmartExtractor` | regex + LLM | Extração de params com cache MD5 |
| `TemplateFormatter` | templates | Markdown rico com tabelas, emojis, métricas |
| `DynamicPromptBuilder` | builder | Monta prompts com documentação de filtros e ações |
| `FairnessGuard` | regex | Bloqueia filtros por gênero, raça, idade |

**Detalhe sobre FactChecker:**
O v5 tem um `FactChecker` que verifica se a IA afirmou algo correto antes de retornar a resposta — verifica contagens, médias, distribuições contra os dados reais. Isso é anti-alucinação implementado no nível de serviço.

---

### LIA

| Serviço | Implementação | Descrição |
|---------|--------------|-----------|
| `ConversationMemory` | PostgreSQL SQLAlchemy | Histórico + summarização automática |
| `VectorSemanticCache` | pgvector | Cache semântico de routing |
| `ResponseCacheService` | Redis | Cache de respostas por intent |
| `ModelDriftService` | PostgreSQL | Detecção de drift em 4 dimensões |
| `DriftAlertService` | Bell + Teams | Notificação automática de drift |
| `SectorBenchmarkService` | PostgreSQL | Anti-sycophancy via benchmark setorial |
| `BiasAuditService` | PostgreSQL | Four-Fifths Rule em 4 dimensões |
| `LLMService` | Anthropic + fallbacks | Claude Sonnet 4.5 primário |
| `NotificationService` | 5 canais | Bell, Email, Teams, WhatsApp, Chat |
| `FairnessGuard` | 3 camadas | Regex + léxico implícito + LLM opt-in |
| `AuditCallback` | LangSmith + S3 | Auditoria de cada chamada LLM |
| `CheckpointService` | MemorySaver/PostgresSaver | Checkpointing LangGraph |

**Serviços que o v5 não tem:**
- Drift detection e alertas automáticos
- Bias audit com Four-Fifths Rule
- Benchmark setorial (anti-sycophancy)
- Auditoria SOX/ISO 27001 em S3 com lifecycle policy
- Notificações multi-canal (Bell, Teams, WhatsApp)
- Checkpointing de agentes LangGraph

> **André recomenda (bancos de dados):** PostgreSQL (transacional + pgvector + checkpoints LangGraph) + Elasticsearch para busca full-text de CVs (considerar pgvector + FTS antes de adicionar ES) + S3/GCS para audit logs + Redis para cache operacional.
> **Status na LIA:** ⚠️ Parcial — PostgreSQL + pgvector + Redis + S3 implementados. LangGraph checkpoints no PostgreSQL (PostgresSaver). Elasticsearch ainda não implementado.
> **Status no v5:** ⚠️ Parcial — PostgreSQL + pgvector + pg_trgm + Redis implementados (pg_trgm é a alternativa ao ES para busca fuzzy). Sem S3 para audit logs (não tem infraestrutura de auditoria). Sem LangGraph checkpoints persistidos em DB.
> **Onde LIA:** `app/core/database.py`, `app/services/vector_semantic_cache.py`, `libs/audit/`. **Onde v5:** `config/database.py`, `services/vector_service.py`.
> **Gap LIA:** Elasticsearch ou `tsvector` para full-text search em CVs e transcrições WSI (ver seção 21, item P7). **Gap v5:** sem S3 para audit logs (compliance impossível), sem PostgresSaver para checkpoints (sessões não persistem).

---

## 11. Compliance e Governança

### recruiter_agent_v5 — Compliance Básico

| Feature | Status |
|---------|--------|
| FairnessGuard | Regex para filtros discriminatórios (gênero, raça, idade) |
| Anonymize for LLM | Remove dados sensíveis antes de enviar ao LLM (ReportAgent) |
| Injection Detection | `safe_process_input()` no domínio de evaluation |
| OTT Auth | One-time tokens para requests RabbitMQ |
| LGPD | Não implementado |
| SOX/ISO 27001 | Não implementado |
| Bias Audit | Não implementado |
| Drift Detection | Não implementado |

---

### LIA — Stack de Compliance Completo

| Feature | Implementação | Status |
|---------|--------------|--------|
| FairnessGuard Camada 1 | **regex 62 termos** (9 categorias, `_PATTERNS_VERSION=2` — Sprint X1) | Ativo |
| FairnessGuard Camada 2 | léxico implícito | Ativo |
| FairnessGuard Camada 3 | LLM opt-in | Ativo (`FAIRNESS_LAYER3_ENABLED`) |
| Bias Audit | Four-Fifths Rule (gênero, idade, PCD, região) | Ativo |
| BiasAuditSnapshot | histórico auditável SOX | Ativo |
| LGPD | consent management, data requests, portal titular | Ativo |
| SOX | audit logs, S3 lifecycle 7 anos | Ativo |
| ISO 27001 | compliance controls, trust center | Ativo |
| EU AI Act | `ai_act_compliance.py` | Ativo |
| BCB 498 | `bcb498_compliance.py` | Ativo |
| Model Drift Detection | 4 triggers (score, aprovação, custo, latência P95) | Ativo |
| Anti-sycophancy | benchmark setorial injetado nos prompts | Ativo |
| FactChecker | verificação de fatos em avaliações | Ativo |
| AuditCallback | cada chamada LLM auditada | Ativo |

**Gap crítico do v5:** qualquer implantação do v5 em ambiente regulado (financeiro, saúde, governo) precisaria de toda essa camada de compliance construída do zero. Representa meses de trabalho.

> **André recomenda (auditabilidade):** AuditCallback no LangGraph (nenhum nó sabe que está sendo auditado). Separação: PostgreSQL (metadados leves) + S3 (logs completos). Timeline de reconstrução por execution_id.
> **Status na LIA:** ✅ Implementado — AuditCallback integrado via LangGraph config, dual storage PostgreSQL + S3, endpoint de timeline por execution_id, S3 lifecycle 7 anos (SOX).
> **Status no v5:** ❌ Não implementado — o v5 não tem nenhuma infraestrutura de auditoria. Chamadas LLM não são rastreadas, não há AuditCallback, sem dual storage, sem timeline de decisões. Impossível reconstruir o que aconteceu em uma entrevista ou avaliação.
> **Onde LIA:** `libs/audit/audit_callback.py`, `libs/audit/audit_storage.py`, `app/services/audit_timeline_service.py`. **Onde v5:** inexistente.
> **Gap LIA:** Nenhum gap crítico. **Gap v5:** auditoria completa seria pré-requisito para qualquer uso em ambiente regulado (financeiro, saúde, governo) — representa semanas de desenvolvimento.

> **André recomenda (política de retenção):** 90d quente → Glacier → Deep Archive (com tiers definidos).
> **Status na LIA:** ✅ Implementado — S3 lifecycle com 90d Standard → Glacier IR → 365d Deep Archive → 7 anos delete. Celery task mensal para aplicar política automaticamente.
> **Status no v5:** ❌ Não implementado — sem infraestrutura de storage de logs, sem política de retenção. Não relevante hoje (sem audit logs), mas bloqueante para compliance SOX/ISO 27001.
> **Onde LIA:** `app/jobs/celery_tasks.py` (task `audit.apply_lifecycle_policy`), `libs/audit/audit_storage.py`. **Onde v5:** inexistente.
> **Gap LIA:** Tiers podem ser refinados por criticidade do dado (prompts vs metadados vs PII). **Gap v5:** não aplicável até que a auditabilidade (acima) seja implementada.

---

## 12. Observabilidade e Qualidade

### recruiter_agent_v5

| Aspecto | Status |
|---------|--------|
| Logging | structlog com correlation IDs |
| Métricas | Não tem Prometheus/Grafana → [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) |
| Tracing | Não tem LangSmith integrado |
| Testes | pytest + pytest-asyncio |
| CI/CD | Não documentado |
| Coverage | Não configurado |
| LangGraph Studio | Não tem `langgraph.json` |

---

### LIA

| Aspecto | Status |
|---------|--------|
| Logging | structlog + correlation IDs |
| Métricas Prometheus | 5 métricas: router_tier_hit, router_latency_ms, router_confidence, agent_tool_failures, llm_cost_usd |
| LangSmith | AuditCallback integrado |
| LangGraph Studio | `langgraph.json` configurado |
| Testes | 4.600+ testes coletados (pytest) + Vitest FE + pirâmide 5-camadas |
| CI/CD | GitHub Actions com ruff, mypy, vitest, fairness, coverage, LangSmith verify (Sprint F6), bandit SAST |
| Coverage | 29%+ atual — gate 30% (Sprints Y–Z, 19/03/2026) — target 40% |
| OpenTelemetry | Z6-02: OTLP export (`app/shared/tracing.py`) — `@trace_span` em CascadedRouter, DLQ, LearningLoop |
| Bias Audit Baseline | Golden dataset + Four-Fifths Rule tests |
| Snapshot Testing | tests/snapshots/ — Wizard, Pipeline, Remaining (Sourcing, Policy, Kanban, Talent, Jobs) |

> **André recomenda (observabilidade):** Sentry (error tracking), Prometheus + Grafana (métricas operacionais), LangSmith (tracing LangGraph), Celery Flower (workers), logs JSON estruturados. PII masking global nos logs (CPF, email, tel — LGPD). Rate limiting por empresa (budget de tokens/chamadas LLM por tenant).
> **Status na LIA:** ✅ Implementado — Prometheus (5 métricas: Sprint A), Sentry (`app/core/sentry.py`, FastAPIIntegration + CeleryIntegration + PII scrubbing: Sprint B), Grafana (`docker-compose.yml` com provisioning: Sprint B), LangSmith (AuditCallback + CI step Sprint F6), Celery Flower (`mher/flower:2.0` em docker-compose: Sprint D), rate limiting por tenant (`rate_limiter.py` + `token_budget_service.py`: Sprint A), logs JSON estruturados via structlog. **Gap remanescente:** PIIMaskingFilter estruturado no structlog ainda não confirmado (ver item 87 da Tabela Mestra).
> **Status no v5:** ❌ Não implementado — logging básico Python (`logging.getLogger`), sem Prometheus, sem LangSmith, sem Sentry, sem PII masking nos logs, sem rate limiting. Sem multi-tenancy, rate limiting por empresa não é um problema hoje — mas seria bloqueante em produção B2B.
> **Onde LIA:** `app/core/metrics.py` (Prometheus), `app/core/sentry.py` (Sentry), `app/shared/agents/audit_callback.py` (LangSmith), `app/middleware/rate_limiter.py` (rate limiting). **Onde v5:** `utils/logger.py` (logging básico).
> **Gap LIA:** PIIMaskingFilter no structlog (pendente verificação). **Gap v5:** toda a pilha de observabilidade está ausente — crítico para operação em produção. **v9.1: Cards Jira criados para remediação:** [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) (Métricas Prometheus), [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) (AuditCallback), [AUD-006/WT-1511](https://wedotalent.atlassian.net/browse/WT-1511) (REST Timeline).

> **André recomenda (testes de agentes):** fixture LLM gravadas (snapshot testing) para testes determinísticos de agentes.
> **Status na LIA:** ✅ Implementado — `tests/snapshots/` com cobertura completa: Wizard + Pipeline + `test_remaining_agents_snapshots.py` cobrindo Sourcing, Policy, Kanban, Talent, JobsManagement (Sprint D). Todos os 7 agentes ReAct têm snapshot testing.
> **Status no v5:** ❌ Não implementado — sem snapshot testing de agentes. Testes existentes são unitários básicos sem fixtures LLM gravadas. Mudança de prompt não é detectada por testes.
> **Onde LIA:** `tests/snapshots/` (4 arquivos). **Onde v5:** `tests/` (sem subdiretório de snapshots).
> **Gap LIA:** nenhum gap crítico — todos os agentes ReAct cobertos. Próximo: expandir para graph agents (Wizard, WSI, Interview). **Gap v5:** criar infraestrutura de snapshot testing do zero.

---

## 13. Gaps Críticos da LIA

### G1 — Fragmentação de Entry Points (ALTO IMPACTO)

**Problema:** o `Orchestrator` principal com `CascadedRouter` + `DomainWorkflow` existe mas não é o caminho real. Cada contexto de chat tem seu próprio orchestrator parcial com lógica duplicada.

**Consequências:**
- Bugs corrigidos no `Orchestrator` podem não afetar `orchestrated_talent_chat.py`
- Features novas precisam ser implementadas em múltiplos lugares
- Impossível ter telemetria unificada do fluxo completo
- Onboarding de novos devs é confuso ("qual orchestrator devo usar?")

**Arquivos afetados:**
`orchestrated_job_chat.py`, `orchestrated_talent_chat.py`, `pipeline_orchestrator.py`, `sourcing_orchestrator.py`, `wizard_smart_orchestrator.py`

---

### G2 — ReAct Agents Desconectados dos Domínios (ALTO IMPACTO)

**Problema:** os ReAct agents e o sistema de domínios (`app/domains/`) são dois mundos paralelos. Os agentes são chamados diretamente pelos endpoints, não como o `execute` step do `DomainWorkflow`.

**Consequência:** o `DomainWorkflow` com seus 7 passos (incluindo PRE_CHECK e POST_CHECK com FairnessGuard) não é executado quando um ReAct agent responde diretamente. Compliance pode ser bypassado.

---

### ~~G3 — ConversationMemory sem Resolução de Referências~~ ✅ RESOLVIDO (Fase 1 MainOrchestrator)

`MemoryResolver` expandido com resolução de pronomes ("e ele?"), posição ("o terceiro"), continuidade de filtros (`should_keep_filters()`), e paginação conversacional. Implementado como parte da Fase 1 do MainOrchestrator.

---

### G4 — PlanExecutor com Resultado Não Aguardado (MÉDIO IMPACTO)

**Problema (identificado na análise profunda):** quando o `PlanExecutor` delega para um domínio que por sua vez delega para um ReAct agent, o resultado assíncrono pode não ser corretamente aguardado. Silent failure: plano "completa" com resultado parcial.

---

### ~~G5 — Domínios Sem ReAct~~ ✅ RESOLVIDO (Fases 4a/4b/4c/5)

`AnalyticsReActAgent`, `CommunicationReActAgent`, `ATSIntegrationReActAgent` criados seguindo o padrão 4 arquivos e wired no WS dispatcher. Automation tem `AutomationReActAgent` (Sprint G). **Remanescente:** `interview_scheduling` — candidato a ser migrado em Sprint K.

---

### ~~G6 — ATS Integration Arquivado~~ ✅ RESOLVIDO (Fase 5 / P13)

`ATSIntegrationReActAgent` criado com 4 arquivos (`ats_integration_react_agent.py`, `ats_integration_tool_registry.py`, `ats_integration_system_prompt.py`, `ats_integration_stage_context.py`). Wired no WS dispatcher. `useActionIntent` detecta keywords Gupy/Pandapé/importar/sincronizar. 18 contract tests passando.

---

### G7 — APIs de Domínio Não Separadas (MÉDIO IMPACTO)

**Novo gap identificado com as recomendações do André:** `apps/api-vagas`, `apps/api-funil`, `apps/api-onboarding` existem como scaffold no UV monorepo, mas a API principal ainda é monolítica. Picos de evaluation com LLM podem degradar operações CRUD simples que deveriam responder em <200ms.

---

## 14. Gaps Críticos do v5

### V1 — Sem Multi-tenancy (BLOQUEADOR para produto B2B)

O v5 não tem `company_id` em nenhum modelo, query, ou lógica de domínio. Para um produto B2B SaaS multi-tenant, isso é um gap fundamental que exigiria refatoração completa de todos os 30+ domínios/ações.

### V2 — Sem Compliance Stack (BLOQUEADOR para mercados regulados)

LGPD, SOX, ISO 27001, BCB 498 — todos ausentes. Implantação em banco, saúde ou governo seria inviável sem essa camada. Na LIA, essa stack levou meses para ser construída.

### V3 — Sem WebSocket/Streaming (DEGRADAÇÃO DE UX)

O v5 é síncrono/batch. Usuário espera a resposta completa antes de receber qualquer coisa. A LIA faz streaming de tokens em tempo real, o que melhora significativamente a percepção de velocidade.

### V4 — Roteamento Menos Sofisticado (CUSTO OPERACIONAL)

O v5 usa hash MD5 para cache de routing (não semântico). Queries semanticamente similares mas textualmente diferentes são processadas duas vezes com LLM. A LIA usa pgvector (cosine similarity >= 0.92), economizando ~40-60% das chamadas LLM de roteamento.

### V5 — Sem Observabilidade Estruturada (OPERAÇÃO CEGA) → [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512)

Sem Prometheus, sem LangSmith integrado, sem LangGraph Studio. Impossível debugar problemas em produção sem logs textuais. **Card Jira criado:** [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) — Métricas Prometheus para o agente Python V5.

### V6 — Cobertura de Domínios Limitada (FUNCIONALIDADE)

2 domínios vs 11 da LIA. Funcionalidades como agendamento de entrevistas, automação, analytics e comunicação multi-canal simplesmente não existem.

### V7 — Sem Monorepo UV (ESCALABILIDADE DE TIME)

Codebase monolítica sem separação de libs compartilhadas. A migração para UV monorepo que a LIA fez (9 libs) permite deploys separados, versões independentes, e times paralelos.

---

## 15. Síntese Comparativa por Dimensão

| Dimensão | v5 | LIA | Vencedor |
|----------|-----|-----|----------|
| **Clareza arquitetural** | Entry point único, fluxo linear | Fragmentado, múltiplos orchestrators | v5 |
| **Sofisticação de roteamento** | 3 estratégias, cache MD5 | 6 tiers, VectorCache, LLM cascade | LIA |
| **Paradigma de agente** | Classes com métodos mapeados | ReAct nativo (LLM decide) | LIA |
| **Memória conversacional** | Rica (pronomes, posição, shortlist) | Estrutura correta, resolução incompleta | v5 |
| **Compliance** | FairnessGuard básico | Stack completo (LGPD, SOX, Bias Audit) | LIA |
| **Multi-tenancy** | Não tem | Completo (company_id em todos os modelos) | LIA |
| **Cobertura de domínios** | 2 domínios | 11 domínios | LIA |
| **Qualidade do DomainWorkflow** | 3 nós simples | 7 passos com compliance embutido | LIA |
| **Sistema de tools** | YAML, thin, HTTP-only | Python handlers reais, escopados | LIA |
| **Observabilidade** | Logging básico | Prometheus + LangSmith + Studio | LIA |
| **Streaming/UX** | Síncrono/batch | WebSocket + token streaming | LIA |
| **FactChecker/Anti-alucinação** | Ativo (fact_checker embutido) | Implementado | Empate |
| **Maturidade de testes** | Básico | 4.600+ testes coletados (pytest), pirâmide 5 camadas | LIA |
| **Infraestrutura** | RabbitMQ + Redis + Postgres | +Celery, +UV monorepo, +Docker Compose | LIA |
| **WSI / Avaliação proprietária** | Não tem | 12+ arquivos, Bloom, scorer determinístico | LIA |
| **Camada ML/Predição** | Não tem | intelligence_layer, outcome_predictor, drift | LIA |
| **Personalização por recrutador** | Não tem | RecruiterPersonalizationService (invisible) | LIA |
| **Sistema de aprendizado contínuo** | Não tem | 7 padrões, FeedbackLoop, LearningLoop | LIA |
| **Human-in-the-loop estruturado** | Flag `needs_confirmation` | ApprovalRequest (5 tipos, multi-tier) | LIA |
| **Orquestração multi-source** | 1 fonte (ATS via HTTP) | 7 fontes priorizadas + consensus detection | LIA |
| **Explicabilidade** | Não tem | ExplainabilityService, timeline por candidato | LIA |
| **Rastreamento de custo/tenant** | Não tem | TokenTrackingService, alertas 80%/100% | LIA |
| **Cache semântico de IA** | Hash MD5 (exato) | pgvector cosine ≥ 0.92 (Z5-03, configurável via `ROUTER_VECTOR_SIMILARITY_THRESHOLD`) | LIA |
| **A/B testing de prompts** | Não tem | ABTestingService (chi-square, effect_size) | LIA |
| **Sourcing externo ativo** | SearchAgent → ATS local | Pearch AI (190M+), Apify, 13+ serviços | LIA |
| **Comunicação multi-canal** | Não tem (retorna para ATS enviar) | 5 canais + dispatch automático | LIA |

**Placar: LIA vence em 23 de 26 dimensões.**

O v5 vence em apenas 2 dimensões — clareza arquitetural e memória conversacional — que são precisamente os pontos que justificam a proposta do Main Orchestrator (Seção 18). São gaps de orquestração, não de capacidade.

---

## 16. Análise do Fluxo Real de uma Mensagem

### v5 — Fluxo de uma Query de Sourcing

```
1. Mensagem JSON chega via RabbitMQ
   └── {"question": "top 5 candidatos python", "domain": "sourced_profile_sourcing",
        "sourcing_id": 123, "user_id": 456}

2. RecruiterAgentWorker.handle_message()
   └── extrai campos, monta context_data

3. MessageRouter.route()
   └── domain presente → DomainOrchestrator.process_query("sourced_profile_sourcing", ...)

4. DomainOrchestrator
   ├── DomainRegistry.get_instance("sourced_profile_sourcing")
   ├── _build_context() → DomainContext com sourcing_id, user_id
   ├── domain.validate_context() → OK
   ├── domain.ensure_aggregated_stats_sync() → cache/API
   └── DomainWorkflow.process()

5. DomainWorkflow (LangGraph 3 nós)
   ├── analyze_intent: domain.process_intent() → LLM → {action_id: "top_candidates", params: {limit: 5, skill: "python"}}
   ├── execute: domain.execute_action("top_candidates", ...)
   │   └── MultiAgentOrchestrator.process()
   │       ├── _analyze_query_complexity() → não é padrão multi-etapa
   │       └── RouterAgent.process()
   │           ├── Memory: nenhuma referência
   │           ├── Fast: "top 5" → score 8 → SearchAgent
   │           └── SearchAgent.process() → busca API ATS → top 5 candidatos Python
   └── format: TemplateFormatter → Markdown rico

6. DomainResponse retorna → send_to_rails_callback()

Total: ~400-800ms (Fast Routing)
```

---

### ~~LIA — Fluxo Antigo (pré-MainOrchestrator)~~ ✅ RESOLVIDO (Fase 2)

> **Nota:** este era o fluxo problemático antes da Fase 2. Mantido para referência histórica sobre o que foi corrigido.

```
ANTES (problemático):
1. POST /api/v1/orchestrated-talent-chat → 7 fases inline
   └── Bypassa CascadedRouter, DomainWorkflow, PRE_CHECK, POST_CHECK/FairnessGuard
```

**Problema (resolvido):** o `CascadedRouter` com 6 tiers, o `DomainWorkflow` com compliance embutido, e o `Orchestrator` principal eram completamente bypassados. Resolvido na Fase 2 — thin adapters.

---

### LIA — Fluxo Ideal com Main Orchestrator (proposto)

```
1. POST /api/v1/chat (ou WS, ou RabbitMQ — mesmo endpoint)
   └── {"message": "top 5 candidatos python", "context_type": "talent",
        "context_id": "sourcing_123", "company_id": 456}

2. MainOrchestrator.process()
   ├── sanitize + cancellation check
   ├── CascadedRouter.route() → sourcing domain, confidence 0.92
   ├── PlanDetector.detect() → não é multi-step
   ├── PolicyEngine.validate() → OK
   └── DomainWorkflow.process(domain=sourcing, query=...)
       ├── PRE_CHECK: rate limit, policy, company_id validation
       ├── RESOLVE_REFERENCES: MemoryResolver → sem pronomes
       ├── SMART_EXTRACT: params extraction → {skill: "python", limit: 5}
       ├── ANALYZE_INTENT: process_intent() → "top_candidates"
       ├── EXECUTE: SourcingReActAgent.run() → LangGraph ReAct loop
       ├── FORMAT: template + suggestions
       └── POST_CHECK: FairnessGuard, audit log, metrics
   └── retorna resposta via WS streaming

Total: ~500ms-1.2s (similar, mas com compliance garantido)
```

---

## 17. ✅ Caminho B — Main Orchestrator (IMPLEMENTADO — Fases 1–2)

### Conceito (Realizado)

O `MainOrchestrator` é o único entry point real para todas as mensagens, independente do canal (REST, WebSocket, RabbitMQ). Os endpoints específicos por contexto são thin adapters que montam contexto e delegam.

### O que mudou (implementado)

```
ANTES (problemático):
endpoint específico → chama agente diretamente (bypassa orchestrator)

AGORA (Fases 1–2):
endpoint específico (thin adapter) → MainOrchestrator → CascadedRouter → DomainWorkflow → ReAct Agent
```

### O que permaneceu intacto

- DomainPrompt ABC e DomainRegistry — sem mudanças
- CascadedRouter 6 tiers — sem mudanças
- DomainWorkflow 7 passos — sem mudanças
- Todos os ReAct agents — chamados via DomainWorkflow.EXECUTE (compliance garantido)
- Stack de compliance — garantidamente executada em 100% dos fluxos
- ConversationMemory DB-backed — sem mudanças

### O que foi incorporado do v5 (Fases 1–2)

- ✅ `ContextAdapter` (`app/orchestrator/context_adapter.py`) — converte contexto de qualquer canal para `DomainContext` unificado (inspirado no `handle_message()` do v5)
- ✅ `MemoryResolver` expandido — pronomes, posição, continuidade de filtros (do v5)
- ✅ `should_keep_filters()` — continuidade de filtros ativos
- ✅ Paginação conversacional explícita

### Estrutura implementada

```
app/orchestrator/
├── main_orchestrator.py        ← entry point único ✅
├── context_adapter.py          ← normaliza contexto de qualquer canal ✅
├── cascaded_router.py          ← existente, sem mudanças ✅
├── orchestrator.py             ← Orchestrator.process_domain() ✅
├── memory_resolver.py          ← expandido com pronomes/posição ✅
└── ...

app/api/v1/
├── orchestrated_job_chat.py    ← thin adapter (~30 linhas) ✅
├── orchestrated_talent_chat.py ← thin adapter (~30 linhas) ✅
├── pipeline_orchestrator.py    ← thin adapter (~30 linhas) ✅
└── agent_chat_ws.py            ← conectado ao MainOrchestrator via WS ✅
```

> **André recomenda:** comunicação entre APIs via eventos (RabbitMQ topic exchange), não HTTP síncrono inter-serviço. Aplicável quando as APIs de domínio estiverem separadas.
> **Status na LIA:** ⚠️ Parcial — infraestrutura RabbitMQ pronta (`platform_events.py`, `rabbitmq_producer.py`), mas APIs ainda são monolíticas. O padrão não está sendo usado entre serviços ainda.
> **Status no v5:** ✅ Implementado e em uso ativo — RabbitMQ é o transport principal do v5. `RecruiterAgentWorker` consome fila RabbitMQ, processa e responde via callback para o Rails. É o padrão que André recomenda, operando hoje. HTTP REST é secundário no v5.
> **Onde LIA:** `app/services/platform_events.py`, `app/services/rabbitmq_producer.py` (pronto, não ativado). **Onde v5:** `main.py → RecruiterAgentWorker`, `utils/rabbitmq_client.py` (em uso).
> **Gap LIA:** ativar o padrão quando as APIs de domínio forem separadas (ver seção 21, item P1). **Gap v5:** sem multi-tenancy nos eventos (sem `company_id` nas mensagens RabbitMQ); sem circuit breaker se a fila travar → [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508).

---

## 18. Roadmap de Implementação

> **Status em 19/03/2026:** Fases 1-4 + Sprints A–F + G1–G7 + I + J + SEG-1–5 + AUD-1–5 + Y1–Y5 + Z1–Z7 + F1-02 + F1-03 + F2-04 todos concluídos. **4.600+ testes, 29%+ coverage (gate 30%), 362 endpoints, 8 agentes principais + 6 subagentes Z1.** Próximo foco: coverage 40%, separação api-funil, métricas por versão de prompt.

### ✅ Fase 1 — Fundação (CONCLUÍDO)
1. ✅ `MainOrchestrator` + `ContextAdapter` + `/chat/universal`
2. ✅ `MemoryResolver` com pronomes/posição
3. ✅ `should_keep_filters()` + `ConversationState`
4. ✅ Testes de contrato para `MainOrchestrator`

### ✅ Fase 2 — Migração dos Entry Points (CONCLUÍDO)
1. ✅ `orchestrated_talent_chat.py` → thin adapter
2. ✅ `orchestrated_job_chat.py` → thin adapter
3. ✅ `pipeline_orchestrator.py` → thin adapter
4. ✅ WS conectado ao `MainOrchestrator`

### ✅ Fase 3 — Paginação e Shortlist (CONCLUÍDO)
1. ✅ Paginação conversacional
2. ✅ Shortlist como feature explícita
3. ✅ `ConversationState` expandido

### ✅ Fase 4 — Domínios Legacy → ReAct (CONCLUÍDO — Fases 4a/4b/4c/5)
1. ✅ `analytics` → `AnalyticsReActAgent` (4-file pattern) + wired no WS dispatcher
2. ✅ `communication` → `CommunicationReActAgent` (4-file pattern) + wired no WS dispatcher
3. ✅ `ats_integration` → `ATSIntegrationReActAgent` (4-file pattern) + wired no WS dispatcher
4. ✅ `LiaSplitPanel` + `NavigationIntentDetector` + `useActionIntent` (5 domínios)
5. ✅ LangGraph nativo ativado (`USE_LANGGRAPH_NATIVE=True`) + `VectorSemanticCache` + `CascadedRouter` 6-tiers
6. ✅ UV Monorepo 9 libs + Docker Compose 10 serviços + Celery high/normal/low + beat + flower

### Critérios de Sucesso (alcançados)
- ✅ 100% das mensagens de chat passam pelo `MainOrchestrator`
- ✅ FairnessGuard executado em todos os paths
- ✅ Pronomes e referências posicionais resolvidos
- ✅ Coverage gate: 25% → 30% (atingido em Sprints Y–Z, 29%+)
- ✅ 4.600+ testes coletados

---

### ✅ Sprint A — Robustez Crítica (CONCLUÍDO — André P2, P4)
1. ✅ Rate limiting LLM por tenant — `app/middleware/rate_limiter.py` + `app/services/token_budget_service.py` — Redis `tokens_used_today` por `company_id`, HTTP 429 com `Retry-After`
2. ✅ `TimedToolNode` em `libs/agents-core/` — `asyncio.wait_for(tool_call, timeout=15s)` + `ToolError("timeout")` fallback

### ✅ Sprint B — Observabilidade Estruturada (CONCLUÍDO — André P3, P6, P8)
1. ✅ `PromptVersionRegistry` — `app/services/prompt_version_registry.py` + campo `prompt_version` em `ConversationLog`
2. ✅ Grafana no `docker-compose.yml` — dashboard provisionado, alertas de custo/latência/tool failure
3. ✅ Sentry — `app/core/sentry.py` + `FastAPIIntegration` + `CeleryIntegration` + PII scrubbing LGPD

### ✅ Sprint C — Qualidade de Busca + HITL (CONCLUÍDO — André P7, P9)
1. ✅ PoC `tsvector` + `pg_trgm` em CVs — benchmark documentado; decisão: adotar FTS nativo antes de Elasticsearch
2. ✅ `interrupt_before/after` LangGraph — 3 fluxos críticos: email em massa, mover para oferta, WSI borderline

### ✅ Sprint D — Testes + APIs (CONCLUÍDO — André P10, P1, P14)
1. ✅ Snapshots para todos os agentes — `tests/snapshots/test_remaining_agents_snapshots.py` (Sourcing, Policy, Kanban, Talent, Jobs)
2. ✅ Coverage gate: 25% → 30% (Sprint I iniciou; Sprints Y–Z consolidaram em 29%+)
3. ⚠️ `api-funil` como micro-serviço — scaffold existe, deploy pendente (threshold: p95 CRUD > 500ms)

### ✅ Sprint E — Qualidade FE (CONCLUÍDO)
1. ✅ `candidates-page.tsx` — hooks `useCandidatesList` + `useBulkCandidateDataRequests` wired
2. ✅ `CandidateSearchBar.tsx` + `CandidateTabs.tsx` extraídos

### ✅ Sprint F — Consolidação (CONCLUÍDO)
- **F1** ✅ HITL Persistence — `app/models/hitl.py` + `alembic/versions/032_add_hitl_tables.py` + `hitl_service.py` Redis+DB
- **F2** ✅ Coverage Gate Unification — `--cov-fail-under=25` alinhado com CI
- **F3** ✅ FE Hooks Wiring — `useCandidatesList()` + `useBulkCandidateDataRequests()` wired em `candidates-page.tsx`
- **F4** ✅ Short List Endpoint — `app/api/v1/short_lists.py` + `short_list_service.py` + proxy FE + hook
- **F5** ✅ Sprint E Phase 3 — `CandidateSearchBar.tsx` + `CandidateTabs.tsx`
- **F6** ✅ LangSmith CI Step — `.github/workflows/ci.yml` step `Verify LangSmith config` (non-blocking)

### ✅ Sprints G1–G7 (CONCLUÍDOS — 08/03/2026)
- **G1** ✅ HITL Multi-tenant — `domain` + `company_id` em `request_approval()` nos 3 agentes HITL
- **G2** ✅ Coverage Gate 29% — 7 novos arquivos de teste, gate `--cov-fail-under=25`
- **G3** ✅ SearchResultsHeader — `src/components/pages/candidates/SearchResultsHeader.tsx` (202L → 9L)
- **G4** ✅ useCandidatesListMapped — `candidate-transforms.ts` + `use-candidates-list-mapped.ts`
- **G5** ✅ YAML Tool Registry — `app/tools/tool_registry_metadata.yaml` (32 tools) + loader + validação
- **G6** ✅ RAG Híbrido — `rag_pipeline_service.py` BM25+pgvector alpha blend + `GET /api/v1/candidates/rag-search`
- **G7** ✅ TOON Format — `toon_service.py` + `GET /api/v1/candidates/{id}/toon` + Redis TTL + LGPD anonymize

### ✅ Sprint I — Coverage Gate + Qualidade (CONCLUÍDO — 09/03/2026)
1. ✅ `test_intent_classifier_coverage` — 56 novos testes
2. ✅ `test_candidate_search_schemas` — 50 novos testes
3. ✅ Coverage gate elevado para 32% (`--cov-fail-under=32` no `pytest.ini`)
4. ✅ Coverage alcançado via sprints subsequentes (29%+, gate ajustado para 30%)

### ✅ Sprint J — Float Chat Nível 3 (CONCLUÍDO — 09/03/2026)
1. ✅ `LiaChatPanel` migrado REST → WebSocket
2. ✅ `use-float-streaming.ts` — HITL + streaming em tempo real
3. ✅ `HITLConfirmCard.tsx` — card de aprovação inline no chat
4. ✅ `navigation_intent.py` — 4 novos grupos (Configurações, Indicadores, WSI) + reordenado por especificidade
5. ✅ Wizard detectado → redireciona para `openSplitView("Vagas")`
6. ✅ 9 testes Vitest

### ✅ Sprints SEG-1 a SEG-5 — Segurança e Governança (CONCLUÍDOS — 11/03/2026)
- **SEG-1** ✅ PromptInjectionGuard — `agent_chat_ws.py` + `wsi_interview_graph.py`
- **SEG-2** ✅ FairnessGuard em agentes ReAct — `sourcing_react_agent.py` + `pipeline_transition_agent.py`
- **SEG-3A** ✅ PII Masking workers Celery — `celery_app.py` `worker_process_init` signal
- **SEG-3B** ✅ Data minimization em prompts LLM — `strip_pii_for_llm_prompt()` em 6 callers
- **SEG-4** ✅ ConsentCheckerService no Gate 1 WSI — LGPD opt-out bloqueia triagem
- **SEG-5** ✅ AuditService em gates de decisão — PipelineTransition + Sourcing auditados

### ✅ Sprints AUD-1 a AUD-5 — Auditoria de Profundidade (CONCLUÍDOS — 12/03/2026)
- **AUD-1** ✅ ANTI_SYCOPHANCY_OPERATIONAL em 6 prompts faltantes (analytics, comm, automation, ats, sourcing, pipeline)
- **AUD-2** ✅ Circuit breakers — OPENAI_CIRCUIT, GEMINI_CIRCUIT, GUPY/PANDAPE/STACKONE/SENDGRID/RESEND + WORKOS
- **AUD-3** ✅ Audit trail em PolicySetupAgent — cada campo configurado registrado
- **AUD-4** ✅ HITL em SourcingReActAgent + CommunicationReActAgent — outreach/mensagens críticas bloqueadas
- **AUD-5** ✅ bandit CI + mock data removido de páginas admin

### ✅ Sprints Y1–Y5 — Compliance Crítico + Quick Wins + Capacidades Avançadas (CONCLUÍDOS — 15/03/2026)
- **Y1** ✅ PII masking structlog raiz, audit trail interview_graph, LGPD ATS campos dinâmicos, FairnessGuard interview agent
- **Y2** ✅ Tool scope validation, Pearch fallback chain, Proactive insights, JobReport backend real, Prometheus por agente
- **Y3** ✅ Bias Audit EEOC chi-square, Confidence Calibration 12 agentes, Granular Consent LGPD, Score clicável Kanban, ML Adaptativo
- **Y4** ✅ Benchmark Salarial Real (Apify), Priority Queue urgência, Multi-Model por agente, WSI Assíncrono, Fit Cultural
- **Y5** ✅ Runbook operacional, YAML Hot-Reload agentes, RAG por domínio, Auto-Routing adaptativo, Agent-to-Agent bus, Event Sourcing

### ✅ Sprints Z1–Z7 — Arquitetura Avançada (CONCLUÍDOS — 19/03/2026)
- **Z1** ✅ KanbanReActAgent + PipelineTransitionAgent decompostos em 6 subagentes (supervisor + workers)
- **Z2-01** ✅ `LearningSnapshotService` — snapshots versionados do loop de aprendizado com rollback
- **Z3-02** ✅ Campos `version` + `updated_at` nos 9 YAMLs de contexto em `libs/contexts/`
- **Z5-02** ✅ `PolicySetupAgent` shim com `DeprecationWarning` → fonte canônica em `app/domains/policy/agents/agent.py`
- **Z5-03** ✅ Threshold semântico configurável via `ROUTER_VECTOR_SIMILARITY_THRESHOLD` (padrão 0.92) + A/B flag `ROUTER_VECTOR_CACHE_ENABLED`
- **Z6-01** ✅ ATS clients: arquivos duplicados em `domains/ats_integration/` convertidos em shims re-exportando de `app/services/ats_clients/`
- **Z6-02** ✅ OpenTelemetry OTLP — `_try_init_otlp()` em `app/shared/tracing.py`, `@trace_span` em CascadedRouter, DLQ, LearningLoop
- **Z6-03** ✅ Microsoft Presidio NER Layer 4 — `strip_pii_for_llm_prompt()` com flag `LLM_PROMPT_PRESIDIO_ENABLED`
- **Z7-01** ✅ `RecruiterBehaviorService` — perfil comportamental (500 sinais, TTL 24h), active_hours, sourcing_channels, stage_conversion_rates

### ✅ Sprints F1-02, F1-03, F2-04 — Resiliência e Qualidade (CONCLUÍDOS — 15–19/03/2026)
- **F1-02** ✅ FairnessGuard no learning loop — validação batch antes de aplicar padrões aprendidos
- **F1-03** ✅ SLOs formais no circuit breaker — degraded mode responses + SLO breaches registradas
- **F2-04** ✅ Dead Letter Queue — `DLQService` Redis LIST, cap 1000, TTL 7d, PII masking, notificação Bell para tasks críticas. 4 endpoints admin: `GET /api/v1/admin/dlq`, requeue, clear

---

### 🟡 Pendentes — Sprint K+ (prioridade média)
1. **Separação api-funil** — deploy do scaffold como primeiro micro-serviço (threshold: p95 CRUD > 500ms)
2. **Métricas por versão de prompt** — latência/custo/satisfaction por `prompt_version` no registry
3. **SonarCloud + PostHog** — quality gate e product analytics (ADR-002 Must-Have)
4. **Coverage 40%** — próximo gate após 30% atingido

---

## 19. Camada de Inteligência Completa da LIA

Esta seção documenta a camada de inteligência da LIA de forma exaustiva — baseada em análise de 150+ arquivos. O objetivo é garantir que tudo que existe na LIA e está ausente no v5 seja registrado para fins de comparação e priorização.

O v5 possui agentes especializados e pipeline LangGraph. A LIA vai muito além: personalização por recrutador, aprendizado contínuo de comportamento, human-in-the-loop estruturado, predição ML de outcomes, explicabilidade, rastreamento de custos por tenant e AB testing — capacidades que representam meses de desenvolvimento e diferenciação competitiva real.

---

### 19.1 Personalização por Recrutador (Invisible Learning)

**Completamente ausente no v5.** A LIA aprende o comportamento individual de cada recrutador de forma silenciosa, sem UI de configuração.

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/recruiter_personalization_service.py` (555L) | Detecta padrões após 10+ vagas: velocidade de decisão, taxa de correção por campo, thresholds preferidos |
| `app/services/intelligence_layer_service.py` (779L) | Orquestra a camada de inteligência — readiness check, IntelligenceContext com 5 camadas de confiança |
| `app/services/sector_benchmark_service.py` (304L) | Anti-sycophancy (Crença #11) — 16 perfis (4 senioridades × 4 áreas) injetados nos prompts |
| `libs/models/lia_models/recruiter_profile.py` | RecruiterProfile: preferred_seniorities, correction_patterns, custom_confidence_thresholds, wizard_mode (quick/detailed) |
| `libs/models/lia_models/intelligence_layer.py` | IntelligenceInsight: loga cada sugestão com was_accepted, was_applied, final_value — 100% auditável |

**Como funciona:**
1. Recrutador cria vagas normalmente
2. Após 10+ vagas, `RecruiterPersonalizationService` detecta padrões: "esse recrutador sempre aumenta o salário sugerido em ~15%", "sempre muda seniority de Pleno para Sênior"
3. Na próxima vaga, a sugestão já vem ajustada — sem que o recrutador precise configurar nada
4. `PersonalizationSettings` tem campo `consent_version` para LGPD

**v5 equivalente?** Não. O v5 não tem nenhuma forma de personalização por usuário ou empresa.

---

### 19.2 Sistema de Aprendizado Contínuo (Feedback Loop)

**Completamente ausente no v5.** A LIA aprende continuamente com o comportamento real do recrutador, sem intervenção humana.

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/feedback_learning_service.py` (851L) | Captura 3 tipos de feedback: correções no wizard, outcomes de vagas (filled/cancelled/expired), rejeição/aceitação de sugestões |
| `app/shared/learning/learning_loop_service.py` (1073L) | Batch processor: agrupa FeedbackEvents → LearningPattern com sample_size, acceptance_rate, confidence_score |
| `app/shared/learning/template_learning_service.py` (375L) | Aprende estilo de JD por empresa: estrutura de seções, verbos preferidos, bullet vs parágrafo |
| `app/shared/learning/ab_testing_service.py` (375L) | Framework de experimentos: chi-square test, stratification por empresa, resultado com effect_size e recommendation |
| `libs/models/lia_models/feedback_learning.py` | WizardFeedback, JobOutcome (time_to_fill_days, salary_final, funnel_metrics) |

**7 tipos de padrão aprendidos:**
- `SALARY_PREFERENCE` — avg_min/max, median, direction de ajustes dos últimos 50 jobs
- `SKILL_PREFERENCE` — top skills por role+seniority com peso e nível sugerido
- `BENEFIT_PREFERENCE` — benefícios mais aceitos por empresa
- `WORK_MODEL_PREFERENCE`, `SCREENING_PREFERENCE`, `JD_STYLE_PREFERENCE`
- `SKILL_SUGGESTION_PATTERN` — acceptance_rate, suggested_weight/level por skill

**Confiança dos padrões:**
- ≥20 amostras → HIGH (0.9)
- ≥10 → MEDIUM (0.7)
- ≥5 → LOW (0.5)
- <5 → VERY_LOW (0.3, não aplica automaticamente)

**v5 equivalente?** Não. O v5 não persiste nenhum aprendizado entre sessões.

---

### 19.3 Human-in-the-Loop Estruturado

**Parcialmente ausente no v5** (tem detecção de confirmação, não tem workflows de aprovação).

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `libs/models/lia_models/approval.py` (117L) | ApprovalRequest: 5 tipos (VACANCY_APPROVAL, CANDIDATE_HIRE, OFFER_APPROVAL, BUDGET_APPROVAL, CUSTOM), multi-tier levels |
| `app/orchestrator/pending_action.py` | Gerencia ações que aguardam confirmação humana |
| `app/shared/learning/learning_confirmation_service.py` | Valida padrões aprendidos com confirmação humana antes de aplicar automaticamente |
| `app/services/human_review_sampling_service.py` | Stratified sampling de decisões de IA para revisão humana (QA contínuo) |

**Fluxos de aprovação:**
- Vaga criada por IA requer aprovação do gestor antes de publicar
- Score WSI borderline (65-75) → encaminha para revisão manual antes de reprovar
- Budget de contratação acima de threshold → aprovação financeira obrigatória
- Email em massa para candidatos → confirmação antes de disparar

**LangGraph interrupt:** `interrupt_before`/`interrupt_after` já configurados na base dos grafos para pausar e aguardar input humano.

**v5 equivalente?** Parcial — o v5 tem `needs_confirmation: true` como flag, mas sem workflow estruturado de aprovação multi-tier.

---

### 19.4 Orquestração Inteligente de Dados (Multi-Source)

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/intelligent_data_orchestrator.py` | 7 fontes priorizadas, consensus detection, caching em 3 camadas |
| `app/services/wizard_orchestrator_service.py` | WizardIntent (8 tipos), keyword + LLM routing para source correto |

**7 fontes com prioridade:**
1. Learning Patterns (VERY_HIGH — 0.95 confidence)
2. Company Skills Catalog (HIGH — 0.85)
3. Company Config (HIGH — 0.85)
4. Job Insights históricos (HIGH — 0.85)
5. ATS History (MEDIUM — 0.70)
6. Market Benchmark (LOW_MEDIUM — 0.55)
7. LLM Inference (LOW — 0.40)

**Consensus detection:** se múltiplas fontes concordam (ex: Learning Pattern + ATS History ambos sugerem R$8-10k), confidence aumenta automaticamente.

**v5 equivalente?** Não. O v5 usa uma única fonte (aggregated_stats do sourcing).

---

### 19.5 Predição e Machine Learning

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/ml/outcome_predictor.py` | Prediz P(filled \| job_id, candidates_in_pipeline) com histórico de funnel |
| `app/services/ml/feature_engineering.py` | Features domain-specific: education_level, skill_match_score, keyword_density, normalized [0,1] |
| `app/services/ml/model_registry.py` | Versioning de modelos ML com performance metrics, suporte a A/B entre versões |
| `app/services/pipeline_prediction_service.py` | Prediz dias até próxima conversão por stage (screening→interview→offer→hire) |
| `app/services/predictive_analytics_service.py` | Churn risk, funnel bottleneck, hiring velocity — análises agregadas |
| `app/shared/agents/proactive_worker.py` | Background worker: age sem input do usuário (drift detection, pattern generation, alertas proativos) |
| `app/services/autonomous_agent_service.py` | Agentes autônomos: feedback automático, notificações, follow-ups |
| `app/services/proactive_alert_service.py` | Monitora KPIs e alerta antes do problema virar crítico ("vaga aberta há 30 dias sem fills") |

**Predições disponíveis:**
- Time to fill (dias até contratar, com intervalo de confiança)
- Probabilidade de outcome (filled vs cancelled) dado o pipeline atual
- Correlações automáticas: qual atributo da vaga mais impacta sucesso

**v5 equivalente?** Não. O v5 usa dados históricos apenas para exibição, não para predição.

---

### 19.6 Explicabilidade

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/explainability_service.py` (322L) | generate_candidate_explanation(): lista critérios avaliados E critérios ignorados (Crença #7 transparência) |
| `app/api/v1/agent_explainability.py` | /explainability/timeline/{session_id}: cada iteração ReAct com reasoning, tool, decision |
| `app/api/v1/agent_explainability.py` | /explainability/stats: avg_confidence, avg_iterations, top tools por agente |

**Saída da explicabilidade:**
- Para candidatos: por que foi aprovado/reprovado, quais critérios contaram, sugestões de melhoria
- Para recrutadores: quais agentes foram invocados, timeline de decisões, overrides humanos
- Para auditores: execution_id → timeline completa (compliance)

**v5 equivalente?** Não. O v5 retorna resposta final sem expor raciocínio intermediário.

---

### 19.7 Rastreamento de Tokens e Budget por Tenant

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/token_tracking_service.py` (722L) | Registra cada chamada LLM com input_tokens, output_tokens, model, latency_ms, custo estimado |
| `libs/models/lia_models/*.py` | AiCreditsBalance: current_usage vs monthly_limit por company |

**Funcionalidades:**
- 10 modelos com preços atualizados (Claude, GPT, Gemini)
- Alertas: 80% → WARNING, 100% → URGENT (Redis dedup 24h para não spammar)
- Limites por usuário, empresa e hora — com custom overrides por plano
- Retenção 365 dias (LGPD scheduled_deletion automática)

**v5 equivalente?** Não. O v5 não rastreia consumo de tokens nem tem controle de custo por tenant.

---

### 19.8 Cache Semântico de IA (Sem Embedding)

**Parcialmente presente no v5** (cache MD5 por hash exato, não semântico).

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/services/ai_cache_service.py` (358L) | Semantic similarity por pgvector cosine (threshold ≥ 0.92, configurável — Z5-03) |
| `app/services/response_cache_service.py` | Cache de respostas de agentes por intent com TTL configurável |
| `app/services/jd_template_cache_service.py` | Templates JD pré-geradas por role/department |

**Tipos de cache com TTLs:**
- `jd_generation`: 24h
- `wsi_questions`: 48h
- `skills_extraction`: 72h
- `salary_analysis`: 12h

**Multi-tenant:** cache key scoped por company_id (dados de uma empresa nunca vazam para outra).

**v5 equivalente?** O v5 tem cache MD5 (hash exato). A LIA tem cache semântico por similaridade textual, sem precisar de modelo de embedding.

---

### 19.9 Robustez e Guardrails (Camada Defensiva)

**Parcialmente presente no v5** (FairnessGuard básico, injection detection no domínio de evaluation).

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/shared/robustness/enhanced_base.py` (301L) | Cancellation detection, telemetry por agente, AgentError → user_friendly_message |
| `app/shared/robustness/intent_schemas.py` (486L) | 50+ schemas de intent (10 agent types × 2-7 intents) com entity requirements e confidence scoring |
| `app/shared/robustness/input_validation.py` | sanitize_text() (XSS/SQL injection), detect_language() (PT-BR, EN, ES, FR) |
| `app/shared/robustness/response_filter.py` | Remove PII, detecta alucinações, filtra conteúdo inapropriado |
| `app/shared/robustness/defensive_prompts.py` | get_out_of_scope_response(), get_clarification_message() por agent type |
| `app/shared/robustness/context_management.py` | CancellationHandler, controle de tamanho/relevância do contexto |

**Intent Schemas — routing determinístico:**
- Cada intent tem REQUIRED / RECOMMENDED / OPTIONAL entities
- Score = base_confidence + entity_contributions + keyword_matches + context_satisfaction
- Retorna missing entities com descriptions (base para mensagem de clarificação)

**v5 equivalente?** O v5 tem `safe_process_input()` e FairnessGuard. A LIA tem 6 módulos dedicados cobrindo injection, alucinação, scope check, cancellation e scoring determinístico de intent.

---

### 19.10 Feature Flags, Monitoramento e Drift

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/shared/governance/feature_flag_service.py` | Gates por company/user: FAIRNESS_LAYER3_ENABLED, USE_LANGGRAPH_NATIVE, PERSONALIZATION_ENABLED |
| `app/shared/governance/agent_monitoring_service.py` | Success rate, avg_response_time, error_rate, tool failure count — por agente |
| `app/services/model_drift_service.py` | 4 triggers: score distribution change, approval_rate drop, cost spike, P95 latency increase |
| `app/jobs/drift_job.py` | Celery task diário (6h Brasília) — verifica drift em todas as empresas |
| `app/services/drift_alert_service.py` | 1 trigger → WARNING (Bell + Teams), 2+ → URGENT |

**v5 equivalente?** Não. O v5 não tem nenhum mecanismo de detecção de degradação de modelo.

---

### 19.11 WSI — Work Simulation Interview (Metodologia Proprietária)

O WSI é a metodologia de avaliação de candidatos da WeDOTalent. Completamente ausente no v5.

O WSI é a metodologia de avaliação de candidatos da WeDOTalent. Completamente ausente no v5 e em qualquer produto concorrente como commodity.

**Componentes principais:**

| Arquivo | Responsabilidade |
|---------|-----------------|
| `wsi_screening_pipeline.py` | Orquestra o fluxo completo de triagem WSI |
| `wsi_interview_graph.py` | LangGraph StateGraph para entrevistas WSI (6 nós) |
| `wsi_deterministic_scorer.py` | Scorer baseado em regras + IA (não puro LLM) |
| `wsi_question_generator.py` | Geração de perguntas calibradas por senioridade/área |
| `wsi_question_adjuster.py` | Ajuste dinâmico de dificuldade durante a entrevista |
| `wsi_voice_orchestrator.py` | Triagem por voz (ligações via OpenMic.ai) |
| `wsi_feedback_generator.py` | Feedback personalizado ao candidato |
| `wsi_bloom_calibrator.py` | Calibração de dificuldade via Taxonomia de Bloom |
| `wsi_profile_matcher.py` | Match pergunta-perfil por senioridade e área |
| `wsi_score_normalizer.py` | Normalização de scores para comparabilidade cross-job |
| `wsi_session_manager.py` | Gestão de estado de sessão de entrevista |
| `wsi_analytics_service.py` | Analytics de performance WSI por job e empresa |

**O que torna o WSI diferente de avaliações genéricas LLM:**

1. **Scorer determinístico** — o score não depende apenas do julgamento do LLM. Regras explícitas garantem consistência e auditabilidade (SOX/LGPD).

2. **Taxonomia de Bloom** — perguntas classificadas por nível cognitivo (Conhecimento → Compreensão → Aplicação → Análise → Síntese → Avaliação). Dificuldade ajustada dinamicamente com base nas respostas anteriores.

3. **Perfis de calibração** — banco de perguntas por senioridade (júnior / pleno / sênior / especialista) e área (tecnologia, vendas, operações, etc.). Uma pergunta "sênior de engenharia" é diferente de uma "sênior de vendas".

4. **Score normalization** — permite comparar candidatos de diferentes processos seletivos em escala comum (0-100 com z-score setorial).

5. **Triagem por voz** — candidatos podem ser entrevistados via ligação (OpenMic.ai + Deepgram STT), com transcrição e scoring automatizados.

6. **Feedback personalizado** — candidato recebe feedback estruturado por competência, não apenas aprovado/reprovado.

**Quantitativo:** 12+ arquivos dedicados, integração com 3 provedores externos (OpenMic.ai, Deepgram, Anthropic).

---

### 19.12 Sourcing Inteligente

O v5 tem um `SearchAgent` que consulta a API do ATS Rails. A LIA tem uma camada de sourcing significativamente mais sofisticada.

| Componente | Função |
|-----------|--------|
| `pearch_service.py` | Integração com Pearch AI (190M+ perfis globais) |
| `apify_service.py` | Web scraping de perfis via Apify |
| `semantic_search_service.py` | Busca semântica via pgvector |
| `boolean_search_service.py` | Busca booleana avançada (LinkedIn-style) |
| `wrf_service.py` | Work Requirements Framework — estruturação de requisitos de vaga |
| `pre_wrf_filter.py` | Filtro rápido antes do WRF completo (custo) |
| `candidate_comparison_service.py` | Comparação N-candidatos com tabela rankeada |
| `candidate_enrichment_service.py` | Enriquecimento de perfil via fontes externas |
| `talent_pool_service.py` | Gestão de pool de talentos reutilizável |
| `sourcing_analytics_service.py` | Analytics de funil de sourcing |
| `contact_inference_service.py` | Inferência de email/contato de candidatos |
| `export_service.py` | Exportação de candidatos em múltiplos formatos |
| `diversity_sourcing_service.py` | Sourcing com metas de diversidade |

**Diferença fundamental:** o v5 busca candidatos já na base do ATS. A LIA busca ativamente em fontes externas (Pearch AI, scraping via Apify) e enriquece perfis antes de apresentar ao recrutador.

---

### 19.13 Comunicação Inteligente

O v5 não tem camada de comunicação — as mensagens ao candidato são geradas pelo LLM e retornam para o ATS Rails enviar. A LIA tem infraestrutura própria de comunicação multi-canal.

| Componente | Função |
|-----------|--------|
| `infer_behavior_service.py` | Inferência de comportamento do candidato (horário preferido, canal preferido) |
| `interpret_context_llm_service.py` | Interpretação de contexto de conversa via LLM para personalização |
| `notification_service.py` | Dispatcher central (Bell, Email, Teams, WhatsApp, Chat) |
| `email_service.py` | Email via Resend/SendGrid/Mailgun (provider-agnostic) |
| `teams_service.py` | Microsoft Teams Incoming Webhook + MessageCard |
| `whatsapp_service.py` | Meta Graph API + Twilio (fallback) |
| `pipeline_notification_service.py` | Notificações automáticas em transições de pipeline |
| `data_request_service.py` | Solicitação de dados ao candidato via WhatsApp |
| `communication_analytics_service.py` | Analytics de abertura, resposta, conversão por canal |

**5 canais ativos:** Bell in-app, Email (3 providers), WhatsApp (2 providers), Microsoft Teams, Chat inline.

**Dispatch automático:** quando um candidato muda de etapa no pipeline, a comunicação relevante é disparada automaticamente sem intervenção do recrutador.

---

### 19.15 Agente de Automação e Planejamento de Tarefas

**Completamente ausente no v5.** A LIA tem um agente ReAct dedicado à automação e orquestração de tarefas complexas, seguindo o padrão canônico de 4 arquivos.

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/domains/automation/agents/automation_react_agent.py` (266L) | Agente ReAct que decompõe tarefas complexas de recrutamento em subtarefas com dependências (DAG), priorização e execução paralela |
| `app/domains/automation/agents/automation_tool_registry.py` (375L) | 10+ tools: create_task, list_tasks, complete_task, decompose_task, plan_execution, generate_briefing, schedule_job, etc. |
| `app/domains/automation/agents/automation_system_prompt.py` (36L) | System prompt definindo 7 sub-agentes disponíveis: job_planner, sourcing, cv_screening, interviewer, wsi_evaluator, scheduling, analyst_feedback |
| `app/domains/automation/agents/automation_stage_context.py` (46L) | Stage definitions para o loop ReAct, incluindo transições de estado |
| `app/domains/automation/domain.py` (200L) | 16+ action types com keyword mapping para routing interno |
| `app/domains/automation/models/planned_task.py` (218L) | PlannedTask: tarefas com dependências, status tracking e relações DAG |

**Como funciona:**
1. Recrutador diz "crie um processo seletivo para Engenheiro Sênior com triagem automática"
2. `AutomationReActAgent` decompõe em subtarefas: criar vaga → configurar WSI → sourcing → triagem → agenda entrevistas
3. Constrói DAG de dependências (sourcing só começa depois da vaga criada)
4. Executa em paralelo onde possível, sequencial onde há dependências
5. Monitora status e reporta progresso ao recrutador

**v5 equivalente?** Não. O v5 não tem capacidade de planejamento de tarefas nem decomposição de workflows complexos.

---

### 19.16 Motor de Automação e Stage Transitions Inteligentes

**Completamente ausente no v5.** A LIA tem um motor de automação que dispara ações automaticamente com base em eventos do pipeline, com predição inteligente de sub-status e geração de mensagens personalizadas via Claude.

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/domains/automation/services/automation_service.py` (1234L) | Motor principal: avalia condições, dispara ações (email, WhatsApp, tasks, notificações), registra histórico de execução |
| `app/domains/automation/services/stage_automation_engine.py` (460L) | Processador central: 15+ trigger types (screening_completed, interview_scheduled, offer_sent, candidate_rejected, etc.) |
| `app/domains/automation/services/stage_transition_automation.py` (800L) | SubStatusPredictor: prediz sub-status de rejeição/avanço baseado em contexto; gera mensagens personalizadas por sub-status via Claude |
| `app/domains/automation/services/automation_trigger_service.py` (798L) | Triggers proativos: candidato sem contato (48h), lembrete de entrevista (24h), scorecard pendente (24h), vaga parada (5d) |
| `app/domains/automation/services/automation_scheduler.py` (881L) | APScheduler: verificação periódica de candidatos inativos (48h+), no-shows, tarefas pendentes |
| `app/domains/automation/services/automation_handlers.py` (855L) | Handlers de evento: valida condições, executa ações correspondentes |
| `app/domains/automation/models/automation.py` (350L) | CommunicationAutomation: 8 TriggerTypes × 7 ActionTypes — regras configuráveis por empresa |

**15+ trigger types:**
- `screening_completed`, `interview_scheduled`, `offer_sent`, `candidate_rejected`
- `candidate_no_contact_48h`, `interview_reminder_24h`, `scorecard_pending_24h`
- `job_stagnant_5d`, `linkedin_update`, `offer_accepted/declined`, etc.

**v5 equivalente?** Não. O v5 não tem automação de pipeline — todas as ações são manuais.

---

### 19.17 Sistema de Alertas Proativos e Monitor de Pipeline

**Completamente ausente no v5.** A LIA monitora ativamente o pipeline e alerta o recrutador antes que problemas se tornem críticos.

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/domains/automation/services/proactive_alert_service.py` (779L) | Sistema de alertas em 5 categorias com priorização automática |
| `app/domains/automation/services/pipeline_monitor.py` (385L) | Monitor: candidatos além do SLA, WSI alto sem ação, deadlines próximas, entrevistas sem feedback |
| `app/domains/automation/services/proactive_service.py` (486L) | 5 tipos de notificação proativa: daily_briefing, end_of_day, interview_reminder, approval_needed, stagnant_candidate |
| `app/domains/automation/services/prediction_action_bridge.py` (176L) | Conecta predições ML a ações concretas: high success → avança candidato; dropout risk → ação preventiva; fill risk → expande sourcing |
| `app/domains/automation/services/autonomous_agent_service.py` (838L) | Background job management: tarefas agendadas, recorrentes, sugestões proativas, ações automáticas |

**5 categorias de alertas proativos:**
1. **Pipeline Health** — candidatos estagnados além do SLA, processos sem movimento
2. **Produtividade** — scorecards pendentes, tarefas atrasadas do recrutador
3. **Comunicação** — candidatos sem resposta há X dias, follow-ups necessários
4. **Preditivo** — dropout risk detectado, time-to-fill em risco, candidatos com score alto sem ação
5. **Sistema** — ATS sync falhou, créditos em alerta (80%/100%), drift detectado

**Ponte Predição-Ação (`prediction_action_bridge.py`):**
- `P(success) > 0.8` → sugere avançar para próxima etapa
- `dropout_risk > 0.6` → sugere contato proativo imediato
- `time_to_fill_risk > 0.7` → sugere expandir sourcing ou revisar requisitos

**v5 equivalente?** Não. O v5 não monitora o pipeline nem gera alertas proativos.

---

### 19.18 Inteligência Semântica Compartilhada

**Parcialmente presente no v5** (busca básica por keywords no SearchAgent).

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/shared/intelligence/semantic_search_service.py` (442L) | Expansão semântica em 7 domínios com Google Gemini + Redis cache; P95 < 300ms |
| `app/shared/intelligence/smart_extractor.py` (213L) | Extração de parâmetros de linguagem natural com caching e scoring de confiança |
| `app/shared/intelligence/embedding_service.py` (195L) | Geração e gerenciamento de embeddings para operações semânticas |
| `app/shared/intelligence/param_patterns.py` (240L) | Padrões de extração de parâmetros por domínio de recrutamento |

**7 domínios de expansão semântica:**
- **Skills** — "python" → [Python, Django, FastAPI, Flask, SQLAlchemy]
- **Job Titles** — "dev backend" → [Engenheiro Backend, Software Engineer, Desenvolvedor Python...]
- **Roles** — mapeamento de cargos para responsabilidades
- **Setores** — "financeiro" → [banco, fintech, seguro, corretora...]
- **Expertise** — níveis de senioridade e especialização
- **Áreas de Estudo** — graduações relacionadas ao perfil buscado
- **Empresas** — segmentação por porte, setor, modelo de negócio

**Como funciona:** quando o recrutador busca "dev sênior com cloud", o `SemanticSearchService` expande automaticamente para incluir variações de título, tecnologias correlatas (AWS, GCP, Azure, Kubernetes) e sinônimos de senioridade — sem que o recrutador precise escrever uma boolean query.

**v5 equivalente?** ⚠️ Parcial — `SmartExtractor` do v5 faz extração de parâmetros mas sem expansão semântica por domínio.

---

### 19.19 Fine-tuning Export e Melhoria Contínua do Modelo

**Completamente ausente no v5.**

**Arquivos-chave:**

| Arquivo | Função |
|---------|--------|
| `app/shared/learning/finetuning_export.py` (334L) | Exporta padrões de aprendizado como datasets de fine-tuning, com anonimização PII e masking LGPD |
| `app/shared/learning/learning_loop_service.py` (1073L) | CAPTURE → ANALYZE → APPLY: captura silenciosa de outcomes, detecção de padrões, aplicação automática em sugestões futuras |
| `app/shared/learning/ab_testing_service.py` (306L) | Framework de experimentos: chi-square, stratification por empresa, effect_size + recomendação |

**Como o fine-tuning export funciona:**
1. `LearningLoopService` acumula padrões de comportamento real: quais sugestões foram aceitas/modificadas/rejeitadas ao longo do tempo
2. `FinetuningExportService` transforma esses padrões em pares (input, ideal_output)
3. Anonimiza: remove PII (nome candidato, empresa, CPF, email), mantém padrões estruturais
4. Exporta em formato compatível com fine-tuning de LLMs (Claude, OpenAI)

**Impacto esperado:** após suficientes ciclos, o modelo fine-tunado performa melhor para o contexto específico de recrutamento BR — especialmente em terminologias, senioridades e expectativas salariais do mercado nacional.

**v5 equivalente?** Não. O v5 não persiste nenhum aprendizado entre sessões, portanto não há dados para fine-tuning.

---

### 19.14 Quantitativo da Camada de Inteligência

| Dimensão | LIA | v5 |
|----------|-----|-----|
| Arquivos na camada de IA | ~215 | ~40 |
| Agentes ReAct (4-file pattern) | 8 (Wizard, Pipeline, Sourcing, Policy, Kanban, Talent, Jobs, Automation) + 3 graph agents | 6 (classes BaseAgent, não ReAct real) |
| Grafos LangGraph | 3 (Wizard, WSI, Interview) | 1 (DomainWorkflow simplificado) |
| Provedores LLM | 3 (Claude, OpenAI, Gemini) | 1 (Gemini) |
| Serviços WSI | 12+ | 0 |
| Serviços de sourcing | 13+ | 1 (SearchAgent via HTTP) |
| Serviços de comunicação | 20+ | 0 (retorna para ATS enviar) |
| Canais de comunicação | 5 (Bell, Email, Teams, WA, Chat) | 0 |
| Personalização por recrutador | Sim (RecruiterPersonalizationService 555L) | Não |
| Sistema de aprendizado contínuo | Sim (7 padrões, LearningLoopService 1073L) | Não |
| Human-in-the-loop estruturado | Sim (5 tipos ApprovalRequest, HITL Persistence DB + HITLConfirmCard WS) | Parcial (flag needs_confirmation) |
| Orquestração multi-source | Sim (7 fontes com prioridade + consensus + 3-layer cache) | Não |
| Predição / ML | Sim (outcome_predictor 532L, drift, proactive_alert, prediction_action_bridge) | Não |
| Explicabilidade | Sim (ExplainabilityService 322L, timeline ReAct por sessão, stats por agente) | Não |
| Rastreamento de tokens/custo | Sim (TokenTrackingService 722L, 10 modelos, alertas 80%/100%, LGPD 365d) | Não |
| Cache semântico de IA | Sim (pgvector cosine ≥ 0.92, configurável via Z5-03) | Hash MD5 (exato) |
| A/B testing de prompts/versões | Sim (ABTestingService 306L, chi-square, effect_size) | Não |
| Feature flags por tenant | Sim (FeatureFlagService, por company/user) | Não |
| Compliance Stack | LGPD + SOX + ISO27001 + BCB498 + EU AI Act | FairnessGuard básico |
| Testes de fairness automatizados | Sim (Bias Audit, Four-Fifths Rule, CI) | Não |
| **Automação de pipeline (NOVO)** | **Sim — AutomationReActAgent + stage_automation_engine (15+ triggers) + APScheduler** | **Não** |
| **Alertas proativos inteligentes (NOVO)** | **Sim — proactive_alert_service (5 categorias) + pipeline_monitor + prediction_action_bridge** | **Não** |
| **Inteligência semântica compartilhada (NOVO)** | **Sim — semantic_search_service (7 domínios, Gemini, Redis cache P95 < 300ms)** | **Parcial — SmartExtractor básico** |
| **Fine-tuning export (NOVO)** | **Sim — finetuning_export.py (334L) + anonimização PII + formato Claude/OpenAI** | **Não** |
| **Snapshot testing de agentes (NOVO)** | **Sim — tests/snapshots/ cobrindo todos os 8 agentes ReAct** | **Não** |
| **Rate limiting por tenant (NOVO)** | **Sim — rate_limiter.py + token_budget_service.py (Redis, HTTP 429)** | **Não (sem multi-tenancy)** |
| **Versionamento de prompts (NOVO)** | **Sim — prompt_version_registry.py + campo prompt_version em ConversationLog** | **Não** |
| RAG Híbrido (BM25 + pgvector) | Sim — rag_pipeline_service.py (alpha blend) | Parcial — pgvector apenas |
| TOON Format por candidato+vaga | Sim — toon_service.py (Redis TTL, LGPD anonymize) | Não |

---

## 19.20 Padrão de Produção e Replicabilidade de Agentes

Esta seção documenta o padrão canônico que garante que qualquer novo agente seja criado de forma consistente, auditável e replicável — um dos pontos mais importantes discutidos com André e documentados no `GUIA_ARQUITETURA_IA_v1.0.md`.

### O Padrão 4 Arquivos — Shell Canônica de Todo Agente

Cada agente ReAct da plataforma **obrigatoriamente** contém 4 arquivos:

```
app/domains/<domínio>/agents/
├── <nome>_react_agent.py      ← Loop ReAct (Thought → Action → Observation → Repeat)
├── <nome>_tool_registry.py    ← Ferramentas disponíveis para o agente
├── <nome>_system_prompt.py    ← Prompt canônico + persona LIA + blocos de compliance
└── <nome>_stage_context.py    ← Contexto por stage, transições de estado
```

**Nenhum agente simulado é aceito.** O loop ReAct deve ser genuíno: o LLM decide qual tool usar, em que ordem, e quando parar. O sistema rejeita agentes "disfarçados" (classes com `process()` estático).

**Scaffold para novos agentes:** `app/shared/agents/agent_scaffold.py` — template funcional que implementa o padrão 4 arquivos com todos os hooks (observabilidade, memory, fairness, multi-tenancy) já conectados.

**Template completo:** `docs/GUIA_ARQUITETURA_IA_v1.0.md` — Apêndice B.

---

### ReactAgentRegistry — Registro Formal

```python
# app/shared/agents/react_agent_registry.py
register_react_agents()
# Registra: wizard, pipeline, sourcing, talent, jobs_management, kanban, policy, automation (8)
# + PipelineTransitionAgent (instanciado diretamente, não registrado) = 9 total
```

O registry é o ponto central de descoberta de agentes. Qualquer novo agente deve ser registrado aqui para ser roteável pelo `MainOrchestrator`.

---

### ADR Process — Decisões Arquiteturais Documentadas

Toda decisão arquitetural relevante está documentada em `docs/adr/`:

| ADR | Decisão | Arquivo |
|-----|---------|---------|
| **001** | Python/FastAPI, não Ruby/Rails (GC, performance, ecossistema ML) | `docs/adr/001-python-not-ruby.md` |
| **002** | Graph vs ReAct vs REST direto — critérios de escolha | `docs/adr/002-graph-vs-react.md` |
| **003** | Async para operações longas (Celery + WebSocket, nunca bloquear HTTP) | `docs/architecture/sync-vs-async.md` |

**Regra de Ouro do ADR-002:**
- **Graph (LangGraph)** → fluxo previsível com steps definidos, checkpoint auditável, compliance crítico (Wizard, WSI)
- **ReAct Loop** → fluxo imprevisível, raciocínio autônomo, ferramentas variáveis (8 agentes)
- **REST direto** → CRUD puro sem LLM, operações < 500ms

---

### Infraestrutura Compartilhada de Agentes

Todo agente herda automaticamente (via `EnhancedAgentMixin`):

| Componente | Arquivo | Função |
|------------|---------|--------|
| `ReActObserver` | `app/shared/agents/observability.py` | Rastreia cada iteração: company_id + user_id + request_id + tool timing |
| `WorkingMemory` | `app/shared/agents/working_memory.py` | Memória de sessão (referências, candidatos vistos, filtros ativos) |
| `LongTermMemory` | `app/shared/agents/long_term_memory.py` | Memória persistida entre sessões |
| `GuardrailRepository` | `app/shared/compliance/guardrail_repository.py` | Guardrails do banco — 3-tier: global → tenant → domínio |
| `FairnessGuard` | `app/shared/compliance/fairness_guard.py` | 3 camadas: regex → léxico → LLM opt-in |
| `LearningExtractor` | `app/shared/agents/learning_extractor.py` | Captura aprendizados de cada execução para o LearningLoop |

**GuardrailRepository** é especialmente importante: guardrails são editáveis via CRUD no admin sem re-deploy. Um admin pode ajustar regras de fairness ou compliance em tempo real. Seed inicial via migration Alembic garante que novos ambientes começam com guardrails corretos.

---

### Prompt Engineering Standards (Apêndices B, C, D do Guia)

| Padrão | Descrição | Arquivo de referência |
|--------|-----------|----------------------|
| YAMLs por domínio | Prompts separados do código, versionados via git | `app/domains/<dom>/prompts/*.yaml` |
| Persona canônica "LIA" | Mesma persona em todos os agentes — consistência UX | `_system_prompt.py` de cada agente |
| Compliance blocks imutáveis | Blocos de texto injetados automaticamente (FairnessGuard, LGPD, anti-discriminação) | Apêndice C do Guia |
| Few-shot padronizado | Exemplos de interação correta para guiar o LLM | Apêndice D do Guia |
| Audit de system prompts | Revisão periódica de conformidade com EU AI Act Art. 14 | `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_2026_02.md` |

---

### Checklist de Reprodução em Novo Ambiente (Seção 37 do Guia)

O `GUIA_ARQUITETURA_IA_v1.0.md` §37 documenta passo a passo como reproduzir o ambiente:
1. Variáveis de ambiente (template completo §7)
2. `alembic upgrade head` — migrations devem estar sempre na head
3. Seeds de guardrails e permissões via migration
4. Health endpoint validado antes de aceitar tráfego
5. LangSmith configurado para tracing
6. Celery workers (high/normal/low) + beat + Flower ativos
7. Sem dados mock em produção — qualquer fixture é detectada como erro

**v5 equivalente?** Não. O v5 não tem documentação de reprodução, padrão de scaffold, nem ADRs formais.

---

## 20. Status de Implementação das Recomendações do André

Tabela comparativa com status nos dois sistemas — permite ao time ver onde cada projeto está em relação às recomendações arquiteturais do André.

**Legenda:** ✅ Implementado | ⚠️ Parcial | ❌ Não implementado | — Não se aplica

| # | Recomendação do André | LIA | v5 | Observações |
|---|----------------------|-----|----|-------------|
| R1 | APIs separadas por domínio (avaliação LLM vs CRUD <200ms) | ⚠️ Parcial | ❌ Não | LIA: scaffold `apps/api-vagas/funil/onboarding` existe, não deployado. v5: monolito único, sem separação. |
| R2 | Workers assíncronos separados por tipo de carga | ✅ LIA | ⚠️ v5 | LIA: `celery_worker_high/normal/low` + beat + flower (Fase 6b). v5: Celery com tasks de evaluation (`domains/evaluation/tasks.py`) mas sem separação por domínio ou prioridade. |
| R3 | Versionamento de prompts com changelog e métricas por versão | ⚠️ Parcial | ❌ Não | LIA: `prompt_version_registry.py` criado (Sprint B), campo `prompt_version` em `ConversationLog`. Falta: métricas por versão (latência/custo/satisfaction). v5: prompts em código Python, sem controle de versão. |
| R4 | Política de retenção de auditoria (90d → Glacier → Deep Archive → 7 anos) | ✅ LIA | ❌ Não → [AUD-004/WT-1509](https://wedotalent.atlassian.net/browse/WT-1509) + [AUD-005/WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) | LIA: `libs/audit/audit_storage.py` + Celery task `audit.apply_lifecycle_policy`. v5: sem infraestrutura de auditoria — **cards criados: [WT-1509](https://wedotalent.atlassian.net/browse/WT-1509) (retention/cleanup) + [WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) (storage S3/GCS)** |
| R5 | Testes de agentes com fixtures LLM gravadas (snapshot testing) | ✅ LIA | ❌ Não | LIA: `tests/snapshots/` — Wizard, Pipeline + `test_remaining_agents_snapshots.py` (Sourcing, Policy, Kanban, Talent, Jobs) concluído no Sprint D. v5: sem snapshot testing. |
| R6 | Rate limiting por empresa (budget de tokens LLM por tenant) | ✅ LIA | ❌ N/A | LIA: `app/middleware/rate_limiter.py` + `app/services/token_budget_service.py` — Redis `tokens_used_today` por `company_id`, HTTP 429 + `Retry-After`. Implementado no Sprint A. |
| R7 | Fallback determinístico sem LLM para operações críticas | ⚠️ Parcial | ⚠️ Parcial | LIA: resposta forçada quando `max_iterations` esgota. v5: RouterAgent tem 3 estratégias (Memory→Fast→LLM), Fast path é determinístico mas ainda usa LLM em fallback. |
| R8 | Migração gradual — não reescrever de uma vez | ✅ LIA | — N/A | LIA: UV monorepo com migração incremental. v5: projeto novo, não migrou nada. |
| R9 | pgvector + FTS antes de adicionar Elasticsearch | ✅ LIA | ✅ v5 | LIA: pgvector implementado, `tsvector` não explorado. v5: pgvector + `pg_trgm` já em uso. Ambos devem avaliar `tsvector` antes de adotar ES. |
| R10 | Comunicação inter-serviço via RabbitMQ (não HTTP síncrono) | ✅ LIA | ✅ v5 | LIA: infraestrutura pronta (`platform_events.py`, `rabbitmq_producer.py`). v5: RabbitMQ-first como transport principal — mais aderente à recomendação hoje. |
| R11 | LangGraph Studio para debug em dev/staging | ✅ LIA | ❌ Não | LIA: `langgraph.json` configurado (Fase G3). v5: sem configuração de Studio. |
| R12 | Monorepo com libs compartilhadas (UV workspace) | ✅ LIA | ❌ Não | LIA: 9 libs (config, utils, models, audit, messaging, agents-core, services, contexts, auth) — Fase 6a/6b/6c. v5: serviço único sem monorepo. |
| R13 | FastAPI como framework REST | ✅ LIA | ⚠️ Parcial | LIA: FastAPI 100%. v5: FastAPI presente mas o transporte principal é RabbitMQ — REST é secundário. |
| R14 | Auth B2B com SSO/SCIM + company_id em toda query | ✅ LIA | ❌ Não | LIA: WorkOS + `libs/auth/` + company_id em todos os modelos. v5: sem multi-tenancy, sem auth B2B. |
| R15 | SecretsProvider plugável (nunca .env em produção) | ✅ LIA | ❌ Não | LIA: `libs/auth/secrets_provider.py` (Doppler, GCP, Env). v5: usa `.env` diretamente. |
| R16 | Prometheus + Grafana + LangSmith + logs JSON estruturado | ✅ LIA | ❌ Não → [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) | LIA: Prometheus (5 métricas) + LangSmith (Sprint F6 CI step) + Grafana (docker-compose, Sprint B) + Sentry (Sprint B) + structlog. v5: logging básico Python, sem observabilidade estruturada — **card [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) criado para Métricas Prometheus no v5** |
| R17 | PII masking global nos logs (LGPD) | ✅ LIA | ❌ Não | LIA: `install_global_pii_masking()` em workers Celery (SEG-3A) + `strip_pii_for_llm_prompt()` em 6 callers LLM + `response_filter.py` + Sentry PII scrubbing. Global PIIMaskingFilter instalado. v5: sem PII masking nos logs. |
| R18 | AuditCallback como cidadão de primeira classe | ✅ LIA | ❌ Não → [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) | LIA: `libs/audit/audit_callback.py` injetado via LangGraph config — nenhum nó sabe que está sendo auditado. v5: sem audit callback — **card [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) criado para propagar AuditCallback no v5** |
| R19 | Separação PostgreSQL (metadados) + S3 (logs completos) na auditoria | ✅ LIA | ❌ Não → [AUD-005/WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) | LIA: `audit_writer.py` (PostgreSQL) + `audit_storage.py` (S3). v5: sem audit storage — **card [WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) criado para storage externo S3/GCS no v5** |
| R20 | Pydantic settings tipadas com defaults documentados | ✅ LIA | ⚠️ Parcial | LIA: `libs/config/lia_config/config.py`. v5: usa Pydantic para models de request/response, não para settings de configuração. |

---

### Placar por sistema

| Sistema | ✅ Implementado | ⚠️ Parcial | ❌ Não implementado |
|---------|----------------|-----------|-------------------|
| **LIA** | **16** (R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, **R17**, R18, R19, R20) | 4 (R1, R2, R3, R7) | 0 |
| **v5** | 2 (R9, R10) | 4 (R2, R7, R13, R20) | 14 (R1, R3, R4, R5, R6, R11, R12, R14, R15, R16, R17, R18, R19 + R6) |

> **Evolução:** Na revisão original (08/03/2026), LIA tinha 10 ✅. Com os Sprints A–F, G1–G7, I, J, K2, X1, X4, X5 concluídos, mantém **15 ✅ de 20** recomendações por completo (sem regressão). R17 (PII masking): PII masking global ativo em logs (`structlog` filter + `SEG-3A` Celery workers), `strip_pii_for_llm_prompt()` em 6 callers LLM — pode ser atualizado para ✅.

**Leitura:** A LIA implementa **16 das 20** recomendações por completo (R17 PII masking confirmado — SEG-3A + strip_pii_for_llm_prompt). O v5 implementa apenas 2. A maioria das recomendações do André — compliance, auditoria, observabilidade, auth B2B, monorepo, rate limiting, snapshot testing — foram todas implementadas na LIA. Os 5 itens parciais (R1, R2, R3, R7, R17) têm work-in-progress documentado.

Isso é esperado: o v5 foi desenvolvido como protótipo de produto, não como plataforma multi-tenant de produção. As recomendações do André foram pensadas para o contexto da LIA (B2B SaaS, multi-tenant, regulado). Adotar a arquitetura do v5 sem implementar essas recomendações seria regredir nos critérios mais importantes para o negócio.

---

## 21. Itens Pendentes de Análise

Pontos que ficaram de fora das análises anteriores e que o time precisa discutir ou decidir. Organizados por prioridade.

---

> **Atualizado em 15/03/2026.** Itens P2, P6, P8, P9, P10, P12, P13 concluídos nos Sprints A–J. P14 (Coverage) atualizado: 5.400+ testes passando, 29%+ coverage (gate: 25%). Os itens abaixo refletem o estado atual.

### ALTA PRIORIDADE

**P1 — Decisão: quando separar as APIs de domínio?**

As APIs `api-vagas`, `api-funil` e `api-onboarding` existem como scaffold. A questão não é se separar, mas quando. André recomendou fortemente por isolamento de carga — evaluation com LLM tem picos imprevisíveis, CRUD de vagas deve ser <200ms.

Victor concordou com a premissa mas disse que monolito é suficiente agora para ATS. Onboarding pode precisar de separação antes.

**O que precisa ser decidido:**
- Qual API separar primeiro? (Sugestão: `api-funil`, pois tem picos de evaluation WSI)
- Qual é o threshold de degradação que dispara a separação? (ex: p95 CRUD > 500ms)
- Como versionar as APIs separadamente sem quebrar o frontend?
- Comunicação entre APIs: RabbitMQ events (infraestrutura pronta) ou REST síncrono?

**Ação:** definir critério de trigger para separação e responsável por monitorar.

---

**~~P2 — Rate Limiting por Tenant~~ ✅ CONCLUÍDO (Sprint A)**

`app/middleware/rate_limiter.py` + `app/services/token_budget_service.py` — Redis `tokens_used_today` por `company_id`, HTTP 429 com `Retry-After`. Budget configurável por plano.

---

**P3 — Versionamento de Prompts com Métricas (⚠️ Parcial — Sprint B)**

`app/services/prompt_version_registry.py` criado + campo `prompt_version` em `ConversationLog`. **Pendente:** métricas por versão (latência média, custo médio, satisfaction score). Sem isso, é impossível comparar impacto de mudanças de prompt.

**Ação:** adicionar coleta de métricas no registry e dashboard Grafana por `prompt_version`.

---

**~~P4 — TimedToolNode~~ ✅ CONCLUÍDO (Sprint A)**

`libs/agents-core/timed_tool_node.py` — `asyncio.wait_for(tool_call, timeout=15s)` + `ToolError("timeout")` fallback. Timeout configurável por tool.

---

### MÉDIA PRIORIDADE

**~~P5 — Resolução de Referências Conversacionais~~ ✅ CONCLUÍDO (Fase 1 MainOrchestrator)**

`MemoryResolver` expandido com resolução de pronomes ("e ele?"), posição ("o terceiro"), continuidade de filtros (`should_keep_filters()`), e paginação conversacional. Implementado como parte da Fase 1 do MainOrchestrator.

---

**~~P6 — Sentry para Error Tracking~~ ✅ CONCLUÍDO (Sprint B)**

`app/core/sentry.py` + `FastAPIIntegration` + `CeleryIntegration` + PII scrubbing antes do envio. `tests/unit/test_sentry_integration.py` cobrindo a integração.

---

**P7 — Full-Text Search: pgvector + FTS ou Elasticsearch?**

CVs e transcrições de entrevistas WSI precisam de busca full-text eficiente. Hoje a LIA usa pgvector para busca semântica, mas busca textual (ex: "candidatos que mencionaram 'liderança de equipe'") não está otimizada.

**Contexto da reunião com André:** André sugeriu Elasticsearch, mas também disse "considere pgvector + FTS antes de adicionar ES". Victor deve avaliar a complexidade operacional de adicionar ES vs uso do `tsvector`/`tsquery` nativo do PostgreSQL.

**O que avaliar:**
- Benchmark: `tsvector` + `pg_trgm` para busca em texto de CVs (PostgreSQL nativo)
- vs Elasticsearch para busca full-text com ranking BM25
- Critério de decisão: se `tsvector` cobrir 80% dos casos com latência aceitável, não adicionar ES

**Ação:** proof of concept com `tsvector` em dataset de CVs real. Decisão baseada em dados.

---

**~~P8 — Grafana Dashboard~~ ✅ CONCLUÍDO (Sprint B)**

Grafana no `docker-compose.yml` (`grafana/grafana:10.4.2`) + provisioning via `./grafana/provisioning`. Dashboard: hit rate CascadedRouter, latência p50/p95, custo LLM/dia, tool failures. Dashboards JSON versionados no repo.

---

**~~P9 — Human-in-the-Loop interrupt_before/after~~ ✅ CONCLUÍDO (Sprint C + F1 + J)**

Sprint C: `interrupt_before/after` nos 3 fluxos críticos (email massa, mover para oferta, WSI borderline). Sprint F1: persistência DB das ações HITL (`hitl_pending_actions` + `hitl_audit_trail`). Sprint J: `HITLConfirmCard.tsx` — card de aprovação com streaming WebSocket no Float Chat.

---

**~~P10 — Snapshot Testing para Todos os Agentes~~ ✅ CONCLUÍDO (Sprint D)**

`tests/snapshots/test_remaining_agents_snapshots.py` — cobre Sourcing, Policy, Kanban, Talent, JobsManagement. Junto com Wizard + Pipeline já existentes, todos os 7 agentes ReAct têm cobertura de snapshot.

---

### BAIXA PRIORIDADE

**P11 — Ruby vs Python: Decisão Documentada**

André levantou a possibilidade de consolidar stacks. Victor respondeu que se o time tem proficiência igual em Ruby e Python, consolidar ajuda time pequeno. Decisão final: manter Python para o sistema de agentes.

O ADR `docs/adr/001-python-not-ruby.md` deve ser atualizado com o contexto completo desta discussão e a decisão final, incluindo a menção de Ruby GC "Stop the World" que André fez (e que Victor corrigiu — resolvido no Ruby 3.1 com WGIT).

**Ação:** atualizar o ADR com a decisão documentada da reunião.

---

**~~P12 — Celery Flower~~ ✅ CONCLUÍDO (Sprint D)**

`docker-compose.yml` — serviço `flower` (`mher/flower:2.0`) verificado e acessível. Auth básica configurada. URL documentada para o time.

---

**~~P13 — ATS Integration: Reativar domínio arquivado~~ ✅ CONCLUÍDO (Fase 5)**

`ATSIntegrationReActAgent` criado seguindo padrão 4 arquivos (`ats_integration_react_agent.py`, `ats_integration_tool_registry.py`, `ats_integration_system_prompt.py`, `ats_integration_stage_context.py`). Agente wired no WS dispatcher com aliases `"ats_integration"` e `"ats"`. 18 contract tests passando. `useActionIntent` detecta keywords Gupy/Pandapé/importar/sincronizar e roteia para domínio `ats_integration`.

---

**P14 — Coverage: ⚠️ Gate 25% ultrapassado — próximo threshold: 40%**

Coverage atual: **29%+** (gate `pytest.ini`: 25%). Sprint K2 adicionou 39 novos testes de integração (guardrails, RAG, HITL). Suite total: **5.400+ testes passando** (era 4.284+ antes da sessão 15/03/2026).

**Módulos com menor cobertura esperada (para priorizar em sprint futuro):**
- `app/domains/automation/services/` — motor de automação (16 arquivos, poucos testes)
- `app/services/ml/` — outcome_predictor, feature_engineering
- `app/services/` — services stateless são os mais fáceis de testar

**35 falhas + 38 erros pré-existentes** (apenas em `test_api_misc_coverage.py` e `test_job_wizard_graph_langgraph.py`) — não afetam gate.

**Ação (próximo ciclo):** atingir 35%→40%+ com foco nos módulos de menor cobertura.

---

## 22. Mapeamento AUD — Cards Jira de Auditoria do Agente Python V5

> **v9.1 (10/03/2026):** Análise cruzada do documento do André ("Plano de Auditoria — Agente Python") com o código de referência da LIA. 7 gaps identificados, 7 cards Jira criados + Epic.

**Epic**: [WT-1505](https://wedotalent.atlassian.net/browse/WT-1505) — AUD — Auditoria e Compliance do Agente Python

| GAP | Card | Jira Key | Título | Sprint | SP | Prioridade |
|-----|------|----------|--------|--------|----|------------|
| GAP 1 | AUD-001 | [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) | Propagar AuditCallback para ReAct Agents | 1 | 2 | P0 High |
| GAP 2 | AUD-002 | [WT-1507](https://wedotalent.atlassian.net/browse/WT-1507) | Rastrear Tools Chamadas por Nome | 1 | 1 | P1 High |
| GAP 7 | AUD-003 | [WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) | Circuit Breaker no Autonomous Agent | 1 | 2 | P1 High |
| GAP 6 | AUD-004 | [WT-1509](https://wedotalent.atlassian.net/browse/WT-1509) | Retention/Cleanup de agent_executions | 2 | 1 | P2 Medium |
| GAP 3 | AUD-005 | [WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) | Storage Externo para Logs Pesados (S3/GCS) | 3 | 3 | P3 Medium |
| GAP 4 | AUD-006 | [WT-1511](https://wedotalent.atlassian.net/browse/WT-1511) | Endpoints REST de Timeline | 3 | 3 | P3 Medium |
| GAP 5 | AUD-007 | [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) | Métricas Prometheus | 3 | 3 | P3 Medium |

**Total**: 7 cards · 15 story points · ~19h de esforço estimado · 3 sprints

### Distribuição por Sprint

| Sprint | Cards | SP | Esforço | Foco |
|--------|-------|----|---------|------|
| Sprint 1 (Fundação) | AUD-001 + AUD-002 + AUD-003 | 5 | ~5h | Auditabilidade básica + resiliência |
| Sprint 2 (Higiene) | AUD-004 | 1 | ~2h | Limpeza e retenção de dados |
| Sprint 3 (Observabilidade) | AUD-005 + AUD-006 + AUD-007 | 9 | ~12h | Storage externo, API, métricas |

### Referências cruzadas neste documento

| Card | Seções referenciadas |
|------|---------------------|
| AUD-001 / WT-1506 | Tabela Mestra #23, #70 · Seção 12 Observabilidade · Seção 20 R18 |
| AUD-002 / WT-1507 | Tabela Mestra #70 |
| AUD-003 / WT-1508 | Seção 17 Gap v5 (circuit breaker) |
| AUD-004 / WT-1509 | Seção 20 R4 |
| AUD-005 / WT-1510 | Seção 20 R4, R19 |
| AUD-006 / WT-1511 | Seção 12 Observabilidade |
| AUD-007 / WT-1512 | Tabela Mestra #29 · Seção 12 Observabilidade · Seção 14 V5 · Seção 20 R16 |

### Documentação de Referência

- **Diagnóstico completo**: `docs/diagnostico-auditoria-agente-python.md` — 7 gaps detalhados com snippets da LIA e passos de implementação
- **Cards no Jira**: Cada card é autocontido com contexto técnico (stack, fluxo do orquestrador, patterns, diretórios, baseline V5), snippets de código e DoD

---

## Conclusão

O **recruiter_agent_v5** é um projeto mais simples e mais limpo arquiteturalmente, especialmente no que diz respeito ao entry point único (`MessageRouter`) e à memória conversacional rica. A LIA vence em **90+ de 93 dimensões** mapeadas na Tabela Mestra — mas os aprendizados arquiteturais do v5 foram incorporados (MainOrchestrator, MemoryResolver, YAML Tool Registry).

A camada de inteligência da LIA vai muito além do que qualquer comparação superficial capturaria:
- **Personalização invisível** por recrutador (RecruiterPersonalizationService — aprende após 10+ vagas, sem UI de configuração)
- **Sistema de aprendizado contínuo** (7 padrões, FeedbackLearningService, LearningLoopService 1073L)
- **Human-in-the-loop estruturado** (5 tipos ApprovalRequest, HITL Persistence DB, HITLConfirmCard WebSocket)
- **Orquestração multi-source com consensus** (7 fontes priorizadas + 3-layer cache)
- **Automação de pipeline** (AutomationReActAgent, stage_automation_engine 15+ triggers, APScheduler)
- **Alertas proativos inteligentes** (proactive_alert_service 5 categorias + prediction_action_bridge)
- **Predição de outcomes via ML** (OutcomePredictor 532L, PipelinePredictionService, ProactiveWorker)
- **Explicabilidade** auditável por candidato, agente e auditor (ExplainabilityService 322L)
- **Controle de custo por tenant** (TokenTrackingService 722L, rate_limiter.py, alertas 80%/100%)
- **A/B testing de prompts** com chi-square, stratification e effect_size (ABTestingService 306L)
- **WSI proprietário** com Taxonomia de Bloom, scorer determinístico e calibração por senioridade
- **Inteligência semântica** em 7 domínios (semantic_search_service 442L, Gemini, Redis cache P95 < 300ms)
- **Fine-tuning export** com anonimização PII e formato Claude/OpenAI para melhoria contínua do modelo

Nenhuma dessas capacidades existe no v5 — elas representam a principal vantagem competitiva da LIA e foram construídas com o produto em produção em mente (LGPD, SOX, ISO 27001, BCB 498, EU AI Act).

O caminho correto não é reescrever a LIA no modelo do v5, nem ignorar as lições do v5. É **usar o v5 como espelho** para identificar onde a LIA estava fragmentada — e o MainOrchestrator, MemoryResolver e YAML Registry foram exatamente isso.

Das 20 recomendações do André, **15 estão totalmente implementadas** e 5 parcialmente — evoluindo de 10 implementadas na revisão original (08/03/2026). A principal pendência estrutural é a separação das APIs por domínio (P1) e a cobertura de testes (P14).

O próximo ciclo (Sprint K+) tem foco claro: coverage 40%, deploy da api-funil como primeiro micro-serviço independente, e métricas por versão de prompt. Em paralelo, os 7 cards AUD (Seção 22) fornecem o roadmap para fechar os gaps de auditabilidade, resiliência e observabilidade no agente Python V5. **Sprints Z1–Z7 + F1-02/F1-03/F2-04 concluídos (19/03/2026):** decomposição Kanban/Pipeline, OpenTelemetry OTLP, Presidio NER Layer 4, RecruiterBehaviorService, DLQ Celery, FairnessGuard no learning loop, SLOs formais.

---

*Revisão 10/03/2026. Sprints A–F, G1–G7, I e J concluídos + AUD Audit Cards (WT-1506→WT-1512). Base: análise de 215+ arquivos do backend LIA + RECRUITER_AGENT_V5_DOCUMENTACAO_COMPLETA.md + guia de arquitetura André (guia_arquitetura_ia_v1.0.md) + notas de reunião de arquitetura + Plano de Auditoria do Agente Python (André).*
