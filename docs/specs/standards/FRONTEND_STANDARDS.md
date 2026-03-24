# Frontend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> **Fonte exclusiva**: código lido via GitHub API — repositórios `wedo-nuxt` e `ats_front` (WeDOTalent)
> Stack: Vue 3 + Nuxt 3 + Vuetify 3 (`wedo-nuxt`) / `ats_front` (vazio no GitHub — sem código publicado)

---

## Aviso de escopo

O repositório `ats_front` existe no GitHub WeDOTalent mas contém apenas `.gitignore` — sem código publicado.
Todo o padrão de componentes, estilo e configuração deste documento vem do repositório `wedo-nuxt`,
que é o Design System LIA e a fonte canônica de referência de frontend.

---

## 1. Estrutura de Pastas (`wedo-nuxt`)

Lida diretamente do repositório GitHub:

```
wedo-nuxt/
├── app/
│   ├── assets/
│   │   └── icons/                ← SVGs inline: brain-tree.svg, upload.svg, download.svg, etc.
│   ├── components/               ← Componentes Lia* + stories Histoire
│   │   ├── LiaBigFiveChart.vue
│   │   ├── LiaBigFiveChart.story.vue
│   │   ├── LiaCtaBanner.vue
│   │   ├── LiaCtaBanner.story.vue
│   │   ├── LiaDepartmentCard.vue
│   │   ├── LiaDepartmentCard.story.vue
│   │   ├── LiaField.vue          ← campo com slot IA + toggle + robot button
│   │   ├── LiaField.story.vue
│   │   ├── LiaFileUpload.vue     ← drag-and-drop com badges de formato
│   │   ├── LiaFileUpload.story.vue
│   │   ├── LiaPageHeader.vue
│   │   ├── LiaPageHeader.story.vue
│   │   ├── LiaSectionHeader.vue
│   │   ├── LiaSectionHeader.story.vue
│   │   ├── LiaTabBar.vue
│   │   ├── LiaTabBar.story.vue
│   │   ├── DadosDaEmpresa.vue    ← componente de domínio (sem prefixo Lia)
│   │   └── Departamentos.vue     ← componente de domínio (sem prefixo Lia)
│   ├── vuetify-options.ts        ← liaTheme + liaDefaults (fonte do tema)
│   └── app.vue
├── assets/scss/
│   ├── settings.scss             ← override de variáveis SASS Vuetify (antes do CSS)
│   └── global.scss               ← overrides de componentes Vuetify
├── docs/
│   └── 00-design-system-v4.md   ← documento canônico do Design System LIA v4.1
├── nuxt.config.ts                ← configuração Nuxt: modules, css, vuetify
├── vuetify.config.ts             ← ponto de entrada Vuetify
├── histoire.config.ts            ← configuração Histoire (preview de stories)
└── histoire-setup.ts             ← setup Histoire (usa mesmo liaTheme/liaDefaults)
```

**Regra obrigatória**: todo componente `Lia*.vue` tem um arquivo `.story.vue` no mesmo diretório.

**Sobre nomenclatura de componentes:**
- Componentes do Design System (reutilizáveis na plataforma): prefixo `Lia` obrigatório → `LiaField`, `LiaTabBar`
- Componentes de domínio/página específicos: sem prefixo, mas PascalCase → `DadosDaEmpresa`, `Departamentos`

---

## 2. Como Criar um Componente Novo

### Passo a passo baseado nos componentes reais do `wedo-nuxt`

**1. Definir o arquivo:**
```
app/components/LiaNomeDoComponente.vue
app/components/LiaNomeDoComponente.story.vue
```

**2. Estrutura obrigatória do `.vue` — ordem das seções:**
```
1. <template>
2. <script setup lang="ts">
3. <style scoped>
```

**3. Template: HTML semântico com BEM — extraído de `LiaField.vue`:**

