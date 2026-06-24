import React from "react"
import {
  Mail,
  MessageSquare,
  Calendar,
  ArrowRight,
  ClipboardList,
} from "lucide-react"
import { RECRUITMENT_STAGES, type RecruitmentStage } from "@/lib/recruitment/stages-data"
import type { TemplateSituation } from "@/hooks/chat/use-communication-templates"

export type TransitionActionType = 'email' | 'whatsapp' | 'triagem_wsi' | 'agendar_entrevista' | 'apenas_mover'

export interface Candidate {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  current_title?: string
  current_company?: string
}

export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
}

export interface TransitionAction {
  id: TransitionActionType
  name: string
  description: string
  icon: React.ReactNode
  color: 'cyan' | 'blue' | 'green' | 'amber' | 'red' | 'gray'
  recommended?: boolean
  templateCategory?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
}

export interface WsiData {
  overall_wsi: number
  technical_wsi: number
  behavioral_wsi: number
  classification: string
}

export interface StageTransitionActionsModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  job: JobVacancy | null
  currentStage: string
  newStage: string
  wsiData?: WsiData
  onConfirm: (action: TransitionActionType, data?: {
    channel?: 'email' | 'whatsapp' | 'both'
    templateId?: string
    subject?: string
    message?: string
    metadata?: Record<string, unknown>
  }) => Promise<void>
}

export const COLOR_CLASSES = {
  cyan: {
    bg: 'bg-lia-bg-secondary',
    border: 'border-lia-border-subtle',
    text: 'text-lia-text-secondary',
    icon: 'text-lia-text-secondary',
    selectedBg: 'bg-lia-bg-tertiary',
    selectedBorder: 'border-lia-btn-primary-bg dark:border-lia-border-medium',
  },
  blue: {
    bg: 'bg-lia-bg-secondary',
    border: 'border-lia-border-subtle',
    text: 'text-lia-text-secondary',
    icon: 'text-lia-text-secondary',
    selectedBg: 'bg-lia-bg-secondary',
    selectedBorder: 'border-lia-btn-primary-bg',
  },
  green: {
    bg: 'bg-status-success/10',
    border: 'border-status-success/30',
    text: 'text-status-success',
    icon: 'text-status-success',
    selectedBg: 'bg-status-success/15',
    selectedBorder: 'border-status-success/30',
  },
  amber: {
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/30',
    text: 'text-status-warning',
    icon: 'text-status-warning',
    selectedBg: 'bg-status-warning/15',
    selectedBorder: 'border-status-warning/30',
  },
  red: {
    bg: 'bg-status-error/10',
    border: 'border-status-error/30',
    text: 'text-status-error',
    icon: 'text-status-error',
    selectedBg: 'bg-status-error/15',
    selectedBorder: 'border-status-error/30',
  },
  gray: {
    bg: 'bg-lia-bg-secondary',
    border: 'border-lia-border-subtle',
    text: 'text-lia-text-primary',
    icon: 'text-lia-text-secondary',
    selectedBg: 'bg-lia-bg-secondary',
    selectedBorder: 'border-lia-btn-primary-bg',
  },
}

// TODO WT-2022: caller should pass company pipeline stages from useRecruitmentStages()
export function getStageDisplayName(
  stageName: string,
  stages: RecruitmentStage[] = RECRUITMENT_STAGES,
): string {
  const stage = stages.find(s => s.name === stageName)
  return stage?.displayName || stageName
}

export function mapTemplateCategoryToSituations(templateCategory: string): TemplateSituation[] {
  switch (templateCategory) {
    case 'rejection':
      return ['feedback_construtivo', 'vaga_fechada']
    case 'interview':
      return ['agendamento']
    case 'screening':
      return ['triagem']
    case 'offer':
      return ['proposta', 'proposta_aceita']
    case 'followup':
      return ['contato_inicial', 'follow_up']
    default:
      return ['contato_inicial', 'follow_up']
  }
}

