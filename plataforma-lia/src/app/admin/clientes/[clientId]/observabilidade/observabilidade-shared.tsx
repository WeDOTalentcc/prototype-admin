"use client"

import { Loader2 } from "lucide-react"

export interface ComplianceFramework {
  id: string
  name: string
  shortName: string
  progress: number
  controlsImplemented: number
  controlsPartial: number
  controlsNotImplemented: number
  totalControls: number
  lastAudit?: string
  nextReview?: string
}

export interface ComplianceControl {
  id: string
  code: string
  name: string
  framework: string
  status: 'implemented' | 'partial' | 'not_implemented'
  lastChecked: string
  owner?: string
}

export interface AIDecision {
  id: string
  timestamp: string
  agent: string
  decisionType: string
  candidateId: string
  candidateName: string
  outcome: string
  overridden: boolean
  explainability: boolean
  confidence: number
}

export interface BiasAlert {
  id: string
  type: string
  description: string
  severity: 'high' | 'medium' | 'low'
  detectedAt: string
  resolved: boolean
}

export const statusColors: Record<string, string> = {
  implemented: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success',
  partial: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  not_implemented: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error',
  in_progress: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  not_started: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-primary/30 dark:text-lia-text-primary',
  verified: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary',
  not_applicable: 'bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-primary/30 dark:text-lia-text-secondary'
}

export const statusLabels: Record<string, string> = {
  implemented: 'Implementado',
  partial: 'Parcial',
  not_implemented: 'Não Implementado',
  in_progress: 'Em Progresso',
  not_started: 'Não Iniciado',
  verified: 'Verificado',
  not_applicable: 'N/A'
}

export function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary`} />
}
