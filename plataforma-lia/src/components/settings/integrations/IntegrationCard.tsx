"use client"

import React from "react"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { CheckCircle2, Clock, Settings, ExternalLink, Info } from "lucide-react"
import { useTranslations } from "next-intl"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { Integration } from "./integration-data"

function highlightText(text: string, query: string): React.ReactNode {
  const q = query.trim()
  if (!q) return text
  const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  const re = new RegExp(escaped, "gi")
  const parts = text.split(re)
  if (parts.length <= 1) return text
  const matches = text.match(re) ?? []
  return (
    <>
      {parts.map((part, i) => (
        <React.Fragment key={i}>
          {part}
          {i < matches.length && (
            <mark className="bg-amber-warning/20 not-italic text-inherit rounded-[2px] px-px">
              {matches[i]}
            </mark>
          )}
        </React.Fragment>
      ))}
    </>
  )
}

interface IntegrationCardProps {
  integration: Integration
  onClick: (integration: Integration) => void
  searchQuery?: string
}

export function IntegrationCard({ integration, onClick, searchQuery = "" }: IntegrationCardProps) {
  const t = useTranslations("settings")
  const isComingSoon = integration.status === "coming_soon"
  const isConnected = integration.status === "connected"

  const actionLabel = isConnected
    ? t("integrations.card.details")
    : isComingSoon
      ? t("integrations.card.learnMore")
      : t("integrations.card.connect")

  const ActionIcon = isConnected ? Info : isComingSoon ? Clock : ExternalLink

  return (
    <TooltipProvider delayDuration={400}>
      <div
        className={cn(
          cardStyles.interactive, "p-4",
          isComingSoon && "opacity-60 hover:opacity-75"
        )}
        onClick={() => onClick(integration)}
        data-testid={`integration-card-${integration.id}`}
      >
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0",
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
                <h3 className={cn(textStyles.h3, "truncate")}>
                  {highlightText(integration.name, searchQuery)}
                </h3>
                {integration.isActiveProvider && (
                  <Chip variant="info" className="text-[10px] px-1.5 py-0 flex-shrink-0">
                    {t("integrations.card.active")}
                  </Chip>
                )}
                {integration.usingSystemKey && (
                  <Chip
                    variant="neutral"
                    className="text-[10px] px-1.5 py-0 flex-shrink-0 text-lia-text-secondary"
                    title={t("integrations.card.systemKeyTooltip")}
                  >
                    {t("integrations.card.systemKey")}
                  </Chip>
                )}
              </div>
              <div className="flex-shrink-0">
                {isConnected ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span tabIndex={0} className="cursor-default">
                        <Chip variant="success" className="text-[10px] gap-1 px-2 py-0.5 pointer-events-none">
                          <CheckCircle2 className="w-3 h-3" />
                          {t("integrations.card.connected")}
                        </Chip>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-[200px] text-xs">
                      {t("integrations.card.connectedTooltip")}
                    </TooltipContent>
                  </Tooltip>
                ) : isComingSoon ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span tabIndex={0} className="cursor-default">
                        <Chip variant="neutral" muted className="text-[10px] gap-1 px-2 py-0.5 pointer-events-none">
                          <Clock className="w-3 h-3" />
                          {t("integrations.card.comingSoon")}
                        </Chip>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-[200px] text-xs">
                      {t("integrations.card.comingSoonTooltip")}
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span tabIndex={0} className="cursor-default">
                        <Chip variant="neutral" className="text-[10px] gap-1 px-2 py-0.5 text-lia-text-secondary pointer-events-none">
                          <Settings className="w-3 h-3" />
                          {t("integrations.card.notConfigured")}
                        </Chip>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-[200px] text-xs">
                      {t("integrations.card.notConfiguredTooltip")}
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>
            <p className={cn(textStyles.description, "mt-1 line-clamp-2")}>
              {highlightText(integration.shortDescription, searchQuery)}
            </p>
            <div className="mt-3">
              <Button
                size="sm"
                variant={isConnected ? "outline" : isComingSoon ? "ghost" : "primary"}
                className="h-7 rounded-md text-[11px] gap-1.5 px-3"
                onClick={(e) => {
                  e.stopPropagation()
                  onClick(integration)
                }}
                data-testid={`integration-card-action-${integration.id}`}
              >
                <ActionIcon className="w-3 h-3" />
                {actionLabel}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
