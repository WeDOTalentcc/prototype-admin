# Design System LIA v4.1 - Documento Oficial

> **Versão:** 4.1  
> **Atualizado:** Fevereiro 2026  
> **Inspiração:** ElevenLabs UI (ui.elevenlabs.io)  
> **Filosofia:** Interface monocromática clean (90% grays) + acentos WeDo estratégicos (10%)  
> **Compatibilidade:** Light-first, Vuetify 3.x, Tailwind CSS

---

## Sumário

### PARTE 1: FUNDAMENTOS
- [1.1 Princípios de Design](#11-princípios-de-design)
- [1.2 Paleta de Cores](#12-paleta-de-cores)
- [1.3 Tipografia](#13-tipografia)
- [1.4 Espaçamento](#14-espaçamento)
- [1.5 Grid & Layout](#15-grid--layout)
- [1.6 Breakpoints](#16-breakpoints)
- [1.7 Sombras & Elevação](#17-sombras--elevação)
- [1.8 Bordas & Raios](#18-bordas--raios)
- [1.9 Motion & Animation](#19-motion--animation)
- [1.10 Glassmorphism & Effects](#110-glassmorphism--effects)
- [1.11 Elemento Visual LIA (Brain Icon)](#111-elemento-visual-lia-brain-icon)

### PARTE 2: COMPONENTES
- [2.1 Botões](#21-botões)
- [2.2 Inputs & Forms](#22-inputs--forms)
- [2.3 Cards](#23-cards)
- [2.4 Modais](#24-modais)
- [2.5 Tabelas](#25-tabelas)
- [2.6 Badges & Tags](#26-badges--tags)
- [2.7 Tooltips & Popovers](#27-tooltips--popovers)
- [2.8 Toasts & Alerts](#28-toasts--alerts)
- [2.9 Navigation](#29-navigation)
- [2.10 Loading States](#210-loading-states)
- [2.11 Dropdowns & Menus](#211-dropdowns--menus)
- [2.12 Accordions](#212-accordions)
- [2.13 Progress Indicators](#213-progress-indicators)
- [2.14 Avatars](#214-avatars)
- [2.15 Breadcrumbs](#215-breadcrumbs)
- [2.16 Pagination](#216-pagination)
- [2.17 Switches & Toggles](#217-switches--toggles)
- [2.18 Radio Buttons](#218-radio-buttons)
- [2.19 Checkboxes](#219-checkboxes)
- [2.20 Date Pickers](#220-date-pickers)
- [2.21 File Upload](#221-file-upload)
- [2.22 Sliders](#222-sliders)
- [2.23 Tabs](#223-tabs)
- [2.24 Dividers](#224-dividers)
- [2.25 Skeleton Loaders](#225-skeleton-loaders)
- [2.26 Feedback Buttons (Like/Dislike)](#226-feedback-buttons-likedislike)
- [2.27 Sort Dropdown (Ordenação)](#227-sort-dropdown-ordenação)
- [2.28 Load More Button (Carregar Mais)](#228-load-more-button-carregar-mais)
- [2.29 Qualification Badge (Classificação de Vaga)](#229-qualification-badge-classificação-de-vaga)

### PARTE 3: PADRÕES
- [3.1 Estados de Componentes](#31-estados-de-componentes)
- [3.2 Formulários](#32-formulários)
- [3.3 Feedback do Sistema](#33-feedback-do-sistema)
- [3.4 Empty States](#34-empty-states)
- [3.5 Error Pages](#35-error-pages)
- [3.6 Acessibilidade](#36-acessibilidade)

### PARTE 4: IMPLEMENTAÇÃO
- [4.1 Design Tokens CSS (Arquivo Completo)](#41-design-tokens-css-arquivo-completo)
- [4.2 Design Tokens TypeScript (Arquivo Completo)](#42-design-tokens-typescript-arquivo-completo)
- [4.3 Classes Utilitárias](#43-classes-utilitárias)
- [4.4 Integração Vuetify](#44-integração-vuetify)
- [4.5 Mapeamento Tailwind ↔ Vuetify](#45-mapeamento-tailwind--vuetify)
- [4.6 Tabela de Migração v4.0 → v4.1](#46-tabela-de-migração-v40--v41)

### PARTE 5: CATÁLOGOS
- [5.1 Catálogo Completo de Ícones](#51-catálogo-completo-de-ícones)
- [5.2 Catálogo de Cores por Contexto](#52-catálogo-de-cores-por-contexto)
- [5.3 Catálogo de Modais (58+)](#53-catálogo-de-modais-58)

---

# PARTE 1: FUNDAMENTOS

## 1.1 Princípios de Design

### Filosofia Core

Inspirado na interface clean e monocromática da ElevenLabs, o Design System LIA v4.1 segue:

| Proporção | Uso |
|-----------|-----|
| **90%** | Escala de cinzas (Gray Scale) - backgrounds, textos, bordas |
| **10%** | Cores de acento WeDo - apenas para destaques estratégicos |

### Princípios Fundamentais

```
✅ FAZER:
├── Texto escuro (nunca preto puro #000000)
├── Backgrounds claros com hierarquia de profundidade
├── Bordas quase invisíveis ou ausentes
├── Sombras sutis para elevação
├── Cores de acento usadas com parcimônia
├── Botões primários PRETOS (bg-gray-900)
├── Tipografia consistente (Open Sans + Inter)
├── Contraste alto para legibilidade (WCAG AA mínimo)
└── Glassmorphism sutil em cards e modais

❌ EVITAR:
├── Gradientes
├── Bordas grossas
├── Cores saturadas demais
├── Animações excessivas
├── Botões coloridos como ação primária
├── Múltiplas fontes decorativas
└── Preto puro (#000000) ou branco puro em texto
```

### Hierarquia Visual

1. **Peso Tipográfico**: Negrito (600/700) para elementos importantes
2. **Tons de Cinza**: Diferentes shades para profundidade (gray-50 até gray-900)
3. **Bordas Sutis**: Quase invisíveis (`border-gray-200`)
4. **Sombras Leves**: Elevação sutil sem dramatismo
5. **Cores como Destaque**: Apenas para chamar atenção específica (10%)

### Regra 90/10

**90% Monocromático:**
- Todos os backgrounds (white, gray-50, gray-100)
- Texto principal (gray-800, gray-900)
- Bordas (gray-200, gray-300)
- Botões principais (gray-900)
- Cards, containers, inputs

**10% Cor:**
- Brain icon LIA (cyan #60BED1)
- Badges contextuais (cyan, green, orange, purple, magenta)
- Status indicators (success green, warning amber, error red)
- Ícones contextuais específicos
- Nunca em botões primários ou ações principais

---

## 1.2 Paleta de Cores

### 1.2.1 Sistema Monocromático (90% da interface)

#### Backgrounds

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-bg-primary` | `#FFFFFF` | `bg-white` | `bg-white` | Fundo principal da página |
| `--lia-bg-secondary` | `#F9FAFB` | `bg-gray-50` | `bg-grey-lighten-5` | Cards, painéis, sidebars |
| `--lia-bg-tertiary` | `#F3F4F6` | `bg-gray-100` | `bg-grey-lighten-4` | Hover states, disabled |
| `--lia-bg-elevated` | `#FFFFFF` | `bg-white` | `bg-white elevation-1` | Cards elevados (com shadow) |

#### Textos

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-text-primary` | `#111827` | `text-gray-900` | `text-grey-darken-4` | Títulos, headings |
| `--lia-text-body` | `#1F2937` | `text-gray-800` | `text-grey-darken-3` | Texto principal, labels |
| `--lia-text-secondary` | `#4B5563` | `text-gray-600` | `text-grey-darken-1` | Descrições, captions |
| `--lia-text-muted` | `#6B7280` | `text-gray-500` | `text-grey` | Placeholders, hints |
| `--lia-text-disabled` | `#9CA3AF` | `text-gray-400` | `text-grey-lighten-1` | Texto desabilitado |

#### Bordas

| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-border-subtle` | `#E5E7EB` | `border-gray-200` | `border-grey-lighten-3` | Bordas padrão (quase invisíveis) |
| `--lia-border-default` | `#D1D5DB` | `border-gray-300` | `border-grey-lighten-2` | Bordas com destaque |
| `--lia-border-medium` | `#9CA3AF` | `border-gray-400` | `border-grey-lighten-1` | Bordas fortes |

#### Botão Primary (Preto) - AÇÃO PRINCIPAL

| Estado | Background | Text | Border |
|--------|------------|------|--------|
| **Default** | `bg-gray-900` (#111827) | `text-white` | none |
| **Hover** | `bg-gray-800` (#1F2937) | `text-white` | none |
| **Active** | `bg-gray-700` (#374151) | `text-white` | none |
| **Focus** | `bg-gray-900` + ring | `text-white` | `ring-2 ring-gray-900/20` |
| **Disabled** | `bg-gray-300` (#D1D5DB) | `text-gray-500` | none |

**IMPORTANTE:** Botão primário é SEMPRE preto. Cores WeDo são APENAS para badges, ícones e indicadores.

### 1.2.2 Cores de Acento WeDo (10% estratégico)

**REGRA DE OURO**: Usar APENAS para badges semânticos, ícones contextuais e status. NUNCA para botões primários.

| Cor | Hex | Token | RGB | Uso Semântico |
|-----|-----|-------|-----|---------------|
| **Cyan** | `#60BED1` | `--wedo-cyan` | 96,190,209 | **Brain LIA**, Vagas, Automação |
| **Cyan Dark** | `#4DA8BB` | `--wedo-cyan-dark` | 77,168,187 | Hover states, ícones ativos |
| **Green** | `#5DA47A` | `--wedo-green` | 93,164,122 | Candidatos, Sucesso, Aprovação |
| **Orange** | `#D19960` | `--wedo-orange` | 209,153,96 | Tempo, Prazos, Alertas médios |
| **Purple** | `#9860D1` | `--wedo-purple` | 152,96,209 | Insights, IA, Análises |
| **Magenta** | `#D160AB` | `--wedo-magenta` | 209,96,171 | Urgência crítica, Prioridade alta |
| **Amber** | `#F59E0B` | `--wedo-amber` | 245,158,11 | Warning vibrante, Atenção |

#### Variações Dark (para hover e estados ativos)

| Cor Base | Dark Variant | Uso |
|----------|--------------|-----|
| Cyan `#60BED1` | `#4DA8BB` | Hover em badges/ícones cyan |
| Green `#5DA47A` | `#4B8862` | Hover em badges/ícones green |
| Orange `#D19960` | `#B8814D` | Hover em badges/ícones orange |
| Purple `#9860D1` | `#7F4DB8` | Hover em badges/ícones purple |
| Magenta `#D160AB` | `#B84D92` | Hover em badges/ícones magenta |

#### Variações Light (para backgrounds sutis - 10% opacidade)

| Cor | Background Token | Valor RGBA | Uso |
|-----|------------------|------------|-----|
| **Cyan Light** | `--wedo-cyan-light` | `rgba(96,190,209,0.1)` | Background badges LIA |
| **Green Light** | `--wedo-green-light` | `rgba(93,164,122,0.1)` | Background badges candidatos |
| **Orange Light** | `--wedo-orange-light` | `rgba(209,153,96,0.1)` | Background badges tempo |
| **Purple Light** | `--wedo-purple-light` | `rgba(152,96,209,0.1)` | Background badges insights |
| **Magenta Light** | `--wedo-magenta-light` | `rgba(209,96,171,0.1)` | Background badges urgência |

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
| `--lia-text-body` | `#1F2937` | `#E5E7EB` |
| `--lia-text-secondary` | `#4B5563` | `#9CA3AF` |
| `--lia-text-muted` | `#6B7280` | `#6B7280` |
| `--lia-text-disabled` | `#9CA3AF` | `#4B5563` |
| `--lia-border-subtle` | `#E5E7EB` | `#374151` |
| `--lia-border-default` | `#D1D5DB` | `#4B5563` |
| `--lia-border-medium` | `#9CA3AF` | `#6B7280` |

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
| **Sidebar** | `bg-white border-gray-200` | `bg-[#0F1113] border-gray-800` |
| **Table Header** | `bg-gray-50` | `bg-[#1A1D1F]` |
| **Table Row Hover** | `bg-gray-50` | `bg-[#26292B]` |

#### Sombras em Dark Mode

| Token | Light | Dark |
|-------|-------|------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | `0 4px 6px rgba(0,0,0,0.4)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | `0 10px 15px rgba(0,0,0,0.5)` |

**Nota**: Aumentar opacidade das sombras em dark mode para compensar fundo escuro.

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
  --lia-border-subtle: #E5E7EB;
  --lia-border-default: #D1D5DB;
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
  --lia-text-body: #E5E7EB;
  --lia-text-secondary: #9CA3AF;
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
| `gray-200` | `#E5E7EB` | Bordas sutis |
| `gray-300` | `#D1D5DB` | Bordas padrão |
| `gray-400` | `#9CA3AF` | Texto disabled, bordas fortes |
| `gray-500` | `#6B7280` | Texto muted, placeholders |
| `gray-600` | `#4B5563` | Texto secundário |
| `gray-700` | `#374151` | Texto com destaque |
| `gray-800` | `#1F2937` | Texto corpo principal |
| `gray-900` | `#111827` | Títulos, botões primários |
| `gray-950` | `#030712` | Texto de máximo contraste ✅ |

**Nota**: `gray-950` é válido no Tailwind v3+ e deve ser usado quando necessário máximo contraste.

### 1.2.6 Cores Deprecadas (Eliminar na Padronização)

| Cor Atual | Substituir Por | Classe Tailwind | Motivo |
|-----------|---------------|-----------------|--------|
| `#FAFAFA` | `#F9FAFB` | `gray-50` | Inconsistente, usar padrão Tailwind |
| `#E8E8E8` | `#E5E7EB` | `gray-200` | Não padronizado |
| `#666666` | `#6B7280` | `gray-500` | Não padronizado |
| `#999999` | `#9CA3AF` | `gray-400` | Não padronizado |
| `#2D2D2D` | `#1F2937` | `gray-800` | Não padronizado |
| `#E4EBEF` | `#E5E7EB` | `gray-200` | Azulado inconsistente |

---

## 1.3 Tipografia

### 1.3.1 Sistema de 2 Fontes

| Fonte | Uso | Proporção | Contexto |
|-------|-----|-----------|----------|
| **Open Sans** | Fonte principal: títulos, labels, botões, textos, navigation, sidebar | **60%** | Toda a UI e navegação |
| **Inter** | Dados numéricos, métricas, KPIs, tabelas, dashboards | **40%** | Dashboards, relatórios, dados |

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&display=swap');

:root {
  --font-primary: "Open Sans", sans-serif;      /* 60% - UI geral + navigation */
  --font-data: "Inter", sans-serif;             /* 40% - números/métricas/dados */
}
```

> **NOTA v4.1:** Source Serif 4 foi removido. Sidebar e navigation agora usam Open Sans para simplificar a stack tipográfica e facilitar a migração para Vuetify.

### 1.3.2 Hierarquia Tipográfica Completa

#### Open Sans (60% - Interface Principal + Navigation)

| Elemento | Tamanho | Peso | Cor | Line Height | Uso |
|----------|---------|------|-----|-------------|-----|
| **H1** | 24px | 600 | gray-900 | 1.2 | Título de página |
| **H2** | 18px | 600 | gray-900 | 1.25 | Título de seção |
| **H3** | 14px | 600 | gray-900 | 1.3 | Título de card |
| **H4** | 13px | 500 | gray-800 | 1.35 | Subtítulo |
| **Body** | 13px | 400 | gray-800 | 1.5 | Texto principal |
| **Body SM** | 12px | 400 | gray-700 | 1.5 | Texto secundário |
| **Label** | 11px | 500 | gray-800 | 1.4 | Labels de form |
| **Caption** | 10px | 400 | gray-600 | 1.3 | Captions, metadados |
| **Button** | 13px | 600 | - | 1.2 | Texto de botões |

#### Inter (40% - Dados e Métricas)

| Elemento | Tamanho | Peso | Cor | Uso |
|----------|---------|------|-----|-----|
| **KPI Large** | 32px | 700 | gray-900 | Números grandes de dashboard |
| **KPI Medium** | 24px | 700 | gray-900 | Valores de cards |
| **KPI Small** | 18px | 600 | gray-900 | Valores inline |
| **Metric** | 14px | 500 | gray-800 | Dados de tabela |
| **Metric SM** | 12px | 500 | gray-700 | Dados secundários |
| **Percentage** | 14px | 600 | contextual | Variações (+ verde, - vermelho) |

**IMPORTANTE:** Usar `font-feature-settings: 'tnum' 1` para números tabulares em tabelas.

#### Open Sans - Navigation & Sidebar

| Elemento | Tamanho | Peso | Cor | Uso |
|----------|---------|------|-----|-----|
| **Sidebar Item** | 13px | 500 | gray-600 | Item de menu inativo |
| **Sidebar Active** | 13px | 600 | gray-900 | Item de menu ativo |
| **Sidebar Section** | 11px | 600 | gray-500 | Título de grupo/seção |

### 1.3.3 Classes CSS de Tipografia

```css
/* ========================================
   OPEN SANS - Títulos, UI e Navigation (60%)
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
   INTER - Métricas, Dados e Body (40%)
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
  color: #6B7280;
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
  color: #6B7280;
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
| **Tight** | 8px | `gap-2` | `ga-2` |
| **Default** | 16px | `gap-4` | `ga-4` |
| **Comfortable** | 24px | `gap-6` | `ga-6` |
| **Spacious** | 32px | `gap-8` | `ga-8` |

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

## 1.7 Sombras & Elevação

### 1.7.1 Shadow Scale

| Nível | Nome | Box Shadow | Uso |
|-------|------|------------|-----|
| **0** | None | none | Elementos planos |
| **1** | Subtle | `0 1px 2px rgba(0,0,0,0.05)` | Cards padrão, inputs |
| **2** | Default | `0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)` | Cards hover, dropdowns |
| **3** | Medium | `0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06)` | Modais, popovers |
| **4** | Large | `0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.08)` | Dialogs grandes |
| **5** | XLarge | `0 16px 32px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.10)` | Drawers, sidebars |

### 1.7.2 Classes

```html
<!-- Tailwind -->
<div class="shadow-none">Level 0</div>
<div class="shadow-sm">Level 1</div>
<div class="shadow">Level 2</div>
<div class="shadow-md">Level 3</div>
<div class="shadow-lg">Level 4</div>
<div class="shadow-xl">Level 5</div>

<!-- Vuetify -->
<v-card elevation="0">Level 0</v-card>
<v-card elevation="1">Level 1</v-card>
<v-card elevation="2">Level 2</v-card>
<v-card elevation="3">Level 3</v-card>
<v-card elevation="4">Level 4</v-card>
<v-card elevation="5">Level 5</v-card>
```

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

### 1.8.1 Border Radius

| Token | Valor | Tailwind | Uso |
|-------|-------|----------|-----|
| `--radius-none` | 0px | `rounded-none` | Elementos sem arredondamento |
| `--radius-sm` | 4px | `rounded-sm` | Elementos compactos |
| `--radius-default` | 6px | `rounded` | **Padrão** - Inputs, buttons |
| `--radius-md` | 8px | `rounded-md` | Cards, modais |
| `--radius-lg` | 12px | `rounded-lg` | Containers grandes |
| `--radius-xl` | 16px | `rounded-xl` | Imagens, avatars grandes |
| `--radius-full` | 9999px | `rounded-full` | Círculos, pills |

### 1.8.2 Uso Recomendado

| Elemento | Border Radius | Justificativa |
|----------|---------------|---------------|
| **Botões** | 6px (`rounded`) | Limpo e moderno |
| **Inputs** | 6px (`rounded`) | Consistência com botões |
| **Cards** | 8px (`rounded-md`) | Suave sem exagero |
| **Modais** | 8px (`rounded-md`) | Mesma linguagem dos cards |
| **Badges/Skills** | 9999px (`rounded-full`) | Pill — formato cápsula |
| **Avatars** | 9999px (`rounded-full`) | Círculo perfeito |

### 1.8.3 Espessura de Bordas

| Token | Valor | Tailwind | Uso |
|-------|-------|----------|-----|
| `--border-none` | 0px | `border-0` | Sem borda |
| `--border-default` | 1px | `border` | **Padrão** |
| `--border-medium` | 2px | `border-2` | Destaque, selecionado |

---

## 1.9 Motion & Animation

### 1.9.1 Duração

| Tipo | Duração | Tailwind | Uso |
|------|---------|----------|-----|
| **Instant** | 50ms | `duration-50` | Feedback imediato |
| **Fast** | 100ms | `duration-100` | Hovers |
| **Normal** | 150ms | `duration-150` | **Padrão** |
| **Slow** | 200ms | `duration-200` | Modais, expansões |
| **Slower** | 300ms | `duration-300` | Sidebars, drawers |

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

# PARTE 2: COMPONENTES

## 2.1 Botões

### 2.1.1 Hierarquia de Botões

| Tipo | Background | Text | Border | Tailwind | Vuetify | Uso |
|------|------------|------|--------|----------|---------|-----|
| **Primary** | `bg-gray-900` | `white` | none | `bg-gray-900 text-white` | `color="grey-darken-4"` | Ação principal |
| **Secondary** | `bg-gray-100` | `gray-700` | none | `bg-gray-100 text-gray-700` | `variant="tonal"` | Ação secundária |
| **Outline** | `transparent` | `gray-700` | `border-gray-300` | `border border-gray-300` | `variant="outlined"` | Ação alternativa |
| **Ghost** | `transparent` | `gray-600` | none | `hover:bg-gray-100` | `variant="text"` | Ação sutil |
| **Destructive** | `bg-red-600` | `white` | none | `bg-red-600 text-white` | `color="red"` | Ações destrutivas |

### 2.1.2 Estados de Botão

| Estado | Primary | Secondary | Outline | Ghost |
|--------|---------|-----------|---------|-------|
| **Default** | `bg-gray-900` | `bg-gray-100` | `border-gray-300` | `transparent` |
| **Hover** | `bg-gray-800` | `bg-gray-200` | `bg-gray-50 border-gray-400` | `bg-gray-100` |
| **Active** | `bg-gray-950` | `bg-gray-300` | `bg-gray-100` | `bg-gray-200` |
| **Focus** | `ring-2 ring-gray-900/20` | `ring-2 ring-gray-500/20` | `ring-2 ring-gray-500/20` | `ring-2 ring-gray-500/20` |
| **Disabled** | `bg-gray-400` | `opacity-50` | `opacity-50` | `opacity-50` |

### 2.1.3 Especificações CSS

```css
.lia-btn-primary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 6px;
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
  background-color: #9CA3AF;
  cursor: not-allowed;
}

.lia-btn-secondary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background-color: #F3F4F6;
  color: #374151;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-outline {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background-color: transparent;
  color: #374151;
  border: 1px solid #D1D5DB;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-ghost {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background-color: transparent;
  color: #4B5563;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.lia-btn-destructive {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background-color: #DC2626;
  color: #FFFFFF;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}
```

### 2.1.4 Tamanhos de Botão

| Tamanho | Padding | Font Size | Height | Icon Size |
|---------|---------|-----------|--------|-----------|
| **XS** | `px-2 py-1` | 11px | 28px | 14px |
| **SM** | `px-3 py-1.5` | 12px | 32px | 14px |
| **MD** | `px-4 py-2` | 13px | 36px | 16px |
| **LG** | `px-5 py-2.5` | 14px | 40px | 18px |
| **XL** | `px-6 py-3` | 15px | 48px | 20px |

---

## 2.2 Inputs & Forms

### 2.2.1 Estados de Input

| Estado | Border | Background | Text | Ring |
|--------|--------|------------|------|------|
| **Default** | `border-gray-300` | `white` | `gray-800` | none |
| **Hover** | `border-gray-400` | `white` | `gray-800` | none |
| **Focus** | `border-gray-900` | `white` | `gray-900` | `ring-2 ring-gray-900/20` |
| **Disabled** | `border-gray-200` | `gray-100` | `gray-400` | none |
| **Error** | `border-red-500` | `white` | `gray-800` | `ring-2 ring-red-500/20` |
| **Success** | `border-green-500` | `white` | `gray-800` | none |

### 2.2.2 Implementação

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

## 2.3 Cards

### 2.3.1 Card Padrão

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

### 2.3.2 Card Interativo

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

---

## 2.4 Modais

### 2.4.1 Tamanhos Fixos

| Tamanho | Max Width | Pixels | Tailwind | Uso |
|---------|-----------|--------|----------|-----|
| **XS** | `max-w-sm` | 384px | `max-w-sm` | Confirmações simples |
| **S** | `max-w-md` | 448px | `max-w-md` | Forms compactos |
| **M** | `max-w-lg` | 512px | `max-w-lg` | **Padrão** - Forms médios |
| **L** | `max-w-2xl` | 672px | `max-w-2xl` | Edição completa |
| **XL** | `max-w-4xl` | 896px | `max-w-4xl` | Visualizações amplas |

**PROIBIDO:** Usar tamanhos intermediários (max-w-xl, max-w-3xl, max-w-5xl)

### 2.4.2 Estrutura

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

---

## 2.5 Tabelas

### 2.5.1 Estrutura Básica

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

---

## 2.6 Badges & Tags

### 2.6.1 Badge Padrão

```html
<!-- Tailwind -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700 border border-gray-200">
  Badge
</span>

<!-- Vuetify -->
<v-chip size="small" variant="outlined">Badge</v-chip>
```

### 2.6.2 Badges Semânticos

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

### 2.6.3 Badges WeDo (10% Accent)

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

---

## 2.7 Tooltips & Popovers

### 2.7.1 Tooltip

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

---

## 2.8 Toasts & Alerts

### 2.8.1 Toast Variants

| Tipo | Border | Icon BG | Icon | Uso |
|------|--------|---------|------|-----|
| **Success** | `border-green-200` | `bg-green-100` | CheckCircle green-600 | Confirmações |
| **Warning** | `border-amber-200` | `bg-amber-100` | AlertTriangle amber-600 | Avisos |
| **Error** | `border-red-200` | `bg-red-100` | XCircle red-600 | Erros |
| **Info** | `border-blue-200` | `bg-blue-100` | Info blue-600 | Informações |

```html
<!-- Tailwind -->
<div class="flex items-start gap-3 bg-white border border-green-200 rounded-md shadow-lg p-4 max-w-sm">
  <div class="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
    <svg class="w-3 h-3 text-green-600">...</svg>
  </div>
  <div class="flex-1 min-w-0">
    <p class="text-sm font-semibold text-gray-900">Sucesso!</p>
    <p class="text-xs text-gray-600 mt-0.5">Candidato salvo com sucesso</p>
  </div>
  <button class="flex-shrink-0 text-gray-400 hover:text-gray-600">
    <svg class="w-4 h-4">...</svg>
  </button>
</div>

<!-- Vuetify -->
<v-snackbar v-model="snackbar" color="green">
  Candidato salvo com sucesso
  <template #actions>
    <v-btn icon="mdi-close" size="small" @click="snackbar = false"></v-btn>
  </template>
</v-snackbar>
```

---

## 2.9 Navigation

### 2.9.1 Sidebar (Open Sans)

```html
<!-- Tailwind -->
<nav class="w-64 h-screen bg-white border-r border-gray-200 p-4">
  <div class="mb-6">
    <div class="flex items-center gap-2 px-3 py-2">
      <svg class="w-6 h-6 text-[#60BED1]"><!-- Brain Icon --></svg>
      <span class="text-lg font-bold text-gray-900 font-['Open_Sans']">LIA</span>
    </div>
  </div>
  
  <div class="space-y-1">
    <!-- Item ativo (Open Sans) -->
    <a href="#" class="flex items-center gap-3 px-3 py-2 bg-gray-100 rounded-md font-['Open_Sans']">
      <svg class="w-5 h-5 text-gray-900">...</svg>
      <span class="text-sm font-semibold text-gray-900">Dashboard</span>
    </a>
    
    <!-- Item inativo (Open Sans) -->
    <a href="#" class="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md font-['Open_Sans']">
      <svg class="w-5 h-5">...</svg>
      <span class="text-sm font-medium">Vagas</span>
    </a>
  </div>
</nav>

<!-- Vuetify -->
<v-navigation-drawer permanent width="256">
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

### 2.9.2 Breadcrumbs

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

---

## 2.10 Loading States

### 2.10.1 Spinner

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

### 2.10.2 Skeleton

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

---

## 2.11 Dropdowns & Menus

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

---

## 2.12 Accordions

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

---

## 2.13 Progress Indicators

```html
<!-- Tailwind -->
<div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
  <div class="bg-gray-900 h-2 rounded-full transition-all duration-300" style="width: 65%"></div>
</div>

<!-- Vuetify -->
<v-progress-linear :model-value="65" color="grey-darken-4"></v-progress-linear>
```

---

## 2.14 Avatars

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

---

## 2.15 Breadcrumbs

Ver seção 2.9.2.

---

## 2.16 Pagination

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

---

## 2.17 Switches & Toggles

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

---

## 2.18 Radio Buttons

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

---

## 2.19 Checkboxes

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

---

## 2.20 Date Pickers

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

---

## 2.21 File Upload

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

---

## 2.22 Sliders

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

---

## 2.23 Tabs

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

---

## 2.24 Dividers

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

---

## 2.25 Skeleton Loaders

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

---

## 2.26 Feedback Buttons (Like/Dislike)

Botões de feedback binário para candidatos em resultados de busca do funil de talentos.
Permite ao recrutador avaliar candidatos com thumbs up (like) ou thumbs down (dislike).

### 2.26.1 Especificação

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

### 2.26.2 Estados

| Estado | ThumbsUp | ThumbsDown |
|--------|----------|------------|
| **Neutro** | `text-gray-400 hover:text-gray-600 hover:bg-gray-100` | `text-gray-400 hover:text-gray-600 hover:bg-gray-100` |
| **Like ativo** | `text-emerald-600 bg-emerald-50` | `text-gray-300` (dimmed) |
| **Dislike ativo** | `text-gray-300` (dimmed) | `text-red-500 bg-red-50` |
| **Loading** | `opacity-50 pointer-events-none` | `opacity-50 pointer-events-none` |
| **Disabled** | `opacity-30 cursor-not-allowed` | `opacity-30 cursor-not-allowed` |

### 2.26.3 Implementação

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

### 2.26.4 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/search/SearchFeedbackButtons.tsx` | Componente reutilizável (React) |
| `src/components/chat/message-feedback.tsx` | Padrão similar para respostas da LIA |
| `src/components/calibration/lia-feedback-widget.tsx` | Padrão similar para calibração |

---

## 2.27 Sort Dropdown (Ordenação)

Dropdown para ordenar resultados de busca no funil de talentos. Posicionado no header da área de resultados.

### 2.27.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Componente** | `Select` (shadcn/ui) com `ArrowUpDown` (lucide-react) |
| **Largura** | `w-[180px]` |
| **Altura** | `h-8` (32px) |
| **Font** | Open Sans, `text-sm` |
| **Posição** | Header de resultados, alinhado à direita |
| **Cor do ícone** | `text-gray-500` |

### 2.27.2 Opções de Ordenação

| Valor | Label | Comportamento |
|-------|-------|---------------|
| `relevance` | Relevância | Ordem original do ranking (padrão) |
| `score_desc` | Maior Score | Score descendente |
| `score_asc` | Menor Score | Score ascendente |
| `name_asc` | Nome (A-Z) | Alfabético ascendente |
| `name_desc` | Nome (Z-A) | Alfabético descendente |
| `experience_desc` | Maior Experiência | Anos de experiência descendente |

### 2.27.3 Implementação

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

---

## 2.28 Load More Button (Carregar Mais)

Botão para carregar mais resultados de busca sob demanda (paginação incremental de 10 em 10).

### 2.28.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Variante** | `outline` (shadcn/ui Button) |
| **Largura** | `w-full` (100% do container de resultados) |
| **Altura** | `h-10` (40px) |
| **Font** | Open Sans, `text-sm font-medium` |
| **Ícone** | `ChevronDown` (lucide-react), `w-4 h-4` |
| **Posição** | Após último card de candidato, antes do footer |
| **Counter** | Exibe total carregado vs total disponível |

### 2.28.2 Estados

| Estado | Aparência |
|--------|-----------|
| **Disponível** | `border-gray-200 text-gray-700 hover:bg-gray-50` |
| **Carregando** | `opacity-70` + `Loader2 animate-spin` substituindo ícone |
| **Todos carregados** | Botão oculto, exibe texto "Todos os X candidatos carregados" em `text-gray-500 text-sm` |

### 2.28.3 Implementação

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

---

## 2.29 Qualification Badge (Classificação de Vaga)

Badge indicador do nível de qualificação da vaga, usado no Funil de Talentos para ajustar precisão de busca.
Classificação automática via LLM com override manual pelo recrutador.

### 2.29.1 Especificação

| Propriedade | Valor |
|-------------|-------|
| **Componente** | `QualificationBadge` (React) |
| **Padrão base** | Badge WeDo (seção 2.6.3) |
| **Border radius** | `rounded-full` (pill) |
| **Font** | `text-[10px] font-medium` |
| **Ícones** | `Crown`, `Briefcase`, `HardHat` (lucide-react) |
| **Override** | Dropdown (seção 2.11) com 3 opções |
| **Tooltip** | Padrão DS v4.1 (seção 2.7) - mostra confiança, razão e impacto |

### 2.29.2 Níveis de Qualificação

| Nível | Cor | Background | Text | Ícone | Uso |
|-------|-----|------------|------|-------|-----|
| **Alta** | Purple `#9860D1` | `rgba(152,96,209,0.1)` | `#9860D1` | `Crown` | Executivas, C-Level, Especialistas |
| **Média** | Orange `#D19960` | `rgba(209,153,96,0.1)` | `#D19960` | `Briefcase` | Pleno, Sênior, Coordenadores |
| **Baixa** | Gray monocromático | `bg-gray-100` | `text-gray-700` | `HardHat` | Júnior, Estágio, Operacional |

### 2.29.3 Estados

| Estado | Aparência |
|--------|-----------|
| **Classificado** | Badge com cor e ícone do nível |
| **Override manual** | Badge + asterisco `*` indicador |
| **Classificando** | `Loader2 animate-spin` + "Classificando..." em gray-500 |
| **Não classificado** | Botão dashed `border-dashed border-gray-300` + ícone Brain + "Classificar" |

### 2.29.4 Implementação

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

### 2.29.5 Referências no Código

| Arquivo | Contexto |
|---------|----------|
| `src/components/search/QualificationBadge.tsx` | Componente reutilizável (React) |
| `src/components/pages/candidates-page.tsx` | Integração no header do Funil de Talentos |

---

# PARTE 3: PADRÕES

## 3.1 Estados de Componentes

### 3.1.1 Hierarquia de Estados

| Estado | Ordem | Classe Visual | Quando Aplicar |
|--------|-------|---------------|----------------|
| **Disabled** | 1 (maior prioridade) | Opacidade reduzida | Elemento não disponível |
| **Loading** | 2 | Spinner + disabled | Ação em progresso |
| **Error** | 3 | Border red, bg red-50 | Validação falhou |
| **Focus** | 4 | Ring 2px gray-900/20 | Teclado selecionado |
| **Active** | 5 | Transform scale 0.98 | Mouse clicando |
| **Hover** | 6 | Background + transform | Mouse sobre |
| **Default** | 7 (menor prioridade) | Estado padrão | Nenhuma interação |

### 3.1.2 Focus Ring Padrão

```css
.lia-focus-ring:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2);
}
```

---

## 3.2 Formulários

### 3.2.1 Layout de Forms

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

### 3.2.2 Validação de Forms

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

### 3.2.3 Validação de Forms Vuetify (Vue)

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

## 3.3 Feedback do Sistema

### 3.3.1 Mensagens de Sucesso

```html
<div class="flex items-start gap-3 bg-green-50 border border-green-200 rounded-md p-4">
  <svg class="w-5 h-5 text-green-600 flex-shrink-0">...</svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-green-900">Sucesso!</h4>
    <p class="text-sm text-green-700 mt-0.5">Dados salvos com sucesso.</p>
  </div>
</div>
```

### 3.3.2 Mensagens de Erro

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

## 3.4 Empty States

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

## 3.5 Error Pages

### 3.5.1 Página 404

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

## 3.6 Acessibilidade

### 3.6.1 Contraste de Cores (WCAG AA Mínimo)

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

### 3.6.2 ARIA Labels Obrigatórios

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

### 3.6.3 Keyboard Navigation

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

### 3.6.4 Screen Reader Support

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

### 3.6.5 Color Blindness

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

### 3.6.6 Reduced Motion

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

# PARTE 4: IMPLEMENTAÇÃO

## 4.1 Design Tokens CSS (Arquivo Completo)

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
  --lia-text-muted: #6B7280;       /* gray-500 */
  --lia-text-disabled: #9CA3AF;    /* gray-400 */
  
  /* ============ CORES - BORDAS ============ */
  --lia-border-subtle: #E5E7EB;    /* gray-200 */
  --lia-border-default: #D1D5DB;   /* gray-300 */
  --lia-border-medium: #9CA3AF;    /* gray-400 */
  
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
  --lia-text-body: #E5E7EB;
  --lia-text-secondary: #9CA3AF;
  --lia-text-muted: #6B7280;
  --lia-text-disabled: #4B5563;
  
  --lia-border-subtle: #374151;
  --lia-border-default: #4B5563;
  --lia-border-medium: #6B7280;
  
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
    --lia-text-body: #E5E7EB;
    --lia-text-secondary: #9CA3AF;
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

## 4.2 Design Tokens TypeScript (Arquivo Completo)

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
    muted: '#6B7280',
    disabled: '#9CA3AF',
  },
  border: {
    subtle: '#E5E7EB',
    default: '#D1D5DB',
    medium: '#9CA3AF',
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

## 4.3 Classes Utilitárias

### 4.3.1 Classes de Texto

```css
.wedo-text-title     { color: #111827; }  /* gray-900 */
.wedo-text-body      { color: #1F2937; }  /* gray-800 */
.wedo-text-secondary { color: #4B5563; }  /* gray-600 */
.wedo-text-muted     { color: #6B7280; }  /* gray-500 */

/* Dark mode automático */
.dark .wedo-text-title     { color: #F9FAFB; }
.dark .wedo-text-body      { color: #E5E7EB; }
.dark .wedo-text-secondary { color: #9CA3AF; }
.dark .wedo-text-muted     { color: #6B7280; }
```

### 4.3.2 Classes WeDo (Cores de Acento)

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

## 4.4 Integração Vuetify

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
          secondary: '#9CA3AF',
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
      rounded: 'sm',
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

## 4.5 Integração Vuetify Avançada

### 4.5.1 Variáveis SASS Vuetify

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

### 4.5.2 global.scss - Overrides Vuetify

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
  color: #D1D5DB !important;
}

.v-label {
  font-family: 'Open Sans', sans-serif !important;
  font-size: 0.6875rem !important;
  font-weight: 500 !important;
}

// ============ CARDS ============
.v-card {
  border: 1px solid #E5E7EB !important;
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
  border: 1px solid #E5E7EB !important;
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
  border-right: 1px solid #E5E7EB !important;
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

### 4.5.3 Composable useDesignTokens()

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
    text: { primary: '#111827', body: '#1F2937', secondary: '#4B5563', muted: '#6B7280', disabled: '#9CA3AF' },
    border: { subtle: '#E5E7EB', default: '#D1D5DB', medium: '#9CA3AF' },
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
    text: { primary: '#F9FAFB', body: '#E5E7EB', secondary: '#9CA3AF', muted: '#6B7280', disabled: '#4B5563' },
    border: { subtle: '#374151', default: '#4B5563', medium: '#6B7280' },
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

### 4.5.4 Plugin Nuxt para Design System

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
    // ... usar a configuração completa da seção 4.4
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
    tokens.css           ← CSS custom properties (seção 4.1)
    settings.scss        ← Variáveis SASS Vuetify (seção 4.5.1)
    global.scss          ← Overrides Vuetify (seção 4.5.2)
composables/
  useDesignTokens.ts     ← Composable type-safe (seção 4.5.3)
plugins/
  design-system.ts       ← Plugin Nuxt (seção 4.5.4)
```

### 4.5.5 Dark Mode Toggle (Vue + Vuetify)

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

### 4.5.6 Padrões de Slots Vuetify

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

## 4.6 Mapeamento Tailwind ↔ Vuetify

### 4.5.1 Cores

| Tailwind | Vuetify 3 |
|----------|-----------|
| `bg-gray-900` | `color="grey-darken-4"` |
| `bg-gray-100` | `class="bg-grey-lighten-4"` |
| `text-gray-800` | `class="text-grey-darken-3"` |
| `border-gray-200` | `class="border-grey-lighten-3"` |
| `shadow-sm` | `elevation="1"` |
| `shadow-md` | `elevation="4"` |

### 4.5.2 Tipografia

| Tailwind | Vuetify 3 |
|----------|-----------|
| `text-2xl font-bold` | `class="text-h3"` |
| `text-lg font-semibold` | `class="text-h4"` |
| `text-sm` | `class="text-body-2"` |
| `text-xs` | `class="text-caption"` |

### 4.5.3 Layout

| Tailwind | Vuetify 3 |
|----------|-----------|
| `flex` | `class="d-flex"` |
| `flex items-center` | `class="d-flex align-center"` |
| `flex justify-between` | `class="d-flex justify-space-between"` |
| `gap-2` | `style="gap: 8px"` |
| `p-4` | `class="pa-4"` |

### 4.5.4 Componentes

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

## 4.6 Tabela de Migração v4.0 → v4.1

### 4.6.1 O Que Mudou

| Aspecto | v4.0 | v4.1 | Ação |
|---------|------|------|------|
| **Estrutura** | 10 seções componentes | 25 seções componentes | Adicionar 2.11-2.25 |
| **Efeitos** | Não tinha Glassmorphism | Seção 1.10 Glassmorphism | Novo |
| **Acessibilidade** | Básica (3.6) | Expandida (WCAG, keyboard, etc) | Atualizar |
| **Vuetify** | Parcial | Mapeamento completo | Adicionar |
| **Focus Ring** | Variado | Padronizado `ring-2 ring-gray-900/20` | Padronizar |

### 4.6.2 O Que NÃO Mudou

| Aspecto | Valor | Motivo |
|---------|-------|--------|
| **Tipografia** | 2 fontes (Open Sans 60%, Inter 40%) | Simplificado na v4.1 - Source Serif 4 removido |
| **Espaçamento** | Base 4px | Consistência existente |
| **Dark Mode** | Implementação completa | Já funcional |
| **Classes CSS** | `.lia-h1`, `.lia-sidebar-item`, etc | Compatibilidade |
| **Cores WeDo** | Mesmos hex codes | Identidade de marca |
| **Botão Primary** | Preto (gray-900) | Decisão de design |

### 4.6.3 Checklist de Migração

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

# PARTE 5: CATÁLOGOS

## 5.1 Catálogo Completo de Ícones

### 5.1.1 Bibliotecas

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

### 5.1.2 Ícones por Categoria

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

## 5.2 Catálogo de Cores por Contexto

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

## 5.3 Catálogo de Modais (58+)

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
- ✅ **Tipografia simplificada:** 2 fontes (Open Sans 60% + Inter 40%) - Source Serif 4 removido
- ✅ **Vuetify defaults expandidos:** 25 componentes com props padrão (seção 4.4)
- ✅ **Variáveis SASS Vuetify:** settings.scss para customização profunda (seção 4.5.1)
- ✅ **global.scss:** Overrides Vuetify completos com dark mode (seção 4.5.2)
- ✅ **Composable useDesignTokens():** API type-safe para tokens em Vue 3 (seção 4.5.3)
- ✅ **Plugin Nuxt:** Setup completo design system (seção 4.5.4)
- ✅ **Dark mode toggle Vue:** useThemeToggle() com persistência (seção 4.5.5)
- ✅ **Padrões de slots Vuetify:** v-btn, v-text-field, v-dialog, v-data-table, v-tabs, v-navigation-drawer (seção 4.5.6)
- ✅ **Validação Vuetify:** Rules padrão em português (seção 3.2.3)
- ✅ **Transições CSS ↔ Vuetify:** Mapeamento com exemplos Vue (seção 1.9.4)
- ✅ **Catálogo de ícones expandido:** 65+ ícones com coluna MDI completa (seção 5.1)
- ✅ **Agent skills sincronizados:** 5 skills + reference files atualizados

### Mantido (Compatibilidade)
- ✅ Espaçamento base 4px
- ✅ Dark mode completo
- ✅ Todas as classes CSS existentes (.lia-h1, .lia-sidebar-item, etc.)
- ✅ Cores WeDo e tokens de cor

---

*Documento gerado em Fevereiro 2026 - Design System LIA v4.1*
