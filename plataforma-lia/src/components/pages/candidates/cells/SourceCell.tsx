// @ts-nocheck
import React from "react"
import { Home, Globe, CheckCircle, DollarSign } from "lucide-react"
import { getSourceDetails } from "@/lib/utils/source-detection"
import type { Candidate } from "@/components/pages/candidates/types"

export function renderSourceCell(candidate: Candidate): React.ReactNode {
  const hasPearchId = !!candidate.pearch_profile_id
  const sourceInfo = getSourceDetails(candidate.source, hasPearchId)
  const isLocal = sourceInfo.isLocal

  return (
    <div className="relative group flex items-center justify-center cursor-help">
      {isLocal ? (
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-stone-400/20"
        >
          <Home className="w-3.5 h-3.5" style={{color: "var(--gray-500)"}} />
        </div>
      ) : (
        <div className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-gray-100 dark:bg-lia-bg-elevated">
          <Globe className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-secondary" />
        </div>
      )}
      {/* Tooltip dinâmico com informações de créditos */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
        <div className="px-3 py-2 rounded-md text-xs min-w-[180px] text-white bg-gray-900">
          <div className="font-semibold mb-1 flex items-center gap-1.5">
            {isLocal ? (
              <Home className="w-3.5 h-3.5" style={{color: "var(--wedo-orange)"}} />
            ) : (
              <Globe className="w-3.5 h-3.5 text-lia-text-disabled" />
            )}
            {sourceInfo.label}
          </div>
          <div className="text-xs text-lia-text-tertiary mb-1">{sourceInfo.subtext}</div>
          {isLocal ? (
            <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700 text-wedo-green-light">
              <CheckCircle className="w-3 h-3" />
              Sem consumo de créditos
            </div>
          ) : (
            <div
              className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700 text-status-warning"
            >
              <DollarSign className="w-3 h-3" />
              {sourceInfo.credits || "5-7 créditos/candidato"}
            </div>
          )}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
  )
}
