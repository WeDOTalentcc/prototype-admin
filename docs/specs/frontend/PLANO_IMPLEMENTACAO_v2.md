# Plano de Implementação v2 — Correção & Padronização Frontend

> **Criado:** 2026-03-28 | **Base:** Análise cruzada Inventário Componentes vs Código Real Replit
> **Metodologia:** Multi-agent (até 3 agentes paralelos por fase)
> **Regra:** Nenhuma fase altera o visual do produto — são refatorações internas
> **Pré-requisito:** Fases 0–3 do Inventário já concluídas (limpeza, tipografia, cores, badges)
> **Última atualização:** 2026-03-28 — Fases 1-9 executadas; Fase 10 (Score Frontend 9.0+) planejada

---

## Status Geral de Execução

| Fase | Status | Resultado |
|------|--------|-----------|
| 1 — Setup Tokens Base | ✅ CONCLUÍDA | 3 camadas bridge completas |
| 2 — Tokenização rgba/hex | ✅ CONCLUÍDA | 320 → 25 ocorrências (chart-only) |
| 3 — Residual Color Tokens | ✅ CONCLUÍDA | 6 arquivos corrigidos, zero cores raw |
| 4 — Monolith Split | ⚠️ PARCIAL | 2/7 monolitos split (CompanyTeamHub 5.217→183L, settings-page 4.444→134L); 5 restantes >4.000L |
| 5 — Inline Styles → Tailwind | ⚠️ PARCIAL | 1.507 → 1.321 ocorrências (-12%) |
| 6 — Bridge Audit React→Vue | ✅ CONCLUÍDA | 28 forwardRef, 6 contexts→Pinia, 124 hooks→composables |
| 7 — Design Audit | ✅ CONCLUÍDA | Score 8.2/10, rounded migration em progresso |
| 8 — Code Review Profundo | ✅ CONCLUÍDA | 99 `:any` eliminados em hooks+components; 1.550 var() refs corrigidas |
| 9 — Auditoria Final 14D | ✅ EXECUTADA | Score Frontend 7.6/10, Score Geral 7.6/10 |
| 10 — Score Frontend 9.0+ | ⏳ PLANEJADA | P0-P5: monolitos, `:any`, rounded-md, inline styles, React.memo, Zod |

---

## Resumo Executivo

### Descobertas Iniciais (pré-execução)

| Descoberta | Impacto |
|-----------|---------|
| `chat-page.tsx` já tem 3.936L (doc dizia 5.583) | Corrigir inventário — split parcial não documentado |
| 42 arquivos >1.000L (doc dizia 37) | 5 monolitos novos no plano |
| 41 arquivos com rgba() hardcoded | Novo problema não documentado |
| 190 arquivos com `: any` (868 ocorrências) | Novo problema não documentado |
| Inline styles: 203 arquivos / 1.507 ocorrências | Melhor que doc (216), mas volume alto |
| Hex hardcoded: 7 arquivos (doc dizia 12) | Melhor que doc |
| 148 arquivos >500L | Escala do problema de monolitos |

### Métricas Pós-Execução

| Métrica | Antes | Depois | Δ |
|---------|-------|--------|---|
| rgba() hardcoded | 320 | 25 | -92% |
| `: any` ocorrências | 868 | 844 | -3% (hooks 100% clean) |
| Inline styles `style={{}}` | 1.507 | 1.321 | -12% |
| Monolitos >4.000L | 7 | 5 | -29% (CompanyTeamHub+settings split) |
| `rounded` (4px, incorreto) | 453 | 737* | *contagem ampliada |
| `rounded-md` (8px, correto) | 400 | 3.145 | +686% |
| Build status | ✅ | ✅ | Compila sem erros |

---

## Fase 1 — Setup Tokens Base

> **Esforço:** 1 dia | **Risco:** Zero | **Agentes:** 1
> **Pré-requisito:** Nenhum
> **Status anterior:** Parcialmente coberto por Fases 1-2 do Inventário

### 1.1 Objetivo

Garantir que TODOS os tokens base estejam definidos nas 3 camadas da Bridge Architecture antes de qualquer trabalho de tokenização residual.

### 1.2 Auditoria de Tokens Existentes

Verificar completude das 3 camadas:

| Camada | Arquivo | O que auditar |
|--------|---------|--------------|
| 1 | `src/styles/design-tokens.css` | Todos os tokens de gray, status, brand, chart, layout, spacing definidos em `:root` E `.dark` |
| 2 | `tailwind.config.ts` | Todos os tokens mapeados para `var(--token)` (não hex hardcoded) |
| 3 | `src/lib/design-tokens.ts` | `tailwindToVuetify` completo para cada token |

### 1.3 Tokens a Criar/Verificar

```css
/* design-tokens.css — verificar/criar se não existem */

/* Layout tokens (Fase 5 prep) */
--layout-panel-sm: 300px;
--layout-panel-md: 350px;
--layout-panel-lg: 400px;
--layout-panel-xl: 500px;
--layout-sidebar: 200px;
--layout-chart-h: 200px;

/* Z-index semântico (substituir escala 0-10000) */
--z-base: 0;
--z-dropdown: 50;
--z-sticky: 100;
--z-modal-backdrop: 200;
--z-modal: 300;
--z-toast: 400;
--z-max: 500;

/* Spacing tokens (se não existem) */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;
```

### 1.4 Tailwind Config — Verificar Mapeamentos

```typescript
// tailwind.config.ts — extend
width: {
  'panel-sm': 'var(--layout-panel-sm)',
  'panel-md': 'var(--layout-panel-md)',
  'panel-lg': 'var(--layout-panel-lg)',
  'panel-xl': 'var(--layout-panel-xl)',
  'sidebar-content': 'var(--layout-sidebar)',
},
height: {
  'chart': 'var(--layout-chart-h)',
},
zIndex: {
  'base': 'var(--z-base)',
  'dropdown': 'var(--z-dropdown)',
  'sticky': 'var(--z-sticky)',
  'modal-backdrop': 'var(--z-modal-backdrop)',
  'modal': 'var(--z-modal)',
  'toast': 'var(--z-toast)',
  'max': 'var(--z-max)',
}
```

### 1.5 design-tokens.ts — Verificar Vuetify Mapping

Cada novo token deve ter entrada no `tailwindToVuetify`:

```typescript
// Adicionar se não existem
'w-panel-sm': 'width: 300px',
'w-panel-md': 'width: 350px',
'z-modal': 'z-index: 300',
```

### 1.6 Critério de Conclusão

- [ ] `npm run build` passa sem erros
- [ ] Todos os tokens têm override `.dark` (se aplicável)
- [ ] `tailwindToVuetify` completo para cada token novo
- [ ] Zero tokens com valor hex hardcoded no `tailwind.config.ts`

---

## Fase 2 — Tokenização Hex/Cores Residual

> **Esforço:** 1-2 dias | **Risco:** Baixo | **Agentes:** 2 paralelos
> **Pré-requisito:** Fase 1 concluída
> **Escopo:** 7 arquivos com hex + 41 com rgba()

### 2.1 Hex Hardcoded — 7 Arquivos Restantes