```vue
<template>
    <div class="lia-field" :class="{ 'lia-field--disabled': disabled }">
        <!-- Label + optional pill + optional image -->
        <div class="lia-field__meta">
            <span class="lia-field__label">{{ label }}</span>
            <div v-if="comment" class="lia-field__pill">
                {{ comment }}
            </div>
        </div>

        <!-- Content area: icon + textarea slot + robot button + toggle -->
        <div class="lia-field__content">
            <!-- Optional icon between meta and textarea -->
            <img v-if="commentImage" :src="commentImage" :alt="comment ?? 'icon'" class="lia-field__image" />

            <!-- Slotted input area -->
            <div class="lia-field__input">
                <slot />
            </div>

            <!-- LIA robot button -->
            <button
                v-if="showRobotButton"
                :disabled="disabled"
                class="lia-field__robot-btn"
                type="button"
                @click="$emit('liaAddData')"
            >
                <!-- SVG inline — nunca src externo para ícones de UI -->
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" ...>...</svg>
            </button>

            <!-- Processing toggle -->
            <v-switch
                v-if="showToggle"
                :model-value="modelValue"
                :disabled="disabled"
                hide-details
                density="compact"
                class="lia-field__toggle"
                @update:model-value="$emit('update:modelValue', $event ?? false)"
            />
        </div>
    </div>
</template>
```

**4. Script: `withDefaults` + JSDoc — extraído de `LiaField.vue`:**

```vue
<script setup lang="ts">
// Interfaces exportadas (quando outros arquivos precisam do tipo)
export interface TabItem {
    key: string
    label: string
}

// Props tipadas com TypeScript e JSDoc em cada prop
withDefaults(defineProps<{
    /** Field label text (mandatory) */
    label: string
    /** Optional comment / pill text */
    comment?: string
    /** Optional image src after the pill */
    commentImage?: string
    /** Disables all interactions */
    disabled?: boolean
    /** Toggle state (v-model) — maps to liaShouldProcess */
    modelValue?: boolean
    /** Whether to show the robot button */
    showRobotButton?: boolean
    /** Whether to show the toggle switch */
    showToggle?: boolean
}>(), {
    comment: undefined,
    commentImage: undefined,
    disabled: false,
    modelValue: true,
    showRobotButton: true,
    showToggle: true,
})

// Emits tipados com JSDoc
defineEmits<{
    /** Fired when the robot button is clicked */
    (e: 'liaAddData'): void
    /** Toggle change event */
    (e: 'update:modelValue', value: boolean): void
}>()

// Estado local — apenas o necessário neste componente
const isDragging = ref(false)   // exemplo de LiaFileUpload.vue
</script>
```

**5. Style: BEM com tokens Vuetify — extraído de `LiaField.vue` e `LiaSectionHeader.vue`:**

```vue
<style scoped>
/*
 * Color mapping (Figma → Vuetify theme):
 *   #111827  →  rgb(var(--v-theme-primary))
 *   #4B5563  →  rgb(var(--v-theme-secondary))
 *   #F9FAFB  →  rgb(var(--v-theme-surface))
 *   #F3F4F6  →  rgb(var(--v-theme-surface-variant))
 */

/* ── Bloco raiz ── */
.lia-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* ── Elementos (__) ── */
.lia-field__label {
    font-family: 'Open Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    line-height: 17px;
    letter-spacing: -0.16px;
    color: rgb(var(--v-theme-on-background));   /* nunca hex hardcoded */
}

.lia-field__robot-btn {
    transition: background 0.15s ease, color 0.15s ease;   /* transição obrigatória */
}

/* ── Modificadores (--) ── */
.lia-field--disabled {
    opacity: 0.6;
    pointer-events: none;
}
</style>
```

**6. Story Histoire — extraído de `LiaField.story.vue`:**

