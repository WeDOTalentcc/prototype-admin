"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { NovoProjetoWizard } from "@/app/[locale]/(dashboard)/projetos/new/NovoProjetoWizard"
import { Megaphone, Users, CheckCircle2, ChevronRight, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"
import { useCampaignsList, type CampaignItem, type CampaignStatus } from "@/hooks/jobs/useCampaignsList"

// ── Status config ──────────────────────────────────────────────────────────

interface StatusConfig {
  label: string
  badge: string
}

function getStatusConfig(status: CampaignStatus): StatusConfig {
  switch (status) {
    case "active":
      return { label: "Ativa", badge: badgeStyles.success }
    case "paused":
      return { label: "Pausada", badge: badgeStyles.warning }
    case "completed":
      return { label: "Concluída", badge: badgeStyles.green }
    case "cancelled":
      return { label: "Cancelada", badge: badgeStyles.error }
    default:
      return { label: status, badge: badgeStyles.default }
  }
}

// ── Stage progress strip ───────────────────────────────────────────────────

function StageStrip({ campaign }: { campaign: CampaignItem }) {
  const { stages } = campaign
  if (!stages.length) return null
  return (
    <div className="flex gap-1">
      {stages.map((stage) => (
        <div
          key={stage.name}
          title={stage.label}
          className={cn(
            "h-1 flex-1 rounded-full",
            stage.status === "completed" && "bg-lia-btn-primary-bg",
            stage.status === "in_progress" && "bg-lia-accent",
            stage.status === "pending" && "bg-lia-bg-tertiary"
          )}
        />
      ))}
    </div>
  )
}

// ── Stats row ──────────────────────────────────────────────────────────────

function StatsRow({ campaign }: { campaign: CampaignItem }) {
  return (
    <div className="flex items-center gap-4 text-micro text-lia-text-secondary">
      <span className="flex items-center gap-1">
        <Users className="w-3 h-3" />
        {campaign.total_candidates} candidatos
      </span>
      {campaign.candidates_hired > 0 && (
        <span className="flex items-center gap-1 text-status-success">
          <CheckCircle2 className="w-3 h-3" />
          {campaign.candidates_hired} contratados
        </span>
      )}
    </div>
  )
}

// ── Skeleton card ──────────────────────────────────────────────────────────

function CampaignCardSkeleton() {
  return (
    <div className="rounded-md border border-lia-border-subtle bg-lia-bg-paper p-4 space-y-3 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary shrink-0" />
        <div className="flex-1 space-y-1.5">
          <div className="h-3.5 bg-lia-bg-tertiary rounded w-3/4" />
          <div className="h-3 bg-lia-bg-tertiary rounded w-1/3" />
        </div>
      </div>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-1 flex-1 rounded-full bg-lia-bg-tertiary" />
        ))}
      </div>
    </div>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────

function CampanhasEmptyState() {
  return (
    <div className="col-span-full flex flex-col items-center justify-center py-16 text-center gap-3">
      <div className="w-12 h-12 rounded-full bg-lia-bg-secondary flex items-center justify-center">
        <Megaphone className="w-6 h-6 text-lia-text-secondary" />
      </div>
      <p className="text-body text-lia-text-primary font-medium">Nenhum projeto ativo</p>
      <p className="text-small text-lia-text-secondary max-w-xs">
        Crie um projeto para organizar e automatizar seu processo de sourcing e triagem.
      </p>
    </div>
  )
}

// ── Campaign card ──────────────────────────────────────────────────────────

function CampaignCard({ campaign }: { campaign: CampaignItem }) {
  const statusCfg = getStatusConfig(campaign.status)
  const currentStageLabel =
    campaign.stages.find((s) => s.status === "in_progress")?.label ??
    campaign.stages[campaign.current_stage_index]?.label ??
    null

  return (
    <StudioCardShell
      icon={<Megaphone className="w-4 h-4 text-lia-text-secondary" />}
      title={campaign.name}
      statusBadge={<span className={statusCfg.badge}>{statusCfg.label}</span>}
      subtitle={currentStageLabel ? `Etapa atual: ${currentStageLabel}` : undefined}
      bodySlot={<StageStrip campaign={campaign} />}
      actionsSlot={
        <div className="flex w-full items-center justify-between">
          <StatsRow campaign={campaign} />
          <button
            type="button"
            className="flex items-center gap-1 text-micro text-lia-btn-primary-bg hover:underline shrink-0"
            onClick={() => {
              window.location.href = `/pt/projetos/${campaign.id}`
            }}
          >
            Ver detalhes
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      }
    />
  )
}

// ── Main section ───────────────────────────────────────────────────────────

export function ProjetosSection() {
  const { campaigns, isLoading, isError } = useCampaignsList()
  const [showWizard, setShowWizard] = useState(false)

  return (
    <>
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-heading-sm text-lia-text-primary font-semibold">Projetos de Recrutamento</h2>
        <Button
          size="sm"
          onClick={() => setShowWizard(true)}
          className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
        >
          <Plus className="w-4 h-4" />
          Novo projeto
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <>
            <CampaignCardSkeleton />
            <CampaignCardSkeleton />
            <CampaignCardSkeleton />
          </>
        ) : isError ? (
          <div className="col-span-full text-small text-lia-text-error text-center py-8">
            Erro ao carregar campanhas. Tente novamente.
          </div>
        ) : campaigns.length === 0 ? (
          <CampanhasEmptyState />
        ) : (
          campaigns.map((c) => <CampaignCard key={c.id} campaign={c} />)
        )}
      </div>
    </div>

    <NovoProjetoWizard open={showWizard} onClose={() => setShowWizard(false)} />
    </>
  )
}