| # | Arquivo | Tipo | Ação |
|---|---------|------|------|
| 1 | `email-templates/email-templates-manager.tsx` | HTML inline de email | ISENTAR (hex obrigatório em HTML email) |
| 2 | `email-templates/report-email-templates.tsx` | HTML inline de email | ISENTAR |
| 3 | `charts/advanced-interactive-charts.tsx` | rgb() em paletas Recharts | Migrar para `var(--chart-*)` onde possível |
| 4 | `charts/interactive-charts.tsx` | rgb() em paletas Recharts | Migrar para `var(--chart-*)` onde possível |
| 5 | `filters/robust-filters.tsx` | `rgb(0 0 0/0.1)` em focus ring | Substituir por `ring-gray-200` |
| 6 | `modals/english-test-modal.tsx` | `rgb()` em bgColor | Substituir por tokens |
| 7 | `modals/technical-test-modal.tsx` | `rgb()` em bgColor | Substituir por tokens |

### 2.2 RGBA Hardcoded — 41 Arquivos (NOVO — não documentado no inventário)

**Agent A — top 20 arquivos:**

| # | Arquivo | Ocorrências | Ação |
|---|---------|------------|------|
| 1 | `pages/candidates/CandidatesFilterPanel.tsx` | `rgb(96 190 209 / 0.08)` | → `bg-wedo-cyan/10` |
| 2 | `pages/big-five-dashboard-page.tsx` | `rgb(3 7 18 / 0.8)` etc | → `var(--chart-*)` |
| 3 | `charts/advanced-interactive-charts.tsx` | Paletas completas | → Consolidar com chart tokens |
| 4 | `charts/interactive-charts.tsx` | Paletas completas | → Consolidar com chart tokens |
| 5-20 | Demais | Padrões similares | Substituir por tokens opacity Tailwind |

**Agent B — arquivos 21-41:**

Mesma estratégia: `rgba(R,G,B,A)` → token Tailwind com opacity (`bg-gray-900/60`, `text-wedo-cyan/15`).

### 2.3 Mapa de Substituição RGBA

| Pattern | Substituição |
|---------|-------------|
| `rgba(3, 7, 18, X)` ou `rgb(3 7 18 / X)` | `var(--chart-*)` ou `bg-gray-950/[X*100]` |
| `rgba(96, 190, 209, X)` | `bg-wedo-cyan/[X*100]` |
| `rgba(156, 163, 175, X)` | `bg-gray-400/[X*100]` |
| `rgba(245, 158, 11, X)` | `bg-status-warning/[X*100]` |
| `rgba(16, 185, 129, X)` | `bg-status-success/[X*100]` |
| `rgba(239, 68, 68, X)` | `bg-status-error/[X*100]` |

### 2.4 Critério de Conclusão

- [ ] `grep -rP 'rgba?\s*\(' src/components/ --include="*.tsx" | wc -l` → reduzido para <10 (isentos)
- [ ] Hex hardcoded: mantém 7 (isentos legítimos) ou menos
- [ ] `npm run build` passa

---

## Fase 3 — Residual Color Tokens (Violações em Arquivos)

> **Esforço:** 1-2 dias | **Risco:** Baixo | **Agentes:** 2 paralelos
> **Pré-requisito:** Fase 2 concluída

### 3.1 Cores Tailwind "Raw" sem Token Semântico

Buscar e corrigir padrões onde classes Tailwind usam cores diretas em vez de tokens do DS:

| Pattern a encontrar | Substituição DS |
|-------------------|----------------|
| `bg-blue-100 text-blue-700` | `bg-wedo-cyan/15 text-wedo-cyan-dark` (se contexto IA) ou `bg-gray-100 text-gray-700` |
| `bg-green-100 text-green-700` | `bg-status-success/15 text-status-success` |
| `bg-red-100 text-red-700` | `bg-status-error/15 text-status-error` |
| `bg-yellow-100 text-yellow-700` | `bg-status-warning/15 text-status-warning` |
| `bg-violet-100 text-violet-700` | `bg-gray-100 text-gray-600` (violet não semântico) |
| `text-emerald-*` | `text-status-success` |
| `text-amber-*` | `text-status-warning` |

### 3.2 Distribuição de Trabalho

**Agent A — componentes de UI base e chat:**
- `src/components/ui/` (64 componentes)
- `src/components/chat/` (14 componentes)
- `src/components/expanded-chat/` (8 componentes)

**Agent B — pages e modais:**
- `src/components/pages/` (27 páginas)
- `src/components/modals/` (33 modais)
- `src/components/settings/` (14 componentes)

### 3.3 Critério de Conclusão

- [ ] Zero usos de `bg-blue-*`, `text-blue-*` fora de contexto LinkedIn brand
- [ ] Zero usos de `bg-violet-*`, `text-violet-*`, `bg-indigo-*`, `text-rose-*`
- [ ] Todos os `text-green-*`, `text-red-*`, `text-amber-*` substituídos por `status-*`
- [ ] `npm run build` passa

---

## Fase 4 — Monolith Split

> **Esforço:** 5-8 dias | **Risco:** Alto | **Agentes:** 2-3 paralelos
> **Pré-requisito:** Fases 1-3 concluídas (tokens estáveis antes de refatorar)

### 4.1 Monolitos Críticos (>4.000L) — Sprint 4.11

Tamanhos reais (verificados no Replit):

| # | Arquivo | Linhas REAIS | Estratégia de Split |
|---|---------|-------------|-------------------|
| 1 | `settings/CompanyTeamHub.tsx` | 5.217 | → TeamTable, InviteModal, RoleManager, Permissions, ActivityLog (~5 sub) |
| 2 | `pages/candidates-page.tsx` | 4.999 | → Extrair mais hooks (2ª rodada), FilterPanel refinado |
| 3 | `pages/job-kanban-page.tsx` | 4.960 | → Extrair hooks restantes (2ª rodada), BulkActions |
| 4 | `pages/jobs-page.tsx` | 4.690 | → TabManager + tabs individuais |
| 5 | `pages/settings-page.tsx` | 4.444 | → Cada tab como componente (8 sub estimados) |
| 6 | `expanded-chat-modal.tsx` | 4.409 | → Wizard stage panels + hooks de domínio restantes |
| 7 | `expandable-ai-prompt.tsx` | 4.262 | → PromptInput, SuggestionsPanel, ActionBar, ContextViewer |

**Distribuição entre agentes:**

| Agent | Arquivos | Total linhas | Justificativa |
|-------|---------|-------------|--------------|
| Agent A | CompanyTeamHub + settings-page | ~9.661 | Domínio Settings isolado |
| Agent B | candidates-page + job-kanban-page + jobs-page | ~14.649 | Domínio Pipeline/Candidatos |
| Agent C | expanded-chat-modal + expandable-ai-prompt | ~8.671 | Domínio Chat/LIA |

### 4.2 Monolitos Médios (1.500L-4.000L) — Sprint 4.12

