---
name: lia-design-patterns
description: Design System LIA v4.1 patterns - component states hierarchy, form layout & validation, system feedback (success/error/warning), empty states, error pages (404/500), accessibility (WCAG AA, ARIA, keyboard navigation, screen readers, color blindness, reduced motion). Use when implementing interaction patterns, form validation, feedback messages, error handling, or accessibility features.
---

# LIA Design System v4.1 - Patterns

> **Source:** Design System LIA v4.1 (Fev 2026) - PARTE 3
> For full code examples, read `~/.agents/skills/lia-design-patterns/reference/`

## 3.1 Component States Hierarchy

Priority order (highest to lowest):
1. **Disabled** - `opacity reduced, cursor-not-allowed`
2. **Loading** - `spinner + disabled behavior`
3. **Error** - `border-red, bg-red-50`
4. **Focus** - `ring-2 ring-gray-900/20` (ALWAYS visible)
5. **Active** - `scale(0.98)`
6. **Hover** - `bg change + translateY(-1px)`
7. **Default** - standard state

Rules:
- NEVER combine conflicting states (e.g., disabled + hover)
- Focus ALWAYS visible for accessibility
- Loading = Disabled + visual indicator

## 3.2 Form Patterns

### Layout
- **Vertical (default):** `space-y-4` between fields
- **2 columns:** `grid grid-cols-2 gap-4`
- **Actions:** `flex justify-end gap-2 pt-2` (Cancel left, Submit right)

### Validation
- **Valid:** `border-green-300 bg-green-50` + check icon
- **Error:** `border-red-300 bg-red-50` + error message `text-xs text-red-600`
- **Required:** Label + `<span class="text-red-600">*</span>`
- ARIA: `aria-invalid="true"`, `aria-describedby="error-id"`, `aria-required="true"`

## 3.3 System Feedback

### Alert Messages
| Type | BG | Border | Icon Color | Title Color |
|------|-----|--------|------------|-------------|
| Success | `bg-green-50` | `border-green-200` | `text-green-600` | `text-green-900` |
| Error | `bg-red-50` | `border-red-200` | `text-red-600` | `text-red-900` |
| Warning | `bg-amber-50` | `border-amber-200` | `text-amber-600` | `text-amber-900` |
| Info | `bg-blue-50` | `border-blue-200` | `text-blue-600` | `text-blue-900` |

Structure: `flex items-start gap-3 rounded-md p-4` + icon(w-5) + title(font-semibold) + description(text-sm)

## 3.4 Empty States
```
py-16 text-center
├── Icon (w-16 h-16 text-gray-400 mx-auto mb-4)
├── Title (text-base font-semibold text-gray-900 mb-1)
├── Description (text-sm text-gray-600 mb-4)
└── CTA Button (bg-gray-900 text-white)
```

## 3.5 Error Pages
- **404:** `text-6xl font-bold` code + title + description + "Voltar ao início" button
- **500:** Same structure + "Tentar novamente" button
- Both: centered `max-w-md`, minimal layout

## 3.6 Accessibility (CRITICAL)

### WCAG Contrast (AA minimum)
| Combo | Ratio | Status |
|-------|-------|--------|
| gray-900/white | 16.73:1 | AAA |
| gray-600/white | 7.92:1 | AAA |
| gray-500/white | 5.89:1 | AA Large |
| gray-400/white | ❌ | FAIL - never use for text |

### ARIA Requirements
- Icon-only buttons: `aria-label="Ação"`
- Modals: `role="dialog" aria-labelledby aria-modal="true"`
- Inputs: `aria-required aria-invalid aria-describedby`
- Loading: `aria-busy="true" aria-live="polite"`
- Tabs: `role="tablist/tab/tabpanel" aria-selected aria-controls`

### Keyboard Navigation
| Key | Action |
|-----|--------|
| Tab/Shift+Tab | Navigate focusable elements |
| Enter | Activate button/link |
| Space | Toggle checkbox/switch |
| Esc | Close modal/dropdown |
| Arrow keys | Navigate menus/tabs |
| Home/End | First/last item in list |

### Color Blindness
- ALWAYS pair colors with icons AND text labels
- NEVER use color alone for status indication
```html
<span class="bg-green-50 text-green-700 border border-green-200">
  <CheckIcon class="w-3 h-3" /> Aprovado
</span>
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Screen Readers
- Use `sr-only` class for visually hidden but accessible text
- Use `aria-live="polite"` for dynamic announcements

## Reference Files
- `reference/states.md` - Complete state hierarchy with CSS/code examples
- `reference/forms.md` - Form layouts, validation patterns, error handling
- `reference/feedback.md` - Alerts, empty states, error pages (404/500)
- `reference/accessibility.md` - WCAG contrast, ARIA, keyboard nav, screen reader, color blindness, reduced motion
