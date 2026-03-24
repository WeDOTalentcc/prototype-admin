# Frontend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> Stack: Vue 3 + Nuxt 3 + Vuetify 3 (`wedo-nuxt` / `ats_front`)
> Baseado no código real do repositório `wedo-nuxt` e `plataforma-lia`.

---

## 1. Estrutura de Pastas

```
wedo-nuxt/                         ← Design System (biblioteca de componentes)
├── app/
│   ├── assets/
│   │   └── icons/                 ← SVGs inline do DS (brain-tree.svg, upload.svg...)
│   ├── components/                ← Componentes Lia* + stories (.story.vue)
│   │   ├── LiaField.vue
│   │   ├── LiaField.story.vue     ← preview Histoire do componente
│   │   ├── LiaTabBar.vue
│   │   └── ...
│   ├── app.vue                    ← Root app
│   └── vuetify-options.ts         ← liaTheme + liaDefaults (importado pelo config)
├── assets/scss/
│   ├── settings.scss              ← Override SASS vars do Vuetify (antes do CSS)
│   └── global.scss                ← Overrides globais de componentes Vuetify
├── docs/
│   └── 00-design-system-v4.md    ← Documentação canônica do DS
├── nuxt.config.ts                 ← Configuração Nuxt (modules, css, vuetify)
└── vuetify.config.ts              ← Ponto de entrada Vuetify (usa vuetify-options.ts)

ats_front/                         ← Frontend de produção (estrutura de features)
├── features/                      ← Módulos por domínio (~25 features)
│   ├── candidates/
│   ├── jobs/
│   └── pipeline/
├── composables/                   ← Composables reutilizáveis (~37)
├── stores/                        ← Pinia stores (~16)
└── pages/                         ← Roteamento file-based (Nuxt)
```

**Regra:** todo arquivo de componente tem um `.story.vue` correspondente no mesmo diretório.

---

## 2. Como Criar um Componente Novo

### Passo a passo obrigatório

**1. Decidir onde vive o componente:**
- Componente do Design System (reutilizável na plataforma toda) → `wedo-nuxt/app/components/Lia*.vue`
- Componente de feature específica → `ats_front/features/{feature}/components/`

**2. Criar o arquivo com nomenclatura correta:**
```
LiaNovoComponente.vue         ← PascalCase, prefixo Lia obrigatório
LiaNovoComponente.story.vue   ← Story Histoire no mesmo diretório
```

**3. Estrutura mínima do arquivo:**

```vue
<!-- LiaNovoComponente.vue -->
<template>
    <div class="lia-novo-componente" :class="{ 'lia-novo-componente--active': isActive }">
        <!-- Seção principal -->
        <div class="lia-novo-componente__header">
            <span class="lia-novo-componente__title">{{ title }}</span>
        </div>

        <!-- Slot para conteúdo dinâmico -->
        <div class="lia-novo-componente__body">
            <slot />
        </div>
    </div>
</template>

<script setup lang="ts">
// 1. Interfaces exportadas (se outros arquivos precisarem)
export interface NovoComponenteItem {
    id: string
    label: string
}

// 2. Props com tipos e JSDoc
withDefaults(defineProps<{
    /** Título exibido no header */
    title: string
    /** Controla estado ativo */
    isActive?: boolean
    /** Lista de itens renderizados */
    items?: NovoComponenteItem[]
}>(), {
    isActive: false,
    items: () => [],
})

// 3. Emits tipados
defineEmits<{
    /** Dispara quando o usuário seleciona um item */
    (e: 'select', item: NovoComponenteItem): void
    /** Dispara ao fechar o componente */
    (e: 'close'): void
}>()

// 4. Estado reativo (apenas o necessário)
// 5. Computed (derivado do estado/props)
// 6. Métodos
</script>

<style scoped>
/* ── Bloco raiz ── */
.lia-novo-componente {
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-radius: 8px;
    border: 1px solid #E5E7EB;
    background: rgb(var(--v-theme-surface));
    padding: 12px;
}

/* ── Elementos (__) ── */
.lia-novo-componente__header {
    display: flex;
    align-items: center;
    gap: 8px;
}

.lia-novo-componente__title {
    font-family: 'Open Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: rgb(var(--v-theme-on-surface));
}

/* ── Modificadores (--) ── */
.lia-novo-componente--active {
    border-color: rgb(var(--v-theme-primary));
}
</style>
```