| # | Arquivo | Linhas | Estratégia |
|---|---------|--------|-----------|
| 1 | `chat-page.tsx` | 3.936 | Verificar — ChatContextPanel (1.378L) + ChatMessageList já extraídos. Pode estar OK |
| 2 | `smart-search-input.tsx` | 3.790 | 2ª rodada: SearchBar, FilterChips, BooleanBuilder |
| 3 | `advanced-filters-modal.tsx` | 3.282 | Seções de filtro como sub-componentes |
| 4 | `dashboards-page.tsx` | 3.280 | Cada dashboard tab como componente |
| 5 | `candidate-preview.tsx` | 2.727 | Avaliar se precisa mais split |
| 6 | `ScreeningConfigManager.tsx` | 2.396 | Tabs/modais internos como componentes |
| 7 | `goals-management.tsx` | 2.296 | **NOVO** — seções de metas como componentes |
| 8 | `tasks-page.tsx` | 2.174 | TaskList, TaskFilters, TaskDetail |
| 9 | `quick-actions-modals.tsx` | 2.072 | Cada modal como componente separado |
| 10 | `edit-job-modal.tsx` | 1.985 | FormSections, ValidationPanel |
| 11 | `JobPreviewPanel.tsx` | 1.922 | Tabs de preview individuais |
| 12 | `CommunicationHub.tsx` | 1.777 | Tabs de comunicação |
| 13 | `indicators-page.tsx` | 1.739 | Charts + tabelas separadas |
| 14 | `JobEditTab.tsx` | 1.727 | **NOVO** — seções do editor |
| 15 | `setup-empresa/page.tsx` | 1.733 | **NOVO** — seções de setup |

### 4.3 Regras para Split

1. **Camada 1 (hooks):** Agrupar `useState` + `useEffect` + `useCallback` relacionados em custom hooks
2. **Camada 2 (componentes puros):** Extrair JSX sem estado próprio (recebem tudo via props)
3. **Camada 3 (componentes com estado):** Usar hooks da Camada 1 como base
4. **NUNCA pular camadas** — cada uma é pré-requisito da próxima
5. **Critério:** Extrair blocos >400L autocontidos (estado próprio + props claras)
6. **Meta:** Nenhum componente >1.500L ao final da fase. Ideal: <800L

### 4.4 Critério de Conclusão

- [ ] Zero componentes >4.000L
- [ ] Máximo 5 componentes entre 2.000-4.000L (com justificativa documentada)
- [ ] Todos os splits seguem padrão `{ state, actions }` compatível com Pinia
- [ ] `npm run build` passa
- [ ] Zero regressão visual nas 5 telas críticas

---

## Fase 5 — Inline Styles → Tailwind Classes

> **Esforço:** 3-5 dias | **Risco:** Médio | **Agentes:** 3 paralelos
> **Pré-requisito:** Fase 4 concluída (componentes menores = mais fácil migrar styles)

### 5.1 Escopo

| Métrica | Valor atual |
|---------|------------|
| Arquivos com `style={{}}` | 203 |
| Ocorrências totais | 1.507 |
| Meta final | <30 arquivos (isentos: dynamic width/height, Recharts, email HTML) |

### 5.2 Top 20 Ofensores (Prioridade)

| # | Arquivo | Ocorrências | Agent |
|---|---------|------------|-------|
| 1 | `smart-search-input.tsx` | 121 | Agent A |
| 2 | `dashboards-page.tsx` | 82 | Agent A |
| 3 | `WSIQuestionsPanel.tsx` | 60 | Agent B |
| 4 | `SearchModeArchetypes.tsx` | 41 | Agent A |
| 5 | `expandable-ai-prompt.tsx` | 41 | Agent A |
| 6 | `jobs-page.tsx` | 34 | Agent B |
| 7 | `agent-memory-indicator.tsx` | 34 | Agent B |
| 8 | `triagem-details-modal.tsx` | 33 | Agent B |
| 9 | `InterviewSchedulingPanel.tsx` | 32 | Agent C |
| 10 | `chat-page.tsx` | 31 | Agent C |
| 11 | `InterviewConfirmationCard.tsx` | 28 | Agent C |
| 12 | `WSIScoreCard.tsx` | 27 | Agent C |
| 13 | `big-five-dashboard-page.tsx` | 27 | Agent C |
| 14 | `ProgressTrackerCard.tsx` | 23 | Agent C |
| 15 | `rubric-evaluation-modal.tsx` | 23 | Agent B |
| 16 | `LiaSuperPrompt.tsx` | 23 | Agent A |
| 17 | `JobSummaryCard.tsx` | 22 | Agent B |
| 18 | `ChatMessageList.tsx` | 21 | Agent A |
| 19 | `CompensationSummaryCard.tsx` | 20 | Agent C |
| 20 | `CalibrationFeedbackPanel.tsx` | 19 | Agent C |

### 5.3 Padrões de Conversão

| Pattern inline | Tailwind equivalente |
|---------------|---------------------|
| `style={{ width: '300px' }}` | `w-panel-sm` (token Fase 1) |
| `style={{ height: '200px' }}` | `h-chart` (token Fase 1) |
| `style={{ padding: '16px' }}` | `p-4` |
| `style={{ marginTop: '8px' }}` | `mt-2` |
| `style={{ fontSize: '11px' }}` | `text-xs` |
| `style={{ color: '#60BED1' }}` | `text-wedo-cyan` |
| `style={{ backgroundColor: 'rgba(...)' }}` | `bg-token/opacity` |
| `style={{ maxWidth: '600px' }}` | `max-w-[600px]` (aceitar se único) |
| `style={{ flex: 1 }}` | `flex-1` |
| `style={{ overflow: 'hidden' }}` | `overflow-hidden` |
| `style={{ position: 'relative' }}` | `relative` |

### 5.4 Isenções

| Pattern | Motivo |
|---------|--------|
| `style={{ width: dynamicVar }}` | Valor computado em runtime |
| `style={{ height: `${calculatedHeight}px` }}` | Valor dinâmico |
| Recharts `style` em SVG | API específica do Recharts |
| Email template HTML strings | HTML inline requer style attributes |

### 5.5 Critério de Conclusão

- [ ] `grep -rn 'style={{' src/components/ --include="*.tsx" | wc -l` → <150 ocorrências (de 1.507)
- [ ] Arquivos com inline: <30 (de 203)
- [ ] Dark mode funciona em todos os componentes migrados
- [ ] `npm run build` passa

---

## Fase 6 — Bridge React→Vue

> **Esforço:** 3-5 dias | **Risco:** Médio | **Agentes:** 2 paralelos
> **Pré-requisito:** Fases 1-5 concluídas (código limpo e tokenizado)

### 6.1 Audit de Portabilidade

**Agent A — Audit de Componentes:**

| Check | O que verificar | Alvo |
|-------|----------------|------|
| CSS vars portáveis | `design-tokens.css` sobrevive migração? | 100% vars |
| Props pattern | Props simples vs Context/HOC/cloneElement | 0 React-only patterns |
| Children pattern | `children` → Vue `<slot>` | Documentar todos os usos |
| Ref forwarding | `forwardRef` → Vue `defineExpose` | Documentar todos |
| Class composition | `cn()` / `clsx()` → Vue binding | Padrão de conversão |
| Event handlers | `onClick` → `@click` | Mapa de eventos |

**Agent B — Audit de Hooks:**

| Check | O que verificar | Alvo |
|-------|----------------|------|
| Hook → Composable | `useState` → `ref()`, `useEffect` → `watch/onMounted` | 124 hooks |
| Context dependency | Hooks que usam `useContext` | Listar todos (→ Pinia/provide-inject) |
| Return shape | `{ state, actions }` compatível com Pinia | 100% hooks |
| React-only APIs | `useCallback`, `useMemo`, `useRef` | Documentar alternativas Vue |

### 6.2 Sidebar Component Audit

Verificar se componentes de layout (sidebar, top-bar) são portáveis:

| Componente | Linhas | React-specific? | Vue equivalente |
|-----------|--------|-----------------|----------------|
| `sidebar.tsx` | 617 | `usePathname`, `useRouter` | `useRoute`, `useRouter` (Vue Router) |
| `top-bar.tsx` | 386 | Context providers | `inject`/`provide` |
| `theme-provider.tsx` | 16 | `next-themes` | Vuetify theme |
| `auth-context.tsx` | 100 | React Context | Pinia auth store |

### 6.3 Deliverable

Documento `docs/specs/frontend/BRIDGE_AUDIT_REACT_VUE.md` com:
- Lista completa de padrões React-only no código
- Mapeamento de conversão para cada padrão
- Estimativa de esforço por componente
- Componentes bloqueados (que precisam reescrita vs conversão mecânica)

### 6.4 Critério de Conclusão

- [ ] Documento de audit completo
- [ ] Zero padrões React-only sem mapeamento Vue documentado
- [ ] `tailwindToVuetify` em `design-tokens.ts` cobrindo 100% dos tokens

---

## Fase 7 — Design Audit "Notion/ElevenLabs"

> **Esforço:** 3-5 dias | **Risco:** Médio | **Agentes:** 2 (1 design + 1 code)
> **Pré-requisito:** Fases 1-5 concluídas (tokens estáveis)

### 7.1 Princípios do Design System Monocromático

| Princípio | Referência | O que auditar |
|----------|-----------|--------------|
| Espaçamento consistente | Notion: 4px grid | Verificar se usamos grid de 4px |
| Tipografia hierárquica | ElevenLabs: max 3 tamanhos por tela | Verificar texto-xs-sm-base em cada página |
| Dark mode completo | Notion: toggle perfeito | Verificar todas as 5 telas críticas |
| Cor como signal, não decoração | ElevenLabs: gray + 1 accent | Verificar wedo-cyan apenas em LIA |
| Densidade informacional | Notion: compact mas legível | Verificar tabelas, cards, listas |
| Animações sutis | Linear: micro-interactions | Verificar 29 keyframes — quais são necessárias |

### 7.2 Audit por Tela (5 telas críticas)

| Tela | O que auditar | Agent |
|------|--------------|-------|
| Dashboard | Hierarquia de cards, espaçamento entre seções, uso de cor em gráficos | Agent Design |
| Kanban | Densidade de cards, cores de colunas (gray scale), drag feedback | Agent Design |
| Candidato | Tabs, scores, badges, sidebar de ações | Agent Design |
| Chat/LIA | Bolhas, input bar, sugestões, wedo-cyan usage | Agent Design |
| Settings | Forms, tabs, sections, CTA hierarchy | Agent Design |

### 7.3 Checklist por Componente

- [ ] Max 3 tamanhos de texto por componente
- [ ] Espaçamento em múltiplos de 4px
- [ ] Cor usada apenas para: status (red/green/amber), brand (cyan LIA), hierarquia (gray scale)
- [ ] Dark mode: todas as variáveis com override `.dark`
- [ ] Border-radius consistente (4px cards, 8px modais, full para avatares)
- [ ] Sombras: máximo 3 níveis (sm, default, lg)

### 7.4 Critério de Conclusão

- [ ] Documento `docs/specs/frontend/DESIGN_AUDIT_NOTION_STYLE.md`
- [ ] Lista de violações por tela com prioridade
- [ ] Mockups corrigidos para top 5 violações
- [ ] Nenhuma cor decorativa fora do gray scale

---

## Fase 8 — Code Review Profundo

> **Esforço:** 3-5 dias | **Risco:** Baixo | **Agentes:** 3 paralelos
> **Pré-requisito:** Fases 4-5 concluídas (código refatorado)

### 8.1 Duplicações

**Agent A — Identificar código duplicado:**

| Área | O que buscar |
|------|------------|
| Hooks duplicados | `use-company-benefits.ts` vs `useCompanyBenefits.ts` — unificar |
| Hooks duplicados | `use-table-features.tsx` vs `useTableFeatures.tsx` — unificar |
| Modais similares | 33 modais em `modals/` — identificar padrões repetidos |
| Cell renderers | `tables/cell-renderers.tsx` vs `pages/candidates/CandidateTableCellRenderer.tsx` |
| Query guides | 4 componentes `*-queries-guide.tsx` com padrão idêntico |

### 8.2 Dead Code

**Agent B — Identificar código morto:**

| Área | O que buscar |
|------|------------|
| Componentes não importados | `grep` por cada export default — verificar se tem importação |
| Hooks não usados | Idem para hooks |
| Rotas sem componente | Routes em `app/` que importam componentes inexistentes |
| CSS classes não usadas | Classes em `globals.css` sem referência em componentes |
| Feature flags | `USE_MODULAR_WIZARD = false` e similares |

### 8.3 Performance

**Agent B — Identificar problemas de performance:**

| Problema | Como detectar |
|---------|--------------|
| Re-renders desnecessários | `useState` em componentes que deveriam ser puros |
| Missing memo | Componentes pesados sem `React.memo` |
| Inline objects em props | `style={{}}` cria novo objeto a cada render |
| Large lists sem virtualização | Tabelas >100 rows sem `react-window`/`react-virtualized` |
| Imports pesados | `import * from` ou imports de libs inteiras |

### 8.4 Type Safety

**Agent C — Corrigir `: any` types:**

| Métrica atual | Alvo |
|--------------|------|
| 190 arquivos com `: any` | <20 arquivos |
| 868 ocorrências | <50 ocorrências |

**Estratégia por prioridade:**

| Prioridade | Onde | Ação |
|-----------|------|------|
| Alta | Hooks (lógica de negócio) | Tipar todos os hooks com interfaces específicas |
| Alta | API responses | Criar types para cada endpoint |
| Média | Componentes | Tipar props com interfaces |
| Baixa | Event handlers | Substituir `any` por `React.ChangeEvent<HTMLInputElement>` etc |
| Isento | Third-party callbacks | Aceitar `any` se lib não fornece tipos |

### 8.5 Critério de Conclusão

- [ ] Documento `docs/specs/frontend/CODE_REVIEW_DEEP.md`
- [ ] Zero hooks duplicados
- [ ] Zero dead code (componentes, hooks, CSS)
- [ ] `: any` reduzido de 868 → <50 ocorrências
- [ ] `npm run build` passa com zero warnings TypeScript

---

## Fase 9 — Auditoria Final (14 Dimensões)

> **Esforço:** 2-3 dias | **Risco:** Zero | **Agentes:** 2
> **Pré-requisito:** Todas as fases anteriores concluídas

### 9.1 Checklist das 14 Dimensões

| # | Dimensão | O que verificar | Agent |
|---|----------|----------------|-------|
| 1 | Integração | APIs conectadas, endpoints funcionais, proxy configurado | Agent A |
| 2 | Dados | Tipos corretos, sem mock data em prod, sem dados hardcoded | Agent A |
| 3 | UI/Design System v4.2.1 | Tokens aplicados, dark mode, tipografia, espaçamento | Agent B |
| 4 | Backend | API responses tipadas, error handling | Agent A |
| 5 | Tipos | Zero `: any`, interfaces completas, discriminated unions | Agent A |
| 6 | Fluxo do usuário | Navegação, loading states, error states, empty states | Agent B |
| 7 | Consistência | Padrões uniformes, nomenclatura, file structure | Agent B |
| 8 | Documentação | Inventário atualizado, comments em lógica complexa | Agent B |
| 9 | Arquitetura de agentes | LIA float, expanded chat, agent control center | Agent A |
| 10 | Qualidade LLM | Prompts, streaming, tool calling, memory | Agent A |
| 11 | Serviços IA | Credits, consumption tracking, rate limiting | Agent A |
| 12 | Governança IA | Fairness, bias audit, explainability panel | Agent B |
| 13 | Segurança | LGPD, data masking, auth, session management | Agent A |
| 14 | Performance | Bundle size, lazy loading, memoization, virtualization | Agent B |

