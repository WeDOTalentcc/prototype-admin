"use client"

import React from"react"
import { Chip, type ChipVariant } from"@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import { 
  Users, Eye, Edit, Copy, Pause, XCircle,
  ArrowUpDown, ArrowUp, ArrowDown, MapPin, Building,
  Clock, Calendar, TrendingUp
} from"lucide-react"
import { JobCampaignBadge } from"@/components/jobs/JobCampaignBadge"
import type { JobVacancy, JobSortConfig } from"./types"

interface JobsTableProps {
  jobs: JobVacancy[]
  sortConfig: JobSortConfig
  onSort: (column: JobSortConfig['column']) => void
  onJobClick: (job: JobVacancy) => void
  onAction: (action: string, job: JobVacancy) => void
  isLoading: boolean
}

export function JobsTable({
  jobs,
  sortConfig,
  onSort,
  onJobClick,
  onAction,
  isLoading,
}: JobsTableProps) {
  const getSortIcon = (column: JobSortConfig['column']) => {
    if (sortConfig.column !== column) {
      return <ArrowUpDown className="h-4 w-4 text-lia-text-muted" />
    }
    return sortConfig.direction ==="asc"
      ? <ArrowUp className="h-4 w-4 text-lia-text-primary" />
      : <ArrowDown className="h-4 w-4 text-lia-text-primary" />
  }

  const getStatusBadge = (status: JobVacancy['status']) => {
    const config: Record<string, { label: string; variant: ChipVariant; muted?: boolean }> = {
      draft: { label:"Rascunho", variant:"warning" },
      active: { label:"Ativa", variant:"success" },
      paused: { label:"Pausada", variant:"warning" },
      closed: { label:"Encerrada", variant:"neutral", muted: true },
      cancelled: { label:"Cancelada", variant:"danger" },
    }
    const { label, variant, muted } = config[status] || config.draft
    return <Chip variant={variant} muted={muted}>{label}</Chip>
  }

  const getPriorityBadge = (priority: JobVacancy['priority']) => {
    const config: Record<string, { label: string; variant: ChipVariant; muted?: boolean }> = {
      low: { label:"Baixa", variant:"neutral", muted: true },
      medium: { label:"Média", variant:"info" },
      high: { label:"Alta", variant:"warning" },
      urgent: { label:"Urgente", variant:"danger" },
    }
    const { label, variant, muted } = config[priority] || config.medium
    return <Chip variant={variant} muted={muted}>{label}</Chip>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-lia-text-tertiary">Carregando vagas...</div>
      </div>
    )
  }

  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-lia-text-tertiary">
        <p className="text-lg">Nenhuma vaga encontrada</p>
        <p className="text-sm mt-2">Crie sua primeira vaga clicando no botão acima</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto" data-testid="jobs-table">
      <table className="w-full">
        <thead className="bg-lia-bg-secondary dark:bg-lia-bg-primary/50 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <tr>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("title")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Vaga
                {getSortIcon("title")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("status")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Status
                {getSortIcon("status")}
              </button>
            </th>
            <th className="text-center p-4">
              <button
                onClick={() => onSort("candidates")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Candidatos
                {getSortIcon("candidates")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("priority")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Prioridade
                {getSortIcon("priority")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("daysOpen")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Dias Aberta
                {getSortIcon("daysOpen")}
              </button>
            </th>
            <th className="text-right p-4">
              <span className="text-sm font-medium text-lia-text-tertiary">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              className="dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 cursor-pointer transition-colors motion-reduce:transition-none"
              onClick={() => onJobClick(job)}
            >
              <td className="p-4">
                <div>
                  <div className="font-medium text-lia-text-primary">{job.title}</div>
                  <div className="flex items-center gap-3 mt-1 text-sm text-lia-text-tertiary">
                    {job.department && (
                      <span className="flex items-center gap-1">
                        <Building className="h-3 w-3" />
                        {job.department}
                      </span>
                    )}
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {job.location}
                      </span>
                    )}
                  </div>
                </div>
              </td>
              <td className="p-4">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {getStatusBadge(job.status)}
                  <JobCampaignBadge jobId={job.id} />
                </div>
              </td>
              <td className="p-4 text-center">
                <div className="flex items-center justify-center gap-1">
                  <Users className="h-4 w-4 text-lia-text-muted" />
                  <span className="text-lia-text-primary font-medium">{job.candidatesCount}</span>
                </div>
                {job.applicationsCount > 0 && (
                  <div className="text-xs text-lia-text-muted mt-0.5">
                    {job.applicationsCount} novos
                  </div>
                )}
              </td>
              <td className="p-4">
                {getPriorityBadge(job.priority)}
              </td>
              <td className="p-4">
                <div className="flex items-center gap-1 text-lia-text-secondary">
                  <Clock className="h-4 w-4 text-lia-text-muted" />
                  {job.daysOpen || 0} dias
                </div>
              </td>
              <td className="p-4" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-1">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-lia-text-muted hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                          onClick={() => onAction("view_candidates", job)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Ver candidatos</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-lia-text-muted hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                          onClick={() => onAction("edit", job)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Editar</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-lia-text-muted hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                          onClick={() => onAction("duplicate", job)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Duplicar</TooltipContent>
                    </Tooltip>

                    {job.status ==="active" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-lia-text-muted hover:text-wedo-orange"
                            onClick={() => onAction("pause", job)}
                          >
                            <Pause className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Pausar</TooltipContent>
                      </Tooltip>
                    )}

                    {job.status !=="closed" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-lia-text-muted hover:text-status-error"
                            onClick={() => onAction("close", job)}
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Encerrar</TooltipContent>
                      </Tooltip>
                    )}
                  </TooltipProvider>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
