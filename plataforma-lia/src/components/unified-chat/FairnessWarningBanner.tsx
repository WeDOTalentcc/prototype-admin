"use client"

import React from "react"
import { AlertTriangle, Shield, X } from "lucide-react"

interface FairnessWarning {
  type: "bias_detected" | "fairness_correction" | "blocked_filter"
  message: string
  severity: "info" | "warning" | "error"
}

interface Props {
  warnings: FairnessWarning[]
  onDismiss?: () => void
}

/**
 * FairnessWarningBanner — C.3 Fairness governance.
 *
 * Surfaces backend fairness flags inline in the chat.
 * Shows when JD enrichment detects bias terms or blocked filters.
 * Connected to JdEnrichmentService fairness_corrections output.
 *
 * Design: lia-* tokens, status-warning for bias, status-error for blocks.
 */
export function FairnessWarningBanner({ warnings, onDismiss }: Props) {
  if (!warnings || warnings.length === 0) return null

  const hasError = warnings.some((w) => w.severity === "error")
  const borderColor = hasError ? "border-status-error/30" : "border-status-warning/30"
  const bgColor = hasError ? "bg-status-error/5" : "bg-status-warning/5"
  const iconColor = hasError ? "text-status-error" : "text-status-warning"

  return (
    <div className={`mx-4 mb-2 px-3 py-2.5 rounded-md ${bgColor} border ${borderColor}`}>
      <div className="flex items-start gap-2">
        <Shield className={`w-4 h-4 ${iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-medium ${iconColor} font-['Open_Sans',sans-serif] mb-1`}>
            {hasError ? "Alerta de compliance" : "Correcoes de fairness aplicadas"}
          </p>
          <ul className="space-y-0.5">
            {warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-1.5">
                {w.severity === "error" ? (
                  <AlertTriangle className="w-3 h-3 text-status-error flex-shrink-0 mt-0.5" />
                ) : (
                  <span className="w-1 h-1 rounded-full bg-status-warning flex-shrink-0 mt-1.5" />
                )}
                <span className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
                  {w.message}
                </span>
              </li>
            ))}
          </ul>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-0.5 rounded text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  )
}
