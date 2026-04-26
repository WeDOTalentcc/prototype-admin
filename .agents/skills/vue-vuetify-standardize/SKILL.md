---
name: vue-vuetify-standardize
description: "Padronizacao visual e estrutural Vue 3 + Vuetify 3 + Nuxt 3 conforme Design System LIA v4.2.1. Use ao criar, converter ou auditar componentes Vue/Vuetify no projeto v5. Cobre 10 passos: setup tokens, tokenizacao hex/cores, residual color tokens, monolith split, bridge React-Vue, design audit Notion/ElevenLabs, code review profundo, auditoria 14 dimensoes, multi-agent workflow, e validacao final. Skill 100% autocontida — todos os tokens, mapeamentos e regras estao inline."
---

# Vue/Vuetify Standardize — DS v4.2.1 para Vue 3 + Vuetify 3

Aplica o Design System LIA v4.2.1 em componentes Vue 3 + Vuetify 3 + Nuxt 3.
Workflow de 10 passos + 1 pre-step (PASSO 0) para padronizacao, conversao e auditoria.

> **Contagem de passos:** PASSO 0 e um pre-step obrigatorio apenas para telas novas.
> PASSOs 1-10 sao o workflow principal sequencial.

> **Repositorio alvo:** `WeDOTalent/recruiter_agent_v5` (GitHub)
> **Stack:** Vue 3 (Composition API) + Vuetify 3 + Nuxt 3 + Pinia + TypeScript
> **Skill autocontida:** Todos os tokens, cores, mapeamentos e regras necessarios estao inline neste documento. Nao depende de acesso a nenhum outro repositorio ou skill.

## Quando ativar

- Quando o usuario disser "padroniza no Vue", "aplica DS no v5", "audita esse componente Vue" ou "adequa ao design system Vuetify"
- Ao criar tela, componente ou layout novo em `recruiter_agent_v5` (Vue 3 + Vuetify 3 + Nuxt 3)
- Ao converter componente React+Tailwind do `plataforma-lia` para Vue+Vuetify (porte React->Vue)
- Ao revisar PR que toca arquivos `.vue`, `app.vue`, `nuxt.config.ts` ou tema Vuetify no v5
- Ao auditar conformidade visual de tela Vue existente (cores, tipografia Open Sans/Inter/JetBrains, border-radius)
- Ao tokenizar hex literais (`#000`, `bg-blue-500`, `color: red`) restantes em arquivo `.vue`
- Ao quebrar monolito Vue (>1500 linhas) em sub-componentes
- Ao configurar tema Vuetify do zero ou ao atualizar `vuetify.options.ts`

## Quando NAO ativar

- Componente React+Tailwind no `plataforma-lia` -> usar `design-standardize`
- Preparacao de codigo React para futura migracao Vue (sem tocar arquivo `.vue` ainda) -> usar `vue-migration-prep`
- Decidir intencao estetica de tela nova de entrada/branding -> usar `frontend-design` antes
- Escolher pattern de composicao (factory, observer, strategy) no codigo Vue -> usar `design-patterns`
- Mudanca de copy/texto em arquivo i18n sem alteracao visual

## Filosofia

> "90% monocromatico, 10% acento WeDo. Botoes sao pretos. Cyan e da LIA."
> "A interface e previsivel para o recruiter. A beleza vem da precisao, nao da decoracao."

---

## PASSO 0: Intencao Estetica (novas telas)

> Obrigatorio para telas novas. Para refatoracoes de componentes existentes, pule para PASSO 1.

### 5 Perguntas Antes de Codificar

**P1 — Problema e usuario:** O que esta tela resolve? Quem a usa e com que frequencia?

| Perfil | Implicacao |
|--------|------------|
| Recruiter diario | Previsibilidade e feature. Zero surpresas. Vuetify defaults. |
| Candidato primeira visita | Impacto visual permitido. Backgrounds atmosfericos. |
| Admin configurando | Densidade funcional. `v-data-table` com muitas colunas. |

**P2 — Sentimento alvo:** confianca | boas-vindas | foco | descoberta

**P3 — Memorabilidade dentro do DS:** O que torna inesquecivel?
- Uma palavra em `color="info"` (cyan) no lugar certo
- Um `v-card` com `rounded="xl"` e `elevation="0"` num fundo `bg-grey-lighten-5`
- Tipografia de impacto (`text-h3 font-weight-light`) na headline
- Composicao assimetrica com `v-row` + `v-col` desproporcionais

**P4 — Tipo de contexto:**
```
TELA DE ENTRADA / BRANDING (login, onboarding, landing)
→ Liberdade para composicao atmosferica, rounded="xl", elevation alto.
→ Ainda dentro do DS — mas com padroes atmosfericos.

INTERFACE INTERNA (Kanban, tabelas, modais, settings)
→ Padronizacao estrita. Pule para PASSO 1.
```

**P5 — Composicao espacial:**

| Padrao | Vuetify | Caracteristica |
|--------|---------|----------------|
| Card centralizado | `v-container` + `v-row justify="center"` | Welcome page |
| Dois paineis | `v-row` + `v-col cols="5"` + `v-col cols="7"` | Login |
| Lista/tabela | `v-data-table` | Densidade funcional |
| Sidebar + main | `v-navigation-drawer` + `v-main` | Settings |

---

## PASSO 1: Setup Tokens Base (vuetify.config.ts)

Configurar o tema Vuetify com os tokens do DS v4.2.1.

### 1.1 Paleta de Cores Completa (extraida do codigo fonte)

#### Escala Monocromatica (Core UI — 90%)

| Token CSS | Hex | Uso |
|-----------|-----|-----|
| `--white` | `#FFFFFF` | Superficie primaria, cards |
| `--gray-50` | `#F9FAFB` | Background pagina, hover sutil |
| `--gray-100` | `#F3F4F6` | Backgrounds alternados, dividers sutis |
| `--gray-200` | `#E5E7EB` | Borders padrao, card backgrounds |
| `--gray-300` | `#D1D5DB` | Borders medios, text disabled |
| `--gray-400` | `#9CA3AF` | Texto desabilitado, placeholders |
| `--gray-500` | `#6B7280` | Texto secundario |
| `--gray-600` | `#4B5563` | Texto secundario enfatizado, labels |
| `--gray-800` | `#1F2937` | Texto primario, headings |
| `--gray-950` | `#030712` | Enfase maxima, botoes primarios |

#### Acentos WeDo/LIA (10% — uso estrategico)

| Token CSS | Hex | Uso EXCLUSIVO |
|-----------|-----|---------------|
| `--wedo-cyan` | `#60BED1` | LIA brain icon, badges IA, sparkles, highlights inteligentes |
| `--wedo-cyan-dark` | `#4DA8BB` | Variacao escura do cyan |
| `--wedo-green` | `#5DA47A` | Candidatos aprovados, sucesso |
| `--wedo-orange` | `#D19960` | Alertas, urgencia |
| `--wedo-purple` | `#9860D1` | Insights, premium, analise IA |
| `--wedo-magenta` | `#D160AB` | Urgencia critica, prioridade alta |
| `--wedo-coral` | `#E16162` | Acento identidade (uso minimo) |
| `--wedo-amber` | `#F59E0B` | Warning vibrante |

#### Status Semanticos (WCAG 1.4.1)

| Token CSS | Hex | Uso |
|-----------|-----|-----|
| `--status-success` | `#16A34A` | Aprovado, concluido |
| `--status-error` | `#DC2626` | Reprovado, erro, destrutivo |
| `--status-warning` | `#D97706` | Pendente, atencao |

#### Marca LIA

