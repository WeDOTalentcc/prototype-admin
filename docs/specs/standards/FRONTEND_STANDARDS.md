# Frontend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> **Fonte**: código lido via GitHub API — repositórios `ats_front` (branch `develop`) e `wedo-nuxt` (WeDOTalent)
> Stack: Nuxt 3 + Vue 3 + Vuetify 3 + Pinia + TypeScript + Axios + ActionCable

---

## Dois Repositórios, Dois Papéis

| Repo | Papel | Contém |
|------|-------|--------|
| `ats_front` | **Aplicação de produção** | 901 arquivos: 34 pages, 28 features, 57 composables, 18 stores, 145 components, 11 plugins, 5 layouts |
| `wedo-nuxt` | **Design System LIA v4.1** — biblioteca de componentes | Componentes `Lia*` com stories Histoire, tema Vuetify (`liaTheme`), tokens de design |

O `ats_front` consome os padrões do `wedo-nuxt`. Os componentes base em `ats_front` (prefixo `Base*`) são wrappers Vuetify para a aplicação; os `Lia*` vêm do Design System.

---

## 1. Estrutura de Pastas (`ats_front`)

Lida diretamente do repositório GitHub (branch `develop`):

```
ats_front/
├── pages/                     ← 34 páginas (file-based routing Nuxt 3)
│   ├── index.vue              ← Login
│   ├── user/                  ← Área autenticada do recrutador
│   │   ├── dashboard/
│   │   ├── candidates/
│   │   ├── jobs/[id]/         ← Detalhe + Kanban
│   │   ├── lia/[uid].vue      ← [AI] Chat LIA
│   │   ├── sourcing/[id]/chat.vue ← [AI] Chat de sourcing
│   │   ├── evaluations/
│   │   ├── settings/
│   │   └── admin/             ← 9 páginas admin
│   ├── evaluations/[id]/[uid].vue  ← [AI] Avaliação pública
│   ├── interviews/[account_uid]/[token].vue ← [AI] Entrevista ao vivo
│   ├── scheduling/[account_uid]/[token].vue ← Auto-agendamento
│   └── vagas/[slug]/[account_slug].vue ← Career page pública
│
├── features/                  ← 28 feature modules (358 arquivos)
│   ├── messages/              ← 88 arquivos (templates de comunicação)
│   ├── candidates/            ← 48 (perfil, filtros, emails, educations)
│   ├── lia/                   ← 46 [AI] (chat, sourcing, search, archetypes)
│   ├── admin/                 ← 44 (AI costs, sectors, roles, WhatsApp)
│   ├── jobs/                  ← 38 (form, cards, workflow, screening)
│   ├── applies/               ← 23 (kanban, dialogs, screening results)
│   ├── evaluations/           ← 8
│   ├── activity_logs/         ← 7
│   ├── setups/                ← 6
│   ├── benefits/              ← 5
│   ├── interview/             ← 5
│   ├── prompt/                ← 5
│   ├── questions/             ← 5
│   ├── control_panel/         ← 4
│   ├── selective_process/     ← 4
│   ├── smart-calendar/        ← 4
│   ├── addresses/             ← 3
│   └── ... (11 features menores: feedbacks, languages, skills, etc.)
│
├── components/                ← 145 componentes
│   ├── ui/                    ← 130 componentes UI
│   │   ├── base/              ← BaseButton, BaseInput, BaseSelect, etc. (wrappers Vuetify)
│   │   ├── form/              ← input, select, textarea, phone, currency, color
│   │   ├── table/             ← wrapper, cells (30+ td* cell renderers), headers, sidePanel
│   │   ├── chat/              ← DomainChat, StreamingMessage, ChatCodeBlock, MarkdownTable
│   │   ├── auth/              ← MfaVerification, SsoProviderIcon, layout
│   │   ├── menu/              ← sidebar, menu (com stories)
│   │   ├── adminMenu/         ← settingsSidebar, sidebar
│   │   ├── hub/               ← HubVoiceOverlay (voice commands)
│   │   ├── dialog/            ← confirm, dialog
│   │   ├── tiptap/            ← tiptap (rich text editor), replace_tags
│   │   ├── icon/              ← icon, lucide
│   │   └── ... (badge, button, credits, flow, stepper, etc.)
│   ├── llm/                   ← 8 componentes de LLM/IA
│   │   ├── LlmLimitBanner.vue
│   │   ├── QuotaStatCard.vue
│   │   ├── UsageProgressBar.vue
│   │   └── ... (BreakdownList, GrantExtraDialog, PlanBadge, etc.)
│   ├── shared/                ← IndustrySelect, SkillsAutocomplete
│   ├── sourcing/              ← AutoSourceLoader, ProfileSkeleton, ProgressDetailed
│   └── applies/               ← 1 componente
│
├── composables/               ← 57 composables (hooks reutilizáveis)
│   ├── useCable.ts            ← WebSocket ActionCable (Rails)
│   ├── useMessageStreaming.ts ← [AI] Streaming de chat
│   ├── useFormatter.ts        ← Formatação de datas, moeda
│   ├── useCandidateFilters.ts ← Filtros de candidatos
│   ├── useTalentSearch.ts     ← [AI] Busca de talentos
│   ├── useInterviewSession.ts ← [AI] Sessão de entrevista
│   ├── useHubVoiceCommand.ts  ← [AI] Comandos de voz
│   ├── useSmartCalendar.ts    ← [AI] Calendário inteligente
│   └── ... (49 mais: auth, audio, clipboard, etc.)
│
├── stores/                    ← 18 Pinia stores
│   ├── user.ts                ← Dados do usuário logado
│   ├── lia.ts                 ← Estado do chat LIA
│   ├── hub.ts                 ← Hub de navegação
│   ├── kanbanSelection.ts     ← Seleções do kanban
│   ├── ui.ts                  ← Estado da UI (expansion panels)
│   ├── table.ts               ← Estado das tabelas
│   ├── searchCredits.ts       ← Créditos de busca
│   └── ... (11 mais: benefit, chatSync, confirm, dialog, etc.)
│
├── plugins/                   ← 11 plugins Nuxt
│   ├── axios.ts               ← Cliente HTTP (baseURL de runtimeConfig)
│   ├── api.ts                 ← $fetch wrapper com auth automática
│   ├── vuetify.ts             ← Vuetify 3 (importa config/vuetify.config.ts)
│   ├── websocket.client.ts    ← WebSocket setup
│   ├── toast.client.ts        ← Vue Toastification
│   ├── vue-flow.ts            ← Vue Flow (diagramas de workflow)
│   ├── vue-tel-input.client.ts ← Input de telefone
│   ├── vue-the-mask.client.ts  ← Máscaras de input
│   ├── auto-animate.client.ts  ← Auto-animate
│   ├── register-table-cells.ts ← Registro de cell renderers
│   └── suppress-logs.client.ts ← Supressão de logs
│
├── layouts/                   ← 5 layouts
│   ├── user.vue               ← Layout principal (Sidebar + Menu + Splitpanes)
│   ├── admin.vue              ← Layout admin
│   ├── blank.vue              ← Sem navegação
│   ├── evaluations.vue        ← Layout de avaliação
│   └── setup.vue              ← Layout de setup
│
├── types/                     ← 7 arquivos de tipos
│   ├── actioncable.d.ts
│   ├── communication-template.ts
│   ├── execution-tracking.ts
│   ├── interview.ts
│   ├── llm-quota.ts
│   ├── sector.ts
│   └── smart-calendar.ts
│
├── config/
│   └── vuetify.config.ts      ← Temas light/dark + componentDefaults
├── constants/
│   └── vagas.js               ← Constantes de vagas
├── middleware/
│   └── microsoft-auth.ts      ← Guard de auth Microsoft
├── src/
│   └── assets/style.css       ← Estilos globais
├── nuxt.config.ts             ← Configuração Nuxt
├── histoire.config.ts         ← Configuração Histoire
└── package.json
```

