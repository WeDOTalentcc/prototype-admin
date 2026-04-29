---
name: vue-migration-prep
description: Preparação estrutural de código React+Tailwind para futura migração Vue.js+Vuetify+Nuxt. Use ao criar ou refatorar componentes para garantir que a estrutura, naming e padrões facilitam a conversão. Cobre separação de concerns, prop patterns, state management, naming conventions e anti-patterns React-only.
---

# Vue Migration Prep — Preparação Estrutural para Migração

Garante que código React+Tailwind está estruturado para facilitar futura conversão para Vue.js + Vuetify + Nuxt. Não muda a stack atual — apenas organiza o código para que a migração seja mecânica.

> **Stack atual:** React (.tsx) + Tailwind CSS + shadcn/ui
> **Stack futura:** Vue 3 + Vuetify 3 + Nuxt 3 + Pinia
> **DS oficial:** `plataforma-lia/docs/design-system/00-design-system-v4.md` (inclui Vuetify mapping)

## Quando ativar

- Ao criar componente React (`.tsx`) novo no `plataforma-lia` (a estrutura precisa nascer portável)
- Ao refatorar componente React existente, especialmente os que serão migrados em breve
- Ao criar hook, store, slice ou serviço de frontend (separação lógica/template para vir Composition API)
- Quando o usuário disser "prepara pra migração Vue", "deixa portável", "evita React-only" ou "usa só padrão que dá pra converter"
- Ao escrever prop interface de componente novo (preferir interface explícita sobre `React.FC`)
- Ao introduzir state management novo (preferir padrão portável a Pinia ao invés de hooks React-only)
- Como parte do fluxo padrão: após implementar feature, antes de `feature-audit`
- Ao revisar componente existente para portabilidade ("isso vai dar pra converter pro Vue?")

## Quando NÃO ativar

- Componente já é Vue/Vuetify no `recruiter_agent_v5` -> usar `vue-vuetify-standardize`
- Padronização visual ao DS v4.2.1 em React -> usar `design-standardize`
- Lógica de pattern de composição (factory, observer, strategy) -> usar `design-patterns`
- Bug pontual sem refactor estrutural -> usar `canonical-fix`

## Caminhos de Conversão

A migração acontece por **dois caminhos** — a skill prepara para ambos:

| Caminho | Fluxo | O que importa |
|---------|-------|---------------|
| **Figma** | Captura tela → Figma → ajusta → Antegraphy/similar → gera Vue | Fidelidade visual DS v4.2.1, componentes consistentes |
| **Código direto** | Cursor/VSCode SSH → prompts de conversão → gera Vue | Estrutura de código, separação lógica/template, props tipadas |

---

## PRINCÍPIO 1: Separação de Concerns

Vue separa `<template>`, `<script>` e `<style>`. Preparar essa separação no React:

**Fazer:** Lógica em hook dedicado (`use-*.ts`), componente é só template + binding.

```tsx
// hooks/use-candidate-filter.ts (→ composables/useCandidateFilter.ts em Vue)
export function useCandidateFilter(jobId: string) {
  const [filters, setFilters] = useState<FilterState>(defaultFilters)
  const applyFilter = useCallback((f: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...f }))
  }, [])
  return { filters, applyFilter }
}

// CandidateFilter.tsx (→ CandidateFilter.vue)
export function CandidateFilter({ jobId }: Props) {
  const { filters, applyFilter } = useCandidateFilter(jobId)
  return <FilterBar filters={filters} onChange={applyFilter} />
}
```

**Evitar:** Lógica misturada com template (30+ linhas de useEffect/useMemo inline).

**Checklist:**
- [ ] Lógica complexa em hook separado (`use-*.ts`)
- [ ] Componente .tsx = import hook + JSX + event binding
- [ ] Side effects no hook, não no componente

---

## PRINCÍPIO 2: Props e Events (Input/Output)

**Fazer:** Props tipadas com `interface`, callbacks `on*`.

```tsx
interface CandidateCardProps {
  candidate: Candidate
  isSelected: boolean
  onSelect: (id: string) => void      // → @select em Vue
  onMove: (id: string, stage: string) => void  // → @move em Vue
}
```

**Checklist:**
- [ ] Props tipadas com `interface` (não `type` inline)
- [ ] Callbacks `on*` (onSelect → @select em Vue)
- [ ] Sem Context para dados que podem ser props
- [ ] Props readonly

