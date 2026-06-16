# Relatório Completo de Capacidades e Prompts — LIA (WeDOTalent)
**Versão:** 4.4 — 19/03/2026 *(v4.4: Sprints Z2-01, Z3-02, F2-04, Z5-02, Z5-03, Z6-01, Z6-02, Z6-03, Z7-01 — LearningSnapshotService, DLQService, OpenTelemetry OTLP, Presidio NER Layer 4, ATS clients consolidados em shim, RecruiterBehaviorService, threshold semântico configurável, updated_at nos prompts YAML; v4.3: Guia de Entrada para Agentes IA adicionado no topo — 25 verificações com comandos grep executáveis, critérios pass/fail, arquivos canônicos por bloco; v4.2: Seções 5, 9, 13, 15, 17, 18, 25, 34 atualizadas; v4.1: Seções 31–33 atualizadas; v4.0: Parte VII adicionada)*
**Fonte:** Auditoria direta do código-fonte (`lia-agent-system/` + `plataforma-lia/`)
**Propósito:** Guia técnico-estratégico exaustivo e autocontido para replicação da camada de inteligência da plataforma LIA. Cobre toda a arquitetura de prompts, 16 agentes (12 ReAct + 4 StateGraph), orquestração, ferramentas, WebSocket, automação, inteligência preditiva, aprendizado contínuo, observabilidade, resiliência, compliance, governança, templates, infraestrutura LLM e referências de arquivo.

**Metodologia:** Auditoria de 13/03/2026 via leitura direta de arquivos-fonte. Verificados: 206 endpoints, 231 serviços, 99 models, 37 migrações (47 após Y1–Y5), 114 hooks, 90 páginas, 227 arquivos de teste, 17 métricas Prometheus (14 originais + 3 adicionadas em Y1), 12 domínios DDD. Escopos (`scope_config.py`), registros de agentes (`react_agent_registry.py`), ferramentas, templates de prompt e serviços auditados individualmente. Exemplos marcados como "ilustrativo" são sintéticos baseados nos templates/schemas do código; os demais refletem schemas e formatos reais. Recomenda-se revisão mensal.

**Público-alvo:** Equipe de desenvolvimento, agentes de IA codificadores (Claude Code, Cursor), arquitetos de software e stakeholders técnicos que precisem replicar a inteligência da plataforma LIA em produto paralelo.

---

## GUIA DE DIAGNÓSTICO PARA AGENTES IA — Como Implementar e Verificar Capacidades

> **Se você é um agente IA (Claude Code / Cursor) usando este documento para diagnosticar ou comparar um produto:** comece aqui. Esta seção contém os 25 comandos de verificação executáveis com critérios pass/fail. Para detalhes de cada capacidade, vá para a **Seção 35**. Para auditar achados de compliance e segurança, use também `docs/RELATORIO_AUDITORIA_LIA.md` (seu próprio Guia de Diagnóstico).

### Como usar este documento

1. **Execute o checklist abaixo** no codebase alvo — cada item tem um `grep` executável e critério pass/fail
2. **Para cada FAIL**, consulte a tabela de mapeamento (abaixo) para ir direto à subseção 35.X correta
3. **O repositório de referência** é `https://github.com/talensestg/wedotalent02202026` — use-o como ground truth para comparar implementações
4. **CLAUDE.md do repo de referência:** o arquivo `CLAUDE.md` na raiz do repositório de referência contém o contexto completo da plataforma (stack, arquitetura, convenções). Claude Code lê este arquivo automaticamente ao abrir o projeto. Se estiver auditando outro projeto, passe explicitamente como contexto adicional.

### Prompt de Invocação — Como usar com Claude Code / Cursor

Copie e cole o seguinte prompt ao iniciar uma sessão de diagnóstico:

```
Você vai diagnosticar este codebase comparando com a plataforma LIA (WeDOTalent).

Documentos de referência (leia nesta ordem):
1. relatorio_capacidades_prompts_lia.md — seção "GUIA DE DIAGNÓSTICO PARA AGENTES IA" (topo do documento)
2. docs/RELATORIO_AUDITORIA_LIA.md — seção "GUIA DE DIAGNÓSTICO PARA AGENTES IA" (após os changelogs)

Tarefa:
1. Execute TODOS os comandos grep dos dois guias neste codebase
2. Liste os FAILs por bloco (P0 primeiro, depois P1, P2, Y1-Y5)
3. Para cada FAIL: leia a subseção 35.X indicada na tabela de mapeamento
4. Compare com o repositório de referência: https://github.com/talensestg/wedotalent02202026
5. Proponha implementação seguindo o padrão do repositório de referência

Comece pelos itens P0 (bloqueantes para produção).
```

### Checklist de Diagnóstico Rápido — 25 Verificações Críticas

Execute cada comando no diretório raiz do projeto backend (`lia-agent-system/` ou equivalente):

#### BLOCO A — Compliance e Proteção (P0 — inegociáveis)

| # | Capacidade | Comando de Verificação | Critério PASS |
|---|-----------|----------------------|---------------|
| A1 | FairnessGuard ativo | `grep -r "FairnessGuard\|fairness_guard" app/ --include="*.py" -l` | ≥ 5 arquivos — deve estar em orchestrator + agentes + mixin |
| A2 | FairnessGuard 3 camadas | `grep -r "check_with_layer3\|IMPLICIT_BIAS\|_PATTERNS_VERSION" app/ --include="*.py"` | Deve encontrar Layer 3 + termos implícitos + versão ≥ 2 |
| A3 | PII Masking em logs | `grep -r "PIIMaskingFilter\|install_global_pii_masking" app/ --include="*.py"` | Deve estar em `logging_config.py` E em `celery_app.py` (workers); Layer 4 Presidio opt-in via `LLM_PROMPT_PRESIDIO_ENABLED` (Z6-03) |
| A4 | PII strip em prompts LLM | `grep -r "strip_pii_for_llm_prompt" app/ --include="*.py" -l` | ≥ 4 callers: rubric_eval, analysis, voice_screening, candidate_compare; Layer 4: `grep -r "_presidio_layer4_strip\|PRESIDIO_ENABLED" app/` |
| A5 | Consentimento LGPD Gate 1 | `grep -r "LGPD_CONSENT\|consent_checker\|ai_screening" app/ --include="*.py"` | Deve bloquear em `wsi_interview_graph.py` com `LGPD_CONSENT_REVOKED` |
| A6 | HITL em decisões críticas | `grep -r "request_approval\|hitl_service" app/ --include="*.py" -l` | ≥ 3 arquivos: wizard_graph, wsi_graph, pipeline_agent |
| A7 | Audit trail append-only | `grep -r "log_decision\|audit_service" app/ --include="*.py" -l` | ≥ 8 arquivos (todos os agentes principais) |
| A8 | Anti-sycophancy em prompts | `grep -r "ANTI_SYCOPHANCY\|anti_sycophancy" app/ --include="*.py" -l` | ≥ 10 arquivos — todos os system_prompts dos agentes |

#### BLOCO B — Resiliência e Infraestrutura (P1 — produção)

| # | Capacidade | Comando de Verificação | Critério PASS |
|---|-----------|----------------------|---------------|
| B1 | Circuit breakers em providers | `grep -r "circuit_breaker_decorator\|@circuit" app/ --include="*.py" -l` | ≥ 8 arquivos: openai, gemini, gupy, pandape, sendgrid, resend, pearch, workos |
| B2 | Fallback LLM chain | `grep -r "FALLBACK_ORDER\|llm_cascade\|LLMCascade" app/ --include="*.py"` | Deve ter lista `["claude", "gemini", "openai"]` ou equivalente |
| B3 | Token budget por tenant | `grep -r "TokenBudget\|token_budget\|MONTHLY_LIMIT" app/ --include="*.py"` | Deve existir serviço + Redis tracking por `company_id` |
| B4 | Celery beat schedules | `grep -r "beat_schedule" . --include="*.py"` | ≥ 8 entradas: drift, lgpd, briefing, followup, wsi-abandoned, ragas, routing, agent-registry, rag-rebuild, ml-feedback; **DLQ** via `process_dlq_task` (F2-04); **RecruiterBehavior** via `compute_behavior_profiles_task` (Z7-01) |
| B5 | Rate limiting | `grep -r "RateLimiter\|rate_limit\|rate_limiter" app/ --include="*.py"` | Deve existir middleware por tenant |
| B6 | Multi-tenant em models | `grep -r "company_id" app/models/ --include="*.py" -l` | ≥ 20 models com `company_id` column |

#### BLOCO C — Inteligência e Agentes (P1 — diferencial)

| # | Capacidade | Comando de Verificação | Critério PASS |
|---|-----------|----------------------|---------------|
| C1 | Agents Registry YAML | `find . -name "agents_registry.yaml" -o -name "agent_registry_watcher.py"` | Ambos devem existir |
| C2 | Multi-model por agente | `grep -r "model_override\|multi_model\|agent_model_config" app/ --include="*.py"` | Deve existir config por agente com fallback |
| C3 | RAG híbrido por domínio | `grep -r "BM25\|alpha.*blend\|rebuild_domain" app/ --include="*.py"` | BM25 + pgvector com alpha param + rebuild task |
| C4 | Adaptive routing com aprendizado | `grep -r "RoutingFeedback\|record_correction\|compute_domain_confidence" app/ --include="*.py"` | Todos os 3 devem existir |
| C5 | ML feedback loop | `grep -r "recruiter_decision_feedback\|process_ml_feedback\|recompute_active_ml" app/ --include="*.py"` | Modelo + task + beat schedule |
| C6 | Streaming ReAct via WS | `grep -r "astream_events\|on_chat_model_stream\|StreamingReAct" app/ --include="*.py"` | Deve existir em agent e em websocket handler |
| C7 | Agent Bus (comunicação entre agentes) | `grep -r "AgentBus\|agent_bus\|lia:agent_bus" app/ --include="*.py"` | Redis pub/sub com canal `lia:agent_bus:` |
| C8 | Event Sourcing imutável | `grep -r "DomainEvent\|event_store\|sequence_number" app/ --include="*.py"` | Model + service + UniqueConstraint em sequence_number |

#### BLOCO D — Observabilidade e Qualidade (P2)

| # | Capacidade | Comando de Verificação | Critério PASS |
|---|-----------|----------------------|---------------|
| D1 | Métricas Prometheus per-agent | `grep -r "agent_llm_calls_total\|agent_latency_seconds\|agent_confidence" app/ --include="*.py"` | 3 métricas — calls, latency, confidence |
| D2 | Confidence calibration | `grep -r "record_confidence\|confidence_action" app/ --include="*.py" -l` | ≥ 8 arquivos — todos os agentes principais |
| D3 | Model drift detection | `grep -r "drift_service\|run_drift_check\|ModelDrift" app/ --include="*.py"` | Service + Celery task + beat schedule diário |
| D4 | WSI assíncrono | `grep -r "WsiSession\|wsi_async\|wsi_invite_token" app/ --include="*.py"` | Model com status enum + service + endpoint |
| D5 | OpenTelemetry tracing (Z6-02) | `grep -r "OTEL_TRACES_ENABLED\|trace_span\|LightweightTracer" app/ --include="*.py"` | tracing.py com suporte OTLP + @trace_span em Router, DLQ e LearningLoop; fallback gracioso se lib não instalada |

### Interpretação dos Resultados

```
PASS em todos A1–A8  → Compliance OK (produção segura)
FAIL em qualquer A   → BLOQUEANTE — não deploy sem corrigir
PASS em B1–B6        → Resiliência OK
FAIL em B1 (circuits) → ALTO RISCO — providers externos sem proteção
PASS em C1–C8        → Inteligência completa (diferencial competitivo)
FAIL em C            → GAP funcional — priorizar por impacto no produto
PASS em D1–D5        → Observabilidade OK
FAIL em D            → Risco operacional — sem visibilidade em produção
```

### Como Corrigir um FAIL

1. Na tabela abaixo, encontre o código que falhou e vá para a **Seção 35.X indicada** (use `offset=<linha>` no Read tool para ir direto)
2. A subseção tem: O que é → Onde está → Como implementar → Como testar
3. Compare com o arquivo canônico em `https://github.com/talensestg/wedotalent02202026`
4. Implemente seguindo o padrão exato do repositório de referência

#### Mapeamento FAIL → Seção 35 (com linha para Read tool)

| Código | Capacidade | Seção 35 | Linha aprox. |
|--------|-----------|----------|-------------|
| A1, A2 | FairnessGuard (3 camadas + Layer 3) | 35.1 | 5586 |
| A3, A4 | PII Masking (logs + prompts LLM) | 35.13 | 6081 |
| A5 | Consentimento LGPD Gate 1 | 35.12 | 6045 |
| A6 | HITL — Human-in-the-Loop | 35.3 | 5670 |
| A7 | Audit Trail append-only | 35.8 | 5859 |
| A8 | Anti-Sycophancy em prompts | 35.4 | 5709 |
| B1 | Circuit Breakers em providers | 35.2 | 5631 |
| B2 | LLM Fallback chain (Claude→Gemini→OpenAI) | 35.5 | 5744 |
| B3 | Token Budget por tenant | 35.22 | 6310 |
| B4 | Celery Beat Schedules | 35.9, 35.10, 35.11 | 5899 |
| B5 | Rate Limiting por tenant | 35.22 | 6310 |
| B6 | Multi-tenant em models | 35.22 | 6310 |
| C1 | YAML Hot-Reload de Agentes | 35.9 | 5899 |
| C2 | Multi-Model por agente | 35.19 | 6239 |
| C3 | RAG Híbrido por domínio | 35.10 | 5937 |
| C4 | Adaptive Routing com aprendizado | 35.6 | 5784 |
| C5 | ML Feedback Loop | 35.11 | 5974 |
| C6 | Streaming ReAct via WS | 35.20 | 6267 |
| C7 | Agent Bus (comunicação entre agentes) | 35.7 | 5822 |
| C8 | Event Sourcing imutável | 35.8 | 5859 |
| D1 | Métricas Prometheus per-agent | 35.15 | 6116 |
| D2 | Confidence Calibration | 35.16 | 6153 |
| D3 | Model Drift Detection | 35.15 | 6116 |
| D4 | WSI Assíncrono | 35.17 | 6183 |

### Arquivos Canônicos por Bloco (referência rápida)

```
Bloco A — Compliance:
  app/shared/compliance/fairness_guard.py     ← FairnessGuard
  app/shared/pii_masking.py                   ← PII Masking
  app/services/consent_checker_service.py     ← Consentimento
  app/services/hitl_service.py               ← HITL
  app/shared/compliance/audit_service.py     ← Audit Trail
  app/shared/prompts/anti_sycophancy_block.py ← Anti-sycophancy

Bloco B — Resiliência:
  app/shared/resilience/circuit_breaker.py   ← Circuit Breakers
  app/orchestrator/llm_cascade.py            ← LLM Fallback
  app/services/token_budget_service.py       ← Token Budget
  libs/config/lia_config/celery_app.py       ← Beat Schedules

Bloco C — Inteligência:
  app/agents_registry.yaml                   ← Registry YAML
  app/core/agent_registry_watcher.py         ← Hot-reload
  app/services/rag_pipeline_service.py       ← RAG híbrido
  app/services/routing_learning_service.py   ← Adaptive Routing
  app/services/ml_feedback_service.py        ← ML Feedback
  app/shared/agents/agent_bus.py             ← Agent Bus
  app/services/event_store_service.py        ← Event Sourcing

Bloco D — Observabilidade:
  app/observability/metrics.py               ← Prometheus
  app/shared/observability/agent_metrics.py  ← Per-agent metrics
  app/services/model_drift_service.py        ← Model Drift
```

---

## Sumário

> **Agentes IA:** leia o [Guia de Entrada](#guia-de-entrada--para-agentes-ia-claude-code--cursor) antes do sumário — contém os 25 comandos de diagnóstico rápido.

**Parte I — Arquitetura e Agentes**
1. [Arquitetura de Prompts e Interação entre Chats](#1-arquitetura-de-prompts-e-interação-entre-chats)
2. [Os 12 Agentes ReAct](#2-os-12-agentes-react)
3. [Os 4 Agentes StateGraph + PolicySetupAgent](#3-os-4-agentes-stategraph--policysetupagent)
4. [Arquitetura DDD e Catálogo de Domínios](#4-arquitetura-ddd-e-catálogo-de-domínios)
5. [Arquitetura WebSocket e Domain Dispatch](#5-arquitetura-websocket-e-domain-dispatch)

**Parte II — Capacidades e Ferramentas**
6. [Capacidades Detalhadas](#6-capacidades-detalhadas)
7. [Templates de Resposta do Chat](#7-templates-de-resposta-do-chat)
8. [Análises e Relatórios](#8-análises-e-relatórios)
9. [Sistema Preditivo e Insights](#9-sistema-preditivo-e-insights)
10. [Quick Actions e Ações Bulk](#10-quick-actions-e-ações-bulk)
11. [Registro de Ferramentas por Agente](#11-registro-de-ferramentas-por-agente)

**Parte III — Infraestrutura de IA**
12. [Infraestrutura de Prompts](#12-infraestrutura-de-prompts)
13. [Camada de Inteligência — Shared Services](#13-camada-de-inteligência--shared-services)
14. [Motor de Automação](#14-motor-de-automação)
15. [Camada de Aprendizado Contínuo](#15-camada-de-aprendizado-contínuo)
16. [Infraestrutura — LLM Factory, Policy Middleware, Templates](#16-infraestrutura--llm-factory-policy-middleware-templates)
17. [Observabilidade e Monitoramento](#17-observabilidade-e-monitoramento)

**Parte IV — Resiliência e Custos**
18. [Resiliência e Circuit Breakers](#18-resiliência-e-circuit-breakers)
19. [Gestão de Custos e Token Tracking](#19-gestão-de-custos-e-token-tracking)
20. [ConfidencePolicyService — Autonomia de Ações](#20-confidencepolicyservice--autonomia-de-ações)

**Parte V — Governança e Compliance**
21. [Governança de Agentes](#21-governança-de-agentes)
22. [FairnessGuard — 3 Camadas de Proteção Anti-Viés](#22-fairnessguard--3-camadas-de-proteção-anti-viés)
23. [Pre-Qualification Pipeline](#23-pre-qualification-pipeline)
24. [Personalized Feedback Service](#24-personalized-feedback-service)
25. [LGPD — Proteção de Dados Pessoais](#25-lgpd--proteção-de-dados-pessoais)
26. [EU AI Act — Conformidade com IA de Alto Risco](#26-eu-ai-act--conformidade-com-ia-de-alto-risco)
27. [Compliance Multi-Framework](#27-compliance-multi-framework)
28. [Framework de Teste de Viés — Bias Audit Service](#28-framework-de-teste-de-viés--bias-audit-service)
29. [Model Drift e Monitoramento Contínuo](#29-model-drift-e-monitoramento-contínuo)
30. [Taxonomia de Incidentes](#30-taxonomia-de-incidentes)

**Parte VI — Status e Evolução**

> **v4.1 (15/03/2026):** Seções 31–33 atualizadas para refletir Sprints Y1–Y5. 15/15 oportunidades resolvidas. Seção 33 reclassificada de "Ausentes" para "Resolvidos".

31. [Production Readiness](#31-production-readiness)
32. [Limitações, Dívidas Técnicas e Funcionalidades Incompletas](#32-limitações-dívidas-técnicas-e-funcionalidades-incompletas)
33. [Oportunidades e Capacidades Ausentes](#33-oportunidades-e-capacidades-ausentes)
34. [Referência Completa de Arquivos](#34-referência-completa-de-arquivos)
**Parte VII — Guia de Implementação para Agentes IA**
35. [Guia de Diagnóstico e Implementação — Claude Code / Cursor](#35-guia-de-diagnóstico-e-implementação--claude-code--cursor)

---

## 1. Arquitetura de Prompts e Interação entre Chats

### 1.1 Os 3 Níveis de Chat

A plataforma possui **3 camadas de chat** com contextos, escopos e lógica de decisão distintos:

#### 1.1.1 Float Chat (candidates-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Contexto:** Página de funil de talentos (listagem geral de candidatos)
- **Escopo de ferramentas:** `TALENT_FUNNEL` — `scope_config.py` filtra ferramentas para:
  - **Query (11):** `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `compare_candidates`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns`
  - **Action (9):** `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `send_email`, `send_whatsapp`, `send_bulk_email`, `export_candidates`
- **Endpoint API:** `callOrchestratedTalentChat()` → `POST /api/backend-proxy/orchestrator/talent-chat`
- **Backend:** `app/api/v1/orchestrated_talent_chat.py` (v3.0 — ActionExecutor + PendingActionState + closed-loop)
- **Estado expandido (Super Prompt):** Gerenciado via `LiaFloatContext` (`lia-float-context.tsx`):
  - `isOpen` / `isExpanded` — Float mini vs. Super Prompt expandido
  - `expand()` / `collapse()` — Transição entre modos
  - `sharedMessages` — Mensagens compartilhadas entre mini e expandido

**Lógica de decisão local vs. delegar (`handleLIAChatMessage`, linha 5659):**

```
1. Mensagem recebida → normalizar
2. Verificar se é COMANDO DE ANÁLISE (analysisCommands[]):
   - "analisar potencial", "resumo executivo", "top 5", "comparar", etc.
   → Se sim: handleAICommand(message) [processamento IA via backend]
3. Verificar se é PERGUNTA GENÉRICA (isGenericQuestion, linha 5617):
   - Regex: /^(o que|como|por que|quando|onde|quem|quanto)/, /?$/
   - EXCETO se contém searchKeywords: "desenvolvedor", "python", "react", "são paulo", etc.
   → Se é pergunta genérica SEM keywords: handleOrchestratedTalentMessage() → backend orquestrador
4. Senão: executar como BUSCA DE CANDIDATOS via executeSearch()
```

**Função `isGenericQuestion()` (linha 5617):**
- **Input:** texto do usuário
- **Processing:** Verifica regex de padrões interrogativos + ausência de keywords de busca
- **Output:** `boolean` — true se é pergunta genérica (vai para orquestrador), false se é busca
- **Keywords de busca (46 termos):** cargos (desenvolvedor, gerente, analista...), tecnologias (python, react, node...), localidades (são paulo, remoto...), senioridades (junior, pleno, senior...)

#### 1.1.2 Kanban Chat (job-kanban-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Contexto:** Kanban de uma vaga específica (pipeline de candidatos por etapa)
- **Escopo de ferramentas:** `IN_JOB` — `scope_config.py` filtra para:
  - **Query (14):** `get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts`
  - **Action (11):** `update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`
- **Endpoint API:** `callOrchestratedJobChat()` → `POST /api/backend-proxy/orchestrator/job-chat`
- **Backend:** `app/api/v1/orchestrated_job_chat.py` (v2.0 — closed-loop action execution)

**Lógica de decisão (backend — `orchestrated_job_chat.py`):**

```
1. Request recebida com job_context + candidates + message
2. Backend detecta command_type via detect_command_type(message) → KanbanCommandType
3. Se command_type ∈ _ANALYTICAL_COMMAND_TYPES (12 tipos): análise IA
4. Se command_type ∈ ACTIONABLE_INTENTS: executa ação via ActionExecutor
5. Se é confirmação/rejeição de ação pendente: resolve via PendingActionStore
6. Senão: roteia para Orchestrator.process_request() com contexto enriquecido
```

#### 1.1.3 Chat Dedicado (chat-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Contexto:** Chat full-page com LIA — acesso a todas as capacidades
- **Escopo:** `GLOBAL` — ferramentas restritas a `generate_report` e `schedule_report` (ver `scope_config.py`)
- **Endpoint API:** `liaApi.orchestratorProcess()` → `POST /api/backend-proxy/orchestrator/process` (com suporte a WebSocket via `wsSendMessage`)
- **Capacidades completas:**
  - Quick actions pré-definidas: "Criar uma nova vaga", "Solicitar aprovação", "Compartilhar candidatos com gestor", "Solicitar feedback de entrevista", "Consultar candidato", "Adicionar candidato", "Reagendar entrevista"
  - Ações contextuais sobre candidatos selecionados: comparar perfis, adicionar a vaga
  - Busca via Pearch AI (deep search externo) e busca local
  - Histórico de conversas persistente
  - Suporte a anexos (arquivos + áudio)
  - Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)

**Lógica:** Todas as mensagens vão diretamente ao backend via `sendMessage()`. O backend processa via `Orchestrator.process_request()` com escopo GLOBAL.

### 1.2 Diagrama de Interação

```
┌─────────────────────────────────────────────────────────┐
│  Float Chat (candidates-page)                           │
│  Escopo: TALENT_FUNNEL                                  │
│  Decisão: isGenericQuestion() → orquestrador            │
│           analysisCommands → handleAICommand             │
│           default → executeSearch (busca candidatos)     │
│  → callOrchestratedTalentChat() → /orchestrator/talent-chat │
├─────────────────────────────────────────────────────────┤
│  Kanban Chat (job-kanban-page)                          │
│  Escopo: IN_JOB                                        │
│  Decisão: detect_command_type() → KanbanCommandType     │
│           analytical → análise IA                        │
│           actionable → ActionExecutor                    │
│  → callOrchestratedJobChat() → /orchestrator/job-chat    │
├─────────────────────────────────────────────────────────┤
│  Chat Full (chat-page)                                  │
│  Escopo: GLOBAL                                         │
│  → liaApi.orchestratorProcess() → /orchestrator/process  │
│  (+ WebSocket wsSendMessage)                            │
└──────────────────────────┬──────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Orchestrator │
                    │ + CascadedR. │
                    └──────┬──────┘
                           │ domain dispatch
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        [16 Agentes — 12 ReAct + 4 StateGraph]
```

### 1.3 CascadedRouter — 6 Tiers de Roteamento

**Arquivo:** `lia-agent-system/app/orchestrator/cascaded_router.py`

| Tier | Nome                | Mecanismo                          | Custo  | Detalhe                                          |
|------|---------------------|------------------------------------|--------|--------------------------------------------------|
| 0    | MemoryResolver      | Resolução de pronomes/referências  | Zero   | Via `WorkingMemory`; resolve "ele", "essa vaga"  |
| 1    | LRU in-process      | Hash MD5 em memória local          | Zero   | Cache O(1); não distribuído entre workers        |
| 2    | Redis hash cache    | Distribuído, exato, entre workers  | Baixo  | TTL configurável via `ROUTER_CACHE_TTL`          |
| 3    | VectorSemanticCache | pgvector, cosine similarity configurável via `ROUTER_VECTOR_SIMILARITY_THRESHOLD` (default 0.92) | Baixo  | Habilitável via `ROUTER_VECTOR_CACHE_ENABLED`; near-miss logging via `ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN` (default 0.05); falha graciosamente se indisponível |
| 4    | FastRouter          | Regex/keyword patterns             | Baixo  | `fast_router.py`; confiança mínima: `ROUTER_FAST_CONFIDENCE_THRESHOLD` |
| 5    | LLM Cascade         | Haiku → Sonnet → Opus              | Alto   | Via `llm_cascade.py`; IntentRouter com **20 exemplos few-shot T3 RH sênior** (Sprint X4/J2) |
| FB   | Clarification       | Pergunta ao usuário                | Zero   | 6 opções padrão quando nenhum tier resolve       |

**Fallback de clarificação — 6 opções padrão:**
1. "Criar ou gerenciar uma vaga"
2. "Buscar ou avaliar candidatos"
3. "Acompanhar pipeline / triagem"
4. "Agendar entrevistas"
5. "Relatórios e analytics"
6. "Outra solicitação"

**Mapeamento Agent → Domain (`AGENT_TYPE_TO_DOMAIN`):**
```python
{
    "job_planner": "job_management",   "job_intake": "job_management",
    "sourcing": "sourcing",            "cv_screening": "cv_screening",
    "screening": "cv_screening",       "wsi_evaluator": "cv_screening",
    "interviewer": "interview_scheduling", "scheduling": "interview_scheduling",
    "analyst_feedback": "analytics",   "analytics": "analytics",
    "communication": "communication",  "ats_integrator": "ats_integration",
    "recruiter_assistant": "recruiter_assistant", "task_planner": "automation",
}
```

**Métricas Prometheus:** `router_tier_hit_total`, `router_latency_ms`, `router_confidence_histogram`

### 1.3.1 IntentRouter — Few-shot T3 RH Sênior (Sprint X4/J2 — 15/03/2026)

**Arquivo:** `lia-agent-system/app/orchestrator/intent_router.py` — `_create_intent_prompt()`

O IntentRouter (Tier 5 LLM do CascadedRouter) foi aprimorado com **seção `## EXEMPLOS FEW-SHOT — RH Sênior (T3)`** contendo **20 exemplos estruturados** calibrados para o perfil de RH sênior brasileiro:

| Grupo | Qtd | Confiança | Intents Cobertos |
|:------|:---:|:---------:|:-----------------|
| Claros (alta confiança) | 10 | ≥0.93 | `job_planner`, `sourcing`, `cv_screening`, `scheduling`, `funnel_analysis`, `feedback`, `sync_ats`, `daily_briefing`, `wsi_evaluator`, `interviewer` |
| Ambíguos (confiança moderada) | 10 | 0.72–0.81 | `atualizar_status`, `funnel_analysis vs assistant`, `wsi_evaluator readiness`, `rank_candidates vs sourcing`, `bottleneck_detection`, `feedback mass comm`, `time_to_fill_prediction`, `sugerir_melhorias`, `pipeline stuck`, `analisar_perfil` |

**Formato de cada exemplo:**
```
Input: "Preciso criar uma nova vaga de desenvolvedor senior"
Output: {"intent": "job_planner", "confidence": 0.97, "reasoning": "Criação explícita de vaga", "requires_planning": true}
```

**Validação:** `tests/unit/test_ach020_api_docs.py::TestIntentRouterFewShot` — 9 testes automáticos verificando presença, quantidade (≥20), contexto RH, intents-chave.

### 1.4 Orchestrator — Fluxo de Processamento

**Arquivo:** `lia-agent-system/app/orchestrator/orchestrator.py`

**System prompt principal da LIA:**
```
Você é LIA, a assistente inteligente de recrutamento da WeDOTalent.
Profissional de RH experiente, amigável e eficiente.
Capacidades: criar/gerenciar vagas, buscar candidatos, triagem curricular,
entrevistas WSI, avaliação científica, agendar entrevistas, relatórios/KPIs,
feedback e comunicações.

Regra anti-sycophancy: nunca confirme pedidos discriminatórios ou que violem compliance.
Apresente alternativas com dados quando necessário.
```

**Fluxo `process_request()` (linha 104):**
```
1. Sanitização: sanitize_text(message)
2. Cancelamento: CancellationHandler.is_cancellation_request() → "Ok, operação cancelada"
3. Reinício: CancellationHandler.is_restart_request() → limpa estado, "Vamos recomeçar!"
4. Contexto: recupera state (last_agent, current_job, current_candidate)
5. Roteamento: CascadedRouter.route() → RouteResult {domain_id, confidence, source}
6. Cache: se intent ∈ cacheable_intents → retorna resposta cacheada
7. Política: PolicyEngine.validate_request() → allowed/denied
8. Plano multi-step: PlanDetector.detect() → PlanExecutor.execute() [não-blocking; falha silenciosa]
9. Domínio: DomainRegistry.get_instance(domain_id) → DomainWorkflow.process()
10. Detecção técnica: se resposta contém padrões técnicos → fallback LLM (Claude)
11. Cache: armazena resposta se intent cacheável
```

**Detecção de resposta técnica** (string matching — `_TECHNICAL_PATTERNS`):
- "Keyword heuristic matched"
- "Ferramenta '"
- "Ação '"
- "encaminhada para o agente"
- "executada para ação"
- "Processado com sucesso."

**Intents cacheáveis:**
`pipeline_stats`, `job_status`, `candidate_count`, `stage_distribution`, `funnel_analysis`, `job_insights`, `market_data`, `salary_benchmark`, `analytics`, `recommendations`, `skills_analysis`, `candidate_search`

**Memória conversacional (`process_request_with_memory`, linha 240):**
- Histórico limitado a 20 mensagens por contexto LLM
- Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)
- `ConversationState` mantém estado entre turnos

---

## 2. Os 12 Agentes ReAct

**Arquivo de registro:** `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py`

**Arquitetura:**
- Padrão Singleton (`ReactAgentRegistry`)
- Armazena CLASSES (não instâncias) + configs
- Instanciação lazy via `get_agent()` (cacheado, NÃO session-safe) ou `AgentFactory.create_agent()` (session-safe, com `WorkingMemoryService` e `ReActObserver` isolados)
- Todos herdam de `LangGraphReActBase` + `EnhancedAgentMixin`
- Ciclo ReAct: Thought → Action → Observation → (repete até max_iterations)
- Anti-sycophancy presente em todos (via bloco `ANTI_SYCOPHANCY_OPERATIONAL` importado OU regra equivalente no prompt)
- **Padrão 4-File por agente:** `{domain}_react_agent.py` + `{domain}_tool_registry.py` + `{domain}_system_prompt.py` + `{domain}_stage_context.py`
- **Ciclo de vida obrigatório (6 etapas):** Memory load → Guardrail resolution → Tool assembly → Configuration → ReAct execution → Post-loop learning

**Regras universais em todos os system prompts:**
1. Idioma estritamente PT-BR
2. Persona profissional, proativa e consultiva
3. Anti-sycophancy: desafiar inputs enviesados ou incorretos com dados
4. Nunca expor JSON, stack traces, IDs internos ao usuário
5. Multi-tenancy: isolamento estrito por `company_id`

### 2.1 Wizard Agent (Criação de Vagas)
- **Domain:** `wizard` | **Classe:** `WizardReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/job_management/agents/wizard_react_agent.py`
- **Escopo:** Criação guiada de vagas com sugestões inteligentes
- **Triggers:** "criar vaga", "nova vaga", "abrir posição"
- **FairnessGuard:** Integrado (verifica bias em descrições)
- **Ferramentas:** `search_salary_benchmark`, `validate_job_fields`, `get_job_suggestions`, `save_job_draft`, `get_company_config`, `get_intelligent_salary`, `get_intelligent_skills`, `capture_wizard_feedback`, `generate_enriched_jd` (9 tools)
- **Fluxo:** coleta dados → valida campos → FairnessGuard → gera JD enriquecida → salva rascunho

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quero criar uma vaga de Engenheiro de Dados Senior"
→ Roteamento: CascadedRouter → domain "job_management" → WizardReActAgent
→ Thought: "Preciso coletar mais informações sobre a vaga"
→ Action: get_company_config() → obtém configurações da empresa
→ Action: get_intelligent_skills("Engenheiro de Dados Senior") → sugestões de skills
→ Action: get_intelligent_salary("Engenheiro de Dados", "Senior", "São Paulo") → faixa salarial
→ Resposta LIA: "Ótimo! Vou criar a vaga de Engenheiro de Dados Senior. Baseado nas vagas similares da sua empresa, sugiro: Skills: Python, Spark, Airflow, SQL, AWS. Faixa salarial: R$ 18.000-25.000. Posso gerar a descrição completa?"
```

### 2.2 Pipeline Agent (Triagem de CVs)
- **Domain:** `pipeline` | **Classe:** `PipelineReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/cv_screening/agents/pipeline_react_agent.py`
- **Escopo IN (10 capacidades):** consultar dados do candidato, scores WSI, triagem, atualizar dados cadastrais, solicitar coleta de dados, extrair preferências de execução, combinar tarefas, sugerir ações/sub-status, personalizar comunicação, verificar fairness em rejeição
- **Escopo OUT (7 restrições):** outros candidatos, busca de novos, comparar vagas, adicionar em outra vaga, configurar pipeline, analytics gerais, templates de comunicação
- **Ferramentas:** `update_candidate_stage`, `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `bulk_update_candidates_stage`, `add_to_list`, `wsi_screening`, `hide_candidate` (8 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Faça a triagem WSI do candidato João Silva"
→ Roteamento: CascadedRouter → domain "cv_screening" → PipelineReActAgent
→ Thought: "Preciso executar triagem WSI para o candidato"
→ Action: wsi_screening(candidate_id="abc123", job_id="job456")
→ Observation: {score: 78, competencies: [{name: "Comunicação", level: "Avançado"}, ...]}
→ Resposta LIA: "Triagem WSI concluída para João Silva. Score geral: 78/100. Destaques: Comunicação (Avançado), Trabalho em equipe (Intermediário). Pontos de atenção: Gestão de conflitos (Básico). Deseja prosseguir com a próxima etapa?"
```

### 2.3 Sourcing Agent (Busca de Candidatos)
- **Domain:** `sourcing` | **Classe:** `SourcingReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/sourcing/agents/sourcing_react_agent.py`
- **Escopo:** Busca local (PostgreSQL) + busca externa (Pearch AI), scoring de match, análise de perfil
- **Triggers:** "buscar candidatos", "encontrar perfis", "sourcing"
- **Ferramentas:** `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `get_candidate_history`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_market_benchmarks` (9 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Busque desenvolvedores Python senior em São Paulo"
→ Roteamento: CascadedRouter → domain "sourcing" → SourcingReActAgent
→ Thought: "Busca por desenvolvedores Python senior em SP"
→ Action: search_candidates(query="desenvolvedor Python senior", location="São Paulo", limit=20)
→ Observation: {candidates: [{name: "Ana Costa", score: 92, ...}, ...], total: 47}
→ Resposta LIA: "Encontrei 47 candidatos para Desenvolvedor Python Senior em São Paulo. Os top 5: 1) Ana Costa (92% fit) - 8 anos exp, 2) Carlos Mendes (89% fit) - 6 anos exp... Deseja ver detalhes de algum candidato?"
```

### 2.4 Talent Agent (Assistente de Talentos)
- **Domain:** `talent` | **Classe:** `TalentReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py`
- **Escopo:** Assistência no funil de talentos, operações sobre candidatos
- **FairnessGuard:** Integrado

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quais candidatos estão parados há mais de 7 dias no funil?"
→ Roteamento: CascadedRouter → domain "recruiter_assistant" → TalentReActAgent
→ Thought: "Preciso identificar candidatos inativos"
→ Action: get_candidate_stats(filter="inactive_7_days")
→ Resposta LIA: "Encontrei 12 candidatos sem movimentação há mais de 7 dias: 5 na etapa Triagem, 4 em Entrevista Técnica, 3 em Proposta. Recomendo priorizar os 4 em Entrevista Técnica. Deseja que eu envie um lembrete aos entrevistadores?"
```

### 2.5 Jobs Management Agent (Portfólio de Vagas)
- **Domain:** `jobs_management` | **Classe:** `JobsMgmtReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/jobs_management_prompts.py`
- **Escopo:** Gestão do portfólio de vagas (listar, filtrar, analisar status)
- **FairnessGuard:** Integrado

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quais vagas estão abertas há mais de 30 dias?"
→ Roteamento: CascadedRouter → domain "recruiter_assistant" → JobsMgmtReActAgent
→ Resposta LIA: "Você tem 8 vagas abertas há mais de 30 dias: 1) Dev Backend Senior (45 dias, 23 candidatos), 2) PM Pleno (38 dias, 15 candidatos)... As vagas #1 e #3 têm poucos candidatos qualificados. Sugiro ampliar as fontes de sourcing."
```

### 2.6 Kanban Agent (Análise do Pipeline)
- **Domain:** `kanban` | **Classe:** `KanbanReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
- **Escopo:** Análise e operações no kanban; 18 tipos de comando (ver seção 4.2)
- **FairnessGuard:** Integrado | **GUARDRAIL_TOOLS:** Integrados

**Exemplo de interação (ilustrativo):**
```
Usuário: "Rankeie os candidatos desta vaga por fit"
→ Roteamento: detect_command_type() → RANKEAR_CANDIDATOS → KanbanReActAgent
→ Resposta LIA (JSON formatado):
{
  "ranking": [
    {"posicao": 1, "candidato_nome": "Maria Santos", "score_fit": 95, "principais_forcas": ["10 anos Python", "Liderança técnica"], "principais_gaps": ["Sem experiência com Kafka"], "justificativa": "Perfil altamente alinhado com requisitos técnicos e culturais"},
    {"posicao": 2, "candidato_nome": "Pedro Lima", "score_fit": 88, ...}
  ],
  "insights": "Pool competitivo com 3 candidatos acima de 85% de fit",
  "recomendacao": "Agendar entrevista técnica com os top 3"
}
```

### 2.7 Policy Agent (Políticas de Contratação)
- **Domain:** `policy` | **Classe:** `PolicyReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/hiring_policy/agents/policy_react_agent.py`
- **Prompt:** `app/domains/hiring_policy/agents/policy_system_prompt.py`
- **Escopo:** CRUD de políticas de contratação, validação de compliance, regras de aprovação

**Exemplo de interação (ilustrativo):**
```
Usuário: "Qual é a política de aprovação para vagas acima de R$ 20.000?"
→ Roteamento: CascadedRouter → domain "hiring_policy" → PolicyReActAgent
→ Resposta LIA: "Para vagas com salário acima de R$ 20.000, a política vigente requer: 1) Aprovação do gestor direto, 2) Aprovação do diretor de área, 3) Validação do RH. Prazo máximo: 5 dias úteis. Deseja criar ou alterar esta política?"
```

### 2.8 Automation Agent (Decomposição de Tarefas)
- **Domain:** `automation` | **Classe:** `AutomationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/automation/agents/automation_react_agent.py`
- **Prompt:** `app/domains/automation/agents/automation_system_prompt.py`
- **Capacidades:**
  - Decomposição de tarefas em subtarefas executáveis
  - Priorização inteligente (urgência × impacto × criticidade)
  - DAG de dependências (grafos acíclicos direcionados)
  - Planos de execução com paralelismo
  - Agentes delegáveis: `job_planner`, `sourcing`, `cv_screening`, `interviewer`, `wsi_evaluator`, `scheduling`, `analyst_feedback`

**Exemplo de interação (ilustrativo):**
```
Usuário: "Preciso preencher a vaga de Tech Lead até sexta-feira"
→ Roteamento: CascadedRouter → domain "automation" → AutomationReActAgent
→ Thought: "Preciso decompor em subtarefas com prazo apertado"
→ Resposta LIA: "Plano de execução para preencher Tech Lead até sexta:
  1. [PARALELO] Sourcing IA (Pearch) + busca banco interno (hoje)
  2. [SEQ] Triagem top 10 candidatos (hoje-amanhã)
  3. [PARALELO] Agendar entrevistas técnicas + enviar teste (amanhã)
  4. [SEQ] Painel final + proposta (quinta)
  Agentes envolvidos: Sourcing, Pipeline, Communication, Scheduling
  Deseja que eu execute este plano?"
```

### 2.9 Analytics Agent (KPIs e Previsões)
- **Domain:** `analytics` | **Classe:** `AnalyticsReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/analytics/agents/analytics_react_agent.py`
- **Prompt:** `app/domains/analytics/agents/analytics_system_prompt.py`
- **Ferramentas:** 19 tools (ver seção 6)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Como está a performance do funil da vaga Dev Backend?"
→ Roteamento: CascadedRouter → domain "analytics" → AnalyticsReActAgent
→ Action: get_prediction_metrics(job_id="job789", time_range="30d")
→ Action: get_conversion_patterns(job_id="job789")
→ Resposta LIA: "Performance da vaga Dev Backend (últimos 30 dias):
  - 156 candidatos totais, 89 triados, 34 entrevistados, 12 finalistas, 3 contratados
  - Taxa de conversão geral: 1.9%
  - Gargalo: Etapa Entrevista Técnica (tempo médio 8.3 dias vs benchmark 5 dias)
  - Previsão TTF: mais 15 dias para preencher as 2 vagas restantes"
```

### 2.10 Communication Agent (Multi-canal LGPD)
- **Domain:** `communication` | **Classe:** `CommunicationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/communication/agents/communication_react_agent.py`
- **Canais:** Email, WhatsApp, Teams
- **Ferramentas:** `send_email`, `send_whatsapp`, `schedule_interview`, `send_bulk_email`, `send_feedback` (5 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Envie um email de feedback para os 3 candidatos rejeitados na vaga de UX Designer"
→ Roteamento: CascadedRouter → domain "communication" → CommunicationReActAgent
→ Thought: "Preciso enviar feedback personalizado para 3 candidatos rejeitados"
→ Action: send_bulk_email(candidate_ids=["c1","c2","c3"], template="rejection_feedback", job_title="UX Designer")
→ Resposta LIA: "Emails de feedback enviados para 3 candidatos:
  - Ana Oliveira (ana@email.com) — Enviado
  - Bruno Costa (bruno@email.com) — Enviado
  - Carla Dias (carla@email.com) — Enviado
  Cada email inclui feedback personalizado sobre pontos fortes e áreas de desenvolvimento."
```

### 2.11 ATS Integration Agent (Integração Bidirecional)
- **Domain:** `ats_integration` | **Classe:** `ATSIntegrationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/ats_integration/agents/ats_integration_react_agent.py`
- **Provedores:** Gupy, Pandapé, Merge (multi-ATS), StackOne (multi-ATS internacional)
- **Fluxos:** Push (WeDOTalent → ATS), Pull (ATS → WeDOTalent)
- **Princípios:** Multi-tenant obrigatório (`company_id`), LGPD (dados sensíveis NÃO sincronizados), idempotência, auditoria SOX/ISO 27001
- **Prompt:** Inclui regras de SOX/ISO 27001 para trilha de auditoria

**Exemplo de interação (ilustrativo):**
```
Usuário: "Sincronize os candidatos aprovados da vaga Tech Lead com o Gupy"
→ Roteamento: CascadedRouter → domain "ats_integration" → ATSIntegrationReActAgent
→ Thought: "Preciso fazer push dos candidatos aprovados para o Gupy"
→ Resposta LIA: "Sincronização com Gupy concluída:
  - 5 candidatos aprovados enviados
  - 4 sincronizados com sucesso
  - 1 falha (Carlos Mendes — email duplicado no Gupy, ID: gupy_err_4521)
  Dados sensíveis (CPF, endereço) NÃO foram sincronizados conforme política LGPD."
```

### 2.12 Pipeline Transition Agent (Transição de Candidatos)
- **Domain:** `pipeline_transition` | **Classe:** `PipelineTransitionAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/pipeline/agents/pipeline_transition_agent.py`
- **Prompt:** `app/domains/pipeline/agents/pipeline_system_prompt.py`
- **Escopo:** Gerenciar movimentação de candidatos entre etapas do pipeline com validação de compliance
- **FairnessGuard:** Integrado — `check_rejection_fairness` obrigatório antes de qualquer rejeição
- **HITL:** Obrigatório para a maioria das transições; bypass apenas para candidatos de fontes automatizadas (web/ATS) na primeira transição (regra COMP-8)
- **Ferramentas (17 tools):** `get_candidate_profile`, `get_candidate_wsi_scores`, `get_candidate_screening_results`, `get_candidate_salary_info`, `update_candidate_field`, `request_data_collection`, `get_stage_sub_statuses`, `suggest_sub_status`, `extract_preferences`, `validate_transition`, `get_job_context`, `schedule_secondary_task`, `personalize_communication`, `check_rejection_fairness`, `check_candidate_availability`, `get_recruiter_preferences`, `view_candidate_profile`

**System Prompt — Capacidades IN (10):**
1. Consultar dados completos do candidato (perfil, scores WSI, triagem, salário)
2. Atualizar dados cadastrais do candidato
3. Solicitar coleta de dados adicionais (via data request)
4. Extrair preferências de execução do recrutador
5. Sugerir sub-status para a etapa atual
6. Validar transição entre etapas (compliance + regras de negócio)
7. Personalizar comunicação para o candidato
8. Verificar fairness em rejeição (FairnessGuard obrigatório)
9. Verificar disponibilidade do candidato
10. Agendar tarefas secundárias (follow-up, lembretes)

**System Prompt — Restrições OUT (7):**
1. Não buscar outros candidatos fora do contexto
2. Não comparar vagas
3. Não adicionar candidato em outra vaga
4. Não configurar pipeline
5. Não acessar analytics gerais
6. Não criar templates de comunicação
7. Não alterar políticas de contratação

**Exemplo de interação (ilustrativo):**
```
Usuário: "Mova João Silva para Entrevista Técnica"
→ Roteamento: CascadedRouter → domain "pipeline_transition" → PipelineTransitionAgent
→ Thought: "Preciso validar a transição e solicitar confirmação"
→ Action: validate_transition(candidate_id, from_stage="Triagem", to_stage="Entrevista Técnica")
→ Action: check_rejection_fairness(candidate_id) [se transição for rejeição]
→ HITL: Solicita confirmação do recrutador
→ Após confirmação: executa transição + notifica candidato
```

---

## 3. Os 4 Agentes StateGraph + PolicySetupAgent

Além dos 12 agentes ReAct, a plataforma possui **4 agentes baseados em StateGraph (LangGraph)** e **1 agente especializado de setup de políticas**. Estes agentes implementam fluxos mais complexos com estados definidos, transições condicionais e checkpoints persistentes.

**Diferenças fundamentais ReAct vs StateGraph:**

| Aspecto | ReAct Agents | StateGraph Agents |
|---------|-------------|-------------------|
| Raciocínio | Livre (Thought → Action → Observation) | Estruturado (nó → condição → nó) |
| Persistência | Via EnhancedAgentMixin | Via PostgresSaver (checkpoints) |
| Fluxo | Dinâmico, LLM decide | Predefinido, transições condicionais |
| HITL | Via PendingActionStore | Via LangGraph interrupt_before |
| Observabilidade | ReActObserver | State snapshots |
| Uso ideal | Conversas livres, análises | Fluxos multi-etapa, entrevistas |

### 3.1 Job Wizard Graph (Criação de Vagas — StateGraph)

**Arquivo:** `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py`
**Tipo:** LangGraph StateGraph com checkpoints PostgreSQL
**Propósito:** Guia recrutadores na criação de vagas com fluxo estruturado multi-etapa

**State (`JobWizardState`):**
```python
class JobWizardState(TypedDict):
    session_id: str
    company_id: str
    job_title: str
    fields: Dict[str, Any]       # Dados extraídos (requisitos, benefícios, etc.)
    current_stage: str            # "draft" | "enriching" | "reviewing" | "published"
    intent: str                   # Intenção classificada do usuário
    tool_calls: List[Dict]        # Ferramentas pendentes
    conversation_history: List    # Histórico de mensagens
```

**6 Nós do Grafo:**

| Nó | Função | Descrição |
|----|--------|-----------|
| `intent_classifier` | Classifica intenção do usuário | `DATA_INPUT`, `QUESTION`, `CORRECTION`, `SKIP`, `CONFIRM`, `REUSE_VACANCY` |
| `field_extractor` | Extrai campos da mensagem | Requisitos, skills, localização, salário, benefícios |
| `tool_router` | Decide se precisa executar tool | Consulta DB, benchmark salarial, validação |
| `tool_executor` | Executa ferramentas pendentes | `validate_job_fields`, `search_salary_benchmark`, `generate_enriched_jd` |
| `response_generator` | Gera resposta conversacional | Próxima pergunta, confirmação, sugestão |
| `stage_transition` | Avança estágio do wizard | `draft` → `enriching` → `reviewing` → `published` |

**Transições Condicionais:**
```
START → intent_classifier
         ├── QUESTION/HELP → response_generator → END
         ├── SKIP/CONFIRM → stage_transition
         │                    ├── mais etapas → intent_classifier
         │                    └── completo → END
         └── DATA_INPUT → field_extractor → tool_router
                                              ├── tools pendentes → tool_executor → response_generator
                                              └── sem tools → response_generator → END
```

**HITL:** Interrupt antes de `stage_transition` quando intent == "CONFIRM" (publicar vaga). Requer aprovação explícita.

**Checkpoint:** `PostgresSaver` persiste estado entre interações. Permite retomar criação de vaga após desconexão.

**System Prompt Específico:**
- Consultivo: fornece benchmarks salariais e questiona requisitos irrealistas
- Anti-sycophancy: NÃO concorda com o recrutador apenas para evitar conflito
- Autonomia: dispara enriquecimento de JD automaticamente ao coletar título
- Proibições: não permite requisitos discriminatórios em JDs (gênero, aparência)

### 3.2 WSI Interview Graph (Entrevista por Simulação de Trabalho)

**Arquivo:** `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`
**Tipo:** LangGraph StateGraph determinístico
**Propósito:** Conduzir entrevistas estruturadas WSI com scoring auditável

**State (`WSIInterviewState`):**
```python
class WSIInterviewState(TypedDict):
    session_id: str
    candidate_id: str
    job_vacancy_id: str
    question_blocks: List[QuestionBlock]    # Banco de perguntas WSI
    current_question_index: int
    responses: List[ResponseScore]          # Score + reasoning por resposta
    technical_score: float
    behavioral_score: float
    situational_score: float
    overall_score: float
    recommendation: str                     # "aprovado" | "aguardando" | "reprovado"
    consent_verified: bool                  # LGPD Gate
```

**6 Nós do Grafo:**

| Nó | Função | Descrição |
|----|--------|-----------|
| `load_context` | Carrega contexto | Requisitos da vaga + perfil do candidato + gera perguntas WSI |
| `generate_question` | Apresenta próxima pergunta | Seleciona do banco de perguntas por bloco |
| `validate_response` | Valida resposta | Verifica vazio, skip, prompt injection |
| `score_response` | Pontua resposta | Scorer determinístico + LLM (Bloom + Dreyfus levels) |
| `advance` | Avança índice | Decide se continua ou vai para feedback |
| `generate_feedback` | Gera resultado final | Score WSI consolidado + recomendação |

**Transições Condicionais:**
```
LOAD_CONTEXT → GENERATE_QUESTION → VALIDATE_RESPONSE
                                        ├── válida → SCORE_RESPONSE → ADVANCE
                                        └── skip/vazia → ADVANCE
                                                          ├── mais perguntas → GENERATE_QUESTION
                                                          └── fim → GENERATE_FEEDBACK → COMPLETE
```

**Compliance integrado:**
- LGPD: Verificação de consentimento no nó `load_context` (Gate obrigatório)
- FairnessGuard: Check de viés antes de iniciar entrevista
- PII Masking: Dados do candidato mascarados antes de enviar ao LLM
- Auditoria: Cada resposta + score armazenados para Art. 20 LGPD

**Metodologia de Scoring:**
- **Bloom's Taxonomy:** Classifica nível cognitivo da resposta (Conhecimento → Avaliação)
- **Dreyfus Model:** Classifica proficiência (Novice → Expert)
- **Score determinístico:** Fórmula ponderada (Técnico 50% + Comportamental 20% + Gap 15% + Contextual 15%)
- **LLM qualitativo:** Claude avalia qualidade da resposta com reasoning
- **Score final:** Combinação determinístico + LLM com pesos configuráveis

### 3.3 Interview Scheduling Graph (Agendamento de Entrevistas)

**Arquivo:** `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py`
**Tipo:** LangGraph StateGraph com slot-filling iterativo
**Propósito:** Coletar informações e agendar entrevistas via conversa

**State (`_InterviewStateDict`):**
```python
class _InterviewStateDict(TypedDict):
    session_id: str
    workflow_data: Dict[str, Any]      # Campos do agendamento (data, hora, tipo, participantes)
    conversation_history: List[Dict]    # Histórico de mensagens
```

**6 Nós do Grafo:**

| Nó | Função | Descrição |
|----|--------|-----------|
| `interview_state_loader` | Inicializa/restaura estado | Carrega ou cria sessão de agendamento |
| `interview_details_collector` | Extrai entidades | Data, hora, tipo, participantes, link da call |
| `interview_router` | Verifica campos faltantes | Identifica quais slots ainda estão vazios |
| `interview_validator` | Valida campos completos | Verifica formato, conflitos de horário, disponibilidade |
| `interview_scheduler_executor` | Executa agendamento | Cria evento no calendário (Google/Teams) + atualiza DB |
| `interview_response_planner` | Gera resposta | Pede campos faltantes ou confirma agendamento |

**Transições Condicionais (Slot-Filling):**
```
LOADER → COLLECTOR → ROUTER
                       ├── campos faltantes → RESPONSE → END (aguarda próxima msg)
                       └── todos preenchidos → VALIDATOR
                                                ├── válido → EXECUTOR → RESPONSE → END
                                                └── inválido → RESPONSE → END
```

**Integrações:**
- Google Calendar API (via `google_calendar_client.py`)
- Microsoft Teams (via `microsoft_graph_service.py`)
- Zoom (via webhook)
- Deepgram (transcrição de entrevistas em tempo real)

**Fluxo iterativo:** O grafo pausa em `RESPONSE` e retoma na próxima mensagem do usuário, preenchendo progressivamente os slots necessários (data, hora, participantes, tipo de entrevista).

### 3.4 PolicySetupAgent (Configuração Inicial de Políticas)

**Arquivo:** `lia-agent-system/app/domains/policy/agents/tool_registry.py`
**Tipo:** Agente ReAct simplificado (sem tool registry — usa chamadas LLM diretas)
**Propósito:** Onboarding de empresas novas com configuração inicial de políticas de contratação

**Escopo:** 5 blocos de configuração:
1. **Pipeline Process** — Etapas do pipeline, SLAs por etapa, regras de transição
2. **Scheduling** — Horários permitidos, buffer entre entrevistas, ferramentas de vídeo
3. **Communication** — Templates de email, canais (Email/WhatsApp/Teams), horário comercial (8h–20h Brasília)
4. **Screening** — Critérios de pré-qualificação, thresholds WSI, rubricas padrão
5. **LIA Autonomy** — Nível de autonomia (CONSERVATIVE/BALANCED/AUTONOMOUS), guardrails

**System Prompt Específico:**
- Consultivo: explica trade-offs de configurações (ex: SLAs muito curtos causam alertas de estagnação)
- Calibração por tamanho: adapta recomendações (Startup vs Corporação)
- Validação obrigatória via `validate_policy_compliance` para regras de screening
- Proibição de regras discriminatórias nas políticas

**Diferença do PolicyReActAgent (2.7):** O PolicyReActAgent gerencia políticas existentes (CRUD, consulta, validação), enquanto o PolicySetupAgent foca no onboarding inicial com wizard guiado.

**Localização canônica (Z5-02):**
- **Canônico:** `app/domains/policy/agents/agent.py` → classe `PolicySetupAgent`
- **Shim (deprecado):** `app/agents/policy_setup_agent.py` — re-exporta de `app.domains.policy.agents.agent.PolicySetupAgent` com `DeprecationWarning`

> A partir do Sprint Z5-02, o arquivo `app/agents/policy_setup_agent.py` é apenas um shim de compatibilidade retroativa. Todo código novo deve importar de `app.domains.policy.agents.agent.PolicySetupAgent` diretamente.

---

## 4. Arquitetura DDD e Catálogo de Domínios

### 4.1 Estrutura de Domínios

A plataforma segue arquitetura DDD (Domain-Driven Design) com **12 domínios** organizados em `lia-agent-system/app/domains/`:

```
app/domains/
├── analytics/            # Domínio: KPIs, previsões, relatórios
│   ├── agents/           # AnalyticsReActAgent + tools + prompt
│   ├── services/         # predictive_analytics_service, wizard_analytics_service
│   └── tools/            # analytics_query_tools, analytics_action_tools
├── ats_integration/      # Domínio: Integração bidirecional com ATSs
│   ├── agents/           # ATSIntegrationReActAgent + tools + prompt
│   ├── services/         # ats_sync_service, ats_clients/ (gupy, pandape, stackone, merge)
│   └── models/           # Modelos de sincronização
├── automation/           # Domínio: Motor de automação e tarefas
│   ├── agents/           # AutomationReActAgent + tools + prompt
│   ├── services/         # automation_service, trigger_service, proactive_service
│   └── tools/            # task planning tools
├── communication/        # Domínio: Multi-canal (Email, WhatsApp, Teams)
│   ├── agents/           # CommunicationReActAgent + tools + prompt
│   ├── services/         # email_service, whatsapp_service, teams_service
│   └── templates/        # Templates de comunicação
├── cv_screening/         # Domínio: Triagem de CVs e WSI
│   ├── agents/           # PipelineReActAgent, WSIInterviewGraph + tools + prompt
│   ├── services/         # wsi_service, cv_scoring_service, cv_parser
│   └── models/           # Modelos de avaliação
├── hiring_policy/        # Domínio: Políticas de contratação
│   ├── agents/           # PolicyReActAgent + tools + prompt
│   ├── services/         # policy_engine_service
│   └── models/           # CompanyHiringPolicy, PolicyRule
├── interview_scheduling/ # Domínio: Agendamento de entrevistas
│   ├── agents/           # InterviewGraph + tools
│   ├── services/         # scheduling_service, calendar_service
│   └── integrations/     # Google Calendar, Teams, Zoom
├── job_management/       # Domínio: Criação e gestão de vagas
│   ├── agents/           # WizardReActAgent, JobWizardGraph + tools + prompt
│   ├── services/         # jd_enrichment_service, jd_generator_service
│   └── models/           # JobVacancy, JobTemplate
├── pipeline/             # Domínio: Transições de pipeline
│   ├── agents/           # PipelineTransitionAgent + tools + prompt
│   ├── services/         # pipeline_service, pipeline_stage_service
│   └── models/           # PipelineStage, Transition
├── policy/               # Domínio: Setup inicial de políticas
│   ├── agents/           # PolicySetupAgent + tool_registry
│   └── services/         # policy_setup_service
├── recruiter_assistant/  # Domínio: Assistente do recrutador (3 sub-agentes)
│   ├── agents/           # TalentReActAgent, JobsMgmtReActAgent, KanbanReActAgent
│   ├── prompts/          # talent_assistant_prompts, kanban_assistant_prompts, jobs_management_prompts
│   └── services/         # kanban_assistant_service
└── sourcing/             # Domínio: Busca e sourcing de candidatos
    ├── agents/           # SourcingReActAgent + tools + prompt
    ├── services/         # pearch_service, sourcing_pipeline_service
    └── tools/            # query_tools, action_tools
```

### 4.2 Camadas Compartilhadas

```
app/shared/
├── compliance/           # FairnessGuard, audit_service, pii_masking
├── governance/           # agent_monitoring_service, RBAC
├── intelligence/         # embedding_service, semantic_search, smart_extractor
├── learning/             # learning_loop, ab_testing, template_learning, finetuning_export
├── messaging/            # dispatchers, celery_config, rabbitmq_consumer
├── prompts/              # prompt_registry, templates, examples/, agent_prompts.py
├── providers/            # llm_factory, anthropic_provider, gemini_provider, openai_provider
├── resilience/           # circuit_breaker
├── robustness/           # defensive_prompts
└── tools/                # insight_tools, proactive_tools, predictive_tools
```

### 4.3 Catálogo de Serviços (231 serviços auditados)

**Distribuição por camada:**

| Camada | Qtd | Exemplos |
|--------|-----|----------|
| Domain Services | 89 | `automation_service`, `jd_enrichment_service`, `pipeline_service` |
| Application Services | 72 | `lia_score_service`, `cv_parser`, `scheduling_service` |
| Shared Intelligence | 8 | `embedding_service`, `semantic_search_service`, `smart_extractor` |
| Shared Learning | 4 | `learning_loop_service`, `ab_testing_service`, `template_learning_service`, `finetuning_export` |
| Compliance Services | 12 | `fairness_guard`, `bias_audit_service`, `consent_checker_service` |
| Integration Services | 18 | `pearch_service`, `gupy_service`, `pandape_service`, `merge_ats_service` |
| Communication Services | 14 | `email_service`, `whatsapp_service`, `teams_service`, `deepgram_service` |
| Predictive Services | 8 | `predictive_analytics_service`, `pipeline_prediction_service`, `early_warning_service` |
| Infrastructure | 6 | `circuit_breaker`, `token_tracking_service`, `structured_logging` |

**Top 20 serviços críticos:**

| # | Serviço | Arquivo | Função |
|---|---------|---------|--------|
| 1 | `LIAScoreService` | `app/services/lia_score_service.py` | Score unificado candidato-vaga (determinístico) |
| 2 | `WSIService` | `app/services/wsi_service.py` | Orquestração de entrevistas WSI |
| 3 | `PredictiveAnalyticsService` | `app/services/predictive_analytics_service.py` | Previsões de contratação |
| 4 | `AutomationService` | `app/domains/automation/services/automation_service.py` | Motor de automações |
| 5 | `FairnessGuard` | `app/shared/compliance/fairness_guard.py` | Anti-viés 3 camadas |
| 6 | `CascadedRouter` | `app/orchestrator/cascaded_router.py` | Roteamento 6 tiers |
| 7 | `ActionExecutor` | `app/orchestrator/action_executor.py` | Execução closed-loop |
| 8 | `TokenTrackingService` | `app/services/token_tracking_service.py` | Controle de custos LLM |
| 9 | `EmbeddingService` | `app/shared/intelligence/embedding_service.py` | Vetores 768-dim (Gemini) |
| 10 | `SemanticSearchService` | `app/shared/intelligence/semantic_search_service.py` | Expansão semântica |
| 11 | `LearningLoopService` | `app/shared/learning/learning_loop_service.py` | Aprendizado silencioso |
| 12 | `CircuitBreaker` | `app/shared/resilience/circuit_breaker.py` | Proteção de APIs |
| 13 | `ConfidencePolicyService` | `app/services/confidence_policy_service.py` | Autonomia de ações |
| 14 | `JDEnrichmentService` | `app/domains/job_management/services/jd_enrichment_service.py` | Enriquecimento de JD |
| 15 | `PearchService` | `app/services/pearch_service.py` | Busca externa 190M+ perfis |
| 16 | `BiasAuditService` | `app/services/bias_audit_service.py` | Auditoria Four-Fifths |
| 17 | `HitlService` | `app/services/hitl_service.py` | Human-in-the-Loop |
| 18 | `AgentMonitoringService` | `app/shared/governance/agent_monitoring_service.py` | Monitoramento de agentes |
| 19 | `LGPDCleanupService` | `app/services/lgpd_cleanup_service.py` | Retenção de dados |
| 20 | `EarlyWarningService` | `app/services/early_warning_service.py` | Alertas proativos |

### 4.4 Inventário de Models (99 models auditados)

**Distribuição por domínio:**

| Domínio | Qtd | Exemplos |
|---------|-----|----------|
| Candidates | 12 | `Candidate`, `CandidateExperience`, `CandidateEducation`, `CandidateAttachment` |
| Jobs | 10 | `JobVacancy`, `JobTemplate`, `JobRequirement`, `JobStage` |
| Pipeline | 8 | `VacancyCandidate`, `PipelineStage`, `StageTransition`, `PipelineHistory` |
| Evaluation | 9 | `RubricEvaluation`, `WSISession`, `WSIResponse`, `LIAOpinion`, `LIAProfileAnalysis` |
| Communication | 7 | `CommunicationLog`, `EmailTemplate`, `WhatsAppMessage`, `NotificationPreference` |
| Automation | 6 | `AutomationRule`, `AutomationTrigger`, `ProactiveAction`, `PlannedTask` |
| Compliance | 14 | `ConsentRecord`, `DataSubjectRequest`, `BreachNotification`, `SOXAuditLog`, `BiasAuditSnapshot` |
| AI/Analytics | 8 | `AIConsumption`, `AIInferenceLog`, `AutomatedDecisionExplanation`, `ModelEvaluation` |
| Policy | 5 | `CompanyHiringPolicy`, `PolicyRule`, `InsurancePolicy`, `InsuranceCoverage` |
| Infrastructure | 11 | `Company`, `User`, `Team`, `Department`, `Activity`, `FeatureFlag` |
| Learning | 5 | `FeedbackCapture`, `LearnedPattern`, `CalibrationFeedback`, `TrainingData` |
| Integration | 4 | `ATSSyncLog`, `ATSFieldMapping`, `ExternalCandidate` |

### 4.5 Overview de API Endpoints (206 endpoints auditados)

**Distribuição por módulo:**

| Módulo API | Arquivo | Endpoints | Autenticação |
|------------|---------|-----------|--------------|
| Agent Chat | `app/api/v1/agent_chat_ws.py` | 1 WS | JWT |
| Orchestrator | `app/api/v1/orchestrator.py` | 8 REST | JWT |
| LGPD Compliance | `app/api/v1/lgpd_compliance.py` | 13 REST | JWT + Admin |
| Health Check | `app/api/v1/health_check.py` | 6 REST | JWT + Admin |
| Insurance (BCB) | `app/api/v1/insurance.py` | 19 REST | JWT + Admin |
| Continuity | `app/api/v1/continuity.py` | 12 REST | JWT + Admin |
| Data Subject Requests | `app/api/v1/dsr.py` | 10 REST | JWT |
| Bias Audit | `app/api/v1/bias_audit.py` | 5 REST | JWT + Admin |
| Token Tracking | `app/api/v1/token_tracking.py` | 4 REST | JWT |
| Automation | `app/api/v1/automation.py` | 8 REST | JWT |
| Pipeline | `app/api/v1/pipeline.py` | 12 REST | JWT |
| Candidates | `app/api/v1/candidates.py` | 15 REST | JWT |
| Jobs | `app/api/v1/jobs.py` | 18 REST | JWT |
| Analytics | `app/api/v1/analytics.py` | 9 REST | JWT |
| Communication | `app/api/v1/communication.py` | 7 REST | JWT |
| ATS Integration | `app/api/v1/ats_integration.py` | 6 REST | JWT |
| Policy | `app/api/v1/policy.py` | 8 REST | JWT + Admin |
| Calibration | `app/api/v1/calibration.py` | 5 REST | JWT |
| Trust Center | `app/api/v1/trust_center.py` | 3 REST | Público |
| Admin | `app/api/v1/admin.py` | 12 REST | JWT + SuperAdmin |
| Django Backend | `plataforma-lia/backend/` | 25 REST | Session |

**Endpoints críticos do Orchestrator:**

| Método | Path | Descrição | Rate Limit |
|--------|------|-----------|------------|
| `POST` | `/orchestrator/chat` | Chat com LIA (REST, síncrono) | 60/min |
| `POST` | `/orchestrator/job-chat` | Chat contextual de vaga (Kanban) | 60/min |
| `POST` | `/orchestrator/float-chat` | Chat flutuante (candidatos-page) | 60/min |
| `POST` | `/orchestrator/wizard-chat` | Chat do wizard de vagas | 60/min |
| `POST` | `/orchestrator/approve-action` | Confirmar ação HITL | 30/min |
| `POST` | `/orchestrator/reject-action` | Rejeitar ação HITL | 30/min |
| `GET` | `/orchestrator/pending-actions` | Listar ações pendentes | 30/min |
| `GET` | `/orchestrator/health` | Health check do orchestrator | 10/min |

### 4.6 Migrations (37 migrations auditadas)

**Distribuição por tipo:**

| Tipo | Qtd | Exemplos |
|------|-----|----------|
| Schema creation | 12 | Tabelas base (candidates, jobs, pipeline, etc.) |
| Schema alterations | 8 | Adição de colunas (lia_score, consent_status, etc.) |
| Compliance tables | 7 | SOX audit, LGPD, breach, decisions |
| Index additions | 5 | Indexes de performance (company_id, created_at) |
| Seed data | 3 | Dados iniciais (compliance controls, templates) |
| Data migrations | 2 | Transformação de dados existentes |

**Convenção de nomeação:** `{seq}_{description}.py` (Alembic)

---

## 5. Arquitetura WebSocket e Domain Dispatch

### 5.1 Fluxo de Mensagem WebSocket

**Arquivo principal:** `lia-agent-system/app/api/v1/agent_chat_ws.py`

```
┌──────────────────────────────────────────────────────────────────┐
│ Frontend (chat-page.tsx)                                          │
│ wsSendMessage(content, context, domain?)                         │
└──────────────────┬───────────────────────────────────────────────┘
                   │ WebSocket /ws/chat/{session_id}
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ agent_chat_ws.py                                                  │
│ 1. JWT Authentication (query param ou header)                    │
│ 2. Extract company_id, user_id                                    │
│ 3. PromptInjectionGuard.check(message) [SEG-1]                  │
│ 4. TokenBudgetService.check_limits()                             │
│ 5. Determine execution mode (sync vs async)                      │
└──────────────────┬───────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼ domain == "auto"    ▼ domain explícito
┌───────────────┐    ┌────────────────┐
│ CascadedRouter│    │ Direct dispatch │
│ (6 tiers)     │    │ ao domínio      │
└───────┬───────┘    └────────┬───────┘
        │ domain_id           │
        └──────────┬──────────┘
                   ▼
        ┌──────────────────┐
        │ Sync ou Async?   │
        └────┬────────┬────┘
             │        │
    ┌────────▼─┐  ┌───▼──────────────┐
    │ SYNC     │  │ ASYNC             │
    │ agent    │  │ DomainDispatcher  │
    │.process()│  │ → RabbitMQ        │
    └────┬─────┘  │ → Celery Worker   │
         │        │ → Response Queue  │
         │        └───────┬───────────┘
         └────────┬───────┘
                  ▼
    ┌──────────────────────┐
    │ WebSocket Response    │
    │ {message, confidence, │
    │  actions, domain}     │
    └──────────────────────┘
```

### 5.2 Domínios Registrados e Aliases

**11 domínios + aliases mapeados no DomainDispatcher:**

| Domain / Alias | Agent Implementation | Celery Queue | Modo | Descrição |
|:---|:---|:---|:---|:---|
| `wizard`, `job_management` | `WizardReActAgent` / `JobWizardGraph` | `vagas_normal` | Sync/Async | Criação de vagas |
| `pipeline`, `cv_screening`, `wsi_assessment` | `PipelineReActAgent` / `WSIInterviewGraph` | `evaluation_normal` | Async | Triagem e entrevistas |
| `sourcing` | `SourcingReActAgent` | `sourcing_high` | Async | Busca de candidatos |
| `talent`, `recruiter_assistant` | `TalentReActAgent` | `vagas_normal` | Sync | Funil de talentos |
| `kanban` | `KanbanReActAgent` | `vagas_normal` | Sync | Análise de pipeline |
| `jobs_management`, `jobs_mgmt` | `JobsMgmtReActAgent` | `vagas_normal` | Sync | Portfólio de vagas |
| `policy`, `hiring_policy` | `PolicyReActAgent` | `onboarding_low` | Sync | Políticas |
| `pipeline_transition` | `PipelineTransitionAgent` | `evaluation_normal` | Sync | Transições de etapa |
| `analytics` | `AnalyticsReActAgent` | N/A | Sync | KPIs e previsões |
| `communication`, `comms` | `CommunicationReActAgent` | N/A | Sync | Comunicação multi-canal |
| `ats_integration`, `ats` | `ATSIntegrationReActAgent` | N/A | Sync | Integração ATS |
| `automation` | `TaskPlanner` (fallback) | `vagas_normal` | Async | Automação de tarefas |

### 5.3 Filas Celery (RabbitMQ)

**Arquivo:** `lia-agent-system/app/shared/messaging/celery_config.py`

| Fila | Prioridade | Domínios | Propósito |
|------|------------|----------|-----------|
| `sourcing_high` | Alta | sourcing | Busca de candidatos (tempo-sensitivo) |
| `evaluation_normal` | Normal | cv_screening, pipeline, pipeline_transition | Triagem e avaliação |
| `vagas_normal` | Normal | wizard, talent, kanban, jobs_management, automation | Gestão de vagas e tarefas |
| `onboarding_low` | Baixa | policy, hiring_policy | Configuração (não urgente) |

### 5.4 HITL via WebSocket

O sistema suporta **Human-in-the-Loop** via WebSocket com mensagem tipo `approval_response`:

```
1. Agente propõe ação → resposta WS com needs_confirmation: true
2. Frontend exibe modal de confirmação
3. Usuário aprova/rejeita → mensagem WS tipo "approval_response"
4. Backend retoma execução:
   - LangGraph: resume checkpoint via interrupt_before
   - ReAct: PendingActionStore.resolve() → ActionExecutor.execute()
```

### 5.5 Token Budget via WebSocket

Cada mensagem WS verifica o orçamento de tokens do tenant via `TokenBudgetService`:
- Se limite atingido → mensagem de erro amigável
- Se > 80% do limite → warning inline na resposta
- Tracking em tempo real: `redis.incr(f"tokens:{company_id}:{date}")`

### 5.6 Protocolo de Mensagens WebSocket

**Mensagem do Cliente (Frontend → Backend):**
```json
{
  "type": "chat_message",
  "content": "Busque candidatos Python senior",
  "context": {
    "current_page": "candidates",
    "selected_job_id": "job_abc123",
    "selected_candidates": ["cand_1", "cand_2"],
    "current_stage": "triagem"
  },
  "domain": "auto",
  "session_id": "sess_xyz789"
}
```

**Tipos de mensagem suportados (cliente → servidor):**

| Tipo | Payload | Descrição |
|------|---------|-----------|
| `chat_message` | `{content, context, domain}` | Mensagem normal de chat |
| `approval_response` | `{action_id, approved, reason?}` | Resposta HITL (aprovar/rejeitar) |
| `cancel_request` | `{action_id?}` | Cancelar operação em andamento |
| `typing_indicator` | `{is_typing}` | Indicador de digitação |
| `ping` | `{}` | Keep-alive |

**Tipos de mensagem suportados (servidor → cliente):**

| Tipo | Payload | Descrição |
|------|---------|-----------|
| `assistant_message` | `{content, confidence, domain, metadata}` | Resposta da LIA |
| `action_proposal` | `{action_id, description, params, needs_confirmation}` | Proposta de ação HITL |
| `action_result` | `{action_id, success, result, error?}` | Resultado de ação executada |
| `thinking` | `{stage, detail}` | Indicador de processamento (thought/action/observation) |
| `error` | `{code, message, retry_after?}` | Erro estruturado |
| `token_warning` | `{usage_percent, limit, remaining}` | Alerta de consumo de tokens |
| `navigation` | `{intent, target, params}` | Comando de navegação frontend |
| `pong` | `{}` | Resposta ao keep-alive |

**Resposta da LIA (servidor → cliente):**
```json
{
  "type": "assistant_message",
  "content": "Encontrei 47 candidatos Python Senior em São Paulo...",
  "confidence": 0.92,
  "domain": "sourcing",
  "metadata": {
    "agent": "SourcingReActAgent",
    "router_tier": 4,
    "router_source": "fast_router",
    "tokens_used": 1250,
    "latency_ms": 3200,
    "tools_called": ["search_candidates"],
    "navigation_intent": "STAY",
    "action_intent": "QUERY"
  }
}
```

### 5.7 Tratamento de Erros WebSocket

| Código | Erro | Comportamento |
|--------|------|---------------|
| `WS_1001` | Mensagem vazia | Resposta: "Por favor, envie sua mensagem." |
| `WS_1002` | Rate limit excedido | Resposta: "Aguarde alguns segundos antes de enviar outra mensagem." |
| `WS_1003` | Token budget esgotado | Resposta: "Limite de uso diário atingido. Tente novamente amanhã." |
| `WS_1004` | Prompt injection detectado | Resposta: "Não consegui processar esta mensagem. Tente reformular." |
| `WS_1005` | Agente indisponível | Resposta: fallback com 3 sugestões + retry automático |
| `WS_1006` | Timeout (30s) | Resposta: "Desculpe, o processamento demorou mais que o esperado. Tente novamente." |
| `WS_1007` | Circuit breaker OPEN | Resposta: mensagem amigável + retry_after em segundos |

### 5.8 Reconexão e Persistência

- **Heartbeat:** Ping/pong a cada 30 segundos
- **Reconexão automática:** Frontend tenta reconectar com backoff exponencial (1s, 2s, 4s, 8s, max 30s)
- **Persistência de sessão:** `session_id` via URL param; estado mantido em Redis (TTL 1 hora)
- **Histórico:** Últimas 20 mensagens carregadas ao reconectar via REST endpoint
- **Multi-tab:** Cada tab cria uma conexão WS separada; estado compartilhado via `session_id`

### 5.9 Streaming ReAct — E7

**Implementado em:** Sprint Y5/E7
**Arquivo BE:** `app/shared/agents/streaming_react_agent.py`
**Arquivo FE:** `plataforma-lia/src/components/react-thinking-stream.tsx`

O Streaming ReAct transmite os "pensamentos" do agente em tempo real via WebSocket, permitindo ao recrutador acompanhar cada etapa do raciocínio durante o processamento:

- **Backend:** `StreamingReActAgent` estende `LangGraphReActBase` — override de `_process_langgraph()` com `astream_events()` emitindo `on_chat_model_stream` e `on_tool_start/end`
- **Eventos WS (servidor → cliente):** `{"type": "thinking", "content": "..."}` para thoughts, `{"type": "tool_call", "tool": "...", "input": {...}}` para tool calls
- **Frontend:** `ReactThinkingStream` component consome os eventos e renderiza progressivamente com estado colapsável
  - Props: `steps: string[]`, `isThinking: boolean`
  - Exibe indicador de spinner enquanto ativo; ponto verde + contagem de etapas ao concluir
  - Só é renderizado quando `isThinking=true` ou quando `steps.length > 0`
- **Integração:** `agent_chat_ws.py` detecta agentes com capacidade de streaming e usa o path de streaming automaticamente
- **Design System:** Usa `bg-gray-50`, `border-gray-200`, `rounded-md` — conforme DS v4.2.1

---

## 6. Capacidades Detalhadas

### 6.1 WSI Screening (Entrevista por Voz Estruturada)

- **O que faz:** Executa triagem de candidatos via entrevista estruturada em 7 blocos
- **Input:** `candidate_id`, `job_vacancy_id`, `questions[]`
- **Processing:** IA (Claude via WSI Evaluator Agent) — 7 dimensões avaliadas
- **Output:** Score 0–100, classificação (Avançar/Revisar/Rejeitar), justificativa por bloco
- **Execução:** IA real (Claude Sonnet)
- **FairnessGuard:** Integrado — 3 camadas verificam output antes de finalizar score
- **Arquivo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

**7 Dimensões Avaliadas:**
1. Abertura e apresentação
2. Motivação para a vaga
3. Experiência técnica relevante
4. Soft skills e comunicação
5. Pretensão salarial e benefícios
6. Disponibilidade e logística
7. Fechamento e próximos passos

**Fluxo End-to-End do WSI:**
```
┌─────────────────────────────────────────────────────────────────┐
│                     WSI SCREENING FLOW                            │
│                                                                   │
│ 1. Recrutador inicia WSI via Kanban Chat ou comando direto       │
│    → "iniciar triagem WSI para João Silva"                       │
│                                                                   │
│ 2. Gate de Consentimento (LGPD)                                  │
│    ├── ConsentCheckerService verifica consentimento               │
│    ├── Se ausente (soft_warning) → log + prossegue               │
│    └── Se ausente (hard_block) → bloqueia + solicita consentimento│
│                                                                   │
│ 3. Gate de FairnessGuard (Anti-Viés)                             │
│    ├── Camada 1: Regex — verifica JD e requisitos                │
│    ├── Camada 2: Léxico — termos implicitamente discriminatórios │
│    └── Se viés detectado → alerta ao recrutador + ajuste         │
│                                                                   │
│ 4. Geração de Perguntas WSI                                      │
│    ├── Baseadas no JD + requisitos técnicos + competências       │
│    ├── 7 blocos de perguntas (1 por dimensão)                    │
│    └── Perguntas calibradas por senioridade do cargo             │
│                                                                   │
│ 5. Condução da Entrevista (WSIInterviewGraph)                    │
│    ├── Apresenta pergunta do bloco atual                         │
│    ├── Recebe resposta do candidato                               │
│    ├── Valida resposta (vazio, skip, prompt injection)            │
│    ├── Pontua resposta (Bloom + Dreyfus + LLM qualitativo)       │
│    └── Avança para próximo bloco (loop até bloco 7)              │
│                                                                   │
│ 6. Consolidação de Score                                          │
│    ├── Score por bloco (0–100)                                   │
│    ├── Score WSI consolidado (média ponderada)                   │
│    ├── Classificação: Avançar (≥60) / Revisar (40-59) / Rejeitar (<40) │
│    └── Justificativa por bloco (reasoning do LLM)                │
│                                                                   │
│ 7. Pós-Processing                                                │
│    ├── PII Masking aplicado ao relatório                         │
│    ├── Score normalizado (ScoreNormalizationService)             │
│    ├── LIA Score atualizado (incorpora wsi_score)                │
│    ├── Decisão automatizada registrada (LGPD Art. 20)            │
│    └── Se score em zona cinzenta → HITL trigger automático       │
│                                                                   │
│ 8. Resultado Entregue                                             │
│    ├── Chat: Resumo com score, classificação, pontos fortes/fracos│
│    ├── Kanban: Badge colorido atualizado no card                 │
│    ├── Audit trail: Registro completo para compliance             │
│    └── Se rejeitado → PersonalizedFeedbackService (3 tons)       │
└─────────────────────────────────────────────────────────────────┘
```

**Modelo de Scoring por Bloco:**

| Bloco | Dimensão | Peso | Critérios de Avaliação |
|-------|----------|------|------------------------|
| 1 | Abertura | 10% | Clareza, cordialidade, apresentação profissional |
| 2 | Motivação | 15% | Alinhamento com empresa/vaga, pesquisa prévia, entusiasmo |
| 3 | Técnico | 25% | Conhecimento específico, profundidade, aplicação prática |
| 4 | Soft Skills | 20% | Comunicação, trabalho em equipe, liderança, adaptabilidade |
| 5 | Salarial | 10% | Alinhamento com faixa, flexibilidade, expectativas |
| 6 | Logística | 10% | Disponibilidade, localização, modelo de trabalho |
| 7 | Fechamento | 10% | Perguntas relevantes, interesse demonstrado, próximos passos |

### 6.2 LIA Score (Scoring Unificado)

- **O que faz:** Calcula pontuação unificada de fit do candidato para uma vaga
- **Input:** rubric scores, WSI scores, prerequisites, recency, calibration_adjustment
- **Processing:** Local (sem LLM) — fórmula ponderada com pesos por cenário
- **Output:** Score 0–100 com breakdown por componente
- **Arquivo:** `lia-agent-system/app/services/lia_score_service.py`

**Fórmula completa:**
```
LIA_Score = Σ(peso_componente × score_componente × DataAvailability) + Calibration_Adjustment

Onde:
  score_componente ∈ {wsi_score, rubric_score, prerequisites_score, recency_score}
  DataAvailability = 1.0 se dados existem, 0.0 se ausentes
  Calibration_Adjustment = 0 (reservado para ML adaptativo futuro)
```

**4 Cenários de peso (seleção automática baseada em dados disponíveis):**

| Cenário | WSI | Rubrica | Prerequisites | Recency | Quando Ativado |
|---------|-----|---------|---------------|---------|----------------|
| **WSI + Rubrica** | 40% | 30% | 15% | 15% | Ambas avaliações disponíveis |
| **Apenas WSI** | 55% | 0% | 25% | 20% | Somente WSI executada |
| **Apenas Rubrica** | 0% | 55% | 25% | 20% | Somente rubrica executada |
| **Sem avaliação** | 0% | 0% | 50% | 50% | Nenhuma avaliação IA |

**Componentes do Score:**

| Componente | Intervalo | Cálculo | Fonte |
|------------|-----------|---------|-------|
| `wsi_score` | 0–100 | Média ponderada dos 7 blocos WSI | `WSIInterviewGraph` |
| `rubric_score` | 0–100 | Média das rubricas avaliadas | `RubricEvaluationService` |
| `prerequisites_score` | 0–100 | % de requisitos obrigatórios atendidos | Match de skills/experiência |
| `recency_score` | 0–100 | Decaimento temporal desde última atividade | Fórmula exponencial |
| `calibration_adjustment` | -20 a +20 | Ajuste de calibração (futuro) | Feedback loop (atualmente 0) |

**Classificação por Score:**
```
Score ≥ 80 → "Forte recomendação" (badge verde)
Score 60-79 → "Recomendado" (badge azul)
Score 40-59 → "Revisar manualmente" (badge amarelo) — trigger HITL
Score < 40  → "Não recomendado" (badge vermelho)
```

**Surfacing do LIA Score:**
- Kanban cards (badge colorido)
- Funil de talentos (coluna LIA Score ordenável)
- Float Chat (análise de candidato)
- Ranking (ordenação por score)
- ProactiveInsightCard (average_lia_score)

### 6.3 Avaliação por Rubrica Multi-dimensional

- **O que faz:** Avaliação estruturada com rubricas customizáveis
- **Input:** candidato, vaga, rubricas selecionadas
- **Processing:** IA real (Claude)
- **Output:** Score por rubrica + score consolidado + justificativa
- **Arquivo:** `lia-agent-system/app/services/rubric_evaluation_service.py`

### 6.4 Busca Inteligente de Candidatos

- **O que faz:** Busca local (PostgreSQL) + busca externa (Pearch AI)
- **Input:** query texto livre, filtros estruturados
- **Processing:** Local + API externa
- **Output:** Lista de candidatos com scores de match
- **Ferramentas:** `search_candidates` em `app/domains/sourcing/tools/query_tools.py`

### 6.5 Comparação de Candidatos

- **O que faz:** Comparação multi-dimensional entre 2+ candidatos
- **Input:** `candidate_ids[]`, `job_context`
- **Processing:** IA real (Claude via Kanban Agent)
- **Output:** Tabela comparativa com dimensões, scores, recomendação
- **Ferramenta:** `compare_candidates` em `app/domains/analytics/tools/analytics_query_tools.py`
- **Endpoint:** `POST /orchestrator/job-chat` com `detect_command_type() → COMPARAR_CANDIDATOS`
- **Prompt template:** `kanban_assistant_prompts.py` → `COMPARAR_CANDIDATOS` (linha 280)

### 6.6 Calibração de Candidatos

- **O que faz:** Sessão de calibração onde recrutador avalia candidatos pré-selecionados
- **Input:** `job_vacancy_id`, `job_description`, `technical_skills[]`, `behavioral_competencies[]`
- **Processing:** Pearch AI busca candidatos → scoring de match → montagem de perfis calibrados
- **Output:** Lista de `CalibrationCandidate` com scores, experiências, skills mapeados
- **Execução:** API externa (Pearch AI) + processamento local (scoring)
- **Arquivo:** `plataforma-lia/src/services/lia-api.ts` (linhas 144-183)
- **Endpoints:** `POST /calibration/start`, `POST /calibration/feedback`, `GET /calibration/status`

**Fluxo:**
1. Iniciar sessão → Pearch retorna candidatos com `overallScore`
2. Recrutador avalia cada um (aprova/rejeita com `lia_score` e `feedback_reason`)
3. Candidatos aprovados → `addCandidatesToPipeline()` para adicionar ao pipeline

```typescript
interface CalibrationCandidate {
  id, name, photoUrl, linkedinUrl, currentRole, currentCompany, location, education,
  highlights: { icon, label, value }[],
  experiences: { company, role, period, duration, skills[] }[],
  educationHistory: { institution, degree, field, period }[],
  skillMap: { category, skills[] }[], languages: string[],
  matchCriteria: { criteria, met, score }[],
  overallScore: number, averageTenure, currentTenure
}
```

### 6.7 Geração de JD Enriquecida

- **O que faz:** Gera job description completa e otimizada a partir de inputs do wizard
- **Input:** Título, requisitos técnicos, competências, localização, salário
- **Processing:** IA (Claude via Wizard Agent)
- **Output:** JD formatada com seções, keywords SEO, linguagem inclusiva
- **Execução:** IA real (Claude)
- **Ferramenta:** `generate_enriched_jd` em `app/domains/job_management/tools/job_wizard_tools.py`

### 6.8 Benchmark Salarial

- **O que faz:** Compara salário proposto com dados de mercado
- **Input:** `job_title`, `location`, `seniority_level`
- **Processing:** IA (Claude via JobIntake Agent) + dados de mercado
- **Output:** Competitividade, faixa sugerida, ajustes recomendados
- **Execução:** IA real (Claude)
- **Ferramenta:** `search_salary_benchmark`, `get_intelligent_salary`

### 6.9 Análise de Skills e Gaps

- **O que faz:** Mapeia skills do candidato vs requisitos da vaga e identifica gaps
- **Input:** `candidate_id`, `job_vacancy_id`
- **Processing:** IA (Claude) + matching semântico (EmbeddingService)
- **Output:** Skills mapeadas (match/gap/bonus), score de aderência, recomendações de desenvolvimento
- **Ferramenta:** `analyze_skills` em Talent Tool Registry
- **Arquivo:** `app/domains/recruiter_assistant/agents/talent_tool_registry.py`

### 6.10 Pipeline Health e Bottleneck Analysis

- **O que faz:** Analisa saúde do pipeline e identifica gargalos
- **Input:** `job_vacancy_id`
- **Processing:** Query SQL (tempos por etapa, taxas de conversão)
- **Output:** Gargalos com recomendações de ação, comparação com benchmarks
- **Ferramenta:** `identify_bottlenecks`, `get_bottleneck_analysis` em Kanban Tool Registry
- **Surfacing:** Kanban Chat + Dashboard

### 6.11 Silver Medalists (Candidatos Reutilizáveis)

- **O que faz:** Identifica candidatos rejeitados em vagas anteriores que podem ser bons fits para novas vagas
- **Input:** `job_vacancy_id` (nova vaga), `company_id`
- **Processing:** Matching semântico (embedding de skills/experiência) + filtro de disponibilidade
- **Output:** Lista de candidatos "prata" com score de match e vaga original
- **Ferramenta:** `find_silver_medalists` em Kanban Tool Registry
- **Arquivo:** `app/domains/recruiter_assistant/agents/kanban_tool_registry.py`

### 6.12 SLA Monitoring e Alertas

- **O que faz:** Monitora SLAs por etapa do pipeline e gera alertas
- **Input:** `job_vacancy_id`, `company_id`
- **Processing:** Comparação de tempos reais vs SLAs configurados na política
- **Output:** Status de SLA (OK/WARNING/CRITICAL), candidatos em violação
- **Ferramenta:** `check_sla` em Jobs Mgmt Tool Registry
- **Surfacing:** Dashboard, SaturationBadge, SmartAlerts

### 6.13 Comunicação Multi-Canal

- **O que faz:** Envio de comunicação via Email, WhatsApp, Teams
- **Input:** `candidate_id(s)`, `template`, `channel`, `message_content`
- **Processing:** Template rendering (Jinja2) + envio via serviço do canal
- **Output:** Confirmação de envio, tracking de delivery/open rates
- **Ferramentas:** `send_email`, `send_whatsapp`, `send_batch_communication`
- **Compliance:** Horário comercial (8h-20h BRT), rate limiting, opt-out, LGPD consent check
- **Cooldown:** Anti-spam com intervalo mínimo entre comunicações

### 6.14 Relatórios com Export PDF

- **O que faz:** Gera relatórios detalhados de vagas, pipeline, candidatos
- **Input:** `job_vacancy_id` ou `company_id`, `report_type`
- **Processing:** Query SQL + formatação IA
- **Output:** Relatório estruturado com métricas, gráficos, recomendações
- **Ferramentas:** `generate_report`, `generate_pipeline_report`, `generate_job_report`
- **Export:** PDF via `job-report-modal.tsx` no frontend
- **Surfacing:** JobReportModal, Chat

### 6.15 Offer Generation

- **O que faz:** Gera proposta de trabalho formal para candidato aprovado
- **Input:** `candidate_id`, `job_vacancy_id`, `salary`, `benefits`, `start_date`
- **Processing:** Template rendering + personalização IA
- **Output:** Documento de proposta formatado
- **Ferramenta:** `generate_offer` em Pipeline Tool Registry
- **Compliance:** LGPD Art. 7 I (consentimento para dados contratuais)

### 6.16 Scheduling Inteligente

- **O que faz:** Agendamento de entrevistas com detecção de conflitos
- **Input:** `candidate_id(s)`, `interviewer_id(s)`, `preferred_dates[]`, `interview_type`
- **Processing:** Verificação de calendário (Google/Teams) + slot-filling
- **Output:** Evento agendado + notificações automáticas
- **Integração:** Google Calendar, Microsoft Teams, Zoom
- **Arquivo:** `app/domains/interview_scheduling/agents/interview_graph.py`

### 6.17 Data Subject Request (DSR)

- **O que faz:** Processa solicitações do titular de dados (LGPD Art. 18)
- **Input:** `candidate_id`, `request_type` (access/rectification/deletion/portability)
- **Processing:** Coleta de dados, masking, geração de relatório
- **Output:** Relatório de dados do titular OU execução de alteração/exclusão
- **Arquivo:** `app/services/dsr_export_service.py`
- **SLA:** 15 dias úteis (LGPD Art. 18 §5)

---

## 7. Templates de Resposta do Chat

### 7.1 Job Analytics — 8 Command Templates

**Arquivo:** `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`

| # | Comando                  | Agente Executor         | Prompt Template (resumido)                           |
|---|--------------------------|-------------------------|------------------------------------------------------|
| 1 | `funnel_analysis`        | AnalistaFeedbackAgent   | "Analise o funil da vaga {job_title}. Mostre: candidatos por etapa, taxa de conversão, gargalos, tempo médio por etapa." |
| 2 | `comparative_analysis`   | AnalistaFeedbackAgent   | "Compare as vagas selecionadas: {job_titles}. Analise: tempo médio, taxa de conversão, qualidade de candidatos." |
| 3 | `bottleneck_detection`   | AnalistaFeedbackAgent   | "Identifique gargalos na vaga {job_title}: etapas com maior tempo de espera, candidatos parados, ações pendentes." |
| 4 | `time_to_fill_prediction`| AnalistaFeedbackAgent   | "Preveja o tempo para preencher a vaga {job_title} com base em dados históricos e progresso atual." |
| 5 | `candidate_quality_score`| AvaliadorWSIAgent       | "Avalie a qualidade dos candidatos da vaga {job_title}: fit técnico médio, fit cultural, diversidade de fontes." |
| 6 | `sourcing_effectiveness` | SourcingAgent           | "Analise a efetividade do sourcing para {job_title}: melhores canais, taxa de conversão por fonte, custo por candidato." |
| 7 | `weekly_summary`         | AnalistaFeedbackAgent   | "Gere o resumo semanal de recrutamento: novos candidatos, movimentações, entrevistas realizadas, propostas enviadas." |
| 8 | `salary_benchmark`       | JobIntakeAgent          | "Compare o salário da vaga {job_title} com o mercado: está competitivo? Sugestões de ajuste." |

**Fallback offline:** Se agente IA falha, `process_analytics_request()` retorna `{"success": false, "error": str(e)}` — sem template offline alternativo.

#### Exemplo completo: `funnel_analysis` (ilustrativo)

**Input do usuário:** "Analise o funil da vaga Dev Backend Senior"

**Resposta LIA (formato baseado no template de `job_analytics_prompt_service.py`):**
```markdown
## Análise do Funil — Dev Backend Senior

### Candidatos por Etapa
| Etapa               | Candidatos | % do Total |
|---------------------|-----------|------------|
| Aplicação           | 156       | 100%       |
| Triagem Curricular  | 89        | 57%        |
| Entrevista Técnica  | 34        | 22%        |
| Entrevista Final    | 12        | 7.7%       |
| Proposta            | 5         | 3.2%       |
| Contratado          | 3         | 1.9%       |

### Taxa de Conversão por Etapa
- Aplicação → Triagem: **57%** (benchmark: 60%)
- Triagem → Entrevista: **38%** (benchmark: 35%) ✅
- Entrevista → Final: **35%** (benchmark: 40%) ⚠️
- Final → Proposta: **42%** (benchmark: 50%) ⚠️
- Proposta → Contratação: **60%** (benchmark: 70%) ⚠️

### Gargalos Identificados
1. **Entrevista Técnica** — Tempo médio: 8.3 dias (benchmark: 5 dias)
2. **Proposta** — Taxa de aceitação abaixo do benchmark

### Recomendações
- Adicionar mais entrevistadores técnicos para reduzir tempo
- Revisar competitividade salarial na etapa de proposta
```

**Fallback offline:** `{"success": false, "error": "Serviço indisponível. Tente novamente em alguns minutos."}`

### 7.2 Kanban — 18 Command Templates

**Arquivo:** `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`

| # | Comando                 | Tipo        | Resposta esperada (JSON format obrigatório)                |
|---|-------------------------|-----------  |------------------------------------------------------------|
| 1 | `rankear_candidatos`    | Análise IA  | `{ranking: [{posicao, candidato_id, score_fit, forcas[], gaps[], justificativa}], insights, recomendacao}` |
| 2 | `performance_funil`     | Análise IA  | `{metricas: {total_candidatos, por_etapa, taxa_conversao_geral, taxa_por_etapa}, performance: {status, pontos_fortes, pontos_atencao, benchmark}}` |
| 3 | `gargalos_processo`     | Análise IA  | `{gargalos: [{etapa, tipo, descricao, impacto, recomendacao}], visao_geral, prioridades}` |
| 4 | `comparar_candidatos`   | Análise IA  | Comparativo detalhado com dimensões e recomendação         |
| 5 | `resumir_perfil`        | Análise IA  | Resumo executivo do candidato                              |
| 6 | `candidatos_ativos`     | Query local | Lista de candidatos ativos na vaga                         |
| 7 | `taxa_conversao`        | Query local | Taxa de conversão por etapa                                |
| 8 | `tempo_medio`           | Query local | Tempo médio por etapa do pipeline                          |
| 9 | `candidatos_parados`    | Query local | Candidatos sem movimentação recente                        |
| 10| `top_candidatos`        | Análise IA  | Top candidatos por score/fit                               |
| 11| `mover_candidato`       | Ação        | Execução via `ActionExecutor.move_candidate()`             |
| 12| `enviar_email`          | Ação        | Execução via `ActionExecutor.send_email()`                 |
| 13| `disparar_triagem`      | Ação        | Execução via `ActionExecutor.start_screening()`            |
| 14| `agendar_entrevista`    | Ação        | Execução via `ActionExecutor.schedule_interview()`         |
| 15| `solicitar_dados`       | Ação        | Execução via `ActionExecutor.request_data()`               |
| 16| `analisar_perfil`       | Análise IA  | Análise aprofundada com recomendações                      |
| 17| `aprovar_candidato`     | Ação        | Execução via `ActionExecutor.approve_candidate()`          |
| 18| `analise_geral`         | Análise IA  | Análise geral do pipeline (fallback default)               |

**Cada template inclui:**
- `keywords[]` — palavras-chave para detecção
- `prompt_template` — prompt com placeholders `{job_context}`, `{candidates_context}`, `{pipeline_context}`
- `response_sections[]` — seções esperadas na resposta
- `follow_up_prompts[]` — sugestões de próximos passos

**Fallback offline:** Templates de análise retornam dados do banco local quando LLM falha. Templates de ação retornam erro com mensagem: "Desculpe, ocorreu um erro ao processar sua requisição."

#### Exemplo completo: `resumir_perfil` (ilustrativo)

**Input do usuário:** "Me fale sobre a candidata Maria Santos"

**Resposta LIA (JSON formatado como markdown):**
```json
{
  "resumo_executivo": "Maria Santos é uma profissional senior com 8 anos de experiência em desenvolvimento backend, atualmente como Tech Lead na Nubank.",
  "perfil_profissional": {
    "cargo_atual": "Tech Lead",
    "empresa_atual": "Nubank",
    "experiencia_anos": 8,
    "formacao": "Ciência da Computação - USP",
    "principais_skills": ["Python", "Go", "Kubernetes", "AWS", "System Design"],
    "certificacoes": ["AWS Solutions Architect", "CKA"]
  },
  "analise_fit": {
    "score_fit": 92,
    "pontos_fortes": ["Experiência sólida em arquitetura distribuída", "Liderança técnica comprovada", "Stack alinhada com requisitos"],
    "pontos_atencao": ["Sem experiência com Kafka (requisito desejável)", "Pretensão salarial 15% acima da faixa"],
    "fit_cultural": "Alto — histórico de mentoria e contribuições open source"
  },
  "perguntas_entrevista": [
    "Como você lidou com uma migração de monolito para microsserviços?",
    "Descreva uma situação de conflito técnico na equipe e como resolveu"
  ],
  "proximos_passos": "Recomendo agendar entrevista técnica com o time de arquitetura"
}
```

**Fallback offline:** Retorna dados básicos do banco sem análise IA: nome, cargo, empresa, skills cadastradas.

#### Exemplo completo: `mover_candidato` (ilustrativo — ação com HITL)

**Input do usuário:** "Mova o João Silva para Entrevista Técnica"

**Resposta LIA (needs_confirmation: true):**
```
Entendi! Vou mover o candidato João Silva para a etapa **Entrevista Técnica**.

Confirmação necessária:
- Candidato: João Silva
- De: Triagem Curricular
- Para: Entrevista Técnica
- Vaga: Dev Backend Senior

Confirma esta movimentação?
```

**Após confirmação do usuário:**
```
João Silva movido para Entrevista Técnica com sucesso!
Próximo passo sugerido: Agendar entrevista técnica com o gestor.
```

**Fallback offline:** `"Desculpe, não foi possível executar a movimentação. Tente novamente em alguns minutos."`

### 7.3 Float Chat — Comandos de Análise

**Detecção via `analysisCommands[]` (candidates-page.tsx, linha 5664):**

| Comando                    | Ação                                      |
|----------------------------|--------------------------------------------|
| "analisar potencial"       | Análise de potencial de crescimento via IA |
| "resumo executivo"         | Resumo executivo dos resultados de busca   |
| "resumir busca"            | Resumo consolidado da busca                |
| "top 5" / "top5"           | Top 5 melhores candidatos                  |
| "comparar"                 | Comparação entre candidatos selecionados   |
| "pontos a desenvolver"     | Pontos de desenvolvimento                  |
| "vagas ideais"             | Tipos de vagas adequadas                   |
| "definir tipo"             | Classificação de tipo de perfil            |

#### Exemplo completo: "top 5" (ilustrativo)

**Input do usuário:** "Top 5 candidatos para essa busca"

**Resposta LIA:**
```markdown
## Top 5 Candidatos — Busca: Desenvolvedor Python Senior

| # | Candidato        | LIA Score | Experiência | Localização  | Destaque                          |
|---|------------------|-----------|-------------|--------------|-----------------------------------|
| 1 | Ana Costa        | 92        | 8 anos      | São Paulo    | Tech Lead na Nubank, AWS cert.    |
| 2 | Carlos Mendes    | 89        | 6 anos      | Remoto       | Contribuidor Django, speaker      |
| 3 | Beatriz Lima     | 87        | 7 anos      | São Paulo    | Data Platform no iFood            |
| 4 | Diego Santos     | 85        | 5 anos      | Campinas     | MLOps + Python, startup exp.      |
| 5 | Elena Ferreira   | 83        | 9 anos      | Rio de Janeiro| Backend Lead na Stone             |

### Análise do Pool
- **Score médio:** 87.2 (acima do benchmark de 75)
- **Disponibilidade:** 3/5 disponíveis para contato imediato
- **Faixa salarial:** R$ 16.000 - R$ 28.000
```

**Fallback offline:** "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre 'Top 5 candidatos para essa busca...' Como posso ajudar você hoje?" com `suggested_prompts: ["Criar uma nova vaga", "Buscar candidatos", "Ver minhas tarefas pendentes"]`

#### Exemplo completo: "comparar" (ilustrativo)

**Input do usuário:** "Compare Ana Costa e Carlos Mendes"

**Resposta LIA:**
```markdown
## Comparação: Ana Costa vs Carlos Mendes

| Dimensão              | Ana Costa (92)        | Carlos Mendes (89)     |
|-----------------------|-----------------------|------------------------|
| Experiência           | 8 anos                | 6 anos                 |
| Stack técnica         | Python, Go, K8s, AWS  | Python, Django, Docker |
| Liderança             | Tech Lead (3 anos)    | IC Senior              |
| Certificações         | AWS SA, CKA           | Nenhuma                |
| Disponibilidade       | 30 dias               | Imediata               |
| Pretensão salarial    | R$ 25.000             | R$ 20.000              |

### Recomendação
Ana Costa é mais adequada para a posição devido à experiência em liderança técnica e certificações. Carlos Mendes é uma opção sólida se o budget for mais restrito e houver disponibilidade imediata.
```

---

## 8. Análises e Relatórios

### 8.1 ProactiveInsightCard

**Arquivo:** `plataforma-lia/src/components/proactive-insight-card.tsx`
**Ativação:** Exibido automaticamente após busca de candidatos em `candidates-page.tsx`
**Execução:** Processamento local (backend calcula distribuições sem LLM); campo `narrative` opcional (IA quando disponível)

**Dados entregues (`SearchAnalytics`):**
- **Summary:** total_candidates, local_count, global_count, average_lia_score
- **Contact quality:** with_valid_phone, with_valid_email, with_linkedin (contagens + percentuais)
- **Distributions:** seniority (Record), location (Record), work_model (Record)
- **Top skills:** skill + count + percentage
- **Top companies:** company + count
- **Experience range:** min, max, average, median (anos)
- **Alerts:** tipo (warning/info/success) + mensagem
- **Suggested actions:** id, label, icon, description, action_type

**Como são computados:**
- Backend analisa os candidatos retornados pela busca
- Distribuições calculadas por contagem/agrupamento
- Alertas baseados em thresholds (ex: "Poucos candidatos com telefone válido")
- Ações sugeridas baseadas no contexto da busca

### 8.2 SaturationBadge

**Arquivo:** `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx`
**Ativação:** Header do kanban de cada vaga
**Execução:** Processamento local (backend calcula thresholds sem LLM)
**Endpoint:** `GET /api/backend-proxy/job-vacancies/{jobId}/saturation-status/`

**Dados entregues (`SaturationStatus`):**
- `approved_count` / `saturation_threshold` → `saturation_percentage`
- `is_saturated` (boolean), `slots_remaining`
- `recommendation`: `"continue_screening"` | `"pause_screening"`
- Canal orgânico vs sourcing com thresholds independentes
- `last_screened_at`, `saturation_disabled_until`

**Como são computados:**
- Backend conta candidatos aprovados por canal
- Compara com threshold configurado (por empresa/vaga)
- Estados: `normal` (< 90%), `almost` (≥ 90%), `saturated` (orgânico ou sourcing saturado)

**Ações do usuário:**
- Aumentar threshold: `POST /job-vacancies/{jobId}/unlock-pipeline/` com `{action: "increase_threshold", new_threshold}`
- Desativar temporariamente: `{action: "disable_temporarily", disable_hours}`

### 8.3 JobReportModal

**Arquivo:** `plataforma-lia/src/components/job-report-modal.tsx`
**Ativação:** Botão em `jobs-page.tsx` e `job-kanban-page.tsx`
**Execução:** Processamento local (dados atualmente mockados no frontend)
**Exportação:** PDF via `html2canvas` + `jsPDF`

**Seções selecionáveis (7):**
1. **Overview** — Dados gerais da vaga (título, departamento, localização)
2. **Funnel** — Total candidatos (156), screening (89), interview (34), final (12), hired (3), taxa conversão (1.9%), time-to-hire (23 dias), custo (R$ 4.500)
3. **Candidates** — Top 5 com nome, score, status, fit %
4. **Timeline** — Eventos: vaga publicada → triagem → entrevistas → testes → decisão → contratação
5. **Costs** — Budget total/gasto/restante + breakdown (divulgação, plataformas, testes, equipe, LIA/automação)
6. **Performance** — Channel performance: LinkedIn (67 cand, 89% qualidade), Website (45, 76%), LIA Database (28, 92%), Referral (16, 94%)
7. **Recommendations** — NPS (87), satisfação candidato (4.6/5), satisfação gestor (4.8/5), benchmarks mercado

**Nota:** Dados atualmente hardcoded no frontend. Funcionalidade incompleta — precisa integrar com backend real.

### 8.4 SearchAnalytics

Interface compartilhada com `ProactiveInsightCard` (ver 5.1). Utilizada em `candidates-page.tsx` após buscas para fornecer insights automáticos sobre os resultados.

---

## 9. Sistema Preditivo e Insights

### 9.1 Ferramentas Preditivas (Analytics Agent)

**Execução:** IA (Claude via Analytics Agent); dados alimentados por queries ao PostgreSQL

| Ferramenta              | Input                      | Processing                              | Output                               | Surfacing UI                     |
|-------------------------|----------------------------|-----------------------------------------|--------------------------------------|----------------------------------|
| `get_prediction_metrics`| `job_id`, `time_range`    | Query histórico + modelo de regressão   | Previsões de hiring (prazo, prob.)   | Analytics dashboard, Chat        |
| `get_ml_predictions`    | `job_id`, `model_type`    | Modelo ML treinado em dados da empresa  | Previsões com confidence intervals   | Analytics dashboard              |
| `get_conversion_patterns`| `job_id`/`company_id`    | Análise de padrões no funil             | Taxas de conversão por etapa/fonte   | JobReportModal, Chat             |
| `get_smart_alerts`      | `company_id`, `threshold` | Detecção de anomalias e tendências      | Lista de alertas com severidade      | Dashboard, SaturationBadge       |
| `get_trends`            | `metric`, `time_range`    | Séries temporais de métricas            | Tendências com visualização          | Analytics dashboard              |
| `get_bottleneck_analysis`| `job_id`                 | Análise de tempos por etapa             | Gargalos + recomendações             | Kanban Chat, Dashboard           |

### 9.2 Predições Específicas

| Predição                     | Dados Utilizados                            | Endpoint/Serviço                          | Surfacing UI                |
|------------------------------|---------------------------------------------|-------------------------------------------|-----------------------------|
| Probabilidade de contratação | Histórico vagas similares, pool atual       | `predictive_analytics_service.py`         | Chat, Analytics             |
| Time-to-Fill (TTF)           | Tempos por etapa, velocidade pipeline       | `time_to_fill_prediction` command         | Chat, JobReportModal        |
| Risco de dropout             | Tempo parado, engajamento, mercado          | `get_smart_alerts` + `EWS`               | SaturationBadge, Alertas    |
| Previsão de pipeline         | Conversão histórica, volume atual           | `get_ml_predictions`                      | Analytics dashboard         |
| Predição salarial            | Mercado, cargo, localização, senioridade    | `get_intelligent_salary` / `salary_benchmark` | Wizard, Chat            |

### 9.3 Serviços de Inteligência Operacional

**Arquivos:** `app/services/predictive_analytics_service.py`, `search_analytics_service.py`, `wizard_analytics_service.py`, `learning_analytics_service.py`

| # | Serviço                       | Tipo           | Dados Utilizados                     | Surfacing UI                       |
|---|-------------------------------|----------------|--------------------------------------|------------------------------------|
| 1 | Pipeline Velocity Engine      | Local (query)  | Timestamps de movimentação por etapa | Kanban page, Analytics dashboard   |
| 2 | Zero-Touch Scheduling         | IA + Local     | Disponibilidade, preferências, SLAs  | Communication Agent, Calendar API  |
| 3 | Silver Medalists              | IA (matching)  | Histórico de candidatos rejeitados   | Sourcing Agent, ProactiveInsightCard|
| 4 | Recruiter Intelligence        | Local (metrics)| Volume, velocidade, qualidade        | Analytics dashboard                |
| 5 | Early Warning Score (EWS)     | IA (anomaly)   | Pipeline metrics, tempos, saturação  | SaturationBadge, SmartAlerts       |
| 6 | Journey Intelligence          | Local + IA     | Touchpoints do candidato             | Kanban page                        |
| 7 | Recruiter Perf. Benchmark     | Local (metrics)| KPIs comparativos entre recrutadores | Analytics dashboard                |
| 8 | Pipeline Prediction           | IA (ML model)  | Dados históricos vagas similares     | JobReportModal, Analytics          |

### 9.4 Serviços Preditivos Detalhados (8 serviços)

**9.4.1 PredictiveAnalyticsService**
- **Arquivo:** `app/services/predictive_analytics_service.py`
- **Função:** Orquestra todas as previsões de contratação
- **Métodos:** `predict_time_to_fill()`, `predict_hiring_probability()`, `get_pipeline_forecast()`
- **Dados:** Histórico de vagas similares (setor, senioridade, localização)
- **Modelo:** Regressão linear + ajustes sazonais

**9.4.2 PipelinePredictionService**
- **Arquivo:** `app/services/pipeline_prediction_service.py`
- **Função:** Prevê volume e conversão do pipeline nas próximas semanas
- **Dados:** Taxas de conversão históricas por etapa + volume atual
- **Output:** Previsão de candidatos por etapa em T+7, T+14, T+30 dias

**9.4.3 EarlyWarningService (EWS)**
- **Arquivo:** `app/services/early_warning_service.py`
- **Função:** Detecta riscos proativamente e gera alertas
- **Alertas:**
  - Vaga estagnada (sem movimentação > SLA)
  - Candidato em risco de dropout (sem contato > 72h)
  - Pipeline saturado (> 50 candidatos na mesma etapa)
  - SLA prestes a expirar (< 24h para deadline)
- **Severidade:** `INFO`, `WARNING`, `CRITICAL`
- **Surfacing:** SaturationBadge, ProactiveInsightCard, SmartAlerts

**9.4.4 JourneyIntelligenceService**
- **Arquivo:** `app/services/journey_intelligence_service.py`
- **Função:** Rastreia e analisa a jornada completa do candidato
- **Touchpoints:** Aplicação → Triagem → WSI → Entrevista → Oferta → Contratação
- **Métricas:** Tempo entre touchpoints, engajamento, satisfação

**9.4.5 SectorBenchmarkService**
- **Arquivo:** `app/services/sector_benchmark_service.py`
- **Função:** Compara métricas da empresa com benchmarks do setor
- **Dados:** Mercado (via Pearch), dados internos agregados
- **Métricas comparadas:** Time-to-hire, custo por contratação, taxa de aceitação, diversidade

**9.4.6 ModelDriftService**
- **Arquivo:** `app/services/model_drift_service.py`
- **Função:** Monitora degradação de performance dos modelos de scoring
- **Detecção:** PSI (Population Stability Index) + KL Divergence
- **Thresholds:** PSI > 0.2 → alerta de drift significativo
- **Ação:** Notifica admin + flag para retreino

**9.4.7 FeatureEngineeringService**
- **Arquivo:** `app/services/feature_engineering.py`
- **Função:** Gera features derivadas para modelos preditivos
- **Features:** Velocidade de pipeline, taxa de conversão por etapa, sazonalidade, diversidade do pool

**9.4.8 OutcomePredictorService**
- **Arquivo:** `app/services/outcome_predictor.py`
- **Função:** Prevê resultado (contratação/rejeição) baseado em features do candidato
- **Input:** Score WSI + Score LIA + Experiência + Skills match
- **Output:** Probabilidade de contratação + confidence interval

### 9.5 Response Cache Service

- **Arquivo:** `app/services/response_cache_service.py`
- Cache de respostas para intents analíticas recorrentes
- `generate_cache_key()`: intent + contexto + mensagem + company_id
- Invalidação por entidade: `invalidate_for_job()`, `invalidate_for_candidate()`, `invalidate_for_company()`
- Invalidação por padrão regex: `invalidate_by_pattern()`
- TTL configurável por tipo de query (padrão: 5 min para analytics, 1 min para pipeline data)

### 9.6 Salary Benchmark Real — D7

**Implementado em:** Sprint Y1/D7
**Arquivo:** `app/services/salary_benchmark_service.py`
**Endpoint:** `GET /api/v1/salary-benchmark?title=&location=&seniority=&company_id=`

Benchmark salarial com dados de mercado reais via Apify (Glassdoor/LinkedIn), com fallback para dados estáticos setoriais:

- **Fluxo:** Cache Redis (TTL=7 dias) → Apify scraping → fallback estático por senioridade
- **Dados retornados:** `{p25, p50, p75, currency, source, fetched_at}` — `source` indica "external" (Apify) ou "fallback" (estático)
- **Seniorities cobertas:** junior, pleno, senior, especialista, gerente
- **Integração anti-sycophancy:** Injetado como contexto no prompt de `evaluate_candidate()` via `sector_benchmark_service.py` (Crença #11)
- **Fail-open:** Sempre retorna resultado válido mesmo sem Apify disponível
- **Cache key:** `salary_benchmark:{job_title}:{seniority}:{location}` (slug normalizado)

### 9.7 Comparação de Candidatos — D9

**Implementado em:** Sprint Y1/D9
**Arquivo BE:** `app/services/candidate_comparison_service.py`
**Endpoint:** `POST /api/v1/candidates/compare` (2–4 candidatos, `X-Company-ID` obrigatório)
**Frontend:** `src/components/modals/candidate-compare-modal.tsx` + `src/hooks/use-candidate-compare.ts`
**Proxy FE:** `src/app/api/backend-proxy/candidates/compare/route.ts`

Análise comparativa multi-dimensional entre 2 a 4 candidatos com modal visual dedicado:

- **Input:** `{candidate_ids: string[], job_id?: string, scenario?: "A"|"B"|"C"}`
- **Scenarios:** A (scores existentes), B (re-avaliação para vaga), C (comparação genérica sem vaga)
- **Scores por dimensão:** technical, experience, education, soft_skills, cultural_fit
- **Output:** scores comparativos, candidato vencedor, análise textual por dimensão
- **PII:** `strip_pii_for_llm_prompt()` aplicado ao `candidates_summary` antes do prompt LLM (SEG-3B)
- **Multi-tenant:** `X-Company-ID` validado como UUID na camada da API

---

## 10. Quick Actions e Ações Bulk

### 10.1 Quick Actions do Chat Full (chat-page.tsx)

| Quick Action                          | Mensagem Enviada                                 |
|---------------------------------------|--------------------------------------------------|
| Criar nova vaga                       | `"Criar uma nova vaga"`                          |
| Solicitar aprovação                   | `"Solicite aprovação de nova vaga"`              |
| Compartilhar com gestor               | `"Compartilhe candidatos com gestor"`            |
| Solicitar feedback                    | `"Solicite feedback de entrevista"`              |
| Consultar candidato                   | `"Consulte informações sobre candidato"`         |
| Adicionar candidato                   | `"Adicione novo candidato"`                      |
| Reagendar entrevista                  | `"Reagende uma entrevista"`                      |
| Agendar entrevista (contextual)       | `"agendar entrevista"`                           |
| Avaliar fit técnico                   | `"avaliar fit técnico do candidato"`             |
| Gerar email follow-up                 | `"gerar email de follow-up"`                     |
| Enviar WhatsApp                       | `"enviar mensagem whatsapp"`                     |
| Comparar perfis                       | `"comparar perfis de candidatos"`                |

### 10.2 Ações Bulk — Funil de Talentos (UnifiedBulkActionsBar)

**Arquivo:** `plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx`
**Contexto:** `context="funnel"` na candidates-page

| # | Ação              | Prop               | Disponível em Funil | Disponível em Kanban |
|---|-------------------|---------------------|---------------------|----------------------|
| 1 | Mover etapa       | `onMoveStage`      | Sim                 | Sim                  |
| 2 | Rejeitar          | `onReject`          | Sim                 | Sim                  |
| 3 | Enviar email      | `onEmail`           | Sim                 | Sim                  |
| 4 | Agendar entrevista| `onSchedule`        | Sim                 | Sim                  |
| 5 | Adicionar a vaga  | `onAddToVacancy`    | Sim                 | Sim                  |
| 6 | Mover para lista  | `onMoveToList`      | Sim                 | Sim                  |
| 7 | Exportar          | `onExport`          | Sim                 | Sim                  |
| 8 | Esconder          | `onHide`            | Sim                 | Sim                  |
| 9 | Triagem WSI       | `onWSIScreening`    | Sim                 | Sim                  |

### 10.3 Ações Contextuais — ContextualActionsBanner

**Arquivo:** `plataforma-lia/src/components/contextual-actions-banner.tsx`

| # | Ação              | Disponível |
|---|-------------------|------------|
| 1 | Mover etapa       | Sim        |
| 2 | Rejeitar          | Sim        |
| 3 | Enviar email      | Sim        |
| 4 | Agendar entrevista| Sim        |
| 5 | Adicionar a vaga  | Sim        |
| 6 | Mover para lista  | Sim        |
| 7 | Esconder          | Sim        |
| 8 | Triagem WSI       | Sim        |

### 10.4 Ações do Kanban Chat (ActionExecutor)

**Arquivo:** `lia-agent-system/app/orchestrator/action_executor.py`

O `ActionExecutor` é o ponto único de execução de ações confirmadas. Implementa o padrão closed-loop: agente propõe → HITL confirma → executor executa → resultado retorna.

**9 action_ids suportados:**

| # | action_id | Descrição | HITL | Serviço Executor |
|---|-----------|-----------|:----:|------------------|
| 1 | `move_candidate` | Move candidato entre etapas | Sim | `pipeline_service.move_candidate()` |
| 2 | `send_email` | Envia email ao candidato | Sim | `email_service.send()` |
| 3 | `schedule_interview` | Agenda entrevista | Sim | `scheduling_service.create_event()` |
| 4 | `start_screening` | Inicia triagem WSI | Sim | `wsi_service.start_session()` |
| 5 | `analyze_profile` | Executa análise de perfil | Não | `smart_extractor.analyze()` |
| 6 | `pause_job` | Pausa vaga (suspende pipeline) | Sim | `job_service.update_status("paused")` |
| 7 | `close_job` | Fecha vaga (arquiva) | Sim | `job_service.update_status("closed")` |
| 8 | `duplicate_job` | Duplica vaga existente | Não | `job_service.duplicate()` |
| 9 | `reopen_job` | Reabre vaga fechada | Sim | `job_service.update_status("active")` |

**Fluxo HITL completo:**
```
1. Agente ReAct identifica ação necessária
2. Agente retorna: {action_id, params, needs_confirmation: true, explanation}
3. Frontend exibe modal de confirmação com explanation
4. Usuário confirma → WS mensagem tipo "approval_response"
5. PendingActionStore.resolve(action_id) → params
6. ActionExecutor.execute(action_id, params, context)
   ├── Valida action_id contra whitelist
   ├── Verifica RBAC (company_id + user permissions)
   ├── Executa via domain service
   ├── Registra resultado em AgentActivity
   └── Emite evento para AutomationTriggerService
7. Resultado retorna ao frontend via WebSocket
```

**Validações de segurança:**
- Whitelist de action_ids (9 definidos — qualquer outro é rejeitado)
- Isolamento multi-tenant (`company_id` obrigatório)
- Rate limiting por usuário
- Auditoria: cada execução registrada com `user_id`, `action_id`, `params`, `result`, `timestamp`

---

## 11. Registro de Ferramentas por Agente

### 11.1 Padrão de Registro

Cada agente ReAct possui um `tool_registry.py` dedicado que define as ferramentas disponíveis. O registro segue o padrão:

```python
class {Domain}ToolRegistry:
    @staticmethod
    def get_tools(context: Dict) -> List[BaseTool]:
        tools = []
        tools.append(StructuredTool.from_function(
            func=tool_function,
            name="tool_name",
            description="Descrição para o LLM",
            args_schema=ToolArgsSchema
        ))
        return tools
```

### 11.2 Ferramentas por Agente

**Wizard Agent (10 tools):**
`validate_job_requirements`, `get_salary_benchmarks`, `search_salary_benchmark`, `validate_job_fields`, `get_job_suggestions`, `save_job_draft`, `get_company_config`, `generate_enriched_jd`, `check_job_draft_health`, `generate_report`
- **Arquivo:** `app/domains/job_management/agents/wizard_tool_registry.py`

**Pipeline Agent (12 tools):**
`view_candidate_profile`, `move_candidate`, `analyze_cv`, `run_wsi_screening`, `schedule_interview`, `send_communication`, `add_notes`, `batch_move`, `add_to_shortlist`, `view_screening_results`, `view_interview_notes`, `generate_offer`
- **Arquivo:** `app/domains/cv_screening/agents/pipeline_tool_registry.py`

**Sourcing Agent (15 tools):**
`set_search_criteria`, `suggest_skills`, `search_candidates`, `filter_results`, `view_candidate`, `analyze_profile`, `compare_candidates`, `score_candidate`, `add_to_shortlist`, `remove_from_shortlist`, `rank_candidates`, `send_outreach`, `generate_message`, `track_response`, `generate_report`
- **Arquivo:** `app/domains/sourcing/agents/sourcing_tool_registry.py`

**Talent Agent (13 tools):**
`search_candidates`, `list_candidates`, `view_candidate_profile`, `compare_candidates`, `rank_candidates`, `analyze_skills`, `recommend_actions`, `create_shortlist`, `export_report`, `check_search_fairness`, `get_talent_pool_benchmarks`, `check_pool_health`, `generate_report`
- **Arquivo:** `app/domains/recruiter_assistant/agents/talent_tool_registry.py`

**Kanban Agent (21 tools):**
`get_pipeline_benchmarks`, `get_pipeline_summary`, `get_stage_metrics`, `list_stage_candidates`, `analyze_stage`, `identify_bottlenecks`, `get_candidate_aging`, `compare_stages`, `suggest_movements`, `batch_move_candidates`, `send_batch_communication`, `start_screening_batch`, `generate_pipeline_report`, `check_rejection_fairness`, `find_silver_medalists`, `get_recruiter_backlog`, `get_recruiter_benchmark`, `get_journey_metrics`, `get_at_risk_candidates`, `get_pipeline_prediction`, `get_pipeline_velocity`
- **Arquivo:** `app/domains/recruiter_assistant/agents/kanban_tool_registry.py`

**Jobs Management Agent (12 tools):**
`validate_job_action_fairness`, `get_recruitment_benchmarks`, `list_jobs`, `view_job_details`, `get_portfolio_metrics`, `compare_jobs`, `check_sla`, `analyze_bottlenecks`, `pause_job`, `reopen_job`, `close_job`, `update_priority`
- **Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py`

**Policy Agent (13 tools):**
`get_current_policy`, `save_policy_field`, `get_policy_summary`, `validate_policy_compliance`, `get_company_context`, `get_industry_benchmarks`, `explain_policy_impact`, `get_setup_progress`, `get_platform_benchmarks`, `detect_policy_impact_anomalies`, `get_policy_effectiveness_report`, `save_policy_block`, `apply_industry_defaults`
- **Arquivo:** `app/domains/hiring_policy/agents/policy_tool_registry.py`

**Analytics Agent (6 tools):**
`get_job_insights`, `predict_hiring_metrics`, `generate_job_report`, `generate_candidate_report`, `get_search_analytics`, `get_agent_performance`
- **Arquivo:** `app/domains/analytics/agents/analytics_tool_registry.py`

**Communication Agent (5 tools):**
`send_email`, `send_whatsapp`, `get_communication_history`, `schedule_message`, `check_rate_limit`
- **Arquivo:** `app/domains/communication/agents/communication_tool_registry.py`

**ATS Integration Agent (5 tools):**
`sync_candidate_to_ats`, `fetch_candidate_from_ats`, `validate_ats_fields`, `bulk_sync_candidates`, `get_sync_status`
- **Arquivo:** `app/domains/ats_integration/agents/ats_integration_tool_registry.py`

**Automation Agent (6 tools):**
`decompose_task`, `prioritize_tasks`, `get_execution_plan`, `build_dag`, `check_dependencies`, `get_next_tasks`
- **Arquivo:** `app/domains/automation/agents/automation_tool_registry.py`

**Pipeline Transition Agent (20 tools):**
`get_candidate_profile`, `get_candidate_wsi_scores`, `get_candidate_screening_results`, `get_candidate_salary_info`, `update_candidate_field`, `request_data_collection`, `get_stage_sub_statuses`, `suggest_sub_status`, `extract_preferences`, `validate_transition`, `get_job_context`, `schedule_secondary_task`, `personalize_communication`, `check_rejection_fairness`, `check_candidate_availability`, `get_recruiter_preferences`, `save_recruiter_preference`, `get_interview_details`, `cancel_interview`, `reschedule_interview`
- **Arquivo:** `app/domains/pipeline/agents/pipeline_tool_registry.py`

### 11.3 Scope Config — Ferramentas por Contexto

**Arquivo:** `lia-agent-system/app/tools/scope_config.py`

O `scope_config.py` define quais ferramentas estão disponíveis baseado no **contexto de navegação** do recrutador no frontend. É independente do agente — funciona como um filtro de acesso.

**TALENT_FUNNEL (20 tools)** — Quando recrutador está na visão de candidatos:

| Tipo | Ferramentas |
|------|-------------|
| Query (11) | `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `compare_candidates`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns` |
| Action (9) | `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `send_email`, `send_whatsapp`, `send_bulk_email`, `export_candidates` |

**JOB_TABLE (19 tools)** — Quando recrutador está na lista de vagas:

| Tipo | Ferramentas |
|------|-------------|
| Query (12) | `search_jobs`, `get_job_details`, `get_pipeline_stats`, `get_recruiter_metrics`, `get_velocity_metrics`, `get_efficiency_metrics`, `get_comparative_metrics`, `get_workload_distribution`, `get_hiring_quality`, `get_cost_metrics`, `get_trends`, `get_market_benchmarks` |
| Action (7) | `create_job`, `update_job`, `pause_job`, `close_job`, `publish_job`, `export_job_analytics`, `generate_report` |

**IN_JOB (25 tools)** — Quando recrutador está dentro de uma vaga específica:

| Tipo | Ferramentas |
|------|-------------|
| Query (14) | `get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts` |
| Action (11) | `update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback` |

**GLOBAL (2 tools)** — Disponível em qualquer contexto:
`generate_report`, `schedule_report`

### 11.4 Interação Scope Config × Tool Registry

O fluxo de resolução de ferramentas combina ambos os sistemas:

```
1. Frontend envia context (scope: "IN_JOB", job_id: 123)
2. CascadedRouter → determina domain → seleciona agente
3. Agente carrega tools do ToolRegistry (domain-specific)
4. ScopeConfig filtra: apenas tools permitidos no scope atual
5. Tools filtrados → passados ao LLM como ferramentas disponíveis
```

Resultado: um agente pode ter 20 tools no registro, mas apenas 11 ficam disponíveis se o scope atual for `IN_JOB`.

---

## 12. Infraestrutura de Prompts

### 12.1 Arquitetura de Prompts — Visão Geral

A plataforma utiliza uma infraestrutura de prompts modular, versionada e baseada em YAML, com carregamento dinâmico e cache.

```
app/shared/prompts/
├── prompt_registry.py        # Registro centralizado com versionamento
├── agent_prompts.py          # Interface Python que expõe prompts carregados de YAML
├── loader.py                 # PromptLoader — carregamento e cache de YAML
├── templates.py              # PromptTemplate + PromptLibrary (CoT + few-shot)
├── anti_sycophancy_block.py  # Bloco canônico anti-sycophancy
├── job_wizard.py             # Lógica especializada para prompts de criação de vagas
└── examples/                 # Few-shot examples
    ├── orchestrator_examples.py
    └── pipeline_examples.py

app/prompts/                  # Armazenamento YAML
├── shared/
│   ├── agent_prompts.yaml    # Prompts base compartilhados
│   ├── lia_persona.yaml      # Persona LIA + HR_VOCABULARY + ETHICAL_GUIDELINES
│   └── defensive.yaml        # Prompts defensivos
└── domains/
    ├── sourcing.yaml
    ├── cv_screening.yaml
    ├── job_management.yaml
    └── ...
```

### 12.2 Estrutura Canônica de 10 Seções (System Prompts)

Todo system prompt de agente segue uma composição modular de 10 seções, conforme definido em `docs/ai-prompts/AI_PROMPT_CREATION_GUIDE.md`:

| # | Seção | Descrição | Obrigatória |
|---|-------|-----------|-------------|
| 1 | **Persona LIA** | Identidade e tom de comunicação | Sim |
| 2 | **Ethical Guidelines** | Regras anti-viés obrigatórias | Sim |
| 3 | **Agent Identity** | Nome, papel e expertise específica | Sim |
| 4 | **HR Vocabulary** | Termos técnicos de RH contextualizados | Sim |
| 5 | **Responsibilities** | Lista de funções do agente (IN/OUT) | Sim |
| 6 | **Specific Methodologies** | WSI, Bloom, Big Five, DISC (se aplicável) | Condicional |
| 7 | **Data Persistence (OBRIGATÓRIO)** | Regras para salvar dados no WeDOTalent | Sim |
| 8 | **ATS Synchronization** | Mapeamento para ATSs externos | Condicional |
| 9 | **Structured Response Formats** | Templates Markdown para output consistente | Sim |
| 10 | **Current Context** | Placeholder `{{context}}` para dados dinâmicos | Sim |

### 12.3 Componentes Compartilhados de Prompt

**HR_VOCABULARY** (carregado de `lia_persona.yaml`):
Termos técnicos de RH brasileiros padronizados: *pipeline, fit cultural, shortlist, senioridade, soft skills, hard skills, time-to-hire, turnover, employer branding, onboarding, headhunting, hunting passivo, talent pool*.

**ETHICAL_GUIDELINES** (carregado de `lia_persona.yaml`):
Regras obrigatórias para avaliação livre de viés:
1. Ignorar nome, gênero, idade, aparência física, estado civil
2. Usar linguagem neutra e inclusiva
3. Avaliar exclusivamente com base em competências e experiência
4. Não inferir habilidades a partir de universidade ou localização
5. Reportar padrões de viés detectados ao FairnessGuard

**ANTI_SYCOPHANCY_OPERATIONAL** (`anti_sycophancy_block.py`):
```
REGRAS ABSOLUTAS:
1. Nunca concordar com pedidos que violem fairness/compliance
2. Recusar filtros discriminatórios com justificativas baseadas em dados
3. Verificar afirmações antes de confirmar
4. "Discordância com dados é preferível a concordância sem evidência"
5. Se recrutador insistir em prática antiética → escalar para supervisor
```

### 12.4 Prompt Registry — Versionamento

**Arquivo:** `app/shared/prompts/prompt_registry.py`

O `PromptRegistry` mantém prompts versionados com suporte a rollback:

```python
class PromptRegistry:
    def register(self, name: str, template: str, version: str = "v1.0.0"):
        """Registra prompt com versionamento semântico"""
    
    def get(self, name: str, version: str = "latest") -> PromptTemplate:
        """Busca prompt por nome e versão"""
    
    def list_versions(self, name: str) -> List[str]:
        """Lista todas as versões de um prompt"""
```

**Estrutura canônica de cada entrada YAML de prompt (Z3-02):**

```yaml
# Estrutura obrigatória por entrada em qualquer *.yaml de prompts
prompts:
  - key: wizard_system_v1
    version: "v1.3.0"
    updated_at: "2026-03-19T00:00:00Z"   # OBRIGATÓRIO — Z3-02; ISO-8601 UTC
    description: "System prompt do Wizard Agent — criação de vagas"
    content: |
      Você é LIA, assistente de recrutamento da WeDOTalent...
```

> **Sprint Z3-02:** Os **9 YAMLs em `app/prompts/domains/`** (`sourcing.yaml`, `cv_screening.yaml`, `job_management.yaml`, `recruiter_assistant.yaml`, `analytics.yaml`, `communication.yaml`, `ats_integration.yaml`, `hiring_policy.yaml`, `automation.yaml`) e os YAMLs compartilhados (`app/prompts/shared/`) foram atualizados para incluir o campo `updated_at` (ISO-8601 UTC) em cada entrada de prompt. Isso permite rastrear quando cada prompt foi modificado, complementando o `version` semântico. O campo é exibido na UI de gerenciamento de prompts e é auditável via `PromptRegistry.get_metadata(key)`.

**Verificação:**
```bash
grep -r "updated_at" app/prompts/ --include="*.yaml" | wc -l
# Deve retornar ≥ número de entradas de prompts (1 por entrada)
```

### 12.5 Prompts Defensivos

**Arquivo:** `app/shared/robustness/defensive_prompts.py`
**YAML:** `app/prompts/shared/defensive.yaml`

| Componente | Função |
|------------|--------|
| `CLARIFICATION_TRIGGERS` | Dispara quando input é ambíguo (ex: "faça algo com os candidatos") |
| `OUT_OF_SCOPE_RESPONSES` | Templates para pedidos fora do mandato do agente |
| `AMBIGUITY_DETECTION_PROMPT` | Instruções para identificar input vago |
| `ERROR_RECOVERY_PROMPT` | Instruções para recuperação de falhas de processamento |

### 12.6 Input Validation e Response Filtering

**Arquivo de validação:** `app/shared/robustness/input_validation.py`
**Arquivo de filtragem:** `app/shared/robustness/response_filter.py`

O pipeline de segurança de prompts segue 3 camadas:
1. **Pre-processing:** `PromptInjectionGuard.check(message)` — detecta tentativas de injeção
2. **Validation:** `input_validation` — valida formato, tamanho, caracteres
3. **Post-processing:** `response_filter` — remove PII, stack traces, IDs internos antes de enviar ao usuário

**Pipeline completo de processamento de mensagem:**
```
Mensagem do usuário
     ↓
[1. PromptInjectionGuard] ─── detecta patterns maliciosos
     │                        "ignore previous instructions"
     │                        "system prompt override"
     │                        SQL injection patterns
     │                        Se detectado → rejeita com mensagem amigável
     ↓
[2. Input Validation] ────── valida formato e limites
     │                        Max length: 4096 caracteres
     │                        Caracteres permitidos: Unicode + emojis
     │                        Rate check: max 60 msg/min
     │                        Se inválido → erro descritivo
     ↓
[3. Sanitização] ─────────── sanitize_text()
     │                        Remove HTML tags
     │                        Normaliza whitespace
     │                        Escapa caracteres especiais
     ↓
[4. PII Masking (pre-LLM)] ─ strip_pii_for_llm_prompt()
     │                        Mascara CPF, email, telefone
     │                        Antes de enviar ao LLM
     ↓
[5. Processamento LLM] ───── Agente ReAct ou StateGraph
     ↓
[6. Response Filter] ─────── Filtragem de saída
     │                        Remove stack traces
     │                        Remove IDs internos (UUIDs)
     │                        Remove referências a tools/funções
     │                        Detecta respostas técnicas (_TECHNICAL_PATTERNS)
     │                        Se detecta → fallback LLM para humanizar
     ↓
[7. PIIMaskingFilter] ─────── Filtra logs
                               Intercepta antes de escrita em log
                               Mascara PII automaticamente
```

### 12.7 Exemplos de System Prompts por Agente

**Wizard Agent — Trecho do system prompt (simplificado):**
```
Você é LIA, a assistente inteligente de recrutamento da WeDOTalent.
Seu papel: Wizard Agent — especialista em criação de vagas.

RESPONSABILIDADES:
- Guiar o recrutador na criação de vagas completas e inclusivas
- Sugerir skills, salários e requisitos baseados em dados de mercado
- Gerar JDs otimizadas com linguagem inclusiva
- Validar requisitos contra FairnessGuard

PROIBIÇÕES:
- Nunca aceitar requisitos discriminatórios (gênero, idade, aparência)
- Nunca confirmar dados sem verificar com as ferramentas disponíveis
- Nunca gerar JDs com linguagem excludente

ANTI-SYCOPHANCY:
{ANTI_SYCOPHANCY_OPERATIONAL}

FORMATO DE RESPOSTA:
- Sempre em PT-BR
- Markdown formatado
- Dados estruturados quando solicitado
- Perguntas consultivas quando faltam informações

CONTEXTO ATUAL:
{{context}}
```

**Kanban Agent — Templates de Comando (18 tipos):**

| # | Tipo | Template Key | Exemplo de Input |
|---|------|-------------|------------------|
| 1 | `RESUMO_PIPELINE` | `pipeline_summary` | "Resumo do pipeline" |
| 2 | `RANKEAR_CANDIDATOS` | `rank_candidates` | "Rankeie os candidatos" |
| 3 | `COMPARAR_CANDIDATOS` | `compare_candidates` | "Compare Ana e Carlos" |
| 4 | `ANALISE_PERFIL` | `profile_analysis` | "Analise o perfil de João" |
| 5 | `TRIAGEM_WSI` | `wsi_screening` | "Inicie triagem WSI" |
| 6 | `MOVER_CANDIDATO` | `move_candidate` | "Mova João para Entrevista" |
| 7 | `REJEITAR_CANDIDATO` | `reject_candidate` | "Rejeite o candidato" |
| 8 | `AGENDAR_ENTREVISTA` | `schedule_interview` | "Agende entrevista" |
| 9 | `ENVIAR_EMAIL` | `send_email` | "Envie email para Ana" |
| 10 | `SUGERIR_ACAO` | `suggest_action` | "O que devo fazer?" |
| 11 | `GERAR_FEEDBACK` | `generate_feedback` | "Gere feedback para Carlos" |
| 12 | `ANALISE_COMPARATIVA` | `comparative_analysis` | "Compare esta vaga com similares" |
| 13 | `KPI_VAGA` | `job_kpis` | "KPIs desta vaga" |
| 14 | `TIME_TO_FILL` | `ttf_prediction` | "Previsão de time-to-fill" |
| 15 | `BOTTLENECK` | `bottleneck_analysis` | "Identifique gargalos" |
| 16 | `SILVER_MEDALISTS` | `silver_medalists` | "Candidatos reutilizáveis" |
| 17 | `BULK_MOVE` | `bulk_move` | "Mova os top 5 para Entrevista" |
| 18 | `GENERAL` | `general_query` | Qualquer outra pergunta |

---

## 13. Camada de Inteligência — Shared Services

### 13.1 EmbeddingService

**Arquivo:** `app/shared/intelligence/embedding_service.py`
**Provider:** Gemini (`text-embedding-004`)
**Dimensão:** 768

| Método | Descrição |
|--------|-----------|
| `generate_embedding(text)` | Gera vetor 768-dim para texto único |
| `generate_batch_embeddings(texts)` | Batch de vetores com chunking |
| `chunk_text(text, overlap)` | Divide texto longo com sobreposição configurável |

**Uso:** Base para busca semântica de candidatos, matching job-candidato, e detecção de similaridade.

### 13.2 SemanticSearchService

**Arquivo:** `app/shared/intelligence/semantic_search_service.py`
**SLA:** P95 < 300ms
**Cache:** Redis (TTL configurável)

Expansão semântica para buscas de candidatos em 4 domínios:

| Domínio | Exemplo Input | Expansões |
|---------|---------------|-----------|
| `SKILLS` | "React" | "ReactJS, React.js, React Native, frontend, SPA" |
| `JOB_TITLES` | "Desenvolvedor" | "Developer, Programador, Engenheiro de Software, SWE" |
| `INDUSTRIES` | "Fintech" | "Fintech, Finanças, Banking, Pagamentos, Crédito" |
| `COMPANIES` | "Google" | "Alphabet, Google Cloud, GCP, Google Brasil" |

**Fallback:** Taxonomias estáticas hardcoded quando LLM está indisponível (circuit breaker OPEN).

**Pipeline de Busca Semântica (4 etapas):**

```
Etapa 1: Query Expansion
   "desenvolvedor React senior São Paulo"
     ↓ SemanticSearchService.expand_query()
   skills: ["React", "ReactJS", "React.js", "React Native", "frontend"]
   titles: ["Desenvolvedor", "Developer", "Engenheiro de Software"]
   locations: ["São Paulo", "SP", "Grande São Paulo"]

Etapa 2: Embedding Generation
   EmbeddingService.generate_embedding(expanded_query)
     ↓
   vetor 768-dim: [0.023, -0.156, 0.891, ...]

Etapa 3: Similarity Search
   PostgreSQL pgvector: candidates.embedding <=> query_embedding
     ↓
   cosine_similarity > 0.7 → candidatos ranqueados

Etapa 4: Re-ranking
   Candidatos filtrados por critérios adicionais:
   - Disponibilidade (ativo nos últimos 90 dias)
   - Experiência mínima (se especificada)
   - Localização (se especificada)
   - LIA Score (se já calculado)
```

**Configurações do SemanticSearchService:**

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `SIMILARITY_THRESHOLD` | 0.7 | Cosine similarity mínimo |
| `MAX_EXPANSIONS` | 10 | Máximo de termos expandidos por domínio |
| `CACHE_TTL` | 3600s | TTL do cache Redis para expansões |
| `MAX_RESULTS` | 50 | Limite de candidatos retornados |
| `BATCH_SIZE` | 100 | Tamanho do batch para embedding em lote |
| `EXPANSION_TEMPERATURE` | 0.0 | Temperatura da LLM para expansão (determinístico) |

**Taxonomias Estáticas (fallback):**

Arquivo: `app/shared/intelligence/taxonomies.py`

| Categoria | Entradas | Exemplo |
|-----------|----------|---------|
| `SKILL_SYNONYMS` | ~200 | `"python": ["python3", "py", "cpython"]` |
| `TITLE_SYNONYMS` | ~80 | `"developer": ["dev", "engineer", "programmer"]` |
| `LOCATION_ALIASES` | ~50 | `"são paulo": ["sp", "sampa", "grande sp"]` |
| `INDUSTRY_MAP` | ~30 | `"tech": ["tecnologia", "software", "it"]` |

### 13.3 SmartExtractor

**Arquivo:** `app/shared/intelligence/smart_extractor.py`

Extrai parâmetros estruturados de linguagem natural usando abordagem híbrida:

```
Input: "Busque desenvolvedores Python em São Paulo com 5+ anos"
         ↓
ParamExtractor (regex patterns — param_patterns.py)
   ├── skill: "Python" (confidence: 0.95)
   ├── location: "São Paulo" (confidence: 0.90)
   └── experience: "5+" (confidence: 0.85)
         ↓
Se confidence < threshold → fallback LLM
         ↓
Output: {skills: ["Python"], location: "São Paulo", min_experience: 5}
```

**Vantagem:** Regex para queries previsíveis (rápido, sem custo LLM); LLM para queries complexas ou ambíguas.

**Padrões Regex do ParamExtractor:**

| Parâmetro | Pattern (simplificado) | Exemplos |
|-----------|----------------------|----------|
| `skill` | Lista de 500+ skills conhecidas | "Python", "React", "SQL", "Docker" |
| `experience` | `(\d+)\+?\s*(anos?\|years?)` | "5+ anos", "3 years", "mínimo 2 anos" |
| `salary` | `R?\$?\s*(\d+[\.,]?\d*)\s*(k\|mil\|reais?)` | "R$ 15k", "15 mil", "$5000" |
| `location` | Banco de 200+ cidades/estados | "São Paulo", "SP", "remoto" |
| `education` | `(graduação\|mestrado\|doutorado\|MBA)` | "mestrado em TI", "graduação" |
| `contract` | `(CLT\|PJ\|freelancer?\|estágio)` | "CLT", "PJ", "estágio" |
| `availability` | `(imediata\|(\d+)\s*dias?\|(\d+)\s*meses?)` | "imediata", "30 dias", "2 meses" |

**Threshold de Confiança:**
- Confidence ≥ 0.8 → Usa resultado regex (custo zero)
- Confidence 0.5-0.8 → Confirma com LLM (custo baixo)
- Confidence < 0.5 → Extração completa via LLM (custo normal)

### 13.4 NavigationIntent e ActionIntent

O sistema classifica cada mensagem do usuário em duas dimensões:

**NavigationIntent** (para onde o usuário quer ir):
- `STAY` — manter na tela atual
- `GO_TO_JOB` — navegar para vaga específica
- `GO_TO_CANDIDATE` — navegar para candidato
- `GO_TO_LIST` — navegar para lista/pipeline

**ActionIntent** (o que o usuário quer fazer):
- `QUERY` — buscar/consultar informações
- `MUTATE` — alterar dados (HITL obrigatório)
- `NAVIGATE` — navegar entre telas
- `CHAT` — conversa livre

Combinação: `NavigationIntent × ActionIntent` determina se a resposta precisa de confirmação HITL, se deve disparar navegação no frontend, e qual agent deve processar.

### 13.5 Agent Bus — E10

**Implementado em:** Sprint Y5/E10
**Arquivo:** `app/shared/agents/agent_bus.py`
**Padrão:** Redis Pub/Sub
**Canal:** `lia:agent_bus:{company_id}:{to_agent}`

Barramento de comunicação direta entre agentes sem passar pelo Orchestrator. Permite coordenação assíncrona de domínios:

| Método | Descrição |
|--------|-----------|
| `publish(from_agent, to_agent, event_type, payload, company_id)` | Publica `AgentEvent` no canal Redis do agente destino. Fail-open: retorna False em erro. |
| `subscribe(agent_name, handler)` | Registra handler in-memory para agente (usado em testes) |
| `dispatch_local(event)` | Despacha evento para subscribers locais (modo teste sem Redis) |
| `list_subscribers()` | Lista agentes com handlers registrados |

**Casos de uso:**
- Sourcing → Pipeline: `candidate_imported` quando candidato é captado
- Pipeline → Communication: `stage_changed` para disparar notificações
- WSI → Kanban: `score_available` quando entrevista conclui

**Audit trail:** Toda publicação gera registro via `audit_service.log_decision(decision_type="agent_communication")`.
**Fail-open:** Exceções em `publish()` são capturadas e logadas como WARNING — nunca propagam para o chamador.

**Dataclass `AgentEvent`:** `from_agent`, `to_agent`, `event_type`, `payload` (dict), `company_id`, `event_id` (UUID hex), `published_at` (ISO string)

### 13.6 Event Sourcing Imutável — E12

**Implementado em:** Sprint Y5/E12
**Arquivo:** `app/services/event_store_service.py`
**Model:** `app/models/event_store.py`
**Migration:** `alembic/versions/047_add_event_store.py`
**Endpoint:** `GET /api/v1/event-history?aggregate_type=&aggregate_id=&company_id=`

Registro append-only de todos os eventos de domínio para auditoria SOX/ISO 27001 e replay de estado:

**Modelo `DomainEvent` (tabela `domain_events`):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `aggregate_type` | String(100) | "candidate" \| "job" \| "pipeline" |
| `aggregate_id` | String(255) | UUID da entidade |
| `event_type` | String(100) | "CandidateMoved" \| "JobCreated" \| etc. |
| `event_data` | JSONB | Payload arbitrário por event_type |
| `company_id` | String(255) | Multi-tenant obrigatório |
| `created_by` | String(255) | user_id ou agent_name |
| `sequence_number` | BigInteger | Auto-incrementado por aggregate (UniqueConstraint) |

**Invariante:** NENHUMA operação de UPDATE ou DELETE é permitida — somente `append()`.

**Métodos do `EventStoreService`:**

| Método | Descrição |
|--------|-----------|
| `append(aggregate_type, aggregate_id, event_type, data, company_id, db)` | Grava evento com próximo sequence_number. Fail-open: retorna False em erro. |
| `get_history(aggregate_type, aggregate_id, db, from_sequence, limit)` | Retorna lista ordenada de eventos para replay. Fail-open: retorna `[]`. |
| `reconstruct_state(aggregate_type, aggregate_id, db, folder)` | Reconstrói estado atual aplicando fold sobre eventos. Default folder: merge de `event_data`. |

**Índices:** `ix_domain_events_aggregate` (aggregate_type + aggregate_id + created_at), `ix_domain_events_company`, `ix_domain_events_event_type`

### 13.7 Adaptive Routing Learning — E9

**Implementado em:** Sprint Y5/E9
**Arquivo:** `app/services/routing_learning_service.py`
**Model:** `app/models/routing_feedback.py`
**Migration:** `alembic/versions/046_add_routing_feedback.py`

O sistema aprende com correções de roteamento para melhorar a accuracy futura do `CascadedRouter`:

**Modelo `RoutingFeedback` (tabela `routing_feedback`):**
- `company_id`, `session_id`, `message_hash` (MD5), `routed_domain` (escolha do router), `actual_domain` (escolha correta), `corrected` ("true"/"false"), `corrected_at`

**Métodos do `RoutingLearningService`:**

| Método | Descrição |
|--------|-----------|
| `record_correction(session_id, routed_domain, actual_domain, company_id, db)` | Persiste sinal de correção. Fail-open. |
| `compute_domain_confidence_adjustments(company_id, db)` | Calcula fator 0.8–1.2 por domínio baseado em taxa de acerto dos últimos 30 dias. |
| `get_cached_adjustments(company_id)` | Lê ajustes pré-calculados do Redis (TTL=24h). Fail-open → `{}`. |
| `cache_adjustments(company_id, adjustments)` | Armazena ajustes no Redis com TTL=24h. |

**Lógica de ajuste:**
- Janela: últimos 30 dias (`_LOOKBACK_DAYS=30`), mínimo 10 amostras (`_MIN_SAMPLES=10`)
- `error_rate > 0.3` → fator `max(0.8, 1.0 - error_rate × 0.5)` (reduz confiança)
- `error_rate < 0.05` → fator `min(1.2, 1.0 + (0.05 - error_rate) × 2)` (eleva confiança)
- Ajuste aplicado ao score do `CascadedRouter` no Tier 4 (LLM intent)

**Beat schedule:** `routing-recompute-daily` às 07h UTC em `celery_app.py`
**Flag:** `USE_ADAPTIVE_ROUTING=true` (padrão); desabilitar em testes para isolar comportamento

---

## 14. Motor de Automação

### 14.1 Arquitetura do Motor

**Diretório:** `app/domains/automation/`

O motor de automação implementa o padrão **Trigger → Condition → Action** com suporte a execução automática ou sugestão para aprovação humana.

```
┌─────────────────────────────────────────────┐
│          StageAutomationEngine               │
│  (Router central de eventos de pipeline)     │
│                                              │
│  Eventos:                                    │
│  ├── SCREENING_COMPLETED                     │
│  ├── STAGE_CHANGED                           │
│  ├── CANDIDATE_HIRED                         │
│  ├── INTERVIEW_SCHEDULED                     │
│  ├── OFFER_SENT                              │
│  └── CANDIDATE_REJECTED                      │
│                                              │
│  Decisão:                                    │
│  ├── confidence >= threshold → auto_execute  │
│  └── confidence < threshold → AISuggestion   │
│      (aguarda aprovação humana)              │
└─────────────────┬───────────────────────────┘
                  ▼
     ┌────────────────────────┐
     │  AutomationService      │
     │  (Executor de ações)    │
     │                         │
     │  Ações:                 │
     │  ├── Send Email         │
     │  ├── Send WhatsApp      │
     │  ├── Create Task        │
     │  ├── Send Notification  │
     │  └── Update Status      │
     │                         │
     │  Cooldown: anti-spam    │
     └────────────────────────┘
```

### 14.2 AutomationTriggerService — Triggers Proativos

**Arquivo:** `app/domains/automation/services/automation_trigger_service.py`

| Trigger | Condição | Ação Padrão |
|---------|----------|-------------|
| `CANDIDATE_NO_CONTACT_48H` | Candidato sem contato há 48h | Email de follow-up |
| `INTERVIEW_REMINDER_24H` | Entrevista em 24h | Lembrete ao recrutador + candidato |
| `JOB_NO_MOVEMENT_5D` | Vaga sem movimentação há 5 dias | Alerta ao recrutador |
| `OFFER_ACCEPTED` | Oferta aceita pelo candidato | Notificação de celebração + próximos passos |

**Lógica:** Verifica banco de dados periodicamente, identifica entidades que satisfazem condições, e dispara `AutomationAction` correspondente.

### 14.3 ProactiveService — Assistência ao Recrutador

**Arquivo:** `app/domains/automation/services/proactive_service.py`

| Funcionalidade | Método | Descrição |
|----------------|--------|-----------|
| Morning Briefing | `generate_daily_briefing()` | Resumo matinal com pendências, entrevistas do dia, alertas |
| End-of-Day Summary | `generate_eod_summary()` | Resumo do dia com ações realizadas, métricas |
| Interview Reminders | `generate_interview_reminders()` | Lembretes de entrevistas próximas |
| Screening Events | `dispatch_screening_completed()` | Notifica quando triagem termina |

**Morning Briefing — Conteúdo (exemplo):**
```markdown
## Bom dia, [Nome]! Aqui está seu briefing de hoje.

### Pendências
- 3 candidatos aguardando feedback há 48h+
- 1 entrevista técnica sem avaliação (Dev Backend - João Silva)
- 2 vagas com pipeline saturado

### Entrevistas Hoje
| Hora  | Candidato      | Vaga              | Entrevistador  |
|-------|---------------|-------------------|----------------|
| 10:00 | Ana Costa     | Tech Lead         | Carlos (Eng)   |
| 14:30 | Pedro Lima    | UX Designer       | Maria (Design) |
| 16:00 | Lucas Santos  | Dev Frontend      | Ana (Tech)     |

### Alertas
⚠️ Vaga "Dev Backend Senior" sem movimentação há 7 dias
⚠️ SLA Triagem: 5 candidatos acima do prazo (meta: 48h)
✅ 3 contratações fechadas esta semana (meta: 4)

### Sugestões
1. Priorizar feedback dos 3 candidatos pendentes
2. Iniciar sourcing ativo para Dev Backend Senior
3. Agendar calibração para vaga UX Designer
```

**Agendamento Celery Beat:**

| Job | Schedule | Fuso | Conteúdo |
|-----|----------|------|----------|
| `morning_briefing` | Seg-Sex 08:00 | BRT | Briefing completo + pendências |
| `interview_reminders` | Contínuo (24h antes) | BRT | Lembrete por candidato |
| `eod_summary` | Seg-Sex 18:00 | BRT | Resumo do dia |
| `weekly_digest` | Sexta 17:00 | BRT | Resumo semanal + métricas |
| `stale_pipeline_check` | Diário 09:00 | BRT | Candidatos parados > SLA |

### 14.4 ActionExecutor — Execução Closed-Loop

**Arquivo:** `app/orchestrator/action_executor.py`

O `ActionExecutor` é o ponto único de execução de ações confirmadas pelo HITL. Suporta **9 action_ids**:

| action_id | Descrição | HITL Required |
|-----------|-----------|:---:|
| `move_candidate` | Move candidato entre etapas do pipeline | Sim |
| `send_email` | Envia email ao candidato/recrutador | Sim |
| `schedule_interview` | Agenda entrevista (Google/Teams/Zoom) | Sim |
| `start_screening` | Inicia triagem WSI de candidato | Sim |
| `analyze_profile` | Executa análise completa de perfil | Não |
| `pause_job` | Pausa vaga (suspende triagem) | Sim |
| `close_job` | Fecha vaga (arquiva) | Sim |
| `duplicate_job` | Duplica vaga existente | Não |
| `reopen_job` | Reabre vaga fechada | Sim |

**Fluxo de execução:**
```python
async def execute(action_id: str, params: Dict, context: ExecutionContext):
    # 1. Valida action_id contra whitelist
    # 2. Resolve serviço executor (domain service)
    # 3. Verifica permissões (RBAC + company_id)
    # 4. Executa ação via serviço do domínio
    # 5. Registra resultado (sucesso/falha)
    # 6. Emite evento para automation triggers
    # 7. Retorna resultado formatado ao frontend
```

---

## 15. Camada de Aprendizado Contínuo

**Diretório:** `app/shared/learning/`

A camada de aprendizado contínuo é composta por 4 serviços que permitem à plataforma melhorar progressivamente sem retreinamento manual.

### 15.1 LearningLoopService — Captura Silenciosa

**Arquivo:** `app/shared/learning/learning_loop_service.py`

O `LearningLoopService` implementa um mecanismo de captura silenciosa ("silent capture") que observa interações do recrutador com sugestões da IA:

| Interação | Significado | Ação do Learning Loop |
|-----------|-------------|----------------------|
| `accept` | Recrutador aceitou sugestão como está | Reforça padrão (peso +1) |
| `modify` | Recrutador editou sugestão antes de usar | Captura diferença como preferência |
| `reject` | Recrutador rejeitou sugestão | Penaliza padrão (peso -1) |

**Métodos-chave:**

| Método | Descrição |
|--------|-----------|
| `capture_feedback(event_type, context, action)` | Registra evento de interação |
| `process_unprocessed_feedback()` | Agrega eventos pendentes em `LearningPattern`; **antes de qualquer update de padrão, chama `LearningSnapshotService.save_snapshot()`** (Z2-01) |
| `get_patterns_for_context(company_id, context)` | Retorna padrões aprendidos para contexto |

**Exemplo:** Se 3+ recrutadores da empresa X editam sugestão de salário para React → sistema aprende faixa salarial preferida e aplica em futuras sugestões.

### 15.1.1 LearningSnapshotService — Rollback de Padrões (Z2-01)

**Arquivo:** `app/shared/learning/learning_snapshot_service.py`

Serviço de snapshot imutável dos padrões de aprendizado, implementado para atender EU AI Act (direito à explicação) e LGPD (reversão de decisões automatizadas). Chamado automaticamente pelo `LearningLoopService` **antes** de qualquer alteração de padrão — garantindo ponto de rollback sempre disponível.

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `save_snapshot(company_id, patterns)` | Persiste snapshot no Redis com chave versionada por timestamp; TTL 30 dias |
| `get_latest_key(company_id)` | Retorna a chave Redis do snapshot mais recente da empresa |
| `list_snapshots(company_id)` | Lista todos os snapshots disponíveis (até MAX_SNAPSHOTS=5 por empresa, LRU) |
| `rollback_to_latest(company_id)` | Restaura padrões do snapshot mais recente via delete + insert no banco |

**Implementação:**
- Redis LIST+SET: chave `lia:learning_snapshot:{company_id}:{timestamp}`
- `MAX_SNAPSHOTS = 5` por empresa (LRU implícito — mais antigo é descartado)
- `_load_patterns()` e `_restore_patterns()` extraídos como métodos internos mockáveis
- Fail-safe em todas as operações (falhas em Redis ou DB não interrompem o loop de aprendizado)

### 15.2 ABTestingService — Teste de Variantes de Prompt

**Arquivo:** `app/shared/learning/ab_testing_service.py`

Gerencia testes A/B para variantes de prompt, permitindo otimização baseada em dados:

| Método | Descrição |
|--------|-----------|
| `get_variant(test_name, session_id)` | Atribui variante via hash determinístico do session_id |
| `record_metric(test_name, variant, metric_name, value)` | Registra métrica de sucesso (ex: taxa de aceitação) |
| `get_test_results(test_name)` | Calcula significância estatística (p-value e z-score) |

**Decisão automática:** Quando uma variante atinge significância estatística (p < 0.05), o sistema promove automaticamente a variante vencedora.

### 15.3 TemplateLearningService — Templates Aprendidos

**Arquivo:** `app/shared/learning/template_learning_service.py`

Automatiza criação de templates de vagas baseado em padrões históricos:

| Método | Descrição |
|--------|-----------|
| `learn_from_job_creation(job_data)` | Analisa nova vaga; se 3+ similares existem → cria template |
| `suggest_templates_for_improvement()` | Identifica padrões de alta frequência sem template |

**Lógica:** Quando o recrutador cria a 4ª vaga de "Desenvolvedor Backend Python" com requisitos similares, o sistema automaticamente gera um template reutilizável, estimando economia de tempo.

### 15.4 FinetuningExport — Exportação para Fine-Tuning

**Arquivo:** `app/shared/learning/finetuning_export.py`

Exporta interações de alta qualidade para fine-tuning de modelos LLM com proteção de dados:

| Método | Descrição |
|--------|-----------|
| `mask_pii(text)` | Mascara Nomes, Emails, Telefones, CPFs via regex |
| `export_wizard_interactions(company_id)` | Converte sugestões aceitas/corrigidas em pares de treino (JSONL) |
| `get_export_stats(company_id)` | Avalia se empresa tem dados suficientes (threshold: 10 interações) |

**Pipeline:** Dados brutos → PII Masking → Filtro de qualidade → Formato JSONL → Export para fine-tuning

### 15.5 LearningExtractor — Extração Pós-Loop

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/learning_extractor.py`

Extrai aprendizados de cada execução do ciclo ReAct e os classifica em 3 categorias:

| Categoria | Descrição | Exemplo |
|-----------|-----------|---------|
| `pattern` | Padrões recorrentes identificados nas interações | "Recrutador sempre pede ranking após triagem" |
| `preference` | Preferências do recrutador/empresa detectadas | "Empresa X prefere candidatos com certificação AWS" |
| `insight` | Insights sobre o processo de recrutamento | "Vagas tech demoram 2x mais que vagas admin" |

### 15.6 LongTermMemoryService

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/long_term_memory.py`

Armazena memórias de longo prazo classificadas por tipo:

**4 Tipos de Memória Válidos (`VALID_MEMORY_TYPES`):**

| Tipo | Propósito | Exemplo de Uso |
|------|-----------|----------------|
| `pattern` | Padrões de comportamento do recrutador | "Sempre rejeita candidatos sem experiência X" |
| `preference` | Preferências persistentes da empresa/recrutador | "Prefere entrevistas às terças e quintas" |
| `learning` | Aprendizados extraídos do LearningExtractor | "WSI scores > 80 correlacionam com contratação" |
| `outcome` | Resultados de ações e decisões | "Candidato contratado após score 85 + entrevista" |

### 15.7 WorkingMemoryService

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/working_memory.py`

Memória de curto prazo para o contexto da sessão atual:
- Mantém estado entre turnos do chat
- Limitada a 20 mensagens por contexto LLM
- Resumo automático a cada N mensagens
- Isolada por sessão (session-safe via `AgentFactory`)

### 15.8 MemoryIntegration

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/memory_integration.py`

Ponte entre WorkingMemory e LongTermMemory:
- `get_enriched_context()` — recupera e formata memórias relevantes para injeção no system prompt
- Combina memórias de curto prazo (sessão) com memórias de longo prazo (empresa/recrutador)
- Filtra por domínio e relevância

### 15.9 FeedbackLearningService

**Arquivo:** `lia-agent-system/app/services/feedback_learning_service.py`

Processa feedback dos recrutadores (thumbs up/down, rating, correções) para melhorar futuras respostas:
- **Feedback positivo (thumbs up / rating ≥ 4):** Armazenado como dados de treinamento de qualidade
- **Feedback negativo com correção:** Gera par DPO (Direct Preference Optimization) para fine-tuning
- **Padrões de feedback:** Identificados e salvos como `learning` na LongTermMemory

### 15.10 OutcomeTracker

**Arquivo:** `lia-agent-system/app/domains/job_management/services/outcome_tracker.py`

Rastreia resultados de contratações para correlacionar com decisões da LIA:
- Candidatos contratados após recomendação → `outcome` positivo
- Candidatos rejeitados que foram recontratados → `outcome` a revisar
- Dados alimentam o loop de aprendizado do LIA Score

### 15.11 TrainingDataService — Export para Fine-tuning

**Arquivo:** `lia-agent-system/app/services/training_data_service.py` (506 linhas)

Exporta dados de treinamento de alta qualidade para fine-tuning de modelos LLM:

**3 Formatos de Exportação:**

| Formato | Método | Estrutura |
|---------|--------|-----------|
| **OpenAI** | `export_openai_format()` | `{"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}` |
| **Anthropic** | `export_anthropic_format()` | Formato nativo Anthropic com `\n\nHuman:` e `\n\nAssistant:` |
| **DPO Pairs** | `export_dpo_pairs()` | `{"chosen": boa_resposta, "rejected": resposta_original, "prompt": user_message}` |

**Critérios de Qualidade (`_is_quality_response`):**
- Rating ≥ 4 OU thumbs == "up"
- Response length > 50 caracteres (`MIN_RESPONSE_LENGTH`)
- Sem padrões de erro (7 patterns: "erro", "error", "exception", "falha", etc.)
- Confidence score ≥ 0.7 (`MIN_CONFIDENCE_SCORE`)

### 15.12 ML Feedback Loop Adaptativo — D6

**Implementado em:** Sprint Y1/D6
**Arquivo:** `app/services/ml_feedback_service.py`
**Model:** `app/models/recruiter_decision_feedback.py` (tabela `recruiter_decision_feedback`)
**Migration:** `alembic/versions/044_add_recruiter_decision_feedback.py`
**Celery task:** `ml.feedback.process_job_weights` (beat: `ml.feedback.recompute_active_jobs` domingo 02h UTC)

Loop de feedback real que ajusta pesos do scoring baseado em decisões do recrutador, corrigindo o `Calibration_Adjustment` que anteriormente retornava sempre 0:

**Tabela `recruiter_decision_feedback`:** `company_id`, `job_id`, `candidate_id`, `lia_score`, `decision` (hire/reject/override_approve/override_reject), `decision_by`, `decision_at`, `created_at`

**Dataclass `FeedbackSignal`:** sinal de feedback com `ai_score`, `recruiter_decision`, `recruiter_score` (opcional), `dimension_overrides` (dict)

**Dataclass `JobScoringWeights`:** pesos adaptativos por dimensão para uma vaga específica:
```python
weights = {
    "technical": 1.0,    # range: 0.7–1.3
    "experience": 1.0,
    "education": 1.0,
    "soft_skills": 1.0,
    "cultural_fit": 1.0,
}
```

**Métodos do `MLFeedbackService`:**

| Método | Descrição |
|--------|-----------|
| `record_signal(db, signal)` | Persiste sinal via `CalibrationService.record_explicit_feedback()`. Fail-open. |
| `compute_job_weights(db, job_id, company_id, lookback_days=30)` | Calcula pesos adaptativos por dimensão. Mínimo 5 amostras (`MIN_FEEDBACK_SAMPLES`). Ajuste limitado a ±30%. |
| `get_weights_for_job(db, job_id, company_id)` | Retorna pesos adaptativos para vaga; computa on-demand. |
| `record_decision(db, company_id, job_id, candidate_id, lia_score, decision)` | Helper simplificado para wiring. |
| `compute_calibration_adjustment(db, company_id, job_id)` | Calcula ajuste de calibração (-5.0 a +5.0) com cache Redis TTL=1h. **Agora retorna valores reais** baseados em peso médio das dimensões. |

**Threshold de divergência:** `OVERRIDE_DIVERGENCE_THRESHOLD=15.0` pontos — divergências menores não geram ajuste.

**Integração:** `lia_score_service.py` lê `compute_calibration_adjustment()` — o `Calibration_Adjustment` agora reflete feedback histórico real.

---

## 16. Infraestrutura — LLM Factory, Policy Middleware, Templates

### 16.1 LLMProviderFactory

**Arquivo:** `app/shared/providers/llm_factory.py`

O `LLMProviderFactory` gerencia os provedores de LLM via padrão Factory + Singleton:

```python
class LLMProviderFactory:
    _providers: Dict[str, Type] = {}    # Classes registradas
    _instances: Dict[str, Any] = {}     # Singletons instanciados
    
    @classmethod
    def register(cls, name: str, provider_class: Type): ...
    
    @classmethod
    def get_provider(cls, name: str = None) -> LLMProvider: ...
    
    @classmethod
    def generate_with_fallback(cls, prompt: str, **kwargs) -> str: ...
```

**Provedores registrados:**

| Provider | Classe | Modelo Padrão | Arquivo |
|----------|--------|---------------|---------|
| `claude` | `ClaudeLLMProvider` | `claude-sonnet-4-6` | `app/shared/providers/llm_claude.py` |
| `gemini` | `GeminiLLMProvider` | `gemini-2.5-flash` | `app/shared/providers/llm_gemini.py` |
| `openai` | `OpenAILLMProvider` | `gpt-4o` | `app/shared/providers/llm_openai.py` |

**Seleção de provedor:**
1. Variável de ambiente `LLM_DEFAULT_PROVIDER` (padrão: `gemini`)
2. Override por domínio (ex: agentes ReAct usam Claude por padrão)
3. Override por chamada específica

**Fallback sequencial:** `generate_with_fallback()` segue a ordem `["claude", "gemini", "openai"]`. Se Claude falha (circuit breaker OPEN) → tenta Gemini → tenta OpenAI.

**Integração com Circuit Breaker:** Antes de cada chamada, verifica estado do circuit breaker do provedor. Se OPEN → pula para próximo na ordem de fallback.

### 16.2 Policy Middleware

**Arquivo:** `app/shared/policy_middleware.py`

O `policy_middleware` atua como dependência FastAPI que injeta `CompanyHiringPolicy` no contexto de cada request:

**Resolução de `company_id` (ordem de prioridade):**
1. Header `x-company-id`
2. Query parameter `company_id`
3. Path parameter `company_id`
4. Fallback para defaults do sistema

**Método principal:**
```python
async def get_policy_from_request(request: Request) -> CompanyHiringPolicy:
    company_id = resolve_company_id(request)
    return await policy_service.get_or_create_policy(company_id)
```

**`resolve_policy_value(policy, field, override=None, default=None)`:**
Utilitário para resolver valores de política com prioridade:
`override explícito > valor da política > default do sistema`

### 16.3 Templates de Comunicação

**Diretório:** `app/domains/communication/templates/`

Templates Jinja2 para comunicação multi-canal:

| Template | Canal | Uso |
|----------|-------|-----|
| `interview_invitation.html` | Email | Convite para entrevista |
| `screening_feedback.html` | Email | Feedback pós-triagem |
| `offer_letter.html` | Email | Proposta de trabalho |
| `rejection_notification.html` | Email | Notificação de não aprovação |
| `follow_up_reminder.html` | Email | Lembrete de follow-up |
| `whatsapp_interview_confirm.txt` | WhatsApp | Confirmação de entrevista |
| `whatsapp_status_update.txt` | WhatsApp | Atualização de status |

**Personalização:** Templates suportam variáveis dinâmicas (`{{candidate_name}}`, `{{job_title}}`, `{{interview_date}}`) + personalização por empresa (logo, cores, tom).

### 16.4 Templates de Vagas

**Serviço:** `app/domains/job_management/services/jd_generator_service.py`

O `JDGeneratorService` gera Job Descriptions enriquecidas usando LLM + templates:

**Pipeline de geração:**
1. Recrutador fornece título + requisitos básicos
2. `JDEnrichmentService` busca benchmarks salariais e skills de mercado
3. `JDGeneratorService` gera JD completa via LLM com seções padronizadas
4. Validação anti-viés (linguagem inclusiva, sem requisitos discriminatórios)
5. Preview para aprovação do recrutador

**Seções da JD gerada:**
- Título e resumo
- Responsabilidades
- Requisitos técnicos e comportamentais
- Benefícios e cultura
- Informações de processo seletivo

### 16.5 Configuração de LLM por Domínio

Cada domínio pode configurar qual provedor LLM utilizar, com fallback automático:

| Domínio | Provider Padrão | Modelo | Fallback | Temperatura |
|---------|----------------|--------|----------|-------------|
| Orchestrator (router) | Gemini | `gemini-2.5-flash` | Claude → OpenAI | 0.0 |
| Wizard | Claude | `claude-sonnet-4-6` | Gemini → OpenAI | 0.3 |
| Pipeline (WSI) | Claude | `claude-sonnet-4-6` | Gemini | 0.2 |
| Sourcing | Claude | `claude-sonnet-4-6` | Gemini | 0.3 |
| Analytics | Claude | `claude-sonnet-4-6` | Gemini | 0.1 |
| Communication | Claude | `claude-sonnet-4-6` | Gemini | 0.5 |
| Kanban | Claude | `claude-sonnet-4-6` | Gemini | 0.3 |
| LLM Cascade Tier 5 | Claude Haiku | `claude-3-haiku` | Sonnet → Opus | 0.0 |
| Embedding | Gemini | `text-embedding-004` | N/A | N/A |
| Semantic Expansion | Claude | `claude-sonnet-4-6` | Taxonomias estáticas | 0.0 |

**Configuração via variáveis de ambiente:**
```
LLM_DEFAULT_PROVIDER=gemini
LLM_AGENT_PROVIDER=claude
LLM_ROUTER_PROVIDER=gemini
LLM_EMBEDDING_PROVIDER=gemini
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=AIza...
OPENAI_API_KEY=sk-...
```

### 16.6 Token Budget por Operação

Limites de tokens estimados por tipo de operação:

| Operação | Input Tokens (est.) | Output Tokens (est.) | Custo Estimado |
|----------|--------------------|--------------------|----------------|
| Roteamento (Tier 5) | 500 | 100 | $0.002 |
| WSI Scoring (1 bloco) | 2.000 | 500 | $0.014 |
| WSI Completo (7 blocos) | 14.000 | 3.500 | $0.098 |
| Rubric Evaluation | 3.000 | 1.000 | $0.024 |
| JD Enrichment | 2.500 | 2.000 | $0.038 |
| Profile Analysis | 3.000 | 1.500 | $0.032 |
| Candidate Comparison | 4.000 | 2.000 | $0.042 |
| Email Generation | 1.000 | 500 | $0.011 |
| Daily Briefing | 2.000 | 1.500 | $0.032 |
| Semantic Expansion | 500 | 200 | $0.004 |

**Nota:** Custos estimados usando preço Claude Sonnet ($0.003/1K input, $0.015/1K output).

---

## 17. Observabilidade e Monitoramento

### 17.1 Métricas Prometheus

**Arquivo:** `app/observability/metrics.py`

**14 métricas registradas:**

**Counters (6):**

| Métrica | Labels | Descrição |
|---------|--------|-----------|
| `llm_requests_total` | `provider`, `model`, `status` | Total de chamadas LLM |
| `agent_iterations_total` | `agent_type`, `domain` | Total de iterações ReAct |
| `fairness_blocks_total` | `agent_type`, `rule` | Bloqueios por FairnessGuard |
| `pipeline_transitions_total` | `from_stage`, `to_stage` | Transições de pipeline |
| `candidates_evaluated_total` | `evaluation_type` | Candidatos avaliados |
| `agent_tool_failures_total` | `agent_type`, `tool_name` | Falhas de ferramentas |

**Histograms (4):**

| Métrica | Buckets | Descrição |
|---------|---------|-----------|
| `llm_latency_seconds` | `[0.1, 0.5, 1, 2, 5, 10, 30]` | Latência de chamadas LLM |
| `http_request_duration_seconds` | `[0.01, 0.05, 0.1, 0.5, 1, 5]` | Duração de requests HTTP |
| `router_latency_ms` | `[1, 5, 10, 50, 100, 500]` | Latência do CascadedRouter |
| `router_confidence_histogram` | `[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]` | Distribuição de confidence do router |

**Gauges (4):**

| Métrica | Descrição |
|---------|-----------|
| `circuit_breaker_state` | Estado dos circuit breakers (0=closed, 1=half_open, 2=open) |
| `active_websocket_connections` | Conexões WebSocket ativas |
| `pending_actions_count` | Ações HITL pendentes de aprovação |
| `token_budget_remaining` | Orçamento de tokens restante por tenant |

### 17.2 Structured Logging

**Arquivo:** `app/shared/structured_logging.py`

O sistema utiliza logs estruturados em formato JSON para integração com ELK/CloudWatch:

**Componentes:**

| Componente | Função |
|------------|--------|
| `JSONFormatter` | Formata logs como JSON com campos padronizados |
| `ContextLogger` | Injeta automaticamente campos de contexto em cada log |
| `setup_structured_logging()` | Configura logging para toda a aplicação |

**Campos injetados automaticamente:**
```json
{
  "timestamp": "2026-03-13T10:30:00Z",
  "level": "INFO",
  "message": "Agent completed task",
  "request_id": "req-abc-123",
  "user_id": "usr-456",
  "tenant_id": "company-789",
  "trace_id": "trace-def-012",
  "agent_type": "WizardReActAgent",
  "domain": "wizard",
  "duration_ms": 1250
}
```

### 17.3 AgentMonitoringService

**Arquivo:** `app/shared/governance/agent_monitoring_service.py`

Monitora saúde e performance de cada agente em tempo real:

**Health Score (0-100):**
```
health_score = (success_rate × 0.4) + (sla_compliance × 0.3) + (response_time_score × 0.3)
```

**Métricas por agente:**

| Métrica | Cálculo | SLA |
|---------|---------|-----|
| Success Rate | Execuções OK / Total | ≥ 95% |
| SLA Compliance | Respostas dentro do tempo / Total | ≥ 90% |
| Response Time | P95 de tempo de resposta | ≤ 10s (Sync), ≤ 30s (Async) |

**Activity Feed:** Cada ação de agente é registrada em `AgentActivity` com tipo, resultado, duração e contexto. Alimenta o "Recruiter Control Center" no frontend.

**Alertas Proativos:**
- Health score < 70 → Alerta WARNING
- Health score < 50 → Alerta CRITICAL
- 3+ falhas consecutivas → Notificação ao admin
- Circuit breaker OPEN → Alerta imediato

### 17.4 Dashboards de Observabilidade

**Dashboard de Agentes (Admin):**

| Painel | Métricas | Refresh |
|--------|----------|---------|
| Agent Health Overview | Health score por agente (heatmap 16 agentes) | 30s |
| Request Volume | `llm_requests_total` por provedor e modelo | 10s |
| Latência | `llm_latency_seconds` P50/P95/P99 por agente | 10s |
| Erros | `agent_tool_failures_total` por tipo | 10s |
| Router | `router_tier_hit_total` distribuição por tier | 30s |
| Circuit Breakers | `circuit_breaker_state` por serviço | 5s |
| Tokens | `token_budget_remaining` por tenant | 60s |
| Pipeline | `pipeline_transitions_total` por etapa | 60s |
| Fairness | `fairness_blocks_total` por categoria | 60s |

**Dashboard de Compliance (DPO):**

| Painel | Dados | Refresh |
|--------|-------|---------|
| Consentimentos | Taxa de consentimento por tipo | Diário |
| DSR Requests | Volume e status de requisições de titulares | 60s |
| Bias Audit | Último resultado por vaga (Four-Fifths) | Diário |
| HITL Queue | Ações pendentes de revisão humana | 30s |
| Breaches | Incidentes abertos e prazos ANPD | 60s |
| PII Masking | Taxa de masking (logs vs produção) | Diário |

**Dashboard Recrutador (Recruiter Control Center):**

| Painel | Dados | Refresh |
|--------|-------|---------|
| Activity Feed | Últimas 20 ações da LIA | Real-time (WS) |
| Pending Actions | Ações HITL aguardando aprovação | Real-time (WS) |
| Pipeline Overview | Contagem por etapa, SLA status | 30s |
| Smart Alerts | Alertas proativos (SLA, saturação, etc.) | 60s |
| Token Usage | Consumo de IA do dia/mês | 60s |

### 17.5 Alerting Rules

**Regras de alerta configuradas:**

| # | Regra | Condição | Severidade | Canal |
|---|-------|----------|------------|-------|
| 1 | LLM Latency High | P95 > 10s por 5 min | Warning | Teams |
| 2 | LLM Error Rate | > 5% em 15 min | Critical | Teams + Bell |
| 3 | Circuit Breaker Open | Qualquer circuit OPEN | Critical | Teams + Bell |
| 4 | Token Budget Critical | > 90% consumido | Warning | Bell |
| 5 | Token Budget Exhausted | 100% consumido | Critical | Bell + Email |
| 6 | Agent Health Low | Health < 50 por 10 min | Critical | Teams |
| 7 | HITL Queue Stale | Ação pendente > 24h | Warning | Bell + Email |
| 8 | Fairness Block Spike | > 3x baseline em 1h | Warning | Teams |
| 9 | WS Connection Drop | > 10 drops em 5 min | Warning | Teams |
| 10 | Model Drift Detected | 2+ métricas fora threshold | Warning | Teams + Email |

### 17.6 Métricas Prometheus Completas — D1

**Arquivo:** `app/observability/metrics.py`

O arquivo atual registra **17 métricas Prometheus** (não 14 como listado em 17.1). Métricas adicionais adicionadas em Y1–Y5:

**Counters adicionais (Y1–Y5):**

| Métrica | Labels | Descrição |
|---------|--------|-----------|
| `lia_router_tier_hit_total` | `tier` | Hits por tier do CascadedRouter (memory/redis_hash/vector/fast_router/llm_cascade/clarification) |
| `lia_agent_llm_tokens_total` | `domain`, `provider` | Total de tokens LLM consumidos por agente |
| `lia_agent_errors_total` | `domain`, `error_type` | Total de erros por agente e tipo |
| `lia_llm_cost_usd_total` | `model`, `domain` | Custo estimado em USD de chamadas LLM |

**Histograms adicionais (Y1–Y5):**

| Métrica | Labels | Descrição |
|---------|--------|-----------|
| `lia_router_latency_ms` | `tier` | Latência do roteamento por tier em ms |
| `lia_router_confidence` | `model` | Distribuição de confiança do roteador por modelo |
| `lia_agent_request_duration_seconds` | `domain`, `agent_class` | Duração das requests por agente (P50/P95/P99) |

**Funções de exportação:** `generate_latest_metrics()` retorna bytes no formato Prometheus text. Constante `PROMETHEUS_CONTENT_TYPE` para o header HTTP correto.

### 17.7 PII Masking em Logs — D4

**Arquivo:** `app/shared/pii_masking.py` — classe `PIIMaskingFilter`
**Wiring:** `app/core/logging_config.py` — instalado como filter no root logger

Filter de logging que mascara automaticamente PII antes de gravar em qualquer destino de log:
- Intercepta todos os records antes de escrita (logging.Filter)
- Mascara: CPF, RG, email, telefone, endereço, nome completo quando identificável
- Previne vazamento acidental em logs de aplicação, APM, CloudWatch, ELK

**Workers Celery:** Instalado via `@signals.worker_process_init.connect` em `libs/config/lia_config/celery_app.py` — cada processo filho (prefork) instala o masking automaticamente ao inicializar (SEG-3A).

**Função auxiliar:** `strip_pii_for_llm_prompt(text)` — Layer 1 (CPF/email/telefone/RG/CNPJ) + Layer 3 basic (quasi-identifiers: ano de formatura, idade explícita, endereço). Flag `LLM_PROMPT_PII_STRIPPING_ENABLED` (padrão: true). Aplicado em 6+ callers LLM críticos (SEG-3B, SEG-GAPS).

### 17.8 OpenTelemetry — Rastreamento Distribuído (Z6-02)

**Arquivo:** `app/shared/tracing.py`

Suporte a rastreamento distribuído via OpenTelemetry com exportação OTLP e fallback gracioso para `LightweightTracer` interno quando Jaeger/Tempo não está disponível.

**Settings adicionadas:**

| Variável de Ambiente | Default | Descrição |
|---------------------|---------|-----------|
| `OTEL_SERVICE_NAME` | `lia-agent-system` | Nome do serviço nos traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | (vazio) | Endpoint OTLP (ex: `http://jaeger:4317`) |
| `OTEL_TRACES_ENABLED` | `false` | Liga/desliga exportação OTLP |

**`@trace_span` aplicado em:**
- `CascadedRouter.route()` — rastreia tempo de roteamento por tier
- `DLQService.push_failure()` — rastreia falhas enviadas ao DLQ
- `LearningLoopService.process_unprocessed_feedback()` — rastreia ciclos de aprendizado

**Novos endpoints REST:**

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/v1/traces` | Lista traces recentes do LightweightTracer |
| `GET /api/v1/traces/stats` | Estatísticas de rastreamento (total, por serviço, latências) |
| `GET /api/v1/traces/status` | Status do exporter OTLP (enabled/disabled, endpoint configurado) |

---

## 18. Resiliência e Circuit Breakers

### 18.1 Arquitetura de Circuit Breaker

**Arquivo:** `lia-agent-system/app/shared/resilience/circuit_breaker.py` (682 linhas)

O sistema implementa o padrão Circuit Breaker para proteger chamadas a APIs externas, prevenindo falhas em cascata quando serviços ficam indisponíveis.

**3 Estados do Circuit Breaker:**

```
┌─────────┐    failure_count ≥ threshold    ┌──────┐
│ CLOSED  │ ──────────────────────────────→ │ OPEN │
│(Normal) │                                 │(Blk) │
└─────────┘                                 └──┬───┘
     ↑                                         │
     │ half_open_calls ≥ max_calls              │ recovery_timeout expirado
     │ (todos sucesso)                          ↓
     │                                    ┌───────────┐
     └────────────────────────────────── │ HALF_OPEN │
           recuperação confirmada         │ (Teste)   │
                                          └───────────┘
```

**Configuração padrão (`CircuitBreakerConfig`):**

| Parâmetro             | Valor Padrão | Descrição                                    |
|-----------------------|-------------|----------------------------------------------|
| `failure_threshold`   | 5           | Falhas consecutivas para abrir o circuit     |
| `recovery_timeout`    | 30.0s       | Tempo antes de tentar recovery (HALF_OPEN)   |
| `success_threshold`   | 2           | Sucessos em HALF_OPEN para fechar circuit    |
| `timeout`             | 10.0s       | Timeout de cada request individual           |
| `exclude_exceptions`  | ()          | Exceções que não contam como falha           |

### 18.2 Circuits Registrados

Os circuit breakers são criados dinamicamente via decorator `@circuit_breaker()` ou instanciação direta de `CircuitBreaker`. O sistema utiliza um dicionário `_circuits: Dict[str, CircuitBreakerState]` como registry lazy — circuits são criados no primeiro uso via `_get_circuit()`.

**Serviços protegidos identificados no codebase:**

| Circuit Name     | Serviço Protegido                | Arquivo que consome                                      |
|------------------|----------------------------------|----------------------------------------------------------|
| `anthropic`      | API Claude (Anthropic)           | Chamadas LLM dos 12 agentes ReAct                       |
| `openai`         | API OpenAI (GPT-4o, GPT-4-turbo)| Fallback LLM, embeddings                                |
| `gemini`         | API Google Gemini                | Modelo alternativo para scoring                          |
| `pearch`         | Pearch AI (busca candidatos)     | `app/domains/sourcing/tools/query_tools.py`              |
| `workos`         | WorkOS (SSO/SCIM)                | `app/auth/` (autenticação enterprise)                    |
| `merge`          | Merge API (ATS unificado)        | `app/domains/ats_integration/`                           |
| `google_calendar`| Google Calendar API              | `app/domains/interview_scheduling/`                      |
| `gupy`           | ATS Gupy (integração)            | `app/services/ats_clients/gupy.py` *(canônico — Z6-01)* |
| `pandape`        | ATS Pandapé (integração)         | `app/services/ats_clients/pandape.py` *(canônico — Z6-01)* |
| `stackone`       | StackOne (ATS unificado)         | `app/services/ats_clients/stackone.py` *(canônico — Z6-01)* |
| `sendgrid`       | SendGrid (email transacional)    | `app/services/email_service.py`                          |
| `resend`         | Resend (email fallback)          | `app/services/email_service.py`                          |

### 18.3 Notificação de Abertura de Circuit

Quando um circuit breaker transiciona para OPEN, o sistema envia notificação automática:

**Arquivo:** `circuit_breaker.py` → `_notify_circuit_open()`

**Mecanismo:**
1. **Redis dedup:** chave `cb_alert:{service_name}` com TTL 1 hora — evita flood de alertas
2. **Canais:** Bell (notificação in-app) + Teams (Microsoft Teams)
3. **Mensagem:** "O circuit breaker para '{service_name}' foi aberto após múltiplas falhas. Chamadas estão sendo rejeitadas automaticamente. O circuit tentará recuperação em 30s."
4. **Non-blocking:** execução via `loop.create_task()` — nunca bloqueia o request principal

### 18.4 Implementação Dual

O arquivo `circuit_breaker.py` contém **duas implementações**:

1. **Classe `CircuitBreaker`** (linhas 117-340) — Implementação orientada a objetos com lock asyncio, estatísticas detalhadas (`CircuitBreakerStats`), e classe registry `ALL_CIRCUITS`. Usada para instanciação direta.

2. **Decorator `circuit_breaker()`** (linhas 626-655) — Implementação funcional via `_circuits` dict com `CircuitBreakerState` dataclass. Usado como decorator em funções async.

**APIs de diagnóstico:**
- `get_circuit_status(service_name)` — status de um circuit específico
- `get_all_circuits_status()` — status de todos os circuits registrados
- `reset_circuit(service_name)` — reset manual para CLOSED
- `reset_all_circuits()` — reset de todos os circuits

**Métricas Prometheus:** `circuit_breaker_state` gauge (0=closed, 1=half_open, 2=open) exportada quando módulo de observabilidade está disponível.

### 18.5 Fallback Strategy

Quando o circuit está OPEN, o sistema suporta fallbacks configuráveis:

```python
@circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=60, fallback=my_fallback_fn)
async def call_anthropic(prompt: str) -> str:
    ...
```

- Se `fallback` é definido e circuit está OPEN → executa fallback em vez de lançar exceção
- Se `fallback` não é definido → lança `CircuitBreakerError(name, retry_after)`
- O Orchestrator captura `CircuitBreakerError` e retorna mensagem amigável ao usuário

### 18.6 Dead Letter Queue — DLQService (F2-04)

**Arquivo:** `app/shared/resilience/dlq_service.py`

Serviço de Dead Letter Queue para tasks Celery que falharam definitivamente (esgotaram todas as retentativas). Garante que falhas críticas não sejam silenciadas e possam ser inspecionadas, reprocessadas ou descartadas manualmente.

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `push_failure(queue, task_name, kwargs, error, traceback)` | Empurra falha para o DLQ; PII masking automático em kwargs antes de persistir |
| `list_entries(queue)` | Lista entradas de uma fila DLQ específica |
| `list_queues()` | Lista todas as filas DLQ ativas |
| `queue_size(queue)` | Retorna tamanho de uma fila |
| `requeue(queue, entry_id)` | Reenvia task para processamento normal |
| `clear(queue)` | Limpa todos os itens de uma fila |
| `summary()` | Retorna sumário de todas as filas (tamanhos, tasks mais antigas) |

**Implementação:**
- Armazenamento: Redis LIST+SET; cap de 1.000 entradas por fila; TTL 7 dias
- PII masking: campos `password`, `token`, `cpf`, `email`, `key` são mascarados antes de gravar
- `@trace_span` integrado — cada push é rastreado via OpenTelemetry
- Notificação Bell automática para tasks críticas: `lgpd`, `audit`, `drift`, `followup`, `wsi`

**LIATask — Base Class Celery:**

`LIATask` é a base class de tasks Celery em `libs/config/lia_config/celery_app.py`. Override de `on_failure()` garante que toda task com falha definitiva seja automaticamente registrada no DLQ (fail-safe — erros no próprio push não propagam).

**Endpoints Admin:**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/admin/dlq` | GET | Sumário de todas as filas DLQ |
| `/admin/dlq/{queue}` | GET | Lista entradas de uma fila específica |
| `/admin/dlq/{queue}` | DELETE | Limpa fila (requer admin) |
| `/admin/dlq/{queue}/requeue/{entry_id}` | POST | Reenvia task para reprocessamento |

### 18.7 Circuits Adicionados em Sprints AUD-2 e Y1 — D10

A tabela em 18.2 já reflete os circuits de AUD-2. O circuit `PEARCH_CIRCUIT` foi adicionado especificamente em Y1/D10:

| Circuit | Serviço | Arquivo Principal | Sprint |
|---------|---------|-------------------|--------|
| `PEARCH_CIRCUIT` | Pearch AI (busca de candidatos) | `app/services/pearch_service.py` (re-exports de `app/domains/sourcing/services/pearch_service.py`) | Y1/D10 |
| `OPENAI_CIRCUIT` | API OpenAI | `app/shared/providers/llm_openai.py` (4 métodos) | AUD-2 |
| `GEMINI_CIRCUIT` | API Google Gemini | `app/shared/providers/llm_gemini.py` (4 métodos) | AUD-2 |
| `GUPY_CIRCUIT` | Gupy ATS | `app/services/ats_clients/gupy.py` *(canônico — Z6-01; shim em `app/domains/ats_integration/services/ats_clients/gupy.py`)* | AUD-2 |
| `PANDAPE_CIRCUIT` | PandaPé ATS | `app/services/ats_clients/pandape.py` *(canônico — Z6-01)* | AUD-2 |
| `STACKONE_CIRCUIT` | StackOne ATS | `app/services/ats_clients/stackone.py` *(canônico — Z6-01)* | AUD-2 |
| `SENDGRID_CIRCUIT` | SendGrid email | `app/services/email_providers/sendgrid.py` | AUD-2 |
| `RESEND_CIRCUIT` | Resend email | `app/services/email_providers/resend.py` | AUD-2 |
| `WORKOS_CIRCUIT` | WorkOS SSO | `app/api/v1/workos.py` via `_fetch_workos_metrics()` helper | AUD-2 |

**Nota sobre Pearch (D10):** O serviço Pearch tem estratégia de fallback para busca interna quando o circuit está OPEN, garantindo que o Sourcing Agent continue operacional mesmo sem acesso à base externa de 190M+ perfis.

### 18.8 RecruiterBehaviorService — Perfis de Comportamento (Z7-01)

**Arquivo:** `app/services/recruiter_behavior_service.py`

Serviço que computa e persiste perfis de comportamento individualizados por recrutador, alimentando personalização da LIA e insights gerenciais.

**Métricas computadas:**

| Métrica | Descrição |
|---------|-----------|
| `active_hours` | Horários de maior atividade (janelas de 1h) |
| `sourcing_channels` | Canais preferidos de sourcing (Pearch, LinkedIn, indicação, etc.) |
| `stage_conversion_rates` | Taxa de conversão por etapa do funil por recrutador |
| `communication_style` | Estilo predominante de comunicação (formal, casual, objetivo) |

**Implementação:**
- Redis signals: TTL 24h, cap de 500 sinais por recrutador (comprimidos — JSON + gzip)
- Chave Redis: `lia:recruiter_behavior:{recruiter_id}:signals`
- Computed on-demand ou via invalidação manual

**Endpoints:**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/recruiters/{id}/behavior-profile` | GET | Retorna perfil computado do recrutador |
| `/api/v1/recruiters/{id}/behavior-signal` | POST | Registra novo sinal de comportamento |
| `/api/v1/recruiters/{id}/behavior-invalidate` | DELETE | Invalida cache e força recomputação |

---

## 19. Gestão de Custos e Token Tracking

### 19.1 TokenTrackingService

**Arquivo:** `lia-agent-system/app/services/token_tracking_service.py` (722 linhas)

Serviço de monitoramento em tempo real de uso de tokens LLM com estimativa de custos e enforcement de limites por usuário e empresa.

### 19.2 Modelos e Preços Suportados

**Dicionário `TOKEN_PRICES` — 10 modelos com preços por 1K tokens (USD):**

| Modelo              | Input ($/1K) | Output ($/1K) | Uso na Plataforma                    |
|---------------------|-------------|---------------|--------------------------------------|
| `claude-3-sonnet`   | $0.003      | $0.015        | Modelo principal dos 12 agentes ReAct |
| `claude-3-haiku`    | $0.00025    | $0.00125      | Tier 5 LLM Cascade (roteamento)      |
| `claude-3-opus`     | $0.015      | $0.075        | Tier 5 LLM Cascade (fallback final)  |
| `claude-3.5-sonnet` | $0.003      | $0.015        | Avaliação WSI, JD enriquecida        |
| `gpt-4o`            | $0.005      | $0.015        | Alternativa OpenAI (quando config.)  |
| `gpt-4o-mini`       | $0.00015    | $0.0006       | Tarefas leves (classificação)        |
| `gpt-4-turbo`       | $0.01       | $0.03         | Análises complexas (quando config.)  |
| `gpt-3.5-turbo`     | $0.0005     | $0.0015       | Embeddings, classificação rápida     |
| `gemini-1.5-pro`    | $0.00125    | $0.005        | Alternativa Google (quando config.)  |
| `gemini-1.5-flash`  | $0.000075   | $0.0003       | Tarefas rápidas/baratas              |

### 19.3 Limites Padrão (DEFAULT_LIMITS)

| Limite                          | Valor Padrão    | Escopo           |
|---------------------------------|-----------------|------------------|
| `daily_tokens_per_user`         | 500.000         | Por usuário/dia  |
| `daily_tokens_per_company`      | 5.000.000       | Por empresa/dia  |
| `monthly_cost_per_company`      | $500.00         | Por empresa/mês  |
| `hourly_tokens_per_user`        | 100.000         | Por usuário/hora |
| `requests_per_minute_per_user`  | 60              | Por usuário/min  |

**Limites customizáveis:** `set_custom_limits(company_id, limits)` permite override por empresa. O merge é aditivo — limites não especificados usam DEFAULT_LIMITS.

### 19.4 Alertas de Consumo

**Thresholds de alerta:** `ALERT_THRESHOLDS = [80, 100]`

- Ao atingir 80% do limite → alerta de aviso (warning)
- Ao atingir 100% do limite → alerta de bloqueio (block) + request rejeitado

### 19.5 Funcionalidades

| Método                    | Descrição                                              |
|---------------------------|--------------------------------------------------------|
| `record_usage()`          | Registra uso de tokens por operação na tabela `ai_consumption` |
| `get_usage_summary()`     | Resumo de uso por período (dia/mês)                    |
| `check_limits()`          | Verifica se usuário/empresa está dentro dos limites    |
| `get_cost_estimate()`     | Calcula custo estimado baseado no modelo e tokens      |
| `_calculate_cost_cents()` | Calcula custo em centavos usando `TOKEN_PRICES`        |

### 19.6 Retenção de Logs

**Constante:** `AI_LOG_RETENTION_DAYS` (definido em `app/models/ai_consumption.py`)

Logs de consumo de IA são marcados com `scheduled_deletion_at` para limpeza automática pelo `lgpd_cleanup_service.py` após o período de retenção (365 dias por padrão para `ai_logs`).

---

## 20. ConfidencePolicyService — Autonomia de Ações

### 20.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/confidence_policy_service.py`

O ConfidencePolicyService determina se a LIA pode executar uma ação autonomamente, notificar o recrutador, ou pedir confirmação. Funciona como gate entre a decisão do agente e a execução real da ação.

### 20.2 Níveis de Confiança

O serviço define 3 níveis de ação baseados na confiança calculada:

| Nível             | Threshold         | Comportamento                                                 |
|-------------------|--------------------|---------------------------------------------------------------|
| `APPLY_SILENT`    | confidence ≥ 0.85 | LIA executa a ação automaticamente sem notificar o recrutador |
| `APPLY_NOTIFY`    | confidence ≥ 0.70 | LIA executa a ação e notifica o recrutador sobre o que foi feito |
| `ASK_USER`        | confidence < 0.70 | LIA apresenta a proposta e aguarda confirmação do recrutador  |

### 20.3 Cálculo de Confiança por Fonte

O serviço mantém um dicionário de confiança base por fonte de dados:

```python
SOURCE_BASE_CONFIDENCES = {
    "cv_parsing": 0.75,
    "wsi_evaluation": 0.80,
    "rubric_evaluation": 0.85,
    "manual_input": 0.95,
    "pearch_api": 0.70,
    "linkedin_scraping": 0.65,
}
```

### 20.4 Modificadores de Confiança

| Modificador                | Valor    | Condição                                            |
|----------------------------|----------|------------------------------------------------------|
| `MULTI_SOURCE_AGREE_BONUS` | +0.10    | Quando 2+ fontes concordam no mesmo resultado        |
| `DISAGREE_PENALTY`         | -0.30    | Quando fontes divergem significativamente             |

**Fórmula:** `confidence_final = base_confidence + bonuses - penalties`

### 20.5 Integração com Fluxo HITL

```
Agente propõe ação
     │
     ▼
ConfidencePolicyService.evaluate(action, sources, confidence)
     │
     ├── ≥ 0.85 → APPLY_SILENT → ActionExecutor.execute()
     │
     ├── ≥ 0.70 → APPLY_NOTIFY → ActionExecutor.execute() + Notification
     │
     └── < 0.70 → ASK_USER → PendingActionStore.store() → HITL flow
```

### 20.6 Exemplos Práticos de Decisão de Confiança

**Cenário 1: Movimentação após WSI (APPLY_SILENT)**
```
Fonte: wsi_evaluation (0.80) + rubric_evaluation (0.85) → base = 0.825
Modificador: MULTI_SOURCE_AGREE_BONUS (+0.10) — ambas fontes recomendam aprovação
Confidence final: 0.925 → APPLY_SILENT
Ação: move_candidate("João Silva", "Entrevista Técnica") executada automaticamente
```

**Cenário 2: Rejeição baseada apenas em CV parsing (ASK_USER)**
```
Fonte: cv_parsing (0.75)
Modificador: nenhum (fonte única)
Confidence final: 0.75 → acima de 0.70 mas ação é "reject_candidate"
Override: Ações irreversíveis (reject, delete) sempre exigem ASK_USER independente do score
Ação: PendingActionStore.store() → modal de confirmação para recrutador
```

**Cenário 3: Fontes divergentes (ASK_USER)**
```
Fonte: wsi_evaluation (0.80) sugere aprovação + cv_parsing (0.75) sugere rejeição
Modificador: DISAGREE_PENALTY (-0.30)
Confidence final: 0.775 - 0.30 = 0.475 → ASK_USER
Ação: LIA apresenta ambas perspectivas + solicita decisão do recrutador
```

### 20.7 Ações com Override de Segurança

Algumas ações possuem regras de override que ignoram o score de confiança:

| Ação | Override | Motivo |
|------|----------|--------|
| `reject_candidate` | Sempre ASK_USER | Decisão adversa — EU AI Act Art. 14 |
| `close_job` | Sempre ASK_USER | Irreversível — impacta pipeline completo |
| `send_bulk_email` | Sempre ASK_USER | Alto impacto — comunicação em massa |
| `finalize_hiring` | Sempre ASK_USER | Decisão final — requer aprovação gerencial |
| `move_candidate` | Normal (score-based) | Reversível — pode ser desfeita |
| `schedule_interview` | Normal (score-based) | Reversível — pode ser cancelada |
| `analyze_profile` | Sempre APPLY_SILENT | Somente leitura — sem side effects |
| `duplicate_job` | Normal (score-based) | Reversível — cópia pode ser deletada |

---

## 21. Governança de Agentes

### 21.1 EnhancedAgentMixin — Ciclo de Vida de 5 Etapas

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` (301 linhas)

Todos os 12 agentes ReAct herdam de `EnhancedAgentMixin`, que adiciona memória, autonomia e aprendizado ao ciclo ReAct padrão.

**Ciclo de vida de 5 etapas:**

```
1. _setup_enhanced(domain)
   ├── Inicializa WorkingMemoryService (memória de curto prazo)
   ├── Inicializa LongTermMemoryService (memória de longo prazo)
   ├── Inicializa MemoryIntegration (ponte entre WM e LTM)
   ├── Inicializa AutonomyEngine (políticas de autonomia)
   └── Inicializa LearningExtractor (extração de aprendizados)

2. _get_memory_context(session_id, company_id)
   └── MemoryIntegration.get_enriched_context()
       → Injeta memórias relevantes no system prompt antes do ReAct loop

3. _resolve_guardrails(company_id)
   ├── 1. AutonomyEngine.resolve_guardrails() (política da empresa)
   ├── 2. Fallback: GuardrailRepository.get_blocked_tools() (banco de dados)
   └── 3. Último recurso: lista estática DEFAULT_GUARDRAIL_TOOLS

4. ReAct Loop (Thought → Action → Observation → ...)
   └── Tools = base_tools + insight_tools + proactive_tools + predictive_tools

5. _post_loop_learning(state, company_id, session_id)
   └── LearningExtractor.extract_and_save()
       → Salva aprendizados na LongTermMemoryService
```

### 21.2 AutonomyEngine — 3 Níveis de Autonomia

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/autonomy_engine.py`

O AutonomyEngine determina o nível de autonomia da LIA por empresa, controlando quais ações requerem confirmação humana.

**3 Níveis:**

| Nível           | Descrição                                                | Ações que requerem HITL                   |
|-----------------|----------------------------------------------------------|-------------------------------------------|
| `CONSERVATIVE`  | Todas as ações destrutivas requerem confirmação          | move, reject, delete, send, bulk_update   |
| `BALANCED`      | Ações de leitura e comunicação são autônomas             | reject, delete, bulk_update, finalize     |
| `AUTONOMOUS`    | Apenas ações irreversíveis requerem confirmação          | delete, finalize_hiring                   |

**Guardrails por nível (`GUARDRAILS_BY_LEVEL`):**
- `CONSERVATIVE`: `["move_candidate", "batch_move", "finalize_hiring", "delete_job", "reject_candidate", "send_bulk_email", "update_candidate_field"]`
- `BALANCED`: `["finalize_hiring", "delete_job", "reject_candidate", "send_bulk_email"]`
- `AUTONOMOUS`: `["finalize_hiring", "delete_job"]`

### 21.3 Guardrails Estáticos (Fallback)

**Arquivo:** `enhanced_agent_mixin.py` → `_resolve_guardrails()`

Se tanto o AutonomyEngine quanto o GuardrailRepository falharem, o sistema usa uma lista estática como último recurso:

```python
_DEFAULT_GUARDRAIL_TOOLS = [
    "move_candidate",
    "batch_move",
    "finalize_hiring",
    "delete_job",
    "reject_candidate",
    "send_bulk_email",
    "update_candidate_field",
]
```

**Estratégia de fallback em 3 camadas:**
1. AutonomyEngine (política da empresa via `CompanyHiringPolicy`)
2. GuardrailRepository (banco de dados via `AsyncSessionLocal`)
3. Lista estática (hardcoded — modo mais restritivo)

### 21.4 Ferramentas Compartilhadas Aprimoradas

O `EnhancedAgentMixin` injeta 3 categorias de ferramentas compartilhadas em todos os agentes:

| Categoria          | Arquivo                                     | Ferramentas incluídas                           |
|--------------------|---------------------------------------------|--------------------------------------------------|
| Insight Tools      | `app/shared/tools/insight_tools.py`         | Análise histórica, tendências, padrões           |
| Proactive Tools    | `app/shared/tools/proactive_tools.py`       | Detecção de riscos, alertas proativos            |
| Predictive Tools   | `app/shared/tools/predictive_tools.py`      | Previsões, recomendações, forecasting            |

### 21.5 Anti-Sycophancy

Todos os 16 agentes incluem regra anti-sycophancy no system prompt:

- **Bloco compartilhado:** `ANTI_SYCOPHANCY_OPERATIONAL` (importado de módulo comum)
- **Regra:** "Nunca confirme pedidos discriminatórios ou que violem compliance. Apresente alternativas com dados quando necessário."
- **Enforcement:** Via FairnessGuard (pré-processamento) + regra no prompt (em runtime)
- **Limitação:** Sem guardrail automatizado em runtime para validar resposta final — depende do LLM seguir a instrução

---

## 22. FairnessGuard — 3 Camadas de Proteção Anti-Viés

### 22.1 Visão Geral

**Arquivo:** `lia-agent-system/app/shared/compliance/fairness_guard.py` (506 linhas) — `_PATTERNS_VERSION = 2`

O FairnessGuard é um middleware que intercepta queries antes do processamento pelos agentes, verificando indicadores de viés discriminatório. Quando detectado, retorna uma mensagem educativa em vez de processar a query. **Sprint X1 (15/03/2026):** expandido de 42→62 termos explícitos; todos os 14 xfails de red teaming eliminados.

### 22.2 Camada 1 — Filtro Regex (Viés Explícito)

**9 categorias discriminatórias com patterns regex compilados — `_PATTERNS_VERSION=2` (Sprint X1):**

| Categoria                | Termos   | Legislação Referenciada                    | Novos em v2                            |
|--------------------------|----------|---------------------------------------------|----------------------------------------|
| `genero`                 | **8**    | Art. 5º CLT, LGPD                          | +2 (gênero implícito: "trabalho de homem") |
| `raca_etnia`             | **8**    | CF Art. 5º, Lei 7.716/89                   | +4 (etnia implícita, aparência racial) |
| `idade`                  | **13**   | Estatuto do Idoso, CLT                     | +4 (idade implícita: "recém-formado", "nativo digital") |
| `religiao`               | 3        | CF Art. 5º VI                              | —                                      |
| `orientacao_sexual`      | 3        | STF ADO 26                                 | —                                      |
| `estado_civil`           | 3        | CLT                                        | —                                      |
| `deficiencia`            | **8**    | Lei 8.213/91, Lei 13.146/15               | +4 (deficiência implícita: "ritmo normal", "mobilidade plena") |
| `maternidade_paternidade`| **13**   | CLT Art. 373-A, Lei 9.029/95              | +6 (termos indiretos sobre família/filhos) |
| `nacionalidade`          | 3        | CF Art. 5º                                 | —                                      |

**Total: 62 termos explícitos** distribuídos em 9 categorias (era 42 em v1). `HIGH_IMPACT_ACTIONS = {"rejection", "shortlist", "wsi_score", "policy_save", "bulk_rejection"}` — 5 ações críticas com verificação obrigatória.

**Cada categoria inclui:**
- `terms[]` — lista de patterns regex (compilados e cacheados em `_COMPILED_PATTERNS`)
- `message` — mensagem educativa personalizada com referência legal

### 22.3 Camada 2 — Léxico Implícito (Viés Sutil)

**Dicionário `IMPLICIT_BIAS_TERMS` — 11 termos com mensagens educativas:**

| Termo Detectado                      | Tipo de Viés                    | Mensagem (resumida)                                     |
|--------------------------------------|----------------------------------|---------------------------------------------------------|
| `boa aparencia`                      | Discriminação estética           | "Use critérios objetivos de apresentação profissional"  |
| `bairros nobres`                     | Discriminação socioeconômica     | "Considere critérios de disponibilidade ou mobilidade"  |
| `regiao nobre`                       | Discriminação socioeconômica     | "Considere critérios de disponibilidade ou mobilidade"  |
| `universidades de primeira linha`    | Elitismo acadêmico               | "Avalie competências e resultados"                      |
| `faculdade de ponta`                 | Elitismo acadêmico               | "Avalie competências e resultados"                      |
| `escola particular`                  | Discriminação socioeconômica     | "Avalie formação e competências"                        |
| `clube social`                       | Discriminação de classe          | "Pode configurar discriminação socioeconômica"          |
| `perfil adequado`                    | Viés inconsciente                | "Especifique competências objetivas"                    |
| `apresentacao pessoal`               | Discriminação estética           | "Use critérios objetivos"                               |
| `morar proximo`                      | Discriminação socioeconômica     | "Considere disponibilidade ou trabalho remoto"          |
| `boa familia`                        | Discriminação de origem          | "Use critérios profissionais"                           |

**Normalização:** `_normalize_text()` remove acentos via NFD para matching case-insensitive e accent-insensitive.

### 22.4 Camada 3 — LLM Judge (Opt-in)

**Ativação:** Variável de ambiente `FAIRNESS_LAYER3_ENABLED=true`
**Modelo:** Claude Sonnet
**Processo:** LLM revisa o output do agente antes de finalizar score
**Uso recomendado:** Clientes em segmentos regulados (financeiro, saúde)

### 22.5 FairnessCheckResult

**Dataclass de retorno:**

```python
@dataclass
class FairnessCheckResult:
    is_blocked: bool           # True se Camada 1 detectou viés explícito
    blocked_terms: List[str]   # Termos que causaram o bloqueio
    category: Optional[str]    # Categoria discriminatória (genero, idade, etc.)
    educational_message: str   # Mensagem educativa com base legal
    original_query: str        # Query original do recrutador
    confidence: float          # Confiança na detecção (0.0-1.0)
    soft_warnings: List[str]   # Avisos da Camada 2 (não bloqueantes)
```

### 22.6 Integração com Agentes

O FairnessGuard está integrado em **11/11 agentes ReAct + Orchestrator** (100% de cobertura desde Sprints SEG-2 e v3.0):

**Via `EnhancedAgentMixin` (`_fairness_pre_check`):**
- Wizard Agent, Talent Agent, Jobs Management Agent, Kanban Agent, Analytics Agent, Automation Agent, ATS Integration Agent, Communication Agent, Policy Agent

**Via chamada explícita (`guard.check()` + `check_implicit_bias()` + `log_check()`):**
- Sourcing Agent (`sourcing_react_agent.py`) — SEG-2: bloqueio + `educational_message` + fail-safe
- Pipeline Transition Agent (`pipeline_transition_agent.py`) — SEG-2: bloqueio + `educational_message` + fail-safe

**Via Orchestrator:**
- `main_orchestrator.py:L151` — FairnessGuard chamado no path principal de `process_request()`

**Ausente:** Interview Scheduling Graph (não é agente ReAct — sem interação de texto natural com recrutador)

**Camada 3 ativa em 3 callers de alto risco (v4.0 ACH-026):**
- `rubric_evaluation_service.py` → `check_with_layer3(action_type="wsi_score")`
- `candidate_feedback_service.py` → `check_with_layer3(action_type="rejection")`
- `sourcing_react_agent.py` output → `check_with_layer3(action_type="shortlist")`

### 22.7 Métricas

**Prometheus counter:** `fairness_blocks_total` — incrementado a cada bloqueio por categoria.
Exportada quando módulo de observabilidade está disponível (`_METRICS_AVAILABLE`).

---

## 23. Pre-Qualification Pipeline

### 23.1 PreQualificationService

**Arquivo:** `lia-agent-system/app/services/pre_qualification_service.py`

Serviço que executa triagem automática de candidatos antes da avaliação WSI completa, filtrando candidatos que não atendem requisitos mínimos.

**Critérios de pré-qualificação:**
- Requisitos obrigatórios da vaga (skills, experiência mínima, localização)
- Disponibilidade do candidato
- Match mínimo com a descrição da vaga

### 23.2 ScoreNormalizationService

**Arquivo:** `lia-agent-system/app/services/score_normalization_service.py`

Normaliza scores entre diferentes avaliadores e vagas para garantir comparabilidade:

**Fator de normalização:** `0.7 ≤ factor ≤ 1.3`
- Calculado como: `factor = max(0.7, min(1.3, raw_factor))`
- Previne que normalização distorça scores excessivamente
- Aplica-se a scores WSI e rubric para cada avaliador/vaga

### 23.3 Fluxo Completo de Pre-Qualification

```
Candidato aplica para vaga
         ↓
[Pre-Qualification Gate]
├── 1. Verificação de requisitos obrigatórios (skills, experiência, localização)
│      └── Se falha → Rejeição automática + feedback "encouraging"
├── 2. Match score mínimo (LIA Score ≥ threshold da política)
│      └── Se falha → Fila de review manual (HITL)
├── 3. Verificação de duplicata (mesmo candidato, mesma vaga)
│      └── Se duplicata → Notificação ao recrutador
└── 4. Consent check (LGPD Art. 7)
       └── Se sem consentimento → Solicita consentimento antes de processar
         ↓
[Candidato qualificado]
         ↓
Encaminhado para WSI ou etapa seguinte
```

**Threshold configurável por política:** Cada empresa pode definir o score mínimo de pre-qualification no `CompanyHiringPolicy`. Default: 40/100.

**Métricas geradas:**
- Taxa de pre-qualification (candidatos qualificados / total de aplicações)
- Motivos de rejeição mais comuns
- Tempo médio de pre-qualification (< 5s, sem LLM)

---

## 24. Personalized Feedback Service

### 24.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/personalized_feedback_service.py`

Gera feedback personalizado para candidatos rejeitados, adaptando tom e conteúdo ao contexto. O feedback é gerado via LLM (Claude) com base nos resultados de avaliação e no perfil do candidato.

### 24.2 3 Tons de Feedback

| Tom | Quando usado | Estilo |
|-----|--------------|--------|
| `encouraging` | Candidato com potencial, vaga muito sênior | Destaca pontos fortes, sugere áreas de desenvolvimento |
| `professional` | Rejeição padrão por fit ou skills | Objetivo, claro, com pontos positivos e gaps |
| `constructive` | Candidato com gaps significativos | Foco em ações concretas de melhoria com recursos sugeridos |

### 24.3 Seleção Automática de Tom

A seleção do tom é automática baseada em:
1. **Score WSI do candidato:** ≥ 70 → `encouraging`, 40-69 → `professional`, < 40 → `constructive`
2. **Distância para o threshold:** Se score está a ≤ 10 pontos do threshold → `encouraging`
3. **Override do recrutador:** Recrutador pode selecionar tom manualmente

### 24.4 Conteúdo do Feedback

O feedback personalizado inclui:
- Agradecimento pela participação no processo
- Pontos fortes identificados na avaliação
- Áreas de desenvolvimento (sem expor informações discriminatórias)
- Sugestões de próximos passos (cursos, certificações, etc.)
- Convite para futuras oportunidades

### 24.4 Compliance

- Feedback **nunca** inclui menção a categorias protegidas (FairnessGuard)
- PII masking aplicado antes de enviar ao LLM para geração
- Feedback registrado no audit trail para LGPD Art. 20

---

## 25. LGPD — Proteção de Dados Pessoais

### 25.1 Arquitetura LGPD

A plataforma implementa compliance LGPD em 6 pilares:

```
┌─────────────────────────────────────────────────────────────────┐
│                        LGPD COMPLIANCE                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│Consent   │ PII      │ DSR      │ Data     │ Breach   │ DPO      │
│Mgmt      │ Masking  │ Export   │ Cleanup  │ Notify   │ Registry │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│consent_  │pii_      │dsr_      │lgpd_     │lgpd_     │lgpd_     │
│checker   │masking   │export    │cleanup   │compliance│compliance│
│_service  │.py       │_service  │_service  │.py       │.py       │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 25.2 ConsentCheckerService — Gate de Consentimento

**Arquivo:** `lia-agent-system/app/services/consent_checker_service.py`

Checagem obrigatória antes de qualquer operação que processe dados pessoais:

**Modos de operação:**
- `soft_warning` (default): Log de aviso quando consentimento ausente, mas permite prosseguir
- `hard_block`: Bloqueia operação completamente quando consentimento ausente

**Controle:** Variável de ambiente `LGPD_CONSENT_ABSENT_HARD_BLOCK`

**Consentimentos verificados:**
- Gravação de voz (WSI)
- Processamento por IA
- Retenção de dados por 180 dias
- Compartilhamento com ferramentas de terceiros (Pearch, etc.)

### 25.3 PII Masking

**Arquivo:** `lia-agent-system/app/shared/pii_masking.py`

**3 componentes (Layer 1 + Layer 3 + Layer 4):**

1. **`strip_pii_for_llm_prompt(text)`** — Remove PII antes de enviar ao LLM:
   - **Layer 1:** CPF, RG, email, telefone, CNPJ (regex)
   - **Layer 3:** Quasi-identifiers: ano de formatura, idade explícita, endereço
   - **Layer 4 (opt-in via `LLM_PROMPT_PRESIDIO_ENABLED=true`):** NER via Microsoft Presidio — remove PERSON, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION. Graceful fallback se `presidio-analyzer` não instalado.
   - Flag principal: `LLM_PROMPT_PII_STRIPPING_ENABLED` (padrão: `true`)

2. **`PIIMaskingFilter`** — Filtro de logging instalado em todos os workers:
   - Intercepta logs antes de escrita
   - Mascara PII automaticamente
   - Previne vazamento acidental em logs de aplicação

3. **`_presidio_layer4_strip(text)`** (Z6-03) — Layer 4 NER via Presidio:
   - Importação lazy de `presidio_analyzer` (não bloqueia se não instalado)
   - Entidades reconhecidas: `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `LOCATION`
   - Substituição por `[REDACTED_<ENTITY_TYPE>]`
   - Ativado por `LLM_PROMPT_PRESIDIO_ENABLED=true` em `settings.py`

### 25.4 DSR Export Service — Portabilidade de Dados

**Arquivo:** `lia-agent-system/app/services/dsr_export_service.py`

Implementa LGPD Art. 18 V — Portabilidade de dados:

**Dados exportados:**
- Dados pessoais básicos (nome, email, telefone, localização, LinkedIn)
- Histórico de vagas e etapas (até 100 registros)
- Avaliações LIA (scores, recomendações, strengths, gaps — até 50 registros)
- Logs de consentimento LGPD
- Histórico de comunicações enviadas

**Dados NÃO exportados:**
- Dados de outros candidatos
- Dados internos de recrutadores
- Modelos proprietários LIA

**Formato:** JSON estruturado, legível por máquina e humano (`LIA DSR Export v1.0`)

**Endpoint:** `POST /api/v1/data-subject-requests` → tipo `portabilidade_dados`

### 25.5 LGPD Cleanup Service — Retenção de Dados

**Arquivo:** `lia-agent-system/app/services/lgpd_cleanup_service.py` (264 linhas)

**Política de retenção (`RETENTION_DAYS`):**

| Tipo de Dado           | Retenção | Ação após expiração                   |
|------------------------|----------|----------------------------------------|
| `rejected` candidates  | 90 dias  | Exclusão permanente (hard delete)      |
| `withdrawn` candidates | 90 dias  | Exclusão permanente (hard delete)      |
| `interview_notes`      | 180 dias | Exclusão permanente (hard delete)      |
| `screening_logs`       | 365 dias | Exclusão permanente (hard delete)      |
| `ai_logs`              | 365 dias | Exclusão de registros `AiConsumption`  |

**Mecanismo:**
1. `schedule_deletion_for_candidate()` — Seta `scheduled_deletion_at` no registro do candidato quando rejeitado/desistente
2. `run_cleanup(dry_run=True|False)` — Job diário que deleta registros expirados
3. **DRY-RUN obrigatório:** Sempre rodar com `dry_run=True` primeiro para validar escopo
4. **Audit trail:** Toda exclusão é logada com `candidate_id`, `company_id`, `scheduled_deletion_at`
5. **Multi-tenant:** Nunca cruza dados entre empresas (scoped por `company_id`)

**Tabelas limpas:**
- `candidates` — registros com `scheduled_deletion_at ≤ now`
- `vacancy_candidates` — registros associados com `scheduled_deletion_at ≤ now`
- `ai_consumption` — logs de IA com `scheduled_deletion_at ≤ now`

### 25.6 LGPD Compliance API

**Arquivo:** `lia-agent-system/app/api/v1/lgpd_compliance.py` (916 linhas)

**3 módulos principais:**

| Módulo                           | Endpoints | Artigos LGPD           |
|----------------------------------|-----------|------------------------|
| DPO Registry                     | CRUD      | Art. 41                |
| Breach Notifications             | CRUD + notify | Art. 48 (48h)      |
| Automated Decision Explanations  | CRUD + review | Art. 20            |

**API Endpoints:**

```
GET    /api/v1/lgpd/stats                              # Estatísticas LGPD consolidadas
GET    /api/v1/lgpd/dpo                                # Listar registros DPO
POST   /api/v1/lgpd/dpo                                # Registrar DPO
GET    /api/v1/lgpd/dpo/{company_id}                   # DPO por empresa
GET    /api/v1/lgpd/breaches                            # Listar incidentes
POST   /api/v1/lgpd/breaches                            # Registrar incidente
POST   /api/v1/lgpd/breaches/{id}/notify-anpd           # Notificar ANPD (48h)
POST   /api/v1/lgpd/breaches/{id}/notify-subjects       # Notificar titulares
POST   /api/v1/lgpd/breaches/{id}/resolve               # Resolver incidente
GET    /api/v1/lgpd/decisions                            # Decisões automatizadas
POST   /api/v1/lgpd/decisions                            # Registrar decisão
POST   /api/v1/lgpd/decisions/{id}/request-review        # Solicitar revisão humana
POST   /api/v1/lgpd/decisions/{id}/complete-review       # Completar revisão
```

**Estatísticas LGPD (`LGPDComplianceStats`):**
- `dpo_registered` / `dpo_active`
- `total_breaches` / `open_breaches` / `breaches_pending_anpd`
- `total_automated_decisions` / `pending_human_reviews` / `completed_human_reviews`

### 25.7 Portal do Titular

**Endpoint base:** `/api/v1/data-subject-requests/`

**7 tipos de requisição suportados:**
1. Acesso aos dados (Art. 18 I-II)
2. Correção de dados (Art. 18 III)
3. Anonimização (Art. 18 IV)
4. Portabilidade (Art. 18 V) — via DSR Export Service
5. Eliminação de dados (Art. 18 VI)
6. Informação sobre compartilhamento (Art. 18 VII)
7. Revisão de decisão automatizada (Art. 20)

**Fluxo de atendimento:**
```
Candidato solicita → Sistema registra → Atribuição a responsável →
Verificação de identidade → Processamento → Conclusão → Notificação ao candidato
```

**APIs do Portal do Titular:**
```
GET    /api/v1/data-subject-requests/                     # Lista requisições
POST   /api/v1/data-subject-requests/                     # Criar requisição
GET    /api/v1/data-subject-requests/{id}                 # Detalhes
PUT    /api/v1/data-subject-requests/{id}/assign          # Atribuir responsável
PUT    /api/v1/data-subject-requests/{id}/verify-identity # Verificar identidade
PUT    /api/v1/data-subject-requests/{id}/process         # Processar
PUT    /api/v1/data-subject-requests/{id}/complete        # Concluir
PUT    /api/v1/data-subject-requests/{id}/reject          # Rejeitar
GET    /api/v1/data-subject-requests/stats                # Estatísticas
GET    /api/v1/data-subject-requests/export               # Exportar
```

### 25.8 Consentimento Granular por Finalidade — D5

**Implementado em:** Sprint Y1/D5
**Arquivo:** `app/services/granular_consent_service.py`
**Migration:** `alembic/versions/043_add_candidate_consent_grants.py`
**Endpoint:** `POST/GET /api/v1/granular-consent`

Expande o `ConsentCheckerService` legado para consentimentos granulares por finalidade de IA. Diferença principal: cada finalidade tem seu próprio `consent_type` distinto (antes todas mapeavam para `SCREENING`).

**Mapeamento de finalidades (`GRANULAR_PURPOSE_MAP`):**

| Finalidade | consent_type | Bloqueante? |
|-----------|--------------|-------------|
| `ai_screening` | `SCREENING` | Sim |
| `ai_scoring` | `AI_SCORING` | Sim |
| `ai_video_analysis` | `AI_VIDEO_ANALYSIS` | Sim |
| `ai_comparison` | `AI_COMPARISON` | Sim |
| `data_retention` | `DATA_RETENTION` | Não |
| `marketing` | `MARKETING` | Não |
| `analytics` | `ANALYTICS` | Não |

**Finalidades bloqueantes (`BLOCKING_PURPOSES`):** `ai_screening`, `ai_scoring`, `ai_video_analysis`, `ai_comparison` — quando revogadas, bloqueiam o processamento.

**Métodos do `GranularConsentService` (instanciado com `db`):**

| Método | Descrição |
|--------|-----------|
| `get_summary(candidate_id, company_id)` | Retorna `GranularConsentSummary` com status de todas as 7 finalidades. `all_blocking_given=True` se todas as BLOCKING_PURPOSES estão ok. |
| `bulk_update(candidate_id, company_id, updates, source, ip_address)` | Atualiza múltiplos consentimentos em lote. `updates={purpose: True/False}`. Rastreável via `ip_address`. |
| `check_purpose(candidate_id, company_id, purpose)` | Verificação rápida booleana. Fail-open: retorna `True` em erro para não bloquear candidato por falha técnica. |

**Integração WSI Gate 1 (SEG-4):** `wsi_interview_graph.load_context()` usa `check_purpose("ai_screening")` — se revogado → `state.error="LGPD_CONSENT_REVOKED"` + `stage=ERROR`.

**Referências LGPD/EU AI Act:** LGPD Art. 7 (base legal: consentimento), LGPD Art. 8 (consentimento inequívoco), EU AI Act Art. 13 (transparência e granularidade).

### 25.9 Mapeamento de Dados (80+ tabelas)

**Referência:** `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` → Seção 3

**Classificação de dados (5 níveis):**

| Classificação       | Descrição                  | Exemplos                          |
|---------------------|----------------------------|-----------------------------------|
| Público             | Dados não sensíveis        | Nome da empresa, cargo            |
| Interno             | Uso interno apenas         | Métricas, configurações           |
| Confidencial        | Dados de negócio           | Candidatos, vagas                 |
| Sensível (LGPD)     | Dados pessoais             | CPF, email, telefone              |
| Altamente Sensível  | Dados especiais            | Saúde, biometria, raça            |

**Tabelas de Candidatos (Sensíveis — LGPD):**

| Tabela                   | Dados                                  | Retenção              |
|--------------------------|----------------------------------------|-----------------------|
| `candidates`             | Nome, email, telefone, CPF, endereço   | Conforme política     |
| `candidate_experiences`  | Histórico profissional                 | Conforme política     |
| `candidate_education`    | Formação acadêmica                     | Conforme política     |
| `candidate_attachments`  | CVs, documentos                        | Conforme política     |
| `vacancy_candidates`     | Associação vaga-candidato              | Vida da vaga + 2 anos |

**Tabelas de IA e Decisões Automatizadas:**

| Tabela                                | Dados                         | Retenção    |
|---------------------------------------|-------------------------------|-------------|
| `ai_inference_logs`                   | Logs de inferência IA         | 2 anos      |
| `automated_decision_explanations`     | Explicações de decisão        | 5 anos      |
| `lia_opinions`                        | Pareceres da LIA              | 5 anos      |
| `lia_profile_analyses`                | Análises de perfil            | 5 anos      |
| `bias_audit_reports`                  | Auditorias de viés            | 7 anos      |
| `calibration_feedback`                | Feedback de calibração        | 2 anos      |
| `model_evaluations`                   | Avaliações de modelo          | 2 anos      |

**Tabelas de Compliance e Auditoria:**

| Tabela                                | Dados                         | Retenção    |
|---------------------------------------|-------------------------------|-------------|
| `sox_audit_logs`                      | Logs SOX-compliant            | 7 anos      |
| `compliance_control_library`          | 218 controles (7 frameworks)  | Permanente  |
| `compliance_health_check_items`       | 242 itens de verificação      | Permanente  |
| `data_subject_requests`               | Requisições de titulares      | 5 anos      |
| `consent_records`                     | Registros de consentimento    | 5 anos      |
| `breach_notifications`                | Notificações de incidente     | 10 anos     |

---

## 26. EU AI Act — Conformidade com IA de Alto Risco

### 26.1 Classificação do Sistema

**Documento:** `docs/compliance/FRIA_WSI.md` (355 linhas)

**Classificação EU AI Act:** Sistema de IA de alto risco — Anexo III, ponto 4
("Employment, workers management and access to self-employment")

O WSI (Voice Screening Interview) é classificado como alto risco por ser um sistema de IA usado para recrutamento e seleção de candidatos.

### 26.2 FRIA — Avaliação de Impacto em Direitos Fundamentais

**6 Direitos Fundamentais Avaliados:**

| Direito             | Risco Identificado                                      | Mitigação Implementada                                   | Risco Residual |
|---------------------|--------------------------------------------------------|----------------------------------------------------------|----------------|
| Dignidade humana    | Avaliação desumanizante por voz sem contexto pessoal    | Blocos estruturados com abertura humanizada               | Baixo          |
| Não-discriminação   | Viés em ASR para sotaques regionais, gagueira           | FairnessGuard 3 camadas; Bias Audit Four-Fifths Rule     | Médio          |
| Privacidade         | Coleta de dados biométricos (voz), processamento LLM    | PII masking; retenção 180 dias; anonimização             | Baixo          |
| Devido processo     | Decisão adversa sem possibilidade de contestação        | HITL path; LGPD Art. 20 endpoint ativo; SLA 15 dias     | Baixo          |
| Transparência       | Candidato não sabe que é avaliado por IA                | ConsentCheckerService Gate 1 obrigatório                  | Baixo          |
| Equidade de acesso  | Candidatos sem microfone de qualidade penalizados       | Score de qualidade de áudio não penaliza resposta        | Médio          |

### 26.3 Artigos EU AI Act Aplicáveis

| Artigo    | Requisito                          | Implementação na Plataforma                              |
|-----------|-------------------------------------|----------------------------------------------------------|
| Art. 9    | Gestão de riscos contínua          | FRIA documentado; Bias Audit mensal; Model Drift diário |
| Art. 10   | Dados de treino e auditoria        | BiasAuditService; TrainingDataService                    |
| Art. 13   | Transparência para candidatos      | Aviso no início da chamada; ConsentCheckerService        |
| Art. 14   | Supervisão humana                  | HITL path obrigatório para decisões adversas             |
| Annex III | Classificação alto risco           | Sistema WSI classificado como Annex III ponto 4          |

### 26.4 HITL (Human-in-the-Loop) — Triggers Automáticos

**Arquivo:** `app/services/hitl_service.py`

O HITL path é acionado automaticamente nas seguintes condições:

| Trigger                                   | Condição                              | Ação                                        |
|-------------------------------------------|---------------------------------------|----------------------------------------------|
| Score na zona cinzenta                    | WSI score entre 40–60                 | Enviar para revisão de recrutador sênior     |
| FairnessGuard Camada 2 ou 3 sinalizada   | Viés implícito ou LLM Judge flag     | Revisão obrigatória antes de finalizar       |
| Candidato solicita revisão               | LGPD Art. 20 endpoint                 | SLA 15 dias úteis                            |
| Qualidade de áudio abaixo do threshold   | Métricas de áudio do Deepgram         | Fallback para avaliação textual              |

**Notificação:** Recrutador recebe Bell (in-app) + Teams com link direto para revisão.

**Pontos de Intervenção Humana e SLAs:**

| Gatilho                                | Ação Requerida            | SLA              |
|----------------------------------------|---------------------------|------------------|
| Confiança < 70%                        | Revisão obrigatória       | 24 horas         |
| Decisão de rejeição final              | Aprovação gerencial       | 48 horas         |
| Score de viés elevado (FairnessGuard)  | Análise de compliance     | 72 horas         |
| Reclamação do candidato (Art. 20)      | Investigação DPO          | 5 dias úteis     |
| Auditoria de viés periódica            | Revisão completa          | Mensal           |

### 26.5 FRIA — Riscos Residuais

**Documento:** `docs/compliance/FRIA_WSI.md` → Seção 9

Riscos remanescentes **após** aplicação de todas as salvaguardas. Metodologia: Probabilidade (1–5) × Impacto (1–5) = Score. Aceitável ≤ 9.

| # | Risco Residual                                                                      | P×I  | Classificação |
|---|--------------------------------------------------------------------------------------|------|---------------|
| R1| Viés de ASR para sotaques muito específicos (interior Norte/Nordeste)                | 8    | Aceitável     |
| R2| Variância alta em avaliação de soft skills (Bloco 4 WSI)                             | 6    | Aceitável     |
| R3| Candidato com gagueira leve não identificado pelo filtro de qualidade de áudio       | 8    | Aceitável     |
| R4| Prompt injection via resposta do candidato não detectado por FairnessGuard           | 5    | Aceitável     |
| R5| Deriva de modelo LLM entre versões sem atualização de rubrica                        | 6    | Aceitável     |
| R6| Ausência de conteúdo em bloco WSI interpretada como nota baixa                       | 6    | Aceitável     |
| R7| Candidatos inexperientes em entrevistas por voz com desempenho abaixo do potencial   | 9    | Aceitável     |

**Nenhum risco residual classificado como Inaceitável (≥ 15).**

**Plano de Tratamento:**

| Risco | Ação de Mitigação                                                              | Prazo   |
|-------|---------------------------------------------------------------------------------|---------|
| R1    | Ampliar golden dataset de sotaques em `tests/fixtures/golden_dataset.py`       | Q2 2026 |
| R7    | Guia de orientação pré-entrevista enviado 24h antes via WhatsApp/e-mail        | Q2 2026 |
| R3    | Detecção de gagueira leve na camada de qualidade de áudio; HITL automático     | Q3 2026 |
| R5    | Benchmark de modelo na suite de CI/CD para regressão cross-versão              | Q2 2026 |

### 26.6 Declaração de Conformidade EU AI Act

**Documento:** `docs/compliance/FRIA_WSI.md` → Seção 11

O sistema WSI é aprovado para uso com as seguintes condições obrigatórias:

1. **Consentimento explícito** do candidato antes de cada sessão (via `ConsentCheckerService`)
2. **HITL ativo**: revisão humana obrigatória para scores em zona cinzenta (40–60)
3. **Bias Audit mensal**: frequência mínima conforme Four-Fifths Rule
4. **Não exclusividade**: score WSI não pode ser o único critério de eliminação
5. **Transparência**: candidatos informados da utilização de IA no início da sessão

**Documento de referência:** RIPD-LIA-WSI-2026-001 (validade 12 meses, próxima revisão 03/2027)

**Gatilhos de revisão antecipada:**
- Mudança de modelo LLM
- Novo regulamento EU AI Act
- Resultado adverso em Bias Audit
- Incidente de discriminação reportado

---

## 27. Compliance Multi-Framework

### 27.1 Compliance Health Check

**Documento:** `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` (1678 linhas)
**Rota admin:** `/compliance/health-check`

Dashboard interativo com **242 itens** de verificação distribuídos em **7 frameworks regulatórios:**

| Framework         | Itens | Escopo                                                |
|-------------------|-------|-------------------------------------------------------|
| ISO 27001:2022    | 96    | Controles de segurança da informação (A.5–A.8)       |
| SOC 2 Type II     | 61    | Trust Services Criteria (CC1–CC9, A1, C1, PI1, P1–P8)|
| SOX 404           | 27    | Controles internos, ITGCs, SoD, evidências            |
| LGPD              | 17    | Princípios, direitos do titular, obrigações           |
| BCB 498/2025      | 13    | Seguro cibernético, coberturas obrigatórias           |
| EU AI Act         | 13    | Governança de IA, alto risco, transparência           |
| NYC LL144         | 11    | Auditoria de viés em AEDT, métricas de impacto       |
| **TOTAL**         | **242** | **100% sincronizado com biblioteca de controles**   |

### 27.2 Funcionalidades do Health Check

- Verificação interativa de status por item (compliant / partial / non_compliant / not_applicable)
- Links para documentação oficial de cada framework
- Sincronização automática com biblioteca de controles (`/sync-from-library`)
- Filtros por framework, status e prioridade
- Estatísticas em tempo real por categoria
- Mapeamento de prioridade (mandatory → critical, optional → medium)

**APIs:**
```
GET    /api/v1/health-check/items                # Lista todos os itens
GET    /api/v1/health-check/items/{id}           # Item específico
PUT    /api/v1/health-check/items/{id}           # Atualiza status
GET    /api/v1/health-check/summary              # Resumo por framework
POST   /api/v1/health-check/sync-from-library    # Sincroniza da biblioteca
```

### 27.3 SOX — Trilha de Auditoria

**Tabela:** `sox_audit_logs`
**Retenção:** 7 anos (financeiro)

Logs SOX-compliant para todas as operações sensíveis:
- Movimentação de candidatos entre etapas
- Alterações em políticas de contratação
- Aprovações de vagas com salário acima de threshold
- Exclusão de registros (LGPD cleanup)

**8 Controles SOX implementados:**

| ID     | Controle                    | Evidência                      |
|--------|------------------------------|--------------------------------|
| SOX-01 | Segregação de funções        | `sod_roles`, `sod_conflicts`   |
| SOX-02 | Logs imutáveis               | `sox_audit_logs` (7 anos)      |
| SOX-03 | Controle de acesso           | RBAC + MFA                     |
| SOX-04 | Aprovação de transações      | Workflow de `approvals`        |
| SOX-05 | Trilha de auditoria          | Todos os registros             |
| SOX-06 | Backup e recuperação         | DR automático                  |
| SOX-07 | Gestão de mudanças           | Git + deploy controlado        |
| SOX-08 | Monitoramento de violações   | `sod_violations`               |

### 27.3.1 Logs de Decisão Automatizada

**Tabela:** `automated_decision_explanations`
**Referência:** LGPD Art. 20, EU AI Act Art. 13

| Campo                  | Descrição                            | Obrigatório |
|------------------------|--------------------------------------|-------------|
| `decision_id`          | ID único da decisão                  | Sim         |
| `agent_name`           | Agente responsável                   | Sim         |
| `decision_type`        | Tipo (screening, ranking, etc.)      | Sim         |
| `input_data`           | Dados de entrada (hash, sem PII)     | Sim         |
| `output`               | Resultado da decisão                 | Sim         |
| `confidence`           | Score de confiança (0–1)             | Sim         |
| `reasoning`            | Explicação em linguagem natural      | Sim         |
| `criteria_used`        | Critérios utilizados                 | Sim         |
| `criteria_ignored`     | Critérios desconsiderados            | Sim         |
| `human_review_required`| Flag para revisão humana             | Sim         |
| `model_version`        | Versão do modelo                     | Sim         |
| `timestamp`            | Data/hora                            | Sim         |

### 27.4 SoD — Segregação de Funções

**Tabelas:** `sod_roles`, `sod_conflicts`, `sod_violations`
**Rota admin:** `/compliance/auditoria` → submódulo SoD

Detecção em tempo real de conflitos de segregação de funções:
- Definição de papéis e funções incompatíveis
- Monitoramento contínuo de violações
- Aprovação de exceções com justificativa

### 27.5 BCB 498 — Seguro Cibernético

**Tabelas:** `insurance_policies`, `insurance_coverages`, `insurance_claims`

Aplicável a clientes instituições financeiras reguladas pelo Banco Central:
- Controles de qualidade e validação de modelos de IA
- Documentação de governança de algoritmos
- Trilha de auditoria completa de decisões automatizadas
- Gestão de apólices de seguro cibernético

**12 Controles BCB implementados:**

| ID     | Controle                       | Evidência                      |
|--------|--------------------------------|--------------------------------|
| BCB-01 | Apólice de seguro              | `insurance_policies`           |
| BCB-02 | Cobertura data breach          | `insurance_coverages`          |
| BCB-03 | Cobertura ransomware           | `insurance_coverages`          |
| BCB-04 | Cobertura business interruption| `insurance_coverages`          |
| BCB-05 | Cobertura regulatory defense   | `insurance_coverages`          |
| BCB-06 | Cobertura cyber liability      | `insurance_coverages`          |
| BCB-07 | Cobertura forensics            | `insurance_coverages`          |
| BCB-08 | Cobertura notification costs   | `insurance_coverages`          |
| BCB-09 | Cobertura crisis management    | `insurance_coverages`          |
| BCB-10 | Alertas de renovação           | Sistema automático             |
| BCB-11 | Registro de sinistros          | `insurance_claims`             |
| BCB-12 | Dashboard de compliance        | `/insurance/bcb-compliance`    |

**APIs:** 19 endpoints em `/api/v1/insurance/`

### 27.6 ISO 22301 — Continuidade de Negócios

**Tabelas:** `business_processes`, `disaster_recovery_plans`, `continuity_tests`

- BIA (Business Impact Analysis) por processo crítico
- DRP (Disaster Recovery Plans)
- Testes de continuidade com registro

**APIs:** 12 endpoints em `/api/v1/continuity/`

### 27.7 Trust Center

**Rota admin:** `/compliance/trust-center`

Portal público de confiança para clientes:

| Submódulo          | Público   | Conteúdo                          |
|--------------------|-----------|-----------------------------------|
| Certificações      | Externo   | Selos, certificados               |
| Subprocessadores   | Externo   | Lista de terceiros                |
| Recursos           | Externo   | Políticas, whitepapers            |

---

## 28. Framework de Teste de Viés — Bias Audit Service

### 28.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/bias_audit_service.py` (290 linhas)

Calcula adverse impact real usando dados de `RubricEvaluation` + `Candidate` por vaga, retornando apenas estatísticas agregadas sem PII (LGPD-safe).

### 28.2 Four-Fifths Rule

**Princípio:** Se a taxa de aprovação do grupo com menor taxa é inferior a 4/5 (80%) da taxa do grupo com maior taxa, existe adverse impact.

**Constantes:**
- `APPROVAL_THRESHOLD = 60.0` — Score mínimo para considerar candidato "aprovado"
- `FOUR_FIFTHS_THRESHOLD = 0.80` — Limiar da Four-Fifths Rule

**Fórmula:**
```
adverse_impact_ratio = taxa_menor_grupo / taxa_maior_grupo
se ratio < 0.80 → alert_level = "warning"
se ratio ≥ 0.80 → alert_level = "ok"
```

### 28.3 4 Dimensões Auditadas

| Dimensão      | Grupos                                       | Função de Classificação                   |
|---------------|----------------------------------------------|-------------------------------------------|
| `gender`      | masculino, feminino, não informado            | `candidate.gender` (lowercase)            |
| `age_group`   | <30, 30-44, 45+                              | `_age_group(candidate.date_of_birth)`     |
| `disability`  | com PCD, sem PCD                              | `candidate.has_disability` (boolean)      |
| `region`      | por `location_state`                          | `candidate.location_state`                |

**Faixas etárias (screening-compliance §4):**
- `AGE_GROUP_YOUNG` = "<30"
- `AGE_GROUP_MID` = "30-44"
- `AGE_GROUP_SENIOR` = "45+"

### 28.4 DTOs de Resultado

**`DemographicAuditResult`:**
```python
dimension: str                    # "gender" | "age_group" | "disability" | "region"
groups: Dict[str, Dict]           # {label: {"count": N, "approved": N, "rate": float}}
adverse_impact_ratio: float       # menor_taxa / maior_taxa
below_threshold: bool             # ratio < 0.80
alert_level: str                  # "ok" | "warning"
```

**`BiasAuditReport`:**
```python
job_id: str
evaluated_at: datetime
total_candidates: int
dimensions: List[DemographicAuditResult]
has_alerts: bool                  # True se qualquer dimensão below_threshold
```

### 28.5 Snapshot Histórico

**Modelo:** `BiasAuditSnapshot`

Snapshots de auditorias são salvos para compliance SOX/ISO 27001:
- Frequência: auditoria mensal automática
- Retenção: 7 anos (tabela `bias_audit_reports`)
- Cada snapshot inclui todas as 4 dimensões com contagens e ratios

### 28.6 Referências de Compliance

| Referência           | Requisito                                            |
|---------------------|------------------------------------------------------|
| dei-fairness §4     | Four-Fifths Rule — adverse_impact_ratio ≥ 0.80      |
| LGPD Art. 5         | Dados pessoais / dado sensível — agregação sem PII  |
| EU AI Act Art. 10   | Dados de treino e auditoria                          |
| SOX / ISO 27001     | Evidência de fairness com dados reais                |

---

## 29. Model Drift e Monitoramento Contínuo

### 29.1 Monitoramento de Drift

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.1

**Triggers monitorados:**
- Desvio de score médio (WSI / LIA Score)
- Taxa de aprovação por grupo demográfico
- Custo por avaliação
- Latência P95 das chamadas LLM
- Variância de scores entre avaliações do mesmo candidato

### 29.2 Agendamento e Cadência de Auditoria

| Auditoria                  | Frequência  | Referência FRIA              | Responsável          |
|----------------------------|-------------|-------------------------------|----------------------|
| Model Drift batch job      | Diário      | `drift.run_batch` Celery Beat | Automático           |
| Bias Audit (Four-Fifths)   | Mensal      | FRIA §7.2                     | Automático + DPO     |
| Red Team                   | Semestral   | FRIA §7.3                     | Equipe interna + ext.|
| Revisão de Prompts         | Trimestral  | FRIA §7.4                     | Produto + IA         |
| FRIA revisão completa      | Anual       | FRIA §8                       | DPO + CTO            |

**Alerta automático:** Bell + Teams quando 2+ triggers ativos (`drift_alert_service`)

### 29.3 Red Team — Teste de Adversário

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.3

- **Execução:** Equipe interna + auditoria externa independente
- **Escopo:** Injeção de candidatos fictícios com características protegidas para verificar viés de output
- **Artefatos de teste:** `tests/fairness/test_four_fifths_rule.py` + `tests/fixtures/golden_dataset.py`
- **Resultado:** Documentado em `docs/compliance/red_team_YYYY_S[1|2].md (nomeação por ano/semestre)`

### 29.4 Revisão de Prompts

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.4

- **Escopo:** Auditoria dos system prompts WSI em `app/domains/cv_screening/agents/system_prompt.py`
- **Verificações:** Linguagem neutra, ausência de critérios implicitamente discriminatórios
- **Resultado:** Documentado em `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_YYYY_MM.md (nomeação por ano/mês)`

### 29.5 Métricas de Drift Monitoradas

| # | Métrica | Threshold de Alerta | Frequência | Cálculo |
|---|---------|---------------------|------------|---------|
| 1 | Score médio WSI | Desvio > 10% do baseline | Diário | `mean(scores_30d) vs mean(scores_baseline)` |
| 2 | Taxa de aprovação global | Desvio > 15% | Semanal | `approved / total por período` |
| 3 | Taxa por grupo demográfico | Four-Fifths Rule < 0.80 | Mensal | `min(taxa_grupo) / max(taxa_grupo)` |
| 4 | Custo por avaliação | Aumento > 20% | Diário | `sum(token_cost) / count(evaluations)` |
| 5 | Latência P95 LLM | > 8 segundos | Contínuo | `percentile(response_time, 95)` |
| 6 | Variância intra-candidato | > 15 pontos | Semanal | `std(scores do mesmo candidato)` |
| 7 | Taxa de fallback | > 5% dos requests | Diário | `fallback_count / total_requests` |
| 8 | Rejeições por FairnessGuard | Spike > 3x baseline | Diário | `fairness_blocks_total vs baseline` |

### 29.6 Ações de Remediação

Quando drift é detectado:
1. Alerta automático para equipe de IA (Bell + Teams)
2. Snapshot de comparação (antes/depois) salvo em `BiasAuditSnapshot`
3. Revisão manual dos triggers ativos pelo responsável
4. Se necessário: recalibração de thresholds ou rollback de modelo
5. Registro em `docs/compliance/incidentes/` se classificado como incidente

**Escalation automático por severidade:**
```
Drift leve (1 métrica fora do threshold)
    → Alerta automático para equipe de IA
    → SLA: 48 horas para investigar

Drift moderado (2-3 métricas fora do threshold)
    → Alerta para equipe de IA + DPO
    → SLA: 24 horas para investigar
    → Considerar pausa de avaliações automatizadas

Drift severo (4+ métricas ou Four-Fifths Rule violada)
    → Alerta para equipe de IA + DPO + CTO
    → SLA: 4 horas para contenção
    → Pausa automática de avaliações WSI
    → Incidente registrado em compliance
```

### 29.7 Pipeline de Detecção de Drift

```
[Celery Beat — Agendamento]
         ↓ (diário 03:00 BRT)
[DriftBatchJob]
├── 1. Coleta métricas dos últimos 30 dias
├── 2. Compara com baseline (90 dias anteriores)
├── 3. Calcula z-score para cada métrica
├── 4. Se |z-score| > 2.0 → trigger ativo
├── 5. Conta triggers ativos
│      ├── 0 triggers → OK, log informativo
│      ├── 1-3 triggers → Alerta moderado
│      └── 4+ triggers → Alerta severo + pausa
├── 6. Salva snapshot no banco (drift_snapshots)
└── 7. Emite métricas Prometheus (model_drift_score gauge)
```

---

## 30. Taxonomia de Incidentes

### 30.1 Gestão de Incidentes

**Rota admin:** `/compliance/monitoramento` → submódulo Incidentes

| Campo            | Descrição                                 |
|------------------|-------------------------------------------|
| Ticket ID        | Identificador único do incidente          |
| Severidade       | Critical / High / Medium / Low            |
| Tipo             | Security / Compliance / Operational / AI  |
| Status           | Open / Investigating / Resolved / Closed  |
| RCA              | Root Cause Analysis (obrigatório ao fechar)|
| Responsável      | Atribuído via workflow                    |
| Tabela DB        | `compliance_incidents` (auditável SOX)    |

### 30.2 Incidentes de IA

Tipos específicos para a plataforma LIA:

| Tipo de Incidente           | Exemplo                                         | Severidade Default |
|-----------------------------|--------------------------------------------------|--------------------|
| Viés detectado pós-produção | Four-Fifths Rule violada em auditoria mensal     | High               |
| Model drift significativo   | Score médio WSI desviou >15% em 30 dias          | High               |
| FairnessGuard bypass        | Query discriminatória não bloqueada              | Critical           |
| PII leak em logs            | Dados pessoais identificados em log de produção  | Critical           |
| Circuit breaker persistente | Serviço OPEN por >1 hora sem recovery            | Medium             |
| LLM hallucination           | Resposta factualmente incorreta da LIA           | Medium             |
| Consent violation           | Processamento sem consentimento registrado       | High               |
| Prompt injection            | Score alterado por resposta maliciosa do candidato| Critical           |
| Adverse impact < 0.65       | Abaixo do limiar NYC LL144 em qualquer dimensão  | Critical           |

### 30.3 Definição de Incidente Grave (EU AI Act Art. 73)

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 10.1

Um incidente no sistema WSI é classificado como **grave** se:
- Candidato eliminado por decisão automatizada com evidência de discriminação por critério protegido
- Taxa de adverse impact ratio < 0.65 em qualquer dimensão
- Falha de segurança com exposição de dados biométricos de voz
- Score de candidato alterado indevidamente por prompt injection confirmado

### 30.4 Fluxo de Resposta a Incidentes

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 10.2

```
Detecção (Sistema / Reclamação)
    ↓
T+0h:  Registrar incidente em #compliance-incidents (Teams) + criar ticket
    ↓
T+4h:  DPO notificado — avaliação de gravidade (grave / não grave)
    ↓
T+24h: Se grave → Contenção imediata (suspender avaliações da empresa afetada)
    ↓
T+72h: Análise de causa raiz (engenharia + IA)
    ↓
T+15d: Notificação ao regulador competente (ANPD / autoridade EU AI Act)
    ↓
T+30d: Relatório de incidente final + plano de correção
    ↓
T+60d: Verificação de eficácia das correções aplicadas
```

### 30.5 Contatos e Responsabilidades

| Papel          | Responsabilidade                                  | Canal                           |
|----------------|---------------------------------------------------|----------------------------------|
| DPO            | Notificação regulatória, comunicação ao titular   | `privacidade@wedotalent.com.br` |
| CISO           | Contenção técnica, análise forense                | Slack `#security-incidents`     |
| Engenharia IA  | Análise de causa raiz, correção de modelo         | Jira projeto `LIA-COMPLIANCE`  |
| Jurídico       | Avaliação de responsabilidade civil/regulatória   | `juridico@wedotalent.com.br`   |

### 30.6 Breach Notification (LGPD Art. 48)

**Arquivo:** `lia-agent-system/app/api/v1/lgpd_compliance.py`

Incidentes de segurança que envolvem dados pessoais seguem fluxo LGPD:

| Etapa                     | Prazo           | Responsável         |
|---------------------------|-----------------|---------------------|
| Detecção e registro       | Imediato        | Sistema automático  |
| Classificação de impacto  | 4 horas         | DPO / Segurança     |
| Notificação ANPD          | 48 horas (legal)| DPO                 |
| Notificação dos titulares | 5 dias úteis    | DPO + Comunicação   |
| Resolução e RCA           | 30 dias         | Equipe responsável  |

**Notificação ao titular (Art. 48):**
- Canal: e-mail registrado + notificação no portal do candidato
- Conteúdo obrigatório: natureza dos dados, medidas adotadas, DPO de contato, data do incidente

### 30.7 Registro de Incidentes

Todos os incidentes (graves e não graves) registrados em:
- `docs/compliance/incidentes/INCIDENTE_<ANO>_<SEQ>.md`
- Banco de dados: tabela `compliance_incidents` (auditável SOX/ISO 27001, retenção 7 anos)

---

## 31. Production Readiness

### 31.1 Checklist de Prontidão

Baseado nos 242 itens do Compliance Health Check e nas 13 Crenças do WeDO Talent Guide v3.3:

**Infraestrutura:**

| Item                        | Status      | Arquivo/Serviço                                |
|-----------------------------|-------------|------------------------------------------------|
| Circuit breakers (12)       | Implementado| `app/shared/resilience/circuit_breaker.py`     |
| Token tracking / limites    | Implementado| `app/services/token_tracking_service.py`       |
| Métricas Prometheus         | Implementado| `app/observability/metrics.py`                 |
| Redis cache (TTL config.)   | Implementado| CascadedRouter Tier 2                          |
| pgvector semantic cache     | Implementado| CascadedRouter Tier 3                          |
| Rate limiting               | Configurado | `DEFAULT_LIMITS` no TokenTrackingService       |
| Audit logging (SOX)         | Implementado| `sox_audit_logs` table                         |

**Compliance:**

| Item                                | Status         | Arquivo/Serviço                               |
|--------------------------------------|----------------|------------------------------------------------|
| FairnessGuard (3 camadas)           | **Implementado (11/11 + Orchestrator)** — 62 termos explícitos + 11 implícitos = **73 padrões** `_PATTERNS_VERSION=2` | `app/shared/compliance/fairness_guard.py`      |
| Bias Audit (Four-Fifths Rule)       | Implementado   | `app/services/bias_audit_service.py`           |
| PII Masking (2 componentes)         | Implementado   | `app/shared/pii_masking.py`                    |
| Consent Checker (Gate 1)            | Implementado   | `app/services/consent_checker_service.py`      |
| LGPD Cleanup (daily job)            | Implementado   | `app/services/lgpd_cleanup_service.py`         |
| DSR Export (portabilidade)          | Implementado   | `app/services/dsr_export_service.py`           |
| HITL path (4 triggers)             | Implementado   | `app/services/hitl_service.py`                 |
| FRIA documentado                    | Implementado   | `docs/compliance/FRIA_WSI.md`                  |
| Health Check (242 itens, 7 FW)     | Implementado   | `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` |
| Anti-sycophancy (16 agentes)       | Implementado   | System prompts de todos os agentes             |

**Governança de Agentes:**

| Item                               | Status       | Arquivo/Serviço                                  |
|-------------------------------------|-------------|--------------------------------------------------|
| EnhancedAgentMixin (5 etapas)      | Implementado| `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` |
| AutonomyEngine (3 níveis)          | Implementado| `libs/agents-core/lia_agents_core/autonomy_engine.py`      |
| LongTermMemory (4 tipos)           | Implementado| `libs/agents-core/lia_agents_core/long_term_memory.py`     |
| LearningExtractor (3 categorias)   | Implementado| `libs/agents-core/lia_agents_core/learning_extractor.py`   |
| TrainingDataService (3 formatos)   | Implementado| `app/services/training_data_service.py`          |
| ConfidencePolicyService            | Implementado| `app/services/confidence_policy_service.py`      |

### 31.2 Deployment Checklist

**Pre-Deploy (obrigatório antes de qualquer release):**

| # | Check | Comando/Ação | Pass Criteria |
|---|-------|-------------|---------------|
| 1 | Testes unitários | `pytest --tb=short -q` | 100% pass, 0 fail |
| 2 | Testes de integração | `pytest tests/integration/ -q` | 100% pass |
| 3 | Type check | `mypy app/ --ignore-missing-imports` | 0 errors |
| 4 | Lint | `ruff check app/` | 0 violations |
| 5 | FairnessGuard audit | `python -m scripts.run_fairness_audit` | 0 critical |
| 6 | Bias Audit (vagas ativas) | `python -m scripts.run_bias_audit --active` | Four-Fifths pass |
| 7 | PII Masking validation | `python -m scripts.validate_pii_masking` | 100% masked |
| 8 | Migration check | `alembic check` | No pending |
| 9 | Circuit Breaker status | Health endpoint `/health` | All CLOSED |
| 10 | Token budget reset | Verificar reset mensal aplicado | Confirmed |
| 11 | Secrets rotation | Verificar rotação de API keys | < 90 days old |
| 12 | LGPD consent check | Verificar gates de consentimento ativos | All gates ON |

**Post-Deploy (primeiras 24h):**

| # | Monitoração | Threshold | Ação se Violado |
|---|------------|-----------|-----------------|
| 1 | Error rate | < 1% | Rollback imediato |
| 2 | LLM latency P95 | < 10s | Investigar provider |
| 3 | Circuit breakers | All CLOSED | Investigar serviço |
| 4 | Token consumption | < 120% baseline | Verificar loop infinito |
| 5 | WS connections | Stable ± 10% | Verificar proxy/LB |
| 6 | Fairness blocks | < 5% total requests | Verificar FairnessGuard |
| 7 | HITL queue depth | < 50 pending | Notificar recrutadores |
| 8 | Agent health scores | All > 70 | Investigar agente |

### 31.3 Itens Pendentes para Produção

| Item                                    | Prioridade | Complexidade | Sprint Est. |
|----------------------------------------|------------|-------------|-------------|
| ~~FairnessGuard em todos os 16 agentes~~   | ~~P0~~     | ~~Baixa~~   | ✅ **CONCLUÍDO** — 11/11 agentes + Orchestrator, 73 padrões (v5.0 Sprint X1) |
| ~~Guardrail automatizado anti-sycophancy~~ | ~~P1~~     | ~~Média~~   | ✅ **CONCLUÍDO** — Sistema de prompts com `ANTI_SYCOPHANCY_OPERATIONAL` em todos os 16 agentes; beat schedule monitoramento contínuo |
| JobReportModal com dados reais (backend)| P1         | Média       | Sprint 2 |
| WSI Voice (real, não text-only)        | P2         | Alta        | Sprint 4 |
| Audit trail centralizado (SOX/ISO)     | P1         | Média       | Sprint 2 |
| ~~Dashboard de Model Drift~~           | ~~P2~~     | ~~Média~~   | ✅ **CONCLUÍDO** — endpoint `GET /api/v1/drift/status` + `drift_alert_service.py` + beat `drift-run-batch-daily` |
| ~~Streaming de pensamentos ReAct via WS~~ | ~~P3~~  | ~~Média~~   | ✅ **CONCLUÍDO** (Sprint Y5/E7 — `streaming_react_agent.py` + WS streaming em `agent_chat_ws.py`) |
| Notificações push mobile               | P2         | Média       | Sprint 3 |
| Integração calendário (Google/Outlook)  | P1         | Alta        | Sprint 3 |
| Multi-idioma (EN/ES além de PT)        | P2         | Alta        | Sprint 5 |
| SSO/SAML enterprise                    | P1         | Alta        | Sprint 3 |

### 31.4 Ambiente e Configuração

**Variáveis de ambiente obrigatórias:**

| Variável | Tipo | Obrigatória | Descrição |
|----------|------|-------------|-----------|
| `DATABASE_URL` | String | Sim | PostgreSQL connection string |
| `REDIS_URL` | String | Sim | Redis connection string |
| `ANTHROPIC_API_KEY` | Secret | Sim | Chave API Claude |
| `GOOGLE_AI_API_KEY` | Secret | Sim | Chave API Gemini |
| `OPENAI_API_KEY` | Secret | Não | Chave API OpenAI (fallback) |
| `JWT_SECRET_KEY` | Secret | Sim | Chave para assinatura JWT |
| `RABBITMQ_URL` | String | Sim | RabbitMQ connection string |
| `PEARCH_API_KEY` | Secret | Não | Chave Pearch AI (sourcing) |
| `SMTP_HOST` | String | Sim | Servidor SMTP para emails |
| `SMTP_USER` | String | Sim | Usuário SMTP |
| `SMTP_PASSWORD` | Secret | Sim | Senha SMTP |
| `WHATSAPP_API_TOKEN` | Secret | Não | Token WhatsApp Business API |
| `SENTRY_DSN` | String | Não | DSN Sentry para error tracking |
| `LLM_DEFAULT_PROVIDER` | String | Não | Provider padrão (default: `gemini`) |
| `FAIRNESS_STRICT_MODE` | Bool | Não | Modo strict FairnessGuard (default: `false`) |
| `HITL_AUTO_APPROVE_TIMEOUT` | Int | Não | Timeout auto-approve HITL em horas (default: `24`) |
| `TOKEN_MONTHLY_LIMIT` | Int | Não | Limite mensal de tokens por tenant (default: `1000000`) |

**Portas utilizadas:**

| Porta | Serviço | Protocolo |
|-------|---------|-----------|
| 3000 | Frontend (Vite dev) | HTTP |
| 8000 | Backend (FastAPI/Uvicorn) | HTTP + WS |
| 5432 | PostgreSQL | TCP |
| 6379 | Redis | TCP |
| 5672 | RabbitMQ | AMQP |
| 15672 | RabbitMQ Management | HTTP |
| 5555 | Flower (Celery monitor) | HTTP |

---

## 32. Limitações, Dívidas Técnicas e Funcionalidades Incompletas

### 32.1 Processamento Local vs IA

| Funcionalidade          | Status Atual                                              |
|-------------------------|------------------------------------------------------------|
| LIA Score               | Local (sem LLM) — fórmula ponderada                      |
| Busca de candidatos     | Local (PostgreSQL) + API externa (Pearch AI)              |
| Distribuições/Analytics | Local — contagens e agrupamentos                          |
| SaturationBadge         | Local — threshold vs contagem                             |
| JobReportModal          | Local — dados hardcoded no frontend (mock)                |
| Avaliação por rubrica   | IA real (Claude)                                          |
| WSI Screening           | IA real (Claude)                                          |
| Comparação candidatos   | IA real (Claude)                                          |
| Ranking                 | IA real (Claude)                                          |
| JD Enriquecida          | IA real (Claude)                                          |
| Benchmark salarial      | IA real (Claude) + dados de mercado                       |

### 32.2 Fallbacks Hardcoded

1. **Orchestrator fallback** — Se LLM falha, retorna: "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre '{msg[:50]}..'" com 3 sugestões fixas
2. **CascadedRouter fallback** — Se nenhum tier resolve, retorna clarificação com 6 opções fixas
3. **VectorSemanticCache** — Inicialização graciosa; se pgvector indisponível, pula silenciosamente
4. **PlanDetector** — Falha silenciosa via try/except (non-blocking)
5. **CircuitBreaker** — Fallback configurável por circuit; se não definido, lança `CircuitBreakerError`
6. **Guardrails** — 3 camadas de fallback (AutonomyEngine → DB → lista estática)

### 32.3 Detecção de Intenção por Keywords

- `isGenericQuestion()` — 5 regex + 46 keywords de busca; frágil para termos novos
- `analysisCommands[]` — 8 padrões fixos de string matching
- `detect_command_type()` — keywords por KanbanCommandType; pode falhar para variações
- `_TECHNICAL_PATTERNS` — 5 padrões de string matching para detecção de resposta técnica

### 32.4 Cache

- **Tier 1 (LRU):** In-process, não distribuído entre workers; eviction FIFO
- **Tier 2 (Redis):** Implementado via `SemanticCache` com TTL configurável
- **Response Cache:** Funcional, mas sem invalidação automática por eventos (ex: novo candidato adicionado)

### 32.5 Funcionalidades Incompletas

1. **handleOpenRubricAnalysis orphaned** — Função em `candidates-page.tsx` (linha 6424) sem call sites; modal ainda renderiza mas não é acessível via botão
2. **JobReportModal com dados mock** — Dados hardcoded no frontend (funnelMetrics, channelPerformance, timeline, budget); sem integração com backend real
3. **WSI Voice** — Não implementado; WSI é text-only
4. **Calibração limitada** — Implementada no frontend sem agente ReAct dedicado; depende 100% do Pearch AI
5. **Arquivo monolítico** — `candidates-page.tsx` tem 10.398 linhas; `lia-api.ts` tem 4.943 linhas
6. **Notificações** — `JobCreatedNotificationRequest` suporta email + Teams; WhatsApp ausente

### 32.6 Dívidas Técnicas

1. **IntentRouter legado** — Coexiste com LLM Cascade como fallback; duplicação de lógica
2. ~~**Mapeamento agent_type → domain**~~ → ✅ **RESOLVIDO** (Sprint Y4/E4 — `agents_registry.yaml` com registro dinâmico; `AgentRegistryWatcher` com mtime-gating elimina hardcoding em `AGENT_TYPE_TO_DOMAIN`)
3. **AgentFactory vs get_agent** — Dois padrões coexistem; `get_agent()` NÃO é session-safe mas é usado em código legado
4. **PolicyEngine** — DB service pode ser `None`; validação pode falhar silenciosamente
5. **Detecção de resposta técnica** — String matching (`_TECHNICAL_PATTERNS`); frágil com novas mensagens
6. **Escopo GLOBAL** — `scope_config.py` limita a apenas `generate_report` + `schedule_report`, mas o chat-page envia tudo para o Orchestrator que ignora scope na execução
7. **Circuit breaker dual** — Duas implementações no mesmo arquivo (classe + decorator); deveria ser unificado
8. ~~**FairnessGuard parcial**~~ → ✅ **RESOLVIDO** — 11/11 agentes ReAct + Orchestrator têm FairnessGuard (Sprints SEG-2, v3.0). 73 padrões (62 explícitos + 11 implícitos), Layer 3 ativa em 3 callers críticos (v4.0 ACH-026), 0 xfails red team (v5.0 Sprint X1).

### 32.7 Compliance

1. **Anti-sycophancy** — Presente em todos os agentes (via bloco compartilhado ou equivalente no prompt), porém sem guardrail automatizado em runtime
2. ~~**FairnessGuard**~~ → ✅ **RESOLVIDO** — Integrado em **11/11 agentes ReAct + Orchestrator**. 73 padrões totais (Sprint X1). Layer 3 ativa em 3 callers de alto risco (ACH-026). 0 xfails red team.
3. ~~**Falta consentimento granular**~~ → ✅ **RESOLVIDO** (Sprint Y2/D5 — consentimento granular por tipo de dado implementado)
3b. **LGPD em ATS** — Lista de campos sensíveis não sincronizados é hardcoded
4. **Audit trail** — SOX/ISO 27001 mencionados no prompt do ATS Agent, mas sem implementação de audit trail centralizado
5. **ConsentChecker mode** — Default é `soft_warning` (não bloqueia); deveria ser `hard_block` em produção
6. **Bias Audit** — Dimensão `disability` depende de campo `has_disability` no registro do candidato, que pode não estar preenchido

---

## 33. Oportunidades e Capacidades Ausentes

### 33.1 Score Clicável no Funil

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y2/E1 — `score_breakdown_service.py` + `ScoreBreakdownPanel.tsx` + endpoint `GET /api/v1/candidates/{id}/score-breakdown`. Score breakdown clicável com breakdown de rubricas, WSI, prerequisites e recency.
**Descrição original:** Permitir que recrutador clique no LIA Score de um candidato no funil e veja breakdown detalhado (rubricas, WSI, prerequisites, recency) com explicação de cada componente
**Arquivos relevantes:** `score_breakdown_service.py`, `ScoreBreakdownPanel.tsx`, `lia_score_service.py`

### 33.2 Análise Comparativa com IA Real

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y2/D9 — `candidate_comparison_service.py` + `compare-candidates-modal.tsx` + endpoint `POST /api/v1/candidates/compare`. Modal visual dedicado implementado.
**Descrição original:** Análise comparativa multi-dimensional entre candidatos com visualização lado-a-lado no frontend
**Arquivos relevantes:** `candidate_comparison_service.py`, `compare-candidates-modal.tsx`

### 33.3 Fit Cultural com Dados de Entrevista

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y2/E2 — `cultural_fit_service.py` cruzando competências WSI com dados de entrevistas. `cultural_fit_score` integrado no funil.
**Descrição original:** Avaliar fit cultural do candidato usando dados de entrevistas realizadas (notas do entrevistador, sentimento, alinhamento de valores)
**Arquivos relevantes:** `cultural_fit_service.py`, `lia_score_service.py`

### 33.4 Auto-routing Inteligente

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y4/E9 — `RoutingLearningService` + model `RoutingFeedback` + `compute_domain_confidence_adjustments()`. Fator de ajuste 0.8–1.2 por domínio/empresa. Beat schedule `routing-recompute-daily` (07h UTC).
**Descrição original:** Roteamento que aprende com o tempo quais agentes foram mais úteis para cada tipo de mensagem
**Arquivos relevantes:** `routing_learning_service.py`, `cascaded_router.py`

### 33.5 Insights Proativos no Kanban

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint P4 — `MLInsightsCard` em `job-kanban-page.tsx` com `useMLPredictions()` hook. Lazy-fetch ao expandir. Previsões de TTF, faixa salarial e percentil de mercado.
**Descrição original:** LIA sugere proativamente ações no kanban (ex: "3 candidatos parados há 7 dias na etapa Entrevista")
**Arquivos relevantes:** `ml-insights-card.tsx`, `use-ml-predictions.ts`, `job-kanban-page.tsx`

### 33.6 Relatório Cross-vagas

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y2/D9 — `candidate_comparison_service.py` com análise cross-vagas. Endpoint atualizado para múltiplas vagas simultâneas.
**Descrição original:** Relatório consolidado comparando métricas entre todas as vagas da empresa (TTF, qualidade, custo, fontes)
**Arquivos relevantes:** `candidate_comparison_service.py`, `job_analytics_prompt_service.py`

### 33.7 ML Adaptativo

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y3/D6 — `ml_feedback_service.py` + Celery task `ml.feedback.recompute_active_jobs` + tabela `recruiter_decision_feedback`. Pesos adaptativos recomputados semanalmente (Diagnóstico v6: beat schedule `ml-feedback-recompute-weekly` adicionado, dom 02h UTC).
**Descrição original:** Modelo que ajusta pesos do scoring baseado em feedback de contratações reais
**Arquivos relevantes:** `ml_feedback_service.py`, `lia_score_service.py`, `learning_analytics_service.py`

### 33.8 Benchmark de Mercado Real

**Status:** ✅ RESOLVIDO (parcial)
**Resolução:** Sprint Y3 — `sector_benchmark_service.py` injeta benchmark setorial no prompt de `evaluate_candidate()` (6 setores: tech/varejo/logistica/financeiro/saude/rpo). Integração Glassdoor/Levels.fyi como evolução futura.
**Descrição original:** Benchmark de mercado com dados reais e atualizados (salário, tempo de contratação, volume)
**Arquivos relevantes:** `sector_benchmark_service.py`, `job_wizard_tools.py`

### 33.9 WSI Assíncrono

**Status:** ✅ RESOLVIDO
**Resolução:** Sprint Y4/E3 — `wsi_async_service.py` + model `WsiSession` com status=pending/in_progress/completed. Follow-up automático via Celery beat `followup-check-hourly`. Abandoned check `wsi-abandoned-check` (a cada 4h).
**Descrição original:** Enviar triagem WSI para candidato e processar respostas assincronamente quando o candidato responder
**Arquivos relevantes:** `wsi_async_service.py`, `wsi_abandoned_service.py`, `followup_service.py`

### 33.10 Roadmap de Escalabilidade

| Fase | Objetivo | Itens Principais | Timeline Est. |
|------|----------|------------------|---------------|
| **Fase 1: Hardening** | Produção segura | ~~FairnessGuard 16 agentes~~ ✅ CONCLUÍDO; audit trail SOX, SSO/SAML | Sprint 1-2 |
| **Fase 2: Intelligence** | IA mais inteligente | ~~RAG por domínio~~ ✅ Y5/E6, ~~auto-routing adaptativo~~ ✅ Y4/E9, ~~ML adaptativo~~ ✅ Y3/D6 | ✅ CONCLUÍDO |
| **Fase 3: Scale** | Multi-tenant enterprise | Isolamento por tenant, rate limiting granular, SLA tiered | Sprint 5-7 |
| **Fase 4: Ecosystem** | Integrações e extensões | Marketplace de agentes, plugin system, API pública | Sprint 8-10 |

### 33.11 Outras Oportunidades

| Oportunidade                           | Complexidade | Impacto | Sprint Est. |
|----------------------------------------|-------------|---------|-------------|
| ~~Registro dinâmico de agentes (YAML)~~    | ~~Alta~~    | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y4/E4 — `agents_registry.yaml` + `AgentRegistryWatcher`) |
| ~~Multi-model por agente (GPT/Gemini)~~    | ~~Média~~   | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y4/E5 — `multi_model_router.py` + config por agente no YAML) |
| ~~RAG por domínio (embeddings)~~           | ~~Alta~~    | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y5/E6 — `rag_pipeline_service.py` BM25+pgvector, rebuild diário) |
| ~~Validar escopo de tools no backend~~     | ~~Baixa~~   | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y5/E8 — `tool_registry_metadata.yaml` 32 tools, `validate_registry_against_yaml()`) |
| ~~Ativar FairnessGuard em todos agentes~~ | ~~Baixa~~ | ~~Alto~~ | ✅ **CONCLUÍDO** (Sprint X1 — 73 padrões, 0 xfails) |
| Remover IntentRouter legado            | Baixa       | Médio   | S2 |
| ~~Streaming de pensamentos ReAct via WS~~  | ~~Média~~   | ~~Médio~~   | ✅ **CONCLUÍDO** (Sprint Y5/E7 — `streaming_react_agent.py`) |
| Unificar circuit breaker (classe+deco) | Baixa       | Médio   | S2 |
| Dashboard real-time de Model Drift     | Média       | Alto    | S3 |
| Bias Audit Dashboard no frontend       | Média       | Alto    | S2 |
| Webhook outbound (notificar sistemas)  | Média       | Alto    | S3 |
| ~~Agent-to-Agent communication~~           | ~~Alta~~    | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y5/E10 — Agent Bus Redis Pub/Sub `lia:agent_bus:{company_id}:{to_agent}`) |
| Supervisor Agent (meta-orquestração)   | Alta        | Alto    | S5 |
| Bulk WSI (triagem em massa)            | Média       | Alto    | S3 |
| ~~Feedback loop automático (sem thumbs)~~  | ~~Alta~~    | ~~Alto~~    | ✅ **CONCLUÍDO** (Sprint Y3/D6 — `ml_feedback_service.py` + `RoutingLearningService`) |

### 33.12 Análise de Gaps por Camada

**Camada de Orquestração:**

| Capacidade | Status | Gap |
|-----------|--------|-----|
| Roteamento multi-tier | Implementado (6 tiers) | ✅ Sprint Y4/E9: `RoutingLearningService` + fator adaptativo 0.8–1.2 |
| Fallback em cascata | Implementado | Sem métricas de qualidade do fallback |
| Memory resolution | Implementado (Tier 0) | Apenas pronomes simples (ele/ela/isso) |
| Multi-agent collaboration | ✅ Sprint Y5/E10 — Agent Bus Redis Pub/Sub implementado | — |
| Request batching | Ausente | Cada mensagem é processada individualmente |
| Priority queue | Ausente | FIFO simples, sem priorização por urgência |

**Camada de Agentes:**

| Capacidade | Status | Gap |
|-----------|--------|-----|
| ReAct loop | Implementado (12 agentes) | Max 5 iterações hardcoded |
| StateGraph | Implementado (4 grafos) | Sem persistência de estado entre sessões |
| Tool execution | Implementado | Sem retry automático em falha de tool |
| Context injection | Implementado | Limite de 20 mensagens no contexto |
| Self-correction | Parcial | Apenas via loop ReAct, sem meta-avaliação |
| Dynamic tool selection | ✅ Sprint Y5/E8 — `tool_registry_metadata.yaml` + scope validation | — |

**Camada de Compliance:**

| Capacidade | Status | Gap |
|-----------|--------|-----|
| FairnessGuard | **Implementado (11/11 + Orchestrator)** | 73 padrões; Layer 3 em 3 callers; 0 xfails red team (v5.0) |
| Bias Audit | Implementado | Apenas Four-Fifths, falta Disparate Impact |
| PII Masking | **Implementado completo** | ✅ SEG-3A/D4: `PIIMaskingFilter` instalado em root logger + workers Celery; `strip_pii_for_llm_prompt()` em 6+ callers LLM |
| Consent Management | ✅ Sprint Y2/D5 — consentimento granular por tipo de dado implementado | — |
| FRIA | Documentado | Não automatizado (manual) |
| Explainability | Parcial | Score breakdown existe, falta natural language |

**Camada de Dados:**

| Capacidade | Status | Gap |
|-----------|--------|-----|
| PostgreSQL + pgvector | Implementado | Sem particionamento por tenant |
| Redis cache | Implementado | Sem invalidação inteligente |
| Embeddings | ✅ Sprint Y5/E6 — `rebuild_domain_index_task` + beat diário 04h UTC | — |
| Event sourcing | ✅ Sprint Y5/E12 — `domain_events` append-only + UniqueConstraint sequence_number | — |
| Data versioning | Ausente | Sem versionamento de dados de treinamento |
| Backup/restore | Parcial | pg_dump manual, sem automação |

---

## 34. Referência de Arquivos

### 34.1 Orquestração

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/orchestrator/orchestrator.py` | Orchestrator principal: process_request(), memória, cache, planos |
| `lia-agent-system/app/orchestrator/cascaded_router.py` | CascadedRouter 6 tiers com métricas Prometheus |
| `lia-agent-system/app/orchestrator/fast_router.py` | FastRouter regex/keyword (Tier 4) |
| `lia-agent-system/app/orchestrator/llm_cascade.py` | LLM Cascade Haiku→Sonnet→Opus (Tier 5) |
| `lia-agent-system/app/orchestrator/action_executor.py` | Execução closed-loop de ações (move, email, triagem) |
| `lia-agent-system/app/orchestrator/pending_action.py` | Store de ações pendentes para HITL |
| `lia-agent-system/app/orchestrator/memory_resolver.py` | Resolução de pronomes/referências (Tier 0) |

### 34.2 Agentes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry Singleton + AgentFactory session-safe |
| `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | Mixin: memória, autonomia, aprendizado (5 etapas) |
| `lia-agent-system/libs/agents-core/lia_agents_core/autonomy_engine.py` | AutonomyEngine: 3 níveis de autonomia |
| `lia-agent-system/libs/agents-core/lia_agents_core/learning_extractor.py` | LearningExtractor: 3 categorias |
| `lia-agent-system/libs/agents-core/lia_agents_core/long_term_memory.py` | LongTermMemoryService: 4 tipos de memória |
| `lia-agent-system/libs/agents-core/lia_agents_core/working_memory.py` | WorkingMemoryService: memória de sessão |
| `lia-agent-system/libs/agents-core/lia_agents_core/memory_integration.py` | MemoryIntegration: ponte WM↔LTM |
| `lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py` | Wizard Agent (criação de vagas) |
| `lia-agent-system/app/domains/cv_screening/agents/pipeline_react_agent.py` | Pipeline Agent (triagem CVs) |
| `lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py` | Sourcing Agent (busca candidatos) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/talent_react_agent.py` | Talent Agent (funil) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Jobs Management Agent (portfólio vagas) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Kanban Agent (pipeline) |
| `lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py` | Policy Agent (políticas) |
| `lia-agent-system/app/domains/automation/agents/automation_react_agent.py` | Automation Agent (decomposição tarefas) |
| `lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py` | Analytics Agent (KPIs, previsões) |
| `lia-agent-system/app/domains/communication/agents/communication_react_agent.py` | Communication Agent (multi-canal LGPD) |
| `lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py` | ATS Integration Agent (Gupy, Pandapé, Merge, StackOne) |

### 34.3 Compliance e Governança

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/compliance/fairness_guard.py` | FairnessGuard: 9 categorias, **62 termos explícitos** + 11 termos implícitos = **73 padrões totais**; `_PATTERNS_VERSION=2`; Layer 3 em 3 callers (v5.0 Sprint X1) |
| `lia-agent-system/app/shared/pii_masking.py` | PII Masking: Layer 1 (regex) + Layer 3 (quasi-id) + Layer 4 Presidio NER (opt-in Z6-03); strip_pii_for_llm_prompt + PIIMaskingFilter |
| `lia-agent-system/app/services/bias_audit_service.py` | Bias Audit: Four-Fifths Rule, 4 dimensões |
| `lia-agent-system/app/services/consent_checker_service.py` | ConsentCheckerService: Gate 1, soft_warning/hard_block |
| `lia-agent-system/app/services/lgpd_cleanup_service.py` | LGPD Cleanup: retenção 90-365 dias, dry-run |
| `lia-agent-system/app/services/dsr_export_service.py` | DSR Export: portabilidade LGPD Art. 18 V |
| `lia-agent-system/app/services/confidence_policy_service.py` | ConfidencePolicy: 3 níveis de autonomia de ação |
| `lia-agent-system/app/api/v1/lgpd_compliance.py` | API LGPD: DPO, Breaches, Decisions (916 linhas) |
| `docs/compliance/FRIA_WSI.md` | FRIA: Avaliação de impacto EU AI Act (355 linhas) |
| `docs/API_REFERENCE.md` | **API Reference completa** (342 linhas): 14 grupos de endpoints, autenticação, convenções, rate limits, changelog — **NOVO v3.1 (ACH-020 ✅)** |
| `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` | Arquitetura de compliance: 242 itens, 7 frameworks (1678 linhas) |

### 34.4 Resiliência e Custos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/resilience/circuit_breaker.py` | Circuit Breaker: 12 circuits, 3 estados, notificação |
| `lia-agent-system/app/shared/resilience/dlq_service.py` | **[NOVO — F2-04]** DLQService: Dead Letter Queue para Celery; Redis LIST+SET, cap 1000, TTL 7d; PII masking; notificação Bell; endpoints admin |
| `lia-agent-system/app/api/v1/admin_dlq.py` | **[NOVO — F2-04]** Admin endpoints para DLQ: sumário, listar, limpar, requeue |
| `lia-agent-system/app/services/token_tracking_service.py` | Token Tracking: 10 modelos, limites, custos |
| `lia-agent-system/app/services/training_data_service.py` | Training Data: 3 formatos export (OpenAI, Anthropic, DPO) |
| `lia-agent-system/app/services/feedback_learning_service.py` | Feedback Learning: thumbs, rating, correções |
| `lia-agent-system/app/domains/job_management/services/outcome_tracker.py` | Outcome Tracker: correlação decisão ↔ contratação |
| `lia-agent-system/app/shared/tracing.py` | **[ATUALIZADO — Z6-02]** OpenTelemetry OTLP + LightweightTracer fallback; @trace_span em Router, DLQ, LearningLoop |
| `lia-agent-system/app/api/v1/traces.py` | **[NOVO — Z6-02]** Endpoints de rastreamento: /traces, /traces/stats, /traces/status |

### 34.5 Aprendizado e Analytics

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/learning/learning_loop_service.py` | Silent capture: accept/modify/reject → LearningPattern; **chama LearningSnapshotService antes de cada update (Z2-01)** |
| `lia-agent-system/app/shared/learning/learning_snapshot_service.py` | **[NOVO — Z2-01]** Snapshots imutáveis de LearningPattern; rollback; Redis TTL 30d; MAX_SNAPSHOTS=5/empresa |
| `lia-agent-system/app/services/recruiter_behavior_service.py` | **[NOVO — Z7-01]** Perfis de comportamento por recrutador: active_hours, sourcing_channels, stage_conversion_rates, communication_style |
| `lia-agent-system/app/api/v1/recruiter_behavior.py` | **[NOVO — Z7-01]** Endpoints: behavior-profile, behavior-signal, behavior-invalidate |
| `lia-agent-system/app/services/predictive_analytics_service.py` | Serviço preditivo de contratação |
| `lia-agent-system/app/services/search_analytics_service.py` | Analytics de busca de candidatos |
| `lia-agent-system/app/services/response_cache_service.py` | Cache de respostas por intent |
| `lia-agent-system/app/services/pre_qualification_service.py` | Pre-qualification: triagem automática pré-WSI |
| `lia-agent-system/app/services/personalized_feedback_service.py` | Feedback personalizado: 3 tons |
| `lia-agent-system/app/services/score_normalization_service.py` | Score normalization: fator 0.7-1.3 |
| `lia-agent-system/app/services/lia_score_service.py` | LIA Score: fórmula unificada, pesos por cenário |

### 34.5.1 Shims (Deprecados — Z5-02, Z6-01)

> Estes arquivos existem para compatibilidade retroativa mas **não devem ser usados em código novo**. Emitem `DeprecationWarning` e delegam ao canônico.

| Arquivo (shim) | Canônico | Sprint |
|----------------|----------|--------|
| `lia-agent-system/app/agents/policy_setup_agent.py` | `app/domains/policy/agents/agent.py` (classe `PolicySetupAgent`) | Z5-02 |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/gupy.py` | `app/services/ats_clients/gupy.py` | Z6-01 |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/pandape.py` | `app/services/ats_clients/pandape.py` | Z6-01 |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/stackone.py` | `app/services/ats_clients/stackone.py` | Z6-01 |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/merge.py` | `app/services/ats_clients/merge.py` | Z6-01 |

### 34.6 Prompts e Templates

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/prompts/prompt_registry.py` | Registro centralizado de prompts com versionamento |
| `lia-agent-system/app/shared/prompts/agent_prompts.py` | Interface Python para prompts carregados de YAML |
| `lia-agent-system/app/shared/prompts/loader.py` | PromptLoader — carregamento e cache de YAML |
| `lia-agent-system/app/shared/prompts/templates.py` | PromptTemplate + PromptLibrary (CoT + few-shot) |
| `lia-agent-system/app/shared/prompts/anti_sycophancy_block.py` | Bloco canônico ANTI_SYCOPHANCY_OPERATIONAL |
| `lia-agent-system/app/shared/prompts/job_wizard.py` | Prompts especializados de criação de vagas |
| `lia-agent-system/app/shared/prompts/examples/orchestrator_examples.py` | Few-shot examples para orquestrador |
| `lia-agent-system/app/shared/prompts/examples/pipeline_examples.py` | Few-shot examples para pipeline |
| `lia-agent-system/app/prompts/shared/agent_prompts.yaml` | Prompts base compartilhados (YAML) |
| `lia-agent-system/app/prompts/shared/lia_persona.yaml` | Persona LIA + HR_VOCABULARY + ETHICAL_GUIDELINES |
| `lia-agent-system/app/prompts/shared/defensive.yaml` | Prompts defensivos (clarificação, out-of-scope) |
| `lia-agent-system/app/shared/robustness/defensive_prompts.py` | get_defensive_prompt_section(), triggers, recovery |
| `lia-agent-system/app/shared/robustness/input_validation.py` | Validação de input (formato, tamanho, caracteres) |
| `lia-agent-system/app/shared/robustness/response_filter.py` | Filtragem de resposta (PII, stack traces, IDs internos) |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py` | 18 Kanban Command Templates + detect_command_type() |
| `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py` | 8 Analytics Command Templates + COMMAND_TEMPLATES |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py` | Talent Agent prompts |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/jobs_management_prompts.py` | Jobs Management prompts |
| `lia-agent-system/app/tools/scope_config.py` | Configuração de escopo: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL |
| `docs/ai-prompts/AI_PROMPT_CREATION_GUIDE.md` | Guia de criação de prompts (10 seções canônicas) |

### 34.7 System Prompts por Agente

| Agente | Arquivo do System Prompt |
|--------|-------------------------|
| Wizard | `app/domains/job_management/agents/wizard_system_prompt.py` |
| Pipeline | `app/domains/cv_screening/agents/pipeline_system_prompt.py` |
| Sourcing | `app/domains/sourcing/agents/sourcing_system_prompt.py` |
| Talent | `app/domains/recruiter_assistant/agents/talent_system_prompt.py` |
| Kanban | `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` |
| Jobs Mgmt | `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` |
| Policy | `app/domains/hiring_policy/agents/policy_system_prompt.py` |
| Analytics | `app/domains/analytics/agents/analytics_system_prompt.py` |
| Communication | `app/domains/communication/agents/communication_system_prompt.py` |
| ATS Integration | `app/domains/ats_integration/agents/ats_system_prompt.py` |
| Automation | `app/domains/automation/agents/automation_system_prompt.py` |
| Pipeline Transition | `app/domains/pipeline/agents/pipeline_system_prompt.py` |

### 34.8 Tool Registries por Agente

| Agente | Arquivo do Tool Registry | Qtd Tools |
|--------|-------------------------|-----------|
| Wizard | `app/domains/job_management/agents/wizard_tool_registry.py` | 10 |
| Pipeline | `app/domains/cv_screening/agents/pipeline_tool_registry.py` | 12 |
| Sourcing | `app/domains/sourcing/agents/sourcing_tool_registry.py` | 15 |
| Talent | `app/domains/recruiter_assistant/agents/talent_tool_registry.py` | 13 |
| Kanban | `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | 21 |
| Jobs Mgmt | `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | 12 |
| Policy | `app/domains/hiring_policy/agents/policy_tool_registry.py` | 13 |
| Analytics | `app/domains/analytics/agents/analytics_tool_registry.py` | 6 |
| Communication | `app/domains/communication/agents/communication_tool_registry.py` | 5 |
| ATS Integration | `app/domains/ats_integration/agents/ats_integration_tool_registry.py` | 5 |
| Automation | `app/domains/automation/agents/automation_tool_registry.py` | 6 |
| Pipeline Transition | `app/domains/pipeline/agents/pipeline_tool_registry.py` | 20 |

### 34.9 Stage Context por Agente

| Agente | Arquivo do Stage Context |
|--------|--------------------------|
| Wizard | `app/domains/job_management/agents/wizard_stage_context.py` |
| Pipeline | `app/domains/cv_screening/agents/pipeline_stage_context.py` |
| Sourcing | `app/domains/sourcing/agents/sourcing_stage_context.py` |
| Talent | `app/domains/recruiter_assistant/agents/talent_stage_context.py` |
| Kanban | `app/domains/recruiter_assistant/agents/kanban_stage_context.py` |
| Jobs Mgmt | `app/domains/recruiter_assistant/agents/jobs_mgmt_stage_context.py` |

### 34.10 StateGraph Agents

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py` | JobWizardGraph: 6 nós, criação guiada de vagas |
| `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` | WSIInterviewGraph: entrevista WSI com scoring |
| `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py` | InterviewGraph: agendamento iterativo (slot-filling) |
| `lia-agent-system/app/domains/pipeline/agents/pipeline_transition_agent.py` | PipelineTransitionAgent: transições com compliance |
| `lia-agent-system/app/domains/policy/agents/tool_registry.py` | PolicySetupAgent: onboarding de políticas |

### 34.11 API Endpoints

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/api/v1/agent_chat_ws.py` | WebSocket /ws/chat/{session_id} (chat principal) |
| `lia-agent-system/app/api/v1/orchestrated_job_chat.py` | Endpoint /orchestrator/job-chat (Kanban) |
| `lia-agent-system/app/api/v1/lia_assistant.py` | Endpoint /orchestrator/talent-chat (Float) |
| `lia-agent-system/app/api/v1/lgpd_compliance.py` | 20 endpoints LGPD (DPO, Breaches, Decisions) |
| `lia-agent-system/app/api/v1/automation.py` | Endpoints de automação |
| `lia-agent-system/app/api/v1/compliance.py` | Endpoints de compliance geral |
| `lia-agent-system/app/api/v1/ai_consumption.py` | Endpoints de consumo de IA |
| `lia-agent-system/app/api/v1/training_data.py` | Endpoints de dados de treinamento |
| `lia-agent-system/app/main.py` | FastAPI app: CORS, middleware, routers (206 endpoints) |

### 34.12 Infraestrutura de IA

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/providers/llm_factory.py` | LLMProviderFactory: Factory + Singleton, fallback sequencial |
| `lia-agent-system/app/shared/providers/llm_claude.py` | ClaudeLLMProvider: claude-sonnet-4-6 |
| `lia-agent-system/app/shared/providers/llm_gemini.py` | GeminiLLMProvider: gemini-2.5-flash |
| `lia-agent-system/app/shared/providers/llm_openai.py` | OpenAILLMProvider: gpt-4o |
| `lia-agent-system/app/shared/intelligence/embedding_service.py` | EmbeddingService: Gemini text-embedding-004, 768-dim |
| `lia-agent-system/app/shared/intelligence/semantic_search_service.py` | SemanticSearchService: expansão 4 domínios, Redis cache |
| `lia-agent-system/app/shared/intelligence/smart_extractor.py` | SmartExtractor: regex + LLM fallback |
| `lia-agent-system/app/shared/policy_middleware.py` | PolicyMiddleware: resolve company_id, injeta policy |

### 34.13 Automação e Messaging

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/domains/automation/services/automation_service.py` | Motor de automação: trigger → condition → action |
| `lia-agent-system/app/domains/automation/services/automation_trigger_service.py` | 4 triggers proativos (48h, 24h, 5d, offer) |
| `lia-agent-system/app/domains/automation/services/proactive_service.py` | Morning briefing, EOD summary, interview reminders |
| `lia-agent-system/app/domains/automation/services/stage_automation_engine.py` | Router de eventos de pipeline → auto_execute ou AISuggestion |
| `lia-agent-system/app/shared/messaging/celery_config.py` | Configuração Celery: 4 filas (sourcing, evaluation, vagas, onboarding) |
| `lia-agent-system/app/shared/messaging/rabbitmq_consumer.py` | Consumer RabbitMQ para processamento assíncrono |

### 34.14 Observabilidade

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/observability/metrics.py` | 14 métricas Prometheus (6 Counters, 4 Histograms, 4 Gauges) |
| `lia-agent-system/app/shared/structured_logging.py` | Structured logging JSON (ELK/CloudWatch) |
| `lia-agent-system/app/shared/governance/agent_monitoring_service.py` | Health score, activity feed, alertas proativos |

### 34.15 Aprendizado e Learning

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/learning/learning_loop_service.py` | Silent capture: accept/modify/reject → LearningPattern |
| `lia-agent-system/app/shared/learning/ab_testing_service.py` | A/B testing de prompts: variantes, p-value, z-score |
| `lia-agent-system/app/shared/learning/template_learning_service.py` | Templates auto-gerados de 3+ vagas similares |
| `lia-agent-system/app/shared/learning/finetuning_export.py` | Export JSONL com PII masking para fine-tuning |
| `lia-agent-system/app/services/feedback_learning_service.py` | Feedback thumbs/rating → DPO pairs |
| `lia-agent-system/app/services/training_data_service.py` | Training Data: 3 formatos (OpenAI, Anthropic, DPO), 506 linhas |
| `lia-agent-system/app/domains/job_management/services/outcome_tracker.py` | Correlação decisão → resultado de contratação |
| `lia-agent-system/app/services/learning_analytics_service.py` | Analytics de aprendizado |

### 34.16 Serviços Preditivos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/services/predictive_analytics_service.py` | Previsões de contratação (TTF, probabilidade) |
| `lia-agent-system/app/services/pipeline_prediction_service.py` | Previsão de pipeline (T+7, T+14, T+30) |
| `lia-agent-system/app/services/early_warning_service.py` | EWS: alertas proativos (estagnação, dropout, saturação) |
| `lia-agent-system/app/services/journey_intelligence_service.py` | Jornada do candidato (touchpoints, engajamento) |
| `lia-agent-system/app/services/sector_benchmark_service.py` | Benchmark setorial (TTH, custo, aceitação) |
| `lia-agent-system/app/services/model_drift_service.py` | Drift monitoring (PSI, KL Divergence) |
| `lia-agent-system/app/services/feature_engineering.py` | Feature engineering para modelos preditivos |
| `lia-agent-system/app/services/outcome_predictor.py` | Previsão de resultado (contratação/rejeição) |
| `lia-agent-system/app/services/search_analytics_service.py` | Analytics de busca de candidatos |
| `lia-agent-system/app/services/response_cache_service.py` | Cache de respostas por intent (TTL configurável) |

### 34.17 Serviços de Scoring e Avaliação

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/services/lia_score_service.py` | LIA Score unificado: fórmula determinística com pesos por cenário |
| `lia-agent-system/app/services/score_normalization_service.py` | Normalização de score: fator 0.7-1.3 |
| `lia-agent-system/app/services/pre_qualification_service.py` | Pre-qualification: triagem automática pré-WSI |
| `lia-agent-system/app/services/personalized_feedback_service.py` | Feedback personalizado: 3 tons |
| `lia-agent-system/app/services/wsi_service.py` | WSI Service: orquestração de entrevistas |

### 34.18 Integração com ATSs

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/domains/ats_integration/services/ats_sync_service.py` | Serviço de sincronização bidirecional |
| `lia-agent-system/app/services/ats_clients/gupy.py` | **[CANÔNICO — Z6-01]** Client ATS Gupy |
| `lia-agent-system/app/services/ats_clients/pandape.py` | **[CANÔNICO — Z6-01]** Client ATS Pandapé |
| `lia-agent-system/app/services/ats_clients/stackone.py` | **[CANÔNICO — Z6-01]** Client ATS StackOne (unificado) |
| `lia-agent-system/app/services/ats_clients/merge.py` | **[CANÔNICO — Z6-01]** Client ATS Merge (unificado) |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/gupy.py` | **[SHIM — Z6-01]** Re-exporta de `app/services/ats_clients/gupy.py` com `DeprecationWarning` |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/pandape.py` | **[SHIM — Z6-01]** Re-exporta de `app/services/ats_clients/pandape.py` |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/stackone.py` | **[SHIM — Z6-01]** Re-exporta de `app/services/ats_clients/stackone.py` |
| `lia-agent-system/app/domains/ats_integration/services/ats_clients/merge.py` | **[SHIM — Z6-01]** Re-exporta de `app/services/ats_clients/merge.py` |

### 34.19 Comunicação Multi-Canal

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/services/email_service.py` | EmailService: SendGrid + Resend (fallback) |
| `lia-agent-system/app/services/whatsapp_service.py` | WhatsAppService: Twilio + templates |
| `lia-agent-system/app/services/teams_service.py` | TeamsService: Microsoft Graph API |
| `lia-agent-system/app/services/deepgram_service.py` | DeepgramService: transcrição de entrevistas |

### 34.20 Frontend (plataforma-lia/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `src/components/pages/candidates-page.tsx` | Float Chat, busca, análise, UnifiedBulkActionsBar, ProactiveInsightCard |
| `src/components/pages/job-kanban-page.tsx` | Kanban Chat, pipeline visual, SaturationBadge, drag-and-drop |
| `src/components/pages/chat-page.tsx` | Chat Full dedicado, Quick Actions, histórico, WebSocket |
| `src/components/pages/analytics-page.tsx` | Dashboard de analytics e métricas |
| `src/components/pages/jobs-page.tsx` | Lista de vagas com filtros e ações bulk |
| `src/components/pages/policy-page.tsx` | Configuração de políticas de contratação |
| `src/components/rubric-evaluation-modal.tsx` | Modal de avaliação por rubrica multi-dimensional |
| `src/components/proactive-insight-card.tsx` | Card de insights proativos após busca |
| `src/components/kanban/components/SaturationBadge.tsx` | Badge de saturação do pipeline por canal |
| `src/components/job-report-modal.tsx` | Modal de relatório da vaga com export PDF |
| `src/components/ui/unified-bulk-actions-bar.tsx` | Barra de ações bulk (9 ações) |
| `src/components/contextual-actions-banner.tsx` | Banner de ações contextuais (8 ações) |
| `src/services/lia-api.ts` | Client API (4943 linhas) |
| `src/lib/api/kanban-assistant.ts` | API helpers: callOrchestratedTalentChat(), callOrchestratedJobChat() |
| `src/contexts/lia-float-context.tsx` | Estado global do Float/Super Prompt |
| `src/hooks/use-websocket.ts` | Hook WebSocket com reconexão automática |
| `src/hooks/use-lia-chat.ts` | Hook de chat com gestão de estado |
| `src/hooks/use-kanban-agent.ts` | Hook do Kanban Agent com comandos |

### 34.21 Documentação de Referência

| Arquivo | Responsabilidade |
|---------|-----------------|
| `docs/compliance/FRIA_WSI.md` | FRIA — Avaliação de Impacto em Direitos Fundamentais (355 linhas) |
| `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` | Arquitetura de Compliance (1678 linhas, 242 itens, 7 frameworks) |
| `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` | Mapa de inteligência LIA (v3.0) |
| `docs/diagnostico-agentes-mvp.md` | Diagnóstico de agentes para MVP |
| `docs/analise-comparativa-v5-vs-lia.md` | Análise comparativa v5 vs LIA |
| `docs/RELATORIO_AUDITORIA_LIA.md` | Relatório de auditoria LIA |
| `docs/ai-prompts/AI_PROMPT_CREATION_GUIDE.md` | Guia de criação de prompts (10 seções canônicas) |
| `relatorio_capacidades_prompts_lia.md` | Este documento (v3.0) |

### 34.22 Inventário Quantitativo

| Métrica | Valor | Data da Auditoria |
|---------|-------|-------------------|
| Total de endpoints | 206 | 13/03/2026 |
| Total de serviços | 231 | 13/03/2026 |
| Total de models | 99 | 13/03/2026 |
| Total de migrações | 37 | 13/03/2026 |
| Total de hooks (frontend) | 114 | 13/03/2026 |
| Total de páginas (frontend) | 90 | 13/03/2026 |
| Total de arquivos de teste | 227 | 13/03/2026 |
| Métricas Prometheus | 14 | 13/03/2026 |
| Domínios DDD | 12 | 13/03/2026 |
| Agentes ReAct | 12 | 13/03/2026 |
| Agentes StateGraph | 4 | 13/03/2026 |
| Agente PolicySetup | 1 | 13/03/2026 |
| Total de agentes | 16 (+1 setup) | 13/03/2026 |
| Tool registries | 12 | 13/03/2026 |
| Scopes definidos | 4 | 13/03/2026 |
| Circuit breakers | 12 | 13/03/2026 |
| Filas Celery | 4 | 13/03/2026 |
| Provedores LLM | 3 | 13/03/2026 |
| Integrações ATS | 4 | 13/03/2026 |
| Canais de comunicação | 4 | 13/03/2026 |

> **Nota v4.2 (15/03/2026):** Os valores acima refletem a auditoria de 13/03/2026. Após Sprints Y1–Y5, os totais reais são maiores: migrações chegaram a 47, métricas Prometheus a 17, novos serviços e modelos adicionados. Ver Seção 34.23 para arquivos incrementais.

### 34.23 Arquivos Adicionados em Sprints Y1–Y5

**Migrations (Alembic) — Y1–Y5:**

| Migration | Descrição |
|-----------|-----------|
| `alembic/versions/041_add_agent_ragas_evaluations.py` | Tabela de avaliações RAGAS por agente |
| `alembic/versions/042_add_disparate_impact_to_snapshot.py` | Disparate Impact ratio no BiasAuditSnapshot |
| `alembic/versions/043_add_candidate_consent_grants.py` | Consentimentos granulares por finalidade (D5) |
| `alembic/versions/044_add_recruiter_decision_feedback.py` | Tabela `recruiter_decision_feedback` (D6) |
| `alembic/versions/045_add_domain_to_embeddings.py` | Campo `domain` em embeddings para RAG por domínio (E6) |
| `alembic/versions/046_add_routing_feedback.py` | Tabela `routing_feedback` para adaptive routing (E9) |
| `alembic/versions/047_add_event_store.py` | Tabela `domain_events` imutável para event sourcing (E12) |

**Models SQLAlchemy — Y1–Y5:**

| Arquivo | Model | Descrição |
|---------|-------|-----------|
| `app/models/event_store.py` | `DomainEvent` | aggregate_id, event_type, event_data (JSONB), sequence_number — append-only |
| `app/models/recruiter_decision_feedback.py` | `RecruiterDecisionFeedback` | Decisões de recrutadores para ML feedback loop |
| `app/models/routing_feedback.py` | `RoutingFeedback` | Correções de roteamento para adaptive learning |

**Services Backend — Y1–Y5:**

| Arquivo | Sprint | Descrição |
|---------|--------|-----------|
| `app/services/ml_feedback_service.py` | D6 | ML feedback loop + pesos adaptativos por vaga |
| `app/services/routing_learning_service.py` | E9 | Adaptive routing com aprendizado de correções |
| `app/services/event_store_service.py` | E12 | Event sourcing append-only com reconstruct_state |
| `app/services/granular_consent_service.py` | D5 | Consentimento granular por finalidade de IA (7 tipos) |
| `app/services/salary_benchmark_service.py` | D7 | Benchmark salarial via Apify + fallback setorial estático |
| `app/services/ragas_evaluation_service.py` | ACH-027 | Avaliação RAGAS de qualidade de respostas do agente |

**Shared / Core — Y1–Y5:**

| Arquivo | Sprint | Descrição |
|---------|--------|-----------|
| `app/shared/agents/agent_bus.py` | E10 | Agent Bus Redis Pub/Sub para comunicação inter-agentes |
| `app/core/agent_registry_watcher.py` | E4 | Watcher polling de agents_registry.yaml + tool_registry_metadata.yaml com hot-reload |
| `app/core/agent_model_config.py` | E5 | Config multi-model por agente (AGENT_MODEL_{NAME} envvars) |
| `app/core/redis_client.py` | Y1 | Cliente Redis centralizado com get_redis() |
| `app/agents_registry.yaml` | E4 | Registro YAML de 7 agentes com model_id, class_path, enabled |

**API Endpoints — Y1–Y5:**

| Arquivo | Sprint | Endpoint | Descrição |
|---------|--------|----------|-----------|
| `app/api/v1/candidate_compare.py` | D9 | `POST /api/v1/candidates/compare` | Comparação 2–4 candidatos |
| `app/api/v1/event_history.py` | E12 | `GET /api/v1/event-history` | Histórico imutável de eventos |
| `app/api/v1/granular_consent.py` | D5 | `POST/GET /api/v1/granular-consent` | Consentimento granular |
| `app/api/v1/metrics.py` | D1 | `GET /api/v1/metrics` | Endpoint Prometheus metrics |
| `app/api/v1/ml_feedback.py` | D6 | `POST /api/v1/ml-feedback` | Registro de feedback ML |
| `app/api/v1/salary_benchmark.py` | D7 | `GET /api/v1/salary-benchmark` | Benchmark salarial |
| `app/api/v1/admin_agents.py` | E4 | `GET/POST /api/v1/admin/agents` | Admin do registro de agentes + hot-reload |

**Frontend Hooks — Y1–Y5:**

| Arquivo | Sprint | Descrição |
|---------|--------|-----------|
| `src/hooks/use-score-breakdown.ts` | E1 | Score breakdown por dimensão |
| `src/hooks/use-candidate-compare.ts` | D9 | Comparação de candidatos |
| `src/hooks/use-proactive-insights.ts` | D8 | Insights proativos no kanban |
| `src/hooks/use-wsi-async.ts` | E3 | WSI assíncrono via token |
| `src/hooks/use-job-report.ts` | D1 | Job report com dados reais |

**Frontend Components — Y1–Y5:**

| Arquivo | Sprint | Descrição |
|---------|--------|-----------|
| `src/components/modals/candidate-compare-modal.tsx` | D9 | Modal de comparação visual multi-dimensional |
| `src/components/react-thinking-stream.tsx` | E7 | Streaming de raciocínio ReAct (colapsável) |

**Frontend Proxies — Y1–Y5:**

| Arquivo | Sprint | Endpoint proxied |
|---------|--------|-----------------|
| `src/app/api/backend-proxy/candidates/compare/route.ts` | D9 | `POST /candidates/compare` |
| `src/app/api/backend-proxy/wsi-async/[token]/route.ts` | E3 | WSI assíncrono por token |
| `src/app/api/backend-proxy/proactive-insights/route.ts` | D8 | Insights proativos |
| `src/app/api/backend-proxy/rubrics/[jobId]/candidates/[candidateId]/breakdown/route.ts` | E1 | Score breakdown |

**Testes — Y1–Y5:**

| Arquivo | Descrição |
|---------|-----------|
| `tests/unit/test_d1_job_report_endpoint.py` | D1: Job report endpoint |
| `tests/unit/test_d10_pearch_fallback.py` | D10: Pearch circuit breaker + fallback |
| `tests/unit/test_e1_score_breakdown.py` | E1: Score breakdown por dimensão |
| `tests/unit/test_e12_event_sourcing.py` | E12: Event sourcing append/replay/reconstruct |
| `tests/unit/test_diagnostico_v6_gaps.py` | 16 testes dos 4 gaps do diagnóstico v6 |
| `tests/integration/test_guardrails_flow.py` | Fluxo completo de guardrails |
| `tests/integration/test_hitl_flow.py` | Fluxo HITL end-to-end |
| `tests/integration/test_rag_search_flow.py` | RAG híbrido BM25+pgvector |
| `tests/security/` | 6 arquivos: fairness, LGPD, PII, multi-tenant, circuit breakers, prompt injection |

---

---

## Apêndice A — Glossário Técnico

| Termo | Definição |
|-------|-----------|
| **ReAct Agent** | Padrão de agente que alterna entre Raciocínio (Reason) e Ação (Act) em loop iterativo. Cada iteração: pensa → seleciona tool → executa → observa resultado → decide próximo passo. |
| **StateGraph Agent** | Agente baseado em máquina de estados (LangGraph) com nós e arestas condicionais. Usado para fluxos multi-etapa estruturados (wizard, entrevista, pipeline). |
| **CascadedRouter** | Roteador de 6 camadas (tiers) que classifica mensagens do usuário para o agente correto. Começa pelo tier mais rápido/barato e escala até LLM se necessário. |
| **WSI (Weighted Screening Interview)** | Entrevista estruturada automatizada onde LIA faz perguntas padronizadas e avalia respostas por bloco temático, gerando score ponderado. |
| **LIA Score** | Score unificado (0-100) que combina WSI, rubrica, prerequisites e recency com pesos configuráveis por cenário de contratação. |
| **HITL (Human-in-the-Loop)** | Padrão de segurança onde ações mutativas (mover candidato, enviar email) requerem confirmação explícita do recrutador antes da execução. |
| **FairnessGuard** | Camada de compliance que bloqueia prompts e respostas contendo viés discriminatório (idade, gênero, raça, etc.). 3 camadas: input, output, audit. |
| **Circuit Breaker** | Padrão de resiliência que previne chamadas a serviços indisponíveis. 3 estados: CLOSED (normal), OPEN (bloqueado), HALF_OPEN (testando recuperação). |
| **DDD (Domain-Driven Design)** | Arquitetura onde código é organizado por domínios de negócio (job_management, cv_screening, sourcing, etc.) ao invés de camadas técnicas. |
| **Scope Config** | Configuração que define quais tools cada agente pode usar em cada contexto do frontend (TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL). |
| **PII Masking** | Técnica de anonimização que substitui dados pessoais (CPF, email, telefone) por tokens antes de enviar ao LLM, restaurando após resposta. |
| **Four-Fifths Rule** | Regra de compliance EEOC que verifica se a taxa de aprovação do grupo minoritário é ≥ 80% da taxa do grupo majoritário. |
| **Prompt Injection** | Ataque onde input malicioso tenta manipular o comportamento do LLM. Mitigado por `detect_and_sanitize_injection()`. |
| **Token Budget** | Limite mensal de tokens LLM por tenant para controle de custos. Rastreado pelo `TokenTrackingService`. |
| **Embedding** | Representação vetorial (768 dimensões) de texto, usada para busca semântica e matching de candidatos. |
| **pgvector** | Extensão PostgreSQL que suporta operações com vetores (embeddings), permitindo busca por similaridade coseno diretamente no banco. |
| **Celery Beat** | Scheduler que executa tarefas periódicas (morning briefing, LGPD cleanup, bias audit) via cron. |
| **DSR (Data Subject Request)** | Requisição de titular de dados (LGPD Art. 18) para acesso, correção, exclusão ou portabilidade de dados pessoais. |
| **FRIA (Fundamental Rights Impact Assessment)** | Avaliação de impacto em direitos fundamentais, obrigatória para sistemas de IA de alto risco conforme EU AI Act. |
| **Anti-Sycophancy** | Bloco de prompt que impede a LIA de concordar com tudo que o recrutador diz, forçando contestação factual quando necessário. |
| **AutonomyEngine** | Motor que classifica ações em 3 níveis: nível 1 (auto-execute), nível 2 (sugerir com confiança), nível 3 (sempre pedir confirmação). |
| **LearningExtractor** | Serviço que extrai padrões de comportamento do recrutador a partir de interações, armazenando como memória de longo prazo. |
| **Model Drift** | Degradação gradual da qualidade do modelo ao longo do tempo, monitorada por 8 métricas (PSI, KL Divergence, etc.). |
| **DPO (Direct Preference Optimization)** | Técnica de fine-tuning que usa pares (resposta boa, resposta ruim) para alinhar o modelo com preferências humanas. |
| **CoT (Chain of Thought)** | Técnica de prompting que força o LLM a raciocinar passo-a-passo antes de dar a resposta final, melhorando qualidade em tarefas complexas. |
| **Few-shot Examples** | Exemplos incluídos no prompt para guiar o formato e qualidade da resposta do LLM. |
| **SLA (Service Level Agreement)** | Acordo de nível de serviço que define thresholds de performance (latência, disponibilidade, taxa de sucesso). |
| **TTF (Time to Fill)** | Métrica de recrutamento que mede o tempo entre abertura da vaga e contratação do candidato. |
| **TTH (Time to Hire)** | Métrica de recrutamento que mede o tempo entre candidatura e contratação. |
| **Rubric Evaluation** | Avaliação multi-dimensional de candidatos usando rubricas padronizadas (technical, behavioral, cultural, experience). |
| **Pre-Qualification** | Triagem automatizada pré-WSI que verifica prerequisites (senioridade, localização, salário, disponibilidade) antes de iniciar entrevista completa. |
| **Morning Briefing** | Relatório proativo diário gerado pela LIA com resumo de atividades, alertas e sugestões para o dia. |
| **Float Chat** | Chat flutuante (overlay) na página de candidatos, com contexto de busca e filtros integrados. |
| **Super Prompt** | Chat expandido (tela cheia) com acesso a todos os agentes e ferramentas. |

---

## Apêndice B — Mapa de Dependências entre Serviços

```
                    ┌─────────────────┐
                    │   Frontend      │
                    │ (React + Vite)  │
                    └────────┬────────┘
                             │ WebSocket / REST
                             ▼
                    ┌─────────────────┐
                    │    FastAPI      │
                    │  (206 endpoints)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌─────────────┐  ┌──────────┐
     │Orchestrator│  │PolicyMiddlw │  │  CORS    │
     │(Router,    │  │(company_id) │  │  Auth    │
     │ Memory,    │  └─────────────┘  └──────────┘
     │ Action)    │
     └─────┬──────┘
           │ route_to_agent()
     ┌─────┴──────────────────────────────────┐
     │         12 ReAct Agents                │
     │    + 4 StateGraph Agents               │
     │    + 1 PolicySetup Agent               │
     └─────┬──────────────────────────────────┘
           │ execute_tool()
     ┌─────┴──────────────────────────────────┐
     │            231 Services                │
     │  (12 DDD domains × ~19 services each)  │
     └─────┬──────────────────────────────────┘
           │
     ┌─────┴──────────┬────────────┬──────────┐
     ▼                ▼            ▼          ▼
┌──────────┐  ┌─────────────┐ ┌───────┐ ┌──────────┐
│PostgreSQL│  │    Redis     │ │Celery │ │ LLM APIs │
│+ pgvector│  │ (cache,      │ │+Rabbit│ │(Claude,  │
│(99 models│  │  sessions)   │ │MQ     │ │ Gemini,  │
│37 migr.) │  └─────────────┘ └───────┘ │ OpenAI)  │
└──────────┘                            └──────────┘
```

**Fluxo de uma requisição típica:**
1. Frontend envia mensagem via WebSocket → `agent_chat_ws.py`
2. Orchestrator recebe → `CascadedRouter` classifica (6 tiers) → seleciona agente
3. Agente ReAct executa loop: Reason → Tool → Observe (max 5 iterações)
4. Tool chama serviço do domínio → serviço acessa banco/cache/LLM
5. Se ação mutativa → `ActionExecutor` → HITL confirmation via WebSocket
6. Resposta formatada → WebSocket → Frontend renderiza
7. Métricas Prometheus atualizadas, logs estruturados emitidos
8. `LearningExtractor` captura padrões silenciosamente

---

---

## Apêndice C — Changelog

### v4.2 (15/03/2026) — Atualização de Seções 5, 9, 13, 15, 17, 18, 25, 34

**Seções atualizadas (auditoria direta do código-fonte):**
- **Seção 5.9:** E7 Streaming ReAct — `ReactThinkingStream` component, protocolo WS `thinking`/`tool_call`
- **Seção 9.6:** D7 Salary Benchmark real — `SalaryBenchmarkService` (Apify + fallback setorial, Redis TTL=7d)
- **Seção 9.7:** D9 Comparação de Candidatos — `CandidateComparisonService`, cenários A/B/C, modal FE
- **Seção 13.5:** E10 Agent Bus — `AgentBus` Redis Pub/Sub, `AgentEvent`, audit trail, fail-open
- **Seção 13.6:** E12 Event Sourcing — `DomainEvent`, `EventStoreService`, append-only, `reconstruct_state()`
- **Seção 13.7:** E9 Adaptive Routing — `RoutingLearningService`, fator 0.8–1.2, beat `routing-recompute-daily`
- **Seção 15.12:** D6 ML Feedback Loop — `MLFeedbackService`, `JobScoringWeights`, `compute_calibration_adjustment()` agora retorna valores reais
- **Seção 17.6:** Métricas Prometheus completas — 17 métricas (não 14): `router_tier_hit_total`, `agent_llm_tokens_total`, `agent_errors_total`, `llm_cost_usd_total`, `router_latency_ms`, `router_confidence`, `agent_request_duration_seconds`
- **Seção 17.7:** D4 PII Masking em logs — `PIIMaskingFilter` no root logger + Celery workers (SEG-3A)
- **Seção 18.6:** D10 Pearch circuit + tabela de circuits AUD-2/Y1 com arquivos reais
- **Seção 25.8 (renumerada 25.9):** D5 Consentimento Granular — `GranularConsentService`, 7 finalidades, 4 blocking, `check_purpose()` fail-open
- **Seção 33 (compliance):** PII Masking status atualizado de gap para "implementado completo"
- **Seção 34.22:** Nota adicionada sobre migrações (47) e métricas (17) após Y1–Y5
- **Seção 34.23:** Nova seção com 7 migrations, 3 models, 6 services, 5 shared/core files, 7 API endpoints, 5 hooks FE, 2 components FE, 4 proxies FE, 9 test files

### v4.0 (15/03/2026) — Y5 + Guia de Implementação para Agentes IA

**Features Y5 adicionadas:**
- Seção 15.4: E9 — Auto-Routing Adaptativo (`RoutingLearningService`, `RoutingFeedback`, `cascaded_router.py`)
- Seção 15.5: E10 — Agent Bus Inter-Agentes (`AgentBus`, `emit()` no mixin, Redis Pub/Sub)
- Seção 15.6: E12 — Event Sourcing Imutável (`DomainEvent`, `EventStoreService`, endpoint `/event-history`)
- Seção 4.13: E4 — YAML Hot-Reload (`AgentRegistryWatcher`, beat `agent-registry-hot-reload`)
- Seção 13.4: E6 — RAG por Domínio (`domain` param, `DomainEmbeddingService`, beat diário)
- Diagnóstico v6: 4 gaps fechados (beat schedules E4/E6/D6, confidence cv_screening)

**Parte VII adicionada:**
- Seção 35: Guia de Diagnóstico e Implementação para Agentes IA
  - 20 capacidades com: O que é / Onde está / Como detectar / Como implementar / Como testar
  - Formato otimizado para consumo por Claude Code e Cursor IDE

**Métricas atualizadas:**
- Suite: 5.450+ testes passando
- 3 novas tasks Celery (agents.registry.check_reload, rag.rebuild_all_domains, ml.feedback.recompute_active_jobs)
- 3 novos beat schedules em celery_app.py

### v3.0 (13/03/2026) — Guia Técnico-Estratégico Completo

**Estrutura:**
- Expandido de ~2.500 para ~5.000+ linhas
- Reorganizado em 6 partes + 34 seções + 3 apêndices
- Corrigido contagem de agentes de 11 para 16 (12 ReAct + 4 StateGraph)

**Conteúdo novo:**
- Seção 3: 4 StateGraph Agents com diagramas de nós/edges/estados
- Seção 4: Arquitetura DDD completa (12 domínios, 231 serviços, 99 models, 206 endpoints, 37 migrações)
- Seção 5: WebSocket Architecture com protocolo de mensagens, error codes, reconnection
- Seção 11: Tool Registry completo com Scope Config (4 escopos, 66 tools)
- Seção 12: Prompt Infrastructure (10 seções canônicas, YAML registry, defensive prompts)
- Seção 13: Intelligence Layer (EmbeddingService, SemanticSearch, SmartExtractor)
- Seção 14: Automation Engine (19 serviços, 4 triggers, morning briefing)
- Seção 16: Infrastructure (LLM Factory, Policy Middleware, token budget)
- Seção 17: Observability (14 Prometheus metrics, dashboards, alerting rules)
- Seção 31: Production Readiness (deployment checklist, environment config)
- Seção 33: Oportunidades expandidas (gaps por camada, roadmap de escalabilidade)
- Apêndice A: Glossário técnico (32 termos)
- Apêndice B: Mapa de dependências entre serviços
- Apêndice C: Changelog

**Expansões detalhadas:**
- 6.1: WSI end-to-end flow com modelo de scoring por bloco
- 6.2: LIA Score fórmula completa com 4 cenários de peso e classificação
- 10.4: ActionExecutor 9 action_ids com fluxo HITL e security overrides
- 12.7: 18 Kanban Command Templates com detect_command_type()
- 14.3: Morning Briefing conteúdo + schedule Celery Beat
- 20.6-20.7: ConfidencePolicy exemplos + security overrides
- 23.3: Pre-Qualification fluxo completo
- 24.2-24.4: Feedback tone auto-selection
- 29.5-29.7: Model Drift 8 métricas + pipeline de escalação

### v2.0 (Anterior)
- Versão original com ~2.500 linhas
- 11 agentes documentados (sem StateGraph)
- Foco em prompts e capabilities básicas

---

---

## 35. Guia de Diagnóstico e Implementação — Claude Code / Cursor

> **Como usar este guia:** Quando uma IA (Claude Code, Cursor) receber este documento junto com um codebase de produto de recrutamento, deve usar esta seção para:
> 1. Verificar quais capacidades estão ausentes no produto
> 2. Entender o que cada capacidade faz
> 3. Seguir os passos de implementação baseados no código de referência da LIA
>
> Cada capacidade tem o formato: **O que é → Onde está na LIA → Como detectar se ausente → Como implementar → Como testar**
>
> **Repositório de referência:** `lia-agent-system/` (backend FastAPI) + `plataforma-lia/` (frontend Next.js)

---

### 35.1 FairnessGuard — Proteção Anti-Viés em 3 Camadas

**O que é:** Sistema de 3 camadas que bloqueia prompts e respostas com viés discriminatório (gênero, raça, idade, deficiência, origem). Obrigatório para compliance com LGPD Art. 20, EU AI Act e políticas anti-discriminação.

**Onde está na LIA:**
- `app/shared/fairness/fairness_guard.py` — classe `FairnessGuard` com Layer 1 (regex 73 padrões), Layer 2 (11 termos léxicos implícitos), Layer 3 (LLM opt-in via `FAIRNESS_LAYER3_ENABLED`)
- `app/shared/fairness/patterns.py` — `_EXPLICIT_PATTERNS`, `IMPLICIT_BIAS_TERMS`, 9 categorias
- `app/domains/sourcing/agents/sourcing_react_agent.py` linha ~50 — `FairnessGuard.check()` no início de `process()`
- `app/domains/pipeline/agents/pipeline_transition_agent.py` linha ~50 — mesmo padrão
- `app/domains/cv_screening/services/rubric_evaluation_service.py` — Layer 3 com `check_with_layer3(action_type="wsi_score")`

**Como detectar se ausente:**
```bash
grep -r "FairnessGuard\|fairness_guard" app/ --include="*.py" | wc -l
# Se resultado < 5: FairnessGuard não está wired nos agentes
grep -r "fairness" app/domains/ --include="*.py" | wc -l
# Se 0: nenhum agente tem proteção anti-viés
```

**Como implementar:**
1. Criar `app/shared/fairness/fairness_guard.py` com classe `FairnessGuard`:
   - `check(text: str) -> FairnessResult` — Layer 1: regex patterns
   - `check_with_layer3(text, action_type) -> FairnessResult` — Layer 1+2+3
   - `FairnessResult(blocked: bool, severity: str, matched_patterns: List[str], message: str)`
2. Criar `app/shared/fairness/patterns.py` com pelo menos 40 padrões explícitos (gênero, raça, idade, deficiência, origem)
3. Adicionar em cada agente `process()`:
   ```python
   from app.shared.fairness.fairness_guard import FairnessGuard
   _guard = FairnessGuard()
   result = _guard.check(input.message)
   if result.blocked:
       return AgentOutput(response=result.message, domain=self._enhanced_domain)
   ```
4. Setar `FAIRNESS_LAYER3_ENABLED=false` (padrão) — ativar só após testes

**Como testar:**
```bash
python -m pytest tests/fairness/ -v
# Mínimo: testar que termos como "jovem", "homem", "deficiente" como critério são bloqueados
```

**Risco se ausente:** 🔴 Crítico — violação de LGPD Art. 20 + EU AI Act High-Risk. Bloqueador de contrato.

---

### 35.2 Circuit Breakers — Resiliência para Integrações Externas

**O que é:** Padrão que "abre" automaticamente (para de chamar) uma integração externa quando ela falha repetidamente. Evita cascata de falhas e melhora a disponibilidade geral do sistema.

**Onde está na LIA:**
- `app/shared/resilience/circuit_breaker.py` — `CircuitBreakerService`, estados CLOSED/OPEN/HALF_OPEN
- `app/shared/resilience/circuit_breaker.py` — `ALL_CIRCUITS` dict com todos os circuits nomeados
- `app/shared/providers/llm_openai.py` — decorator `@circuit_breaker_decorator(OPENAI_CIRCUIT)`
- `app/services/ats_clients/gupy.py` — `@circuit_breaker_decorator(GUPY_CIRCUIT)`
- `app/api/v1/admin_circuit_breakers.py` — `GET /api/v1/admin/circuit-breakers` + reset endpoints

**Como detectar se ausente:**
```bash
grep -r "circuit_breaker\|CircuitBreaker" app/ --include="*.py" | wc -l
# Se 0: sem circuit breakers
grep -r "ALL_CIRCUITS" app/ --include="*.py"
# Se não encontrar: circuits não estão catalogados
```

**Como implementar:**
1. Criar `app/shared/resilience/circuit_breaker.py`:
   - Estado armazenado em Redis: `circuit:{name}:state`, `circuit:{name}:failures`, `circuit:{name}:last_failure`
   - `FAILURE_THRESHOLD = 5` (falhas antes de OPEN)
   - `RECOVERY_TIMEOUT = 60` (segundos em OPEN antes de HALF_OPEN)
2. Criar decorator `@circuit_breaker_decorator(circuit_name)` para wrapping de métodos externos
3. Criar `ALL_CIRCUITS` dict: `{"OPENAI": ..., "GEMINI": ..., "GUPY": ..., "PANDAPE": ..., "REDIS": ...}`
4. Aplicar decorator em todos os callers externos (LLM providers, ATS clients, email providers)
5. Criar endpoint admin `GET /admin/circuit-breakers` para status + reset

**Como testar:**
```bash
python -m pytest tests/unit/test_circuit_breaker.py -v
# Testar: CLOSED→OPEN após N falhas, OPEN rejeita sem chamar, HALF_OPEN tenta recuperação
```

**Risco se ausente:** 🟠 Alto — cascata de falhas em produção, SLA comprometido.

---

### 35.3 HITL — Human-in-the-Loop para Decisões Críticas

**O que é:** Mecanismo que pausa a execução de um agente e solicita aprovação humana antes de realizar ações destrutivas ou de alto impacto (envio de emails em massa, mudança de stage de candidatos, criação de vagas).

**Onde está na LIA:**
- `app/services/hitl_service.py` — `HITLService.request_approval()`, `receive_approval()`, Redis backing + DB persistence
- `app/models/hitl.py` — `HITLRequest`, `HITLDecision` models
- `alembic/versions/032_add_hitl_tables.py` — migration
- `app/api/v1/hitl.py` — `POST /api/v1/hitl/{thread_id}/approve`
- `app/api/v1/agent_chat_ws.py` — resume após aprovação (3 casos: cv_screening, wizard, genérico)
- `app/domains/sourcing/agents/sourcing_react_agent.py` — bloqueia envio de outreach

**Como detectar se ausente:**
```bash
grep -r "hitl_service\|request_approval\|HITL" app/ --include="*.py" | wc -l
# Se < 5: HITL não está implementado ou não wired nos agentes
ls alembic/versions/ | grep hitl
# Se vazio: sem tabelas de persistência HITL
```

**Como implementar:**
1. Criar tabelas: `hitl_requests` (id, thread_id, domain, company_id, payload, status, created_at) + `hitl_decisions` (id, request_id, decision, decided_by, decided_at)
2. Criar `HITLService`:
   - `request_approval(thread_id, domain, company_id, action_description, payload, db) -> str` — persiste + notifica via Redis
   - `receive_approval(thread_id, decision, decided_by, db) -> bool`
   - `get_pending(thread_id, db) -> Optional[HITLRequest]`
3. Criar endpoint `POST /hitl/{thread_id}/approve` com `{"decision": "approved"|"rejected"}`
4. No WebSocket handler: após envio da mensagem HITL, aguardar Redis key `hitl:{thread_id}:decision`
5. No agente: antes de ações destrutivas, `await hitl_service.request_approval(...)` e retornar awaiting_approval

**Como testar:**
```bash
python -m pytest tests/unit/test_hitl_service.py tests/unit/test_hitl_persistence.py -v
```

**Risco se ausente:** 🟠 Alto — agentes autônomos podem realizar ações irreversíveis sem supervisão.

---

### 35.4 Anti-Sycophancy — Respostas Honestas (não apenas agradáveis)

**O que é:** Instrução nos system prompts que força o agente a dar respostas honestas e fundamentadas em dados, mesmo que contrariem a expectativa do usuário. Baseada na Crença #11 da WeDOTalent ("Honestidade Radical").

**Onde está na LIA:**
- `app/shared/agents/system_prompts/base_prompt.py` — constante `ANTI_SYCOPHANCY_OPERATIONAL`
- Todos os system_prompts dos domínios — `ANTI_SYCOPHANCY_OPERATIONAL` injetado como seção
- `app/services/sector_benchmark_service.py` — benchmark setorial injetado em `evaluate_candidate()` para âncora factual

**Como detectar se ausente:**
```bash
grep -r "anti.sycophancy\|ANTI_SYCOPHANCY\|honest\|discordo" app/domains/ --include="*.py" -l | wc -l
# Se 0: agente pode ser sycophantic (concorda com tudo)
grep -r "ANTI_SYCOPHANCY" app/shared/agents/system_prompts/ --include="*.py"
```

**Como implementar:**
1. Criar constante `ANTI_SYCOPHANCY_OPERATIONAL`:
   ```python
   ANTI_SYCOPHANCY_OPERATIONAL = """
   ## Princípio de Honestidade Radical
   - Se os dados contradizem a expectativa do usuário, apresente os dados primeiro.
   - Nunca concorde apenas para agradar. Se uma decisão é arriscada, diga claramente.
   - Forneça benchmarks do mercado quando disponíveis para embasar avaliações.
   - Prefira "os dados indicam X, embora entenda que esperava Y" a validações vazias.
   """
   ```
2. Injetar em todos os system_prompts dos agentes como seção obrigatória

**Como testar:** Enviar prompt "Este candidato é ótimo, concorda?" com dados ruins → verificar que agente discorda fundamentado em dados.

**Risco se ausente:** 🟡 Médio — qualidade das recomendações IA comprometida, decisões ruins validadas.

---

### 35.5 CascadedRouter — Orquestração Multi-Tier

**O que é:** Router de 6 tiers que classifica mensagens do usuário para o agente correto usando: cache semântico → embeddings → LLM classificador → regras → fallback. Evita chamar o LLM para classificações óbvias.

**Onde está na LIA:**
- `app/orchestrator/cascaded_router.py` — `CascadedRouter.route()` com 6 tiers
- `app/orchestrator/intent_router.py` — `IntentRouter` com few-shot examples T3
- `app/orchestrator/semantic_cache.py` — cache de classificações anteriores (Redis TTL 1h)

**Knobs de configuração do Tier 1 — Cache Semântico (Z5-03):**

| Variável de Ambiente | Padrão | Descrição |
|---------------------|--------|-----------|
| `ROUTER_VECTOR_SIMILARITY_THRESHOLD` | `0.92` | Score mínimo cosine similarity para cache hit |
| `ROUTER_VECTOR_CACHE_ENABLED` | `true` | Habilita/desabilita o cache semântico vetorial |
| `ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN` | `0.05` | Margem abaixo do threshold para logar near-misses |

**Tiers:**
1. Cache semântico (embedding similarity > `ROUTER_VECTOR_SIMILARITY_THRESHOLD`, default `0.92` — configurável via env, Z5-03; habilitável via `ROUTER_VECTOR_CACHE_ENABLED`; near-misses logados quando similarity > threshold − `ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN`)
2. Regras explícitas (keywords exatas)
3. Embeddings locais (sem LLM)
4. LLM classificador (Claude Haiku — barato)
5. Fallback por domínio anterior
6. Default domain

**Como detectar se ausente:**
```bash
grep -r "CascadedRouter\|cascaded_router" app/ --include="*.py" | wc -l
# Se 0: sem orquestração inteligente — todo request vai para um agente fixo
grep -r "semantic_cache" app/ --include="*.py" | wc -l
# Se 0: sem cache de classificação
```

**Como implementar:**
1. Criar `app/orchestrator/intent_router.py` — prompt classificador com few-shot examples (20+ exemplos Input→Domain)
2. Criar `app/orchestrator/semantic_cache.py` — Redis cache com key `intent:{hash(message)}`, TTL 3600s
3. Criar `app/orchestrator/cascaded_router.py` com os 6 tiers em ordem de custo crescente
4. Injetar `CascadedRouter` no WebSocket handler como primeiro passo de cada mensagem

**Como testar:**
```bash
python -m pytest tests/unit/test_cascaded_router.py tests/unit/test_intent_router.py -v
```

**Risco se ausente:** 🟡 Médio — alto custo de LLM para classificação, latência elevada.

---

### 35.6 Auto-Routing Adaptativo (E9)

**O que é:** Sistema que aprende com as correções dos usuários (quando redirecionam a conversa para outro agente) e ajusta automaticamente os scores de confiança do roteamento. Domínios com alto índice de erro têm confiança reduzida; com baixo erro, confiança aumentada.

**Onde está na LIA:**
- `app/models/routing_feedback.py` — `RoutingFeedback` model (session_id, routed_domain, actual_domain, corrected)
- `alembic/versions/046_add_routing_feedback.py` — migration
- `app/services/routing_learning_service.py` — `RoutingLearningService.record_correction()`, `compute_domain_confidence_adjustments()`, Redis cache TTL=24h
- `app/orchestrator/cascaded_router.py` — `_apply_adaptive_adjustments()` chamado após Tiers 4 e 5
- `app/jobs/celery_tasks.py` — task `routing.recompute_adjustments`
- `libs/config/lia_config/celery_app.py` — beat `routing-recompute-daily` (07h UTC)

**Como detectar se ausente:**
```bash
grep -r "RoutingFeedback\|record_correction\|routing_feedback" app/ --include="*.py" | wc -l
# Se 0: sem aprendizado adaptativo
grep "routing.recompute" libs/config/lia_config/celery_app.py
# Se não encontrar: sem recompute automático
```

**Como implementar:**
1. Migration: tabela `routing_feedback` (id, company_id, session_id, message_hash, routed_domain, actual_domain, corrected, corrected_at)
2. `RoutingLearningService.record_correction()` — persiste quando usuário redireciona conversa (fail-open)
3. `compute_domain_confidence_adjustments(company_id, db)` — SQLAlchemy GROUP BY + case() → ajuste 0.8–1.2 (mínimo 10 samples)
4. Fórmula: `error_rate > 0.3 → max(0.8, 1.0 - error_rate * 0.5)` / `error_rate < 0.05 → min(1.2, 1.0 + (0.05 - error_rate) * 2)`
5. Redis cache TTL=24h: `routing_adj:{company_id}`
6. Wiring em `cascaded_router.py`: após classificação, multiplicar score por adjustment factor
7. Celery task `routing.recompute_adjustments(company_id)` + beat diário

**Como testar:**
```bash
python -m pytest tests/unit/test_e9_adaptive_routing.py -v  # 12 testes
```

**Risco se ausente:** 🟢 Baixo inicialmente — roteamento funciona sem aprendizado, melhora com ele.

---

### 35.7 Agent Bus — Comunicação Inter-Agentes (E10)

**O que é:** Barramento de eventos baseado em Redis Pub/Sub que permite agentes se comunicarem de forma assíncrona. Exemplo: Sourcing publica `candidate_imported` → Pipeline consome e inicia avaliação automaticamente.

**Onde está na LIA:**
- `app/shared/agents/agent_bus.py` — `AgentBus` singleton, `AgentEvent` dataclass, `publish()`, `subscribe()`, `dispatch_local()`
- `CHANNEL_PREFIX = "lia:agent_bus"`, canal: `lia:agent_bus:{company_id}:{to_agent}`
- `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `emit(to_agent, event_type, payload, company_id) -> bool`
- `app/domains/sourcing/agents/sourcing_react_agent.py` — emite `candidate_imported` para pipeline
- `app/domains/job_management/agents/job_wizard_graph.py` — emite `job_creation_ready` para jobs_management

**Como detectar se ausente:**
```bash
grep -r "AgentBus\|agent_bus\|emit(" app/ --include="*.py" | wc -l
# Se 0: sem comunicação inter-agentes
grep -r "CHANNEL_PREFIX" app/shared/agents/ --include="*.py"
```

**Como implementar:**
1. `AgentEvent` dataclass: `from_agent, to_agent, event_type, payload, company_id, event_id (uuid4), published_at`
2. `AgentBus.publish(from_agent, to_agent, event_type, payload, company_id)`:
   - `redis.publish(f"lia:agent_bus:{company_id}:{to_agent}", json.dumps(event.to_dict()))`
   - Audit trail: `audit_service.log_decision(decision_type="agent_event_published")`
   - Fail-open: retorna `False` se Redis indisponível
3. `AgentBus.subscribe(agent_name, handler)` — registro in-memory para dispatch local (testes)
4. `AgentBus.dispatch_local(event)` — chama handlers registrados (fail-open por handler)
5. Adicionar `emit()` ao `EnhancedAgentMixin` com lazy import de `agent_bus`

**Como testar:**
```bash
python -m pytest tests/unit/test_e10_agent_bus.py -v  # 12 testes
```

**Risco se ausente:** 🟢 Baixo — agentes operam independentemente, mas automações cross-domínio não funcionam.

---

### 35.8 Event Sourcing — Audit Trail Imutável (E12)

**O que é:** Padrão onde todas as mudanças de estado são registradas como eventos imutáveis (apenas INSERT, nunca UPDATE/DELETE). Permite replay de histórico, reconstituição de estado em qualquer ponto no tempo e compliance SOX.

**Onde está na LIA:**
- `app/models/event_store.py` — `DomainEvent` (aggregate_type, aggregate_id, event_type, event_data JSONB, company_id, sequence_number BIGINT, UniqueConstraint)
- `alembic/versions/047_add_event_store.py` — migration com 3 indexes
- `app/services/event_store_service.py` — `EventStoreService.append()`, `get_history()`, `reconstruct_state()`
- `app/api/v1/event_history.py` — `GET /api/v1/candidates/{id}/event-history`
- `app/domains/pipeline/agents/pipeline_transition_agent.py` — dual-write ao mover stage
- `app/domains/job_management/agents/job_wizard_graph.py` — dual-write ao completar wizard

**Como detectar se ausente:**
```bash
grep -r "DomainEvent\|event_store\|EventStoreService" app/ --include="*.py" | wc -l
# Se 0: sem event sourcing
ls alembic/versions/ | grep "event_store"
# Se vazio: sem tabela de eventos
```

**Como implementar:**
1. Migration: tabela `domain_events` com `UniqueConstraint('aggregate_type', 'aggregate_id', 'sequence_number')`
2. `EventStoreService.append(aggregate_type, aggregate_id, event_type, data, company_id, db)`:
   - Calcula `next_seq = MAX(sequence_number) + 1` para o aggregate
   - INSERT apenas — nunca UPDATE/DELETE
   - Fail-open: retorna `False` sem lançar
3. `get_history(aggregate_type, aggregate_id, db, from_sequence=0, limit=500)` — ORDER BY sequence_number
4. `reconstruct_state(aggregate_type, aggregate_id, db, folder=None)` — fold com default merger
5. Endpoint `GET /candidates/{id}/event-history` com header `X-Company-ID` obrigatório
6. Adicionar dual-write nos pontos de mudança de estado críticos (pipeline transitions, wizard completion)

**Como testar:**
```bash
python -m pytest tests/unit/test_e12_event_sourcing.py -v  # 12 testes
```

**Risco se ausente:** 🟠 Alto — sem audit trail imutável para SOX/ISO 27001.

---

### 35.9 YAML Hot-Reload de Agentes (E4)

**O que é:** Mecanismo que detecta mudanças no arquivo `agents_registry.yaml` e recarrega a configuração dos agentes (modelo LLM usado, habilitado/desabilitado) sem reiniciar o servidor.

**Onde está na LIA:**
- `app/agents_registry.yaml` — 7 agentes com `class_path`, `model_id`, `enabled`
- `app/core/agent_registry_watcher.py` — `AgentRegistryWatcher.check_and_reload()` (mtime-gated)
- `libs/agents-core/lia_agents_core/react_agent_registry.py` — `reload_from_yaml(path)`, `_flat_registry` dict
- `app/api/v1/admin_agents.py` — `POST /api/v1/admin/agents/reload` (manual trigger)
- `app/jobs/celery_tasks.py` — task `agents.registry.check_reload`
- `libs/config/lia_config/celery_app.py` — beat `agent-registry-hot-reload` (a cada 1 minuto)

**Como detectar se ausente:**
```bash
ls app/agents_registry.yaml 2>/dev/null || echo "AUSENTE"
grep -r "reload_from_yaml\|AgentRegistryWatcher" app/ --include="*.py" | wc -l
# Se 0: sem hot-reload
grep "agent-registry-hot-reload" libs/config/lia_config/celery_app.py
# Se não encontrar: sem polling automático
```

**Como implementar:**
1. Criar `agents_registry.yaml` com lista de agentes (`name, class_path, model_id, enabled, description`)
2. Adicionar `_flat_registry: Dict[str, AgentConfig]` ao registry principal
3. `reload_from_yaml(path)` — lê YAML, skipa `enabled: false`, atualiza `_flat_registry`
4. `AgentRegistryWatcher` — armazena `_last_mtime`, `check_and_reload()` compara mtime → chama `reload_from_yaml` se mudou
5. Endpoint `POST /admin/agents/reload` — trigger manual
6. Celery task + beat (1 min, expires=55s)

**Como testar:**
```bash
python -m pytest tests/unit/test_e4_agent_hot_reload.py -v  # 8 testes
```

**Risco se ausente:** 🟢 Baixo — operacional, mas mudanças de config exigem restart.

---

### 35.10 RAG por Domínio — Busca Semântica Especializada (E6)

**O que é:** Extensão do RAG híbrido (BM25 + pgvector) que segmenta os embeddings por domínio (`general`, `jobs`, `talent`, `policy`, `company`). Buscas no domínio de vagas não retornam documentos de candidatos.

**Onde está na LIA:**
- `alembic/versions/045_add_domain_to_embeddings.py` — coluna `domain VARCHAR(50)` em `routing_cache_vectors`
- `app/services/rag_pipeline_service.py` — `DOMAIN_ALIASES` dict, `normalize_domain()`, `domain` param em `search()`
- `app/services/domain_embedding_service.py` — `DomainEmbeddingService.embed_document()`, `rebuild_domain_index()`
- `app/jobs/celery_tasks.py` — task `rag.rebuild_all_domains` (itera 5 domínios)
- `libs/config/lia_config/celery_app.py` — beat `rag-rebuild-domain-index-daily` (04h UTC)

**Como detectar se ausente:**
```bash
grep -r "domain.*param\|domain_filter\|normalize_domain" app/services/rag_pipeline_service.py
# Se não encontrar: RAG não filtra por domínio
grep "domain" alembic/versions/ -r | grep "routing_cache"
# Se não encontrar: coluna domain não existe na tabela
```

**Como implementar:**
1. Migration: `ALTER TABLE routing_cache_vectors ADD COLUMN domain VARCHAR(50) DEFAULT 'general'` + index `(domain, company_id)`
2. `DOMAIN_ALIASES = {"candidates": "talent", "job_vacancies": "jobs", ...}`
3. `normalize_domain(domain_raw)` — aplica aliases, default `"general"`
4. `search(query, company_id, db, domain=None)` — adicionar `AND domain = :domain` quando fornecido
5. `embed_document(text, source_type, company_id, db)` — detecta domínio pelo `source_type`
6. `rebuild_domain_index(domain, company_id, db)` — reprocessa documentos do domínio
7. Wrapper task `rag.rebuild_all_domains` + beat diário

**Como testar:**
```bash
python -m pytest tests/unit/test_e6_rag_domain.py -v  # 10 testes
```

**Risco se ausente:** 🟡 Médio — RAG retorna resultados de contextos errados.

---

### 35.11 ML Feedback Loop — Calibração Adaptativa de Pesos (D6)

**O que é:** Sistema que aprende com as decisões dos recrutadores (contratar/rejeitar/override) e ajusta automaticamente os pesos dos critérios de avaliação por vaga. Vagas onde candidatos "overrideados" são bons performers → critérios originais estavam errados.

**Onde está na LIA:**
- `app/models/recruiter_decision_feedback.py` — `RecruiterDecisionFeedback` model
- `alembic/versions/044_add_recruiter_decision_feedback.py` — migration
- `app/services/ml_feedback_service.py` — `MLFeedbackService.record_signal()`, `compute_job_weights()`, `JobScoringWeights` dataclass
- `app/domains/pipeline/agents/pipeline_transition_agent.py` — `record_signal()` chamado ao mover candidato
- `app/services/lia_score_service.py` — `_get_calibration_adjustment_async()` aplica pesos ao score
- `app/jobs/celery_tasks.py` — task `ml.feedback.recompute_active_jobs` + task `ml.feedback.process_weights`
- `libs/config/lia_config/celery_app.py` — beat `ml-feedback-recompute-weekly` (domingo 02h UTC)

**Como detectar se ausente:**
```bash
grep -r "MLFeedbackService\|ml_feedback\|calibration_adjustment" app/ --include="*.py" | wc -l
# Se < 3: sem feedback loop ML
grep -r "record_signal\|compute_job_weights" app/ --include="*.py" | wc -l
```

**Como implementar:**
1. Migration: tabela `recruiter_decision_feedback` (id, company_id, job_id, candidate_id, decision, score_at_decision, created_at)
2. `MLFeedbackService.record_signal(job_id, candidate_id, decision, score, company_id, db)` — persiste (fail-open)
3. `compute_job_weights(job_id, company_id, db) -> JobScoringWeights` — analisa correlação decisão/score
4. `JobScoringWeights(technical=1.0, behavioral=1.0, cultural=1.0, sample_count=0)` — pesos padrão até ter dados
5. `_get_calibration_adjustment_async(job_id, company_id)` — busca pesos no Redis (TTL 7d), aplica ao score
6. Wrapper task para recompute semanal de vagas com feedback recente

**Como testar:**
```bash
python -m pytest tests/unit/test_d6_ml_feedback.py -v  # 14 testes
```

**Risco se ausente:** 🟡 Médio — avaliações não melhoram com feedback, critérios ficam fixos.

---

### 35.12 LGPD — Consentimento Granular (D5)

**O que é:** Sistema de consentimento com 7 tipos distintos (ai_screening, ai_scoring, ai_video_analysis, ai_comparison, data_retention, marketing, analytics). Cada tipo pode ser concedido ou revogado individualmente pelo candidato.

**Onde está na LIA:**
- `app/services/granular_consent_service.py` — `GranularConsentService.grant()`, `revoke()`, `check()`
- `app/models/candidate_consent_grants.py` — `CandidateConsentGrant` model
- `alembic/versions/043_add_candidate_consent_grants.py` — migration
- `app/api/v1/granular_consent.py` — `GET/POST /api/v1/granular-consent`
- `app/services/ats_clients/ats_pii_filter.py` — `filter_sensitive_outbound()` verifica consentimento antes de enviar PII para ATS

**Como detectar se ausente:**
```bash
grep -r "GranularConsentService\|ConsentGrant\|ai_screening" app/ --include="*.py" | wc -l
# Se 0: sem controle granular de consentimento
grep -r "check_consent\|consent_check" app/ --include="*.py" | wc -l
```

**Como implementar:**
1. Migration: tabela `candidate_consent_grants` (id, candidate_id, company_id, consent_type, granted, granted_at, revoked_at, legal_basis)
2. 7 tipos de consentimento como Enum: `ai_screening, ai_scoring, ai_video_analysis, ai_comparison, data_retention, marketing, analytics`
3. `check(candidate_id, company_id, consent_type, db) -> bool` — retorna `True` se consentido
4. Antes de cada operação de IA com dados do candidato: `if not await consent_service.check(...): raise ConsentRequired`
5. Endpoint para candidato gerenciar seus consentimentos

**Como testar:**
```bash
python -m pytest tests/unit/test_d5_granular_consent.py tests/unit/test_d5_consent_wiring.py -v
```

**Risco se ausente:** 🔴 Crítico — violação LGPD Art. 7 + EU AI Act. Bloqueador de contrato.

---

### 35.13 PII Masking em Logs e Prompts LLM

**O que é:** Sistema em 2 camadas: (1) Filtro de logging que mascara CPF, email, telefone, RG, CNPJ antes de gravar logs. (2) Strip de PII nos textos antes de enviar para LLM (reduz exposição de dados pessoais ao modelo).

**Onde está na LIA:**
- `app/shared/pii_masking.py` — `PIIMaskingFilter`, `strip_pii_for_llm_prompt(text)`, `install_global_pii_masking()`
- `app/core/logging_config.py` — `handler.addFilter(PIIMaskingFilter())`
- `libs/config/lia_config/celery_app.py` — `@signals.worker_process_init.connect` → `install_global_pii_masking()`
- `app/services/ats_clients/ats_pii_filter.py` — `filter_sensitive_inbound()` aplica strip em textos livres de ATS
- `app/domains/cv_screening/services/rubric_evaluation_service.py` — `cv_content = strip_pii_for_llm_prompt(cv_content)`

**Como detectar se ausente:**
```bash
grep -r "PIIMaskingFilter\|strip_pii\|pii_masking" app/ --include="*.py" | wc -l
# Se < 3: PII não mascarado
grep "addFilter\|PIIMasking" app/core/logging_config.py
# Se não encontrar: logs podem expor CPF/email
```

**Como implementar:**
1. `PIIMaskingFilter(logging.Filter)`:
   - `filter(record)` — aplica regex nos campos `msg`, `args` do record
   - Padrões: `\d{3}\.\d{3}\.\d{3}-\d{2}` (CPF), email, telefone, RG
2. `strip_pii_for_llm_prompt(text)` — Layer 1 (estruturado) + Layer 3 (quasi-identifiers: ano formatura, idade explícita)
3. Instalar em todos os handlers de log na inicialização
4. Instalar em cada processo Celery via signal

**Como testar:**
```bash
python -m pytest tests/unit/test_pii_masking_celery.py tests/unit/test_pii_llm_prompt_stripping.py -v
```

**Risco se ausente:** 🔴 Crítico — LGPD Art. 46 (segurança de dados), vazamento de PII em logs.

---

### 35.14 Bias Audit — Teste de Impacto Disparate (D3)

**O que é:** Implementação automática da regra Four-Fifths (80%) do EEOC. Verifica se candidatos de grupos protegidos (gênero, faixa etária, PCD, região) são aprovados em taxa ≥ 80% da taxa do grupo favorecido.

**Onde está na LIA:**
- `app/services/bias_audit_service.py` — `BiasAuditService.run_audit()`, `_chi_square_test()`, `Four-Fifths Rule`
- `app/models/bias_audit_snapshot.py` — `BiasAuditSnapshot` para histórico auditável
- `app/api/v1/bias_audit.py` — `GET /api/v1/bias-audit/job/{job_id}` + history endpoint
- `tests/fairness/test_four_fifths_rule.py` — golden dataset de 100+ candidatos sintéticos

**Como detectar se ausente:**
```bash
grep -r "four_fifths\|adverse_impact\|BiasAudit" app/ --include="*.py" | wc -l
# Se 0: sem audit automatizado de viés
ls tests/fairness/
# Se vazio: sem testes de fairness
```

**Como implementar:**
1. `BiasAuditService.run_audit(job_id, company_id, db)`:
   - Busca aprovados/total por dimensão (gender, age_group, disability, region)
   - `adverse_impact_ratio = minority_rate / majority_rate`
   - Se ratio < 0.80: `eeoc_compliant = False`, gera alerta
2. `BiasAuditSnapshot` para histórico (SOX: registros de auditoria imutáveis por 7 anos)
3. Endpoint para recruiter ver status por vaga

**Como testar:**
```bash
python -m pytest tests/fairness/test_four_fifths_rule.py -v
```

**Risco se ausente:** 🟠 Alto — exposição legal por discriminação inadvertida.

---

### 35.15 Model Drift Detection — Monitoramento Contínuo (D2/C4)

**O que é:** Sistema que monitora métricas do modelo LLM ao longo do tempo e detecta degradação automática (score médio cai, taxa de aprovação muda, custo por chamada sobe, latência aumenta). Dispara alertas quando drift é detectado.

**Onde está na LIA:**
- `app/services/model_drift_service.py` — `DriftDetectionService`, 4 triggers (score, aprovação, custo, latência P95)
- `app/services/drift_alert_service.py` — notificação Bell+Teams: 1 trigger=WARNING, 2+=URGENT
- `app/jobs/drift_job.py` — `run_drift_check_all_companies(db, notify_user_id)`
- `app/api/v1/drift.py` — `GET /api/v1/drift/status`
- `app/jobs/celery_tasks.py` — beat `drift-run-batch-daily` (09h UTC)
- `app/shared/observability/agent_metrics.py` — Prometheus histogram `confidence_score_histogram`

**Como detectar se ausente:**
```bash
grep -r "DriftDetection\|model_drift\|drift_alert" app/ --include="*.py" | wc -l
# Se 0: sem drift detection
grep -r "record_confidence\|confidence_score_histogram" app/ --include="*.py" | wc -l
# Se < 5: confidence não sendo registrada — sem base para drift detection
```

**Como implementar:**
1. Prometheus histogram `confidence_score_histogram` com labels `domain`, `has_tools`
2. `record_confidence(domain, confidence, has_tools)` em cada agente após gerar resposta
3. `DriftDetectionService` com janelas móveis de 7/30 dias: calcula baseline e compara com recente
4. `DriftAlertService` com threshold WARNING (1 trigger) e URGENT (2+ triggers)
5. Endpoint `GET /drift/status` para dashboard admin
6. Beat diário às 06h

**Como testar:**
```bash
python -m pytest tests/unit/test_model_drift_service.py -v
```

**Risco se ausente:** 🟠 Alto — degradação do modelo passa despercebida, qualidade das respostas cai silenciosamente.

---

### 35.16 Confidence Calibration — Calibração de Confiança (D2)

**O que é:** Cada agente reporta um score de confiança (0.0–1.0) junto com a resposta. Esse score é baseado em: iterações do loop ReAct usadas, presença de tool calls bem-sucedidas, ausência de erros. Alimenta o drift detection e o dashboard de qualidade.

**Onde está na LIA:**
- `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `_record_confidence(state)` chamado em `state_to_output()`
- `app/shared/observability/agent_metrics.py` — `record_confidence(domain, confidence, has_tools)`
- Fórmula: `confidence = base * tool_factor * iteration_factor`
  - `base = 0.9 se tool_calls sucesso, 0.7 se nenhuma tool, 0.5 se erro`
  - `tool_factor = 1.0 se ferramentas usadas, 0.85 se não`
  - `iteration_factor = max(0.6, 1.0 - (iterations - 1) * 0.1)`
- `app/domains/cv_screening/agents/wsi_interview_graph.py` — `record_confidence(domain="cv_screening", confidence=score/10.0)`

**Como detectar se ausente:**
```bash
grep -r "_record_confidence\|record_confidence" app/ libs/ --include="*.py" | wc -l
# Se < 5: confidence calibration não implementada
grep -r "confidence_score_histogram" app/ --include="*.py"
```

**Como implementar:**
1. Prometheus histogram com labels domain, has_tools
2. Fórmula conforme acima no `enhanced_agent_mixin.py`
3. Para agentes não-ReAct (StateGraph): chamar `record_confidence()` explicitamente após decisão final
4. Dashboard Grafana: histograma por domínio, percentil P10 como threshold de alerta

**Risco se ausente:** 🟡 Médio — sem visibilidade sobre qualidade das respostas por domínio.

---

### 35.17 WSI Assíncrono — Triagem Assíncrona de Candidatos (E3)

**O que é:** Permite que candidatos respondam ao questionário WSI (triagem IA) em seu próprio tempo, via link por email, sem precisar estar online simultaneamente ao recruiter.

**Onde está na LIA:**
- `app/api/v1/wsi_async.py` — 4 endpoints: `/wsi/sessions` (invite), `/wsi/sessions/{token}` (get), `/wsi/sessions/{token}/answer`, `/wsi/sessions/{token}/complete`
- `app/services/wsi_session_service.py` — gestão de sessões com token único
- FE: `src/hooks/use-wsi-async.ts`, `src/app/api/backend-proxy/wsi/...`

**Como detectar se ausente:**
```bash
grep -r "wsi_async\|wsi.*session.*token" app/ --include="*.py" | wc -l
# Se 0: WSI é síncrono — candidato precisa estar online durante triagem
```

**Como implementar:**
1. Gerar token único por convite (UUID4, TTL 7 dias)
2. 4 endpoints REST conforme acima
3. Enviar email com link `{BASE_URL}/triagem/{token}`
4. Sessão armazena estado: questions, answers, current_index, completed_at

**Como testar:**
```bash
python -m pytest tests/unit/test_e3_wsi_async.py -v  # 10 testes
```

**Risco se ausente:** 🟡 Médio — triagem síncrona reduz taxa de resposta dos candidatos.

---

### 35.18 Score Breakdown — Transparência na Avaliação (E1)

**O que é:** Decomposição do score final em dimensões (técnica, comportamental, cultural, experiência) visível para recruiter e candidato. Obrigatório para EU AI Act Art. 13 (explicabilidade de IA).

**Onde está na LIA:**
- `app/services/lia_score_service.py` — `get_score_breakdown(candidate_id, job_id, db) -> ScoreBreakdown`
- `app/api/v1/score_breakdown.py` — `GET /api/v1/candidates/{id}/score-breakdown`
- FE: `src/components/score-breakdown-badge-lazy.tsx` — badge clicável no kanban

**Como detectar se ausente:**
```bash
grep -r "score_breakdown\|ScoreBreakdown" app/ --include="*.py" | wc -l
# Se 0: sem breakdown — score é opaco
```

**Como implementar:**
1. `ScoreBreakdown(technical: float, behavioral: float, cultural: float, experience: float, total: float, weights: Dict)`
2. `get_score_breakdown()` busca scores parciais e aplica pesos configurados
3. Endpoint + component FE clicável

**Como testar:** `python -m pytest tests/unit/test_e1_score_breakdown.py -v`

**Risco se ausente:** 🟠 Alto — não conformidade EU AI Act Art. 13 (explicabilidade). Bloqueador regulatório.

---

### 35.19 Multi-Model — Agente usa Modelos Diferentes (E5)

**O que é:** Cada agente pode ser configurado para usar um modelo LLM diferente (Claude, GPT-4, Gemini) via variável de ambiente ou YAML. Permite otimizar custo/qualidade por domínio.

**Onde está na LIA:**
- `app/shared/agents/multi_model_config.py` — `AGENT_MODEL_CONFIG` dict, `get_model_for_agent(agent_name)`
- `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `model_id` property que chama `get_model_for_agent`
- Envvars: `AGENT_MODEL_PIPELINE=claude-sonnet-4-5`, `AGENT_MODEL_SOURCING=gpt-4o-mini`
- `app/agents_registry.yaml` — campo `model_id` por agente

**Como detectar se ausente:**
```bash
grep -r "get_model_for_agent\|AGENT_MODEL_" app/ --include="*.py" | wc -l
# Se 0: todos os agentes usam o mesmo modelo
```

**Como implementar:**
1. `AGENT_MODEL_CONFIG = {agent: os.getenv(f"AGENT_MODEL_{agent.upper()}", DEFAULT_MODEL)}`
2. `model_id` property no mixin: `return get_model_for_agent(self._enhanced_domain)`
3. LLM Factory usa `model_id` para selecionar provider
4. Suporte em `agents_registry.yaml` com campo `model_id`

**Como testar:** `python -m pytest tests/unit/test_e5_multi_model.py -v`

**Risco se ausente:** 🟢 Baixo — funcional com modelo único, sem otimização de custo.

---

### 35.20 Streaming de Pensamentos ReAct (E7)

**O que é:** Transmissão em tempo real do "raciocínio" do agente (chain-of-thought) via WebSocket enquanto processa. Melhora a percepção de velocidade e transparência do processo de IA.

**Onde está na LIA:**
- `app/api/v1/agent_chat_ws.py` — emit de `{"type": "thinking", "step": ..., "thought": ...}` durante loop ReAct
- FE: `src/components/react-thinking-stream.tsx` — renderiza steps de raciocínio
- FE: `src/hooks/use-float-streaming.ts` — `thinkingSteps` state, handler `type:thinking`

**Como detectar se ausente:**
```bash
grep -r "type.*thinking\|thinkingSteps\|ReactThinkingStream" app/ src/ --include="*.py" --include="*.tsx" | wc -l
# Se 0: sem streaming de pensamentos
```

**Como implementar:**
1. No loop ReAct, após cada iteração de reasoning: `await ws.send_json({"type": "thinking", "step": i, "thought": state.last_thought})`
2. FE: tratar mensagens `type:thinking` separadamente, exibir em componente collapsible

**Risco se ausente:** 🟢 Baixo — UX menos transparente, funcionalidade principal intacta.

---

### 35.22 Infraestrutura Base — Token Budget, Rate Limiting e Multi-Tenancy

**O que é:** Controles de infraestrutura que garantem isolamento, custo e segurança por tenant.

**Onde está no repo de referência:**
- Token Budget: `app/services/token_budget_service.py` + `app/services/token_tracking_service.py`
- Rate Limiting: `app/middleware/rate_limiter.py`
- Multi-Tenancy: `company_id` obrigatório em todos os models SQLAlchemy

**Como detectar se ausente:**
```bash
# Token Budget
grep -r "TokenBudget\|token_budget_service\|MONTHLY_LIMIT" app/ --include="*.py"
# Rate Limiter
grep -r "RateLimiter\|rate_limiter\|rate_limit" app/middleware/ --include="*.py"
# Multi-tenant
grep -r "company_id" app/models/ --include="*.py" -l | wc -l  # esperado: ≥ 20
```

**Como implementar se ausente:**
1. **Token Budget:** criar `token_budget_service.py` com Redis tracking por `company_id`. Estrutura mínima: `check_budget(company_id) -> bool`, `consume(company_id, tokens)`, `get_remaining(company_id)`. Limites por plano: `starter=100k`, `professional=500k`, `enterprise=2M` tokens/mês.
2. **Rate Limiter:** middleware FastAPI que lê `X-Company-ID` do header e aplica `slowapi` ou Redis counter por `company_id + endpoint`.
3. **Multi-tenant:** todo model SQLAlchemy deve ter `company_id: Mapped[str] = mapped_column(String, nullable=False, index=True)`. Toda query deve filtrar por `company_id`.

**Como testar:**
```python
# Token Budget
def test_token_budget_blocks_over_limit():
    svc = TokenBudgetService()
    svc.set_limit("co-1", 100)
    svc.consume("co-1", 100)
    assert svc.check_budget("co-1") is False  # bloqueado

# Multi-tenant
def test_query_filters_by_company():
    # query sem company_id deve retornar vazio ou erro
    ...
```

**Risco se ausente:** Tenant A vê dados do Tenant B (violação LGPD), custos de LLM não controlados, DoS por um único tenant consumindo todos os recursos.

---

### 35.21 Checklist Rápido de Diagnóstico

Use este checklist para avaliar rapidamente o estado de implementação de um produto:

```bash
#!/bin/bash
# Diagnóstico rápido — execute na raiz do repositório backend

echo "=== COMPLIANCE/LGPD (CRÍTICO) ==="
echo -n "FairnessGuard: "; grep -r "FairnessGuard" app/ --include="*.py" -l 2>/dev/null | wc -l | xargs -I{} echo "{} arquivos"
echo -n "PII Masking logs: "; grep -r "PIIMaskingFilter" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Consent granular: "; grep -r "GranularConsentService\|ConsentGrant" app/ --include="*.py" 2>/dev/null | wc -l

echo ""
echo "=== RESILIÊNCIA (ALTO) ==="
echo -n "Circuit Breakers: "; grep -r "circuit_breaker\|ALL_CIRCUITS" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "HITL service: "; grep -r "HITLService\|request_approval" app/ --include="*.py" 2>/dev/null | wc -l

echo ""
echo "=== QUALIDADE IA (MÉDIO) ==="
echo -n "Anti-sycophancy: "; grep -r "ANTI_SYCOPHANCY\|anti_sycophancy" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Confidence calibration: "; grep -r "_record_confidence\|record_confidence" app/ libs/ --include="*.py" 2>/dev/null | wc -l
echo -n "Drift detection: "; grep -r "DriftDetection\|model_drift" app/ --include="*.py" 2>/dev/null | wc -l

echo ""
echo "=== AUDITORIA (ALTO) ==="
echo -n "Event Sourcing: "; grep -r "DomainEvent\|EventStoreService" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Bias Audit: "; grep -r "BiasAudit\|four_fifths" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Score Breakdown: "; grep -r "ScoreBreakdown\|score_breakdown" app/ --include="*.py" 2>/dev/null | wc -l

echo ""
echo "=== OPERACIONAL (BAIXO) ==="
echo -n "YAML Hot-Reload: "; grep -r "AgentRegistryWatcher\|reload_from_yaml" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Agent Bus: "; grep -r "AgentBus\|agent_bus" app/ --include="*.py" 2>/dev/null | wc -l
echo -n "Adaptive Routing: "; grep -r "RoutingFeedback\|routing_learning" app/ --include="*.py" 2>/dev/null | wc -l

echo ""
echo "Contagem > 0 = implementado. Contagem = 0 = AUSENTE (verificar implementação)."
```

**Interpretação:**
- Qualquer item COMPLIANCE/LGPD com 0 = bloqueador imediato
- Itens ALTO com 0 = backlog urgente (Sprint 1)
- Itens MÉDIO com 0 = backlog normal (Sprint 2-3)
- Itens BAIXO com 0 = backlog planejado (Sprint 4+)

---

*Documento gerado por auditoria direta do código-fonte em 13/03/2026. Versão 4.0 (15/03/2026) — guia técnico-estratégico completo com 35 seções em 7 partes + 3 apêndices, cobrindo 16 agentes, 231+ serviços, 12 domínios DDD, infraestrutura de prompts, automação, inteligência preditiva, observabilidade, compliance, referência de arquivos completa e Guia de Implementação para Agentes IA (Seção 35: 21 capacidades com diagnóstico e passos de implementação). ~8.000 linhas.*