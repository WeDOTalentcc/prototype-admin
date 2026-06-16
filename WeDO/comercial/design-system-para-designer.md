# WeDo Talent - Guia Completo para Designer

Este documento contém todas as informações necessárias para um designer trabalhar no projeto WeDo Talent, extraídas diretamente dos arquivos de código fonte.

## Acesso Rápido

### Storybook (Referência Visual)
- **URL Local**: http://localhost:6000
- **URL Pública**: https://7ce0a62c-6426-43d6-8c3c-f9e1dcef099b-00-1d771t3pez3we.picard.replit.dev:6000

### Arquivos de Referência (Código Fonte)

| Arquivo | Descrição |
|---------|-----------|
| `src/styles/design-tokens.css` | Variáveis CSS principais - FONTE PRIMÁRIA |
| `src/app/globals.css` | Estilos globais e utilitários |
| `tailwind.config.ts` | Configuração Tailwind |
| `src/components/ui/*.tsx` | Componentes base |

---

## Filosofia de Design

### Princípios (Inspirado em ElevenLabs, Linear, Vercel)

1. **90% Monocromático**: Interface predominantemente em escala de cinzas
2. **10% Acentos**: Cores estratégicas usadas com parcimônia
3. **Sem bordas**: Cards usam sombras sutis em vez de bordas
4. **Sem gradientes**: Cores sólidas e planas
5. **Texto escuro**: Hierarquia clara com tons de cinza escuro

---

## Paleta de Cores Principal

### Cores da Marca WeDo/LIA

| Nome | Hex | CSS Variable | Uso |
|------|-----|--------------|-----|
| **Brand Primary (Vermelho Coral)** | `#C74446` | `--lia-brand-primary` | Identidade LIA - USO MÍNIMO! |
| **Brand Hover** | `#B23B3D` | `--lia-brand-primary-hover` | Hover do brand |
| **Brand Light** | `#FEF2F2` | `--lia-brand-primary-light` | Background sutil |

### Paleta WeDo - 5 Cores Semânticas

| Cor | Hex | CSS Variable | Uso Semântico |
|-----|-----|--------------|---------------|
| **Cyan** | `#60BED1` | `--wedo-cyan` | Vagas, LIA, Automação, Tecnologia |
| **Green** | `#5DA47A` | `--wedo-green` | Candidatos, Sucesso, Aprovação |
| **Orange** | `#D19960` | `--wedo-orange` | Tempo, Custos, Economia, Alertas |
| **Purple** | `#9860D1` | `--wedo-purple` | Insights, Premium, Análises IA |
| **Magenta** | `#D160AB` | `--wedo-magenta` | Urgência crítica, Prioridade alta |

### Variantes das Cores Semânticas

| Cor | Light | Hover |
|-----|-------|-------|
| Cyan | `#A8CED5` | `#4DA8BB` |
| Green | `#A8D5B7` | `#4A8A68` |
| Orange | `#D5BFA8` | `#BF8554` |
| Purple | `#BFA8D5` | `#8652B8` |
| Magenta | `#D5A8C6` | `#B84D95` |

### Cores de Sucesso/Alerta

| Nome | Hex | CSS Variable |
|------|-----|--------------|
| Green Success | `#60D186` | `--wedo-green-success` |
| Orange Alert | `#E5A853` | `--wedo-orange-alert` |
| Info Color | `#60BED1` | `--lia-info-color` |

---

## Escala Monocromática (Base do Sistema)

### Backgrounds - Modo Claro

| Token | Hex | Uso |
|-------|-----|-----|
| `--lia-bg-primary` | `#FFFFFF` | Fundo principal |
| `--lia-bg-secondary` | `#F9FAFB` | Cards, painéis |
| `--lia-bg-tertiary` | `#F3F4F6` | Hover, disabled |
| `--lia-bg-elevated` | `#FFFFFF` | Cards com sombra |

### Backgrounds - Modo Escuro

