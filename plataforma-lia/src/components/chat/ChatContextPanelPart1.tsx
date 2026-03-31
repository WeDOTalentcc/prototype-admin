"use client"

import React from "react"
import {
  DollarSign, Network, Target, Clock, Globe, CheckCircle, Edit,
  Download, Send
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
 * compensation-package, org-structure-analysis, role-scope-definition,
 * work-arrangement, final-job-description, job-publishing
 */
export function ChatContextPanelPart1({ contextData }: Props) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = contextData.data as any
  return (
    <>
      {contextData.type === "compensation-package" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <DollarSign className="w-5 h-5 lia-text-600" />
                  <span className="lia-text-950 dark:lia-text-50">Pacote de Compensação</span>
                </div>
                <Badge variant="outline" className="border-lia-border-subtle dark:border-lia-border-subtle lia-text-500 dark:text-lia-text-tertiary">Inteligência de Mercado</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-md bg-stone-50 dark:bg-stone-900/20">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">Recomendação LIA - Target</p>
                      <p className="text-xl font-bold lia-text-800 dark:text-lia-text-primary">{data.recommended_package.base_salary.target}</p>
                    </div>
                    <Badge className="bg-status-warning/10 dark:bg-status-warning/20 lia-text-800 dark:text-lia-text-primary">Percentil 90</Badge>
                  </div>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">{data.recommended_package.total_compensation.positioning}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Mediana de Mercado</h4>
                    <p className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">{data.market_analysis.salary_research.market_median}</p>
                  </div>
                  <div className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Faixa Recomendada</h4>
                    <p className="text-base font-semibold lia-text-800 dark:text-lia-text-primary">{data.recommended_package.base_salary.min} - {data.recommended_package.base_salary.max}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Pacote de Benefícios</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(data.recommended_package.benefits_package).map(([key, benefit]: [string, any]) => (
                      <div key={key} className="flex items-center justify-between p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <span className="text-sm font-medium capitalize">{key.replace('_', ' ')}</span>
                        <span className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary">{benefit.estimated_value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Benchmarking Competitivo</h4>
                  <div className="space-y-2">
                    {(data.market_analysis as { benchmarking_companies: { company: string; notes: string; range: string }[] }).benchmarking_companies.map((company) => (
                      <div key={company.company} className="flex items-center justify-between p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <div>
                          <h5 className="font-medium lia-text-800 dark:text-lia-text-primary">{company.company}</h5>
                          <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">{company.notes}</p>
                        </div>
                        <Badge variant="outline" className="border-lia-border-subtle dark:border-lia-border-subtle">{company.range}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center justify-between">
                    <span className="text-base font-semibold lia-text-800 dark:text-lia-text-primary">Compensação Total Anual</span>
                    <span className="text-xl font-bold lia-text-800 dark:text-lia-text-primary">{data.recommended_package.total_compensation.total_annual}</span>
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Ajustar Valores</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Pacote</Button>
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Download className="w-4 h-4 mr-2" />Exportar</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "org-structure-analysis" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3">
                <Network className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Análise da Estrutura Organizacional</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-md bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <h5 className="text-lg font-bold mb-2 lia-text-800 dark:text-lia-text-primary">{data.current_structure.missing_layer.role}</h5>
                  <p className="text-sm mb-3 lia-text-500 dark:text-lia-text-tertiary">{data.current_structure.missing_layer.purpose}</p>
                  <div className="p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                    <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{data.current_structure.missing_layer.impact}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Visão Geral da Empresa</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between"><span className="text-sm lia-text-500 dark:text-lia-text-tertiary">Porte:</span><span className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.company_overview.size}</span></div>
                      <div className="flex justify-between"><span className="text-sm lia-text-500 dark:text-lia-text-tertiary">Setor:</span><span className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.company_overview.industry}</span></div>
                      <div className="flex justify-between"><span className="text-sm lia-text-500 dark:text-lia-text-tertiary">Time Tech Atual:</span><span className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.company_overview.current_tech_team} pessoas</span></div>
                    </div>
                  </div>
                  <div className="p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Projeção de Crescimento</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between"><span className="text-sm lia-text-500 dark:text-lia-text-tertiary">6 meses:</span><span className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.growth_projection.projected_6months} pessoas</span></div>
                      <div className="flex justify-between"><span className="text-sm lia-text-500 dark:text-lia-text-tertiary">12 meses:</span><span className="font-semibold lia-text-800 dark:text-lia-text-primary">{data.growth_projection.projected_12months} pessoas</span></div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Estrutura</Button>
                  <Button className="flex-1 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Confirmar Análise</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "role-scope-definition" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3">
                <Target className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Definição do Escopo da Posição</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-md bg-status-warning/10 dark:bg-status-warning/20">
                  <h4 className="text-sm font-medium mb-2 lia-text-500 dark:text-lia-text-tertiary">Foco Principal</h4>
                  <p className="text-base font-bold lia-text-800 dark:text-lia-text-primary">{data.role_focus}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Responsabilidades Principais</h4>
                  <div className="space-y-2">
                    {data.key_responsibilities.map((responsibility: string) => (
                      <div key={responsibility} className="flex items-start space-x-3 p-3 rounded-md bg-status-success/10 dark:bg-status-success/20">
                        <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-gray-500 dark:lia-bg-400"></div>
                        <span className="text-sm lia-text-800 dark:text-lia-text-primary">{responsibility}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Escopo</Button>
                  <Button className="flex-1 bg-status-warning/10 dark:bg-status-warning/20 lia-text-800 dark:text-lia-text-primary"><CheckCircle className="w-4 h-4 mr-2" />Aprovar Definição</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "work-arrangement" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Clock className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Modelo de Trabalho Híbrido</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4 font-open-sans">
                <div className="grid grid-cols-2 gap-6">
                  <div><h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-2">Modalidade</h4><p className="font-semibold">{data.arrangement}</p></div>
                  <div><h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-2">Flexibilidade</h4><p className="font-semibold">{data.flexibility}</p></div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-2">Dias Presenciais</h4>
                    <div className="flex flex-wrap gap-1">{data.office_days.map((day: string, index: number) => (<Badge key={`${index}-${day}`} variant="outline" className="text-xs">{day}</Badge>))}</div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-2">Home Office</h4>
                    <div className="flex flex-wrap gap-1">{data.home_office_days.map((day: string, index: number) => (<Badge key={`${index}-${day}`} variant="outline" className="text-xs">{day}</Badge>))}</div>
                  </div>
                </div>
                <div><h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-2">Benefícios Inclusos</h4><p className="text-sm lia-text-600 dark:text-lia-text-tertiary">{data.benefits}</p></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "final-job-description" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center space-x-3 font-open-sans">
                <Globe className="w-5 h-5 lia-text-600" />
                <span className="lia-text-950 dark:lia-text-50">Job Description Completo</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6 font-open-sans">
                <div className="p-4 rounded-md bg-pink-50 dark:bg-pink-900/20">
                  <h3 className="text-base font-semibold lia-text-800 dark:text-lia-text-primary">{data.header.title}</h3>
                  <p className="lia-text-500 dark:text-lia-text-tertiary">{data.header.company} • {data.header.location}</p>
                  <p className="text-sm mt-2 lia-text-500 dark:text-lia-text-tertiary">{data.header.salary_range}</p>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Responsabilidades Principais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.key_responsibilities).map(([key, items]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium lia-text-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {items.slice(0, 2).map((item: string, i: number) => (<div key={`item-${i}`} className="flex items-start space-x-2 text-sm mb-1"><div className="w-1 h-1 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div><span>{item}</span></div>))}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Qualificações Essenciais</h4>
                    <div className="space-y-2">
                      {Object.entries(data.required_qualifications).map(([key, items]: [string, any]) => (
                        <div key={key}>
                          <h5 className="text-xs font-medium lia-text-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                          {items.slice(0, 2).map((item: string, i: number) => (<div key={`item-${i}`} className="flex items-start space-x-2 text-sm mb-1"><CheckCircle className="w-3 h-3 lia-text-600 mt-0.5 flex-shrink-0" /><span>{item}</span></div>))}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="border-t-0 pt-4">
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Pacote de Compensação</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div><p className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary">{data.compensation_highlights.total_package.split(' ')[1]}</p><p className="text-xs lia-text-600">Total Anual</p></div>
                    <div><p className="text-sm font-medium">{data.compensation_highlights.variable_bonus}</p><p className="text-xs lia-text-600">Bônus Variável</p></div>
                    <div><p className="text-sm font-medium">{data.compensation_highlights.benefits_value}</p><p className="text-xs lia-text-600">Benefícios</p></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {contextData.type === "job-publishing" && (
        <div className="space-y-6 font-open-sans">
          <Card className="border-0 bg-white dark:lia-bg-950">
            <CardHeader className="bg-gray-100 dark:bg-lia-bg-secondary">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Globe className="w-5 h-5 lia-text-600" />
                  <span className="lia-text-950 dark:lia-text-50">Publicação Multi-Canal</span>
                </div>
                <Badge className="bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary">{data.ats_integration.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="p-5 rounded-md bg-wedo-cyan/15 dark:bg-wedo-cyan/20">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium lia-text-500 dark:text-lia-text-tertiary">Sistema ATS Integrado</p>
                      <h4 className="text-base font-bold mt-1 lia-text-800 dark:text-lia-text-primary">{data.ats_integration.system}</h4>
                    </div>
                    <div className="text-right">
                      <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">Job ID</p>
                      <p className="text-sm font-mono font-semibold lia-text-800 dark:text-lia-text-primary">{data.ats_integration.job_id}</p>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Canais de Publicação</h4>
                  <div className="space-y-2">
                    {(data.publication_channels as { platform: string; reach: string; budget: string; status: string }[]).map((channel) => (
                      <div key={channel.platform} className="flex items-center justify-between p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <div className="flex-1">
                          <h5 className="font-medium lia-text-800 dark:text-lia-text-primary">{channel.platform}</h5>
                          <p className="text-sm mt-1 lia-text-500 dark:text-lia-text-tertiary">{channel.reach} • {channel.budget}</p>
                        </div>
                        <Badge variant="outline" className="border-lia-border-subtle dark:border-lia-border-subtle lia-text-800 dark:text-lia-text-primary">{channel.status}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary mb-3">Metas de Sucesso</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(data.success_metrics.targets).map(([key, value]: [string, any]) => (
                      <div key={key} className="text-center p-4 rounded-md border bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                        <p className="text-lg font-bold lia-text-800 dark:text-lia-text-primary">{String(value)}</p>
                        <p className="text-xs mt-1 capitalize lia-text-500 dark:text-lia-text-tertiary">{key.replace('_', ' ')}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 border border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"><Edit className="w-4 h-4 mr-2" />Editar Canais</Button>
                  <Button className="flex-1 bg-status-success/10 dark:bg-status-success/20 lia-text-800 dark:text-lia-text-primary"><Send className="w-4 h-4 mr-2" />Publicar Vaga</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}
