# TEMPLATE — Saída do script jira-fetch-analyze.py
# Card de exemplo: WT-1637 — Menu Lateral
# Gerado por: python3 scripts/jira-fetch-analyze.py WT-1637 --vue-file components/ui/menu/sidebar.vue
# ─────────────────────────────────────────────────────────────────────────────
# Escopo: Funcionalidade + Design (todos os layers)
# Inclui: ANTES/DEPOIS React + Vue, Vuetify defaults, bloco vuetify.ts
# ─────────────────────────────────────────────────────────────────────────────


# MENU LATERAL — Auditoria Completa: Funcionalidade + Design DS LIA v4.2.1

Card: WT-1637  |  Gerado em: 21/03/2026

O card reporta três problemas no menu lateral: (1) menu visível apenas no hover — sem ser
permanente por padrão; (2) logo "We Do" sobrepondo elementos ao expandir; (3) seção de
filtros de vagas ausente. A análise consultou o componente React no Replit (sidebar.tsx),
o equivalente Vue no GitHub (sidebar.vue) e o hook de estado (use-sidebar.ts).

Cada issue inclui código React atual e Vue ANTES/DEPOIS concreto. A seção de
Vuetify Defaults aponta a causa raiz sistêmica e entrega o bloco pronto do vuetify.ts.

🐛 BetterBugs: https://app.betterbug.io/issue/xyz123

─────────────────────────────────────────────────────────────────

## 📁 Arquivos de Referência

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Sidebar principal (fonte da verdade)
• [Frontend React] plataforma-lia/src/hooks/use-sidebar.ts — Hook de estado colapsado/expandido
• [Frontend React] plataforma-lia/src/components/ui/sidebar-nav.tsx — Itens de navegação
• [Vue/GitHub] components/ui/menu/sidebar.vue — Equivalente Vue a ser corrigido
• [Integrações] plataforma-lia/src/lib/auth/session.ts — Sessão (controla itens de menu)

─────────────────────────────────────────────────────────────────

## ⚙️ Issues de Funcionalidade

Problemas funcionais identificados na transcrição: erros, comportamentos incorretos,
features incompletas, integrações e lógica de IA. Cada issue inclui código React
(Replit) e Vue (GitHub) com ANTES e DEPOIS concretos.

### Issue F01 — Sidebar invisível por padrão (expand-on-hover) [BUG] [Frontend]

O sidebar usa `expand-on-hover` no Vuetify, aparecendo apenas quando o cursor passa
por cima. O comportamento correto (React) é `permanent` — sempre visível, alternando
entre colapsado (64px) e expandido (240px) via botão chevron explícito.

Arquivo React: `plataforma-lia/src/components/ui/sidebar.tsx`

**Código React atual:**
```tsx
// React — usa shadcn Sheet/Collapsible — sidebar sempre visível no DOM
// Alteração via estado isCollapsed, nunca via hover
const { isCollapsed, setIsCollapsed } = useSidebar()

return (
  <aside
    className={cn(
      "relative flex flex-col h-screen border-r border-gray-200 transition-all duration-200",
      isCollapsed ? "w-16" : "w-60"
    )}
  >
```

**Sugestão React:**
```tsx
// Sem alteração necessária — React já está correto
// Garantir que isCollapsed nunca seja controlado por onMouseEnter/onMouseLeave
```

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue — ANTES (incorreto):**
```vue
<v-navigation-drawer
  expand-on-hover
  :rail="isRail"
  :rail-width="64"
  v-model="drawer"
  @mouseenter="isHovered = true"
  @mouseleave="isHovered = false"
>
```

**Vue — DEPOIS (corrigido):**
```vue
<v-navigation-drawer
  permanent
  :rail="isRail"
  :rail-width="64"
  :width="240"
  v-model="drawer"
>
<!-- Remover @mouseenter e @mouseleave do template -->
<!-- Remover isHovered do estado e de todos os computed -->
```

─────────────────────────────────────────────────────────────────

### Issue F02 — Logo "We Do" sobreposto incorretamente [BUG] [Frontend]

O logo está posicionado como item de lista dentro do drawer, sem controle correto por
estado. No React, o logo alterna entre pequeno (colapsado) e completo (expandido)
controlado exclusivamente pelo estado `isCollapsed`, sem qualquer lógica de hover.

Arquivo React: `plataforma-lia/src/components/ui/sidebar.tsx`

