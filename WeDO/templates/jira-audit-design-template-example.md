# TEMPLATE — Saída do script jira-audit-design.py
# Card de exemplo: WT-1637 — Menu Lateral
# Gerado por: python3 scripts/jira-audit-design.py WT-1637 --vue-file components/ui/menu/sidebar.vue
# ─────────────────────────────────────────────────────────────────────────────
# Foco EXCLUSIVO em design — mapeamento completo de TODOS os elementos visuais
# mencionados na transcrição, com ANTES/DEPOIS concreto em Vue.
# ─────────────────────────────────────────────────────────────────────────────


# AUDITORIA DE DESIGN — LIA Design System v4.2.1

Card Jira: WT-1637
Tela: Menu Lateral Esquerdo (Sidebar)
Rota: /
Gerado em: 21/03/2026

─────────────────────────────────────────────────────────────────

## 🔍 Issues de Auditoria — React vs Vue (gerados por IA)

Metodologia: React/Replit = fonte da verdade absoluta.
Cada Issue abaixo é um bug confirmado — Vue diverge do React.
Sem '[VER NO PROD]'. Sem 'verificar'. Cada Issue tem Antes/Depois concreto.

# Auditoria DS LIA v4.2.1 — Menu Lateral Esquerdo (Sidebar)

Card Jira: WT-1637
Tela: Menu Lateral Esquerdo (Sidebar)
Arquivos auditados: components/ui/menu/sidebar.vue

## Issues Identificadas

### Issue 01 — Comportamento de visibilidade incorreto (expand-on-hover vs sempre visível)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: O menu deve estar sempre visível (expandido ou colapsado), nunca aparecer apenas no hover.

**ANTES (Vue atual — INCORRETO):**
```vue
<v-navigation-drawer
  v-if="!isLoading"
  id="menu-nav-drawer"
  v-model="drawer"
  :rail-width="64"
  expand-on-hover
  :rail="isRail"
  @mouseenter="isHovered = true"
  @mouseleave="isHovered = false"
>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-navigation-drawer
  v-if="!isLoading"
  id="menu-nav-drawer"
  v-model="drawer"
  :rail-width="64"
  :rail="isRail"
  :width="240"
  permanent
>
```

⚠️ BUG CRÍTICO REPORTADO NO JIRA: O comportamento expand-on-hover faz o menu aparecer apenas quando o mouse passa por cima, sobrepondo o logo "We Do". O React usa sidebar permanente que alterna entre colapsado (rail) e expandido via botão chevron, não via hover.

─────────────────────────────────────────────────────────────────

### Issue 02 — Largura do modo expandido não especificada (256px vs 240px)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Sidebar expandido deve ter largura fixa de 240px (w-60 no React).

**ANTES (Vue atual — INCORRETO):**
```vue
<v-navigation-drawer
  :rail-width="64"
  expand-on-hover
  :rail="isRail"
  <!-- width não especificado — usa default Vuetify de 256px -->
>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-navigation-drawer
  :rail-width="64"
  :width="240"
  :rail="isRail"
  permanent
>
```

⚠️ DEFAULT VUETIFY: Sem width explícito, v-navigation-drawer usa 256px. O DS LIA especifica 240px (w-60). Diferença de 16px visível no layout da página.

─────────────────────────────────────────────────────────────────

### Issue 03 — Logo: transição controlada por hover em vez de isRail

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Logo controlado pelo estado do rail (colapsado/expandido), não por hover.

