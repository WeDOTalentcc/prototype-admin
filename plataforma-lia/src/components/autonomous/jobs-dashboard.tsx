"use client"

import React, { useState, useEffect } from "react"
import { 
  Play, RefreshCw, Clock, CheckCircle2, 
  XCircle, Loader2, Calendar, Search, Plus,
  Users, FileSearch, BarChart3, Mail, TrendingUp, Brain,
  Eye, AlertCircle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { listBackgroundJobs, executeJob } from "@/services/lia-api"
import { CreateJobModal } from "./create-job-modal"

const JOB_TYPE_ICONS: Record<string, React.ElementType> = {
  screening: Users,
  sourcing: FileSearch,
  report_generation: BarChart3,
  candidate_outreach: Mail,
  market_analysis: TrendingUp,
  pattern_learning: Brain
}

const JOB_TYPE_LABELS: Record<string, string> = {
  screening: 'Triagem de Candidatos',
  sourcing: 'Busca de Talentos',
  report_generation: 'Geração de Relatórios',
  candidate_outreach: 'Contato com Candidatos',
  market_analysis: 'Análise de Mercado',
  pattern_learning: 'Aprendizado de Padrões'
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendente',
  running: 'Em Execução',
  completed: 'Concluído',
  failed: 'Falhou',
  cancelled: 'Cancelado'
}

interface BackgroundJob {
  id: string
  name: string
  job_type: string
  status: string
  progress?: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  result_summary?: string
  config?: Record<string, any>
}

interface JobsDashboardProps {
  className?: string
  onJobSelect?: (job: BackgroundJob) => void
}

export function JobsDashboard({ className, onJobSelect }: JobsDashboardProps) {
  const [jobs, setJobs] = useState<BackgroundJob[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [executingJobId, setExecutingJobId] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    loadJobs()
  }, [statusFilter])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const result = await listBackgroundJobs(
        statusFilter === 'all' ? undefined : statusFilter, 
        50
      )
      setJobs(result || [])
    } catch (error) {
      console.error('Erro ao carregar jobs:', error)
      setJobs([])
    }
    setLoading(false)
  }

  const handleExecuteJob = async (jobId: string) => {
    setExecutingJobId(jobId)
    try {
      await executeJob(jobId)
      await loadJobs()
    } catch (error) {
      console.error('Erro ao executar job:', error)
    }
    setExecutingJobId(null)
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
      running: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
      completed: 'bg-green-500/10 text-green-600 dark:text-green-400',
      failed: 'bg-red-500/10 text-red-600 dark:text-red-400',
      cancelled: 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
    }
    return styles[status] || styles.pending
  }

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ElementType> = {
      pending: Clock,
      running: Loader2,
      completed: CheckCircle2,
      failed: XCircle,
      cancelled: AlertCircle
    }
    return icons[status] || Clock
  }

  const filteredJobs = jobs.filter(job => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      return (
        job.name.toLowerCase().includes(search) ||
        JOB_TYPE_LABELS[job.job_type]?.toLowerCase().includes(search)
      )
    }
    return true
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Jobs Autônomos
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Gerencie tarefas de background executadas pela LIA
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadJobs}
            disabled={loading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-1", loading && "animate-spin")} />
            Atualizar
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            <Plus className="h-4 w-4 mr-1" />
            Novo Job
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar jobs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os Status</SelectItem>
            <SelectItem value="pending">Pendente</SelectItem>
            <SelectItem value="running">Em Execução</SelectItem>
            <SelectItem value="completed">Concluído</SelectItem>
            <SelectItem value="failed">Falhou</SelectItem>
            <SelectItem value="cancelled">Cancelado</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-600 dark:text-gray-400" />
        </div>
      ) : filteredJobs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
              <Calendar className="h-6 w-6 text-gray-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
              Nenhum job encontrado
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center max-w-sm">
              {searchTerm || statusFilter !== 'all'
                ? 'Tente ajustar os filtros de busca'
                : 'Crie seu primeiro job autônomo para a LIA executar tarefas em background'}
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button
                size="sm"
                className="mt-4 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus className="h-4 w-4 mr-1" />
                Criar Job
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredJobs.map((job) => {
            const TypeIcon = JOB_TYPE_ICONS[job.job_type] || Brain
            const StatusIcon = getStatusIcon(job.status)
            const isExecuting = executingJobId === job.id

            return (
              <Card
                key={job.id}
                className="rounded-md hover:border-gray-400 dark:hover:border-gray-500 transition-colors cursor-pointer dark:bg-gray-800 dark:border-gray-700"
                onClick={() => onJobSelect?.(job)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <TypeIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="truncate" style={{ fontFamily: 'Open Sans, sans-serif' }}>{job.name}</CardTitle>
                        <CardDescription className="truncate">
                          {JOB_TYPE_LABELS[job.job_type] || job.job_type}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge className={cn("shrink-0", getStatusBadge(job.status))}>
                      <StatusIcon className={cn(
                        "h-3 w-3 mr-1",
                        job.status === 'running' && "animate-spin"
                      )} />
                      {STATUS_LABELS[job.status] || job.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {job.status === 'running' && job.progress !== undefined && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-micro text-gray-500">
                        <span>Progresso</span>
                        <span>{Math.round(job.progress)}%</span>
                      </div>
                      <Progress value={job.progress} className="h-1.5" />
                    </div>
                  )}

                  {job.result_summary && job.status === 'completed' && (
                    <p className="text-micro text-gray-600 dark:text-gray-400 line-clamp-2">
                      {job.result_summary}
                    </p>
                  )}

                  {job.error_message && job.status === 'failed' && (
                    <p className="text-micro text-red-600 dark:text-red-400 line-clamp-2">
                      {job.error_message}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800">
                    <span className="text-micro text-gray-400">
                      {formatDate(job.created_at)}
                    </span>
                    <div className="flex items-center gap-1">
                      {job.status === 'pending' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleExecuteJob(job.id)
                          }}
                          disabled={isExecuting}
                        >
                          {isExecuting ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Play className="h-3 w-3" />
                          )}
                          <span className="ml-1 text-micro">Executar</span>
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2"
                        onClick={(e) => {
                          e.stopPropagation()
                          onJobSelect?.(job)
                        }}
                      >
                        <Eye className="h-3 w-3" />
                        <span className="ml-1 text-micro">Ver</span>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <CreateJobModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onJobCreated={() => {
          setShowCreateModal(false)
          loadJobs()
        }}
      />
    </div>
  )
}
