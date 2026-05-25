"use client"

/**
 * AITransparencyPanel — T-18 EU AI Act Annex III (Wave 1 Agent #2, 2026-05-21)
 *
 * Documentacao canonical de transparencia da IA WeDOTalent:
 *   - Art. 13 Explainability Statement (8 secoes canonical: onde/por que/como
 *     a IA opera, monitoring, corrective action, decisao humana final, opt-out).
 *   - Art. 14 Human Oversight (override de decisoes automatizadas).
 *   - Automated Decisions (LGPD Art. 22 right to explanation).
 *   - Annex III Technical Documentation (Model Card, training summary,
 *     intended use, limitations, fairness results).
 *
 * Backend endpoints (Agent #1 paralelo):
 *   GET    /api/backend-proxy/ai-transparency/explainability-statement
 *   GET    /api/backend-proxy/ai-transparency/automated-decisions
 *   POST   /api/backend-proxy/ai-transparency/human-oversight/{decision_id}/override
 *   GET    /api/backend-proxy/ai-transparency/technical-documentation
 *
 * Pattern canonical: BiasAuditPanel/AuditLogsPanel (apiFetch + useCompanyId +
 * design tokens via textStyles/cardStyles/tabStyles, zero hardcode).
 */

import React, { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Shield, FileText, UserCheck, Book, Download, AlertCircle } from "lucide-react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, tabStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

type TabId = "explainability" | "decisions" | "oversight" | "technical"

interface ExplainabilitySection {
  id: string
  title: string
  content: string
}

interface ExplainabilityStatement {
  version: string
  updated_at: string
  sections: ExplainabilitySection[]
}

interface AutomatedDecision {
  id: string
  candidate_id_masked: string
  decision_type: string
  criteria_used: string[]
  score: number | null
  human_reviewed: boolean
  overridden: boolean
  created_at: string
}

interface AutomatedDecisionsResponse {
  items: AutomatedDecision[]
  total: number
}

interface ModelCardData {
  model_name: string
  model_version: string
  intended_use: string
  training_data_summary: string
  limitations: string[]
  fairness_results: Array<{ dimension: string; ratio: number; passes_four_fifths: boolean }>
  last_evaluation_at: string
}

interface TechnicalDocumentation {
  model_card: ModelCardData
  annex_iii_compliance: {
    art9_risk_management: boolean
    art10_data_governance: boolean
    art11_technical_docs: boolean
    art12_record_keeping: boolean
    art13_transparency: boolean
    art14_human_oversight: boolean
    art15_accuracy: boolean
  }
}

const TAB_DEFINITIONS: Array<{ id: TabId; labelKey: string; descKey: string; icon: React.ElementType }> = [
  { id: "explainability", labelKey: "tabs.explainability", descKey: "tabs.explainabilityDesc", icon: FileText },
  { id: "decisions", labelKey: "tabs.decisions", descKey: "tabs.decisionsDesc", icon: Shield },
  { id: "oversight", labelKey: "tabs.oversight", descKey: "tabs.oversightDesc", icon: UserCheck },
  { id: "technical", labelKey: "tabs.technical", descKey: "tabs.technicalDesc", icon: Book },
]

