"use client"

import React from "react"
import {
  DollarSign, Network, Target, Clock, FileText, Globe, TrendingUp, Calendar,
  UserCheck, Workflow, Award, Brain, ArrowUpDown, CheckCircle, Edit,
  Download, Send, Eye, Briefcase, CalendarDays, X
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { PipelineReport } from "@/components/ui/pipeline-report"
import { ContextPanelData } from "@/types/chat"

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

interface Props {
  contextData: ContextPanelData | null
  isPanelOpen: boolean
  onClose: () => void
  onPipelineAction: (candidateId: string, actionId: string, candidateName: string) => Promise<void>
}

// ──────────────────────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────────────────────

export function ChatContextPanel({ contextData, isPanelOpen, onClose, onPipelineAction }: Props) {
  if (!contextData || !isPanelOpen) return null

  return (
      <div className="w-2/5 p-4 flex transition-all duration-300 overflow-hidden" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
        {/* Card Container com bordas suaves e arredondadas */}
        <Card className="w-full border-0 rounded-md overflow-hidden flex flex-col" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
          {/* Header sem linha divisória */}
          <CardHeader className="p-6 border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                  {contextData.title}
                </h3>
                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Powered by LIA Intelligence
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onClose()}
                className="rounded-full"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>

          {/* Content Area com scroll suave e altura flexível */}
          <CardContent
            className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500"
            style={{ scrollBehavior: 'smooth' }}
          >
          {contextData.type === "compensation-package" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <DollarSign className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">Pacote de Compensação</span>
                    </div>
                    <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)', color: 'var(--eleven-text-secondary)' }}>
                      Inteligência de Mercado
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight Card */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Recomendação LIA - Target</p>
                          <p className="text-xl font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.recommended_package.base_salary.target}
                          </p>
                        </div>
                        <Badge style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                          Percentil 90
                        </Badge>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {contextData.data.recommended_package.total_compensation.positioning}
                      </p>
                    </div>

                    {/* Benchmarking Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Mediana de Mercado</h4>
                        <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.market_analysis.salary_research.market_median}
                        </p>
                      </div>
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Faixa Recomendada</h4>
                        <p className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.recommended_package.base_salary.min} - {contextData.data.recommended_package.base_salary.max}
                        </p>
                      </div>
                    </div>

                    {/* Benefits */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Pacote de Benefícios</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(contextData.data.recommended_package.benefits_package).map(([key, benefit]: [string, any], index) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <span className="text-sm font-medium capitalize">{key.replace('_', ' ')}</span>
                            <span className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{benefit.estimated_value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Benchmarking Companies */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Benchmarking Competitivo</h4>
                      <div className="space-y-2">
                        {contextData.data.market_analysis.benchmarking_companies.map((company: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div>
                              <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{company.company}</h5>
                              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>{company.notes}</p>
                            </div>
                            <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)' }}>{company.range}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Total Compensation */}
                    <div className="p-4 rounded-md border-2" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                      <div className="flex items-center justify-between">
                        <span className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>Compensação Total Anual</span>
                        <span className="text-xl font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.recommended_package.total_compensation.total_annual}
                        </span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar Valores
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Pacote
                      </Button>
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "org-structure-analysis" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <Network className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Análise da Estrutura Organizacional</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight Card - Missing Layer */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h5 className="text-lg font-bold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
                        {contextData.data.current_structure.missing_layer.role}
                      </h5>
                      <p className="text-sm mb-3" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {contextData.data.current_structure.missing_layer.purpose}
                      </p>
                      <div className="p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                        <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.current_structure.missing_layer.impact}
                        </p>
                      </div>
                    </div>

                    {/* Company Overview Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Visão Geral da Empresa</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Porte:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.size}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Setor:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.industry}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Time Tech Atual:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.current_tech_team} pessoas
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Projeção de Crescimento</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>6 meses:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.growth_projection.projected_6months} pessoas
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>12 meses:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.growth_projection.projected_12months} pessoas
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Estrutura
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Análise
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "role-scope-definition" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <Target className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Definição do Escopo da Posição</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight - Main Focus */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-gold)' }}>
                      <h4 className="text-sm font-medium mb-2" style={{ color: 'var(--eleven-text-secondary)' }}>Foco Principal</h4>
                      <p className="text-base font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                        {contextData.data.role_focus}
                      </p>
                    </div>

                    {/* Key Responsibilities */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Responsabilidades Principais</h4>
                      <div className="space-y-2">
                        {contextData.data.key_responsibilities.map((responsibility: string, index: number) => (
                          <div key={index} className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                            <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                            <span className="text-sm" style={{ color: 'var(--eleven-text-primary)' }}>{responsibility}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Escopo
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Definição
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "work-arrangement" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Clock className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Modelo de Trabalho Híbrido</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4 font-open-sans">
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Modalidade</h4>
                        <p className="font-semibold">{contextData.data.arrangement}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Flexibilidade</h4>
                        <p className="font-semibold">{contextData.data.flexibility}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Dias Presenciais</h4>
                        <div className="flex flex-wrap gap-1">
                          {contextData.data.office_days.map((day: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">{day}</Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Home Office</h4>
                        <div className="flex flex-wrap gap-1">
                          {contextData.data.home_office_days.map((day: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">{day}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Benefícios Inclusos</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{contextData.data.benefits}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "final-job-description" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Job Description Completo</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-salmon)' }}>
                      <h3 className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.header.title}</h3>
                      <p style={{ color: 'var(--eleven-text-secondary)' }}>{contextData.data.header.company} • {contextData.data.header.location}</p>
                      <p className="text-sm mt-2" style={{ color: 'var(--eleven-text-secondary)' }}>{contextData.data.header.salary_range}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Responsabilidades Principais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.key_responsibilities).map(([key, items]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {items.slice(0, 2).map((item: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-sm mb-1">
                                  <div className="w-1 h-1 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                                  <span>{item}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Qualificações Essenciais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.required_qualifications).map(([key, items]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {items.slice(0, 2).map((item: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-sm mb-1">
                                  <CheckCircle className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                                  <span>{item}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="border-t-0 pt-4">
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Pacote de Compensação</h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.compensation_highlights.total_package.split(' ')[1]}
                          </p>
                          <p className="text-xs text-gray-600">Total Anual</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{contextData.data.compensation_highlights.variable_bonus}</p>
                          <p className="text-xs text-gray-600">Bônus Variável</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{contextData.data.compensation_highlights.benefits_value}</p>
                          <p className="text-xs text-gray-600">Benefícios</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "job-publishing" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">Publicação Multi-Canal</span>
                    </div>
                    <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                      {contextData.data.ats_integration.status}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* ATS Integration Highlight */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Sistema ATS Integrado</p>
                          <h4 className="text-base font-bold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.ats_integration.system}
                          </h4>
                        </div>
                        <div className="text-right">
                          <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Job ID</p>
                          <p className="text-sm font-mono font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.ats_integration.job_id}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Publication Channels */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Canais de Publicação</h4>
                      <div className="space-y-2">
                        {contextData.data.publication_channels.map((channel: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="flex-1">
                              <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{channel.platform}</h5>
                              <p className="text-sm mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                                {channel.reach} • {channel.budget}
                              </p>
                            </div>
                            <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)', color: 'var(--eleven-text-primary)' }}>
                              {channel.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Success Metrics */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Metas de Sucesso</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(contextData.data.success_metrics.targets).map(([key, value]: [string, any], index) => (
                          <div key={index} className="text-center p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                            <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>{String(value)}</p>
                            <p className="text-xs mt-1 capitalize" style={{ color: 'var(--eleven-text-secondary)' }}>
                              {key.replace('_', ' ')}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Canais
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Publicar Vaga
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "sourcing-progress" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <TrendingUp className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Progress do Sourcing - Tempo Real</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-4 gap-3">
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.applications_received}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Aplicações</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.active_sourcing_reached}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Sourcing Ativo</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-coral)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.response_rate}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Taxa Resposta</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.avg_candidate_score}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Score Médio</p>
                      </div>
                    </div>

                    {/* Top Candidates */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Candidatos Top Performance</h4>
                      <div className="space-y-2">
                        {contextData.data.top_candidates.map((candidate: any, index: number) => (
                          <div key={index} className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{candidate.name}</h5>
                                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>{candidate.current_role}</p>
                              </div>
                              <Badge style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                                Score: {candidate.score}
                              </Badge>
                            </div>
                            <div className="flex flex-wrap gap-2 mb-2">
                              {candidate.highlights.map((highlight: string, i: number) => (
                                <Badge key={i} variant="outline" className="text-xs" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                                  {highlight}
                                </Badge>
                              ))}
                            </div>
                            <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                              Status: {candidate.status}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Eye className="w-4 h-4 mr-2" />
                        Ver Pipeline Completo
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Convidar Candidatos
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "interview-management" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Gestão de Entrevistas</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Cronograma de Screening</h4>
                      <div className="space-y-3 font-open-sans">
                        {contextData.data.screening_schedule.map((interview: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md">
                            <div>
                              <h5 className="font-medium text-gray-950 dark:text-gray-50">{interview.candidate}</h5>
                              <p className="text-sm text-gray-600">{interview.date} • {interview.time}</p>
                              <p className="text-xs text-gray-600">{interview.interviewer}</p>
                            </div>
                            <Badge 
                              variant="outline" 
                              style={{ 
                                backgroundColor: interview.status === 'Confirmed' ? 'var(--eleven-sepia-mint)' : 'var(--eleven-sepia-gold)',
                                borderColor: 'var(--eleven-border-subtle)',
                                color: 'var(--eleven-text-primary)'
                              }}
                            >
                              {interview.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Estrutura do Processo</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(contextData.data.interview_structure).map(([key, stage]: [string, any], index) => (
                          <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                            <h5 className="font-medium capitalize mb-2">{key.replace('stage_', 'Etapa ').replace('_', ' ')}</h5>
                            <div className="text-sm space-y-1">
                              <p><span className="text-gray-600">Duração:</span> {stage.duration}</p>
                              <p><span className="text-gray-600">Entrevistador:</span> {stage.interviewer}</p>
                              <p><span className="text-gray-600">Critério:</span> {stage.success_criteria}</p>
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
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <UserCheck className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Seleção Final</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                      <h4 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Candidato Selecionado: Carlos Mendonça</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Score Final: 94/100 • Cultural Fit: Excelente</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Processo de Finalização</h4>
                      <div className="space-y-3 font-open-sans">
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Referências Profissionais</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>Concluído</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Background Check</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>Aprovado</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Proposta Salarial</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>Aceita</Badge>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Detalhes da Contratação</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Data de Início:</p>
                          <p className="font-medium">15 de Março, 2024</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Salário Negociado:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>R$ 47.500</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Revisar Proposta
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Seleção
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "onboarding-plan" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Workflow className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Plano de Onboarding</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h4 className="text-base font-bold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>Programa de 90 Dias</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Integração estratégica e cultural personalizada</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Primeiros 30 Dias</h4>
                      <div className="space-y-2">
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Imersão na cultura e processos da empresa</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Reuniões 1:1 com stakeholders principais</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Análise do estado atual da infraestrutura TI</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">60-90 Dias</h4>
                      <div className="space-y-2">
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Apresentação do plano estratégico de transformação digital</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Início das primeiras iniciativas de melhoria</span>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Cronograma
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Plano
                      </Button>
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar PDF
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "performance-management" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Target className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Gestão de Performance</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-gold)' }}>
                      <h4 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Framework de Avaliação Anual</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>OKRs + 360-feedback + desenvolvimento contínuo</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">OKRs do Primeiro Ano</h4>
                      <div className="space-y-3 font-open-sans">
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 1: Transformação Digital</h5>
                          <p className="text-sm text-gray-600">Migrar 80% dos sistemas para cloud em 12 meses</p>
                        </div>
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 2: Crescimento da Equipe</h5>
                          <p className="text-sm text-gray-600">Escalar equipe de 45 para 75 pessoas com 95% de retenção</p>
                        </div>
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 3: Excelência Operacional</h5>
                          <p className="text-sm text-gray-600">Reduzir downtime em 50% e implementar monitoramento avançado</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Cronograma de Reviews</h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">30 dias</p>
                          <p className="text-xs text-gray-600">Check-in inicial</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">90 dias</p>
                          <p className="text-xs text-gray-600">Avaliação onboarding</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">12 meses</p>
                          <p className="text-xs text-gray-600">Review anual</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar OKRs
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Framework
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "journey-summary" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Award className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Relatório Executivo Final</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h3 className="text-base font-semibold mb-3" style={{ color: 'var(--eleven-text-primary)' }}>Sumário Executivo</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Posição:</p>
                          <p className="font-medium">{contextData.data.executive_summary.position}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">ROI Projetado:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.executive_summary.roi_projection}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Investimento Total:</p>
                          <p className="font-medium">{contextData.data.executive_summary.total_investment}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Probabilidade Sucesso:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.executive_summary.success_probability}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Fases da Jornada</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(contextData.data.journey_phases).map(([key, phase]: [string, any], index) => (
                          <div key={index} className="p-3 rounded-md">
                            <h5 className="font-medium capitalize mb-2">{key.replace('phase_', 'Fase ').replace('_', ' ')}</h5>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Duração: {phase.duration}</p>
                            <div className="space-y-1">
                              {phase.activities.slice(0, 2).map((activity: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-xs">
                                  <div className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></div>
                                  <span>{activity}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Resultados Mensuráveis</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.measurable_results).slice(0, 4).map(([key, value]: [string, any], index) => (
                            <div key={index} className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}:</span>
                              <span className="text-sm font-medium">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Inovações Principais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.key_innovations).map(([key, innovations]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {innovations.slice(0, 2).map((innovation: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-xs mb-1">
                                  <CheckCircle className="w-3 h-3 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                                  <span>{innovation}</span>
                                </div>
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

          {contextData.type === "predictive-insights" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                    <span className="text-gray-950 dark:text-gray-50">Inteligência Preditiva</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-coral)' }}>
                      <h4 className="font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>Base de Análise</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
 <span className="text-wedo-cyan-dark dark:text-gray-300">Processos Históricos:</span>
                          <p className="font-semibold">{contextData.data.analysis_base.historical_processes}</p>
                        </div>
                        <div>
 <span className="text-wedo-cyan-dark dark:text-gray-300">Pontos de Dados:</span>
                          <p className="font-semibold">{contextData.data.analysis_base.data_points.toLocaleString()}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Predições de Melhoria</h4>
                      <div className="space-y-4 font-open-sans">
                        {contextData.data.predictions.map((prediction: any, index: number) => (
                          <div key={index} className="p-4 rounded-md">
                            <div className="flex items-center justify-between mb-3">
                              <h5 className="font-medium text-gray-950 dark:text-gray-50">{prediction.category}</h5>
                              <Badge variant="outline" className="text-xs">
                                {prediction.confidence}% confiança
                              </Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                              <div>
                                <span className="text-gray-600">Atual:</span>
                                <p className="font-medium">{prediction.current_performance}</p>
                              </div>
                              <div>
                                <span className="text-gray-600">Predição:</span>
                                <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{prediction.predicted_improvement}</p>
                              </div>
                            </div>
                            <div>
                              <span className="text-xs text-gray-600">Ações Recomendadas:</span>
                              <ul className="mt-1 space-y-1">
                                {prediction.actions.slice(0, 2).map((action: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2 text-xs">
                                    <div className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                                    <span>{action}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Roadmap de Implementação</h4>
                      <div className="space-y-2">
                        {Object.entries(contextData.data.implementation_roadmap).map(([phase, description]: [string, any], index) => (
                          <div key={index} className="flex items-center space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                              {index + 1}
                            </div>
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

          {/* Painel de Carta Oferta */}
          {contextData.type === "offer-letter" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between font-open-sans">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    {/* Informações do Candidato */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <h4 className="font-medium mb-3" style={{ color: 'var(--eleven-text-primary)' }}>Candidato</h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Nome:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.name}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Email:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.email}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Telefone:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.phone}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Empresa Atual:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.current_company}</p>
                        </div>
                      </div>
                    </div>

                    {/* Template da Carta Oferta */}
                    <div className="p-6 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-card)', borderColor: 'var(--eleven-border-subtle)' }}>
                      <div className="prose prose-sm max-w-none">
                        <pre className="whitespace-pre-wrap font-open-sans text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.letter_template}
                        </pre>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Revisar e Editar
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Enviar para Candidato
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Painel de Agendamento de Entrevistas */}
          {contextData.type === "interview-scheduling" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    {/* Candidatos para Agendar */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Candidatos Selecionados</h4>
                      <div className="space-y-3">
                        {contextData.data.candidates_to_schedule.map((candidate: any, index: number) => (
                          <div key={index} className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{candidate.name}</h5>
                                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Score: {candidate.score}/100</p>
                              </div>
                              <Badge style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                                {candidate.interview_type}
                              </Badge>
                            </div>
                            <div className="flex gap-2 text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                              <span>Preferências:</span>
                              {candidate.preferred_times.map((time: string, i: number) => (
                                <span key={i} className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>{time}</span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Horários Disponíveis */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Horários Disponíveis</h4>
                      <div className="space-y-4">
                        {Object.entries(contextData.data.available_slots).map(([date, slots]: [string, any], index) => (
                          <div key={index}>
                            <h5 className="text-sm font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>{date}</h5>
                            <div className="grid grid-cols-3 gap-2">
                              {slots.map((slot: any, i: number) => (
                                <button
                                  key={i}
                                  disabled={!slot.available}
                                  className={`p-2 rounded text-xs transition-all ${slot.available ? 'hover:scale-105' : 'opacity-50 cursor-not-allowed'}`}
                                  style={{
                                    backgroundColor: slot.available ? 'var(--eleven-sepia-mint)' : 'var(--eleven-bg-message)',
                                    color: 'var(--eleven-text-primary)',
                                    border: `1px solid ${slot.available ? 'var(--eleven-border-subtle)' : 'var(--eleven-border-light)'}`
                                  }}
                                >
                                  {slot.time}
                                  <div className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>{slot.duration}</div>
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Informações Adicionais */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Entrevistador:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.interviewer}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Integração:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.calendar_integration}</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar Horários
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Agendamentos
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Add other context types as needed */}

          {/* Job Creation Frames - Technical Matrix */}
          {contextData.type === "technical-matrix" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Target className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Timeline */}
          {contextData.type === "timeline" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <CalendarDays className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Interview Flow */}
          {contextData.type === "interview-flow" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Workflow className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Org Chart */}
          {contextData.type === "org-chart" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Network className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Progress */}
          {contextData.type === "job-creation-progress" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Briefcase className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Progress Overview */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          Progresso da Criação
                        </span>
                        <span className="text-sm font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.completion_percentage}%
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                        <div 
                          className="h-full rounded-full transition-all duration-500 bg-gray-700" style={{ width: `${contextData.data.completion_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Field Status */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Status dos Campos</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {contextData.data.collected_fields?.map((field: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                            <CheckCircle className="w-4 h-4 text-status-success" />
                            <span className="text-sm">{field}</span>
                          </div>
                        ))}
                        {contextData.data.pending_fields?.map((field: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <Clock className="w-4 h-4 text-gray-600" />
                            <span className="text-sm text-gray-600">{field}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Next Steps */}
                    {contextData.data.next_panel && (
                      <div className="p-4 rounded-md border-2 border-gray-400" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                        <div className="flex items-start gap-3">
                          <ArrowUpDown className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                          <div>
                            <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                              Próximo Passo
                            </h4>
                            <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                              {contextData.data.next_panel}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Pipeline Report - Stale Candidates */}
          {contextData.type === "pipeline-report" && contextData.data && (
            <PipelineReport
              data={contextData.data}
              onAction={onPipelineAction}
              onClose={() => onClose()}
            />
          )}

          </CardContent>
        </Card>
      </div>
  )
}
