"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import {
  Download,
  FileArchive,
  Calendar,
  FileText,
  Shield,
  ScrollText,
  Award,
  BarChart3,
  CheckCircle2,
  Clock,
  Package,
  User,
  AlertTriangle,
} from "lucide-react"

interface EvidenceType {
  id: string
  name: string
  description: string
  icon: React.ElementType
  count: number
  selected: boolean
}

interface PreviousExport {
  id: number
  framework: string
  period: string
  evidenceCount: number
  generatedAt: string
  generatedBy: string
  status: 'completed' | 'pending' | 'failed'
  fileSize: string
}

const frameworks = [
  { id: 'iso-27001', name: 'ISO 27001', description: 'Sistema de Gestão de Segurança da Informação' },
  { id: 'soc-2', name: 'SOC 2 Type II', description: 'Service Organization Control' },
  { id: 'sox', name: 'SOX', description: 'Sarbanes-Oxley Act Compliance' },
  { id: 'lgpd', name: 'LGPD', description: 'Lei Geral de Proteção de Dados' },
  { id: 'bcb-498', name: 'BCB 498', description: 'Resolução BCB nº 498 - Política de Segurança Cibernética' },
]

const periods = [
  { id: 'last-month', name: 'Último mês' },
  { id: 'last-quarter', name: 'Último trimestre' },
  { id: 'last-6-months', name: 'Últimos 6 meses' },
  { id: 'last-year', name: 'Último ano' },
  { id: 'custom', name: 'Período customizado' },
]

const initialEvidenceTypes: EvidenceType[] = [
  { id: 'logs', name: 'Logs de Auditoria', description: 'Trilha completa de auditoria SOX', icon: ScrollText, count: 12847, selected: true },
  { id: 'controls', name: 'Controles Implementados', description: 'Controles de segurança e compliance ativos', icon: Shield, count: 156, selected: true },
  { id: 'policies', name: 'Políticas Vigentes', description: 'Políticas de segurança e privacidade', icon: FileText, count: 24, selected: true },
  { id: 'certificates', name: 'Certificações', description: 'Certificações e atestados', icon: Award, count: 8, selected: true },
  { id: 'bias-reports', name: 'Relatórios de Bias', description: 'Auditorias de viés algorítmico', icon: BarChart3, count: 12, selected: false },
  { id: 'incidents', name: 'Incidentes e Resoluções', description: 'Histórico de incidentes e ações corretivas', icon: AlertTriangle, count: 7, selected: false },
]

const previousExports: PreviousExport[] = [
  { 
    id: 1, 
    framework: 'SOC 2 Type II', 
    period: 'Último trimestre', 
    evidenceCount: 156, 
    generatedAt: '2024-12-15T10:30:00Z', 
    generatedBy: 'Maria Silva', 
    status: 'completed',
    fileSize: '45.2 MB',
  },
  { 
    id: 2, 
    framework: 'ISO 27001', 
    period: 'Último ano', 
    evidenceCount: 423, 
    generatedAt: '2024-11-28T14:15:00Z', 
    generatedBy: 'Carlos Santos', 
    status: 'completed',
    fileSize: '128.7 MB',
  },
  { 
    id: 3, 
    framework: 'SOX', 
    period: 'Últimos 6 meses', 
    evidenceCount: 287, 
    generatedAt: '2024-11-15T09:00:00Z', 
    generatedBy: 'Ana Costa', 
    status: 'completed',
    fileSize: '78.4 MB',
  },
  { 
    id: 4, 
    framework: 'SOC 2 Type II', 
    period: 'Último mês', 
    evidenceCount: 52, 
    generatedAt: '2024-12-01T16:45:00Z', 
    generatedBy: 'Pedro Lima', 
    status: 'completed',
    fileSize: '15.8 MB',
  },
]