**Código React atual:**
```tsx
<div className="relative flex items-center px-3 py-3 h-14 shrink-0">
  {isCollapsed ? (
    <img src="/we-logo-pequeno.png" className="w-8 h-8 rounded-lg" alt="We" />
  ) : (
    <img src="/wedo-logo.png" className="h-7" alt="WeDoTalent" />
  )}
</div>
```

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue — ANTES (incorreto):**
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

<!-- computed problemático — depende de hover -->
const showOnOpenNavigation = computed(() => isHovered.value || !isRail.value)
```

**Vue — DEPOIS (corrigido):**
```vue
<div class="d-flex align-center px-3 py-3" style="height: 56px;">
  <nuxt-link to="/user/dashboard">
    <img
      v-if="isRail"
      src="/we-logo-pequeno.png"
      alt="We"
      style="width: 32px; height: 32px; border-radius: 8px;"
    />
    <img
      v-else
      src="/wedo-logo.png"
      alt="WeDoTalent"
      style="height: 28px;"
    />
  </nuxt-link>
</div>

<!-- Remover showOnOpenNavigation — usar isRail diretamente -->
```

─────────────────────────────────────────────────────────────────

### Issue F03 — Filtros de vagas contextuais ausentes no sidebar [INCOMPLETO] [Frontend]

Quando o usuário navega em /vagas, o sidebar deve exibir filtros expansíveis
(Todas, Ativas, Paralisadas, Concluídas, Canceladas, Por Estágio). Esta seção existe
no React e está completamente ausente no Vue.

Arquivo React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`

**Código React atual:**
```tsx
{isJobsPage && !isCollapsed && (
  <div className="px-3 py-2">
    <button
      onClick={() => setFiltersOpen(!filtersOpen)}
      className="flex items-center justify-between w-full text-[13px] text-gray-500"
    >
      <span className="font-medium">Filtros de Vagas</span>
      <ChevronDown className={cn("w-4 h-4 transition-transform", filtersOpen && "rotate-180")} />
    </button>
    {filtersOpen && (
      <nav className="mt-1 space-y-0.5">
        {JOB_FILTERS.map(f => (
          <button key={f.value} onClick={() => setJobFilter(f.value)}
            className={cn(
              "flex items-center gap-2 w-full px-2 py-1.5 text-[13px] rounded-md",
              jobFilter === f.value ? "bg-gray-100 font-semibold" : "text-gray-600 hover:bg-gray-50"
            )}
          >
            <f.icon className="w-4 h-4" />
            {f.label}
            <span className="ml-auto text-xs text-gray-400">{f.count}</span>
          </button>
        ))}
      </nav>
    )}
  </div>
)}
```

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue — ANTES (incorreto):**
```vue
<!-- Não existe implementação de filtros contextuais de vagas -->
```

**Vue — DEPOIS (corrigido):**
```vue
<template v-if="isJobsPage && !isRail">
  <v-divider class="my-2" />
  <div class="px-4 py-2">
    <button
      @click="isFiltersExpanded = !isFiltersExpanded"
      class="d-flex align-center justify-space-between w-100"
      style="font-size: 13px; line-height: 1.25;"
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
      class="rounded-lg"
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

<script setup>
// Adicionar ao setup:
const isFiltersExpanded = ref(false)
const currentJobFilter = ref('todas')
const isJobsPage = computed(() => route.path.startsWith('/vagas'))
const jobFilterItems = [
  { value: 'todas', label: 'Todas', icon: 'lucide-list', count: 24 },
  { value: 'ativas', label: 'Ativas', icon: 'lucide-circle-check', count: 18 },
  { value: 'paralisadas', label: 'Paralisadas', icon: 'lucide-pause', count: 3 },
  { value: 'concluidas', label: 'Concluídas', icon: 'lucide-check-circle-2', count: 2 },
  { value: 'canceladas', label: 'Canceladas', icon: 'lucide-x-circle', count: 1 },
]
</script>
```

─────────────────────────────────────────────────────────────────

## 🎨 Issues de Design (DS LIA v4.2.1)

Problemas visuais identificados nos elementos mencionados na transcrição.
Cada issue mapeia ANTES (Vue atual incorreto) → DEPOIS (Vue corrigido conforme DS LIA).
React/Replit = fonte da verdade absoluta.
Para auditoria de design ainda mais aprofundada, usar jira-audit-design.py.

### Issue D01 — Border radius dos itens incorreto (12px vs 8px)

Itens do menu usam classe `rounded-12px` (12px custom). DS LIA v4.2.1 exige 8px universal.

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-list-item
  v-for="item in menuItems"
  class="rounded-12px py-2"
