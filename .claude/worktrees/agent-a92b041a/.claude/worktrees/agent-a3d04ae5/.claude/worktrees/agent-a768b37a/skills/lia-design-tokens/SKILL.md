---
name: lia-design-tokens
description: Design System LIA v4.1 implementation tokens - CSS custom properties, TypeScript type-safe tokens, utility classes, Vuetify integration & configuration, migration guide v4.0→v4.1. Use when setting up the design system in code, configuring Vuetify theme, creating utility classes, or migrating from v4.0.
---

# LIA Design System v4.1 - Tokens & Implementation

> **Source:** Design System LIA v4.1 (Fev 2026) - PARTE 4
> For complete token files, read `~/.agents/skills/lia-design-tokens/reference/`

## 4.1 CSS Design Tokens (`:root`)

Key tokens (full file in `reference/css-tokens.md`):
```css
:root {
  /* Backgrounds */
  --lia-bg-primary: #FFFFFF;
  --lia-bg-secondary: #F9FAFB;
  
  /* Text */
  --lia-text-primary: #111827;
  --lia-text-body: #1F2937;
  --lia-text-secondary: #4B5563;
  
  /* Borders */
  --lia-border-subtle: #E5E7EB;
  --lia-border-default: #D1D5DB;
  
  /* WeDo Accent */
  --wedo-cyan: #60BED1;
  --wedo-green: #5DA47A;
  --wedo-purple: #9860D1;
  
  /* Typography */
  --font-brand: 'Open Sans', system-ui, sans-serif;
  --font-data: 'Inter', system-ui, sans-serif;
  
  /* Focus */
  --focus-ring: 0 0 0 3px rgba(17, 24, 39, 0.2);
}
```

## 4.2 TypeScript Tokens

Key exports (full file in `reference/ts-tokens.md`):
- `colors` - bg, text, border, wedo, semantic
- `typography` - fonts, sizes
- `spacing` - 8px system
- `borderRadius`, `shadows`, `transitions`, `breakpoints`
- `buttonStyles`, `getButtonClasses()`, `getBadgeClasses()`

## 4.3 Utility Classes (Tailwind `@apply`)

```css
.btn-primary { @apply px-4 py-2 rounded text-sm font-semibold bg-gray-900 text-white hover:bg-gray-800; }
.btn-secondary { @apply px-4 py-2 rounded text-sm font-semibold border border-gray-300 hover:bg-gray-50; }
.card { @apply bg-white border border-gray-200 rounded-md shadow-sm p-6; }
.card-interactive { @apply card hover:shadow-md hover:-translate-y-0.5 cursor-pointer; }
.input { @apply w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-gray-900/20; }
.badge-success { @apply inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-50 text-green-700 border-green-200; }
```

## 4.4 Vuetify Integration

Theme colors mapping:
| WeDo Token | Vuetify Color | Hex |
|------------|---------------|-----|
| Primary (preto) | `color="primary"` | #111827 |
| Cyan (accent) | `color="accent"` | #60BED1 |
| Success | `color="success"` | #22C55E |
| Error | `color="error"` | #EF4444 |

Component defaults: VBtn(`text-none`), VTextField/VSelect/VTextarea(`outlined, comfortable`), VCard(`elevation-1`)

## 4.5 Tailwind ↔ Vuetify Mapping

| Tailwind | Vuetify |
|----------|---------|
| `bg-gray-900` | `bg-grey-darken-4` |
| `p-4` | `pa-4` |
| `gap-2` | `ga-2` |
| `<button>` | `<v-btn>` |
| `<input>` | `<v-text-field variant="outlined">` |

## 4.6 Migration v4.0 → v4.1

| Change | Old (v4.0) | New (v4.1) |
|--------|-----------|------------|
| Primary Button | cyan #60BED1 | preto #111827 |
| Typography | 3 fonts | 2 fonts (Open Sans + Inter) |
| Cyan usage | Buttons | ONLY badges/icons LIA |
| Focus Ring | Variable | Standardized gray-900/20 |
| Modal Sizes | 7 sizes | 5 sizes (XS/S/M/L/XL) |

## Reference Files
- `reference/css-tokens.md` - Complete CSS :root tokens with dark mode
- `reference/ts-tokens.md` - Complete TypeScript tokens with helper functions
- `reference/utility-classes.md` - Tailwind @apply utility classes
- `reference/vuetify-config.md` - Full Vuetify theme config + color/spacing/component mapping
- `reference/migration.md` - v4.0 → v4.1 migration checklist
