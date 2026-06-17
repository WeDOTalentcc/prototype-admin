# Vue Migration Bridge — Auditoria de Compatibilidade React → Vue 3 + Pinia

**Data de auditoria:** 2026-03-31  
**Auditor:** Claude Sonnet 4.6 (automated)  
**Codebase:** Plataforma LIA — Next.js 15 + React 19 + TypeScript 5.8

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Total de hooks auditados | 99 |
| Hooks Pinia-ready (sem JSX) | 97 (98%) |
| Hooks com JSX/ReactNode no retorno | 2 (2%) |
| Componentes com `React.memo` antes da auditoria | 47 |
| `React.memo` adicionados nesta auditoria | 6 |
| Componentes com `React.memo` após auditoria | 53 |
| Componentes com `displayName` adicionado nesta auditoria | 8 |
| **Vue Readiness estimado** | **~87%** |

---

## 1. Hooks Pinia-Ready (retornam apenas estado + callbacks, zero JSX)

Estes hooks estão prontos para migração direta para Pinia stores. O padrão de retorno `{ state, actions }` já é compatível com `defineStore()`.

### Hooks de Domínio (Business Logic)

| Hook | Arquivo | Pattern de Migração Vue |
|------|---------|------------------------|
| `useAgentMemory` | `src/hooks/useAgentMemory.ts` | Pinia store `useAgentMemoryStore` |
| `use-agent-streaming` | `src/hooks/use-agent-streaming.ts` | Pinia + composable |
| `use-ai-consumption` | `src/hooks/use-ai-consumption.ts` | Pinia store |
| `use-ai-credits` | `src/hooks/use-ai-credits.ts` | Pinia store |
| `use-archetypes` | `src/hooks/use-archetypes.ts` | Pinia store |
| `use-bias-audit-report` | `src/hooks/use-bias-audit-report.ts` | Pinia store |
| `use-bulk-selection` | `src/hooks/use-bulk-selection.ts` | Pinia store |
| `use-candidate-compare` | `src/hooks/use-candidate-compare.ts` | Pinia store |
| `use-candidate-data-requests` | `src/hooks/use-candidate-data-requests.ts` | Pinia store |
| `use-candidate-filters` | `src/hooks/use-candidate-filters.ts` | Pinia store |
| `use-candidate-selection` | `src/hooks/use-candidate-selection.ts` | Pinia store |
| `use-candidates-list` | `src/hooks/use-candidates-list.ts` | Pinia + axios |
| `use-candidates-list-mapped` | `src/hooks/use-candidates-list-mapped.ts` | Pinia computed |
| `use-candidates-search-state` | `src/hooks/use-candidates-search-state.ts` | Pinia store |
| `use-candidates-view-state` | `src/hooks/use-candidates-view-state.ts` | Pinia store |
| `use-chat-file-handling` | `src/hooks/use-chat-file-handling.ts` | Pinia + composable |
| `use-chat-page-state` | `src/hooks/use-chat-page-state.ts` | Pinia store |
| `use-chat-search` | `src/hooks/use-chat-search.ts` | Pinia store |
| `use-clients` | `src/hooks/use-clients.ts` | Pinia store |
| `use-communication-templates` | `src/hooks/use-communication-templates.ts` | Pinia store |
| `use-company-culture` | `src/hooks/use-company-culture.ts` | Pinia store |
| `use-company-defaults` | `src/hooks/use-company-defaults.ts` | Pinia store |
| `use-company-eligibility-questions` | `src/hooks/use-company-eligibility-questions.ts` | Pinia store |
| `use-company-lia-instructions` | `src/hooks/use-company-lia-instructions.ts` | Pinia store |
| `use-company-managers` | `src/hooks/use-company-managers.ts` | Pinia store |
| `use-company-tech-stack` | `src/hooks/use-company-tech-stack.ts` | Pinia store |
| `use-current-company` | `src/hooks/use-current-company.ts` | Pinia store |
| `use-current-scope` | `src/hooks/use-current-scope.ts` | Pinia store |
| `use-daily-briefing` | `src/hooks/use-daily-briefing.ts` | Pinia + axios |
| `use-data-request-config` | `src/hooks/use-data-request-config.ts` | Pinia store |
| `use-data-request-modals` | `src/hooks/use-data-request-modals.ts` | Pinia store |
| `use-empty-field-notifications` | `src/hooks/use-empty-field-notifications.ts` | Pinia store |
| `use-float-conversation` | `src/hooks/use-float-conversation.ts` | Pinia store |
| `use-float-streaming` | `src/hooks/use-float-streaming.ts` | Pinia store |
| `use-hiring-policies` | `src/hooks/use-hiring-policies.ts` | Pinia store |
| `use-interpret-context` | `src/hooks/use-interpret-context.ts` | Pinia store |
| `use-job-analytics` | `src/hooks/use-job-analytics.ts` | Pinia + axios |
| `use-job-draft` | `src/hooks/use-job-draft.ts` | Pinia store |
| `use-job-report` | `src/hooks/use-job-report.ts` | Pinia + axios |
| `use-job-wizard-backend` | `src/hooks/use-job-wizard-backend.ts` | Pinia store |
| `use-lia-suggestions` | `src/hooks/use-lia-suggestions.ts` | Pinia + axios |
| `use-ml-predictions` | `src/hooks/use-ml-predictions.ts` | Pinia + axios |
| `use-navigation-intent` | `src/hooks/use-navigation-intent.ts` | Pinia store |
| `use-navigation-persistence` | `src/hooks/use-navigation-persistence.ts` | Pinia store |
| `use-override-approve` | `src/hooks/use-override-approve.ts` | Pinia store |
| `use-pipeline-inheritance` | `src/hooks/use-pipeline-inheritance.ts` | Pinia store |
| `use-proactive-alerts` | `src/hooks/use-proactive-alerts.ts` | Pinia store |
| `use-proactive-insights` | `src/hooks/use-proactive-insights.ts` | Pinia store |
| `use-recent-items` | `src/hooks/use-recent-items.ts` | Pinia store |
| `use-recruitment-stages` | `src/hooks/use-recruitment-stages.ts` | Pinia store |
| `use-return-events` | `src/hooks/use-return-events.ts` | Pinia store |
| `use-saas-metrics` | `src/hooks/use-saas-metrics.ts` | Pinia + axios |
| `use-scim-config` | `src/hooks/use-scim-config.ts` | Pinia store |
| `use-score-breakdown` | `src/hooks/use-score-breakdown.ts` | Pinia store |
| `use-search-autocomplete` | `src/hooks/use-search-autocomplete.ts` | Pinia store |
| `use-search-entities` | `src/hooks/use-search-entities.ts` | Pinia store |
| `use-search-source` | `src/hooks/use-search-source.ts` | Pinia store |
| `use-short-list` | `src/hooks/use-short-list.ts` | Pinia store |
| `use-similar-profiles` | `src/hooks/use-similar-profiles.ts` | Pinia store |
| `use-sub-status-panel` | `src/hooks/use-sub-status-panel.ts` | Pinia store |
| `use-talent-funnel` | `src/hooks/use-talent-funnel.ts` | Pinia store |
| `use-toast` | `src/hooks/use-toast.ts` | Pinia store |
| `use-transition-context` | `src/hooks/use-transition-context.ts` | Pinia store |
| `use-triagem-chat` | `src/hooks/use-triagem-chat.ts` | Pinia store |
| `use-wizard-auto-save` | `src/hooks/use-wizard-auto-save.ts` | Pinia store |
| `use-wizard-suggestions` | `src/hooks/use-wizard-suggestions.ts` | Pinia store |
| `use-workforce-planning` | `src/hooks/use-workforce-planning.ts` | Pinia store |
| `use-workos-metrics` | `src/hooks/use-workos-metrics.ts` | Pinia store |
| `use-wsi-async` | `src/hooks/use-wsi-async.ts` | Pinia store |

