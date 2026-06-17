# Design System - Plataforma LIA v2.0

> **Versão:** 2.0  
> **Atualizado:** Dezembro 2024  
> **Storybook:** Porta 6000 (v10.1.4)  
> **Arquivos Base:** `design-tokens.css`, `globals.css`

---

## Índice

1. [Filosofia de Design](#1-filosofia-de-design)
2. [Sistema de Cores](#2-sistema-de-cores)
3. [Tipografia](#3-tipografia)
4. [Classes LIA v2.0](#4-classes-lia-v20)
5. [Componentes Padrão](#5-componentes-padrão)
6. [Design Tokens CSS](#6-design-tokens-css)
7. [Responsividade](#7-responsividade)
8. [Animações](#8-animações)
9. [Acessibilidade](#9-acessibilidade)
10. [Storybook](#10-storybook)
11. [Regras de Uso de Cores](#11-regras-de-uso-de-cores)
12. [Modais & Dialogs](#12-modais--dialogs)
13. [Padrões de Componentes](#13-padrões-de-componentes)
14. [Checklist de Implementação](#14-checklist-de-implementação)

---

## 1. Filosofia de Design

### 1.1 Padrão ElevenLabs

Interface **monocromática** com acentos de cor estratégicos:

| Proporção | Uso |
|-----------|-----|
| **90%** | Escala de cinzas (Gray Scale) |
| **10%** | Cores de acento WeDo dessaturadas |

### 1.2 Hierarquia Visual

1. **Peso Tipográfico**: Negrito para elementos importantes
2. **Tons de Cinza**: Diferentes shades para profundidade
3. **Bordas Sutis**: Quase invisíveis (`border-gray-200/dark:border-gray-700`)
4. **Sombras Leves**: Elevação sutil sem dramatismo
5. **Sem Gradientes**: Cores sólidas, interfaces limpas

### 1.3 Princípios Fundamentais

```
✓ Texto escuro (nunca preto puro #000000)
✓ Backgrounds claros com hierarquia de profundidade
✓ Bordas quase invisíveis ou ausentes
✓ Sombras sutis para elevação
✓ Cores de acento usadas com parcimônia
✗ Gradientes
✗ Bordas grossas
✗ Cores saturadas demais
✗ Animações excessivas
```

---

## 2. Sistema de Cores

### 2.1 Paleta WeDo Principal (Dessaturada)

```css
:root {
  /* CYAN - Vagas, LIA, Automação, Tecnologia */
  --wedo-cyan: #60BED1;
  --wedo-cyan-light: #A8CED5;
  --wedo-cyan-hover: #4DA8BB;

  /* GREEN - Candidatos, Sucesso, Aprovação */
  --wedo-green: #5DA47A;
  --wedo-green-light: #A8D5B7;
  --wedo-green-hover: #4A8A68;
  --wedo-green-success: #60D186;

  /* ORANGE - Tempo, Custos, Economia, Alertas */
  --wedo-orange: #D19960;
  --wedo-orange-light: #D5BFA8;
  --wedo-orange-hover: #BF8554;
  --wedo-orange-alert: #E5A853;

  /* PURPLE - Insights, Premium, Análises IA */
  --wedo-purple: #9860D1;
  --wedo-purple-light: #BFA8D5;
  --wedo-purple-hover: #8652B8;

  /* MAGENTA - Urgência crítica, Prioridade alta */
  --wedo-magenta: #D160AB;
  --wedo-magenta-light: #D5A8C6;
  --wedo-magenta-hover: #B84D95;
}
```

**Classes Utilitárias:**
```css
.text-wedo-cyan    { color: var(--wedo-cyan); }
.text-wedo-green   { color: var(--wedo-green); }
.text-wedo-orange  { color: var(--wedo-orange); }
.text-wedo-purple  { color: var(--wedo-purple); }
.text-wedo-magenta { color: var(--wedo-magenta); }

.bg-wedo-cyan      { background-color: var(--wedo-cyan); color: white; }
.bg-wedo-green     { background-color: var(--wedo-green); color: white; }
.bg-wedo-orange    { background-color: var(--wedo-orange); color: white; }
.bg-wedo-purple    { background-color: var(--wedo-purple); color: white; }
.bg-wedo-magenta   { background-color: var(--wedo-magenta); color: white; }

.bg-wedo-cyan-light    { background-color: var(--wedo-cyan-light); }
.bg-wedo-green-light   { background-color: var(--wedo-green-light); }
.bg-wedo-orange-light  { background-color: var(--wedo-orange-light); }
.bg-wedo-purple-light  { background-color: var(--wedo-purple-light); }
.bg-wedo-magenta-light { background-color: var(--wedo-magenta-light); }
```

### 2.2 Paleta ElevenLabs Sépia

```css
:root {
  /* Backgrounds monocromáticos */
  --eleven-bg-main: #F8F8F8;
  --eleven-bg-card: #FFFFFF;
  --eleven-bg-message: #F5F5F5;

  /* Textos - nunca preto puro */
  --eleven-text-primary: #2D2D2D;
  --eleven-text-secondary: #666666;
  --eleven-text-tertiary: #999999;

  /* Cards coloridos escuros (modo dark) */
  --eleven-card-sepia-dark: #3D3330;
  --eleven-card-forest: #2C4A3A;
  --eleven-card-navy: #2A3744;
  --eleven-card-brown: #443C35;
  --eleven-card-slate: #3A3F47;

  /* Cores pastéis sépia */
  --eleven-sepia-light: #F3EBE1;
  --eleven-sepia-mint: #DCE4DB;
  --eleven-sepia-rose: #E3DADC;
  --eleven-sepia-blue: #DDE1E9;
  --eleven-sepia-lilac: #E5E0E2;
  --eleven-sepia-ice: #EAEAEA;
  --eleven-sepia-coral: #E17B75;

  /* Bordas sutis */
  --eleven-border-subtle: #E8E8E8;
  --eleven-border-light: #F0F0F0;
}
```

### 2.3 Paleta Tech Startups 2024-2025

```css
:root {
  /* Cores vibrantes futuristas */
  --ai-aqua: 194 100% 39%;       /* #0094c6 - azul-verde futurista */
  --electric-red: 351 79% 49%;   /* #de1c31 - vermelho vibrante */
  --ethereal-green: 75 65% 44%;  /* #8bb923 - verde suave futurista */
  --warm-energy: 44 86% 54%;     /* #f0b323 - amarelo energético */
  --peach-fuzz: 16 89% 76%;      /* #f6A68c - Pantone 2024 */
  --deep-tech: 0 0% 11%;         /* #1d1d1f - quase preto */

  /* Variações claras (20% mais claras) */
  --ai-aqua-light: 194 100% 85%;
  --electric-red-light: 351 79% 85%;
  --ethereal-green-light: 75 65% 85%;
  --warm-energy-light: 44 86% 85%;
  --peach-fuzz-light: 16 89% 90%;

  /* Neutros da paleta */
  --neutral-warm: 48 15% 92%;    /* #edeecb */
  --neutral-cool: 220 9% 75%;    /* #bebebf */
  --neutral-dark: 240 2% 49%;    /* #7e7e81 */
}
```

**Classes Utilitárias Tech:**
```css
.bg-ai-aqua        { background-color: hsl(var(--ai-aqua)); }
.bg-ai-aqua-light  { background-color: hsl(var(--ai-aqua-light)); }
.text-ai-aqua      { color: hsl(var(--ai-aqua)); }

.bg-electric-red       { background-color: hsl(var(--electric-red)); }
.bg-electric-red-light { background-color: hsl(var(--electric-red-light)); }
.text-electric-red     { color: hsl(var(--electric-red)); }

.bg-ethereal-green       { background-color: hsl(var(--ethereal-green)); }
.bg-ethereal-green-light { background-color: hsl(var(--ethereal-green-light)); }
.text-ethereal-green     { color: hsl(var(--ethereal-green)); }

.bg-warm-energy       { background-color: hsl(var(--warm-energy)); }
.bg-warm-energy-light { background-color: hsl(var(--warm-energy-light)); }
.text-warm-energy     { color: hsl(var(--warm-energy)); }

.bg-peach-fuzz       { background-color: hsl(var(--peach-fuzz)); }
.bg-peach-fuzz-light { background-color: hsl(var(--peach-fuzz-light)); }
.text-peach-fuzz     { color: hsl(var(--peach-fuzz)); }

.bg-deep-tech  { background-color: hsl(var(--deep-tech)); }
.text-deep-tech { color: hsl(var(--deep-tech)); }
```

### 2.4 Sistema Monocromático LIA

```css
:root {
  /* Backgrounds - Hierarquia de profundidade */
  --lia-bg-primary: #FFFFFF;     /* Branco puro - fundo principal */
  --lia-bg-secondary: #F9FAFB;   /* Cinza quase branco - cards */
  --lia-bg-tertiary: #F3F4F6;    /* Cinza claro - hover */
  --lia-bg-elevated: #FFFFFF;    /* Cards elevados (com shadow) */

  /* Borders & Dividers - Sutileza máxima */
  --lia-border-subtle: #E5E7EB;  /* Borders quase invisíveis */
  --lia-border-default: #D1D5DB; /* Borders padrão */
  --lia-border-medium: #9CA3AF;  /* Borders com destaque */

  /* Textos - Hierarquia tipográfica */
  --lia-text-primary: #111827;   /* Quase preto - títulos */
  --lia-text-secondary: #6B7280; /* Cinza médio - corpo */
  --lia-text-tertiary: #9CA3AF;  /* Cinza claro - labels */
  --lia-text-disabled: #D1D5DB;  /* Desabilitado */
  --lia-text-inverse: #FFFFFF;   /* Texto em fundo escuro */

  /* Interactive States */
  --lia-interactive-hover: #F3F4F6;
  --lia-interactive-active: #E5E7EB;
  --lia-interactive-focus: #111827;

  /* Shadows - Elevação sutil */
  --lia-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.02);
  --lia-shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.05);
  --lia-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.05);
  --lia-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.05);

  /* Vermelho Coral - Identidade LIA (USO MÍNIMO!) */
  --lia-brand-primary: #C74446;
  --lia-brand-primary-hover: #B23B3D;
  --lia-brand-primary-light: #FEF2F2;
}

.dark {
  --lia-bg-primary: #0F1113;
  --lia-bg-secondary: #1A1D1F;
  --lia-bg-tertiary: #26292B;
  --lia-bg-elevated: #1A1D1F;

  --lia-border-subtle: #2D3748;
  --lia-border-default: #374151;
  --lia-border-medium: #4B5563;

  --lia-text-primary: #F9FAFB;
  --lia-text-secondary: #D1D5DB;
  --lia-text-tertiary: #9CA3AF;
  --lia-text-disabled: #6B7280;
  --lia-text-inverse: #111827;

  --lia-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
  --lia-shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.4);
  --lia-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.5);
  --lia-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.6);

  --lia-brand-primary: #EF4444;
  --lia-brand-primary-hover: #DC2626;
  --lia-brand-primary-light: #2D1D1E;
}
```

**Classes Utilitárias LIA:**
```css
/* Backgrounds */
.lia-bg-primary   { background-color: var(--lia-bg-primary); }
.lia-bg-secondary { background-color: var(--lia-bg-secondary); }
.lia-bg-tertiary  { background-color: var(--lia-bg-tertiary); }

/* Textos */
.lia-text-primary   { color: var(--lia-text-primary); }
.lia-text-secondary { color: var(--lia-text-secondary); }
.lia-text-tertiary  { color: var(--lia-text-tertiary); }

/* Borders */
.lia-border-subtle  { border-color: var(--lia-border-subtle); }
.lia-border-default { border-color: var(--lia-border-default); }

/* Brand (uso MÍNIMO!) */
.lia-brand-text   { color: var(--lia-brand-primary); }
.lia-brand-bg     { background-color: var(--lia-brand-primary); }
.lia-brand-border { border-color: var(--lia-brand-primary); }

/* Shadows */
.lia-shadow-sm { box-shadow: var(--lia-shadow-sm); }
.lia-shadow    { box-shadow: var(--lia-shadow-default); }
.lia-shadow-md { box-shadow: var(--lia-shadow-md); }
.lia-shadow-lg { box-shadow: var(--lia-shadow-lg); }
```

### 2.5 Cores de Status (Vagas)

```typescript
const getStatusColor = (status: string) => {
  const colors = {
    'Ativa': '#A8D5B7',                // Verde menta
    'Aprovada': '#B8E6B8',             // Verde claro
    'Aguardando aprovação': '#F5E6B3', // Amarelo suave
    'Reaberta': '#FFD9B3',             // Pêssego
    'Paralisada': '#E8B8B8',           // Rosa salmão
    'Interna': '#B8D8E8',              // Azul bebê
    'Fechada (preenchida)': '#D3D3D3', // Cinza médio
    'Fechada (expirada)': '#C8A8A8',   // Marrom claro
    'Cancelada': '#E8A8A8',            // Vermelho suave
    'Rascunho': '#F0F0F0',             // Cinza claro
    'Arquivada': '#E0E0E0',            // Cinza neutro
    'Concluída': '#C8D8C8'             // Verde acinzentado
  }
  return colors[status] || '#E5E7EB'
}
```

### 2.6 Identidade Visual LIA (Brain)

**TODAS as referências visuais à inteligência LIA usam:**

| Atributo | Valor |
|----------|-------|
| **Ícone** | `Brain` ou `BrainCircuit` (Lucide React) |
| **Cor Padrão** | `text-wedo-cyan` (#60BED1) |
| **Aplicação** | Botões LIA, cards LIA, badges de automação |

```tsx
import { Brain, BrainCircuit } from 'lucide-react'

// Uso padrão
<Brain className="w-4 h-4 text-wedo-cyan" />
<BrainCircuit className="w-5 h-5 text-wedo-cyan" />
```

---

## 3. Tipografia

### 3.1 Fontes do Sistema

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Open+Sans:wght@300;400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&display=swap');

:root {
  --font-inter: "Inter", sans-serif;
  --font-open-sans: "Open Sans", sans-serif;
  --font-source-serif: "Source Serif 4", "Georgia", serif;
}
```

### 3.2 Sistema de 3 Níveis

| Fonte | Uso | Peso | Tamanhos |
|-------|-----|------|----------|
| **Source Serif 4** | Títulos de página (H1-H4) | 600-700 | `text-lg` a `text-2xl` |
| **Open Sans** | UI Elements, labels, menus | 400-600 | `text-xs` a `text-sm` |
| **Inter** | Dados tabulares, métricas | 400-500 | `text-xs` a `text-3xl` |

### 3.3 Hierarquia de Tamanhos (Dashboard)

```typescript
// Dashboard Ultra-Compacto
H1 (Título página):    text-sm font-semibold
H2 (CardTitle):        text-[12px] font-medium
KPI Values:            text-xl font-bold
Tertiary Text:         text-[9px] tracking-tight
ALL Badges:            text-[9px] tracking-tight

// Menu Principal
Menu items:            text-[11px] font-medium (0.6875rem)
```

---

## 4. Classes LIA v2.0

### 4.1 Tipografia

```css
/* Títulos - Source Serif 4, Preto */
.lia-h1 {
  font-family: "Source Serif 4", serif;
  font-size: 2rem;
  font-weight: 600;
  line-height: 1.2;
  color: #1F2937;
  letter-spacing: -0.02em;
}

.lia-h2 {
  font-family: "Source Serif 4", serif;
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.25;
  color: #1F2937;
  letter-spacing: -0.01em;
}

.lia-h3 {
  font-family: "Source Serif 4", serif;
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.3;
  color: #1F2937;
}

.lia-h4 {
  font-family: "Source Serif 4", serif;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  color: #1F2937;
}

/* Subtítulos - Open Sans, Cinza escuro */
.lia-subtitle {
  font-family: "Open Sans", sans-serif;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.5;
  color: #374151;
}

.lia-subtitle-sm {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 400;
  line-height: 1.5;
  color: #374151;
}

/* Corpo - Open Sans */
.lia-body {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 400;
  line-height: 1.6;
  color: #4B5563;
}

.lia-body-sm {
  font-family: "Open Sans", sans-serif;
  font-size: 0.8125rem;
  font-weight: 400;
  line-height: 1.5;
  color: #4B5563;
}

/* Helpers/Captions */
.lia-helper {
  font-family: "Open Sans", sans-serif;
  font-size: 0.75rem;
  font-weight: 400;
  line-height: 1.4;
  color: #6B7280;
}

.lia-caption {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;
  font-weight: 500;
  line-height: 1.3;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Labels */
.lia-label {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.4;
  color: #1F2937;
}

.lia-label-sm {
  font-family: "Open Sans", sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.3;
  color: #1F2937;
}
```

### 4.2 Cards

```css
/* Card básico - Clean, sem bordas */
.lia-card {
  background-color: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: none !important;
}

/* Card elevado */
.lia-card-elevated {
  background-color: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border: none !important;
}

/* Card com hover */
.lia-card-hover {
  background-color: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: none !important;
  transition: box-shadow 0.2s ease;
}

.lia-card-hover:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Dark mode */
.dark .lia-card,
.dark .lia-card-elevated,
.dark .lia-card-hover {
  background-color: #1F2937;
}
```

### 4.3 Botões

```css
/* Botão Primário - Cyan */
.lia-btn-primary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  background-color: #60BED1;
  color: #FFFFFF;
  border: none !important;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.lia-btn-primary:hover {
  background-color: #4FA8BA;
}

/* Botão Secundário - Cinza */
.lia-btn-secondary {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  background-color: #F3F4F6;
  color: #1F2937;
  border: none !important;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.lia-btn-secondary:hover {
  background-color: #E5E7EB;
}

/* Botão Ghost */
.lia-btn-ghost {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  background-color: transparent;
  color: #4B5563;
  border: none !important;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.lia-btn-ghost:hover {
  background-color: #F9FAFB;
}

/* Dark mode */
.dark .lia-btn-secondary {
  background-color: #374151;
  color: #F9FAFB;
}

.dark .lia-btn-secondary:hover {
  background-color: #4B5563;
}

.dark .lia-btn-ghost {
  color: #D1D5DB;
}

.dark .lia-btn-ghost:hover {
  background-color: #374151;
}
```

### 4.4 Badges por Categoria

```css
/* Badge base */
.lia-badge {
  font-family: "Open Sans", sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  border: none !important;
}

/* Categorias */
.lia-badge-jobs {
  background-color: rgba(96, 190, 209, 0.12);
  color: #0E7490;
}

.lia-badge-candidates {
  background-color: rgba(93, 164, 122, 0.12);
  color: #166534;
}

.lia-badge-interviews {
  background-color: rgba(229, 168, 83, 0.12);
  color: #92400E;
}

.lia-badge-reports {
  background-color: rgba(139, 92, 246, 0.12);
  color: #6D28D9;
}

.lia-badge-industry {
  background-color: rgba(59, 130, 246, 0.12);
  color: #1D4ED8;
}

.lia-badge-neutral {
  background-color: #F3F4F6;
  color: #4B5563;
}

/* Dark mode */
.dark .lia-badge-neutral {
  background-color: #374151;
  color: #D1D5DB;
}
```

### 4.5 Inputs

```css
.lia-input {
  font-family: "Open Sans", sans-serif;
  font-size: 0.875rem;
  padding: 0.625rem 0.875rem;
  border-radius: 8px;
  background-color: #F9FAFB;
  color: #1F2937;
  border: 1px solid #E5E7EB;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.lia-input:focus {
  outline: none;
  border-color: #60BED1;
  box-shadow: 0 0 0 3px rgba(96, 190, 209, 0.1);
}

.lia-input::placeholder {
  color: #9CA3AF;
}

/* Dark mode */
.dark .lia-input {
  background-color: #1F2937;
  border-color: #374151;
  color: #F9FAFB;
}

.dark .lia-input::placeholder {
  color: #6B7280;
}
```

### 4.6 Page Header

```css
.lia-page-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.lia-page-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lia-page-eyebrow {
  font-family: "Open Sans", sans-serif;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.lia-page-title {
  font-family: "Source Serif 4", serif;
  font-size: 1.75rem;
  font-weight: 600;
  color: #1F2937;
  line-height: 1.2;
}

.lia-page-description {
  font-family: "Open Sans", sans-serif;
  font-size: 0.9375rem;
  font-weight: 400;
  color: #4B5563;
  line-height: 1.5;
}

/* Dark mode */
.dark .lia-page-title { color: #F9FAFB; }
.dark .lia-page-description { color: #D1D5DB; }
.dark .lia-page-eyebrow { color: #9CA3AF; }
```

---

## 5. Componentes Padrão

### 5.1 Cards (shadcn/ui)

```tsx
<Card className="bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800">
  <CardHeader className="p-3">
    <CardTitle className="text-[12px] font-medium">Título</CardTitle>
  </CardHeader>
  <CardContent className="p-3">
    {/* Conteúdo */}
  </CardContent>
</Card>
```

### 5.2 Badges

```tsx
// Badge padrão
<Badge className="text-[9px] tracking-tight bg-gray-100 dark:bg-gray-800">
  Label
</Badge>

// Badge LIA
<span className="lia-badge lia-badge-jobs">Vagas</span>
<span className="lia-badge lia-badge-candidates">Candidatos</span>
```

### 5.3 Botões

```tsx
// Primário
<Button className="lia-btn-primary">Ação Principal</Button>

// Secundário
<Button variant="outline" className="lia-btn-secondary">Secundário</Button>

// Ghost
<Button variant="ghost" className="lia-btn-ghost">Ghost</Button>
```

### 5.4 Ícones LIA

```tsx
import { Brain, BrainCircuit, Sparkles } from 'lucide-react'

<Brain className="w-4 h-4 text-wedo-cyan" />
<BrainCircuit className="w-5 h-5 text-wedo-cyan" />
<Sparkles className="w-4 h-4 text-wedo-purple" />
```

---

## 6. Design Tokens CSS

### 6.1 Cores de Categoria

```css
:root {
  --lia-cat-jobs: #60BED1;        /* Cyan - Vagas */
  --lia-cat-candidates: #5DA47A;  /* Green - Candidatos */
  --lia-cat-interviews: #E5A853;  /* Orange - Entrevistas/LIA */
  --lia-cat-reports: #8B5CF6;     /* Purple - Relatórios */
  --lia-cat-industry: #3B82F6;    /* Blue - Indústria */
}
```

### 6.2 Hierarquia de Texto

```css
:root {
  --lia-text-black: #1F2937;   /* Preto suave - títulos */
  --lia-text-dark: #374151;    /* Cinza muito escuro - subtítulos */
  --lia-text-body: #4B5563;    /* Cinza escuro - texto corpo */
  --lia-text-muted: #6B7280;   /* Cinza médio - helpers */
}
```

### 6.3 Paleta WeDo Apoio

```css
:root {
  --wedo-apoio-cream: #F5EFE7;
  --wedo-apoio-peach-light: #FADCD2;
  --wedo-apoio-salmon: #FFB5A7;
  --wedo-apoio-blue: #8FA4C4;
  --wedo-apoio-mint: #A8D5BA;
  --wedo-apoio-coral: #F08080;
  --wedo-apoio-gold: #F4D06F;
}
```

---

## 7. Responsividade

### 7.1 Breakpoints Tailwind

```typescript
screens: {
  'sm': '640px',
  'md': '768px',
  'lg': '1024px',
  'xl': '1280px',
  '2xl': '1536px'
}
```

### 7.2 Otimização para Laptops 11" (1366px)

| Atributo | Valor |
|----------|-------|
| **Viewport Alvo** | 1366x768px |
| **Estratégia** | Elementos ultra-compactos sem scroll horizontal |
| **Sidebar** | 256px (w-64) expansível, 64px colapsada |
| **Spacing** | `gap-2.5`, `p-3`, `px-3` |
| **Overflow** | `overflow-hidden min-h-0` em containers flex |

### 7.3 Layout Dashboard com Sidebar

```tsx
<div className="flex h-screen overflow-hidden">
  {/* Sidebar - w-16 colapsada, w-64 expandida */}
  <aside className="hover:w-64 transition-all duration-200">
    {/* Menu */}
  </aside>
  
  {/* Conteúdo principal */}
  <main className="flex-1 overflow-auto px-3 pt-3 pb-6">
    {/* Content */}
  </main>
</div>
```

---

## 8. Animações

### 8.1 Animações Desabilitadas (Radix UI)

```css
/* Tooltips e Dropdowns sem animação */
[data-radix-tooltip-content],
[data-radix-dropdown-menu-content],
[data-radix-popover-content] {
  animation: none !important;
  transition: none !important;
  transform: none !important;
}

/* Classes Tailwind de animação desabilitadas */
.animate-in,
.animate-out,
.fade-in-0,
.zoom-in-95 {
  animation: none !important;
  transition: none !important;
}
```

### 8.2 Animações Permitidas

```css
/* Shimmer para loading */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-shimmer {
  animation: shimmer 2s infinite linear;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  background-size: 200% 100%;
}

/* Hover lift */
.hover-lift {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

/* Micro bounce */
.micro-bounce:active {
  transform: scale(0.95);
}
```

---

## 9. Acessibilidade

### 9.1 Focus Rings

```css
/* Focus ring padrão */
focus:ring-2 focus:ring-blue-500 focus:ring-offset-2

/* Focus ring LIA */
.lia-input:focus {
  outline: none;
  border-color: #60BED1;
  box-shadow: 0 0 0 3px rgba(96, 190, 209, 0.1);
}
```

### 9.2 Contraste WCAG

| Nível | Ratio | Status |
|-------|-------|--------|
| **AA** | ≥ 4.5:1 (texto normal) | ✓ Obrigatório |
| **AAA** | ≥ 7:1 | Meta quando possível |

Todas as cores pastel foram testadas para garantir contraste adequado.

### 9.3 Semantic HTML

```html
<nav>       <!-- Navegação -->
<main>      <!-- Conteúdo principal -->
<aside>     <!-- Sidebar -->
<article>   <!-- Conteúdo independente -->
<section>   <!-- Seções temáticas -->
```

- ARIA labels em ícones sem texto
- Alt text em imagens
- Roles semânticos (`role="tab"`, `role="tablist"`)

---

## 10. Storybook

### 10.1 Configuração

| Info | Valor |
|------|-------|
| **Versão** | 10.1.4 |
| **Porta** | 6000 |
| **Comando** | `npm run storybook` |
| **Build Time** | Manager 2.22s, Preview 3.87s |

### 10.2 Estrutura

```
plataforma-lia/
├── .storybook/
│   ├── main.ts         # Configuração principal
│   └── preview.ts      # Decoradores e parâmetros
└── src/
    └── components/
        └── *.stories.tsx  # Stories dos componentes
```

### 10.3 Executar

```bash
# Desenvolvimento
cd plataforma-lia && npm run storybook

# Build estático
cd plataforma-lia && npm run build-storybook
```

### 10.4 Criar Nova Story

```tsx
// src/components/ui/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './button'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    children: 'Botão Primário',
    className: 'lia-btn-primary',
  },
}

export const Secondary: Story = {
  args: {
    children: 'Botão Secundário',
    className: 'lia-btn-secondary',
  },
}
```

---

## 11. Regras de Uso de Cores

### 11.1 Regras de Accent Color (#60BED1)

| ✅ Use accent em | ❌ Nunca use accent em |
|------------------|------------------------|
| Ícones | Backgrounds de containers grandes |
| Botões primários (CTA) | Backgrounds de cards |
| Badges/pills pequenos | Backgrounds de painéis |
| Containers de ícones (círculos pequenos) | Backgrounds de seções |

```css
/* Badge/pill pequeno - CORRETO */
.accent-badge {
  background-color: rgba(96, 190, 209, 0.1);  /* bg-[#60BED1]/10 */
  color: #60BED1;
}

/* Containers grandes - CORRETO */
.large-container {
  background-color: #FFFFFF;  /* bg-white */
}

/* Containers grandes - ERRADO */
.large-container-wrong {
  background-color: rgba(96, 190, 209, 0.05);  /* bg-[#60BED1]/5 - NÃO USAR */
}
```

---

## 12. Modais & Dialogs

### 12.1 Modal Container

```css
.modal-container {
  background-color: #FFFFFF;
  border-radius: 12px;           /* rounded-xl */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F3F4F6;     /* border-gray-100 */
  max-width: 32rem;              /* max-w-lg */
}
```

### 12.2 Modal Header

```css
.modal-header {
  border-bottom: 1px solid #F3F4F6;  /* border-gray-100 */
  padding: 1.25rem;                   /* p-5 */
}

.modal-title {
  font-size: 13px;
  font-weight: 600;
  color: #1F2937;                     /* gray-800 */
}

.modal-subtitle {
  font-size: 11px;
  color: #6B7280;                     /* gray-500 */
  margin-top: 0.25rem;
}
```

### 12.3 Modal Overlay

```css
.modal-overlay {
  background-color: rgba(0, 0, 0, 0.3);  /* bg-black/30 - NÃO /40 */
  backdrop-filter: blur(1px);             /* backdrop-blur-[1px] */
}
```

### 12.4 Modal Close Button

```css
.modal-close {
  padding: 0.25rem;
  border-radius: 6px;
  color: #9CA3AF;                    /* gray-400 */
  transition: all 0.2s;
}

.modal-close:hover {
  color: #4B5563;                    /* gray-600 */
  background-color: #F9FAFB;         /* gray-50 */
}
```

---

## 13. Padrões de Componentes

### 13.1 NewCandidateUnifiedModal

Modal multi-step wizard para adicionar candidatos:

```css
/* Header */
border-b border-gray-100, p-5
title: text-[13px] font-semibold text-gray-800
subtitle: text-[11px] text-gray-500 mt-1

/* Cards Grid */
grid-cols-3 gap-3
card: border border-gray-100, hover:shadow-sm
card title: text-xs font-medium text-gray-800
card desc: text-[11px] text-gray-500

/* Accent Icons */
container: w-10 h-10 rounded-full bg-[#60BED1]/10
icon: text-[#60BED1]

/* List Items */
py-2 px-3, hover:bg-gray-100
selected: bg-[#60BED1]/10
```

### 13.2 SmartSearchInput

```css
/* Container */
font-family: "Open Sans", sans-serif

/* Placeholder */
color: #9CA3AF;  /* gray-400 */

/* Suggestion Cards */
background-color: #FFFFFF;
border: 1px solid #F3F4F6;
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);

/* Suggestion Text */
title: text-gray-800
description: text-gray-500

/* Accent Suggestions */
background-color: rgba(96, 190, 209, 0.1);
color: #60BED1;
```

### 13.3 Command Palette / Dropdown

```css
.command-palette {
  background-color: #FFFFFF;
  border: 1px solid #F3F4F6;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 0.25rem 0;
}

.command-item {
  padding: 0.375rem 0.75rem;  /* py-1.5 px-3 */
  font-size: 11px;
  color: #1F2937;
}

.command-item:hover {
  background-color: #F9FAFB;  /* gray-50 */
}

.command-item.selected {
  background-color: #F3F4F6;  /* gray-100 */
}
```

### 13.4 Pills & Tags

```css
.pill {
  background-color: #F9FAFB;       /* gray-50 */
  border: 1px solid #E5E7EB;       /* gray-200 */
  color: #4B5563;                  /* gray-600 */
  padding: 0.125rem 0.625rem;      /* py-0.5 px-2.5 */
  border-radius: 9999px;           /* rounded-full */
  font-size: 10px;
}
```

### 13.5 Context Pills (Inline)

```css
.context-pill {
  background-color: #FFFFFF;
  border: 1px solid #E5E7EB;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 10px;
  color: #4B5563;
}

.context-pill:hover {
  background-color: #F9FAFB;
}
```

### 13.6 Lists & Tables

```css
/* List Item */
.list-item {
  padding: 0.625rem 0.75rem;       /* py-2.5 px-3 */
  border-bottom: 1px solid #F3F4F6;
  font-size: 11px;
  color: #1F2937;
  transition: background-color 0.15s;
}

.list-item:hover {
  background-color: #F9FAFB;
}

/* Table Cell */
.table-cell {
  padding: 0.5rem 0.75rem;         /* py-2 px-3 */
  font-size: 11px;
  color: #4B5563;
  border-bottom: 1px solid #F3F4F6;
}
```

---

## 14. Checklist de Implementação

Ao criar componentes, verifique:

- [ ] **Tipografia**: Source Serif 4 (títulos), Open Sans (corpo), Inter (dados)
- [ ] **Cores de texto**: #1F2937 (títulos), #4B5563 (corpo), #6B7280 (helpers)
- [ ] **Sombras**: Apenas sutis (shadow-sm, sem sombras pesadas)
- [ ] **Bordas**: gray-100 ou gray-200, ou nenhuma
- [ ] **Accent color (#60BED1)**: Apenas em ícones, botões, badges pequenos
- [ ] **Cards**: Classe `.lia-card`, sem borda, sombra sutil
- [ ] **Botões**: `.lia-btn-primary`, `.lia-btn-secondary`, `.lia-btn-ghost`
- [ ] **Badges**: `.lia-badge-*` para categorias
- [ ] **Inputs**: `.lia-input` com focus ring cyan
- [ ] **Dark mode**: Funciona com classe `.dark`
- [ ] **Ícone LIA**: Brain com `text-wedo-cyan`
- [ ] **Modal overlay**: `bg-black/30` (não /40)
- [ ] **Modal blur**: `backdrop-blur-[1px]`
- [ ] **Transições**: Suaves em hover states
- [ ] **Spacing**: Grid 4px do Tailwind

---

## Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `src/styles/design-tokens.css` | Tokens CSS completos |
| `src/app/globals.css` | Estilos globais + animações |
| `tailwind.config.ts` | Configuração Tailwind |
| `.storybook/main.ts` | Configuração Storybook |

---

*Documento atualizado em Dezembro 2024 - Versão 2.0*  
*Plataforma LIA - WeDo Talent*
