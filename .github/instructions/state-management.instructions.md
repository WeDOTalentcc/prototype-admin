---
applyTo: "plataforma-lia/src/stores/**/*.ts"
---

# State Management — WeDO Talent

Quatro lugares possíveis para estado. Escolha o **mais fraco** que resolve o problema.

## Árvore de decisão

```
É dado que vem do backend?
  └─ SIM → SWR (server state). Ver `data-fetching.instructions.md`.
  └─ NÃO → É estado de UI?
             └─ SIM → É compartilhado entre rotas/páginas não-aninhadas?
                        └─ SIM → Zustand store
                        └─ NÃO → É filtro/busca que deve persistir no reload?
                                   └─ SIM → searchParams (URL) ou Zustand `persist`
                                   └─ NÃO → useState local
             └─ NÃO → Context (DI estática: provider de tema, auth)
```

| Situação | Solução |
|---|---|
| Lista de vagas vinda do backend | **SWR** (`useJobs`) |
| Filtros de busca na página Vagas | **Zustand persist** (`useJobFiltersStore`) |
| Tab ativa de um modal | **useState local** |
| Tab ativa que deve persistir no reload | **searchParams** |
| Usuário autenticado global | **Zustand** (`useAuthStore`) |
| Tema (dark/light) | **Context** (next-themes) |
| Idioma atual | **Context** (next-intl provider) |
| Form state | **React Hook Form** (ver forms-and-validation) |
| Seleção em bulk (checkboxes) | **useState local** ou Zustand se durar entre rotas |

> ⚠️ Há stores Zustand no projeto (`candidates-store`, `triagem-store`) que guardam **dados do backend** — isso é anti-padrão (cache duplicado com o SWR). Não copie; migrar quando tocar.

## Zustand — padrão canônico

Os stores vivem em `src/stores/`. **Um store = um domínio**. Sempre use `devtools`; use `persist` só quando o estado deve sobreviver ao reload (filtros salvos, preferências de UI).

### Estrutura

```ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface JobFiltersState {
  selectedStatus: string
  searchTerm: string
  advancedFilters: Record<string, string[]>
}

interface JobFiltersActions {
  setFiltersState: (state: JobFiltersState) => void
  updateFilter: <K extends keyof JobFiltersState>(key: K, value: JobFiltersState[K]) => void
  clearAllFilters: () => void
  hasActiveFilters: () => boolean
}

export type JobFiltersStore = JobFiltersState & JobFiltersActions

function createDefaultState(): JobFiltersState {
  return {
    selectedStatus: 'todas',
    searchTerm: '',
    advancedFilters: {},
  }
}

export const useJobFiltersStore = create<JobFiltersStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...createDefaultState(),

        setFiltersState: (state) =>
          set(state, false, 'jobFilters/setFiltersState'),

        updateFilter: (key, value) =>
          set(
            (s) => ({ ...s, [key]: value }),
            false,
            'jobFilters/updateFilter',
          ),

        clearAllFilters: () =>
          set(createDefaultState(), false, 'jobFilters/clearAllFilters'),

        hasActiveFilters: () => {
          const s = get()
          return s.selectedStatus !== 'todas' || s.searchTerm.trim().length > 0
        },
      }),
      { name: 'wedotalent_job_filters' },  // chave localStorage
    ),
    { name: 'JobFiltersStore' },  // nome no Redux DevTools
  ),
)
```

### Regras estruturais

- **`interface State` + `interface Actions` separadas**. Type do store é `State & Actions`. Portável para Pinia.
- **Função de default**: `createDefaultState()` — usada em init e em `clearAll`. Evita mutação de objeto congelado.
- **Action naming**: `'domain/action'` (ex. `'jobFilters/updateFilter'`) — aparece no Redux DevTools.
- **Actions retornam `void`** por padrão. Se precisar valor (`saveCurrentSearch` retornando o novo id), documente.
- **`set` imutável**: sempre `(s) => ({ ...s, ... })`, nunca `s.foo = x`.
- **`get()` nas actions** para ler estado atual.
- **Computed values**: via função em Actions (`hasActiveFilters: () => boolean`). Não use `selectors` separados.

### Persist

Use `persist` só quando justificado:

- ✅ Filtros salvos (usuário espera reencontrar).
- ✅ Preferências de UI (sidebar aberta/fechada, tema).
- ❌ Seleção efêmera (marcações em bulk).
- ❌ Dado de backend.

Sempre prefixe a key com `wedotalent_` para evitar colisão e facilitar migração (`wedotalent_job_filters`, `wedotalent_ui_prefs`).

