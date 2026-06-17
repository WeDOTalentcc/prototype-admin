import React from "react"
import { AlertCircle } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

interface HubErrorStateProps {
  /** Error message. Defaults to Portuguese generic error. */
  message?: string
  /** Optional retry callback -- renders an underline "Tentar novamente" button */
  onRetry?: () => void
  /** Use "full" for hub-level full-page error, "banner" for inline banner. Default: "full" */
  variant?: "full" | "banner"
}

/**
 * Canonical error state for Settings hubs and manager components.
 *
 * Replaces the scattered {error && <div className="text-destructive">...</div>} pattern.
 * Accessible: role="alert" for immediate screenreader announcement.
 *
 * Variants:
 *   - "full"   -- centered with py-12 (used when the whole section errored)
 *   - "banner" -- compact horizontal strip with bg-status-error/10 (for inline errors)
 *
 * Usage:
 *   if (error) return <HubErrorState message={error} onRetry={refetch} />
 *   {error && <HubErrorState variant="banner" message={error} onRetry={refetch} />}
 */
export function HubErrorState({
  message = "Erro ao carregar. Tente novamente.",
  onRetry,
  variant = "full",
}: HubErrorStateProps) {
  if (variant === "banner") {
    return (
      <div
        className="flex items-center gap-2 p-2 bg-status-error/10 rounded-md text-xs text-status-error"
        role="alert"
      >
        <AlertCircle className="w-4 h-4 shrink-0" />
        <span className="flex-1">{message}</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="underline text-status-error hover:opacity-80 transition-opacity ml-2 shrink-0"
            type="button"
          >
            Tentar novamente
          </button>
        )}
      </div>
    )
  }

  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-12 text-status-error"
      role="alert"
    >
      <AlertCircle className="w-6 h-6" />
      <span className={textStyles.description}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className={textStyles.linkSubtle + " underline"}
          type="button"
        >
          Tentar novamente
        </button>
      )}
    </div>
  )
}