// TODO WT-2022: caller should pass company pipeline stages from useRecruitmentStages()
export function getSuggestedActions(
  currentStage: string,
  newStage: string,
  stages: RecruitmentStage[] = RECRUITMENT_STAGES,
): TransitionAction[] {
  const baseActions: TransitionAction[] = []

  const newStageData = stages.find(s => s.name === newStage)

  if (newStageData?.isRejection) {
    baseActions.push({
      id: 'email',
      name: 'Enviar feedback por email',
      description: 'Comunicar resultado negativo de forma profissional',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'red',
      recommended: true,
      templateCategory: 'rejection',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar feedback por WhatsApp',
      description: 'Comunicação rápida via WhatsApp',
      icon: React.createElement(MessageSquare, { className: "h-4 w-4" }),
      color: 'red',
      templateCategory: 'rejection',
    })
  } else if (newStage === 'screening' || currentStage === 'sourcing') {
    baseActions.push({
      id: 'triagem_wsi',
      name: 'Convidar para Triagem WSI',
      description: 'Enviar convite para triagem com nossa assistente',
      icon: React.createElement(ClipboardList, { className: "h-4 w-4" }),
      color: 'cyan',
      recommended: true,
      templateCategory: 'screening',
    })
    baseActions.push({
      id: 'email',
      name: 'Enviar email de contato',
      description: 'Primeiro contato por email',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'blue',
      templateCategory: 'followup',
    })
  } else if (newStage === 'long_list' || newStage === 'short_list') {
    baseActions.push({
      id: 'email',
      name: 'Enviar email de aprovação',
      description: 'Comunicar avanço no processo seletivo',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'blue',
      recommended: true,
      templateCategory: 'followup',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar WhatsApp de aprovação',
      description: 'Comunicação rápida de aprovação',
      icon: React.createElement(MessageSquare, { className: "h-4 w-4" }),
      color: 'blue',
      templateCategory: 'followup',
    })
  } else if (newStage.includes('interview')) {
    baseActions.push({
      id: 'agendar_entrevista',
      name: 'Agendar entrevista',
      description: 'Enviar convite para agendamento de entrevista',
      icon: React.createElement(Calendar, { className: "h-4 w-4" }),
      color: 'blue',
      recommended: true,
      templateCategory: 'interview',
    })
    baseActions.push({
      id: 'email',
      name: 'Enviar convite por email',
      description: 'Enviar email com detalhes da entrevista',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'blue',
      templateCategory: 'interview',
    })
  } else if (newStage === 'offer') {
    baseActions.push({
      id: 'email',
      name: 'Enviar proposta por email',
      description: 'Enviar proposta formal de contratação',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'green',
      recommended: true,
      templateCategory: 'offer',
    })
  } else if (newStage === 'hired') {
    baseActions.push({
      id: 'email',
      name: 'Enviar boas-vindas',
      description: 'Email de boas-vindas e próximos passos',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'green',
      recommended: true,
      templateCategory: 'offer',
    })
  } else {
    baseActions.push({
      id: 'email',
      name: 'Enviar email',
      description: 'Comunicar atualização do processo',
      icon: React.createElement(Mail, { className: "h-4 w-4" }),
      color: 'blue',
      templateCategory: 'followup',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar WhatsApp',
      description: 'Comunicação rápida via WhatsApp',
      icon: React.createElement(MessageSquare, { className: "h-4 w-4" }),
      color: 'blue',
      templateCategory: 'followup',
    })
  }

  baseActions.push({
    id: 'apenas_mover',
    name: 'Apenas mover',
    description: 'Mover sem enviar comunicação',
    icon: React.createElement(ArrowRight, { className: "h-4 w-4" }),
    color: 'gray',
  })

  return baseActions
}

export function generateDefaultMessage(
  action: TransitionAction,
  candidate: Candidate | null,
  job: JobVacancy | null,
  newStage: string,
  wsiData?: WsiData
): { subject: string; message: string } {
  const candidateName = candidate?.name || 'Candidato'
  const jobTitle = job?.title || 'a vaga'
  const firstName = candidateName.split(' ')[0]

  if (action.templateCategory === 'rejection') {
    const wsiParagraph = wsiData
      ? `\n\nSua avaliação indicou uma compatibilidade de ${wsiData.overall_wsi}% com os requisitos da posição.`
      : ''
    return {
      subject: `Retorno sobre sua candidatura - ${jobTitle}`,
      message: `Olá ${firstName},\n\nAgradecemos seu interesse e participação em nosso processo seletivo para ${jobTitle}.\n\nApós análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades atuais da posição.${wsiParagraph}\n\nMantemos seu currículo em nosso banco de talentos para futuras oportunidades.\n\nDesejamos sucesso em sua carreira!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'interview') {
    const wsiParagraph = wsiData
      ? `\n\nSua avaliação na triagem foi muito positiva (${wsiData.classification}), o que reforça nosso interesse em conhecê-lo(a) melhor.`
      : ''
    return {
      subject: `Convite para entrevista - ${jobTitle}`,
      message: `Olá ${firstName},\n\nParabéns por avançar em nosso processo seletivo para ${jobTitle}! 🎉\n\nGostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista.${wsiParagraph}\n\nPor favor, clique no link abaixo para escolher o melhor horário:\n[Link para agendamento]\n\nCaso tenha alguma dúvida, estamos à disposição.\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'offer') {
    return {
      subject: `Proposta de contratação - ${jobTitle}`,
      message: `Olá ${firstName},\n\nÉ com grande satisfação que comunicamos que você foi selecionado(a) para a posição de ${jobTitle}!\n\nAnexo a esta mensagem você encontrará nossa proposta formal de contratação.\n\nAguardamos seu retorno em até 5 dias úteis.\n\nEstamos muito animados com a possibilidade de tê-lo(a) em nossa equipe!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'screening') {
    return {
      subject: `Próximo passo: Avaliação - ${jobTitle}`,
      message: `Olá ${firstName},\n\nEstamos avançando em nosso processo seletivo para ${jobTitle} e gostaríamos de convidá-lo(a) para uma triagem rápida com a nossa assistente virtual.\n\n📋 Sobre a triagem:\n• Duração estimada: 15-20 minutos\n• Formato: Conversa por chat ou WhatsApp\n• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas\n\nClique no link abaixo para iniciar:\n[Link para triagem]\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  const wsiFollowupParagraph = wsiData
    ? `\n\nSua avaliação na triagem foi muito positiva (${wsiData.classification}), o que reforça nosso interesse em conhecê-lo(a) melhor.`
    : ''
  return {
    subject: `Atualização do processo seletivo - ${jobTitle}`,
    message: `Olá ${firstName},\n\nGostaríamos de informar que você avançou para a próxima etapa do processo seletivo para ${jobTitle}!${wsiFollowupParagraph}\n\nEm breve entraremos em contato com mais detalhes sobre os próximos passos.\n\nQualquer dúvida, estamos à disposição.\n\nAtenciosamente,\nEquipe de Recrutamento`,
  }
}

export function getWsiClassificationColor(classification: string): { bg: string; text: string } {
  const lower = classification.toLowerCase()
  if (lower === 'excelente' || lower === 'alto') {
    return { bg: 'bg-status-success/15', text: 'text-status-success' }
  }
  if (lower === 'medio' || lower === 'médio') {
    return { bg: 'bg-status-warning/15', text: 'text-status-warning' }
  }
  return { bg: 'bg-status-error/15', text: 'text-status-error' }
}
