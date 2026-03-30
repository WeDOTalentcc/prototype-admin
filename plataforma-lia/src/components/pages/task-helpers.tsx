"use client"

// Camada 2 (componentes puros): Helpers de formatação e badges para TasksPage
// Sem estado próprio — apenas funções e componentes de apresentação

import React from "react"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Calendar, Search, AlertTriangle, AlertCircle, CheckCircle, Info } from "lucide-react"

// --- Helpers de estilo ---

export const getTaskPriorityStyle = (priority: 'high' | 'medium' | 'low') => {
  switch (priority) {
    case 'high': return { backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)' }
    case 'medium': return { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }
    case 'low': return { backgroundColor: 'var(--blue-50, #eff6ff)', color: 'var(--gray-800)' }
  }
}

export const getAlertSeverityStyle = (severity: 'high' | 'medium' | 'low') => {
  switch (severity) {
    case 'high': return { backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)' }
    case 'medium': return { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }
    case 'low': return { backgroundColor: 'var(--blue-50, #eff6ff)', color: 'var(--gray-800)' }
  }
}

export const getPriorityLabel = (priority: 'high' | 'medium' | 'low') => {
  switch (priority) {
    case 'high': return 'Alta'
    case 'medium': return 'Média'
    case 'low': return 'Baixa'
  }
}

export const getSeverityLabel = (severity: 'high' | 'medium' | 'low') => {
  switch (severity) {
    case 'high': return 'Alto'
    case 'medium': return 'Médio'
    case 'low': return 'Baixo'
  }
}

export const getTaskTypeIcon = (type: 'feedback' | 'entrevista' | 'sourcing') => {
  switch (type) {
    case 'feedback': return <MessageSquare className="w-3.5 h-3.5" />
    case 'entrevista': return <Calendar className="w-3.5 h-3.5" />
    case 'sourcing': return <Search className="w-3.5 h-3.5" />
  }
}

export const getAlertIcon = (type: string) => {
  switch (type) {
    case 'urgent': return <AlertTriangle className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
    case 'warning': return <AlertCircle className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
    case 'success': return <CheckCircle className="w-4 h-4" style={{color: 'var(--gray-800)'}} />
    default: return <Info className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
  }
}

export const getAlertStyle = (type: string) => {
  switch (type) {
    case 'urgent': return { backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)' }
    case 'warning': return { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }
    case 'success': return { backgroundColor: 'var(--green-50, #f0fdf4)', color: 'var(--gray-800)' }
    default: return { backgroundColor: 'var(--amber-50, #fffbeb)', color: 'var(--gray-500)' }
  }
}

export const getUrgencyBadge = (urgency: string, daysOpen: number) => {
  if (urgency === 'critical') return <Badge className="border-0 text-xs font-medium" style={{backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)'}}>🔴 Crítico</Badge>
  if (urgency === 'urgent') return <Badge className="border-0 text-xs font-semibold" style={{backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)'}}>⚠ Urgente</Badge>
  if (daysOpen > 30) return <Badge className="border-0 text-xs font-medium" style={{backgroundColor: 'var(--blue-50, #eff6ff)', color: 'var(--gray-800)'}}>⏰ Atenção</Badge>
  return <Badge className="border-0 text-xs" style={{backgroundColor: 'var(--green-50, #f0fdf4)', color: 'var(--gray-800)'}}>✓ Normal</Badge>
}

export const getConversionRate = (from: number, to: number) => {
  if (from === 0) return 0
  return Math.round((to / from) * 100)
}

export const getConversionStyle = (rate: number) => {
  return { color: 'var(--gray-800)' }
}

export const getRequestStatusBadge = (status: string) => {
  switch (status) {
    case 'draft': return { label: 'Rascunho', color: 'border-0', style: { backgroundColor: 'var(--amber-50, #fffbeb)', color: 'var(--gray-500)' }, icon: '📝' }
    case 'pending_approval': return { label: 'Aguardando Aprovação', color: 'border-0 font-medium', style: { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }, icon: '⏳' }
    case 'in_review': return { label: 'Em Revisão', color: 'border-0 font-medium', style: { backgroundColor: 'var(--blue-50, #eff6ff)', color: 'var(--gray-800)' }, icon: '👁️' }
    case 'requires_changes': return { label: 'Requer Alterações', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }, icon: '✏️' }
    case 'approved': return { label: 'Aprovado', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--green-50, #f0fdf4)', color: 'var(--gray-800)' }, icon: '✅' }
    case 'rejected': return { label: 'Rejeitado', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)' }, icon: '❌' }
    case 'published': return { label: 'Publicado', color: 'border-0 font-medium', style: { backgroundColor: 'var(--gray-950)', color: 'var(--gray-50)' }, icon: '🚀' }
    default: return { label: status, color: 'border-0', style: { backgroundColor: 'var(--amber-50, #fffbeb)', color: 'var(--gray-500)' }, icon: '•' }
  }
}

export const getRequestPriorityBadge = (priority: string) => {
  switch (priority) {
    case 'critical': return { label: 'Crítico', color: 'border-0 font-medium', style: { backgroundColor: 'var(--pink-50, #fdf2f8)', color: 'var(--gray-800)' }, icon: '🔴' }
    case 'high': return { label: 'Alta', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--yellow-50, #fefce8)', color: 'var(--gray-800)' }, icon: '🟠' }
    case 'medium': return { label: 'Média', color: 'border-0 font-medium', style: { backgroundColor: 'var(--blue-50, #eff6ff)', color: 'var(--gray-800)' }, icon: '🟡' }
    case 'low': return { label: 'Baixa', color: 'border-0', style: { backgroundColor: 'var(--green-50, #f0fdf4)', color: 'var(--gray-800)' }, icon: '🟢' }
    default: return { label: priority, color: 'border-0', style: { backgroundColor: 'var(--amber-50, #fffbeb)', color: 'var(--gray-500)' }, icon: '•' }
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
    default: return 'var(--gray-400)'
  }
}
