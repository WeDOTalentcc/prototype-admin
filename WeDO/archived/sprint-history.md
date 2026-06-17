# LIA Platform — Histórico de Sprints

> Arquivo de referência. Para o estado atual e convenções ativas, ver `CLAUDE.md`.
> Última atualização: 25/03/2026

---

## Estado Final (20/03/2026)

Sprints A–F + G1–G7 + SEG-1–SEG-5 + SEG-GAPS + AUD-1–AUD-5 + Y1 + Y2 + Y3 + Y4 + Y5 + FAR concluídos.
Coverage: **30.99%+** (gate: 30%). **4680+ testes passando.**

---

## Sprint FAR — Fairness Audit Remediation (20/03/2026)

- **FAR-1 — Expansão FairnessGuard**: 4 novas categorias bloqueadoras (`antecedentes_criminais`, `saude_doenca`, `filiacao_sindical`, `aparencia_fisica`). 18+ novos termos em `IMPLICIT_BIAS_TERMS`. Fix regex idade (falso positivo "X anos no mercado"). `_PATTERNS_VERSION = 3`. `log_check()` reescrito (aceita `db=None`, context dict ou str). 44 testes em `test_far1_new_categories.py`.
- **FAR-2 — Proteção de Entry Points**: FairnessGuard em `RAGPipelineService.search()`, `PearchService.search_candidates()`, `CommunicationReActAgent.process()`, `jd_import.py`. 13 testes em `test_far2_entry_points.py`.
- **FAR-3 — Soft Warnings ao Recrutador**: `_fg_result.soft_warnings` → `output.metadata["fairness_warnings"]` em Sourcing e Pipeline. WS payload inclui `fairness_warnings`. 7 testes em `test_far3_soft_warnings.py`.
- **FAR-4 — Layer 3 LLM Ativado**: `HIGH_IMPACT_ACTIONS` com `sourcing_search` e `jd_import`. `check_with_layer3()` respeita `FAIRNESS_LAYER3_ENABLED` (opt-in). 8 testes em `test_far4_layer3.py`.
- **FAR-5 — Auditoria de Disparate Impact**: `BiasAuditService.audit_ranking_results()` Four-Fifths Rule EEOC 80%. Campo `soft_warnings JSONB nullable` em `fairness_audit`. Migration 048. 8 testes em `test_far5_output_audit.py`.
- **FAR-AUDIT**: 2 gaps pós-auditoria: `query[:60]` removido (apenas `query_len` logado); `FAIRNESS_LAYER3_ENABLED` honrada em `check_with_layer3()`.

---

## Sprint Y5 — Arquitetura Avançada (15/03/2026)

- **Y5/C5 — Runbook Operacional**: `docs/RUNBOOK_DEGRADATION.md` expandido (6 seções). `docs/RUNBOOK_INCIDENT_PLAYBOOKS.md` criado (5 playbooks). 54 testes em `test_c5_runbook_links.py`.
- **Y5/E4 — YAML Hot-Reload de Agentes**: `app/agents_registry.yaml` (7 agentes). `AgentRegistryWatcher` com `check_and_reload()`. `reload_from_yaml()` em `react_agent_registry.py`. `POST /api/v1/admin/agents/reload`. 8 testes em `test_e4_agent_hot_reload.py`.
- **Y5/E6 — RAG por Domínio**: Migration 045 (`domain` column). `DOMAIN_ALIASES` + `normalize_domain()` + filtro por domain em `rag_pipeline_service.py`. `DomainEmbeddingService`. Celery task `rag.rebuild_domain_index`. 10 testes em `test_e6_rag_domain.py`.
- **Y5/E9 — Auto-Routing Adaptativo**: `RoutingFeedback` model + migration 046. `routing_learning_service.py` com `record_correction()` + `compute_domain_confidence_adjustments()`. Wired em `cascaded_router.py`. Redis cache TTL=24h. `app/core/redis_client.py` criado. 12 testes em `test_e9_adaptive_routing.py`.
- **Y5/E10 — Agent-to-Agent Communication**: `AgentBus` singleton (Redis Pub/Sub). `emit()` em `enhanced_agent_mixin.py`. Wiring: Sourcing→Pipeline (`candidate_imported`), Wizard→JobsManagement (`job_creation_ready`). 12 testes em `test_e10_agent_bus.py`.
- **Y5/E12 — Event Sourcing Imutável**: `DomainEvent` model + migration 047. `EventStoreService.append()` + `get_history()` + `reconstruct_state()`. `GET /api/v1/candidates/{id}/event-history`. Dual write em `pipeline_transition_agent.py` e `job_wizard_graph.py`. 12 testes em `test_e12_event_sourcing.py`.

