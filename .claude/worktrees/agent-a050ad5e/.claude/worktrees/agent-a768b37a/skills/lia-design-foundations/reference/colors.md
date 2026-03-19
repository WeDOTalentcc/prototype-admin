# Colors Reference - Design System LIA v4.1

## 1. Sistema Monocromático (90%)

### Backgrounds
| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-bg-primary` | `#FFFFFF` | `bg-white` | `bg-white` | Fundo principal |
| `--lia-bg-secondary` | `#F9FAFB` | `bg-gray-50` | `bg-grey-lighten-5` | Cards, painéis, sidebars |
| `--lia-bg-tertiary` | `#F3F4F6` | `bg-gray-100` | `bg-grey-lighten-4` | Hover, disabled |
| `--lia-bg-elevated` | `#FFFFFF` | `bg-white` | `bg-white elevation-1` | Cards elevados |

### Textos
| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-text-primary` | `#111827` | `text-gray-900` | `text-grey-darken-4` | Títulos |
| `--lia-text-body` | `#1F2937` | `text-gray-800` | `text-grey-darken-3` | Texto principal |
| `--lia-text-secondary` | `#4B5563` | `text-gray-600` | `text-grey-darken-1` | Descrições |
| `--lia-text-muted` | `#6B7280` | `text-gray-500` | `text-grey` | Placeholders |
| `--lia-text-disabled` | `#9CA3AF` | `text-gray-400` | `text-grey-lighten-1` | Desabilitado |

### Bordas
| Token | Hex | Tailwind | Vuetify | Uso |
|-------|-----|----------|---------|-----|
| `--lia-border-subtle` | `#E5E7EB` | `border-gray-200` | `border-grey-lighten-3` | Padrão |
| `--lia-border-default` | `#D1D5DB` | `border-gray-300` | `border-grey-lighten-2` | Destaque |
| `--lia-border-medium` | `#9CA3AF` | `border-gray-400` | `border-grey-lighten-1` | Forte |

### Botão Primary (Preto)
| Estado | Background | Text | Border |
|--------|------------|------|--------|
| Default | `bg-gray-900` (#111827) | `text-white` | none |
| Hover | `bg-gray-800` (#1F2937) | `text-white` | none |
| Active | `bg-gray-700` (#374151) | `text-white` | none |
| Focus | `bg-gray-900` + ring | `text-white` | `ring-2 ring-gray-900/20` |
| Disabled | `bg-gray-300` (#D1D5DB) | `text-gray-500` | none |

## 2. Cores de Acento WeDo (10%)

**REGRA DE OURO**: APENAS para badges, ícones contextuais e status. NUNCA para botões primários.

| Cor | Hex | Token | Uso Semântico |
|-----|-----|-------|---------------|
| Cyan | `#60BED1` | `--wedo-cyan` | Brain LIA, Vagas, Automação |
| Cyan Dark | `#4DA8BB` | `--wedo-cyan-dark` | Hover states |
| Green | `#5DA47A` | `--wedo-green` | Candidatos, Sucesso |
| Orange | `#D19960` | `--wedo-orange` | Tempo, Prazos |
| Purple | `#9860D1` | `--wedo-purple` | Insights, IA |
| Magenta | `#D160AB` | `--wedo-magenta` | Urgência crítica |
| Amber | `#F59E0B` | `--wedo-amber` | Warning vibrante |

### Variações Dark (hover)
| Base | Dark | Uso |
|------|------|-----|
| Cyan #60BED1 | #4DA8BB | Hover cyan |
| Green #5DA47A | #4B8862 | Hover green |
| Orange #D19960 | #B8814D | Hover orange |
| Purple #9860D1 | #7F4DB8 | Hover purple |
| Magenta #D160AB | #B84D92 | Hover magenta |

### Variações Light (backgrounds 10% opacidade)
| Cor | Token | Valor RGBA | Uso |
|-----|-------|------------|-----|
| Cyan Light | `--wedo-cyan-light` | `rgba(96,190,209,0.1)` | Background badges LIA |
| Green Light | `--wedo-green-light` | `rgba(93,164,122,0.1)` | Background badges candidatos |
| Orange Light | `--wedo-orange-light` | `rgba(209,153,96,0.1)` | Background badges tempo |
| Purple Light | `--wedo-purple-light` | `rgba(152,96,209,0.1)` | Background badges insights |
| Magenta Light | `--wedo-magenta-light` | `rgba(209,96,171,0.1)` | Background badges urgência |

## 3. Cores de Status (Semântico)

| Status | Background | Text | Border | Ícone | Quando Usar |
|--------|------------|------|--------|-------|-------------|
| Sucesso | `bg-green-50` | `text-green-700` | `border-green-200` | CheckCircle | Confirmações |
| Alerta | `bg-amber-50` | `text-amber-700` | `border-amber-200` | AlertTriangle | Avisos |
| Erro | `bg-red-50` | `text-red-700` | `border-red-200` | XCircle | Erros |
| Info | `bg-blue-50` | `text-blue-700` | `border-blue-200` | Info | Informações |
| Neutro | `bg-gray-100` | `text-gray-700` | `border-gray-200` | Circle | Padrão |

**Contraste WCAG AA:**
- green-700/green-50: 7.2:1 (AAA) ✅
- amber-700/amber-50: 6.8:1 (AAA) ✅
- red-700/red-50: 7.1:1 (AAA) ✅
- blue-700/blue-50: 7.3:1 (AAA) ✅

## 4. Dark Mode

| Token | Light | Dark |
|-------|-------|------|
| `--lia-bg-primary` | #FFFFFF | #0F1113 |
| `--lia-bg-secondary` | #F9FAFB | #1A1D1F |
| `--lia-bg-tertiary` | #F3F4F6 | #26292B |
| `--lia-bg-elevated` | #FFFFFF | #1A1D1F |
| `--lia-text-primary` | #111827 | #F9FAFB |
| `--lia-text-body` | #1F2937 | #E5E7EB |
| `--lia-text-secondary` | #4B5563 | #9CA3AF |
| `--lia-text-muted` | #6B7280 | #6B7280 |
| `--lia-text-disabled` | #9CA3AF | #4B5563 |
| `--lia-border-subtle` | #E5E7EB | #374151 |
| `--lia-border-default` | #D1D5DB | #4B5563 |
| `--lia-border-medium` | #9CA3AF | #6B7280 |

Cores WeDo mantêm-se iguais em dark mode.
