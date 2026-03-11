# Migration v4.0 → v4.1 Reference - Design System LIA v4.1

## Changes Summary

| Mudança | v4.0 (Antigo) | v4.1 (Novo) |
|---------|---------------|-------------|
| **Botão Primary** | cyan `#60BED1` | preto `#111827` |
| **Tipografia** | 3 fontes (Open Sans + Inter + Serif) | 2 fontes (Open Sans + Inter) |
| **Cyan** | Botões principais | APENAS badges/ícones LIA |
| **Dark Mode** | Opcional | Light-first + Dark preparado |
| **Focus Ring** | Variável por componente | Padronizado `gray-900/20` |
| **Modal Sizes** | 7 tamanhos | 5 tamanhos (XS/S/M/L/XL) |
| **Glassmorphism** | Não documentado | Adicionado (seção 1.10) |
| **Integração Vuetify** | Não documentada | Completa (seção 4.4) |
| **Tokens CSS/TS** | Mencionados apenas | Arquivos completos |
| **Acessibilidade** | Básica | Expandida (contraste WCAG, ARIA) |

## Migration Checklist

### 1. Buttons (CRITICAL)
- [ ] Replace ALL `bg-[#60BED1]` or `bg-cyan-*` primary buttons with `bg-gray-900`
- [ ] Update hover states to `bg-gray-800`
- [ ] Ensure disabled states use `bg-gray-300 text-gray-500`
- [ ] Add focus ring: `focus:ring-2 focus:ring-gray-900/20`

### 2. Typography
- [ ] Remove all Source Serif 4 references
- [ ] Replace Source Serif 4 with Open Sans for headers
- [ ] Verify Open Sans for: headers, nav, buttons, labels
- [ ] Verify Inter for: body, forms, tables, badges

### 3. Cyan Usage
- [ ] Audit all cyan color usage
- [ ] Keep cyan ONLY for: Brain icon, LIA badges, AI feature indicators
- [ ] Remove cyan from: buttons, links, form elements, borders

### 4. Modal Sizes
- [ ] Replace max-w-xl with max-w-lg (M) or max-w-2xl (L)
- [ ] Replace max-w-3xl with max-w-2xl (L) or max-w-4xl (XL)
- [ ] Replace max-w-5xl with max-w-4xl (XL)
- [ ] Only use: max-w-sm, max-w-md, max-w-lg, max-w-2xl, max-w-4xl

### 5. Focus Rings
- [ ] Standardize all focus rings to `ring-2 ring-gray-900/20`
- [ ] Remove any colored focus rings (blue, cyan, etc.)
- [ ] Ensure focus is visible on all interactive elements

### 6. Dark Mode
- [ ] Add CSS custom properties from tokens
- [ ] Set up `data-theme="dark"` attribute on root
- [ ] Test contrast ratios in dark mode
- [ ] WeDo accent colors stay the same in dark mode

### 7. Accessibility
- [ ] Add `aria-label` to all icon-only buttons
- [ ] Add `role="dialog"` and `aria-modal="true"` to modals
- [ ] Add `aria-required`, `aria-invalid` to form inputs
- [ ] Implement `prefers-reduced-motion` media query
- [ ] Test with screen reader
