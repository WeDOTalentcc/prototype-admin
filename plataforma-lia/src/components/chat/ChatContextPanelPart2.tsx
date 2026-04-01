"use client"

import React from "react"
import {
  TrendingUp, Calendar, UserCheck, Workflow, Target, Award,
  CheckCircle, Edit, Download, Send, Eye
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ContextPanelData } from "@/types/chat"

interface Props {
  contextData: ContextPanelData
}

/**
 * Renders context panel content for types:
 * sourcing-progress, interview-management, final-selection,
 * onboarding-plan, performance-management, journey-summary
 */
export function ChatContextPanelPart2({ contextData }: Props) {
  // TODO: fix type - cast contextData.data for dynamic data access
  const data = contextData.data as any // eslint-disable-line @typescript-eslint/no-explicit-any
  return (
    <>
      {contextData.type === "sourcing-progress" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3">
                <TrendingUp className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Progress do Sourcing - Tempo Real</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="grid grid-cols-4 gap-3">
                  // @ts-ignore // TODO: fix type
                  <div className="text-center p-4 rounded-md bg-stone-50 dark:bg-stone-900/20"><p className="text-lg font-bold lia-text-800 dark:text-lia-text-primary">{data.realtime_metrics.applications_received}</p><p className="text-xs mt-1 lia-text-500 dark:text-lia-text-tertiary">Aplicações</p></div>
                  // @ts-ignore // TODO: fix type
                  <div className="text-center p-4 rounded-md bg-status-success/10 dark:bg-status-success/20"><p className="text-lg font-bold lia-text-800 dark:text-lia-text-primary">{data.realtime_metrics.active_sourcing_reached}</p><p className="text-xs mt-1 lia-text-500 dark:text-lia-text-tertiary">Sourcing Ativo</p></div>
                  <div className="text-center p-4 rounded-md bg-status-error/10 dark:bg-status-error/20"><p className="text-lg font-bold lia-text-800 dark:text-lia-text-primary">{data.realtime_metrics.response_rate}</p><p className="text-xs mt-1 lia-text-500 dark:text-lia-text-tertiary">Taxa Resposta</p></div>
                  <div className="text-center p-4 rounded-md bg-wedo-cyan/15 dark:bg-wedo-cyan/20"><p className="text-lg font-bold lia-text-800 dark:text-lia-text-primary">{data.realtime_metrics.avg_candidate_score}</p><p className="text-xs mt-1 lia-text-500 dark:text-lia-text-tertiary">Score Médio</p></div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Candidatos Top Performance</h4>
                  <div className="space-y-2">
                    {(data.top_candidates as { name: string; current_role: string; score: number; highlights: string[]; status: string }[]).map((candidate) => (
                      <div key={candidate.name} className="p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <div className="flex items-center justify-between mb-3">
                          <div><h5 className="font-medium lia-text-800 dark:text-lia-text-primary">{candidate.name}</h5><p className="text-sm lia-text-500 dark:text-lia-text-tertiary">{candidate.current_role}</p></div>
                          <Badge className="bg-status-warning/10 dark:bg-status-warning/20 lia-text-800 dark:text-lia-text-primary">Score: {candidate.score}</Badge>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {candidate.highlights.map((highlight: string, i: number) => (<Badge key={`hl-${i}`} variant="outline" className="text-xs border-lia-border-subtle dark:border-lia-border-subtle">{highlight}</Badge>))}
                        </div>
                        <p className="text-xs lia-text-400 dark:lia-text-500">Status: {candidate.status}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Eye className="w-4 h-4 mr-2" />Ver Pipeline Completo</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary"><Send className="w-4 h-4 mr-2" />Convidar Candidatos</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "interview-management" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Calendar className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Gestão de Entrevistas</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Cronograma de Screening</h4>
                  <div className="space-y-3 font-open-sans">
                    {(data.screening_schedule as { candidate: string; date: string; time: string; interviewer: string; status: string }[]).map((interview) => (
                      <div key={`${interview.candidate}-${interview.date}`} className="flex items-center justify-between p-3 rounded-md">
                        <div>
                          <h5 className="font-medium lia-text-950 dark:lia-text-50">{interview.candidate}</h5>
                          <p className="text-sm lia-text-600">{interview.date} • {interview.time}</p>
                          <p className="text-xs lia-text-600">{interview.interviewer}</p>
                        </div>
                        <Badge variant="outline" style={{backgroundColor: interview.status === 'Confirmed' ? 'var(--green-50, #f0fdf4)' : 'var(--yellow-50, #fefce8)', borderColor: 'var(--gray-200)'}}>{interview.status}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Estrutura do Processo</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(data.interview_structure).map(([key, stage]: [string, any]) => (
                      <div key={key} className="p-3 bg-gray-50 dark:bg-lia-bg-elevated rounded-md">
                        <h5 className="font-medium capitalize mb-2">{key.replace('stage_', 'Etapa ').replace('_', ' ')}</h5>
                        <div className="text-sm space-y-1">
                          <p><span className="lia-text-600">Duração:</span> {stage.duration}</p>
                          <p><span className="lia-text-600">Entrevistador:</span> {stage.interviewer}</p>
                          <p><span className="lia-text-600">Critério:</span> {stage.success_criteria}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "final-selection" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <UserCheck className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Seleção Final</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-status-success/10 dark:bg-status-success/20">
                  <h4 className="font-medium lia-text-800 dark:text-lia-text-primary">Candidato Selecionado: Carlos Mendonça</h4>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">Score Final: 94/100 • Cultural Fit: Excelente</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Processo de Finalização</h4>
                  <div className="space-y-3 font-open-sans">
                    <div className="flex items-center justify-between p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"><span className="text-sm font-medium">Referências Profissionais</span><Badge className="bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary">Concluído</Badge></div>
                    <div className="flex items-center justify-between p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"><span className="text-sm font-medium">Background Check</span><Badge className="bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary">Aprovado</Badge></div>
                    <div className="flex items-center justify-between p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"><span className="text-sm font-medium">Proposta Salarial</span><Badge className="bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary">Aceita</Badge></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Detalhes da Contratação</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div><p className="text-xs lia-text-600 mb-1">Data de Início:</p><p className="font-medium">15 de Março, 2024</p></div>
                    <div><p className="text-xs lia-text-600 mb-1">Salário Negociado:</p><p className="font-semibold lia-text-800 dark:text-lia-text-primary">R$ 47.500</p></div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Revisar Proposta</Button>
                  <Button className="flex-1 bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Confirmar Seleção</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "onboarding-plan" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Workflow className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Plano de Onboarding</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-5 rounded-md bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h4 className="text-base font-bold mb-2 lia-text-800 dark:text-lia-text-primary">Programa de 90 Dias</h4>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">Integração estratégica e cultural personalizada</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Primeiros 30 Dias</h4>
                  <div className="space-y-2">
                    {['Imersão na cultura e processos da empresa', 'Reuniões 1:1 com stakeholders principais', 'Análise do estado atual da infraestrutura TI'].map((item, i) => (
                      <div key={i} className="flex items-start space-x-3 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"><div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-gray-500 dark:lia-bg-400"></div><span className="text-sm">{item}</span></div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">60-90 Dias</h4>
                  <div className="space-y-2">
                    {['Apresentação do plano estratégico de transformação digital', 'Início das primeiras iniciativas de melhoria'].map((item, i) => (
                      <div key={i} className="flex items-start space-x-3 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"><div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-gray-500 dark:lia-bg-400"></div><span className="text-sm">{item}</span></div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Cronograma</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Plano</Button>
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Download className="w-4 h-4 mr-2" />Exportar PDF</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "performance-management" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Target className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Gestão de Performance</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-status-warning/10 dark:bg-status-warning/20">
                  <h4 className="font-medium lia-text-800 dark:text-lia-text-primary">Framework de Avaliação Anual</h4>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">OKRs + 360-feedback + desenvolvimento contínuo</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">OKRs do Primeiro Ano</h4>
                  <div className="space-y-3 font-open-sans">
                    {[
                      { title: 'Objetivo 1: Transformação Digital', desc: 'Migrar 80% dos sistemas para cloud em 12 meses' },
                      { title: 'Objetivo 2: Crescimento da Equipe', desc: 'Escalar equipe de 45 para 75 pessoas com 95% de retenção' },
                      { title: 'Objetivo 3: Excelência Operacional', desc: 'Reduzir downtime em 50% e implementar monitoramento avançado' },
                    ].map((obj, i) => (
                      <div key={i} className="p-3 rounded-md">
                        <h5 className="font-medium lia-text-950 dark:lia-text-50">{obj.title}</h5>
                        <p className="text-sm lia-text-600">{obj.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Cronograma de Reviews</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-elevated rounded-md"><p className="text-sm font-semibold">30 dias</p><p className="text-xs lia-text-600">Check-in inicial</p></div>
                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-elevated rounded-md"><p className="text-sm font-semibold">90 dias</p><p className="text-xs lia-text-600">Avaliação onboarding</p></div>
                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-elevated rounded-md"><p className="text-sm font-semibold">12 meses</p><p className="text-xs lia-text-600">Review anual</p></div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Ajustar OKRs</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Framework</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "journey-summary" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Award className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Relatório Executivo Final</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h3 className="text-base font-semibold mb-3 lia-text-800 dark:text-lia-text-primary">Sumário Executivo</h3>
                  <div className="grid grid-cols-2 gap-4">
                    // @ts-ignore // TODO: fix type
                    <div><p className="text-xs lia-text-600 mb-1">Posição:</p><p className="font-medium">{data.executive_summary.position}</p></div>
                    <div><p className="text-xs lia-text-600 mb-1">ROI Projetado:</p><p className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.executive_summary.roi_projection}</p></div>
                    // @ts-ignore // TODO: fix type
                    <div><p className="text-xs lia-text-600 mb-1">Investimento Total:</p><p className="font-medium">{data.executive_summary.total_investment}</p></div>
                    // @ts-ignore // TODO: fix type
                    <div><p className="text-xs lia-text-600 mb-1">Probabilidade Sucesso:</p><p className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.executive_summary.success_probability}</p></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Fases da Jornada</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(data.journey_phases).map(([key, phase]: [string, any]) => (
                      <div key={key} className="p-3 rounded-md">
                        <h5 className="font-medium capitalize mb-2">{key.replace('phase_', 'Fase ').replace('_', ' ')}</h5>
                        <p className="text-sm lia-text-600 dark:text-lia-text-tertiary mb-2">Duração: {phase.duration}</p>
                        <div className="space-y-1">
                          {phase.activities.slice(0, 2).map((activity: string, i: number) => (
                            <div key={`phact-${i}`} className="flex items-start space-x-2 text-xs"><div className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></div><span>{activity}</span></div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Resultados Mensuráveis</h4>
                    <div className="space-y-2">
                      {Object.entries(data.measurable_results).slice(0, 4).map(([key, value]: [string, any]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-sm lia-text-600 dark:text-lia-text-tertiary capitalize">{key.replace('_', ' ')}:</span>
                          <span className="text-sm font-medium">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Inovações Principais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.key_innovations).map(([key, innovations]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium lia-text-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {innovations.slice(0, 2).map((innovation: string, i: number) => (
                            <div key={`innov-${i}`} className="flex items-start space-x-2 text-xs mb-1"><CheckCircle className="w-3 h-3 lia-text-600 dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" /><span>{innovation}</span></div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}