---

## Sprint Y4 — Capacidades Novas (15/03/2026)

- **Y4/D7 — Benchmark Salarial Real**: `SalaryBenchmarkService` (Redis TTL=7d → Apify → fallback setorial). `GET /api/v1/salary-benchmark`. `apify_service.scrape_salary_data()`. 7 testes em `test_d7_salary_benchmark.py`.
- **Y4/E11 — Priority Queue por Urgência**: `PriorityCalculator.compute()` escala 1-5 (sourcing deadline<7d→1, cv_screening backlog>50→2, followup→3, padrão→5). 11 testes em `test_e11_priority_queue.py`.
- **Y4/E5 — Multi-Model por Agente**: `AGENT_MODEL_CONFIG` (12 agentes). `build_agent_model_config()` lê envvars `AGENT_MODEL_{NAME_UPPER}`. `@property model_id` em `enhanced_agent_mixin.py`. 9 testes em `test_e5_multi_model.py`.
- **Y4/E7 — Streaming Pensamentos ReAct**: `ReactThinkingStream` componente. `thinkingSteps/isThinking` em `use-float-streaming.ts`. WS handler em `agent_chat_ws.py`. 5 testes BE em `test_e7_react_streaming.py`.
- **Y4/E3 — WSI Assíncrono**: 4 endpoints em `wsi_async.py` (invite/load/answer/complete). `useWSIAsync(token)` hook. Proxy FE. 6 testes BE em `test_e3_wsi_async.py`.
- **Y4/E2 — Fit Cultural Integrado**: `CulturalFitIntegrationService.compute_integrated_fit()` combina WSI (0.4) + entrevistadores (0.4) + cultura empresa (0.2). `GET /api/v1/candidates/{id}/cultural-fit`. 9 testes em `test_e2_cultural_fit.py`.
- **Y3 Gaps Fechados**: migration 043 `candidate_consent_grants`; `ats_pii_filter.py` wiring `check_consent("ats_sharing")`; `RecruiterDecisionFeedback` model + migration 044; wiring em `pipeline_transition_agent.py` (hired/rejected); `_get_calibration_adjustment_async()` usa `ml_feedback_service`; checkbox multi-select Kanban; `ScoreBreakdownBadgeLazy` em `candidates-page.tsx`.

---

## Sprint Y3 — Fairness, Calibração e Produto (15/03/2026)

- **Y3/D3 — Bias Audit Disparate Impact (EEOC)**: `_chi_square_test()` (scipy + fallback Python puro). `DemographicAuditResult.disparate_impact + eeoc_compliant`. Migration 042. 7 testes em `test_d3_disparate_impact.py`.
- **Y3/D2 — Confidence Calibration (12 agentes)**: `confidence_score` em `ReActState`. `_record_confidence(state)` em `enhanced_agent_mixin.py`. 4 agentes wired explicitamente. 9 testes em `test_d2_confidence_calibration.py`.
- **Y3/D5 — Granular Consent LGPD**: `GranularConsentService` (7 tipos). `GET/POST /api/v1/consent/granular/{candidate_id}`. 11 testes em `test_d5_granular_consent.py`.
- **Y3/E1 — Score Clicável Kanban**: `GET /api/v1/rubrics/{job_id}/candidates/{candidate_id}/breakdown`. `ScoreBreakdownBadgeLazy` com Popover lazy-load. 4 testes BE em `test_e1_score_breakdown.py`.
- **Y3/D9 — Análise Comparativa Visual**: `POST /api/v1/candidates/compare`. `candidate-compare-modal.tsx` (winner banner, scores por dimensão). Wired em `job-kanban-page.tsx`. 6 testes em `test_d9_candidate_compare.py`.
- **Y3/D6 — ML Adaptativo (Feedback Loop)**: `MLFeedbackService.record_signal()` + `compute_job_weights()` (pesos [0.7, 1.3]). `POST /api/v1/ml-feedback/signal`. Celery task `ml.feedback.process_weights`. 10 testes em `test_d6_ml_feedback.py`.

---

## Sprint Y2 — Quick Wins + Infra (15/03/2026)