**4. Criar a story Histoire:**

```vue
<!-- LiaNovoComponente.story.vue -->
<script setup lang="ts">
import LiaNovoComponente from './LiaNovoComponente.vue'
</script>

<template>
    <Story title="LIA / NovoComponente">
        <Variant title="Default">
            <LiaNovoComponente title="Título de exemplo" />
        </Variant>

        <Variant title="Active">
            <LiaNovoComponente title="Ativo" :is-active="true" />
        </Variant>
    </Story>
</template>
```

**O que NÃO fazer:**
```vue
<!-- ❌ ERRADO — Options API -->
<script>
export default {
    props: { title: String },
    data() { return { count: 0 } }
}
</script>

<!-- ❌ ERRADO — sem lang="ts" -->
<script setup>
defineProps({ title: String })   <!-- sem tipagem TypeScript -->
</script>

<!-- ❌ ERRADO — nome sem prefixo Lia e sem PascalCase -->
<!-- campo-formulario.vue, formField.vue, field.vue -->
```

---

## 3. Gerenciamento de Estado

### 3.1 Quando usar estado local (`ref` / `reactive`)

Use `ref` para estado que pertence **somente** ao componente e não precisa ser compartilhado:

```vue
<script setup lang="ts">
import { ref } from 'vue'

// ✅ Estado local: isDragging é relevante apenas neste componente
const isDragging = ref(false)

function onDrop(event: DragEvent) {
    isDragging.value = false
    // processar arquivo...
}
</script>
```

**Use estado local quando:** loading de um botão, toggle de modal, valor temporário de input, estado de drag-and-drop.

### 3.2 Quando usar Pinia

Use Pinia quando o estado precisa ser **compartilhado entre rotas ou componentes sem relação de pai-filho**:

```typescript
// stores/jobStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useJobStore = defineStore('job', () => {
    // State
    const jobs = ref<Job[]>([])
    const selectedJobId = ref<string | null>(null)
    const isLoading = ref(false)

    // Getters (computed)
    const selectedJob = computed(() =>
        jobs.value.find(j => j.id === selectedJobId.value) ?? null
    )

    // Actions
    async function fetchJobs() {
        isLoading.value = true
        try {
            jobs.value = await useJobApi().getAll()
        } finally {
            isLoading.value = false
        }
    }

    return { jobs, selectedJobId, selectedJob, isLoading, fetchJobs }
})
```

**Use Pinia quando:** dados do usuário logado, lista de vagas usada em múltiplas telas, configurações globais, carrinho/seleção persistida entre navegações.

**O que NÃO fazer:**
```typescript
// ❌ ERRADO — Vuex (não usar, projeto usa Pinia)
// ❌ ERRADO — provide/inject para dados globais de negócio
// ❌ ERRADO — props drilling por mais de 2 níveis (usar store)
// ❌ ERRADO — localStorage diretamente sem store (não rastreável)
```

---

## 4. Chamadas de API

### 4.1 Padrão: composable dedicado por recurso

```typescript
// composables/useJobApi.ts
export function useJobApi() {
    const baseUrl = '/api/backend-proxy'   // sempre via proxy — nunca URL direta do backend

    async function getAll(params?: { page?: number; term?: string }): Promise<Job[]> {
        const query = new URLSearchParams(params as Record<string, string>)
        const res = await fetch(`${baseUrl}/jobs?${query}`)
        if (!res.ok) throw new ApiError(res.status, await res.json())
        return res.json()
    }

    async function getById(id: string): Promise<Job> {
        const res = await fetch(`${baseUrl}/jobs/${id}`)
        if (!res.ok) throw new ApiError(res.status, await res.json())
        return res.json()
    }

    async function create(data: CreateJobPayload): Promise<Job> {
        const res = await fetch(`${baseUrl}/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!res.ok) throw new ApiError(res.status, await res.json())
        return res.json()
    }

    return { getAll, getById, create }
}
```

### 4.2 Padrão de uso no componente com loading e erro

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const jobApi = useJobApi()
const jobs = ref<Job[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
    isLoading.value = true
    error.value = null
    try {
        jobs.value = await jobApi.getAll()
    } catch (e) {
        error.value = 'Não foi possível carregar as vagas.'
        console.error(e)
    } finally {
        isLoading.value = false
    }
})
</script>

<template>
    <!-- Estado de loading -->
    <v-skeleton-loader v-if="isLoading" type="list-item-two-line" :count="3" />

    <!-- Estado de erro -->
    <v-alert v-else-if="error" type="error" variant="tonal">{{ error }}</v-alert>

    <!-- Estado de sucesso -->
    <template v-else>
        <div v-if="jobs.length === 0" class="text-secondary">Nenhuma vaga encontrada.</div>
        <div v-for="job in jobs" :key="job.id">{{ job.title }}</div>
    </template>
</template>
```