| Token CSS | Hex (Light) | Hex (Dark) | Uso |
|-----------|-------------|------------|-----|
| `--lia-brand-primary` | `#C74446` | `#EF4444` | Vermelho coral — identidade LIA |
| `--lia-brand-primary-hover` | `#B53B3D` | `#DC2626` | Hover do brand |

### 1.2 Tema Vuetify

```typescript
import { createVuetify } from 'vuetify'

const liaLightTheme = {
  dark: false,
  colors: {
    primary: '#111827',
    'on-primary': '#FFFFFF',
    secondary: '#F3F4F6',
    'on-secondary': '#111827',
    accent: '#60BED1',
    surface: '#FFFFFF',
    background: '#F9FAFB',

    success: '#16A34A',
    warning: '#D97706',
    error: '#DC2626',
    info: '#60BED1',

    'grey-darken-4': '#111827',
    'grey-darken-3': '#1F2937',
    'grey-darken-2': '#374151',
    'grey-darken-1': '#4B5563',
    grey: '#6B7280',
    'grey-lighten-1': '#9CA3AF',
    'grey-lighten-2': '#D1D5DB',
    'grey-lighten-3': '#E5E7EB',
    'grey-lighten-4': '#F3F4F6',
    'grey-lighten-5': '#F9FAFB',

    'wedo-cyan': '#60BED1',
    'wedo-cyan-dark': '#4DA8BB',
    'wedo-green': '#5DA47A',
    'wedo-orange': '#D19960',
    'wedo-purple': '#9860D1',
    'wedo-magenta': '#D160AB',
    'wedo-coral': '#E16162',
    'wedo-amber': '#F59E0B',
  },
}

const liaDarkTheme = {
  dark: true,
  colors: {
    primary: '#F9FAFB',
    'on-primary': '#111827',
    secondary: '#26292B',
    'on-secondary': '#F9FAFB',
    accent: '#60BED1',
    surface: '#1A1D1F',
    background: '#0F1113',

    success: '#16A34A',
    warning: '#D97706',
    error: '#EF4444',
    info: '#60BED1',

    'grey-darken-4': '#F9FAFB',
    'grey-darken-3': '#E5E7EB',
    'grey-darken-2': '#D1D5DB',
    'grey-darken-1': '#9CA3AF',
    grey: '#6B7280',
    'grey-lighten-1': '#4B5563',
    'grey-lighten-2': '#374151',
    'grey-lighten-3': '#2D3748',
    'grey-lighten-4': '#1A1D1F',
    'grey-lighten-5': '#0F1113',

    'wedo-cyan': '#60BED1',
    'wedo-cyan-dark': '#4DA8BB',
    'wedo-green': '#5DA47A',
    'wedo-orange': '#D19960',
    'wedo-purple': '#9860D1',
    'wedo-magenta': '#D160AB',
    'wedo-coral': '#E16162',
    'wedo-amber': '#F59E0B',
  },
}
// NOTA: dark theme INVERTE a escala grey — grey-darken-4 vira claro (texto),
// grey-lighten-5 vira escuro (fundo). Isso garante que color="grey-darken-4"
// funcione corretamente em ambos os modos.

export default createVuetify({
  theme: {
    defaultTheme: 'liaLight',
    themes: {
      liaLight: liaLightTheme,
      liaDark: liaDarkTheme,
    },
  },
  defaults: {
    VBtn: { variant: 'flat', rounded: 'md' },
    VCard: { variant: 'outlined', rounded: 'md', elevation: 0 },
    VTextField: { variant: 'outlined', density: 'compact' },
    VSelect: { variant: 'outlined', density: 'compact' },
    VTextarea: { variant: 'outlined', density: 'compact' },
    VChip: { size: 'small', variant: 'tonal' },
    VSwitch: { color: 'grey-darken-4' },
    VCheckbox: { color: 'grey-darken-4' },
    VRadio: { color: 'grey-darken-4' },
    VPagination: { color: 'grey-darken-4', rounded: 'md' },
    VTabs: { density: 'compact', color: 'grey-darken-4' },
    VDialog: { maxWidth: 600 },
  },
})
```

### 1.3 Tipografia SCSS

```scss
// _lia-vuetify-settings.scss
@use 'vuetify/settings' with (
  $body-font-family: ("Open Sans", sans-serif),
  $font-size-root: 16px,
  $line-height-root: 1.5,
  $border-radius-root: 8px,
  $border-color-root: rgba(0, 0, 0, 0.08),
  $spacer: 4px,
  $transition-duration-root: 0.2s,
);
```

### 1.4 CSS Variables Bridge (Light + Dark)