>
```

**deve ficar assim — React/DS LIA:**
```vue
<v-list-item
  v-for="item in menuItems"
  class="rounded-lg py-2"
  style="border-radius: 8px !important;"
>
```

⚠️ rounded-12px viola a regra de 8px universal do DS LIA. Diferença visual de 4px por item — multiplicada por todos os itens de navegação.

─────────────────────────────────────────────────────────────────

### Issue D02 — Ícones dos itens com 14px (deve ser 16px)

DS LIA v4.2.1: todos os ícones de interface SEMPRE 16px (w-4 h-4).

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<Icon :name="item.icon" size="14" customClasses="mx-1" />
```

**deve ficar assim — React/DS LIA:**
```vue
<Icon :name="item.icon" size="16" customClasses="mx-1" />
```

⚠️ 14px vs 16px é sistemático — todos os itens de navegação ficam 2px menores que o esperado pelo DS.

─────────────────────────────────────────────────────────────────

### Issue D03 — Tipografia dos itens sem font-size explícito (13px)

DS LIA v4.2.1: texto de navegação 13px, line-height 1.25. Vuetify usa 14px por padrão.

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-list-item :title="showOnOpenNavigation ? item.label : ''">
  <!-- font-size não especificado → Vuetify aplica 14px -->
</v-list-item>
```

**deve ficar assim — React/DS LIA:**
```vue
<v-list-item
  :title="!isRail ? item.label : ''"
  style="font-size: 13px; line-height: 1.25;"
>
```

⚠️ Diferença de 1px mas sistemática — afeta a densidade visual de toda a navegação.

─────────────────────────────────────────────────────────────────

### Issue D04 — Label de seção MENU com letter-spacing excessivo

DS LIA não usa letter-spacing acima de 0.05em. Valor atual (0.2em) é visualmente muito amplo.

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<p class="f12 text-body-dark font-weight-medium pt-4 pb-3 px-4"
   style="letter-spacing: 0.2em"
   v-if="showOnOpenNavigation">
  MENU
</p>
```

**deve ficar assim — React/DS LIA:**
```vue
<p v-if="!isRail"
   class="text-xs text-grey-darken-1 font-weight-medium pt-4 pb-3 px-4"
   style="letter-spacing: 0.05em;">
  MENU
</p>
```

⚠️ Controlado por `showOnOpenNavigation` (hover-dependent) → deve ser `!isRail` (estado permanente).

─────────────────────────────────────────────────────────────────

### Issue D05 — Largura expandido não especificada (256px default vs 240px DS LIA)

DS LIA: sidebar expandido = 240px. Sem width explícito, Vuetify usa 256px.

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-navigation-drawer
  :rail-width="64"
  :rail="isRail"
  <!-- sem width → Vuetify usa 256px por padrão -->
>
```

**deve ficar assim — React/DS LIA:**
```vue
<v-navigation-drawer
  :rail-width="64"
  :width="240"
  :rail="isRail"
  permanent
>
```

⚠️ 16px de largura extra → layout da página principal desloca 16px para a direita.

─────────────────────────────────────────────────────────────────

## ⚠️ ALERTA VUETIFY DEFAULTS — Para dev / ClaudeCode / Cursor

Causa raiz sistêmica: os problemas abaixo não são erros isolados — são causados por
defaults implícitos do Vuetify que divergem do DS LIA (React/Replit = fonte da verdade).
Corrija localmente E atualize o vuetify.ts (global defaults) para evitar reincidência.

### v-icon — size ausente

- Vuetify default implícito: 24px (Material Design default)
- React/Replit (correto): w-4 h-4 = 16px
- Impacto visual: ícones 8px maiores que o esperado em toda a navegação
- Fix local: `<v-icon size="16">mdi-*</v-icon>`
- Fix global (vuetify.ts): `VIcon: { size: '16' }`

### v-navigation-drawer — width ausente

- Vuetify default implícito: 256px
- React/Replit (correto): 240px (w-60)
- Impacto visual: layout da página desloca 16px para a direita
- Fix local: `:width="240"`
- Fix global (vuetify.ts): `VNavigationDrawer: { width: 240 }`

### v-btn — variant ausente

- Vuetify default implícito: elevated (box-shadow visível)
- React/Replit (correto): flat (sem sombra)
- Impacto visual: botões do toggle e filtros com sombra indevida
- Fix local: `<v-btn variant="flat" size="small">`
- Fix global (vuetify.ts): `VBtn: { variant: 'flat', size: 'small' }`

### v-card — elevation ausente

- Vuetify default implícito: 1 (box-shadow sutil)
- React/Replit (correto): 0 (flat, sem sombra)
- Impacto visual: cards aninhados no menu com sombra indevida
- Fix local: `<v-card elevation="0" class="border border-grey-lighten-3">`
- Fix global (vuetify.ts): `VCard: { elevation: 0 }`

### Como atualizar o vuetify.ts

```typescript
// plugins/vuetify.ts (ou config/vuetify.config.ts)

