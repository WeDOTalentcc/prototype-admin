/**
 * Chart Colors — Tokens semanticos para Recharts (DS LIA v4.2.1).
 *
 * Recharts (LineChart/BarChart/PieChart) recebe `stroke` e `fill` como strings
 * literais — nao aceita classes Tailwind. Para evitar hex hardcoded espalhados
 * pelos paineis, todos os componentes que renderizam graficos devem importar
 * dessa fonte canonica.
 *
 * Mapeamento (alinhado com `tailwind.config.ts` -> `theme.extend.colors`):
 *   - GRID                -> gray-200 (border-subtle)
 *   - AXIS_TICK / LABEL   -> gray-500 (text-muted)
 *   - SERIES_NEUTRAL      -> gray-900 (data dominante / 90% mono)
 *   - SERIES_LIA          -> wedo-cyan (#60BED1) — uso unico para acento IA
 *   - SERIES_SUCCESS      -> wedo-green (#5DA47A)
 *   - SERIES_WARNING      -> amber-500 (status warning)
 *   - SERIES_DANGER       -> red-600 (status error)
 *   - SERIES_INFO         -> sky-500 (status info)
 *
 * Quando precisar de paleta multi-serie em um grafico, prefira usar a sequencia
 * abaixo (NEUTRAL -> LIA -> SUCCESS -> WARNING -> DANGER) para manter a regra
 * 90/10 do DS — nunca empilhar 4 cores vivas no mesmo chart.
 */

export const CHART_GRID = "#E5E7EB" // gray-200
export const CHART_AXIS = "#6B7280" // gray-500

export const CHART_NEUTRAL = "#111827" // gray-900
export const CHART_LIA = "#60BED1" // wedo-cyan
export const CHART_SUCCESS = "#5DA47A" // wedo-green
export const CHART_WARNING = "#EAB308" // amber-500 / yellow-500
export const CHART_DANGER = "#DC2626" // red-600
export const CHART_INFO = "#0EA5E9" // sky-500

/** Paleta padrao para multi-series — segue regra 90/10 do DS. */
export const CHART_PALETTE = [
  CHART_NEUTRAL,
  CHART_LIA,
  CHART_SUCCESS,
  CHART_WARNING,
  CHART_DANGER,
] as const
