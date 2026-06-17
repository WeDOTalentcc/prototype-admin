export type ScoreLevel = 'excellent' | 'good' | 'satisfactory' | 'regular' | 'poor'

export interface ScoreClassification {
  level: ScoreLevel
  label: string
  colorClass: string
  colorVar: string
  bgVar: string
}

const PERCENTAGE_THRESHOLDS: { min: number; level: ScoreLevel; label: string }[] = [
  { min: 90, level: 'excellent', label: 'Excelente' },
  { min: 80, level: 'good', label: 'Muito Bom' },
  { min: 70, level: 'satisfactory', label: 'Bom' },
  { min: 60, level: 'regular', label: 'Satisfatório' },
  { min: 50, level: 'poor', label: 'Regular' },
]

const LEVEL_STYLES: Record<ScoreLevel, { colorClass: string; colorVar: string; bgVar: string }> = {
  excellent: {
    colorClass: 'text-status-success',
    colorVar: 'var(--status-success)',
    bgVar: 'var(--status-success-bg)',
  },
  good: {
    colorClass: 'text-status-success',
    colorVar: 'var(--status-success)',
    bgVar: 'var(--status-success-bg)',
  },
  satisfactory: {
    colorClass: 'text-lia-text-tertiary',
    colorVar: 'var(--lia-text-tertiary)',
    bgVar: 'var(--lia-bg-tertiary)',
  },
  regular: {
    colorClass: 'text-status-warning',
    colorVar: 'var(--status-warning)',
    bgVar: 'var(--status-warning-bg)',
  },
  poor: {
    colorClass: 'text-status-error',
    colorVar: 'var(--status-error)',
    bgVar: 'var(--status-error-bg)',
  },
}

export function classifyPercentageScore(score: number): ScoreClassification {
  for (const t of PERCENTAGE_THRESHOLDS) {
    if (score >= t.min) {
      return { level: t.level, label: t.label, ...LEVEL_STYLES[t.level] }
    }
  }
  return { level: 'poor', label: 'Insuficiente', ...LEVEL_STYLES.poor }
}

export function getPercentageScoreColorClass(score: number): string {
  if (score >= 80) return 'text-status-success'
  if (score >= 60) return 'text-status-warning'
  return 'text-status-error'
}

export function getPercentageScoreVar(score: number): string {
  if (score >= 80) return 'var(--status-success)'
  if (score >= 60) return 'var(--lia-text-tertiary)'
  if (score >= 40) return 'var(--status-warning)'
  return 'var(--status-error)'
}

export function getPercentageScoreBgVar(score: number): string {
  if (score >= 80) return 'var(--status-success-bg)'
  if (score >= 60) return 'var(--lia-bg-tertiary)'
  if (score >= 40) return 'var(--status-warning-bg)'
  return 'var(--status-error-bg)'
}

export function getPercentageScoreLabel(score: number): string {
  return classifyPercentageScore(score).label
}

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low'

export interface RiskClassification {
  level: RiskLevel
  label: string
  bg: string
  text: string
}

