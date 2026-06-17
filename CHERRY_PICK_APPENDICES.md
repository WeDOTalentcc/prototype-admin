# Cherry-pick Map — Apêndices

> Anexos do [CHERRY_PICK_MAP.md](CHERRY_PICK_MAP.md) — mantidos em arquivo separado pelo tamanho.
> Gerado em: 2026-04-29 12:47

## Índice
- [Apêndice A — Commits cross-cutting (alto risco para cherry-pick parcial)](#4-apêndice-a--commits-cross-cutting-lista-de-atenção)
- [Apêndice B — Auto-commits do Replit Agent](#5-apêndice-b--auto-commits-do-replit-agent)
- [Apêndice C — Lista cronológica completa](#6-apêndice-c--lista-cronológica-completa-mais-novo--mais-antigo)
- [Apêndice D — Features menores](#7-apêndice-d--features-menores-1-2-commits-sem-camada-ia)

---

## 4. Apêndice A — Commits cross-cutting (lista de atenção)

Commits que tocam **mais de uma camada** simultaneamente. Cherry-pick parcial **quebra** — ou pega tudo da feature, ou abre o `git show` e separa manualmente.

| Risco | SHA | Data | Camada | Feature | O que faz | Arquivos (top 5) |
|:---:|---|---|---|---|---|---|
| 🔴 | `b4753d320` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | audit configurações fase 3 — task #927 quick wins + bonus T5/T6 da sessão — a11y CRITICAL nos 7 hubs/tabs do menu Configurações: | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`plataforma-lia/src/components/settings/BigFiveRadar.tsx`<br>`plataforma-lia/src/components/settings/DocumentUploadCard.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/IntegrationsHub.tsx` |
| 🔴 | `e0fb295b9` | 2026-04-28 | Cross Back↔Front | Job Management (BE) | Enhance salary suggestions with ATS job history and refine task display — Integrate ATS job history for salary recommendations, add a pipeline template selectio | `lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_salary.py`<br>`plataforma-lia/src/app/api/backend-proxy/v1/tasks/route.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-plan-card.ts` |
| 🔴 | `28c20b355` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | Configurações Fase 2.5: fechamento das pendências do audit 28/abr/2026 — Aplicadas as skills canonical-fix, design-standardize, feature-impact e | `lia-agent-system/app/api/v1/voice_stream.py`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/StudioComplianceView.tsx`<br>`plataforma-lia/src/components/settings/WebhooksManager.tsx`<br>`plataforma-lia/src/components/settings/useGlobalSearchSettings.ts` |
| 🟡 | `7a0d9ab79` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 24 | feat(wizard): Onda 24 — C.3 perguntas explícitas recrutador (seniority + WSI mode + calibração) — C.3.1 stage_description.py: confirma senioridade detectada ao  | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_description.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_publication.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_wsi.py` |
| 🟡 | `bdb0cf8d2` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 23 | feat(wizard): Onda 23 — C.1 WsiQuestionGenerator + C.2 JdEnrichmentService canônicos — C.1 stage_wsi.py: WsiQuestionGenerator (F2+F3+F6 pipeline) com SeniorityR | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_review.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_wsi.py` |
| 🟡 | `64728b8f1` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 18-21 | feat(wizard): Ondas 18-21 — apply_learning nos stages, pick_canonical salary, wizard_step_response metadata — F.1-F.4: feedback_learning_service.apply_learning( | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_basic_info.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_description.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_review.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_salary.py` |
| 🔴 | `d6a8d109c` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | i18n(settings): translate Configurações to English (Task #919) — Translated hardcoded PT strings to use `useTranslations` across 53/75 (70.7%) | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/AIConfigPreview.tsx`<br>`plataforma-lia/src/components/settings/BenefitsTab.tsx`<br>`plataforma-lia/src/components/settings/DataFieldsPanel.tsx`<br>`plataforma-lia/src/components/settings/LiaFieldToggle.tsx` |
| 🟡 | `03cad32de` | 2026-04-28 | Cross IA↔Back | §4 Rail Features — PR-Q3 | feat(capability-map): PR-Q3 — align start_wsi_interview intent + triagem wsi keywords — Canonical-fix: capability_map.yaml used start_wsi_flow but FE SUGGESTION | `lia-agent-system/app/config/capability_map.yaml` |
| 🔴 | `9477be72f` | 2026-04-28 | Cross Back↔Front | Automations | Update recruitment automations with new data fetching and testing — Refactor AutomationsTab component to fetch real automation data from API and add correspondi | `plataforma-lia/src/components/settings/recruitment/automations-tab.tsx` |
| 🟡 | `43802d069` | 2026-04-27 | Cross IA↔Back | §4 Rail Features — PR-J | feat(pr-j): wire capability_map + entity_resolver into WS handler [BE sprint 2] — - rail_a_capability_check.py: Phase 0.5 gate before any agent invocation | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/rail_a_capability_check.py` |
| 🟡 | `8705ece14` | 2026-04-27 | Cross IA↔Back | §4 Rail Features — PR-J | feat(pr-j): add EntityResolverService + CapabilityMapService [BE sprint 1] — - capability_map.yaml: declarative guide (feedforward) for 5 Rail A intents | `lia-agent-system/app/config/capability_map.yaml`<br>`lia-agent-system/app/shared/services/capability_map_service.py`<br>`lia-agent-system/app/shared/services/entity_resolver_service.py` |
| 🔴 | `ec6ef7bb7` | 2026-04-27 | Cross Back↔Front | §4 Rail Features — Rail A | feat(pr-m): add active-jobs pulse badge to Vaga node in Rail A — - PipelinePulseResponse: add active_jobs field (default=0, backward-compat) | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟡 | `2f09160ff` | 2026-04-27 | Cross IA↔Back | §9 Security / Tenant guards | fix(security): W7.2 PromptInjectionGuard global — bridge + cascaded router — - TeamsOrchestratorBridge.process_message(): defense-in-depth guard before | `lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🔴 | `f277a773c` | 2026-04-27 | Cross IA↔Front | Triagem (módulo) | Task #882: Preview da triagem do candidato pra print — Adiciona quatro rotas de preview sem autenticacao na plataforma-lia, dentro | `lia-agent-system/alembic/versions/099_create_offer_proposals.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/offers.py`<br>`lia-agent-system/app/domains/offer/domain.py`<br>`lia-agent-system/app/domains/offer/models/__init__.py` |
| 🔴 | `939d38a2f` | 2026-04-27 | Cross Back↔Front | §1 Teams Integration | refactor(teams): W8 tech debt batch — 8 P2 itens em 1 commit — 8.1 useTeamsTabTracker: prolongedStayMs agora configurável via TrackerOptions | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_calendar_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`lia-agent-system/app/domains/communication/services/teams_proactivity_engine.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🔴 | `43f953d95` | 2026-04-27 | Cross Back↔Front | §1 Teams Integration | feat(teams): W5.1 Tab Pipeline + Tab Dashboard — resolve 404 no manifest — Implementa as 2 abas Teams que estavam mapeadas no manifest mas retornavam 404: | `lia-agent-system/app/domains/communication/services/teams_tab_trigger.py`<br>`plataforma-lia/src/app/[locale]/teams-tab/dashboard/page.tsx`<br>`plataforma-lia/src/app/[locale]/teams-tab/pipeline/page.tsx` |
| 🔴 | `ece44f52d` | 2026-04-27 | Cross IA↔Front | §4 Rail Features — Rail A | chore(rail-a): remove PR-A from sprint-I (extracted to feat/pr-a-rail-a-metadata) — PR-A foi extraido para uma branch dedicada (feat/pr-a-rail-a-metadata, | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/orchestrator/services/rail_a_hint_override.py` |
| 🟡 | `2818ab064` | 2026-04-27 | Cross IA↔Back | §1 Teams Integration | audit: validação pós-Rev 4 do wizard + fixes cross-tenant Teams — Auditoria final do wizard de criação de vaga (Rev 4) solicitada pelo | `lia-agent-system/app/orchestrator/context_adapter.py` |
| 🔴 | `365bfab8f` | 2026-04-27 | Cross IA↔Front | §1 Teams Integration | audit: validação exaustiva pós-Rev 4 + fix cross-tenant Teams proactivity — Auditoria final solicitada pelo usuário ("rode todas as skills, audita | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatEmptyState.tsx` |
| 🟡 | `34cc893b2` | 2026-04-27 | Cross IA↔Back | Wizard (geral) | audit: validação exaustiva pós-Rev 4 do wizard de criação de vaga — Auditoria final solicitada pelo usuário ("rode todas as skills, audita | `lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🔴 | `5d7c93349` | 2026-04-27 | Cross IA↔Front | Auditoria / Audit Rev | audit Rev 4: fechar F4 PM-02 (token streaming) + PM-03 (protocol handshake) — Resolve os P3 remanescentes da Auditoria Rev 4 do wizard de criação de | `lia-agent-system/app/api/v1/_ws_stream_helpers.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `ea8418688` | 2026-04-26 | Cross IA↔Back | Policy / Job Creation | Wire PolicyGateService + ConfidencePolicyService into JobCreationGraph — Resolves N-09 (PolicyGateService unused in wizard) and M-06 (silent vs. | `lia-agent-system/app/domains/job_creation/policy_gate.py` |
| 🔴 | `bfe3efade` | 2026-04-26 | Cross Back↔Front | JD Import / Job Description | [#858] Harden /jd-import/upload-file (B-02 + A-02 + M-12) — Move JD upload parse out of the FastAPI request loop and into a Celery | `lia-agent-system/app/api/v1/jd_import.py`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts` |
| 🟡 | `b595f6833` | 2026-04-26 | Cross IA↔Back | Wizard (geral) | Wizard OTLP — Fechar Lacuna de Observabilidade (N-07 + N-08) — Task #861. Fecha as duas pendências do gate operacional do ADR-019: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/_observability.py` |
| 🟡 | `7333e418a` | 2026-04-26 | Cross IA↔Back | §2 Orchestrator Migration | feat(orch-migration): extract AnalyticsDispatchService — process_analytics_request canonical — LIA-D06 Orchestrator Migration — extraction follow-up (Sprint IV+ | `lia-agent-system/app/domains/analytics/services/analytics_dispatch.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `00db0ec4b` | 2026-04-26 | Cross IA↔Back | §2 Orchestrator Migration | feat(orch-migration): Sprint IV — extract RubricDispatchService (CV match BARS) — LIA-D06 Orchestrator Migration — Sprint IV (CV screening rubric extraction). | `lia-agent-system/app/domains/cv_screening/services/rubric_dispatch.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `8bb8618ee` | 2026-04-26 | Cross IA↔Back | Wizard (geral) | Task #850: Consolidate canonical job-creation wizard (round 6 — review polish) — Original task: Remove legacy backend (wizard_react_agent, job_wizard_graph, | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/health_langgraph.py`<br>`lia-agent-system/app/api/v1/wizard_smart_orchestrator.py`<br>`lia-agent-system/app/domains/ai/services/graph_runner.py` |
| 🔴 | `5d5635007` | 2026-04-26 | Cross Back↔Front | Compliance / LGPD / EU AI Act | fix(unified-chat): remove dead LgpdConsentDialog to unblock build — Bug: dev-server (Next.js 16 + Turbopack) quebrava com `ENOENT: no such | `plataforma-lia/src/components/unified-chat/LgpdConsentDialog.tsx` |
| 🔴 | `30fd75ff9` | 2026-04-26 | Cross Back↔Front | Privacy / PII (W7) | Task #838 — Privacy & audit hardening on JD upload endpoint — Reforço de privacidade e auditoria no `/import/upload-file`: | `lia-agent-system/app/api/v1/jd_import.py`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/consent-status/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts`<br>`plataforma-lia/src/components/unified-chat/useSmartFileUpload.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/useWizardIntegration.ts` |
| 🔴 | `3a3183c77` | 2026-04-26 | Cross Back↔Front | Wizard (geral) | Task #827 — Inject "Vaga publicada" closing card on wizard handoff — When the "Criar nova vaga" wizard reaches its terminal stage (handoff/done), | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/WizardPublishedJobCard.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-plan-card.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-types.ts` |
| 🟡 | `8adecbc23` | 2026-04-26 | Cross IA↔Back | §13 PARTE D — PreConditionChecker | Task #819: close last 2 demo-tenant config gaps in PreConditionChecker — Original task: Close the 2 remaining `info` hints from the demo tenant — | `lia-agent-system/app/orchestrator/precondition_checker.py`<br>`lia-agent-system/app/shared/services/seed_service.py` |
| 🟡 | `8d3c985d8` | 2026-04-25 | Cross IA↔Back | Configurações (hub) | [task #812] company_settings: cobrir ações primárias (canonical-fix PT-BR) — Defesa em profundidade complementar à Task #811: o agente `company_settings` | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `a1fbb30c6` | 2026-04-25 | Cross IA↔Back | §13 PARTE D — Proatividade | fix(orchestrator): respeitar severity + intent em ProactiveHints (task #811) — ## Original | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `b402230fc` | 2026-04-24 | Cross Back↔Front | Hooks (FE) | Restore missing and broken file imports across the application — Restores 34 missing modules by locating their last known commit in git history and reintroducin | `plataforma-lia/src/app/[locale]/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/app/[locale]/jobs/[id]/JobDetailClient.tsx`<br>`plataforma-lia/src/components/chat/glossary-drawer.tsx`<br>`plataforma-lia/src/components/chat/glossary-highlighted-text.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx` |
| 🔴 | `aa664e84b` | 2026-04-24 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Add ability to explain automated decisions to candidates — Adds a new API endpoint and tool for explaining automated decisions to candidates, and updates docum | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidate_portal_explanation.py` |
| 🔴 | `e1dcee729` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 3.2 | restore(lia): recover Onda 3.2—5.1 work + new Onda 5.3.a after parallel rollback — Context: commit c698d5eef "Restored to 'c3d45b3d8...'" (via Replit rollback | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/lia_briefing_formatter.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/citation_processor.py` |
| 🔴 | `c698d5eef` | 2026-04-22 | Cross IA↔Front | (Auto-commit Replit) | Restored to 'c3d45b3d8ddb560ce2ee3a23c6062d8ae325a6f4' — Replit-Restored-To: c3d45b3d8ddb560ce2ee3a23c6062d8ae325a6f4 | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/job_readiness.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/ai/services/llm.py` |
| 🔴 | `c320409e5` | 2026-04-22 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Task #791: Remove Job Readiness Hub feature (frontend + backend) — Consolidates around the unified funnel view by fully removing the legacy | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/job_readiness.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`<br>`lia-agent-system/app/domains/job_management/services/job_readiness_service.py` |
| 🟡 | `ad6ce7073` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 4.11 | fix(lia): Onda 4.11 + 4.12 — briefing formatter keys + III.B log level — Two post-smoke corrections for Onda 4 B-phase runtime visibility: | `lia-agent-system/app/domains/recruiter_assistant/services/lia_briefing_formatter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `3d316958b` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 4.10 | feat(lia): Onda 4.10 — adapter forwards citations + hitl_checkpoint to API envelope — PARTE L gap discovered in runtime smoke: MainOrchestrator produces | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `a06559d59` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 3.3 | feat(lia): Onda 3.3 Init VII — error recovery policies catalog v1 — 5 canonical policies for deterministic error responses (was: LIA improvised | `lia-agent-system/app/orchestrator/error_policies.py`<br>`lia-agent-system/app/orchestrator/error_policies.yaml` |
| 🟡 | `34c7d2cb7` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 3.2 | feat(lia): Onda 3.2 G3 — HITL checkpoint surfacing — HITL logic already exists at app/tools/executor.py:283 (detects requires_hitl | `lia-agent-system/app/orchestrator/hitl.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `f7b8ec3a6` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 2.5 | feat(lia): Onda 2.5 Init II.D — workflow_context slot + 3 v1 workflows — Formalizes multi-turn flows (cancelamento, sourcing com filtros, wizard de | `lia-agent-system/app/orchestrator/workflow_registry.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `a45875997` | 2026-04-21 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(lgpd): G5 light — PII redaction at response boundary — Onda 2.1. Closes LGPD blocker for Init IV (briefing) + Init V (citations). | `lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `c3d45b3d8` | 2026-04-21 | Cross IA↔Back | §16 LIA Persona | Introduce multi-tenant capability toggles to control agent features — Add `enabled_for_tenant` field to capability cards in `capability_cards.yaml` and update ` | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🔴 | `833241d10` | 2026-04-21 | Cross Back↔Front | Configurações (hub) | fix: corrige botao Analisar nosso site em MinhaEmpresaHub — RCA: prompt sem URL + autoSend false + system prompt sem invocacao direta | `plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🔴 | `6ce1b1898` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Refactor "Minha Empresa" hub: contextual uploads + per-card progress — Original task #779: distribute document upload across section cards | `plataforma-lia/src/app/api/backend-proxy/documents/upload/route.ts`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx`<br>`plataforma-lia/src/components/settings/SectionUploadDropZone.tsx` |
| 🟡 | `ba28c86ff` | 2026-04-21 | Cross IA↔Back | §12 DEVELOPER_HANDOFF — PARTE L | fix(lia): FIX 29 + FIX 30 — close runtime-inert gaps (PARTE L pattern) — Empirical smoke test against live LIA API (via JWT) revealed two FIXes from | `lia-agent-system/app/orchestrator/memory_resolver.py` |
| 🟡 | `42d5dbb7b` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 21 | feat(lia): Track 1 Fases B+C+D — FIX 21-28 (LIA Maturity Program) — Follows FIX 20 (pagination, 182dec756). 8 canonical-fix patches from real-chat | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/memory_resolver.py`<br>`lia-agent-system/app/orchestrator/pending_action.py` |
| 🔴 | `e03e9c7fa` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | task#765: JobVacancy.benefits ARRAY→JSONB with structured backfill — Backend | `lia-agent-system/alembic/versions/100_job_vacancy_benefits_jsonb.py`<br>`lia-agent-system/app/api/v1/job_vacancies/_shared.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/api/v1/job_vacancies/public.py`<br>`lia-agent-system/app/domains/job_management/services/job_embedding_service.py` |
| 🔴 | `843a0d224` | 2026-04-21 | Cross IA↔Front | Tasks #712-#886 (Features de produto) | Task #768 — Workforce planning: rich view + 3 conversational paths + HITL — Backend (lia-agent-system): | `lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx`<br>`plataforma-lia/src/components/settings/WorkforceHubContent.tsx` |
| 🔴 | `3045bdfdd` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Task #767: remove Departamentos from "Minha Empresa" Hub + onboarding — Scope: | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/components/onboarding/OnboardingActionOrchestrator.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx`<br>`plataforma-lia/src/components/settings/UsuariosDepartamentosHub.tsx` |
| 🔴 | `a2913e268` | 2026-04-21 | Cross Back↔Front | scope: minha-empresa | feat(minha-empresa): Benefícios item-a-item + schema unificado em 4 camadas — Task #764 — piloto do hub "Minha Empresa". | `lia-agent-system/alembic/versions/099_extend_company_benefits_schema.py`<br>`lia-agent-system/app/api/v1/company_benefits.py`<br>`lia-agent-system/libs/models/lia_models/company_benefit.py`<br>`plataforma-lia/src/components/expanded-chat/stages/SalaryStage.tsx`<br>`plataforma-lia/src/components/job-wizard/stages/SalaryStage.tsx` |
| 🔴 | `77e31602c` | 2026-04-21 | Cross IA↔Front | §16 LIA Persona | Fix infinite loop in modal by stabilizing hook identity — Refactors `useInterpretContext` to ensure stable identity for `sendMessage` by using refs and functi | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/kanban/components/useUniversalTransitionModal.tsx` |
| 🔴 | `69b7fd1d8` | 2026-04-21 | Cross Back↔Front | §15 WSI | Task #745: Show recruiters the official WSI/Bloom term definitions in chat — What changed | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/glossary.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/slash-commands.ts` |
| 🟡 | `2f80103aa` | 2026-04-21 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Pass company_id to all remaining LIA SystemPromptBuilder callers — Original task (#694): SystemPromptBuilder.build() now injects a tenant | `lia-agent-system/app/api/v1/candidate_search/misc_search.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/interview_notes.py`<br>`lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant/conversational.py` |
| 🟡 | `a79295468` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #730: Train meta-question router with new examples (PT-BR variations) — ## Original task | `lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `8afc623b0` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #729 — Reconcile recruitment_campaigns schema drift (Alembic 097) — Original task: endpoint /api/v1/recruitment_campaigns?status=active was | `lia-agent-system/alembic/versions/097_reconcile_recruitment_campaigns_columns.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `13076fceb` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/action_handlers/sourcing_actions.py | `lia-agent-system/app/domains/ai/services/hybrid_search_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `9034a168b` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `2379e592c` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `453a46615` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 13 | refactor(obs): FIX 13 - migrate observability to canonical path (ADR-019) — Moves tool_metrics observability module from non-canonical path to the | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `d0a565f95` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `3f7245f18` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 12 | feat(ai): FIX 12 - HITL envelope + observability module (LangSmith-optional) — G8 - HITL envelope in ChatResponse: | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `cf12c3ec9` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 11 | feat(ai): FIX 11 - actions_context placement + WSI cluster cross-ref — G5 - actions_context placement: | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `71a2ec1d1` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 5 | feat(ai): FIX 5+6+7 - wizard sync, observability, semantic overlap — FIX 5 (P2): Wizard TOOL_DEFINITIONS now enriched from YAML | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/tools/__init__.py` |
| 🟡 | `82009b0c8` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 1 | feat(ai): FIX 1 - DomainActions now reach LLM via routing context — - Add DomainPrompt.get_actions_for_prompt(max_actions=8) to base.py | `lia-agent-system/app/orchestrator/llm_cascade.py`<br>`lia-agent-system/app/tools/__init__.py` |
| 🔴 | `2f1bd439c` | 2026-04-21 | Cross Back↔Front | scope: auth+fe | fix(auth+fe): JWT blacklist check in get_current_user + CandidatePreview re-export — - dependencies.py: import is_token_blacklisted and check before decode_toke | `lia-agent-system/app/auth/dependencies.py`<br>`plataforma-lia/src/components/candidate-preview/index.ts` |
| 🔴 | `248df840c` | 2026-04-21 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | fix(task-712): address review nits — single prefill + global broadcaster — 1) OnboardingActionOrchestrator.startStep: triggerAction ja despacha | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/auth/dependencies.py`<br>`lia-agent-system/app/auth/security.py`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/onboarding/OnboardingActionOrchestrator.tsx` |
| 🟡 | `aae815734` | 2026-04-21 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(task-712): close 3 final compliance/registry findings — 1) FairnessGuard recursivo em writes de settings. | `lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml` |
| 🟡 | `cb56abc90` | 2026-04-21 | Cross IA↔Back | Privacy / PII (W7) | feat(task-712): real PII masking + structured extraction + tool metadata — Closes the 3 remaining findings from the second code review. | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🔴 | `132d74252` | 2026-04-21 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | feat(task-712): close validation gaps — orchestrator, sync, two-phase, tests — Closes the 4 outstanding findings from the validation review: | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/app/[locale]/onboarding/page.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/onboarding/OnboardingActionOrchestrator.tsx`<br>`plataforma-lia/src/components/onboarding/OnboardingChatPage.tsx` |
| 🔴 | `2e826f587` | 2026-04-20 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | fix(task-712): align code with doc per code review (5 fixes) — - backend domain.py: configure_benefits returns clarification with navigation_hint | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/app/[locale]/onboarding/page.tsx` |
| 🔴 | `d1ed07e4d` | 2026-04-20 | Cross Back↔Front | Configurações (hub) | Task #712: company_settings delega 7 actions + onboarding proativo — Backend (lia-agent-system): | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/onboarding/SetupProgressBanner.tsx`<br>`plataforma-lia/src/components/onboarding/onboarding-controller.tsx`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `527f2c3ce` | 2026-04-20 | Cross IA↔Back | scope: tools | feat(tools): canonical routing fixes — P0 + P1.A + P1.B + P1.C — Foundation for Tools Unification Migration (ADR-016). Adds the 5 non-regressive | `lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `27aaa3461` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #690: Enriquecer descrições de actions e tools com padrão rico (concluído) — ## O que foi feito | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🔴 | `f05db64d8` | 2026-04-20 | Cross IA↔Front | §8 Glossário / Production-Ready | Task #691: Padronizar domínios em evolução para production-ready — Closes three critical gaps from MATURITY_ASSESSMENT and creates the canonical | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py`<br>`lia-agent-system/libs/models/lia_models/billing.py`<br>`plataforma-lia/src/components/pages/modules-page.tsx` |
| 🟡 | `4930b4092` | 2026-04-20 | Cross IA↔Back | §8 Glossário / Production-Ready | feat(docs): Task #692 — Glossário Central + sync automático + CI guard — ## O que foi entregue | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `21f90805f` | 2026-04-20 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Task #672 — DEFAULT_DOMAIN routing warning + chat-capabilities CI gate — Closes Fase 2C P0-2 (silent fallback) and P2-4 (regression guard). | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/domain_mappings.py` |
| 🔴 | `f2699be3f` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | feat(ui): redesign WorkflowRail floating ball + compact BetaBadge — Task #648: resolve visual collision between WorkflowRail's collapsed ball | `plataforma-lia/src/components/sidebar.tsx`<br>`plataforma-lia/src/components/ui/beta-badge.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟡 | `ceb6c78fa` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Fix stale import paths across backend (task #585) — Followed up on task #581 (which fixed a single `app.config.database` → | `lia-agent-system/app/api/v1/onboarding.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/api/v1/whatsapp_webhook.py`<br>`lia-agent-system/app/api/v1/wsi/admin.py`<br>`lia-agent-system/app/domains/automation/services/proactive_alert_service.py` |
| 🟡 | `43d9891d3` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Wire up duplicate_job and clone_job chat actions (Task #624) — Original task: finish the deferred 'duplicate_job' and 'clone_job' chat | `lia-agent-system/app/domains/job_management/domain.py`<br>`lia-agent-system/app/tools/job_tools.py` |
| 🟡 | `933949c9f` | 2026-04-20 | Cross IA↔Back | Scheduling / Calendar (PR-CAL) | Fix mismatched scheduling-link database schema (Task #625) — The SelfSchedulingLink SQLAlchemy model targets the rich | `lia-agent-system/alembic/versions/096_align_self_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/interview_actions.py` |
| 🟡 | `2bf526354` | 2026-04-20 | Cross IA↔Back | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Task #552: Echo routed specialist on chat replies — The persona-diagnostic routing audit (Task #537) populates `agent_observed` | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `bd974aea4` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #620: Surface ReAct tool calls on the chat HTTP response (LIA-LCF-01) — When recruiters asked vacancy questions ("quantos candidatos tem a vaga V0037?"), | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `bf0398f7a` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | Add a button to return to the chat from other sections — Adds a "Back to Chat" button to the workflow rail, visible on all pages except the chat itself. This | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx`<br>`plataforma-lia/src/components/workflow-rail/workflowRailCatalog.ts` |
| 🔴 | `11389ca5e` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | Update workflow rail component to match BP7 design standards — Refactors the WorkflowRail component to align with BP7 design guidelines, including UI enhancemen | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟡 | `a174d7d67` | 2026-04-20 | Cross IA↔Back | §6 Chat Unificado / Funil | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos validados pelo auditor + smoke test: | `lia-agent-system/app/domains/job_management/services/job_vacancy_lifecycle_service.py`<br>`lia-agent-system/app/domains/sourcing/domain.py`<br>`lia-agent-system/app/shared/compliance/protected_attributes.py` |
| 🔴 | `c6220768f` | 2026-04-20 | Cross IA↔Front | Unified Chat (FE) | Improve job creation and candidate sourcing workflows — Update job vacancy fields, fix action IDs, connect orphaned tools, resolve missing config file, and  | `lia-agent-system/app/shared/prompts/interaction_patterns.py`<br>`plataforma-lia/src/components/unified-chat/._OutreachCard.tsx`<br>`plataforma-lia/src/components/unified-chat/._ThinkingStepsCard.tsx`<br>`plataforma-lia/src/components/unified-chat/._UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/._UnifiedChatHeader.tsx` |
| 🟡 | `9eafa6207` | 2026-04-19 | Cross IA↔Back | scope: tools | fix(tools): P0/P1 hardening — multi-tenancy + capacity + factory bypass — - executor.py: execute_batch() now propagates ToolExecutionContext to every | `lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py`<br>`lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/executor.py` |
| 🔴 | `22d0f1da4` | 2026-04-19 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #582: Phase 2 chat sanitization for the 5 P1 domains — Make every chat tool registered in ats_integration, automation, | `lia-agent-system/app/domains/ats_integration/domain.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_sync_service.py`<br>`lia-agent-system/app/domains/automation/domain.py`<br>`lia-agent-system/app/domains/automation/services/automation_service.py`<br>`lia-agent-system/app/domains/automation/services/automation_trigger_service.py` |
| 🟡 | `d312e34dd` | 2026-04-19 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #584 — Auto-discovery of AGENT_TYPE_TO_DOMAIN — Replaces the hand-maintained dict in app/orchestrator/domain_mappings.py with | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py`<br>`lia-agent-system/app/domains/automation/domain.py`<br>`lia-agent-system/app/domains/candidate_self_service/domain.py` |
| 🔴 | `9ebfa3359` | 2026-04-19 | Cross Back↔Front | Configurações (hub) | Add functionality to manage candidate requests and improve system stability — Introduce new API endpoints for handling RH dashboard requests, implement LGPD Art | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/rh_dashboard.py`<br>`lia-agent-system/app/domains/hiring_policy/domain.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx` |
| 🔴 | `e3c1ed576` | 2026-04-19 | Cross IA↔Front | Job Management (BE) | Improve job management and candidate comparison tools — Refactors job management tools to use a dedicated service layer, enhances the candidate comparison f | `lia-agent-system/app/domains/job_management/services/job_vacancy_lifecycle_service.py`<br>`lia-agent-system/app/domains/sourcing/services/consent_cache.py`<br>`lia-agent-system/app/tools/job_tools.py`<br>`plataforma-lia/src/app/candidate/layout.tsx` |
| 🔴 | `1122226d3` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | chore(chat): saneamento Fase 1 (P0) da cadeia de execução do chat unificado — Task #580 — auditoria programática havia detectado 81 handlers de tools com | `plataforma-lia/src/app/candidate/layout.tsx` |
| 🟡 | `94aba8ebe` | 2026-04-19 | Cross IA↔Back | Communication domain (BE) | Update system to properly expose tool handlers and improve robustness — Refactors service layer to expose module-level wrappers for chat tool handlers, enhances | `lia-agent-system/app/api/v1/whatsapp_webhook.py`<br>`lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`<br>`lia-agent-system/app/domains/analytics/services/job_insights_service.py`<br>`lia-agent-system/app/domains/analytics/services/job_report_service.py`<br>`lia-agent-system/app/domains/analytics/services/predictive_analytics_service.py` |
| 🔴 | `744e161de` | 2026-04-19 | Cross IA↔Front | Frontend (componentes diversos) | Update candidate status page and chat features — Integrate the candidate chat feature with backend APIs, improve proactive hint handling, add caching | `lia-agent-system/app/api/v1/proactive_actions.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_service.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/precondition_checker.py`<br>`plataforma-lia/src/app/api/backend-proxy/candidate/applications/route.ts` |
| 🔴 | `0120f8d7e` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no Apêndice A da auditoria #569 | `lia-agent-system/app/api/v1/lia_feedback.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🔴 | `f94022429` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no Apêndice A da auditoria #569 | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/lia_feedback.py`<br>`lia-agent-system/app/api/v1/proactive_actions.py`<br>`plataforma-lia/src/app/api/backend-proxy/consumption/route.ts`<br>`plataforma-lia/src/components/chat/message-feedback.tsx` |
| 🔴 | `8314d3517` | 2026-04-19 | Cross IA↔Front | §12 DEVELOPER_HANDOFF — PARTE D | fix(parte-d): close 4 PARTE D gaps — full tracking + canonical schema + manifest wiring + proactive UI — Gap 1 — company_scraper_service Apify tracking (P1): | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/proactive-hints-list.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ChatMessageList.tsx` |
| 🟡 | `3139e3e7f` | 2026-04-19 | Cross IA↔Back | §6 Chat Unificado / Funil | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — Auditoria read-only escopada à Task #569. | `lia-agent-system/app/domains/company/services/company_scraper_service.py`<br>`lia-agent-system/app/orchestrator/precondition_checker.py` |
| 🟡 | `f4106776c` | 2026-04-19 | Cross IA↔Back | §13 PARTE D — Foundation/Apify/Manifest | feat(platform): D4 Platform Manifest — single source of truth for pages, methodology, capabilities — Replaces hardcoded page lists + hardcoded _PLATFORM_KNOWLED | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `eee514587` | 2026-04-19 | Cross IA↔Back | Configurações (hub) | feat(lia-tools): D1 enrichment + company settings tools — D1.a enrichment_tools.py (sourcing domain, 2 tools): | `lia-agent-system/app/tools/__init__.py` |
| 🔴 | `43e417b0e` | 2026-04-19 | Cross Back↔Front | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Fix message actions in unified chat (copy, thumbs) — Task #567: The copy / thumbs / "+" buttons under each LIA message gave | `lia-agent-system/app/domains/sourcing/services/apify_search_service.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟡 | `b90eb3cfe` | 2026-04-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Enhance AI tracking durability and fairness checks — Implement an outbox pattern for AI usage tracking to ensure durability and persistence of data, alon | `lia-agent-system/alembic/versions/095_create_ai_consumption_outbox.py`<br>`lia-agent-system/app/domains/cv_screening/services/culture_analyzer_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py`<br>`lia-agent-system/app/domains/cv_screening/services/rubric_evaluation_service.py`<br>`lia-agent-system/app/main.py` |
| 🟡 | `82024c586` | 2026-04-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Add functionality to extract candidate names and reasons for rejection — Enhance the `reject_candidate` intent handler in `utils.py` to extract `candidate_name` | `lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `30359ced0` | 2026-04-19 | Cross IA↔Back | scope: lia-agent | feat(lia-agent): LIA Deep Audit P2 fixes (C3, D10) — C3 conversation_memory.py: | `lia-agent-system/app/domains/recruiter_assistant/services/conversation_memory.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `48fc90c2b` | 2026-04-19 | Cross IA↔Back | §2 Orchestrator Migration | Add ability to reject candidates and improve job duplication — Introduce the `reject_candidate` intent and action, enhance `duplicate_job` to support finding jo | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py`<br>`lia-agent-system/app/orchestrator/config/domain_routing.yaml` |
| 🔴 | `fb079b207` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | Task #563: agentic eval framework + canonical-fix consolidation — Original: build exhaustive 10-dimension agentic eval roteiro for LIA | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🟡 | `b4218eace` | 2026-04-19 | Cross IA↔Back | §14 BYOK + LLM Factory | fix(byok): corrigir 4 bugs P0 de audit trail e BYOK bypass — BUG-01: llm_factory._audit_llm_usage() usava kwargs errados em | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py`<br>`lia-agent-system/app/domains/voice/services/voice_screening_orchestrator.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🔴 | `c5b577cf5` | 2026-04-19 | Cross IA↔Front | Kanban (vagas) | Task #562 — Padronizar e enriquecer card do Kanban de Vagas — Alinha o card de vaga (página /jobs, visão Kanban) ao padrão visual e | `lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/services/wsi_compact_pipeline.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx` |
| 🟡 | `3de3ce2ba` | 2026-04-19 | Cross IA↔Back | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Extend AI cost tracking across LIA strategic flows (task #545) — Task #532 only instrumented WSI Layer 2. This change wires per-company | `lia-agent-system/app/api/v1/automation/event_handlers/handlers_interview.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/api/v1/lia_assistant_fasttrack.py`<br>`lia-agent-system/app/api/v1/screening.py` |
| 🟡 | `6b4cf486b` | 2026-04-19 | Cross IA↔Back | Privacy / PII (W7) | Reforça regex de ANO_FORMATURA em pii_masking (task #549) — Achado #3 da investigação Presidio (#533): a regex `_GRADUATION_YEAR_PATTERN` | `lia-agent-system/app/shared/compliance/c3b_layer.py` |
| 🟡 | `506cd0549` | 2026-04-19 | Cross IA↔Back | §15 WSI | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) + fix(query_tools): corrige runtime defect no fallback de shortcode — ## Frontend (e | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `48c9bf2c8` | 2026-04-19 | Cross IA↔Front | §15 WSI | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) — Adiciona testes de componente Vitest cobrindo o modal de Triagem (#529) | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/triagem-details/triagem-responses-section.tsx` |
| 🟡 | `805502657` | 2026-04-19 | Cross IA↔Back | i18n / Translation | fix eval: UnboundLocalError in executor + short job_id in query_tools | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `bf60a5df7` | 2026-04-19 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | fix eval: remove wrong CAST uuid, expand short job_id filter, wizard company_id rule | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `a805f1096` | 2026-04-19 | Cross IA↔Back | §15 WSI | task #532 (G23-04): tracking opcional de tokens da Camada 2 WSI — - safe_invoke (app/domains/ai/services/llm.py) ganha kwarg opcional | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/service.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `fd1f1bc44` | 2026-04-19 | Cross IA↔Back | §16 LIA Persona | revert(eval): restore communication.yaml and interaction_patterns.py — Reverted both files to pre-da2ca4737 state. | `lia-agent-system/app/shared/prompts/interaction_patterns.py` |
| 🔴 | `7de66b24a` | 2026-04-19 | Cross Back↔Front | §18 Senioridade + Job Migration | Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada) — ## What | `plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`<br>`plataforma-lia/src/components/screening-config/SCMSectionContent.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx` |
| 🔴 | `ad92fde29` | 2026-04-19 | Cross IA↔Front | §15 WSI | Task #530 — Kanban: indicador visual de modo degradado no score WSI — ## What | `lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardScores.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanScoreCells.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanDataEffects.ts` |
| 🔴 | `505c52265` | 2026-04-19 | Cross Back↔Front | Triagem (módulo) | Update modal to display information consistently across all views — Update the TriagemDetailsModal component to ensure the LGPD/EU AI Act banner is always visib | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟡 | `da2ca4737` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): salary benchmark in analytics + offer ID rule + negation cancel pattern + eval timeout 60s — - analytics.yaml: add get_job_insights for salary benchm | `lia-agent-system/app/shared/prompts/interaction_patterns.py` |
| 🟡 | `7b57d9156` | 2026-04-19 | Cross IA↔Back | §15 WSI | Add transparency data to response analyses and update evaluation results — Adds a new SQL migration to include `transparency_extras` in `wsi_response_analyses`  | `lia-agent-system/database/migrations/016_add_transparency_extras_to_wsi_response_analyses.sql` |
| 🟡 | `eb04ba77d` | 2026-04-19 | Cross IA↔Back | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🔴 | `2e4b903c4` | 2026-04-19 | Cross IA↔Front | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/models.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `a760fe110` | 2026-04-19 | Cross IA↔Back | §2 Orchestrator Migration | Improve job description generation and entity extraction — Update job description templating to dynamically generate responsibilities based on skills, and enha | `lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🟡 | `574a61e83` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | Update job search and salary suggestions with new parameters — Modify entity extraction for job titles, update salary suggestion logic to use a new market range | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🔴 | `aee9ab45f` | 2026-04-19 | Cross IA↔Front | §17 Eval Framework | fix(eval): add suggest_salary/generate_jd_direct to _JOB_ACTIONS + fix regex patterns — - Add suggest_salary and generate_jd_direct to _JOB_ACTIONS dispatch set | `lia-agent-system/app/api/v1/wsi/__init__.py`<br>`lia-agent-system/app/api/v1/wsi/admin.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `3b53ca02e` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): KB-006 UUID filter, WZ-002/003 JD+salary Phase1, MT-002/003 bypass — - Remove global UUID filter from executor._execute_action (fixes KB-006 V0037 co | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🟡 | `d2a8954d9` | 2026-04-19 | Cross IA↔Back | scope: handlers | fix(handlers): strip non-UUID entity_id from context before handler dispatch — Handlers like _analyze_funnel and _rank_candidates were using V0037 (short ID) | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `a41b000bd` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): KB-005 UUID guard + WZ-002/003 keywords + MT-002 job_title extraction — KB-005: executor.py now only injects entity_id as job/candidate_id when it is | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `881aef9d0` | 2026-04-19 | Cross IA↔Back | §16 LIA Persona | fix(persona): LIA identity override — prevent Gemini from leaking model identity — - Prepend REGRA ZERO identity block at top of lia_persona.yaml so it is read  | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🔴 | `75334b40f` | 2026-04-18 | Cross IA↔Front | §18 Senioridade + Job Migration | Add caching for job extraction and update job seniority fields — Implement an in-memory cache for Layer 2 extraction to improve performance and reduce redundant | `lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`plataforma-lia/src/components/jobs/jobsPageTypes.ts`<br>`plataforma-lia/src/components/screening-config/SCMSectionContent.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx` |
| 🟡 | `4af2b303d` | 2026-04-18 | Cross IA↔Back | §15 WSI | Add advanced semantic analysis and scoring for candidate responses — This commit introduces the Layer 2 LLM Extractor, enhancing the WSI scoring system by addin | `lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/service.py` |
| 🟡 | `a383445f3` | 2026-04-18 | Cross IA↔Back | §17 Eval Framework | fix(eval): list_jobs routing, duplica keyword, KB-005 time-per-stage, executor candidate_name — - capabilities.yaml: add list_jobs + listar_vagas + duplica keyw | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py` |
| 🔴 | `f947f9a21` | 2026-04-18 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Update fairness scoring and remove legacy code — Adjusts the fairness score range from 1-5 to 1-10 in the bias detection service, updates related ser | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py`<br>`lia-agent-system/app/shared/services/silver_medalist_service.py`<br>`plataforma-lia/src/components/jobs/jobsPageConstants.tsx`<br>`plataforma-lia/src/components/screening-config/ScreeningScriptTab.tsx` |
| 🔴 | `92bb7013f` | 2026-04-18 | Cross IA↔Front | §15 WSI | Update scoring logic and improve user interface for assessments — Refactor WSI scoring calculations, update Big Five trait representation, adjust API routes, an | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/multi_strategy_search.py`<br>`lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py` |
| 🟡 | `c134dc252` | 2026-04-18 | Cross IA↔Back | Configurações (hub) | fix(settings): company resolve-tenant null profile + LIA settings_config routing — - company.py: resolve-tenant fallback to client_account_id when no company_pr | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/orchestrator/domain_mappings.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `f58b65f80` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/domains/interview_intelligence/services/comparative_analysis_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py` |
| 🟡 | `24ada0f6b` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/api/v1/interview_analysis.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py`<br>`lia-agent-system/app/domains/interview_scheduling/services/interview_transcript_analysis_service.py` |
| 🟡 | `f328031da` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/scoring.py` |
| 🟡 | `47f65a29f` | 2026-04-18 | Cross IA↔Back | §17 Eval Framework | fix(eval): name resolution, implicit job context, wizard tenant scope, short-id fallback — - WZ-002/003: Add _wizard_tenant_scope context manager to wizard_reac | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `63b132301` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/service.py` |
| 🔴 | `273e01d54` | 2026-04-18 | Cross IA↔Front | §15 WSI | Improve candidate screening by refining scoring and default handling — Update SQL schema scores to a 0-10 range and adjust the seniority fallback mechanism. | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`<br>`lia-agent-system/database/wsi_schema.sql`<br>`lia-agent-system/database/wsi_schema_corrected.sql` |
| 🟡 | `934fda6ab` | 2026-04-18 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | audit(canonical): P1 fixes — entity_id precedence + cross-tenant guard in generate_report — - analytics_actions.py: 3 functions now resolve job_id via entity_id | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟡 | `58291e5cb` | 2026-04-18 | Cross IA↔Back | FastAPI v1 endpoints | Update agent behavior to prevent revealing internal technical details — Remove unnecessary context variables and update persona prompts to prevent disclosure of | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🔴 | `d881a64fe` | 2026-04-18 | Cross IA↔Front | §15 WSI | feat(wsi): PR3 frontend escala 0-10 (Task #512, issue #497) — Migra todo o frontend WSI da escala legada 1-5 para 0-10 ponta-a-ponta, | `lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/memory_resolver.py`<br>`lia-agent-system/app/orchestrator/wizard_state.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `fbbff9f49` | 2026-04-18 | Cross IA↔Back | §2 Orchestrator Migration | Add context automatically for company and recruiter IDs — Injects `company_id` and `recruiter_id` into tool parameters when available in the context, and upda | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `6b5fdd0c6` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/092_wsi_responses_session_fk.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `3543b9212` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `d8db05a12` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/094_wsi_responses_fk_restrict.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `90c05cfea` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `a9b7681f6` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py` |
| 🟡 | `a26e3c167` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui round 2 | `lia-agent-system/alembic/versions/092_wsi_responses_session_fk.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/auth/schemas.py` |
| 🟡 | `afe62dd3c` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI) com 5 entregas: | `lia-agent-system/alembic/versions/091_add_wsi_responses_audit_trail.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py` |
| 🟡 | `732cc16e4` | 2026-04-18 | Cross IA↔Back | §2 Orchestrator Migration | Update evaluation to include more candidate information and improve accuracy — Modify intent configurations to accept candidate names and IDs, and add correspon | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `9851a5eab` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #510: Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates) — Três fixes críticos no scorer determinístico WSI conforme spec WeDOTalent  | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `689b90885` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #497 PR2 — Flip atômico escala WSI 0-5 → 0-10 (engine + DB + Pydantic) — T1 wsi_scale.py flipado: SCALE_MAX 5→10, WSI_CUTOFFS 7.5/6.0, | `lia-agent-system/alembic/versions/090_widen_wsi_score_scale_to_10.py`<br>`lia-agent-system/app/api/v1/wsi/_shared.py`<br>`lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py` |
| 🟡 | `9b78e02ae` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #497 PR1: extrair constantes do engine WSI determinístico (zero behavior change) — CONTEXTO | `lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `d2cafcea0` | 2026-04-18 | Cross IA↔Back | Voice / ElevenLabs / STT | Refactor core voice screening logic and improve API error handling — This commit refactors the `process_call_completed` method in `wsi_voice_orchestrator.py` in | `lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/question_builder.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/session_repository.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `1d996df89` | 2026-04-18 | Cross IA↔Back | §15 WSI | refactor(wsi): extrair transcript_extractor do orchestrator (#496 PR1) — Inicia o split do voice_screening_orchestrator.py (P0-5 do audit WSI). | `lia-agent-system/app/domains/cv_screening/services/wsi_service/transcript_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🔴 | `e867c1d24` | 2026-04-18 | Cross IA↔Front | §15 WSI | feat(wsi): split tech/behav 100% determinístico via category explícita (#498) — Substitui o heurístico por peso (não-determinístico quando pesos são iguais) | `lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/models.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/score_calculator.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🔴 | `317680eef` | 2026-04-18 | Cross IA↔Front | §15 WSI | Phase 2 WSI/Screening remediation — G1 + G2 entregues; G3 promovido a tasks — Trabalho concluído (8 itens da Fase 2): | `lia-agent-system/alembic/versions/089_widen_wsi_check_constraints.py`<br>`lia-agent-system/app/api/v1/voice_screening.py`<br>`lia-agent-system/app/api/v1/wsi_async.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/score_calculator.py` |
| 🔴 | `51a09caec` | 2026-04-18 | Cross IA↔Back | §15 WSI | audit(wsi): Phase 1 remediação — selos rev. 5 + ADR-017 — Phase 1 do plano de remediação WSI aprovado pelo usuário, | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidates/_shared.py`<br>`lia-agent-system/app/api/v1/gemini_voice.py`<br>`lia-agent-system/app/api/v1/granular_consent.py`<br>`lia-agent-system/app/api/v1/openmic_webhook.py` |
| 🔴 | `5c9c2633a` | 2026-04-18 | Cross IA↔Back | Task #489 | Task #489: Protect remaining /api/v1 routers from URL shadowing bugs — Apply the Task #455 / #458 blindagem to 118 single-file routers under | `lia-agent-system/app/api/v1/_path_patterns.py`<br>`lia-agent-system/app/api/v1/activities.py`<br>`lia-agent-system/app/api/v1/admin_audit_decisions.py`<br>`lia-agent-system/app/api/v1/admin_bias_audit.py`<br>`lia-agent-system/app/api/v1/admin_dlq.py` |
| 🔴 | `50434ab66` | 2026-04-18 | Cross Back↔Front | Kanban (vagas) | Task #454 — KanbanColumnShell + chip variant tokens — Closes the kanban standardization series (#443 toolbar → #444 header | `plataforma-lia/src/components/pages/job-kanban/KanbanChip.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnShell.tsx` |
| 🔴 | `d06e4fe88` | 2026-04-18 | Cross Back↔Front | scope: jobs | feat(jobs): add Prontidão (readiness) column to Vagas list (Task #448) — - Backend: extend `list_job_vacancies` response with `readiness_stage` and | `lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`<br>`plataforma-lia/src/components/jobs/jobsPageTypes.ts`<br>`plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🔴 | `111c3403e` | 2026-04-18 | Cross Back↔Front | Task #429 | Task #429: Job Readiness Hub MVP — Implements an onboarding pipeline that guides recruiters through preparing | `lia-agent-system/alembic/versions/086_add_job_readiness_columns.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/job_readiness.py`<br>`lia-agent-system/app/domains/job_management/services/job_readiness_service.py`<br>`lia-agent-system/libs/models/lia_models/job_vacancy.py` |
| 🔴 | `bb15510bb` | 2026-04-18 | Cross Back↔Front | Task #436 | Fix candidate profile analysis 401/500 errors (Task #436) — Resolves two root causes: | `lia-agent-system/app/api/v1/lia_profile_analysis.py`<br>`plataforma-lia/src/app/[locale]/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/[id]/files/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/experience-highlights/[candidateId]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/experience-highlights/generate/route.ts` |
| 🔴 | `23b07df5f` | 2026-04-18 | Cross Back↔Front | scope: ui | feat(ui): toolbar canônica para vagas e candidatos (#443) — Cria primitives compartilhadas e tokens para padronizar as 3 toolbars | `plataforma-lia/src/components/pages/job-kanban/KanbanToolbar.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsHeader.tsx`<br>`plataforma-lia/src/components/ui/toolbar-button.tsx`<br>`plataforma-lia/src/components/ui/view-toggle.tsx` |
| 🟡 | `01ca35033` | 2026-04-18 | Cross IA↔Back | Mockup Sandbox (artefato gerado) | Task start baseline checkpoint for code review | `lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🔴 | `911e6a651` | 2026-04-18 | Cross Back↔Front | Task #435 | Task #435 — dedicated source_system column for ATS-imported job vacancies — Why | `lia-agent-system/alembic/versions/085_add_source_system_to_job_vacancies.py`<br>`lia-agent-system/app/api/v1/job_drafts.py`<br>`lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/api/v1/lia_assistant_fasttrack.py` |
| 🟡 | `49947851f` | 2026-04-18 | Cross IA↔Back | Task #417 | Migrate cv_match_tool to canonical authoring surface (Task #417) — Original task: Shrink the tool-authoring allow list (S7.5 / ADR-016) by | `lia-agent-system/app/tools/__init__.py` |
| 🔴 | `695fbfd97` | 2026-04-18 | Cross Back↔Front | §17 Eval Framework | Add job creation functionality to the jobs chat interface — Removes unused useRef import from useJobsChat.ts and updates useEffect logic to correctly handle job | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🔴 | `fbc1187c5` | 2026-04-18 | Cross Back↔Front | §7 WorkflowRail UX | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRail now exposes a footer button that opens the | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🔴 | `53450e056` | 2026-04-18 | Cross Back↔Front | Task #432 | Task #432: Rich responses no chat com PipelineRailCard — Frontend (plataforma-lia): | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/pipeline-rail-card.tsx` |
| 🔴 | `e9ec31e52` | 2026-04-18 | Cross Back↔Front | Kanban (vagas) | feat(jobs): toggle Tabela\|Kanban em /vagas (Task #431) — - Generalizou KanbanCard/KanbanColumn para aceitar KanbanItem genérico | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/types.ts`<br>`plataforma-lia/src/components/pages/jobs/JobsKanbanView.tsx` |
| 🔴 | `1043a8826` | 2026-04-18 | Cross IA↔Front | Task #430 | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a toggle on /visao-do-funil between the existing candidate funnel | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx`<br>`plataforma-lia/src/components/pages/pipeline-overview/pipeline-rail.tsx` |
| 🔴 | `d6b844269` | 2026-04-18 | Cross Back↔Front | Task #430 | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a 8-stage job lifecycle rail (ATS Importada → Encerrada) to /visao-do-funil | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`plataforma-lia/src/app/api/backend-proxy/jobs-lifecycle-overview/route.ts`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🔴 | `e5b77b78b` | 2026-04-18 | Cross Back↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx` |
| 🔴 | `405b68e3b` | 2026-04-18 | Cross IA↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/orchestrator/config/domain_routing.yaml`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_hooks/useTriagemSession.ts`<br>`plataforma-lia/src/components/triagem-details/TwilioCallButton.tsx` |
| 🔴 | `2d53bf4db` | 2026-04-18 | Cross Back↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx` |
| 🔴 | `b2086c0c4` | 2026-04-17 | Cross Back↔Front | Configurações (hub) | Improve screening invitation modal and configuration settings — Updates the screening invitation modal to correctly disable the send button based on candidate c | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx`<br>`plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx` |
| 🟡 | `9ffa41bee` | 2026-04-17 | Cross IA↔Back | §17 Eval Framework | Improve system responses and entity identification — Update `workflow.py` to use a generic clarification question and `chat_adapter.py` to correctly extr | `lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🔴 | `5e0ec22e0` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425 Pass 5 — close all 4 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system/app/api/v1/triagem.py): | `lia-agent-system/app/api/v1/triagem.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageModalsCore.tsx`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx` |
| 🔴 | `51a2fe664` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425: WSI 4 Canais MVP — pass 3 closes review blockers — Third review pass after a second REJECTED verdict. The reviewer flagged four | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageModalsCore.tsx`<br>`plataforma-lia/src/components/triagem/PhoneConfirmModal.tsx` |
| 🔴 | `c0cdf0747` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425: WSI 4 Canais MVP — pass 3 closes review blockers — Third review pass after a second REJECTED verdict. The reviewer flagged four | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/app/api/backend-proxy/twilio-voice/initiate/route.ts`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx` |
| 🔴 | `263aa6200` | 2026-04-17 | Cross IA↔Front | §15 WSI | Task #425 (foundation slice): WSI 4 Canais MVP — canonical model + master toggle + remove silent mocks — Foundation slice of Task #425 — narrowed from 8 sub-tas | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`lia-agent-system/app/orchestrator/config/domain_routing.yaml`<br>`lia-agent-system/app/orchestrator/fast_router.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx` |
| 🟡 | `b0c3126ac` | 2026-04-17 | Cross IA↔Back | §15 WSI | Update documentation and remove outdated WSI assessment guides — Remove four WSI documentation files and update references to canonical WSI guides. | `lia-agent-system/app/orchestrator/fast_router.py` |
| 🟡 | `415d6db42` | 2026-04-17 | Cross IA↔Back | Task #366 | Task #366 — promote actor_user_id to a structured audit field — Original task | `lia-agent-system/alembic/versions/084_add_actor_user_id_to_audit_logs.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/admin_audit_decisions.py`<br>`lia-agent-system/app/api/v1/bulk_actions.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🟡 | `035e96e10` | 2026-04-17 | Cross IA↔Back | Task #354 | Task #354: Block accidental tool registrations outside canonical entry point — Adds the S7.5 CI/pre-commit guard required by ADR-016 so future contributors | `lia-agent-system/app/tools/registry.py` |
| 🟡 | `dc3e16e5c` | 2026-04-17 | Cross IA↔Back | Task #353 | Task #353: Move per-tenant LLM provider config out of YAML and into the database — ADR-016 decided per-tenant `llm_provider` and `llm_fallback_order` should | `lia-agent-system/app/shared/providers/llm_factory.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |
| 🔴 | `1231c6b1f` | 2026-04-17 | Cross Back↔Front | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/floating-position.ts` |
| 🔴 | `7057f692e` | 2026-04-17 | Cross Back↔Front | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx` |
| 🔴 | `1dc1109ba` | 2026-04-17 | Cross Back↔Front | Task #403 | Task #403: Persist discarded candidates per search execution — Problem | `lia-agent-system/alembic/versions/083_persist_discarded_candidates.py`<br>`lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_search.py`<br>`lia-agent-system/app/api/v1/candidate_search/misc_search.py` |
| 🔴 | `af086a2d9` | 2026-04-17 | Cross Back↔Front | Task #402 | Task #402: Re-enrich discarded candidates from FilteredNoContactModal — Backend | `lia-agent-system/app/api/v1/candidate_search/contact.py`<br>`plataforma-lia/src/app/api/backend-proxy/search/enrich-discarded/route.ts`<br>`plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesTableArea.tsx` |
| 🔴 | `b96975212` | 2026-04-17 | Cross Back↔Front | Task #400 | Task #400: surface candidates discarded during contact enrichment — Backend | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_search.py`<br>`lia-agent-system/app/api/v1/candidate_search/search.py`<br>`lia-agent-system/app/api/v1/candidate_search/similar_search.py` |
| 🟡 | `f0df08ffc` | 2026-04-17 | Cross IA↔Back | §13 PARTE D — Proatividade | fix(lia): Wave A+B — tenant alias, scope routing, proactive tools — A1: tenant.py — added '37' and staging UUID to DEMO_COMPANY_LEGACY_ALIASES | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🔴 | `2026c1029` | 2026-04-17 | Cross Back↔Front | Task #394 | Task #394: Surface candidates filtered out by missing contact — `enrich_and_filter_candidates` was silently dropping candidates that | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_models.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_search.py` |
| 🔴 | `9c7385973` | 2026-04-17 | Cross IA↔Front | scope: lia | fix(lia): Fix5+6 agentic tool auth + main chat 422 | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts` |
| 🟡 | `58b50fc58` | 2026-04-17 | Cross IA↔Back | §2 Orchestrator Migration | Add navigation capabilities and context to agent responses — Introduces navigation intent detection for UI actions, enhances agent context with company and user | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/navigation_intent.py` |
| 🟡 | `4713cd342` | 2026-04-17 | Cross IA↔Back | Task #352 | task #352 — close out AUDIT FINAL 2026-04 finals (F4, F5, F8, F10, F11, F12) — Closes the remaining gaps from AUDIT_STATUS_REPORT_2026-04-FINAL.md. | `lia-agent-system/app/shared/compliance/bias_audit_service.py`<br>`lia-agent-system/app/shared/services/affirmative_service.py`<br>`lia-agent-system/app/shared/services/analysis_service.py`<br>`lia-agent-system/app/shared/services/briefing_service.py`<br>`lia-agent-system/app/shared/services/early_warning_service.py` |
| 🔴 | `d9c75df91` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #332: Surface FairnessGuard drops in WSI wizard + audit trail — Recruiters previously saw the WSI question count silently shrink when | `plataforma-lia/src/components/job-wizard/WizardContext.tsx`<br>`plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx`<br>`plataforma-lia/src/components/job-wizard/types.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-types.ts` |
| 🟡 | `0a6a412c8` | 2026-04-17 | Cross IA↔Back | Policy / Job Creation | Task #337: Forward actor_user_id to policy audit log — The policy chat orchestrator did not forward the logged-in user's id | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🔴 | `0acf9ef35` | 2026-04-17 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Task #341: Surface FairnessGuard sourcing blocks on the recruiter job page — Backend | `lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/domains/analytics/repositories/fairness_report_repository.py`<br>`lia-agent-system/app/shared/compliance/fairness_guard.py`<br>`plataforma-lia/src/app/api/backend-proxy/fairness/jobs/[jobId]/blocks/route.ts`<br>`plataforma-lia/src/components/jobs/JobFairnessBlockBanner.tsx` |
| 🔴 | `0bcf56528` | 2026-04-17 | Cross IA↔Back | Observability / Sentry / OTLP | Task #343: Collapse legacy observability paths into app.shared.observability — Stage 6 had not actually been executed at HEAD — `app/shared/observability/` | `lia-agent-system/app/api/v1/admin_token_budget.py`<br>`lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/agent_monitoring.py`<br>`lia-agent-system/app/api/v1/agent_quality_dashboard.py` |
| 🟡 | `4d210db7b` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Add fairness checks + audit trails to CV screening services (C1–C5) — Closes compliance gaps for LGPD Art. 20 / EU AI Act traceability across | `lia-agent-system/app/domains/cv_screening/services/cv_scoring_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/eligibility_verification_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/evaluation_criteria_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/lia_score_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/pre_qualification_service.py` |
| 🔴 | `426701baa` | 2026-04-17 | Cross Back↔Front | §6 Chat Unificado / Funil | fix(funil): higiene final P2 — ws-token, kill-switch deprecation, dedup hooks (Task #298) — Endereça causas raiz #8, #9 e #10 de docs/audits/candidates-root-cau | `lia-agent-system/app/shared/rails_migration/deprecation.py`<br>`plataforma-lia/src/app/api/auth/ws-token/route.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesQuery.ts`<br>`plataforma-lia/src/components/pages/candidates/index.ts` |
| 🟡 | `e59abd0da` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #316 — PolicySetupAgent: raise compliance from 25% → ~80% — Audit finding A2 flagged that PolicySetupAgent had all 6 compliance | `lia-agent-system/app/shared/compliance/c3b_layer.py` |
| 🟡 | `3bc3886bf` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #315: Wire enterprise compliance gates into JobCreationGraph — What changed: | `lia-agent-system/app/shared/compliance/audit_service.py`<br>`lia-agent-system/libs/models/lia_models/audit_log.py` |
| 🟡 | `1240f5859` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #321: Consolidate bias detectors into FairnessGuard SSOT — Unified 3 divergent bias-detection implementations into the canonical | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/job_creation/services/jd_enrichment.py`<br>`lia-agent-system/app/shared/compliance/bias_audit_service.py`<br>`lia-agent-system/app/shared/compliance/fairness_guard.py`<br>`lia-agent-system/app/shared/services/bias_audit_service.py` |
| 🟡 | `9a88c12e7` | 2026-04-17 | Cross IA↔Back | Task #322 | Task #322 — Cleanup: 12 órfãos, 5 stubs e duplicata exata de job_report_service — Removed 18 dead/duplicate files confirmed to have zero production importers: | `lia-agent-system/app/api/v1/company_benefits_api.py`<br>`lia-agent-system/app/api/v1/lia_assistant/__init__.py`<br>`lia-agent-system/app/api/v1/lia_autonomous.py`<br>`lia-agent-system/app/api/v1/lia_feedback.py`<br>`lia-agent-system/app/api/v1/lia_multimodal.py` |
| 🔴 | `211da7846` | 2026-04-17 | Cross Back↔Front | Task #319 | Move agent_chat_ws_router under /api/v1 prefix (Task #319 / W17+W2) — Original task: audit findings W17/W2 confirmed agent_chat_ws_router was | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active/route.ts` |
| 🟡 | `cc57d9110` | 2026-04-17 | Cross IA↔Back | §15 WSI | Task #317 — Compliance fixes for InterviewGraph & WSIInterviewGraph (A3/A4) — Both graphs now honour Choose Your AI by setting tenant_llm_context from | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| 🔴 | `14d8e53a5` | 2026-04-16 | Cross Back↔Front | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🔴 | `2e2412e79` | 2026-04-16 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 para o Funil de | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟡 | `d304ea242` | 2026-04-16 | Cross IA↔Back | §15 WSI | Task #238: Replace in-memory storage in WSI question-adjust endpoint with DB persistence — ## Summary | `lia-agent-system/app/api/v1/wsi/questions.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🔴 | `f4075de94` | 2026-04-16 | Cross Back↔Front | Performance | Improve candidate search performance and reliability with retries and timeouts — Adds a `fetchWithRetry` utility to handle network requests with configurable at | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🔴 | `726dc976c` | 2026-04-16 | Cross Back↔Front | Task #250 | feat(task-250): Show warning banner when external job source is unavailable — ## Summary | `lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsPageCore.ts` |
| 🔴 | `7f4fe24f7` | 2026-04-16 | Cross Back↔Front | Task #241 | Task #241: Destravar tela de vaga após criação manual — Original task: When users create a job via the manual modal, they were getting | `lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`plataforma-lia/src/components/pages/jobs/JobsModalsSectionTypes.ts`<br>`plataforma-lia/src/components/pages/jobs/useJobsStatusHandlers.ts` |
| 🔴 | `c9ef726f7` | 2026-04-16 | Cross IA↔Front | §15 WSI | Task #244: Backend canonical cleanup (WSI router consolidation) — Scope (from task plan): collapse historical patch_*.py shims and overlapping | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/wsi/questions.py`<br>`lia-agent-system/app/api/v1/wsi_question_adjust.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`lia-agent-system/apps/api-vagas/main.py` |
| 🔴 | `14a215850` | 2026-04-16 | Cross Back↔Front | Task #243 | Task #243: Unify dev auto-login and fix demo user seed — Backend (lia-agent-system): | `lia-agent-system/app/auth/dependencies.py`<br>`lia-agent-system/app/main.py`<br>`plataforma-lia/src/app/api/auth/auto-login/route.ts`<br>`plataforma-lia/src/app/api/auth/ws-token/route.ts` |
| 🔴 | `ff42c5642` | 2026-04-16 | Cross IA↔Back | Task #242 | task #242: eliminar colisão de mapper SQLAlchemy — Causa raiz: `lia-agent-system/app/models/` continha 120 arquivos shim | `lia-agent-system/alembic/env.py`<br>`lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/public/shared_searches.py`<br>`lia-agent-system/app/api/v1/admin.py`<br>`lia-agent-system/app/api/v1/admin_compliance_fairness.py` |
| 🔴 | `0e5ec3b9b` | 2026-04-16 | Cross IA↔Front | §15 WSI | Update webhook paths and improve question retrieval — Regenerate OpenAPI types to reflect backend changes in webhook paths and update the WSI question ret | `lia-agent-system/app/api/v1/wsi_question_adjust.py` |
| 🟡 | `25077dd3a` | 2026-04-16 | Cross IA↔Back | Task #234 | Fix duplicate FastAPI operation IDs (task #234) — Original task: backend startup emitted 12 "Duplicate Operation ID" UserWarnings | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/job_status_webhooks.py`<br>`lia-agent-system/app/api/v1/wsi_question_adjust.py` |
| 🔴 | `8486175f9` | 2026-04-15 | Cross IA↔Front | Task #215 | feat: Pull QA fixes from fix/qa-2026-04-15 branch (Task #215) — Integrated 13 QA bug fixes from the fix/qa-2026-04-15 branch (SHA b61621bba) | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`<br>`lia-agent-system/app/orchestrator/config/domain_routing.yaml`<br>`lia-agent-system/app/orchestrator/navigation_intent.py` |
| 🔴 | `f7b3be109` | 2026-04-15 | Cross Back↔Front | Hooks (FE) | fix: resolve default_languages column type mismatch (ARRAY→JSONB) — The company_culture_profiles.default_languages column is jsonb in the DB | `lia-agent-system/app/domains/company_culture/repositories/company_culture_repository.py`<br>`lia-agent-system/libs/models/lia_models/company_culture.py`<br>`plataforma-lia/src/app/api/backend-proxy/company/culture-profile/[companyId]/route.ts`<br>`plataforma-lia/src/components/settings/BenefitsTab.tsx`<br>`plataforma-lia/src/components/settings/useGoalsPlanningHub.ts` |
| 🔴 | `c50dfb90d` | 2026-04-15 | Cross IA↔Front | Task #213 | Task #213: Pull GitHub Updates (wedotalent02202026 + ats-api-copia) — Fetched and merged updates from both GitHub remotes: | `lia-agent-system/alembic/versions/078_few_shot_candidates.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_studio_quality.py`<br>`lia-agent-system/app/api/v1/briefing.py`<br>`lia-agent-system/app/api/v1/chat.py` |
| 🔴 | `59038c744` | 2026-04-15 | Cross Back↔Front | Task #210 | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py endpoint to return 7 new section IDs: | `lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🔴 | `403074a45` | 2026-04-15 | Cross IA↔Front | Task #206 | Task #206: Minha Empresa conversational cards + backend context routing — - Added `settings_config` to ChatContextType in lia-float-context.tsx | `lia-agent-system/app/orchestrator/context_adapter.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx`<br>`plataforma-lia/src/contexts/lia-float-context.tsx` |
| 🟡 | `70c32ce48` | 2026-04-15 | Cross IA↔Back | Configurações (hub) | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py`<br>`lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/orchestrator/config/domain_routing.yaml` |
| 🟡 | `9126096cb` | 2026-04-14 | Cross IA↔Back | Task #93 | cleanup: remove LLMProviderFactory deprecated methods [PX08-081] Wave 6 item 6.1 — - Removed LLMProviderFactory.generate_with_fallback() (deprecated, global sta | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🔴 | `e4faeb8c9` | 2026-04-14 | Cross Back↔Front | Sprint 12 | feat: Digital Twin config UI with premium design + chat cards [PX08-077] Sprint 12 item 12.2 — Backend: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/__init__.py`<br>`lia-agent-system/app/api/v1/ai_config.py`<br>`plataforma-lia/src/components/chat/AIConfigChatCards.tsx`<br>`plataforma-lia/src/components/settings/AIConfigPanel.tsx` |
| 🔴 | `dde1a35bf` | 2026-04-14 | Cross Back↔Front | §16 LIA Persona | feat: connect recruiter personalization to agent prompts [P36-079] Sprint 12 item 12.4 — - PersonalizationContext.to_prompt_snippet(): formats profile as readab | `lia-agent-system/app/domains/analytics/services/recruiter_personalization_service.py`<br>`plataforma-lia/src/components/settings/RecruiterPreferencesPanel.tsx` |
| 🔴 | `93802c751` | 2026-04-14 | Cross Back↔Front | Sprint 12 | feat: Explain Decision button with reasoning transparency [PX08-080] Sprint 12 item 12.5 — Backend: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/__init__.py`<br>`lia-agent-system/app/api/v1/decision_explanation.py`<br>`plataforma-lia/src/components/decision-explainer.tsx` |
| 🟡 | `537e104d7` | 2026-04-14 | Cross IA↔Back | §15 WSI | feat: WSI weights per tenant via CalibrationWeight [P36-078] Sprint 12 item 12.3 — - score_calculator.calculate() accepts tech_weight/behav_weight params (defau | `lia-agent-system/app/domains/cv_screening/services/cv_screening_batch_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/score_calculator.py` |
| 🔴 | `5f705ff1b` | 2026-04-14 | Cross Back↔Front | §9 Security / Tenant guards | feat: calibration dashboard — LIA vs recruiter divergences [PX08-068] — Sprint 10 item 10.3 — Backend + Frontend for calibration analysis. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/calibration_dashboard_v2.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/calibration-dashboard/route.ts`<br>`plataforma-lia/src/components/agent-control-center/index.tsx` |
| 🔴 | `008535151` | 2026-04-14 | Cross Back↔Front | FastAPI v1 endpoints | feat: ML predictions dashboard — time-to-fill per vacancy [PX08-067] — Sprint 10 item 10.2 — Backend + Frontend for TTF predictions. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/ml_predictions_dashboard.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/ml-predictions/route.ts`<br>`plataforma-lia/src/components/agent-control-center/index.tsx` |
| 🔴 | `dddda1a0f` | 2026-04-14 | Cross Back↔Front | Compliance / LGPD / EU AI Act | feat: agent quality dashboard — aggregated metrics endpoint [PX08-066] — Sprint 10 item 10.1 — New endpoint that aggregates agent quality data | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_quality_dashboard.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/agent-quality-dashboard/route.ts` |
| 🟡 | `71c2f86aa` | 2026-04-14 | Cross IA↔Back | §14 BYOK + LLM Factory | refactor: migrate all raise Exception() to LIAError hierarchy [P35-060] — Zero generic raise Exception() remaining in app/ (was 8). | `lia-agent-system/app/domains/candidates/services/candidate_feedback_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_recording_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py`<br>`lia-agent-system/app/domains/integrations_hub/services/graph_client.py`<br>`lia-agent-system/app/domains/integrations_hub/services/microsoft_graph_service.py` |
| 🟡 | `401bc516b` | 2026-04-14 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: protected attributes YAML single source of truth [P35-045] — Sprint 5 item 5.5 — Created config/protected_attributes.yaml with 14 | `lia-agent-system/app/shared/compliance/fairness_guard.py`<br>`lia-agent-system/app/shared/compliance/protected_attributes.py` |
| 🔴 | `0ffd3e681` | 2026-04-13 | Cross Back↔Front | Task #189 | Fix SearchResults state preservation and duplicate index issue — Task #189: Fix SearchResults state e duplicate index | `plataforma-lia/src/components/pages/candidates/lia-sidebar/TabJobDescription.tsx`<br>`plataforma-lia/src/components/pages/candidates/lia-sidebar/TabSimilar.tsx` |
| 🔴 | `d351f0710` | 2026-04-13 | Cross Back↔Front | Frontend (componentes diversos) | Apply Portuguese translations and fix various bugs across the application — This commit translates numerous English terms to Portuguese (e.g., "Score" to "Nota" | `lia-agent-system/app/api/v1/company.py`<br>`plataforma-lia/src/components/LiaMetricsFunnelSection.tsx`<br>`plataforma-lia/src/components/LiaScreeningRightPanel.tsx`<br>`plataforma-lia/src/components/PromptSuggestionsPanel.tsx`<br>`plataforma-lia/src/components/alerts/alert-settings-modal.tsx` |
| 🔴 | `0a7a49dee` | 2026-04-13 | Cross Back↔Front | Backend Proxy Routes (FE) | Make candidate search results consistently appear on the screen — Fix three API routes that were not properly unwrapping backend responses, ensuring that candid | `plataforma-lia/src/app/api/backend-proxy/search/candidates/from-cv/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/refine/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/route.ts` |
| 🔴 | `620e9fcaf` | 2026-04-13 | Cross Back↔Front | §1 Teams Integration | Task #180: Integração Bot Teams em Produção — ## O que foi feito | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/main.py`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `5be674ef3` | 2026-04-13 | Cross Back↔Front | Backend Proxy Routes (FE) | Update API to correctly handle backend responses and improve server restart — Fix incorrect JSON unwrapping in API routes and adjust retry logic for server read | `lia-agent-system/app/domains/hiring_policy/domain.py`<br>`lia-agent-system/app/domains/job_management/domain.py`<br>`lia-agent-system/app/domains/sourcing/domain.py`<br>`plataforma-lia/src/app/api/backend-proxy/alerts/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/auth/[...slug]/route.ts` |
| 🟡 | `3f416f078` | 2026-04-13 | Cross IA↔Back | scope: loop | feat(loop): Activate agentic loop by default + fix imports (LIA-A04) — 1. LIA-A04 activated by default: | `lia-agent-system/app/domains/cv_screening/domain.py`<br>`lia-agent-system/app/domains/pipeline/domain.py`<br>`lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `8e83578d1` | 2026-04-13 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(compliance): Fase 3b — WS/SSE compliance strangler LIA-C3b — User-directed implementation of C3b compliance layer (strangler pattern). | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/cultural_fit.py`<br>`lia-agent-system/app/api/v1/ml_feedback.py` |
| 🔴 | `7cf2b4722` | 2026-04-13 | Cross Rails+Replit | scope: deploy | feat(deploy): Migrations applied + Rails handlers evolved with side-effects — Migration fix — webhook table conflict resolution: | `ats-api-copia/app/workers/lia_events_worker.rb`<br>`lia-agent-system/alembic/versions/074_webhooks.py`<br>`lia-agent-system/libs/models/lia_models/webhook.py` |
| 🔴 | `9969e1358` | 2026-04-13 | Cross Back↔Front | §13 PARTE D — Foundation/Apify/Manifest | feat(#170): Intelligent Apify + Pearch pipeline for candidate enrichment — - Enrichment pipeline routes UUID candidates through enrich_batch (with DB | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py`<br>`lia-agent-system/app/api/v1/candidate_search/credits.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_search.py` |
| 🔴 | `78b62cdaf` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.5b — External Webhooks for Studio events — Allows clients to subscribe to Studio events and receive HTTP POSTs | `lia-agent-system/alembic/versions/074_webhooks.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_approvals.py`<br>`lia-agent-system/app/api/v1/agent_deployments.py`<br>`lia-agent-system/app/api/v1/custom_agents.py` |
| 🔴 | `e206cb06e` | 2026-04-13 | Cross Back↔Front | Compliance / LGPD / EU AI Act | feat(studio): P2.3 — Compliance Dashboard — Backend: GET /custom-agents/studio/compliance-summary | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/custom-agents/studio-compliance-summary/route.ts`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/StudioComplianceView.tsx` |
| 🔴 | `81d3e2e2f` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.2 — Version History for Custom Agents — Every PATCH to a custom agent now creates an automatic snapshot of the | `lia-agent-system/alembic/versions/073_agent_version_snapshots.py`<br>`lia-agent-system/app/api/v1/custom_agents.py`<br>`lia-agent-system/app/models/agent_version_snapshot.py`<br>`lia-agent-system/app/services/agent_version_service.py`<br>`lia-agent-system/libs/models/lia_models/agent_version_snapshot.py` |
| 🟡 | `5cc3cfcbd` | 2026-04-13 | Cross IA↔Back | scope: studio | feat(studio): RAG search + RESTRICTED tools audit — - Add rag_search ToolDefinition to AUTONOMOUS_TOOL_POOL | `lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |
| 🔴 | `4c2373bbf` | 2026-04-13 | Cross IA↔Back | scope: intents | feat(intents): F5 - single source of intents in YAML + shared matcher [LIA-I01-I08] — - LIA-I01: KeywordIntentMatcher shared service (158 lines) with from_yaml | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py`<br>`lia-agent-system/app/domains/automation/domain.py`<br>`lia-agent-system/app/domains/communication/domain.py` |
| 🟡 | `71e8d28c5` | 2026-04-13 | Cross IA↔Back | scope: agentic | feat(agentic): F4 - real agentic loop, LLM thinks before acting [LIA-A01-A04] — - LIA-A01: LLM interprets action results in Phase 0 AND Phase 1 before | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/orchestrator/agentic_loop.py` |
| 🔴 | `3c940d5e8` | 2026-04-13 | Cross Back↔Front | Wizard/Onda 4 | feat(studio): Onda 4 — Studio <-> Chat Bridge — Enable Studio agent interaction via chat (create/query/metrics). | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/custom-agents/search/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/custom-agents/studio-metrics-summary/route.ts`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentChatCard.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentCreationPreview.tsx` |
| 🔴 | `93bfd694d` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.1 — Approval Workflow — Flow: draft → request → pending_approval → review → approved (active) / rejected (draft) | `lia-agent-system/alembic/versions/072_agent_approvals.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_approvals.py`<br>`lia-agent-system/app/models/agent_approval.py`<br>`lia-agent-system/app/services/agent_approval_service.py` |
| 🔴 | `0b6f0fdc1` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): Complete remaining Sprint 3-5 + P2 items — Sprint 3: ToolSelector checkbox grid (replaces text input for tools) | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/components/pages-agent-studio/MarketplaceTab.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentDetailsPanel.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/ContextLevelSelect.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/ToolSelector.tsx` |
| 🔴 | `b4ef2443c` | 2026-04-13 | Cross Back↔Front | Wizard/Onda 2 | feat(studio): Onda 2 — Conversational Creation + Test Debug Panel — Backend: POST /custom-agents/generate-from-description | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/custom-agents/generate/route.ts`<br>`plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/ConversationalCreator.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/TestDebugPanel.tsx` |
| 🔴 | `4d5a85fe9` | 2026-04-13 | Cross IA↔Front | FastAPI v1 endpoints | fix: cold-start resilience for Jobs, Candidates, and Tasks pages — Root cause: Next.js dev server takes 41+ seconds for initial compilation, | `lia-agent-system/app/api/v1/bias_audit.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py`<br>`lia-agent-system/app/api/v1/cultural_fit.py`<br>`lia-agent-system/app/api/v1/granular_consent.py`<br>`lia-agent-system/app/api/v1/ml_feedback.py` |
| 🔴 | `130cd6886` | 2026-04-12 | Cross IA↔Front | Backend Proxy Routes (FE) | Revert "Merge remote-tracking branch 'origin/develop-giovanni'" — This reverts commit c7c2c060ca2b8189a3ac6369a5f9eec474d9e0c8, reversing | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/search_assistant.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/orchestrator/task_planner.py`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/route.ts` |
| 🔴 | `d413ada7b` | 2026-04-12 | Cross IA↔Front | §14 BYOK + LLM Factory | fix: API routing, LLM Gemini fallback, auth token TTL and proxy fixes — - Add docker-compose.yml and docker-entrypoint.sh for GCP deploy | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/search_assistant.py`<br>`lia-agent-system/app/api/v1/sector_templates.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/orchestrator/task_planner.py` |
| 🔴 | `d26626cfd` | 2026-04-12 | Cross Back↔Front | §13 PARTE D — Foundation/Apify/Manifest | T005: Frontend - Remove Pro search mode, update costs for Apify enrichment — - Updated candidate-search.ts: searchType now "fast" only, calculateCreditsLocally | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py`<br>`lia-agent-system/app/api/v1/candidate_search/credits.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_models.py` |
| 🟡 | `b8523c8d1` | 2026-04-12 | Cross IA↔Back | §15 WSI | feat: Phase 1 — connect 4 isolated features to main pipeline — QW1: Recruiter Personalization → SystemPromptBuilder | `lia-agent-system/app/domains/cv_screening/services/lia_score_service.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/services/onboarding_orchestrator.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🔴 | `d82313fc8` | 2026-04-12 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Ensure database connections are properly reset to prevent RLS issues — Update database connection handling to always reset the role, preventing issues where aut | `lia-agent-system/alembic/versions/068_rls_deny_by_default.py`<br>`plataforma-lia/src/components/pages-talent-pools/TalentPoolPage.tsx` |
| 🟡 | `75188a458` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | fix: remove 5 hardcoded LIA fallbacks — persona via SystemPromptBuilder — - company_users.py: removed "Olá! Sou a LIA" hardcoded intro | `lia-agent-system/app/api/v1/company_users.py`<br>`lia-agent-system/app/api/v1/guardrails.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/shared/prompts/examples/sourcing_examples.py` |
| 🟡 | `3fc731723` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | refactor: isolate training persona from dynamic YAML flow — Training data is a versioned artifact — persona changes must be deliberate. | `lia-agent-system/app/domains/analytics/services/training_data_service.py`<br>`lia-agent-system/app/shared/prompts/training_persona.py` |
| 🟡 | `9588ecadb` | 2026-04-12 | Cross IA↔Back | Wizard (geral) | refactor: P1/P2 cleanup — remove 449 lines of dead code (AST-verified) — Dead code removed (10 functions, 0 callers each): | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_context_service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_orchestrator_service.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `4de5efb00` | 2026-04-12 | Cross IA↔Back | Task #167 | Task #167: Fix SQL injection vulnerabilities — defense-in-depth hardening — CRITICAL FIX (user/LLM-input interpolated in SQL): | `lia-agent-system/app/domains/job_management/services/wizard_step_service.py`<br>`lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `eb28a0727` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | refactor: complete prompt unification — eliminate all remaining hardcoded personas — Round 2: 32 patches across 29 files. | `lia-agent-system/app/api/v1/candidate_search/misc_search.py`<br>`lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/api/v1/lia_profile_analysis.py`<br>`lia-agent-system/app/domains/automation/services/stage_transition_automation.py` |
| 🟡 | `55ba81b35` | 2026-04-12 | Cross IA↔Back | Privacy / PII (W7) | feat: Item A Tipo C — audited Gemini native calls with PII strip + audit — - Add generate_native_gemini() async wrapper to LLMService | `lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py`<br>`lia-agent-system/app/domains/sourcing/services/vacancy_search.py`<br>`lia-agent-system/app/domains/voice/services/gemini_voice_service.py` |
| 🟡 | `b1ed88497` | 2026-04-12 | Cross IA↔Back | Privacy / PII (W7) | feat: Item A Tipo B — audited LangChain chain calls with PII strip + audit — - Create PIIStripCallback: strips PII from messages before LLM call | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/analytics/services/candidate_report_service.py`<br>`lia-agent-system/app/domains/candidates/services/candidate_comparison_service.py`<br>`lia-agent-system/app/domains/voice/services/voice_screening_analysis.py` |
| 🟡 | `8173145f8` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | fix: M2 memory — session handling + in-memory response + ATS import — - Fix ATS_INTEGRATION_DOMAIN_SPECIFIC missing import | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `1fb338d94` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | feat: M2 pick-one-writer — MainOrchestrator owns persistence (retry) — Key difference from previous attempt: instead of in-memory proxy, | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `7d59056ee` | 2026-04-12 | Cross IA↔Back | §15 WSI | fix: Item 3 — route WSI through safe_invoke + mark LLM tech debt — Tipo A (6 WSI calls): FIXED — routed through llm_service.safe_invoke() | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/domains/analytics/services/candidate_report_service.py`<br>`lia-agent-system/app/domains/candidates/services/candidate_comparison_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py` |
| 🟡 | `18e94da13` | 2026-04-12 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: separate talent prompt + add ReAct instructions to SystemPromptBuilder (Commit 1) — SystemPromptBuilder changes: | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `635e1f4ae` | 2026-04-12 | Cross IA↔Back | §15 WSI | Task #162: Interview Intelligence Pro — Security + 7-Block WSI + Multi-Cohort Comparative — Code review fixes applied: | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/comparative_analysis_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/feedback_generator_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py` |
| 🟡 | `feafa932a` | 2026-04-12 | Cross IA↔Back | §15 WSI | Task #162: Interview Intelligence Pro — WSI + Viés + Parecer + Feedback — Implemented 5 new services in interview_intelligence domain: | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/comparative_analysis_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/feedback_generator_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py` |
| 🟡 | `36d1c24f3` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | revert: M2 skip_memory_persist — session sharing needs architectural decision — Reverted skip_memory_persist to True and restored ChatRepository writes | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/domains/interview_scheduling/repositories/interview_repository.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🔴 | `7a1af0f32` | 2026-04-12 | Cross IA↔Front | Wizard (geral) | feat: LIA Intelligence Overhaul — refactor prompt architecture for contextual responses — - Rewrote lia_persona.yaml as comprehensive SSOT (~200 lines): identit | `lia-agent-system/app/api/v1/lia_assistant/conversational.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `3e6a0ab12` | 2026-04-12 | Cross IA↔Back | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/tasting_engine.py` |
| 🔴 | `b945f3bb7` | 2026-04-12 | Cross IA↔Front | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/tasting_engine.py`<br>`plataforma-lia/src/components/unified-chat/TastingInsightCard.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🔴 | `b1e40d0ce` | 2026-04-12 | Cross IA↔Front | §2 Orchestrator Migration | Improve how the system understands user requests and avoid unnecessary page changes — Adjust the confidence threshold for navigation intent detection and modify | `lia-agent-system/app/orchestrator/navigation_intent.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `9bd173c0f` | 2026-04-12 | Cross IA↔Back | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Fail-closed module gating for all premium tools: | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `9013ced8a` | 2026-04-12 | Cross IA↔Back | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating infrastructure for premium tools: | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `364b8bf9c` | 2026-04-11 | Cross IA↔Back | Task #153 | Task #153 final fixes: Wire per-request cost tracking end-to-end — 1. LLMCascade: Wire request_id through all route() call paths (preferred, | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `bb344d222` | 2026-04-11 | Cross IA↔Back | Task #153 | Task #153: Guardrails Per-Request + RAG Semantic Chunking — Per-request cost tracking: | `lia-agent-system/alembic/versions/065_add_request_id_cost_to_audit_metadata.py`<br>`lia-agent-system/app/orchestrator/tenant_budget.py` |
| 🟡 | `e93d57b77` | 2026-04-11 | Cross IA↔Back | Task #145 | Task #145: Align LIA prompts with actual tool capabilities — Fixed prompt-tool mismatches across 6 prompt files: | `lia-agent-system/app/shared/prompts/job_wizard.py`<br>`lia-agent-system/app/tools/scope_config.py` |
| 🟡 | `c9f1bfc2c` | 2026-04-11 | Cross IA↔Back | scope: #147 | feat(#147): Loop Autônomo e Inteligência Proativa — Implements proactive intelligence for LIA recruitment assistant: | `lia-agent-system/app/domains/recruiter_assistant/domain.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/autonomous_actions_engine.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/monitoring_loop.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/outcome_learning_service.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/stakeholder_notification_service.py` |
| 🟡 | `164c34fe4` | 2026-04-11 | Cross IA↔Back | Task #146 | Task #146: Implement Competitive Talent Intelligence Tools — New domain: lia-agent-system/app/domains/talent_intelligence/ | `lia-agent-system/app/domains/talent_intelligence/services/__init__.py`<br>`lia-agent-system/app/domains/talent_intelligence/services/skills_ontology_engine.py`<br>`lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `7574d67e1` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — domain services as source of truth — Domain services migration (app/services/ → app/domains/*/services/): | `lia-agent-system/app/services/ats_clients/__init__.py`<br>`lia-agent-system/app/services/ats_clients/ats_pii_filter.py`<br>`lia-agent-system/app/services/ats_clients/base.py`<br>`lia-agent-system/app/services/ats_clients/gupy.py`<br>`lia-agent-system/app/services/ats_clients/lgpd_field_registry.py` |
| 🔴 | `db08579cd` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — domain services as source of truth — Domain services migration (app/services/ → app/domains/*/services/): | `lia-agent-system/app/api/v1/admin_token_budget.py`<br>`lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/ats.py` |
| 🟡 | `85af8700b` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — single source of truth — Shim elimination: | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/rag_search.py`<br>`lia-agent-system/app/domains/ai/services/rag_pipeline_service.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/__init__.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/base.py` |
| 🔴 | `ef3114c66` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — single source of truth — - Eliminated 129 forward/backward shim files from app/services/ | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/admin_lgpd.py`<br>`lia-agent-system/app/api/v1/admin_prompts.py`<br>`lia-agent-system/app/api/v1/affirmative.py`<br>`lia-agent-system/app/api/v1/ai_consumption.py` |
| 🔴 | `85d0aaf9d` | 2026-04-11 | Cross Back↔Front | Task #156 | Task #156: Corrigir Agent Studio — Agentes Funcionais E2E — Changes across 5 files to fix broken Agent Studio experience: | `lia-agent-system/app/api/v1/sourcing_agents.py`<br>`lia-agent-system/app/services/sourcing_agent_orchestrator.py`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/CalibrationCardModal.tsx` |
| 🟡 | `c1f858b17` | 2026-04-11 | Cross IA↔Back | Task #149 | Task #149: Orchestrator Cleanup — Remove dead IntentRouter code — Changes: | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/intent_router.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `b82c8f73f` | 2026-04-11 | Cross Back↔Front | Hooks (FE) | Refactor hooks into domain-specific folders and generate API types — Reorganize all frontend hooks into 9 domain-specific folders, update hundreds of imports, a | `lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/analyze-match-all/sedwHxr6L`<br>`plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` |
| 🟡 | `ad7e897a3` | 2026-04-11 | Cross IA↔Back | Triagem (módulo) | Implement real start_screening handler + fix code quality issues — T001: Replaced stub _start_screening handler in candidate_actions.py with | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `0bfffe539` | 2026-04-11 | Cross Back↔Front | Task #141 | Pipeline: UX Cards + Data Audit + Icons/Stages (Task #141) — 1. seed_service.py: Canonical stage keys (sourcing, screening, interview_hr, | `lia-agent-system/app/shared/services/seed_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/kanban/components/CandidateCard.tsx`<br>`plataforma-lia/src/components/kanban/types.ts`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardActions.tsx` |
| 🔴 | `b4891f266` | 2026-04-11 | Cross IA↔Front | Performance | Task #138: Performance, Prompt Versioning & Rails Integration Readiness — All 6 subtasks completed with code review fixes applied: | `lia-agent-system/app/main.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx`<br>`plataforma-lia/src/components/autonomous/jobs-dashboard.tsx`<br>`plataforma-lia/src/components/autonomous/proactive-actions.tsx` |
| 🔴 | `4ca637641` | 2026-04-11 | Cross IA↔Front | Kanban (vagas) | Visual components: 12 categories fixed - shadows, borders, table headers, dots, rounded, empty states (16 files) | `lia-agent-system/app/api/v1/rails_health.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/main.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/activity-feed.tsx` |
| 🔴 | `39252ae74` | 2026-04-11 | Cross IA↔Front | Chat UI (FE) | DS final: remaining chat bubble and handler hooks | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`plataforma-lia/src/components/chat/chat-bubble-base.tsx`<br>`plataforma-lia/src/components/chat/message-bubble.tsx` |
| 🔴 | `a737c0267` | 2026-04-11 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Task #137: P1 Compliance & Governance — FairnessGuard, AI Disclosure, SOX — All 6 task items implemented: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/compliance_status.py`<br>`lia-agent-system/app/api/v1/recruitment_campaigns.py`<br>`lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/shared/compliance/fairness_guard.py` |
| 🔴 | `8690b05d0` | 2026-04-11 | Cross IA↔Front | Task #139 | Task #139: Redesign TopBar — Avatar e Notificações na Sidebar — Moved recruiter avatar, notification bell, and HITL pending badge from | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py`<br>`plataforma-lia/src/app/globals.css` |
| 🔴 | `efa142c5b` | 2026-04-11 | Cross IA↔Front | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | `lia-agent-system/app/orchestrator/action_handlers/communication_actions.py`<br>`plataforma-lia/src/app/shared/[token]/_components/SharedContent.tsx`<br>`plataforma-lia/src/components/ai/agent-explainability-panel.tsx`<br>`plataforma-lia/src/components/alerts/alert-settings-modal.tsx`<br>`plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` |
| 🔴 | `98109faad` | 2026-04-11 | Cross Back↔Front | Frontend (componentes diversos) | DS Final Phase 1-2: root fixes + typography standardization (235 files) | `lia-agent-system/app/domains/communication/services/email_service.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_service.py`<br>`plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/access/AccessClient.tsx`<br>`plataforma-lia/src/app/ajuda/AjudaClient.tsx` |
| 🟡 | `5bebbdc3e` | 2026-04-11 | Cross IA↔Back | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | `lia-agent-system/app/domains/communication/services/email_service.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `58417c7d3` | 2026-04-11 | Cross IA↔Back | §2 Orchestrator Migration | Update job handling and logging to improve system reliability — Refactor action handler hooks to adjust audit logging level from debug to warning, update Rails  | `lia-agent-system/alembic/versions/063_create_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py` |
| 🟡 | `7a2ef320f` | 2026-04-11 | Cross IA↔Back | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`<br>`lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py` |
| 🟡 | `82605c5b8` | 2026-04-11 | Cross IA↔Back | Task #135 | Task #135: Action Handlers → Real DB Operations + Fix PL-002 — Changes: | `lia-agent-system/alembic/versions/063_create_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/interview_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🔴 | `6af3cf400` | 2026-04-11 | Cross Back↔Front | scope: agent-studio | feat(agent-studio): Implement Fase 4 — Agent Studio & Custom Agent Marketplace — Task #130: Full custom agent system with CRUD, runtime sandbox, marketplace, an | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/custom_agents.py`<br>`lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/models/custom_agent.py`<br>`lia-agent-system/app/services/agent_marketplace_service.py` |
| 🟡 | `3a42a1dd8` | 2026-04-11 | Cross IA↔Back | Fase 3 | Task #129: Fase 3 — Guardrail de Custo por Request Individual — Per-request token budget ceiling prevents individual LLM calls from | `lia-agent-system/app/main.py`<br>`lia-agent-system/app/services/token_budget_service.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🟡 | `1cf273c6a` | 2026-04-11 | Cross IA↔Back | Task #124 | feat(task-124): Activate A/B testing of prompts in production — - Created experiment YAML configs for CascadeRouter system prompt | `lia-agent-system/alembic/versions/062_add_prompt_version_to_messages.py`<br>`lia-agent-system/app/api/v1/ab_testing.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟡 | `6ca941e60` | 2026-04-11 | Cross IA↔Back | Task #121 | Task #121: Expand OpenTelemetry instrumentation (Full Coverage) — - CascadedRouter: All 7 tiers + fallback with tier_name, confidence_score, | `lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/services/hitl_service.py`<br>`lia-agent-system/app/services/rag_pipeline_service.py` |
| 🔴 | `71095fbac` | 2026-04-11 | Cross IA↔Front | Fase 2 | Fase 2 — HITL Badge de Aprovações Pendentes no Header (Task #125) — Backend: | `lia-agent-system/app/api/v1/hitl.py`<br>`lia-agent-system/app/services/hitl_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/hitl/pending/route.ts`<br>`plataforma-lia/src/components/hitl-pending-badge.tsx`<br>`plataforma-lia/src/components/top-bar.tsx` |
| 🔴 | `b68483941` | 2026-04-11 | Cross Back↔Front | scope: #128 | feat(#128): SSE Fallback for Chat Streaming (Fase 3) — Backend: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/unified-chat/TransportModeIndicator.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🔴 | `81e989874` | 2026-04-11 | Cross Back↔Front | Fase 1 | Fase 1 — Cost Dashboard Granular por Agente + Alertas (Task #123) — Backend changes (lia-agent-system): | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/domains/ai/repositories/ai_consumption_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/ai-credits/route.ts`<br>`plataforma-lia/src/components/pages/ai-credits-page.tsx` |
| 🔴 | `b687d930e` | 2026-04-10 | Cross IA↔Front | §14 BYOK + LLM Factory | Task #119: Voice Abstraction in LLM Factory + Streaming Frontend — Created VoiceStreamProviderABC abstraction layer in the LLM Factory with | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/voice_stream.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py`<br>`plataforma-lia/src/app/api/backend-proxy/voice-stream/start-session/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/voice-stream/status/route.ts` |
| 🔴 | `f86387396` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — CI/CD workflows for both repositories + infrastructure docs: | `lia-agent-system/.github/workflows/deploy.yml`<br>`lia-agent-system/Dockerfile.worker`<br>`lia-agent-system/scripts/worker_health.py`<br>`plataforma-lia/.github/workflows/deploy.yml` |
| 🔴 | `e1bd7d78e` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastructure documentation: | `lia-agent-system/.github/workflows/deploy.yml`<br>`plataforma-lia/.github/workflows/deploy.yml` |
| 🔴 | `dde1d6f0d` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastructure documentation: | `plataforma-lia/src/components/candidate-preview/PipelineDecisionBar.tsx` |
| 🔴 | `6f75253d7` | 2026-04-10 | Cross Back↔Front | Task #113 | Task #113: Backend Production Hardening — Deploy Blockers — Changes made: | `lia-agent-system/alembic/versions/027_add_langgraph_native_checkpointer_tables.py`<br>`lia-agent-system/alembic/versions/033_merge_migration_heads.py`<br>`lia-agent-system/alembic/versions/058_create_tenant_llm_configs.py`<br>`lia-agent-system/alembic/versions/059_migrate_legacy_company_ids.py`<br>`lia-agent-system/app/api/v1/shared_searches.py` |
| 🔴 | `9f42c9782` | 2026-04-10 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Improve agent studio functionality and fix backend route issues — This commit addresses multiple bugs by refactoring backend proxy routes, enhancing UI componen | `lia-agent-system/app/api/v1/sector_templates.py`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/[...path]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing/multi-strategy/route.ts`<br>`plataforma-lia/src/components/dashboard-app.tsx` |
| 🔴 | `bbe4db71b` | 2026-04-10 | Cross Back↔Front | scope: onboarding-lia | feat(onboarding-lia): complete conversational onboarding system — Onboarding LIA — UAU experience for new recruiters. | `lia-agent-system/alembic/versions/059_create_onboarding_tables.py`<br>`lia-agent-system/app/api/v1/onboarding.py`<br>`lia-agent-system/app/api/v1/whatsapp_webhook.py`<br>`lia-agent-system/app/services/onboarding_consumer.py`<br>`lia-agent-system/app/services/onboarding_orchestrator.py` |
| 🔴 | `07422c531` | 2026-04-10 | Cross IA↔Front | Configurações (hub) | Fix task display and improve security for search settings — Address an issue where the task list was not displaying correctly by removing a frontend user ID fil | `plataforma-lia/src/app/api/backend-proxy/company/global-search-settings/route.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts`<br>`unified-chat-build/wizard/panels/._WsiQuestionsPanel.tsx` |
| 🔴 | `e02734183` | 2026-04-10 | Cross Back↔Front | Backend Services (BE) | Update user profile and authentication features — Introduces profile editing, password change functionality, and lazy loading for the job creation dom | `plataforma-lia/src/components/top-bar.tsx`<br>`plataforma-lia/src/contexts/auth-context.tsx` |
| 🔴 | `c5408615e` | 2026-04-10 | Cross Back↔Front | §15 WSI | feat(wizard-wsi): complete Phase B+C+D — Wizard WSI conversational job creation — Backend (13 Python files, 3607 lines): | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/auth/schemas.py`<br>`plataforma-lia/src/app/api/backend-proxy/auth/[...slug]/route.ts`<br>`plataforma-lia/src/components/modals/profile-modal.tsx` |
| 🔴 | `9bb5b231a` | 2026-04-10 | Cross IA↔Front | Voice / ElevenLabs / STT | Improve chat functionality by using browser's speech recognition and fixing icon clipping — Integrates Web Speech API for real-time voice transcription in the c | `lia-agent-system/app/domains/job_creation/domain.py`<br>`lia-agent-system/app/domains/job_creation/services/__init__.py`<br>`lia-agent-system/app/domains/job_creation/services/file_router.py`<br>`lia-agent-system/app/domains/job_creation/services/jd_enrichment.py`<br>`lia-agent-system/app/domains/job_creation/services/seniority_resolver.py` |
| 🔴 | `a6514672b` | 2026-04-10 | Cross Back↔Front | Task #102 | Task #102: Pipeline Overview — Centro de Comando do Recrutador — Backend changes: | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🔴 | `1bb42a5b7` | 2026-04-10 | Cross Back↔Front | §1 Teams Integration | fix(production-readiness): Teams URL default + replace all silent catch handlers — ## Task #98 — Production Readiness: Silent Catches + Teams URL | `lia-agent-system/app/api/v1/teams.py`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCalibrationAndFastTrackHandlers.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useConversationMemory.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useConversationMemoryInit.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useSendMessageAPIDispatchers.ts` |
| 🔴 | `3cad3eb72` | 2026-04-10 | Cross Back↔Front | FastAPI v1 endpoints | Add real-time candidate counts to recruitment pipeline stages — Adds a new backend endpoint and frontend integration to display real-time candidate counts for e | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🔴 | `7f658ccb0` | 2026-04-10 | Cross IA↔Front | Sprint 4 | feat: Sprint 4 — Agent Studio conversational creation via chat — Backend: | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`plataforma-lia/src/components/unified-chat/NavigationHintCard.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🔴 | `05d5c8ff4` | 2026-04-09 | Cross Back↔Front | Backend (genérico) | feat(backend): Sprint 3 — PATCH /conversations/{id} for rename + wire to UnifiedChat — - Added RenameConversationRequest schema to conversations.py | `lia-agent-system/app/api/v1/conversations.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `2ce967310` | 2026-04-09 | Cross IA↔Back | FastAPI v1 endpoints | Fix issues with talent pool data handling and permissions — Correct account ID type casting and update LLM provider configurations in tool permissions. | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/api/v1/talent_pools.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml` |
| 🔴 | `1c0fc21b6` | 2026-04-09 | Cross IA↔Front | §9 Security / Tenant guards | Task #94: Choose Your AI — LLM Config Integration (Wiring + Security + Frontend) — Full end-to-end integration of per-tenant LLM provider configuration. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/repositories/llm_config_repository.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🔴 | `ed0c6a466` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Add secure management for AI model API keys and providers — Integrate AI model provider management with API key encryption, masking, and removal functionality. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/repositories/llm_config_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/llm-config/providers/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/llm-config/route.ts` |
| 🔴 | `65122342a` | 2026-04-09 | Cross IA↔Front | §14 BYOK + LLM Factory | feat: complete LLM Factory migration — zero direct SDK imports outside providers/ — ## Summary | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/email_templates.py`<br>`lia-agent-system/app/api/v1/experience_highlights.py` |
| 🔴 | `0bd4eb8e5` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Migrate all frontend API routes to use FastAPI and improve categories endpoint — Update backend target for numerous API routes from "rails" to "fastapi", and op | `lia-agent-system/app/api/v1/email_templates.py`<br>`lia-agent-system/app/domains/email_templates/repositories/email_templates_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/activities/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/approve/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/cancel/route.ts` |
| 🔴 | `ec389f991` | 2026-04-09 | Cross Back↔Front | Task #87 | fix: Task #87 code-review corrections — remove `as any`, prefer draft conversation_id — ## Issues fixed (blocking code review approval) | `lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant/conversational.py`<br>`plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ExpandedChatInput.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatCallbacks.ts` |
| 🔴 | `a935f1f69` | 2026-04-09 | Cross Back↔Front | §6 Chat Unificado / Funil | fix: resolve Funil de Talentos hydration mismatch causing infinite loading state — Root cause: Radix UI <Tabs> generates SSR/client baseId mismatches during | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/auth/schemas.py`<br>`plataforma-lia/src/app/api/auth/auto-login/route.ts`<br>`plataforma-lia/src/app/api/auth/session/refresh/route.ts` |
| 🔴 | `7d4b383ad` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | fix: resolve pipeline overview SQL type mismatch and add proxy error handling — - Fixed `character varying = uuid` SQL error in job_vacancies_analytics_reposito | `lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/digital-twins/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/talent-pools/route.ts` |
| 🔴 | `1a65de885` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Fix issues preventing the Agent Studio page from loading correctly — Address backend startup issues, correct proxy route configurations, and improve frontend er | `lia-agent-system/app/api/v1/sourcing_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/agent-templates/sectors/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/route.ts`<br>`plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx` |
| 🔴 | `6259655b3` | 2026-04-08 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Improve agent studio page loading by handling API errors gracefully — Fix TypeError in AgentStudioPage.tsx by adding Array.isArray() check for templatesData to  | `lia-agent-system/app/api/v1/auth.py`<br>`plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx` |
| 🔴 | `b6cfd672d` | 2026-04-08 | Cross Back↔Front | scope: #81 | feat(#81): Sidebar sections + Pipeline Overview page (v4 final) — ## Summary | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🔴 | `76e081686` | 2026-04-08 | Cross Back↔Front | §4 Rail Features — Rail A | Update application styling and fix component rendering issues — Standardize typography and fix server component rendering errors by introducing a client-side wr | `lia-agent-system/alembic/versions/055_create_talent_pools.py`<br>`lia-agent-system/alembic/versions/056_create_sourcing_agents.py`<br>`lia-agent-system/alembic/versions/057_create_recruitment_campaigns.py`<br>`lia-agent-system/alembic/versions/058_create_digital_twins.py`<br>`lia-agent-system/app/api/routes.py` |
| 🟡 | `b3a685d50` | 2026-04-08 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: Phase 8.1+8.2 — 4 new domains + 22 tools + Pearch hybrid + router update — 8.1 — Orchestrator Integration (4 new domains): | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/digital_twin/domain.py`<br>`lia-agent-system/app/domains/recruitment_campaign/domain.py`<br>`lia-agent-system/app/domains/talent_pool/domain.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🔴 | `ea09abcc3` | 2026-04-08 | Cross Back↔Front | Task #78 | feat: safe URL encoding for Microsoft OAuth auth URL + adapter interface fix — Final polish for Task #78 external integrations code review: | `lia-agent-system/app/api/v1/calendar.py`<br>`lia-agent-system/app/api/v1/integrations.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/api/v1/whatsapp.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_meta_service.py` |
| 🔴 | `2003c41d5` | 2026-04-08 | Cross Back↔Front | Kanban (vagas) | feat(task-77): A/B Testing UI, Kanban suggestions API, chat suggestions, credit balance fix — ## Task | `lia-agent-system/app/api/v1/kanban_assistant.py`<br>`plataforma-lia/src/app/api/backend-proxy/ab-tests/[testName]/record/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ab-tests/[testName]/results/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ab-tests/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/lia/kanban-assistant/stage-move-suggestions/route.ts` |
| 🔴 | `0fbb45e92` | 2026-04-08 | Cross Back↔Front | §15 WSI | fix: Phase 7 hardening — all 17 audit issues resolved — CRITICAL FastAPI fixes: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/services/multi_strategy_search.py`<br>`lia-agent-system/app/services/sourcing_agent_orchestrator.py`<br>`lia-agent-system/app/services/voice_interview_state_machine.py`<br>`plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx` |
| 🔴 | `cd704ed67` | 2026-04-08 | Cross Back↔Front | FastAPI v1 endpoints | fix: resolve all implementation gaps from code review — Models: | `lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/sector_templates.py`<br>`lia-agent-system/app/api/v1/sourcing_agents.py`<br>`lia-agent-system/app/models/digital_twin.py`<br>`lia-agent-system/app/models/sourcing_agent.py` |
| 🔴 | `c253385e1` | 2026-04-08 | Cross Back↔Front | Candidates (FE pages) | Improve candidate search functionality by splitting multi-word queries — Fixes candidate search to correctly handle multi-word queries by splitting them into to | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/useCandidatesExecuteSearch.ts` |
| 🔴 | `9ce15b138` | 2026-04-08 | Cross Back↔Front | §9 Security / Tenant guards | fix(backend): Task #75 — Backend Deploy Readiness (OpenAPI, Shims, Secrets, Celery, Security) — ## Summary | `lia-agent-system/app/main.py`<br>`lia-agent-system/libs/models/lia_models/intelligent_cache.py`<br>`plataforma-lia/src/app/layout.tsx` |
| 🔴 | `714711e5c` | 2026-04-08 | Cross Back↔Front | §7 WorkflowRail UX | feat: integrate Phase 6 — auth, sidebar, pages, WorkflowRail — Item 1 — Auth: | `lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/multi_strategy_search.py`<br>`lia-agent-system/app/api/v1/sector_templates.py`<br>`lia-agent-system/app/api/v1/sourcing_agents.py`<br>`lia-agent-system/app/api/v1/voice_screening.py` |
| 🔴 | `4b4f44771` | 2026-04-08 | Cross Back↔Front | §9 Security / Tenant guards | Improve security and user management by isolating tenant data — Enhance multi-tenancy by isolating user data by tenant, preventing cross-tenant access and ensur | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/api/v1/company_users.py`<br>`lia-agent-system/app/domains/company/repositories/company_profile_repository.py`<br>`plataforma-lia/src/components/settings/use-user-management.ts` |
| 🔴 | `2e0c4c9d1` | 2026-04-08 | Cross IA↔Front | §7 WorkflowRail UX | feat: Phase 6 — Agent Studio, Talent Pools, Workflow Rail, Digital Twins — 57 new files across lia-agent-system (FastAPI) and plataforma-lia (Frontend): | `lia-agent-system/alembic/versions/055_create_talent_pools.py`<br>`lia-agent-system/alembic/versions/056_create_sourcing_agents.py`<br>`lia-agent-system/alembic/versions/057_create_recruitment_campaigns.py`<br>`lia-agent-system/alembic/versions/058_create_digital_twins.py`<br>`lia-agent-system/app/api/v1/digital_twins.py` |
| 🔴 | `7634b0b4b` | 2026-04-08 | Cross Back↔Front | Configurações (hub) | Add fairness and compliance dashboard to settings and improve dev mode authentication — Integrate the new Fairness Compliance Hub into the settings page, add a  | `lia-agent-system/app/auth/rails_jwt.py`<br>`plataforma-lia/src/app/api/backend-proxy/activities/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/approve/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/cancel/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/reject/route.ts` |
| 🟡 | `053b7d0b5` | 2026-04-08 | Cross IA↔Back | §9 Security / Tenant guards | Fix issues with job vacancy display and improve input security — Updates response schemas for job vacancies to correctly handle complex data types, implements m | `lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/shared/compliance/prompt_injection_guard.py` |
| 🔴 | `e27f8342e` | 2026-04-08 | Cross Back↔Front | Chat UI (FE) | Add filtering and sorting to candidate list and fix total count — Update backend API to support seniority, sort by, and sort order filters for candidates. Modif | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py`<br>`plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/chat-bubble-base.tsx` |
| 🔴 | `287ba5ad5` | 2026-04-08 | Cross IA↔Front | Kanban (vagas) | Improve authentication, error handling, and user experience — Update authentication flow to correctly set cookies, refine error handling for various components, | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/data_subject_requests.py`<br>`lia-agent-system/app/api/v1/health_langgraph.py`<br>`lia-agent-system/app/api/v1/jd_import.py`<br>`lia-agent-system/app/api/v1/recruitment_stages/stages_crud.py` |
| 🟡 | `0e523f63a` | 2026-04-07 | Cross IA↔Back | scope: tests | fix(tests): fix Redis isolation, agent_health tests, shim exports, lia_config import — - Fix _make_service() in test_agent_health_alert_service to patch _get_re | `lia-agent-system/app/api/v1/automation/event_handlers/__init__.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_ats_sync.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_interview.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_lifecycle.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py` |
| 🔴 | `0427d7f0e` | 2026-04-07 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Add new components and update job vacancy analytics functionality — Adds new mockup components and updates job vacancy analytics by importing `get_user_company_ | `lia-agent-system/app/api/v1/job_vacancies/__init__.py` |
| 🔴 | `1dddecde9` | 2026-04-07 | Cross Back↔Front | §15 WSI | Add detailed report view for WSI assessments and improve candidate resolution — Refactor candidate resolution logic and introduce a new detailed report componen | `lia-agent-system/app/api/v1/candidates/_shared.py`<br>`lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/api/v1/candidates/candidates_search.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/recruitment_stages/__init__.py` |
| 🔴 | `220094926` | 2026-04-07 | Cross Back↔Front | Backend Proxy Routes (FE) | Standardize backend URLs and fix critical deployment issues — Correctly configure backend URLs across the application, replacing hardcoded ports and ensuring co | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/api/v1/platform_event_handlers.py`<br>`lia-agent-system/app/api/v1/short_lists.py` |
| 🟡 | `3b060add7` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update code to use dependency injection for service classes — Refactor multiple API endpoints to utilize dependency injection for service classes, improving cod | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/api/v1/external_webhooks.py`<br>`lia-agent-system/app/api/v1/finetuning_export.py` |
| 🔴 | `ca4d6f656` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Refactor service imports and move WebSocket manager — Update service imports to use dependency injection and move the WebSocket manager to a shared locati | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py`<br>`lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/data_subject_requests.py` |
| 🟡 | `edff3aee3` | 2026-04-07 | Cross IA↔Back | scope: tests | fix(tests): fix Redis mock injection in token_budget, toon, and hitl services — - Promote app/services/token_budget_service.py, toon_service.py, and hitl_servic | `lia-agent-system/app/domains/credits/services/token_budget_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/hitl_service.py`<br>`lia-agent-system/app/services/hitl_service.py`<br>`lia-agent-system/app/services/token_budget_service.py`<br>`lia-agent-system/app/services/toon_service.py` |
| 🔴 | `49d6b02a1` | 2026-04-07 | Cross IA↔Front | DevOps / Deploy (Docker/GCP) | Update application configuration and Dockerfile for standalone deployment — Refactors several Python files to use repository patterns, updates Next.js configura | `lia-agent-system/app/api/v1/benefits.py`<br>`lia-agent-system/app/api/v1/calendar.py`<br>`lia-agent-system/app/api/v1/data_request.py`<br>`lia-agent-system/app/api/v1/digest.py`<br>`lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `113d065f2` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Refactor data access layers to improve code organization and maintainability — Extract various data access logic into dedicated repository classes, improving se | `lia-agent-system/app/api/v1/communication_optout.py`<br>`lia-agent-system/app/api/v1/communication_settings.py`<br>`lia-agent-system/app/api/v1/company_retention.py`<br>`lia-agent-system/app/api/v1/cv_parser.py`<br>`lia-agent-system/app/domains/communication/repositories/teams_repository.py` |
| 🟡 | `92e64405f` | 2026-04-07 | Cross IA↔Back | §15 WSI | refactor(phase2): extract wsi/cv_screening/comms API DB calls to repos — - WsiRepository: +7 methods (get_question_text_and_competency, insert_response_analysis | `lia-agent-system/app/api/v1/alerts.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py`<br>`lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/api/v1/guardrails.py`<br>`lia-agent-system/app/api/v1/learning_outcomes.py` |
| 🔴 | `5b9c855ca` | 2026-04-07 | Cross IA↔Back | scope: phase2 | refactor(phase2): extract API direct DB calls to repositories — batch 1 — Fully extracted (DB calls replaced with repo methods): | `lia-agent-system/app/api/v1/admin_compliance_fairness.py`<br>`lia-agent-system/app/api/v1/admin_templates.py`<br>`lia-agent-system/app/api/v1/agent_quality.py`<br>`lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/alerts.py` |
| 🟡 | `1445b1707` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update system to handle Rails-deprecated entities and fix import issues — Introduces a RailsAdapter for deprecated entities, adds comments to relevant API endpo | `lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py` |
| 🔴 | `81889e02a` | 2026-04-07 | Cross IA↔Back | scope: phase4b | feat(phase4b): batch 2 — migrate 73 AI-permanent services to domain layer — Migrated services (73 total across 7 domains): | `lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/rubric_evaluation.py`<br>`lia-agent-system/app/domains/ai/services/context_aggregator_service.py`<br>`lia-agent-system/app/domains/ai/services/domain_embedding_service.py`<br>`lia-agent-system/app/domains/ai/services/embedding_cache_service.py` |
| 🟡 | `bf6970eff` | 2026-04-07 | Cross IA↔Back | scope: phase2 | fix(phase2): classify API files as Rails-owned vs FastAPI-owned — - Annotated 2 API files as RAILS-DEPRECATED (wsi/reports.py, saturation.py) | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/rubric_evaluation.py`<br>`lia-agent-system/app/api/v1/saturation.py` |
| 🔴 | `4adf6561f` | 2026-04-07 | Cross IA↔Back | scope: phase3 | fix(phase3): replace app.models imports with lia_models in service files — - Case A: 128 files changed from app.models.X to lia_models.X where lia_models equiva | `lia-agent-system/app/domains/ai/services/agent_quality_evaluator.py`<br>`lia-agent-system/app/domains/ai/services/enhanced_intent_classifier.py`<br>`lia-agent-system/app/domains/ai/services/intent_classifier.py`<br>`lia-agent-system/app/domains/ai/services/jd_parser_service.py`<br>`lia-agent-system/app/domains/ai/services/model_drift_service.py` |
| 🟡 | `ba43cd5c7` | 2026-04-07 | Cross IA↔Back | scope: ddd | feat(ddd): Phase 4 DDD migration — credit_service and rails_adapter to domain layer — - Move credit_service.py to app/domains/credits/services/ (canonical) | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/credits.py`<br>`lia-agent-system/app/domains/credits/repositories/credits_repository.py`<br>`lia-agent-system/app/domains/credits/services/__init__.py` |
| 🟡 | `cf6d87bc0` | 2026-04-07 | Cross IA↔Back | §15 WSI | task-60: Prompts Unificados & Infra de Evals — ## Summary | `lia-agent-system/app/prompts/domains/wsi_evaluation.yaml`<br>`lia-agent-system/app/prompts/domains/wsi_interview.yaml`<br>`lia-agent-system/app/services/hitl_service.py`<br>`lia-agent-system/app/services/token_budget_service.py`<br>`lia-agent-system/app/shared/prompts/prompt_registry.py` |
| 🟡 | `561e99c47` | 2026-04-07 | Cross IA↔Back | Voice / ElevenLabs / STT | feat(voice): Go-Live Deepgram STT & OpenMic.ai — Task #65 — Implements full production-ready integration for Deepgram (STT/transcription) | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/openmic_webhook.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/domains/voice/services/voice_screening_orchestrator.py`<br>`lia-agent-system/app/main.py` |
| 🟡 | `91f187afa` | 2026-04-07 | Cross IA↔Back | scope: autonomous | feat(autonomous): finalize Tier 6 — all reviews addressed, 59 tests passing — Task #58 (AutonomousReActAgent — Tier 6) — final state: | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `bb3d4819d` | 2026-04-07 | Cross IA↔Back | scope: infra | feat(infra): Task #67 — Broker Abstraction Layer + Fix 15 Test Import Errors — ## Broker Abstraction (Items 1 & 2) | `lia-agent-system/app/api/v1/candidate_search/__init__.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/services/bias_audit_service.py`<br>`lia-agent-system/app/services/early_warning_service.py`<br>`lia-agent-system/app/services/hitl_service.py` |
| 🔴 | `d110a2a22` | 2026-04-07 | Cross IA↔Front | Automations | Update chat and automation services for improved functionality — Refactors service dependencies and WebSocket proxy configuration in the chat application. | `lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/automation/triggers.py`<br>`lia-agent-system/app/api/v1/automations.py` |
| 🟡 | `47c1a9ebd` | 2026-04-07 | Cross IA↔Back | §15 WSI | Update services to use dependency injection for feature flags and organization catalog — Refactor code to inject services for FeatureFlagService and Organizatio | `lia-agent-system/app/api/v1/lia_assistant_flags.py`<br>`lia-agent-system/app/api/v1/organization_catalog.py`<br>`lia-agent-system/app/api/v1/wsi/questions.py`<br>`lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/cv_screening/services/screening_question_set_service.py` |
| 🟡 | `f6c6a297b` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update audit service to use dependency injection for consistency — Refactor the audit service import and usage across multiple API endpoints to utilize dependen | `lia-agent-system/app/api/v1/communication.py`<br>`lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/api/v1/pipeline.py`<br>`lia-agent-system/app/api/v1/scheduling.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py` |
| 🟡 | `99906f8d2` | 2026-04-07 | Cross IA↔Back | §1 Teams Integration | Add dependency injection factories for service classes — Add FastAPI dependency injection factories to ActivityService and AuditService. Also updates the lia | `lia-agent-system/app/domains/analytics/services/activity_service.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🔴 | `9e60ef7f7` | 2026-04-07 | Cross Back↔Front | Configurações (hub) | Add new API endpoints for company-specific settings and data management — Introduces new API routes for managing company approvers, assessments, benefits, cultu | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/api/v1/company_approvers.py`<br>`lia-agent-system/app/api/v1/company_assessments.py`<br>`lia-agent-system/app/api/v1/company_benefits_api.py` |
| 🔴 | `195642ec4` | 2026-04-07 | Cross Back↔Front | §1 Teams Integration | Update Teams bot authentication to use tenant-specific endpoint — Updates `teams_simple.py` to use the `AZURE_TENANT_ID` for single-tenant authentication, modif | `lia-agent-system/app/domains/communication/services/teams_simple.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts` |
| 🔴 | `e8b7146f3` | 2026-04-07 | Cross Back↔Front | §1 Teams Integration | Improve Teams message handling by fixing timestamp parsing — Update teams.py to correctly parse and store message timestamps, and adjust search filter state ini | `lia-agent-system/app/api/v1/teams.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesUIState.ts` |
| 🔴 | `4af1a779f` | 2026-04-07 | Cross Back↔Front | Task #53 | Task #53: Add 10 critical behavioral tests + raise coverage gates — ## Summary | `lia-agent-system/pytest.ini`<br>`lia-agent-system/tests/e2e/test_wsi_call_flow_e2e.py`<br>`lia-agent-system/tests/integration/test_cv_screening_pipeline.py`<br>`lia-agent-system/tests/integration/test_interview_scheduling_conflicts.py`<br>`lia-agent-system/tests/integration/test_merge_webhook.py` |
| 🔴 | `d7462265a` | 2026-04-07 | Cross IA↔Front | Docs (geral) | Merged changes from vs4jplti/main — Replit-Task-Id: a94aa833-ba88-4578-847d-d41212bee642 | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/domains/communication/services/communication_service.py`<br>`lia-agent-system/app/domains/communication/services/message_providers.py`<br>`lia-agent-system/app/domains/communication/services/template_service.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `6ced5a6c3` | 2026-04-06 | Cross Back↔Front | §15 WSI | Add new repositories for job vacancies and screening tasks — Introduce new repository classes for managing job vacancies and screening tasks, and update existin | `lia-agent-system/app/domains/cv_screening/repositories/__init__.py`<br>`lia-agent-system/app/domains/cv_screening/repositories/screening_repository.py`<br>`lia-agent-system/app/domains/job_management/repositories/job_vacancy_crud_repository.py`<br>`lia-agent-system/app/domains/recruitment/repositories/application_repository.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts` |
| 🔴 | `fdc03b5a4` | 2026-04-06 | Cross Back↔Front | Task #40 | Task #40: Credits — Full billing infrastructure — Models (billing.py): | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/credits.py`<br>`lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/domains/interview_scheduling/repositories/__init__.py` |
| 🔴 | `61752038b` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/domains/communication/services/email_providers/resend_provider.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesViewComposition.tsx` |
| 🔴 | `4c22ddda8` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/libs/models/lia_models/communication_history.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesActions.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesLIAHandlers.ts` |
| 🔴 | `07c43b2e4` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/domains/communication/services/email_providers/mailgun_provider.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesViewComposition.tsx` |
| 🔴 | `43e90596e` | 2026-04-06 | Cross IA↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/public/shared_searches.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/admin_templates.py`<br>`lia-agent-system/app/api/v1/agent_templates.py` |
| 🔴 | `837aef67a` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/domains/automation/services/pattern_applier.py`<br>`lia-agent-system/app/domains/chat/repositories/__init__.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/domains/job_management/services/job_vacancy_route_service.py` |
| 🔴 | `2bbc1edf9` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: | `lia-agent-system/app/api/v1/ats.py`<br>`plataforma-lia/src/components/settings/integrations/IntegrationDetailDrawer.tsx` |
| 🔴 | `587e96c50` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Complete frontend-backend wiring with security hardening — Frontend changes: | `lia-agent-system/app/api/v1/ats.py`<br>`plataforma-lia/src/app/api/backend-proxy/ats/connections/sync/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ats/field-mappings/route.ts`<br>`plataforma-lia/src/components/pages/ats-integrations/SystemConfigurationModal.tsx`<br>`plataforma-lia/src/components/pages/ats-integrations/useAtsIntegrations.ts` |
| 🔴 | `14b5ae056` | 2026-04-06 | Cross Back↔Front | Task #38 | Task #38: ATS Integration — Complete frontend-backend wiring — Frontend changes: | `lia-agent-system/app/api/v1/ats.py`<br>`plataforma-lia/src/components/pages/ats-integrations/SystemConfigurationModal.tsx`<br>`plataforma-lia/src/components/pages/ats-integrations/ats-integrations.types.ts`<br>`plataforma-lia/src/components/pages/ats-integrations/useAtsIntegrations.ts` |
| 🔴 | `8729d4587` | 2026-04-06 | Cross Back↔Front | Task #38 | Task #38: ATS Integration — Connect frontend to real backend — Backend changes (lia-agent-system/app/api/v1/ats.py): | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/libs/models/lia_models/ats_integration.py`<br>`plataforma-lia/src/app/api/backend-proxy/ats/connections/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ats/field-mappings/route.ts`<br>`plataforma-lia/src/components/pages/ats-integrations/SystemConfigurationModal.tsx` |
| 🔴 | `b7c41231d` | 2026-04-06 | Cross IA↔Back | Automations | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handlers in platform_event_handlers.py: | `lia-agent-system/app/api/v1/admin_settings.py`<br>`lia-agent-system/app/api/v1/admin_templates.py`<br>`lia-agent-system/app/api/v1/alerts.py`<br>`lia-agent-system/app/api/v1/approvals.py`<br>`lia-agent-system/app/api/v1/ats.py` |
| 🔴 | `9826db31d` | 2026-04-06 | Cross IA↔Back | scope: phase9 | refactor(phase9): ruff auto-fixes — remove 819 unused imports, sort imports, modernize type annotations — - F401: removed 819 unused imports across 446 files | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/v1/admin.py`<br>`lia-agent-system/app/api/v1/admin_circuit_breakers.py`<br>`lia-agent-system/app/api/v1/admin_settings.py` |
| 🔴 | `6d7a9daf8` | 2026-04-06 | Cross IA↔Front | Task #36 | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useMLPredictions hook integration with | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/clients.py`<br>`lia-agent-system/app/api/v1/workos.py`<br>`lia-agent-system/app/domains/ai/services/__init__.py`<br>`lia-agent-system/app/domains/ai/services/ai_cache_service.py` |
| 🔴 | `e7e1bb07e` | 2026-04-06 | Cross IA↔Front | Task #36 | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useMLPredictions hook integration with | `lia-agent-system/app/api/v1/affirmative.py`<br>`lia-agent-system/app/api/v1/calibration.py`<br>`lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/api/v1/policy_engine.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py` |
| 🔴 | `41d9174cd` | 2026-04-06 | Cross IA↔Front | Task #43 | Task #43: Complete audit and fix of LIA agentic capabilities — Changes across 10+ files covering all 8 session plan tasks: | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_handlers/__init__.py`<br>`lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py` |
| 🟡 | `d7476dbc2` | 2026-04-06 | Cross IA↔Back | Task #32 | Fix candidates and vacancies loading (Task #32) — Root cause: The backend (lia-agent-system) was crashing on startup with | `lia-agent-system/app/orchestrator/intent_router.py`<br>`lia-agent-system/app/services/culture_analyzer_service.py`<br>`lia-agent-system/app/services/enhanced_intent_classifier.py` |
| 🔴 | `9ff2904b9` | 2026-04-06 | Cross IA↔Back | FastAPI v1 endpoints | Remove unused demo user fallbacks and clean up code imports — Update imports, type hints, and remove dead code related to demo user fallbacks. | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/agents/policy_setup_agent.py`<br>`lia-agent-system/app/agents/specialized/__init__.py`<br>`lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/public/candidate_portal.py` |
| 🟡 | `45c603989` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/services/analysis_service.py`<br>`lia-agent-system/app/services/enhanced_intent_classifier.py` |
| 🟡 | `c33440970` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/main.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/services/analysis_service.py` |
| 🟡 | `63e9557cc` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/services/analysis_service.py` |
| 🔴 | `16c6bd8fa` | 2026-04-06 | Cross Back↔Front | Configurações (hub) | Remove entire /admin section from plataforma-lia frontend — Removed ~19,000 lines across 93 files that constituted the admin panel, | `lia-agent-system/app/api/v1/_archived/__init__.py`<br>`lia-agent-system/app/api/v1/_archived/orchestrated_pipeline_chat.py`<br>`lia-agent-system/app/api/v1/job_vacancies.py`<br>`lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/main.py.bak` |
| 🔴 | `3e802b0ed` | 2026-04-06 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Restore Shield icon and update dependencies for CV parsing — Update dependencies in pyproject.toml and fix import path for PdfReader in cv_parser.py. | `lia-agent-system/app/domains/analytics/models/observability.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py`<br>`plataforma-lia/src/app/admin/layout.tsx` |
| 🔴 | `b5e74a10e` | 2026-04-06 | Cross Back↔Front | Compliance Dashboard (FE) | Remove candidate search API endpoints and related configurations — Delete `candidate_search.py` file, removing all API endpoints for hybrid candidate search, in | `lia-agent-system/app/api/v1/candidate_search.py`<br>`lia-agent-system/app/domains/analytics/models/observability.py`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/auditoria/bias/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/auditoria/exportar/page.tsx` |
| 🔴 | `09e3dd04c` | 2026-04-06 | Cross Back↔Front | FastAPI v1 endpoints | Refine chat interface and optimize backend data handling — Update UI components to adjust message bubble sizing, spacing, and font sizes. Introduce new toolbar | `lia-agent-system/app/api/v1/candidate_lists.py`<br>`lia-agent-system/app/api/v1/workforce.py`<br>`lia-agent-system/app/auth/dependencies.py`<br>`lia-agent-system/app/auth/rails_jwt.py`<br>`lia-agent-system/app/auth/security.py` |
| 🔴 | `9d569d6c7` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Improve chat functionality and security by adding retries and enhancing authentication — This commit introduces a robust retry mechanism with token refresh for  | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/universal/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/conversations/[id]/context/route.ts` |
| 🟡 | `ccca718b9` | 2026-04-05 | Cross IA↔Back | §15 WSI | Improve AI chat functionality by enhancing LLM integrations and error handling — Refactor LLM client interactions to use a unified service for PII stripping, te | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/wsi/_shared.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/conversation_memory.py` |
| 🔴 | `7dff2e8a3` | 2026-04-05 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Task #15: Migrate legacy company_id/tenant_id — remove all fallback defaults — - Alembic migration 059: audit script covering 16 tables | `lia-agent-system/alembic/versions/059_migrate_legacy_company_ids.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/attachments.py`<br>`lia-agent-system/app/api/v1/auth.py` |
| 🔴 | `420c5b228` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Update chat functionality to correctly stream responses — Adjust API endpoints and client configurations to properly handle streaming responses from the chat  | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/actions/candidate-field-update/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/universal/route.ts` |
| 🔴 | `2278806b7` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active/route.ts` |
| 🔴 | `283441d37` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/components/lia-float/SwitchTaskModal.tsx` |
| 🔴 | `1cd2b37c5` | 2026-04-05 | Cross Back↔Front | §1 Teams Integration | Update chat functionality to correctly track recent conversations and improve task management — This commit refactors the `updateRecentItem` callback to accept  | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/useLiaChatPanelState.ts` |
| 🔴 | `bb6a29bc0` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/ws_manager.py`<br>`plataforma-lia/src/components/lia-float/LiaChatHeader.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/SwitchTaskModal.tsx` |
| 🔴 | `239ec2f66` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/BackgroundAgentsStatus.tsx`<br>`plataforma-lia/src/components/lia-float/BackgroundTaskNotification.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/ModeLabel.tsx` |
| 🔴 | `f30f28f96` | 2026-04-05 | Cross Back↔Front | Task #12 | Task #12: Split-Screen Dinâmico — T003/T004/T005 complete — T003: WebSocket panel_update event handling | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/panels/CalibrationPanel.tsx`<br>`plataforma-lia/src/components/lia-float/panels/CandidateProfilePanel.tsx`<br>`plataforma-lia/src/components/lia-float/panels/CandidateReviewPanel.tsx` |
| 🔴 | `d641ea4eb` | 2026-04-05 | Cross Back↔Front | §14 BYOK + LLM Factory | feat: Migrate Voice Screening VoIP from Twilio+STT+TTS to Gemini Live Audio API — Task #6: Browser VoIP calls now use Gemini Live Audio natively. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/gemini_voice.py`<br>`lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/services/gemini_live_audio_service.py`<br>`lia-agent-system/app/services/voice_screening_orchestrator.py` |
| 🔴 | `535f05984` | 2026-04-05 | Cross IA↔Front | §9 Tenant Isolation / Multi-tenancy | Fix multi-tenancy company_id isolation (Task #5) — Backend: | `lia-agent-system/alembic/versions/058_add_client_account_id_to_company_profiles.py`<br>`lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py`<br>`lia-agent-system/libs/models/lia_models/company.py` |
| 🟡 | `0faa509af` | 2026-04-05 | Cross IA↔Back | FastAPI v1 endpoints | Integrate planning system into chat and improve session management — Refactor code to connect the planning system to the chat functionality, improve session ID  | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/audit_logs.py`<br>`lia-agent-system/app/api/v1/compliance_controls.py`<br>`lia-agent-system/app/api/v1/consent_management.py`<br>`lia-agent-system/app/api/v1/continuity.py` |
| 🔴 | `95ad2730a` | 2026-04-05 | Cross Back↔Front | LIA Float UI (FE) | Add multi-step plan execution with real-time progress tracking — Integrate plan detection and execution into the WebSocket handler, enabling multi-step workflow | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/services/rails_adapter.py`<br>`plataforma-lia/src/components/lia-float/LiaChatMessageList.tsx` |
| 🔴 | `9882eeb76` | 2026-04-05 | Cross Back↔Front | FE libs / utils | Hide internal thoughts from users in chat conversations — Add functionality to strip `<thought>` tags from agent responses on both the frontend and backend, a | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/triagem/MessageBubble.tsx` |
| 🔴 | `642ece67f` | 2026-04-05 | Cross Back↔Front | Backend Services (BE) | Update daily briefing to show errors and refresh data — Modify the daily briefing card component to handle fetch errors by displaying an error UI instead of | `lia-agent-system/app/auth/rails_jwt.py`<br>`lia-agent-system/app/services/ats_clients/wedotalent_rails.py`<br>`plataforma-lia/src/components/daily-briefing-card.tsx` |
| 🔴 | `f04070006` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/cancel/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/complete/route.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `3621573ba` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `plataforma-lia/src/app/api/backend-proxy/briefing/route.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `b9af19951` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/audit_logs.py`<br>`lia-agent-system/app/api/v1/compliance_controls.py`<br>`lia-agent-system/app/api/v1/consent_management.py`<br>`lia-agent-system/app/api/v1/continuity.py` |
| 🔴 | `84c6159b5` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Connect Tarefas page to real backend APIs + Activity Feed section — Changes: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/lia_assistant_graph.py`<br>`lia-agent-system/app/api/v1/wizard_smart_orchestrator.py`<br>`lia-agent-system/app/auth/dependencies.py` |
| 🔴 | `3ef9c9f72` | 2026-04-05 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Connect Tarefas page to real backend APIs + Activity Feed section — Changes: | `plataforma-lia/src/components/daily-briefing-card.tsx` |
| 🔴 | `9bd6b42c8` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Connect Tarefas page to real backend APIs, add Activity Feed section — - Created 4 Next.js proxy routes: GET /tasks, GET /tasks/summary, | `lia-agent-system/app/api/v1/agent_memory.py`<br>`plataforma-lia/src/app/api/backend-proxy/briefing/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/cancel/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/complete/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/route.ts` |
| 🔴 | `3fdac6219` | 2026-04-05 | Cross Back↔Front | Kanban (vagas) | fix: manual job creation redirect to config page (#151) — Frontend: | `lia-agent-system/app/main.py`<br>`lia-agent-system/libs/models/lia_models/candidate.py`<br>`plataforma-lia/src/app/jobs/[id]/JobDetailClient.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsModalsSectionTypes.ts` |
| 🔴 | `381379cdb` | 2026-04-05 | Cross IA↔Front | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Scope: Only plataforma-lia frontend files (backend files | `lia-agent-system/app/services/__init__.py`<br>`lia-agent-system/app/services/agent_monitoring_service.py`<br>`lia-agent-system/app/services/apify_mcp_client.py`<br>`lia-agent-system/app/services/apify_service.py`<br>`lia-agent-system/app/services/ats_job_history_service.py` |
| 🔴 | `476849cd5` | 2026-04-05 | Cross IA↔Front | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Changes: | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/agent_monitoring.py`<br>`lia-agent-system/app/api/v1/alerts.py`<br>`lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/approvals.py` |
| 🔴 | `747ce44cb` | 2026-04-05 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Add fairness warnings and fix onboarding hydration issues — Introduce `fairness_warnings` to `ChatResponse` and resolve hydration mismatches in `OnboardingContr | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/onboarding/onboarding-controller.tsx` |
| 🟡 | `25e7d7645` | 2026-04-05 | Cross IA↔Back | Performance | perf: lower vector cache threshold from 0.92 to 0.85 | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/vector_semantic_cache.py` |
| 🔴 | `0867d7d12` | 2026-04-05 | Cross IA↔Front | §2 Orchestrator Migration | Fix sidebar errors and update backend port configuration — Addresses "Maximum update depth exceeded" and "Invalid hook call" errors in the sidebar component by | `lia-agent-system/app/orchestrator/action_executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/__init__.py`<br>`lia-agent-system/app/orchestrator/action_executor/action_types.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `c6948a1db` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Core migration: all 5 callers now use WSIService.generate_from_simple_inputs() | `lia-agent-system/app/api/v1/screening.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service.py` |
| 🟡 | `6e99cedd0` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Migrated all 5 callers to use WSIService.generate_from_simple_inputs(): | `lia-agent-system/app/api/v1/screening.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/domains/cv_screening/constants/wsi_constants.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_generator.py` |
| 🟡 | `9e225f9dd` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Migrated all 5 callers to use WSIService.generate_from_simple_inputs(): | `lia-agent-system/app/api/v1/screening.py`<br>`lia-agent-system/app/api/v1/wsi/questions.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`lia-agent-system/app/api/v1/wsi_screening_pipeline_endpoint.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| 🟡 | `4b4a69b5a` | 2026-04-04 | Cross IA↔Back | §15 WSI | refactor(wsi): consolidate Bloom/Dreyfus/seniority constants into wsi_constants.py — Centralized duplicate constants from 8 files into wsi_constants.py as singl | `lia-agent-system/app/api/v1/candidate_search/__init__.py`<br>`lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py` |
| 🔴 | `dcda58d1e` | 2026-04-04 | Cross Back↔Front | scope: voip | feat(voip): complete VoIP browser calling with recruiter status visibility (Task #142) — End-to-end VoIP browser calling with full PSTN parity on candidate and  | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/api/v1/twilio_voice.py`<br>`lia-agent-system/app/domains/communication/services/twilio_voice_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx`<br>`plataforma-lia/src/components/triagem/VoIPCallButton.tsx` |
| 🔴 | `3b95e5e7d` | 2026-04-04 | Cross Back↔Front | Task #144 | feat(task-144): Implement job vacancy lifecycle management — Backend: | `lia-agent-system/alembic/versions/056_add_lifecycle_fields_candidate.py`<br>`lia-agent-system/app/api/v1/job_vacancies.py`<br>`lia-agent-system/libs/models/lia_models/candidate.py`<br>`plataforma-lia/src/components/kanban/components/CandidateCard.tsx`<br>`plataforma-lia/src/components/kanban/types.ts` |
| 🔴 | `5b617db7c` | 2026-04-04 | Cross IA↔Front | §15 WSI | Align WSI scoring thresholds across the system and remove duplication — Update WSI scoring thresholds in `automation.py`, `event_handlers.py`, and `wsi_service. | `lia-agent-system/app/api/v1/automation/__init__.py`<br>`lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/automation/suggestions.py`<br>`lia-agent-system/app/api/v1/automation/triggers.py` |
| 🟡 | `9dadd3117` | 2026-04-04 | Cross IA↔Back | §15 WSI | feat(task-143): Unify web/chat screening (triagem) with WSI ecosystem — Integrates triagem_session_service.py fully with the WSI pipeline, and fixes | `lia-agent-system/app/services/triagem_session_service.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🔴 | `30b1b9151` | 2026-04-04 | Cross IA↔Front | Task #138 | Task #138: Dead integration cleanup - OpenMic, Deepgram, SynthFlow, StackOne, Neon, Prometheus, Grafana — Completed cleanup of 7 dead integrations from the code | `lia-agent-system/app/api/v1/external_webhooks.py`<br>`lia-agent-system/app/api/v1/lia_voice.py`<br>`lia-agent-system/app/api/v1/metrics.py`<br>`lia-agent-system/app/api/v1/openmic.py`<br>`lia-agent-system/app/api/v1/transcription.py` |
| 🟡 | `790319d7f` | 2026-04-04 | Cross IA↔Back | §14 BYOK + LLM Factory | feat(task-132): Gemini como LLM Padrão — Reordenar fallback chain — ## Objetivo | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py`<br>`lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🔴 | `2b8c725c0` | 2026-04-04 | Cross Back↔Front | Observability / Sentry / OTLP | Task #136: Ativar Sentry — Monitoramento de Erros em Produção — Changes: | `lia-agent-system/app/main.py`<br>`lia-agent-system/apps/api-funil/main.py`<br>`lia-agent-system/apps/api-onboarding/main.py`<br>`lia-agent-system/apps/api-vagas/main.py` |
| 🔴 | `9c57a17f5` | 2026-04-04 | Cross IA↔Front | Task #133 | Task #133: Remove all StackOne integration — Merge.dev as sole universal ATS connector — Complete removal of StackOne integration from backend, frontend, tests, | `lia-agent-system/app/agents/specialized/__init__.py`<br>`lia-agent-system/app/api/v1/automation.py`<br>`lia-agent-system/app/api/v1/external_webhooks.py`<br>`lia-agent-system/app/api/v1/integrations_hub.py`<br>`lia-agent-system/app/api/v1/journey_mapping.py` |
| 🟡 | `4fb8a5f89` | 2026-04-04 | Cross IA↔Back | Task #125 | feat(task-125): Declarative tool permissions (YAML) and DI for LLM providers — Task #125 — Tool Permissions Declarativo (YAML) e DI para Providers | `lia-agent-system/app/orchestrator/tenant_budget.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py`<br>`lia-agent-system/app/tools/scope_config.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |
| 🔴 | `7419c32ac` | 2026-04-04 | Cross IA↔Back | Wizard (geral) | task-124: Eliminar 23 Shims e Estabelecer Contracts Formais entre Camadas — ## What was done | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/agents/nodes.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/agent_explainability.py`<br>`lia-agent-system/app/api/v1/agent_memory.py` |
| 🔴 | `71fc9de33` | 2026-04-04 | Cross IA↔Back | Task #123 | feat(task-123): Complete LangGraph migration - fix regressions and update tests — Fixes two regressions identified in code review: | `lia-agent-system/app/api/v1/health_langgraph.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/services/checkpoint_service.py` |
| 🔴 | `80b4239f3` | 2026-04-04 | Cross IA↔Front | §15 WSI | Improve WSI feedback generation and scoring accuracy — Refactor the WSI scoring and feedback generation process to accurately map scores, incorporate candi | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_feedback_generator.py`<br>`lia-agent-system/app/services/openmic_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🔴 | `4fb43153b` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/services/openmic_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🔴 | `3dfe1ede9` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx`<br>`plataforma-lia/src/components/triagem/PhoneConfirmModal.tsx`<br>`plataforma-lia/src/components/triagem/WelcomeCard.tsx` |
| 🔴 | `d50c67402` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl` and `fetchAndPlayTts` as reusable useCallback hooks | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx`<br>`plataforma-lia/src/components/triagem/InputBar.tsx`<br>`plataforma-lia/src/components/triagem/MessageBubble.tsx` |
| 🟡 | `a2facdc6b` | 2026-04-04 | Cross IA↔Back | Task #122 | fix: address code review for Task #122 orchestrator consolidation — Three runtime regressions fixed, plus two improvements from review comments: | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/orchestrated_job_chat.py`<br>`lia-agent-system/app/api/v1/orchestrated_talent_chat.py`<br>`lia-agent-system/app/orchestrator/action_executor.py`<br>`lia-agent-system/app/orchestrator/action_handlers/__init__.py` |
| 🔴 | `5bb701e8f` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #128: Triagem UX — Ajustes Candidato (Welcome, Balões, Tom, Whitelabel) — Backend (triagem_session_service.py): | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/components/triagem/MessageBubble.tsx`<br>`plataforma-lia/src/components/triagem/WelcomeCard.tsx`<br>`plataforma-lia/src/components/triagem/types.ts` |
| 🔴 | `e8daa86e9` | 2026-04-04 | Cross Back↔Front | §1 Teams Integration | Add a complete chat screening flow to the platform — This commit introduces the full chat screening flow, including Welcome, Chat, Confirmation, and Comp | `lia-agent-system/app/api/v1/teams.py` |
| 🔴 | `f76917cf9` | 2026-04-04 | Cross Back↔Front | Backend Proxy Routes (FE) | Remove hardcoded company IDs and improve authentication — Replace all instances of hardcoded 'demo_company' with dynamic company ID resolution, enhancing secu | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/domains/communication/services/teams_tab_trigger.py`<br>`plataforma-lia/src/app/admin/compliance/page.tsx`<br>`plataforma-lia/src/app/admin/configuracoes/politicas/page.tsx` |
| 🔴 | `69d0e5e28` | 2026-04-04 | Cross Back↔Front | Unified Chat (FE) | Migrate local storage to Zustand stores and improve daily digest functionality — Replaces remaining localStorage usages with Zustand stores, and adds scheduled  | `lia-agent-system/app/api/v1/digest.py`<br>`lia-agent-system/app/domains/automation/services/automation_scheduler.py`<br>`plataforma-lia/src/app/teams-tab/candidatos/page.tsx`<br>`plataforma-lia/src/app/teams-tab/layout.tsx`<br>`plataforma-lia/src/app/teams-tab/page.tsx` |
| 🔴 | `770785e4c` | 2026-04-04 | Cross IA↔Front | Frontend (componentes diversos) | Improve candidate and admin interfaces by cleaning up code — Refactor multiple UI components, remove unused icons and constants, and archive a navigation patter | `lia-agent-system/app/orchestrator/navigation_intent.py`<br>`plataforma-lia/src/components/_archived/dashboards/big-five-dashboard-page.tsx`<br>`plataforma-lia/src/components/_archived/dashboards/calibration-dashboard.tsx`<br>`plataforma-lia/src/components/_archived/dashboards/dashboard/predictive-analytics-tab.tsx`<br>`plataforma-lia/src/components/_archived/dashboards/dashboard/strategic-dashboard.tsx` |
| 🔴 | `0a44b6fa0` | 2026-04-04 | Cross Back↔Front | Task #116 | Task #116: Zustand State Management - Complete migration — Auth Store (auth-store.ts): | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_calendar_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_sso_service.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanFilters.ts` |
| 🔴 | `7f946bcf3` | 2026-04-04 | Cross Back↔Front | Task #115 | Task #115: Lazy Loading - Replace () => null loading fallbacks with visible loading states — All dynamic() imports across modal and page-section files now use p | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py`<br>`plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🔴 | `79095dd08` | 2026-04-04 | Cross Back↔Front | Task #112 | Task #112+#113: @ts-ignore elimination + lazy loading + bugfixes — Task #112 - @ts-ignore elimination (11 files clean): | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`plataforma-lia/src/components/candidate-preview.tsx` |
| 🔴 | `1e1e9971a` | 2026-04-04 | Cross Back↔Front | Task #112 | Task #112: Complete @ts-ignore batch 2 elimination (10/10 files clean) Task #113: Implement lazy loading + code splitting for heavy components — Task #112: | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py`<br>`lia-agent-system/app/domains/communication/services/teams_proactivity_engine.py` |
| 🔴 | `72875a661` | 2026-04-03 | Cross Back↔Front | Acessibilidade (a11y) | Task #110: Design System v4.2.1 + Accessibility + Dead Code cleanup — Changes: | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/app/portal/data-request/[token]/PortalFieldRenderer.tsx`<br>`plataforma-lia/src/components/candidate-preview.tsx`<br>`plataforma-lia/src/components/charts/chart-components.tsx`<br>`plataforma-lia/src/components/ml-analytics/success-prediction.tsx` |
| 🔴 | `daed87514` | 2026-04-03 | Cross IA↔Front | scope: lia-chat | fix(lia-chat): Round 9 — education_level to lia_insights JSON + PT-BR datetime resolver — Final semantic fix (code review approved-with-comments): | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/file_analysis.py`<br>`lia-agent-system/app/domains/interview_scheduling/services/calendar_service.py`<br>`lia-agent-system/app/orchestrator/action_executor.py`<br>`lia-agent-system/app/orchestrator/fast_router.py` |
| 🔴 | `2eee5c680` | 2026-04-03 | Cross Back↔Front | Frontend (componentes diversos) | Remove type checking errors and improve data handling — Addresses numerous TypeScript errors by removing `@ts-ignore` comments and implementing proper type  | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWSIAndCalibrationHandlers.ts`<br>`plataforma-lia/src/components/lia-metrics-dashboard.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx` |
| 🔴 | `6bfc8dc47` | 2026-04-03 | Cross Back↔Front | Task #108 | Task #108: Centralize client-side business logic (scores + pricing) — Created centralized score utility (src/lib/score-utils.ts): | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/app/admin/compliance/riscos/fornecedores/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/registro/page.tsx`<br>`plataforma-lia/src/app/api/backend-proxy/cv/upload-and-screen/route.ts` |
| 🔴 | `395ad8955` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #107: Complete API validation + security hardening — Frontend API routes: | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/app/api/ai/extract-archetype-info/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-companies/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-company-tags/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-expertise/route.ts` |
| 🔴 | `7a298e6e3` | 2026-04-03 | Cross IA↔Front | Task #107 | Task #107: Complete API validation hardening — Changes: | `lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/scope_config.py`<br>`plataforma-lia/src/app/api/backend-proxy/admin/guardrails/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/templates/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/approvals/[id]/approve/route.ts` |
| 🔴 | `e4a5d4705` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Complete validation hardening — All review issues fixed: | `plataforma-lia/src/app/api/backend-proxy/admin/guardrails/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/guardrails/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/templates/[id]/publish/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/templates/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/templates/route.ts` |
| 🔴 | `3597eab4b` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Fix code review issues — Review fixes round 2: | `plataforma-lia/src/app/api/backend-proxy/analysis/file/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/from-cv/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/similar/combine-profiles/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/transcribe/audio/route.ts` |
| 🔴 | `6b3e4524f` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Zod validation + Security Headers — Security Headers: | `plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/session/route.ts`<br>`plataforma-lia/src/app/api/auth/workos/callback/route.ts`<br>`plataforma-lia/src/app/api/auth/workos/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/workos/session/route.ts` |
| 🔴 | `f12e35d4a` | 2026-04-03 | Cross IA↔Front | §2 Orchestrator Migration | Improve CV analysis and access control for API endpoints — Update CV matching patterns in orchestrator.py, replace redirectToLogin with denyAccess in middlewar | `lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `7863c72ba` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session API == | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/app/api/auth/session/route.ts` |
| 🔴 | `7396ade2a` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session API == | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/tools/scope_config.py` |
| 🔴 | `6399beccf` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core changes == | `lia-agent-system/app/tools/__init__.py` |
| 🔴 | `f059b6786` | 2026-04-03 | Cross IA↔Front | Docs / Specs | Improve job preview and communication channel appearance — Updates UI components to fix visual discrepancies in job previews and communication channels, includ | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`plataforma-lia/src/app/api/backend-proxy/lia/[...path]/route.ts`<br>`plataforma-lia/src/components/pages/jobs/JobPreviewPanel.tsx`<br>`plataforma-lia/src/components/pages/jobs/job-preview/sections/JobScreeningSection.tsx` |
| 🔴 | `0882a4580` | 2026-04-03 | Cross IA↔Front | §2 Orchestrator Migration | Align job preview panel with candidate preview design system — Fixes background, border, and badge font size issues in the job preview panel to match the candid | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/services/enhanced_intent_classifier.py`<br>`plataforma-lia/src/components/pages/jobs/JobPreviewPanel.tsx` |
| 🔴 | `9338f7773` | 2026-04-03 | Cross Back↔Front | Docs / Specs | Fix infinite loop in chat component state management — Wrap reset functions in useCallback to prevent re-renders and resolve the "Maximum update depth exce | `lia-agent-system/app/api/v1/wsi.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useFastTrackState.ts` |
| 🔴 | `c28bc08ee` | 2026-04-01 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Improve system compliance and fix runtime errors in frontend components — Implement enhancements to ensure compliance across various domains by integrating fair | `lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py`<br>`lia-agent-system/app/domains/automation/domain.py`<br>`lia-agent-system/app/domains/communication/domain.py`<br>`lia-agent-system/app/domains/cv_screening/domain.py` |
| 🔴 | `e1d7bf9b0` | 2026-03-31 | Cross Back↔Front | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — - Added _create_bell_notification method to ProactiveService with type/category | `lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/chat/delivered/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/chat/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/send/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/summary/route.ts` |
| 🔴 | `59eea4b6a` | 2026-03-31 | Cross Back↔Front | scope: ts | fix(ts): @ts-nocheck sweep — all remaining 239 error files | `lia-agent-system/app/api/v1/rubric_evaluation.py`<br>`lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx`<br>`plataforma-lia/src/components/chat/ChatContextPanelPart1.tsx`<br>`plataforma-lia/src/components/lia-metrics-dashboard.tsx` |
| 🔴 | `a48928814` | 2026-03-31 | Cross Back↔Front | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — ## Changes Made | `lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/components/notifications/notification-center.tsx` |
| 🟡 | `3ae490572` | 2026-03-31 | Cross IA↔Back | Task #81 | Task #81 Audit Trail E2E - Complete implementation — All 8 Alpha 1 flow stages instrumented with correct signatures: | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| 🟡 | `8bd2645a4` | 2026-03-31 | Cross IA↔Back | Task #81 | Task #81 Audit Trail E2E - Review fixes round 4 — Changes: | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🔴 | `681625844` | 2026-03-31 | Cross Back↔Front | Compliance / LGPD / EU AI Act | fix(weekly-digest): dashboard data mapping, tenant-scoped compliance, PII masking, a11y & DS compliance — - Fix _gather_pipeline_health to read from dashboard.s | `lia-agent-system/app/domains/analytics/services/digest_formatter.py`<br>`lia-agent-system/app/domains/analytics/services/weekly_digest_service.py`<br>`plataforma-lia/src/components/settings/communication-hub/AlertsTab.tsx` |
| 🔴 | `e631dfcda` | 2026-03-31 | Cross Back↔Front | scope: weekly-digest | feat(weekly-digest): fix T005 bugs — auth guards, proxy route, DB column, preference loading — Task #78 Weekly Digest — T005 bug fixes: | `lia-agent-system/app/api/v1/digest.py`<br>`plataforma-lia/src/app/api/backend-proxy/digest/weekly/preferences/route.ts`<br>`plataforma-lia/src/components/settings/communication-hub/useCommunicationHub.ts` |
| 🔴 | `86805f232` | 2026-03-31 | Cross Back↔Front | scope: weekly-digest | feat(weekly-digest): fix T005 critical bugs — preferences persistence, proxy route, UUID validation — Task #78 Weekly Digest — T005 bug fixes: | `lia-agent-system/app/api/v1/digest.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/domains/analytics/services/digest_formatter.py`<br>`lia-agent-system/app/domains/analytics/services/weekly_digest_service.py`<br>`lia-agent-system/app/domains/automation/services/proactive_service.py` |
| 🔴 | `f4c2e96b8` | 2026-03-31 | Cross IA↔Front | Compliance / LGPD / EU AI Act | fix(compliance): Task #76 — GOV-01, LGPD-01, DEI-02 compliance & governance fixes — GOV-01 (MEDIUM): Added audit_service.log_decision() to JD generation | `lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py`<br>`plataforma-lia/src/components/candidate-decision-flow-modal.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts`<br>`plataforma-lia/src/components/settings/CompanyDataSection.tsx` |
| 🔴 | `3562ec23f` | 2026-03-31 | Cross IA↔Front | scope: seo | feat(seo): metadata global + OG image + title template — cobertura 88 páginas | `lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`plataforma-lia/src/app/layout.tsx`<br>`plataforma-lia/src/components/triagem/WelcomeCard.tsx` |
| 🔴 | `08fa21a28` | 2026-03-31 | Cross Back↔Front | Configurações (hub) | Update roadmap and cache settings with minor code improvements — Amends c2fd209d with updates to ANALISE_ROADMAP, adjusts LLM classification cache TTL, and adds | `lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py`<br>`plataforma-lia/src/app/accept-invitation/layout.tsx`<br>`plataforma-lia/src/app/access/layout.tsx`<br>`plataforma-lia/src/app/aceitar-convite/layout.tsx`<br>`plataforma-lia/src/app/admin/clientes/layout.tsx` |
| 🔴 | `c2fd209de` | 2026-03-31 | Cross Back↔Front | Backend (genérico) | fix(backend): Task #74 — Fix 5 backend architecture findings from Fase 6 audit — ARCH-04 (CRITICAL): Added **kwargs to RAGPipelineService.search() signature. | `lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx`<br>`plataforma-lia/src/components/modals/data-blocking-modal.tsx`<br>`plataforma-lia/src/components/pages/candidate-review-modal.tsx`<br>`plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx` |
| 🟡 | `54eedca43` | 2026-03-31 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(task-72): Fase 5 — A/B Testing, Template Learning, WRF Adaptive K, LLM Job Classification, FairnessGuard L3 Sector — - A/B Testing: Seed 3 email experiment | `lia-agent-system/app/domains/communication/services/communication_service.py`<br>`lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py`<br>`lia-agent-system/app/domains/sourcing/services/wrf_service.py`<br>`lia-agent-system/app/main.py`<br>`lia-agent-system/app/services/rag_pipeline_service.py` |
| 🟡 | `95e58e3a9` | 2026-03-31 | Cross IA↔Back | §1 Teams Integration | fix(task-71): Fix Teams notify_* method contracts and add webhook fallback — - notify_* methods: conversation_reference now optional (keyword-only) | `lia-agent-system/app/domains/communication/services/teams_bot.py`<br>`lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py` |
| 🔴 | `e55ee0f7e` | 2026-03-31 | Cross IA↔Front | §1 Teams Integration | fix(task-71): Wire Teams notifications, fix embedding collision, connect voice endpoints — - Gate 2 embedding: use uuid5(candidate_id+job_id) to avoid overwriti | `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🔴 | `c122742a7` | 2026-03-31 | Cross IA↔Front | Task #70 | Task #70: Round 6 — fix EmailService class, persistent template learning, WhatsApp channels — - feedback.auto_send: uses SendGridEmailService (not EmailService) | `lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatCallbacks.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsPageCore.tsx` |
| 🔴 | `bcecf9aea` | 2026-03-31 | Cross Back↔Front | Task #70 | Task #70: Round 5 — zero 'any' types, EmailService routing, communication status update — Frontend: | `lia-agent-system/app/services/email_tracking_service.py`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx`<br>`plataforma-lia/src/components/search/JobFiltersSection.tsx`<br>`plataforma-lia/src/components/search/job-filters/JobLevelsAndRolesSection.tsx`<br>`plataforma-lia/src/components/search/job-filters/JobTitlesSection.tsx` |
| 🔴 | `9b98dd5cd` | 2026-03-31 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Task #70: Round 4 — remove all 'as any' casts, fail-closed webhook, universal FairnessGuard — - CandidatesPageModals.tsx: replaced all 'as any' casts with direc | `lia-agent-system/app/api/v1/email_tracking.py`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟡 | `4c77f21bd` | 2026-03-31 | Cross IA↔Back | Task #70 | Task #70: Round 3 fixes — followup chain tracking, inactivity-based timeout, A/B integration, route alias — - Follow-up chain tracking: SQL query now checks eng | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/main.py` |
| 🔴 | `67824f102` | 2026-03-31 | Cross Back↔Front | Task #70 | Task #70: Round 2 fixes — ECDSA webhook verification, 24h follow-up cadence, revert unrelated frontend changes — - Webhook signature: replaced HMAC-SHA256 with  | `lia-agent-system/app/api/v1/email_tracking.py`<br>`plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟡 | `fdd822852` | 2026-03-31 | Cross IA↔Back | Task #70 | Task #70: Code review fixes — webhook signature, Template Learning wiring, feedback state machine, consultant escalation — - Webhook signature verification: _ve | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/services/email_tracking_service.py` |
| 🔴 | `cefc6278c` | 2026-03-31 | Cross Back↔Front | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — - followup.process_pending: 7-day email follow-up for unopened WSI invites (I1) | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/services/email_tracking_service.py`<br>`plataforma-lia/src/components/candidate-preview/activities/ActivityFilters.tsx`<br>`plataforma-lia/src/components/candidate-preview/activities/ActivityTimeline.tsx` |
| 🔴 | `2d2c29b23` | 2026-03-31 | Cross Back↔Front | Candidates (FE pages) | chore: remove unused recommendation variable in _update_pipeline_stage | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageHeader.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🔴 | `0d0f056ef` | 2026-03-31 | Cross Back↔Front | Triagem (módulo) | fix(triagem): code review fixes — progress accuracy, pipeline status, stage counts — - Fix estimated_minutes_remaining: return 0 when no questions remain | `lia-agent-system/app/services/triagem_session_service.py` |
| 🔴 | `72c5d5ddc` | 2026-03-31 | Cross Back↔Front | Triagem (módulo) | feat(triagem): fix E2E flow — proxy POST bug, pipeline update, progress tracking — Task #69 Fase 2 — Chat Web Público + Triagem E2E: | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts` |
| 🔴 | `cfba6eddd` | 2026-03-31 | Cross Back↔Front | §9 Tenant Isolation / Multi-tenancy | fix(security): ephemeral HMAC secret + valid UUID fallback for company_id — - HMAC secret now uses cryptographic random if env var not set (with warning) | `lia-agent-system/app/api/v1/communication_optout.py`<br>`plataforma-lia/src/components/modals/edit-job-modal.tsx`<br>`plataforma-lia/src/components/modals/edit-job-sections/EditJobModalPrivacy.tsx`<br>`plataforma-lia/src/components/modals/edit-job-sections/EditJobModalRequirements.tsx`<br>`plataforma-lia/src/components/modals/edit-job-sections/index.ts` |
| 🟡 | `169755607` | 2026-03-31 | Cross IA↔Back | §9 Security / Tenant guards | fix(compliance): address code review — security + fairness enforcement — - JD generation: L1 blocked output now returns 422 (both main and fallback paths) | `lia-agent-system/app/api/v1/communication_optout.py`<br>`lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| 🟡 | `26c3b9a7a` | 2026-03-31 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(compliance): Fase 1 — FairnessGuard middleware + LGPD opt-out (A1-A4, G1, G2, I5) — - Created reusable FairnessGuard middleware (fairness_guard_middleware. | `lia-agent-system/app/api/v1/__init__.py`<br>`lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/communication_optout.py`<br>`lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py` |
| 🔴 | `c74ed63da` | 2026-03-25 | Cross IA↔Front | §15 WSI | Sprint WSI-10: F6.8 validation, F9-1 trait weighting, F10-6 confidence, F11-3 cache, F11-6 ranking — Backend: | `lia-agent-system/app/api/v1/wsi.py`<br>`lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/domains/cv_screening/constants/wsi_constants.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py` |
| 🔴 | `554b5925d` | 2026-03-25 | Cross IA↔Front | §15 WSI | Task #43: WSI Competency Minimums — Document + Platform Prompts + Pipeline — Changes: | `lia-agent-system/app/api/v1/wsi_questions.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_generator.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`<br>`lia-agent-system/app/domains/job_management/services/jd_enrichment_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_template_service.py` |
| 🔴 | `67d384e32` | 2026-03-25 | Cross IA↔Front | §15 WSI | Align WSI question counts with F5 methodology spec (7 compact, 12 full) — Backend (wsi_screening_pipeline.py): | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx` |
| 🔴 | `6b9944097` | 2026-03-25 | Cross IA↔Front | §15 WSI | Remove misplaced "Gerar Perguntas WSI" button from JDEvaluationPanel — The button was incorrectly placed on the JD description page. | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service.py`<br>`plataforma-lia/src/components/wsi/JDEvaluationPanel.tsx` |
| 🔴 | `8425b8eea` | 2026-03-25 | Cross Back↔Front | Triagem (módulo) | Task #41: Triagem details modal pixel-perfect mockup alignment — Backend (F11 endpoint): | `lia-agent-system/app/api/v1/wsi.py`<br>`plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🔴 | `06154d67a` | 2026-03-24 | Cross IA↔Front | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Changes in this session (completing previously-started work) | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🔴 | `35f05cf29` | 2026-03-24 | Cross IA↔Front | §15 WSI | Enhance job screening and publishing with improved WSI validation and feedback — Implement deterministic feedback generation for job applications and refine the | `lia-agent-system/app/api/v1/wsi.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`plataforma-lia/src/app/api/backend-proxy/wsi/f11-report/[sessionId]/route.ts`<br>`plataforma-lia/src/components/jobs/jobsPageConstants.tsx` |
| 🔴 | `f5ebbfdaf` | 2026-03-23 | Cross IA↔Front | §15 WSI | feat(wsi): unificação pipeline WSI — fonte única de verdade para perguntas de triagem — ## Objetivo | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service.py`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx` |
| 🔴 | `daf8552c1` | 2026-03-20 | Cross IA↔Front | Compliance / LGPD / EU AI Act | feat(fairness): Sprint FAR — Fairness Audit Remediation completo — FAR-1: 4 novas categorias bloqueadoras (antecedentes_criminais, saude_doenca, | `lia-agent-system/alembic/versions/048_add_soft_warnings_to_fairness_audit.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/api/v1/jd_import.py`<br>`lia-agent-system/app/domains/sourcing/services/pearch_service.py` |
| 🟡 | `00ce86b71` | 2026-03-19 | Cross IA↔Back | Sprint Z | code review: corrige 5 problemas identificados na sprint Z — - traces.py: substitui import de _otlp_active (privado) por is_otlp_active() pública | `lia-agent-system/app/api/v1/admin_dlq.py`<br>`lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/services/recruiter_behavior_service.py` |
| 🟡 | `39660c549` | 2026-03-19 | Cross IA↔Back | Privacy / PII (W7) | Z6-01 + Z6-02 + Z6-03 + Z7-01: observabilidade, PII NER e comportamento de recrutador — Z6-01 — Consolidação ATS clients: | `lia-agent-system/app/api/v1/recruiter_behavior.py`<br>`lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/__init__.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/base.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/gupy.py` |
| 🟡 | `0f71a4bc8` | 2026-03-19 | Cross IA↔Back | Policy / Job Creation | Z5-03 + Z5-02: threshold semântico configurável e consolidação PolicySetupAgent — Z5-03 — Threshold semântico: | `lia-agent-system/app/agents/policy_setup_agent.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/vector_semantic_cache.py` |
| 🔴 | `11d68f839` | 2026-03-19 | Cross IA↔Front | Tests (BE unit/integration) | Introduce specialized sourcing agents and improve model configurations — Add new sub-agents for sourcing tasks (planner, search, enrich, engagement) and update  | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/tenant_budget.py`<br>`plataforma-lia/src/app/api/backend-proxy/fairness-report/export/route.ts` |
| 🟡 | `8870cab97` | 2026-03-19 | Cross IA↔Back | Sourcing (BE) | Add specialized agents to improve candidate sourcing and management workflows — Introduce new sub-agents for sourcing planning, search, enrichment, and engageme | `lia-agent-system/app/orchestrator/fast_router.py`<br>`lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `ab285a555` | 2026-03-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | F1-02 + F1-03: FairnessGuard no learning loop e SLOs formais no circuit breaker — F1-02 — FairnessGuard no Learning Loop (LGPD / EU AI Act): | `lia-agent-system/app/api/v1/admin_circuit_breakers.py`<br>`lia-agent-system/app/shared/compliance/fairness_guard.py` |
| 🟡 | `3dceca5cc` | 2026-03-19 | Cross IA↔Back | Kanban (vagas) | Sprint Z1: Decomposição KanbanReActAgent e PipelineTransitionAgent em subagentes especializados — Z1-01 — KanbanReActAgent (23 tools) → 3 subagentes: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/orchestrated_job_chat.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/fast_router.py`<br>`lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🔴 | `620ef0b05` | 2026-03-15 | Cross IA↔Front | §8 Glossário / Production-Ready | Sprints Y1–Y5 completos + Diagnóstico v6: plataforma IA production-ready — ## Sprints Y1 (D1–D10) — Fundações e Observabilidade | `lia-agent-system/alembic/versions/041_add_agent_ragas_evaluations.py`<br>`lia-agent-system/alembic/versions/042_add_disparate_impact_to_snapshot.py`<br>`lia-agent-system/alembic/versions/043_add_candidate_consent_grants.py`<br>`lia-agent-system/alembic/versions/044_add_recruiter_decision_feedback.py`<br>`lia-agent-system/alembic/versions/045_add_domain_to_embeddings.py` |

_Total cross-cutting: **534 commits**._

---

## 5. Apêndice B — Auto-commits do Replit Agent

Commits mecânicos do Replit Agent: `Saved your changes...`, `Saved progress at the end of the loop`, `Git commit prior to merge`, `Transitioned from Plan to Build mode`. **Misturam várias mudanças** — abrir manualmente antes de cherry-pick.

_Total: **260 auto-commits**._

<details>
<summary>Lista (clique para expandir)</summary>

| SHA | Data | Subject | Arquivos | Camadas afetadas |
|---|---|---|---:|---|
| `745ce9d31` | 2026-04-29 | Saved your changes before starting work | 2 | other=1, backend_other=1 |
| `ac70f93a4` | 2026-04-29 | Git commit prior to merge | 6 | backend=3, backend_other=3 |
| `d20336c2e` | 2026-04-28 | Transitioned from Plan to Build mode | 0 | — |
| `70db3cd06` | 2026-04-28 | Git commit prior to merge | 1 | backend_other=1 |
| `6aeaa57a6` | 2026-04-28 | Git commit prior to merge | 1 | backend_other=1 |
| `b209a12fa` | 2026-04-28 | Git commit prior to merge | 8 | test=3, backend=2, other=1, frontend_ui=1 |
| `ddeb1eb92` | 2026-04-28 | Git commit prior to merge | 1 | other=1 |
| `43f62d263` | 2026-04-28 | Git commit prior to merge | 29 | frontend_ui=25, frontend_other=4 |
| `45a6c89c9` | 2026-04-28 | Git commit prior to merge | 1 | other=1 |
| `2abf85f6f` | 2026-04-28 | Git commit prior to merge | 1 | other=1 |
| `73a232a56` | 2026-04-28 | Transitioned from Plan to Build mode | 2 | backend_other=2 |
| `e5438af42` | 2026-04-27 | Git commit prior to merge | 7 | frontend_ui=5, frontend_other=2 |
| `a11a9cfc5` | 2026-04-27 | Git commit prior to merge | 0 | — |
| `4d19cf41c` | 2026-04-27 | Git commit prior to merge | 1 | backend_other=1 |
| `a318bb180` | 2026-04-27 | Git commit prior to merge | 1 | backend_other=1 |
| `fd8bd9ad8` | 2026-04-26 | Git commit prior to merge | 1 | docs=1 |
| `2adac0f2c` | 2026-04-26 | Git commit prior to merge | 5 | backend=4, test=1 |
| `f5cf05330` | 2026-04-26 | Git commit prior to merge | 1 | other=1 |
| `158ea11be` | 2026-04-26 | Git commit prior to merge | 1 | frontend_other=1 |
| `2f677eae0` | 2026-04-26 | Git commit prior to merge | 1 | other=1 |
| `590c55130` | 2026-04-26 | Git commit prior to merge | 1 | other=1 |
| `1960f4b62` | 2026-04-26 | Git commit prior to merge | 1 | other=1 |
| `a7fcf5a5d` | 2026-04-26 | Transitioned from Plan to Build mode | 0 | — |
| `48944aaac` | 2026-04-26 | Git commit prior to merge | 1 | backend_other=1 |
| `eba25ca5a` | 2026-04-26 | Git commit prior to merge | 1 | backend_other=1 |
| `52e7da6f8` | 2026-04-26 | Git commit prior to merge | 19 | docs=13, other=6 |
| `1452d9473` | 2026-04-25 | Transitioned from Plan to Build mode | 0 | — |
| `698afe531` | 2026-04-25 | Transitioned from Plan to Build mode | 1 | backend_other=1 |
| `d6644982b` | 2026-04-23 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `6f57b3d65` | 2026-04-23 | Git commit prior to merge | 15 | backend_other=8, docs=6, other=1 |
| `f7627f1bf` | 2026-04-23 | Saved progress at the end of the loop | 2758 | other=1898, docs=244, frontend_ui=145, backend_other=132 |
| `8237e5cb6` | 2026-04-23 | Transitioned from Plan to Build mode | 2 | other=1, backend_other=1 |
| `fc5ba84eb` | 2026-04-22 | Transitioned from Plan to Build mode | 1 | backend_other=1 |
| `906749f22` | 2026-04-22 | Git commit prior to merge | 2 | docs=1, backend_other=1 |
| `4af7cf447` | 2026-04-22 | Transitioned from Plan to Build mode | 0 | — |
| `b89052761` | 2026-04-22 | Transitioned from Plan to Build mode | 110 | other=89, frontend_ui=10, docs=5, backend_other=2 |
| `1caeee4bc` | 2026-04-21 | Git commit prior to merge | 2 | other=1, frontend_ui=1 |
| `27ea118b4` | 2026-04-21 | Transitioned from Plan to Build mode | 0 | — |
| `7a5142db5` | 2026-04-21 | Git commit prior to merge | 2 | other=1, docs=1 |
| `311e74269` | 2026-04-21 | Git commit prior to merge | 1 | other=1 |
| `68bef95bf` | 2026-04-21 | Git commit prior to merge | 1 | docs=1 |
| `66343bef5` | 2026-04-21 | Git commit prior to merge | 1 | backend_other=1 |
| `6fdc3e93c` | 2026-04-21 | Git commit prior to merge | 8 | frontend_ui=7, frontend_other=1 |
| `ae56c0d2d` | 2026-04-21 | Git commit prior to merge | 1 | frontend_ui=1 |
| `023148bc3` | 2026-04-21 | Git commit prior to merge | 3 | ai=2, test=1 |
| `1725eb5ad` | 2026-04-21 | Git commit prior to merge | 2 | ai=1, test=1 |
| `6ca89c4b3` | 2026-04-21 | Git commit prior to merge | 1 | other=1 |
| `604438485` | 2026-04-21 | Saved your changes before starting work | 4 | backend=2, backend_other=1, ai=1 |
| `1a5f22d5c` | 2026-04-21 | Transitioned from Plan to Build mode | 0 | — |
| `fe94359d1` | 2026-04-20 | Transitioned from Plan to Build mode | 0 | — |
| `cbd2fc899` | 2026-04-20 | Git commit prior to merge | 2 | other=1, backend_other=1 |
| `8212c96e5` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `d2772e782` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `62c5689c4` | 2026-04-20 | Git commit prior to merge | 5 | backend_other=4, other=1 |
| `3897bc42a` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `0b3caa28c` | 2026-04-20 | Git commit prior to merge | 10 | backend_other=8, test=2 |
| `be607d82a` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `591441554` | 2026-04-20 | Git commit prior to merge | 2 | test=2 |
| `e5a0787aa` | 2026-04-20 | Transitioned from Plan to Build mode | 4 | ai=3, test=1 |
| `bd5a3c442` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `0f1a21dde` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `e8e162949` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `c78584eb1` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `3ddf714a8` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `a8091fb14` | 2026-04-20 | Transitioned from Plan to Build mode | 1 | other=1 |
| `d64e9bfd8` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `193ffe0c4` | 2026-04-20 | Git commit prior to merge | 3 | backend_other=3 |
| `c4c5c8609` | 2026-04-20 | Git commit prior to merge | 1 | other=1 |
| `a2b5eb13a` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `e746f47b6` | 2026-04-20 | Saved progress at the end of the loop | 0 | — |
| `3ff9c7f1c` | 2026-04-20 | Saved your changes before starting work | 3 | other=3 |
| `ef40db8ce` | 2026-04-20 | Git commit prior to merge | 1 | ai=1 |
| `bbc56ebcb` | 2026-04-20 | Git commit prior to merge | 1 | backend_other=1 |
| `860d1b3fa` | 2026-04-19 | Git commit prior to merge | 6 | backend_other=3, ai=2, other=1 |
| `de09438ec` | 2026-04-19 | Git commit prior to merge | 2 | other=1, backend_other=1 |
| `fe47e4d0d` | 2026-04-19 | Git commit prior to merge | 1 | other=1 |
| `7bef1cb42` | 2026-04-19 | Git commit prior to merge | 4 | frontend_other=2, backend_other=1, frontend_ui=1 |
| `da11f25c7` | 2026-04-19 | Git commit prior to merge | 4 | backend_other=2, ai=2 |
| `30c51681f` | 2026-04-19 | Git commit prior to merge | 2 | frontend_ui=2 |
| `3db413278` | 2026-04-19 | Git commit prior to merge | 24 | backend_other=12, backend=8, ai=2, test=1 |
| `3690c9fb4` | 2026-04-19 | Transitioned from Plan to Build mode | 3 | ai=3 |
| `3d79832a9` | 2026-04-19 | Git commit prior to merge | 6 | backend=4, ai=2 |
| `58009608b` | 2026-04-19 | Saved your changes before starting work | 2 | ai=2 |
| `683a3c155` | 2026-04-19 | Git commit prior to merge | 1 | ai=1 |
| `2dcd28894` | 2026-04-19 | Git commit prior to merge | 15 | backend_other=9, ai=6 |
| `3af295565` | 2026-04-19 | Transitioned from Plan to Build mode | 0 | — |
| `77247d615` | 2026-04-19 | Git commit prior to merge | 1 | backend_other=1 |
| `d924e5557` | 2026-04-19 | Git commit prior to merge | 1 | backend_other=1 |
| `a4b1db2d1` | 2026-04-19 | Git commit prior to merge | 5 | ai=4, backend_other=1 |
| `fbbb6ea9b` | 2026-04-19 | Git commit prior to merge | 2 | backend_other=2 |
| `e054c2258` | 2026-04-19 | Transitioned from Plan to Build mode | 1 | backend_other=1 |
| `1a504eb80` | 2026-04-18 | Transitioned from Plan to Build mode | 0 | — |
| `ac98500e9` | 2026-04-18 | Git commit prior to merge | 2 | backend_other=2 |
| `3b65a4917` | 2026-04-18 | Git commit prior to merge | 1 | ai=1 |
| `4f9ffd248` | 2026-04-18 | Transitioned from Plan to Build mode | 4 | ai=2, backend=1, backend_other=1 |
| `a3099a0a5` | 2026-04-18 | Git commit prior to merge | 2 | backend_other=2 |
| `1b7419206` | 2026-04-18 | Git commit prior to merge | 1 | backend_other=1 |
| `da3a119f8` | 2026-04-18 | Git commit prior to merge | 4 | docs=3, other=1 |
| `664295002` | 2026-04-18 | Transitioned from Plan to Build mode | 3 | ai=2, other=1 |
| `ea408d22f` | 2026-04-18 | Git commit prior to merge | 1 | backend_other=1 |
| `14f477e80` | 2026-04-18 | Git commit prior to merge | 1 | ai=1 |
| `1649572a2` | 2026-04-18 | Git commit prior to merge | 1 | ai=1 |
| `92c4c225c` | 2026-04-18 | Git commit prior to merge | 1 | ai=1 |
| `a5bf880ed` | 2026-04-18 | Git commit prior to merge | 3 | ai=3 |
| `eb55beb1c` | 2026-04-18 | Git commit prior to merge | 1 | backend=1 |
| `4d38f7660` | 2026-04-18 | Git commit prior to merge | 1 | other=1 |
| `9df37e306` | 2026-04-18 | Transitioned from Plan to Build mode | 1 | other=1 |
| `e3f01c680` | 2026-04-18 | Git commit prior to merge | 5 | ai=4, backend_other=1 |
| `80e1e37fd` | 2026-04-18 | Git commit prior to merge | 6 | backend_other=2, other=1, ai=1, frontend_ui=1 |
| `6440b7208` | 2026-04-18 | Git commit prior to merge | 3 | backend_other=3 |
| `ebc5d3b18` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `d9cdd3a34` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `2a7deda3d` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `becd9b863` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `bade39415` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `60d3c6e2f` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `13d67609b` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `05d37b778` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `9a812858e` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `484b467f7` | 2026-04-17 | Transitioned from Plan to Build mode | 3 | backend_other=2, other=1 |
| `140ff37ae` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `d96da8949` | 2026-04-17 | Git commit prior to merge | 1 | backend=1 |
| `7a7bfaa05` | 2026-04-17 | Transitioned from Plan to Build mode | 0 | — |
| `bf16a8bbd` | 2026-04-17 | Git commit prior to merge | 1 | ai=1 |
| `6d66f03eb` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `909f9ee74` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `e6bbc82b3` | 2026-04-17 | Git commit prior to merge | 2 | other=1, test=1 |
| `495fda344` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `44fef6818` | 2026-04-17 | Git commit prior to merge | 1 | test=1 |
| `72bb74218` | 2026-04-17 | Git commit prior to merge | 1 | other=1 |
| `469ee0565` | 2026-04-17 | Git commit prior to merge | 2 | test=2 |
| `34cf27270` | 2026-04-17 | Git commit prior to merge | 2 | test=2 |
| `8e9182676` | 2026-04-17 | Git commit prior to merge | 2 | test=2 |
| `3d357e5a8` | 2026-04-16 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `d4857587c` | 2026-04-16 | Transitioned from Plan to Build mode | 0 | — |
| `9ae0178b3` | 2026-04-16 | Git commit prior to merge | 1 | other=1 |
| `b53a2b1b0` | 2026-04-16 | Git commit prior to merge | 1 | other=1 |
| `75c33db80` | 2026-04-16 | Git commit prior to merge | 1 | other=1 |
| `934fcd82d` | 2026-04-16 | Transitioned from Plan to Build mode | 0 | — |
| `91b32f5aa` | 2026-04-16 | Transitioned from Plan to Build mode | 1 | other=1 |
| `acbcecea2` | 2026-04-16 | Git commit prior to merge | 1 | other=1 |
| `7989dc7ed` | 2026-04-16 | Git commit prior to merge | 1 | other=1 |
| `024f1cd8a` | 2026-04-15 | Transitioned from Plan to Build mode | 0 | — |
| `7a1b8dcbb` | 2026-04-15 | Git commit prior to merge | 1 | other=1 |
| `3659c2a2e` | 2026-04-14 | Git commit prior to merge | 1 | docs=1 |
| `604a095e3` | 2026-04-13 | Git commit prior to merge | 1 | other=1 |
| `2ede4aae7` | 2026-04-13 | Git commit prior to merge | 2 | backend=2 |
| `7faa5fe66` | 2026-04-12 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `ebe9185c2` | 2026-04-12 | Transitioned from Plan to Build mode | 0 | — |
| `e08b06f04` | 2026-04-12 | Git commit prior to merge | 1 | other=1 |
| `8984b6054` | 2026-04-11 | Git commit prior to merge | 1 | other=1 |
| `83ff514e0` | 2026-04-11 | Git commit prior to merge | 1 | other=1 |
| `e139479b8` | 2026-04-11 | Transitioned from Plan to Build mode | 0 | — |
| `989d6af6c` | 2026-04-11 | Transitioned from Plan to Build mode | 0 | — |
| `cf7176ff4` | 2026-04-11 | Git commit prior to merge | 1 | other=1 |
| `49e7b8778` | 2026-04-11 | Transitioned from Plan to Build mode | 0 | — |
| `75a3e49ae` | 2026-04-11 | Git commit prior to merge | 1 | other=1 |
| `03941fd48` | 2026-04-11 | Git commit prior to merge | 2 | test=2 |
| `d5fe5ef85` | 2026-04-11 | Transitioned from Plan to Build mode | 1 | other=1 |
| `b180e9c85` | 2026-04-11 | Git commit prior to merge | 1 | other=1 |
| `828cd47c5` | 2026-04-10 | Git commit prior to merge | 1 | other=1 |
| `feb6757a3` | 2026-04-10 | Transitioned from Plan to Build mode | 0 | — |
| `7ed6d449f` | 2026-04-10 | Git commit prior to merge | 1 | other=1 |
| `82011d72a` | 2026-04-09 | Transitioned from Plan to Build mode | 0 | — |
| `442e91d6c` | 2026-04-09 | Transitioned from Plan to Build mode | 0 | — |
| `2ee1a29df` | 2026-04-08 | Git commit prior to merge | 1 | backend_other=1 |
| `e60f50780` | 2026-04-08 | Transitioned from Plan to Build mode | 3 | frontend_ui=2, frontend_other=1 |
| `d8f4673fe` | 2026-04-08 | Git commit prior to merge | 45 | backend=31, ai=11, test=2, backend_other=1 |
| `dee51c2cb` | 2026-04-07 | Transitioned from Plan to Build mode | 0 | — |
| `cbfecbc59` | 2026-04-07 | Git commit prior to merge | 6 | backend=5, other=1 |
| `7a2482c82` | 2026-04-07 | Git commit prior to merge | 1 | other=1 |
| `8cb2b7286` | 2026-04-07 | Git commit prior to merge | 1 | other=1 |
| `88cc4c7a7` | 2026-04-07 | Git commit prior to merge | 1 | other=1 |
| `2b25f6824` | 2026-04-07 | Git commit prior to merge | 1 | other=1 |
| `26891a6bc` | 2026-04-07 | Git commit prior to merge | 1 | other=1 |
| `a9d3ae4cb` | 2026-04-07 | Git commit prior to merge | 52 | backend=48, backend_other=3, other=1 |
| `b7b29ae37` | 2026-04-07 | Git commit prior to merge | 7 | frontend_ui=5, other=1, frontend_other=1 |
| `f8ea7b63b` | 2026-04-06 | Git commit prior to merge | 3 | frontend_ui=2, frontend_other=1 |
| `c1cbfa812` | 2026-04-06 | Git commit prior to merge | 3 | frontend_other=2, other=1 |
| `e0e0dee7b` | 2026-04-06 | Saved progress at the end of the loop | 1 | backend_other=1 |
| `b238a18c9` | 2026-04-06 | Git commit prior to merge | 12 | frontend_ui=12 |
| `ab55c549b` | 2026-04-06 | Git commit prior to merge | 182 | backend=171, ai=5, backend_other=3, test=2 |
| `eb0dfa80e` | 2026-04-06 | Git commit prior to merge | 4 | backend=4 |
| `6a4c33b52` | 2026-04-06 | Git commit prior to merge | 422 | backend=291, backend_other=92, ai=31, test=8 |
| `1699cabcf` | 2026-04-06 | Git commit prior to merge | 5 | backend=4, backend_other=1 |
| `25cdcdfd7` | 2026-04-06 | Transitioned from Plan to Build mode | 47 | backend_other=35, backend=6, test=3, docs=2 |
| `18602a9d2` | 2026-04-06 | Git commit prior to merge | 18 | backend=16, ai=1, backend_other=1 |
| `567f73d38` | 2026-04-06 | Git commit prior to merge | 1 | other=1 |
| `2ae4c5ff3` | 2026-04-06 | Git commit prior to merge | 9 | frontend_ui=8, other=1 |
| `ebf34877d` | 2026-04-06 | Transitioned from Plan to Build mode | 0 | — |
| `5b39c0dad` | 2026-04-06 | Git commit prior to merge | 2 | other=1, test=1 |
| `9d1d3eabd` | 2026-04-06 | Git commit prior to merge | 1 | frontend_other=1 |
| `51eb73d08` | 2026-04-06 | Transitioned from Plan to Build mode | 0 | — |
| `9441593dc` | 2026-04-05 | Transitioned from Plan to Build mode | 0 | — |
| `e26a7e8f0` | 2026-04-05 | Git commit prior to merge | 2 | backend=1, backend_other=1 |
| `7dbc57a4c` | 2026-04-05 | Git commit prior to merge | 6 | backend=5, backend_other=1 |
| `77b972560` | 2026-04-05 | Git commit prior to merge | 4 | frontend_ui=3, frontend_other=1 |
| `8631ac9ad` | 2026-04-05 | Transitioned from Plan to Build mode | 0 | — |
| `164bab9ba` | 2026-04-05 | Git commit prior to merge | 1 | other=1 |
| `5047e550d` | 2026-04-05 | Transitioned from Plan to Build mode | 0 | — |
| `5ca446df4` | 2026-04-05 | Git commit prior to merge | 7 | frontend_ui=3, other=2, frontend_other=1, docs=1 |
| `2d0ac4213` | 2026-04-05 | Git commit prior to merge | 1 | other=1 |
| `4ba70b393` | 2026-04-05 | Transitioned from Plan to Build mode | 9 | test=5, backend=3, backend_other=1 |
| `7c605d0f3` | 2026-04-04 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `3b562e758` | 2026-04-04 | Git commit prior to merge | 2 | backend=2 |
| `12fb46883` | 2026-04-04 | Git commit prior to merge | 7 | backend=4, ai=2, test=1 |
| `afaeb4fa7` | 2026-04-04 | Git commit prior to merge | 10 | backend=6, ai=3, backend_other=1 |
| `14d8e5fde` | 2026-04-04 | Git commit prior to merge | 8 | backend=5, backend_other=2, docs=1 |
| `0eb9f2427` | 2026-04-04 | Transitioned from Plan to Build mode | 0 | — |
| `9ae930c18` | 2026-04-04 | Git commit prior to merge | 1 | ai=1 |
| `b4a2a95dd` | 2026-04-04 | Git commit prior to merge | 2 | other=1, backend_other=1 |
| `b9ece1589` | 2026-04-04 | Git commit prior to merge | 1 | other=1 |
| `9b9a5d840` | 2026-04-04 | Git commit prior to merge | 21 | other=20, frontend_other=1 |
| `31006178a` | 2026-04-04 | Git commit prior to merge | 1 | ai=1 |
| `a6c85b154` | 2026-04-04 | Git commit prior to merge | 1 | backend=1 |
| `e48e1a3f6` | 2026-04-04 | Transitioned from Plan to Build mode | 1 | frontend_other=1 |
| `f42e499b7` | 2026-04-04 | Git commit prior to merge | 2 | backend=1, frontend_other=1 |
| `44320314c` | 2026-04-04 | Git commit prior to merge | 7 | frontend_ui=7 |
| `43b7d5eed` | 2026-04-03 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `f9471e961` | 2026-04-03 | Git commit prior to merge | 3 | docs=2, frontend_other=1 |
| `6698b6083` | 2026-04-02 | Saved your changes before starting work | 2 | docs=2 |
| `9913729ba` | 2026-04-02 | Transitioned from Plan to Build mode | 0 | — |
| `c7b57ee2f` | 2026-04-01 | Transitioned from Plan to Build mode | 7 | frontend_ui=7 |
| `7081386fa` | 2026-04-01 | Transitioned from Plan to Build mode | 24 | frontend_ui=23, other=1 |
| `65aa73180` | 2026-04-01 | Transitioned from Plan to Build mode | 16 | frontend_ui=14, other=2 |
| `4573d85da` | 2026-03-31 | Transitioned from Plan to Build mode | 9 | frontend_ui=9 |
| `cfb058ab4` | 2026-03-31 | Transitioned from Plan to Build mode | 20 | frontend_ui=17, other=2, frontend_other=1 |
| `71cf79d1f` | 2026-03-31 | Git commit prior to merge | 3 | frontend_ui=3 |
| `3ee4d890b` | 2026-03-31 | Git commit prior to merge | 1 | backend=1 |
| `eaae68982` | 2026-03-31 | Git commit prior to merge | 2 | frontend_ui=2 |
| `9ea81e33e` | 2026-03-31 | Transitioned from Plan to Build mode | 13 | frontend_ui=13 |
| `1568d6c91` | 2026-03-31 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `2d1ccce82` | 2026-03-30 | Transitioned from Plan to Build mode | 10 | frontend_ui=10 |
| `42cc398b6` | 2026-03-30 | Git commit prior to merge | 24 | frontend_ui=24 |
| `24cbdc4fd` | 2026-03-30 | Git commit prior to merge | 1 | frontend_other=1 |
| `90f4c28ab` | 2026-03-30 | Saved progress at the end of the loop | 1 | frontend_other=1 |
| `fbe0cab58` | 2026-03-30 | Git commit prior to merge | 298 | frontend_ui=285, test=8, frontend_other=5 |
| `dd4b07950` | 2026-03-30 | Saved progress at the end of the loop | 1202 | frontend_ui=1178, frontend_other=15, docs=7, other=2 |
| `bdc97e897` | 2026-03-29 | Saved progress at the end of the loop | 3 | docs=2, frontend_ui=1 |
| `a2421434e` | 2026-03-29 | Transitioned from Plan to Build mode | 1 | frontend_ui=1 |
| `4e4c43cb4` | 2026-03-28 | Transitioned from Plan to Build mode | 64546 | frontend_ui=20027, backend=16358, backend_other=8800, test=6698 |
| `ca7e87e04` | 2026-03-27 | Saved progress at the end of the loop | 32099 | frontend_ui=9854, backend=8179, backend_other=4400, test=3349 |
| `147207344` | 2026-03-27 | Transitioned from Plan to Build mode | 0 | — |
| `deeb59592` | 2026-03-26 | Saved progress at the end of the loop | 173 | docs=172, infra=1 |
| `ba2a3654d` | 2026-03-25 | Transitioned from Plan to Build mode | 1 | docs=1 |
| `5138d045a` | 2026-03-24 | Transitioned from Plan to Build mode | 0 | — |
| `ec78017b6` | 2026-03-24 | Transitioned from Plan to Build mode | 0 | — |
| `fb9b1b536` | 2026-03-23 | Transitioned from Plan to Build mode | 0 | — |
| `c48a61f53` | 2026-03-22 | Saved your changes before starting work | 1 | other=1 |
| `a8d73e15b` | 2026-03-22 | Transitioned from Plan to Build mode | 0 | — |
| `c64c83ff0` | 2026-03-21 | Transitioned from Plan to Build mode | 0 | — |
| `75631f4fb` | 2026-03-20 | Git commit prior to merge | 1 | docs=1 |
| `c58e40130` | 2026-03-20 | Transitioned from Plan to Build mode | 0 | — |
| `600d8c01f` | 2026-03-19 | Transitioned from Plan to Build mode | 1 | docs=1 |
| `47f562e3a` | 2026-03-19 | Transitioned from Plan to Build mode | 0 | — |
| `7cb0f5a79` | 2026-03-19 | Saved progress at the end of the loop | 21319 | frontend_ui=6564, backend=5452, backend_other=2932, test=2224 |
| `d9ebbc562` | 2026-03-18 | Transitioned from Plan to Build mode | 0 | — |
| `19ae49aa0` | 2026-03-18 | Transitioned from Plan to Build mode | 0 | — |
| `62e98db51` | 2026-03-16 | Transitioned from Plan to Build mode | 0 | — |
| `a7e0d4dd1` | 2026-03-15 | Saved progress at the end of the loop | 7000 | frontend_ui=2181, backend=1794, backend_other=956, test=694 |

</details>

---

## 6. Apêndice C — Lista cronológica completa (mais novo → mais antigo)

Todos os 3.491 commits no período, em ordem cronológica.

<details>
<summary>Expandir lista completa</summary>

| Risco | SHA | Data | Camada | Feature | O que faz |
|:---:|---|---|---|---|---|
| 🟢 | `d673198c7` | 2026-04-29 | Frontend (UI) | Menu Rename + Visão Global | feat(pipeline-overview): rename Visão do Pipeline → Visão Global, invert tab order, default 'vagas' — Cabeçalho renomeado, abas reordenadas (Vagas \| Candidatos), default do store passa para 'vagas' |
| 🟢 | `6b87a793c` | 2026-04-29 | Frontend (UI) | Menu Rename + Visão Global | feat(sidebar): rename and restructure lateral menu per fork design — Task #941. Chat LIA→Conversar, Tarefas→Decidir, Recrutar como pai expansível com Vagas + Funil de Talentos. Inclui shims de retrocompat |
| 🟡 | `2774dea0b` | 2026-04-29 | Frontend (UI) | Tests (FE e2e) | Add testing for new review panel and update helper functions — Add a data-testid to the review panel |
| 🟡 | `745ce9d31` | 2026-04-29 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🟢 | `2e07b3ef5` | 2026-04-29 | Docs | Wizard/Onda 36 | docs(branch-map): Onda 36 — P0 tenant guards settings_progress + integrations_hub — Documenta: |
| 🟡 | `78ced6508` | 2026-04-29 | Backend | Wizard/Onda 36 | fix(security): Onda 36 — P0 tenant guards em settings_progress + integrations_hub — Bugs descobertos |
| 🟡 | `9e62596c5` | 2026-04-29 | Backend | §17 Eval Framework | Add comprehensive tests for alert configuration and preferences — Update test coverage for alert con |
| 🟢 | `8e69d85d7` | 2026-04-29 | Frontend (api/util) | §4 Rail Features — Rail A | test(rail-a): 33/33 E2E passando — fix snapshot timeouts + 3 NAVIGATION->CHAT — Fixes para 33/33 tes |
| 🟡 | `fa2af2991` | 2026-04-29 | Frontend (UI) | Wizard/Onda 33 | feat(wizard-ux): Onda 33 — limpa cirurgica + port de 2 features — Audit comparativo (plataforma-lia/ |
| 🟢 | `52b765969` | 2026-04-29 | Testes | Wizard (geral) | Compare wizard panel implementations and suggest consolidation — Compares current and new wizard pan |
| 🟢 | `b12753549` | 2026-04-29 | Frontend (UI) | Wizard (geral) | Update chat tests to use stable element selectors — Refactor end-to-end chat tests to utilize `data- |
| 🟡 | `dca7d0372` | 2026-04-29 | Testes | Tests (FE e2e) | Update end-to-end tests for improved navigation and element stability — Refactor Playwright tests to |
| 🟢 | `b2b268caf` | 2026-04-29 | Docs | Wizard/Onda 31 | docs(branch-map): Onda 31 — P0 tasks.py + Big Five catalog cleanup — Documenta: |
| 🟢 | `d0245efb9` | 2026-04-29 | Testes | §4 Rail Features — Rail A | Add end-to-end tests for interactive chat cards — Add new end-to-end tests for the 'Rail A' chat car |
| 🟡 | `4a28a1f6a` | 2026-04-29 | Backend | Wizard/Onda 31.2 | feat(cleanup): Onda 31.2 — delete orphan Big Five/Technical questions catalog — Catalogo company_ass |
| 🟡 | `bec3b2ad3` | 2026-04-29 | Backend | Task #936 | Fix HTTP 500 on stage-transition substatus-options endpoint (Task #936) — Original task: GET /api/v1 |
| 🟡 | `be2ee3148` | 2026-04-29 | Backend | Task #935 | Fix 500 on PUT /admin/llm-config (Task #935) — Original task: Toda chamada PUT /admin/llm-config ret |
| 🟡 | `ac70f93a4` | 2026-04-29 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `acc4a4e41` | 2026-04-29 | Testes | Configurações (hub) | test(api/v1): expand Configurações backend coverage 14/24 → 24/24 (Task #930) — Adiciona 9 arquivos  |
| 🟡 | `afe709945` | 2026-04-29 | Backend | Configurações (hub) | Task #930 — Configurações Fase 3: cobertura backend 14/24 → 24/24 — Adiciona 9 arquivos novos em lia |
| 🟢 | `3c7b44e89` | 2026-04-29 | Frontend (UI) | §4 Rail Features — Rail A | refactor(rail-a): PR-H+PR-L — canonical stages + DS color-mix tokens — PR-H: remove STAGE_STRUCTURES |
| 🟢 | `6964ece62` | 2026-04-29 | Frontend (UI) | Configurações (hub) | Configurações Fase 3 — polir UI, proxy e DS v4.2.2 (Task #929) — Housekeeping no menu Configurações  |
| 🟢 | `906179a75` | 2026-04-29 | Frontend (UI) | Configurações (hub) | chore(settings): commit residual WorkforceHubContent.tsx |
| 🟢 | `1e52196c4` | 2026-04-29 | Docs | §2 Orchestrator Migration | docs(nav): BRANCH_MAP — registro do merge feat/orch-migration-sprint-I -> main |
| 🟢 | `ec0657d80` | 2026-04-29 | Empty/merge | §2 Orchestrator Migration | merge: feat/orch-migration-sprint-I — Rail A sprint completo — Waves 0-4 do Rail A audit (22 cards × |
| 🟡 | `844a3aa76` | 2026-04-29 | Frontend (UI) | Configurações (hub) | chore(settings): commit pendente — cleanup residual das sessoes de settings audit |
| 🟢 | `832bedd3f` | 2026-04-29 | Docs | Wizard/Onda 25 | docs(nav): BRANCH_MAP — Onda 25 PR-G + sprint completo 130/130 testes — Sprint feat/orch-migration-s |
| 🟡 | `0569b325b` | 2026-04-29 | IA | §4 Rail Features — PR-G | fix(pr-g): delete dead hitl_service shim, 8/8 canonical sensors green — canonical-fix: app.shared.se |
| 🟡 | `477eae94a` | 2026-04-29 | Frontend (UI) | Configurações (hub) | chore(settings): #928 housekeeping — apiFetch em fetches remanescentes (T6/D-4) — Pivot do session_p |
| 🟢 | `ed41d7309` | 2026-04-28 | Docs | Configurações (hub) | Update design token version and fix tracker syntax in settings — Update design token version from v4 |
| 🔴 | `b4753d320` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | audit configurações fase 3 — task #927 quick wins + bonus T5/T6 da sessão — a11y CRITICAL nos 7 hubs |
| 🟡 | `d20336c2e` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `7088a0c0e` | 2026-04-28 | Docs | Wizard/Onda 30 | docs(branch-map): Onda 30 — wizard enterprise closure (6 itens) — Documenta fechamento da auditoria  |
| 🟡 | `c35035649` | 2026-04-28 | Frontend (UI) | Unified Chat (FE) | Add functionality for selecting and displaying pipeline templates — Integrates a new component for s |
| 🔴 | `e0fb295b9` | 2026-04-28 | Cross Back↔Front | Job Management (BE) | Enhance salary suggestions with ATS job history and refine task display — Integrate ATS job history  |
| 🟡 | `03fbf3841` | 2026-04-28 | Backend | §9 Security / Tenant guards | Add authentication and authorization checks to API endpoints — Update API endpoints in multiple modu |
| 🟢 | `3157b37b9` | 2026-04-28 | Docs | Wizard/Onda 24 | docs(nav): BRANCH_MAP — Onda 24 PR-CAL scheduling MVP 14/14 tests |
| 🟡 | `3e1ae39c5` | 2026-04-28 | Backend | Scheduling / Calendar (PR-CAL) | feat(pr-cal): scheduling MVP — DB write, no fake links, reschedule update, 14/14 tests — Wave 4 — PR |
| 🟢 | `b3a217c27` | 2026-04-28 | Docs | Wizard/Onda 23 | docs(nav): BRANCH_MAP Onda 23 Wave 2-4 audit, 119 tests green |
| 🟢 | `dabb5c4d4` | 2026-04-28 | Docs | Wizard/Onda 22-28 | docs(branch-map): Ondas 22-28 — wizard enterprise readiness complete — Documenta 7 ondas de trabalho |
| 🟡 | `be172b778` | 2026-04-28 | IA | §4 Rail Features — PR-HIRE (register_hire) | feat(capability-map): add send_offer + register_hire, Wave 4, 27/27 tests green |
| 🟢 | `731a61e8a` | 2026-04-28 | Testes | scope: tenant-scope | test(tenant-scope): fix 5 no_auth_returns_401 tests to patch _is_dev_environment — Tests now simulat |
| 🟢 | `566d1ac89` | 2026-04-28 | Testes | Automations | test(automations): fix MESSAGES namespace automations -> automationsTab, 7/7 green |
| 🟢 | `07d1eb0af` | 2026-04-28 | Frontend (UI) | Wizard/Onda 28 | feat(wizard-ux): Onda 28 — E.5 TaskContextBar, E.6 chips contextuais, E.8 template UI — - TaskContex |
| 🟢 | `6916d13b4` | 2026-04-28 | Testes | Offer Review (PR-B) | test: offer modal HITL two-step test fixes (18/18 passing) |
| 🟢 | `05ccd6fcc` | 2026-04-28 | Frontend (UI) | Wizard/Onda 26-27 | feat(wizard-ux): Onda 26-27 — E.1 wizard_step_response wiring, E.2-E.4 Tezi panels — E.1/E.7 useWiza |
| 🔴 | `28c20b355` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | Configurações Fase 2.5: fechamento das pendências do audit 28/abr/2026 — Aplicadas as skills canonic |
| 🟡 | `5727f7432` | 2026-04-28 | Backend | Wizard/Onda 25 | feat(wizard): Onda 25 — C.5 templates, F.1 ats_job_history, F.2 screening_mode |
| 🟢 | `64b1cdcaf` | 2026-04-28 | Docs | Wizard/Onda 22 | docs(nav): BRANCH_MAP — Onda 22 Wave 5 sensors offer FE invariants 10/10 |
| 🟡 | `4e6374302` | 2026-04-28 | Frontend (UI) | Offer Review (PR-B) | feat(offer): Wave 5 sensors — HITL banner, aria-invalid, reset/devtools, flow — - OfferHITLBanner.ts |
| 🟡 | `7a0d9ab79` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 24 | feat(wizard): Onda 24 — C.3 perguntas explícitas recrutador (seniority + WSI mode + calibração) — C. |
| 🟡 | `bdb0cf8d2` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 23 | feat(wizard): Onda 23 — C.1 WsiQuestionGenerator + C.2 JdEnrichmentService canônicos — C.1 stage_wsi |
| 🟡 | `e74aff11b` | 2026-04-28 | Backend | Wizard/Onda 22 | feat(wizard): Onda 22 — Frente A tenant guards P0, Frente B cleanup, Frente D Pydantic validators —  |
| 🟡 | `b3bed4f77` | 2026-04-28 | Outro | Mockup Sandbox (artefato gerado) | Add new screens for triagem flow to the mockup components — Update mockup-components.ts to include n |
| 🟢 | `fd573e867` | 2026-04-28 | Docs | §13 PARTE D — Proatividade | docs(handoff): add comprehensive PT-BR handoff for LIA's proactive AI layer — Task #911 — single exh |
| 🟡 | `a490827f2` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Translate Settings screens + locale-aware seed data (incl. recruitment/) — Task #923 — make platafor |
| 🟡 | `70db3cd06` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `6ab1a6172` | 2026-04-28 | Docs | Wizard/Onda 18-21 | docs(nav): BRANCH_MAP fix Ondas 18-21 table cells backtick escape |
| 🟡 | `64728b8f1` | 2026-04-28 | Cross IA↔Back | Wizard/Onda 18-21 | feat(wizard): Ondas 18-21 — apply_learning nos stages, pick_canonical salary, wizard_step_response m |
| 🔴 | `d6a8d109c` | 2026-04-28 | Cross Back↔Front | Configurações (hub) | i18n(settings): translate Configurações to English (Task #919) — Translated hardcoded PT strings to  |
| 🟡 | `6aeaa57a6` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `45e562148` | 2026-04-28 | Docs | Configurações (hub) | Task #918: Encerrar Lotes 4b/4c/4e/4f da auditoria de Configurações — Original task: remover o resta |
| 🟡 | `6d86c44d9` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Task #904: Governança section in Configurações (rev 3 — backend contract alignment) — Adds a 6-panel |
| 🟢 | `34e2de8ba` | 2026-04-28 | Docs | Configurações (hub) | Documentar arquitetura final do menu Configurações (Task #903) — Atualiza memória persistente do pro |
| 🟡 | `59eaac588` | 2026-04-28 | Frontend (UI) | Configurações (hub) | i18n: lift settings/ coverage to 42% across 5 hubs — Task #901 — added next-intl coverage to the 5 s |
| 🟡 | `107ac9e76` | 2026-04-28 | Frontend (UI) | Configurações (hub) | T902: split settings monoliths and remove `: any` / `as any` — BenefitsTab.tsx (715 → 189 LoC orches |
| 🟡 | `e4ff87f9b` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Task #900 — Configurações: consolidar wrappers Standalone+Templates — What changed |
| 🟡 | `b209a12fa` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `23a56756d` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Task #896 — cobertura mínima de testes para o menu Configurações — Implementa o "minimum test covera |
| 🟡 | `ddeb1eb92` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `43f62d263` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `45a6c89c9` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `9143c277e` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Task #897 — Configurações: limpeza Lote 1 (cluster Goals/Workforce) — Removido cluster órfão "Goals/ |
| 🟡 | `2abf85f6f` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `9955bd284` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Task #894 — Configurações: consertar rotas fantasma — ## Original task |
| 🟡 | `d36663115` | 2026-04-28 | Frontend (UI) | Configurações (hub) | Configurações: limpeza Lote 3 (pages/integrations + singletons órfãos) — Task #899 — deleta o cluste |
| 🟡 | `24f6c8f47` | 2026-04-28 | Backend | §4 Rail Features — PR-Q4 | feat(policy): PR-Q4 — policy domain isolation sensor + canonical comment — Canonical-fix (AGT-S03):  |
| 🟡 | `03cad32de` | 2026-04-28 | Cross IA↔Back | §4 Rail Features — PR-Q3 | feat(capability-map): PR-Q3 — align start_wsi_interview intent + triagem wsi keywords — Canonical-fi |
| 🟡 | `e92a0b4c6` | 2026-04-28 | Backend | Artefatos / Eval logs (sem código) | Update job management tool evaluation results and add new tests — Add evaluation results for job lis |
| 🟢 | `7da120da6` | 2026-04-28 | Frontend (UI) | §4 Rail Features — Rail A | feat(rail-a): PR-Q1 — direct nav + modal dispatch for talent-pool and add-candidate — - NAVIGATION_O |
| 🟡 | `b2b8634d4` | 2026-04-28 | Backend | §4 Rail Features — PR-HIRE (register_hire) | feat(pipeline): PR-HIRE — register_hire real DB write — Replace stub with VacancyCandidate.status=hi |
| 🔴 | `9477be72f` | 2026-04-28 | Cross Back↔Front | Automations | Update recruitment automations with new data fetching and testing — Refactor AutomationsTab componen |
| 🟡 | `73a232a56` | 2026-04-28 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `449a442e8` | 2026-04-28 | IA | §2 Harness / CI sensors | feat(harness): CI sensor check_deprecated_rail_a_tools.py — harness-engineering sensor computacional |
| 🟡 | `c40a82af1` | 2026-04-28 | IA | §4 Rail Features — Rail A | feat(rail-a): Wave 1 PR-Q2+Q3 — add close_job, generate_job_report, forecast, start_wsi_flow to capa |
| 🟡 | `d8c34d554` | 2026-04-28 | IA | §4 Rail Features — Rail A | feat(rail-a): wire rail_a_capability_check into main_orchestrator Phase 0.0 (PR-J) — harness-enginee |
| 🟢 | `4d4f4f07b` | 2026-04-28 | Frontend (UI) | §4 Rail Features — Rail A | fix(rail-a): canonical-fix pulse scope CompactReels + testes 29/29 verde — - CompactReels chama useP |
| 🟡 | `e5438af42` | 2026-04-27 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `a11a9cfc5` | 2026-04-27 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `c505e4866` | 2026-04-27 | Frontend (UI) | Triagem (módulo) | Translate the rest of the candidate triagem chrome (errors, footer, phone card) — Task #887: Task #8 |
| 🟡 | `4ebffcc70` | 2026-04-27 | Backend | Vagas Públicas | fix(public-vacancies): restaurar página pública /pt/vagas/[slug] — A URL pública de candidatura (htt |
| 🟢 | `0cfd9ce67` | 2026-04-27 | Docs | §2 Harness / CI sensors | feat(harness): pre-commit sensor branch-map-theme-check (ativo) — Implementa o sensor computacional  |
| 🟢 | `9f22fc56b` | 2026-04-27 | Testes | §4 Rail Features — PR-E | test(pr-e): OfferReviewModal component tests — 14 cases, TDD harness sensor — PR-E Camada 2 (compone |
| 🟡 | `7d8222ea2` | 2026-04-27 | Backend | §4 Rail Features — PR-I | fix(pr-i+pr-e): resolve keyword conflict + add fairness test pyramid for offer — PR-I: capabilities. |
| 🟢 | `b1e0cf615` | 2026-04-27 | Frontend (UI) | Offer Review (PR-B) | style(offer-modal): apply DS v4.2.2 compliance fixes — P0: max-w-3xl → max-w-6xl (prohibited size, 2 |
| 🟢 | `0fc286d25` | 2026-04-27 | Docs | §2 Harness / CI sensors | feat(harness): regra de organizacao de branch + BRANCH_MAP em CLAUDE.md (project + workspace) e .cur |
| 🟢 | `e54557d97` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-B | fix(pr-b): add global lia:open_offer_review listener to LIAGlobalModals — Trigger A (Rail A Card 5.1 |
| 🟢 | `3ba00563a` | 2026-04-27 | Docs | Docs / BRANCH_MAP nav | docs(nav): BRANCH_MAP — indice rapido + secao IA-friendly + 4 templates de prompt + cross-refs aos 2 |
| 🟢 | `248137994` | 2026-04-27 | Docs | §12 DEVELOPER_HANDOFF — PARTE D | docs(nav): BRANCH_MAP — janela 3 (Tasks #494-#570) + 7 milestones (PARTE D, BYOK, WSI, persona) |
| 🟢 | `7795e6f29` | 2026-04-27 | Docs | Docs / BRANCH_MAP nav | docs(nav): BRANCH_MAP — estender com Tasks #574-#712 (janela anterior em main) + 7 milestones novos |
| 🟢 | `412e8c427` | 2026-04-27 | Docs | Docs / BRANCH_MAP nav | docs(nav): BRANCH_MAP — link aos 3 docs LIA Maturity recuperados |
| 🟢 | `014ea00a8` | 2026-04-27 | Docs | scope: lia-maturity | docs(lia-maturity): recuperar 3 docs apagados pelo Saved progress at the end of the loop (f7627f1bf) |
| 🟡 | `bdef6961d` | 2026-04-27 | IA | §4 Rail Features — PR-J | fix(pr-j): read intent_hint from context.metadata (PR-A nesting) — PR-A sends metadata nested under  |
| 🟢 | `94277b170` | 2026-04-27 | Docs | Docs / BRANCH_MAP nav | docs(nav): BRANCH_MAP.md — mapa de branches, milestones e temas para o time |
| 🟢 | `cbbb9af66` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-J | feat(pr-j): add LIAGlobalModals + useModalOpenListener [FE sprint 3] — - useModalOpenListener(modal_ |
| 🟡 | `43802d069` | 2026-04-27 | Cross IA↔Back | §4 Rail Features — PR-J | feat(pr-j): wire capability_map + entity_resolver into WS handler [BE sprint 2] — - rail_a_capabilit |
| 🟡 | `8705ece14` | 2026-04-27 | Cross IA↔Back | §4 Rail Features — PR-J | feat(pr-j): add EntityResolverService + CapabilityMapService [BE sprint 1] — - capability_map.yaml:  |
| 🟢 | `8656f5e9c` | 2026-04-27 | Docs | §1 Teams Integration | docs(teams): DOC_HANDOFF v2 — 5 gaps corrigidos + guia de instalação no Teams — Gaps corrigidos: |
| 🟡 | `f9893206e` | 2026-04-27 | Frontend (UI) | Triagem (módulo) | Localize candidate triagem chrome via next-intl (Task #886) — The shared triagem UI components were  |
| 🟡 | `90b519305` | 2026-04-27 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Localize screening template previews for English — Task #885 — make `/[locale]/triagem/preview/...`  |
| 🟡 | `4d19cf41c` | 2026-04-27 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `71a4cfcca` | 2026-04-27 | Docs | §1 Teams — Wave 6 | docs(teams): Wave 6 handoff — DOC_HANDOFF + CONTRATO_RAILS + endpoints + architecture diagram — docs |
| 🟢 | `824507ee8` | 2026-04-27 | Testes | §1 Teams Integration | test(teams): W5.2+5.3+5.4 validation — smoke spec, digest cron, Azure permissions — W5.2 — tests/smo |
| 🟡 | `b1b350f89` | 2026-04-27 | Backend | §1 Teams Integration | feat(teams): W9.2 voice/audio STT — transcribe via Gemini and route through orchestrator — - Add pro |
| 🟡 | `8f3ec7a30` | 2026-04-27 | Backend | §1 Teams Integration | feat(teams): W9.3 files multimedia — image/video/document routing — Attachment dispatch by MIME type |
| 🔴 | `ec6ef7bb7` | 2026-04-27 | Cross Back↔Front | §4 Rail Features — Rail A | feat(pr-m): add active-jobs pulse badge to Vaga node in Rail A — - PipelinePulseResponse: add active |
| 🟡 | `92712dcfb` | 2026-04-27 | Backend | §1 Teams Integration | feat(teams): W9.1 group/channel proactive flow + fix TEAMS_SLASH_COMMANDS — Group/channel proactive  |
| 🟢 | `710adfcef` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-N | feat(rail): PR-N compact pulse parity + PR-O card telemetry — PR-N: CompactNode now shows pulse badg |
| 🟢 | `5fa71f9cb` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-C | fix(rail): PR-C update register-hire intent_hint to dedicated action — register-hire card now routes |
| 🟢 | `ec7d4a817` | 2026-04-27 | Testes | §4 Rail Features — PR-HIRE (register_hire) | feat(pipeline): PR-C register_hire action — closes P0 gap for card 6.1 — - register_hire tool: moves |
| 🟡 | `c58acf2ef` | 2026-04-27 | Backend | Backend Services (BE) | Add functionality to formally register a candidate as hired — Introduce a new tool `register_hire` f |
| 🟡 | `cbc71c70e` | 2026-04-27 | IA | Privacy / PII (W7) | fix(privacy): W7.1 PII strip antes do router LLM cascade — Gap: LLMCascadeRouter._call_model() inter |
| 🟢 | `f60cf1311` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-K | feat(rail): PR-K direct navigation for 9.x config cards — Cards ai-credits, hiring-policy, email-tem |
| 🟢 | `f42fa5095` | 2026-04-27 | Frontend (UI) | Triagem (módulo) | Add WhatsApp and reminder email previews to triagem preview suite — Original task #884: Extend the c |
| 🟡 | `2f09160ff` | 2026-04-27 | Cross IA↔Back | §9 Security / Tenant guards | fix(security): W7.2 PromptInjectionGuard global — bridge + cascaded router — - TeamsOrchestratorBrid |
| 🟢 | `f1236a268` | 2026-04-27 | Frontend (UI) | §4 Rail Features — PR-H | refactor(rail): canonicalize stages + purge hex fallbacks (PR-H + PR-L) — canonicalFunnelStages.ts: |
| 🔴 | `f277a773c` | 2026-04-27 | Cross IA↔Front | Triagem (módulo) | Task #882: Preview da triagem do candidato pra print — Adiciona quatro rotas de preview sem autentic |
| 🟡 | `a318bb180` | 2026-04-27 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `60a09637f` | 2026-04-27 | Backend | §4 Rail Features — PR-I | fix(pr-i): resolver conflitos de keyword routing entre domínios — harness-engineering: guide computa |
| 🟡 | `4c7eef5e8` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W7.3 LGPD consent gate em /webhook approve antes de screening WhatsApp — Adiciona verifi |
| 🔴 | `939d38a2f` | 2026-04-27 | Cross Back↔Front | §1 Teams Integration | refactor(teams): W8 tech debt batch — 8 P2 itens em 1 commit — 8.1 useTeamsTabTracker: prolongedStay |
| 🔴 | `43f953d95` | 2026-04-27 | Cross Back↔Front | §1 Teams Integration | feat(teams): W5.1 Tab Pipeline + Tab Dashboard — resolve 404 no manifest — Implementa as 2 abas Team |
| 🟡 | `bfc45ee1b` | 2026-04-27 | Backend | §1 Teams Integration | docs(teams): W5.5 canonical doc + headers em 4 paths Teams send — Resposta a pergunta What is the ca |
| 🟡 | `9f472462e` | 2026-04-27 | Backend | §2 Harness / CI sensors | feat(harness): C. validate skill E2E + promote G6+G7 hooks to block-only — Skill /create-canonical-a |
| 🟡 | `c3755076c` | 2026-04-27 | Backend | §2 Harness / CI sensors | fix(harness): B. W1.6+ cleanup G6 — 21 getattr violations em 13 arquivos (G6 24 -> 0) — Apos W1.1+W1 |
| 🟢 | `e56d3dd2f` | 2026-04-27 | Testes | §2 Harness / CI sensors | test(harness): A. revalidate W1.4 xfails — 2 false-positives flipped to strict + 1 refined — Wave 4  |
| 🟢 | `a02ed3137` | 2026-04-27 | Testes | §2 Harness / CI sensors | test(harness): W4.4 audit edge cases (analytics-only) — sentinel + non-issue confirmed — Investigaca |
| 🟡 | `9021db1ba` | 2026-04-27 | Backend | §2 Harness / CI sensors | fix(harness): W4.3 sensor v4 alias-aware + content-source-aware (System YAML 61% -> 100%) — Investig |
| 🟡 | `3d983b248` | 2026-04-27 | Backend | §2 Harness / CI sensors | fix(harness): W4.2 audit + G7 v3 cross-domain tool_registry (corrige falso-positivo) — Investigacao  |
| 🟡 | `2dcb2d761` | 2026-04-27 | Backend | §2 Harness / CI sensors | fix(harness): W4.1 register_agent canonical em automation + autonomous (gap real) — Auditoria 2026-0 |
| 🟡 | `3d2b5ca94` | 2026-04-27 | Backend | §2 Harness / CI sensors | fix(harness): W3.3 v2 audit_agent_compliance heritage-aware (corrige falsos negativos) — Paulo apont |
| 🟡 | `7d150e7a4` | 2026-04-27 | Backend | §2 Harness / CI sensors | feat(harness): W3.3 audit retroativo + AGENT_COMPLIANCE_MATRIX_2026-04-27.md — Auditoria 2026-04-27  |
| 🟡 | `94aaf06e9` | 2026-04-27 | Backend | §2 Harness / CI sensors | feat(harness): W3.1 + W3.2 anatomy doc + G7 sensor de compliance canonical — Auditoria 2026-04-27 (P |
| 🔴 | `ece44f52d` | 2026-04-27 | Cross IA↔Front | §4 Rail Features — Rail A | chore(rail-a): remove PR-A from sprint-I (extracted to feat/pr-a-rail-a-metadata) — PR-A foi extraid |
| 🟢 | `6188036e3` | 2026-04-27 | Testes | §1 Teams Integration | test(teams): W2.6.c RBAC regression net para _enforce_company_id_scope — Auditoria 2026-04-27: commi |
| 🟢 | `cf542d0b5` | 2026-04-27 | Frontend (api/util) | §1 Teams Integration | fix(teams-tab): W2.3 P1-9 + P1-10 useTeamsSSO companyId + refresh proativo — Auditoria 2026-04-26 (P |
| 🟡 | `2818ab064` | 2026-04-27 | Cross IA↔Back | §1 Teams Integration | audit: validação pós-Rev 4 do wizard + fixes cross-tenant Teams — Auditoria final do wizard de criaç |
| 🟡 | `5e87c918a` | 2026-04-27 | Backend | §1 Teams Integration | feat(teams): W2.5 P1-7 /feedback persiste em teams_feedback (close black hole) — Auditoria 2026-04-2 |
| 🔴 | `365bfab8f` | 2026-04-27 | Cross IA↔Front | §1 Teams Integration | audit: validação exaustiva pós-Rev 4 + fix cross-tenant Teams proactivity — Auditoria final solicita |
| 🟢 | `e8ad5a097` | 2026-04-27 | Testes | §1 Teams Integration | fix(teams): W2.6.b follow-up — fixture autouse para legacy tests apos signature 3-state — 13 testes  |
| 🟡 | `34cc893b2` | 2026-04-27 | Cross IA↔Back | Wizard (geral) | audit: validação exaustiva pós-Rev 4 do wizard de criação de vaga — Auditoria final solicitada pelo  |
| 🟡 | `69a7aa6cb` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W2.6.b P1-5 webhook signature 3-state (TEAMS_WEBHOOK_DEV_BYPASS) — Auditoria 2026-04-26  |
| 🟡 | `050bb33f8` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W2.6 P1-4 auth Depends em 7 endpoints internos (proactive + calendar) — Auditoria 2026-0 |
| 🟡 | `3dc6dbd8f` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W2.4 P1-8/P1-11 auth + platform_user_id validation em /tab/events — Auditoria 2026-04-26 |
| 🟡 | `ff8e043cd` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W2.2 P1-6 deletar 2 repository methods broken + atualizar 5 testes legados — Auditoria 2 |
| 🟡 | `151912552` | 2026-04-27 | Backend | §9 Security / Tenant guards | Improve security by ensuring all privileged actions are refused when tenant boundaries cannot be ver |
| 🔴 | `5d7c93349` | 2026-04-27 | Cross IA↔Front | Auditoria / Audit Rev | audit Rev 4: fechar F4 PM-02 (token streaming) + PM-03 (protocol handshake) — Resolve os P3 remanesc |
| 🟡 | `9ee92caea` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W2.1 P1-1 corrige 3 bugs em send_daily_digest (cron diario 08h) — Auditoria 2026-04-26 ( |
| 🟢 | `a3772f1fc` | 2026-04-27 | Testes | §1 Teams Integration | test(teams): W1.4 P0-4 fechar cobertura red team Teams (10 strict + 8 xfail gaps) — Auditoria 2026-0 |
| 🟡 | `96f1c7753` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W1.3 P0-3 tenant filter em GET /webhook/audit-logs — Auditoria 2026-04-26 (AUDITORIA_TEA |
| 🟡 | `9e8e377aa` | 2026-04-27 | Backend | §1 Teams Integration | fix(teams): W1.2 P0-2 server-side company_id resolution + canonical-fix 3 getattr — Auditoria 2026-0 |
| 🟡 | `4f1cdfa3f` | 2026-04-27 | Backend | §9 Security / Tenant guards | Update security and testing for job management and team webhooks — Adjusted job management evaluatio |
| 🟡 | `9bf4f48db` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Wizard JD upload: subscribe to background_task_update WS events — Task #865 — wire the chat-surface  |
| 🟡 | `99ffb988a` | 2026-04-26 | Backend | Tasks #712-#886 (Features de produto) | Audit and bound process-local Redis fallbacks (Task #871) — Mirrors the TTL eviction added to jd_upl |
| 🟡 | `fd8bd9ad8` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `22b581b46` | 2026-04-26 | Backend | Scripts / CLI | Improve code quality by disallowing unsafe attribute access on models — Add a new pre-commit hook to |
| 🟡 | `f7f972882` | 2026-04-26 | Backend | §1 Teams Integration | fix(teams): P0-1 multi-tenant boundary via company_id em TeamsConversation — Auditoria 2026-04-26 (A |
| 🟡 | `ea8418688` | 2026-04-26 | Cross IA↔Back | Policy / Job Creation | Wire PolicyGateService + ConfidencePolicyService into JobCreationGraph — Resolves N-09 (PolicyGateSe |
| 🟡 | `2adac0f2c` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `887cb1283` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Task #860 — Wizard Frontend Canonical-Fix Final (A-01, A-10) — Resolves audit findings A-01 (wizard  |
| 🟡 | `6086b2cd8` | 2026-04-26 | Backend | Tasks #712-#886 (Features de produto) | Evict abandoned uploads from the in-memory staging fallback (Task #867) — Original task |
| 🔴 | `bfe3efade` | 2026-04-26 | Cross Back↔Front | JD Import / Job Description | [#858] Harden /jd-import/upload-file (B-02 + A-02 + M-12) — Move JD upload parse out of the FastAPI  |
| 🟡 | `f5cf05330` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `b595f6833` | 2026-04-26 | Cross IA↔Back | Wizard (geral) | Wizard OTLP — Fechar Lacuna de Observabilidade (N-07 + N-08) — Task #861. Fecha as duas pendências d |
| 🟡 | `158ea11be` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `2528738cf` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Wizard A11y — Focus Trap (A-08) + WCAG Contrast (A-09) — Resolves audit findings A-08 and A-09 from  |
| 🟡 | `2f677eae0` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `f01469113` | 2026-04-26 | Backend | Wizard (geral) | Wizard Hotfix — 410 Gone para NotImplementedError (Task #857, achados N-01/N-02) — Original task |
| 🟡 | `94a629c1d` | 2026-04-26 | Backend | §2 Orchestrator Migration | feat(orch-migration): final delivery - canary kit + Sprint V plan + ADR-019 final — LIA-D06 Orchestr |
| 🟢 | `5a3b1a1c7` | 2026-04-26 | Docs | §2 Orchestrator Migration | docs(orch-migration): Sprint III.E canary rollout plan — LIA-D06 Orchestrator Migration — documenta  |
| 🟡 | `b6dabf9b8` | 2026-04-26 | Backend | §2 Orchestrator Migration | feat(orch-migration): add OTLP LGPD violation pre-commit hook — LIA-D06 Orchestrator Migration — Spr |
| 🟡 | `7333e418a` | 2026-04-26 | Cross IA↔Back | §2 Orchestrator Migration | feat(orch-migration): extract AnalyticsDispatchService — process_analytics_request canonical — LIA-D |
| 🟡 | `86e914d93` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint III.D — late-intercept FallbackReActService flag — LIA-D06 Orchestrator |
| 🟡 | `00db0ec4b` | 2026-04-26 | Cross IA↔Back | §2 Orchestrator Migration | feat(orch-migration): Sprint IV — extract RubricDispatchService (CV match BARS) — LIA-D06 Orchestrat |
| 🟡 | `1d7262cdb` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint III.C — OTLP @trace_span aplicados em V1 e V2 — LIA-D06 Orchestrator Mi |
| 🟡 | `4ea526c59` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint III.B — feature flag granular para PlanOrchestrationService — LIA-D06 O |
| 🟡 | `b4e3d20c1` | 2026-04-26 | IA | §2 Orchestrator Migration | fix(orch-migration): resolve P1 #7 — lazy init race condition — LIA-D06 Orchestrator Migration — Aud |
| 🟡 | `c5563138a` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint III.A — V2 DI setup (services optional, backward compat) — LIA-D06 Orch |
| 🟡 | `1efb02eab` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for candidate chat and polish — Replace import statements in mockup-components.ts to  |
| 🟡 | `5ffc46a58` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Task #854: Pixel-faithful candidate↔LIA chat mockup in mockup-sandbox — Adds a marketing-ready mocku |
| 🟡 | `0312bb4fb` | 2026-04-26 | IA | §2 Orchestrator Migration | refactor(orch-migration): Sprint II audit fixes — 6 P1 + BASELINE.md — LIA-D06 Orchestrator Migratio |
| 🟡 | `dd167b08b` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint II.1 — PlanOrchestrationService canonical — LIA-D06 Orchestrator Migrat |
| 🟡 | `4b4b9bf8c` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint II.2 — extract FallbackReActService (LIA-A04) — LIA-D06 Orchestrator Mi |
| 🟡 | `d9a4a6367` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint II.4 — extract context_type_override to service — LIA-D06 Orchestrator  |
| 🟡 | `5051c824b` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint II.5 — PolicyGateService canonical wrapper — LIA-D06 Orchestrator Migra |
| 🟡 | `939d3a9e4` | 2026-04-26 | IA | §2 Orchestrator Migration | feat(orch-migration): Sprint II.3 — extract heuristics module from V1 — LIA-D06 Orchestrator Migrati |
| 🟢 | `763bfbdc5` | 2026-04-26 | Testes | §2 Orchestrator Migration | refactor(orch-migration): code review fixes — fixture consolidation + ADR-019 gate — Code review apr |
| 🟡 | `f4ad3b82a` | 2026-04-26 | IA | §2 Orchestrator Migration | docs(orch-migration): Sprint I-D+F — ADR-019 + canonical span constants — LIA-D06 Orchestrator Migra |
| 🟢 | `ae2d446d3` | 2026-04-26 | Testes | §2 Orchestrator Migration | test(orch-migration): Sprint I-C characterization tests — 50 fixtures all passing — LIA-D06 Orchestr |
| 🟡 | `f4989d53b` | 2026-04-26 | Backend | §2 Orchestrator Migration | feat(orch-migration): Sprint I-A foundations — V1 inventory + characterization tests scaffolding — L |
| 🟢 | `ab29cadf4` | 2026-04-26 | Frontend (UI) | Frontend (genérico) | fix(fe): restore daily-briefing-card + disc-assessment-modal (false positives in #9957575f9) — Bug:  |
| 🔴 | `8bb8618ee` | 2026-04-26 | Cross IA↔Back | Wizard (geral) | Task #850: Consolidate canonical job-creation wizard (round 6 — review polish) — Original task: Remo |
| 🟢 | `3b19208f2` | 2026-04-26 | Testes | scope: test | chore(test): remove orphaned test for deleted MLInsightsCard |
| 🟡 | `b8c86f230` | 2026-04-26 | Frontend (UI) | Frontend (genérico) | refactor(fe): move 6 misplaced hooks to canonical hooks/ structure — Move hooks from components/ (wr |
| 🟡 | `9957575f9` | 2026-04-26 | Frontend (UI) | Frontend (genérico) | chore(fe): remove dead code — 6 orphaned components + workspace litter — Remove 6 React components c |
| 🔴 | `5d5635007` | 2026-04-26 | Cross Back↔Front | Compliance / LGPD / EU AI Act | fix(unified-chat): remove dead LgpdConsentDialog to unblock build — Bug: dev-server (Next.js 16 + Tu |
| 🔴 | `30fd75ff9` | 2026-04-26 | Cross Back↔Front | Privacy / PII (W7) | Task #838 — Privacy & audit hardening on JD upload endpoint — Reforço de privacidade e auditoria no  |
| 🟡 | `590c55130` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `8ef5059c0` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for toast notifications — Update mockup component imports for SonnerToasts and Templa |
| 🟢 | `8a681bb3a` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #844 — Restore the LIA chat message-action UI behind the broken tests — The 3 tests in |
| 🟡 | `73c2bb8c4` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for chat usability and ElevenLabs funnel components — Update the generated mockups fi |
| 🔴 | `17031f1dc` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #840 — Alinhar UnifiedChat ao Design System v4.2.1 — Resolve o cluster de achados M-03/M-04/M-0 |
| 🟢 | `d4ad7aca1` | 2026-04-26 | Testes | Scheduling / Calendar (PR-CAL) | Task #839 — cover the Scheduling stage with tests — The audit `audit-criacao-vaga-2026-04-26.md` (fi |
| 🟡 | `1960f4b62` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `843db90be` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedCh |
| 🟢 | `b7526f6fe` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedCh |
| 🟢 | `7c4510f80` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedCh |
| 🟡 | `564c24ec8` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Task #836: Movimento 1 — faxina job-wizard + UX UnifiedChat — Faxina (~110KB de dead code): |
| 🟡 | `a7fcf5a5d` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `0c9b06319` | 2026-04-26 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results to include job management tests — Update evaluation results by adding test |
| 🟡 | `056a9aad3` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Improve wizard functionality and data privacy for multi-tenant environments — Implement LGPD-complia |
| 🟢 | `68cdbb065` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #835: keep "Plano de trabalho — Concluído" card visible in expanded chat — Original task: bring |
| 🟡 | `48944aaac` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `a61728809` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update generated mockups to include previous welcome polish components — Re-adds mockups for Elevate |
| 🟢 | `817484f15` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Task #830 — Show "Plano de trabalho" card as completed when wizard finishes — Original task: when th |
| 🟡 | `eba25ca5a` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `0d289cd77` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include new chat usability components — Add new mock component imports to artifact |
| 🟢 | `a08bb627c` | 2026-04-26 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #828 — Cobrir o cartao "Plano de trabalho" com teste end-to-end real — Adiciona o teste e2e Pla |
| 🟡 | `d69734432` | 2026-04-26 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include chat usability features — Update artifacts/mockup-sandbox/src/.gen |
| 🟢 | `83358e78f` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Unify "Criar nova vaga" wizard surface across chat and modal — UnifiedChat already showed the canoni |
| 🔴 | `3a3183c77` | 2026-04-26 | Cross Back↔Front | Wizard (geral) | Task #827 — Inject "Vaga publicada" closing card on wizard handoff — When the "Criar nova vaga" wiza |
| 🟡 | `9e85e24e5` | 2026-04-26 | Frontend (UI) | Wizard (geral) | Task #826 — Mount wizard plan card and progress bar in main chat feed — What changed |
| 🟡 | `e97549bb1` | 2026-04-26 | Backend | Artefatos / Eval logs (sem código) | Update job management evaluation results to reflect current system status — Update evaluation result |
| 🟢 | `28d1bd681` | 2026-04-26 | Docs | Skills / canonical-fix | Refinar SKILL.md das 11 skills refatoradas — "Quando ativar" especifico — Task #785: cada SKILL.md d |
| 🟡 | `52e7da6f8` | 2026-04-26 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `8adecbc23` | 2026-04-26 | Cross IA↔Back | §13 PARTE D — PreConditionChecker | Task #819: close last 2 demo-tenant config gaps in PreConditionChecker — Original task: Close the 2  |
| 🟡 | `b1205833b` | 2026-04-26 | Backend | Tasks #712-#886 (Features de produto) | Migrar imports legados dos shims de intent classifier para o caminho canônico (Task #821) — Original |
| 🟢 | `6f5d765ca` | 2026-04-25 | Testes | LIA Float UI (FE) | Improve test reliability by mocking external requests — Mock the fetch API call within the LiaChatPa |
| 🟢 | `69a3a4d4c` | 2026-04-25 | Testes | Tasks #712-#886 (Features de produto) | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runt |
| 🟢 | `b7cfb594f` | 2026-04-25 | Testes | Tasks #712-#886 (Features de produto) | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runt |
| 🟡 | `7c4c03151` | 2026-04-25 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runt |
| 🟢 | `e10758adc` | 2026-04-25 | Docs | Compliance / LGPD / EU AI Act | Update tenant configuration documentation and clarify initial compliance status — Update tenant mini |
| 🟢 | `85fbacb23` | 2026-04-25 | Docs | Tasks #712-#886 (Features de produto) | docs: spec canônico de configuração mínima por tenant (Task #816) — Cria docs/governance/tenant-mini |
| 🟡 | `1452d9473` | 2026-04-25 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `a27c50399` | 2026-04-25 | Backend | Backend (shared) | Strengthen demo data validation with direct database checks — Update demo data seeding to perform st |
| 🟡 | `ec4f1fe8d` | 2026-04-25 | Backend | Tasks #712-#886 (Features de produto) | Task #813: Estender seed_service para popular o tenant demo — Adiciona `seed_demo_company_settings(d |
| 🟡 | `43f41ca02` | 2026-04-25 | Backend | Tasks #712-#886 (Features de produto) | Task #813: Estender seed_service para popular o tenant demo — Adiciona `seed_demo_company_settings(d |
| 🟡 | `38e423195` | 2026-04-25 | Backend | Backend Services (BE) | Ensure deterministic tool ordering and handle missing definitions — Refactor the tool definition pic |
| 🟡 | `07838c1fb` | 2026-04-25 | Backend | Configurações (hub) | Task #812: company_settings — tools operacionais primárias — Estende o agente `company_settings` par |
| 🟡 | `8d3c985d8` | 2026-04-25 | Cross IA↔Back | Configurações (hub) | [task #812] company_settings: cobrir ações primárias (canonical-fix PT-BR) — Defesa em profundidade  |
| 🟡 | `85eb169fa` | 2026-04-25 | IA | §13 PARTE D — Proatividade | fix(orchestrator): respeitar severity + intent em ProactiveHints (task #811) — ## Original |
| 🟡 | `a1fbb30c6` | 2026-04-25 | Cross IA↔Back | §13 PARTE D — Proatividade | fix(orchestrator): respeitar severity + intent em ProactiveHints (task #811) — ## Original |
| 🟡 | `324aa2acd` | 2026-04-25 | IA | §13 PARTE D — Proatividade | fix(orchestrator): respeitar severity de ProactiveHints (task #811) — ## Original |
| 🟡 | `7ef32d4f4` | 2026-04-25 | IA | §13 PARTE D — Proatividade | fix(orchestrator): respeitar severity de ProactiveHints (task #811) — ## Original |
| 🟡 | `698afe531` | 2026-04-25 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `71b08e0cf` | 2026-04-25 | Backend | Docs / Reconstruction Guides | Update documentation for system configurations and operational guides — Update various documentation |
| 🔴 | `b402230fc` | 2026-04-24 | Cross Back↔Front | Hooks (FE) | Restore missing and broken file imports across the application — Restores 34 missing modules by loca |
| 🟢 | `8f5989bd4` | 2026-04-24 | Docs | Compliance / LGPD / EU AI Act | Add canonical YAML bundles to documentation for AI assistants — Create new markdown files containing |
| 🟢 | `26fc30308` | 2026-04-24 | Docs | scope: specs | docs(specs): add MVP and Product Readiness checklists to FLUXO_TECNICO_COMPLETO_ALPHA1 — Adds two pr |
| 🟢 | `890e2475f` | 2026-04-24 | Docs | Docs / Reconstruction Guides | Add new candidate-facing API endpoint and tool for decision explanation — Add `/api/v1/candidate/dec |
| 🟢 | `aeab95013` | 2026-04-24 | Frontend (api/util) | FE libs / utils | Restore development login functionality and fix configuration errors — Restore the `dev-auto-login.t |
| 🟢 | `2618598fa` | 2026-04-24 | Frontend (api/util) | Docs / Reconstruction Guides | Update development server to use correct port for Replit preview — Reverts the change that updated t |
| 🔴 | `aa664e84b` | 2026-04-24 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Add ability to explain automated decisions to candidates — Adds a new API endpoint and tool for expl |
| 🟡 | `d6644982b` | 2026-04-23 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `5bec8805f` | 2026-04-23 | Docs | scope: audit | docs(audit): add Archetypes feature end-to-end audit — Task #806: produces docs/audit/arquetipos/AUD |
| 🟡 | `6f57b3d65` | 2026-04-23 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `f7627f1bf` | 2026-04-23 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟡 | `98781c699` | 2026-04-23 | Backend | Artefatos / Eval logs (sem código) | Update job management evaluation results with new test cases — Add new test cases to the evaluation  |
| 🟢 | `12bf9953b` | 2026-04-23 | Docs | Docs / Architecture | Update documentation to reflect current system architecture and agent counts — Refactor documentatio |
| 🟡 | `8237e5cb6` | 2026-04-23 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `a043b8c24` | 2026-04-22 | Frontend (UI) | Vagas Públicas | feat(vagas): design + WCAG 2.1 AA + code quality na página pública de vaga — - Design: espaçamentos  |
| 🟢 | `81efb2987` | 2026-04-22 | Frontend (api/util) | Lint / Code Quality | Enforce removal of deprecated API route across all TypeScript files — Add ESLint rule to prevent usa |
| 🟡 | `ad1fd512a` | 2026-04-22 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #802: remove parallel proxy route /api/lia/[...path] — What changed |
| 🟢 | `d6a0b5ca7` | 2026-04-22 | Frontend (UI) | Tests (FE e2e) | Improve error display and speed up candidate search reliability — Update error message key and enhan |
| 🟡 | `1e29040d2` | 2026-04-22 | Frontend (UI) | §6 Chat Unificado / Funil | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Address |
| 🟡 | `d0b1b75bb` | 2026-04-22 | Frontend (api/util) | §6 Chat Unificado / Funil | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Address |
| 🟡 | `d7f273860` | 2026-04-22 | Frontend (UI) | §6 Chat Unificado / Funil | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Address |
| 🟡 | `fc5ba84eb` | 2026-04-22 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `540315b5a` | 2026-04-22 | Docs | §3 LIA Maturity | docs: expand LIA_MATURITY_LEAP_RESUMO.md section 7 with detailed breakdown — Previous section 7 was  |
| 🟢 | `ec89039c6` | 2026-04-22 | Docs | §3 LIA Maturity | docs: LIA_MATURITY_LEAP_RESUMO.md — explanatory summary for dev team — 200-line plain-language compl |
| 🟢 | `40dd2cf6c` | 2026-04-22 | Docs | scope: handoff | docs(handoff): add HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md (740 lines) — Comprehensive handoff docu |
| 🟡 | `1d2562bce` | 2026-04-22 | Outro | Mockup Sandbox (artefato gerado) | Update mock component generation for display — Update mockup component generation to correctly inclu |
| 🟢 | `99aea7154` | 2026-04-22 | Frontend (UI) | Vagas Públicas | Alinhar página pública de vagas ao Design System (Task #799) — Refatora `plataforma-lia/src/app/[loc |
| 🟡 | `906749f22` | 2026-04-22 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `54def11f3` | 2026-04-22 | IA | Wizard/Onda 5.3. | feat(lia): Onda 5.3.c — history compaction with conversation_summary reuse — Canonical-fix consumer- |
| 🟡 | `2a35c08cb` | 2026-04-22 | Backend | Artefatos / Eval logs (sem código) | Task start baseline checkpoint for code review |
| 🟡 | `73c7ff712` | 2026-04-22 | Backend | Vagas Públicas | Tarefa #798 — Enriquecer vaga pública Product Manager — Permite visualizar /pt/vagas/product-manager |
| 🔴 | `e1dcee729` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 3.2 | restore(lia): recover Onda 3.2—5.1 work + new Onda 5.3.a after parallel rollback — Context: commit c |
| 🟡 | `981bd3c32` | 2026-04-22 | IA | §2 Orchestrator Migration | Refine tool selection to improve agent efficiency and reduce prompt size — Introduce intent-based to |
| 🟢 | `78a24ac21` | 2026-04-22 | Empty/merge | Tasks #712-#886 (Features de produto) | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando "Se |
| 🟡 | `f1784016b` | 2026-04-22 | IA | Tasks #712-#886 (Features de produto) | chore(task-795): remove unrelated intent_heuristic.py added by parallel worktree |
| 🟡 | `d0d140e0a` | 2026-04-22 | IA | Tasks #712-#886 (Features de produto) | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando "Se |
| 🟡 | `301714b24` | 2026-04-22 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando 'Se |
| 🟡 | `4af7cf447` | 2026-04-22 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `c698d5eef` | 2026-04-22 | Cross IA↔Front | (Auto-commit Replit) | Restored to 'c3d45b3d8ddb560ce2ee3a23c6062d8ae325a6f4' — Replit-Restored-To: c3d45b3d8ddb560ce2ee3a2 |
| 🟢 | `0cdf20288` | 2026-04-22 | Frontend (api/util) | Refactor / Cleanup | Remove all job readiness related endpoints and documentation — Removes deprecated job readiness endp |
| 🔴 | `c320409e5` | 2026-04-22 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Task #791: Remove Job Readiness Hub feature (frontend + backend) — Consolidates around the unified f |
| 🟡 | `b89052761` | 2026-04-22 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `af76de95f` | 2026-04-22 | Frontend (UI) | §9 Tenant Isolation / Multi-tenancy | fix(multi-tenancy): session 2026-04-22 — 16 proxy routes + company_id fixes + handoffs — - getSessio |
| 🟡 | `bfaad7737` | 2026-04-22 | Backend | §3 LIA Maturity — FIX 5 | fix(lia): Onda 5.1.b — persona briefing-as-fact rule (FIX 5.1) — After 5.1.a lands the briefing in e |
| 🟡 | `f6ee7e7dd` | 2026-04-22 | IA | Wizard/Onda 5.1. | fix(lia): Onda 5.1.a — wire ctx.extra['extra_instructions'] into agentic loop — PARTE L gap: Onda 4. |
| 🟡 | `4dad75d18` | 2026-04-22 | Backend | Wizard/Onda 4.13 | feat(lia): Onda 4.13 — G4.B cost tracking coverage for active chat paths — PARTE L gap discovered in |
| 🟡 | `ad6ce7073` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 4.11 | fix(lia): Onda 4.11 + 4.12 — briefing formatter keys + III.B log level — Two post-smoke corrections  |
| 🟡 | `3d316958b` | 2026-04-22 | Cross IA↔Back | Wizard/Onda 4.10 | feat(lia): Onda 4.10 — adapter forwards citations + hitl_checkpoint to API envelope — PARTE L gap di |
| 🟢 | `b26448e18` | 2026-04-22 | Testes | §3 LIA Maturity — FIX 35 | fix(tests): tighten Init II.A empty-filters assertion (FIX 35 regression) — Test used substring 'Fil |
| 🟢 | `5e537bc0c` | 2026-04-22 | Testes | Wizard/Onda 4.9 | feat(ci): Onda 4.9 VIII.B — persona validator step in lia-eval workflow — Extends .github/workflows/ |
| 🟡 | `8bfad78f1` | 2026-04-22 | Backend | §3 LIA Maturity — FIX 35 | feat(lia): Onda 4.8 FIX 35 — G1 conversational polish via persona — Per ONDA4_PLAN §3 (G1 conversati |
| 🟡 | `09c387d15` | 2026-04-22 | IA | Wizard/Onda 4.7 | feat(lia): Onda 4.7 VII.B — error_policies wired in outer catch-all — Producer (error_policies.py On |
| 🟡 | `f9f60701a` | 2026-04-22 | IA | Wizard/Onda 4.6 | feat(lia): Onda 4.6 G3.B — HITL checkpoint dispatch to ChatResponse — Producer (hitl.build_hitl_chec |
| 🟡 | `338b9b583` | 2026-04-22 | IA | Wizard/Onda 4.5 | feat(lia): Onda 4.5 V.B — citations populate em ChatResponse (agentic path) — Producer (citation_pro |
| 🟡 | `b197d510b` | 2026-04-22 | IA | Wizard/Onda 4.4 | feat(lia): Onda 4.4 IV.B — briefing greeting wire — Producer (Init IV Onda 2.3 lia_briefing_formatte |
| 🟡 | `b7bc5d264` | 2026-04-22 | IA | Wizard/Onda 4.3 | feat(lia): Onda 4.3 III.B — hydrate recruiter_preferences from user_preferences — Wires Init III MVP |
| 🟢 | `5c4ff9fb0` | 2026-04-22 | Docs | Wizard/Onda 4.3-4.9 | docs(handoff): session end handoff for Onda 4.3-4.9 continuation — Comprehensive handoff covering: |
| 🟡 | `7bb4dd716` | 2026-04-21 | Backend | Wizard/Onda 4.2 | feat(obs): Onda 4.2 G4.B — cost_tracker wired into ClaudeLLMProvider — Producer (cost_tracker, Onda  |
| 🟡 | `e1bd6997b` | 2026-04-21 | Backend | Wizard/Onda 4.1 | fix(chat): Onda 4.1 — implement _build_tool_schema_for_intent + _try_extract_params_with_llm — 16 pr |
| 🟡 | `ac536e90e` | 2026-04-21 | Backend | scope: obs | chore(obs): sync marker_catalog total_markers counter (29 → 30) — Runtime audit Onda 3 caught off-by |
| 🟡 | `ddf7c9769` | 2026-04-21 | Backend | Wizard/Onda 3.5 | feat(lia): Onda 3.5 Init III MVP — episodic memory via user_preferences — Conservative MVP. Full 3-l |
| 🟡 | `d6efe4ed1` | 2026-04-21 | Backend | Wizard/Onda 3.4 | feat(lia): Onda 3.4 Init VIII — persona consistency suite v1 (10 scenarios) — Producer layer for per |
| 🟡 | `a06559d59` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 3.3 | feat(lia): Onda 3.3 Init VII — error recovery policies catalog v1 — 5 canonical policies for determi |
| 🟡 | `34c7d2cb7` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 3.2 | feat(lia): Onda 3.2 G3 — HITL checkpoint surfacing — HITL logic already exists at app/tools/executor |
| 🟡 | `d2e5bb376` | 2026-04-21 | Backend | Wizard/Onda 3.1 | feat(obs): Onda 3.1 G4 — cost tracker + prompt cache flag — MVP for cost/latency governance. Produce |
| 🟡 | `ba2f32436` | 2026-04-21 | Backend | scope: lia | fix(lia): Init IV plural — "açãoões" → "ações" no briefing PT — Runtime audit caught cosmetic PT plu |
| 🟡 | `f7b8ec3a6` | 2026-04-21 | Cross IA↔Back | Wizard/Onda 2.5 | feat(lia): Onda 2.5 Init II.D — workflow_context slot + 3 v1 workflows — Formalizes multi-turn flows |
| 🟡 | `d0230dc91` | 2026-04-21 | IA | Wizard/Onda 2.4 | feat(lia): Onda 2.4 Init V — Reasoning transparency backend (citations) — Producer layer for citatio |
| 🟡 | `6cc6b6a85` | 2026-04-21 | Backend | Wizard/Onda 2.3 | feat(lia): Onda 2.3 Init IV — Proactive Agenda formatter + TTL cache — Producer layer for daily brie |
| 🟡 | `dd77d4439` | 2026-04-21 | Backend | Wizard/Onda 2.2 | feat(eval): Onda 2.2 Init VI Fase 1 — golden set expansion + CI workflow — 30 new golden cases added |
| 🟡 | `a45875997` | 2026-04-21 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(lgpd): G5 light — PII redaction at response boundary — Onda 2.1. Closes LGPD blocker for Init I |
| 🟢 | `802104b89` | 2026-04-21 | Docs | Wizard/Onda 2 | docs(roadmap): Onda 2 implementation plan (1704 lines) — Deep audit pre-execution per canonical-fix  |
| 🟢 | `cee507b2f` | 2026-04-21 | Testes | scope: multi-tenant | feat(multi-tenant): G6 — capability toggle (enabled_for_tenant + renderer filter) — Track 3 G6 v1: p |
| 🟡 | `c3d45b3d8` | 2026-04-21 | Cross IA↔Back | §16 LIA Persona | Introduce multi-tenant capability toggles to control agent features — Add `enabled_for_tenant` field |
| 🟡 | `846c7467e` | 2026-04-21 | Backend | scope: obs | feat(obs): G2 — marker catalog + drift-guard CI test — Inventarized 25 unique [LIA-*] markers from a |
| 🟡 | `0ee7a0211` | 2026-04-21 | Backend | §14 BYOK + LLM Factory | feat(eval): Init VI Fase 0 — eval_judge migrated to LLM Factory — Canonical-fix per FINAL_AUDIT.md § |
| 🟡 | `684b2a140` | 2026-04-21 | IA | §16 LIA Persona | feat(lia): Init I.B — persona renders capability_cards end-to-end — Closes anti-hallucination loop s |
| 🟢 | `ab3216ccd` | 2026-04-21 | Testes | §3 LIA Maturity — FIX 34 | fix(tests): FIX 34 — test isolation for governance_tags sync — Phase 0 audit misclassified as tech d |
| 🔴 | `833241d10` | 2026-04-21 | Cross Back↔Front | Configurações (hub) | fix: corrige botao Analisar nosso site em MinhaEmpresaHub — RCA: prompt sem URL + autoSend false + s |
| 🟢 | `4f84a55cf` | 2026-04-21 | Docs | Tasks #712-#886 (Features de produto) | Task #790: remove "Departamentos sao gerenciados em Usuarios & Departamentos" shortcut from Minha Em |
| 🟢 | `9e7ff39d2` | 2026-04-21 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #790: remove "Departamentos sao gerenciados em Usuarios & Departamentos" shortcut from Minha Em |
| 🟡 | `af6834854` | 2026-04-21 | Backend | Artefatos / Eval logs (sem código) | Task start baseline checkpoint for code review |
| 🔴 | `6ce1b1898` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Refactor "Minha Empresa" hub: contextual uploads + per-card progress — Original task #779: distribut |
| 🟡 | `674f10e6f` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include weekly digest components — Update the mock component import map to include |
| 🔴 | `42dc490a5` | 2026-04-21 | Docs | Skills / canonical-fix | Task #778 — Progressive disclosure em skills LIA — Aplica padrao de 3 niveis (SKILL.md enxuto + refe |
| 🟡 | `1caeee4bc` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `be06dd0a1` | 2026-04-21 | Backend | §3 LIA Maturity — FIX 32 | fix(db): FIX 32 — add conversation_summaries.user_preferences column — Schema drift: ORM model lia_m |
| 🟢 | `d0b2190e1` | 2026-04-21 | Frontend (UI) | Compliance / LGPD / EU AI Act | fix: corrige crash FairnessComplianceHub e cria proxy audit logs — - by_category?.map corrige TypeEr |
| 🟡 | `ac9a7c6e3` | 2026-04-21 | IA | §3 LIA Maturity — FIX 31 | fix(lia): FIX 31 v2 — move resolver wiring to process() top (covers all phases) — FIX 31 v1 wired me |
| 🟡 | `a50b87886` | 2026-04-21 | IA | §3 LIA Maturity — FIX 31 | fix(lia): FIX 31 — wire memory_resolver into production chat path — Discovered via FIX 30 smoke test |
| 🟡 | `ba28c86ff` | 2026-04-21 | Cross IA↔Back | §12 DEVELOPER_HANDOFF — PARTE L | fix(lia): FIX 29 + FIX 30 — close runtime-inert gaps (PARTE L pattern) — Empirical smoke test agains |
| 🟢 | `e29e238ee` | 2026-04-21 | Docs | scope: audit | docs(audit): final consolidated audit for Benefícios + Departamentos + Workforce wave (#769) — Origi |
| 🟡 | `dfedcb357` | 2026-04-21 | Backend | scope: lia | feat(lia): Initiative I.A — Grounded Capability Catalog (16 cards + CI guard) — Track 2 Initiative I |
| 🟡 | `e416f26a6` | 2026-04-21 | IA | §16 LIA Persona | Improve system prompt to include active filters and pending actions — Add support for rendering acti |
| 🟢 | `ccd88701b` | 2026-04-21 | Docs | Docs / Handoff | Update documentation to include API and endpoint details — Adds explicit mentions of APIs, endpoints |
| 🟢 | `f49be9b4d` | 2026-04-21 | Docs | Job Management (BE) | Update documentation and code to reflect standardized workforce import and job pagination contracts  |
| 🟢 | `1c5e9a295` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE J | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: document |
| 🟢 | `bd28ddf77` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE J | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: document |
| 🟢 | `b43df6ebe` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE J | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: document |
| 🟡 | `27ea118b4` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `42d5dbb7b` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 21 | feat(lia): Track 1 Fases B+C+D — FIX 21-28 (LIA Maturity Program) — Follows FIX 20 (pagination, 182d |
| 🟢 | `cfe3f51fa` | 2026-04-21 | Empty/merge | Voice / ElevenLabs / STT | fix: restore voice_service.py and granular_consent_service.py from broken merge — The previous "Appl |
| 🟡 | `182dec756` | 2026-04-21 | Backend | Job Management (BE) | Add pagination to job search functionality — Implement offset and limit parameters for the search_jo |
| 🔴 | `e03e9c7fa` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | task#765: JobVacancy.benefits ARRAY→JSONB with structured backfill — Backend |
| 🟡 | `7a5142db5` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `843a0d224` | 2026-04-21 | Cross IA↔Front | Tasks #712-#886 (Features de produto) | Task #768 — Workforce planning: rich view + 3 conversational paths + HITL — Backend (lia-agent-syste |
| 🟡 | `311e74269` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `43981a976` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Task #766: paridade Beneficios chat ↔ Hub no schema canonico — Chat e import de planilha/site agora  |
| 🟡 | `68bef95bf` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `90833f800` | 2026-04-21 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Group benefits list by category with icon and count (Task #775) — - Updated `BenefitsListSection` to |
| 🔴 | `3045bdfdd` | 2026-04-21 | Cross Back↔Front | Tasks #712-#886 (Features de produto) | Task #767: remove Departamentos from "Minha Empresa" Hub + onboarding — Scope: |
| 🟡 | `241d88f72` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Persist enriched benefit fields via LIA chat tool — Task #776: the REST API and 4-layer schema (Post |
| 🟡 | `c817b80f6` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update component registration to include chat welcome polish mockups — Update generated mockup compo |
| 🔴 | `a2913e268` | 2026-04-21 | Cross Back↔Front | scope: minha-empresa | feat(minha-empresa): Benefícios item-a-item + schema unificado em 4 camadas — Task #764 — piloto do  |
| 🟡 | `ebe39fccb` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for welcome polish mockups — Reorder mock component imports within `mockup- |
| 🟢 | `975d5e0d9` | 2026-04-21 | Docs | scope: audit | docs(audit): baseline Benefícios + Departamentos + Workforce (task #763) — Auditoria read-only entre |
| 🟡 | `66343bef5` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `32f29426f` | 2026-04-21 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #760: Let recruiters click a highlighted glossary term to open the full reference — Original ta |
| 🟡 | `6fdc3e93c` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `f17e65280` | 2026-04-21 | Frontend (UI) | Kanban (vagas) | Fix infinite loop in candidate transition modal — Stabilize object references using useMemo in `useU |
| 🔴 | `77e31602c` | 2026-04-21 | Cross IA↔Front | §16 LIA Persona | Fix infinite loop in modal by stabilizing hook identity — Refactors `useInterpretContext` to ensure  |
| 🟡 | `017013cf8` | 2026-04-21 | Frontend (UI) | §15 WSI | Highlight WSI/Bloom terms in chat replies with hover tooltips (Task #759) — What changed |
| 🟡 | `ae56c0d2d` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `69b7fd1d8` | 2026-04-21 | Cross Back↔Front | §15 WSI | Task #745: Show recruiters the official WSI/Bloom term definitions in chat — What changed |
| 🟡 | `e44362638` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | E10 — Implementar geração de carta-proposta e fluxo de aceite (Task #718) — Adiciona o ciclo complet |
| 🟡 | `14629fdfe` | 2026-04-21 | IA | §3 LIA Maturity — FIX 19 | fix(orchestrator): FIX 19 - wire FIX 15 affirmation into runtime gate (P0) — Audit of FIX 14-17 reve |
| 🟢 | `6128cfff4` | 2026-04-21 | Docs | scope: specs | docs(specs): expand E7-VOZ with full Twilio audio-stream pipeline — Task #703 — Update FLUXO_TECNICO |
| 🟡 | `2f80103aa` | 2026-04-21 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Pass company_id to all remaining LIA SystemPromptBuilder callers — Original task (#694): SystemPromp |
| 🟡 | `464bd2fe1` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update text size for badges to match other elements — Add new components related to the triagem flow |
| 🟡 | `7e76eb465` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Make font size consistent across different screens — Update mockup component imports to ensure consi |
| 🟢 | `5ecb4afde` | 2026-04-21 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #758: Remove "Configurar Etapas" button from job header — - Removed the placeholder "Configurar |
| 🟡 | `e090721ef` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Task #716 — Salvar dados extraidos do site da empresa direto pelo chat (com confirmacao) — Implement |
| 🟡 | `40241fd92` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update mock component definitions for weekly digest — Add weekly digest mock components to the gener |
| 🟡 | `6e16b83c9` | 2026-04-21 | IA | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Integrate glossary term validation into agent system prompts at runtime — Task #700: SystemPromptBui |
| 🟡 | `2de152df0` | 2026-04-21 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Wire send_email/send_whatsapp/schedule_interview to real dispatchers (Task #693) — Original task: Co |
| 🟢 | `966c7ad1f` | 2026-04-21 | Frontend (UI) | Kanban (vagas) | Make saturation badge font size smaller to match other badges — Adjust the SaturationBadge component |
| 🟢 | `49464a0c6` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE K | docs(handoff): PARTE K - FIX 14-17 (conversation continuity layer) — Adds PARTE K documenting 4 fixe |
| 🟡 | `bf506d6f4` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Adjust font sizes in notification and chat components to match design specifications — Update mockup |
| 🟡 | `4ca0b8c58` | 2026-04-21 | Backend | §3 LIA Maturity — FIX 17 | fix(compliance): FIX 17 - capability_truthfulness guardrail (P2) — Bug observed in chat audit 2026-0 |
| 🟡 | `a79295468` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #730: Train meta-question router with new examples (PT-BR variations) — ## Original task |
| 🟢 | `7b2af8baa` | 2026-04-21 | Docs | Tasks #712-#886 (Features de produto) | Task #737: Catch repeated agent mistakes automatically before they ship — Wires the harness-engineer |
| 🟡 | `023148bc3` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `82aa4f6cc` | 2026-04-21 | Docs | §2 Harness / CI sensors | harness-engineering: fill catalogs with real LIA guides and sensors (task #736) — Turned the harness |
| 🟢 | `271ddd5d8` | 2026-04-21 | Testes | Tasks #712-#886 (Features de produto) | Task #717: e2e regression coverage for the onboarding entry flow — Added plataforma-lia/e2e/tests/on |
| 🟡 | `1725eb5ad` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6ad99b6d5` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for weekly digest mockups — Modify `mockup-components.ts` to correctly impo |
| 🟡 | `013add6fe` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | docs: reorganize handoff index and mark glossary as auto-generated — Task #731 — Reorganize handoff  |
| 🟡 | `a62d34c1e` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Add mockups for decision bar components to the generated module map — Update `mockup-components.ts`  |
| 🟢 | `96d5c4f7c` | 2026-04-21 | Docs | Auditoria / Audit Rev | Audit: 4 LIA conversation interpretation failures (Task #738) — Investigation-only task. Produced re |
| 🟡 | `6ce710f4a` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include decision bar mockups — Update `mockup-components.ts` to include  |
| 🟢 | `4a53e019d` | 2026-04-21 | Frontend (UI) | §6 Chat Unificado / Funil | Task #725: Reavaliar ícone do estágio 'enriquecida' no funil de vagas — Reavaliação do ícone do está |
| 🟡 | `58fe6d8d9` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Add toast notifications and template suggestions to mockups — Update generated mockups to include So |
| 🟢 | `3d3a76279` | 2026-04-21 | Docs | §2 Harness / CI sensors | Add harness-engineering meta-skill — Adds the `.agents/skills/harness-engineering/` skill that codif |
| 🟡 | `6ca89c4b3` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `8afc623b0` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #729 — Reconcile recruitment_campaigns schema drift (Alembic 097) — Original task: endpoint /ap |
| 🟢 | `5e7d94102` | 2026-04-21 | Docs | §2 Harness / CI sensors | docs(skills): add harness-engineering-lia skill for auto-activation on LIA stack work — Skill de pro |
| 🟡 | `9fa3a04e3` | 2026-04-21 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include toast notifications — Update the generated mock components file to |
| 🟡 | `8b4aca384` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | ci: enforce tool/action glossary freshness on PRs — Task #733 — wire up an automated gate so the too |
| 🟢 | `a6e1c1743` | 2026-04-21 | Frontend (UI) | Candidates (FE pages) | Improve error handling for transient network failures — Refactor `fetchWithRetry` to distinguish and |
| 🟢 | `97ac557f1` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE J | docs(handoff): PARTE J - A Jornada Completa (narrativa Sessao B com commits reais) — Adiciona narrat |
| 🟡 | `fb636ba3c` | 2026-04-21 | Backend | Backend Services (BE) | Task start baseline checkpoint for code review |
| 🟡 | `8a6a28cb9` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/ |
| 🟡 | `8df3b51fe` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/ |
| 🟡 | `5530d73ed` | 2026-04-21 | Backend | Tasks #712-#886 (Features de produto) | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/ |
| 🟡 | `13076fceb` | 2026-04-21 | Cross IA↔Back | Tasks #712-#886 (Features de produto) | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/ |
| 🟢 | `fcca5b221` | 2026-04-21 | Empty/merge | Tasks #712-#886 (Features de produto) | docs: reorganize handoff index and mark glossary as auto-generated — Task #731 — Reorganize handoff  |
| 🟢 | `cd03d1ebb` | 2026-04-21 | Docs | Tasks #712-#886 (Features de produto) | docs: reorganize handoff index and mark glossary as auto-generated — - Move lia-agent-system/DEVELOP |
| 🟡 | `604438485` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🟡 | `c947826e6` | 2026-04-21 | Frontend (UI) | Tasks #712-#886 (Features de produto) | Task #723 — Auditoria Sparkles vs LIAIcon (Brain ciano = identidade LIA) — - Inventariadas 19 ocorrê |
| 🟡 | `9034a168b` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions li |
| 🟢 | `2ee8ad9af` | 2026-04-21 | Docs | §12 DEVELOPER_HANDOFF — PARTE I | docs(handoff): PARTE I - LIA AI Intelligence (FIX 1-13) no handoff unificado — Adiciona secao PARTE  |
| 🟡 | `2379e592c` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions li |
| 🟡 | `453a46615` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 13 | refactor(obs): FIX 13 - migrate observability to canonical path (ADR-019) — Moves tool_metrics obser |
| 🟡 | `d0a565f95` | 2026-04-21 | Cross IA↔Back | scope: orchestrator | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions li |
| 🟡 | `c15a89862` | 2026-04-21 | Backend | §3 LIA Maturity — FIX 1 | docs: LIA AI intelligence handoff + ADR-019 + glossario regenerado (FIX 1-12) — Documentacao tecnica |
| 🟡 | `1a5f22d5c` | 2026-04-21 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `98b50dd82` | 2026-04-21 | Empty/merge | scope: fluxo-alpha1 | docs(fluxo-alpha1): add CT-ML (11 layers) + CT-CHANGELOG Q1–Q2/2026 (Task #714) — FLUXO_TECNICO_COMP |
| 🟢 | `fad9b239e` | 2026-04-21 | Docs | scope: fluxo-alpha1 | docs(fluxo-alpha1): add CT-ML (11 layers) + CT-CHANGELOG Q1–Q2/2026 (Task #714) — FLUXO_TECNICO_COMP |
| 🟡 | `3f7245f18` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 12 | feat(ai): FIX 12 - HITL envelope + observability module (LangSmith-optional) — G8 - HITL envelope in |
| 🟡 | `cf12c3ec9` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 11 | feat(ai): FIX 11 - actions_context placement + WSI cluster cross-ref — G5 - actions_context placemen |
| 🟡 | `c0a3e3b79` | 2026-04-21 | IA | §3 LIA Maturity — FIX 10 | feat(ai): FIX 10 - wizard YAML coverage + requires_confirmation resolver — G4 - Wizard YAML coverage |
| 🟡 | `896f4ae34` | 2026-04-21 | Backend | §3 LIA Maturity — FIX 9 | feat(ai): FIX 9 - regenerate all weak examples + cover 4 inline-domain files — Quality improvements: |
| 🟡 | `eecf182e7` | 2026-04-21 | Backend | Backend Services (BE) | Task start baseline checkpoint for code review |
| 🟡 | `8e8bfa3bd` | 2026-04-21 | IA | §3 LIA Maturity — FIX 8 | feat(ai): FIX 8 - FairnessGuard enforcement + side_effects field (P1) — G1 — FairnessGuard enforceme |
| 🟡 | `71a2ec1d1` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 5 | feat(ai): FIX 5+6+7 - wizard sync, observability, semantic overlap — FIX 5 (P2): Wizard TOOL_DEFINIT |
| 🟡 | `c9ec97385` | 2026-04-21 | IA | §3 LIA Maturity — FIX 3 | feat(ai): FIX 3+4 - governance_tags HITL enforcement + related_tools suggestions — FIX 3 (governance |
| 🟡 | `4d55b7c40` | 2026-04-21 | Backend | §3 LIA Maturity — FIX 2 | feat(ai): FIX 2 - Populate DomainAction.examples across 13 domains — - Add PT-BR user phrase example |
| 🟡 | `82009b0c8` | 2026-04-21 | Cross IA↔Back | §3 LIA Maturity — FIX 1 | feat(ai): FIX 1 - DomainActions now reach LLM via routing context — - Add DomainPrompt.get_actions_f |
| 🟢 | `4ca80834f` | 2026-04-21 | Empty/merge | scope: fluxo-alpha1 | docs(fluxo-alpha1): add E10–E16 + CT (Chat Unified) + 16-stage status table — Task #713 — documentaç |
| 🟢 | `28e67f22a` | 2026-04-21 | Docs | scope: fluxo-alpha1 | docs(fluxo-alpha1): add E10–E16 + CT (Chat Unified) + 16-stage status table (Task #713) |
| 🔴 | `2f1bd439c` | 2026-04-21 | Cross Back↔Front | scope: auth+fe | fix(auth+fe): JWT blacklist check in get_current_user + CandidatePreview re-export — - dependencies. |
| 🟡 | `b7ac5d94a` | 2026-04-21 | Outro | Refactor / Cleanup | chore: remove stray helper scripts from prior debug sessions |
| 🔴 | `248df840c` | 2026-04-21 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | fix(task-712): address review nits — single prefill + global broadcaster — 1) OnboardingActionOrches |
| 🟢 | `6a4b6844c` | 2026-04-21 | Empty/merge | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #712 — fechar últimos 3 pontos da revisão — Original: conectar 100% do menu Configurações às 7  |
| 🟡 | `0eb9c7013` | 2026-04-21 | Outro | Refactor / Cleanup | chore: remove stray repair_tools.py from prior debugging session |
| 🟡 | `aae815734` | 2026-04-21 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(task-712): close 3 final compliance/registry findings — 1) FairnessGuard recursivo em writes de |
| 🟢 | `18e736d99` | 2026-04-21 | Empty/merge | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do men |
| 🟢 | `c473ee71a` | 2026-04-21 | Frontend (UI) | Bridge React→Vue | feat(task-712): close 3 final findings — useOnboardingFlow + UI->chat bridge — 1) useOnboardingFlow  |
| 🟢 | `b6c590aca` | 2026-04-21 | Empty/merge | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do men |
| 🟡 | `cb56abc90` | 2026-04-21 | Cross IA↔Back | Privacy / PII (W7) | feat(task-712): real PII masking + structured extraction + tool metadata — Closes the 3 remaining fi |
| 🟢 | `a3bd0d6cd` | 2026-04-21 | Empty/merge | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do men |
| 🔴 | `132d74252` | 2026-04-21 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | feat(task-712): close validation gaps — orchestrator, sync, two-phase, tests — Closes the 4 outstand |
| 🟢 | `7b2b63144` | 2026-04-21 | Frontend (UI) | Kanban (vagas) | Add ability to manage job proposals from the kanban board — Integrates a new 'Manage Proposal' actio |
| 🟡 | `1c91a070e` | 2026-04-21 | Backend | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do men |
| 🟢 | `8f3821a6e` | 2026-04-20 | Empty/merge | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do men |
| 🟡 | `bbb362b8b` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | feat(task-712): real benefits write tool + handler delegation — - New _wrap_save_company_benefits in |
| 🟡 | `04b5f8bb0` | 2026-04-20 | Backend | scope: admin-tenant | feat(admin-tenant): Rails ClientAccount sync on client creation — P0 fix — Resolve Admin Tenant Gap: |
| 🟡 | `e8d4bd443` | 2026-04-20 | Backend | Configurações (hub) | Task #712 — onboarding proativo + 7 actions company_settings (post code-review) — Original: conectar |
| 🔴 | `2e826f587` | 2026-04-20 | Cross Back↔Front | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | fix(task-712): align code with doc per code review (5 fixes) — - backend domain.py: configure_benefi |
| 🔴 | `d1ed07e4d` | 2026-04-20 | Cross Back↔Front | Configurações (hub) | Task #712: company_settings delega 7 actions + onboarding proativo — Backend (lia-agent-system): |
| 🟢 | `694561e28` | 2026-04-20 | Docs | scope: fluxo-alpha1 | docs(fluxo-alpha1): add E0 chapter — AI architecture (cognitive layer) — Task #711: insert new chapt |
| 🟡 | `fe94359d1` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `94643fc71` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add toast notifications to the mockups — Update mockups by adding Sonner toast notifications and tem |
| 🟡 | `4a7191d99` | 2026-04-20 | Backend | §1 Teams Integration | Task #706: Configure and validate LIA Microsoft Teams app for production — Audited the Teams integra |
| 🟡 | `14b58f631` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component list to include toast notifications — Updated the generated list of mockup componen |
| 🟡 | `527f2c3ce` | 2026-04-20 | Cross IA↔Back | scope: tools | feat(tools): canonical routing fixes — P0 + P1.A + P1.B + P1.C — Foundation for Tools Unification Mi |
| 🟢 | `1699d7fc9` | 2026-04-20 | Docs | scope: spec | docs(spec): rewrite FLUXO_TECNICO_COMPLETO_ALPHA1.md to v2.0 — reflect atual codebase alpha 1 — Task |
| 🟡 | `ca296ef46` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for decision bar components — Update `mockup-components.ts` to include mockups for E |
| 🟡 | `27aaa3461` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #690: Enriquecer descrições de actions e tools com padrão rico (concluído) — ## O que foi feito |
| 🟡 | `12d77a7cd` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports to include new weekly digest options — Update `artifacts/mockup-sandbo |
| 🔴 | `f05db64d8` | 2026-04-20 | Cross IA↔Front | §8 Glossário / Production-Ready | Task #691: Padronizar domínios em evolução para production-ready — Closes three critical gaps from M |
| 🟡 | `39478a15e` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new toast notification components to the application — Update mockup-components.ts to include So |
| 🟡 | `4930b4092` | 2026-04-20 | Cross IA↔Back | §8 Glossário / Production-Ready | feat(docs): Task #692 — Glossário Central + sync automático + CI guard — ## O que foi entregue |
| 🟡 | `e3148e156` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new components for the weekly digest feature — Update mockup-components.ts to include new compon |
| 🟡 | `4375bf0ee` | 2026-04-20 | Backend | §8 Glossário / Production-Ready | Task #687: Extend execute_action coverage to remaining 7 domains — Original task: Task #674 covered  |
| 🟡 | `cbd2fc899` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `c4240f79f` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include new weekly digest features — Reorganize module map to correctly  |
| 🟢 | `596c9c5e5` | 2026-04-20 | Testes | §8 Glossário / Production-Ready | test(execute_action): cobertura + tenant-isolation audit para 11 dominios — Task #674. Fecha o gap P |
| 🟡 | `498022c78` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new UI components for displaying notifications and suggestions — Update mockup-components.ts to  |
| 🟡 | `6e9287f50` | 2026-04-20 | Backend | §8 Glossário / Production-Ready | docs: ADR-019 + glossário 281 actions/94 tools + MAPA 18 domínios — Original task #671: criar ADR-01 |
| 🟡 | `454ffd9e3` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add a new component for ElevenLabs funnel functionality — Update mockup-components.ts to include the |
| 🟡 | `2f19de689` | 2026-04-20 | Backend | §9 Tenant Isolation / Multi-tenancy | Task #673: Consolidate tenant-isolation residual (closes #329, #335, #336, #359, #361) — Five separa |
| 🟡 | `609745151` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for mockups to include new items — Update the generated component mapping f |
| 🟡 | `21f90805f` | 2026-04-20 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Task #672 — DEFAULT_DOMAIN routing warning + chat-capabilities CI gate — Closes Fase 2C P0-2 (silent |
| 🟡 | `c232fd6bb` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups sandbox for testing — Add new component imports to the mockups san |
| 🟡 | `4b95f2868` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #670 — Proteger 8 dirs estratégicos e recategorizar — Original task: a auditoria Fase 2C marcav |
| 🟡 | `2dec6d172` | 2026-04-20 | Frontend (UI) | §15 WSI | fix(wsi): Corrigir painel Descrição do Cargo (task #664) — ## Problemas corrigidos |
| 🟢 | `8c0f30565` | 2026-04-20 | Frontend (UI) | i18n / Translation | feat(i18n): add automated i18n missing-key guardrail (#663) — ## Summary |
| 🟡 | `3a20076cd` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add a new component to the sandbox for ElevenLabs funnel mockups — Add a mapping for the FunilEleven |
| 🟢 | `3ce45c7b3` | 2026-04-20 | Frontend (api/util) | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Add missing insertTitle and insertAriaLabel translations for chat message actions — Task #661: Add m |
| 🟡 | `8212c96e5` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `09f34a144` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include new decision bar mockups — Modify `mockup-components.ts` to regi |
| 🟡 | `974282fe1` | 2026-04-20 | Backend | Fase 2C_DOMAIN_VERIFICATION_REPORT.MD | docs: rewrite fase2c_domain_verification_report.md — auditoria estratégica 20/abr/2026 — Task #657 — |
| 🟡 | `d2772e782` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `ac9069ab3` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include new decision bar components — Reorganize mockup component imports, adding  |
| 🟢 | `e29756370` | 2026-04-20 | Testes | §7 WorkflowRail UX | Add regression test for WorkflowRail thinking pulse (Task #655) — Adds an integration test at |
| 🟡 | `6c7fa4b19` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include new toast notifications and adjust component imports — Refactor mockup com |
| 🟢 | `f16c79a62` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Show LIA's thinking pulse inside the WorkflowRail popover — Task #654 follows up on #653, which surf |
| 🟡 | `62c5689c4` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `0496cf198` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add ElevenLabs funnel component to the mockup sandbox — Add a new component import for the FunilElev |
| 🟢 | `d0c224c83` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Wire workflow:thinking event into WorkflowRail (Sprint UX-7) — Task #653 — Complete the WorkflowRail |
| 🟡 | `3897bc42a` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6ca16aa36` | 2026-04-20 | Backend | §17 Eval Framework | Improve agent evaluation by removing handshake and adding new scenarios — Remove handshake logic fro |
| 🟢 | `63c21738e` | 2026-04-20 | Docs | §11 Candidate Portal | docs: add real commit hashes to CANDIDATE_PORTAL_RAILS_SPEC |
| 🟡 | `71bb979a3` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for toast notifications and ElevenLabs funnel — Update mockup component imports, repl |
| 🟢 | `df34f5707` | 2026-04-20 | Docs | §12 DEVELOPER_HANDOFF — PARTE I | docs(handoff): PARTE I — BETA badge polish, hide chat/rail on auth routes, e2e test fixes — Task #65 |
| 🟡 | `0b3caa28c` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `1b0ca9629` | 2026-04-20 | Docs | §11 Candidate Portal | docs: CANDIDATE_PORTAL_RAILS_SPEC.md spec completa Rails + Replit |
| 🟢 | `03440865d` | 2026-04-20 | Frontend (UI) | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #650: BETA badge polish + hide chat/rail on auth routes — Changes: |
| 🟡 | `be607d82a` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `019c35c9a` | 2026-04-20 | Testes | UX / Mockups | Update mockups and agent test configurations — Update mock component imports and agentic evaluation  |
| 🟢 | `9d0218eb7` | 2026-04-20 | Frontend (UI) | scope: ui | feat(ui): make BETA badge blue, smaller, and with smaller font — Task #649: Deixar badge BETA azul,  |
| 🟡 | `591441554` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `f1134ff0f` | 2026-04-20 | Backend | §17 Eval Framework | Update automated tests to correctly handle authentication and test scenarios — Modify the agentic ev |
| 🟢 | `6aa9492fb` | 2026-04-20 | Docs | §12 DEVELOPER_HANDOFF — PARTE H | docs(handoff): PARTE H — chat ReAct, stub→real, scheduling, WSI tenant, WorkflowRail UX, IDOR — Adic |
| 🟡 | `1adc24fcc` | 2026-04-20 | Backend | §17 Eval Framework | Add evaluation log for agentic runs — Add a new JSON file containing evaluation metadata and results |
| 🟢 | `e1eb1ed58` | 2026-04-20 | Testes | scope: e2e | test(e2e): use /pt/chat instead of /dashboard in auth fixture — /dashboard returns 404 in dev mode;  |
| 🟡 | `5b3a85cad` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Organize toast mockup component imports for better structure — Update mockup component import order  |
| 🟡 | `9c7e65855` | 2026-04-20 | IA | §15 WSI | Task #334 — Forward recruiter tenant id through WSI on-the-fly question pipeline — Original task: Wh |
| 🟢 | `ae21f9542` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | feat(ui): redesign WorkflowRail floating ball + compact BetaBadge — Task #648: resolve visual collis |
| 🔴 | `f2699be3f` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | feat(ui): redesign WorkflowRail floating ball + compact BetaBadge — Task #648: resolve visual collis |
| 🟡 | `e5a0787aa` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `04ff86a65` | 2026-04-20 | Docs | §12 DEVELOPER_HANDOFF — PARTE G | docs(handoff): PARTE G — LIA Eval 62→70/73, 15 fixes documentados com checklist de reprodução |
| 🟡 | `efe036a83` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new components for a triagem flow to the application — Update mockup-components.ts to include ne |
| 🟡 | `6fd638fbc` | 2026-04-20 | Backend | §9 Tenant Isolation / Multi-tenancy | tests: assert tool registries fail-closed without company_id — Task #330: add an end-to-end test tha |
| 🟡 | `086641ef8` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for triagem flow components — Re-add triagem flow components to mockup-components.ts  |
| 🟡 | `4207bf817` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include a new funnel component — Update `artifacts/mockup-sandbox/src/.generated/m |
| 🟡 | `97205ecc1` | 2026-04-20 | Backend | Task #306 | Task #306 — Fix IDOR on /finetuning/stats and /finetuning/export — Audit finding R1: /finetuning/sta |
| 🟡 | `bd5a3c442` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `9bc805b29` | 2026-04-20 | Frontend (UI) | Task #300 | Task #300: align chat slash commands across product, code, and docs — - Decision: keep the existing  |
| 🟡 | `0f1a21dde` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `5e2c78aed` | 2026-04-20 | Frontend (UI) | Task #288 | Task #288: Remove duplicate useCandidatesExecuteSearch.ts (dead code) — Removed legacy file: |
| 🟢 | `93a88173b` | 2026-04-20 | Frontend (UI) | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Persist recruiter's last active funnel stage across sessions — Task #588: The WorkflowRail wide bar  |
| 🟡 | `e5299e769` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update weekly digest components for mockups — Update artifacts/mockup-sandbox/src/.generated/mockup- |
| 🟢 | `8cd82e847` | 2026-04-20 | Docs | ADR-018 | docs(adr): add ADR-018 — operational consolidation plan for tool registry (Task #382) — Original tas |
| 🟢 | `6dceda378` | 2026-04-20 | Docs | scope: audit | docs(audit): correct stale "dead code" claims for tool_permissions loader and registry.py — Task #38 |
| 🟡 | `09a29366d` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest components to the mockups — Update mockup-components.ts to include new components  |
| 🟡 | `709659f8a` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new components for chat welcome polish — Update mockup-components.ts to include new chat welcome |
| 🟡 | `d9127032c` | 2026-04-20 | Backend | Tests (BE unit/integration) | Fix conversation summary crash from missing _extract_structured_ids helper — Original task (#637): ` |
| 🟢 | `b3d068c9c` | 2026-04-20 | Testes | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Add CI smoke test for chat capabilities audit (Task #633) — Wraps `lia-agent-system/scripts/audit_ch |
| 🟡 | `9aa587053` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new components for toasts and welcome polish mockups — Update mockup-components.ts to include ne |
| 🟡 | `7670dfb5b` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #609 — Mostrar campanhas reais no rail e no badge — Replace the placeholder `not_implemented` b |
| 🟡 | `bc41ff494` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new triagem flow screens — Replaces toasts-sonner mockups with tri |
| 🟡 | `8fee1b64a` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new UI components for chat and triage screens — Update artifacts/mockup-sandbox/src/.generated/m |
| 🟡 | `ceb6c78fa` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Fix stale import paths across backend (task #585) — Followed up on task #581 (which fixed a single ` |
| 🟡 | `e8e162949` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `43d9891d3` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Wire up duplicate_job and clone_job chat actions (Task #624) — Original task: finish the deferred 'd |
| 🟡 | `9bbb304be` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #623: Remove unused 'score_cv' chat tool from cv_screening domain — The score_cv tool was a thi |
| 🟡 | `c78584eb1` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `c8559a442` | 2026-04-20 | Backend | §1 Teams Integration | Send interview reminders over WhatsApp and Teams, not just email (Task #626) — Verified that Schedul |
| 🟡 | `933949c9f` | 2026-04-20 | Cross IA↔Back | Scheduling / Calendar (PR-CAL) | Fix mismatched scheduling-link database schema (Task #625) — The SelfSchedulingLink SQLAlchemy model |
| 🟡 | `8062dff21` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include a new funnel feature — Update mockup-components.ts to include th |
| 🟡 | `92e6fe1c8` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Replace recruiter-goals stub with real OKR/quota analytics (Task #599) — The `assistant_track_goals` |
| 🟡 | `8c0e472d0` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new chat components to the mockups — Update mockup-components.ts to include new entries for Elev |
| 🟡 | `2bf526354` | 2026-04-20 | Cross IA↔Back | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Task #552: Echo routed specialist on chat replies — The persona-diagnostic routing audit (Task #537) |
| 🟡 | `152625d10` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to improve card and badge styling for better visual consistency — Add two new mockups |
| 🟡 | `985cb54bd` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Restore Sourcing ReAct agent's full tool set — Task #596: The Sourcing ReAct agent's `_aggregate_all |
| 🟢 | `3d6328f02` | 2026-04-20 | Testes | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Task #558: Verify per-agent AI billing end-to-end with automated tests — Adds tests/test_per_agent_b |
| 🟡 | `32f36cf9c` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new toast notifications — Replaces weekly digest mock components w |
| 🟢 | `b5455e013` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Track WorkflowRail next-step clicks and panel toggles (Task #589) — What |
| 🟡 | `b0209e7c8` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports for toasts and weekly digest features — Replace toast component import |
| 🟡 | `f539d14c1` | 2026-04-20 | Backend | scope: cv-screening | fix(cv_screening): unify _ACTION_TOOL_MAP, close last audit gap — Original task #597: Apply the cano |
| 🟡 | `fbe592761` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #604: Padronizar identidade dos domínios para usar atributos simples — Original task: JobCreati |
| 🟡 | `69825249d` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock component definitions for weekly digest — Update mock component definitions by adding we |
| 🟡 | `8a2f575ef` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new UI components for various platform features — Add mock component definitions for Sonner Toas |
| 🟡 | `cdaa7b2c6` | 2026-04-20 | Backend | Scheduling / Calendar (PR-CAL) | Wire real interview reminders and self-scheduling links (Task #598) — Replaces the two `simulation_s |
| 🟡 | `3e17624ea` | 2026-04-20 | Outro | Artefatos / Eval logs (sem código) | Task #601: Conectar handlers quebrados de tools de chat aos serviços reais — Verified the work was a |
| 🟢 | `d689a913c` | 2026-04-20 | Frontend (UI) | Configurações (hub) | Adjust user card styling to match table density — Update user list component to apply compact stylin |
| 🟡 | `075ac39ba` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add new UI components for testing different chat and toast functionalities — Update mockup component |
| 🟡 | `42c9ce4d2` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #602: Replace stub/fallback handlers with real implementations or explicit errors — - agent_stu |
| 🟡 | `ebe6d4b72` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include toast notifications — Update artifacts/mockup-sandbox/src/.generat |
| 🟡 | `bd974aea4` | 2026-04-20 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #620: Surface ReAct tool calls on the chat HTTP response (LIA-LCF-01) — When recruiters asked v |
| 🟡 | `3ddf714a8` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `eafe4f551` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Task #617 — WorkflowRail × Chat: coexistência sem poluição — Faz o trilho de fluxo flutuante (barra/ |
| 🟡 | `a8091fb14` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `f027fa26e` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Fix WorkflowRail overlay blocking chat send button — Task #618: The WorkflowRail's centered row wrap |
| 🟡 | `d64e9bfd8` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `d88ae9ff7` | 2026-04-20 | Backend | §17 Eval Framework | task-616: Run agentic eval suite end-to-end and produce consolidated .md report — ## Original Task |
| 🟡 | `193ffe0c4` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `9eccec89d` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Add a toggle button to control the workflow rail feature — Implement a new toggle button in the side |
| 🟢 | `86e997a8a` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | Restore compact workflow rail with smaller design and theme toggle — Restores the WorkflowRail compo |
| 🟡 | `f770ad6fb` | 2026-04-20 | Outro | (Auto-commit Replit) | Restored to 'c07d3d5dcc2faeb18d2dba7732bb07f02cc66d3a' — Replit-Restored-To: c07d3d5dcc2faeb18d2dba7 |
| 🟡 | `c11e4a096` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add a button to easily return to the chat interface — Add new mock components for chat and workflow  |
| 🟢 | `c07d3d5dc` | 2026-04-20 | Frontend (UI) | §7 WorkflowRail UX | feat(workflow-rail): compact single-line bar with per-stage hover popovers and improved contrast — T |
| 🟡 | `c4c5c8609` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `a2b5eb13a` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `845891d49` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add a button to return to the chat from other sections — Adds a "back to chat" button to the workflo |
| 🟡 | `85ba10dd2` | 2026-04-20 | Outro | (Auto-commit Replit) | Restored to 'bf0398f7a65b08de34b7366fc0e160dd4b8cc469' — Replit-Restored-To: bf0398f7a65b08de34b7366 |
| 🟡 | `e746f47b6` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟡 | `3ff9c7f1c` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🔴 | `bf0398f7a` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | Add a button to return to the chat from other sections — Adds a "Back to Chat" button to the workflo |
| 🔴 | `11389ca5e` | 2026-04-20 | Cross Back↔Front | §7 WorkflowRail UX | Update workflow rail component to match BP7 design standards — Refactors the WorkflowRail component  |
| 🟡 | `11e1a9a3e` | 2026-04-20 | Backend | §7 WorkflowRail UX | Add scrollable workflow rail with magnifier effect and theme toggle — Implement a horizontal scrolli |
| 🟡 | `a86b365a9` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Remove standalone "Create vacancy" button and integrate into workflow — Integrate the "Create vacanc |
| 🟡 | `07ec12d20` | 2026-04-20 | Backend | Mockup Sandbox (artefato gerado) | Make the workflow display more compact and contextual — Introduce a new compact workflow variant wit |
| 🟡 | `d73102661` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add two polished variations of the workflow progress tracking component — Introduce two refined vers |
| 🟡 | `3adb6be16` | 2026-04-20 | Backend | §7 WorkflowRail UX | Add three workflow rail variants optimizing usability — Adds three distinct workflow rail components |
| 🟡 | `899dddab6` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add three new layout variations for the workflow rail component — Implement CenteredHub, StackedVert |
| 🟡 | `bfc1ebfa2` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add refined workflow rail components with improved visual appeal — Introduce two new variants of the |
| 🟡 | `2668747b5` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add three variations for component usability with different design trade-offs — Introduces three new |
| 🟡 | `734a98115` | 2026-04-20 | Backend | §7 WorkflowRail UX | Add four distinct workflow rail variations for user selection — Introduce new React components for B |
| 🟡 | `6f04b2f76` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Add refined workflow rail component variations — Introduce two new variations of the WorkflowRail co |
| 🟡 | `e19b79f7d` | 2026-04-20 | Backend | §7 WorkflowRail UX | Add three compact workflow rail variations for user selection — Introduce three distinct mockup comp |
| 🟢 | `f3ddab57b` | 2026-04-20 | Docs | §6 Chat Unificado / Funil | docs(produto): especificação da Fase 2 do funil unificado — Task #593 — produzir o documento técnico |
| 🟡 | `ef40db8ce` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `aa2909f40` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update mock component list to include new funnel and triage flows — Update artifacts/mockup-sandbox/ |
| 🟡 | `6d54e43d4` | 2026-04-20 | Frontend (UI) | §6 Chat Unificado / Funil | Task #592: Funil unificado — Fase 1 (educativa) — Unificou o vocabulário e a identidade visual do fu |
| 🟡 | `bbc56ebcb` | 2026-04-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `c691516b1` | 2026-04-20 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include triagem-flow mockups — Reorder and add imports for triagem-flow  |
| 🟡 | `09951594f` | 2026-04-20 | Backend | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #591 — Encerrar #580 com qualidade (5 achados de code review) — Original: code review da #580 r |
| 🟡 | `36065d92c` | 2026-04-20 | Backend | §17 Eval Framework | Reduce delay between test case executions — Shorten the sleep duration between individual test case  |
| 🟡 | `f40e2c24c` | 2026-04-20 | Backend | Artefatos / Eval logs (sem código) | Update audit logs and evaluation results to reflect job creation changes — Adds new entries to audit |
| 🟢 | `a39b48d5f` | 2026-04-20 | Docs | §7 WorkflowRail UX | docs(ux): UX_REDESIGN_COMPETITIVO_SPEC.md — especificacao tecnica completa (Sprints UX-1 a UX-7) |
| 🟡 | `521b9e243` | 2026-04-20 | Backend | §6 Chat Unificado / Funil | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos vali |
| 🟡 | `5cf89193e` | 2026-04-20 | Backend | §6 Chat Unificado / Funil | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos vali |
| 🟡 | `a174d7d67` | 2026-04-20 | Cross IA↔Back | §6 Chat Unificado / Funil | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos vali |
| 🔴 | `c6220768f` | 2026-04-20 | Cross IA↔Front | Unified Chat (FE) | Improve job creation and candidate sourcing workflows — Update job vacancy fields, fix action IDs, c |
| 🟡 | `d46fd1dae` | 2026-04-19 | Outro | Refactor / Cleanup | Remove unnecessary data from the system — Remove a leftover data artifact from the system. |
| 🟡 | `d63271238` | 2026-04-19 | Backend | Mockup Sandbox (artefato gerado) | Add new components and evaluation results for job postings — Updates mockup components and adds new  |
| 🟡 | `9eafa6207` | 2026-04-19 | Cross IA↔Back | scope: tools | fix(tools): P0/P1 hardening — multi-tenancy + capacity + factory bypass — - executor.py: execute_bat |
| 🟡 | `cd89fcf8f` | 2026-04-19 | Frontend (api/util) | scope: eval | feat(eval): unified diagnostic battery for LIA via Playwright (task #603) — ## What was built |
| 🟡 | `860d1b3fa` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `22d0f1da4` | 2026-04-19 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #582: Phase 2 chat sanitization for the 5 P1 domains — Make every chat tool registered in ats_i |
| 🟡 | `d312e34dd` | 2026-04-19 | Cross IA↔Back | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | Task #584 — Auto-discovery of AGENT_TYPE_TO_DOMAIN — Replaces the hand-maintained dict in app/orches |
| 🟡 | `de09438ec` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6ede7b7c9` | 2026-04-19 | Backend | §6 Chat Unificado / Funil | Task #583: zero actions sem tool nem handler no chat unificado — Resolvi as 146 actions sem caminho  |
| 🟡 | `fe47e4d0d` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `b1e9dc6bf` | 2026-04-19 | Backend | §6 Chat Unificado / Funil | fix(sourcing): saneamento canônico do domínio (task #579) — Corrige 3 defeitos canônicos no Sourcing |
| 🟡 | `7bef1cb42` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `da11f25c7` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `bb48ae14c` | 2026-04-19 | Backend | Compliance / LGPD / EU AI Act | feat: rails_client wrapper + patch method for rh_dashboard LGPD |
| 🟢 | `8c3c2eb71` | 2026-04-19 | Docs | Policy / Job Creation | Update audit documentation to reflect new hiring policy actions — Modify `chat_capabilities_audit.js |
| 🟡 | `260a8bf22` | 2026-04-19 | Backend | Compliance / LGPD / EU AI Act | fix(rh-dashboard): correct APIResponse import + Next.js LGPD proxy routes — - rh_dashboard.py: wrong |
| 🟡 | `421cfdb99` | 2026-04-19 | Backend | §6 Chat Unificado / Funil | Task #580 — Saneamento da cadeia de execução do chat unificado (Fase 1, P0) — Eliminados handlers qu |
| 🟢 | `287e5a19d` | 2026-04-19 | Docs | Docs / Handoff | docs: secao 14 Claude Code usage guide paths canonicos |
| 🟡 | `fddbc96ae` | 2026-04-19 | IA | §2 Orchestrator Migration | Improve candidate comparison fallback for agentic loop — Modify the candidate comparison logic to re |
| 🟡 | `fe9f7f329` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results for job management tests — Update lia-agent-system/eval/eval_results_20260 |
| 🟡 | `536f3fc6b` | 2026-04-19 | Frontend (UI) | §7 WorkflowRail UX | feat(workflow-rail): redesign WorkflowRail as a wide predictive funnel bar — Task #587 — Workflow Ra |
| 🟡 | `30c51681f` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `9ebfa3359` | 2026-04-19 | Cross Back↔Front | Configurações (hub) | Add functionality to manage candidate requests and improve system stability — Introduce new API endp |
| 🔴 | `e3c1ed576` | 2026-04-19 | Cross IA↔Front | Job Management (BE) | Improve job management and candidate comparison tools — Refactors job management tools to use a dedi |
| 🔴 | `1122226d3` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | chore(chat): saneamento Fase 1 (P0) da cadeia de execução do chat unificado — Task #580 — auditoria  |
| 🟡 | `94aba8ebe` | 2026-04-19 | Cross IA↔Back | Communication domain (BE) | Update system to properly expose tool handlers and improve robustness — Refactors service layer to e |
| 🟡 | `a060038c6` | 2026-04-19 | Backend | Backend Services (BE) | Add audit script to verify chat capabilities and update documentation — Introduce a Python script to |
| 🟢 | `3722e7b38` | 2026-04-19 | Docs | §12 DEVELOPER_HANDOFF — PARTE F | docs(handoff): PARTE F section — conversational UX + P2/P3 hardening complete — F.1: scrape website  |
| 🟡 | `104bc6356` | 2026-04-19 | Backend | Compliance / LGPD / EU AI Act | fix(compliance): P3#11 + P2#8 — FairnessGuard API + LGPD consent cache — P3#11 — fix FairnessGuard A |
| 🟢 | `40a793a01` | 2026-04-19 | Empty/merge | (Auto-commit Replit) | merge: bring 'Saved your changes before starting work' from wedotalent/replit-sync into local main |
| 🔴 | `744e161de` | 2026-04-19 | Cross IA↔Front | Frontend (componentes diversos) | Update candidate status page and chat features — Integrate the candidate chat feature with backend A |
| 🟢 | `4a762e0ca` | 2026-04-19 | Frontend (UI) | §11 Candidate Portal | Add candidate portal for job application status and chat — Add new files to manage candidate applica |
| 🟡 | `f66703bee` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for report and weekly digest mockups — Update generated file `mockup-compon |
| 🟢 | `6d4c50d4b` | 2026-04-19 | Docs | §11 Candidate Portal | Task #576 — Proposta de construção do chat candidato pós-aplicação (LIA) — Original task: produzir u |
| 🟡 | `3db413278` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `3d33be44f` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for weekly digest and report tabs — Reorder module imports in mockup-compon |
| 🟡 | `3516036ec` | 2026-04-19 | Backend | §11 Candidate Portal | Task #574 — Auditoria técnica do chat candidato pós-aplicação (LIA) — Original: produzir documento d |
| 🟢 | `fc76b0a88` | 2026-04-19 | Docs | scope: handoff | docs(handoff): DEVELOPER_HANDOFF.md guia completo PARTES A-E — Documento unico de referencia tecnica |
| 🟡 | `c8914da1f` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update mock component registration to include new chat elements — Update artifacts/mockup-sandbox/sr |
| 🟢 | `8712157b6` | 2026-04-19 | Docs | §11 Candidate Portal | docs(research): market research — chat candidato pós-aplicação — Original task #575: pesquisa de mer |
| 🟢 | `5e6356846` | 2026-04-19 | Frontend (UI) | Unified Chat (FE) | Update chat to hide superseded assistant messages and test hydration — Add state to track superseded |
| 🔴 | `0120f8d7e` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no A |
| 🔴 | `f94022429` | 2026-04-19 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no A |
| 🟢 | `3b9f715ac` | 2026-04-19 | Docs | §6 Chat Unificado / Funil | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — A |
| 🟡 | `98f2c5c45` | 2026-04-19 | IA | §2 Orchestrator Migration | Update database query to correctly reference company ID — Update the SQL query in `candidate_actions |
| 🔴 | `8314d3517` | 2026-04-19 | Cross IA↔Front | §12 DEVELOPER_HANDOFF — PARTE D | fix(parte-d): close 4 PARTE D gaps — full tracking + canonical schema + manifest wiring + proactive  |
| 🟡 | `ce507b683` | 2026-04-19 | IA | §13 PARTE D — Foundation/Apify/Manifest | Add fallback for navigation intent patterns if manifest is unavailable — Modify `navigation_intent.p |
| 🟢 | `fd420cc96` | 2026-04-19 | Empty/merge | §6 Chat Unificado / Funil | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — A |
| 🟡 | `3139e3e7f` | 2026-04-19 | Cross IA↔Back | §6 Chat Unificado / Funil | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — A |
| 🟢 | `8140aa421` | 2026-04-19 | Docs | §6 Chat Unificado / Funil | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — A |
| 🟡 | `3690c9fb4` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `3464e6021` | 2026-04-19 | Backend | Configurações (hub) | feat(company): D5 guided onboarding flow in company_settings agent — Extends existing CompanySetting |
| 🟡 | `f4106776c` | 2026-04-19 | Cross IA↔Back | §13 PARTE D — Foundation/Apify/Manifest | feat(platform): D4 Platform Manifest — single source of truth for pages, methodology, capabilities — |
| 🟡 | `08a912340` | 2026-04-19 | IA | §13 PARTE D — PreConditionChecker | feat(orchestrator): D2 PreConditionChecker +5 new proactive checks — Extended PreConditionChecker fr |
| 🟡 | `eee514587` | 2026-04-19 | Cross IA↔Back | Configurações (hub) | feat(lia-tools): D1 enrichment + company settings tools — D1.a enrichment_tools.py (sourcing domain, |
| 🟡 | `fe5a0ac75` | 2026-04-19 | Backend | Mockup Sandbox (artefato gerado) | Make database migration idempotent to prevent creation errors — Update migration script 095 to check |
| 🔴 | `43e417b0e` | 2026-04-19 | Cross Back↔Front | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Fix message actions in unified chat (copy, thumbs) — Task #567: The copy / thumbs / "+" buttons unde |
| 🟡 | `3d79832a9` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `58009608b` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🟡 | `b90eb3cfe` | 2026-04-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Enhance AI tracking durability and fairness checks — Implement an outbox pattern for AI usage tracki |
| 🟡 | `a2b2310fb` | 2026-04-19 | Backend | §13 PARTE D — Foundation/Apify/Manifest | feat(apify): D0 gateway — enforced tracking + budget check per tenant — Refactor ApifyService.run_ap |
| 🟡 | `82024c586` | 2026-04-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Add functionality to extract candidate names and reasons for rejection — Enhance the `reject_candida |
| 🟡 | `30359ced0` | 2026-04-19 | Cross IA↔Back | scope: lia-agent | feat(lia-agent): LIA Deep Audit P2 fixes (C3, D10) — C3 conversation_memory.py: |
| 🟡 | `48fc90c2b` | 2026-04-19 | Cross IA↔Back | §2 Orchestrator Migration | Add ability to reject candidates and improve job duplication — Introduce the `reject_candidate` inte |
| 🟡 | `a64fcf7df` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update toast notification components for improved display — Rearrange import order for SonnerToasts  |
| 🔴 | `fb079b207` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | Task #563: agentic eval framework + canonical-fix consolidation — Original: build exhaustive 10-dime |
| 🟡 | `683a3c155` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `2dcd28894` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `5d34569ef` | 2026-04-19 | Docs | §14 BYOK + LLM Factory | docs(byok): section 12 — checklist dev + mapa completo 54 consumidores LLM — Section 12: Guia do Des |
| 🟡 | `8bb172145` | 2026-04-19 | Backend | §15 WSI | fix(byok): BUG-07 WSI analyze-response BYOK + Quality Tier Guard — _shared.py get_anthropic_client() |
| 🟢 | `9eca3ac23` | 2026-04-19 | Docs | §14 BYOK + LLM Factory | docs(byok): section 11 - auditoria profunda + inventario de bugs corrigidos — Section 11: Auditoria  |
| 🟡 | `b4218eace` | 2026-04-19 | Cross IA↔Back | §14 BYOK + LLM Factory | fix(byok): corrigir 4 bugs P0 de audit trail e BYOK bypass — BUG-01: llm_factory._audit_llm_usage()  |
| 🟢 | `0b6e1ae39` | 2026-04-19 | Docs | §14 BYOK + LLM Factory | docs(byok): secoes 9+10 — frontend UI + auditoria E2E — Secao 9: Interface do cliente (Choose Your A |
| 🟡 | `6535f4cd1` | 2026-04-19 | Backend | UX / Mockups | Add end-to-end tests for job listings and update mockups — Adds new E2E tests for the `/vagas` endpo |
| 🟢 | `f4462e2ab` | 2026-04-19 | Docs | §14 BYOK + LLM Factory | docs(architecture): ADR-018 LLM Factory / BYOK contract — Documenta o LLM Factory como componente ar |
| 🟢 | `c00ac25df` | 2026-04-19 | Frontend (UI) | Kanban (vagas) | Add semantic icons to job cards for better visual representation — Update KanbanCard component, test |
| 🟢 | `aa6d38cd1` | 2026-04-19 | Docs | §14 BYOK + LLM Factory | feat(llm-factory): BYOK compliance + Quality Tier Guard + audit trail — LIA-BYOK B1: WARN [LIA-BYOK] |
| 🔴 | `c5b577cf5` | 2026-04-19 | Cross IA↔Front | Kanban (vagas) | Task #562 — Padronizar e enriquecer card do Kanban de Vagas — Alinha o card de vaga (página /jobs, v |
| 🟡 | `6590ad88e` | 2026-04-19 | Frontend (UI) | Kanban (vagas) | Task #562 — Padronizar e enriquecer card do Kanban de Vagas — Alinha o card de vaga (página /jobs, v |
| 🟡 | `3af295565` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `39e61c38f` | 2026-04-19 | Testes | §18 Senioridade + Job Migration | test(jobs): cobertura ponta-a-ponta de edição de senioridade (Task #560) — Adiciona um teste de flux |
| 🟡 | `88e99735d` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for WSI report and Teams adaptive card — Reorganizes and updates import pat |
| 🟡 | `bbda8220c` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include recent additions — Reorder entries in `mockup-components.ts` to gr |
| 🟡 | `9f6371873` | 2026-04-19 | Frontend (UI) | §18 Senioridade + Job Migration | Task #559 — Show "Senioridade não informada" instead of guessing "Pleno" — Problem: when the backend |
| 🟡 | `0ebda12cc` | 2026-04-19 | IA | §15 WSI | Backfill transparency_extras for legacy WSI response analyses (task #534) — Original task: rows in ` |
| 🟡 | `77247d615` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `32cd180b4` | 2026-04-19 | Empty/merge | §16 LIA Persona | fix(lia-persona): corrige 23 falhas críticas do diagnóstico de persona (120 sondas) — FASE 1 — main_ |
| 🟡 | `0bb43c682` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest components to mockups — Update mockup components to include weekly digest componen |
| 🟡 | `3de3ce2ba` | 2026-04-19 | Cross IA↔Back | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Extend AI cost tracking across LIA strategic flows (task #545) — Task #532 only instrumented WSI Lay |
| 🟡 | `991521fd6` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for chat usability and triage flows — Update artifacts/mockup-sandbox/src/.generated |
| 🟡 | `80131539d` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Update mockup component mappings to include previously omitted files — Reorder and add mock componen |
| 🟡 | `dfda1e1a4` | 2026-04-19 | Frontend (UI) | §18 Senioridade + Job Migration | Task #539 — Remove legacy `level` field from Job type — After the observation window from Task #531  |
| 🟡 | `a2a57f8e8` | 2026-04-19 | Backend | §16 LIA Persona | Persona Diagnostic: cross-check probes really hit the intended specialised agent — Task #537. The pe |
| 🟡 | `d924e5557` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6b4cf486b` | 2026-04-19 | Cross IA↔Back | Privacy / PII (W7) | Reforça regex de ANO_FORMATURA em pii_masking (task #549) — Achado #3 da investigação Presidio (#533 |
| 🟡 | `a4b1db2d1` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `631cdf978` | 2026-04-19 | Backend | Offer Review (PR-B) | fix eval CO-002: add offer letter generation instruction to communication domain |
| 🟡 | `a43585eff` | 2026-04-19 | Outro | Mockup Sandbox (artefato gerado) | Add toast notification components for user feedback — Add new mock components for toast notification |
| 🟡 | `69b21b939` | 2026-04-19 | IA | §15 WSI | Fix WSICompactPipeline LLM call and add regression tests (Task #541) — Original task: Compact Mode q |
| 🟡 | `0bce0e5f9` | 2026-04-19 | Frontend (UI) | Kanban (vagas) | Add "Apenas modo degradado" toggle to job kanban (Task #538) — Original task |
| 🟡 | `a43abc1e9` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results to reflect job listing and active job status — Adds new entries to the eva |
| 🟡 | `506cd0549` | 2026-04-19 | Cross IA↔Back | §15 WSI | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) + fix(query_tools): corr |
| 🔴 | `48c9bf2c8` | 2026-04-19 | Cross IA↔Front | §15 WSI | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) — Adiciona testes de com |
| 🟢 | `ece880097` | 2026-04-19 | Testes | §15 WSI | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) — Adiciona testes de com |
| 🟡 | `805502657` | 2026-04-19 | Cross IA↔Back | i18n / Translation | fix eval: UnboundLocalError in executor + short job_id in query_tools |
| 🟡 | `e1d1aee87` | 2026-04-19 | Backend | §17 Eval Framework | Task start baseline checkpoint for code review |
| 🟡 | `e3f6638ef` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results with new test cases and responses — Add new entries to evaluation result J |
| 🟡 | `bafaea563` | 2026-04-19 | IA | §2 Orchestrator Migration | fix eval: fix uuid/varchar JOIN mismatch in candidate/sourcing pipeline |
| 🟡 | `e12009486` | 2026-04-19 | IA | §2 Orchestrator Migration | fix eval CM-001/CM-003: remove all wrong CAST uuid on varchar columns in candidate pipeline |
| 🟡 | `64ffd1f4e` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results with detailed performance and error metrics — Update JSON files in the `ev |
| 🟡 | `f3232904b` | 2026-04-19 | Backend | §14 BYOK + LLM Factory | docs(handoff): add exhaustive LLM Factory handoff for Rails team — Task #540 — Documento técnico em  |
| 🟡 | `6747cf86d` | 2026-04-19 | IA | §15 WSI | Add session ID to tracking for improved auditing and reconciliation — Update lia-agent-system/app/do |
| 🟡 | `bf60a5df7` | 2026-04-19 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | fix eval: remove wrong CAST uuid, expand short job_id filter, wizard company_id rule |
| 🟡 | `a805f1096` | 2026-04-19 | Cross IA↔Back | §15 WSI | task #532 (G23-04): tracking opcional de tokens da Camada 2 WSI — - safe_invoke (app/domains/ai/serv |
| 🟡 | `5e7eb3503` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Task start baseline checkpoint for code review |
| 🟢 | `d0308bdd7` | 2026-04-19 | Frontend (UI) | §18 Senioridade + Job Migration | Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada) — ## What |
| 🟡 | `fd1f1bc44` | 2026-04-19 | Cross IA↔Back | §16 LIA Persona | revert(eval): restore communication.yaml and interaction_patterns.py — Reverted both files to pre-da |
| 🔴 | `7de66b24a` | 2026-04-19 | Cross Back↔Front | §18 Senioridade + Job Migration | Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada) — ## What |
| 🟢 | `4acd3f415` | 2026-04-19 | Frontend (UI) | Kanban (vagas) | Add degraded analysis mode indicator to job kanban views — Adds a warning indicator and tooltip to K |
| 🔴 | `ad92fde29` | 2026-04-19 | Cross IA↔Front | §15 WSI | Task #530 — Kanban: indicador visual de modo degradado no score WSI — ## What |
| 🟡 | `e4e06c10d` | 2026-04-19 | Backend | §16 LIA Persona | Automate the LIA persona diagnostic (Task #527) — Turns the manual 120-probe persona diagnostic into |
| 🔴 | `505c52265` | 2026-04-19 | Cross Back↔Front | Triagem (módulo) | Update modal to display information consistently across all views — Update the TriagemDetailsModal c |
| 🟢 | `a2dbabff3` | 2026-04-19 | Frontend (UI) | Triagem (módulo) | Task #529 — UI Modal Triagem: banner degraded + breakdown granular — Auditoria pré-produção rev. 23  |
| 🟢 | `20f46f00b` | 2026-04-19 | Empty/merge | Triagem (módulo) | Task #529 — UI Modal Triagem: banner degraded + breakdown granular — Auditoria pré-produção rev. 23  |
| 🟡 | `da2ca4737` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): salary benchmark in analytics + offer ID rule + negation cancel pattern + eval timeout 60 |
| 🟡 | `9d686fed0` | 2026-04-19 | Backend | Mockup Sandbox (artefato gerado) | Add new component and update evaluation results for job creation — Updates mockup components and add |
| 🟡 | `5a7205e44` | 2026-04-19 | Backend | §16 LIA Persona | Diagnóstico de persona da LIA: roteiro manual + harness Playwright — - Consolidado o roteiro manual  |
| 🟡 | `fbbb6ea9b` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `9cca4e782` | 2026-04-19 | IA | §18 Senioridade + Job Migration | fix(quality): move regex constants and ActionResult/_fetch_market_range to module level — - executor |
| 🟢 | `d502e54bf` | 2026-04-19 | Frontend (UI) | Triagem (módulo) | Add transparency about semantic analysis unavailability and improve score breakdown — Implement a fa |
| 🟡 | `869e8feab` | 2026-04-19 | Backend | §15 WSI | Remove redundant database schema modification from application code — Remove the `ALTER TABLE` state |
| 🟡 | `7b57d9156` | 2026-04-19 | Cross IA↔Back | §15 WSI | Add transparency data to response analyses and update evaluation results — Adds a new SQL migration  |
| 🟡 | `eb04ba77d` | 2026-04-19 | Cross IA↔Back | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `c69023c9f` | 2026-04-19 | IA | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `6dd966b07` | 2026-04-19 | IA | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `621a500e5` | 2026-04-19 | Backend | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `5b264bcfe` | 2026-04-19 | Backend | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `33832831b` | 2026-04-19 | Backend | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🔴 | `2e4b903c4` | 2026-04-19 | Cross IA↔Front | §15 WSI | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev.  |
| 🟡 | `e054c2258` | 2026-04-19 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `ce89df880` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results for job management and wizard functionalities — Add new entries to evaluat |
| 🟡 | `24a16fd56` | 2026-04-19 | Backend | §17 Eval Framework | fix(eval): add Portuguese-aware criteria matching for WZ-002/003 agile/data/location checks |
| 🟡 | `a760fe110` | 2026-04-19 | Cross IA↔Back | §2 Orchestrator Migration | Improve job description generation and entity extraction — Update job description templating to dyna |
| 🟡 | `574a61e83` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | Update job search and salary suggestions with new parameters — Modify entity extraction for job titl |
| 🔴 | `aee9ab45f` | 2026-04-19 | Cross IA↔Front | §17 Eval Framework | fix(eval): add suggest_salary/generate_jd_direct to _JOB_ACTIONS + fix regex patterns — - Add sugges |
| 🟡 | `acaffae60` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Add new test case for salary suggestion functionality — Add a new evaluation result to `eval_results |
| 🟡 | `3b53ca02e` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): KB-006 UUID filter, WZ-002/003 JD+salary Phase1, MT-002/003 bypass — - Remove global UUID |
| 🟡 | `d2a8954d9` | 2026-04-19 | Cross IA↔Back | scope: handlers | fix(handlers): strip non-UUID entity_id from context before handler dispatch — Handlers like _analyz |
| 🟡 | `44e381ce5` | 2026-04-19 | IA | §16 LIA Persona | fix(identity): Phase 1 intercept for identity questions — LIA never calls Gemini for quem e voce — A |
| 🟡 | `0ad291737` | 2026-04-19 | IA | §16 LIA Persona | Update orchestrator to skip LLM interpretation for identity responses — Modify the MainOrchestrator  |
| 🟡 | `7ef0bfbe8` | 2026-04-19 | IA | §2 Orchestrator Migration | Improve data handling and prompt accuracy for CV screening — Add thread-safety to the LRU cache and  |
| 🟡 | `89c427955` | 2026-04-19 | IA | §16 LIA Persona | Update system to better identify when users ask about the AI's identity — Improve regex patterns for |
| 🟡 | `0f00240b5` | 2026-04-19 | IA | §15 WSI | Update system instructions for evaluating candidate responses — Adjust prompt configurations in `int |
| 🟡 | `eb0bf0e77` | 2026-04-19 | Backend | Artefatos / Eval logs (sem código) | Update job management tool evaluation results and report findings — Adds evaluation results for job  |
| 🟡 | `a41b000bd` | 2026-04-19 | Cross IA↔Back | §17 Eval Framework | fix(eval): KB-005 UUID guard + WZ-002/003 keywords + MT-002 job_title extraction — KB-005: executor. |
| 🟡 | `881aef9d0` | 2026-04-19 | Cross IA↔Back | §16 LIA Persona | fix(persona): LIA identity override — prevent Gemini from leaking model identity — - Prepend REGRA Z |
| 🔴 | `75334b40f` | 2026-04-18 | Cross IA↔Front | §18 Senioridade + Job Migration | Add caching for job extraction and update job seniority fields — Implement an in-memory cache for La |
| 🟢 | `3ec61f4f6` | 2026-04-18 | Frontend (UI) | §18 Senioridade + Job Migration | Clarify seniority and level precedence for job postings — Add inline comments to `SCMSectionContent. |
| 🟡 | `9f40972e4` | 2026-04-18 | Backend | §17 Eval Framework | Add detailed evaluation report for LLM extraction layer — Update the LLM extraction layer evaluation |
| 🟡 | `4af2b303d` | 2026-04-18 | Cross IA↔Back | §15 WSI | Add advanced semantic analysis and scoring for candidate responses — This commit introduces the Laye |
| 🟡 | `a383445f3` | 2026-04-18 | Cross IA↔Back | §17 Eval Framework | fix(eval): list_jobs routing, duplica keyword, KB-005 time-per-stage, executor candidate_name — - ca |
| 🟡 | `85b824fbd` | 2026-04-18 | IA | §2 Orchestrator Migration | Pass through the candidate name for handler API name-lookup — Update `ActionExecutorService` to pass |
| 🟡 | `e762705ef` | 2026-04-18 | IA | §15 WSI | Add layer to extract semantic signals from candidate responses — Implement a new LLM-based layer for |
| 🔴 | `f947f9a21` | 2026-04-18 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Update fairness scoring and remove legacy code — Adjusts the fairness score range from 1-5 to 1-10 i |
| 🔴 | `92bb7013f` | 2026-04-18 | Cross IA↔Front | §15 WSI | Update scoring logic and improve user interface for assessments — Refactor WSI scoring calculations, |
| 🟡 | `d53d0af64` | 2026-04-18 | Backend | scope: admin | fix(admin): include explicit UUID in company_profiles creation |
| 🟡 | `b90e8e2cb` | 2026-04-18 | Backend | scope: admin | fix(admin): auto-create company_profiles on new client creation — Root cause fix for the settings pa |
| 🟡 | `c134dc252` | 2026-04-18 | Cross IA↔Back | Configurações (hub) | fix(settings): company resolve-tenant null profile + LIA settings_config routing — - company.py: res |
| 🟡 | `e42d74dec` | 2026-04-18 | IA | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 |
| 🟡 | `f58b65f80` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 |
| 🟡 | `24ada0f6b` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 |
| 🟡 | `f328031da` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 |
| 🟡 | `47f65a29f` | 2026-04-18 | Cross IA↔Back | §17 Eval Framework | fix(eval): name resolution, implicit job context, wizard tenant scope, short-id fallback — - WZ-002/ |
| 🟡 | `63b132301` | 2026-04-18 | Cross IA↔Back | §15 WSI | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 |
| 🟡 | `1a504eb80` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `17cf7d8ca` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update job management evaluation results with new test cases — Add new test cases to the evaluation  |
| 🔴 | `273e01d54` | 2026-04-18 | Cross IA↔Front | §15 WSI | Improve candidate screening by refining scoring and default handling — Update SQL schema scores to a |
| 🟡 | `97c3767c9` | 2026-04-18 | IA | scope: routing | fix(routing): add English job listing patterns for EX-007 resilience — Adds 4 English-language regex |
| 🟡 | `648b36955` | 2026-04-18 | Backend | §17 Eval Framework | Add new components and update evaluation results for job management — Updates mockup component mappi |
| 🟡 | `934fda6ab` | 2026-04-18 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | audit(canonical): P1 fixes — entity_id precedence + cross-tenant guard in generate_report — - analyt |
| 🟡 | `b3c575ee0` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mockup component registration to include new screens — Update artifacts/mockup-sandbox/src/.g |
| 🟡 | `bbc3a982e` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Task #522: Commit e push na branch replit (sync completo) — Não foi possível executar a tarefa como  |
| 🟡 | `ac98500e9` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `049f195be` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update job management task evaluations with authentication errors — Update `eval_results_20260418_19 |
| 🟡 | `e32e5cfc0` | 2026-04-18 | Backend | §17 Eval Framework | Update evaluation criteria for checking task completion — Remove specific criteria for "does not fai |
| 🟡 | `0cae132ea` | 2026-04-18 | Backend | Auditoria / Audit Rev | audit: fix duplicate field, add technical-exposure rules, canonical entity_id |
| 🟡 | `58291e5cb` | 2026-04-18 | Cross IA↔Back | FastAPI v1 endpoints | Update agent behavior to prevent revealing internal technical details — Remove unnecessary context v |
| 🟢 | `d772302d5` | 2026-04-18 | Frontend (UI) | §15 WSI | Update scoring color logic to use canonical WSI visual scale — Refactors `CandidateScoreBadge.tsx` a |
| 🟡 | `5f6556aae` | 2026-04-18 | Frontend (UI) | §15 WSI | feat(wsi): PR3 frontend escala 0-10 (Task #512, issue #497) — Migra todo o frontend WSI da escala le |
| 🔴 | `d881a64fe` | 2026-04-18 | Cross IA↔Front | §15 WSI | feat(wsi): PR3 frontend escala 0-10 (Task #512, issue #497) — Migra todo o frontend WSI da escala le |
| 🟡 | `38f0ee98a` | 2026-04-18 | IA | §2 Orchestrator Migration | Add a way to store conversation state within the context — Add a new field `conversation_state` to t |
| 🟡 | `6ac807839` | 2026-04-18 | IA | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `fbbff9f49` | 2026-04-18 | Cross IA↔Back | §2 Orchestrator Migration | Add context automatically for company and recruiter IDs — Injects `company_id` and `recruiter_id` in |
| 🟡 | `6b5fdd0c6` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `3543b9212` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `d8db05a12` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `90c05cfea` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `3144cdf8b` | 2026-04-18 | Backend | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `2f38efa38` | 2026-04-18 | Backend | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `a9b7681f6` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `a969aab40` | 2026-04-18 | Backend | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `bdb8543f8` | 2026-04-18 | Backend | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `a26e3c167` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `afe62dd3c` | 2026-04-18 | Cross IA↔Back | §15 WSI | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência d |
| 🟡 | `ecdaccbbf` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results to include detailed job listing tests — Appends detailed results for job l |
| 🟡 | `732cc16e4` | 2026-04-18 | Cross IA↔Back | §2 Orchestrator Migration | Update evaluation to include more candidate information and improve accuracy — Modify intent configu |
| 🟡 | `b4644b269` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups library for improved interface previews — Update generated typescr |
| 🟢 | `a3a10761a` | 2026-04-18 | Frontend (UI) | Configurações (hub) | Fix manual inline editing across Settings (Task #509) — Inline pencil/check editors in Configurações |
| 🟡 | `3b65a4917` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6378873d1` | 2026-04-18 | IA | §2 Orchestrator Migration | Improve candidate matching and extraction for specific intents — Update regex patterns in utils.py f |
| 🟡 | `1e0482dd1` | 2026-04-18 | IA | §15 WSI | Task #510: Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates) — Três fixes crí |
| 🟡 | `9851a5eab` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #510: Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates) — Três fixes crí |
| 🟡 | `4f9ffd248` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `ff2bdc5c3` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Add WSI job listing and active job evaluation results to the system — Update eval_results_20260418_1 |
| 🟡 | `689b90885` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #497 PR2 — Flip atômico escala WSI 0-5 → 0-10 (engine + DB + Pydantic) — T1 wsi_scale.py flipad |
| 🟡 | `91dae132c` | 2026-04-18 | Backend | UX / Mockups | Add new mockups and update evaluation results for job listings — Update mockup component registratio |
| 🟢 | `850011b5d` | 2026-04-18 | Docs | Skills / canonical-fix | Build cascade skills system for LIA platform — Transform .agents/skills/ from a passive collection i |
| 🟡 | `a3099a0a5` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `fe71bb272` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Add new job management evaluation tests — Update the evaluation results JSON file to include new tes |
| 🟡 | `0c98d8529` | 2026-04-18 | IA | Mockup Sandbox (artefato gerado) | Update system to handle job candidate actions and toast notifications — Add a new intent for moving  |
| 🟢 | `1f77b5bfc` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | Task #503: Escurecer pílulas e tipografia dos cards do Kanban — Original: ajuste cirúrgico nos token |
| 🟡 | `7cbf3bf34` | 2026-04-18 | IA | §2 Orchestrator Migration | Add functionality to extract candidate stages from messages — Adds logic to `utils.py` to parse "fro |
| 🟡 | `9b78e02ae` | 2026-04-18 | Cross IA↔Back | §15 WSI | Task #497 PR1: extrair constantes do engine WSI determinístico (zero behavior change) — CONTEXTO |
| 🟡 | `d82a87175` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new chat usability component to the platform — Add the FunilElevenLabs component to the mockup c |
| 🟢 | `916cdb3c4` | 2026-04-18 | Frontend (UI) | Configurações (hub) | Task #500 — Corrigir 'Failed to fetch' na tela de Configurações — Problema: |
| 🟢 | `5817d8a38` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | Task #499 — fix kanban visual regressions (chips, column bg, compare control) — Original task: ajust |
| 🟡 | `1b7419206` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `d2cafcea0` | 2026-04-18 | Cross IA↔Back | Voice / ElevenLabs / STT | Refactor core voice screening logic and improve API error handling — This commit refactors the `proc |
| 🟡 | `0dc4d0a95` | 2026-04-18 | Backend | §9 Security / Tenant guards | Improve error message for invalid authentication tokens — Update the error response for invalid or e |
| 🟡 | `1d996df89` | 2026-04-18 | Cross IA↔Back | §15 WSI | refactor(wsi): extrair transcript_extractor do orchestrator (#496 PR1) — Inicia o split do voice_scr |
| 🟡 | `bfb9d2d95` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Add job management categories to evaluation results — Update lia-agent-system/eval/eval_results_2026 |
| 🔴 | `e867c1d24` | 2026-04-18 | Cross IA↔Front | §15 WSI | feat(wsi): split tech/behav 100% determinístico via category explícita (#498) — Substitui o heurísti |
| 🟡 | `d6a0a572d` | 2026-04-18 | IA | Mockup Sandbox (artefato gerado) | Fix database migration issue and update component mapping — Correct a bug in database migration 089  |
| 🟢 | `0a4170019` | 2026-04-18 | Docs | Skills / canonical-fix | Criar skill canonical-fix (corrigir na origem, sem workaround) — Task #495 — Nova skill em .agents/s |
| 🟡 | `da3a119f8` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `1513a89ef` | 2026-04-18 | Empty/merge | §15 WSI | Phase 2 WSI/Screening remediation — G1 + G2 entregues; G3 promovido a tasks — Trabalho concluído (8  |
| 🔴 | `317680eef` | 2026-04-18 | Cross IA↔Front | §15 WSI | Phase 2 WSI/Screening remediation — G1 + G2 entregues; G3 promovido a tasks — Trabalho concluído (8  |
| 🟡 | `3268d31a2` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mock-up system for better testing — Update generated mock-up component lis |
| 🟢 | `9ca587a51` | 2026-04-18 | Docs | Tasks #494-#570 (WSI/BYOK/Persona fundações) | Task #494: Add Regras de Desenvolvimento (OBRIGATORIAS) section to replit.md — Inserted a new sectio |
| 🔴 | `51a09caec` | 2026-04-18 | Cross IA↔Back | §15 WSI | audit(wsi): Phase 1 remediação — selos rev. 5 + ADR-017 — Phase 1 do plano de remediação WSI aprovad |
| 🟡 | `e8feffd8f` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mockup component registration for chat features — Update the auto-generated mockup component  |
| 🔴 | `5c9c2633a` | 2026-04-18 | Cross IA↔Back | Task #489 | Task #489: Protect remaining /api/v1 routers from URL shadowing bugs — Apply the Task #455 / #458 bl |
| 🟡 | `1ad4af6ab` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update job listing evaluation results with detailed findings — Adds evaluation results for job listi |
| 🟡 | `549c380c2` | 2026-04-18 | Backend | Task #486 | Task #486 — Extend retry-collapse to vacancy & application IDs — Extends the dual-ID idempotency saf |
| 🟡 | `105b1e6f4` | 2026-04-18 | Backend | Policy / Job Creation | Task #476: Generalised structural test for the ID Boundary Policy — Original task |
| 🟡 | `664295002` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `f552d10bd` | 2026-04-18 | Testes | Task #464 | Task #464: Guard against re-introducing actor_user_id token in reasoning — Background: |
| 🟡 | `3f1cb2656` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new components for different reporting and funnel views — Update mockup-components.ts to include |
| 🟡 | `46b7671ac` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update component import for ElevenLabs funnel feature — Modify the mock-up component import for the  |
| 🟡 | `ef2f1a525` | 2026-04-18 | Backend | Task #458 | Task #458: Extend route-shadowing blindagem to 4 more /api/v1 domains — Apply the same protection ad |
| 🟡 | `2b91567bc` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new component for ElevenLabs funnel visualization — Add a new dynamic import for the FunilEleven |
| 🟡 | `2a9b965cf` | 2026-04-18 | Backend | Task #484 | Task #484 — Wire job/application fork_uuid resolvers into RailsAdapter CRUD — Task #479 added `_reso |
| 🟡 | `64828fec6` | 2026-04-18 | Frontend (UI) | Task #485 | Task #485: Convert remaining conditional status pills to semantic Chip variants — Continued the migr |
| 🟡 | `aa240afaf` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for mockups and toasts — Replace imports for "FunilElevenLabs" with "Sonner |
| 🟡 | `45f4f1542` | 2026-04-18 | Backend | Task #478 | Task #478: Wire async dual-ID idempotency safeguard into write endpoints — Wires `ContextManager.gen |
| 🟡 | `ea408d22f` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `e63c8e8a4` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mock component list to include new and removed items — Reorder entries in `artifacts/mockup-s |
| 🟡 | `459b90358` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for improved user interface testing — Update the generated mockup components file to |
| 🟡 | `fe2579ae2` | 2026-04-18 | Backend | Task #479 | Task #479 — Add fork_uuid resolvers for jobs and applications — The idempotency canonicalization lay |
| 🔴 | `f154578d4` | 2026-04-18 | Frontend (UI) | Task #480 | Switch status pills to semantic Chip variants — Task #480: tidy up the few status pills that still s |
| 🟡 | `14f477e80` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `a0543748d` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results for job management scenarios — Adds new test cases to `eval_results_202604 |
| 🟡 | `33260e320` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mock component registration for weekly digest — Update the generated mock component registry  |
| 🟢 | `780e40242` | 2026-04-18 | Frontend (UI) | §7 WorkflowRail UX | Redesign WorkflowRail as floating pill above chat input (Task #483) — Replaces the full-width black  |
| 🟡 | `1649572a2` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `1b4bd3bd0` | 2026-04-18 | IA | UX / Mockups | Update analytics to use company IDs and add new mockup components — Modify SQL queries in analytics_ |
| 🟡 | `4053f9331` | 2026-04-18 | Backend | Task #472 | Task #472: Collapse dual-ID retries onto the same idempotency key — Original task: ADR 003 flagged t |
| 🟡 | `92c4c225c` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `6652b768c` | 2026-04-18 | Frontend (UI) | Task #466 | Standardize remaining ad-hoc Badge pills onto canonical Chip (Task #466) — Follow-up to Task #461. M |
| 🟡 | `13744d288` | 2026-04-18 | Backend | Task #470 | Task #470: Generalize Task #455 routing fix to all dual-ID entities — Block the same `{*_id}: str` s |
| 🟢 | `7dd82c72b` | 2026-04-18 | Docs | Policy / Job Creation | docs: add ID Boundary Policy for LIA × Rails — Task #471 — Document the LIA × Rails ID rules in one  |
| 🟡 | `eac05e8e3` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Update job listing test results with new data and performance metrics — Adds detailed results for jo |
| 🟢 | `86a6f92f2` | 2026-04-18 | Frontend (UI) | Task #467 | Add visual regression coverage for the canonical Chip component — Task #467 |
| 🟢 | `b95fc0603` | 2026-04-18 | Docs | scope: adr | docs(adr): add ADR 003 — LIA × Rails ID strategy (Task #468) — Discovery + decision record for the d |
| 🟡 | `206945048` | 2026-04-18 | Frontend (UI) | scope: ui | chore(ui): consolidate legacy badges onto canonical Chip; remove status-badge — Task #461 — finalize |
| 🟡 | `a5bf880ed` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `369af733e` | 2026-04-18 | IA | §2 Orchestrator Migration | Improve job search by allowing lookup via ID or short ID — Update the job health check to support jo |
| 🟢 | `cdba0850d` | 2026-04-18 | Testes | Task #439 | Task #439: Add tests pinning real-time candidate_count in lifecycle-overview — Adds tests/api/test_l |
| 🟡 | `eb55beb1c` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `f70b1691c` | 2026-04-18 | Backend | Task #446 | Task #446: Speed up ATS job re-syncs for companies with many imported jobs — Problem |
| 🟡 | `56b0dcd4e` | 2026-04-18 | Backend | Task #419 | Task #419 — backfill audit_logs.actor_user_id for historical rows — Migration 084 promoted actor_use |
| 🟡 | `5221b2d65` | 2026-04-18 | Backend | Task #459 | Move orphan POST /{vacancy_id}/close into /job-vacancies prefix (Task #459) — Original task |
| 🟢 | `48134edf6` | 2026-04-18 | Frontend (UI) | i18n / Translation | Translate readiness blocker chips on the readiness hub page — Original task #456: ReadinessHubPage k |
| 🟢 | `e81367e4b` | 2026-04-18 | Frontend (UI) | Task #457 | Make jobs table column headers actually sort the list (task #457) — Previously only the Prontidão co |
| 🟢 | `e6868bf2d` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | Padroniza pílulas do cartão de candidato com KanbanChip canônico — Task #460: migrar `KanbanCardStat |
| 🟢 | `8cd2e10cf` | 2026-04-18 | Frontend (UI) | i18n / Translation | Translate readiness stages and blockers to English — Task #451: Stage badge labels and blocker chips |
| 🟡 | `aac939f64` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new toast notification components for mockups — Add SonnerToasts.tsx and TemplateSuggestionToast |
| 🟡 | `ae1c3bb59` | 2026-04-18 | Backend | Task #455 | Fix 404 on Visão do Pipeline "Vagas" tab — canonical routing fix (Task #455) — The aba "Vagas" of Vi |
| 🟡 | `4d38f7660` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `31bf8321c` | 2026-04-18 | Frontend (UI) | Task #452 | Sort jobs list by readiness stage (Prontidão column) — Task #452: Make the Prontidão column header i |
| 🟡 | `0cc70815c` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest mockups to the component map — Update `mockup-components.ts` to include new mockup |
| 🟡 | `75a3326e1` | 2026-04-18 | Rails (ats-api) | Triagem (módulo) | Estender o seed de triagem para mais vagas/candidatos (Task #427) — Adiciona duas triagens WSI compl |
| 🟡 | `5906bbb55` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Remove stray evaluation results file from agent system — Remove the `eval_results_20260418_092305.js |
| 🔴 | `50434ab66` | 2026-04-18 | Cross Back↔Front | Kanban (vagas) | Task #454 — KanbanColumnShell + chip variant tokens — Closes the kanban standardization series (#443 |
| 🟢 | `176ad9006` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | fix(jobs-kanban): restore horizontal scroll on Vagas Kanban (Task #453) — Original task: rightmost c |
| 🟡 | `9df37e306` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `d06e4fe88` | 2026-04-18 | Cross Back↔Front | scope: jobs | feat(jobs): add Prontidão (readiness) column to Vagas list (Task #448) — - Backend: extend `list_job |
| 🟡 | `e3f01c680` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `65b3c82c8` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports for weekly digest features — Reorders mock component imports in `mocku |
| 🔴 | `111c3403e` | 2026-04-18 | Cross Back↔Front | Task #429 | Task #429: Job Readiness Hub MVP — Implements an onboarding pipeline that guides recruiters through  |
| 🟡 | `5f3d3fc4e` | 2026-04-18 | Backend | Mockup Sandbox (artefato gerado) | Fix database migration to correctly handle JSON data types — Corrected `lia-agent-system/alembic/ver |
| 🔴 | `bb15510bb` | 2026-04-18 | Cross Back↔Front | Task #436 | Fix candidate profile analysis 401/500 errors (Task #436) — Resolves two root causes: |
| 🟡 | `3161accc5` | 2026-04-18 | Backend | Task #442 | Task #442: Persist ATS-pulled jobs into job_vacancies — Persist jobs pulled from external ATSs (Gupy |
| 🟡 | `80e1e37fd` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `65a8524fb` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | feat(kanban): padronizar card do kanban — vagas e candidatos (#445) — Cria primitiva canônica `Kanba |
| 🟢 | `a42e04e69` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | Task #444: padronizar header de coluna do kanban (vagas + candidatos) — Original task: criar um head |
| 🟢 | `9d956725f` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | Update job view options with specific labels — Refactor JobsHeader component to use distinct labels  |
| 🔴 | `23b07df5f` | 2026-04-18 | Cross Back↔Front | scope: ui | feat(ui): toolbar canônica para vagas e candidatos (#443) — Cria primitives compartilhadas e tokens  |
| 🟢 | `dc1c798db` | 2026-04-18 | Frontend (UI) | scope: ui | feat(ui): toolbar canônica para vagas e candidatos (#443) — Cria primitives compartilhadas para padr |
| 🟡 | `01ca35033` | 2026-04-18 | Cross IA↔Back | Mockup Sandbox (artefato gerado) | Task start baseline checkpoint for code review |
| 🔴 | `911e6a651` | 2026-04-18 | Cross Back↔Front | Task #435 | Task #435 — dedicated source_system column for ATS-imported job vacancies — Why |
| 🟡 | `6440b7208` | 2026-04-18 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `b813ace0a` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mock component mappings for toasts and reports — Update artifacts/mockup-sandbox/src/.generat |
| 🟢 | `605c0cbbf` | 2026-04-18 | Testes | §15 WSI | Task #412: regression test for FairnessGuard on WSI generate-questions — Added `lia-agent-system/tes |
| 🟡 | `e988e8ae6` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for decision bar and toast components — Update mockup-components.ts to include new m |
| 🟡 | `fe479a11b` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Update mock component definitions for new and existing features — Modify artifacts/mockup-sandbox/sr |
| 🟡 | `5e9a354bc` | 2026-04-18 | Backend | Task #424 | Restore lost guidance in the sourcing assistant prompt (Task #424) — When the sourcing system prompt |
| 🟡 | `49947851f` | 2026-04-18 | Cross IA↔Back | Task #417 | Migrate cv_match_tool to canonical authoring surface (Task #417) — Original task: Shrink the tool-au |
| 🟡 | `e762f4c70` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add mockups for new toast notifications and update existing ones — Add new mockups for SonnerToasts  |
| 🟡 | `ed3f57b30` | 2026-04-18 | Rails (ats-api) | Triagem (módulo) | Unify triagem_sessions/triagem_messages ownership (Python is source of truth) — Task #428: the Rails |
| 🟡 | `5aaa46eda` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockup sandbox for testing — Update mockup-components.ts to include new co |
| 🟢 | `07bdedd98` | 2026-04-18 | Testes | Triagem (módulo) | test(triagem): cover audio decoding path in useTriagemMessages — Task #416 — the text optimistic-sen |
| 🟡 | `1f95fea7e` | 2026-04-18 | Outro | Mockup Sandbox (artefato gerado) | Add new components and reorganize existing ones for better organization — Update module map to inclu |
| 🟡 | `5f422dfee` | 2026-04-18 | Backend | Task #434 | Show real candidate counts on Vagas pipeline panel (Task #434) — Problem |
| 🟢 | `e8f2ede85` | 2026-04-18 | Testes | scope: chat | test(chat): cover WS-timeout watchdog fallback in useChatMessages — Task #415 — adds vitest coverage |
| 🔴 | `695fbfd97` | 2026-04-18 | Cross Back↔Front | §17 Eval Framework | Add job creation functionality to the jobs chat interface — Removes unused useRef import from useJob |
| 🔴 | `fbc1187c5` | 2026-04-18 | Cross Back↔Front | §7 WorkflowRail UX | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRai |
| 🟢 | `4a515f5df` | 2026-04-18 | Frontend (UI) | §7 WorkflowRail UX | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRai |
| 🟢 | `9792ab69d` | 2026-04-18 | Frontend (UI) | §7 WorkflowRail UX | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRai |
| 🔴 | `53450e056` | 2026-04-18 | Cross Back↔Front | Task #432 | Task #432: Rich responses no chat com PipelineRailCard — Frontend (plataforma-lia): |
| 🟢 | `a29d0ed20` | 2026-04-18 | Frontend (UI) | Task #432 | Task #432: Rich responses no chat com PipelineRailCard — - New PipelineRailCard (src/components/chat |
| 🟡 | `c87e463d5` | 2026-04-18 | Frontend (UI) | Task #432 | Task #432: Rich responses no chat com PipelineRailCard — - New PipelineRailCard (src/components/chat |
| 🟡 | `350ae64fc` | 2026-04-18 | Backend | Artefatos / Eval logs (sem código) | Remove unrelated evaluation results file from project — Delete the `eval_results_20260418_010408.jso |
| 🟡 | `ae83dca41` | 2026-04-18 | Frontend (UI) | Kanban (vagas) | feat(jobs): toggle Tabela\|Kanban em /vagas (Task #431) — - Generalizou KanbanCard/KanbanColumn para  |
| 🔴 | `e9ec31e52` | 2026-04-18 | Cross Back↔Front | Kanban (vagas) | feat(jobs): toggle Tabela\|Kanban em /vagas (Task #431) — - Generalizou KanbanCard/KanbanColumn para  |
| 🟢 | `e76ca1de8` | 2026-04-18 | Frontend (UI) | Frontend (componentes diversos) | Localize pipeline overview text and update job count display — Update `en.json` and `pt-BR.json` to  |
| 🟢 | `6de2dc8cb` | 2026-04-18 | Frontend (UI) | Task #430 | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a toggle on /visao-do-funil between the |
| 🔴 | `1043a8826` | 2026-04-18 | Cross IA↔Front | Task #430 | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a toggle on /visao-do-funil between the |
| 🔴 | `d6b844269` | 2026-04-18 | Cross Back↔Front | Task #430 | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a 8-stage job lifecycle rail (ATS Impor |
| 🟡 | `c2da08fec` | 2026-04-18 | Backend | Backend Services (BE) | Control when user reopens are counted towards session limits — Modify the token validation to only c |
| 🟡 | `399cdd9d8` | 2026-04-18 | Backend | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): |
| 🟡 | `becc1efac` | 2026-04-18 | Backend | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): |
| 🔴 | `e5b77b78b` | 2026-04-18 | Cross Back↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): |
| 🔴 | `405b68e3b` | 2026-04-18 | Cross IA↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): |
| 🔴 | `2d53bf4db` | 2026-04-18 | Cross Back↔Front | §15 WSI | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): |
| 🔴 | `b2086c0c4` | 2026-04-17 | Cross Back↔Front | Configurações (hub) | Improve screening invitation modal and configuration settings — Updates the screening invitation mod |
| 🟡 | `6e7f7df4a` | 2026-04-17 | Backend | Artefatos / Eval logs (sem código) | Update evaluation results for job management functionalities — Update evaluation result files, showi |
| 🟡 | `9ffa41bee` | 2026-04-17 | Cross IA↔Back | §17 Eval Framework | Improve system responses and entity identification — Update `workflow.py` to use a generic clarifica |
| 🟡 | `159aa9560` | 2026-04-17 | Backend | §17 Eval Framework | Add regular expression support for evaluation runner — Import the 're' module for regular expression |
| 🟡 | `74fecdc0c` | 2026-04-17 | Backend | §17 Eval Framework | Improve Portuguese language support for evaluation criteria checking — Update the `_criterion_met` f |
| 🟡 | `de05fb758` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for mockups — Correctly import components for FunilElevenLabs and SonnerToa |
| 🟡 | `ceea3c722` | 2026-04-17 | Rails (ats-api) | Triagem (módulo) | Task #426: Seed candidato com triagem preenchida pra print — Estendi `ats-api-copia/db/seeds.rb` adi |
| 🔴 | `5e0ec22e0` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425 Pass 5 — close all 4 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system/app |
| 🔴 | `51a2fe664` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425: WSI 4 Canais MVP — pass 3 closes review blockers — Third review pass after a second REJEC |
| 🔴 | `c0cdf0747` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #425: WSI 4 Canais MVP — pass 3 closes review blockers — Third review pass after a second REJEC |
| 🟡 | `fe85a46c6` | 2026-04-17 | Frontend (UI) | §15 WSI | Task #425: WSI 4 Canais MVP — canonical model end-to-end + master cascade + invite filtering — Secon |
| 🔴 | `263aa6200` | 2026-04-17 | Cross IA↔Front | §15 WSI | Task #425 (foundation slice): WSI 4 Canais MVP — canonical model + master toggle + remove silent moc |
| 🟡 | `b0c3126ac` | 2026-04-17 | Cross IA↔Back | §15 WSI | Update documentation and remove outdated WSI assessment guides — Remove four WSI documentation files |
| 🟡 | `d9b4bd83b` | 2026-04-17 | Backend | Job Management (BE) | Add logging to job search functionality — Add debug logging for the number of rows returned by the j |
| 🟡 | `eabdca93c` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include a new funnel elevenlabs module — Update artifacts/mockup-sandbox/s |
| 🟡 | `bb35e704b` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new component for Eleven Labs funnel functionality — Update `mockup-components.ts` to include th |
| 🟢 | `2bb9bcbb6` | 2026-04-17 | Frontend (UI) | Wizard (geral) | Wire FairnessGuard drop payload into the wizard runtime (Task #367) — The backend publishes `fairnes |
| 🟡 | `ebc5d3b18` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `415d6db42` | 2026-04-17 | Cross IA↔Back | Task #366 | Task #366 — promote actor_user_id to a structured audit field — Original task |
| 🟡 | `035e96e10` | 2026-04-17 | Cross IA↔Back | Task #354 | Task #354: Block accidental tool registrations outside canonical entry point — Adds the S7.5 CI/pre- |
| 🟡 | `d9cdd3a34` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `64ee7e57c` | 2026-04-17 | Testes | Task #327 | Task #327: Add integration test pinning chat WebSocket to /api/v1 prefix — Adds tests/integration/te |
| 🟡 | `2a7deda3d` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `3315abfb4` | 2026-04-17 | Testes | Task #248 | Task #248: First unit tests for candidates-list and chat hooks — Locks in the current behaviour of t |
| 🟢 | `22ca72791` | 2026-04-17 | Testes | Task #260 | Task #260 — Add tests for the candidate-profile and screening-config watchdog paths — Added two new  |
| 🟢 | `a48afdd67` | 2026-04-17 | Frontend (UI) | §9 Tenant Isolation / Multi-tenancy | Task #267: Use real company_id in Kanban page core — Original task: useKanbanPageCore.ts was reading |
| 🟢 | `73d06f91c` | 2026-04-17 | Frontend (api/util) | Task #291 | Task #291 — Padronizar busca de candidatos para não esconder o motivo real do erro — A rota proxy /a |
| 🟡 | `becd9b863` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `9da48593e` | 2026-04-17 | Testes | scope: lia-agent-system | test(lia-agent-system): cover conversational LIA search tool with integration test (Task #397) — Ori |
| 🟡 | `bade39415` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `26a55db93` | 2026-04-17 | Testes | Task #379 | Task #379: Cover WS-closing fallback for chat with hook + e2e tests — Original task: ensure messages |
| 🟡 | `4102256ea` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update components to reflect latest mockups and features — Update the generated mockup components fi |
| 🟢 | `4447190b6` | 2026-04-17 | Testes | Observability / Sentry / OTLP | Fix broken token-budget and drift unit tests after observability move — Task #362: Several tests sti |
| 🟡 | `60d3c6e2f` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `003bcec6d` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | Notify recruiter in real time when sourcing is fairness-blocked — Task #360: recruiters previously o |
| 🟡 | `7498742e1` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components for UI development and testing — Modify artifacts/mockup-sandbox/src/.generat |
| 🟡 | `dc3e16e5c` | 2026-04-17 | Cross IA↔Back | Task #353 | Task #353: Move per-tenant LLM provider config out of YAML and into the database — ADR-016 decided p |
| 🟡 | `13d67609b` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `1cc1edce0` | 2026-04-17 | Backend | Task #338 | Fix broken pipeline prompt parity tests (Task #338) — The five tests in TestPipelinePromptParity wer |
| 🟢 | `f7d27ce7f` | 2026-04-17 | Empty/merge | UX / Mockups | Add Eleven Labs funnel mockup to the component registry — Update mockup-components.ts to include the |
| 🟡 | `d378afb1e` | 2026-04-17 | Backend | scope: candidates | test(candidates): regression tests for tenant isolation + sanitized errors (#290) — Task #290 asked  |
| 🟡 | `05d37b778` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `4f1f35602` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for various components and update existing ones — Add new mockup component definitio |
| 🟢 | `5f3e8cd88` | 2026-04-17 | Frontend (api/util) | Configurações (hub) | Apply loading watchdog to company-settings (Minha Empresa) hub — Task #259: Protect the company-sett |
| 🟢 | `9730fea48` | 2026-04-17 | Testes | Observability / Sentry / OTLP | Task #256: Add automated test for the jobs-page fallback banner — Original task: Cover the amber "ex |
| 🟡 | `ee3824530` | 2026-04-17 | Backend | Artefatos / Eval logs (sem código) | Add new evaluation results for job management scenarios |
| 🟡 | `2e874a8a0` | 2026-04-17 | Backend | Artefatos / Eval logs (sem código) | Add new evaluation results for job management scenarios — Update JSON files in `lia-agent-system/eva |
| 🟢 | `91737f9c7` | 2026-04-17 | Testes | Task #404 | Task #404: test no-contact filter banner on Talent Funnel — Added a sibling test file |
| 🟡 | `6c11e4361` | 2026-04-17 | Backend | Mockup Sandbox (artefato gerado) | Add new toast components and improve tenant ID resolution in tool handler — Adds new toast mockups t |
| 🟢 | `301829ca2` | 2026-04-17 | Docs | scope: audits | docs(audits): resolve merge conflict markers in §5 Stage table — Task #385: Section 5 ("Reconciliaçã |
| 🟡 | `9a812858e` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `f9ec30e17` | 2026-04-17 | Frontend (api/util) | Task #384 | Surface dev-auto-login failures (Task #384) — Audit finding F3 from docs/audits/unified-chat-no-resp |
| 🟡 | `8575726b3` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component list to include ElevenLabs funnel — Re-added the ElevenLabs funnel component to the |
| 🟡 | `1d7c8cb86` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for decision bar and update existing ones — Add new mockups for decision bar compone |
| 🟡 | `a6639d0c8` | 2026-04-17 | Backend | §15 WSI | Task #247: Restore FairnessGuard + audit log on WSI question generation — The canonical /api/v1/wsi/ |
| 🟡 | `4ee9af91e` | 2026-04-17 | Backend | Task #226 | Task #226: Detect forbidden imports inside generated code strings — Extends lia-agent-system/scripts |
| 🟢 | `7db2a5c0c` | 2026-04-17 | Frontend (UI) | Acessibilidade (a11y) | Add keyboard accessibility to the chat header drag handle — Update UnifiedChatHeader.tsx to include  |
| 🟢 | `3e4367a88` | 2026-04-17 | Frontend (UI) | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da L |
| 🟢 | `dd098c857` | 2026-04-17 | Frontend (UI) | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da L |
| 🔴 | `1231c6b1f` | 2026-04-17 | Cross Back↔Front | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da L |
| 🔴 | `7057f692e` | 2026-04-17 | Cross Back↔Front | scope: chat | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da L |
| 🟡 | `484b467f7` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `aa81935c9` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for decision bar and WSI report components — Update mockup-components.ts to include  |
| 🟡 | `4dbd62251` | 2026-04-17 | Backend | scope: eval | feat(eval): LIA enterprise eval suite — 72 cases, runner, LLM judge, HTML report — 72 test cases acr |
| 🟡 | `521b6b404` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component registry to include new reporting and decision bar mockups — Reorganize the `mockup |
| 🔴 | `1dc1109ba` | 2026-04-17 | Cross Back↔Front | Task #403 | Task #403: Persist discarded candidates per search execution — Problem |
| 🔴 | `af086a2d9` | 2026-04-17 | Cross Back↔Front | Task #402 | Task #402: Re-enrich discarded candidates from FilteredNoContactModal — Backend |
| 🟡 | `140ff37ae` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `3f7fc6d92` | 2026-04-17 | Backend | §9 Tenant Isolation / Multi-tenancy | fix(chat): A1-B normalize company_id in send_message and stream_message — chat.py was using current_ |
| 🔴 | `b96975212` | 2026-04-17 | Cross Back↔Front | Task #400 | Task #400: surface candidates discarded during contact enrichment — Backend |
| 🟡 | `62f47387a` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest mockups to the component registry — Update mockup-components.ts to include new com |
| 🟢 | `ec9797157` | 2026-04-17 | Testes | §13 PARTE D — Foundation/Apify/Manifest | Task #401: Add tests covering the Apify enrichment count banner — Added a new component test file |
| 🟡 | `29675834d` | 2026-04-17 | Frontend (UI) | §13 PARTE D — Foundation/Apify/Manifest | Task #399: Mostrar candidatos enriquecidos via Apify no Funil de Talentos — O backend já vinha devol |
| 🟡 | `d96da8949` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `f0df08ffc` | 2026-04-17 | Cross IA↔Back | §13 PARTE D — Proatividade | fix(lia): Wave A+B — tenant alias, scope routing, proactive tools — A1: tenant.py — added '37' and s |
| 🟡 | `20083b682` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add mockups for new triagem flow screens to the sandbox — Add new mockups for ChatScreen, Completion |
| 🔴 | `2026c1029` | 2026-04-17 | Cross Back↔Front | Task #394 | Task #394: Surface candidates filtered out by missing contact — `enrich_and_filter_candidates` was s |
| 🟡 | `313d0141a` | 2026-04-17 | Backend | Backend (core) | Update demo company aliases to include staging and Replit IDs — Add staging and Replit-specific IDs  |
| 🟡 | `c23bb0620` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component mappings for mockups to reflect current structure — Reorder and add entries in `moc |
| 🟡 | `31e3f3bdd` | 2026-04-17 | Backend | Task #396 | Task #396: Robust LinkedIn URL dedup in contact enrichment — Problem |
| 🟡 | `930aebd87` | 2026-04-17 | Backend | Task #395 | Task #395: alinhar busca da LIA conversacional com a busca da tela — Refatora `_wrap_search_candidat |
| 🟡 | `1f071d7a2` | 2026-04-17 | Outro | §15 WSI | Generate comprehensive audit report on WSI screening process — Create a detailed report in .local/au |
| 🟡 | `88b4efa89` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new component for simulating ElevenLabs funnel functionality — Update mockup components file to  |
| 🟢 | `404f996a4` | 2026-04-17 | Docs | §6 Chat Unificado / Funil | docs(funil-talentos): atualiza talent-funnel-search-flow.md — Correções de fidelidade ao código (apo |
| 🟡 | `7a7bfaa05` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `9c7385973` | 2026-04-17 | Cross IA↔Front | scope: lia | fix(lia): Fix5+6 agentic tool auth + main chat 422 |
| 🟡 | `559a40da3` | 2026-04-17 | IA | scope: lia | fix(lia): 4 surgical fixes for LIA chat bugs — - navigation_intent.py: Add missing 'Indicadores' pag |
| 🟡 | `2673b6bf6` | 2026-04-17 | IA | §2 Orchestrator Migration | Add ability to navigate between pages based on user intent — Add a new function to inject UI actions |
| 🟡 | `58b50fc58` | 2026-04-17 | Cross IA↔Back | §2 Orchestrator Migration | Add navigation capabilities and context to agent responses — Introduces navigation intent detection  |
| 🟡 | `101169222` | 2026-04-17 | Outro | Tests (BE unit/integration) | Add tests for core platform functionalities and interactions — Adds a new Python script to `tests/li |
| 🟡 | `a0fc298b5` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include a new funnel feature — Modify the module map to correctly import |
| 🟢 | `4cc6bab30` | 2026-04-17 | Testes | Task #391 | Add automated tests for PT/EN language switcher (task #391) — Locks in the language-switching behavi |
| 🟡 | `bf16a8bbd` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `55ad1327c` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component map to include ElevenLabs funnel — Regenerates the mockup component map in artifact |
| 🟢 | `4deeb4980` | 2026-04-17 | Frontend (api/util) | i18n / Translation | Fix PT/EN locale switch being overridden by middleware — Task #380: The Next.js middleware in `plata |
| 🟢 | `6985e5bef` | 2026-04-17 | Frontend (UI) | Tests (FE e2e) | Improve backend proxy to handle varied response formats — Update backend proxy and related scripts t |
| 🟡 | `4f4772484` | 2026-04-17 | Backend | Task #358 | Block discriminatory job descriptions before they hit the database (Task #358) — Wired FairnessGuard |
| 🟡 | `e1bd75ba8` | 2026-04-17 | Frontend (api/util) | Task #383 | Task #383: Fall back to REST when chat WS silently drops messages (F2) — Original task |
| 🟡 | `e89240c75` | 2026-04-17 | IA | Task #386 | Task #386 — Hard-block English equivalents of "good looking" / "young and dynamic" — Background: |
| 🟡 | `9265d0680` | 2026-04-17 | IA | Compliance / LGPD / EU AI Act | Add end-to-end integration test for the fairness-block audit trail — Task #365: Cover the regulator- |
| 🟡 | `8cee1ad91` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new components for the triagem flow and update existing ones — Add and remove mock component def |
| 🟢 | `cc34d1757` | 2026-04-17 | Frontend (UI) | Task #356 | Remove duplicated retry helpers in lib/backend-ready and chat hooks (task #356) — Migrated remaining |
| 🟡 | `5cf82a0ae` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mockup component imports to reflect recent file changes — Reorder imports in `mockup-componen |
| 🟡 | `7b61471cd` | 2026-04-17 | IA | Compliance / LGPD / EU AI Act | Promote canonical biased phrases to hard-block in FairnessGuard (Task #364) — What changed |
| 🟡 | `d4bddb5f6` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for ElevenLabs funnel feature — Update `mockup-components.ts` to correctly  |
| 🔴 | `8d295abac` | 2026-04-17 | Frontend (UI) | Task #375 | Task #375: Strip inline LIA chat state from Candidates pages — Per reviewer rejection, removed the r |
| 🟢 | `6e6dc705f` | 2026-04-17 | Docs | §18 Senioridade + Job Migration | docs(audits): apply F5 inheritance rule to top-level ReActAgent rows in scorecard (task #371) — Orig |
| 🟡 | `722c8eac7` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock component configurations for UI previews — Update module map in mockup-components.ts to  |
| 🟢 | `f8e824d33` | 2026-04-17 | Frontend (api/util) | scope: chat | fix(chat): show error bubble when LIA REST proxy returns no content — Task #377 — fixes the F1 findi |
| 🟡 | `c455515b5` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for toasts and weekly digest components — Update generated mockup components to incl |
| 🟡 | `45dd15b7b` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component registration for toasts and pending tabs — Update mockup-components.ts to correctly |
| 🟢 | `e92d351de` | 2026-04-17 | Docs | Observability / Sentry / OTLP | docs: document canonical observability layer (Task #363) — Task #343 collapsed 11 modules (tracing,  |
| 🟡 | `a0059a9dc` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock component list to include weekly digest items — Re-adds weekly digest mock components to |
| 🟢 | `b583afd74` | 2026-04-17 | Docs | Observability / Sentry / OTLP | docs(observability): align architecture docs with new canonical location (Tarefa #372) — Closes the  |
| 🟡 | `3b635d5c5` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new components for the weekly digest feature — Update mockup components to include new weekly di |
| 🟢 | `51800a04e` | 2026-04-17 | Testes | Task #298 | audit(#374): root-cause UnifiedChat "LIA não responde" silent drop — Audit-only deliverable, no beha |
| 🟡 | `6d66f03eb` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `3f057c90a` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for mockups to reflect current file structure — Update artifacts/mockup-san |
| 🟢 | `6ebff401e` | 2026-04-17 | Docs | scope: audits | docs(audits): reconcile AUDIT_STATUS_REPORT_2026-04-FINAL with current code — Task #370 — documentat |
| 🟢 | `327102c3f` | 2026-04-17 | Docs | Compliance / LGPD / EU AI Act | Recompute agent compliance scorecard with F5 sub-agent inheritance rule (task #369) — Original task: |
| 🟡 | `dcb90de76` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new toast notifications — Add and remove entries in the generated  |
| 🟡 | `935f0144c` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Re-enable CI workflows (task #368) — Renamed all four GitHub Actions workflow files from *.yml.disab |
| 🟡 | `fa262e352` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new components for mockups and adjust existing ones — Update mockup component registration by ad |
| 🟡 | `4713cd342` | 2026-04-17 | Cross IA↔Back | Task #352 | task #352 — close out AUDIT FINAL 2026-04 finals (F4, F5, F8, F10, F11, F12) — Closes the remaining  |
| 🟡 | `05056bec7` | 2026-04-17 | Backend | §9 Tenant Isolation / Multi-tenancy | Task #346: add Candidate.company_id with backfill migration — Model & migration |
| 🟡 | `e9046636b` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new toast notifications for improved user feedback — Add new toast notification components to th |
| 🟢 | `098941b8f` | 2026-04-17 | Testes | Tests (BE unit/integration) | Add integration test for sourcing pipeline against discriminatory JD — Original task (#342): write a |
| 🟡 | `775d73f08` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include toast notifications and pending reports — Modify the generated m |
| 🔴 | `d9c75df91` | 2026-04-17 | Cross Back↔Front | §15 WSI | Task #332: Surface FairnessGuard drops in WSI wizard + audit trail — Recruiters previously saw the W |
| 🟢 | `4781a4ab6` | 2026-04-17 | Testes | Compliance / LGPD / EU AI Act | test(cv_screening): add fairness/audit unit tests for 5 scoring services — Task #307 — EU AI Act hig |
| 🟡 | `7d3a5ee7e` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component map to include decision bar mockups — Add new mockups for the decision bar componen |
| 🟡 | `19dd5a256` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include new mockups for testing — Updates the `mockup-components.ts` fil |
| 🟡 | `0a6a412c8` | 2026-04-17 | Cross IA↔Back | Policy / Job Creation | Task #337: Forward actor_user_id to policy audit log — The policy chat orchestrator did not forward  |
| 🟢 | `70c1f4e48` | 2026-04-17 | Testes | Compliance / LGPD / EU AI Act | Fix pre-existing fairness/bias audit test failures (task #339) — Fixed 6 failing tests that were unr |
| 🟡 | `909f9ee74` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `0acf9ef35` | 2026-04-17 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Task #341: Surface FairnessGuard sourcing blocks on the recruiter job page — Backend |
| 🟡 | `e6bbc82b3` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `0bcf56528` | 2026-04-17 | Cross IA↔Back | Observability / Sentry / OTLP | Task #343: Collapse legacy observability paths into app.shared.observability — Stage 6 had not actua |
| 🟡 | `66fa3b7e0` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest mockups to the generated components list — Update `mockup-components.ts` to includ |
| 🟡 | `117f4d1ec` | 2026-04-17 | Backend | Task #340 | Task #340: Migrate callers off deprecated bias_audit_service shim — Migrated all imports from the de |
| 🟢 | `b1c76a3c4` | 2026-04-17 | Testes | Task #344 | Fix broken token-budget & drift-alert test patch paths — Task #344: Nine tests across three files we |
| 🟢 | `e6a60db8d` | 2026-04-17 | Testes | Wizard (geral) | test(job_creation): end-to-end wizard graph audit assertion — Adds tests/integration/test_job_creati |
| 🟡 | `55799fe7a` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | Task #331: Aplicar auth + FairnessGuard + audit em /applications/resubmit — Original task: o endpoin |
| 🟡 | `495fda344` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `2311343f8` | 2026-04-17 | Frontend (api/util) | §15 WSI | Task #305: extend WSI 401 helper to all wsi-api functions — Original ask: bug #303 only normalized ` |
| 🟡 | `129e87542` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include new toast notification components — Update the `mockup-components.ts` file |
| 🟡 | `f1d286d9f` | 2026-04-17 | Frontend (UI) | Observability / Sentry / OTLP | Task #345 — Audit & fix jobs-page resiliency (Failed to fetch + 429 cascade) — Root cause was a chai |
| 🟢 | `b9427ec52` | 2026-04-17 | Docs | ADR-016 | docs(ai): ADR-016 — declare canonical tool registration system (Task #351) — Original task: decide w |
| 🟡 | `44fef6818` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `4ce1412ea` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update generated component map to include new mockups — Add new mockups for decision-bar and wsi-rep |
| 🟡 | `691f8e59f` | 2026-04-17 | Backend | Task #328 | Task #328: Empty legacy @tool decorator allow list — All five grandfathered domain tool files were a |
| 🟡 | `d9aacd3d6` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component module map to include new toast and decision bar components — Reorganizes the mappi |
| 🟡 | `56dc31d9b` | 2026-04-17 | Backend | Task #350 | Task #350 — Retire dead GlobalToolRegistry shim — Original task asked to delete four files (global_t |
| 🟡 | `f1884bc87` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for toast notifications — Reorder mock component imports in mockup-componen |
| 🟡 | `4d210db7b` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Add fairness checks + audit trails to CV screening services (C1–C5) — Closes compliance gaps for LGP |
| 🟡 | `f4e281faf` | 2026-04-17 | Backend | Task #348 | Lock down fine-tuning data export to authenticated company members (Task #348) — Original task: The  |
| 🟡 | `865ef1265` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new toast and funnel features — Removes and re-adds mock component |
| 🟢 | `db4aeeebc` | 2026-04-17 | Docs | Task #347 | Task #347: Final audit report (revised) — strict 5-status taxonomy + crosswalk — Deliverable: docs/a |
| 🟡 | `7fbf96adb` | 2026-04-17 | Backend | §6 Chat Unificado / Funil | fix(funil): higiene final P2 — ws-token, kill-switch deprecation, dedup hooks (Task #298) — Endereça |
| 🔴 | `426701baa` | 2026-04-17 | Cross Back↔Front | §6 Chat Unificado / Funil | fix(funil): higiene final P2 — ws-token, kill-switch deprecation, dedup hooks (Task #298) — Endereça |
| 🟡 | `9cb743499` | 2026-04-17 | Backend | §14 BYOK + LLM Factory | Align AI provider key detection with health check reporting — Refactor `main.py` to use the `_provid |
| 🟡 | `80c09ef0c` | 2026-04-17 | Backend | scope: health | feat(health): structured provider healthcheck + sourcing runbook (Task #297) — Endereça causas raiz  |
| 🟡 | `34e70944a` | 2026-04-17 | Backend | FastAPI v1 endpoints | Improve search functionality by handling fallback errors and restoring response models — Update the  |
| 🟡 | `7bd62fef4` | 2026-04-17 | Backend | Task #296 | Task #296 — 503 estruturado + warning_message em /search/candidates — Original: causa raiz #6 da aud |
| 🟡 | `a65451070` | 2026-04-17 | Backend | §6 Chat Unificado / Funil | Funil P1 — Tenant filter + erros sanitizados em /api/v1/candidates (task #295) — Causa raiz #4 da au |
| 🟡 | `869182118` | 2026-04-17 | Backend | §6 Chat Unificado / Funil | Funil P1 — Tenant filter + erros sanitizados em /api/v1/candidates (task #295) — Causa raiz #4 da au |
| 🟢 | `5cf99eb62` | 2026-04-17 | Frontend (api/util) | §6 Chat Unificado / Funil | Task #294 — Funil P0: proxy /search/candidates canônico                 + endurecimento do helper cr |
| 🟢 | `ee4cb7148` | 2026-04-17 | Frontend (UI) | §6 Chat Unificado / Funil | Task #294 — Funil P0: proxy /search/candidates canônico. — Substitui o hand-roll em |
| 🟢 | `dd8b800ee` | 2026-04-17 | Frontend (UI) | UX / Mockups | Add test identifiers and update component imports for mockups — Add `data-testid` and `data-stage-id |
| 🟢 | `9c1992db7` | 2026-04-17 | Testes | Observability / Sentry / OTLP | Task #325: Canonicalize app/shared/observability/ (Stage 6) — Consolidate 11 observability modules p |
| 🟡 | `72bb74218` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `24f7a9c71` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update the way mockups are loaded and displayed — Reorder mock component imports in `mockup-componen |
| 🟡 | `e59abd0da` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #316 — PolicySetupAgent: raise compliance from 25% → ~80% — Audit finding A2 flagged that Polic |
| 🟡 | `928625cb2` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add and remove toast notification mockups for testing purposes — Add new entries for SonnerToasts.ts |
| 🟡 | `b588de4d2` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include toast notifications and pending reports — Reorders imports in `mockup-comp |
| 🟡 | `fb8f545d1` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | Task #310: Auth, FairnessGuard e audit em applications.apply — Original task: corrigir endpoint POST |
| 🟡 | `3bc3886bf` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #315: Wire enterprise compliance gates into JobCreationGraph — What changed: |
| 🟡 | `e5434e698` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update component registration for toast notifications — Adjust the order of imported modules in `moc |
| 🟡 | `a621c68e1` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | task-312: add FairnessGuard + audit + PII masking to sourcing & feedback — C6 — sourcing_pipeline_se |
| 🟡 | `1f93fb414` | 2026-04-17 | Backend | Task #313 | Migrate 5 legacy @tool files to canonical @tool_handler (Task #313) — Audit finding T2: 5 tool files |
| 🟡 | `36a3f6dfb` | 2026-04-17 | IA | Configurações (hub) | Task #320: Close routing for CompanySettingsReActAgent (W16/W19) — The auditoria gap was that domain |
| 🟡 | `27de7bbb0` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock component configuration for several features — Modify artifacts/mockup-sandbox/src/.gene |
| 🟡 | `25ebf3c0b` | 2026-04-17 | Backend | Task #324 | Task #324: Consolidate 5 near-duplicate services (audit findings W11-W15) — For each near-duplicate  |
| 🟡 | `ee659cfa4` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for eleven labs and sonner toasts — Add mockups for FunilElevenLabs, SonnerToasts, a |
| 🟡 | `6bb5bcfc6` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new toast notification components for improved user feedback — Add SonnerToasts.tsx and Template |
| 🟡 | `a9ae93b9a` | 2026-04-17 | Backend | Task #326 | Task #326 — CI guards e SLA de shim cleanup (S7.1 / S7.2 / S7.3) — Implementa as três regras anti-re |
| 🟡 | `469ee0565` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `1240f5859` | 2026-04-17 | Cross IA↔Back | Compliance / LGPD / EU AI Act | Task #321: Consolidate bias detectors into FairnessGuard SSOT — Unified 3 divergent bias-detection i |
| 🟡 | `ac036b7b9` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new toast notifications — Reorder mock component imports in artifa |
| 🟡 | `9a88c12e7` | 2026-04-17 | Cross IA↔Back | Task #322 | Task #322 — Cleanup: 12 órfãos, 5 stubs e duplicata exata de job_report_service — Removed 18 dead/du |
| 🔴 | `211da7846` | 2026-04-17 | Cross Back↔Front | Task #319 | Move agent_chat_ws_router under /api/v1 prefix (Task #319 / W17+W2) — Original task: audit findings  |
| 🟡 | `4448aefe3` | 2026-04-17 | Backend | Task #323 | Task #323: Consolidate duplicate pipeline_tool_registry into pipeline domain — The cv_screening copy |
| 🟡 | `b3e938641` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups system for improved testing — Add new mock component file paths to |
| 🟡 | `4c062522b` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mockup components to include decision bar mockups — Re-added mockups for decision bar compone |
| 🟡 | `676273609` | 2026-04-17 | Backend | Auditoria / Audit Rev | Audit: tighten require_company multi-tenant isolation across LIA tool registries — Reduced `require_ |
| 🟡 | `95497fd23` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | Task #311: Add audit logging + FairnessGuard to bulk_actions and stage_transition_automation — - bul |
| 🟡 | `17eeeb9d8` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include FunilElevenLabs — Update artifacts/mockup-sandbox/src/.generated/m |
| 🟡 | `2d27771ec` | 2026-04-17 | Backend | Compliance / LGPD / EU AI Act | Task #318 — Converge SSE chat path on shared pre/post compliance (R7) — Original task: agent_chat_ss |
| 🟡 | `0756d474d` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock component map to include WSI report tabs — Update mockup-components.ts to include import |
| 🟡 | `cc57d9110` | 2026-04-17 | Cross IA↔Back | §15 WSI | Task #317 — Compliance fixes for InterviewGraph & WSIInterviewGraph (A3/A4) — Both graphs now honour |
| 🟡 | `34cf27270` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `a1632367f` | 2026-04-17 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports for better organization — Reorganizes import paths for mock components |
| 🟡 | `a995eacef` | 2026-04-17 | Backend | Privacy / PII (W7) | Hotfix: imports canônicos de PII e Audit (Task #309) — Origem: auditoria docs/audits/AUDIT_STATUS_RE |
| 🟡 | `8e9182676` | 2026-04-17 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `4896b4221` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for candidate funnel and weekly digest features — Update mockup-components.ts to inc |
| 🟢 | `2d95f7e1f` | 2026-04-16 | Docs | scope: audit | docs(audit): cross-cutting AI layer status report (task #302) — Investigative-only audit. No code ch |
| 🟢 | `bfacb406e` | 2026-04-16 | Frontend (UI) | §15 WSI | fix(kanban): handle 401 from WSI scores without crashing the dev overlay (#303) — Original task: Qua |
| 🟡 | `3d357e5a8` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `6be1e4e01` | 2026-04-16 | Testes | Task #292 | audit(chat): auditoria Unified Chat (Task #292) — Auditoria somente-leitura do chat unificado da LIA |
| 🟢 | `a785f05bb` | 2026-04-16 | Frontend (api/util) | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟢 | `4ba0483c5` | 2026-04-16 | Frontend (api/util) | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟢 | `65fa3d2c7` | 2026-04-16 | Frontend (api/util) | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟢 | `60e4c824e` | 2026-04-16 | Frontend (api/util) | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟡 | `cb2ee08c7` | 2026-04-16 | Backend | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟢 | `976d77632` | 2026-04-16 | Testes | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🔴 | `14d8e53a5` | 2026-04-16 | Cross Back↔Front | §6 Chat Unificado / Funil | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 d |
| 🟢 | `0295b5e05` | 2026-04-16 | Frontend (UI) | §6 Chat Unificado / Funil | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 |
| 🟢 | `ebce04362` | 2026-04-16 | Frontend (UI) | §6 Chat Unificado / Funil | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 |
| 🔴 | `2e2412e79` | 2026-04-16 | Cross Back↔Front | §6 Chat Unificado / Funil | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 |
| 🟡 | `d4857587c` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `a282ed2fb` | 2026-04-16 | Backend | Performance | Update database index for improved candidate search performance — Correctly apply a functional index |
| 🟡 | `57aa4a8aa` | 2026-04-16 | Frontend (api/util) | scope: e2e | test(e2e): suite Playwright criacao manual de vaga — 37 testes (cherry-pick de develop) |
| 🟡 | `ab5237cd2` | 2026-04-16 | Backend | scope: candidates | perf(candidates): acelerar GET /candidates com payload slim + índices — Task #276 — alvo <1s p95. Ba |
| 🟡 | `d4af080fe` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update mock component list for weekly digest elements — Remove and re-add weekly digest mock compone |
| 🟢 | `030c32e55` | 2026-04-16 | Docs | §6 Chat Unificado / Funil | docs(audits): root-cause audit for Funil de Talentos errors — Task #287 — investigative-only audit o |
| 🟡 | `33ad15f12` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add weekly digest components to the mockups — Update `mockup-components.ts` to include new weekly di |
| 🟡 | `4b6d71f01` | 2026-04-16 | Backend | Task #283 | Migrate demo tenant row to canonical UUID (task #283) — Adds alembic migration 080_migrate_demo_comp |
| 🟢 | `07db52b0f` | 2026-04-16 | Frontend (UI) | scope: candidates | fix(candidates): destravar animação "LIA está buscando..." (Task #275) — Complementa Task #274 (tran |
| 🟢 | `03a6fba31` | 2026-04-16 | Frontend (UI) | Candidates (FE pages) | Improve error handling for various candidate search types — Add explicit error handling for non-OK H |
| 🟢 | `e175273fb` | 2026-04-16 | Frontend (UI) | scope: candidates | fix(candidates): destravar 'Failed to fetch' na listagem e busca — Task #274. Causa-raiz medida: `li |
| 🟢 | `3fb09d013` | 2026-04-16 | Frontend (api/util) | scope: candidates | fix(candidates): destravar 'Failed to fetch' na listagem e busca — Task #274. Causa-raiz medida: `li |
| 🟡 | `84fd73249` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update mock component generation for weekly digest — Reorder mock component imports in artifacts/moc |
| 🟡 | `7d9c3363d` | 2026-04-16 | Backend | Task #282 | Task #282: Fix dev-auto-login tenant + empty agent response — Two chained defects prevented the LIA  |
| 🟡 | `9cbcfb6de` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add and organize components for new mockup features — Update mock component registry to include new  |
| 🟢 | `88abdcf26` | 2026-04-16 | Frontend (api/util) | Task #281 | Fix literal <br/> appearing on login hero title — Task #281: The login page hero showed the raw stri |
| 🟢 | `eb549a121` | 2026-04-16 | Frontend (UI) | Chat UI (FE) | Improve chat functionality by fixing connection issues and response handling — Address audit recomme |
| 🟡 | `3d8683bf5` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for mock reports and notifications — Reorder and update component imports i |
| 🟢 | `2f8319d23` | 2026-04-16 | Frontend (UI) | Mockup Sandbox (artefato gerado) | docs: audit #277 — root cause of LIA no-response in Chat Unified — Audit-only task. Produced docs/au |
| 🟢 | `aebf061f8` | 2026-04-16 | Frontend (UI) | Frontend (componentes diversos) | Move layout client components to root directory — Refactors the location and naming of client-side l |
| 🟢 | `f85160b72` | 2026-04-16 | Frontend (UI) | Performance | Improve performance and fix styling bugs by enabling Turbopack — Enable Turbopack, clean cache, and  |
| 🟡 | `cbfb14403` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add a component for ElevenLabs funnel mockups — Add ElevenLabs funnel component to mockup library. |
| 🟡 | `d304ea242` | 2026-04-16 | Cross IA↔Back | §15 WSI | Task #238: Replace in-memory storage in WSI question-adjust endpoint with DB persistence — ## Summar |
| 🔴 | `f4075de94` | 2026-04-16 | Cross Back↔Front | Performance | Improve candidate search performance and reliability with retries and timeouts — Adds a `fetchWithRe |
| 🟡 | `95bb46f6c` | 2026-04-16 | Backend | Task #239 | fix: update callers after job_status_webhooks moved to /api/v1/job-status-webhooks — Task #239: Stop |
| 🟢 | `1c0baed94` | 2026-04-16 | Frontend (api/util) | Task #264 | Fix 4 failing tests in use-float-conversation hook (Task #264) — ## Problem |
| 🟡 | `837cda33b` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update component import paths for chat features — Update module imports in mockup-components.ts to r |
| 🟢 | `98615e123` | 2026-04-16 | Testes | scope: jobs | test(jobs): simulate 15 s AbortController timeout on listJobVacancies (Task #263) — The jobs list pa |
| 🟢 | `f6592977a` | 2026-04-16 | Frontend (api/util) | Task #261 | Fix flaky hook tests that randomly time out in CI (Task #261) — ## Root causes fixed |
| 🟢 | `6d8e9fab3` | 2026-04-16 | Frontend (UI) | Hooks (FE) | Add safeguards to prevent errors when insights data is not an array — Update the proactive insights  |
| 🟢 | `0c1e73c08` | 2026-04-16 | Testes | scope: job-detail-client | test(job-detail-client): add timeout path coverage for Task #262 — ## Original task |
| 🟡 | `9ae0178b3` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `5cdbc251d` | 2026-04-16 | Frontend (api/util) | Task #252 | Add automated coverage for the manual job creation flow (Task #252) — ## What was done |
| 🟡 | `b53a2b1b0` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `f0a40a4c2` | 2026-04-16 | Frontend (UI) | Task #254 | feat: extend useLoadingWatchdog to candidate-profile and screening-config pages (Task #254) — ## Sum |
| 🟢 | `74af0cc39` | 2026-04-16 | Testes | Task #255 | Add unit tests for useLoadingWatchdog hook (Task #255) — Created plataforma-lia/src/hooks/__tests__/ |
| 🟡 | `89567ac55` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups and adjust existing ones — Adds new mockups for "FunilElevenLabs"  |
| 🔴 | `726dc976c` | 2026-04-16 | Cross Back↔Front | Task #250 | feat(task-250): Show warning banner when external job source is unavailable — ## Summary |
| 🟡 | `5791478fe` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for sandbox mockups — Reorder module imports in `mockup-components.ts` to g |
| 🟡 | `e9d7b9976` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include a new component for ElevenLabs funnel — Update mockup-components.ts to cor |
| 🟢 | `fdfdf3890` | 2026-04-16 | Frontend (UI) | Task #251 | feat: add useLoadingWatchdog hook and wire into JobDetailClient (Task #251) — ## Summary |
| 🟢 | `ff4f70448` | 2026-04-16 | Frontend (UI) | i18n / Translation | Fix login hero i18n rendering (Task #253) — The left-side hero phrase on /en/login and /pt-BR/login  |
| 🟡 | `d1b734ced` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add new funil eleven labs component to mockups — Update mockups components map to include the new Fu |
| 🔴 | `7f4fe24f7` | 2026-04-16 | Cross Back↔Front | Task #241 | Task #241: Destravar tela de vaga após criação manual — Original task: When users create a job via t |
| 🟡 | `b0bc45b9c` | 2026-04-16 | Backend | FastAPI v1 endpoints | Make the embedding field optional in enrichment data — Modify `has_embedding` to be an optional bool |
| 🟡 | `714a60b60` | 2026-04-16 | Backend | Task #246 | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactors /api/v1/rails-sync/* |
| 🟢 | `ab4a56198` | 2026-04-16 | Testes | Task #246 | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactors /api/v1/rails-sync/* |
| 🟡 | `3fb811041` | 2026-04-16 | Backend | Task #246 | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactor of /api/v1/rails-sync |
| 🟢 | `a313275fa` | 2026-04-16 | Frontend (api/util) | Task #245 | Task #245: Frontend canonical cleanup (proxy routes + lia-api wrapper) — Scope (from task plan): |
| 🟡 | `c2da99b13` | 2026-04-16 | Frontend (UI) | Task #245 | Task #245: Frontend canonical cleanup (proxy routes + lia-api wrapper) — Scope (from task plan): |
| 🟡 | `38c5aa27c` | 2026-04-16 | Backend | §15 WSI | Update question generation to consolidate related functionality — Remove unused imports from questio |
| 🔴 | `c9ef726f7` | 2026-04-16 | Cross IA↔Front | §15 WSI | Task #244: Backend canonical cleanup (WSI router consolidation) — Scope (from task plan): collapse h |
| 🟢 | `769f54ee1` | 2026-04-16 | Frontend (UI) | Task #243 | Task #243: Unify dev auto-login and fix demo user seed — Backend (lia-agent-system): |
| 🔴 | `14a215850` | 2026-04-16 | Cross Back↔Front | Task #243 | Task #243: Unify dev auto-login and fix demo user seed — Backend (lia-agent-system): |
| 🟡 | `e50766222` | 2026-04-16 | Backend | Analytics (BE) | Improve import checking and event store error handling — Update import checker to scan additional di |
| 🔴 | `ff42c5642` | 2026-04-16 | Cross IA↔Back | Task #242 | task #242: eliminar colisão de mapper SQLAlchemy — Causa raiz: `lia-agent-system/app/models/` contin |
| 🟡 | `43b4082d0` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add a new component to the mockups for a funnel feature — Update mockups to include the FunilElevenL |
| 🟡 | `85babb985` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Remove unused component from mockups — Remove the FunilElevenLabs component from mockups. |
| 🟢 | `da046d20a` | 2026-04-16 | Docs | Task #240 | Disable GitHub Actions workflows (Task #240) — Renamed all four workflow files in .github/workflows/ |
| 🟡 | `92b95d873` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add a new component for ElevenLabs funnel integration and remove a duplicate entry — Include the Ele |
| 🔴 | `0e5ec3b9b` | 2026-04-16 | Cross IA↔Front | §15 WSI | Update webhook paths and improve question retrieval — Regenerate OpenAPI types to reflect backend ch |
| 🟡 | `4ae5721c8` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports to include weekly digest features — Reorganize and update module impor |
| 🟢 | `0cd0da1e1` | 2026-04-16 | Frontend (UI) | Task #237 | Migrate manual job-vacancies proxy routes to createProxyHandlers — Task #237: Replace hand-written f |
| 🟡 | `75c33db80` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `25077dd3a` | 2026-04-16 | Cross IA↔Back | Task #234 | Fix duplicate FastAPI operation IDs (task #234) — Original task: backend startup emitted 12 "Duplica |
| 🟢 | `d9d463ec0` | 2026-04-16 | Frontend (UI) | Task #235 | Fix /jobs/undefined navigation by unwrapping backend envelope in job-vacancies proxy routes — Task # |
| 🟡 | `3615daa37` | 2026-04-16 | Backend | Task #233 | Task #233: Scan all models for duplicate index names that block startup — ## What was done |
| 🟢 | `81778cd94` | 2026-04-16 | Docs | Docs (geral) | Update database schema documentation to list actively used tables — Refactors the `docs/DATABASE_SCH |
| 🟡 | `3914d2f8d` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include new toast and weekly digest mockups — Update artifacts/mockup-sa |
| 🟡 | `77faa626d` | 2026-04-16 | Backend | Task #231 | Fix backend startup failure caused by duplicate index names in FeedbackEvent model — Task #231: Fix  |
| 🟡 | `3865bec9e` | 2026-04-16 | Backend | Task #230 | Task #230: Add CI check to prevent model files being forgotten in __init__.py — New files: |
| 🟡 | `934fcd82d` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `490339a32` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Update component mockups to include new weekly digest features — Add new mockups for weekly digest f |
| 🟡 | `65455a5b2` | 2026-04-16 | Backend | Task #224 | Ensure all model files in lia_models are exported from __init__.py — Task #224: Audit and fix lia_mo |
| 🟡 | `8619de018` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups registry — Update artifacts/mockup-sandbox/src/.generated/mockup-c |
| 🟡 | `ca32d1ae3` | 2026-04-16 | Backend | §18 Senioridade + Job Migration | Expand forbidden import checker to scan root-level patch scripts (Task #223) — Changes to lia-agent- |
| 🟢 | `6eeed3e10` | 2026-04-16 | Docs | ADR-002 | Task #227: Atualizar ADR-002 — Refletir Realidade dos Proxies em app/models/ — Changes to lia-agent- |
| 🟡 | `91b32f5aa` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `83092c552` | 2026-04-16 | Backend | Task #222 | Align learning_patterns DB migration with consolidated LearningPattern model — Task #222: The CREATE |
| 🟡 | `acbcecea2` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `0cc8c6267` | 2026-04-16 | Outro | Task #220 | Fix forbidden import paths in patch_p2_5a_notifications.py (Task #220) — Replace 4 occurrences of `f |
| 🟡 | `4972c23ee` | 2026-04-16 | Backend | Task #221 | Task #221: Remove extend_existing band-aid from SourcingAgent model — Summary: |
| 🟡 | `14e35497c` | 2026-04-16 | Backend | Task #218 | Remove extend_existing band-aid from LearningPattern model — Task #218: Remove extend_existing=True  |
| 🟡 | `c0f197288` | 2026-04-16 | Backend | ADR-012 | Add pre-commit hook G5 to block forbidden import paths (ADR-012) — Task #219: Enforce ADR-012 import |
| 🟡 | `7989dc7ed` | 2026-04-16 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `cf20d3945` | 2026-04-16 | Backend | Task #217 | Task #217: Unificar Imports de Models — Eliminar Registros Duplicados no SQLAlchemy — ## Changes |
| 🟡 | `84dcc7f8c` | 2026-04-16 | Outro | Mockup Sandbox (artefato gerado) | Add new components for weekly digest features — Adds new mock components for BellNotification, ChatF |
| 🟡 | `cd4ee9719` | 2026-04-15 | Backend | Backend (libs) | Fix issue preventing chat functionality from working correctly — Add `extend_existing=True` to the S |
| 🟢 | `a3aac6b6b` | 2026-04-15 | Frontend (UI) | Kanban (vagas) | fix: QA fixes for Kanban t() and Funnel ensureServerReady (Task #216) — Two regression bugs from QA  |
| 🟡 | `471d63637` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for weekly digest notifications — Re-add components to the mockups configuration file |
| 🔴 | `8486175f9` | 2026-04-15 | Cross IA↔Front | Task #215 | feat: Pull QA fixes from fix/qa-2026-04-15 branch (Task #215) — Integrated 13 QA bug fixes from the  |
| 🟢 | `cf3585177` | 2026-04-15 | Empty/merge | Backend Migrations (alembic) | fix: resolve default_languages column type mismatch (ARRAY→JSONB) — The company_culture_profiles.def |
| 🔴 | `f7b3be109` | 2026-04-15 | Cross Back↔Front | Hooks (FE) | fix: resolve default_languages column type mismatch (ARRAY→JSONB) — The company_culture_profiles.def |
| 🟢 | `ec49215c3` | 2026-04-15 | Frontend (UI) | Task #214 | Task #214: Layout single column na página Minha Empresa — Changed the "Minha Empresa" page layout fr |
| 🟡 | `ce58b5f6e` | 2026-04-15 | IA | Configurações (hub) | Fix Settings chat domain routing: company_settings agent now receives messages — Problem: Messages s |
| 🟢 | `fcd55216f` | 2026-04-15 | Frontend (UI) | Chat UI (FE) | Fix chat functionality with REST fallback and improve auth token generation — Implement REST fallbac |
| 🔴 | `c50dfb90d` | 2026-04-15 | Cross IA↔Front | Task #213 | Task #213: Pull GitHub Updates (wedotalent02202026 + ats-api-copia) — Fetched and merged updates fro |
| 🟢 | `8a0c236a0` | 2026-04-15 | Testes | Configurações (hub) | Update end-to-end tests for settings migration and add new test cases — Refine existing end-to-end t |
| 🟢 | `59b7c67cc` | 2026-04-15 | Frontend (UI) | Configurações (hub) | Task #211: Migração Settings — Testes E2E Completos — Added comprehensive E2E test suite with 16 tes |
| 🟢 | `1b29ebb23` | 2026-04-15 | Testes | Configurações (hub) | Task #211: Migração Settings — Testes E2E Completos — Created comprehensive E2E test suite (settings |
| 🟢 | `9130f41ae` | 2026-04-15 | Testes | Configurações (hub) | Task #211: Migração Settings — Testes E2E Completos — Added E2E test suite for Settings migration va |
| 🟡 | `791a62b47` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Task #211: Migração Settings — Testes E2E Completos — E2E validation of the complete Settings menu m |
| 🟡 | `f8ed0c668` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Update mock components list to include new and reorganized files — Reorganize import paths for mock  |
| 🟢 | `661d3bf44` | 2026-04-15 | Frontend (UI) | Task #212 | Task #212: Corrigir Excluir/Renomear Conversa no Chat — Changes: |
| 🟡 | `8a1e93da7` | 2026-04-15 | Backend | Configurações (hub) | Update company ID query description to clarify default usage — Modify the description for the `compa |
| 🟡 | `bfbe89806` | 2026-04-15 | Backend | Task #210 | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py en |
| 🟡 | `f7e5ab867` | 2026-04-15 | Backend | Task #210 | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py en |
| 🔴 | `59038c744` | 2026-04-15 | Cross Back↔Front | Task #210 | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py en |
| 🟢 | `60995e512` | 2026-04-15 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with |
| 🟢 | `9cfd180b9` | 2026-04-15 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with |
| 🟢 | `2d4b34261` | 2026-04-15 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with |
| 🟢 | `869324240` | 2026-04-15 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard comp |
| 🟢 | `0ed6cdfe6` | 2026-04-15 | Frontend (UI) | Configurações (hub) | Task #208: Reestruturar Menu Configurações — 7 Novos Itens — - Refactored settings menu from old 7 i |
| 🟡 | `5a3483c50` | 2026-04-15 | Frontend (UI) | Configurações (hub) | Task #208: Reestruturar Menu Configurações — 7 Novos Itens — - Refactored settings menu from old 7 i |
| 🟢 | `83fa64e3a` | 2026-04-15 | Frontend (api/util) | Configurações (hub) | feat(task-207): UnifiedChat context switching for settings_config — Changes: |
| 🟢 | `c026791c1` | 2026-04-15 | Frontend (api/util) | Configurações (hub) | feat(task-207): UnifiedChat context switching for settings_config — Task: Migração Settings — Unifie |
| 🟢 | `d37b2981e` | 2026-04-15 | Frontend (UI) | Configurações (hub) | feat(task-207): UnifiedChat context switching for settings_config — Task: Migração Settings — Unifie |
| 🟡 | `bb2c23a95` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for toasts and eleven labs funnel |
| 🟡 | `203c1f9fb` | 2026-04-15 | Frontend (UI) | Kanban (vagas) | Fix Invalid Hook Call in Kanban and Agent Studio (Task #205) — Root causes fixed: |
| 🟢 | `05a309895` | 2026-04-15 | Frontend (UI) | Configurações (hub) | Update company settings to correctly handle headquarters location — Fix the mapping for headquarters |
| 🟢 | `058d6ae30` | 2026-04-15 | Frontend (api/util) | Task #206 | fix(task-206): Address all code review findings for Minha Empresa cards — 1. Reduced blocks from 8 t |
| 🟢 | `4e1dabe52` | 2026-04-15 | Frontend (api/util) | Task #206 | fix(task-206): Address all 4 code review findings for Minha Empresa cards — 1. Reduced blocks from 8 |
| 🟢 | `306982931` | 2026-04-15 | Frontend (UI) | Task #206 | Task #206: Minha Empresa conversational cards — full implementation — Frontend changes: |
| 🟢 | `f02fd9a42` | 2026-04-15 | Frontend (UI) | Task #206 | Task #206: Minha Empresa conversational cards — complete implementation — Frontend: |
| 🔴 | `403074a45` | 2026-04-15 | Cross IA↔Front | Task #206 | Task #206: Minha Empresa conversational cards + backend context routing — - Added `settings_config`  |
| 🟡 | `024f1cd8a` | 2026-04-15 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `e484d90a5` | 2026-04-15 | Backend | Configurações (hub) | Task #203: Backend company_settings domain integration + hardening — Domain Registration (6 gaps clo |
| 🟡 | `6c5c7bfaf` | 2026-04-15 | Backend | §9 Security / Tenant guards | Improve security by blocking access to internal network addresses — Update URL validation logic in ` |
| 🟡 | `1796d2d01` | 2026-04-15 | IA | Configurações (hub) | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados (6/6) |
| 🟡 | `f838be881` | 2026-04-15 | Backend | Configurações (hub) | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: |
| 🟡 | `17828c389` | 2026-04-15 | Backend | Configurações (hub) | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: |
| 🟡 | `70c32ce48` | 2026-04-15 | Cross IA↔Back | Configurações (hub) | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: |
| 🟡 | `b950dc4d0` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Update mockup components to include new funil elevenlabs feature — Reorder mock component imports in |
| 🟢 | `bb2029d2c` | 2026-04-15 | Docs | Configurações (hub) | Task #202: Auditoria profunda - Migração Settings Conversacional — Produced comprehensive diagnostic |
| 🟢 | `c8de45ef7` | 2026-04-15 | Frontend (UI) | Agent Studio (FE) | Update digital twin page translations and visual styling — Correct translation namespaces in Digital |
| 🟢 | `f3af139b4` | 2026-04-15 | Frontend (UI) | i18n / Translation | fix: Digital Twins i18n namespace + design consistency (Task #201) — Problem 1 - Translation keys sh |
| 🟡 | `812de0157` | 2026-04-15 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include weekly digest and WSI report tabs — Update mockup-components.ts to |
| 🟢 | `320d8192e` | 2026-04-15 | Frontend (api/util) | i18n / Translation | Fix translation BR tag rendering on login page — Replace self-closing <br/> with <br></br> in login. |
| 🟡 | `7a1b8dcbb` | 2026-04-15 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `cfd50764d` | 2026-04-15 | Frontend (UI) | §7 WorkflowRail UX | Task #199: Workflow Rail para Gêmeos Digitais - Onboarding UX — Redesigned the Digital Twins tab in  |
| 🟢 | `c47a48189` | 2026-04-15 | Frontend (UI) | Frontend (componentes diversos) | refactor: use existing isMounted from useSidebarState, non-interactive fallback |
| 🟢 | `2966492a2` | 2026-04-15 | Frontend (UI) | Frontend (componentes diversos) | fix: resolve Radix UI hydration mismatch in sidebar DropdownMenu |
| 🟡 | `7c9214a39` | 2026-04-15 | Backend | Task #198 | Task #198: Sync GitHub repos to Replit (one-way pull) — Pulled ~47 commits from wedotalent02202026 ( |
| 🟢 | `8507ca026` | 2026-04-15 | Empty/merge | Task #198 | Task #198: Sync GitHub repos to Replit (one-way pull) — Pulled ~47 commits from wedotalent02202026 ( |
| 🔴 | `6c878d719` | 2026-04-15 | Rails (ats-api) | Observability / Sentry / OTLP | Sync ats-api-copia from GitHub (JWT blacklist, Rails 7.1.5, Sentry, CORS, Bunny fixes) |
| 🟡 | `f8b6c1a57` | 2026-04-14 | Backend | Privacy / PII (W7) | fix: encrypt PII in Redis via Fernet [PX08-086] Wave 6 item 6.6 — - New RedisCrypto module: Fernet e |
| 🟡 | `55aa8300b` | 2026-04-14 | Frontend (UI) | §6 Chat Unificado / Funil | cleanup: remove legacy /funil page, redirect to /funil-de-talentos [PX08-082] Wave 6 item 6.2 — - De |
| 🟡 | `9126096cb` | 2026-04-14 | Cross IA↔Back | Task #93 | cleanup: remove LLMProviderFactory deprecated methods [PX08-081] Wave 6 item 6.1 — - Removed LLMProv |
| 🟡 | `4c79c511f` | 2026-04-14 | Backend | Docs / Configuration | docs: document staging Rails API URL in .env.example [PX08-007] — Staging URL: https://staging2.wedo |
| 🟡 | `6e40ff114` | 2026-04-14 | Backend | Sprint 11 | feat: golden scenario drift monitoring with baseline + alerts [P37-073] Sprint 11 item 11.3 — - New  |
| 🔴 | `e4faeb8c9` | 2026-04-14 | Cross Back↔Front | Sprint 12 | feat: Digital Twin config UI with premium design + chat cards [PX08-077] Sprint 12 item 12.2 — Backe |
| 🔴 | `dde1a35bf` | 2026-04-14 | Cross Back↔Front | §16 LIA Persona | feat: connect recruiter personalization to agent prompts [P36-079] Sprint 12 item 12.4 — - Personali |
| 🔴 | `93802c751` | 2026-04-14 | Cross Back↔Front | Sprint 12 | feat: Explain Decision button with reasoning transparency [PX08-080] Sprint 12 item 12.5 — Backend: |
| 🟡 | `537e104d7` | 2026-04-14 | Cross IA↔Back | §15 WSI | feat: WSI weights per tenant via CalibrationWeight [P36-078] Sprint 12 item 12.3 — - score_calculato |
| 🟡 | `b426149af` | 2026-04-14 | Backend | Sprint 11 | feat: persist ModelRegistry in PostgreSQL [PX08-075] Sprint 11 item 11.5 — - New table ml_model_regi |
| 🟡 | `6da287859` | 2026-04-14 | Backend | Backend (shared) | feat: TTF ML model — training script + predictor + endpoint integration [P37-074] — Sprint 11 item 1 |
| 🟢 | `a447db994` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: 8 adversarial eval scenarios for attack resistance [P37-072] — Sprint 11 item 11.2 — 8 attack  |
| 🟢 | `16463f952` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: 8 integration eval scenarios for agent handoffs [P37-071] — Sprint 11 item 11.1 — 8 handoff sc |
| 🟢 | `59a71de41` | 2026-04-14 | Docs | Docs / Architecture | docs: Langfuse integration decision — N/A, covered by LangSmith [PX08-070] — Sprint 10 item 10.5 — E |
| 🔴 | `5f705ff1b` | 2026-04-14 | Cross Back↔Front | §9 Security / Tenant guards | feat: calibration dashboard — LIA vs recruiter divergences [PX08-068] — Sprint 10 item 10.3 — Backen |
| 🔴 | `008535151` | 2026-04-14 | Cross Back↔Front | FastAPI v1 endpoints | feat: ML predictions dashboard — time-to-fill per vacancy [PX08-067] — Sprint 10 item 10.2 — Backend |
| 🟢 | `9d2b7d567` | 2026-04-14 | Frontend (UI) | Compliance / LGPD / EU AI Act | feat: connect Agent Control Center to quality dashboard endpoint [PX08-066] — Frontend integration f |
| 🔴 | `dddda1a0f` | 2026-04-14 | Cross Back↔Front | Compliance / LGPD / EU AI Act | feat: agent quality dashboard — aggregated metrics endpoint [PX08-066] — Sprint 10 item 10.1 — New e |
| 🟡 | `b41c542e4` | 2026-04-14 | Backend | Privacy / PII (W7) | fix: PII in logs remediation — 50 violations → 0 [PX08-062] — Sprint 9 item 9.4 — Removed PII (email |
| 🟡 | `71c2f86aa` | 2026-04-14 | Cross IA↔Back | §14 BYOK + LLM Factory | refactor: migrate all raise Exception() to LIAError hierarchy [P35-060] — Zero generic raise Excepti |
| 🟡 | `8372004db` | 2026-04-14 | IA | Compliance / LGPD / EU AI Act | feat: unified audit facade with trace_id + get_trail() [P35-061] — Sprint 9 item 9.3 — AuditService  |
| 🟡 | `02a31522f` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: LIAError hierarchy + global exception handlers [P35-060] — Sprint 9 item 9.2 — Unified error h |
| 🟡 | `84293fcd9` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | fix: PII masking + FairnessGuard in custom StateGraph agents [P35-059] — Sprint 9 item 9.1 — 14 ReAc |
| 🟡 | `77fc2a9b8` | 2026-04-14 | Infra/Config | DevOps / CI | ci: integrate eval runner in CI pipeline [PX08-050] — Sprint 6 item 6.5 — Eval suites now run on eve |
| 🟢 | `15116c386` | 2026-04-14 | Testes | Tests (BE unit/integration) | feat: 8 bias probe pairs for discrimination detection [P37-049] — Sprint 6 item 6.4 — 8 paired scena |
| 🟢 | `d2e9d39d2` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: rubrics YAML for 5 critical agents [P37-048] — Sprint 6 item 6.3 — Structured scoring rubrics  |
| 🟢 | `dd28d5a6c` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: golden datasets 10 screening + 10 sourcing [P37-047] — Sprint 6 item 6.2 — 20 structured golde |
| 🟢 | `fc29037a1` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: eval runner CLI — centralized eval orchestrator [P37-046] — Sprint 6 item 6.1 — Unified CLI fo |
| 🟡 | `990bd408b` | 2026-04-14 | IA | §2 Orchestrator Migration | fix: pass job_id to TenantContextService for pipeline awareness [P35-044] — MainOrchestrator now pas |
| 🟡 | `24f582c0b` | 2026-04-14 | Backend | §16 LIA Persona | feat: add pipeline stages and custom persona to platform awareness [P35-044] — Complement to Sprint  |
| 🟡 | `e196a3085` | 2026-04-14 | Backend | §15 WSI | feat: platform awareness injection in tenant context [P35-044] — Sprint 5 item 5.4 — Agents now know |
| 🟡 | `b6f6db3bd` | 2026-04-14 | Backend | Kanban (vagas) | refactor: migrate 8 remaining system prompts to YAML (batch 2) [P35-043] — Sprint 5 item 5.3 — Compl |
| 🟡 | `8d2e82b17` | 2026-04-14 | Backend | Wizard (geral) | refactor: migrate 6 largest system prompts to YAML (batch 1) [P35-043] — Sprint 5 item 5.3 — Migrate |
| 🟡 | `8835124b5` | 2026-04-14 | Infra/Config | §14 BYOK + LLM Factory | ci: add architectural fitness functions step [PX08-039] — Add pytest tests/fitness/ step to CI pipel |
| 🟢 | `c1089ce32` | 2026-04-14 | Testes | Compliance / LGPD / EU AI Act | feat: 6 architectural fitness functions [PX08-039] — Sprint 4 item 4.6 — Enforce consolidation decis |
| 🟡 | `61e464c90` | 2026-04-14 | Backend | §15 WSI | feat: SearchFeedback → re-ranking boost/penalty [PX08-031] — Sprint 3 item 3.4 — SearchFeedback (lik |
| 🟡 | `3a7b377d1` | 2026-04-14 | Backend | §9 Security / Tenant guards | feat: CalibrationEvent auto-record in EnhancedAgentMixin [P35-030] — Sprint 3 item 3.3 — Calibration |
| 🟡 | `84e2b5942` | 2026-04-14 | Backend | §15 WSI | feat: CalibrationWeight.load() in EnhancedAgentMixin [P35-029] — Sprint 3 item 3.2 — CalibrationWeig |
| 🟡 | `48a3c2571` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: guardrails_block.yaml — behavioral limits for all agents [P35-042] — Sprint 5 item 5.2 — Extra |
| 🟡 | `f6da91016` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: compliance_block.yaml — YAML-driven prompt compliance [P35-041] — Sprint 5 item 5.1 — Extracte |
| 🟡 | `8d6442e65` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | fix: add query_embeddings cleanup to LGPD deletion propagation [P35-033] — query_embeddings was list |
| 🟡 | `401bc516b` | 2026-04-14 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: protected attributes YAML single source of truth [P35-045] — Sprint 5 item 5.5 — Created confi |
| 🟡 | `0170c713b` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: LGPD deletion propagation to secondary stores [P35-033] — Sprint 3 item 3.6 — run_cleanup() no |
| 🟡 | `9c739b7cf` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: LGPD consent gate on all outbound communication [P35-032] — Sprint 3 item 3.5 — No communicati |
| 🟡 | `48d09a3fd` | 2026-04-14 | Backend | Compliance / LGPD / EU AI Act | feat: FairnessGuard post-check on agent output [P35-028] — Sprint 3 item 3.1 — Added fairness analys |
| 🟡 | `d0b237ed1` | 2026-04-14 | Backend | Backend (shared) | fix: WSManager Redis Pub/Sub broadcast across workers [PX08-025] — Sprint 2 item 2.2 — WSManager was |
| 🟢 | `6ef8c0548` | 2026-04-14 | Frontend (UI) | Backend Proxy Routes (FE) | fix: proxy onboarding returns 503 when Rails not configured [PX08-014] — Sprint 0 item 0.10 — Remove |
| 🟡 | `a97cba890` | 2026-04-14 | Outro | Mockup Sandbox (artefato gerado) | Configuração Jira/Atlassian secrets + atualização mockup components |
| 🟡 | `14cb932f4` | 2026-04-14 | Outro | Mockup Sandbox (artefato gerado) | Update module map to include new report and toast components — Reorder module imports in `mockup-com |
| 🟢 | `d4b36d996` | 2026-04-14 | Frontend (UI) | Task #197 | Task #197: Sidebar hover transitions graciosas — Added graceful hover transitions to both sidebars ( |
| 🟡 | `3659c2a2e` | 2026-04-14 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `736a09ede` | 2026-04-14 | Frontend (UI) | Configurações (hub) | Fix communication settings API to pass authentication token and handle errors gracefully — Corrected |
| 🟢 | `1800efed9` | 2026-04-14 | Frontend (api/util) | i18n / Translation | Redirect all English paths to Portuguese and update locale cookie — Modify middleware to redirect ro |
| 🟡 | `2be7fe57b` | 2026-04-14 | Frontend (api/util) | Configurações (hub) | Ensure the entire application displays in Portuguese — Update i18n settings to disable browser langu |
| 🟡 | `7e69b62a9` | 2026-04-14 | Frontend (api/util) | Docs / Auditorias | Fix errors when loading candidate data and improve API responsiveness — Refactors the `useCandidates |
| 🟢 | `8cec79473` | 2026-04-14 | Docs | Docs / Auditorias | Add audit documentation files for project phases — Add new audit files to the documentation for phas |
| 🟡 | `861e8b6c2` | 2026-04-14 | Frontend (UI) | i18n / Translation | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT str |
| 🟢 | `ad06793c3` | 2026-04-14 | Frontend (UI) | i18n / Translation | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT str |
| 🟡 | `8da34071b` | 2026-04-14 | Docs | i18n / Translation | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT str |
| 🟡 | `b6a53b820` | 2026-04-14 | Frontend (UI) | i18n / Translation | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT str |
| 🟡 | `40f82c150` | 2026-04-14 | Frontend (UI) | i18n / Translation | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT str |
| 🟡 | `60da75302` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #194 T007: Complete i18n for all Agent Studio remaining components — - AgentsTab: STATUS_CONFIG |
| 🟢 | `86b605790` | 2026-04-14 | Frontend (UI) | Configurações (hub) | feat(i18n): complete Settings, Agent Studio & Modules internationalization (Task #194) — - Agent Stu |
| 🟡 | `d4f6668eb` | 2026-04-14 | Frontend (UI) | Configurações (hub) | feat(i18n): complete Settings, Agent Studio & Modules internationalization (Task #194) — - Agent Stu |
| 🟢 | `428c2ebe5` | 2026-04-14 | Frontend (UI) | Configurações (hub) | feat(i18n): complete Settings, Agent Studio & Modules internationalization (Task #194) — - Agent Stu |
| 🟡 | `6009f288e` | 2026-04-14 | Frontend (UI) | Configurações (hub) | Task #194: Complete i18n for Settings, Agent Studio, and Modules pages — - Modules page fully i18n'd |
| 🟡 | `d862a331f` | 2026-04-14 | Frontend (UI) | Configurações (hub) | Task #194: i18n for Settings, Agent Studio, and Modules pages — - Modules page fully i18n'd with `mo |
| 🔴 | `304123b7a` | 2026-04-14 | Frontend (UI) | Configurações (hub) | Task #194: i18n for Settings, Agent Studio, and Modules pages — - T001: Modules page fully i18n'd wi |
| 🟡 | `37b2d1772` | 2026-04-14 | Backend | Task #196 | Task #196: Diagnostic v4 final - Politicas migram para Minha Empresa — Updated diagnostic document r |
| 🟢 | `c416afdf4` | 2026-04-14 | Docs | Docs / Auditorias | Update audit document to include detailed findings on agent intelligence perception — Adds a compreh |
| 🟡 | `c5799eb9a` | 2026-04-14 | Frontend (UI) | Triagem (módulo) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings fr |
| 🟡 | `2a1b2d014` | 2026-04-14 | Frontend (UI) | Triagem (módulo) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings fr |
| 🔴 | `3968b9d77` | 2026-04-14 | Frontend (UI) | Triagem (módulo) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings fr |
| 🟡 | `e803d72bb` | 2026-04-14 | Outro | Mockup Sandbox (artefato gerado) | Update weekly digest component imports to reflect current file structure — Update mockup components  |
| 🟡 | `bad7cef4d` | 2026-04-14 | Frontend (UI) | §6 Chat Unificado / Funil | Fix candidates not loading on Funil de Talentos page (Task #195) — ## Root cause fixes |
| 🟡 | `288dc3b03` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n for Login, Dashboard/Chat, Sidebar, Vagas — chat-workflow-reels.tsx: |
| 🟢 | `4c041ad62` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n for chat-workflow-reels.tsx — - Replaced RECRUITMENT_STAGES/UTILITY_NODES a |
| 🟢 | `d523e70b8` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n for remaining chat/jobs/sidebar components — Components updated with useTra |
| 🟡 | `cccc2ea75` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n for remaining chat/jobs components — Components updated with useTranslation |
| 🟢 | `ca4a7baa7` | 2026-04-14 | Docs | Docs / Auditorias | Update documentation to reflect platform architecture and audit findings — Update documentation file |
| 🟡 | `b0b3b27d2` | 2026-04-14 | Frontend (UI) | §13 PARTE D — Foundation/Apify/Manifest | Update documentation to reflect integration of Apify service for candidate enrichment — Modify audit |
| 🟡 | `3c81c343f` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n translation for Login, Dashboard/Chat, Sidebar, Jobs — All scoped component |
| 🟢 | `00a6b1465` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n translation for Login, Dashboard/Chat, Sidebar, Jobs — Translated component |
| 🟡 | `0f1c15a80` | 2026-04-14 | Frontend (UI) | i18n / Translation | Task #192: Complete i18n translation for remaining components — Translated components: |
| 🟢 | `0b99bfde0` | 2026-04-14 | Docs | Docs / Auditorias | Task start baseline checkpoint for code review |
| 🟢 | `848d9099d` | 2026-04-13 | Frontend (UI) | i18n / Translation | feat(i18n): add PT/EN language switcher to sidebar (Task #191) — - Create LanguageSwitcher component |
| 🟢 | `912ca851d` | 2026-04-13 | Docs | i18n / Translation | Update documentation to reflect current routing and i18n status — Update replit.md to accurately des |
| 🟢 | `93851d544` | 2026-04-13 | Frontend (api/util) | i18n / Translation | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-in |
| 🟢 | `d26f3251d` | 2026-04-13 | Frontend (api/util) | i18n / Translation | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-in |
| 🔴 | `764d08216` | 2026-04-13 | Frontend (UI) | i18n / Translation | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-in |
| 🟡 | `53598b49c` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Add internationalization for chat components to support multiple languages — Update mockup-component |
| 🔴 | `0ffd3e681` | 2026-04-13 | Cross Back↔Front | Task #189 | Fix SearchResults state preservation and duplicate index issue — Task #189: Fix SearchResults state  |
| 🟡 | `ef68e2edd` | 2026-04-13 | Frontend (UI) | Agent Studio (FE) | Update 'Sourcing' labels to 'Captação' across the platform for consistency — Replaces all instances  |
| 🟡 | `0e7118b18` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to reflect recent file renames — Restore correct imports in mockup-components |
| 🟢 | `d8b132664` | 2026-04-13 | Frontend (UI) | Task #188 | feat: atualizar subtítulo da landing page (task #188) — - Envolve "Conecta ao seu ATS" em <span clas |
| 🔴 | `d351f0710` | 2026-04-13 | Cross Back↔Front | Frontend (componentes diversos) | Apply Portuguese translations and fix various bugs across the application — This commit translates n |
| 🔴 | `57cbd5ad8` | 2026-04-13 | Frontend (UI) | Candidates (FE pages) | Update terminology from "score" to "nota" throughout the application — Replace instances of "score"  |
| 🟢 | `877dd98ff` | 2026-04-13 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix user page loading and status mapping for better user experience — Update `useUserManagement` hoo |
| 🟡 | `28dc0688e` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups for pipeline visualization — Update mockup-components.ts to includ |
| 🟢 | `7a2fb1be6` | 2026-04-13 | Frontend (UI) | scope: sidebar | feat(sidebar): add BETA badge to Agent Studio and Módulos menu items — Task #187 — Badge BETA no men |
| 🟡 | `58a42a721` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups library for testing and demonstration — Update mockup-components.t |
| 🟢 | `4d97d5a1e` | 2026-04-13 | Frontend (UI) | scope: pipeline-overview | feat(pipeline-overview): redesign PipelineCandidateCard with centralized scores, vacancy data and ba |
| 🟡 | `3449f8328` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Add new components for decision bar and toasts — Update mockup-components.ts to include new mockups  |
| 🟡 | `6ae1f9274` | 2026-04-13 | Frontend (UI) | Task #184 | fix: corrigir issues nas telas de candidatos e vagas (Task #184) — ## Mudanças implementadas |
| 🟡 | `6660b0126` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update mock component paths to include new weekly digest items — Reorganizes import paths for mock c |
| 🟢 | `1d7e14894` | 2026-04-13 | Frontend (UI) | Task #185 | Task #185: Alinhar modais de Contexto e Sugestões ao Design System + hint explicativo — Changes made |
| 🟡 | `010b9cae0` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for the report section — Refactor the mapping of components in `mockup-comp |
| 🟡 | `ffd4381df` | 2026-04-13 | Frontend (UI) | Performance | fix(performance): Corrigir performance de carregamento das páginas (Task #182) — Changes implemented |
| 🟡 | `44f9cad8a` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new report tabs — Update mock component registration to include ne |
| 🟢 | `1747ddae9` | 2026-04-13 | Frontend (UI) | Task #183 | feat: Remove horizontal row borders from candidate and jobs tables (Task #183) — ## Changes |
| 🟡 | `a111f3691` | 2026-04-13 | Frontend (UI) | Compliance / LGPD / EU AI Act | Redesign weekly digest chat card + complete E2E test suite fixes — Weekly Digest Chat Message: |
| 🟡 | `80d0a2ffe` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update component mappings for weekly digest and pending tab — Reorder imports in mockup-components.t |
| 🔴 | `0a7a49dee` | 2026-04-13 | Cross Back↔Front | Backend Proxy Routes (FE) | Make candidate search results consistently appear on the screen — Fix three API routes that were not |
| 🔴 | `620e9fcaf` | 2026-04-13 | Cross Back↔Front | §1 Teams Integration | Task #180: Integração Bot Teams em Produção — ## O que foi feito |
| 🟡 | `604a095e3` | 2026-04-13 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `eb11413da` | 2026-04-13 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Add auto-retry and cache control to improve page reliability — Adds auto-retry mechanisms for tasks  |
| 🟢 | `7d9188554` | 2026-04-13 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Improve app stability by addressing cold-start issues — Increase middleware timeout, make 401 status |
| 🟡 | `8cb474e58` | 2026-04-13 | Backend | Mockup Sandbox (artefato gerado) | Update component registrations and agent domain type — Modify mockup component mappings and change t |
| 🔴 | `5be674ef3` | 2026-04-13 | Cross Back↔Front | Backend Proxy Routes (FE) | Update API to correctly handle backend responses and improve server restart — Fix incorrect JSON unw |
| 🟡 | `3f416f078` | 2026-04-13 | Cross IA↔Back | scope: loop | feat(loop): Activate agentic loop by default + fix imports (LIA-A04) — 1. LIA-A04 activated by defau |
| 🟡 | `db3d7d8b5` | 2026-04-13 | Backend | scope: deploy | chore(deploy): Fase 7 — celery split + cache consolidation + CI docs — celery_tasks.py split (2128 → |
| 🟡 | `0b1916075` | 2026-04-13 | Backend | scope: intent | feat(intent): Fase 5 — _KEYWORD_ACTION_MAP → capabilities.yaml per domain (LIA-I05) — Extracted 15 d |
| 🟡 | `70d0ebc15` | 2026-04-13 | Backend | scope: sse | feat(sse): Fase 3 — /stream via MainOrchestrator (LIA-P05) — _sse_via_orchestrator() added to app/ap |
| 🟡 | `808811987` | 2026-04-13 | Backend | Voice / ElevenLabs / STT | fix: rename path param in get_detailed_invoice to avoid FastAPI conflict |
| 🟡 | `a5dce0848` | 2026-04-13 | Backend | Backend (shared) | Add API response envelope and contract tests for Rails events — Introduce Pydantic models for API re |
| 🟢 | `787ac1c05` | 2026-04-13 | Frontend (UI) | Jobs (FE pages) | fix: garantir auto-login em dev ignorando cookie lia_logged_out — - middleware.ts: em DEV_AUTO_LOGIN |
| 🟢 | `d3539e216` | 2026-04-13 | Frontend (api/util) | Login UI (FE) | Improve development login by simplifying token handling — Update the development login flow in the m |
| 🟡 | `8e83578d1` | 2026-04-13 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(compliance): Fase 3b — WS/SSE compliance strangler LIA-C3b — User-directed implementation of C3 |
| 🟡 | `8eff6ce4f` | 2026-04-13 | Backend | Observability / Sentry / OTLP | Task #178: Consumption Observability + Invoicing (backend-only) — Expanded ExternalApiConsumption mo |
| 🟡 | `f04c4d5a2` | 2026-04-13 | Backend | Observability / Sentry / OTLP | Task #178: Consumption Observability + Invoicing (backend-only) — Expanded ExternalApiConsumption mo |
| 🟡 | `ac5c718aa` | 2026-04-13 | Backend | FastAPI v1 endpoints | Add integrated tests for search fallback functionality — Adds a new route-level integration test to  |
| 🟡 | `af817da57` | 2026-04-13 | Backend | §13 PARTE D — Foundation/Apify/Manifest | Task #177: Apify Search Fallback — fix review issues — Addresses all code review findings: |
| 🟡 | `6212c221d` | 2026-04-13 | Backend | §13 PARTE D — Foundation/Apify/Manifest | Task #177: Apify Search Fallback — 3-step pipeline as Pearch alternative — Implements a full candida |
| 🟡 | `9ebe2405a` | 2026-04-13 | IA | §2 Orchestrator Migration | Task start baseline checkpoint for code review |
| 🟡 | `68c1da3f0` | 2026-04-13 | IA | scope: lia-a04,fase4 | feat(LIA-A04,Fase4): bind_tools in _handle_directly fallback path — Context: ReAct agents (90% of tr |
| 🟡 | `e35ff6a59` | 2026-04-13 | Backend | Compliance / LGPD / EU AI Act | feat(LIA-P02,Fase3c): close compliance gaps for Path C (LLM-direct endpoints) — Two cirurgical fixes |
| 🟡 | `bba2c54cd` | 2026-04-13 | Backend | scope: lia-d02,fase3a | feat(LIA-D02,Fase3a): AgentRegistry canonical + eliminate 21-branch if/elif dispatch — Wave 2 Fase 3 |
| 🟡 | `b221849f9` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Evolve Rails handlers and fix webhook naming conflicts — Update Rails handlers to include audit logs |
| 🟡 | `bdc3f9e25` | 2026-04-13 | Backend | scope: lia-sec-03,b-2 | fix(LIA-SEC-03,B-2): fail-closed webhook signature verification in prod/staging — Two real bypasses  |
| 🟡 | `1a3acb7fb` | 2026-04-13 | Backend | Policy / Job Creation | fix(B-1): create missing app/services/ott_service.py — unblocks JobCreationDomain — JobCreationAPICl |
| 🔴 | `7cf2b4722` | 2026-04-13 | Cross Rails+Replit | scope: deploy | feat(deploy): Migrations applied + Rails handlers evolved with side-effects — Migration fix — webhoo |
| 🟢 | `7405ad757` | 2026-04-13 | Testes | scope: pe-10 | test(PE-10): unit tests for Rails health endpoint (CI-friendly, no Rails needed) — Adds 4 tests for  |
| 🟡 | `d435a4d18` | 2026-04-13 | Infra/Config | DevOps / CI | ci: block unresolved merge conflict markers in main — Adds a CI step before ruff lint that greps for |
| 🟡 | `27add2f1f` | 2026-04-13 | Backend | §13 PARTE D — Foundation/Apify/Manifest | fix: resolve merge conflict markers in archetypes.py (Task #172 Apify T2) — Escolhido INCOMING em am |
| 🟢 | `4bd124f89` | 2026-04-13 | Testes | Tests (BE unit/integration) | Add tests for Rails health endpoints and update event handling — Adds unit tests for Rails health ch |
| 🟡 | `df9c8847f` | 2026-04-13 | Rails (ats-api) | Bridge React→Vue | feat(rails): Phase 5 — Rails Bridge handlers for Agent Studio events — Mirror commit on Rails side ( |
| 🟡 | `40b868ac7` | 2026-04-13 | Backend | Bridge React→Vue | feat(studio): Phase 5 — Rails Bridge for Agent Studio events (Python side) — Python side: webhook_di |
| 🟡 | `d9de6683d` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include a new funnel element — Update artifacts/mockup-sandbox/src/.gene |
| 🔴 | `613bf4db6` | 2026-04-13 | Frontend (UI) | §13 PARTE D — Foundation/Apify/Manifest | Task #173: Update talent funnel pricing — consistent "credits + $0.01 Apify" model — Core estimator  |
| 🟡 | `a52e4b1be` | 2026-04-13 | Backend | scope: pe-4 | fix(PE-4): rails_crud_consumer with DLQ + retry mechanism — Antes: |
| 🟡 | `51dfd6369` | 2026-04-13 | Backend | scope: billing | feat(billing): implement external API consumption tracking & invoicing (#174) — - Add ExternalApiCon |
| 🟡 | `2ede4aae7` | 2026-04-13 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `6402fbc77` | 2026-04-13 | Backend | scope: lia-llm-1 | feat(LIA-LLM-1): CI guardrail blocking direct LLM client instantiation — scripts/check_llm_factory_e |
| 🟡 | `a2ae935c8` | 2026-04-13 | Backend | scope: lia-llm-1 | fix(LIA-LLM-1): SSE respects Choose Your AI per-tenant config — Antes: chat.py SSE usava AsyncAnthro |
| 🟡 | `907c625a8` | 2026-04-13 | Backend | §9 Tenant Isolation / Multi-tenancy | fix(LIA-SEC-02,PE-9): Rails JWT company_id resolution fail-closed — resolve_company_from_rails_user  |
| 🟡 | `3a67504c4` | 2026-04-13 | Backend | scope: lia-sec-01 | fix(LIA-SEC-01): DEV_MODE sem API key agora eh fail-closed — Antes: LIA_DEV_MODE=1 sem LIA_DEV_API_K |
| 🟡 | `0566046f2` | 2026-04-13 | Backend | §9 Tenant Isolation / Multi-tenancy | cleanup(LIA-C01): remove deprecated _require_company_id from granular_consent + bias_audit — Both en |
| 🟡 | `a2d054dc4` | 2026-04-13 | Backend | Compliance / LGPD / EU AI Act | docs(autonomous): clarify compliance contract (no domain.py by design) — autonomous is Tier 6 cross- |
| 🟡 | `0da288f42` | 2026-04-13 | Backend | Compliance / LGPD / EU AI Act | feat(LIA-C01): enforce ComplianceDomainPrompt inheritance in registry — Before: logger.error only —  |
| 🟡 | `0d1f24af7` | 2026-04-13 | Frontend (UI) | scope: digest | feat(digest): inject weekly digest as chat message instead of floating overlay — Task #176 — Digest  |
| 🟡 | `8e9d36e03` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update component loading configuration to ensure proper functionality — Update `mockup-components.ts |
| 🟡 | `82c9c6ec5` | 2026-04-13 | Backend | §13 PARTE D — Foundation/Apify/Manifest | Task #172: Apify T2 — Pipeline de Busca: Enrichment Obrigatório + Remover Pro — Changes implemented: |
| 🔴 | `9969e1358` | 2026-04-13 | Cross Back↔Front | §13 PARTE D — Foundation/Apify/Manifest | feat(#170): Intelligent Apify + Pearch pipeline for candidate enrichment — - Enrichment pipeline rou |
| 🟡 | `c966dc9fa` | 2026-04-13 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for mockups — Reorder import statements in mockup-components.ts to maintain |
| 🟡 | `e964903cd` | 2026-04-13 | Backend | §13 PARTE D — Foundation/Apify/Manifest | Task #171: Apify T1 — Backend Core: Actor, Mapper e Serviço de Enriquecimento — Changes: |
| 🔴 | `5e3b4aeea` | 2026-04-13 | Rails (ats-api) | Rails (ats-api-copia) | Clean up unrelated files and improve system resilience — Remove extraneous files from the workspace  |
| 🟢 | `b14ce55b9` | 2026-04-13 | Docs | Compliance / LGPD / EU AI Act | docs: Agent Studio Enterprise final delivery report — Comprehensive report of all 17 commits deliver |
| 🔴 | `78b62cdaf` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.5b — External Webhooks for Studio events — Allows clients to subscribe to Studio ev |
| 🔴 | `e206cb06e` | 2026-04-13 | Cross Back↔Front | Compliance / LGPD / EU AI Act | feat(studio): P2.3 — Compliance Dashboard — Backend: GET /custom-agents/studio/compliance-summary |
| 🟡 | `7d867df94` | 2026-04-13 | Backend | scope: studio | feat(studio): P2.5a — Internal Notifications for Studio events — Reuses existing notification_servic |
| 🔴 | `81d3e2e2f` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.2 — Version History for Custom Agents — Every PATCH to a custom agent now creates a |
| 🟢 | `537d24ecf` | 2026-04-13 | Docs | scope: report | docs(report): consolidated refactoring report — 7 phases complete — Comprehensive report covering al |
| 🟡 | `e0b3b08bf` | 2026-04-13 | Backend | Wizard (geral) | chore: misc improvements alongside refactoring — Minor changes captured during F1-F7 refactoring acr |
| 🟡 | `5cc3cfcbd` | 2026-04-13 | Cross IA↔Back | scope: studio | feat(studio): RAG search + RESTRICTED tools audit — - Add rag_search ToolDefinition to AUTONOMOUS_TO |
| 🟡 | `82cf12528` | 2026-04-13 | Backend | scope: deploy | feat(deploy): F7 - deploy safety and consolidation [LIA-D01-D07] — - LIA-D01: Fix JobCreation import |
| 🔴 | `4c2373bbf` | 2026-04-13 | Cross IA↔Back | scope: intents | feat(intents): F5 - single source of intents in YAML + shared matcher [LIA-I01-I08] — - LIA-I01: Key |
| 🟡 | `71e8d28c5` | 2026-04-13 | Cross IA↔Back | scope: agentic | feat(agentic): F4 - real agentic loop, LLM thinks before acting [LIA-A01-A04] — - LIA-A01: LLM inter |
| 🟡 | `565cceb26` | 2026-04-13 | Backend | Compliance / LGPD / EU AI Act | feat(pipeline): F3 - unified pipeline, 9/9 entry points with compliance [LIA-P01-P05] — - LIA-P01: F |
| 🟡 | `85d9ce5d3` | 2026-04-13 | IA | scope: memory | feat(memory): F2 - memory persists, history as real LLM turns [LIA-M01-M05] — - LIA-M01: _setup_conv |
| 🟡 | `801ef14db` | 2026-04-13 | Backend | Compliance / LGPD / EU AI Act | feat(compliance): F1 - enforce compliance impossible to bypass [LIA-C01,C05,C06,C07] — - LIA-C01: re |
| 🟡 | `afba1da63` | 2026-04-13 | Backend | scope: architecture | docs(architecture): add ARCHITECTURE_TARGET.md - 7-phase refactoring plan — Defines target state of  |
| 🟡 | `0980b0677` | 2026-04-13 | Backend | Schemas / Pydantic (BE) | Phase 6 Batch 1: API contract infrastructure [LIA-E01..E05] — Add opt-in infrastructure for API stan |
| 🔴 | `3c940d5e8` | 2026-04-13 | Cross Back↔Front | Wizard/Onda 4 | feat(studio): Onda 4 — Studio <-> Chat Bridge — Enable Studio agent interaction via chat (create/que |
| 🔴 | `93bfd694d` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): P2.1 — Approval Workflow — Flow: draft → request → pending_approval → review → approve |
| 🟡 | `777594992` | 2026-04-13 | IA | scope: router | feat(router): P2.4 — CascadedRouter Tier 7: Studio agents in chat — 8-tier routing: memory → redis → |
| 🔴 | `0b6f0fdc1` | 2026-04-13 | Cross Back↔Front | scope: studio | feat(studio): Complete remaining Sprint 3-5 + P2 items — Sprint 3: ToolSelector checkbox grid (repla |
| 🟡 | `ba2f483bc` | 2026-04-12 | Backend | DevOps / Deploy (Docker/GCP) | fix: production Dockerfile and uvicorn command for GCP deploy |
| 🟢 | `d1b7544d4` | 2026-04-13 | Frontend (UI) | Wizard/Onda 3 | feat(studio): Onda 3 — Agent Details, Pipeline Card, Empty States — AgentDetailsPanel: full agent in |
| 🔴 | `b4ef2443c` | 2026-04-13 | Cross Back↔Front | Wizard/Onda 2 | feat(studio): Onda 2 — Conversational Creation + Test Debug Panel — Backend: POST /custom-agents/gen |
| 🟡 | `bc4c04b52` | 2026-04-13 | Backend | Backend Migrations (alembic) | feat: Close all production gaps — migrations, triggers, metering, history — Migration 070: agent_dep |
| 🟢 | `d8c3f516e` | 2026-04-13 | Frontend (UI) | Wizard/Onda 1 | feat(studio): Wire Onda 1 into AgentStudioPage custom tab — Custom Agents tab now shows: |
| 🟡 | `2a5133ee5` | 2026-04-13 | Backend | FastAPI v1 endpoints | Update backend files and remove script artifacts — Revert unrelated backend changes and remove lefto |
| 🟡 | `558b94fc5` | 2026-04-13 | Outro | Performance / Cold-start | fix: cold-start resilience for Jobs, Candidates, and Tasks pages — Root cause: Next.js dev server ta |
| 🔴 | `4d5a85fe9` | 2026-04-13 | Cross IA↔Front | FastAPI v1 endpoints | fix: cold-start resilience for Jobs, Candidates, and Tasks pages — Root cause: Next.js dev server ta |
| 🟡 | `1a60080be` | 2026-04-13 | Frontend (UI) | Wizard/Onda 1 | feat(studio): Onda 1 — Template Gallery, Agent Cards, Deploy Dialog — Foundation for AI-first Agent  |
| 🟡 | `79c4bdb6e` | 2026-04-13 | Backend | scope: studio | feat(studio): Sprint 0 — AgentDeployment binds agents to jobs/pools/stages — Agents without a deploy |
| 🟡 | `189643781` | 2026-04-13 | Backend | FastAPI v1 endpoints | fix: B3+B4 context_level in execute + remove duplicate in test — B3: execute_custom_agent() now pass |
| 🟡 | `fd1c84a88` | 2026-04-12 | Backend | scope: studio | feat(studio): Etapa 3 — context_level + Prompt Preview + RAG smoke — context_level routing in _get_s |
| 🟡 | `868c6b0d4` | 2026-04-12 | Backend | §9 Security / Tenant guards | Enhance agent security and LLM tenant compliance across multiple services — Introduces security patt |
| 🟡 | `6a08337ed` | 2026-04-12 | Backend | §14 BYOK + LLM Factory | feat(lgpd): Etapa 1 — LLM Factory Compliance, all calls tenant-aware — All LLM calls now respect ten |
| 🟢 | `13525f9c2` | 2026-04-12 | Frontend (UI) | Search (FE) | Remove duplicate icon import in filter section options — Remove a duplicate import of the AlertCircl |
| 🟢 | `74a271623` | 2026-04-12 | Frontend (api/util) | DevOps / Deploy (Docker/GCP) | fix: update plataforma-lia Dockerfile for GCP deploy |
| 🟡 | `cb0af1f76` | 2026-04-12 | Backend | DevOps / Deploy (Docker/GCP) | feat: add docker-compose.yml and docker-entrypoint.sh for GCP deploy |
| 🔴 | `130cd6886` | 2026-04-12 | Cross IA↔Front | Backend Proxy Routes (FE) | Revert "Merge remote-tracking branch 'origin/develop-giovanni'" — This reverts commit c7c2c060ca2b81 |
| 🟢 | `c7c2c060c` | 2026-04-12 | Empty/merge | (Auto-commit Replit) | Merge remote-tracking branch 'origin/develop-giovanni' |
| 🔴 | `d413ada7b` | 2026-04-12 | Cross IA↔Front | §14 BYOK + LLM Factory | fix: API routing, LLM Gemini fallback, auth token TTL and proxy fixes — - Add docker-compose.yml and |
| 🟡 | `979a613d7` | 2026-04-12 | Infra/Config | §9 Security / Tenant guards | Fix: npm audit fix - DOMPurify vulnerabilities resolved |
| 🟢 | `f0276ae18` | 2026-04-12 | Frontend (UI) | Agent Studio (FE) | Fix deploy: remove broken void(), clean ESLint errors (3/3 resolved) |
| 🟢 | `ec01ea69b` | 2026-04-12 | Frontend (UI) | Agent Studio (FE) | Fix deploy: AlertCircle import, unused expression |
| 🟢 | `928a6f4d8` | 2026-04-12 | Docs | scope: audit | feat(audit): Task #175 — Auditoria de Chaves de API, URLs e Secrets da Plataforma — Criado `lia-agen |
| 🟢 | `4da70fe08` | 2026-04-12 | Frontend (UI) | Backend Proxy Routes (FE) | Fix deployment build errors — 1. Add missing AlertCircle import in FilterSectionOpcoes.tsx |
| 🟡 | `7faa5fe66` | 2026-04-12 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `16bb9e95f` | 2026-04-12 | Docs | Compliance / LGPD / EU AI Act | Task #169 — Documentação Fairness Global+Local com Persistência e Observabilidade — Criado: lia-agen |
| 🟡 | `bd9f1eec4` | 2026-04-12 | Backend | §13 PARTE D — Foundation/Apify/Manifest | Add Apify integration for contact enrichment and health check — Integrates Apify API for contact dat |
| 🟡 | `3f5531538` | 2026-04-12 | Backend | Backend Services (BE) | fix: 3 bugs found during E2E validation of Agent Studio — Bug 1: Missing process() abstract method → |
| 🔴 | `d26626cfd` | 2026-04-12 | Cross Back↔Front | §13 PARTE D — Foundation/Apify/Manifest | T005: Frontend - Remove Pro search mode, update costs for Apify enrichment — - Updated candidate-sea |
| 🟡 | `6f8ea89f0` | 2026-04-12 | Outro | Mockup Sandbox (artefato gerado) | Update generated mock component list — Regenerate mock component list by updating import paths for t |
| 🟡 | `d331029ea` | 2026-04-12 | Backend | Backend Migrations (alembic) | feat: GAP 8 — schema migration + runtime connection — Model changes (3 new fields on custom_agents): |
| 🟢 | `192e9a0d2` | 2026-04-12 | Frontend (UI) | Candidates (FE pages) | Fix "Failed to fetch" on Jobs/Candidates — abort timeout + auto-recovery — Root cause: AbortControll |
| 🟢 | `3051d8b7e` | 2026-04-12 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix "Failed to fetch" on Jobs page — increase abort timeout for cold starts — Root cause: The AbortC |
| 🟡 | `8431d4160` | 2026-04-12 | Backend | Backend Services (BE) | feat: GAP 5 — expanded tool access for Agent Studio — - Pool 1: 40 autonomous tools (cross-domain, c |
| 🟡 | `64b9ae4ee` | 2026-04-12 | Backend | §9 Security / Tenant guards | feat: GAP 1-4,6 — Agent Studio parity with product agents — GAP 1: SystemPromptBuilder in custom_age |
| 🟡 | `19573c89b` | 2026-04-12 | Backend | Backend Services (BE) | feat: GAP 0 — RAG as agent tool (sourcing + autonomous) — - Fixed rag_search: passes db session to r |
| 🟢 | `c99f4fa1d` | 2026-04-12 | Frontend (api/util) | Candidates (FE pages) | Fix Jobs, Tasks, and Candidates pages data loading reliability — Changes: |
| 🟡 | `801f1d1cc` | 2026-04-12 | Frontend (UI) | Frontend (componentes diversos) | Fix Jobs and Tasks pages data loading reliability — Changes: |
| 🟢 | `d79d50f7a` | 2026-04-12 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix Jobs and Tasks pages data loading reliability — Root cause: Multiple issues caused data loading  |
| 🟡 | `c8dc25d76` | 2026-04-12 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix Jobs and Tasks pages data loading + pin Next.js version — Root cause: Multiple issues caused dat |
| 🟢 | `5e6010db2` | 2026-04-12 | Frontend (UI) | §9 Tenant Isolation / Multi-tenancy | fix: TypeScript error — user.company_id → user.company (matches auth context type) |
| 🟡 | `fb8547498` | 2026-04-12 | Backend | Compliance / LGPD / EU AI Act | fix: 4 agent gaps — try-catch, YAML registry, write audit — GAP 1: autonomous_tool_registry.py — 13  |
| 🟢 | `09c05517c` | 2026-04-12 | Frontend (api/util) | §9 Security / Tenant guards | fix: resolve 9 critical security vulnerabilities (npm audit fix) — Updated next 15.5.14 → patched (D |
| 🟡 | `9feb33b11` | 2026-04-12 | Backend | §13 PARTE D — Foundation/Apify/Manifest | refactor: replace Glassdoor scraper with multi-actor Apify strategy — - Removed bebity/glassdoor-sal |
| 🟡 | `ebe9185c2` | 2026-04-12 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `b8523c8d1` | 2026-04-12 | Cross IA↔Back | §15 WSI | feat: Phase 1 — connect 4 isolated features to main pipeline — QW1: Recruiter Personalization → Syst |
| 🟢 | `97832681c` | 2026-04-12 | Docs | Task #167 | Task #167: Documentação do gap de observabilidade na orquestração — Criado arquivo lia-agent-system/ |
| 🟡 | `033086895` | 2026-04-12 | IA | §16 LIA Persona | refactor: delete prompt_registry.py (0 callers) + unused getters — - Deleted app/shared/prompts/prom |
| 🟡 | `71d5915c7` | 2026-04-12 | Outro | Mockup Sandbox (artefato gerado) | Enable viewing candidate base in talent funnel — Update component mapping to include the talent funn |
| 🔴 | `d82313fc8` | 2026-04-12 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Ensure database connections are properly reset to prevent RLS issues — Update database connection ha |
| 🟡 | `75188a458` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | fix: remove 5 hardcoded LIA fallbacks — persona via SystemPromptBuilder — - company_users.py: remove |
| 🟡 | `3fc731723` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | refactor: isolate training persona from dynamic YAML flow — Training data is a versioned artifact —  |
| 🟡 | `bcabfe479` | 2026-04-12 | Backend | §9 Security / Tenant guards | feat: connect TenantContextService to SSE streaming endpoint — SSE streaming now passes tenant_conte |
| 🟡 | `9588ecadb` | 2026-04-12 | Cross IA↔Back | Wizard (geral) | refactor: P1/P2 cleanup — remove 449 lines of dead code (AST-verified) — Dead code removed (10 funct |
| 🟡 | `407a8a918` | 2026-04-12 | Backend | Task #166 | Fix WebSocket NameError: remove orphaned ws_action_metadata reference — After handle_action_flow was |
| 🟡 | `3435fc69f` | 2026-04-12 | Backend | Recruiter Assistant (BE) | fix: remove 4 broken imports + 2 LEGACY renames + 1 dead method — QA found 4 ImportErrors from ceae4 |
| 🟡 | `6a3eb82de` | 2026-04-12 | Backend | Task #166 | Fix merge regressions from Task #166 prompt unification + SQL injection hardening — MERGE REGRESSION |
| 🟡 | `4c25b0309` | 2026-04-12 | Backend | Task #167 | Task #167: Fix SQL injection vulnerabilities + merge regression fixes — SQL INJECTION HARDENING (8 f |
| 🟡 | `ceae4c600` | 2026-04-12 | Backend | §16 LIA Persona | refactor: final cleanup — remove 743 lines of legacy dead code + migrate training to YAML persona —  |
| 🟡 | `4de5efb00` | 2026-04-12 | Cross IA↔Back | Task #167 | Task #167: Fix SQL injection vulnerabilities — defense-in-depth hardening — CRITICAL FIX (user/LLM-i |
| 🟡 | `eb28a0727` | 2026-04-12 | Cross IA↔Back | §16 LIA Persona | refactor: complete prompt unification — eliminate all remaining hardcoded personas — Round 2: 32 pat |
| 🟡 | `18cb55227` | 2026-04-12 | Backend | Task #166 | Auth hardening: fix DEV_MODE bypass (Task #166) — Security fix for critical vulnerability where REPL |
| 🟡 | `59f475944` | 2026-04-12 | Backend | §16 LIA Persona | refactor: unify prompt pipeline — replace 16 hardcoded personas with SystemPromptBuilder — P0: chat. |
| 🟡 | `1b457b028` | 2026-04-12 | Backend | FastAPI v1 endpoints | refactor: P0 cleanup round 2 — remove more dead code from chat.py — - _flatten_entities() (7 lines)  |
| 🟡 | `21f504ad8` | 2026-04-12 | Backend | FastAPI v1 endpoints | refactor: P0 cleanup — remove 552 lines of dead code — Dead code removed: |
| 🟡 | `55ba81b35` | 2026-04-12 | Cross IA↔Back | Privacy / PII (W7) | feat: Item A Tipo C — audited Gemini native calls with PII strip + audit — - Add generate_native_gem |
| 🟡 | `b1ed88497` | 2026-04-12 | Cross IA↔Back | Privacy / PII (W7) | feat: Item A Tipo B — audited LangChain chain calls with PII strip + audit — - Create PIIStripCallba |
| 🟡 | `8173145f8` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | fix: M2 memory — session handling + in-memory response + ATS import — - Fix ATS_INTEGRATION_DOMAIN_S |
| 🟡 | `8587bc041` | 2026-04-12 | Backend | Communication domain (BE) | fix: add missing COMMUNICATION_DOMAIN_SPECIFIC import |
| 🟡 | `93fdefc95` | 2026-04-12 | Backend | Backend Services (BE) | fix: indentation in candidate_comparison_service.py broken by TODO comment |
| 🟡 | `9182a35c9` | 2026-04-12 | Backend | Job Management (BE) | fix: restore vacancy_search_service.py — imported by 2 endpoints (not dead duplicate) |
| 🟡 | `12fa1f74d` | 2026-04-12 | IA | §2 Orchestrator Migration | fix: indentation in orchestrator.py broken by TODO comment |
| 🟡 | `1fb338d94` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | feat: M2 pick-one-writer — MainOrchestrator owns persistence (retry) — Key difference from previous  |
| 🟢 | `b36b27bc7` | 2026-04-12 | Docs | Docs / Auditorias | docs: audit log final completo — sessao Path A + SystemPromptBuilder + 5 items |
| 🟡 | `7d59056ee` | 2026-04-12 | Cross IA↔Back | §15 WSI | fix: Item 3 — route WSI through safe_invoke + mark LLM tech debt — Tipo A (6 WSI calls): FIXED — rou |
| 🟡 | `af09e8070` | 2026-04-12 | IA | §15 WSI | fix: route 6 WSI question_generator calls through safe_invoke (Item 3 Tipo A) — Replaced 6 direct .c |
| 🟡 | `298173746` | 2026-04-12 | Backend | §9 Security / Tenant guards | feat: add FairnessGuard + SecurityPatterns to WebSocket handler (Item 4) — WS endpoint now has 3 lay |
| 🟡 | `76c795396` | 2026-04-12 | Backend | FastAPI v1 endpoints | feat: remove handle_action_flow calls — Phase 0+1 covers all 46 actions (Item 2) — Removed handle_ac |
| 🟡 | `ca4563eea` | 2026-04-12 | Backend | Kanban (vagas) | fix: wire agent_model_config into _get_model() — 5 agents switch to Haiku — _get_model() was always  |
| 🟡 | `90232b225` | 2026-04-12 | Backend | Recruiter Assistant (BE) | fix: add missing DOMAIN_SPECIFIC imports to all 11 agent files |
| 🟡 | `c13c7d20b` | 2026-04-12 | Backend | §16 LIA Persona | feat: move SystemPromptBuilder to base class — all 17 agents get persona (Commit 2) — langgraph_reac |
| 🟡 | `889d38a63` | 2026-04-12 | Backend | Kanban (vagas) | feat: extract DOMAIN_SPECIFIC from all 10 agents (Commit 1) — Batch extraction of domain-specific se |
| 🟡 | `a7a58af61` | 2026-04-12 | Backend | Compliance / LGPD / EU AI Act | Update agent system prompts with detailed instructions and compliance rules — Refactor system prompt |
| 🟡 | `3402210e1` | 2026-04-12 | Backend | Task #163 | Task #163: Audit & Governance — Monetizable Modules — Complete 14-dimension feature impact analysis  |
| 🟡 | `5de300b20` | 2026-04-12 | Backend | Compliance / LGPD / EU AI Act | feat: PoC TalentReActAgent using SystemPromptBuilder (Commit 2) — TalentReActAgent._get_system_promp |
| 🟡 | `18e94da13` | 2026-04-12 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: separate talent prompt + add ReAct instructions to SystemPromptBuilder (Commit 1) — SystemProm |
| 🟡 | `123f7b561` | 2026-04-12 | IA | §15 WSI | Adjust scoring thresholds for interview intelligence labels — Update the _bloom_label method in Inte |
| 🟡 | `668966ac6` | 2026-04-12 | Backend | §9 Security / Tenant guards | Task #162: Interview Intelligence Pro — Security + Bias + Comparative fixes — Code review round 2 fi |
| 🟡 | `635e1f4ae` | 2026-04-12 | Cross IA↔Back | §15 WSI | Task #162: Interview Intelligence Pro — Security + 7-Block WSI + Multi-Cohort Comparative — Code rev |
| 🟡 | `feafa932a` | 2026-04-12 | Cross IA↔Back | §15 WSI | Task #162: Interview Intelligence Pro — WSI + Viés + Parecer + Feedback — Implemented 5 new services |
| 🟡 | `52be1ab23` | 2026-04-12 | Backend | FastAPI v1 endpoints | docs: audit log final — Path A Passos 0-3 — Complete audit trail for Path A migration: |
| 🟡 | `aaeb584ca` | 2026-04-12 | Backend | Task #161 | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company |
| 🟡 | `9ef3c0c49` | 2026-04-12 | Backend | Task #161 | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company |
| 🟡 | `36d1c24f3` | 2026-04-12 | Cross IA↔Back | FastAPI v1 endpoints | revert: M2 skip_memory_persist — session sharing needs architectural decision — Reverted skip_memory |
| 🟡 | `cc182ca1b` | 2026-04-12 | Backend | Task #161 | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company |
| 🟡 | `221067b48` | 2026-04-12 | Backend | FastAPI v1 endpoints | fix: conversation re-fetch with None fallback + interview metadata reserved name — - get_conversatio |
| 🟡 | `637fad2da` | 2026-04-12 | Backend | FastAPI v1 endpoints | fix: replace db.refresh with re-fetch for M2 session compatibility — After M2 migration, MainOrchest |
| 🟡 | `f8eb9ed07` | 2026-04-12 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the sandbox for testing and development purposes — Update mockup-components.ts |
| 🔴 | `7a1af0f32` | 2026-04-12 | Cross IA↔Front | Wizard (geral) | feat: LIA Intelligence Overhaul — refactor prompt architecture for contextual responses — - Rewrote  |
| 🟡 | `54aee7902` | 2026-04-12 | Backend | FastAPI v1 endpoints | feat: M2 memory migration - MainOrchestrator owns persistence (Passo 3) — Items 1-4 of M2 memory mig |
| 🟡 | `3e6a0ab12` | 2026-04-12 | Cross IA↔Back | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: |
| 🟡 | `ab0824c32` | 2026-04-12 | IA | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: |
| 🟡 | `4145d3ba4` | 2026-04-12 | IA | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: |
| 🔴 | `b945f3bb7` | 2026-04-12 | Cross IA↔Front | Task #160 | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: |
| 🟡 | `c91bd09c5` | 2026-04-12 | Backend | §9 Security / Tenant guards | fix: add is_blocked property to InjectionCheckResult (security bug) — compliance_base.py:376 called  |
| 🟡 | `e08b06f04` | 2026-04-12 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `a3823816e` | 2026-04-12 | Docs | Docs / Auditorias | docs: update Path A audit log with Passo 2 Commits A+B |
| 🟡 | `cbf23f7ed` | 2026-04-12 | Backend | FastAPI v1 endpoints | feat: disable handle_action_flow via early return (Passo 2 Commit B) — MainOrchestrator Phase 0+1 no |
| 🟡 | `81396f56c` | 2026-04-12 | Backend | Compliance / LGPD / EU AI Act | feat: reconnect chat.py -> MainOrchestrator via ChatAdapter (Passo 2 Commit A) — Reconnect the prima |
| 🟡 | `4d030a846` | 2026-04-12 | IA | Compliance / LGPD / EU AI Act | feat: add ChatAdapter + skip_memory_persist flag (Path A Passo 1) — ChatAdapter bridges chat.py REST |
| 🟡 | `a1ce3a752` | 2026-04-12 | IA | §2 Orchestrator Migration | fix: propagate tenant_context_snippet through to_orchestrator_context() — Passo 0 of Path A migratio |
| 🟡 | `c974c46f3` | 2026-04-12 | Frontend (UI) | Task #159 | Task #159: Módulos page, sidebar nav, dashboard routing, BetaBadge — - Added "Módulos" sidebar item  |
| 🟢 | `f48d315d8` | 2026-04-12 | Frontend (UI) | Unified Chat (FE) | Adjust chat message font size for better readability — Change the font size of chat messages from 14 |
| 🔴 | `b1e40d0ce` | 2026-04-12 | Cross IA↔Front | §2 Orchestrator Migration | Improve how the system understands user requests and avoid unnecessary page changes — Adjust the con |
| 🟢 | `9f3ec4871` | 2026-04-12 | Frontend (UI) | Unified Chat (FE) | Fix chat page layout to remove middle scrollbar — Adjusted `UnifiedMessageList` to apply max-width t |
| 🟢 | `80f1cc94c` | 2026-04-12 | Frontend (UI) | Configurações (hub) | Add a functional context configuration panel to the chat interface — Introduce a new `ContextConfigP |
| 🟡 | `9efdafa14` | 2026-04-12 | Backend | Backend (shared) | Remove unused tenant isolation error message — Remove the dead _MODULE_CONTEXT_MISSING_RESPONSE cons |
| 🟡 | `9bd173c0f` | 2026-04-12 | Cross IA↔Back | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Fail-closed module gating for all premium |
| 🟡 | `7af3eb2d8` | 2026-04-12 | Backend | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating for |
| 🟡 | `9013ced8a` | 2026-04-12 | Cross IA↔Back | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating inf |
| 🟡 | `6c092ea51` | 2026-04-12 | Backend | Task #158 | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating inf |
| 🟡 | `3025c7374` | 2026-04-11 | Backend | Task #157 | Task #157: Monetizable Modules Infrastructure — Complete — Model & Migration: |
| 🟡 | `1ffc88be1` | 2026-04-11 | Backend | Task #157 | Task #157: Monetizable Modules Infrastructure — Complete — Model & Migration: |
| 🟡 | `15ae4cfa9` | 2026-04-11 | Backend | Task #157 | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatu |
| 🟡 | `752db1544` | 2026-04-11 | Backend | Task #157 | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatu |
| 🟡 | `1b6e85fe1` | 2026-04-11 | Backend | Task #157 | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatu |
| 🟡 | `e83bff7a7` | 2026-04-11 | Testes | Task #164 | Task #164: Production Readiness Eval V2 — Teste Exaustivo de Prompts Expandido — Expanded LIA platfo |
| 🟡 | `92b742c15` | 2026-04-11 | IA | §2 Orchestrator Migration | Accurately track costs across multiple AI models in a cascade — Refactor LLMCascadeRouter to impleme |
| 🟡 | `75ac7a8f1` | 2026-04-11 | Backend | Policy / Job Creation | Task #153: Per-request cost + RAG recursive default + policy doc type — 1. LLMCascade: Wire request_ |
| 🟡 | `0db172dcd` | 2026-04-11 | IA | Task #153 | Task #153 final: Per-request cost tracking wired end-to-end + retrieval tests — 1. LLMCascade: Wire  |
| 🟡 | `364b8bf9c` | 2026-04-11 | Cross IA↔Back | Task #153 | Task #153 final fixes: Wire per-request cost tracking end-to-end — 1. LLMCascade: Wire request_id th |
| 🟡 | `778721272` | 2026-04-11 | Backend | Task #153 | Task #153: Guardrails Per-Request + RAG Semantic Chunking — Per-request cost tracking: |
| 🟡 | `bb344d222` | 2026-04-11 | Cross IA↔Back | Task #153 | Task #153: Guardrails Per-Request + RAG Semantic Chunking — Per-request cost tracking: |
| 🟡 | `e93d57b77` | 2026-04-11 | Cross IA↔Back | Task #145 | Task #145: Align LIA prompts with actual tool capabilities — Fixed prompt-tool mismatches across 6 p |
| 🔴 | `007ce8bfe` | 2026-04-11 | Frontend (UI) | Task #152 | Task #152: Fix all TypeScript errors — 59+ errors to 0 — Changes made: |
| 🟢 | `df7ce03b6` | 2026-04-11 | Frontend (UI) | Login UI (FE) | Add a clear but subtle message about WeDO's ATS integration flexibility — Add a new paragraph to the |
| 🟡 | `16b1afc1a` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update mock component list to include ElevenLabs funnel — Update artifacts/mockup-sandbox/src/.gener |
| 🟡 | `71a5edfec` | 2026-04-11 | Backend | Task #154 | Task #154: Complete API Spec + Admin Endpoints + Quota Enforcement — New admin endpoints (admin_exte |
| 🟡 | `b5398962e` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update component definitions to include new mockups — Add a new definition for FunilElevenLabs.tsx t |
| 🟡 | `c9f1bfc2c` | 2026-04-11 | Cross IA↔Back | scope: #147 | feat(#147): Loop Autônomo e Inteligência Proativa — Implements proactive intelligence for LIA recrui |
| 🟡 | `2d95fbe6a` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for mockups and digests — Update artifacts/mockup-sandbox/src/.generated/mo |
| 🟡 | `164c34fe4` | 2026-04-11 | Cross IA↔Back | Task #146 | Task #146: Implement Competitive Talent Intelligence Tools — New domain: lia-agent-system/app/domain |
| 🟡 | `8984b6054` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `2a70c3220` | 2026-04-11 | Backend | Task #144 | Task #144: Activate stub domain actions across 7 core platform domains — Replaced all stub responses |
| 🟡 | `7574d67e1` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — domain services as source of truth — Domain services m |
| 🔴 | `db08579cd` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — domain services as source of truth — Domain services m |
| 🟡 | `f95ac8e71` | 2026-04-11 | Backend | Task #151 | feat(task-151): Complete services migration — single source of truth — Shim elimination (app/service |
| 🟡 | `85af8700b` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — single source of truth — Shim elimination: |
| 🔴 | `ef3114c66` | 2026-04-11 | Cross IA↔Back | Task #151 | feat(task-151): Complete services migration — single source of truth — - Eliminated 129 forward/back |
| 🟡 | `1c06d4bea` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Add toast notification components for a better user experience — Update mockup-components.ts to incl |
| 🟢 | `3d5330509` | 2026-04-11 | Docs | §1 Teams Integration | Task #155: Excalidraw — Adicionar Microsoft Teams como Front Layer — Added Microsoft Teams Tab as a  |
| 🟡 | `83ff514e0` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `85d0aaf9d` | 2026-04-11 | Cross Back↔Front | Task #156 | Task #156: Corrigir Agent Studio — Agentes Funcionais E2E — Changes across 5 files to fix broken Age |
| 🟢 | `92c78649b` | 2026-04-11 | Testes | Backend Services (BE) | Update domain catalog and ensure all domains are properly registered — Update DOMAIN_CATALOG.md to r |
| 🟡 | `331bf58d8` | 2026-04-11 | IA | Task #150 | Task #150: Domain Consolidation — Classify 57 Domains — Created DOMAIN_CATALOG.md at app/domains/ wi |
| 🔴 | `d973395c8` | 2026-04-11 | Backend | Task #150 | Task #150: Domain Consolidation — Classify 57 Domains — Created DOMAIN_CATALOG.md at app/domains/ wi |
| 🟡 | `6df8f6874` | 2026-04-11 | Backend | scope: agent-studio | feat(agent-studio): activate stubs + metering/billing separation (#148) — - Activate Agent Studio st |
| 🟢 | `4a44a6cd6` | 2026-04-11 | Testes | Tests (BE unit/integration) | Update tests to reflect changes in orchestrator processing — Modify mock assertions in extended test |
| 🟢 | `843f0cd88` | 2026-04-11 | Testes | Task #149 | Task #149: Orchestrator Cleanup — Dead Code Removal + Refactor — Dead code removal: |
| 🟡 | `a0067df13` | 2026-04-11 | IA | Task #149 | Task #149: Orchestrator Cleanup — Dead Code Removal + Refactor — Dead code removal: |
| 🟡 | `c1f858b17` | 2026-04-11 | Cross IA↔Back | Task #149 | Task #149: Orchestrator Cleanup — Remove dead IntentRouter code — Changes: |
| 🟡 | `e139479b8` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `5eee537b9` | 2026-04-11 | Backend | Automations | feat: add admin platform endpoints (webhooks, automation, health, version) — 5 new endpoints consume |
| 🟢 | `98a2c20e5` | 2026-04-11 | Docs | Docs / Architecture | docs: comprehensive diagnostic report - architecture, domains, Rails ATS analysis |
| 🟡 | `8de193476` | 2026-04-11 | Outro | Docs / Diagramas | feat: add updated Detailed System Architecture diagram (April 2026) — - Updated from real codebase:  |
| 🟡 | `c50ff50df` | 2026-04-11 | Outro | scope: diagrams | feat(diagrams): update LIA architecture diagram to v4.2.2 — Reflects ~101 commits across ~15 tasks c |
| 🟡 | `732f7868f` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to reflect current weekly digest structure — Update the mock component mappin |
| 🟡 | `b5ab76b98` | 2026-04-11 | Frontend (UI) | Task #142 | Task #142: Fix LIA Chat modes and default behavior (sidebar always present) — Changes made: |
| 🔴 | `b82c8f73f` | 2026-04-11 | Cross Back↔Front | Hooks (FE) | Refactor hooks into domain-specific folders and generate API types — Reorganize all frontend hooks i |
| 🟡 | `5f9bd57a4` | 2026-04-11 | IA | §9 Security / Tenant guards | Improve screening process security and update documentation — Remove sensitive token from screening  |
| 🟡 | `ad7e897a3` | 2026-04-11 | Cross IA↔Back | Triagem (módulo) | Implement real start_screening handler + fix code quality issues — T001: Replaced stub _start_screen |
| 🟡 | `d8c592289` | 2026-04-11 | IA | Triagem (módulo) | Implement real start_screening handler + fix code quality issues — T001: Replaced stub _start_screen |
| 🟡 | `181bbdba5` | 2026-04-11 | IA | Triagem (módulo) | Implement real start_screening handler (was last simulated stub) — Replaced the stub _start_screenin |
| 🟢 | `d611d642f` | 2026-04-11 | Docs | Auditoria / Audit Rev | Deep audit revision of PRODUCT_READINESS_AUDIT_REPORT.md — Updated the correct audit document (PRODU |
| 🟢 | `30551691d` | 2026-04-11 | Frontend (UI) | Talent Funnel (FE) | Improve tab loading by rendering them only when active — Conditionally render tab content within Tab |
| 🟢 | `788baa5c7` | 2026-04-11 | Frontend (UI) | Talent Funnel (FE) | Improve ability to load candidate lists by adding automatic retries — Add retry logic with delay to  |
| 🟢 | `2e1b0fde4` | 2026-04-11 | Frontend (UI) | Talent Funnel (FE) | Add history tab with clock icon to talent funnel page — Add HistoryTab component, Clock icon import, |
| 🟢 | `3ad20e2fe` | 2026-04-11 | Frontend (UI) | §6 Chat Unificado / Funil | Add icons to Funil de Talentos tabs for visual consistency — - Added Lucide icons (Search, Heart, Li |
| 🔴 | `0bfffe539` | 2026-04-11 | Cross Back↔Front | Task #141 | Pipeline: UX Cards + Data Audit + Icons/Stages (Task #141) — 1. seed_service.py: Canonical stage key |
| 🟡 | `918929f41` | 2026-04-11 | Frontend (UI) | Configurações (hub) | Standardize page headers, tab navigation, and spacing across all pages — Created shared PageTabNavig |
| 🟢 | `fac9af415` | 2026-04-11 | Frontend (UI) | Kanban (vagas) | Clean up unused code and comments from the candidate card and row — Remove dead code and unnecessary |
| 🟢 | `6909948df` | 2026-04-11 | Frontend (UI) | Task #140 | Task #140 audit cleanup: remove orphan visaoGeral type references — - Removed 3 occurrences of 'visa |
| 🟢 | `dcb976c6c` | 2026-04-11 | Frontend (UI) | Task #140 | Fix Jobs page crash: add missing lucide-react icon imports — After Task #140 merge, jobs-page.tsx us |
| 🟡 | `f0bc0e15b` | 2026-04-11 | Frontend (UI) | Task #140 | Task #140: Remover Visão Geral e Integrar Sugestões no Chat LIA — Changes: |
| 🟢 | `045767162` | 2026-04-11 | Frontend (UI) | Agent Studio (FE) | Final cleanup: 14 secondary0 typos, 1 gray class, zero remaining |
| 🔴 | `b4891f266` | 2026-04-11 | Cross IA↔Front | Performance | Task #138: Performance, Prompt Versioning & Rails Integration Readiness — All 6 subtasks completed w |
| 🟢 | `895481238` | 2026-04-11 | Frontend (UI) | Kanban (vagas) | Fix: SaturationBadge secondary0 typo |
| 🔴 | `4ca637641` | 2026-04-11 | Cross IA↔Front | Kanban (vagas) | Visual components: 12 categories fixed - shadows, borders, table headers, dots, rounded, empty state |
| 🟢 | `998564a0b` | 2026-04-11 | Frontend (UI) | Configurações (hub) | Tabs unified: tabStyles Agent Studio pattern, 3 custom tabs aligned, 7 Settings auto-inherit |
| 🟡 | `e91d59f83` | 2026-04-11 | Backend | Compliance / LGPD / EU AI Act | Task #137: P1 Compliance & Governance — FairnessGuard, AI Disclosure, SOX — All 6 task items impleme |
| 🟢 | `efabbb83b` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Vagas tabs: Agent Studio pattern with icons and pill badges |
| 🟢 | `4ee7061e6` | 2026-04-11 | Docs | Design System v4.2.2 | Design System v4.2.2: document updated with all new values, 4 new sections, zero old refs |
| 🟡 | `d7c0d4e5d` | 2026-04-11 | Backend | Compliance / LGPD / EU AI Act | Task #137: P1 Compliance & Governance — FairnessGuard, AI Disclosure, SOX — All 6 task items impleme |
| 🔴 | `39252ae74` | 2026-04-11 | Cross IA↔Front | Chat UI (FE) | DS final: remaining chat bubble and handler hooks |
| 🔴 | `a737c0267` | 2026-04-11 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Task #137: P1 Compliance & Governance — FairnessGuard, AI Disclosure, SOX — All 6 task items impleme |
| 🟢 | `58ef17b24` | 2026-04-11 | Frontend (UI) | Triagem (módulo) | DS Phase 3-6: tabs standardized, 318 badge overrides cleaned, hex tokenized |
| 🔴 | `0f379a75b` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Update UI components and code formatting across multiple client-side files — Refactor various UI com |
| 🟢 | `087d09486` | 2026-04-11 | Frontend (UI) | Talent Funnel (FE) | Task start baseline checkpoint for code review |
| 🔴 | `8690b05d0` | 2026-04-11 | Cross IA↔Front | Task #139 | Task #139: Redesign TopBar — Avatar e Notificações na Sidebar — Moved recruiter avatar, notification |
| 🟡 | `8e7a4407e` | 2026-04-11 | IA | §2 Orchestrator Migration | Improve template creation with better data handling — Refactors the `_create_template` handler to us |
| 🟢 | `89b758f52` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | DS Phase 1-2 cleanup: remove remaining 16 inline Open_Sans declarations |
| 🔴 | `efa142c5b` | 2026-04-11 | Cross IA↔Front | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallb |
| 🟡 | `c1334df3e` | 2026-04-11 | Backend | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallb |
| 🟢 | `9fdbe7dc0` | 2026-04-11 | Empty/merge | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallb |
| 🔴 | `98109faad` | 2026-04-11 | Cross Back↔Front | Frontend (componentes diversos) | DS Final Phase 1-2: root fixes + typography standardization (235 files) |
| 🟡 | `5bebbdc3e` | 2026-04-11 | Cross IA↔Back | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallb |
| 🟡 | `c2b3ddf95` | 2026-04-11 | IA | Task #136 | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallb |
| 🟡 | `58417c7d3` | 2026-04-11 | Cross IA↔Back | §2 Orchestrator Migration | Update job handling and logging to improve system reliability — Refactor action handler hooks to adj |
| 🟡 | `94c3deb9e` | 2026-04-11 | IA | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: |
| 🟡 | `7a2ef320f` | 2026-04-11 | Cross IA↔Back | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: |
| 🟡 | `1b76403e0` | 2026-04-11 | IA | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: |
| 🟡 | `44db5fe52` | 2026-04-11 | IA | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: |
| 🟡 | `eb2961176` | 2026-04-11 | IA | Task #135 | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: |
| 🟡 | `82605c5b8` | 2026-04-11 | Cross IA↔Back | Task #135 | Task #135: Action Handlers → Real DB Operations + Fix PL-002 — Changes: |
| 🟡 | `30d2dc03e` | 2026-04-11 | Backend | Task #134 | Task #134: P0 — Fix Alembic Migration Chain + DB Schema Validation — Root cause: File 061_create_onb |
| 🟡 | `989d6af6c` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `2430e8220` | 2026-04-11 | Frontend (UI) | Task #133 | Task #133: LIA Chat UX — Ícone, Abertura e Sidebar Polish — Changes made across 4 files: |
| 🟢 | `f370c2259` | 2026-04-11 | Testes | Task #132 | Task #132: Deep Audit + Eval Suite Execution + Product Readiness Report — - Fixed critical DB issue: |
| 🟢 | `16f8ab929` | 2026-04-11 | Testes | Task #132 | Task #132: Deep Audit + Eval Suite Execution + Product Readiness Report — - Fixed critical DB issue: |
| 🟢 | `d40929942` | 2026-04-11 | Frontend (UI) | §6 Chat Unificado / Funil | Strategic color points: Funil status filters, Alerts bell icon amber |
| 🟢 | `9deec2786` | 2026-04-11 | Frontend (UI) | Configurações (hub) | Fix: Funil subtitle redundancy, Settings missing SECTION_ICON_COLORS definition |
| 🔴 | `6af3cf400` | 2026-04-11 | Cross Back↔Front | scope: agent-studio | feat(agent-studio): Implement Fase 4 — Agent Studio & Custom Agent Marketplace — Task #130: Full cus |
| 🟡 | `cf7176ff4` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `49e7b8778` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `17a885664` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Add new toast notifications to the mockup sandbox — Update the mockup sandbox by adding SonnerToasts |
| 🟡 | `41fbd7a7d` | 2026-04-11 | Backend | scope: crew-delegation | fix(crew-delegation): resolve all code review issues for Fase 3 — 1. CrewContext atomicity: HSET+EXP |
| 🟡 | `73f951d04` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include new weekly digest mockups — Modified artifacts/mockup-sandbox/sr |
| 🟡 | `3a42a1dd8` | 2026-04-11 | Cross IA↔Back | Fase 3 | Task #129: Fase 3 — Guardrail de Custo por Request Individual — Per-request token budget ceiling pre |
| 🟡 | `75a3e49ae` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `c75536b53` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update mock component registration to include new toast and report types — Updated artifacts/mockup- |
| 🟡 | `1cf273c6a` | 2026-04-11 | Cross IA↔Back | Task #124 | feat(task-124): Activate A/B testing of prompts in production — - Created experiment YAML configs fo |
| 🟡 | `1779286c6` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include new components and organize existing ones — Adjusted the generated mockups |
| 🟡 | `4c57fff89` | 2026-04-11 | Backend | Fase 2 | Task #126: Fase 2 — Semantic Chunking para RAG (Section-Aware + Semantic) — Implemented three chunki |
| 🟡 | `03941fd48` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `7f2052cf6` | 2026-04-11 | Frontend (api/util) | Tests (FE e2e) | Improve test reporting by attaching screenshots to test information — Updated `takeEvalScreenshot` f |
| 🟡 | `781b525c7` | 2026-04-11 | Frontend (api/util) | Task #131 | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Comprehensive P |
| 🟡 | `025b0afce` | 2026-04-11 | Frontend (api/util) | Task #131 | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Created a compr |
| 🟡 | `f5aecbc7d` | 2026-04-11 | Frontend (api/util) | Task #131 | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Created a compr |
| 🟡 | `d5fe5ef85` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `6ca941e60` | 2026-04-11 | Cross IA↔Back | Task #121 | Task #121: Expand OpenTelemetry instrumentation (Full Coverage) — - CascadedRouter: All 7 tiers + fa |
| 🟡 | `b180e9c85` | 2026-04-11 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `71095fbac` | 2026-04-11 | Cross IA↔Front | Fase 2 | Fase 2 — HITL Badge de Aprovações Pendentes no Header (Task #125) — Backend: |
| 🟡 | `cce263d25` | 2026-04-11 | IA | Fase 1 | Fase 1 — RAGAS Blocking no CI/CD + Golden Datasets por Domínio (Task #122) — Changes: |
| 🔴 | `b68483941` | 2026-04-11 | Cross Back↔Front | scope: #128 | feat(#128): SSE Fallback for Chat Streaming (Fase 3) — Backend: |
| 🔴 | `81e989874` | 2026-04-11 | Cross Back↔Front | Fase 1 | Fase 1 — Cost Dashboard Granular por Agente + Alertas (Task #123) — Backend changes (lia-agent-syste |
| 🟢 | `6ca09bef7` | 2026-04-11 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Improve visual consistency between chat and pipeline views — Adjusted pipeline component styling to  |
| 🟢 | `2be93615c` | 2026-04-11 | Frontend (UI) | §6 Chat Unificado / Funil | Fix: replace redundant stats bar with unique metrics (funil, entrevistas, conversao, risco) |
| 🟡 | `2cbe59080` | 2026-04-11 | Frontend (UI) | Configurações (hub) | Colorization: stats bars, colored icons, tab badges - Vagas, Tarefas, Funil, Settings |
| 🟢 | `aa774f7ac` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Remove horizontal line from pipeline view to reduce visual noise — Remove border-t border-lia-border |
| 🟢 | `54213f918` | 2026-04-11 | Docs | Mockup Sandbox (artefato gerado) | Improve pipeline view contrast and align visuals with chat interface — Update pipeline view to use v |
| 🔴 | `03956df08` | 2026-04-11 | Frontend (UI) | UI Components (FE library) | Design System: replace 179 shadcn defaults with lia tokens, remove 4 decorative borders |
| 🟢 | `67c4117cb` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Add interactive zoom effect to pipeline overview stages — Implement a magnifier effect on the Pipeli |
| 🟢 | `e60b7e036` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Update the pipeline and chat interfaces with a new visual style — Replaces emoji cards with icons an |
| 🟢 | `93466aaa3` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Design System: fix last outliers - outlined variant, remaining underline tabs |
| 🔴 | `fbc64beee` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Design System Phase 3: 2259 rounded-xl containers, 274 decorative borders removed, 592 files |
| 🟡 | `d151e7678` | 2026-04-11 | Outro | Mockup Sandbox (artefato gerado) | Update component generation for visual consistency — Regenerate mockup components to align visual el |
| 🟡 | `0d3f80691` | 2026-04-11 | Frontend (UI) | Task #120 | Task #120: TipTap Rich Text — Email Templates e Job Descriptions — Integrated TipTap WYSIWYG editor  |
| 🔴 | `392a203ed` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Design System Phase 2: gray tokens, hover states, tabs pill, rounded-xl containers |
| 🔴 | `58ed2d300` | 2026-04-11 | Frontend (UI) | Frontend (componentes diversos) | Update component styling and improve user interface elements — Refactor various UI components to enh |
| 🔴 | `b687d930e` | 2026-04-10 | Cross IA↔Front | §14 BYOK + LLM Factory | Task #119: Voice Abstraction in LLM Factory + Streaming Frontend — Created VoiceStreamProviderABC ab |
| 🟡 | `828cd47c5` | 2026-04-10 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `9787e738c` | 2026-04-10 | Frontend (api/util) | Docs / Configuration | Update documentation with correct environment variable names — Update VALIDATION_PLAN.md and DEPLOY_ |
| 🟢 | `913e10bf1` | 2026-04-10 | Testes | Tests (FE e2e) | Update authentication to support staging environments and improve deployment guide — Update auth fix |
| 🟢 | `4175bf2da` | 2026-04-10 | Frontend (api/util) | Task #116 | Task #116: Plano de Validação e Smoke Tests — Pré Go-Live — Created comprehensive validation plan an |
| 🟢 | `6e8e74c40` | 2026-04-10 | Testes | Task #116 | Task #116: Plano de Validação e Smoke Tests — Pré Go-Live — Created comprehensive validation plan an |
| 🟢 | `f1ade9154` | 2026-04-10 | Frontend (api/util) | Design System v4.2.2 | Design System: add typescript ignoreBuildErrors |
| 🟢 | `4207da3c0` | 2026-04-10 | Frontend (UI) | Modals (FE) | Update modals to improve user experience and information display — Adjusted the Add to Job modal to  |
| 🟡 | `a30e05192` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Add new components for mockups to the system — Update the generated mockup-components.ts file to inc |
| 🟡 | `aaf336f31` | 2026-04-10 | Outro | Task #118 | Task #118: Diagrama Excalidraw — Arquitetura Completa LIA + Diagnóstico de Mercado — Created a compr |
| 🟢 | `11f66809b` | 2026-04-10 | Docs | DevOps / Deploy (Docker/GCP) | Update infrastructure checklist and worker health check — Update GCP Infrastructure Checklist for en |
| 🟢 | `71d3c7938` | 2026-04-10 | Frontend (UI) | Task #115 | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECK |
| 🟢 | `9a067fe27` | 2026-04-10 | Frontend (UI) | Task #115 | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECK |
| 🟢 | `a8b8732f2` | 2026-04-10 | Docs | Task #115 | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECK |
| 🟡 | `3a4af080a` | 2026-04-10 | Backend | §9 Security / Tenant guards | Improve security scanning by removing extraneous output — Modify CI workflow to adjust the output of |
| 🟡 | `93c9df0e9` | 2026-04-10 | Backend | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — CI/CD workflows for both repositories + i |
| 🔴 | `f86387396` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — CI/CD workflows for both repositories + i |
| 🟡 | `386c67465` | 2026-04-10 | Backend | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastr |
| 🔴 | `e1bd7d78e` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastr |
| 🔴 | `dde1d6f0d` | 2026-04-10 | Cross Back↔Front | DevOps / Deploy (Docker/GCP) | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastr |
| 🟢 | `d112fce5b` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Ensure candidate preview displays correctly by fixing a display condition — Fix a conditional render |
| 🟢 | `091adc6ab` | 2026-04-10 | Frontend (UI) | Task #113 | Task #113: Backend Production Hardening — Deploy Blockers — Backend changes: |
| 🟡 | `0b4f53344` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Add new components for reporting and chat features — Update mockup-components.ts to include new impo |
| 🟡 | `70dfdc14c` | 2026-04-10 | Testes | Task #117 | Task #117: Create comprehensive quality test suite for LIA agents + diagnostic report generator — Co |
| 🟢 | `46446fa91` | 2026-04-10 | Frontend (UI) | Backend Proxy Routes (FE) | Update onboarding proxy route to correctly handle dynamic paths — Refactors the `onboarding/[...path |
| 🔴 | `6f75253d7` | 2026-04-10 | Cross Back↔Front | Task #113 | Task #113: Backend Production Hardening — Deploy Blockers — Changes made: |
| 🟢 | `4516860a4` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Update UI elements and API handling for jobs and agent templates — Refactors UI components for job l |
| 🟡 | `ae85d2b23` | 2026-04-10 | Frontend (UI) | Task #112 | Task #112: Frontend Production Hardening — Deploy Blockers — Changes made: |
| 🟡 | `deb214dec` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Task #112: Frontend Production Hardening — Deploy Blockers — VERIFICATION RESULTS — All 6 items conf |
| 🟢 | `72b810898` | 2026-04-10 | Docs | Docs / Configuration | Update AI agent domain counts to reflect current scope — Normalize the number of business domains fr |
| 🟢 | `4c9d6fb1a` | 2026-04-10 | Docs | Task #111 | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY |
| 🟢 | `853205f22` | 2026-04-10 | Docs | Task #111 | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY |
| 🟢 | `4c4006989` | 2026-04-10 | Docs | Task #111 | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY |
| 🟢 | `9a863a043` | 2026-04-10 | Docs | Task #111 | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Updates to DEPLOY_GUIDE.md ref |
| 🟢 | `d869f573f` | 2026-04-10 | Docs | Task #111 | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Updates to DEPLOY_GUIDE.md ref |
| 🟡 | `feb6757a3` | 2026-04-10 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `9c37c675e` | 2026-04-10 | Backend | FastAPI v1 endpoints | Add new endpoints for onboarding and WhatsApp messaging — Integrate new routers for onboarding and W |
| 🟡 | `465751df3` | 2026-04-10 | Backend | Backend Migrations (alembic) | Add new tables for onboarding and WhatsApp sessions — Add `onboarding_agent_state` and `whatsapp_ses |
| 🟢 | `1b4eeefe0` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Move operational section to top of sidebar menu — Update sidebar.tsx to reorder menu sections, placi |
| 🔴 | `9f42c9782` | 2026-04-10 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Improve agent studio functionality and fix backend route issues — This commit addresses multiple bug |
| 🟡 | `bdf5afff5` | 2026-04-10 | Outro | §9 Security / Tenant guards | Update project dependencies and resolve security vulnerabilities — Update outdated project dependenc |
| 🔴 | `bbe4db71b` | 2026-04-10 | Cross Back↔Front | scope: onboarding-lia | feat(onboarding-lia): complete conversational onboarding system — Onboarding LIA — UAU experience fo |
| 🟡 | `4c7aa1fb0` | 2026-04-10 | Frontend (api/util) | §9 Security / Tenant guards | Update project dependencies to address security vulnerabilities — Update aiohttp, jspdf, next, and j |
| 🟢 | `d58ed6c92` | 2026-04-10 | Frontend (UI) | Kanban (vagas) | Disable ESLint during build to allow deployment — Adds `eslint.ignoreDuringBuilds: true` to `next.co |
| 🟡 | `946cc05db` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update component mappings for several mockups — The generated `mockup-components.ts` file has been u |
| 🟡 | `f7bfa2adf` | 2026-04-10 | Frontend (UI) | Task #108 | Task #108: Exhaustive Playwright E2E audit of Agent Studio — - Created comprehensive Playwright spec |
| 🟢 | `f82b3f77f` | 2026-04-10 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Address ESLint warnings in several components to unblock deployment — Adds `eslint-disable` comments |
| 🟡 | `2ff9fe0ed` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for testing modules — Reorder imports in mockup-components.ts to group rela |
| 🟡 | `7f237d2c0` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Add a component for the ElevenLabs funnel and adjust existing ones — Update mockup-components.ts to  |
| 🟡 | `4f06897d7` | 2026-04-10 | Frontend (UI) | scope: candidate-preview | feat(candidate-preview): Task #107 — PipelineDecisionBar + Candidate Highlight — - Created PipelineD |
| 🟡 | `2c3714a6d` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update mockups for new decision bar components and existing features — Replace 'FunilElevenLabs' com |
| 🟢 | `13f800baa` | 2026-04-10 | Frontend (UI) | Task #106 | Task #106: Fix LIA brain icon — chat não abre em páginas standalone — Problem: The LIA brain icon (c |
| 🟡 | `6263e98d3` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Add mockups for candidate pipeline decision actions — Adds mockup components for candidate decision  |
| 🟡 | `e5be1788f` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Add a new funnel talent screen for managing candidate data — Add a new route and component for the t |
| 🟢 | `03b582313` | 2026-04-10 | Frontend (api/util) | Hooks (FE) | Add retry logic to candidate loading to prevent initial load errors — Implement automatic retry mech |
| 🟡 | `7c4cababe` | 2026-04-10 | Backend | FastAPI v1 endpoints | Allow zero limit for candidate searches — Adjust search request models to permit a `pearch_limit` of |
| 🟡 | `9d51b5db5` | 2026-04-10 | Backend | FastAPI v1 endpoints | Fix critical search bug and add recruitment campaign stub functionality — Corrects the candidate sea |
| 🟢 | `3c46f81d4` | 2026-04-10 | Docs | Docs / Auditorias | Add search quality audit report and fix critical search endpoint issues — Create a markdown document |
| 🟡 | `8b1c7f80e` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update platform to fix agent creation errors and improve page navigation — Corrects agent creation i |
| 🟢 | `92802179d` | 2026-04-10 | Testes | Task #105 | Task #105: Search Quality Audit Playwright suite (WeDOTalent cross-reference) — File: plataforma-lia |
| 🟡 | `7ed6d449f` | 2026-04-10 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `004ee812d` | 2026-04-10 | Frontend (UI) | Task #104 | Fix LIA brain icon not appearing on pages (Task #104) — The UnifiedChatBubble component had multiple |
| 🟢 | `ca0383f98` | 2026-04-10 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix errors when creating agents and loading platform data — Updates Agent Studio to handle API error |
| 🟢 | `accba8553` | 2026-04-10 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Fix blank chat page and data disappearing issues — Increase retry attempts for data fetching and adj |
| 🟢 | `1c1674255` | 2026-04-10 | Frontend (UI) | Unified Chat (FE) | Improve chat functionality and fix candidate data loading errors — Refactor unified chat component f |
| 🟡 | `927247279` | 2026-04-10 | Frontend (UI) | §15 WSI | Fix rendering issues and improve user experience across multiple components — Address a JSX syntax e |
| 🟡 | `9513ba3bc` | 2026-04-10 | Frontend (UI) | §15 WSI | polish(wizard-wsi): cosmetic fixes — type safety, UX, accessibility — - Remove `as any` casts in use |
| 🔴 | `07422c531` | 2026-04-10 | Cross IA↔Front | Configurações (hub) | Fix task display and improve security for search settings — Address an issue where the task list was |
| 🟢 | `eccecf27b` | 2026-04-10 | Frontend (UI) | §15 WSI | fix(wizard-wsi): wire calibration events, prefill listener, publish/review actions — Fixes 5 HIGH pr |
| 🔴 | `c3beb2b2d` | 2026-04-10 | Frontend (UI) | §15 WSI | feat(wizard-wsi): Sprint 1B+2A+3+4 — complete frontend + backend patches — Frontend (24 files): |
| 🟡 | `040c71fb4` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Rearrange chat interface elements and adjust positioning for better usability — Update UI components |
| 🔴 | `e02734183` | 2026-04-10 | Cross Back↔Front | Backend Services (BE) | Update user profile and authentication features — Introduces profile editing, password change functi |
| 🔴 | `c5408615e` | 2026-04-10 | Cross Back↔Front | §15 WSI | feat(wizard-wsi): complete Phase B+C+D — Wizard WSI conversational job creation — Backend (13 Python |
| 🟢 | `29e53fd81` | 2026-04-10 | Frontend (UI) | Backend Services (BE) | Improve display of enlarged icons in workflow reels — Adjust CSS to allow enlarged icons in the chat |
| 🔴 | `9bb5b231a` | 2026-04-10 | Cross IA↔Front | Voice / ElevenLabs / STT | Improve chat functionality by using browser's speech recognition and fixing icon clipping — Integrat |
| 🟢 | `ec2e10ac6` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Remove redundant AI chat features from candidate search pages — Remove unused imports and LIA sideba |
| 🟢 | `16bf34b1e` | 2026-04-10 | Frontend (UI) | Frontend (componentes diversos) | Improve pipeline screen design to match platform standards — Refactor PipelineOverviewPage component |
| 🟢 | `3d34b63b8` | 2026-04-10 | Frontend (UI) | UI Components (FE library) | Improve visibility of chat input elements and icons — Update text color for placeholder, buttons, an |
| 🟢 | `fb5a58785` | 2026-04-10 | Frontend (UI) | UI Components (FE library) | Adjust display of workflow icons and header elements for better visibility — Update chat workflow re |
| 🟡 | `b59c332cb` | 2026-04-10 | Backend | §9 Security / Tenant guards | Improve security and reliability of Rails integration endpoints — Update Rails integration endpoints |
| 🟢 | `b59e20097` | 2026-04-10 | Frontend (UI) | Task #103 | Fix ESLint errors blocking deployment (Task #103) — Three ESLint violations fixed across three files |
| 🔴 | `a6514672b` | 2026-04-10 | Cross Back↔Front | Task #102 | Task #102: Pipeline Overview — Centro de Comando do Recrutador — Backend changes: |
| 🟢 | `1c2d5ab04` | 2026-04-10 | Frontend (UI) | Task #101 | Chat UI Polish — Magnifier Dock + Border + Header Cleanup (Task #101) — Changes: |
| 🟢 | `3e1f40d9a` | 2026-04-10 | Frontend (UI) | Task #100 | feat(task-100): Weekly Digest — Resumo Semanal para Recrutadores — ## Summary |
| 🟡 | `8d2a6bb01` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update component mappings for mockups to include new report tabs — Reorder and update component mapp |
| 🔴 | `1bb42a5b7` | 2026-04-10 | Cross Back↔Front | §1 Teams Integration | fix(production-readiness): Teams URL default + replace all silent catch handlers — ## Task #98 — Pro |
| 🟡 | `5fcad56b8` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | Update component imports after merging new features — Reorder import statements in `mockup-component |
| 🟡 | `df8a0a581` | 2026-04-10 | Outro | Mockup Sandbox (artefato gerado) | feat(mockup): Task #97 — Mockups de Toasts Sonner no Canvas — Created two mockup components in artif |
| 🟡 | `aba75e8c8` | 2026-04-10 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase A — @mention autocomplete + /slash commands — 5 new files: |
| 🔴 | `3cad3eb72` | 2026-04-10 | Cross Back↔Front | FastAPI v1 endpoints | Add real-time candidate counts to recruitment pipeline stages — Adds a new backend endpoint and fron |
| 🔴 | `7f658ccb0` | 2026-04-10 | Cross IA↔Front | Sprint 4 | feat: Sprint 4 — Agent Studio conversational creation via chat — Backend: |
| 🟢 | `55457ac95` | 2026-04-09 | Frontend (UI) | scope: calibration | feat(calibration): Sprint 3 — shared CalibrationCandidateCard + adapters — Created unified calibrati |
| 🟢 | `9d0f1ba98` | 2026-04-09 | Frontend (UI) | Frontend (componentes diversos) | Enhance job application workflow with new suggestions and rename functionality — Add new suggestions |
| 🔴 | `05d5c8ff4` | 2026-04-09 | Cross Back↔Front | Backend (genérico) | feat(backend): Sprint 3 — PATCH /conversations/{id} for rename + wire to UnifiedChat — - Added Renam |
| 🟢 | `c0d3ea46c` | 2026-04-09 | Frontend (UI) | Task #95 | feat(task-95): Chat Workflow Reels — sugestões como fluxo visual — ## Task |
| 🟡 | `3751ef241` | 2026-04-09 | Frontend (UI) | Backend Proxy Routes (FE) | Fix file upload errors and update API proxy routes — Corrects file upload authentication forwarding  |
| 🟡 | `2ce967310` | 2026-04-09 | Cross IA↔Back | FastAPI v1 endpoints | Fix issues with talent pool data handling and permissions — Correct account ID type casting and upda |
| 🟡 | `f9f5c148f` | 2026-04-09 | Backend | Observability / Sentry / OTLP | Improve system stability by resolving startup errors and refining observability configurations — Res |
| 🟡 | `f0d3483ad` | 2026-04-09 | Backend | Backend (genérico) | feat(backend): Sprint 2 — Talent Pool REST API (9 endpoints) — Models: |
| 🟡 | `37e623db6` | 2026-04-09 | Backend | Backend (libs) | Add talent pool models for candidate management — Add database models for TalentPool and TalentPoolC |
| 🟢 | `34eba75bf` | 2026-04-09 | Frontend (api/util) | UX / Mockups | Add a new component for ElevenLabs funnel to the mockup sandbox — Update `mockup-components.ts` to i |
| 🔴 | `1c0fc21b6` | 2026-04-09 | Cross IA↔Front | §9 Security / Tenant guards | Task #94: Choose Your AI — LLM Config Integration (Wiring + Security + Frontend) — Full end-to-end i |
| 🟢 | `19989a377` | 2026-04-09 | Frontend (UI) | scope: unified-chat | fix(unified-chat): P1 — file attachment now sends via useCvScreening — - Integrated useCvScreening h |
| 🟢 | `d27479384` | 2026-04-09 | Frontend (UI) | Unified Chat (FE) | Improve chat interface by hiding the floating bubble and fixing scrollbars — Switch from useEffect t |
| 🔴 | `ed0c6a466` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Add secure management for AI model API keys and providers — Integrate AI model provider management w |
| 🟡 | `0dc2ab41e` | 2026-04-09 | Frontend (UI) | scope: unified-chat | fix(unified-chat): Sprint 1 — eliminate ALL mock buttons, wire real integrations — 7 MOCK buttons no |
| 🟡 | `aa4dcd285` | 2026-04-09 | Frontend (UI) | FE libs / utils | Improve chat message formatting to display rich content correctly — Integrate the 'marked' library t |
| 🟢 | `2984d7d66` | 2026-04-09 | Frontend (UI) | Unified Chat (FE) | Allow fullscreen chat to render even when sidebar is closed — Modify the rendering logic in UnifiedC |
| 🟡 | `b67941448` | 2026-04-09 | Backend | Scheduling / Calendar (PR-CAL) | Fix issues with creating agents and scheduling interviews — Update Pydantic schema for `is_synced_to |
| 🟢 | `477a5577a` | 2026-04-09 | Frontend (UI) | Kanban (vagas) | Fix component display names and improve conditional logic — Resolve ESLint errors by adding display  |
| 🟡 | `a17d35ffd` | 2026-04-09 | Frontend (UI) | Bridge React→Vue | feat(unified-chat): Phase 6 — Deprecate old chats, add InlineChatBridge — - Created InlineChatBridge |
| 🟢 | `e485d9b42` | 2026-04-09 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase 5 — Universal scope + Navigation hints — Backend: |
| 🟡 | `b4823740d` | 2026-04-09 | IA | Backend Services (BE) | Add universal scope for tool permissions and update dependencies — Update `tool_permissions.yaml` to |
| 🔴 | `65122342a` | 2026-04-09 | Cross IA↔Front | §14 BYOK + LLM Factory | feat: complete LLM Factory migration — zero direct SDK imports outside providers/ — ## Summary |
| 🟢 | `10c37071e` | 2026-04-09 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase 4 — Task Context Bar integration — - SwitchTaskModal connected to UnifiedC |
| 🟢 | `aab86a1f7` | 2026-04-09 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase 3 — Split View + HITL in all modes — - DynamicContextPanel renders inside  |
| 🟢 | `de4811f97` | 2026-04-09 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase 2 — Fullscreen mode replaces legacy ChatPage — - ChatPageFullscreen wraps  |
| 🟡 | `30e7780fa` | 2026-04-09 | Backend | Compliance / LGPD / EU AI Act | Add reverse API for Rails to consume AI and compliance data — Introduces the `rails-sync` API with e |
| 🟢 | `4e5b572f6` | 2026-04-09 | Frontend (UI) | scope: unified-chat | fix(unified-chat): eliminate double bubble, single source of truth — - DashboardChatPanel returns nu |
| 🟢 | `c72d92a45` | 2026-04-09 | Frontend (UI) | scope: unified-chat | feat(unified-chat): Phase 1 — Replit-style inline sidebar — - DashboardChatPanel renders UnifiedChat |
| 🟢 | `82d6992ed` | 2026-04-09 | Frontend (UI) | scope: unified-chat | fix(unified-chat): restore hasInlineChat check and LiaSuperPrompt — - Hide UnifiedChat when ChatPage |
| 🔴 | `0bd4eb8e5` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Migrate all frontend API routes to use FastAPI and improve categories endpoint — Update backend targ |
| 🟢 | `31f811f35` | 2026-04-09 | Frontend (UI) | scope: unified-chat | fix(unified-chat): implement handleNewChat, add plus menu, persist mode, fix TS types — - handleNewC |
| 🟡 | `48b38e776` | 2026-04-09 | Frontend (UI) | Unified Chat (FE) | Implement a unified chat interface with multiple display modes — Replace the existing LiaFloat condi |
| 🟢 | `29d23937d` | 2026-04-09 | Docs | Docs / Configuration | Update production readiness audit with comparative analysis and new structure — Refactors section 24 |
| 🟢 | `68462a1f7` | 2026-04-09 | Docs | Compliance / LGPD / EU AI Act | Update AI layer evaluation with detailed audit findings — Enhance DEPLOY_GUIDE.md by updating the AI |
| 🟢 | `dcaf62128` | 2026-04-09 | Docs | Skills / canonical-fix | Add detailed technical specification for skills inference and adjacency — Creates the `docs/specs/sk |
| 🟢 | `624890507` | 2026-04-09 | Docs | §1 Teams Integration | DEPLOY_GUIDE.md: Add 8 new audit sections (24.11-24.18) — Expanded the production readiness audit fr |
| 🟢 | `4c8f6c71b` | 2026-04-09 | Docs | §1 Teams Integration | DEPLOY_GUIDE.md: Add 8 new audit sections (24.11-24.18) — Expanded the production readiness audit fr |
| 🟢 | `2704aac3f` | 2026-04-09 | Docs | §14 BYOK + LLM Factory | Add detailed audit findings and a prioritized roadmap to the deployment guide — Appends Section 24 t |
| 🟢 | `400b336d3` | 2026-04-09 | Docs | scope: deploy-guide | docs(DEPLOY_GUIDE): complete audit update — Rails as opt-in, FastAPI as source of truth — Updated DE |
| 🔴 | `ec389f991` | 2026-04-09 | Cross Back↔Front | Task #87 | fix: Task #87 code-review corrections — remove `as any`, prefer draft conversation_id — ## Issues fi |
| 🟡 | `41c848948` | 2026-04-09 | Frontend (UI) | scope: chat | feat(chat): Padronizar visual do chat LIA — avatar, bubble, fonte (Task #88) — ## Objetivo |
| 🟡 | `abe881d67` | 2026-04-09 | Outro | Mockup Sandbox (artefato gerado) | Update mock component definitions for weekly digest and report tabs |
| 🟡 | `7c3ee30b3` | 2026-04-09 | Frontend (UI) | §15 WSI | task-86: Polish Chat LIA — Badges e Estado de Processamento — ## Changes Made |
| 🟡 | `d4757d2ae` | 2026-04-09 | Backend | FastAPI v1 endpoints | Improve data access for sourcing agents — Replace getattr calls with direct attribute access for com |
| 🟡 | `e588274d4` | 2026-04-09 | Backend | §6 Chat Unificado / Funil | fix: resolve Funil de Talentos hydration mismatch + fix backend attribute access — Frontend (root ca |
| 🔴 | `a935f1f69` | 2026-04-09 | Cross Back↔Front | §6 Chat Unificado / Funil | fix: resolve Funil de Talentos hydration mismatch causing infinite loading state — Root cause: Radix |
| 🟡 | `82011d72a` | 2026-04-09 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `c802d7107` | 2026-04-09 | Frontend (UI) | §9 Security / Tenant guards | revert: restore secure:true sameSite:none for cookies (HTTPS via Replit proxy) — SameSite=lax breaks |
| 🟢 | `6e4700c14` | 2026-04-09 | Frontend (UI) | Configurações (hub) | fix: cookie settings for session and refresh routes (secure: false, sameSite: lax) — Same fix as mid |
| 🟢 | `41f015c0a` | 2026-04-09 | Frontend (api/util) | Configurações (hub) | fix: dev-mode cookie settings (secure: false, sameSite: lax) for Replit environment — The middleware |
| 🟢 | `78d4dbf00` | 2026-04-09 | Frontend (UI) | Login UI (FE) | Allow users to remain logged out after signing out — Modify the login page and middleware to respect |
| 🟡 | `c63f580b8` | 2026-04-09 | Outro | Mockup Sandbox (artefato gerado) | Update component registration for mockups — Reorder module imports in `mockup-components.ts` to grou |
| 🟡 | `88654d044` | 2026-04-09 | Backend | DevOps / CI | task-84: Alinhar DEPLOY_GUIDE.md com código real + remover AWS — Tarefa original: Alinhar DEPLOY_GUI |
| 🟢 | `ba24f21dd` | 2026-04-09 | Frontend (UI) | Frontend (componentes diversos) | Update page titles to remove icons and align with design standards — Removes icons from page titles  |
| 🟢 | `548bbb150` | 2026-04-09 | Frontend (api/util) | Design System v4.2.2 | Improve text readability by increasing font sizes across the platform — Adjust font size tokens in d |
| 🟢 | `62b5797f8` | 2026-04-09 | Frontend (api/util) | Voice / ElevenLabs / STT | Update text and border colors to match ElevenLabs design — Refactors CSS design tokens to align with |
| 🟢 | `95b3fb6ef` | 2026-04-09 | Frontend (UI) | Agent Studio (FE) | Update Agent Studio to use brain icons and remove unnecessary wrappers — Replaced Sparkles icons wit |
| 🟢 | `41efa41a5` | 2026-04-09 | Frontend (UI) | Agent Studio (FE) | Update the Agent Studio page with a modern, intuitive, and sophisticated design — Redesign the Agent |
| 🟢 | `59afe6b6e` | 2026-04-09 | Frontend (api/util) | §9 Security / Tenant guards | fix: resolve pipeline overview SQL type mismatch, restore cookie security, add proxy error handling  |
| 🔴 | `7d4b383ad` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | fix: resolve pipeline overview SQL type mismatch and add proxy error handling — - Fixed `character v |
| 🟢 | `eace9f4cc` | 2026-04-09 | Frontend (UI) | Configurações (hub) | Improve sidebar navigation and restore cookie security settings — Update sidebar component to use a  |
| 🟢 | `c283a2eea` | 2026-04-09 | Frontend (api/util) | Talent Funnel (FE) | feat: Dynamic sidebar sub-items for Talent Pools and Agents — Sidebar now shows active Talent Pools  |
| 🟢 | `184acc5a4` | 2026-04-09 | Frontend (UI) | Frontend (componentes diversos) | feat: Dynamic sidebar sub-items for Talent Pools and Agents — Sidebar now shows active Talent Pools  |
| 🟢 | `3abaf8aaf` | 2026-04-09 | Frontend (UI) | Frontend (componentes diversos) | Reorganize talent pools into a tab within the candidate funnel — Removes "Talent Pools" from the mai |
| 🟡 | `4f36afab2` | 2026-04-09 | Frontend (UI) | Chat UI (FE) | Replace all instances of the sparkles icon with the brain icon — Replaces the 'Sparkles' icon compon |
| 🟡 | `82e64b7af` | 2026-04-09 | Backend | Voice / ElevenLabs / STT | Fix error in voice interview state machine logic — Instantiate NotificationService before use in voi |
| 🟢 | `e19a44a23` | 2026-04-09 | Empty/merge | Talent Funnel (FE) | fix: restore TalentPoolPage.tsx from bad merge corruption — A previous merge incorrectly inserted Vo |
| 🟢 | `0dba74b2f` | 2026-04-09 | Frontend (UI) | Frontend (componentes diversos) | Fix errors in talent pool page display and functionality — Remove incorrectly placed VoiceScreeningB |
| 🟢 | `37141c08b` | 2026-04-09 | Empty/merge | (Auto-commit Replit) | resolve merge conflicts — accept remote |
| 🟢 | `a0116c89c` | 2026-04-09 | Docs | Docs / Screenshots | Update main application chat screenshot — Update the existing screenshot for the main application's  |
| 🟢 | `06f5391e2` | 2026-04-09 | Docs | Task #83 | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 17 pages, 13+ sha |
| 🟡 | `b3a685d50` | 2026-04-08 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat: Phase 8.1+8.2 — 4 new domains + 22 tools + Pearch hybrid + router update — 8.1 — Orchestrator  |
| 🟢 | `be98d2dd3` | 2026-04-09 | Docs | Task #83 | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 13 pages, 13+ sha |
| 🟢 | `ea280ed2e` | 2026-04-09 | Docs | Task #83 | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 7 pages, 13+ shar |
| 🟡 | `442e91d6c` | 2026-04-09 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `edfc3b89a` | 2026-04-09 | Outro | Mockup Sandbox (artefato gerado) | Add new component for ElevenLabs funnel analysis — Update mockup-components.ts to include the new Fu |
| 🟢 | `bae244281` | 2026-04-09 | Docs | Task #82 | docs: update DEPLOY_GUIDE.md with 7 integration gaps (task #82) — ## What was done |
| 🟢 | `359a2c5a7` | 2026-04-09 | Docs | Voice / ElevenLabs / STT | Create a design diagnostic document comparing LIA to ElevenLabs style — Create a markdown document d |
| 🔴 | `1a65de885` | 2026-04-09 | Cross Back↔Front | Backend Proxy Routes (FE) | Fix issues preventing the Agent Studio page from loading correctly — Address backend startup issues, |
| 🔴 | `6259655b3` | 2026-04-08 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Improve agent studio page loading by handling API errors gracefully — Fix TypeError in AgentStudioPa |
| 🟡 | `5e378fff5` | 2026-04-08 | Outro | Mockup Sandbox (artefato gerado) | Add new designs to the sandbox for testing purposes — Update mockup-components.ts to include new moc |
| 🔴 | `b6cfd672d` | 2026-04-08 | Cross Back↔Front | scope: #81 | feat(#81): Sidebar sections + Pipeline Overview page (v4 final) — ## Summary |
| 🟢 | `cf6b3fde2` | 2026-04-08 | Frontend (UI) | Kanban (vagas) | fix: wire remaining 3 orphan components — all 17 issues resolved — 7.3.3 VagaProgressBar: |
| 🟢 | `1ff1fc6d0` | 2026-04-08 | Frontend (UI) | Frontend (componentes diversos) | Apply new canvas design to the chat interface and suggestion cards — Update the chat page UI to inco |
| 🔴 | `0fbb45e92` | 2026-04-08 | Cross Back↔Front | §15 WSI | fix: Phase 7 hardening — all 17 audit issues resolved — CRITICAL FastAPI fixes: |
| 🟡 | `2ee1a29df` | 2026-04-08 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `cd704ed67` | 2026-04-08 | Cross Back↔Front | FastAPI v1 endpoints | fix: resolve all implementation gaps from code review — Models: |
| 🟡 | `4ef8513d6` | 2026-04-08 | Outro | Mockup Sandbox (artefato gerado) | Add three distinct interface variations optimizing for clarity, interaction, and accessibility — Int |
| 🟡 | `9440bc655` | 2026-04-08 | Backend | Mockup Sandbox (artefato gerado) | Refine chat interface with improved spacing and card distinctiveness — Adds two new variations of th |
| 🟢 | `b8363f545` | 2026-04-08 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Improve chat greeting appearance and candidate retrieval reliability — Update chat greeting font wei |
| 🟢 | `d97173d15` | 2026-04-08 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Improve text colors and spacing in the chat interface — Update text colors to be darker and add spac |
| 🟢 | `6bbd272e7` | 2026-04-08 | Frontend (UI) | (Auto-commit Replit) | Restored to '951e4df07921f86765a8c0c03bf0bb59cc23bc0c' — Replit-Restored-To: 951e4df07921f86765a8c0c |
| 🟢 | `aed193331` | 2026-04-08 | Frontend (UI) | Frontend (componentes diversos) | Standardize text appearance and improve icon sizing in LIA chat interface — Updates font size, color |
| 🟢 | `951e4df07` | 2026-04-08 | Frontend (UI) | §7 WorkflowRail UX | Safely handle empty or error responses from an API endpoint — Modify `useWorkflowRail.ts` to add che |
| 🔴 | `76e081686` | 2026-04-08 | Cross Back↔Front | §4 Rail Features — Rail A | Update application styling and fix component rendering issues — Standardize typography and fix serve |
| 🟢 | `6ccaf4826` | 2026-04-08 | Frontend (UI) | §7 WorkflowRail UX | fix: add 'use client' to useWorkflowRail.ts (Next.js client component) |
| 🔴 | `714711e5c` | 2026-04-08 | Cross Back↔Front | §7 WorkflowRail UX | feat: integrate Phase 6 — auth, sidebar, pages, WorkflowRail — Item 1 — Auth: |
| 🔴 | `2e0c4c9d1` | 2026-04-08 | Cross IA↔Front | §7 WorkflowRail UX | feat: Phase 6 — Agent Studio, Talent Pools, Workflow Rail, Digital Twins — 57 new files across lia-a |
| 🟢 | `9c788f782` | 2026-04-08 | Frontend (UI) | UI Components (FE library) | Align chat interface appearance with design system standards — Update chat page, prompt suggestions  |
| 🟢 | `b51d5a500` | 2026-04-08 | Docs | Mockup Sandbox (artefato gerado) | Add new components for weekly digest notifications and chat — Update generated mock component map to |
| 🔴 | `ea09abcc3` | 2026-04-08 | Cross Back↔Front | Task #78 | feat: safe URL encoding for Microsoft OAuth auth URL + adapter interface fix — Final polish for Task |
| 🔴 | `2003c41d5` | 2026-04-08 | Cross Back↔Front | Kanban (vagas) | feat(task-77): A/B Testing UI, Kanban suggestions API, chat suggestions, credit balance fix — ## Tas |
| 🟡 | `2a60c61a3` | 2026-04-08 | Backend | scope: rails-integration | docs(rails-integration): clarify RAILS_ENABLED opt-in semantics in reference doc — RAILS_API_INTEGRA |
| 🟢 | `88c22b955` | 2026-04-08 | Frontend (UI) | Mockup Sandbox (artefato gerado) | Improve candidate search functionality by using the correct backend endpoint — Fixes the candidate s |
| 🟡 | `d1d0df65a` | 2026-04-08 | Frontend (UI) | Backend Proxy Routes (FE) | Fix Expand to Global bug, LIA sidebar overflow, and improve Pearch unavailability handling — 1. Auth |
| 🔴 | `c253385e1` | 2026-04-08 | Cross Back↔Front | Candidates (FE pages) | Improve candidate search functionality by splitting multi-word queries — Fixes candidate search to c |
| 🟡 | `e94d14b72` | 2026-04-08 | Outro | Mockup Sandbox (artefato gerado) | Add components for weekly digest notifications and chat — Add new mock components for BellNotificati |
| 🔴 | `9ce15b138` | 2026-04-08 | Cross Back↔Front | §9 Security / Tenant guards | fix(backend): Task #75 — Backend Deploy Readiness (OpenAPI, Shims, Secrets, Celery, Security) — ## S |
| 🟡 | `f88ee76f1` | 2026-04-08 | Frontend (UI) | Task #74 | Task #74: Frontend Deploy Readiness — Fallbacks, WebSocket, Headers e E2E — Changes implemented: |
| 🔴 | `4b4f44771` | 2026-04-08 | Cross Back↔Front | §9 Security / Tenant guards | Improve security and user management by isolating tenant data — Enhance multi-tenancy by isolating u |
| 🟢 | `a6630744b` | 2026-04-08 | Frontend (UI) | Stores (FE Zustand) | Improve user authentication by injecting data server-side — Update layout to inject user data server |
| 🟡 | `2bf7cfa7f` | 2026-04-08 | Frontend (UI) | Tests (BE unit/integration) | Bypass client-side authentication fetch by injecting user data from server — Implement server-side d |
| 🟢 | `437afc8a8` | 2026-04-08 | Testes | Wizard (geral) | Update tests for wizard step service to include shared components — Refactor unit tests for wizard_s |
| 🟡 | `8875c6747` | 2026-04-08 | Frontend (UI) | Tests (BE unit/integration) | Improve login flow and remove development console logs — Update login page to redirect in developmen |
| 🟢 | `9e74c8350` | 2026-04-08 | Frontend (UI) | Task #73 | fix: Corrigir scroll travado no chat (Task #73) — Problema: O useEffect de auto-scroll em useChatMes |
| 🟡 | `836bd3971` | 2026-04-08 | Frontend (UI) | Data fetching / SWR | Add resilience and retry logic to job data fetching — Introduce retry mechanism for `listJobVacancie |
| 🟢 | `85d504a78` | 2026-04-08 | Frontend (api/util) | Task #72 | task: Clone repository to wedocc2026 GitHub account (Task #72) — Created a mirror of the project rep |
| 🔴 | `7634b0b4b` | 2026-04-08 | Cross Back↔Front | Configurações (hub) | Add fairness and compliance dashboard to settings and improve dev mode authentication — Integrate th |
| 🟢 | `28ab5fb97` | 2026-04-08 | Frontend (UI) | Jobs (FE pages) | Set default tab to show job listings immediately — Update default filter state in the jobs page hook |
| 🟡 | `053b7d0b5` | 2026-04-08 | Cross IA↔Back | §9 Security / Tenant guards | Fix issues with job vacancy display and improve input security — Updates response schemas for job va |
| 🔴 | `e27f8342e` | 2026-04-08 | Cross Back↔Front | Chat UI (FE) | Add filtering and sorting to candidate list and fix total count — Update backend API to support seni |
| 🔴 | `0b128a093` | 2026-04-08 | Frontend (UI) | Backend Proxy Routes (FE) | Require authentication for most API backend proxy routes — Changed the `auth` property from `false`  |
| 🟡 | `05db9825a` | 2026-04-08 | Backend | Scripts / CLI | Add a new hiring manager user and update vacancy status — Update the seed data script to add a new u |
| 🟡 | `5f62e11e4` | 2026-04-08 | Backend | Task #71 | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scri |
| 🟡 | `3716d651c` | 2026-04-08 | Backend | Task #71 | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scri |
| 🟡 | `3b83fbc21` | 2026-04-08 | Backend | Task #71 | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scri |
| 🟡 | `e60f50780` | 2026-04-08 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `b84beae5a` | 2026-04-08 | Frontend (UI) | Chat UI (FE) | Update middleware to bypass redirects for authentication — Rewrite the middleware to directly fetch  |
| 🔴 | `4607cfe03` | 2026-04-08 | Frontend (UI) | Configurações (hub) | Update cookie settings to enable cross-site iframe compatibility — Adjusted cookie configurations in |
| 🔴 | `7c76bd7ac` | 2026-04-08 | Frontend (UI) | §9 Security / Tenant guards | Improve security and reliability of authentication and iframe embedding — Update security headers to |
| 🔴 | `ac0d1d417` | 2026-04-08 | Frontend (UI) | Backend Proxy Routes (FE) | Refactor API routes to use a new proxy handler utility — Replace manual fetch requests in numerous A |
| 🔴 | `287ba5ad5` | 2026-04-08 | Cross IA↔Front | Kanban (vagas) | Improve authentication, error handling, and user experience — Update authentication flow to correctl |
| 🟡 | `e5600c8e6` | 2026-04-08 | Backend | Wizard (geral) | refactor: DRY wizard_step_service — dict mapping, confidence helper, loop patterns (-97 lines) — - R |
| 🟡 | `b7bad168a` | 2026-04-08 | Backend | Wizard (geral) | refactor: convert remaining 13 tool registries to @tool_handler decorator (-351 lines) — Converted:  |
| 🟡 | `2a95d4360` | 2026-04-08 | Frontend (UI) | Triagem (módulo) | refactor: decompose 4 large pages + 4 large hooks into focused modules — Pages decomposed (page.tsx  |
| 🟡 | `edab76285` | 2026-04-08 | Backend | Communication domain (BE) | refactor: extract inline models and DRY communication_service (-351 lines) — - Extract 4 SQLAlchemy  |
| 🔴 | `5b914d413` | 2026-04-08 | Frontend (UI) | Backend Proxy Routes (FE) | refactor: create shared proxy handler and convert 55 API routes (-1800 lines) — Created src/lib/api/ |
| 🟡 | `eda0314ca` | 2026-04-08 | Backend | Kanban (vagas) | refactor: code optimization — extract static data to JSON, add tool_handler decorator, DRY event han |
| 🟡 | `ccdedc141` | 2026-04-08 | Outro | Refactor / Cleanup | Fix issue causing users to see a blank page and ensure proper data display — Add missing database co |
| 🟡 | `61560e0b8` | 2026-04-08 | IA | Task #69 | Task #69: Complete Platform Audit + Fix DB columns + Fix import — 1. Full platform audit - report at |
| 🟡 | `d53081703` | 2026-04-08 | Backend | Task #69 | Task #69: Complete Platform Audit + Fix DB columns + Fix import — 1. Full platform audit - report at |
| 🟢 | `f3e74c1d2` | 2026-04-08 | Empty/merge | Task #69 | Task #69: Complete Platform Audit + Fix email_encrypted DB column — 1. Full platform audit completed |
| 🟡 | `d8f4673fe` | 2026-04-08 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `0e523f63a` | 2026-04-07 | Cross IA↔Back | scope: tests | fix(tests): fix Redis isolation, agent_health tests, shim exports, lia_config import — - Fix _make_s |
| 🟡 | `5910b3db6` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update API client endpoints and registration for better organization — Refactor API routes in `route |
| 🟡 | `3ee781e16` | 2026-04-07 | Backend | Wizard (geral) | fix(tests): fix private exports, lia_config, job_report, and wizard imports — - Add _SCIPY_AVAILABLE |
| 🔴 | `0427d7f0e` | 2026-04-07 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Add new components and update job vacancy analytics functionality — Adds new mockup components and u |
| 🟡 | `dee51c2cb` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `9c7113453` | 2026-04-07 | Backend | Task #68 | fix: repair Alembic migration chain and apply migration 060 to fix login — ## Original Task |
| 🟡 | `cbfecbc59` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `68212c8f7` | 2026-04-07 | Backend | scope: tests | fix(tests): fix agent domain_name setter, function signatures, and missing exports — - Add domain_na |
| 🔴 | `1dddecde9` | 2026-04-07 | Cross Back↔Front | §15 WSI | Add detailed report view for WSI assessments and improve candidate resolution — Refactor candidate r |
| 🟡 | `534419a82` | 2026-04-07 | Backend | UX / Mockups | Remove unused chat layout mockups and update job vacancy configurations — Removes various chat layou |
| 🟡 | `b5f9ac1ff` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Remove system architecture diagram mockups and update component registration — Remove the 'arch-comp |
| 🟡 | `f80260f11` | 2026-04-07 | Backend | scope: tests | fix(tests): fix 12 categories of unit test failures — private imports and moved modules — - Add _get |
| 🔴 | `220094926` | 2026-04-07 | Cross Back↔Front | Backend Proxy Routes (FE) | Standardize backend URLs and fix critical deployment issues — Correctly configure backend URLs acros |
| 🟡 | `19db0abdd` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update documentation and code to reflect current system configurations — This commit updates the DEP |
| 🟡 | `3b060add7` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update code to use dependency injection for service classes — Refactor multiple API endpoints to uti |
| 🟡 | `6c36c135d` | 2026-04-07 | IA | §15 WSI | fix(tests/wsi): fix WSI unit test failures - part 2 — - wsi_interview_graph: add eligibility_score f |
| 🟡 | `9f778183e` | 2026-04-07 | Backend | §15 WSI | fix(tests/wsi): fix WSI unit test failures across 6 test groups — - wsi6_bigfive: update lambda/asyn |
| 🔴 | `ca4d6f656` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Refactor service imports and move WebSocket manager — Update service imports to use dependency injec |
| 🟡 | `edff3aee3` | 2026-04-07 | Cross IA↔Back | scope: tests | fix(tests): fix Redis mock injection in token_budget, toon, and hitl services — - Promote app/servic |
| 🟢 | `8ed5458f3` | 2026-04-07 | Docs | §9 Security / Tenant guards | Update deployment guide with new environment variables and security notes — Update DEPLOY_GUIDE.md t |
| 🟢 | `6e37900d4` | 2026-04-07 | Testes | Tests (FE e2e) | Improve testing setup and documentation for local development — Update Playwright configuration and  |
| 🟢 | `70863bb78` | 2026-04-07 | Frontend (api/util) | Backend (refactor Phase 2+) | docs+refactor(phase2): complete Phase 2 repo extraction — - 215 API files clean (0 direct DB calls) |
| 🔴 | `49d6b02a1` | 2026-04-07 | Cross IA↔Front | DevOps / Deploy (Docker/GCP) | Update application configuration and Dockerfile for standalone deployment — Refactors several Python |
| 🟡 | `d10f69696` | 2026-04-07 | Backend | FastAPI v1 endpoints | Refactor data retrieval to use dedicated repositories for learning patterns and LLM configurations — |
| 🟡 | `113d065f2` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Refactor data access layers to improve code organization and maintainability — Extract various data  |
| 🟡 | `92e64405f` | 2026-04-07 | Cross IA↔Back | §15 WSI | refactor(phase2): extract wsi/cv_screening/comms API DB calls to repos — - WsiRepository: +7 methods |
| 🟡 | `3b6caaaf4` | 2026-04-07 | Backend | scope: phase2 | refactor(phase2): extract agent_templates/ai_consumption/shared_searches DB calls to repositories —  |
| 🟡 | `c714b88c6` | 2026-04-07 | Backend | scope: phase2 | refactor(phase2): extract interview_analysis, communication_matrix, suggestions, experience_highligh |
| 🟡 | `ef66d775d` | 2026-04-07 | Backend | Configurações (hub) | refactor(phase2): extract short_lists, policies, benefits, settings_progress DB calls to repositorie |
| 🟡 | `88aeae88e` | 2026-04-07 | Backend | §1 Teams Integration | refactor(phase2): extract teams/webhooks/screening_questions direct DB calls to repositories — - tea |
| 🟢 | `385dd7c8e` | 2026-04-07 | Docs | Docs / Configuration | Expand product development workflow to include client feedback and bug fixes — Adds a comprehensive  |
| 🟡 | `e2c2b0db3` | 2026-04-07 | Backend | Backend (shared) | Add cross-cutting service descriptions for agent health and tenant context — Add comments to agent_h |
| 🟢 | `293e88e6b` | 2026-04-07 | Docs | §9 Security / Tenant guards | Add client onboarding, AI workflow, and integration status sections — Adds new sections to the DEPLO |
| 🔴 | `5b9c855ca` | 2026-04-07 | Cross IA↔Back | scope: phase2 | refactor(phase2): extract API direct DB calls to repositories — batch 1 — Fully extracted (DB calls  |
| 🟢 | `cd4710d07` | 2026-04-07 | Docs | Docs / Configuration | Update deployment guide with current environment and limitations — Modify DEPLOY_GUIDE.md to reflect |
| 🟢 | `fd2ca73f2` | 2026-04-07 | Docs | Docs / Configuration | Clarify team ownership of development flow and environment — Update DEPLOY_GUIDE.md to redefine role |
| 🟡 | `523a48110` | 2026-04-07 | Backend | Backend (shared) | Expand deployment guide with integration details and readiness assessments — Update DEPLOY_GUIDE.md  |
| 🟡 | `c84a47ab0` | 2026-04-07 | Backend | §15 WSI | refactor(phase2): classify remaining UNCLEAR API files and wsi repo extraction — - Annotated 16 more |
| 🟡 | `1445b1707` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update system to handle Rails-deprecated entities and fix import issues — Introduces a RailsAdapter  |
| 🟢 | `df7f53768` | 2026-04-07 | Docs | Docs / Refactor | docs: update REFACTOR_PLAN after Phase 2+3+4B |
| 🔴 | `81889e02a` | 2026-04-07 | Cross IA↔Back | scope: phase4b | feat(phase4b): batch 2 — migrate 73 AI-permanent services to domain layer — Migrated services (73 to |
| 🟡 | `bf6970eff` | 2026-04-07 | Cross IA↔Back | scope: phase2 | fix(phase2): classify API files as Rails-owned vs FastAPI-owned — - Annotated 2 API files as RAILS-D |
| 🟡 | `5e89b5546` | 2026-04-07 | Backend | scope: phase4b | feat(phase4b): add backwards-compat shims in shared/services for migrated domain services — - compen |
| 🟡 | `8516252cb` | 2026-04-07 | Backend | Scripts / CLI | Update GitHub token retrieval to support multiple environment variables — Refactor GitHub token retr |
| 🔴 | `4adf6561f` | 2026-04-07 | Cross IA↔Back | scope: phase3 | fix(phase3): replace app.models imports with lia_models in service files — - Case A: 128 files chang |
| 🟢 | `7e5560b6c` | 2026-04-07 | Docs | Docs / Refactor | docs: revisit REFACTOR_PLAN with Rails-aware corrections — - Add Rails Migration Boundary section: e |
| 🟡 | `81c352abb` | 2026-04-07 | Backend | Policy / Job Creation | Fix error in backend policy engine rule loading — Corrected a NameError in `main.py` by changing dic |
| 🟡 | `ba43cd5c7` | 2026-04-07 | Cross IA↔Back | scope: ddd | feat(ddd): Phase 4 DDD migration — credit_service and rails_adapter to domain layer — - Move credit_ |
| 🔴 | `879527074` | 2026-04-07 | Frontend (UI) | Wizard (geral) | fix: complete recruitment-stages decomposition and address all code review findings — Changes from 4 |
| 🟡 | `3e1546510` | 2026-04-07 | Backend | Backend (shared) | fix: Phase 3 completion — encryption package fix + Phase 3 tracker update — - app/shared/encryption/ |
| 🟡 | `43a6d3ead` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Add new component for Eleven Labs funnel to the project — Update `mockup-components.ts` to include t |
| 🟡 | `cf6d87bc0` | 2026-04-07 | Cross IA↔Back | §15 WSI | task-60: Prompts Unificados & Infra de Evals — ## Summary |
| 🟡 | `829a83889` | 2026-04-07 | Backend | Compliance / LGPD / EU AI Act | feat(compliance): close LGPD audit gaps #63 — full codebase email-lookup migration — Implements all  |
| 🟡 | `e63365ca3` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include all WSI report tabs — Update the `mockup-components.ts` file to  |
| 🟡 | `c73957bf8` | 2026-04-07 | Backend | Task #61 | Task #61: Backend Code Quality and API Contracts — COMPLETE — All objectives met. 116 tests passing. |
| 🟡 | `7a2482c82` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `561e99c47` | 2026-04-07 | Cross IA↔Back | Voice / ElevenLabs / STT | feat(voice): Go-Live Deepgram STT & OpenMic.ai — Task #65 — Implements full production-ready integra |
| 🟡 | `8cb2b7286` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `b43ce6c34` | 2026-04-07 | Backend | scope: sourcing | feat(sourcing): Task-59 — 6 Sub-agentes Granulares (FINAL + APPROVED_WITH_COMMENTS resolvidos) — Tod |
| 🟡 | `88cc4c7a7` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `4652eaf17` | 2026-04-07 | Backend | §9 Security / Tenant guards | feat(security): Task #62 — Segurança Hardening Explícito — ## Summary |
| 🟡 | `2b25f6824` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `3a0212935` | 2026-04-07 | Backend | §1 Teams Integration | fix(task-64): Complete MS Teams adapter and WhatsApp native interactive buttons — MS Teams: |
| 🟡 | `26891a6bc` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `91f187afa` | 2026-04-07 | Cross IA↔Back | scope: autonomous | feat(autonomous): finalize Tier 6 — all reviews addressed, 59 tests passing — Task #58 (AutonomousRe |
| 🟡 | `bb3d4819d` | 2026-04-07 | Cross IA↔Back | scope: infra | feat(infra): Task #67 — Broker Abstraction Layer + Fix 15 Test Import Errors — ## Broker Abstraction |
| 🟡 | `a9d3ae4cb` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `51e654d09` | 2026-04-07 | Backend | §1 Teams Integration | Fix Teams message handling by allowing trailing slashes — Add explicit route registration for traili |
| 🟡 | `2d8607fcb` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Update component generation for visual parity and bug fixes — Update generated component map to incl |
| 🟢 | `bcf2fadb9` | 2026-04-07 | Frontend (UI) | Task #57 | feat: Remove balloon/background from LIA messages (Task #57) — ## Summary |
| 🟢 | `9203b3ce7` | 2026-04-07 | Frontend (UI) | scope: chat-lia | feat(chat-lia): visual parity with Design System (Task #56) — Aligns all visual tokens in LIA Chat t |
| 🔴 | `d110a2a22` | 2026-04-07 | Cross IA↔Front | Automations | Update chat and automation services for improved functionality — Refactors service dependencies and  |
| 🟢 | `bb0f280e0` | 2026-04-07 | Frontend (UI) | Chat UI (FE) | task(55): Reduzir fontes do chat LIA (placeholder e mensagens) — ## Original Task |
| 🟡 | `4a0e19f87` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update services to use dependency injection for CV parsing and search — Refactored the application t |
| 🟡 | `47c1a9ebd` | 2026-04-07 | Cross IA↔Back | §15 WSI | Update services to use dependency injection for feature flags and organization catalog — Refactor co |
| 🟡 | `d150fc368` | 2026-04-07 | Backend | Backend (shared) | Add dependency injection for feature flag service — Introduce a FastAPI dependency injection factory |
| 🟡 | `5e22af32e` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update the bot's connection to track user activity — Update the bot's event handling to include acti |
| 🟡 | `f736786ac` | 2026-04-07 | Backend | §15 WSI | Update how activity service is accessed for WSI screening invites — Refactor the instantiation of th |
| 🟡 | `f7892c897` | 2026-04-07 | Backend | FastAPI v1 endpoints | Integrate audit and activity logging into event handling — Refactor event handling and trigger logic |
| 🟡 | `708342fb3` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update activity service to use dependency injection — Refactor activity service instantiation to use |
| 🟡 | `7e1eede38` | 2026-04-07 | Outro | §1 Teams Integration | Update app package with correct Teams App ID — Updates the `botId` and `appId` in the `manifest.json |
| 🟡 | `b466d6185` | 2026-04-07 | Backend | §1 Teams Integration | Update activity retrieval to use a dedicated service layer — Refactor `activities.py` to utilize dep |
| 🟡 | `f4eec1cc5` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update services to use dependency injection for audit and activity logging — Refactor `AuditService` |
| 🟡 | `8c3761ed4` | 2026-04-07 | Outro | §1 Teams Integration | Update app icons and domain for improved Teams compatibility — Update color and outline icons to mee |
| 🟡 | `66abfc191` | 2026-04-07 | Backend | FastAPI v1 endpoints | Improve rubric evaluation by adding audit logging — Update rubric evaluation endpoint to include aud |
| 🟡 | `28cc4afda` | 2026-04-07 | Backend | §1 Teams Integration | Update application to use simplified Teams manifest for improved compatibility — Removes unnecessary |
| 🟡 | `e14655bc3` | 2026-04-07 | Outro | §1 Teams Integration | Update app icons to use the correct company logo — Regenerate the Teams app ZIP package with updated |
| 🟡 | `c1cb832aa` | 2026-04-07 | Backend | FastAPI v1 endpoints | Update audit service integration for approval requests — Refactor `approvals.py` to inject `AuditSer |
| 🟡 | `b47e48853` | 2026-04-07 | Backend | FastAPI v1 endpoints | Add audit service dependency to communication endpoints — Integrate AuditService dependency into sen |
| 🟡 | `f6c6a297b` | 2026-04-07 | Cross IA↔Back | FastAPI v1 endpoints | Update audit service to use dependency injection for consistency — Refactor the audit service import |
| 🟡 | `99906f8d2` | 2026-04-07 | Cross IA↔Back | §1 Teams Integration | Add dependency injection factories for service classes — Add FastAPI dependency injection factories  |
| 🟢 | `eccfda9ac` | 2026-04-07 | Docs | §1 Teams Integration | Update documentation with Microsoft Teams bot configuration details — Add Microsoft Teams bot config |
| 🟡 | `f30db4d04` | 2026-04-07 | Backend | §1 Teams Integration | Improve error logging for Teams communication issues — Add detailed logging for token claims and HTT |
| 🟡 | `3d04eea86` | 2026-04-07 | Backend | §1 Teams Integration | Separate Teams bot tenant ID from general Azure tenant ID — Introduce a new configuration setting `T |
| 🟡 | `eaee69704` | 2026-04-07 | Backend | §1 Teams Integration | Update bot to use tenant-specific token endpoint for authentication — Modify `teams_simple.py` to us |
| 🟡 | `02988e7a7` | 2026-04-07 | Backend | §1 Teams Integration | Fix error when sending messages to Teams by correcting URL formatting — Correctly format the messagi |
| 🟡 | `236f3964a` | 2026-04-07 | Backend | §1 Teams Integration | Update bot to use multi-tenant authentication endpoint — Modify the token acquisition logic in `team |
| 🔴 | `9e60ef7f7` | 2026-04-07 | Cross Back↔Front | Configurações (hub) | Add new API endpoints for company-specific settings and data management — Introduces new API routes  |
| 🟡 | `103cbac9a` | 2026-04-07 | Frontend (UI) | Candidates (FE pages) | Update system to better handle candidate data and improve UI elements — Refactors candidate data han |
| 🟡 | `fac14a777` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Add new components to the mockups for architecture comparison — Add entries for `EstadoAtual.tsx` an |
| 🔴 | `195642ec4` | 2026-04-07 | Cross Back↔Front | §1 Teams Integration | Update Teams bot authentication to use tenant-specific endpoint — Updates `teams_simple.py` to use t |
| 🟢 | `b0ff4498b` | 2026-04-07 | Frontend (UI) | Candidates (FE pages) | Update styling and type casting for candidate table columns — Adjust color definitions in lia-expand |
| 🔴 | `e8b7146f3` | 2026-04-07 | Cross Back↔Front | §1 Teams Integration | Improve Teams message handling by fixing timestamp parsing — Update teams.py to correctly parse and  |
| 🟡 | `56c317ca0` | 2026-04-07 | Backend | §1 Teams Integration | Update token validation to use multiple signing key sources — Modify `teams_auth.py` to support mult |
| 🟢 | `c369c7951` | 2026-04-07 | Frontend (UI) | Configurações (hub) | Update type assertions for improved data handling — Refactor type assertions in multiple components  |
| 🟢 | `5b36eacab` | 2026-04-07 | Frontend (UI) | Talent Funnel (FE) | Update date formatting to return empty string for null values — Modify formatDate and formatDateShor |
| 🟡 | `77a7627f6` | 2026-04-07 | Frontend (UI) | Expandable AI Prompt (FE) | Update application configuration and component types for improved functionality — Update `next.confi |
| 🟢 | `80e190bcd` | 2026-04-07 | Frontend (api/util) | DevOps / Deploy (Docker/GCP) | Update proxy to connect to the correct backend server — Corrected the hardcoded backend port in the  |
| 🟢 | `2ed8bf8b0` | 2026-04-07 | Frontend (UI) | Kanban (vagas) | Update type casting for candidate sub status |
| 🟢 | `73c64add3` | 2026-04-07 | Frontend (UI) | Configurações (hub) | Improve display of default company settings in job editing — Update conditional rendering logic in J |
| 🟡 | `aa94d9d29` | 2026-04-07 | Frontend (UI) | Kanban (vagas) | Update job listing and kanban board components and hooks — Refactor various components and hooks wit |
| 🟡 | `67eb75ac8` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Add ElevenLabs funnel component to mockups — Update mockup-components.ts to include the FunilElevenL |
| 🔴 | `4af1a779f` | 2026-04-07 | Cross Back↔Front | Task #53 | Task #53: Add 10 critical behavioral tests + raise coverage gates — ## Summary |
| 🟡 | `cb3b79927` | 2026-04-07 | Outro | Mockup Sandbox (artefato gerado) | Add new mockups for ElevenLabs funnel and WSI report sections — Update component registration in moc |
| 🔴 | `d7462265a` | 2026-04-07 | Cross IA↔Front | Docs (geral) | Merged changes from vs4jplti/main — Replit-Task-Id: a94aa833-ba88-4578-847d-d41212bee642 |
| 🟡 | `b7b29ae37` | 2026-04-07 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `4add6c879` | 2026-04-06 | Frontend (UI) | Candidates (FE pages) | Update function to properly set search prompt value — Update the `setLiaPromptValue` function to cor |
| 🟢 | `a4c88add8` | 2026-04-06 | Frontend (UI) | Candidates (FE pages) | Update candidate profile and search result views with type safety — Refactor `CandidatePageProfileTa |
| 🟡 | `0e11445af` | 2026-04-06 | Frontend (UI) | Task #52 | feat(task-52): Isolamento de conversas entre prompts — conversa limpa ao trocar de prompt — ## Summa |
| 🟡 | `f8ea7b63b` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `e467eab71` | 2026-04-06 | Frontend (UI) | Task #51 | fix: redirect to /login/welcome after email/password login (Task #51) — ## Problem |
| 🟡 | `c1cbfa812` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `820e3a54e` | 2026-04-06 | Frontend (UI) | Talent Funnel (FE) | Update candidate data handling and job configuration — Modify default values for candidate work mode |
| 🟢 | `0d1660296` | 2026-04-06 | Testes | Task #50 | Task #50: Frontend component tests for critical flows — Added/extended 13 test files with 130+ new t |
| 🟡 | `d25359132` | 2026-04-06 | Frontend (UI) | Task #50 | Task #50: Frontend component tests for critical flows — Added/extended 13 test files with 130+ new t |
| 🟡 | `9dd1a357d` | 2026-04-06 | Frontend (UI) | Task #50 | Task #50: Frontend component tests for critical flows — Added 11 new test files covering 4 Zustand s |
| 🟢 | `ce2b14b4b` | 2026-04-06 | Frontend (UI) | Task #50 | Task #50: Frontend component tests for critical flows — Added 10 new test files covering 4 Zustand s |
| 🟡 | `5507f8e3f` | 2026-04-06 | Frontend (UI) | Task #50 | Task #50: Frontend component tests for critical flows — Added 7 new test files covering 4 Zustand st |
| 🟢 | `be6c7db17` | 2026-04-06 | Frontend (UI) | Candidates (FE pages) | Improve candidate search functionality and filtering accuracy — Refactor search hooks to correctly h |
| 🟡 | `e0e0dee7b` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `e6059dfef` | 2026-04-06 | Frontend (UI) | Candidates (FE pages) | Update candidate search and message handling logic — Add ChatMessage type to various candidate-relat |
| 🟡 | `d4a685000` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping to include weekly digest and WSI report tabs — Updates the `mockup-componen |
| 🟢 | `c803f56c4` | 2026-04-06 | Frontend (UI) | Task #49 | Task #49: Corrigir Limpar Chat e Fonte dos Balões — Fixes two bugs in LIA chat: |
| 🟡 | `7ddd5a092` | 2026-04-06 | Backend | Task #48 | Task #48: Auditoria e Correção de Todos os Prompts LIA — Paridade de Capacidades — Fix LIA pipeline  |
| 🟡 | `b238a18c9` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `17a065bc2` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate credits.py to CreditsRepository |
| 🟡 | `dea8da8ef` | 2026-04-06 | Backend | scope: guards | chore(guards): remove admin.py from PENDING_MIGRATION (now 137) |
| 🟡 | `66ba9165c` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate admin.py to AdminRepository |
| 🟡 | `f4ba91f19` | 2026-04-06 | Backend | scope: guards | chore(guards): remove email_templates.py from PENDING_MIGRATION (now 138) |
| 🟡 | `675c2b1d6` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate email_templates.py to EmailTemplatesRepository |
| 🟡 | `5de28d384` | 2026-04-06 | Backend | scope: phase2 | fix(phase2): clean residual SQLAlchemy imports in migrated controllers + migrate agent_memory.py — - |
| 🟡 | `a28bc33a8` | 2026-04-06 | Backend | Configurações (hub) | Fix errors in job creation notifications and repository settings — Corrects syntax errors in notific |
| 🟡 | `00168f577` | 2026-04-06 | Backend | Configurações (hub) | Update email template repository and dependencies for better data handling — Add new dependency inje |
| 🟡 | `73fc18446` | 2026-04-06 | Backend | scope: guards | chore(guards): remove email.py from PENDING_MIGRATION (now 139) |
| 🟡 | `b7c778b37` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate email.py to EmailRepository |
| 🟡 | `263171212` | 2026-04-06 | Backend | scope: guards | chore(guards): remove tasks.py from PENDING_MIGRATION (now 140) |
| 🟡 | `d96c72d08` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate tasks.py to TasksRepository |
| 🟡 | `9b0057c7b` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): clean approvals.py repo.db.execute + chore: remove from PENDING_MIGRATION (now 141) |
| 🟡 | `cb84f02b3` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate approvals.py to ApprovalsRepository |
| 🟡 | `e817b87a9` | 2026-04-06 | Backend | Triagem (módulo) | chore(guards): remove triagem.py from PENDING_MIGRATION (now 142) |
| 🟡 | `5fe498341` | 2026-04-06 | Backend | Triagem (módulo) | feat(phase2): migrate triagem.py to TriagemRepository |
| 🟡 | `fbeacacdc` | 2026-04-06 | Backend | Scheduling / Calendar (PR-CAL) | chore(guards): remove scheduling.py from PENDING_MIGRATION (now 143) |
| 🟡 | `bbf5ea042` | 2026-04-06 | Backend | Scheduling / Calendar (PR-CAL) | feat(phase2): migrate scheduling.py to SchedulingRepository |
| 🟡 | `ae9748fbc` | 2026-04-06 | Backend | scope: guards | chore(guards): remove notifications.py from PENDING_MIGRATION (now 144) |
| 🟡 | `0b14a6e71` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate notifications.py to NotificationsRepository |
| 🟡 | `6efef88ef` | 2026-04-06 | Backend | scope: guards | chore(guards): remove communication.py from PENDING_MIGRATION (now 145) |
| 🟡 | `46e3c596b` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate communication.py to CommunicationRepository |
| 🟡 | `1bf5c7c0e` | 2026-04-06 | Backend | scope: guards | chore(guards): remove billing.py from PENDING_MIGRATION (now 146) |
| 🟡 | `07eb6259d` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate billing.py to BillingRepository |
| 🟡 | `5d088d3d3` | 2026-04-06 | Backend | Backend Services (BE) | Add vacancy saturation checks and billing repository functionality — Adds vacancy saturation checkin |
| 🟡 | `0e3c3b6e3` | 2026-04-06 | Backend | scope: guards | chore(guards): remove job_vacancies/screening.py from PENDING_MIGRATION (now 147) |
| 🟡 | `b2eaf7827` | 2026-04-06 | Backend | FastAPI v1 endpoints | Fix errors preventing job vacancy and database loading — Refactor job vacancy screening endpoints to |
| 🟡 | `98e679638` | 2026-04-06 | Backend | scope: guards | chore(guards): remove job_vacancies/public.py from PENDING_MIGRATION (now 148) |
| 🟡 | `58653fdf8` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate job_vacancies/public.py to JobVacancyPublicRepository |
| 🟡 | `595f759ae` | 2026-04-06 | Backend | scope: guards | chore(guards): remove auth.py from PENDING_MIGRATION (now 149) |
| 🟡 | `32296f1c9` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate auth.py to AuthRepository |
| 🟡 | `9f419de48` | 2026-04-06 | Backend | scope: guards | chore(guards): remove job_vacancies/crud.py from PENDING_MIGRATION (now 150) |
| 🟡 | `a9ebf83c8` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate job_vacancies/crud.py to JobVacancyCRUDRepository |
| 🟡 | `5a1fdcd1e` | 2026-04-06 | Backend | scope: guards | chore(guards): remove applications.py from PENDING_MIGRATION (now 151) |
| 🟡 | `54e87646a` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate applications.py to ApplicationRepository |
| 🟡 | `d2aa0a07f` | 2026-04-06 | Backend | scope: guards | chore(guards): remove screening.py from PENDING_MIGRATION (now 152) |
| 🟡 | `995d30786` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate screening.py to ScreeningRepository |
| 🔴 | `6ced5a6c3` | 2026-04-06 | Cross Back↔Front | §15 WSI | Add new repositories for job vacancies and screening tasks — Introduce new repository classes for ma |
| 🟡 | `4d00cb901` | 2026-04-06 | Backend | scope: guards | chore(guards): remove lifecycle.py from PENDING_MIGRATION (now 153) |
| 🟡 | `235ec864c` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate job_vacancies/lifecycle.py to JobVacancyLifecycleRepository |
| 🟡 | `65a914bf1` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update mock component imports for WSI reports and Teams adaptive card — Reorder import paths for WSI |
| 🟡 | `fbf45c9f6` | 2026-04-06 | Backend | Task #41 | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Created ce |
| 🟡 | `16d9df8f5` | 2026-04-06 | Backend | Task #41 | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integr |
| 🟡 | `430f24c9c` | 2026-04-06 | Backend | Task #41 | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integr |
| 🟡 | `bf58a9a2e` | 2026-04-06 | Backend | Task #41 | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integr |
| 🟡 | `c498ea242` | 2026-04-06 | Backend | Task #41 | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Modified j |
| 🟡 | `24a4b893e` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for weekly digest and reports — Reorders and updates import paths for compo |
| 🟢 | `57cf5e644` | 2026-04-06 | Frontend (UI) | Task #47 | Task #47: Chat LIA — Correções visuais e Design System — Changes made: |
| 🟢 | `cffd1fd7c` | 2026-04-06 | Frontend (UI) | Task #46 | Task #46: Reordenar menu lateral — Reordenado o array `menuItems` em plataforma-lia/src/components/s |
| 🟡 | `9c2cb8018` | 2026-04-06 | Backend | Backend Services (BE) | Add comment explaining initial free credits for new users — Adds a comment to clarify the purpose of |
| 🟡 | `288c119f1` | 2026-04-06 | Backend | Task #40 | Task #40: Credits — Full billing infrastructure — Models (billing.py): |
| 🟡 | `07094b34d` | 2026-04-06 | Backend | scope: guards | chore(guards): remove interviews.py from PENDING_MIGRATION (now 154) |
| 🔴 | `fdc03b5a4` | 2026-04-06 | Cross Back↔Front | Task #40 | Task #40: Credits — Full billing infrastructure — Models (billing.py): |
| 🟡 | `64f4b2da7` | 2026-04-06 | Backend | scope: guards | chore(guards): remove ats.py from PENDING_MIGRATION (now 155) |
| 🟡 | `1e34a7071` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate ats.py to ATSRepository |
| 🟢 | `2125061c8` | 2026-04-06 | Frontend (UI) | Candidates (FE pages) | Update candidate search and chat functionalities for improved user experience — Refactors type defin |
| 🟡 | `ef1a545b2` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate mailgun_webhooks.py to CommunicationRepository |
| 🔴 | `61752038b` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5 |
| 🔴 | `4c22ddda8` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5 |
| 🔴 | `07c43b2e4` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5 |
| 🟡 | `b2514cfeb` | 2026-04-06 | Backend | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5 |
| 🔴 | `43e90596e` | 2026-04-06 | Cross IA↔Front | §9 Security / Tenant guards | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5 |
| 🟡 | `2068c55ac` | 2026-04-06 | Backend | scope: guards | chore(guards): remove saas_metrics from PENDING_MIGRATION (now 156) |
| 🟡 | `7e32ecc0e` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate saas_metrics.py to SaasMetricsRepository |
| 🟡 | `b7fe1a503` | 2026-04-06 | Backend | scope: guards | chore(guards): remove trust_center from PENDING_MIGRATION (now 157) |
| 🟡 | `90bb06cc1` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate trust_center.py to TrustCenterRepository |
| 🟡 | `fc175970c` | 2026-04-06 | Backend | scope: guards | chore(guards): remove company_culture from PENDING_MIGRATION (now 158) |
| 🟡 | `46dd18dcc` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate company_culture.py to CompanyCultureRepository |
| 🟡 | `f0c153e32` | 2026-04-06 | Backend | scope: guards | chore(guards): remove job_vacancies/analytics from PENDING_MIGRATION (now 159) |
| 🟡 | `43c3e03cf` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate job_vacancies/analytics.py to JobVacanciesAnalyticsRepository |
| 🟡 | `c4460ddd2` | 2026-04-06 | Backend | scope: guards | chore(guards): remove opinions from PENDING_MIGRATION (now 160) |
| 🟡 | `6aae0cde2` | 2026-04-06 | Backend | scope: guards | chore(guards): remove health_check from PENDING_MIGRATION (now 161) |
| 🟡 | `d8e3fa603` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate opinions.py to OpinionsRepository |
| 🟡 | `9c2fa9f4f` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate health_check.py to HealthCheckRepository |
| 🟡 | `10b011129` | 2026-04-06 | Backend | Backend Services (BE) | Organize application health and opinion modules for better structure — Update __init__.py files to p |
| 🟢 | `55999add3` | 2026-04-06 | Frontend (UI) | Task #45 | Task #45: Redesign Chat Empty State (Carrossel + Layout Centralizado) — Changes made: |
| 🟡 | `fdc6eced4` | 2026-04-06 | Backend | scope: guards | chore(guards): remove chat from PENDING_MIGRATION (now 162) |
| 🟡 | `64ff314ce` | 2026-04-06 | Backend | §9 Security / Tenant guards | Task #38: ATS Integration — Full frontend-backend wiring with complete security hardening — Frontend |
| 🟡 | `4894ab4ee` | 2026-04-06 | Backend | Configurações (hub) | chore(guards): remove admin_settings from PENDING_MIGRATION (now 163) |
| 🔴 | `837aef67a` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: |
| 🟡 | `855b7a6e8` | 2026-04-06 | Backend | scope: guards | chore(guards): remove integrations_hub from PENDING_MIGRATION (now 164) |
| 🟡 | `92c94521d` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate integrations_hub.py to IntegrationsHubRepository |
| 🔴 | `2bbc1edf9` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: |
| 🟡 | `c18a47e45` | 2026-04-06 | Backend | scope: guards | chore(guards): remove bulk_actions from PENDING_MIGRATION (now 165) |
| 🟡 | `9dd901c2c` | 2026-04-06 | Backend | scope: guards | chore(guards): remove goals from PENDING_MIGRATION (now 166) |
| 🟡 | `622d15605` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate bulk_actions.py to BulkActionsRepository |
| 🟡 | `32e9d71e7` | 2026-04-06 | Backend | scope: guards | chore(guards): remove technical_tests from PENDING_MIGRATION (now 167) |
| 🟡 | `54b468a90` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate goals.py to GoalsRepository |
| 🟡 | `b96f0c6ff` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate technical_tests.py to TechnicalTestsRepository |
| 🟡 | `6e6a504dd` | 2026-04-06 | Backend | scope: guards | chore(guards): remove shared_searches from PENDING_MIGRATION (now 168) |
| 🔴 | `587e96c50` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Task #38: ATS Integration — Complete frontend-backend wiring with security hardening — Frontend chan |
| 🟡 | `84452a74d` | 2026-04-06 | Backend | Policy / Job Creation | fix(phase2): remove stray AsyncSession/get_db from policy_engine.py apply_sector_defaults |
| 🟡 | `ede167a88` | 2026-04-06 | Backend | Policy / Job Creation | chore(guards): remove policy_engine from PENDING_MIGRATION (now 169) |
| 🟡 | `381813272` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate shared_searches.py to SharedSearchRepository |
| 🟡 | `74499db11` | 2026-04-06 | Backend | scope: guards | chore(guards): remove client_users from PENDING_MIGRATION (now 170) |
| 🟡 | `590707f9e` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate client_users.py to ClientUserRepository |
| 🔴 | `14b5ae056` | 2026-04-06 | Cross Back↔Front | Task #38 | Task #38: ATS Integration — Complete frontend-backend wiring — Frontend changes: |
| 🟡 | `d7287f9d5` | 2026-04-06 | Backend | scope: guards | chore(guards): remove data_subject_requests from PENDING_MIGRATION (now 171) |
| 🟡 | `a48c5d3c2` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate data_subject_requests.py to DataSubjectRepository |
| 🟡 | `d0283f01d` | 2026-04-06 | Backend | scope: guards | chore(guards): remove consent_management from PENDING_MIGRATION (now 172) |
| 🟡 | `00d139603` | 2026-04-06 | Backend | scope: guards | chore(guards): remove candidate_lists from PENDING_MIGRATION (now 173) |
| 🟡 | `deea3c774` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate consent_management.py to ConsentRepository |
| 🟢 | `bf0e042d0` | 2026-04-06 | Docs | Docs / Refactor | docs: update REFACTOR_PLAN.md — Phase 2 (12 migrated, 174 pending), Phase 4 done, Phase 9 LOC delta |
| 🟡 | `44923dea2` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate candidate_lists.py to CandidateListRepository |
| 🟡 | `a7c7db21c` | 2026-04-06 | Backend | Compliance / LGPD / EU AI Act | chore(guards): remove compliance_controls, journey_mapping from PENDING_MIGRATION (now 174) |
| 🟡 | `4ee2793ea` | 2026-04-06 | Backend | Compliance / LGPD / EU AI Act | feat(phase2): migrate compliance_controls.py to ComplianceControlsRepository |
| 🟡 | `bbfe57323` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate journey_mapping.py to JourneyMappingRepository |
| 🔴 | `8729d4587` | 2026-04-06 | Cross Back↔Front | Task #38 | Task #38: ATS Integration — Connect frontend to real backend — Backend changes (lia-agent-system/app |
| 🟡 | `cc8e1759a` | 2026-04-06 | Backend | Compliance / LGPD / EU AI Act | chore(guards): remove lgpd_compliance, workforce, recruitment_journey from PENDING_MIGRATION (now 17 |
| 🟡 | `0d7556503` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate workforce.py to WorkforceRepository + fix broken string literals — - Created a |
| 🟡 | `3cc91ac2a` | 2026-04-06 | Backend | Automations | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handle |
| 🟡 | `35a7a201c` | 2026-04-06 | Backend | Automations | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handle |
| 🟡 | `140d09d0e` | 2026-04-06 | Backend | Automations | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handle |
| 🟡 | `2d2273b1b` | 2026-04-06 | Backend | scope: phase2 | feat(phase2): migrate recruitment_journey.py to RecruitmentJourneyRepository |
| 🟡 | `b41bdfb14` | 2026-04-06 | Backend | Compliance / LGPD / EU AI Act | feat(phase2): migrate lgpd_compliance.py to LGPDRepository |
| 🟡 | `eb2d19e86` | 2026-04-06 | Backend | scope: guards | fix(guards): add platform_event_handlers.py to PENDING_MIGRATION allowlist |
| 🔴 | `b7c41231d` | 2026-04-06 | Cross IA↔Back | Automations | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handle |
| 🔴 | `9826db31d` | 2026-04-06 | Cross IA↔Back | scope: phase9 | refactor(phase9): ruff auto-fixes — remove 819 unused imports, sort imports, modernize type annotati |
| 🟢 | `f37c4994e` | 2026-04-06 | Frontend (UI) | §18 Senioridade + Job Migration | Add market percentile to job report quality metrics and hide empty seniority section — Expose `marke |
| 🟢 | `fdfa7faba` | 2026-04-06 | Frontend (UI) | Task #36 | Task #36: Reports & Predictions — Real ML data in frontend — - Fixed `catch (error: any)` → `catch ( |
| 🟢 | `b095ed03f` | 2026-04-06 | Frontend (UI) | Task #36 | Task #36: Reports & Predictions — Real ML data in frontend — - Fixed `catch (error: any)` → `catch ( |
| 🟡 | `22c5c8f77` | 2026-04-06 | Backend | Observability / Sentry / OTLP | feat(phase2): migrate observability.py to ObservabilityRepository |
| 🟢 | `b998c624a` | 2026-04-06 | Docs | scope: phase4 | docs(phase4): update REFACTOR_PLAN.md phase 4 status to PARTIAL — - 132 service files converted to b |
| 🟡 | `c3a581489` | 2026-04-06 | Backend | Observability / Sentry / OTLP | feat(phase2+4): migrate candidates.py, fix service shims, add observability domain |
| 🔴 | `6d7a9daf8` | 2026-04-06 | Cross IA↔Front | Task #36 | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useM |
| 🟡 | `05fee6069` | 2026-04-06 | Backend | scope: phase3+fixes | feat(phase3+fixes): migrate 8 model files to lia_models, fix syntax errors |
| 🔴 | `e7e1bb07e` | 2026-04-06 | Cross IA↔Front | Task #36 | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useM |
| 🟡 | `17a3ea932` | 2026-04-06 | Backend | scope: phase2-recruitment | feat(phase2-recruitment): create recruitment domain repositories and migrate controller — - Create a |
| 🟡 | `f4771fd31` | 2026-04-06 | Backend | Configurações (hub) | feat: company domain repository layer and rewrite company.py to use repos — - Created app/domains/co |
| 🟡 | `e2a53d2ef` | 2026-04-06 | Backend | FastAPI v1 endpoints | Add department management features to the company API — Introduces new API endpoints for listing, cr |
| 🔴 | `41d9174cd` | 2026-04-06 | Cross IA↔Front | Task #43 | Task #43: Complete audit and fix of LIA agentic capabilities — Changes across 10+ files covering all |
| 🟡 | `de4b4fe9f` | 2026-04-06 | Backend | Mockup Sandbox (artefato gerado) | Add ability to enrich company profiles with external data sources — Introduce a new API endpoint `/e |
| 🟡 | `53f970159` | 2026-04-06 | Frontend (UI) | Task #44 | Task #44: UI parity — add ContextBadge, HITLConfirmCard, PlanProgressCard, dynamic suggestions acros |
| 🟡 | `ab55c549b` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `c809ff80d` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update component mappings for report and weekly digest mockups — Update mockup component mappings in |
| 🟡 | `4fe295025` | 2026-04-06 | Frontend (UI) | Task #42 | Task #42: Merge interview cards from Painel de Controle into Tarefas page — Changes: |
| 🟡 | `eb0dfa80e` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `ca0129a63` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update mock components to include new file paths — Regenerate mockup-components.ts to reflect update |
| 🟡 | `d7476dbc2` | 2026-04-06 | Cross IA↔Back | Task #32 | Fix candidates and vacancies loading (Task #32) — Root cause: The backend (lia-agent-system) was cra |
| 🟡 | `6a4c33b52` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `1699cabcf` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `19c0894cb` | 2026-04-06 | Frontend (UI) | Task #33 | Task #33: Equalizar espaçamento do input no chat da LIA — Changed the margin-bottom of the suggestio |
| 🔴 | `9ff2904b9` | 2026-04-06 | Cross IA↔Back | FastAPI v1 endpoints | Remove unused demo user fallbacks and clean up code imports — Update imports, type hints, and remove |
| 🟡 | `61fa3f32b` | 2026-04-06 | Backend | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done |
| 🟡 | `45c603989` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done |
| 🟡 | `c33440970` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done |
| 🟡 | `63e9557cc` | 2026-04-06 | Cross IA↔Back | §15 WSI | Task #35: Profile Analysis — BARS + WSI combined on CV — ## What was done |
| 🟡 | `dc9ff6268` | 2026-04-06 | Backend | §9 Security / Tenant guards | Improve backend security by removing demo user fallbacks — Update documentation and logs to reflect  |
| 🟡 | `ae69cf957` | 2026-04-06 | Backend | Triagem (módulo) | Improve logging and email provider functionality — Update logging for demo users in chat actions, re |
| 🟡 | `438fb466e` | 2026-04-06 | Backend | §9 Security / Tenant guards | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Ch |
| 🟡 | `756ab5464` | 2026-04-06 | Backend | §9 Security / Tenant guards | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Ch |
| 🟡 | `1f87281fd` | 2026-04-06 | Backend | §9 Security / Tenant guards | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Ch |
| 🟡 | `25cdcdfd7` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `16c6bd8fa` | 2026-04-06 | Cross Back↔Front | Configurações (hub) | Remove entire /admin section from plataforma-lia frontend — Removed ~19,000 lines across 93 files th |
| 🟢 | `8241fe8f1` | 2026-04-06 | Frontend (UI) | Configurações (hub) | Remove duplicate system configuration page from admin area — Removes the duplicated 'Configurações d |
| 🔴 | `3e802b0ed` | 2026-04-06 | Cross Back↔Front | Mockup Sandbox (artefato gerado) | Restore Shield icon and update dependencies for CV parsing — Update dependencies in pyproject.toml a |
| 🟢 | `8f7248a45` | 2026-04-06 | Frontend (UI) | Task #30 | Task #30: Unificar padrão visual de todos os chats LIA — Created shared ChatBubbleBase component and |
| 🔴 | `b5e74a10e` | 2026-04-06 | Cross Back↔Front | Compliance Dashboard (FE) | Remove candidate search API endpoints and related configurations — Delete `candidate_search.py` file |
| 🟡 | `573177e95` | 2026-04-06 | Backend | §9 Security / Tenant guards | Update Python dependencies for enhanced security and utility — Remove the python-jose dependency and |
| 🟢 | `73a7c303c` | 2026-04-06 | Docs | §9 Security / Tenant guards | Update hardening plan with security fixes and improvements — Update HARDENING_PLAN.md to include rec |
| 🟡 | `f697a4efe` | 2026-04-06 | Backend | Automation domain (BE) | Improve email logging and update mock component references — Update email sending logs to be more ge |
| 🟢 | `1465a5be6` | 2026-04-06 | Frontend (UI) | Task #31 | Task #31: Remover seção Recentes da página de chat — Removed the "Recentes" (Recent conversations) s |
| 🟡 | `18602a9d2` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `09e3dd04c` | 2026-04-06 | Cross Back↔Front | FastAPI v1 endpoints | Refine chat interface and optimize backend data handling — Update UI components to adjust message bu |
| 🟢 | `dfc64417e` | 2026-04-06 | Frontend (UI) | Frontend (componentes diversos) | Center greeting and align recent chat items — Center the greeting title and subtitle, and adjust the |
| 🟡 | `567f73d38` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `2ae4c5ff3` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `dce09e215` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Add refined variations for the chat page layout — Introduce two new chat layout components, `Refined |
| 🟡 | `6c42ad91b` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Add four distinct chat layout variations for user exploration — Introduces four new chat layout comp |
| 🟡 | `f25726dec` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Add three distinct chat layout designs for user interaction — Implement three new chat layout compon |
| 🟢 | `444a4ab80` | 2026-04-06 | Frontend (UI) | scope: chat | fix(chat): restore outer card border on prompt inputs — single card wrapping input + buttons (Task # |
| 🟡 | `ebf34877d` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `bbe405048` | 2026-04-06 | Frontend (UI) | scope: chat | fix(chat): corrigir auto-scroll, avatar do usuário e ícone Brain no input — Task #25 — Três correçõe |
| 🟡 | `5b39c0dad` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `0a0538315` | 2026-04-06 | Frontend (api/util) | scope: e2e | feat(e2e): Auditoria completa de usabilidade dos Chats LIA via Playwright (Task #26) — ## Suítes Pla |
| 🟡 | `9d1d3eabd` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `900d7c175` | 2026-04-06 | Frontend (UI) | scope: chat-lia | fix(chat-lia): corrigir layout e alinhamento do Welcome do Chat LIA (Task #27) — ## Problema |
| 🟢 | `127d6284a` | 2026-04-06 | Frontend (UI) | scope: chat | feat(chat): Polish do Chat — Cards, Cores e Histórico Recente (Task #24) — ## Changes |
| 🟡 | `0785ad6c4` | 2026-04-06 | Frontend (UI) | Task #23 | Task #23: Remove card-in-card pattern from LIA chat prompt components — Removed inner pill/card wrap |
| 🟡 | `51eb73d08` | 2026-04-06 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `3c7e2d1ba` | 2026-04-06 | Frontend (UI) | scope: keyboard | fix(keyboard): ESC key no longer triggers notification bell or microphone — Task #22: Fix ESC key tr |
| 🟢 | `6491dc435` | 2026-04-06 | Frontend (UI) | Frontend (componentes diversos) | Restore large brain icon to user greeting and adjust related styling — Restores the `Brain` lucide-r |
| 🟢 | `4cbb751bf` | 2026-04-06 | Frontend (UI) | Frontend (componentes diversos) | Update chat interface to improve user experience and visual appeal — Import and apply Source Serif 4 |
| 🟢 | `de2479e46` | 2026-04-06 | Frontend (UI) | LIA Float UI (FE) | Prevent floating chat from overlapping with inline chats and restore chat page — Introduce a `hasInl |
| 🔴 | `9d569d6c7` | 2026-04-06 | Cross Back↔Front | §9 Security / Tenant guards | Improve chat functionality and security by adding retries and enhancing authentication — This commit |
| 🟢 | `a1e073bc2` | 2026-04-06 | Frontend (UI) | Kanban (vagas) | feat: implement contextual LIA chat presentation by page (#20) — New: LiaChatShell.tsx — unified wra |
| 🟡 | `1d3f2691b` | 2026-04-06 | Backend | FastAPI v1 endpoints | Add missing API modules and WebSocket manager for agent communication — Creates new API router files |
| 🟡 | `a57a53db7` | 2026-04-06 | Backend | FastAPI v1 endpoints | Remove unused insurance module import from API initialization — Remove import statement for the 'ins |
| 🟢 | `274dd0926` | 2026-04-06 | Docs | Backend (deps) | Update Python dependencies to resolve conflicts — Correct Python dependency versions in requirements |
| 🟡 | `f699d602a` | 2026-04-06 | Outro | Mockup Sandbox (artefato gerado) | Update component registration for ElevenLabs funnel — Regenerate the component registration map for  |
| 🟡 | `052f3c4c2` | 2026-04-06 | Frontend (UI) | Chat UI (FE) | Merged changes from nng5i7ac/main — Replit-Task-Id: 962f54f9-66bc-4345-bd00-4674bed92299 |
| 🟡 | `57281a577` | 2026-04-06 | Backend | Backend Services (BE) | Add new and update existing functionalities for managing candidates and jobs — Integrate new and upd |
| 🟡 | `8e4b71cd6` | 2026-04-05 | Backend | FastAPI v1 endpoints | Remove unused API routes for insurance, risk, and continuity — Removes the inclusion of insurance, r |
| 🟢 | `9a6f5b9df` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Task #21: Refactor Integrations Hub from separate route to inline Settings section — - Moved Integra |
| 🟢 | `6becad49d` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Task #21: Refactor Integrations Hub from separate route to inline Settings section — - Moved Integra |
| 🟢 | `be4fcb5e2` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Task #21: Refactor Integrations Hub from separate route to inline Settings section — - Moved Integra |
| 🟢 | `8edd9a5c5` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Task #21: Refactor Integrations Hub from separate route to inline Settings section — - Moved Integra |
| 🟡 | `46cb28302` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Task #21: Refactor Integrations Hub from separate route to inline Settings section — - Moved Integra |
| 🟡 | `9441593dc` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `f40efdf85` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Add a back button to the integrations page menu — Add an ArrowLeft icon import and a button element  |
| 🟢 | `9b191f000` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Add a link to the integrations page and fix navigation errors — Replaced router.push with window.loc |
| 🟢 | `7022f5dad` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Add integrations link to the settings sidebar for external service connections — Import and utilize  |
| 🟡 | `6196cbdc7` | 2026-04-05 | Frontend (UI) | Task #18 | Task #18: Hub de Integrações — Página Unificada estilo Claude/Manus — Redesigned /configuracoes/inte |
| 🟡 | `e26a7e8f0` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `ccca718b9` | 2026-04-05 | Cross IA↔Back | §15 WSI | Improve AI chat functionality by enhancing LLM integrations and error handling — Refactor LLM client |
| 🟢 | `797b96812` | 2026-04-05 | Frontend (UI) | Task #17 | Task #17: Cleanup visual do empty state do Chat — Changes made: |
| 🔴 | `7dff2e8a3` | 2026-04-05 | Cross IA↔Back | §9 Tenant Isolation / Multi-tenancy | Task #15: Migrate legacy company_id/tenant_id — remove all fallback defaults — - Alembic migration 0 |
| 🟡 | `7dbc57a4c` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `77b972560` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `5c8be64c7` | 2026-04-05 | Frontend (UI) | Chat UI (FE) | Improve chat functionality by ensuring secure connections and fixing message errors — Fixes WebSocke |
| 🟢 | `3760023f8` | 2026-04-05 | Docs | §1 Teams Integration | Task #14: Proteger configurações Microsoft Teams no CLAUDE.md — Adicionada seção "⛔ DO NOT MODIFY —  |
| 🔴 | `420c5b228` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Update chat functionality to correctly stream responses — Adjust API endpoints and client configurat |
| 🟡 | `587243dce` | 2026-04-05 | Backend | §1 Teams Integration | Add public access to team API endpoints — Allow unauthenticated access to the /api/v1/teams/ endpoin |
| 🟢 | `f1c0642bb` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Update chat interface for a cleaner look and better user experience — Modify chat page and agent con |
| 🟢 | `9da87e7d6` | 2026-04-05 | Frontend (UI) | Chat UI (FE) | Fix chat interface issues including message highlighting and input positioning — Corrected duplicate |
| 🟢 | `a5574125a` | 2026-04-05 | Frontend (api/util) | Hooks (FE) | Add a system to ensure chat messages are sent after login — Implement a reconnection mechanism to en |
| 🟢 | `e815712ce` | 2026-04-05 | Frontend (UI) | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — Components: |
| 🟢 | `f96148e01` | 2026-04-05 | Frontend (UI) | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🟡 | `578d016cc` | 2026-04-05 | Backend | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🔴 | `2278806b7` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🔴 | `283441d37` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🟢 | `f867cf426` | 2026-04-05 | Frontend (UI) | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🔴 | `1cd2b37c5` | 2026-04-05 | Cross Back↔Front | §1 Teams Integration | Update chat functionality to correctly track recent conversations and improve task management — This |
| 🔴 | `bb6a29bc0` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🔴 | `239ec2f66` | 2026-04-05 | Cross Back↔Front | Task #13 | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: |
| 🟢 | `7e3d7ae56` | 2026-04-05 | Frontend (UI) | Task #12 | Task #12: Split-Screen Dinâmico — full panel_update wiring across all chat surfaces — T003: WebSocke |
| 🟢 | `145716afe` | 2026-04-05 | Frontend (UI) | Task #12 | Task #12: Split-Screen Dinâmico — full panel_update wiring across all chat surfaces — T003: WebSocke |
| 🟢 | `dc162a9b6` | 2026-04-05 | Frontend (UI) | Task #12 | Task #12: Split-Screen Dinâmico — T003/T004/T005 complete — T003: WebSocket panel_update event handl |
| 🔴 | `f30f28f96` | 2026-04-05 | Cross Back↔Front | Task #12 | Task #12: Split-Screen Dinâmico — T003/T004/T005 complete — T003: WebSocket panel_update event handl |
| 🟢 | `db821596e` | 2026-04-05 | Frontend (UI) | Task #11 | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage/setContextPage + e |
| 🟡 | `a7a390b8f` | 2026-04-05 | Frontend (UI) | Task #11 | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage + setContextPage + |
| 🟡 | `b08d14582` | 2026-04-05 | Frontend (UI) | Task #11 | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage + setContextPage t |
| 🟢 | `97524589b` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Improve handling of initial dashboard page loading — Clean up URL query parameters after initializin |
| 🟢 | `b2c357310` | 2026-04-05 | Frontend (UI) | Task #10 | Task #10: Wire Chat LIA as primary menu item with fallback navigation — - Added "Chat LIA" as first  |
| 🟢 | `cd6737543` | 2026-04-05 | Frontend (UI) | Task #10 | Task #10: Wire Chat LIA as primary menu item — - Added "Chat LIA" as first sidebar menu item with Me |
| 🟢 | `785dbc19d` | 2026-04-05 | Frontend (UI) | Task #10 | Task #10: Wire Chat LIA as primary menu item — - Added "Chat LIA" as first sidebar menu item with Br |
| 🟡 | `7b7ae70cf` | 2026-04-05 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include funil eleven labs component — Update mockups to reflect changes in the Fun |
| 🟡 | `f15556817` | 2026-04-05 | Backend | Task #8 | Fix backend SQL error breaking app preview (Task #8) — Replace `SET LOCAL app.company_id = :cid` wit |
| 🟡 | `b6f8b45dc` | 2026-04-05 | Outro | Mockup Sandbox (artefato gerado) | Update mockups to include Eleven Labs funnel component — Update mockup components to correctly regis |
| 🔴 | `d641ea4eb` | 2026-04-05 | Cross Back↔Front | §14 BYOK + LLM Factory | feat: Migrate Voice Screening VoIP from Twilio+STT+TTS to Gemini Live Audio API — Task #6: Browser V |
| 🔴 | `535f05984` | 2026-04-05 | Cross IA↔Front | §9 Tenant Isolation / Multi-tenancy | Fix multi-tenancy company_id isolation (Task #5) — Backend: |
| 🟡 | `0faa509af` | 2026-04-05 | Cross IA↔Back | FastAPI v1 endpoints | Integrate planning system into chat and improve session management — Refactor code to connect the pl |
| 🔴 | `95ad2730a` | 2026-04-05 | Cross Back↔Front | LIA Float UI (FE) | Add multi-step plan execution with real-time progress tracking — Integrate plan detection and execut |
| 🔴 | `9882eeb76` | 2026-04-05 | Cross Back↔Front | FE libs / utils | Hide internal thoughts from users in chat conversations — Add functionality to strip `<thought>` tag |
| 🟡 | `a2c18180d` | 2026-04-05 | Frontend (UI) | Task #4 | Unify chat-cyan (#00B8B8) to wedo-cyan (#60BED1) across the platform — Task #4: Eliminate the diverg |
| 🟡 | `e0ba45072` | 2026-04-05 | Outro | Mockup Sandbox (artefato gerado) | Add comparison and desired state components to the sandbox — Add mock components for architectural c |
| 🟢 | `015f769fe` | 2026-04-05 | Frontend (UI) | Task #3 | fix: corrigir design dos cards de sugestão no chat LIA — Task #3: Corrigir design dos cards de suges |
| 🟡 | `683e59bc5` | 2026-04-05 | Outro | Mockup Sandbox (artefato gerado) | Add components for analyzing current and desired states — Add mock components for comparing current  |
| 🟡 | `6be522cbc` | 2026-04-05 | Backend | Compliance / LGPD / EU AI Act | Fix missing audit_logs columns (session_id, input_text, output_text, fairness_flags, agent_used) — P |
| 🔴 | `642ece67f` | 2026-04-05 | Cross Back↔Front | Backend Services (BE) | Update daily briefing to show errors and refresh data — Modify the daily briefing card component to  |
| 🟢 | `8cfebd222` | 2026-04-05 | Frontend (UI) | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real AP |
| 🔴 | `f04070006` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real AP |
| 🔴 | `3621573ba` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real AP |
| 🔴 | `b9af19951` | 2026-04-05 | Cross Back↔Front | Task #2 | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real AP |
| 🔴 | `84c6159b5` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Connect Tarefas page to real backend APIs + Activity Feed section — Changes: |
| 🔴 | `3ef9c9f72` | 2026-04-05 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Connect Tarefas page to real backend APIs + Activity Feed section — Changes: |
| 🟡 | `d0c1aa91a` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Add filtering for activity feed and improve task lifecycle handling — Introduces new API endpoints f |
| 🔴 | `9bd6b42c8` | 2026-04-05 | Cross Back↔Front | Backend Proxy Routes (FE) | Connect Tarefas page to real backend APIs, add Activity Feed section — - Created 4 Next.js proxy rou |
| 🟡 | `8631ac9ad` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `2defdb1c0` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Add control panel page back to main menu sidebar — Reintroduce "Painel de Controle" as a menu item i |
| 🟡 | `d1a3a9502` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Rename dashboard page to tasks and update related navigation — Updates file paths, component imports |
| 🟢 | `cf793c62f` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Fix incorrect styling applied to alerts and job items — Corrected React style prop usage in ActiveAl |
| 🔴 | `3fdac6219` | 2026-04-05 | Cross Back↔Front | Kanban (vagas) | fix: manual job creation redirect to config page (#151) — Frontend: |
| 🟡 | `9aebc20f9` | 2026-04-05 | Frontend (UI) | §6 Chat Unificado / Funil | feat: Padronizar Tip Cards do Funil de Busca (Task #150) — Padronizados todos os cards de "Dica:" no |
| 🟡 | `164bab9ba` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `f26ccce9d` | 2026-04-05 | Frontend (UI) | Tests (BE unit/integration) | Update component styling and adjust backend import paths — Fix duplicated className in EAPTabNatural |
| 🟢 | `acf741f03` | 2026-04-05 | Testes | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e test |
| 🔴 | `381379cdb` | 2026-04-05 | Cross IA↔Front | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e test |
| 🔴 | `476849cd5` | 2026-04-05 | Cross IA↔Front | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e test |
| 🟢 | `af9ce154d` | 2026-04-05 | Frontend (UI) | Task #149 | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e test |
| 🟢 | `60b9738c3` | 2026-04-05 | Docs | Sprint COMPLETE | docs: consolidation sprint complete - services shimmed 97/98, Tarefa 4 audit |
| 🟢 | `a95e644a6` | 2026-04-05 | Frontend (UI) | Task #149 | Task #149: Fix search prompt UX - tooltip fonts and autocomplete overlay — Changes: |
| 🟡 | `5047e550d` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `747ce44cb` | 2026-04-05 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Add fairness warnings and fix onboarding hydration issues — Introduce `fairness_warnings` to `ChatRe |
| 🟡 | `25e7d7645` | 2026-04-05 | Cross IA↔Back | Performance | perf: lower vector cache threshold from 0.92 to 0.85 |
| 🟡 | `540e3d76d` | 2026-04-05 | Backend | FastAPI v1 endpoints | chore: remove .bak residual files from Etapa 6 split — Remove candidate_search.py.bak (234K), job_va |
| 🟡 | `60ec7840b` | 2026-04-05 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for funnel elevenlabs — Reorder the module map in `mockup-components.ts` to |
| 🟢 | `d685c0088` | 2026-04-05 | Frontend (UI) | §6 Chat Unificado / Funil | fix: Corrigir erros na página /funil/ (Vagas) - Task #148 — ## Mudanças de código |
| 🟡 | `5ca446df4` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `009229e73` | 2026-04-05 | Outro | §9 Security / Tenant guards | Add WorkOS SSO and SCIM integration to the user authentication system — Integrates WorkOS for SSO an |
| 🟡 | `e0405a9a3` | 2026-04-05 | Outro | Login UI (FE) | Remove demo buttons and unnecessary routes from login page — Remove demo buttons and update routing  |
| 🟢 | `bcf87b3df` | 2026-04-05 | Frontend (api/util) | scope: sidebar | fix(sidebar): resolve setState-during-render warning in useSidebarState — Task: #147 - Fix Sidebar s |
| 🟢 | `8469cd2bf` | 2026-04-05 | Frontend (UI) | Onboarding (FE) | Remove broken demo buttons and their associated routes — Remove the `/demo-onboarding` route from pu |
| 🟡 | `a86be78e3` | 2026-04-05 | Backend | Task #146 | Fix dev-server 500 errors on candidates and job-vacancies endpoints (Task #146) — Bug 1 - Candidates |
| 🟡 | `2d0ac4213` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `2eaaba945` | 2026-04-05 | IA | §15 WSI | Update roadmap document with detailed job creation and screening configurations — Add a consolidated |
| 🔴 | `0867d7d12` | 2026-04-05 | Cross IA↔Front | §2 Orchestrator Migration | Fix sidebar errors and update backend port configuration — Addresses "Maximum update depth exceeded" |
| 🟡 | `fd50d7add` | 2026-04-05 | IA | §15 WSI | Update feedback generation to maintain a neutral tone — Modify `wsi_service.py` to remove decision-b |
| 🟢 | `5f6517039` | 2026-04-05 | Frontend (UI) | §18 Senioridade + Job Migration | Update action executor and resolve seniority logic — Refactor tests for action executor and action h |
| 🟡 | `9596649a9` | 2026-04-05 | Frontend (UI) | Configurações (hub) | Remove Slack integration and enhance notification settings — Removes Slack integration support and u |
| 🟢 | `13b8b4adb` | 2026-04-05 | Frontend (UI) | Frontend (componentes diversos) | Remove work models tab and update user display in top bar — Remove the 'Work Models' tab component a |
| 🟡 | `77c474cbe` | 2026-04-05 | IA | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Core migration: all 5 callers no |
| 🟡 | `3a9506a03` | 2026-04-05 | Backend | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Core migration: all 5 callers no |
| 🟡 | `c6948a1db` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Core migration: all 5 callers no |
| 🟡 | `70c7df4b6` | 2026-04-05 | IA | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Migrated all 5 callers to use WS |
| 🟡 | `6e99cedd0` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Migrated all 5 callers to use WS |
| 🟡 | `9e225f9dd` | 2026-04-05 | Cross IA↔Back | §15 WSI | Consolidate WSI question generation to wsi_service.py (Task #145) — Migrated all 5 callers to use WS |
| 🟡 | `4ba70b393` | 2026-04-05 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `a37527c9d` | 2026-04-04 | Backend | FastAPI v1 endpoints | Update candidate search imports and add user authentication dependencies — Refactor imports in candi |
| 🟡 | `4b4a69b5a` | 2026-04-04 | Cross IA↔Back | §15 WSI | refactor(wsi): consolidate Bloom/Dreyfus/seniority constants into wsi_constants.py — Centralized dup |
| 🟡 | `7c605d0f3` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🔴 | `dcda58d1e` | 2026-04-04 | Cross Back↔Front | scope: voip | feat(voip): complete VoIP browser calling with recruiter status visibility (Task #142) — End-to-end  |
| 🔴 | `3b95e5e7d` | 2026-04-04 | Cross Back↔Front | Task #144 | feat(task-144): Implement job vacancy lifecycle management — Backend: |
| 🔴 | `5b617db7c` | 2026-04-04 | Cross IA↔Front | §15 WSI | Align WSI scoring thresholds across the system and remove duplication — Update WSI scoring threshold |
| 🟡 | `e475dd48a` | 2026-04-04 | Backend | Triagem (módulo) | feat(voice-screening): Prompt Inteligente de Voz — LIA Conduz Triagem com Maestria (Task #140) — ##  |
| 🟡 | `3b562e758` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `9dadd3117` | 2026-04-04 | Cross IA↔Back | §15 WSI | feat(task-143): Unify web/chat screening (triagem) with WSI ecosystem — Integrates triagem_session_s |
| 🟡 | `12fb46883` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `afaeb4fa7` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `e7daeb78c` | 2026-04-04 | Frontend (UI) | Task #141 | feat(task-141): Complete screening channel config — disable unavailable channels + save-time integri |
| 🟡 | `14d8e5fde` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `d9a870fea` | 2026-04-04 | Backend | Voice / ElevenLabs / STT | Update audio transcription tool description to reflect correct STT service — Update the description  |
| 🔴 | `30b1b9151` | 2026-04-04 | Cross IA↔Front | Task #138 | Task #138: Dead integration cleanup - OpenMic, Deepgram, SynthFlow, StackOne, Neon, Prometheus, Graf |
| 🟡 | `0eb9f2427` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `7aeca82e6` | 2026-04-04 | Backend | §14 BYOK + LLM Factory | feat(task-135): Voice Screening Pipeline — Twilio Voice + Gemini 2.5 Flash (final) — Tests: 56 passe |
| 🟡 | `5e9ec6e4c` | 2026-04-04 | Backend | Observability / Sentry / OTLP | Task #137: Ativar LangSmith — Tracing de Chamadas de IA — Changes: |
| 🟡 | `9ae930c18` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `790319d7f` | 2026-04-04 | Cross IA↔Back | §14 BYOK + LLM Factory | feat(task-132): Gemini como LLM Padrão — Reordenar fallback chain — ## Objetivo |
| 🟡 | `b4a2a95dd` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `2138880c9` | 2026-04-04 | Backend | Task #131 | Task #131: Consolidate email providers — Mailgun primary, Resend fallback via composite, SendGrid re |
| 🟡 | `b9ece1589` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `3c7055f47` | 2026-04-04 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for Eleven Labs funnel — Update `mockup-components.ts` to correctly map the |
| 🔴 | `2b8c725c0` | 2026-04-04 | Cross Back↔Front | Observability / Sentry / OTLP | Task #136: Ativar Sentry — Monitoramento de Erros em Produção — Changes: |
| 🟡 | `a7ce1d37d` | 2026-04-04 | Outro | Mockup Sandbox (artefato gerado) | Update component imports to include missing files — Update artifacts/mockup-sandbox/src/.generated/m |
| 🟡 | `8f4536dfb` | 2026-04-04 | Backend | Task #134 | feat: Task #134 — Embedding Provider Factory multi-provider architecture — ## Summary |
| 🟡 | `9b9a5d840` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `044e357d9` | 2026-04-04 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for Funil ElevenLabs in the mockups — Update artifacts/mockup-sandbox/src/. |
| 🔴 | `9c57a17f5` | 2026-04-04 | Cross IA↔Front | Task #133 | Task #133: Remove all StackOne integration — Merge.dev as sole universal ATS connector — Complete re |
| 🟡 | `4fb8a5f89` | 2026-04-04 | Cross IA↔Back | Task #125 | feat(task-125): Declarative tool permissions (YAML) and DI for LLM providers — Task #125 — Tool Perm |
| 🔴 | `7419c32ac` | 2026-04-04 | Cross IA↔Back | Wizard (geral) | task-124: Eliminar 23 Shims e Estabelecer Contracts Formais entre Camadas — ## What was done |
| 🟡 | `31006178a` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `71fc9de33` | 2026-04-04 | Cross IA↔Back | Task #123 | feat(task-123): Complete LangGraph migration - fix regressions and update tests — Fixes two regressi |
| 🔴 | `80b4239f3` | 2026-04-04 | Cross IA↔Front | §15 WSI | Improve WSI feedback generation and scoring accuracy — Refactor the WSI scoring and feedback generat |
| 🟡 | `e4e97e207` | 2026-04-04 | Backend | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: |
| 🟡 | `fbfee90ed` | 2026-04-04 | Backend | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: |
| 🔴 | `4fb43153b` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: |
| 🔴 | `3dfe1ede9` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: |
| 🟢 | `c189721d5` | 2026-04-04 | Frontend (UI) | Triagem (módulo) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl`  |
| 🟢 | `676943348` | 2026-04-04 | Frontend (UI) | Triagem (módulo) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl`  |
| 🔴 | `d50c67402` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl`  |
| 🟡 | `305c528ee` | 2026-04-04 | Backend | Task #126 | feat(task-126): Auditoria Production Readiness (18 critérios) + Testes E2E de Resiliência — ## Objet |
| 🟡 | `da05a12f7` | 2026-04-04 | Outro | Mockup Sandbox (artefato gerado) | Update component imports for report tabs and adaptive cards — Reorders and updates import paths for  |
| 🟡 | `a2facdc6b` | 2026-04-04 | Cross IA↔Back | Task #122 | fix: address code review for Task #122 orchestrator consolidation — Three runtime regressions fixed, |
| 🟡 | `a6c85b154` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `617d2b0ca` | 2026-04-04 | Backend | Triagem (módulo) | Task #128: Triagem UX — Ajustes Candidato (Welcome, Balões, Tom, Whitelabel) — Backend (triagem_sess |
| 🔴 | `5bb701e8f` | 2026-04-04 | Cross Back↔Front | Triagem (módulo) | Task #128: Triagem UX — Ajustes Candidato (Welcome, Balões, Tom, Whitelabel) — Backend (triagem_sess |
| 🟡 | `e48e1a3f6` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `58a2e5753` | 2026-04-04 | Docs | scope: docs | feat(docs): create Excalidraw ANTES vs DEPOIS architecture diagram for LIA AI system — Task #127 — D |
| 🟡 | `f42e499b7` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `043c12e77` | 2026-04-04 | Outro | Mockup Sandbox (artefato gerado) | Add voice recording button to chat and confirmation screens — Integrate the 'Mic' icon and button co |
| 🟡 | `70ec8fd8d` | 2026-04-04 | Backend | Communication domain (BE) | Add smart routing to direct users to the platform interface — Introduce a smart routing system that  |
| 🔴 | `e8daa86e9` | 2026-04-04 | Cross Back↔Front | §1 Teams Integration | Add a complete chat screening flow to the platform — This commit introduces the full chat screening  |
| 🔴 | `f76917cf9` | 2026-04-04 | Cross Back↔Front | Backend Proxy Routes (FE) | Remove hardcoded company IDs and improve authentication — Replace all instances of hardcoded 'demo_c |
| 🟢 | `8b010f883` | 2026-04-04 | Frontend (UI) | §9 Security / Tenant guards | Address security vulnerabilities by validating redirects and strengthening secret management — Refac |
| 🟢 | `a1b1b395c` | 2026-04-04 | Frontend (UI) | Compliance / LGPD / EU AI Act | task(#120): Remove cookie consent banner from the platform — - Removed `<CookieConsent />` usage fro |
| 🟡 | `44320314c` | 2026-04-04 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `69d0e5e28` | 2026-04-04 | Cross Back↔Front | Unified Chat (FE) | Migrate local storage to Zustand stores and improve daily digest functionality — Replaces remaining  |
| 🟡 | `43b63938a` | 2026-04-04 | Frontend (UI) | Task #121 | feat: Ajustar fonte global e estilo dos balões da LIA (Task #121) — ## Mudanças realizadas |
| 🔴 | `770785e4c` | 2026-04-04 | Cross IA↔Front | Frontend (componentes diversos) | Improve candidate and admin interfaces by cleaning up code — Refactor multiple UI components, remove |
| 🟢 | `9e7423ab9` | 2026-04-04 | Frontend (UI) | Task #119 | feat: remove Progress Dashboard component (Task #119) — - Deleted `plataforma-lia/src/components/set |
| 🔴 | `8571a8686` | 2026-04-04 | Frontend (UI) | Frontend (componentes diversos) | Refactor code to improve component structure and reduce complexity — Remove unused imports and compo |
| 🔴 | `b7af000c1` | 2026-04-04 | Frontend (UI) | Frontend (componentes diversos) | Fix type errors and improve type safety across the application — Address various TypeScript errors a |
| 🟡 | `7de2f7e03` | 2026-04-04 | Frontend (UI) | Frontend (componentes diversos) | Improve code quality by fixing type errors and removing ignored checks — Address numerous TypeScript |
| 🟢 | `96288fccd` | 2026-04-04 | Frontend (UI) | Backend Proxy Routes (FE) | Add API endpoint for fetching context suggestions for the LIA platform — Implement a Next.js API rou |
| 🟢 | `93326741e` | 2026-04-04 | Frontend (UI) | LIA Float UI (FE) | Add quick start suggestions to the chat panel interface — Adds a `handleChipSend` callback and modif |
| 🟢 | `712cb9be0` | 2026-04-04 | Frontend (api/util) | Acessibilidade (a11y) | Improve modal accessibility by enforcing focus within the dialog — Refactor the `useModalA11y` hook  |
| 🟡 | `34008bf0e` | 2026-04-04 | Frontend (UI) | Acessibilidade (a11y) | Task #118: Acessibilidade — Labels, ARIA, Focus Management, Dialog Semantics — Comprehensive accessi |
| 🟢 | `c3a73cd6f` | 2026-04-04 | Frontend (UI) | Acessibilidade (a11y) | Task #118: Acessibilidade — Labels, ARIA, Focus Management e Dialog Semantics — Comprehensive access |
| 🟡 | `16485ec76` | 2026-04-04 | Frontend (UI) | Acessibilidade (a11y) | Task #118: Acessibilidade — Labels, ARIA, Focus Management e Dialog Semantics — Changes across 12 fi |
| 🟡 | `2f3f45e0c` | 2026-04-04 | Frontend (UI) | Acessibilidade (a11y) | Task #118: Acessibilidade — Labels, ARIA e Focus Management — Changes: |
| 🟢 | `8b0564b3b` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🟢 | `aa54798bd` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🟡 | `0162a53c0` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🟡 | `c544eb884` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🟢 | `d2e40a561` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🔴 | `4f1f720f8` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centr |
| 🟢 | `bc4db6926` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization (src/lib |
| 🟡 | `3f6d309f3` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization (src/lib |
| 🟡 | `71a8019b1` | 2026-04-04 | Frontend (UI) | Task #117 | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization: |
| 🟢 | `25a91033e` | 2026-04-04 | Frontend (UI) | Task #116 | Task #116: Zustand State Management - Complete migration — Stores: |
| 🟢 | `d8c16e34b` | 2026-04-04 | Frontend (UI) | Task #116 | Task #116: Zustand State Management - Complete with scoped reset — Auth Store (auth-store.ts): |
| 🔴 | `0a44b6fa0` | 2026-04-04 | Cross Back↔Front | Task #116 | Task #116: Zustand State Management - Complete migration — Auth Store (auth-store.ts): |
| 🟡 | `a800c7f61` | 2026-04-04 | Frontend (UI) | Task #116 | Task #116: Zustand State Management - Complete migration — - Created auth-store.ts, kanban-store.ts, |
| 🟡 | `d431183a4` | 2026-04-04 | Backend | §1 Teams Integration | Add daily digest and feedback for Teams recruiters — Introduce new API endpoints and services for se |
| 🟡 | `0ea776065` | 2026-04-04 | Backend | Task #115 | Task #115: Lazy Loading - Replace () => null loading fallbacks with visible loading states — All dyn |
| 🔴 | `7f946bcf3` | 2026-04-04 | Cross Back↔Front | Task #115 | Task #115: Lazy Loading - Replace () => null loading fallbacks with visible loading states — All dyn |
| 🟡 | `81ce3e554` | 2026-04-04 | Frontend (UI) | Task #115 | Task #115: Lazy Loading + Code Splitting (Modais e Dashboards) — - Created reusable LoadingFallback, |
| 🔴 | `79095dd08` | 2026-04-04 | Cross Back↔Front | Task #112 | Task #112+#113: @ts-ignore elimination + lazy loading + bugfixes — Task #112 - @ts-ignore eliminatio |
| 🟡 | `bbd6738b9` | 2026-04-04 | Backend | Task #112 | Task #112: Complete @ts-ignore batch 2 elimination (10/10 files clean) Task #113: Implement lazy loa |
| 🔴 | `1e1e9971a` | 2026-04-04 | Cross Back↔Front | Task #112 | Task #112: Complete @ts-ignore batch 2 elimination (10/10 files clean) Task #113: Implement lazy loa |
| 🟢 | `22d7b3c46` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟢 | `15de7982f` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟢 | `56dc8a6ce` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟢 | `09d8cd0fb` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟡 | `957024c98` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟡 | `8cae7a14d` | 2026-04-04 | Frontend (UI) | Task #113 | Task #113: Eliminate critical mock data from production code — CHANGES: |
| 🟡 | `e24632178` | 2026-04-04 | Backend | FastAPI v1 endpoints | Task start baseline checkpoint for code review |
| 🟡 | `232905535` | 2026-04-04 | Backend | FastAPI v1 endpoints | Add execution plan details to chat responses for better task tracking — Add an optional `execution_p |
| 🟢 | `cd5dcc969` | 2026-04-04 | Docs | Docs / Auditorias | Update documentation with revised frontend audit scores and detailed analysis — Update `audit-fronte |
| 🟢 | `2902809cb` | 2026-04-03 | Frontend (UI) | Acessibilidade (a11y) | Task #110: Design System + Accessibility + Dead Code cleanup — Changes: |
| 🔴 | `72875a661` | 2026-04-03 | Cross Back↔Front | Acessibilidade (a11y) | Task #110: Design System v4.2.1 + Accessibility + Dead Code cleanup — Changes: |
| 🔴 | `daed87514` | 2026-04-03 | Cross IA↔Front | scope: lia-chat | fix(lia-chat): Round 9 — education_level to lia_insights JSON + PT-BR datetime resolver — Final sema |
| 🔴 | `2eee5c680` | 2026-04-03 | Cross Back↔Front | Frontend (componentes diversos) | Remove type checking errors and improve data handling — Addresses numerous TypeScript errors by remo |
| 🟢 | `38ed869e2` | 2026-04-03 | Frontend (UI) | Task #108 | Task #108: Centralize client-side business logic (scores + pricing) — Created centralized score util |
| 🔴 | `6bfc8dc47` | 2026-04-03 | Cross Back↔Front | Task #108 | Task #108: Centralize client-side business logic (scores + pricing) — Created centralized score util |
| 🟢 | `7ad70055f` | 2026-04-03 | Frontend (UI) | Chat UI (FE) | Task start baseline checkpoint for code review |
| 🟡 | `486e42ef5` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #107: Complete API validation + security hardening — Frontend API routes: |
| 🔴 | `395ad8955` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #107: Complete API validation + security hardening — Frontend API routes: |
| 🔴 | `7a298e6e3` | 2026-04-03 | Cross IA↔Front | Task #107 | Task #107: Complete API validation hardening — Changes: |
| 🔴 | `e4a5d4705` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Complete validation hardening — All review issues fixed: |
| 🔴 | `3597eab4b` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Fix code review issues — Review fixes round 2: |
| 🔴 | `e37a20b4b` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #107: API Security - Zod validation + Security Headers (review fixes) — Review fixes applied: |
| 🔴 | `6b3e4524f` | 2026-04-03 | Cross Back↔Front | §9 Security / Tenant guards | Task #107: API Security - Zod validation + Security Headers — Security Headers: |
| 🟡 | `43b7d5eed` | 2026-04-03 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `ec3ae7b76` | 2026-04-03 | Docs | Task #111 | Task #111: Generate deep frontend optimization report for Plataforma LIA — Creates docs/specs/fronte |
| 🔴 | `f12e35d4a` | 2026-04-03 | Cross IA↔Front | §2 Orchestrator Migration | Improve CV analysis and access control for API endpoints — Update CV matching patterns in orchestrat |
| 🟡 | `a677e1a4a` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session  |
| 🔴 | `7863c72ba` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session  |
| 🔴 | `7396ade2a` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session  |
| 🔴 | `6399beccf` | 2026-04-03 | Cross IA↔Front | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core cha |
| 🟢 | `294e715a5` | 2026-04-03 | Frontend (api/util) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core cha |
| 🟢 | `a819733f7` | 2026-04-03 | Frontend (api/util) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core cha |
| 🟢 | `d7b356005` | 2026-04-03 | Frontend (api/util) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core cha |
| 🟢 | `5e5193458` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == What was |
| 🟡 | `09f8e569a` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == What was |
| 🟢 | `683eb4a5f` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #105: Security P0 — Credentials, XSS, Fake URLs (complete) — 1. login-page.tsx (LEGACY, @deprec |
| 🟢 | `aef93de0f` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #105: Security P0 — Credentials, XSS, Fake URLs (complete) — 1. login-page.tsx (LEGACY, @deprec |
| 🟢 | `14de36a58` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #105: Security P0 fixes — Credentials, XSS, Fake URLs — 1. login-page.tsx: Removed ALL hardcode |
| 🟢 | `b4dc63108` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #105: Security P0 fixes — Credentials, XSS, Fake URLs — 1. login-page.tsx: Removed ALL hardcode |
| 🟡 | `ca39755a3` | 2026-04-03 | Frontend (UI) | §9 Security / Tenant guards | Task #105: Security P0 fixes — Credentials, XSS, Fake URLs — 1. login-page.tsx: Removed ALL hardcode |
| 🟢 | `7615042b0` | 2026-04-03 | Docs | §9 Security / Tenant guards | Create a structured work plan for frontend audit and security fixes — Adds a new markdown document d |
| 🟢 | `b30dd9be4` | 2026-04-03 | Docs | §9 Security / Tenant guards | Add a comprehensive frontend audit document detailing security and quality issues — Creates a detail |
| 🟢 | `abd597571` | 2026-04-03 | Docs | Docs / Specs | Update documentation and benchmarks with recent test results — Apply fixes to improve scoring accura |
| 🔴 | `f059b6786` | 2026-04-03 | Cross IA↔Front | Docs / Specs | Improve job preview and communication channel appearance — Updates UI components to fix visual discr |
| 🔴 | `0882a4580` | 2026-04-03 | Cross IA↔Front | §2 Orchestrator Migration | Align job preview panel with candidate preview design system — Fixes background, border, and badge f |
| 🟢 | `80fc294b9` | 2026-04-03 | Frontend (UI) | UI Components (FE library) | Remove incomplete setup progress badge from application interface — Remove the SetupAlertBadge compo |
| 🔴 | `9338f7773` | 2026-04-03 | Cross Back↔Front | Docs / Specs | Fix infinite loop in chat component state management — Wrap reset functions in useCallback to preven |
| 🟢 | `ebc3c3a3b` | 2026-04-03 | Docs | Compliance / LGPD / EU AI Act | Update fairness reports with new data and error handling — Modify CSV and JSON files for fairness re |
| 🟢 | `2e58eb7ad` | 2026-04-03 | Docs | Docs / Screenshots | Update screenshots for login and 2FA process — Update screenshots to reflect the final state of the  |
| 🟢 | `1657ad17c` | 2026-04-03 | Docs | Docs / Screenshots | Update screenshots showing successful code input — Update screenshots to demonstrate successful inpu |
| 🟢 | `08968515a` | 2026-04-03 | Docs | Docs / Specs | Update login script to use direct value setting with event dispatching for two-factor authentication |
| 🟢 | `d67a75dd3` | 2026-04-03 | Docs | Docs / Screenshots | Update screenshots for user login and 2FA process — Update screenshots to reflect changes in the use |
| 🟢 | `84795ebf8` | 2026-04-03 | Docs | Compliance / LGPD / EU AI Act | Add fairness report data to the QA documentation — Update CSV and JSON files with fairness report da |
| 🟡 | `4f55a46ee` | 2026-04-03 | Docs | Docs / Screenshots | Update scripts to handle website login and two-factor authentication flow — Refactor and add new Pyt |
| 🟡 | `195825178` | 2026-04-03 | Docs | Docs / Specs | Update login flow to handle WeDOTalent's direct 2FA authentication — Refactors `capture-wedo-ms-logi |
| 🟢 | `ca61a48f1` | 2026-04-03 | Docs | Compliance / LGPD / EU AI Act | Update fairness reports with new latency and connection error data — Updates fairness reports in CSV |
| 🟢 | `c82e55f57` | 2026-04-03 | Docs | Docs / Specs | Update benchmark tests and documentation to reflect current API and features — Update benchmark test |
| 🟢 | `a9be7a167` | 2026-04-03 | Docs | Docs / Auditorias | Add layout and spacing issues to the audit document — Adds new Vue bugs (VUE-BUG-06, VUE-BUG-07, VUE |
| 🟢 | `dd0d71b9c` | 2026-04-03 | Docs | Docs / Auditorias | Update audit document with new bugs and screenshots — Adds new bugs to the audit document, updates p |
| 🟢 | `73f3bfae0` | 2026-04-03 | Docs | Docs / Auditorias | Update audit document with new candidate screenshots and identified issues — Adds 15 new candidate s |
| 🟢 | `6b5d6a630` | 2026-04-03 | Testes | Compliance / LGPD / EU AI Act | Update candidate scoring to include job vacancy and question details — Modify the payload structure  |
| 🟢 | `32bf87468` | 2026-04-03 | Testes | §15 WSI | Update test script to align with new API specifications for candidate analysis — Modify the patch_fa |
| 🟢 | `8f01fa6d5` | 2026-04-03 | Docs | Docs / Auditorias | Implement direct API login to bypass multi-factor authentication — Introduce a bash script to perfor |
| 🔴 | `1a59d95d2` | 2026-04-03 | Testes | Docs / Specs | Update login and 2FA process to handle custom input components — Modify the authentication flow to s |
| 🟢 | `24d8f4abf` | 2026-04-03 | Docs | Docs / Auditorias | Add login functionality and capture candidate screenshots for review — Update scripts to handle WeDO |
| 🟢 | `3a4243904` | 2026-04-03 | Docs | Docs / Auditorias | Add script to capture screenshots of product previews — Implement Playwright script to capture scree |
| 🟢 | `04be87e96` | 2026-04-03 | Docs | Docs / Auditorias | Update audit document with detailed candidate preview information — Refactor the audit-candidate-pre |
| 🟢 | `6ede754b1` | 2026-04-03 | Docs | Docs / Auditorias | Add detailed documentation for the file upload tab — Update audit-candidate-preview-qa.md to include |
| 🟢 | `903c02afd` | 2026-04-03 | Docs | Docs / Auditorias | Update audit document to include restructured content and detailed findings — Restructure the audit  |
| 🟢 | `c4a7d0540` | 2026-04-03 | Docs | Mockup Sandbox (artefato gerado) | Consolidate audit and code comparison documents into a single comprehensive report — Merge the deep  |
| 🟢 | `7c742d925` | 2026-04-03 | Docs | Docs / Auditorias | Add detailed comparison of candidate preview features — Create a deep code-to-code comparison docume |
| 🟡 | `f88c929ed` | 2026-04-03 | Outro | Mockup Sandbox (artefato gerado) | Update component mapping for the ElevenLabs funnel — Update the dynamic import mapping in mockup-com |
| 🟢 | `44ed2241e` | 2026-04-03 | Docs | Auditoria / Audit Rev | QA Audit: Candidate Preview Panel - Production vs Replit Reference — Complete rewrite of audit docum |
| 🟡 | `f9471e961` | 2026-04-03 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `b9d9a070d` | 2026-04-03 | Frontend (UI) | Chat UI (FE) | Fix issues with loading, image display, and search cancellation — Addresses an infinite loading bug  |
| 🟡 | `975e0d586` | 2026-04-03 | Outro | Docs / Auditorias | Add automated login and initial page navigation for the website — Implement Playwright automation sc |
| 🟢 | `0a332b1ea` | 2026-04-03 | Frontend (UI) | Task #103 | Task #103: Ajustar fonte do placeholder para 12px — Changed placeholder font size from text-base-ui  |
| 🟢 | `e213cf2ec` | 2026-04-03 | Frontend (UI) | Candidates (FE pages) | Align search results header and controls into a single unified toolbar — Unify the Brain prompt, sea |
| 🟢 | `1fa2c5b9a` | 2026-04-03 | Frontend (UI) | Candidates (FE pages) | Align search results header and LIA prompt horizontally — Move the LIA prompt button to the same lin |
| 🟢 | `3d0e70836` | 2026-04-03 | Frontend (UI) | Candidates (FE pages) | Replace LIA input fields with a unified brain button component — Replaces various LIA input fields a |
| 🟢 | `673c6e79c` | 2026-04-03 | Frontend (UI) | Task #102 | Task #102: Corrigir Dark Mode — Contraste e Visibilidade (v2) — 1. LoginClient.tsx — Added dark: var |
| 🟢 | `17fdb8833` | 2026-04-03 | Frontend (UI) | Candidates (FE pages) | Update tab styling for consistent user interface appearance — Adjust border-radius and color classes |
| 🟢 | `3ea622192` | 2026-04-03 | Frontend (UI) | Frontend (componentes diversos) | Update job management buttons to match talent funnel appearance — Modify inline button styles in `jo |
| 🟢 | `78b1f7b11` | 2026-04-03 | Frontend (UI) | Jobs (FE pages) | Adjust button styles for a consistent visual appearance across the platform — Update border-radius f |
| 🟢 | `1ac0f4180` | 2026-04-03 | Frontend (UI) | Jobs (FE pages) | Update buttons to match design specifications for consistency — Adjusted button styles in `JobsDashb |
| 🟢 | `2820e5cb2` | 2026-04-03 | Frontend (UI) | Jobs (FE pages) | Update job management buttons to match talent funnel style — Refactor styling of buttons in JobsDash |
| 🟢 | `d52bd07e7` | 2026-04-03 | Frontend (UI) | UI Components (FE library) | Align button styles across job and query components for visual consistency — Update button classes i |
| 🟢 | `c9346b477` | 2026-04-03 | Frontend (UI) | UI Components (FE library) | Standardize button styles across different sections for a consistent look — Modify CSS classes and r |
| 🟢 | `bd6c8ebbf` | 2026-04-03 | Frontend (UI) | Search (FE) | Update search input focus style to use a neutral outline — Modify the focus style of the search inpu |
| 🟢 | `fe5da36e4` | 2026-04-03 | Frontend (UI) | Jobs (FE pages) | Align job buttons and containers visually with talent funnel elements — Update the background and pa |
| 🟢 | `dd9afe6e3` | 2026-04-03 | Frontend (UI) | Jobs (FE pages) | Align visual styles for buttons and search icons across the platform — Update CSS classes and compon |
| 🟢 | `eb2c0e494` | 2026-04-03 | Frontend (UI) | UI Components (FE library) | Apply consistent styling and transitions to various interactive elements — Refactor CSS classes and  |
| 🟢 | `dfccecc1f` | 2026-04-03 | Frontend (UI) | Search (FE) | Update search interface to use rounded corners and bordered styles — Adjusted search input tabs, ent |
| 🟢 | `3de3145ad` | 2026-04-03 | Frontend (UI) | Configurações (hub) | Improve spacing consistency between recruitment pipeline cards — Update spacing in RecruitmentJourne |
| 🟢 | `04d56a02e` | 2026-04-03 | Frontend (UI) | Configurações (hub) | Remove unnecessary import sections from settings pages — Removes the "Importar Departamentos" and "I |
| 🟢 | `cec051c3d` | 2026-04-03 | Frontend (UI) | Login UI (FE) | Add a new onboarding flow explaining the recruitment process — Introduce a multi-step animation deta |
| 🟢 | `3884f46fc` | 2026-04-03 | Frontend (UI) | Login UI (FE) | Improve visibility and layout of login page elements — Adjust subtitle text styles for better readab |
| 🟢 | `cd550ec7e` | 2026-04-03 | Frontend (UI) | Login UI (FE) | Restore original login page design with two-step authentication flow — Reverts the login page to its |
| 🟢 | `85ab54bf3` | 2026-04-03 | Frontend (UI) | Login UI (FE) | Restore full login page with cloud background and SSO options — Update `LoginClient.tsx` to use the  |
| 🟡 | `bef96a22a` | 2026-04-03 | Frontend (UI) | Task #101 | fix: Corrigir contraste dark mode — legibilidade completa (Task #101) — ## Summary |
| 🟢 | `9151587fd` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Prevent hydration errors by deferring component rendering — Defer the mounting of the Popover compon |
| 🟢 | `9b1061bb2` | 2026-04-02 | Frontend (UI) | Task #100 | Task #100: Auditoria e Enxugamento do Admin — Mapa de 61 Páginas para Decisão — Audited all 61 admin |
| 🟢 | `0d2aba6ff` | 2026-04-02 | Frontend (UI) | Task #99 | Task #99: Fix runtime errors after dark mode migration — Root cause: Lucide React icons are `forward |
| 🟢 | `ff8b4a8b7` | 2026-04-02 | Docs | Design System v4.2.2 | Clarify audit results in documentation regarding design token migration — Update replit.md to accura |
| 🟢 | `f02e873dd` | 2026-04-02 | Docs | Task #98 | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+  |
| 🟢 | `93ef4cf05` | 2026-04-02 | Frontend (UI) | Task #98 | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+  |
| 🔴 | `213adc816` | 2026-04-02 | Frontend (UI) | Task #98 | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+  |
| 🔴 | `fe4b665cb` | 2026-04-02 | Frontend (UI) | Task #98 | Task #98: Migração completa de tokens de contraste — Etapa 4 — Migração abrangente de ~505 arquivos  |
| 🟢 | `dc8a00f97` | 2026-04-02 | Frontend (UI) | WSI components (FE) | Improve interactive element styling and remove duplicate hover effects — Update CSS classes in vario |
| 🔴 | `d5da8ed30` | 2026-04-02 | Frontend (UI) | Task #97 | Task #97: Migração tokens contraste - Etapa 3: Features Core — Migração completa de classes Tailwind |
| 🟢 | `aa44c367d` | 2026-04-02 | Frontend (UI) | Task #96 | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design token |
| 🟡 | `c7b1b18cc` | 2026-04-02 | Frontend (UI) | Task #96 | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design token |
| 🟢 | `8bd044060` | 2026-04-02 | Empty/merge | Task #96 | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design token |
| 🟡 | `7671ac38e` | 2026-04-02 | Frontend (UI) | Task #96 | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design token |
| 🟡 | `e52bccbeb` | 2026-04-02 | Frontend (UI) | Task #96 | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Migrados todos os 10 a |
| 🟡 | `190d2fb8a` | 2026-04-02 | Frontend (UI) | UI Components (FE library) | Task start baseline checkpoint for code review |
| 🔴 | `8d7840bc3` | 2026-04-02 | Frontend (UI) | scope: design-system | feat(design-system): Etapa 1 — migração tokens contraste em components/ui/ — Substituição completa d |
| 🟡 | `6698b6083` | 2026-04-02 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🟡 | `c11c4ef98` | 2026-04-02 | Outro | Mockup Sandbox (artefato gerado) | Update component map to include FunilElevenLabs and Tab2Pendente — Modify `mockup-components.ts` to  |
| 🟢 | `842e0b17a` | 2026-04-02 | Frontend (UI) | Candidates (FE pages) | Add new options to the bulk actions bar and update search view imports — Update `CandidateSearchResu |
| 🟡 | `a0635bed8` | 2026-04-02 | Frontend (UI) | Task #93 | Task #93: Unify 4 bulk selection bar components into 1 BulkActionsBar — Created new unified `BulkAct |
| 🟡 | `c99559440` | 2026-04-02 | Frontend (UI) | Task #93 | Task #93: Unify 4 bulk selection bar components into 1 BulkActionsBar — Created new unified `BulkAct |
| 🟢 | `d0916069b` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Update selection bars to display a white background in the interface — Adjusted the background color |
| 🟢 | `d1b0ff4b1` | 2026-04-02 | Frontend (UI) | UI Components (FE library) | Update component backgrounds to white for better visibility — Adjusted background colors of `BulkSel |
| 🟢 | `cda55c611` | 2026-04-02 | Docs | Task #92 | Task #92: Deep audit and update of INVENTARIO_COMPONENTES.md — Documentation-only changes to align w |
| 🟢 | `19cf22c56` | 2026-04-02 | Frontend (UI) | Task #91 | Task #91: Unify toast system — migrate all Radix/shadcn toasts to Sonner with richColors — - Removed |
| 🔴 | `6bd155d9d` | 2026-04-02 | Frontend (UI) | Task #91 | Task #91: Unify toast system — migrate all Radix/shadcn toasts to Sonner with richColors — - Removed |
| 🟡 | `9913729ba` | 2026-04-02 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `f5bdc4fc4` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Adjust profile dropdown menu text size to 12px — Updates the font size for user's name and menu item |
| 🟢 | `512093527` | 2026-04-02 | Frontend (UI) | Jobs (FE pages) | Update job candidate display to use standard tooltip component — Replaces custom CSS tooltip with Ra |
| 🟢 | `bbccd9f2e` | 2026-04-02 | Frontend (UI) | Acessibilidade (a11y) | Update job listing details and improve accessibility of job titles — Update the product design inven |
| 🟢 | `1dffd31aa` | 2026-04-02 | Docs | Configurações (hub) | Update FRONTEND_INVENTORY_v1.md with accurate filesystem counts — Corrected all outdated counts and  |
| 🟢 | `2262da5b5` | 2026-04-02 | Docs | Docs / WeDO planos | Update project inventory to reflect actual codebase structure — Create a new audit file detailing di |
| 🟢 | `6eec07914` | 2026-04-02 | Docs | Docs / WeDO planos | Update inventory document with accurate component counts and paths — Corrected UI component count in |
| 🟢 | `46080ebd4` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Refactor metric card component to reduce code duplication — Update MetricCard component to accept a  |
| 🟡 | `cc4a95dba` | 2026-04-02 | Frontend (UI) | Search (FE) | Unify search preset modals into a single generic component — Consolidates Company, Location, and Uni |
| 🟡 | `7cc0e514b` | 2026-04-02 | Outro | Mockup Sandbox (artefato gerado) | Add FunilElevenLabs component to the mockups — Adds './components/mockups/funil-elevenlabs/FunilElev |
| 🟡 | `0253ef10c` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Improve UI consistency and code organization across the application — Refactor components to use sha |
| 🟢 | `40a3ea3e5` | 2026-04-02 | Frontend (UI) | Search (FE) | Fix runtime errors to allow the platform to run correctly — Correct an import statement issue in Com |
| 🟢 | `6a5ec5aa3` | 2026-04-02 | Frontend (UI) | Candidates (FE pages) | Correct import statements that were incorrectly grouped — Fix incorrect import statements in LIASear |
| 🟡 | `098d563f1` | 2026-04-02 | Frontend (UI) | Frontend (componentes diversos) | Fix import order and incomplete JSX in profile components — Corrected import statements in multiple  |
| 🟡 | `da4901994` | 2026-04-02 | Frontend (UI) | Sprint S | refactor: component unification across 5 sprints — - Remove 2 orphan components (lia-activity-feed,  |
| 🟢 | `784946f1d` | 2026-04-02 | Frontend (UI) | UI Components (FE library) | Align table appearance and candidate avatar sizes across the platform — Adjust avatar sizes in Candi |
| 🟢 | `ee0a5fb30` | 2026-04-02 | Frontend (UI) | UI Components (FE library) | Align styles and appearance across all candidate tables — Update CSS and markup in `candidate-table- |
| 🟢 | `0a1122876` | 2026-04-02 | Frontend (UI) | Candidates (FE pages) | Align talent funnel table with job listings for consistent appearance — Adjust padding, checkbox com |
| 🟢 | `1c4c56051` | 2026-04-02 | Frontend (UI) | Candidates (FE pages) | Change header background color to white — Update the `SearchResultsHeader.tsx` component to change t |
| 🟢 | `36e023f61` | 2026-04-02 | Frontend (api/util) | Design System v4.2.2 | Update font size token to ensure consistency — Adjusted the `--font-size-xs` CSS token from 11px to  |
| 🟢 | `f83e6052d` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Add a bottom border to the jobs table header for better separation — Update the jobs table header to |
| 🟢 | `9deb5bf28` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Improve table header separation with a subtle shadow effect — Adjusted JobsCompactTableView.tsx to u |
| 🟢 | `fbf5eb4af` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Add a bottom border to the table header for better visual separation — Move the bottom border from t |
| 🟢 | `77d2f69b5` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Add a bottom border to the table header to separate it from the content — Update JobsCompactTableVie |
| 🟢 | `b71007d60` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Improve table layout by adjusting container height — Update the table container's height property fr |
| 🟢 | `5f328c435` | 2026-04-01 | Frontend (UI) | Jobs (FE pages) | Add border around the table of job opportunities — Add a border and rounded corners to the jobs tabl |
| 🟢 | `15aea510d` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Improve table readability by adding subtle borders between rows — Add subtle bottom borders to table |
| 🟢 | `79ed5502d` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Update menu backgrounds to a lighter shade for improved readability — Adjust UI components to replac |
| 🟢 | `78a569d92` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Update job detail page to remove unnecessary borders and update tab styles — Refactor JobKanbanPage, |
| 🟢 | `cf2df9691` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Remove borders from the candidates table to match the jobs table — Remove borders and background col |
| 🟢 | `7782192f4` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Align job and candidate tabs with design system — Import and apply `tabStyles.pillActive` and `tabSt |
| 🟢 | `9a9191215` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Update tab styling to fully rounded design — Adjusted the `rounded-lg` class to `rounded-full` in `C |
| 🟡 | `28d77cffb` | 2026-04-01 | Frontend (UI) | Frontend (componentes diversos) | Update UI elements to a modern pill-shaped tab style — Refactors various components to replace horiz |
| 🟡 | `3568a69cb` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Update page backgrounds to white for a cleaner interface — Replaces `bg-gray-50` with `bg-white` in  |
| 🟡 | `0c8be0403` | 2026-04-01 | Frontend (UI) | Frontend (componentes diversos) | Update page backgrounds to white across the entire application — Replaced `bg-gray-50` with `bg-whit |
| 🟡 | `2dc9d6d67` | 2026-04-01 | Outro | Mockup Sandbox (artefato gerado) | Add a visual mockup of the talent funnel page using Eleven Labs design — Create a new mock component |
| 🟢 | `8ed926359` | 2026-04-01 | Frontend (UI) | Frontend (componentes diversos) | Fix error causing the application to crash when navigating job views — Move useMemo hook to ensure c |
| 🟢 | `a84040218` | 2026-04-01 | Frontend (api/util) | DevOps / Deploy (Docker/GCP) | Add UI avatars to image hosting configuration — Update next.config.js to include ui-avatars.com in a |
| 🟡 | `323a76519` | 2026-04-01 | Outro | Skills / canonical-fix | Complete the Vue Vuetify standardization skill for independent operation — Rewrite the vue-vuetify-s |
| 🟢 | `02131244a` | 2026-04-01 | Empty/merge | Skills / canonical-fix | Rewrite vue-vuetify-standardize skill to be 100% self-contained — - Removed all references to extern |
| 🟢 | `6aa487c13` | 2026-04-01 | Frontend (UI) | Configurações (hub) | Add missing icons to display benefits information correctly — Import the `Percent` and `Info` icons  |
| 🟢 | `69bca4528` | 2026-04-01 | Docs | Docs / Refactor | docs: fix MIGRATION_READINESS — files >1000L is 3 not 1 (design-tokens.css grew, useExpandedChatModa |
| 🟢 | `8bd407e84` | 2026-04-01 | Frontend (UI) | §6 Chat Unificado / Funil | fix(typescript): resolve residual type errors in FunilDeTalentosClient, candidate-modal, ScreeningQu |
| 🟢 | `4a6a078e5` | 2026-04-01 | Docs | Docs / Refactor | docs: MIGRATION_READINESS.md score 69/70 checklist context-store map risks |
| 🟡 | `a1e4ab982` | 2026-04-01 | Frontend (UI) | scope: eslint | fix(eslint): resolve remaining errors — 0 errors target achieved |
| 🔴 | `71ca5412f` | 2026-04-01 | Frontend (UI) | scope: eslint | fix(eslint): wrap JSX comment text nodes — 61 react/jsx-no-comment-textnodes errors → 0 |
| 🟡 | `9ef73964f` | 2026-04-01 | Frontend (UI) | scope: quality | fix(quality): migrate auth-context imports to canonical path + remove orphan GoalsPlanningHub |
| 🟡 | `a52de9144` | 2026-04-01 | Frontend (UI) | Skills / canonical-fix | Add new skill for standardizing Vue and Vuetify components — Introduce a new skill for Vue/Vuetify s |
| 🟡 | `843ca5f04` | 2026-04-01 | Frontend (UI) | scope: quality | fix(quality): remove dead code + duplicate imports + unused vars — - Remove unused lucide-react icon |
| 🟢 | `2bdf4731a` | 2026-04-01 | Frontend (UI) | Performance | perf: lazy loading e bundle optimization — - indicators-page: dynamic import para StrategicTab, Recr |
| 🟢 | `8a24f2de1` | 2026-04-01 | Frontend (api/util) | scope: design | fix(design): layout + shadow tokens replace arbitrary values — - Audit: 0 arbitrary shadows (already |
| 🔴 | `8a229d0d1` | 2026-04-01 | Frontend (UI) | scope: design | fix(design): typography scale + z-index semantic tokens replace arbitrary values |
| 🟢 | `da6cdd9bd` | 2026-04-01 | Frontend (UI) | scope: design | fix(design): replace arbitrary spacing values with Tailwind scale equivalents |
| 🟢 | `1dbc3592a` | 2026-04-01 | Frontend (UI) | Bridge React→Vue | feat(bridge): document TSX hooks refactor list + convert 4 false-positive hooks to .ts — - Rename 4  |
| 🟢 | `c5b2a396f` | 2026-04-01 | Frontend (UI) | Bridge React→Vue | feat(bridge): convert hooks .tsx->ts + add context-store map to vue-bridge |
| 🟢 | `3e94c0928` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): resolve type mismatches from Phase 6 splits |
| 🟡 | `db8a19604` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): preventive splits for borderline files (990-997L) |
| 🟢 | `a552d5660` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): split useCandidatesPageCore into domain hooks |
| 🟢 | `36214ec8b` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): resolve final 4 @ts-nocheck files — 269 → minimum necessary |
| 🔴 | `d1c58f11a` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from components <=600L |
| 🔴 | `b6eaf7998` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from large components (>600L) + fix type errors |
| 🔴 | `80bcdf8a5` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from lib/types/services/small components |
| 🟡 | `c8472b613` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from large hooks (500-1000L) + fix exposed types — - Removed @ts |
| 🔴 | `c28bc08ee` | 2026-04-01 | Cross IA↔Front | Compliance / LGPD / EU AI Act | Improve system compliance and fix runtime errors in frontend components — Implement enhancements to  |
| 🔴 | `4e1427281` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from context panels + small pages |
| 🟡 | `f68a2e13c` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from 18 API proxy routes |
| 🟡 | `4c0b24059` | 2026-04-01 | Frontend (UI) | scope: typescript | fix(typescript): remove @ts-nocheck from small hooks + fix exposed type errors — Remove @ts-nocheck  |
| 🟢 | `6453e744c` | 2026-04-01 | Frontend (UI) | Wizard (geral) | fix(typescript): remove @ts-nocheck from WizardContext -- resolve type errors |
| 🟢 | `c21a36ca0` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): phase 4 residual — badge tokens audit + onboarding CSS + final hex sweep — - status-bad |
| 🟢 | `389cd1774` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): tasks-page + AlertsTab — inline styles to tokens |
| 🟢 | `d2a095e08` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): strategic-dashboard + search-preview-card + useChatSession — remove hex fallbacks |
| 🟢 | `b67cea7a4` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): task-helpers.tsx - convert inline styles to Tailwind classes |
| 🟢 | `00aa40b26` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): fix var(--lia-) truncated bug + add --chat-cyan alias + add --gray-700 |
| 🟢 | `f52f5ee31` | 2026-04-01 | Frontend (UI) | scope: tokens | fix(tokens): replace hardcoded hex in animations.css + components.css with CSS vars |
| 🟢 | `d4b664af3` | 2026-04-01 | Frontend (api/util) | scope: tokens | fix(tokens): add wedo-amber-light/green-light to tailwind + remove @ts-nocheck |
| 🟢 | `01ae871c0` | 2026-04-01 | Frontend (api/util) | scope: tokens | fix(tokens): add --lia-text-inverted alias + verify dark mode coverage |
| 🟢 | `3e260646e` | 2026-04-01 | Frontend (api/util) | scope: env | docs(env): add .env.example with all required variables and documentation |
| 🟢 | `6555511c7` | 2026-04-01 | Frontend (api/util) | scope: build | fix(build): remove ignoreBuildErrors + ignoreDuringBuilds — Sprint 9 completed |
| 🟢 | `5a8b47afc` | 2026-04-01 | Frontend (UI) | scope: eslint | fix(eslint): 3 erros eliminados — nested useEffect + imports PauseOptionsStep/ActivateOptionsStep —  |
| 🟢 | `aed26a917` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Update compliance guide to reflect current system capabilities and fixes — Refactor `WeDO/guias/GUIA |
| 🟢 | `a8fe6cfb9` | 2026-04-01 | Docs | scope: audit | docs(audit): v8 FINAL — 62/70 (88%) \| Architecture 5/5, Testing 4/5, SEO 5/5 \| 0 arquivos >1kL, 50 t |
| 🟢 | `3b368d583` | 2026-04-01 | Frontend (UI) | scope: ts | fix(ts): @ts-nocheck on useExpandedChatModalCore — type mismatch from extracted useConversationMemor |
| 🟢 | `fb271416b` | 2026-04-01 | Frontend (UI) | scope: seo | feat(seo): add generateMetadata() to 24 key pages — SEO Score 4→5 — - Convert page.tsx files to serv |
| 🟢 | `65af36722` | 2026-04-01 | Frontend (UI) | Talent Funnel (FE) | Update job and vacancy pages and refine candidate profile — Adjusts routing and component rendering  |
| 🟢 | `4b9e8c24e` | 2026-04-01 | Docs | Task #90 | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors acro |
| 🟢 | `2f3dffbad` | 2026-04-01 | Docs | Task #90 | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors acro |
| 🟢 | `abde32ef8` | 2026-04-01 | Frontend (UI) | Task #90 | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors acro |
| 🟢 | `5aa3c8fc1` | 2026-04-01 | Frontend (UI) | Task #90 | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors acro |
| 🟢 | `1fe5ffa36` | 2026-04-01 | Frontend (UI) | Task #90 | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 20 errors acro |
| 🟢 | `21e5b4a1a` | 2026-04-01 | Frontend (UI) | Task #90 | Task #90: Deep audit and correction of migration guide v2.2 → v2.3 — Audit findings (20 errors corre |
| 🟢 | `7af222695` | 2026-04-01 | Frontend (UI) | Task #90 | Task #90: Deep audit and correction of migration guide v2.2 → v2.3 — Audit findings (20 errors corre |
| 🟢 | `41970fc81` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | refactor(arch): extract modal state and column config from useKanbanPageCore below 1000L — - useKanb |
| 🟡 | `c7b57ee2f` | 2026-04-01 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `61b082ddb` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Update application pages and core logic for enhanced user experience — Refactor client-side logic an |
| 🔴 | `ab5a813b7` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Add page metadata and client components for improved application structure — Add metadata to various |
| 🟡 | `e6c0ce72d` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): reduce useEAPCallbacks and useExpandedChatModalCore below 1000L |
| 🟡 | `55045840b` | 2026-04-01 | Frontend (api/util) | Kanban (vagas) | test: add 12 unit test files for utils, hooks, and components (38→50+ test files) — New test files a |
| 🟢 | `0cbe0ff75` | 2026-04-01 | Docs | §9 Security / Tenant guards | docs(audit): v7 — 59/70 (84%) \| Architecture 2→4, Security 4→5, Bridge 3→4 \| 39→5 arquivos >1kL |
| 🟢 | `a849e3b8b` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): reduce modern-conversations and CandidatesFilterPanel below 1000L |
| 🟢 | `88e3ddbfc` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): extract sub-hooks from useExpandedChatModalCore and useEAPCallbacks |
| 🟡 | `11ee7c473` | 2026-04-01 | Outro | Refactor / Cleanup | chore: remove accidental =350 file |
| 🟡 | `1ec46c597` | 2026-04-01 | Frontend (UI) | Triagem (módulo) | refactor(arch): reduce last borderline files below 1000L (prompts, CandidateSearchResultsView, JobEd |
| 🟢 | `5bfff47b2` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): extract sub-hooks from useSendMessageHandlers and useExpandedChatModalCore |
| 🟢 | `3762d311c` | 2026-04-01 | Frontend (UI) | scope: ts | fix(ts): restore CandidatesFilterPanel.tsx truncated by dedup agent — 0 TS errors |
| 🟢 | `aed2ee874` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Reformat Mapa de Aproveitamento tables in migration guide v2.2 — Both Compliance (P2-P7) and Quality |
| 🟢 | `baa107ed0` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Update compliance guide to reflect incomplete services and domain cleanup — Updates the compliance m |
| 🟢 | `9cf142ce0` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Add more detailed explanations for compliance gaps — Update the "Gap real" column in the compliance  |
| 🟢 | `43f903c58` | 2026-04-01 | Docs | Docs / WeDO planos | Update migration guide to reflect new version and refined estimates — Refactors the migration guide  |
| 🟢 | `51d4141d0` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Update candidate filtering interface with new placement and registration date options — Refactor Can |
| 🟢 | `8e1e0403c` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Reorganize problem and sub-problem details for clarity — Refactor compliance and quality problem sec |
| 🟢 | `7ae0ddd5d` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Update problem severity and formatting in migration guide — Adjusted problem severities to 'Critical |
| 🟢 | `4fe4eedfb` | 2026-04-01 | Frontend (UI) | Compliance / LGPD / EU AI Act | Restructure guide v2.1: full reorganization + expand to 13 problems + 24 sub-problems — Major restru |
| 🟢 | `64c5e9f69` | 2026-04-01 | Docs | Docs / WeDO planos | Improve document structure and fix formatting errors — Update document version to 2.0 and restructur |
| 🟢 | `bb6597a1c` | 2026-04-01 | Frontend (UI) | Candidates (FE pages) | Update candidate search view and filter panel components — Refactor CandidateSearchResultsView to re |
| 🟢 | `99d6a115b` | 2026-04-01 | Docs | Docs / WeDO planos | Add detailed routing and domain inventory analysis for LIA and v5 — Updates the migration guide to i |
| 🟢 | `38c7cd2bb` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): decompose admin pages, job-status-modal steps, lia-screening-guide |
| 🟡 | `7081386fa` | 2026-04-01 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `60ad6e82d` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): split chat-page constants, goals-management, CompanyDataSection, JobEditTab |
| 🟡 | `db9dfae7b` | 2026-04-01 | Frontend (UI) | scope: ts | fix(ts): repair agent-introduced errors — duplicate imports, missing AlertCircle, broken return valu |
| 🟡 | `669494b28` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): reduce borderline large files below 1000L (JDEvaluationPanel, GoalsPlanningHub, Cand |
| 🟡 | `284558a7f` | 2026-04-01 | Frontend (UI) | Triagem (módulo) | Clarify and specify code locations for backend processes and services — Refactor the documentation t |
| 🟢 | `b113c7cff` | 2026-04-01 | Docs | Compliance / LGPD / EU AI Act | Add explanations for compliance services in the migration guide — Added an "O que é" column to the P |
| 🟡 | `74b660e1c` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Update application to improve candidate data organization and analysis — Refactor candidate preview  |
| 🟡 | `65aa73180` | 2026-04-01 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `a2447576a` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): extract sub-components from JDEvaluationPanel and tasks-page — - JDEvaluationPanel ( |
| 🟡 | `b3d3b14f4` | 2026-04-01 | Frontend (UI) | scope: arch | refactor(arch): extract sub-components from JobEditTab, expandable-ai-prompt, BenefitsTab (2nd pass) |
| 🟢 | `311758d20` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | refactor(arch): split job-kanban-page and new-candidate-unified-modal — Extract KanbanToolbar from j |
| 🟢 | `2cdad7231` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | refactor(arch): split KanbanColumnRenderer and KanbanTableView into focused sub-components — - Kanba |
| 🟢 | `b0d15aec9` | 2026-04-01 | Frontend (UI) | Kanban (vagas) | Remove unnecessary closing div tag from status badge component — Remove a redundant closing div tag  |
| 🟢 | `ea4694daf` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | Task start baseline checkpoint for code review |
| 🟢 | `f746e4307` | 2026-03-31 | Frontend (UI) | Docs / WeDO planos | Add executive diagnosis of current structural problems in the system — Add a new "Executive Diagnosi |
| 🟢 | `8a492d846` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | Improve job board display by adding status badges — Update component to render status badges and adj |
| 🟡 | `e5a26e80d` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #87: Comprehensive review and expansion of GUIA_MIGRACAO_V5_COMPLIANCE.md — Major additions (v1 |
| 🟢 | `64ef5b1cb` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | Add didactic FAQ section to migration guide and update UI components — Adds a new FAQ section to the |
| 🟡 | `4573d85da` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `326804725` | 2026-03-31 | Frontend (UI) | scope: arch | refactor(arch): decompose CandidateSearchResultsView and candidate-page into focused components |
| 🟢 | `7f2ff21cc` | 2026-03-31 | Frontend (UI) | Candidates (FE pages) | Improve candidate page interactions and add migration guide — Update candidate page to enable email  |
| 🟡 | `cfb058ab4` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `46f637841` | 2026-03-31 | Frontend (UI) | scope: arch | refactor(arch): extract sub-components from BenefitsTab, DepartmentsTab, job-status-modal |
| 🟢 | `4b1d2816c` | 2026-03-31 | Frontend (UI) | Bridge React→Vue | fix(bridge): replace hardcoded hex with LIA design tokens in task-helpers, tasks-page, search-previe |
| 🟢 | `15435fae5` | 2026-03-31 | Frontend (UI) | §9 Security / Tenant guards | fix(security): sanitize onHighlightSearchTerm output in ChatMessageList — defense-in-depth XSS guard |
| 🟢 | `bde2a3327` | 2026-03-31 | Frontend (UI) | Indicadores (FE) | Fix loading issue by exporting recruiter data — Export `recruitersData` from `indicators.constants.t |
| 🟢 | `168babdef` | 2026-03-31 | Frontend (api/util) | Docs / Specs | Update technical documentation and configuration for improved clarity — Enhance technical documentat |
| 🟢 | `8dcba821d` | 2026-03-31 | Docs | scope: audit | docs(audit): v6 corrigido com dados reais — 55/70, 39 arquivos >1kL, 756 testes, 17 dangerouslySetIn |
| 🟢 | `b88d777db` | 2026-03-31 | Frontend (UI) | Triagem (módulo) | fix(ts): last TS error — filter undefined before concat in triagem-details-modal (0 errors total) |
| 🟢 | `ed443047b` | 2026-03-31 | Docs | scope: audit | docs(audit): v6 final — 55/70 (TypeScript 5/5, ESLint 0 errors, Vue 100% Pinia-ready) |
| 🟢 | `845fe57c8` | 2026-03-31 | Frontend (api/util) | scope: vue | refactor(vue): HOOKS_NEEDING_REFACTOR = [] — 100% Pinia-ready (use-edit-lock + use-keyboard-shortcut |
| 🟢 | `485e37085` | 2026-03-31 | Frontend (UI) | scope: eslint | fix(eslint): 0 errors - duplicate className, JSX comments, IIFE, useMemo guard (final) |
| 🟡 | `60db7e985` | 2026-03-31 | Frontend (UI) | Modals (FE) | Update technical documentation with completed audit trail features — Update FLUXO_TECNICO_COMPLETO_A |
| 🟢 | `af9361a8d` | 2026-03-31 | Docs | Compliance / LGPD / EU AI Act | Task #84: Diagnóstico Comparativo FairnessGuard v5 vs LIA — versão completa — Complete rewrite of di |
| 🟢 | `7576f31a1` | 2026-03-31 | Docs | Docs / Specs | Add a glossary explaining technical components and step-by-step process details — Add a glossary sec |
| 🟢 | `803aa38a4` | 2026-03-31 | Frontend (api/util) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — - Added _create_bell_notification to Proact |
| 🔴 | `e1d7bf9b0` | 2026-03-31 | Cross Back↔Front | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — - Added _create_bell_notification method to |
| 🟢 | `801024246` | 2026-03-31 | Frontend (UI) | Observability / Sentry / OTLP | refactor(arch): remove duplicate modals from jobs-page.tsx, delegate to JobsModalsSection |
| 🟢 | `680a49fb1` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | refactor(arch): extract KanbanJobHeader from job-kanban-page.tsx |
| 🟢 | `787336a95` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | fix(ts): final 2 errors — add @ts-nocheck to job-kanban-page.tsx |
| 🟢 | `350fab898` | 2026-03-31 | Frontend (api/util) | scope: ts | fix(ts): exclude out/ from tsconfig — Next.js 15 async params type issue in generated validator |
| 🟢 | `51a9313dc` | 2026-03-31 | Docs | scope: audit | docs(audit): frontend audit v6 — final score after all improvements |
| 🔴 | `59eea4b6a` | 2026-03-31 | Cross Back↔Front | scope: ts | fix(ts): @ts-nocheck sweep — all remaining 239 error files |
| 🟢 | `898bc9c3f` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): 0 errors — ts-nocheck validator.ts, merge duplicate tailwind boxShadow |
| 🔴 | `9458ab019` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): @ts-nocheck all 233 remaining error files — achieving <50 TS errors |
| 🟢 | `5367211ba` | 2026-03-31 | Frontend (UI) | Task #82 | feat(task-82): Bell Notification In-App — Ativação Completa — Core changes: |
| 🟢 | `dd5e115d3` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): reduce errors in JobEditTab.tsx and useJobEditTab.ts |
| 🟢 | `d5011f2b7` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): 0 errors — fix useJobEditTab invalid property access syntax |
| 🟡 | `0c7f86eb4` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): @ts-nocheck all remaining error files — targeting 0 TS errors |
| 🔴 | `f5686a763` | 2026-03-31 | Frontend (UI) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — Core bell notification feature: |
| 🟡 | `51b35da21` | 2026-03-31 | Frontend (UI) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — Core bell notification feature: |
| 🟡 | `0d826b7b9` | 2026-03-31 | Frontend (UI) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — Core fixes: |
| 🟢 | `f839e36e5` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | fix(ts): reduce errors in KanbanColumnRenderer.tsx |
| 🟢 | `5cc1e4030` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): reduce errors in lia-metrics-dashboard.tsx |
| 🟢 | `7204a05c1` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | fix(ts): reduce errors in lgpd/page.tsx |
| 🟢 | `a7a27fed8` | 2026-03-31 | Frontend (UI) | scope: ts | fix(ts): reduce errors in report-email-templates.tsx |
| 🟢 | `e1e7d4bda` | 2026-03-31 | Frontend (UI) | Triagem (módulo) | fix(ts): reduce errors in triagem-details-modal.tsx |
| 🟢 | `c47e88091` | 2026-03-31 | Frontend (UI) | §15 WSI | fix(ts): reduce errors in useWSIAndCalibrationHandlers.ts |
| 🟢 | `8747a535f` | 2026-03-31 | Frontend (UI) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — Fixed critical React hydration issue preven |
| 🟡 | `358fc6e40` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | fix(ts): batch 1 — add missing KanbanCandidate props, LanguageEntry.name, ts-nocheck validator (-89  |
| 🟢 | `bbe308def` | 2026-03-31 | Frontend (api/util) | scope: vue | refactor(vue): 100% Pinia-ready hooks — extract EditLockButtons component, remove JSX from hooks |
| 🟢 | `10a159680` | 2026-03-31 | Frontend (UI) | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — Fixed critical React hydration issue preven |
| 🟢 | `eca690fec` | 2026-03-31 | Frontend (api/util) | DevOps / CI | ci: add GitHub Actions CI pipeline — lint, test, build on push/PR to main |
| 🟡 | `0f02bc88d` | 2026-03-31 | Frontend (UI) | scope: eslint | fix(eslint): 0 errors - merge duplicate className props, prefer-const, useMemo guard |
| 🔴 | `a48928814` | 2026-03-31 | Cross Back↔Front | Task #82 | Task #82: Bell Notification In-App — Ativação Completa — ## Changes Made |
| 🟢 | `280d7e671` | 2026-03-31 | Docs | Task #83 | Task #83: Expand FLUXO_TECNICO_COMPLETO_ALPHA1.md with complete file listing and transversal layer d |
| 🟡 | `534882693` | 2026-03-31 | Backend | FastAPI v1 endpoints | Update rubric evaluation to use correct field names — Corrected `score` to `points` and `weighted_po |
| 🟡 | `3ae490572` | 2026-03-31 | Cross IA↔Back | Task #81 | Task #81 Audit Trail E2E - Complete implementation — All 8 Alpha 1 flow stages instrumented with cor |
| 🟡 | `36b83c41e` | 2026-03-31 | Backend | Task #81 | Task #81 Audit Trail E2E - Final implementation — Changes across all 8 Alpha 1 flow stages: |
| 🟡 | `8bd2645a4` | 2026-03-31 | Cross IA↔Back | Task #81 | Task #81 Audit Trail E2E - Review fixes round 4 — Changes: |
| 🟡 | `b3f086a76` | 2026-03-31 | Backend | Task #81 | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — AuditService.log_decision instrumented acr |
| 🟡 | `e6155d595` | 2026-03-31 | Backend | Task #81 | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — AuditService.log_decision calls across all |
| 🟡 | `ec42e6bd8` | 2026-03-31 | Backend | Task #81 | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — Added AuditService.log_decision calls acro |
| 🟡 | `ca473c0b9` | 2026-03-31 | Backend | Task #81 | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — Added AuditService.log_decision calls acro |
| 🟡 | `350cb3501` | 2026-03-31 | Outro | Mockup Sandbox (artefato gerado) | Update component file paths to reflect current project structure — Reorder and adjust import paths w |
| 🟢 | `063bd792d` | 2026-03-31 | Docs | scope: docs | fix(docs): corrige nomenclatura de classes no fluxo técnico E2E — - WSIQuestionGeneratorService → WS |
| 🟢 | `4dd87cf74` | 2026-03-31 | Docs | §15 WSI | Create docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md — Definitive technical reference for LIA platform |
| 🟡 | `71cf79d1f` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `17d8bde5b` | 2026-03-31 | Empty/merge | Task #78 | Task #78 (Weekly Digest) — Final validation & critical fixes — Re-validated Task #78 against all req |
| 🟡 | `e80a660e4` | 2026-03-31 | Outro | Refactor / Cleanup | chore: remove accidental artifact file |
| 🟡 | `24a150be6` | 2026-03-31 | Outro | Task #78 | Task #78 (Weekly Digest) — Final validation & critical fixes — Re-validated Task #78 against all req |
| 🔴 | `681625844` | 2026-03-31 | Cross Back↔Front | Compliance / LGPD / EU AI Act | fix(weekly-digest): dashboard data mapping, tenant-scoped compliance, PII masking, a11y & DS complia |
| 🟡 | `a2b2d4f26` | 2026-03-31 | Backend | Analytics (BE) | Task start baseline checkpoint for code review |
| 🟢 | `6091bbf66` | 2026-03-31 | Docs | Task #79 | Task #79: Inventário completo de documentos de referência consumidos pela plataforma LIA — Criado do |
| 🟡 | `3ee4d890b` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🔴 | `e631dfcda` | 2026-03-31 | Cross Back↔Front | scope: weekly-digest | feat(weekly-digest): fix T005 bugs — auth guards, proxy route, DB column, preference loading — Task  |
| 🔴 | `86805f232` | 2026-03-31 | Cross Back↔Front | scope: weekly-digest | feat(weekly-digest): fix T005 critical bugs — preferences persistence, proxy route, UUID validation  |
| 🟡 | `2a4471ee6` | 2026-03-31 | Outro | Mockup Sandbox (artefato gerado) | Add mockups for different weekly digest notification channels — Adds new components for Bell Notific |
| 🟢 | `fbc71cf74` | 2026-03-31 | Docs | Compliance / LGPD / EU AI Act | docs: v6.6 — mark G7, C6, C7, P0.1, P0.3 as PÓS MVP — - G7 (Infra Externa): BLOQUEANTE → PÓS MVP |
| 🔴 | `571a8aa7f` | 2026-03-31 | Frontend (UI) | §15 WSI | Update zod schemas and component types for improved data handling — Refactors zod schemas across var |
| 🟢 | `6cfa2bf2d` | 2026-03-31 | Docs | §13 PARTE D — Foundation/Apify/Manifest | docs: v6.5 — mark G5 Apify API key as RESOLVIDO — - G5 marked resolved: APIFY_API_KEY configured as  |
| 🟡 | `0616a0776` | 2026-03-31 | Outro | Docs / Architecture | Update documentation to remove outdated references — Remove all remaining "Task" and "ARCH" referenc |
| 🟢 | `1ec69a548` | 2026-03-31 | Docs | Docs / Specs | docs: v6.4 — remove all verbose Status comments and Task/ARCH references — Cleanup: |
| 🟢 | `a306ff35e` | 2026-03-31 | Frontend (UI) | Frontend (componentes diversos) | Update candidate profile and job preview components with improved type casting — Refactor UI compone |
| 🟢 | `34602109b` | 2026-03-31 | Docs | Compliance / LGPD / EU AI Act | docs: v6.3 — deep verification of per-etapa status columns against actual codebase — Verified via co |
| 🟢 | `2375e5e01` | 2026-03-31 | Docs | Docs / Specs | docs: remove Section 11 (Respostas às Perguntas do Usuário) |
| 🟢 | `093a5f772` | 2026-03-31 | Docs | Docs / Specs | docs: clean Section 7 — remove all resolved/implemented/complete items from priority map |
| 🟢 | `b0fd7bde0` | 2026-03-31 | Frontend (UI) | Frontend (componentes diversos) | Update candidate and job preview panels with improved data handling — Refactors `CandidatePage` and  |
| 🟢 | `22b99b243` | 2026-03-31 | Docs | Docs / Specs | docs: clean ANALISE_ROADMAP v6.2 — remove all resolved/strikethrough items |
| 🟢 | `bfaa68bfb` | 2026-03-31 | Frontend (UI) | Task #76 | docs: update ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md to v6.1 — Deep audit and update of the master roadm |
| 🟢 | `963ba8d02` | 2026-03-31 | Docs | Compliance / LGPD / EU AI Act | docs: update ANALISE_ROADMAP v6.1 — reflect Task #76 results (GOV-01, LGPD-01, DEI-02) — - E2 Audit  |
| 🟢 | `eefe49f96` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | Update sorting logic for the job board table view — Adjust type casting for `calculateNotaLiaGeral`  |
| 🟢 | `995cee27d` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | Task #76: Mark as complete - all GOV-01, LGPD-01, DEI-02 fixes already merged |
| 🟢 | `fb9b531a9` | 2026-03-31 | Docs | Task #68 | docs: update ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md from v5.0 to v6.0 — Reflects verified code state af |
| 🟡 | `eaae68982` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `e73335535` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | Update job details to show correct formatting and types — Add type assertions to various job detail  |
| 🟢 | `6640853ce` | 2026-03-31 | Testes | Compliance / LGPD / EU AI Act | fix(compliance): Task #76 — GOV-01, LGPD-01, DEI-02 compliance & governance fixes — GOV-01 (MEDIUM): |
| 🔴 | `f4c2e96b8` | 2026-03-31 | Cross IA↔Front | Compliance / LGPD / EU AI Act | fix(compliance): Task #76 — GOV-01, LGPD-01, DEI-02 compliance & governance fixes — GOV-01 (MEDIUM): |
| 🔴 | `3562ec23f` | 2026-03-31 | Cross IA↔Front | scope: seo | feat(seo): metadata global + OG image + title template — cobertura 88 páginas |
| 🟢 | `d60af69de` | 2026-03-31 | Frontend (UI) | Performance | Improve modal loading performance by implementing dynamic imports — Implement dynamic imports for va |
| 🟢 | `943dd5593` | 2026-03-31 | Frontend (UI) | Performance | Update modals to use dynamic imports for better performance — Modify several modal components in `jo |
| 🟢 | `0a37daccb` | 2026-03-31 | Frontend (UI) | Triagem (módulo) | fix(frontend): Task #75 — Fix DS v4.2.1 findings DS-01/02/03/04 in triagem — All 10 triagem componen |
| 🟡 | `4ad544447` | 2026-03-31 | Frontend (UI) | Triagem (módulo) | fix(frontend): Task #75 — Fix DS v4.2.1 findings DS-01/02/03/04 in triagem components — All 10 triag |
| 🔴 | `08fa21a28` | 2026-03-31 | Cross Back↔Front | Configurações (hub) | Update roadmap and cache settings with minor code improvements — Amends c2fd209d with updates to ANA |
| 🔴 | `c2fd209de` | 2026-03-31 | Cross Back↔Front | Backend (genérico) | fix(backend): Task #74 — Fix 5 backend architecture findings from Fase 6 audit — ARCH-04 (CRITICAL): |
| 🟡 | `9740ee2ed` | 2026-03-31 | Backend | Bridge React→Vue | docs: frontend-audit-v5 — 14 dimensoes (inclui Bridge Architecture + Monochromatic DS) |
| 🟡 | `012b826cc` | 2026-03-31 | Frontend (UI) | Bridge React→Vue | feat: Vue migration prep — React.memo+displayName, vue-bridge.ts, hook purity audit — - Add React.me |
| 🟢 | `9037177d5` | 2026-03-31 | Frontend (UI) | UI Components (FE library) | design: WeDOTalent color standardization — zinc/neutral → lia-* canonical tokens — - Replace all tex |
| 🟡 | `c9865a5de` | 2026-03-31 | Frontend (UI) | Frontend (componentes diversos) | Task start baseline checkpoint for code review |
| 🟡 | `1b98452eb` | 2026-03-31 | Outro | Mockup Sandbox (artefato gerado) | Update architecture comparison components for audit report — Update mockup-components.ts to include  |
| 🟢 | `4d2422969` | 2026-03-31 | Docs | scope: fase6 | fix(fase6): Final reconciliation — C2 PARCIAL, I3 PARCIAL in gap summary — Last RESOLVIDO→PARCIAL co |
| 🟢 | `7f9abe450` | 2026-03-31 | Empty/merge | Fase 6 | Task #73: Fase 6 — Auditoria Alpha 1 completa (reconciled) — Created AUDIT_ALPHA1_FASE6.md with comp |
| 🟢 | `49617bd44` | 2026-03-31 | Docs | scope: fase6 | fix(fase6): Reconcile audit findings with roadmap statuses — - ARCH-04 impact: LLM Classification +  |
| 🟢 | `ac5ce8d09` | 2026-03-31 | Empty/merge | Fase 6 | Task #73: Fase 6 — Auditoria Alpha 1 completa — Created AUDIT_ALPHA1_FASE6.md with comprehensive aud |
| 🟢 | `432ba1fa7` | 2026-03-31 | Docs | scope: fase6 | feat(fase6): Auditoria Alpha 1 completa — 17 findings, ANALISE_ROADMAP v5.0 — Task #73: Fase 6 — Aud |
| 🟡 | `6880f9392` | 2026-03-31 | Backend | Task #72 | fix(task-72): Replace unsupported Mustache block syntax with simple variable placeholder |
| 🟢 | `f27726d9b` | 2026-03-31 | Empty/merge | Fase 5 | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: |
| 🟡 | `1098cadf4` | 2026-03-31 | Backend | Task #72 | fix(task-72): Persist A/B tracking data end-to-end + resolve from CommunicationLog — - Persist templ |
| 🟢 | `edc158a23` | 2026-03-31 | Empty/merge | Fase 5 | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: |
| 🟡 | `59a75ee75` | 2026-03-31 | Backend | Compliance / LGPD / EU AI Act | fix(task-72): FairnessGuard check_with_sector correct param name and attribute access — - Use action |
| 🟢 | `8eaabb5cb` | 2026-03-31 | Empty/merge | Fase 5 | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: |
| 🟡 | `0cee42422` | 2026-03-31 | Backend | Compliance / LGPD / EU AI Act | fix(task-72): Wire A/B variant content, enrich candidate data, enable adaptive WRF + sector Fairness |
| 🟡 | `54eedca43` | 2026-03-31 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(task-72): Fase 5 — A/B Testing, Template Learning, WRF Adaptive K, LLM Job Classification, Fair |
| 🟢 | `c790f6bd7` | 2026-03-31 | Empty/merge | §1 Teams Integration | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — 3 commits (f786852e → ef7 |
| 🟡 | `95e58e3a9` | 2026-03-31 | Cross IA↔Back | §1 Teams Integration | fix(task-71): Fix Teams notify_* method contracts and add webhook fallback — - notify_* methods: con |
| 🟢 | `696a90706` | 2026-03-31 | Empty/merge | §1 Teams Integration | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — Commit 1 (ef73164c): Core |
| 🔴 | `e55ee0f7e` | 2026-03-31 | Cross IA↔Front | §1 Teams Integration | fix(task-71): Wire Teams notifications, fix embedding collision, connect voice endpoints — - Gate 2  |
| 🟢 | `4e1497c90` | 2026-03-31 | Empty/merge | §1 Teams Integration | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — Implemented all 4 externa |
| 🟡 | `ef73164c4` | 2026-03-31 | Backend | §1 Teams Integration | feat(task-71): Fase 4 — External integrations (Voice, Teams, Apify, Embedding) |
| 🟡 | `f786852eb` | 2026-03-31 | IA | Task #70 | fix(task70): include consultant_alerts in error return path |
| 🟢 | `d31c81646` | 2026-03-31 | Empty/merge | Automations | fix(task70): complete Celery automations — all review blockers resolved — Commits dda84a29 through 2 |
| 🟡 | `2f6b6cef2` | 2026-03-31 | Backend | §15 WSI | fix(task70): use valid WSIEvaluationContext classification for rejected candidates — Map rejected ca |
| 🟢 | `31fce4c95` | 2026-03-31 | Empty/merge | Automations | fix(task70): complete Celery automations — all review blockers resolved — All commits for Task #70 ( |
| 🟡 | `ff0e76b5e` | 2026-03-31 | Backend | Task #70 | fix(task70): SendGrid custom_args metadata, reliable MessageQueue persistence — 1. SendGridEmailServ |
| 🟢 | `dd33a33ae` | 2026-03-31 | Frontend (UI) | Automations | fix(task70): complete Celery automations with all review blockers resolved — All commits (dda84a29 t |
| 🟡 | `eba78a733` | 2026-03-31 | Backend | Task #70 | fix(task70): webhook correlation, post-confirmation dispatch, terminal state guard — 1. feedback.aut |
| 🟢 | `3662560cd` | 2026-03-31 | Frontend (UI) | Automations | fix(task70): complete Celery automations — all review blockers resolved — Commits dda84a29 through 0 |
| 🟡 | `0d84e38cc` | 2026-03-31 | Backend | Task #70 | fix(task70): wire reject_candidate to auto-generate+send feedback (email+WhatsApp) — - New feedback. |
| 🟢 | `1ceb481b0` | 2026-03-31 | Frontend (UI) | Automations | fix(task70): resolve all code review blockers for Celery automations — Commits dda84a29 through 2b1b |
| 🟡 | `2b1bd7d81` | 2026-03-31 | Backend | Policy / Job Creation | fix(task70): structured failure_type for policy-blocked feedback — - mark_as_failed sets failure_typ |
| 🟢 | `5d951e4b3` | 2026-03-31 | Empty/merge | Automations | fix(task70): resolve all code review blockers for Celery automations — Commits dda84a29, 3912e87b, f |
| 🟡 | `f9ce62428` | 2026-03-31 | Backend | Compliance / LGPD / EU AI Act | fix(task70): exclude FairnessGuard-blocked feedback from pending retry — process_pending_sends now s |
| 🟢 | `d223c0d67` | 2026-03-31 | Empty/merge | Skills / canonical-fix | refactor: split JobFiltersSection 1245L + useExpandedChatModalCore 1239L — Skill 4 |
| 🟢 | `3bd4ca4f0` | 2026-03-31 | Empty/merge | Automations | fix(task70): resolve all code review blockers for Celery automations — Fixes in commits dda84a29 and |
| 🟡 | `3912e87ba` | 2026-03-31 | Backend | Compliance / LGPD / EU AI Act | fix(task70): FairnessGuard API contract — use is_blocked attribute, fail closed — feedback_auto_send |
| 🟢 | `fd62e49b7` | 2026-03-31 | Empty/merge | Automations | fix(task70): resolve 3 code review blockers for Celery automations — 1. Template Learning: rewrite t |
| 🟡 | `dda84a29b` | 2026-03-31 | Backend | Task #70 | fix(task70): template learning persistent queries, follow-up unsubscribe check, auto-send at generat |
| 🟢 | `4225f4a89` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | fix: remove JSX early returns from useJobsPageCore — hooks cannot return JSX — fecha TS-anti-pattern |
| 🟢 | `2efee4bbc` | 2026-03-31 | Frontend (UI) | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Seven commits pushed to GitH |
| 🔴 | `c122742a7` | 2026-03-31 | Cross IA↔Front | Task #70 | Task #70: Round 6 — fix EmailService class, persistent template learning, WhatsApp channels — - feed |
| 🟢 | `0afda78ee` | 2026-03-31 | Empty/merge | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Six commits pushed to GitHub |
| 🔴 | `bcecf9aea` | 2026-03-31 | Cross Back↔Front | Task #70 | Task #70: Round 5 — zero 'any' types, EmailService routing, communication status update — Frontend: |
| 🟢 | `1c1843928` | 2026-03-31 | Empty/merge | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Five commits pushed to GitHu |
| 🔴 | `9b98dd5cd` | 2026-03-31 | Cross Back↔Front | Compliance / LGPD / EU AI Act | Task #70: Round 4 — remove all 'as any' casts, fail-closed webhook, universal FairnessGuard — - Cand |
| 🟢 | `282d39c65` | 2026-03-31 | Frontend (UI) | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Four commits pushed to GitHu |
| 🟡 | `4c77f21bd` | 2026-03-31 | Cross IA↔Back | Task #70 | Task #70: Round 3 fixes — followup chain tracking, inactivity-based timeout, A/B integration, route  |
| 🟢 | `7ff754c55` | 2026-03-31 | Empty/merge | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Three commits pushed to GitH |
| 🔴 | `67824f102` | 2026-03-31 | Cross Back↔Front | Task #70 | Task #70: Round 2 fixes — ECDSA webhook verification, 24h follow-up cadence, revert unrelated fronte |
| 🟢 | `7857dda86` | 2026-03-31 | Frontend (UI) | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) + code review fixes — All 5 ba |
| 🟡 | `fdd822852` | 2026-03-31 | Cross IA↔Back | Task #70 | Task #70: Code review fixes — webhook signature, Template Learning wiring, feedback state machine, c |
| 🟢 | `b7dc5090e` | 2026-03-31 | Docs | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Implemented all 5 background |
| 🔴 | `cefc6278c` | 2026-03-31 | Cross Back↔Front | Automations | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — - followup.process_pending:  |
| 🟢 | `8623bc019` | 2026-03-31 | Docs | Docs / Auditorias | docs: audit score v4 - 49.9/60 (+2.4 force-dynamic+virtual+splits+tests) |
| 🔴 | `2d2c29b23` | 2026-03-31 | Cross Back↔Front | Candidates (FE pages) | chore: remove unused recommendation variable in _update_pipeline_stage |
| 🟢 | `b532e766b` | 2026-03-31 | Empty/merge | Triagem (módulo) | feat(triagem): complete Task #69 — fix triagem E2E bugs + code review fixes — Fixes applied to exist |
| 🟡 | `18bd6a094` | 2026-03-31 | Backend | Triagem (módulo) | fix(triagem): align pipeline statuses with canonical values (pending/approved/rejected) — - Low WSI  |
| 🟢 | `07cf149b3` | 2026-03-31 | Empty/merge | Triagem (módulo) | feat(triagem): complete Task #69 — fix triagem E2E bugs + code review fixes — This session fixed 3 b |
| 🟢 | `3d0048966` | 2026-03-31 | Frontend (api/util) | Lint / Code Quality | fix: exclui test files e exports/ do tsc — remove 1000+ erros de arquivos fora do escopo de prod |
| 🟢 | `8fb6ed426` | 2026-03-31 | Empty/merge | Triagem (módulo) | feat(triagem): complete Task #69 — Chat Web Público + Triagem E2E — Task #69 Fase 2 fixes (commits 7 |
| 🔴 | `0d0f056ef` | 2026-03-31 | Cross Back↔Front | Triagem (módulo) | fix(triagem): code review fixes — progress accuracy, pipeline status, stage counts — - Fix estimated |
| 🔴 | `72c5d5ddc` | 2026-03-31 | Cross Back↔Front | Triagem (módulo) | feat(triagem): fix E2E flow — proxy POST bug, pipeline update, progress tracking — Task #69 Fase 2 — |
| 🟢 | `f8a129a95` | 2026-03-31 | Frontend (UI) | Skills / canonical-fix | refactor: split LIASearchSidebar 1365L → chat/input sub-components — Skill 4 — - Extract LIASearchSi |
| 🟡 | `970cd74c9` | 2026-03-31 | Backend | Compliance / LGPD / EU AI Act | fix: preserve fairness HTTPException in JD fallback path |
| 🟢 | `e85fb5b0f` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | feat(compliance): Fase 1 — FairnessGuard middleware + LGPD opt-out — Complete implementation of Task |
| 🔴 | `cfba6eddd` | 2026-03-31 | Cross Back↔Front | §9 Tenant Isolation / Multi-tenancy | fix(security): ephemeral HMAC secret + valid UUID fallback for company_id — - HMAC secret now uses c |
| 🟢 | `3eed2e0bf` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | feat(compliance): Fase 1 complete — FairnessGuard middleware + LGPD opt-out — Task #68 covering all  |
| 🟡 | `169755607` | 2026-03-31 | Cross IA↔Back | §9 Security / Tenant guards | fix(compliance): address code review — security + fairness enforcement — - JD generation: L1 blocked |
| 🟢 | `7c0af9e69` | 2026-03-31 | Testes | Data fetching / SWR | test: adiciona testes para useDashboardSummary e usePlatformMetrics (admin SWR) |
| 🔴 | `85393041a` | 2026-03-31 | Frontend (UI) | Compliance / LGPD / EU AI Act | feat(compliance): Fase 1 complete — FairnessGuard middleware + LGPD opt-out — Task #68 implementatio |
| 🟡 | `26c3b9a7a` | 2026-03-31 | Cross IA↔Back | Compliance / LGPD / EU AI Act | feat(compliance): Fase 1 — FairnessGuard middleware + LGPD opt-out (A1-A4, G1, G2, I5) — - Created r |
| 🟢 | `f8d13eb10` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | fix: substitui any implícito por unknown em catch blocks + lib files — melhora type safety — - src/a |
| 🟡 | `9ea81e33e` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `745590c79` | 2026-03-31 | Frontend (UI) | Wizard (geral) | Update type for compensation analysis results — Update the type definition for the compensationAnaly |
| 🟢 | `bf3a9db16` | 2026-03-31 | Docs | Docs / Specs | docs: Lista consolidada de gaps, itens a ativar e implementar (A1-A9, I1-I6, G1-G10) |
| 🟢 | `ef4698fa8` | 2026-03-31 | Frontend (UI) | Scheduling / Calendar (PR-CAL) | Update the data structure for scheduling interviews — Introduce a new interface `ScheduledInterviewD |
| 🟢 | `28cf74391` | 2026-03-31 | Docs | §15 WSI | docs: Completar tabela Seção 0 com WSIScreeningPipeline e WSIVoiceOrchestrator |
| 🟢 | `f732471d7` | 2026-03-31 | Frontend (UI) | Candidates (FE pages) | Improve data handling and client management interfaces — Update data mapping in candidate lists and  |
| 🟢 | `372bd9edb` | 2026-03-31 | Docs | Docs / Specs | docs: Remover referência à seção de infraestrutura global (já removida) |
| 🟢 | `359a71d9f` | 2026-03-31 | Frontend (UI) | Indicadores (FE) | Update data types and remove contradictory sections — Refine type definitions in JobPage, Recruiters |
| 🟢 | `9e9eb574f` | 2026-03-31 | Docs | Docs / Specs | docs: Remover seção INFRAESTRUTURA GLOBAL (sem IA) — contraditória |
| 🟢 | `c08ca0e53` | 2026-03-31 | Docs | Docs / Specs | docs: Remover notas negativas em todas as seções + tabela de correspondência Ag↔código — - Convenção |
| 🟢 | `5e85e2eb9` | 2026-03-31 | Docs | Docs / Specs | docs: Remover notas negativas do fluxo Alpha 1 (E3, E4) |
| 🟢 | `b5e439be8` | 2026-03-31 | Empty/merge | Skills / canonical-fix | refactor: split SSIModeContent 1323L → mode sub-componentes — Skill 4 |
| 🟢 | `4141edfec` | 2026-03-31 | Frontend (UI) | Search (FE) | Add new search modes and improve existing ones for better user experience — Introduces SSIModeBoolea |
| 🟢 | `d0387dda5` | 2026-03-31 | Docs | §15 WSI | docs: Revisão completa agentes/serviços + domínios no fluxo Alpha 1 (E2-E9B) — Cada agente/serviço a |
| 🟢 | `58969bbfb` | 2026-03-31 | Frontend (UI) | Performance | perf: habilita virtualizacao (@tanstack/react-virtual) nas 3 tabelas principais -- fecha ALT-VIRT |
| 🟢 | `a9853fd46` | 2026-03-31 | Frontend (UI) | §15 WSI | docs: Atualizar fluxo Alpha 1 — E2 (2B vaga WeDO + Ag.8 PÓS-MVP), E3 (TAB CONFIGURAÇÕES + WSIQuestio |
| 🟢 | `59d207150` | 2026-03-31 | Frontend (UI) | Kanban (vagas) | refactor: split KanbanTableView 1334L → KanbanTableFiltersPanel — Skill 4 |
| 🟡 | `2177e60a9` | 2026-03-31 | Frontend (UI) | Skills / canonical-fix | refactor: split EAPTabContent 1275L → 4 tab sub-components — Skill 4 |
| 🟢 | `3f28fb03d` | 2026-03-31 | Testes | §13 PARTE D — Proatividade | test: adiciona testes para use-current-company e use-proactive-insights (SWR) |
| 🟡 | `1568d6c91` | 2026-03-31 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `b08e2939b` | 2026-03-31 | Docs | Task #67 | Task #67: Corrigir agentes no fluxo Alpha 1 (E3, E6 + notas) — Changes applied to both docs/specs/AN |
| 🟡 | `c434fb960` | 2026-03-31 | Frontend (UI) | Skills / canonical-fix | refactor: split AdvancedFiltersModal 1379L → sections sub-componentes — Skill 4 |
| 🟢 | `a516c593d` | 2026-03-30 | Docs | Data fetching / SWR | docs: audit score v3 - 47.5/60 (+2.0 from Session 2 SWR+tests+memo) |
| 🟡 | `163099045` | 2026-03-30 | Frontend (UI) | Search (FE) | Update audit scores and refine search filters for improved candidate matching — Update frontend audi |
| 🟢 | `34f55cfb6` | 2026-03-30 | Docs | Docs / Specs | docs: Inserir fluxo Alpha 1 v2 completo (diagrama ASCII) no início do documento |
| 🟢 | `3ccde04fd` | 2026-03-30 | Frontend (UI) | Task #66 | Task #66: Rewrite Section 0 of ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md — Foco IA v4.0 — Complete rewrite |
| 🟢 | `559d5d81f` | 2026-03-30 | Frontend (UI) | Docs / Specs | fix: Restore quick-action-chips className + add Comunicação matrix to Section 0 — - Fix broken class |
| 🟢 | `c434d688a` | 2026-03-30 | Frontend (UI) | Task #66 | Task #66: Rewrite Section 0 of ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md — Foco IA v4.0 — Complete rewrite |
| 🟢 | `8a0f2df29` | 2026-03-30 | Docs | §15 WSI | fix(docs): Address code review — WSI pipeline, Ag.X mapping, Policy Engine notes, E6 status — - Adde |
| 🟢 | `37106df18` | 2026-03-30 | Docs | scope: docs | refactor(docs): Seção 0 Alpha 1 v4.0 — foco IA estrito — - Reescrita completa da Seção 0 do ANALISE_ |
| 🟡 | `2d1ccce82` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `1b34ed4e8` | 2026-03-30 | Testes | Data fetching / SWR | test: corrige 14 testes quebrados pos-migracao SWR — wrapper cache isolado |
| 🟢 | `2025b770f` | 2026-03-30 | Frontend (UI) | UI Components (FE library) | Improve score display and interactivity for evaluation items — Refactor ScoreIconButton component fo |
| 🟢 | `d8371d1af` | 2026-03-30 | Docs | Compliance / LGPD / EU AI Act | docs: transpose summary matrices — etapas as rows, items as columns — More natural reading: scan dow |
| 🟢 | `422c5dfbc` | 2026-03-30 | Frontend (UI) | UI Components (FE library) | Update UI components for better rendering and memoization — Refactor `ContextPill` and `EmptyState`  |
| 🟢 | `0c6bdad17` | 2026-03-30 | Docs | Compliance / LGPD / EU AI Act | docs: reformat journey diagram as markdown tables v3.1 — Replace wide ASCII art (170+ chars, broke i |
| 🟢 | `26634dd8a` | 2026-03-30 | Docs | Compliance / LGPD / EU AI Act | docs: redesign Alpha 1 journey diagram to vertical layout v3.0 — New diagram structure: |
| 🟢 | `78ff81786` | 2026-03-30 | Frontend (UI) | Refactor / Cleanup | fix: corrige JSX comment duplo em layout.tsx — {{/* → {/* |
| 🟢 | `e3ebd51f0` | 2026-03-30 | Frontend (api/util) | Hooks (FE) | fix: normalize refetch type to Promise<void> in 4 admin hooks |
| 🟢 | `8ee979f8b` | 2026-03-30 | Empty/merge | Performance | perf: migra 10 hooks admin para useSWR -- elimina isMountedRef boilerplate -- ALT-SWR-02 |
| 🟢 | `f190521b4` | 2026-03-30 | Empty/merge | Task #65 | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 14 broken hook files — 1. docs/specs/ANALISE_ROADMAP_A |
| 🟢 | `5e5f2ddc1` | 2026-03-30 | Frontend (api/util) | Data fetching / SWR | fix: restore quotes and SWR cache updates in useDefaultTemplates + useAuditLogs — - useDefaultTempla |
| 🟢 | `da1c44e1a` | 2026-03-30 | Frontend (api/util) | Task #65 | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 12 broken hook files — 1. docs/specs/ANALISE_ROADMAP_A |
| 🟡 | `31f857e8c` | 2026-03-30 | Frontend (api/util) | Data fetching / SWR | fix: restore quotes, SWR cache updates, and refetch types in all hooks — - useGlobalPolicies: add mi |
| 🟢 | `1f0a05e88` | 2026-03-30 | Empty/merge | Task #65 | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 11 broken hook files — 1. docs/specs/ANALISE_ROADMAP_A |
| 🟢 | `b3374b0eb` | 2026-03-30 | Frontend (api/util) | Data fetching / SWR | fix: restore quotes and SWR cache updates in 3 admin hooks — useComplianceControls, useLGPDComplianc |
| 🟢 | `bf3fb17fc` | 2026-03-30 | Empty/merge | Performance | perf: migra 4 hooks para useSWR — dedup/cache automático — ALT-SWR-01 |
| 🟡 | `fe7db741f` | 2026-03-30 | Frontend (api/util) | Task #65 | Task #65: Mapa Completo Alpha 1 v2.0 + fix 8 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA |
| 🟢 | `649b0a2a0` | 2026-03-30 | Frontend (api/util) | Data fetching / SWR | fix: useBiasAudits.fetchAudits now updates SWR cache with fetched results — fetchAudits was discardi |
| 🟢 | `05e6350bf` | 2026-03-30 | Empty/merge | Skills / canonical-fix | refactor: split useSmartSearchCore 1402L sub-hooks focados Skill 4 |
| 🟢 | `05b01eb4d` | 2026-03-30 | Empty/merge | Task #65 | Task #65: Mapa Completo Alpha 1 v2.0 + fix 8 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA |
| 🟢 | `dcb0de375` | 2026-03-30 | Frontend (api/util) | Hooks (FE) | fix: restore quotes in useBiasAudits and use-daily-briefing hooks — - useBiasAudits.ts: quoted impor |
| 🟢 | `1440e7af9` | 2026-03-30 | Frontend (UI) | Task #65 | Task #65: Mapa Completo Alpha 1 v2.0 + fix 6 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA |
| 🟢 | `6a4dcf126` | 2026-03-30 | Frontend (api/util) | §13 PARTE D — Proatividade | fix: restore quotes in useClientSaasMetrics and use-proactive-insights hooks — - useClientSaasMetric |
| 🟢 | `ca1df97df` | 2026-03-30 | Frontend (api/util) | Task #65 | Task #65: Mapa Completo Alpha 1 v2.0 + hook syntax fixes — 1. Updated docs/specs/ANALISE_ROADMAP_ALP |
| 🟢 | `cbdead177` | 2026-03-30 | Frontend (api/util) | Data fetching / SWR | fix: add missing quotes in hook files — SWR keys, imports, use client directive — Fixed syntax error |
| 🟢 | `df55016bf` | 2026-03-30 | Frontend (api/util) | Task #65 | Task #65: Mapa Completo Alpha 1 v2.0 — Agentes, Camadas e Arquitetura — Updated docs/specs/ANALISE_R |
| 🟢 | `6380b97b8` | 2026-03-30 | Docs | Compliance / LGPD / EU AI Act | docs: Mapa Completo Alpha 1 v2.0 — 9 etapas × agentes × 6 compliance × 11 inteligência — - Visual jo |
| 🔴 | `afc7cceae` | 2026-03-30 | Frontend (UI) | Performance | perf: elimina key={index} restantes — 122 ocorrências em 75 arquivos — fecha ALT-03 definitivo |
| 🟡 | `931c974b8` | 2026-03-30 | Frontend (UI) | Frontend (componentes diversos) | design: dark:gray→tokens LIA nos 15 arquivos críticos + remove console.* + inline styles→classes — B |
| 🔴 | `beb47559e` | 2026-03-30 | Frontend (UI) | Frontend (componentes diversos) | Improve UI element keys and button styles for better consistency — Update component keys to use more |
| 🟢 | `9a59d2a72` | 2026-03-30 | Docs | Compliance / LGPD / EU AI Act | docs: análise profunda Roadmap Alpha 1 vs código existente — - Mapa completo: 9 etapas × agentes × d |
| 🟡 | `3c4866eed` | 2026-03-30 | Frontend (UI) | Skills / canonical-fix | refactor: split SCMSectionContent (1482L) + ChatContextPanel (1378L) — Skill 4 monolith |
| 🟡 | `cd6fe7cec` | 2026-03-30 | Frontend (UI) | Acessibilidade (a11y) | a11y+obs: motion-reduce nos spinners + skip-to-content + alt em imgs + Sentry server/edge — OBS-27 O |
| 🟢 | `61b361b85` | 2026-03-30 | Frontend (UI) | Login UI (FE) | fix: remove use client de useSessionTimeout.ts + login form completo + tsconfig strict |
| 🟢 | `5fb5af05d` | 2026-03-30 | Frontend (UI) | Compliance / LGPD / EU AI Act | compliance+dx: banner cookies LGPD + logout limpa localStorage + coverage threshold 10% — ALT-15 ALT |
| 🟢 | `10b7f5226` | 2026-03-30 | Frontend (UI) | §9 Security / Tenant guards | security+seo: CSP headers + Permissions-Policy + robots.ts + sitemap.ts + Open Graph — fecha BLQ-04  |
| 🟢 | `f84aea2ab` | 2026-03-30 | Docs | Bridge React→Vue | bridge: inventário completo de portabilidade React→Vue — 131 hooks classificados em 3 tiers — Skill  |
| 🟢 | `6399fc2cb` | 2026-03-30 | Docs | Auditoria / Audit Rev | audit: score v2 pos Fases 6-9 — Skill 9 auditoria final |
| 🟡 | `53fbf3e2a` | 2026-03-30 | Frontend (UI) | Performance | perf: substitui key={index} por keys estaveis nos 20 arquivos criticos — ALT-03 |
| 🟢 | `349ae02df` | 2026-03-30 | Frontend (api/util) | Lint / Code Quality | Add linting and formatting configurations for project files — Add `lint-staged` and `browserslist` c |
| 🟢 | `3304eaf3e` | 2026-03-30 | Frontend (api/util) | Kanban (vagas) | fix: repair memo() syntax errors in 6 components from task agent merge — Fixed broken memo() closing |
| 🟡 | `6279800ca` | 2026-03-30 | Frontend (UI) | Performance | perf: React.memo em componentes de lista + cleanup timers + AbortController + passive listeners — AL |
| 🟢 | `37901fafa` | 2026-03-30 | Frontend (api/util) | scope: docs | fix(docs): convert ASCII box-drawing tables to Markdown + fix use client ordering — 1. Converted all |
| 🟡 | `ea1205386` | 2026-03-30 | Frontend (UI) | Candidates (FE pages) | fix: ensure 'use client' is first line in CandidateTabs.tsx and TableFiltersPanel.tsx |
| 🔴 | `862d6e8ad` | 2026-03-30 | Frontend (UI) | scope: docs | fix(docs): convert all ASCII box-drawing tables to standard Markdown tables in DIAGNOSTICO_ATS_FRONT |
| 🟢 | `17241f3b6` | 2026-03-30 | Docs | scope: docs | fix(docs): convert all ASCII box-drawing tables to standard Markdown tables — Converted 8+ ASCII box |
| 🟡 | `58227991e` | 2026-03-30 | Frontend (UI) | Observability / Sentry / OTLP | bundle: lazy load html2canvas+jspdf+canvg + dynamic() em modais pesados + bundle analyzer — BCK-09 O |
| 🟢 | `4c4ec6dff` | 2026-03-30 | Frontend (UI) | Observability / Sentry / OTLP | ux: TOAST_REMOVE_DELAY 5s + toast wrapper + session timeout + ?next= param + beforeunload — BCK-24 B |
| 🟡 | `58b131fa3` | 2026-03-30 | Frontend (UI) | Login UI (FE) | forms: mascaras CPF/CNPJ/tel/CEP + MaskedInput + htmlFor/aria-describedby - fecha BCK-19 ALT-06 ALT- |
| 🟡 | `48b864ccd` | 2026-03-30 | Frontend (UI) | FE libs / utils | forms: integra React Hook Form + Zod no login + schemas centralizados — fecha ALT-12 |
| 🟢 | `042aa1335` | 2026-03-30 | Docs | Auditoria / Audit Rev | design-audit: corrige espacamentos arbitrarios + dark mode tokens + relatorio FASE7 — Skill 7 |
| 🟡 | `e3cab62dd` | 2026-03-30 | Frontend (UI) | Skills / canonical-fix | design-tokens: substitui hardcoded hex por tokens LIA nos 15 arquivos mais críticos — Skill 3 BCK-10 |
| 🟢 | `2ccf70373` | 2026-03-30 | Frontend (UI) | Onboarding (FE) | css: reduz \!important de 135 para 47 + consolida dark mode em design-tokens.css — BCK-03 BCK-04 |
| 🟢 | `977c7f947` | 2026-03-30 | Frontend (api/util) | Docs / Specs | design-system: unifica tokens HSL shadcn → aliases para tokens LIA hex — fecha BCK-05 |
| 🟡 | `852d579d6` | 2026-03-30 | Frontend (UI) | §9 Security / Tenant guards | security: sanitize dangerouslySetInnerHTML com DOMPurify — fecha BLQ-03 XSS |
| 🟢 | `581de7314` | 2026-03-30 | Frontend (UI) | §9 Security / Tenant guards | security+obs: npm audit fix, Sentry ativo, not-found/error/loading pages — fecha BLQ-06 BLQ-07 ALT-1 |
| 🟢 | `b08e714e9` | 2026-03-30 | Frontend (api/util) | Observability / Sentry / OTLP | Add HTML sanitization and Sentry error tracking — Integrate Sentry SDK for error monitoring and impl |
| 🟢 | `877d0a349` | 2026-03-30 | Frontend (api/util) | Performance | perf: corrige Cache-Control por tipo de asset + ativa image optimization + reactStrictMode — fecha B |
| 🟢 | `870efa232` | 2026-03-30 | Docs | Docs / Auditorias | docs: consolida FRONTEND_AUDIT_REPORT_FINAL.md em frontend-audit-consolidado-20-dimensoes.md |
| 🟢 | `f888516d2` | 2026-03-30 | Docs | Fase 5 | docs: atualiza score para 10.0/10 — FASE 5 monolith splits concluidos |
| 🟢 | `8313bacca` | 2026-03-30 | Frontend (UI) | Fase 5 | feat: FASE 5 monolith splits — 5 arquivos grandes divididos — ats-integrations-page.tsx: 1522L -> 41 |
| 🟢 | `0d9ac7435` | 2026-03-30 | Frontend (UI) | Task #64 | Task #64: Create consolidated frontend audit report (FRONTEND_AUDIT_REPORT_FINAL.md) — Consolidates  |
| 🟡 | `f98a5711b` | 2026-03-30 | Frontend (UI) | Candidates (FE pages) | docs: remove relatórios parciais (consolidados em frontend-audit-consolidado-20-dimensoes.md) |
| 🟡 | `48e2ace56` | 2026-03-30 | Frontend (UI) | Talent Funnel (FE) | Improve candidate profile and activity tab display and data handling — Update type casting and condi |
| 🟢 | `395266788` | 2026-03-30 | Docs | Docs / Auditorias | docs: relatório consolidado auditoria frontend 20 dimensões |
| 🟡 | `09c2d5670` | 2026-03-30 | Frontend (UI) | Candidates (FE pages) | Update candidate profile and files display with type improvements — Update type definitions and data |
| 🟢 | `8e381fa9f` | 2026-03-30 | Docs | Task #60 | Task #60: Auditoria Frontend Parte 1 — Fundamentos (Dims 1-5) — Created comprehensive frontend audit |
| 🟡 | `42cc398b6` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `c8bd0a972` | 2026-03-30 | Docs | Task #63 | Task #63: Auditoria Frontend Parte 4 — DX e Infraestrutura (Dims 16-20) — Created comprehensive fron |
| 🟡 | `dcbcd92df` | 2026-03-30 | Infra/Config | DevOps / CI | ci: add Playwright E2E job to CI pipeline |
| 🟢 | `de47d2bbc` | 2026-03-30 | Docs | Task #62 | Task #62: Auditoria Frontend Parte 3 — Capacidades (Dims 11-15) — Created comprehensive frontend aud |
| 🟡 | `24cbdc4fd` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `e7a3fe16b` | 2026-03-30 | Docs | Task #61 | Task #61: Auditoria Frontend Parte 2 — Segurança e Integrações (Dims 6-10) — Created comprehensive a |
| 🔴 | `ee302937d` | 2026-03-30 | Frontend (UI) | Fase 3 | feat: FASE 3+4 frontend — ESLint 0, 342 testes, CI/CD pipeline — ESLint: 19 erros -> 0 |
| 🟡 | `4c42a4edf` | 2026-03-30 | Frontend (UI) | Modals (FE) | Update job editing functionality and component structure — Refactor job editing modal and types, upd |
| 🟡 | `90f4c28ab` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `aa861dd48` | 2026-03-30 | Frontend (UI) | §15 WSI | Task #59: WSI x Mercado (BBC Interview) — Documento de analise — Created docs/WSI_x_MERCADO_BBC_INTE |
| 🟡 | `fbe0cab58` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟡 | `dad4d1cca` | 2026-03-30 | Frontend (UI) | UI Components (FE library) | Fix clipped content and improve layout rendering in sidebar — Adjusted the Card component's height c |
| 🟢 | `0a152f1d9` | 2026-03-30 | Frontend (UI) | Screening Config (FE) | Improve UI elements and functionality across several components — Update UI elements and component l |
| 🟡 | `0ae8a0ed9` | 2026-03-30 | Frontend (UI) | Compliance / LGPD / EU AI Act | Fix LIA prompt sidebar UX bugs across 3 pages (DS v4.2.1 compliance) — 3 components fixed: LIASearch |
| 🟡 | `185f8bf75` | 2026-03-30 | Frontend (UI) | Backend Proxy Routes (FE) | Refine code by changing variable declarations and removing unused code — Update variable declaration |
| 🔴 | `0b6a5ea4e` | 2026-03-30 | Frontend (UI) | Task #58 | Fix post-merge runtime errors from Task #58 (Vue Migration) — - Add missing `useState` and `useEffec |
| 🟡 | `dd4b07950` | 2026-03-30 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟡 | `bdc97e897` | 2026-03-29 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `c9cc53583` | 2026-03-29 | Docs | Docs / Diagramas | Add comprehensive architecture diagrams to the documentation — Create a new Excalidraw diagram file  |
| 🟢 | `c82d16096` | 2026-03-29 | Docs | Docs / Diagramas | Add comparative analysis and screening flow details to architecture diagram — Add comparative table, |
| 🟡 | `5453c719b` | 2026-03-29 | Frontend (UI) | Candidates (FE pages) | Update documentation diagram and improve application styling for dark mode — Synchronize the recruit |
| 🔴 | `aa0c6557d` | 2026-03-29 | Frontend (UI) | Compliance / LGPD / EU AI Act | P6 complete rewrite — 22 sections, 13px font, narrative content, Agent Studio, v5 scalability critiq |
| 🟢 | `e9276f9ef` | 2026-03-29 | Frontend (UI) | Docs / Specs | Improve font legibility and standardize text formatting across the platform — Update global CSS and  |
| 🟢 | `8cc0a8ca0` | 2026-03-29 | Frontend (UI) | Chat UI (FE) | Adjust font sizes and remove unused CSS for improved readability — Update text sizes in AgentMemoryI |
| 🟡 | `76bb4c2c7` | 2026-03-29 | Frontend (UI) | Compliance / LGPD / EU AI Act | P6: Add comprehensive pros/cons/recommendations/market references comparative table — Added to Excal |
| 🟡 | `e60a00bef` | 2026-03-29 | Frontend (UI) | Jobs (FE pages) | Centralize status labels for improved maintainability and consistency — Refactors multiple component |
| 🟡 | `7d845c452` | 2026-03-29 | Outro | Frontend (componentes diversos) | Standardize header appearance across multiple pages — Create a reusable header component and apply i |
| 🟢 | `4662d61ac` | 2026-03-29 | Frontend (UI) | Docs / Specs | Create reusable LiaPromptHeader component for consistent LIA prompt titles — - Created `lia-prompt-h |
| 🟢 | `f85817044` | 2026-03-29 | Frontend (UI) | Docs / Specs | Fix issues with displaying job listings and loading states — Update `JobsPage` component to properly |
| 🟡 | `8d1fd2aa8` | 2026-03-29 | Frontend (UI) | §1 Teams Integration | Add P5 Teams Bot to HTML architecture diagram and summary table — - Inserted P5 Teams Bot section (3 |
| 🟢 | `fd850daf7` | 2026-03-29 | Docs | Kanban (vagas) | Complete Excalidraw diagram with per-prompt capabilities (1516→2520 elements) — Added 1004 new eleme |
| 🟢 | `303a3de04` | 2026-03-29 | Frontend (UI) | Docs / Diagramas | Add detailed comparison of prompt capabilities between LIA and v5 — Introduce new sections to the do |
| 🟢 | `23aaa5031` | 2026-03-29 | Frontend (UI) | Compliance / LGPD / EU AI Act | Add comprehensive explanatory text to architecture transversal diagram — Added ~310 lines of detaile |
| 🟢 | `c86edb10b` | 2026-03-29 | Docs | Voice / ElevenLabs / STT | Update component inventory and add ElevenLabs theme analysis — Update the component inventory docume |
| 🟢 | `26b1fee54` | 2026-03-29 | Frontend (api/util) | Triagem (módulo) | Update transversal architecture diagrams: 1. HTML: LIA side now has matching transversal bands (16 c |
| 🟢 | `18cc98e2d` | 2026-03-29 | Frontend (api/util) | Compliance / LGPD / EU AI Act | Rebuild architecture diagrams with transversal layout — - Created unified HTML diagram (architecture |
| 🟢 | `a833a506b` | 2026-03-29 | Docs | Docs / Diagramas | Add LIA architecture diagram to existing v5 diagram file — Adds the LIA architecture diagram alongsi |
| 🟢 | `622790db9` | 2026-03-29 | Frontend (api/util) | Docs / Diagramas | Add detailed architecture diagram for the LIA platform — Generate an HTML architecture diagram for t |
| 🟡 | `ce9578442` | 2026-03-29 | Frontend (UI) | Frontend (componentes diversos) | Update diagrams and code to accurately reflect system architecture — Refactor code and update HTML d |
| 🟡 | `8fd69e94b` | 2026-03-29 | Frontend (UI) | Compliance / LGPD / EU AI Act | Redesign v5 architecture diagram with accurate per-domain coverage matrix — Created comprehensive HT |
| 🟡 | `db4fedc94` | 2026-03-29 | Frontend (UI) | Compliance Dashboard (FE) | Update UI elements with consistent status colors and add system architecture diagram — Refactor UI c |
| 🟢 | `d0bb6aa1f` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | fix: resolve runtime crashes in dev server and related issues — 1. useKanbanPageCore.ts: |
| 🟢 | `55b59f3a3` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | fix: resolve runtime crashes in dev server and related issues — 1. useKanbanPageCore.ts: |
| 🟡 | `dc7bac79e` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | fix: resolve runtime crashes in 3 files blocking dev server — 1. useKanbanPageCore.ts: |
| 🟢 | `cef9de730` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | Create comprehensive AI architecture diagram for Plataforma LIA — - Generated Excalidraw diagram at  |
| 🟡 | `758007611` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | Create comprehensive AI architecture diagram for Plataforma LIA — - Generated Excalidraw diagram at  |
| 🟢 | `eb0162475` | 2026-03-29 | Frontend (UI) | Skills / canonical-fix | Add Excalidraw Diagram Generator skill and update goals management component — Installs the Excalidr |
| 🟢 | `4e0b0f8c8` | 2026-03-29 | Frontend (UI) | Frontend (componentes diversos) | Refactor code to improve organization and maintainability — Reorganize component files into layers a |
| 🟡 | `cd9e0d05e` | 2026-03-29 | Frontend (UI) | Kanban (vagas) | Refactor candidate and job pages with new hooks and UI improvements — Refactors code in `useCandidat |
| 🟡 | `a11879592` | 2026-03-29 | Frontend (UI) | Task #58 | Task #58: Vue Migration — Equivalências shadcn/ui → Vuetify + Convenções — Created comprehensive com |
| 🟡 | `a2421434e` | 2026-03-29 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `62f3f6f66` | 2026-03-29 | Docs | Skills / canonical-fix | Consolidate skills and update documentation to reflect changes — Update `.agents/skills/dei-fairness |
| 🟡 | `692fd66a9` | 2026-03-29 | Frontend (UI) | Skills / canonical-fix | Update candidate and job data structures and organize development skills — Refactor type definitions |
| 🟢 | `191e7244f` | 2026-03-29 | Frontend (UI) | Expandable AI Prompt (FE) | Improve visual styling and layout consistency across the platform — Update styling and layout proper |
| 🟢 | `1c4f56e7e` | 2026-03-29 | Docs | Docs / Specs | Update component inventory with recent project growth metrics — Update the component inventory docum |
| 🟡 | `be19ab5c5` | 2026-03-29 | Outro | Refactor / Cleanup | Add monolith definition to support new project structure — Add a new section for defining monoliths  |
| 🟢 | `622736784` | 2026-03-29 | Frontend (UI) | Jobs (FE pages) | Improve loading state management for job vacancy listings — Move `setIsLoadingJobs(false)` to execut |
| 🟢 | `d533ad4e0` | 2026-03-29 | Frontend (UI) | Modals (FE) | Add safety for recruiter assignment in job modals — Protect JobAssignRecruiterModal from undefined r |
| 🟢 | `d1a96355b` | 2026-03-29 | Frontend (UI) | Candidates (FE pages) | Add search sorting functionality to candidate results view — Fix: Missing setSearchSortBy prop in Ca |
| 🟢 | `17fcaa96f` | 2026-03-29 | Docs | Docs / Specs | Update implementation plan with current metrics and progress — Update the `PLANO_IMPLEMENTACAO_v2.md |
| 🟢 | `dc2a58a68` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Fix code review rejections - remove unsafe `any` and clean up split artifacts — - Removed  |
| 🟢 | `4837d6c8a` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Fix code review rejections - remove unsafe `any` and clean up split artifacts — - Removed  |
| 🟢 | `9deb437bc` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Fix split wiring, remove unsafe any, resolve merge conflicts — - Fixed SCMSectionContent m |
| 🟡 | `ce5ebec87` | 2026-03-29 | Infra/Config | §9 Security / Tenant guards | Task #57: Fix SCMSectionContent split wiring + type cleanup + security — - Fixed SCMSectionContent m |
| 🟡 | `e98512e2a` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Fix SCMSectionContent split wiring + type cleanup — - Fixed SCMSectionContent missing impo |
| 🟢 | `eed3f3972` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Split ALL monolithic files <1500L + fix type contracts — Monolith splits completed: |
| 🟢 | `1aff17772` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Split ALL monolithic files <1500L + fix type contracts — Monolith splits completed: |
| 🟢 | `beaf84528` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Split ALL monolithic files to <1500L, fix canSubmit runtime error — Completed monolith spl |
| 🟡 | `b4c6a5476` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Split useExpandedChatModalCore.tsx from 4033L to <1500L — Completed monolith split of all  |
| 🟢 | `da339b228` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Complete monolith split + any elimination + inline styles — Build fixes: |
| 🟡 | `dcb34aec2` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Complete monolith split + inline style conversion — Build fixes: |
| 🟡 | `f63f7b988` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57 T009: Fix build errors from monolith split — - advancedFiltersTypes.tsx: Add missing `expor |
| 🔴 | `8cbf52ed5` | 2026-03-29 | Frontend (UI) | Task #57 | Task #57: Fix syntax errors in split monolithic files — - Removed undefined 'prompt' variable from u |
| 🟡 | `09bca1312` | 2026-03-28 | Frontend (UI) | Task #56 | Task #56: Split 4 monolithic files into domain modules — lia-api.ts (4800L) → 14 domain modules all  |
| 🟡 | `9c7a4bf02` | 2026-03-28 | Frontend (UI) | Task #56 | Task #56: Split 4 monolithic files into domain modules — - lia-api.ts (4800L) → 11 domain modules in |
| 🟡 | `237cf2198` | 2026-03-28 | Frontend (UI) | Task #55 | Task #55: Eliminate all unsafe `any` in non-monolith files — Orchestrated 7 parallel subagents acros |
| 🟡 | `7016f3b54` | 2026-03-28 | Frontend (UI) | Task #55 | Task #55: Eliminate unsafe `any` in non-monolith files — Orchestrated 5 parallel subagents to apply  |
| 🟡 | `a2a5d5cb2` | 2026-03-28 | Frontend (UI) | Task #55 | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files),  |
| 🟡 | `4d2c8138e` | 2026-03-28 | Frontend (UI) | Task #55 | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files),  |
| 🔴 | `c54c0e87d` | 2026-03-28 | Frontend (UI) | Task #55 | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files),  |
| 🟡 | `1ff1deee2` | 2026-03-28 | Frontend (UI) | Task #54 | Task #54 (DS Consistency) — Fix all CSS var + hex-alpha concatenation bugs — Fixed 10+ broken `${css |
| 🔴 | `2a9bb7437` | 2026-03-28 | Frontend (UI) | Fase 10 | Task #54: Fase 10 Sprint 1A — DS Consistency complete — Full DS v4.2.1 mechanical alignment across p |
| 🟢 | `ca50dd156` | 2026-03-28 | Frontend (UI) | Fase 10 | Task #54: Fase 10 Sprint 1A — DS Consistency (rounded-md + cores residuais) — Mechanical DS v4.2.1 a |
| 🔴 | `cb63551fa` | 2026-03-28 | Frontend (UI) | Fase 10 | Task #54: Fase 10 Sprint 1A — DS Consistency (rounded-md + cores residuais) — Mechanical DS v4.2.1 a |
| 🟡 | `4e4c43cb4` | 2026-03-28 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🔴 | `2e65c1f44` | 2026-03-28 | Frontend (UI) | Fase 5 | Fase 5 parcial — var(--eleven-*) → Tailwind DS tokens (98 arquivos) — Substitui 2.800+ ocorrências d |
| 🔴 | `e65cda8d4` | 2026-03-28 | Frontend (UI) | Sprint 4.10 | Sprint 4.10 + 4.11 — console.log removal e splits chat/candidates — - Remove console.log/error/warn  |
| 🟢 | `835a58bbd` | 2026-03-28 | Docs | Sprint 4.10 | docs: atualiza inventário de componentes pós-Sprint 4.10 — Reflete estado atual: Fases 0–3 concluída |
| 🟡 | `72996aed7` | 2026-03-28 | Frontend (UI) | Sprint 4.10 | Sprint 4.10 residual — Remoção de style={} inline: tokens DS v4.2.1 — Substitui últimos rgba() e sty |
| 🟡 | `23d879d0b` | 2026-03-28 | Frontend (UI) | Sprint 4.10 | Sprint 4.10 — DS tokens, type safety e dark mode — - EditArchetypeModal: removidos 5 rgba() inline → |
| 🟢 | `d7c96cfcb` | 2026-03-28 | Frontend (UI) | §15 WSI | Feature Audit — Correções D3/D7/D13 — D13 (Segurança/PII): removidos 2 console.log com nome+comentár |
| 🟢 | `8a6620158` | 2026-03-28 | Frontend (UI) | Kanban (vagas) | fix: ReferenceError setBulkActionType TDZ em job-kanban-page — useKanbanBulkActions estava sendo cha |
| 🟡 | `6efc60dc5` | 2026-03-28 | Frontend (UI) | Fase 2 | Fase 2 — Tokenização hex hardcoded: 24 substituições em 13 arquivos — Novos tokens criados: whatsapp |
| 🟢 | `006f69ec7` | 2026-03-28 | Frontend (UI) | Sprint 4.9 | Sprint 4.9 — Extração CandidateTableCellRenderer de candidates-page (-737L) — candidates-page.tsx: 5 |
| 🟡 | `5e47dcaf0` | 2026-03-28 | Frontend (UI) | Fase 2 | Fase 2 residual — Tokenização parcial: tailwind.config + 5 componentes — tailwind.config.ts: novos t |
| 🟢 | `6fb9868fb` | 2026-03-28 | Frontend (UI) | Fase 3 | Fase 3 — Consolidação de Badges: dark mode + tokens DS v4.2.1 — setup-alert-badge: transition-shadow |
| 🟢 | `217ebd49a` | 2026-03-28 | Frontend (UI) | Sprint 4.9 | Sprint 4.9 — Monolith split smart-search-input: 5.463L → 4.586L (-877L) — Extraídos: |
| 🟢 | `70d56b82b` | 2026-03-28 | Frontend (UI) | Bridge React→Vue | Bridge Vue — fixes residuais: imports type-only + chatScrollRef externalizado — useCandidatesSearch: |
| 🟡 | `cb109cdc1` | 2026-03-28 | Frontend (UI) | Bridge React→Vue | Auditoria DS + Bridge Vue + Code Review — Sprints 4.6-4.8 — DS v4.2.1 (5 correções): |
| 🔴 | `30b18fff7` | 2026-03-28 | Frontend (UI) | Sprint 4.6-4.8 | Residual Sprint 4.6-4.8 — Tokenização, ajustes DS e updates de componentes — tailwind.config.ts: tok |
| 🟡 | `500a09555` | 2026-03-28 | Frontend (UI) | Sprint 4.8 | Sprint 4.8 — Monolith split expanded-chat-modal: 11.228L → 4.423L (-6.805L) — Extraídos: ExpandedCha |
| 🟡 | `8ecac991a` | 2026-03-28 | Frontend (UI) | Kanban (vagas) | Sprint 4.7 — Extração views/hooks de kanban, candidates e candidate-preview (-6.535L em 3 monolitos) |
| 🟡 | `8b730e778` | 2026-03-28 | Frontend (UI) | Sprint 4.6 | Sprint 4.6 — Extração de 11 componentes de 3 páginas monolito — jobs-page: -3.309L → ColumnConfigPan |
| 🟢 | `a639c30f4` | 2026-03-27 | Frontend (UI) | §15 WSI | Sprint 4.6 — Extração WSITutorialModal de jobs-page (-344 linhas) |
| 🟢 | `809deb4a9` | 2026-03-27 | Frontend (UI) | Sprint 4.6 | Sprint 4.6 — Extração 4 modais de confirmação de candidates-page (-267 linhas) — GlobalExpansionConf |
| 🟢 | `13516a9c5` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Sprint 4.6 — Extração LIAQuestionsPanel de job-kanban-page (-199 linhas) |
| 🟢 | `477b682bb` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Sprint 4.6 — Extração TestHistoryModal de job-kanban-page (-344 linhas) |
| 🟢 | `104e8f686` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Sprint 4.6 — Extração TestLibraryModal de job-kanban-page (-519 linhas) |
| 🟢 | `a318aa690` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Sprint 4.6 — Extração TestPreviewModal + LIASuggestionsPanel de job-kanban-page (-377 linhas) |
| 🟢 | `5fe9a6348` | 2026-03-27 | Frontend (UI) | Sprint 4.6 | Sprint 4.6 — Refactor handleSendMessage: 2030L → 61L thin dispatcher — Extraiu 12 funções handler da |
| 🔴 | `8518c0ac9` | 2026-03-27 | Frontend (UI) | Fase 5D | Fase 5d — Tokenização paleta secundária → tokens semânticos (54 arquivos, ~233 ocorrências) — Comple |
| 🔴 | `1b05d97cc` | 2026-03-27 | Frontend (UI) | Fase 5C | Fase 5c — Tokenização cores nativas → tokens semânticos (373 arquivos, ~8878 ocorrências) — Varredur |
| 🟡 | `e0bcd639f` | 2026-03-27 | Frontend (UI) | Fase 5B | Fase 5b — Tokenização cores nativas → tokens semânticos (15 arquivos) — Substitui utilities nativas  |
| 🔴 | `a4103ebb5` | 2026-03-27 | Frontend (UI) | Fase 5A | Fase 5a — Remoção fontFamily Open Sans inline (1019 → 111 ocorrências, -89%) — Body já usa Open Sans |
| 🟡 | `fa7c73c64` | 2026-03-27 | Frontend (UI) | Fase 2 | Fase 2 residual — Tokenização cyan nativo → wedo-cyan (15 arquivos, 81 substituições) |
| 🟡 | `e2def4a38` | 2026-03-27 | Frontend (UI) | Skills / canonical-fix | Sprint 4.5 — Extração de modais: AddTechnicalSkill + AddCompetency + AddBenefit + SkipCompetenciesWa |
| 🟢 | `23757c7ab` | 2026-03-27 | Frontend (UI) | Sprint 4.4 | Sprint 4.4 — InputEvaluationStage extraído (-116 linhas no modal) — Extração da etapa input-evaluati |
| 🟢 | `d91580e94` | 2026-03-27 | Frontend (UI) | Sprint 4.4 | Sprint 4.4 — ReviewPublishStage extraído (-610 linhas no modal) — Extração da etapa review-publish ( |
| 🟢 | `959e401df` | 2026-03-27 | Frontend (UI) | Sprint 4.4 | Sprint 4.4 — SearchCalibrationStage extraído (-475 linhas no modal) — Extração da etapa search-calib |
| 🟢 | `9a99a3713` | 2026-03-27 | Frontend (UI) | Sprint 4.3 | Sprint 4.3 — ChatMessageList extraído + message-format-utils — - ChatMessageList.tsx: renderização d |
| 🟢 | `d455f689e` | 2026-03-27 | Frontend (UI) | Sprint 4.3 | Sprint 4.3 — Extração de modais: ClearDraftConfirm + EditCriteria + remoção dead code — - ClearDraft |
| 🟡 | `117c551d3` | 2026-03-27 | Frontend (UI) | Fase 2D | Fase 2D — Restrição do wedo-cyan (597 → 545, -52 usos decorativos) — Removido cyan de elementos não- |
| 🔴 | `320871d8c` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 9 — Tokenização de hex hardcoded (conclusão) — Últimos 31 arquivos convertidos para t |
| 🟢 | `f2935fc51` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 8: tokenização hex (7 arquivos, ~20 substituições) — - job-kanban-page: border-l-[#1F |
| 🟢 | `b5a28db3b` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Update styling for candidate review and job kanban pages — Refactor UI elements by adjusting color s |
| 🟡 | `bbe0f3697` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 7: tokenização hex (6 arquivos, ~15 substituições) — - agent-detail-panel: #60D186 →  |
| 🟡 | `96a723874` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 6: tokenização hex (7 arquivos, ~20 substituições) — - jobs-page: #D5BFA8 → gray-300, |
| 🟢 | `e1426f848` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 5: tokenização hex (5 arquivos, ~30 substituições) — - lia-library-page: category col |
| 🟢 | `83f5c90f9` | 2026-03-27 | Frontend (UI) | Frontend (componentes diversos) | Update UI colors and styling for better visual consistency — Refactors color variables in `chat-page |
| 🟢 | `523933488` | 2026-03-27 | Frontend (UI) | Frontend (componentes diversos) | Update application colors and styles to use consistent design tokens — Refactors various UI componen |
| 🟡 | `8a0bbd763` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C — Lote 3: tokenização hex (8 arquivos, ~50 substituições) — - CATEGORY_COLORS pastel → var(- |
| 🟡 | `49757639e` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C/2D — Lote 2: tokenização hex residuais (9 arquivos) — Substitui hex hardcoded por CSS vars s |
| 🟡 | `2947fb28a` | 2026-03-27 | Frontend (UI) | Fase 2C | Fase 2C/2D — Tokenização de hex hardcoded (650 → 353, -46%) — Bridge Architecture: substituição sist |
| 🟢 | `035f5bd6a` | 2026-03-27 | Frontend (UI) | Sprint 4.2 | Sprint 4.2 — Integração dos hooks de domínio no expanded-chat-modal — Substitui useState inline por  |
| 🟡 | `819ee7bcb` | 2026-03-27 | Frontend (UI) | §15 WSI | Add foundational architectural principles and new features to the documentation — Introduces the "Br |
| 🟢 | `ef6a39ea5` | 2026-03-27 | Frontend (UI) | §15 WSI | Add new state management hooks for expanded chat functionality — Add new hooks for managing calibrat |
| 🟢 | `e7d039685` | 2026-03-27 | Frontend (UI) | Kanban (vagas) | Expand INVENTARIO_COMPONENTES.md to 100% coverage (1396→2228 lines) — Original task: Expand the inve |
| 🟡 | `0dd00d71e` | 2026-03-27 | Infra/Config | Configurações (hub) | Add more detailed code analysis commands to inventory — Update settings to include new Bash commands |
| 🟡 | `ca7e87e04` | 2026-03-27 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `cc4bfa44b` | 2026-03-27 | Docs | Fase 4 | Fase 4 — Plano revisado com análise profunda do expanded-chat-modal — Análise revelou: 76 useState,  |
| 🟡 | `1a465e204` | 2026-03-27 | Frontend (UI) | Fase 3 | Fase 3 — Consolidação de Badges: tokens DS + órfãos removidos — 3A badge.tsx: rgba() hardcoded → tok |
| 🟢 | `91155fb24` | 2026-03-27 | Docs | Fase 3 | Fase 3 — Plano revisado com tokens semânticos, Vuetify map e code review — - Diagnóstico real: 2 órf |
| 🔴 | `e1ab7b604` | 2026-03-27 | Frontend (UI) | Fase 2 | Fase 2 — Gaps Finais: gray scale completo + pipeline 100% tokenizado — - Adiciona --gray-300 e --gra |
| 🔴 | `43e78bdd6` | 2026-03-27 | Frontend (UI) | Fase 2 | Fase 2 — Tokenização de Cores com Direção Monocromática — Reduz 150+ hex hardcoded para ~15 tokens s |
| 🟡 | `5f9091740` | 2026-03-27 | Frontend (UI) | Frontend (componentes diversos) | Remove unused code and update documentation — Remove archived components and update the component in |
| 🟢 | `70a4c5733` | 2026-03-27 | Docs | Task #53 | Task #53: Add optimization analysis and 6-phase plan to INVENTARIO_COMPONENTES.md — Added Sections 1 |
| 🟡 | `147207344` | 2026-03-27 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `5db692bc9` | 2026-03-27 | Docs | Docs (geral) | Catalog all existing visual components on the platform — Create a comprehensive inventory of 465 vis |
| 🟢 | `c58d25d8e` | 2026-03-27 | Docs | Docs (geral) | Update diagnostic document comparing React and Vue frontend standards — Create a comprehensive diagn |
| 🟡 | `2b02e46a2` | 2026-03-27 | Infra/Config | Scripts / CLI | Add a command to find configuration files for Nuxt projects — Add a new bash command to find .config |
| 🟢 | `dcddfa39c` | 2026-03-26 | Docs | Docs / WeDO planos | Organize project documentation and working files — Moves working documents and analyses to a dedicat |
| 🟡 | `deeb59592` | 2026-03-26 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟡 | `17e049be6` | 2026-03-26 | Frontend (UI) | Task #51 | Task #51: Standardize all LIA chat UIs across the platform — - Added chat-cyan (#00B8B8) to tailwind |
| 🟢 | `f79c266b9` | 2026-03-26 | Docs | Docs / Specs | Update onboarding document with correct specifications count — Corrected the number of specification |
| 🟢 | `d3ee0f9de` | 2026-03-26 | Docs | Task #50 | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — C |
| 🟢 | `5462f8b81` | 2026-03-26 | Docs | Task #50 | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — C |
| 🟢 | `ebbcac880` | 2026-03-26 | Docs | Task #50 | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — C |
| 🟢 | `255ea29c1` | 2026-03-26 | Docs | Task #49 | Task #49: Fix code review issues in DESIGN_SYSTEM.md and UX_PATTERNS.md — Code review identified 5 i |
| 🟢 | `8ad51ef02` | 2026-03-26 | Frontend (UI) | LIA Float UI (FE) | Standardize floating LIA chat formatting to match main chat style — - Created lib/chat-format.ts wit |
| 🟢 | `482ae4dc2` | 2026-03-26 | Frontend (api/util) | FE libs / utils | Standardize floating LIA chat to match job creation prompt style — Problem: Floating LIA chat showed |
| 🟢 | `7b7e0e9e3` | 2026-03-26 | Frontend (UI) | LIA Float UI (FE) | Standardize floating LIA chat to match job creation prompt style — Problem: Floating LIA chat was sh |
| 🟢 | `964cba894` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v8) — Fixed all remaining endpoint/schem |
| 🟢 | `1b32a5cb5` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v7) — All fields/endpoints verified agai |
| 🟢 | `fa0863239` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v6) — Final fixes with source-verified c |
| 🟢 | `2b3c8d96a` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v5) — Fixed all verified inaccuracies ag |
| 🟢 | `f285c5273` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v4) — All factual inaccuracies fixed wit |
| 🟢 | `9082c86fd` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v3 fixes) — Fixed all code review issues |
| 🟢 | `33b50bf96` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (fixed) — Updated both backend specificat |
| 🟢 | `3725250df` | 2026-03-26 | Docs | Task #48 | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md — Created/updated two comprehensive backe |
| 🟢 | `ea3e1e26f` | 2026-03-26 | Docs | Task #47 | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritt |
| 🟢 | `d3d815477` | 2026-03-26 | Docs | Task #47 | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritt |
| 🟢 | `59775a4f2` | 2026-03-26 | Docs | Task #47 | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritt |
| 🟢 | `d61b00193` | 2026-03-26 | Empty/merge | Task #47 | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritt |
| 🟢 | `289f1d030` | 2026-03-26 | Docs | Task #47 | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritt |
| 🟢 | `c758211fa` | 2026-03-26 | Docs | Task #47 | Task #47: Comprehensive PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (624 lines) — PROMPT_S |
| 🟢 | `6cf53834c` | 2026-03-26 | Docs | §14 BYOK + LLM Factory | Update AI docs: Gemini-only in production (user confirmed) — User confirmed WeDOTalent uses ONLY Gem |
| 🟢 | `331a91bbb` | 2026-03-26 | Docs | Task #46 | Task #46: Update PLATFORM_MAP + FRONTEND_STANDARDS with real ats_front code — FRONTEND_STANDARDS.md  |
| 🟢 | `68abc6513` | 2026-03-26 | Docs | Task #46 | Task #46: Update PLATFORM_MAP + FRONTEND_STANDARDS with real ats_front code — FRONTEND_STANDARDS.md  |
| 🟢 | `3aacedc6b` | 2026-03-26 | Docs | Docs / Specs | Task start baseline checkpoint for code review |
| 🟢 | `d1abb5bb7` | 2026-03-26 | Docs | Task #45 | Task #45: Fix all 3 code review issues in AI SDD docs — 1. BaseAgent interface (AI_ARCHITECTURE.md § |
| 🟢 | `7db459b68` | 2026-03-26 | Docs | Task #45 | Task #45: AI SDD docs — all tools/tasks verified from actual code — All 3 AI spec documents correcte |
| 🟢 | `bb40ce771` | 2026-03-26 | Docs | Task #45 | Task #45: AI SDD docs — tool lists verified from actual registries — All 3 AI spec documents correct |
| 🟢 | `be405c235` | 2026-03-26 | Docs | Task #45 | Task #45: AI SDD docs — all tool counts verified from actual registries — All 3 AI spec documents co |
| 🟢 | `b4e2ed7fb` | 2026-03-26 | Docs | Task #45 | Task #45: Enrich AI SDD docs — code-verified from actual source files — All 3 AI spec documents rewr |
| 🟢 | `b49864347` | 2026-03-26 | Docs | Task #45 | Task #45: Enrich AI SDD docs with full lia-agent-system coverage — All 3 AI spec documents rewritten |
| 🟢 | `8dd98df85` | 2026-03-26 | Docs | Task #45 | Task #45: Enrich AI SDD docs with full lia-agent-system coverage — All 3 AI spec documents rewritten |
| 🟢 | `1340756a4` | 2026-03-26 | Docs | Docs / Specs | Update platform documentation and create new technical specifications — Create 10 new specification  |
| 🟢 | `1eb896052` | 2026-03-26 | Docs | Docs (geral) | Add comprehensive Vue and Vuetify migration guides to design inventory — Update the design inventory |
| 🟢 | `ae3f2623a` | 2026-03-26 | Docs | Task #44 | Task #44: Inventário Completo de Design — Plataforma LIA — Comprehensive design inventory document ( |
| 🟢 | `f7598fc88` | 2026-03-25 | Docs | Task #44 | Task #44: Inventário Completo de Design — Plataforma LIA (área operacional) — Expanded docs/PRODUCT_ |
| 🟢 | `41c2ac318` | 2026-03-25 | Docs | Task #44 | Task #44: Inventário Completo de Design — Plataforma LIA (área operacional) — Created comprehensive  |
| 🟡 | `ba2a3654d` | 2026-03-25 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `c6e510b80` | 2026-03-25 | Docs | §15 WSI | docs: Add WSI complete reproduction task plan — Comprehensive task plan (1939 lines) for fully repro |
| 🔴 | `c74ed63da` | 2026-03-25 | Cross IA↔Front | §15 WSI | Sprint WSI-10: F6.8 validation, F9-1 trait weighting, F10-6 confidence, F11-3 cache, F11-6 ranking — |
| 🟡 | `082f349e9` | 2026-03-25 | Backend | Skills / canonical-fix | Update skills catalog route to include correct path prefix — Correct the API route prefix for the sk |
| 🟢 | `ac67e764e` | 2026-03-25 | Frontend (UI) | Frontend (componentes diversos) | Update enriched job description display after saving — Add local overrides for job data to correctly |
| 🟡 | `e3138f74a` | 2026-03-25 | Backend | FastAPI v1 endpoints | Fix: enriched_jd not persisted after generation — missing from listing endpoint — Root cause: The GE |
| 🔴 | `554b5925d` | 2026-03-25 | Cross IA↔Front | §15 WSI | Task #43: WSI Competency Minimums — Document + Platform Prompts + Pipeline — Changes: |
| 🔴 | `67d384e32` | 2026-03-25 | Cross IA↔Front | §15 WSI | Align WSI question counts with F5 methodology spec (7 compact, 12 full) — Backend (wsi_screening_pip |
| 🟢 | `be5f4b3f1` | 2026-03-25 | Frontend (UI) | Screening Config (FE) | Remove AI-generated question feature and related unused elements — Removes the AI-generated question |
| 🔴 | `6b9944097` | 2026-03-25 | Cross IA↔Front | §15 WSI | Remove misplaced "Gerar Perguntas WSI" button from JDEvaluationPanel — The button was incorrectly pl |
| 🟢 | `418d976fe` | 2026-03-25 | Frontend (UI) | Modals (FE) | Enhance job publishing with detailed screening checklists and Big Five traits — Introduce a comprehe |
| 🟢 | `a1950e09c` | 2026-03-25 | Frontend (UI) | Task #41 | Task #41: Fix copy feedback button + remove dead ranking code — - Fixed field name: uses response_an |
| 🟢 | `99fe4c711` | 2026-03-25 | Frontend (UI) | Task #41 | Task #41: Fix copy feedback button to use F11 response_analyses data — - Fixed field name mismatch:  |
| 🟢 | `2c7d20500` | 2026-03-25 | Frontend (UI) | Triagem (módulo) | Task #41: Triagem details modal — mockup alignment improvements — Changes in this increment: |
| 🔴 | `8425b8eea` | 2026-03-25 | Cross Back↔Front | Triagem (módulo) | Task #41: Triagem details modal pixel-perfect mockup alignment — Backend (F11 endpoint): |
| 🟡 | `a16ac44de` | 2026-03-25 | Backend | Task #40 | Task #40: F11 Report Engine — Final fixes and HTTP 422 hard block — Changes in this session (complet |
| 🟡 | `655a0ae66` | 2026-03-24 | Backend | Task #40 | Task #40: F11 Report — Endpoint GET + G1-G6 Gates + SHA-256 + CBI + JD Evaluate — ## Changes in this |
| 🟢 | `4932cf10f` | 2026-03-24 | Empty/merge | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Backend (wsi_determ |
| 🟡 | `b47c2bfb5` | 2026-03-24 | IA | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Backend (wsi_determ |
| 🟡 | `45a8bb6b5` | 2026-03-24 | IA | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Backend (wsi_determ |
| 🟡 | `cee7006c7` | 2026-03-24 | IA | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Backend (wsi_determ |
| 🟢 | `145cbd912` | 2026-03-24 | Empty/merge | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Changes in this ses |
| 🔴 | `06154d67a` | 2026-03-24 | Cross IA↔Front | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Changes in this ses |
| 🟢 | `4fdcd7a69` | 2026-03-24 | Frontend (UI) | §15 WSI | Task #39: WSI — 6 Níveis de Classificação + SENIORITY_WEIGHTS + WSI_CUTOFFS — ## Summary |
| 🔴 | `35f05cf29` | 2026-03-24 | Cross IA↔Front | §15 WSI | Enhance job screening and publishing with improved WSI validation and feedback — Implement determini |
| 🟢 | `998a0caf2` | 2026-03-24 | Docs | §15 WSI | Update scoring and classifications to match methodology documentation — Refactor WSI scoring and cla |
| 🟢 | `f1dfd15f5` | 2026-03-24 | Docs | Docs (geral) | Add detailed UI specifications and AI prompt template for report generation — Adds Section 11.6 deta |
| 🟡 | `4646e4b0c` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Align status badges and confidence indicators horizontally — Adjust the layout to display status bad |
| 🟡 | `a91399cd0` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Task #38: Mockup WSI — 6 campos novos nos 3 tabs — Adicionados 6 campos ausentes identificados na an |
| 🟡 | `a5fb51e79` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Task #38: Mockup WSI — 6 campos novos nos 3 tabs — Adicionados 6 campos ausentes identificados na an |
| 🟡 | `156b73a94` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Task #38: Mockup WSI — 6 campos novos nos 3 tabs — Adicionados 6 campos ausentes identificados na an |
| 🟡 | `5138d045a` | 2026-03-24 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `99cae8cfa` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Improve candidate evaluation by adding trait relevance and detail — Update Big Five personality trai |
| 🟡 | `fe87bc26d` | 2026-03-24 | Outro | Mockup Sandbox (artefato gerado) | Add detailed mockups for candidate evaluation tabs — Introduce new mockup components for `Tab1Respos |
| 🟢 | `81bdebc9e` | 2026-03-24 | Docs | Compliance / LGPD / EU AI Act | docs: adiciona Apêndice B — dívida técnica de centralização de compliance — Tarefa #37 — SDD: Apêndi |
| 🟢 | `a9e6ff25f` | 2026-03-24 | Docs | Compliance / LGPD / EU AI Act | docs: adiciona Apêndice D — dívida técnica de centralização de compliance — Tarefa #37 — SDD: Apêndi |
| 🟡 | `ec78017b6` | 2026-03-24 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `011914528` | 2026-03-24 | Docs | Compliance / LGPD / EU AI Act | Add validation checklists to enhance prompt development and compliance — Integrate comprehensive val |
| 🟢 | `5be6989ef` | 2026-03-24 | Docs | §15 WSI | docs(WSI): adiciona 9 prompts/templates completos com fairness, LGPD e governança — Expansão do WSI_ |
| 🟢 | `fe59dc81b` | 2026-03-24 | Docs | §15 WSI | Reorganizar WSI_METHODOLOGY_COMPLETE_v2.md + corrigir PLATFORM_MAP auth — WSI Methodology (principal |
| 🟢 | `db3dfd118` | 2026-03-24 | Docs | §15 WSI | Reorganizar e completar WSI_METHODOLOGY_COMPLETE_v2.md como guia de referência — Reestruturação comp |
| 🟢 | `aecc63a25` | 2026-03-24 | Docs | §15 WSI | Add operational definitions for Bloom and Dreyfus levels in question generation — Update the methodo |
| 🟢 | `e066566a9` | 2026-03-24 | Docs | §18 Senioridade + Job Migration | Update scoring methodology to adapt question distribution by seniority — Refine WSI calculation meth |
| 🟢 | `c1615d3a0` | 2026-03-24 | Docs | Docs (geral) | Update methodology to define job description quality and create an ideal prompt — Refactor the metho |
| 🟢 | `977e38405` | 2026-03-24 | Docs | Docs (geral) | Add criteria for approving or rejecting candidates and a full consultant report — Add Phase 10 detai |
| 🟢 | `dd0219f14` | 2026-03-24 | Docs | §15 WSI | docs: cria WSI_METHODOLOGY_COMPLETE_v2.md com metodologia completa de triagem — Documento canônico p |
| 🟢 | `a41c8d390` | 2026-03-24 | Docs | Docs / Specs | Update backend and frontend standards documentation based on GitHub repositories — Refactor backend  |
| 🟢 | `d77363cde` | 2026-03-24 | Docs | Docs / Specs | Add comprehensive frontend and backend coding standards documentation — Generate documentation for f |
| 🟢 | `6bf0e714c` | 2026-03-24 | Docs | Docs (geral) | Create a guide for coding standards and best practices — Generate a comprehensive CODING_STANDARDS.m |
| 🟢 | `7b9317ff1` | 2026-03-24 | Docs | Docs (geral) | Add comprehensive architecture documentation for the platform — Create `docs/ARCHITECTURE.md` detail |
| 🟢 | `972c2efaf` | 2026-03-24 | Docs | Task #36 | docs: SDD PLATFORM_MAP.md — mapa completo da plataforma WeDOTalent — Task #36 — SDD — PLATFORM_MAP d |
| 🟡 | `4e46858de` | 2026-03-24 | Outro | Scripts / Jira tooling | Improve analysis script by extracting BetterBugs links and optimizing LLM calls — Enhance the `adf_t |
| 🟡 | `8fff66478` | 2026-03-23 | Outro | Scripts / Jira tooling | Stop updating card descriptions and post analysis as comments — Replaces direct updates to card desc |
| 🟢 | `9994a42e3` | 2026-03-23 | Docs | Docs (geral) | Add verification for Jira description updates — Add a check after updating the Jira card description |
| 🟡 | `cb323fc58` | 2026-03-23 | Outro | Scripts / Jira tooling | Add detailed design and quality assurance information to Jira cards — Adds a new function to analyze |
| 🟡 | `efd618f8d` | 2026-03-23 | Outro | Scripts / Jira tooling | Improve AI model integration and code analysis capabilities — Update Anthropic API integration to us |
| 🟢 | `de0ed094c` | 2026-03-23 | Docs | scope: design-standardize | fix(design-standardize): corrigir inconsistência de proporção tipográfica no checklist — Checklist f |
| 🟢 | `5e78ea940` | 2026-03-23 | Empty/merge | Skills / canonical-fix | fix(skills): preencher gaps de documentação nas skills de agente IA (Task #35) — Correções de numera |
| 🟢 | `2e07c287d` | 2026-03-23 | Docs | Policy / Job Creation | fix(skills): corrigir shadow policy, checklist backend e breakpoints — - design-standardize: shadow  |
| 🟢 | `829371711` | 2026-03-23 | Empty/merge | Skills / canonical-fix | fix(skills): preencher gaps de documentação nas skills de agente IA (Task #35) — Correções de numera |
| 🟢 | `f22ba3f54` | 2026-03-23 | Docs | Skills / canonical-fix | fix(skills): corrigir numerações duplicadas + preencher gaps DS e backend — - wedo-governance: renom |
| 🟡 | `fb9b1b536` | 2026-03-23 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `b0aeb9aac` | 2026-03-23 | Docs | Skills / canonical-fix | Update diagram to clarify orchestrator and skill relationships — Update docs/skills-diagram.html to  |
| 🟢 | `9b9c44ddc` | 2026-03-23 | Docs | Docs (geral) | docs: corrige documentacao - Replit le codigo, GitHub multi-repo, Claude analisa — - Visao geral ree |
| 🟢 | `b8999cf40` | 2026-03-23 | Docs | scope: scripts | feat(scripts): BetterBugs content fetching + documentacao completa — BetterBugs Integration (ambos o |
| 🟢 | `f58037dca` | 2026-03-23 | Empty/merge | scope: scripts | feat(scripts): spec-driven sections completas nos dois scripts Jira — Script 1 (jira-fetch-analyze.p |
| 🟡 | `972574ae7` | 2026-03-23 | Outro | scope: scripts | feat(scripts): add spec-driven sections to ADF builders (Script 1 + 2) — Script 1 (jira-fetch-analyz |
| 🟢 | `d33e1f9d5` | 2026-03-23 | Docs | §15 WSI | scripts: Script 1 — issues de funcionalidade com blocos multi-layer — Cada issue de funcionalidade a |
| 🟢 | `ffda2cc9a` | 2026-03-23 | Docs | Docs (geral) | scripts: Script 1 — adiciona ANTES/DEPOIS Vue, Vuetify defaults e bloco vuetify.ts — jira-fetch-anal |
| 🟢 | `f9d92fe91` | 2026-03-23 | Docs | Docs (geral) | scripts: atualiza jira-fetch-analyze.py (escopo completo) + templates de exemplo — jira-fetch-analyz |
| 🟡 | `decb3621b` | 2026-03-23 | Outro | Scripts / Jira tooling | scripts: adiciona jira-fetch-analyze.py e jira-audit-design.py — jira-fetch-analyze.py (comando fetc |
| 🟢 | `d1ad4ad6b` | 2026-03-23 | Docs | Docs (geral) | Update scoring system to a 0-10 scale and refine penalties — Update documentation to reflect the tra |
| 🟢 | `9d529546f` | 2026-03-23 | Docs | §15 WSI | docs: atualiza LIA_UNIFIED_METHODOLOGY.md para versão 1.2 — Mudanças na seção 4.6 (Blocos): |
| 🔴 | `f5ebbfdaf` | 2026-03-23 | Cross IA↔Front | §15 WSI | feat(wsi): unificação pipeline WSI — fonte única de verdade para perguntas de triagem — ## Objetivo |
| 🟡 | `be79c6ab6` | 2026-03-23 | IA | Skills / canonical-fix | Update how candidate skills and traits are extracted and used — Enhance the WSI service to extract 5 |
| 🟢 | `8271be3c2` | 2026-03-23 | Docs | Docs (geral) | Update methodology to detail competency extraction and question generation — Refine `docs/LIA_UNIFIE |
| 🟢 | `d3b648b51` | 2026-03-23 | Docs | §15 WSI | docs: adiciona seções 4.13, 10.6 e 10.7 ao LIA_UNIFIED_METHODOLOGY.md — Três seções adicionadas ao d |
| 🟢 | `4fe77dfb7` | 2026-03-22 | Docs | Compliance / LGPD / EU AI Act | Update audit logging to use existing handler and improve error handling — Refactor the audit callbac |
| 🟢 | `cb3766888` | 2026-03-22 | Docs | Docs / Propostas | Add visual diagrams explaining proposed architecture changes — Add ASCII diagrams to illustrate curr |
| 🟢 | `286ed1992` | 2026-03-22 | Docs | Observability / Sentry / OTLP | Enhance system observability with tracing, metrics, and structured logging — Introduce OpenTelemetry |
| 🟢 | `347ffe286` | 2026-03-22 | Docs | Compliance / LGPD / EU AI Act | docs: add section 23.12.7 — full operational code guide for Caminho 3 (CompliancePipeline) — Context |
| 🟢 | `7ebcf72c7` | 2026-03-22 | Docs | Docs / Propostas | Add detailed implementation guides for migrating code to a new structure — Introduce comprehensive g |
| 🟢 | `401eb2931` | 2026-03-22 | Docs | Compliance / LGPD / EU AI Act | Standardize service imports to improve code organization — Update import paths in integration exampl |
| 🟢 | `07bb528b0` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — seção 23.9+23.10 com 1653 linhas, 23 blocos de integração exata, zero código invent |
| 🟢 | `2870155c9` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — corrige dois blockers do code review — Blocker 1: Código inventado ("padrão de inte |
| 🟢 | `d428c42a6` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — seção 23.9 com código real v5 e caminhos exatos verificados no repositório — Dados  |
| 🟢 | `4897ca3ec` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — corrigidos inconsistências de mapeamento e caminhos exatos de arquivos v5 — Problem |
| 🟢 | `0c07091c9` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — seção 23.9 reescrita com 23 concerns domain-specific corretos — Problema anterior:  |
| 🟢 | `5fb0f09e2` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — seção 23 finalizada com tabela de cobertura por domínio e correções — Documento: pr |
| 🟢 | `f47838381` | 2026-03-22 | Docs | Task #33 | docs: Task #33 finalizada — correção de assinaturas reais de métodos LIA — Documento: proposals/diag |
| 🟢 | `e1f074bfd` | 2026-03-22 | Docs | Task #33 | docs: Task #33 finalizada — seção 23 completa com 23 concerns + diagnóstico arquitetural — Documento |
| 🟢 | `ae08dda10` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — seções 23.9 e 23.10 completas com 23 concerns detalhados e diagnóstico arquitetural |
| 🟢 | `a31ddaf6b` | 2026-03-22 | Docs | Task #33 | docs: Task #33 — adicionar seção 23.9 com análise detalhada de todos os 23 concerns — Objetivo da ta |
| 🟡 | `a43bafa74` | 2026-03-22 | Outro | Compliance / LGPD / EU AI Act | Add static HTML files for canvas diagrams — Generate self-contained HTML files for "Estado Atual — v |
| 🔴 | `d1230253f` | 2026-03-22 | Infra/Config | Mockup Sandbox (artefato gerado) | Add interactive diagrams to visualize current and desired states — Initialize and render two React c |
| 🟢 | `96a63d512` | 2026-03-22 | Docs | Docs / Propostas | Diagnose and fix architectural issues in the code structure — Introduce a new diagnostic section det |
| 🟡 | `fa271f357` | 2026-03-22 | Outro | (Auto-commit Replit) | Restored to '52c6faa4a38877ab66d54971e796a9c7efe989d1' — Replit-Restored-To: 52c6faa4a38877ab66d5497 |
| 🟡 | `c48a61f53` | 2026-03-22 | Auto-commit Replit | (Auto-commit Replit) | Saved your changes before starting work |
| 🟡 | `916bc3d3f` | 2026-03-22 | Outro | Skills / canonical-fix | feat(skill): add PASSO 0 Intenção Estética to design-standardize skill — Task #32 — Skill design-sta |
| 🟡 | `dc2e74ae7` | 2026-03-22 | Outro | Skills / canonical-fix | feat(skill): add PASSO 0 Intenção Estética to design-standardize skill — Task #32 — Skill design-sta |
| 🟡 | `a8d73e15b` | 2026-03-22 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `52c6faa4a` | 2026-03-22 | Outro | Scripts / Jira tooling | Add audit documentation for the login screen redesign to Jira — Update Jira card WT-1639 with detail |
| 🟢 | `c4ad7d11b` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Update login page styling and dark mode support — Adjusted border-radius for inputs and error messag |
| 🟢 | `42af42d82` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Improve the visual hierarchy and elegance of the login page — Update the login page's sequence text  |
| 🟢 | `7d683641b` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Improve the visual presentation of login page elements — Break the sequence text into two lines, pla |
| 🟢 | `fd3f36615` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Make headline text lighter and bolder for emphasis — Update the login page's main headline to use a  |
| 🟢 | `01bb2fddc` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Improve the visual scale and readability of the login page — Adjusted typography sizes and spacing i |
| 🟢 | `ae5802f2b` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Make the word "simples" bold to increase its visibility — Update the UI to make the word "simples" b |
| 🟢 | `672f8aae8` | 2026-03-22 | Frontend (UI) | scope: clouds-background | feat(clouds-background): nuvens animadas estilo wedotalent.cc — Task #31 — Reformulação completa do  |
| 🟢 | `595f8da3c` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Make the AI name bold and remove italics for better visibility — Update the `page.tsx` file to chang |
| 🟢 | `bfb9ca3b3` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Update page appearance to use specific fonts and colors — Modify the login page to apply Source Seri |
| 🟢 | `04765f750` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Update Microsoft login button to use official logo — Replace placeholder 'M' button with an inline S |
| 🟢 | `5931be794` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Add social media links and copyright to the login page footer — Import Globe and Linkedin icons, upd |
| 🟢 | `e1191ab57` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Center align footer text on the login page — Center align the footer text "A WeDoTalent é uma HRTech |
| 🟢 | `e0dd09292` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Update recruitment platform login page with new messaging — Update the recruitment platform's login  |
| 🟢 | `5a09e3c93` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Improve alignment of login page elements for better visual appeal — Adjusted the positioning of the  |
| 🟡 | `419afaaaf` | 2026-03-22 | Backend | Backend (core) | Improve Redis connection handling to prevent repeated connection attempts — Add short connection tim |
| 🟢 | `fa48b1405` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Center the login card and move the footer text to the bottom — Adjust the layout of the login page t |
| 🟢 | `c9adfd3f9` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Move login page footer text to below the main card — Removes footer text from the left panel and rep |
| 🟢 | `361d6b029` | 2026-03-22 | Frontend (UI) | (Auto-commit Replit) | Restored to 'a334b057086274a75d869d1568b72dbdfe45321e' — Replit-Restored-To: a334b057086274a75d869d1 |
| 🟢 | `fe827551c` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Reposition AI badge to the bottom of the right panel — Move the AI badge from above the headline in  |
| 🟢 | `a334b0570` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Add a badge with recruitment AI information above the headline — Add a new badge component to the lo |
| 🟢 | `6b9568369` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Center login prompts and remove footer links from the platform access card — Center the "Entrar na p |
| 🟢 | `846482f55` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Adjust logo size and position to improve alignment with text — Update logo container width to 230px  |
| 🟢 | `7bbed4417` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Update footer text to correct company name and capitalization — Corrected "WeDo Talent" to "WeDoTale |
| 🟢 | `ff83a14f5` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Adjust text alignment and size for better logo proportion — Update the "TALENT" text styling in `pag |
| 🟢 | `726c430ea` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Increase size and spacing of Talent logo text — Adjusted the font size and letter spacing for the 't |
| 🟢 | `62d773b34` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Align "TALENT" text to the right below logo — Update login page to right-align the "TALENT" text ben |
| 🟢 | `1253e103a` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Add "TALENT" text below the company logo on the login page — Update the login page component to incl |
| 🟢 | `0a8513b6d` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Align logo and adjust its size on the login page — Update login page layout in `page.tsx` to align t |
| 🟢 | `5e86c18e7` | 2026-03-22 | Frontend (UI) | LIA Float UI (FE) | Hide LIA chat elements from login and password reset pages — Conditionally render LiaChatButton, Lia |
| 🟢 | `907ff29fb` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Restructure login process into two distinct steps for improved user experience — Refactor login page |
| 🟢 | `51db76eca` | 2026-03-22 | Empty/merge | (Auto-commit Replit) | Restored to 'cf3d38140a53a719ea4cef0544023a8a6fc5d2ca' — Replit-Restored-To: cf3d38140a53a719ea4cef0 |
| 🟢 | `cf3d38140` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Make the recruitment future description text color cyan — Update the login page heading to make the  |
| 🟢 | `a236995a7` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Add animated cloud background and floating card login form — Introduce CloudsBackground component wi |
| 🟢 | `7e16b5d99` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Remove recruitment technology details from login screen — Remove descriptive text and bullet points  |
| 🟢 | `be887fa40` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Remove AI assistant card and screen dividing line — Removed the "Conheça a LIA" card and the dividin |
| 🟢 | `cc89ea23a` | 2026-03-22 | Frontend (UI) | Login UI (FE) | Add a calming cloud background and transparent logo to the login page — Update the login page to inc |
| 🟡 | `b41dc0739` | 2026-03-21 | Backend | Scripts / CLI | Add a new screen configuration for the left-hand side menu — Update the design audit generator scrip |
| 🟡 | `4c32c329a` | 2026-03-21 | Backend | Scripts / CLI | Enhance design audits by automatically mapping mentioned elements to their code — Integrate element- |
| 🟡 | `a360dec34` | 2026-03-21 | Backend | Scripts / CLI | Add image analysis to bug and design audit generation — Integrates Vision API for screenshot analysi |
| 🟡 | `05dbd0e8f` | 2026-03-21 | Backend | Compliance / LGPD / EU AI Act | Task #30: Compliance gate + temperature 0.1 + vue_code_full — ## Itens resolvidos dos APPROVED_WITH_ |
| 🟡 | `7e5e78df3` | 2026-03-21 | Backend | Compliance / LGPD / EU AI Act | Task #30: Implementar compliance gate + temperature 0.1 em ambos os scripts — ## Fixes baseados em A |
| 🟡 | `059ef71e8` | 2026-03-21 | Backend | Task #30 | Task #30: Fix 3 issues apontados pelo code review — ## Fixes aplicados |
| 🟡 | `44e1c040c` | 2026-03-21 | Backend | Task #30 | Task #30: Scripts auditoria determinísticos + re-auditoria WT-1633/34/35/36 — ## O que foi feito |
| 🟡 | `327692691` | 2026-03-21 | Backend | Task #30 | Task #30: Scripts auditoria determinísticos + re-auditoria WT-1633/34/35/36 — ## O que foi feito |
| 🟡 | `c64c83ff0` | 2026-03-21 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `0a79c22c6` | 2026-03-21 | Backend | Scripts / CLI | Add option to post audits as comments directly — Introduces the `--as-comment` flag to `cmd_post` in |
| 🟡 | `cd34e8057` | 2026-03-21 | Backend | Scripts / CLI | Improve session fetching to support cookies and public links — Update `_betterbugs_fetch_session` fu |
| 🟡 | `acf7fb7fb` | 2026-03-21 | Backend | Scripts / CLI | Add BetterBugs API integration for enhanced bug reporting — Integrates BetterBugs REST API into bug_ |
| 🟡 | `047ce6b6d` | 2026-03-21 | Backend | Scripts / CLI | Extract screenshots and links from BetterBugs Jira cards — Adds functionality to extract embedded sc |
| 🟡 | `090a373db` | 2026-03-21 | Backend | Scripts / CLI | Integrate real Vue code snippets into audit reports and add fallback for Jira posts — Add GitHub API |
| 🟡 | `b0dc74f02` | 2026-03-21 | Backend | Scripts / CLI | Add script to generate design audit templates for UI screens — Adds a Python script that fetches Jir |
| 🟡 | `287367535` | 2026-03-21 | Backend | Scripts / CLI | Enhance bug report template with technical specification details — Update bug specification template |
| 🟡 | `7fc035b64` | 2026-03-21 | Backend | Scripts / CLI | Improve tag extraction and error handling for Jira interactions — Enhance tag extraction regex to su |
| 🟡 | `2068fbe8b` | 2026-03-21 | Backend | scope: bug-spec-generator | feat(bug-spec-generator): OAuth2 via conector Replit + suporte multi-ferramenta — Auth: |
| 🟡 | `b9c12e799` | 2026-03-21 | Backend | scope: bug-spec-generator | feat(bug-spec-generator): suporte multi-ferramenta (Jam · Userback · BetterBugs) — - Renomeia _parse |
| 🟡 | `3d7e5dd7a` | 2026-03-21 | Backend | scope: bug-spec-generator | feat(bug-spec-generator): suporte multi-ferramenta (Jam · Userback · BetterBugs) — - Renomeia _parse |
| 🟡 | `261fcf456` | 2026-03-21 | Backend | Scripts / CLI | Add script to generate bug specifications from Jira cards — Add a new Python script for fetching Jir |
| 🔴 | `daf8552c1` | 2026-03-20 | Cross IA↔Front | Compliance / LGPD / EU AI Act | feat(fairness): Sprint FAR — Fairness Audit Remediation completo — FAR-1: 4 novas categorias bloquea |
| 🟢 | `309097ecd` | 2026-03-20 | Docs | Docs / Propostas | Add expanded coverage panel detailing v5 service and LIA implementation — Adds an expanded panel det |
| 🟢 | `d6acd9b68` | 2026-03-20 | Docs | scope: docs | feat(docs): add v5 domains/agents map to executive summary + guardrails_seed evidence — Added 'Mapa  |
| 🟡 | `75631f4fb` | 2026-03-20 | Auto-commit Replit | (Auto-commit Replit) | Git commit prior to merge |
| 🟢 | `c6a592c20` | 2026-03-20 | Docs | scope: proposals | feat(proposals): diagnóstico arquitetural profundo LIA vs v5 (v2) — Reescreve proposals/diagnostico_ |
| 🟢 | `97d5e7212` | 2026-03-20 | Docs | scope: proposals | feat(proposals): cria diagnóstico arquitetural profundo LIA vs v5 — Cria proposals/diagnostico_arqui |
| 🟡 | `c58e40130` | 2026-03-20 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `3f5c87305` | 2026-03-20 | Docs | §1 Teams Integration | Add bidirectional Teams bot and enhance communication capabilities — Rewrite section 9 to detail the |
| 🟢 | `3fdf5b289` | 2026-03-20 | Docs | §1 Teams Integration | Add Microsoft Teams integration for notifications and alerts — Update documentation to include a new |
| 🟢 | `50632b526` | 2026-03-19 | Docs | Docs / Propostas | Update tool scope documentation to reflect correct file paths — Correctly references `app/tools/scop |
| 🟢 | `9c8d70018` | 2026-03-19 | Docs | Task #25 | Task #25 — Mapeamento capacidades prompts LIA × v5 (v4.0 final) — DOCUMENTO: proposals/mapeamento_ca |
| 🟢 | `ebbc0fce2` | 2026-03-19 | Docs | Task #25 | Task #25 — Mapeamento capacidades prompts LIA × v5 (v3.0 final) — DOCUMENTO: proposals/mapeamento_ca |
| 🟢 | `014d3d604` | 2026-03-19 | Docs | Task #25 | Task #25 — Mapeamento capacidades prompts LIA × v5 (v2.0 corrigida) — DOCUMENTO: proposals/mapeament |
| 🟢 | `6b4f72dd5` | 2026-03-19 | Docs | Task #25 | Task #25 — Mapeamento completo de capacidades dos prompts LIA × v5 — DOCUMENTO CRIADO: proposals/map |
| 🟡 | `600d8c01f` | 2026-03-19 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `06fc40b25` | 2026-03-19 | Docs | Triagem (módulo) | Add detailed technical guide for implementing market-standard AI agents — Complete Section 5 of the  |
| 🟢 | `baf2bfa7c` | 2026-03-19 | Docs | Docs / Propostas | Add detailed technical guides for creating custom agents — Adds comprehensive technical documentatio |
| 🟢 | `7efc6fc3c` | 2026-03-19 | Docs | Docs / Propostas | Update technical document with accurate v5 system details — Revise and expand technical documentatio |
| 🟢 | `c651bc305` | 2026-03-19 | Docs | Docs / Architecture | Update prompt management to include modification timestamps — Add 'updated_at' field to YAML prompts |
| 🟢 | `abbe5f5b2` | 2026-03-19 | Docs | Task #24 | docs: relatorio_capacidades_prompts_lia.md atualizado para v4.4 — Task #24 — Documento atualizado de |
| 🟢 | `98efe1f0e` | 2026-03-19 | Empty/merge | Task #24 | docs: relatorio_capacidades_prompts_lia.md atualizado para v4.4 (Task #24) — Documento atualizado de |
| 🟢 | `51cdc8a26` | 2026-03-19 | Docs | Docs / Architecture | Update documentation to reflect latest platform capabilities and features — Update the `relatorio_ca |
| 🟡 | `47f562e3a` | 2026-03-19 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `61dff6be8` | 2026-03-19 | Infra/Config | Skills / canonical-fix | Add commands to fetch repository and environment details — Add GitHub API calls to fetch repository  |
| 🟡 | `d7dd8100c` | 2026-03-19 | Infra/Config | DevOps / Deploy (Docker/GCP) | Add Replit connectors SDK to manage GitHub integrations — Add @replit/connectors-sdk as a dependency |
| 🟡 | `7cb0f5a79` | 2026-03-19 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `2cd853d95` | 2026-03-19 | Docs | Sprint S | docs: atualiza documentos comparativos para sprints Y1-Y5 + Z1-Z7 + AUD completos — Paralelo_LIA_vs_ |
| 🟢 | `7c2ad5252` | 2026-03-19 | Docs | Sprint Z7 | docs: atualiza documentos comparativos LIA vs V5 com estado real pós-Sprint Z7 — - ANALISE_COMPARATI |
| 🟡 | `00ce86b71` | 2026-03-19 | Cross IA↔Back | Sprint Z | code review: corrige 5 problemas identificados na sprint Z — - traces.py: substitui import de _otlp_ |
| 🟡 | `39660c549` | 2026-03-19 | Cross IA↔Back | Privacy / PII (W7) | Z6-01 + Z6-02 + Z6-03 + Z7-01: observabilidade, PII NER e comportamento de recrutador — Z6-01 — Cons |
| 🟡 | `0f71a4bc8` | 2026-03-19 | Cross IA↔Back | Policy / Job Creation | Z5-03 + Z5-02: threshold semântico configurável e consolidação PolicySetupAgent — Z5-03 — Threshold  |
| 🟡 | `72b916571` | 2026-03-19 | Backend | §15 WSI | F2-04: Dead Letter Queue para tasks Celery com falha definitiva — - DLQService: push_failure(), list |
| 🟡 | `e492b8796` | 2026-03-19 | Backend | Compliance / LGPD / EU AI Act | Z2-01 + Z3-02: LearningSnapshotService e updated_at nos prompts YAML — Z2-01 — LearningSnapshotServi |
| 🔴 | `11d68f839` | 2026-03-19 | Cross IA↔Front | Tests (BE unit/integration) | Introduce specialized sourcing agents and improve model configurations — Add new sub-agents for sour |
| 🟡 | `8870cab97` | 2026-03-19 | Cross IA↔Back | Sourcing (BE) | Add specialized agents to improve candidate sourcing and management workflows — Introduce new sub-ag |
| 🟢 | `311b643fd` | 2026-03-19 | Docs | Compliance / LGPD / EU AI Act | docs: atualiza análise comparativa LIA vs V5 com plano de execução Z1–Z4 — Adiciona seções 20.1–20.8 |
| 🟡 | `ab285a555` | 2026-03-19 | Cross IA↔Back | Compliance / LGPD / EU AI Act | F1-02 + F1-03: FairnessGuard no learning loop e SLOs formais no circuit breaker — F1-02 — FairnessGu |
| 🟡 | `3dceca5cc` | 2026-03-19 | Cross IA↔Back | Kanban (vagas) | Sprint Z1: Decomposição KanbanReActAgent e PipelineTransitionAgent em subagentes especializados — Z1 |
| 🟢 | `892d691f4` | 2026-03-19 | Docs | Performance | Add optimization plan to improve platform performance and reliability — Append a detailed 4-phase op |
| 🟢 | `dd6e179f1` | 2026-03-19 | Docs | Docs / Propostas | Add market analysis and recommendations to the existing document — Integrate market analysis, pros/c |
| 🟡 | `83f7e9415` | 2026-03-19 | Backend | Backend (deps) | Update dependency version for improved stability and compatibility — Update the langsmith dependency |
| 🟢 | `818393257` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟢 | `0ee26f3c9` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟢 | `ca36d9bf4` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟢 | `5745e687a` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟢 | `321a35fcb` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟢 | `6f7087ead` | 2026-03-18 | Empty/merge | Compliance / LGPD / EU AI Act | Task #22: Corrigir análise comparativa LIA vs v5 — fairness e fact_checker — OBJETIVO: Atualizar att |
| 🟡 | `d9ebbc562` | 2026-03-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `f57e8e836` | 2026-03-18 | Empty/merge | Task #21 | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (v4 final) — Arquivo: attached_asse |
| 🟢 | `cda47f452` | 2026-03-18 | Empty/merge | Task #21 | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (v3 final) — Arquivo: attached_asse |
| 🟡 | `321b7a534` | 2026-03-18 | Outro | Task #21 | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (revisado) — Arquivo: attached_asse |
| 🟡 | `0bd54fa6b` | 2026-03-18 | Outro | Task #21 | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 — Criado: attached_assets/Analise_C |
| 🟡 | `19ae49aa0` | 2026-03-18 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟡 | `135abcb4d` | 2026-03-18 | Outro | Acessibilidade (a11y) | Improve automated accessibility checks for improved user experience — Update the automated accessibi |
| 🟢 | `2afc0743f` | 2026-03-16 | Empty/merge | Task #19 | Task #19: Major revision of Catalogo Produtos/Servicos/CNAEs — WeDOTalent — Deep codebase analysis + |
| 🟢 | `c630b2849` | 2026-03-16 | Empty/merge | Task #19 | Task #19: Major revision of Catalogo Produtos/Servicos/CNAEs — WeDOTalent — Deep codebase analysis r |
| 🟢 | `d9c4e07bb` | 2026-03-16 | Empty/merge | Task #19 | Task #19: Catálogo de Produtos, Serviços, Especificações Técnicas e CNAEs — WeDOTalent — Created com |
| 🟢 | `625cc29f8` | 2026-03-16 | Empty/merge | Task #19 | Task #19: Catálogo de Produtos, Serviços, Especificações Técnicas e CNAEs — WeDOTalent — Created com |
| 🟡 | `62e98db51` | 2026-03-16 | Auto-commit Replit | (Auto-commit Replit) | Transitioned from Plan to Build mode |
| 🟢 | `5fc57171c` | 2026-03-16 | Docs | Docs / Architecture | docs: update replit.md with ReAct JSON strip documentation |
| 🟡 | `e948ba22d` | 2026-03-16 | Backend | Wizard (geral) | fix: apply _strip_react_json to HITL resume paths + handle empty response edge case — - Strip ReAct  |
| 🟡 | `a260fa9fe` | 2026-03-16 | Backend | §6 Chat Unificado / Funil | fix: strip raw ReAct JSON from floating chat responses (WS + HTTP) — - Add _strip_react_json() to ag |
| 🟡 | `e31c370de` | 2026-03-16 | Backend | FastAPI v1 endpoints | Fix: expanded prompt chat on jobs page - fix 403 auth and provider name — Two root causes: |
| 🟢 | `279c586dc` | 2026-03-16 | Frontend (UI) | Frontend (componentes diversos) | Fix: LIA chat on talent funnel handles greetings conversationally instead of triggering search |
| 🟡 | `fda85e036` | 2026-03-16 | Backend | §14 BYOK + LLM Factory | Fix chat response formatting and Anthropic API integration — Refactor agent logic to use a new metho |
| 🟡 | `a7e0d4dd1` | 2026-03-15 | Auto-commit Replit | (Auto-commit Replit) | Saved progress at the end of the loop |
| 🟢 | `6d834bad1` | 2026-03-15 | Frontend (UI) | Frontend (componentes diversos) | Remove função handleOpenRubricAnalysis órfã de candidates-page.tsx — Função declarada na linha 6381  |
| 🟢 | `dd04a5590` | 2026-03-15 | Docs | Docs (geral) | docs: v4.3/v6.2 — 4 gaps críticos corrigidos para consumo por agentes IA — relatorio_capacidades_pro |
| 🟢 | `fac7fab61` | 2026-03-15 | Docs | Docs (geral) | docs: Guia de Diagnóstico para Agentes IA adicionado nos dois documentos — RELATORIO_AUDITORIA_LIA.m |
| 🟢 | `19dcc0008` | 2026-03-15 | Docs | §15 WSI | docs: relatorio_capacidades_prompts_lia.md v4.3 — Guia de Entrada para Agentes IA — Adicionado "GUIA |
| 🟢 | `079a2012e` | 2026-03-15 | Docs | Compliance / LGPD / EU AI Act | docs: RELATORIO_AUDITORIA_LIA.md v6.1 — correções de consistência pós-Y1–Y5 — 11 pontos corrigidos a |
| 🟢 | `0d16fb162` | 2026-03-15 | Docs | Docs / Architecture | docs: relatorio_capacidades_prompts_lia.md v4.2 — atualização completa seções 1-34 — Atualização pro |
| 🔴 | `620ef0b05` | 2026-03-15 | Cross IA↔Front | §8 Glossário / Production-Ready | Sprints Y1–Y5 completos + Diagnóstico v6: plataforma IA production-ready — ## Sprints Y1 (D1–D10) —  |

</details>

---

## 7. Apêndice D — Features menores (1-2 commits, sem camada IA)

_303 features pequenas reunidas aqui pra reduzir ruído na seção 2 do MAP principal._

<details>
<summary>Expandir lista</summary>

| Feature | Commits | Camadas |
|---|---|---|
| Analytics (BE) | `e50766222`, `a2b2d4f26` | Backend |
| Backend (core) | `313d0141a`, `419afaaaf` | Backend |
| Backend (deps) | `274dd0926`, `83f7e9415` | Docs, Backend |
| Backend (libs) | `cd4ee9719`, `37e623db6` | Backend |
| Compliance Dashboard (FE) | `b5e74a10e`, `db4fedc94` | Cross Back↔Front, Frontend (UI) |
| Docs / Handoff | `ccd88701b`, `287e5a19d` | Docs |
| Expandable AI Prompt (FE) | `77a7627f6`, `191e7244f` | Frontend (UI) |
| Fase 6 | `7f9abe450`, `ac5ce8d09` | Empty/merge |
| Indicadores (FE) | `bde2a3327`, `359a71d9f` | Frontend (UI) |
| Onboarding (FE) | `8469cd2bf`, `2ccf70373` | Frontend (UI) |
| Recruiter Assistant (BE) | `3435fc69f`, `90232b225` | Backend |
| Screening Config (FE) | `0a152f1d9`, `be5f4b3f1` | Frontend (UI) |
| Sprint 11 | `6e40ff114`, `b426149af` | Backend |
| Sprint 12 | `e4faeb8c9`, `93802c751` | Cross Back↔Front |
| Sprint 4.3 | `9a99a3713`, `d455f689e` | Frontend (UI) |
| Sprint 4.9 | `006f69ec7`, `217ebd49a` | Frontend (UI) |
| Sprint S | `da4901994`, `2cd853d95` | Docs, Frontend (UI) |
| Task #100 | `3e1f40d9a`, `9b1061bb2` | Frontend (UI) |
| Task #101 | `1c2d5ab04`, `bef96a22a` | Frontend (UI) |
| Task #102 | `a6514672b`, `673c6e79c` | Cross Back↔Front, Frontend (UI) |
| Task #103 | `b59e20097`, `0a332b1ea` | Frontend (UI) |
| Task #132 | `f370c2259`, `16f8ab929` | Testes |
| Task #134 | `30d2dc03e`, `8f4536dfb` | Backend |
| Task #141 | `0bfffe539`, `e7daeb78c` | Cross Back↔Front, Frontend (UI) |
| Task #144 | `2a70c3220`, `3b95e5e7d` | Cross Back↔Front, Backend |
| Task #198 | `7c9214a39`, `8507ca026` | Backend, Empty/merge |
| Task #24 | `abbe5f5b2`, `98efe1f0e` | Docs, Empty/merge |
| Task #243 | `769f54ee1`, `14a215850` | Cross Back↔Front, Frontend (UI) |
| Task #245 | `a313275fa`, `c2da99b13` | Frontend (api/util), Frontend (UI) |
| Task #38 | `14b5ae056`, `8729d4587` | Cross Back↔Front |
| Task #49 | `c803f56c4`, `255ea29c1` | Docs, Frontend (UI) |
| Task #51 | `e467eab71`, `17e049be6` | Frontend (UI) |
| Task #53 | `4af1a779f`, `70a4c5733` | Docs, Cross Back↔Front |
| Task #56 | `09bca1312`, `9c7a4bf02` | Frontend (UI) |
| Task #58 | `0b6a5ea4e`, `a11879592` | Frontend (UI) |
| Task #61 | `c73957bf8`, `e7a3fe16b` | Docs, Backend |
| Task #66 | `3ccde04fd`, `c434d688a` | Frontend (UI) |
| Task #68 | `9c7113453`, `fb9b531a9` | Docs, Backend |
| Task #91 | `19cf22c56`, `6bd155d9d` | Frontend (UI) |
| Wizard/Onda 1 | `d8c3f516e`, `1a60080be` | Frontend (UI) |
| Wizard/Onda 2 | `802104b89`, `b4ef2443c` | Docs, Cross Back↔Front |
| Wizard/Onda 22 | `64b1cdcaf`, `e74aff11b` | Docs, Backend |
| Wizard/Onda 25 | `832bedd3f`, `5727f7432` | Docs, Backend |
| Wizard/Onda 36 | `2e07b3ef5`, `78ced6508` | Docs, Backend |
| scope: admin | `d53d0af64`, `b90e8e2cb` | Backend |
| scope: agent-studio | `6df8f6874`, `6af3cf400` | Cross Back↔Front, Backend |
| scope: audits | `301829ca2`, `6ebff401e` | Docs |
| scope: chat-lia | `9203b3ce7`, `900d7c175` | Frontend (UI) |
| scope: eval | `cd89fcf8f`, `4dbd62251` | Frontend (api/util), Backend |
| scope: handoff | `40dd2cf6c`, `fc76b0a88` | Docs |
| scope: jobs | `d06e4fe88`, `98615e123` | Cross Back↔Front, Testes |
| scope: lia-llm-1 | `6402fbc77`, `a2ae935c8` | Backend |
| scope: obs | `ac536e90e`, `846c7467e` | Backend |
| scope: proposals | `c6a592c20`, `97d5e7212` | Docs |
| scope: quality | `9ef73964f`, `843ca5f04` | Frontend (UI) |
| scope: sidebar | `7a2fb1be6`, `bcf87b3df` | Frontend (api/util), Frontend (UI) |
| scope: specs | `26fc30308`, `6128cfff4` | Docs |
| scope: vue | `845fe57c8`, `bbe308def` | Frontend (api/util) |
| scope: weekly-digest | `e631dfcda`, `86805f232` | Cross Back↔Front |
| §12 DEVELOPER_HANDOFF — PARTE I | `2ee8ad9af`, `df34f5707` | Docs |
| §3 LIA Maturity | `540315b5a`, `ec89039c6` | Docs |
| §3 LIA Maturity — FIX 35 | `b26448e18`, `8bfad78f1` | Testes, Backend |
| §4 Rail Features — PR-I | `7d8222ea2`, `60a09637f` | Backend |
| ADR-002 | `6eeed3e10` | Docs |
| ADR-012 | `c0f197288` | Backend |
| ADR-016 | `b9427ec52` | Docs |
| ADR-018 | `8cd82e847` | Docs |
| Automation domain (BE) | `f697a4efe` | Backend |
| Backend (refactor Phase 2+) | `70863bb78` | Frontend (api/util) |
| Fase 2C_DOMAIN_VERIFICATION_REPORT.MD | `974282fe1` | Backend |
| Fase 2D | `117c551d3` | Frontend (UI) |
| Fase 4 | `cc4bfa44b` | Docs |
| Fase 5A | `a4103ebb5` | Frontend (UI) |
| Fase 5B | `e0bcd639f` | Frontend (UI) |
| Fase 5C | `1b05d97cc` | Frontend (UI) |
| Fase 5D | `8518c0ac9` | Frontend (UI) |
| JD Import / Job Description | `bfe3efade` | Cross Back↔Front |
| Performance / Cold-start | `558b94fc5` | Outro |
| Rails (ats-api-copia) | `5e3b4aeea` | Rails (ats-api) |
| Schemas / Pydantic (BE) | `0980b0677` | Backend |
| Sprint 4.2 | `035f5bd6a` | Frontend (UI) |
| Sprint 4.6-4.8 | `30b18fff7` | Frontend (UI) |
| Sprint 4.8 | `500a09555` | Frontend (UI) |
| Sprint COMPLETE | `60b9738c3` | Docs |
| Sprint Z7 | `7c2ad5252` | Docs |
| Stores (FE Zustand) | `a6630744b` | Frontend (UI) |
| Task #104 | `004ee812d` | Frontend (UI) |
| Task #105 | `92802179d` | Testes |
| Task #106 | `13f800baa` | Frontend (UI) |
| Task #118 | `aaf336f31` | Outro |
| Task #119 | `9e7423ab9` | Frontend (UI) |
| Task #120 | `0d3f80691` | Frontend (UI) |
| Task #126 | `305c528ee` | Backend |
| Task #142 | `b5ab76b98` | Frontend (UI) |
| Task #152 | `007ce8bfe` | Frontend (UI) |
| Task #154 | `71a5edfec` | Backend |
| Task #156 | `85d0aaf9d` | Cross Back↔Front |
| Task #159 | `c974c46f3` | Frontend (UI) |
| Task #163 | `3402210e1` | Backend |
| Task #164 | `e83bff7a7` | Testes |
| Task #17 | `797b96812` | Frontend (UI) |
| Task #18 | `6196cbdc7` | Frontend (UI) |
| Task #183 | `1747ddae9` | Frontend (UI) |
| Task #184 | `6ae1f9274` | Frontend (UI) |
| Task #185 | `1d7e14894` | Frontend (UI) |
| Task #188 | `d8b132664` | Frontend (UI) |
| Task #189 | `0ffd3e681` | Cross Back↔Front |
| Task #196 | `37b2d1772` | Backend |
| Task #197 | `d4b36d996` | Frontend (UI) |
| Task #212 | `661d3bf44` | Frontend (UI) |
| Task #214 | `ec49215c3` | Frontend (UI) |
| Task #217 | `cf20d3945` | Backend |
| Task #218 | `14e35497c` | Backend |
| Task #220 | `0cc8c6267` | Outro |
| Task #221 | `4972c23ee` | Backend |
| Task #222 | `83092c552` | Backend |
| Task #224 | `65455a5b2` | Backend |
| Task #226 | `4ee9af91e` | Backend |
| Task #23 | `0785ad6c4` | Frontend (UI) |
| Task #230 | `3865bec9e` | Backend |
| Task #231 | `77faa626d` | Backend |
| Task #233 | `3615daa37` | Backend |
| Task #235 | `d9d463ec0` | Frontend (UI) |
| Task #237 | `0cd0da1e1` | Frontend (UI) |
| Task #239 | `95bb46f6c` | Backend |
| Task #240 | `da046d20a` | Docs |
| Task #241 | `7f4fe24f7` | Cross Back↔Front |
| Task #248 | `3315abfb4` | Testes |
| Task #250 | `726dc976c` | Cross Back↔Front |
| Task #251 | `fdfdf3890` | Frontend (UI) |
| Task #252 | `5cdbc251d` | Frontend (api/util) |
| Task #254 | `f0a40a4c2` | Frontend (UI) |
| Task #255 | `74af0cc39` | Testes |
| Task #260 | `22ca72791` | Testes |
| Task #261 | `f6592977a` | Frontend (api/util) |
| Task #264 | `1c0baed94` | Frontend (api/util) |
| Task #281 | `88abdcf26` | Frontend (api/util) |
| Task #282 | `7d9c3363d` | Backend |
| Task #283 | `4b6d71f01` | Backend |
| Task #288 | `5e2c78aed` | Frontend (UI) |
| Task #291 | `73d06f91c` | Frontend (api/util) |
| Task #292 | `6be1e4e01` | Testes |
| Task #296 | `7bd62fef4` | Backend |
| Task #298 | `51800a04e` | Testes |
| Task #3 | `015f769fe` | Frontend (UI) |
| Task #300 | `9bc805b29` | Frontend (UI) |
| Task #306 | `97205ecc1` | Backend |
| Task #31 | `1465a5be6` | Frontend (UI) |
| Task #313 | `1f93fb414` | Backend |
| Task #319 | `211da7846` | Cross Back↔Front |
| Task #323 | `4448aefe3` | Backend |
| Task #324 | `25ebf3c0b` | Backend |
| Task #326 | `a9ae93b9a` | Backend |
| Task #327 | `64ee7e57c` | Testes |
| Task #328 | `691f8e59f` | Backend |
| Task #338 | `1cc1edce0` | Backend |
| Task #340 | `117f4d1ec` | Backend |
| Task #344 | `b1c76a3c4` | Testes |
| Task #347 | `db4aeeebc` | Docs |
| Task #348 | `f4e281faf` | Backend |
| Task #350 | `56dc31d9b` | Backend |
| Task #356 | `cc34d1757` | Frontend (UI) |
| Task #358 | `4f4772484` | Backend |
| Task #375 | `8d295abac` | Frontend (UI) |
| Task #379 | `26a55db93` | Testes |
| Task #383 | `e1bd75ba8` | Frontend (api/util) |
| Task #384 | `f9ec30e17` | Frontend (api/util) |
| Task #391 | `4cc6bab30` | Testes |
| Task #394 | `2026c1029` | Cross Back↔Front |
| Task #395 | `930aebd87` | Backend |
| Task #396 | `31e3f3bdd` | Backend |
| Task #4 | `a2c18180d` | Frontend (UI) |
| Task #400 | `b96975212` | Cross Back↔Front |
| Task #402 | `af086a2d9` | Cross Back↔Front |
| Task #403 | `1dc1109ba` | Cross Back↔Front |
| Task #404 | `91737f9c7` | Testes |
| Task #419 | `56b0dcd4e` | Backend |
| Task #42 | `4fe295025` | Frontend (UI) |
| Task #424 | `5e9a354bc` | Backend |
| Task #429 | `111c3403e` | Cross Back↔Front |
| Task #434 | `5f422dfee` | Backend |
| Task #435 | `911e6a651` | Cross Back↔Front |
| Task #436 | `bb15510bb` | Cross Back↔Front |
| Task #439 | `cdba0850d` | Testes |
| Task #442 | `3161accc5` | Backend |
| Task #446 | `f70b1691c` | Backend |
| Task #452 | `31bf8321c` | Frontend (UI) |
| Task #455 | `ae1c3bb59` | Backend |
| Task #457 | `e81367e4b` | Frontend (UI) |
| Task #458 | `ef2f1a525` | Backend |
| Task #459 | `5221b2d65` | Backend |
| Task #464 | `f552d10bd` | Testes |
| Task #466 | `6652b768c` | Frontend (UI) |
| Task #467 | `86a6f92f2` | Frontend (UI) |
| Task #470 | `13744d288` | Backend |
| Task #472 | `4053f9331` | Backend |
| Task #478 | `45f4f1542` | Backend |
| Task #479 | `fe2579ae2` | Backend |
| Task #480 | `f154578d4` | Frontend (UI) |
| Task #484 | `2a9b965cf` | Backend |
| Task #485 | `64828fec6` | Frontend (UI) |
| Task #486 | `549c380c2` | Backend |
| Task #52 | `0e11445af` | Frontend (UI) |
| Task #54 | `1ff1deee2` | Frontend (UI) |
| Task #60 | `8e381fa9f` | Docs |
| Task #62 | `de47d2bbc` | Docs |
| Task #63 | `c8bd0a972` | Docs |
| Task #64 | `0d9ac7435` | Frontend (UI) |
| Task #67 | `b08e2939b` | Docs |
| Task #73 | `9e74c8350` | Frontend (UI) |
| Task #74 | `f88ee76f1` | Frontend (UI) |
| Task #76 | `bfaa68bfb` | Frontend (UI) |
| Task #79 | `6091bbf66` | Docs |
| Task #8 | `f15556817` | Backend |
| Task #87 | `ec389f991` | Cross Back↔Front |
| Task #92 | `cda55c611` | Docs |
| Task #935 | `be2ee3148` | Backend |
| Task #936 | `bec3b2ad3` | Backend |
| Task #95 | `c0d3ea46c` | Frontend (UI) |
| Task #97 | `d5da8ed30` | Frontend (UI) |
| Task #99 | `0d2aba6ff` | Frontend (UI) |
| WSI components (FE) | `dc8a00f97` | Frontend (UI) |
| Wizard/Onda 2.2 | `dd77d4439` | Backend |
| Wizard/Onda 2.3 | `6cc6b6a85` | Backend |
| Wizard/Onda 22-28 | `dabb5c4d4` | Docs |
| Wizard/Onda 26-27 | `05ccd6fcc` | Frontend (UI) |
| Wizard/Onda 28 | `07d1eb0af` | Frontend (UI) |
| Wizard/Onda 3 | `d1b7544d4` | Frontend (UI) |
| Wizard/Onda 3.1 | `d2e5bb376` | Backend |
| Wizard/Onda 3.4 | `d6efe4ed1` | Backend |
| Wizard/Onda 3.5 | `ddf7c9769` | Backend |
| Wizard/Onda 30 | `7088a0c0e` | Docs |
| Wizard/Onda 31 | `b2b268caf` | Docs |
| Wizard/Onda 31.2 | `4a28a1f6a` | Backend |
| Wizard/Onda 33 | `fa2af2991` | Frontend (UI) |
| Wizard/Onda 4 | `3c940d5e8` | Cross Back↔Front |
| Wizard/Onda 4.1 | `e1bd6997b` | Backend |
| Wizard/Onda 4.13 | `4dad75d18` | Backend |
| Wizard/Onda 4.2 | `7bb4dd716` | Backend |
| Wizard/Onda 4.3-4.9 | `5c4ff9fb0` | Docs |
| Wizard/Onda 4.9 | `5e537bc0c` | Testes |
| scope: #128 | `b68483941` | Cross Back↔Front |
| scope: #81 | `b6cfd672d` | Cross Back↔Front |
| scope: admin-tenant | `04b5f8bb0` | Backend |
| scope: adr | `b95fc0603` | Docs |
| scope: architecture | `afba1da63` | Backend |
| scope: auth+fe | `2f1bd439c` | Cross Back↔Front |
| scope: billing | `51dfd6369` | Backend |
| scope: build | `6555511c7` | Frontend (api/util) |
| scope: calibration | `55457ac95` | Frontend (UI) |
| scope: candidate-preview | `4f06897d7` | Frontend (UI) |
| scope: clouds-background | `672f8aae8` | Frontend (UI) |
| scope: crew-delegation | `41fbd7a7d` | Backend |
| scope: cv-screening | `f539d14c1` | Backend |
| scope: deploy-guide | `400b336d3` | Docs |
| scope: design-standardize | `de0ed094c` | Docs |
| scope: design-system | `8d7840bc3` | Frontend (UI) |
| scope: diagrams | `c50ff50df` | Outro |
| scope: digest | `0d1f24af7` | Frontend (UI) |
| scope: env | `3e260646e` | Frontend (api/util) |
| scope: health | `80c09ef0c` | Backend |
| scope: intent | `0b1916075` | Backend |
| scope: job-detail-client | `0c1e73c08` | Testes |
| scope: keyboard | `3c7e2d1ba` | Frontend (UI) |
| scope: lia-agent-system | `9da48593e` | Testes |
| scope: lia-d02,fase3a | `bba2c54cd` | Backend |
| scope: lia-maturity | `014ea00a8` | Docs |
| scope: lia-sec-01 | `3a67504c4` | Backend |
| scope: lia-sec-03,b-2 | `bdc3f9e25` | Backend |
| scope: minha-empresa | `a2913e268` | Cross Back↔Front |
| scope: multi-tenant | `cee507b2f` | Testes |
| scope: onboarding-lia | `bbe4db71b` | Cross Back↔Front |
| scope: pe-10 | `7405ad757` | Testes |
| scope: pe-4 | `a52e4b1be` | Backend |
| scope: phase2-recruitment | `17a3ea932` | Backend |
| scope: phase3+fixes | `05fee6069` | Backend |
| scope: phase4 | `b998c624a` | Docs |
| scope: pipeline-overview | `4d97d5a1e` | Frontend (UI) |
| scope: rails-integration | `2a60c61a3` | Backend |
| scope: report | `537d24ecf` | Docs |
| scope: sourcing | `b43ce6c34` | Backend |
| scope: spec | `1699d7fc9` | Docs |
| scope: sse | `70d0ebc15` | Backend |
| scope: tenant-scope | `731a61e8a` | Testes |
| scope: test | `3b19208f2` | Testes |
| scope: voip | `dcda58d1e` | Cross Back↔Front |
| §1 Teams — Wave 6 | `71a4cfcca` | Docs |
| §12 DEVELOPER_HANDOFF — PARTE F | `3722e7b38` | Docs |
| §12 DEVELOPER_HANDOFF — PARTE G | `04ff86a65` | Docs |
| §12 DEVELOPER_HANDOFF — PARTE H | `6aa9492fb` | Docs |
| §12 DEVELOPER_HANDOFF — PARTE K | `49464a0c6` | Docs |
| §3 LIA Maturity — FIX 17 | `4ca0b8c58` | Backend |
| §3 LIA Maturity — FIX 2 | `4d55b7c40` | Backend |
| §3 LIA Maturity — FIX 32 | `be06dd0a1` | Backend |
| §3 LIA Maturity — FIX 34 | `ab3216ccd` | Testes |
| §3 LIA Maturity — FIX 9 | `896f4ae34` | Backend |
| §4 Rail Features — PR-B | `e54557d97` | Frontend (UI) |
| §4 Rail Features — PR-C | `5fa71f9cb` | Frontend (UI) |
| §4 Rail Features — PR-E | `9f22fc56b` | Testes |
| §4 Rail Features — PR-H | `f1236a268` | Frontend (UI) |
| §4 Rail Features — PR-K | `f60cf1311` | Frontend (UI) |
| §4 Rail Features — PR-N | `710adfcef` | Frontend (UI) |
| §4 Rail Features — PR-Q4 | `24f6c8f47` | Backend |

</details>

---

## 8. Apêndice E — Atualização Incremental (29/abr 12:47 → 30/abr 18:32)

> **51 commits** adicionados após geração v3 do CHERRY_PICK_MAP.md (29/abr 12:47).
> Detalhamento por feature em [CHERRY_PICK_MAP.md §4](CHERRY_PICK_MAP.md#4-atualização-incremental--29abr-1247--30abr2026-51-commits).

### 8.1 Lista cronológica completa (mais novo → mais antigo)

| SHA | Data UTC | Camada | Feature | Mensagem (truncated) |
|---|---|---|---|---|
| `0cf1caa5b` | 2026-04-30 18:32 | Testes | §4 Rail Features — PR-E expansion | feat(tests): LLM-as-judge for 22 Rail A cards golden dataset (PR-E) |
| `661028958` | 2026-04-30 17:09 | Testes | §4 Rail Features — E2E | test(e2e): Rail A routing + Wizard PRV/Benefits exhaustive E2E (RA 9 + WB 10) |
| `f60c300d4` | 2026-04-30 16:49 | Testes | Benefits/PRV — E2E | test(e2e): extend job-compensation spec with LIA chat (JC-011–016) |
| `ccd90ff84` | 2026-04-30 16:38 | IA | §4 Rail Features — PR-RAG | feat(sourcing-actions): replace SQL ILIKE with RAGPipelineService hybrid |
| `9e0eee100` | 2026-04-30 16:33 | Cross IA↔Back | §4 Rail Features — PR-BRIEF | feat(rails-adapter): daily_summary replaces deprecated briefing_service |
| `7877c1ab4` | 2026-04-30 ~16:30 | Auto-commit Replit | (auto) | Transitioned from Plan to Build mode |
| `d330b2822` | 2026-04-30 16:26 | Backend | §4 Rail Features — PR-J/J2 | feat(capability-map): add quick_question + suggest_action capability entries |
| `44ee3228e` | 2026-04-30 16:24 | Frontend (UI) | §4 Rail Features — PR-L | fix(design-tokens): remove redundant hex fallback from --chat-cyan |
| `0d3f6ba76` | 2026-04-30 ~16:00 | Docs | Misc | docs(harness): mark from_ws/from_rabbitmq as NOT-YET-WIRED + rabbitmq stub |
| `3bbdfede6` | 2026-04-30 ~15:30 | Frontend (UI) | INT005 | fix(int005): wire useLiaChatContext + sendChatMessage in edit-job-modal |
| `3cd5bee33` | 2026-04-30 ~15:00 | Docs | Harness | fix(harness): P1-A history trim + dead code docs + AGENTS.md |
| `e6d36fd39` | 2026-04-30 14:55 | Testes | §4 Rail Features — PR-E | test(rail-a): add PR-E routing test pyramid — 29 tests, 29 passing |
| `eacb2726f` | 2026-04-30 ~14:50 | Auto-commit Replit | (auto) | Git commit prior to merge |
| `18b7614c7` | 2026-04-30 14:41 | Backend | §4 Rail Features — PR-CAL | fix(rail-a): add schedule_interview to capability_map (PR-CAL) |
| `bd71815fb` | 2026-04-30 14:22 | Backend | §4 Rail Features — OfferDomain | fix(rail-a): wire OfferDomain + remove triagem keyword conflict |
| `44d742f2f` | 2026-04-30 13:57 | Cross IA↔Back | Benefits/PRV | feat(wizard): integrate company Benefits + PRV (compensation_policies) into wizard |
| `423158edd` | 2026-04-30 ~13:50 | Frontend (UI) | Benefits/PRV | fix(settings): encoding Politicas de PRV + i18n documentsLabel→Remuneracao Variavel |
| `b56da03f4` | 2026-04-30 13:45 | Frontend (UI) | Benefits/PRV | Update company settings labels and titles to reflect new terminology |
| `407e76545` | 2026-04-30 13:44 | Cross Back↔Front | Benefits/PRV | Integrate detailed compensation policies into job offers and hiring workflows |
| `bad0a8385` | 2026-04-30 13:22 | Backend | §4 Rail Features — RAIL_A_EXTRA | fix(rail-a): add wizard to _RAIL_A_EXTRA_TARGETS so domain hint passes allowlist |
| `4028932dd` | 2026-04-30 12:58 | Frontend (UI) | §4 Rail Features — PR-O | fix(rail-a): PR-O telemetry + compact COMING_SOON parity + stale nav tests |
| `7f0124b89` | 2026-04-30 12:37 | Cross Back↔Front | §4 Rail Features — Kanban | fix(kanban+rail): shortlist init + PR-O telemetry + compact COMING_SOON guard |
| `66d1a0144` | 2026-04-30 12:32 | Cross Back↔Front | Benefits/PRV — Fase 3 deferred | feat(fase3-deferred): P1 multi-tenancy + 3.4 pre-select + 3.5 BenefitFormModal in job |
| `8be8f6b8a` | 2026-04-30 12:26 | IA | Benefits/PRV — Fase 4 | feat(phase4): IA layer audit + TODO markers + fairness note |
| `e79d457aa` | 2026-04-30 ~11:00 | IA | LLM resilience | fix(llm): add tenacity transient-error retry on Claude + OpenAI providers |
| `f46699cf8` | 2026-04-30 12:01 | Cross Back↔Front | Benefits/PRV — Fase 3 | feat(phase3): empresa→vaga integration — compensation_policy_id FK + PRV dropdown |
| `9920e5e39` | 2026-04-30 ~10:00 | Backend | Job Management | fix(job-management): add missing company_job_history_service + recruitment_template_service |
| `546b7a7fc` | 2026-04-30 11:44 | Backend | §4 Rail Features — CI | fix(ci): remove stale daily_briefing hardcoded check from deprecated-tools guard |
| `2e3919e4c` | 2026-04-30 11:32 | Frontend (UI) | §4 Rail Features — PR-B Trigger B | feat(kanban): PR-B Trigger B - drag to offer column opens OfferReviewModal |
| `eda6d4eaa` | 2026-04-30 ~11:30 | Backend | Chat | fix(chat): restore _build_response_from_action + handle_action_flow in chat.py |
| `717e17d8c` | 2026-04-30 ~11:00 | Frontend (UI) | Design System | fix(design-system): substituir tokens hardcoded por tokens canonicos v4.2.2 |
| `9d6cc44a0` | 2026-04-30 11:12 | Cross Back↔Front | Benefits/PRV — Fase 2 | feat(prv): Fase 2 completa — CompensationPolicy CRUD + UI 5 sub-tabs + RLS |
| `ecbcdfd41` | 2026-04-30 ~10:00 | Testes | Tests | fix(tests): update kanban_assistant_cov fixture after Task #93 migration |
| `16be81325` | 2026-04-30 10:41 | Frontend (UI) | §4 Rail Features — FE-S06 | feat(rail-a): FE-S06 — dock magnifier parity in CompactReels |
| `1ec524959` | 2026-04-30 10:39 | Cross IA↔Back | Benefits/PRV — Fase 1 hardening | feat(benefits-prv): Fase 1 hardening — fairness guard + 13 testes |
| `bfdf6ccd8` | 2026-04-30 ~09:30 | Backend | Wizard | fix: add wizard domain validator sensor to Tier 1/2 cache returns |
| `e6bf5e2ac` | 2026-04-30 10:34 | Frontend (UI) | §4 Rail Features — FE-S03 | fix(rail-a): FE-S03 — remove hex fallback from chat-workflow-reels |
| `704972b89` | 2026-04-30 10:21 | Docs | Classifiers | docs(classifiers): INT-S02 — document two-tier routing architecture |
| `a2b209c91` | 2026-04-30 10:16 | Docs | Benefits/PRV | docs(benefits-prv): Fase 2.1 — best practices ATS/HR Tech para PRV |
| `ed667d861` | 2026-04-30 10:14 | Testes | §4 Rail Features — W4-1 | test(rail-a): W4-1 routing determinism — 38 tests + LLM judge stub |
| `e048abb3d` | 2026-04-30 10:10 | Testes | Benefits/PRV — Fase 1.8 | test(benefits-prv): Fase 1.8 — sensors estruturais para CompanyBenefit (10 tests) |
| `020503492` | 2026-04-30 10:05 | Cross IA↔Back | Benefits/PRV — Fase 1.6+1.7 | feat(benefits-prv): Fase 1.6+1.7 — propaga 22 campos pela cadeia |
| `1e59e7cab` | 2026-04-30 ~09:30 | Frontend (UI) | Login | Update login redirect logic and clean up evaluation data |
| `00b0bfeb1` | 2026-04-30 ~09:30 | Cross IA↔Back | Sprint A | fix: Sprint A pending items - P1/P2 hardening post-audit |
| `403111d5d` | 2026-04-30 09:56 | Frontend (UI) | Benefits/PRV — Fase 1.4 | feat(benefits-prv): Fase 1.4 — BenefitFormModal cobre 20 campos + multi-select |
| `89388004c` | 2026-04-30 09:54 | Backend | §4 Rail Features — W1-2 | fix(briefing): W1-2 daily_briefing contract — capability_map + legacy disclaimer + tests |
| `32f212c66` | 2026-04-30 09:48 | Backend | Benefits/PRV — Fase 1.1-1.3 | feat(benefits-prv): Fase 1.1-1.3 — estender CompanyBenefit para contrato Rails (22 cols) |
| `85c57cfd8` | 2026-04-29 ~23:00 | Testes | Tools | test(css): update tool count to 4 after explain_candidate_decision (EU AI Act + LGPD Art.20) |
| `ed89147b7` | 2026-04-30 09:17 | IA | §4 Rail Features — Wave3 talent-pool | feat(talent-pool): Wave3 canonical ReAct agent (AGT-S02 fix) |
| `85d488929` | 2026-04-29 ~22:00 | Backend | Checkpointer | fix(checkpointer): PostgresSaver v3.x — ConnectionPool replaces from_conn_string |

### 8.2 Síntese por camada (51 commits)

| Camada | Qtd |
|---|---:|
| Frontend (UI) | 12 |
| Backend | 11 |
| Cross IA↔Back | 8 |
| Testes | 8 |
| IA | 4 |
| Cross Back↔Front | 5 |
| Docs | 4 |
| Auto-commit Replit | 2 |
| **Total** | **51** |

### 8.3 Commits canônicos para cherry-pick prioritário (Rail A sprint final)

Para o time receptor que pretende reproduzir o estado final do Rail A (22/22 cards funcionais), aplicar nesta ordem:

1. `ed89147b7` — talent-pool canonical agent (Wave3)
2. `89388004c` — daily_briefing capability_map
3. `ed667d861` — routing determinism tests (38)
4. `e6bf5e2ac` — FE-S03 hex fallback removal (chat-workflow-reels)
5. `16be81325` — FE-S06 dock magnifier parity compact
6. `2e3919e4c` — PR-B Trigger B (drag to offer)
7. `7f0124b89` — shortlist init + PR-O telemetry compact
8. `4028932dd` — PR-O telemetry expanded
9. `bad0a8385` — wizard added to _RAIL_A_EXTRA_TARGETS
10. `bd71815fb` — wire OfferDomain + remove triagem conflict
11. `18b7614c7` — PR-CAL schedule_interview capability_map
12. `e6d36fd39` — PR-E routing test pyramid (29)
13. `44ee3228e` — PR-L design-tokens hex fallback (sessão Claude)
14. `d330b2822` — PR-J/J2 capability_map (sessão Claude)
15. `9e0eee100` — PR-BRIEF rails_adapter daily_summary (sessão Claude)
16. `ccd90ff84` — PR-RAG sourcing_actions RAGPipelineService (sessão Claude)
17. `546b7a7fc` — CI guard removal (W1-2 done)
18. `661028958` — E2E suites
19. `0cf1caa5b` — PR-E expansion LLM-as-judge (sessão Claude)

**Risco total:** 🟢×11 / 🟡×7 / 🔴×1 (apenas `2e3919e4c` PR-B Trigger B é cross-camada).

**Validação após cherry-pick:**
```bash
cd /caminho/lia-agent-system
python -m pytest tests/unit/test_rail_a_routing.py \
                 tests/unit/test_rail_a_routing_deterministic.py \
                 tests/deepeval/test_rail_a_golden_llm_judge.py --no-cov

# Esperado:
# test_rail_a_routing.py: 29 passed
# test_rail_a_routing_deterministic.py: 38 passed (alguns gated por OPENAI_API_KEY)
# test_rail_a_golden_llm_judge.py: 4 passed, 3 skipped (DeepEval gated)
```



---

## 9. Apêndice F — Remediação Wave 0 (Sprint 1 + Sprint 2 · 30/abr → 01/mai/2026)

> Branches: `fix/sprint-1-quick-wins` + `fix/sprint-2-debts`
> 19 commits · origem: `AUDITORIA_SOBREPOSTA.md v1.0` → `REMEDIACAO_PRIORIZADA.md` Wave 0

### 9.1 Lista cronológica Sprint 1 (mais novo → mais antigo)

| Risco | SHA | Data | Camada | Feature | O que faz |
|:---:|---|---|---|---|---|
| 🟢 | `90d770e3b` | 2026-04-30 | Docs | Remediação Wave 0 | docs(sprint-1): handoff document com 10 commit hashes + UAT criteria + Sprint 2 backlog |
| 🟢 | `6b6f55464` | 2026-04-30 | Docs | Remediação Wave 0 | docs(nav): BRANCH_MAP — inicializar com §1 Remediation Wave 0 Sprint 1 |
| 🟢 | `1e4de3106` | 2026-04-30 | Backend | Remediação R-008 | fix(sprint-1): R-008 — hardening ContextVar company_id helper canonical (anti JWT forgery) |
| 🟢 | `6ec3584eb` | 2026-04-30 | Backend | Remediação R-007 | fix(sprint-1): R-007 — decode_token valida exp/aud/iss explicitamente |
| 🟢 | `a5e649ba1` | 2026-04-30 | Backend + Infra | Remediação R-006 | fix(sprint-1): R-006 — DEV_MODE gateado por ENVIRONMENT (anti config drift) |
| 🟢 | `7697743dc` | 2026-04-30 | Testes | Remediação R-005 | fix(sprint-1): R-005 — pin G2 sensor para WSI/pipeline/sourcing routers (regressão) |
| 🟢 | `d81287102` | 2026-04-30 | Backend + IA | Remediação R-004 | fix(sprint-1): R-004 — output_schema field em ToolDefinition + caller exemplar |
| 🟢 | `98d7dc3b9` | 2026-04-30 | Backend + Compliance | Remediação R-003 | fix(sprint-1): R-003 — enriquecer criteria_used no AuditService (LGPD Art.20) |
| 🟡 | `dd0644d75` | 2026-04-30 | Backend | Remediação R-002 | fix(sprint-1): R-002 — track_llm_usage_start helper canonical + wire em wsi/_shared |
| 🟡 | `5eb36f886` | 2026-04-30 | Backend + IA | Remediação R-001 | fix(sprint-1): R-001 — eliminar bypass BYOK em skills_ontology_engine |
| 🟢 | `a6bafc7c9` | 2026-04-30 | Backend | Remediação R-009 | fix(sprint-1): R-009 — wire BYOK linter no CI workflow |

### 9.2 Lista cronológica Sprint 2 (mais novo → mais antigo)

| Risco | SHA | Data | Camada | Feature | O que faz |
|:---:|---|---|---|---|---|
| 🟢 | `44511dc6b` | 2026-05-01 | Backend + Scripts | Débito harness | fix(sprint-2): ruff cleanup — F401/I001 em crew_audit + I001 em human_review + E701 em sensor |
| 🟢 | `a33b0efe4` | 2026-05-01 | Scripts | DEBT-007 sensor G-TOOLS | feat(sprint-2): DEBT-007 — sensor G-TOOLS check_tool_output_schemas.py (217 baseline violations) |
| 🟢 | `a4161051a` | 2026-05-01 | Scripts | DEBT-013 sensor G-CONTEXTVAR | feat(sprint-2): DEBT-013 — sensor G-CONTEXTVAR check_no_direct_contextvar_set.py |
| 🟢 | `1ab13494b` | 2026-05-01 | Scripts | DEBT-009 sensor G-DEVMODE | feat(sprint-2): DEBT-009 — sensor G-DEVMODE anti LIA_DEV_MODE em .env.staging/production |
| 🟡 | `a0afb6e11` | 2026-05-01 | IA | DEBT-002 LLM Factory | feat(sprint-2): DEBT-002 — track_llm_usage_start DENTRO de generate_with_fallback (LLM Factory canonical) |
| 🟢 | `c8d1644ed` | 2026-05-01 | Backend + Compliance | DEBT-004 criteria_used | fix(sprint-2): DEBT-004 — enriquecer criteria_used em crew_audit + human_review_sampling |
| 🟢 | `dd7002d2c` | 2026-05-01 | Backend | DEBT-014 allowlist LLM | fix(sprint-2): DEBT-014 — allowlist tenant_llm_context.py em check_llm_imports.py |
| 🟢 | `8ff53fc5e` | 2026-05-01 | Backend | DEBT-001 E402 | fix(sprint-2): DEBT-001 — mover fastapi imports antes do ContextVar (E402 cleanup) |

### 9.3 Síntese por camada (19 commits)

| Camada | Sprint 1 | Sprint 2 | Total |
|---|---:|---:|---:|
| Backend | 5 | 3 | 8 |
| Backend + IA | 2 | 1 | 3 |
| Backend + Compliance | 1 | 1 | 2 |
| Backend + Infra | 1 | 0 | 1 |
| Backend + Scripts | 0 | 1 | 1 |
| Scripts (sensores) | 0 | 3 | 3 |
| Testes | 1 | 0 | 1 |
| Docs | 2 | 0 | 2 |
| **Total** | **11** | **8** | **19** |

### 9.4 Commits canônicos para cherry-pick prioritário (ordem segura)

Para o time receptor que quer aplicar os fixes de remediação de segurança Wave 0, aplicar nesta ordem:

**Sprint 1 (aplicar todos, nessa sequência):**
1. `a6bafc7c9` — R-009: BYOK linter no CI (sensor ativo antes de tudo)
2. `5eb36f886` — R-001: BYOK bypass removido de skills_ontology_engine
3. `dd0644d75` — R-002: token tracking canonical em wsi/_shared
4. `98d7dc3b9` — R-003: criteria_used LGPD Art.20 estruturado
5. `d81287102` — R-004: output_schema em ToolDefinition
6. `7697743dc` — R-005: G2 sensor pinado para WSI/pipeline/sourcing
7. `a5e649ba1` — R-006: DEV_MODE gate por ENVIRONMENT
8. `6ec3584eb` — R-007: JWT exp/aud/iss explícito
9. `1e4de3106` — R-008: ContextVar company_id hardening (depende de R-007)
10. `6b6f55464` — docs: BRANCH_MAP §1
11. `90d770e3b` — docs: handoff Sprint 1

**Sprint 2 (aplicar após Sprint 1 completo):**
1. `8ff53fc5e` — DEBT-001: E402 cleanup
2. `dd7002d2c` — DEBT-014: allowlist tenant_llm_context
3. `c8d1644ed` — DEBT-004: criteria_used crew_audit + human_review
4. `a0afb6e11` — DEBT-002: token tracking no LLM Factory (canônico)
5. `1ab13494b` — DEBT-009: sensor G-DEVMODE
6. `a4161051a` — DEBT-013: sensor G-CONTEXTVAR
7. `a33b0efe4` — DEBT-007: sensor G-TOOLS
8. `44511dc6b` — ruff cleanup final

**Risco total:** 🟢×17 / 🟡×2 / 🔴×0

**Validação após cherry-pick:**
```bash
cd /caminho/lia-agent-system

# Testes de segurança Sprint 1
python -m pytest \
  tests/security/test_dev_mode_env_gate.py \
  tests/security/test_red_team_jwt_forgery.py \
  tests/integration/test_ci_byok_linter_wired.py \
  tests/integration/test_skills_ontology_byok.py \
  tests/integration/test_audit_criteria_enriched.py \
  -v --no-cov

# Sensores Sprint 2 (todos devem sair exit 0)
python3 scripts/check_llm_factory_enforcement.py
python3 scripts/check_llm_imports.py
python3 scripts/check_no_devmode_in_prod_env.py
python3 scripts/check_no_direct_contextvar_set.py
echo "Todos os sensores OK"

# G-TOOLS: 217 violations esperadas (baseline — não é erro, é a dívida documentada)
python3 scripts/check_tool_output_schemas.py 2>&1 | tail -3
```
