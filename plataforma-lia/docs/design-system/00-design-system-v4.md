# WeDo Talent Design System v4.2

> **Versão:** 4.2.2  
> **Atualizado:** Abril 2026  
> **Maturidade:** Em evolução (benchmarked 6.8 → 7.5/10)  
> **Changelog v4.2.2:** Revisão profunda DS ↔ código real (Abril 2026):
> - Tokens escurecidos: text-secondary #2D2D2D, text-tertiary #5C5C5C, borders #D4D4D4/#BEBEBE/#999999
> - Cards: rounded-md → rounded-xl (16px)
> - Tabs: pill style (bg-lia-bg-secondary rounded-lg, active shadow-sm)
> - Modais: dialog.tsx rounded-xl, sem border separators
> - Tipografia: font-bold → font-semibold em headings, Crimson/SourceSerif removidos, títulos padronizados text-lg
> - Badges: 9 variants coloridos (success/warning/info/danger/lilac), overrides limpos
> - 318 badge overrides → variants, 275 gray→tokens, 2.433 rounded-xl, 303 bordas removidas
> - Stats bars coloridas em Vagas, Funil. Ícones coloridos por contexto em Tarefas, Settings
> - Zero: gray classes, hex hardcoded, shadcn defaults, font-crimson, Open_Sans inline
> **Changelog v4.2.1:** Reconciliação DS ↔ código real — tipografia 85/10/5, botões font-medium, border-radius rounded-xl cards, rounded-md inputs, sidebar valores reais, sistema --eleven-* documentado, bug --wedo-cyan/orange corrigido  
> **Referências:** ElevenLabs UI, Shopify Polaris, IBM Carbon, Material Design 3  
> **Filosofia:** Interface monocromática clean (90% grays) + acentos WeDo estratégicos (10%)  
> **Stacks:** React + Tailwind + shadcn/ui (protótipos) | Vue + Vuetify 3 + Nuxt (produção)
>
> **Status Legend:** `[Stable]` Pronto para uso | `[Draft]` Em desenvolvimento | `[Planned]` No roadmap

---

## Sumário

