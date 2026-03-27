"use client"

import React, { useState } from "react"
import { 
  ClipboardList, BarChart3, Brain, Lightbulb, Layers3, Settings, 
  MessageSquare, Globe, Phone, CheckCircle, CalendarCheck,
  ChevronUp, ChevronDown
} from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  category?: string
  options?: string[]
  time_limit?: number
  required?: boolean
  [key: string]: any
}

interface ScreeningConfig {
  status?: {
    enabled: boolean
    last_updated?: string | null
  }
  channels?: {
    whatsapp?: { enabled: boolean }
    chat_web?: { enabled: boolean }
    phone?: { enabled: boolean }
  }
  settings?: {
    min_score?: number
    response_timeout_hours?: number
    max_retries?: number
  }
  scheduling?: {
    auto_enabled?: boolean
    min_score_for_auto?: number
    calendar_provider?: string
    available_hours?: string
    interview_duration_min?: number
  }
  wsi_skills?: string[]
}

interface JobFunnel {
  total: number
  screening: number
  interview: number
  final: number
  hired: number
}

interface PreviewJob {
  funnel: JobFunnel
  nps: number
  screeningQuestions?: ScreeningQuestion[]
  screeningConfig?: ScreeningConfig
  behavioralCompetencies?: any[]
  [key: string]: any
}

