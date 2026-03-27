"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { 
  Users, Eye, Edit, Copy, Pause, XCircle,
  ArrowUpDown, ArrowUp, ArrowDown, MapPin, Building,
  Clock, Calendar, TrendingUp
} from "lucide-react"
import type { JobVacancy, JobSortConfig } from "./types"

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
      return <ArrowUpDown className="h-4 w-4 text-gray-400 dark:text-gray-500" />
    }
    return sortConfig.direction === "asc"
      ? <ArrowUp className="h-4 w-4 text-gray-900 dark:text-gray-50" />
      : <ArrowDown className="h-4 w-4 text-gray-900 dark:text-gray-50" />
  }

  const getStatusBadge = (status: JobVacancy['status']) => {
    const config = {
      draft: { label: "Rascunho", className: "border-yellow-500/30 text-yellow-400" },
      active: { label: "Ativa", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
      paused: { label: "Pausada", className: "border-orange-500/30 text-orange-400" },
      closed: { label: "Encerrada", className: "border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400" },
      cancelled: { label: "Cancelada", className: "border-red-500/30 text-red-400" },
    }
    const { label, className } = config[status] || config.draft
    return <Badge variant="outline" className={className}>{label}</Badge>
  }

  const getPriorityBadge = (priority: JobVacancy['priority']) => {
    const config = {
      low: { label: "Baixa", className: "border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400" },
      medium: { label: "Média", className: "border-blue-500/30 text-blue-400" },
      high: { label: "Alta", className: "border-orange-500/30 text-orange-400" },
      urgent: { label: "Urgente", className: "bg-red-500/20 text-red-400 border-red-500/30" },
    }
    const { label, className } = config[priority] || config.medium
    return <Badge variant="outline" className={`text-xs ${className}`}>{label}</Badge>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500 dark:text-gray-400">Carregando vagas...</div>
      </div>
    )
  }

  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500 dark:text-gray-400">
        <p className="text-lg">Nenhuma vaga encontrada</p>
        <p className="text-sm mt-2">Crie sua primeira vaga clicando no botão acima</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("title")}
                className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Vaga
                {getSortIcon("title")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("status")}
                className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Status
                {getSortIcon("status")}
              </button>
            </th>
            <th className="text-center p-4">
              <button
                onClick={() => onSort("candidates")}
                className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Candidatos
                {getSortIcon("candidates")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("priority")}
                className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Prioridade
                {getSortIcon("priority")}
              </button>
            </th>
            <th className="text-left p-4">
              <button
                onClick={() => onSort("daysOpen")}
                className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Dias Aberta
                {getSortIcon("daysOpen")}
              </button>
            </th>
            <th className="text-right p-4">
              <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
              onClick={() => onJobClick(job)}
            >
              <td className="p-4">
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-50">{job.title}</div>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
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
                {getStatusBadge(job.status)}
              </td>
              <td className="p-4 text-center">
                <div className="flex items-center justify-center gap-1">
                  <Users className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  <span className="text-gray-900 dark:text-gray-200 font-medium">{job.candidatesCount}</span>
                </div>
                {job.applicationsCount > 0 && (
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                    {job.applicationsCount} novos
                  </div>
                )}
              </td>
              <td className="p-4">
                {getPriorityBadge(job.priority)}
              </td>
              <td className="p-4">
                <div className="flex items-center gap-1 text-gray-700 dark:text-gray-300">
                  <Clock className="h-4 w-4 text-gray-400 dark:text-gray-500" />
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
                          className="h-8 w-8 text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-50"
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
                          className="h-8 w-8 text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-50"
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
                          className="h-8 w-8 text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-50"
                          onClick={() => onAction("duplicate", job)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Duplicar</TooltipContent>
                    </Tooltip>

                    {job.status === "active" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-gray-400 dark:text-gray-500 hover:text-orange-400"
                            onClick={() => onAction("pause", job)}
                          >
                            <Pause className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Pausar</TooltipContent>
                      </Tooltip>
                    )}

                    {job.status !== "closed" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-gray-400 dark:text-gray-500 hover:text-red-400"
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