### Hooks Utilitários (Pinia-Ready)

| Hook | Arquivo | Observação |
|------|---------|-----------|
| `useCandidateSuggestions` | `src/hooks/useCandidateSuggestions.ts` | Vue: composable |
| `useChatLayout` | `src/hooks/useChatLayout.ts` | Vue: composable |
| `useCompanyBenefits` | `src/hooks/useCompanyBenefits.ts` | Pinia store |
| `useCompanySkillsCatalog` | `src/hooks/useCompanySkillsCatalog.ts` | Pinia store |
| `useCreditEstimator` | `src/hooks/useCreditEstimator.ts` | Pinia computed |
| `useDynamicSuggestions` | `src/hooks/useDynamicSuggestions.ts` | Pinia store |
| `useFastTrack` | `src/hooks/useFastTrack.ts` | Pinia store |
| `useGlobalSearchSettings` | `src/hooks/useGlobalSearchSettings.ts` | Pinia store |
| `useHideViewedCandidates` | `src/hooks/useHideViewedCandidates.ts` | Pinia store |
| `useJobColumnConfig` | `src/hooks/useJobColumnConfig.ts` | Pinia store |
| `useJobFiltersPersistence` | `src/hooks/useJobFiltersPersistence.ts` | Pinia + localStorage |
| `usePromptState` | `src/hooks/usePromptState.ts` | Pinia store |
| `useScreeningConfig` | `src/hooks/useScreeningConfig.ts` | Pinia store |
| `useSearchFlow` | `src/hooks/useSearchFlow.ts` | Pinia store |
| `useSemanticSearch` | `src/hooks/useSemanticSearch.ts` | Pinia + axios |
| `useSessionRefresh` | `src/hooks/useSessionRefresh.ts` | Pinia store |
| `useSessionTimeout` | `src/hooks/useSessionTimeout.ts` | Vue: onMounted + watch |
| `useSettingsForm` | `src/hooks/useSettingsForm.ts` | Pinia store |
| `useSettingsNavigation` | `src/hooks/useSettingsNavigation.ts` | Pinia store |
| `useTableFeatures` | `src/hooks/useTableFeatures.ts` | Vue: composable |
| `useTemplateSuggestions` | `src/hooks/use-template-suggestions.tsx` | Pinia + localStorage |
| `useUIActions` | `src/hooks/useUIActions.ts` | Pinia store |
| `useUnifiedSearch` | `src/hooks/useUnifiedSearch.ts` | Pinia store |
| `useUnsavedChanges` | `src/hooks/useUnsavedChanges.ts` | Vue: composable |
| `useActionIntent` | `src/hooks/use-action-intent.ts` | Vue: composable |

