// Onda 1 F2 (2026-05-27) — Studio Sala de Controle (4ª aba).
//
// Composição:
//   - LiveAgentsList (auto-refresh 5s)
//   - RecentExecutionsTable (filtros agente/surface/status)
//   - LgpdAuditPanel (collapsible + export CSV)
//
// Cada seção em um StudioCardShell-like, mas com cabeçalho próprio (não usa
// a shape de "agent card"). Mantém layout consistente com outras abas do Studio.
"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { Activity, History } from "lucide-react"
import { LiveAgentsList } from "./LiveAgentsList"
import { MorningDigest } from "./MorningDigest"
import { RecentExecutionsTable } from "./RecentExecutionsTable"
import { LgpdAuditPanel } from "./LgpdAuditPanel"
import { DecisionTreeDrawer } from "../decision-tree/DecisionTreeDrawer"
// Onda 3 F7 (2026-05-28) — filtro global "Por surface" propagado pros componentes.
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type ControlRoomSurfaceFilter =
  | "all"
  | "talent_pool"
  | "job"
  | "pipeline_stage"
  | "candidate_list"

export function StudioControlRoom() {
  const t = useTranslations("agents.studio.controlRoom")
  const tLive = useTranslations("agents.studio.controlRoom.liveSection")
  const tRecent = useTranslations("agents.studio.controlRoom.recentSection")
  const [openExecutionId, setOpenExecutionId] = React.useState<string | null>(null)
  // Onda 3 F7 — filtro global "Por surface" propagado pros componentes filhos.
  const [surfaceFilter, setSurfaceFilter] =
    React.useState<ControlRoomSurfaceFilter>("all")
  const tFilters = useTranslations("agents.studio.controlRoom.filters")

  return (
    <div className="mx-auto mt-6 flex w-full max-w-7xl flex-col gap-6">
      {/* Onda C4.2 — Morning Brief: o que aconteceu enquanto você não estava. */}
      <MorningDigest onOpenReasoning={setOpenExecutionId} />
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-lia-text-primary">{t("title")}</h2>
          <p className="mt-1 max-w-2xl text-xs text-lia-text-secondary">{t("description")}</p>
        </div>
        <div
          className="flex items-center gap-2"
          data-testid="control-room-surface-filter"
        >
          <span className="text-xs text-lia-text-secondary">
            {tFilters("surface")}
          </span>
          <Select
            value={surfaceFilter}
            onValueChange={(v) => setSurfaceFilter(v as ControlRoomSurfaceFilter)}
          >
            <SelectTrigger
              className="h-8 w-44 border-lia-border-default text-xs"
              aria-label={tFilters("surface")}
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{tFilters("surfaceAll")}</SelectItem>
              <SelectItem value="talent_pool">{tFilters("surfacePool")}</SelectItem>
              <SelectItem value="job">{tFilters("surfaceJobLabel")}</SelectItem>
              <SelectItem value="pipeline_stage">{tFilters("surfacePipelineLabel")}</SelectItem>
              <SelectItem value="candidate_list">{tFilters("surfaceDecidir")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </header>

      {/* Seção Ao Vivo */}
      <section
        className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
        aria-labelledby="control-room-live-heading"
        data-testid="control-room-live-section"
      >
        <div className="mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4 text-lia-cyan" aria-hidden="true" />
          <h3
            id="control-room-live-heading"
            className="text-sm font-semibold text-lia-text-primary"
          >
            {tLive("title")}
          </h3>
          <span className="text-xs text-lia-text-tertiary">— {tLive("subtitle")}</span>
        </div>
        <LiveAgentsList onOpenReasoning={setOpenExecutionId} surfaceFilter={surfaceFilter} />
      </section>

      {/* Seção Histórico recente */}
      <section
        className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
        aria-labelledby="control-room-recent-heading"
        data-testid="control-room-recent-section"
      >
        <div className="mb-3 flex items-center gap-2">
          <History className="h-4 w-4 text-lia-text-secondary" aria-hidden="true" />
          <h3
            id="control-room-recent-heading"
            className="text-sm font-semibold text-lia-text-primary"
          >
            {tRecent("title")}
          </h3>
          <span className="text-xs text-lia-text-tertiary">— {tRecent("subtitle")}</span>
        </div>
        <RecentExecutionsTable onOpenReasoning={setOpenExecutionId} surfaceFilter={surfaceFilter} />
      </section>

      {/* Seção Auditoria LGPD */}
      <section
        aria-labelledby="control-room-lgpd-heading"
        data-testid="control-room-lgpd-section"
      >
        <h3 id="control-room-lgpd-heading" className="sr-only">
          {t("title")}
        </h3>
        <LgpdAuditPanel />
      </section>

      {/* Drawer canonical (props canonical: executionId + onClose) */}
      <DecisionTreeDrawer
        executionId={openExecutionId}
        onClose={() => setOpenExecutionId(null)}
      />
    </div>
  )
}