**O que NÃO fazer:**
```vue
<!-- ❌ ERRADO — fetch direto no componente sem composable -->
<script setup>
const data = await fetch('http://api.internal:8080/jobs')  // URL interna exposta
</script>

<!-- ❌ ERRADO — sem tratamento de erro -->
<script setup>
const jobs = await fetch('/api/jobs').then(r => r.json())  // sem try/catch, sem loading
</script>

<!-- ❌ ERRADO — sem estado de empty -->
<div v-for="job in jobs" :key="job.id">{{ job.title }}</div>
<!-- (e se jobs for [] ou null?) -->
```

### 4.3 Proxy Next.js (plataforma-lia)

No protótipo `plataforma-lia`, todas as chamadas ao `lia-agent-system` passam por proxy:

```typescript
// src/lib/api/candidate-search.ts — padrão real do projeto
const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""

export async function searchCandidates(query: string) {
    const response = await fetch(`${API_BASE}/api/backend-proxy/search/candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
    })
    if (!response.ok) throw new Error(`Search failed: ${response.status}`)
    return response.json()
}
```

**Nunca** chamar o backend diretamente do browser — sempre via `/api/backend-proxy/*`.

---

## 5. Autenticação e Roles na UI

### 5.1 Fluxo de auth (plataforma-lia — padrão do protótipo)

```typescript
// src/contexts/auth-context.tsx — padrão real do projeto
"use client"

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"

interface AuthContextType {
    user: AuthenticatedUser | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (email: string, password: string) => Promise<void>
    loginWithSSO: (options: { organization?: string }) => void
    logout: () => Promise<void>
    isSSO: boolean
}

export function JWTAuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthenticatedUser | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const refreshUser = useCallback(async () => {
        const method = authService.getAuthMethod()
        if (method === 'sso') {
            const session = await authService.checkSSOSession()
            setUser(session.authenticated ? session.user : null)
        } else if (method === 'jwt') {
            try {
                setUser(await authService.getMe())
            } catch {
                setUser(null)
                authService.clearTokens()
            }
        } else {
            setUser(null)
        }
        setIsLoading(false)
    }, [])

    useEffect(() => { refreshUser() }, [refreshUser])
    // ...
}
```

### 5.2 Guard de rota no Nuxt (ats_front)

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
    const authStore = useAuthStore()

    if (!authStore.isAuthenticated) {
        return navigateTo('/login')
    }
})

// middleware/admin.ts — guard por role
export default defineNuxtRouteMiddleware(() => {
    const authStore = useAuthStore()

    if (!authStore.hasRole('admin')) {
        return navigateTo('/unauthorized')
    }
})
```

### 5.3 Condicional de UI por role

```vue
<template>
    <!-- ✅ Esconde elemento sem bloquear rota -->
    <v-btn v-if="authStore.hasRole('admin')" color="error">
        Excluir vaga
    </v-btn>

    <!-- ✅ Desabilita action sem esconder -->
    <v-btn :disabled="!authStore.hasPermission('job:publish')">
        Publicar
    </v-btn>
</template>
```

**O que NÃO fazer:**
```vue
<!-- ❌ ERRADO — segurança apenas no frontend (backend deve validar também) -->
<div v-if="user.role === 'admin'">
    <!-- O backend DEVE rejeitar a requisição se não for admin -->
</div>

<!-- ❌ ERRADO — redirecionar client-side sem verificar no servidor -->
<script setup>
if (!user) { window.location.href = '/login' }   // use navigateTo() do Nuxt
</script>
```

---

## 6. Padrões de Estilo com Vuetify

### 6.1 O que o DS já configura para você (não repetir)

O tema `liaTheme` e `liaDefaults` (em `app/vuetify-options.ts`) já definem:

```typescript
// vuetify-options.ts — defaults já configurados globalmente
export const liaDefaults = {
    VBtn: { variant: 'flat', rounded: 'md', density: 'comfortable', color: 'primary' },
    VCard: { elevation: 1, rounded: 'md', variant: 'elevated' },
    VTextField: { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VSelect:    { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    // ...todos os inputs seguem o mesmo padrão
}
```

**Você NÃO precisa (e não deve) repetir estas props em cada uso:**

```vue
<!-- ✅ CORRETO — defaults já configurados globalmente -->
<v-btn>Salvar</v-btn>
<v-text-field label="Nome" v-model="name" />

<!-- ❌ ERRADO — repetindo defaults desnecessariamente -->
<v-btn variant="flat" rounded="md" density="comfortable" color="primary">Salvar</v-btn>
<v-text-field variant="outlined" density="comfortable" color="primary" hide-details="auto" label="Nome" />
```

### 6.2 Paleta de cores — como usar corretamente

```vue
<!-- ✅ CORRETO — tokens semânticos do tema -->
<v-btn color="primary">Ação principal</v-btn>
<v-btn color="error">Excluir</v-btn>
<v-chip color="success">Aprovado</v-chip>

<!-- ✅ CORRETO — acentos WeDo (com parcimônia — 10% da interface) -->
<v-icon color="wedo-cyan">mdi-robot</v-icon>

<!-- ❌ ERRADO — hex hardcoded (quebra dark mode e tematização) -->
<v-btn style="background: #111827">Errado</v-btn>
<div style="color: #60BED1">Acento hardcoded</div>
```

**Paleta real (de `vuetify-options.ts`):**

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `primary` | `#111827` | `#F9FAFB` | Botões, elementos principais |
| `secondary` | `#4B5563` | `#9CA3AF` | Textos secundários, ícones |
| `surface` | `#F9FAFB` | `#1A1D1F` | Fundo de cards |
| `surface-variant` | `#F3F4F6` | `#26292B` | Hover, backgrounds alternativos |
| `wedo-cyan` | `#60BED1` | `#60BED1` | Elementos IA, acentos especiais |
| `error` | `#DC2626` | `#F87171` | Erros, ações destrutivas |
| `success` | `#16A34A` | `#4ADE80` | Sucesso, aprovação |
| `warning` | `#F59E0B` | `#FBBF24` | Alertas |

### 6.3 O que customizar (e onde)

| O que customizar | Onde colocar | Exemplo |
|----------------|-------------|---------|
| Override de variável SASS Vuetify | `assets/scss/settings.scss` | `$border-radius-root: 6px` |
| Override de CSS de componente Vuetify | `assets/scss/global.scss` | `.v-btn { font-weight: 600 }` |
| Default de props globais | `app/vuetify-options.ts` (`liaDefaults`) | `VBtn: { rounded: 'md' }` |
| Estilo scoped de componente Lia | `<style scoped>` do `.vue` | `.lia-field { gap: 8px }` |

**O que NÃO customizar:**
```scss
// ❌ PROIBIDO — shadow-xl/2xl quebra o DS
.meu-card { box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important; }

// ❌ PROIBIDO — hardcode de dark mode sem CSS vars
.meu-componente { background: #111 }  // quebrará no light mode

// ❌ PROIBIDO — `!important` para forçar estilo nos componentes Lia*
// (indica que algo está estruturalmente errado)
```

### 6.4 CSS em componentes: tokens Vuetify via CSS vars

```vue
<style scoped>
/* ✅ CORRETO — responsivo a troca de tema (light/dark) */
.lia-card {
    background: rgb(var(--v-theme-surface));
    color: rgb(var(--v-theme-on-surface));
    border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);   /* shadow-sm equivalente */
}

