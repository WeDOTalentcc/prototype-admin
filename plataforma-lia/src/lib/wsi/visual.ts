/**
 * Task #512 (PR3 da #497) — Token canônico de escala visual WSI.
 *
 * Backend (PR2 do #497) trabalha em escala 0-10 end-to-end. Este módulo
 * é a ÚNICA fonte da verdade no frontend para:
 *   - cores semânticas por faixa de score
 *   - labels de classificação
 *   - cutoffs de status (aprovado / médio / abaixo)
 *   - escala máxima de display
 *
 * Qualquer componente que renderize WSI deve consumir daqui — proibido
 * hardcodar `>= 3.5`, `/5`, `/10`, etc. nos componentes.
 */

export const WSI_DISPLAY_SCALE = 10
export const WSI_DISPLAY_FORMATTED = `${WSI_DISPLAY_SCALE}.0`

/**
 * Cutoffs visuais 3-tier (política de design WSI 0-10):
 *   verde   >= 7.5
 *   amarelo >= 6.0
 *   vermelho < 6.0
 * Cutoffs intermediários (excelente/alto) existem para classificação
 * semântica/badges mas todos mapeiam para a MESMA cor (verde) no esquema
 * 3-tier — nunca quebrar a invariante visual.
 */
export const WSI_VISUAL_3TIER = {
  green: 7.5,
  yellow: 6.0,
} as const

export const WSI_CUTOFFS = {
  excepcional: 9.0,
  excelente: 8.0,
  alto: 7.5,
  medio: 6.0,
  abaixo_da_media: 4.5,
} as const

export const WSI_DECISION_CUTOFFS = {
  approved: 8.4,
  humanReview: 7.6,
} as const

export type WsiClassification =
  | 'excepcional'
  | 'excelente'
  | 'alto'
  | 'medio'
  | 'abaixo_da_media'
  | 'regular'

export interface WsiVisualState {
  classification: WsiClassification
  text: string
  bg: string
  border: string
}

export function getWsiClassification(score: number): WsiClassification {
  if (score >= WSI_CUTOFFS.excepcional) return 'excepcional'
  if (score >= WSI_CUTOFFS.excelente) return 'excelente'
  if (score >= WSI_CUTOFFS.alto) return 'alto'
  if (score >= WSI_CUTOFFS.medio) return 'medio'
  if (score >= WSI_CUTOFFS.abaixo_da_media) return 'abaixo_da_media'
  return 'regular'
}

// Política 3-tier: success (>=7.5) / warning (>=6.0) / error (<6.0).
// Classificações intermediárias (excelente/alto) compartilham success.
const VISUAL_BY_CLASSIFICATION: Record<WsiClassification, Omit<WsiVisualState, 'classification'>> = {
  excepcional:     { text: 'text-status-success',  bg: 'bg-status-success/15',  border: 'border-status-success/30' },
  excelente:       { text: 'text-status-success',  bg: 'bg-status-success/15',  border: 'border-status-success/30' },
  alto:            { text: 'text-status-success',  bg: 'bg-status-success/15',  border: 'border-status-success/30' },
  medio:           { text: 'text-status-warning',  bg: 'bg-status-warning/15',  border: 'border-status-warning/30' },
  abaixo_da_media: { text: 'text-status-error',    bg: 'bg-status-error/15',    border: 'border-status-error/30' },
  regular:         { text: 'text-status-error',    bg: 'bg-status-error/15',    border: 'border-status-error/30' },
}

export function getWsiVisualState(score: number): WsiVisualState {
  const classification = getWsiClassification(score)
  return { classification, ...VISUAL_BY_CLASSIFICATION[classification] }
}

export function getWsiVisualStateForClassification(classification: string): WsiVisualState {
  const safe = (classification as WsiClassification) in VISUAL_BY_CLASSIFICATION
    ? (classification as WsiClassification)
    : 'medio'
  return { classification: safe, ...VISUAL_BY_CLASSIFICATION[safe] }
}

export function wsiPercent(score: number): number {
  return Math.max(0, Math.min(100, Math.round((score / WSI_DISPLAY_SCALE) * 100)))
}

export function formatWsiScore(score: number, fractionDigits = 1): string {
  return `${score.toFixed(fractionDigits)}/${WSI_DISPLAY_SCALE.toFixed(fractionDigits)}`
}

/**
 * Converte uma WsiClassification (snake_case usada no helper) para a chave
 * i18n correspondente (camelCase em messages/*.json -> wsi.classification.*).
 */
const I18N_KEY_BY_CLASSIFICATION: Record<WsiClassification, string> = {
  excepcional: 'excepcional',
  excelente: 'excelente',
  alto: 'alto',
  medio: 'medio',
  abaixo_da_media: 'abaixoDaMedia',
  regular: 'regular',
}

export function wsiClassificationI18nKey(classification: string): string {
  return I18N_KEY_BY_CLASSIFICATION[classification as WsiClassification] ?? 'medio'
}

/**
 * Wrapper canônico para a cor do score WSI no esquema 3-tier.
 * Substitui qualquer `getScoreColor(score, isWsi=true)` local.
 */
export function getWsiScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'text-lia-text-secondary'
  if (score >= WSI_VISUAL_3TIER.green) return 'text-status-success'
  if (score >= WSI_VISUAL_3TIER.yellow) return 'text-status-warning'
  return 'text-status-error'
}
