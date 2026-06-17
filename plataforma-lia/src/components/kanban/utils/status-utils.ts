import type { ReactNode } from 'react'

export interface LiaAlert {
  type: 'urgent' | 'action' | 'warning'
  icon: ReactNode
  label: string
  color: string
}

export interface UrgencyLevel {
  level: 'excellent' | 'great' | 'good' | 'average' | 'below' | 'low'
  label: string
  color: string
}

export function getUrgencyLevel(score: number): UrgencyLevel {
  if (score >= 90) {
    return {
      level: 'excellent',
      label: 'Excelente',
      color: 'text-lia-text-primary'
    }
  }
  if (score >= 80) {
    return {
      level: 'great',
      label: 'Ótimo',
      color: 'text-lia-text-primary'
    }
  }
  if (score >= 70) {
    return {
      level: 'good',
      label: 'Bom',
      color: 'text-lia-text-primary'
    }
  }
  if (score >= 60) {
    return {
      level: 'average',
      label: 'Médio',
      color: 'text-lia-text-secondary'
    }
  }
  if (score >= 50) {
    return {
      level: 'below',
      label: 'Abaixo',
      color: 'text-lia-text-primary'
    }
  }
  return {
    level: 'low',
    label: 'Baixo',
    color: 'text-lia-text-secondary'
  }
}

export function getScoreColor(score: number | null | undefined): string {
  if (score == null) return 'bg-lia-bg-tertiary'
  if (score >= 80) return 'bg-status-success/15 text-status-success'
  if (score >= 60) return 'bg-status-warning/15 text-status-warning'
  if (score >= 40) return 'bg-wedo-orange/15 text-wedo-orange-text'
  return 'bg-status-error/15 text-status-error'
}

export function getScoreBgColor(score: number | null | undefined): string {
  if (score == null) return 'var(--lia-border-subtle)'
  if (score >= 80) return 'var(--status-success)'
  if (score >= 60) return 'var(--status-warning)'
  if (score >= 40) return 'var(--lia-text-tertiary)'
  return 'var(--lia-text-secondary)'
}

export function getStageColor(stageName: string): string {
  const stage = stageName?.toLowerCase() || ''

  if (stage === 'funil' || stage === 'sourcing') return 'var(--lia-border-subtle)'
  if (stage === 'triagem' || stage === 'screening') return 'var(--lia-border-default)'
  if (stage.includes('entrevista') || stage.includes('interview')) return 'var(--lia-text-tertiary)'
  if (stage === 'final' || stage === 'offer') return 'var(--lia-text-secondary)'
  if (stage === 'aprovados' || stage === 'hired') return 'var(--status-success)'
  if (stage === 'reprovados' || stage === 'rejected') return 'var(--lia-border-subtle)'
  
  return 'var(--lia-border-subtle)'
}

export function calculateGeneralScore(candidate: {
  liaScore?: number | null
  score?: number | null
  fitScore?: number | null
  skillsMatch?: number | null
  technicalTestScore?: number | null
  englishTestScore?: number | null
}): number {
  const scores: number[] = []
  
  if (candidate.liaScore != null) scores.push(candidate.liaScore)
  else if (candidate.score != null) scores.push(candidate.score)
  
  if (candidate.fitScore != null) scores.push(candidate.fitScore)
  else if (candidate.skillsMatch != null) scores.push(candidate.skillsMatch)
  
  if (candidate.technicalTestScore != null) scores.push(candidate.technicalTestScore)
  if (candidate.englishTestScore != null) scores.push(candidate.englishTestScore)
  
  if (scores.length === 0) return 0
  
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
}

export function formatScoreDisplay(score: number | null | undefined, decimals: number = 0): string {
  if (score == null) return '—'
  return `${Math.round(score * Math.pow(10, decimals)) / Math.pow(10, decimals)}%`
}

export const URGENCY_ICON_COLORS = {
  excellent: 'text-lia-text-primary',
  great: 'text-lia-text-primary',
  good: 'text-lia-text-primary',
  average: 'text-lia-text-secondary',
  below: 'text-lia-text-primary',
  low: 'text-lia-text-secondary'
} as const

export const ALERT_COLORS = {
  urgent: 'bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg dark:border-lia-border-subtle',
  action: 'bg-lia-interactive-active text-lia-text-primary border-lia-border-default dark:border-lia-border-strong',
  warning: 'bg-lia-border-default text-lia-text-primary border-lia-border-medium dark:border-lia-border-medium',
  pending: 'bg-lia-interactive-active text-lia-text-primary border-lia-border-default dark:border-lia-border-medium'
} as const
