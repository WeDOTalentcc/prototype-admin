"use client"

import React from "react"
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  Users, Share2, ChevronRight, Pin, Star, AlertTriangle,
  Brain, GripVertical, ArrowUp, ArrowDown, ArrowUpDown,
  Shield, Building, Lock, MoreVertical
} from "lucide-react"
import { getStatusColor } from "@/components/jobs/jobsPageConstants"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import type { Job } from "@/components/jobs"

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

const jobsColumnConfig: Record<string, { label: string; sortable: boolean; align: 'left' | 'center' | 'right' }> = {
  checkbox: { label: '', sortable: false, align: 'center' },
  id: { label: 'ID', sortable: true, align: 'left' },
  vaga: { label: 'Vaga', sortable: true, align: 'left' },
  candidatos: { label: 'Candidatos', sortable: true, align: 'center' },
  performance: { label: 'Performance LIA Triagens', sortable: false, align: 'left' },
  status: { label: 'Status', sortable: true, align: 'left' },
  screeningStatus: { label: 'Triagem', sortable: true, align: 'center' },
  recrutador: { label: 'Recrutador(a)', sortable: true, align: 'left' },
  gestor: { label: 'Gestor', sortable: true, align: 'left' },
  prazoTriagem: { label: 'Prazo Triagem', sortable: true, align: 'center' },
  prazoShortlist: { label: 'Prazo Short List', sortable: true, align: 'center' },
  prazoEncerramento: { label: 'Prazo Encerramento', sortable: true, align: 'center' },
  acoes: { label: 'Ações', sortable: false, align: 'center' }
}