---

## PRINCÍPIO 3: Composição (Slots)

**Fazer:** `children` e named props para composição.

```tsx
function Card({ children, header, footer }: {
  children: React.ReactNode       // → <slot> default
  header?: React.ReactNode        // → <slot name="header">
  footer?: React.ReactNode        // → <slot name="footer">
}) { ... }
```

**Checklist:** Sem render props complexas. Preferir composição declarativa.

---

## PRINCÍPIO 4: State Management (Pinia-Compatible)

**Fazer:** Hooks globais `use*Store` com interfaces State/Actions explícitas.

```tsx
interface PipelineState { stages: Stage[]; selectedId: string | null }
interface PipelineActions { move: (id: string, to: string) => Promise<void> }
export function usePipelineStore(): PipelineState & PipelineActions { ... }
```

**Checklist:** `use*Store` → Pinia. `useMemo` → `computed`. `useState` → `ref`.

---

## PRINCÍPIO 5: Estilização

**Fazer:** Usar helpers de tokens (`getButtonClasses`, etc.) em vez de classes Tailwind hardcoded.

**Checklist:** Evitar `@apply`. Classes condicionais via `cn()` ou ternary simples.

---

## PRINCÍPIO 6: Anti-Patterns a Evitar

| Pattern React | Problema para Vue | Alternativa |
|---|---|---|
| `React.Children.map` / `cloneElement` | Não existe em Vue | Slots nomeados |
| `useContext` para tudo | Vue usa provide/inject | Props ou Pinia |
| `forwardRef` / `useImperativeHandle` | Não existe em Vue | Props + emit |
| `dangerouslySetInnerHTML` | Vue usa `v-html` | Isolar em componente |
| HOC | Vue usa composables | Extrair para hook |
| Render props complexas | Vue slots simples | Usar slots pattern |
| CSS-in-JS (styled-components) | Incompatível Vuetify | Tailwind + tokens |

---

## MAPEAMENTO COMPLETO: React → Vue

### Reactivity

| React | Vue 3 (Composition API) | Notas |
|-------|------------------------|-------|
| `useState(value)` | `ref(value)` | `.value` para acessar em Vue |
| `useState({...})` | `reactive({...})` | Sem `.value`, proxy direto |
| `useMemo(() => x, [deps])` | `computed(() => x)` | Auto-track deps em Vue |
| `useCallback(fn, [deps])` | `fn` (função normal) | Vue não precisa memoizar funções |
| `useEffect(() => {}, [dep])` | `watch(dep, () => {})` | Mais explícito em Vue |
| `useEffect(() => {}, [])` | `onMounted(() => {})` | Lifecycle hook |
| `useEffect(() => () => cleanup)` | `onUnmounted(() => cleanup)` | Lifecycle hook |
| `useRef(value)` | `ref(value)` | Mesmo API, diferente uso |
| `useReducer(reducer, init)` | `reactive({...}) + methods` | Pinia para complexo |

### Components

| React | Vue 3 | Notas |
|-------|-------|-------|
| `function Component(props)` | `<script setup> + defineProps` | — |
| `interface Props { x: string }` | `defineProps<{ x: string }>()` | — |
| `props.children` | `<slot />` | — |
| `props.header` (ReactNode) | `<slot name="header" />` | — |
| `onClick={handler}` | `@click="handler"` | — |
| `onChange={handler}` | `@update:modelValue` ou `@change` | v-model para inputs |
| `className={cn(...)}` | `:class="[...]"` | Array syntax |
| `style={{ color: 'red' }}` | `:style="{ color: 'red' }"` | Idêntico |
| `{condition && <div>}` | `<div v-if="condition">` | — |
| `{items.map(i => <X key={i.id}/>)}` | `<X v-for="i in items" :key="i.id"/>` | — |
| `<>...</>` (Fragment) | `<template>...</template>` | — |

### State Management

| React (hook) | Vue/Pinia | Notas |
|------|-----------|-------|
| `useContext(AuthCtx)` | `useAuthStore()` (Pinia) | — |
| `createContext()` | `defineStore()` | Pinia store |
| `Provider value={...}` | `app.use(pinia)` | Global |
| `useReducer + dispatch` | `store.action()` | Pinia action |

### Tailwind → Vuetify

