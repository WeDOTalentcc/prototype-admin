"use client"

import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React from"react"
import {
  TrendingUp, Calendar, UserCheck, Workflow, Target, Award,
  CheckCircle, Edit, Download, Send, Eye
} from"lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { ContextPanelData } from"@/types/chat"

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
  const data = contextData.data as any  
  return (
    <>
      {contextData.type ==="sourcing-progress" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3">
                <TrendingUp className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Progress do Sourcing - Tempo Real</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="grid grid-cols-4 gap-3">
                  <div className="text-center p-4 rounded-xl bg-stone-50 dark:bg-stone-900/20"><p className="text-lg font-semibold text-lia-text-primary">{data.realtime_metrics.applications_received}</p><p className="text-xs mt-1 text-lia-text-secondary">Aplicações</p></div>
                  <div className="text-center p-4 rounded-xl bg-status-success/10 dark:bg-status-success/20"><p className="text-lg font-semibold text-lia-text-primary">{data.realtime_metrics.active_sourcing_reached}</p><p className="text-xs mt-1 text-lia-text-secondary">Sourcing Ativo</p></div>
                  <div className="text-center p-4 rounded-xl bg-status-error/10 dark:bg-status-error/20"><p className="text-lg font-semibold text-lia-text-primary">{data.realtime_metrics.response_rate}</p><p className="text-xs mt-1 text-lia-text-secondary">Taxa Resposta</p></div>
                  <div className="text-center p-4 rounded-xl bg-wedo-cyan/15 dark:bg-wedo-cyan/20"><p className="text-lg font-semibold text-lia-text-primary">{data.realtime_metrics.avg_candidate_score}</p><p className="text-xs mt-1 text-lia-text-secondary">Score Médio</p></div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Candidatos Top Performance</h4>
                  <div className="space-y-2">
                    {(data.top_candidates as { name: string; current_role: string; score: number; highlights: string[]; status: string }[]).map((candidate) => (
                      <div key={candidate.name} className="p-4 rounded-xl bg-lia-bg-tertiary">
                        <div className="flex items-center justify-between mb-3">
                          <div><h5 className="font-medium text-lia-text-primary">{candidate.name}</h5><p className="text-sm text-lia-text-secondary">{candidate.current_role}</p></div>
                          <Chip variant="neutral" muted className="bg-status-warning/10 dark:bg-status-warning/20 text-lia-text-primary">Nota: {candidate.score}</Chip>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {candidate.highlights.map((highlight: string, i: number) => (<Chip density="relaxed" key={`hl-${i}`} variant="neutral" className="border-lia-border-subtle">{highlight}</Chip>))}
                        </div>
                        <p className="text-xs text-lia-text-tertiary">Status: {candidate.status}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary bg-lia-bg-primary text-lia-text-primary"><Eye className="w-4 h-4 mr-2" />Ver Pipeline Completo</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 text-lia-text-primary"><Send className="w-4 h-4 mr-2" />Convidar Candidatos</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="interview-management" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Calendar className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Gestão de Entrevistas</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Cronograma de Screening</h4>
                  <div className="space-y-3 font-open-sans">
                    {(data.screening_schedule as { candidate: string; date: string; time: string; interviewer: string; status: string }[]).map((interview) => (
                      <div key={`${interview.candidate}-${interview.date}`} className="flex items-center justify-between p-3 rounded-md">
                        <div>
                          <h5 className="font-medium text-lia-text-primary">{interview.candidate}</h5>
                          <p className="text-sm text-lia-text-secondary">{interview.date} • {interview.time}</p>
                          <p className="text-xs text-lia-text-secondary">{interview.interviewer}</p>
                        </div>
                        <Chip variant="neutral" className={`border-lia-border-subtle ${interview.status === 'Confirmed' ? 'bg-green-50' : 'bg-yellow-50'}`}>{interview.status}</Chip>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Estrutura do Processo</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(data.interview_structure).map(([key, stage]: [string, any]) => (
                      <div key={key} className="p-3 bg-lia-bg-secondary rounded-xl">
                        <h5 className="font-medium capitalize mb-2">{key.replace('stage_', 'Etapa ').replace('_', ' ')}</h5>
                        <div className="text-sm space-y-1">
                          <p><span className="text-lia-text-secondary">Duração:</span> {stage.duration}</p>
                          <p><span className="text-lia-text-secondary">Entrevistador:</span> {stage.interviewer}</p>
                          <p><span className="text-lia-text-secondary">Critério:</span> {stage.success_criteria}</p>
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

      {contextData.type ==="final-selection" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <UserCheck className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Seleção Final</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-xl bg-status-success/10 dark:bg-status-success/20">
                  <h4 className="font-medium text-lia-text-primary">Candidato Selecionado: Carlos Mendonça</h4>
                  <p className="text-sm text-lia-text-secondary">Score Final: 94/100 • Cultural Fit: Excelente</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Processo de Finalização</h4>
                  <div className="space-y-3 font-open-sans">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-tertiary"><span className="text-sm font-medium">Referências Profissionais</span><Chip variant="neutral" muted className="bg-status-success/10 dark:bg-status-success/20 text-lia-text-primary">Concluído</Chip></div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-tertiary"><span className="text-sm font-medium">Background Check</span><Chip variant="neutral" muted className="bg-status-success/10 dark:bg-status-success/20 text-lia-text-primary">Aprovado</Chip></div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-tertiary"><span className="text-sm font-medium">Proposta Salarial</span><Chip variant="neutral" muted className="bg-wedo-cyan/15 dark:bg-wedo-cyan/20 text-lia-text-primary">Aceita</Chip></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Detalhes da Contratação</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div><p className="text-xs text-lia-text-secondary mb-1">Data de Início:</p><p className="font-medium">15 de Março, 2024</p></div>
                    <div><p className="text-xs text-lia-text-secondary mb-1">Salário Negociado:</p><p className="font-semibold text-lia-text-primary">{CURRENCY_SYMBOL} 47.500</p></div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Revisar Proposta</Button>
                  <Button className="flex-1 bg-status-success/10 dark:bg-status-success/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Confirmar Seleção</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="onboarding-plan" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Workflow className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Plano de Onboarding</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-5 rounded-xl bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h4 className="text-base font-semibold mb-2 text-lia-text-primary">Programa de 90 Dias</h4>
                  <p className="text-sm text-lia-text-secondary">Integração estratégica e cultural personalizada</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Primeiros 30 Dias</h4>
                  <div className="space-y-2">
                    {['Imersão na cultura e processos da empresa', 'Reuniões 1:1 com stakeholders principais', 'Análise do estado atual da infraestrutura TI'].map((item, i) => (
                      <div key={i} className="flex items-start space-x-3 p-3 rounded-xl bg-lia-bg-tertiary"><div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-lia-bg-secondary"></div><span className="text-sm">{item}</span></div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">60-90 Dias</h4>
                  <div className="space-y-2">
                    {['Apresentação do plano estratégico de transformação digital', 'Início das primeiras iniciativas de melhoria'].map((item, i) => (
                      <div key={i} className="flex items-start space-x-3 p-3 rounded-xl bg-lia-bg-tertiary"><div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-lia-bg-secondary"></div><span className="text-sm">{item}</span></div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Cronograma</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Plano</Button>
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary bg-lia-bg-primary text-lia-text-primary"><Download className="w-4 h-4 mr-2" />Exportar PDF</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="performance-management" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Target className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Gestão de Performance</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-xl bg-status-warning/10 dark:bg-status-warning/20">
                  <h4 className="font-medium text-lia-text-primary">Framework de Avaliação Anual</h4>
                  <p className="text-sm text-lia-text-secondary">OKRs + 360-feedback + desenvolvimento contínuo</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">OKRs do Primeiro Ano</h4>
                  <div className="space-y-3 font-open-sans">
                    {[
                      { title: 'Objetivo 1: Transformação Digital', desc: 'Migrar 80% dos sistemas para cloud em 12 meses' },
                      { title: 'Objetivo 2: Crescimento da Equipe', desc: 'Escalar equipe de 45 para 75 pessoas com 95% de retenção' },
                      { title: 'Objetivo 3: Excelência Operacional', desc: 'Reduzir downtime em 50% e implementar monitoramento avançado' },
                    ].map((obj, i) => (
                      <div key={i} className="p-3 rounded-md">
                        <h5 className="font-medium text-lia-text-primary">{obj.title}</h5>
                        <p className="text-sm text-lia-text-secondary">{obj.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Cronograma de Reviews</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-lia-bg-secondary rounded-xl"><p className="text-sm font-semibold">30 dias</p><p className="text-xs text-lia-text-secondary">Check-in inicial</p></div>
                    <div className="p-3 bg-lia-bg-secondary rounded-xl"><p className="text-sm font-semibold">90 dias</p><p className="text-xs text-lia-text-secondary">Avaliação onboarding</p></div>
                    <div className="p-3 bg-lia-bg-secondary rounded-xl"><p className="text-sm font-semibold">12 meses</p><p className="text-xs text-lia-text-secondary">Review anual</p></div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Ajustar OKRs</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Framework</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="journey-summary" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Award className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Relatório Executivo Final</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-xl bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h3 className="text-base font-semibold mb-3 text-lia-text-primary">Sumário Executivo</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div><p className="text-xs text-lia-text-secondary mb-1">Posição:</p><p className="font-medium">{data.executive_summary.position}</p></div>
                    <div><p className="text-xs text-lia-text-secondary mb-1">ROI Projetado:</p><p className="font-semibold text-lia-text-primary">{data.executive_summary.roi_projection}</p></div>
                    <div><p className="text-xs text-lia-text-secondary mb-1">Investimento Total:</p><p className="font-medium">{data.executive_summary.total_investment}</p></div>
                    <div><p className="text-xs text-lia-text-secondary mb-1">Probabilidade Sucesso:</p><p className="font-semibold text-lia-text-primary">{data.executive_summary.success_probability}</p></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Fases da Jornada</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(data.journey_phases).map(([key, phase]: [string, any]) => (
                      <div key={key} className="p-3 rounded-md">
                        <h5 className="font-medium capitalize mb-2">{key.replace('phase_', 'Fase ').replace('_', ' ')}</h5>
                        <p className="text-sm text-lia-text-secondary mb-2">Duração: {phase.duration}</p>
                        <div className="space-y-1">
                          {phase.activities.slice(0, 2).map((activity: string, i: number) => (
                            <div key={`phact-${i}`} className="flex items-start space-x-2 text-xs"><div className="w-1 h-1 bg-lia-border-medium rounded-full mt-1.5 flex-shrink-0"></div><span>{activity}</span></div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Resultados Mensuráveis</h4>
                    <div className="space-y-2">
                      {Object.entries(data.measurable_results).slice(0, 4).map(([key, value]: [string, any]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-sm text-lia-text-secondary capitalize">{key.replace('_', ' ')}:</span>
                          <span className="text-sm font-medium">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Inovações Principais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.key_innovations).map(([key, innovations]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {innovations.slice(0, 2).map((innovation: string, i: number) => (
                            <div key={`innov-${i}`} className="flex items-start space-x-2 text-xs mb-1"><CheckCircle className="w-3 h-3 text-lia-text-secondary mt-0.5 flex-shrink-0" /><span>{innovation}</span></div>
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