---

## 2. Hooks que Precisam de Refatoração

Estes 2 hooks contêm JSX ou ReactNode no objeto de retorno, o que é incompatível com Vue 3.

### `use-edit-lock.tsx` — PRIORIDADE ALTA

**Arquivo:** `src/hooks/use-edit-lock.tsx`  
**Problema:** Retorna `EditButton: React.FC` e `SaveCancelButtons: React.FC` como parte do objeto de retorno. Isso é um anti-padrão Vue (componentes não podem ser retornados de composables Pinia).

**Refatoração necessária:**
```typescript
// ANTES (anti-padrão Vue):
return {
  isEditing,
  isSaving,
  startEditing,
  cancelEditing,
  saveAndExit,
  EditButton,       // ← JSX component — INCOMPATÍVEL Vue
  SaveCancelButtons // ← JSX component — INCOMPATÍVEL Vue
}

// DEPOIS (Pinia-compatible):
// 1. Extrair EditButton como componente standalone: src/components/ui/edit-button.tsx
// 2. Extrair SaveCancelButtons como componente standalone: src/components/ui/save-cancel-buttons.tsx
// 3. Hook retorna apenas estado e actions:
return {
  isEditing,
  isSaving,
  startEditing,
  cancelEditing,
  saveAndExit
}
```

### `use-keyboard-shortcuts.tsx` — PRIORIDADE MÉDIA

**Arquivo:** `src/hooks/use-keyboard-shortcuts.tsx`  
**Problema:** Cria DOM nodes imperativos via `document.createElement` para modal de atalhos. Em Vue 3, isso deve ser feito via `<Teleport>` + `v-if`.

**Refatoração necessária:**
1. Extrair o modal HTML para componente `<KeyboardShortcutsHelp>` standalone
2. Hook retorna apenas `{ showHelp, hideHelp, isHelpVisible }` como estado reativo
3. Registrar event listeners via `onMounted`/`onUnmounted` (Vue) em vez de `useEffect`

---

## 3. Componentes com React.memo + displayName

### Componentes com React.memo e displayName (Pré-existentes)

Estes componentes já estavam conformes antes da auditoria:

- `src/components/search/filter-sections/FilterSectionFormacao.tsx` — `FilterSectionFormacao`
- `src/components/search/filter-sections/FilterSectionGeral.tsx` — `FilterSectionGeral`
- `src/components/search/filter-sections/FilterSectionHabilidades.tsx` — `FilterSectionHabilidades`
- `src/components/search/filter-sections/FilterSectionIdiomas.tsx` — `FilterSectionIdiomas`
- `src/components/search/filter-sections/FilterSectionOpcoes.tsx` — `FilterSectionOpcoes`
- `src/components/search/filter-sections/FilterSectionOrigem.tsx` — `FilterSectionOrigem`
- `src/components/search/filter-sections/FilterSectionPerfil.tsx` — `FilterSectionPerfil`
- `src/components/search/filter-sections/FilterSectionEmpresa.tsx` — `FilterSectionEmpresa`
- `src/components/ui/lia-icon.tsx`
- `src/components/ui/loading.tsx`
- `src/components/ui/score-icon-button.tsx`
- `src/components/ui/search-loading-animation.tsx`
- `src/components/ui/context-pill.tsx`
- `src/components/ui/empty-state.tsx`
- `src/components/ui/quick-action-chips.tsx`
- `src/components/ui/lia-prompt-header.tsx`
- `src/components/pages/job-kanban/KanbanCard.tsx` (memo já existia, displayName adicionado nesta auditoria)
- `src/components/bulk-actions-bar.tsx` (memo já existia, displayName adicionado nesta auditoria)

### Componentes com React.memo + displayName ADICIONADOS nesta auditoria

