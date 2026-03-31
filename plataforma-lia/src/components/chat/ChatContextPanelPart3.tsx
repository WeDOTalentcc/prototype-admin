// @ts-nocheck
"use client"

import React from "react"
import {
  Brain, FileText, Calendar, Target, CalendarDays, Workflow,
  Network, Briefcase, ArrowUpDown, CheckCircle, Edit, Send, Clock
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { PipelineReport } from "@/components/ui/pipeline-report"
import { ContextPanelData } from "@/types/chat"

interface Props {
  contextData: ContextPanelData
  onPipelineAction: (candidateId: string, actionId: string, candidateName: string) => Promise<void>
  onClose: () => void
}

/**
 * Renders context panel content for types:
 * predictive-insights, offer-letter, interview-scheduling,
 * technical-matrix, timeline, interview-flow, org-chart,
 * job-creation-progress, pipeline-report
 */
export function ChatContextPanelPart3({ contextData, onPipelineAction, onClose }: Props) {
  return (
    <>
      {contextData.type === "predictive-insights" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Brain className="w-5 h-5 text-wedo-cyan" />
                <span className="lia-text-950 dark:lia-text-50">Inteligência Preditiva</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-status-error/10 dark:bg-status-error/20">
                  <h4 className="font-medium mb-2 lia-text-800 dark:text-lia-text-primary">Base de Análise</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-wedo-cyan-dark dark:text-lia-text-secondary">Processos Históricos:</span><p className="font-semibold">{contextData.data.analysis_base.historical_processes}</p></div>
                    <div><span className="text-wedo-cyan-dark dark:text-lia-text-secondary">Pontos de Dados:</span><p className="font-semibold">{contextData.data.analysis_base.data_points.toLocaleString()}</p></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Predições de Melhoria</h4>
                  <div className="space-y-4 font-open-sans">
                    {(contextData.data.predictions as { category: string; confidence: number; current_performance: string; predicted_improvement: string; actions: string[] }[]).map((prediction) => (
                      <div key={prediction.category} className="p-4 rounded-md">
                        <div className="flex items-center justify-between mb-3">
                          <h5 className="font-medium lia-text-950 dark:lia-text-50">{prediction.category}</h5>
                          <Badge variant="outline" className="text-xs">{prediction.confidence}% confiança</Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                          <div><span className="lia-text-600">Atual:</span><p className="font-medium">{prediction.current_performance}</p></div>
                          <div><span className="lia-text-600">Predição:</span><p className="font-semibold lia-text-800 dark:text-lia-text-primary">{prediction.predicted_improvement}</p></div>
                        </div>
                        <div>
                          <span className="text-xs lia-text-600">Ações Recomendadas:</span>
                          <ul className="mt-1 space-y-1">
                            {prediction.actions.slice(0, 2).map((action: string, i: number) => (
                              <li key={`act-${i}`} className="flex items-start space-x-2 text-xs"><div className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0 bg-gray-500 dark:lia-bg-400"></div><span>{action}</span></li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Roadmap de Implementação</h4>
                  <div className="space-y-2">
                    {Object.entries(contextData.data.implementation_roadmap).map(([phase, description]: [string, any], index) => (
                      <div key={phase} className="flex items-center space-x-3 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary">{index + 1}</div>
                        <span className="text-sm">{description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "offer-letter" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center justify-between font-open-sans">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 lia-text-600" />
                  <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-stone-50 dark:bg-stone-900/20">
                  <h4 className="font-medium mb-3 lia-text-800 dark:text-lia-text-primary">Candidato</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Nome:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.candidate_info.name}</p></div>
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Email:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.candidate_info.email}</p></div>
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Telefone:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.candidate_info.phone}</p></div>
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Empresa Atual:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.candidate_info.current_company}</p></div>
                  </div>
                </div>
                <div className="p-6 rounded-md border bg-white dark:lia-bg-950 border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap font-open-sans text-sm lia-text-800 dark:text-lia-text-primary">{contextData.data.letter_template}</pre>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Revisar e Editar</Button>
                  <Button className="flex-1 bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary"><Send className="w-4 h-4 mr-2" />Enviar para Candidato</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "interview-scheduling" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Calendar className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Candidatos Selecionados</h4>
                  <div className="space-y-3">
                    {(contextData.data.candidates_to_schedule as { name: string; score: number; interview_type: string; preferred_times: string[] }[]).map((candidate) => (
                      <div key={candidate.name} className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                        <div className="flex justify-between items-start mb-2">
                          <div><h5 className="font-medium lia-text-800 dark:text-lia-text-primary">{candidate.name}</h5><p className="text-sm lia-text-500 dark:text-lia-text-tertiary">Score: {candidate.score}/100</p></div>
                          <Badge className="bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary">{candidate.interview_type}</Badge>
                        </div>
                        <div className="flex gap-2 text-xs lia-text-500 dark:text-lia-text-tertiary">
                          <span>Preferências:</span>
                          {candidate.preferred_times.map((time: string, i: number) => (<span key={`ptime-${i}`} className="px-2 py-1 rounded-md bg-white dark:lia-bg-950">{time}</span>))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Horários Disponíveis</h4>
                  <div className="space-y-4">
                    {Object.entries(contextData.data.available_slots as Record<string, { time: string; duration: string; available: boolean }[]>).map(([date, slots]) => (
                      <div key={date}>
                        <h5 className="text-sm font-medium mb-2 lia-text-800 dark:text-lia-text-primary">{date}</h5>
                        <div className="grid grid-cols-3 gap-2">
                          {slots.map((slot, i: number) => (
                            <button key={`slot-${i}-${slot.time}`} disabled={!slot.available}
                              className={`p-2 rounded-md text-xs transition-transform motion-reduce:transition-none ${slot.available ? 'hover:scale-105' : 'opacity-50 cursor-not-allowed'}`}
                              style={{backgroundColor: slot.available ? 'var(--green-50, #f0fdf4)' : 'var(--gray-100)', color: 'inherit', border: `1px solid ${slot.available ? 'var(--gray-200)' : 'var(--gray-100)'}`}}>
                              {slot.time}
                              <div className="text-xs lia-text-400 dark:lia-text-500">{slot.duration}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4 rounded-md bg-stone-50 dark:bg-stone-900/20">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Entrevistador:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.interviewer}</p></div>
                    <div><span className="lia-text-500 dark:text-lia-text-tertiary">Integração:</span><p className="font-medium lia-text-800 dark:text-lia-text-primary">{contextData.data.calendar_integration}</p></div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Ajustar Horários</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Confirmar Agendamentos</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "technical-matrix" && contextData.data && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Target className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary">{contextData.data}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "timeline" && contextData.data && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <CalendarDays className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary">{contextData.data}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "interview-flow" && contextData.data && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Workflow className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary">{contextData.data}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "org-chart" && contextData.data && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Network className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary">{contextData.data}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "job-creation-progress" && contextData.data && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Briefcase className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">{contextData.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-4 rounded-md bg-stone-50 dark:bg-stone-900/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">Progresso da Criação</span>
                    <span className="text-sm font-bold lia-text-800 dark:text-lia-text-primary">{contextData.data.completion_percentage}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-gray-100 dark:bg-lia-bg-secondary">
                    <div className="h-full rounded-full transition-[width,height] duration-500 bg-gray-700" style={{width: `${contextData.data.completion_percentage}%`}} />
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Status dos Campos</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {contextData.data.collected_fields?.map((field: string) => (
                      <div key={field} className="flex items-center gap-2 p-2 rounded-md bg-status-success/10 dark:bg-status-success/20">
                        <CheckCircle className="w-4 h-4 text-status-success" />
                        <span className="text-sm">{field}</span>
                      </div>
                    ))}
                    {contextData.data.pending_fields?.map((field: string) => (
                      <div key={`pending-${field}`} className="flex items-center gap-2 p-2 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <Clock className="w-4 h-4 lia-text-600" />
                        <span className="text-sm lia-text-600">{field}</span>
                      </div>
                    ))}
                  </div>
                </div>
                {contextData.data.next_panel && (
                  <div className="p-4 rounded-md border border-gray-400 bg-white dark:lia-bg-950">
                    <div className="flex items-start gap-3">
                      <ArrowUpDown className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary mt-0.5" />
                      <div>
                        <h4 className="text-sm font-semibold mb-1 lia-text-800 dark:text-lia-text-primary">Próximo Passo</h4>
                        <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">{contextData.data.next_panel}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "pipeline-report" && contextData.data && (
        <PipelineReport data={contextData.data} onAction={onPipelineAction} onClose={() => onClose()} />
      )}
    </>
  )
}