---

## 2. Como Criar um Componente Novo

### 2.1 Componentes base (`components/ui/base/`) — wrapper Vuetify

O `ats_front` usa componentes `Base*` que são wrappers tipados sobre Vuetify:

```vue
<!-- components/ui/base/BaseButton.vue — extraído de ats_front/components/ui/base/BaseButton.vue -->
<template>
  <v-btn
    :variant="vuetifyVariant"
    :color="vuetifyColor"
    :size="vuetifySize"
    :disabled="disabled"
    :loading="loading"
    :block="block"
    :icon="iconOnly"
    :class="buttonClasses"
    v-bind="$attrs"
    @click="$emit('click', $event)"
  >
    <template v-if="$slots.prepend && !iconOnly" #prepend>
      <slot name="prepend" />
    </template>
    <slot />
    <template v-if="$slots.append && !iconOnly" #append>
      <slot name="append" />
    </template>
  </v-btn>
</template>

<script setup lang="ts">
  import { computed } from 'vue'

  export interface Props {
    variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
    size?: 'xs' | 'sm' | 'md' | 'lg'
    disabled?: boolean
    loading?: boolean
    block?: boolean
    iconOnly?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
    block: false,
    iconOnly: false,
  })
</script>
```

**Componentes base disponíveis (13):**