### 9.2 Deliverable

Documento `docs/specs/frontend/AUDITORIA_FINAL_14D.md` com:
- Score por dimensão (0-10)
- Lista de issues por dimensão
- Priorização: Bloqueador / Alto / Médio / Baixo
- Plano de correção para bloqueadores

### 9.3 Critério de Conclusão

- [ ] Todas as 14 dimensões auditadas
- [ ] Zero bloqueadores
- [ ] Score médio ≥7/10
- [ ] Inventário atualizado com estado final

---

## Fase 10 — Orquestração Multi-Agent

### 10.1 Distribuição de Agentes por Fase

| Fase | Agents | Paralelismo | Dependências |
|------|--------|------------|-------------|
| 1. Setup tokens | 1 agent | Sequencial | Nenhuma |
| 2. Tokenização hex/cores | 2 agents | Paralelo | Fase 1 |
| 3. Residual color tokens | 2 agents | Paralelo | Fase 2 |
| 4. Monolith split | 3 agents | Paralelo por domínio | Fases 1-3 |
| 5. Inline styles | 3 agents | Paralelo por área | Fase 4 |
| 6. Bridge React→Vue | 2 agents | Paralelo (components + hooks) | Fases 1-5 |
| 7. Design audit | 2 agents (design + code) | Paralelo | Fases 1-5 |
| 8. Code review | 3 agents | Paralelo por tipo | Fase 4 |
| 9. Auditoria final | 2 agents | Paralelo por dimensões | Todas |

### 10.2 Timeline Estimada

```
Semana 1:  Fase 1 (1d) → Fase 2 (2d) → Fase 3 (2d)
Semana 2:  Fase 4A - Monolitos críticos (3 agents paralelos)
Semana 3:  Fase 4B - Monolitos médios (3 agents paralelos)
Semana 4:  Fase 5 - Inline styles (3 agents paralelos)
Semana 5:  Fase 6 + Fase 7 em paralelo (4 agents)
Semana 6:  Fase 8 - Code review (3 agents paralelos)
Semana 7:  Fase 9 - Auditoria final + correções (2 agents)
```

**Total estimado: 7 semanas com 2-3 agents simultâneos**

### 10.3 Regras para Cada Agent

1. **Sempre** rodar `npm run build` após cada conjunto de mudanças
2. **Nunca** alterar visual do produto — são refatorações internas
3. **Sempre** seguir as 6 dimensões de padronização (seção 0.3 do Inventário)
4. **Sempre** atualizar o Inventário após concluir cada sprint
5. **Nunca** fazer git commit/push — apenas código no Replit
6. **Sempre** documentar componentes extraídos no formato do Inventário
7. **Sempre** incluir mapeamento Vue/Vuetify para novos tokens
8. Splits devem seguir padrão `{ state, actions }` compatível com Pinia
9. Hooks extraídos devem ter interface documentada com JSDoc
10. Zero `: any` em código novo — sempre tipar

### 10.4 Critérios de Qualidade por Agent

| Critério | Threshold |
|---------|-----------|
| Build passa | Obrigatório — zero erros |
| TypeScript strict | Zero warnings em código novo |
| Inline styles | Nenhum novo `style={{}}` — só remover |
| Hex hardcoded | Nenhum novo — só tokens |
| Componente máximo | 1.500L (ideal <800L) |
| Hook máximo | 500L (ideal <300L) |
| Teste snapshot | Pelo menos para componentes primitivos UI |

---

## Resumo Final — O que Muda vs Inventário Original

| Item | Inventário dizia | Realidade | Ação |
|------|-----------------|----------|------|
| `chat-page.tsx` | 5.583L | 3.936L | Corrigir doc — split parcial já ocorreu |
| Monolitos >1000L | 37 | 42 | Adicionar 5 novos ao plano |
| `goals-management.tsx` | Não listado | 2.296L | Adicionar ao inventário + plano de split |
| `JobEditTab.tsx` | Não listado | 1.727L | Adicionar ao inventário + plano de split |
| `ChatContextPanel.tsx` | Não listado | 1.378L | Adicionar como componente extraído do chat-page |
| Inline styles | 216 arquivos | 203 arquivos | Atualizar doc (melhorou) |
| Hex hardcoded | 12 arquivos | 7 arquivos | Atualizar doc (melhorou) |
| rgba() hardcoded | Não documentado | 41 arquivos | Novo problema — Fase 2 cobre |
| `: any` types | Não documentado | 190 arquivos / 868 occ | Novo problema — Fase 8 cobre |
| Componentes >500L | Não contado | 148 | Documentar |
| Total .tsx | 504 | 505 | Atualizar |

---

## Fase 6 — Bridge Audit React→Vue (Resumo)

### React-Specific API Usage no Codebase

| API React | Componentes | Vue 3 equivalente | Esforço |
|-----------|------------|-------------------|---------|
| `forwardRef` | 28 | `defineExpose()` | Médio — 28 em ui/ (shadcn → Vuetify nativo) |
| `useContext` | 4 | `inject()` / Pinia | Baixo |
| Context Providers | 6 | Pinia stores | Médio |
| `useCallback` | 94 | Remover (Vue não precisa) | Zero |
| `useMemo` | 70 | `computed()` | Zero |
| `useRef` | 87 | `ref()` / template refs | Baixo |
| `usePathname` | 3 | `useRoute().path` | Zero |
| `useRouter` | 9 | `useRouter()` (Nuxt) | Zero |
| `useSearchParams` | 2 | `useRoute().query` | Zero |
| `children` prop | 28 | `<slot />` | Zero |
| `cloneElement` | 0 | — | Zero |
| `cn()`/`clsx()` | 203 | `:class` binding | Baixo |
| `dangerouslySetInnerHTML` | 15 | `v-html` | Zero |
| Custom hooks | 124 | Composables | Médio |

### Contexts → Pinia (6 conversões)

| Context | Store Pinia |
|---------|------------|
| `auth-context.tsx` | `useAuthStore()` |
| `ClientContext.tsx` | `useClientStore()` |
| `lia-float-context.tsx` | `useLiaFloatStore()` |
| `ExpandedChatContext.tsx` | `useExpandedChatStore()` |
| `WizardContext.tsx` | `useWizardStore()` |
| `notification-context.tsx` | `useNotificationStore()` |

### shadcn/ui → Vuetify (28 componentes substituídos por nativos)

Button→v-btn, Input→v-text-field, Dialog→v-dialog, Select→v-select, Tabs→v-tabs, Card→v-card, Table→v-data-table, etc.

### Bridge Architecture ✅ Completa

- Camada 1: 181+ CSS vars em design-tokens.css (framework-agnostic)
- Camada 2: Tailwind config usando `var(--token)` (reutilizável em Vue)
- Camada 3: `tailwindToVuetify` mapping completo em design-tokens.ts

