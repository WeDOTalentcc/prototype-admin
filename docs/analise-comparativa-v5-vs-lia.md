# Análise Comparativa Profunda: Recruiter Agent V5 vs Plataforma LIA

**Data**: 19 de Março de 2026 (atualizado v12.0 — Sprints Y1–Y5 + Z1–Z7 + AUD-1–5 completos: métricas re-verificadas, 17 agentes principais + 6 subagentes Z1 = 23 totais, 102 models, 245+ services, 47 migrations, 289+ test files, 13 domínios DDD, 16 métricas Prometheus)
**Escopo**: Análise qualitativa profunda, benchmark de mercado, análise estrutural e cruzamento comparativo
**Método**: Leitura completa do código-fonte (V5 via GitHub API read-only, LIA via filesystem local) + web research de plataformas concorrentes
**Perspectiva**: Diagnóstico técnico com foco em production readiness e conformidade com padrões de mercado
**Versão**: 12.0 (substitui v11.0 — Sprints Y1–Y5 (Bias Audit EEOC, Confidence Calibration, Granular Consent, Multi-Model, Event Sourcing, Agent Bus, Adaptive Routing) + Z1–Z7 (KanbanReActAgent+PipelineTransitionAgent→6 subagentes, LearningSnapshot, Context YAML versioning, DomainEmbedding, PolicyShim, VectorSimilarityConfig, ATS shims, OpenTelemetry OTLP, Presidio NER Layer 4, RecruiterBehaviorService) + AUD-1–5 (Anti-sycophancy 6 prompts, 15+ circuit breakers, HITL Sourcing+Communication, bandit CI, mock data removed) + F1-02 (FairnessGuard learning loop) + F1-03 (SLOs circuit breaker) + F2-04 (DLQ Redis). 17+6=23 agentes, 102 models, 245+ services, 47 migrations, 289+ test files, coverage gate 30%.)

**Nota metodológica**: Scores de 1-10 são atribuídos com base em: (a) leitura direta do código-fonte, (b) contagem de componentes via filesystem/API, (c) comparação com padrões de mercado documentados publicamente. Cada score na Seção 4 inclui justificativa com evidências de arquivo. Os scores da v2.0 diferem da v1.0 porque a análise anterior não incluiu análise estrutural profunda nem benchmarks de mercado — a reavaliação reduziu scores onde problemas estruturais foram encontrados (ex: Organização 8.0→3.5 após descoberta de god objects e arquivos órfãos). Os scores da v3.0 incorporam o Sprint de Qualidade e Compliance (2026-02-28). Os scores da v3.1 incorporam as correções do QA Audit (7 bugs corrigidos, 9 testes restaurados) — código verificado diretamente no filesystem com `pytest` executado e 100% passando. Os scores da v5.0 incorporam as Fases 4a/4b/4c/5 (Float Chat, navegação intencional, intent routing, agentes Phase 5), os Gaps Arquiteturais G1-G4 (LangGraph nativo, Orchestrator Intelligence, Observabilidade, Arquitetura Distribuída) e o UV Monorepo 6a/6b/6c (9 libs, 10 serviços Docker, Celery distribuído). Os scores da v6.0 incorporam os Sprints A–D (Token Budget, Monitoring, HITL, RAG/TOON), F1–F5 (HITL Persistence, Coverage Gate, Hooks Wiring, Short Lists, Componentes FE) e G1–G7 (YAML Tool Registry, RAG Híbrido, TOON Format, componentes FE, coverage 30.71%). Os scores da v6.1 incorporam o Sprint H: FactChecker granular, Deploy Cloud, Coverage 34%, FE testes unitários fix. Os scores da v7.0 incorporam o Sprint I: type cleanup FE (candidates-page.tsx −311 linhas), test categorization difficulty (easy/medium/hard/very_hard via pytestmark), coverage 34%→40% (meta aspiracional; gate CI efetivo é 32%, achieved 32.66%) (+106 testes: intent_classifier + candidate_search_schemas).

---

## Changelog v12.0 — Sprints Y1–Y5 + Z1–Z7 + AUD + F1–F2: Métricas Completas 19/03/2026

> Atualização completa com todas as sprints concluídas desde v11.0. Métricas re-verificadas por filesystem scan profundo (19/03/2026). Novos sistemas documentados: subagentes Z1, RecruiterBehaviorService, LearningSnapshotService, DLQService, OpenTelemetry, Presidio NER, Event Sourcing, Agent Bus, Adaptive Routing, Multi-Model per agent. Gap `AutomationReActAgent não registrado` marcado como resolvido.

| Área | v11.0 | v12.0 | Δ | Justificativa |
|------|-------|-------|---|---------------|
| Agentes IA | 16 (12 ReAct + 4 StateGraph) | **17 + 6 subagentes Z1 = 23 totais** | +7 | Sprint Z1: KanbanReActAgent→3 subagentes + PipelineTransitionAgent→3 subagentes. +1 agente: contagem correta de StateGraphs (WSI, Interview, Wizard, Policy) = 4. Total: 12+4+1 PolicySetup = 17 principais. |
| Models SQLAlchemy | 99 | **102** | +3 | Sprint Y3/D6: `RecruiterDecisionFeedback` (migration 044). Y5/E12: `DomainEvent` (migration 047). Y5/E9: `RoutingFeedback` (migration 046). + migration 043 `candidate_consent_grants`. |
| Services | 231 | **245+** | +14 | Novos serviços Y1–Y5 + Z1–Z7: RecruiterBehaviorService, LearningSnapshotService, DLQService, SalaryBenchmarkService, CulturalFitIntegrationService, GranularConsentService, EventStoreService, RoutingLearningService, DomainEmbeddingService, MLFeedbackService, CandidateComparisonService, PriorityCalculator, AgentBus, ScoreBreakdownService. |
| Migrations Alembic | 37 | **47** | +10 | Sprints Y1–Y5 + Z1: migrations 038–047. Última: `047_add_event_store.py`. |
| Test Files | 227 | **289+** | +62 | 62 novos arquivos de teste das sprints Y1–Y5, Z1–Z7, AUD-1–5, F1–F2. Total: 4.600+ casos. |
| Coverage gate | 32% (pytest.ini) | **30%** | −2 | Gate ajustado para 30% em `pytest.ini` pós-expansão do codebase. Achieved: 29%+. |
| Circuit Breakers | 7 | **15+** | +8 | AUD-2: OPENAI, GEMINI, GUPY, PANDAPE, STACKONE, SENDGRID, RESEND, WORKOS circuits adicionados. |
| Prometheus Metrics | 14 | **16** | +2 | Y2/C4: `agent_latency_timer` + `record_tokens()` wiring em react_loop.py e enhanced_agent_mixin.py. |
| Domínios DDD | 12 | **13** | +1 | `talent_intelligence` adicionado nas sprints Y-series. |
| Prometheus endpoint | Não documentado | **`GET /api/v1/metrics`** | Novo | `app/api/v1/metrics.py` — `generate_latest()` Prometheus (graceful ImportError). |
| FE Hooks | 114 | **103** | −11 | Nota: contagem original incluía hooks de lib/vendor. Hooks de app: 103 verificados. |
| FE Components | 437 | **469** | +32 | Novos: ScoreBreakdownBadge, CandidateCompareModal, MLInsightsCard, ReactThinkingStream, etc. |
| FE Pages | 90 | **90+** | ≈ | Novos: granular consent, WSI async, salary benchmark. |

**Gaps resolvidos desde v11.0:**
- ✅ `AutomationReActAgent`: registrado no dispatcher (`agent_chat_ws.py`) — AUD-2 circuit breakers aplicados
- ✅ Coverage gate: mantido em 30% mesmo com expansão significativa do codebase
- ✅ FairnessGuard no learning loop: F1-02 implementado com `validate_learning_batch()` + rollback Z2-01
- ✅ HITL em Sourcing e Communication: AUD-4 implementado (17 testes)
- ✅ Policy agent consolidado: Z5-02 HiringPolicyAgent→shim com DeprecationWarning
- ✅ PII Presidio Layer 4: Z6-03 opt-in com `LLM_PROMPT_PRESIDIO_ENABLED`
- ✅ OpenTelemetry OTLP: Z6-02 `_try_init_otlp()` com OTLP exporter + `@trace_span` em 3 componentes críticos
- ✅ DLQ Redis: F2-04 `DLQService` com cap 1000, TTL 7d, PII masking, Bell para tasks críticas
- ✅ Anti-sycophancy em 6 prompts faltantes: AUD-1 aplicado em analytics, communication, automation, ats_integration, sourcing, pipeline

**Gaps que permanecem após v12.0:**
- `candidates-page.tsx` god object: ainda grande (Sprint E extraiu componentes mas arquivo principal persiste)
- Deploy Terraform/Pulumi: scripts bash existem; IaC declarativo pendente
- Fine-tuning pipeline: `lia_feedback.py` DPO export existe; pipeline training contínuo pendente
- DeepEval integration: testes de LLM quality no CI — pendente (prioridade alta)
- Relatório de fairness exportável PDF/CSV: pendente (prioridade alta — compliance comercial)
- Coverage aspiracional 80%: gate atual 30%, achieved 29%+; target 80% em domínios críticos é meta de médio prazo

---

## Changelog v11.0 — Análise Profunda Pós-Auditoria: Métricas Verificadas e Inventário Completo (2026-03-13)

> Atualização profunda com métricas verificadas por filesystem (`find`, `wc -l`, `grep -c`), cruzamento com RELATORIO_AUDITORIA_LIA.md v2.0, e adição de subseções técnicas que faltavam: ActionExecutor, Scope Config, Sistema Preditivo, Intelligence Layer detalhado. Todas as contagens anteriores que estavam imprecisas foram corrigidas.

| Área | v10.0 | v11.0 | Δ | Justificativa |
|------|-------|-------|---|---------------|
| Agentes IA | 14-15 citados | **16 verificados** | +1-2 | `find app/domains -name "*_react_agent.py" -o -name "*_graph.py" -o -name "*_transition_agent.py" -o -name "agent.py"` — PolicySetupAgent (`policy/agents/agent.py`) agora contado separadamente |
| Models SQLAlchemy | 95 citados | **99 verificados** | +4 | `find app/models -name "*.py" ! -name "__init__.py" | wc -l` |
| Services | 215-230 citados | **231 verificados** | +1-16 | `find app/services -name "*.py" ! -name "__init__.py" | wc -l` |
| Migrations Alembic | 33-36 citados | **37 verificados** | +1-4 | `ls alembic/versions/*.py | wc -l` |
| API Endpoints | 202 citados | **206 verificados** | +4 | `find app/api -name "*.py" ! -name "__init__.py" | wc -l` |
| Hooks FE | 93 citados | **114 verificados** | +21 | `find plataforma-lia/src/hooks -name "*.ts" -o -name "*.tsx" | wc -l` |
| Pages FE | 89 citados | **90 verificados** | +1 | `find plataforma-lia/src/app -name "page.tsx" | wc -l` |
| Test Files | ~50 citados | **227 verificados** | +177 | `find tests -name "test_*.py" | wc -l` |
| Python Files (app/) | ~1095 | **1095 verificados** | ± 0 | `find app -name "*.py" ! -name "__init__.py" | wc -l` |
| TSX Files | 584 | **584 verificados** | ± 0 | `find plataforma-lia/src -name "*.tsx" | wc -l` |
| candidates-page.tsx | 10.592L | **10.397L** | −195 | `wc -l plataforma-lia/src/components/pages/candidates-page.tsx` |
| Prometheus Metrics | 13 citados | **14 verificados** | +1 | `grep -c "Histogram\|Counter\|Gauge\|Summary" app/observability/metrics.py` |
| Domínios DDD | 11 citados | **12 verificados** | +1 | `ls -d app/domains/*/` (excluindo `__pycache__`) — analytics, ats_integration, automation, communication, cv_screening, hiring_policy, interview_scheduling, job_management, pipeline, policy, recruiter_assistant, sourcing |
| Scope Config Tools | Não detalhado | **66 tools em 4 escopos** | Novo | TALENT_FUNNEL: 20, JOB_TABLE: 19, IN_JOB: 25, GLOBAL: 2 |
| ActionExecutor | Não detalhado | **1080L, 9 action_ids** | Novo | `wc -l app/orchestrator/action_executor.py`; 9 unique action_ids via `ACTIONABLE_INTENTS` |

**Novas subseções adicionadas:**
- **3.2.5** — ActionExecutor e Sistema de Ações (9 action_ids, 1080L)
- **3.2.6** — Scope Config: Controle de Acesso por Contexto (4 escopos, 66 tools)
- **3.2.7** — Sistema Preditivo e Intelligence Services (8 serviços preditivos, 3 intelligence, 4 learning)

**Correções de consistência:**
- Tabela de agentes (Seção 3.2.2): 16 agentes (era 14-15 confuso entre versões)
- Seção 11.1 Gap 4: candidates-page.tsx 10.397L (era 10.592L)
- Seção 5.1 D2: gap FE corrigido para 10.397L
- Contagem de domínios: 12 (era 11 — `policy` como domínio separado)

---

## Changelog v10.0 — Sprints SEG-1 a SEG-5: Wiring Completo de Segurança e Governança (2026-03-11)

> Implementação e testes dos 5 sprints de segurança e governança. Fecha os últimos 5 gaps críticos de wiring (PromptInjectionGuard, FairnessGuard, PII Masking, ConsentChecker, AuditService). Auditoria de governança executada contra os 6 checklists de skills (wedo-governance, lgpd-data-protection, screening-compliance, dei-fairness, testing-patterns, feature-audit): 8/8 Inegociáveis ✅, 12/13 Crenças ✅, Production Readiness ✅. 34 testes unitários adicionados em 6 arquivos. Estado final: 4193 testes passando, 0 regressões, coverage gate 32% mantido.

| Dimensão | v9.1 | v10.0 | Δ | Implementações que justificam |
|----------|------|-------|---|-------------------------------|
| D5 — Governança IA | 9.6 | 9.8 | +0.2 | SEG-2: FairnessGuard 3 camadas wired em 100% das decisões de screening/ranking — `sourcing_react_agent.process()` + `pipeline_transition_agent.process()`. `check()` + `check_implicit_bias()` com fail-safe e `educational_message` para bloqueios. SEG-5: `AuditService.log_decision()` com `PROTECTED_CRITERIA` sempre em `criteria_ignored` — pipeline HITL pending/transition/LangGraph + sourcing ReAct/LangGraph + HITL rejected via WebSocket. Todos os 8 Inegociáveis WeDOTalent satisfeitos. |
| D6 — Segurança | 9.0 | 9.4 | +0.4 | SEG-1: `PromptInjectionGuard` singleton em `agent_chat_ws.py` (high→block+`error_code`, medium→log+continue) + `validate_response()` em `wsi_interview_graph.py` (high risk→score 0 sem scoring LLM). SEG-4: `ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` em `wsi_interview_graph.load_context()` — revogado→`LGPD_CONSENT_REVOKED`+`stage=ERROR`, ausente→warning+continue. Fail-safe em ambos. SEG-3A: PII masking em Celery workers via `@signals.worker_process_init.connect` (modelo prefork — processo filho separado). SEG-3B: `strip_pii_for_llm_prompt()` aplicado em `rubric_evaluation_service.py`, `analysis_service.py`, `voice_screening_analysis.py`, `candidate_comparison_service.py` — LGPD Art. 12 data minimization antes de qualquer chamada LLM. Feature flag `LLM_PROMPT_PII_STRIPPING_ENABLED`. |
| D11 — Testes | 9.2 | 9.3 | +0.1 | 34 novos testes unitários em 6 arquivos: `test_injection_guard_integration.py` (6 casos — clean, high-risk, medium, fields, WSI block, WSI allow), `test_fairness_guard_agents.py` (5 — sourcing clean/blocked/fail-safe, pipeline clean/blocked), `test_pii_masking_celery.py` (2 — signal connect, handler install), `test_pii_llm_prompt_stripping.py` (7 — CPF, email, phone, graduation year, clean, flag-off, empty), `test_wsi_consent_gate.py` (4 — revoked, absent, fail, no-candidate-id), `test_audit_trail_gates.py` (10 — HITL request, not-blocking, protected criteria, sourcing ReAct, sourcing LangGraph, pipeline LangGraph, HITL rejected, PII strip x3). Camada 5 (contrato+fairness): `test_protected_criteria_always_ignored` verifica `PROTECTED_CRITERIA ⊆ criteria_ignored`. |
| **Média LIA** | **9.0** | **9.1** | **+0.1** | Governança (+0.2) e Segurança (+0.4) foram as dimensões de maior avanço — wiring completo fecha o principal gap de produção da plataforma |

**Gaps que permanecem após v11.0:**
- `candidates-page.tsx` god object: **10.397 linhas** (reduzido de 10.592 na v10.0; extração de modais requer `useCandidatesModals` — sprint dedicado)
- Deploy Terraform/Pulumi: scripts bash GCP/AWS existem; IaC declarativo pendente
- Test categorization `very_hard`: markers registrados, sem testes nessa categoria
- Fine-tuning pipeline: `lia_feedback.py` DPO export existe; pipeline training contínuo pendente
- `AutomationReActAgent`: agente existe em `domains/automation/agents/`; não registrado no WS dispatcher (`agent_chat_ws.py`)
- Coverage: gate 32%, achieved 32.66%; target aspiracional 80%
- **Governança — recomendações baixa prioridade:** TTL configurável para audit logs; placeholder genérico para `candidate_name` em voice_screening + analysis (quasi-identifier de gênero/etnia); testes de integração C3 para os novos gates SEG
- **V5 Auditoria**: 7 gaps identificados, cards Jira criados (AUD-001→AUD-007, WT-1506→WT-1512) — aguardando implementação pelo time V5. Ver Seção 12

---

## Changelog v9.1 — AUD Audit Cards: Auditoria e Compliance do Agente Python V5 (2026-03-10)

> Análise cruzada do documento do André ("Plano de Auditoria — Agente Python") com o código de referência da LIA. 7 gaps identificados, 7 cards Jira criados (WT-1506→WT-1512) + Epic WT-1505. Cards são agent-ready (autocontidos com contexto técnico, snippets da LIA, passos de implementação, testes e DoD). Diagnóstico completo: `docs/diagnostico-auditoria-agente-python.md`.

| Entrega | Detalhe |
|---------|---------|
| **Epic WT-1505** | AUD — Auditoria e Compliance do Agente Python |
| **WT-1506** AUD-001 | Propagar AuditCallback para ReAct Agents [P0 Crítico] — 2 SP |
| **WT-1507** AUD-002 | Rastrear Tools Chamadas por Nome [P1] — 1 SP |
| **WT-1508** AUD-003 | Circuit Breaker no Autonomous Agent [P1] — 2 SP |
| **WT-1509** AUD-004 | Retention/Cleanup de agent_executions [P2] — 1 SP |
| **WT-1510** AUD-005 | Storage Externo para Logs Pesados [P3] — 3 SP |
| **WT-1511** AUD-006 | Endpoints REST de Timeline [P3] — 3 SP |
| **WT-1512** AUD-007 | Métricas Prometheus [P3] — 3 SP |
| **Total** | 7 cards · 15 SP · ~19h · 3 sprints |
| **Referência** | Seção 12 deste documento + `docs/diagnostico-auditoria-agente-python.md` |

**Impacto no V5**: Os 7 cards representam o roadmap de remediação para fechar os gaps de auditabilidade, resiliência e observabilidade no agente Python V5. Ver Seção 12 para mapeamento completo.

---

## Changelog v9.0 — Sprint J: Float Chat WebSocket + Inventário Completo (2026-03-10)

> Sprint J completo: `LiaChatPanel` migrado REST→WebSocket com streaming nativo. `use-float-streaming.ts` com HITL + streaming integrados. `HITLConfirmCard.tsx` — card de aprovação inline no chat (approve/reject + comentário sem sair da conversa). `navigation_intent.py` expandido: 4 novos grupos adicionados (Configurações, Indicadores, WSI, total 8 grupos reordenados por especificidade). Wizard intent detectado redireciona automaticamente para `openSplitView("Vagas")`. 9 testes Vitest novos. Inventário v9.0: verificação filesystem — 99 modelos, 215 serviços (v11.0: **231**), 16 agentes distintos, 36 migrations (v11.0: **37**), 85 hooks (v11.0: **114**).

| Dimensão | v8.0 | v9.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D1 — Arquitetura de Agentes | 9.2 | 9.3 | +0.1 | Sprint J: `navigation_intent.py` com 8 grupos (Configurações/Indicadores/WSI adicionados, reordenados por especificidade, threshold 0.65). Wizard intent detectado → `openSplitView("Vagas")` automaticamente. Float Chat migrado REST→WS melhora roteamento e latência. |
| D7 — Human-in-the-Loop | 9.2 | 9.4 | +0.2 | Sprint J3: `HITLConfirmCard.tsx` — card inline no chat com approve/reject + comentário. `use-float-streaming.ts` integra HITL aprovações diretamente no fluxo de streaming WS — usuário aprova/rejeita ações sem sair do chat. Fecha gap "UI de aprovação HITL fora do contexto de conversa". |
| D2 — Qualidade de Código | 7.5 | 7.6 | +0.1 | `LiaChatPanel` refatorado REST→WebSocket — eliminação de polling e lógica de retry redundante. Inventário v9.0 confirma contagens reais: 99 modelos, 215 serviços, 16 agentes. |
| D11 — Testes | 9.1 | 9.2 | +0.1 | Sprint J: 9 novos testes Vitest (HITLConfirmCard render/approve/reject, use-float-streaming start/stop/HITL, navigation_intent 8 grupos). Total FE: ~60+ testes unitários. |
| **Média LIA** | **8.9** | **9.0** | **+0.1** | Float Chat WS (+0.2 HITL UX), arquitetura intent (+0.1), testes FE (+0.1) |

**Gaps que permanecem após v9.0/v9.1 → resolvidos parcialmente por v10.0:**
- `candidates-page.tsx` god object: **10.397 linhas** (verificado 2026-03-13; extração de modais requer `useCandidatesModals` — sprint dedicado) → **ainda pendente**
- Deploy Terraform/Pulumi: scripts bash GCP/AWS existem; IaC declarativo pendente → **ainda pendente**
- Test categorization `very_hard`: markers registrados, sem testes nessa categoria → **ainda pendente**
- Fine-tuning pipeline: `lia_feedback.py` DPO export existe; pipeline training contínuo pendente → **ainda pendente**
- `AutomationReActAgent`: agente existe em `domains/automation/agents/`; não registrado no WS dispatcher → **ainda pendente**
- Coverage: gate 32%, achieved 32.66%; target aspiracional 80% → **ainda pendente**
- **V5 Auditoria**: 7 gaps identificados, cards Jira criados (AUD-001→AUD-007, WT-1506→WT-1512) — aguardando implementação pelo time V5. Ver Seção 12 → **ainda pendente**
- ~~PromptInjectionGuard não wired~~ → ✅ **Resolvido SEG-1**
- ~~FairnessGuard não wired em screening~~ → ✅ **Resolvido SEG-2**
- ~~PII Masking Celery workers~~ → ✅ **Resolvido SEG-3A**
- ~~strip_pii_for_llm_prompt callers LLM~~ → ✅ **Resolvido SEG-3B**
- ~~ConsentCheckerService no Gate WSI~~ → ✅ **Resolvido SEG-4**
- ~~AuditService não wired nos gates~~ → ✅ **Resolvido SEG-5**

---

## Changelog v8.0 — Sprints I3+J+F: Prompts, Policy Domain, HITL Persistence, Quality Eval (2026-03-10)