- **Y2/E8 — Validação de escopo de tools**: `active_scope` em `ReActConfig`. `is_tool_allowed_in_scope()` antes de `_act()`. `_validate_tool_scope()` em `enhanced_agent_mixin.py`. 9 testes em `test_e8_scope_validation.py`.
- **Y2/D10 — Fallback Pearch AI → Busca Interna**: `_pearch_search_fallback()` tenta `RAGPipelineService.search()` quando circuit aberto. `status="internal_fallback"`. 5 testes em `test_d10_pearch_fallback.py`.
- **Y2/D8 — Insights Proativos no Kanban**: `GET /api/v1/proactive-actions/insights`. `useProactiveInsights()` auto-refresh 5min. Painel dismissível no kanban. 5 testes BE em `test_d8_proactive_insights.py`.
- **Y2/D1 — JobReportModal: wire backend real**: `GET /api/v1/jobs/{job_id}/report` (funnel_metrics, channel_performance, top_candidates). `useJobReport()` hook. 5 testes BE em `test_d1_job_report_endpoint.py`.
- **Y2/C4 — Métricas Prometheus por agente**: `agent_latency_timer` em `_process_langgraph()`. `record_tokens()` após tool execution. `GET /api/v1/metrics` → `generate_latest()`. 8 testes em `test_c4_agent_metrics.py`.

---

## Sprint Y1 — Compliance Crítico (15/03/2026)

- **Y1/D4 — PII masking em logs**: `install_global_pii_masking()` cobre handlers do root logger + `exc_info`. Filtro no `StreamHandler` em `configure_logging()`. 12 testes em `test_d4_pii_log_masking.py`.
- **Y1/C2 — Audit trail interview_graph**: 3 pontos `audit_service.log_decision()` em `interview_graph.py` (pending_review, validation_failed, error). ACH-006 fechado: 14/14 agentes com audit trail (100%). 4 testes em `test_c2_interview_audit.py`.
- **Y1/C1 — LGPD em ATS: campos sensíveis dinâmicos**: `lgpd_field_registry.py` (OUTBOUND_SENSITIVE_FIELDS, INBOUND_TEXT_FIELDS). `ats_pii_filter.py` (filter_outbound + filter_inbound_text). Wired em gupy.py + pandape.py. ACH-030 fechado. 14 testes em `test_c1_ats_lgpd_fields.py`.
- **Y1/C3 — Interview Scheduling Agent: FairnessGuard + Confidence Score**: `_compute_confidence_score()`. FairnessGuard em `interview_details_collector`. `record_confidence()` em ambos os paths. 11 testes em `test_c3_interview_scheduling_agent.py`.

---

## Sprints AUD-1–AUD-5 — Auditoria de Profundidade (12/03/2026)

- **AUD-1 (ACH-001)**: `ANTI_SYCOPHANCY_OPERATIONAL` injetado nos 6 prompts faltantes (analytics, communication, automation, ats_integration, sourcing, pipeline).
- **AUD-2 (ACH-004/010/011/014)**: Circuit breakers — `OPENAI_CIRCUIT`, `GEMINI_CIRCUIT`, `GUPY_CIRCUIT`, `PANDAPE_CIRCUIT`, `STACKONE_CIRCUIT`, `SENDGRID_CIRCUIT`, `RESEND_CIRCUIT`, `WORKOS_CIRCUIT`. Aplicados em todos os providers de ATS e email.
- **AUD-3 (ACH-006)**: `audit_service.log_decision()` em `PolicySetupAgent._process_answer()`.
- **AUD-4 (ACH-005)**: HITL em `SourcingReActAgent.process()` (stage="outreach"). HITL em `CommunicationReActAgent` (`_HITL_MESSAGE_TYPES`). 17 testes em `test_aud4_hitl_and_domain_circuits.py`.
- **AUD-5 (ACH-025/023/018)**: `bandit` scan no CI. Job `load-tests` não-bloqueante. `mockUsers` e `MOCK_BILLING_DATA` removidos (substituídos por estado de erro real).
- 36 testes em `test_aud_audit_fixes.py`.

---

## Sprints SEG-1–SEG-5 — Segurança e Governança (11/03/2026)

