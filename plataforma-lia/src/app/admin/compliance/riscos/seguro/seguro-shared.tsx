"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Clock } from "lucide-react"

export const BCB_COVERAGE_TYPES = [
  { type: 'data_breach', name: 'Violação de Dados', article: 'Art. 3º, I', description: 'Cobertura para violação e vazamento de dados pessoais' },
  { type: 'ransomware', name: 'Extorsão Cibernética', article: 'Art. 3º, II', description: 'Pagamento de resgate e custos de ransomware' },
  { type: 'business_interruption', name: 'Interrupção de Negócios', article: 'Art. 3º, III', description: 'Perdas por interrupção de operações devido a incidentes cyber' },
  { type: 'regulatory_defense', name: 'Defesa Regulatória', article: 'Art. 3º, IV', description: 'Custos legais e defesa junto a órgãos reguladores' },
  { type: 'crisis_management', name: 'Gestão de Crise', article: 'Art. 3º, V', description: 'Comunicação de crise e gestão de reputação' },
  { type: 'forensic_investigation', name: 'Investigação Forense', article: 'Art. 3º, VI', description: 'Custos de investigação e análise forense' },
  { type: 'notification_costs', name: 'Custos de Notificação', article: 'Art. 3º, VII', description: 'Notificação de titulares e autoridades' },
  { type: 'third_party_liability', name: 'Responsabilidade Civil', article: 'Art. 3º, VIII', description: 'Responsabilidade civil perante terceiros' },
]

export const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

export const getStatusBadge = (status: string) => {
  switch (status) {
    case 'active':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Ativo
      </Badge>
    case 'expired':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">
        Expirado
      </Badge>
    case 'pending':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
        <Clock className="w-3 h-3 mr-1" />
        Pendente
      </Badge>
    case 'cancelled':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
        Cancelado
      </Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export const getClaimStatusBadge = (status: string) => {
  switch (status) {
    case 'open':
 return <Badge className="text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-lia-bg-tertiary">Aberto</Badge>
    case 'under_review':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Em Análise</Badge>
    case 'approved':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Aprovado</Badge>
    case 'denied':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Negado</Badge>
    case 'paid':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Pago</Badge>
    case 'closed':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">Encerrado</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export const getAlertSeverityStyle = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { bg: 'var(--status-error-bg)', border: 'var(--status-error)', icon: 'text-status-error' }
    case 'high':
      return { bg: 'var(--status-warning-bg)', border: 'var(--status-warning)', icon: 'text-status-warning' }
    case 'medium':
      return { bg: 'var(--lia-interactive-active)', border: 'var(--lia-border-subtle)', icon: 'text-lia-text-secondary dark:text-lia-text-tertiary' }
    default:
      return { bg: 'var(--lia-bg-secondary)', border: 'var(--lia-text-tertiary)', icon: 'text-lia-text-secondary' }
  }
}