Se quebrar shape do estado, versione via `version` + `migrate`:

```ts
persist(impl, {
  name: 'wedotalent_job_filters',
  version: 2,
  migrate: (persistedState, version) => {
    if (version === 1) {
      // migração de v1 → v2
      return { ...(persistedState as object), newField: 'default' }
    }
    return persistedState as JobFiltersStore
  },
})
```

## Consumindo stores

**Sempre seletor** — nunca desestruture o store inteiro:

```tsx
// ✅ seletor — só re-renderiza quando o slice muda
const searchTerm = useJobFiltersStore((s) => s.searchTerm)
const updateFilter = useJobFiltersStore((s) => s.updateFilter)

// ❌ re-renderiza a cada mudança de qualquer campo
const { searchTerm, updateFilter } = useJobFiltersStore()
```

Quando precisar de múltiplos campos, use `useShallow` (já no projeto via Zustand 5):

```tsx
import { useShallow } from 'zustand/react/shallow'

const { searchTerm, selectedStatus } = useJobFiltersStore(
  useShallow((s) => ({ searchTerm: s.searchTerm, selectedStatus: s.selectedStatus })),
)
```

## Export via `src/stores/index.ts`

Adicione barrel export dos novos stores:

```ts
// ✅ src/stores/index.ts
export { useJobFiltersStore, type JobFiltersStore } from './job-filters-store'
```

## Reset entre sessões

O `useAuthStore` expõe `registerStoreReset(cb)` — stores que guardam dados do usuário devem registrar seu reset:

```ts
// ✅ em qualquer store com dados que devem sumir no logout
import { registerStoreReset } from './auth-store'

export const useCandidatesUIStore = create<...>()(
  devtools(
    (set) => ({ ... }),
    { name: 'CandidatesUIStore' },
  ),
)

registerStoreReset(() => useCandidatesUIStore.setState(createDefaultState()))
```

## Context — só DI estática

**Não crie Context para estado mutável.** Use Zustand. Context só para:

- Provider de tema (`next-themes`).
- Provider de i18n (`next-intl`).
- Auth provider que lê do Zustand e expõe init effects (`AuthContext`).
- Canal/servicing provider que não muda (SDK do Microsoft Teams).

Se o valor do Context muda muitas vezes, **todos** os consumidores re-renderizam. Isso é bug esperando para acontecer.

```tsx
// ❌ Context para state mutável
const JobsContext = createContext<{ jobs: Job[]; setJobs: (j: Job[]) => void }>(...)

// ✅ Zustand
useJobsStore((s) => s.jobs)
```

## useState local — é OK

Não estigmatize `useState`. Para estado que **não precisa** sair do componente, é a resposta certa.

```tsx
// ✅
const [isOpen, setIsOpen] = useState(false)
const [activeTab, setActiveTab] = useState<'screening' | 'pipeline'>('screening')
```

Se o mesmo bloco de `useState` se repete em 3+ componentes, extraia para um hook `src/hooks/<feature>/use-*-state.ts`.

## URL state (searchParams)

Estado que **deve ser compartilhável por link ou sobreviver ao reload** vai para `searchParams`:

- Filtros de listagem (`?status=open&page=2`)
- Tab ativa (`?tab=pipeline`)
- Modal aberto (`?modal=create-job`)

```tsx
'use client'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'

const searchParams = useSearchParams()
const router = useRouter()
const pathname = usePathname()

const status = searchParams.get('status') ?? 'open'

const setStatus = (next: string) => {
  const qs = new URLSearchParams(searchParams)
  qs.set('status', next)
  router.replace(`${pathname}?${qs}`)
}
```

Quando também precisa de persist entre rotas não-aninhadas ou lógica complexa, migre para Zustand — mas **deixe a URL como source de verdade** para estado bookmarkable.

## Rules

- **Escolha o mais fraco que resolve**: useState > URL > Zustand > Context.
- **`interface State` + `interface Actions`** separadas.
- **`devtools` sempre**; `persist` só quando justificado.
- **Action naming `'domain/action'`**.
- **Seletores obrigatórios** no consumo — nunca desestruture store inteiro.
- **`useShallow` para múltiplos campos**.
- **`createDefaultState()` helper** para init/reset.
- **`set` imutável** — spread, nunca mutação direta.
- **`registerStoreReset`** em stores com dado de usuário.
- **Context só DI estática** (tema, i18n, auth init).
- **Sem server state em Zustand** — é SWR.
- **Key `persist` prefixada `wedotalent_`**.
