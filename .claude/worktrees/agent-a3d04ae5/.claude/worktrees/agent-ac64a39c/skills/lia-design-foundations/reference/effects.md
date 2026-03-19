# Effects Reference - Design System LIA v4.1

## Sombras & Elevação

| Nível | Nome | Box Shadow | Uso |
|-------|------|------------|-----|
| 0 | None | none | Elementos planos |
| 1 | Subtle | `0 1px 2px rgba(0,0,0,0.05)` | Cards padrão, inputs |
| 2 | Default | `0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)` | Cards hover, dropdowns |
| 3 | Medium | `0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06)` | Modais, popovers |
| 4 | Large | `0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.08)` | Dialogs grandes |
| 5 | XLarge | `0 16px 32px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.10)` | Drawers, sidebars |

```html
<!-- Tailwind -->
<div class="shadow-sm">Level 1</div>
<div class="shadow">Level 2</div>
<div class="shadow-md">Level 3</div>
<div class="shadow-lg">Level 4</div>
<div class="shadow-xl">Level 5</div>

<!-- Vuetify -->
<v-card elevation="1">Level 1</v-card>
<v-card elevation="3">Level 3</v-card>
```

### Focus Ring
SEMPRE gray-900 com 20% opacidade:
```css
.interactive:focus { outline: none; box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.2); }
```
```html
<button class="focus:ring-2 focus:ring-gray-900/20 focus:ring-offset-2">Botão</button>
```

## Bordas & Raios

### Border Radius
| Token | Valor | Tailwind | Uso |
|-------|-------|----------|-----|
| `--radius-sm` | 4px | `rounded-sm` | Badges pequenos |
| `--radius-default` | 6px | `rounded` | Inputs, buttons |
| `--radius-md` | 8px | `rounded-md` | Cards, modais |
| `--radius-lg` | 12px | `rounded-lg` | Containers grandes |
| `--radius-xl` | 16px | `rounded-xl` | Imagens, avatars |
| `--radius-full` | 9999px | `rounded-full` | Círculos, pills |

### Espessura
| Valor | Tailwind | Uso |
|-------|----------|-----|
| 0px | `border-0` | Sem borda |
| 1px | `border` | **Padrão** |
| 2px | `border-2` | Destaque, selecionado |

## Motion & Animation

### Transitions
- Fast: `100ms cubic-bezier(0.4, 0, 0.2, 1)` → microinterações
- Default: `150ms cubic-bezier(0.4, 0, 0.2, 1)` → hover, focus
- Slow: `200ms cubic-bezier(0.4, 0, 0.2, 1)` → modais, drawers

### Hover Effects - Cards
```css
.card { transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1); }
.card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
```

### Hover Effects - Botões
```css
.button { transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1); }
.button:hover { transform: translateY(-1px); }
.button:active { transform: translateY(0) scale(0.98); }
```

### Modal Animation
```css
@keyframes modalFadeIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.modal-enter { animation: modalFadeIn 150ms cubic-bezier(0.4, 0, 0.2, 1); }
```

## Glassmorphism

```css
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
}
.glass-card-dark {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

Tailwind: `bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-md`

**Quando usar:** Cards sobre backgrounds complexos, modais importantes, dropdowns elegantes
**Quando NÃO usar:** Todos os cards (visual poluído), listas/tabelas simples

## Brain Icon LIA

| Propriedade | Valor |
|-------------|-------|
| Cor | Cyan `#60BED1` |
| Hover | Cyan Dark `#4DA8BB` |
| Tamanhos | 16px, 20px, 24px, 32px, 48px |
| Stroke | 2px |

```html
<!-- React/Lucide -->
<Brain className="w-6 h-6 text-[#60BED1]" />
<!-- Vue/Lucide -->
<Brain :size="24" color="#60BED1" />
```

Brain icon SEMPRE em cyan #60BED1. Nunca em preto/cinza.

### Background Pattern (RARO)
```css
.subtle-pattern {
  background-image:
    radial-gradient(circle at 25% 25%, rgba(0,0,0,0.02) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(0,0,0,0.02) 0%, transparent 50%);
}
```
Usar com EXTREMA parcimônia.
