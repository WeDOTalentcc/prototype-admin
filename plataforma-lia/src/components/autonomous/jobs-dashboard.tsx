"use client"

import React, { useState, useEffect } from"react"
import { 
  Play, RefreshCw, Clock, CheckCircle2, 
  XCircle, Loader2, Calendar, Search, Plus,
  Users, FileSearch, BarChart3, Mail, TrendingUp, Brain,
  Eye, AlertCircle
} from"lucide-react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from"@/components/ui/card"
import { Chip, type ChipVariant } from"@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import { Input } from"@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import { cn } from"@/lib/utils"
import { listBackgroundJobs, executeJob } from"@/services/lia-api"
import { CreateJobModal } from"./create-job-modal"

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
  config?: Record<string, unknown>
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    }
    setExecutingJobId(null)
  }

  const getStatusVariant = (status: string): ChipVariant => {
    const map: Record<string, ChipVariant> = {
      pending: 'warning',
      running: 'info',
      completed: 'success',
      failed: 'danger',
      cancelled: 'neutral',
    }
    return map[status] || 'warning'
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
          <h2 className="text-lg font-semibold text-lia-text-primary">
            Jobs Autônomos
          </h2>
          <p className="text-xs text-lia-text-tertiary">
            Gerencie tarefas de background executadas pela IA
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadJobs}
            disabled={loading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-1", loading &&"animate-spin motion-reduce:animate-none")} />
            Atualizar
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            <Plus className="h-4 w-4 mr-1" />
            Novo Job
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lia-text-secondary" />
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
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
        </div>
      ) : filteredJobs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mb-4">
              <Calendar className="h-6 w-6 text-lia-text-secondary" />
            </div>
            <h3 className="text-sm font-medium text-lia-text-primary mb-1">
              Nenhum job encontrado
            </h3>
            <p className="text-xs text-lia-text-tertiary text-center max-w-sm">
              {searchTerm || statusFilter !== 'all'
                ? 'Tente ajustar os filtros de busca'
                : 'Crie seu primeiro job autônomo para a IA executar tarefas em background'}
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button
                size="sm"
                className="mt-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
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
                className="rounded-xl hover:border-lia-border-medium dark:hover:border-lia-border-medium transition-colors motion-reduce:transition-none cursor-pointer dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
                onClick={() => onJobSelect?.(job)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                        <TypeIcon className="h-4 w-4 text-lia-text-secondary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="truncate">{job.name}</CardTitle>
                        <CardDescription className="truncate">
                          {JOB_TYPE_LABELS[job.job_type] || job.job_type}
                        </CardDescription>
                      </div>
                    </div>
                    <Chip variant={getStatusVariant(job.status)} className="shrink-0">
                      <StatusIcon className={cn("h-3 w-3",
                        job.status === 'running' &&"animate-spin motion-reduce:animate-none"
                      )} />
                      {STATUS_LABELS[job.status] || job.status}
                    </Chip>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {job.status === 'running' && job.progress !== undefined && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-micro text-lia-text-secondary">
                        <span>Progresso</span>
                        <span>{Math.round(job.progress)}%</span>
                      </div>
                      <Progress value={job.progress} className="h-1.5" />
                    </div>
                  )}

                  {job.result_summary && job.status === 'completed' && (
                    <p className="text-micro text-lia-text-secondary line-clamp-2">
                      {job.result_summary}
                    </p>
                  )}

                  {job.error_message && job.status === 'failed' && (
                    <p className="text-micro text-status-error dark:text-status-error line-clamp-2">
                      {job.error_message}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-lia-border-subtle">
                    <span className="text-micro text-lia-text-secondary">
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
                            <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
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
