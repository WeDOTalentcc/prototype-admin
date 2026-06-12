"use client"

import React from 'react'
import { PanelRight, Briefcase } from 'lucide-react'
import { useToolSurface } from '@/contexts/ToolSurfaceContext'

export interface JobSummary {
  id: string
  title: string
  department?: string | null
  status?: string | null
  candidateCount?: number | null
}

const STATUS_LABELS: Record<string, string> = {
  ao_vivo: 'Ao vivo',
  publicada: 'Publicada',
  rascunho: 'Rascunho',
  enriquecida: 'Enriquecida',
  aguardando_aprovacao: 'Aguardando',
  encerrada: 'Encerrada',
}

const STATUS_COLORS: Record<string, string> = {
  ao_vivo: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  publicada: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  rascunho: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300',
}

function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return null
  const label = STATUS_LABELS[status] ?? status
  const color =
    STATUS_COLORS[status] ??
    'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'
  return (
    <span
      className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${color}`}
    >
      {label}
    </span>
  )
}

function JobRow({ job }: { job: JobSummary }) {
  return (
    <div className="flex items-center gap-2 py-1.5">
      <Briefcase className="size-4 shrink-0 text-gray-400 dark:text-gray-500" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
          {job.title}
        </p>
        {job.department && (
          <p className="truncate text-xs text-gray-500 dark:text-gray-400">
            {job.department}
          </p>
        )}
      </div>
      <StatusBadge status={job.status} />
    </div>
  )
}

interface JobListCardProps {
  jobs: JobSummary[]
  totalCount: number
  onOpenPanel?: () => void
}

export function JobListCard({ jobs, totalCount, onOpenPanel }: JobListCardProps) {
  const surface = useToolSurface()

  if (surface === 'panel') {
    return (
      <div className="flex flex-col gap-0.5 px-1 py-2">
        <p className="mb-2 text-xs text-gray-500 dark:text-gray-400 font-medium">
          {totalCount} vagas
        </p>
        {jobs.map((j) => (
          <JobRow key={j.id} job={j} />
        ))}
      </div>
    )
  }

  // inline mode (default)
  const preview = jobs.slice(0, 5)
  const remaining = totalCount - preview.length

  return (
    <div className="mt-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {totalCount} vagas encontradas
        </span>
        {onOpenPanel && (
          <button
            onClick={onOpenPanel}
            className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Ver todas <PanelRight className="size-3" />
          </button>
        )}
      </div>
      {preview.map((j) => (
        <JobRow key={j.id} job={j} />
      ))}
      {remaining > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 pt-1">
          +{remaining} outras
        </p>
      )}
    </div>
  )
}
