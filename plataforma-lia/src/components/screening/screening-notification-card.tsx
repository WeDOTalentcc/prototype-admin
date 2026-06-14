"use client"

import React from "react"
import { Brain, ChevronRight } from "lucide-react"
import { useTranslations } from "next-intl"

interface ScreeningNotificationCardProps {
  candidateName: string
  jobTitle: string
  wsiScore?: number
  wsiBlocks?: Array<{ name: string; score: number }>
  recommendation: "aprovado" | "reprovado" | "avaliação_manual"
  source: string
  timestamp: string
  onViewDetails?: () => void
  className?: string
}

export function ScreeningNotificationCard({
  candidateName,
  jobTitle,
  wsiScore,
  wsiBlocks = [],
  recommendation,
  source,
  timestamp,
  onViewDetails,
  className = "",
}: ScreeningNotificationCardProps) {
  const t = useTranslations('screening')

  const recommendationConfig = {
    aprovado: {
      borderColor: "border-l-emerald-500",
      badgeBg: "bg-status-success/10 dark:bg-status-success/10/20",
      badgeText: "text-status-success dark:text-status-success",
      label: t('notification.approved'),
    },
    reprovado: {
      borderColor: "border-l-red-500",
      badgeBg: "bg-status-error/10 dark:bg-status-error/10/20",
      badgeText: "text-status-error dark:text-status-error",
      label: t('notification.rejected'),
    },
    avaliação_manual: {
      borderColor: "border-l-amber-500",
      badgeBg: "bg-status-warning/10 dark:bg-status-warning/10/20",
      badgeText: "text-status-warning dark:text-status-warning",
      label: t('notification.manualReview'),
    },
  }

  const config = recommendationConfig[recommendation]

  return (
    <div
      className={`rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary border-l-4 ${config.borderColor} ${className}`}
    >
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-md bg-wedo-cyan/10 dark:bg-wedo-cyan-dark/20">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <h3 className="text-sm font-semibold text-lia-text-primary">
            {t('notification.title')}
          </h3>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-lia-text-tertiary">{t('notification.candidate')}</p>
            <p className="text-sm font-medium text-lia-text-primary">
              {candidateName}
            </p>
          </div>

          <div>
            <p className="text-xs text-lia-text-tertiary">{t('notification.job')}</p>
            <p className="text-sm font-medium text-lia-text-primary">
              {jobTitle}
            </p>
          </div>

          {wsiScore !== undefined && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-lia-text-tertiary">
                  {t('notification.wsiScore')}
                </p>
                <p className="font-['Inter',sans-serif] text-sm font-semibold text-lia-text-primary">
                  {wsiScore}/100
                </p>
              </div>
              <div className="h-2 rounded-full bg-lia-interactive-active dark:bg-lia-bg-elevated overflow-hidden">
                <div
                  className={`h-full rounded-full transition-[width,height] ${
 wsiScore >= 75
                      ? "bg-status-success/10"
                      : wsiScore >= 50
                        ? "bg-status-warning/10"
                        : "bg-status-error/10"
                  }`}
                  style={{width: `${wsiScore}%`}}
                />
              </div>
            </div>
          )}

          {wsiBlocks && wsiBlocks.length > 0 && (
            <div>
              <p className="text-xs text-lia-text-tertiary mb-2">
                {t('notification.dimensions')}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {wsiBlocks.map((block, index) => (
                  <div
                    key={block.name}
                    className="p-2 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-elevated/50"
                  >
                    <p className="text-micro text-lia-text-secondary">
                      {block.name}
                    </p>
                    <p className="font-['Inter',sans-serif] text-xs font-semibold text-lia-text-primary">
                      {block.score}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="pt-2">
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-micro font-medium ${config.badgeBg} ${config.badgeText}`}
            >
              {config.label}
            </span>
          </div>

          <div className="pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <p className="text-micro text-lia-text-tertiary">
              {t('notification.autoScreeningViaWebsite')}
            </p>
          </div>
        </div>
      </div>

      {onViewDetails && (
        <div className="px-4 py-3 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-elevated/30 rounded-b-md">
          <button
            onClick={onViewDetails}
            className="flex items-center gap-1.5 text-sm font-medium text-wedo-cyan-text dark:text-wedo-cyan hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan transition-colors motion-reduce:transition-none"
          >
            {t('notification.viewDetails')}
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}