```vue
<!-- LiaMeuComponente.story.vue -->
<script setup lang="ts">
import LiaMeuComponente from './LiaMeuComponente.vue'
</script>

<template>
    <Story title="LIA / MeuComponente">
        <Variant title="Default">
            <LiaMeuComponente label="Label padrão" />
        </Variant>
        <Variant title="Disabled">
            <LiaMeuComponente label="Desabilitado" :disabled="true" />
        </Variant>
        <Variant title="With comment">
            <LiaMeuComponente label="Com comentário" comment="Opcional" />
        </Variant>
    </Story>
</template>
```

**O que NÃO fazer:**
```vue
<!-- ❌ Options API — nunca usar no projeto -->
<script>
export default {
    props: { label: String },
    data() { return { count: 0 } }
}
</script>

<!-- ❌ sem lang="ts" — TypeScript não é aplicado -->
<script setup>
defineProps({ label: String })
</script>

<!-- ❌ sem prefixo e sem PascalCase -->
<!-- campo.vue, form-field.vue, formField.vue -->
```

---

## 3. Gerenciamento de Estado

### 3.1 Estado local com `ref` — padrão real do `LiaFileUpload.vue`

Use `ref` para estado que pertence **somente** ao componente:

```vue
<script setup lang="ts">
import { ref } from 'vue'

// Estado de UI local — relevante apenas neste componente
const isDragging = ref(false)

function onDrop(event: DragEvent) {
    isDragging.value = false
    const files = event.dataTransfer?.files
    if (files?.length) {
        // processamento do arquivo
    }
}
</script>

<template>
    <!-- modificador BEM refletindo estado reativo -->
    <div class="lia-file-upload__card" :class="{ 'lia-file-upload__card--dragging': isDragging }">
        ...
    </div>
</template>
```

**Use estado local quando:** loading de botão, toggle de modal, drag-and-drop, valor temporário de input, controle de step de wizard.

### 3.2 Estado global com Pinia

Use Pinia quando o estado precisa ser **compartilhado entre rotas ou componentes sem relação de pai-filho**.

O `wedo-nuxt` (Design System puro) não contém stores — é uma biblioteca de componentes.
O `ats_front` (aplicação) é onde Pinia é usado; como esse repositório está vazio no GitHub,
o padrão a seguir é o da documentação do Nuxt/Pinia com Setup Stores:

```typescript
// stores/jobStore.ts — padrão Setup Store (preferível ao Options Store)
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useJobStore = defineStore('job', () => {
    // State — refs
    const jobs = ref<Job[]>([])
    const selectedJobId = ref<string | null>(null)
    const isLoading = ref(false)

    // Getters — computed
    const selectedJob = computed(() =>
        jobs.value.find(j => j.id === selectedJobId.value) ?? null
    )

    // Actions — funções regulares
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

**Use Pinia quando:** dados do usuário logado, lista de vagas usada em múltiplas telas, filtros persistidos entre navegações, seleções de kanban/pipeline.

---

## 4. Chamadas de API

O `wedo-nuxt` é uma biblioteca de componentes — não faz chamadas de API.
O padrão abaixo é o que o `ats_front` (aplicação) deve seguir ao consumir o `ats_api`:

### 4.1 Composable por recurso — nunca fetch direto no componente

```typescript
// composables/useJobApi.ts
export function useJobApi() {
    const baseUrl = '/api/v1'   // proxy local — nunca URL direta do backend Rails

    async function getAll(params?: { term?: string; page?: number }): Promise<Job[]> {
        const query = new URLSearchParams(params as Record<string, string>)
        const res = await fetch(`${baseUrl}/users/jobs?${query}`, {
            headers: { 'Authorization': `Bearer ${useAuthStore().token}` }
        })
        if (!res.ok) throw new ApiError(res.status, await res.json())
        const body = await res.json()
        return body.data   // JSONAPI::Serializer retorna { data: [...] }
    }

    async function create(data: CreateJobPayload): Promise<Job> {
        const res = await fetch(`${baseUrl}/users/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${useAuthStore().token}`
            },
            body: JSON.stringify({ job: data }),   // Rails espera strong params: { job: {...} }
        })
        if (!res.ok) throw new ApiError(res.status, await res.json())
        return res.json()
    }

    return { getAll, create }
}
```

### 4.2 Padrão de uso com loading, error e empty

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
    } finally {
        isLoading.value = false
    }
})
</script>

<template>
    <v-skeleton-loader v-if="isLoading" type="list-item-two-line" :count="5" />
    <v-alert v-else-if="error" type="error" variant="tonal">{{ error }}</v-alert>
    <template v-else>
        <p v-if="!jobs.length" class="text-secondary">Nenhuma vaga encontrada.</p>
        <div v-for="job in jobs" :key="job.id">{{ job.title }}</div>
    </template>
</template>
```