| Componente | Wraps | Story |
|-----------|-------|-------|
| `BaseButton` | `v-btn` | ✅ |
| `BaseInput` | `v-text-field` | ✅ |
| `BaseSelect` | `v-select` | ✅ |
| `BaseAutocomplete` | `v-autocomplete` | ✅ |
| `BaseTextarea` | `v-textarea` | — |
| `BaseChip` | `v-chip` | ✅ |
| `BaseAvatar` | `v-avatar` | ✅ |
| `BaseCard` | `v-card` | — |
| `BaseDialog` | `v-dialog` | — |
| `BaseLabel` | label tipado | ✅ |
| `BaseMenu` | `v-menu` | — |
| `BaseSwitch` | `v-switch` | — |
| `BaseTabs` / `BaseTabsWindow` | `v-tabs` | ✅ |

### 2.2 Componentes do Design System (`wedo-nuxt`) — prefixo `Lia*`

Componentes do Design System (reutilizáveis): prefixo `Lia` obrigatório → `LiaField`, `LiaTabBar`.
Componentes de domínio/página: sem prefixo, PascalCase → `DadosDaEmpresa`, `Departamentos`.

**Estrutura obrigatória:**
```
1. <template>
2. <script setup lang="ts">
3. <style scoped>
```

**Regras:**
- Todo `Lia*.vue` tem `.story.vue` correspondente
- Props: `withDefaults(defineProps<{...}>(), {...})`
- Emits: `defineEmits<{...}>()`
- CSS: BEM com tokens Vuetify (`rgb(var(--v-theme-*))`)

---

## 3. Feature Modules — Convenção de Pastas

Cada feature em `features/` segue uma organização por domínio:

```
features/candidates/
├── overview.vue              ← Componente principal (lista/overview)
├── form.vue                  ← Formulário de criação/edição
├── form.story.vue            ← Story Histoire
├── preview.vue               ← Preview inline
├── skills.vue                ← Sub-feature
├── curriculum_text.vue       ← Sub-feature
├── lia_assessment.vue        ← [AI] Análise IA
├── new_candidate_dialog.vue  ← Dialog
├── cards/                    ← Cards de seção (layout, educations, experiences, etc.)
├── educations/               ← Sub-domínio (form + list)
├── experiences/              ← Sub-domínio (form + list)
├── email/                    ← Sub-domínio de comunicação
├── files/                    ← Upload de arquivos
└── filters/                  ← Painel de filtros (tipos + seções)
    ├── CandidateFiltersPanel.vue
    ├── FilterChipsBar.vue
    ├── types.ts
    └── sections/             ← Filtros individuais (10 filtros)
```

**Padrões observados:**
- `cards/` — cards de detalhe (usados em página de visualização)
- `form/` — sub-formulários (steps de formulário complexo)
- `workflow/` — steps de workflow (ex: `features/jobs/workflow/`)
- Dialogs: sufixo `_dialog.vue` ou `Dialog.vue`
- Listas: `list.vue` ou `index.vue`
- Formulários: `form.vue`

---

## 4. Gerenciamento de Estado

### 4.1 Pinia — Options Store (padrão real do `ats_front`)

O `ats_front` usa **Options Store** (não Setup Store):

```typescript
// stores/user.ts — extraído de ats_front (simplificado)
import { defineStore } from "pinia";

export const useUserStore = defineStore("user", {
  state: () => ({
    id: null,
    name: null,
    email: null,
    account_id: null,
    role: null,
    is_admin: false,
    is_super_admin: false,
    microsoft_connected: false,
    business_name: null,
    business_logo: null,
    sourcing_config: null,
  }),

  getters: {
    getUser: (state) => state,
  },

  actions: {
    setUser(user: any) {
      this.id = user.id;
      this.name = user.name;
      // ... (mapeia todos os campos)
    },
    resetUser() {
      this.id = null;
      // ... (reseta todos os campos)
    },
  },
});
```

