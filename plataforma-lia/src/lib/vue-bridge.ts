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
  'use-edit-lock',
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
  // -------------------------------------------------------------------------
  // Hooks que contem JSX real -- precisam ter o JSX extraido para componentes
  // separados antes da migracao Vue/Pinia. Nao converter para .ts ate resolver.
  // -------------------------------------------------------------------------

  // Categoria A: Funcoes que sao componentes React (nao hooks), na pasta errada
  // Acao: Mover para fora de /hooks/ e tratar como componentes legitimos
  "renderHighlightedText",    // buildHighlightedText() retorna <span> JSX -- componente em hooks/ incorretamente
  "SearchScopeControls",      // componente React completo (189L, 30 jsx hits) em hooks/ incorretamente

  // Categoria B: Hooks que retornam JSX inline (toast descriptions, modais, badges)
  // Acao: Extrair o JSX dos retornos para componentes separados
  "useRevealContact",              // JSX em description do toast() -- extrair ToastRevealDescription.tsx
  "useAdvancedFiltersCore",        // 6 jsx hits inline -- extrair para componentes de filtro
  "useSmartSearchCallbacks",       // 6 jsx hits inline -- extrair callbacks de renderizacao
  "useSmartSearchCore",            // 10 jsx hits inline -- extrair SmartSearchResult.tsx
  "useScreeningConfigManagerCore", // 12 jsx hits inline -- extrair ScreeningConfigDisplay.tsx
  "useExpandedChatModalCore",      // 10 jsx hits inline -- extrair ExpandedChatPanels.tsx
  "useCandidatesPageCore",         // 6 jsx hits em orquestrador -- revisar sub-hooks com JSX

  // Categoria C: Hook que retorna React.FC como API publica (legítimo manter .tsx)
  "use-edit-lock",                 // retorna EditButton e SaveCancelButtons como React.FC por design
] as const
// Hooks convertidos de .tsx -> .ts nesta sessao (falsos positivos -- so tinham tipos React):
// useJobsPageCore.ts          (React.ChangeEvent/useState generics, sem JSX real)
// useExpandedChatSubHooks.ts  (React.ChangeEvent<HTMLInputElement>, sem JSX real)
// use-template-suggestions.ts (useState<T> generics, sem JSX real)
// use-keyboard-shortcuts.ts   (innerHTML HTML strings, sem sintaxe JSX)

/**
 * Mapeamento React Context -> Pinia Store
 * Para uso durante a migracao Vue 3 + Nuxt 3
 */
export const CONTEXT_TO_STORE_MAP = {
  // AuthContext -> useAuthStore
  // src/contexts/auth-context.tsx -> stores/auth.ts
  // Estado: user, isAuthenticated, isLoading
  // Actions: login, logout, refreshToken
  AuthContext: "useAuthStore",

  // WizardContext -> useWizardStore
  // src/components/job-wizard/WizardContext.tsx -> stores/wizard.ts
  // Estado: currentStage, basicInfoFields, salaryInfo, detectedCriteria
  // Actions: updateField, nextStage, prevStage, publishJob
  WizardContext: "useWizardStore",

  // ExpandedChatContext -> useExpandedChatStore
  // src/components/expanded-chat/ExpandedChatContext.tsx -> stores/expandedChat.ts
  // Estado: isOpen, messages, currentMode, isLoading
  // Actions: sendMessage, toggleChat, setMode
  ExpandedChatContext: "useExpandedChatStore",

  // LiaFloatContext -> useLiaFloatStore
  // src/contexts/lia-float-context.tsx -> stores/liaFloat.ts
  // Estado: isVisible, position, isMinimized
  // Actions: show, hide, minimize, setPosition
  LiaFloatContext: "useLiaFloatStore",

  // ClientContext -> useClientStore
  // src/contexts/ClientContext.tsx -> stores/client.ts
  // Estado: currentClient, clients, isLoading
  // Actions: selectClient, fetchClients
  ClientContext: "useClientStore",
} as const

/**
 * Mapeamento de 404 rotas proxy -> nitro.devProxy (nuxt.config.ts)
 * As rotas /api/backend-proxy/** e /api/v1/** sao proxies puros
 * que podem ser substituidas por uma unica linha em nuxt.config.ts:
 *
 * devProxy: {
 *   "/api/v1": { target: "http://127.0.0.1:8000", changeOrigin: true },
 *   "/api/backend-proxy": { target: "http://127.0.0.1:8000/api/v1", changeOrigin: true }
 * }
 *
 * Excecoes que requerem logica Vue/Nuxt equivalente:
 * - /api/auth/workos/** -> Nuxt auth module (WorkOS)
 * - /api/lia/chat/stream -> Nuxt server route (SSE streaming)
 */
export const PROXY_MIGRATION_NOTE = "See nitro.devProxy in nuxt.config.ts" as const
