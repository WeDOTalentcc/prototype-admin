import React from 'react'
import type { JobStatus, WSIBlock, WSIAutomaticMessage } from './jobsPageTypes'
// Audit P2-1/NEW-3: WSI_BLOCKS / WSI_AUTOMATIC_MESSAGES / formatMessageWithVariables
// agora vivem em @/constants/wsi-blocks (fonte canônica). Re-exportados aqui só
// para preservar imports legados.
import {
  WSI_BLOCKS as CANONICAL_WSI_BLOCKS,
  WSI_AUTOMATIC_MESSAGES as CANONICAL_WSI_AUTOMATIC_MESSAGES,
  formatMessageWithVariables as canonicalFormatMessageWithVariables,
} from '@/constants/wsi-blocks'

/** @deprecated Importe de `@/constants/wsi-blocks` diretamente. */
export const formatMessageWithVariables = canonicalFormatMessageWithVariables

export function getBloomComplexity(bloomLevel: number): { label: string; color: string } {
  if (bloomLevel <= 2) return { label: 'Baixa', color: 'bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20 dark:border-status-success/30' }
  if (bloomLevel <= 4) return { label: 'Média', color: 'bg-status-warning/10 text-status-warning border-status-warning/30 dark:bg-status-warning/20 dark:border-status-warning/30' }
  return { label: 'Alta', color: 'bg-status-error/10 text-status-error border-status-error/30 dark:bg-status-error/20 dark:text-status-error dark:border-status-error/30' }
}

const BLOOM_PT_BR: Record<number, string> = {
  1: 'Recordar',
  2: 'Compreender',
  3: 'Aplicar',
  4: 'Analisar',
  5: 'Avaliar',
  6: 'Criar',
}

const DREYFUS_PT_BR: Record<number, string> = {
  1: 'Iniciante',
  2: 'Básico',
  3: 'Intermediário',
  4: 'Avançado',
  5: 'Especialista',
}

export function getBloomLabelPTBR(level: number | string | null | undefined): string {
  if (!level) return ''
  const n = typeof level === 'string' ? parseInt(level, 10) : level
  return BLOOM_PT_BR[n] || BLOOM_PT_BR[Math.max(1, Math.min(6, n))] || ''
}

export function getDreyfusLabelPTBR(level: number | string | null | undefined): string {
  if (!level) return ''
  const n = typeof level === 'string' ? parseInt(level, 10) : level
  return DREYFUS_PT_BR[n] || DREYFUS_PT_BR[Math.max(1, Math.min(5, n))] || ''
}

export function getEstimatedTime(questionType: string): string {
  switch (questionType) {
    case 'yes_no': return '~30s'
    case 'single_choice': return '~1 min'
    case 'multiple_choice': return '~1 min'
    case 'scale': return '~45s'
    case 'open': default: return '~2-3 min'
  }
}

export function getStatusColor(status: JobStatus): string {
  const statusColors: Record<JobStatus, string> = {
    'Ativa': 'var(--status-success)',
    'Aprovada': 'var(--status-success)',
    'Aguardando aprovação': 'var(--status-warning)',
    'Reaberta': 'var(--status-warning)',
    'Paralisada': 'var(--lia-text-tertiary)',
    'Interna': 'var(--lia-border-default)',
    'Fechada (preenchida)': 'var(--lia-text-secondary)',
    'Fechada (expirada)': 'var(--lia-text-tertiary)',
    'Cancelada': 'var(--status-error)',
    'Rascunho': 'var(--lia-border-subtle)',
    'Arquivada': 'var(--lia-border-subtle)',
    'Concluída': 'color-mix(in srgb, var(--wedo-purple) 10%, transparent)'
  }
  return statusColors[status] || 'var(--lia-border-subtle)'
}

export const priorityColors = {
  "alta": "bg-status-error/10 text-status-error dark:text-status-error",
  "média": "bg-lia-bg-secondary text-lia-text-primary",
  "baixa": "bg-lia-bg-secondary text-lia-text-primary"
}

