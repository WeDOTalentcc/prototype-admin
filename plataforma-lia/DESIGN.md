---
name: WeDOTalent Platform
description: The Quiet Operator — recruitment platform UI for the LIA AI agent + recruiter workbench
colors:
  paper: "#FFFFFF"
  chalk: "#F9FAFB"
  powder: "#F3F4F6"
  mist: "#E5E7EB"
  pebble: "#D1D5DB"
  fog: "#9CA3AF"
  ash: "#6B7280"
  slate: "#4B5563"
  graphite: "#1F2937"
  ink: "#030712"
  lia-cyan: "#60BED1"
  lia-cyan-hover: "#4DA8BB"
  coral-quiet: "#C74446"
  forest-green: "#5DA47A"
  amber-warning: "#D19960"
  insight-purple: "#9860D1"
  alert-magenta: "#D160AB"
  status-success: "#16A34A"
  status-error: "#DC2626"
  status-warning: "#D97706"
typography:
  display:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
  caption:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.05em"
  micro:
    fontFamily: "Open Sans, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 400
    lineHeight: 1.3
rounded:
  sm: "4px"
  md: "6px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-secondary:
    backgroundColor: "{colors.powder}"
    textColor: "{colors.graphite}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.graphite}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-destructive:
    backgroundColor: "{colors.status-error}"
    textColor: "{colors.paper}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-outline:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  input-default:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "40px"
  card-default:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.lg}"
    padding: "24px"
  badge-default:
    backgroundColor: "{colors.powder}"
    textColor: "{colors.graphite}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  badge-info:
    backgroundColor: "{colors.lia-cyan}"
    textColor: "{colors.paper}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  badge-success:
    backgroundColor: "{colors.forest-green}"
    textColor: "{colors.paper}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
---

# Design System: WeDOTalent Platform

## 1. Overview

**Creative North Star: "The Quiet Operator"**

A WeDOTalent é um sistema de design que prefere não se apresentar. A maior parte
do produto é monocromática — 90% gray scale, branco, preto suave — e o trabalho
visual é carregado por hierarquia tipográfica e densidade controlada. Cor entra
no jogo em pontos específicos: quando a LIA está agindo (LIA Cyan), quando um
candidato avança (verde), quando uma decisão precisa de atenção (amber). Toda
cor é funcional.

A inspiração explícita do código é Linear (densidade calma), Vercel (admin sem
gritar) e ElevenLabs (UI que serve produto, não marca). O sistema rejeita os
reflexos típicos de ATS brasileiro (Gupy / Kenoby densos de planilha+formulário),
SaaS infantil (azul + amarelo + vermelho saturados simultâneos, blobs amorfos)
e chatbot brincalhão emoji-heavy (Drift / Intercom widget cheia de comemoração
performática).

**Key Characteristics:**
- Monocromático por default, cor por função
- Open Sans single-family typography
- Flat-by-default — shadow só em modal / popover / elevated card em hover
- rounded-md (6px) em controles, rounded-xl (12px) em cards, rounded-full em badges
- Dark mode mandatório, paridade total entre light e dark
- Animações Radix desligadas globalmente (decisão arquitetural) — apenas hover
  reactions e field sync animations sobrevivem, com `prefers-reduced-motion`
  respeitado

## 2. Colors: The Monochromatic Operator Palette

Paleta sóbria com 10 stops de cinza canonical + 7 acentos funcionais + 3 status
semânticos obrigatórios (WCAG 1.4.1 / 1.4.3). Toda surface usa 90% gray scale,
acento só quando há significado.

### Primary
- **LIA Cyan** (`#60BED1`): exclusivo pra LIA / IA. Aparece em loaders, badges
  de IA, ThinkingStepsCard, focus rings em surfaces de chat. Quando você vê
  cyan na tela, a LIA está envolvida. Marca presença, nunca decora.

### Secondary
- **Coral Quiet** (`#C74446`): vermelho-coral histórico da identidade LIA.
  **USO MÍNIMO** — destrutivo (delete confirmado, erro crítico) e cases
  isolados onde "marca LIA" precisa aparecer (login, surfaces brand-adjacent).