**18 stores disponíveis:**

| Store | Arquivo | Responsabilidade |
|-------|---------|------------------|
| `useUserStore` | `stores/user.ts` | Dados do usuário logado |
| `useLiaStore` | `stores/lia.ts` | Estado do chat LIA (messageTrigger) |
| `useHubStore` | `stores/hub.ts` | Hub de navegação |
| `useUiStore` | `stores/ui.ts` | Estado da UI (expansion containers) |
| `useUiContextStore` | `stores/uiContext.ts` | Contexto de UI |
| `useTableStore` | `stores/table.ts` | Estado das tabelas |
| `useTableSidePanelsStore` | `stores/table_side_panels.ts` | Side panels das tabelas |
| `useKanbanSelectionStore` | `stores/kanbanSelection.ts` | Seleções do kanban |
| `useConfirmStore` | `stores/confirm.ts` | Dialog de confirmação |
| `useDialogStore` | `stores/dialog.ts` | Estado de dialogs |
| `useChatSyncStore` | `stores/chatSync.ts` | Sincronização de chat |
| `useSearchCreditsStore` | `stores/searchCredits.ts` | Créditos de busca |
| `useSourcingFiltersStore` | `stores/sourcingFilters.ts` | Filtros de sourcing |
| `useBenefitStore` | `stores/benefit.ts` | Benefícios |
| `useCandidateFeedbacksStore` | `stores/candidate_feedbacks.ts` | Feedbacks de candidatos |
| `useLiaGlobalAudioTriggerStore` | `stores/liaGlobalAudioTrigger.ts` | [AI] Trigger de áudio global |
| `useSelectiveProcessesStore` | `stores/selective_processes.ts` | Processos seletivos |
| `useWorkspacesStore` | `stores/workspaces.ts` | Workspaces |

### 4.2 Estado local com `ref`

Use `ref` para estado que pertence **somente** ao componente (loading, drag, toggle):

```vue
<script setup lang="ts">
const isDragging = ref(false)
const isLoading = ref(false)
</script>
```

---

## 5. Formulários e Validação

### 5.1 Biblioteca: Vuelidate (NÃO VeeValidate/Zod)

O `ats_front` usa **Vuelidate v2** para validação (`@vuelidate/core` ^2.0.3 + `@vuelidate/validators` ^2.0.4). Não há VeeValidate nem Zod no projeto.

### 5.2 Validators centralizados — `composables/useValidators.ts`

```typescript
// composables/useValidators.ts — extraído de ats_front (completo)
import { required, email, minLength, maxLength, helpers } from '@vuelidate/validators'

export const validators = {
  required: helpers.withMessage('Campo obrigatório', required),
  email: helpers.withMessage('Email inválido', email),
  minLength: (min: number) => helpers.withMessage(`Mínimo ${min} caracteres`, minLength(min)),
  maxLength: (max: number) => helpers.withMessage(`Máximo ${max} caracteres`, maxLength(max)),
}
```

### 5.3 Uso em componentes

```vue
<script setup lang="ts">
import { useVuelidate } from '@vuelidate/core'
import { validators } from '~/composables/useValidators'

const state = reactive({ name: '', email: '' })
const rules = {
  name: { required: validators.required },
  email: { required: validators.required, email: validators.email },
}
const v$ = useVuelidate(rules, state)

const submit = async () => {
  const valid = await v$.value.$validate()
  if (!valid) return
  // proceed with API call
}
</script>
```

### 5.4 Componentes de formulário (`components/ui/form/`)

Formulários usam wrappers UI específicos (não Base*):

| Componente | Função |
|-----------|--------|
| `form/input.vue` | Text input com label + validação |
| `form/select.vue` | Select com label |
| `form/textarea.vue` | Textarea com label |
| `form/autocomplete.vue` | Autocomplete com label |
| `form/phone.vue` | Input de telefone (vue-tel-input) |
| `form/currency.vue` | Input de moeda |
| `form/color.vue` | Color picker |
| `form/checkbox.vue` | Checkbox |
| `form/radio.vue` | Radio buttons |
| `form/switch.vue` | Switch |
| `form/avatar.vue` | Upload de avatar |
| `form/user_autocomplete.vue` | Autocomplete de usuários |

### 5.5 Formulários multi-step

Formulários complexos são organizados em sub-componentes dentro de `form/`:

