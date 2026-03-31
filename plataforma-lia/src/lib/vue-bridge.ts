/**
 * Vue Migration Bridge
 *
 * Patterns que garantem compatibilidade React ↔ Vue 3 + Pinia.
 *
 * Regras:
 * 1. Hooks retornam { state, actions } — nunca JSX
 * 2. Actions retornam Promise<void> ou void — nunca ReactNode
 * 3. State é objeto plano ou primitivo — nunca componente
 * 4. Side effects isolados em useEffect (→ watch em Vue)
 */

// Tipo base para hooks compatíveis com Pinia
export type PiniaCompatibleHook<
  S,
  A extends Record<string, (...args: unknown[]) => unknown>,
> = {
  state: S
  actions: A
}

// Helper para validar que hooks não retornam JSX
// Se T extends React.ReactNode, o tipo resulta em never (erro de compilação)
export type AssertNoJSX<T> = T extends React.ReactNode ? never : T

/**
 * Anotação de conformidade Vue para documentar hooks Pinia-ready.
 *
 * Uso:
 *   const result: VueBridgeConformant<typeof useMyHook> = useMyHook(args)
 *
 * Isso falhará em compilação se o hook retornar JSX ou ReactNode diretamente.
 */
export type VueBridgeConformant<
  THook extends (...args: unknown[]) => unknown,
> = AssertNoJSX<ReturnType<THook>>

// Mapeamento React → Vue para padrões comuns
export const VueBridgePatterns = {
  // useState      → ref()         (Vue 3 Composition API)
  // useEffect     → watch()       (Vue 3 — com cleanup via onUnmounted)
  // useMemo       → computed()    (Vue 3)
  // useCallback   → métodos da store (Pinia actions — sem equivalente direto)
  // Context       → Pinia store   (substituição direta via defineStore)
  // SWR/useQuery  → Pinia + axios (actions assíncronas com estado reativo)
  // React.memo    → shallowRef / defineComponent (otimização de re-render)
  // displayName   → name em defineComponent
} as const

/**
 * Tipo de ação Pinia-compatible.
 * Actions devem retornar Promise<void>, void ou dados serializáveis.
 * NUNCA ReactNode, JSX.Element ou componentes.
 */
export type PiniaAction<TArgs extends unknown[] = unknown[]> = (
  ...args: TArgs
) => Promise<void> | void | Promise<unknown> | unknown

/**
 * Estrutura de estado Pinia-compatible.
 * Estado deve ser serializável: sem funções, sem refs React, sem componentes.
 */
export type PiniaState = Record<
  string,
  | string
  | number
  | boolean
  | null
  | undefined
  | unknown[]
  | Record<string, unknown>
>

/**
 * Valida em tempo de compilação que um objeto de retorno de hook
 * é compatível com o padrão Pinia (sem JSX, sem ReactNode).
 *
 * Exemplo de uso:
 *   export function useMyHook() {
 *     const state = { count: 0, loading: false }
 *     const actions = { increment: () => { state.count++ } }
 *     return assertPiniaCompat({ state, actions })
 *   }
 */
export function assertPiniaCompat<
  S extends PiniaState,
  A extends Record<string, PiniaAction>,
>(hookReturn: { state: S; actions: A }): { state: S; actions: A } {
  return hookReturn
}

/**
 * Lista de hooks auditados como Pinia-ready (sem JSX, sem ReactNode).
 * Atualizar conforme auditoria em docs/vue-migration-bridge.md
 */
export const PINIA_READY_HOOKS = [
  'useAgentMemory',
  'use-agent-streaming',
  'use-ai-consumption',
  'use-ai-credits',
  'use-archetypes',
  'use-bias-audit-report',
  'use-bulk-selection',
  'use-candidate-compare',
  'use-candidate-data-requests',
  'use-candidate-filters',
  'use-candidate-selection',
  'use-candidates-list',
  'use-candidates-list-mapped',
  'use-candidates-search-state',
  'use-candidates-view-state',
  'use-chat-file-handling',
  'use-chat-page-state',
  'use-chat-search',
  'use-clients',
  'use-communication-templates',
  'use-company-culture',
  'use-company-defaults',
  'use-company-eligibility-questions',
  'use-company-lia-instructions',
  'use-company-managers',
  'use-company-tech-stack',
  'use-current-company',
  'use-current-scope',
  'use-daily-briefing',
  'use-data-request-config',
  'use-data-request-modals',
  'use-edit-lock', // AVISO: retorna React.FC no objeto — necessita refatoração (ver docs)
  'use-empty-field-notifications',
  'use-float-conversation',
  'use-float-streaming',
  'use-hiring-policies',
  'use-interpret-context',
  'use-job-analytics',
  'use-job-draft',
  'use-job-report',
  'use-job-wizard-backend',
  'use-lia-suggestions',
  'use-ml-predictions',
  'use-navigation-intent',
  'use-navigation-persistence',
  'use-override-approve',
  'use-pipeline-inheritance',
  'use-proactive-alerts',
  'use-proactive-insights',
  'use-recent-items',
  'use-recruitment-stages',
  'use-return-events',
  'use-saas-metrics',
  'use-scim-config',
  'use-score-breakdown',
  'use-search-autocomplete',
  'use-search-entities',
  'use-search-source',
  'use-short-list',
  'use-similar-profiles',
  'use-sub-status-panel',
  'use-talent-funnel',
  'use-toast',
  'use-transition-context',
  'use-triagem-chat',
  'use-wizard-auto-save',
  'use-wizard-suggestions',
  'use-workforce-planning',
  'use-workos-metrics',
  'use-wsi-async',
  'useActionIntent',
  'useCandidateSuggestions',
  'useChatLayout',
  'useCompanyBenefits',
  'useCompanySkillsCatalog',
  'useCreditEstimator',
  'useDynamicSuggestions',
  'useFastTrack',
  'useGlobalSearchSettings',
  'useHideViewedCandidates',
  'useJobColumnConfig',
  'useJobFiltersPersistence',
  'usePromptState',
  'useScreeningConfig',
  'useSearchFlow',
  'useSemanticSearch',
  'useSessionRefresh',
  'useSessionTimeout',
  'useSettingsForm',
  'useSettingsNavigation',
  'useTableFeatures',
  'useTemplateSuggestions',
  'useUIActions',
  'useUnifiedSearch',
  'useUnsavedChanges',
] as const

/**
 * Hooks que requerem refatoração antes da migração Vue.
 * Razão documentada por hook.
 */
export const HOOKS_NEEDING_REFACTOR = [
  {
    name: 'use-edit-lock',
    file: 'src/hooks/use-edit-lock.tsx',
    reason:
      'Retorna React.FC (EditButton, SaveCancelButtons) como parte do objeto de retorno. ' +
      'Para Vue: extrair EditButton e SaveCancelButtons como componentes standalone, ' +
      'hook retorna apenas { isEditing, isSaving, startEditing, cancelEditing, saveAndExit }.',
  },
  {
    name: 'use-keyboard-shortcuts',
    file: 'src/hooks/use-keyboard-shortcuts.tsx',
    reason:
      'Cria DOM nodes imperativos via document.createElement (modal de ajuda). ' +
      'Para Vue: usar teleport + v-if para o modal de atalhos, hook retorna apenas evento handlers.',
  },
] as const
