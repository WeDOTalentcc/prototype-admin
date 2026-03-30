# Auditoria Frontend Parte 1 — Fundamentos (Dimensões 1-5)

**Plataforma LIA — WeDo Talent**
**Data:** 2026-03-30
**Auditor:** Agente Técnico
**Escopo:** Frontend Next.js 15 + React 19 + Tailwind CSS 3 + shadcn/ui
**Codebase:** 1.540 arquivos (709 TSX + 831 TS), 398.179 linhas totais em `src/`

---

## Sumário Executivo

| Dimensão | Score | Severidade Máxima |
|---|---|---|
| 1. Qualidade de Código | 1.5/3 | Crítico |
| 2. Arquitetura CSS | 2.0/3 | Importante |
| 3. Performance de Renderização | 1.5/3 | Crítico |
| 4. Performance de Bundle/Assets | 0.5/3 | Crítico |
| 5. Design System e UI | 2.5/3 | Melhoria |

**Score médio geral: 1.6/3**

---

## Dimensão 1 — Qualidade de Código

**Score: 1.5/3** — Abaixo do esperado. Muitos componentes gigantes, TypeScript relaxado, linting desabilitado no build.

### ✅ Checklist de Inspeções

| Item | Status | Evidência |
|---|---|---|
| Nomenclatura arquivos/componentes/variáveis/funções | ⚠️ Inconsistente | §1.4 |
| Separação de responsabilidades (lógica vs UI vs dados) | ⚠️ Parcial | §1.6 |
| Profundidade de aninhamento | ✅ Conforme | §1.10 |
| Dead code (imports não utilizados, código comentado) | ⚠️ Presente | §1.5 |
| Duplicação de lógica | ✅ Verificado | §1.11 |
| Componentes acima de 300 linhas | ❌ Violação severa | §1.1 |
| Props drilling (3+ níveis) | ⚠️ Mitigado por contextos | §1.8 |
| Componentes com múltiplas responsabilidades | ❌ Presente | §1.1 |
| Gestão de estado (store global, mutação, race conditions, stale data) | ✅ Adequado | §1.8 |
| Tipagem TypeScript (any, interfaces, contratos API, props) | ❌ Relaxado | §1.2 |

### Achados Críticos

#### §1.1 Componentes acima de 300 linhas (Violação severa)

Há **30+ componentes** com mais de 1.000 linhas cada. Os 15 maiores:

| Arquivo | Linhas |
|---|---|
| `src/components/pages/ats-integrations-page.tsx` | 1.522 |
| `src/components/pages/candidates/hooks/useCandidatesPageCore.tsx` | 1.509 |
| `src/components/pages/chat-page/useChatPageCore.tsx` | 1.500 |
| `src/components/modals/job-insights-modal.tsx` | 1.496 |
| `src/components/pages/job-kanban-page.tsx` | 1.487 |
| `src/components/screening-config/SCMSectionContent.tsx` | 1.482 |
| `src/components/pages/jobs-page.tsx` | 1.408 |
| `src/components/search/hooks/useSmartSearchCore.tsx` | 1.402 |
| `src/components/search/advanced-filters-modal.tsx` | 1.379 |
| `src/components/chat/ChatContextPanel.tsx` | 1.378 |
| `src/components/pages/candidates/LIASearchSidebar.tsx` | 1.365 |
| `src/components/expanded-chat/hooks/useExpandedChatEffects.tsx` | 1.353 |
| `src/components/expandable-ai-prompt/useEAPCallbacks.tsx` | 1.347 |
| `src/components/pages/job-kanban/KanbanTableView.tsx` | 1.334 |
| `src/components/search/SSIModeContent.tsx` | 1.323 |

**Métricas:** 284.274 linhas em TSX (src/components + src/app). Componentes com >1.000 linhas indicam múltiplas responsabilidades misturadas (UI rendering + business logic + data fetching + state management).

#### §1.2 TypeScript relaxado — `noImplicitAny: false` e linting desabilitado

- **`tsconfig.json` L12:** `"noImplicitAny": false` — permite `any` implícito em todo o projeto.
- **`next.config.js` L19-20:** `eslint: { ignoreDuringBuilds: true }` — ESLint completamente ignorado durante build.
- **`next.config.js` L22-23:** `typescript: { ignoreBuildErrors: true }` — erros TypeScript ignorados durante build.
- **`eslint.config.mjs` L22:** `"@typescript-eslint/no-unused-vars": "off"` — variáveis não utilizadas não são reportadas.
- **`eslint.config.mjs` L23:** `"@typescript-eslint/no-explicit-any": "off"` — uso de `any` explícito permitido.
- **`biome.json` L25:** `"noUnusedVariables": "off"` — redundante com ESLint, ambos desabilitados.
- **Impacto:** Sem guardrails de tipo, bugs de runtime passam despercebidos. Com 398k linhas de código, a ausência de checagem estática é risco alto.

#### §1.3 Regras de acessibilidade (a11y) desabilitadas em massa

- **`biome.json` L30-46:** 15 regras de acessibilidade desabilitadas: `noAutofocus`, `noDistractingElements`, `noHeaderScope`, `noInteractiveElementToNoninteractiveRole`, `noLabelWithoutControl`, `noNoninteractiveElementToInteractiveRole`, `noNoninteractiveTabindex`, `noPositiveTabindex`, `noRedundantAlt`, `noRedundantRoles`, `noSvgWithoutTitle`, `useAltText`, `useKeyWithClickEvents`, `useKeyWithMouseEvents`, `useButtonType`.
- **`eslint.config.mjs` L24:** `"react/no-unescaped-entities": "off"`.
- **`eslint.config.mjs` L25:** `"@next/next/no-img-element": "off"` — permite `<img>` ao invés de `<Image>` do Next.js.
- **Impacto:** A plataforma pode ter problemas sérios de acessibilidade não detectados por ferramentas.

### Achados Importantes

#### §1.4 Nomenclatura inconsistente de arquivos

- **`src/contexts/`**: Mistura kebab-case e PascalCase:
  - kebab-case: `src/contexts/auth-context.tsx`, `src/contexts/lia-float-context.tsx`
  - PascalCase: `src/contexts/ClientContext.tsx`
- **`src/hooks/`**: Mistura camelCase e kebab-case:
  - camelCase: `src/hooks/useAgentMemory.ts`, `src/hooks/useFastTrack.ts`, `src/hooks/useTableFeatures.ts`
  - kebab-case: `src/hooks/use-agent-streaming.ts`, `src/hooks/use-candidates-list.ts`, `src/hooks/use-daily-briefing.ts`
