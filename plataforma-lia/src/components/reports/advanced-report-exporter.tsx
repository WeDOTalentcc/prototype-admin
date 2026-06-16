"use client"

import { useState } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Download, FileText, Table, Image, Mail, Calendar, Settings,
  CheckCircle, AlertCircle, Clock, Target, BarChart3, PieChart,
  TrendingUp, Users, DollarSign, Star, Zap, RefreshCw
} from"lucide-react"

interface ReportTemplate {
  id: string
  name: string
  description: string
  type: 'executive' | 'operational' | 'analytical' | 'custom'
  format: 'pdf' | 'excel' | 'both'
  sections: string[]
  frequency: 'manual' | 'daily' | 'weekly' | 'monthly'
  recipients: string[]
  lastGenerated?: Date
  scheduled?: boolean
}

interface ExportConfig {
  includeCharts: boolean
  includeRawData: boolean
  includeSummary: boolean
  dateRange: 'last_week' | 'last_month' | 'last_quarter' | 'custom'
  customDateStart?: string
  customDateEnd?: string
  departments: string[]
  metrics: string[]
  branding: boolean
  watermark: boolean
}

interface AdvancedReportExporterProps {
  isOpen: boolean
  onClose: () => void
  data: Record<string, unknown>
  userRole: 'executive' | 'hr' | 'recruiter'
}

