# React → Vue Bridge — Portability Assessment

**Sprint:** F2-6  
**Data:** 2026-03-30  
**Componente piloto:** `sidebar.tsx` → `Sidebar.vue`  
**Autor:** LIA Platform Engineering

---

## Objetivo

Avaliar a portabilidade da plataforma de React (Next.js 14) para Vue 3, usando o componente `Sidebar` como caso de referência. Este documento define o contrato de interfaces, o mapeamento de primitivas e o roteiro de migração incremental sem breaking changes.

---

## 1. Estrutura de Arquivos Criada (Sprint F2-6)

```
src/lib/sidebar/
├── sidebar.types.ts       ← Interfaces framework-agnósticas (dados puros)
└── useSidebarState.ts     ← Hook React (lógica de estado extraída)

src/components/
└── sidebar.tsx            ← Atualizado: importa de lib/sidebar/
```

### Princípio de Design

A lógica de estado foi **completamente desacoplada da renderização**:
- `sidebar.types.ts` contém apenas tipos TypeScript — zero dependências de framework
- `useSidebarState.ts` contém a lógica de estado — apenas React hooks
- `sidebar.tsx` contém apenas JSX e event handlers de UI

---

## 2. Mapeamento React → Vue 3

### 2.1 State Management

| React (`useSidebarState.ts`) | Vue 3 (equivalente) | Notas |
|---|---|---|
| `useState(false)` | `ref(false)` | 1:1 mapping |
| `useState(256)` | `ref(256)` | 1:1 mapping |
| `useMemo(() => ..., [deps])` | `computed(() => ...)` | Sem deps array em Vue |
| `useCallback(() => ..., [deps])` | Função plain ou `computed` | Vue reatividade automática |
| `useEffect(() => {}, [])` | `onMounted(() => {})` | Mount guard |
| `useEffect(() => {}, [dep])` | `watch(dep, () => {})` | Watchers explícitos |
| `useEffect cleanup return` | `onUnmounted(() => {})` | Event listener cleanup |

### 2.2 Props e Emits

| React (`SidebarProps`) | Vue 3 | Código Vue |
|---|---|---|
| Props via desestruturação | `defineProps<SidebarProps>()` | Mesma interface `SidebarProps` |
| Callbacks nas props (`onNavigate`) | `defineEmits<SidebarEmits>()` | Interface `SidebarEmits` no types |
| `children` (não usado) | `<slot>` | N/A para Sidebar |

### 2.3 Componentes Filhos Memoizados

| React | Vue 3 |
|---|---|
| `React.memo(Component)` | `defineComponent` com reatividade automática |
| `React.memo` + props comparison | Props reativas — Vue não re-renderiza sem mudança |
| `displayName = 'MenuItem'` | `name: 'MenuItem'` no options ou `__name` automático |

### 2.4 Renderização Condicional e Listas

| React (JSX) | Vue 3 (Template) |
|---|---|
| `{condition && <Comp />}` | `<Comp v-if="condition" />` |
| `items.map(i => <Item key={i.id} />)` | `<Item v-for="i in items" :key="i.id" />` |
| `className={cn(...)}` | `:class="[..., condition && 'class']"` |
| `style={{width: dynamicWidth}}` | `:style="{ width: dynamicWidth }"` |

---

## 3. SidebarState — Conversão para Vue Composable

```typescript
// React (atual) — src/lib/sidebar/useSidebarState.ts
export function useSidebarState(): UseSidebarStateReturn {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const shouldShowContent = useMemo(
    () => !isCollapsed || isTemporaryExpanded,
    [isCollapsed, isTemporaryExpanded]
  )
  // ...
}
```

```typescript
// Vue 3 (target) — src/composables/useSidebarState.ts
export function useSidebarState() {
  const isCollapsed = ref(false)
  const shouldShowContent = computed(
    () => !isCollapsed.value || isTemporaryExpanded.value
  )
  // ...
  return { isCollapsed, shouldShowContent, ... }
}
```

**Observação:** A interface de retorno `UseSidebarStateReturn` é idêntica nas duas versões — apenas a implementação interna muda. `sidebar.tsx` e `Sidebar.vue` consomem exatamente o mesmo contrato.

---

## 4. Tipos Compartilhados — O que já é agnóstico

Os seguintes tipos em `sidebar.types.ts` são **100% compatíveis com Vue 3** sem modificação:

- `SidebarProps` → `defineProps<SidebarProps>()`
- `SidebarState` → `reactive<SidebarState>()`
- `SidebarComputed` → documentação de `computed()` refs
- `SidebarEmits` → `defineEmits<SidebarEmits>()`
- `SIDEBAR_STORAGE_KEYS` → constante compartilhada
- `SIDEBAR_DEFAULTS` → constante compartilhada

**Única exceção:** `icon: React.ElementType` nos tipos `MenuItemType` e `JobFilterItemType`.  
Em Vue 3, substituir por `icon: Component` (importado de `vue`).

```diff
- import type { ComponentType } from "react"  // React.ElementType
+ import type { Component } from "vue"

  export interface MenuItemType {
-   icon: React.ElementType
+   icon: Component
    label: string
    // ... resto igual
  }
```

---

## 5. Dependências Externas — Compatibilidade

| Dependência | Uso no Sidebar | Vue 3 Equivalente | Compatível? |
|---|---|---|---|
| `lucide-react` | Ícones | `lucide-vue-next` | ✓ Sim, mesmos nomes |
| `@/lib/utils` (cn) | className merge | Manter (utilitário puro) | ✓ Sim |
| `@/hooks/use-recent-items` | Tipo `RecentItem` | Converter para composable | Parcial |
| `@/utils/license-manager` | `hasModuleAccess()` | Manter (função pura) | ✓ Sim |
| `@/components/ui/button` | Button component | Portável ou shadcn-vue | Parcial |
| `@/components/theme-toggle` | ThemeToggle | Portável | Parcial |
| `@/components/lia-tips-modal` | LIATipsModal | Requer conversão | Não |
| `next/image` | Image otimizada | `<img>` ou Nuxt `<NuxtImg>` | Não |
| localStorage | Persistência | Manter (Web API) | ✓ Sim |

**Score de portabilidade do Sidebar:** 6/10 dependências são portáveis sem mudança.

---

## 6. Roteiro de Migração Incremental

### Fase 1 — Fundação (concluída no F2-6)
- [x] Extrair `sidebar.types.ts` com interfaces agnósticas
- [x] Extrair `useSidebarState.ts` com toda a lógica de estado
- [x] `sidebar.tsx` importa de `lib/sidebar/` — sem quebra de comportamento

### Fase 2 — Composable Vue (próxima sprint)
- [ ] Criar `src/composables/useSidebarState.ts` (Vue) com mesma interface
- [ ] Criar `Sidebar.vue` com `<template>` e `<script setup lang="ts">`
- [ ] Substituir `lucide-react` por `lucide-vue-next` nas importações de ícones
- [ ] Adaptar `MenuItemType.icon: React.ElementType` → `Component`

### Fase 3 — Componentes de UI
- [ ] Portabilidade de `Button`, `ThemeToggle` para Vue
- [ ] Substituir `next/image` por `<img>` ou `<NuxtImg>`
- [ ] Converter `LIATipsModal` para Vue

### Fase 4 — Validação e Paridade
- [ ] Testes E2E cobrindo collapse, hover-expand, resize, Ctrl+B
- [ ] Visual regression com screenshots (Playwright)
- [ ] Verificar persistência localStorage cross-framework

---

## 7. Estimativa de Esforço

| Fase | Esforço | Risco |
|---|---|---|
| Fase 1 (concluída) | 2h | Baixo |
| Fase 2 (composable + template) | 4h | Médio |
| Fase 3 (componentes UI) | 8h | Alto (next/image, modais) |
| Fase 4 (testes) | 4h | Médio |
| **Total** | **~18h** | **Médio** |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| `next/image` não existe em Vue | Alta | Usar `<img>` com lazy loading manual |
| Comportamento de SSR diferente (`"use client"`) | Média | `isMounted` guard já presente no hook |
| Gerenciamento de estado global (contexts) | Média | Analisar em sprint dedicada |
| Quebra de comportamento de resize | Baixa | Lógica centralizada em `useSidebarState` |

---

## 9. Conclusão

O componente `Sidebar` está **pronto para migração incremental** para Vue 3. A extração do hook `useSidebarState` e dos tipos agnósticos em `sidebar.types.ts` elimina a maior barreira de portabilidade (estado acoplado ao JSX). O esforço restante é principalmente substituição de primitivas de renderização (JSX → template) e troca de bibliotecas de componentes específicas do React.

A abordagem de **"extrair lógica primeiro, migrar renderização depois"** permite que React e Vue coexistam durante a transição sem nenhum breaking change.