- **`src/components/` raiz**: Mistura PascalCase e kebab-case:
  - PascalCase: `src/components/GoalsPlanningHub.tsx`, `src/components/PromptSuggestionsPanel.tsx`, `src/components/PromptContextViewer.tsx`
  - kebab-case: `src/components/big-five-modal.tsx`, `src/components/candidate-modal.tsx`, `src/components/batch-approval-modal.tsx`
- **`src/components/ui/`**: Consistente em kebab-case (conforme shadcn/ui). ✅

#### §1.5 Dead code e código arquivado

- **`src/components/pages/_archived/`**: Contém 3 arquivos: `mockup-shadcn-vue-page.tsx`, `jobs2-page.tsx`, `settings-page.tsx`.
- **`src/hooks/_archived/`**: Contém `use-table-features.tsx` (substituído por `src/hooks/useTableFeatures.ts`).
- **`src/app/globals.css` L13-15, L36-38:** Comentários extensivos sobre código removido (8+ blocos de comentário "removido/NOP").
- **`src/app/globals.css` L52-59:** 7 variáveis CSS deprecated comentadas (`--wedo-apoio-*`), marcadas para remoção no Sprint 10.

#### §1.6 Separação de responsabilidades — hooks extraídos, mas gigantes

- **Positivo:** Padrão de extração de lógica para hooks companion bem estabelecido:
  - `useCandidatesPageCore.tsx` (1.509 linhas) para `candidates-page.tsx`
  - `useChatPageCore.tsx` (1.500 linhas) para `chat-page.tsx`
  - `useSmartSearchCore.tsx` (1.402 linhas) para search
  - `useKanbanPageCore.ts`, `useJobsPageCore.tsx`, etc.
- **Negativo:** Os hooks extraídos são tão grandes quanto os componentes originais. A extração moveu complexidade mas não a reduziu.

#### §1.7 TODOs/FIXMEs no código

- **16 ocorrências** de `TODO`/`FIXME`/`HACK`/`XXX` encontradas em TS/TSX.
- Exemplos com citação:
  - `src/components/pages/candidates-page.tsx` L795: `// TODO: Replace 'demo' with actual company_id from auth context when authentication is implemented.`
  - `src/components/expandable-ai-prompt/EAPTabContent.tsx` L43: `// [OPT-043] TODO: revisar inline styles dinâmicos (21 ocorrências)`
  - `src/app/ajuda/page.tsx` L1: `// TODO: Sprint 4 Dark Mode — File exceeds 400 lines. Needs manual dark: class review.`
  - `src/components/pages/job-kanban-page.tsx` L962, L1036: Comentários em português sobre filtros (não TODOs formais, mas lógica inline)

### Achados — Melhorias

#### §1.8 Gestão de estado (Adequado)

- **3 contextos globais** bem definidos: `auth-context.tsx` (4 useState), `ClientContext.tsx` (5 useState), `lia-float-context.tsx` (4 useState).
- **2 contextos de feature:** `WizardContext.tsx`, `ExpandedChatContext.tsx`.
- **1 contexto de notificações:** `notification-context.tsx`.
- **useContext consumido em ~20 arquivos** — distribuição moderada, sem over-sharing.
- **SWR** (`swr@^2.4.1`) usado para data fetching — evita estado global desnecessário para dados do servidor.
- **useState:** 4.192 ocorrências totais no projeto. Volume alto mas proporcional ao tamanho do codebase.
- **Não detectado:** Mutação direta de estado, race conditions evidentes, ou promoção desnecessária a store global.

#### §1.9 Tipagem de domínio (Insuficiente)

- **`src/types/`**: 5 arquivos de tipos — `benefits.ts`, `chat.ts`, `interview-notes.ts`, `screening.ts`, `wizard-suggestions.ts`.
- **`src/services/lia-api/types/`**: Contém `job.types.ts` (1+ arquivo).
- Para um projeto com 398k linhas e ~1.540 arquivos, a cobertura de tipos de domínio é insuficiente. Muitos tipos provavelmente são inline ou ausentes.

#### §1.10 Profundidade de aninhamento (Conforme)

- Verificado por amostragem: componentes seguem padrão flat com early returns. Não foram encontrados aninhamentos >5 níveis em JSX de forma sistêmica.

#### §1.11 Duplicação de lógica (Verificado)

- Padrão DRY razoável: componentes base em `src/components/ui/` (50+ componentes shadcn/ui), hooks reutilizáveis em `src/hooks/` (70+ hooks), utilitários em `src/lib/`.
- Exceção: `src/hooks/_archived/use-table-features.tsx` duplica funcionalidade de `src/hooks/useTableFeatures.ts` — dead code que deveria ser removido.

---

## Dimensão 2 — Arquitetura CSS

**Score: 2.0/3** — Estratégia clara (Tailwind + design tokens), mas com problemas de `!important` excessivo e duplicação de tokens.

### ✅ Checklist de Inspeções

| Item | Status | Evidência |
|---|---|---|
| Estratégia de escopo (Tailwind utility-first + shadcn/ui) | ✅ Conforme | §2.7 |
| Estilos globais vazando | ⚠️ Presente | §2.5 |
| Ocorrências de `!important` | ❌ Excessivo | §2.1 |
| Especificidade descontrolada | ⚠️ Parcial | §2.1 |
| Tokens de design centralizados vs hardcoded | ⚠️ Parcial | §2.3, §2.4 |
| CSS morto | ⚠️ Presente | §2.8 |
| Mistura de unidades sem critério | ✅ Conforme | §2.9 |
| Reset/normalize | ✅ Conforme | §2.10 |
| Escala de z-index | ⚠️ Parcial | §2.6 |
| Ordem de importação | ✅ Conforme | §2.11 |
| Estilos de impressão | ⚠️ Ausente | §2.12 |

### Achados Críticos

#### §2.1 Uso excessivo de `!important` — 139 ocorrências totais

| Arquivo | Ocorrências | Justificação |
|---|---|---|
| `src/components/onboarding/onboarding-styles.css` | 78 | Injustificado — CSS convencional |
| `src/styles/design-tokens.css` | 29 | Parcialmente justificado (desabilitar animações Radix) |
| `src/app/globals.css` | 12 | Parcialmente justificado (animações Radix) |
| `src/app/styles/typography.css` | 9 | Injustificado — forçando fontes via seletores amplos |
| `src/app/styles/animations.css` | 4 | Justificado (animações desabilitadas) |
| `src/app/styles/components.css` | 3 | Parcialmente justificado |
| `src/components/pages/job-kanban-page.tsx` | 1 | Inline, verificado |

