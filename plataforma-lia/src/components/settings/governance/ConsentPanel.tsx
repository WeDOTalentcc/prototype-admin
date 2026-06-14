"use client"

import React, { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

interface ConsentRecord {
  purpose: string
  consent_type: string
  given: boolean
  revoked: boolean
  consent_date?: string | null
  revoked_at?: string | null
  source?: string | null
}

interface GranularConsentSummary {
  candidate_id: string
  company_id: string
  all_blocking_given: boolean
  consents: ConsentRecord[]
}

interface CompanyTrainingConsentStatus {
  consent_given: boolean
  is_active: boolean
  granted_at?: string | null
  revoked_at?: string | null
  version: string
  legal_basis: string
  consent_text?: string | null
  consent_source?: string | null
  user_id_granted?: string | null
  user_id_revoked?: string | null
  revoke_reason?: string | null
  last_updated?: string | null
}

const DEFAULT_TRAINING_CONSENT_TEXT =
  "Autorizo o uso de feedback de recrutadores para fine-tune do modelo Claude via AWS Bedrock, " +
  "respeitando a anonimização canonical (4 camadas PII strip) e mantendo o modelo customizado " +
  "exclusivo WeDOTalent (não-compartilhado). Conforme LGPD Art. 7 §I, Art. 8 e Art. 33."

function escapeCsv(v: unknown): string {
  if (v == null) return ""
  const s = String(v)
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

function exportCsv(candidateId: string, records: ConsentRecord[]) {
  const header = ["purpose", "consent_type", "given", "revoked", "consent_date", "revoked_at", "source"]
  const lines = [header.join(",")]
  for (const r of records) {
    lines.push(
      [
        escapeCsv(r.purpose),
        escapeCsv(r.consent_type),
        escapeCsv(r.given),
        escapeCsv(r.revoked),
        escapeCsv(r.consent_date),
        escapeCsv(r.revoked_at),
        escapeCsv(r.source),
      ].join(","),
    )
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `consent_${candidateId}_${new Date().toISOString().split("T")[0]}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ───────────────────────────────────────────────────────────────────────
// Candidate granular tab (preserved 273 LOC behavior canonical)
// ───────────────────────────────────────────────────────────────────────

function CandidateGranularConsentTab() {
  const t = useTranslations("settings.governanca.consent")
  const { companyId } = useCompanyId()
  const [candidateId, setCandidateId] = useState("")
  const [searchedId, setSearchedId] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<Record<string, boolean>>({})
  const {
    data: summary = null,
    isFetching: loading,
    refetch: reloadSummary,
  } = useQuery<GranularConsentSummary | null>({
    queryKey: ["consent-granular", searchedId],
    enabled: !!companyId && !!searchedId.trim(),
    queryFn: async () => {
      const res = await apiFetch(
        `/api/backend-proxy/consent/granular/${encodeURIComponent(searchedId.trim())}`,
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
  })
  const load = (id: string) => {
    const trimmed = id.trim()
    if (!companyId || !trimmed) return
    if (trimmed === searchedId) {
      void reloadSummary()
    } else {
      setSearchedId(trimmed)
    }
  }

  const revoke = async (purpose: string) => {
    if (!summary || !companyId) return
    setPending((p) => ({ ...p, [purpose]: true }))
    try {
      const res = await apiFetch(
        `/api/backend-proxy/consent/granular/${encodeURIComponent(summary.candidate_id)}/update`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            updates: { [purpose]: false },
            source: "governanca-admin" }) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      notifyChatOfSettingsUpdate({
        actionId: "revoke_granular_consent",
        section: "governance",
        field: purpose,
      })
      await reloadSummary()
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorRevoke"))
    } finally {
      setPending((p) => ({ ...p, [purpose]: false }))
    }
  }

  const records = summary?.consents ?? []
  const given = records.filter((r) => r.given && !r.revoked).length
  const revoked = records.filter((r) => r.revoked).length

  return (
    <div className="space-y-4" data-testid="consent-panel-candidate">
      <p className={textStyles.description}>{t("description")}</p>

      <form
        className={cn(cardStyles.default, "flex flex-wrap items-end gap-3 p-3")}
        onSubmit={(e) => {
          e.preventDefault()
          load(candidateId)
        }}
      >
        <label className="flex-1 text-[11px] text-lia-text-secondary">
          <div className="mb-0.5">{t("candidateIdLabel")}</div>
          <input
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            placeholder={t("candidateIdPlaceholder")}
            data-testid="consent-candidate-input"
            className="w-full rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
          />
        </label>
        <button
          type="submit"
          disabled={loading || !candidateId.trim()}
          data-testid="consent-load"
          className="rounded-md bg-wedo-purple px-3 py-1 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "…" : t("load")}
        </button>
        <button
          type="button"
          onClick={() => summary && exportCsv(summary.candidate_id, records)}
          disabled={!summary || records.length === 0}
          data-testid="consent-export-csv"
          className="rounded-md border border-lia-border-default px-3 py-1 text-xs font-medium hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("exportCsv")}
        </button>
      </form>

      {loading && <Loading variant="spinner" text={t("loading")} />}

      {error && (
        <div className={cn(cardStyles.default, "p-4 text-status-error")}>
          {t("errorLoad")}: {error}
        </div>
      )}

      {summary && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
            <SummaryCard label={t("totalConsents")} value={records.length} />
            <SummaryCard label={t("activeConsents")} value={given} accent="success" />
            <SummaryCard label={t("withdrawn")} value={revoked} accent="warning" />
          </div>

          <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
            <span className="font-mono">{summary.candidate_id}</span>
            <Chip
              variant={summary.all_blocking_given ? "success" : "warning"}
              density="compact"
            >
              {summary.all_blocking_given ? t("allBlockingGiven") : t("missingBlocking")}
            </Chip>
          </div>

          <div className={cn(cardStyles.default, "overflow-x-auto")}>
            <table className="min-w-full text-xs">
              <thead className="bg-lia-bg-secondary">
                <tr className="text-left text-lia-text-secondary">
                  <th className="px-3 py-2 font-medium">{t("colPurpose")}</th>
                  <th className="px-3 py-2 font-medium">{t("colType")}</th>
                  <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
                  <th className="px-3 py-2 font-medium">{t("colDate")}</th>
                  <th className="px-3 py-2 font-medium">{t("colSource")}</th>
                  <th className="px-3 py-2 font-medium">{t("colActions")}</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-3 py-6 text-center text-lia-text-secondary">
                      {t("empty")}
                    </td>
                  </tr>
                )}
                {records.map((r) => {
                  const status = r.revoked ? "revoked" : r.given ? "given" : "missing"
                  const variant =
                    status === "given" ? "success" : status === "revoked" ? "danger" : "neutral"
                  const isPending = pending[r.purpose]
                  return (
                    <tr key={r.purpose} className="border-t border-lia-border-subtle">
                      <td className="px-3 py-2 font-mono">{r.purpose}</td>
                      <td className="px-3 py-2">{r.consent_type}</td>
                      <td className="px-3 py-2">
                        <Chip variant={variant} density="compact">{t(`status_${status}`)}</Chip>
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px]">
                        {r.revoked_at
                          ? new Date(r.revoked_at).toLocaleString()
                          : r.consent_date
                            ? new Date(r.consent_date).toLocaleString()
                            : "-"}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px]">{r.source ?? "-"}</td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          disabled={!r.given || r.revoked || isPending}
                          onClick={() => revoke(r.purpose)}
                          data-testid={`consent-revoke-${r.purpose}`}
                          className="rounded-md border border-lia-border-default px-2 py-1 text-xs font-medium hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {t("revoke")}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

// ───────────────────────────────────────────────────────────────────────
// Training Data tab (T-21c) — company-level admin toggle
// ───────────────────────────────────────────────────────────────────────

function TrainingDataConsentTab() {
  const t = useTranslations("settings.governanca.consent.trainingData")
  const { companyId } = useCompanyId()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [revokeReason, setRevokeReason] = useState("")

  const {
    data: status = null,
    isLoading: loading,
    refetch: reloadStatus,
  } = useQuery<CompanyTrainingConsentStatus | null>({
    queryKey: ["company-training-consent", companyId],
    enabled: !!companyId,
    queryFn: async () => {
      const res = await apiFetch(
        `/api/backend-proxy/admin/consent/company-training-consent`,
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
  })

  const grant = async () => {
    if (!companyId) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/admin/consent/company-training-consent/grant`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            consent_text: DEFAULT_TRAINING_CONSENT_TEXT,
            version: "1.0" }) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await reloadStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorGrant"))
    } finally {
      setSubmitting(false)
    }
  }

  const revoke = async () => {
    if (!companyId || !revokeReason.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/admin/consent/company-training-consent/revoke`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: revokeReason.trim() }) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setRevokeOpen(false)
      setRevokeReason("")
      await reloadStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorRevoke"))
    } finally {
      setSubmitting(false)
    }
  }

  const isActive = status?.is_active ?? false

  return (
    <div className="space-y-4" data-testid="consent-panel-training-data">
      <div className={cn(cardStyles.default, "p-4 space-y-3")}>
        <h3 className={textStyles.subtitle}>{t("heading")}</h3>
        <p className={textStyles.description}>{t("description")}</p>

        <ul className="space-y-1 text-xs text-lia-text-secondary list-disc pl-4">
          <li>{t("disclaimerAnon")}</li>
          <li>{t("disclaimerCrossBorder")}</li>
          <li>{t("disclaimerCustomModel")}</li>
        </ul>

        <div className="flex flex-wrap items-center gap-2 text-[11px] text-lia-text-secondary">
          <span>{t("legalBasisLabel")}:</span>
          <Chip variant="neutral" density="compact">LGPD Art. 7 §I + 8 + 33</Chip>
          <a
            href="/docs/adr/ADR-RLHF-001"
            target="_blank"
            rel="noreferrer noopener"
            className="text-wedo-purple-text underline hover:opacity-80"
          >
            ADR-RLHF-001
          </a>
          <span aria-hidden>·</span>
          <a
            href="/docs/adr/ADR-LGPD-002"
            target="_blank"
            rel="noreferrer noopener"
            className="text-wedo-purple-text underline hover:opacity-80"
          >
            ADR-LGPD-002
          </a>
        </div>
      </div>

      {loading && <Loading variant="spinner" text={t("loading")} />}

      {error && (
        <div className={cn(cardStyles.default, "p-4 text-status-error")}>
          {error}
        </div>
      )}

      {status && (
        <div className={cn(cardStyles.default, "p-4 space-y-3")} data-testid="training-consent-status">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className={textStyles.subtitleMuted}>{t("statusLabel")}</div>
              <div className="mt-1 flex items-center gap-2">
                <Chip variant={isActive ? "success" : "neutral"} density="compact">
                  {isActive ? t("statusActive") : t("statusInactive")}
                </Chip>
                {status.version && (
                  <span className="font-mono text-[11px] text-lia-text-secondary">
                    v{status.version}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {!isActive && (
                <button
                  type="button"
                  onClick={grant}
                  disabled={submitting}
                  data-testid="training-consent-grant"
                  className="rounded-md bg-wedo-purple px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {t("grant")}
                </button>
              )}
              {isActive && (
                <button
                  type="button"
                  onClick={() => setRevokeOpen(true)}
                  disabled={submitting}
                  data-testid="training-consent-revoke-open"
                  className="rounded-md border border-status-error/40 px-3 py-1.5 text-xs font-medium text-status-error hover:bg-status-error/10 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {t("revoke")}
                </button>
              )}
            </div>
          </div>

          <dl className="grid grid-cols-2 gap-2 text-[11px]">
            <DetailField label={t("grantedAt")} value={status.granted_at} mono />
            <DetailField label={t("revokedAt")} value={status.revoked_at} mono />
            <DetailField label={t("legalBasis")} value={status.legal_basis} mono />
            <DetailField label={t("lastUpdated")} value={status.last_updated} mono />
            {status.revoke_reason && (
              <DetailField
                label={t("revokeReason")}
                value={status.revoke_reason}
                full
              />
            )}
          </dl>
        </div>
      )}

      {revokeOpen && (
        <div
          className={cn(cardStyles.default, "p-4 space-y-3 border-status-error/40")}
          data-testid="training-consent-revoke-modal"
        >
          <h4 className={textStyles.subtitle}>{t("revokeConfirmTitle")}</h4>
          <p className="text-xs text-lia-text-secondary">{t("revokeConfirmBody")}</p>
          <label className="block text-[11px] text-lia-text-secondary">
            <div className="mb-1">{t("revokeReasonLabel")}</div>
            <textarea
              value={revokeReason}
              onChange={(e) => setRevokeReason(e.target.value)}
              rows={3}
              data-testid="training-consent-revoke-reason"
              className="w-full rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            />
          </label>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setRevokeOpen(false)
                setRevokeReason("")
              }}
              disabled={submitting}
              className="rounded-md border border-lia-border-default px-3 py-1.5 text-xs font-medium hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("cancel")}
            </button>
            <button
              type="button"
              onClick={revoke}
              disabled={submitting || !revokeReason.trim()}
              data-testid="training-consent-revoke-confirm"
              className="rounded-md bg-status-error px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("revokeConfirm")}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function DetailField({
  label,
  value,
  mono,
  full }: {
  label: string
  value: string | null | undefined
  mono?: boolean
  full?: boolean
}) {
  return (
    <div className={full ? "col-span-2" : undefined}>
      <dt className="text-lia-text-secondary">{label}</dt>
      <dd
        className={cn(
          "text-lia-text-primary break-words",
          mono && "font-mono text-[11px]",
        )}
      >
        {value ?? "-"}
      </dd>
    </div>
  )
}

// ───────────────────────────────────────────────────────────────────────
// Metrics tab (consent adoption by purpose)
// ───────────────────────────────────────────────────────────────────────

interface ConsentStats {
  purpose: string
  granted: number
  revoked: number
  total: number
}

function ConsentMetricsTab() {
  const t = useTranslations("settings.governanca.consent.metrics")
  const { companyId } = useCompanyId()
  const {
    data: statsData,
    isLoading: loading,
    error: queryError,
  } = useQuery<ConsentStats[]>({
    queryKey: ["consent-stats", companyId],
    enabled: !!companyId,
    queryFn: async () => {
      const res = await apiFetch(`/api/backend-proxy/consent/stats`)
      if (!res.ok) {
        // Endpoint pode nao existir ainda — fallback silencioso para [].
        return []
      }
      const data = await res.json()
      let items: ConsentStats[] = []
      if (Array.isArray(data?.stats)) {
        items = data.stats
      } else if (Array.isArray(data)) {
        items = data
      } else if (Array.isArray(data?.by_type)) {
        items = data.by_type.map((entry: {
          consent_type: string
          total_granted: number
          total_revoked: number
          total_expired?: number
        }) => ({
          purpose: entry.consent_type,
          granted: entry.total_granted ?? 0,
          revoked: entry.total_revoked ?? 0,
          total: (entry.total_granted ?? 0) + (entry.total_revoked ?? 0),
        }))
      }
      return items
    },
  })
  const stats = statsData ?? null
  const error = queryError
    ? queryError instanceof Error
      ? queryError.message
      : t("errorLoad")
    : null

  const maxTotal = useMemo(
    () => stats?.reduce((m, s) => Math.max(m, s.total), 0) ?? 0,
    [stats],
  )

  return (
    <div className="space-y-4" data-testid="consent-panel-metrics">
      <p className={textStyles.description}>{t("description")}</p>

      {loading && <Loading variant="spinner" text={t("loading")} />}
      {error && (
        <div className={cn(cardStyles.default, "p-4 text-status-error")}>{error}</div>
      )}

      {stats && stats.length === 0 && !loading && (
        <div className={cn(cardStyles.default, "p-4 text-xs text-lia-text-secondary")}>
          {t("empty")}
        </div>
      )}

      {stats && stats.length > 0 && (
        <div className={cn(cardStyles.default, "p-4 space-y-2")}>
          {stats.map((s) => {
            const grantedPct = s.total > 0 ? (s.granted / s.total) * 100 : 0
            const revokedPct = s.total > 0 ? (s.revoked / s.total) * 100 : 0
            const barWidth = maxTotal > 0 ? (s.total / maxTotal) * 100 : 0
            return (
              <div key={s.purpose} className="text-xs">
                <div className="flex items-center justify-between font-mono text-[11px] text-lia-text-secondary">
                  <span>{s.purpose}</span>
                  <span>
                    {s.granted}/{s.total} ({grantedPct.toFixed(0)}%)
                  </span>
                </div>
                <div className="mt-1 h-2 w-full rounded-full bg-lia-bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-wedo-green"
                    style={{ width: `${barWidth * (grantedPct / 100)}%` }}
                  />
                  <div
                    className="h-full -mt-2 bg-wedo-orange"
                    style={{
                      width: `${barWidth * (revokedPct / 100)}%`,
                      marginLeft: `${barWidth * (grantedPct / 100)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ───────────────────────────────────────────────────────────────────────
// Main panel (Tabs canonical)
// ───────────────────────────────────────────────────────────────────────

export function ConsentPanel() {
  const t = useTranslations("settings.governanca.consent")

  return (
    <div className="space-y-3" data-testid="consent-panel">
      <Tabs defaultValue="candidate-granular">
        <TabsList>
          <TabsTrigger value="candidate-granular" data-testid="consent-tab-candidate">
            {t("tabCandidate")}
          </TabsTrigger>
          <TabsTrigger value="training-data" data-testid="consent-tab-training-data">
            {t("tabTrainingData")}
          </TabsTrigger>
          <TabsTrigger value="metrics" data-testid="consent-tab-metrics">
            {t("tabMetrics")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="candidate-granular" className="mt-4">
          <CandidateGranularConsentTab />
        </TabsContent>

        <TabsContent value="training-data" className="mt-4">
          <TrainingDataConsentTab />
        </TabsContent>

        <TabsContent value="metrics" className="mt-4">
          <ConsentMetricsTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function SummaryCard({
  label,
  value,
  accent }: {
  label: string
  value: number | string
  accent?: "success" | "warning"
}) {
  const color =
    accent === "success"
      ? "text-wedo-green-text"
      : accent === "warning"
        ? "text-wedo-orange-text"
        : "text-lia-text-primary"
  return (
    <div className={cn(cardStyles.default, "p-3")}>
      <div className={textStyles.subtitleMuted}>{label}</div>
      <div className={cn("mt-1 font-data tabular-nums text-xl font-semibold", color)}>{value}</div>
    </div>
  )
}

export default ConsentPanel