| Tailwind (React) | Vuetify 3 | Notas |
|-------------------|-----------|-------|
| `<button className={getButtonClasses('primary')}>` | `<v-btn color="grey-darken-4">` | — |
| `<input className={getInputClasses()}>` | `<v-text-field variant="outlined">` | — |
| `<div className={getCardClasses()}>` | `<v-card variant="outlined">` | — |
| `getBadgeClasses('success')` | `<v-chip color="success" size="small">` | — |
| `flex items-center gap-2` | `d-flex align-center ga-2` | — |
| `grid grid-cols-12 gap-6` | `<v-row><v-col cols="...">` | — |
| `p-4` | `pa-4` | — |
| `px-6 py-4` | `px-6 py-4` | Idêntico |
| `rounded-md shadow-sm` | `rounded="md" elevation="1"` | — |
| `text-sm text-gray-600` | `text-body-2 text-grey-darken-1` | — |
| `animate-spin` | `<v-progress-circular indeterminate>` | — |
| `animate-pulse` (skeleton) | `<v-skeleton-loader>` | — |
| Modal (custom div) | `<v-dialog>` | — |
| Dropdown (custom div) | `<v-menu> + <v-list>` | — |
| Tabs (custom div) | `<v-tabs> + <v-tab>` | — |
| Accordion | `<v-expansion-panels>` | — |
| Toggle/Switch | `<v-switch color="grey-darken-4">` | — |
| Pagination | `<v-pagination color="grey-darken-4">` | — |
| Tooltip | `<v-tooltip>` | — |
| Toast | `<v-snackbar>` | — |
| Avatar | `<v-avatar>` | — |
| Progress bar | `<v-progress-linear>` | — |

### Mapeamento Completo: shadcn/ui → Vuetify 3

Referência completa com props, variantes e exemplos em `docs/specs/frontend/COMPONENT_EQUIVALENCES.md`.

#### Quick Reference — Top 25 Componentes

| shadcn/ui | Vuetify 3 | Props-chave |
|-----------|-----------|-------------|
| `<Button variant size>` | `<v-btn color variant size>` | variant: flat/outlined/text; size: small/default/large |
| `<Badge variant>` | `<v-chip size="small" color variant>` | variant: tonal/outlined; color: success/error/warning/info |
| `<Card>` + subcomps | `<v-card>` + subcomps | variant="outlined" rounded="md" |
| `<Input>` | `<v-text-field variant="outlined">` | density="compact" para menor |
| `<Textarea>` | `<v-textarea variant="outlined">` | — |
| `<Dialog>` + subcomps | `<v-dialog>` + `<v-card>` | activator slot para trigger |
| `<AlertDialog>` | `<v-dialog persistent>` | persistent impede fechar fora |
| `<Select>` + subcomps | `<v-select :items>` | items como array de objetos |
| `<Tabs>` + subcomps | `<v-tabs>` + `<v-tabs-window>` | v-model para tab ativa |
| `<Table>` + subcomps | `<v-data-table :headers :items>` | slots #item.col para custom |
| `<Avatar>` + subcomps | `<v-avatar :image size>` | size numérico em px |
| `<Switch>` | `<v-switch color="grey-darken-4">` | v-model para estado |
| `<Checkbox>` | `<v-checkbox>` | v-model para estado |
| `<RadioGroup>` + Item | `<v-radio-group>` + `<v-radio>` | v-model para valor |
| `<DropdownMenu>` + subcomps | `<v-menu>` + `<v-list>` | activator slot |
| `<Tooltip>` + subcomps | `<v-tooltip text>` | activator slot |
| `<Popover>` + subcomps | `<v-menu>` | activator slot |
| `<Progress value>` | `<v-progress-linear :model-value>` | color para cor |
| `<Skeleton>` | `<v-skeleton-loader :type>` | type: text/heading/card/avatar |
| `<Sheet side>` | `<v-navigation-drawer temporary :location>` | location: right/left/top/bottom |
| `<Accordion>` + subcomps | `<v-expansion-panels>` + panel | multiple prop |
| `<Slider>` | `<v-slider>` | v-model, min, max, step |
| `<Label>` | prop `label` do input | Integrado nos campos Vuetify |
| `<ScrollArea>` | CSS `overflow-auto` | Nativo |
| `<Separator>` | `<v-divider>` | vertical prop |

#### Variantes Button — Mapeamento Detalhado

