import React from "react"
import { Loader2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

interface HubLoadingStateProps {
  /** Loading message. Defaults to Portuguese "Carregando..." */
  message?: string
  /** Use "full" for hub-level full-page loader, "inline" for card-level. Default: "full" */
  variant?: "full" | "inline"
}

/**
 * Canonical loading state for Settings hubs and manager components.
 *
 * Replaces the inline Loader2 + aria-live pattern replicated across >= 12 hubs.
 * Use this component for consistent accessible loading feedback.
 *
 * Variants:
 *   - "full"   -- centered with py-12 (used when the whole section is loading)
 *   - "inline" -- compact row (used inside a card or next to other content)
 *
 * Usage:
 *   if (isLoading) return <HubLoadingState />
 *   if (isLoading) return <HubLoadingState message={t("loadingCompanyData")} />
 *   {isLoading && <HubLoadingState variant="inline" message={t("loading")} />}
 */
export function HubLoadingState({
  message = "Carregando...",
  variant = "full",
}: HubLoadingStateProps) {
  if (variant === "inline") {
    return (
      <div
        className="flex items-center gap-2 text-lia-text-secondary"
        aria-live="polite"
        role="status"
      >
        <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none shrink-0" />
        <span className={textStyles.description}>{message}</span>
      </div>
    )
  }

  return (
    <div
      className="flex items-center justify-center gap-2 py-12 text-lia-text-secondary"
      aria-live="polite"
      role="status"
    >
      <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none shrink-0" />
      <span className={textStyles.body}>{message}</span>
    </div>
  )
}