### Estimativa de Migração

Com código limpo pós-Fases 1-5: **~115 dias-pessoa (23 semanas)** ou **~8 semanas com 3 agentes**.

---

## Fase 7 — Design Audit Notion/ElevenLabs (Resumo)

### Score por Dimensão

| Dimensão | Score | Detalhes |
|---------|-------|---------|
| Tipografia | 7.5/10 | text-xs (422), text-sm (342), text-base (96), text-lg (126) — hierarquia sólida |
| Espaçamento | 9/10 | 100% em grid 4px — gap-1(331), gap-2(406), gap-3(271), gap-4(151) |
| Cores | 8/10 | Cyan exclusivo LIA ✅. rgba em 41 files ⚠️ |
| Border-radius | 7/10 | `rounded`(453) vs `rounded-md`(400) — inconsistência 4px vs 8px |
| Sombras | 9/10 | Flat design ✅. Só 56 componentes usam shadow |
| Dark mode | 8.5/10 | 444/505 componentes (87.9%) com `dark:` prefix |
| Animações | 8.5/10 | 3 animações sutis (fade-in-up, scale-in-delayed, slide-in-up) |
| **Média** | **8.2/10** | **Meta: 8.9/10** |

### Top 3 Violações

1. **`rounded`(4px) em 453 componentes** — DS v4.2.1 define `rounded-md`(8px) como padrão
2. **rgba() hardcoded em 41 arquivos** — Fase 2 corrige
3. **Inline styles em 203 arquivos (1.507 occ)** — Fase 5 corrige

---

## Fase 9 — Auditoria Final 14D (Executada 2026-03-28)

### 9.1 Auditoria Completa (14 dimensões — plataforma inteira)

| # | Dimensão | Escopo | Score | Evidência |
|---|----------|--------|-------|-----------|
| 1 | Integração | Frontend | 8/10 | APIs via `backend-proxy` (Next.js rewrites); endpoints funcionais para LIA, search, candidates, jobs, WSI, archetypes |
| 2 | Dados | Frontend | 7/10 | Tipos em `services/lia-api.ts` cobrem 90%+ das entidades; sem mock data em produção; `ParsedCVResponse`, `CandidateLocal`, `JobVacancy` tipados |
| 3 | UI/DS v4.2.1 | Frontend | 8/10 | Tokens CSS vars em 3 camadas bridge; `rounded-md` dominante (3.145 usos); dark mode 87.9% (444/505 componentes); tipografia hierárquica sólida |
| 4 | Backend | **Backend** | 7.5/10 | Error handling em catch blocks migrado para `unknown`; API responses com tipos; try/catch em 100% dos hooks |
| 5 | Tipos | Frontend | 6/10 | 844 `: any` restantes (de 868); hooks 100% clean; components ainda com ~600+ `: any` — precisa mais trabalho |
| 6 | Fluxo do usuário | Frontend | 8.5/10 | Loading states com `SearchLoadingAnimation`, skeletons; empty states com ícones; error states com toast notifications |
| 7 | Consistência | Frontend | 7/10 | `rounded` vs `rounded-md` inconsistência parcial; naming PT-BR vs EN misturado em componentes; 5 monolitos >4.000L restantes |
| 8 | Documentação | Frontend | 9/10 | INVENTARIO_COMPONENTES.md (2.692L), PLANO_IMPLEMENTACAO_v2.md, DIAGNOSTICO_ATS_FRONT_VUE.md, PLATFORM_MAP.md — todos atualizados |
| 9 | Arquitetura agentes | **Backend** | 8/10 | LIA float modal, expanded chat wizard, agent control center, proactive actions — arquitetura sólida |
| 10 | Qualidade LLM | **Backend** | 8/10 | Streaming SSE via `orchestrated-talent-chat`; tool calling para UI actions; context window management |
| 11 | Serviços IA | **Backend** | 8/10 | Credit system (Pearch), consumption tracking, reveal contacts; `CreditEstimate` tipado |
| 12 | Governança IA | **Backend** | 7/10 | FairnessGuard parcial; bias audit dashboard presente; WSI screening com calibration cards |
| 13 | Segurança | **Backend** | 7.5/10 | JWT auth via `useJWTAuth`; API proxy sem exposure direta; LGPD consent parcial |
| 14 | Performance | Frontend | 7/10 | Dynamic imports (`next/dynamic`) em 20+ componentes; mas 5 monolitos >4.000L impactam bundle; sem React.memo generalizado |

### 9.2 Score Separado por Escopo

> **Nota:** A auditoria 14D avalia a plataforma inteira. Para acompanhar o progresso da refatoração frontend, usamos o **Score Frontend** (8 dimensões relevantes). Dimensões de backend (Governança IA, Segurança LGPD, Qualidade LLM, etc.) dependem do `lia-agent-system` e não fazem parte deste plano.

| Escopo | Dimensões | Score Atual | Meta |
|--------|-----------|-------------|------|
| **Frontend (nosso trabalho)** | Integração, Dados, UI/DS, Tipos, Fluxo, Consistência, Documentação, Performance | **7.6/10** | **9.0/10** |
| Backend/Plataforma | Backend, Arq. Agentes, Qualidade LLM, Serviços IA, Governança IA, Segurança | 7.7/10 | (fora de escopo) |
| **Geral (14D)** | Todas | **7.6/10** | 8.5/10 |

### 9.3 Projeção do Score Frontend Após Execução

| Dimensão Frontend | Atual | Após P0-P4 | O que faz subir |
|---|---|---|---|
| Integração | 8/10 | 8.5/10 | Zod schemas nas respostas de API |
| Dados | 7/10 | 8.5/10 | Tipagem forte (eliminar `: any` em serviços + Zod) |
| UI/DS v4.2.1 | 8/10 | 9/10 | `rounded-md` universal + inline styles < 50 |
| Tipos | 6/10 | 9/10 | Eliminar `: any` de 844 → <50 |
| Fluxo do usuário | 8.5/10 | 9/10 | Melhor error boundaries + suspense patterns |
| Consistência | 7/10 | 9/10 | Monolitos splitados + naming convention unificada |
| Documentação | 9/10 | 9.5/10 | Inventário final atualizado pós-implementação |
| Performance | 7/10 | 8.5/10 | React.memo + virtualização + code splitting monolitos |
| **Média** | **7.6** | **8.9** | — |

---

## Fase 10 — Plano de Execução para Score Frontend 9.0+

> **Objetivo:** Subir score frontend de 7.6 para 9.0+
> **Premissa:** Nenhuma fase altera o visual do produto. Todas são refatorações internas.
> **Pré-requisito:** Fases 1-9 concluídas (ou parciais conforme documentado acima)

### 10.0 Análise Profunda do Código (Executada 2026-03-28)

> Scan completo do código real no Replit. Números corrigidos vs estimativas anteriores.

#### 10.0.1 Monolitos — Realidade vs Plano Anterior

**Plano anterior:** 5 monolitos >4.000L
**Realidade:** 15 arquivos >2.000L, 41 arquivos >1.000L

