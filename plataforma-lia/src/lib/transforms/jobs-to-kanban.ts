import type { Job, JobStatus } from "@/components/jobs"
import type { KanbanItem } from "@/components/pages/job-kanban/types"

export interface JobKanbanColumnDef {
  id: string
  statuses: JobStatus[]
  /** Tailwind class for the column accent dot (DS token) */
  accentClass: string
}

export const JOB_KANBAN_COLUMNS: JobKanbanColumnDef[] = [
  { id: "rascunho",   statuses: ["Rascunho"],                       accentClass: "bg-lia-text-disabled" },
  { id: "aguardando", statuses: ["Aguardando aprovação"],           accentClass: "bg-status-warning" },
  { id: "publicada",  statuses: ["Aprovada"],                       accentClass: "bg-lia-interactive-active" },
  { id: "ao_vivo",    statuses: ["Ativa", "Reaberta", "Interna"],   accentClass: "bg-status-success" },
  { id: "encerrada",  statuses: ["Fechada (preenchida)", "Fechada (expirada)", "Cancelada", "Concluída", "Arquivada", "Paralisada"], accentClass: "bg-lia-text-tertiary" },
]

interface JobToKanbanItemDeps {
  locale?: string
  labels: {
    deadlineSoon: (days: number) => string
    deadlinePast: (days: number) => string
    candidatesCount: (count: number) => string
  }
}

function daysBetween(target: string): number | null {
  if (!target) return null
  const t = new Date(target).getTime()
  if (Number.isNaN(t)) return null
  return Math.floor((t - Date.now()) / (1000 * 60 * 60 * 24))
}

function deptInitials(value?: string): string {
  if (!value) return "VG"
  const parts = value.split(/\s+/).filter(Boolean)
  return (parts[0]?.[0] ?? "V") + (parts[1]?.[0] ?? parts[0]?.[1] ?? "G")
}

export function jobToKanbanItem(job: Job, deps: JobToKanbanItemDeps): KanbanItem {
  const candidates = job.funnel?.total ?? 0
  const progress = computeProgress(job)

  const chips: string[] = []
  if (job.workModel) chips.push(job.workModel)
  const jobSeniority = (job as Job & { seniority?: string }).seniority || job.level
  if (jobSeniority) chips.push(jobSeniority)
  chips.push(deps.labels.candidatesCount(candidates))

  let dateLabel: string | undefined
  if (job.deadline) {
    const days = daysBetween(job.deadline)
    if (days != null && days >= 0 && days <= 7) {
      dateLabel = deps.labels.deadlineSoon(days)
    } else if (days != null && days < 0) {
      dateLabel = deps.labels.deadlinePast(Math.abs(days))
    } else if (deps.locale) {
      try {
        dateLabel = new Date(job.deadline).toLocaleDateString(deps.locale, { day: "2-digit", month: "short" })
      } catch {
        dateLabel = undefined
      }
    }
  }

  return {
    id: String(job.id),
    title: job.title,
    subtitle: job.department || undefined,
    tertiary: job.location || undefined,
    avatarFallback: deptInitials(job.department).toUpperCase(),
    progressPercent: progress != null ? Math.round(progress * 100) : undefined,
    chips,
    flagAttention: job.priority === "alta" ? { tooltip: deps.labels.candidatesCount(candidates) } : undefined,
    dateLabel,
  }
}

function computeProgress(job: Job): number | null {
  switch (job.status) {
    case "Rascunho":
      return 0.1
    case "Aguardando aprovação":
      return 0.3
    case "Aprovada":
      return 0.5
    case "Reaberta":
    case "Interna":
    case "Ativa":
      return 0.75
    case "Fechada (preenchida)":
    case "Concluída":
      return 1
    case "Fechada (expirada)":
    case "Cancelada":
    case "Arquivada":
    case "Paralisada":
      return null
    default:
      return null
  }
}

export function groupJobsByKanbanColumn(jobs: Job[]): Record<string, Job[]> {
  const groups: Record<string, Job[]> = {}
  JOB_KANBAN_COLUMNS.forEach((col) => {
    groups[col.id] = []
  })
  jobs.forEach((job) => {
    const col = JOB_KANBAN_COLUMNS.find((c) => c.statuses.includes(job.status))
    if (col) groups[col.id].push(job)
  })
  return groups
}
