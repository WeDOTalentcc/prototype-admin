# TEMPLATE — Saída do script jira-fetch-analyze.py
# Card de exemplo: WT-1637 — Menu Lateral
# Gerado por: python3 scripts/jira-fetch-analyze.py WT-1637
# ─────────────────────────────────────────────────────────────────────────────
# Este arquivo mostra como o card ficará no Jira após rodar o script.
# O conteúdo real será gerado pela IA com base na transcrição e no código.
# ─────────────────────────────────────────────────────────────────────────────


# MENU LATERAL — Auditoria Completa: Visibilidade, Logo e Expansão

Card: WT-1637  |  Gerado em: 21/03/2026

O card reporta três problemas no menu lateral esquerdo da plataforma: (1) o menu
só aparece quando o mouse passa sobre ele (hover), sem ser visível por padrão;
(2) o menu aparece sobreposto ao botão/logo "We Do" de forma incorreta; (3)
partes do menu estão ausentes. A análise consultou o componente React no Replit
(`sidebar.tsx`) e o equivalente Vue no GitHub (`wedo-nuxt/components/ui/menu/sidebar.vue`).

As correções cobrem frontend React, equivalente Vue, e garantem consistência com
o Design System LIA v4.2.1.

🐛 BetterBugs: https://app.betterbug.io/issue/xyz123

─────────────────────────────────────────────────────────────────

## 📁 Arquivos de Referência

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Sidebar principal React (fonte da verdade)
• [Frontend React] plataforma-lia/src/components/ui/sidebar-nav.tsx — Itens de navegação do sidebar
• [Frontend React] plataforma-lia/src/hooks/use-sidebar.ts — Hook de estado colapsado/expandido
• [Vue/GitHub] components/ui/menu/sidebar.vue — Equivalente Vue a ser corrigido
• [Integrações] plataforma-lia/src/lib/auth/session.ts — Sessão do usuário (controla itens de menu)

─────────────────────────────────────────────────────────────────

## ⚙️ Issues de Funcionalidade

Problemas funcionais identificados na transcrição: erros, comportamentos incorretos,
features incompletas, integrações e lógica de IA.

### Issue F01 — Sidebar invisível por padrão (expand-on-hover) [BUG] [Frontend]

O sidebar usa `expand-on-hover` no Vuetify, fazendo com que apareça apenas quando o
cursor passa sobre ele. O comportamento correto (React) é `permanent` — sempre visível,
alternando entre colapsado (64px) e expandido (240px) via botão chevron explícito.

Arquivo: `components/ui/menu/sidebar.vue`

**Código atual:**
```vue
<v-navigation-drawer
  expand-on-hover
  :rail="isRail"
  :rail-width="64"
  v-model="drawer"
>
```

**Sugestão de correção:**
```vue
<v-navigation-drawer
  permanent
  :rail="isRail"
  :rail-width="64"
  :width="240"
  v-model="drawer"
>
```

─────────────────────────────────────────────────────────────────

### Issue F02 — Logo "We Do" sobreposto incorretamente [BUG] [Frontend]

O logo está posicionado dentro do fluxo do drawer e sem z-index correto, causando
sobreposição com o conteúdo quando o drawer abre. No React, o logo é posicionado
`absolute` com z-index superior ao drawer.

Arquivo: `plataforma-lia/src/components/ui/sidebar.tsx`

**Código atual:**
```tsx
<div className="flex items-center p-4">
  <img src="/wedo-logo.png" className="h-8" />
</div>
```

**Sugestão de correção:**
```tsx
<div className="relative flex items-center px-3 py-3 h-14 shrink-0">
  {isCollapsed ? (
    <img src="/we-logo-pequeno.png" className="w-8 h-8 rounded-lg" alt="We" />
  ) : (
    <img src="/wedo-logo.png" className="h-7" alt="WeDoTalent" />
  )}
</div>
```

─────────────────────────────────────────────────────────────────

### Issue F03 — Itens de menu ausentes (seção de filtros de vagas) [INCOMPLETO] [Frontend]