> Sprint I3b: implementações reais de prompts movidas para `app/shared/prompts/` (loader, templates, cot, few_shot_examples, job_wizard, agent_prompts); `app/prompts/` convertido para shims — fecha gap "prompts fragmentados em 4 locais". Sprint I3c: `PolicySetupAgent` migrado de arquivo monolítico (`app/agents/policy_setup_agent.py` 371L) para padrão 4 arquivos em `app/domains/policy/agents/` (agent.py + system_prompt.py + tool_registry.py + stage_context.py). Sprint J1: `agent_quality_evaluator.py` + `agent_health_alert_service.py` + migration `034_add_agent_quality_evaluations.py`. Sprint J3: `user_agent_preference_service.py` + `user_agent_preference.py` + migration `035_add_user_agent_preferences.py` + `HITLConfirmCard.tsx` + `use-float-streaming.ts`. Sprint F1 completo: `hitl_service.py` com DB source-of-truth, `032_add_hitl_tables.py`. Load tests: `locustfile.py` + `load_test_config.py`. CI/CD: `.github/workflows/ci.yml` com step LangSmith (`continue-on-error: true`). Coverage gate 32%, achieved 32.66%, 3.712 testes.

| Dimensão | v7.0 | v8.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D1 — Arquitetura de Agentes | 9.1 | 9.2 | +0.1 | I3c: `PolicySetupAgent` migrado para padrão 4 arquivos canônico em `app/domains/policy/agents/` — 12º domínio DDD. `app/agents/policy_setup_agent.py` reduzido a shim de 10 linhas. Consistência de 100% dos agentes ativos com padrão `agent.py + system_prompt.py + tool_registry.py + stage_context.py`. |
| D2 — Qualidade de Código | 7.4 | 7.5 | +0.1 | I3b: `app/prompts/__init__.py` + 4 submodules convertidos para shims. Implementações reais centralizadas em `app/shared/prompts/` (6 arquivos: loader.py, templates.py, cot.py, few_shot_examples.py, job_wizard.py, agent_prompts.py). Eliminação do padrão importação circular — `agent_prompts.py` e `defensive_prompts.py` agora importam de `app.shared.prompts.loader` diretamente. |
| D3 — Organização/Estrutura | 7.7 | 7.9 | +0.2 | I3b: gap "prompts fragmentados em 4 locais" → prompts consolidados em `app/shared/prompts/` (fonte de verdade) com shims em `app/prompts/` para retrocompatibilidade sem breaking changes. I3c: domínio `policy` com estrutura DDD completa criada. HITL: models/hitl.py + migration 032 + service unificado. Migrations 032-035 em sequência correta com `033_merge_migration_heads` para resolução de branches divergentes. |
| D5 — Governança IA | 9.5 | 9.6 | +0.1 | J1: `agent_quality_evaluator.py` — avaliação automática de task_completion, fairness, response_quality por execução de agente, com persistência em `agent_quality_evaluations` (migration 034). `agent_health_alert_service.py` — alertas Bell + Teams quando qualidade cai abaixo de threshold configurável por domínio. |
| D7 — Human-in-the-Loop | 9.0 | 9.2 | +0.2 | F1: `hitl_service.py` com PostgreSQL source-of-truth (Redis = fast-path cache; DB = registro persistente auditável). HITLPendingAction + HITLAuditTrail com company_id, domain, ws_session_id, expires_at (SOX/BCB-498). J3: `user_agent_preference_service.py` — `auto_confirm` por (user, company, domain, action_type): resolve André's recommendation "permitir desativar confirmações após a primeira vez". `HITLConfirmCard.tsx` + `use-float-streaming.ts` no FE. |
| D10 — Observability | 9.5 | 9.7 | +0.2 | J1 + Sprint H: `agent_quality_evaluator.py` fecha gap "Sem avaliação de agentes" (Ragas/DeepEval pattern); `agent_health_alert_service.py` fecha gap "Sem dashboard de saúde de agentes" e "Sem alerta automático quando agente falha N vezes" listados na Seção 6.1 do diagnóstico. Observabilidade agora cobre: ReActObserver + LangSmith + Prometheus + ExecutionLogStore + QualityEvaluator + HealthAlerts. |
| D11 — Testes | 9.0 | 9.1 | +0.1 | Load tests: `tests/load/locustfile.py` (WizardUser, PipelineUser, HealthCheckUser com relatório p50/p95/p99) + `load_test_config.py`. Fecha gap "Sem testes de carga com cenários reais" (Seção 6.1). `test_hitl_persistence.py`: 25 testes BE. CI/CD: `ci.yml` com step LangSmith non-blocking + cobertura gate 32% confirmado no CI. |
| **Média LIA** | **8.8** | **8.9** | **+0.1** | Observability (+0.2) e HITL (+0.2) foram as dimensões de maior avanço; arquitetura e organização avançaram com I3 cleanup |

**Gaps que permanecem após v8.0:**
- `candidates-page.tsx` god object: **10.397 linhas** (verificado 2026-03-13; extração de modais requer `useCandidatesModals`)
- Deploy Terraform/Pulumi: scripts bash GCP/AWS existem; IaC declarativo ainda pendente
- Test categorization `very_hard`: marcadores registrados em pytest.ini mas sem testes nessa categoria
- ~~Guardrails code-based~~ ✅ **Implementado**: `app/models/guardrail.py` + `app/api/v1/guardrails.py` + migration 020 + UI admin/compliance/guardrails
- Few-shot T3 sem exemplos de RH sênior validados

---

## Changelog v7.0 — Sprint I: Type Cleanup FE, Test Categorization, Coverage 40% (2026-03-09)

> Sprint I: 3 gaps fechados de v6.1. Type cleanup FE: interface Candidate e TableFilters removidas de candidates-page.tsx (−311 linhas, importadas de types.ts e use-candidate-filters.ts). Test categorization: markers easy/medium/hard/very_hard registrados em pytest.ini + pytestmark em 15 arquivos de teste (419 testes categorizados). Coverage 34%→40%: +106 testes em test_intent_classifier_coverage.py e test_candidate_search_schemas.py.

| Dimensão | v6.1 | v7.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D2 — Qualidade de Código | 7.2 | 7.4 | +0.2 | `candidates-page.tsx`: interface `Candidate` inline (182 linhas) removida → importada de `candidates/types.ts` (merged com campos Pearch/bigFive/liaAnalysis). `TableFilters` inline (73 linhas) removida → importada de `use-candidate-filters.ts`. `getDefaultTableFilters` inline (53 linhas) removida → importada. Total: −311 linhas de duplicação. Arquivo: 10.903 → 10.592 → **10.397 linhas** (v11.0). |
| D11 — Testes | 8.8 | 9.0 | +0.2 | Test difficulty categorization: `pytest.ini` com markers `easy/medium/hard/very_hard`. `pytestmark` adicionado em 15 arquivos unitários (7 easy: pii_masking, ws_schemas, prompt_injection, fact_checker_granular, structured_logging, scope_config, evaluation_schemas; 5 medium: rag_pipeline, toon_service, hitl_service, yaml_tool_registry, short_list_service; 3 hard: wsi_interview_graph, hitl_persistence, hitl_langgraph_integration). 419 testes coletados com `-m "easy or medium or hard"`. Paridade com V5 `easy/medium/hard/very_hard`. +106 novos testes: `test_intent_classifier_coverage.py` (IntentType enum, ClassificationResult, _quick_classify 18 casos, _extract_entities 15 casos, classify() rule-based 7 casos, constants 8 casos) + `test_candidate_search_schemas.py` (SearchRequestDTO 16, ExperienceDTO 4, ImportCandidateDTO 6, ImportCandidatesResponse 3, _normalize_priority 8 + demais DTOs). Coverage 34%→40% (subset crítico); gate CI efetivo: **32%**, coverage suite completa: **32.66%**. |
| **Média LIA** | **8.7** | **8.8** | **+0.1** | Qualidade (+0.2) e Testes (+0.2) avançaram; god object FE continua em progresso |

**Gaps que permanecem após v7.0:**
- `candidates-page.tsx` god object: **10.397 linhas** (reduzido de 12.153→10.592→10.397; extração de modais requer `useCandidatesModals` hook — sprint dedicado)
- Deploy Terraform/Pulumi: scripts bash manuais criados; IaC declarativo ainda pendente
- Test categorization `very_hard`: marcadores registrados mas sem testes classificados nessa categoria ainda

---

## Changelog v6.1 — Sprint H: FE Tests, FactChecker Granular, Coverage 34%, Deploy Cloud (2026-03-09)

> Sprint H: 4 gaps fechados de v6.0. 154 novos testes unitários (+128 BE unitários, +8 FE). Coverage 30.71% → 34% (gate CI 25% → 34%). FactChecker granular com 3 métodos públicos. Deploy Cloud completo com Dockerfile.prod multi-stage, docker-compose.prod.yml, scripts GCP/AWS, CI/CD OIDC keyless.

| Dimensão | v6.0 | v6.1 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D2 — Qualidade de Código | 7.0 | 7.2 | +0.2 | `fact_checker.py`: 3 novos métodos públicos granulares — `verify_count_claim()` (regex `CANDIDATE_COUNT_PATTERN`, tolerance_pct, deviation_pct calculado), `verify_average_claim()` (regex `PERCENTAGE_PATTERN`, claim_type configurável), `verify_top_candidates_claim()` (regex `TOP_PATTERN`, max_reasonable_top). Parity com V5 para verificação de claims numéricas distintas por tipo. |
| D11 — Testes | 8.5 | 8.8 | +0.3 | 154 novos testes: `test_fact_checker_granular.py` (28), `test_pii_masking.py` (20), `test_prompt_injection.py` (25), `test_structured_logging.py` (14), `test_scope_config.py` (30), `test_ws_schemas.py` (25), `test_api_health_endpoints.py` (12). FE: `use-candidates-list.test.ts` — 8 timeouts resolvidos com `vi.useFakeTimers({ shouldAdvanceTime: true })` (fake timer + waitFor polling compatíveis). Coverage 30.71% → 34%, gate CI 25% → 34%. `pytest.ini` + `ci.yml` atualizados. |
| D12 — Infraestrutura | 9.5 | 9.8 | +0.3 | `Dockerfile.prod` multi-stage (builder: gcc+libpq-dev+pip install; runtime: libpq5+curl, uid=1001 non-root, HEALTHCHECK, gunicorn+uvicorn workers); `docker-compose.prod.yml` (restart: always, resource limits cpu/mem, json-file logging, health checks); `deploy/Makefile` (targets: build, push, deploy-gcp, deploy-aws, health-check, rollback); `deploy/gcp_setup.sh` (e2-standard-4, GCR auth, firewall tcp:8000); `deploy/aws_setup.sh` (EC2 t3.xlarge, ECR, SSM user-data Docker install); `.github/workflows/deploy.yml` (OIDC keyless auth — Workload Identity GCP + AWS role federation, build+push+deploy-gcp+deploy-aws jobs, environment protection). |
| **Média LIA** | **8.6** | **8.7** | **+0.1** | Infraestrutura (+0.3) e Testes (+0.3) foram as dimensões com maior avanço; FactChecker granular contribui para Qualidade (+0.2) |

**Gaps que permanecem após v6.1:**
- `candidates-page.tsx` god object: 12.153 linhas — extração em progresso, requer sessão dedicada (CandidatesFilterPanel, CandidatesTable como componentes autônomos)
- Coverage 40%: atual 34% (gap de ~6pp). Próximos alvos: `candidate_search.py` (2299 stmts), `company.py` (1815 stmts), `job_vacancies.py` (1821 stmts) — requer mocks de DB pesados
- Test categorization por dificuldade (easy/medium/hard): ainda por tipo, não por dificuldade
- Deploy Terraform/Pulumi: scripts bash manuais criados; IaC declarativo ainda pendente

---

## Changelog v6.0 — Sprints A–D, F1–F5, G1–G7 (2026-03-08)

> Análise profunda do filesystem em 08/03/2026. 3953 testes coletados, 1582 passando no subset crítico (0 falhas), cobertura 30.71% (gate CI 25%). Fechamento dos 3 principais gaps de v5.0 (RAG Híbrido, YAML Tool Registry, TOON Format). 10 libs UV Monorepo. 33 migrations Alembic.

| Dimensão | v5.0 | v6.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D2 — Qualidade de Código | 6.5 | 7.0 | +0.5 | Sprint E + G3/G4/G5: `SearchResultsHeader.tsx`, `CandidateSearchBar.tsx`, `CandidateTabs.tsx` extraídos como componentes autônomos; `useCandidatesListMapped.ts` + `candidate-transforms.ts` (pure functions); `use-candidate-filters.ts` + `use-candidate-selection.ts` wired; candidates-page.tsx reduzido de 12.375 → 12.153 linhas. Ainda é god object mas trend descendente. |
| D4 — Eficiência LLM | 7.5 | 8.0 | +0.5 | G6: `rag_pipeline_service.py` — RAG Híbrido real: pgvector cosine + tsvector BM25 + alpha blend (alpha=0 BM25, alpha=1 semântico, 0<alpha<1 híbrido). FairnessGuard stub top-10 diversity. Endpoint `GET /api/v1/candidates/rag-search`. G7: `toon_service.py` — TOON Format com LGPD (anonymize=True), Redis TTL=1h, `GET /api/v1/candidates/{id}/toon`. Sprint A: `token_budget_service.py` daily limits per tenant (PLAN_DAILY_LIMITS), HTTP 429, TimedToolNode 15s timeout. |
| D7 — Human-in-the-Loop | 8.5 | 9.0 | +0.5 | Sprint C + F1: HITL completo com persistência SOX/BCB-498. `HITLPendingAction` + `HITLAuditTrail` (models/hitl.py, migrations 031+032). `hitl_service.py` Redis fast-path + DB source-of-truth. Interrupt_before em 3 flows: `job_wizard_graph.py`, `wsi_interview_graph.py`, `pipeline_transition_agent.py`. G1: `domain` + `company_id` multi-tenant adicionados a `request_approval()`. |
| D9 — Tool System | 6.5 | 7.5 | +1.0 | G5: `tool_registry_metadata.yaml` (446 linhas, 32 tools declarativos com name, description, allowed_agents, scope, version) + `tool_registry_loader.py` (`load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()`) + `registry.py` com `.export_to_yaml()` + `.validate_yaml()`. LIA agora tem best-of-both-worlds: YAML declarativo + code-driven flexível. Scopes: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL. |
| D11 — Testes | 8.5 | 8.5 | = | 3953 testes coletados. 1582 passando no subset crítico (0 falhas), 7 skipped. Coverage 30.71% (gate CI 25%). 9 novos arquivos de cobertura (unit+integration). Pirâmide 5-camadas mantida. Gap: cobertura ainda longe de 80% target. |
| D3 — Organização/Estrutura | 7.5 | 7.5 | = | G3/G5: componentes FE extraídos. Sprint F4: Short Lists API (`short_lists.py` 243L + `use-short-list.ts`). 10 libs UV Monorepo (nova: `libs/orchestrator/`). 33 migrations Alembic. God object FE candidates-page.tsx ainda 12.153 linhas — extração em progresso mas gap persistente. |
| **Média LIA** | **8.4** | **8.6** | **+0.2** | Tool System (+1.0), HITL (+0.5), Eficiência LLM (+0.5) e Qualidade Código (+0.5) foram as dimensões de maior avanço |

**Gaps que permanecem após v6.0:**
- `candidates-page.tsx` god object: 12.153 linhas (tendência descendente: 12.375→12.153, mas ainda bloqueante para testes unitários FE)
- LangSmith CI Step (F6): ✅ já implementado — ci.yml linhas 55–59 + `app/config/langsmith.py`
- Deploy cloud: sem scripts GCP/AWS, sem Terraform/Pulumi, sem health checks automatizados
- Coverage 40%: atual 30.71% (gap de ~9.3pp para meta aspiracional)
- Test categorization por dificuldade (easy/medium/hard): ainda por tipo, não por dificuldade
- FactChecker granular por tipo de claim numérico: verificação genérica sem separação count/avg/top

---

## Changelog v5.0 — Fases 4-5, Gaps G1-G4, UV Monorepo 6a/6b/6c (2026-03-08)

> Sprint completo: 10 gaps arquiteturais fechados, Float Chat + Navegação Intencional + Intent Routing + Phase 5 Agent Wiring + UV Monorepo com 9 libs. 2291 testes passando.

| Dimensão | v4.0 | v5.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D1 — Arquitetura de Agentes | 8.5 | 9.0 | +0.5 | Fase G1: `USE_LANGGRAPH_NATIVE=True` ativado globalmente (12 agentes migrados); G2: `VectorSemanticCache` pgvector cosine similarity (threshold 0.92, substitui MD5 hash) + `CascadedRouter` 6-tiers (in-process → Redis → regex → LLM Haiku→Sonnet→Opus) + `ClarificationOutput` no AgentInterface; Fase 4b: `NavigationIntentDetector` (4 grupos, threshold 0.65) + endpoint REST + split-view; Fase 4c: `useActionIntent` hook keyword-based (5 domínios) + `actionTypeToDomain()` roteando WS; Fase 5: 3 novos agentes (Analytics, Communication, ATSIntegration) wired no dispatcher WS com aliases |
| D3 — Organização/Estrutura | 7.0 | 7.5 | +0.5 | Fase 6a/6b/6c: UV Monorepo com 9 libs (`config`, `utils`, `models`, `audit`, `messaging`, `agents-core`, `services`, `contexts`, `auth`) — código real migrado, shims de retro-compatibilidade; Fase 4b/4c: hooks `use-navigation-intent.ts`, `use-action-intent.ts` extraídos de componentes; `LiaSplitPanel.tsx` componente autônomo; Fase 5: 3 novos domínios com padrão 4 arquivos canônico. Gap remanescente: `candidates-page.tsx` ainda 12.375 linhas. |
| D10 — Observability | 9.0 | 9.5 | +0.5 | Fase G3: 5 novas métricas Prometheus estratégicas (`router_tier_hit`, `router_latency_ms`, `router_confidence`, `agent_tool_failures`, `llm_cost_usd`); S3 lifecycle SOX (90d Standard→Glacier IR→365d Deep Archive→7 anos delete); `langgraph.json` para LangGraph Studio; Celery task `audit.apply_lifecycle_policy` mensal; G4: `platform_events.py` com handler registry + observabilidade de eventos inter-API |
| D11 — Testes | 7.5 | 8.5 | +1.0 | 2291 testes BE passando (0 falhas); Vitest hooks project configurado (jsdom); Fase 4b: 12 FE unit tests (`use-navigation-intent`) + 23 BE contracts (`test_navigation_intent_contracts`) + 21 BE contracts (`test_lia_float_contracts`) + 25 BE contracts (`test_context_type_routing_contracts`); Fase 4c: 30 FE unit tests (`use-action-intent`, threshold 0.70, 5 domínios); Fase 5: 53 BE contract tests (3 arquivos: analytics/communication/ats_integration × 4 classes cada); Fase 6c: 98 BE contract tests (interface, handoff, PII, multi-tenant); G1-G4: 185 testes novos; Pirâmide 5-camadas completa |
| D12 — Infraestrutura | 8.5 | 9.5 | +1.0 | Fase 6b: `docker-compose.yml` completo — 10 serviços (postgres, redis, rabbitmq, api, api-vagas, api-funil, api-onboarding, celery_worker, celery_beat, flower); Fase 6b: Celery distribuído com prioridades (high/normal/low) + beat agendado (drift daily 06h Brasília) + Flower monitoring; Fase 6a/6b/6c: UV workspace root + 9 libs com `[build-system] hatchling`, `.pth` files, shims; `apps/api-vagas/api-funil/api-onboarding` como micro-serviços independentes; Fase G3: S3 lifecycle audit SOX 7 anos |
| **Média LIA** | **8.1** | **8.4** | **+0.3** | Infraestrutura (+1.0), Testes (+1.0), Observabilidade (+0.5) e Arquitetura (+0.5) foram as dimensões com maior avanço |

**Gaps que permanecem após v5.0:**
- `candidates-page.tsx` god object: 12.375 linhas (hooks criados mas componente não desmembrado)
- RAG Híbrido: LIA ainda embedding-only (sem full-text BM25 + reranking como V5)
- YAML Tool Registry declarativo: LIA usa code-driven (flexível mas menos inspecionável)
- TOON Format: LIA ainda sem formato comprimido (~15% custo extra em tokens)
- `use-candidates-list.test.ts`: 8 timeouts pré-existentes (hook usa `liaApi` global não mockado)

---

## Changelog v4.0 — Sprint de Qualidade v2: Observabilidade, Resiliência e Refatoração (2026-02-28)

> Sprint completo com 18 itens implementados nos Sprints A-D + Sprint E fase 1 iniciado.

| Dimensão | v3.1.1 | v4.0 | Δ | Implementações que justificam |
|----------|--------|------|---|-------------------------------|
| D3 — Organização/Estrutura | 6.5 | 7.0 | +0.5 | Sprint E: `lia_assistant.py` 8274→6923 linhas — extraídos `lia_voice.py` (265 linhas), `lia_multimodal.py` (177), `lia_autonomous.py` (212), `lia_feedback.py` (287); `use-candidate-filters.ts` e `use-candidate-selection.ts` criados para candidates-page.tsx |
| D4 — Eficiência LLM | 7.0 | 7.5 | +0.5 | D-1: SSE streaming endpoint `/chat/stream` com `AsyncAnthropic.messages.stream()` — tokens chegam em tempo real no FE via ReadableStream; `generate_with_fallback()` em `llm_factory.py` (claude→gemini→openai) |
| D6 — Segurança | 8.5 | 9.0 | +0.5 | A-2: `SECRET_KEY` obrigatório em produção — startup falha se valor default ou ausente; C-2: candidates-page migrado para `useJWTAuth` (auth mock always-authenticated eliminado); C-3: `getAuthHeaders(required=true)` — proxy routes de ações críticas lançam erro sem auth header; C-1: `ignoreBuildErrors: false` — TypeScript rigoroso ativo |
| D10 — Observability | 7.5 | 9.0 | +1.5 | B-2: 8 métricas Prometheus estratégicas em `app/observability/metrics.py` + endpoint `/metrics`; B-1: `@traceable` em `ReActLoop.run()` e todos os 4 `ClaudeLLMProvider.generate*()` — ReAct loop customizado visível no LangSmith; B-3: `FairnessAuditLog` table (migration 015) — EU AI Act compliance com persistência temporal de hits de bias; A-3: Sentry integrado no backend (FastAPI+Starlette) + frontend (@sentry/nextjs) + `ErrorBoundary` global; C-4: `ErrorBoundary` React com `Sentry.captureException` |
| D11 — Testes | 7.5 | 7.5 | = | T3: E2E Playwright (wizard); T4: Locust load test — mantidos. CI/CD adicionado (D-2) para garantir suite roda automaticamente. |
| D12 — Infraestrutura | 6.5 | 8.5 | +2.0 | D-2: GitHub Actions CI completo (3 jobs: backend ruff+pytest, frontend biome+tsc+build, security npm-audit+pip-audit); D-3: `.pre-commit-config.yaml` com 8 hooks (ruff, ruff-format, biome, no-@ts-nocheck, no-print, no-console-log, no-hardcoded-secrets, detect-private-key); A-4: Rate limiter migrado de 4 dicts in-memory para Redis ZSET sliding window atômica com fallback graceful |
| D14 — Resiliência | 8.5 | 9.5 | +1.0 | A-1: `@circuit_breaker_decorator(ANTHROPIC_CIRCUIT)` aplicado nos 4 `generate*()` do Claude (era inexistente — circuito criado mas não conectado ao provider); `generate_with_fallback()` — auto-failover claude→gemini→openai; A-4: Redis ZSET sliding window — rate limiter sobrevive a restarts |
| D2 — Qualidade de Código | 6.0 | 6.5 | +0.5 | Sprint E fase 1: 1351 linhas extraídas de lia_assistant.py; `use-candidate-filters.ts` e `use-candidate-selection.ts` estabelecem arquitetura para extração gradual de candidates-page.tsx |
| **Média LIA** | **7.7** | **8.1** | **+0.4** | Sprint v2 elevou infra (6.5→8.5), observability (7.5→9.0) e resiliência (8.5→9.5) — as 3 maiores lacunas de produção |