```
features/jobs/form/
├── index.vue          ← Container com stepper
├── general.vue        ← Step 1: dados gerais
├── description.vue    ← Step 2: descrição
├── people.vue         ← Step 3: responsáveis
├── remuneration.vue   ← Step 4: remuneração
├── questions.vue      ← Step 5: perguntas
├── screening.vue      ← Step 6: [AI] triagem IA
├── selective_processes.vue ← Step 7: processos seletivos
├── menu.vue           ← Menu lateral do form
└── NewSkillDialog.vue ← Dialog auxiliar
```

---

## 6. Chamadas de API

### 6.1 Dois clientes HTTP

O `ats_front` tem **dois** clientes HTTP registrados como plugins:

**Plugin `axios.ts`** — Axios com interceptor de auth:
```typescript
// plugins/axios.ts — extraído de ats_front (simplificado)
const api = axios.create({ baseURL: config.public.apiBase })
api.interceptors.request.use(config => {
  const token = useCookie('auth_token');
  if (token.value) {
    config.headers.Authorization = `Bearer ${token.value}`
  }
  return config
})
// Uso: const { $axios } = useNuxtApp()
```

**Plugin `api.ts`** — `$fetch` wrapper nativo Nuxt:
```typescript
// plugins/api.ts — extraído de ats_front (simplificado)
const fetcher = $fetch.create({
  baseURL,
  async onRequest({ options }) {
    const token = useCookie('auth_token');
    if (token.value) {
      options.headers = { ...options.headers, Authorization: `Bearer ${token.value}` };
    }
  },
  async onResponseError({ response }) {
    if (response?.status === 401) { /* redirect/logout */ }
  },
});
const api = {
  get: <T>(url, options = {}) => fetcher<T>(url, { method: 'GET', ...options }),
  post: <T>(url, body = {}, options = {}) => fetcher<T>(url, { method: 'POST', body, ...options }),
  put: <T>(url, body = {}, options = {}) => fetcher<T>(url, { method: 'PUT', body, ...options }),
  patch: <T>(url, body = {}, options = {}) => fetcher<T>(url, { method: 'PATCH', body, ...options }),
  delete: <T>(url, options = {}) => fetcher<T>(url, { method: 'DELETE', ...options }),
};
// Uso: const { $api } = useNuxtApp()
```

### 6.2 Composables de domínio

Chamadas de API ficam em composables, nunca direto no componente:

```typescript
// composables/useTalentSearch.ts, useSmartCalendar.ts, etc.
```

### 6.3 WebSocket — ActionCable (Rails)

```typescript
// composables/useCable.ts — extraído de ats_front (simplificado)
import { createConsumer } from '@rails/actioncable'

export default function useCable(token, entity = null, account_uid = null) {
  const config = useRuntimeConfig()
  const base = config.public?.websocketUrl || 'ws://localhost:8080/cable'
  const consumer = createConsumer(base)

  const subscribeToChannel = (channelName, params, callback, options) => {
    return consumer.subscriptions.create({
      channel: channelName,
      auth_token: token,
      ...(entity && { entity }),
      ...(account_uid && { account_uid }),
      ...params
    }, {
      connected() { /* reconnect logic */ },
      received(data) { callback(data) },
      disconnected() { /* mark disconnected */ },
    })
  }
  return { subscribeToChannel, disconnect: () => consumer.disconnect() }
}
```

### 6.4 Streaming de chat IA

```typescript
// composables/useMessageStreaming.ts — detecta blocks (text, table, list)
// e renderiza progressivamente com interval-based character streaming
export function useMessageStreaming() {
  const streamingContent = ref('')
  const streamingBlocks = ref<StreamingBlock[]>([])
  const isStreaming = ref(false)

  const startStreaming = (fullContent: string, speed: number = 20) => { ... }
  const stopStreaming = () => { ... }
  return { streamingContent, streamingBlocks, isStreaming, startStreaming, stopStreaming }
}
```

---

## 6. Autenticação

**Token:** JWT via cookie `auth_token` (não localStorage).
**Interceptor:** Ambos plugins (axios e api) adicionam `Authorization: Bearer <token>` automaticamente.
**Middleware:** `middleware/microsoft-auth.ts` para auth Microsoft.
**WorkOS:** SSO callback em `pages/workos-callback.vue`.

---

## 7. Configuração Vuetify

### 7.1 Nuxt Config

