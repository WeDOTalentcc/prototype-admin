"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React, { useState } from"react"
import { 
  ClipboardList, BarChart3, Brain, Lightbulb, Layers3, Settings, 
  MessageSquare, Globe, Phone, CheckCircle, CalendarCheck,
  ChevronUp, ChevronDown
} from"lucide-react"
import { Chip } from "@/components/ui/chip"
// Audit P2-1/NEW-3: cópia local removida — usa fonte canônica.
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables } from "@/constants/wsi-blocks"

interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  category?: string
  options?: string[]
  time_limit?: number
  required?: boolean
  [key: string]: string | number | boolean | string[] | undefined
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
  behavioralCompetencies?: Array<string | { competency?: string; name?: string }>
  [key: string]: unknown
}

// P3-1 (rev. 17): cópia local removida — usa fonte canônica em
// `@/constants/wsi-blocks` importada acima.

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
          <ClipboardList className="w-4 h-4 text-lia-text-secondary" />
          <h4 className="text-xs font-semibold text-lia-text-primary">Roteiro de Triagem Automática</h4>
          <Chip variant="neutral" muted 
            className={`text-micro px-1.5 py-0 h-4 flex items-center text-lia-text-primary ${(previewJob.screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-lia-interactive-active'}`}
          >
            {(previewJob.screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
          </Chip>
        </div>
      </div>

      {/* 1. Card Performance da Triagem */}
      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-3">
          <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
          Performance da Triagem
        </h5>
        
        {/* Métricas do Roteiro - Linha 1 */}
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {(() => {
                const questions = previewJob.screeningQuestions || []
                const totalTime = questions.reduce((acc: number, q: ScreeningQuestion) => acc + (q.time_limit || 120), 0)
                return Math.ceil(totalTime / 60)
              })()}min
            </div>
            <p className="text-micro text-lia-text-secondary">Tempo Total</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {previewJob.screeningQuestions?.length || 0}
            </div>
            <p className="text-micro text-lia-text-secondary">Perguntas</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              ~{100 - (previewJob.screeningConfig?.settings?.min_score ?? 70)}%
            </div>
            <p className="text-micro text-lia-text-secondary">Reprovação Est.</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {previewJob.screeningConfig?.status?.last_updated 
                ? new Date(previewJob.screeningConfig.status.last_updated).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
                : new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
            </div>
            <p className="text-micro text-lia-text-secondary">Atualizado</p>
          </div>
        </div>
        
        {/* Performance - Linha 2 */}
        <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-lia-border-subtle">
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {Math.round(funnel.screening * 0.6)}
            </div>
            <p className="text-micro text-lia-text-secondary">Triados</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {funnel.total > 0 ? Math.round((funnel.screening / funnel.total) * 100) : 0}%
            </div>
            <p className="text-micro text-lia-text-secondary">Conclusão</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-status-success">
              {funnel.screening > 0 ? Math.round((funnel.interview / funnel.screening) * 100) : 0}%
            </div>
            <p className="text-micro text-lia-text-secondary">Aprovação</p>
          </div>
          <div className="text-center">
            <div className="text-base-ui font-semibold text-lia-text-primary">
              {nps > 0 ? (nps / 20).toFixed(1) : '4.2'}
            </div>
            <p className="text-micro text-lia-text-secondary">Nota Média</p>
          </div>
        </div>
      </div>

      {/* 2. Skills WSI Utilizadas */}
      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Skills WSI Avaliadas
        </h5>
        <div className="flex flex-wrap gap-1.5">
          {(() => {
            const skills = previewJob.screeningConfig?.wsi_skills 
              || (previewJob.behavioralCompetencies?.map((bc) => typeof bc === 'string' ? bc : bc.competency || bc.name || '') || [])
            const defaultSkills = ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
            const finalSkills = skills.length > 0 ? skills : defaultSkills
            return finalSkills.slice(0, 6).map((skill: string, idx: number) => (
              <Chip variant="neutral" muted key={idx} className="bg-lia-bg-tertiary text-lia-text-secondary text-micro px-2 py-0.5 h-5 font-medium">
                {skill}
              </Chip>
            ))
          })()}
        </div>
        <p className="text-micro text-lia-text-secondary mt-2 flex items-center gap-1">
          <Lightbulb className="w-3 h-3" />
          Extraídas automaticamente do perfil da vaga via metodologia WSI
        </p>
      </div>

      {/* 3. Blocos WSI do Roteiro de Triagem */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
            <Layers3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            Fluxo de Triagem WSI
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-interactive-active text-lia-text-primary">
              6 Blocos
            </Chip>
          </h5>
        </div>

        {/* WSI Blocks Accordion */}
        <div className="space-y-2">
          {WSI_BLOCKS.map((block) => {
            const isExpanded = expandedBlocks.includes(block.id)
            
            const allQuestions = previewJob.screeningQuestions || []
            const cat = (q: ScreeningQuestion) => (String(q.category || '')).toLowerCase()
            const typ = (q: ScreeningQuestion) => (String(q.type || '')).toLowerCase()

            const isBlock2 = (q: ScreeningQuestion) => {
              if (typ(q) === 'eliminatory' || q.required) return true
              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
              return false
            }
            
            const isBlock3 = (q: ScreeningQuestion) => {
              if (isBlock2(q)) return false
              return cat(q).includes('tecn') || cat(q).includes('tech') ||
                cat(q).includes('skill') || cat(q).includes('técnica') ||
                typ(q).includes('tech')
            }

            const isBlock4 = (q: ScreeningQuestion) => {
              if (isBlock2(q) || isBlock3(q)) return false
              return true
            }

            const blockQuestions = allQuestions.filter((q: ScreeningQuestion) => {
              if (block.id === 2) return isBlock2(q)
              if (block.id === 3) return isBlock3(q)
              if (block.id === 4) return isBlock4(q)
              return false
            })

            
            const eliminatoryCount = blockQuestions.filter((q: ScreeningQuestion) => q.type === 'eliminatory' || q.required).length
            const informativeCount = blockQuestions.length - eliminatoryCount
            
            return (
              <div 
                key={block.id} 
                className={`border rounded-md overflow-hidden ${
 block.editable ? 'border-lia-border-subtle' : 'border-lia-border-subtle bg-lia-bg-secondary/50'
                }`}
              >
                {/* Block Header */}
                <div 
                  className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors motion-reduce:transition-none ${
 block.editable 
                      ? 'bg-lia-bg-secondary hover:bg-lia-interactive-hover' 
                      : 'bg-lia-bg-tertiary/80'
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
 block.editable ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-medium'
                    }`}>
                      {block.id}
                    </span>
                    <div>
                      <span className={`text-xs font-semibold ${block.editable ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                        {block.name}
                      </span>
                      <span className="text-micro text-lia-text-secondary ml-1.5">({block.duration})</span>
                    </div>
                    {!block.editable && (
                      <Chip variant="neutral" muted className="text-micro px-1 py-0 h-3.5 bg-lia-interactive-active text-lia-text-secondary">
                        Auto
                      </Chip>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {block.editable && blockQuestions.length > 0 && (
                      <>
                        {eliminatoryCount > 0 && (
                          <Chip variant="danger" muted className="text-micro px-1.5 py-0">
                            {eliminatoryCount} Elim.
                          </Chip>
                        )}
                        {informativeCount > 0 && (
                          <Chip variant="neutral" muted className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary">
                            {informativeCount} Info.
                          </Chip>
                        )}
                      </>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-lia-text-secondary" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />
                    )}
                  </div>
                </div>
                
                {/* Block Content */}
                {isExpanded && (
                  <div className={`p-2.5 space-y-1.5 ${!block.editable ? 'bg-lia-bg-secondary/30' : ''}`}>
                    {/* Non-editable blocks show automatic WSI messages */}
                    {!block.editable ? (
                      WSI_AUTOMATIC_MESSAGES[block.id as keyof typeof WSI_AUTOMATIC_MESSAGES] ? (
                        <div className="rounded-xl border border-lia-border-default bg-lia-bg-secondary/50 overflow-hidden">
                          <div className="px-2.5 py-1.5 border-b border-lia-btn-primary-bg/10 bg-lia-bg-tertiary">
                            <p className="text-xs font-medium text-lia-text-primary">
                              {WSI_AUTOMATIC_MESSAGES[block.id].title}
                            </p>
                          </div>
                          <div className="p-2.5">
                            <div className="text-micro text-lia-text-primary leading-relaxed whitespace-pre-line">
                              {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                            </div>
                          </div>
                          <div className="px-2.5 py-1.5 border-t border-lia-btn-primary-bg/10 bg-lia-bg-secondary">
                            <p className="text-micro text-lia-text-secondary italic">
                              {WSI_AUTOMATIC_MESSAGES[block.id].note}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-2.5 bg-lia-bg-primary/60 border border-lia-border-subtle rounded-xl">
                          <p className="text-micro text-lia-text-secondary italic">
                            {block.description}
                          </p>
                          <p className="text-micro text-lia-text-secondary mt-1">
                            Gerenciado automaticamente pela LIA
                          </p>
                        </div>
                      )
                    ) : (
                      <>
                        {/* Questions in this block */}
                        {blockQuestions.length === 0 ? (
                          <div className="p-3 bg-lia-bg-secondary border border-lia-border-subtle border-dashed rounded-xl text-center">
                            <p className="text-micro text-lia-text-secondary">
                              Nenhuma pergunta neste bloco
                            </p>
                          </div>
                        ) : (
                          blockQuestions.map((item: ScreeningQuestion, idx: number) => (
                            <div 
                              key={item.id || idx} 
                              className="p-2 bg-lia-bg-primary border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none"
                            >
                              <div className="flex items-start gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                                    <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 flex items-center ${
 item.category === 'behavioral' || item.category === 'Comportamental'
                                        ? ' border border-wedo-purple/30'
                                        : item.category === 'technical' || item.category === 'Técnica'
                                        ? 'bg-lia-bg-tertiary text-wedo-cyan-text border border-lia-border-default'
                                        : ' border border-status-success/30'
                                    }`}>
                                      {item.category === 'behavioral' ? 'Comport.' 
                                        : item.category === 'technical' ? 'Técnica' 
                                        : item.category === 'cultural' ? 'Cultural'
                                        : item.category || 'Geral'}
                                    </Chip>
                                    {(item.type === 'eliminatory' || item.required) && (
                                      <Chip variant="danger" muted className="text-micro px-1.5 py-0 h-4 flex items-center">
                                        Eliminatória
                                      </Chip>
                                    )}
                                  </div>
                                  <p className="text-micro text-lia-text-primary leading-relaxed">
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
      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-3">
          <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
          Canais e Configurações
        </h5>

        {/* Canais em linha */}
        <div className="flex items-center gap-3 mb-3 pb-3">
          <span className="text-micro text-lia-text-secondary">Canais:</span>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(previewJob.screeningConfig?.channels?.whatsapp?.enabled ?? true) ? '' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
              <MessageSquare className="w-3 h-3" />
              <span className="text-micro font-medium">WhatsApp</span>
              {(previewJob.screeningConfig?.channels?.whatsapp?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
            </div>
            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(previewJob.screeningConfig?.channels?.chat_web?.enabled ?? true) ? '' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
              <Globe className="w-3 h-3" />
              <span className="text-micro font-medium">Chat Web</span>
              {(previewJob.screeningConfig?.channels?.chat_web?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
            </div>
            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(previewJob.screeningConfig?.channels?.phone?.enabled ?? false) ? '' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
              <Phone className="w-3 h-3" />
              <span className="text-micro font-medium">Telefone</span>
              {(previewJob.screeningConfig?.channels?.phone?.enabled ?? false) && <CheckCircle className="w-3 h-3" />}
            </div>
          </div>
        </div>

        {/* Configurações em grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center justify-between">
            <span className="text-micro text-lia-text-secondary">Score Mínimo</span>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">{previewJob.screeningConfig?.settings?.min_score ?? 70}%</Chip>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-lia-text-secondary">Timeout Resposta</span>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-primary">{previewJob.screeningConfig?.settings?.response_timeout_hours ?? 48}h</Chip>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-lia-text-secondary">Re-tentativas</span>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-primary">{previewJob.screeningConfig?.settings?.max_retries ?? 2}x</Chip>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-micro text-lia-text-secondary">Secundário</span>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">Revisão Manual</Chip>
          </div>
        </div>

        {/* Status Integrações */}
        <div className="flex items-center gap-3 mt-3 pt-2 border-t border-lia-border-subtle">
          <span className="text-micro text-lia-text-secondary">Integrações:</span>
          <div className="flex items-center gap-1 text-micro">
            <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>
            <span className="text-lia-text-secondary">OpenMic.ai</span>
          </div>
          <div className="flex items-center gap-1 text-micro">
            <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>
            <span className="text-lia-text-secondary">Deepgram</span>
          </div>
        </div>
      </div>

      {/* 5. Agendamento Automático */}
      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <CalendarCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
            <h5 className="text-xs font-semibold text-lia-text-primary">Agendamento Automático</h5>
          </div>
          <Chip variant={(previewJob.screeningConfig?.scheduling?.auto_enabled ?? true) ? "success" : "neutral"} muted={!(previewJob.screeningConfig?.scheduling?.auto_enabled ?? true)} className="text-micro px-1.5 py-0 h-4 flex items-center">
            {(previewJob.screeningConfig?.scheduling?.auto_enabled ?? true) ? 'Ativo' : 'Inativo'}
          </Chip>
        </div>
        <p className="text-micro text-lia-text-secondary mb-2">Aprovados na triagem são agendados automaticamente para entrevista</p>

        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-xl">
            <span className="text-micro text-lia-text-secondary">Score Mínimo</span>
            <span className="text-micro font-medium text-lia-text-primary">{previewJob.screeningConfig?.scheduling?.min_score_for_auto ?? 75}%</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-xl">
            <span className="text-micro text-lia-text-secondary">Calendário</span>
            <span className="text-micro font-medium text-lia-text-primary">{previewJob.screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-xl">
            <span className="text-micro text-lia-text-secondary">Horários</span>
            <span className="text-micro font-medium text-lia-text-primary">{previewJob.screeningConfig?.scheduling?.available_hours || '9h-18h'}</span>
          </div>
          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-xl">
            <span className="text-micro text-lia-text-secondary">Duração</span>
            <span className="text-micro font-medium text-lia-text-primary">{previewJob.screeningConfig?.scheduling?.interview_duration_min ?? 45}min</span>
          </div>
        </div>
      </div>

      {/* 6. Insights LIA */}
      <div className="p-2.5 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-micro font-medium text-lia-text-primary mb-1">Insights da LIA</p>
            <ul className="space-y-0.5 text-micro text-lia-text-secondary">
              <li>• Triagens 6.5x mais rápidas que processo manual</li>
              <li>• Economia estimada: {CURRENCY_SYMBOL} {(() => {
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
