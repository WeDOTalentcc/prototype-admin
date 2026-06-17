# Forms & Misc Components Reference - Design System LIA v4.1

## Tooltips
```html
<div class="relative group inline-block">
  <button class="p-2 text-gray-600 hover:text-gray-900"><svg class="w-5 h-5">...</svg></button>
  <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none">
    Editar candidato
    <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
  </div>
</div>
<v-tooltip text="Editar candidato" location="top">
  <template #activator="{ props }"><v-btn icon="mdi-pencil" v-bind="props"></v-btn></template>
</v-tooltip>
```
Positions: Top (`bottom-full mb-2`), Bottom (`top-full mt-2`), Left (`right-full mr-2`), Right (`left-full ml-2`)

## Toasts
```html
<div class="fixed top-4 right-4 z-50 space-y-2">
  <div class="flex items-start gap-3 bg-white border border-green-200 rounded-md shadow-lg p-4 max-w-sm">
    <div class="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
      <svg class="w-3 h-3 text-green-600">...</svg>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-gray-900">Sucesso!</p>
      <p class="text-xs text-gray-600 mt-0.5">Candidato salvo com sucesso</p>
    </div>
    <button class="flex-shrink-0 text-gray-400 hover:text-gray-600"><svg class="w-4 h-4">...</svg></button>
  </div>
</div>
```
| Type | Border | Icon BG | Icon Color |
|------|--------|---------|------------|
| Success | `border-green-200` | `bg-green-100` | green-600 |
| Warning | `border-amber-200` | `bg-amber-100` | amber-600 |
| Error | `border-red-200` | `bg-red-100` | red-600 |
| Info | `border-blue-200` | `bg-blue-100` | blue-600 |

## Dropdowns
```html
<div class="relative">
  <button class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50">
    <span>Opções</span><svg class="w-4 h-4">...</svg>
  </button>
  <div class="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50">
    <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Editar</a>
    <div class="border-t border-gray-200 my-1"></div>
    <a href="#" class="block px-4 py-2 text-sm text-red-600 hover:bg-red-50">Deletar</a>
  </div>
</div>
```

## Accordions
```html
<div class="border border-gray-200 rounded-md overflow-hidden">
  <button class="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 text-left">
    <span class="text-sm font-semibold text-gray-900">Pergunta</span>
    <svg class="w-5 h-5 text-gray-600 transition-transform duration-200">...</svg>
  </button>
  <div class="px-4 py-3 bg-gray-50 border-t border-gray-200">
    <p class="text-sm text-gray-600">Resposta</p>
  </div>
</div>
```

## Progress - Linear
```html
<div class="space-y-2">
  <div class="flex items-center justify-between text-sm">
    <span class="font-semibold text-gray-900">Progresso</span>
    <span class="text-gray-600">65%</span>
  </div>
  <div class="w-full bg-gray-200 rounded-full h-2">
    <div class="bg-gray-900 h-2 rounded-full transition-all" style="width: 65%"></div>
  </div>
</div>
```

## Progress - Circular
```html
<div class="relative inline-flex items-center justify-center">
  <svg class="w-16 h-16">
    <circle cx="32" cy="32" r="28" stroke="#E5E7EB" stroke-width="4" fill="none"></circle>
    <circle cx="32" cy="32" r="28" stroke="#111827" stroke-width="4" fill="none"
      stroke-dasharray="176" stroke-dashoffset="52.8" transform="rotate(-90 32 32)" class="transition-all"></circle>
  </svg>
  <span class="absolute text-sm font-semibold text-gray-900">70%</span>
</div>
<v-progress-circular :model-value="70" :size="64" :width="4" color="grey-darken-4">70%</v-progress-circular>
```

## Avatars
```html
<!-- Small 24px --><div class="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-[10px] font-semibold text-gray-700">JS</div>
<!-- Medium 32px --><div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-semibold text-gray-700">JS</div>
<!-- Large 40px --><div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-sm font-semibold text-gray-700">JS</div>
<!-- With image --><img src="avatar.jpg" alt="Nome" class="w-8 h-8 rounded-full object-cover" />
<!-- Group -->
<div class="flex -space-x-2">
  <img src="u1.jpg" class="w-8 h-8 rounded-full border-2 border-white" />
  <img src="u2.jpg" class="w-8 h-8 rounded-full border-2 border-white" />
  <div class="w-8 h-8 bg-gray-200 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-semibold text-gray-700">+5</div>
</div>
```

## Pagination
```html
<div class="flex items-center justify-between">
  <div class="text-sm text-gray-600">Mostrando <span class="font-semibold">1-10</span> de <span class="font-semibold">97</span></div>
  <div class="flex items-center gap-1">
    <button class="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50" disabled>Anterior</button>
    <button class="px-3 py-1.5 text-sm bg-gray-900 text-white rounded">1</button>
    <button class="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">2</button>
    <span class="px-2 text-sm text-gray-600">...</span>
    <button class="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">Próximo</button>
  </div>
</div>
```

## Switches
```html
<label class="flex items-center gap-3 cursor-pointer">
  <button :class="enabled ? 'bg-gray-900' : 'bg-gray-300'"
    class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:ring-2 focus:ring-gray-900/20">
    <span :class="enabled ? 'translate-x-6' : 'translate-x-1'"
      class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"></span>
  </button>
  <span class="text-sm text-gray-800">Ativar notificações</span>
</label>
<v-switch label="Ativar notificações" color="grey-darken-4" hide-details></v-switch>
```

## Tabs
```html
<div class="border-b border-gray-200">
  <nav class="flex gap-4">
    <button class="px-4 py-2 text-sm font-semibold text-gray-900 border-b-2 border-gray-900">Detalhes</button>
    <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent">Histórico</button>
  </nav>
</div>
<v-tabs v-model="tab" color="grey-darken-4">
  <v-tab value="details">Detalhes</v-tab>
  <v-tab value="history">Histórico</v-tab>
</v-tabs>
```

## Dividers
```html
<hr class="border-t border-gray-200" />
<div class="w-px h-8 bg-gray-200"></div><!-- Vertical -->
<!-- With text -->
<div class="flex items-center gap-4">
  <hr class="flex-1 border-t border-gray-200" />
  <span class="text-xs text-gray-600 font-semibold">OU</span>
  <hr class="flex-1 border-t border-gray-200" />
</div>
```

## File Upload
```html
<div class="border-2 border-dashed border-gray-300 rounded-md p-6 text-center hover:border-gray-400 transition-colors">
  <input type="file" id="file-upload" class="hidden" />
  <label for="file-upload" class="cursor-pointer">
    <svg class="w-12 h-12 text-gray-400 mx-auto mb-2">...</svg>
    <p class="text-sm text-gray-600"><span class="text-gray-900 font-semibold">Clique para enviar</span> ou arraste</p>
    <p class="text-xs text-gray-500 mt-1">PNG, JPG ou PDF até 10MB</p>
  </label>
</div>
```

## Sliders
```html
<input type="range" min="0" max="100" value="50"
  class="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-gray-900" />
<v-slider label="Volume" :min="0" :max="100" color="grey-darken-4" thumb-label></v-slider>
```

## Date Pickers
```html
<input type="date" class="w-full px-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-gray-900/20" />
<v-text-field label="Data" type="date" variant="outlined" density="comfortable"></v-text-field>
```
