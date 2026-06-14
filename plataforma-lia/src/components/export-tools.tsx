"use client"

import { useState } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Download, FileText, FileSpreadsheet, File, Image,
  Calendar, Filter, Mail, Share2, Settings, Clock,
  CheckCircle, AlertCircle
} from"lucide-react"

interface ExportConfig {
  format: 'csv' | 'excel' | 'pdf' | 'png' | 'json'
  includeCharts: boolean
  includeSummary: boolean
  includeRawData: boolean
  dateRange: '30d' | '90d' | '6m' | '1y' | 'custom'
  filters: string[]
}

interface ExportToolsProps {
  data?: Record<string, unknown> | Record<string, unknown>[]
  className?: string
}

export function ExportTools({ data, className }: ExportToolsProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'excel',
    includeCharts: true,
    includeSummary: true,
    includeRawData: true,
    dateRange: '90d',
    filters: []
  })
  const [lastExport, setLastExport] = useState<string | null>(null)

  // Mock export functions
  const handleExport = async (format: ExportConfig['format']) => {
    setIsExporting(true)

    // Simular processamento
    await new Promise(resolve => setTimeout(resolve, 2000))

    const timestamp = new Date().toLocaleString('pt-BR')
    setLastExport(`Exportado em ${format.toUpperCase()} - ${timestamp}`)
    setIsExporting(false)

    // Simular download
  }

  const handleScheduleExport = () => {
    alert('📅 Exportação agendada com sucesso! Você receberá o relatório por email semanalmente.')
  }

  const handleShareReport = () => {
    alert('📧 Link de compartilhamento copiado! Válido por 7 dias.')
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'csv': return <FileText className="w-4 h-4" />
      case 'excel': return <FileSpreadsheet className="w-4 h-4" />
      case 'pdf': return <File className="w-4 h-4" />
      case 'png': return <Image className="w-4 h-4" />
      case 'json': return <FileText className="w-4 h-4" />
      default: return <Download className="w-4 h-4" />
    }
  }

  const getFormatDescription = (format: string) => {
    switch (format) {
      case 'csv': return 'Dados tabulares para análise externa'
      case 'excel': return 'Planilha com gráficos e formatação'
      case 'pdf': return 'Relatório completo para apresentação'
      case 'png': return 'Imagem dos gráficos para compartilhar'
      case 'json': return 'Dados estruturados para APIs'
      default: return 'Formato de exportação'
    }
  }

  const exportFormats = [
    {
      format: 'excel' as const,
      label: 'Excel',
      description: 'Planilha com dados e gráficos',
      color: ' border-status-success/30',
      recommended: true
    },
    {
      format: 'pdf' as const,
      label: 'PDF',
      description: 'Relatório executivo completo',
      color: ' border-status-error/30',
      recommended: false
    },
    {
      format: 'csv' as const,
      label: 'CSV',
      description: 'Dados brutos para análise',
      color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default',
      recommended: false
    },
    {
      format: 'png' as const,
      label: 'PNG',
      description: 'Imagem dos gráficos',
      color: ' border-wedo-purple/30',
      recommended: false
    },
    {
      format: 'json' as const,
      label: 'JSON',
      description: 'Dados estruturados',
      color: 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle',
      recommended: false
    }
  ]

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5 text-lia-text-secondary" />
            Exportação de Dados
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">

          {/* Formatos de exportação */}
          <div>
            <h3 className="text-sm font-medium text-lia-text-primary mb-3">
              Formatos Disponíveis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {exportFormats.map((format) => (
                <button
                  key={format.format}
                  onClick={() => handleExport(format.format)}
                  disabled={isExporting}
                  className={`relative p-4 border rounded-md text-left transition-opacity motion-reduce:transition-none duration-200 hover:disabled:opacity-50 disabled:cursor-not-allowed ${
 format.format === exportConfig.format
 ? 'border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary'
                      : 'border-lia-border-subtle hover:border-lia-border-default'
                  }`}
                >
                  {format.recommended && (
                    <Chip density="relaxed" variant="neutral" muted className="absolute -top-2 -right-2 bg-wedo-orange text-white">
                      Recomendado
                    </Chip>
                  )}

                  <div className="flex items-center gap-3 mb-2">
                    {getFormatIcon(format.format)}
                    <span className="font-medium text-lia-text-primary">
                      {format.label}
                    </span>
                  </div>

                  <p className="text-xs text-lia-text-secondary mb-3">
                    {format.description}
                  </p>

                  <div className="flex items-center justify-between">
                    <Chip variant="neutral" className={format.color}>
                      {format.format.toUpperCase()}
                    </Chip>

                    {isExporting ? (
                      <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                        <div className="w-3 h-3 border-2 border-lia-btn-primary-bg border-t-transparent rounded-full animate-spin motion-reduce:animate-none"></div>
                        Exportando...
                      </div>
                    ) : (
                      <Download className="w-4 h-4 text-lia-text-secondary" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Configurações de exportação */}
          <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
            <h3 className="text-sm font-medium text-lia-text-primary mb-3">
              Configurações de Exportação
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* Período */}
              <div>
                <label className="text-xs font-medium text-lia-text-primary mb-2 block">
                  Período dos Dados
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {(['30d', '90d', '6m', '1y'] as const).map((period) => (
                    <button
                      key={period}
                      onClick={() => setExportConfig(prev => ({ ...prev, dateRange: period }))}
                      className={`px-3 py-2 text-xs rounded-md border transition-colors motion-reduce:transition-none ${
 exportConfig.dateRange === period
                          ? 'border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-primary text-wedo-cyan-text'
                          : 'border-lia-border-subtle text-lia-text-secondary hover:border-lia-border-default'
                      }`}
                    >
                      {period === '30d' ? '30 dias' :
                       period === '90d' ? '90 dias' :
                       period === '6m' ? '6 meses' : '1 ano'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Conteúdo */}
              <div>
                <label className="text-xs font-medium text-lia-text-primary mb-2 block">
                  Incluir no Relatório
                </label>
                <div className="space-y-2">
                  {[
                    { key: 'includeCharts', label: 'Gráficos e visualizações' },
                    { key: 'includeSummary', label: 'Resumo executivo' },
                    { key: 'includeRawData', label: 'Dados brutos' }
                  ].map((option) => (
                    <label key={option.key} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={exportConfig[option.key as keyof ExportConfig] as boolean}
                        onChange={(e) => setExportConfig(prev => ({
                          ...prev,
                          [option.key]: e.target.checked
                        }))}
                        className="w-3 h-3 rounded-xl border-lia-border-default"
                      />
                      <span className="text-xs text-lia-text-secondary">
                        {option.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Ações rápidas */}
          <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
            <h3 className="text-sm font-medium text-lia-text-primary mb-3">
              Ações Rápidas
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button
                variant="outline"
                onClick={handleScheduleExport}
                className="gap-2 text-xs"
              >
                <Calendar className="w-4 h-4" />
                Agendar Exportação
              </Button>

              <Button
                variant="outline"
                onClick={handleShareReport}
                className="gap-2 text-xs"
              >
                <Share2 className="w-4 h-4" />
                Compartilhar Link
              </Button>

              <Button
                variant="outline"
                onClick={() => alert('📬 Configurações de email atualizadas!')}
                className="gap-2 text-xs"
              >
                <Mail className="w-4 h-4" />
                Enviar por Email
              </Button>
            </div>
          </div>

          {/* Status da última exportação */}
          {lastExport && (
            <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
              <div className="flex items-center gap-2 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="text-sm text-status-success dark:text-status-success">
                  {lastExport}
                </span>
              </div>
            </div>
          )}

          {/* Informações adicionais */}
          <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
 <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-lia-text-secondary mt-0.5" />
                <div>
 <h4 className="text-sm font-medium text-lia-text-secondary mb-1">
                    Dicas de Exportação
                  </h4>
 <ul className="text-xs text-lia-text-muted space-y-1">
                    <li>• Use <strong>Excel</strong> para análises detalhadas com gráficos</li>
                    <li>• Use <strong>PDF</strong> para apresentações executivas</li>
                    <li>• Use <strong>CSV</strong> para importar em outras ferramentas</li>
                    <li>• Use <strong>PNG</strong> para compartilhar gráficos específicos</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