### Tertiary (acentos funcionais — cada um carrega 1 papel semântico)
- **Forest Green** (`#5DA47A`): candidatos, sucesso, aprovação.
- **Amber Warning** (`#D19960`): warning operacional, prazos próximos.
- **Insight Purple** (`#9860D1`): insights, análises IA, relatórios premium.
- **Alert Magenta** (`#D160AB`): urgência crítica, prioridade máxima (raro).

### Status (semânticos obrigatórios — WCAG)
- **Status Success** (`#16A34A`): aprovado, contratado, ação concluída.
- **Status Error** (`#DC2626`): reprovado, erro, ação destrutiva.
- **Status Warning** (`#D97706`): pendente, atenção.

### Neutral (gray scale canonical — 10 stops)
- **Paper** (`#FFFFFF`): surface principal, cards, modals.
- **Chalk** (`#F9FAFB`): bg de página, hover muito sutil.
- **Powder** (`#F3F4F6`): bg alternada, button secondary, hover de ghost.
- **Mist** (`#E5E7EB`): border padrão, divisores, bg de inputs.
- **Pebble** (`#D1D5DB`): pipeline early stages, border de input em foco frouxo.
- **Fog** (`#9CA3AF`): text disabled, placeholder.
- **Ash** (`#6B7280`): text muted, icons.
- **Slate** (`#4B5563`): text secondary, labels descritivas.
- **Graphite** (`#1F2937`): text body, content principal.
- **Ink** (`#030712`): text máxima ênfase, button primary background.

### Named Rules

**The 90/10 Rule.** Acento funcional fica em ≤10% de qualquer tela. Se você conta
4 cores diferentes simultaneamente fora de gray scale na mesma view, refatore.

**The LIA Cyan Exclusivity Rule.** LIA Cyan **só** aparece quando a IA está
envolvida. Não usar cyan como "destaque qualquer" — quebra o sinal canônico
que treina o recrutador a reconhecer a presença da LIA.

**The Brand Restraint Rule.** Coral Quiet (`#C74446`) é da marca, não do produto.
Em UI operacional, ele só aparece em destrutivo ou em surfaces brand-adjacent
(login, materiais de marca).

## 3. Typography

**Single Family:** Open Sans (system-ui fallback). Mantida em **toda** a UI —
display, body, label, caption. Inter e Source Serif 4 foram removidos
intencionalmente em DS v4.1.

**Character:** Tom adulto e operacional. Pesos 400, 500, 600. Letter-spacing
negativa só em display (-0.02em) e title (-0.01em). Tracking positiva (0.05em)
reservada para caption uppercase.

### Hierarchy
- **Display** (Open Sans 600, 2rem / 32px, line-height 1.2, letter-spacing
  -0.02em): hero ou onboarding empty state.
- **Headline** (Open Sans 600, 1.75rem / 28px, line-height 1.2): page title
  canonical (`.lia-page-title`).
- **Title** (Open Sans 600, 1.5rem ou 1.25rem, line-height 1.25): section
  heading dentro de página, card title quando precisa de peso.
- **Body** (Open Sans 400, 0.8125rem / 13px, line-height 1.5): texto corrido,
  descrições, conteúdo de card. **65–75ch máximo de line length em texto
  corrido.**
- **Label** (Open Sans 500, 0.875rem / 14px, line-height 1.4): labels de form,
  callouts.
- **Caption** (Open Sans 500, 0.75rem / 12px, line-height 1.3, letter-spacing
  0.05em, UPPERCASE): eyebrow de página, metadata densa.
- **Micro** (Open Sans 400, 0.6875rem / 11px, line-height 1.3): badges,
  timestamps.

### Named Rules

**The One Family Rule.** Open Sans em tudo. Inter foi removido em DS v4.1 e fica
fora — não reintroduzir "só pra números". Source Serif 4 também removida;
nenhuma surface usa serif.

**The Negative Tracking Rule.** Letter-spacing negativa em display + title
apenas. Em body ou label vira ilegível.

## 4. Elevation

**Flat-by-default.** Surfaces são chatas em estado normal — fundo cobre estrutura,
hierarquia tipográfica carrega o resto. Shadow aparece **como resposta a estado**:
modal aberto, popover, card elevated em hover. Nunca shadow decorativa.

