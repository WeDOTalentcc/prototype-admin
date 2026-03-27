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
      color: 'text-gray-950 dark:text-gray-50'
    }
  }
  if (score >= 80) {
    return {
      level: 'great',
      label: 'Ótimo',
      color: 'text-gray-800 dark:text-gray-200'
    }
  }
  if (score >= 70) {
    return {
      level: 'good',
      label: 'Bom',
      color: 'text-gray-800 dark:text-gray-200'
    }
  }
  if (score >= 60) {
    return {
      level: 'average',
      label: 'Médio',
      color: 'text-gray-600 dark:text-gray-400'
    }
  }
  if (score >= 50) {
    return {
      level: 'below',
      label: 'Abaixo',
      color: 'text-gray-800 dark:text-gray-200'
    }
  }
  return {
    level: 'low',
    label: 'Baixo',
    color: 'text-gray-600 dark:text-gray-600'
  }
}

export function getScoreColor(score: number | null | undefined): string {
  if (score == null) return 'bg-gray-100'
  if (score >= 80) return 'bg-green-100 text-green-800'
  if (score >= 60) return 'bg-yellow-100 text-yellow-800'
  if (score >= 40) return 'bg-orange-100 text-orange-800'
  return 'bg-red-100 text-red-800'
}

export function getScoreBgColor(score: number | null | undefined): string {
  if (score == null) return 'var(--gray-200)'
  if (score >= 80) return 'var(--status-success)'
  if (score >= 60) return 'var(--status-warning)'
  if (score >= 40) return 'var(--gray-400)'
  return 'var(--gray-600)'
}

export function getStageColor(stageName: string): string {
  const stage = stageName?.toLowerCase() || ''

  if (stage === 'funil' || stage === 'sourcing') return 'var(--gray-200)'
  if (stage === 'triagem' || stage === 'screening') return 'var(--gray-300)'
  if (stage.includes('entrevista') || stage.includes('interview')) return 'var(--gray-400)'
  if (stage === 'final' || stage === 'offer') return 'var(--gray-600)'
  if (stage === 'aprovados' || stage === 'hired') return 'var(--status-success)'
  if (stage === 'reprovados' || stage === 'rejected') return 'var(--gray-200)'
  
  return 'var(--gray-200)'
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
  excellent: 'text-gray-950 dark:text-gray-50',
  great: 'text-gray-800 dark:text-gray-200',
  good: 'text-gray-800 dark:text-gray-200',
  average: 'text-gray-600 dark:text-gray-400',
  below: 'text-gray-800 dark:text-gray-200',
  low: 'text-gray-600 dark:text-gray-600'
} as const

export const ALERT_COLORS = {
  urgent: 'bg-gray-900 text-white border-gray-900 dark:bg-gray-200 dark:text-gray-950 dark:border-gray-200',
  action: 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700',
  warning: 'bg-gray-300 text-gray-950 border-gray-400 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600',
  pending: 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600'
} as const
