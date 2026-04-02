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
        return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Ativo</Badge>
      case 'pending':
        return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Pendente</Badge>
      case 'in_progress':
        return <Badge className="text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-lia-bg-tertiary">Em andamento</Badge>
      case 'completed':
        return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Concluído</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <Clock className="w-4 h-4 text-status-warning" />
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-status-error" />
      default:
        return <Shield className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
    }
  }

  const getAlertBg = (type: string) => {
    switch (type) {
      case 'warning':
        return 'var(--status-warning-bg-05)'
      case 'error':
        return 'var(--status-error-bg)'
      default:
        return 'var(--lia-bg-tertiary)'
    }
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <Lock className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                LGPD & Privacidade
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
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
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between" role="status" aria-live="polite" aria-label="Carregando...">
                <div role="status" aria-live="polite" aria-label="Carregando...">
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    DPO Registrado
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" /> : (stats?.dpoRegistered ? 'Sim' : 'Não')}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <UserCircle className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Consentimentos Ativos
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    —
                  </p>
                  <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Ver em Consentimentos
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckCircle className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    DSRs Pendentes
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {dsrsPendentes}
                  </p>
                  <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Ver no Portal do Titular
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-amber-500/10">
                  <Clock className="w-5 h-5 text-status-warning" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between" role="status" aria-live="polite" aria-label="Carregando...">
                <div role="status" aria-live="polite" aria-label="Carregando...">
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Incidentes LGPD
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : incidentesLGPD}
                  </p>
                  {stats?.breachesPendingAnpd ? (
                    <p className="text-xs mt-1 text-status-error">
                      {stats.breachesPendingAnpd} pendentes ANPD
                    </p>
                  ) : null}
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Link href="/admin/compliance/lgpd/dpo">
            <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer h-full" >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <UserCheck className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >DPOs</p>
                    <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Registro de DPOs</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/portal-titular">
            <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer h-full" >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <FileText className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >Portal Titular</p>
                    <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Art. 18 LGPD</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/consentimentos">
            <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer h-full" >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <CheckSquare className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >Consentimentos</p>
                    <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Gestão de termos</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/admin/compliance/lgpd/transferencias">
            <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer h-full" >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <Globe className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >Transferências</p>
                    <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Dados internacionais</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
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
                  <FileText className="w-8 h-8 mb-3 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                  <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    Gerencie as DSRs no Portal do Titular
                  </p>
                  <p className="text-xs mt-1 mb-4 text-lia-text-tertiary dark:text-lia-text-secondary" >
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
            <Card >
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  DPOs Cadastrados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4 text-center">
                  <UserCheck className="w-6 h-6 mb-2 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
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

            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
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
                  <CheckSquare className="w-6 h-6 mb-2 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Dados de consentimento disponíveis na página dedicada.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card >
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary" >
                  <AlertTriangle className="w-4 h-4 text-status-warning" />
                  Alertas de Compliance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {complianceAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-3 p-3 rounded-md"
                      style={{backgroundColor: getAlertBg(alert.type)}}
                    >
                      {getAlertIcon(alert.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary" >
                          {alert.message}
                        </p>
                        <Button variant="link" size="sm" className="h-auto p-0 mt-1 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
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