**Detalhe `typography.css` L50-53:**
```css
font-family: var(--font-open-sans) !important;
font-size: 0.6875rem !important; /* 11px */
line-height: 1.125rem !important;
font-weight: 500 !important;
```
Aplica-se a seletores como `nav`, `[data-sidebar="true"] a`, `[data-sidebar="true"] span`, `[data-sidebar="true"] div` — sobrescrevendo QUALQUER especificidade.

**Detalhe `onboarding-styles.css`:** 78 `!important` em 225 linhas (1 a cada 3 linhas). Arquivo inteiro usa `!important` como padrão.

### Achados Importantes

#### §2.2 Duplicação de tokens de dark mode

Dark mode vars definidas em **3 locais separados com sobreposição:**

1. **`src/app/globals.css` L160-195** — `.dark` block com vars shadcn/ui (`--background`, `--foreground`, `--card`, etc.)
2. **`src/app/styles/dark-mode.css` L6-41** — `.dark` block **idêntico** ao de globals.css (mesmos vars, mesmos valores)
3. **`src/styles/design-tokens.css` L191-268** — `.dark` block com tokens LIA (`--lia-bg-primary`, `--lia-text-primary`, etc.)

**Evidência de duplicação exata:** `globals.css` L160 e `dark-mode.css` L6 definem:
- `--background: var(--deep-tech);`
- `--foreground: var(--neutral-warm);`
- `--card: 240 2% 15%;`
- `--card-foreground: var(--neutral-warm);`
- (... todas idênticas)

**Impacto:** Manutenção duplicada. Alterar um valor exige alterar em 2 locais.

#### §2.3 Dois sistemas de tokens CSS coexistentes