export function AITransparencyPanel() {
  const t = useTranslations("settings.aiTransparency")
  const { companyId } = useCompanyId()
  const [active, setActive] = useState<TabId>("explainability")

  const [statement, setStatement] = useState<ExplainabilityStatement | null>(null)
  const [decisions, setDecisions] = useState<AutomatedDecision[]>([])
  const [techDocs, setTechDocs] = useState<TechnicalDocumentation | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [overrideTarget, setOverrideTarget] = useState<AutomatedDecision | null>(null)
  const [overrideReason, setOverrideReason] = useState("")
  const [overrideSubmitting, setOverrideSubmitting] = useState(false)
  const [overrideError, setOverrideError] = useState<string | null>(null)

  // --- fetch helpers ---------------------------------------------------------

  const loadStatement = useCallback(async () => {
    if (!companyId) return
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch(
        "/api/backend-proxy/ai-transparency/explainability-statement",
        {},
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: ExplainabilityStatement = await res.json()
      setStatement(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorLoad"))
    } finally {
      setLoading(false)
    }
  }, [companyId, t])

  const loadDecisions = useCallback(async () => {
    if (!companyId) return
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch(
        "/api/backend-proxy/ai-transparency/automated-decisions?limit=50",
        {},
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: AutomatedDecisionsResponse = await res.json()
      const items = Array.isArray(data) ? data : (data.items ?? [])
      setDecisions(items)
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorLoad"))
    } finally {
      setLoading(false)
    }
  }, [companyId, t])

  const loadTechnicalDocs = useCallback(async () => {
    if (!companyId) return
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch(
        "/api/backend-proxy/ai-transparency/technical-documentation",
        {},
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: TechnicalDocumentation = await res.json()
      setTechDocs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorLoad"))
    } finally {
      setLoading(false)
    }
  }, [companyId, t])

  // --- effect: load per active tab ------------------------------------------

  useEffect(() => {
    if (!companyId) return
    if (active === "explainability") {
      loadStatement()
    } else if (active === "decisions" || active === "oversight") {
      loadDecisions()
    } else if (active === "technical") {
      loadTechnicalDocs()
    }
  }, [active, companyId, loadStatement, loadDecisions, loadTechnicalDocs])

  // --- override flow ---------------------------------------------------------

  const submitOverride = async () => {
    if (!overrideTarget || !companyId) return
    setOverrideSubmitting(true)
    setOverrideError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/ai-transparency/human-oversight/${encodeURIComponent(overrideTarget.id)}/override`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            override_reason: overrideReason.trim(),
            new_decision: "human_reviewed",
          }),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      // Refresh decisions list (overridden flag now true)
      notifyChatOfSettingsUpdate({
        actionId: "override_ai_decision",
        section: "governance",
        field: overrideTarget.id,
      })
      setOverrideTarget(null)
      setOverrideReason("")
      await loadDecisions()
    } catch (err) {
      setOverrideError(err instanceof Error ? err.message : t("errorOverride"))
    } finally {
      setOverrideSubmitting(false)
    }
  }

  const exportPdf = () => {
    if (!companyId) return
    console.warn("WT-2022 P0.D: Export PDF endpoint not implemented yet")
  }

  // --- render ----------------------------------------------------------------

  return (
    <div className="space-y-6" data-testid="ai-transparency-panel">
      <header className="space-y-1">
        <h1 className={textStyles.h1}>{t("title")}</h1>
        <p className={textStyles.description}>{t("description")}</p>
      </header>

      <nav
        className={cn(tabStyles.pillContainer, "flex-wrap")}
        role="tablist"
        aria-label={t("title")}
      >
        {TAB_DEFINITIONS.map((tab) => {
          const Icon = tab.icon
          const isActive = active === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`ai-transparency-panel-${tab.id}`}
              data-testid={`ai-transparency-tab-${tab.id}`}
              className={isActive ? tabStyles.pillActive : tabStyles.pill}
              onClick={() => setActive(tab.id)}
            >
              <Icon className={tabStyles.pillIcon} aria-hidden="true" />
              {t(tab.labelKey)}
            </button>
          )
        })}
      </nav>

      <section
        id={`ai-transparency-panel-${active}`}
        role="tabpanel"
        aria-labelledby={`ai-transparency-tab-${active}`}
        data-testid={`ai-transparency-tabpanel-${active}`}
      >
        {loading && <Loading variant="spinner" text={t("loading")} />}
        {error && !loading && (
          <div className={cn(cardStyles.default, "flex items-start gap-3 p-4 text-status-error")}>
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <div>
              <div className={textStyles.subtitle}>{t("errorLoad")}</div>
              <div className={cn(textStyles.description, "text-status-error")}>{error}</div>
            </div>
          </div>
        )}

        {!loading && !error && active === "explainability" && (
          <ExplainabilityTab statement={statement} t={t} />
        )}
        {!loading && !error && active === "decisions" && (
          <DecisionsTab decisions={decisions} t={t} />
        )}
        {!loading && !error && active === "oversight" && (
          <OversightTab
            decisions={decisions}
            t={t}
            onOverride={(d) => {
              setOverrideTarget(d)
              setOverrideReason("")
              setOverrideError(null)
            }}
          />
        )}
        {!loading && !error && active === "technical" && (
          <TechnicalTab docs={techDocs} t={t} onExportPdf={exportPdf} />
        )}
      </section>

      {overrideTarget && (
        <OverrideModal
          target={overrideTarget}
          reason={overrideReason}
          setReason={setOverrideReason}
          submitting={overrideSubmitting}
          error={overrideError}
          onCancel={() => {
            setOverrideTarget(null)
            setOverrideReason("")
            setOverrideError(null)
          }}
          onSubmit={submitOverride}
          t={t}
        />
      )}
    </div>
  )
}

// =============================================================================
// Tab: Explainability Statement (Art. 13)
// =============================================================================

function ExplainabilityTab({
  statement,
  t,
}: {
  statement: ExplainabilityStatement | null
  t: ReturnType<typeof useTranslations>
}) {
  if (!statement) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-center")}>
        <span className={textStyles.description}>{t("explainability.empty")}</span>
      </div>
    )
  }
  return (
    <div className="space-y-4" data-testid="ai-transparency-explainability">
      <div className={cn(cardStyles.flat, "flex flex-wrap items-center justify-between gap-2 p-3")}>
        <div className={textStyles.subtitleMuted}>
          {t("explainability.version", { v: statement.version })}
        </div>
        <div className={textStyles.subtitleMuted}>
          {t("explainability.updatedAt")}: {new Date(statement.updated_at).toLocaleString()}
        </div>
      </div>
      <div className="space-y-3">
        {statement.sections.map((section, index) => (
          // Defensive: backend pode retornar sections com id ausente/duplicado.
          // Fallback para index garante uniqueness sem assumir contrato runtime.
          <div key={section.id || `section-${index}`} className={cn(cardStyles.default, "space-y-2 p-4")}>
            <h2 className={textStyles.h2}>{section.title}</h2>
            <p className={cn(textStyles.body, "whitespace-pre-wrap")}>{section.content}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Tab: Automated Decisions (LGPD Art. 22)
// =============================================================================

function DecisionsTab({
  decisions,
  t,
}: {
  decisions: AutomatedDecision[]
  t: ReturnType<typeof useTranslations>
}) {
  if (decisions.length === 0) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-center")}>
        <span className={textStyles.description}>{t("decisions.empty")}</span>
      </div>
    )
  }
  return (
    <div className={cn(cardStyles.default, "overflow-x-auto")} data-testid="ai-transparency-decisions">
      <table className="min-w-full text-xs">
        <thead className="bg-lia-bg-secondary">
          <tr className="text-left text-lia-text-secondary">
            <th className="px-3 py-2 font-medium">{t("decisions.colCandidate")}</th>
            <th className="px-3 py-2 font-medium">{t("decisions.colType")}</th>
            <th className="px-3 py-2 font-medium">{t("decisions.colCriteria")}</th>
            <th className="px-3 py-2 font-medium">{t("decisions.colScore")}</th>
            <th className="px-3 py-2 font-medium">{t("decisions.colStatus")}</th>
            <th className="px-3 py-2 font-medium">{t("decisions.colWhen")}</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((d) => {
            const variant = d.overridden
              ? "warning"
              : d.human_reviewed
                ? "success"
                : "info"
            const statusKey = d.overridden
              ? "decisions.statusOverridden"
              : d.human_reviewed
                ? "decisions.statusReviewed"
                : "decisions.statusAutomated"
            return (
              <tr key={d.id} className="border-t border-lia-border-subtle">
                <td className="px-3 py-2 font-mono text-[11px]">{d.candidate_id_masked}</td>
                <td className="px-3 py-2">{d.decision_type}</td>
                <td className="px-3 py-2 text-[11px]">
                  {(d.criteria_used ?? []).slice(0, 3).join(", ") || "-"}
                </td>
                <td className="px-3 py-2 font-mono">
                  {typeof d.score === "number" ? d.score.toFixed(2) : "-"}
                </td>
                <td className="px-3 py-2">
                  <Chip variant={variant} density="compact">
                    {t(statusKey)}
                  </Chip>
                </td>
                <td className="px-3 py-2 font-mono text-[11px]">
                  {d.created_at ? new Date(d.created_at).toLocaleString() : "-"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// =============================================================================
// Tab: Human Oversight (Art. 14)
// =============================================================================

function OversightTab({
  decisions,
  t,
  onOverride,
}: {
  decisions: AutomatedDecision[]
  t: ReturnType<typeof useTranslations>
  onOverride: (d: AutomatedDecision) => void
}) {
  const overridable = decisions.filter((d) => !d.overridden)
  if (overridable.length === 0) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-center")}>
        <span className={textStyles.description}>{t("oversight.empty")}</span>
      </div>
    )
  }
  return (
    <div className="space-y-3" data-testid="ai-transparency-oversight">
      <p className={textStyles.description}>{t("oversight.help")}</p>
      <div className={cn(cardStyles.default, "overflow-x-auto")}>
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("decisions.colCandidate")}</th>
              <th className="px-3 py-2 font-medium">{t("decisions.colType")}</th>
              <th className="px-3 py-2 font-medium">{t("decisions.colScore")}</th>
              <th className="px-3 py-2 font-medium">{t("oversight.colAction")}</th>
            </tr>
          </thead>
          <tbody>
            {overridable.map((d) => (
              <tr key={d.id} className="border-t border-lia-border-subtle">
                <td className="px-3 py-2 font-mono text-[11px]">{d.candidate_id_masked}</td>
                <td className="px-3 py-2">{d.decision_type}</td>
                <td className="px-3 py-2 font-mono">
                  {typeof d.score === "number" ? d.score.toFixed(2) : "-"}
                </td>
                <td className="px-3 py-2">
                  <button
                    type="button"
                    data-testid={`ai-transparency-override-${d.id}`}
                    className="rounded-md bg-wedo-purple px-3 py-1 text-xs font-medium text-white hover:opacity-90"
                    onClick={() => onOverride(d)}
                  >
                    {t("oversight.overrideBtn")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function OverrideModal({
  target,
  reason,
  setReason,
  submitting,
  error,
  onCancel,
  onSubmit,
  t,
}: {
  target: AutomatedDecision
  reason: string
  setReason: (v: string) => void
  submitting: boolean
  error: string | null
  onCancel: () => void
  onSubmit: () => void
  t: ReturnType<typeof useTranslations>
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-transparency-override-title"
      data-testid="ai-transparency-override-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className={cn(cardStyles.default, "w-full max-w-md space-y-3 p-4")}>
        <h2 id="ai-transparency-override-title" className={textStyles.h2}>
          {t("oversight.modalTitle")}
        </h2>
        <p className={textStyles.description}>
          {t("oversight.modalDescription", {
            candidate: target.candidate_id_masked,
            type: target.decision_type,
          })}
        </p>
        <label className="block space-y-1">
          <span className={textStyles.label}>{t("oversight.reasonLabel")}</span>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            data-testid="ai-transparency-override-reason"
            data-field="override_reason"
            className="w-full rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
          />
        </label>
        {error && <div className="text-xs text-status-error">{error}</div>}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-md border border-lia-border-default px-3 py-1 text-xs font-medium text-lia-text-primary hover:bg-lia-bg-secondary disabled:opacity-50"
          >
            {t("oversight.cancel")}
          </button>
          <button
            type="button"
            data-testid="ai-transparency-override-submit"
            onClick={onSubmit}
            disabled={submitting || reason.trim().length === 0}
            className="rounded-md bg-wedo-purple px-3 py-1 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "…" : t("oversight.confirm")}
          </button>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Tab: Technical Documentation (Annex III)
// =============================================================================

function TechnicalTab({
  docs,
  t,
  onExportPdf,
}: {
  docs: TechnicalDocumentation | null
  t: ReturnType<typeof useTranslations>
  onExportPdf: () => void
}) {
  if (!docs) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-center")}>
        <span className={textStyles.description}>{t("technical.empty")}</span>
      </div>
    )
  }
  const card = docs.model_card
  const compliance = docs.annex_iii_compliance
  return (
    <div className="space-y-4" data-testid="ai-transparency-technical">
      <div className="flex justify-end">
        <button
          type="button"
          data-testid="ai-transparency-export-pdf"
          onClick={onExportPdf}
          className="inline-flex items-center gap-1 rounded-md border border-lia-border-default px-3 py-1 text-xs font-medium text-lia-text-primary hover:bg-lia-bg-secondary"
        >
          <Download className="h-3.5 w-3.5" aria-hidden="true" />
          {t("technical.exportPdf")}
        </button>
      </div>

      <div className={cn(cardStyles.default, "space-y-3 p-4")}>
        <h2 className={textStyles.h2}>{t("technical.modelCardTitle")}</h2>
        <dl className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Definition label={t("technical.modelName")} value={card.model_name} />
          <Definition label={t("technical.modelVersion")} value={card.model_version} />
          <Definition
            label={t("technical.lastEval")}
            value={card.last_evaluation_at ? new Date(card.last_evaluation_at).toLocaleString() : "-"}
          />
        </dl>
        <Definition label={t("technical.intendedUse")} value={card.intended_use} multiline />
        <Definition
          label={t("technical.trainingSummary")}
          value={card.training_data_summary}
          multiline
        />
        <div className="space-y-1">
          <div className={textStyles.label}>{t("technical.limitations")}</div>
          <ul className="ml-5 list-disc space-y-0.5">
            {(card.limitations ?? []).map((l, i) => (
              <li key={i} className={textStyles.body}>
                {l}
              </li>
            ))}
            {(card.limitations ?? []).length === 0 && (
              <li className={textStyles.description}>-</li>
            )}
          </ul>
        </div>
      </div>

      <div className={cn(cardStyles.default, "space-y-3 p-4")}>
        <h2 className={textStyles.h2}>{t("technical.fairnessTitle")}</h2>
        {(card.fairness_results ?? []).length === 0 ? (
          <span className={textStyles.description}>{t("technical.fairnessEmpty")}</span>
        ) : (
          <table className="min-w-full text-xs">
            <thead className="bg-lia-bg-secondary">
              <tr className="text-left text-lia-text-secondary">
                <th className="px-3 py-2 font-medium">{t("technical.colDimension")}</th>
                <th className="px-3 py-2 font-medium">{t("technical.colRatio")}</th>
                <th className="px-3 py-2 font-medium">{t("technical.colFourFifths")}</th>
              </tr>
            </thead>
            <tbody>
              {card.fairness_results.map((r) => (
                <tr key={r.dimension} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2 font-mono">{r.dimension}</td>
                  <td className="px-3 py-2 font-mono">{r.ratio.toFixed(3)}</td>
                  <td className="px-3 py-2">
                    <Chip
                      variant={r.passes_four_fifths ? "success" : "danger"}
                      density="compact"
                    >
                      {r.passes_four_fifths ? t("technical.pass") : t("technical.fail")}
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className={cn(cardStyles.default, "space-y-3 p-4")}>
        <h2 className={textStyles.h2}>{t("technical.annexTitle")}</h2>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {(
            [
              ["art9_risk_management", compliance.art9_risk_management],
              ["art10_data_governance", compliance.art10_data_governance],
              ["art11_technical_docs", compliance.art11_technical_docs],
              ["art12_record_keeping", compliance.art12_record_keeping],
              ["art13_transparency", compliance.art13_transparency],
              ["art14_human_oversight", compliance.art14_human_oversight],
              ["art15_accuracy", compliance.art15_accuracy],
            ] as Array<[string, boolean]>
          ).map(([key, ok]) => (
            <div
              key={key}
              className={cn(cardStyles.flat, "flex items-center justify-between gap-2 p-2")}
            >
              <span className={textStyles.body}>{t(`technical.${key}`)}</span>
              <Chip variant={ok ? "success" : "warning"} density="compact">
                {ok ? t("technical.compliant") : t("technical.pending")}
              </Chip>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Definition({
  label,
  value,
  multiline,
}: {
  label: string
  value: string | number | null | undefined
  multiline?: boolean
}) {
  return (
    <div className="space-y-1">
      <div className={textStyles.label}>{label}</div>
      <div className={cn(textStyles.body, multiline && "whitespace-pre-wrap")}>
        {value === null || value === undefined || value === "" ? "-" : value}
      </div>
    </div>
  )
}

export default AITransparencyPanel
