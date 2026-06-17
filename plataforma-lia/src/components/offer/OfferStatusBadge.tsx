"use client"

/**
 * OfferStatusBadge — purely presentational badge for offer status.
 * REGRA 6: zero hooks, zero fetch — recebe status como props.
 *
 * Usado em KanbanCardStatusBadges para o estágio "offer".
 */
import { Clock, Eye, CheckCircle, XCircle, AlertCircle } from "lucide-react"

export type OfferStatusValue = "draft" | "sent" | "accepted" | "declined" | "expired" | "cancelled"

interface OfferStatusBadgeProps {
  status: OfferStatusValue
  candidateViewed?: boolean
}

const STATUS_CONFIG: Record<
  OfferStatusValue,
  { label: string; icon: React.ElementType; className: string; pulse?: boolean }
> = {
  draft:     { label: "Rascunho",      icon: Clock,        className: "bg-gray-100 text-gray-600" },
  sent:      { label: "Enviada",       icon: Clock,        className: "bg-blue-50 text-blue-600", pulse: true },
  accepted:  { label: "Aceita",        icon: CheckCircle,  className: "bg-green-50 text-green-700" },
  declined:  { label: "Recusada",      icon: XCircle,      className: "bg-red-50 text-red-600" },
  expired:   { label: "Expirada",      icon: AlertCircle,  className: "bg-amber-50 text-amber-600" },
  cancelled: { label: "Cancelada",     icon: XCircle,      className: "bg-gray-100 text-gray-500" },
}

export function OfferStatusBadge({ status, candidateViewed }: OfferStatusBadgeProps) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.draft
  const Icon = cfg.icon

  // Override label for "sent + viewed" combination
  const label = status === "sent" && candidateViewed ? "Visualizada" : cfg.label
  const icon = status === "sent" && candidateViewed ? Eye : Icon

  const EffIcon = icon

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${cfg.className}`}
      aria-label={`Status proposta: ${label}`}
    >
      {cfg.pulse && !candidateViewed ? (
        <span className="relative flex items-center">
          <EffIcon className="w-3 h-3" />
          <span className="absolute top-0 right-0 w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
        </span>
      ) : (
        <EffIcon className="w-3 h-3" />
      )}
      {label}
    </span>
  )
}
