import type { Job, JobStatus } from "@/components/jobs"
import type { KanbanItem } from "@/components/pages/job-kanban/types"
import { getJobSeniority } from "@/lib/jobs/seniority"
import { formatJobLocation } from "@/lib/jobs/location"

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
    /** Task #562 — Labels novos. Mapper só pede o que o caller fornece. */
    ageDays?: (days: number) => string
    deadlineDays?: (days: number) => string
    deadlineOverdue?: (days: number) => string
    /** Task #562 — Labels de ribbon por motivo (caller controla i18n). */
    ribbon?: {
      deadlineOverdue: (days: number) => string
      deadlineSoon: (days: number) => string
      urgent: () => string
      pendingApproval: () => string
      noCandidates: () => string
      label: () => string
    }
  }
}

function daysBetween(target: string): number | null {
  if (!target) return null
  const t = new Date(target).getTime()
  if (Number.isNaN(t)) return null
  return Math.floor((t - Date.now()) / (1000 * 60 * 60 * 24))
}

function daysSince(start: string): number | null {
  if (!start) return null
  const t = new Date(start).getTime()
  if (Number.isNaN(t)) return null
  return Math.floor((Date.now() - t) / (1000 * 60 * 60 * 24))
}

function deptInitials(value?: string): string {
  if (!value) return "VG"
  const parts = value.split(/\s+/).filter(Boolean)
  return (parts[0]?.[0] ?? "V") + (parts[1]?.[0] ?? parts[0]?.[1] ?? "G")
}

function personInitials(name?: string): string | null {
  if (!name) return null
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return null
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function jobToKanbanItem(job: Job, deps: JobToKanbanItemDeps): KanbanItem {
  const candidates = job.funnel?.total ?? 0
  const progress = computeProgress(job)

  // Task #562 — Chips com ícone semântico para paridade com card de
  // candidato (Briefcase/Star/Users). Fallback para string quando não há
  // ícone associado.
  const chips: KanbanItem["chips"] = []
  if (job.workModel) chips.push({ icon: "briefcase", label: job.workModel })
  // Audit task #531 (G23-01) — leitura via helper canônico (precedência
  // `seniority` → `level` legacy). Mantém shape para evitar regressão.
  const jobSeniority = getJobSeniority(job as Job & { seniority?: string })
  if (jobSeniority) chips.push({ icon: "star", label: jobSeniority })
  chips.push({ icon: "users", label: deps.labels.candidatesCount(candidates) })

  let dateLabel: string | undefined
  let deadlineStatus: KanbanItem["deadlineStatus"]
  if (job.deadline) {
    const days = daysBetween(job.deadline)
    if (days != null && days >= 0 && days <= 7) {
      dateLabel = deps.labels.deadlineSoon(days)
      deadlineStatus = "warning"
    } else if (days != null && days < 0) {
      dateLabel = deps.labels.deadlinePast(Math.abs(days))
      deadlineStatus = "danger"
    } else if (days != null && deps.locale) {
      try {
        dateLabel = new Date(job.deadline).toLocaleDateString(deps.locale, { day: "2-digit", month: "short" })
        deadlineStatus = "ok"
      } catch (e) {
        if (e instanceof RangeError) {
          dateLabel = undefined
        } else {
          throw e
        }
      }
    }
  }

  // Task #562 — Idade da vaga (desde openDate). Sem default: se openDate
  // ausente/inválido, o campo simplesmente não aparece no card.
  const ageDays = job.openDate ? (daysSince(job.openDate) ?? undefined) : undefined

  // Task #562 — Mini funil. Só inclui se houver ao menos 1 candidato no
  // total — evita pintar 4 zeros no card.
  const funnel = job.funnel && job.funnel.total > 0
    ? {
        total: job.funnel.total,
        screening: job.funnel.screening ?? 0,
        interview: job.funnel.interview ?? 0,
        final: job.funnel.final ?? 0,
        hired: job.funnel.hired ?? 0,
      }
    : undefined

  // Task #562 — Owner. Sem placeholder; só renderiza se o backend forneceu
  // o nome do manager.
  const ownerInitials = personInitials(job.manager)
  const owner = job.manager && ownerInitials
    ? { name: job.manager, initials: ownerInitials }
    : undefined

  // Task #562 — Ribbon de atenção acionável. Cobre estados que o
  // recrutador precisa ver no card sem abrir o detalhe:
  //  • deadline vencido     → danger
  //  • deadline ≤ 7 dias    → warning
  //  • urgencyLevel >= 4    → warning
  //  • aguardando aprovação → info
  //  • vaga ativa há > 14d sem candidatos → info
  //  • prioridade alta      → warning (fallback)
  // Cada condição define um `reason` (string já localizada pelo caller)
  // e o ribbon escala pela primeira correspondência na ordem acima.
  const ribbonLabels = deps.labels.ribbon
  let ribbon: KanbanItem["ribbon"] | undefined
  if (ribbonLabels) {
    const deadlineDays = job.deadline ? daysBetween(job.deadline) : null
    const stale = ageDays != null && ageDays > 14 && (job.funnel?.total ?? 0) === 0
    const isUrgent = (job.urgencyLevel ?? 0) >= 4
    const isPendingApproval = job.status === "Aguardando aprovação"
    const isHighPriority = job.priority === "alta"

    let variant: "warning" | "danger" | "info" | null = null
    let reason: string | null = null

    if (deadlineDays != null && deadlineDays < 0) {
      variant = "danger"
      reason = ribbonLabels.deadlineOverdue(Math.abs(deadlineDays))
    } else if (deadlineDays != null && deadlineDays >= 0 && deadlineDays <= 7) {
      variant = "warning"
      reason = ribbonLabels.deadlineSoon(deadlineDays)
    } else if (isUrgent) {
      variant = "warning"
      reason = ribbonLabels.urgent()
    } else if (isPendingApproval) {
      variant = "info"
      reason = ribbonLabels.pendingApproval()
    } else if (stale) {
      variant = "info"
      reason = ribbonLabels.noCandidates()
    } else if (isHighPriority) {
      variant = "warning"
      reason = ribbonLabels.urgent()
    }

    if (variant && reason) {
      ribbon = { label: ribbonLabels.label(), variant, reason }
    }
  }

  return {
    id: String(job.id),
    title: job.title,
    subtitle: job.department || undefined,
    tertiary: formatJobLocation(job.location) || undefined,
    avatarFallback: deptInitials(job.department).toUpperCase(),
    progressPercent: progress != null ? Math.round(progress * 100) : undefined,
    chips,
    flagAttention: job.priority === "alta" ? { tooltip: deps.labels.candidatesCount(candidates) } : undefined,
    dateLabel,
    funnel,
    ribbon,
    owner,
    ageDays,
    deadlineStatus,
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