### Shadow Vocabulary

- **lia-shadow-sm** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02)`): borda quase
  nula. Tooltips, popovers leves.
- **lia-shadow-default** (`box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05)`): card
  elevated em estado normal (raro).
- **lia-shadow-md** (`box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05)`): card em
  hover, dropdown content.
- **lia-shadow-lg** (`box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05)`): modal,
  sheet, large popover.

No dark mode, opacities sobem (0.3 → 0.6) pra preservar percepção de elevação
contra fundo escuro.

### Named Rules

**The Flat-By-Default Rule.** Em estado de repouso, surface não tem shadow.
Shadow aparece **só** em (1) modal / popover, (2) card explicitamente elevated
em hover, (3) feedback de interatividade. Em pipeline, listing, kanban —
surfaces são planas.

**The Tonal Layer Rule.** Profundidade extra antes de shadow: usar bg gray
scale (paper → chalk → powder) para criar hierarquia de container.

## 5. Components

Cada componente tem caráter contido, monocromático, com o mínimo necessário
para affordance. Refined and restrained — o controle silencia, o conteúdo fala.

### Buttons
- **Shape:** rounded-md (6px). Nunca rounded-full ou square — exceção é
  icon-only com altura = largura.
- **Primary:** background **Ink** (`#030712`) + text **Paper** (`#FFFFFF`).
  Altura 40px (default size), padding 16px horizontal. Font-weight 500,
  text-xs (0.8125rem). **Nunca cyan como primary** (conflito histórico em
  `.lia-btn-primary` CSS legacy — componente canonical Button é preto).
- **Secondary:** background **Powder** + text **Graphite**. Mesma forma do
  primary.
- **Ghost:** background transparent + text **Graphite**, hover bg **Powder**.
  Usado em toolbars e contexto onde "botão" não deve gritar.
- **Destructive:** background **Status Error** + text **Paper**. Reservado para
  delete confirmado.
- **Outline:** border **Mist** + bg transparent + text **Ink**. Quando precisa
  de affordance sem peso.
- **Hover:** transição de opacidade 200ms, nunca shift de cor brand.
- **Focus:** ring 2px **Ink/20** com 2px offset. Visível, restrained.
- **Sizes:** `default` h-10 px-4, `sm` h-9 px-3, `lg` h-11 px-8, `icon` h-10 w-10.

### Inputs
- **Style:** background **Paper** + border **Mist** (1px) + radius **md** (6px)
  + altura 40px + padding 12px horizontal + text-xs.
- **Focus:** border passa pra **Pebble**, ring 2px **Ink/20** (dark: **Mist/20**).
  Não cyan exceto em surfaces de chat/onboarding contextuais.
- **Disabled:** opacity 50%, cursor not-allowed.
- **Placeholder:** **Fog** (light) / **Ash** (dark) — sempre legível contra paper.

### Cards
- **Corner Style:** rounded-xl (12px). **Nunca rounded-md** em card.
- **Background:** **Paper** light / `lia-bg-secondary` dark.
- **Border:** 1px **Mist** (light) / `lia-border-subtle` (dark). Componente
  canonical shadcn permite border; `border: none !important` da legacy
  `.lia-card` CSS class é pattern antigo, não canonical.
- **Internal Padding:** 24px (CardHeader / CardContent). Espaço respira.
- **Shadow:** ausente em estado normal (Flat-By-Default Rule). Hover de cards
  interativos pode adicionar `lia-shadow-md`.

### Badges
- **Shape:** rounded-full (pill). Padding 2px 8px. Font micro (11px) weight 500.
- **Variants semânticos:** `default` (powder bg, graphite text), `secondary`,
  `destructive`, `success` (forest-green/15 bg + text), `warning`
  (amber-warning/15), `info` (lia-cyan/15), `danger` (status-error/15),
  `lilac` (insight-purple/15).
- **Border:** transparent por default — `outline` variant tem border **Mist**.

### Chips (canonical pill consolidado)
- **Densidades:** `comfortable` (default), `compact` (kanban candidate cards,
  10px tight leading), `relaxed` (modais, previews, 12px).