**ANTES (Vue atual — INCORRETO):**
```vue
<Transition name="logo-transition">
  <img
    v-if="!showOnOpenNavigation"
    src="/we-logo-pequeno.png"
    style="width: 38px; border-radius: 6px; position: absolute"
  />
  <img
    v-else
    src="/wedo-logo.png"
    style="height: 32px; position: absolute"
  />
</Transition>

<!-- showOnOpenNavigation depende de hover -->
const showOnOpenNavigation = computed(() => isHovered.value || !isRail.value)
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<div class="d-flex align-center" style="height: 40px;">
  <img
    v-if="isRail"
    src="/we-logo-pequeno.png"
    alt="We Logo"
    style="width: 32px; border-radius: 8px;"
  />
  <img
    v-else
    src="/wedo-logo.png"
    alt="WeDO Logo"
    style="height: 28px;"
  />
</div>

<!-- Remover showOnOpenNavigation — usar isRail diretamente -->
const showExpandedContent = computed(() => !isRail.value)
```

⚠️ O logo aparece incorretamente durante o hover antes do menu expandir completamente, criando flash visual. Deve ser binário: isRail = logo pequeno, !isRail = logo completo.

─────────────────────────────────────────────────────────────────

### Issue 04 — Botão chevron posicionado como append do logo (vs separado abaixo)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Botão de toggle (chevron) é separado do logo, não um append.

**ANTES (Vue atual — INCORRETO):**
```vue
<v-list-item>
  <template v-slot:prepend>
    <!-- Logo aqui -->
  </template>
  <template v-slot:append>
    <Icon
      :name="isRail ? 'lucide-chevron-right' : 'lucide-chevron-left'"
      size="x-small"
      @click="isRail = !isRail"
    />
  </template>
</v-list-item>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<!-- Logo em bloco separado -->
<v-list-item class="pa-2">
  <nuxt-link to="/user/dashboard" class="d-flex align-center">
    <img v-if="isRail" src="/we-logo-pequeno.png" style="width: 32px; border-radius: 8px;" />
    <img v-else src="/wedo-logo.png" style="height: 28px;" />
  </nuxt-link>
</v-list-item>

<!-- Botão toggle separado, visível quando expandido -->
<div v-if="!isRail" class="px-2 pb-2">
  <v-btn variant="text" size="small" icon @click="isRail = !isRail" class="rounded-lg">
    <Icon name="lucide-chevron-left" size="16" color="on-background" />
  </v-btn>
</div>
```

⚠️ O posicionamento como append faz o chevron ficar colado ao logo, criando área de clique confusa. O React separa os dois elementos visualmente.

─────────────────────────────────────────────────────────────────

### Issue 05 — Ícone chevron com tamanho x-small (variável) em vez de 16px (fixo)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Todos os ícones de interface devem ter 16px (w-4 h-4).

**ANTES (Vue atual — INCORRETO):**
```vue
<Icon
  :name="isRail ? 'lucide-chevron-right' : 'lucide-chevron-left'"
  size="x-small"
  @click="isRail = !isRail"
/>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<Icon
  :name="isRail ? 'lucide-chevron-right' : 'lucide-chevron-left'"
  size="16"
  @click="isRail = !isRail"
/>
```

⚠️ x-small do Vuetify = 16px apenas em alguns componentes, mas pode variar. Sempre especificar 16 numericamente para garantir consistência.

─────────────────────────────────────────────────────────────────

### Issue 06 — Label "MENU": controlada por hover, não por isRail

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Elementos condicionais do sidebar controlados por isRail, nunca por hover.

**ANTES (Vue atual — INCORRETO):**
```vue
<p
  class="f12 text-body-dark font-weight-medium pt-4 pb-3 px-4"
  style="letter-spacing: 0.2em"
  v-if="showOnOpenNavigation"
>
  MENU
</p>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<!-- Controlar por isRail, não por hover -->
<p
  v-if="!isRail"
  class="text-xs text-grey-darken-1 font-weight-medium pt-4 pb-3 px-4"
  style="letter-spacing: 0.05em;"
>
  MENU
</p>
```

⚠️ letter-spacing: 0.2em é muito amplo — DS LIA usa no máximo 0.05em para labels de seção.

─────────────────────────────────────────────────────────────────

### Issue 07 — Border radius dos itens de menu incorreto (12px vs 8px)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Border radius SEMPRE 8px (rounded-md). Nunca valores custom.

