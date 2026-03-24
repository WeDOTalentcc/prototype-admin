import React from 'react'
import type { JobStatus, WSIBlock, WSIAutomaticMessage } from './jobsPageTypes'

export function getBloomComplexity(bloomLevel: number): { label: string; color: string } {
  if (bloomLevel <= 2) return { label: 'Baixa', color: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800' }
  if (bloomLevel <= 4) return { label: 'Média', color: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800' }
  return { label: 'Alta', color: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800' }
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
    'Ativa': '#A8D5B7',
    'Aprovada': '#B8E0D2',
    'Aguardando aprovação': '#F5E6B3',
    'Reaberta': '#F5D6A8',
    'Paralisada': '#D5BFA8',
    'Interna': '#C5D9ED',
    'Fechada (preenchida)': '#B8C5D0',
    'Fechada (expirada)': '#E8B8B8',
    'Cancelada': '#E5C5C5',
    'Rascunho': '#E8E4E0',
    'Arquivada': '#E5E7EB',
    'Concluída': '#A8CED5'
  }
  return statusColors[status] || '#E5E7EB'
}

export const priorityColors = {
  "alta": "bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400",
  "média": "bg-gray-50 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  "baixa": "bg-gray-50 text-gray-800 dark:bg-gray-800 dark:text-gray-500"
}

export const WSI_BLOCKS: WSIBlock[] = [
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
    description: 'Perguntas situacionais com follow-ups e fit cultural',
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

export const WSI_AUTOMATIC_MESSAGES: Record<number, WSIAutomaticMessage> = {
  0: {
    title: "Abordagem Inicial via WhatsApp",
    message: `Olá {candidato.nome}! 👋

Aqui é a LIA, assistente de recrutamento da {empresa.nome}.

Vi que você se candidatou para a vaga de {vaga.titulo} e gostaria de conversar sobre a oportunidade.

Podemos iniciar agora? Leva menos de 10 minutos! 🚀`,
    note: "Template pré-aprovado • Enviado automaticamente ao candidato"
  },
  1: {
    title: "Apresentação da Oportunidade",
    message: `Que ótimo ter você aqui! Deixa eu te contar um pouco sobre a vaga:

📋 **Posição:** {vaga.titulo}
🏢 **Empresa:** {empresa.nome}
📍 **Modelo:** {vaga.modelo_trabalho}
💰 **Faixa Salarial:** {vaga.faixa_salarial}

{vaga.descricao_resumida}

Agora vou fazer algumas perguntas rápidas para entender melhor seu perfil. Responda naturalmente, como se estivéssemos conversando! 💬`,
    note: "Pitch conversacional • Gerado a partir dos dados da vaga"
  },
  5: {
    title: "Resultado e Encerramento",
    message: `Muito obrigada pelas suas respostas, {candidato.nome}! 🙏

Analisei todas as informações e já encaminhei seu perfil para nossa equipe de recrutamento.

📊 **Próximos passos:**
• Você receberá um feedback em até {prazo_feedback}
• Se aprovado(a), entraremos em contato para agendar a entrevista

Qualquer dúvida, estou por aqui! Boa sorte! 🍀`,
    note: "Índice WSI calculado automaticamente • Feedback enviado conforme configuração"
  }
}

export function formatMessageWithVariables(message: string): React.ReactNode[] {
  const parts = message.split(/(\{[^}]+\})/g)
  return parts.map((part, index) => {
    if (part.match(/^\{[^}]+\}$/)) {
      return (
        <span key={index} style={{ fontWeight: 500 }}>
          {part}
        </span>
      )
    }
    if (part.includes('**')) {
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g)
      return boldParts.map((bp, bpIndex) => {
        if (bp.match(/^\*\*[^*]+\*\*$/)) {
          return <strong key={`${index}-${bpIndex}`}>{bp.replace(/\*\*/g, '')}</strong>
        }
        return <span key={`${index}-${bpIndex}`}>{bp}</span>
      })
    }
    return <span key={index}>{part}</span>
  })
}

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
  performance: { label: 'Performance LIA Triagens', sortable: false, align: 'left' },
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