| shadcn variant | Vuetify variant + color |
|---|---|
| `default` / `primary` | `variant="flat" color="grey-darken-4"` |
| `destructive` | `variant="flat" color="error"` |
| `outline` | `variant="outlined"` |
| `secondary` | `variant="flat" color="grey-lighten-4"` |
| `ghost` | `variant="text"` |
| `link` | `variant="text" :ripple="false"` + underline class |

#### Variantes Badge — Mapeamento Detalhado

| shadcn variant | Vuetify chip props |
|---|---|
| `default` | `color="grey-lighten-4"` |
| `secondary` | `color="grey-lighten-3"` |
| `destructive` / `danger` | `color="error" variant="tonal"` |
| `outline` | `variant="outlined"` |
| `success` | `color="success" variant="tonal"` |
| `warning` | `color="warning" variant="tonal"` |
| `info` | `color="info" variant="tonal"` |
| `lilac` | `color="purple" variant="tonal"` |

#### Componentes Custom LIA (sem equivalente Vuetify)

13 componentes proprietários que precisam ser recriados como Vue components:

| Componente | Estratégia Vue | Complexidade |
|---|---|---|
| `lia-icon` | `LiaIcon.vue` — SVG/CSS puro | Baixa |
| `empty-state` | `<v-empty-state>` (Labs) ou custom | Baixa |
| `context-pill` | `<v-chip closable>` customizado | Baixa |
| `quick-action-chips` | `<v-chip-group>` | Baixa |
| `audio-record-button` | Custom + composable `useAudioRecorder` | Alta |
| `file-upload-button` | `<v-file-input>` + custom drag&drop | Média |
| `loading` | `<v-overlay>` + `<v-progress-circular>` | Baixa |
| `status-badge` (602L) | Custom `StatusBadge.vue` + `statusMappings.ts` | Alta |
| `command-palette` | Custom — `<v-dialog>` + search + list | Alta |
| `prompt-suggestions-dock` | Custom — específico LIA | Alta |
| `search-loading-animation` | CSS animation puro | Baixa |
| `data-request-indicator` | `<v-progress-linear>` + status text | Média |
| `setup-alert-badge` | `<v-alert>` + `<v-badge>` | Média |

### Transitions CSS → Vuetify

| CSS LIA | Vuetify | Uso |
|---------|---------|-----|
| `fadeIn 150ms` | `<v-fade-transition>` | Entrada/saída |
| `slideInFromBottom 200ms` | `<v-slide-y-transition>` | Modais, menus |
| `slideInFromRight 300ms` | `<v-slide-x-reverse-transition>` | Painéis laterais |
| `scale 150ms` | `<v-scale-transition>` | FABs, tooltips |
| `expandFromTop 200ms` | `<v-expand-transition>` | Acordeões |

---

## PROMPTS DE CONVERSÃO

Prompts prontos para usar no Cursor/VSCode para converter componentes React → Vue:

### Prompt 1: Componente Simples (Botão, Card, Badge)

```
Converta este componente React+Tailwind para Vue 3 + Vuetify 3 + TypeScript.
Regras:
1. Use <script setup lang="ts"> com defineProps e defineEmits
2. Substitua className por Vuetify components (v-btn, v-card, v-chip, etc.)
3. Use a paleta monocromática LIA: color="grey-darken-4" para primary
4. Cyan (#60BED1) APENAS em elementos LIA (brain icon, badges LIA)
5. Open Sans como font padrão, Inter para dados numéricos
6. Mantenha dark mode (Vuetify theme handles it)
7. Mantenha acessibilidade (aria-labels, roles)
```

### Prompt 2: Formulário com Validação

```
Converta este formulário React para Vue 3 + Vuetify 3.
Regras:
1. Use v-form com ref para validação
2. Converta inputs para v-text-field, v-select, v-textarea
3. Converta regras de validação para formato Vuetify: (v) => !!v || 'Obrigatório'
4. Use v-model para two-way binding
5. Labels como prop do v-text-field (não separadas)
6. variant="outlined" para inputs
7. Botões: v-btn color="grey-darken-4" para submit
8. Mantenha estados de erro inline
```

### Prompt 3: Page Layout com Sidebar

```
Converta este layout React para Nuxt 3 + Vuetify 3.
Regras:
1. Use v-app, v-navigation-drawer, v-main, v-app-bar
2. Sidebar com v-list e v-list-item
3. Brain icon em cyan (#60BED1) no logo
4. v-navigation-drawer permanent width="256"
5. Navegação com NuxtLink e useRoute()
6. Open Sans em toda a navegação
7. color="grey-darken-4" para item ativo
```