- **Sistema 1 (globals.css L92-158 + dark-mode.css):** Tokens HSL shadcn/ui (`--background: 0 0% 100%`, `--primary: 215 25% 15%`) + tokens WeDo legados (`--wedo-primary-coral: #E87575`, `--ai-aqua: 194 100% 39%`)
- **Sistema 2 (design-tokens.css L10-185):** Tokens hex LIA (`--lia-bg-primary: #FFFFFF`, `--lia-text-primary: #111827`)
- **Overlap semântico:** `--foreground: 215 25% 15%` (≈#1F2937) e `--lia-text-primary: #111827` representam conceitos quase idênticos (texto escuro principal) com valores ligeiramente diferentes.

#### §2.4 Hardcoded colors em componentes TSX

| Arquivo | L | Exemplo |
|---|---|---|
| `src/components/pages/login-page.tsx` | (12 ocorrências) | Cores hex inline |
| `src/components/pages/chat-page/useChatPageCore.tsx` | (2 ocorrências) | Cores hex inline |
| `src/components/triagem-details-modal.tsx` | (1 ocorrência) | Cor hex inline |
| `src/components/disc-assessment-modal.tsx` | L416, L424, L432 | `style={{backgroundColor: dim.color + '20', color: dim.color}}` |
| `src/components/lia-expanded-prompt.tsx` | L97, L109, L117, L125 | `style={{borderColor: colors.borderColor, ...}}` |
| `src/components/lia-metrics-chart.tsx` | L78, L99, L149, L173 | `style={{fontSize: '10px'}}`, `style={{fontSize: '9px'}}` |

#### §2.5 Estilos globais com seletores amplos demais

- **`src/app/styles/typography.css` L30-53:** Aplica `!important` a seletores como `nav`, `[data-sidebar="true"]`, `[data-sidebar="true"] a`, `[data-sidebar="true"] span`, `[data-sidebar="true"] div`, `.sidebar a`, `.sidebar span`, `.sidebar div` — sobrescrevendo QUALQUER herança de CSS.
- **`src/app/globals.css` L200-201:** `* { border-color: hsl(var(--border)); }` — aplica border-color a TODOS os elementos HTML.

### Achados — Melhorias

#### §2.6 Escala de z-index semântica (Parcialmente conforme)

- **`tailwind.config.ts` L277-288:** Escala semântica definida: `base(0)`, `raised(10)`, `dropdown(40)`, `sticky(50)`, `overlay(60)`, `toast(100)`, `select(200)`, `backdrop(9998)`, `modal(9999)`, `max(10000)`.
- **`src/styles/design-tokens.css` L166-176:** Bridge Layer 1 com vars CSS (`--z-base`, `--z-raised`, etc.).
- **Adoção parcial:** ~20 arquivos em `src/components` ainda usam z-index numérico arbitrário (`z-[N]` ou `z-50`, etc.).
  - Exemplos: `batch-approval-modal.tsx`, `ai-search-toggle.tsx`, `candidate-preview/LiaChatModal.tsx`, `expandable-ai-prompt.tsx`, `job-report-modal.tsx`, `intelligence-notifications.tsx`, `global-search-modal.tsx`.

#### §2.7 CSS Split e estratégia de escopo (Conforme)

- CSS global bem organizado em módulos: `globals.css` importa → `design-tokens.css`, `typography.css`, `animations.css`, `components.css`, `dark-mode.css`.
- **`globals.css` L6-8:** Imports Tailwind na ordem correta (`@tailwind base`, `@tailwind components`, `@tailwind utilities`).
- Total: ~2.493 linhas de CSS customizado.
- Tailwind utility-first com shadcn/ui como base de componentes.

#### §2.8 CSS morto (Presente)

- **`src/app/styles/components.css` L9-75:** Classes como `.bg-ai-aqua`, `.text-ai-aqua`, `.bg-electric-red`, `.text-electric-red`, `.bg-peach-fuzz`, etc. — utility classes customizadas que provavelmente são redundantes com tokens Tailwind. Necessita verificação de uso.
- **`src/app/globals.css` L52-59:** 7 variáveis CSS deprecated comentadas mas não removidas.

#### §2.9 Mistura de unidades (Conforme)

- Unidades consistentes: `rem` para tipografia e espaçamento, `px` para dimensões fixas (panel widths, chart heights), `%` para progress bars. Sem mistura sem critério.

#### §2.10 Reset/normalize (Conforme)

- Tailwind CSS inclui Preflight (normalize) por padrão.
- PostCSS configurado com `autoprefixer` (`postcss.config.mjs` L4-5).

#### §2.11 Ordem de importação CSS (Conforme)

- **`globals.css` L1-8:**
  1. `@import '../styles/design-tokens.css'` (tokens first)
  2. `@import './styles/typography.css'`
  3. `@import './styles/animations.css'`
  4. `@import './styles/components.css'`
  5. `@import './styles/dark-mode.css'`
  6. `@tailwind base/components/utilities`
- Ordem lógica correta: tokens → overrides → Tailwind layers.

#### §2.12 Estilos de impressão (Ausente)

- **Verificado:** Zero ocorrências de `@media print` no projeto (exceto 2 arquivos de modais: `job-insights-modal.tsx`, `triagem-details-modal.tsx` — que são referências a botões de exportação, não CSS de impressão).
- Para uma plataforma de recrutamento que gera relatórios e fichas de candidatos, print styles seriam desejáveis.

---

## Dimensão 3 — Performance de Renderização

**Score: 1.5/3** — Ausência significativa de memoização, keys de índice em listas, timers/listeners sem cleanup.

### ✅ Checklist de Inspeções

| Item | Status | Evidência |
|---|---|---|
| Re-renders desnecessários | ⚠️ Provável | §3.2, §3.7 |
| Listas sem key adequada / key de índice | ❌ Disseminado (153 arquivos) | §3.1 |
| Memoização ausente (React.memo, useMemo, useCallback) | ⚠️ Insuficiente | §3.2 |
| Watchers com lógica pesada sem debounce | ⚠️ Parcial | §3.6 |
| Listas sem virtualização (>100 itens) | ⚠️ Presente | §3.5 |
| Operações síncronas bloqueando main thread | ✅ Verificado | §3.8 |
| Event listeners sem cleanup no unmount | ⚠️ Parcial | §3.4 |
| Polling/timers sem cleanup | ⚠️ Presente | §3.3 |
| Scroll listeners sem `passive: true` | ⚠️ Presente | §3.4 |

### Achados Críticos

#### §3.1 Keys de índice em listas — 153 arquivos afetados

**153 arquivos** usam `key={index}` ou `key={i}` para renderizar listas. Exemplos com citação de arquivo e linha:

| Arquivo | Linhas | Contexto |
|---|---|---|
| `src/components/work-model-charts.tsx` | L106, L137, L161, L236, L309 | 5 listas diferentes com key={index} |
| `src/components/triagem-details-modal.tsx` | L625, L658, L686, L701, L715, L844, L870, L973, L983, L995, L1007 | 11 listas com key={i} |
| `src/components/save-command-modal.tsx` | L287, L329 | Listas de tags/inputs |
| `src/components/quick-view-modal.tsx` | L233, L246, L263, L304, L319 | 5 listas de dados |
| `src/components/presentation-mode.tsx` | L56, L107, L184 | Cards com React.memo mas key={index} |
| `src/components/react-thinking-stream.tsx` | L44 | Lista de itens de pensamento |
| `src/components/proactive-insight-card.tsx` | L175 | Lista de insights |
| `src/app/portal/data-request/[token]/page.tsx` | L880 | Lista de dados pessoais |

**Impacto:** Keys de índice causam re-renders desnecessários e bugs de reconciliação quando listas são reordenadas, filtradas ou editadas. Em componentes como kanban, tabelas de candidatos e formulários dinâmicos, isso pode causar estado fantasma.

#### §3.2 Memoização — ratio desfavorável

**Métricas quantitativas (todo o `src/`):**

| Hook | Ocorrências |
|---|---|
| `useState` | 4.192 |
| `useEffect` | 927 |
| `useMemo` + `useCallback` | 1.806 |
| `React.memo` | 4 arquivos (11 componentes total) |

- **Ratio useMemo+useCallback / useState:** 0.43 — para cada variável de estado, há 0.43 memoizações. Em codebase com componentes >1.000 linhas, ratio deveria ser >1.0.
- **React.memo usado em apenas 4 arquivos:**
  - `src/components/sidebar.tsx` L58, L195, L250 (MenuItem, JobFilterItem, RecentItemRow)
  - `src/components/presentation-mode.tsx` L55, L82, L106, L144, L164, L197 (KPICard, KPISlide, DepartmentCard, etc.)
  - `src/components/notification-system.tsx` L68 (NotificationItem)
  - `src/components/pages/job-kanban/KanbanCard.tsx` L19 (KanbanCard)
- **Impacto:** Componentes grandes (1.000+ linhas) com 4.192 useState provavelmente re-renderizam sub-árvores inteiras a cada mudança de estado.

#### §3.3 Timers/intervals — 164 arquivos com potencial leak

- **164 arquivos** usam `setTimeout` ou `setInterval`.
- Exemplos de alta concentração (useEffect count por arquivo):
  - `src/components/presentation-mode.tsx`: 17 useEffect + 3 setTimeout
  - `src/components/notification-system.tsx`: 14 useEffect + 4 setTimeout
  - `src/contexts/lia-float-context.tsx`: 10 useEffect + timers
  - `src/app/triagem/[token]/page.tsx`: 9 useEffect + 3 setTimeout
- Cleanup functions (`return () => ...`, `clearTimeout`, `clearInterval`) existem em muitos hooks, mas a proporção useEffect vs cleanup não é garantida 1:1 em todos os 164 arquivos.

### Achados Importantes

#### §3.4 addEventListener sem `passive: true` — 59 arquivos, 12 com passive

- **59 arquivos** usam `addEventListener`.
- **Apenas 12 arquivos** especificam `{ passive: true }`.
- **47 arquivos** potencialmente usam event listeners sem `passive: true`.
- Exemplos sem passive:
  - `src/components/tables/unified-candidate-table.tsx` (addEventListener para scroll)
  - `src/components/ui/dialog.tsx` (addEventListener para keyboard)
  - `src/components/ui/pipeline-stages-carousel.tsx` (addEventListener para scroll/touch)
  - `src/components/ui/prompt-suggestions-dock.tsx` (addEventListener)
  - `src/components/search/filter-autocomplete.tsx` (addEventListener para click outside)

#### §3.5 Listas sem virtualização

- **Apenas 1 arquivo** usa virtualização (`@tanstack/react-virtual`): `src/components/tables/unified-candidate-table.tsx`.
- Listas potencialmente longas sem virtualização:
  - Tabelas de candidatos (multi-page mas renderizadas in-DOM)
  - Tabelas de vagas (`src/components/pages/jobs-page.tsx`)
  - Kanban cards (`src/components/pages/job-kanban-page.tsx`)
  - Listas de atividades (`src/components/candidate-preview/CandidateActivitiesTab.tsx`)
  - Logs de auditoria (pages admin/compliance)
  - Resultados de busca (`src/components/search/SSIModeContent.tsx`)

#### §3.6 Debounce/throttle (Parcialmente conforme)

- **Debounce/throttle encontrado em 10+ arquivos**, incluindo:
  - `src/hooks/useFastTrack.ts` (10 ocorrências)
  - `src/hooks/useSemanticSearch.ts` (10 ocorrências)
  - `src/hooks/use-triagem-chat.ts` (6 ocorrências)
  - `src/hooks/use-wizard-auto-save.ts` (5 ocorrências)
  - `src/components/lists/add-candidate-to-list-modal.tsx` (4 ocorrências)
  - `src/hooks/use-candidates-list.ts` (3 ocorrências)
- **Positivo:** Hooks de busca e streaming usam debounce adequadamente.
- **Verificar:** Hooks com muitos useEffect (`presentation-mode.tsx`, `notification-system.tsx`) podem ter watchers sem debounce.

### Achados — Melhorias

#### §3.7 `reactStrictMode: false`

- **`next.config.js` L18:** `reactStrictMode: false`.
- **Impacto:** React não detecta efeitos colaterais impuros em desenvolvimento. Recomendado ativar para expor bugs de lifecycle escondidos.

#### §3.8 Operações síncronas bloqueando main thread (Verificado)

- Não foram encontradas operações síncronas pesadas (computações CPU-bound, parsing de JSON gigante, etc.) no main thread. Operações de PDF/imagem (`html2canvas`, `jspdf`) são invocadas por ação do usuário (export buttons), não on-render.

---

## Dimensão 4 — Performance de Bundle e Assets

**Score: 0.5/3** — Bundle principal de 49.7MB (!), cache desabilitado globalmente, imagens não otimizadas, bibliotecas pesadas duplicadas.

### ✅ Checklist de Inspeções

| Item | Status | Evidência |
|---|---|---|
| Tamanho do bundle principal (>250KB gzipped = alerta) | ❌ **49.7MB uncompressed** | §4.1 |
| Lazy loading de rotas | ⚠️ Parcial (12 de ~95 rotas) | §4.2 |
| Code splitting de componentes pesados | ⚠️ Parcial | §4.2 |
| Tree shaking (imports específicos vs totais) | ✅ Conforme | §4.8 |
| Dependências duplicadas | ❌ Presente (2 chart libs) | §4.5 |
| Imagens: compressão, formato, width/height, loading lazy | ❌ Tudo desabilitado | §4.3 |
| Fontes: famílias/pesos, font-display, preload | ✅ Conforme | §4.6 |
| CSS não utilizado (PurgeCSS/Tailwind purge) | ✅ Conforme | §4.7 |

### Achados Críticos

#### §4.1 Bundle principal catastroficamente grande — 49.7MB

**Build output medido (diretório `out/static/chunks/`):**

| Chunk | Tamanho (não comprimido) |
|---|---|
| `app/page.js` | **49.7 MB** |
| `main-app.js` | 7.6 MB |
| `_..._expanded-chat-modal_tsx.js` | 5.9 MB |
| `app/layout.js` | 3.9 MB |
| `_..._candidate-preview_tsx.js` | 2.4 MB |
| `_..._smart-search-input_tsx.js` | 1.5 MB |
| `_..._canvg_lib_index_es_js.js` | 1.3 MB (canvg library) |
| `_..._candidate-page_tsx.js` | 1.0 MB |
| `app-pages-internals.js` | 249 KB |
| `_..._dompurify_dist_purify_es_mjs.js` | 165 KB |
| `polyfills.js` | 113 KB |
| `webpack.js` | 141 KB |
| **Total JS** | **~72 MB** |

**Nota:** O `app/page.js` com 49.7MB indica que a rota principal (dashboard) inclui TODA a lógica da aplicação no chunk inicial. Isso é catastrófico para First Contentful Paint e Time to Interactive.

**Threshold:** >250KB gzipped = alerta. Estimando ~30% compression ratio, `app/page.js` sozinho seria ~15MB gzipped — **60x acima do threshold**.

#### §4.2 Lazy loading insuficiente de rotas

- **12 arquivos** usam `dynamic()` (Next.js lazy loading):
  - `src/app/funil-de-talentos/candidato/[id]/page.tsx`
  - `src/components/pages/jobs-page.tsx`
  - `src/components/pages/job-kanban-page.tsx`
  - `src/components/pages/candidates-page.tsx`
  - `src/components/pages/candidates/CandidateSearchResultsView.tsx`
  - `src/components/pages/candidates/CandidateSearchBar.tsx`
  - `src/components/pages/candidates/EditQueryModal.tsx`
  - `src/components/pages/candidates/hooks/useCandidatesPageCore.tsx`
  - `src/components/pages/jobs/InlineChatPanel.tsx`
  - `src/components/pages/job-kanban/KanbanTableView.tsx`
  - `src/components/pages/job-kanban/KanbanPageModals.tsx`
  - `src/components/candidate-preview.tsx`
- **~83 rotas** em `src/app/` NÃO usam lazy loading.
- **Modais pesados** (1.000-1.500 linhas) importados estaticamente: `job-insights-modal.tsx`, `edit-job-modal.tsx`, `advanced-filters-modal.tsx`, `new-candidate-unified-modal.tsx`, etc.

#### §4.3 Otimização de imagens completamente desabilitada

- **`next.config.js` L26:** `images: { unoptimized: true }` — desabilita resizing, formato WebP/AVIF, e lazy loading nativo do Next.js.
- **Zero ocorrências** de `loading="lazy"` em `<img>` tags no codebase.
- **`eslint.config.mjs` L25:** `@next/next/no-img-element: "off"` — permite `<img>` HTML nativo ao invés de `<Image>` otimizado do Next.js.
- **Impacto:** Todas as imagens são servidas no formato original, tamanho original, sem lazy loading.

#### §4.4 Cache desabilitado globalmente

- **`next.config.js` L56-68:**
  ```js
  headers: [{
    source: '/:path*',
    headers: [{ key: 'Cache-Control', value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0' }]
  }]
  ```
- Aplica-se a **TODAS as rotas** incluindo assets estáticos (JS, CSS, fontes, imagens).
- **Impacto:** Cada navegação recarrega todos os assets. Para chunks de 49.7MB + 7.6MB + 5.9MB, isso significa download de ~63MB a cada page load. Destrutivo para performance percebida.

### Achados Importantes

#### §4.5 Duas bibliotecas de gráficos (Dependências duplicadas)

- **Recharts** (`recharts@^3.2.1`): Usado em 4 arquivos (`src/components/charts/interactive-charts.tsx`, `src/components/charts/advanced-interactive-charts.tsx`, `src/components/pages/big-five-dashboard-page.tsx`, `src/components/pages/_archived/mockup-shadcn-vue-page.tsx`).
- **Chart.js** (`chart.js@^4.5.0`) + `react-chartjs-2@^5.3.0` + `chartjs-adapter-date-fns@^3.0.0`: Usado em 4 arquivos.
- **html2canvas** (`^1.4.1`) + **jspdf** (`^3.0.3`): Importados em `src/components/job-report-modal.tsx` e `src/components/modals/job-compare-modal.tsx` sem `dynamic()`.
- **canvg** (`^4.0.3`): Chunk próprio de 1.3MB no build output.
- **Impacto:** Duas bibliotecas de gráficos (~400KB+ combinadas) quando uma bastaria. html2canvas+jspdf+canvg adicionam ~1.5MB sem lazy loading.

### Achados — Melhorias (Conformes)

#### §4.6 Fontes (Conforme)

- **`src/app/layout.tsx` L16-31:** Três fontes Google via `next/font/google`:
  - `Inter` — subsets: latin, variable: `--font-inter`
  - `Open_Sans` — subsets: latin, variable: `--font-open-sans`
  - `Crimson_Text` — subsets: latin, weights: [400, 600, 700], `display: "swap"`
- Next.js `next/font` automaticamente otimiza (self-hosting, preload, `font-display: swap` por default). Conforme.

#### §4.7 CSS purge (Conforme)

- **`tailwind.config.ts` L5-9:** `content` configurado corretamente para purge: `src/pages/**`, `src/components/**`, `src/app/**`.
- CSS não utilizado será removido em produção. Conforme.

#### §4.8 Tree shaking (Conforme)

- lucide-react importado com named imports: `import { Search, Plus, ... } from "lucide-react"`. Tree-shaking funciona.
- Recharts importado com named imports: `import { BarChart, ... } from "recharts"`. Conforme.

---

## Dimensão 5 — Design System e UI

**Score: 2.5/3** — Design system maduro e bem documentado, com tokens centralizados, dark mode, e componentes base. Pontos de melhoria em cobertura de estados e valores arbitrários residuais.

### ✅ Checklist de Inspeções

| Item | Status | Evidência |
|---|---|---|
| Cores: tokens reutilizáveis vs hardcoded | ⚠️ Parcial (tokens excelentes, mas valores arbitrários residuais) | §5.1, §5.4 |
| Tipografia: tokens reutilizáveis vs hardcoded | ✅ Conforme | §5.8 |
| Espaçamento: tokens reutilizáveis vs hardcoded | ⚠️ Parcial | §5.1 |
| Valores mágicos no código | ⚠️ 553 ocorrências em 226 arquivos | §5.1 |
| Suporte a dark mode | ✅ Implementado | §5.5 |
| Componentes base centralizados (shadcn/ui) | ✅ Excelente | §5.6 |
| Cobertura hover/focus/disabled/loading | ✅ Conforme | §5.10 |
| Cobertura loading/success/error em async | ✅ Conforme | §5.10 |
| Empty states em listas | ✅ Conforme (~19 arquivos) | §5.7 |
| Form states (pristine/dirty/valid/invalid) | ⚠️ Parcial | §5.9 |
| Consistência entre telas (tabelas, cards, modais, mensagens, ícones) | ✅ Conforme (via design-tokens.ts) | §5.4, §5.6 |

### Achados Críticos

Nenhum achado crítico nesta dimensão.

### Achados Importantes

#### §5.1 Valores arbitrários Tailwind residuais — 553 ocorrências em 226 arquivos

- **226 arquivos** em `src/components` contêm valores arbitrários (`w-[Npx]`, `h-[Npx]`, `p-[Npx]`, `m-[Npx]`, `gap-[Npx]`, `text-[Npx]`, `rounded-[Npx]`).
- **553 ocorrências totais.**
- Tokens semânticos de layout existem (`w-panel-sm`, `h-chart-sm`, etc. em `tailwind.config.ts` L248-271), mas adoção é parcial.

#### §5.2 Inline styles (`style={{}}`) — 875 ocorrências em 211 arquivos

- **211 arquivos** em `src/components` usam inline styles.
- **875 ocorrências totais.**
- Exemplos com citação:
  - `src/components/big-five-modal.tsx` L286: `style={{color: fitScore >= 70 ? 'var(--status-success)' : ...}}`
  - `src/components/big-five-modal.tsx` L457: `style={{width: \`${score}%\`}}`
  - `src/components/lia-metrics-dashboard.tsx` L338, L503, L637, L661, L830, L834: Progress bars com inline `width`
  - `src/components/disc-assessment-modal.tsx` L416: `style={{backgroundColor: dim.color + '20', color: dim.color}}`
  - `src/components/lia-metrics-chart.tsx` L78, L99: `style={{fontSize: '10px'}}` — deveria usar token `text-micro`
  - `src/components/batch-approval-modal.tsx` L330: `style={{width: \`${...}%\`}}`
- **Nota:** Muitos inline styles são para dynamic widths (progress bars, computed values) — justificados. Os de `fontSize` e `color` são migráveis para tokens.

#### §5.3 Cores hardcoded em CSS utility classes

- **`src/styles/design-tokens.css` L547-649:** Classes `.lia-h1` a `.lia-label-sm` usam cores hex hardcoded:
  - L552: `.lia-h1 { color: #1F2937; }` — deveria usar `var(--lia-text-primary)` ou `var(--wedo-text-body)`
  - L558: `.lia-h2 { color: #1F2937; }` — idem
  - L570: `.lia-h3 { color: #1F2937; }` — idem
  - L604: `.lia-body { color: #4B5563; }` — deveria usar `var(--lia-text-secondary)`
  - L621: `.lia-helper { color: #6B7280; }` — deveria usar `var(--lia-text-tertiary)`
- **Impacto:** Dark mode precisa de overrides explícitos (que existem em L832-857) ao invés de funcionar automaticamente via tokens. Manutenção duplicada.

### Achados — Melhorias (Positivos)

#### §5.4 Design tokens centralizados (Excelente)

- **`src/styles/design-tokens.css`** (996 linhas): Fonte de verdade para cores (backgrounds, borders, textos, interactive states, shadows), tipografia (escala, line-heights), espaçamento, e z-index.
- **`src/lib/design-tokens.ts`** (470+ linhas): Mirror TypeScript com classes utilitárias para componentes React:
  - `textStyles` (L203-248): 20+ variantes de texto (h1-h4, body, caption, metric, link, sidebar)
  - `cardStyles` (L254-262): 7 variantes de card
  - `buttonStyles` (L269-291): 7 variantes de botão
  - `badgeStyles` (L308-332): 12 variantes de badge
  - `tabStyles` (L338-350): 2 estilos (underline + pill)
  - `inputStyles` (L297-302): 4 estados
  - `formStyles` (L381-387): 5 padrões
  - `modalStyles` (L369-376): 5 partes
  - `actionButtonStyles` (L356-364): 4 variantes
- **`tailwind.config.ts`**: 50+ tokens customizados mapeados para classes Tailwind (`lia-bg-primary`, `lia-text-secondary`, `status-success`, `lia-btn-primary-bg`, etc.).
- **Mapeamento Vuetify preparado** (`tailwindToVuetify` em `design-tokens.ts` L392-472) para migração futura.

#### §5.5 Dark mode (Implementado)

- Dark mode via `class` strategy (`tailwind.config.ts` L4: `darkMode: ["class"]`).
- ThemeProvider com `next-themes` (`src/app/layout.tsx` L51-57`): `attribute="class"`, `defaultTheme="light"`, `storageKey="wedo-theme"`.
- Tokens CSS com variantes `.dark` completas em `design-tokens.css` L191-268 (backgrounds, borders, textos, interactive states, shadows, brand colors, status, buttons, badges, inputs).
- **Limitação:** `enableSystem={false}` (`layout.tsx` L54) — não detecta preferência do sistema operacional.

#### §5.6 Componentes base centralizados via shadcn/ui (Excelente)

- **`components.json`:** Style `new-york`, ícones `lucide`, RSC enabled, aliases configurados.
- **`src/components/ui/`**: 50+ componentes base incluindo:
  - Layout: `card.tsx`, `dialog.tsx`, `sheet.tsx`, `collapsible.tsx`, `scroll-area.tsx`, `separator.tsx`
  - Forms: `button.tsx`, `input.tsx`, `label.tsx`, `checkbox.tsx`, `radio-group.tsx`, `select.tsx`, `slider.tsx`, `switch.tsx`
  - Feedback: `badge.tsx`, `progress.tsx`, `loading.tsx`, `empty-state.tsx`
  - Navigation: `dropdown-menu.tsx`, `popover.tsx`, `tabs.tsx`, `tooltip.tsx`, `command.tsx`, `accordion.tsx`
  - Overlay: `alert-dialog.tsx`, `dialog.tsx`
  - Data: `avatar.tsx`, `resizable-table-header.tsx`
  - Custom: `audio-player.tsx`, `audio-record-button.tsx`, `big-five-profile.tsx`, `candidate-card.tsx`, `command-palette.tsx`, `date-range-picker.tsx`, `pipeline-stages-carousel.tsx`, `premium-autocomplete.tsx`

#### §5.7 Empty states (Conforme)

- **`src/components/ui/empty-state.tsx`**: Componente reutilizável centralizado.
- **~19 arquivos** referenciam `EmptyState`/`empty-state`/`noData`:
  - `src/components/pages/jobs-page.tsx`
  - `src/components/pages/job-kanban-page.tsx`
  - `src/components/pages/chat-page.tsx`
  - `src/components/pages/candidates/CandidateSearchResultsView.tsx`
  - `src/components/pages/templates-page.tsx`
  - `src/components/pages/onboarding-premium-page.tsx`
  - `src/components/talent-funnel-tabs/favorites-tab.tsx`
  - `src/components/lia-float/LiaSplitPanel.tsx`
  - `src/components/lia-float/LiaChatPanel.tsx`
  - `src/components/global-search-modal.tsx`
  - `src/components/admin/clients/ClientTable.tsx`
  - `src/components/wsi/JDEvaluationPanel.tsx`
  - `src/components/pages/job-kanban/KanbanColumn.tsx`
  - `src/components/candidate-preview/CandidateFilesTab.tsx`
  - `src/components/expanded-chat/hooks/useExpandedChatEffects.tsx`

#### §5.8 Escala tipográfica padronizada (Conforme)

- **`tailwind.config.ts` L17-21:** 4 tamanhos customizados:
  - `xs`: 11px (UI labels, badges, status)
  - `micro`: 10px (metadados densos, timestamps)
  - `sm-ui`: 12px (helpers, captions)
  - `base-ui`: 13px (corpo compacto, inputs)
- **`design-tokens.css` L331-339:** Variables CSS:
  - `--font-size-xs: 0.6875rem`, `--font-size-micro: 0.625rem`, `--font-size-sm-ui: 0.75rem`, `--font-size-base-ui: 0.8125rem`
  - `--line-height-tight: 1.3`, `--line-height-normal: 1.4`, `--line-height-relaxed: 1.5`, `--line-height-body: 1.6`
- **Fontes:** Open Sans (primária), Inter (dados/métricas), Crimson Text (decorativa).
- **Classes utilitárias CSS:** `.wedo-text-title` (L290), `.wedo-text-body` (L291), `.wedo-text-secondary` (L292), `.wedo-text-muted` (L293) com dark mode automático (L296-299).
- **`tailwind.config.ts` L210-216:** Font families mapeadas: `font-inter`, `font-open-sans`, `font-crimson`, `font-brand`, `font-data`.

#### §5.9 Form states (Parcialmente conforme)

- **Verificado explicitamente:**
  - **Zod validation** presente (`zod@^4.3.6` no package.json). Usado para validação de formulários.
  - **`src/lib/api/validate.ts`** (4 ocorrências de valid/invalid) — validação centralizada.
  - **`src/app/vagas/[slug]/page.tsx`** (26 ocorrências de valid/invalid/errors/formState) — formulário de candidatura com cobertura completa.
  - **`src/app/aceitar-convite/page.tsx`** (6 ocorrências) — formulário de convite com validação.
  - **`src/app/portal/data-request/[token]/page.tsx`** (6 ocorrências) — formulário LGPD com validação.
  - **`src/components/expandable-ai-prompt/useEAPCallbacks.tsx`** (5 ocorrências) — validação inline.
  - **`inputStyles.error`** e **`inputStyles.success`** definidos em `design-tokens.ts` L299-300 — estados visuais para inputs.
  - **`formStyles.errorText`** em `design-tokens.ts` L386 — mensagem de erro padronizada.
  - **`formStyles.labelRequired`** em `design-tokens.ts` L384 — indicador de campo obrigatório.
- **Limitação:** Não há biblioteca de form management (react-hook-form, formik) no package.json. Formulários usam validação manual via useState, sem tracking sistemático de pristine/dirty/touched. Cobertura de estados visuais (valid/invalid/error) existe nos tokens mas a aplicação consistente depende de cada formulário individual.

#### §5.10 Cobertura de estados interativos (Conforme)

- **Hover/Focus/Active/Disabled em `button.tsx`** (L8-20):
  - Base: `focus-visible:outline-none`, `focus:outline-none`, `disabled:pointer-events-none`, `disabled:opacity-50`
  - Primary (L12): `hover:bg-gray-800`, `focus:ring-2 focus:ring-gray-900/20`
  - Destructive (L14): `hover:bg-status-error`, `focus:ring-2 focus:ring-red-600/20`
  - Outline (L16): `hover:bg-gray-50`, `hover:text-lia-text-primary`, `focus:ring-2`
  - Ghost (L19): `hover:bg-gray-100`, `hover:text-lia-text-primary`, `focus:ring-2`
  - Link (L20): `hover:underline`, `hover:text-lia-text-primary`, `focus:text-lia-text-primary`
- **Loading states:**
  - `src/components/ui/loading.tsx` (10 ocorrências de loading/disabled)
  - `src/components/ui/chat-status-indicators.tsx` (2 ocorrências)
  - `src/components/ui/search-loading-animation.tsx`
  - `src/components/ui/candidate-card.tsx` (5 ocorrências de loading/disabled)
- **Disabled states em UI components:**
  - `src/components/ui/interview-rating.tsx` (11 ocorrências)
  - `src/components/ui/bulk-selection-bar.tsx` (4)
  - `src/components/ui/command-palette.tsx` (2)
  - `src/components/ui/dialog.tsx` (2)
  - `src/components/ui/dropdown-menu.tsx` (3)
- **Status semânticos (success/error/warning):** Sistema completo com `status-success`, `status-error`, `status-warning` + backgrounds (`status-success-bg`), borders (`status-error-border`), e texto. Definidos em `design-tokens.css` L359-381 e `tailwind.config.ts` L36-44.

#### §5.11 Página de Design System (Conforme)

- **`src/app/design-system/page.tsx`** existe como referência interna para desenvolvedores.

---

## Resumo de Recomendações por Prioridade

### P0 — Críticos (impacto imediato)

1. **Investigar bundle de 49.7MB** — `app/page.js` inclui toda a aplicação. Implementar code splitting agressivo com `dynamic()` para todos os modais e componentes pesados.
2. **Remover cache-busting global** — `Cache-Control: no-store` em `next.config.js` L56-68 é destrutivo. Aplicar apenas a rotas API, não a assets estáticos.
3. **Habilitar otimização de imagens** — remover `images: { unoptimized: true }` de `next.config.js` L26.
4. **Lazy-load bibliotecas pesadas** — `html2canvas`, `jspdf`, `canvg` (chunk de 1.3MB) devem usar `dynamic()`.
5. **Consolidar bibliotecas de gráficos** — escolher Recharts OU Chart.js, não ambos.

### P1 — Importantes (próximo sprint)

6. **Habilitar `reactStrictMode: true`** em `next.config.js` L18.
7. **Substituir keys de índice** nos 153 arquivos que usam `key={index}`.
8. **Adicionar `React.memo`** aos componentes de lista mais renderizados (kanban cards, candidate rows, filter items).
9. **Refatorar componentes >1.000 linhas** — ao menos os top 15 maiores.
10. **Eliminar duplicação de dark mode** entre `globals.css` L160-195 e `dark-mode.css` L6-41.
11. **Reduzir `!important`** — especialmente os 78 em `onboarding-styles.css`.
12. **Adicionar `{ passive: true }`** a scroll/touch listeners nos 47 arquivos sem.

### P2 — Melhorias (roadmap)

13. Habilitar `noImplicitAny: true` no `tsconfig.json` L12.
14. Reativar ESLint/TS checking no build (`next.config.js` L19-24).
15. Padronizar nomenclatura de arquivos (kebab-case único).
16. Remover diretórios `_archived/`.
17. Migrar inline styles (875 ocorrências) para tokens Tailwind onde possível.
18. Migrar valores arbitrários (553 ocorrências) para tokens semânticos.
19. Migrar hardcoded hex colors em `.lia-*` CSS classes para `var()`.
20. Adicionar virtualização em listas longas.
21. Adicionar estilos de impressão (`@media print`).
22. Habilitar `enableSystem={true}` no ThemeProvider.
23. Adicionar biblioteca de form management para cobertura sistemática de estados.

---

---

## Apêndice A — Metodologia e Comandos de Verificação

Todos os números agregados foram computados via linha de comando no diretório `plataforma-lia/`:

| Métrica | Comando |
|---|---|
| Total de arquivos TS/TSX em `src/` | `find src -name '*.tsx' \| wc -l` → 709; `find src -name '*.ts' \| wc -l` → 831 |
| Total de linhas TSX em components+app | `find src/app src/components -name '*.tsx' \| xargs wc -l \| tail -1` → 284.274 |
| Total de linhas TS/TSX em `src/` | `find src -name '*.tsx' -o -name '*.ts' \| xargs wc -l \| tail -1` → 398.179 |
| Componentes >1.000 linhas | `find src/components -name '*.tsx' \| xargs wc -l \| sort -rn \| head -15` |
| useState | `find src -name '*.tsx' -o -name '*.ts' \| xargs grep -c 'useState' \| awk -F: '$2>0{sum+=$2}END{print sum}'` → 4.192 |
| useEffect | Idem com `'useEffect'` → 927 |
| useMemo+useCallback | Idem com `'useMemo\|useCallback'` → 1.806 |
| React.memo | `find src -name '*.tsx' -o -name '*.ts' \| xargs grep -cl 'React.memo' \| wc -l` → 4 |
| key={index} | `find src -name '*.tsx' -o -name '*.ts' \| xargs grep -c 'key={index}\|key={i}' \| awk -F: '$2>0{count++}END{print count}'` → 153 |
| addEventListener | Idem com `'addEventListener'` → 59 |
| passive listeners | `find src -name '*.tsx' -o -name '*.ts' \| xargs grep -cl 'passive' \| wc -l` → 12 |
| setTimeout/setInterval | Idem → 164 |
| `!important` | `grep -r '!important' src/ \| wc -l` → 139 |
| Arbitrary Tailwind values | `find src/components -name '*.tsx' -o -name '*.ts' \| xargs grep -c 'w-\[\|h-\[\|p-\[\|m-\[\|gap-\[\|text-\[\|rounded-\[' \| awk -F: '$2>0{count++; sum+=$2}END{print count, sum}'` → 226 arquivos, 553 ocorrências |
| Inline styles | `find src/components -name '*.tsx' \| xargs grep -c 'style={{' \| awk -F: '$2>0{count++; sum+=$2}END{print count, sum}'` → 211 arquivos, 875 ocorrências |
| debounce/throttle | `find src -name '*.tsx' -o -name '*.ts' \| xargs grep -cl 'debounce\|throttle' \| wc -l` → 10+ |
| Bundle sizes | `ls -lS out/static/chunks/*.js out/static/chunks/app/*.js` (build output) |
| Total JS | `du -sh out/static/chunks/` → 72MB |

*Relatório gerado em 2026-03-30. Dimensões 6-20 serão cobertas em tarefas subsequentes.*
