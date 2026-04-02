# Auditoria: Arquivos Replit vs PRODUCT_DESIGN_INVENTORY.md

> Gerado: Abril 2026 | Comparação arquivo-a-arquivo

---

## RESUMO EXECUTIVO

| Métrica | Replit (Real) | Inventário (Doc) | Status |
|---------|---------------|-------------------|--------|
| **Componentes UI base** (`ui/`) | 68 .tsx | 68 | ✅ Match |
| **Modais centrais** (`modals/`) | 34 .tsx + 6 subdirs | "33 principais + subdirs" | ⚠️ Doc diz 33, real = 34 |
| **Componentes root** (soltos em `components/`) | 71 .tsx | ~20 documentados | ❌ 51 não documentados |
| **Hooks** (`hooks/`) | 102 arquivos | "90+" | ⚠️ Aproximação OK, real = 102 |
| **Lib/Utils** (`lib/`) | 28 arquivos | "20+" | ⚠️ Aproximação OK, real = 28 |
| **Pages** (`pages/`) | 25 .tsx + 8 subdirs | ~20 pages | ⚠️ Faltam 5 pages |
| **Settings** | 40 arquivos + 5 subdirs | "30+" | ⚠️ Real = 40 |
| **Total diretórios de componentes** | 53 | ~45 documentados | ⚠️ ~8 dirs sem seção dedicada |
| **Total arquivos src** | 1,825 | — | (não contado no doc) |

---

## 1. COMPONENTES UI BASE (`ui/`) — 68 ARQUIVOS

### Arquivos no Replit (68 .tsx):
```
accordion.tsx, ai-disclaimer.tsx, alert-dialog.tsx, audio-player.tsx,
audio-record-button.tsx, avatar.tsx, badge.tsx, big-five-profile.tsx,
bulk-selection-bar.tsx, button.tsx, candidate-card.tsx, candidate-queries-guide.tsx,
card.tsx, chat-status-indicators.tsx, checkbox.tsx, collapsible.tsx,
command-palette.tsx, command.tsx, context-pill.tsx, cookie-consent.tsx,
data-request-indicator.tsx, date-range-picker.tsx, dialog.tsx, dropdown-menu.tsx,
empty-state.tsx, file-upload-button.tsx, input.tsx, interview-rating.tsx,
interview-scheduling-modal.tsx, label.tsx, lia-expanded-panel.tsx, lia-icon.tsx,
lia-prompt-header.tsx, lia-queries-guide.tsx, lia-search-queries-guide.tsx,
lia-vacancy-queries-guide.tsx, loading.tsx, masked-input.tsx, pipeline-report.tsx,
pipeline-stages-carousel.tsx, popover.tsx, premium-autocomplete.tsx, progress.tsx,
prompt-suggestions-dock.tsx, prompt-suggestions-popover.tsx, quick-action-chips.tsx,
radio-group.tsx, resizable-table-header.tsx, score-icon-button.tsx, scroll-area.tsx,
search-loading-animation.tsx, select.tsx, separator.tsx, setup-alert-badge.tsx,
sheet.tsx, skeleton.tsx, slider.tsx, status-badge.tsx, switch.tsx, table.tsx,
tabs.tsx, textarea.tsx, thinking-dots.tsx, toaster.tsx, toast.tsx, tooltip.tsx,
unified-bulk-actions-bar.tsx, variable-selector.tsx
```

### Status no inventário: ✅ Todos documentados na Seção 2

---

## 2. MODAIS CENTRAIS (`modals/`) — 34 ARQUIVOS + 6 SUBDIRS

### Arquivos no Replit (34 .tsx):
```
add-candidate-modal, add-candidates-to-vacancy-modal, add-list-to-vacancies-modal,
add-to-job-modal, add-to-list-modal, bulk-action-modal, candidate-compare-modal,
close-vacancy-modal, create-job-modal, create-job-with-candidates-modal,
data-blocking-modal, data-request-modal, edit-job-modal.constants, edit-job-modal,
english-test-modal, general-score-modal, insufficient-data-modal,
job-assign-recruiter-modal, job-compare-modal, job-duplicate-modal,
job-insights-modal, job-publish-modal, job-status-modal, job-unpublish-modal,
lia-analysis-modal, new-candidate-unified-modal, persona-creation-modal,
screening-media-modal, shared-search-details-modal, share-search-modal,
stage-transition-actions-modal, technical-test-modal, unified-communication-modal,
unsaved-pearch-warning-modal
```