export function JobsCompactTableView(props: JobsCompactTableViewProps) {
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
            <tr className="">
              <th className="py-3 px-3 text-center w-12">
                <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse mx-auto" />
              </th>
              <th className="py-3 px-3 text-left w-[80px]">
                <div className="w-8 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-left w-[200px]">
                <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-center w-[100px]">
                <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse mx-auto" />
              </th>
              <th className="py-3 px-3 text-left w-[180px]">
                <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-left w-[100px]">
                <div className="w-14 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-left w-[60px]">
                <div className="w-10 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-left w-[120px]">
                <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-left w-[100px]">
                <div className="w-14 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" />
              </th>
              <th className="py-3 px-3 text-center w-[100px]">
                <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse mx-auto" />
              </th>
              <th className="py-3 px-3 text-center w-[80px]">
                <div className="w-12 h-4 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse mx-auto" />
              </th>
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((row) => (
              <tr key={row} className="">
                <td className="py-3 px-3 text-center">
                  <div className="w-4 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse mx-auto" />
                </td>
                <td className="py-3 px-3">
                  <div className="w-16 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                </td>
                <td className="py-3 px-3">
                  <div className="space-y-1">
                    <div className="w-40 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                    <div className="w-24 h-3 bg-gray-50 dark:bg-gray-800/50 rounded-md animate-pulse" />
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-8 h-6 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse mx-auto" />
                </td>
                <td className="py-3 px-3">
                  <div className="flex gap-1">
                    <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                    <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                    <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                    <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                    <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="w-16 h-5 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse" />
                </td>
                <td className="py-3 px-3">
                  <div className="w-8 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse" />
                    <div className="w-20 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="w-20 h-4 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse" />
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-16 h-5 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse mx-auto" />
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-md animate-pulse mx-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center justify-center py-6 text-sm text-gray-800 dark:text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full animate-spin bg-gray-600" />
            <span>Carregando vagas...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="overflow-auto h-full">
      <table className="w-full table-fixed">
        <thead className="sticky top-0 z-10 bg-white dark:bg-gray-900">
          <tr className="">
            {jobsColumnOrder.filter((columnId) => {
              if (columnId === 'checkbox' || columnId === 'acoes') return true
              const hookId = Object.entries(hookToTableColumnMap).find(([_, tableId]) => tableId === columnId)?.[0]
              if (!hookId) return true
              return visibleColumnIds.includes(hookId)
            }).map((columnId) => {
              const config = jobsColumnConfig[columnId]
              if (!config) return null

              if (columnId === 'checkbox') {
                return (
                  <th key={columnId} className="py-3 px-3 text-center w-12">
                    <input
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
                    className="text-center py-3 px-3 text-xs font-semibold text-gray-950 dark:text-gray-200"
                    style={{width: jobsColumnWidths.acoes}} /* dynamic */
                  >
                    <span className="sr-only">Ações</span>
                    <MoreVertical className="w-4 h-4 text-gray-800 dark:text-gray-200 mx-auto" aria-hidden="true" />
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
                    text-${config.align} py-3 px-3 text-xs font-semibold text-gray-950 dark:text-gray-200 
                    relative group select-none
                    ${isDragging ? 'opacity-50' : ''}
                    ${isDragOver ? 'bg-wedo-cyan/10 dark:bg-wedo-cyan/20' : ''}
                    ${config.sortable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50' : ''}
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
                    <GripVertical className="w-3 h-3 text-gray-800 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab" />
                    <span>{config.label}</span>
                    {config.sortable && (
                      jobsSortColumn === columnId 
                        ? (jobsSortDirection === 'asc' 
                            ? <ArrowUp className="w-3 h-3 text-gray-800" />
                            : <ArrowDown className="w-3 h-3 text-gray-800" />)
                        : <ArrowUpDown className="w-3 h-3 text-gray-800" />
                    )}
                  </div>
                  
                  <div
                    className="absolute right-0 top-0 h-full w-1 cursor-col-resize opacity-0 group-hover:opacity-100 bg-gray-300 dark:bg-gray-600 hover:bg-gray-500 dark:hover:bg-gray-500 transition-colors"
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
                      className="hover:bg-gray-50 dark:hover:bg-gray-800/50 text-xs cursor-pointer transition-colors"
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
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-200">
                                V{job.id.toString().padStart(4, '0')}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'vaga') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div>
                                <div className="font-semibold text-xs text-gray-950 dark:text-gray-50 flex items-center gap-1">
                                  {pinnedJobs.has(job.id) && (
                                    <Pin className="w-3 h-3 text-gray-800 dark:text-gray-200 fill-current" />
                                  )}
                                  {job.title}
                                  {(job.visibility === 'confidential' || job.isConfidential) && (
                                    <span title="Vaga Confidencial" className="flex items-center">
                                      <Shield className="w-3.5 h-3.5 text-wedo-orange" />
                                    </span>
                                  )}
                                  {job.visibility === 'internal' && (
                                    <span title="Vaga Interna" className="flex items-center">
                                      <Building className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                                    </span>
                                  )}
                                  {job.visibility === 'hidden' && (
                                    <span title="Vaga Oculta" className="flex items-center">
                                      <Lock className="w-3.5 h-3.5 text-gray-600" />
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
                              <div className="flex items-center justify-center group relative cursor-help">
                                <div className="flex items-center gap-1">
                                  <Users 
                                    className="w-3.5 h-3.5"
                                    style={{color: job.funnel.total >= 50
                                        ? 'var(--gray-600)'
                                        : job.funnel.total >= 20
                                        ? 'var(--status-error)'
                                        : 'var(--status-warning)'}} /* dynamic */
                                  />
                                  <span className="text-sm font-normal text-gray-800 dark:text-gray-50">
                                    {job.funnel.total}
                                  </span>
                                </div>
                                <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                  <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md text-xs min-w-sidebar-content">
                                    <div className="font-semibold mb-2">Funil de Candidatos</div>
                                    <div className="space-y-1.5 mb-2">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Total</span>
                                        <span className="text-xs font-semibold text-white">{job.funnel.total}</span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Triagem</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.screening} ({job.funnel.total > 0 ? Math.round((job.funnel.screening / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Entrevistas</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.interview} ({job.funnel.total > 0 ? Math.round((job.funnel.interview / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Finalistas</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.final} ({job.funnel.total > 0 ? Math.round((job.funnel.final / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between pt-1">
                                        <span className="text-xs text-gray-300">✓ Contratados</span>
                                        <span className="text-xs font-bold text-white">
                                          {job.funnel.hired} ({job.funnel.total > 0 ? Math.round((job.funnel.hired / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                    </div>
                                    <div className="pt-2">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Taxa conversão final</span>
                                        <span className={`text-xs ${
                                          job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 10 ? 'font-bold text-white' :
                                          job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 5 ? 'font-semibold text-gray-200' :
                                          'font-medium text-gray-300'
                                        }`}>
                                          {job.funnel.total > 0 ? ((job.funnel.hired / job.funnel.total) * 100).toFixed(1) : 0}%
                                        </span>
                                      </div>
                                    </div>
                                    <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                  </div>
                                </div>
                              </div>
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
                                      className="h-6 rounded-md flex items-center justify-center transition-all hover:ring-2 hover:scale-105 bg-gray-200" 
                                      style={{width: `${getCardWidth(liaTriages.pipeline)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.pipeline}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1 flex items-center gap-1">
                                          <Brain className="w-3 h-3 text-wedo-cyan" />
                                          Pipeline LIA
                                        </div>
                                        <div className="text-xs text-gray-500">{liaTriages.pipeline} candidatos contatados</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-md flex items-center justify-center transition-all hover:ring-2 hover:scale-105 bg-gray-300" 
                                      style={{width: `${getCardWidth(liaTriages.agendadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.agendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Triagens Agendadas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.agendadas} triagens marcadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-md flex items-center justify-center transition-all hover:ring-2 hover:scale-105 bg-wedo-green-pastel" 
                                      style={{width: `${getCardWidth(liaTriages.realizadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.realizadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Triagens Completas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.realizadas} triagens finalizadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded-md flex items-center justify-center transition-all hover:ring-2 hover:scale-105 bg-gray-200" 
                                      style={{width: `${getCardWidth(liaTriages.entrevistasAgendadas)}px`,
                                        minWidth: '24px'}} /* dynamic */>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.entrevistasAgendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Entrevistas Agendadas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.entrevistasAgendadas} entrevistas marcadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
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
                                <Badge
                                  variant="outline"
                                  className="border-0 text-xs font-normal px-2 py-0.5 text-gray-950 dark:text-gray-50"
                                  style={{backgroundColor: getStatusColor(job.status)}} /* dynamic */
                                >
                                  {job.status}
                                </Badge>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'screeningStatus') {
                          const status = job.screeningStatus || 'not_configured'
                          const statusLabels = SCREENING_STATUS_LABELS
                          const screeningColors: Record<string, string> = {
                            not_configured: 'var(--gray-200)',
                            not_started: 'var(--gray-100)',
                            active: 'var(--status-success)',
                            paused: 'var(--gray-300)',
                            completed: 'var(--gray-400)',
                          }
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <Badge
                                variant="outline"
                                className="border-0 text-micro font-normal px-2 py-0.5 text-gray-950 dark:text-gray-50 cursor-pointer hover:opacity-80 transition-opacity"
                                style={{backgroundColor: screeningColors[status] || 'var(--gray-200)'}} /* dynamic */
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onJobPreview(job)
                                }}
                              >
                                {statusLabels[status] || 'Não Configurada'}
                              </Badge>
                            </td>
                          )
                        }

                        if (columnId === 'recrutador') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="flex items-center gap-2">
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={`https://i.pravatar.cc/100?u=${job.recruiterEmail}`} />
                                  <AvatarFallback className="text-xs bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                                    {job.recruiter.split(' ').map(n => n[0]).join('')}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                  {job.recruiter}
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'gestor') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{width: `${width}px`}} /* dynamic */>
                              <div className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.manager}
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'prazoTriagem') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{width: `${width}px`}} /* dynamic */>
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.openDate 
                                  ? new Date(job.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
                                  : '—'}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'prazoShortlist' || columnId === 'prazoEncerramento') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{width: `${width}px`}} /* dynamic */>
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.deadline 
                                  ? new Date(job.deadline).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
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
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isUrgent 
                                      ? 'bg-status-error/10 hover:bg-status-error/15 dark:bg-status-error/20 dark:hover:bg-status-error/30' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onToggleUrgent(job.id)
                                  }}
                                  title={isUrgent ? "Remover urgência" : "Marcar como urgente"}
                                >
                                  <AlertTriangle className={`w-3.5 h-3.5 transition-colors ${
                                    isUrgent 
                                      ? 'text-status-error fill-red-100' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isPinned 
                                      ? 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onTogglePin(job.id)
                                  }}
                                  title={isPinned ? "Desafixar vaga" : "Fixar vaga"}
                                >
                                  <Pin className={`w-3 h-3 transition-colors ${
                                    isPinned 
                                      ? 'text-gray-950 dark:text-gray-50 fill-current' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isFavorite 
                                      ? 'bg-status-warning/10 hover:bg-status-warning/15 dark:bg-status-warning/20 dark:hover:bg-status-warning/30' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onToggleFavorite(job.id)
                                  }}
                                  title={isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
                                >
                                  <Star className={`w-3 h-3 transition-colors ${
                                    isFavorite 
                                      ? 'text-status-warning fill-yellow-400' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-800"
                                  onClick={async (e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    try {
                                      const result = await liaApi.generatePublicLink(job.backendId)
                                      if (result.success) {
                                        const fullUrl = `${window.location.origin}${result.public_url}`
                                        await navigator.clipboard.writeText(fullUrl)
                                        toast.success("Link copiado!", {
                                          description: "O link público da vaga foi copiado para a área de transferência."
                                        })
                                      }
                                    } catch (error) {
                                      toast.error("Erro ao gerar link", {
                                        description: "Não foi possível gerar o link público. Tente novamente."
                                      })
                                    }
                                  }}
                                  title="Compartilhar vaga (copiar link público)"
                                >
                                  <Share2 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-800"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    onJobClick(job)
                                  }}
                                  title="Abrir Kanban da vaga"
                                >
                                  <ChevronRight className="w-4 h-4 text-gray-800 dark:text-gray-200" />
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
  )
}
