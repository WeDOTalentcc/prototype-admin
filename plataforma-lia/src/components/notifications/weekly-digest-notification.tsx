"use client"

import { useState } from "react"
import { Bell, BarChart3, AlertTriangle, Shield, Lightbulb, X, MessageSquare } from "lucide-react"

export interface WeeklyDigestData {
  date: string
  pipeline: {
    activeJobs: number
    screened: number
    interviews: number
    conversionRate?: number
    conversionDelta?: number
  }
  atRiskJobs: {
    title: string
    company: string
    daysOpen: number
    targetDays: number
    severity: "critical" | "warning"
    detail?: string
  }[]
  compliance: {
    status: "ok" | "warning" | "alert"
    message: string
  }
  optimization?: {
    message: string
  }
}

interface WeeklyDigestNotificationProps {
  digest: WeeklyDigestData
  unreadCount?: number
  onViewInChat?: () => void
  onDismiss?: () => void
  onViewAll?: () => void
}

export function WeeklyDigestNotification({
  digest,
  unreadCount = 1,
  onViewInChat,
  onDismiss,
  onViewAll,
}: WeeklyDigestNotificationProps) {
  const [isOpen, setIsOpen] = useState(true)

  if (!isOpen) return null

  return (
    <div className="w-full max-w-[400px]">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl shadow-lia-lg border border-lia-border-subtle overflow-hidden">
        <div className="px-4 py-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-lia-text-primary">Notificações</h3>
          <button
            className="text-xs text-lia-text-secondary hover:text-wedo-cyan-dark font-medium transition-colors"
            onClick={onViewAll}
          >
            Marcar todas como lidas
          </button>
        </div>

        <div className="divide-y divide-lia-border-subtle">
          <div className="p-4 bg-wedo-cyan/5 hover:bg-wedo-cyan/10 transition-colors cursor-pointer border-l-[3px] border-wedo-cyan">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-wedo-cyan flex items-center justify-center shrink-0">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                  <p className="text-sm font-semibold text-lia-text-primary">Resumo Semanal Disponível</p>
                  <span className="text-[10px] text-lia-text-tertiary whitespace-nowrap ml-2">agora</span>
                </div>
                <p className="text-xs text-lia-text-secondary line-clamp-2">
                  Seu resumo semanal está pronto. {digest.atRiskJobs.length} vaga{digest.atRiskJobs.length !== 1 ? "s" : ""} precisa{digest.atRiskJobs.length !== 1 ? "m" : ""} de atenção, pipeline com {digest.pipeline.screened} triados, compliance {digest.compliance.status === "ok" ? "OK" : "com alertas"}.
                </p>
                <div className="flex items-center gap-2 mt-2">
                  {onViewInChat && (
                    <button
                      className="text-[10px] bg-wedo-cyan text-white px-2.5 py-1 rounded-md hover:bg-wedo-cyan-dark transition-colors font-medium"
                      onClick={onViewInChat}
                    >
                      Ver no Chat
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      className="text-[10px] text-lia-text-tertiary px-2.5 py-1 rounded-xl hover:bg-lia-bg-secondary transition-colors border border-lia-border-subtle"
                      onClick={onDismiss}
                    >
                      Dispensar
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {onViewAll && (
          <div className="px-4 py-2.5 border-t border-lia-border-subtle bg-lia-bg-secondary">
            <button
              className="w-full text-xs text-lia-text-secondary hover:text-wedo-cyan-dark font-medium text-center transition-colors"
              onClick={onViewAll}
            >
              Ver todas as notificações
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