```typescript
// nuxt.config.ts — extraído de ats_front (simplificado)
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_BASE_URL || 'http://localhost:8080',
      websocketUrl: process.env.NUXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080/cable',
      interviewAiWsUrl: process.env.INTERVIEW_AI_WS_URL || 'ws://localhost:8001',
      interviewAiHttpUrl: process.env.INTERVIEW_AI_HTTP_URL || 'http://localhost:8001',
    },
  },
  css: ['vuetify/styles', '@mdi/font/css/materialdesignicons.css'],
  modules: ['@pinia/nuxt'],
  build: { transpile: ['vuetify', 'vue-toastification'] },
})
```

### 7.2 Tema: `lightTheme` / `darkTheme` — de `config/vuetify.config.ts`

```typescript
// config/vuetify.config.ts — extraído de ats_front (cores principais mostradas)
export const lightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    // SURFACE
    background: '#f9fafb',
    'on-background': '#111827',
    surface: '#ffffff',
    'on-surface': '#111827',
    'surface-variant': '#F3F4F6',

    // PRIMARY — Gray 900 (botões primários são PRETOS)
    primary: '#111827',
    'on-primary': '#ffffff',

    // SECONDARY
    secondary: '#E5E7EB',
    'on-secondary': '#374151',

    // TEXT CUSTOM
    heading: '#111827',
    body: '#1F2937',
    'body-light': '#4B5563',
    'body-lighter': '#6B7280',
    'body-disabled': '#9CA3AF',

    // WEDO ACCENT (10% da interface)
    'wedo-cyan': '#60BED1',
    'wedo-green': '#5DA47A',
    'wedo-orange': '#D19960',
    'wedo-purple': '#9860D1',
    'wedo-magenta': '#D160AB',

    // SEMANTIC
    error: '#EF4444',
    warning: '#F59E0B',
    info: '#3B82F6',
    success: '#22C55E',
  },
}

export const darkTheme: ThemeDefinition = {
  dark: true,
  colors: {
    background: '#1A1D1F',
    surface: '#0F1113',
    primary: '#F9FAFB',
    'on-primary': '#111827',
    // ... (inversão completa)
  },
}
```

### 7.3 Component Defaults

```typescript
// config/vuetify.config.ts — componentDefaults
export const componentDefaults = {
  VBtn:       { rounded: '12px', class: 'font-weight-medium wedo-label text-none' },
  VTextField: { rounded: '12px', density: 'compact' },
  VSelect:    { density: 'compact', menuProps: { offset: 4 } },
  VCombobox:  { density: 'compact', menuProps: { offset: 4 } },
  VList:      { density: 'compact' },
  VListItem:  { class: 'wedo-label', density: 'compact' },
  VTabs:      { density: 'compact' },
}
```

### 7.4 Plugin Vuetify — manual component import

O `ats_front` NÃO usa auto-import de componentes Vuetify. Cada componente é importado manualmente em `plugins/vuetify.ts` (~60 componentes).

### 7.5 Vuetify no `wedo-nuxt` (Design System)

O `wedo-nuxt` usa `vuetify-nuxt-module` com `liaTheme` e `liaDefaults` definidos em `app/vuetify-options.ts` + SASS overrides em `assets/scss/settings.scss`.

---

## 8. Layout Principal

O layout `user.vue` (171 linhas) organiza a interface do recrutador:

```
┌─────────────────────────────────────────────────────┐
│  Sidebar (componente)                               │
├─────────────────────────────────────────────────────┤
│  Menu (top bar) ──────────────────── @logout        │
├─────────────────────────────────────────────────────┤
│  LlmLimitBanner (quando quota atingida)             │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────┬──────────────────────┐    │
│  │  Splitpanes (70%)    │  Expansion Pane (30%)│    │
│  │  <slot /> (conteúdo) │  (side panel)        │    │
│  │                      │  Dinâmico via store  │    │
│  └──────────────────────┴──────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  HubVoiceOverlay (floating, voice commands)         │
│  FAB de acesso rápido (create job, etc.)            │
└─────────────────────────────────────────────────────┘
```

**Splitpanes:** Usa `splitpanes` para divisão redimensionável. O expansion pane é controlado via `useUiStore().showExpansionContainer`.

---

## 9. Tabela Dinâmica — Sistema de Cell Renderers

O `ats_front` tem um sistema sofisticado de tabela com 30+ cell renderers:

**Wrapper:** `components/ui/table/wrapper.vue` — tabela configurável por dados.
**Headers:** `thText`, `thDate`, `thRange`, `thScore` — headers tipados.
**Cells (30+):**