Quando o usuário está na página de Vagas, o sidebar deve exibir filtros expandíveis
(Todas, Ativas, Paralisadas, Concluídas, Canceladas, Por Estágio). Esta seção está
completamente ausente na implementação atual.

Arquivo: `plataforma-lia/src/components/ui/sidebar.tsx`

**Código atual:**
```tsx
// Não existe implementação de filtros contextuais no sidebar
```

**Sugestão de correção:**
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
          <button
            key={f.value}
            onClick={() => setJobFilter(f.value)}
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

─────────────────────────────────────────────────────────────────

## 🎨 Issues de Design (DS LIA v4.2.1)

Problemas visuais e de design system identificados nas funcionalidades mencionadas.
React/Replit = fonte da verdade. Para auditoria de design completa, usar jira-audit-design.py.

### Issue D01 — Border radius dos itens de menu incorreto

Itens do menu usam `rounded-12px` (12px) quando o DS LIA especifica 8px universal.

Arquivo: `components/ui/menu/sidebar.vue`

**Código atual:**
```vue
<v-list-item class="rounded-12px py-2">
```

**Sugestão DS LIA v4.2.1:**
```vue
<v-list-item class="rounded-lg py-2" style="border-radius: 8px;">
```

─────────────────────────────────────────────────────────────────

### Issue D02 — Ícones dos itens com tamanho incorreto (14px vs 16px)

DS LIA v4.2.1 especifica 16px para todos os ícones de navegação.

Arquivo: `components/ui/menu/sidebar.vue`

**Código atual:**
```vue
<Icon :name="item.icon" size="14" />
```

**Sugestão DS LIA v4.2.1:**
```vue
<Icon :name="item.icon" size="16" />
```

─────────────────────────────────────────────────────────────────

## 🗂️ Arquivos a Modificar

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Corrigir posicionamento do logo e adicionar filtros contextuais
• [Frontend React] plataforma-lia/src/hooks/use-sidebar.ts — Garantir que isCollapsed não dependa de hover
• [Vue/GitHub] components/ui/menu/sidebar.vue — Corrigir expand-on-hover, border-radius e tamanho de ícones

─────────────────────────────────────────────────────────────────

## 📋 Action Items

• [ ] [Frontend React] Remover dependência de hover do estado do sidebar — usar botão chevron explícito
• [ ] [Frontend React] Corrigir posicionamento do logo "We Do" (absolute, z-index correto)
• [ ] [Frontend React] Implementar seção de filtros contextuais de vagas no sidebar
• [ ] [Vue] Substituir expand-on-hover por permanent no v-navigation-drawer
• [ ] [Vue] Corrigir largura do drawer expandido para 240px (não 256px default Vuetify)
• [ ] [Vue] Corrigir logo para ser controlado por isRail (não por hover)
• [ ] [Vue] Corrigir border-radius de 12px para 8px nos itens de menu
• [ ] [Vue] Corrigir tamanho dos ícones de 14px para 16px

─────────────────────────────────────────────────────────────────

## ✅ Critérios de Aceite

• [Sidebar] Menu visível permanentemente sem precisar de hover (colapsado ou expandido)
• [Sidebar] Alternância colapsado ↔ expandido via botão chevron explícito
• [Logo] Logo "We Do" não sobrepõe nenhum elemento ao expandir o menu
• [Logo] Logo pequeno (icone) quando colapsado, logo completo quando expandido
• [Logo] Transição controlada pelo estado isRail/isCollapsed, não por hover
• [Filtros] Seção de filtros de vagas aparece no sidebar quando usuário está em /vagas
• [Filtros] Filtros expandem/colapsam com animação via chevron
• [Filtros] Filtro ativo destacado com bg-gray-100 + font-semibold
• [Design] Border radius dos itens: 8px (rounded-md / rounded-lg)
• [Design] Ícones dos itens: 16px (w-4 h-4)
• [Design] Largura expandido: exatamente 240px
• [Design] Largura colapsado: exatamente 64px
• [Vue] v-navigation-drawer com permanent (sem expand-on-hover)
• [Vue] Vuetify defaults atualizados no vuetify.ts (VIcon: 16px, VBtn: flat)