- **Variants:** `neutral`, `success`, `warning`, `danger`, `info`. Aplicação
  via `kanbanChipStyles` em `src/lib/design-tokens.ts` — não duplicar lógica.
- **Muted prop:** atenua saturation, uso em listings densas.

### Navigation (sidebar primário)
- **Style:** items com altura 36-40px, padding horizontal 12-16px, text-xs.
- **States:** default text-**Graphite** hover bg-**Powder**; active bg-**Mist**
  + text-**Ink** + indicador de left edge 1-2px **Ink**. **Nunca side-stripe
  colorida grossa** — pattern banido pela skill.
- **Mobile:** drawer slide-in via right panel ou overlay full-screen.

### Signature Component: ThinkingStepsCard (Live Task Feed)
Card canonical que renderiza o trabalho da LIA quando ela está executando.
Premissa "Mostrar o trabalho da IA" (Design Principle 3 do PRODUCT.md):
- `rounded-xl border bg-lia-bg-secondary` + max-width 85%.
- Step ativo: ícone Loader2 animado **LIA Cyan** + text-lia-text-primary
  font-medium.
- Steps concluídos: ícone CheckCircle2 **Status Success** + text-lia-text-secondary.
- Substitui `<TypingIndicator />` genérico — IA opaca = IA não confiável.

## 6. Do's and Don'ts

### Do:
- **Do** usar **Ink** (`#030712`) como background de button primary; cyan é da
  IA, não dos botões.
- **Do** reservar **LIA Cyan** (`#60BED1`) **só** quando a LIA está agindo ou
  um signal de IA está sendo emitido.
- **Do** preferir tonal layering (paper → chalk → powder) antes de adicionar
  shadow.
- **Do** colocar shadow só em modal, popover, ou card elevated em hover. Em
  estado de repouso, surfaces são chatas.
- **Do** manter Open Sans em **toda** a UI — display, body, label, caption.
- **Do** respeitar `prefers-reduced-motion` em qualquer animação (field
  highlight + field pulse já têm fallback canonical em design-tokens.css).
- **Do** usar rounded-md (6px) em controles, rounded-xl (12px) em cards,
  rounded-full em badges. Não inverter.
- **Do** consolidar pill / chip / badge novos em `Chip` canonical com props
  `density` + `variant`; não criar mais um componente lookalike.

### Don't:
- **Don't** usar cyan como cor primary de botão. (Conflito histórico de
  `.lia-btn-primary` CSS legacy — componente canonical Button é Ink preto.)
- **Don't** combinar simultaneamente cyan + amber + purple + magenta na mesma
  tela. Isso é categoria-reflex ATS infantil e quebra a 90/10 Rule.
- **Don't** usar side-stripe (`border-left > 1px colorida`) em cards, alerts,
  list items ou callouts. **Banido** pela skill em qualquer surface.
- **Don't** usar gradient text (`background-clip: text` com gradient). **Banido**.
- **Don't** usar glassmorphism decorativo. Surfaces são sólidas, não fingem vidro.
- **Don't** abrir modal como primeira escolha. Modais só quando inline e
  progressive disclosure realmente não atendem (Design Principle "Zero páginas
  novas").
- **Don't** reintroduzir Inter "só pra números" ou Source Serif 4 "só pra
  sidebar". Removidos em DS v4.1 — fora.
- **Don't** adicionar nova paleta de acento (azul-roxo SaaS típico, neon,
  gradient acento). 90/10 Rule é canonical.
- **Don't** usar emoji decorativo em UI ou em outputs de LIA. Comemoração
  performática (festa, faísca, aceno) fica fora — anti-reference canonical do
  PRODUCT.md.
- **Don't** copiar visual de Gupy, Kenoby, Vagas.com (tabela infinita sem
  hierarquia, formulário-mãe de 40 campos). Anti-reference canonical do
  PRODUCT.md.
- **Don't** desabilitar `prefers-reduced-motion` em animações novas. WCAG 2.1
  AA é mandatório (PRODUCT.md Accessibility).
- **Don't** usar `border: none !important` por reflexo. Componente shadcn
  canonical Card tem border — pattern legacy `.lia-card` é exceção, não regra.
