"use client"

import { useState, useEffect } from "react"
import { KPIAlertSystem } from "@/components/alerts/kpi-alert-system"
import type { RecruiterData } from "../indicators.types"
import { Clock, CheckCircle, AlertCircle, Info } from "lucide-react"

interface AlertsTabProps {
  recruiters: RecruiterData[]
  onAlertAction: (alertId: string, action: string) => void
}

interface ProactiveHistoryItem {
  id: string
  action_type: string
  title: string
  description?: string
  status: string
  priority: string
  created_at: string
}

function useProactiveHistory() {
  const [items, setItems] = useState<ProactiveHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const r = await fetch("/api/backend-proxy/notifications/proactive-history?limit=20", { signal: AbortSignal.timeout(8000) })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const json = await r.json()
        setItems((json.data ?? []) as ProactiveHistoryItem[])
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao carregar histórico")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return { items, loading, error }
}

function statusIcon(status: string) {
  if (status === "executed" || status === "accepted")
    return <CheckCircle className="w-3 h-3 text-status-success" />
  if (status === "expired")
    return <AlertCircle className="w-3 h-3 text-status-warning" />
  return <Info className="w-3 h-3 text-lia-text-secondary" />
}

export function AlertsTab({ recruiters, onAlertAction }: AlertsTabProps) {
  const { items, loading, error } = useProactiveHistory()

  return (
    <div className="space-y-6" data-testid="alerts-tab">
      <KPIAlertSystem
        recruiterData={recruiters as unknown as Record<string, unknown>[]}
        onAlertAction={onAlertAction}
      />

      {/* B3: Histórico de alertas proativos */}
      <section className="space-y-2" data-testid="proactive-history">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
          <h3 className="text-xs font-semibold text-lia-text-primary">
            Histórico de alertas proativos
          </h3>
        </div>

        {loading && (
          <p className="text-micro text-lia-text-secondary pl-5">Carregando...</p>
        )}
        {error && (
          <p className="text-micro text-status-error pl-5">{error}</p>
        )}
        {!loading && !error && items.length === 0 && (
          <p className="text-micro text-lia-text-secondary pl-5">
            Nenhum alerta registrado ainda.
          </p>
        )}
        {!loading && items.length > 0 && (
          <ul className="space-y-1">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-start gap-1.5 text-micro text-lia-text-primary bg-lia-bg-secondary/40 rounded-lg px-2 py-1.5"
              >
                <span className="mt-0.5 shrink-0">{statusIcon(item.status)}</span>
                <span className="flex-1 min-w-0">
                  <span className="font-medium">{item.title}</span>
                  {item.description && (
                    <span className="text-lia-text-secondary ml-1">— {item.description}</span>
                  )}
                </span>
                <span className="text-lia-text-secondary shrink-0 ml-2">
                  {new Date(item.created_at).toLocaleDateString("pt-BR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
