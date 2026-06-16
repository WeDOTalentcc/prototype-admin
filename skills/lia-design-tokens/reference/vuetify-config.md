# Vuetify Integration Reference - Design System LIA v4.1

## Full Configuration (main.js)
```javascript
import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'

const vuetify = createVuetify({
  components, directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#111827',
          secondary: '#1F2937',
          accent: '#60BED1',
          error: '#EF4444',
          warning: '#F59E0B',
          info: '#3B82F6',
          success: '#22C55E',
          background: '#FFFFFF',
          surface: '#F9FAFB',
          'on-background': '#111827',
          'on-surface': '#1F2937',
        },
      },
      dark: {
        colors: {
          primary: '#F9FAFB',
          secondary: '#E5E7EB',
          accent: '#60BED1',
          background: '#0F1113',
          surface: '#1A1D1F',
          'on-background': '#F9FAFB',
          'on-surface': '#E5E7EB',
        },
      },
    },
  },
  defaults: {
    VBtn: { variant: 'elevated', color: 'primary', class: 'text-none' },
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
    VTextarea: { variant: 'outlined', density: 'comfortable' },
    VCard: { elevation: 1 },
  },
})

const app = createApp(App)
app.use(vuetify)
app.mount('#app')
```

## Color Mapping
| Token WeDo | Hex | Vuetify Color | Uso |
|------------|-----|---------------|-----|
| Primary (preto) | #111827 | `color="primary"` | Botões principais |
| Secondary | #1F2937 | `color="secondary"` | Botões secundários |
| Cyan (accent) | #60BED1 | `color="accent"` | Brain icon, badges |
| Success | #22C55E | `color="success"` | Status positivo |
| Warning | #F59E0B | `color="warning"` | Avisos |
| Error | #EF4444 | `color="error"` | Erros, deletar |
| Info | #3B82F6 | `color="info"` | Informações |

## Tailwind ↔ Vuetify

### Colors
| Tailwind | Vuetify | Hex |
|----------|---------|-----|
| `bg-gray-900` | `bg-grey-darken-4` | #111827 |
| `bg-gray-800` | `bg-grey-darken-3` | #1F2937 |
| `bg-gray-600` | `bg-grey-darken-1` | #4B5563 |
| `bg-gray-50` | `bg-grey-lighten-5` | #F9FAFB |
| `text-gray-900` | `text-grey-darken-4` | #111827 |
| `border-gray-200` | `border-grey-lighten-3` | #E5E7EB |

### Spacing
| Tailwind | Vuetify | Pixels |
|----------|---------|--------|
| `p-2` | `pa-2` | 8px |
| `p-4` | `pa-4` | 16px |
| `p-6` | `pa-6` | 24px |
| `p-8` | `pa-8` | 32px |
| `gap-2` | `ga-2` | 8px |

### Components
| HTML/Tailwind | Vuetify | Notes |
|---------------|---------|-------|
| `<button class="btn">` | `<v-btn>` | `class="text-none"` |
| `<input type="text">` | `<v-text-field variant="outlined">` | `density="comfortable"` |
| `<textarea>` | `<v-textarea variant="outlined">` | |
| `<select>` | `<v-select variant="outlined">` | |
| `<div class="card">` | `<v-card>` | `elevation="1"` |
| `<dialog>` | `<v-dialog>` | `max-width` required |
