"use client"

import React from"react"
import { useTranslations, useLocale } from 'next-intl'
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from"@/types/screening"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Button } from"@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import {
  Users, Share2, ChevronRight, Pin, Star, AlertTriangle,
  Brain, GripVertical, ArrowUp, ArrowDown, ArrowUpDown,
  Shield, Building, Lock, MoreVertical
} from"lucide-react"
import { getStatusColor } from"@/components/jobs/jobsPageConstants"
import { liaApi } from"@/services/lia-api"
import { toast } from"sonner"
import type { Job } from"@/components/jobs"

interface JobsCompactTableViewProps {
  isLoading: boolean
  filteredJobs: Job[]
  statusOrder: readonly string[] | string[]
  groupedJobs: Record<string, Job[]>
  jobsColumnOrder: string[]
  visibleColumnIds: string[]
  hookToTableColumnMap: Record<string, string>
  jobsColumnWidths: Record<string, number>
  selectedJobsForBatch: Set<number>
  pinnedJobs: Set<number>
  urgentJobs: Set<number>
  favoriteJobs: Set<number>
  draggedJobColumnId: string | null
  dragOverJobColumnId: string | null
  jobsSortColumn: string | null
  jobsSortDirection: 'asc' | 'desc'
  onSelectAll: () => void
  onDeselectAll: () => void
  onToggleJobSelection: (id: number) => void
  onJobPreview: (job: Job) => void
  onJobClick: (job: Job) => void
  onToggleUrgent: (id: number) => void
  onTogglePin: (id: number) => void
  onToggleFavorite: (id: number) => void
  onSort: (column: string) => void
  onColumnDragStart: (id: string, e: React.DragEvent) => void
  onColumnDragOver: (id: string, e: React.DragEvent) => void
  onColumnDragLeave: () => void
  onColumnDrop: (id: string, e: React.DragEvent) => void
  onColumnDragEnd: () => void
  onColumnResize: (column: string, e: React.MouseEvent) => void
}

const columnSortAlign: Record<string, { sortable: boolean; align: 'left' | 'center' | 'right'; labelKey: string }> = {
  checkbox: { sortable: false, align: 'center', labelKey: '' },
  id: { sortable: true, align: 'left', labelKey: 'id' },
  vaga: { sortable: true, align: 'left', labelKey: 'job' },
  candidatos: { sortable: true, align: 'center', labelKey: 'candidates' },
  performance: { sortable: false, align: 'left', labelKey: 'performance' },
  status: { sortable: true, align: 'left', labelKey: 'status' },
  screeningStatus: { sortable: true, align: 'center', labelKey: 'screening' },
  recrutador: { sortable: true, align: 'left', labelKey: 'recruiter' },
  gestor: { sortable: true, align: 'left', labelKey: 'manager' },
  prazoTriagem: { sortable: true, align: 'center', labelKey: 'screeningDeadline' },
  prazoShortlist: { sortable: true, align: 'center', labelKey: 'shortlistDeadline' },
  prazoEncerramento: { sortable: true, align: 'center', labelKey: 'closingDeadline' },
  acoes: { sortable: false, align: 'center', labelKey: 'actions' }
}

