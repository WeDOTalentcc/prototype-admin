"use client"

import { useMemo } from "react"

export interface DashboardCandidate {
  liaScore?: number
  skillsMatch?: number
  contactStatus?: string
  liaStatus?: string
  triageComplete?: boolean
  triageData?: {
    mobility?: string
    salary?: string
    interest?: string
    [key: string]: unknown
  }
  status?: string
  stage?: string
  approvalPending?: boolean
  feedbackSent?: boolean
  source?: string
  [key: string]: unknown
}

export interface TimeSeriesPoint {
  date: string
  value: number
}

export interface StageBreakdownItem {
  stage: string
  count: number
  total: number
  rate: number
  avgTime: number
  color: string
  bgColor: string
}

export interface SourceMetricItem {
  source: string
  count: number
  contacted: number
  avgScore: number
  conversionRate: number
}

export interface CandidateStatusItem {
  status: string
  count: number
  percentage: number
}

export const generateTimeSeriesData = (currentValue: number, volatility: number = 5): TimeSeriesPoint[] => {
  const days = ['7d', '6d', '5d', '4d', '3d', '2d', 'Hoje']
  return days.map((day, index) => ({
    date: day,
    value: Math.max(0, Math.min(100,
      currentValue + (Math.random() - 0.5) * volatility * (7 - index)
    ))
  }))
}

