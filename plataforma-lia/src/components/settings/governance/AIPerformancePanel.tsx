"use client"

import React, { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Activity,
  BarChart3,
  Pause,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, tabStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExperimentVariant {
  variant_name: string
  traffic_percentage?: number
  is_active?: boolean
}

interface Experiment {
  name: string
  variants: ExperimentVariant[]
  current_winner?: string | null
  p_value?: number | null
  n_arms?: number
  status?: string
  total_observations?: number | null
  created_at?: string | null
  recommendation?: string | null
}

interface BanditPosterior {
  arm: string
  alpha: number
  beta: number
  expected_value: number
  n_observations: number
}

interface EarlyStopDecision {
  action: "stop_winner" | "stop_futility" | "continue"
  winner?: string | null
  p_value?: number | null
  alpha_per_look?: number | null
  look_number?: number
  max_looks?: number
  reason?: string
  observed_effect?: number | null
}

interface PromoteResult {
  promoted: boolean
  winner?: string | null
  reason?: string
  gate_used?: string
  n_arms?: number
  alpha_adjusted?: number
  fairness_violation?: boolean
  thompson_winner_probability?: number
}

interface HistoryEntry {
  kind: string
  variant?: string | null
  p_value?: number | null
  mean_diff?: number | null
  metric?: string | null
  n_control?: number | null
  n_variant?: number | null
}

interface HistoryPayload {
  test_name: string
  winner?: { variant?: string; p_value?: number; mean_diff?: number; metric?: string } | null
  recommendation?: string | null
  total_observations?: number | null
  history: HistoryEntry[]
}

interface DashboardSummary {
  active_count: number
  promoted_ready: number
  pending_fairness_gate: number
  total_observations: number
}

type TabId = "experiments" | "bandit" | "early-stop" | "history"

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AIPerformancePanel(): React.ReactElement {
  const t = useTranslations("settings.governanca.aiPerformance")
  const { companyId } = useCompanyId()

  const [activeTab, setActiveTab] = useState<TabId>("experiments")
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [experiments, setExperiments] = useState<Experiment[]>([])
  // Auditoria 2026-05-22: initial=false. Antes (true) + `if (!companyId) return`
  // no useEffect deixava spinner eterno se useCompanyId nao resolvesse o JWT.
  // Agora loading so vira true quando o fetch realmente arranca.
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null)
  const [posteriors, setPosteriors] = useState<BanditPosterior[]>([])
  const [posteriorsLoading, setPosteriorsLoading] = useState(false)
  const [earlyStopLook, setEarlyStopLook] = useState<number>(1)
  const [earlyStopMaxLooks, setEarlyStopMaxLooks] = useState<number>(10)
  const [earlyStopResult, setEarlyStopResult] = useState<EarlyStopDecision | null>(null)
  const [earlyStopLoading, setEarlyStopLoading] = useState(false)
  const [history, setHistory] = useState<HistoryPayload | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [promoting, setPromoting] = useState<string | null>(null)
  const [promoteResult, setPromoteResult] = useState<PromoteResult | null>(null)

  // Auditoria 2026-05-22: authHeaders ficou vazio depois do Boy Scout que
  // removeu o X-Company-ID anti-pattern (REGRA 6). Memo mantido pra evitar
  // tocar os ~5 call-sites `headers: authHeaders` no resto do arquivo. Nao
  // depende de companyId (JWT canonical via apiFetch + proxy ja resolve auth).
  const authHeaders = useMemo<Record<string, string>>(() => ({}), [])

  // -------------------------------------------------------------------------
  // Load experiments + summary on mount
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!companyId) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [expRes, sumRes] = await Promise.all([
          apiFetch("/api/backend-proxy/ai-performance/experiments", { headers: authHeaders }),
          apiFetch("/api/backend-proxy/ai-performance/dashboard/summary", { headers: authHeaders }),
        ])
        if (!expRes.ok) throw new Error(`HTTP ${expRes.status}`)
        if (!sumRes.ok) throw new Error(`HTTP ${sumRes.status}`)
        const expBody = await expRes.json()
        const sumBody = await sumRes.json()
        if (cancelled) return
        const items: Experiment[] = expBody.experiments ?? []
        setExperiments(items)
        setSummary(sumBody.summary ?? null)
        if (items.length > 0 && !selectedExperiment) {
          setSelectedExperiment(items[0].name)
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : t("errorLoad"))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [companyId, authHeaders, selectedExperiment, t])

  // -------------------------------------------------------------------------
  // Load posteriors when bandit tab active + experiment selected
  // -------------------------------------------------------------------------

  const loadPosteriors = useCallback(async (testName: string) => {
    setPosteriorsLoading(true)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/ai-performance/experiments/${encodeURIComponent(testName)}/posteriors`,
        { headers: authHeaders },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      setPosteriors(body.posteriors ?? [])
    } catch (err) {
      setPosteriors([])
      setError(err instanceof Error ? err.message : t("errorLoad"))
    } finally {
      setPosteriorsLoading(false)
    }
  }, [authHeaders, t])

  const loadHistory = useCallback(async (testName: string) => {
    setHistoryLoading(true)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/ai-performance/experiments/${encodeURIComponent(testName)}/history`,
        { headers: authHeaders },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body: HistoryPayload = await res.json()
      setHistory(body)
    } catch {
      setHistory(null)
    } finally {
      setHistoryLoading(false)
    }
  }, [authHeaders])

  useEffect(() => {
    if (activeTab === "bandit" && selectedExperiment) {
      void loadPosteriors(selectedExperiment)
    }
    if (activeTab === "history" && selectedExperiment) {
      void loadHistory(selectedExperiment)
    }
  }, [activeTab, selectedExperiment, loadPosteriors, loadHistory])

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  const promoteWinner = async (testName: string, useThompson: boolean) => {
    setPromoting(testName)
    setPromoteResult(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/ai-performance/experiments/${encodeURIComponent(testName)}/promote-winner`,
        {
          method: "POST",
          headers: { ...authHeaders, "Content-Type": "application/json" },
          body: JSON.stringify({ use_thompson_sampling: useThompson, thompson_threshold: 0.95 }),
        },
      )
      const body: PromoteResult = await res.json()
      setPromoteResult(body)
      notifyChatOfSettingsUpdate({
        actionId: "promote_ab_test_winner",
        section: "governance",
        field: testName,
      })
    } catch (err) {
      setPromoteResult({
        promoted: false,
        reason: err instanceof Error ? err.message : "request_failed",
      })
    } finally {
      setPromoting(null)
    }
  }

  const runEarlyStop = async () => {
    if (!selectedExperiment) return
    setEarlyStopLoading(true)
    setEarlyStopResult(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/ai-performance/experiments/${encodeURIComponent(selectedExperiment)}/check-early-stop`,
        {
          method: "POST",
          headers: { ...authHeaders, "Content-Type": "application/json" },
          body: JSON.stringify({
            look_number: earlyStopLook,
            max_looks: earlyStopMaxLooks,
            alpha_total: 0.01,
            futility_threshold: 0.001,
          }),
        },
      )
      const body: EarlyStopDecision = await res.json()
      setEarlyStopResult(body)
      notifyChatOfSettingsUpdate({
        actionId: "ab_test_early_stop_check",
        section: "governance",
        field: selectedExperiment,
      })
    } catch {
      setEarlyStopResult({ action: "continue", reason: "request_failed" })
    } finally {
      setEarlyStopLoading(false)
    }
  }

  // -------------------------------------------------------------------------
  // Render helpers
  // -------------------------------------------------------------------------

  const tabs: Array<{ id: TabId; label: string; icon: React.ElementType }> = [
    { id: "experiments", label: t("tabs.experiments"), icon: Activity },
    { id: "bandit", label: t("tabs.bandit"), icon: BarChart3 },
    { id: "early-stop", label: t("tabs.earlyStop"), icon: Pause },
    { id: "history", label: t("tabs.history"), icon: CheckCircle2 },
  ]

  if (loading) {
    return (
      <div className={cardStyles.default}>
        <Loading />
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn(cardStyles.default, "p-6")}>
        <p className={textStyles.description}>{t("errorLoad")}: {error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="ai-performance-panel">
      <header className="space-y-1">
        <h2 className={textStyles.h2}>{t("title")}</h2>
        <p className={textStyles.description}>{t("description")}</p>
      </header>

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <SummaryCard label={t("summary.active")} value={summary.active_count} icon={Activity} />
          <SummaryCard
            label={t("summary.promotedReady")}
            value={summary.promoted_ready}
            icon={ShieldCheck}
          />
          <SummaryCard
            label={t("summary.pendingFairness")}
            value={summary.pending_fairness_gate}
            icon={AlertTriangle}
          />
          <SummaryCard
            label={t("summary.totalObservations")}
            value={summary.total_observations}
            icon={BarChart3}
          />
        </div>
      )}

      <nav
        className={cn(tabStyles.pillContainer, "flex-wrap")}
        role="tablist"
        aria-label={t("title")}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              data-testid={`ai-performance-tab-${tab.id}`}
              className={isActive ? tabStyles.pillActive : tabStyles.pill}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon className={tabStyles.pillIcon} aria-hidden="true" />
              {tab.label}
            </button>
          )
        })}
      </nav>

      <section role="tabpanel" data-testid={`ai-performance-panel-${activeTab}`}>
        {activeTab === "experiments" && (
          <ExperimentsTab
            experiments={experiments}
            promoteWinner={promoteWinner}
            promoting={promoting}
            promoteResult={promoteResult}
            onSelect={setSelectedExperiment}
            selected={selectedExperiment}
            t={t}
          />
        )}
        {activeTab === "bandit" && (
          <BanditTab
            posteriors={posteriors}
            loading={posteriorsLoading}
            experimentName={selectedExperiment}
            experiments={experiments}
            onSelect={setSelectedExperiment}
            t={t}
          />
        )}
        {activeTab === "early-stop" && (
          <EarlyStopTab
            experiments={experiments}
            selected={selectedExperiment}
            onSelect={setSelectedExperiment}
            look={earlyStopLook}
            setLook={setEarlyStopLook}
            maxLooks={earlyStopMaxLooks}
            setMaxLooks={setEarlyStopMaxLooks}
            run={runEarlyStop}
            loading={earlyStopLoading}
            result={earlyStopResult}
            t={t}
          />
        )}
        {activeTab === "history" && (
          <HistoryTab
            history={history}
            loading={historyLoading}
            experimentName={selectedExperiment}
            experiments={experiments}
            onSelect={setSelectedExperiment}
            t={t}
          />
        )}
      </section>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components (kept in same file for cohesion — under 500 LOC total)
