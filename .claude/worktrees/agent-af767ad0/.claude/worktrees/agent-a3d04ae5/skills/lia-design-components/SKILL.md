---
name: lia-design-components
description: Design System LIA v4.1 components - buttons, inputs, cards, modals, tables, badges, tooltips, toasts, navigation, loading states, dropdowns, accordions, progress, avatars, pagination, switches, tabs, dividers, file upload, sliders, date pickers, skeletons. Use when building any UI component for the LIA/WeDo Talent platform.
---

# LIA Design System v4.1 - Components

> **Source:** Design System LIA v4.1 (Fev 2026) - PARTE 2
> For full code examples (Tailwind + Vuetify), read files in `~/.agents/skills/lia-design-components/reference/`

## Quick Rules

1. **Botão Primary = bg-gray-900** (NUNCA cyan)
2. **Labels = 11px semibold Inter** | Body = 14px Inter | Headers = Open Sans
3. **Focus ring = ring-2 ring-gray-900/20** (SEMPRE gray-900)
4. **Border radius:** Buttons/Inputs = `rounded` (6px) | Cards/Modals = `rounded-md` (8px)
5. **Sombras:** Cards = `shadow-sm` | Hover = `shadow-md` | Modais = `shadow-lg`
6. **Switches/Toggles:** `bg-gray-900` padrão. Cyan APENAS em componentes LIA

## Component Summary

### Buttons (2.1)
| Variant | BG | Text | Border | Uso |
|---------|----|----|--------|-----|
| Primary | `bg-gray-900` | `text-white` | none | Ação principal |
| Secondary | transparent | `text-gray-900` | `border-gray-300` | Ação secundária |
| Ghost | transparent | `text-gray-700` | none | Ação terciária |
| Destructive | `bg-red-600` | `text-white` | none | Deletar apenas |

Sizes: Small (32px/12px), Medium (36px/14px), Large (44px/14px)

### Inputs & Forms (2.2)
- **Text Input:** `border-gray-200 rounded` | Focus: `ring-2 ring-gray-900/20 border-gray-900`
- **Error state:** `border-red-300 bg-red-50` + error message `text-red-600`
- **Disabled:** `bg-gray-100 text-gray-500 cursor-not-allowed`
- **Label:** `text-[11px] font-semibold text-gray-800 font-['Inter']`
- **Helper text:** `text-xs text-gray-600`
- Includes: TextInput, Textarea, Select, Checkbox, Radio

### Cards (2.3)
- **Standard:** `bg-white rounded-md shadow-sm border border-gray-200 p-6`
- **Interactive:** add `hover:shadow-md hover:-translate-y-0.5 cursor-pointer`
- **Glass:** `bg-white/70 backdrop-blur-lg border border-gray-200/50`
- **With Header/Footer:** header/footer with `border-b/t border-gray-200`

### Modals (2.4)
5 sizes ONLY: XS(384px), S(448px), M(512px), L(672px), XL(896px)
**PROIBIDO:** max-w-xl, max-w-3xl, max-w-5xl
- Overlay: `bg-black/50 backdrop-blur-sm`
- Header: icon(w-5) + title(14px semibold) + close button
- Footer: `bg-gray-50 border-t` with buttons right-aligned

### Tables (2.5)
- Header: `bg-gray-50` + `text-[11px] font-semibold text-gray-800`
- Rows: `hover:bg-gray-50` + `divide-y divide-gray-200`
- Numbers: `font-feature-settings: 'tnum' 1`
- Empty state: centered icon + title + description

### Badges & Tags (2.6)
- Base: `inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium`
- Semantic: green-50/700, amber-50/700, red-50/700 (with border)
- WeDo accent: 10% opacity bg + matching text/border

### Navigation (2.9)
- Sidebar: `w-64 bg-white border-r` | Active: `bg-gray-100 text-gray-900 font-semibold`
- Top Nav: `h-16 border-b` | Active tab: `border-b-2 border-gray-900`
- Breadcrumbs: gray-600 links + gray-400 separators + gray-900 current

### Loading (2.10)
- Spinner: `animate-spin text-gray-900`
- Progress bar: `bg-gray-200` track + `bg-gray-900` fill
- Skeleton: `animate-pulse` + `bg-gray-200 rounded`

### Other Components
- **Tooltips (2.7):** `bg-gray-900 text-white text-xs rounded`
- **Toasts (2.8):** white bg + semantic border + icon circle
- **Dropdowns (2.11):** `bg-white border-gray-200 rounded-md shadow-lg`
- **Accordions (2.12):** `border border-gray-200 rounded-md` + rotate chevron
- **Progress (2.13):** Linear + Circular variants
- **Avatars (2.14):** 24px/32px/40px sizes + initials fallback
- **Pagination (2.16):** Active `bg-gray-900 text-white`
- **Switches (2.17):** `bg-gray-900` when ON (never cyan unless LIA component)
- **Tabs (2.23):** Underline `border-b-2 border-gray-900`
- **Dividers (2.24):** `border-t border-gray-200`
- **Date Pickers (2.20):** Standard input styling
- **File Upload (2.21):** Dashed border `border-2 border-dashed border-gray-300`
- **Sliders (2.22):** `accent-gray-900`

## Reference Files
- `reference/buttons-inputs.md` - Buttons (all variants/sizes/states) + Form inputs (text, textarea, select, checkbox, radio)
- `reference/cards-modals.md` - Cards (4 variants) + Modals (sizes, structure, animation)
- `reference/tables-badges.md` - Tables (structure, actions, empty) + Badges (semantic, WeDo, with icon)
- `reference/navigation-loading.md` - Sidebar, top nav, breadcrumbs + Spinner, progress, skeleton
- `reference/forms-misc.md` - Tooltips, toasts, dropdowns, accordions, progress indicators, avatars, pagination, switches, tabs, dividers, file upload, sliders, date pickers