```css
/* lia-bridge.css — importar no app.vue ou nuxt.config */
:root {
  /* Tipografia */
  --lia-font-primary: "Open Sans", sans-serif;
  --lia-font-data: "Inter", sans-serif;
  --lia-font-mono: "JetBrains Mono", monospace;

  /* Tamanhos (DS v4.2.1) */
  --font-size-xs: 0.6875rem;    /* 11px — UI labels, badges, status */
  --font-size-sm-ui: 0.75rem;   /* 12px — helpers, captions */
  --font-size-base-ui: 0.8125rem; /* 13px — corpo compacto, inputs */

  /* Escala Gray canonica (usada por StatusBadge e componentes) */
  --white: #FFFFFF;
  --gray-50: #F9FAFB;
  --gray-100: #F3F4F6;
  --gray-200: #E5E7EB;
  --gray-300: #D1D5DB;
  --gray-400: #9CA3AF;
  --gray-500: #6B7280;
  --gray-600: #4B5563;
  --gray-800: #1F2937;
  --gray-950: #030712;

  /* Backgrounds */
  --lia-bg-primary: #FFFFFF;
  --lia-bg-secondary: #F9FAFB;
  --lia-bg-tertiary: #F3F4F6;
  --lia-bg-elevated: #FFFFFF;

  /* Textos */
  --lia-text-primary: #111827;
  --lia-text-secondary: #6B7280;
  --lia-text-tertiary: #9CA3AF;
  --lia-text-disabled: #D1D5DB;
  --lia-text-inverse: #F9FAFB;

  /* Borders */
  --lia-border-subtle: #E5E7EB;
  --lia-border-default: #D1D5DB;
  --lia-border-medium: #9CA3AF;

  /* Interactive States */
  --lia-interactive-hover: #F3F4F6;
  --lia-interactive-active: #E5E7EB;
  --lia-interactive-focus: #111827;

  /* Shadows */
  --lia-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.02);
  --lia-shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.05);
  --lia-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07);
  --lia-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08);

  /* Marca */
  --lia-brand-primary: #C74446;
  --lia-brand-primary-hover: #B53B3D;
  --lia-brand-primary-light: #FEF2F2;

  /* Acentos WeDo */
  --wedo-cyan: #60BED1;
  --wedo-cyan-dark: #4DA8BB;
  --wedo-green: #5DA47A;
  --wedo-orange: #D19960;
  --wedo-purple: #9860D1;
  --wedo-magenta: #D160AB;
  --wedo-coral: #E16162;
  --wedo-amber: #F59E0B;

  /* Status Semanticos */
  --status-success: #16A34A;
  --status-error: #DC2626;
  --status-warning: #D97706;

  /* Botoes */
  --lia-btn-primary-bg: #111827;
  --lia-btn-primary-hover: #030712;
  --lia-btn-primary-text: #FFFFFF;
  --lia-btn-secondary-bg: transparent;
  --lia-btn-secondary-hover: #F3F4F6;
  --lia-btn-secondary-text: #111827;
  --lia-btn-secondary-border: #D1D5DB;
  --lia-btn-ghost-bg: transparent;
  --lia-btn-ghost-hover: #F3F4F6;
  --lia-btn-ghost-text: #4B5563;

  /* Badges */
  --lia-badge-neutral-bg: #F3F4F6;
  --lia-badge-neutral-text: #4B5563;
  --lia-badge-neutral-border: #E5E7EB;

  /* Input/Forms */
  --lia-input-bg: #FFFFFF;
  --lia-input-border: #D1D5DB;
  --lia-input-border-focus: #111827;
  --lia-input-text: #111827;
  --lia-input-placeholder: #9CA3AF;

  /* Info (cyan) */
  --lia-info-color: #60BED1;
  --lia-info-light: rgba(96, 190, 209, 0.08);

  /* Status por intensidade */
  --lia-status-high-bg: #111827;
  --lia-status-high-text: #FFFFFF;
  --lia-status-high-border: #111827;
  --lia-status-medium-bg: transparent;
  --lia-status-medium-text: #4B5563;
  --lia-status-medium-border: #D1D5DB;
  --lia-status-low-bg: transparent;
  --lia-status-low-text: #9CA3AF;
  --lia-status-low-border: #E5E7EB;

  /* Custom utility classes */
  --lia-border-radius: 8px;
}

/* ======== DARK MODE ======== */
/* Em Vuetify: .v-theme--liaDark ou html[data-theme="dark"] */
.v-theme--liaDark,
[data-theme="dark"] {
  /* Escala Gray invertida para dark mode */
  --gray-50: #0F1113;
  --gray-100: #1A1D1F;
  --gray-200: #2D3748;
  --gray-300: #374151;
  --gray-400: #4B5563;
  --gray-500: #6B7280;
  --gray-600: #9CA3AF;
  --gray-800: #E5E7EB;
  --gray-950: #F9FAFB;
  --white: #0F1113;

  --lia-bg-primary: #0F1113;
  --lia-bg-secondary: #1A1D1F;
  --lia-bg-tertiary: #26292B;
  --lia-bg-elevated: #1A1D1F;

  --lia-text-primary: #F9FAFB;
  --lia-text-secondary: #D1D5DB;
  --lia-text-tertiary: #9CA3AF;
  --lia-text-disabled: #6B7280;
  --lia-text-inverse: #111827;

  --lia-border-subtle: #2D3748;
  --lia-border-default: #374151;
  --lia-border-medium: #4B5563;

  --lia-interactive-hover: #26292B;
  --lia-interactive-active: #2D3748;
  --lia-interactive-focus: #F9FAFB;

  --lia-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
  --lia-shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.4);
  --lia-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.5);
  --lia-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.6);

  --lia-brand-primary: #EF4444;
  --lia-brand-primary-hover: #DC2626;
  --lia-brand-primary-light: #2D1D1E;

  --lia-info-color: #60BED1;
  --lia-info-light: rgba(96, 190, 209, 0.15);

  --lia-status-high-bg: #F9FAFB;
  --lia-status-high-text: #111827;
  --lia-status-high-border: #F9FAFB;
  --lia-status-medium-bg: transparent;
  --lia-status-medium-text: #D1D5DB;
  --lia-status-medium-border: #4B5563;
  --lia-status-low-bg: transparent;
  --lia-status-low-text: #6B7280;
  --lia-status-low-border: #374151;

  --lia-btn-primary-bg: #F9FAFB;
  --lia-btn-primary-hover: #FFFFFF;
  --lia-btn-primary-text: #111827;
  --lia-btn-secondary-bg: transparent;
  --lia-btn-secondary-hover: #26292B;
  --lia-btn-secondary-text: #D1D5DB;
  --lia-btn-secondary-border: #374151;
  --lia-btn-ghost-bg: transparent;
  --lia-btn-ghost-hover: #26292B;
  --lia-btn-ghost-text: #D1D5DB;

  --lia-badge-neutral-bg: #26292B;
  --lia-badge-neutral-text: #D1D5DB;
  --lia-badge-neutral-border: #374151;

  --lia-input-bg: #1A1D1F;
  --lia-input-border: #374151;
  --lia-input-border-focus: #F9FAFB;
  --lia-input-text: #F9FAFB;
  --lia-input-placeholder: #6B7280;
}

/* Custom utility classes (definir no projeto) */
.font-open-sans { font-family: var(--lia-font-primary); }
.font-inter { font-family: var(--lia-font-data); }
.font-mono { font-family: var(--lia-font-mono); }
.border-subtle { border-color: var(--lia-border-subtle); }
```

### Checklist PASSO 1
- [ ] `vuetify.config.ts` criado com `liaLight` e `liaDark`
- [ ] `_lia-vuetify-settings.scss` importado no Vuetify
- [ ] `lia-bridge.css` importado no `app.vue` ou `nuxt.config.ts` (com secao dark mode)
- [ ] Google Fonts: Open Sans (400,500,600,700), Inter (400,500,600,700), JetBrains Mono (400)
- [ ] `$vuetify.theme.current` funciona no template
- [ ] Dark mode toggle funciona e CSS vars respondem

---

## PASSO 2: Tokenizacao Hex/Cores

Substituir todos os hex hardcoded por tokens Vuetify ou CSS variables.

### Tabela de Substituicao

| Hex Hardcoded | Token Vuetify | CSS Variable |
|---------------|---------------|--------------|
| `#111827` | `color="grey-darken-4"` | `var(--lia-text-primary)` |
| `#1F2937` | `class="text-grey-darken-3"` | `var(--lia-text-primary)` |
| `#374151` | `class="text-grey-darken-2"` | — |
| `#4B5563` | `class="text-grey-darken-1"` | `var(--lia-text-secondary)` |
| `#6B7280` | `class="text-grey"` | `var(--lia-text-secondary)` |
| `#9CA3AF` | `class="text-grey-lighten-1"` | `var(--lia-text-tertiary)` |
| `#D1D5DB` | `class="text-grey-lighten-2"` | `var(--lia-text-disabled)` |
| `#E5E7EB` | `class="border-grey-lighten-3"` | `var(--lia-border-subtle)` |
| `#F3F4F6` | `class="bg-grey-lighten-4"` | `var(--lia-bg-tertiary)` |
| `#F9FAFB` | `class="bg-grey-lighten-5"` | `var(--lia-bg-secondary)` |
| `#FFFFFF` | `class="bg-surface"` | `var(--lia-bg-primary)` |
| `#030712` | `color="grey-darken-4"` (enfase maxima, usar com parcimonia) | `var(--gray-950)` |
| `#60BED1` | `color="info"` ou `color="wedo-cyan"` | `var(--wedo-cyan)` |
| `#4DA8BB` | `color="wedo-cyan-dark"` | `var(--wedo-cyan-dark)` |
| `#5DA47A` | `color="success"` ou `color="wedo-green"` | `var(--wedo-green)` |
| `#D19960` | `color="warning"` ou `color="wedo-orange"` | `var(--wedo-orange)` |
| `#9860D1` | `color="wedo-purple"` | `var(--wedo-purple)` |
| `#D160AB` | `color="wedo-magenta"` | `var(--wedo-magenta)` |
| `#DC2626` | `color="error"` | `var(--status-error)` |
| `#16A34A` | `color="success"` | `var(--status-success)` |
| `#D97706` | `color="warning"` | `var(--status-warning)` |

### Cores a ELIMINAR (deprecadas)

| Cor Atual | Substituir Por |
|-----------|---------------|
| `#FAFAFA` | `#F9FAFB` → `bg-grey-lighten-5` |
| `#E8E8E8` | `#E5E7EB` → `border-grey-lighten-3` |
| `#666666` | `#6B7280` → `text-grey` |
| `#999999` | `#9CA3AF` → `text-grey-lighten-1` |
| `#2D2D2D` | `#1F2937` → `text-grey-darken-3` |
| `#E4EBEF` | `#E5E7EB` → `border-grey-lighten-3` |
| `#E87575` | `#C74446` → `var(--lia-brand-primary)` (legacy coral) |