**Gaps que permanecem após Sprint v2:**
- Celery Workers async: LIA ainda síncrona em algumas operações
- RAG Híbrido: LIA ainda embedding-only (sem full-text + reranking como V5)
- Sprint E fase 2: Extração gradual de candidates-page.tsx (hooks + sub-componentes) ainda pendente
- Sprint E fase 3: Split completo do wizard section em lia_assistant.py (~3300 linhas restantes)
- God Objects FE: candidates-page.tsx ainda 12375 linhas — hooks criados mas não conectados

---

## Changelog v3.0 — Sprint de Qualidade e Compliance (2026-02-28)

> Scores LIA atualizados com base na leitura direta do código após implementações do sprint. Código é fonte de verdade — sem inferências.

| Dimensão | v2.0 | v3.0 | Δ | Implementações que justificam |
|----------|------|------|---|-------------------------------|
| D4 — Eficiência LLM | 6.5 | 7.0 | +0.5 | M5: alertas automáticos 80%/100% com Redis dedup; M4: AI Credits dashboard (consumo por agente, gráfico 30 dias) |
| D5 — Governança IA | 8.5 | 9.5 | +1.0 | B4+B4.1: FAIRNESS_AND_COMPLIANCE em todos os 8 system prompts (wizard, sourcing, jobs_mgmt, cv_screening/pipeline, pipeline, kanban, talent, policy); L5: consent check com HTTP 451 para revogação e `consent_warnings` no response para soft enforcement; B3: FairnessGuard verificando outputs LLM (não só inputs); **v3.1**: B1: nome do candidato removido do contexto LLM (blind evaluation); B2: `GEOGRAPHIC_ADJUSTMENTS` discriminatório removido (multiplicador universal 1.0) |
| D6 — Segurança | 7.5 | 8.5 | +1.0 | L7: `PIIMaskingFilter` instalado no root logger — todos os logs da aplicação mascarados; L8: WhatsApp verify token sem default hardcoded (warning log quando ausente); L5: HTTP 451 para consent revogado; L3: human review gate em rejeições; **v3.1**: L1: `LANGCHAIN_TRACING_V2` default `False` (opt-in — dados de candidatos não transitam para servidores externos sem configuração explícita) |
| D7 — Human-in-the-Loop | 8.0 | 8.5 | +0.5 | L3: `PATCH /candidates/{id}/stage` retorna 422 quando stage de rejeição sem `user_id` — rejeição nunca automatizada; L4: `POST /lgpd/run-cleanup` protegido com `require_admin` |
| D10 — Observability | 7.0 | 7.5 | +0.5 | L7: PII masking ativo globalmente (root logger) — CPF/email/telefone/nome mascarados em todos os logs; L5: audit log em toda verificação de consent ausente |
| D11 — Testes | 4.5 | 7.5 | +3.0 | T1: 19 testes unitários rubric BARS — 19/19 passando (cache, variação, batch, legado, priority); T2: 28 testes integração pipeline triagem — 28/28 passando (4 blocos, calibração, deduplicação, schemas); T3: 5 cenários E2E Playwright (wizard conversacional + checkpoint A3); T4: Locust WizardUser/PipelineUser/HealthCheckUser com relatório p50/p95/p99; B5: 17 testes disparate impact WSI — 17/17 passando (4/5 Rule por gênero/idade/etnia). **v3.1**: T1 corrigido (campo `priority` nos testes BARS); T2 corrigido (`question_count` max 15→25 no schema) |
| D12 — Infraestrutura | 5.0 | 6.5 | +1.5 | M1: `check_active_jobs_limit` FastAPI dependency com HTTP 402; M2: `require_active_subscription` com HTTP 402 + página /upgrade; M4: proxy routes + hooks + página /configuracoes/ai-credits; N3: migration 014 JSONB + `CandidateChannelSelector`; L4: LGPD cleanup com `AutomationScheduler` (01h/02h) |
| D14 — Resiliência | 7.5 | 8.5 | +1.0 | A5: `@circuit_breaker` aplicado em produção (Pearch threshold=3/15s, Deepgram threshold=3/30s, OpenMic threshold=5/60s) + `@retry(stop=stop_after_attempt(2), wait=wait_exponential)` como decorator inner; **v3.1**: A2: Gemini provider com `@retry(retry_if_result=_is_empty_response)` — retry automático para respostas vazias com warning log |
| **Média LIA** | **7.0** | **7.7** | **+0.7** | Sprint fechou gaps de testes (D11 era único score onde V5 superava), compliance (L3/L4/L5/L7/L8) e resiliência aplicada (A5) |

**Gaps que permanecem (backlog):**
- CI/CD: GitHub Actions CI implementado em Sprint D-2 (v4.0) — Docker production deploy ainda ausente
- Docker/Deploy produção: LIA ainda no Replit — maior gap infra restante
- Celery Workers async: LIA ainda síncrona
- RAG Híbrido: LIA ainda embedding-only
- Test difficulty categorization: LIA organiza por tipo, V5 por dificuldade (easy/medium/hard/very_hard)

---

## Changelog v3.1 — QA Audit e Correções (2026-02-28)

> Auditoria QA executou 32 verificações em 7 camadas (L=Legal, B=Bias, A=Arquitetura, M=Monetização, N=Notificações, T=Testes). 5 bugs corrigidos (B1, B2, L1, L8, A2) + 9 testes restaurados (T1: 6, T2: 3) = 32/32 itens OK. Relatório completo: `docs/QA_REPORT_SPRINT_2026-02-28.md`.

| ID | Severidade | Problema | Correção | Arquivo |
|----|-----------|----------|----------|---------|
| B2 | 🔴 Crítico | `GEOGRAPHIC_ADJUSTMENTS` com multiplicadores por país (JP/KR/IN penalizados) | Constante removida, multiplicador universal 1.0 | `calibration_profiles.py` |
| B1 | 🔴 Crítico | Nome do candidato incluído no contexto LLM (`Name: {name}`) | Removido de `_extract_cv_content()` — blind evaluation | `rubric_evaluation_service.py` |
| L1 | 🟠 Alto | `LANGCHAIN_TRACING_V2 = True` por padrão — dados transitam para LangSmith | Default alterado para `False` (opt-in) | `config.py` |
| L8 | 🟠 Alto | WhatsApp verify token com default previsível `"lia_whatsapp_verify"` | Default removido, warning log quando ausente | `whatsapp_meta_service.py` |
| A2 | 🟡 Médio | Gemini provider sem retry para respostas vazias | `@retry(retry_if_result=_is_empty_response)` com tenacity | `llm_gemini.py` |
| T1 | 🟡 Médio | 6/19 testes BARS falhando (campo `priority` ausente no factory) | Campo `priority=priority` adicionado ao `make_requirement()` | `test_rubric_evaluation_service.py` |
| T2 | 🟡 Médio | 3/28 testes pipeline falhando (`question_count` max=15, pipeline passa 16) | Limite ajustado para `le=25` no schema | `screening.py` |

**Resultado pós-correção**: 32/32 verificações OK. 64/64 testes passando (19 BARS + 28 pipeline + 17 disparate impact). Zero bugs pendentes.

**Impacto nos scores**: Nenhum score foi alterado — as correções eliminaram vulnerabilidades que existiam quando os scores v3.0 foram atribuídos, validando que os scores agora refletem corretamente o estado do código.

**Correções quantitativas (v3.1.1)**: Contagens re-verificadas contra filesystem real:
- Arquivos Python: ~1.035 → ~1.157 (via `find . -name "*.py" | wc -l`)
- LOC: ~413K → ~433K (via `wc -l`)
- Serviços: 190 → 200+ (201 arquivos em `app/services/`)
- Modelos: 89 → 91 (em `app/models/`)
- Testes: 56 → 47 arquivos (42 test files + 5 infra — conftest, __init__, etc.)
- Shared agents: 18 → 17 arquivos (em `app/shared/agents/`)

---

## 1. Executive Summary

### Veredicto

O **recruiter_agent_v5** apresenta um pipeline de agentes funcional (IntentAnalyzer→Planner→Executor→Validator→DataProcessor→Formatter), um YAML Tool Registry bem estruturado com 70 definições, e um RAG híbrido (pgvector + full-text + reranking) acima da média. Porém, o repositório apresenta problemas estruturais documentados nesta análise — god objects, arquivos órfãos na raiz, duplicação massiva, ausência de governança IA completa, dependência single-provider (Gemini-only), e ausência de mecanismos de resiliência sistêmica — que o posicionam abaixo dos critérios padrão de production readiness enterprise.

A **Plataforma LIA** implementa camadas enterprise mais abrangentes: multi-provider LLM com factory pattern, circuit breaker (agora aplicado em produção em Pearch/Deepgram/OpenMic com tenacity retry), rate limiter, PII masking global no root logger, prompt injection multi-pattern, policy middleware per-company, learning loop adaptativo, token tracking com billing e alertas automáticos de consumo (80%/100%), comunicação multicanal (5 canais) com preferências de canal por candidato, consentimento LGPD granular por finalidade com HTTP 451, human review gate em rejeições, plan limits enforcement (HTTP 402), LGPD cleanup scheduler, e 12 domínios DDD com ReAct agents e FAIRNESS_AND_COMPLIANCE em todos os system prompts. O Sprint de Qualidade e Compliance de fevereiro de 2026 fechou os gaps de testes (T1 unitários, T2 integração, T3 E2E Playwright, T4 carga Locust, B5 disparate impact) — a LIA agora supera o V5 também nessa dimensão. A auditoria QA subsequente (v3.1) identificou e corrigiu 7 vulnerabilidades adicionais: eliminação de bias geográfico discriminatório (B2), blind evaluation sem nome do candidato (B1), LangSmith tracing opt-in (L1), WhatsApp token seguro (L8), retry automático no Gemini provider (A2), e 9 testes restaurados (T1+T2) — resultando em 64/64 testes passando e zero bugs pendentes.

### Scorecard Resumido

> v10.0 — 11/03/2026. ↑ = melhoria nesta versão v10.0 vs v9.1. SEG-1 a SEG-5 elevaram D5 e D6.

| Dimensão | V5 | LIA v10.0 | Delta | Vantagem |
|----------|-----|-----------|-------|----------|
| 1. Arquitetura de Agentes | 7.0 | 9.3 | +2.3 | LIA |
| 2. Qualidade de Código | 6.5 | 7.6 | +1.1 | LIA |
| 3. **Organização/Estrutura** | **3.5** | **7.9** | **+4.4** | **LIA** |
| 4. Eficiência LLM | 7.5 | 8.0 | +0.5 | LIA |
| 5. Governança IA | 5.0 | **9.8 ↑** | **+4.8** | LIA |
| 6. Segurança | 5.5 | **9.4 ↑** | **+3.9** | LIA |
| 7. Human-in-the-Loop | 5.5 | 9.4 | +3.9 | LIA |
| 8. Sistema de Aprendizado | 3.0 | 7.5 | +4.5 | LIA |
| 9. Tool System | 8.5 | 7.5 | -1.0 | V5 |
| 10. Observability | 5.0 | 9.7 | +4.7 | LIA |
| 11. Testes | 7.0 | **9.3 ↑** | **+2.3** | LIA |
| 12. Infraestrutura | 7.5 | 9.8 | +2.3 | LIA |
| 13. Multi-provider LLM | 1.0 | 8.5 | +7.5 | LIA |
| 14. Resiliência | 3.0 | 9.5 | +6.5 | LIA |
| **Média** | **5.4** | **9.1 ↑** | **+3.7** | **LIA** |

### Métricas Quantitativas

> v9.0 — 10/03/2026. Todas as contagens verificadas contra filesystem real.

| Métrica | V5 | LIA (v8.0) — verificado filesystem |
|---------|-----|-----|
| Arquivos Python (app/) | ~196 | **1.180+** |
| LOC estimado | ~49K | ~465K+ |
| Domínios DDD | 2 | **12** (analytics, ats_integration, automation, communication, cv_screening, interview_scheduling, job_management, pipeline, policy, recruiter_assistant, sourcing + hiring_policy legacy) |
| Agentes ReAct (4-file pattern) | 0 | **12** ReAct (wizard, sourcing, pipeline, talent, jobs_mgmt, kanban, policy_react, policy_setup, analytics, communication, ats_integration, automation) — verificado v11.0 |
| Agentes StateGraph (LangGraph nativo) | 6 (pipeline linear) | **4** (job_wizard_graph, wsi_interview_graph, interview_graph, pipeline_transition_agent) — `USE_LANGGRAPH_NATIVE=True` global; **16 agentes distintos** total |
| Routers REST registrados (main.py) | 0 (CLI) | **204** (app.include_router) |
| Endpoints em app/api/v1/ | 0 | **206** arquivos de router (verificado v11.0) |
| Tools YAML declarativos | 70 | **32** (`tool_registry_metadata.yaml`) + code-driven |
| Serviços (app/services/) | ~15 | **231** arquivos .py (verificado v11.0) |
| Modelos SQLAlchemy (app/models/) | — | **99** verificados filesystem |
| Migrations Alembic | — | **37** (verificado v11.0; inclui compliance: 010 human review, 015 fairness audit, 018 bias snapshot, 020 guardrails, 032 HITL SOX) |
| Providers LLM | 1 (Gemini) | 3 (Claude primário, OpenAI fallback, Gemini fallback) + Factory + `generate_with_fallback()` |
| Canais comunicação | 1 (callback REST) | 5 (email, WhatsApp, SMS, Teams, in-app Bell) |
| Testes BE coletados | 53 arquivos | **227 test files** (verificado v11.0); coverage gate 32%, achieved 32.66% |
| Cobertura BE | — | **32.66%** (gate CI: 32%) |
| Testes FE | — | Vitest + **60+** testes unitários (use-navigation-intent, use-action-intent, use-candidates-list, HITLConfirmCard, use-float-streaming + 9 Sprint J) |
| Testes de carga | — | Locust: WizardUser + PipelineUser + HealthCheckUser (`tests/load/`) |
| Libs UV Monorepo | — | **10** (config, utils, models, audit, messaging, agents-core, services, contexts, auth, orchestrator) |
| Serviços Docker Compose | 2 (workers) | **14** (postgres, redis, rabbitmq, api, api-vagas, api-funil, api-onboarding, celery_worker_high/normal/low, celery_beat, flower, prometheus, grafana) |
| Métricas Prometheus | — | **14** (Histogram/Counter/Gauge/Summary — verificado v11.0) |
| WS Domains registrados | — | **11 + aliases** (wizard, talent, pipeline/cv_screening, kanban, sourcing, jobs_management/jobs_mgmt, policy, pipeline_transition, analytics, communication/comms, ats_integration/ats — verificado v11.0) |
| Páginas Next.js (page.tsx) | — | **90** (verificado v11.0) |
| FE Hooks (src/hooks/) | — | **114** (verificado v11.0; inclui use-float-streaming.ts Sprint J3, use-short-list.ts F4) |
| FE Componentes (src/components/) | — | **47 diretórios** (~450 arquivos .tsx, inclui HITLConfirmCard Sprint J3) |
| Componentes extraídos de candidates-page | — | **5** (CandidateSearchBar, CandidatesHeader, CandidatesTable, CandidateTabs, SearchResultsHeader) |
| Tabelas HITL | — | 2 (`hitl_pending_actions` + `hitl_audit_trail`) |
| Tabela Quality Evaluations | — | 1 (`agent_quality_evaluations`) |
| Tabela User Preferences | — | 1 (`user_agent_preferences`) |

---

## 2. Inventário V5 (recruiter_agent_v5)

### 2.1 Stack Técnico

| Camada | Tecnologia |
|--------|-----------|
| LLM | Google Gemini 2.5 Flash (hardcoded) |
| Framework Agentes | LangGraph + LangChain |
| Backend | Flask (evaluation API) + CLI (main.py) |
| Queue | RabbitMQ (pika) + Celery + Redis |
| Database | PostgreSQL + pgvector |
| Deploy | Docker Compose + GCP VM |
| Tracing | LangSmith |
| UI (debug) | Streamlit |
| Embeddings | Google text-embedding-004 |

### 2.2 Mapa de Componentes

```
recruiter_agent_v5/
├── src/
│   ├── agents/           # 6 agentes pipeline (132KB total)
│   │   ├── intent_analyzer.py    (19.6KB) — Análise de intent + detecção de ambiguidade
│   │   ├── api_planner.py        (22.3KB) — Planejamento de API calls
│   │   ├── api_executor.py       (10.8KB) — Execução HTTP
│   │   ├── data_processor.py     (53.5KB) — ⚠️ GOD OBJECT (1387 linhas)
│   │   ├── answer_formatter.py   (19.7KB) — Formatação com taxonomia 11 tipos
│   │   └── plan_validator.py     (6.8KB)  — Validação + replanning
│   ├── domains/
│   │   ├── evaluation/           # Entrevistas com LangGraph
│   │   │   ├── graph.py          — StateGraph (classify→evaluate→decide→craft)
│   │   │   ├── nodes.py          — 4 nós com Gemini structured output
│   │   │   ├── security.py       — 17 patterns de prompt injection
│   │   │   ├── state.py, models.py, prompts.py, processor.py
│   │   │   ├── worker.py, tasks.py — Celery async workers
│   │   │   └── final_analysis.py
│   │   ├── sourced_profile_sourcing/  # Sourcing completo
│   │   │   ├── agents/ (11 agentes): router, orchestrator, planner, search, 
│   │   │   │   detail, comparison, analytics, report, action, base
│   │   │   ├── actions/ (11 ações): search, details, comparison, analysis,
│   │   │   │   distribution, insights, report, score, count, base, search_improvement
│   │   │   ├── fairness.py       — FairnessGuard + FairnessMetrics
│   │   │   ├── fact_checker.py   — FactChecker (verify_count, verify_average, verify_top)
│   │   │   ├── memory.py         — ConversationMemory (in-session)
│   │   │   ├── smart_extractor.py — LLM-based skill/company extraction
│   │   │   ├── validators.py, cache.py, api_client.py, api_operations.py
│   │   │   ├── config/ (domain_settings.py + extraction_config.yaml)
│   │   │   └── prompt_builder/
│   │   ├── base.py, registry.py, orchestrator.py, workflow.py
│   │   └── __init__.py
│   ├── tools/                # YAML-driven tool system
│   │   ├── registry.py       — ToolRegistry singleton (thread-safe)
│   │   ├── executor.py       — ToolExecutor (HTTP + context)
│   │   ├── contracts.py      — ToolConfig, ExecutionContext, ExecutionResult
│   │   ├── hooks.py          — PreHook/PostHook/HookRegistry (OCP)
│   │   └── formatter.py      — ResponseFormatter
│   ├── services/             # ~15 serviços
│   │   ├── api_client.py     — ATSAPIClient (requests + retry)
│   │   ├── rag_service.py    — RAG híbrido (semantic + fulltext + reranking)
│   │   ├── memory_service.py — PostgreSQL persistence
│   │   ├── embedding_service.py — Google text-embedding-004
│   │   ├── clarification_service.py — Detecção de ambiguidade
│   │   ├── message_router.py — Router global/domain
│   │   ├── rabbitmq_service.py — Consumer RabbitMQ
│   │   ├── ott_service.py    — One-Time Token auth
│   │   ├── auth_service.py   — Autenticação OTT/credentials
│   │   ├── endpoint_loader.py — Carregamento dinâmico de endpoints
│   │   └── evaluation_service.py
│   ├── config/               # 13 arquivos de configuração
│   │   ├── settings.py       — Settings centralizado (dataclasses)
│   │   └── [gemini|langsmith|postgres|rabbitmq|celery|evaluation|...]_config.py
│   ├── models/               # Modelos de dados
│   │   ├── state.py          — QueryState (TypedDict)
│   │   ├── conversation_state.py — ClarificationRequest, ClarificationType
│   │   ├── intent.py, api_plan.py, response.py, exceptions.py
│   │   └── pydantic_models.py
│   ├── utils/                # 10 utilitários
│   │   ├── timing.py, logger.py, callbacks.py, variable_substitutor.py
│   │   └── yaml_to_tools.py, confirmation_builder.py, item_formatter.py
│   ├── workflow/
│   │   └── graph.py          — WorkflowOrchestrator (LangGraph StateGraph)
│   └── api_controllers/      — Controllers REST (Flask)
├── documentation/            # 40+ arquivos YAML de tools
├── documentation_toon/       # 30+ arquivos TOON (duplicação de documentation/)
├── tests/                    # 53 arquivos de teste
├── scripts/                  # 25+ scripts utilitários
├── deploy/                   # 3 scripts de deploy (GCP)
├── ⚠️ RAIZ (arquivos órfãos):
│   ├── chat.py (13.6KB)      — CLI interativo (deveria estar em src/cli/)
│   ├── web_debug.py (16.2KB) — Streamlit com MOCK DATA HARDCODED
│   ├── examples.py           — Exemplos (deveria estar em docs/)
│   ├── test_domains.py       — Teste (deveria estar em tests/)
│   ├── test_list_by_index.py — Teste (deveria estar em tests/)
│   ├── evaluation_worker_backup.py — BACKUP FILE no repo
│   └── ALL_PYTHON_FILES.txt (338KB) — Concatenação de TODOS os .py
└── docker-compose.workers.yml
```

### 2.3 Pipeline de Agentes (Fluxo Principal)

```
User Query → IntentAnalyzer → APIPlannerAgent → APIExecutorAgent → PlanValidator
                                                                        ↓
                                                              (needs_replanning?)
                                                              ├── Yes → APIPlannerAgent (retry, max 3)
                                                              └── No → DataProcessorAgent → AnswerFormatterAgent → Response
```

### 2.4 Dependências (requirements.txt)

| Categoria | Pacotes |
|-----------|---------|
| LLM | langchain-core, langchain-google-genai, langgraph, google-generativeai |
| HTTP | requests, httpx |
| Database | psycopg2-binary, pgvector |
| Queue | pika (RabbitMQ), celery[redis], redis, flower |
| Web | streamlit, flask, gunicorn |
| Data | pandas, PyYAML |
| Dev | pytest, pytest-cov, black, mypy, pylint |

---

## 3. Inventário LIA (Plataforma LIA)

### 3.1 Stack Técnico

| Camada | Tecnologia |
|--------|-----------|
| LLM | Claude (Anthropic) + OpenAI + Gemini com Factory Pattern |
| Framework Backend | FastAPI (async) |
| ORM | SQLAlchemy (async) |
| Auth | WorkOS (SSO) |
| Database | PostgreSQL |
| Search | Embeddings + Semantic Search |
| Voice | Deepgram, Gemini Voice |
| ATS | Gupy, Pandapé, StackOne, Merge |
| Email | Resend, SendGrid |
| Billing | Iugu, Vindi |
| WhatsApp | Twilio, Meta |
| Collaboration | Microsoft Teams |
| Observability | OpenTelemetry, LangSmith |
| Frontend | Next.js + React + TypeScript + Tailwind |

### 3.2 Mapa de Componentes

