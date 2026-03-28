# Buttons & Inputs Reference - Design System LIA v4.1

## Buttons

### Primary (Preto - Ação Principal)
```html
<!-- Tailwind -->
<button class="px-5 py-2 bg-gray-900 text-white text-sm font-semibold rounded font-['Open_Sans'] hover:bg-gray-800 active:scale-98 focus:ring-2 focus:ring-gray-900/20 disabled:bg-gray-300 disabled:text-gray-500 transition-all duration-150">
  Primary Button
</button>

<!-- Vuetify -->
<v-btn color="grey-darken-4" class="text-none font-weight-semibold">Primary Button</v-btn>
```

| Estado | Background | Text | Border | Transform |
|--------|------------|------|--------|-----------|
| Default | `bg-gray-900` | `text-white` | none | none |
| Hover | `bg-gray-800` | `text-white` | none | `translateY(-1px)` |
| Active | `bg-gray-700` | `text-white` | none | `translateY(0) scale(0.98)` |
| Focus | `bg-gray-900` | `text-white` | `ring-2 ring-gray-900/20` | none |
| Disabled | `bg-gray-300` | `text-gray-500` | none | none |
| Loading | `bg-gray-900` | `text-white` | none | none |

### Secondary (Outline)
```html
<button class="px-5 py-2 bg-transparent text-gray-900 text-sm font-semibold rounded border border-gray-300 hover:bg-gray-50 hover:border-gray-400 focus:ring-2 focus:ring-gray-900/20 disabled:text-gray-400 disabled:border-gray-200">
  Secondary Button
</button>
<v-btn variant="outlined" color="grey-darken-4" class="text-none">Secondary</v-btn>
```

### Ghost (Texto)
```html
<button class="px-5 py-2 bg-transparent text-gray-700 text-sm font-semibold rounded hover:bg-gray-100 hover:text-gray-900">
  Ghost Button
</button>
<v-btn variant="text" color="grey-darken-2" class="text-none">Ghost</v-btn>
```

### Destructive
```html
<button class="px-5 py-2 bg-red-600 text-white text-sm font-semibold rounded hover:bg-red-700 focus:ring-2 focus:ring-red-600/20">
  Deletar
</button>
<v-btn color="red-darken-2" class="text-none">Deletar</v-btn>
```

### Sizes
| Size | Height | Padding X | Font Size | Icon Size |
|------|--------|-----------|-----------|-----------|
| Small | 32px | 12px | 12px | 16px |
| Medium | 36px | 16px | 14px | 20px |
| Large | 44px | 20px | 14px | 20px |

```html
<button class="px-3 py-1.5 text-xs">Small</button>
<button class="px-4 py-2 text-sm">Medium (default)</button>
<button class="px-5 py-2.5 text-sm">Large</button>
```

### With Icons
```html
<button class="flex items-center gap-2 px-5 py-2 bg-gray-900 text-white rounded">
  <svg class="w-5 h-5">...</svg>
  <span>Adicionar</span>
</button>
<button class="p-2 bg-gray-900 text-white rounded" aria-label="Editar">
  <svg class="w-5 h-5">...</svg>
</button>
```

### Loading State
```html
<button class="px-5 py-2 bg-gray-900 text-white rounded flex items-center gap-2" disabled>
  <svg class="w-5 h-5 animate-spin" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
  <span>Salvando...</span>
</button>
<v-btn :loading="true" color="grey-darken-4">Salvando</v-btn>
```

---

## Text Input

```html
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800 font-['Inter']">Email</label>
  <input type="email" placeholder="seu@email.com"
    class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-900" />
  <p class="text-xs text-gray-600">Digite seu email principal</p>
</div>

<!-- Error -->
<input class="w-full px-3 py-2 text-sm border border-red-300 rounded focus:ring-2 focus:ring-red-600/20 bg-red-50"
  aria-invalid="true" aria-describedby="email-error" />
<p id="email-error" class="text-xs text-red-600 flex items-center gap-1">
  <svg class="w-4 h-4">...</svg> Email inválido
</p>

<!-- Disabled -->
<input disabled class="w-full px-3 py-2 text-sm border border-gray-200 rounded bg-gray-100 text-gray-500 cursor-not-allowed" />

<!-- Vuetify -->
<v-text-field label="Email" placeholder="seu@email.com" variant="outlined" density="comfortable" hint="Digite seu email principal" persistent-hint></v-text-field>
<v-text-field label="Email" variant="outlined" :error-messages="['Email inválido']"></v-text-field>
```

## Textarea
```html
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Descrição</label>
  <textarea rows="4" placeholder="Descreva aqui..."
    class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-900 resize-none"></textarea>
  <p class="text-xs text-gray-600">Máximo 500 caracteres</p>
</div>
<v-textarea label="Descrição" variant="outlined" rows="4" no-resize counter="500"></v-textarea>
```

## Select
```html
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Status</label>
  <select class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-gray-900/20 bg-white">
    <option value="">Selecione...</option>
    <option value="active">Ativo</option>
  </select>
</div>
<v-select label="Status" :items="['Ativo', 'Pendente']" variant="outlined" density="comfortable"></v-select>
```

## Checkbox
```html
<label class="flex items-center gap-2 cursor-pointer">
  <input type="checkbox" class="w-4 h-4 border-gray-300 rounded text-gray-900 focus:ring-2 focus:ring-gray-900/20" />
  <span class="text-sm text-gray-800">Aceito os termos</span>
</label>
<v-checkbox label="Aceito os termos" color="grey-darken-4"></v-checkbox>
```

## Radio
```html
<div class="space-y-2">
  <label class="flex items-center gap-2 cursor-pointer">
    <input type="radio" name="plan" value="free" class="w-4 h-4 border-gray-300 text-gray-900 focus:ring-2 focus:ring-gray-900/20"/>
    <span class="text-sm text-gray-800">Gratuito</span>
  </label>
</div>
<v-radio-group>
  <v-radio label="Gratuito" value="free" color="grey-darken-4"></v-radio>
</v-radio-group>
```
