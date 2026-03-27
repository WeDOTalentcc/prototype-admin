# Component States Reference - Design System LIA v4.1

## Hierarchy (Priority Order)

| Estado | Ordem | Classe Visual | Quando Aplicar |
|--------|-------|---------------|----------------|
| **Disabled** | 1 (highest) | Opacidade reduzida | Elemento não disponível |
| **Loading** | 2 | Spinner + disabled | Ação em progresso |
| **Error** | 3 | Border red, bg red-50 | Validação falhou |
| **Focus** | 4 | Ring 2px gray-900/20 | Teclado selecionado |
| **Active** | 5 | Transform scale 0.98 | Mouse clicando |
| **Hover** | 6 | Background + transform | Mouse sobre |
| **Default** | 7 (lowest) | Estado padrão | Nenhuma interação |

## Rules

```css
/* NEVER combine conflicting states */
.button:disabled:hover { } /* ❌ WRONG */
.button:disabled { /* ✅ CORRECT - disabled always wins */ }

/* Focus ALWAYS visible for accessibility */
.button:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2);
}

/* Loading = Disabled + Indicator */
.button[aria-busy="true"] {
  opacity: 0.7;
  cursor: not-allowed;
  pointer-events: none;
}
```

## Button States Example
```html
<!-- Default -->
<button class="bg-gray-900 text-white">Action</button>
<!-- Hover -->
<button class="bg-gray-800 text-white -translate-y-px">Action</button>
<!-- Active -->
<button class="bg-gray-700 text-white scale-[0.98]">Action</button>
<!-- Focus -->
<button class="bg-gray-900 text-white ring-2 ring-gray-900/20">Action</button>
<!-- Disabled -->
<button class="bg-gray-300 text-gray-500 cursor-not-allowed" disabled>Action</button>
<!-- Loading -->
<button class="bg-gray-900 text-white opacity-70 cursor-not-allowed" disabled aria-busy="true">
  <svg class="animate-spin w-4 h-4">...</svg> Loading...
</button>
```

## Input States Example
```html
<!-- Default -->
<input class="border-gray-200 rounded" />
<!-- Focus -->
<input class="border-gray-900 ring-2 ring-gray-900/20" />
<!-- Error -->
<input class="border-red-300 bg-red-50" aria-invalid="true" />
<!-- Disabled -->
<input class="border-gray-200 bg-gray-100 text-gray-500 cursor-not-allowed" disabled />
```