- **SEG-1 — PromptInjectionGuard**: Singleton em `agent_chat_ws.py` (high=block, medium=log). Check em `wsi_interview_graph.validate_response()` (injeção alta = score 0). 6 testes em `test_injection_guard_integration.py`.
- **SEG-2 — FairnessGuard nos agentes ReAct**: `sourcing_react_agent.py` e `pipeline_transition_agent.py` — check no início de `process()`, fail-safe. 5 testes em `test_fairness_guard_agents.py`.
- **SEG-3A — PII Masking Celery**: `@signals.worker_process_init.connect` → `install_global_pii_masking()` em cada processo filho. 2 testes em `test_pii_masking_celery.py`.
- **SEG-3B — Data minimization em prompts LLM**: `strip_pii_for_llm_prompt()` Layer 1+3 basic. Wired em `rubric_evaluation_service.py`. Flag `LLM_PROMPT_PII_STRIPPING_ENABLED`. 7 testes em `test_pii_llm_prompt_stripping.py`.
- **SEG-4 — ConsentCheckerService Gate 1 WSI**: `load_context()` verifica `ai_screening` consent. revoked → `LGPD_CONSENT_REVOKED`. Fail-safe. 4 testes em `test_wsi_consent_gate.py`.
- **SEG-5 — AuditService nos gates**: `pipeline_transition_agent.py` (2 pontos: pre-HITL + completed). `sourcing_react_agent.py` (final de `_process_react_loop()`). 5 testes em `test_audit_trail_gates.py`.
- **SEG-GAPS**: LangGraph audit path em sourcing+pipeline; `strip_pii_for_llm_prompt()` em analysis_service, voice_screening_analysis, candidate_comparison_service; HITL rejected audit em `agent_chat_ws.py`. 10 testes em `test_audit_trail_gates.py`.

---

## Sprints G1–G7 (08/03/2026)

- **G1 — HITL Multi-tenant Fix**: `domain` + `company_id` em `request_approval()` nos 3 agentes HITL.
- **G2 — Coverage Gate 29%**: 7 novos arquivos de teste. pytest.ini `--cov-fail-under=25`.
- **G3 — SearchResultsHeader**: Extraído de candidates-page.tsx (202L → 9L). `src/components/pages/candidates/SearchResultsHeader.tsx`.
- **G4 — useCandidatesListMapped**: `mapCandidateLocalToCandidate()` em `candidate-transforms.ts`. Hook `use-candidates-list-mapped.ts` com `useMemo`.
- **G5 — YAML Tool Registry**: `tool_registry_metadata.yaml` (32 tools). `tool_registry_loader.py`. `.export_to_yaml()` + `.validate_yaml()` em `registry.py`. Scopes: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL.
- **G6 — RAG Híbrido**: `RAGPipelineService.search()` BM25+pgvector alpha blend. `GET /api/v1/candidates/rag-search`. 31 testes em `test_rag_pipeline.py`.
- **G7 — TOON Format**: `TOONService.get_or_generate()` Redis TTL=3600s. LGPD anonymize. `GET /api/v1/candidates/{id}/toon`. Proxy FE. 34 testes em `test_toon_service.py`.

---

## Sprints F1–F6 (08–12/03/2026)

- **F1 — HITL Persistence**: Já existia (032_add_hitl_tables.py). Nada implementado.
- **F2 — Coverage Gate Unification**: `--cov-fail-under=12` → `25` no pytest.ini.
- **F3 — FE Hooks Wiring**: `useCandidatesListMapped` wired como `candidatesListHook`. Manual useEffect (143L) removido. 10 testes em `use-candidates-list.test.ts`.
- **F4 — Short List Endpoint**: `short_lists.py`, `short_list_service.py`, `short_list.py` model, migration 032. Endpoints POST/GET + POST/DELETE candidates. Hook `use-short-list.ts`.
- **F5 — Sprint E Phase 3**: Já existia (`CandidateSearchBar`, `CandidateTabs`, `SearchResultsHeader`). Nada implementado.
- **F6 — LangSmith CI Step**: Step `Verify LangSmith config` no ci.yml (non-blocking). `test_langsmith_config.py` (18 testes).

---

## Sprints P3 + Features Diversas (12/03/2026)

- **P3-1 Briefing Diário**: Celery task `briefing.send_daily`. Beat `briefing-daily` 09h UTC. `useDailyBriefing()` hook. `daily-briefing-card.tsx`. Wired em `dashboards-page.tsx`.
- **P3-2 JD Import via Upload**: `POST /import/upload-file` (.txt/.md/.pdf/.docx, 5MB). `strip_pii_for_llm_prompt()` antes de importar. Wired em `jobs-page.tsx` (paperclip).
- **P3-3 Policy Templates por Setor**: UI em `admin/configuracoes/politicas/page.tsx`. Select (6 setores) + botão "Aplicar Template".
- **P3-4 ML Preditiva FE**: `useMLPredictions()` (fetchInsights, fetchTimeToFill, fetchSalary). Proxies em `/api/backend-proxy/ml/`.
- **Short List UI Wiring**: `useShortList` no `job-kanban-page.tsx`. Auto-create. DropdownMenuItem "Adicionar à Short List". 6 testes em `use-short-list.test.ts`.
- **MLInsightsCard**: Card expansível (time-to-fill, salary range, market percentile). Lazy-fetch. Wired no kanban. 7 testes em `ml-insights-card.test.tsx`.
- **Follow-up Automático WSI**: `followup_service.py`. MAX_FOLLOWUPS=7. LGPD opt-out check. Celery task `followup.process_pending` + beat hourly. 9 testes em `test_followup_service.py`.
- **WSI Triagem Abandonada**: `wsi_abandoned_service.py`. FIRST_REMINDER=48h, SECOND=96h (+ Bell+Teams ao recruiter). `reminder_count` via `jsonb_set()`. Beat `wsi-abandoned-check` (*/4h). 8 testes em `test_wsi_abandoned_service.py`.
- **Diagnóstico #7 fixes**: UUID parse safety, double-submit guard, warning log em `_resolve_guardrails()`, per-circuit try/except em `reset_all`. 7 testes em `test_diagnostico7_fixes.py`.

