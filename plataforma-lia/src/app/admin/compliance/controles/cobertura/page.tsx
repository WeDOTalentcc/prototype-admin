"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Grid3X3,
  ChevronLeft,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Shield,
  Scale,
  TrendingUp,
  TrendingDown
} from "lucide-react"
import { toast } from "sonner"
import { complianceService, ComplianceDashboard, ControlLibrary, CompanyControl, FrameworkStats } from '@/services/admin/compliance-service'

const ADMIN_CLIENT_ID = 'admin-global'

interface FrameworkCoverage {
  key: string
  name: string
  icon: React.ReactNode
  stats: FrameworkStats | null
  color: string
}

interface GapItem {
  controlId: string
  controlName: string
  framework: string
  category: string
  priority: 'high' | 'medium' | 'low'
}

export default function CoberturaPage() {
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null)
  const [allControls, setAllControls] = useState<ControlLibrary[]>([])
  const [companyControls, setCompanyControls] = useState<CompanyControl[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const [dashboardData, controlsData, companyData] = await Promise.all([
        complianceService.getDashboard(ADMIN_CLIENT_ID),
        complianceService.getControlLibrary({ limit: 500 }),
        complianceService.getCompanyControls(ADMIN_CLIENT_ID, { limit: 500 })
      ])
      setDashboard(dashboardData)
      setAllControls(controlsData.controls)
      setCompanyControls(companyData.controls)
    } catch (err) {
      console.error('Error fetching coverage data:', err)
      toast.error('Erro ao carregar dados de cobertura')
    } finally {
      setIsRefreshing(false)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const frameworks: FrameworkCoverage[] = [
    {
      key: 'ISO27001',
      name: 'ISO 27001:2022',
      icon: <ShieldCheck className="w-5 h-5" />,
      stats: dashboard?.byFramework?.['ISO27001'] || null
    },
    {
      key: 'SOC2',
      name: 'SOC 2 Type II',
      icon: <Shield className="w-5 h-5" />,
      stats: dashboard?.byFramework?.['SOC2'] || null,
      color: 'var(--wedo-green-light)'
    },
    {
      key: 'SOX',
      name: 'SOX',
      icon: <Scale className="w-5 h-5" />,
      stats: dashboard?.byFramework?.['SOX'] || null,
      color: 'var(--wedo-purple)'
    }
  ]

  const gaps: GapItem[] = allControls
    .filter(control => {
      const companyControl = companyControls.find(cc => cc.controlLibraryId === control.id)
      return !companyControl || companyControl.status === 'not_started'
    })
    .map(control => ({
      controlId: control.controlId,
      controlName: control.controlName,
      framework: control.framework,
      category: control.controlCategory || 'Geral',
      priority: control.isMandatory ? 'high' : 'medium'
    }))
    .slice(0, 20)

  const totalControls = dashboard?.totalControls || 0
  const totalImplemented = dashboard?.totalImplemented || 0
  const overallPercentage = dashboard?.overallCompliancePercentage || 0
  const gapsCount = totalControls - totalImplemented

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Carregando mapa de cobertura...
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/compliance/controles">
              <Button variant="ghost" size="sm">
                <ChevronLeft className="w-4 h-4 mr-1" />
                Voltar
              </Button>
            </Link>
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <Grid3X3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Mapa Cross-Framework
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Cobertura de controles entre frameworks (ISO, SOC 2, SOX, LGPD)
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Atualizando...' : 'Atualizar'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Cobertura Global
                  </p>
                  <p className="text-3xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {Math.round(overallPercentage)}%
                  </p>
                </div>
                {overallPercentage >= 70 ? (
                  <TrendingUp className="w-6 h-6 text-status-success" />
                ) : (
                  <TrendingDown className="w-6 h-6 text-status-warning" />
                )}
              </div>
              <Progress value={overallPercentage} className="h-2 mt-4" />
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Controles Implementados
                  </p>
                  <p className="text-3xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {totalImplemented}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    de {totalControls} total
                  </p>
                </div>
                <CheckCircle2 className="w-6 h-6 text-status-success" />
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Gaps Identificados
                  </p>
                  <p className="text-3xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {gapsCount}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    controles pendentes
                  </p>
                </div>
                <AlertTriangle className="w-6 h-6 text-status-warning" />
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Frameworks Ativos
                  </p>
                  <p className="text-3xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {frameworks.filter(f => f.stats && f.stats.totalControls > 0).length}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    de {frameworks.length} configurados
                  </p>
                </div>
                <Grid3X3 className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Cobertura por Framework
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {frameworks.map(framework => (
                <div key={framework.key}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-8 h-8 rounded-md flex items-center justify-center"
                        style={{ backgroundColor: `${framework.color}20` }}
                      >
                        <div style={{ color: framework.color }}>
                          {framework.icon}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {framework.name}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {framework.stats?.totalControls || 0} controles
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                        {Math.round(framework.stats?.compliancePercentage || 0)}%
                      </p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        {(framework.stats?.implemented || 0) + (framework.stats?.verified || 0)} / {framework.stats?.totalControls || 0}
                      </p>
                    </div>
                  </div>
                  <div className="relative h-8 rounded-md overflow-hidden" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <div 
                      className="absolute inset-y-0 left-0 rounded-md transition-all duration-500"
                      style={{ 
                        width: `${framework.stats?.compliancePercentage || 0}%`,
                        backgroundColor: framework.color 
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-status-success" />
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>
                            {(framework.stats?.implemented || 0) + (framework.stats?.verified || 0)} Implementados
                          </span>
                        </span>
                        <span className="flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-status-warning" />
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>
                            {framework.stats?.inProgress || 0} Em Progresso
                          </span>
                        </span>
                        <span className="flex items-center gap-1">
                          <XCircle className="w-3 h-3 text-gray-400" />
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>
                            {framework.stats?.notStarted || 0} Pendentes
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Principais Gaps
              </CardTitle>
              <Badge variant="warning">{gaps.length} pendentes</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {gaps.length > 0 ? (
              <div className="rounded-md border overflow-hidden" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-50 dark:bg-gray-800/50">
                      <TableHead className="w-32">ID</TableHead>
                      <TableHead>Controle</TableHead>
                      <TableHead className="w-32">Framework</TableHead>
                      <TableHead className="w-40">Categoria</TableHead>
                      <TableHead className="w-28">Prioridade</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {gaps.map((gap, index) => (
                      <TableRow key={`${gap.framework}-${gap.controlId}-${index}`}>
                        <TableCell className="font-mono text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {gap.controlId}
                        </TableCell>
                        <TableCell style={{ color: 'var(--eleven-text-primary)' }}>
                          {gap.controlName}
                        </TableCell>
                        <TableCell>
                          <Badge variant="info" className="text-micro">
                            {gap.framework}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {gap.category}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={gap.priority === 'high' ? 'destructive' : gap.priority === 'medium' ? 'warning' : 'default'}
                            className="text-micro"
                          >
                            {gap.priority === 'high' ? 'Alta' : gap.priority === 'medium' ? 'Média' : 'Baixa'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-status-success mx-auto mb-3" />
                <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Parabéns! Todos os controles estão implementados.
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Sua organização está em conformidade com todos os frameworks configurados.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Mapeamento Cross-Framework
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                    <th className="text-left py-3 px-4 font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Domínio
                    </th>
                    {frameworks.map(fw => (
                      <th key={fw.key} className="text-center py-3 px-4 font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        {fw.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { domain: 'Políticas de Segurança', coverage: [true, true, false] },
                    { domain: 'Organização da Segurança', coverage: [true, true, true] },
                    { domain: 'Segurança em RH', coverage: [true, false, false] },
                    { domain: 'Gestão de Ativos', coverage: [true, true, true] },
                    { domain: 'Controle de Acesso', coverage: [true, true, true] },
                    { domain: 'Criptografia', coverage: [true, true, false] },
                    { domain: 'Segurança Física', coverage: [true, false, false] },
                    { domain: 'Segurança de Operações', coverage: [true, true, true] },
                    { domain: 'Segurança de Comunicações', coverage: [true, true, false] },
                    { domain: 'Gestão de Incidentes', coverage: [true, true, true] },
                    { domain: 'Continuidade de Negócio', coverage: [true, true, true] },
                    { domain: 'Conformidade', coverage: [true, true, true] },
                  ].map((row, idx) => (
                    <tr key={idx} className="border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                      <td className="py-3 px-4" style={{ color: 'var(--eleven-text-primary)' }}>
                        {row.domain}
                      </td>
                      {row.coverage.map((covered, fwIdx) => (
                        <td key={fwIdx} className="text-center py-3 px-4">
                          {covered ? (
                            <CheckCircle2 className="w-5 h-5 text-status-success mx-auto" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-300 mx-auto" />
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs mt-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
              * Este mapeamento mostra a cobertura de domínios entre os diferentes frameworks de compliance.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