| Token | Hex | Uso |
|-------|-----|-----|
| `--lia-bg-primary` | `#0F1113` | Fundo principal |
| `--lia-bg-secondary` | `#1A1D1F` | Cards, painéis |
| `--lia-bg-tertiary` | `#26292B` | Hover, disabled |
| `--lia-bg-elevated` | `#1A1D1F` | Cards com sombra |

### Bordas & Divisores - Modo Claro

| Token | Hex | Uso |
|-------|-----|-----|
| `--lia-border-subtle` | `#E5E7EB` | Bordas quase invisíveis |
| `--lia-border-default` | `#D1D5DB` | Bordas padrão |
| `--lia-border-medium` | `#9CA3AF` | Bordas com destaque |

### Bordas & Divisores - Modo Escuro

| Token | Hex |
|-------|-----|
| `--lia-border-subtle` | `#2D3748` |
| `--lia-border-default` | `#374151` |
| `--lia-border-medium` | `#4B5563` |

### Textos - Modo Claro

| Token | Hex | Uso |
|-------|-----|-----|
| `--lia-text-primary` | `#111827` | Títulos, texto principal |
| `--lia-text-secondary` | `#6B7280` | Texto corpo |
| `--lia-text-tertiary` | `#9CA3AF` | Labels, hints |
| `--lia-text-disabled` | `#D1D5DB` | Desabilitado |
| `--lia-text-inverse` | `#FFFFFF` | Texto em fundo escuro |

### Textos - Modo Escuro

| Token | Hex |
|-------|-----|
| `--lia-text-primary` | `#F9FAFB` |
| `--lia-text-secondary` | `#D1D5DB` |
| `--lia-text-tertiary` | `#9CA3AF` |
| `--lia-text-disabled` | `#6B7280` |
| `--lia-text-inverse` | `#111827` |

### Textos - Hierarquia LIA Design System v2

| Token | Hex | Uso |
|-------|-----|-----|
| `--lia-text-black` | `#1F2937` | Títulos principais |
| `--lia-text-dark` | `#374151` | Subtítulos |
| `--lia-text-body` | `#4B5563` | Texto corpo |
| `--lia-text-muted` | `#6B7280` | Helpers, captions |

---

## Sistema de Status

### Alto Desempenho / Ativo

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-status-high-bg` | `#111827` (preto suave) |
| Light | `--lia-status-high-text` | `#FFFFFF` (branco) |
| Dark | `--lia-status-high-bg` | `#F9FAFB` |
| Dark | `--lia-status-high-text` | `#111827` |

### Médio Desempenho / Em Progresso

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-status-medium-bg` | transparent |
| Light | `--lia-status-medium-text` | `#6B7280` |
| Light | `--lia-status-medium-border` | `#D1D5DB` |
| Dark | `--lia-status-medium-text` | `#D1D5DB` |
| Dark | `--lia-status-medium-border` | `#4B5563` |

### Baixo Desempenho / Inativo

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-status-low-bg` | transparent |
| Light | `--lia-status-low-text` | `#9CA3AF` |
| Light | `--lia-status-low-border` | `#E5E7EB` |
| Dark | `--lia-status-low-text` | `#6B7280` |
| Dark | `--lia-status-low-border` | `#374151` |

### Destrutivo (Vermelho da Marca)

| Token | Valor |
|-------|-------|
| `--lia-destructive-bg` | `var(--lia-brand-primary)` |
| `--lia-destructive-text` | `#FFFFFF` |
| `--lia-destructive-border` | `var(--lia-brand-primary)` |

---

## Cores de Categoria (Badges e Ícones)

| Categoria | Hex | CSS Variable |
|-----------|-----|--------------|
| Vagas (Jobs) | `#60BED1` | `--lia-cat-jobs` |
| Candidatos | `#5DA47A` | `--lia-cat-candidates` |
| Entrevistas/LIA | `#E5A853` | `--lia-cat-interviews` |
| Relatórios/Localização | `#8B5CF6` | `--lia-cat-reports` |
| Indústria/Setor | `#3B82F6` | `--lia-cat-industry` |

---

## Paleta ElevenLabs (Monocromático/Sépia)

### Cards Coloridos - Tons Monocromáticos/Sépia