export function useLiaMetricsData(candidates: DashboardCandidate[]) {
  return useMemo(() => {
    const totalCandidates = candidates.length

    const contacted = candidates.filter(c => c.contactStatus !== 'não contatado').length
    const contactRate = totalCandidates > 0 ? (contacted / totalCandidates) * 100 : 0

    const triageStarted = candidates.filter(c =>
      c.liaStatus === 'em_contato' ||
      c.liaStatus === 'triagem_completa' ||
      c.triageComplete
    ).length
    const triageCompleted = candidates.filter(c =>
      c.liaStatus === 'triagem_completa' ||
      c.triageComplete
    ).length
    const triageConversionRate = contacted > 0 ? (triageCompleted / contacted) * 100 : 0

    const triageApproved = candidates.filter(c => {
      if (!c.triageComplete || !c.triageData) return false
      return c.triageData.mobility === 'OK' &&
             c.triageData.salary !== 'Acima do budget' &&
             c.triageData.interest !== 'Baixo'
    }).length
    const triageApprovalRate = triageCompleted > 0 ? (triageApproved / triageCompleted) * 100 : 0

    const interviewScheduled = candidates.filter(c =>
      c.status === 'Entrevista marcada' ||
      c.status === 'Entrevista agendada' ||
      c.stage === 'Entrevista'
    ).length
    const interviewConversionRate = triageApproved > 0 ? (interviewScheduled / triageApproved) * 100 : 0

    const avgLiaScore = candidates.length > 0
      ? candidates.reduce((sum, c) => sum + (c.liaScore ?? 0), 0) / candidates.length
      : 0
    const avgSkillsMatch = candidates.length > 0
      ? candidates.reduce((sum, c) => sum + (c.skillsMatch ?? 0), 0) / candidates.length
      : 0

    const avgTimeContact = 1.5
    const avgTimeTriage = 2.8
    const avgTimeInterview = 5.2
    const avgTimeTotal = avgTimeContact + avgTimeTriage + avgTimeInterview

    const pendingApproval = candidates.filter(c => c.approvalPending).length
    const pendingFeedback = candidates.filter(c =>
      c.status === 'Reprovado' && !c.feedbackSent
    ).length

    const stageBreakdown: StageBreakdownItem[] = [
      {
        stage: 'Contato Inicial',
        count: contacted,
        total: totalCandidates,
        rate: contactRate,
        avgTime: avgTimeContact,
        color: 'text-lia-text-secondary',
        bgColor: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
      },
      {
        stage: 'Triagem Iniciada',
        count: triageStarted,
        total: contacted,
        rate: contacted > 0 ? (triageStarted / contacted) * 100 : 0,
        avgTime: avgTimeTriage,
        color: 'text-lia-text-primary',
        bgColor: 'bg-lia-bg-secondary dark:bg-lia-bg-secondary'
      },
      {
        stage: 'Triagem Completa',
        count: triageCompleted,
        total: triageStarted,
        rate: triageConversionRate,
        avgTime: avgTimeTriage,
        color: 'text-status-success',
        bgColor: 'bg-status-success/10'
      },
      {
        stage: 'Triagem Aprovada',
        count: triageApproved,
        total: triageCompleted,
        rate: triageApprovalRate,
        avgTime: 0.5,
        color: 'text-status-success',
        bgColor: 'bg-status-success/10'
      },
      {
        stage: 'Entrevista Agendada',
        count: interviewScheduled,
        total: triageApproved,
        rate: interviewConversionRate,
        avgTime: avgTimeInterview,
        color: 'text-wedo-purple-text',
        bgColor: 'bg-wedo-purple/10'
      }
    ]

    const funnelStages = stageBreakdown.map(stage => ({
      ...stage,
      stage: stage.stage.replace('Triagem', 'Triagem Iniciada')
    }))

    const scoreDistribution: TimeSeriesPoint[] = [
      { date: '0-2', value: candidates.filter(c => (c.liaScore ?? 0) >= 0 && (c.liaScore ?? 0) < 2).length },
      { date: '2-4', value: candidates.filter(c => (c.liaScore ?? 0) >= 2 && (c.liaScore ?? 0) < 4).length },
      { date: '4-6', value: candidates.filter(c => (c.liaScore ?? 0) >= 4 && (c.liaScore ?? 0) < 6).length },
      { date: '6-8', value: candidates.filter(c => (c.liaScore ?? 0) >= 6 && (c.liaScore ?? 0) < 8).length },
      { date: '8-10', value: candidates.filter(c => (c.liaScore ?? 0) >= 8 && (c.liaScore ?? 0) <= 10).length },
    ]

    const sourceMetricsObj = candidates.reduce((acc, c) => {
      const source = c.source
      if (!source) return acc
      if (!acc[source]) {
        acc[source] = { source, count: 0, contacted: 0, avgScore: 0 }
      }
      acc[source].count += 1
      acc[source].contacted += c.contactStatus !== 'não contatado' ? 1 : 0
      acc[source].avgScore = (acc[source].avgScore * (acc[source].count - 1) + (c.liaScore ?? 0)) / acc[source].count
      return acc
    }, {} as Record<string, { source: string; count: number; contacted: number; avgScore: number }>)

    const sourceMetrics: SourceMetricItem[] = Object.values(sourceMetricsObj).map((source) => ({
      ...source,
      conversionRate: source.count > 0 ? (source.contacted / source.count) * 100 : 0
    }))

    const candidateStatusBreakdown: CandidateStatusItem[] = [
      { status: 'Contato Inicial', count: contacted, percentage: (contacted / totalCandidates) * 100 },
      { status: 'Triagem Iniciada', count: triageStarted, percentage: (triageStarted / totalCandidates) * 100 },
      { status: 'Triagem Completa', count: triageCompleted, percentage: (triageCompleted / totalCandidates) * 100 },
      { status: 'Triagem Aprovada', count: triageApproved, percentage: (triageApproved / totalCandidates) * 100 },
      { status: 'Entrevista Agendada', count: interviewScheduled, percentage: (interviewScheduled / totalCandidates) * 100 },
      { status: 'Reprovado', count: candidates.filter(c => c.status === 'Reprovado').length, percentage: (candidates.filter(c => c.status === 'Reprovado').length / totalCandidates) * 100 },
    ]

    return {
      totalCandidates,
      contacted,
      contactRate,
      triageStarted,
      triageCompleted,
      triageConversionRate,
      triageApproved,
      triageApprovalRate,
      interviewScheduled,
      interviewConversionRate,
      avgLiaScore,
      avgSkillsMatch,
      avgTimeContact,
      avgTimeTriage,
      avgTimeInterview,
      avgTimeTotal,
      pendingApproval,
      pendingFeedback,
      stageBreakdown,
      funnelStages,
      scoreDistribution,
      sourceMetrics,
      candidateStatusBreakdown,
    }
  }, [candidates])
}

export type LiaMetricsData = ReturnType<typeof useLiaMetricsData>