/* ❌ ERRADO — hex hardcoded, quebra dark mode */
.lia-card {
    background: #F9FAFB;
    color: #111827;
}
</style>
```

### 6.5 Tipografia padrão

Definida no `settings.scss` — não precisa repetir em cada componente:

```scss
/* settings.scss — já configurado globalmente */
$body-font-family: ('Open Sans', sans-serif);
$font-size-root: 0.8125rem;   /* 13px */
```

Para labels e tabs (padrão real do `LiaTabBar.vue`):
```css
font-family: 'Open Sans', sans-serif;
font-size: 11px;
font-weight: 500;
line-height: 17px;
letter-spacing: -0.16px;
```

---

## 7. Responsividade e Mobile

### 7.1 Breakpoints do Design System (v4.1)

| Breakpoint | Valor | Vuetify equiv. |
|------------|-------|----------------|
| `xs` | < 600px | `xs` |
| `sm` | 600–960px | `sm` |
| `md` | 960–1280px | `md` |
| `lg` | 1280–1920px | `lg` |
| `xl` | > 1920px | `xl` |

### 7.2 Grid responsivo com Vuetify

```vue
<template>
    <!-- ✅ Grid responsivo com v-row/v-col -->
    <v-row>
        <v-col cols="12" md="6" lg="4">
            <LiaDepartmentCard :department="dept" />
        </v-col>
    </v-row>

    <!-- ✅ Esconder em mobile -->
    <v-btn class="d-none d-md-flex">Exportar CSV</v-btn>

    <!-- ✅ Exibir apenas em mobile -->
    <v-bottom-navigation class="d-flex d-md-none" />
