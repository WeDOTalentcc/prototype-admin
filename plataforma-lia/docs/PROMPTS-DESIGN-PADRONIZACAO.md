# DESIGN SYSTEM LIA v4.1 - GUIA DE PROMPTS PARA PADRONIZAÇÃO

> **Versão:** 4.1 Corrigida  
> **Stack Atual:** React (.jsx/.tsx) + Tailwind CSS  
> **Stack Futura:** Vue.js + Nuxt + Vuetify (migração planejada)  
> **Última Atualização:** Fevereiro 2026

---

## ÍNDICE

1. [Contexto Inicial](#contexto-inicial)
2. [Fase 0: Preparação - Inventário](#fase-0-preparação---inventário)
3. [Fase 1: Setup Base - Fontes e Tailwind](#fase-1-setup-base---fontes-e-tailwind)
4. [Fase 2: Botões](#fase-2-botões)
5. [Fase 3: Inputs e Forms](#fase-3-inputs-e-forms)
6. [Fase 4: Cards e Containers](#fase-4-cards-e-containers)
7. [Fase 5: Navegação e Sidebar](#fase-5-navegação-e-sidebar)
8. [Fase 6: Modais e Componentes Avançados](#fase-6-modais-e-componentes-avançados)
9. [Fase 7: Badges e Utilities](#fase-7-badges-e-utilities)
10. [Fase 8: Validação Final](#fase-8-validação-final)
11. [Resumo Rápido](#resumo-rápido)

---

# CONTEXTO INICIAL

```markdown
# CONTEXTO: DESIGN SYSTEM LIA v4.1 - REACT + TAILWIND

Você vai me ajudar a aplicar o Design System LIA v4.1 no projeto WeDO Talent (React + Tailwind).

## STACK ATUAL:
- Framework: React (arquivos .jsx ou .tsx)
- Styling: Tailwind CSS
- SEM Vue, SEM Vuetify

## ESPECIFICAÇÕES DO DESIGN SYSTEM:

### Cores:
- **Botão Primary:** PRETO (bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900)
- **Botão Secondary:** Border cinza (border border-gray-300 bg-white hover:bg-gray-50)
- **Cyan (#60BED1):** APENAS para elementos LIA/IA (brain icon, Sparkles, Bot icons, badges LIA)
- **Filosofia:** 90% grays + 10% cores WeDo (apenas accents estratégicos)
- **Status semânticos:** green (sucesso), amber (warning), red (erro) - apenas para indicadores

### Tipografia (CRÍTICO):
| Fonte | Uso | Proporção |
|-------|-----|-----------|
| **Open Sans** | UI geral - headers, labels, botões, body text, títulos de cards | **85%** |
| **Inter** | APENAS métricas numéricas, KPIs, números em tabelas, dashboards | **10%** |
| **Source Serif 4** | APENAS sidebar/navigation | **5%** |

⚠️ **REGRA CRÍTICA:** Source Serif 4 NÃO deve ser usado em card titles, section headers ou body text - APENAS sidebar/navigation.

### Espaçamento:
- **Base 4px** (NÃO 8px)
- p-0.5=2px, p-1=4px, p-2=8px, p-4=16px, p-6=24px, p-8=32px

### Componentes:
- **Cards:** rounded-xl (NÃO rounded-md), border border-gray-200
- **Focus ring:** ring-2 ring-gray-900/20 (grayscale, não cyan)
- **Switch/Toggle padrão:** bg-gray-900 quando ativo (cyan apenas em LiaFieldToggle)

## REGRAS OBRIGATÓRIAS:
1. ✅ Sempre fazer INVENTÁRIO COMPLETO antes de implementar
2. ✅ Trabalhar em LOTES PEQUENOS (máximo 10 arquivos por vez)
3. ✅ Listar TODOS os arquivos modificados com contadores
4. ✅ Usar APENAS classes Tailwind do Design System
5. ✅ Parar após cada fase para validação
6. ✅ Se incompleto, NÃO prosseguir
7. ✅ Cyan APENAS para elementos com ícones LIA (Sparkles, Brain, Bot)
8. ✅ Source Serif 4 APENAS em sidebar - NUNCA em cards ou headers
9. ✅ Incluir variantes dark mode em todos os componentes

Confirme que entendeu o contexto React + Tailwind antes de começarmos.
```

---

# FASE 0: PREPARAÇÃO - INVENTÁRIO

```markdown
# FASE 0: PREPARAÇÃO - INVENTÁRIO DO PROJETO REACT

## OBJETIVO:
Mapear o projeto atual ANTES de qualquer implementação.

## TAREFA:

### ETAPA 1: INVENTÁRIO DE ARQUIVOS

Liste:
1. Todos os componentes React (.jsx, .tsx) no projeto
2. Arquivos de estilo (CSS, Tailwind config)
3. Estrutura de pastas (src/, components/, pages/, etc)
4. Fonte atual sendo usada (verificar index.html ou App.css)

Formato esperado:
```
📁 INVENTÁRIO REPLIT - REACT PROJECT:

Componentes React (.jsx/.tsx): X arquivos
- src/components/Button.jsx
- src/components/Card.jsx
- src/pages/Dashboard.jsx
[lista completa]

Arquivos de estilo:
- tailwind.config.js: [existe? sim/não]
- src/index.css ou App.css: [path]
- Outros CSS: [lista]

Estrutura de pastas:
src/
  ├── components/
  ├── pages/
  ├── [outras pastas]

Fontes atuais:
- [listar fontes carregadas no <head> ou CSS]
```

### ETAPA 2: ANÁLISE DE PADRÕES ATUAIS

Para os 5 componentes mais usados, identifique:
1. Botões: classes Tailwind atuais usadas
2. Cards: estrutura e classes
3. Inputs: styling atual
4. Cores: quais são mais usadas (background, text, border)
5. Espaçamento: padrões de padding/margin

Formato:
```
🔍 PADRÕES ATUAIS:

Botões mais comuns:
- Classe 1: bg-blue-500 text-white px-4 py-2
- Classe 2: border border-gray-300 px-4 py-2
[listar todas variações]

Cards:
- Estrutura típica: <div class="bg-white p-4 rounded shadow">
- Variações: [listar]

Inputs:
- Padrão: <input class="border px-3 py-2 rounded">

Cores mais usadas:
- Backgrounds: bg-blue-500, bg-white, bg-gray-100
- Text: text-gray-900, text-blue-600
- Borders: border-gray-300, border-blue-500

Espaçamentos:
- Padding: p-1, p-2, p-4, p-6 (base 4px)
- Margin: m-1, m-2, m-4
- Gap: gap-1, gap-2, gap-4
```

### ETAPA 3: CRIAR ESTRUTURA DE TOKENS

Crie o arquivo `/src/styles/design-tokens.js`:

```javascript
// Design System LIA v4.1 - Tokens para React + Tailwind
// Base: 4px spacing | 3 fonts | 90% gray + 10% accent

export const colors = {
  // Backgrounds
  bg: {
    primary: 'bg-white dark:bg-gray-900',
    secondary: 'bg-gray-50 dark:bg-gray-800',
    tertiary: 'bg-gray-100 dark:bg-gray-700',
  },
  
  // Texts
  text: {
    primary: 'text-gray-900 dark:text-gray-50',
    body: 'text-gray-800 dark:text-gray-200',
    secondary: 'text-gray-600 dark:text-gray-400',
    muted: 'text-gray-500 dark:text-gray-500',
    disabled: 'text-gray-400 dark:text-gray-600',
  },
  
  // Borders
  border: {
    subtle: 'border-gray-200 dark:border-gray-700',
    default: 'border-gray-300 dark:border-gray-600',
    medium: 'border-gray-400 dark:border-gray-500',
  },
  
  // WeDo Accent Colors (10% - apenas contextos específicos)
  wedo: {
    cyan: '#60BED1',      // Brain icon LIA APENAS
    green: '#5DA47A',     // Candidatos
    orange: '#D19960',    // Tempo/Urgência
    purple: '#9860D1',    // Insights
    magenta: '#D160AB',   // Crítico
  },
}

// Tipografia - 3 sistemas de fontes
export const fonts = {
  primary: "font-['Open_Sans']",      // 85% - UI geral
  data: "font-['Inter']",              // 10% - métricas/KPIs
  sidebar: "font-['Source_Serif_4']",  // 5% - sidebar APENAS
}

// Espaçamento base 4px
export const spacing = {
  0: '0px',      // p-0
  0.5: '2px',    // p-0.5
  1: '4px',      // p-1
  2: '8px',      // p-2
  3: '12px',     // p-3
  4: '16px',     // p-4
  5: '20px',     // p-5
  6: '24px',     // p-6
  8: '32px',     // p-8
  10: '40px',    // p-10
  12: '48px',    // p-12
  16: '64px',    // p-16
}

// Helper para gerar classes de botões
export function getButtonClasses(variant = 'primary', size = 'default') {
  const baseClasses = "font-semibold rounded transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 font-['Open_Sans']"
  
  const variants = {
    primary: 'bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200',
    secondary: 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-700',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100',
    destructive: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus:ring-red-600/20',
  }
  
  const sizes = {
    small: 'px-3 py-1.5 text-xs',    // 32px height
    default: 'px-4 py-2 text-sm',     // 40px height
    large: 'px-5 py-2.5 text-sm',     // 48px height
  }
  
  return `${baseClasses} ${variants[variant]} ${sizes[size]}`
}

// Helper para badges
export function getBadgeClasses(type = 'neutral') {
  const base = 'inline-flex items-center px-2 py-1 rounded text-xs font-medium border'
  
  const types = {
    success: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800',
    warning: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800',
    error: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800',
    info: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800',
    neutral: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700',
    lia: 'text-[#60BED1] border-[#60BED1]/20 bg-[#60BED1]/10', // APENAS para LIA
  }
  
  return `${base} ${types[type]}`
}

// Helper para inputs
export function getInputClasses(hasError = false) {
  const base = "w-full px-3 py-2 text-sm text-gray-900 bg-white border rounded transition-all duration-150 focus:outline-none font-['Open_Sans'] dark:bg-gray-800 dark:text-gray-100"
  const normal = 'border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 dark:border-gray-600 dark:focus:border-gray-400'
  const error = 'border-red-500 focus:ring-2 focus:ring-red-500/20 bg-red-50 dark:bg-red-900/10'
  
  return `${base} ${hasError ? error : normal}`
}

// Helper para cards
export function getCardClasses(variant = 'default') {
  const base = 'bg-white border border-gray-200 rounded-xl dark:bg-gray-800 dark:border-gray-700'
  
  const variants = {
    default: `${base} shadow-sm`,
    interactive: `${base} shadow-sm transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer`,
    glass: 'bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-xl shadow-sm dark:bg-gray-800/70',
  }
  
  return variants[variant]
}
```

### ETAPA 4: CRIAR ARQUIVO DE PROGRESSO

Crie `/DESIGN_SYSTEM_PROGRESS.md`:

```markdown
# Design System LIA v4.1 - Progresso (React + Tailwind)

## STATUS
- Projeto: WeDO Talent (Replit)
- Stack: React + Tailwind CSS
- Data Início: [hoje]
- Fase Atual: 0 - Preparação
- % Completo: 0%

## ESPECIFICAÇÕES CRÍTICAS
- Tipografia: Open Sans (85%) + Inter (10%) + Source Serif 4 (5% sidebar)
- Espaçamento: Base 4px
- Cores: 90% gray + 10% accent (cyan APENAS para LIA)
- Cards: rounded-xl
- Dark mode: obrigatório em todos componentes

## FASES
- [ ] Fase 0: Preparação (inventário) ← ATUAL
- [ ] Fase 1: Setup Base (fontes, tokens, Tailwind config)
- [ ] Fase 2: Botões
- [ ] Fase 3: Inputs e Forms
- [ ] Fase 4: Cards e Containers
- [ ] Fase 5: Navegação e Sidebar
- [ ] Fase 6: Modais e Componentes Avançados
- [ ] Fase 7: Badges e Utilities
- [ ] Fase 8: Validação Final

## INVENTÁRIO
[será preenchido na Fase 0]

## LOG
[cada sessão adiciona entrada]
```

### VALIDAÇÃO FASE 0:

Confirme:
- [ ] Inventário de arquivos .jsx/.tsx completo
- [ ] Padrões atuais identificados
- [ ] design-tokens.js criado com helpers (3 fontes, base 4px, dark mode)
- [ ] DESIGN_SYSTEM_PROGRESS.md criado
- [ ] Entendeu que é React + Tailwind (não Vue)

**Responda:**
```
✅ FASE 0 COMPLETA

Arquivos React: X
Componentes mapeados: Y
design-tokens.js criado: ✅ (3 fontes, base 4px, dark mode)
DESIGN_SYSTEM_PROGRESS.md criado: ✅

Padrões identificados:
- Botões: [X variações]
- Cards: [Y variações]
- Inputs: [Z variações]

Próxima: Fase 1 (Setup Base)
```

Aguarde validação antes de Fase 1.
```

---

# FASE 1: SETUP BASE - FONTES E TAILWIND

```markdown
# FASE 1: SETUP BASE - FONTES E TAILWIND

## PRÉ-REQUISITO:
Fase 0 deve estar 100% completa com inventário.

## TAREFA:

### ETAPA 1: ADICIONAR FONTES (3 FONTES OBRIGATÓRIAS)

No arquivo `public/index.html` ou onde está o <head>, adicione:

```html
<!-- ANTES de outros links -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Open+Sans:wght@400;600;700&family=Source+Serif+4:wght@400;600;700&display=swap" rel="stylesheet">
```

⚠️ **CRÍTICO:** São 3 fontes: Open Sans + Inter + Source Serif 4

### ETAPA 2: CONFIGURAR TAILWIND

Atualize `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class', // ou 'media'
  theme: {
    extend: {
      colors: {
        // Cores WeDo custom (10% - apenas accents)
        'wedo-cyan': '#60BED1',    // APENAS LIA
        'wedo-green': '#5DA47A',
        'wedo-orange': '#D19960',
        'wedo-purple': '#9860D1',
        'wedo-magenta': '#D160AB',
      },
      fontFamily: {
        // Sistema de 3 fontes
        'brand': ['Open Sans', 'sans-serif'],       // 85% - UI geral
        'data': ['Inter', 'sans-serif'],            // 10% - métricas/KPIs
        'sidebar': ['Source Serif 4', 'serif'],     // 5% - sidebar APENAS
      },
      // Espaçamento base 4px (Tailwind já usa, mas documentar)
      // p-1 = 4px, p-2 = 8px, p-4 = 16px, p-6 = 24px
      boxShadow: {
        'focus': '0 0 0 3px rgba(17, 24, 39, 0.2)',
      },
      borderRadius: {
        'xl': '12px', // Cards padrão
      },
    },
  },
  plugins: [],
}
```

### ETAPA 3: CRIAR CSS GLOBAL

Atualize `src/index.css` ou `src/App.css`:

```css
/* Design System LIA v4.1 - Global Styles */
/* Tipografia: Open Sans 85% | Inter 10% | Source Serif 4 5% */
/* Espaçamento: Base 4px */

@tailwind base;
@tailwind components;
@tailwind utilities;

/* Aplicar fontes globalmente */
@layer base {
  /* Open Sans é a fonte PADRÃO (85%) para toda UI */
  body {
    @apply font-brand;  /* Open Sans - NÃO Inter! */
    @apply text-gray-900 dark:text-gray-100;
    @apply bg-white dark:bg-gray-900;
  }
  
  /* Open Sans para títulos, botões, labels (85%) */
  h1, h2, h3, h4, h5, h6,
  button,
  label {
    @apply font-brand;  /* Open Sans */
  }
  
  /* Inter APENAS para dados numéricos (10%) */
  .metric, .kpi, .data-value {
    @apply font-data;  /* Inter */
    font-feature-settings: 'tnum' 1;
  }
  
  /* Source Serif 4 APENAS para sidebar (5%) */
  .sidebar-item, .nav-sidebar {
    @apply font-sidebar;  /* Source Serif 4 */
  }
  
  /* Tabular numbers para tabelas */
  td, th {
    font-feature-settings: 'tnum' 1;
  }
}

/* Utility classes customizadas */
@layer components {
  /* Focus ring padrão (grayscale, não cyan) */
  .focus-ring:focus {
    @apply outline-none ring-2 ring-gray-900/20;
  }
  
  /* Card padrão */
  .card {
    @apply bg-white border border-gray-200 rounded-xl shadow-sm;
    @apply dark:bg-gray-800 dark:border-gray-700;
  }
  
  /* Card interativo */
  .card-interactive {
    @apply card transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer;
  }
  
  /* Glassmorphism */
  .glass-card {
    @apply bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-xl shadow-sm;
    @apply dark:bg-gray-800/70 dark:border-gray-700/50;
  }
  
  /* Screen reader only */
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
}

/* Reduced motion */
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

### VALIDAÇÃO FASE 1:

Rode o projeto e verifique:
- [ ] 3 Fontes carregando: Open Sans + Inter + Source Serif 4
- [ ] Tailwind config tem font-brand, font-data, font-sidebar
- [ ] Tailwind config tem cores WeDo
- [ ] Body usa font-brand (Open Sans), NÃO font-data
- [ ] index.css tem classes .focus-ring, .card, .glass-card
- [ ] Dark mode configurado

**Responda:**
```
✅ FASE 1 COMPLETA

Arquivos modificados:
- index.html: 3 fontes adicionadas ✅
- tailwind.config.js: 3 fonts + cores WeDo ✅
- index.css: @layer + utilities + dark mode ✅

Validação:
- Open Sans (85%): ✅ fonte padrão body
- Inter (10%): ✅ classe .metric/.kpi
- Source Serif 4 (5%): ✅ classe .sidebar-item
- Dark mode: ✅ configurado

Próxima: Fase 2 (Botões)
```

Aguarde validação.
```

---

# FASE 2: BOTÕES

```markdown
# FASE 2: BOTÕES (Máximo 10 Arquivos por Leva)

## PRÉ-REQUISITO:
Fase 1 validada e 100% completa.

## TAREFA:

### ETAPA 1: INVENTÁRIO DE BOTÕES

Liste os 10 arquivos .jsx/.tsx com MAIS botões:

```bash
grep -r "<button\|<Button" src/ --include="*.jsx" --include="*.tsx" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

Formato:
```
📋 INVENTÁRIO DE BOTÕES (Top 10):

1. src/components/CandidateCard.jsx - 8 botões
2. src/pages/Dashboard.jsx - 6 botões
[continuar até 10]

Total estimado: X botões em 10 arquivos
```

**AGUARDE CONFIRMAÇÃO** antes de modificar.

### ETAPA 2: MAPEAR VARIANTES

| Variante | Uso | Classes Tailwind (com dark mode) |
|----------|-----|----------------------------------|
| **Primary** | CTA, Salvar, Confirmar | `bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200` |
| **Secondary** | Cancelar, Voltar | `bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700` |
| **Ghost** | Links, opções | `text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800` |
| **Destructive** | Deletar, Remover | `bg-red-600 text-white hover:bg-red-700` |

### ETAPA 3: REFATORAR BOTÕES

**PRIMARY (Preto):**
```jsx
// Helper (RECOMENDADO)
import { getButtonClasses } from '../styles/design-tokens'

<button className={getButtonClasses('primary')}>
  Salvar
</button>

// OU classes inline completas:
<button className="px-4 py-2 bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 text-sm font-semibold rounded transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 font-['Open_Sans']">
  Salvar
</button>
```

**SECONDARY (Outline):**
```jsx
<button className={getButtonClasses('secondary')}>
  Cancelar
</button>

// OU:
<button className="px-4 py-2 bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 text-sm font-semibold rounded transition-all duration-150 focus:ring-2 focus:ring-gray-900/20 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-700">
  Cancelar
</button>
```

**GHOST:**
```jsx
<button className={getButtonClasses('ghost')}>
  Ver mais
</button>
```

**DESTRUCTIVE:**
```jsx
<button className={getButtonClasses('destructive')}>
  Deletar
</button>
```

### ETAPA 4: REMOVER CORES CYAN DE BOTÕES

⚠️ **CRÍTICO:** Buscar e substituir:

```bash
grep -rn "bg-blue-\|bg-cyan-\|bg-\[#60BED1\]" src/ --include="*.jsx" --include="*.tsx"
```

Se encontrar em BOTÕES:
- Botão principal → `bg-gray-900` (preto)
- Se é badge/ícone LIA → MANTER cyan (está correto)

**Cyan APENAS permitido em:**
- `<BrainIcon className="text-[#60BED1]">` (ícone LIA)
- `<Sparkles className="text-[#60BED1]">` (ícone LIA)
- Badges LIA: `className={getBadgeClasses('lia')}`

### ETAPA 5: TAMANHOS

```jsx
// Small (32px height)
<button className={getButtonClasses('primary', 'small')}>Pequeno</button>

// Default (40px height)
<button className={getButtonClasses('primary', 'default')}>Padrão</button>

// Large (48px height)
<button className={getButtonClasses('primary', 'large')}>Grande</button>
```

### VALIDAÇÃO FASE 2:

Por arquivo:
```
✅ src/components/CandidateCard.jsx
   Botões totais: 8
   Botões refatorados: 8 (100%)
   - Primary (preto): 3
   - Secondary (outline): 2
   - Ghost: 2
   - Destructive: 1
   Cyan removido de botões: 2 (agora preto)
   Dark mode aplicado: ✅
   Helper function usado: ✅
```

**CONTADORES FINAIS:**
```
✅ FASE 2A COMPLETA

Arquivos processados: 10 de 10 (100%)
Botões refatorados: X de X (100%)
- Primary: Y
- Secondary: Z
- Ghost: W
- Destructive: V

Cores cyan removidas de botões: N
Brain icons cyan mantidos: M (correto)
Dark mode aplicado: 100%

Próxima: Fase 2B (mais arquivos) ou Fase 3 (Inputs)
```

Aguarde validação.
```

---

# FASE 3: INPUTS E FORMS

```markdown
# FASE 3: INPUTS E FORMS (Máximo 8 Arquivos)

## PRÉ-REQUISITO:
Fase 2 (botões) 100% completa.

## TAREFA:

### ETAPA 1: INVENTÁRIO DE INPUTS

```bash
grep -r "<input\|<Input\|<textarea\|<select" src/ --include="*.jsx" --include="*.tsx" | cut -d: -f1 | sort | uniq -c | sort -rn | head -8
```

### ETAPA 2: REFATORAR INPUTS

**TEXT INPUT:**
```jsx
import { getInputClasses } from '../styles/design-tokens'

<div className="space-y-1.5">
  <label 
    htmlFor="nome" 
    className="block text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans']"
  >
    Nome
  </label>
  <input
    id="nome"
    type="text"
    placeholder="Digite seu nome"
    className={getInputClasses(false)}
  />
  <p className="text-xs text-gray-600 dark:text-gray-400">Digite seu nome completo</p>
</div>

// OU classes completas:
<input
  type="text"
  className="w-full px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 bg-white border border-gray-300 rounded transition-all duration-150 hover:border-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 focus:outline-none disabled:bg-gray-50 disabled:border-gray-200 disabled:text-gray-500 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:focus:border-gray-400"
/>
```

**INPUT COM ERRO:**
```jsx
<input
  type="email"
  className={getInputClasses(true)} // true = com erro
  aria-invalid="true"
/>
<p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
  <svg className="w-3 h-3">...</svg>
  Email inválido
</p>
```

**TEXTAREA:**
```jsx
<textarea
  rows={4}
  placeholder="Descreva aqui..."
  className="w-full px-3 py-2 text-sm text-gray-900 bg-white border border-gray-300 rounded resize-none focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 focus:outline-none dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600"
/>
```

**SELECT:**
```jsx
<select className="w-full px-3 py-2 text-sm text-gray-900 bg-white border border-gray-300 rounded focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 focus:outline-none cursor-pointer dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600">
  <option value="">Selecione...</option>
  <option value="active">Ativo</option>
</select>
```

**CHECKBOX:**
```jsx
<div className="flex items-start gap-2">
  <input
    type="checkbox"
    id="terms"
    className="w-4 h-4 mt-0.5 text-gray-900 border-gray-300 rounded focus:ring-2 focus:ring-gray-900/20 cursor-pointer accent-gray-900"
  />
  <label htmlFor="terms" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
    Aceito os termos
  </label>
</div>
```

**RADIO:**
```jsx
<div className="space-y-2">
  <div className="flex items-center gap-2">
    <input
      type="radio"
      id="option1"
      name="options"
      className="w-4 h-4 text-gray-900 border-gray-300 focus:ring-2 focus:ring-gray-900/20 cursor-pointer accent-gray-900"
    />
    <label htmlFor="option1" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
      Opção 1
    </label>
  </div>
</div>
```

### ETAPA 3: PADRONIZAR LABELS

TODOS os inputs devem ter:
- Label: `text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans']`
- htmlFor ligado ao id do input
- Descrição opcional: `text-xs text-gray-600 dark:text-gray-400`

### VALIDAÇÃO FASE 3:

```
✅ FASE 3 COMPLETA

Arquivos: 8 de 8 (100%)
Inputs refatorados: X de X (100%)
Labels padronizados: X
Dark mode aplicado: 100%

Próxima: Fase 4 (Cards)
```

Aguarde validação.
```

---

# FASE 4: CARDS E CONTAINERS

```markdown
# FASE 4: CARDS E CONTAINERS (Máximo 10 Arquivos)

## PRÉ-REQUISITO:
Fases 2 e 3 100% completas.

## TAREFA:

### ETAPA 1: INVENTÁRIO DE CARDS

```bash
grep -rn "className.*bg-white.*rounded\|className.*card\|className.*shadow" src/ --include="*.jsx" --include="*.tsx" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

### ETAPA 2: REFATORAR CARDS

⚠️ **CRÍTICO:** Cards usam `rounded-xl` (NÃO rounded-md)

**CARD BÁSICO:**
```jsx
import { getCardClasses } from '../styles/design-tokens'

<div className={`${getCardClasses('default')} p-6`}>
  <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2 font-['Open_Sans']">
    Título do Card
  </h3>
  <p className="text-sm text-gray-600 dark:text-gray-400">
    Descrição do conteúdo.
  </p>
</div>

// OU classes completas:
<div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 dark:bg-gray-800 dark:border-gray-700">
  ...
</div>
```

**CARD INTERATIVO:**
```jsx
<div className={`${getCardClasses('interactive')} p-6`}>
  ...
</div>

// OU:
<div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer dark:bg-gray-800 dark:border-gray-700">
  ...
</div>
```

**CARD COM GLASSMORPHISM:**
```jsx
<div className={`${getCardClasses('glass')} p-6`}>
  ...
</div>
```

**CARD COM HEADER E FOOTER:**
```jsx
<div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden dark:bg-gray-800 dark:border-gray-700">
  {/* Header */}
  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
    <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
      Título
    </h3>
  </div>
  
  {/* Body */}
  <div className="p-6">
    <p className="text-sm text-gray-600 dark:text-gray-400">
      Conteúdo principal.
    </p>
  </div>
  
  {/* Footer */}
  <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2 dark:bg-gray-900 dark:border-gray-700">
    <button className={getButtonClasses('secondary', 'small')}>
      Cancelar
    </button>
    <button className={getButtonClasses('primary', 'small')}>
      Confirmar
    </button>
  </div>
</div>
```

### ETAPA 3: REMOVER

- [ ] `rounded-md` em cards → trocar por `rounded-xl`
- [ ] Shadows excessivos (shadow-xl, shadow-2xl) → `shadow-sm`
- [ ] Bordas grossas (border-2, border-4) → `border`
- [ ] Gradientes em backgrounds → cores sólidas
- [ ] Cores não-gray (bg-blue-100, bg-purple-50) → grayscale

### VALIDAÇÃO FASE 4:

```
✅ FASE 4 COMPLETA

Arquivos: 10 de 10
Cards refatorados: X de X (100%)
- rounded-md → rounded-xl: Y
- shadows ajustados: Z
- dark mode aplicado: 100%

Próxima: Fase 5 (Navegação)
```

Aguarde validação.
```

---

# FASE 5: NAVEGAÇÃO E SIDEBAR

```markdown
# FASE 5: NAVEGAÇÃO E SIDEBAR

## PRÉ-REQUISITO:
Fase 4 100% completa.

## TAREFA:

### ETAPA 1: INVENTÁRIO

Identificar:
- Sidebar principal
- Menus de navegação
- Breadcrumbs
- Tabs

### ETAPA 2: REFATORAR SIDEBAR

⚠️ **CRÍTICO:** Sidebar usa `font-sidebar` (Source Serif 4)

```jsx
<nav className="w-64 h-screen bg-white border-r border-gray-200 p-4 dark:bg-gray-900 dark:border-gray-800">
  {/* Logo com brain icon cyan */}
  <div className="mb-6">
    <div className="flex items-center gap-2 px-3 py-2">
      <BrainIcon className="w-6 h-6 text-[#60BED1]" /> {/* Cyan PERMITIDO aqui */}
      <span className="text-lg font-bold text-gray-900 dark:text-gray-100 font-['Open_Sans']">
        LIA
      </span>
    </div>
  </div>
  
  <div className="space-y-1">
    {/* Item ativo - Source Serif 4 */}
    <a 
      href="#" 
      className="flex items-center gap-3 px-3 py-2 bg-gray-100 text-gray-900 rounded-md font-semibold text-sm font-['Source_Serif_4'] dark:bg-gray-800 dark:text-gray-100"
    >
      <DashboardIcon className="w-5 h-5" />
      <span>Dashboard</span>
    </a>
    
    {/* Item inativo - Source Serif 4 */}
    <a 
      href="#" 
      className="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-md text-sm font-['Source_Serif_4'] dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
    >
      <JobsIcon className="w-5 h-5" />
      <span>Vagas</span>
    </a>
  </div>
</nav>
```

### ETAPA 3: TABS

```jsx
{/* Tabs - Open Sans (NÃO Source Serif 4) */}
<div className="border-b border-gray-200 dark:border-gray-700">
  <nav className="flex gap-4">
    {/* Tab ativa */}
    <button className="px-4 py-2 text-sm font-semibold text-gray-900 border-b-2 border-gray-900 dark:text-gray-100 dark:border-gray-100">
      Detalhes
    </button>
    
    {/* Tab inativa */}
    <button className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent dark:text-gray-400 dark:hover:text-gray-100">
      Histórico
    </button>
  </nav>
</div>
```

### ETAPA 4: BREADCRUMBS

```jsx
<nav className="flex items-center gap-2 text-sm">
  <a href="#" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
    Home
  </a>
  <ChevronRightIcon className="w-4 h-4 text-gray-400" />
  <a href="#" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
    Vagas
  </a>
  <ChevronRightIcon className="w-4 h-4 text-gray-400" />
  <span className="text-gray-900 font-semibold dark:text-gray-100">
    Desenvolvedor
  </span>
</nav>
```

### VALIDAÇÃO FASE 5:

```
✅ FASE 5 COMPLETA

Sidebar: Source Serif 4 aplicado ✅
Tabs: Open Sans aplicado ✅
Breadcrumbs: padronizados ✅
Brain icon: cyan mantido ✅
Dark mode: 100%

Próxima: Fase 6 (Modais)
```

Aguarde validação.
```

---

# FASE 6: MODAIS E COMPONENTES AVANÇADOS

```markdown
# FASE 6: MODAIS E COMPONENTES AVANÇADOS

## TAREFA:

### MODAL BÁSICO

```jsx
{/* Overlay */}
<div className="fixed inset-0 bg-gray-900/50 dark:bg-gray-950/70 z-50 flex items-center justify-center">
  
  {/* Modal */}
  <div 
    className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 dark:bg-gray-800"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
  >
    {/* Header */}
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <h2 
        id="modal-title" 
        className="text-lg font-semibold text-gray-900 dark:text-gray-100"
      >
        Título do Modal
      </h2>
      <button 
        className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
        aria-label="Fechar"
      >
        <XIcon className="w-5 h-5" />
      </button>
    </div>
    
    {/* Body */}
    <div className="px-6 py-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Conteúdo do modal.
      </p>
    </div>
    
    {/* Footer */}
    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2 dark:bg-gray-900 dark:border-gray-700">
      <button className={getButtonClasses('secondary')}>
        Cancelar
      </button>
      <button className={getButtonClasses('primary')}>
        Confirmar
      </button>
    </div>
  </div>
</div>
```

### DROPDOWN MENU

```jsx
<div className="relative">
  <button 
    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
  >
    <span>Opções</span>
    <ChevronDownIcon className="w-4 h-4" />
  </button>
  
  {/* Dropdown */}
  <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50 dark:bg-gray-800 dark:border-gray-700">
    <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700">
      Editar
    </a>
    <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700">
      Duplicar
    </a>
    <div className="border-t border-gray-200 my-1 dark:border-gray-700"></div>
    <a href="#" className="block px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20">
      Deletar
    </a>
  </div>
</div>
```

### ACCORDION

```jsx
<div className="border border-gray-200 rounded-xl overflow-hidden dark:border-gray-700">
  <button 
    className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 text-left dark:bg-gray-800 dark:hover:bg-gray-700"
  >
    <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
      Pergunta Frequente
    </span>
    <ChevronDownIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
  </button>
  
  <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 dark:bg-gray-900 dark:border-gray-700">
    <p className="text-sm text-gray-600 dark:text-gray-400">
      Resposta da pergunta.
    </p>
  </div>
</div>
```

### VALIDAÇÃO FASE 6:

```
✅ FASE 6 COMPLETA

Modais: rounded-xl, dark mode ✅
Dropdowns: padronizados ✅
Accordions: padronizados ✅

Próxima: Fase 7 (Badges)
```
```

---

# FASE 7: BADGES E UTILITIES

```markdown
# FASE 7: BADGES E UTILITIES

## BADGES SEMÂNTICOS

```jsx
import { getBadgeClasses } from '../styles/design-tokens'

{/* Semânticos - para status */}
<span className={getBadgeClasses('success')}>Ativo</span>
<span className={getBadgeClasses('warning')}>Pendente</span>
<span className={getBadgeClasses('error')}>Rejeitado</span>
<span className={getBadgeClasses('info')}>Info</span>
<span className={getBadgeClasses('neutral')}>Neutro</span>

{/* LIA - único caso onde cyan é permitido */}
<span className={getBadgeClasses('lia')}>
  <Sparkles className="w-3 h-3 mr-1" />
  LIA
</span>
```

### CLASSES INLINE:

```jsx
{/* Success */}
<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
  Ativo
</span>

{/* Warning */}
<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800">
  Pendente
</span>

{/* Error */}
<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">
  Rejeitado
</span>

{/* Neutral */}
<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
  Neutro
</span>

{/* LIA (cyan permitido) */}
<span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium text-[#60BED1] border border-[#60BED1]/20 bg-[#60BED1]/10">
  <Sparkles className="w-3 h-3 mr-1" />
  LIA
</span>
```

## TOOLTIPS

```jsx
<div className="relative group inline-block">
  <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
    <InfoIcon className="w-5 h-5" />
  </button>
  
  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none dark:bg-gray-700">
    Informação adicional
    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
  </div>
</div>
```

## TOASTS

```jsx
{/* Toast Success */}
<div className="flex items-start gap-3 bg-white border border-green-200 rounded-xl shadow-lg p-4 max-w-sm dark:bg-gray-800 dark:border-green-800">
  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center dark:bg-green-900/30">
    <CheckIcon className="w-3 h-3 text-green-600 dark:text-green-400" />
  </div>
  <div className="flex-1 min-w-0">
    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Sucesso!</p>
    <p className="text-xs text-gray-600 mt-0.5 dark:text-gray-400">Operação realizada.</p>
  </div>
  <button className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
    <XIcon className="w-4 h-4" />
  </button>
</div>
```

## LOADING STATES

```jsx
{/* Spinner */}
<div className="flex items-center justify-center p-12">
  <svg className="w-8 h-8 animate-spin text-gray-900 dark:text-gray-100" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
  </svg>
</div>

{/* Skeleton */}
<div className="animate-pulse space-y-4">
  <div className="h-6 bg-gray-200 rounded w-1/3 dark:bg-gray-700"></div>
  <div className="space-y-2">
    <div className="h-4 bg-gray-200 rounded dark:bg-gray-700"></div>
    <div className="h-4 bg-gray-200 rounded w-5/6 dark:bg-gray-700"></div>
  </div>
</div>
```

### VALIDAÇÃO FASE 7:

```
✅ FASE 7 COMPLETA

Badges semânticos: ✅
Badge LIA (cyan): ✅
Tooltips: ✅
Toasts: ✅
Loading states: ✅
Dark mode: 100%

Próxima: Fase 8 (Validação Final)
```
```

---

# FASE 8: VALIDAÇÃO FINAL

```markdown
# FASE 8: VALIDAÇÃO FINAL

## CHECKLIST COMPLETO

### Tipografia
- [ ] Open Sans (85%): body, headers, labels, botões, cards
- [ ] Inter (10%): APENAS métricas, KPIs, números em tabelas
- [ ] Source Serif 4 (5%): APENAS sidebar/navigation
- [ ] Source Serif 4 NÃO usado em card titles ou headers

### Cores
- [ ] Botões primary: bg-gray-900 (preto)
- [ ] Cyan (#60BED1) APENAS em: Brain icon, Sparkles, badges LIA
- [ ] Sem cyan em botões, cards, inputs
- [ ] 90% grayscale + 10% accent

### Espaçamento
- [ ] Base 4px aplicado (p-1=4px, p-2=8px, p-4=16px)

### Componentes
- [ ] Cards: rounded-xl (não rounded-md)
- [ ] Focus ring: ring-2 ring-gray-900/20 (grayscale)
- [ ] Dark mode em todos os componentes

### Arquivos
- [ ] design-tokens.js com helpers
- [ ] tailwind.config.js com 3 fonts + cores WeDo
- [ ] index.css com @layer base/components/utilities

## COMANDOS DE VALIDAÇÃO

```bash
# Verificar se não há cyan em botões
grep -rn "bg-cyan\|bg-\[#60BED1\]" src/ --include="*.jsx" --include="*.tsx" | grep -i button

# Verificar se Source Serif 4 não está em cards
grep -rn "Source_Serif_4\|font-sidebar" src/ --include="*.jsx" --include="*.tsx" | grep -i card

# Verificar rounded-xl em cards (não deveria ter rounded-md)
grep -rn "rounded-md" src/ --include="*.jsx" --include="*.tsx" | grep -i card

# Verificar dark mode
grep -rn "dark:" src/ --include="*.jsx" --include="*.tsx" | wc -l
```

## RESPOSTA FINAL

```
✅ VALIDAÇÃO FINAL COMPLETA

Design System LIA v4.1 implementado: 100%

Tipografia:
- Open Sans (85%): ✅
- Inter (10%): ✅
- Source Serif 4 (5%): ✅

Cores:
- Botões pretos (gray-900): ✅
- Cyan apenas LIA: ✅
- 90% grayscale: ✅

Componentes:
- Cards rounded-xl: ✅
- Focus ring grayscale: ✅
- Dark mode: ✅

Arquivos:
- design-tokens.js: ✅
- tailwind.config.js: ✅
- index.css: ✅

PROJETO PADRONIZADO! 🎉
```
```

---

# RESUMO RÁPIDO

## Stack:
| Item | Valor |
|------|-------|
| Framework | React (.jsx/.tsx) |
| Styling | Tailwind CSS |
| NÃO usar | Vue, Vuetify, arquivos .vue |

## Especificações Design System v4.1:

| Aspecto | Valor |
|---------|-------|
| **Botão Primary** | `bg-gray-900` (preto) |
| **Cyan** | APENAS LIA (brain icon, sparkles) |
| **Open Sans** | 85% - UI geral, body, headers |
| **Inter** | 10% - métricas/KPIs APENAS |
| **Source Serif 4** | 5% - sidebar APENAS |
| **Espaçamento** | Base 4px |
| **Cards** | rounded-xl |
| **Focus ring** | ring-gray-900/20 (grayscale) |
| **Dark mode** | Obrigatório em todos componentes |

## Estratégia de Implementação:
1. Inventário primeiro (grep, listar)
2. Lote pequeno (máx 10 arquivos)
3. Refatorar com classes Tailwind
4. Validar com contadores
5. Dark mode em tudo
6. Só prosseguir se 100%

## Regras Críticas:
- ⚠️ Source Serif 4 **NUNCA** em card titles ou headers
- ⚠️ Cyan **NUNCA** em botões ou inputs
- ⚠️ Cyan **APENAS** em: Brain icon, Sparkles, Bot icon, badges LIA
- ⚠️ Cards sempre `rounded-xl`, **NUNCA** `rounded-md`
- ⚠️ Body usa Open Sans, **NÃO** Inter

---

## REFERÊNCIAS

- **Design System completo:** `plataforma-lia/docs/design-system/00-design-system-v4.md`
- **Tokens TypeScript:** `plataforma-lia/src/lib/design-tokens.ts`
- **Backup:** `plataforma-lia/docs/design-system/00-design-system-v4-backup.md`

---

> **Última atualização:** Fevereiro 2026  
> **Versão:** 4.1 Corrigida
