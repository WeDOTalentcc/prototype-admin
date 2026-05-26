"use client"

import { useEffect, useState } from "react"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

/**
 * Teams Tab — Dashboard
 *
 * Manifest entry: tab-dashboard → /teams-tab/dashboard (W5.1).
 *
 * Minimalist KPI dashboard inside the Teams iframe — focuses on glanceable
 * metrics. Heavy analytics/drill-down lives in the full platform; this tab
 * fires a "click_dashboard_drilldown" tracker event when the recruiter
 * tries to drill into details, which sends a proactive Adaptive Card with
 * a deep link to the full platform (consistent with vagas/candidatos UX).
 */

interface DashboardKPIs {
  active_jobs: number | null
  new_candidates_week: number | null
  stalled_pipelines: number | null
  deadlines_7d: number | null
}

const INITIAL: DashboardKPIs = {
  active_jobs: null,
  new_candidates_week: null,
  stalled_pipelines: null,
  deadlines_7d: null,
}

export default function TeamsTabDashboard() {
  const { teamsUserId, platformUserId, isAuthenticated } = useTeamsSSOContext()
  const { trackEvent } = useTeamsTabTracker({ teamsUserId, platformUserId })
  const [kpis, setKpis] = useState<DashboardKPIs>(INITIAL)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return

    const fetchKpis = async () => {
      try {
        setLoading(true)
        const token = localStorage.getItem("access_token")
        const res = await fetch("/api/backend-proxy/dashboard/kpis", {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!res.ok) {
          setKpis(INITIAL)
          setError(null)
          return
        }
        const data = await res.json()
        setKpis({
          active_jobs: data.active_jobs ?? null,
          new_candidates_week: data.new_candidates_week ?? null,
          stalled_pipelines: data.stalled_pipelines ?? null,
          deadlines_7d: data.deadlines_7d ?? null,
        })
        setError(null)
      } catch (err) {
        setKpis(INITIAL)
        setError(err instanceof Error ? err.message : "Failed to load")
      } finally {
        setLoading(false)
      }
    }

    fetchKpis()
  }, [isAuthenticated])

  const handleDrilldown = (kpi: string) => {
    trackEvent("click_dashboard_drilldown", { entityType: "kpi", entityId: kpi })
  }

  return (
    <ErrorBoundarySection>
      <div className="p-6 bg-lia-bg-primary min-h-screen">
        <header className="mb-6">
          <h1 className="text-xl font-semibold text-lia-text-primary mb-1">
            Dashboard
          </h1>
          <p className="text-sm text-lia-text-tertiary">
            Visão rápida do recrutamento. Para análises detalhadas, acesse a plataforma completa.
          </p>
        </header>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-status-warning-bg text-status-warning-text text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <KPICard
            label="Vagas ativas"
            value={kpis.active_jobs}
            loading={loading}
            onClick={() => handleDrilldown("active_jobs")}
          />
          <KPICard
            label="Novos candidatos (7d)"
            value={kpis.new_candidates_week}
            loading={loading}
            onClick={() => handleDrilldown("new_candidates_week")}
          />
          <KPICard
            label="Pipelines parados"
            value={kpis.stalled_pipelines}
            loading={loading}
            onClick={() => handleDrilldown("stalled_pipelines")}
            severity={
              kpis.stalled_pipelines && kpis.stalled_pipelines > 0
                ? "warning"
                : "default"
            }
          />
          <KPICard
            label="Deadlines em 7 dias"
            value={kpis.deadlines_7d}
            loading={loading}
            onClick={() => handleDrilldown("deadlines_7d")}
            severity={
              kpis.deadlines_7d && kpis.deadlines_7d > 0 ? "warning" : "default"
            }
          />
        </div>

        <footer className="mt-6 pt-4 border-t border-lia-border-default">
          <p className="text-xs text-lia-text-tertiary">
            Clique em qualquer card para abrir os detalhes na plataforma.
          </p>
        </footer>
      </div>
    </ErrorBoundarySection>
  )
}

interface KPICardProps {
  label: string
  value: number | null
  loading: boolean
  onClick: () => void
  severity?: "default" | "warning"
}

function KPICard({ label, value, loading, onClick, severity = "default" }: KPICardProps) {
  const severityClasses =
    severity === "warning"
      ? "border-status-warning-text bg-status-warning-bg"
      : "border-lia-border-default bg-lia-bg-secondary"

  return (
    <button
      onClick={onClick}
      className={`text-left p-4 rounded-xl border ${severityClasses} hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none`}
    >
      <p className="text-xs text-lia-text-tertiary mb-1">{label}</p>
      <p className="text-2xl font-semibold text-lia-text-primary">
        {loading ? "—" : value ?? "—"}
      </p>
    </button>
  )
}