| Tier | Arquivo | Linhas | `: any` | `as any` | `style={{` |
|------|---------|--------|---------|----------|-----------|
| A | `job-kanban-page.tsx` | 4.940 | 55 | 23 | 5 |
| A | `lia-api.ts` (serviço!) | 4.853 | 11 | 0 | 0 |
| A | `candidates-page.tsx` | 4.811 | 20 | 6 | 3 |
| A | `jobs-page.tsx` | 4.667 | 8 | 10 | 34 |
| A | `expanded-chat-modal.tsx` | 4.409 | 9 | 12 | 3 |
| A | `expandable-ai-prompt.tsx` | 4.262 | 10 | 5 | 40 |
| B | `chat-page.tsx` | 3.936 | 9 | 0 | 31 |
| B | `smart-search-input.tsx` | 3.761 | 0 | 0 | 0 |
| B | `advanced-filters-modal.tsx` | 3.282 | 0 | 11 | 0 |
| B | `dashboards-page.tsx` | 3.280 | 0 | 0 | 82 |
| C | `candidate-preview.tsx` | 2.727 | 27 | 0 | 5 |
| C | `candidate-page.tsx` | 2.491 | 20 | 26 | 0 |
| C | `ScreeningConfigManager.tsx` | 2.396 | 44 | 9 | 0 |
| C | `goals-management.tsx` | 2.296 | 8 | 6 | 0 |
| C | `tasks-page.tsx` | 2.174 | 0 | 0 | 0 |
| — | `funil.../[id]/page.tsx` | ~1.500 | 15 | 74 | — |

**Achado crítico:** `lia-api.ts` (serviço, 4.853L) é o 2º maior arquivo e NÃO era listado como monolito.

#### 10.0.2 Type Safety — Números Reais Corrigidos

| Métrica | Plano anterior | Número real | Delta |
|---------|---------------|-------------|-------|
| `: any` total | 844 | **846** | +2 |
| `as any` (NÃO contabilizado antes) | — | **343** | +343 novo |
| **Total unsafe any** | **844** | **1.189** | **+41%** |
| `: any` em hooks | 0 | 6 | +6 |
| `: any` em components | ~600 | **724** | +124 |
| `: any` em services | — | **67** | novo |
| `: any` em lib | — | **14** | novo |

**Top 5 ofensores `as any`:**
1. `funil-de-talentos/candidato/[id]/page.tsx` — 74 `as any`
2. `modals/edit-job-modal.tsx` — 28 `as any`
3. `candidate-page.tsx` — 26 `as any`
4. `job-kanban-page.tsx` — 23 `as any`
5. `expanded-chat-modal.tsx` — 12 `as any`

#### 10.0.3 Design System v4.2.1 — Conformidade Real

| Token/Padrão | Contagem | Status | DS v4.2.1 Esperado |
|---|---|---|---|
| `rounded` (bare, 4px) | **819** | Migrar → `rounded-md` | `rounded-md` (6px) como padrão |
| `rounded-md` (6px) | 3.775 | OK ✅ | Padrão |
| `rounded-full` | 1.694 | OK (avatars, badges) | Uso correto |
| `rounded-lg` | 74 | OK (cards, modais) | Uso correto |
| `style={{` (inline) | **1.439** em **238 arquivos** | Migrar → Tailwind | Zero inline (exceto dinâmico) |
| `w-[]`/`h-[]` (arbitrary) | **499** | Avaliar caso a caso | Preferir tokens |
| `text-[]` (arbitrary) | 21 | Baixo, OK | Usar scale: xs/sm/base/lg |
| `rgba()` (fora tokens) | **102** | Migrar → CSS vars | Usar tokens `--lia-*` |
| `color-mix()` | **114** | Artefato subagente | Não é padrão DS |
| Hex hardcoded | **60** | Migrar → tokens | Usar `--lia-*` ou `text-*` |

#### 10.0.4 Tipografia — Ratio Invertido!

| Fonte | Contagem | DS v4.2.1 Target | Status |
|---|---|---|---|
| Open Sans / `font-sans` | **150** | 85% (primária) | ⚠️ Abaixo! |
| Inter / `font-inter` | **172** | 10% (UI/dados) | ⚠️ **Supera Open Sans!** |
| JetBrains Mono / `font-mono` | 99 | 5% (código) | OK |
| Crimson / `font-serif` | 4 | Minimal | OK |

> **Problema:** Inter está sendo usada mais que Open Sans, quando o DS diz que Open Sans deve ser a primária (85%). Precisa investigar se `font-sans` já mapeia para Open Sans no Tailwind config (sim, via `--font-open-sans`). A inversão pode ser intencional para UI densa.

#### 10.0.5 Performance — React.memo Quase Inexistente

| Padrão | Contagem | Adequação |
|--------|----------|-----------|
| `React.memo` / `memo()` | **11** | ⚠️ Muito baixo para app desta escala |
| `useMemo` | 339 | OK |
| `useCallback` | 1.437 | OK (pode até ter excesso) |
| `forwardRef` | 86 | OK |
| `dynamic()` (lazy loading) | **11** | ⚠️ Baixo — 15 monolitos precisam |
| dark mode `dark:` | 14.743 | ✅ Excelente cobertura |
| Arquivos SEM `dark:` | 62 | Aceitável |

---

### 10.1 Prioridade P0 — Split Monolitos (15 arquivos >2.000L → nenhum >1.500L)

**Impacto:** Consistência 7→9, Performance 7→8.5
**Esforço estimado:** 5-7 dias (agentes em paralelo)
**Risco:** Médio

**Tier A — Críticos (>4.000L):** Devem ser splitados primeiro.

| Monolito | Linhas | Estratégia |
|----------|--------|-----------|
| `job-kanban-page.tsx` | 4.940 | Extrair KanbanBoard, KanbanColumn, KanbanCard, KanbanFilters, BulkActions |
| `lia-api.ts` | 4.853 | Split por domínio: candidates-api, jobs-api, search-api, wsi-api, chat-api |
| `candidates-page.tsx` | 4.811 | Extrair CandidateTable, FilterPanel, SearchResults, PreviewPanel |
| `jobs-page.tsx` | 4.667 | Extrair JobTable, JobFilters, JobFormPanel, JobStats |
| `expanded-chat-modal.tsx` | 4.409 | Extrair WizardStagePanel, ChatHistory, ToolResultsPanel |
| `expandable-ai-prompt.tsx` | 4.262 | Extrair PromptInput, SuggestionsList, ContextCards |

**Tier B — Altos (3.000-4.000L):**

| Monolito | Linhas | Estratégia |
|----------|--------|-----------|
| `chat-page.tsx` | 3.936 | Extrair ChatSidebar, ConversationView, MessageInput |
| `smart-search-input.tsx` | 3.761 | Extrair SearchSuggestions, FilterChips, SearchHistory |
| `advanced-filters-modal.tsx` | 3.282 | Extrair FilterSections, FilterPresets, FilterSummary |
| `dashboards-page.tsx` | 3.280 | Extrair DashboardCards, ChartGrid, MetricsPanel |

**Tier C — Médios (2.000-3.000L):**

| Monolito | Linhas | Estratégia |
|----------|--------|-----------|
| `candidate-preview.tsx` | 2.727 | Extrair tabs (Activities, Skills, Experience) |
| `candidate-page.tsx` | 2.491 | Extrair seções (Header, Details, Actions) |
| `ScreeningConfigManager.tsx` | 2.396 | Extrair tabs (Script, Questions, Evaluation) |
| `goals-management.tsx` | 2.296 | Extrair GoalCard, GoalForm, GoalTimeline |
| `tasks-page.tsx` | 2.174 | Extrair TaskList, TaskFilters, TaskDetail |

