"use client"

import React from "react"
import { PenLine, Briefcase, ArrowRight, Rocket } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"
import { useJobDraftsList, type JobDraftItem, type JobDraftStatus } from "@/hooks/jobs/useJobDraftsList"

// ── Status config ──────────────────────────────────────────────────────────

interface StatusConfig {
  label: string
  badge: string
}

function getStatusConfig(status: JobDraftStatus): StatusConfig {
  switch (status) {
    case "draft":
      return { label: "Rascunho", badge: badgeStyles.default }
    case "structured":
      return { label: "Estruturado", badge: badgeStyles.info }
    case "reviewed":
      return { label: "Revisado", badge: badgeStyles.warning }
    case "confirmed":
      return { label: "Confirmado", badge: badgeStyles.success }
    case "published":
      return { label: "Publicado", badge: badgeStyles.green }
    case "cancelled":
      return { label: "Cancelado", badge: badgeStyles.error }
    default:
      return { label: status, badge: badgeStyles.default }
  }
}

// ── Progress bar ───────────────────────────────────────────────────────────

function CompletionBar({ current, total }: { current: number; total: number }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-lia-bg-tertiary rounded-full overflow-hidden">
        <div
          className="h-full bg-lia-btn-primary-bg rounded-full transition-colors"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-micro text-lia-text-secondary tabular-nums">{pct}%</span>
    </div>
  )
}

// ── Skeleton card ──────────────────────────────────────────────────────────

function DraftCardSkeleton() {
  return (
    <div className="rounded-md border border-lia-border-subtle bg-lia-bg-paper p-4 space-y-3 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary shrink-0" />
        <div className="flex-1 space-y-1.5">
          <div className="h-3.5 bg-lia-bg-tertiary rounded w-3/4" />
          <div className="h-3 bg-lia-bg-tertiary rounded w-1/2" />
        </div>
      </div>
      <div className="h-1 bg-lia-bg-tertiary rounded-full" />
      <div className="flex gap-2">
        <div className="h-7 bg-lia-bg-tertiary rounded w-24" />
      </div>
    </div>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────

function DraftsEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-xl bg-lia-bg-tertiary flex items-center justify-center mb-4">
        <PenLine className="w-6 h-6 text-lia-text-secondary" />
      </div>
      <p className="text-base-ui font-medium text-lia-text-primary mb-1">
        Nenhum rascunho por aqui
      </p>
      <p className="text-sm text-lia-text-secondary max-w-xs">
        Peça à LIA para iniciar uma nova vaga — ela vai gerar um rascunho inteligente para você revisar.
      </p>
    </div>
  )
}

// ── Single draft card ──────────────────────────────────────────────────────

function DraftCard({ draft, onContinue, onPublish }: {
  draft: JobDraftItem
  onContinue: (id: string) => void
  onPublish: (id: string) => void
}) {
  const statusConfig = getStatusConfig(draft.status)
  const title = draft.job_title ?? "Vaga sem título"
  const subtitle = [draft.department, draft.seniority].filter(Boolean).join(" · ") || "Sem departamento"
  const canPublish = draft.status === "confirmed" || draft.status === "reviewed"

  return (
    <StudioCardShell
      tone="elevated"
      icon={<PenLine className="w-4 h-4 text-lia-text-secondary" />}
      iconWrapperClassName="bg-lia-bg-tertiary"
      title={title}
      subtitle={<span className="text-lia-text-secondary text-sm">{subtitle}</span>}
      statusBadge={
        <span className={cn(statusConfig.badge, "text-micro")}>
          {statusConfig.label}
        </span>
      }
      bodySlot={
        <CompletionBar current={draft.current_step} total={draft.total_steps} />
      }
      actionsSlot={
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => onContinue(draft.id)}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-lia-text-primary hover:text-lia-btn-primary-bg transition-colors"
          >
            Continuar
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          {canPublish && (
            <button
              onClick={() => onPublish(draft.id)}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-status-success hover:text-status-success/80 transition-colors ml-2"
            >
              <Rocket className="w-3.5 h-3.5" />
              Publicar
            </button>
          )}
        </div>
      }
    />
  )
}

// ── Section ────────────────────────────────────────────────────────────────

export function JobDraftsSection() {
  const { drafts, total, isLoading, isError } = useJobDraftsList()

  const handleContinue = (id: string) => {
    window.location.href = `/pt/jobs/wizard?draft_id=${id}`
  }

  const handlePublish = async (id: string) => {
    try {
      const res = await fetch(`/api/backend-proxy/job-drafts/${id}/publish`, {
        method: "POST",
      })
      if (res.ok) {
        window.location.href = "/pt/jobs"
      }
    } catch {
      // non-critical — page will reload naturally
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Briefcase className="w-4 h-4 text-lia-text-secondary" />
        <h2 className="text-base-ui font-semibold text-lia-text-primary">
          Rascunhos
        </h2>
        {!isLoading && total > 0 && (
          <span className={cn(badgeStyles.default, "text-micro")}>
            {total}
          </span>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <DraftCardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <p role="alert" className="text-sm text-status-error">
          Erro ao carregar rascunhos. Tente recarregar a página.
        </p>
      ) : drafts.length === 0 ? (
        <DraftsEmptyState />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {drafts.map((draft) => (
            <DraftCard
              key={draft.id}
              draft={draft}
              onContinue={handleContinue}
              onPublish={handlePublish}
            />
          ))}
        </div>
      )}
    </div>
  )
}
