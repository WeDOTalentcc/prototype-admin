"use client"

/**
 * FairnessComplianceHub — dispatcher minimal.
 *
 * Histórico (2026-05-25, PR 2 plan canonical em ~/.claude/plans/jolly-roaming-moler.md):
 * Antes desta PR, esse hub renderizava:
 *   - default → Dashboard de Fairness (summary cards + chart + export CSV/JSON + incidents)
 *   - studio → StudioComplianceView
 *   - lgpd-candidatos → DSRInboxPanel
 *   - ai-transparency → AITransparencyPanel
 *
 * Em PR 2, o dashboard foi movido para `(staff)/wedo-admin/fairness/` —
 * componente canonical em `src/components/_wedo_internal/fairness/FairnessDashboard.tsx`.
 *
 * Settings-page-enhanced.tsx remove a subsection `'fairness'` do hub
 * `'fairness-compliance'`, então a default branch deste dispatcher
 * não é mais alcançada via UI cliente. Mantida defensiva como `null`.
 *
 * Subsections KEEP cliente:
 * - studio (Agent Studio compliance)
 * - lgpd-candidatos (DSR Art. 20)
 * - ai-transparency (move em PR 3 — vide plan)
 */

import React from "react"
import { StudioComplianceView } from "./StudioComplianceView"
import { DSRInboxPanel } from "./governance/DSRInboxPanel"
import { AITransparencyPanel } from "./governance/AITransparencyPanel"

interface FairnessComplianceHubProps {
  activeSubsection: string
}

export function FairnessComplianceHub({ activeSubsection }: FairnessComplianceHubProps) {
  if (activeSubsection === "studio") {
    return <StudioComplianceView />
  }

  // P0.8 (audit 2026-05-20): LGPD Candidatos subsection renders DSR inbox
  // canonical. Distinção semântica: aqui foco é Art. 20 (revisão de decisão
  // automatizada); Governança lista todos os DSR.
  if (activeSubsection === "lgpd-candidatos") {
    // WT-2022 P1.B: filter Art. 20 (decisão automatizada review)
    return <DSRInboxPanel defaultRequestType="explanation" />
  }

  // T-18 EU AI Act Annex III: subsection canonical para AI Transparency.
  // Render componente dedicado com 4 tabs (Art. 13 Explainability +
  // Automated Decisions + Art. 14 Oversight + Annex III Technical Docs).
  // Será movido em PR 3 (plan canonical).
  if (activeSubsection === "ai-transparency") {
    return <AITransparencyPanel />
  }

  // Default: dashboard movido para wedo-admin (staff-only).
  // Subsection 'fairness' não está mais declarada em settings-page-enhanced.tsx,
  // então essa branch não é alcançada via UI cliente. Defensive null.
  return null
}