| Cell Renderer | Função |
|---------------|--------|
| `tdText` | Texto simples |
| `tdDate` | Data formatada |
| `tdCurrency` | Valor monetário |
| `tdAvatar` | Avatar circular |
| `tdAvatarWithName` | Avatar + nome |
| `tdBoolean` | Checkbox/switch |
| `tdColor` | Color swatch |
| `tdEnum` | Badge por enum |
| `tdLink` / `tdInternalLink` | Link externo/interno |
| `tdScore` / `tdIaScore` | Score numérico / [AI] Score IA |
| `tdMatchScore` | [AI] Score de match |
| `tdJobStatus` | Status da vaga (badge) |
| `tdApplyEvaluation` | [AI] Avaliação do candidato |
| `tdScreeningScript` | [AI] Script de triagem |
| `tdSourceBadge` | Badge de origem |
| `tdSourcedProfileStatus` | Status de perfil sourced |
| `tdDynamicSelect` | Select inline editável |
| `tdDynamicText` | Texto editável inline |
| `tdDynamicSwitch` | Switch editável inline |
| `tdDynamicAutocomplete` | Autocomplete editável |
| ... | (30+ total) |

**Registro:** `plugins/register-table-cells.ts` registra todos globalmente.

---

## 10. Componentes de Chat IA

O chat com LIA usa componentes dedicados em `components/ui/chat/`:

| Componente | Função |
|-----------|--------|
| `DomainChat.vue` | Container principal do chat por domínio |
| `StreamingMessage.vue` | Mensagem com streaming progressivo |
| `MessageContent.vue` | Renderização de conteúdo (markdown, tables) |
| `MarkdownTable.vue` | Tabela extraída de markdown |
| `ChatCodeBlock.vue` | Bloco de código com syntax highlighting |
| `ChatDocumentCard.vue` | Card de documento anexado |
| `ChatImageViewer.vue` | Visualizador de imagens |
| `ChatLinkPreview.vue` | Preview de links |
| `ChatVoiceMessage.vue` | Mensagem de voz |
| `SkillsChart.vue` | [AI] Gráfico de skills |

---

## 11. Composables — Padrões Extraídos

### 11.1 Composables de AI (14):

| Composable | Função |
|-----------|--------|
| `useMessageStreaming` | Streaming de chat com detecção de blocks |
| `useHubVoiceCommand` | [AI] Comandos de voz via hub |
| `useInterviewSession` | [AI] Sessão de entrevista |
| `useInterviewAudio` | [AI] Áudio da entrevista |
| `useInterviewCall` | [AI] Chamada de entrevista |
| `useEvaluationVoiceSession` | [AI] Sessão de voz de avaliação |
| `useEvaluationSending` | [AI] Envio de avaliação |
| `useTalentSearch` | [AI] Busca de talentos |
| `useSimilarCandidates` | [AI] Candidatos similares |
| `useCandidateMatches` | [AI] Matches de candidatos |
| `useCurriculumParser` | [AI] Parser de currículo |
| `useScoringDisplay` | [AI] Display de scoring |
| `useAutoSource` | [AI] Auto-sourcing |
| `useSmartCalendar` | [AI] Calendário inteligente |

### 11.2 Composables de Infraestrutura (14):

| Composable | Função |
|-----------|--------|
| `useCable` | WebSocket ActionCable |
| `useFormatter` | Formatação (datas, moeda, etc.) |
| `useClipboard` | Clipboard API |
| `useColumnResize` | Redimensionamento de colunas |
| `useConfirm` | Dialog de confirmação |
| `useCustomTheme` | Troca de tema light/dark |
| `useExpansion` | Controle de expansion panels |
| `useActiveSection` | Seção ativa (scroll spy) |
| `useValidators` | Validadores de formulário |
| `useTextFormatting` | Formatação de texto |
| `useHubNavigation` | Navegação do hub |
| `useExecutionTracking` | Rastreamento de execução |
| `useConfirmationSound` | Som de confirmação |
| `useSessionTimer` | Timer de sessão |

### 11.3 Composables de Domínio (29):