export function JobsCompactTableView(props: JobsCompactTableViewProps) {
  const t = useTranslations('jobs')
  const tc = useTranslations('jobs.tableColumns')
  const ta = useTranslations('jobs.tableActions')
  const tf = useTranslations('jobs.tableFunnel')
  const locale = useLocale()
  const columnLabels: Record<string, string> = {
    id: tc('id'),
    vaga: tc('job'),
    candidatos: tc('candidates'),
    performance: tc('performance'),
    status: tc('status'),
    screeningStatus: tc('screening'),
    recrutador: tc('recruiter'),
    gestor: tc('manager'),
    prazoTriagem: tc('screeningDeadline'),
    prazoShortlist: tc('shortlistDeadline'),
    prazoEncerramento: tc('closingDeadline'),
    acoes: tc('actions'),
  }
  const statusLabels: Record<string, string> = {
    'Ativa': t('statuses.Ativa'),
    'Aprovada': t('statuses.Aprovada'),
    'Aguardando aprovação': t('statuses.Aguardando aprovação'),
    'Reaberta': t('statuses.Reaberta'),
    'Paralisada': t('statuses.Paralisada'),
    'Interna': t('statuses.Interna'),
    'Rascunho': t('statuses.Rascunho'),
    'Fechada (preenchida)': t('statuses.Fechada (preenchida)'),
    'Fechada (expirada)': t('statuses.Fechada (expirada)'),
    'Cancelada': t('statuses.Cancelada'),
    'Concluída': t('statuses.Concluída'),
    'Arquivada': t('statuses.Arquivada'),
  }
  const {
    isLoading,
    filteredJobs,
    statusOrder,
    groupedJobs,
    jobsColumnOrder,
    visibleColumnIds,
    hookToTableColumnMap,
    jobsColumnWidths,
    selectedJobsForBatch,
    pinnedJobs,
    urgentJobs,
    favoriteJobs,
    draggedJobColumnId,
    dragOverJobColumnId,
    jobsSortColumn,
    jobsSortDirection,
    onSelectAll,
    onDeselectAll,
    onToggleJobSelection,
    onJobPreview,
    onJobClick,
    onToggleUrgent,
    onTogglePin,
    onToggleFavorite,
    onSort,
    onColumnDragStart,
    onColumnDragOver,
    onColumnDragLeave,
    onColumnDrop,
    onColumnDragEnd,
    onColumnResize,
  } = props

  if (isLoading) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full table-fixed">
          <thead>
            <tr >
              <th className="py-3 px-3 text-center w-12">
                <div className="w-4 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
              </th>
              <th className="py-3 px-3 text-left w-[80px]">
                <div className="w-8 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-left w-[200px]">
                <div className="w-16 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-center w-[100px]">
                <div className="w-20 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
              </th>
              <th className="py-3 px-3 text-left w-[180px]">
                <div className="w-32 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-left w-[100px]">
                <div className="w-14 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-left w-[60px]">
                <div className="w-10 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-left w-[120px]">
                <div className="w-20 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-left w-[100px]">
                <div className="w-14 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none" />
              </th>
              <th className="py-3 px-3 text-center w-[100px]">
                <div className="w-16 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
              </th>
              <th className="py-3 px-3 text-center w-[80px]">
                <div className="w-12 h-4 bg-lia-interactive-active rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
              </th>
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((row) => (
              <tr key={row} >
                <td className="py-3 px-3 text-center">
                  <div className="w-4 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
                </td>
                <td className="py-3 px-3">
                  <div className="w-16 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                </td>
                <td className="py-3 px-3">
                  <div className="space-y-1">
                    <div className="w-40 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                    <div className="w-24 h-3 bg-lia-bg-secondary rounded-xl animate-pulse motion-reduce:animate-none" />
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-8 h-6 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
                </td>
                <td className="py-3 px-3">
                  <div className="flex gap-1">
                    <div className="w-6 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                    <div className="w-6 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                    <div className="w-6 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                    <div className="w-6 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                    <div className="w-6 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="w-16 h-5 bg-lia-bg-tertiary rounded-full animate-pulse motion-reduce:animate-none" />
                </td>
                <td className="py-3 px-3">
                  <div className="w-8 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-lia-bg-tertiary rounded-full animate-pulse motion-reduce:animate-none" />
                    <div className="w-20 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="w-20 h-4 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none" />
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-16 h-5 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-6 h-6 bg-lia-bg-tertiary rounded-xl animate-pulse motion-reduce:animate-none mx-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center justify-center py-6 text-sm text-lia-text-primary">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full animate-spin motion-reduce:animate-none bg-lia-border-medium" />
            <span>{t('loadingJobs')}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
    <div className="overflow-auto max-h-full min-h-content-lg border border-lia-border-subtle rounded-xl">
      <table className="w-full table-fixed">
        <thead className="sticky top-0 z-10 bg-lia-bg-primary">
          <tr >
            {jobsColumnOrder.filter((columnId) => {
              if (columnId === 'checkbox' || columnId === 'acoes') return true
              const hookId = Object.entries(hookToTableColumnMap).find(([_, tableId]) => tableId === columnId)?.[0]
              if (!hookId) return true
              return visibleColumnIds.includes(hookId)
            }).map((columnId) => {
              const colMeta = columnSortAlign[columnId]
              if (!colMeta) return null
              const config = { label: columnLabels[columnId] || '', sortable: colMeta.sortable, align: colMeta.align }

              if (columnId === 'checkbox') {
                return (
                  <th key={columnId} className="py-3 px-3 text-center w-12">
                    <input
                      data-testid="jobs-select-all"
                      type="checkbox"
                      checked={selectedJobsForBatch.size === filteredJobs.length && filteredJobs.length > 0}
                      ref={(input) => {
                        if (input) {
                          input.indeterminate = selectedJobsForBatch.size > 0 && selectedJobsForBatch.size < filteredJobs.length
                        }
                      }}
                      onChange={(e) => {
                        if (e.target.checked) {
                          onSelectAll()
                        } else {
                          onDeselectAll()
                        }
                      }}
                      className="w-4 h-4 rounded-md"
                    />
                  </th>
                )
              }

              if (columnId === 'acoes') {
                return (
                  <th 
                    key={columnId} 
                    className="text-center py-3 px-3 text-xs font-semibold text-lia-text-primary"
                    style={{width: jobsColumnWidths.acoes}} /* dynamic */
                  >
                    <span className="sr-only">{tc('actionsScreenReader')}</span>
                    <MoreVertical className="w-4 h-4 text-lia-text-primary mx-auto" aria-hidden="true" />
                  </th>
                )
              }

              const width = jobsColumnWidths[columnId as keyof typeof jobsColumnWidths] || 100
              const isDragging = draggedJobColumnId === columnId
              const isDragOver = dragOverJobColumnId === columnId

              return (
                <th
                  key={columnId}
                  className={`
                    text-${config.align} py-3 px-3 text-xs font-semibold text-lia-text-primary 
                    relative group select-none
                    ${isDragging ? 'opacity-50' : ''}
                    ${isDragOver ? 'bg-wedo-cyan/10 dark:bg-wedo-cyan/20' : ''}
                    ${config.sortable ? 'cursor-pointer hover:bg-lia-interactive-hover' : ''}
                  `}
                  style={{width: `${width}px`, minWidth: '50px'}} /* dynamic */
                  draggable={columnId !== 'checkbox' && columnId !== 'acoes'}
                  onDragStart={(e) => onColumnDragStart(columnId, e)}
                  onDragOver={(e) => onColumnDragOver(columnId, e)}
                  onDragLeave={onColumnDragLeave}
                  onDrop={(e) => onColumnDrop(columnId, e)}
                  onDragEnd={onColumnDragEnd}
                  onClick={() => config.sortable && onSort(columnId)}
                >
                  <div className="flex items-center gap-1">
                    <GripVertical className="w-3 h-3 text-lia-text-primary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none cursor-grab" />
                    <span>{config.label}</span>
                    {config.sortable && (
                      jobsSortColumn === columnId 
                        ? (jobsSortDirection === 'asc' 
                            ? <ArrowUp className="w-3 h-3 text-lia-text-primary" />
                            : <ArrowDown className="w-3 h-3 text-lia-text-primary" />)
                        : <ArrowUpDown className="w-3 h-3 text-lia-text-primary" />
                    )}
                  </div>
                  
                  <div
                    className="absolute right-0 top-0 h-full w-1 cursor-col-resize opacity-0 group-hover:opacity-100 bg-lia-border-default hover:bg-lia-border-medium transition-colors motion-reduce:transition-none"
                    onMouseDown={(e) => onColumnResize(columnId, e)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {statusOrder.map((status) => {
            const statusJobs = groupedJobs[status]

            if (!statusJobs || statusJobs.length === 0) return null

            return (
              <React.Fragment key={status}>
                {statusJobs.map((job) => (
                  <React.Fragment key={job.id}>
                    <tr
                      data-testid={`job-row-${job.id}`}
                      className="hover:bg-lia-interactive-hover text-xs cursor-pointer transition-colors motion-reduce:transition-none"
                      onClick={() => onJobPreview(job)}
                    >
                      {jobsColumnOrder.filter((columnId) => {
                        if (columnId === 'checkbox' || columnId === 'acoes') return true
                        const hookId = Object.entries(hookToTableColumnMap).find(([_, tableId]) => tableId === columnId)?.[0]
                        if (!hookId) return true
                        return visibleColumnIds.includes(hookId)
                      }).map((columnId) => {
                        const width = jobsColumnWidths[columnId as keyof typeof jobsColumnWidths] || 100
                        
                        if (columnId === 'checkbox') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center">
                              <input
                                type="checkbox"
                                checked={selectedJobsForBatch.has(job.id)}
                                onChange={(e) => {
                                  e.stopPropagation()
                                  onToggleJobSelection(job.id)
                                }}
                                onClick={(e) => e.stopPropagation()}
                                className="w-4 h-4 rounded-md"
                              />
                            </td>
                          )
                        }

                        if (columnId === 'id') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <span className="text-xs font-normal text-lia-text-primary">
                                V{job.id.toString().padStart(4, '0')}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'vaga') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div>
                                <div className="font-semibold text-xs text-lia-text-primary flex items-center gap-1">
                                  {pinnedJobs.has(job.id) && (
                                    <Pin className="w-3 h-3 text-lia-text-primary fill-current" />
                                  )}
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      onJobClick(job)
                                    }}
                                    className="text-left hover:underline hover:text-wedo-cyan dark:hover:text-wedo-cyan cursor-pointer transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan focus-visible:ring-offset-1 rounded-sm"
                                    title={ta('openJob', { title: job.title })}
                                  >
                                    {job.title}
                                  </button>
                                  {(job.visibility === 'confidential' || job.isConfidential) && (
                                    <span title={ta('confidentialJob')} className="flex items-center">
                                      <Shield className="w-3.5 h-3.5 text-wedo-orange" />
                                    </span>
                                  )}
                                  {job.visibility === 'internal' && (
                                    <span title={ta('internalJob')} className="flex items-center">
                                      <Building className="w-3.5 h-3.5 text-lia-text-secondary" />
                                    </span>
                                  )}
                                  {job.visibility === 'hidden' && (
                                    <span title={ta('hiddenJob')} className="flex items-center">
                                      <Lock className="w-3.5 h-3.5 text-lia-text-secondary" />
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'candidatos') {
                          return (
                            <td key={columnId} className="py-2 px-2" style={{width: `${width}px`}} /* dynamic */>
                              <TooltipProvider delayDuration={200}>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <div className="flex items-center justify-center cursor-help">
                                      <div className="flex items-center gap-1">
                                        <Users 
                                          className="w-3.5 h-3.5"
                                          style={{color: job.funnel.total >= 50
                                              ? 'var(--lia-text-secondary)'
                                              : job.funnel.total >= 20
                                              ? 'var(--status-error)'
                                              : 'var(--status-warning)'}} /* dynamic */
                                        />
                                        <span className="text-sm font-normal text-lia-text-primary">
                                          {job.funnel.total}
                                        </span>
                                      </div>
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="min-w-[180px] p-0">
                                    <div className="px-3 py-2 text-xs">
                                      <div className="font-semibold mb-2">{tf('candidateFunnel')}</div>
                                      <div className="space-y-1.5 mb-2">
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-lia-text-primary/60">{tf('total')}</span>
                                          <span className="font-semibold">{job.funnel.total}</span>
                                        </div>
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-lia-text-primary/60">{tf('screening')}</span>
                                          <span className="font-semibold">
                                            {job.funnel.screening} ({job.funnel.total > 0 ? Math.round((job.funnel.screening / job.funnel.total) * 100) : 0}%)
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-lia-text-primary/60">{tf('interviews')}</span>
                                          <span className="font-semibold">
                                            {job.funnel.interview} ({job.funnel.total > 0 ? Math.round((job.funnel.interview / job.funnel.total) * 100) : 0}%)
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-lia-text-primary/60">{tf('finalists')}</span>
                                          <span className="font-semibold">
                                            {job.funnel.final} ({job.funnel.total > 0 ? Math.round((job.funnel.final / job.funnel.total) * 100) : 0}%)
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-4 pt-1 border-t border-lia-border-default">
                                          <span className="text-lia-text-primary/60">{tf('hired')}</span>
                                          <span className="font-bold">
                                            {job.funnel.hired} ({job.funnel.total > 0 ? Math.round((job.funnel.hired / job.funnel.total) * 100) : 0}%)
                                          </span>
                                        </div>
                                      </div>
                                      <div className="pt-1.5 border-t border-lia-border-default">
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-lia-text-primary/60">{tf('conversionRate')}</span>
                                          <span className={`${
                                            job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 10 ? 'font-bold' :
                                            job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 5 ? 'font-semibold' :
                                            'font-medium text-lia-text-primary/60'
                                          }`}>
                                            {job.funnel.total > 0 ? ((job.funnel.hired / job.funnel.total) * 100).toFixed(1) : 0}%
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </td>
                          )
                        }

                        if (columnId === 'performance') {
                          const liaTriages = job.liaMetrics ? {
                            pipeline: job.liaMetrics.pipeline_lia,
                            agendadas: job.liaMetrics.triagens_agendadas,
                            realizadas: job.liaMetrics.triagens_realizadas,
                            semResposta: job.liaMetrics.sem_resposta,
                            entrevistasAgendadas: job.liaMetrics.entrevistas_agendadas
                          } : {
                            pipeline: 0,
                            agendadas: 0,
                            realizadas: 0,
                            semResposta: 0,
                            entrevistasAgendadas: 0
                          }
                          
                          const allValues = [liaTriages.pipeline, liaTriages.agendadas, liaTriages.realizadas, liaTriages.entrevistasAgendadas]
                          const maxValue = Math.max(...allValues, 1)
                          const getCardWidth = (value: number) => {
                            const minWidth = 24
                            const maxWidth = 40
                            const ratio = value / maxValue
                            return Math.round(minWidth + (maxWidth - minWidth) * ratio)
                          }
                          
                          return (
                            <td key={columnId} className="py-2 px-2" style={{width: `${width}px`}} /* dynamic */>
                              <div className="space-y-1">
                                <div className="flex items-center gap-0.5">
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-xl flex items-center justify-center transition-[color,background-color,border-color,transform] hover:ring-2 hover:scale-105 bg-lia-interactive-active" 
                                      style={{width: `${getCardWidth(liaTriages.pipeline)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-lia-text-primary">
                                        {liaTriages.pipeline}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-lia-bg-inverse text-lia-text-on-inverse px-3 py-2 rounded-xl whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1 flex items-center gap-1">
                                          <Brain className="w-3 h-3 text-wedo-cyan" />
                                          {tf('pipelineLIA')}
                                        </div>
                                        <div className="text-xs text-lia-text-on-inverse/80">{tf('candidatesContacted', { count: liaTriages.pipeline })}</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-lia-bg-inverse"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-lia-text-primary flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-xl flex items-center justify-center transition-[color,background-color,border-color,transform] hover:ring-2 hover:scale-105 bg-lia-border-default" 
                                      style={{width: `${getCardWidth(liaTriages.agendadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-lia-text-primary">
                                        {liaTriages.agendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-lia-bg-inverse text-lia-text-on-inverse px-3 py-2 rounded-xl whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">{tf('screeningsScheduled')}</div>
                                        <div className="text-xs text-lia-text-on-inverse/80">{tf('screeningsScheduledDesc', { count: liaTriages.agendadas })}</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-lia-bg-inverse"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-lia-text-primary flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-xl flex items-center justify-center transition-[color,background-color,border-color,transform] hover:ring-2 hover:scale-105 bg-wedo-green-pastel" 
                                      style={{width: `${getCardWidth(liaTriages.realizadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-lia-text-primary">
                                        {liaTriages.realizadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-lia-bg-inverse text-lia-text-on-inverse px-3 py-2 rounded-xl whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">{tf('screeningsCompleted')}</div>
                                        <div className="text-xs text-lia-text-on-inverse/80">{tf('screeningsCompletedDesc', { count: liaTriages.realizadas })}</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-lia-bg-inverse"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-lia-text-primary flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-xl flex items-center justify-center transition-[color,background-color,border-color,transform] hover:ring-2 hover:scale-105 bg-lia-interactive-active" 
                                      style={{width: `${getCardWidth(liaTriages.entrevistasAgendadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-lia-text-primary">
                                        {liaTriages.entrevistasAgendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-lia-bg-inverse text-lia-text-on-inverse px-3 py-2 rounded-xl whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">{tf('interviewsScheduled')}</div>
                                        <div className="text-xs text-lia-text-on-inverse/80">{tf('interviewsScheduledDesc', { count: liaTriages.entrevistasAgendadas })}</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-lia-bg-inverse"></div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'status') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="space-y-1">
                                <Chip
                                  variant="neutral"
                                  className={`border-0 text-xs font-normal px-2 py-0.5 ${job.status === 'Concluída' ? 'text-wedo-purple' : 'text-lia-text-primary'}`}
                                  style={{backgroundColor: getStatusColor(job.status)}} /* dynamic */
                                >
                                  {statusLabels[job.status] || job.status}
                                </Chip>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'screeningStatus') {
                          const status = job.screeningStatus || 'not_configured'
                          const statusLabels = SCREENING_STATUS_LABELS
                          const screeningColors: Record<string, string> = {
                            not_configured: 'var(--lia-border-subtle)',
                            not_started: 'var(--lia-bg-tertiary)',
                            active: 'var(--status-success)',
                            paused: 'var(--lia-border-default)',
                            completed: 'var(--lia-border-medium)',
                          }
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <Chip
                                variant="neutral"
                                className="border-0 text-micro font-normal px-2 py-0.5 text-lia-text-primary cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none"
                                style={{backgroundColor: screeningColors[status] || 'var(--lia-border-subtle)'}} /* dynamic */
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onJobPreview(job)
                                }}
                              >
                                {statusLabels[status] || ta('notConfigured')}
                              </Chip>
                            </td>
                          )
                        }

                        if (columnId === 'recrutador') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="flex items-center gap-2">
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={undefined} />
                                  <AvatarFallback className="text-xs bg-lia-interactive-active text-lia-text-primary">
                                    {job.recruiter.split(' ').map(n => n[0]).join('')}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="text-xs font-normal text-lia-text-primary">
                                  {job.recruiter}
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'gestor') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="text-xs font-normal text-lia-text-primary">
                                {job.manager}
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'prazoTriagem') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{width: `${width}px`}} /* dynamic */>
                              <span className="text-xs font-normal text-lia-text-primary">
                                {job.openDate 
                                  ? new Date(job.openDate).toLocaleDateString(locale, { day: '2-digit', month: '2-digit' })
                                  : '—'}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'prazoShortlist' || columnId === 'prazoEncerramento') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{width: `${width}px`}} /* dynamic */>
                              <span className="text-xs font-normal text-lia-text-primary">
                                {job.deadline 
                                  ? new Date(job.deadline).toLocaleDateString(locale, { day: '2-digit', month: '2-digit' })
                                  : '—'}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'acoes') {
                          const isUrgent = urgentJobs.has(job.id) || job.urgencyLevel >= 4
                          const isPinned = pinnedJobs.has(job.id)
                          const isFavorite = favoriteJobs.has(job.id)
                          
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="flex items-center gap-1">
                                <Button
                                  data-testid={`job-toggle-urgent-${job.id}`}
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors motion-reduce:transition-none ${
                                    isUrgent 
                                      ? 'bg-status-error/10 hover:bg-status-error/15 dark:bg-status-error/20 dark:hover:bg-status-error/30' 
                                      : 'hover:bg-lia-interactive-hover'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onToggleUrgent(job.id)
                                  }}
                                  title={isUrgent ? ta('removeUrgency') : ta('markUrgent')}
                                >
                                  <AlertTriangle className={`w-3.5 h-3.5 transition-colors motion-reduce:transition-none ${
                                    isUrgent 
                                      ? 'text-status-error fill-red-100' 
                                      : 'text-lia-text-primary'
                                  }`} />
                                </Button>
                                <Button
                                  data-testid={`job-toggle-pin-${job.id}`}
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors motion-reduce:transition-none ${
                                    isPinned 
                                      ? 'bg-lia-bg-tertiary hover:bg-lia-interactive-active' 
                                      : 'hover:bg-lia-interactive-hover'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onTogglePin(job.id)
                                  }}
                                  title={isPinned ? ta('unpinJob') : ta('pinJob')}
                                >
                                  <Pin className={`w-3 h-3 transition-colors motion-reduce:transition-none ${
                                    isPinned 
                                      ? 'text-lia-text-primary fill-current' 
                                      : 'text-lia-text-primary'
                                  }`} />
                                </Button>
                                <Button
                                  data-testid={`job-toggle-favorite-${job.id}`}
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors motion-reduce:transition-none ${
                                    isFavorite 
                                      ? 'bg-status-warning/10 hover:bg-status-warning/15 dark:bg-status-warning/20 dark:hover:bg-status-warning/30' 
                                      : 'hover:bg-lia-interactive-hover'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onToggleFavorite(job.id)
                                  }}
                                  title={isFavorite ? ta('removeFavorite') : ta('addFavorite')}
                                >
                                  <Star className={`w-3 h-3 transition-colors motion-reduce:transition-none ${
                                    isFavorite 
                                      ? 'text-status-warning fill-yellow-400' 
                                      : 'text-lia-text-primary'
                                  }`} />
                                </Button>
                                <Button
                                  data-testid={`job-share-link-${job.id}`}
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-lia-interactive-hover"
                                  onClick={async (e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    try {
                                      const result = await liaApi.generatePublicLink(job.backendId)
                                      if (result.success) {
                                        const fullUrl = `${window.location.origin}${result.public_url}`
                                        await navigator.clipboard.writeText(fullUrl)
                                        toast.success(ta('linkCopied'), {
                                          description: ta('linkCopiedDesc')
                                        })
                                      }
                                    } catch (error) {
                                      toast.error(ta('linkError'), {
                                        description: ta('linkErrorDesc')
                                      })
                                    }
                                  }}
                                  title={ta('shareJob')}
                                >
                                  <Share2 className="w-3.5 h-3.5 text-lia-text-primary" />
                                </Button>
                                <Button
                                  data-testid={`job-open-kanban-${job.id}`}
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-lia-interactive-hover"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    onJobClick(job)
                                  }}
                                  title={ta('openKanban')}
                                >
                                  <ChevronRight className="w-4 h-4 text-lia-text-primary" />
                                </Button>
                              </div>
                            </td>
                          )
                        }

                        return null
                      })}
                    </tr>
                  </React.Fragment>
                ))}
              </React.Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
    </>
  )
}