### Sub-diretórios (6 + __tests__):
- `edit-job/` (2 arquivos: types, hook)
- `edit-job-sections/` (4 arquivos: BasicInfo, Privacy, Requirements, index)
- `job-compare/` (3 arquivos: candidate-funnel-panel, lia-analysis-panel, index)
- `job-insights/` (6 arquivos: constants, types, sections/Overview, sections/Pipeline, hook, index)
- `job-status/` (4 arquivos: ActivateOptions, PauseOptions, utils, test)
- `new-candidate/` (1 arquivo: InputStep)

### Discrepância: Doc diz "33", real = 34. Verificar `edit-job-modal.constants.tsx` (pode ser contado separadamente)

---

## 3. COMPONENTES ROOT (soltos em `components/`) — 71 ARQUIVOS ❌

### Arquivos no Replit NÃO documentados individualmente no inventário:

Os seguintes 71 arquivos .tsx existem diretamente em `components/` (não dentro de subdiretórios):

| # | Arquivo | Documentado? |
|---|---------|-------------|
| 1 | activity-feed.tsx | ❌ |
| 2 | ai-search-toggle.tsx | ❌ |
| 3 | auth-context.tsx | ❌ |
| 4 | batch-approval-modal.tsx | ✅ (Seção 13O) |
| 5 | big-five-modal.tsx | ✅ (Seção 13O) |
| 6 | bulk-actions-bar.tsx | ❌ |
| 7 | calibration-card.tsx | ❌ |
| 8 | candidate-comparison.tsx | ❌ |
| 9 | candidate-decision-flow-modal.tsx | ✅ (Seção 13O) |
| 10 | candidate-modal.tsx | ❌ |
| 11 | candidate-page.tsx | ❌ |
| 12 | candidate-preview.tsx | ❌ |
| 13 | client-only.tsx | ❌ |
| 14 | clouds-background.tsx | ❌ |
| 15 | column-configuration-modal.tsx | ✅ (Seção 13O) |
| 16 | company-screening-settings.tsx | ❌ |
| 17 | contextual-actions-banner.tsx | ❌ |
| 18 | daily-briefing-card.tsx | ❌ |
| 19 | dashboard-app.tsx | ❌ |
| 20 | disc-assessment-modal.tsx | ✅ (Seção 13O) |
| 21 | error-boundary.tsx | ❌ |
| 22 | events-section.tsx | ❌ |
| 23 | expandable-ai-prompt.tsx | ❌ |
| 24 | expanded-chat-modal.tsx | ✅ (Seção 13C) |
| 25 | experience-highlight-card.tsx | ❌ |
| 26 | export-tools.tsx | ❌ |
| 27 | fairness-warning-banner.tsx | ❌ |
| 28 | global-search-modal.tsx | ✅ (Seção 13O) |
| 29 | intelligence-notifications.tsx | ❌ |
| 30 | interviews-section.tsx | ❌ |
| 31 | job-actions-bar.tsx | ❌ |
| 32 | job-report-modal.tsx | ✅ (Seção 13O) |
| 33 | lia-expanded-prompt.tsx | ❌ |
| 34 | lia-metrics-chart.tsx | ❌ |
| 35 | lia-metrics-dashboard.tsx | ❌ |
| 36 | lia-performance-indicators.tsx | ❌ |
| 37 | lia-processing-card.tsx | ❌ |
| 38 | lia-score-card.tsx | ❌ |
| 39 | lia-screening-dialogue.tsx | ❌ |
| 40 | lia-screening-guide.tsx | ❌ |
| 41 | lia-suggestion-cards.tsx | ❌ |
| 42 | lia-tips-modal.tsx | ✅ (Seção 13O) |
| 43 | ml-insights-card.tsx | ❌ |
| 44 | notification-system.tsx | ❌ |
| 45 | page-transition.tsx | ❌ |
| 46 | presentation-mode.tsx | ❌ |
| 47 | proactive-insight-card.tsx | ❌ |
| 48 | PromptContextViewer.tsx | ❌ |
| 49 | PromptSuggestionsPanel.tsx | ❌ |
| 50 | quick-actions-modals.tsx | ✅ (Seção 13Y) |
| 51 | quick-view-modal.tsx | ✅ (Seção 13O) |
| 52 | react-thinking-stream.tsx | ❌ |
| 53 | regional-analysis.tsx | ❌ |
| 54 | reveal-credits-modal.tsx | ✅ (Seção 13O) |
| 55 | rubric-evaluation-card.tsx | ❌ |
| 56 | rubric-evaluation-modal.tsx | ✅ (Seção 10.35) |
| 57 | save-command-modal.tsx | ✅ (Seção 13O) |
| 58 | sidebar.tsx | ✅ (Seção 3) |
| 59 | task-modal.tsx | ✅ (Seção 13O) |
| 60 | tasks-section.tsx | ❌ |
| 61 | template-suggestion-toast.tsx | ❌ |
| 62 | test-status-indicators.tsx | ❌ |
| 63 | theme-provider.tsx | ❌ |
| 64 | theme-toggle.tsx | ❌ |
| 65 | timeline-section.tsx | ❌ |
| 66 | top-bar.tsx | ✅ (Seção 4) |
| 67 | triagem-details-modal.tsx | ✅ (Seção 13O) |
| 68 | user-commands-section.tsx | ❌ |
| 69 | war-room.tsx | ❌ |
| 70 | wedo-logo.tsx | ❌ |
| 71 | work-model-charts.tsx | ❌ |