### Prompt 4: Tabela de Dados

```
Converta esta tabela React para Vue 3 + Vuetify 3.
Regras:
1. Use v-data-table com :headers e :items
2. Slots personalizados para badges/status (#item.status)
3. Inter para dados numéricos (font-family: 'Inter')
4. v-chip para badges de status
5. Sorting e pagination integrados do Vuetify
6. Hover row via item-class
```

### Prompt 5: Hook → Composable

```
Converta este React hook para Vue 3 composable.
Regras:
1. useState → ref() ou reactive()
2. useMemo → computed()
3. useCallback → função normal
4. useEffect com deps → watch()
5. useEffect sem deps → onMounted()
6. Retornar refs diretamente (Vue auto-unwraps em template)
7. Exportar como função useXxx()
8. Tipo de retorno explícito
```

### Prompt 6: Store (Context → Pinia)

```
Converta este React Context+Provider para Pinia store.
Regras:
1. Use defineStore('name', () => { ... })
2. State com ref() (= useState)
3. Getters com computed() (= useMemo)
4. Actions como funções async
5. Exportar hook useXxxStore()
6. Não precisa de Provider wrapper
```

---

## TEMPLATE Vue 3 + Vuetify 3 Padrão

Todo componente convertido deve seguir esta estrutura:

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDesignTokens } from '@/composables/useDesignTokens'
import type { Candidate } from '@/types/candidate'

interface Props {
  candidate: Candidate
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
})

const emit = defineEmits<{
  select: [id: string]
  move: [id: string, stage: string]
}>()

const { colors } = useDesignTokens()

const displayName = computed(() =>
  `${props.candidate.firstName} ${props.candidate.lastName}`
)

function handleSelect() {
  emit('select', props.candidate.id)
}
</script>

<template>
  <v-card
    variant="outlined"
    rounded="md"
    :class="{ 'border-2 border-grey-darken-4': isSelected }"
    @click="handleSelect"
  >
    <v-card-title class="text-body-1 font-weight-bold">
      {{ displayName }}
    </v-card-title>
    <v-card-text>
      <v-chip
        size="small"
        :color="candidate.status === 'active' ? 'success' : 'grey'"
        variant="outlined"
      >
        {{ candidate.status }}
      </v-chip>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="grey-darken-4"
        variant="flat"
        size="small"
        @click.stop="emit('move', candidate.id, 'interview')"
      >
        Avançar
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.v-card {
  font-family: 'Open Sans', sans-serif;
}
</style>
```

---

## CONVENÇÕES ENFORÇADAS PARA MIGRAÇÃO

### Regra 1: Props Interface (não type inline)

```tsx
// CORRETO — mapeia para defineProps<Props>()
interface StatusBadgeProps {
  status: CandidateStatus
  size?: 'sm' | 'md' | 'lg'
  onStatusChange?: (status: CandidateStatus) => void
}

// EVITAR — difícil converter automaticamente
type Props = { status: string; size?: string }
```

### Regra 2: Callbacks on* (drop "on" → emit name)

```tsx
// React: onSelect, onMove, onStatusChange
// Vue:   @select,  @move,  @status-change
```

### Regra 3: Composição Slot-Ready

```tsx
// CORRETO (mapeia para slots Vue)
function Panel({ children, header, footer, actions }: {
  children: React.ReactNode      // → <slot />
  header?: React.ReactNode       // → <slot name="header">
  footer?: React.ReactNode       // → <slot name="footer">
  actions?: React.ReactNode      // → <slot name="actions">
}) { ... }

// EVITAR (render props não mapeiam para slots)
function Panel({ renderHeader }: {
  renderHeader: (data: PanelData) => React.ReactNode
}) { ... }
```

### Regra 4: Extrair Lógica em Hook

Componentes com >150 linhas devem ter lógica em hook separado:
- `use-candidate-filter.ts` → `composables/useCandidateFilter.ts`
- `use-pipeline-state.ts` → `composables/usePipelineState.ts`

### Regra 5: CVA → Vuetify Props

Ao criar variantes com CVA, documentar o mapeamento Vuetify equivalente em comentário:

```tsx
const buttonVariants = cva("...", {
  variants: {
    variant: {
      default: "...",    // Vuetify: variant="flat" color="grey-darken-4"
      destructive: "...", // Vuetify: variant="flat" color="error"
      outline: "...",     // Vuetify: variant="outlined"
    }
  }
})
```

### Regra 6: Evitar asChild/Slot Pattern do Radix

O pattern `asChild` com `<Slot>` do Radix não existe em Vue. Preferir composição direta:

```tsx
// EVITAR (Radix Slot pattern)
<DialogTrigger asChild><Button>Open</Button></DialogTrigger>

