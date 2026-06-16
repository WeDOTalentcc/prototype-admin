/**
 * WSI Blocks — Canonical single-source-of-truth (audit P2-1/NEW-3).
 *
 * Antes desta consolidação havia TRÊS definições de WSI_BLOCKS:
 *   1. plataforma-lia/src/components/jobs/jobsPageConstants.tsx (mais usada)
 *   2. plataforma-lia/src/components/job-creation/ScreeningPanelConstants.tsx (com icons)
 *   3. plataforma-lia/src/components/screening-config/ScreeningScriptTab.tsx (local)
 *
 * Cada uma com nomes e durations levemente diferentes. Inconsistência semântica
 * para o usuário (mesmo "bloco 3" aparecia ora como "Avaliação Técnica" ora
 * como "Competências Técnicas") e bug-trap para devs (mexer numa cópia não
 * propagava).
 *
 * Esta é agora a fonte canônica. As cópias antigas re-exportam daqui para
 * preservar os imports existentes.
 */

export interface WSIBlock {
  id: number
  name: string
  description: string
  duration: string
  editable: boolean
  type: 'template' | 'presentation' | 'company' | 'technical' | 'situational' | 'result'
  /** Nome do ícone Lucide (consumidor mapeia para o componente). */
  iconName?: 'MessageCircle' | 'FileText' | 'Building2' | 'Zap' | 'Users' | 'Brain'
}

export interface WSIAutomaticMessage {
  title: string
  message: string
  note: string
}

export const WSI_BLOCKS: WSIBlock[] = [
  {
    id: 0,
    name: 'Abordagem Inicial',
    description: 'Template WhatsApp pré-aprovado',
    duration: '< 1 min',
    editable: false,
    type: 'template',
    iconName: 'MessageCircle',
  },
  {
    id: 1,
    name: 'Apresentação da Oportunidade',
    description: 'Pitch conversacional com detalhes da vaga',
    duration: '3 min',
    editable: false,
    type: 'presentation',
    iconName: 'FileText',
  },
  {
    id: 2,
    name: 'Perguntas Padrão da Empresa',
    description: 'Perguntas configuradas pela empresa (incluindo elegibilidade)',
    duration: '3 min',
    editable: true,
    type: 'company',
    iconName: 'Building2',
  },
  {
    id: 3,
    name: 'Competências Técnicas',
    description: 'Skills com pesos e rubricas automáticas',
    duration: '5 min',
    editable: true,
    type: 'technical',
    iconName: 'Zap',
  },
  {
    id: 4,
    name: 'Competências Comportamentais e Fit',
    description: 'Perguntas situacionais com follow-ups e aderência cultural',
    duration: '4 min',
    editable: true,
    type: 'situational',
    iconName: 'Users',
  },
  {
    id: 5,
    name: 'Resultado e Encerramento',
    description: 'Índice WSI automático e feedback',
    duration: '3 min',
    editable: false,
    type: 'result',
    iconName: 'Brain',
  },
]

export const WSI_AUTOMATIC_MESSAGES: Record<number, WSIAutomaticMessage> = {
  0: {
    title: 'Abordagem Inicial via WhatsApp',
    message: `Olá {candidato.nome}! 👋

Aqui é a IA, assistente de recrutamento da {empresa.nome}.

Vi que você se candidatou para a vaga de {vaga.titulo} e gostaria de conversar sobre a oportunidade.

Podemos iniciar agora? Leva menos de 10 minutos! 🚀`,
    note: 'Template pré-aprovado • Enviado automaticamente ao candidato',
  },
  1: {
    title: 'Apresentação da Oportunidade',
    message: `Que ótimo ter você aqui! Deixa eu te contar um pouco sobre a vaga:

📋 **Posição:** {vaga.titulo}
🏢 **Empresa:** {empresa.nome}
📍 **Modalidade:** {vaga.modalidade}
💰 **Faixa salarial:** {vaga.salario}

Você confirma que tem interesse em prosseguir?`,
    note: 'Mensagem dinâmica • Personalizada pela IA com dados da vaga',
  },
  5: {
    title: 'Resultado e Encerramento',
    message: `Pronto, {candidato.nome}! Sua triagem foi concluída. 🎉

Em até 2 dias úteis você receberá o retorno por aqui mesmo.

Agradecemos seu tempo e interesse na vaga!`,
    note: 'Encerramento automático • WSI calculado e enviado ao recrutador',
  },
}

import React from 'react'

/**
 * Renderiza uma mensagem WSI como nós React, destacando placeholders `{x.y}`
 * em `<span>` e marcações `**bold**` em `<strong>`. Mesma assinatura/comportamento
 * da função histórica em `jobsPageConstants.tsx` (preservada na consolidação).
 */
export function formatMessageWithVariables(message: string): React.ReactNode[] {
  const parts = message.split(/(\{[^}]+\})/g)
  return parts.map((part, index) => {
    if (part.match(/^\{[^}]+\}$/)) {
      return React.createElement('span', { key: `var-${index}` }, part)
    }
    if (part.includes('**')) {
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g)
      return boldParts.map((bp, bpIndex) => {
        if (bp.match(/^\*\*[^*]+\*\*$/)) {
          return React.createElement(
            'strong',
            { key: `${index}-${bpIndex}` },
            bp.replace(/\*\*/g, ''),
          )
        }
        return React.createElement('span', { key: `${index}-${bpIndex}` }, bp)
      })
    }
    return React.createElement('span', { key: `part-${index}` }, part)
  })
}
