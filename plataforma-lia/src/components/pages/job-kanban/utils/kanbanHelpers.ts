import React from "react"
import { Flag, CheckCircle, AlertCircle, Mail, Clock } from "lucide-react"
import type { DynamicStage } from "./kanbanStageUtils"

interface KanbanCandidateBase {
  skillsMatch?: number
  fitScore?: number
  liaScore?: number
  score?: number
  technicalTestScore?: number
  englishTestScore?: number
  approvalPending?: boolean
  needsAction?: boolean
  liaStatus?: string
  stage?: string
  triageComplete?: boolean
  status?: string
  feedbackStatus?: string
  warnings?: number
  name: string
  role?: string
  location?: string
  currentCompany?: string
  id: string | number
}

export const calculateNotaLiaGeral = (candidate: KanbanCandidateBase) => {
  const scoreLiaCV = candidate.skillsMatch || candidate.fitScore || 0
  const scoreLiaTriagem = (candidate.liaScore || candidate.score || 0)
  const scoreTesteTecnico = candidate.technicalTestScore || 0
  const scoreTesteIngles = candidate.englishTestScore || 0

  const notaBase = (
    (scoreLiaCV / 100 * 25) +
    (scoreLiaTriagem / 100 * 30) +
    (scoreTesteTecnico / 100 * 25) +
    (scoreTesteIngles / 100 * 20)
  )

  let bonusUrgencia = 0
  if (candidate.approvalPending && candidate.liaStatus === 'aguardando_aprovacao_contato') {
    bonusUrgencia = 10
  } else if (candidate.approvalPending && candidate.liaStatus === 'triagem_completa') {
    bonusUrgencia = 8
  } else if (candidate.approvalPending || candidate.needsAction) {
    bonusUrgencia = 5
  }

  let bonusEtapa = 0
  if (candidate.stage === 'Final') {
    bonusEtapa = 5
  } else if (candidate.stage === 'Entrevista') {
    bonusEtapa = 3
  }

  let bonusTriagem = 0
  if (candidate.triageComplete) {
    bonusTriagem = 5
  }

  const daysStuck = 0
  const penalizacaoTempo = Math.min(daysStuck * 0.5, 10)

  let notaFinal = notaBase + bonusUrgencia + bonusEtapa + bonusTriagem - penalizacaoTempo
  notaFinal = Math.max(0, Math.min(100, notaFinal))

  return Math.round(notaFinal * 10) / 10
}

export const getLiaAlerts = (candidate: KanbanCandidateBase) => {
  const alerts: Array<{
    type: string
    icon: React.ReactElement
    label: string
    color: string
  }> = []

  if (candidate.approvalPending || candidate.needsAction) {
    if (candidate.liaStatus === 'aguardando_aprovacao_contato') {
      alerts.push({
        type: 'urgent',
        icon: React.createElement(Flag, { className: "w-3.5 h-3.5" }),
        label: 'Aprovar Contato',
        color: 'bg-lia-interactive-active text-lia-text-primary border-lia-border-default dark:bg-lia-bg-tertiary dark:border-lia-border-default'
      })
    } else if (candidate.liaStatus === 'triagem_completa') {
      alerts.push({
        type: 'urgent',
        icon: React.createElement(CheckCircle, { className: "w-3 h-3" }),
        label: 'Aprovar Entrevista',
        color: 'bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg dark:bg-lia-bg-secondary dark:border-lia-border-medium'
      })
    } else if (candidate.needsAction) {
      alerts.push({
        type: 'urgent',
        icon: React.createElement(AlertCircle, { className: "w-3 h-3" }),
        label: 'Ação Necessária',
        color: 'bg-lia-border-medium text-lia-text-primary border-lia-border-medium dark:bg-lia-bg-elevated dark:border-lia-border-default'
      })
    }
  }

  if (candidate.status === 'reprovado' && candidate.feedbackStatus !== 'feedback_enviado') {
    alerts.push({
      type: 'action',
      icon: React.createElement(Mail, { className: "w-3 h-3" }),
      label: 'Enviar Feedback',
      color: 'bg-lia-interactive-active text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    })
  }

  if (candidate.warnings && candidate.warnings > 0) {
    alerts.push({
      type: 'warning',
      icon: React.createElement(Clock, { className: "w-3 h-3" }),
      label: `${candidate.warnings} Alerta${candidate.warnings > 1 ? 's' : ''}`,
      color: 'bg-lia-border-default text-lia-text-primary border-lia-border-medium dark:bg-lia-bg-tertiary dark:border-lia-border-default'
    })
  }

  return alerts
}

export const getFilteredAndSortedCandidates = (
  getAllCandidates: () => KanbanCandidateBase[],
  searchQuery: string,
  tableStageFilter: string[],
  tableSortColumn: string,
  tableSortDirection: 'asc' | 'desc'
) => {
  let candidates = getAllCandidates()

  if (searchQuery) {
    const query = searchQuery.toLowerCase()
    candidates = candidates.filter(candidate =>
      candidate.name.toLowerCase().includes(query) ||
      candidate.role?.toLowerCase().includes(query) ||
      candidate.location?.toLowerCase().includes(query) ||
      candidate.currentCompany?.toLowerCase().includes(query)
    )
  }

  if (tableStageFilter.length > 0) {
    candidates = candidates.filter(c => tableStageFilter.includes(c.stage as string))
  }

  candidates.sort((a, b) => {
    let aVal: string | number, bVal: string | number

    switch (tableSortColumn) {
      case 'name':
        aVal = a.name.toLowerCase()
        bVal = b.name.toLowerCase()
        break
      case 'scoreLiaTriagem':
        aVal = a.liaScore || a.score || 0
        bVal = b.liaScore || b.score || 0
        break
      case 'scoreLiaCV':
        aVal = a.skillsMatch || a.fitScore || 0
        bVal = b.skillsMatch || b.fitScore || 0
        break
      case 'testeTecnico':
        aVal = a.technicalTestScore || 0
        bVal = b.technicalTestScore || 0
        break
      case 'testeIngles':
        aVal = a.englishTestScore || 0
        bVal = b.englishTestScore || 0
        break
      case 'location':
        aVal = (a.location || '').toLowerCase()
        bVal = (b.location || '').toLowerCase()
        break
      case 'stage':
        aVal = (a.stage || '').toLowerCase()
        bVal = (b.stage || '').toLowerCase()
        break
      case 'notaLiaGeral':
        aVal = calculateNotaLiaGeral(a)
        bVal = calculateNotaLiaGeral(b)
        break
      default:
        aVal = calculateNotaLiaGeral(a)
        bVal = calculateNotaLiaGeral(b)
    }

    if (aVal < bVal) return tableSortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return tableSortDirection === 'asc' ? 1 : -1
    return 0
  })

  return candidates
}
