"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Activity, Wifi, Server, Database, Clock, Zap, AlertTriangle,
  CheckCircle, XCircle, TrendingUp, TrendingDown, Users, Briefcase,
  Eye, RefreshCw, Play, Pause, BarChart3, Cpu, HardDrive,
  Network, Router, Globe, Signal, BatteryFull, BatteryLow,
  Timer, ArrowUpRight, ArrowDownRight, Minimize2,
  Maximize2, Settings, Download, Share2, Filter, Calendar
} from "lucide-react"

interface SystemMetric {
  id: string
  name: string
  status: 'healthy' | 'warning' | 'critical' | 'offline'
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  lastUpdate: string
  threshold: { warning: number; critical: number }
}

interface ATSConnection {
  id: string
  name: string
  type: 'sap' | 'workday' | 'bamboohr' | 'greenhouse'
  status: 'connected' | 'syncing' | 'error' | 'offline'
  latency: number
  throughput: number
  lastSync: string
  recordsProcessed: number
  errorRate: number
  uptime: number
}

interface WorkflowExecution {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed' | 'queued'
  progress: number
  startTime: string
  estimatedCompletion?: string
  stepsCurrent: number
  stepsTotal: number
  lastAction: string
}

export function RealTimeDashboardPage() {
  const [isLive, setIsLive] = useState(true)
  const [selectedTimeframe, setSelectedTimeframe] = useState("5m")
  const [refreshInterval, setRefreshInterval] = useState(5000)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  // Simular dados em tempo real
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([
    {
      id: "cpu",
      name: "CPU Usage",
      status: "healthy",
      value: 45,
      unit: "%",
      trend: "stable",
      lastUpdate: new Date().toISOString(),
      threshold: { warning: 70, critical: 90 }
    },
    {
      id: "memory",
      name: "Memory Usage",
      status: "warning",
      value: 78,
      unit: "%",
      trend: "up",
      lastUpdate: new Date().toISOString(),
      threshold: { warning: 75, critical: 90 }
    },
    {
      id: "database",
      name: "Database Response",
      status: "healthy",
      value: 24,
      unit: "ms",
      trend: "down",
      lastUpdate: new Date().toISOString(),
      threshold: { warning: 100, critical: 200 }
    },
    {
      id: "api",
      name: "API Response Time",
      status: "healthy",
      value: 120,
      unit: "ms",
      trend: "stable",
      lastUpdate: new Date().toISOString(),
      threshold: { warning: 500, critical: 1000 }
    }
  ])

  const [atsConnections, setATSConnections] = useState<ATSConnection[]>([
    {
      id: "sap_sf",
      name: "SAP SuccessFactors",
      type: "sap",
      status: "connected",
      latency: 45,
      throughput: 1247,
      lastSync: "2 min ago",
      recordsProcessed: 15680,
      errorRate: 0.2,
      uptime: 99.8
    },
    {
      id: "workday",
      name: "Workday HCM",
      type: "workday",
      status: "syncing",
      latency: 78,
      throughput: 856,
      lastSync: "syncing...",
      recordsProcessed: 8943,
      errorRate: 0.1,
      uptime: 99.9
    },
    {
      id: "bamboo",
      name: "BambooHR",
      type: "bamboohr",
      status: "error",
      latency: 0,
      throughput: 0,
      lastSync: "15 min ago",
      recordsProcessed: 4521,
      errorRate: 2.3,
      uptime: 97.2
    }
  ])

  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([
    {
      id: "wf_1",
      name: "Triagem Automática - Frontend Dev",
      status: "running",
      progress: 65,
      startTime: "14:32",
      estimatedCompletion: "14:47",
      stepsCurrent: 3,
      stepsTotal: 5,
      lastAction: "Analyzing candidate profiles"
    },
    {
      id: "wf_2",
      name: "Envio de NPS - UX Designers",
      status: "completed",
      progress: 100,
      startTime: "14:20",
      stepsCurrent: 4,
      stepsTotal: 4,
      lastAction: "Emails sent successfully"
    },
    {
      id: "wf_3",
      name: "Sync Candidates - SAP",
      status: "queued",
      progress: 0,
      startTime: "14:45",
      stepsCurrent: 0,
      stepsTotal: 3,
      lastAction: "Waiting for queue"
    }
  ])

  // Simular atualizações em tempo real
  useEffect(() => {
    if (!isLive) return

    const interval = setInterval(() => {
      // Atualizar métricas do sistema
      setSystemMetrics(prev => prev.map(metric => ({
        ...metric,
        value: Math.max(0, metric.value + (Math.random() - 0.5) * 10),
        lastUpdate: new Date().toISOString(),
        trend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable'
      })))

      // Atualizar workflows
      setWorkflows(prev => prev.map(wf => ({
        ...wf,
        progress: wf.status === 'running' ? Math.min(100, wf.progress + Math.random() * 5) : wf.progress
      })))

      setLastRefresh(new Date())
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [isLive, refreshInterval])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'completed':
        return 'text-status-success bg-status-success/15 border-status-success/30'
      case 'warning':
      case 'syncing':
      case 'running':
        return 'text-status-warning bg-status-warning/15 border-status-warning/30'
      case 'critical':
      case 'error':
      case 'failed':
        return 'text-status-error bg-status-error/15 border-status-error/30'
      case 'offline':
      case 'queued':
        return 'text-lia-text-secondary bg-gray-100 border-lia-border-subtle'
      default:
        return 'text-lia-text-secondary bg-gray-100 border-lia-border-subtle'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'completed':
        return <CheckCircle className="w-4 h-4" />
      case 'warning':
      case 'syncing':
      case 'running':
        return <AlertTriangle className="w-4 h-4" />
      case 'critical':
      case 'error':
      case 'failed':
        return <XCircle className="w-4 h-4" />
      case 'offline':
      case 'queued':
        return <Clock className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-status-success" />
      case 'down': return <TrendingDown className="w-3 h-3 text-status-error" />
      default: return <div className="w-3 h-3 bg-gray-400 rounded-full" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
      <div className="max-w-full mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1 flex items-center gap-1.5">
                <Activity className="w-6 h-6 text-status-success" />
                Dashboard de Performance em Tempo Real
                {isLive && (
                  <div className="flex items-center gap-2 ml-4">
                    <div className="w-2 h-2 bg-status-success rounded-full animate-pulse" />
                    <span className="text-sm text-status-success font-medium">LIVE</span>
                  </div>
                )}
              </h1>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Monitoramento em tempo real de sistemas ATS, workflows e performance da plataforma
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant={isLive ? "default" : "outline"}
                size="sm"
                onClick={() => setIsLive(!isLive)}
                className="gap-2"
              >
                {isLive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isLive ? 'Pausar' : 'Ativar'} Live
              </Button>

              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
              >
                <option value="1m">1 minuto</option>
                <option value="5m">5 minutos</option>
                <option value="15m">15 minutos</option>
                <option value="1h">1 hora</option>
              </select>

              <Button variant="outline" size="sm" className="gap-2">
                <Download className="w-4 h-4" />
                Exportar
              </Button>
            </div>
          </div>

          <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
            Última atualização: {lastRefresh.toLocaleTimeString('pt-BR')} •
            Atualizando a cada {refreshInterval / 1000}s
          </div>
        </div>

        {/* System Health Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {systemMetrics.map((metric) => (
            <Card key={metric.id} className="relative overflow-hidden">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {metric.id === 'cpu' && <Cpu className="w-4 h-4 text-lia-text-secondary" />}
                    {metric.id === 'memory' && <HardDrive className="w-4 h-4 text-lia-text-secondary" />}
                    {metric.id === 'database' && <Database className="w-4 h-4 text-lia-text-secondary" />}
                    {metric.id === 'api' && <Network className="w-4 h-4 text-lia-text-secondary" />}
                    <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{metric.name}</span>
                  </div>
                  {getTrendIcon(metric.trend)}
                </div>

                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {Math.round(metric.value)}{metric.unit}
                    </div>
                    <Badge variant="outline" className={`text-xs ${getStatusColor(metric.status)}`}>
                      {getStatusIcon(metric.status)}
                      <span className="ml-1">{metric.status}</span>
                    </Badge>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-[width,height] ${
                        metric.value >= metric.threshold.critical ? 'bg-status-error' :
                        metric.value >= metric.threshold.warning ? 'bg-status-warning' : 'bg-status-success'
                      }`}
                      style={{width: `${Math.min(100, (metric.value / metric.threshold.critical) * 100)}%`}}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* ATS Connections Status */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Status das Conexões ATS
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {atsConnections.map((ats) => (
                <div key={ats.id} className="p-4 border border-lia-border-subtle rounded-md">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">{ats.name}</h4>
                      <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Última sync: {ats.lastSync}</p>
                    </div>
                    <Badge variant="outline" className={`${getStatusColor(ats.status)}`}>
                      {getStatusIcon(ats.status)}
                      <span className="ml-1 capitalize">{ats.status}</span>
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Latência:</span>
                      <div className="font-medium">{ats.latency}ms</div>
                    </div>
                    <div>
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Throughput:</span>
                      <div className="font-medium">{ats.throughput}/min</div>
                    </div>
                    <div>
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Registros:</span>
                      <div className="font-medium">{ats.recordsProcessed.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Uptime:</span>
                      <div className="font-medium text-status-success">{ats.uptime}%</div>
                    </div>
                  </div>

                  {ats.errorRate > 0 && (
                    <div className="mt-3 p-2 bg-status-error/10 rounded-md text-xs">
                      <span className="text-status-error">Taxa de erro: {ats.errorRate}%</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Active Workflows */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-wedo-purple" />
              Workflows em Execução
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {workflows.map((workflow) => (
                <div key={workflow.id} className="p-4 border border-lia-border-subtle rounded-md">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">{workflow.name}</h4>
                      <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                        Iniciado às {workflow.startTime} •
                        Etapa {workflow.stepsCurrent} de {workflow.stepsTotal}
                      </p>
                    </div>
                    <Badge variant="outline" className={`${getStatusColor(workflow.status)}`}>
                      {getStatusIcon(workflow.status)}
                      <span className="ml-1 capitalize">{workflow.status}</span>
                    </Badge>
                  </div>

                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progresso</span>
                      <span>{workflow.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full transition-[width,height] duration-500"
                        style={{width: `${workflow.progress}%`}}
                      />
                    </div>
                  </div>

                  <div className="text-xs text-lia-text-secondary">
                    <span className="font-medium">Última ação:</span> {workflow.lastAction}
                    {workflow.estimatedCompletion && (
                      <span className="ml-4">
                        <span className="font-medium">Conclusão estimada:</span> {workflow.estimatedCompletion}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Real-time Activity Feed */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-status-success" />
              Feed de Atividades em Tempo Real
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {[
                { time: "14:45:32", event: "Nova sincronização iniciada", system: "SAP SuccessFactors", type: "info" },
                { time: "14:45:18", event: "Workflow 'Triagem Automática' completou etapa 3/5", system: "Automation Engine", type: "success" },
                { time: "14:44:55", event: "15 candidatos processados com sucesso", system: "Pipeline", type: "success" },
                { time: "14:44:42", event: "Conexão com BambooHR apresentou timeout", system: "BambooHR", type: "error" },
                { time: "14:44:31", event: "CPU usage atingiu 78% - limite de warning", system: "System Monitor", type: "warning" },
                { time: "14:44:12", event: "Backup automático concluído", system: "Database", type: "info" },
                { time: "14:43:58", event: "Novo candidato adicionado ao pipeline", system: "Recruitment", type: "success" },
                { time: "14:43:45", event: "Email NPS enviado para 23 candidatos", system: "Communication", type: "success" }
              ].map((activity, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
                  <div className="text-xs text-lia-text-primary dark:text-lia-text-primary w-16">{activity.time}</div>
                  <div className={`w-2 h-2 rounded-full ${
                    activity.type === 'success' ? 'bg-status-success' :
                    activity.type === 'warning' ? 'bg-status-warning' :
                    activity.type === 'error' ? 'bg-status-error' : 'bg-gray-700 dark:bg-gray-300'
                  }`} />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{activity.event}</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">{activity.system}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