export default function ExportarPage() {
  const [selectedFramework, setSelectedFramework] = useState<string>('soc-2')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('last-quarter')
  const [evidenceTypes, setEvidenceTypes] = useState<EvidenceType[]>(initialEvidenceTypes)
  const [isGenerating, setIsGenerating] = useState(false)

  const toggleEvidence = (id: string) => {
    setEvidenceTypes(prev => prev.map(e => 
      e.id === id ? { ...e, selected: !e.selected } : e
    ))
  }

  const selectedCount = evidenceTypes.filter(e => e.selected).length
  const totalItems = evidenceTypes.filter(e => e.selected).reduce((acc, e) => acc + e.count, 0)

  const handleGeneratePackage = async () => {
    if (selectedCount === 0) {
      toast.error('Selecione pelo menos um tipo de evidência')
      return
    }
    setIsGenerating(true)
    await new Promise(resolve => setTimeout(resolve, 2500))
    toast.success('Pacote de auditoria gerado com sucesso!')
    setIsGenerating(false)
  }

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusBadge = (status: 'completed' | 'pending' | 'failed') => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3 h-3" />Concluído</Badge>
      case 'pending':
        return <Badge className="bg-status-warning/15 text-status-warning gap-1"><Clock className="w-3 h-3" />Gerando...</Badge>
      case 'failed':
        return <Badge variant="destructive" className="gap-1"><AlertTriangle className="w-3 h-3" />Falhou</Badge>
    }
  }

  const selectedFrameworkData = frameworks.find(f => f.id === selectedFramework)
  const selectedPeriodData = periods.find(p => p.id === selectedPeriod)

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
            >
              <FileArchive className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              >
                Gerador de Pacote para Auditores
              </h1>
              <p className="text-sm lia-text-400 dark:lia-text-500">
                Exportação de evidências e documentação para auditorias
              </p>
            </div>
          </div>
        </div>

        <Card className="mb-6 border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/10 dark:border-status-warning/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-status-warning/15 dark:bg-status-warning/30 rounded-md">
                <AlertTriangle className="w-5 h-5 text-status-warning" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                  Gap Crítico Identificado - Facilitação de Auditorias
                </p>
                <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                  Esta funcionalidade automatiza a geração de pacotes de evidências para auditores externos, 
                  reduzindo o tempo de preparação de auditorias de <strong>semanas para minutos</strong>. 
                  Requisito recomendado por ISO 27001 (A.18.2.1) e SOC 2.
                </p>
              </div>
              <Badge className="bg-status-warning/20 text-status-warning dark:bg-status-warning dark:text-status-warning">Novo</Badge>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Shield className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  Configuração do Pacote
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2 block">
                      Framework de Compliance
                    </label>
                    <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o framework" />
                      </SelectTrigger>
                      <SelectContent>
                        {frameworks.map((fw) => (
                          <SelectItem key={fw.id} value={fw.id}>
                            <div className="flex flex-col">
                              <span>{fw.name}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedFrameworkData && (
                      <p className="text-xs lia-text-500 mt-1">{selectedFrameworkData.description}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2 block">
                      Período
                    </label>
                    <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                      <SelectTrigger>
                        <Calendar className="w-4 h-4 mr-2 lia-text-400" />
                        <SelectValue placeholder="Selecione o período" />
                      </SelectTrigger>
                      <SelectContent>
                        {periods.map((p) => (
                          <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                    Tipos de Evidência
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {evidenceTypes.map((evidence) => {
                      const Icon = evidence.icon
                      return (
                        <div 
                          key={evidence.id}
                          className={`p-4 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none ${
                            evidence.selected 
                              ? 'border-gray-900 dark:lia-border-50 bg-gray-50 dark:bg-lia-bg-secondary/50' 
                              : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default'
                          }`}
                          onClick={() => toggleEvidence(evidence.id)}
                        >
                          <div className="flex items-start gap-3">
                            <Checkbox 
                              checked={evidence.selected} 
                              onCheckedChange={() => toggleEvidence(evidence.id)}
                              className="mt-1"
                            />
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <Icon className={`w-4 h-4 ${evidence.selected ? 'lia-text-600 dark:text-lia-text-tertiary' : 'lia-text-400'}`} />
                                <span className="text-sm font-medium lia-text-950 dark:lia-text-50">
                                  {evidence.name}
                                </span>
                                <Badge variant="secondary" className="text-xs">
                                  {evidence.count.toLocaleString('pt-BR')}
                                </Badge>
                              </div>
                              <p className="text-xs lia-text-500 mt-1">{evidence.description}</p>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                    Exportações Anteriores
                  </CardTitle>
                  <Badge variant="outline">{previousExports.length} exportações</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary/50">
                        <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-6 py-3">Framework</th>
                        <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Período</th>
                        <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Evidências</th>
                        <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Gerado em</th>
                        <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Por</th>
                        <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Status</th>
                        <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Ação</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:lia-divide-700">
                      {previousExports.map((exp) => (
                        <tr key={exp.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors motion-reduce:transition-none">
                          <td className="px-6 py-4">
                            <span className="text-sm font-medium lia-text-950 dark:lia-text-50">{exp.framework}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm lia-text-800 dark:text-lia-text-primary">{exp.period}</span>
                          </td>
                          <td className="px-4 py-4 text-center">
                            <Badge variant="secondary">{exp.evidenceCount}</Badge>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm lia-text-600 dark:text-lia-text-tertiary">{formatDateTime(exp.generatedAt)}</span>
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-1 text-sm lia-text-600 dark:text-lia-text-tertiary">
                              <User className="w-3 h-3" />
                              {exp.generatedBy}
                            </div>
                          </td>
                          <td className="px-4 py-4 text-center">
                            {getStatusBadge(exp.status)}
                          </td>
                          <td className="px-4 py-4 text-center">
                            {exp.status === 'completed' && (
                              <Button variant="ghost" size="sm" className="gap-1">
                                <Download className="w-4 h-4" />
                                {exp.fileSize}
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card className="sticky top-6">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Package className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  Preview do Pacote
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <p className="text-xs lia-text-500 mb-1">Framework</p>
                    <p className="text-sm font-medium lia-text-950 dark:lia-text-50">
                      {selectedFrameworkData?.name || 'Não selecionado'}
                    </p>
                  </div>

                  <div className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <p className="text-xs lia-text-500 mb-1">Período</p>
                    <p className="text-sm font-medium lia-text-950 dark:lia-text-50">
                      {selectedPeriodData?.name || 'Não selecionado'}
                    </p>
                  </div>

                  <div className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <p className="text-xs lia-text-500 mb-1">Tipos de Evidência</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {evidenceTypes.filter(e => e.selected).map((e) => (
                        <Badge key={e.id} variant="secondary" className="text-xs">
                          {e.name}
                        </Badge>
                      ))}
                      {selectedCount === 0 && (
                        <span className="text-sm lia-text-400">Nenhum selecionado</span>
                      )}
                    </div>
                  </div>

                  <div className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <p className="text-xs lia-text-500 mb-1">Total de Itens</p>
                    <p className="text-2xl font-semibold lia-text-950 dark:lia-text-50">
                      {totalItems.toLocaleString('pt-BR')}
                    </p>
                  </div>

                  <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-4">
                    <Button 
                      className="w-full gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                      onClick={handleGeneratePackage}
                      disabled={isGenerating || selectedCount === 0}
                    >
                      {isGenerating ? (
                        <>
                          <Clock className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                          Gerando Pacote...
                        </>
                      ) : (
                        <>
                          <FileArchive className="w-4 h-4" />
                          Gerar Pacote
                        </>
                      )}
                    </Button>
                    {selectedCount === 0 && (
                      <p className="text-xs text-status-warning mt-2 text-center">
                        Selecione pelo menos um tipo de evidência
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
                    <Shield className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium lia-text-950 dark:lia-text-50">
                      Pacote Seguro
                    </p>
                    <p className="text-xs lia-text-500 mt-1">
                      O pacote é gerado com criptografia AES-256 e pode incluir assinatura digital para integridade.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
