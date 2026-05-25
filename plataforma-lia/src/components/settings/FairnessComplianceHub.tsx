"use client"

/**
 * FairnessComplianceHub — dispatcher minimal + status banner FairnessGuard.
 *
 * Histórico:
 * - PR 2 (2026-05-25): dashboard movido para /wedo-admin/fairness/ (staff).
 * - PR 3 (2026-05-25): AITransparencyPanel movido para /wedo-admin/governanca/ai-transparency/.
 *   ConsentPanel + AuditLogsSummaryPanel adicionados (vindos de Governança que dissolveu).
 * - Quick Wins P0 (2026-05-25): banner "FairnessGuard ativo" read-only adicionado no topo
 *   de TODAS subsections (visibilidade canônica do gate sempre-on per LGPD).
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 *
 * Subsections:
 * - lgpd-candidatos (DSR Art. 20 — DSRInboxPanel filtered)
 * - consent (consent viewer/revoke — vindo de Governança)
 * - audit-summary (read-only últimos 30d — split do AuditLogsPanel)
 * - studio (Agent Studio compliance)
 */

import React from "react"
import { Shield } from "lucide-react"
import { useTranslations } from "next-intl"
import { StudioComplianceView } from "./StudioComplianceView"
import { DSRInboxPanel } from "./governance/DSRInboxPanel"
import { ConsentPanel } from "./governance/ConsentPanel"
import { AuditLogsSummaryPanel } from "./compliance/AuditLogsSummaryPanel"

interface FairnessComplianceHubProps {
  activeSubsection: string
}

/**
 * Banner read-only sempre visível.
 * FairnessGuard é obrigatório por LGPD/EU AI Act — não há toggle, é sempre on.
 * Feature 3 do PR 2 (Quick Wins P0): status read-only em vez de toggle ilusório.
 */
function FairnessGuardStatusBanner() {
  const t = useTranslations("settings.fairnessCompliance.fairnessGuardStatus")
  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-lg bg-status-success/10 border border-status-success/30"
      data-testid="fairness-guard-status-banner"
    >
      <div className="w-8 h-8 rounded-md bg-status-success/15 flex items-center justify-center shrink-0">
        <Shield className="w-4 h-4 text-status-success" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-lia-text-primary">
          {t("title")}
        </p>
        <p className="text-xs text-lia-text-secondary mt-0.5">
          {t("subtitle")}
        </p>
      </div>
    </div>
  )
}

export function FairnessComplianceHub({ activeSubsection }: FairnessComplianceHubProps) {
  let content: React.ReactNode = null

  if (activeSubsection === "studio") {
    content = <StudioComplianceView />
  } else if (activeSubsection === "lgpd-candidatos") {
    // WT-2022 P1.B: DSRInbox filtered por Art. 20 (decisão automatizada review).
    content = <DSRInboxPanel defaultRequestType="explanation" />
  } else if (activeSubsection === "consent") {
    // PR 3 (2026-05-25): Consent viewer/revoke — vindo de Governança.
    content = <ConsentPanel />
  } else if (activeSubsection === "audit-summary") {
    // PR 3 (2026-05-25): Audit log summary read-only últimos 30d.
    // Para drill-down completo, staff acessa /wedo-admin/governanca/audit-logs/.
    content = <AuditLogsSummaryPanel />
  }

  return (
    <div className="space-y-4" data-testid="compliance-lgpd-hub">
      <FairnessGuardStatusBanner />
      {content}
    </div>
  )
}