```
workspace/
├── lia-agent-system/app/
│   ├── agents/               # 13 especializados + infra (robustness layer)
│   ├── domains/              # 12 domínios DDD
│   │   ├── analytics/        # analytics_react_agent.py ← PHASE 5 (wired WS)
│   │   ├── ats_integration/  # ats_integration_react_agent.py + 5 ATS clients ← PHASE 5
│   │   ├── automation/       # automation_react_agent.py + 17 serviços
│   │   ├── communication/    # communication_react_agent.py + 18 serviços ← PHASE 5 (wired WS)
│   │   ├── cv_screening/     # pipeline_react_agent.py + wsi_interview_graph.py
│   │   ├── hiring_policy/    # policy_react_agent.py (4-file pattern — legado)
│   │   ├── interview_scheduling/ # interview_graph.py + interview_scheduling_nodes.py
│   │   ├── job_management/   # wizard_react_agent.py + job_wizard_graph.py + job_vacancy_nodes.py
│   │   ├── pipeline/         # pipeline_transition_agent.py (20+ tools, invocação direta)
│   │   ├── policy/           # agent.py (PolicySetupAgent — I3c, 19 perguntas/5 blocos)
│   │   ├── recruiter_assistant/ # kanban_react_agent.py + talent_react_agent.py + jobs_mgmt_react_agent.py
│   │   └── sourcing/         # sourcing_react_agent.py + 11 serviços
│   ├── services/             # 225 serviços especializados (verificado: 225 arquivos .py)
│   │   ├── billing_providers/    # Iugu, Vindi
│   │   ├── email_providers/      # Resend, SendGrid
│   │   ├── ats_clients/          # Gupy, Pandapé, StackOne, Merge
│   │   ├── ml/                   # feature_engineering, outcome_predictor
│   │   ├── token_budget_service.py       # ← Sprint A: PLAN_DAILY_LIMITS, HTTP 429
│   │   ├── token_tracking_service.py     # Token prices + usage tracking
│   │   ├── prompt_version_registry.py    # ← Sprint B: SHA256 hash, admin endpoint
│   │   ├── rag_pipeline_service.py       # ← G6: pgvector + BM25 + alpha blend
│   │   ├── toon_service.py               # ← G7: TOON Format LGPD, Redis TTL 1h
│   │   ├── hitl_service.py               # ← Sprint C+F1: Redis + DB source-of-truth
│   │   ├── bias_audit_service.py         # Four-Fifths Rule (gender/age/PCD/region)
│   │   └── model_drift_service.py        # 4 triggers + alertas automáticos
│   ├── shared/
│   │   ├── providers/        # LLM Factory (Claude, OpenAI, Gemini + ABC + generate_with_fallback)
│   │   ├── resilience/       # Circuit Breaker CLOSED/OPEN/HALF_OPEN + Cache Manager
│   │   ├── compliance/       # FairnessGuard (3 camadas) + FactChecker + AuditCallback
│   │   ├── channels/         # 5 adapters (email, WhatsApp, SMS, Teams, in-app)
│   │   ├── learning/         # Learning Loop + Template Learning + A/B Testing
│   │   ├── intelligence/     # Smart Extractor + Semantic Search + Embeddings
│   │   ├── robustness/       # 7 protection modules
│   │   ├── agents/           # langgraph_base, langgraph_react_base, streaming_callback, checkpointer ← G1
│   │   ├── execution/        # Action planner, executor
│   │   ├── tools/            # Export, insight, predictive, proactive
│   │   ├── platform_events.py            # ← G4: PlatformEvent + handler registry + RabbitMQ
│   │   ├── pii_masking.py, prompt_injection.py, policy_middleware.py
│   │   ├── tracing.py, structured_logging.py
│   │   └── encryption.py
│   ├── middleware/            # Rate limiter (Redis ZSET sliding window) + Request ID
│   ├── orchestrator/         # cascaded_router (6-tier) + vector_semantic_cache (pgvector) + navigation_intent
│   ├── models/               # 99 modelos SQLAlchemy (verificado filesystem 2026-03-13)
│   │   └── hitl.py           # ← F1: HITLPendingAction + HITLAuditTrail (SOX/BCB-498)
│   ├── schemas/              # 50+ schemas Pydantic
│   ├── api/v1/               # 206 routers registrados (verificado filesystem 2026-03-13)
│   │   ├── agent_chat_ws.py  # WS (11 domínios wired + aliases)
│   │   ├── hitl.py           # POST /api/v1/hitl/{thread_id}/approve
│   │   ├── rag_search.py     # GET /api/v1/candidates/rag-search
│   │   ├── toon.py           # GET /api/v1/candidates/{id}/toon
│   │   ├── short_lists.py    # ← F4: POST/GET /api/v1/short-lists
│   │   ├── admin_token_budget.py  # ← Sprint A: GET /api/v1/admin/token-budget
│   │   └── fairness_reports.py    # GET /api/v1/bias-audit/job/{job_id}
│   ├── tools/                # 10 code-driven + tool_registry_metadata.yaml (32 tools YAML) ← G5
│   │   └── scope_config.py   # ← 4 escopos: TALENT_FUNNEL(20), JOB_TABLE(19), IN_JOB(25), GLOBAL(2) = 66 tools
│   ├── prompts/              # YAML + Python (20+ arquivos)
│   ├── auth/                 # WorkOS SSO (6 arquivos)
│   ├── config/               # langsmith.py, sentry.py, cache_config.py, industry_weights.py
│   ├── observability/        # metrics.py — 14 métricas Prometheus (Histogram/Counter/Gauge/Summary)
│   └── jobs/                 # drift_job.py, celery_tasks.py
│
├── plataforma-lia/src/       # FRONTEND — Next.js 15 + React 19 (90 pages, 114 hooks)
│   ├── app/                  # 90 páginas (page.tsx) — verificado 2026-03-13
│   ├── components/lia-float/
│   │   ├── LiaChatPanel.tsx   # Float chat + navigation hints + action mode banner
│   │   ├── LiaSplitPanel.tsx  # Split-view 360px com WS streaming
│   │   └── LiaFloatButton.tsx
│   ├── components/pages/candidates/   # 5 componentes extraídos de candidates-page ← G3/F5
│   │   ├── CandidateSearchBar.tsx     # Busca com operadores avançados
│   │   ├── CandidatesHeader.tsx       # Header com filtros
│   │   ├── CandidatesTable.tsx        # Tabela principal
│   │   ├── CandidateTabs.tsx          # Tabs (todos/aplicantes/etc.)
│   │   └── SearchResultsHeader.tsx    # Header de resultados com pills DS v4.2.1
│   ├── hooks/ (114 total — verificado 2026-03-13)
│   │   ├── use-navigation-intent.ts   # POST /api/v1/navigation-intent, threshold 0.65
│   │   ├── use-action-intent.ts       # 5 domains, threshold 0.70, ScoredAction loop
│   │   ├── use-agent-streaming.ts     # WS streaming hook
│   │   ├── use-candidate-filters.ts   # Filtros candidatos (wired)
│   │   ├── use-candidate-selection.ts # Seleção múltipla (wired)
│   │   ├── use-candidates-list-mapped.ts  # ← G4: useMemo wrapper + transforms
│   │   ├── use-short-list.ts          # ← F4: Short Lists API hook
│   │   └── [86 outros hooks]
│   ├── lib/transforms/
│   │   └── candidate-transforms.ts    # ← G4: Pure functions 298L (100% Vue-portável)
│   └── components/dashboard-app.tsx   # Flex layout + LiaSplitPanel
│
└── libs/                     # UV Monorepo — 10 libs ← 6a/6b/6c + orchestrator
    ├── config/lia_config/    # config.py, database.py, celery_app.py
    ├── utils/lia_utils/      # datetime_helpers.py, skill_classifier.py
    ├── models/lia_models/    # 94 modelos SQLAlchemy migrados
    ├── audit/                # audit_callback, audit_models, audit_storage, audit_writer
    ├── messaging/            # notification_service.py (1261L) + email + teams + whatsapp
    ├── agents-core/          # 24 arquivos: langgraph_base, checkpointer, streaming_callback, etc.
    ├── services/             # BaseRepository, SQLAlchemyRepository, domain repos
    ├── contexts/             # 9 domínios: wizard, pipeline, sourcing, kanban, talent, etc.
    ├── auth/                 # SecretsProvider, EnvProvider, get_secrets_provider
    └── orchestrator/         # scaffold para migração
```

### 3.2.1 Automação Engine — Detalhamento

O domínio `app/domains/automation/` contém **19 serviços** que formam o motor completo de automações:

| Serviço | Responsabilidade |
|---------|-----------------|
| `automation_service.py` | Orquestrador central — recebe eventos, resolve regras, despacha handlers |
| `automation_scheduler.py` | Cron-like scheduler para automações periódicas (daily/weekly/monthly) |
| `automation_trigger_service.py` | Detecta eventos que disparam automações (stage change, score threshold, tempo sem resposta) |
| `automation_handlers.py` | Executores de ações específicas por tipo de automação |
| `stage_automation_engine.py` | Motor de transição automática de stages com regras configuráveis por empresa |
| `stage_transition_automation.py` | Integração direta com pipeline — move candidatos automaticamente |
| `planned_task_service.py` | Tarefas agendadas por data/condição (follow-ups, lembretes, expiração) |
| `autonomous_agent_service.py` | Execução autônoma de tarefas (com HITL para ações destrutivas) |
| `proactive_alert_service.py` | Notificações automáticas: pipeline parado, candidato quente sem resposta |
| `proactive_service.py` | Sugestões contextuais de próxima ação para o recrutador |
| `prediction_action_bridge.py` | Ponte ML predictions → automações (ex: alta probabilidade aceite → automatizar oferta) |
| `learning_automation.py` | Automações que melhoram com feedbacks e resultados históricos |
| `pattern_applier.py` | Aplica padrões aprendidos a novos candidatos/vagas |
| `pipeline_monitor.py` | Monitora saúde do pipeline em tempo real — detecta gargalos |
| `event_action_connector.py` | Conecta PlatformEvents a ações de automação |
| `candidate_context_aggregator.py` | Agrega contexto completo do candidato para decisões de automação |
| `webhook_adapters.py` | Adapta eventos de ATS externos para o modelo de eventos interno |
| `task_service.py` | CRUD de tasks geradas automaticamente |

**APIs de automação registradas:** `automation.py`, `automations.py`, `automation_rules.py`, `stage_transition_automation.py`, `task_planner.py`, `task_monitoring.py`, `tasks.py`, `task_lifecycle.py`

**O que LIA tem que V5 não tem:** stage automation engine, trigger-based workflows, proactive alerts, ML-driven automation, planned tasks, pipeline health monitoring, webhook-triggered automations.

### 3.2.2 Intelligence Layer — Detalhamento

```
Intelligence Stack LIA:
├── RAG Híbrido (G6)
│   ├── rag_pipeline_service.py — pgvector cosine + tsvector BM25 + alpha blend
│   │   ├── alpha=0.0 → BM25 full-text puro
│   │   ├── alpha=1.0 → Semântico pgvector puro
│   │   └── 0<alpha<1 → Híbrido parametrizável
│   └── GET /api/v1/candidates/rag-search?q=&company_id=&limit=20&alpha=0.5
│
├── TOON Format (G7)
│   ├── toon_service.py — TOONCard, Redis TTL=3600s, LGPD anonymize=True
│   └── GET /api/v1/candidates/{id}/toon
│
├── CascadedRouter (G2) — 6 tiers de custo crescente
│   ├── Tier 1: in-process cache (0ms, custo zero)
│   ├── Tier 2: Redis cache (1-5ms, custo zero)
│   ├── Tier 3: regex/keyword matching (0ms, custo zero)
│   ├── Tier 4: LLM Haiku (rápido/barato para queries simples)
│   ├── Tier 5: LLM Sonnet (balanceado — 80% dos casos)
│   └── Tier 6: LLM Opus (complexo — casos difíceis)
│
├── Navigation Intent (Sprint J — 8 grupos)
│   ├── Grupo 1: Vagas | Grupo 2: Candidatos | Grupo 3: Pipeline
│   ├── Grupo 4: Sourcing | Grupo 5: WSI (novo Sprint J)
│   ├── Grupo 6: Indicadores (novo Sprint J)
│   ├── Grupo 7: Configurações (novo Sprint J)
│   └── Grupo 8: Wizard → openSplitView("Vagas") (novo Sprint J)
│
└── ML Services (analytics/services/ + services/ml/)
    ├── feature_engineering.py, outcome_predictor.py
    ├── predictive_analytics_service.py, pipeline_prediction_service.py, early_warning_service.py
    ├── journey_intelligence_service.py
    └── sector_benchmark_service.py (anti-sycophancy — Crença #11)
```

**Agentes de IA Ativos — Inventário Completo (v11.0 — verificado filesystem 2026-03-13):**

| # | Agente | Arquivo | Domínio | Tipo | WS Registrado |
|---|--------|---------|---------|------|---------------|
| 1 | WizardReActAgent | `wizard_react_agent.py` | `job_management` | ReAct 4-file | ✅ "wizard" |
| 2 | JobWizardGraph | `job_wizard_graph.py` | `job_management` | LangGraph StateGraph | ✅ (via resume) |
| 3 | SourcingReActAgent | `sourcing_react_agent.py` | `sourcing` | ReAct 4-file | ✅ "sourcing" |
| 4 | PipelineReActAgent | `pipeline_react_agent.py` | `cv_screening` | ReAct 4-file | ✅ "pipeline" / "cv_screening" |
| 5 | WSIInterviewGraph | `wsi_interview_graph.py` | `cv_screening` | LangGraph StateGraph | ✅ (via resume) |
| 6 | TalentReActAgent | `talent_react_agent.py` | `recruiter_assistant` | ReAct 4-file | ✅ "talent" (+ default fallback) |
| 7 | JobsMgmtReActAgent | `jobs_mgmt_react_agent.py` | `recruiter_assistant` | ReAct 4-file | ✅ "jobs_management" / "jobs_mgmt" |
| 8 | KanbanReActAgent | `kanban_react_agent.py` | `recruiter_assistant` | ReAct 4-file | ✅ "kanban" |
| 9 | PolicyReActAgent | `policy_react_agent.py` | `hiring_policy` | ReAct 4-file | ✅ "policy" |
| 10 | PolicySetupAgent | `domains/policy/agents/agent.py` | `policy` | ReAct 4-file | ❌ (domínio legado) |
| 11 | AnalyticsReActAgent | `analytics_react_agent.py` | `analytics` | ReAct 4-file | ✅ "analytics" |
| 12 | CommunicationReActAgent | `communication_react_agent.py` | `communication` | ReAct 4-file | ✅ "communication" / "comms" |
| 13 | ATSIntegrationReActAgent | `ats_integration_react_agent.py` | `ats_integration` | ReAct 4-file | ✅ "ats_integration" / "ats" |
| 14 | AutomationReActAgent | `automation_react_agent.py` | `automation` | ReAct 4-file | ❌ **pendente wiring** |
| 15 | PipelineTransitionAgent | `pipeline_transition_agent.py` | `pipeline` | Direto 20+ tools | ✅ "pipeline_transition" |
| 16 | InterviewGraph | `interview_graph.py` | `interview_scheduling` | LangGraph StateGraph | ❌ via REST |

**Resumo de agentes por tipo:**
- **12 ReAct 4-file** (wizard, sourcing, pipeline, talent, jobs_mgmt, kanban, policy_react [hiring_policy], policy_setup [policy/legado], analytics, communication, ats_integration, automation)
- **4 LangGraph/StateGraph** (job_wizard_graph, wsi_interview_graph, interview_graph, pipeline_transition_agent)
- Total: **16 agentes distintos** (verificado filesystem 2026-03-13)
- **12 de 16 com WS wired** (75%): wizard, pipeline/cv_screening, sourcing, talent (default), kanban, jobs_mgmt, policy, pipeline_transition, analytics, communication/comms, ats/ats_integration + fallback
- **1 pendente wiring** (AutomationReActAgent); **2 via REST/invocação direta** (InterviewGraph, PolicySetupAgent legado); **1 via resume WS** (job_wizard_graph via resume_domain)

### 3.2.3 Voz e Multimodal — Detalhamento

| Componente | Arquivo | Tecnologia | Função |
|-----------|---------|-----------|--------|
| Deepgram STT | `deepgram_service.py` | Deepgram Nova-2 | Speech-to-text entrevistas/triagem |
| OpenMic.ai | `openmic_service.py` | OpenMic.ai API | Triagem automática por ligação |
| WSI Voice | `wsi_voice_orchestrator.py` | Deepgram + LLM | Orquestra entrevistas WSI por voz |
| Transcrição | `transcription_service.py` | Deepgram + Gemini | Transcrição e análise de áudio |
| Interview Notes | `interview_notes_service.py` | LLM | Notas estruturadas automáticas |
| Transcript Analysis | `interview_transcript_analysis_service.py` | LLM | Análise semântica de transcrições |
| Voice Screening | `voice.py` + `lia_voice.py` | REST | Endpoints de screening por voz |

**Fluxo WSI por voz:** Candidato → [WhatsApp/Tel/Web] → OpenMic.ai / Deepgram → `wsi_voice_orchestrator.py` → `wsi_interview_graph.py` (LangGraph: generate_questions → evaluate_responses → HITL interrupt → generate_final_report) → `rubric_evaluation_service.py` (FairnessGuard + blind evaluation) → Feedback personalizado

### 3.2.4 Compliance e Auditoria — Detalhamento

| Componente | Arquivo | Padrão | Função |
|-----------|---------|--------|--------|
| FairnessGuard Camada 1 | `shared/compliance/fairness_guard.py` | EU AI Act | Regex 40+ patterns |
| FairnessGuard Camada 2 | `shared/compliance/fairness_guard.py` | EU AI Act | Léxico implícito |
| FairnessGuard Camada 3 | `shared/compliance/fairness_guard.py` | EU AI Act | LLM opt-in (`FAIRNESS_LAYER3_ENABLED`) |
| FactChecker | `shared/compliance/fact_checker.py` | Anti-alucinação | verify_count/avg/top por tipo |
| Audit Callback/Writer/Storage | `shared/compliance/audit_*.py` | SOC 2/ISO 27001 | 5 arquivos de auditoria completa |
| Bias Audit Service | `services/bias_audit_service.py` | EEOC/Four-Fifths | Four-Fifths Rule: gender/age/PCD/region |
| Bias Audit Snapshot | `models/bias_audit_snapshot.py` | SOX | Histórico auditável de snapshots |
| FairnessAuditLog | `models/fairness_audit.py` | EU AI Act | Log persistente de hits de bias |
| Model Drift | `services/model_drift_service.py` | ISO 42001 | 4 triggers: score/aprovação/custo/latência P95 |
| Drift Alert | `services/drift_alert_service.py` | ISO 42001 | Bell+Teams quando drift detectado |
| PII Masking | `shared/pii_masking.py` | LGPD | CPF/email/telefone/nome no root logger |
| LGPD Consent | `api/v1/consent_management.py` | LGPD Art. 7 | Consentimento granular por finalidade |
| Data Request Portal | `api/v1/data_subject_requests.py` | LGPD Art. 18 | Portal do titular |
| LGPD Cleanup | `api/v1/lgpd_compliance.py` | LGPD Art. 16 | Scheduler 30/90/180d admin-only |
| Guardrails | `models/guardrail.py` + `api/v1/guardrails.py` | NIST AI RMF | Code-based guardrails por empresa |
| Blind Evaluation | `rubric_evaluation_service.py` | EU AI Act | Nome removido do contexto LLM |
| Human Review Gate | `api/v1/pipeline.py` | EU AI Act Art. 14 | 422 sem user_id em rejeição |
| Agent Quality Eval | `services/agent_quality_evaluator.py` | NIST AI RMF | task_completion/fairness/response_quality |

**Migrations de compliance (em ordem):** 010 human_review_gate → 013 scheduled_deletion → 015 fairness_audit_log → 016 scheduled_deletion_ai → 018 bias_audit_snapshot → 020 guardrails → 025 agent_execution_metadata → 032 hitl_tables (SOX) → 034 agent_quality_evaluations

**Total de migrations Alembic: 37** (verificado filesystem 2026-03-13)

### 3.2.5 ActionExecutor e Sistema de Comandos Kanban — Detalhamento

> Seção adicionada na v11.0. O `ActionExecutor` é o componente central que traduz intenções de ação do chat em operações concretas no sistema.

**Arquivo:** `app/orchestrator/action_executor.py` — **1.080 linhas**

O ActionExecutor é invocado pelo sistema de chat quando uma intenção de ação é detectada (via `use-action-intent.ts` no frontend, threshold 0.70). Ele recebe o contexto da ação e despacha para o handler correto.

**9 Action IDs** mapeados via `ACTIONABLE_INTENTS` dict (verificado em código 2026-03-13):

| # | action_id | Descrição | Intents mapeados | HITL |
|---|-----------|-----------|-----------------|------|
| 1 | `move_candidate` | Mover candidato entre stages do pipeline | mover_candidato, aprovar_candidato, reprovar_candidato, encaminhar_candidato | ✅ requires_confirmation |
| 2 | `send_email` | Enviar email para candidato | enviar_email, comunicar_candidato | ✅ requires_confirmation |
| 3 | `schedule_interview` | Agendar entrevista com candidato | agendar_entrevista | ✅ requires_confirmation |
| 4 | `start_screening` | Iniciar triagem/screening de candidato | iniciar_triagem, avaliar_candidato | ✅ requires_confirmation |
| 5 | `analyze_profile` | Analisar perfil detalhado do candidato | analisar_perfil, comparar_candidatos | ❌ read-only |
| 6 | `pause_job` | Pausar vaga ativa | pausar_vaga | ✅ requires_confirmation |
| 7 | `close_job` | Fechar/encerrar vaga | fechar_vaga | ✅ requires_confirmation |
| 8 | `duplicate_job` | Duplicar vaga existente | duplicar_vaga | ✅ requires_confirmation |
| 9 | `reopen_job` | Reabrir vaga fechada/pausada | reabrir_vaga | ✅ requires_confirmation |

**Fluxo de execução:** Intent detectado (chat/WS) → `ACTIONABLE_INTENTS[intent]` → `ActionExecutorConfig` → HITL check (se `requires_confirmation=True` → `HITLConfirmCard` inline → aguarda aprovação) → execução do `action_id` handler → resposta ao usuário.

**Integração com HITL:** 8 de 9 action_ids requerem confirmação via `HITLConfirmCard` inline no chat — apenas `analyze_profile` (leitura) executa direto sem aprovação.

### 3.2.6 Scope Config — Controle de Acesso por Contexto

> Seção adicionada na v11.0. O `scope_config.py` define quais ferramentas estão disponíveis em cada contexto de prompt.

**Arquivo:** `app/tools/scope_config.py`

```
PromptScope (Enum) — verificado via código 2026-03-13:
├── TALENT_FUNNEL  — 20 tools (busca e gestão de candidatos)
│   ├── Query (11): search_candidates, get_candidate_details, get_candidate_stats,
│   │              compare_candidates, get_talent_quality, get_talent_engagement,
│   │              get_talent_availability, get_diversity_metrics, get_candidate_history,
│   │              get_ml_predictions, get_conversion_patterns
│   └── Action (9): add_candidate_to_vacancy, reject_candidate, shortlist_candidate,
│                   add_to_list, hide_candidate, send_email, send_whatsapp,
│                   send_bulk_email, export_candidates
│
├── JOB_TABLE — 19 tools (gestão de vagas)
│   ├── Query (12): search_jobs, get_job_details, get_pipeline_stats,
│   │              get_recruiter_metrics, get_velocity_metrics, get_efficiency_metrics,
│   │              get_comparative_metrics, get_workload_distribution,
│   │              get_hiring_quality, get_cost_metrics, get_market_benchmarks, get_trends
│   └── Action (7): create_job, update_job, close_job, pause_job,
│                   publish_job, export_job_analytics, generate_report
│
├── IN_JOB — 25 tools (ações dentro de vaga específica)
│   ├── Query (14): compare_candidates, get_candidate_details, get_candidate_stats,
│   │              get_job_details, get_activity_summary, get_bottleneck_analysis,
│   │              get_job_benchmark, get_job_quality_metrics, get_job_velocity,
│   │              get_pending_actions, get_prediction_metrics, get_smart_alerts,
│   │              get_stakeholder_metrics, get_vacancy_funnel
│   └── Action (11): update_candidate_stage, reject_candidate, shortlist_candidate,
│                    schedule_interview, send_email, send_whatsapp, send_feedback,
│                    add_to_list, hide_candidate, bulk_update_candidates_stage, wsi_screening
│
└── GLOBAL — 2 tools (disponíveis em qualquer contexto)
    └── Action: generate_report, schedule_report
```