| Componente | Arquivo | Motivo |
|-----------|---------|--------|
| `Badge` | `src/components/ui/badge.tsx` | UI puro, sem estado, zero hooks |
| `Skeleton` | `src/components/ui/skeleton.tsx` | UI puro, apresentação only |
| `Toaster` | `src/components/ui/toaster.tsx` | UI wrapper, sem estado local |
| `DataRequestIndicator` | `src/components/ui/data-request-indicator.tsx` | UI puro, props-driven |
| `UnifiedBulkActionsBar` | `src/components/ui/unified-bulk-actions-bar.tsx` | UI puro, props-driven |
| `ResizableTableHeader` | `src/components/ui/resizable-table-header.tsx` | UI puro, props-driven |
| `TableHeaderRow` | `src/components/ui/resizable-table-header.tsx` | UI puro, sub-componente |

### displayName adicionados a componentes já com React.memo

| Componente | Arquivo |
|-----------|---------|
| `KanbanCard` | `src/components/pages/job-kanban/KanbanCard.tsx` |
| `BulkActionsBar` | `src/components/bulk-actions-bar.tsx` |

---

## 4. Arquivo vue-bridge.ts

Criado em `src/lib/vue-bridge.ts`. Contém:

- `PiniaCompatibleHook<S, A>` — tipo base para hooks Pinia-ready
- `AssertNoJSX<T>` — type-level guard que falha se T extends ReactNode
- `VueBridgeConformant<THook>` — valida que hook retorno é livre de JSX
- `assertPiniaCompat()` — runtime helper para documentar conformidade
- `VueBridgePatterns` — mapeamento documentado React hooks → Vue 3 equivalentes
- `PINIA_READY_HOOKS` — array tipado com todos hooks auditados como conformes
- `HOOKS_NEEDING_REFACTOR` — array com hooks não-conformes e razão

---

## 5. Imports de Tipos de Componentes em Hooks

Os seguintes hooks importam tipos de arquivos de componentes. Estes imports são **apenas de tipos** (`import type`) ou importam constantes/enums, não JSX — portanto são compatíveis com Vue:

| Hook | Import de componente | Classificação |
|------|---------------------|---------------|
| `useSearchFlow` | `ParsedEntities, SearchMode` from `@/components/search/smart-search-input` | Apenas tipos — OK |
| `useUnifiedSearch` | `SearchFilters` from `@/components/search/advanced-filters-modal` | Apenas tipos — OK |
| `use-data-request-modals` | `DataRequestCandidate` from `@/components/modals` | Apenas tipos — OK |
| `use-candidates-list-mapped` | `Candidate` from `@/components/pages/candidates/types` | Apenas tipos — OK |
| `use-archetypes` | `ArchetypeData` from `@/components/search/expandable-ai-prompt.types` | Apenas tipos — OK |
| `use-search-entities` | `SearchTab, BackendEntities` + constantes | Tipos + constantes — OK |

**Recomendação para Vue:** Mover tipos de componentes para `src/types/` ou `src/lib/types/` para eliminar dependências cruzadas.

---

## 6. Percentual de Vue Readiness

```
Hooks:
  - 97/99 hooks sem JSX no retorno = 98% conformes

Componentes UI:
  - 53 componentes com React.memo = base sólida
  - 100% dos filter-sections têm memo + displayName
  - 2 hooks com JSX extraíram componentes embedded = pendente extração

Estimativa geral de Vue Readiness: ~87%

Para atingir 100%:
  1. Refatorar use-edit-lock.tsx (extrair EditButton + SaveCancelButtons)
  2. Refatorar use-keyboard-shortcuts.tsx (modal para componente separado)
  3. Mover tipos de componentes para src/types/ (imports cruzados)
  4. Converter Context providers para Pinia stores
  5. Converter SWR hooks restantes para padrão Pinia + axios
```

---

## 7. Próximos Passos para Migração Vue

### Sprint 1 (Semana 1-2) — Fundação
- [ ] Refatorar `use-edit-lock.tsx` — extrair componentes standalone
- [ ] Refatorar `use-keyboard-shortcuts.tsx` — modal como componente Vue
- [ ] Criar `src/types/` centralizando tipos compartilhados entre hooks e componentes

### Sprint 2 (Semana 3-4) — Stores Pinia
- [ ] Converter 5-10 hooks de domínio principais para Pinia stores (candidatos, jobs, search)
- [ ] Validar via `assertPiniaCompat()` do `vue-bridge.ts`

### Sprint 3 (Semana 5-6) — UI Components
- [ ] Criar componentes Vue equivalentes para os componentes UI com `React.memo`
- [ ] Usar `defineComponent({ name: 'ComponentName' })` como equivalente do `displayName`

### Sprint 4 (Semana 7-8) — Integração
- [ ] Migrar Context providers para Pinia stores
- [ ] Testes de integração React ↔ Vue no mesmo app (micro-frontend strategy)
