---
name: lia-design-foundations
description: Design System LIA v4.1 foundations - colors, typography, spacing, grid, shadows, borders, motion, glassmorphism. Use when creating any UI component, layout, or page for the LIA/WeDo Talent platform. Ensures correct colors, fonts, spacing and visual hierarchy.
---

# LIA Design System v4.1 - Foundations

> **Source:** Design System LIA v4.1 (Fev 2026) | **Inspiration:** ElevenLabs UI
> For full details, read files in `~/.agents/skills/lia-design-foundations/reference/`

## Critical Rules (MUST follow)

### Regra 90/10
- **90% Monocromático**: backgrounds, textos, bordas, botões principais = escala de cinzas
- **10% Cor Accent**: APENAS para Brain icon LIA (#60BED1), badges contextuais, status indicators
- **NUNCA** usar cores accent em botões primários ou ações principais

### Botão Primário = PRETO
- Default: `bg-gray-900 text-white` | Hover: `bg-gray-800` | Disabled: `bg-gray-300 text-gray-500`
- Dark mode: `bg-gray-50 text-gray-900`
- **NUNCA** usar cyan (#60BED1) como botão primário

### Tipografia Dual (2 fontes apenas)
- **Open Sans** (~60%): Headers, nav, buttons, labels, CTAs → `font-['Open_Sans']`
- **Inter** (~40%): Body text, forms, tables, badges, KPIs → `font-['Inter']`
- **Source Serif 4 foi REMOVIDO** na v4.1
- Mínimo: 10px (WCAG AA) | Tabelas: `font-feature-settings: 'tnum' 1`

### Type Scale Essencial
| Nome | Size | Weight | Fonte | Uso |
|------|------|--------|-------|-----|
| H1 | 32px/2rem | 700 | Open Sans | Page titles |
| H2 | 24px/1.5rem | 700 | Open Sans | Section titles |
| H3 | 20px/1.25rem | 600 | Open Sans | Card titles |
| H4 | 16px/1rem | 600 | Open Sans | Sub-headers |
| Body | 14px/0.875rem | 400 | Inter | Default text |
| Body Small | 12px/0.75rem | 400 | Inter | Secondary text |
| Label | 11px/0.6875rem | 600 | Inter | Form labels |
| Micro | 10px/0.625rem | 500 | Inter | Badges, tiny |

### Cores - Quick Reference
**Backgrounds:** white, gray-50 (cards/panels), gray-100 (hover/disabled)
**Textos:** gray-900 (títulos), gray-800 (body), gray-600 (secondary), gray-500 (muted)
**Bordas:** gray-200 (padrão sutil), gray-300 (destaque)
**WeDo Accent:** Cyan #60BED1, Green #5DA47A, Orange #D19960, Purple #9860D1, Magenta #D160AB

### Espaçamento (8px system)
4px, 8px, 12px, 16px (padrão), 24px, 32px, 40px, 48px, 64px

### Sombras (extremamente sutis)
- Cards: `shadow-sm` | Hover: `shadow-md` | Modais: `shadow-lg`
- Focus ring: `ring-2 ring-gray-900/20` (SEMPRE gray-900, nunca colorido)

### Bordas
- Padrão: `border border-gray-200` (quase invisível) | Destaque: `border-gray-300`
- Border radius: Buttons/Inputs=6px(`rounded`), Cards/Modals=8px(`rounded-md`)

### Glassmorphism (usar com parcimônia)
```css
background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.05);
```
Tailwind: `bg-white/70 backdrop-blur-lg border border-gray-200/50`

### Dark Mode Tokens (light-first)
| Token | Light | Dark |
|-------|-------|------|
| bg-primary | #FFFFFF | #0F1113 |
| bg-secondary | #F9FAFB | #1A1D1F |
| text-primary | #111827 | #F9FAFB |
| text-body | #1F2937 | #E5E7EB |
| border-subtle | #E5E7EB | #374151 |

### DO / DON'T
```
✅ DO: Texto escuro (nunca #000), bg claros, bordas sutis, sombras leves, contraste WCAG AA
❌ DON'T: Gradientes, bordas grossas, cores saturadas, animações excessivas, botões coloridos como primário
```

## Reference Files
- `reference/colors.md` - Paleta completa, tokens, dark mode, status colors
- `reference/typography.md` - Fontes, type scale, classes Tailwind/Vuetify
- `reference/spacing-grid.md` - Espaçamento 8px, grid 12 colunas, breakpoints
- `reference/effects.md` - Sombras, bordas, motion, glassmorphism, Brain icon LIA