### Como Executar

```bash
grep -rn "#[0-9A-Fa-f]\{6\}" src/ --include="*.vue" --include="*.ts" --include="*.scss" | grep -v "node_modules\|dist\|.nuxt"
```

### Checklist PASSO 2
- [ ] Zero hex hardcoded em arquivos `.vue`
- [ ] Zero hex hardcoded em arquivos `.scss` (exceto `_lia-vuetify-settings.scss`)
- [ ] Cores deprecadas eliminadas (#FAFAFA, #E8E8E8, #666666, #999999, #2D2D2D, #E4EBEF, #E87575)
- [ ] Cores WeDo usando tokens Vuetify (`color="wedo-cyan"`) ou CSS vars

---

## PASSO 3: Residual Color Tokens

Buscar e corrigir usos residuais de classes Tailwind ou tokens antigos que nao existem no Vuetify.

### Classes Invalidas

| Classe Tailwind | Nao Existe em Vuetify | Substituir Por |
|-----------------|----------------------|----------------|
| `bg-gray-750` | N/A | `bg-grey-darken-2` |
| `bg-gray-850` | N/A | `bg-grey-darken-3` |
| Classes `text-gray-*` | Usar Vuetify helpers | `text-grey-darken-*` |
| Classes `bg-gray-*` | Usar Vuetify helpers | `bg-grey-lighten-*` |

### Regra 90/10 em Vuetify

A regra 90% monocromatico / 10% acento se traduz assim em Vuetify:

**90% — Componentes monocromaticos:**
- `v-btn color="grey-darken-4"` (primario)
- `v-btn color="grey-lighten-4"` (secundario)
- `v-btn variant="outlined"` (outline)
- `v-btn variant="text"` (ghost)
- `v-card variant="outlined"` (cards)
- `v-chip color="grey-lighten-4"` (badges neutros)

**10% — Acento WeDo (uso estrategico):**
- `color="wedo-cyan"` — APENAS em: brain icon LIA, badges LIA, sparkles, acento IA
- `color="wedo-green"` — APENAS em: candidatos aprovados, sucesso
- `color="wedo-orange"` — APENAS em: tempo, urgencia
- `color="wedo-purple"` — APENAS em: insights, recomendacoes IA
- `color="wedo-magenta"` — APENAS em: prioridade critica

### Classes Nativas vs Custom

> **Importante:** Diferenciar classes nativas Vuetify de classes custom do projeto.
>
> **Nativas Vuetify:** `d-flex`, `align-center`, `justify-space-between`, `text-body-2`,
> `font-weight-bold`, `pa-4`, `ma-2`, `rounded-md`, `bg-grey-lighten-4`, `text-grey-darken-1`,
> `elevation-0`, `ga-2` (gap)
>
> **Custom projeto (definir em `lia-bridge.css`):** `font-open-sans`, `font-inter`,
> `font-mono`, `border-subtle`, classes de utilidade especificas do DS

### Como Executar

```bash
grep -rn "bg-gray-\|text-gray-\|border-gray-" src/ --include="*.vue" | grep -v "grey"
grep -rn "text-blue-\|bg-blue-\|text-purple-\|bg-purple-\|text-green-5\|bg-green-5" src/ --include="*.vue"
```

### Checklist PASSO 3
- [ ] Zero classes Tailwind `*-gray-*` (usar `*-grey-*` do Vuetify)
- [ ] Zero cores de acento fora dos contextos permitidos
- [ ] Cyan nunca em botoes (apenas em elementos LIA)
- [ ] Regra 90/10 respeitada visualmente

---

## PASSO 4: Monolith Split

Componentes Vue com mais de 300 linhas devem ser divididos.

### Estrategia de Split

| Sinal | Acao |
|-------|------|
| Componente `.vue` > 300 linhas | Extrair sub-componentes |
| `<script setup>` > 100 linhas | Extrair composable `useXxx.ts` |
| Template com > 5 niveis de aninhamento | Extrair componentes filhos |
| Multiplos `v-dialog` no mesmo componente | Um componente por dialog |
| Multiplos `v-tab-window-item` com logica propria | Um componente por tab |

### Padrao de Split

```
ComponenteGrande.vue (500 linhas)
↓ dividir em:
├── ComponenteGrande.vue (150 linhas — template orquestrador)
├── ComponenteGrandeHeader.vue (80 linhas)
├── ComponenteGrandeTable.vue (120 linhas)
├── ComponenteGrandeDialog.vue (100 linhas)
└── composables/useComponenteGrande.ts (50 linhas — logica)
```

### Regra do Composable

Extrair logica em composable quando:
- Mais de 3 `ref()` no `<script setup>`
- Mais de 2 `watch()` ou `watchEffect()`
- Mais de 1 `onMounted()` com fetch
- Logica reutilizavel entre componentes

```typescript
// composables/useCandidateFilter.ts
import { ref, computed, watch } from 'vue'
import type { FilterState } from '@/types/candidate'

export function useCandidateFilter(jobId: Ref<string>) {
  const filters = ref<FilterState>(defaultFilters)
  const activeCount = computed(() =>
    Object.values(filters.value).filter(Boolean).length
  )

  watch(jobId, () => {
    filters.value = defaultFilters
  })

  function applyFilter(partial: Partial<FilterState>) {
    filters.value = { ...filters.value, ...partial }
  }

  return { filters, activeCount, applyFilter }
}
```

### Como Executar

```bash
find src/ -name "*.vue" -exec wc -l {} + | sort -rn | head -20
find src/composables/ -name "*.ts" -exec wc -l {} + | sort -rn | head -10
```

### Checklist PASSO 4
- [ ] Zero componentes `.vue` > 300 linhas
- [ ] Zero `<script setup>` > 100 linhas
- [ ] Composables extraidos para logica complexa
- [ ] Cada `v-dialog` em componente separado

---

## PASSO 5: Bridge React → Vue

Tabela de mapeamento para conversao de componentes React+Tailwind para Vue+Vuetify.

### 5.1 Componentes shadcn/ui → Vuetify 3

| shadcn/ui (React) | Vuetify 3 (Vue) | Props-chave DS v4.2.1 |
|---|---|---|
| `<Button variant="default">` | `<v-btn color="grey-darken-4" variant="flat">` | Primario PRETO |
| `<Button variant="destructive">` | `<v-btn color="error" variant="flat">` | Vermelho |
| `<Button variant="outline">` | `<v-btn variant="outlined">` | Borda cinza |
| `<Button variant="ghost">` | `<v-btn variant="text">` | Sem fundo |
| `<Badge variant="success">` | `<v-chip color="success" variant="tonal" size="small">` | Verde 10% |
| `<Card>` | `<v-card variant="outlined" rounded="md">` | Sem sombra |
| `<Input>` | `<v-text-field variant="outlined" density="compact">` | Borda sutil |
| `<Dialog>` | `<v-dialog>` + `<v-card>` interno | max-width adequado |
| `<Select>` | `<v-select :items variant="outlined">` | density compact |
| `<Tabs>` | `<v-tabs>` + `<v-tabs-window>` | v-model ativa |
| `<Table>` | `<v-data-table :headers :items>` | Inter para numeros |
| `<Switch>` | `<v-switch color="grey-darken-4">` | Preto quando ativo |
| `<Tooltip>` | `<v-tooltip>` | activator slot |
| `<Avatar>` | `<v-avatar>` | size numerico |
| `<Skeleton>` | `<v-skeleton-loader :type>` | type= text/card/avatar |
| `<Sheet>` | `<v-navigation-drawer temporary>` | location prop |
| `<Accordion>` | `<v-expansion-panels>` | multiple prop |
| `<Progress>` | `<v-progress-linear>` | model-value |
| `<Separator>` | `<v-divider>` | vertical prop |

### 5.2 Reactivity

| React | Vue 3 | Notas |
|-------|-------|-------|
| `useState(v)` | `ref(v)` | `.value` para acessar |
| `useState({})` | `reactive({})` | Proxy direto |
| `useMemo(() => x, [deps])` | `computed(() => x)` | Auto-track |
| `useCallback(fn, [deps])` | `fn` (funcao normal) | Vue nao precisa memoizar |
| `useEffect(() => {}, [dep])` | `watch(dep, () => {})` | Mais explicito |
| `useEffect(() => {}, [])` | `onMounted(() => {})` | Lifecycle |
| `useContext(Ctx)` | `useStore()` (Pinia) | Global |
| `useReducer` | `reactive() + methods` | Pinia para complexo |

### 5.3 Tailwind → Vuetify Layout

| Tailwind | Vuetify | Notas |
|----------|---------|-------|
| `flex items-center gap-2` | `d-flex align-center ga-2` | |
| `flex justify-between` | `d-flex justify-space-between` | |
| `flex flex-col` | `d-flex flex-column` | |
| `grid grid-cols-12 gap-6` | `<v-row><v-col>` | Sem gap manual |
| `p-4` | `pa-4` | padding all |
| `px-6 py-4` | `px-6 py-4` | Identico |
| `rounded-md` | `rounded="md"` | Prop do componente |
| `shadow-sm` | `elevation="1"` | Ou `elevation="0"` + border |
| `text-sm text-gray-600` | `text-body-2 text-grey-darken-1` | Typography class |
| `animate-spin` | `<v-progress-circular indeterminate>` | Componente |
| `animate-pulse` | `<v-skeleton-loader>` | Componente |

### 5.4 Template Vue Padrao

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Candidate } from '@/types/candidate'

