import React from "react"
import { Home, Globe, CheckCircle, DollarSign, Loader2 } from "lucide-react"
import { getSourceDetails } from "@/lib/utils/source-detection"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { Candidate } from "@/components/pages/candidates/types"

type TranslateFn = (key: string, values?: Record<string, unknown>) => string

function getEnrichmentBadge(enrichmentSource: string | null | undefined, isEnriching?: boolean, t?: TranslateFn) {
  if (isEnriching) {
    return { label: t ? t('enriching') : "Enriquecendo...", className: "bg-status-warning/15 text-status-warning", icon: <Loader2 className="w-2.5 h-2.5 animate-spin" /> }
  }
  if (!enrichmentSource) return null
  const src = enrichmentSource.toLowerCase()
  if (src === 'apify') return { label: "Apify", className: "bg-wedo-orange/15 text-wedo-orange-text", icon: null }
  if (src === 'pearch') return { label: "Pearch", className: "bg-wedo-cyan/15 text-wedo-cyan-text", icon: null }
  if (src === 'local') return { label: "Local", className: "bg-stone-400/15 text-stone-500", icon: null }
  return { label: enrichmentSource, className: "bg-lia-bg-tertiary text-lia-text-secondary", icon: null }
}

export function renderSourceCell(candidate: Candidate, t?: TranslateFn): React.ReactNode {
  const hasPearchId = !!candidate.pearch_profile_id
  const sourceInfo = getSourceDetails(candidate.source, hasPearchId)
  const isLocal = sourceInfo.isLocal
  const enrichBadge = getEnrichmentBadge(candidate.enrichment_source, candidate.is_enriching, t)

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div data-testid="source-cell" className="flex items-center gap-1.5 justify-center cursor-help">
            {isLocal ? (
              <div className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-stone-400/20">
                <Home className="w-3.5 h-3.5" />
              </div>
            ) : (
              <div className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-lia-bg-tertiary dark:bg-lia-bg-elevated">
                <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
              </div>
            )}
            {enrichBadge && (
              <span className={`inline-flex items-center gap-0.5 text-micro px-1.5 py-0.5 rounded-full font-medium ${enrichBadge.className}`}>
                {enrichBadge.icon}
                {enrichBadge.label}
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="min-w-[180px] p-3 text-white bg-lia-btn-primary-bg border-transparent">
          <div className="font-semibold mb-1 flex items-center gap-1.5">
            {isLocal ? (
              <Home className="w-3.5 h-3.5" />
            ) : (
              <Globe className="w-3.5 h-3.5 text-lia-text-disabled" />
            )}
            {sourceInfo.label}
          </div>
          <div className="text-xs text-lia-text-tertiary mb-1">{sourceInfo.subtext}</div>
          {isLocal ? (
            <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-lia-border-strong text-wedo-green-text-light">
              <CheckCircle className="w-3 h-3" />
              {t ? t('noCredits') : "Sem consumo de créditos"}
            </div>
          ) : (
            <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-lia-border-strong text-status-warning">
              <DollarSign className="w-3 h-3" />
              {sourceInfo.credits || (t ? t('defaultCredits') : "1 cred + $0.01 Apify/cand")}
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