### Resumo root: 18 documentados / 53 NÃO documentados

---

## 4. HOOKS (`hooks/`) — 102 ARQUIVOS

### Doc diz "90+", real = 102. Diferença de 12 hooks.

### Hooks no Replit não mencionados no inventário:
```
promptStateCriteriaUtils.ts, use-action-intent.ts, useAgentMemory.ts,
use-agent-streaming.ts, use-ai-consumption.ts, use-ai-credits.ts,
use-archetypes.ts, use-bias-audit-report.ts, use-candidate-compare.ts,
use-candidate-data-requests.ts, use-chat-file-handling.ts, useChatLayout.ts,
use-chat-page-state.ts, use-chat-search.ts, use-clients.ts,
use-communication-templates.ts, useCompanyBenefits.ts, use-company-culture.ts,
use-company-defaults.ts, use-company-eligibility-questions.ts,
use-company-lia-instructions.ts, use-company-managers.ts, use-company-pipeline.ts,
useCompanySkillsCatalog.ts, use-company-tech-stack.ts, useCreditEstimator.ts,
use-current-company.ts, use-current-scope.ts, use-daily-briefing.ts,
use-data-request-config.ts, use-data-request-modals.ts, useDynamicSuggestions.ts,
use-edit-lock.tsx, use-empty-field-notifications.ts, useFastTrack.ts,
use-float-conversation.ts, use-float-streaming.ts, useGlobalSearchSettings.ts,
useHideViewedCandidates.ts, use-hiring-policies.ts, use-interpret-context.ts,
use-job-analytics.ts, useJobColumnConfig.ts, use-job-draft.ts,
useJobFiltersPersistence.ts, use-job-report.ts, use-job-wizard-backend.ts,
use-keyboard-shortcuts.ts, use-lia-suggestions.ts, use-ml-predictions.ts,
use-navigation-intent.ts, use-navigation-persistence.ts, use-notifications.ts,
use-override-approve.ts, use-pipeline-inheritance.ts, use-proactive-alerts.ts,
use-proactive-insights.ts, usePromptState.ts, use-recent-items.ts,
use-recruitment-stages.ts, use-return-events.ts, use-saas-metrics.ts,
use-scim-config.ts, use-score-breakdown.ts, useScreeningConfig.ts,
use-screening-questions.ts, use-search-autocomplete.ts, use-search-entities.ts,
useSearchFlow.ts, use-search-source.ts, useSemanticSearch.ts,
useSessionRefresh.ts, useSessionTimeout.ts, useSettingsForm.ts,
useSettingsNavigation.ts, use-short-list.ts, use-similar-profiles.ts,
use-sub-status-panel.ts, useTableFeatures.ts, useTagInputState.ts,
use-talent-funnel.ts, use-template-suggestions.ts, use-toast.ts,
use-transition-context.ts, use-triagem-chat.ts, useUIActions.ts,
useUnifiedSearch.ts, useUnsavedChanges.ts, use-wizard-auto-save.ts,
use-wizard-suggestions.ts, use-workforce-planning.ts, use-workos-metrics.ts,
use-wsi-async.ts
```

