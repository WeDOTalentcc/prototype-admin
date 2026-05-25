"use client"

// Camada 2 (componentes puros): Helpers de formatação e badges para TasksPage
// Sem estado próprio — apenas funções e componentes de apresentação

import React from"react"
import { Chip } from"@/components/ui/chip"
import { MessageSquare, Calendar, Search, AlertTriangle, AlertCircle, CheckCircle, Info } from"lucide-react"

// --- Helpers de estilo ---

export const getTaskPriorityStyle = (priority: 'high' | 'medium' | 'low') => {
  switch (priority) {
    case 'high': return ''
    case 'medium': return ''
    case 'low': return ''
  }
}

export const getAlertSeverityStyle = (severity: 'critical' | 'high' | 'medium' | 'low' | 'info') => {
  switch (severity) {
    case 'critical': return ''
    case 'high': return ''
    case 'medium': return ''
    case 'low': return ''
  }
}

export const getPriorityLabel = (priority: 'high' | 'medium' | 'low') => {
  switch (priority) {
    case 'high': return 'Alta'
    case 'medium': return 'Média'
    case 'low': return 'Baixa'
  }
}

export const getSeverityLabel = (severity: 'critical' | 'high' | 'medium' | 'low' | 'info') => {
  switch (severity) {
    case 'critical': return 'Crítico'
    case 'high': return 'Alto'
    case 'medium': return 'Médio'
    case 'low': return 'Baixo'
    case 'info': return 'Info'
  }
}

export const getTaskTypeIcon = (type: 'feedback' | 'entrevista' | 'sourcing') => {
  switch (type) {
    case 'feedback': return <MessageSquare className="w-3.5 h-3.5 text-violet-500" />
    case 'entrevista': return <Calendar className="w-3.5 h-3.5 text-emerald-500" />
    case 'sourcing': return <Search className="w-3.5 h-3.5 text-wedo-cyan" />
  }
}

export const getAlertIcon = (type: string) => {
  switch (type) {
    case 'urgent': return <AlertTriangle className="w-4 h-4 text-rose-500" />
    case 'warning': return <AlertCircle className="w-4 h-4 text-amber-500" />
    case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />
    default: return <Info className="w-4 h-4 text-wedo-cyan" />
  }
}

export const getAlertStyle = (type: string) => {
  switch (type) {
    case 'urgent': return 'bg-lia-brand-primary-light text-lia-text-primary'
    case 'warning': return 'bg-wedo-amber-light text-lia-text-primary'
    case 'success': return 'bg-wedo-green-light text-lia-text-primary'
    default: return 'bg-wedo-amber-light text-lia-text-secondary'
  }
}

export const getAlertColor = (type: string) => {
  switch (type) {
    case 'urgent': return 'bg-lia-brand-primary-light'
    case 'warning': return 'bg-wedo-amber-light'
    case 'success': return 'bg-wedo-green-light'
    default: return 'bg-wedo-amber-light'
  }
}

export const getUrgencyBadge = (urgency: string, daysOpen: number) => {
  if (urgency === 'critical') return <Chip variant="danger" className="font-medium">Crítico</Chip>
  if (urgency === 'urgent') return <Chip variant="warning">Urgente</Chip>
  if (daysOpen > 30) return <Chip variant="info" className="font-medium">Atenção</Chip>
  return <Chip variant="success">Normal</Chip>
}

export const getConversionRate = (from: number, to: number) => {
  if (from === 0) return 0
  return Math.round((to / from) * 100)
}

export const getConversionStyle = (rate: number) => {
  if (rate >= 75) return 'text-emerald-600 font-semibold'
  if (rate >= 40) return 'text-amber-600'
  return 'text-rose-600'
}

export const getRequestStatusBadge = (status: string) => {
  switch (status) {
    case 'draft': return { label: 'Rascunho', color: 'border-0', className: 'bg-wedo-amber-light text-lia-text-secondary', icon: '📝' }
    case 'pending_approval': return { label: 'Aguardando Aprovação', color: 'border-0 font-medium', className: 'bg-wedo-amber-light text-lia-text-primary', icon: '⏳' }
    case 'in_review': return { label: 'Em Revisão', color: 'border-0 font-medium', className: 'bg-lia-info-light text-lia-text-primary', icon: '👁️' }
    case 'requires_changes': return { label: 'Requer Alterações', color: 'border-0 font-semibold', className: 'bg-wedo-amber-light text-lia-text-primary', icon: '✏️' }
    case 'approved': return { label: 'Aprovado', color: 'border-0 font-semibold', className: 'bg-wedo-green-light text-lia-text-primary', icon: '✅' }
    case 'rejected': return { label: 'Rejeitado', color: 'border-0 font-semibold', className: 'bg-lia-brand-primary-light text-lia-text-primary', icon: '❌' }
    case 'published': return { label: 'Publicado', color: 'border-0 font-medium', className: 'bg-lia-btn-primary-bg text-lia-text-inverse', icon: '🚀' }
    default: return { label: status, color: 'border-0', className: 'bg-wedo-amber-light text-lia-text-secondary', icon: '•' }
  }
}

export const getRequestPriorityBadge = (priority: string) => {
  switch (priority) {
    case 'critical': return { label: 'Crítico', color: 'border-0 font-medium', className: 'bg-lia-brand-primary-light text-lia-text-primary', icon: '🔴' }
    case 'high': return { label: 'Alta', color: 'border-0 font-semibold', className: 'bg-wedo-amber-light text-lia-text-primary', icon: '🟠' }
    case 'medium': return { label: 'Média', color: 'border-0 font-medium', className: 'bg-lia-info-light text-lia-text-primary', icon: '🟡' }
    case 'low': return { label: 'Baixa', color: 'border-0', className: 'bg-wedo-green-light text-lia-text-primary', icon: '🟢' }
    default: return { label: priority, color: 'border-0', className: 'bg-wedo-amber-light text-lia-text-secondary', icon: '•' }
  }
}

export const getWorkModelLabel = (model: string) => {
  switch (model) {
    case 'remote': return { label: 'Remoto', icon: '🏠' }
    case 'hybrid': return { label: 'Híbrido', icon: '🔄' }
    case 'onsite': return { label: 'Presencial', icon: '🏢' }
    default: return { label: model, icon: '•' }
  }
}

export const getTaskIconBackground = (taskType: string) => {
  switch (taskType) {
    case 'entrevista': return 'var(--status-success)'
    default: return 'var(--lia-text-tertiary)'
  }
}