// ---------------------------------------------------------------------------

function SummaryCard({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: number
  icon: React.ElementType
}): React.ReactElement {
  return (
    <div className={cn(cardStyles.default, "p-4 flex items-start justify-between gap-3")}>
      <div>
        <p className={textStyles.description}>{label}</p>
        <p className="text-2xl font-semibold mt-1 text-lia-text-primary">{value}</p>
      </div>
      <Icon className="w-6 h-6 text-lia-text-tertiary" aria-hidden="true" />
    </div>
  )
}

interface TabPropsBase {
  t: (k: string) => string
}

function ExperimentsTab({
  experiments,
  promoteWinner,
  promoting,
  promoteResult,
  onSelect,
  selected,
  t,
}: TabPropsBase & {
  experiments: Experiment[]
  promoteWinner: (name: string, useThompson: boolean) => Promise<void>
  promoting: string | null
  promoteResult: PromoteResult | null
  onSelect: (name: string) => void
  selected: string | null
}): React.ReactElement {
  if (experiments.length === 0) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-center")}>
        <p className={textStyles.description}>{t("empty.experiments")}</p>
      </div>
    )
  }
  return (
    <div className="space-y-3">
      {experiments.map((exp) => {
        const isSelected = selected === exp.name
        const isPromoting = promoting === exp.name
        return (
          <div
            key={exp.name}
            className={cn(cardStyles.default, "p-4 space-y-3", isSelected && "ring-2 ring-lia-accent")}
            data-testid={`experiment-row-${exp.name}`}
            onClick={() => onSelect(exp.name)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onSelect(exp.name)
            }}
          >
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <h3 className="font-semibold text-lia-text-primary">{exp.name}</h3>
                <p className={textStyles.description}>
                  {t("experiments.arms")}: {exp.n_arms ?? exp.variants.length} ·{" "}
                  {t("experiments.observations")}: {exp.total_observations ?? 0}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {exp.current_winner ? (
                  <Chip variant="info">
                    {t("experiments.winner")}: {exp.current_winner}
                  </Chip>
                ) : (
                  <Chip variant="neutral">{t("experiments.noWinner")}</Chip>
                )}
                {typeof exp.p_value === "number" && (
                  <Chip variant={exp.p_value < 0.01 ? "info" : "neutral"}>
                    p={exp.p_value.toFixed(4)}
                  </Chip>
                )}
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant="secondary"
                disabled={isPromoting || !exp.current_winner}
                onClick={(e) => {
                  e.stopPropagation()
                  void promoteWinner(exp.name, false)
                }}
                data-testid={`promote-frequentist-${exp.name}`}
              >
                {isPromoting ? <Loader2 className="w-4 h-4 animate-spin" /> : t("experiments.promoteFrequentist")}
              </Button>
              <Button
                size="sm"
                variant="primary"
                disabled={isPromoting || !exp.current_winner}
                onClick={(e) => {
                  e.stopPropagation()
                  void promoteWinner(exp.name, true)
                }}
                data-testid={`promote-thompson-${exp.name}`}
              >
                {t("experiments.promoteThompson")}
              </Button>
            </div>
          </div>
        )
      })}

      {promoteResult && (
        <div
          className={cn(
            cardStyles.default,
            "p-4 border-l-4",
            promoteResult.promoted
              ? "border-status-success"
              : promoteResult.fairness_violation
              ? "border-status-error"
              : "border-status-warning",
          )}
          data-testid="promote-result"
          role="status"
        >
          <p className="font-semibold text-lia-text-primary">
            {promoteResult.promoted ? t("experiments.promoted") : t("experiments.notPromoted")}
          </p>
          <p className={textStyles.description}>{promoteResult.reason}</p>
          {promoteResult.gate_used && (
            <p className={textStyles.description}>
              {t("experiments.gateUsed")}: {promoteResult.gate_used}
            </p>
          )}
          {promoteResult.fairness_violation && (
            <p className="text-status-error mt-1 text-sm">{t("experiments.fairnessBlocked")}</p>
          )}
        </div>
      )}
    </div>
  )
}

