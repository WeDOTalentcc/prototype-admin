# Typography Reference - Design System LIA v4.1

## Sistema Dual de Fontes

**v4.1:** Source Serif 4 REMOVIDO. Sistema com apenas 2 fontes.

| Fonte | Uso | Proporção | Quando Usar |
|-------|-----|-----------|-------------|
| **Open Sans** | Brand Layer | ~60% | Headers, nav, buttons, labels |
| **Inter** | Data Layer | ~40% | Body, forms, tables, métricas |

### Open Sans - Brand Layer
Pesos: 400 (Regular), 600 (Semibold), 700 (Bold)
Usar em: Headers (h1-h6), navegação, botões, títulos de cards, labels, CTAs
```css
font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
```

### Inter - Data Layer
Pesos: 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)
Usar em: Body text, formulários, tabelas, badges, descrições, KPIs, tooltips
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
font-feature-settings: 'tnum' 1; /* Para tabelas */
```

## Type Scale

| Nome | Tamanho | Line Height | Peso | Fonte | Uso |
|------|---------|-------------|------|-------|-----|
| Display | 40px (2.5rem) | 1.25 (50px) | 700 | Open Sans | Hero titles |
| H1 | 32px (2rem) | 1.25 (40px) | 700 | Open Sans | Page titles |
| H2 | 24px (1.5rem) | 1.25 (30px) | 700 | Open Sans | Section titles |
| H3 | 20px (1.25rem) | 1.5 (30px) | 600 | Open Sans | Card titles |
| H4 | 16px (1rem) | 1.5 (24px) | 600 | Open Sans | Sub-headers |
| H5 | 14px (0.875rem) | 1.5 (21px) | 600 | Open Sans | Small headers |
| Body Large | 16px (1rem) | 1.5 (24px) | 400 | Inter | Primary body |
| Body | 14px (0.875rem) | 1.5 (21px) | 400 | Inter | Default text |
| Body Small | 12px (0.75rem) | 1.5 (18px) | 400 | Inter | Secondary text |
| Caption | 12px (0.75rem) | 1.5 (18px) | 400 | Inter | Captions, hints |
| Label | 11px (0.6875rem) | 1.5 (16.5px) | 600 | Inter | Form labels |
| Micro | 10px (0.625rem) | 1.5 (15px) | 500 | Inter | Badges, tiny |

**Mínimo:** 10px por acessibilidade (WCAG AA).

## Classes Tailwind
```html
<!-- Headers (Open Sans) -->
<h1 class="text-4xl font-bold font-['Open_Sans']">Display</h1>
<h2 class="text-3xl font-bold font-['Open_Sans']">H1</h2>
<h3 class="text-2xl font-bold font-['Open_Sans']">H2</h3>
<h4 class="text-xl font-semibold font-['Open_Sans']">H3</h4>
<h5 class="text-base font-semibold font-['Open_Sans']">H4</h5>
<h6 class="text-sm font-semibold font-['Open_Sans']">H5</h6>

<!-- Body (Inter) -->
<p class="text-base font-['Inter']">Body Large</p>
<p class="text-sm font-['Inter']">Body</p>
<p class="text-xs font-['Inter']">Body Small</p>
<span class="text-xs text-gray-600 font-['Inter']">Caption</span>
<label class="text-[11px] font-semibold font-['Inter']">Label</label>
<span class="text-[10px] font-medium font-['Inter']">Micro</span>
```

## Classes Vuetify
```html
<h1 class="text-h1">Display</h1>
<h2 class="text-h2">H1</h2>
<h3 class="text-h3">H2</h3>
<h4 class="text-h4">H3</h4>
<h5 class="text-h5">H4</h5>
<h6 class="text-h6">H5</h6>
<p class="text-body-1">Body Large</p>
<p class="text-body-2">Body</p>
<span class="text-caption">Caption</span>
<span class="text-overline">Label</span>
```

## Carregamento
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```
