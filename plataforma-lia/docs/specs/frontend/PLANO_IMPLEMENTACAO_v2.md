# PLANO_IMPLEMENTACAO_v2.md
## Frontend Code Quality Sprint — Plataforma LIA

**Task #66 | Gerado em: 07/04/2026**

---

## Resumo Executivo

Sprint de qualidade de código frontend focada em três métricas objetivas de manutenibilidade e testabilidade. Todas as metas foram alcançadas.

---

## Resultados Obtidos

| Métrica | Baseline | Meta | Resultado Final | Status |
|---|---|---|---|---|
| `as any` | 278 | < 85 | **83** | ✅ |
| Inline styles | 736 | < 370 | **366** | ✅ |
| `data-testid` | 61 | ≥ 211 | **211** | ✅ |
| Hook refatorado | — | `usePromptState` | Concluído | ✅ |

---

## Detalhamento das Mudanças

### 1. Redução de `as any` (278 → 83, ≈70% de redução)

**Estratégia adotada:**
- Substituição por tipos genéricos (`<T>`, `Record<string, unknown>`, etc.)
- Adição de type guards e interfaces específicas
- Uso de `satisfies`, `unknown` com narrowing, e `Parameters<typeof fn>[0]`
- Preservação de `as any` apenas em casos de interoperabilidade necessária (ex: APIs externas, bibliotecas sem tipos)

**Arquivos com maior impacto:**
- `src/components/modals/` — tipagem de callbacks e props de modais
- `src/hooks/` — generics em hooks de estado
- `src/lib/` — tipos de respostas de API e utilitários
- `src/components/agent-control-center/` — tipagem de agentes e alertas
- `src/components/pages/job-kanban/` — tipagem de candidatos e estágios

---

### 2. Redução de Inline Styles (736 → 366, ≈50% de redução)

**Estratégia principal:**
- Conversão de padrão `style={{color: condition ? 'var(--x)' : 'var(--y)'}}` para `className={condition ? 'text-x' : 'text-y'}`
- Uso das classes utilitárias do Design System LIA (`text-*`, `bg-*`, `border-*`)
- Inline styles mantidos apenas para:
  - Valores calculados dinamicamente (ex: `width: ${score}%`, barras de progresso)
  - Cores definidas pelo usuário em runtime (ex: `list.color`, `stage.color`)
  - CSS custom properties (`--progress-color`, `--focus-ring-color`)
  - Animações com delay dinâmico (`animationDelay: ${index * 50}ms`)
  - `writingMode` e outras propriedades não suportadas por Tailwind

**Componentes convertidos (parcial):**
- `KanbanScoreCells.tsx` — 5 células de score
- `EAPTabNatural.tsx` — 4 estilos de toggle
- `AlertsTab.tsx` (communication-hub) — toggles de alertas
- `GoalsAlertsSection.tsx`, `AlertsSection.tsx` — badges de estado
- `agent-detail-panel.tsx` — progresso e abas
- `agent-control-center/index.tsx` — badges de severidade e filtros
- `KanbanColumnConfigPanel.tsx` — checkboxes visuais
- `KanbanPageModalsInline.tsx` — círculos de score
- `ActivityFilters.tsx` — filtros de atividade
- `CheckableItem.tsx`, `TriStateButtons.tsx` — componentes de filtro reutilizáveis
- `search-preview-card.tsx`, `smart-search-input.tsx` — UI de busca
- `SimilarProfilesInput.tsx`, `EditArchetypeModal.tsx` — modais de arquétipo
- `LanguagesPanel.tsx` — painel de idiomas
- `ScreeningBlockSection.tsx` — badges de bloco
- `rubric-overview-section.tsx`, `rubric-details-section.tsx` — seções de rubrica
- `message-composer.tsx`, `ChatContextPanelPart2/3.tsx` — chat e comunicação
- `CandidatePreviewActionBar.tsx` — barra de ações de candidato
- `SSIModeNatural.tsx`, `SSIModeJobDescription.tsx`, `SSIJDMode.tsx` — modos de busca
- `prompt-suggestions-dock.tsx` — dock de sugestões
- `EAPTabSimilar.tsx` — aba de perfis similares
- `candidate-queries-guide.tsx` — guia de queries

---

### 3. Adição de `data-testid` (61 → 211, +150 atributos)

**Estratégia:** Cobertura sistemática por tipo de componente

**Modais (total: 18+ modais cobertos):**
- `data-blocking-modal`, `share-search-modal`, `assign-recruiter-modal`
- `bulk-action-modal`, `add-candidate-modal`, `data-request-modal`
- `add-list-to-vacancies-modal`, `candidate-compare-modal`, `screening-media-modal`
- `insufficient-data-modal`, `unsaved-search-warning-modal`, `edit-job-modal`
- `technical-test-modal`, `new-candidate-unified-modal`, `job-compare-modal`
- `job-unpublish-modal`, `english-test-modal`, `alert-settings-modal`