interface Props {
  candidate: Candidate
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
})

const emit = defineEmits<{
  select: [id: string]
  move: [id: string, stage: string]
}>()

const displayName = computed(() =>
  `${props.candidate.firstName} ${props.candidate.lastName}`
)
</script>

<template>
  <v-card
    variant="outlined"
    rounded="md"
    :class="{ 'border-2 border-grey-darken-4': isSelected }"
    @click="emit('select', candidate.id)"
  >
    <v-card-title class="text-body-1 font-weight-bold"
      style="font-family: 'Open Sans', sans-serif">
      {{ displayName }}
    </v-card-title>
    <v-card-text>
      <v-chip
        size="small"
        :color="candidate.status === 'active' ? 'success' : 'grey'"
        variant="tonal"
      >
        {{ candidate.status }}
      </v-chip>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="grey-darken-4"
        variant="flat"
        size="small"
        @click.stop="emit('move', candidate.id, 'interview')"
      >
        Avancar
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.v-card {
  font-family: 'Open Sans', sans-serif;
}
</style>
```

### Checklist PASSO 5
- [ ] Componentes shadcn convertidos para Vuetify equivalentes
- [ ] React hooks convertidos para composables Vue
- [ ] Tailwind layout classes convertidas para Vuetify helpers
- [ ] Props tipadas com `defineProps<Props>()`
- [ ] Eventos com `defineEmits<{}>()`
- [ ] Sem anti-patterns React-only (cloneElement, forwardRef, useImperativeHandle)

---

## PASSO 6: Design Audit "Notion/ElevenLabs"

Auditoria visual pixel-level inspirada em interfaces de referencia.

### 6.1 Tipografia (3 Fontes — DS v4.2.1)

| Fonte | Proporcao | Uso | Vuetify Class |
|-------|-----------|-----|---------------|
| **Open Sans** | 85% | UI geral: titulos, labels, botoes, body, sidebar, chat | `style="font-family: 'Open Sans'"` |
| **Inter** | 10% | Dados numericos: metricas, KPIs, tabelas, dashboards | `style="font-family: 'Inter'"` |
| **JetBrains Mono** | 5% | Codigo, queries booleanas, IDs tecnicos | `style="font-family: 'JetBrains Mono'"` |

### Hierarquia Open Sans em Vuetify

| Elemento | Vuetify Class | Peso | Tamanho |
|----------|---------------|------|---------|
| H1 Page Title | `text-h5` | `font-weight-bold` | 24px |
| H2 Section Title | `text-h6` | `font-weight-bold` | 20px |
| H3 Card Title | `text-subtitle-1` | `font-weight-bold` | 16px |
| Body | `text-body-2` | `font-weight-regular` | 14px |
| Body SM | `text-caption` | `font-weight-regular` | 12px |
| Label | `text-caption` | `font-weight-medium` | 12px |
| Caption | `text-overline` | `font-weight-regular` | 10px |
| Button Text | `text-caption` | `font-weight-medium` | 12px |

> **font-weight v4.2.1:** `font-weight-medium` (500) e dominante para botoes, labels, sidebar.
> `font-weight-bold` (700) ou `font-weight-semi-bold` (600) apenas para titulos.

### 6.2 Componentes por Tipo

#### Botoes

| Variante | Vuetify Props | Dark Mode |
|----------|---------------|-----------|
| **Primary** | `color="grey-darken-4" variant="flat"` | Auto-inverte via theme |
| **Secondary** | `color="grey-lighten-4" variant="flat"` | Auto-inverte |
| **Outline** | `variant="outlined"` | Auto-inverte |
| **Ghost** | `variant="text"` | Auto-inverte |
| **Destructive** | `color="error" variant="flat"` | Mantém vermelho |
| **Disabled** | `:disabled="true"` | Vuetify handles |

Tamanhos: `size="small"` (32px) | `size="default"` (40px) | `size="large"` (48px)
Base: `rounded="md"` (via defaults)

#### Cards

```vue
<v-card variant="outlined" rounded="md" elevation="0">
  <v-card-title class="text-subtitle-1 font-weight-bold"
    style="font-family: 'Open Sans', sans-serif">
    Titulo
  </v-card-title>
  <v-card-text>Conteudo</v-card-text>
  <v-card-actions class="px-4 py-3">
    <v-spacer />
    <v-btn color="grey-darken-4" size="small">Acao</v-btn>
  </v-card-actions>
</v-card>
```

Regras: `elevation="0"` (sem sombra). Separacao visual via border (`variant="outlined"`).
Cards interativos: adicionar `hover` prop e `@click`.

#### Badges/Chips

| Tipo | Vuetify Props |
|------|---------------|
| Success | `color="success" variant="tonal" size="small"` |
| Error | `color="error" variant="tonal" size="small"` |
| Warning | `color="warning" variant="tonal" size="small"` |
| Info/LIA | `color="info" variant="tonal" size="small"` |
| Neutral | `color="grey-lighten-4" variant="tonal" size="small"` |
| Dark | `color="grey-darken-4" variant="flat" size="small"` |

#### Modais/Dialogs

```vue
<v-dialog v-model="dialogOpen" max-width="600">
  <v-card rounded="md">
    <v-card-title class="d-flex align-center justify-space-between pa-4">
      <span class="text-h6 font-weight-bold">Titulo</span>
      <v-btn icon variant="text" size="small" @click="dialogOpen = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>
    <v-divider />
    <v-card-text class="pa-4">
      Conteudo
    </v-card-text>
    <v-divider />
    <v-card-actions class="pa-4 d-flex justify-end ga-2">
      <v-btn variant="outlined" @click="dialogOpen = false">Cancelar</v-btn>
      <v-btn color="grey-darken-4" @click="onConfirm">Confirmar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

#### Sidebar + Navigation