function BanditTab({
  posteriors,
  loading,
  experimentName,
  experiments,
  onSelect,
  t,
}: TabPropsBase & {
  posteriors: BanditPosterior[]
  loading: boolean
  experimentName: string | null
  experiments: Experiment[]
  onSelect: (name: string) => void
}): React.ReactElement {
  return (
    <div className="space-y-3">
      <ExperimentSelector
        experiments={experiments}
        selected={experimentName}
        onSelect={onSelect}
        t={t}
      />
      <p className={textStyles.description}>{t("bandit.explanation")}</p>
      {loading ? (
        <Loading />
      ) : posteriors.length === 0 ? (
        <div className={cn(cardStyles.default, "p-6 text-center")}>
          <p className={textStyles.description}>{t("empty.posteriors")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {posteriors.map((p) => {
            const barWidth = Math.round(p.expected_value * 100)
            return (
              <div
                key={p.arm}
                className={cn(cardStyles.default, "p-4")}
                data-testid={`bandit-row-${p.arm}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-lia-text-primary">{p.arm}</span>
                  <span className={textStyles.description}>
                    α={p.alpha.toFixed(2)} · β={p.beta.toFixed(2)} · n={p.n_observations}
                  </span>
                </div>
                <div className="w-full bg-lia-bg-tertiary rounded h-2 overflow-hidden">
                  <div
                    className="bg-lia-accent h-full transition-all"
                    style={{ width: `${barWidth}%` }}
                    aria-label={`Expected value ${barWidth}%`}
                  />
                </div>
                <p className={cn(textStyles.description, "mt-1")}>
                  {t("bandit.expectedValue")}: {(p.expected_value * 100).toFixed(2)}%
                </p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function EarlyStopTab({
  experiments,
  selected,
  onSelect,
  look,
  setLook,
  maxLooks,
  setMaxLooks,
  run,
  loading,
  result,
  t,
}: TabPropsBase & {
  experiments: Experiment[]
  selected: string | null
  onSelect: (name: string) => void
  look: number
  setLook: (n: number) => void
  maxLooks: number
  setMaxLooks: (n: number) => void
  run: () => Promise<void>
  loading: boolean
  result: EarlyStopDecision | null
}): React.ReactElement {
  const actionVariant: Record<EarlyStopDecision["action"], "info" | "warning" | "neutral"> = {
    stop_winner: "info",
    stop_futility: "warning",
    continue: "neutral",
  }
  return (
    <div className="space-y-3">
      <ExperimentSelector
        experiments={experiments}
        selected={selected}
        onSelect={onSelect}
        t={t}
      />
      <p className={textStyles.description}>{t("earlyStop.explanation")}</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <label className="flex flex-col gap-1">
          <span className={textStyles.description}>{t("earlyStop.lookNumber")}</span>
          <input
            type="number"
            min={1}
            value={look}
            onChange={(e) => setLook(Number(e.target.value))}
            className="rounded border bg-lia-bg-secondary p-2 text-lia-text-primary"
            data-testid="early-stop-look"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className={textStyles.description}>{t("earlyStop.maxLooks")}</span>
          <input
            type="number"
            min={1}
            value={maxLooks}
            onChange={(e) => setMaxLooks(Number(e.target.value))}
            className="rounded border bg-lia-bg-secondary p-2 text-lia-text-primary"
            data-testid="early-stop-max-looks"
          />
        </label>
        <div className="flex items-end">
          <Button
            onClick={() => void run()}
            disabled={loading || !selected}
            data-testid="early-stop-run"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : t("earlyStop.run")}
          </Button>
        </div>
      </div>

      {result && (
        <div
          className={cn(cardStyles.default, "p-4")}
          data-testid="early-stop-result"
          role="status"
        >
          <div className="flex items-center gap-2 mb-2">
            <Chip variant={actionVariant[result.action]}>
              {t(`earlyStop.action.${result.action}`)}
            </Chip>
            {result.winner && <span className="text-lia-text-primary font-semibold">{result.winner}</span>}
          </div>
          <p className={textStyles.description}>{result.reason}</p>
        </div>
      )}
    </div>
  )
}

function HistoryTab({
  history,
  loading,
  experimentName,
  experiments,
  onSelect,
  t,
}: TabPropsBase & {
  history: HistoryPayload | null
  loading: boolean
  experimentName: string | null
  experiments: Experiment[]
  onSelect: (name: string) => void
}): React.ReactElement {
  return (
    <div className="space-y-3">
      <ExperimentSelector
        experiments={experiments}
        selected={experimentName}
        onSelect={onSelect}
        t={t}
      />
      {loading ? (
        <Loading />
      ) : !history || history.history.length === 0 ? (
        <div className={cn(cardStyles.default, "p-6 text-center")}>
          <p className={textStyles.description}>{t("empty.history")}</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {history.history.map((entry, idx) => (
            <li
              key={`${entry.kind}-${idx}`}
              className={cn(cardStyles.default, "p-3 flex items-center justify-between gap-3 flex-wrap")}
              data-testid={`history-entry-${idx}`}
            >
              <div>
                <p className="font-medium text-lia-text-primary">{entry.variant ?? "—"}</p>
                <p className={textStyles.description}>{entry.kind}</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                {typeof entry.p_value === "number" && (
                  <Chip variant={entry.p_value < 0.01 ? "info" : "neutral"}>
                    p={entry.p_value.toFixed(4)}
                  </Chip>
                )}
                {typeof entry.mean_diff === "number" && (
                  <Chip variant="neutral">Δ={entry.mean_diff.toFixed(4)}</Chip>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ExperimentSelector({
  experiments,
  selected,
  onSelect,
  t,
}: TabPropsBase & {
  experiments: Experiment[]
  selected: string | null
  onSelect: (name: string) => void
}): React.ReactElement {
  return (
    <label className="flex flex-col gap-1">
      <span className={textStyles.description}>{t("selectExperiment")}</span>
      <select
        value={selected ?? ""}
        onChange={(e) => onSelect(e.target.value)}
        className="rounded border bg-lia-bg-secondary p-2 text-lia-text-primary max-w-md"
        data-testid="experiment-selector"
      >
        <option value="">{t("selectPlaceholder")}</option>
        {experiments.map((exp) => (
          <option key={exp.name} value={exp.name}>
            {exp.name}
          </option>
        ))}
      </select>
    </label>
  )
}

export default AIPerformancePanel