| Nome | Hex | CSS Variable |
|------|-----|--------------|
| Sepia Dark | `#3D3330` | `--eleven-card-sepia-dark` |
| Forest | `#2C4A3A` | `--eleven-card-forest` |
| Navy | `#2A3744` | `--eleven-card-navy` |
| Brown | `#443C35` | `--eleven-card-brown` |
| Slate | `#3A3F47` | `--eleven-card-slate` |

### Cores Pastéis Suaves

| Nome | Hex | CSS Variable |
|------|-----|--------------|
| Blue | `#B8D4E8` | `--eleven-pastel-blue` |
| Green | `#C1E1C1` | `--eleven-pastel-green` |
| Peach | `#F0DDD3` | `--eleven-pastel-peach` |
| Lavender | `#D4CEE3` | `--eleven-pastel-lavender` |
| Rose | `#E9D5D5` | `--eleven-pastel-rose` |
| Mint | `#D4E8E1` | `--eleven-pastel-mint` |
| Sand | `#E8DDD4` | `--eleven-pastel-sand` |

### Paleta Sépia ElevenLabs (Screenshot Reference)

| Nome | Hex | CSS Variable |
|------|-----|--------------|
| Light | `#F3EBE1` | `--eleven-sepia-light` |
| Mint | `#DCE4DB` | `--eleven-sepia-mint` |
| Rose | `#E3DADC` | `--eleven-sepia-rose` |
| Blue | `#DDE1E9` | `--eleven-sepia-blue` |
| Lilac | `#E5E0E2` | `--eleven-sepia-lilac` |
| Ice | `#EAEAEA` | `--eleven-sepia-ice` |
| Coral | `#E17B75` | `--eleven-sepia-coral` |

---

## Paleta Tech Startups 2024-2025

| Nome | Hex | CSS Variable | Uso |
|------|-----|--------------|-----|
| AI Aqua | `#0094c6` | `--ai-aqua` | Azul-verde futurístico |
| Electric Red | `#de1c31` | `--electric-red` | Vermelho vibrante |
| Ethereal Green | `#8bb923` | `--ethereal-green` | Verde futurístico |
| Warm Energy | `#f0b323` | `--warm-energy` | Amarelo energético |
| Peach Fuzz | `#f6A68c` | `--peach-fuzz` | Pantone 2024 |
| Deep Tech | `#1d1d1f` | `--deep-tech` | Quase preto |

### Variantes Light (20% mais claras)

| Nome | CSS Variable |
|------|--------------|
| AI Aqua Light | `--ai-aqua-light` |
| Electric Red Light | `--electric-red-light` |
| Ethereal Green Light | `--ethereal-green-light` |
| Warm Energy Light | `--warm-energy-light` |
| Peach Fuzz Light | `--peach-fuzz-light` |

### Tons Neutros

| Nome | Hex | CSS Variable |
|------|-----|--------------|
| Neutral Warm | `#edeecb` | `--neutral-warm` |
| Neutral Cool | `#bebebf` | `--neutral-cool` |
| Neutral Dark | `#7e7e81` | `--neutral-dark` |

---

## Tipografia

### Fontes do Sistema

| Fonte | CSS Variable | Uso |
|-------|--------------|-----|
| Inter | `--font-inter` | UI moderna, alternativa |
| Open Sans | `--font-open-sans` | Corpo, navegação, buttons |
| Source Serif 4 | `--font-source-serif` | Títulos, elegância |
| Crimson Text | `--font-crimson` | Serifada alternativa |

### Hierarquia Tipográfica (Classes LIA)