```vue
<v-navigation-drawer
  permanent
  width="240"
  class="bg-grey-lighten-5"
>
  <v-list density="compact" nav>
    <v-list-item
      v-for="item in navItems"
      :key="item.route"
      :to="item.route"
      :prepend-icon="item.icon"
      :title="item.label"
      rounded="md"
      class="text-body-2 font-weight-medium"
      color="grey-darken-4"
    />
  </v-list>
</v-navigation-drawer>
```

#### Tabelas

```vue
<v-data-table
  :headers="headers"
  :items="items"
  :items-per-page="20"
  density="compact"
  hover
  class="font-inter"
>
  <template #item.name="{ item }">
    <span class="font-weight-medium font-open-sans">{{ item.name }}</span>
  </template>
  <template #item.score="{ item }">
    <span class="font-inter">{{ item.score }}%</span>
  </template>
</v-data-table>
```

> Numeros SEMPRE em Inter. Nomes e labels em Open Sans.

#### Tabs

```vue
<v-tabs v-model="activeTab" color="grey-darken-4" density="compact">
  <v-tab value="overview">Visao Geral</v-tab>
  <v-tab value="candidates">Candidatos</v-tab>
  <v-tab value="settings">Configuracoes</v-tab>
</v-tabs>

<v-tabs-window v-model="activeTab">
  <v-tabs-window-item value="overview">
    <OverviewTab />
  </v-tabs-window-item>
</v-tabs-window>
```

### Checklist PASSO 6
- [ ] 85% Open Sans verificado (UI geral)
- [ ] 10% Inter verificado (apenas dados numericos)
- [ ] 5% JetBrains Mono verificado (apenas codigo/queries)
- [ ] Zero fontes fora do DS (Roboto Vuetify default removido via SCSS override)
- [ ] Botoes primarios PRETOS (grey-darken-4), nunca azuis
- [ ] Cards com elevation="0" e variant="outlined"
- [ ] Modais com max-width adequado e header/divider/actions

---

## PASSO 7: Code Review Profundo

Auditoria de qualidade de codigo Vue.

### 7.1 Design Patterns para Vue 3

| Pattern | Implementacao Vue | Quando Usar |
|---------|-------------------|-------------|
| **Composable (Hook)** | `export function useXxx()` | Logica reutilizavel |
| **Provide/Inject** | `provide('key', value)` / `inject('key')` | Dependency injection |
| **Pinia Store** | `defineStore('id', () => {})` | State global |
| **Renderless Component** | Component sem template, emite via slot | Logica encapsulada |
| **Plugin** | `app.use(plugin)` | Funcionalidade global |

### 7.2 Anti-Patterns Vue a Verificar

| Anti-Pattern | Deteccao | Correcao |
|-------------|-----------|---------|
| Options API | `data()`, `methods:`, `computed:` | `<script setup lang="ts">` |
| Props `any` | `defineProps<{ x: any }>` | Tipagem estrita |
| v-html sem sanitizacao | `v-html="userInput"` | Sanitizar ou interpolacao |
| Mutacao de props | `props.x = y` | `emit('update:x', y)` |
| Fetch no template | chamada async no template | Composable com loading state |
| Watchers excessivos | 5+ `watch()` no componente | `computed()` ou composable |
| Componente 500+ linhas | `wc -l *.vue` | Split (PASSO 4) |

### 7.3 Regras TypeScript

```typescript
// BOM — tipagem estrita
interface Props {
  candidate: Candidate
  stage: RecruitmentStage
}

const props = defineProps<Props>()

// RUIM — sem tipagem
const props = defineProps(['candidate', 'stage'])
```

### Checklist PASSO 7
- [ ] Zero Options API (tudo `<script setup lang="ts">`)
- [ ] Zero `any` em props, emits e composables
- [ ] Zero `v-html` sem sanitizacao
- [ ] Zero mutacao direta de props
- [ ] Composables extraidos para logica complexa
- [ ] Pinia para state global (nunca reactive() global solto)

---

## PASSO 8: Auditoria 14 Dimensoes

Aplicar as 14 dimensoes de auditoria adaptadas para Vue/Vuetify.

### Dimensoes

| # | Dimensao | O que verificar no Vue/Vuetify |
|---|----------|-------------------------------|
| 1 | **Integracao** | Props e emits tipados. Pinia stores conectados. API calls em composables. |
| 2 | **Dados** | Reactive state consistente. Sem mutacao direta de props. |
| 3 | **UI/DS v4.2.1** | Tokens corretos. Regra 90/10. Fontes DS. Botoes pretos. |
| 4 | **Backend** | API endpoints corretos. Error handling em composables. |
| 5 | **Tipos** | Zero `any`. Interfaces para props, emits, stores. |
| 6 | **Fluxo Usuario** | Loading states. Error states. Empty states. |
| 7 | **Consistencia** | Componentes seguem mesmo padrao visual. Spacing uniforme. |
| 8 | **Documentacao** | JSDoc em composables publicos. README para componentes complexos. |
| 9 | **Arquitetura Agentes** | (Se LIA-related) Conexao correta com backend IA. |
| 10 | **Qualidade LLM** | (Se LIA-related) Prompts tipados. Responses parseadas. |
| 11 | **Servicos IA** | (Se LIA-related) Timeouts. Fallbacks. Rate limiting. |
| 12 | **Governanca IA** | (Se LIA-related) Audit trail. Transparencia de decisoes. |
| 13 | **Seguranca** | XSS (v-html). CSRF. Input sanitization. Auth guards. |
| 14 | **Performance** | Lazy loading. Virtual scroll para listas longas. Bundle size. |

### Checklist PASSO 8
- [ ] Todas as 14 dimensoes verificadas
- [ ] Issues documentados com severidade (critico/alto/medio/baixo)
- [ ] Dimensoes N/A justificadas
- [ ] Score parcial calculado

---

## PASSO 9: Multi-Agent Workflow

Para projetos com multiplos agentes trabalhando no v5.

### Coordenacao entre Agentes

| Agente | Responsabilidade | Output |
|--------|------------------|--------|
| Agente DS | Tokens, cores, tipografia (PASSOs 1-3) | `vuetify.config.ts`, `lia-bridge.css` |
| Agente Structure | Split, composables (PASSO 4) | Componentes refatorados |
| Agente Bridge | Conversao React→Vue (PASSO 5) | Componentes Vue |
| Agente QA | Audit visual + code review (PASSOs 6-8) | Report de conformidade |
| Agente Final | Validacao + score (PASSO 10) | Aprovacao/rejeicao |

### Regras de Merge

1. Agente DS vai primeiro — sem tokens corretos, nada funciona
2. Agente Structure depende de DS
3. Agente Bridge pode rodar paralelo ao Structure
4. Agente QA so roda depois de Structure + Bridge
5. Agente Final e sempre ultimo

### Checklist PASSO 9
- [ ] Ordem de execucao respeitada
- [ ] Conflitos de merge resolvidos
- [ ] Tokens base (PASSO 1) consistentes em todos os componentes

---

## PASSO 10: Validacao Final

### 10.1 Grep de Validacao

```bash
echo "=== Hex hardcoded ==="
grep -rn "#[0-9A-Fa-f]\{6\}" src/ --include="*.vue" --include="*.scss" | grep -v "node_modules\|dist\|.nuxt\|_lia-vuetify-settings"

echo "=== Tailwind gray (deve ser zero) ==="
grep -rn "gray-" src/ --include="*.vue" | grep -v "grey"

echo "=== Options API (deve ser zero) ==="
grep -rn "data()\|methods:\|computed:" src/ --include="*.vue"

echo "=== Props any (deve ser zero) ==="
grep -rn ": any" src/ --include="*.vue" --include="*.ts" | grep -v "node_modules"

echo "=== elevation alto (deve ser zero em cards) ==="
grep -rn "elevation=\"[2-9]\|elevation=\"1[0-9]" src/ --include="*.vue"

echo "=== v-html sem sanitizacao ==="
grep -rn "v-html" src/ --include="*.vue"

echo "=== Componentes grandes ==="
find src/ -name "*.vue" -exec wc -l {} + | sort -rn | head -10
```

