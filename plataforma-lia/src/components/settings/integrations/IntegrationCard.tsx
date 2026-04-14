"use client"

import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { cn } from"@/lib/utils"
import { cardStyles, textStyles } from"@/lib/design-tokens"
import { CheckCircle2, Clock, Settings, ExternalLink, Info } from"lucide-react"
import { useTranslations } from "next-intl"
import type { Integration } from"./integration-data"

interface IntegrationCardProps {
  integration: Integration
  onClick: (integration: Integration) => void
}

export function IntegrationCard({ integration, onClick }: IntegrationCardProps) {
  const t = useTranslations("settings")
  const isComingSoon = integration.status ==="coming_soon"
  const isConnected = integration.status ==="connected"

  const actionLabel = isConnected
    ? t("integrations.card.details")
    : isComingSoon
      ? t("integrations.card.learnMore")
      : t("integrations.card.connect")

  const ActionIcon = isConnected ? Info : isComingSoon ? Clock : ExternalLink

  return (
    <div
      className={cn(
        cardStyles.interactive,"p-4",
        isComingSoon &&"opacity-60 hover:opacity-75"
      )}
      onClick={() => onClick(integration)}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn("w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0",
            textStyles.metricSmall,
            integration.iconBg,
            integration.iconColor
          )}
        >
          {integration.iconLetter}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <h3 className={cn(textStyles.h3,"truncate")}>
                {integration.name}
              </h3>
              {integration.isActiveProvider && (
                <Badge variant="info" className="text-[10px] px-1.5 py-0 flex-shrink-0">
                  {t("integrations.card.active")}
                </Badge>
              )}
            </div>
            <div className="flex-shrink-0">
              {isConnected ? (
                <Badge variant="success" className="text-[10px] gap-1 px-2 py-0.5">
                  <CheckCircle2 className="w-3 h-3" />
                  {t("integrations.card.connected")}
                </Badge>
              ) : isComingSoon ? (
                <Badge variant="secondary" className="text-[10px] gap-1 px-2 py-0.5">
                  <Clock className="w-3 h-3" />
                  {t("integrations.card.comingSoon")}
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[10px] gap-1 px-2 py-0.5 text-lia-text-secondary">
                  <Settings className="w-3 h-3" />
                  {t("integrations.card.notConfigured")}
                </Badge>
              )}
            </div>
          </div>
          <p className={cn(textStyles.description,"mt-1 line-clamp-2")}>
            {integration.shortDescription}
          </p>
          <div className="mt-3">
            <Button
              size="sm"
              variant={isConnected ?"outline" : isComingSoon ?"ghost" :"primary"}
              className="h-7 rounded-md text-[11px] gap-1.5 px-3"
              onClick={(e) => {
                e.stopPropagation()
                onClick(integration)
              }}
            >
              <ActionIcon className="w-3 h-3" />
              {actionLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
