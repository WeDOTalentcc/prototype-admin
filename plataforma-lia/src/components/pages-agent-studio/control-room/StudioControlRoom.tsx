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
import { RecentExecutionsTable } from "./RecentExecutionsTable"
import { LgpdAuditPanel } from "./LgpdAuditPanel"
import { DecisionTreeDrawer } from "../decision-tree/DecisionTreeDrawer"

export function StudioControlRoom() {
  const t = useTranslations("agents.studio.controlRoom")
  const tLive = useTranslations("agents.studio.controlRoom.liveSection")
  const tRecent = useTranslations("agents.studio.controlRoom.recentSection")
  const [openExecutionId, setOpenExecutionId] = React.useState<string | null>(null)

  return (
    <div className="mx-auto mt-6 flex w-full max-w-7xl flex-col gap-6">
      <header>
        <h2 className="text-base font-semibold text-lia-text-primary">{t("title")}</h2>
        <p className="mt-1 max-w-2xl text-xs text-lia-text-secondary">{t("description")}</p>
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
        <LiveAgentsList onOpenReasoning={setOpenExecutionId} />
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
        <RecentExecutionsTable onOpenReasoning={setOpenExecutionId} />
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