/** @deprecated Importe de `@/constants/wsi-blocks` diretamente. */
export const WSI_BLOCKS: WSIBlock[] = CANONICAL_WSI_BLOCKS as unknown as WSIBlock[]

const _LEGACY_WSI_BLOCKS_REMOVED: WSIBlock[] = [
  { 
    id: 0, 
    name: 'Abordagem Inicial', 
    description: 'Template WhatsApp pré-aprovado',
    duration: '< 1 min', 
    editable: false,
    type: 'template'
  },
  { 
    id: 1, 
    name: 'Apresentação da Oportunidade', 
    description: 'Pitch conversacional com detalhes da vaga',
    duration: '3 min', 
    editable: false,
    type: 'presentation'
  },
  { 
    id: 2, 
    name: 'Perguntas Padrão da Empresa', 
    description: 'Perguntas configuradas pela empresa (incluindo elegibilidade)',
    duration: '3 min', 
    editable: true,
    type: 'company'
  },
  {
    id: 3,
    name: 'Competências Técnicas',
    description: 'Skills com pesos e rubricas automáticas',
    duration: '5 min',
    editable: true,
    type: 'technical'
  },
  {
    id: 4,
    name: 'Competências Comportamentais e Fit',
    description: 'Perguntas situacionais com follow-ups e aderência cultural',
    duration: '4 min',
    editable: true,
    type: 'situational'
  },
  { 
    id: 5, 
    name: 'Resultado e Encerramento', 
    description: 'Índice WSI automático e feedback',
    duration: '3 min', 
    editable: false,
    type: 'result'
  }
]

/** @deprecated Importe de `@/constants/wsi-blocks` diretamente. */
export const WSI_AUTOMATIC_MESSAGES: Record<number, WSIAutomaticMessage> =
  CANONICAL_WSI_AUTOMATIC_MESSAGES as Record<number, WSIAutomaticMessage>

// P3-1 (rev. 17): código morto _LEGACY_* removido — fonte canônica em
// `@/constants/wsi-blocks`. i18n via next-intl deferido para task dedicada.

export const STATUS_ORDER = [
  'Ativa',
  'Aprovada', 
  'Aguardando aprovação',
  'Reaberta',
  'Paralisada',
  'Interna',
  'Rascunho',
  'Fechada (preenchida)',
  'Fechada (expirada)',
  'Cancelada',
  'Concluída',
  'Arquivada'
] as const

export const SEARCH_TEMPLATES = [
  "Vagas Tech Sênior",
  "Vagas Design",
  "Vagas Remotas",
  "Vagas Urgentes",
  "Vagas Júnior",
  "Vagas Product Manager",
  "Vagas Data Science",
  "Vagas DevOps",
  "Vagas Startup",
  "Vagas Enterprise"
]

export const JOBS_COLUMN_CONFIG: Record<string, { label: string; sortable: boolean; align: 'left' | 'center' | 'right' }> = {
  checkbox: { label: '', sortable: false, align: 'center' },
  id: { label: 'ID', sortable: true, align: 'left' },
  vaga: { label: 'Vaga', sortable: true, align: 'left' },
  candidatos: { label: 'Candidatos', sortable: true, align: 'center' },
  performance: { label: 'Performance de Triagens', sortable: false, align: 'left' },
  status: { label: 'Status', sortable: true, align: 'left' },
  nps: { label: 'NPS', sortable: true, align: 'left' },
  recrutador: { label: 'Recrutador(a)', sortable: true, align: 'left' },
  gestor: { label: 'Gestor', sortable: true, align: 'left' },
  prazoTriagem: { label: 'Prazo Triagem', sortable: true, align: 'center' },
  prazoShortlist: { label: 'Prazo Short List', sortable: true, align: 'center' },
  prazoEncerramento: { label: 'Prazo Encerramento', sortable: true, align: 'center' },
  roteiro: { label: 'Roteiro Triagem', sortable: false, align: 'center' },
  acoes: { label: 'Ações', sortable: false, align: 'center' }
}