(Inventário lista somente os hooks de nível alto, não cada um individualmente)

---

## 5. LIB/UTILS (`lib/`) — 28 ARQUIVOS

### Doc diz "20+", real = 28. Listagem completa:
```
candidates-mock-data.ts, chat-commands.ts, chat-format.test.ts, chat-format.ts,
design-tokens.ts, fetch-client.ts, format-utils.ts (T001),
hiring-policy-utils.test.ts, hiring-policy-utils.ts, industry-constants.ts,
masks.test.ts, masks.ts, recruitment-stages.ts, safe-data.test.ts, safe-data.ts,
sanitize.test.ts, sanitize.ts, session-cleanup.ts, session-crypto.ts,
template-variables.test.ts, template-variables.ts, toast.ts, utils.ts,
vue-bridge.ts, web-vitals.ts, workos-links.ts, workos-session.ts, workos.ts
```

---

## 6. PAGES (`pages/`) — 25 ARQUIVOS + 8 SUBDIRS

### Pages no Replit:
```
ai-credits-page.tsx, ats-integrations-page.tsx, big-five-dashboard-page.tsx,
candidate-review-modal.tsx, candidates-page.tsx, chat-page.tsx, dashboards-page.tsx,
executive-dashboard-page.tsx, indicators-page.tsx, integrations-page.tsx,
job-kanban-page.tsx, jobs-page.tsx, job-templates-page.tsx, lia-library-page.tsx,
login-page.tsx, onboarding-page.tsx, onboarding-premium-page.tsx,
real-time-dashboard-page.tsx, settings-page-enhanced.tsx, task-helpers.tsx,
tasks-page-mvp.tsx, tasks-page.tsx, templates-page.tsx,
workflow-automation-page.tsx, work-model-analytics-page.tsx
```

### Sub-diretórios de pages:
| Subdir | Arquivos | Status Doc |
|--------|----------|-----------|
| `ats-integrations/` | 5 | ✅ Documentado |
| `candidates/` | 76 | ✅ Parcial (doc menciona ~30+) |
| `chat-page/` | 16 | ✅ Documentado |
| `dashboards-page/` | 12 | ✅ Documentado |
| `indicators/` | 9 | ✅ Documentado |
| `job-kanban/` | 51 | ✅ Parcial (doc menciona ~20+) |
| `jobs/` | 26 | ✅ Parcial (doc menciona ~12+) |
| `tasks/` | 2 | ✅ Documentado |

---

## 7. DIRETÓRIOS NÃO DOCUMENTADOS NO INVENTÁRIO

| Diretório | Arquivos | Conteúdo |
|-----------|----------|----------|
| `async/` | 1 | AsyncJobProgress.tsx |
| `automation/` | 1 | ProactiveChatMessage.tsx |
| `cv/` | 3 | cv-preview, cv-upload-modal, index |
| `dashboard/` | 2 | predictive-analytics-tab, strategic-dashboard |
| `expandable-ai-prompt/` | 14 | Prompt expandível (tabs, hooks) |
| `filters/` | 1 | robust-filters.tsx |
| `jobs/` (componente) | 14 | Componentes de jobs fora de pages |
| `lia-screening/` | 1 | LIA screening |
| `lists/` | 1 | Listas |
| `ml/` | 1 | ML component |
| `ml-analytics/` | 1 | ML Analytics |
| `module-access/` | 1 | Module access control |
| `report-scheduler/` | 1 | Agendamento de relatórios |
| `reports/` | 1 | Relatórios |
| `score/` | 1 | Score component |
| `wizard/` | 0 | (vazio) |

---

## 8. SETTINGS (`settings/`) — 40 ARQUIVOS + 5 SUBDIRS

### Arquivos root settings (40):
```
ApprovalsHub, ApproverSection, BenefitsTab, BigFiveRadar, CommunicationHub,
CompanyDataCard, CompanyDataSection, CompanyTeamHub, companyTeamHub.types,
CultureAnalyzer, CultureProfilePreview, DataRequestTab, DepartmentsTab,
eligibility-questions-bank, GlobalSearchHub, goals-management, goalsPlanningConstants,
GoalsPlanningHub, HiringPoliciesHub, LiaFieldToggle, LiaInstructionPopover,
progress-dashboard, RecruitmentHub, RecruitmentJourneyConfig, recruitment-journey.types,
settings-api-keys-tab, settings-billing-tab, settings-company-tabs, settings-general-tab,
settings-integrations-tab, settings-journey-tab, settings-notifications-tab,
settings-recruitment-tabs, settings-security-tab, SmartImportZone, StageCard,
TechStackTab, use-goals-management, user-management, validation-system
```

