# Diagnóstico Completo Front-End React × Vue — WeDOTalent

> **Objetivo:** Documento de análise e decisão para padronizar visualmente os dois produtos (React/Tailwind no Replit + Vue/Vuetify no GitHub ats_front). Cada tabela inclui coluna "Decisão / Comentários" vazia para preenchimento durante avaliação.
>
> **Fontes de dados:**
> - React: `plataforma-lia/` (Replit) — design-tokens.css, tailwind.config.ts, componentes ui/*.tsx
> - Vue: `WeDOTalent/ats_front` branch `develop` (GitHub API) — vuetify.config.ts, style.css, componentes ui/base/*.vue
> - Análise original: Cruzamento DS v4.2.2, Blocos 1-5

---

## SEÇÃO 1 — Análise Original (Blocos 1-5)

### Bloco 1 — O que o documento DS v4.2.2 cobre

#### 1.1 Border Radius
- **Documento:** Muda `rounded="xl"` (24px) → `rounded="lg"` (12px) em cards. Sidebar já tem 12px.
- **Realidade:** O documento aceita 12px como padrão Vue. Não aborda conflito com 8px do React (rounded-md). Implicitamente escolheu 12px.
- **Recomendação original:** Adotar 10px como canônico nos dois. Mais moderno que 12px, mais suave que 8px — típico de SaaS enterprise (Linear, Notion, Retool).

#### 1.2 Tipografia
- **Documento:** Fase 3 — migração f* → wedo-* com mapa completo.
- **Realidade:** Classes wedo-* já existem no style.css (branch develop):
  - Vue existente: `.wedo-display`, `.wedo-h1` a `.wedo-h5`, `.wedo-body-lg`, `.wedo-body`, `.wedo-body-sm`, `.wedo-caption`, `.wedo-label`, `.wedo-micro`
  - Proposta cria nomes diferentes: `.wedo-title`, `.wedo-heading`, `.wedo-subtitle` — vai duplicar
- **Problema:** A proposta não decide entre 11px (React) e 12px (Vue) como base. Sem decisão, texto em tamanhos diferentes nos dois produtos.
- **Recomendação original:** Base 12px para os dois. Mais legível em interfaces densas.

#### 1.3 Cores Semânticas
- **Documento:** Fase 0-B muda: error `#EF4444` → `#C74446`, warning `#F59E0B` → `#D19960`, info `#3B82F6` → `#60BED1`, success `#22C55E` → `#5DA47A`
- **Realidade:** Os dois produtos hoje têm `#EF4444`, `#F59E0B`, `#3B82F6`, `#22C55E` — iguais. A proposta cria divergência onde não existe.
- **Recomendação original:** Manter cores padrão nos dois. WeDo colors ficam para contextos específicos da plataforma. Misturar brand com semânticos universais cria ambiguidade.

#### 1.4 wedo-coral
- **Documento:** Fase 0-B adiciona `wedo-coral: #C74446` ao Vuetify.
- **Conflito:** React tem `wedo-coral: #E16162` — visivelmente diferente (#E16162 = vermelho-salmão vibrante, #C74446 = vermelho mais escuro e sóbrio).
- **Recomendação original:** Usar #C74446. Melhor contraste WCAG AA para B2B. Atualizar React também.

#### 1.5 Dark Mode WeDo Colors
- **Documento:** Fase 0-B normaliza cores WeDo do dark mode para mesmos valores do light (atualmente Vue escurece: #4DA8BB, #4B8862).
- **Avaliação:** Correto. Cores de marca não devem mudar de tom por modo — identidade visual constante.

#### 1.6 Sidebar Active State
- **Documento:** Fase 0-D muda `rgba(body-medium, 0.5)` translúcido → `surface-variant` sólido (#F3F4F6).
- **Avaliação:** Correto e alinha com React. Falta especificar timing de transição (React usa 200ms, Vue usa expand-on-hover sem timing explícito).

#### 1.7 Migração Hex Hardcoded #60bed1
- **Documento:** Fase 1 — substituir todas ocorrências de #60bed1 por tokens Vuetify.
- **Avaliação:** Correto. Faltam outros hardcoded: #0077B5 (LinkedIn, 8+ arquivos), #de1c31 (WSI score baixo), #10B981 (WSI score alto).

#### 1.8 Job Status Color → Token
- **Documento:** Fase 4 — mapa JOB_STATUS_COLOR com tokens para active/paused/completed/cancelled/urgent/draft.
- **Falta:** Não especifica como status se traduzem visualmente (chip color, text color, border). React tem variantes completas de badge.

#### 1.9 Acessibilidade (aria-labelledby)
- **Documento:** Fase 5 — adiciona aria-labelledby em v-dialog.
- **Avaliação:** Correto e necessário. Gap de acessibilidade não coberto por nenhum dos produtos.

#### 1.10 Tabelas e Badges de Vagas
- **Documento:** Fase 6 — muda density compact → comfortable em tabelas Jobs; tab counter badge; botão "Nova Vaga".
- **Falta:** Só aborda tabelas de Jobs, não generaliza. BaseTabs Vue já tem counter nativo — documento reinventa com CSS custom.

#### 1.11 Painel do Candidato
- **Documento:** Fase 7 — painel lateral 469px, avatar 48px, 4 tabs compact, chips de skills por categoria, timeline com border-left.
- **Avaliação:** Fase mais detalhada e bem especificada. Faltam: dark mode para timeline, estado vazio do painel.

#### 1.12 Sidebar Estado Aberto
- **Documento:** Fase 8 — seção "MENU" (12px/600/2.4px letter-spacing), largura 256px, labels 11px/500.
- **Falta:** Timing de transição, scrollbar customizada (Vue tem border-radius 24px + cor border-color — React não tem).

#### 1.13 Interface LIA no "Visão Geral"
- **Documento:** Fase 9 — aba "Visão Geral" deveria ser chat LIA, não tabela.
- **Avaliação:** Decisão de produto, não de design system. Bem documentado como pendente de aprovação.

### Bloco 2 — Itens na análise que o documento NÃO cobre

| Item | Impacto | Recomendação |
|------|---------|-------------|
| Paleta de etapas de pipeline (17 tons sépia/pastel + dark) | Alto | Adicionar como Fase 0-E. Copiar do React para Vue — cores mais características da interface |
| Política global de elevation no vuetify.config defaults | Alto | VCard: elevation:0, VDialog: elevation:0, VMenu: elevation:1, VNavigationDrawer: elevation:0, VSheet: elevation:0 |
| BaseButton — especificação completa | Médio | Documentar variantes primary/secondary/outline/ghost/destructive com dimensões, estados hover/focus/disabled |
| BaseInput/BaseSelect — states e tamanhos | Médio | Error state padronizado, tamanhos sm/default, prefix/suffix icon slot |
| BaseDialog — múltiplos tamanhos | Médio | xs=384px, sm=448px, md=512px, lg=672px, xl=896px |
| Overlay com backdrop-blur | Baixo | scrim-opacity="0.3" + CSS backdrop-filter: blur(1px) |
| wedo-green-light (sólido #7BC29A) | Baixo | Adicionar como token separado do rgba |
| wedo-green-pastel #A8D5B7, wedo-green-bright #60D186 | Baixo | Adicionar ao config |
| WsiScoreBadge — tokens para scores | Médio | wedo-score-high: #10B981, wedo-score-mid: #60BED1, wedo-score-low: #C74446 |
| Títulos de card (React 12px vs Vue 18px) | Médio | Decidir: 14px/600 como meio-termo |
| Scrollbar customizada | Baixo | border-radius 6px, cor rgba(border-color, 0.8), nos dois |
| Animação de modal | Baixo | fade + scale 98%, 150ms ease-out nos dois |
| Dark mode para pipeline badges | Alto | Adicionar junto com paleta de etapas |
| JetBrains Mono | Baixo | Import no Vue; usar em code, IDs técnicos, queries |
| Tab style ativo — pill vs underline | Médio | Pill (rounded-full, bg-white) nos dois para consistência |

### Bloco 3 — Itens no documento que NÃO estavam na análise

| Item do Documento | O que é | Status |
|-------------------|---------|--------|
| RISCOS DE QUEBRA (R1–R7) | Lista de riscos de implementação | Válido. R3 (prop status vs variant) e R4 (\b no sed macOS) são críticos |
| .wedo-tab-badge (Fase 6) | Classe CSS para counter em tabs | Conflita com BaseTabs (suporte nativo) — risco de duplicação |
| .wedo-sidebar-section-header (Fase 8) | Classe CSS para "MENU" | Correto, não conflita |
| .wedo-timeline-item (Fase 7) | CSS de timeline com border-left | Bem especificado, sem conflito |
| Mapa reverso hex→token (Fase 4) | Fallback se API retornar hex | Boa precaução |
| Script perl de migração f*→wedo* (Fase 3) | Automatização | Correto para macOS/Linux. R4 documenta risco |
| Score 83–87/100 | Promessa pós-implementação | Score real seria ~70–75/100 com gaps não cobertos |

### Bloco 4 — Itens que precisam de revisão

| Fase | O que está | Problema |
|------|-----------|----------|
| Fase 0-B — semantic colors | Muda para WeDo colors | Cria divergência onde hoje há alinhamento. NÃO fazer |
| Fase 0-A — remove Inter import | Remove fonte Inter do style.css | Inter é usada em wedo-label/wedo-micro. Remover quebra tipografia silenciosamente |
| Fase 3 — wedo-overline/caption/label | Cria novas classes | wedo-caption, wedo-label já existem — vai duplicar ou sobrescrever |
| Fase 6 — .wedo-tab-badge CSS custom | Cria classe nova | BaseTabs.vue já tem counter badge nativo — dois sistemas paralelos |
| Score 83–87/100 | Promessa pós-implementação | Irrealista com gaps não cobertos (pipeline palette, elevation, border-radius, font-base) |

### Bloco 5 — Decisões recomendadas (original)

| # | Decisão | Recomendação | Justificativa |
|---|---------|-------------|---------------|
| 1 | Border radius | 10px nos dois | Middle ground moderno. Atualizar $border-radius-root no Vuetify e rounded-md no Tailwind |
| 2 | Font size base | 12px nos dois | Legibilidade em interfaces densas. Atualizar text-xs do React de 11px para 12px |
| 3 | Cores semânticas | Manter #EF4444 etc. nos dois | Já alinhados. Não criar divergência. WeDo colors para contextos específicos |
| 4 | wedo-coral canônico | #C74446 nos dois | Melhor contraste WCAG. Atualizar React de #E16162 para #C74446 |
| 5 | Sombras | Sutíssimas nos dois | box-shadow: 0 1px 2px rgba(0,0,0,0.04). React já tem tokens. Vue usa elevation apenas onde necessário |

---

## SEÇÃO 2 — Tabelas Comparativas com Dados Reais

> Dados extraídos de: React (`plataforma-lia/` local) e Vue (`ats_front` GitHub API, branch `develop`)

### 2.1 Cores — Paleta Primária e de Marca

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 1 | Primary color | `#111827` (gray-900) via --lia-btn-primary-bg | `#111827` (primary em vuetify.config) | ✓ Igual | Manter | |
| 2 | Primary dark mode | `#F9FAFB` via --lia-btn-primary-bg(.dark) | `#F9FAFB` (primary em darkTheme) | ✓ Igual | Manter | |
| 3 | wedo-cyan | `#60BED1` via --wedo-cyan + tailwind | `#60BED1` em vuetify.config + style.css :root | ✓ Igual | Manter | |
| 4 | wedo-green | `#5DA47A` via --wedo-green | `#5DA47A` em vuetify.config | ✓ Igual | Manter | |
| 5 | wedo-orange | `#D19960` via --wedo-orange | `#D19960` em vuetify.config | ✓ Igual | Manter | |
| 6 | wedo-purple | `#9860D1` via --wedo-purple + tailwind | `#9860D1` em vuetify.config | ✓ Igual | Manter | |
| 7 | wedo-magenta | `#D160AB` via --wedo-magenta | `#D160AB` em vuetify.config | ✓ Igual | Manter | |
| 8 | wedo-coral | `#E16162` em tailwind.config | Não existe no vuetify.config (proposta: `#C74446`) | ⚠️ Diverge | #C74446 nos dois (melhor contraste WCAG) | |
| 9 | wedo-cyan dark mode | `#60BED1` (mantém mesmo valor) | `#4DA8BB` (escurece) em darkTheme | ⚠️ Diverge | Manter #60BED1 — marca não muda por modo | |
| 10 | wedo-green dark mode | `#5DA47A` (mantém) | `#4B8862` (escurece) | ⚠️ Diverge | Manter #5DA47A | |
| 11 | wedo-orange dark mode | `#D19960` (mantém) | `#B8814D` (escurece) | ⚠️ Diverge | Manter #D19960 | |
| 12 | wedo-purple dark mode | `#9860D1` (mantém) | `#7F4DB8` (escurece) | ⚠️ Diverge | Manter #9860D1 | |
| 13 | wedo-magenta dark mode | `#D160AB` (mantém) | `#B84D92` (escurece) | ⚠️ Diverge | Manter #D160AB | |
| 14 | Brand primary (LIA coral) | `#C74446` via --lia-brand-primary | Não existe como token | ⚠️ Ausente Vue | Adicionar ao vuetify.config | |
| 15 | wedo-green-light (sólido) | `#7BC29A` em tailwind.config | Só tem `rgba(93,164,122,0.1)` | ⚠️ Diverge | Adicionar #7BC29A ao Vue | |
| 16 | wedo-green-pastel | `#A8D5B7` em --wedo-green-light | Não existe | ⚠️ Ausente Vue | Adicionar | |
| 17 | wedo-green-bright | `#60D186` em --wedo-green-success | Não existe | ⚠️ Ausente Vue | Adicionar | |
| 18 | wedo-amber | `#F59E0B` via --wedo-amber | Não existe em vuetify.config | ⚠️ Ausente Vue | Adicionar | |

### 2.2 Cores — Semânticas e Status

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 19 | error | `#EF4444` (Tailwind default) | `#EF4444` em vuetify.config | ✓ Igual | Manter. NÃO mudar para #C74446 | |
| 20 | warning | `#F59E0B` | `#F59E0B` em vuetify.config | ✓ Igual | Manter | |
| 21 | info | `#3B82F6` | `#3B82F6` em vuetify.config | ✓ Igual | Manter | |
| 22 | success | `#22C55E` | `#22C55E` em vuetify.config | ✓ Igual | Manter | |
| 23 | WSI score high | `#10B981` hardcoded | `#10B981` hardcoded em WsiScoreBadge | ✓ Igual | Tokenizar nos dois | |
| 24 | WSI score low | `#C74446` / `#de1c31` hardcoded | `#de1c31` hardcoded | ⚠️ Ambíguo | Unificar: #C74446 como token | |

### 2.3 Cores — Surface e Background

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 25 | Background principal | `#FFFFFF` via --lia-bg-primary | `#f9fafb` em vuetify background | ⚠️ Diverge | Decidir: branco puro ou off-white | |
| 26 | Background dark | `#0F1113` via --lia-bg-primary(.dark) | `#1A1D1F` em vuetify dark background | ⚠️ Diverge | Unificar. React mais escuro | |
| 27 | Surface | `#FFFFFF` via --lia-bg-elevated | `#ffffff` em vuetify surface | ✓ Igual | Manter | |
| 28 | Surface dark | `#1A1D1F` via --lia-bg-secondary(.dark) | `#0F1113` em vuetify dark surface | ⚠️ Invertido | React: bg=#0F, surface=#1A. Vue: bg=#1A, surface=#0F. Alinhar | |
| 29 | Surface variant | `#F3F4F6` via --lia-bg-tertiary | `#F3F4F6` em vuetify surface-variant | ✓ Igual | Manter | |
| 30 | Border color | `#E5E7EB` via --lia-border-subtle | `#E5E7EB` em vuetify border-color | ✓ Igual | Manter | |
| 31 | Border dark | `#2D3748` via --lia-border-subtle(.dark) | `#374151` em vuetify dark border-color | ⚠️ Diverge | Unificar para #374151 | |

### 2.4 Tipografia

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 32 | Font family principal | Open Sans (via layout.tsx + design-tokens) | Open Sans (via style.css body + @import) | ✓ Igual | Manter | |
| 33 | Font family dados | Inter (via tailwind fontFamily.data) | Inter (via @import + .wedo-micro + .font-data) | ✓ Igual | Manter | |
| 34 | Font family serif | Source Serif 4 (via tailwind fontFamily.sidebar) | Source Serif 4 (via @import + .font-serif) | ✓ Igual | Manter | |
| 35 | Font family mono | JetBrains Mono (via layout.tsx) | Não importada | ⚠️ Ausente Vue | Adicionar import + usar em code blocks | |
| 36 | Font size base UI | `text-[11px]` (0.6875rem) via text-xs override | `12px` (.f12 + BaseInput font-size: 12px) | ⚠️ Diverge | Decidir: 11px vs 12px canônico | |
| 37 | Display | `.lia-h1` 2rem/600 | `.wedo-display` 2.5rem/700 | ⚠️ Diverge | Vue tem display extra. Decidir se React precisa | |
| 38 | H1 | 2rem/600 | `.wedo-h1` 2rem/700 | ⚠️ Peso difere | Unificar: 700 ou 600? | |
| 39 | H2 | 1.5rem/600 | `.wedo-h2` 1.5rem/700 | ⚠️ Peso difere | Unificar | |
| 40 | H3 | 1.25rem/600 | `.wedo-h3` 1.25rem/600 | ✓ Igual | Manter | |
| 41 | H4 | 1rem/600 | `.wedo-h4` 1rem/600 | ✓ Igual | Manter | |
| 42 | H5 | Não existe como classe lia-h5 | `.wedo-h5` 0.875rem/600 | ⚠️ Ausente React | Avaliar necessidade | |
| 43 | Body | `.lia-body` 0.875rem/400 | `.wedo-body` 0.875rem/400 | ✓ Igual | Manter | |
| 44 | Body small | `.lia-body-sm` 0.8125rem/400 | `.wedo-body-sm` 0.75rem/400 | ⚠️ Diverge | React 13px vs Vue 12px. Decidir | |
| 45 | Caption | `.lia-caption` 0.6875rem/500 uppercase | `.wedo-caption` 0.75rem/400 | ⚠️ Diverge | Tamanho e peso diferentes | |
| 46 | Label | `.lia-label` 0.875rem/500 | `.wedo-label` 0.6875rem (sem peso definido) | ⚠️ Diverge | React 14px vs Vue 11px — grande diferença | |
| 47 | Micro | Não existe | `.wedo-micro` Inter 0.625rem/500 | ⚠️ Ausente React | Avaliar necessidade | |
| 48 | Line height global | 1.4 (via design-tokens) | 1.5 (via style.css body) | ⚠️ Diverge | Decidir: 1.4 vs 1.5 | |
| 49 | Letter spacing body | `-0.01em` (via style.css) | `-0.01em` (via style.css) | ✓ Igual | Manter | |
| 50 | Classes f8-f32 utilitárias | Não existem | `f8` a `f32` (12 classes utilitárias) | ⚠️ Legado Vue | Migrar para wedo-* e remover | |

### 2.5 Spacing, Layout e Estrutura

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 51 | Border radius padrão | `rounded-md` = `calc(var(--radius) - 2px)` ≈ 6-8px | `12px` global (VBtn rounded: '12px', .rounded-12px) | ⚠️ Diverge | Decidir: 8px, 10px, ou 12px canônico | |
| 52 | Shadow sm | `0 1px 2px 0 rgb(0 0 0 / 0.02)` | `.shadow-sm` = `0 1px 2px 0 rgb(0 0 0 / 0.05)` | ⚠️ Diverge | React mais sutil. Decidir | |
| 53 | Shadow default | `0 1px 3px 0 rgb(0 0 0 / 0.05)` | Usa Vuetify elevation system | ⚠️ Diferente abordagem | Desativar elevation global no Vue. Usar shadow tokens | |
| 54 | Elevation global Vuetify | N/A | Ativa por default (Material shadows automáticas) | ⚠️ Problema Vue | Adicionar defaults: VCard:{elevation:0}, VDialog:{elevation:0}, etc. | |
| 55 | Card border-radius | 12px via .lia-card | `rounded-lg` default no BaseCard | ✓ Similar | Confirmar valor exato do rounded-lg no Vuetify | |
| 56 | Card shadow | `0 1px 3px rgba(0,0,0,0.04)` via .lia-card | Sem shadow definido (usa elevation) | ⚠️ Diverge | Usar shadow token no Vue | |
| 57 | Card title font size | `text-xs` (11px) via card.tsx | `18px` font-weight 700 via BaseCard.vue | ⚠️ Grande divergência | 18px muito grande vs 11px muito pequeno. Meio-termo: 14px/600 | |
| 58 | Card padding | `p-6` (24px) | `pa-6` (24px) | ✓ Igual | Manter | |
| 59 | Container padding | 1rem(default) → 6rem(2xl) via tailwind | Não definido — Vuetify grid system | ⚠️ Abordagem diferente | Documentar equivalência | |
| 60 | Breakpoints | sm:640 md:768 lg:1024 xl:1280 2xl:1536 | Vuetify: xs:0 sm:600 md:960 lg:1280 xl:1920 | ⚠️ Diverge | Vuetify breakpoints são diferentes por design. Documentar mapeamento | |

### 2.6 Componentes Base

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 61 | Button — variantes | 6: default, destructive, outline, secondary, ghost, link | 4: primary, secondary, ghost, destructive (BaseButton.vue) | ⚠️ Diverge | Vue faltam outline e link. Adicionar? | |
| 62 | Button — tamanhos | 4: default(h-10), sm(h-9), lg(h-11), icon(h-10 w-10) | 4: xs(26px), sm(32px), md(36px), lg(44px) via Vuetify size | ⚠️ Diverge | Alturas diferentes. React h-10=40px, Vue md=36px | |
| 63 | Button — border-radius | `rounded-md` ≈ 6px | `12px` via componentDefaults | ⚠️ Diverge | Alinhar com decisão #51 | |
| 64 | Button — font size | `text-[11px]` | `.wedo-label` = 0.6875rem (11px) via class | ✓ Igual | Manter 11px | |
| 65 | Button — text transform | `text-none` (normal case) | `text-none` via class | ✓ Igual | Manter | |
| 66 | Input — altura | `h-10` (40px) | density `compact` (~36px) via BaseInput | ⚠️ Diverge | Decidir: 36px vs 40px | |
| 67 | Input — border-radius | `rounded-md` ≈ 6px | `12px` (VTextField rounded: '12px') | ⚠️ Diverge | Alinhar com decisão #51 | |
| 68 | Input — font size | `text-[11px]` | `12px !important` (BaseInput scoped CSS) | ⚠️ Diverge | Alinhar com decisão #36 | |
| 69 | Input — variante | border via `border-gray-300` | `outlined` variant (Vuetify) | ✓ Similar | Ambos usam borda — OK | |
| 70 | Input — focus | `border-gray-500 ring-gray-900/20` | Vuetify default focus + `border-color` token | ⚠️ Diverge | React usa gray, Vue usa Vuetify primary. Alinhar | |
| 71 | Input — placeholder color | `#9CA3AF` via --lia-input-placeholder | `body-lighter` = `#6B7280` via BaseInput CSS | ⚠️ Diverge | React mais claro. Decidir | |
| 72 | Select — altura | `h-10` (40px) | density `compact` via BaseSelect | ⚠️ Diverge | Alinhar com Input | |
| 73 | Select — dropdown border | Vuetify default | `border-sm border-border-color` via componentDefaults.VSelect.listProps | ✓ Customizado | OK — Vue tem border explícita | |
| 74 | Tabs — estilo ativo | Pill: `rounded-full bg-white text-gray-900` | Underline: `border-bottom` (Vuetify v-tabs default) | ⚠️ Grande divergência | Pill vs underline — decisão de produto importante | |
| 75 | Tabs — font size | `text-[11px]` | `11px` via .v-tab CSS | ✓ Igual | Manter | |
| 76 | Badge — variantes | 8: default, secondary, destructive, outline, success, warning, info, lilac | WsiScoreBadge + BaseChip (chip como badge) | ⚠️ Diverge | Vue não tem sistema de badge equivalente | |
| 77 | Badge — border-radius | `rounded-full` (pill) | BaseChip com Vuetify chip styling | ⚠️ Verificar | Confirmar se pill no Vue | |
| 78 | Dialog — overlay | `bg-black/30 backdrop-blur-[1px]` | Vuetify scrim (default opaco sem blur) | ⚠️ Diverge | Adicionar backdrop-blur ao Vue | |
| 79 | Dialog — max-width | `max-w-lg` (512px) default | Prop `maxWidth` no BaseDialog (default varia) | ⚠️ Verificar | Definir tamanhos padrão: xs/sm/md/lg/xl | |
| 80 | Dialog — border-radius | `rounded-md` | BaseCard `rounded-lg` dentro do dialog | ⚠️ Diverge | Alinhar com decisão #51 | |
| 81 | Avatar — tamanho default | `h-10 w-10` (40px) | `medium` = 40px via BaseAvatar size map | ✓ Igual | Manter | |
| 82 | Avatar — fallback | `bg-muted` com iniciais | Iniciais com `color` prop | ✓ Similar | OK | |
| 83 | Switch — estilo | Shadcn/Radix switch | Vuetify VSwitch `inset` (BaseSwitch) | ⚠️ Diferente framework | Visual pode diferir. Verificar resultado | |
| 84 | Toast — posição | `top-0` mobile, `bottom-0` sm+ | `vue-toastification` plugin (posição configurável) | ⚠️ Verificar | Alinhar posições | |
| 85 | Tooltip — estilo | `rounded-md border bg-popover px-3 py-1.5` | Vuetify VTooltip (sem background override: `background: none !important`) | ⚠️ Diverge | Vue remove bg do tooltip. Verificar visual | |
| 86 | Progress — estilo | `h-2 rounded-full bg-gray-100`, indicator `bg-gray-900` | Vuetify VProgressLinear | ⚠️ Verificar | Confirmar se estilo alinha | |
| 87 | Skeleton/Loading | `animate-pulse rounded-md bg-gray-200`, 4 variantes | Vuetify VSkeletonLoader | ✓ Similar | Frameworks diferentes mas função igual | |
| 88 | Separator | `bg-gray-200 h-[1px]` | Vuetify VDivider | ✓ Similar | OK | |

### 2.7 Componentes Complexos

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 89 | Sidebar — largura collapsed | 64px | `rail-width="64"` em sidebar.vue | ✓ Igual | Manter | |
| 90 | Sidebar — largura expandida | 200-450px (default 256px) via resizable | 256px implícito (Vuetify drawer) + expand-on-hover | ⚠️ Similar | React é resizable, Vue é hover-expand. Abordagem diferente | |
| 91 | Sidebar — active state | `bg-gray-100 dark:bg-gray-800 font-semibold` | `rgba(body-medium, 0.5)` translúcido | ⚠️ Diverge | Vue deve mudar para surface-variant sólido (#F3F4F6) | |
| 92 | Sidebar — section header | `text-xs tracking-[0.2em]` uppercase | `f12 text-body-dark font-weight-medium pt-4 pb-3 px-4` + letter-spacing: 0.2em | ✓ Similar | Quase igual — confirmar font-size | |
| 93 | Sidebar — border-right | `border-r border-gray-100` | `border-color: rgba(var(--v-theme-border-color), 1)` | ✓ Similar | Ambos usam border sutil | |
| 94 | Top Bar / Menu | Custom top-bar.tsx (px-2 py-3, avatar h-7 w-7) | Menu component separado + AdminSidebar | ⚠️ Estrutura diferente | Estrutura de layout é diferente — documento para referência | |
| 95 | Table — estrutura | Resizable table custom | `.custom-table` + `data-table` + wrapper.vue | ⚠️ Abordagem diferente | React: componente resizable. Vue: custom HTML table com 30+ cell types | |
| 96 | Table — row height | Configurável | `36px` via `.custom-table tbody tr` | ⚠️ Verificar | Documentar altura canônica | |
| 97 | Table — header sticky | Via componente | `position: sticky; top: 0` via CSS | ✓ Similar | OK | |
| 98 | Table — hover row | Via componente classes | `rgba(primary, 0.1)` via CSS | ✓ Implementado | OK | |
| 99 | Table — scrollbar | Custom scroll-area component | CSS global customizado (16px, border-radius 20px, thumb rgba) | ⚠️ Abordagem diferente | Vue tem scrollbar global customizada, React usa componente | |
| 100 | Chat — componente | Custom chat components | DomainChat + StreamingMessage + ChatCodeBlock + etc. (10+ componentes) | ⚠️ Verificar | Garantir que estilos de chat alinhem | |
| 101 | Stepper/Wizard | Job wizard custom stepper | `stepper/header.vue` | ⚠️ Verificar | Comparar visual | |
| 102 | Breadcrumbs | Custom com GLOBAL/Cliente badges | `breadcrumbs/index.vue` | ⚠️ Verificar | Verificar se badges usam mesmos tokens | |
| 103 | Layout — splitpanes | Não usa | `splitpanes` (layouts/user.vue: 70/30 split) | ⚠️ Exclusivo Vue | Feature do Vue. React não precisa replicar | |
| 104 | Tiptap editor | Não existe | Tiptap com extensões (table, image, link, etc.) | ⚠️ Exclusivo Vue | Feature do Vue | |
| 105 | Vue Flow (diagramas) | Não existe | `@vue-flow/core` com customNode | ⚠️ Exclusivo Vue | Feature do Vue | |

### 2.8 Padrões de Interação e Dark Mode

| # | Elemento | React (Replit) | Vue (GitHub) | Status | Recomendação | Decisão / Comentários |
|---|----------|---------------|-------------|--------|-------------|----------------------|
| 106 | Transição global | `200ms ease` / `cubic-bezier` | `0.2s ease` / `0.3s ease` (vários no CSS) | ⚠️ Similar | Padronizar: 200ms ease nos dois | |
| 107 | Modal animação | Fade + scale (Radix) | `dialog-bottom-transition` (Vuetify default) | ⚠️ Diverge | Padronizar: fade + scale 98%, 150ms ease-out | |
| 108 | Keyboard: Ctrl+B | Toggle sidebar | Não implementado | ⚠️ Ausente Vue | Implementar no Vue | |
| 109 | Keyboard: Ctrl+K | Command palette | Não implementado | ⚠️ Ausente Vue | Implementar no Vue | |
| 110 | Dark mode toggle | Classe `.dark` no html | `localStorage 'app-theme-preference'` | ✓ Ambos têm | Mecanismo diferente mas funcional | |
| 111 | Dark mode text hierarchy | 4 níveis: #F9FAFB → #E5E7EB → #9CA3AF → #6B7280 | Via Vuetify tokens: heading → body → body-light → body-lighter | ✓ Similar | Valores muito próximos. OK | |
| 112 | Scrollbar custom | Via scroll-area componente (rounded-full bg-gray-200 hover:bg-gray-300) | CSS global (16px, border-radius 20px, rgba thumb) | ⚠️ Abordagem diferente | Unificar visual: 6px thumb, border-radius 6px | |
| 113 | anti-aliasing | `-webkit-font-smoothing: antialiased` via globals.css | Mesmo via style.css | ✓ Igual | Manter | |
| 114 | !important usage | Mínimo (design-tokens sem !important) | Extensivo (93+ usos de !important no style.css) | ⚠️ Problema Vue | Reduzir !important no Vue gradualmente | |

---

## SEÇÃO 3 — Tabela-Mestra de Decisões por Prioridade

### P0 — Bloqueantes (divergências que causam incoerência visual imediata)

| # | Item | React | Vue | Ação Necessária | Decisão / Comentários |
|---|------|-------|-----|----------------|----------------------|
| 8 | wedo-coral hex | #E16162 | Proposto #C74446 | Escolher um valor e aplicar nos dois | |
| 9-13 | wedo-* dark mode (5 cores) | Mantém valores light | Escurece (#4DA8BB etc.) | Vue deve manter valores light no dark mode | |
| 19 | error semantic color | #EF4444 | #EF4444 (proposta muda para #C74446) | NÃO mudar. Manter alinhado | |
| 25 | Background principal light | #FFFFFF | #F9FAFB | Escolher: branco puro ou off-white | |
| 26-28 | Background/surface dark | bg:#0F1113 surface:#1A1D1F | bg:#1A1D1F surface:#0F1113 | Invertidos entre os produtos. Alinhar | |
| 54 | Elevation global Vuetify | N/A (sem elevation) | Ativa por default | Desativar: elevation:0 nos defaults do vuetify.config | |
| 57 | Card title font size | 11-12px | 18px/700 | Enorme diferença visual. Decidir tamanho canônico | |
| 74 | Tabs estilo ativo | Pill (rounded-full) | Underline (border-bottom) | Decisão de produto: pill ou underline nos dois? | |

### P1 — Importantes (componentes com specs diferentes)

| # | Item | React | Vue | Ação Necessária | Decisão / Comentários |
|---|------|-------|-----|----------------|----------------------|
| 36 | Font size base UI | 11px | 12px | Escolher tamanho canônico para os dois | |
| 38-39 | H1/H2 font weight | 600 | 700 | Unificar peso de headings | |
| 44 | Body small | 13px (0.8125rem) | 12px (0.75rem) | Escolher tamanho canônico | |
| 46 | Label font size | 14px (0.875rem) | 11px (0.6875rem) | Grande diferença. Decidir | |
| 51 | Border radius global | ~6-8px | 12px | Decisão estrutural: qual valor canônico? | |
| 61 | Button variantes | 6 variantes | 4 variantes | Vue faltam outline e link | |
| 62 | Button alturas | 40px default | 36px default | Decidir altura canônica | |
| 66 | Input altura | 40px | ~36px | Decidir altura canônica | |
| 71 | Input placeholder color | #9CA3AF | #6B7280 | Decidir tom | |
| 76 | Badge sistema | 8 variantes estruturadas | Chip genérico | Vue precisa sistema de badge equivalente | |
| 78 | Dialog overlay | blur(1px) + 30% opacity | Vuetify scrim sem blur | Adicionar backdrop-blur ao Vue | |
| 91 | Sidebar active | bg sólido #F3F4F6 | rgba translúcido | Vue mudar para sólido | |
| 107 | Modal animação | fade + scale | bottom-transition | Padronizar animação | |

### P2 — Desejáveis (alinhamento fino)

| # | Item | React | Vue | Ação Necessária | Decisão / Comentários |
|---|------|-------|-----|----------------|----------------------|
| 14 | Brand primary token | Existe (#C74446) | Não existe | Adicionar ao vuetify.config | |
| 15-18 | Tokens green/amber extras | Existem | Não existem | Adicionar variantes ao Vue | |
| 31 | Border dark mode | #2D3748 | #374151 | Pequena diferença — unificar | |
| 35 | JetBrains Mono | Importada | Não importada | Adicionar ao Vue | |
| 48 | Line height global | 1.4 | 1.5 | Decidir canônico | |
| 50 | Classes f8-f32 | Não existem | 12 classes utilitárias legado | Migrar para wedo-* no Vue | |
| 85 | Tooltip background | bg-popover | `background: none !important` | Verificar e alinhar | |
| 106 | Transição padrão | 200ms | 200-300ms variado | Padronizar 200ms | |
| 112 | Scrollbar visual | Componente dedicado | CSS global | Unificar dimensões e cores | |

### P3 — Futuro (nice-to-have)

| # | Item | React | Vue | Ação Necessária | Decisão / Comentários |
|---|------|-------|-----|----------------|----------------------|
| 37 | Display heading | Não tem | .wedo-display 2.5rem | Avaliar necessidade no React | |
| 42 | H5 heading | Não tem | .wedo-h5 0.875rem | Avaliar necessidade no React | |
| 47 | Micro text | Não tem | .wedo-micro Inter 10px | Avaliar necessidade no React | |
| 60 | Breakpoints | Tailwind padrão | Vuetify padrão | Diferentes por natureza dos frameworks | |
| 83 | Switch visual | Radix | Vuetify inset | Frameworks diferentes — aceitar variação | |
| 103-105 | Features exclusivas Vue | N/A | Splitpanes, Tiptap, Vue Flow | Não precisam existir no React | |
| 108-109 | Keyboard shortcuts | Ctrl+B, Ctrl+K | Não implementados | Implementar no Vue quando possível | |
| 114 | !important no CSS | Mínimo | Extensivo (93+) | Refatorar gradualmente | |

---

## SEÇÃO 4 — Referências de Mercado

### Border Radius
- **ElevenLabs:** 8px para botões, 12px para cards e modais
- **Notion:** 3-4px para botões, 8px para cards, 12px para modais
- **Linear:** 6px para botões, 8px para cards
- **Vercel:** 6px global, 8px para cards maiores
- **Tendência 2025-2026:** 8-10px é o sweet spot para SaaS enterprise

### Tipografia Base
- **ElevenLabs:** 13px base, Inter
- **Notion:** 14px base, Inter para UI
- **Linear:** 13px base, Inter
- **Vercel:** 14px base, Inter/Geist
- **Tendência:** 12-14px para interfaces densas de dados, 14-16px para content-heavy

### Paleta de Cores
- **ElevenLabs:** Monocromática sépia com 1 cor de acento (verde)
- **Notion:** Grayscale + 9 cores suaves para categorias
- **Linear:** Grayscale + roxo brand + cores de status padrão
- **Vercel:** Preto/branco puro + azul brand minimal
- **WeDO atual:** 5 cores de marca (cyan, green, orange, purple, magenta) + semânticas — mais cores que a maioria dos concorrentes

### Sombras
- **ElevenLabs:** Quase nenhuma sombra, usa borders sutis
- **Notion:** Shadow muito sutil (0.04 opacity) apenas em dropdowns
- **Linear:** Shadow mínima, usa borders e backgrounds
- **Vercel:** 1 nível de shadow sutil
- **Material Design (Vuetify default):** 5 níveis de elevation com sombras pronunciadas — é isso que precisa ser desativado no Vue

### Animações
- **ElevenLabs:** 150ms para micro-interações, 300ms para transições de página
- **Notion:** 200ms para quase tudo
- **Linear:** 150-200ms, cubic-bezier para fluidez
- **Tendência:** 150-200ms com ease ou cubic-bezier(0.4, 0, 0.2, 1)

---

## RESUMO EXECUTIVO

**Estado atual:** Os dois produtos compartilham a mesma paleta WeDo (cyan, green, orange, purple, magenta) e a mesma fonte principal (Open Sans). Há **18 itens alinhados** e **~40 itens com divergência** que afetam a coerência visual.

**3 divergências mais impactantes:**
1. **Border radius** (React ~6-8px vs Vue 12px) — afeta TODOS os componentes
2. **Card title** (React 11px vs Vue 18px) — diferença visual brutal
3. **Tabs estilo** (React pill vs Vue underline) — experiência de navegação diferente

**3 problemas do Vue que independem de decisão:**
1. Elevation do Material Design ativa por default — sombras indesejadas
2. Dark mode escurece cores de marca — deveria manter consistência
3. 93+ usos de `!important` no CSS global — dificulta manutenção

**Próximo passo:** Preencher a coluna "Decisão / Comentários" nos itens P0, depois P1. Cada decisão tomada se transforma em uma ação específica de implementação.
