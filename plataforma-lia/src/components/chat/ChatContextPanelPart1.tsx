"use client"

import React from"react"
import {
  DollarSign, Network, Target, Clock, Globe, CheckCircle, Edit,
  Download, Send
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
 * compensation-package, org-structure-analysis, role-scope-definition,
 * work-arrangement, final-job-description, job-publishing
 */
export function ChatContextPanelPart1({ contextData }: Props) {
   
  const data = contextData.data as any
  return (
    <>
      {contextData.type ==="compensation-package" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <DollarSign className="w-5 h-5 text-lia-text-secondary" />
                  <span className="text-lia-text-primary">Pacote de Compensação</span>
                </div>
                <Chip variant="neutral" className="border-lia-border-subtle text-lia-text-secondary">Inteligência de Mercado</Chip>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-xl bg-stone-50 dark:bg-stone-900/20">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm text-lia-text-secondary">Recomendação IA - Target</p>
                      <p className="text-xl font-semibold text-lia-text-primary">{data.recommended_package.base_salary.target}</p>
                    </div>
                    <Chip variant="neutral" muted className="bg-status-warning/10 dark:bg-status-warning/20 text-lia-text-primary">Percentil 90</Chip>
                  </div>
                  <p className="text-sm text-lia-text-secondary">{data.recommended_package.total_compensation.positioning}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Mediana de Mercado</h4>
                    <p className="text-lg font-semibold text-lia-text-primary">{data.market_analysis.salary_research.market_median}</p>
                  </div>
                  <div className="p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Faixa Recomendada</h4>
                    <p className="text-base font-semibold text-lia-text-primary">{data.recommended_package.base_salary.min} - {data.recommended_package.base_salary.max}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Pacote de Benefícios</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(data.recommended_package.benefits_package).map(([key, benefit]: [string, any]) => (
                      <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-tertiary">
                        <span className="text-sm font-medium capitalize">{key.replace('_', ' ')}</span>
                        <span className="text-sm font-semibold text-lia-text-primary">{benefit.estimated_value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Benchmarking Competitivo</h4>
                  <div className="space-y-2">
                    {(data.market_analysis as { benchmarking_companies: { company: string; notes: string; range: string }[] }).benchmarking_companies.map((company) => (
                      <div key={company.company} className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-tertiary">
                        <div>
                          <h5 className="font-medium text-lia-text-primary">{company.company}</h5>
                          <p className="text-sm text-lia-text-secondary">{company.notes}</p>
                        </div>
                        <Chip variant="neutral" className="border-lia-border-subtle">{company.range}</Chip>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                  <div className="flex items-center justify-between">
                    <span className="text-base font-semibold text-lia-text-primary">Compensação Total Anual</span>
                    <span className="text-xl font-semibold text-lia-text-primary">{data.recommended_package.total_compensation.total_annual}</span>
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Ajustar Valores</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Pacote</Button>
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary"><Download className="w-4 h-4 mr-2" />Exportar</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="org-structure-analysis" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3">
                <Network className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Análise da Estrutura Organizacional</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-xl bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h5 className="text-lg font-semibold mb-2 text-lia-text-primary">{data.current_structure.missing_layer.role}</h5>
                  <p className="text-sm mb-3 text-lia-text-secondary">{data.current_structure.missing_layer.purpose}</p>
                  <div className="p-3 rounded-xl bg-lia-bg-tertiary">
                    <p className="text-sm font-medium text-lia-text-primary">{data.current_structure.missing_layer.impact}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Visão Geral da Empresa</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between"><span className="text-sm text-lia-text-secondary">Porte:</span><span className="font-semibold text-lia-text-primary">{data.company_overview.size}</span></div>
                      <div className="flex justify-between"><span className="text-sm text-lia-text-secondary">Setor:</span><span className="font-semibold text-lia-text-primary">{data.company_overview.industry}</span></div>
                      <div className="flex justify-between"><span className="text-sm text-lia-text-secondary">Time Tech Atual:</span><span className="font-semibold text-lia-text-primary">{data.company_overview.current_tech_team} pessoas</span></div>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Projeção de Crescimento</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between"><span className="text-sm text-lia-text-secondary">6 meses:</span><span className="font-semibold text-lia-text-primary">{data.growth_projection.projected_6months} pessoas</span></div>
                      <div className="flex justify-between"><span className="text-sm text-lia-text-secondary">12 meses:</span><span className="font-semibold text-lia-text-primary">{data.growth_projection.projected_12months} pessoas</span></div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Estrutura</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Confirmar Análise</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="role-scope-definition" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3">
                <Target className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Definição do Escopo da Posição</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-xl bg-status-warning/10 dark:bg-status-warning/20">
                  <h4 className="text-sm font-medium mb-2 text-lia-text-secondary">Foco Principal</h4>
                  <p className="text-base font-bold text-lia-text-primary">{data.role_focus}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Responsabilidades Principais</h4>
                  <div className="space-y-2">
                    {data.key_responsibilities.map((responsibility: string) => (
                      <div key={responsibility} className="flex items-start space-x-3 p-3 rounded-md bg-status-success/10 dark:bg-status-success/20">
                        <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-lia-bg-secondary"></div>
                        <span className="text-sm text-lia-text-primary">{responsibility}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Escopo</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Definição</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="work-arrangement" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Clock className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Modelo de Trabalho Híbrido</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4 font-open-sans">
                <div className="grid grid-cols-2 gap-6">
                  <div><h4 className="text-sm font-medium text-lia-text-secondary mb-2">Modalidade</h4><p className="font-semibold">{data.arrangement}</p></div>
                  <div><h4 className="text-sm font-medium text-lia-text-secondary mb-2">Flexibilidade</h4><p className="font-semibold">{data.flexibility}</p></div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-2">Dias Presenciais</h4>
                    <div className="flex flex-wrap gap-1">{data.office_days.map((day: string, index: number) => (<Chip density="relaxed" key={`${index}-${day}`} variant="neutral" >{day}</Chip>))}</div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-2">Home Office</h4>
                    <div className="flex flex-wrap gap-1">{data.home_office_days.map((day: string, index: number) => (<Chip density="relaxed" key={`${index}-${day}`} variant="neutral" >{day}</Chip>))}</div>
                  </div>
                </div>
                <div><h4 className="text-sm font-medium text-lia-text-secondary mb-2">Benefícios Inclusos</h4><p className="text-sm text-lia-text-secondary">{data.benefits}</p></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="final-job-description" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Globe className="w-5 h-5 text-lia-text-secondary" />
                <span className="text-lia-text-primary">Job Description Completo</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-xl bg-pink-50 dark:bg-pink-900/20">
                  <h3 className="text-base font-semibold text-lia-text-primary">{data.header.title}</h3>
                  <p className="text-lia-text-secondary">{data.header.company} • {data.header.location}</p>
                  <p className="text-sm mt-2 text-lia-text-secondary">{data.header.salary_range}</p>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Responsabilidades Principais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.key_responsibilities).map(([key, items]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {items.slice(0, 2).map((item: string, i: number) => (<div key={`item-${i}`} className="flex items-start space-x-2 text-sm mb-1"><div className="w-1 h-1 bg-lia-border-medium rounded-full mt-2 flex-shrink-0"></div><span>{item}</span></div>))}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Qualificações Essenciais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.required_qualifications).map(([key, items]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {items.slice(0, 2).map((item: string, i: number) => (<div key={`item-${i}`} className="flex items-start space-x-2 text-sm mb-1"><CheckCircle className="w-3 h-3 text-lia-text-secondary mt-0.5 flex-shrink-0" /><span>{item}</span></div>))}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="border-t-0 pt-4">
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Pacote de Compensação</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div><p className="text-sm font-semibold text-lia-text-primary">{data.compensation_highlights.total_package.split(' ')[1]}</p><p className="text-xs text-lia-text-secondary">Total Anual</p></div>
                    <div><p className="text-sm font-medium">{data.compensation_highlights.variable_bonus}</p><p className="text-xs text-lia-text-secondary">Bônus Variável</p></div>
                    <div><p className="text-sm font-medium">{data.compensation_highlights.benefits_value}</p><p className="text-xs text-lia-text-secondary">Benefícios</p></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type ==="job-publishing" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-lia-bg-primary">
            <CardHeader className="bg-lia-bg-tertiary">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Globe className="w-5 h-5 text-lia-text-secondary" />
                  <span className="text-lia-text-primary">Publicação Multi-Canal</span>
                </div>
                <Chip variant="neutral" muted className="bg-status-success/10 dark:bg-status-success/20 text-lia-text-primary">{data.ats_integration.status}</Chip>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-xl bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-lia-text-secondary">Sistema ATS Integrado</p>
                      <h4 className="text-base font-semibold mt-1 text-lia-text-primary">{data.ats_integration.system}</h4>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-lia-text-secondary">Job ID</p>
                      <p className="text-sm font-mono font-semibold text-lia-text-primary">{data.ats_integration.job_id}</p>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Canais de Publicação</h4>
                  <div className="space-y-2">
                    {(data.publication_channels as { platform: string; reach: string; budget: string; status: string }[]).map((channel) => (
                      <div key={channel.platform} className="flex items-center justify-between p-4 rounded-xl bg-lia-bg-tertiary">
                        <div className="flex-1">
                          <h5 className="font-medium text-lia-text-primary">{channel.platform}</h5>
                          <p className="text-sm mt-1 text-lia-text-secondary">{channel.reach} • {channel.budget}</p>
                        </div>
                        <Chip variant="neutral" className="border-lia-border-subtle text-lia-text-primary">{channel.status}</Chip>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-lia-text-secondary mb-3">Metas de Sucesso</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(data.success_metrics.targets).map(([key, value]: [string, any]) => (
                      <div key={key} className="text-center p-4 rounded-xl border bg-lia-bg-tertiary border-lia-border-subtle">
                        <p className="text-lg font-semibold text-lia-text-primary">{String(value)}</p>
                        <p className="text-xs mt-1 capitalize text-lia-text-secondary">{key.replace('_', ' ')}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Canais</Button>
                  <Button className="flex-1 bg-status-success/10 dark:bg-status-success/20 text-lia-text-primary"><Send className="w-4 h-4 mr-2" />Publicar Vaga</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}