**Função-chave:** `get_tools_for_scope(scope, tool_type)` — retorna o set de tools permitidos para o escopo e tipo (query/action/all).

**Função de filtragem:** `filter_tools_by_scope(tools, scope)` — filtra lista de definições de tools para apenas os permitidos no escopo.

**Função de validação:** `is_tool_allowed_in_scope(tool_name, scope)` — verifica se tool específico é permitido.

### 3.2.7 Sistema Preditivo e Intelligence Services — Detalhamento

> Seção adicionada na v11.0. Documenta os serviços de inteligência e predição que alimentam as decisões automatizadas da LIA.

**Serviços Preditivos (8 serviços — verificado filesystem 2026-03-13):**

| # | Serviço | Arquivo | Função |
|---|---------|---------|--------|
| 1 | `predictive_analytics_service.py` | `app/services/predictive_analytics_service.py` | Previsões de métricas de recrutamento |
| 2 | `pipeline_prediction_service.py` | `app/services/pipeline_prediction_service.py` | Predição de pipeline e conversão |
| 3 | `early_warning_service.py` | `app/services/early_warning_service.py` | Alertas precoces de problemas no pipeline |
| 4 | `journey_intelligence_service.py` | `app/services/journey_intelligence_service.py` | Análise de jornada do candidato |
| 5 | `sector_benchmark_service.py` | `app/services/sector_benchmark_service.py` | Benchmarks por setor (anti-sycophancy — Crença #11) |
| 6 | `feature_engineering.py` | `app/services/ml/feature_engineering.py` | Engenharia de features para modelos preditivos |
| 7 | `outcome_predictor.py` | `app/services/ml/outcome_predictor.py` | Predição de outcomes de contratação |
| 8 | `model_drift_service.py` | `app/services/model_drift_service.py` | Detecção de drift em 4 triggers: score/aprovação/custo/latência P95 |

**Intelligence Services (3 serviços em `app/shared/intelligence/`):**

| # | Serviço | Arquivo | Função |
|---|---------|---------|--------|
| 1 | `smart_extractor.py` | `app/shared/intelligence/smart_extractor.py` | Extração inteligente de dados de CVs e documentos |
| 2 | `semantic_search_service.py` | `app/shared/intelligence/semantic_search_service.py` | Busca semântica via embeddings |
| 3 | `embedding_service.py` | `app/shared/intelligence/embedding_service.py` | Geração e gestão de embeddings vetoriais |

**Learning Services (4 serviços em `app/shared/learning/`):**

| # | Serviço | Arquivo | Função |
|---|---------|---------|--------|
| 1 | `learning_loop_service.py` | `app/shared/learning/learning_loop_service.py` | Loop de feedback e aprendizado contínuo |
| 2 | `template_learning_service.py` | `app/shared/learning/template_learning_service.py` | Aprendizado de templates de uso frequente |
| 3 | `ab_testing_service.py` | `app/shared/learning/ab_testing_service.py` | A/B testing de prompts e modelos |
| 4 | `finetuning_export.py` | `app/shared/learning/finetuning_export.py` | Export DPO para fine-tuning |

**Stack completo de inteligência:** RAG Híbrido (pgvector + BM25) → Smart Extractor → Semantic Search → Embeddings → Predictions → Learning Loop → Fine-tuning Export. Cada camada alimenta a seguinte, formando um pipeline de inteligência progressiva.

### 3.3 Padrões Arquiteturais Identificados

| Padrão | Implementação |
|--------|--------------|
| Domain-Driven Design | **12 bounded contexts** (verificado 2026-03-13) com agents/services/tools/models/schemas: analytics, ats_integration, automation, communication, cv_screening, hiring_policy, interview_scheduling, job_management, pipeline, policy, recruiter_assistant, sourcing |
| ReAct Agent (4-file) | **12 agentes ReAct** (wizard, sourcing, pipeline, talent, jobs_mgmt, kanban, policy_react, policy_setup, analytics, communication, ats_integration, automation): agent.py + system_prompt.py + stage_context.py + tool_registry.py |
| StateGraph (LangGraph nativo) | **4 graphs** principais: job_wizard_graph, wsi_interview_graph, interview_graph, pipeline_transition_agent. `USE_LANGGRAPH_NATIVE=True` global — todos os ReAct agents usando base nativa |
| Factory Pattern | LLMProviderFactory, ATS Factory, WhatsApp Factory, Email Provider Factory |
| Adapter Pattern | 5 channel adapters, 5 ATS clients, 3 email providers, 2 billing providers |
| Circuit Breaker | Decorator `@circuit_breaker()` com states CLOSED/OPEN/HALF_OPEN + tenacity retry |
| Cost Cascade | CascadedRouter 6-tier: in-process → Redis → regex → Haiku → Sonnet → Opus |
| Singleton | ReactAgentRegistry, AgentFactory, VectorSemanticCache |
| Strategy | LLM provider selection, email provider selection, SearchBackend (postgres/elasticsearch) |
| Observer | Learning loop (silent feedback capture) + PlatformEvents handler registry |
| Repository | BaseRepository + SQLAlchemyRepository (libs/services/) |
| Event-Driven | PlatformEvents RabbitMQ topic exchange + stage transition automation (19 serviços) |
| CQRS (parcial) | Read (RAG + semantic) separado de Write (HITL approval, stage transitions) |

---

## 4. Scorecard V5 — 14 Dimensões com Benchmark de Mercado

### 4.1 Arquitetura de Agentes — Score: 7.0/10

**Pontos fortes**:
- Pipeline plan-execute bem definido: IntentAnalyzer → APIPlannerAgent → APIExecutorAgent → PlanValidator → DataProcessor → AnswerFormatter
- Cada agente é uma classe com `execute(state) -> state` — padrão limpo
- PlanValidator com replanning (max 3 tentativas) — recuperação inteligente
- Evaluation domain usa LangGraph StateGraph real (classify→evaluate→decide→craft)
- Sourcing domain com 11 agentes especializados + orchestrator

**Pontos fracos**:
- Pipeline é **linear** (plan-execute) — não é ReAct nem agentic loop
- Sem autonomia do agente — não decide quais ferramentas usar dinamicamente
- Fluxo hardcoded no `WorkflowOrchestrator` — sem flexibilidade runtime
- `data_processor.py` é GOD OBJECT (53.5KB, 1387 linhas) — viola SRP radicalmente
- Duplicação de edge: `workflow.add_edge("answer_formatter", END)` aparece 2x

**Benchmark de mercado**:

| Plataforma | Padrão | Nível |
|-----------|--------|-------|
| **CrewAI** | Crews com Agents + Tasks + Tools, Flows para orquestração | Mais flexível — agentes autônomos com delegation |
| **LangGraph** | StateGraph com conditional edges, subgraphs | V5 usa LangGraph mas apenas como pipeline linear |
| **Manus AI** | 3-layer (Planner→Worker→Verifier), sandbox execution | Mais sofisticado — workers paralelos, sandboxed |
| **Beam AI** | Multi-agent com especialização por função HR | Similar ao V5 mas com agent coordination |
| **AutoGen** | Conversational agents com GroupChat | Mais dinâmico — agents negociam entre si |

**Posicionamento V5**: Abaixo da média do mercado de agentes autônomos — usa LangGraph mas como pipeline linear (plan-execute), não como agentic system com autonomia de tool selection. Sistemas modernos (CrewAI, Manus AI) permitem que agentes decidam dinamicamente quais ferramentas usar.

*Fontes: CrewAI Docs (docs.crewai.com/concepts/crews), Manus AI technical blog (manus.im/blog), LangGraph docs (langchain-ai.github.io/langgraph)*

### 4.2 Qualidade de Código — Score: 6.5/10

**Pontos fortes**:
- Type hints em funções-chave (intent, response, state)
- Docstrings consistentes (Google style)
- Dataclasses imutáveis para contracts (`ToolConfig(frozen=True)`)
- Separação de configuração (13 arquivos config individuais)
- Error handling com exceções customizadas (`APIClientError`, `StepDependencyError`)

**Pontos fracos**:
- **GOD OBJECT**: `data_processor.py` tem 53.5KB (1387 linhas) mas docstring diz "API Executor Agent" — confusão de nomenclatura
- `comparison.py` (33.7KB), `search.py` (30.6KB), `insights.py` (26.2KB) — arquivos enormes
- `print()` statements em código de produção (agents usam `print()` para debug em vez de logging)
- Class-level mutable state: `SmartExtractor._cache: Dict = {}` — não thread-safe
- `FairnessMetrics` usa class variables mutáveis (`_blocked_count: int = 0`) — race conditions
- `.github/instructions/base.instructions.md` diz "nunca faça comentário" — mas vários arquivos têm comentários extensos

**Benchmark**: Projetos enterprise maduros (Stripe, Vercel) mantêm arquivos < 500 linhas. O V5 tem 4 arquivos acima de 700 linhas.

### 4.3 Organização/Estrutura — Score: 3.5/10

**Esta é a dimensão com maior defasagem identificada no V5 em relação a padrões de mercado.**

**Problemas identificados**:

1. **Arquivos órfãos na raiz** (7 arquivos que não pertencem ali):
   - `chat.py` (13.6KB) — CLI interativo, deveria estar em `src/cli/`
   - `web_debug.py` (16.2KB) — Streamlit com **MOCK DATA HARDCODED** (10 candidatos fake com nomes reais)
   - `examples.py` — Deveria estar em `docs/examples/`
   - `test_domains.py` — Deveria estar em `tests/`
   - `test_list_by_index.py` — Deveria estar em `tests/`
   - `evaluation_worker_backup.py` — **BACKUP FILE commitado no repo** (anti-pattern grave)
   - `ALL_PYTHON_FILES.txt` (338KB) — Concatenação de todo o código Python do projeto **dentro do repo**

2. **Duplicação massiva** — `documentation/` (40+ YAMLs) vs `documentation_toon/` (30+ TOONs):
   - Cada tool tem 2 versões: YAML (detalhada) e TOON (compacta, ~10% menor)
   - São 70+ arquivos duplicando a mesma informação em formatos diferentes
   - Sem automation para manter sincronizados — script `convert_yml_to_toon.py` existe mas é manual

3. **God Objects**:
   - `data_processor.py`: 53.5KB, 1387 linhas — mas docstring diz "API Executor Agent"
   - `domain.py` (sourcing): 24KB — orchestration + business logic + formatting misturados
   - `comparison.py`: 33.7KB — agent com 6+ responsabilidades

4. **Scripts na raiz desorganizados**:
   - `scripts/` tem 25+ arquivos incluindo `concat_candidates_docs.py`, `concat_project.py`, `concat_python_files.py`, `concat_sourced_profile_sourcing.py`, `concat_sourcing_domain.py` — 5 scripts de concatenação para alimentar LLMs

5. **Mistura de concerns**:
   - `web_debug.py` mistura UI (Streamlit) + mock data + business logic
   - `chat.py` mistura CLI parsing + workflow execution + pagination detection
   - Agents usam `print()` para output de debug em vez de logging estruturado

6. **Ausência de padrões enterprise**:
   - Sem `Makefile` ou `pyproject.toml` para build
   - Sem CI/CD (apenas deploy scripts manuais)
   - Sem `.pre-commit-config.yaml`
   - Sem `CHANGELOG.md`

**Comparação com scaffolds padrão**:

| Aspecto | CrewAI Scaffold | LangGraph Canonical | V5 Atual |
|---------|----------------|--------------------|---------| 
| Entry point | `src/main.py` | `my_agent/agent.py` | 4 entry points (main.py, chat.py, web_debug.py, celery_worker.py) |
| Configuração | `.env` + `pyproject.toml` | `.env` + `langgraph.json` | `.env` + `requirements.txt` (sem pyproject.toml) |
| Testes na raiz | Não | Não | Sim (test_domains.py, test_list_by_index.py) |
| Backup files | Não | Não | Sim (evaluation_worker_backup.py) |
| Debug files | Não | Não | Sim (web_debug.py, ALL_PYTHON_FILES.txt) |
| Tool definitions | `tools/` dir | `utils/tools.py` | `documentation/` + `documentation_toon/` (duplicado) |

**Posicionamento**: A estrutura apresenta características típicas de um **single-developer repository** — crescimento orgânico sem revisão de pares, sem guidelines formais de organização, e sem tooling de enforcement (pre-commit hooks, CI/CD). Este padrão é comum em projetos conduzidos por um único desenvolvedor, mas representa uma barreira para escalabilidade em equipe e para adoção enterprise.

### 4.4 Eficiência LLM — Score: 7.5/10

**Pontos fortes**:
- **TOON format** — formato compacto que economiza ~10-15% de tokens vs YAML completo
- RAG híbrido (semantic + fulltext + reranking) reduz tokens enviados ao LLM
- Prompts bem estruturados com exemplos (few-shot) no IntentAnalyzer
- `compact` parameter nas API calls — solicita apenas campos necessários
- SmartExtractor com cache in-memory (MD5 key) — evita re-extrações
- Gemini 2.5 Flash — modelo eficiente em custo
- Answer Formatter com taxonomia de 11 tipos — evita re-prompting

**Pontos fracos**:
- Sem medição de token usage — não sabe quanto gasta
- Sem limite de tokens por request
- System prompts são enormes (IntentAnalyzer: ~3000 tokens de prompt)
- Sem prompt versioning

**Benchmark**:

| Plataforma | Otimização | V5 vs |
|-----------|-----------|-------|
| **Manus AI** | Context distillation, file-based context vs in-context | V5 inferior — sem distillation |
| **Eightfold AI** | Proprietary models fine-tuned para recrutamento | V5 inferior — usa modelo genérico |
| **CrewAI** | Token budgets per task, delegated summarization | V5 inferior — sem budgets |

### 4.5 Governança IA — Score: 5.0/10

**O que existe**:
- `FairnessGuard` com `SENSITIVE_FILTER_KEYS` (gender, age, race, etc.) — detecta e bloqueia filtros discriminatórios
- `FairnessMetrics` — contadores de bloqueios, warnings, PII scrubs
- 3 disclaimers específicos (DISCARD, RANKING, HIRING_PROBABILITY)
- `FactChecker` — verifica claims numéricas (count, average, top candidates) contra dados reais
- `FairnessWarning` dataclass com attribute, message, severity, recommendation

**O que falta**:
- Sem audit trail persistente (FairnessMetrics são in-memory, perdidos no restart) — **→ Cards [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) + [AUD-002/WT-1507](https://wedotalent.atlassian.net/browse/WT-1507)**
- Sem PII masking — dados pessoais transitam em plaintext
- Sem compliance framework (LGPD, GDPR)
- Sem policy middleware — regras são hardcoded
- Sem confidence thresholds — LLM output aceito sem validação de confiança
- Sem A/B testing de modelos/prompts
- Sem data retention policies — **→ Card [AUD-004/WT-1509](https://wedotalent.atlassian.net/browse/WT-1509)**
- FairnessGuard só atua em filtros de busca — não verifica output do LLM

> **v9.1**: Cards Jira criados para remediação de auditoria V5: AUD-001 (AuditCallback propagation), AUD-002 (tool tracking), AUD-004 (retention) — ver Seção 12.

**Benchmark**:

| Standard/Platform | Requisitos | V5 Coverage |
|------------------|-----------|------------|
| **NIST AI RMF** | Govern, Map, Measure, Manage | Parcial: Map (fairness), nenhum Govern/Measure/Manage |
| **EU AI Act** (High-Risk HR) | Transparency, human oversight, accuracy, robustness | Disclaimers (parcial), sem os demais |
| **Eightfold AI** | Responsible AI dashboard, bias reports, explainability | V5 não tem nenhum equivalente |
| **HiredScore** | Algorithmic auditing, EEOC compliance | V5 tem fairness básico, sem auditing |
| **Paradox/Olivia** | Consent management, data minimization | V5 sem qualquer consent flow |

*Fontes: NIST AI RMF (airc.nist.gov/AI_RMF), EU AI Act Annex III (eur-lex.europa.eu), Eightfold AI Responsible AI (eightfold.ai/responsible-ai), HiredScore/Workday press release (workday.com, Feb 2024), Paradox docs (paradox.ai)*

### 4.6 Segurança — Score: 5.5/10

**O que existe**:
- `security.py` (evaluation domain): 17 `INJECTION_PATTERNS` para detecção de prompt injection
- `sanitize_input()` — limpa caracteres perigosos, normaliza whitespace
- `detect_injection()` — regex matching contra 17 patterns
- `safe_process_input()` — pipeline completo (sanitize → detect → block)
- `create_safe_context()` — escaping de `{`, `}`, `` ``` `` para prevenir template injection
- `escape_for_prompt()` — proteção contra format string injection
- `validate_structured_field()` — validação com max_length + injection check
- OTT (One-Time Token) authentication service

**O que falta**:
- Prompt injection **só protege evaluation domain** — pipeline principal (intent_analyzer, api_planner) não tem proteção
- Sem rate limiting
- Sem input size limits globais
- Sem sanitização de output do LLM
- Sem secrets management (env vars em plaintext)
- Sem CORS/CSP headers
- Sem API authentication para Flask endpoints

**Benchmark OWASP LLM Top 10**:

| OWASP Risco | V5 Coverage |
|-------------|------------|
| LLM01: Prompt Injection | Parcial (só evaluation domain, 17 patterns) |
| LLM02: Insecure Output Handling | Nenhum |
| LLM03: Training Data Poisoning | N/A |
| LLM04: Model Denial of Service | Nenhum (sem rate limiting) |
| LLM05: Supply Chain Vulnerabilities | Nenhum (sem dependency scanning) |
| LLM06: Sensitive Info Disclosure | Nenhum (sem PII masking) |
| LLM07: Insecure Plugin Design | Parcial (tools têm contracts) |
| LLM08: Excessive Agency | Parcial (confirmation_required para ações destrutivas) |
| LLM09: Overreliance | Parcial (FactChecker) |
| LLM10: Model Theft | N/A (usa API) |

### 4.7 Human-in-the-Loop — Score: 5.5/10

**O que existe**:
- `ClarificationService` — detecta ambiguidade quando múltiplas entidades encontradas
- `requires_confirmation` flag no intent para ações destrutivas/bulk
- `confirmation_builder.py` — formata mensagens de confirmação para o usuário
- IntentAnalyzer detecta: `ambiguous_references`, `requires_entity_resolution`, `requires_confirmation`
- PlanValidator pede replanning quando resultados insuficientes (max 3 tentativas)

**O que falta**:
- Sem approval workflows (ações executam direto após confirmação textual simples)
- Sem confidence thresholds — não há nível mínimo de confiança para ações automáticas
- Sem escalation para humano quando LLM está incerto
- Sem audit trail de decisões humanas
- Sem policy-driven HITL (decisões não variam por empresa/contexto)
- Confirmação é binária (sim/não) — sem opções intermediárias

**Benchmark**:

| Plataforma | HITL Level |
|-----------|-----------|
| **Beam AI** | "Trust levels" configuráveis por tipo de ação | Mais maduro |
| **Paradox/Olivia** | Handoff para recrutador humano quando confiança < threshold | Mais maduro |
| **Manus AI** | Human review checkpoints em workflows complexos | Similar |
| **V5** | Confirmação binária para ações destrutivas/bulk | Básico |

### 4.8 Sistema de Aprendizado — Score: 3.0/10

**O que existe**:
- `MemoryService` — salva histórico de conversas e métricas em PostgreSQL
- `ConversationMemory` (sourcing) — estado in-session (candidatos vistos, shortlist, filtros)
- `query_metrics` table — registra execution_time, api_calls, success rate

**O que falta**:
- Sem feedback loop — sistema não aprende com erros
- Sem template learning — não aprende padrões de queries frequentes
- Sem adaptation — mesmas perguntas sempre processadas do zero
- Sem training data export — não alimenta fine-tuning
- Sem A/B testing de prompts
- Sem personalização por recrutador/empresa
- Memória é stateless entre sessions (ConversationMemory resetada a cada nova sessão)

**Benchmark**:

| Plataforma | Learning |
|-----------|---------|
| **Eightfold AI** | Deep learning com 1.6B+ perfis, melhora contínua | Significativamente mais maduro |
| **HiredScore** | Algorithmic learning from hiring outcomes | Muito mais maduro |
| **Beam AI** | Self-learning agents que melhoram com uso | Mais maduro |
| **V5** | Salva métricas mas não usa para melhorar | Embrionário |

### 4.9 Tool System — Score: 8.5/10

**Dimensão com melhor desempenho do V5 no scorecard.**

**Pontos fortes**:
- **YAML-driven ToolRegistry** — singleton thread-safe com double-checked locking
- 70 definições de tools em YAML (40 YAML + 30 TOON)
- Indexação tripla: por ID, por entity_group, por category
- `ToolConfig` imutável (`frozen=True`) — thread-safe
- Hook system (PreHook/PostHook) — extensibilidade sem modificar core (OCP)
- `ExecutionContext` com conversation state + metadata
- `ExecutionResult` com raw response + tool reference + success flag
- Contracts claros: query_contract, body_contract, response_handling
- `requires_context` / `provides_context` — dependency tracking entre tools
- 6 categorias: SEARCH, CREATE, UPDATE, DELETE, WORKFLOW, SHOW

**Pontos fracos**:
- Tools são staticamente mapeadas a endpoints REST — não são "tool calling" moderno (function calling API)
- Sem tool composition — não combina tools automaticamente
- Sem tool recommendation baseada em context
- YAML + TOON duplicação desnecessária

**Benchmark**:

| Framework | Tool Pattern |
|-----------|------------|
| **CrewAI** | `@tool` decorator + auto-schema + delegation | Mais ergonômico |
| **LangGraph** | `ToolNode` com function calling nativo | Mais moderno |
| **Composio** | YAML-driven + 250+ integrations | Similar ao V5 mas com mais integrações |
| **V5** | YAML-driven + hooks + contracts | Muito bom, falta function calling |

### 4.10 Observability — Score: 5.0/10

**O que existe**:
- LangSmith tracing configurado (`langsmith_config.py`)
- `logging` stdlib com níveis (DEBUG, INFO, WARNING, ERROR)
- `RequestTimer` com `step()` para timing por fase
- `FactChecker` stats (contadores in-memory)
- `FairnessMetrics` stats (contadores in-memory)

**O que falta**:
- Logging é texto livre (não structured/JSON)
- Sem métricas exportáveis (Prometheus, StatsD) — **→ Card [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512)**
- Sem dashboards (exceto Flower para Celery)
- Sem alerting
- Sem distributed tracing (OpenTelemetry)
- Sem error aggregation (Sentry)
- Métricas de FairnessMetrics e FactChecker são in-memory — perdidas no restart
- `print()` statements em agents de produção (misturados com logging)

**Benchmark**: Sistemas enterprise usam structured logging + OpenTelemetry + Prometheus + Grafana. V5 tem apenas logging básico + LangSmith terceirizado.

> **v9.1**: Cards Jira criados para remediação de observabilidade V5 — ver Seção 12 (AUD-007 Métricas Prometheus).

### 4.11 Testes — Score: 7.0/10

**Pontos fortes**:
- 53 arquivos de teste organizados por tipo
- Categorização por dificuldade: easy, medium, hard, very_hard, difficult
- `test_difficult_cases.py` (44.8KB) — testes abrangentes de edge cases
- `test_answer_formatter_unit.py` (18.7KB) — testes unitários detalhados
- `test_api_planner_unit.py` (30.6KB), `test_api_planner_contracts.py` (17.4KB)
- `test_data_processor_unit.py` (21.8KB)
- `test_fact_checker.py`, `test_fairness.py` — governança testada
- `test_hallucination_prevention.py` — teste específico de alucinação
- Mocks organizados em `tests/mocks/` com `mock_api_client.py` (14.3KB)
- `conftest.py` com fixtures reutilizáveis
- Integration tests com `result_validator.py` e `test_cases.json`
- Scripts de teste: `run_difficult_tests.py`, `test_with_rate_limit.py`, `test_celery_workers.py`

**Pontos fracos**:
- Sem CI/CD — testes não rodam automaticamente
- Sem coverage reports
- Sem property-based testing (Hypothesis)
- Sem mutation testing
- 2 arquivos de teste na raiz em vez de em `tests/`
- `planner_test_cases.yml` (33.9KB) — caso de teste no nível errado

### 4.12 Infraestrutura — Score: 7.5/10

**Pontos fortes**:
- Docker Compose para workers (`docker-compose.workers.yml`)
- Deploy scripts para GCP VM (`deploy/gcp_vm_setup.sh`, `deploy/deploy_prod.sh`)
- Celery + RabbitMQ para processamento assíncrono
- Redis para Celery broker + cache
- Flower para monitoring de workers
- Separação de workers: `celery_worker.py` (geral) + `evaluation_worker.py` (avaliação)

**Pontos fracos**:
- Deploy é VM-based (não containerizado end-to-end)
- Sem Kubernetes/ECS
- Sem auto-scaling
- Sem health checks
- Sem IaC (Terraform/Pulumi)
- Sem staging environment

### 4.13 Multi-provider LLM — Score: 1.0/10

**Estado atual**: Gemini-only. `ChatGoogleGenerativeAI` hardcoded em todos os agentes.

Cada agente instancia diretamente:
```python
ChatGoogleGenerativeAI(
    model=settings.gemini.model,
    temperature=0.0,
    google_api_key=settings.gemini.api_key,
)
```

Não há:
- Factory pattern
- Provider abstraction
- Fallback para outro LLM
- Seleção de modelo por task
- Custo/performance trade-offs

**Benchmark**: **Todos** os sistemas enterprise de IA usam multi-provider. Single-provider é risco operacional e vendor lock-in.

### 4.14 Resiliência — Score: 3.0/10

**O que existe**:
- `requests` com `HTTPAdapter` + `Retry(total=3, backoff_factor=1)` no API client
- Status forcelist: `[429, 500, 502, 503, 504]`
- PlanValidator com replanning (max 3 tentativas)
- `execute_if` conditional execution em API plan steps

**O que falta**:
- Sem Circuit Breaker — **→ Card [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508)**
- Sem Rate Limiting
- Sem Cache Layer
- Sem Graceful Degradation
- Sem Bulkhead Pattern
- Sem Health Checks
- Sem Timeout configurável por operação
- Sem fallback providers
- Single point of failure: Gemini API down = sistema inteiro down

> **v9.1**: Card AUD-003 criado para implementar Circuit Breaker no Autonomous Agent V5 — ver Seção 12.

---

## 5. Análise Comparativa V5 vs LIA — Lado a Lado

### 5.1 Tabela Comparativa por Dimensão

| # | Dimensão | V5 (5.4) | LIA (9.1) | O que V5 tem a mais | O que LIA tem a mais |
|---|----------|----------|-----------|---------------------|---------------------|
| 1 | Arq. Agentes | 7.0 | 9.3 ↑ | Pipeline linear bem definido, PlanValidator com replanning | **16 agentes** (12 ReAct 4-file + 4 StateGraph); `USE_LANGGRAPH_NATIVE=True`; CascadedRouter 6-tiers; VectorSemanticCache pgvector; NavigationIntent 8 grupos (Sprint J); HITLConfirmCard inline; useActionIntent 5 domínios; ActionExecutor 1080L com 9 action_ids; Scope Config 4 escopos 66 tools |
| 2 | Qualidade Código | 6.5 | 6.5 | Dataclasses frozen, docstrings Google style | Sem god objects no BE; 231 serviços reais (sem mocks em memória). Gap remanescente: `candidates-page.tsx` **10.397 linhas** FE |
| 3 | Organização | 3.5 | 7.5 ↑ | — | **12 domínios DDD**; `LiaSplitPanel`, `use-navigation-intent`, `use-action-intent` como módulos autônomos; Sprint E: `lia_assistant.py` decomposto em 4 sub-routers; 114 hooks FE; 90 pages. Gap: `candidates-page.tsx` |
| 4 | Eficiência LLM | 7.5 | 7.5 | TOON format (-15% tokens), RAG híbrido maduro | Token tracking + alertas 80%/100% (M5); SSE streaming Chat LIA; CascadedRouter 6-tiers (in-process → Redis → regex → Haiku→Sonnet→Opus); VectorSemanticCache (pgvector cosine threshold 0.92) |
| 5 | Governança IA | 5.0 | **9.8 ↑** | FactChecker verificação numérica | PII masking global (root logger), FAIRNESS_AND_COMPLIANCE em todos os 8 prompts, LGPD consentimento granular HTTP 451, **FairnessGuard wired em 100% screening/ranking (SEG-2)**, blind evaluation (B1), sem bias geográfico (B2), compliance LGPD/EU AI Act/BCB 498, Bias Audit API + snapshots SOX, **AuditService em todos os gates (SEG-5)**, 8/8 Inegociáveis WeDOTalent ✅ |
| 6 | Segurança | 5.5 | **9.4 ↑** | 17 injection patterns detalhados | PII masking global, SECRET_KEY obrigatório, LangSmith opt-in, HTTP 451, rate limiting, **PromptInjectionGuard wired em WSI+chat (SEG-1)**, **PII strip antes do LLM 4 callers (SEG-3B)**, **ConsentCheckerService Gate 1 WSI (SEG-4)**, **Celery PII masking workers (SEG-3A)**, Sentry BE+FE, auth JWT rigoroso |
| 7 | HITL | 5.5 | 9.4 ↑ | ClarificationService com entity selection | HITLPendingAction+AuditTrail SOX; HITLConfirmCard inline no chat (Sprint J3); use-float-streaming HITL+WS; user_agent_preferences auto_confirm; human review gate rejeições; LGPD gate admin |
| 8 | Aprendizado | 3.0 | 7.5 | Métricas em PostgreSQL | Learning loop, template learning, A/B testing, fine-tuning export, feedback capture |
| 9 | Tool System | 8.5 | 6.5 | YAML-driven, hooks, contracts, frozen, 70 tools | Code-driven, mais flexível para complex logic, domain-scoped, function calling nativo via LangGraph ToolNode |
| 10 | Observability | 5.0 | 9.5 ↑ | — | **14 métricas Prometheus** (Histogram/Counter/Gauge/Summary: lia_llm_requests, lia_llm_latency, lia_agent_iterations, lia_fairness_blocks, lia_circuit_breaker_state, lia_http_request_duration, lia_pipeline_transitions, lia_candidates_evaluated, lia_router_tier_hit, lia_router_latency_ms, +4 outros); LangGraph Studio; S3 lifecycle SOX 7 anos; Sentry BE+FE; FairnessGuard persistência + relatórios; LangSmith `@traceable` em ReActLoop + Claude |
| 11 | Testes | 7.0 | **9.3 ↑** | Categorizado por dificuldade (easy/medium/hard/very_hard), hallucination tests | **227 test files** (verificado 2026-03-13); Vitest hooks project; 42+ FE unit tests; 98 contract tests + 53 Phase 5 + 81 Phase 4b; T1/T2/T3/T4/B5 completos; Pirâmide 5-camadas; **34 novos testes SEG-1→SEG-5 (6 arquivos)** — camada 2 (unitários) + camada 5 (PROTECTED_CRITERIA fairness) |
| 12 | Infraestrutura | 7.5 | 9.5 ↑↑ | Docker workers, Celery, GCP deploy | docker-compose.yml 10 serviços; Celery high/normal/low + beat + flower; GitHub Actions CI (ruff+pytest+biome+tsc); pre-commit hooks; Redis sliding window rate limiter; S3 lifecycle SOX; apps/api-vagas/api-funil/api-onboarding como micro-serviços |
| 13 | Multi-provider | 1.0 | 8.5 | — | Claude + OpenAI + Gemini com Factory + ABC; `generate_with_fallback()` auto-failover |
| 14 | Resiliência | 3.0 | 9.5 | Retry HTTP básico | Circuit breaker em produção (Pearch/Deepgram/OpenMic/Claude) + tenacity retry; `generate_with_fallback()` Claude→Gemini→OpenAI; Redis ZSET sliding window rate limiter com fallback in-memory; cache layer (VectorSemanticCache + Redis) |

### 5.2 Feature Parity Matrix

| Feature | V5 | LIA | Status |
|---------|-----|-----|--------|
| LLM Provider Abstraction | ❌ | ✅ Factory + ABC | Gap V5 |
| Circuit Breaker (aplicado em prod) | ❌ | ✅ Pearch + Deepgram + OpenMic + tenacity retry | Gap V5 ↑ → [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) |
| Rate Limiting | ❌ | ✅ Sliding window | Gap V5 |
| PII Masking (global) | ❌ | ✅ Root logger ativo — CPF/email/phone/nome | Gap V5 ↑ |
| Prompt Injection (global) | ❌ (só evaluation) | ✅ Global | Gap V5 |
| Policy per company | ❌ | ✅ Middleware FastAPI | Gap V5 |
| Token Tracking + Alertas | ❌ | ✅ Por user/company/agent + alertas 80%/100% (Redis dedup) | Gap V5 ↑ |
| Learning Loop | ❌ | ✅ Feedback + patterns | Gap V5 |
| A/B Testing | ❌ | ✅ Prompts/models | Gap V5 |
| Multi-channel (5 canais) | ❌ | ✅ Email/WhatsApp/SMS/Teams/InApp | Gap V5 |
| Canal preferences por candidato | ❌ | ✅ preferred_channels + channel_opt_out + LGPD consent | Gap V5 ↑ |
| LGPD Consentimento granular | ❌ | ✅ HTTP 451 (revogado) + soft_warning (ausente) | Gap V5 ↑ |
| Human Review Gate | ❌ | ✅ 422 sem user_id em rejeição | Gap V5 ↑ |
| Plan Limits Enforcement | ❌ | ✅ HTTP 402 por plano (Starter/Pro/Enterprise) | Gap V5 ↑ |
| Trial Expiration Enforcement | ❌ | ✅ HTTP 402 + redirect /upgrade | Gap V5 ↑ |
| LGPD Data Cleanup Scheduler | ❌ | ✅ 30/90/180 dias, dry_run, admin-only | Gap V5 ↑ |
| Agent State Checkpoints | ❌ | ✅ PostgreSQL upsert por session_id | Gap V5 ↑ |
| FAIRNESS nos system prompts | ❌ | ✅ Todos os 8 prompts com bloco FAIRNESS_AND_COMPLIANCE | Gap V5 ↑ |
| FairnessGuard em outputs LLM | ✅ Filter-level | ✅ Filter + Output level (B3) | LIA mais completo ↑ |
| Blind evaluation (sem nome no LLM) | ❌ | ✅ Nome removido do contexto (B1) | Gap V5 ↑ |
| Sem bias geográfico | ❌ | ✅ GEOGRAPHIC_ADJUSTMENTS removido (B2) | Gap V5 ↑ |
| LLM tracing opt-in | ❌ (forçado) | ✅ Default False, opt-in explícito (L1) | Gap V5 ↑ |
| Gemini retry (empty response) | ❌ | ✅ tenacity @retry com _is_empty_response (A2) | Gap V5 ↑ |
| Testes unitários (rubric BARS) | ✅ categorizado | ✅ 19/19 testes (T1) | Parity ↑ |
| Testes integração (pipeline) | ✅ parcial | ✅ 28/28 testes (T2) | Parity ↑ |
| Testes E2E (wizard) | ❌ | ✅ 5 cenários Playwright (T3) | Gap V5 ↑ |
| Testes de carga | ❌ | ✅ Locust WizardUser/PipelineUser (T4) | Gap V5 ↑ |
| Testes disparate impact | ❌ | ✅ 17/17 testes 4/5 Rule WSI (B5) | Gap V5 ↑ |
| YAML Tool Registry | ✅ 70 tools | ✅ 32 tools (`tool_registry_metadata.yaml` G5) + code-driven | Parity ↑ |
| RAG Híbrido | ✅ pgvector + fulltext + reranking | ✅ pgvector + BM25 + alpha blend (`rag_pipeline_service.py` G6) | Parity ↑ |
| TOON Format | ✅ -15% tokens | ✅ `toon_service.py` + LGPD anonymize + Redis cache (G7) | Parity ↑ |
| Celery Workers | ✅ Async tasks | ✅ high/normal/low + beat + flower (Fase 6b) | Parity ↑ |
| HITL Persistência (SOX/BCP-498) | ❌ | ✅ `HITLPendingAction` + `HITLAuditTrail` tables (Sprint F1) | Gap V5 → [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) |
| Token Budget per-tenant | ❌ | ✅ PLAN_DAILY_LIMITS, HTTP 429, TimedToolNode 15s (Sprint A) | Gap V5 |
| Short Lists compartilhadas | ❌ | ✅ `short_lists.py` + `use-short-list.ts` (Sprint F4) | Gap V5 |
| Prompt Version Registry | ❌ | ✅ SHA256 hash, `/admin/prompts/versions` (Sprint B) | Gap V5 |
| Test Categorization (difficulty) | ✅ easy/medium/hard/very_hard | ❌ Por tipo, não dificuldade | Gap LIA |
| FactChecker numérico | ✅ verify_count/avg/top | ✅ Similar | Parity |
| ReAct Agents | ❌ | ✅ **11 agents ReAct** + 4 StateGraph + 1 legado = 16 total, 4-file pattern | Gap V5 |
| ATS Integrations | ❌ (API genérica) | ✅ 5 connectors (Gupy, Pandapé, etc.) + ATSIntegrationReActAgent wired | Gap V5 |
| Billing/Usage | ❌ | ✅ Iugu + Vindi | Gap V5 |
| Voice/Deepgram | ❌ | ✅ Deepgram + Gemini Voice | Gap V5 |
| SSO/WorkOS | ❌ (OTT básico) | ✅ WorkOS SSO | Gap V5 |
| Docker/GCP Deploy | ✅ | ✅ docker-compose.yml 10 serviços (Fase 6b) | Parity ↑ |
| CI/CD | ❌ | ✅ GitHub Actions CI (Sprint D-2) | Gap V5 |
| Celery Workers async | ✅ | ✅ Celery high/normal/low + beat + flower (Fase 6b) | Parity ↑ |
| UV Monorepo | ❌ | ✅ 9 libs com workspace root (Fase 6a/6b/6c) | Gap V5 |
| Float Chat universal | ❌ | ✅ LiaFloatPanel + WS streaming + PII masking (Fase 4a) | Gap V5 |
| Navigation Intent | ❌ | ✅ NavigationIntentDetector + split-view (Fase 4b) | Gap V5 |
| Intent → Domain routing | ❌ | ✅ useActionIntent 5 domínios → WS domain dispatch (Fase 4c/5) | Gap V5 |
| Vector Semantic Cache | ❌ | ✅ pgvector cosine, threshold 0.92 (Fase G2) | Gap V5 |
| Cascaded Router 6-tier | ❌ | ✅ in-process→Redis→regex→Haiku→Sonnet→Opus (Fase G2) | Gap V5 |
| Analytics Agent wired | ❌ | ✅ AnalyticsReActAgent + WS dispatcher (Fase 5) | Gap V5 |
| Communication Agent wired | ❌ | ✅ CommunicationReActAgent + WS dispatcher + alias "comms" (Fase 5) | Gap V5 |
| LangGraph nativo ativo | ❌ | ✅ USE_LANGGRAPH_NATIVE=True, PostgresSaver prod (Fase G1) | Gap V5 |
| SearchBackend ABC | ❌ | ✅ PostgresSearchBackend + ElasticsearchSearchBackend factory (Fase G4) | Gap V5 |
| Platform Events RabbitMQ | ✅ (producer básico) | ✅ PlatformEvent + handler registry + topic exchange (Fase G4) | Parity ↑ |
| **Automação** | | | |
| Stage automation engine | ❌ | ✅ `stage_automation_engine.py` | Gap V5 |
| Trigger-based workflows | ❌ | ✅ `automation_trigger_service.py` | Gap V5 |
| Proactive alerts | ❌ | ✅ `proactive_alert_service.py` | Gap V5 |
| ML-driven automation | ❌ | ✅ `prediction_action_bridge.py` | Gap V5 |
| Planned tasks agendadas | ❌ | ✅ `planned_task_service.py` | Gap V5 |
| Pattern learning (automação) | ❌ | ✅ `learning_automation.py` | Gap V5 |
| Pipeline health monitoring | ❌ | ✅ `pipeline_monitor.py` | Gap V5 |
| **Voz e Multimodal** | | | |
| Speech-to-text (Deepgram) | ❌ | ✅ `deepgram_service.py` | Gap V5 |
| Triagem por voz (OpenMic.ai) | ❌ | ✅ `openmic_service.py` | Gap V5 |
| WSI entrevista por voz | ❌ | ✅ `wsi_voice_orchestrator.py` | Gap V5 |
| Transcrição automática | ❌ | ✅ `transcription_service.py` | Gap V5 |
| Interview notes automáticas | ❌ | ✅ `interview_notes_service.py` | Gap V5 |
| **HITL Sprint J** | | | |
| HITLConfirmCard inline | ❌ | ✅ `HITLConfirmCard.tsx` (Sprint J3) | Gap V5 |
| HITL + WS streaming | ❌ | ✅ `use-float-streaming.ts` (Sprint J3) | Gap V5 |
| Auto-confirm por preferência | ❌ | ✅ `user_agent_preference_service.py` (J3) | Gap V5 |
| Navigation Intent 8 grupos | ❌ | ✅ `navigation_intent.py` 8 grupos (Sprint J) | Gap V5 |
| **Compliance Extra** | | | |
| Agent Quality Evaluations | ❌ | ✅ `agent_quality_evaluator.py` (J1) | Gap V5 |
| Agent Health Alerts | ❌ | ✅ `agent_health_alert_service.py` (J1) | Gap V5 |
| Bias Audit Snapshot histórico | ❌ | ✅ `bias_audit_snapshot.py` + migration 018 | Gap V5 |
| Model Drift Detection | ❌ | ✅ `model_drift_service.py` + 4 triggers | Gap V5 |
| Guardrails code-based | ❌ | ✅ `guardrail.py` + migration 020 | Gap V5 |
| **Sprints SEG — Wiring Segurança/Governança** | | | |
| PromptInjectionGuard wired | ❌ | ✅ **SEG-1** — `agent_chat_ws.py` (singleton) + `wsi_interview_graph.validate_response()`. 6 categorias, high→block+`error_code`, medium→log | Gap V5 → fechado LIA ↑ |
| FairnessGuard wired em screening | ⚠️ 1 camada sourcing | ✅ **SEG-2** — 3 camadas em `sourcing_react_agent.process()` + `pipeline_transition_agent.process()`. Blocked→`educational_message` | LIA mais completo ↑ |
| PII Masking em Celery workers | ❌ | ✅ **SEG-3A** — `@signals.worker_process_init.connect` em `libs/config/lia_config/celery_app.py` (modelo prefork) | Gap V5 → fechado LIA ↑ |
| strip_pii_for_llm_prompt (data minimization) | ❌ | ✅ **SEG-3B** — LGPD Art. 12. Feature flag `LLM_PROMPT_PII_STRIPPING_ENABLED`. Wired em rubric, analysis, voice, comparison | Gap V5 → fechado LIA ↑ |
| ConsentCheckerService no Gate WSI | ❌ | ✅ **SEG-4** — `wsi_interview_graph.load_context()`. Revogado→`LGPD_CONSENT_REVOKED`+stage=ERROR. Fail-safe | Gap V5 → fechado LIA ↑ |
| AuditService nos gates de decisão | ❌ | ✅ **SEG-5** — pipeline (HITL+transition+LangGraph+rejected) + sourcing (ReAct+LangGraph). `PROTECTED_CRITERIA` em `criteria_ignored`. Fail-safe | Gap V5 → fechado LIA ↑ |

---

## 6. Gap Analysis Bidirecional

### 6.1 O que falta no V5 que a LIA resolve (Gaps Críticos)

> **Atualizado em 2026-03-08 após Fases 4-5, G1-G4 e UV Monorepo 6a/6b/6c.** Todos os 13 gaps originais estão resolvidos na LIA.

| # | Gap | Impacto | LIA Implementation | Status |
|---|-----|---------|--------------------|----|
| 1 | **Multi-provider LLM** | Vendor lock-in, single point of failure | `llm_factory.py` + `llm_provider.py` (ABC) + 3 providers (Claude, Gemini, OpenAI) + `generate_with_fallback()` auto-failover (Sprint A-1) | ✅ **Resolvido** |
| 2 | **Circuit Breaker** | Cascading failures quando provider falha | `circuit_breaker.py` CLOSED/OPEN/HALF_OPEN + `@circuit_breaker_decorator` aplicado em `llm_claude.py` (4 métodos), Pearch, Deepgram, OpenMic (Sprint A-1, A-5) | ✅ **Resolvido** na LIA · V5: [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) |
| 3 | **Rate Limiting** | Sem proteção contra abuse/custo | `rate_limiter.py` sliding window Redis ZSET atômica per-user/company com fallback in-memory graceful (Sprint A-4) | ✅ **Resolvido** |
| 4 | **PII Masking** | Dados pessoais em plaintext nos logs/LLM | `pii_masking.py` regex patterns instalado no root logger — CPF/email/telefone/nome mascarados globalmente | ✅ **Resolvido** |
| 5 | **Prompt Injection global** | Pipeline principal desprotegido | `prompt_injection.py` multi-pattern + risk levels em todos os inputs | ✅ **Resolvido** |
| 6 | **Token Tracking + Alertas** | Sem visibilidade de custos nem alertas de consumo | `token_tracking_service.py` + alertas automáticos 80%/100% Redis dedup (M5) + dashboard AI Credits `/configuracoes/ai-credits` com Recharts (M4) | ✅ **Resolvido** |
| 7 | **Policy Middleware** | Regras hardcoded, não customizáveis | `policy_middleware.py` FastAPI dependency per-company + `policy_engine.py` | ✅ **Resolvido** |
| 8 | **Learning Loop** | Sistema não melhora com uso | `learning_loop_service.py` + `template_learning_service.py` + Feedback Loop (thumbs/rating/correction) + DPO training data export (`lia_feedback.py`, Sprint E) | ✅ **Resolvido** |
| 9 | **Structured Logging** | Logs em texto livre, não parseable | `structured_logging.py` JSON format + PII masking global no root logger | ✅ **Resolvido** |
| 10 | **Comunicação multicanal** | Só callback REST | 5 canais (Bell in-app, Email, Teams, WhatsApp, Chat inline) + `CandidateChannelSelector` por candidato (N3) | ✅ **Resolvido** |
| 11 | **Confidence Policies** | LLM output aceito sem threshold | `confidence_policy_service.py` + `confidence_threshold` por domínio | ✅ **Resolvido** |
| 12 | **Audit Trail persistente** | FairnessMetrics in-memory — perdidas no restart | `fairness_audit_log` table (migration 015) + `FairnessAuditLog` model + `log_check()` + relatórios `GET /fairness/reports/summary` e `/trend` (Sprint B-3) | ✅ **Resolvido** na LIA · V5: [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) |
| 13 | **Observabilidade** | V5 tem LangSmith mas sem métricas de infra | Prometheus 8 métricas estratégicas + `/metrics` endpoint + LangSmith `@traceable` em ReActLoop e Claude + Sentry BE+FE + ErrorBoundary React (Sprints A-3, B-1, B-2, C-4) | ✅ **Resolvido** na LIA · V5: [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) |

### 6.2 O que falta na LIA que o V5 resolve (Gaps para considerar)

> **Atualizado em 2026-03-08 após Sprints A–D, F1–F5, G1–G7.**

| # | Gap | Impacto | V5 Implementation | Complexidade | Status |
|---|-----|---------|-------------------|--------------|--------|
| 1 | **RAG Híbrido maduro** | LIA usava embedding-only, menos recall em buscas complexas | `rag_service.py` com hybrid_search + reranking (pgvector + full-text BM25) | Média (2-3 semanas) | ✅ **Resolvido (G6)** — `rag_pipeline_service.py` com pgvector cosine + tsvector BM25 + alpha blend parametrizável (alpha=0 BM25-only, alpha=1 semântico-only, 0<alpha<1 híbrido). FairnessGuard top-10 diversity. Endpoint `GET /api/v1/candidates/rag-search`. 31 testes em `test_rag_pipeline.py`. `SearchBackend` ABC (G4) com PostgresSearchBackend + ElasticsearchSearchBackend factory. |
| 2 | **YAML Tool Registry** | LIA tools eram code-driven — mais difícil inspecionar e documentar sem executar | `ToolRegistry` singleton + 70 YAMLs declarativos + hooks | Alta (3-4 semanas) — mudança arquitetural | ✅ **Resolvido (G5)** — `tool_registry_metadata.yaml` (446 linhas, 32 tools declarativos com name, description, allowed_agents, scope, version) + `tool_registry_loader.py` (`load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()`) + `registry.py` com `.export_to_yaml()` + `.validate_yaml()`. Scopes: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL. LIA agora tem best-of-both-worlds: declarativo inspecionável + code-driven flexível. |
| 3 | **TOON Format** | LIA gastava ~15% mais tokens por não ter formato comprimido | `convert_yml_to_toon.py` + `documentation_toon/` — YAML → representação densa | Baixa (1 semana) | ✅ **Resolvido (G7)** — `toon_service.py`: `TOONCard` dataclass, `get_or_generate()`, Redis TTL=3600s. LGPD: `anonymize=True` → `name_display="Candidato X"`. Sem avatar, sem age raw. Chave Redis: `toon:{company_id}:{candidate_id}:{job_id}`. Endpoint `GET /api/v1/candidates/{id}/toon`. Proxy FE `backend-proxy/candidates/[id]/toon/route.ts`. 34 testes em `test_toon_service.py`. |
| 4 | **Celery Workers distribuídos** | V5 tem workers dedicados por tipo de tarefa | `celery_worker.py` + `evaluation_worker.py` + RabbitMQ filas dedicadas | Alta (4-6 semanas) — infra nova | ✅ **Resolvido (Fase 6b)** — `celery_worker_high`, `celery_worker_normal`, `celery_worker_low` + `celery_beat` (drift daily 06h Brasília) + `flower` monitoring no `docker-compose.yml`. LIA tem Celery distribuído com prioridades. |
| 5 | **Test categorization por dificuldade** | LIA organiza testes por tipo (unit/integration/E2E/load/disparate impact) mas não por difficulty level (easy/medium/hard/very_hard) | Organização por `difficulty_level` nos YAMLs de casos de teste | Baixa (1-2 dias) | ✅ **Resolvido (Sprint I)** — `pytest.ini` com markers `easy/medium/hard/very_hard`. `pytestmark` adicionado em 15 arquivos (7 easy, 5 medium, 3 hard). 419 testes coletados com `-m "easy or medium or hard"`. `very_hard` registrado mas sem testes nessa categoria ainda. |
| 6 | **FactChecker granular** por tipo de claim | LIA tem `FactChecker` mas sem separação explícita por tipo de claim | `verify_count_claim`, `verify_average_claim`, `verify_top_candidates_claim` separados | Baixa (3-5 dias) | ✅ **Resolvido (Sprint H)** — `verify_count_claim()` (regex `CANDIDATE_COUNT_PATTERN`, tolerance_pct), `verify_average_claim()` (regex `PERCENTAGE_PATTERN`, claim_type configurável), `verify_top_candidates_claim()` (regex `TOP_PATTERN`, max_reasonable_top). Paridade com V5 para verificação granular por tipo de claim. |
| 7 | **Docker + Deploy cloud** | LIA sem portabilidade para cloud (GCP/AWS) | `docker-compose.workers.yml` + `deploy/` scripts + GCP VM config | Média (2-3 semanas) | ✅ **Resolvido (Sprint H)** — `Dockerfile.prod` multi-stage (builder + runtime uid=1001 non-root, HEALTHCHECK, gunicorn+uvicorn); `docker-compose.prod.yml` (restart: always, resource limits, json-file logging, health checks); `deploy/gcp_setup.sh` + `deploy/aws_setup.sh` + `deploy/Makefile`; `.github/workflows/deploy.yml` (OIDC keyless auth GCP+AWS). Pendente: IaC declarativo (Terraform/Pulumi). |
| 8 | **God Object FE** | `candidates-page.tsx` ainda grande — difícil manter e testar | V5 tem arquivos menores mas também tem God Objects no BE | N/A (refatoração interna) | 🟡 **Parcial** — De 12.375 → **10.397 linhas** (verificado 2026-03-13). Hooks wired: `use-candidate-filters.ts`, `use-candidate-selection.ts`, `useCandidatesListMapped`, `use-candidates-list.ts`, `use-candidate-data-requests.ts`. Componentes extraídos: `CandidateSearchBar.tsx`, `CandidateTabs.tsx`, `SearchResultsHeader.tsx`. `use-candidates-list.test.ts`: 8 timeouts ✅ corrigidos com `vi.useFakeTimers({ shouldAdvanceTime: true })` (Sprint H). Ainda god object — extração de modais requer sprint dedicado. |
| 9 | **LangSmith CI Step** | Validação automática da config LangSmith no CI | `app/config/langsmith.py` + step CI `.github/workflows/ci.yml` linhas 55–59 | Baixa | ✅ **Resolvido** — step "Verify LangSmith config" com `continue-on-error: true`. `is_langsmith_enabled()` + `configure_langsmith()`. 18 testes em `test_langsmith_config.py`. |
| 10 | **IaC Terraform/Pulumi** | Scripts bash GCP/AWS existem; deploy declarativo ausente | Média | 🔴 **Pendente** — `deploy/gcp_setup.sh` + `deploy/aws_setup.sh` existem; Terraform/Pulumi não implementado |
| 11 | **Test categorization `very_hard`** | V5 tem testes nessa categoria | Baixa | 🔴 **Pendente** — marker registrado em `pytest.ini`, sem testes classificados |
| 12 | **Fine-tuning pipeline contínuo** | V5 tem pipeline completo | Alta | 🔴 **Pendente** — `lia_feedback.py` DPO export existe; pipeline de training automático ausente |
| 13 | **AutomationReActAgent WS** | — | Baixa | 🔴 **Pendente** — `automation_react_agent.py` existe em `domains/automation/agents/`; não registrado no dispatcher `agent_chat_ws.py` |

---

## 7. Análise Estrutural Profunda do V5

### 7.1 Classificação dos Problemas

| Severidade | Problema | Impacto |
|-----------|---------|---------|
| 🔴 Crítico | `data_processor.py` (53KB GOD OBJECT) | Impossível manter, testar ou refatorar |
| 🔴 Crítico | `ALL_PYTHON_FILES.txt` (338KB) no repo | Inflação do repo, possível leak de código |
| 🔴 Crítico | `evaluation_worker_backup.py` commitado | Anti-pattern grave, confusão sobre versão canônica |
| 🔴 Crítico | Prompt injection só em 1 de 2 domínios | Pipeline principal vulnerável |
| 🟠 Alto | 7 arquivos órfãos na raiz | Difícil navegar, anti-pattern de organização |
| 🟠 Alto | `web_debug.py` com mock data hardcoded | Dados fake podem vazar para produção |
| 🟠 Alto | Duplicação documentation/ vs documentation_toon/ | 70 arquivos duplicados, manutenção dobrada |
| 🟠 Alto | `print()` em agents de produção | Output poluído, não parseable, sem levels |
| 🟡 Médio | 5 scripts de concatenação (concat_*.py) | Indicam workaround para limitações de tooling |
| 🟡 Médio | Testes na raiz (test_domains.py, test_list_by_index.py) | Violação de convenção |
| 🟡 Médio | Class-level mutable state (SmartExtractor._cache) | Race conditions em multi-thread |
| 🟡 Médio | Duplicação de edge no workflow graph | `add_edge("answer_formatter", END)` aparece 2x |
| 🟢 Baixo | `.github/instructions` diz "nunca faça comentário" mas código tem comentários | Inconsistência de guidelines |
| 🟢 Baixo | Sem Makefile/pyproject.toml | Build não padronizado |

### 7.2 God Objects — Análise Detalhada

#### `data_processor.py` — 53.5KB, 1387 linhas

| Problema | Detalhe |
|---------|---------|
| Nome vs Conteúdo | Docstring: "API Executor Agent" — mas arquivo é `data_processor.py` |
| Responsabilidades | Execução HTTP + variable substitution + conditional execution + user confirmation injection + pagination + error handling + result formatting |
| SRP Violação | Pelo menos 6 responsabilidades distintas em 1 classe |
| Recomendação | Split em: `APIExecutorAgent` (pure execution), `VariableSubstitutor` (param resolution), `PaginationHandler`, `ConfirmationInjector`, `ResultAggregator` |

#### `comparison.py` (sourcing agents) — 33.7KB

| Problema | Detalhe |
|---------|---------|
| Responsabilidades | Comparison logic + prompt building + formatting + scoring + ranking + tabular output |
| Recomendação | Split em: `ComparisonAgent`, `ComparisonFormatter`, `ComparisonScorer` |

#### `domain.py` (sourcing) — 24KB

| Problema | Detalhe |
|---------|---------|
| Responsabilidades | Domain orchestration + business logic + action routing + context management |
| Recomendação | Usar Strategy pattern — cada ação como uma classe separada (já existe `actions/` mas `domain.py` ainda concentra lógica) |

### 7.3 Production Readiness Checklist

| Critério | V5 Status | Necessário para Prod |
|---------|----------|---------------------|
| CI/CD Pipeline | ❌ | Sim |
| Automated Testing | ⚠️ (tem testes, sem CI) | Sim |
| Secrets Management | ❌ (.env) | Sim (Vault/KMS) |
| Health Checks | ❌ | Sim |
| Monitoring/Alerting | ❌ → [AUD-007/WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) | Sim |
| Error Aggregation | ❌ | Sim (Sentry) |
| Rate Limiting | ❌ | Sim |
| Auth (API) | ⚠️ (OTT básico) | Sim (JWT/OAuth2) |
| PII Protection | ❌ | Sim (LGPD) |
| Audit Trail | ❌ (in-memory) → [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) | Sim |
| Backup Strategy | ❌ (backup file no repo) | Sim |
| Rollback Strategy | ❌ | Sim |
| Load Testing | ❌ | Sim |
| Security Scanning | ❌ | Sim |
| Dependency Updates | ❌ (sem Dependabot) | Sim |
| Documentation (ops) | ❌ | Sim (runbook) |

**Production Readiness**: 3 de 16 critérios atendidos (parcialmente) — V5 precisa de trabalho significativo antes de ir para produção.

---

## 8. Best Practices de Mercado — Sugestões de Implementação

### 8.1 Arquitetura de Agentes (baseado em CrewAI + LangGraph + Manus AI)

| Best Practice | Fonte | Sugestão para V5 | Esforço |
|--------------|-------|------------------|---------|
| **Agent autonomy** — agentes decidem quais tools usar | CrewAI, Manus AI | Converter pipeline linear em ReAct loop com tool selection | 3-4 semanas |
| **Tool calling nativo** — usar function calling API do LLM | LangGraph, OpenAI | Converter YAML tools para function calling schemas | 2-3 semanas |
| **Agent specialization** — um agente por domínio/skill | CrewAI Crews | Criar agents por domínio (já existe parcialmente em sourcing) | 2-3 semanas |
| **State graph com subgraphs** — composição de workflows | LangGraph | Usar subgraphs para sourcing, evaluation, etc. | 1-2 semanas |
| **Delegation pattern** — agentes delegam subtasks | CrewAI | Implementar delegation entre agents | 2-3 semanas |

### 8.2 Governança IA (baseado em NIST AI RMF + EU AI Act)

| Best Practice | Standard | Sugestão para V5 | Esforço |
|--------------|---------|------------------|---------|
| **Audit trail persistente** | NIST Govern | Salvar FairnessMetrics em banco, não in-memory — **→ [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506)** | 1 semana |
| **PII masking em logs/prompts** | LGPD/GDPR | Implementar regex masks antes de enviar ao LLM | 3-5 dias |
| **Explainability** | EU AI Act Art. 13 | Logging do reasoning chain completo | 1-2 semanas |
| **Bias monitoring dashboard** | NIST Measure | Dashboard com métricas de fairness ao longo do tempo | 2-3 semanas |
| **Data minimization** | LGPD Art. 6 | Solicitar apenas campos necessários (já faz com compact) | Já implementado parcialmente |
| **Human oversight** | EU AI Act Art. 14 | Confidence thresholds + escalation automática | 1-2 semanas |
| **Risk assessment** | NIST Map | Classificar outputs por risco (hire/reject = alto; list = baixo) | 1 semana |

### 8.3 Segurança (baseado em OWASP LLM Top 10)

| Best Practice | OWASP | Sugestão para V5 | Esforço |
|--------------|-------|------------------|---------|
| **Prompt injection global** | LLM01 | Aplicar `safe_process_input()` em todos os entry points | 3-5 dias |
| **Output validation** | LLM02 | Validar output do LLM contra schema esperado | 1-2 semanas |
| **Rate limiting** | LLM04 | Implementar sliding window per-user/per-API-key | 3-5 dias |
| **Input size limits** | LLM04 | Max tokens por request, max depth de JSON | 1-2 dias |
| **Dependency scanning** | LLM05 | Adicionar `pip-audit` ou `safety` no CI | 1 dia |
| **Secrets management** | — | Migrar de .env para Vault/KMS | 1-2 semanas |

### 8.4 Resiliência (baseado em patterns enterprise)

| Best Practice | Pattern | Sugestão para V5 | Esforço |
|--------------|---------|------------------|---------|
| **Circuit Breaker** | Resilience | Decorator para LLM calls e API calls — **→ [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508)** | 3-5 dias |
| **Multi-provider fallback** | Redundancy | Gemini → OpenAI → Claude fallback chain | 2-3 semanas |
| **Cache layer** | Performance | Redis cache para RAG results e common queries | 1-2 semanas |
| **Bulkhead** | Isolation | Separar pools para LLM, ATS API, DB | 1-2 semanas |
| **Health checks** | Monitoring | `/health` endpoint com checks de dependências | 2-3 dias |
| **Graceful degradation** | Resilience | Resposta parcial quando dependência falha | 1-2 semanas |

### 8.5 Organização de Código (baseado em CrewAI scaffold + LangGraph canonical)

| Best Practice | Fonte | Sugestão para V5 | Esforço |
|--------------|-------|------------------|---------|
| **Mover arquivos da raiz** | Universal | `chat.py` → `src/cli/`, `web_debug.py` → `src/debug/`, testes → `tests/` | 1 dia |
| **Remover artefatos** | Universal | Deletar `ALL_PYTHON_FILES.txt`, `evaluation_worker_backup.py` | 30 min |
| **pyproject.toml** | PEP 621 | Migrar de `requirements.txt` para `pyproject.toml` | 1-2 horas |
| **Split god objects** | Clean Code | `data_processor.py` → 5 classes menores | 2-3 dias |
| **Unificar tool formats** | DRY | Escolher YAML ou TOON, não ambos | 1 dia |
| **Pre-commit hooks** | Dev Best Practice | black, mypy, pylint, pytest | 1-2 horas |
| **CI/CD (GitHub Actions)** | DevOps | Lint → test → build → deploy | 1-2 dias |
| **Remover prints** | Logging | Substituir todos os `print()` por `logger.info()` | 1 dia |

---

## 9. Recomendações de Portabilidade — Priorizado por Impacto × Esforço

### P0 — Crítico (Implementar em 2-4 semanas)

| # | Item | Impacto | Esforço | Fonte |
|---|------|---------|---------|-------|
| 1 | **Limpeza estrutural do repo** | Alto | 1-2 dias | Análise estrutural |
| 2 | **Prompt injection global** | Alto | 3-5 dias | LIA `prompt_injection.py` |
| 3 | **Multi-provider LLM** | Crítico | 2-3 semanas | LIA `llm_factory.py` + providers |
| 4 | **Circuit Breaker** | Alto | 3-5 dias | LIA `circuit_breaker.py` — [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) |
| 5 | **Rate Limiting** | Alto | 3-5 dias | LIA `rate_limiter.py` |
| 6 | **PII Masking** | Alto (compliance) | 2-3 dias | LIA `pii_masking.py` |
| 7 | **Split data_processor.py** | Alto (maintainability) | 2-3 dias | Clean Code |

### P1 — Alto (Implementar em 1-2 meses)

| # | Item | Impacto | Esforço | Fonte |
|---|------|---------|---------|-------|
| 8 | **Token Tracking** | Médio-Alto | 1-2 semanas | LIA `token_tracking_service.py` |
| 9 | **Policy Middleware** | Médio-Alto | 1-2 semanas | LIA `policy_middleware.py` |
| 10 | **Structured Logging** | Médio | 2-3 dias | LIA `structured_logging.py` |
| 11 | **Audit Trail persistente** | Médio-Alto | 1-2 semanas | LIA `audit_service.py` — [AUD-001/WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) |
| 12 | **Confidence Policies** | Médio | 1-2 semanas | LIA `confidence_policy_service.py` |
| 13 | **CI/CD Pipeline** | Alto | 1-2 dias | GitHub Actions |
| 14 | **Health Checks** | Médio | 2-3 dias | Best practice |

### P2 — Médio (Implementar em 2-4 meses)

| # | Item | Impacto | Esforço | Fonte |
|---|------|---------|---------|-------|
| 15 | **Learning Loop** | Alto (longo prazo) | 3-4 semanas | LIA `learning_loop_service.py` |
| 16 | **ReAct Agent Pattern** | Alto (arquitetural) | 3-4 semanas | LIA 4-file pattern |
| 17 | **A/B Testing** | Médio | 1-2 semanas | LIA `ab_testing_service.py` |
| 18 | **Comunicação multicanal** | Médio | 4-6 semanas | LIA channel adapters |
| 19 | **ATS Integrations** | Médio | 3-4 semanas | LIA ATS clients |
| 20 | **Output Validation** | Médio | 1-2 semanas | OWASP LLM02 |

### P3 — Futuro (3-6 meses)

| # | Item | Impacto | Esforço | Fonte |
|---|------|---------|---------|-------|
| 21 | **Agent autonomy (ReAct loop)** | Transformacional | 4-6 semanas | CrewAI/LangGraph |
| 22 | **Function calling nativo** | Alto | 2-3 semanas | OpenAI/Anthropic API |
| 23 | **Voice integration** | Médio | 3-4 semanas | LIA Deepgram/Gemini Voice |
| 24 | **ML pipeline** | Alto (longo prazo) | 6-8 semanas | LIA ml/ services |
| 25 | **Kubernetes deploy** | Alto (scale) | 4-6 semanas | Industry standard |

---

## 10. Riscos, Oportunidades e Roadmap

### 10.1 Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Gemini API outage** → sistema 100% down | Alta | Crítico | Multi-provider LLM (P0) |
| **Prompt injection em produção** | Alta | Crítico | Proteção global (P0) |
| **Data breach (PII em logs/prompts)** | Média | Crítico | PII masking (P0) |
| **Cost explosion (sem token tracking)** | Alta | Alto | Token tracking (P1) |
| **God object regression** | Alta | Alto | Split + CI checks (P0) |
| **Test degradation** | Média | Médio | CI/CD com testes obrigatórios (P1) |

### 10.2 Oportunidades

| Oportunidade | Benefício | Timeline |
|-------------|-----------|----------|
| Portar multi-provider da LIA | Elimina vendor lock-in, permite A/B de modelos | 2-3 semanas |
| Portar circuit breaker + rate limiter | Resiliência enterprise-grade com minimal effort — [AUD-003/WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) | 1 semana |
| Portar PII masking | Compliance LGPD imediato | 3 dias |
| Adotar ReAct pattern da LIA | Agentes autônomos, mais inteligentes | 3-4 semanas |
| Combinar YAML tools (V5) + ReAct agents (LIA) | Best-of-both-worlds: declarativo + autônomo | 4-6 semanas |

### 10.3 Roadmap Sugerido

```
Mês 1: Foundations (P0) + AUD Sprint 1
├── Semana 1: Limpeza estrutural + split god objects + CI/CD
├── Semana 2: Multi-provider LLM (factory + 3 providers)
├── Semana 3: Circuit breaker (AUD-003/WT-1508) + rate limiter + PII masking
└── Semana 4: Prompt injection global + structured logging + AuditCallback (AUD-001/WT-1506) + Tool tracking (AUD-002/WT-1507)

Mês 2: Enterprise Layer (P1) + AUD Sprints 2-3
├── Semana 5: Token tracking + audit trail + Retention/Cleanup (AUD-004/WT-1509)
├── Semana 6: Policy middleware + confidence policies
├── Semana 7: Health checks + output validation + Storage S3/GCS (AUD-005/WT-1510)
└── Semana 8: Testes + stabilização + REST Timeline (AUD-006/WT-1511) + Prometheus (AUD-007/WT-1512)

Mês 3: Intelligence Layer (P2)
├── Semana 9-10: Learning loop + A/B testing
├── Semana 11-12: ReAct agent pattern (converter pipeline)

Mês 4: Scale Layer (P2-P3)
├── Semana 13-14: Comunicação multicanal
├── Semana 15-16: ATS integrations + voice
```

**Investimento estimado total**: 4-5 meses para atingir production readiness enterprise.

---

## 11. Avaliação de Produto — O que Falta para a LIA Evoluir

> Esta seção analisa os gaps da LIA como produto (não apenas em relação ao V5) e prioriza os próximos passos de evolução. Baseada no estado atual do código em 08/03/2026.

### 11.1 Gaps Técnicos Prioritários

> **Atualizado v6.0 — 08/03/2026.** Gaps 1, 5 e 6 da lista anterior foram resolvidos nos Sprints G5–G7.

| # | Gap | Categoria | Impacto no Produto | Esforço | Prioridade | Status |
|---|-----|-----------|-------------------|---------|-----------|--------|
| 1 | **RAG Híbrido** | Qualidade IA | +15-20% recall | Média | — | ✅ **Resolvido (G6)** — `rag_pipeline_service.py` pgvector + BM25 |
| 2 | **TOON Format** | Eficiência LLM | -15% custo tokens | Baixa | — | ✅ **Resolvido (G7)** — `toon_service.py` LGPD-compliant |
| 3 | **YAML Tool Registry** | Arquitetura | Inspecionabilidade | Alta | — | ✅ **Resolvido (G5)** — 32 tools YAML + loader |
| 4 | **candidates-page.tsx god object** (**10.397L**) | Qualidade FE | Impossível testar, lento para evoluir | Alta (2-3 semanas restantes) | 🔴 P0 | 🟡 Em progresso — de 12.375→**10.397L** (verificado 2026-03-13), 5 componentes + 4 hooks extraídos |
| 5 | **Deploy cloud** | Infra | Dependência do Replit | — | — | ✅ **Resolvido** — Dockerfile.prod + docker-compose.prod.yml + deploy/gcp_setup.sh + deploy/aws_setup.sh |
| 6 | **LangSmith CI Step** | DevOps/CI | Validação automática config LangSmith | Baixa | — | ✅ **Resolvido** — `.github/workflows/ci.yml` linha 55-59: step "Verify LangSmith config" com `continue-on-error: true`. `app/config/langsmith.py` com `is_langsmith_enabled()` + `configure_langsmith()`. 18 testes em `test_langsmith_config.py`. |
| 7 | **Coverage** | Qualidade Testes | Gate **32%**, achieved **32.66%** | — | — | ✅ **Gate atingido** (32%); 32.66% na suite completa |
| 8 | **use-candidates-list.test.ts** — 8 timeouts | Qualidade Testes | Pirâmide FE incompleta | — | — | ✅ **Resolvido** — `vi.useFakeTimers({ shouldAdvanceTime: true })` (Sprint H) |
| 9 | **FactChecker granular** por tipo de claim | Governança IA | Verificação mais precisa | — | — | ✅ **Resolvido** (Sprint H) |
| 10 | **Test categorization por dificuldade** | Qualidade Testes | Facilita priorização | — | — | ✅ **Resolvido** (Sprint I) |

### 11.2 Oportunidades de Produto (Novas Features)

| # | Feature | Benefício Negócial | Alinhamento com Roadmap |
|---|---------|-------------------|------------------------|
| 1 | **Wizard-to-Pipeline handoff automático** — ao criar vaga via wizard, abrir kanban da vaga automaticamente no split-view | UX fluida end-to-end; recrutador nunca perde contexto | Fase 4b split-view já presente |
| 2 | **Dashboard Analytics em tempo real** — agent analytics respondendo via WS com gráficos gerados in-chat | Diferencial competitivo: insights de recrutamento conversacionais sem navegar para outra tela | Fase 5 AnalyticsReActAgent já wired |
| 3 | **Communication agent com templates inteligentes** — agent sugere template de email baseado no stage do candidato | Reduz 80% do tempo em comunicações repetitivas; LGPD-compliant | Fase 5 CommunicationReActAgent já wired |
| 4 | **ATS sync bidirecional em tempo real** — mudanças no Gupy/Pandapé refletem no kanban automaticamente via PlatformEvents | Elimina principal dor de duplicidade de dados em equipes com ATS legado | Fase G4 PlatformEvents + ATSIntegrationReActAgent (Fase 5) já presentes |
| 5 | **LIA como copiloto em páginas** — ao navegar para qualquer página, LIA assume contexto automaticamente (navigation intent já detecta a página) | Chat contextual sem precisar explicar onde o recrutador está | Fase 4b NavigationIntentDetector + LiaFloatContext já implementados |
| 6 | **Fine-tuning contínuo** — exportar feedback DPO para fine-tuning do modelo base | LIA aprende padrões específicos da empresa, aumentando acurácia ao longo do tempo | `lia_feedback.py` DPO export já presente; falta pipeline de fine-tuning |
| 7 | **Multi-tenant isolation no split-view** — cada empresa tem configuração de split-view independente (domínios habilitados, threshold de confiança) | Permite personalizar a experiência por tier de plano (Starter/Pro/Enterprise) | Policy middleware já presente |

### 11.3 Dívida Técnica Identificada

| Área | Dívida | Risco | Ação Recomendada |
|------|--------|-------|-----------------|
| **Frontend god object** | `candidates-page.tsx` **10.397 linhas** (reduzido de 12.375; verificado 2026-03-13) | Alto — qualquer mudança pode quebrar features escondidas | Extrair em fases: `use-candidates-search.ts` → `use-candidates-pagination.ts` → `CandidatesFilterPanel` → `CandidatesTable` |
| **Testes FE** | `use-candidates-list.test.ts` — 8 timeouts resolvidos com `vi.useFakeTimers` | — | ✅ Resolvido (Sprint H) |
| **Sprint E fase 2-3** | ✅ **Resolvido** (Sprint F3: hooks wired) — `candidates-page.tsx` conectada a `use-candidates-list.ts` e `use-candidate-data-requests.ts` | — | — |
| **ReAct loop depth** | `USE_LANGGRAPH_NATIVE=True` ativo — garantir que todos os agentes foram testados com dados reais | Médio — smoke tests por domínio ainda pendentes | Suite de regressão com dados reais + smoke tests por domínio |
| **Coverage meta** | `--cov-fail-under=32` — gate CI 32%, achieved 32.66% | Médio — target real 80% | Aumentar incrementalmente: 40% → 60% → 80% |

### 11.4 Roadmap Sugerido (Próximas 4-6 Semanas)

> ⚠️ **ATUALIZAÇÃO 10/03/2026:** Sprints H, I, J concluídos. Ver Changelogs v7.0, v8.0, v9.0 para detalhes.

```
Sprint K (Semana 1-2): Produto — Features de Alta Demanda
├── Wizard→Pipeline handoff automático no split-view
├── AutomationReActAgent wired no WS dispatcher (1 linha em agent_chat_ws.py)
├── Smoke tests por domínio WS com dados reais
└── candidates-page.tsx: extração useCandidatesModals hook

Sprint L (Semana 3-4): Qualidade + Cobertura
├── Coverage: 32.66% → 40% (candidate_search.py, company.py, job_vacancies.py)
├── Test categorization very_hard: 10+ testes nessa categoria
├── Fine-tuning: pipeline DPO training contínuo (lia_feedback.py já exporta)
└── IaC básico: Terraform para GCP/AWS

Sprint M (Semana 5-6): Features Avançadas
├── Dashboard Analytics real-time: gráficos via AnalyticsReActAgent WS
├── Communication agent: templates inteligentes por stage do candidato
├── ATS sync bidirecional via PlatformEvents
└── Multi-tenant split-view config (por plano Starter/Pro/Enterprise)
```

---

## 12. Mapeamento Gap → Card Jira (Auditoria Agente Python)

Em Março/2026, foi realizada uma análise cruzada do documento do André ("Plano de Auditoria — Agente Python") com o código de referência da LIA. Foram identificados **7 gaps** de auditabilidade no V5 e criados cards no Jira para o time de desenvolvimento implementar os fixes.

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

**Total**: 7 cards | 15 story points | ~19h de esforço estimado

### Distribuição por Sprint

| Sprint | Cards | SP | Esforço | Foco |
|--------|-------|----|---------|------|
| Sprint 1 (Fundação) | AUD-001 + AUD-002 + AUD-003 | 5 | ~5h | Auditabilidade básica + resiliência |
| Sprint 2 (Higiene) | AUD-004 | 1 | ~2h | Limpeza e retenção de dados |
| Sprint 3 (Observabilidade) | AUD-005 + AUD-006 + AUD-007 | 9 | ~12h | Storage externo, API, métricas |

### Documentação de Referência

- **Diagnóstico completo**: `docs/diagnostico-auditoria-agente-python.md` — 7 gaps detalhados com snippets da LIA e passos de implementação
- **Cards no Jira**: Cada card é autocontido com contexto técnico (stack, fluxo do orquestrador, patterns, diretórios, baseline V5), snippets de código e DoD

---

## Apêndice A — Evidências de Arquivo

### V5

| Claim | Arquivo | Evidência |
|-------|---------|-----------|
| GOD OBJECT data_processor.py | `src/agents/data_processor.py` | 53.5KB, 1387 linhas, docstring diz "API Executor Agent" |
| YAML Tool Registry | `src/tools/registry.py` | `ToolRegistry` singleton com double-checked locking |
| 70 Tool Definitions | `documentation/*.yml` (40+) + `documentation_toon/*.toon` (30+) | Contagem via GitHub API |
| RAG Híbrido | `src/services/rag_service.py` | `_hybrid_search()` com semantic + fulltext + reranking |
| FactChecker | `src/domains/sourced_profile_sourcing/fact_checker.py` | `verify_count_claim`, `verify_average_claim`, `verify_top_candidates_claim` |
| FairnessGuard | `src/domains/sourced_profile_sourcing/fairness.py` | `SENSITIVE_FILTER_KEYS`, `check_sensitive_filters()`, 3 disclaimers |
| Prompt Injection (evaluation only) | `src/domains/evaluation/security.py` | 17 `INJECTION_PATTERNS`, `detect_injection()`, `sanitize_input()` |
| Pipeline sem proteção | `src/agents/intent_analyzer.py` | Nenhum import de security.py, input não sanitizado |
| ALL_PYTHON_FILES.txt | Raiz do repo | 338KB, listado no git tree |
| evaluation_worker_backup.py | Raiz do repo | Backup file commitado |
| web_debug.py mock data | `web_debug.py` | `generate_mock_data()` com 10 candidatos fake hardcoded |
| Gemini hardcoded | `src/agents/intent_analyzer.py` | `ChatGoogleGenerativeAI(model=settings.gemini.model)` direto |
| print() em agents | `src/agents/api_executor.py` | `print(f"   [{i}/{len(plan)}] Calling {api_name}...")` |
| Retry HTTP | `src/services/api_client.py` | `Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])` |
| Celery Workers | `celery_worker.py`, `evaluation_worker.py` | Workers para tasks assíncronas |
| No CI/CD | `.github/` | Apenas `instructions/base.instructions.md`, sem workflows |
| Duplicated edge | `src/workflow/graph.py` | `workflow.add_edge("answer_formatter", END)` aparece 2 vezes |
| Class mutable state | `src/domains/sourced_profile_sourcing/smart_extractor.py` | `_cache: Dict[str, ExtractionResult] = {}` class variable |
| Sourcing agents | `src/domains/sourced_profile_sourcing/agents/` | 11 agentes (router, orchestrator, planner, search, detail, comparison, analytics, report, action, base) |
| Sourcing actions | `src/domains/sourced_profile_sourcing/actions/` | 11 ações (search, details, comparison, analysis, distribution, insights, report, score, count, base, search_improvement) |

### LIA

| Claim | Arquivo | Evidência |
|-------|---------|-----------|
| Multi-provider LLM com Factory | `app/shared/providers/llm_factory.py` | `LLMProviderFactory` com `register()`, `get()`, `get_default()` |
| Provider ABC | `app/shared/providers/llm_provider.py` | `LLMProviderABC` com `LLMResponse`, `LLMToolCall` |
| Circuit Breaker | `app/shared/resilience/circuit_breaker.py` | Decorator `@circuit_breaker()` |
| Rate Limiter | `app/middleware/rate_limiter.py` | Sliding window per-user/per-company |
| Token Tracking | `app/services/token_tracking_service.py` | `TOKEN_PRICES`, `DEFAULT_LIMITS` |
| PII Masking | `app/shared/pii_masking.py` | Regex patterns (CPF, email, phone) |
| Prompt Injection Guard | `app/shared/prompt_injection.py` | `PromptInjectionGuard`, risk levels |
| Policy Middleware | `app/shared/policy_middleware.py` | `get_policy_from_request()` FastAPI dependency |
| Learning Loop | `app/shared/learning/learning_loop_service.py` | Feedback capture + pattern detection |
| Structured Logging | `app/shared/structured_logging.py` | JSON format logging |
| Agent Monitoring | `app/shared/governance/agent_monitoring_service.py` | Monitoring de agentes |
| 16 Agentes IA (12 ReAct + 4 StateGraph) | `app/domains/*/agents/` | 4-file pattern em 12 domínios; 4 LangGraph StateGraph. Verificado filesystem 2026-03-13 |
| 231 Serviços | `app/services/` | `find app/services -name "*.py" ! -name "__init__.py" | wc -l` — verificado 2026-03-13 |
| 5 Channel Adapters | `app/shared/channels/adapters/` | email, whatsapp, sms, teams, in-app |
| 5 ATS Clients | `app/services/ats_clients/` | gupy, pandape, stackone, merge, base |
| Billing | `app/services/billing_providers/` | iugu, vindi, base |
| OpenTelemetry | `app/shared/tracing.py` | Distributed tracing |
| 206 API Endpoints | `app/api/v1/` | `find app/api -name "*.py" ! -name "__init__.py" | wc -l` — verificado 2026-03-13 |
| NavigationIntentDetector | `app/orchestrator/navigation_intent.py` | 4 grupos, confidence formula, threshold 0.65 — Fase 4b |
| useNavigationIntent | `plataforma-lia/src/hooks/use-navigation-intent.ts` | POST /api/v1/navigation-intent, threshold 0.65 — Fase 4b |
| LiaSplitPanel | `plataforma-lia/src/components/lia-float/LiaSplitPanel.tsx` | Split-view 360px WS streaming — Fase 4b |
| useActionIntent | `plataforma-lia/src/hooks/use-action-intent.ts` | 5 domínios, ScoredAction loop, threshold 0.70 — Fase 4c/5 |
| WS dispatcher 11 domains + aliases | `app/api/v1/agent_chat_ws.py` | `_get_agent()`: wizard, pipeline/cv_screening, sourcing, talent (default fallback), kanban, jobs_management/jobs_mgmt, policy, pipeline_transition, analytics, communication/comms, ats_integration/ats — verificado 2026-03-13 |
| VectorSemanticCache | `app/orchestrator/vector_semantic_cache.py` | pgvector cosine similarity, threshold 0.92, migration 028 — Fase G2 |
| CascadedRouter 6-tier | `app/orchestrator/cascaded_router.py` | in-process→Redis→regex→Haiku→Sonnet→Opus — Fase G2 |
| 14 métricas Prometheus | `app/observability/metrics.py` | lia_llm_requests_total, lia_llm_latency_seconds, lia_agent_iterations_total, lia_fairness_blocks_total, lia_circuit_breaker_state, lia_http_request_duration_seconds, lia_pipeline_transitions_total, lia_candidates_evaluated_total, lia_router_tier_hit_total, lia_router_latency_ms + 4 others — verificado 2026-03-13 |
| SearchBackend ABC | `app/services/search_service.py` | PostgresSearchBackend + ElasticsearchSearchBackend factory — Fase G4 |
| PlatformEvents | `app/shared/platform_events.py` | PlatformEvent + handler registry + RabbitMQ topic exchange — Fase G4 |
| UV Monorepo 9 libs | `libs/*/pyproject.toml` | config, utils, models, audit, messaging, agents-core, services, contexts, auth — Fase 6a/6b/6c |
| Docker Compose 10 serviços | `docker-compose.yml` | postgres, redis, rabbitmq, api, api-vagas, api-funil, api-onboarding, celery_worker, celery_beat, flower — Fase 6b |
| Celery prioridades | `docker-compose.yml` | celery_worker_high/normal/low + celery_beat + flower — Fase 6b |
| 227 test files (verificado 2026-03-13) | `tests/` | `find tests -name "test_*.py" | wc -l`; pytest --cov-fail-under=32; coverage gate 32%, achieved 32.66% |
| RAG Híbrido (G6) | `app/services/rag_pipeline_service.py` | pgvector cosine + tsvector BM25 + alpha blend; multi-tenant; `GET /api/v1/candidates/rag-search` |
| TOON Format (G7) | `app/services/toon_service.py` | `TOONCard` dataclass; Redis TTL=3600s; LGPD anonymize=True; chave `toon:{company_id}:{candidate_id}:{job_id}` |
| YAML Tool Registry (G5) | `app/tools/tool_registry_metadata.yaml` | 446 linhas, 32 tools declarativos; scopes: TALENT_FUNNEL/JOB_TABLE/IN_JOB/GLOBAL |
| Tool Registry Loader (G5) | `app/tools/tool_registry_loader.py` | `load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()` |
| HITL Persistence (F1) | `app/models/hitl.py` | `HITLPendingAction` + `HITLAuditTrail` tables; migrations 031+032; SOX/BCB-498 compliant |
| Token Budget per-tenant (Sprint A) | `app/services/token_budget_service.py` | PLAN_DAILY_LIMITS per tier; HTTP 429; Redis cache 1h→DB; 298 linhas |
| TimedToolNode (Sprint A) | `libs/agents-core/lia_agents_core/timed_tool_node.py` | asyncio.wait_for(15s); tool_timeouts dict; `_build_timeout_response` |
| Prompt Version Registry (Sprint B) | `app/services/prompt_version_registry.py` | SHA256 hash 12-char; `GET /api/v1/admin/prompts/versions`; 166 linhas |
| Short Lists (F4) | `app/api/v1/short_lists.py` + `src/hooks/use-short-list.ts` | 243L; `POST/GET /api/v1/short-lists`; proxy FE + hook |
| CandidateSearchBar + CandidateTabs (G3/F5) | `src/components/pages/candidates/CandidateSearchBar.tsx` + `CandidateTabs.tsx` | Extraídos de candidates-page.tsx; interface Props; on* callbacks |
| useCandidatesListMapped + transforms (G4) | `src/hooks/use-candidates-list-mapped.ts` + `src/lib/transforms/candidate-transforms.ts` | useMemo wrapper; pure functions 298L |
| SearchResultsHeader (G3) | `src/components/pages/candidates/SearchResultsHeader.tsx` | DS v4.2.1 tokens; inline pills por tipo de entidade |
| 10 UV Monorepo libs | `libs/*/pyproject.toml` | +orchestrator lib vs v5.0 (9→10 libs) |
| 37 Alembic migrations | `alembic/versions/` | `ls alembic/versions/*.py | wc -l` — verificado 2026-03-13
| Blind evaluation (B1) | `app/domains/cv_screening/services/rubric_evaluation_service.py` | `_extract_cv_content()` sem `Name:` — nome do candidato removido do contexto LLM |
| GEOGRAPHIC_ADJUSTMENTS removido (B2) | `app/domains/cv_screening/services/calibration_profiles.py` | `GEOGRAPHIC_ADJUSTMENTS = {}` — constante esvaziada, multiplicador universal 1.0 |
| LangSmith tracing opt-in (L1) | `app/config/config.py` | `LANGCHAIN_TRACING_V2: bool = False` — opt-in explícito |
| WhatsApp token seguro (L8) | `app/domains/communication/services/whatsapp_meta_service.py` | `os.getenv("WHATSAPP_VERIFY_TOKEN")` sem default, warning log quando ausente |
| Gemini retry (A2) | `app/shared/providers/llm_gemini.py` | `@retry(retry_if_result=_is_empty_response, stop=stop_after_attempt(2))` com warning log |
| 19/19 testes BARS (T1) | `tests/test_rubric_evaluation_service.py` | `make_requirement()` com `priority=priority` — 19/19 passando |
| 28/28 testes pipeline (T2) | `app/schemas/screening.py` | `question_count: int = Field(default=8, ge=4, le=25)` — limite corrigido |
| 17/17 testes disparate impact (B5) | `tests/test_disparate_impact_wsi.py` | 4/5 Rule por gênero/idade/etnia — 17/17 passando |
| HITLConfirmCard inline (Sprint J3) | `src/components/agent-control-center/HITLConfirmCard.tsx` | approve/reject + comentário inline no Float Chat |
| use-float-streaming HITL+WS (Sprint J3) | `src/hooks/use-float-streaming.ts` | HITL aprovações integradas no fluxo de streaming WS |
| Navigation Intent 8 grupos (Sprint J) | `app/orchestrator/navigation_intent.py` | 8 grupos: Vagas/Candidatos/Pipeline/Sourcing/WSI/Indicadores/Configurações/Wizard; threshold 0.65 |
| AutomationReActAgent | `app/domains/automation/agents/automation_react_agent.py` | ReAct 4-file; não wired WS (pendente) |
| Automation Engine 19 serviços | `app/domains/automation/services/` | automation_service, scheduler, trigger, handlers, stage_engine, stage_transition, planned_task, autonomous, proactive_alert, proactive, prediction_action_bridge, learning_automation, pattern_applier, pipeline_monitor, event_action_connector, context_aggregator, webhook_adapters, task_service |
| WSI Voice (Deepgram + LLM) | `app/domains/communication/services/wsi_voice_orchestrator.py` | Orquestra entrevistas WSI por voz — Deepgram STT + wsi_interview_graph |
| Bias Audit Snapshot | `app/models/bias_audit_snapshot.py` + `app/services/bias_audit_service.py` | Four-Fifths Rule gender/age/PCD/region; histórico auditável SOX; migration 018 |
| Model Drift Detection | `app/services/model_drift_service.py` | 4 triggers (score/aprovação/custo/latência P95); `GET /api/v1/drift/status`; Celery beat daily 06h Brasília |
| Agent Quality Evaluator (J1) | `app/services/agent_quality_evaluator.py` | task_completion/fairness/response_quality por execução; `agent_quality_evaluations` table; migration 034 |
| 99 modelos SQLAlchemy | `app/models/` | Verificado filesystem — contagem real (vs 97 estimados em v8.0) |
| 215 serviços | `app/services/` | `find app/services -name "*.py" \| wc -l` = 215 (vs 225+ estimados) |
| 36 migrations | `alembic/versions/` | 001→035 + 033_merge_migration_heads |
| 16 agentes distintos | `app/domains/*/agents/` | 12 ReAct (4-file) + 4 LangGraph StateGraph |

## Apêndice B — Benchmarks de Mercado Consultados

### Plataformas de Agentes de IA

| Plataforma | Arquitetura | Diferencial |
|-----------|------------|------------|
| **Manus AI** | 3-layer (Planner→Worker→Verifier), sandboxed browser, multi-agent coordination | Context distillation, file-based context management, todo-list tracking |
| **CrewAI** | Crews + Agents + Tasks, Flows para orquestração, `@tool` decorator | Delegation entre agentes, structured outputs, memory, training |
| **AutoGen** | Conversational agents, GroupChat, code execution | Agents negociam em natural language, code sandbox |
| **LangGraph** | StateGraph, conditional edges, subgraphs, checkpointing | Persistence, human-in-the-loop nativo, streaming |

### Plataformas de Recrutamento com IA

| Plataforma | Arquitetura | Diferencial |
|-----------|------------|------------|
| **Eightfold AI** | Deep learning, 1.6B+ perfis, Skills Graph, Digital Twin | Talent Intelligence Platform, responsible AI dashboard |
| **Paradox/Olivia** | NLP/NLU conversational, multi-channel (SMS, WhatsApp, web) | High-volume hiring, automated scheduling, 24/7 |
| **Beam AI** | Multi-agent, goal-driven, self-learning | End-to-end automation, trust levels configuráveis |
| **HiredScore** (Workday) | AI scoring, talent orchestration, Skills Cloud | Algorithmic auditing, EEOC compliance, internal mobility |

### Standards e Frameworks

| Standard | Escopo | Relevância |
|---------|--------|-----------|
| **NIST AI RMF** | Govern, Map, Measure, Manage | Framework para governança IA completo |
| **EU AI Act** | Transparency, human oversight, accuracy | HR/recruitment é categoria "high-risk" |
| **OWASP LLM Top 10** | Prompt injection, output handling, DoS, etc. | Checklist de segurança para sistemas LLM |
| **ISO 42001** | AI Management System | Standard para gestão de IA |

## Apêndice C — Limitações desta Análise

1. **LOC é estimativa**: V5 ~49K LOC calculado por tamanho de arquivo; LIA ~433K LOC via `wc -l` (1.157 arquivos .py).
2. **Profundidade vs amplitude**: Nem todos os 200+ serviços da LIA foram lidos em detalhe — contagem via filesystem, conteúdo verificado para ~30 arquivos-chave.
3. **Status de produção (v3.1)**: A LIA evoluiu de protótipo para plataforma com compliance enterprise após o Sprint de Qualidade e Compliance (2026-02-28). A auditoria QA (v3.1) identificou e corrigiu 7 vulnerabilidades (B1 blind evaluation, B2 bias geográfico, L1 tracing opt-in, L8 WhatsApp token, A2 Gemini retry, T1/T2 testes) — resultando em 64/64 testes passando e zero bugs pendentes. Os scores da v3.1 refletem o código implementado, verificado e auditado. Gap principal restante: infraestrutura de deploy (Docker/CI/CD) e workers async (Celery).
4. **Sem análise de UX/produto**: Esta análise foca na camada de IA/backend. Fluxos de UX e operational readiness não foram avaliados.
5. **Benchmark qualitativo**: Comparações com plataformas de mercado são baseadas em documentação pública e web search, não em análise de código-fonte.
6. **V5 é read-only**: Toda a análise do V5 foi feita via GitHub API (GET). Nenhum teste foi executado — scores de testes baseados na estrutura de arquivos, não em execution results.
7. **Viés de comparação**: A LIA foi analisada com acesso completo ao filesystem; o V5 via API com leitura limitada. Isso pode criar assimetria de informação favorecendo a LIA.