createVuetify({
  defaults: {
    VIcon:             { size: '16' },
    VTextField:        { density: 'compact', variant: 'outlined' },
    VSelect:           { density: 'compact', variant: 'outlined' },
    VAutocomplete:     { density: 'compact', variant: 'outlined' },
    VBtn:              { variant: 'flat', size: 'small' },
    VCard:             { elevation: 0 },
    VNavigationDrawer: { width: 240 },
    VTabs:             { density: 'compact' },
  },
})
```

─────────────────────────────────────────────────────────────────

## 🗂️ Arquivos a Modificar

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Confirmar que logo usa isCollapsed (não hover)
• [Frontend React] plataforma-lia/src/components/ui/sidebar-nav.tsx — Garantir filtros contextuais de vagas
• [Frontend React] plataforma-lia/src/hooks/use-sidebar.ts — Verificar que isCollapsed nunca depende de hover
• [Vue] components/ui/menu/sidebar.vue — Corrigir permanent, logo, largura, tipografia, border-radius, ícones, letter-spacing
• [Vue] plugins/vuetify.ts — Adicionar defaults globais (VIcon, VBtn, VCard, VNavigationDrawer)

─────────────────────────────────────────────────────────────────

## 📋 Action Items

• [ ] [Vue] Remover expand-on-hover e substituir por permanent no v-navigation-drawer
• [ ] [Vue] Remover isHovered e showOnOpenNavigation — usar isRail diretamente
• [ ] [Vue] Adicionar :width="240" explícito no v-navigation-drawer
• [ ] [Vue] Corrigir logo para usar isRail (não hover/showOnOpenNavigation)
• [ ] [Vue] Implementar seção de filtros contextuais de vagas no sidebar
• [ ] [Vue] Corrigir border-radius de 12px para 8px nos itens de menu
• [ ] [Vue] Corrigir tamanho dos ícones de 14px para 16px
• [ ] [Vue] Adicionar font-size: 13px e line-height: 1.25 nos itens
• [ ] [Vue] Corrigir letter-spacing da label MENU de 0.2em para 0.05em
• [ ] [Vue/Global] Atualizar vuetify.ts com defaults: VIcon(16px), VBtn(flat), VCard(0), VNavigationDrawer(240px)
• [ ] [React] Verificar que use-sidebar.ts não tem lógica de hover residual

─────────────────────────────────────────────────────────────────

## ✅ Critérios de Aceite

• [Sidebar] Menu visível permanentemente sem precisar de hover (colapsado ou expandido)
• [Sidebar] Alternância colapsado ↔ expandido via botão chevron explícito — nunca por hover
• [Sidebar] Largura expandido: exatamente 240px (não 256px)
• [Sidebar] Largura colapsado: exatamente 64px
• [Logo] Logo pequeno (32px, rounded-8px) quando colapsado; logo completo (28px) quando expandido
• [Logo] Transição controlada por isRail — sem flash visual no hover
• [Logo] Não sobrepõe nenhum elemento em nenhum estado de transição
• [Filtros] Seção de filtros de vagas aparece no sidebar quando rota começa com /vagas
• [Filtros] Filtros expandem/colapsam com chevron — animação suave
• [Filtros] Filtro ativo: highlighted + font-semibold; inativo: texto gray-600
• [Design] Border radius dos itens de menu: 8px (rounded-lg / style explícito)
• [Design] Ícones de navegação: 16px em todos os itens
• [Design] Font-size dos itens de navegação: 13px, line-height 1.25
• [Design] Label MENU: letter-spacing 0.05em (não 0.2em)
• [Vue/Global] vuetify.ts atualizado com todos os defaults DS LIA
• [Vue/Global] Nenhum novo componente introduce variante incorreta do Vuetify

─────────────────────────────────────────────────────────────────

> Referência: React/Replit é sempre a fonte da verdade de design e funcionalidade.
> Para auditoria de design exclusiva e mais completa, usar jira-audit-design.py.