</template>
```

### 7.3 Composable de breakpoint

```typescript
// composables/useBreakpoint.ts
import { useDisplay } from 'vuetify'

export function useBreakpoint() {
    const { mobile, tablet, mdAndUp } = useDisplay()
    return { mobile, tablet, mdAndUp }
}
```

```vue
<script setup lang="ts">
const { mobile } = useBreakpoint()
</script>

<template>
    <!-- Layout diferente por breakpoint -->
    <v-navigation-drawer v-if="!mobile" permanent />
    <v-bottom-navigation v-else />
</template>
```

### 7.4 Mobile-first no CSS

```vue
<style scoped>
/* ✅ Mobile-first: base é mobile, expande para desktop */
.lia-layout {
    display: flex;
    flex-direction: column;          /* mobile: coluna */
    gap: 12px;
    padding: 12px;
}

@media (min-width: 960px) {         /* md+ */
    .lia-layout {
        flex-direction: row;         /* desktop: linha */
        gap: 24px;
        padding: 24px;
    }
}

/* ❌ ERRADO — desktop-first (difícil de manter em mobile) */
.lia-layout {
    flex-direction: row;
    gap: 24px;
}

@media (max-width: 959px) {
    .lia-layout { flex-direction: column; }
}
</style>
```

### 7.5 Touch targets e interatividade mobile

```vue
<!-- ✅ Target mínimo 44px para toque -->
<button class="lia-action-btn" type="button" @click="handleAction">
    <!-- SVG icone -->
</button>

<style scoped>
.lia-action-btn {
    min-width: 44px;
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    cursor: pointer;
}
</style>
```

---

## Checklist antes de fazer PR de componente frontend

- [ ] Arquivo nomeado `LiaXxx.vue` em PascalCase com prefixo `Lia`
- [ ] `<script setup lang="ts">` (nunca Options API)
- [ ] Props tipadas com `defineProps<{...}>()` e JSDoc em cada prop
- [ ] Emits tipados com `defineEmits<{...}>()`
- [ ] CSS em `<style scoped>` com BEM (`.lia-bloco__elemento--modificador`)
- [ ] Cores via `rgb(var(--v-theme-*))` — sem hex hardcoded
- [ ] Story `.story.vue` criada no mesmo diretório
- [ ] Sem `shadow-xl` nem `shadow-2xl`
- [ ] Loading state, empty state e error state cobertos no template
- [ ] Mobile testado nos breakpoints xs e md

> Para padrões de CODING, ver `docs/CODING_STANDARDS.md`.
> Para padrões do backend que este frontend consome, ver `docs/specs/standards/BACKEND_STANDARDS.md`.