| Classe | Fonte | Tamanho | Peso | Cor |
|--------|-------|---------|------|-----|
| `.lia-h1` | Source Serif 4 | 2rem (32px) | 600 | `#1F2937` |
| `.lia-h2` | Source Serif 4 | 1.5rem (24px) | 600 | `#1F2937` |
| `.lia-h3` | Source Serif 4 | 1.25rem (20px) | 600 | `#1F2937` |
| `.lia-h4` | Source Serif 4 | 1rem (16px) | 600 | `#1F2937` |
| `.lia-subtitle` | Open Sans | 1rem (16px) | 400 | `#374151` |
| `.lia-subtitle-sm` | Open Sans | 0.875rem (14px) | 400 | `#374151` |
| `.lia-body` | Open Sans | 0.875rem (14px) | 400 | `#4B5563` |
| `.lia-body-sm` | Open Sans | 0.8125rem (13px) | 400 | `#4B5563` |
| `.lia-helper` | Open Sans | 0.75rem (12px) | 400 | `#6B7280` |
| `.lia-caption` | Open Sans | 0.6875rem (11px) | 500 | `#6B7280` |
| `.lia-label` | Open Sans | 0.875rem (14px) | 500 | `#1F2937` |
| `.lia-label-sm` | Open Sans | 0.75rem (12px) | 500 | `#1F2937` |

### Navegação (Regra Especial)

**Todos os itens de navegação usam:**
- Fonte: Open Sans
- Tamanho: **11px (0.6875rem)**
- Peso: 500
- Line-height: 1.125rem

Aplica-se a: `nav`, sidebar, menu-item, tabs, tab-button, settings-menu-item

---

## Componentes

### Botões - Tokens Oficiais

#### Primário (Ação Principal) - PRETO

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-btn-primary-bg` | `#111827` (preto) |
| Light | `--lia-btn-primary-hover` | `#000000` |
| Light | `--lia-btn-primary-text` | `#FFFFFF` |
| Dark | `--lia-btn-primary-bg` | `#F9FAFB` |
| Dark | `--lia-btn-primary-hover` | `#FFFFFF` |
| Dark | `--lia-btn-primary-text` | `#111827` |

#### Secundário

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-btn-secondary-bg` | transparent |
| Light | `--lia-btn-secondary-hover` | `#F3F4F6` |
| Light | `--lia-btn-secondary-text` | `#6B7280` |
| Light | `--lia-btn-secondary-border` | `#E5E7EB` |
| Dark | `--lia-btn-secondary-hover` | `#26292B` |
| Dark | `--lia-btn-secondary-text` | `#D1D5DB` |
| Dark | `--lia-btn-secondary-border` | `#374151` |

#### Ghost

| Modo | Token | Valor |
|------|-------|-------|
| Light | `--lia-btn-ghost-bg` | transparent |
| Light | `--lia-btn-ghost-hover` | `#F3F4F6` |
| Light | `--lia-btn-ghost-text` | `#6B7280` |
| Dark | `--lia-btn-ghost-hover` | `#26292B` |
| Dark | `--lia-btn-ghost-text` | `#D1D5DB` |

#### Botão LIA (Cyan) - Classe Customizada

Para ações relacionadas à LIA/Vagas/Automação:
```css
background: #60BED1;
hover: #4FA8BA;
color: #FFFFFF;
```

### Especificações de Botões

```css
font-family: "Open Sans", sans-serif;
font-size: 0.875rem (14px);
font-weight: 600;
padding: 0.625rem 1.25rem (10px 20px);
border-radius: 8px;
border: none;
```

### Cards

#### Card Padrão (`.lia-card`)
```css
background: #FFFFFF;
border-radius: 12px;
box-shadow: 0 1px 3px rgba(0,0,0,0.04);
border: none;
```

#### Card Elevado (`.lia-card-elevated`)
```css
background: #FFFFFF;
border-radius: 12px;
box-shadow: 0 4px 12px rgba(0,0,0,0.06);
border: none;
```

#### Card com Hover (`.lia-card-hover`)
```css
/* Normal */
background: #FFFFFF;
border-radius: 12px;
box-shadow: 0 1px 3px rgba(0,0,0,0.04);
border: none;

/* Hover */
box-shadow: 0 4px 16px rgba(0,0,0,0.08);
```

### Badges

#### Tokens de Badge

| Token | Light | Dark |
|-------|-------|------|
| `--lia-badge-neutral-bg` | `#F3F4F6` | `#26292B` |
| `--lia-badge-neutral-text` | `#6B7280` | `#D1D5DB` |
| `--lia-badge-neutral-border` | `#E5E7EB` | `#374151` |