**ANTES (Vue atual — INCORRETO):**
```vue
<v-list-item
  v-for="item in menuItems"
  class="rounded-12px py-2"
>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-list-item
  v-for="item in menuItems"
  class="rounded-lg py-2"
  style="border-radius: 8px !important;"
>
```

⚠️ rounded-12px (12px) viola a regra de 8px universal. rounded-lg do Vuetify mapeia para 8px ou usar style explícito.

─────────────────────────────────────────────────────────────────

### Issue 08 — Ícones dos itens de menu com tamanho 14px (vs 16px)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Ícones padrão SEMPRE 16px (w-4 h-4).

**ANTES (Vue atual — INCORRETO):**
```vue
<Icon :name="item.icon" size="14" customClasses="mx-1" />
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<Icon :name="item.icon" size="16" customClasses="mx-1" />
```

⚠️ 14px vs 16px: diferença sutil mas sistemática — todos os ícones ficam ligeiramente menores que o esperado pelo DS.

─────────────────────────────────────────────────────────────────

### Issue 09 — Cor ativa dos itens usa token customizado (vs bg-gray-100)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Estado ativo usa bg-gray-100 (light) / bg-gray-800 (dark).

**ANTES (Vue atual — INCORRETO):**
```vue
<v-list-item
  :active="isActive(item.url).value"
  color="rgba(var(--v-theme-body-medium), 0.5)"
  base-color="rgba(var(--v-theme-body-dark), 1)"
>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-list-item
  :active="isActive(item.url).value"
  :class="{
    'bg-grey-lighten-4': isActive(item.url).value && !isDark,
    'bg-grey-darken-3': isActive(item.url).value && isDark,
  }"
  active-class="font-weight-semibold"
>
```

⚠️ rgba com variáveis de tema custom cria dependência desnecessária. DS LIA usa classes Tailwind/Vuetify diretas.

─────────────────────────────────────────────────────────────────

### Issue 10 — Tipografia dos itens sem font-size explícito (13px)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Texto dos itens de menu deve ser 13px com line-height 1.25.

**ANTES (Vue atual — INCORRETO):**
```vue
<v-list-item :title="showOnOpenNavigation ? item.label : ''">
  <!-- Usa tipografia default do Vuetify — 14px ou 16px -->
</v-list-item>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-list-item
  :title="!isRail ? item.label : ''"
  class="text-body-2"
  style="font-size: 13px; line-height: 1.25;"
>
```

⚠️ Vuetify v-list-item usa 14px por padrão. DS LIA especifica 13px para navegação — diferença visível em menus densos.

─────────────────────────────────────────────────────────────────

### Issue 11 — Altura mínima dos itens não especificada (sem min-h: 40px)

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Itens de menu devem ter min-height 40px.

**ANTES (Vue atual — INCORRETO):**
```vue
<v-list-item class="rounded-12px py-2">
  <!-- Sem min-height especificado — varia com conteúdo -->
</v-list-item>
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<v-list-item
  class="rounded-lg py-2"
  style="min-height: 40px; border-radius: 8px;"
>
```

─────────────────────────────────────────────────────────────────

### Issue 12 — Filtros de vagas contextuais completamente ausentes

Arquivo Vue: `components/ui/menu/sidebar.vue`
Regra DS LIA: Quando em /vagas, exibir filtros expandíveis no sidebar (Todas, Ativas, Paralisadas, etc.)

**ANTES (Vue atual — INCORRETO):**
```vue
<!-- Não existe implementação de filtros contextuais de vagas -->
```