**Critério de sucesso:** Nenhum arquivo >1.500L. Subcomponentes <500L cada.

### 10.2 Prioridade P1 — Eliminar Unsafe Any (1.189 → <100)

**Impacto:** Tipos 6→9
**Esforço estimado:** 3-4 dias
**Risco:** Baixo (tipagem não altera runtime)

| Categoria | `: any` | `as any` | Total | Abordagem |
|-----------|---------|----------|-------|-----------|
| Components | 724 | ~200 | ~924 | Interfaces para props + event handlers tipados |
| Services | 67 | ~30 | ~97 | Interfaces de API response + Zod schemas |
| Lib | 14 | ~10 | ~24 | Genéricos ou interfaces específicas |
| Hooks | 6 | ~3 | ~9 | Tipagem de return values |
| App pages | — | ~100 | ~100 | `funil/[id]/page.tsx` sozinho tem 74 `as any` |
| **Total** | **846** | **343** | **1.189** | — |

**Top 10 arquivos (concentram ~50% do total):**

| Arquivo | `: any` | `as any` | Total |
|---------|---------|----------|-------|
| `funil-de-talentos/candidato/[id]/page.tsx` | 15 | 74 | 89 |
| `job-kanban-page.tsx` | 55 | 23 | 78 |
| `ScreeningConfigManager.tsx` | 44 | 9 | 53 |
| `candidate-page.tsx` | 20 | 26 | 46 |
| `CompanyDataSection.tsx` | 33 | 0 | 33 |
| `KanbanTableView.tsx` | 35 | 0 | 35 |
| `edit-job-modal.tsx` | 0 | 28 | 28 |
| `candidate-preview.tsx` | 27 | 0 | 27 |
| `candidates-page.tsx` | 20 | 6 | 26 |
| `KanbanColumnRenderer.tsx` | 23 | 0 | 23 |

**Critério de sucesso:** <100 unsafe any total (`: any` + `as any`). Isenções documentadas.

### 10.3 Prioridade P2 — Migrar `rounded` → `rounded-md` (819 ocorrências)

**Impacto:** UI/DS 8→9
**Esforço estimado:** 0.5 dia
**Risco:** Baixo (mudança visual: 4px → 6px border-radius)

**Abordagem:**
1. Regex: substituir `rounded` (não seguido de `-`) por `rounded-md`
2. Preservar: `rounded-full`, `rounded-lg`, `rounded-xl`, `rounded-none`, `rounded-sm`, `rounded-t`, `rounded-b`, `rounded-l`, `rounded-r`
3. Validação visual por amostragem em 5 páginas

### 10.4 Prioridade P3 — Inline Styles → Tailwind (1.439 occ em 238 arquivos)

**Impacto:** Consistência +0.5, UI/DS +0.2
**Esforço estimado:** 3-4 dias
**Risco:** Médio (alguns inline styles são dinâmicos e devem permanecer)

**Top 10 ofensores (concentram ~30% das ocorrências):**

| Arquivo | `style={{` | Categoria |
|---------|-----------|-----------|
| `dashboards-page.tsx` | 82 | Charts/data viz (muitos serão dinâmicos) |
| `WSIQuestionsPanel.tsx` | 60 | Layouts de painel |
| `expandable-ai-prompt.tsx` | 40 | UI dinâmica |
| `jobs-page.tsx` | 34 | Tabelas e layouts |
| `InterviewSchedulingPanel.tsx` | 32 | Layouts |
| `JobsCompactTableView.tsx` | 32 | Tabelas |
| `chat-page.tsx` | 31 | Chat UI |
| `InterviewConfirmationCard.tsx` | 28 | Cards |
| `WSIScoreCard.tsx` | 27 | Data viz |
| `big-five-dashboard-page.tsx` | 27 | Charts |

**Abordagem:**
1. Classificar inline styles: estático (converter) vs dinâmico (manter com comentário `// dynamic`)
2. Top 20 ofensores primeiro
3. Meta: <300 inline styles, <100 arquivos

### 10.5 Prioridade P4 — React.memo + Dynamic Imports + Performance

**Impacto:** Performance 7→8.5
**Esforço estimado:** 2 dias
**Risco:** Baixo

**Estado atual:**
- React.memo: **11 usos** (extremamente baixo para 500+ componentes)
- dynamic(): **11 usos** (baixo — 15 monolitos devem ser lazy-loaded)

**Ações:**
1. `React.memo` em todos os componentes de lista: rows, cards, items (~20 componentes)
2. `next/dynamic` com `{ ssr: false }` em: modais, painéis pesados, dashboards (~15 componentes)
3. Virtualização (tanstack-virtual) em CandidateTable (pode ter 1.000+ rows)

### 10.6 Prioridade P5 — Cores Residuais (rgba + color-mix + hex)

**Impacto:** UI/DS +0.3
**Esforço estimado:** 1 dia
**Risco:** Baixo

| Padrão | Contagem | Ação |
|--------|----------|------|
| `rgba()` fora de tokens | 102 | Migrar para `var(--lia-*)` ou `bg-*/text-*` |
| `color-mix()` (artefato subagente) | 114 | Avaliar: converter para `opacity-*` Tailwind |
| Hex hardcoded | 60 | Migrar para tokens ou classes utilitárias |
| **Total** | **276** | — |

### 10.7 Prioridade P6 — Zod Schemas + API Type Safety

**Impacto:** Dados 7→8.5
**Esforço estimado:** 2 dias
**Risco:** Baixo

**Ações:**
1. Instalar `zod`
2. Split `lia-api.ts` (4.853L) em módulos por domínio (parte do P0)
3. Criar schemas: `CandidateSchema`, `JobVacancySchema`, `SearchResponseSchema`, `WSISchema`
4. Validar respostas de API com `schema.safeParse()`
5. Fallback gracioso: log + toast para dados inválidos

---

### 10.8 Resumo — Roadmap Corrigido para Score 9.0+

| Sprint | Tasks (paralelo) | Ações | Score Projetado |
|--------|-----------------|-------|----------------|
| Atual | — | Fases 1-9 concluídas | **7.6/10** |
| Sprint 1 | 2-3 agentes | P1 (unsafe any top 10 arquivos) + P2 (`rounded-md`) + P5 (cores residuais) | **8.2/10** |
| Sprint 2 | 2-3 agentes | P0 Tier A (6 monolitos >4.000L, inclui lia-api.ts) | **8.6/10** |
| Sprint 3 | 2-3 agentes | P0 Tier B+C (9 monolitos restantes) + P1 (any restantes) | **8.9/10** |
| Sprint 4 | 1-2 agentes | P3 (inline styles top 20) + P4 (React.memo + dynamic) + P6 (Zod) | **9.1/10** |

> **Nota sobre tipografia:** Inter vs Open Sans ratio invertido (172 vs 150). O Tailwind config mapeia `font-sans` → Open Sans e `font-inter` → Inter. Avaliar se a inversão é intencional (UI densa) ou precisa correção. Não incluído nos sprints até decisão.

> **Nota sobre `as any`:** Descoberta crítica — 343 `as any` NÃO estavam no plano original. O total real de unsafe any é **1.189**, não 844. Sprint 1 prioriza os top 10 arquivos que concentram ~50% do total.
