# Accessibility Reference - Design System LIA v4.1

## WCAG AA Contrast

| Combinação | Contraste | Status | Uso |
|------------|-----------|--------|-----|
| gray-900 / white | 16.73:1 | AAA | Texto primário |
| gray-800 / white | 13.36:1 | AAA | Texto body |
| gray-600 / white | 7.92:1 | AAA | Texto secundário |
| gray-500 / white | 5.89:1 | AA Large | Texto muted |
| green-700 / green-50 | 7.2:1 | AAA | Success |
| red-700 / red-50 | 7.1:1 | AAA | Error |
| amber-700 / amber-50 | 6.8:1 | AAA | Warning |

**NEVER use gray-400 or lighter as main text (insufficient contrast)**

## ARIA Labels

```html
<!-- Icon-only buttons -->
<button aria-label="Editar candidato"><svg>...</svg></button>

<!-- Modals -->
<div role="dialog" aria-labelledby="modal-title" aria-modal="true">
  <h2 id="modal-title">Título</h2>
</div>

<!-- Inputs -->
<label for="email">Email</label>
<input id="email" type="email" aria-required="true" aria-invalid="false" aria-describedby="email-hint" />
<span id="email-hint">Digite seu email</span>

<!-- Loading -->
<button aria-busy="true" aria-live="polite">
  <span class="sr-only">Carregando...</span>
  <svg class="animate-spin">...</svg>
</button>

<!-- Tabs -->
<div role="tablist">
  <button role="tab" aria-selected="true" aria-controls="panel-1">Tab 1</button>
</div>
<div id="panel-1" role="tabpanel">...</div>
```

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Next focusable element |
| Shift+Tab | Previous element |
| Enter | Activate button/link |
| Space | Toggle checkbox/switch, activate button |
| Esc | Close modal/dropdown/popover |
| Arrow Up/Down | Navigate vertical menus/lists |
| Arrow Left/Right | Navigate horizontal tabs/menus |
| Home | First item in list |
| End | Last item in list |

Focus Order: Always follow logical DOM order (top→bottom, left→right)

## Screen Reader Support

```html
<!-- Visually hidden but accessible -->
<span class="sr-only">Descrição para screen readers</span>

<!-- CSS for sr-only -->
<style>
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0;
  margin: -1px; overflow: hidden; clip: rect(0,0,0,0);
  white-space: nowrap; border-width: 0;
}
</style>

<!-- Dynamic announcements -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  Candidato salvo com sucesso
</div>
```

## Color Blindness
- ALWAYS use icons + colors + text labels together
- NEVER rely on color alone for status
```html
<span class="bg-green-50 text-green-700 border border-green-200">
  <svg class="w-3 h-3"><!-- Check --></svg> Aprovado
</span>
```

## Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