**DEPOIS (deve ficar assim — React/DS LIA):**
```vue
<template v-if="isJobsPage && !isRail">
  <v-divider class="my-2" />
  <div class="px-4 py-2">
    <button
      @click="isFiltersExpanded = !isFiltersExpanded"
      class="d-flex align-center justify-space-between w-100"
      style="font-size: 13px;"
    >
      <span class="text-grey-darken-1 font-weight-medium">Filtros de Vagas</span>
      <Icon
        :name="isFiltersExpanded ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        size="16"
      />
    </button>
  </div>
  <v-list v-if="isFiltersExpanded" density="compact" nav class="px-4">
    <v-list-item
      v-for="filter in jobFilterItems"
      :key="filter.value"
      :active="currentJobFilter === filter.value"
      class="rounded-lg py-1"
      style="min-height: 36px; border-radius: 8px; font-size: 13px;"
      @click="$emit('job-filter-change', filter.value)"
    >
      <template v-slot:prepend>
        <Icon :name="filter.icon" size="16" class="mr-2" />
      </template>
      <template v-slot:default>{{ filter.label }}</template>
      <template v-slot:append>
        <span class="text-grey text-caption">{{ filter.count }}</span>
      </template>
    </v-list-item>
  </v-list>
</template>
```

⚠️ Feature completamente ausente no Vue — presente e funcional no React. Alta prioridade pois afeta UX diretamente na página mais usada da plataforma.

─────────────────────────────────────────────────────────────────

## ⚠️ ALERTA VUETIFY DEFAULTS — Para dev / ClaudeCode / Cursor

Causa raiz sistêmica: Os Issues abaixo não são erros isolados — são causados por
defaults implícitos do Vuetify que divergem do DS LIA (React/Replit = fonte da verdade).
Corrija localmente E atualize o arquivo vuetify.ts (global defaults) para
evitar que os mesmos erros apareçam em features futuras.

### Defaults identificados nesta auditoria

#### v-icon — size ausente
- Vuetify default implícito: 24px (padrão Material Design)
- React/Replit (correto): w-4 h-4 = 16px (padrão DS LIA)
- Impacto visual: 8px a mais em cada ícone — visualmente desproporcional no menu
- Fix local: `<v-icon size="16">mdi-*</v-icon>`
- Fix global (vuetify.ts): `VIcon: { size: '16' }`

#### v-btn — variant ausente
- Vuetify default implícito: elevated (box-shadow visível)
- React/Replit (correto): flat (sem sombra)
- Impacto visual: sombra indevida + altura maior nos botões do sidebar
- Fix local: `<v-btn variant="flat" size="small">`
- Fix global (vuetify.ts): `VBtn: { variant: 'flat', size: 'small' }`

#### v-card — elevation ausente
- Vuetify default implícito: 1 (sombra sutil box-shadow)
- React/Replit (correto): 0 (flat — borda apenas, sem sombra)
- Impacto visual: sombra indevida em cards aninhados no menu
- Fix local: `<v-card elevation="0" class="border border-grey-lighten-3">`
- Fix global (vuetify.ts): `VCard: { elevation: 0 }`

#### v-navigation-drawer — width ausente
- Vuetify default implícito: 256px
- React/Replit (correto): 240px (w-60)
- Impacto visual: 16px de largura extra — layout da página desloca
- Fix local: `:width="240"`
- Fix global (vuetify.ts): `VNavigationDrawer: { width: 240 }`

### Como atualizar o vuetify.ts

```typescript
// ats_front/plugins/vuetify.ts (ou config/vuetify.config.ts)

createVuetify({
  defaults: {
    VIcon:               { size: '16' },
    VTextField:          { density: 'compact', variant: 'outlined' },
    VSelect:             { density: 'compact', variant: 'outlined' },
    VAutocomplete:       { density: 'compact', variant: 'outlined' },
    VBtn:                { variant: 'flat', size: 'small' },
    VCard:               { elevation: 0 },
    VNavigationDrawer:   { width: 240 },
    VTabs:               { density: 'compact' },
  },
})
```

─────────────────────────────────────────────────────────────────

> **Referência:** React/Replit é sempre a fonte da verdade de design.
> Qualquer componente Vue que diverge do React = bug a corrigir.