### PARTE 1: FUNDAMENTOS
- [1.1 Princípios de Design](#11-princípios-de-design) `[Stable]`
- [1.2 Paleta de Cores](#12-paleta-de-cores) `[Stable]`
- [1.3 Tipografia](#13-tipografia) `[Stable]`
- [1.4 Espaçamento](#14-espaçamento) `[Stable]`
- [1.5 Grid & Layout](#15-grid--layout) `[Stable]`
- [1.6 Breakpoints](#16-breakpoints) `[Stable]`
- [1.7 Sombras & Elevação](#17-sombras--elevação) `[Stable]`
- [1.8 Bordas & Raios](#18-bordas--raios) `[Stable]`
- [1.9 Motion & Animation](#19-motion--animation) `[Stable]`
- [1.10 Glassmorphism & Effects](#110-glassmorphism--effects) `[Stable]`
- [1.11 Elemento Visual LIA (Brain Icon)](#111-elemento-visual-lia-brain-icon) `[Stable]`

### PARTE 2: CONTEÚDO & VOZ
- [2.1 Voice & Tone da LIA](#21-voice--tone-da-lia) `[Draft]`
- [2.2 Escrita para Interface](#22-escrita-para-interface) `[Draft]`
- [2.3 Glossário de Termos](#23-glossário-de-termos) `[Draft]`
- [2.4 Data Formats](#24-data-formats) `[Draft]`

### PARTE 3: COMPONENTES
- [3.1 Botões](#31-botões) `[Stable]`
- [3.2 Inputs & Forms](#32-inputs--forms) `[Stable]`
- [3.3 Cards](#33-cards) `[Stable]`
- [3.4 Modais](#34-modais) `[Stable]`
- [3.5 Tabelas](#35-tabelas) `[Stable]`
- [3.6 Badges & Tags](#36-badges--tags) `[Stable]`
- [3.7 Tooltips & Popovers](#37-tooltips--popovers) `[Stable]`
- [3.8 Toasts & Alerts](#38-toasts--alerts) `[Stable]`
- [3.9 Navigation](#39-navigation) `[Stable]`
- [3.10 Loading States](#310-loading-states) `[Stable]`
- [3.11 Dropdowns & Menus](#311-dropdowns--menus) `[Stable]`
- [3.12 Accordions](#312-accordions) `[Stable]`
- [3.13 Progress Indicators](#313-progress-indicators) `[Stable]`
- [3.14 Avatars](#314-avatars) `[Stable]`
- [3.15 Breadcrumbs](#315-breadcrumbs) `[Stable]`
- [3.16 Pagination](#316-pagination) `[Stable]`
- [3.17 Switches & Toggles](#317-switches--toggles) `[Stable]`
- [3.18 Radio Buttons](#318-radio-buttons) `[Stable]`
- [3.19 Checkboxes](#319-checkboxes) `[Stable]`
- [3.20 Date Pickers](#320-date-pickers) `[Stable]`
- [3.21 File Upload](#321-file-upload) `[Stable]`
- [3.22 Sliders](#322-sliders) `[Stable]`
- [3.23 Tabs](#323-tabs) `[Stable]`
- [3.24 Dividers](#324-dividers) `[Stable]`
- [3.25 Skeleton Loaders](#325-skeleton-loaders) `[Stable]`
- [3.26 Feedback Buttons (Like/Dislike)](#326-feedback-buttons-likedislike) `[Stable]`
- [3.27 Sort Dropdown (Ordenação)](#327-sort-dropdown-ordenação) `[Stable]`
- [3.28 Load More Button (Carregar Mais)](#328-load-more-button-carregar-mais) `[Stable]`
- [3.29 Qualification Badge (Classificação de Vaga)](#329-qualification-badge-classificação-de-vaga) `[Stable]`
- [3.30 Chat Message (LiaMessage)](#330-chat-message-liamessage) `[Draft]`
- [3.31 Chat Input (LiaChatInput)](#331-chat-input-liachatinput) `[Draft]`
- [3.32 Chat Thinking (LiaThinking)](#332-chat-thinking-liathinking) `[Draft]`
- [3.33 Chat Suggestion Cards](#333-chat-suggestion-cards) `[Draft]`
- [3.34 Pipeline Kanban Card](#334-pipeline-kanban-card) `[Stable]`
- [3.35 Chat Conversation Container (LiaConversation)](#335-chat-conversation-container-liaconversation) `[Draft]`
- [3.36 Chat Response (LiaResponse)](#336-chat-response-liaresponse) `[Draft]`
- [3.37 Chat Welcome (LiaWelcome)](#337-chat-welcome-liawelcome) `[Draft]`
- [3.38 Data Visualization](#338-data-visualization) `[Draft]`
- [3.39 Chip (ex-StatusBadge)](#339-chip-ex-statusbadge) `[Stable]`
- [3.40 CandidateCard](#340-candidatecard) `[Stable]`
- [3.41 PromptSuggestionsDock](#341-promptsuggestionsdock) `[Draft]`
- [3.42 PremiumAutocomplete](#342-premiumautocomplete) `[Draft]`
- [3.43 BulkSelectionBar](#343-bulkselectionbar) `[Stable]`
- [3.44 ContextPill](#344-contextpill) `[Stable]`
- [3.45 CommandPalette](#345-commandpalette) `[Draft]`
- [3.46 QuickActionChips](#346-quickactionchips) `[Stable]`
- [3.47 ScoreIconButton](#347-scoreiconbutton) `[Stable]`
- [3.48 LiaExpandedPanel](#348-liaexpandedpanel) `[Draft]`
- [3.49 PipelineStagesCarousel](#349-pipelinestagescarousel) `[Stable]`
- [3.50 DateRangePicker](#350-daterangepicker) `[Stable]`

### PARTE 4: PADRÕES
- [4.1 Estados de Componentes](#41-estados-de-componentes) `[Stable]`
- [4.2 Formulários](#42-formulários) `[Stable]`
- [4.3 Feedback do Sistema](#43-feedback-do-sistema) `[Stable]`
- [4.4 Empty States](#44-empty-states) `[Stable]`
- [4.5 Error Pages](#45-error-pages) `[Stable]`
- [4.6 Acessibilidade](#46-acessibilidade) `[Stable]`
- [4.7 Page Layouts](#47-page-layouts) `[Draft]`
- [4.8 Navigation Patterns](#48-navigation-patterns) `[Draft]`
- [4.9 Chat Conversation Flows](#49-chat-conversation-flows) `[Draft]`
- [4.10 Onboarding Flow](#410-onboarding-flow) `[Planned]`
- [4.11 Stats Bar Pattern](#411-stats-bar-pattern) `[Stable]`
- [4.12 Mapa de Cores por Contexto](#412-mapa-de-cores-por-contexto) `[Stable]`
- [4.13 Filtros Coloridos por Status](#413-filtros-coloridos-por-status) `[Stable]`
- [4.14 Ícones Coloridos por Seção](#414-ícones-coloridos-por-seção) `[Stable]`

##

---

## 4.11 Stats Bar Pattern `[Stable]` *(Novo v4.2.2)*

Barra horizontal de métricas com ícones coloridos. Padrão usado em Vagas, Funil, Agent Studio.

```jsx
<div className="flex items-center gap-6 mt-1 mb-2">
  <div className="flex items-center gap-2">
    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
    <span className="text-xs text-lia-text-secondary">
      <span className="font-semibold text-lia-text-primary">{count}</span> label
    </span>
  </div>
  <div className="flex items-center gap-1.5">
    <Icon className="w-3.5 h-3.5 text-wedo-cyan" />
    <span className="text-xs text-lia-text-secondary">
      <span className="font-semibold text-lia-text-primary">{count}</span> label
    </span>
  </div>
</div>
```

**Regras:**
- Dot pulse (animate-pulse) apenas para métrica "ao vivo" (ex: vagas ativas)
- Ícones w-3.5 h-3.5 com cor contextual
- Texto text-xs, número font-semibold text-lia-text-primary
- Não repetir informação já visível em tabs/badges

## 4.12 Mapa de Cores por Contexto `[Stable]` *(Novo v4.2.2)*

Cores usadas pontualmente para dar vida sem poluir (clean > colorido):

| Cor | Token/Class | Contexto | Onde usar |
|-----|-------------|----------|-----------|
| **Cyan** | `text-wedo-cyan` / `bg-wedo-cyan/15` | LIA, AI, busca, links | Ícones Brain/Bot, input focus glow, badges info |
| **Emerald** | `text-emerald-500` / `bg-emerald-50` | Ativo, sucesso, aprovado | Dots pulse, badges success, ícones check |
| **Amber** | `text-amber-500` / `bg-amber-50` | Pendente, atenção, warning | Ícones Clock, badges warning, filtros |
| **Rose** | `text-rose-500` / `bg-rose-50` | Urgente, erro, rejeitado | Ícones AlertTriangle, badges danger |
| **Violet** | `text-violet-500` / `bg-violet-50` | Insights, premium, análise | Ícones Brain, badges lilac |

**Regra 90/10:** Cores aparecem em no máximo 10% dos elementos visuais de uma tela.

## 4.13 Filtros Coloridos por Status `[Stable]` *(Novo v4.2.2)*

Botões de filtro mudam de cor quando ativos, seguindo o contexto do status:

```typescript
const STATUS_COLORS = {
  "Novo": { active: "bg-cyan-50 text-cyan-700 border-cyan-200", inactive: "..." },
  "Em triagem": { active: "bg-amber-50 text-amber-700 border-amber-200", inactive: "..." },
  "Aprovado": { active: "bg-emerald-50 text-emerald-700 border-emerald-200", inactive: "..." },
  "Reprovado": { active: "bg-rose-50 text-rose-700 border-rose-200", inactive: "..." },
}
```

## 4.14 Ícones Coloridos por Seção `[Stable]` *(Novo v4.2.2)*

Ícones de navegação/seção com cor fixa por área:

```typescript
const SECTION_ICON_COLORS = {
  'company-team': 'text-wedo-cyan',
  'recruitment': 'text-emerald-500',
  'communication': 'text-violet-500',
  'goals-planning': 'text-amber-500',
  'global-search': 'text-wedo-cyan',
  'integrations': 'text-emerald-500',
  'fairness-compliance': 'text-rose-500',
}
```


# PARTE 5: IMPLEMENTAÇÃO
- [5.1 Design Tokens CSS](#51-design-tokens-css) `[Stable]`
- [5.2 Design Tokens TypeScript](#52-design-tokens-typescript) `[Stable]`
- [5.3 Classes Utilitárias](#53-classes-utilitárias) `[Stable]`
- [5.4 tailwind.config.js de Referência](#54-tailwindconfigjs-de-referência) `[Stable]`
- [5.5 Integração shadcn/ui](#55-integração-shadcnui) `[Stable]`
- [5.6 Integração Vuetify](#56-integração-vuetify) `[Stable]`
- [5.7 Integração Vuetify Avançada](#57-integração-vuetify-avançada) `[Stable]`
- [5.8 Mapeamento Tailwind ↔ Vuetify](#58-mapeamento-tailwind--vuetify) `[Stable]`
- [5.9 Tabela de Migração v4.0 → v4.1](#59-tabela-de-migração-v40--v41) `[Stable]`

### PARTE 6: CATÁLOGOS
- [6.1 Catálogo Completo de Ícones](#61-catálogo-completo-de-ícones) `[Stable]`
- [6.2 Catálogo de Cores por Contexto](#62-catálogo-de-cores-por-contexto) `[Stable]`
- [6.3 Catálogo de Modais (58+)](#63-catálogo-de-modais-58) `[Stable]`

---

# PARTE 1: FUNDAMENTOS

## 1.1 Princípios de Design `[Stable]`

O Design System WeDo Talent é guiado por 5 princípios fundamentais que orientam todas as decisões de design e implementação. Inspirado na interface clean da ElevenLabs e na profundidade de sistemas como Polaris e Carbon.

### Princípio 1: Conversa como Interface (Conversation-First)

> A LIA é a interface. O chat é o ponto de contato primário — painéis, tabelas e formulários são suporte visual para a conversa.

O recrutador interage com a plataforma através de linguagem natural. Botões e formulários existem como atalhos, nunca como caminho principal. Toda transição de etapa é confirmada via texto no chat.

**Na prática:**
- Chat sempre visível e acessível como elemento central do layout
- Painéis laterais complementam a conversa, não a substituem
- A LIA pergunta, o recrutador responde — fluxo conversacional
- Ações executadas pela LIA com confirmação textual antes de destrutivas

### Princípio 2: Clareza Monocromática (90/10 Rule)

> 90% da interface usa escala de cinzas. Cor aparece em apenas 10% — e sempre com propósito semântico.

Cores nunca são decorativas. Cada cor WeDo carrega significado: cyan = LIA/automação, green = candidato/sucesso, orange = prazo/atenção, purple = insight/IA. O resultado é uma interface que respira, onde a informação importante se destaca naturalmente.

**Na prática:**
- Backgrounds: white, gray-50, gray-100 (hierarquia de profundidade)
- Textos: gray-800, gray-900 (alta legibilidade)
- Botão primário: sempre preto (gray-900), nunca colorido
- Cor apenas em: badges semânticos, ícones contextuais, status indicators
- Bordas quase invisíveis (gray-200), sombras sutis

### Princípio 3: Dados com Confiança (Data Integrity)

> Cada número, score e métrica exibida deve ser rastreável, explicável e visualmente distinto do texto narrativo.

A plataforma lida com decisões de contratação — dados precisam inspirar confiança. Métricas usam fonte Inter (tabular-nums) para alinhamento preciso. Scores WSI sempre acompanham indicador de confiança. Nenhum dado é apresentado sem contexto.

**Na prática:**
- Fonte Inter para todos os dados numéricos (KPIs, scores, métricas)
- Fonte Open Sans para texto narrativo (85% da interface)
- Scores sempre com indicador de confiança (alta/média/baixa)
- Tooltips explicativos em métricas complexas
- Tabelas com header Inter uppercase para dados tabulares

### Princípio 4: Acessibilidade Inclusiva (WCAG AA+)

> Todo elemento interativo deve ser acessível por teclado, legível em contraste mínimo AA, e compreensível sem depender apenas de cor.

Acessibilidade não é opcional — é requisito de compliance (LGPD, EU AI Act). Contraste mínimo WCAG AA (4.5:1 para texto normal, 3:1 para texto grande). Status sempre combina cor + ícone + texto. Touch targets mínimos de 44x44px em mobile.

**Na prática:**
- Focus ring padronizado: `ring-2 ring-gray-900/20` (3px, visível em light e dark)
- Touch targets: mínimo 44x44px (mobile), 32x32px (desktop)
- Badges de status: sempre cor + ícone + label textual
- ARIA labels obrigatórios em botões icon-only
- Suporte a `prefers-reduced-motion` e `prefers-color-scheme`

### Princípio 5: Dualidade de Stack (Write Once, Map Twice)

> Todo componente é especificado uma vez e mapeado para duas stacks: React+Tailwind (prototipagem) e Vue+Vuetify (produção).

O design system serve como ponte entre prototipagem rápida (Replit) e produção robusta (Nuxt). Cada componente documenta implementação em ambas as stacks com mapeamento de tokens equivalentes.

**Na prática:**
- Cada componente tem bloco React+Tailwind e bloco Vue+Vuetify
- Design tokens em CSS custom properties (stack-agnostic)
- Composable `useDesignTokens()` para Vue, `textStyles` object para React
- Mapeamento Tailwind ↔ Vuetify em tabela de referência (seção 5.6)
- Convenções de naming preparadas para migração (kebab-case, slots pattern)

---

### Regra 90/10 — Referência Rápida

| Área | Proporção | Exemplos |
|------|-----------|----------|
| **90% Monocromático** | Estrutura, texto, ações | Backgrounds (white, gray-50, gray-100), texto (gray-800, gray-900), bordas (gray-200, gray-300), botões primários (gray-900), cards, containers, inputs |
| **10% Cor Semântica** | Destaque com significado | Brain LIA (cyan #60BED1), badges contextuais, status indicators (green/amber/red), ícones de domínio específico |

**REGRA:** Cor nunca em botões primários ou ações principais. Cor = informação, não decoração.

---

## 1.2 Paleta de Cores

### 1.2.1 Sistema Monocromático (90% da interface)

#### Backgrounds

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-bg-primary` | `#FFFFFF` | `bg-white` | `bg-white` | Fundo principal da página |
| `--lia-bg-secondary` | `#F9FAFB` | `bg-gray-50` | `bg-grey-lighten-5` | Cards, painéis (sidebar usa bg-white) |
| `--lia-bg-tertiary` | `#F3F4F6` | `bg-gray-100` | `bg-grey-lighten-4` | Hover states, disabled |
| `--lia-bg-elevated` | `#FFFFFF` | `bg-white` | `bg-white elevation-1` | Cards elevados (com shadow) |

#### Textos

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-text-primary` | `#111827` | `text-gray-900` | `text-grey-darken-4` | Títulos, headings |
| `--lia-text-body` | `#1F2937` | `text-gray-800` | `text-grey-darken-3` | Texto principal, labels |
| `--lia-text-secondary` | `#2D2D2D` | `text-gray-600` | `text-grey-darken-1` | Descrições, captions |
| `--lia-text-muted` | `#5C5C5C` | `text-gray-500` | `text-grey` | Placeholders, hints |
| `--lia-text-disabled` | `#999999` | `text-gray-400` | `text-grey-lighten-1` | Texto desabilitado |

#### Bordas

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-border-subtle` | `#D4D4D4` | `border-gray-200` | `border-grey-lighten-3` | Bordas padrão (quase invisíveis) |
| `--lia-border-default` | `#BEBEBE` | `border-gray-300` | `border-grey-lighten-2` | Bordas com destaque |
| `--lia-border-medium` | `#999999` | `border-gray-400` | `border-grey-lighten-1` | Bordas fortes |

#### Botão Primary (Preto) - AÇÃO PRINCIPAL

| Estado | Background | Text | Border |
|--------|------------|------|--------|
| **Default** | `bg-gray-900` (#111827) | `text-white` | none |
| **Hover** | `bg-gray-800` (#1F2937) | `text-white` | none |
| **Active** | `bg-gray-700` (#374151) | `text-white` | none |
| **Focus** | `bg-gray-900` + ring | `text-white` | `ring-2 ring-gray-900/20` |
| **Disabled** | `bg-gray-300` (#BEBEBE) | `text-gray-500` | none |

**IMPORTANTE:** Botão primário é SEMPRE preto. Cores WeDo são APENAS para badges, ícones e indicadores.

### 1.2.2 Cores de Acento WeDo (10% estratégico)

**REGRA DE OURO**: Usar APENAS para badges semânticos, ícones contextuais e status. NUNCA para botões primários.

#### Cores Primárias (10 tokens no `tailwind.config.ts`)

| Cor | Hex | Token Tailwind | Token CSS | Uso Semântico |
|-----|-----|----------------|-----------|---------------|
| **Cyan** | `#60BED1` | `wedo-cyan` | `--wedo-cyan` | **Brain LIA**, Vagas, Automação |
| **Cyan Dark** | `#4DA8BB` | `wedo-cyan-dark` | `--wedo-cyan-dark` | Hover states, ícones ativos |
| **Green** | `#5DA47A` | `wedo-green` | `--wedo-green` | Candidatos, Sucesso, Aprovação |
| **Green Light** | `#7BC29A` | `wedo-green-light` | `--wedo-green-light` | Variante clara do green, badges |
| **Green Pastel** | `#A8D5B7` | `wedo-green-pastel` | `--wedo-green-pastel` | Backgrounds pastel, progress bars |
| **Green Bright** | `#60D186` | `wedo-green-bright` | `--wedo-green-bright` | Status ativo, indicadores positivos |
| **Orange** | `#D19960` | `wedo-orange` | `--wedo-orange` | Tempo, Prazos, Alertas médios |
| **Purple** | `#9860D1` | `wedo-purple` | `--wedo-purple` | Insights, IA, Análises |
| **Magenta** | `#D160AB` | `wedo-magenta` | `--wedo-magenta` | Urgência crítica, Prioridade alta |
| **Coral** | `#E16162` | `wedo-coral` | `--wedo-coral` | Rejeição, erro, destaque vermelho |

> **NOTA v4.2.1:** `amber` (`#F59E0B`) usa a classe nativa Tailwind `amber-500` — não é um token custom no `tailwind.config.ts`. Para warnings, use `text-amber-500` / `bg-amber-50` diretamente.

#### Variações Dark (para hover e estados ativos)

| Cor Base | Dark Variant | Uso |
|----------|--------------|-----|
| Cyan `#60BED1` | `#4DA8BB` (`wedo-cyan-dark`) | Hover em badges/ícones cyan |
| Green `#5DA47A` | `#4B8862` | Hover em badges/ícones green |
| Orange `#D19960` | `#B8814D` | Hover em badges/ícones orange |
| Purple `#9860D1` | `#7F4DB8` | Hover em badges/ícones purple |
| Magenta `#D160AB` | `#B84D92` | Hover em badges/ícones magenta |
| Coral `#E16162` | `#C54C4D` | Hover em badges/ícones coral |

#### Variações Light (para backgrounds sutis - 10% opacidade)

| Cor | Background Tailwind | Valor | Uso |
|-----|---------------------|-------|-----|
| **Cyan Light** | `bg-wedo-cyan/10` | `rgba(96,190,209,0.1)` | Background badges LIA |
| **Green Light** | `bg-wedo-green/10` | `rgba(93,164,122,0.1)` | Background badges candidatos |
| **Orange Light** | `bg-wedo-orange/10` | `rgba(209,153,96,0.1)` | Background badges tempo |
| **Purple Light** | `bg-wedo-purple/10` | `rgba(152,96,209,0.1)` | Background badges insights |
| **Magenta Light** | `bg-wedo-magenta/10` | `rgba(209,96,171,0.1)` | Background badges urgência |
| **Coral Light** | `bg-wedo-coral/10` | `rgba(225,97,98,0.1)` | Background badges rejeição |

### 1.2.3 Cores de Status (Sistema Semântico)

| Status | Background | Text | Border | Ícone | Quando Usar |
|--------|------------|------|--------|-------|-------------|
| **Sucesso** | `bg-green-50` | `text-green-700` | `border-green-200` | CheckCircle | Confirmações, aprovações |
| **Alerta** | `bg-amber-50` | `text-amber-700` | `border-amber-200` | AlertTriangle | Avisos, atenção necessária |
| **Erro** | `bg-red-50` | `text-red-700` | `border-red-200` | XCircle | Erros, falhas, rejeições |
| **Info** | `bg-blue-50` | `text-blue-700` | `border-blue-200` | Info | Informações neutras |
| **Neutro** | `bg-gray-100` | `text-gray-700` | `border-gray-200` | Circle | Estados padrão |

**Contraste WCAG AA:**
- ✅ green-700 em green-50: 7.2:1 (AAA)
- ✅ amber-700 em amber-50: 6.8:1 (AAA)
- ✅ red-700 em red-50: 7.1:1 (AAA)
- ✅ blue-700 em blue-50: 7.3:1 (AAA)

### 1.2.4 Dark Mode

#### Tokens de Cores

| Token | Valor Light | Valor Dark |
|-------|-------------|------------|
| `--lia-bg-primary` | `#FFFFFF` | `#0F1113` |
| `--lia-bg-secondary` | `#F9FAFB` | `#1A1D1F` |
| `--lia-bg-tertiary` | `#F3F4F6` | `#26292B` |
| `--lia-bg-elevated` | `#FFFFFF` | `#1A1D1F` |
| `--lia-text-primary` | `#111827` | `#F9FAFB` |
| `--lia-text-body` | `#1F2937` | `#D4D4D4` |
| `--lia-text-secondary` | `#2D2D2D` | `#999999` |
| `--lia-text-muted` | `#5C5C5C` | `#5C5C5C` |
| `--lia-text-disabled` | `#999999` | `#4B5563` |
| `--lia-border-subtle` | `#D4D4D4` | `#374151` |
| `--lia-border-default` | `#BEBEBE` | `#4B5563` |
| `--lia-border-medium` | `#999999` | `#5C5C5C` |

#### Cores WeDo em Dark Mode

As cores WeDo **mantêm-se iguais** em dark mode para preservar a identidade da marca:

| Cor | Light Mode | Dark Mode | Nota |
|-----|------------|-----------|------|
| **Cyan** | `#60BED1` | `#60BED1` | Mantém (Brain icon) |
| **Green** | `#5DA47A` | `#5DA47A` | Mantém |
| **Orange** | `#D19960` | `#D19960` | Mantém |
| **Purple** | `#9860D1` | `#9860D1` | Mantém |
| **Magenta** | `#D160AB` | `#D160AB` | Mantém |

#### Backgrounds de Badges em Dark Mode

| Cor | Light Mode | Dark Mode |
|-----|------------|-----------|
| Cyan Light | `rgba(96,190,209,0.1)` | `rgba(96,190,209,0.15)` |
| Green Light | `rgba(93,164,122,0.1)` | `rgba(93,164,122,0.15)` |
| Orange Light | `rgba(209,153,96,0.1)` | `rgba(209,153,96,0.15)` |
| Purple Light | `rgba(152,96,209,0.1)` | `rgba(152,96,209,0.15)` |
| Magenta Light | `rgba(209,96,171,0.1)` | `rgba(209,96,171,0.15)` |

**Nota**: Aumentar opacidade para 15% em dark mode para manter visibilidade.

#### Cores de Status em Dark Mode

| Status | Light Bg | Dark Bg | Light Text | Dark Text |
|--------|----------|---------|------------|-----------|
| **Sucesso** | `bg-green-50` | `bg-green-900/20` | `text-green-700` | `text-green-400` |
| **Alerta** | `bg-amber-50` | `bg-amber-900/20` | `text-amber-700` | `text-amber-400` |
| **Erro** | `bg-red-50` | `bg-red-900/20` | `text-red-700` | `text-red-400` |
| **Info** | `bg-blue-50` | `bg-blue-900/20` | `text-blue-700` | `text-blue-400` |
| **Neutro** | `bg-gray-100` | `bg-gray-800` | `text-gray-700` | `text-gray-300` |

#### Componentes em Dark Mode

| Componente | Light | Dark |
|------------|-------|------|
| **Card** | `bg-white border-gray-200` | `bg-[#1A1D1F] border-gray-700` |
| **Card Elevated** | `bg-white shadow-md` | `bg-[#26292B] border-gray-700` |
| **Button Primary** | `bg-gray-900 text-white` | `bg-white text-gray-900` |
| **Button Secondary** | `bg-gray-100 text-gray-700` | `bg-gray-800 text-gray-200` |
| **Button Outline** | `border-gray-300 text-gray-700` | `border-gray-600 text-gray-200` |
| **Input** | `bg-white border-gray-300` | `bg-[#1A1D1F] border-gray-600` |
| **Modal** | `bg-white` | `bg-[#1A1D1F]` |
| **Modal Overlay** | `bg-black/40` | `bg-black/60` |
| **Dropdown** | `bg-white shadow-lg` | `bg-[#26292B] border-gray-700` |
| **Tooltip** | `bg-gray-900 text-white` | `bg-gray-100 text-gray-900` |
| **Sidebar** | `bg-white border-gray-100` | `bg-[#0F1113] border-gray-800` |
| **Table Header** | `bg-gray-50` | `bg-[#1A1D1F]` |
| **Table Row Hover** | `bg-gray-50` | `bg-[#26292B]` |

#### Sombras em Dark Mode

| Token | Light | Dark |
|-------|-------|------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | `0 4px 6px rgba(0,0,0,0.4)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | `0 10px 15px rgba(0,0,0,0.5)` |

**Nota**: Aumentar opacidade das sombras em dark mode para compensar fundo escuro.

> **⚠️ Dark Mode Coverage Checklist:**
> 
> | Componente | Dark Mode | Status |
> |------------|-----------|--------|
> | Core UI (Cards, Buttons, Inputs, Modals) | ✅ Mapeado | `[Stable]` |
> | Table, Sidebar, Dropdown, Tooltip | ✅ Mapeado | `[Stable]` |
> | Status Badges & Alerts | ✅ Mapeado | `[Stable]` |
> | Chat Components (LiaMessage, LiaChatInput) | ⚠️ Parcial | `[Draft]` |
> | LiaThinking, LiaSuggestionCards | ⚠️ Parcial | `[Draft]` |
> | Data Visualization (Charts, Graphs) | ❌ Pendente | `[Planned]` |
> | Pipeline/Kanban Cards | ⚠️ Parcial | `[Draft]` |
> | Command Palette | ❌ Pendente | `[Planned]` |
> | Code/Snippet Blocks | ❌ Pendente | `[Planned]` |
> 
> **Regra de implementação dark mode:**  
> Usar tokens CSS custom (`var(--lia-bg-primary)`) em vez de classes hardcoded (`bg-white`/`bg-[#0F1113]`). Isso permite que o toggle de tema funcione com uma única troca de variáveis no `:root` / `[data-theme="dark"]`.

#### Implementação CSS

```css
/* Light mode (padrão) */
:root {
  --lia-bg-primary: #FFFFFF;
  --lia-bg-secondary: #F9FAFB;
  --lia-bg-tertiary: #F3F4F6;
  --lia-text-primary: #111827;
  --lia-text-body: #1F2937;
  --lia-text-secondary: #4B5563;
  --lia-border-subtle: #D4D4D4;
  --lia-border-default: #BEBEBE;
  --lia-shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --lia-shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --lia-shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}

/* Dark mode */
.dark,
[data-theme="dark"] {
  --lia-bg-primary: #0F1113;
  --lia-bg-secondary: #1A1D1F;
  --lia-bg-tertiary: #26292B;
  --lia-text-primary: #F9FAFB;
  --lia-text-body: #D4D4D4;
  --lia-text-secondary: #999999;
  --lia-border-subtle: #374151;
  --lia-border-default: #4B5563;
  --lia-shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --lia-shadow-md: 0 4px 6px rgba(0,0,0,0.4);
  --lia-shadow-lg: 0 10px 15px rgba(0,0,0,0.5);
}

/* Respeitar preferência do sistema */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --lia-bg-primary: #0F1113;
    --lia-bg-secondary: #1A1D1F;
    /* ... demais variáveis dark */
  }
}
```

### 1.2.5 Escala Completa de Cinzas (Tailwind)

| Classe | Hex | Uso Recomendado |
|--------|-----|-----------------|
| `gray-50` | `#F9FAFB` | Backgrounds secundários |
| `gray-100` | `#F3F4F6` | Backgrounds terciários, hover |
| `gray-200` | `#D4D4D4` | Bordas sutis (escurecido v4.2.2) |
| `gray-300` | `#BEBEBE` | Bordas padrão (escurecido v4.2.2) |
| `gray-400` | `#999999` | Texto disabled, bordas fortes (escurecido v4.2.2) |
| `gray-500` | `#5C5C5C` | Texto muted, placeholders (escurecido v4.2.2) |
| `gray-600` | `#4B5563` | Texto secundário |
| `gray-700` | `#374151` | Texto com destaque |
| `gray-800` | `#1F2937` | Texto corpo principal |
| `gray-900` | `#111827` | Títulos, botões primários |
| `gray-950` | `#030712` | Texto de máximo contraste ✅ |

**Nota**: `gray-950` é válido no Tailwind v3+ e deve ser usado quando necessário máximo contraste.

### 1.2.6 Dual Token System: `--lia-*` vs `--eleven-*` `[Stable]`

> **NOTA v4.2.1:** A plataforma opera com 3 sistemas paralelos de CSS variables. Esta seção documenta os dois sistemas principais e quando usar cada um.

#### Os dois sistemas e seus propósitos

| Sistema | Prefixo | Definido em | Propósito |
|---------|---------|-------------|-----------|
| **LIA Core** | `--lia-*` | `design-tokens.css` | UI funcional padrão — layout, textos, bordas, backgrounds base. Usa escala Tailwind gray. |
| **ElevenLabs** | `--eleven-*` | `globals.css` | Superfícies com personalidade — chat, Kanban cards, badges pastel, painéis expandidos. Usa cinzas puros (não-Tailwind). |
| **shadcn/ui** | `--background`, `--foreground`, etc. | `globals.css` | Sistema HSL interno para componentes shadcn/ui (não usar diretamente). |

#### Quando usar cada sistema

| Contexto | Sistema | Motivo |
|----------|---------|--------|
| Layout (sidebar, header, topbar) | `--lia-*` + Tailwind classes | Funcional, previsível, compatível com shadcn/ui |
| Formulários, tabelas, modais | `--lia-*` + Tailwind classes | Compatível com Tailwind utilities |
| **Chat e mensagens** | `--eleven-*` | Personalidade, identidade ElevenLabs |
| **Kanban cards e badges** | `--eleven-*` (sepia/pastel) | Visual diferenciado |
| **Painéis expandidos da LIA** | `--eleven-*` | Superfície premium |
| Componentes novos genéricos | `--lia-*` + Tailwind classes | Padrão |

> **Diretriz:** Se o componente faz parte do **chat, Kanban ou painéis de IA**, use `--eleven-*`. Para **todo o resto**, use classes Tailwind (`text-gray-900`, `bg-white`) ou tokens `--lia-*`.

#### Diferenças visuais entre os sistemas

| Aspecto | `--lia-*` | `--eleven-*` |
|---------|-----------|--------------|
| Texto principal | `--lia-text-primary` → `#111827` (gray-900) | `--eleven-text-primary` → `#2D2D2D` (cinza puro) |
| Texto secundário | `--lia-text-secondary` → `#4B5563` (gray-600) | `--eleven-text-secondary` → `#666666` (cinza puro) |
| Texto terciário | `--lia-text-tertiary` → `#5C5C5C` (escurecido v4.2.2) | `--eleven-text-tertiary` → `#999999` (cinza puro) |
| Background base | `--lia-bg-primary` → `#FFFFFF` / `#F9FAFB` | `--eleven-bg-main` → `#F8F8F8` / `#F5F5F5` |
| Bordas | `--lia-border-subtle` → `#D4D4D4` (escurecido v4.2.2) | `--eleven-border-subtle` → `#E8E8E8` (cinza puro) |
| Escala de cinzas | Tailwind gray (50–950) | Cinzas puros (#2D2D2D, #666, #999, #E8E8E8, #F5F5F5, #F8F8F8) |
| Personalidade | Neutro, funcional | Quente, tons sepia/pastel, identidade própria |

> **Por que dois sistemas?** O `--lia-*` mantém compatibilidade com Tailwind utilities e facilita migração Vue+Vuetify. O `--eleven-*` dá identidade visual ao chat e componentes interativos sem quebrar a escala Tailwind dos componentes genéricos. Unificar tudo em `--eleven-*` quebraria a compatibilidade com `text-gray-*` classes usadas em ~180 arquivos.

#### Volume de uso no código

| Sistema | Usos aproximados | Arquivos |
|---------|------------------|----------|
| `--eleven-text-*` | ~1.728 | Chat, Kanban, cards, painéis |
| `--eleven-bg-*` / `--eleven-border-*` | ~360 | Chat modal, message bubbles |
| `--eleven-sepia-*` / `--eleven-pastel-*` | ~100 | Badges, Kanban cards |
| `--lia-*` (total) | ~473 | Sidebar, headers, tabelas, formulários |
| Tailwind gray classes | ~7.600+ | Toda a plataforma |

#### Backgrounds ElevenLabs

| Token | Hex | Uso |
|-------|-----|-----|
| `--eleven-bg-main` | `#F8F8F8` | Background principal de painéis ElevenLabs |
| `--eleven-bg-card` | `#FFFFFF` | Cards ElevenLabs |
| `--eleven-bg-message` | `#F5F5F5` | Background de mensagens no chat |

#### Textos ElevenLabs

| Token | Hex | Uso |
|-------|-----|-----|
| `--eleven-text-primary` | `#2D2D2D` | Texto principal (mais escuro que gray-800) |
| `--eleven-text-secondary` | `#666666` | Texto secundário |
| `--eleven-text-tertiary` | `#999999` | Texto terciário/muted |

#### Bordas ElevenLabs

| Token | Hex | Uso |
|-------|-----|-----|
| `--eleven-border-subtle` | `#E8E8E8` | Borda sutil entre elementos |
| `--eleven-border-light` | `#F0F0F0` | Borda muito leve |

#### Paleta Sepia (Backgrounds de badges e Kanban cards)

| Token | Hex | Visual | Uso |
|-------|-----|--------|-----|
| `--eleven-sepia-light` | `#F3EBE1` | Bege sépia claro | Background de cards/badges |
| `--eleven-sepia-mint` | `#DCE4DB` | Verde menta claro | Cards de status positivo |
| `--eleven-sepia-rose` | `#E3DADC` | Rosa antigo/bege rosado | Cards de status intermediário |
| `--eleven-sepia-blue` | `#DDE1E9` | Azul acinzentado claro | Cards informativos |
| `--eleven-sepia-lilac` | `#E5E0E2` | Lilás acinzentado | Cards de insights |
| `--eleven-sepia-ice` | `#EAEAEA` | Cinza muito claro/gelo | Cards neutros |
| `--eleven-sepia-coral` | `#E17B75` | Coral/vermelho pastel | Destaque de urgência |

#### Paleta Pastel (Badges e indicadores)

| Token | Hex | Uso |
|-------|-----|-----|
| `--eleven-pastel-blue` | `#B8D4E8` | Badge informativo |
| `--eleven-pastel-green` | `#C1E1C1` | Badge sucesso |
| `--eleven-pastel-peach` | `#F0DDD3` | Badge atenção |
| `--eleven-pastel-lavender` | `#D4CEE3` | Badge insight |
| `--eleven-pastel-rose` | `#E9D5D5` | Badge urgência |
| `--eleven-pastel-mint` | `#D4E8E1` | Badge positivo |
| `--eleven-pastel-sand` | `#E8DDD4` | Badge neutro |

#### Cards Escuros (Dark cards ElevenLabs)

| Token | Hex | Uso |
|-------|-----|-----|
| `--eleven-card-sepia-dark` | `#3D3330` | Marrom escuro |
| `--eleven-card-forest` | `#2C4A3A` | Verde floresta |
| `--eleven-card-navy` | `#2A3744` | Azul marinho |
| `--eleven-card-brown` | `#443C35` | Marrom |
| `--eleven-card-slate` | `#3A3F47` | Cinza ardósia |

### 1.2.7 Cor de Marca (`--lia-brand-primary`) `[Stable]`

| Token | Hex | RGB | Uso |
|-------|-----|-----|-----|
| `--lia-brand-primary` | `#C74446` | 199,68,70 | Cor coral/vermelha da marca WeDo — usada em elementos de identidade visual, logotipo alternativo, CTAs de marca |

> **NOTA:** Esta cor NÃO é usada para botões ou UI funcional. É reservada para elementos de branding e identidade visual.

### 1.2.8 Cores Deprecadas (Eliminar na Padronização)

| Cor Atual | Substituir Por | Classe Tailwind | Motivo |
|-----------|---------------|-----------------|--------|
| `#FAFAFA` | `#F9FAFB` | `gray-50` | Inconsistente, usar padrão Tailwind |
| `#E4EBEF` | `#D4D4D4` | `gray-200` | Azulado inconsistente |

> **NOTA v4.2.1:** As cores `#E8E8E8`, `#666666`, `#999999`, `#2D2D2D` e `#F5F5F5` **NÃO são deprecadas** — são valores legítimos do sistema `--eleven-*` (seção 1.2.6). Só devem ser substituídas por Tailwind grays quando usadas **fora** de contextos ElevenLabs (chat, Kanban, painéis).

---

## 1.3 Tipografia

### 1.3.1 Sistema de 3 Fontes

| Fonte | Uso | Proporção | Contexto |
|-------|-----|-----------|----------|
| **Open Sans** | Fonte principal: títulos, labels, botões, textos, navigation, sidebar | **85%** | Toda a UI e navegação |
| **Inter** | Dados numéricos, métricas, KPIs, tabelas, dashboards | **10%** | Dashboards, relatórios, dados |
| **JetBrains Mono** | Queries booleanas, dados técnicos, code snippets, IDs | **5%** | Código, filtros técnicos |

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-primary: "Open Sans", sans-serif;      /* 85% - UI geral + navigation */
  --font-data: "Inter", sans-serif;             /* 10% - números/métricas/dados */
  --font-mono: "JetBrains Mono", monospace;     /* 5% - código/queries/técnico */
}
```

> **NOTA v4.2.1:** Sistema expandido de 2 para 3 fontes. Open Sans domina 85% da interface (UI, navegação, chat, formulários). Inter é reservado para dados numéricos/KPIs (10%). JetBrains Mono adicionado para queries booleanas e dados técnicos (5%). Source Serif 4 e Crimson Text foram removidos. Apenas Open Sans (85%) + Inter para números (10%) + JetBrains Mono (5%).

### 1.3.2 Hierarquia Tipográfica Completa

#### Open Sans (85% - Interface Principal + Navigation)

| Elemento | Tamanho | Peso | Cor | Line Height | Uso |
|----------|---------|------|-----|-------------|-----|
| **H1** | 24px | 600 | gray-900 | 1.2 | Título de página |
| **H2** | 18px | 600 | gray-900 | 1.25 | Título de seção |
| **H3** | 14px | 600 | gray-900 | 1.3 | Título de card |
| **H4** | 13px | 500 | gray-800 | 1.35 | Subtítulo |
| **Body** | 11px | 400 | gray-800 | 1.5 | Texto principal (base) — `text-xs` redefinido para 11px |
| **Body MD** | 13px | 400 | gray-800 | 1.5 | Texto com destaque |
| **Body SM** | 11px | 400 | gray-700 | 1.5 | Texto secundário |
| **Label** | 11px | 500 | gray-800 | 1.4 | Labels de form |
| **Caption** | 10px | 400 | gray-600 | 1.3 | Captions, metadados |
| **Button** | 11px | 500 | - | 1.2 | Texto de botões (font-medium) |

#### Inter (10% - Dados e Métricas)

| Elemento | Tamanho | Peso | Cor | Uso |
|----------|---------|------|-----|-----|
| **KPI Large** | 32px | 700 | gray-900 | Números grandes de dashboard |
| **KPI Medium** | 24px | 700 | gray-900 | Valores de cards |
| **KPI Small** | 18px | 600 | gray-900 | Valores inline |
| **Metric** | 14px | 500 | gray-800 | Dados de tabela |
| **Metric SM** | 11px | 500 | gray-700 | Dados secundários |
| **Percentage** | 14px | 600 | contextual | Variações (+ verde, - vermelho) |

**IMPORTANTE:** Usar `font-feature-settings: 'tnum' 1` para números tabulares em tabelas.

> **⚠️ Referência de Font-Weight (v4.2.1):**  
> O sistema usa 4 pesos: `400` (regular), `500` (medium), `600` (semibold), `700` (bold).  
> - `font-weight: 500` (medium) = **dominante (60%)** — botões, labels, subtítulos, sidebar items, métricas, texto interativo  
> - `font-weight: 600` (semibold) = headings (H1-H3), labels importantes (27%)  
> - `font-weight: 400` (regular) = body text, descrições, captions (12%)  
> - `font-weight: 700` (bold) = KPIs grandes, números de destaque — apenas Inter (1%)  
> - NUNCA usar `font-weight: 300` (light) ou `font-weight: 800/900` (black)  
> - Tailwind: `font-medium` (500), `font-semibold` (600), `font-normal` (400), `font-semibold` (600) — font-bold NÃO USAR em headings
>
> **⚠️ Body Base = 11px (v4.2.1):**  
> O `text-xs` foi redefinido no `tailwind.config.ts` para `0.6875rem` (11px) com `lineHeight: 1.4`.  
> Isso unifica o body base da plataforma — antes havia mistura de 11px (hardcoded) e 12px (Tailwind padrão).  
> A escala de font-size real da plataforma: 9px, 10px, **11px (base)**, 13px, 14px, 18px, 24px, 32px.

#### Open Sans - Navigation & Sidebar

| Elemento | Tamanho | Peso | Cor | Uso |
|----------|---------|------|-----|-----|
| **Sidebar Item** | 13px | 500 | gray-600 | Item de menu inativo |
| **Sidebar Active** | 13px | 600 | gray-900 | Item de menu ativo |
| **Sidebar Section** | 11px | 600 | gray-500 | Título de grupo/seção |

#### JetBrains Mono (5% - Código e Dados Técnicos)

| Elemento | Tamanho | Peso | Cor | Uso |
|----------|---------|------|-----|-----|
| **Code Block** | 13px | 400 | gray-800 | Blocos de código, snippets |
| **Boolean Query** | 12px | 500 | gray-900 | Queries booleanas de busca |
| **Technical ID** | 11px | 400 | gray-600 | IDs, hashes, tokens |
| **Inline Code** | 12px | 400 | gray-700 | Código inline em texto |

```css
.lia-code {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.8125rem;
  font-weight: 400;
  line-height: 1.5;
  color: #1F2937;
}

.lia-boolean-query {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.75rem;
  font-weight: 500;
  color: #111827;
}
```

### 1.3.3 Classes CSS de Tipografia

```css
/* ========================================
   OPEN SANS - Títulos, UI e Navigation (85%)
   ======================================== */

.lia-h1 {
  font-family: "Open Sans", sans-serif;
  font-size: 1.5rem;        /* 24px */
  font-weight: 600;
  line-height: 1.2;
  color: #111827;
  letter-spacing: -0.01em;
}

.lia-h2 {
  font-family: "Open Sans", sans-serif;
  font-size: 1.125rem;      /* 18px */
  font-weight: 600;
  line-height: 1.25;
  color: #111827;
}

.lia-h3 {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;      /* 14px */
  font-weight: 600;
  line-height: 1.3;
  color: #111827;
}

.lia-h4 {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;     /* 13px */
  font-weight: 500;
  line-height: 1.35;
  color: #1F2937;
}

.lia-body {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;     /* 13px */
  font-weight: 400;
  line-height: 1.5;
  color: #1F2937;
}

.lia-body-sm {
  font-family: "Open Sans", sans-serif;
  font-size: 0.75rem;       /* 12px */
  font-weight: 400;
  line-height: 1.5;
  color: #374151;
}

.lia-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;     /* 11px */
  font-weight: 500;
  line-height: 1.4;
  color: #1F2937;
}

.lia-caption {
  font-family: "Open Sans", sans-serif;
  font-size: 0.625rem;      /* 10px */
  font-weight: 400;
  line-height: 1.3;
  color: #4B5563;
}

/* ========================================
   INTER - Métricas, Dados e Body (10%)
   ======================================== */

.lia-kpi-lg {
  font-family: "Inter", sans-serif;
  font-size: 2rem;          /* 32px */
  font-weight: 700;
  line-height: 1.1;
  color: #111827;
  letter-spacing: -0.02em;
}

.lia-kpi-md {
  font-family: "Inter", sans-serif;
  font-size: 1.5rem;        /* 24px */
  font-weight: 700;
  line-height: 1.2;
  color: #111827;
}

.lia-kpi-sm {
  font-family: "Inter", sans-serif;
  font-size: 1.125rem;      /* 18px */
  font-weight: 600;
  line-height: 1.3;
  color: #111827;
}

.lia-metric {
  font-family: "Inter", sans-serif;
  font-size: 0.875rem;      /* 14px */
  font-weight: 500;
  line-height: 1.4;
  color: #1F2937;
}

.lia-metric-sm {
  font-family: "Inter", sans-serif;
  font-size: 0.75rem;       /* 12px */
  font-weight: 500;
  line-height: 1.4;
  color: #374151;
}

.lia-table-number {
  font-family: "Inter", sans-serif;
  font-size: 0.8125rem;     /* 13px */
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: #1F2937;
}

/* ========================================
   OPEN SANS - Navigation & Sidebar
   ======================================== */

.lia-sidebar-item {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;     /* 13px */
  font-weight: 500;
  line-height: 1.4;
  color: #4B5563;
  letter-spacing: 0.01em;
}

.lia-sidebar-item-active {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.4;
  color: #111827;
}

.lia-sidebar-section {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;     /* 11px */
  font-weight: 600;
  line-height: 1.3;
  color: #5C5C5C; /* escurecido v4.2.2 */
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ========================================
   ESTILOS EXPRESSIVOS (CTAs, Labels)
   ======================================== */

.lia-section-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.625rem;      /* 10px */
  font-weight: 600;
  line-height: 1.3;
  color: #5C5C5C; /* escurecido v4.2.2 */
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.lia-tag-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.625rem;      /* 10px */
  font-weight: 500;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.lia-cta-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.75rem;       /* 12px */
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.02em;
}

.lia-overline {
  font-family: "Open Sans", sans-serif;
  font-size: 0.625rem;      /* 10px */
  font-weight: 600;
  line-height: 1.3;
  color: #60BED1;           /* Cyan para destaque */
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.lia-status-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.625rem;      /* 10px */
  font-weight: 600;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### 1.3.4 Quando Usar Estilos Expressivos

| Estilo | Uso | Exemplo |
|--------|-----|---------|
| **Section Label** | Títulos de grupo em listas/forms | "INFORMAÇÕES BÁSICAS" |
| **Tag Label** | Badges e tags pequenos | "NOVO", "URGENTE" |
| **CTA Label** | Botões com mais destaque | "CRIAR VAGA" |
| **Overline** | Categoria acima de título principal | "TECNOLOGIA" |
| **Status Label** | Status em badges | "ATIVO", "PENDENTE" |

---

## 1.4 Espaçamento

### 1.4.1 Scale Base (4px)

| Token | Valor | Tailwind | Vuetify | Uso |
|-------|-------|----------|---------|-----|
| `--space-0` | 0 | `p-0` | `pa-0` | Reset |
| `--space-0.5` | 2px | `p-0.5` | - | Micro ajustes |
| `--space-1` | 4px | `p-1` | `pa-1` | Gaps mínimos |
| `--space-1.5` | 6px | `p-1.5` | - | Gaps pequenos |
| `--space-2` | 8px | `p-2` | `pa-2` | Padding interno |
| `--space-2.5` | 10px | `p-2.5` | - | Intermediário |
| `--space-3` | 12px | `p-3` | `pa-3` | Padding cards |
| `--space-4` | 16px | `p-4` | `pa-4` | **Padding padrão** |
| `--space-5` | 20px | `p-5` | `pa-5` | Padding médio |
| `--space-6` | 24px | `p-6` | `pa-6` | Padding grande |
| `--space-8` | 32px | `p-8` | `pa-8` | Seções |
| `--space-10` | 40px | `p-10` | `pa-10` | Áreas amplas |
| `--space-12` | 48px | `p-12` | `pa-12` | Headers |
| `--space-16` | 64px | `p-16` | `pa-16` | Containers |

### 1.4.2 Espaçamento por Componente

| Componente | Padding | Gap Interno | Gap Externo |
|------------|---------|-------------|-------------|
| **Button SM** | `px-3 py-1.5` (12px 6px) | 4px | - |
| **Button MD** | `px-4 py-2` (16px 8px) | 8px | - |
| **Button LG** | `px-5 py-2.5` (20px 10px) | 8px | - |
| **Input** | `px-3 py-2` (12px 8px) | - | - |
| **Card** | `p-4` a `p-6` (16-24px) | 12-16px | 16-24px |
| **Modal Header** | `p-4` (16px) | 8px | - |
| **Modal Body** | `p-6` (24px) | 16px | - |
| **Modal Footer** | `p-4` (16px) | 8px | - |
| **Table Cell** | `px-4 py-3` (16px 12px) | - | - |
| **Badge** | `px-2 py-0.5` (8px 2px) | 4px | - |

---

## 1.5 Grid & Layout

### 1.5.1 Container Widths

| Breakpoint | Max Width | Padding Lateral |
|------------|-----------|-----------------|
| **Mobile** (< 640px) | 100% | 16px |
| **Tablet** (640px - 1023px) | 100% | 24px |
| **Desktop** (≥ 1024px) | 1280px | 32px |
| **Wide** (≥ 1536px) | 1440px | 40px |

### 1.5.2 Grid de 12 Colunas

```html
<!-- Tailwind -->
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-12 md:col-span-6 lg:col-span-4">...</div>
  <div class="col-span-12 md:col-span-6 lg:col-span-8">...</div>
</div>

<!-- Vuetify -->
<v-row class="ga-6">
  <v-col cols="12" md="6" lg="4">...</v-col>
  <v-col cols="12" md="6" lg="8">...</v-col>
</v-row>
```

### 1.5.3 Gaps Padrão

| Contexto | Gap | Classe Tailwind | Classe Vuetify |
|----------|-----|-----------------|----------------|
| **Tight** | 4px | `gap-1` | `ga-1` |
| **Default** | 8px | `gap-2` | `ga-2` |
| **Comfortable** | 12px | `gap-3` | `ga-3` |
| **Spacious** | 16px | `gap-4` | `ga-4` |
| **Wide** | 24px | `gap-6` | `ga-6` |

> **NOTA v4.2.1:** `gap-2` (8px) é o gap mais usado na plataforma (3.804 usos), seguido de `gap-1` (1.470) e `gap-3` (1.222). O gap padrão reflete a densidade compacta da interface (body base 11px).

---

## 1.6 Breakpoints

| Nome | Min Width | Target Device | Classe Tailwind | Vuetify |
|------|-----------|---------------|-----------------|---------|
| **xs** | < 640px | Mobile portrait | (default) | `xs` |
| **sm** | 640px | Mobile landscape | `sm:` | `sm` |
| **md** | 768px | Tablet portrait | `md:` | `md` |
| **lg** | 1024px | Desktop | `lg:` | `lg` |
| **xl** | 1280px | Large desktop | `xl:` | `xl` |
| **2xl** | 1536px | Extra large | `2xl:` | `xxl` |

---

## 1.7 Elevação & Separação Visual

> **⚠️ DECISÃO v4.2.1: Sem sombras.** A plataforma usa design flat. Separação visual entre elementos é feita por **bordas** (`border border-gray-200`), **backgrounds** (alternância white/gray-50) e **gaps**, não por sombras.

### 1.7.1 Política de Sombras

| Regra | Detalhes |
|-------|---------|
| **Sombras removidas** | `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl` — todas removidas da plataforma |
| **Separação por bordas** | `border border-gray-200` (light) / `border-gray-700` (dark) — padrão para cards, inputs, containers |
| **Separação por background** | Alternância `bg-white` / `bg-gray-50` para criar hierarquia visual |
| **Separação por gap** | `gap-2` / `gap-3` entre elementos para criar respiro visual |

### 1.7.2 Alternativas às Sombras

| Antes (deprecated) | Agora (v4.2.1) | Contexto |
|---------------------|----------------|----------|
| `shadow-sm` em cards | `border border-gray-200` | Cards, inputs |
| `shadow-md` em dropdowns | `border border-gray-200` + backdrop | Dropdowns, popovers |
| `shadow-lg` em modais | `border border-gray-200` + backdrop overlay | Modais, dialogs |
| `shadow-xl` em painéis | `border border-gray-200` | Painéis flutuantes |

```html
<!-- Tailwind -->
<div class="border border-gray-200 rounded-md">Card sem sombra</div>
<div class="border border-gray-200 rounded-md bg-white">Card destacado</div>

<!-- Vuetify -->
<v-card elevation="0" border>Card sem sombra</v-card>
```

> **Exceção:** Focus rings (`ring-2 ring-gray-900/20`) continuam usando box-shadow para acessibilidade — não são sombras decorativas.

### ~~1.7.1 Shadow Scale (Legacy — Deprecated)~~

| ~~Nível~~ | ~~Nome~~ | ~~Classe Tailwind~~ | ~~Status~~ |
|-----------|----------|---------------------|------------|
| ~~1~~ | ~~Subtle~~ | ~~`shadow-sm`~~ | ❌ Removido |
| ~~2~~ | ~~Default~~ | ~~`shadow`~~ | ❌ Removido |
| ~~3~~ | ~~Medium~~ | ~~`shadow-md`~~ | ❌ Removido |
| ~~4~~ | ~~Large~~ | ~~`shadow-lg`~~ | ❌ Removido |
| ~~5~~ | ~~XLarge~~ | ~~`shadow-xl`~~ | ❌ Removido |

### 1.7.3 Focus Ring (Acessibilidade)

**Padrão para todos os elementos interativos:**

```css
.interactive-element:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2); /* gray-900 com 20% opacidade */
}
```

```html
<!-- Tailwind -->
<button class="focus:ring-2 focus:ring-gray-900/20 focus:ring-offset-2">
  Botão
</button>

<!-- Vuetify (aplicado automaticamente) -->
<v-btn>Botão com focus ring</v-btn>
```

**Cor do focus ring:** SEMPRE `gray-900` com 20% opacidade (`rgba(17, 24, 39, 0.2)`), nunca colorido.

---

## 1.8 Bordas & Raios

### 1.8.1 Border Radius — 5 Níveis

| Nível | Valor | Tailwind | Usos | Uso |
|-------|-------|----------|------|-----|
| **Sutil** | 4px | `rounded-sm` | 14 | Elementos inline: `<code>`, `<kbd>`, skeletons, date-picker nav |
| **Padrão** | 8px | `rounded-md` | 3.806 (68%) | **Tudo:** botões, inputs, cards, modais, dropdowns, dialogs |
| **Intermediário** | 12px | `rounded-lg` | 52 (<1%) | Cards expandidos, containers médios, painéis secundários |
| **Imersivo** | 16-20px | `rounded-xl` / `rounded-2xl` | 82 (1.5%) | Chat expandido, login, modais especiais, previews, lock buttons |
| **Pill** | 9999px | `rounded-full` | 1.679 (30%) | Badges, avatars, tags, pills |

> **⚠️ NOTA v4.2.1:** 98% do uso é `rounded-md` + `rounded-full`. O `rounded-lg` (12px) existe como nível intermediário para containers que precisam de mais suavidade que 8px mas menos que 16px. O token `--radius-default` (6px / `rounded`) existe em `design-tokens.ts` mas NÃO é usado por componentes reais.

### 1.8.2 Uso Recomendado

| Elemento | Border Radius | Nível |
|----------|---------------|-------|
| **Botões** | `rounded-md` (8px) | Padrão |
| **Inputs** | `rounded-md` (8px) | Padrão |
| **Cards** | `rounded-md` (8px) | Padrão |
| **Modais/Dialogs** | `rounded-md` (8px) | Padrão |
| **Dropdowns** | `rounded-md` (8px) | Padrão |
| **Chat expandido** | `rounded-2xl` (20px) | Imersivo |
| **Login containers** | `rounded-2xl` (20px) | Imersivo |
| **Modais de chat** | `rounded-2xl` (20px) | Imersivo |
| **Lock/unlock buttons** | `rounded-2xl` (20px) | Imersivo |
| **Badges/Skills** | `rounded-full` | Pill |
| **Avatars** | `rounded-full` | Pill |
| **Code inline** | `rounded-sm` (4px) | Sutil |
| **Skeletons** | `rounded-sm` (4px) | Sutil |

### 1.8.3 Espessura de Bordas

| Token | Valor | Tailwind | Uso |
|-------|-------|----------|-----|
| `--border-none` | 0px | `border-0` | Sem borda |
| `--border-default` | 1px | `border` | **Padrão** |
| `--border-medium` | 2px | `border-2` | Destaque, selecionado |

---

## 1.9 Motion & Animation

### 1.9.1 Duração

| Tipo | Duração | Tailwind | Usos | Uso |
|------|---------|----------|------|-----|
| **Instant** | 50ms | `duration-50` | — | Feedback imediato |
| **Fast** | 100ms | `duration-100` | — | Hovers rápidos |
| **Normal** | 200ms | `duration-200` | 107 | **Padrão** — transições de UI, modais, expansões |
| **Slow** | 300ms | `duration-300` | 112 | Sidebars, drawers, painéis |
| **Legacy** | 150ms | `duration-150` | — | Mantido para compatibilidade, migrar para 200ms |

> **NOTA v4.2.1:** `duration-200` e `duration-300` são os mais usados no código (107 e 112 usos respectivamente). O padrão anterior de 150ms foi ajustado para 200ms. Classes de transição mais usadas: `transition-colors` (994×), `transition-all` (801×), `animate-spin` (482×), `animate-pulse` (132×). `transition-all` é aceito como alternativa a `transition-colors` quando múltiplas propriedades mudam simultaneamente.

### 1.9.2 Easing

```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### 1.9.3 Animações Permitidas

```css
/* Pulse para Brain Icon */
@keyframes lia-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.animate-lia-pulse {
  animation: lia-pulse 3s ease-in-out infinite;
}

/* Spin para Loading */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 600ms linear infinite;
}

/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-fade-in {
  animation: fadeIn 150ms ease-out;
}
```

### 1.9.4 Mapeamento de Transições CSS ↔ Vuetify

| Animação CSS LIA | Componente Vuetify | Uso |
|------------------|--------------------|-----|
| `fadeIn 150ms ease-out` | `<v-fade-transition>` | Entrada/saída de elementos |
| `slideInFromBottom 200ms` | `<v-slide-y-transition>` | Modais, menus dropdown |
| `slideInFromRight 300ms` | `<v-slide-x-reverse-transition>` | Painéis laterais, drawers |
| `slideInFromLeft 300ms` | `<v-slide-x-transition>` | Navegação de páginas |
| `scale 150ms ease-out` | `<v-scale-transition>` | FABs, tooltips |
| `expandFromTop 200ms` | `<v-expand-transition>` | Acordeões, colapsáveis |
| `expandX 200ms` | `<v-expand-x-transition>` | Expansão horizontal |
| N/A (custom) | `<v-dialog-transition>` | Modais (built-in do v-dialog) |

**Uso em Vue:**

```vue
<!-- Transição de fade (substitui .animate-fade-in) -->
<v-fade-transition>
  <div v-if="visible">Conteúdo</div>
</v-fade-transition>

<!-- Slide vertical (substitui slideInFromBottom) -->
<v-slide-y-transition>
  <v-card v-if="showCard">...</v-card>
</v-slide-y-transition>

<!-- Expand para acordeões -->
<v-expand-transition>
  <div v-show="expanded">Conteúdo colapsável</div>
</v-expand-transition>

<!-- Grupo com transição (listas) -->
<v-fade-transition group>
  <v-chip v-for="item in items" :key="item.id">{{ item.label }}</v-chip>
</v-fade-transition>
```

**Reduced motion (acessibilidade):**

```vue
<template>
  <component :is="prefersReducedMotion ? 'div' : 'v-fade-transition'">
    <slot />
  </component>
</template>

<script setup lang="ts">
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
</script>
```

---

## 1.10 Glassmorphism & Effects

### 1.10.1 Glassmorphism (Cards e Modais)

**Inspiração ElevenLabs:** Efeito de vidro fosco sutil.

```css
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.glass-card-dark {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

```html
<!-- Tailwind -->
<div class="bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-md p-6 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Card Glass</h3>
  <p class="text-sm text-gray-600 mt-2">Efeito glassmorphism sutil</p>
</div>

<!-- Vuetify -->
<v-card 
  class="pa-6"
  style="background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.05);"
>
  <v-card-title>Card Glass</v-card-title>
  <v-card-text>Efeito glassmorphism sutil</v-card-text>
</v-card>
```

### 1.10.2 Quando Usar

| Uso | Recomendação |
|-----|--------------|
| **Cards sobre imagens** | ✅ Usar glass para legibilidade |
| **Modais overlay** | ✅ Glass sutil no overlay |
| **Sidebars fixas** | ⚠️ Usar com moderação |
| **Cards padrão** | ❌ Preferir bg-white sólido |
| **Mobile** | ⚠️ Performance - testar |

### 1.10.3 Suporte de Navegadores

```css
/* Fallback para navegadores sem suporte */
@supports not (backdrop-filter: blur(10px)) {
  .glass-card {
    background: rgba(255, 255, 255, 0.95);
  }
}
```

---

## 1.11 Elemento Visual LIA (Brain Icon)

### 1.11.1 O Brain Icon como Identidade Visual

O **ícone de cérebro ciano** é o elemento visual chave que representa a LIA em toda a plataforma. Ele funciona como:
- **Identificador da IA**: Sempre que a LIA está presente ou atuando
- **Indicador de automação**: Mostra que algo foi gerado/processado por IA
- **Elemento de marca**: Reconhecimento instantâneo da LIA

### 1.11.2 Especificações do Brain Icon

| Propriedade | Valor | Token |
|-------------|-------|-------|
| **Cor principal** | `#60BED1` | `--wedo-cyan` |
| **Cor em dark mode** | `#60BED1` (mantém) | `--wedo-cyan` |
| **Biblioteca** | Lucide React | `Brain` ou `BrainCircuit` |

### 1.11.3 Tamanhos Padrão

| Contexto | Tamanho | Classes |
|----------|---------|---------|
| **Inline com texto** | 16px | `w-4 h-4` |
| **Badges** | 14px | `w-3.5 h-3.5` |
| **Headers de seção** | 20px | `w-5 h-5` |
| **Cards de feature** | 24px | `w-6 h-6` |
| **Hero sections** | 32px | `w-8 h-8` |
| **Empty states** | 48px | `w-12 h-12` |
| **Onboarding/Marketing** | 64px | `w-16 h-16` |

### 1.11.4 Estados do Brain Icon

| Estado | Visual | CSS |
|--------|--------|-----|
| **Static** | Parado, cor sólida | `text-[#60BED1]` |
| **Resting** | Pulse sutil (3s loop) | `animate-lia-pulse` |
| **Processing** | Pulse mais rápido (1.5s) | `animate-lia-processing` |
| **Success** | Flash de confirmação | Flash verde momentâneo |

```css
/* Brain icon - Estado Resting (pensando) */
.lia-brain-resting {
  color: #60BED1;
  animation: lia-pulse 3s ease-in-out infinite;
}

/* Brain icon - Processando */
.lia-brain-processing {
  color: #60BED1;
  animation: lia-pulse 1.5s ease-in-out infinite;
}

/* Brain icon - Success flash */
@keyframes lia-brain-success {
  0% { color: #60BED1; }
  50% { color: #5DA47A; }
  100% { color: #60BED1; }
}

.lia-brain-success {
  animation: lia-brain-success 600ms ease-out;
}
```

### 1.11.5 Uso do Brain Icon

#### Onde USAR (Obrigatório)

| Local | Exemplo | Tamanho |
|-------|---------|---------|
| **Chat da LIA** | Avatar/indicador da LIA | 24px |
| **Badges "Analisado por LIA"** | Junto ao texto | 14px |
| **Headers de seção IA** | "Insights LIA", "Sugestões" | 20px |
| **Loading states IA** | Processando análise | 32px (pulsing) |
| **Empty states** | "LIA ainda não analisou" | 48px |
| **Sidebar** | Item "LIA" no menu | 18px |
| **Onboarding** | Apresentação da LIA | 64px |

#### Onde NÃO USAR

```
❌ EVITAR:
├── Como decoração genérica
├── Em botões de ação (usar texto)
├── Repetido múltiplas vezes próximas
├── Em elementos que não envolvem IA
├── Com outras cores (sempre cyan)
└── Com efeitos de sombra/glow
```

### 1.11.6 Exemplos de Implementação

```tsx
import { Brain, BrainCircuit } from 'lucide-react'

// Avatar da LIA no chat
<div className="flex items-center gap-2">
  <div className="p-2 rounded-full bg-[#60BED1]/10">
    <Brain className="w-5 h-5 text-[#60BED1]" />
  </div>
  <span className="lia-h4">LIA</span>
</div>

// Badge "Analisado por LIA"
<Badge className="bg-[#60BED1]/10 text-[#0E7490]">
  <Brain className="w-3.5 h-3.5 mr-1" />
  Analisado por LIA
</Badge>

// Header de seção
<div className="flex items-center gap-2 mb-4">
  <Brain className="w-5 h-5 text-[#60BED1]" />
  <h2 className="lia-h2">Insights da LIA</h2>
</div>

// Loading state (processando)
<div className="flex flex-col items-center gap-3">
  <Brain className="w-8 h-8 text-[#60BED1] animate-[lia-pulse_1.5s_ease-in-out_infinite]" />
  <span className="lia-body text-gray-600">LIA está analisando...</span>
</div>
```

---

# PARTE 2: CONTEÚDO & VOZ `[Draft]`

A LIA é uma assistente de recrutamento — sua voz define a experiência da plataforma. Esta seção estabelece como a LIA se comunica, como escrevemos para a interface, e o vocabulário padrão do produto.

## 2.1 Voice & Tone da LIA

### 2.1.1 Persona

A LIA é uma **consultora de recrutamento sênior** — experiente, precisa e empática. Ela não é um chatbot genérico, é uma especialista que domina o universo de R&S.

| Atributo | A LIA É | A LIA NÃO É |
|----------|---------|--------------|
| **Tom** | Profissional e acessível | Formal demais ou casual demais |
| **Expertise** | Consultiva, oferece insights com dados | Robótica, repete scripts fixos |
| **Postura** | Proativa, sugere próximos passos | Passiva, espera comandos explícitos |
| **Linguagem** | Clara, direta, sem jargão desnecessário | Verbosa, evasiva, excessivamente técnica |
| **Empatia** | Reconhece esforço, contextualiza decisões | Fria, transacional, descarta sentimentos |

### 2.1.2 Espectro de Tom

O tom da LIA varia conforme o contexto. A persona é constante, o tom se adapta.

| Contexto | Tom | Exemplo |
|----------|-----|---------|
| **Onboarding** | Acolhedor + guia | *"Bem-vinda! Vou te ajudar a criar sua primeira vaga. Me conta: qual posição você está buscando?"* |
| **Job Creation** | Consultivo + proativo | *"Para um cargo de Engenheiro de Dados Sênior, recomendo incluir experiência com Spark e Airflow. Quer que eu adicione?"* |
| **Screening** | Analítico + confiante | *"Analisei 47 candidatos. 8 atendem aos requisitos técnicos e têm fit cultural acima de 75%. Vamos revisar os top 5?"* |
| **Resultado negativo** | Empático + construtivo | *"O candidato não atingiu o score mínimo em Python (42/100). Porém, tem excelente comunicação. Quer considerar para outra posição?"* |
| **Erro/Problema** | Transparente + solucionador | *"Não consegui acessar o perfil do LinkedIn neste momento. Vou tentar novamente em 5 minutos. Enquanto isso, posso analisar o currículo enviado."* |
| **Celebração** | Genuíno + breve | *"Ótimo! A vaga 'Product Manager' foi publicada com sucesso. Já estou buscando candidatos no banco de talentos."* |

### 2.1.3 Padrões de Escrita Conversacional

**Estrutura de mensagens da LIA:**

```
1. CONTEXTO (o que aconteceu / o que ela fez)
2. INSIGHT (dados relevantes, análise)
3. PRÓXIMO PASSO (pergunta ou sugestão de ação)
```

**Do's & Don'ts:**

| ✅ Fazer | ❌ Evitar |
|----------|-----------|
| Usar primeira pessoa: *"Encontrei 12 candidatos"* | Terceira pessoa: *"Foram encontrados 12 candidatos"* |
| Ser específica com dados: *"3 de 5 requisitos atendidos"* | Vago: *"Alguns requisitos foram atendidos"* |
| Oferecer próximo passo: *"Quer que eu agende as entrevistas?"* | Terminar sem direção: *"Os dados estão disponíveis."* |
| Confirmar antes de ações destrutivas: *"Tem certeza que quer rejeitar esses 15 candidatos?"* | Executar ações irreversíveis sem confirmação |
| Reconhecer o recrutador: *"Boa decisão. Vou priorizar candidatos com esse perfil."* | Ignorar input: *"Ok. Processando."* |
| Admitir limitações: *"Não tenho dados suficientes para essa análise. Preciso de mais informações sobre..."* | Inventar dados ou fingir certeza |

### 2.1.4 Formatação de Mensagens

A LIA usa markdown estruturado para organizar informações complexas:

| Elemento | Quando Usar | Formato |
|----------|-------------|---------|
| **Negrito** | Dados-chave, nomes, scores | `**85/100**` |
| *Itálico* | Citações, exemplos contextuais | `*como mencionou antes*` |
| Listas | 3+ itens para comparação | `- Item 1\n- Item 2` |
| Tabelas | Comparações lado a lado | Tabela markdown |
| Emojis | Nunca em mensagens da LIA | — |
| Quebras | Separar blocos lógicos (contexto → insight → ação) | Parágrafo simples |

---

## 2.2 Escrita para Interface

### 2.2.1 Princípios de UX Writing

| Princípio | Descrição | Exemplo Bom | Exemplo Ruim |
|-----------|-----------|-------------|--------------|
| **Clareza** | Diga exatamente o que acontece | "Vaga publicada com sucesso" | "Operação concluída" |
| **Concisão** | Elimine palavras desnecessárias | "Salvar vaga" | "Clique aqui para salvar a vaga" |
| **Ação** | Use verbos ativos no infinitivo | "Adicionar candidato" | "Adição de candidato" |
| **Contexto** | Explique o porquê quando relevante | "Arquivar vaga (candidatos mantidos)" | "Arquivar" |
| **Consistência** | Mesma ação = mesma palavra sempre | "Salvar" em todo o sistema | "Salvar" / "Guardar" / "Gravar" alternando |

### 2.2.2 Padrões por Componente

| Componente | Padrão | Exemplo |
|------------|--------|---------|
| **Botão primário** | Verbo no infinitivo, 1-3 palavras | "Criar vaga", "Publicar", "Confirmar" |
| **Botão secundário** | Verbo ou substantivo, contexto claro | "Cancelar", "Voltar", "Ver detalhes" |
| **Botão destrutivo** | Verbo explícito + objeto | "Excluir vaga", "Rejeitar candidato" |
| **Label de input** | Substantivo ou pergunta curta | "Nome completo", "E-mail corporativo" |
| **Placeholder** | Exemplo ou instrução breve | "ex: maria@empresa.com" |
| **Helper text** | Restrição ou dica relevante | "Mínimo 8 caracteres, com 1 número" |
| **Error message** | O que deu errado + como corrigir | "E-mail inválido. Use formato nome@domínio.com" |
| **Empty state** | O que está vazio + como resolver | "Nenhum candidato nesta etapa. Mova candidatos do banco de talentos." |
| **Toast/Sucesso** | O que aconteceu, brevemente | "Candidato movido para Entrevista" |
| **Modal de confirmação** | Consequência + ação clara | "Ao rejeitar, o candidato será notificado. Deseja continuar?" |

### 2.2.3 Capitalização

| Elemento | Padrão | Exemplo |
|----------|--------|---------|
| Títulos de página | Title Case (PT-BR) | "Banco de Talentos" |
| Nomes de seção | Title Case (PT-BR) | "Informações da Vaga" |
| Labels de campo | Sentence case | "Nome completo" |
| Botões | Sentence case (verbo no infinitivo) | "Criar vaga" |
| Tabs | Title Case | "Candidatos", "Pipeline" |
| Menu items | Sentence case | "Configurações da conta" |
| Tooltips | Sentence case, sem ponto final | "Editar informações do candidato" |
| Badges/Status | Title Case curto | "Em Análise", "Aprovado" |

---

## 2.3 Glossário de Termos

Vocabulário padronizado da plataforma. Use SEMPRE estes termos, nunca sinônimos.

| Termo Oficial | Sinônimos Proibidos | Contexto |
|---------------|---------------------|----------|
| **Vaga** | Posição, cargo, oportunidade | Abertura de trabalho no sistema |
| **Candidato** | Profissional, talento (exceto "Banco de Talentos") | Pessoa sendo avaliada |
| **Pipeline** | Funil, esteira, fluxo | Etapas de seleção de uma vaga |
| **Etapa** | Fase, estágio, step | Momento no pipeline |
| **Score WSI** | Nota, pontuação, rating | Avaliação WSI (0-100) |
| **Fit Cultural** | Alinhamento, match | Compatibilidade com cultura da empresa |
| **Triagem** | Screening, filtro inicial | Primeira análise de candidatos |
| **Banco de Talentos** | Pool, base de candidatos | Repositório central de candidatos |
| **Processo Seletivo** | Seleção, recrutamento | Ciclo completo de contratação |
| **Entrevista** | Conversa, call | Etapa de avaliação síncrona |
| **Feedback** | Retorno, parecer | Avaliação/resposta sobre candidato |
| **Publicar** | Postar, divulgar | Tornar vaga visível externamente |
| **Arquivar** | Fechar, encerrar (vaga) | Mover vaga para inativo |
| **Rejeitar** | Reprovar, eliminar | Mover candidato para "Não Aprovado" |
| **Aprovar** | Selecionar, aceitar | Mover candidato para próxima etapa |

---

## 2.4 Data Formats `[Draft]`

Formatação padronizada para dados na plataforma. Locale: PT-BR. Todas as datas, números e valores monetários seguem as convenções brasileiras.

### 2.4.1 Formatação de Datas e Horas

| Formato | Exemplo | Uso | Font |
|---------|---------|-----|------|
| Data curta | `24 fev 2026` | Tabelas, cards, listas | Open Sans |
| Data longa | `24 de fevereiro de 2026` | Headers, títulos de página | Open Sans |
| Data + hora | `24 fev 2026, 14:30` | Logs, histórico de atividades | Open Sans |
| Hora | `14:30` | Agendamentos, timestamps | Inter |
| Data relativa | `há 2 min`, `há 3 horas`, `ontem`, `há 5 dias` | Chat timestamps, atividades recentes | Open Sans |
| Data relativa longa | `há 2 semanas`, `há 1 mês` | Itens antigos | Open Sans |

**Regras de data relativa:**
- < 1 minuto → "agora"
- 1-59 minutos → "há X min"
- 1-23 horas → "há X horas"
- 1 dia → "ontem"
- 2-6 dias → "há X dias"
- 7+ dias → data curta ("24 fev 2026")

### 2.4.2 Formatação Numérica

| Formato | Exemplo | Uso | Font |
|---------|---------|-----|------|
| Score WSI | `84/100` | Cards de candidato, pipeline | Inter `font-bold tnum` |
| Porcentagem | `87%` | Fit cultural, match scores | Inter `tnum` |
| Salário | `R$ 12.000` | Detalhes da vaga | Inter `tnum` |
| Faixa salarial | `R$ 8.000 – R$ 12.000` | Criação de vaga | Inter `tnum` |
| Contagem | `247 candidatos` | Contadores, paginação | Inter (número) + Open Sans (texto) |
| Grande número | `1.2K`, `45.8K` | KPI cards, dashboards | Inter `font-bold` |
| Telefone | `+55 11 99999-9999` | Contato do candidato | Inter `tnum` |
| Experiência | `5 anos` | Perfil do candidato | Inter (número) + Open Sans (texto) |

### 2.4.3 Formatação de Listas

| Formato | Exemplo | Uso |
|---------|---------|-----|
| Lista curta (≤3) | `Python, React e Node.js` | Skills, tags inline |
| Lista truncada (>3) | `Python, React e +3` | Skills em cards compactos |
| Lista expandida | `Python, React, Node.js, AWS, Docker` | Detalhes, modais |

### 2.4.4 Regras de Font por Tipo de Dado

| Tipo de Dado | Font | Feature Settings | Classe Tailwind |
|-------------|------|------------------|-----------------|
| Números, scores, percentuais | Inter | `'tnum' 1` | `font-['Inter']` + style `font-feature-settings: 'tnum' 1` |
| Valores monetários | Inter | `'tnum' 1` | `font-['Inter']` |
| Datas (texto) | Open Sans | — | `font-['Open_Sans']` |
| Horas isoladas | Inter | `'tnum' 1` | `font-['Inter']` |
| Labels, texto descritivo | Open Sans | — | `font-['Open_Sans']` |

---

# PARTE 3: COMPONENTES

## 3.1 Botões

### 3.1.1 Hierarquia de Botões

| Tipo | Background | Text | Border | Tailwind | Vuetify | Uso |
|------|------------|------|--------|----------|---------|-----|
| **Primary** | `bg-gray-900` | `white` | none | `bg-gray-900 text-white` | `color="grey-darken-4"` | Ação principal |
| **Secondary** | `bg-gray-100` | `gray-950` | none | `bg-gray-100 text-gray-950` | `variant="tonal"` | Ação secundária |
| **Outline** | `transparent` | `gray-700` | `border-gray-300` | `border border-gray-300` | `variant="outlined"` | Ação alternativa |
| **Ghost** | `transparent` | `gray-600` | none | `hover:bg-gray-100` | `variant="text"` | Ação sutil |
| **Destructive** | `bg-red-600` | `white` | none | `bg-red-600 text-white` | `color="red"` | Ações destrutivas |

> **📐 NOTA v4.2.1 — font-weight 500 universal:**  
> Todas as variantes de botão usam `font-medium` (500), incluindo ghost. Na densidade compacta da plataforma (font-size 11px), o peso 500 produz um visual mais limpo e equilibrado. O ghost se diferencia pela ausência de background, não pelo peso da fonte.

### 3.1.2 Estados de Botão

| Estado | Primary | Secondary | Outline | Ghost |
|--------|---------|-----------|---------|-------|
| **Default** | `bg-gray-900` | `bg-gray-100` | `border-gray-300` | `transparent` |
| **Hover** | `bg-gray-800` | `bg-gray-200` | `bg-gray-50 border-gray-400` | `bg-gray-100` |
| **Active** | `bg-gray-950` | `bg-gray-300` | `bg-gray-100` | `bg-gray-200` |
| **Focus** | `ring-2 ring-gray-900/20` | `ring-2 ring-gray-500/20` | `ring-2 ring-gray-500/20` | `ring-2 ring-gray-500/20` |
| **Disabled** | `bg-gray-400` | `opacity-50` | `opacity-50` | `opacity-50` |

### 3.1.3 Especificações CSS

> **⚠️ NOTA v4.2.1:** Todos os botões usam `font-weight: 500` (font-medium) e `border-radius: 8px` (rounded-md). O font-size base é `11px` para todas as variantes. Essas são decisões conscientes de design — o peso 500 produz um visual mais limpo na densidade compacta da plataforma.

```css
.lia-btn-primary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;       /* 11px */
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;          /* rounded-md */
  background-color: #111827;
  color: #FFFFFF;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-primary:hover {
  background-color: #1F2937;
}

.lia-btn-primary:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2);
}

.lia-btn-primary:disabled {
  background-color: #999999;
  cursor: not-allowed;
}

.lia-btn-secondary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;       /* 11px */
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background-color: #F3F4F6;   /* bg-gray-100 — solid, sem borda */
  color: #030712;              /* text-gray-950 */
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-outline {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;       /* 11px */
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background-color: #FFFFFF;
  color: #1F2937;              /* text-gray-800 */
  border: 1px solid #BEBEBE;  /* border-gray-300 */
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-ghost {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;       /* 11px */
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background-color: transparent;
  color: #1F2937;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-destructive {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;       /* 11px */
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background-color: #DC2626;
  color: #FFFFFF;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}
```

> **⚠️ Botões legados (deprecated):** Existem classes `lia-btn-primary` com `bg-[#60BED1]` (cyan) em `design-tokens.css` e `wedo-button-primary` em `globals.css`. São restos da v3, usados em 9 componentes. Migrar gradualmente para as variantes padrão acima.

### 3.1.4 Tamanhos de Botão

| Tamanho | Padding | Font Size | Height | Icon Size |
|---------|---------|-----------|--------|-----------|
| **XS** | `px-2 py-1` | 11px | 28px | 14px |
| **SM** | `px-3 py-1.5` | 12px | 32px | 14px |
| **MD** | `px-4 py-2` | 13px | 36px | 16px |
| **LG** | `px-5 py-2.5` | 14px | 40px | 18px |
| **XL** | `px-6 py-3` | 15px | 48px | 20px |

### 3.1.5 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'destructive'` | `'primary'` | Estilo visual do botão |
| `size` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Tamanho do botão |
| `disabled` | `boolean` | `false` | Desabilita interação |
| `loading` | `boolean` | `false` | Exibe spinner e desabilita |
| `icon` | `ReactNode` | — | Ícone antes do label |
| `iconRight` | `ReactNode` | — | Ícone após o label |
| `iconOnly` | `boolean` | `false` | Botão apenas com ícone (requer `aria-label`) |
| `fullWidth` | `boolean` | `false` | Largura 100% do container |
| `as` | `'button' \| 'a' \| 'link'` | `'button'` | Elemento HTML renderizado |
| `href` | `string` | — | URL para variant como link |
| `onClick` | `() => void` | — | Callback de clique |
| `className` | `string` | — | Classes CSS adicionais |

### 3.1.6 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Um botão primário por seção/modal | Múltiplos botões primários competindo |
| Label como verbo de ação: "Criar vaga" | Labels genéricos: "Clique aqui", "OK" |
| Touch target mínimo 44x44px em mobile | Botões menores que 32px height |
| `aria-label` em botões icon-only | Ícone sem label acessível |
| Botão destrutivo (vermelho) para excluir/rejeitar | Botão primário (preto) para ações destrutivas |
| Loading state com spinner ao submeter | Desabilitar sem feedback visual |
| Ordem: Secundário (esq) → Primário (dir) | Primário à esquerda do secundário |

---

## 3.2 Inputs & Forms

### 3.2.1 Estados de Input

| Estado | Border | Background | Text | Ring |
|--------|--------|------------|------|------|
| **Default** | `border-gray-300` | `white` | `gray-800` | none |
| **Hover** | `border-gray-400` | `white` | `gray-800` | none |
| **Focus** | `border-gray-900` | `white` | `gray-900` | `ring-2 ring-gray-900/20` |
| **Disabled** | `border-gray-200` | `gray-100` | `gray-400` | none |
| **Error** | `border-red-500` | `white` | `gray-800` | `ring-2 ring-red-500/20` |
| **Success** | `border-green-500` | `white` | `gray-800` | none |

### 3.2.2 Implementação

```html
<!-- Tailwind -->
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Nome</label>
  <input 
    type="text"
    placeholder="Digite seu nome"
    class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-900"
  />
</div>

<!-- Vuetify -->
<v-text-field
  label="Nome"
  placeholder="Digite seu nome"
  variant="outlined"
  density="comfortable"
></v-text-field>
```

---

## 3.3 Cards

### 3.3.1 Card Padrão

```html
<!-- Tailwind -->
<div class="bg-white rounded-md shadow-sm border border-gray-200 p-6">
  <h3 class="text-base font-semibold text-gray-900 mb-2 font-['Open_Sans']">
    Título do Card
  </h3>
  <p class="text-sm text-gray-600">
    Descrição do conteúdo do card aqui.
  </p>
</div>

<!-- Vuetify -->
<v-card class="pa-6">
  <v-card-title class="text-base font-weight-semibold text-grey-darken-4 mb-2">
    Título do Card
  </v-card-title>
  <v-card-text class="text-sm text-grey-darken-1 pa-0">
    Descrição do conteúdo do card aqui.
  </v-card-text>
</v-card>
```

### 3.3.2 Card Interativo

```html
<!-- Tailwind -->
<div class="bg-white rounded-md shadow-sm border border-gray-200 p-6 transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
  <h3 class="text-base font-semibold text-gray-900">Card Interativo</h3>
  <p class="text-sm text-gray-600 mt-2">Passe o mouse para ver o efeito</p>
</div>

<!-- Vuetify -->
<v-card class="pa-6" hover>
  <v-card-title>Card Interativo</v-card-title>
  <v-card-text>Passe o mouse para ver o efeito</v-card-text>
</v-card>
```

### 3.3.3 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'default' \| 'interactive' \| 'elevated' \| 'flat'` | `'default'` | Estilo do card |
| `padding` | `'none' \| 'sm' \| 'md' \| 'lg'` | `'md'` | Espaçamento interno (none=0, sm=16px, md=24px, lg=32px) |
| `hover` | `boolean` | `false` | Efeito hover (shadow + translateY) |
| `selected` | `boolean` | `false` | Estado selecionado (borda cyan) |
| `disabled` | `boolean` | `false` | Card desabilitado (opacity 50%) |
| `onClick` | `() => void` | — | Torna card clicável (adiciona cursor pointer) |
| `as` | `'div' \| 'article' \| 'section'` | `'div'` | Elemento HTML renderizado |
| `className` | `string` | — | Classes CSS adicionais |

### 3.3.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Border radius `rounded-md` (8px) consistente | Misturar border radius diferentes entre cards |
| Sombra sutil `shadow-sm` para elevação | Sombras dramáticas (`shadow-xl`) sem necessidade |
| Conteúdo com hierarquia clara (título → descrição → ações) | Excesso de informação sem hierarquia |
| Card interativo com hover visível e cursor pointer | Card clicável sem indicação visual |
| Padding consistente (24px padrão) | Padding inconsistente entre cards do mesmo grupo |
| Glassmorphism (`backdrop-blur-sm`) apenas em cards sobrepostos | Glassmorphism em cards simples (poluição visual) |

---

## 3.4 Modais

### 3.4.1 Tamanhos Fixos

| Tamanho | Max Width | Pixels | Tailwind | Uso |
|---------|-----------|--------|----------|-----|
| **XS** | `max-w-sm` | 384px | `max-w-sm` | Confirmações simples |
| **S** | `max-w-md` | 448px | `max-w-md` | Forms compactos |
| **M** | `max-w-lg` | 512px | `max-w-lg` | **Padrão** - Forms médios |
| **L** | `max-w-2xl` | 672px | `max-w-2xl` | Edição completa |
| **XL** | `max-w-4xl` | 896px | `max-w-4xl` | Visualizações amplas |

**PROIBIDO:** Usar tamanhos intermediários (max-w-xl, max-w-3xl, max-w-5xl)

### 3.4.2 Estrutura

```html
<!-- Tailwind -->
<div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" aria-hidden="true"></div>
<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-md shadow-xl max-w-lg w-full">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-sm font-semibold text-gray-900">Título do Modal</h2>
      <button class="text-gray-600 hover:text-gray-900 p-1 rounded hover:bg-gray-100">
        <svg class="w-5 h-5">...</svg>
      </button>
    </div>
    <!-- Body -->
    <div class="px-6 py-4">
      <!-- Conteúdo -->
    </div>
    <!-- Footer -->
    <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
      <button class="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded">Cancelar</button>
      <button class="px-4 py-2 text-sm bg-gray-900 text-white rounded">Confirmar</button>
    </div>
  </div>
</div>

<!-- Vuetify -->
<v-dialog v-model="dialog" max-width="512">
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between">
      <span class="text-sm font-weight-semibold">Título do Modal</span>
      <v-btn icon="mdi-close" variant="text" size="small" @click="dialog = false"></v-btn>
    </v-card-title>
    <v-divider></v-divider>
    <v-card-text><!-- Conteúdo --></v-card-text>
    <v-divider></v-divider>
    <v-card-actions class="justify-end ga-2">
      <v-btn variant="outlined">Cancelar</v-btn>
      <v-btn color="grey-darken-4">Confirmar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

### 3.4.3 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `open` | `boolean` | `false` | Controla visibilidade do modal |
| `onClose` | `() => void` | — | Callback ao fechar |
| `title` | `string` | — | Título do modal (header) |
| `size` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Tamanho máximo (vide tabela 3.4.1) |
| `closeOnOverlay` | `boolean` | `true` | Fecha ao clicar no overlay |
| `closeOnEsc` | `boolean` | `true` | Fecha ao pressionar Escape |
| `showCloseButton` | `boolean` | `true` | Exibe botão X no header |
| `footer` | `ReactNode` | — | Conteúdo do rodapé (botões de ação) |
| `preventClose` | `boolean` | `false` | Previne fechamento (para formulários em progresso) |
| `className` | `string` | — | Classes CSS adicionais para o container |

### 3.4.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar tamanhos padronizados (XS, S, M, L, XL) | Tamanhos custom ou intermediários |
| Fechar com Escape e clique no overlay | Prender usuário sem saída |
| Título conciso (máx 5 palavras) | Títulos longos que truncam |
| Footer com botões: Cancelar (outline) + Ação (primary) | Apenas um botão sem opção de cancelar |
| Overlay com `backdrop-blur-sm` + `bg-black/50` | Overlay opaco sem blur (parece flat) |
| Focus trap dentro do modal | Focus escapando para conteúdo atrás |
| Border radius `rounded-md` (8px) | Border radius diferente do padrão |
| Confirmação extra para ações destrutivas | Excluir dados com um único clique |

---

## 3.5 Tabelas

### 3.5.1 Estrutura Básica

```html
<!-- Tailwind -->
<div class="bg-white rounded-md border border-gray-200 overflow-hidden">
  <table class="w-full">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800 font-['Inter']">
          NOME
        </th>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800">STATUS</th>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800">SCORE</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-200">
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 text-sm text-gray-900">João Silva</td>
        <td class="px-6 py-4">
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
            Ativo
          </span>
        </td>
        <td class="px-6 py-4 text-sm text-gray-900 font-['Inter']" style="font-feature-settings: 'tnum' 1;">95</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Vuetify -->
<v-data-table :headers="headers" :items="items" class="elevation-1">
  <template #item.status="{ item }">
    <v-chip color="green" size="small" variant="outlined">{{ item.status }}</v-chip>
  </template>
</v-data-table>
```

### 3.5.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `columns` | `Column[]` | `[]` | Definição das colunas (header, key, sortable) |
| `data` | `Row[]` | `[]` | Array de dados da tabela |
| `sortable` | `boolean` | `false` | Habilita ordenação por coluna |
| `pagination` | `boolean` | `true` | Mostra controles de paginação |
| `pageSize` | `10 \| 25 \| 50` | `10` | Itens por página |
| `loading` | `boolean` | `false` | Exibe skeleton no corpo da tabela |
| `emptyMessage` | `string` | `'Nenhum resultado'` | Texto do empty state |
| `onRowClick` | `(row: Row) => void` | — | Callback ao clicar em uma linha |
| `striped` | `boolean` | `true` | Alterna cor de fundo entre linhas |
| `stickyHeader` | `boolean` | `false` | Header fixo durante scroll |

### 3.5.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar font Inter para dados numéricos e scores | Usar Open Sans para colunas de números |
| Zebra striping para tabelas com +5 linhas | Tabela sem diferenciação visual entre linhas |
| Paginação para +10 itens | Scroll infinito em tabelas de dados |
| Header sticky em tabelas longas | Header que desaparece no scroll |
| Ações contextuais por linha (hover) | Botões fixos ocupando espaço em cada linha |
| Headers em UPPER CASE `text-[11px] font-semibold` | Headers em sentence case ou tamanhos variados |

---

## 3.6 Badges & Tags

> **📐 Reconciliação Chip/Badge border-radius:**  
> O Vuetify defaults configura `VChip` com `rounded: 'sm'` (4px) para uso geral como **tags de filtro** e **categorias técnicas**. Porém, badges de status e skills usam `rounded-full` (pill) tanto no Tailwind (`rounded-full`) quanto no Vuetify (override inline: `rounded="pill"`). **Regra:** `rounded-sm` = tags/filtros técnicos (clicáveis, removíveis). `rounded-full` = badges de status, skills, contadores (informativos, estáticos).

### 3.6.1 Badge Padrão

```html
<!-- Tailwind -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700 border border-gray-200">
  Badge
</span>

<!-- Vuetify -->
<v-chip size="small" variant="outlined">Badge</v-chip>
```

### 3.6.2 Badges Semânticos

```html
<!-- Success -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">
  Ativo
</span>

<!-- Warning -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
  Pendente
</span>

<!-- Error -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium bg-red-50 text-red-700 border border-red-200">
  Rejeitado
</span>
```

### 3.6.3 Badges WeDo (10% Accent)

```html
<!-- Cyan (LIA) -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium text-[#60BED1] border border-[#60BED1]/20" style="background: rgba(96,190,209,0.1);">
  LIA
</span>

<!-- Green (Candidatos) -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium text-[#5DA47A] border border-[#5DA47A]/20" style="background: rgba(93,164,122,0.1);">
  Candidato
</span>

<!-- Purple (Insights) -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium text-[#9860D1] border border-[#9860D1]/20" style="background: rgba(152,96,209,0.1);">
  Insight
</span>
```

### 3.6.4 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'default' \| 'success' \| 'warning' \| 'error' \| 'wedo-cyan' \| 'wedo-green' \| 'wedo-purple'` | `'default'` | Variante semântica |
| `size` | `'sm' \| 'md'` | `'sm'` | Tamanho do badge |
| `rounded` | `'full' \| 'sm'` | `'full'` | `full` para status/skills, `sm` para tags/filtros técnicos |
| `removable` | `boolean` | `false` | Mostra botão X para remover (apenas tags) |
| `icon` | `ReactNode` | — | Ícone antes do texto |
| `children` | `ReactNode` | — | Conteúdo do badge |

### 3.6.5 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| `rounded-full` para badges de status e skills | `rounded-full` para tags técnicas removíveis |
| `rounded-sm` para tags de filtro clicáveis | `rounded-sm` para badges informativos de status |
| `text-[10px]` como tamanho padrão | Tamanhos maiores que `text-xs` em badges |
| Cores semânticas consistentes (green=ativo, amber=pendente, red=rejeitado) | Cores aleatórias sem significado |
| Máximo 3-4 badges visíveis por item + counter "+N" | Exibir 10+ badges sem truncar |

---

## 3.7 Tooltips & Popovers

### 3.7.1 Tooltip

```html
<!-- Tailwind -->
<div class="relative group inline-block">
  <button class="p-2 text-gray-600 hover:text-gray-900">
    <svg class="w-5 h-5">...</svg>
  </button>
  <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none">
    Editar candidato
    <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
  </div>
</div>

<!-- Vuetify -->
<v-tooltip text="Editar candidato" location="top">
  <template #activator="{ props }">
    <v-btn icon="mdi-pencil" v-bind="props"></v-btn>
  </template>
</v-tooltip>
```

### 3.7.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `content` | `string \| ReactNode` | — | Conteúdo do tooltip/popover |
| `side` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'top'` | Posição relativa ao trigger |
| `delayDuration` | `number` | `200` | Delay em ms antes de abrir (tooltip) |
| `triggerAsChild` | `boolean` | `true` | Usa o filho como trigger sem wrapper |

### 3.7.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Tooltip para ícones sem label | Tooltip em botões com texto visível |
| `bg-gray-900 text-white text-xs` para tooltips | Tooltips com backgrounds claros ou coloridos |
| Delay de 200ms antes de mostrar | Mostrar tooltip instantaneamente (causa flickering) |
| Conteúdo de 1 linha, máximo 2 | Tooltips com parágrafos longos (usar popover) |
| Popover para conteúdo interativo ou multi-linha | Tooltip com botões ou links clicáveis |

---

## 3.8 Toasts & Alerts

> **Implementação oficial: Sonner** (`sonner` npm package) com `richColors` habilitado.
> Posição padrão: `top-right`. O sistema Radix/shadcn toast foi removido.

### 3.8.1 Toast Variants (Sonner richColors)

| Tipo | Método | Cor automática (richColors) | Uso |
|------|--------|----------------------------|-----|
| **Success** | `toast.success()` | Verde | Confirmações de ações bem-sucedidas |
| **Warning** | `toast.warning()` | Amarelo | Avisos e alertas não-críticos |
| **Error** | `toast.error()` | Vermelho | Erros e falhas |
| **Info** | `toast.info()` | Azul | Informações gerais |

```tsx
import { toast } from "sonner"

toast.success("Candidato salvo!", { description: "Dados atualizados com sucesso" })
toast.error("Erro ao salvar", { description: "Tente novamente" })
toast.warning("Atenção", { description: "Campos obrigatórios não preenchidos" })
toast.info("Dica", { description: "Use filtros para refinar a busca" })
```

```tsx
// layout.tsx — configuração global
import { Toaster as SonnerToaster } from "sonner"

<SonnerToaster position="top-right" richColors />
```

### 3.8.2 API Sonner

| Parâmetro | Type | Default | Descrição |
|-----------|------|---------|-----------|
| `message` | `string` | — | Primeiro argumento: título do toast |
| `description` | `string` | — | Texto descritivo (segundo arg, dentro de options) |
| `duration` | `number` | `4000` | Tempo em ms antes de auto-dismiss |
| `action` | `{ label: string, onClick: () => void }` | — | Botão de ação opcional |

### 3.8.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `toast.success/error/warning/info()` direto | Usar `useToast()` hook (removido) |
| `import { toast } from "sonner"` | `import { useToast } from "@/components/ui/use-toast"` |
| Auto-dismiss após 4s para sucesso/info | Auto-dismiss para erros (devem exigir ação) |
| Posição consistente `top-right` | Alternar posição entre páginas |
| Máximo 3 toasts simultâneos (stack) | Exibir 5+ toasts empilhados |
| Toast para confirmações rápidas, Alert inline para validações | Toast para erros de formulário |

---

## 3.9 Navigation

### 3.9.1 Sidebar (Open Sans)

> **⚠️ NOTA v4.2.1:** Valores atualizados para refletir a implementação real em `sidebar.tsx`. Sidebar é colapsada por padrão (64px), expandível ao hover, e resizável via drag quando expandida (200-450px).

| Propriedade | Valor | Nota |
|-------------|-------|------|
| **Width colapsada** | 64px | Apenas ícones + tooltips |
| **Width expandida** | 256px (default) | Resizável: 200-450px via drag |
| **Background** | `bg-white` | Fundo branco limpo |
| **Border** | `border-r border-gray-100` | Borda sutil (mais leve que gray-200) |
| **Ícones** | `w-4 h-4` (16px) | Proporcionais ao espaço compacto |
| **Label font** | `text-[13px] font-medium` | Open Sans |
| **Section header** | `text-[11px] font-semibold text-gray-500 uppercase` | Separador de grupos |
| **Item ativo** | `bg-gray-100 text-gray-950 font-semibold` | Destaque claro |
| **Item inativo** | `text-gray-600 hover:bg-gray-50` | Estado padrão |
| **Hover expand** | Sim | Expand temporário ao passar mouse na sidebar colapsada |

```html
<!-- Tailwind -->
<nav class="w-16 h-screen bg-white border-r border-gray-100 p-2 transition-all duration-200">
  <div class="mb-6">
    <div class="flex items-center justify-center py-2">
      <svg class="w-6 h-6 text-[#60BED1]"><!-- Brain Icon --></svg>
    </div>
  </div>
  
  <div class="space-y-1">
    <!-- Item ativo (Open Sans) -->
    <a href="#" class="flex items-center justify-center p-2 bg-gray-100 rounded-md">
      <svg class="w-4 h-4 text-gray-950">...</svg>
    </a>
    
    <!-- Item inativo (Open Sans) -->
    <a href="#" class="flex items-center justify-center p-2 text-gray-600 hover:bg-gray-50 rounded-md">
      <svg class="w-4 h-4">...</svg>
    </a>
  </div>
</nav>

<!-- Sidebar expandida -->
<nav class="w-64 h-screen bg-white border-r border-gray-100 p-3 transition-all duration-200" style="min-width: 200px; max-width: 450px; resize: horizontal;">
  <div class="space-y-1">
    <a href="#" class="flex items-center gap-3 px-3 py-2 bg-gray-100 rounded-md">
      <svg class="w-4 h-4 text-gray-950">...</svg>
      <span class="text-[13px] font-semibold text-gray-950 font-['Open_Sans']">Dashboard</span>
    </a>
    <a href="#" class="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md">
      <svg class="w-4 h-4">...</svg>
      <span class="text-[13px] font-medium font-['Open_Sans']">Vagas</span>
    </a>
  </div>
</nav>

<!-- Vuetify -->
<v-navigation-drawer permanent width="256" :rail="collapsed" rail-width="64">
  <v-list>
    <v-list-item 
      v-for="item in items" 
      :key="item.title"
      :prepend-icon="item.icon"
      :title="item.title"
      :active="item.active"
      color="grey-darken-4"
    ></v-list-item>
  </v-list>
</v-navigation-drawer>
```

### 3.9.2 Breadcrumbs

```html
<!-- Tailwind -->
<nav class="flex items-center gap-2 text-sm">
  <a href="#" class="text-gray-600 hover:text-gray-900">Home</a>
  <svg class="w-4 h-4 text-gray-400">...</svg>
  <a href="#" class="text-gray-600 hover:text-gray-900">Vagas</a>
  <svg class="w-4 h-4 text-gray-400">...</svg>
  <span class="text-gray-900 font-semibold">Desenvolvedor</span>
</nav>

<!-- Vuetify -->
<v-breadcrumbs :items="['Home', 'Vagas', 'Desenvolvedor']"></v-breadcrumbs>
```

### 3.9.3 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `items` | `NavItem[]` | `[]` | Itens de navegação (icon, label, href, badge) |
| `collapsed` | `boolean` | `true` | Sidebar colapsada (64px, apenas ícones) |
| `resizable` | `boolean` | `true` | Permite redimensionar via drag (200-450px) |
| `expandOnHover` | `boolean` | `true` | Expand temporário ao hover na sidebar colapsada |
| `activeItem` | `string` | — | ID do item ativo |
| `onItemClick` | `(item: NavItem) => void` | — | Callback ao clicar em item |
| `footer` | `ReactNode` | — | Conteúdo do rodapé (avatar, settings) |
| `width` | `number` | `256` | Largura expandida em px |

### 3.9.4 TopBar `[Stable]`

> Barra superior fixa com busca global, notificações, Brain icon e menu do usuário.

| Propriedade | Valor | Nota |
|-------------|-------|------|
| **Height** | 48px (`h-12`) | Fixa, não colapsa |
| **Background** | `bg-white` / `dark:bg-gray-900` | Mesmo do sidebar |
| **Border** | `border-b border-gray-200` | Separação sutil do conteúdo |
| **Position** | `sticky top-0 z-50` | Sempre visível |
| **Elementos** | Brain icon (esq), busca global (centro), notificações + avatar (dir) | Layout flex justify-between |

**Componentes internos:**
- **Brain icon** — `w-5 h-5 text-wedo-cyan`, clicável para abrir LIA tips
- **Busca global** — Abre `GlobalSearchModal` via ícone Search
- **Notificações** — `NotificationSystem` com badge counter
- **Avatar** — Dropdown com perfil, alterar senha, logout

**Props API:**

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `onNavigate` | `(page: string) => void` | — | Callback de navegação |
| `currentPage` | `string` | — | Página ativa (para highlight) |
| `onShowLIATips` | `() => void` | — | Callback para abrir LIA tips |

### 3.9.5 PageTransition `[Stable]`

> Wrappers de animação para transições entre páginas.

| Variante | Animação | Duração | Uso |
|----------|----------|---------|-----|
| **PageTransition** | `slideInUp` | 400ms ease-out | Transição padrão entre páginas |
| **SlidePageTransition** | `slideInRight` | 300ms ease-out | Navegação lateral (drawer→página) |
| **FadePageTransition** | `fadeIn` | 250ms ease-in-out | Transições suaves (modais, overlays) |
| **AnimatedPageWrapper** | nenhuma | — | Wrapper sem animação (passthrough) |

**Props API:**

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `children` | `ReactNode` | — | Conteúdo da página |
| `className` | `string` | `""` | Classes CSS adicionais |

### 3.9.6 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Ícones de 16px (`w-4 h-4`) com tooltip quando colapsado | Ícones sem tooltip no modo colapsado |
| Item ativo com `bg-gray-100 text-gray-950 font-semibold` | Item ativo sem diferenciação visual |
| Sidebar fixa (`sticky top-0 h-screen`) | Sidebar que rola com o conteúdo |
| Máximo 7-8 itens visíveis na sidebar | Sidebar com 15+ itens sem agrupamento |
| Badge counter no ícone para notificações | Números grandes expostos (usar "+9") |
| `bg-white` com `border-gray-100` | `bg-gray-50` ou bordas pesadas (`border-gray-200/300`) |
| TopBar sempre sticky com `z-50` | TopBar que rola com o conteúdo |
| PageTransition para navegação principal | Animações em cada interação menor |

---

## 3.10 Loading States

### 3.10.1 Spinner

```html
<!-- Tailwind -->
<div class="flex items-center justify-center p-12">
  <svg class="w-8 h-8 animate-spin text-gray-900" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
</div>

<!-- Vuetify -->
<v-progress-circular indeterminate color="grey-darken-4"></v-progress-circular>
```

### 3.10.2 Skeleton

```html
<!-- Tailwind -->
<div class="animate-pulse space-y-4">
  <div class="h-6 bg-gray-200 rounded w-1/3"></div>
  <div class="space-y-2">
    <div class="h-4 bg-gray-200 rounded"></div>
    <div class="h-4 bg-gray-200 rounded w-5/6"></div>
    <div class="h-4 bg-gray-200 rounded w-4/6"></div>
  </div>
</div>

<!-- Vuetify -->
<v-skeleton-loader type="article"></v-skeleton-loader>
```

### 3.10.3 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'spinner' \| 'skeleton' \| 'shimmer' \| 'progress'` | `'spinner'` | Tipo de indicador de loading |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Tamanho do spinner (16/20/24px) |
| `label` | `string` | — | Texto descritivo ("Carregando candidatos...") |
| `fullPage` | `boolean` | `false` | Overlay de tela inteira |

### 3.10.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Skeleton para conteúdo que tem layout previsível | Spinner genérico para tudo |
| Label descritivo ("Analisando 47 candidatos...") | Label vago ("Carregando...") |
| Spinner inline no botão que disparou a ação | Spinner centralizado sem contexto |
| Desabilitar interações durante loading | Permitir cliques duplos durante processamento |

---

## 3.11 Dropdowns & Menus

```html
<!-- Tailwind -->
<div class="relative">
  <button class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50">
    <span>Opções</span>
    <svg class="w-4 h-4">...</svg>
  </button>
  
  <div class="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50">
    <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Editar</a>
    <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Duplicar</a>
    <div class="border-t border-gray-200 my-1"></div>
    <a href="#" class="block px-4 py-2 text-sm text-red-600 hover:bg-red-50">Deletar</a>
  </div>
</div>

<!-- Vuetify -->
<v-menu>
  <template #activator="{ props }">
    <v-btn v-bind="props">Opções</v-btn>
  </template>
  <v-list>
    <v-list-item @click="handleEdit">Editar</v-list-item>
    <v-list-item @click="handleDuplicate">Duplicar</v-list-item>
    <v-divider></v-divider>
    <v-list-item @click="handleDelete" class="text-red">Deletar</v-list-item>
  </v-list>
</v-menu>
```

### 3.11.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `items` | `MenuItem[]` | `[]` | Itens do menu (label, icon, onClick, disabled, destructive) |
| `trigger` | `ReactNode` | — | Elemento que abre o dropdown |
| `align` | `'start' \| 'end'` | `'end'` | Alinhamento do menu em relação ao trigger |
| `separator` | `boolean` | `false` | Adiciona separador visual entre grupos |

### 3.11.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Ícone + label em cada item | Itens sem ícone (dificulta scanning) |
| Item destrutivo em `text-red-600` com separador acima | Item destrutivo misturado com ações normais |
| Máximo 7 itens por dropdown | Dropdown com 15+ itens (usar modal/page) |
| Fechar ao clicar fora ou selecionar item | Menu que permanece aberto após seleção |

---

## 3.12 Accordions

```html
<!-- Tailwind -->
<div class="border border-gray-200 rounded-md divide-y divide-gray-200">
  <details class="group">
    <summary class="px-4 py-3 text-sm font-semibold text-gray-900 cursor-pointer flex items-center justify-between hover:bg-gray-50">
      Seção 1
      <svg class="w-4 h-4 text-gray-600 transition-transform group-open:rotate-180">...</svg>
    </summary>
    <div class="px-4 py-3 text-sm text-gray-600">
      Conteúdo da seção 1
    </div>
  </details>
</div>

<!-- Vuetify -->
<v-expansion-panels>
  <v-expansion-panel title="Seção 1" text="Conteúdo da seção 1"></v-expansion-panel>
  <v-expansion-panel title="Seção 2" text="Conteúdo da seção 2"></v-expansion-panel>
</v-expansion-panels>
```

### 3.12.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Primeiro item aberto por padrão se for o mais relevante | Todos os itens fechados inicialmente (conteúdo escondido) |
| Ícone de chevron animado (rotate 180°) | Ícone + ou − que muda abruptamente |
| Permitir múltiplos abertos simultaneamente | Fechar outros ao abrir um (accordion exclusivo) |
| Conteúdo com padding interno consistente `p-4` | Conteúdo sem padding que encosta nas bordas |

---

## 3.13 Progress Indicators

```html
<!-- Tailwind -->
<div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
  <div class="bg-gray-900 h-2 rounded-full transition-all duration-300" style="width: 65%"></div>
</div>

<!-- Vuetify -->
<v-progress-linear :model-value="65" color="grey-darken-4"></v-progress-linear>
```

### 3.13.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `bg-gray-900` como cor da barra de progresso | Cores aleatórias por etapa |
| Mostrar porcentagem ou fração ("3 de 7 etapas") | Barra sem indicação numérica |
| Stepper para fluxos sequenciais com etapas nomeadas | Barra para fluxos com etapas não-lineares |
| Animar transição da barra (`transition-all duration-300`) | Mudança abrupta sem animação |

---

## 3.14 Avatars

```html
<!-- Tailwind -->
<div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-sm font-semibold">
  JS
</div>

<!-- Com imagem -->
<img src="..." alt="User" class="w-10 h-10 rounded-full object-cover" />

<!-- Vuetify -->
<v-avatar size="40" color="grey-lighten-2">JS</v-avatar>
<v-avatar size="40" image="..."></v-avatar>
```

### 3.14.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `src` | `string` | — | URL da imagem |
| `fallback` | `string` | — | Iniciais para exibir quando sem imagem |
| `size` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | 24/32/40/48/64px |
| `alt` | `string` | — | Texto alternativo |
| `status` | `'online' \| 'offline' \| 'busy'` | — | Indicador de status (dot colorido) |

### 3.14.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Sempre ter fallback com iniciais (2 letras, uppercase) | Ícone genérico de pessoa como fallback |
| `rounded-full` sempre para avatars | Avatars quadrados ou com border-radius parcial |
| `bg-gray-200 text-gray-600` para fallback | Cores aleatórias para backgrounds de iniciais |
| Tamanhos consistentes conforme contexto (ver seção 1.8) | Tamanhos ad-hoc fora da escala definida |

---

## 3.15 Breadcrumbs

Ver seção 3.9.2.

---

## 3.16 Pagination

```html
<!-- Tailwind -->
<nav class="flex items-center gap-1">
  <button class="p-2 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50">
    <svg class="w-4 h-4">...</svg>
  </button>
  <button class="px-3 py-1 text-sm bg-gray-900 text-white rounded">1</button>
  <button class="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded">2</button>
  <button class="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded">3</button>
  <button class="p-2 text-gray-600 hover:bg-gray-100 rounded">
    <svg class="w-4 h-4">...</svg>
  </button>
</nav>

<!-- Vuetify -->
<v-pagination v-model="page" :length="10" color="grey-darken-4"></v-pagination>
```

### 3.16.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `totalItems` | `number` | `0` | Total de itens para calcular páginas |
| `pageSize` | `10 \| 25 \| 50` | `10` | Itens por página |
| `currentPage` | `number` | `1` | Página atual |
| `onPageChange` | `(page: number) => void` | — | Callback ao trocar página |
| `onPageSizeChange` | `(size: number) => void` | — | Callback ao trocar pageSize |
| `showPageSize` | `boolean` | `true` | Mostra seletor de itens por página |

### 3.16.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Mostrar "1-10 de 247 resultados" | Apenas números de página sem contexto |
| PageSize selector (10/25/50) | Forçar tamanho fixo sem opção de ajuste |
| Truncar com `...` para muitas páginas (1 2 ... 24 25) | Mostrar todos os números de página |
| Font Inter para contadores numéricos | Font Open Sans para números de paginação |

---

## 3.17 Switches & Toggles

```html
<!-- Tailwind -->
<button 
  type="button"
  class="relative w-11 h-6 bg-gray-200 rounded-full transition-colors focus:ring-2 focus:ring-gray-900/20"
  aria-pressed="false"
>
  <span class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></span>
</button>

<!-- Ativo -->
<button 
  type="button"
  class="relative w-11 h-6 bg-gray-900 rounded-full transition-colors"
  aria-pressed="true"
>
  <span class="absolute left-6 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></span>
</button>

<!-- Vuetify -->
<v-switch color="grey-darken-4"></v-switch>
```

### 3.17.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `checked` | `boolean` | `false` | Estado on/off |
| `onChange` | `(checked: boolean) => void` | — | Callback ao alterar |
| `disabled` | `boolean` | `false` | Desabilita interação |
| `label` | `string` | — | Label visível à direita |
| `size` | `'sm' \| 'md'` | `'md'` | Tamanho (16/20px height) |

### 3.17.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Switch para ações on/off imediatas (ativar notificações) | Switch para ações que precisam de "Salvar" |
| Label descritivo à direita ("Receber alertas por email") | Switch sem label ou com label ambíguo |
| `bg-gray-900` quando ativo | Cor accent como estado ativo de switches |
| Sempre ter efeito imediato ao alterar | Agrupar múltiplos switches com submit button |

---

## 3.18 Radio Buttons

```html
<!-- Tailwind -->
<div class="space-y-2">
  <label class="flex items-center gap-2 cursor-pointer">
    <input type="radio" name="plan" value="free" class="w-4 h-4 border-gray-300 text-gray-900 focus:ring-2 focus:ring-gray-900/20"/>
    <span class="text-sm text-gray-800">Gratuito</span>
  </label>
  <label class="flex items-center gap-2 cursor-pointer">
    <input type="radio" name="plan" value="pro" class="w-4 h-4 border-gray-300 text-gray-900 focus:ring-2 focus:ring-gray-900/20"/>
    <span class="text-sm text-gray-800">Professional</span>
  </label>
</div>

<!-- Vuetify -->
<v-radio-group>
  <v-radio label="Gratuito" value="free" color="grey-darken-4"></v-radio>
  <v-radio label="Professional" value="pro" color="grey-darken-4"></v-radio>
</v-radio-group>
```

### 3.18.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Radio para escolha única obrigatória (um de N) | Radio para seleção múltipla (usar checkbox) |
| Listar todas as opções visíveis | Radio dentro de dropdown/hidden |
| Opção padrão pré-selecionada quando houver default lógico | Nenhuma opção selecionada inicialmente sem razão |
| `accent-gray-900` para o indicador preenchido | Cores variadas para diferentes grupos de radio |

---

## 3.19 Checkboxes

```html
<!-- Tailwind -->
<label class="flex items-center gap-2 cursor-pointer">
  <input 
    type="checkbox" 
    class="w-4 h-4 border-gray-300 rounded text-gray-900 focus:ring-2 focus:ring-gray-900/20"
  />
  <span class="text-sm text-gray-800">Aceito os termos</span>
</label>

<!-- Vuetify -->
<v-checkbox label="Aceito os termos" color="grey-darken-4"></v-checkbox>
```

### 3.19.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Checkbox para seleção múltipla (0 a N de M) | Checkbox para escolha exclusiva (usar radio) |
| Indeterminate state quando parcialmente selecionado | Checkbox que alterna true/false em listas parciais |
| Label clicável (clicar no texto marca o checkbox) | Apenas a caixa ser clicável |
| `accent-gray-900` para checked, `border-gray-300` para unchecked | Cores de borda inconsistentes |

---

## 3.20 Date Pickers

```html
<!-- Tailwind -->
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Data</label>
  <input 
    type="date"
    class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-gray-900/20"
  />
</div>

<!-- Vuetify -->
<v-text-field
  label="Data"
  type="date"
  variant="outlined"
  density="comfortable"
></v-text-field>
```

### 3.20.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Formato PT-BR: "24 fev 2026" (ver seção 2.4) | Formato US "02/24/2026" |
| Ícone Calendar à esquerda do input | Ícone à direita ou sem ícone |
| Limitar range com `min`/`max` conforme contexto | Picker aberto sem restrições de data |
| Font Inter para a data selecionada exibida | Open Sans para números de data |

---

## 3.21 File Upload

```html
<!-- Tailwind -->
<div class="border-2 border-dashed border-gray-300 rounded-md p-6 text-center hover:border-gray-400 transition-colors">
  <input type="file" id="file-upload" class="hidden" />
  <label for="file-upload" class="cursor-pointer">
    <svg class="w-12 h-12 text-gray-400 mx-auto mb-2">...</svg>
    <p class="text-sm text-gray-600">
      <span class="text-gray-900 font-semibold">Clique para enviar</span> ou arraste aqui
    </p>
    <p class="text-xs text-gray-500 mt-1">PNG, JPG ou PDF até 10MB</p>
  </label>
</div>

<!-- Vuetify -->
<v-file-input
  label="Anexo"
  variant="outlined"
  prepend-icon="mdi-paperclip"
  accept="image/*,application/pdf"
></v-file-input>
```

### 3.21.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Área de drag/drop com `border-dashed border-gray-300` | Botão de upload sem área de drag |
| Mostrar tipos aceitos e limite: "PNG, JPG ou PDF até 10MB" | Sem indicação de restrições |
| Preview do arquivo após upload (thumbnail para imagens) | Apenas nome do arquivo sem preview |
| Feedback visual durante upload (progress bar) | Upload silencioso sem indicação de progresso |
| Validar tipo/tamanho antes de enviar | Tentar upload e falhar no servidor |

---

## 3.22 Sliders

```html
<!-- Tailwind -->
<input 
  type="range" 
  min="0" 
  max="100" 
  value="50"
  class="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-gray-900"
/>

<!-- Vuetify -->
<v-slider :min="0" :max="100" color="grey-darken-4" thumb-label></v-slider>
```

### 3.22.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Thumb label para mostrar valor atual | Slider sem indicação numérica |
| `accent-gray-900` para trilha preenchida | Cores accent para trilha de slider |
| Usar para ranges (salário, experiência) | Usar para valores precisos (preferir input numérico) |
| Step definido conforme contexto (ex: step 1000 para salário) | Step de 1 para ranges grandes (0-100000) |

---

## 3.23 Tabs

```html
<!-- Tailwind -->
<div class="border-b border-gray-200">
  <nav class="flex gap-4">
    <button class="px-4 py-2 text-sm font-semibold text-gray-900 border-b-2 border-gray-900">
      Detalhes
    </button>
    <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent">
      Histórico
    </button>
    <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent">
      Documentos
    </button>
  </nav>
</div>

<!-- Vuetify -->
<v-tabs v-model="tab" color="grey-darken-4">
  <v-tab value="details">Detalhes</v-tab>
  <v-tab value="history">Histórico</v-tab>
  <v-tab value="documents">Documentos</v-tab>
</v-tabs>
```

### 3.23.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `tabs` | `Tab[]` | `[]` | Array de tabs (id, label, icon?, badge?) |
| `activeTab` | `string` | — | ID da tab ativa |
| `onChange` | `(tabId: string) => void` | — | Callback ao trocar tab |
| `variant` | `'underline' \| 'pill'` | `'underline'` | Estilo visual |

### 3.23.3 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Tab ativa com `border-b-2 border-gray-900 font-semibold` | Tab ativa com background colorido |
| Title Case para labels de tab | UPPER CASE ou sentence case em tabs |
| Máximo 5-6 tabs visíveis (scroll horizontal se mais) | 10+ tabs sem scroll, quebrando layout |
| Badge counter na tab quando houver notificações | Counter diretamente no label da tab |
| Usar `color="grey-darken-4"` no Vuetify | Cores accent como indicator de tab ativa |

---

## 3.24 Dividers

```html
<!-- Horizontal -->
<hr class="border-t border-gray-200" />

<!-- Vertical -->
<div class="w-px h-8 bg-gray-200"></div>

<!-- Com texto -->
<div class="flex items-center gap-4">
  <hr class="flex-1 border-t border-gray-200" />
  <span class="text-xs text-gray-600 font-semibold">OU</span>
  <hr class="flex-1 border-t border-gray-200" />
</div>

<!-- Vuetify -->
<v-divider></v-divider>
<v-divider vertical></v-divider>
```

### 3.24.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| `border-gray-200` para cor de dividers | Dividers pretos ou com cores fortes |
| Divider "com texto" para separar seções lógicas ("OU") | Texto longo dentro de dividers |
| Vertical dividers para separar ações inline | Vertical dividers para separar seções grandes |
| Consistência: horizontal para seções, vertical para inline | Misturar padrões no mesmo contexto |

---

## 3.25 Skeleton Loaders

```html
<!-- Card skeleton -->
<div class="bg-white rounded-md border border-gray-200 p-6 animate-pulse">
  <div class="flex items-center gap-3 mb-4">
    <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 bg-gray-200 rounded w-1/3"></div>
      <div class="h-3 bg-gray-200 rounded w-1/4"></div>
    </div>
  </div>
  <div class="space-y-2">
    <div class="h-3 bg-gray-200 rounded"></div>
    <div class="h-3 bg-gray-200 rounded w-5/6"></div>
  </div>
</div>

<!-- Vuetify -->
<v-skeleton-loader type="card"></v-skeleton-loader>
<v-skeleton-loader type="table"></v-skeleton-loader>
```

### 3.25.2 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Skeleton que replica o layout final (card, table, list) | Skeleton genérico que não corresponde ao conteúdo |
| `animate-pulse` com `bg-gray-200` | Animações elaboradas ou cores vibrantes em skeleton |
| Skeleton para carregamentos >300ms | Skeleton para loads instantâneos (<100ms) |
| Transição suave skeleton → conteúdo (`fade-in`) | Substituição abrupta sem transição |

---

## 3.26 Feedback Buttons (Like/Dislike)

Botões de feedback binário para candidatos em resultados de busca do funil de talentos.
Permite ao recrutador avaliar candidatos com thumbs up (like) ou thumbs down (dislike).

### 3.26.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Ícones** | `ThumbsUp`, `ThumbsDown` (lucide-react) |
| **Tamanho ícone** | `w-4 h-4` (16px) |
| **Tamanho botão** | `h-8 w-8` (32px) - botão ícone quadrado |
| **Border radius** | `rounded-md` (6px) |
| **Espaçamento entre botões** | `gap-1` (4px) |
| **Posição no card** | Inline à direita na linha de ações do candidato |
| **Comportamento** | Toggle - apenas um ativo por vez (like OU dislike) |
| **Persistência** | API backend com optimistic update no frontend |

### 3.26.2 Estados

| Estado | ThumbsUp | ThumbsDown |
|--------|----------|------------|
| **Neutro** | `text-gray-400 hover:text-gray-600 hover:bg-gray-100` | `text-gray-400 hover:text-gray-600 hover:bg-gray-100` |
| **Like ativo** | `text-emerald-600 bg-emerald-50` | `text-gray-300` (dimmed) |
| **Dislike ativo** | `text-gray-300` (dimmed) | `text-red-500 bg-red-50` |
| **Loading** | `opacity-50 pointer-events-none` | `opacity-50 pointer-events-none` |
| **Disabled** | `opacity-30 cursor-not-allowed` | `opacity-30 cursor-not-allowed` |

### 3.26.3 Implementação

```tsx
{/* React + Tailwind (Protótipo Replit) */}
import { ThumbsUp, ThumbsDown } from "lucide-react"

<div className="flex items-center gap-1">
  <button
    onClick={() => onFeedback('like')}
    className={cn(
      "h-8 w-8 flex items-center justify-center rounded-md transition-colors",
      feedback === 'like'
        ? "text-emerald-600 bg-emerald-50"
        : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
    )}
    title="Candidato relevante"
  >
    <ThumbsUp className="w-4 h-4" />
  </button>
  <button
    onClick={() => onFeedback('dislike')}
    className={cn(
      "h-8 w-8 flex items-center justify-center rounded-md transition-colors",
      feedback === 'dislike'
        ? "text-red-500 bg-red-50"
        : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
    )}
    title="Candidato não relevante"
  >
    <ThumbsDown className="w-4 h-4" />
  </button>
</div>
```

```html
<!-- Vuetify (Produção) -->
<div class="d-flex align-center ga-1">
  <v-btn
    icon variant="text" size="small"
    :color="feedback === 'like' ? 'success' : 'grey-lighten-1'"
    @click="onFeedback('like')"
  >
    <v-icon size="16">mdi-thumb-up</v-icon>
    <v-tooltip activator="parent">Candidato relevante</v-tooltip>
  </v-btn>
  <v-btn
    icon variant="text" size="small"
    :color="feedback === 'dislike' ? 'error' : 'grey-lighten-1'"
    @click="onFeedback('dislike')"
  >
    <v-icon size="16">mdi-thumb-down</v-icon>
    <v-tooltip activator="parent">Candidato não relevante</v-tooltip>
  </v-btn>
</div>
```

### 3.26.4 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/search/SearchFeedbackButtons.tsx` | Componente reutilizável (React) |
| `src/components/chat/message-feedback.tsx` | Padrão similar para respostas da LIA |
| `src/components/calibration/lia-feedback-widget.tsx` | Padrão similar para calibração |

### 3.26.5 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Toggle exclusivo (like OU dislike, nunca ambos) | Permitir like e dislike simultâneos |
| Optimistic update com rollback em caso de erro | Esperar resposta da API para atualizar UI |
| Dimmed (`text-gray-300`) no botão não selecionado | Esconder o botão oposto ao selecionado |
| `aria-label` descritivo em cada botão | Botões sem acessibilidade |

---

## 3.27 Sort Dropdown (Ordenação)

Dropdown para ordenar resultados de busca no funil de talentos. Posicionado no header da área de resultados.

### 3.27.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Componente** | `Select` (shadcn/ui) com `ArrowUpDown` (lucide-react) |
| **Largura** | `w-[180px]` |
| **Altura** | `h-8` (32px) |
| **Font** | Open Sans, `text-sm` |
| **Posição** | Header de resultados, alinhado à direita |
| **Cor do ícone** | `text-gray-500` |

### 3.27.2 Opções de Ordenação

| Valor | Label | Comportamento |
|-------|-------|---------------|
| `relevance` | Relevância | Ordem original do ranking (padrão) |
| `score_desc` | Maior Score | Score descendente |
| `score_asc` | Menor Score | Score ascendente |
| `name_asc` | Nome (A-Z) | Alfabético ascendente |
| `name_desc` | Nome (Z-A) | Alfabético descendente |
| `experience_desc` | Maior Experiência | Anos de experiência descendente |

### 3.27.3 Implementação

```tsx
{/* React + Tailwind (Protótipo Replit) */}
import { ArrowUpDown } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

<Select value={sortBy} onValueChange={setSortBy}>
  <SelectTrigger className="w-[180px] h-8 text-sm">
    <ArrowUpDown className="w-3.5 h-3.5 mr-1.5 text-gray-500" />
    <SelectValue placeholder="Ordenar por..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="relevance">Relevância</SelectItem>
    <SelectItem value="score_desc">Maior Score</SelectItem>
    <SelectItem value="score_asc">Menor Score</SelectItem>
    <SelectItem value="name_asc">Nome (A-Z)</SelectItem>
    <SelectItem value="name_desc">Nome (Z-A)</SelectItem>
    <SelectItem value="experience_desc">Maior Experiência</SelectItem>
  </SelectContent>
</Select>
```

```html
<!-- Vuetify (Produção) -->
<v-select
  v-model="sortBy"
  :items="sortOptions"
  label="Ordenar por"
  variant="outlined"
  density="compact"
  prepend-inner-icon="mdi-sort"
  style="max-width: 200px"
/>
```

### 3.27.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Ícone `ArrowUpDown` antes do label | Dropdown sem ícone indicativo |
| Largura fixa `w-[180px]` para consistência | Largura variável que muda com o conteúdo |
| Default "Relevância" como primeira opção | Default "Nome (A-Z)" ou outro critério não-relevante |
| Posição no header de resultados, alinhado à direita | Dentro do conteúdo dos resultados |

---

## 3.28 Load More Button (Carregar Mais)

Botão para carregar mais resultados de busca sob demanda (paginação incremental de 10 em 10).

### 3.28.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Variante** | `outline` (shadcn/ui Button) |
| **Largura** | `w-full` (100% do container de resultados) |
| **Altura** | `h-10` (40px) |
| **Font** | Open Sans, `text-sm font-medium` |
| **Ícone** | `ChevronDown` (lucide-react), `w-4 h-4` |
| **Posição** | Após último card de candidato, antes do footer |
| **Counter** | Exibe total carregado vs total disponível |

### 3.28.2 Estados

| Estado | Aparência |
|--------|-----------|
| **Disponível** | `border-gray-200 text-gray-700 hover:bg-gray-50` |
| **Carregando** | `opacity-70` + `Loader2 animate-spin` substituindo ícone |
| **Todos carregados** | Botão oculto, exibe texto "Todos os X candidatos carregados" em `text-gray-500 text-sm` |

### 3.28.3 Implementação

```tsx
{/* React + Tailwind (Protótipo Replit) */}
import { ChevronDown, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

{hasMore && (
  <div className="flex flex-col items-center gap-2 py-4">
    <Button
      variant="outline"
      className="w-full max-w-md h-10 gap-2 text-sm font-medium"
      onClick={onLoadMore}
      disabled={isLoadingMore}
    >
      {isLoadingMore ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <ChevronDown className="w-4 h-4" />
      )}
      {isLoadingMore ? 'Carregando...' : 'Carregar mais 10 candidatos'}
    </Button>
    <span className="text-xs text-gray-500">
      {loadedCount} de {totalCount} candidatos
    </span>
  </div>
)}

{!hasMore && loadedCount > 0 && (
  <p className="text-center text-sm text-gray-500 py-4">
    Todos os {loadedCount} candidatos carregados
  </p>
)}
```

```html
<!-- Vuetify (Produção) -->
<div v-if="hasMore" class="d-flex flex-column align-center ga-2 py-4">
  <v-btn
    variant="outlined"
    block
    :loading="isLoadingMore"
    @click="loadMore"
    prepend-icon="mdi-chevron-down"
    class="text-body-2"
    style="max-width: 400px"
  >
    Carregar mais 10 candidatos
  </v-btn>
  <span class="text-caption text-grey">
    {{ loadedCount }} de {{ totalCount }} candidatos
  </span>
</div>
```

### 3.28.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Mostrar "X de Y candidatos" como contexto | Botão "Carregar mais" sem indicação de progresso |
| Spinner inline no botão durante carregamento | Substituir botão inteiro por spinner |
| Desabilitar botão se carregando ou sem mais itens | Permitir cliques múltiplos durante loading |
| Progress bar abaixo do botão (candidatos carregados/total) | Sem indicação visual de quanto falta |

---

## 3.29 Qualification Badge (Classificação de Vaga)

Badge indicador do nível de qualificação da vaga, usado no Funil de Talentos para ajustar precisão de busca.
Classificação automática via LLM com override manual pelo recrutador.

### 3.29.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Componente** | `QualificationBadge` (React) |
| **Padrão base** | Badge WeDo (seção 3.6.3) |
| **Border radius** | `rounded-full` (pill) |
| **Font** | `text-[10px] font-medium` |
| **Ícones** | `Crown`, `Briefcase`, `HardHat` (lucide-react) |
| **Override** | Dropdown (seção 3.11) com 3 opções |
| **Tooltip** | Padrão DS v4.1 (seção 3.7) - mostra confiança, razão e impacto |

### 3.29.2 Níveis de Qualificação

| Nível | Cor | Background | Text | Ícone | Uso |
|-------|-----|------------|------|-------|-----|
| **Alta** | Purple `#9860D1` | `rgba(152,96,209,0.1)` | `#9860D1` | `Crown` | Executivas, C-Level, Especialistas |
| **Média** | Orange `#D19960` | `rgba(209,153,96,0.1)` | `#D19960` | `Briefcase` | Pleno, Sênior, Coordenadores |
| **Baixa** | Gray monocromático | `bg-gray-100` | `text-gray-700` | `HardHat` | Júnior, Estágio, Operacional |

### 3.29.3 Estados

| Estado | Aparência |
|--------|-----------|
| **Classificado** | Badge com cor e ícone do nível |
| **Override manual** | Badge + asterisco `*` indicador |
| **Classificando** | `Loader2 animate-spin` + "Classificando..." em gray-500 |
| **Não classificado** | Botão dashed `border-dashed border-gray-300` + ícone Brain + "Classificar" |

### 3.29.4 Implementação

```tsx
{/* React + Tailwind (Protótipo Replit) */}
import { Crown, Briefcase, HardHat } from "lucide-react"

{/* Alta Qualificação */}
<span
  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium text-[#9860D1] border border-[#9860D1]/20 dark:text-[#9860D1] dark:border-[#9860D1]/30 dark:bg-[#9860D1]/20"
  style={{ background: "rgba(152,96,209,0.1)" }}
>
  <Crown className="w-3 h-3" />
  Alta
</span>

{/* Média Qualificação */}
<span
  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium text-[#D19960] border border-[#D19960]/20 dark:text-[#D19960] dark:border-[#D19960]/30 dark:bg-[#D19960]/20"
  style={{ background: "rgba(209,153,96,0.1)" }}
>
  <Briefcase className="w-3 h-3" />
  Média
</span>

{/* Baixa Qualificação */}
<span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium text-gray-700 border border-gray-200 bg-gray-100 dark:text-gray-300 dark:border-gray-600 dark:bg-gray-800">
  <HardHat className="w-3 h-3" />
  Baixa
</span>
```

```html
<!-- Vuetify (Produção) -->
<v-chip v-if="level === 'alta'" size="small" color="purple" variant="tonal" prepend-icon="mdi-crown">
  Alta
</v-chip>
<v-chip v-else-if="level === 'media'" size="small" color="orange" variant="tonal" prepend-icon="mdi-briefcase">
  Média
</v-chip>
<v-chip v-else size="small" color="grey" variant="tonal" prepend-icon="mdi-hard-hat">
  Baixa
</v-chip>
```

### 3.29.5 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/search/QualificationBadge.tsx` | Componente reutilizável (React) |
| `src/components/pages/candidates-page.tsx` | Integração no header do Funil de Talentos |

### 3.29.6 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Tooltip com descrição completa do nível ao hover | Badge sem explicação do que significa cada nível |
| Cor e ícone consistentes por nível (conforme 3.29.2) | Cores que mudam entre contextos |
| Permitir override manual pelo recrutador | Apenas classificação automática sem ajuste |
| Posição no header da vaga, ao lado do título | Badge escondido em seção de detalhes |

---

## 3.30 Chat Message (LiaMessage) `[Draft]`

Componente base para mensagens no chat da LIA. Suporta mensagens do usuário (recrutador) e da assistente (LIA), com formatação markdown, anexos e ações inline.

### 3.30.1 Anatomia

```
┌─────────────────────────────────────────────────┐
│  ┌──────┐                                       │
│  │Avatar│  Nome · Timestamp                      │
│  └──────┘                                       │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ Corpo da mensagem (markdown rendered)    │    │
│  │                                          │    │
│  │ **Dados em negrito**, listas, tabelas    │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 👍 Útil  │ │ 👎       │ │ 📋 Copiar│        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
```

### 3.30.2 Variantes

| Variante | Remetente | Background | Alinhamento | Avatar |
|----------|-----------|------------|-------------|--------|
| **LIA Message** | LIA (assistente) | `bg-gray-50` | Esquerda | Brain icon cyan |
| **User Message** | Recrutador | `bg-white` border `border-gray-200` | Direita | Iniciais do usuário |
| **System Message** | Sistema | `bg-gray-100` centralizado | Centro | Nenhum |
| **Error Message** | Sistema | `bg-red-50` border `border-red-200` | Esquerda | ⚠️ icon |

### 3.30.3 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'lia' \| 'user' \| 'system' \| 'error'` | `'lia'` | Tipo de mensagem |
| `content` | `string` | — | Conteúdo markdown da mensagem |
| `timestamp` | `Date \| string` | — | Data/hora do envio |
| `senderName` | `string` | `'LIA'` | Nome do remetente |
| `senderAvatar` | `string \| ReactNode` | — | URL da imagem ou componente de avatar |
| `actions` | `MessageAction[]` | `[]` | Ações de feedback (like/dislike/copy) |
| `attachments` | `Attachment[]` | `[]` | Anexos (arquivos, imagens) |
| `isStreaming` | `boolean` | `false` | Se a mensagem está sendo gerada em tempo real |
| `className` | `string` | — | Classes CSS adicionais |

### 3.30.4 Implementação

**React + Tailwind:**

```tsx
<div className={cn(
  "flex gap-3 px-4 py-3",
  variant === 'user' && "flex-row-reverse",
  variant === 'system' && "justify-center"
)}>
  {/* Avatar */}
  {variant !== 'system' && (
    <div className="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden">
      {variant === 'lia' ? (
        <div className="w-full h-full bg-gray-100 flex items-center justify-center">
          <Brain className="w-5 h-5 text-[#60BED1]" />
        </div>
      ) : (
        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
          <span className="text-xs font-semibold text-gray-600">{initials}</span>
        </div>
      )}
    </div>
  )}

  {/* Message Body */}
  <div className={cn(
    "max-w-[80%] rounded-md px-4 py-3",
    variant === 'lia' && "bg-gray-50",
    variant === 'user' && "bg-white border border-gray-200",
    variant === 'system' && "bg-gray-100 text-center text-sm text-gray-500",
    variant === 'error' && "bg-red-50 border border-red-200"
  )}>
    {/* Header */}
    <div className="flex items-center gap-2 mb-1">
      <span className="text-sm font-semibold text-gray-900">{senderName}</span>
      <span className="text-xs text-gray-400">{formattedTime}</span>
    </div>

    {/* Content (markdown rendered) */}
    <div className="text-sm text-gray-800 prose prose-sm max-w-none">
      <MarkdownRenderer content={content} />
    </div>

    {/* Actions */}
    {actions.length > 0 && (
      <div className="flex items-center gap-1 mt-2 pt-2 border-t border-gray-100">
        {actions.map(action => (
          <button
            key={action.id}
            className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label={action.label}
          >
            <action.icon className="w-4 h-4" />
          </button>
        ))}
      </div>
    )}
  </div>
</div>
```

**Vue + Vuetify:**

```vue
<template>
  <div :class="['d-flex', 'ga-3', 'px-4', 'py-3', variantClasses]">
    <v-avatar v-if="variant !== 'system'" size="32" :color="avatarColor">
      <v-icon v-if="variant === 'lia'" color="#60BED1" size="20">mdi-brain</v-icon>
      <span v-else class="text-caption font-weight-bold">{{ initials }}</span>
    </v-avatar>

    <div :class="['rounded', 'px-4', 'py-3', messageClasses]" style="max-width: 80%">
      <div class="d-flex align-center ga-2 mb-1">
        <span class="text-body-2 font-weight-bold text-grey-darken-4">{{ senderName }}</span>
        <span class="text-caption text-grey-lighten-1">{{ formattedTime }}</span>
      </div>
      <div class="text-body-2 text-grey-darken-3" v-html="renderedContent" />
    </div>
  </div>
</template>
```

### 3.30.5 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Renderizar markdown completo (negrito, listas, tabelas) | Exibir markdown como texto puro |
| Mostrar timestamp relativo ("há 2 min") com tooltip absoluto | Mostrar apenas timestamp absoluto |
| Limitar largura a 80% do container | Permitir que mensagens ocupem 100% |
| Animar entrada com `fade-in` sutil (150ms) | Usar animações elaboradas na entrada |
| Agrupar mensagens consecutivas do mesmo remetente | Repetir avatar em cada mensagem sequencial |

---

## 3.31 Chat Input (LiaChatInput) `[Draft]`

Input principal do chat onde o recrutador digita mensagens para a LIA. Suporta texto multilinha, envio por Enter, e indicadores de contexto.

### 3.31.1 Anatomia

```
┌─────────────────────────────────────────────────┐
│ ┌─────────────┐                                 │
│ │ 📎 Contexto │  "Criando: Eng. de Dados Sr"    │
│ └─────────────┘                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Digite sua mensagem para a LIA...          ⬆️  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 3.31.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `placeholder` | `string` | `'Digite sua mensagem para a LIA...'` | Texto placeholder |
| `onSubmit` | `(message: string) => void` | — | Callback ao enviar mensagem |
| `disabled` | `boolean` | `false` | Desabilita input (ex: durante streaming) |
| `isLoading` | `boolean` | `false` | Mostra indicador de que LIA está processando |
| `contextLabel` | `string` | — | Label de contexto atual (ex: "Criando: Eng. de Dados") |
| `contextIcon` | `ReactNode` | — | Ícone do contexto ativo |
| `maxLength` | `number` | `2000` | Limite de caracteres |
| `autoFocus` | `boolean` | `true` | Auto-focus ao montar componente |
| `onAttach` | `() => void` | — | Callback para anexar arquivo |

### 3.31.3 Comportamento

| Interação | Comportamento |
|-----------|--------------|
| **Enter** | Envia mensagem (single line) |
| **Shift+Enter** | Nova linha (multilinha) |
| **Ctrl+Enter** | Envia mensagem (sempre, mesmo multilinha) |
| **Durante streaming** | Input desabilitado, mostra "LIA está respondendo..." |
| **Input vazio** | Botão enviar desabilitado (gray-300) |
| **Input preenchido** | Botão enviar ativo (gray-900) |
| **Contexto ativo** | Badge acima do input mostra contexto atual |

### 3.31.4 Implementação

**React + Tailwind:**

```tsx
<div className="border-t border-gray-200 bg-white">
  {/* Context Bar */}
  {contextLabel && (
    <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-100">
      {contextIcon}
      <span className="text-xs text-gray-500 font-medium">{contextLabel}</span>
    </div>
  )}

  {/* Input Area */}
  <div className="flex items-end gap-2 px-4 py-3">
    <textarea
      ref={inputRef}
      value={message}
      onChange={(e) => setMessage(e.target.value)}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      disabled={disabled || isLoading}
      rows={1}
      className={cn(
        "flex-1 resize-none bg-transparent text-sm text-gray-800",
        "placeholder:text-gray-400 focus:outline-none",
        "max-h-32 overflow-y-auto",
        "font-['Open_Sans']"
      )}
    />
    <button
      onClick={handleSubmit}
      disabled={!message.trim() || disabled || isLoading}
      className={cn(
        "flex-shrink-0 w-8 h-8 rounded flex items-center justify-center",
        "transition-colors duration-150",
        message.trim() && !disabled
          ? "bg-gray-900 text-white hover:bg-gray-800"
          : "bg-gray-100 text-gray-300 cursor-not-allowed"
      )}
      aria-label="Enviar mensagem"
    >
      <ArrowUp className="w-4 h-4" />
    </button>
  </div>
</div>
```

---

## 3.32 Chat Thinking (LiaThinking) `[Draft]`

Indicador visual de que a LIA está processando/pensando antes de responder. Transmite confiança de que a ação está em andamento.

### 3.32.1 Variantes

| Variante | Visual | Duração Típica | Uso |
|----------|--------|----------------|-----|
| **Dots** (padrão) | Três pontos pulsantes | < 5s | Respostas rápidas |
| **Processing** | Ícone brain + texto rotativo | 5-30s | Análise de candidatos, scoring |
| **Progress** | Barra de progresso com etapas | > 30s | Processamento em lote |

### 3.32.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'dots' \| 'processing' \| 'progress'` | `'dots'` | Tipo de indicador |
| `message` | `string` | `'LIA está pensando...'` | Texto descritivo |
| `progress` | `number` | — | Progresso 0-100 (para variant `progress`) |
| `steps` | `string[]` | — | Etapas do processamento (para variant `progress`) |
| `currentStep` | `number` | — | Etapa atual (0-indexed) |

### 3.32.3 Implementação

**React + Tailwind:**

```tsx
{/* Variant: Dots */}
<div className="flex items-center gap-3 px-4 py-3">
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
    <Brain className="w-5 h-5 text-[#60BED1]" />
  </div>
  <div className="flex items-center gap-1">
    <div className="flex gap-1">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-gray-300 animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  </div>
</div>

{/* Variant: Processing */}
<div className="flex items-center gap-3 px-4 py-3">
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
    <Brain className="w-5 h-5 text-[#60BED1] animate-pulse" />
  </div>
  <div className="flex flex-col">
    <span className="text-sm text-gray-600">{message}</span>
    <span className="text-xs text-gray-400 mt-0.5">{elapsedTime}</span>
  </div>
</div>

{/* Variant: Progress */}
<div className="flex items-start gap-3 px-4 py-3">
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
    <Brain className="w-5 h-5 text-[#60BED1]" />
  </div>
  <div className="flex-1 max-w-sm">
    <span className="text-sm text-gray-600">{message}</span>
    <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
      <div
        className="bg-[#60BED1] h-1.5 rounded-full transition-all duration-300"
        style={{ width: `${progress}%` }}
      />
    </div>
    <div className="flex flex-col gap-1 mt-2">
      {steps.map((step, i) => (
        <div key={i} className={cn(
          "text-xs flex items-center gap-2",
          i < currentStep ? "text-gray-400" : i === currentStep ? "text-gray-700 font-medium" : "text-gray-300"
        )}>
          {i < currentStep ? <Check className="w-3 h-3 text-green-500" /> : i === currentStep ? <Loader className="w-3 h-3 animate-spin" /> : <Circle className="w-3 h-3" />}
          {step}
        </div>
      ))}
    </div>
  </div>
</div>
```

### 3.32.4 Motion

| Elemento | Animação | Duração | Easing |
|----------|----------|---------|--------|
| Dots bounce | `translateY(-4px)` | 600ms loop | ease-in-out |
| Brain pulse | opacity 0.5→1→0.5 | 1.5s loop | ease-in-out |
| Progress bar | width transition | 300ms | ease-out |
| Step check-in | scale 0→1 + fade | 200ms | spring |

---

## 3.33 Chat Suggestion Cards `[Draft]`

Cards de sugestão rápida exibidos na **zona do input** (abaixo ou acima do prompt), nunca dentro do corpo das mensagens. Funcionam como atalhos — o recrutador pode clicar OU digitar a resposta equivalente. Ao clicar, o texto da sugestão é enviado como mensagem do recrutador no chat.

> **Posicionamento:** As sugestões pertencem à zona do input (`PromptSuggestionsDock`, `PromptSuggestionsPopover`, `QuickActionChips`), não à área de mensagens. Isso mantém o princípio conversation-first: a LIA pergunta, o recrutador responde — botões são atalhos, nunca a interface principal.

### 3.33.1 Anatomia

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 🔍               │  │ 📝               │  │ 📊               │
│ Buscar candidatos│  │ Criar nova vaga  │  │ Ver pipeline     │
│ no banco         │  │                  │  │                  │
│                  │  │                  │  │                  │
│ "Buscar talentos │  │ "Vou criar uma   │  │ "Mostrar o       │
│  para esta vaga" │  │  nova posição"   │  │  pipeline atual" │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### 3.33.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `suggestions` | `Suggestion[]` | — | Lista de sugestões |
| `onSelect` | `(suggestion: Suggestion) => void` | — | Callback ao selecionar |
| `layout` | `'horizontal' \| 'vertical'` | `'horizontal'` | Disposição dos cards |
| `maxVisible` | `number` | `3` | Máximo de cards visíveis |

**Tipo `Suggestion`:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `id` | `string` | Identificador único |
| `icon` | `ReactNode` | Ícone do card |
| `title` | `string` | Título curto (2-4 palavras) |
| `description` | `string` | Texto que será enviado ao chat |

### 3.33.3 Implementação

**React + Tailwind:**

```tsx
<div className="flex gap-2 px-4 py-2 overflow-x-auto">
  {suggestions.slice(0, maxVisible).map(suggestion => (
    <button
      key={suggestion.id}
      onClick={() => onSelect(suggestion)}
      className={cn(
        "flex-shrink-0 flex flex-col gap-2 p-3 rounded-md",
        "border border-gray-200 bg-white",
        "hover:border-gray-300 hover:bg-gray-50",
        "transition-all duration-150",
        "text-left max-w-[200px]",
        "focus:outline-none focus:ring-2 focus:ring-gray-900/20"
      )}
    >
      <div className="text-gray-600">{suggestion.icon}</div>
      <span className="text-sm font-medium text-gray-900">{suggestion.title}</span>
      <span className="text-xs text-gray-500 line-clamp-2">{suggestion.description}</span>
    </button>
  ))}
</div>
```

### 3.33.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Máximo 3-4 sugestões por vez | Sobrecarregar com 6+ opções |
| Texto curto e direto (2-4 palavras título) | Títulos longos que quebram layout |
| Desaparecer após seleção ou resposta do usuário | Manter sugestões antigas visíveis |
| Enviar `description` como mensagem do usuário no chat | Executar ação diretamente sem contexto no chat |
| Sugestões contextuais ao momento do fluxo | Sugestões genéricas repetitivas |

---

## 3.34 Pipeline Kanban Card `[Stable]`

Card que representa um candidato dentro de uma coluna do Pipeline/Kanban. Arrastável entre etapas. Exibe informações resumidas do candidato com indicadores inteligentes baseados em score WSI e tempo de permanência.

### 3.34.1 Anatomia

```
┌────────────────────────────────────────┐
│ ⠿  ┌──┐  Ana Silva              84    │  ← grip handle (hover) + avatar + nome + score LIA
│    │AS│  Product Manager               │  ← cargo atual (truncate)
│    └──┘  Empresa XYZ                   │  ← empresa atual (truncate)
│                                         │
│  ┌───────────┐                         │  ← substatus badge (outline, opcional)
│  │ Em análise │                         │
│  └───────────┘                         │
│                                         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌────┐    │  ← skills (max 3 + "+N" counter)
│  │Python│ │React │ │AWS   │ │+2  │    │
│  └──────┘ └──────┘ └──────┘ └────┘    │
│                                         │
│  ─────────────────────────────────────  │  ← border-t separator
│  ★ 💬 🕐 📈 ⚠️                24 fev  │  ← indicadores + data adição
└────────────────────────────────────────┘
```

### 3.34.2 Indicadores Inteligentes (Footer)

| Ícone | Condição | Cor | Tooltip |
|-------|----------|-----|---------|
| ★ `Star` | `tags.includes('favorite')` | `text-amber-500 fill-amber-500` | — |
| 💬 `MessageSquare` | `notes` existe | `text-gray-400` | — |
| 🕐 `Clock` | `days_in_stage > 7` (stale) | `text-amber-500` | "Parado há X dias — considere avançar ou dar retorno" |
| 📈 `TrendingUp` | `lia_score >= 80` | `text-emerald-500` | "Score WSI alto (X) — considere priorizar" |
| ⚠️ `AlertTriangle` | `lia_score < 40 && lia_score > 0` | `text-red-500` | "Score WSI baixo (X) — avaliar permanência" |

### 3.34.3 Cores do Score

| Range | Classe | Significado |
|-------|--------|-------------|
| `≥ 80` | `text-emerald-600` (dark: `emerald-400`) | Alto — candidato forte |
| `≥ 60` | `text-amber-600` (dark: `amber-400`) | Médio — precisa avaliação |
| `< 40` | `text-red-600` (dark: `red-400`) | Baixo — atenção necessária |
| sem score | `text-gray-400` (dark: `gray-500`) | Não avaliado |

### 3.34.4 Props API

**KanbanCardProps:**

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `candidate` | `KanbanCandidate` | — | Dados do candidato |
| `index` | `number` | — | Posição na lista (para drag & drop) |
| `onClick` | `() => void` | — | Callback ao clicar no card |
| `isDragDisabled` | `boolean` | `false` | Desabilita arrasto |

**KanbanCandidate:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `id` | `string` | ID único |
| `name` | `string` | Nome completo |
| `email` | `string` | Email |
| `avatar_url` | `string?` | URL da foto |
| `current_title` | `string?` | Cargo atual |
| `current_company` | `string?` | Empresa atual |
| `lia_score` | `number?` | Score WSI (0-100) |
| `skills` | `string[]?` | Skills técnicas |
| `substatus` | `string?` | Sub-status na etapa |
| `notes` | `string?` | Notas do recrutador |
| `tags` | `string[]?` | Tags (ex: "favorite") |
| `days_in_stage` | `number?` | Dias na etapa atual |
| `addedAt` | `string` | Data de adição |

**KanbanColumn (sub-componente):**

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `stage` | `KanbanStage` | — | Dados da etapa (id, name, color) |
| `candidates` | `KanbanCandidate[]` | `[]` | Candidatos na coluna |
| `onCandidateClick` | `(candidate) => void` | — | Callback ao clicar em card |
| `onAddCandidate` | `() => void?` | — | Callback para adicionar candidato |
| `isDragDisabled` | `boolean` | `false` | Desabilita drag em todos os cards |

### 3.34.5 Implementação

**React + Tailwind:**

```tsx
<Card
  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
    hover:border-gray-300 dark:hover:border-gray-600 cursor-pointer 
    transition-all hover:shadow-lg group rounded-md"
  onClick={onClick}
>
  <CardContent className="p-3">
    <div className="flex items-start gap-2">
      {!isDragDisabled && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity cursor-grab">
          <GripVertical className="h-4 w-4 text-gray-400" />
        </div>
      )}
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-gray-100 text-gray-700 text-xs">
          {initials}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-900 text-sm truncate">{name}</span>
          <span className={`text-sm font-bold ${getScoreColor(lia_score)}`}>
            {Math.round(lia_score)}
          </span>
        </div>
        <p className="text-xs text-gray-600 truncate">{current_title}</p>
        <p className="text-xs text-gray-500 truncate">{current_company}</p>
      </div>
    </div>
    {/* Skills (max 3 + counter) */}
    <div className="flex flex-wrap gap-1 mt-2">
      {skills.slice(0, 3).map(skill => (
        <Badge variant="outline" className="text-[10px] py-0">{skill}</Badge>
      ))}
      {skills.length > 3 && (
        <Badge variant="outline" className="text-[10px] py-0">+{skills.length - 3}</Badge>
      )}
    </div>
    {/* Footer: indicadores + data */}
    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-200">
      <div className="flex items-center gap-2">
        {/* Indicadores inteligentes com tooltips */}
      </div>
      <span className="text-[10px] text-gray-500">{formattedDate}</span>
    </div>
  </CardContent>
</Card>
```

**Vue + Vuetify:**

```vue
<template>
  <v-card
    variant="outlined"
    class="cursor-pointer"
    rounded="md"
    hover
    @click="$emit('click')"
  >
    <v-card-text class="pa-3">
      <div class="d-flex align-start ga-2">
        <v-avatar size="32" color="grey-lighten-2">
          <span class="text-caption font-weight-bold">{{ initials }}</span>
        </v-avatar>
        <div class="flex-1 overflow-hidden">
          <div class="d-flex align-center justify-space-between">
            <span class="text-body-2 font-weight-medium text-truncate">{{ candidate.name }}</span>
            <span class="text-body-2 font-weight-bold" :class="scoreColorClass">
              {{ Math.round(candidate.lia_score) }}
            </span>
          </div>
          <div class="text-caption text-grey-darken-1 text-truncate">{{ candidate.current_title }}</div>
        </div>
      </div>
      <div class="d-flex flex-wrap ga-1 mt-2">
        <v-chip v-for="skill in candidate.skills?.slice(0, 3)" :key="skill"
          size="x-small" variant="outlined">{{ skill }}</v-chip>
        <v-chip v-if="candidate.skills?.length > 3" size="x-small" variant="outlined">
          +{{ candidate.skills.length - 3 }}
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>
```

### 3.34.6 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Grip handle visível apenas no hover (`opacity-0 group-hover:opacity-100`) | Grip handle sempre visível (poluição visual) |
| Máximo 3 skills visíveis + counter "+N" | Exibir todas as skills (quebra layout do card) |
| Score com cor semântica (green/amber/red) | Score monocromático sem diferenciação |
| Tooltips explicativos nos indicadores do footer | Ícones sem explicação |
| `truncate` em nome, cargo e empresa | Texto quebrando em múltiplas linhas |
| Data formatada "24 fev" (curta, PT-BR) | Timestamp completo "2026-02-24T14:30:00Z" |
| `rounded-md` conforme DS | Border radius diferente do padrão |

### 3.34.7 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/pages/job-kanban/KanbanCard.tsx` | Componente do card (React) |
| `src/components/pages/job-kanban/KanbanColumn.tsx` | Componente da coluna |
| `src/components/pages/job-kanban/types.ts` | Types: KanbanCandidate, KanbanStage, MoveAction |
| `src/components/pages/job-kanban/hooks/useKanbanState.ts` | State management |

---

## 3.35 Chat Conversation Container (LiaConversation) `[Draft]`

Container principal que agrupa todas as mensagens do chat. Gerencia auto-scroll, stick-to-bottom (rola automaticamente quando novas mensagens chegam) e carregamento de histórico.

### 3.35.1 Anatomia

```
┌─────────────────────────────────────────────────────────┐
│ LiaConversation                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  ↑ Scroll area (overflow-y-auto, flex-1)            │ │
│ │                                                      │ │
│ │  ┌─ LiaWelcome (se chat vazio) ──────────────────┐  │ │
│ │  │ 🧠 "Olá! Eu sou a LIA..."                    │  │ │
│ │  └───────────────────────────────────────────────┘  │ │
│ │                                                      │ │
│ │  ┌─ LiaMessage (lia) ────────────────────────────┐  │ │
│ │  │ "Encontrei 12 candidatos..."                  │  │ │
│ │  └───────────────────────────────────────────────┘  │ │
│ │                                                      │ │
│ │  ┌───────────────────── LiaMessage (user) ──────┐   │ │
│ │  │                   "Mostra os top 5"          │   │ │
│ │  └──────────────────────────────────────────────┘   │ │
│ │                                                      │ │
│ │  ┌─ LiaThinking ────────────────────────────────┐   │ │
│ │  │ ● ● ● LIA está analisando...                │   │ │
│ │  └──────────────────────────────────────────────┘   │ │
│ │                                                      │ │
│ │              ← auto-scroll to bottom →              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─ Zona do Input ─────────────────────────────────────┐ │
│ │ ┌────────────────────────────┐ ┌───────────────────┐│ │
│ │ │ Suggestion Chips (3.33)    │ │ 💡 Botão Ideias  ││ │
│ │ └────────────────────────────┘ └───────────────────┘│ │
│ │ ┌──────────────────────────────────────┐ ┌──┐ ┌──┐ │ │
│ │ │ Digite sua mensagem...               │ │📎│ │➤ │ │ │
│ │ └──────────────────────────────────────┘ └──┘ └──┘ │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.35.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `messages` | `Message[]` | `[]` | Array de mensagens a renderizar |
| `isLoading` | `boolean` | `false` | Se true, mostra LiaThinking no final |
| `stickyBottom` | `boolean` | `true` | Auto-scroll para novas mensagens |
| `onScrollTop` | `() => void` | — | Callback ao atingir o topo (carregar histórico) |
| `emptyState` | `ReactNode` | `<LiaWelcome />` | Componente exibido quando `messages` vazio |
| `className` | `string` | — | Classes CSS adicionais |

### 3.35.3 Comportamento

| Interação | Comportamento |
|-----------|--------------|
| **Nova mensagem** | Auto-scroll para o final se `stickyBottom` e usuário está no bottom |
| **Scroll manual para cima** | Desativa auto-scroll temporariamente |
| **Scroll de volta ao bottom** | Reativa auto-scroll |
| **Atingir topo** | Dispara `onScrollTop` para carregar mensagens antigas |
| **Chat vazio** | Exibe `emptyState` (LiaWelcome por padrão) |
| **Durante streaming** | Mantém scroll no bottom enquanto LiaResponse está em streaming |

### 3.35.4 Implementação

**React + Tailwind:**

```tsx
<div className="flex flex-col h-full">
  <div
    ref={scrollRef}
    className="flex-1 overflow-y-auto"
    onScroll={handleScroll}
  >
    {messages.length === 0 ? (
      emptyState
    ) : (
      <div className="space-y-1 py-4">
        {messages.map(msg => (
          <LiaMessage key={msg.id} {...msg} />
        ))}
        {isLoading && <LiaThinking />}
        <div ref={bottomRef} />
      </div>
    )}
  </div>
  {/* Zona do input fica fora, no parent layout */}
</div>
```

### 3.35.5 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Auto-scroll apenas se o usuário está no bottom | Forçar scroll para baixo quando o usuário está lendo histórico |
| Agrupar mensagens consecutivas do mesmo remetente | Repetir avatar e header em cada mensagem sequencial |
| `space-y-1` entre mensagens do mesmo remetente | Espaçamento grande entre todas as mensagens |
| Lazy load de mensagens antigas ao scroll top | Carregar todo o histórico de uma vez |

---

## 3.36 Chat Response (LiaResponse) `[Draft]`

Componente de renderização de resposta da LIA com suporte a streaming progressivo (token-by-token). Separado do LiaMessage: o Message é o container (avatar, timestamp, ações), o Response é o **conteúdo** que pode estar sendo gerado em tempo real.

### 3.36.1 Estados

```
Estado 1 — Streaming:
┌─────────────────────────────────────────────┐
│ Analisei os 47 candidatos e identif█        │  ← cursor piscando
│                                              │
│ (markdown parcial renderizado em tempo real) │
└─────────────────────────────────────────────┘

Estado 2 — Complete:
┌─────────────────────────────────────────────┐
│ Analisei os 47 candidatos e identifiquei    │
│ **8 matches** acima de 75% de fit:          │
│                                              │
│ 1. **Ana Silva** — Score WSI: 89/100        │
│ 2. **Carlos Lima** — Score WSI: 84/100      │
│ 3. **Julia Santos** — Score WSI: 81/100     │
│                                              │
│ Quer que eu detalhe algum candidato?        │
│                                              │
│ [👍] [👎] [📋 Copiar]                       │  ← ações só após completar
└─────────────────────────────────────────────┘

Estado 3 — Com Action Cards inline:
┌─────────────────────────────────────────────┐
│ Preparei a comparação dos 3 finalistas:     │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │ 📊 Comparação de Candidatos          │    │  ← ActionCard inline
│ │ Ana vs Carlos vs Julia               │    │
│ │           [Ver Comparação]           │    │
│ └──────────────────────────────────────┘    │
│                                              │
│ Posso agendar entrevistas com eles?         │
└─────────────────────────────────────────────┘
```

### 3.36.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `content` | `string` | — | Conteúdo markdown da resposta |
| `isStreaming` | `boolean` | `false` | Se está em streaming progressivo |
| `streamCursor` | `boolean` | `true` | Mostra cursor piscando durante streaming |
| `actionCards` | `ActionCard[]` | `[]` | Cards de ação inline (comparação, agendamento, etc.) |
| `onComplete` | `() => void` | — | Callback quando streaming termina |
| `feedbackActions` | `FeedbackAction[]` | `[]` | Ações de feedback (like/dislike/copy) — visíveis só após complete |

**ActionCard:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `icon` | `ReactNode` | Ícone do card |
| `title` | `string` | Título da ação |
| `description` | `string` | Descrição breve |
| `actionLabel` | `string` | Texto do botão de ação |
| `onAction` | `() => void` | Callback ao clicar |

### 3.36.3 Implementação

**React + Tailwind:**

```tsx
<div className="text-sm text-gray-800 prose prose-sm max-w-none font-['Open_Sans']">
  <MarkdownRenderer content={content} />
  {isStreaming && streamCursor && (
    <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5" />
  )}

  {actionCards.length > 0 && !isStreaming && (
    <div className="mt-3 space-y-2">
      {actionCards.map(card => (
        <div key={card.title}
          className="border border-gray-200 rounded-md p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-2 mb-1">
            {card.icon}
            <span className="text-sm font-medium text-gray-900">{card.title}</span>
          </div>
          <p className="text-xs text-gray-500 mb-2">{card.description}</p>
          <button className="text-xs font-medium text-gray-700 hover:text-gray-900">
            {card.actionLabel} →
          </button>
        </div>
      ))}
    </div>
  )}

  {!isStreaming && feedbackActions.length > 0 && (
    <div className="flex items-center gap-1 mt-2 pt-2 border-t border-gray-100">
      {feedbackActions.map(action => (
        <button key={action.id}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <action.icon className="w-4 h-4" />
        </button>
      ))}
    </div>
  )}
</div>
```

### 3.36.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Cursor piscando (`animate-pulse`) durante streaming | Nenhuma indicação visual de que texto está sendo gerado |
| Renderizar markdown progressivamente conforme chega | Esperar resposta completa para renderizar |
| Ações de feedback só após resposta completa | Mostrar like/dislike durante streaming |
| ActionCards inline para ações contextuais | Botões avulsos no corpo da mensagem |
| Transition suave ao completar streaming | Mudança abrupta ao terminar |

---

## 3.37 Chat Welcome (LiaWelcome) `[Draft]`

Empty state conversacional exibido quando o chat está vazio. É uma **mensagem da LIA** com layout centralizado — sem botões clicáveis. As sugestões de interação ficam nos mecanismos já existentes na zona do input (3.33 Chat Suggestion Cards).

### 3.37.1 Variantes

```
Variante 'first-time' (primeira vez do recrutador):
┌──────────────────────────────────────────────┐
│                                               │
│              ┌────────┐                       │
│              │  🧠    │                       │  ← Brain icon 48px (maior que avatar)
│              │ (cyan) │                       │     bg-gray-100, icon #60BED1
│              └────────┘                       │
│                                               │
│     Olá! Eu sou a LIA, sua assistente        │  ← title (Open Sans, text-lg, font-semibold)
│        de recrutamento.                       │
│                                               │
│   Posso te ajudar a criar vagas, buscar      │  ← subtitle (text-sm, text-gray-500)
│   candidatos, analisar perfis e gerenciar    │
│   seu pipeline.                               │
│                                               │
│   Me conta: no que está trabalhando hoje?    │  ← prompt (text-sm, text-gray-700, font-medium)
│                                               │
└──────────────────────────────────────────────┘

Variante 'new-conversation' (recrutador recorrente):
┌──────────────────────────────────────────────┐
│              ┌────────┐                       │
│              │  🧠    │                       │
│              └────────┘                       │
│                                               │
│     Olá de novo, Marina!                     │  ← title personalizado com nome
│                                               │
│   Você tem 3 processos ativos e 12           │  ← subtitle com dados contextuais
│   candidatos aguardando análise.             │
│                                               │
│   No que quer focar hoje?                    │  ← prompt
│                                               │
└──────────────────────────────────────────────┘
```

### 3.37.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `variant` | `'first-time' \| 'new-conversation'` | `'first-time'` | Tipo de welcome |
| `title` | `string` | `'Olá! Eu sou a LIA...'` | Título principal |
| `subtitle` | `string` | `'Posso te ajudar a...'` | Texto descritivo |
| `prompt` | `string` | `'Me conta: no que está trabalhando hoje?'` | Pergunta conversacional |
| `userName` | `string` | — | Nome do recrutador (para variante new-conversation) |
| `contextData` | `{ activeJobs?: number, pendingCandidates?: number }` | — | Dados contextuais |
| `icon` | `ReactNode` | `<Brain />` | Ícone principal (48px) |

### 3.37.3 Implementação

**React + Tailwind:**

```tsx
<div className="flex flex-col items-center justify-center h-full px-8 py-12 text-center">
  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
    <Brain className="w-7 h-7 text-[#60BED1]" />
  </div>

  <h2 className="text-lg font-semibold text-gray-900 font-['Open_Sans'] mb-2">
    {variant === 'new-conversation' && userName
      ? `Olá de novo, ${userName}!`
      : title}
  </h2>

  <p className="text-sm text-gray-500 max-w-md mb-4">
    {variant === 'new-conversation' && contextData
      ? `Você tem ${contextData.activeJobs} processos ativos e ${contextData.pendingCandidates} candidatos aguardando análise.`
      : subtitle}
  </p>

  <p className="text-sm text-gray-700 font-medium">
    {prompt}
  </p>
</div>
```

**Vue + Vuetify:**

```vue
<template>
  <div class="d-flex flex-column align-center justify-center fill-height pa-8 text-center">
    <v-avatar size="48" color="grey-lighten-3" class="mb-4">
      <v-icon color="#60BED1" size="28">mdi-brain</v-icon>
    </v-avatar>

    <h2 class="text-h6 font-weight-bold text-grey-darken-4 mb-2">
      {{ displayTitle }}
    </h2>

    <p class="text-body-2 text-grey-darken-1" style="max-width: 400px">
      {{ displaySubtitle }}
    </p>

    <p class="text-body-2 font-weight-medium text-grey-darken-3 mt-4">
      {{ prompt }}
    </p>
  </div>
</template>
```

### 3.37.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Pergunta aberta como prompt ("No que está trabalhando hoje?") | Opções clicáveis dentro do welcome (botões) |
| Dados contextuais na variante recorrente (jobs ativos, candidatos pendentes) | Mesma mensagem genérica para todos os recrutadores |
| Brain icon 48px centralizado | Avatar pequeno ou ícone genérico |
| Desaparecer quando a primeira mensagem é enviada | Permanecer visível junto com mensagens |
| Sugestões na zona do input (3.33), nunca no corpo do welcome | Suggestion chips dentro do componente welcome |

### 3.37.5 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/expanded-chat/config/wizard-config.ts` | `INITIAL_GENERAL_MESSAGE`, `PRE_WIZARD_MESSAGE` — mensagens de welcome existentes |
| `src/components/ui/prompt-suggestions-dock.tsx` | Sugestões que aparecem na zona do input |
| `src/components/ui/prompt-suggestions-popover.tsx` | Popover de sugestões (💡 botão ideias) |

---

## 3.38 Data Visualization `[Draft]`

Diretrizes para gráficos e visualizações de dados nos dashboards de KPI da plataforma. Segue a regra 90/10 (grays dominantes, WeDo cyan como destaque único).

### 3.38.1 Paleta de Cores para Gráficos

| Série | Cor | Hex | Uso |
|-------|-----|-----|-----|
| Série 1 (primária) | `gray-900` | `#111827` | Dado principal |
| Série 2 | `gray-600` | `#4B5563` | Comparação secundária |
| Série 3 | `gray-400` | `#999999` | Terceiro nível |
| Série 4 | `gray-200` | `#D4D4D4` | Background/referência |
| Destaque | WeDo Cyan | `#60BED1` | Dado destacado, selecionado |
| Positivo | `green-600` | `#16A34A` | Tendência positiva, crescimento |
| Negativo | `red-600` | `#DC2626` | Tendência negativa, queda |
| Neutro | `amber-500` | `#F59E0B` | Atenção, sem direção definida |

### 3.38.2 Tipos de Gráfico por Contexto

| Dado | Gráfico Recomendado | Exemplo na Plataforma |
|------|---------------------|------------------------|
| Score WSI (0-100) | Gauge / radial progress | Card de candidato, detalhes |
| Candidatos por etapa | Horizontal bar chart | Dashboard pipeline |
| Evolução temporal | Line chart | Métricas ao longo do tempo |
| Distribuição | Donut chart | Distribuição por skill, localização |
| Comparação | Grouped bar chart | Comparação entre vagas |
| KPI single value | Stat card (número grande) | KPI cards no dashboard |

### 3.38.3 KPI Stat Card

```
┌─────────────────────────────┐
│  Candidatos Ativos          │  ← label (Open Sans, text-sm, text-gray-500)
│                              │
│  247                         │  ← valor (Inter, text-3xl, font-bold, text-gray-900)
│  ↑ 12% vs mês anterior      │  ← trend (text-xs, green-600 ou red-600)
│                              │
│  ▁▂▃▅▇█▇▅▃                  │  ← sparkline opcional (gray-400, 24px height)
└─────────────────────────────┘
```

**Especificações:**

| Elemento | Font | Tamanho | Cor |
|----------|------|---------|-----|
| Label | Open Sans | `text-sm` | `text-gray-500` |
| Valor | Inter | `text-3xl font-bold` | `text-gray-900` |
| Trend positivo | Inter | `text-xs` | `text-green-600` com ↑ |
| Trend negativo | Inter | `text-xs` | `text-red-600` com ↓ |
| Sparkline | — | 24px height | `text-gray-400` |

### 3.38.4 Regras Gerais

| Regra | Descrição |
|-------|-----------|
| **90/10 em charts** | Grays como cores primárias de séries, cyan apenas para destaque/seleção |
| **Font Inter para números** | Todos os valores numéricos em gráficos usam Inter com `tnum` (tabular numbers) |
| **Labels em Open Sans** | Títulos de eixos, legendas e labels usam Open Sans |
| **Sem cores de background em charts** | Fundo branco (`bg-white`), sem fill de área colorido |
| **Tooltip padrão** | `bg-gray-900 text-white text-xs rounded px-2 py-1` — mesmo do DS |
| **Border radius em bars** | `rounded-t` (2px) no topo de bars verticais |
| **Grid lines** | `border-gray-100` (sutil), horizontal apenas |
| **Animação** | `transition-all duration-300 ease-out` para entradas de dados |

### 3.38.5 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Gauge/radial para scores individuais (WSI, fit cultural) | Bar chart para um único score |
| Horizontal bar para comparação de etapas do pipeline | Pie chart para +6 categorias |
| Paleta monochrome (grays) com cyan como destaque único | Múltiplas cores vibrantes em um gráfico |
| Sparkline para tendência em KPI cards | Gráfico completo dentro de um card pequeno |
| Inter `tnum` para todos os números em eixos e labels | Open Sans para valores numéricos em gráficos |

---

## 3.39 Chip (ex-StatusBadge) `[Stable]`

> **⚠️ Migração concluída (Task #461):** O componente legacy `StatusBadge` (`src/components/ui/status-badge.tsx`) e seus subcomponentes (`ChannelBadge`, `SourceBadge`, `WarningBadge`, `DateTimeBadge`, `OriginBadge`, `AwaitingBadge`, `HiredBadge`, `OffLimitsBadge`) foram removidos. O Kanban moderno (`pages/job-kanban`) utiliza `KanbanChip` + `KanbanCardStatusBadges`, e os demais consumidores foram migrados para o componente canônico `Chip`.
>
> **✅ Migração massiva concluída (Task #466):** Todos os ~1.000 usos ad-hoc de `<Badge>` em `plataforma-lia/src` foram migrados para `Chip` (307 arquivos). Uma regra ESLint (`no-restricted-imports` em `eslint.config.mjs`) emite **warning** ao importar `@/components/ui/badge`, redirecionando novos consumidores para `@/components/ui/chip`. O primitivo `Badge` permanece no repo apenas para affordances raras do tipo "chip-com-botão" (shadcn-style), mas não deve ser usado para pílulas de status/estado.
>
> **Mapeamento aplicado pela migração:**
> | Badge variant | Chip equivalente |
> |--------------|------------------|
> | `default` / sem variant | `variant="neutral" muted` |
> | `secondary` | `variant="neutral" muted` |
> | `outline` | `variant="neutral"` |
> | `destructive` / `danger` | `variant="danger"` |
> | `success` | `variant="success"` |
> | `warning` | `variant="warning"` |
> | `info` | `variant="info"` |

Chip é o componente canônico de pill/badge da plataforma. Encapsula `kanbanChipStyles` (definido em `src/lib/design-tokens.ts`) garantindo paridade visual light/dark e consistência com o Kanban.

> **Arquivo:** `src/components/ui/chip.tsx`
> **Tokens:** `kanbanChipStyles` em `src/lib/design-tokens.ts`

### 3.39.1 Anatomia

```
┌─────────────────────────────┐
│ [Icon 8px] Label text 9px   │
└─────────────────────────────┘
  ↑ rounded-full, px-1.5 py-0.5
  ↑ bg: cor pastel por etapa (variant=accent)
  ↑ border: variant-dependent
  ↑ pulse animation quando isWaiting=true
```

**Especificações visuais:**

| Elemento | Valor |
|----------|-------|
| Font | Open Sans, 9px |
| Icon size | 8px (`w-2 h-2`) |
| Padding | `px-1.5 py-0.5` (6px horizontal, 2px vertical) |
| Border radius | `rounded-full` (9999px) |
| Gap icon↔text | `gap-0.5` (2px) |

### 3.39.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `density` | `"comfortable" \| "compact"` | `comfortable` | `comfortable` para tabelas/modais; `compact` para listas densas |
| `variant` | `"neutral" \| "success" \| "warning" \| "danger" \| "info"` | `neutral` | Paleta semântica |
| `muted` | `boolean` | `false` | Reduz contraste (variantes secundárias) |
| `className` | `string` | — | Classes adicionais |
| Demais props | `HTMLAttributes<HTMLSpanElement>` | — | Forwarded para o `<span>` |

### 3.39.3 Implementação

```tsx
import { Chip } from '@/components/ui/chip'

<Chip variant="success">Aprovado</Chip>
<Chip variant="warning" density="compact">Pendente</Chip>
<Chip variant="neutral" muted>Rascunho</Chip>
```

### 3.39.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `Chip` para qualquer pill/badge novo | Recriar pills com `<Badge>` ou `<span>` ad-hoc |
| Escolher a variante semântica adequada | Sobrescrever cores via `className` quando há variante |
| Usar `density="compact"` em listas/tabs densas | Misturar densidades dentro do mesmo grupo |
| Para o Kanban moderno, continuar usando `KanbanChip` | Reintroduzir o legacy `StatusBadge` |

---

## 3.40 CandidateCard `[Stable]`

Card de candidato exibido em resultados de busca e listagens, com informações de perfil, skills, score de match e histórico de comunicação expansível.

> **Arquivo:** `src/components/ui/candidate-card.tsx` (340 linhas)  
> **Tokens:** Usa `--eleven-*` para textos e backgrounds

### 3.40.1 Anatomia

```
┌─────────────────────────────────────────────┐
│ Nome do Candidato         [Source Badge]     │
│ 🏢 Título Profissional • Empresa             │
│ 📍 Localização                               │
│                                              │
│ [skill] [skill] [skill] [skill] [+N]         │
│                                              │
│ 🏆 85% match                                │
│                                              │
│ [✉ Contatar] [📅 Agendar] [in LinkedIn] [→]│
│ ─────────────────────────────────────────── │
│ 💬 Histórico de Comunicações         [▼/▲]  │
│   ├─ Email: Proposta enviada  12/02  ✓ Lida │
│   └─ WhatsApp: Retorno      10/02  ✓ Entregue│
└─────────────────────────────────────────────┘
```

### 3.40.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `name` | `string` | — (obrigatório) | Nome do candidato |
| `title` | `string \| null` | `null` | Título profissional |
| `company` | `string \| null` | `null` | Empresa atual |
| `location` | `string` | — (obrigatório) | Localização |
| `skills` | `string[]` | — (obrigatório) | Lista de skills (exibe até 6, trunca com `+N`) |
| `source_badge` | `string` | `"🏢 Banco Proprietário"` | Texto do badge de origem |
| `match_score` | `number \| null` | `null` | Percentual de match (0-100) |
| `email` | `string \| null` | `null` | Email (habilita botão Contatar) |
| `linkedin` | `string \| null` | `null` | URL LinkedIn (habilita botão LinkedIn) |
| `candidateId` | `string \| null` | `null` | ID do candidato (habilita histórico) |
| `companyId` | `string` | `'default'` | ID da empresa |
| `onViewProfile` | `() => void` | `undefined` | Callback ver perfil |
| `onContact` | `() => void` | `undefined` | Callback contatar |
| `onScheduleInterview` | `() => void` | `undefined` | Callback agendar entrevista |
| `onViewMoreCommunications` | `() => void` | `undefined` | Callback ver mais comunicações |

### 3.40.3 Implementação

```tsx
import { CandidateCard } from '@/components/ui/candidate-card'

<CandidateCard
  name="Ana Silva"
  title="Senior Frontend Developer"
  company="TechCorp"
  location="São Paulo, SP"
  skills={['React', 'TypeScript', 'Node.js', 'AWS']}
  match_score={92}
  email="ana@email.com"
  linkedin="https://linkedin.com/in/anasilva"
  candidateId="cand_123"
  onViewProfile={() => router.push('/candidato/cand_123')}
  onContact={() => openEmailModal('ana@email.com')}
  onScheduleInterview={() => openScheduleModal()}
/>
```

### 3.40.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar tokens `--eleven-*` para cores de texto | Hardcodar cores fora do sistema de tokens |
| Limitar skills visíveis a 6 com badge `+N` | Exibir todas as skills sem truncamento |
| Carregar histórico de comunicação sob demanda (lazy) | Pré-carregar histórico para todos os cards |
| Usar botões `variant="ghost"` para ações secundárias | Usar botões primários dentro do card |
| Fornecer `candidateId` para habilitar histórico expansível | Renderizar seção de histórico sem candidateId |

---

## 3.41 PromptSuggestionsDock `[Draft]`

Dock de sugestões do chat com 4 categorias temáticas (vagas, candidatos, entrevistas, relatórios), posicionável via drag-and-drop e com persistência de posição via localStorage.

> **Arquivo:** `src/components/ui/prompt-suggestions-dock.tsx` (412 linhas)  
> **Modos:** Inline (chat vazio) e Floating (chat com mensagens)

### 3.41.1 Anatomia

**Modo Inline (isEmpty=true):**
```
┌─────────────────────────────────────────────┐
│ 🧠 Tarefas Sugeridas                        │
├──────────────────┬──────────────────────────┤
│ [Icon] Título    │ [Icon] Título            │
│ Descrição curta  │ Descrição curta          │
├──────────────────┼──────────────────────────┤
│ [Icon] Título    │ [Icon] Título            │
│ Descrição curta  │ Descrição curta          │
└──────────────────┴──────────────────────────┘
  ↑ grid-cols-2, gap-3
```

**Modo Floating (isEmpty=false):**
```
┌ Draggable ──────────────────┐
│ ⠿ 🧠 Tarefas Sugeridas  ✕ │  ← Header draggable
├─────────────────────────────┤
│ [Icon] Título               │  ← Suggestion item
│ [Icon] Título               │
│ [Icon] Título               │
└─────────────────────────────┘
  ↑ fixed, w-80, max-h-480px, z-50
  ↑ rounded-16px, shadow: 0 8px 32px
```

**Cores por categoria:**

| Categoria | Icon Color | Bg | Border | Hover Bg |
|-----------|-----------|-----|--------|----------|
| vagas | `#374151` | `#F3F4F6` | `#BEBEBE` | `#D0EFF5` |
| candidatos | `#5DA47A` | `#E5F5EB` | `#5DA47A` | `#D5EFE0` |
| entrevistas | `#E5A853` | `#FDF4E8` | `#E5A853` | `#FAECD8` |
| relatorios | `#8B5CF6` | `#F3EAFF` | `#8B5CF6` | `#EBE0FF` |

### 3.41.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `onSelect` | `(command: string) => void` | — (obrigatório) | Callback quando sugestão é selecionada |
| `isEmpty` | `boolean` | — (obrigatório) | Se o chat está vazio (alterna modo inline/floating) |
| `onClose` | `() => void` | `undefined` | Callback de fechar |

### 3.41.3 Implementação

```tsx
import { PromptSuggestionsDock } from '@/components/ui/prompt-suggestions-dock'

<PromptSuggestionsDock
  onSelect={(command) => sendMessage(command)}
  isEmpty={messages.length === 0}
  onClose={() => setShowSuggestions(false)}
/>
```

### 3.41.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar modo inline quando o chat está vazio | Mostrar dock floating sobre chat vazio |
| Manter persistência de posição via localStorage | Resetar posição a cada render |
| Usar cores semânticas por categoria | Usar cores uniformes para todas as categorias |
| Fechar dock ao selecionar sugestão (modo floating) | Manter dock aberto após seleção |
| Respeitar font Open Sans para textos | Usar outras fontes fora do DS |

---

## 3.42 PremiumAutocomplete `[Draft]`

Autocomplete avançado com sugestões organizadas por categorias (recentes, populares na empresa, usados pelo time, recomendados pela LIA), com debounce de 300ms e navegação por teclado.

> **Arquivo:** `src/components/ui/premium-autocomplete.tsx` (255 linhas)  
> **Endpoint:** `/api/backend-proxy/search/autocomplete/premium`

### 3.42.1 Anatomia

```
┌──────────────────────────────────────┐
│ 🕐 Recentes                         │  ← Category header (bg-gray-100, text-10px, uppercase)
│   🔍 Python Developer Sênior SP     │  ← Suggestion item
│   🔍 React Frontend Pleno           │
├──────────────────────────────────────┤
│ 📈 Populares na empresa        15x  │  ← Com contagem de uso
│   🔍 Data Engineer Fintech          │
├──────────────────────────────────────┤
│ 👥 Usados pelo time                 │
│   🔍 Python AWS Data Engineer   8x  │
├──────────────────────────────────────┤
│ ⭐ Recomendados pela LIA            │
│   🔍 Data Scientist ML              │
└──────────────────────────────────────┘
  ↑ absolute, z-50, w-full, border-gray-200, rounded-md
```

### 3.42.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `query` | `string` | — (obrigatório) | Texto de busca (mínimo 2 caracteres) |
| `companyId` | `string` | `"demo"` | ID da empresa |
| `userId` | `string` | `"default_user"` | ID do usuário |
| `onSelect` | `(suggestion: string) => void` | — (obrigatório) | Callback de seleção |
| `isOpen` | `boolean` | — (obrigatório) | Controle de visibilidade |
| `onClose` | `() => void` | — (obrigatório) | Callback de fechamento |
| `className` | `string` | `undefined` | Classes adicionais |

**Categorias de sugestão:**

| Categoria | Ícone | Cor | Bg |
|-----------|-------|-----|-----|
| `recent` | Clock | `text-gray-600` | `bg-gray-100` |
| `popular` | TrendingUp | `text-green-500` | `bg-green-50` |
| `team` | Users | `text-purple-500` | `bg-purple-50` |
| `recommended` | Star | `text-amber-500` | `bg-amber-50` |

### 3.42.3 Implementação

```tsx
import { PremiumAutocomplete } from '@/components/ui/premium-autocomplete'

<div className="relative">
  <Input
    value={query}
    onChange={(e) => setQuery(e.target.value)}
    onFocus={() => setIsOpen(true)}
  />
  <PremiumAutocomplete
    query={query}
    companyId={companyId}
    onSelect={(text) => { setQuery(text); setIsOpen(false) }}
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
  />
</div>
```

### 3.42.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar debounce de 300ms para chamadas à API | Chamar API a cada keystroke |
| Fornecer fallback suggestions quando API falha | Mostrar estado vazio em caso de erro |
| Navegar com ↑↓ + Enter/Tab para seleção | Obrigar uso do mouse para selecionar |
| Fechar com Escape | Deixar dropdown aberto ao perder foco |
| Exibir contagem de uso (`count`) quando disponível | Omitir frequência de uso das sugestões |

---

## 3.43 BulkSelectionBar `[Stable]`

Barra de ações em massa (bulk actions) que aparece no topo da página quando candidatos são selecionados. Inclui ações primárias inline e secundárias em dropdown.

> **Arquivo:** `src/components/ui/bulk-selection-bar.tsx` (269 linhas)  
> **Variantes:** `BulkSelectionBar` (fixed top) e `BulkSelectionBarInline` (inline)

### 3.43.1 Anatomia

**BulkSelectionBar (fixed):**
```
┌──────────────────────────────────────────────────────────────────────┐
│ ☑ Selecionar todos │ 👥 5 │ candidatos selecionados de 42          │
│                    │      │    [→ Mover] [📝 Dados] [✉ Msg] [⋯] [✕]│
└──────────────────────────────────────────────────────────────────────┘
  ↑ fixed top-0, z-50, bg-gray-900, text-gray-200
  ↑ slide-in-from-top animation
```

**BulkSelectionBarInline:**
```
┌──────────────────────────────────────────────────────────────────┐
│ ☑ Todos  │ 5 selecionados │  [→] [📝] [✉] [✕ Reprovar] [✕]   │
└──────────────────────────────────────────────────────────────────┘
  ↑ inline, bg-gray-100, border-gray-200, rounded-md
```

### 3.43.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `selectedCount` | `number` | — (obrigatório) | Quantidade selecionada (retorna `null` se 0) |
| `totalCount` | `number` | — (obrigatório) | Total disponível |
| `isAllSelected` | `boolean` | `false` | Se todos estão selecionados |
| `actions` | `BulkAction[]` | `DEFAULT_ACTIONS` | Lista de ações disponíveis |
| `onSelectAll` | `() => void` | — (obrigatório) | Callback selecionar todos |
| `onClearSelection` | `() => void` | — (obrigatório) | Callback limpar seleção |
| `onAction` | `(actionId: BulkActionType) => void` | — (obrigatório) | Callback de ação |
| `className` | `string` | `undefined` | Classes adicionais |
| `showSecondaryActions` | `boolean` | `true` | Exibir dropdown de ações extras |

**Ações padrão (`DEFAULT_ACTIONS`):**

| ID | Label | Ícone | Variante |
|----|-------|-------|----------|
| `move_stage` | Mover Etapa | ArrowRight | default |
| `request_data` | Solicitar Dados | FileText | default |
| `send_message` | Mensagem | Mail | default |
| `reject` | Reprovar | XCircle | destructive |

### 3.43.3 Implementação

```tsx
import { BulkSelectionBar, BulkSelectionBarInline } from '@/components/ui/bulk-selection-bar'

{/* Versão fixed (topo da página) */}
<BulkSelectionBar
  selectedCount={selectedIds.length}
  totalCount={candidates.length}
  isAllSelected={selectedIds.length === candidates.length}
  onSelectAll={() => setSelectedIds(candidates.map(c => c.id))}
  onClearSelection={() => setSelectedIds([])}
  onAction={(actionId) => handleBulkAction(actionId, selectedIds)}
/>

{/* Versão inline (dentro de seção) */}
<BulkSelectionBarInline
  selectedCount={selectedIds.length}
  totalCount={candidates.length}
  onSelectAll={selectAll}
  onClearSelection={clearSelection}
  onAction={handleAction}
/>
```

### 3.43.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Ocultar a barra quando `selectedCount === 0` | Exibir barra vazia sem seleção |
| Usar `variant="destructive"` para ações destrutivas (reprovar) | Usar estilo default para ações irreversíveis |
| Primeiras 3 ações inline, restante em dropdown `⋯` | Exibir todas as ações inline (excede espaço) |
| Usar `slide-in-from-top` animation para entrada | Aparecer sem transição |
| Mostrar contagem `"N candidato(s) selecionado(s)"` | Omitir feedback visual da seleção |

---

## 3.44 ContextPill `[Stable]`

Pill de contexto compacta com ícone, texto primário e secundário opcional, e botão de dismiss. Usada para exibir contexto ativo (vaga selecionada, filtro aplicado, candidato em foco) em painéis da LIA.

> **Arquivo:** `src/components/ui/context-pill.tsx` (60 linhas)  
> **Tokens:** Usa sistema `--eleven-*` para cores

### 3.44.1 Anatomia

```
┌──────────────────────────────────────┐
│ [📍] Texto Primário • Texto Sec  [✕] │
└──────────────────────────────────────┘
  ↑ inline-flex, rounded-full, px-3 py-1.5
  ↑ bg: var(--eleven-bg-card)
  ↑ border: var(--eleven-border)
  ↑ text: var(--eleven-text-primary)
```

### 3.44.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `icon` | `React.ReactNode` | `<MapPin />` | Ícone à esquerda |
| `primaryText` | `string` | — (obrigatório) | Texto principal |
| `secondaryText` | `string` | `undefined` | Texto secundário (após separador `•`) |
| `onDismiss` | `() => void` | `undefined` | Callback de dismiss (exibe botão `✕`) |
| `className` | `string` | `''` | Classes adicionais |

### 3.44.3 Implementação

```tsx
import { ContextPill } from '@/components/ui/context-pill'

<ContextPill
  icon={<Briefcase className="w-3.5 h-3.5" />}
  primaryText="Frontend Developer Sr."
  secondaryText="3 candidatos"
  onDismiss={() => clearContext()}
/>

{/* Sem dismiss (informativo) */}
<ContextPill
  primaryText="São Paulo, SP"
  secondaryText="Remoto"
/>
```

### 3.44.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar tokens `--eleven-*` para manter consistência com painéis LIA | Usar classes Tailwind hardcoded para cores |
| Manter texto primário curto (2-4 palavras) | Usar textos longos que quebrem o layout pill |
| Fornecer `onDismiss` quando o contexto é removível | Omitir dismiss em pills que representam filtros ativos |
| Usar ícones de 3.5×3.5 (`w-3.5 h-3.5`) | Usar ícones grandes que desproporcionem a pill |
| Usar `secondaryText` para metadados complementares | Duplicar informação entre primary e secondary |

---

## 3.45 CommandPalette `[Draft]`

Overlay de command palette (estilo ⌘K) com busca, categorias (ações, navegação, configurações), navegação por teclado e atalhos de teclado por comando.

> **Arquivo:** `src/components/ui/command-palette.tsx` (279 linhas)  
> **Tokens:** Usa sistema `--eleven-*` para superfícies  
> **Trigger:** `Ctrl+K` / `⌘K`

### 3.45.1 Anatomia

```
┌──────────────────────────────────────────────┐
│ 🔍 Buscar ação ou digitar comando...  [ESC] │  ← Search input
├──────────────────────────────────────────────┤
│ AÇÕES                                        │  ← Category label (text-xs, text-tertiary)
│   📅 Agendar Entrevista                  [A] │  ← Command item com shortcut
│   ⚡ Avaliar Candidato                   [E] │
│   ✉  Gerar Email                             │
│   💬 Enviar WhatsApp                         │
│   👥 Comparar Perfis                         │
├──────────────────────────────────────────────┤
│ NAVEGAÇÃO                                    │
│   📊 Ver Analytics                           │
├──────────────────────────────────────────────┤
│ CONFIGURAÇÕES                                │
│   ⚙ Configurações                           │
│   👤 Meu Perfil                              │
├──────────────────────────────────────────────┤
│ Use ↑↓ para navegar, Enter para selecionar   │
└──────────────────────────────────────────────┘
  ↑ max-w-2xl, Dialog overlay
  ↑ max-h-400px scrollable
  ↑ bg: var(--eleven-bg-main)
```

### 3.45.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `isOpen` | `boolean` | — (obrigatório) | Controle de visibilidade |
| `onClose` | `() => void` | — (obrigatório) | Callback de fechamento |
| `commands` | `CommandItem[]` | — (obrigatório) | Lista de comandos disponíveis |
| `placeholder` | `string` | `"Buscar ação ou digitar comando..."` | Placeholder do input |

**Tipo `CommandItem`:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `id` | `string` | Identificador único |
| `label` | `string` | Nome do comando |
| `description` | `string` | Descrição (exibida como subtexto) |
| `icon` | `React.ReactNode` | Ícone (Lucide, 16px) |
| `category` | `'actions' \| 'navigation' \| 'settings'` | Agrupamento |
| `shortcut` | `string` | Atalho de teclado (exibido como `<kbd>`) |
| `onSelect` | `() => void` | Callback de execução |

### 3.45.3 Implementação

```tsx
import { CommandPalette, defaultCommands } from '@/components/ui/command-palette'

const commands = defaultCommands({
  onSchedule: () => openScheduleModal(),
  onEvaluate: () => evaluateCandidate(),
  onEmail: () => openEmailComposer(),
  onAnalytics: () => router.push('/analytics'),
  onSettings: () => router.push('/configuracoes'),
})

<CommandPalette
  isOpen={isCommandPaletteOpen}
  onClose={() => setIsCommandPaletteOpen(false)}
  commands={commands}
/>
```

### 3.45.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Auto-focus no input ao abrir | Exigir clique no input para começar a digitar |
| Filtrar comandos em tempo real por label e description | Filtrar apenas por label |
| Usar categorias para agrupar logicamente | Listar todos os comandos sem agrupamento |
| Fechar ao executar comando (Enter) ou Escape | Manter palette aberta após execução |
| Exibir atalhos de teclado como `<kbd>` styled | Exibir shortcuts como texto simples |
| Mostrar mensagem "Nenhum comando encontrado" quando vazio | Deixar lista vazia sem feedback |

---

## 3.46 QuickActionChips `[Stable]`

Chips de ações rápidas com variantes semânticas (default, primary, success, warning), usados como atalhos contextuais em painéis de candidatos e chat expandido.

> **Arquivo:** `src/components/ui/quick-action-chips.tsx` (96 linhas)  
> **Tokens:** Usa `--eleven-border` para bordas

### 3.46.1 Anatomia

```
[📅 Agendar Entrevista] [⚡ Avaliar Fit] [✉ Gerar Email] [💬 WhatsApp]
  ↑ inline-flex, rounded-full, px-3 py-1.5
  ↑ border: var(--eleven-border)
  ↑ gap-2 entre chips
  ↑ text-sm, font-medium
```

### 3.46.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `actions` | `QuickAction[]` | — (obrigatório) | Lista de ações |
| `className` | `string` | `''` | Classes adicionais |

**Tipo `QuickAction`:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `id` | `string` | Identificador único |
| `label` | `string` | Texto do chip |
| `icon` | `LucideIcon` | Ícone (Lucide component type) |
| `onClick` | `() => void` | Callback de ação |
| `variant` | `'default' \| 'primary' \| 'success' \| 'warning'` | Estilo visual |

**Estilos por variante:**

| Variante | Classes |
|----------|---------|
| `default` | `hover:bg-gray-100` |
| `primary` | `text-gray-600 border-gray-300 hover:bg-gray-100` |
| `success` | `bg-green-500/10 text-green-600 border-green-500/30 hover:bg-green-500/20` |
| `warning` | `bg-amber-500/10 text-amber-600 border-amber-500/30 hover:bg-amber-500/20` |

### 3.46.3 Implementação

```tsx
import { QuickActionChips, defaultCandidateActions } from '@/components/ui/quick-action-chips'

const actions = defaultCandidateActions.map(action => ({
  ...action,
  onClick: () => handleQuickAction(action.id)
}))

<QuickActionChips actions={actions} />
```

### 3.46.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `rounded-full` para forma pill | Usar `rounded-md` (desvio do design) |
| Manter ícone 3.5×3.5 + label text-sm | Usar ícones grandes ou texto extenso |
| Usar variante `success`/`warning` apenas com propósito semântico | Usar cores para decoração |
| Usar `defaultCandidateActions` como base e customizar | Recriar lista de ações do zero |
| Limite visual de 4-6 chips visíveis por linha | Exibir 10+ chips sem scroll/wrap |

---

## 3.47 ScoreIconButton `[Stable]`

Botão compacto com ícone e score numérico, com tooltip informativo. Usado para exibir scores LIA (geral, triagem, CV, técnico, inglês, Big Five) em cards de candidatos no Kanban.

> **Arquivo:** `src/components/ui/score-icon-button.tsx` (86 linhas)  
> **LIA Score IDs:** `geral`, `triagem`, `cv`

### 3.47.1 Anatomia

```
  [🧠 85]    [📋 92%]    [📝]
   ↑           ↑           ↑
   ativo       ativo       inativo (opacity-25)
   (scale      com value   sem score
    hover)     formatado   cursor-default
```

**Especificações:**

| Elemento | Valor |
|----------|-------|
| Ícone | `w-3.5 h-3.5` |
| Score text | `text-[11px] font-bold font-['Open_Sans'] text-gray-700` |
| Active color (LIA scores) | `#111827` |
| Active color (outros) | `#374151` |
| Inactive color | `#999999` (opacity 25%) |
| Focus ring | `ring-2 ring-offset-1 ring-gray-400 rounded-full` |
| Hover | `scale-105` |

### 3.47.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `id` | `string` | — (obrigatório) | ID do score (`geral`, `triagem`, `cv`, `tecnico`, `ingles`, `b5`) |
| `icon` | `React.ComponentType` | — (obrigatório) | Componente de ícone |
| `value` | `number \| null \| undefined` | — (obrigatório) | Valor numérico do score |
| `formattedValue` | `string` | `undefined` | Valor formatado (ex: `"85%"`) |
| `label` | `string` | — (obrigatório) | Label para tooltip e aria-label |
| `onClick` | `() => void` | — (obrigatório) | Callback de clique |
| `disabled` | `boolean` | `undefined` | Desabilitar externamente |
| `alwaysClickable` | `boolean` | `false` | Clicável mesmo sem score (para modais CV/Triagem) |

### 3.47.3 Implementação

```tsx
import { ScoreIconButton } from '@/components/ui/score-icon-button'
import { Brain, FileText, Code } from 'lucide-react'

<div className="flex items-center gap-2">
  <ScoreIconButton
    id="geral"
    icon={Brain}
    value={85}
    label="Score Geral LIA"
    onClick={() => openScoreDetail('geral')}
  />
  <ScoreIconButton
    id="cv"
    icon={FileText}
    value={null}
    label="Análise de CV"
    onClick={() => openCvModal()}
    alwaysClickable
  />
  <ScoreIconButton
    id="tecnico"
    icon={Code}
    value={72}
    formattedValue="72%"
    label="Score Técnico"
    onClick={() => openTechDetail()}
  />
</div>
```

### 3.47.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `alwaysClickable` para CV/Triagem (modais acessíveis sem score) | Desabilitar botões que têm modais associados |
| Usar `formattedValue` para exibir `%` ou unidades | Formatar valor no label do tooltip |
| Manter ícone+score compactos (11px font, 3.5 icon) | Aumentar tamanho — componente é micro by design |
| Usar IDs semânticos (`geral`, `triagem`, `cv`) | Usar IDs genéricos ou numéricos |
| Diferenciar visualmente LIA scores (cor `#111827`) dos demais | Usar mesma cor para todos os scores |

---

## 3.48 LiaExpandedPanel `[Draft]`

Painel expandido da LIA com header padronizado (Brain icon), slots para contextPills, quickActions, tabs, conteúdo scrollable e footer. Suporta redimensionamento horizontal.

> **Arquivo:** `src/components/ui/lia-expanded-panel.tsx` (514 linhas)  
> **Subcomponentes:** `LiaTabButton`, `LiaQuickActionChip`, `LiaChatInput`, `LiaChatMessage`, `LiaLoadingIndicator`

### 3.48.1 Anatomia

```
┌─────────────────────────────────────────────┐
│ [🧠] Olá! Sou a Lia.                   [✕] │  ← Header (Brain icon cyan)
│      Posso criar vagas, buscar...           │     bg: #FFFFFF
├─────────────────────────────────────────────┤
│ [📍 Frontend Dev Sr. • 3 candidatos]    [✕] │  ← Context Pills (opcional)
│                                             │     bg: rgba(96,190,209,0.04)
├─────────────────────────────────────────────┤
│ [📅 Agendar] [⚡ Avaliar] [✉ Email]        │  ← Quick Actions (opcional)
├─────────────────────────────────────────────┤
│ [Chat ●] [Candidatos] [Pipeline]            │  ← Tabs (opcional, pill ou underline)
├─────────────────────────────────────────────┤
│                                             │
│  (Conteúdo scrollable)                      │  ← Main content (flex-1, overflow-y-auto)
│                                             │
├─────────────────────────────────────────────┤
│ [Input / Footer area]                       │  ← Footer (opcional)
└─────────────────────────────────────────────┘│
                                               │← Resize handle (w-2, cursor-ew-resize)
```

### 3.48.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `title` | `string` | `"Olá! Sou a Lia."` | Título do header |
| `description` | `string` | `"Posso criar vagas..."` | Descrição do header |
| `onClose` | `() => void` | — (obrigatório) | Callback de fechar |
| `width` | `number` | `undefined` | Largura em pixels |
| `height` | `string` | `"calc(100vh - 12rem)"` | Altura CSS |
| `resizable` | `boolean` | `true` | Habilitar redimensionamento |
| `onResize` | `(e: React.MouseEvent) => void` | `undefined` | Callback de resize |
| `contextPills` | `React.ReactNode` | `undefined` | Slot para ContextPills |
| `quickActions` | `React.ReactNode` | `undefined` | Slot para QuickActionChips |
| `tabs` | `React.ReactNode` | `undefined` | Slot para tabs |
| `children` | `React.ReactNode` | — (obrigatório) | Conteúdo principal scrollable |
| `footer` | `React.ReactNode` | `undefined` | Slot para footer (input, botões) |
| `className` | `string` | `''` | Classes adicionais |

**Subcomponente `LiaTabButton`:**

| Prop | Type | Descrição |
|------|------|-----------|
| `active` | `boolean` | Tab ativa |
| `onClick` | `() => void` | Callback |
| `icon` | `React.ReactNode` | Ícone da tab |
| `label` | `string` | Texto da tab |
| `variant` | `'pill' \| 'underline'` | Estilo da tab |

### 3.48.3 Implementação

```tsx
import { LiaExpandedPanel, LiaTabButton, LiaChatInput, LiaChatMessage } from '@/components/ui/lia-expanded-panel'
import { ContextPill } from '@/components/ui/context-pill'
import { QuickActionChips } from '@/components/ui/quick-action-chips'

<LiaExpandedPanel
  title="Olá! Sou a Lia."
  description="Posso criar vagas, buscar candidatos e muito mais!"
  onClose={() => setExpanded(false)}
  width={panelWidth}
  onResize={handleResize}
  contextPills={
    <ContextPill primaryText="Frontend Dev Sr." secondaryText="3 candidatos" onDismiss={clearContext} />
  }
  quickActions={<QuickActionChips actions={actions} />}
  tabs={
    <div className="flex gap-2">
      <LiaTabButton active={tab === 'chat'} onClick={() => setTab('chat')} icon={<MessageCircle className="w-3 h-3" />} label="Chat" />
      <LiaTabButton active={tab === 'candidates'} onClick={() => setTab('candidates')} icon={<Users className="w-3 h-3" />} label="Candidatos" />
    </div>
  }
  footer={
    <LiaChatInput value={input} onChange={setInput} onSubmit={sendMessage} />
  }
>
  {messages.map(msg => (
    <LiaChatMessage key={msg.id} type={msg.role} content={msg.content} />
  ))}
</LiaExpandedPanel>
```

### 3.48.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar Brain icon cyan no header (identidade LIA) | Substituir Brain icon por outro ícone |
| Usar slots (contextPills, quickActions, tabs, footer) | Inserir elementos fixos dentro do children |
| Manter conteúdo principal scrollable (`overflow-y-auto`) | Fixar conteúdo sem scroll |
| Usar `LiaTabButton` com variant `pill` ou `underline` | Criar tabs customizadas fora do padrão |
| Fornecer `onResize` quando `resizable=true` | Habilitar resizable sem handler de resize |
| Usar fonte Open Sans 14px para título, 11px para descrição | Usar tamanhos de fonte diferentes |

---

## 3.49 PipelineStagesCarousel `[Stable]`

Carrossel horizontal de estágios do pipeline de recrutamento com contadores de candidatos, indicadores de cor por etapa e scroll com botões de navegação e gradientes de fade.

> **Arquivo:** `src/components/ui/pipeline-stages-carousel.tsx` (207 linhas)

### 3.49.1 Anatomia

```
  [◀]  ░░                                                            ░░  [▶]
       ┌──────────┐  ›  ┌──────────┐  ›  ┌──────────┐  ›  ┌──────────┐
       │ Sourcing  │     │ Screening│     │ Entrev HR │     │ Oferta   │
       │ 24        │     │ 15       │     │ 8         │     │ 3        │
       │ candidatos│     │ candidatos│     │ candidatos│     │ candidatos│
       │ ████████░░│     │ ██████░░░│     │ ████░░░░░│     │ ██░░░░░░░│
       └──────────┘     └──────────┘     └──────────┘     └──────────┘
         ↑ min-w-130px, rounded-md, border-2
         ↑ selected: border-gray-900 + checkmark
         ↑ progress bar: cor por etapa
```

**Cores por etapa:**

| Etapa | Cor |
|-------|-----|
| sourcing | `#A8CED5` |
| screening | `#BFA8D5` |
| interview_hr | `#A8D5B7` |
| interview_technical | `#B8E0D2` |
| interview_manager | `#F5E6B3` |
| offer | `#F5D6A8` |
| hired | `#A8D5B7` |

### 3.49.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `stages` | `PipelineStage[]` | — (obrigatório) | Lista de estágios |
| `selectedStages` | `string[]` | `[]` | IDs dos estágios selecionados |
| `onStageClick` | `(stageId: string) => void` | `undefined` | Callback de clique em estágio |
| `className` | `string` | `undefined` | Classes adicionais |

**Tipo `PipelineStage`:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `id` | `string` | ID do estágio (sourcing, screening, etc.) |
| `name` | `string` | Nome interno |
| `displayName` | `string` | Nome exibido (opcional, usa `name` como fallback) |
| `count` | `number` | Quantidade de candidatos |
| `color` | `string` | Cor customizada (opcional, usa mapa interno) |

### 3.49.3 Implementação

```tsx
import { PipelineStagesCarousel } from '@/components/ui/pipeline-stages-carousel'

const stages = [
  { id: 'sourcing', name: 'Sourcing', displayName: 'Captação', count: 24 },
  { id: 'screening', name: 'Screening', displayName: 'Triagem', count: 15 },
  { id: 'interview_hr', name: 'Interview HR', displayName: 'Entrevista RH', count: 8 },
  { id: 'offer', name: 'Offer', displayName: 'Proposta', count: 3 },
  { id: 'hired', name: 'Hired', displayName: 'Contratado', count: 1 },
]

<PipelineStagesCarousel
  stages={stages}
  selectedStages={['screening']}
  onStageClick={(stageId) => setFilter(stageId)}
/>
```

### 3.49.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar `displayName` para nomes em pt-BR | Exibir IDs internos como `interview_hr` para o usuário |
| Mostrar setas de navegação apenas quando há scroll | Exibir setas sempre (mesmo sem overflow) |
| Usar gradientes de fade nas bordas para indicar scroll | Cortar cards abruptamente nas bordas |
| Usar `ChevronRight` entre stages como separador | Omitir separadores visuais entre etapas |
| Manter `min-w-130px` por card para legibilidade | Comprimir cards para caber tudo sem scroll |
| Exibir checkmark no estágio selecionado | Usar apenas cor para indicar seleção |

---

## 3.50 DateRangePicker `[Stable]`

Seletor de período com calendário visual, presets rápidos (últimos 7/30/90 dias, este mês, trimestre) e meses em pt-BR. Usado em filtros de dashboard e relatórios.

> **Arquivo:** `src/components/ui/date-range-picker.tsx` (297 linhas)

### 3.50.1 Anatomia

```
┌───────────────────────────────────────┐
│ 📅 01/02/2026 - 28/02/2026       [✕] │  ← Trigger button (outline, min-w-200px)
└───────────────────────────────────────┘

  ↓ Dropdown (Card, z-50, min-w-360px)

┌──────────────────────────────┬────────────────┐
│ [◀] Fevereiro 2026    [▶]   │ Atalhos         │
│                              │                │
│ Dom Seg Ter Qua Qui Sex Sáb │ Últimos 7 dias  │
│                 1   2   3   │ Últimos 30 dias │
│  4   5   6   7   8   9  10  │ Últimos 90 dias │
│ 11  12  [13] 14  15  16  17 │ Este mês        │
│ 18  19  20  21  22  [23] 24 │ Mês passado     │
│ 25  26  27  28              │ Este trimestre  │
│                              │                │
│ [Cancelar]       [Aplicar]   │                │
└──────────────────────────────┴────────────────┘
  ↑ Dias selecionados: bg-gray-900 text-white
  ↑ Dias no range: bg-gray-200
  ↑ Hoje: ring-1 ring-gray-400
  ↑ Font: Open Sans (text-xs)
```

### 3.50.2 Props API

| Prop | Type | Default | Descrição |
|------|------|---------|-----------|
| `value` | `DateRange` | `undefined` | Período selecionado (`{ start_date, end_date }`) |
| `onChange` | `(range: DateRange) => void` | — (obrigatório) | Callback de mudança |
| `className` | `string` | `undefined` | Classes adicionais |
| `placeholder` | `string` | `"Selecionar período"` | Placeholder do trigger |

**Tipo `DateRange`:**

| Campo | Type | Descrição |
|-------|------|-----------|
| `start_date` | `string` | Data início (ISO: `YYYY-MM-DD`) |
| `end_date` | `string` | Data fim (ISO: `YYYY-MM-DD`) |

**Presets disponíveis:**

| Label | Tipo |
|-------|------|
| Últimos 7 dias | `days: 7` |
| Últimos 30 dias | `days: 30` |
| Últimos 90 dias | `days: 90` |
| Este mês | `type: 'this_month'` |
| Mês passado | `type: 'last_month'` |
| Este trimestre | `type: 'this_quarter'` |

### 3.50.3 Implementação

```tsx
import { DateRangePicker } from '@/components/ui/date-range-picker'

const [dateRange, setDateRange] = useState<{ start_date: string; end_date: string }>({
  start_date: '',
  end_date: ''
})

<DateRangePicker
  value={dateRange}
  onChange={(range) => setDateRange(range)}
  placeholder="Filtrar por período"
/>
```

### 3.50.4 Do's & Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Usar meses em pt-BR (`Janeiro`, `Fevereiro`, etc.) | Exibir meses em inglês |
| Exibir presets no painel lateral para acesso rápido | Esconder presets em submenu |
| Usar botão "Aplicar" para confirmar seleção | Aplicar range automaticamente a cada clique |
| Fechar dropdown ao clicar fora (`mousedown` listener) | Manter dropdown aberto ao perder foco |
| Exibir botão `✕` para limpar seleção no trigger | Obrigar re-seleção para limpar filtro |
| Usar `bg-gray-900 text-white` para datas selecionadas | Usar cores WeDo para seleção de datas |
| Indicar "hoje" com `ring-1 ring-gray-400` | Não destacar o dia atual |
| Usar font Open Sans `text-xs` para consistência | Usar fontes ou tamanhos diferentes |

---

# PARTE 4: PADRÕES

## 4.1 Estados de Componentes

### 4.1.1 Hierarquia de Estados

| Estado | Ordem | Classe Visual | Quando Aplicar |
|--------|-------|---------------|----------------|
| **Disabled** | 1 (maior prioridade) | Opacidade reduzida | Elemento não disponível |
| **Loading** | 2 | Spinner + disabled | Ação em progresso |
| **Error** | 3 | Border red, bg red-50 | Validação falhou |
| **Focus** | 4 | Ring 2px gray-900/20 | Teclado selecionado |
| **Active** | 5 | Transform scale 0.98 | Mouse clicando |
| **Hover** | 6 | Background + transform | Mouse sobre |
| **Default** | 7 (menor prioridade) | Estado padrão | Nenhuma interação |

### 4.1.2 Focus Ring Padrão

```css
.lia-focus-ring:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2);
}
```

---

## 4.2 Formulários

### 4.2.1 Layout de Forms

```html
<!-- Form vertical (padrão) -->
<form class="space-y-4">
  <div class="space-y-1">
    <label class="block text-[11px] font-semibold text-gray-800">Nome</label>
    <input type="text" class="w-full px-3 py-2 text-sm border border-gray-200 rounded" />
  </div>
  
  <div class="flex justify-end gap-2 pt-2">
    <button type="button" class="px-4 py-2 text-sm border border-gray-300 rounded">Cancelar</button>
    <button type="submit" class="px-4 py-2 text-sm bg-gray-900 text-white rounded">Salvar</button>
  </div>
</form>
```

### 4.2.2 Validação de Forms

```html
<!-- Campo com erro -->
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Email</label>
  <input 
    type="email"
    class="w-full px-3 py-2 text-sm border border-red-300 rounded bg-red-50"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p id="email-error" class="text-xs text-red-600 flex items-center gap-1">
    <svg class="w-3 h-3">...</svg>
    Email inválido
  </p>
</div>

<!-- Campo obrigatório -->
<label class="block text-[11px] font-semibold text-gray-800">
  Nome <span class="text-red-600">*</span>
</label>
```

### 4.2.3 Validação de Forms Vuetify (Vue)

Padrão de regras de validação para uso com Vuetify, com mensagens em português:

```typescript
// utils/validation-rules.ts

export type ValidationRule = (value: any) => boolean | string

export const rules = {
  required: (msg = 'Campo obrigatório'): ValidationRule =>
    (v) => !!v || msg,

  email: (msg = 'Email inválido'): ValidationRule =>
    (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || msg,

  minLength: (min: number, msg?: string): ValidationRule =>
    (v) => !v || v.length >= min || msg || `Mínimo de ${min} caracteres`,

  maxLength: (max: number, msg?: string): ValidationRule =>
    (v) => !v || v.length <= max || msg || `Máximo de ${max} caracteres`,

  phone: (msg = 'Telefone inválido'): ValidationRule =>
    (v) => !v || /^\(\d{2}\)\s?\d{4,5}-\d{4}$/.test(v) || msg,

  cpf: (msg = 'CPF inválido'): ValidationRule =>
    (v) => !v || /^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(v) || msg,

  cnpj: (msg = 'CNPJ inválido'): ValidationRule =>
    (v) => !v || /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/.test(v) || msg,

  url: (msg = 'URL inválida'): ValidationRule =>
    (v) => !v || /^https?:\/\/.+/.test(v) || msg,

  numeric: (msg = 'Apenas números'): ValidationRule =>
    (v) => !v || /^\d+$/.test(String(v)) || msg,

  minValue: (min: number, msg?: string): ValidationRule =>
    (v) => !v || Number(v) >= min || msg || `Valor mínimo: ${min}`,

  maxValue: (max: number, msg?: string): ValidationRule =>
    (v) => !v || Number(v) <= max || msg || `Valor máximo: ${max}`,

  salary: (msg = 'Formato de salário inválido (ex: 12000.00)'): ValidationRule =>
    (v) => !v || /^\d+(\.\d{1,2})?$/.test(String(v)) || msg,

  noSpecialChars: (msg = 'Caracteres especiais não permitidos'): ValidationRule =>
    (v) => !v || /^[a-zA-ZÀ-ÿ0-9\s]+$/.test(v) || msg,

  passwordStrength: (msg = 'Senha deve ter ao menos 8 caracteres, 1 maiúscula, 1 número'): ValidationRule =>
    (v) => !v || /^(?=.*[A-Z])(?=.*\d).{8,}$/.test(v) || msg,
} as const
```

**Uso em componentes Vue com Vuetify:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { rules } from '@/utils/validation-rules'

const form = ref<any>(null)
const nome = ref('')
const email = ref('')
const salario = ref('')

async function submit() {
  const { valid } = await form.value.validate()
  if (valid) { /* processar */ }
}
</script>

<template>
  <v-form ref="form" @submit.prevent="submit">
    <v-text-field
      v-model="nome"
      label="Nome completo"
      :rules="[rules.required(), rules.minLength(3)]"
    />
    <v-text-field
      v-model="email"
      label="Email"
      :rules="[rules.required(), rules.email()]"
    />
    <v-text-field
      v-model="salario"
      label="Salário (R$)"
      :rules="[rules.salary(), rules.minValue(1000, 'Salário mínimo: R$ 1.000')]"
      prefix="R$"
    />
    <v-btn type="submit" color="primary">Salvar</v-btn>
  </v-form>
</template>
```

---

## 4.3 Feedback do Sistema

### 4.3.1 Mensagens de Sucesso

```html
<div class="flex items-start gap-3 bg-green-50 border border-green-200 rounded-md p-4">
  <svg class="w-5 h-5 text-green-600 flex-shrink-0">...</svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-green-900">Sucesso!</h4>
    <p class="text-sm text-green-700 mt-0.5">Dados salvos com sucesso.</p>
  </div>
</div>
```

### 4.3.2 Mensagens de Erro

```html
<div class="flex items-start gap-3 bg-red-50 border border-red-200 rounded-md p-4">
  <svg class="w-5 h-5 text-red-600 flex-shrink-0">...</svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-red-900">Erro</h4>
    <p class="text-sm text-red-700 mt-0.5">Não foi possível salvar. Tente novamente.</p>
  </div>
</div>
```

---

## 4.4 Empty States

```html
<div class="py-16 text-center">
  <svg class="w-16 h-16 text-gray-400 mx-auto mb-4">...</svg>
  <h3 class="text-base font-semibold text-gray-900 mb-1">Nenhum candidato encontrado</h3>
  <p class="text-sm text-gray-600 mb-4">Comece adicionando candidatos à sua vaga</p>
  <button class="px-4 py-2 bg-gray-900 text-white text-sm font-semibold rounded">
    Adicionar Candidato
  </button>
</div>
```

---

## 4.5 Error Pages

### 4.5.1 Página 404

```html
<div class="min-h-screen flex items-center justify-center p-6">
  <div class="text-center max-w-md">
    <h1 class="text-6xl font-bold text-gray-900 mb-2">404</h1>
    <h2 class="text-2xl font-semibold text-gray-900 mb-2">Página não encontrada</h2>
    <p class="text-sm text-gray-600 mb-6">
      A página que você está procurando não existe ou foi movida.
    </p>
    <a href="/" class="inline-block px-6 py-3 bg-gray-900 text-white rounded font-semibold">
      Voltar ao início
    </a>
  </div>
</div>
```

---

## 4.6 Acessibilidade

### 4.6.1 Contraste de Cores (WCAG AA Mínimo)

| Combinação | Contraste | Status | Uso |
|------------|-----------|--------|-----|
| `gray-900` / `white` | 16.73:1 | ✅ AAA | Texto primário |
| `gray-800` / `white` | 13.36:1 | ✅ AAA | Texto body |
| `gray-600` / `white` | 7.92:1 | ✅ AAA | Texto secundário |
| `gray-500` / `white` | 5.89:1 | ✅ AA Large | Texto muted |
| `green-700` / `green-50` | 7.2:1 | ✅ AAA | Success messages |
| `red-700` / `red-50` | 7.1:1 | ✅ AAA | Error messages |
| `amber-700` / `amber-50` | 6.8:1 | ✅ AAA | Warning messages |

**IMPORTANTE:** Nunca usar `gray-400` ou mais claro como texto principal.

### 4.6.2 ARIA Labels Obrigatórios

```html
<!-- Botões com apenas ícone -->
<button aria-label="Editar candidato">
  <svg>...</svg>
</button>

<!-- Modais -->
<div role="dialog" aria-labelledby="modal-title" aria-modal="true">
  <h2 id="modal-title">Título do Modal</h2>
</div>

<!-- Inputs -->
<label for="email">Email</label>
<input 
  id="email" 
  type="email" 
  aria-required="true"
  aria-invalid="false"
  aria-describedby="email-hint"
/>
<span id="email-hint">Digite seu email principal</span>

<!-- Loading states -->
<button aria-busy="true" aria-live="polite">
  <span class="sr-only">Carregando...</span>
  <svg class="animate-spin">...</svg>
</button>
```

### 4.6.3 Keyboard Navigation

| Tecla | Ação |
|-------|------|
| **Tab** | Navegar para próximo elemento focável |
| **Shift + Tab** | Navegar para elemento anterior |
| **Enter** | Ativar botão/link |
| **Space** | Toggle checkbox/switch, ativar botão |
| **Esc** | Fechar modal/dropdown/popover |
| **Arrow Up/Down** | Navegar em menus/listas verticais |
| **Arrow Left/Right** | Navegar em tabs/menus horizontais |
| **Home** | Ir para primeiro item de lista |
| **End** | Ir para último item de lista |

**Focus Order:** Sempre seguir ordem lógica do DOM (top → bottom, left → right).

### 4.6.4 Screen Reader Support

```html
<!-- Texto visualmente oculto mas acessível para leitores -->
<span class="sr-only">Descrição para screen readers</span>

<!-- CSS para sr-only -->
<style>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>

<!-- Anúncios dinâmicos -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  Candidato salvo com sucesso
</div>
```

### 4.6.5 Color Blindness

- ✅ **SEMPRE** usar ícones junto com cores em badges de status
- ✅ **SEMPRE** usar labels textuais, não apenas cores
- ✅ Testar com simuladores (Chrome DevTools, Color Oracle)
- ❌ **NUNCA** usar apenas cor vermelha/verde para indicar erro/sucesso

**Exemplo correto:**
```html
<!-- Com ícone + cor + texto -->
<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-green-50 text-green-700 border border-green-200">
  <svg class="w-3 h-3"><!-- Check icon --></svg>
  <span>Aprovado</span>
</span>
```

### 4.6.6 Touch Targets `[Stable]`

Todos os elementos interativos devem respeitar tamanhos mínimos de toque para acessibilidade mobile (WCAG 2.5.5, WCAG 2.5.8).

| Elemento | Tamanho Mínimo | Tamanho Recomendado | Espaçamento Mínimo |
|----------|----------------|---------------------|---------------------|
| **Botões** | 44x44px | 48x48px | 8px entre botões |
| **Icon buttons** | 44x44px | 40px + 4px padding | 8px entre ícones |
| **Links em texto** | 44px height (via padding) | — | 8px entre links |
| **Checkbox/Radio** | 44x44px (área de toque) | 20px visual + padding | 12px entre opções |
| **Sidebar items** | 44px height | 48px height | 4px gap |
| **Chat suggestion cards** | 44px height | 48px height | 8px gap |

```css
.lia-touch-target {
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.lia-icon-button {
  min-height: 44px;
  min-width: 44px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
}
```

> **⚠️ Regra obrigatória:** Nenhum elemento clicável pode ter área de toque menor que 44x44px. Elementos visuais podem ser menores desde que o hit area (via padding) atinja 44px.

### 4.6.7 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 4.7 Page Layouts `[Draft]`

Templates de layout padronizados para as páginas principais da plataforma. Todos seguem o padrão conversation-first com chat como interface primária.

### 4.7.1 Layout Base (Chat + Painel)

O layout principal da plataforma: chat à esquerda (interface primária) + painel contextual à direita (suporte visual).

```
┌──────────────────────────────────────────────────────────────┐
│  Sidebar (56px)  │  Chat Area (flex-1)    │  Context Panel   │
│                  │                        │  (400px, opt.)   │
│  ┌────────────┐  │  ┌──────────────────┐  │  ┌────────────┐  │
│  │ Logo       │  │  │ Chat History     │  │  │ Panel      │  │
│  │            │  │  │ (scroll)         │  │  │ Content    │  │
│  │ Nav Items  │  │  │                  │  │  │            │  │
│  │ (icons)    │  │  │ LIA Messages     │  │  │ Cards,     │  │
│  │            │  │  │ User Messages    │  │  │ Tables,    │  │
│  │            │  │  │ Suggestions      │  │  │ Forms      │  │
│  │            │  │  │                  │  │  │            │  │
│  │            │  │  ├──────────────────┤  │  │            │  │
│  │ Settings   │  │  │ Chat Input       │  │  │            │  │
│  └────────────┘  │  └──────────────────┘  │  └────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Especificações:**

| Área | Largura | Background | Comportamento |
|------|---------|------------|---------------|
| **Sidebar** | 56px (collapsed) / 240px (expanded) | `bg-gray-50` | Collapsible, icons-only no mobile |
| **Chat Area** | `flex-1` (mín 400px) | `bg-white` | Sempre visível, scroll vertical |
| **Context Panel** | 400px (desktop) / fullscreen (mobile) | `bg-white border-l border-gray-200` | Slide-in, pode ser ocultado |

**React + Tailwind:**

```tsx
<div className="flex h-screen bg-white">
  {/* Sidebar */}
  <aside className="w-14 bg-gray-50 border-r border-gray-200 flex flex-col items-center py-4 gap-4">
    <BrainIcon className="w-8 h-8 text-[#60BED1]" />
    {/* Nav icons */}
  </aside>

  {/* Chat Area */}
  <main className="flex-1 flex flex-col min-w-0">
    <div className="flex-1 overflow-y-auto">
      {/* Chat messages */}
    </div>
    <LiaChatInput />
  </main>

  {/* Context Panel (conditional) */}
  {showPanel && (
    <aside className="w-[400px] border-l border-gray-200 overflow-y-auto">
      {/* Panel content */}
    </aside>
  )}
</div>
```

### 4.7.2 Layout Dashboard

Para páginas de KPIs e métricas. Grid responsivo com cards de dados.

```
┌──────────────────────────────────────────────────────┐
│  Sidebar  │  Header (page title + actions)           │
│           ├──────────────────────────────────────────│
│           │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│           │  │ KPI │ │ KPI │ │ KPI │ │ KPI │       │
│           │  └─────┘ └─────┘ └─────┘ └─────┘       │
│           │                                          │
│           │  ┌──────────────────┐ ┌──────────────┐  │
│           │  │  Chart/Table     │ │  Chart       │  │
│           │  │  (2/3 width)     │ │  (1/3 width) │  │
│           │  └──────────────────┘ └──────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Especificações:**

| Elemento | Grid | Gap | Comportamento |
|----------|------|-----|---------------|
| KPI row | 4 colunas (`grid-cols-4`) | 16px | Stack em 2x2 no tablet, 1 col no mobile |
| Content area | 2/3 + 1/3 (`grid-cols-3`) | 24px | Stack no tablet |
| KPI Card | Fonte Inter, valor grande | — | Border-left colored para categoria |

### 4.7.3 Layout Pipeline/Kanban

Para visualização de candidatos em etapas. Scroll horizontal para colunas.

```
┌──────────────────────────────────────────────────────────────┐
│  Sidebar  │  Header (vaga + filtros + ações)                 │
│           ├──────────────────────────────────────────────────│
│           │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│           │  │ Triagem  │ │Entrevista│ │ Oferta   │  ← scroll│
│           │  │  (count) │ │  (count) │ │  (count) │         │
│           │  │          │ │          │ │          │         │
│           │  │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │         │
│           │  │ │ Card │ │ │ │ Card │ │ │ │ Card │ │         │
│           │  │ └──────┘ │ │ └──────┘ │ │ └──────┘ │         │
│           │  │ ┌──────┐ │ │          │ │          │         │
│           │  │ │ Card │ │ │          │ │          │         │
│           │  │ └──────┘ │ │          │ │          │         │
│           │  └──────────┘ └──────────┘ └──────────┘         │
└──────────────────────────────────────────────────────────────┘
```

**Especificações:**

| Elemento | Largura | Comportamento |
|----------|---------|---------------|
| Coluna | 280px (fixa) | Scroll vertical interno |
| Card de candidato | 100% da coluna | Drag & drop entre colunas |
| Header de coluna | Título + count badge | Sticky no topo |
| Área de colunas | Scroll horizontal | `overflow-x-auto` |

### 4.7.4 Breakpoints de Layout

| Breakpoint | Largura | Sidebar | Chat Panel | Context Panel |
|------------|---------|---------|------------|---------------|
| **Mobile** | < 768px | Hidden (menu hamburger) | Full width | Overlay fullscreen |
| **Tablet** | 768-1024px | Collapsed (56px, icons) | Full width | Overlay slide-in |
| **Desktop** | 1024-1440px | Collapsed (56px) | flex-1 | 400px side panel |
| **Wide** | > 1440px | Expanded (240px) | flex-1 | 400px side panel |

---

## 4.8 Navigation Patterns `[Draft]`

### 4.8.1 Hierarquia de Navegação

A plataforma utiliza 3 níveis de navegação, do mais persistente ao mais efêmero:

```
Nível 1: SIDEBAR (persistente)
┌──────┐
│ 🏠   │  ← Sidebar colapsada (56px) com ícones
│ 💼   │     Tooltip no hover de cada ícone
│ 👥   │     Expandida (240px) em telas > 1440px
│ 📊   │
│ ⚙️   │
│      │
│ 🧑   │  ← Avatar do usuário no rodapé
└──────┘

Nível 2: CONTEXT PANEL (semi-persistente)
┌──────┬──────────────────────────────────────┐
│      │ ┌──────────────────────────────────┐ │
│ Side │ │  Chat LIA (área principal)       │ │
│ bar  │ │                                  │ │
│      │ │                                  │ │
│      │ └──────────────────────────────────┘ │
│      │ ┌──────────────────────────────────┐ │
│      │ │  Context Panel (detalhes, forms) │ │  ← Panel lateral 400px
│      │ │                                  │ │     Slide-in/out
│      │ └──────────────────────────────────┘ │
└──────┴──────────────────────────────────────┘

Nível 3: MODAL/DRAWER (efêmero)
┌──────────────────────────────────────────────┐
│              ┌──────────────────┐             │
│              │  Modal/Drawer    │             │  ← Sobreposição
│              │  (confirmações,  │             │     Fecha ao clicar fora
│              │  detalhes,       │             │     ou ESC
│              │  formulários)    │             │
│              └──────────────────┘             │
└──────────────────────────────────────────────┘
```

### 4.8.2 Princípio: LIA como Navegadora

A LIA pode navegar pela plataforma em nome do recrutador via chat:

| Comando do recrutador | Ação da LIA |
|-----------------------|-------------|
| "Mostra a vaga de Eng. de Dados" | Abre context panel com detalhes da vaga |
| "Vai pro pipeline" | Navega para a view de pipeline |
| "Me mostra o perfil do João" | Abre drawer com perfil do candidato |
| "Volta" | Retorna à view anterior |

### 4.8.3 Responsividade (ref 4.7.4)

| Breakpoint | Sidebar | Navegação principal |
|------------|---------|---------------------|
| **Mobile** (< 768px) | Menu hamburger (overlay) | Bottom tab bar ou chat fullscreen |
| **Tablet** (768-1024px) | Colapsada (56px, ícones) | Chat como view principal |
| **Desktop** (1024-1440px) | Colapsada (56px) | Chat + context panel side-by-side |
| **Wide** (> 1440px) | Expandida (240px) | Chat + context panel + detalhes |

---

## 4.9 Chat Conversation Flows `[Draft]`

Diagramas de estado para os fluxos conversacionais principais. Princípio fundamental: **LIA pergunta → recrutador responde**. A navegação entre etapas é confirmada via texto no chat, nunca por botões.

### 4.9.1 Job Creation Flow (Wizard)

Baseado em `WIZARD_STAGES` e `WIZARD_PHASES` do código real.

```
[LiaWelcome]
    │
    ▼
[pre_wizard] ── LIA: "Vamos criar uma vaga? Me conta o cargo."
    │
    ▼ (recrutador digita cargo)
[cargo] ── LIA: "Entendi! Eng. de Dados Sr. Qual o nível de senioridade?"
    │
    ▼ (recrutador responde)
[senioridade] ── LIA: "Quais são as competências técnicas essenciais?"
    │
    ▼ (recrutador lista skills)
[competencias] ── LIA: "Resumo das skills: Python, SQL, AWS. Quer adicionar mais?"
    │
    ▼ ("não" / "pode seguir")
[requisitos] ── LIA: "Qual a faixa salarial?"
    │
    ▼ (recrutador informa)
[salario] ── LIA: "Formato de trabalho: remoto, híbrido ou presencial?"
    │
    ▼ (recrutador escolhe)
[formato] ── LIA: "Quer adicionar algo mais? Benefícios, requisitos?"
    │
    ▼ ("não" / responde)
[revisao] ── LIA: "Aqui está o resumo da vaga: [card]. Posso publicar?"
    │
    ├── ("sim" / "publica") ──▶ [publicar] ── LIA: "Vaga publicada! ✅"
    │
    └── ("salva como rascunho") ──▶ [rascunho] ── LIA: "Salvo como rascunho."
```

### 4.9.2 Pipeline Action Flow

```
[Pipeline Chat]
    │
    ▼
LIA: "Selecione um candidato ou me diga o que precisa."
    │
    ▼ (recrutador menciona candidato)
LIA: "Encontrei Ana Silva no pipeline. O que quer fazer?"
    │
    ├── "avança ela" ──▶ LIA: "Mover Ana para Entrevista Técnica. Confirma?"
    │                        │
    │                        ├── "sim" ──▶ ✅ Movida + toast
    │                        └── "não" ──▶ Cancelado
    │
    ├── "rejeita" ──▶ LIA: "Motivo da rejeição?"
    │                    │
    │                    ▼ (recrutador informa)
    │                    LIA: "Rejeitar Ana por [motivo]. Confirma?"
    │
    └── "compara com o Carlos" ──▶ LIA: "Comparação Ana vs Carlos: [ActionCard]"
```

### 4.9.3 Princípios dos Fluxos Conversacionais

| Princípio | Descrição |
|-----------|-----------|
| **LIA pergunta, recrutador responde** | A LIA nunca assume — sempre confirma antes de ações |
| **Confirmação textual** | "sim", "pode", "vamos", "confirma" — LIA entende variações naturais |
| **Sem botões como interface principal** | Botões são atalhos opcionais, nunca obrigatórios |
| **Ações destrutivas exigem confirmação explícita** | Rejeitar, excluir, arquivar — sempre pergunta "Confirma?" |
| **Contexto persistente** | LIA lembra do que foi dito na conversa (sessão) |
| **Voltar é natural** | "Volta", "muda o salário", "quero mudar" — LIA entende correções |
| **Sugestões na zona do input** | Quick actions e sugestões ficam no 3.33 (zona do input), não no corpo |

---

## 4.10 Onboarding Flow `[Planned]`

> **Status `[Planned]`**: Este fluxo precisa de validação com o time de produto. A estrutura abaixo documenta os princípios e etapas esperadas, não a spec final.

### 4.10.1 Estrutura do Onboarding

```
Etapa 1: WELCOME
┌────────────────────────────────────────┐
│                                         │
│  [LiaWelcome variant="first-time"]     │
│                                         │
│  LIA: "Olá! Eu sou a LIA, sua         │
│   assistente de recrutamento. Vou te   │
│   ajudar a configurar tudo."           │
│                                         │
│  "Me conta: qual o nome da sua         │
│   empresa?"                             │
│                                         │
└────────────────────────────────────────┘
    │
    ▼ (recrutador responde)

Etapa 2: COMPANY SETUP (via chat conversacional)
    LIA: "Legal! [Empresa]. Qual o setor de atuação?"
    │
    ▼
    LIA: "Quantos funcionários vocês têm hoje?"
    │
    ▼
    LIA: "Como funciona o processo seletivo atualmente?"
    │
    ▼
    [CompanyHiringPolicy criada com base nas respostas]

Etapa 3: PRIMEIRA VAGA
    LIA: "Tudo configurado! Quer criar sua primeira vaga agora?"
    │
    ├── "sim" ──▶ [Job Creation Wizard (4.9.1)]
    └── "depois" ──▶ LIA: "Sem problemas! Quando quiser, é só me pedir."
```

### 4.10.2 Princípios do Onboarding

| Princípio | Descrição |
|-----------|-----------|
| **100% conversacional** | Nenhum formulário de onboarding — tudo via chat com a LIA |
| **Progressivo** | Coleta apenas o necessário para começar, detalhes vêm com o uso |
| **Skippable** | Recrutador pode pular etapas ("depois eu configuro isso") |
| **Dados inferidos** | LIA sugere valores com base nas respostas (ex: automação level) |
| **Sem tour/walkthrough** | A LIA ensina conforme o uso, não com tooltips/overlays |

---



---

## 4.11 Stats Bar Pattern `[Stable]` *(Novo v4.2.2)*

Barra horizontal de métricas com ícones coloridos. Padrão usado em Vagas, Funil, Agent Studio.

```jsx
<div className="flex items-center gap-6 mt-1 mb-2">
  <div className="flex items-center gap-2">
    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
    <span className="text-xs text-lia-text-secondary">
      <span className="font-semibold text-lia-text-primary">{count}</span> label
    </span>
  </div>
  <div className="flex items-center gap-1.5">
    <Icon className="w-3.5 h-3.5 text-wedo-cyan" />
    <span className="text-xs text-lia-text-secondary">
      <span className="font-semibold text-lia-text-primary">{count}</span> label
    </span>
  </div>
</div>
```

**Regras:**
- Dot pulse (animate-pulse) apenas para métrica "ao vivo" (ex: vagas ativas)
- Ícones w-3.5 h-3.5 com cor contextual
- Texto text-xs, número font-semibold text-lia-text-primary
- Não repetir informação já visível em tabs/badges

## 4.12 Mapa de Cores por Contexto `[Stable]` *(Novo v4.2.2)*

Cores usadas pontualmente para dar vida sem poluir (clean > colorido):

| Cor | Token/Class | Contexto | Onde usar |
|-----|-------------|----------|-----------|
| **Cyan** | `text-wedo-cyan` / `bg-wedo-cyan/15` | LIA, AI, busca, links | Ícones Brain/Bot, input focus glow, badges info |
| **Emerald** | `text-emerald-500` / `bg-emerald-50` | Ativo, sucesso, aprovado | Dots pulse, badges success, ícones check |
| **Amber** | `text-amber-500` / `bg-amber-50` | Pendente, atenção, warning | Ícones Clock, badges warning, filtros |
| **Rose** | `text-rose-500` / `bg-rose-50` | Urgente, erro, rejeitado | Ícones AlertTriangle, badges danger |
| **Violet** | `text-violet-500` / `bg-violet-50` | Insights, premium, análise | Ícones Brain, badges lilac |

**Regra 90/10:** Cores aparecem em no máximo 10% dos elementos visuais de uma tela.

## 4.13 Filtros Coloridos por Status `[Stable]` *(Novo v4.2.2)*

Botões de filtro mudam de cor quando ativos, seguindo o contexto do status:

```typescript
const STATUS_COLORS = {
  "Novo": { active: "bg-cyan-50 text-cyan-700 border-cyan-200", inactive: "..." },
  "Em triagem": { active: "bg-amber-50 text-amber-700 border-amber-200", inactive: "..." },
  "Aprovado": { active: "bg-emerald-50 text-emerald-700 border-emerald-200", inactive: "..." },
  "Reprovado": { active: "bg-rose-50 text-rose-700 border-rose-200", inactive: "..." },
}
```

## 4.14 Ícones Coloridos por Seção `[Stable]` *(Novo v4.2.2)*

Ícones de navegação/seção com cor fixa por área:

```typescript
const SECTION_ICON_COLORS = {
  'company-team': 'text-wedo-cyan',
  'recruitment': 'text-emerald-500',
  'communication': 'text-violet-500',
  'goals-planning': 'text-amber-500',
  'global-search': 'text-wedo-cyan',
  'integrations': 'text-emerald-500',
  'fairness-compliance': 'text-rose-500',
}
```


# PARTE 5: IMPLEMENTAÇÃO

## 5.1 Design Tokens CSS (Arquivo Completo)

```css
/* ================================================================
   WEDO TALENT - DESIGN TOKENS CSS v4.1
   Design System LIA - Light-first com Dark Mode completo
   ================================================================ */

:root {
  /* ============ CORES - BACKGROUNDS ============ */
  --lia-bg-primary: #FFFFFF;
  --lia-bg-secondary: #F9FAFB;
  --lia-bg-tertiary: #F3F4F6;
  --lia-bg-elevated: #FFFFFF;
  
  /* ============ CORES - TEXTOS ============ */
  --lia-text-primary: #111827;     /* gray-900 */
  --lia-text-body: #1F2937;        /* gray-800 */
  --lia-text-secondary: #4B5563;   /* gray-600 */
  --lia-text-muted: #5C5C5C;       /* gray-500 */
  --lia-text-disabled: #999999;    /* gray-400 */
  
  /* ============ CORES - BORDAS ============ */
  --lia-border-subtle: #D4D4D4;    /* gray-200 */
  --lia-border-default: #BEBEBE;   /* gray-300 */
  --lia-border-medium: #999999;    /* gray-400 */
  
  /* ============ CORES WEDO - ACCENT (10%) ============ */
  --wedo-cyan: #60BED1;
  --wedo-cyan-dark: #4DA8BB;
  --wedo-cyan-light: rgba(96, 190, 209, 0.1);
  
  --wedo-green: #5DA47A;
  --wedo-green-light: rgba(93, 164, 122, 0.1);
  
  --wedo-orange: #D19960;
  --wedo-orange-light: rgba(209, 153, 96, 0.1);
  
  --wedo-purple: #9860D1;
  --wedo-purple-light: rgba(152, 96, 209, 0.1);
  
  --wedo-magenta: #D160AB;
  --wedo-magenta-light: rgba(209, 96, 171, 0.1);
  
  --wedo-amber: #F59E0B;
  
  /* ============ TIPOGRAFIA - 2 FONTES ============ */
  --font-primary: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-data: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  
  /* ============ ESPAÇAMENTO (4px system) ============ */
  --space-0: 0px;
  --space-0-5: 2px;
  --space-1: 4px;
  --space-1-5: 6px;
  --space-2: 8px;
  --space-2-5: 10px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  
  /* ============ BORDER RADIUS ============ */
  --radius-sm: 4px;
  --radius-default: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* ============ SHADOWS ============ */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-default: 0 2px 4px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.10), 0 4px 8px rgba(0, 0, 0, 0.08);
  --shadow-xl: 0 16px 32px rgba(0, 0, 0, 0.12), 0 8px 16px rgba(0, 0, 0, 0.10);
  
  /* ============ FOCUS RING ============ */
  --focus-ring: 0 0 0 3px rgba(17, 24, 39, 0.2);
  
  /* ============ TRANSITIONS ============ */
  --transition-fast: 100ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-default: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============ DARK MODE ============ */
.dark,
[data-theme="dark"] {
  --lia-bg-primary: #0F1113;
  --lia-bg-secondary: #1A1D1F;
  --lia-bg-tertiary: #26292B;
  --lia-bg-elevated: #1A1D1F;
  
  --lia-text-primary: #F9FAFB;
  --lia-text-body: #D4D4D4;
  --lia-text-secondary: #999999;
  --lia-text-muted: #5C5C5C;
  --lia-text-disabled: #4B5563;
  
  --lia-border-subtle: #374151;
  --lia-border-default: #4B5563;
  --lia-border-medium: #5C5C5C;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --lia-bg-primary: #0F1113;
    --lia-bg-secondary: #1A1D1F;
    --lia-bg-tertiary: #26292B;
    --lia-text-primary: #F9FAFB;
    --lia-text-body: #D4D4D4;
    --lia-text-secondary: #999999;
    --lia-border-subtle: #374151;
    --lia-border-default: #4B5563;
  }
}

/* ============ UTILITY CLASSES ============ */

.focus-ring:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 5.2 Design Tokens TypeScript (Arquivo Completo)

```typescript
// ================================================================
// WEDO TALENT - DESIGN TOKENS TYPESCRIPT v4.1
// Design System LIA - Type-safe tokens
// ================================================================

export const colors = {
  bg: {
    primary: '#FFFFFF',
    secondary: '#F9FAFB',
    tertiary: '#F3F4F6',
    elevated: '#FFFFFF',
  },
  text: {
    primary: '#111827',
    body: '#1F2937',
    secondary: '#4B5563',
    muted: '#5C5C5C',
    disabled: '#999999',
  },
  border: {
    subtle: '#D4D4D4',
    default: '#BEBEBE',
    medium: '#999999',
  },
  wedo: {
    cyan: '#60BED1',
    cyanDark: '#4DA8BB',
    cyanLight: 'rgba(96, 190, 209, 0.1)',
    green: '#5DA47A',
    greenLight: 'rgba(93, 164, 122, 0.1)',
    orange: '#D19960',
    orangeLight: 'rgba(209, 153, 96, 0.1)',
    purple: '#9860D1',
    purpleLight: 'rgba(152, 96, 209, 0.1)',
    magenta: '#D160AB',
    magentaLight: 'rgba(209, 96, 171, 0.1)',
    amber: '#F59E0B',
  },
} as const;

export const typography = {
  fonts: {
    primary: "'Open Sans', sans-serif",
    data: "'Inter', sans-serif",
  },
} as const;

export const textStyles = {
  h1: 'text-2xl font-semibold text-gray-900 font-[Open_Sans]',
  h2: 'text-lg font-semibold text-gray-900 font-[Open_Sans]',
  h3: 'text-sm font-semibold text-gray-900 font-[Open_Sans]',
  h4: 'text-[13px] font-medium text-gray-800 font-[Open_Sans]',
  body: 'text-[13px] text-gray-800 font-[Open_Sans]',
  bodySm: 'text-xs text-gray-700 font-[Open_Sans]',
  label: 'text-[11px] font-medium text-gray-800 font-[Open_Sans]',
  caption: 'text-[10px] text-gray-600 font-[Open_Sans]',
  kpiLg: 'text-[32px] font-bold text-gray-900 font-[Inter]',
  kpiMd: 'text-2xl font-bold text-gray-900 font-[Inter]',
  kpiSm: 'text-lg font-semibold text-gray-900 font-[Inter]',
  metric: 'text-sm font-medium text-gray-800 font-[Inter]',
  sidebarItem: 'text-[13px] font-medium text-gray-600 font-[Open_Sans]',
  sidebarActive: 'text-[13px] font-semibold text-gray-900 font-[Open_Sans]',
} as const;

export const buttonStyles = {
  primary: 'px-4 py-2 bg-gray-900 text-white text-[13px] font-semibold rounded hover:bg-gray-800 focus:ring-2 focus:ring-gray-900/20 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all',
  secondary: 'px-4 py-2 bg-gray-100 text-gray-700 text-[13px] font-semibold rounded hover:bg-gray-200 focus:ring-2 focus:ring-gray-500/20 transition-all',
  outline: 'px-4 py-2 border border-gray-300 text-gray-700 text-[13px] font-semibold rounded hover:bg-gray-50 focus:ring-2 focus:ring-gray-500/20 transition-all',
  ghost: 'px-4 py-2 text-gray-600 text-[13px] font-medium rounded hover:bg-gray-100 focus:ring-2 focus:ring-gray-500/20 transition-all',
  destructive: 'px-4 py-2 bg-red-600 text-white text-[13px] font-semibold rounded hover:bg-red-700 focus:ring-2 focus:ring-red-500/20 transition-all',
} as const;

export const cardStyles = {
  default: 'bg-white rounded-md shadow-sm border border-gray-200',
  elevated: 'bg-white rounded-md shadow-md border border-gray-200',
  interactive: 'bg-white rounded-md shadow-sm border border-gray-200 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer',
  flat: 'bg-gray-50 rounded-md border border-gray-200',
} as const;

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
```

---

## 5.3 Classes Utilitárias

### 5.3.1 Classes de Texto

```css
.wedo-text-title     { color: #111827; }  /* gray-900 */
.wedo-text-body      { color: #1F2937; }  /* gray-800 */
.wedo-text-secondary { color: #4B5563; }  /* gray-600 */
.wedo-text-muted     { color: #5C5C5C; /* escurecido v4.2.2 */ }  /* gray-500 */

/* Dark mode automático */
.dark .wedo-text-title     { color: #F9FAFB; }
.dark .wedo-text-body      { color: #D4D4D4; }
.dark .wedo-text-secondary { color: #999999; }
.dark .wedo-text-muted     { color: #5C5C5C; /* escurecido v4.2.2 */ }
```

### 5.3.2 Classes WeDo (Cores de Acento)

```css
/* Texto */
.text-wedo-cyan    { color: #60BED1 !important; }
.text-wedo-green   { color: #5DA47A !important; }
.text-wedo-orange  { color: #D19960 !important; }
.text-wedo-purple  { color: #9860D1 !important; }
.text-wedo-magenta { color: #D160AB !important; }

/* Background light (10% opacidade) */
.bg-wedo-cyan-light    { background-color: rgba(96,190,209,0.1) !important; }
.bg-wedo-green-light   { background-color: rgba(93,164,122,0.1) !important; }
.bg-wedo-orange-light  { background-color: rgba(209,153,96,0.1) !important; }
.bg-wedo-purple-light  { background-color: rgba(152,96,209,0.1) !important; }
.bg-wedo-magenta-light { background-color: rgba(209,96,171,0.1) !important; }
```

---

## 5.4 tailwind.config.js de Referência `[Stable]`

```javascript
// tailwind.config.js — Configuração unificada WeDo Talent DS v4.1
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    fontFamily: {
      sans: ['"Open Sans"', 'system-ui', 'sans-serif'],
      mono: ['"Inter"', 'system-ui', 'sans-serif'],
    },
    extend: {
      colors: {
        // Cores WeDo Accent (10%)
        wedo: {
          cyan:    '#60BED1',
          green:   '#5DA47A',
          orange:  '#D19960',
          purple:  '#9860D1',
          magenta: '#D160AB',
        },
        // Semantic aliases
        lia: {
          bg: {
            primary:   'var(--lia-bg-primary)',
            secondary: 'var(--lia-bg-secondary)',
            tertiary:  'var(--lia-bg-tertiary)',
            elevated:  'var(--lia-bg-elevated)',
          },
          text: {
            primary:   'var(--lia-text-primary)',
            body:      'var(--lia-text-body)',
            secondary: 'var(--lia-text-secondary)',
            muted:     'var(--lia-text-muted)',
            disabled:  'var(--lia-text-disabled)',
          },
          border: {
            subtle:  'var(--lia-border-subtle)',
            default: 'var(--lia-border-default)',
            medium:  'var(--lia-border-medium)',
          },
        },
      },
      fontSize: {
        'h1':      ['1.5rem',    { lineHeight: '2rem',    fontWeight: '600' }],
        'h2':      ['1.125rem',  { lineHeight: '1.75rem', fontWeight: '600' }],
        'h3':      ['0.875rem',  { lineHeight: '1.25rem', fontWeight: '600' }],
        'h4':      ['0.8125rem', { lineHeight: '1.125rem', fontWeight: '500' }],
        'body':    ['0.8125rem', { lineHeight: '1.25rem', fontWeight: '400' }],
        'body-sm': ['0.75rem',   { lineHeight: '1rem',    fontWeight: '400' }],
        'label':   ['0.6875rem', { lineHeight: '1rem',    fontWeight: '500' }],
        'caption': ['0.625rem',  { lineHeight: '0.875rem', fontWeight: '400' }],
        'kpi-lg':  ['2rem',      { lineHeight: '2.5rem',  fontWeight: '700' }],
        'kpi-md':  ['1.5rem',    { lineHeight: '2rem',    fontWeight: '700' }],
        'kpi-sm':  ['1.125rem',  { lineHeight: '1.5rem',  fontWeight: '600' }],
      },
      borderRadius: {
        'sm':   '4px',
        DEFAULT: '6px',
        'md':   '8px',
        'lg':   '12px',
        'xl':   '16px',
      },
      boxShadow: {
        'sm':  '0 1px 2px rgba(0,0,0,0.05)',
        DEFAULT: '0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'md':  '0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06)',
        'lg':  '0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.08)',
        'xl':  '0 16px 32px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.10)',
      },
      spacing: {
        '4.5': '1.125rem',
        '13':  '3.25rem',
        '15':  '3.75rem',
        '18':  '4.5rem',
        '68':  '17rem',     // sidebar width (272px)
        '64':  '16rem',     // sidebar collapsed (256px)
      },
      transitionTimingFunction: {
        'lia': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        'fast': '100ms',
        'default': '150ms',
        'slow': '200ms',
      },
    },
  },
  plugins: [],
}
```

---

## 5.5 Integração shadcn/ui `[Stable]`

O stack React atual usa shadcn/ui como base de componentes. Aqui está como mapear os tokens do DS para o theme do shadcn.

### 5.5.1 Componentes shadcn Aprovados

| shadcn Component | DS Equivalente | Customização Necessária |
|-----------------|----------------|-------------------------|
| `Button` | 3.1 Botões | Variantes custom (5), font-weight 600, rounded 6px |
| `Card` | 3.3 Cards | `shadow-sm`, border `gray-200`, padding 24px |
| `Dialog` | 3.4 Modais | 5 tamanhos fixos (XS-XL), overlay `bg-black/40` |
| `Input` | 3.5 Inputs | `h-9`, border `gray-300`, focus `ring-gray-900/20` |
| `Select` | 3.5 Inputs | Mesmo estilo de input, com `ArrowUpDown` icon |
| `Badge` | 3.6 Badges | `rounded-full`, font-size 10px, cores semânticas |
| `Tooltip` | 3.10 Tooltips | `bg-gray-900 text-white`, font-size 12px |
| `Tabs` | 3.13 Tabs | Underline style, cor `gray-900` active |
| `Table` | 3.8 Tabelas | Header `bg-gray-50`, hover `bg-gray-50/50` |
| `Separator` | 3.23 Dividers | `bg-gray-200` |
| `Skeleton` | 3.18 Skeleton | `bg-gray-200 animate-pulse` |
| `Alert` | 3.19 Alerts | 4 variantes semânticas |
| `Avatar` | 3.20 Avatars | `rounded-full`, 4 tamanhos |
| `Switch` | 3.16 Toggles | `bg-gray-200` off, `bg-gray-900` on |
| `Command` | 3.27 Command Palette | Ctrl+K trigger, search overlay |

### 5.5.2 CSS Variables para shadcn Theme

```css
/* globals.css — Mapeamento DS → shadcn theme */
@layer base {
  :root {
    --background: 0 0% 100%;           /* #FFFFFF */
    --foreground: 222 47% 11%;         /* #111827 (gray-900) */
    --card: 0 0% 100%;
    --card-foreground: 222 47% 11%;
    --popover: 0 0% 100%;
    --popover-foreground: 222 47% 11%;
    --primary: 222 47% 11%;            /* gray-900 */
    --primary-foreground: 0 0% 100%;   /* white */
    --secondary: 220 14% 96%;          /* gray-100 */
    --secondary-foreground: 220 9% 46%;/* gray-600 */
    --muted: 220 14% 96%;
    --muted-foreground: 220 9% 46%;
    --accent: 191 52% 63%;             /* #60BED1 (WeDo Cyan) */
    --accent-foreground: 222 47% 11%;
    --destructive: 0 84% 60%;          /* red-500 */
    --destructive-foreground: 0 0% 100%;
    --border: 220 13% 91%;             /* gray-200 */
    --input: 220 13% 91%;
    --ring: 222 47% 11%;               /* gray-900 for focus rings */
    --radius: 0.375rem;                /* 6px — DS default */
  }

  .dark {
    --background: 220 16% 7%;          /* #0F1113 */
    --foreground: 220 14% 96%;         /* #F9FAFB */
    --card: 220 11% 11%;               /* #1A1D1F */
    --card-foreground: 220 14% 96%;
    --popover: 220 9% 16%;             /* #26292B */
    --popover-foreground: 220 14% 96%;
    --primary: 0 0% 100%;              /* Inversão: branco em dark */
    --primary-foreground: 222 47% 11%;
    --secondary: 217 10% 30%;          /* gray-700 */
    --secondary-foreground: 220 14% 96%;
    --muted: 217 10% 30%;
    --muted-foreground: 220 9% 46%;
    --accent: 191 52% 63%;             /* WeDo Cyan mantém */
    --accent-foreground: 220 14% 96%;
    --destructive: 0 63% 31%;
    --destructive-foreground: 0 0% 100%;
    --border: 217 19% 27%;             /* gray-700 */
    --input: 217 19% 27%;
    --ring: 0 0% 100%;
    --radius: 0.375rem;
  }
}
```

### 5.5.3 Exemplo: Button com shadcn + DS

```tsx
// components/ui/button.tsx — Variantes customizadas do DS
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap font-sans text-[13px] transition-all duration-150 ease-lia focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-0 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:     "bg-gray-900 text-white font-semibold rounded hover:bg-gray-800 focus-visible:ring-gray-900/20",
        secondary:   "bg-gray-100 text-gray-700 font-semibold rounded hover:bg-gray-200 focus-visible:ring-gray-500/20",
        outline:     "border border-gray-300 text-gray-700 font-semibold rounded bg-transparent hover:bg-gray-50 focus-visible:ring-gray-500/20",
        ghost:       "text-gray-600 font-medium rounded hover:bg-gray-100 focus-visible:ring-gray-500/20",
        destructive: "bg-red-600 text-white font-semibold rounded hover:bg-red-700 focus-visible:ring-red-600/20",
      },
      size: {
        xs: "h-7 px-2 text-[11px]",
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-4 text-[13px]",
        lg: "h-10 px-6 text-sm",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
)
```

> **Nota:** Esta seção fornece os padrões `cva` (class-variance-authority) requeridos para componentização React profissional. Cada componente core deve seguir este padrão.

---

## 5.6 Integração Vuetify

```typescript
// vuetify.config.ts
import { createVuetify } from 'vuetify'

export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#111827',
          secondary: '#4B5563',
          background: '#FFFFFF',
          surface: '#F9FAFB',
          'surface-variant': '#F3F4F6',
          error: '#DC2626',
          warning: '#F59E0B',
          success: '#16A34A',
          info: '#2563EB',
          'on-primary': '#FFFFFF',
          'on-secondary': '#FFFFFF',
          'on-background': '#111827',
          'on-surface': '#111827',
          'on-error': '#FFFFFF',
          'on-warning': '#FFFFFF',
          'on-success': '#FFFFFF',
          'on-info': '#FFFFFF',
          // Cores WeDo customizadas
          'wedo-cyan': '#60BED1',
          'wedo-green': '#5DA47A',
          'wedo-orange': '#D19960',
          'wedo-purple': '#9860D1',
          'wedo-magenta': '#D160AB',
        },
      },
      dark: {
        colors: {
          primary: '#F9FAFB',
          secondary: '#999999',
          background: '#0F1113',
          surface: '#1A1D1F',
          'surface-variant': '#26292B',
          error: '#F87171',
          warning: '#FBBF24',
          success: '#4ADE80',
          info: '#60A5FA',
          'on-primary': '#111827',
          'on-secondary': '#111827',
          'on-background': '#F9FAFB',
          'on-surface': '#F9FAFB',
          // Cores WeDo mantêm-se iguais em dark mode
          'wedo-cyan': '#60BED1',
          'wedo-green': '#5DA47A',
          'wedo-orange': '#D19960',
          'wedo-purple': '#9860D1',
          'wedo-magenta': '#D160AB',
        },
      },
    },
  },
  defaults: {
    // === BOTÕES ===
    VBtn: {
      variant: 'flat',
      rounded: 'md',
      density: 'comfortable',
      color: 'primary',
    },
    // === CARDS ===
    VCard: {
      elevation: 1,
      rounded: 'md',
      variant: 'elevated',
    },
    // === INPUTS & FORMS ===
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      hideDetails: 'auto',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      hideDetails: 'auto',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      hideDetails: 'auto',
    },
    VAutocomplete: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      hideDetails: 'auto',
    },
    VCombobox: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      hideDetails: 'auto',
    },
    VFileInput: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
      prependIcon: 'mdi-paperclip',
      hideDetails: 'auto',
    },
    // === CONTROLES ===
    VCheckbox: {
      color: 'primary',
      density: 'comfortable',
      hideDetails: 'auto',
    },
    VRadio: {
      color: 'primary',
      density: 'comfortable',
    },
    VRadioGroup: {
      color: 'primary',
      density: 'comfortable',
      hideDetails: 'auto',
    },
    VSwitch: {
      color: 'primary',
      density: 'comfortable',
      hideDetails: 'auto',
      inset: true,
    },
    VSlider: {
      color: 'primary',
      thumbLabel: true,
      hideDetails: 'auto',
    },
    // === DADOS ===
    VDataTable: {
      density: 'comfortable',
      hover: true,
      fixedHeader: true,
    },
    VChip: {
      size: 'small',
      variant: 'outlined',
      rounded: 'sm', // Tags/filtros técnicos. Para badges/skills pill, usar rounded="pill" inline
    },
    VBadge: {
      color: 'primary',
    },
    // === NAVEGAÇÃO ===
    VTabs: {
      color: 'primary',
      density: 'comfortable',
    },
    VTab: {
      density: 'comfortable',
    },
    VPagination: {
      color: 'primary',
      density: 'comfortable',
      rounded: 'md',
    },
    VBreadcrumbs: {
      density: 'comfortable',
    },
    VNavigationDrawer: {
      width: 256,
      color: 'background',
    },
    // === FEEDBACK ===
    VDialog: {
      maxWidth: 512,
      persistent: false,
      scrollable: true,
    },
    VSnackbar: {
      timeout: 4000,
      location: 'bottom right',
    },
    VTooltip: {
      location: 'top',
    },
    VMenu: {
      closeOnContentClick: true,
    },
    // === LOADING ===
    VProgressLinear: {
      color: 'primary',
      rounded: true,
      height: 8,
    },
    VProgressCircular: {
      color: 'primary',
    },
    VSkeletonLoader: {
      elevation: 0,
    },
    // === LAYOUT ===
    VExpansionPanels: {
      variant: 'accordion',
    },
    VDivider: {
      color: 'grey-lighten-3',
    },
    VAvatar: {
      size: 40,
      rounded: 'circle',
      color: 'grey-lighten-2',
    },
  },
})
```

---

## 5.7 Integração Vuetify Avançada

### 5.7.1 Variáveis SASS Vuetify

Para customização profunda, criar arquivo `settings.scss` importado antes do Vuetify:

```scss
// settings.scss - Importar ANTES do Vuetify
// @use 'vuetify/settings' with ( ... )

// ============ TIPOGRAFIA ============
$body-font-family: 'Open Sans', sans-serif;
$heading-font-family: 'Open Sans', sans-serif;

// ============ BORDER RADIUS ============
$border-radius-root: 6px;
$button-border-radius: 6px;
$card-border-radius: 8px;
$chip-border-radius: 4px;
$dialog-border-radius: 8px;
$expansion-panel-border-radius: 8px;
$sheet-border-radius: 8px;
$tooltip-border-radius: 6px;

// ============ BOTÕES ============
$button-font-weight: 600;
$button-font-size: 0.8125rem;
$button-height: 36px;
$button-icon-font-size: 16px;

// ============ INPUTS ============
$input-font-size: 0.875rem;
$label-font-size: 0.6875rem;

// ============ CARDS ============
$card-title-font-size: 0.875rem;
$card-title-font-weight: 600;
$card-subtitle-font-size: 0.75rem;
$card-text-font-size: 0.8125rem;

// ============ TABELAS ============
$table-header-font-size: 0.6875rem;
$table-row-font-size: 0.8125rem;

// ============ CHIPS ============
$chip-font-size: 0.625rem;
$chip-font-weight: 500;

// ============ SOMBRAS ============
$shadow-key-umbra-opacity: 0.05;
$shadow-key-penumbra-opacity: 0.04;
$shadow-key-ambient-opacity: 0.03;

// ============ TRANSIÇÕES ============
$transition-fast-in-fast-out: cubic-bezier(0.4, 0, 0.2, 1);
$primary-transition: 150ms $transition-fast-in-fast-out;

// ============ Z-INDEX ============
$tooltip-z-index: 2100;
$snackbar-z-index: 2200;
$dialog-z-index: 2400;
```

### 5.7.2 global.scss - Overrides Vuetify

```scss
// global.scss - Importar DEPOIS do Vuetify

// ============ TIPOGRAFIA GLOBAL ============
.v-application {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.8125rem;
  color: #1F2937;
}

// ============ FOCUS RING PADRÃO ============
.v-btn:focus-visible,
.v-text-field .v-field:focus-within,
.v-checkbox .v-input__control:focus-within,
.v-radio .v-input__control:focus-within,
.v-switch .v-input__control:focus-within,
.v-select .v-field:focus-within,
.v-tab:focus-visible,
.v-chip:focus-visible,
.v-pagination__item:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2) !important;
}

// ============ BOTÕES ============
.v-btn {
  font-family: 'Open Sans', sans-serif !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: normal !important;
}

.v-btn--variant-flat {
  &.bg-primary {
    background-color: #111827 !important;
    &:hover { background-color: #1F2937 !important; }
  }
}

// ============ INPUTS ============
.v-field {
  font-family: 'Open Sans', sans-serif !important;
  border-radius: 6px !important;
}

.v-field--variant-outlined .v-field__outline {
  --v-field-border-opacity: 1;
  color: #BEBEBE !important;
}

.v-label {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.6875rem !important;
  font-weight: 500 !important;
}

// ============ CARDS ============
.v-card {
  border: 1px solid #D4D4D4 !important;
}

.v-card-title {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

.v-card-text {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.8125rem !important;
  color: #4B5563 !important;
}

// ============ TABELAS ============
.v-data-table {
  font-family: 'Open Sans', sans-serif !important;
  border: 1px solid #D4D4D4 !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

.v-data-table-header th {
  font-family: 'Inter', sans-serif !important;
  font-size: 0.6875rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  color: #1F2937 !important;
  background-color: #F9FAFB !important;
}

.v-data-table__td {
  font-size: 0.8125rem !important;
  color: #1F2937 !important;
}

// ============ CHIPS / BADGES ============
.v-chip {
  font-family: 'Open Sans', sans-serif !important;
  font-weight: 500 !important;
  text-transform: none !important;
}

// ============ TABS ============
.v-tab {
  font-family: 'Open Sans', sans-serif !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: normal !important;
}

// ============ NAVIGATION DRAWER ============
.v-navigation-drawer {
  border-right: 1px solid #D4D4D4 !important;
}

.v-list-item-title {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.8125rem !important;
}

// ============ DIALOG / MODAL ============
.v-dialog > .v-overlay__content > .v-card {
  border-radius: 8px !important;
}

.v-overlay__scrim {
  background-color: rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(4px) !important;
}

// ============ SNACKBAR ============
.v-snackbar__wrapper {
  font-family: 'Open Sans', sans-serif !important;
  border-radius: 8px !important;
}

// ============ TOOLTIP ============
.v-tooltip > .v-overlay__content {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.75rem !important;
  background-color: #111827 !important;
  color: #FFFFFF !important;
  border-radius: 6px !important;
  padding: 6px 12px !important;
}

// ============ DADOS NUMÉRICOS (Inter) ============
.v-data-table__td .metric,
.kpi-value,
[data-font="data"] {
  font-family: 'Inter', sans-serif !important;
  font-variant-numeric: tabular-nums;
}

// ============ DARK MODE ============
.v-theme--dark {
  .v-card {
    border-color: #374151 !important;
  }
  .v-data-table {
    border-color: #374151 !important;
  }
  .v-navigation-drawer {
    border-right-color: #374151 !important;
  }
  .v-field--variant-outlined .v-field__outline {
    color: #4B5563 !important;
  }
}
```

### 5.7.3 Composable useDesignTokens()

```typescript
// composables/useDesignTokens.ts
import { computed } from 'vue'
import { useTheme } from 'vuetify'

export interface DesignTokens {
  colors: {
    bg: { primary: string; secondary: string; tertiary: string; elevated: string }
    text: { primary: string; body: string; secondary: string; muted: string; disabled: string }
    border: { subtle: string; default: string; medium: string }
    wedo: {
      cyan: string; cyanDark: string; cyanLight: string
      green: string; greenLight: string
      orange: string; orangeLight: string
      purple: string; purpleLight: string
      magenta: string; magentaLight: string
      amber: string
    }
    status: {
      success: { bg: string; text: string; border: string }
      warning: { bg: string; text: string; border: string }
      error: { bg: string; text: string; border: string }
      info: { bg: string; text: string; border: string }
    }
  }
  fonts: { primary: string; data: string }
  spacing: Record<string, string>
  radius: Record<string, string>
  shadows: Record<string, string>
  focusRing: string
  transitions: { fast: string; default: string; slow: string }
}

const lightTokens: DesignTokens = {
  colors: {
    bg: { primary: '#FFFFFF', secondary: '#F9FAFB', tertiary: '#F3F4F6', elevated: '#FFFFFF' },
    text: { primary: '#111827', body: '#1F2937', secondary: '#4B5563', muted: '#5C5C5C', disabled: '#999999' },
    border: { subtle: '#D4D4D4', default: '#BEBEBE', medium: '#999999' },
    wedo: {
      cyan: '#60BED1', cyanDark: '#4DA8BB', cyanLight: 'rgba(96,190,209,0.1)',
      green: '#5DA47A', greenLight: 'rgba(93,164,122,0.1)',
      orange: '#D19960', orangeLight: 'rgba(209,153,96,0.1)',
      purple: '#9860D1', purpleLight: 'rgba(152,96,209,0.1)',
      magenta: '#D160AB', magentaLight: 'rgba(209,96,171,0.1)',
      amber: '#F59E0B',
    },
    status: {
      success: { bg: '#F0FDF4', text: '#15803D', border: '#BBF7D0' },
      warning: { bg: '#FFFBEB', text: '#B45309', border: '#FDE68A' },
      error: { bg: '#FEF2F2', text: '#B91C1C', border: '#FECACA' },
      info: { bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
    },
  },
  fonts: { primary: "'Open Sans', sans-serif", data: "'Inter', sans-serif" },
  spacing: { '0': '0px', '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px', '6': '24px', '8': '32px' },
  radius: { sm: '4px', default: '6px', md: '8px', lg: '12px', xl: '16px', full: '9999px' },
  shadows: {
    sm: '0 1px 2px rgba(0,0,0,0.05)',
    default: '0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
    md: '0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06)',
    lg: '0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.08)',
  },
  focusRing: '0 0 0 3px rgba(17, 24, 39, 0.2)',
  transitions: { fast: '100ms cubic-bezier(0.4, 0, 0.2, 1)', default: '150ms cubic-bezier(0.4, 0, 0.2, 1)', slow: '200ms cubic-bezier(0.4, 0, 0.2, 1)' },
}

const darkTokens: DesignTokens = {
  ...lightTokens,
  colors: {
    ...lightTokens.colors,
    bg: { primary: '#0F1113', secondary: '#1A1D1F', tertiary: '#26292B', elevated: '#1A1D1F' },
    text: { primary: '#F9FAFB', body: '#D4D4D4', secondary: '#999999', muted: '#5C5C5C', disabled: '#4B5563' },
    border: { subtle: '#374151', default: '#4B5563', medium: '#5C5C5C' },
    status: {
      success: { bg: 'rgba(22,163,74,0.15)', text: '#4ADE80', border: 'rgba(22,163,74,0.3)' },
      warning: { bg: 'rgba(245,158,11,0.15)', text: '#FBBF24', border: 'rgba(245,158,11,0.3)' },
      error: { bg: 'rgba(220,38,38,0.15)', text: '#F87171', border: 'rgba(220,38,38,0.3)' },
      info: { bg: 'rgba(37,99,235,0.15)', text: '#60A5FA', border: 'rgba(37,99,235,0.3)' },
    },
  },
  shadows: {
    sm: '0 1px 2px rgba(0,0,0,0.3)',
    default: '0 2px 4px rgba(0,0,0,0.3)',
    md: '0 4px 6px rgba(0,0,0,0.4)',
    lg: '0 10px 15px rgba(0,0,0,0.5)',
  },
}

export function useDesignTokens() {
  const theme = useTheme()
  const isDark = computed(() => theme.global.current.value.dark)
  const tokens = computed<DesignTokens>(() => isDark.value ? darkTokens : lightTokens)

  return {
    tokens,
    isDark,
    colors: computed(() => tokens.value.colors),
    fonts: computed(() => tokens.value.fonts),
    spacing: computed(() => tokens.value.spacing),
    radius: computed(() => tokens.value.radius),
    shadows: computed(() => tokens.value.shadows),
    focusRing: computed(() => tokens.value.focusRing),
    transitions: computed(() => tokens.value.transitions),
  }
}
```

**Uso em componentes Vue:**

```vue
<script setup lang="ts">
import { useDesignTokens } from '@/composables/useDesignTokens'

const { colors, fonts, isDark } = useDesignTokens()
</script>

<template>
  <div :style="{ color: colors.text.primary, fontFamily: fonts.primary }">
    <span :style="{ color: colors.wedo.cyan }">LIA</span>
  </div>
</template>
```

### 5.7.4 Plugin Nuxt para Design System

```typescript
// plugins/design-system.ts
import { defineNuxtPlugin } from '#app'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Importar SASS overrides (deve vir ANTES do Vuetify CSS)
import '@/assets/styles/settings.scss'
import 'vuetify/styles'
import '@/assets/styles/global.scss'

export default defineNuxtPlugin((nuxtApp) => {
  const vuetify = createVuetify({
    components,
    directives,
    // ... usar a configuração completa da seção 5.6
  })

  nuxtApp.vueApp.use(vuetify)
})
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  css: [
    '@/assets/styles/fonts.css',
    '@/assets/styles/tokens.css',
  ],
  build: {
    transpile: ['vuetify'],
  },
  vite: {
    define: {
      'process.env.DEBUG': false,
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@use "@/assets/styles/settings.scss" as *;',
        },
      },
    },
  },
})
```

```css
/* assets/styles/fonts.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&display=swap');
```

**Estrutura de arquivos recomendada:**

```
assets/
  styles/
    fonts.css            ← Google Fonts import
    tokens.css           ← CSS custom properties (seção 5.1)
    settings.scss        ← Variáveis SASS Vuetify (seção 5.7.1)
    global.scss          ← Overrides Vuetify (seção 5.7.2)
composables/
  useDesignTokens.ts     ← Composable type-safe (seção 5.7.3)
plugins/
  design-system.ts       ← Plugin Nuxt (seção 5.7.4)
```

### 5.7.5 Dark Mode Toggle (Vue + Vuetify)

```typescript
// composables/useThemeToggle.ts
import { computed, watch } from 'vue'
import { useTheme } from 'vuetify'

const STORAGE_KEY = 'lia-theme-preference'

export function useThemeToggle() {
  const theme = useTheme()

  const isDark = computed({
    get: () => theme.global.current.value.dark,
    set: (value: boolean) => {
      theme.global.name.value = value ? 'dark' : 'light'
    },
  })

  function toggle() {
    isDark.value = !isDark.value
  }

  function setTheme(mode: 'light' | 'dark' | 'system') {
    if (mode === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = prefersDark
      localStorage.setItem(STORAGE_KEY, 'system')
    } else {
      isDark.value = mode === 'dark'
      localStorage.setItem(STORAGE_KEY, mode)
    }
  }

  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY) as 'light' | 'dark' | 'system' | null
    if (saved) {
      setTheme(saved)
    } else {
      setTheme('light') // Light-first por padrão
    }
  }

  // Ouvir mudanças do sistema
  watch(() => window.matchMedia('(prefers-color-scheme: dark)').matches, (prefersDark) => {
    if (localStorage.getItem(STORAGE_KEY) === 'system') {
      isDark.value = prefersDark
    }
  })

  return { isDark, toggle, setTheme, initTheme }
}
```

**Uso no layout principal:**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useThemeToggle } from '@/composables/useThemeToggle'
import { Sun, Moon, Monitor } from 'lucide-vue-next'

const { isDark, setTheme, initTheme } = useThemeToggle()

onMounted(() => initTheme())
</script>

<template>
  <v-btn-toggle v-model="themeMode" mandatory density="compact">
    <v-btn value="light" icon size="small">
      <Sun :size="16" />
    </v-btn>
    <v-btn value="dark" icon size="small">
      <Moon :size="16" />
    </v-btn>
    <v-btn value="system" icon size="small">
      <Monitor :size="16" />
    </v-btn>
  </v-btn-toggle>
</template>
```

### 5.7.6 Padrões de Slots Vuetify

Documentação de como usar slots nos componentes Vuetify seguindo o design system LIA:

#### v-btn (Botão com ícone)

```vue
<v-btn color="primary">
  <template #prepend>
    <Plus :size="16" />
  </template>
  Criar Vaga
</v-btn>

<!-- Botão apenas ícone -->
<v-btn icon variant="text" size="small" aria-label="Editar candidato">
  <Pencil :size="16" />
  <v-tooltip activator="parent" location="top">Editar</v-tooltip>
</v-btn>
```

#### v-text-field (Input com slots)

```vue
<v-text-field
  label="Buscar candidatos"
  placeholder="Nome, email ou cargo..."
  variant="outlined"
  density="comfortable"
>
  <template #prepend-inner>
    <Search :size="16" class="text-grey-darken-1" />
  </template>
  <template #append-inner>
    <v-btn icon variant="text" size="x-small" @click="clearSearch">
      <X :size="14" />
    </v-btn>
  </template>
</v-text-field>
```

#### v-dialog (Modal padrão LIA)

```vue
<v-dialog v-model="dialog" max-width="512" scrollable>
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between pa-4">
      <div class="d-flex align-center ga-2">
        <component :is="headerIcon" :size="20" class="text-grey-darken-1" />
        <span class="text-sm font-weight-semibold">Título do Modal</span>
      </div>
      <v-btn icon="mdi-close" variant="text" size="small" @click="dialog = false" />
    </v-card-title>

    <v-divider />

    <v-card-text class="pa-6">
      <!-- Conteúdo -->
    </v-card-text>

    <v-divider />

    <v-card-actions class="pa-4 justify-end ga-2" style="background: #F9FAFB;">
      <v-btn variant="outlined" @click="dialog = false">Cancelar</v-btn>
      <v-btn color="primary" @click="confirm">Confirmar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

#### v-data-table (Tabela com slots customizados)

```vue
<v-data-table
  :headers="headers"
  :items="candidates"
  hover
  density="comfortable"
>
  <template #item.name="{ item }">
    <div class="d-flex align-center ga-3">
      <v-avatar size="32" color="grey-lighten-2">
        <span class="text-caption font-weight-semibold">{{ item.initials }}</span>
      </v-avatar>
      <div>
        <div class="text-sm font-weight-semibold text-grey-darken-4">{{ item.name }}</div>
        <div class="text-caption text-grey-darken-1">{{ item.email }}</div>
      </div>
    </div>
  </template>

  <template #item.status="{ item }">
    <v-chip
      :color="getStatusColor(item.status)"
      size="small"
      variant="outlined"
    >
      {{ item.status }}
    </v-chip>
  </template>

  <template #item.score="{ item }">
    <span style="font-family: 'Inter', sans-serif; font-variant-numeric: tabular-nums;">
      {{ item.score }}
    </span>
  </template>

  <template #item.actions="{ item }">
    <v-menu>
      <template #activator="{ props }">
        <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props" />
      </template>
      <v-list density="compact">
        <v-list-item @click="editCandidate(item)" prepend-icon="mdi-pencil">
          Editar
        </v-list-item>
        <v-divider />
        <v-list-item @click="deleteCandidate(item)" prepend-icon="mdi-delete" class="text-red">
          Excluir
        </v-list-item>
      </v-list>
    </v-menu>
  </template>
</v-data-table>
```

#### v-tabs (Tabs padrão)

```vue
<v-tabs v-model="activeTab" color="primary">
  <v-tab value="details">
    <template #prepend>
      <FileText :size="16" />
    </template>
    Detalhes
  </v-tab>
  <v-tab value="candidates">
    <template #prepend>
      <Users :size="16" />
    </template>
    Candidatos
    <template #append>
      <v-chip size="x-small" color="primary" class="ml-2">12</v-chip>
    </template>
  </v-tab>
</v-tabs>

<v-tabs-window v-model="activeTab">
  <v-tabs-window-item value="details">...</v-tabs-window-item>
  <v-tabs-window-item value="candidates">...</v-tabs-window-item>
</v-tabs-window>
```

#### v-navigation-drawer (Sidebar LIA)

```vue
<v-navigation-drawer permanent width="256" color="background">
  <template #prepend>
    <div class="d-flex align-center ga-2 pa-4">
      <Brain :size="24" class="text-wedo-cyan" />
      <span class="text-lg font-weight-bold text-grey-darken-4" style="font-family: 'Open Sans';">
        LIA
      </span>
    </div>
  </template>

  <v-list density="comfortable" nav>
    <v-list-item
      v-for="item in menuItems"
      :key="item.title"
      :prepend-icon="item.icon"
      :title="item.title"
      :value="item.value"
      :active="item.active"
      color="primary"
      rounded="md"
    />
  </v-list>

  <template #append>
    <div class="pa-4">
      <v-divider class="mb-4" />
      <v-list-item prepend-icon="mdi-cog" title="Configurações" />
    </div>
  </template>
</v-navigation-drawer>
```

---

## 5.8 Mapeamento Tailwind ↔ Vuetify

### 5.8.1 Cores

| Tailwind | Vuetify 3 |
|----------|-----------|
| `bg-gray-900` | `color="grey-darken-4"` |
| `bg-gray-100` | `class="bg-grey-lighten-4"` |
| `text-gray-800` | `class="text-grey-darken-3"` |
| `border-gray-200` | `class="border-grey-lighten-3"` |
| `shadow-sm` | `elevation="1"` |
| `shadow-md` | `elevation="4"` |

### 5.8.2 Tipografia

| Tailwind | Vuetify 3 |
|----------|-----------|
| `text-2xl font-bold` | `class="text-h3"` |
| `text-lg font-semibold` | `class="text-h4"` |
| `text-sm` | `class="text-body-2"` |
| `text-xs` | `class="text-caption"` |

### 5.8.3 Layout

| Tailwind | Vuetify 3 |
|----------|-----------|
| `flex` | `class="d-flex"` |
| `flex items-center` | `class="d-flex align-center"` |
| `flex justify-between` | `class="d-flex justify-space-between"` |
| `gap-2` | `style="gap: 8px"` |
| `p-4` | `class="pa-4"` |

### 5.8.4 Componentes

| shadcn/Tailwind | Vuetify 3 |
|-----------------|-----------|
| `<Card>` | `<v-card variant="outlined">` |
| `<Button>` | `<v-btn variant="flat">` |
| `<Button variant="outline">` | `<v-btn variant="outlined">` |
| `<Input>` | `<v-text-field variant="outlined" density="compact">` |
| `<Badge>` | `<v-chip size="small">` |
| `<Dialog>` | `<v-dialog>` |
| `<Tooltip>` | `<v-tooltip>` |
| `<Tabs>` | `<v-tabs>` |

---

## 5.9 Tabela de Migração v4.0 → v4.1

### 5.9.1 O Que Mudou

| Aspecto | v4.0 | v4.1 | Ação |
|---------|------|------|------|
| **Estrutura** | 10 seções componentes | 25 seções componentes | Adicionar 2.11-2.25 |
| **Efeitos** | Não tinha Glassmorphism | Seção 1.10 Glassmorphism | Novo |
| **Acessibilidade** | Básica (3.6) | Expandida (WCAG, keyboard, etc) | Atualizar |
| **Vuetify** | Parcial | Mapeamento completo | Adicionar |
| **Focus Ring** | Variado | Padronizado `ring-2 ring-gray-900/20` | Padronizar |

### 5.9.2 O Que NÃO Mudou

| Aspecto | Valor | Motivo |
|---------|-------|--------|
| **Tipografia** | 3 fontes (Open Sans 85%, Inter 10%, JetBrains Mono 5%) | Expandido na v4.2.1 - JetBrains Mono adicionado |
| **Espaçamento** | Base 4px | Consistência existente |
| **Dark Mode** | Implementação completa | Já funcional |
| **Classes CSS** | `.lia-h1`, `.lia-sidebar-item`, etc | Compatibilidade |
| **Cores WeDo** | Mesmos hex codes | Identidade de marca |
| **Botão Primary** | Preto (gray-900) | Decisão de design |

### 5.9.3 Checklist de Migração

```bash
# 1. Verificar que tipografia usa 2 fontes (Source Serif 4 removido)
grep -r "Source Serif 4" --include="*.css" --include="*.tsx" --include="*.vue"  # NÃO deve existir - substituir por Open Sans

# 2. Verificar espaçamento base 4px
grep -r "space-" --include="*.css"  # Valores devem ser múltiplos de 4px

# 3. Atualizar focus rings para padrão
grep -r "ring-\[#60BED1\]" --include="*.tsx"  # Substituir por ring-gray-900/20

# 4. Adicionar novos componentes (2.11-2.25) conforme necessário
```

---

# PARTE 6: CATÁLOGOS

## 6.1 Catálogo Completo de Ícones

### 6.1.1 Bibliotecas

| Stack | Biblioteca | Instalação |
|-------|-----------|------------|
| **React (atual)** | Lucide React | `npm install lucide-react` |
| **Vue (migração)** | Lucide Vue Next | `npm install lucide-vue-next` |
| **Vuetify (MDI)** | Material Design Icons | `npm install @mdi/font` (ou `@mdi/js` para tree-shaking) |

**Setup MDI no Vuetify:**

```typescript
// Para @mdi/font (mais simples):
import '@mdi/font/css/materialdesignicons.css'

// Para @mdi/js (tree-shaking, menor bundle):
import { aliases, mdi } from 'vuetify/iconSets/mdi-svg'
import { createVuetify } from 'vuetify'

export default createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
})
```

### 6.1.2 Ícones por Categoria

#### Navigation

| Lucide (React/Vue) | MDI (Vuetify) | Tamanho | Uso |
|--------------------|---------------|---------|-----|
| `Home` | `mdi-home` | 18px | Dashboard |
| `Briefcase` | `mdi-briefcase` | 18px | Vagas |
| `Users` | `mdi-account-group` | 18px | Candidatos |
| `BarChart3` | `mdi-chart-bar` | 18px | Relatórios |
| `Settings` | `mdi-cog` | 18px | Configurações |
| `Bell` | `mdi-bell` | 18px | Notificações |
| `Search` | `mdi-magnify` | 18px | Busca |
| `ChevronLeft` | `mdi-chevron-left` | 16px | Voltar |
| `ChevronRight` | `mdi-chevron-right` | 16px | Avançar |
| `ChevronDown` | `mdi-chevron-down` | 14px | Dropdown |
| `Menu` | `mdi-menu` | 18px | Menu hamburger |
| `LayoutDashboard` | `mdi-view-dashboard` | 18px | Dashboard alt |

#### Actions

| Lucide (React/Vue) | MDI (Vuetify) | Tamanho | Uso |
|--------------------|---------------|---------|-----|
| `Plus` | `mdi-plus` | 16px | Criar/Adicionar |
| `Pencil` | `mdi-pencil` | 16px | Editar |
| `Trash2` | `mdi-delete` | 16px | Excluir |
| `Download` | `mdi-download` | 16px | Download |
| `Upload` | `mdi-upload` | 16px | Upload |
| `Check` | `mdi-check` | 16px | Confirmar |
| `X` | `mdi-close` | 16px | Fechar/Cancelar |
| `Copy` | `mdi-content-copy` | 16px | Copiar |
| `Filter` | `mdi-filter` | 16px | Filtrar |
| `Save` | `mdi-content-save` | 16px | Salvar |
| `RefreshCw` | `mdi-refresh` | 16px | Atualizar |
| `MoreVertical` | `mdi-dots-vertical` | 16px | Menu contextual |
| `ExternalLink` | `mdi-open-in-new` | 16px | Link externo |
| `Send` | `mdi-send` | 16px | Enviar |
| `Paperclip` | `mdi-paperclip` | 16px | Anexar |

#### Status

| Lucide (React/Vue) | MDI (Vuetify) | Cor | Uso |
|--------------------|---------------|-----|-----|
| `CheckCircle` | `mdi-check-circle` | green-600 | Sucesso |
| `XCircle` | `mdi-close-circle` | red-600 | Erro |
| `AlertTriangle` | `mdi-alert` | amber-600 | Alerta |
| `Info` | `mdi-information` | blue-600 | Informação |
| `Loader2` | `mdi-loading` (+ `mdi-spin`) | gray-600 | Carregando |
| `Clock` | `mdi-clock-outline` | gray-500 | Pendente |
| `Eye` | `mdi-eye` | gray-600 | Visualizar |
| `EyeOff` | `mdi-eye-off` | gray-400 | Ocultar |

#### LIA (AI)

| Lucide (React/Vue) | MDI (Vuetify) | Cor | Uso |
|--------------------|---------------|-----|-----|
| `Brain` | `mdi-brain` | cyan (#60BED1) | LIA padrão |
| `BrainCircuit` | `mdi-head-snowflake` | cyan (#60BED1) | LIA processando |
| `Sparkles` | `mdi-creation` | cyan (#60BED1) | Sugestão AI |
| `Wand2` | `mdi-auto-fix` | cyan (#60BED1) | Ação AI |
| `MessageCircle` | `mdi-message-text` | cyan (#60BED1) | Chat LIA |

#### Data & Forms

| Lucide (React/Vue) | MDI (Vuetify) | Tamanho | Uso |
|--------------------|---------------|---------|-----|
| `FileText` | `mdi-file-document` | 16px | Documento |
| `Calendar` | `mdi-calendar` | 16px | Data |
| `Mail` | `mdi-email` | 16px | Email |
| `Phone` | `mdi-phone` | 16px | Telefone |
| `MapPin` | `mdi-map-marker` | 16px | Localização |
| `Link` | `mdi-link` | 16px | URL |
| `Star` | `mdi-star` | 16px | Favorito |
| `Tag` | `mdi-tag` | 16px | Tag/Label |
| `Hash` | `mdi-pound` | 16px | Número/ID |
| `DollarSign` | `mdi-currency-usd` | 16px | Valor monetário |

#### Theme

| Lucide (React/Vue) | MDI (Vuetify) | Tamanho | Uso |
|--------------------|---------------|---------|-----|
| `Sun` | `mdi-white-balance-sunny` | 16px | Tema claro |
| `Moon` | `mdi-weather-night` | 16px | Tema escuro |
| `Monitor` | `mdi-monitor` | 16px | Tema sistema |

---

## 6.2 Catálogo de Cores por Contexto

| Contexto | Cor Principal | Background Light | Text | Exemplo |
|----------|---------------|------------------|------|---------|
| **LIA/Vagas** | `#60BED1` | `rgba(96,190,209,0.1)` | `#0E7490` | Badges LIA |
| **Candidatos** | `#5DA47A` | `rgba(93,164,122,0.1)` | `#166534` | Badges candidato |
| **Tempo/Prazo** | `#D19960` | `rgba(209,153,96,0.1)` | `#92400E` | Urgência |
| **Insights/IA** | `#9860D1` | `rgba(152,96,209,0.1)` | `#6D28D9` | Análises |
| **Sucesso** | `#16A34A` | `#F0FDF4` | `#15803D` | Aprovado |
| **Erro** | `#DC2626` | `#FEF2F2` | `#B91C1C` | Rejeitado |
| **Warning** | `#F59E0B` | `#FFFBEB` | `#B45309` | Atenção |

---

## 6.3 Catálogo de Modais (58+)

### Categorias de Modais

| Categoria | Quantidade | Tamanho Típico |
|-----------|------------|----------------|
| **Confirmação** | 12 | XS (384px) |
| **Formulários Simples** | 18 | S-M (448-512px) |
| **Formulários Complexos** | 15 | L (672px) |
| **Visualização** | 8 | XL (896px) |
| **Seleção** | 5 | M (512px) |

### Modais Mais Usados

| Modal | Tamanho | Uso |
|-------|---------|-----|
| **Confirmar Exclusão** | XS | Deletar vaga/candidato |
| **Criar Vaga** | L | Form de nova vaga |
| **Editar Candidato** | M | Form de edição |
| **Visualizar Análise LIA** | XL | Dashboard de insights |
| **Selecionar Template** | M | Escolher template de email |

---

# CHANGELOG

## v4.2.0 (Fevereiro 2026 - Expansão de Maturidade)

### Novidades
- ✅ **Props API + Do's & Don'ts** para 25 componentes (3.5–3.29): tabelas de props tipadas + regras de uso
- ✅ **3.34 Pipeline Kanban Card** `[Stable]`: documentação completa baseada no código real (KanbanCard.tsx), anatomia, indicadores inteligentes, lógica de cores do score, KanbanColumn sub-componente
- ✅ **3.35 LiaConversation** `[Draft]`: container de chat com auto-scroll, stick-to-bottom, gerenciamento de scroll
- ✅ **3.36 LiaResponse** `[Draft]`: renderizador de resposta com streaming progressivo, cursor piscando, ActionCards inline
- ✅ **3.37 LiaWelcome** `[Draft]`: empty state conversacional (variantes first-time e new-conversation), sem botões
- ✅ **3.38 Data Visualization** `[Draft]`: paleta de cores para gráficos (90/10), tipos por contexto, KPI Stat Card spec
- ✅ **2.4 Data Formats** `[Draft]`: formatação padronizada PT-BR (datas, números, salários, scores, listas), regras de font por tipo de dado
- ✅ **4.8 Navigation Patterns** `[Draft]`: hierarquia 3 níveis (Sidebar → Context Panel → Modal), LIA como navegadora
- ✅ **4.9 Chat Conversation Flows** `[Draft]`: diagramas de estado ASCII para Job Creation Wizard e Pipeline Action
- ✅ **4.10 Onboarding Flow** `[Planned]`: fluxo de primeiro acesso 100% conversacional
- ✅ **3.33 nota de posicionamento**: sugestões na zona do input, nunca no corpo das mensagens
- ✅ **Maturidade elevada**: 6.8/10 → 7.5/10 (38 componentes documentados, 10 padrões, tooling completo)

## v4.1.2 (Fevereiro 2026 - Fase 2 Funil de Talentos)

### Novidades
- ✅ **2.29 Qualification Badge:** Indicador de nível de qualificação da vaga (Alta=Purple/Crown, Média=Orange/Briefcase, Baixa=Gray/HardHat)
- ✅ Classificação automática via LLM (Gemini) com override manual pelo recrutador
- ✅ Tooltip com confiança, reasoning e descrição do impacto na busca
- ✅ Estados: classificado, override manual (*), classificando (spinner), não classificado (dashed)
- ✅ Implementações React+Tailwind (protótipo) e Vuetify (produção)

## v4.1.1 (Fevereiro 2026 - Fase 1 Funil de Talentos)

### Novidades
- ✅ **2.26 Feedback Buttons (Like/Dislike):** Componente ThumbsUp/ThumbsDown para cards de candidato no funil de talentos
- ✅ **2.27 Sort Dropdown (Ordenação):** Dropdown de ordenação para resultados de busca (Relevância, Score, Nome, Experiência)
- ✅ **2.28 Load More Button (Carregar Mais):** Botão de paginação incremental (10 em 10) com counter de progresso
- ✅ Implementações React+Tailwind (protótipo) e Vuetify (produção) para cada componente

## v4.1 (Fevereiro 2026)

### Novidades
- ✅ Seções de componentes expandidas (2.11-2.25)
- ✅ Seção 1.10 Glassmorphism & Effects
- ✅ Acessibilidade expandida (WCAG, keyboard nav, screen reader, color blindness, reduced motion)
- ✅ Mapeamento completo Tailwind ↔ Vuetify
- ✅ Focus Ring padronizado (`ring-2 ring-gray-900/20`)
- ✅ Tokens CSS/TS simplificados (--font-primary e --font-data apenas)
- ✅ Seção de migração v4.0 → v4.1
- ✅ **Tipografia:** 3 fontes (Open Sans 85% + Inter 10% + JetBrains Mono 5%) - v4.2.1 reconciliado com código real
- ✅ **Vuetify defaults expandidos:** 25 componentes com props padrão (seção 5.6)
- ✅ **Variáveis SASS Vuetify:** settings.scss para customização profunda (seção 5.7.1)
- ✅ **global.scss:** Overrides Vuetify completos com dark mode (seção 5.7.2)
- ✅ **Composable useDesignTokens():** API type-safe para tokens em Vue 3 (seção 5.7.3)
- ✅ **Plugin Nuxt:** Setup completo design system (seção 5.7.4)
- ✅ **Dark mode toggle Vue:** useThemeToggle() com persistência (seção 5.7.5)
- ✅ **Padrões de slots Vuetify:** v-btn, v-text-field, v-dialog, v-data-table, v-tabs, v-navigation-drawer (seção 5.7.6)
- ✅ **Validação Vuetify:** Rules padrão em português (seção 4.2.3)
- ✅ **Transições CSS ↔ Vuetify:** Mapeamento com exemplos Vue (seção 1.9.4)
- ✅ **Catálogo de ícones expandido:** 65+ ícones com coluna MDI completa (seção 6.1)
- ✅ **Agent skills sincronizados:** 5 skills + reference files atualizados

### Mantido (Compatibilidade)
- ✅ Espaçamento base 4px
- ✅ Dark mode completo
- ✅ Todas as classes CSS existentes (.lia-h1, .lia-sidebar-item, etc.)
- ✅ Cores WeDo e tokens de cor

---

*Documento gerado em Fevereiro 2026 - Design System LIA v4.1*