Incluem `useAppliesImport`, `useApplyCollectionChannel`, `useArchetypes`, `useAudioMessages`, `useAudioPlayer`, `useAudioRecorder`, `useCandidateFilters`, `useCommunicationTemplates`, `useContactEnrichment`, `useCreateJobModal`, `useCreditWebSocket`, `useDomainMessageChannel`, `useDomainMessages`, `useIndustries`, `useJobDuplication`, `useLanguages`, `useLiaDomainConfig`, `useLlmQuota`, `useLlmUsages`, `useMicrosoftAuth`, `useSearchCredits`, `useSectors`, `useSelectiveProcessTriggers`, `useSkills`, `useSourcedProfiles`, `useSourcingWebSocket`, `useSourcings`, `useVoiceRecorder`, `useWorkOSAuth`.

---

## 12. Naming Conventions

| Item | Convenção | Exemplo |
|------|-----------|---------|
| Páginas | kebab-case (file-based Nuxt) | `pages/user/dashboard/index.vue` |
| Componentes UI base | PascalCase com prefixo `Base` | `BaseButton.vue`, `BaseInput.vue` |
| Componentes DS | PascalCase com prefixo `Lia` | `LiaField.vue`, `LiaTabBar.vue` |
| Componentes de feature | PascalCase sem prefixo | `CreateJobModal.vue`, `FilterChipsBar.vue` |
| Composables | camelCase com prefixo `use` | `useCable.ts`, `useFormatter.ts` |
| Stores | camelCase com prefixo `use...Store` | `useUserStore`, `useLiaStore` |
| Cell renderers | camelCase com prefixo `td` | `tdScore.vue`, `tdAvatar.vue` |
| Dialogs | sufixo `_dialog.vue` ou `Dialog.vue` | `confirm_dialog.vue`, `BaseDialog.vue` |
| Stories | sufixo `.story.vue` | `form.story.vue`, `BaseButton.story.vue` |
| Types | camelCase ou kebab-case `.ts` | `llm-quota.ts`, `interview.ts` |

---

## 13. Padrões de Estilo

### 13.1 CSS: scoped + Vuetify theme vars

```vue
<style scoped>
.my-component {
  color: rgb(var(--v-theme-on-background));
  background: rgb(var(--v-theme-surface));
}
</style>
```

### 13.2 Classe utilitária `wedo-label`

Aplicada globalmente via `componentDefaults` nos botões e list items. Define a tipografia padrão.

### 13.3 Ícones: Material Design Icons (`@mdi/font`)

O `ats_front` usa MDI como icon set principal (importado via CSS em `nuxt.config.ts`). Componente `Icon` customizado em `components/ui/icon/`.

### 13.4 Transições obrigatórias

Toda interação visual deve ter `transition` definida (0.15s–0.3s ease).

---

## 14. Testes e Stories

- **Histoire** como Storybook equivalente (`histoire.config.ts`, `histoire.setup.ts`)
- Stories em `.story.vue` no mesmo diretório do componente
- Componentes base e form têm stories; features nem sempre

---

## Checklist de PR — componente frontend

- [ ] `<script setup lang="ts">` — nunca Options API
- [ ] Props com `withDefaults(defineProps<{...}>(), {...})` tipadas
- [ ] Emits com `defineEmits<{...}>()` tipados
- [ ] CSS em `<style scoped>` — cores via `rgb(var(--v-theme-*))`, nunca hex para cores de tema
- [ ] Story `.story.vue` criada (obrigatório para componentes base/DS)
- [ ] Loading, empty state e error state cobertos
- [ ] Transições CSS em interações
- [ ] API calls em composables, nunca direto no componente

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| nuxt.config.ts | `ats_front/nuxt.config.ts` |
| Vuetify config (temas + defaults) | `ats_front/config/vuetify.config.ts` |
| Plugin axios | `ats_front/plugins/axios.ts` |
| Plugin api ($fetch) | `ats_front/plugins/api.ts` |
| Plugin vuetify | `ats_front/plugins/vuetify.ts` |
| WebSocket composable | `ats_front/composables/useCable.ts` |
| Streaming composable | `ats_front/composables/useMessageStreaming.ts` |
| Layout principal | `ats_front/layouts/user.vue` |
| Design System doc | `wedo-nuxt/docs/00-design-system-v4.md` |
| Vuetify options (wedo-nuxt) | `wedo-nuxt/app/vuetify-options.ts` |

> **Fonte**: Código extraído via GitHub API dos repositórios `ats_front` (branch `develop`, 901 arquivos) e `wedo-nuxt` no GitHub WeDOTalent. Trechos marcados como "(simplificado)" mostram a estrutura essencial; consulte os arquivos originais para o código completo.
