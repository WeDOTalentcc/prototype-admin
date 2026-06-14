"use client"

import React from "react"
import { FlaskConical, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface TastingInsight {
  module_name: string
  module_label: string
  insight_type: string
  summary: string
  cta: string
  badge: string
}

interface TastingInsightCardProps {
  insights: TastingInsight[]
}

export function TastingInsightCard({ insights }: TastingInsightCardProps) {
  if (!insights || insights.length === 0) return null

  return (
    <div className="mt-2 space-y-2">
      {insights.map((insight, i) => (
        <div
          key={`${insight.module_name}-${i}`}
          className={cn(
            "rounded-md border border-wedo-purple/20 bg-wedo-purple/5",
            "dark:border-wedo-purple/30 dark:bg-wedo-purple/10",
            "p-3 transition-colors"
          )}
        >
          <div className="flex items-start gap-2">
            <div className="mt-0.5 flex-shrink-0 rounded-md bg-wedo-purple/15 p-1">
              <FlaskConical className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-semibold bg-wedo-purple/15 text-wedo-purple-text">
                  {insight.badge}
                </span>
                <span className="text-[10px] font-medium text-lia-text-secondary">
                  {insight.module_label}
                </span>
              </div>
              <p className="text-[12px] leading-relaxed text-lia-text-primary">
                {insight.summary.replace(/\*\*/g, "")}
              </p>
              <p className="mt-1.5 flex items-center gap-1 text-[11px] text-wedo-purple-text dark:text-wedo-purple font-medium">
                <ArrowRight className="w-3 h-3" />
                {insight.cta.replace(/\*\*/g, "")}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