### 10.2 Metricas de Qualidade

| Metrica | Target | Tolerancia |
|---------|--------|------------|
| Hex hardcoded | 0 | 0 |
| Classes Tailwind gray- | 0 | 0 |
| Elevation > 1 em cards | 0 | 0 |
| Options API | 0 | 0 |
| Props `any` | 0 | 2 (com justificativa) |
| Componentes > 300 linhas | 0 | 1 (com justificativa) |
| Fontes nao-DS | 0 | 0 |
| Composables desconectados | 0 | 0 |
| Coverage auditoria 14 dims | 100% | 85% (N/A justificado) |

### 10.3 Score de Conformidade

```
Score = (itens_ok / itens_total) * 100

90-100%: APROVADO — merge permitido
75-89%:  CONDICIONAL — merge com issues abertos
50-74%:  REPROVADO — refatorar antes de merge
<50%:    CRITICO — voltar ao PASSO 1
```

### Checklist PASSO 10
- [ ] Grep de validacao executado com zero violations
- [ ] Score de conformidade >= 90%
- [ ] Screenshot visual comparado com DS reference
- [ ] Dark mode testado
- [ ] Responsividade testada (mobile, tablet, desktop)

---

## Anti-Patterns a Evitar

| Anti-Pattern | Problema | Solucao |
|-------------|----------|---------|
| `v-btn color="primary"` sem definir tema | Pode ser azul (Vuetify default) | Usar `color="grey-darken-4"` ou configurar tema |
| `elevation="6"` em cards | Visual "inflado", fora do DS | `elevation="0"` + `variant="outlined"` |
| `rounded="xl"` em interface interna | Inconsistente com DS 8px | `rounded="md"` |
| Inline styles para cores | Nao responde a dark mode | Vuetify color system ou CSS vars |
| `<style>` sem scoped | CSS vaza entre componentes | Sempre `<style scoped>` |
| Options API (`data()`, `methods`) | Nao e Composition API | `<script setup lang="ts">` |
| `any` em props | Type safety perdida | `defineProps<Props>()` |
| v-html sem sanitizacao | XSS vulneravel | Sanitizar ou usar interpolacao |
| Fetch no template lifecycle | Race conditions | Composable com loading/error states |
| Import tudo de Vuetify | Bundle grande | Tree-shaking automatico com Vuetify plugin |

---

## Componentes Custom LIA (sem equivalente Vuetify)

13 componentes que precisam ser recriados como Vue components:

| Componente React | Estrategia Vue | Complexidade | Specs Essenciais |
|---|---|---|---|
| `LIAIcon` | `LiaIcon.vue` — SVG Brain + CSS | Baixa | Sizes: xs=12px, sm=16px, md=24px, lg=32px, xl=48px. Cor: `wedo-cyan`. Props: `size`, `animate` (pulse), `speaking` (sound wave overlay, brain opacity 30%). Rounded-full bg. |
| `EmptyState` | `LiaEmptyState.vue` | Baixa | Center-aligned, py-12 px-6. Props: `icon` (10x10), `title` (text-secondary), `description` (text-tertiary), `action` ({label, onClick} → outlined btn). |
| `ContextPill` | `<v-chip closable>` customizado | Baixa | Props: `icon` (default MapPin), `primaryText`, `secondaryText` (dot separator `•`), `onDismiss` → close btn. Rounded-full, border-default. |
| `QuickActionChips` | `<v-chip-group>` | Baixa | Props: `actions[]` (id, label, icon 14px, onClick, variant). Flex-wrap gap-2. Variants: default, primary (gray hover), success (green tint), warning (orange tint). |
| `AudioRecordButton` | Custom + composable `useAudioRecorder` | Alta | MediaRecorder API. States: idle, recording (red + pulse + timer), transcribing. Props: `onTranscription(text)`, `maxDuration` (60s), `transcriptionUrl`. Ghost icon btn. |
| `FileUploadButton` | `<v-file-input>` + custom drag&drop | Media | Hidden file input + btn trigger. Props: `onFilesSelected`, `onFileAnalyzed`, `autoAnalyze` (server-side PDF/DOC). File chips with status colors (green=success, red=error). |
| `Loading` | `<v-overlay>` + `<v-progress-circular>` | Baixa | Variants: spinner (border-t-gray-400), dots (keyframes dotsPulse), skeleton (loading-skeleton class), pulse. Props: `variant`, `size` (sm/md/lg), `text`. Helpers: `LoadingCard`, `LoadingList`. |
| `StatusBadge` | `StatusBadge.vue` + `statusMappings.ts` | Alta | **Detalhado abaixo** |
| `CommandPalette` | `<v-dialog>` + search + `<v-list>` | Alta | Props: `isOpen`, `commands[]` (label, category, shortcut, onSelect). Keyboard nav (ArrowUp/Down). Category grouping. Max-width 2xl, fixed height, scrollable. Search icon input top. |
| `PromptSuggestionsDock` | Custom — especifico LIA | Alta | Props: `onSelect(command)`, `isEmpty` (grid vs floating dock). Draggable (localStorage pos). Floating: brain icon. Expanded: w-80 card. Category colors: vagas=gray, candidatos=green. |
| `SearchLoadingAnimation` | CSS animation puro | Baixa | Props: `isActive`. Stages cycle: Interpretando → Buscando → Rankeando. Keyframes: ping, pulse, spin. Outer pulse wedo-cyan/40. |
| `DataRequestIndicator` | `<v-progress-linear>` + status text | Media | Props: `status` (pending/complete/partial/expired/cancelled), `fieldsRequested[]`. Circle indicator in tables. Tooltip on hover with field-by-field progress. Colors: cyan=pending, green=complete, orange=partial. |
| `SetupAlertBadge` | `<v-alert>` + `<v-badge>` | Media | Consumes `/api/backend-proxy/settings/progress`. Global floating, draggable, persists position. AlertCircle icon + percentage + mini progress bar. Color: warning(<50%) or cyan(>50%). Links to /configuracoes. |

### StatusBadge — Especificacao Completa (extraida do codigo)

O StatusBadge e o componente mais complexo. Requer recriacao cuidadosa.

#### Cores por Etapa do Funil (Escala Cinza Hierarquica)

Tom = progresso no funil (claro = inicio, escuro = final).

| Etapa | Light Mode | Dark Mode |
|-------|-----------|-----------|
| `sourcing` | `var(--gray-200)` | `var(--gray-600)` |
| `screening` | `var(--gray-200)` | `var(--gray-600)` |
| `long_list` | `var(--gray-300)` | `var(--gray-600)` |
| `short_list` | `var(--gray-300)` | `var(--gray-600)` |
| `interview_hr` | `var(--gray-400)` | `var(--gray-500)` |
| `technical_test` | `var(--gray-400)` | `var(--gray-500)` |
| `english_test` | `var(--gray-400)` | `var(--gray-500)` |
| `interview_technical` | `var(--gray-500)` | `var(--gray-400)` |
| `interview_manager` | `var(--gray-500)` | `var(--gray-400)` |
| `interview_manager2` | `var(--gray-500)` | `var(--gray-400)` |
| `interview_final` | `var(--gray-600)` | `var(--gray-300)` |
| `references` | `var(--gray-600)` | `var(--gray-300)` |
| `offer` | `var(--gray-800)` | `var(--gray-200)` |
| `hired` | `var(--status-success)` | `var(--status-success)` |
| `rejected` | `var(--gray-200)` | `var(--gray-600)` |
| `offer_declined` | `var(--gray-200)` | `var(--gray-600)` |
| `standby` | `var(--gray-300)` | `var(--gray-600)` |

