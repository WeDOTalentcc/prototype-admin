"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { CheckCircle2, Clock, Settings, ExternalLink, Info } from "lucide-react"
import type { Integration } from "./integration-data"

interface IntegrationCardProps {
  integration: Integration
  onClick: (integration: Integration) => void
}

export function IntegrationCard({ integration, onClick }: IntegrationCardProps) {
  const isComingSoon = integration.status === "coming_soon"
  const isConnected = integration.status === "connected"

  const actionLabel = isConnected
    ? "Detalhes"
    : isComingSoon
      ? "Saiba mais"
      : "Conectar"

  const ActionIcon = isConnected ? Info : isComingSoon ? Clock : ExternalLink

  return (
    <Card
      className={cn(
        "border border-lia-border-subtle dark:border-lia-border-subtle rounded-md shadow-none transition-all duration-200 cursor-pointer",
        isComingSoon
          ? "opacity-60 hover:opacity-75"
          : "hover:border-lia-border-default dark:hover:border-lia-border-medium"
      )}
      onClick={() => onClick(integration)}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 font-semibold text-xs font-['Inter',sans-serif]",
              integration.iconBg,
              integration.iconColor
            )}
          >
            {integration.iconLetter}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <h3 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] truncate">
                  {integration.name}
                </h3>
                {integration.isActiveProvider && (
                  <Badge variant="info" className="text-[10px] px-1.5 py-0 flex-shrink-0">
                    Ativo
                  </Badge>
                )}
              </div>
              <div className="flex-shrink-0">
                {isConnected ? (
                  <Badge variant="success" className="text-[10px] gap-1 px-2 py-0.5">
                    <CheckCircle2 className="w-3 h-3" />
                    Conectado
                  </Badge>
                ) : isComingSoon ? (
                  <Badge variant="secondary" className="text-[10px] gap-1 px-2 py-0.5">
                    <Clock className="w-3 h-3" />
                    Em breve
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px] gap-1 px-2 py-0.5 text-lia-text-secondary">
                    <Settings className="w-3 h-3" />
                    Não configurado
                  </Badge>
                )}
              </div>
            </div>
            <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary font-['Open_Sans',sans-serif] mt-1 line-clamp-2">
              {integration.shortDescription}
            </p>
            <div className="mt-3">
              <Button
                size="sm"
                variant={isConnected ? "outline" : isComingSoon ? "ghost" : "default"}
                className="h-7 rounded-md text-[11px] gap-1.5 font-['Open_Sans',sans-serif] px-3"
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
    </Card>
  )
}
