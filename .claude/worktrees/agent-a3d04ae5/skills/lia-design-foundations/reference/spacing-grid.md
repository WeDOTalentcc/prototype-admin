# Spacing & Grid Reference - Design System LIA v4.1

## Espaçamento (8px system)

| Token | Pixels | Rem | Tailwind | Vuetify | Uso |
|-------|--------|-----|----------|---------|-----|
| `--space-0` | 0px | 0 | `p-0` | `pa-0` | Sem espaçamento |
| `--space-0.5` | 4px | 0.25rem | `p-1` | `pa-1` | Micro spacing |
| `--space-1` | 8px | 0.5rem | `p-2` | `pa-2` | Extra pequeno |
| `--space-1.5` | 12px | 0.75rem | `p-3` | `pa-3` | Pequeno |
| `--space-2` | 16px | 1rem | `p-4` | `pa-4` | **Padrão** |
| `--space-2.5` | 20px | 1.25rem | `p-5` | `pa-5` | Médio-pequeno |
| `--space-3` | 24px | 1.5rem | `p-6` | `pa-6` | Médio |
| `--space-4` | 32px | 2rem | `p-8` | `pa-8` | Grande |
| `--space-5` | 40px | 2.5rem | `p-10` | `pa-10` | Extra grande |
| `--space-6` | 48px | 3rem | `p-12` | `pa-12` | Seções |
| `--space-8` | 64px | 4rem | `p-16` | `pa-16` | Entre seções |

### Uso Recomendado
| Contexto | Espaçamento | Exemplo |
|----------|-------------|---------|
| Entre ícone e texto | 8px (space-1) | Botões com ícone |
| Padding de botões | 12-16px | Botões médios |
| Gap entre form fields | 16px (space-2) | Formulários |
| Padding de cards | 24px (space-3) | Cards principais |
| Entre cards | 24px (space-3) | Grids de cards |
| Padding de modais | 24-32px | Headers e bodies |
| Entre seções | 48-64px | Páginas |

## Grid de 12 Colunas

```html
<!-- Tailwind -->
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-12 md:col-span-6 lg:col-span-4">...</div>
  <div class="col-span-12 md:col-span-6 lg:col-span-8">...</div>
</div>

<!-- Vuetify -->
<v-row class="ga-6">
  <v-col cols="12" md="6" lg="4">...</v-col>
  <v-col cols="12" md="6" lg="8">...</v-col>
</v-row>
```

### Container Widths
| Breakpoint | Max Width | Padding |
|------------|-----------|---------|
| Mobile (< 640px) | 100% | 16px |
| Tablet (640-1023px) | 100% | 24px |
| Desktop (≥ 1024px) | 1280px | 32px |
| Wide (≥ 1536px) | 1440px | 40px |

### Gaps Padrão
| Contexto | Gap | Tailwind | Vuetify |
|----------|-----|----------|--------|
| Tight | 8px | `gap-2` | `ga-2` |
| Default | 16px | `gap-4` | `ga-4` |
| Comfortable | 24px | `gap-6` | `ga-6` |
| Spacious | 32px | `gap-8` | `ga-8` |

## Breakpoints

| Nome | Min Width | Target | Tailwind | Vuetify |
|------|-----------|--------|----------|---------|
| xs | < 640px | Mobile portrait | (default) | `xs` |
| sm | 640px | Mobile landscape | `sm:` | `sm` |
| md | 768px | Tablet portrait | `md:` | `md` |
| lg | 1024px | Desktop | `lg:` | `lg` |
| xl | 1280px | Large desktop | `xl:` | `xl` |
| 2xl | 1536px | Extra large | `2xl:` | `xxl` |

### Mobile-First
```html
<div class="p-4 md:p-6 lg:p-8">Card</div>
<!-- Vuetify -->
<v-card class="pa-4 pa-md-6 pa-lg-8">Card</v-card>
```