---

## Gaps Compliance (Gap 16.x — 11/03/2026)

- **PolicyEngine Alpha 1**: `policy_engine_service.py`. `save_policy_block()` defaults setoriais (6 setores). `POST /api/v1/policy-engine/apply-sector/{company_id}`. 22 testes.
- **Data Retention LGPD Celery fix**: `import run_cleanup` direto. `GET /admin/lgpd/cleanup-status` + `GET /admin/lgpd/retention-policy`. Beat `lgpd-cleanup-daily` 05h UTC.
- **DSR Notifications**: `_notify_subject()` fail-safe, `_REQUEST_TYPE_LABELS` (PT-BR), `calculate_sla_deadline()`. Wired em create/complete/reject DSR. 16 testes.
- **Email Tracking**: `inject_pixel_and_links()` em `email_tracking_service.py`. `_send_to_email()` injeta pixel automaticamente, fail-safe. 13 testes.
- **Gate-differentiated feedback**: `send_gate_feedback(gate_level)` com 4 gates. PII masking nos logs. Wired em `wsi_interview_graph.generate_feedback()`. 13 testes.
- **Web inscription Gate 1 alignment**: `stage="pending_gate1"` + `screening_invite_token`. Verificação de saturação em `applications.py`. `send_gate_feedback("screening_invited")` canônico. SAT-007 Jira. 3 bugs corrigidos pós-review.
- **Circuit Breakers admin**: `GET /api/v1/admin/circuit-breakers`, `POST reset/{name}`, `POST reset-all`. 7 testes.

---

## Compliance Detalhado — Sistemas Implementados

### Float Chat Nível 3 (Sprint J — 09/03/2026)
`LiaChatPanel` migrado REST→WebSocket. `use-float-streaming.ts` — HITL + streaming. `HITLConfirmCard.tsx`. `navigation_intent.py` — 4 grupos: Configurações, Indicadores, WSI. Wizard detectado redireciona para `openSplitView("Vagas")`. 9 testes Vitest.

### Sistemas de Compliance Arquiteturais
- **LGPD**: `data_request.py`, `consent_management.py`, portal de titular
- **SOC 2 / ISO 27001**: `compliance_controls.py`, `audit_logs.py`, `trust_center.py`
- **FairnessGuard**: 3 camadas — Camada 1 (regex 40+ patterns), Camada 2 (léxico implícito), Camada 3 LLM (opt-in `FAIRNESS_LAYER3_ENABLED`)
- **Model Drift Detection**: `model_drift_service.py` — 4 triggers. `GET /api/v1/drift/status`. Beat `drift-run-batch-daily` 06h Brasília.
- **Drift Alert Service**: `drift_alert_service.py` — Bell+Teams. 1 trigger=WARNING, 2+=URGENT.
- **Bias Audit API**: `bias_audit_service.py` — Four-Fifths Rule 4 dimensões. `GET /api/v1/bias-audit/job/{job_id}`.
- **BiasAuditSnapshot**: `bias_audit_snapshot.py` + migration 018. `save_snapshot()` + `get_snapshot_history()`. Histórico auditável SOX/ISO 27001.
- **Wizard Orchestrator**: `wizard_orchestrator_service.py` — WizardIntent (8 valores), INTENT_TO_TOOL_MAPPING.
- **Anti-sycophancy**: `sector_benchmark_service.py` — benchmark setorial injetado no prompt de `evaluate_candidate()`.
- **RAG Híbrido**: `rag_pipeline_service.py` — BM25 + pgvector alpha blend. FairnessGuard top-10.
- **TOON Format**: `toon_service.py` — TOONCard, Redis TTL 1h, LGPD anonymize.
- **YAML Tool Registry**: `tool_registry_metadata.yaml` — 32 tools, scopes validados.
- **HITL audit multi-tenant**: `request_approval()` com `domain`/`company_id` nos 3 agentes.
