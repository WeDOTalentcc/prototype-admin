"use client"

import React from "react"
import {
  Brain, MessageCircle, FileText, Building2, Zap, Users
} from "lucide-react"
import type { BigFiveProfile } from "@/hooks/recruitment/use-screening-questions"

export interface ScreeningQuestionsPanelProps {
  jobTitle: string
  department?: string
  seniority: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  bigFiveProfile?: BigFiveProfile
  skills: string[]
  behavioralCompetencies?: string[]
  isAffirmative?: boolean
  affirmativeType?: string
  onQuestionsChange?: (questions: Record<string, unknown>[]) => void
  className?: string
}

export const WSI_BLOCKS = [
  {
    id: 0,
    name: 'Abordagem Inicial',
    description: 'Template WhatsApp pré-aprovado',
    duration: '< 1 min',
    editable: false,
    type: 'template',
    icon: MessageCircle
  },
  {
    id: 1,
    name: 'Apresentação da Oportunidade',
    description: 'Pitch conversacional com detalhes da vaga',
    duration: '3 min',
    editable: false,
    type: 'presentation',
    icon: FileText
  },
  {
    id: 2,
    name: 'Perguntas Padrão da Empresa',
    description: 'Perguntas configuradas pela empresa (incluindo elegibilidade)',
    duration: '3 min',
    editable: true,
    type: 'company',
    icon: Building2
  },
  {
    id: 3,
    name: 'Avaliação Técnica',
    description: 'Skills com pesos e rubricas automáticas',
    duration: '5 min',
    editable: true,
    type: 'technical',
    icon: Zap
  },
  {
    id: 4,
    name: 'Análise Situacional e Fit',
    description: 'Perguntas situacionais com follow-ups',
    duration: '4 min',
    editable: true,
    type: 'situational',
    icon: Users
  },
  {
    id: 5,
    name: 'Resultado e Encerramento',
    description: 'Índice WSI automático e feedback',
    duration: '3 min',
    editable: false,
    type: 'result',
    icon: Brain
  }
]

export const WSI_AUTOMATIC_MESSAGES: Record<number, { title: string; message: string; note: string }> = {
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
  6: {
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
        <span key={`ph-${index}`}>
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
    return <span key={`part-${index}`}>{part}</span>
  })
}

export const BLOOM_COLORS: Record<number, string> = {
  1: "bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle",
  2: "bg-status-warning/10 text-status-warning border-status-warning/30",
  3: "bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30",
  4: "bg-status-error/10 text-status-error border-status-error/30",
  5: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30",
  6: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30"
}

export const DREYFUS_COLORS: Record<number, string> = {
  1: "bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle",
  2: "bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default",
  3: "bg-status-success/10 text-status-success border-status-success/30",
  4: "bg-status-warning/10 text-status-warning border-status-warning/30",
  5: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30"
}