**O que NÃO fazer:**
```vue
<!-- ❌ URL direta do backend — nunca expor no browser -->
<script setup>
const jobs = await fetch('http://internal-api:3000/v1/jobs').then(r => r.json())

<!-- ❌ sem tratamento de erro, sem loading, sem empty -->
const jobs = await fetch('/api/jobs').then(r => r.json())
</script>
```

---

## 5. Autenticação e Roles na UI

O `ats_api` usa JWT manual (lido de `sessions_controller.rb`):
- `POST /v1/sessions` → retorna `{ user: {...}, token: "eyJ..." }`
- Header em todas as requisições autenticadas: `Authorization: Bearer <token>`
- `GET /v1/me` → retorna usuário atual com o token

### 5.1 Guard de rota no Nuxt

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware(() => {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
        return navigateTo('/login')
    }
})
```

```vue
<!-- pages/dashboard.vue — proteger rota -->
<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
</script>
```

### 5.2 Condicional de UI por role/permissão

```vue
<template>
    <!-- ✅ Esconde elemento — backend DEVE também validar -->
    <v-btn v-if="authStore.hasRole('admin')" color="error">Excluir</v-btn>

    <!-- ✅ Desabilita sem esconder -->
    <v-btn :disabled="!authStore.hasPermission('job:publish')">Publicar</v-btn>
</template>
```

**Regra:** o frontend esconde/desabilita elementos por UX — o backend Rails **sempre** valida a permissão na requisição. Nunca depender só do frontend para segurança.

---

## 6. Padrões de Estilo com Vuetify

### 6.1 Configuração: onde cada coisa fica

Extraído dos arquivos reais do `wedo-nuxt`:

```
nuxt.config.ts          → registra modules: ['vuetify-nuxt-module']
                          css: ['~/assets/scss/global.scss']
                          vuetify.moduleOptions.styles.configFile: 'assets/scss/settings.scss'

vuetify.config.ts       → importa liaTheme e liaDefaults de app/vuetify-options.ts

