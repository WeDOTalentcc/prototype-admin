"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  FileCheck,
  ShieldCheck,
  Shield,
  Scale,
  Grid3X3,
  ChevronRight,
  RefreshCw,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle
} from "lucide-react"
import { toast } from "sonner"
import { complianceService, ComplianceDashboard, FrameworkStats } from '@/services/admin/compliance-service'

interface FrameworkCard {
  key: string
  name: string
  description: string
  icon: React.ReactNode
  href: string
  stats: FrameworkStats | null
}

const ADMIN_CLIENT_ID = 'admin-global'

function getStatusBadge(stats: FrameworkStats | null) {
  if (!stats) {
    return <Badge variant="default">Não Configurado</Badge>
  }
  const percentage = stats.compliancePercentage
  if (percentage >= 80) {
    return <Badge variant="success">Conforme</Badge>
  } else if (percentage >= 50) {
    return <Badge variant="warning">Parcial</Badge>
  } else if (percentage > 0) {
    return <Badge variant="destructive">Em Progresso</Badge>
  }
  return <Badge variant="default">Não Iniciado</Badge>
}

export default function ControlesPage() {
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const data = await complianceService.getDashboard(ADMIN_CLIENT_ID)
      setDashboard(data)
    } catch (err) {
      toast.error('Erro ao carregar dados de controles')
    } finally {
      setIsRefreshing(false)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const frameworkCards: FrameworkCard[] = [
    {
      key: 'ISO27001',
      name: 'ISO 27001:2022',
      description: 'Sistema de Gestão de Segurança da Informação',
      icon: <ShieldCheck className="w-6 h-6 text-gray-600 dark:text-gray-400" />,
      href: '/admin/compliance/controles/iso-27001',
      stats: dashboard?.byFramework?.['ISO27001'] || null
    },
    {
      key: 'SOC2',
      name: 'SOC 2 Type II',
      description: 'Trust Service Criteria',
      icon: <Shield className="w-6 h-6 text-gray-600 dark:text-gray-400" />,
      href: '/admin/compliance/controles/soc-2',
      stats: dashboard?.byFramework?.['SOC2'] || null
    },
    {
      key: 'SOX',
      name: 'SOX',
      description: 'Sarbanes-Oxley Compliance',
      icon: <Scale className="w-6 h-6 text-gray-600 dark:text-gray-400" />,
      href: '/admin/compliance/controles/sox',
      stats: dashboard?.byFramework?.['SOX'] || null
    }
  ]

  const totalControls = dashboard?.totalControls || 0
  const totalImplemented = dashboard?.totalImplemented || 0
  const overallPercentage = dashboard?.overallCompliancePercentage || 0

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Carregando biblioteca de controles...
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
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <FileCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Biblioteca de Controles
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Controles de segurança e conformidade por framework
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Atualizando...' : 'Atualizar'}
          </Button>
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                  Visão Geral de Conformidade
                </h2>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Status consolidado de todos os frameworks
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                  {Math.round(overallPercentage)}%
                </p>
                <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Conformidade Global
                </p>
              </div>
            </div>
            <Progress value={overallPercentage} className="h-2 mb-4" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    {totalImplemented}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Implementados
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-status-warning" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    {Object.values(dashboard?.byFramework || {}).reduce((acc, fw) => acc + fw.inProgress, 0)}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Em Progresso
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-wedo-orange" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    {Object.values(dashboard?.byFramework || {}).reduce((acc, fw) => acc + fw.notStarted, 0)}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Não Iniciados
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    {Object.values(dashboard?.byFramework || {}).reduce((acc, fw) => acc + fw.notApplicable, 0)}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    N/A
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div>
          <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--eleven-text-primary)' }}>
            Frameworks de Compliance
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {frameworkCards.map((framework) => (
              <Link key={framework.key} href={framework.href}>
                <Card 
                  className="h-full transition-all hover:cursor-pointer"
                  style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-4">
                      <div 
                        className="w-12 h-12 rounded-md flex items-center justify-center"
                        style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                      >
                        {framework.icon}
                      </div>
                      {getStatusBadge(framework.stats)}
                    </div>
                    <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {framework.name}
                    </h3>
                    <p className="text-xs mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      {framework.description}
                    </p>
                    {framework.stats ? (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {framework.stats.implemented + framework.stats.verified} / {framework.stats.totalControls} controles
                          </span>
                          <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                            {Math.round(framework.stats.compliancePercentage)}%
                          </span>
                        </div>
                        <Progress 
                          value={framework.stats.compliancePercentage} 
                          className="h-1.5"
                        />
                      </>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          Nenhum controle configurado
                        </span>
                      </div>
                    )}
                    <div className="flex items-center justify-end mt-3">
                      <span className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1">
                        Ver controles <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}

            <Link href="/admin/compliance/controles/cobertura">
              <Card 
                className="h-full transition-all hover:cursor-pointer border-dashed"
                style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}
              >
                <CardContent className="p-5 flex flex-col h-full">
                  <div className="flex items-start justify-between mb-4">
                    <div 
                      className="w-12 h-12 rounded-md flex items-center justify-center"
                      style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                    >
                      <Grid3X3 className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                    </div>
                    <Badge variant="info">Cross-Framework</Badge>
                  </div>
                  <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    Mapa de Cobertura
                  </h3>
                  <p className="text-xs mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Análise de gaps e sobreposição entre frameworks
                  </p>
                  <div className="flex-1" />
                  <div className="flex items-center justify-end mt-3">
                    <span className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      Ver cobertura <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardContent className="p-6">
            <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--eleven-text-primary)' }}>
              Legenda de Status
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-status-success" />
                <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Implementado / Verificado
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-status-warning" />
                <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Em Progresso
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-wedo-orange" />
                <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Não Iniciado
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-300" />
                <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Não Aplicável
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-700 dark:bg-gray-300" />
                <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Verificado
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