#### Badges por Categoria

| Categoria | Background | Texto |
|-----------|------------|-------|
| Jobs | `rgba(96, 190, 209, 0.12)` | `#0E7490` |
| Candidates | `rgba(93, 164, 122, 0.12)` | `#166534` |
| Interviews | `rgba(229, 168, 83, 0.12)` | `#92400E` |
| Reports | `rgba(139, 92, 246, 0.12)` | `#6D28D9` |
| Industry | `rgba(59, 130, 246, 0.12)` | `#1D4ED8` |
| Neutral | `#F3F4F6` | `#4B5563` |

#### Especificações de Badge

```css
font-family: "Open Sans", sans-serif;
font-size: 0.75rem (12px);
font-weight: 500;
padding: 0.25rem 0.625rem (4px 10px);
border-radius: 6px;
border: none;
```

### Inputs

#### Tokens de Input

| Token | Light | Dark |
|-------|-------|------|
| `--lia-input-bg` | `#FFFFFF` | `#1A1D1F` |
| `--lia-input-border` | `#E5E7EB` | `#374151` |
| `--lia-input-border-focus` | `#111827` | `#F9FAFB` |
| `--lia-input-text` | `#111827` | `#F9FAFB` |
| `--lia-input-placeholder` | `#9CA3AF` | `#6B7280` |

#### Especificações de Input

```css
font-family: "Open Sans", sans-serif;
font-size: 0.875rem (14px);
padding: 0.625rem 0.875rem (10px 14px);
border-radius: 8px;
background: #F9FAFB;
border: 1px solid #E5E7EB;
color: #1F2937;
```

**Focus State:**
```css
border-color: #60BED1;
box-shadow: 0 0 0 3px rgba(96, 190, 209, 0.1);
outline: none;
```

---

## Sombras

| Nome | Valor | CSS Variable |
|------|-------|--------------|
| Small | `0 1px 2px rgba(0,0,0,0.02)` | `--lia-shadow-sm` |
| Default | `0 1px 3px rgba(0,0,0,0.05)` | `--lia-shadow-default` |
| Medium | `0 4px 6px rgba(0,0,0,0.05)` | `--lia-shadow-md` |
| Large | `0 10px 15px rgba(0,0,0,0.05)` | `--lia-shadow-lg` |

### Sombras - Modo Escuro (mais pronunciadas)

| Nome | Valor |
|------|-------|
| Small | `0 1px 2px rgba(0,0,0,0.3)` |
| Default | `0 1px 3px rgba(0,0,0,0.4)` |
| Medium | `0 4px 6px rgba(0,0,0,0.5)` |
| Large | `0 10px 15px rgba(0,0,0,0.6)` |

---

## Espaçamentos

### Border Radius

| Token | Valor |
|-------|-------|
| `--radius` (lg) | 0.75rem (12px) |
| Radius MD | calc(0.75rem - 2px) = 10px |
| Radius SM | calc(0.75rem - 4px) = 8px |

### Container Padding

| Breakpoint | Padding |
|------------|---------|
| Default | 1rem (16px) |
| SM (640px+) | 2rem (32px) |
| LG (1024px+) | 4rem (64px) |
| XL (1280px+) | 5rem (80px) |
| 2XL (1536px+) | 6rem (96px) |

---

## Animações

### Keyframes Disponíveis

| Nome | Descrição |
|------|-----------|
| `fadeIn` | Fade + translate Y 10px |
| `slideIn` | Translate Y 10px |
| `scaleIn` | Scale 0.95 → 1 |
| `slideInRight` | Translate X 30px |
| `slideInUp` | Translate Y 20px + scale |
| `dotsPulse` | Pulse para loading dots |
| `shimmer` | Efeito shimmer loading |

### Classes Utilitárias

| Classe | Duração |
|--------|---------|
| `.animate-fade-in` | 0.5s ease-out |
| `.animate-slide-in` | 0.4s ease-out |
| `.animate-scale-in` | 0.3s ease-out |
| `.animate-loading` | 1s linear infinite |

