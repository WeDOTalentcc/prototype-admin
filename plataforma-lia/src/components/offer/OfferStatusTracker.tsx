"use client"

/**
 * OfferStatusTracker — mostra o histórico da proposta em tempo real.
 *
 * Polls GET /api/backend-proxy/offers/drafts/{offerId}/status a cada 15s.
 * Exibe timeline: Enviada → Visualizada → Aceita/Recusada.
 * Inclui OfferLinkCopyField quando link disponível.
 *
 * Rules-of-hooks: todos os hooks antes de qualquer early return.
 */
import { CheckCircle, Clock, Eye, XCircle, RefreshCw, ExternalLink } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { OfferLinkCopyField } from "./OfferLinkCopyField"

interface OfferStatus {
  offer_id: string
  status: string
  sent_at: string | null
  candidate_viewed_at: string | null
  accepted_at: string | null
  declined_at: string | null
  response_deadline: string | null
  offer_link: string | null
}

async function fetchOfferStatus(offerId: string): Promise<OfferStatus> {
  const res = await fetch(`/api/backend-proxy/offers/drafts/${offerId}/status`)
  if (!res.ok) throw new Error(`status ${res.status}`)
  return res.json()
}

function fmt(iso: string | null): string {
  if (!iso) return ""
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso))
}

interface StepProps {
  icon: React.ReactNode
  label: string
  time: string | null
  active: boolean
  variant?: "ok" | "danger" | "neutral"
}

function Step({ icon, label, time, active, variant = "neutral" }: StepProps) {
  const colors: Record<string, string> = {
    ok: "text-green-600",
    danger: "text-red-500",
    neutral: active ? "text-lia-text-primary" : "text-lia-text-secondary",
  }
  return (
    <div className={`flex items-start gap-2.5 ${active ? "opacity-100" : "opacity-40"}`}>
      <div className={`mt-0.5 ${colors[variant]}`}>{icon}</div>
      <div>
        <p className="text-xs font-medium">{label}</p>
        {time && <p className="text-[11px] text-lia-text-secondary">{time}</p>}
      </div>
    </div>
  )
}

interface OfferStatusTrackerProps {
  offerId: string
}

export function OfferStatusTracker({ offerId }: OfferStatusTrackerProps) {
  // ─── TODOS OS HOOKS ANTES DE QUALQUER EARLY RETURN ──────────────────────
  const { data, isLoading, error } = useQuery({
    queryKey: ["offer-status", offerId],
    queryFn: () => fetchOfferStatus(offerId),
    refetchInterval: 15_000,
    staleTime: 10_000,
    enabled: !!offerId,
  })

  // ─── EARLY RETURNS APÓS TODOS OS HOOKS ──────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-lia-text-secondary p-3">
        <RefreshCw className="w-3 h-3 animate-spin" />
        Carregando status…
      </div>
    )
  }

  if (error || !data) return null

  const isSent = !!data.sent_at
  const isViewed = !!data.candidate_viewed_at
  const isAccepted = data.status === "accepted"
  const isDeclined = data.status === "declined"
  const isExpired = data.status === "expired"

  return (
    <div className="space-y-3 p-3 bg-lia-surface-secondary rounded-lg border border-lia-border text-xs">
      <div className="flex items-center justify-between mb-1">
        <p className="font-semibold text-lia-text-primary text-[11px] uppercase tracking-wide">
          Acompanhamento da proposta
        </p>
        {data.response_deadline && (
          <span className="text-[10px] text-lia-text-secondary">
            Prazo: {fmt(data.response_deadline)}
          </span>
        )}
      </div>

      <div className="space-y-2.5">
        <Step
          icon={<CheckCircle className="w-4 h-4" />}
          label="Proposta enviada"
          time={fmt(data.sent_at)}
          active={isSent}
          variant={isSent ? "ok" : "neutral"}
        />
        <Step
          icon={<Eye className="w-4 h-4" />}
          label="Visualizada pelo candidato"
          time={fmt(data.candidate_viewed_at)}
          active={isViewed}
          variant={isViewed ? "ok" : "neutral"}
        />
        {isAccepted && (
          <Step
            icon={<CheckCircle className="w-4 h-4" />}
            label="Proposta aceita!"
            time={fmt(data.accepted_at)}
            active
            variant="ok"
          />
        )}
        {isDeclined && (
          <Step
            icon={<XCircle className="w-4 h-4" />}
            label="Proposta recusada"
            time={fmt(data.declined_at)}
            active
            variant="danger"
          />
        )}
        {isExpired && (
          <Step
            icon={<Clock className="w-4 h-4" />}
            label="Proposta expirada"
            time={fmt(data.response_deadline)}
            active
            variant="danger"
          />
        )}
        {!isAccepted && !isDeclined && !isExpired && isSent && (
          <Step
            icon={<Clock className="w-4 h-4" />}
            label="Aguardando resposta do candidato"
            time={null}
            active
            variant="neutral"
          />
        )}
      </div>

      {data.offer_link && (
        <div className="pt-2 border-t border-lia-border space-y-1.5">
          <div className="flex items-center gap-1 text-[11px] text-lia-text-secondary">
            <ExternalLink className="w-3 h-3" />
            Link da proposta
          </div>
          <OfferLinkCopyField link={data.offer_link} />
        </div>
      )}
    </div>
  )
}
