"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { Lock, Users, CheckCircle, AlertTriangle, UserCheck, ChevronRight, Clock, ExternalLink, Shield, Globe, CheckSquare, FileText, UserCircle, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { lgpdService, LGPDStats } from "@/services/admin/lgpd-service"

const complianceAlerts = [
  { id: 1, type: 'warning', message: 'Verifique os DSRs próximos do prazo legal de 15 dias', action: 'Ver DSRs' },
  { id: 2, type: 'info', message: 'Versão do termo de consentimento aguardando aprovação', action: 'Revisar' },
  { id: 3, type: 'error', message: 'Transferências internacionais requerem revisão periódica', action: 'Verificar' },
]

export default function LGPDPage() {
  const [stats, setStats] = useState<LGPDStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    lgpdService.getStats("platform")
      .then(setStats)
      .catch(() => {/* silently fail — stats serão 0 */})
      .finally(() => setIsLoading(false))
  }, [])

  const dposRegistrados = stats?.dpoRegistered ? 1 : 0
  const dsrsPendentes = 0  // dados reais disponíveis em /admin/compliance/lgpd/portal-titular
  const incidentesLGPD = stats?.openBreaches ?? 0

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Ativo</Badge>
      case 'pending':
        return <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Pendente</Badge>
      case 'in_progress':
        return <Badge className="text-gray-600 dark:text-gray-400 hover:bg-gray-100">Em andamento</Badge>
      case 'completed':
        return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Concluído</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <Clock className="w-4 h-4 text-amber-500" />
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      default:
        return <Shield className="w-4 h-4 text-gray-600 dark:text-gray-400" />
    }
  }

  const getAlertBg = (type: string) => {
    switch (type) {
      case 'warning':
        return 'rgba(245, 158, 11, 0.05)'
      case 'error':
        return 'rgba(239, 68, 68, 0.05)'
      default:
        return 'rgba(229, 231, 235, 0.2)'
    }
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <Lock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1
                className="text-xl font-semibold"
                style={{ color: 'var(--eleven-text-primary)' }}
              >
                LGPD & Privacidade
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Gestão de privacidade e conformidade com a Lei Geral de Proteção de Dados
              </p>
            </div>
          </div>
          <Button asChild>
            <Link href="/admin/compliance/lgpd/portal-titular">
              <ExternalLink className="w-4 h-4 mr-2" />
              Portal do Titular
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    DPO Registrado
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : (stats?.dpoRegistered ? 'Sim' : 'Não')}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <UserCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Consentimentos Ativos
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    —
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Ver em Consentimentos
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    DSRs Pendentes
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {dsrsPendentes}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Ver no Portal do Titular
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                  <Clock className="w-5 h-5 text-amber-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Incidentes LGPD
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : incidentesLGPD}
                  </p>
                  {stats?.breachesPendingAnpd ? (
                    <p className="text-xs mt-1 text-red-600">
                      {stats.breachesPendingAnpd} pendentes ANPD
                    </p>
                  ) : null}
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Link href="/admin/compliance/lgpd/dpo">
            <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer h-full" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <UserCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>DPOs</p>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Registro de DPOs</p>
                  </div>
                  <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/portal-titular">
            <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer h-full" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Portal Titular</p>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Art. 18 LGPD</p>
                  </div>
                  <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/consentimentos">
            <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer h-full" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <CheckSquare className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Consentimentos</p>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Gestão de termos</p>
                  </div>
                  <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/transferencias">
            <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer h-full" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Transferências</p>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Dados internacionais</p>
                  </div>
                  <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    DSRs Pendentes
                  </CardTitle>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/admin/compliance/lgpd/portal-titular">
                      Ver todos
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <FileText className="w-8 h-8 mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    Gerencie as DSRs no Portal do Titular
                  </p>
                  <p className="text-xs mt-1 mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    As solicitações de titulares (Art. 18 LGPD) são gerenciadas na página dedicada.
                  </p>
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/admin/compliance/lgpd/portal-titular">
                      Abrir Portal do Titular
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  DPOs Cadastrados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4 text-center">
                  <UserCheck className="w-6 h-6 mb-2" style={{ color: 'var(--eleven-text-tertiary)' }} />
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    {isLoading ? 'Carregando...' : stats?.dpoRegistered ? 'DPO registrado' : 'Nenhum DPO cadastrado'}
                  </p>
                </div>
                <Button variant="ghost" size="sm" className="w-full mt-2" asChild>
                  <Link href="/admin/compliance/lgpd/dpo">
                    Gerenciar DPOs
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    Consentimentos
                  </CardTitle>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/admin/compliance/lgpd/consentimentos">
                      Ver todos
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4 text-center">
                  <CheckSquare className="w-6 h-6 mb-2" style={{ color: 'var(--eleven-text-tertiary)' }} />
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Dados de consentimento disponíveis na página dedicada.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Alertas de Compliance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {complianceAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-3 p-3 rounded-md"
                      style={{ backgroundColor: getAlertBg(alert.type) }}
                    >
                      {getAlertIcon(alert.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {alert.message}
                        </p>
                        <Button variant="link" size="sm" className="h-auto p-0 mt-1 text-xs text-gray-600 dark:text-gray-400">
                          {alert.action} →
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