app/vuetify-options.ts  → define lightTheme, darkTheme, liaTheme, liaDefaults
assets/scss/settings.scss → override de variáveis SASS Vuetify (carregado ANTES do CSS)
assets/scss/global.scss   → override de CSS de componentes Vuetify
```

### 6.2 Tema: `liaTheme` — cores reais de `vuetify-options.ts`

```typescript
// app/vuetify-options.ts — código real do repositório wedo-nuxt (GitHub)
const lightTheme: ThemeDefinition = {
    dark: false,
    colors: {
        // === Core Monocromático (90% da interface) ===
        primary:            '#111827',   // Ebony — botões, textos principais
        secondary:          '#4B5563',   // River Bed — textos secundários
        background:         '#FFFFFF',
        surface:            '#F9FAFB',   // fundo de cards
        'surface-variant':  '#F3F4F6',   // hover states

        // === Status Semântico ===
        error:    '#DC2626',
        warning:  '#F59E0B',
        success:  '#16A34A',
        info:     '#2563EB',

        // === Cores WeDo (10% — acentos estratégicos) ===
        'wedo-cyan':    '#60BED1',   // Brain LIA, Vagas
        'wedo-green':   '#5DA47A',   // Candidatos, Aprovação
        'wedo-orange':  '#D19960',   // Tempo, Prazos
        'wedo-purple':  '#9860D1',   // Insights, IA
        'wedo-magenta': '#D160AB',   // Urgência crítica
    },
}
```

**Dark mode** usa os mesmos tokens WeDo (cyan, green, etc.) — eles **não mudam** entre temas. Apenas os tons core (primary, surface, background) se invertem.

### 6.3 Defaults: `liaDefaults` — o que já está configurado globalmente

```typescript
// app/vuetify-options.ts — código real
export const liaDefaults = {
    VBtn:         { variant: 'flat', rounded: 'md', density: 'comfortable', color: 'primary' },
    VCard:        { elevation: 1, rounded: 'md', variant: 'elevated' },
    VTextField:   { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VTextarea:    { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VSelect:      { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VAutocomplete:{ variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VCombobox:    { variant: 'outlined', density: 'comfortable', color: 'primary', hideDetails: 'auto' },
    VFileInput:   { variant: 'outlined', density: 'comfortable', color: 'primary',
                    prependIcon: 'mdi-paperclip', hideDetails: 'auto' },
    VCheckbox:    { color: 'primary', density: 'comfortable', hideDetails: 'auto' },
    VRadio:       { color: 'primary', density: 'comfortable' },
    // ... (todos os componentes de input seguem o mesmo padrão)
}
```

**Consequência direta:** você NÃO precisa repetir essas props em cada uso:

```vue
<!-- ✅ CORRETO — defaults já aplicados globalmente -->
<v-btn>Salvar</v-btn>
<v-text-field label="Nome" v-model="name" />

<!-- ❌ ERRADO — repetindo o que já está em liaDefaults -->
<v-btn variant="flat" rounded="md" density="comfortable" color="primary">Salvar</v-btn>
<v-text-field variant="outlined" density="comfortable" color="primary" hide-details="auto" label="Nome" />
```

### 6.4 Settings SASS — `assets/scss/settings.scss`

```scss
/* assets/scss/settings.scss — código real do wedo-nuxt */
@use 'vuetify/settings' with (
    $body-font-family:    ('Open Sans', sans-serif),
    $heading-font-family: ('Open Sans', sans-serif),
    $font-size-root:      0.8125rem,     /* 13px */
    $border-radius-root:  6px,
    $standard-easing:     cubic-bezier(0.4, 0, 0.2, 1),
    $typography: ('button': (
        'size': 0.8125rem,
        'weight': 600,
        'letter-spacing': normal,
        'text-transform': none,          /* remove uppercase dos botões */
    )),
);
```

### 6.5 Onde cada tipo de customização vai

| O que customizar | Arquivo | Exemplo |
|----------------|---------|---------|
| Variável SASS Vuetify (`$border-radius-root`) | `assets/scss/settings.scss` | `$border-radius-root: 6px` |
| CSS de componente Vuetify (`.v-btn`) | `assets/scss/global.scss` | `.v-btn { font-weight: 600 }` |
| Props default de componente Vuetify | `app/vuetify-options.ts` (`liaDefaults`) | `VBtn: { rounded: 'md' }` |
| Estilo exclusivo do componente Lia | `<style scoped>` do `.vue` | `.lia-field { gap: 8px }` |

### 6.6 Cores nos `<style scoped>`: tokens CSS vars, nunca hex

```vue
<style scoped>
/* ✅ CORRETO — responsivo a troca de tema (light/dark) */
.lia-field__label {
    color: rgb(var(--v-theme-on-background));
}
.lia-file-upload__card {
    background: rgb(var(--v-theme-background));
    border: 2px dashed #E5E7EB;             /* borda pode ser literal quando é fixa no DS */
    box-shadow: 0px 1px 2px rgba(0,0,0,0.05);  /* shadow-sm — nunca shadow-xl/2xl */
}

/* ❌ ERRADO — hex hardcoded para cores que mudam no dark mode */
.lia-field__label { color: #111827; }
.lia-card { background: #F9FAFB; }
</style>
```

### 6.7 Tipografia padrão (de `LiaTabBar.vue` e `LiaSectionHeader.vue`)

Labels, tabs e section headers do DS:
```css
font-family: 'Open Sans', sans-serif;
font-size: 11px;
font-weight: 500 ou 600;
line-height: 17px;
letter-spacing: -0.16px;
```

---

## 7. Responsividade e Mobile

### 7.1 Breakpoints do Design System LIA v4.1

Extraídos de `docs/00-design-system-v4.md`:

| Breakpoint | Largura | Vuetify | Tailwind |
|------------|---------|---------|---------|
| `xs` | < 600px | `xs` | `sm:` não aplicado |
| `sm` | 600–960px | `sm` | `sm:` |
| `md` | 960–1280px | `md` | `md:` |
| `lg` | 1280–1920px | `lg` | `lg:` |
| `xl` | > 1920px | `xl` | `xl:` |

### 7.2 Drag-and-drop com mobile em mente — `LiaFileUpload.vue`

```vue
<!-- LiaFileUpload.vue — drag-and-drop com fallback de botão para mobile -->
<template>
    <div
        class="lia-file-upload"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
    >
        <!-- Em mobile: drag não funciona, exibir botão "Selecionar" sempre -->
        <button class="lia-file-upload__btn lia-file-upload__btn--select"
                type="button"
                @click="$emit('select-file')">
            <img :src="uploadIcon" alt="" class="lia-file-upload__btn-icon" />
            <span>{{ selectLabel }}</span>
        </button>
    </div>
</template>
```

### 7.3 CSS mobile-first

```vue
<style scoped>
/* ── Base: mobile ── */
.lia-file-upload__card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px;
    border-radius: 16px;
    border: 2px dashed #E5E7EB;
    transition: opacity 0.2s ease, border-color 0.2s ease;
}

/* ── Hover e drag: desktop ── */
.lia-file-upload__card:hover,
.lia-file-upload__card--dragging {
    opacity: 1;
    border-color: rgb(var(--v-theme-primary));
}

@media (min-width: 960px) {
    .lia-file-upload__card {
        padding: 32px 24px;   /* mais espaço em desktop */
    }
}
</style>
```

### 7.4 Grid Vuetify responsivo

```vue
<template>
    <v-row>
        <!-- mobile: coluna inteira | tablet: metade | desktop: terço -->
        <v-col cols="12" sm="6" lg="4" v-for="dept in departments" :key="dept.id">
            <LiaDepartmentCard :department="dept" />
        </v-col>
    </v-row>

    <!-- Ocultar ação em mobile — usar classes Vuetify -->
    <v-btn class="d-none d-md-flex">Exportar CSV</v-btn>
</template>
```

---

## Checklist de PR — componente frontend

- [ ] Arquivo `LiaNome.vue` em PascalCase (prefixo `Lia` para DS, sem prefixo para domínio)
- [ ] `<script setup lang="ts">` — nunca Options API
- [ ] Props com `defineProps<{...}>()` tipadas e JSDoc em cada prop
- [ ] Emits com `defineEmits<{...}>()` tipados
- [ ] CSS em `<style scoped>` com nomenclatura BEM
- [ ] Cores via `rgb(var(--v-theme-*))` — sem hex hardcoded para cores de tema
- [ ] Story `.story.vue` criada no mesmo diretório com ao menos 2 variants
- [ ] Sem `shadow-xl` nem `shadow-2xl`
- [ ] Loading, empty state e error state cobertos no template
- [ ] Interações com `transition:` definida no CSS

> **Fonte**: todo código deste documento foi lido diretamente do repositório `wedo-nuxt` no GitHub WeDOTalent.
> Para padrões de backend, ver `docs/specs/standards/BACKEND_STANDARDS.md`.
