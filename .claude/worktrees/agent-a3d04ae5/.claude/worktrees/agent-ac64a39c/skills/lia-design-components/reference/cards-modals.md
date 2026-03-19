# Cards & Modals Reference - Design System LIA v4.1

## Cards

### Standard Card
```html
<div class="bg-white rounded-md shadow-sm border border-gray-200 p-6">
  <h3 class="text-base font-semibold text-gray-900 mb-2 font-['Open_Sans']">Título</h3>
  <p class="text-sm text-gray-600 font-['Inter']">Descrição do conteúdo.</p>
</div>

<v-card class="pa-6">
  <v-card-title class="text-base font-weight-semibold text-grey-darken-4 mb-2">Título</v-card-title>
  <v-card-text class="text-sm text-grey-darken-1 pa-0">Descrição.</v-card-text>
</v-card>
```

### Interactive Card (Hover)
```html
<div class="bg-white rounded-md shadow-sm border border-gray-200 p-6 transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
  <h3 class="text-base font-semibold text-gray-900">Card Interativo</h3>
  <p class="text-sm text-gray-600 mt-2">Hover effect</p>
</div>
<v-card class="pa-6 hover-lift" hover>...</v-card>
```

### Glass Card
```html
<div class="bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-md p-6 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Card Glass</h3>
</div>
<v-card class="pa-6" style="background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.05);">...</v-card>
```

### Card with Header & Footer
```html
<div class="bg-white rounded-md shadow-sm border border-gray-200 overflow-hidden">
  <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
    <h3 class="text-base font-semibold text-gray-900">Título</h3>
    <button class="text-gray-600 hover:text-gray-900"><svg class="w-5 h-5">...</svg></button>
  </div>
  <div class="px-6 py-4">
    <p class="text-sm text-gray-600">Conteúdo principal</p>
  </div>
  <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
    <button class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">Cancelar</button>
    <button class="px-4 py-2 text-sm bg-gray-900 text-white rounded hover:bg-gray-800">Confirmar</button>
  </div>
</div>
```

---

## Modals

### 5 Standard Sizes (ONLY these)
| Size | Max Width | Pixels | Tailwind | Uso |
|------|-----------|--------|----------|-----|
| XS | max-w-sm | 384px | `max-w-sm` | Confirmações |
| S | max-w-md | 448px | `max-w-md` | Forms compactos |
| M | max-w-lg | 512px | `max-w-lg` | **Padrão** |
| L | max-w-2xl | 672px | `max-w-2xl` | Edição completa |
| XL | max-w-4xl | 896px | `max-w-4xl` | Visualizações |

**PROIBIDO:** max-w-xl, max-w-3xl, max-w-5xl

### Complete Structure
```html
<!-- Overlay -->
<div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" aria-hidden="true"></div>

<!-- Modal Container -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-md shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
    
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-gray-700">...</svg>
        <h2 class="text-sm font-semibold text-gray-900 font-['Open_Sans']">Título do Modal</h2>
      </div>
      <button class="text-gray-600 hover:text-gray-900 p-1 rounded hover:bg-gray-100" aria-label="Fechar">
        <svg class="w-5 h-5">...</svg>
      </button>
    </div>
    
    <!-- Body -->
    <div class="px-6 py-4">
      <p class="text-xs text-gray-600 mb-4 font-['Inter']">Descrição opcional</p>
      <div class="space-y-4"><!-- Content --></div>
    </div>
    
    <!-- Footer -->
    <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
      <button class="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded hover:bg-gray-50">Cancelar</button>
      <button class="px-4 py-2 text-sm bg-gray-900 text-white rounded hover:bg-gray-800">Confirmar</button>
    </div>
  </div>
</div>
```

### Vuetify Modal
```html
<v-dialog v-model="dialog" max-width="512">
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center ga-2">
        <v-icon size="20">mdi-information</v-icon>
        <span class="text-sm font-weight-semibold">Título</span>
      </div>
      <v-btn icon="mdi-close" variant="text" size="small" @click="dialog = false"></v-btn>
    </v-card-title>
    <v-divider></v-divider>
    <v-card-text><!-- Content --></v-card-text>
    <v-divider></v-divider>
    <v-card-actions class="justify-end ga-2">
      <v-btn variant="outlined">Cancelar</v-btn>
      <v-btn color="grey-darken-4">Confirmar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

### Animation
```css
@keyframes modalFadeIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.modal-enter { animation: modalFadeIn 150ms cubic-bezier(0.4, 0, 0.2, 1); }
```