const WSI_BLOCKS = [
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
    name: 'Avaliação Técnica', 
    description: 'Skills com pesos e rubricas automáticas',
    duration: '5 min', 
    editable: true,
    type: 'technical'
  },
  { 
    id: 4, 
    name: 'Análise Situacional e Fit', 
    description: 'Perguntas situacionais com follow-ups',
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

const WSI_AUTOMATIC_MESSAGES: Record<number, { title: string; message: string; note: string }> = {
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

function formatMessageWithVariables(message: string): React.ReactNode[] {
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

interface ScreeningScriptTabProps {
  previewJob: PreviewJob
}

export function ScreeningScriptTab({ previewJob }: ScreeningScriptTabProps) {
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([])

  const funnel = previewJob.funnel || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
  const nps = previewJob.nps || 0

  return (
    <div className="space-y-4">
      {/* Header externo: Título + Status + Botão Editar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Roteiro de Triagem Automática</h4>
          <Badge 
            className={`text-micro px-1.5 py-0 h-4 text-gray-800 ${(previewJob.screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-gray-200'}`}
          >
            {(previewJob.screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
          </Badge>
        </div>
      </div>

      {/* 1. Card Performance da Triagem */}
      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-3">
          <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Performance da Triagem
        </h5>
        
        {/* Métricas do Roteiro - Linha 1 */}
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              {(() => {
                const questions = previewJob.screeningQuestions || []
                const totalTime = questions.reduce((acc: number, q: any) => acc + (q.time_limit || 120), 0)
                return Math.ceil(totalTime / 60)
              })()}min
            </div>
            <p className="text-micro text-gray-500">Tempo Total</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              {previewJob.screeningQuestions?.length || 0}
            </div>
            <p className="text-micro text-gray-500">Perguntas</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              ~{100 - (previewJob.screeningConfig?.settings?.min_score ?? 70)}%
            </div>
            <p className="text-micro text-gray-500">Reprovação Est.</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-900 dark:text-gray-50">
              {previewJob.screeningConfig?.status?.last_updated 
                ? new Date(previewJob.screeningConfig.status.last_updated).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
                : new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
            </div>
            <p className="text-micro text-gray-500">Atualizado</p>
          </div>
        </div>
        
        {/* Performance - Linha 2 */}
        <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-gray-100">
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              {Math.round(funnel.screening * 0.6)}
            </div>
            <p className="text-micro text-gray-500">Triados</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              {funnel.total > 0 ? Math.round((funnel.screening / funnel.total) * 100) : 0}%
            </div>
            <p className="text-micro text-gray-500">Conclusão</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-status-success">
              {funnel.screening > 0 ? Math.round((funnel.interview / funnel.screening) * 100) : 0}%
            </div>
            <p className="text-micro text-gray-500">Aprovação</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-gray-800">
              {nps > 0 ? (nps / 20).toFixed(1) : '4.2'}
            </div>
            <p className="text-micro text-gray-500">Nota Média</p>
          </div>
        </div>
      </div>

      {/* 2. Skills WSI Utilizadas */}
      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Skills WSI Avaliadas
        </h5>
        <div className="flex flex-wrap gap-1.5">
          {(() => {
            const skills = previewJob.screeningConfig?.wsi_skills 
              || (previewJob.behavioralCompetencies?.map((bc: any) => typeof bc === 'string' ? bc : bc.competency || bc.name) || [])
            const defaultSkills = ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
            const finalSkills = skills.length > 0 ? skills : defaultSkills
            return finalSkills.slice(0, 6).map((skill: string, idx: number) => (
              <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-micro px-2 py-0.5 h-5 font-medium">
                {skill}
              </Badge>
            ))
          })()}
        </div>
        <p className="text-micro text-gray-400 mt-2 flex items-center gap-1">
          <Lightbulb className="w-3 h-3" />
          Extraídas automaticamente do perfil da vaga via metodologia WSI
        </p>
      </div>

      {/* 3. Blocos WSI do Roteiro de Triagem */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
            <Layers3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Fluxo de Triagem WSI
            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-200 text-gray-800 dark:text-gray-200">
              6 Blocos
            </Badge>
          </h5>
        </div>

        {/* WSI Blocks Accordion */}
        <div className="space-y-2">
          {WSI_BLOCKS.map((block) => {
            const isExpanded = expandedBlocks.includes(block.id)
            
            const allQuestions = previewJob.screeningQuestions || []
            const cat = (q: any) => (q.category || '').toLowerCase()
            const typ = (q: any) => (q.type || '').toLowerCase()
            
            const isBlock2 = (q: any) => {
              if (typ(q) === 'eliminatory' || q.required) return true
              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
              return false
            }
            
            const isBlock3 = (q: any) => {
              if (isBlock2(q)) return false
              return cat(q).includes('tecn') || cat(q).includes('tech') ||
                cat(q).includes('skill') || cat(q).includes('técnica') ||
                typ(q).includes('tech')
            }
            
            const isBlock4 = (q: any) => {
              if (isBlock2(q) || isBlock3(q)) return false
              return true
            }
            
            const blockQuestions = allQuestions.filter((q: any) => {
              if (block.id === 2) return isBlock2(q)
              if (block.id === 3) return isBlock3(q)
              if (block.id === 4) return isBlock4(q)
              return false
            })

            
            const eliminatoryCount = blockQuestions.filter((q: any) => q.type === 'eliminatory' || q.required).length
            const informativeCount = blockQuestions.length - eliminatoryCount
            
            return (
              <div 
                key={block.id} 
                className={`border rounded-md overflow-hidden ${
                  block.editable ? 'border-gray-200' : 'border-gray-100 bg-gray-50/50'
                }`}
              >
                {/* Block Header */}
                <div 
                  className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors ${
                    block.editable 
                      ? 'bg-gray-50 hover:bg-gray-100' 
                      : 'bg-gray-100/80'
                  }`}
                  onClick={() => {
                    if (isExpanded) {
                      setExpandedBlocks(prev => prev.filter(id => id !== block.id))
                    } else {
                      setExpandedBlocks(prev => [...prev, block.id])
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-5 h-5 rounded-full text-white text-micro font-bold flex items-center justify-center ${
                      block.editable ? 'bg-gray-700' : 'bg-gray-400'
                    }`}>
                      {block.id}
                    </span>
                    <div>
                      <span className={`text-xs font-semibold ${block.editable ? 'text-gray-950' : 'text-gray-600'}`}>
                        {block.name}
                      </span>
                      <span className="text-micro text-gray-500 ml-1.5">({block.duration})</span>
                    </div>
                    {!block.editable && (
                      <Badge className="text-micro px-1 py-0 h-3.5 bg-gray-200 text-gray-500">
                        Auto
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {block.editable && blockQuestions.length > 0 && (
                      <>
                        {eliminatoryCount > 0 && (
                          <Badge className="text-micro px-1.5 py-0 bg-status-error/10 text-status-error border border-status-error/30">
                            {eliminatoryCount} Elim.
                          </Badge>
                        )}
                        {informativeCount > 0 && (
                          <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-600">
                            {informativeCount} Info.
                          </Badge>
                        )}
                      </>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                    )}
                  </div>
                </div>
                
                {/* Block Content */}
                {isExpanded && (
                  <div className={`p-2.5 space-y-1.5 ${!block.editable ? 'bg-gray-50/30' : ''}`}>
                    {/* Non-editable blocks show automatic WSI messages */}
                    {!block.editable ? (
                      WSI_AUTOMATIC_MESSAGES[block.id] ? (
                        <div className="rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 overflow-hidden">
                          <div className="px-2.5 py-1.5 border-b border-gray-900 dark:border-gray-50/10 bg-gray-100 dark:bg-gray-800">
                            <p className="text-xs font-medium text-gray-800">
                              {WSI_AUTOMATIC_MESSAGES[block.id].title}
                            </p>
                          </div>
                          <div className="p-2.5">
                            <div className="text-micro text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">
                              {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                            </div>
                          </div>
                          <div className="px-2.5 py-1.5 border-t border-gray-900 dark:border-gray-50/10 bg-gray-50">
                            <p className="text-micro text-gray-500 italic">
                              {WSI_AUTOMATIC_MESSAGES[block.id].note}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-2.5 bg-white/60 border border-gray-100 rounded-md">
                          <p className="text-micro text-gray-600 italic">
                            {block.description}
                          </p>
                          <p className="text-micro text-gray-400 mt-1">
                            Gerenciado automaticamente pela LIA
                          </p>
                        </div>
                      )
                    ) : (
                      <>
                        {/* Questions in this block */}
                        {blockQuestions.length === 0 ? (
                          <div className="p-3 bg-gray-50 border border-gray-200 border-dashed rounded-md text-center">
                            <p className="text-micro text-gray-500">
                              Nenhuma pergunta neste bloco
                            </p>
                          </div>
                        ) : (
                          blockQuestions.map((item: any, idx: number) => (
                            <div 
                              key={item.id || idx} 
                              className="p-2 bg-white border border-gray-200 rounded-md transition-colors"
                            >
                              <div className="flex items-start gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                                    <Badge className={`text-micro px-1.5 py-0 h-4 ${
                                      item.category === 'behavioral' || item.category === 'Comportamental'
                                        ? 'bg-wedo-purple/15 text-wedo-purple border border-wedo-purple/30'
                                        : item.category === 'technical' || item.category === 'Técnica'
                                        ? 'bg-gray-100 dark:bg-gray-800 text-wedo-cyan-dark border border-gray-300 dark:border-gray-600'
                                        : 'bg-status-success/15 text-status-success border border-status-success/30'
                                    }`}>
                                      {item.category === 'behavioral' ? 'Comport.' 
                                        : item.category === 'technical' ? 'Técnica' 
                                        : item.category === 'cultural' ? 'Cultural'
                                        : item.category || 'Geral'}
                                    </Badge>
                                    {(item.type === 'eliminatory' || item.required) && (
                                      <Badge className="text-micro px-1.5 py-0 h-4 bg-status-error/10 text-status-error border border-status-error/30">
                                        Eliminatória
                                      </Badge>
                                    )}
                                  </div>
                                  <p className="text-micro text-gray-950 dark:text-gray-50 leading-relaxed">
                                    {item.question}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 4. Canais + Configurações Agrupados */}
      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-3">
          <Settings className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Canais e Configurações
        </h5>

        {/* Canais em linha */}
        <div className="flex items-center gap-3 mb-3 pb-3 border-b border-gray-100">
          <span className="text-micro text-gray-500">Canais:</span>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(previewJob.screeningConfig?.channels?.whatsapp?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-400'}`}>
              <MessageSquare className="w-3 h-3" />
              <span className="text-micro font-medium">WhatsApp</span>
              {(previewJob.screeningConfig?.channels?.whatsapp?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
            </div>
            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(previewJob.screeningConfig?.channels?.chat_web?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-400'}`}>
              <Globe className="w-3 h-3" />
              <span className="text-micro font-medium">Chat Web</span>
              {(previewJob.screeningConfig?.channels?.chat_web?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
            </div>
            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(previewJob.screeningConfig?.channels?.phone?.enabled ?? false) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-400'}`}>
              <Phone className="w-3 h-3" />
              <span className="text-micro font-medium">Telefone</span>
              {(previewJob.screeningConfig?.channels?.phone?.enabled ?? false) && <CheckCircle className="w-3 h-3" />}
            </div>
          </div>
        </div>

        {/* Configurações em grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center justify-between">
            <span className="text-micro text-gray-500">Score Mínimo</span>
            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-700 text-white">{previewJob.screeningConfig?.settings?.min_score ?? 70}%</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-gray-500">Timeout Resposta</span>
            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.settings?.response_timeout_hours ?? 48}h</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-gray-500">Re-tentativas</span>
            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.settings?.max_retries ?? 2}x</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-gray-500">Fallback</span>
            <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-orange/15 text-wedo-orange">Revisão Manual</Badge>
          </div>
        </div>

        {/* Status Integrações */}
        <div className="flex items-center gap-3 mt-3 pt-2 border-t border-gray-100">
          <span className="text-micro text-gray-400">Integrações:</span>
          <div className="flex items-center gap-1 text-micro">
            <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>
            <span className="text-gray-600">OpenMic.ai</span>
          </div>
          <div className="flex items-center gap-1 text-micro">
            <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>
            <span className="text-gray-600">Deepgram</span>
          </div>
        </div>
      </div>

      {/* 5. Agendamento Automático */}
      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <CalendarCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Agendamento Automático</h5>
          </div>
          <Badge className={`${(previewJob.screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-gray-700 text-white dark:bg-gray-600' : 'bg-gray-400 text-white'} text-micro px-1.5 py-0 h-4`}>
            {(previewJob.screeningConfig?.scheduling?.auto_enabled ?? true) ? 'Ativo' : 'Inativo'}
          </Badge>
        </div>
        <p className="text-micro text-gray-500 mb-2">Aprovados na triagem são agendados automaticamente para entrevista</p>

        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
            <span className="text-micro text-gray-500">Score Mínimo</span>
            <span className="text-micro font-medium text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.scheduling?.min_score_for_auto ?? 75}%</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
            <span className="text-micro text-gray-500">Calendário</span>
            <span className="text-micro font-medium text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
            <span className="text-micro text-gray-500">Horários</span>
            <span className="text-micro font-medium text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.scheduling?.available_hours || '9h-18h'}</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
            <span className="text-micro text-gray-500">Duração</span>
            <span className="text-micro font-medium text-gray-800 dark:text-gray-200">{previewJob.screeningConfig?.scheduling?.interview_duration_min ?? 45}min</span>
          </div>
        </div>
      </div>

      {/* 6. Insights LIA */}
      <div className="p-2.5 bg-gray-50 rounded-md border border-gray-100">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-micro font-medium text-gray-800 dark:text-gray-200 mb-1">Insights da LIA</p>
            <ul className="space-y-0.5 text-micro text-gray-600">
              <li>• Triagens 6.5x mais rápidas que processo manual</li>
              <li>• Economia estimada: R$ {(() => {
                const triagens = Math.round(funnel.total * 0.85)
                const horasEconomizadas = Math.round((triagens * 15) / 60)
                return (horasEconomizadas * 80).toLocaleString('pt-BR')
              })()} em custos</li>
              <li>• Taxa de aprovação 8% acima da média do setor</li>
            </ul>
          </div>
        </div>
      </div>

    </div>
  )
}