#### Variantes de Badge

| Variante | Derivacao Automatica | Estilo Light | Estilo Dark |
|----------|---------------------|-------------|-------------|
| `standard` | Default | bg: gray-50, text: gray-600, icon: gray-400, weight: 500 | bg: gray-600, text: gray-200, icon: gray-400 |
| `dark` | `isApproval` | bg: gray-950, text: white, icon: white, weight: 700 | bg: gray-50, text: gray-950, icon: gray-950 |
| `accent` | `isWaiting` | bg: STAGE_COLOR, text: gray-950, icon: gray-800, weight: 600. Pulse animation. | bg: gray-600, text: gray-200, icon: gray-200 |
| `outlined` | in_progress/analyzing/evaluating/negotiating | bg: gray-50, text: gray-600, icon: gray-600, border: gray-200, weight: 400 | bg: gray-800, text: gray-200, border: gray-600 |
| `channel` | Canal de comunicacao | bg: gray-50, text: gray-800, border: gray-200, weight: 400 | bg: gray-600, text: gray-200, border: gray-400 |
| `scheduled` | scheduled/confirmed | bg: gray-800, text: white, icon: wedo-cyan, border: gray-600, weight: 600 | bg: gray-200, text: gray-950, icon: wedo-cyan-dark |
| `hired` | stageId='hired' + isApproval | bg: gray-950, text: white, icon: status-success (Trophy verde), weight: 700 | bg: gray-50, text: gray-950, icon: status-success |
| `rejected` | `isRejection` | bg: gray-50, text: gray-600, icon: gray-400, border: gray-200, weight: 500 | bg: gray-600, text: gray-200, icon: gray-400, border: gray-400 |

#### Logica de Derivacao de Variante

```
1. Se stageId='hired' E isApproval → 'hired'
2. Se isRejection → 'rejected'
3. Se isWaiting → 'accent' (com pulse)
4. Se isApproval → 'dark'
5. Se nome contem 'scheduled' ou 'confirmed' → 'scheduled'
6. Se nome contem 'in_progress', 'analyzing', 'evaluating', 'negotiating' → 'outlined'
7. Default → 'standard'
```

#### Icones por Contexto

| Contexto | Icone |
|----------|-------|
| Variante `accent` | Clock |
| Variante `hired` | Trophy |
| Variante `rejected` | XCircle |
| Variante `scheduled` | CalendarCheck |
| Nome contem `completed`/`approved` | CheckCircle |
| Nome contem `in_progress`/`andamento` | MessageCircle |
| Nome contem `interview`/`entrevista` | Users |
| Nome contem `screening`/`triagem` | BrainCircuit |
| Nome contem `test`/`teste` | FileText |
| Nome contem `offer`/`proposta` | Star |
| Nome contem `document`/`doc` | FileText |
| Default | FileText |

#### Badges Especializados

**ChannelBadge** — canal de comunicacao:

| Canal | Icone | Label |
|-------|-------|-------|
| `whatsapp` | MessageSquare | WhatsApp |
| `email` | Mail | Email |
| `phone` | Phone | Telefone |
| `linkedin` | Linkedin | LinkedIn |
| `teams` | Video | Teams |
| `presencial` | Building | Presencial |

**SourceBadge** — origem do candidato:

| Origem | Icone | Label |
|--------|-------|-------|
| `linkedin` | Linkedin | LinkedIn |
| `indeed` | Briefcase | Indeed |
| `google_jobs` | Search | Google Jobs |
| `website` | Globe | Site |
| `referral` | Users | Indicacao |
| `headhunting` | Target | Hunting |
| `internal` | Building | Interno |
| `lia_database` | BrainCircuit | Banco LIA |
| `recruiter` | User | Manual |

**OriginBadge** — origem da entrada (com cores de acento):

| Origem | Icone | Cor |
|--------|-------|-----|
| `web` | Globe | wedo-cyan/10 bg, wedo-cyan text |
| `whatsapp` | MessageCircle | wedo-green/15 bg, wedo-green text |
| `sourcing` | Search | gray-50 bg, text-secondary |
| `ats` | Briefcase | wedo-purple/15 bg, wedo-purple text |

**WarningBadge** — dias parado: AlertCircle icon, `X dias parado`, bg gray-100.

**AwaitingBadge** — fila saturacao: Clock icon, `Aguardando`, bg status-warning/10.

**DateTimeBadge** — data/hora: Calendar icon, formato `DD/MM as HH:MM`.

#### Visual do Badge

- Tamanho: font 9px, icon 8px (w-2 h-2), padding px-1.5 py-0.5, rounded-full
- Pulse animation em variant accent quando isWaiting
- CSS custom properties para dark mode (--badge-bg, --badge-text, --badge-icon, etc.)

### Etapas do Pipeline de Recrutamento (referencia)

17 etapas com transicoes permitidas, SLA default e assistencia LIA:

| Etapa | displayName | Ordem | Tipo | LIA-assisted | SLA (dias) |
|-------|------------|-------|------|-------------|------------|
| `sourcing` | Funil | 1 | active | Sim | 5 |
| `screening` | Triagem | 2 | active | Sim | 3 |
| `long_list` | Long List | 3 | active | Nao | 3 |
| `short_list` | Short List | 4 | active | Nao | 2 |
| `interview_hr` | Entrevista RH | 5 | active | Sim | 3 |
| `technical_test` | Teste Tecnico | 6 | active | Nao | 5 |
| `english_test` | Teste de Ingles | 7 | active | Nao | 3 |
| `interview_technical` | Entrevista Tecnica | 8 | active | Nao | 3 |
| `interview_manager` | Entrevista Gestor | 9 | active | Nao | 3 |
| `interview_manager2` | Entrevista Gestor 2 | 10 | active | Nao | 3 |
| `interview_final` | Entrevista Final | 11 | active | Nao | 3 |
| `references` | Referencias | 12 | active | Nao | 3 |
| `offer` | Proposta | 13 | active | Nao | 2 |
| `hired` | Contratado | 14 | final | Sim | 1 |
| `rejected` | Reprovado | 15 | final | Sim | 1 |
| `offer_declined` | Proposta Recusada | 16 | final | Nao | 1 |
| `standby` | Stand By | 17 | standby | Nao | — |

---

## Transicoes CSS → Vuetify

| CSS LIA | Vuetify | Uso |
|---------|---------|-----|
| `fadeIn 150ms` | `<v-fade-transition>` | Entrada/saida |
| `slideInFromBottom 200ms` | `<v-slide-y-transition>` | Modais, menus |
| `slideInFromRight 300ms` | `<v-slide-x-reverse-transition>` | Paineis laterais |
| `scale 150ms` | `<v-scale-transition>` | FABs, tooltips |
| `expandFromTop 200ms` | `<v-expand-transition>` | Acordeoes |

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Ativa ao trabalhar com arquivos `.vue` ou Vuetify |
| **Cursor IDE** | Mencione `@.agents/skills/vue-vuetify-standardize/SKILL.md` |
| **GitHub v5** | Referencie diretamente no PR template |

**Workflow recomendado:**
1. PASSO 0 (intencao) → PASSO 1-3 (tokens/cores) → PASSO 4 (split)
2. PASSO 5 (bridge) → PASSO 6 (design audit) → PASSO 7 (code review)
3. PASSO 8 (14 dimensoes) → PASSO 9 (multi-agent) → PASSO 10 (validacao)
4. Merge com score >= 90%