// Em Vue será:
// <template v-slot:activator="{ props }">
//   <v-btn v-bind="props">Open</v-btn>
// </template>
```

---

## VALIDAÇÃO

```bash
# 1. Anti-patterns React-only:
grep -rn "cloneElement\|Children.map\|useImperativeHandle\|forwardRef\|dangerouslySetInnerHTML\|styled-components" [ARQUIVOS] --include="*.tsx" --include="*.ts"

# 2. Context excessivo:
grep -rn "useContext\|createContext" [ARQUIVOS] --include="*.tsx" --include="*.ts"

# 3. Componentes grandes (>150 linhas = precisa extrair hook):
wc -l [ARQUIVOS]/*.tsx | sort -rn | head -10

# 4. Helpers de tokens:
grep -rn "getButtonClasses\|getCardClasses\|getInputClasses\|getBadgeClasses" [ARQUIVOS] --include="*.tsx"

# 5. Props tipadas:
grep -rn "interface.*Props" [ARQUIVOS] --include="*.tsx"

# 6. Callbacks on*:
grep -rn "on[A-Z].*:" [ARQUIVOS] --include="*.tsx" | head -20

# 7. Stores:
grep -rn "use.*Store" [ARQUIVOS] --include="*.ts" --include="*.tsx"
```

---

## DIAGNÓSTICO DE PORTABILIDADE

Rodar script: `.agents/skills/vue-migration-prep/vue-migration-diagnostic.sh`

O script gera relatório com:
- Score geral de portabilidade (%)
- Score por caminho (Figma visual vs código direto)
- Categorização por arquivo (100%/90%/70%/50% portável)
- Lista de arquivos críticos (precisam refatorar)
- Lista de arquivos migration-ready (copiar direto)
- Ações específicas para aumentar %

### Nível de Portabilidade por Tipo

| Tipo | Portabilidade | Ação |
|------|--------------|------|
| `types.ts`, `constants.ts` | 100% Direto | Copiar |
| `utils/*.ts` (funções puras) | 100% Direto | Copiar |
| `hooks/use-*.ts` | 90% Adaptação | → composables, ajustar reactivity |
| `stores/use-*-store.ts` | 80% Adaptação | → Pinia defineStore |
| `components/*.tsx` (pequenos) | 70% Adaptação | JSX → template |
| `components/*.tsx` (complexos) | 50% Reconstruir | Separar lógica, converter |
| `design-tokens.ts` | Mapear | → Vuetify theme config |
| `*.css` com `@apply` | Reconstruir | Vuetify não suporta |

---

## Formato de Relatório

```
## Migration Prep — [Nome]

### Score Geral: XX% portável

### Por Caminho
- Via Figma (visual): XX% (DS v4.2.1 conformante)
- Via Código (direto): XX% aproveitável

### Arquivos Analisados
- src/components/X.tsx (120 linhas) — 70% portável
- src/hooks/use-x.ts (45 linhas) — 90% portável

### Conformidade
- Separação lógica/template: ✅
- Props tipadas (interface): ✅
- Callbacks on*: ✅ (4 callbacks)
- Anti-patterns: ✅ zero
- Design tokens: ⚠️ 3 classes hardcoded
- Context usage: ✅ apenas AuthContext

### Ações para Aumentar %
- [ ] Extrair lógica do componente X para hook (+10%)
- [ ] Trocar 3 classes hardcoded por helpers (+5%)
- [ ] Renomear callbacks para padrão on* (+2%)
```

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/vue-migration-prep` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/vue-migration-prep.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/vue-migration-prep/SKILL.md` |

**Quando ativar:**
- Ao criar ou refatorar qualquer componente React (`.tsx`)
- Ao criar hooks, stores ou serviços de frontend
- Como parte do fluxo padrão: após implementar, antes de `/feature-audit`
- Ao verificar portabilidade de código existente para migração futura