export function AdvancedReportExporter({
  isOpen,
  onClose,
  data,
  userRole
}: AdvancedReportExporterProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null)
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    includeCharts: true,
    includeRawData: false,
    includeSummary: true,
    dateRange: 'last_month',
    departments: [],
    metrics: [],
    branding: true,
    watermark: false
  })
  const [isExporting, setIsExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)

  if (!isOpen) return null

  const reportTemplates: ReportTemplate[] = [
    {
      id: 'executive-summary',
      name: 'Relatório Executivo',
      description: 'Visão estratégica com KPIs de alto nível e análise de tendências',
      type: 'executive',
      format: 'pdf',
      sections: ['KPIs Estratégicos', 'Benchmarks', 'ROI', 'Previsões', 'Riscos'],
      frequency: 'monthly',
      recipients: ['CEO', 'CHO', 'Diretores']
    },
    {
      id: 'operational-detailed',
      name: 'Relatório Operacional',
      description: 'Análise detalhada de processos e performance operacional',
      type: 'operational',
      format: 'both',
      sections: ['Funil Detalhado', 'Performance por Recrutador', 'Métricas de Processo'],
      frequency: 'weekly',
      recipients: ['Gerentes de RH', 'Recrutadores']
    },
    {
      id: 'analytical-deep',
      name: 'Análise Avançada',
      description: 'Relatório técnico com análises estatísticas e predições',
      type: 'analytical',
      format: 'excel',
      sections: ['Análise Estatística', 'Modelos Preditivos', 'Correlações', 'Dados Brutos'],
      frequency: 'monthly',
      recipients: ['Analistas', 'Data Scientists']
    },
    {
      id: 'department-specific',
      name: 'Relatório por Departamento',
      description: 'Foco específico em métricas departamentais',
      type: 'operational',
      format: 'both',
      sections: ['Performance Departamental', 'Orçamento', 'Pipeline', 'Metas'],
      frequency: 'weekly',
      recipients: ['Gestores de Departamento']
    }
  ]

  const getTemplatesForRole = () => {
    switch (userRole) {
      case 'executive':
        return reportTemplates.filter(t => t.type === 'executive' || t.type === 'analytical')
      case 'hr':
        return reportTemplates.filter(t => t.type === 'operational' || t.type === 'analytical')
      case 'recruiter':
        return reportTemplates.filter(t => t.type === 'operational')
      default:
        return reportTemplates
    }
  }

  const handleExportPDF = async () => {
    setIsExporting(true)
    setExportProgress(0)

    try {
      // Simulação de progresso
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 200))
        setExportProgress(i)
      }

      // Aqui integraria com uma biblioteca de PDF real como jsPDF ou Puppeteer
      const pdfContent = generatePDFContent()
      downloadFile(pdfContent, `relatorio-${selectedTemplate?.id}-${new Date().toISOString().split('T')[0]}.pdf`, 'pdf')

    } catch (error) {
      alert('Erro ao gerar PDF. Tente novamente.')
    } finally {
      setIsExporting(false)
      setExportProgress(0)
    }
  }

  const handleExportExcel = async () => {
    setIsExporting(true)
    setExportProgress(0)

    try {
      // Simulação de progresso
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 150))
        setExportProgress(i)
      }

      // Aqui integraria com uma biblioteca de Excel real como xlsx
      const excelContent = generateExcelContent()
      downloadFile(excelContent, `dados-${selectedTemplate?.id}-${new Date().toISOString().split('T')[0]}.xlsx`, 'excel')

    } catch (error) {
      alert('Erro ao gerar Excel. Tente novamente.')
    } finally {
      setIsExporting(false)
      setExportProgress(0)
    }
  }

  const generatePDFContent = () => {
    // Mock de geração de PDF - integraria com biblioteca real
    return {
      title: selectedTemplate?.name || 'Relatório',
      sections: selectedTemplate?.sections || [],
      data: data,
      config: exportConfig,
      generatedAt: new Date().toISOString()
    }
  }

  const generateExcelContent = () => {
    // Mock de geração de Excel - integraria com biblioteca real
    return {
      sheets: [
        {
          name: 'Resumo',
          data: [
            ['Métrica', 'Valor', 'Variação'],
            ['Total Candidatos', '1247', '+15%'],
            ['Contratações', '45', '+8%'],
            ['Tempo de Preenchimento', '28 dias', '-12%'],
            ['NPS Médio', '85%', '+5%']
          ]
        },
        {
          name: 'Dados Detalhados',
          data: [
            ['Data', 'Departamento', 'Candidatos', 'Entrevistas', 'Contratações'],
            ['2024-01', 'Tech', '234', '89', '12'],
            ['2024-01', 'Sales', '156', '67', '8'],
            ['2024-01', 'Design', '98', '45', '6']
          ]
        }
      ],
      config: exportConfig
    }
  }

  const downloadFile = (content: unknown, filename: string, type: 'pdf' | 'excel') => {
    // Mock de download - integraria com geração real de arquivo

    // Simulação de download
    const blob = new Blob([JSON.stringify(content, null, 2)], {
      type: type === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getTemplateIcon = (type: string) => {
    switch (type) {
      case 'executive': return <Target className="w-5 h-5 text-wedo-purple-text" />
      case 'operational': return <BarChart3 className="w-5 h-5 text-lia-text-secondary" />
      case 'analytical': return <PieChart className="w-5 h-5 text-status-success" />
      default: return <FileText className="w-5 h-5 text-lia-text-secondary" />
    }
  }

  const availableMetrics = [
    'Candidatos Totais', 'Entrevistas', 'Contratações', 'Tempo de Preenchimento',
    'Taxa de Conversão', 'NPS', 'Custo por Hire', 'Qualidade de Hire',
    'Taxa de Retenção', 'Diversidade', 'Performance por Fonte'
  ]

  const departments = ['Tech', 'Sales', 'Design', 'Marketing', 'Product', 'Operations']

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-5xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-lia-text-primary">
              Exportação Avançada de Relatórios
            </h2>
            <p className="text-sm text-lia-text-secondary">
              Gere relatórios personalizados em PDF e Excel
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            ×
          </Button>
        </div>

        <div className="flex-1 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 h-full">

            {/* Templates */}
            <div className="p-6 border-r overflow-y-auto">
              <h3 className="text-lg font-medium mb-4">
                Escolha um Template ({userRole.toUpperCase()})
              </h3>

              <div className="space-y-3">
                {getTemplatesForRole().map((template) => (
                  <Card
                    key={template.id}
                    className={`cursor-pointer transition-colors motion-reduce:transition-none hover:${
 selectedTemplate?.id === template.id ? 'ring-2 ring-lia-btn-primary-bg/20 dark:ring-lia-border-subtle/20 bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : ''
                    }`}
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {getTemplateIcon(template.type)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium text-lia-text-primary">{template.name}</h4>
                            <Chip density="relaxed" variant="neutral" >
                              {template.format.toUpperCase()}
                            </Chip>
                          </div>
                          <p className="text-sm text-lia-text-secondary mb-2">{template.description}</p>
                          <div className="flex flex-wrap gap-1">
                            {template.sections.slice(0, 3).map((section, index) => (
                              <Chip density="relaxed" key={section} variant="neutral" muted >
                                {section}
                              </Chip>
                            ))}
                            {template.sections.length > 3 && (
                              <Chip density="relaxed" variant="neutral" muted >
                                +{template.sections.length - 3} mais
                              </Chip>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Configurações */}
            <div className="p-6 overflow-y-auto">
              {selectedTemplate ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-2">Configurações de Exportação</h3>
                    <p className="text-sm text-lia-text-secondary">Template: {selectedTemplate.name}</p>
                  </div>

                  {/* Período */}
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary block mb-2">
                      Período dos Dados
                    </label>
                    <select
                      value={exportConfig.dateRange}
                      onChange={(e) => setExportConfig(prev => ({
                        ...prev,
                        dateRange: e.target.value as ExportConfig['dateRange']
                      }))}
                      className="w-full p-2 border border-lia-border-default rounded-xl"
                    >
                      <option value="last_week">Última Semana</option>
                      <option value="last_month">Último Mês</option>
                      <option value="last_quarter">Último Trimestre</option>
                      <option value="custom">Período Personalizado</option>
                    </select>
                  </div>

                  {/* Departamentos */}
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary block mb-2">
                      Departamentos (deixe vazio para todos)
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {departments.map(dept => (
                        <label key={dept} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={exportConfig.departments.includes(dept)}
                            onChange={(e) => {
                              const newDepts = e.target.checked
                                ? [...exportConfig.departments, dept]
                                : exportConfig.departments.filter(d => d !== dept)
                              setExportConfig(prev => ({ ...prev, departments: newDepts }))
                            }}
                            className="rounded-md"
                          />
                          {dept}
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Métricas */}
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary block mb-2">
                      Métricas Específicas
                    </label>
                    <div className="grid grid-cols-1 gap-2 max-h-32 overflow-y-auto">
                      {availableMetrics.map(metric => (
                        <label key={metric} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={exportConfig.metrics.includes(metric)}
                            onChange={(e) => {
                              const newMetrics = e.target.checked
                                ? [...exportConfig.metrics, metric]
                                : exportConfig.metrics.filter(m => m !== metric)
                              setExportConfig(prev => ({ ...prev, metrics: newMetrics }))
                            }}
                            className="rounded-md"
                          />
                          {metric}
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Opções Adicionais */}
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary block mb-2">
                      Opções de Conteúdo
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={exportConfig.includeCharts}
                          onChange={(e) => setExportConfig(prev => ({
                            ...prev,
                            includeCharts: e.target.checked
                          }))}
                          className="rounded-md"
                        />
                        Incluir gráficos
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={exportConfig.includeRawData}
                          onChange={(e) => setExportConfig(prev => ({
                            ...prev,
                            includeRawData: e.target.checked
                          }))}
                          className="rounded-md"
                        />
                        Incluir dados brutos
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={exportConfig.includeSummary}
                          onChange={(e) => setExportConfig(prev => ({
                            ...prev,
                            includeSummary: e.target.checked
                          }))}
                          className="rounded-md"
                        />
                        Incluir resumo executivo
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={exportConfig.branding}
                          onChange={(e) => setExportConfig(prev => ({
                            ...prev,
                            branding: e.target.checked
                          }))}
                          className="rounded-md"
                        />
                        Branding corporativo
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={exportConfig.watermark}
                          onChange={(e) => setExportConfig(prev => ({
                            ...prev,
                            watermark: e.target.checked
                          }))}
                          className="rounded-md"
                        />
                        Marca d'água
                      </label>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {isExporting && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Gerando relatório...</span>
                        <span>{exportProgress}%</span>
                      </div>
                      <div className="w-full bg-lia-interactive-active rounded-full h-2">
                        <div
                          className="bg-lia-bg-inverse h-2 rounded-full transition-[width,height] duration-300"
                          style={{width: `${exportProgress}%`}}
                        />
                      </div>
                    </div>
                  )}

                  {/* Export Buttons */}
                  <div className="flex gap-2 pt-4 border-t">
                    {(selectedTemplate.format === 'pdf' || selectedTemplate.format === 'both') && (
                      <Button
                        onClick={handleExportPDF}
                        disabled={isExporting}
                        className="gap-2 flex-1"
                      >
                        <FileText className="w-4 h-4" />
                        {isExporting ? 'Gerando...' : 'Exportar PDF'}
                      </Button>
                    )}
                    {(selectedTemplate.format === 'excel' || selectedTemplate.format === 'both') && (
                      <Button
                        variant="outline"
                        onClick={handleExportExcel}
                        disabled={isExporting}
                        className="gap-2 flex-1"
                      >
                        <Table className="w-4 h-4" />
                        {isExporting ? 'Gerando...' : 'Exportar Excel'}
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-lia-text-primary">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-lia-text-secondary" />
                    <p>Selecione um template para configurar a exportação</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