const RISK_THRESHOLDS: { min: number; level: RiskLevel; label: string; bg: string; text: string }[] = [
  { min: 12, level: 'critical', label: 'Crítico', bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
  { min: 8, level: 'high', label: 'Alto', bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
  { min: 4, level: 'medium', label: 'Médio', bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
]

export function classifyRiskScore(score: number): RiskClassification {
  for (const t of RISK_THRESHOLDS) {
    if (score >= t.min) {
      return { level: t.level, label: t.label, bg: t.bg, text: t.text }
    }
  }
  return { level: 'low', label: 'Baixo', bg: 'var(--status-success-bg)', text: 'var(--status-success)' }
}

export function isRiskCritical(score: number): boolean {
  return score >= RISK_THRESHOLDS[0].min
}

export type VendorGrade = 'A' | 'B' | 'C' | 'D' | 'F'

export interface VendorGradeClassification {
  bg: string
  text: string
  border: string
}

const VENDOR_GRADE_STYLES: Record<VendorGrade, VendorGradeClassification> = {
  A: { bg: 'bg-status-success/15', text: 'text-status-success', border: 'border-status-success/30' },
  B: { bg: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary dark:text-lia-text-tertiary', border: 'border-lia-border-default dark:border-lia-border-default' },
  C: { bg: 'bg-status-warning/15', text: 'text-status-warning', border: 'border-status-warning/30' },
  D: { bg: 'bg-wedo-orange/15', text: 'text-wedo-orange-text', border: 'border-wedo-orange/30' },
  F: { bg: 'bg-status-error/15', text: 'text-status-error', border: 'border-status-error/30' },
}

const DEFAULT_VENDOR_GRADE: VendorGradeClassification = {
  bg: 'bg-lia-bg-tertiary',
  text: 'text-lia-text-primary dark:text-lia-text-primary',
  border: 'border-lia-border-default',
}

export function classifyVendorGrade(grade: string): VendorGradeClassification {
  return VENDOR_GRADE_STYLES[grade as VendorGrade] ?? DEFAULT_VENDOR_GRADE
}

export function getEnglishLevel(score: number): string {
  if (score >= 90) return 'C2'
  if (score >= 80) return 'C1'
  if (score >= 70) return 'B2'
  if (score >= 60) return 'B1'
  if (score >= 40) return 'A2'
  return 'A1'
}

export function getJobScoreClass(score: number): string {
  if (score >= 80) return 'text-lia-text-secondary font-semibold'
  if (score >= 60) return 'text-lia-text-primary'
  return 'text-lia-text-secondary'
}

export function getJobDimensionColorClass(score: number): { bar: string; text: string } {
  if (score >= 80) return { bar: 'bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg', text: 'text-lia-text-secondary' }
  if (score >= 60) return { bar: 'bg-status-warning', text: 'text-status-warning' }
  return { bar: 'bg-status-error', text: 'text-status-error' }
}

export function getPredictionScoreColor(score: number): string {
  if (score >= 85) return 'text-status-success'
  if (score >= 70) return 'text-status-warning'
  return 'text-status-error'
}

export function getRiskBadgeColor(risk: string): string {
  switch (risk) {
    case 'Baixo':
    case 'low':
      return 'bg-status-success/10 text-status-success border-status-success/30'
    case 'Médio':
    case 'medium':
      return 'bg-status-warning/10 text-status-warning border-status-warning/30'
    case 'Alto':
    case 'high':
      return 'bg-status-error/10 text-status-error border-status-error/30'
    default:
      return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
  }
}

export function getCompareScoreAboveAvg(score: number, avgScore: number): boolean {
  return score >= avgScore
}

export type ScoreDomain = 'percentage' | 'risk' | 'prediction' | 'job' | 'english'

export interface UnifiedScoreResult {
  label: string
  colorClass: string
  colorVar: string
  bgVar: string
}

export function classifyScore(score: number, domain: ScoreDomain = 'percentage'): UnifiedScoreResult {
  switch (domain) {
    case 'risk': {
      const r = classifyRiskScore(score)
      return {
        label: r.label,
        colorClass: r.text.replace('var(--', 'text-').replace(')', ''),
        colorVar: r.text,
        bgVar: r.bg,
      }
    }
    case 'prediction': {
      const color = getPredictionScoreColor(score)
      return { label: score >= 85 ? 'Alto' : score >= 70 ? 'Médio' : 'Baixo', colorClass: color, colorVar: color.replace('text-', 'var(--').replace(/$/g, ')'), bgVar: '' }
    }
    case 'job': {
      const cls = getJobScoreClass(score)
      return { label: score >= 80 ? 'Excelente' : score >= 60 ? 'Bom' : 'Regular', colorClass: cls, colorVar: '', bgVar: '' }
    }
    case 'english': {
      const level = getEnglishLevel(score)
      const pct = classifyPercentageScore(score)
      return { label: level, colorClass: pct.colorClass, colorVar: pct.colorVar, bgVar: pct.bgVar }
    }
    case 'percentage':
    default: {
      const p = classifyPercentageScore(score)
      return { label: p.label, colorClass: p.colorClass, colorVar: p.colorVar, bgVar: p.bgVar }
    }
  }
}

export function getScoreBadgeClasses(score: number): string {
  if (score >= 80) return 'bg-status-success/15 text-status-success'
  if (score >= 60) return 'bg-status-warning/15 text-status-warning'
  return 'bg-status-error/15 text-status-error'
}