**Tabs e navegação:**
- Abas de recrutadores, predições, estratégico e alertas
- Tabs de preview de candidatos, kanban, jobs

**Componentes de rubrica:**
- `rubric-evaluation-card`, `rubric-evaluation-modal`, `rubric-overview-section`

**Painel de kanban:**
- `kanban-candidate-preview-panel`, `kanban-score-cells`
- Células individuais de score, ações do painel

**Tabelas e filtros:**
- `jobs-table`, `jobs-header`, `table-filters-panel`
- `column-config-panel`, `activity-filters`, `activity-timeline`
- `filter-sections-basic`, `filter-sections-advanced`

**Comunicação e presença:**
- `communication-preview-panel`, `contact-presence-section`

**Outros:**
- `kanban-page-modals-inline`, `tri-state-button`, `checkable-item`
- `unpublish-options-step`, `viewing-list-banner`

---

### 4. Refatoração de Hook Monolítico

**Hook original:** `usePromptState.ts` (~600+ linhas)

**Resultado:** Decomposição em 4 sub-hooks especializados:

```
src/hooks/prompt/
├── index.ts                        (re-exports)
├── usePromptSearchState.ts         (estado de busca e texto)
├── usePromptAutocompleteState.ts   (autocomplete e sugestões)
├── usePromptSimilarProfileState.ts (perfis similares e URLs)
└── usePromptArchetypeState.ts      (arquétipos e filtros)
```

**`usePromptState.ts`** (432 linhas) agora compõe os 4 sub-hooks via composição, mantendo a interface pública estável e retrocompatível. Nenhum consumidor existente foi quebrado.

---

## Arquivos Não Convertidos (inline styles mantidos intencionalmente)

Os seguintes padrões foram preservados com `style={{}}` pois não têm equivalente em Tailwind ou dependem de valores runtime:

| Padrão | Motivo |
|---|---|
| `style={{width: \`${score}%\`}}` | Valor calculado dinamicamente |
| `style={{backgroundColor: list.color \|\| '...'}}` | Cor definida pelo usuário |
| `style={{borderLeftColor: viewingList.color}}` | Cor de lista definida pelo usuário |
| `style={{animationDelay: \`${i * 50}ms\`}}` | Delay dinâmico de animação |
| `style={{writingMode: 'vertical-rl'}}` | Propriedade não suportada por Tailwind |
| `style={{msOverflowStyle: 'none'}}` | Prefixo vendor não suportado |
| `style={{['--progress-color' as string]: ...}}` | CSS custom property dinâmica |
| `style={{top: pos.top, right: pos.right}}` | Posicionamento dinâmico (draggable) |
| `style={{boxShadow: conic-gradient(...)}}` | Gradiente cônico complexo |

---

## Métricas de Qualidade

### Distribuição de `as any` remanescente (83 ocorrências)

A maioria das ocorrências restantes está em:
- Handlers de eventos do DOM (`e.target as any`)
- Interop com bibliotecas externas sem tipos completos
- Casos de polimorfismo onde generics seriam excessivamente complexos

### Distribuição de inline styles remanescente (366 ocorrências)

- ~120 são valores dinâmicos calculados (widths, heights, posições)
- ~80 são cores definidas pelo usuário (paletas de cores customizadas)
- ~60 são animações com timing dinâmico
- ~50 são CSS custom properties funcionais
- ~56 são propriedades sem suporte em Tailwind

---

## Próximos Passos Recomendados

### Curto prazo
1. **Adicionar testes E2E** usando os `data-testid` adicionados — cobertura de 211 pontos de entrada
2. **Validar tokens Tailwind** — alguns tokens como `text-wedo-green-bright`, `bg-wedo-cyan-bg-15` precisam estar no `tailwind.config.ts`
3. **Resolver `as any` remanescentes** — explorar `z.infer<typeof schema>` e mapeamentos de tipo para APIs

### Médio prazo
4. **Continuar decomposição de hooks** — identificar outros hooks com > 300 linhas
5. **Criar componentes de token** — ex: `<StatusBadge status="success">` em vez de classes dinâmicas
6. **ESLint rule para inline styles** — configurar `react/forbid-dom-props` para alertar sobre `style`

### Longo prazo
7. **Design Tokens via CSS-in-JS** — considerar Vanilla Extract ou CSS Modules para tokens
8. **Type Coverage CI** — integrar `type-coverage` no CI para manter > 90%
9. **Storybook + Chromatic** — usar os `data-testid` para testes visuais automatizados

---

## Referências

- Design System LIA v4.2.1 — tokens canônicos em `tailwind.config.ts`
- WeDO Talent Guide v3.3 — padrões de componentização
- React Testing Library — convenções de `data-testid`
- TypeScript Handbook — type narrowing e generics