### Micro Interações

| Classe | Efeito |
|--------|--------|
| `.micro-bounce` | Scale 0.95 no active |
| `.micro-scale` | Scale 1.02 no hover |
| `.hover-lift` | TranslateY -2px + shadow |
| `.hover-glow` | Box-shadow cyan glow |
| `.hover-border` | Border color change |

### Easing

- **Padrão**: `cubic-bezier(0.4, 0, 0.2, 1)`
- **Duração rápida**: 150ms
- **Duração normal**: 200ms
- **Duração lenta**: 300ms

---

## Interactive States

### Light Mode

| Token | Valor |
|-------|-------|
| `--lia-interactive-hover` | `#F3F4F6` |
| `--lia-interactive-active` | `#E5E7EB` |
| `--lia-interactive-focus` | `#111827` |

### Dark Mode

| Token | Valor |
|-------|-------|
| `--lia-interactive-hover` | `#26292B` |
| `--lia-interactive-active` | `#2D3748` |
| `--lia-interactive-focus` | `#F9FAFB` |

---

## Page Header (Estrutura Padronizada)

### Classes

| Classe | Uso |
|--------|-----|
| `.lia-page-header` | Container do header |
| `.lia-page-header-row` | Row com justify-between |
| `.lia-page-eyebrow` | Label pequeno acima do título |
| `.lia-page-title` | Título principal |
| `.lia-page-description` | Descrição abaixo |

### Especificações

```css
.lia-page-eyebrow {
  font: 500 11px "Open Sans";
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.lia-page-title {
  font: 600 1.75rem "Source Serif 4";
  color: #1F2937;
  line-height: 1.2;
}

.lia-page-description {
  font: 400 15px "Open Sans";
  color: #4B5563;
  line-height: 1.5;
}
```

---

## Componentes no Storybook

### Com Stories

1. **Button** - `UI/Button` - Todas as variantes e tamanhos
2. **Card** - `UI/Card` - Cards com header, footer, content
3. **Input** - `UI/Input` - Inputs com variantes
4. **Badge** - `UI/Badge` - Badges por categoria
5. **Select** - `UI/Select` - Selects com opções
6. **Dialog** - `UI/Dialog` - Modais e diálogos
7. **CandidatePreview** - Preview de candidato

---

## Páginas Principais do App

### Gestão de Vagas
- `/jobs` - Lista de vagas
- `/jobs/[id]` - Detalhe da vaga

### Funil de Talentos
- `/funil` - Pipeline de candidatos
- `/funil-de-talentos/candidato/[id]` - Perfil do candidato

### Comunicações
- `/chat` - Chat com LIA
- `/tasks` - Tarefas

### Admin
- `/admin` - Dashboard admin
- `/admin/clientes` - Gestão de clientes
- `/admin/clientes/[clientId]/*` - Subpáginas de cliente
- `/admin/compliance/*` - Compliance e LGPD
- `/admin/configuracoes/*` - Configurações

### Autenticação
- `/login` - Login
- `/register` - Registro
- `/forgot-password` - Recuperação de senha
- `/reset-password` - Reset de senha
- `/accept-invitation` - Aceitar convite

---

## Plugins Figma Recomendados

1. **HTML to Figma** - Para importar páginas existentes
2. **Storybook Connect** - Sincronizar com Storybook
3. **Tokens Studio** - Gerenciar design tokens
4. **Tailwind CSS** - Visualizar classes Tailwind

---

## Notas Importantes

### Regra 90/10
A interface deve ser 90% monocromática (escalas de cinza) e apenas 10% de cores de destaque. Use as cores semânticas com parcimônia.

### Sem Bordas em Cards
Cards usam **sombras sutis** em vez de bordas para definição visual.

### Botão Primário
O botão primário padrão é **PRETO** (`#111827`), não cyan. Use cyan apenas para ações específicas relacionadas à LIA/Vagas.

### Navegação 11px
Todos os itens de navegação, tabs e menus usam fonte de **11px**.
