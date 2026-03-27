"use client"

import React from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  ClipboardList,
  ScrollText,
  Scale,
  Users,
  GraduationCap,
  Download,
  ArrowRight,
  Activity,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  FileArchive,
} from "lucide-react"

const dashboardStats = {
  totalLogs: 12847,
  lastBiasAudit: '2024-12-01',
  sodConflicts: 3,
  trainingRate: 87,
}

const recentActivity = [
  { id: 1, action: 'Exportação de evidências SOC 2', user: 'Maria Silva', time: 'Há 2 horas', type: 'export' },
  { id: 2, action: 'Auditoria de bias mensal concluída', user: 'Sistema', time: 'Há 1 dia', type: 'bias' },
  { id: 3, action: 'Treinamento LGPD completado por 5 usuários', user: 'Sistema', time: 'Há 2 dias', type: 'training' },
  { id: 4, action: 'Revisão de matriz SoD', user: 'Carlos Santos', time: 'Há 3 dias', type: 'sod' },
  { id: 5, action: 'Atualização de política de retenção', user: 'Ana Costa', time: 'Há 5 dias', type: 'logs' },
]

const scheduledAudits = [
  { id: 1, name: 'Auditoria de Bias Mensal', date: '2025-01-15', type: 'bias', status: 'scheduled' },
  { id: 2, name: 'Revisão SOC 2 Type II', date: '2025-02-01', type: 'external', status: 'scheduled' },
  { id: 3, name: 'Auditoria Interna LGPD', date: '2025-02-15', type: 'internal', status: 'scheduled' },
  { id: 4, name: 'Revisão Matriz SoD', date: '2025-03-01', type: 'sod', status: 'scheduled' },
]

const quickLinks = [
  {
    title: 'Audit Logs (SOX)',
    description: 'Trilha de auditoria completa para conformidade SOX',
    href: '/admin/compliance/auditoria/logs',
    icon: ScrollText,
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
  },
  {
    title: 'Auditorias de Bias',
    description: 'Análise de viés algorítmico e fairness em IA',
    href: '/admin/compliance/auditoria/bias',
    icon: Scale,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
  },
  {
    title: 'Matriz SoD',
    description: 'Segregação de Funções (Segregation of Duties)',
    href: '/admin/compliance/auditoria/sod',
    icon: Users,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
  },
  {
    title: 'Tracking de Treinamentos',
    description: 'Acompanhamento de treinamentos de segurança e compliance',
    href: '/admin/compliance/auditoria/treinamentos',
    icon: GraduationCap,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
  },
  {
    title: 'Gerador de Pacote para Auditores',
    description: 'Exportação de evidências e documentação',
    href: '/admin/compliance/auditoria/exportar',
    icon: FileArchive,
    color: 'text-rose-600',
    bgColor: 'bg-rose-50 dark:bg-rose-900/20',
  },
]

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'export':
      return <Download className="w-4 h-4 text-rose-500" />
    case 'bias':
      return <Scale className="w-4 h-4 text-purple-500" />
    case 'training':
      return <GraduationCap className="w-4 h-4 text-emerald-500" />
    case 'sod':
      return <Users className="w-4 h-4 text-amber-500" />
    case 'logs':
      return <ScrollText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
    default:
      return <Activity className="w-4 h-4 text-gray-500" />
  }
}

const getAuditTypeBadge = (type: string) => {
  switch (type) {
    case 'bias':
      return <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400">Bias</Badge>
    case 'external':
      return <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">Externa</Badge>
    case 'internal':
      return <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400">Interna</Badge>
    case 'sod':
      return <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">SoD</Badge>
    default:
      return <Badge variant="secondary">{type}</Badge>
  }
}

export default function AuditoriaPage() {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
          >
            <ClipboardList className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold"
              style={{ 
                color: 'var(--eleven-text-primary)',
                
              }}
            >
              Sala de Auditoria
            </h1>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Central de recursos para auditores internos e externos
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total de Registros</p>
                  <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                    {dashboardStats.totalLogs.toLocaleString('pt-BR')}
                  </p>
                </div>
                <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <ScrollText className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                <span>Retenção: 7 anos (SOX)</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Última Auditoria de Bias</p>
                  <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                    {formatDate(dashboardStats.lastBiasAudit)}
                  </p>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md">
                  <Scale className="w-6 h-6 text-purple-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-1 text-xs text-emerald-600">
                <CheckCircle2 className="w-3 h-3" />
                <span>Aprovada</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Conflitos SoD Detectados</p>
                  <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                    {dashboardStats.sodConflicts}
                  </p>
                </div>
                <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-md">
                  <Users className="w-6 h-6 text-amber-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-1 text-xs text-amber-600">
                <AlertTriangle className="w-3 h-3" />
                <span>2 mitigados, 1 pendente</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Taxa de Treinamentos</p>
                  <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                    {dashboardStats.trainingRate}%
                  </p>
                </div>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-md">
                  <GraduationCap className="w-6 h-6 text-emerald-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-1 text-xs text-emerald-600">
                <CheckCircle2 className="w-3 h-3" />
                <span>Acima da meta (85%)</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium">Acesso Rápido</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {quickLinks.map((link) => {
                    const Icon = link.icon
                    return (
                      <Link
                        key={link.href}
                        href={link.href}
                        className="group p-4 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-900 dark:hover:border-gray-50 hover:transition-all"
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-md ${link.bgColor}`}>
                            <Icon className={`w-5 h-5 ${link.color}`} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h3 className="font-medium text-gray-950 dark:text-gray-50 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors">
                                {link.title}
                              </h3>
                              <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
                            </div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                              {link.description}
                            </p>
                          </div>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    Auditorias Programadas
                  </CardTitle>
                  <Badge variant="outline">{scheduledAudits.length} próximas</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scheduledAudits.map((audit) => (
                    <div 
                      key={audit.id}
                      className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-900 dark:hover:border-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Calendar className="w-4 h-4" />
                          {formatDate(audit.date)}
                        </div>
                        <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                          {audit.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getAuditTypeBadge(audit.type)}
                        <Badge variant="outline" className="text-xs">Agendada</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    Atividade Recente
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start gap-3">
                      <div className="mt-0.5">
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-950 dark:text-gray-50 truncate">
                          {activity.action}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500">{activity.user}</span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">{activity.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-md">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      Conformidade SOX
                    </p>
                    <p className="text-xs text-gray-500">
                      Retenção de 7 anos ativa (Section 802)
                    </p>
                  </div>
                  <Badge variant="success" className="ml-auto">Ativo</Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-md">
                    <Scale className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      NYC LL144 Compliance
                    </p>
                    <p className="text-xs text-gray-500">
                      Auditoria de bias ativa
                    </p>
                  </div>
                  <Badge variant="success" className="ml-auto">Ativo</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
