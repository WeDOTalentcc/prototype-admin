# Auditoria de Nomenclatura — Plataforma LIA
**Data:** 2026-03-30

## Padrão definido
- Componentes React: PascalCase (ex: `CandidateCard.tsx`)
- Hooks: kebab-case com prefixo `use-` (ex: `use-candidate-data.ts`)
- Páginas Next.js (app router): kebab-case (ex: `page.tsx` dentro de `candidato/[id]/`)
- Utilitários/libs: kebab-case (ex: `auth-utils.ts`)
- Constantes: UPPER_SNAKE_CASE (ex: `API_BASE_URL`)

## Inconsistências encontradas

### 1. Componentes com PascalCase misturado com kebab-case em `src/components/`
A maioria dos arquivos usa kebab-case, mas 3 usam PascalCase:
- `GoalsPlanningHub.tsx` → padrão correto seria `goals-planning-hub.tsx`
- `PromptContextViewer.tsx` → padrão correto seria `prompt-context-viewer.tsx`
- `PromptSuggestionsPanel.tsx` → padrão correto seria `prompt-suggestions-panel.tsx`

### 2. Hooks em `src/hooks/` com camelCase em vez de kebab-case
O padrão dominante na pasta é kebab-case (`use-candidate-data.ts`), mas 24 arquivos usam camelCase:
- `useAgentMemory.ts` → `use-agent-memory.ts`
- `useCandidateSuggestions.ts` → `use-candidate-suggestions.ts`
- `useChatLayout.ts` → `use-chat-layout.ts`
- `useCompanyBenefits.ts` → `use-company-benefits.ts`
- `useCompanySkillsCatalog.ts` → `use-company-skills-catalog.ts`
- `useCreditEstimator.ts` → `use-credit-estimator.ts`
- `useDynamicSuggestions.ts` → `use-dynamic-suggestions.ts`
- `useFastTrack.ts` → `use-fast-track.ts`
- `useGlobalSearchSettings.ts` → `use-global-search-settings.ts`
- `useHideViewedCandidates.ts` → `use-hide-viewed-candidates.ts`
- `useJobColumnConfig.ts` → `use-job-column-config.ts`
- `useJobFiltersPersistence.ts` → `use-job-filters-persistence.ts`
- `usePromptState.ts` → `use-prompt-state.ts`
- `useScreeningConfig.ts` → `use-screening-config.ts`
- `useSearchFlow.ts` → `use-search-flow.ts`
- `useSemanticSearch.ts` → `use-semantic-search.ts`
- `useSessionRefresh.ts` → `use-session-refresh.ts`
- `useSessionTimeout.ts` → `use-session-timeout.ts`
- `useSettingsForm.ts` → `use-settings-form.ts`
- `useSettingsNavigation.ts` → `use-settings-navigation.ts`
- `useTableFeatures.ts` → `use-table-features.ts`
- `useUIActions.ts` → `use-ui-actions.ts`
- `useUnifiedSearch.ts` → `use-unified-search.ts`
- `useUnsavedChanges.ts` → `use-unsaved-changes.ts`

### 3. Hooks em `src/components/expanded-chat/hooks/` — todos em camelCase
Esta subpasta usa 100% camelCase para hooks (ex: `useExpandedChatEffects.tsx`, `useWSIAndCalibrationHandlers.ts`). É internamente consistente mas diverge do padrão kebab-case do restante do projeto.
- `expandedChatCriteriaExtractor.ts` — não é um hook (sem prefixo `use`), deveria ser `expanded-chat-criteria-extractor.ts`

## CSS morto
Busca por classes `bg-ai-aqua`, `text-electric-red`, `lia-aqua`, `electric-red` em `design-tokens.css` — **nenhuma classe morta encontrada**. O arquivo de tokens está limpo.

## Plano de correção incremental
Renomear gradualmente ao tocar cada arquivo em PRs futuros.
- Ao modificar qualquer arquivo listado acima, incluir o rename no mesmo PR
- Prioridade: começar pelos 3 componentes em `src/components/` (menor impacto)
- Hooks de `src/hooks/` podem ser renomeados em batch por letra do alfabeto
- Hooks de `src/components/expanded-chat/hooks/` — definir padrão consistente para o subdiretório antes de renomear
