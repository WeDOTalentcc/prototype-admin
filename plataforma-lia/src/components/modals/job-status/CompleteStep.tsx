"use client"

import React, { useState } from "react"
import { CheckCircle, Send, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"

interface NotificationReport {
  success_count?: number
  failure_count?: number
  details?: Array<{ candidate_id: string; success?: boolean; error?: string }>
}

interface CompleteStepProps {
  successMessage: string
  notificationReport?: NotificationReport
}

export function CompleteStep({ successMessage, notificationReport }: CompleteStepProps) {
  const [showFailures, setShowFailures] = useState(false)

  const hasReport = notificationReport && (
    (notificationReport.success_count ?? 0) > 0 || (notificationReport.failure_count ?? 0) > 0
  )

  const failedDetails = notificationReport?.details?.filter(d => !d.success && (d.error || d.success === false)) || []

  return (
    <div data-testid="complete-step" className="py-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mx-auto">
        <CheckCircle className="w-8 h-8 text-status-success" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-lia-text-primary">Processo Concluído!</h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          {successMessage}
        </p>
      </div>

      {hasReport && (
        <div className="mx-auto max-w-sm space-y-2 pt-2">
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide">
            Relatório de Envio
          </h4>
          <div className="flex items-center justify-center gap-4">
            {(notificationReport.success_count ?? 0) > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-status-success">
                <Send className="w-3.5 h-3.5" />
                <span className="font-medium">{notificationReport.success_count} enviado(s)</span>
              </div>
            )}
            {(notificationReport.failure_count ?? 0) > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-status-error">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span className="font-medium">{notificationReport.failure_count} falha(s)</span>
              </div>
            )}
          </div>

          {failedDetails.length > 0 && (
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowFailures(!showFailures)}
                className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 mx-auto"
              >
                {showFailures ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showFailures ? 'Ocultar detalhes' : 'Ver candidatos com falha'}
              </button>
              {showFailures && (
                <div className="mt-2 space-y-1 text-left bg-lia-bg-surface-secondary rounded-xl p-2 max-h-32 overflow-y-auto">
                  {failedDetails.map((detail, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-xs text-status-error">
                      <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                      <span className="break-all">
                        ID: {detail.candidate_id.slice(0, 8)}...
                        {detail.error && <span className="text-lia-text-tertiary ml-1">({detail.error})</span>}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