### Sub-diretórios settings:
| Subdir | Arquivos | No Doc? |
|--------|----------|---------|
| `benefits/` | 3 (BenefitFormModal, BenefitItemCard, BenefitTemplateModal) | ✅ Mencionado |
| `communication-hub/` | 8 (AlertsTab, constants, types, utils, ScheduleTab, SignatureTab, TemplatesTab, hook) | ✅ Mencionado |
| `company/` | 2 (GeneralInfoSection, index) | ✅ Mencionado |
| `goals/` | 6 (ApplyAllModal, DeleteConfirmModal, EditableCell, GoalsStatsCards, goals-utils, index) | ✅ Mencionado |
| `recruitment/` | 6 (assessment-tab, automations-tab, communication-tab, index, nps-tab, recruitment-journey-tab) | ✅ Mencionado |

### Componentes settings NÃO no inventário:
```
ApprovalsHub.tsx, BigFiveRadar.tsx, CompanyDataCard.tsx, CompanyDataSection.tsx,
CompanyTeamHub.tsx, companyTeamHub.types.ts, CultureAnalyzer.tsx,
CultureProfilePreview.tsx, DataRequestTab.tsx, eligibility-questions-bank.ts,
GlobalSearchHub.tsx, goals-management.tsx, goalsPlanningConstants.ts,
GoalsPlanningHub.tsx, HiringPoliciesHub.tsx, LiaFieldToggle.tsx,
LiaInstructionPopover.tsx, progress-dashboard.tsx, recruitment-journey.types.ts,
use-goals-management.ts
```

---

## 9. SCREENING CONFIG vs WSI vs SCREENING

| Diretório | Arquivos Real | No Doc? |
|-----------|---------------|---------|
| `screening-config/` | 17 (15 tsx + 1 ts + hooks/) | ✅ Seção 10.34B |
| `screening/` | 2 (index, screening-notification-card) | ✅ Seção 10.34C |
| `wsi/` | 13 (10 tsx + jd-evaluation/ subdir) | ✅ Seção 10.34D |

---

## 10. RESUMO FINAL DE GAPS

### Gaps Críticos (componentes existem mas NÃO estão documentados):

| Categoria | Qtd Faltando | Prioridade |
|-----------|-------------|-----------|
| Componentes root soltos | 53 de 71 | 🔴 Alta |
| Settings componentes | ~20 de 40 | 🟡 Média |
| Hooks (listagem individual) | Sem listagem 1-a-1 | 🟡 Média |
| Diretórios sem seção dedicada | ~16 dirs | 🟡 Média |
| Candidates page sub-componentes | ~46 faltando | 🟡 Média |
| Job-Kanban sub-componentes | ~31 faltando | 🟡 Média |

### Contagens que precisam atualizar no Doc:

| Campo | Doc Atual | Real | Ação |
|-------|-----------|------|------|
| Modais centrais | 33 | 34 | Atualizar para 34 |
| Hooks | 90+ | 102 | Atualizar para 102 |
| Lib | 20+ | 28 | Atualizar para 28 |
| Settings | 30+ | 40 + 25 sub | Atualizar para 40 |
| Pages | ~20 | 25 | Atualizar para 25 |
| Root components | — | 71 | Adicionar seção |

---

## CONCLUSÃO

O inventário cobre bem a **estrutura geral** e os **componentes UI base**, mas tem gaps significativos nos:

1. **71 componentes root** soltos em `components/` — apenas 18 estão documentados
2. **Sub-componentes de pages** — candidates (76 arquivos), job-kanban (51 arquivos), jobs (26 arquivos) estão parcialmente documentados
3. **Settings** — 20 dos 40 arquivos root não estão listados
4. **Hooks** — listagem individual de todos os 102 hooks não existe
5. **~16 diretórios menores** sem seção dedicada no inventário

Total de cobertura estimada: **~60-65%** dos arquivos reais estão representados no inventário.
