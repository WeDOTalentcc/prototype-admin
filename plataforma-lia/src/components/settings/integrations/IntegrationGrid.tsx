"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { HubLoadingState } from "@/components/settings/_shared"
import { IntegrationCard } from "./IntegrationCard"
import type { Integration, IntegrationCategory } from "./integration-data"
import { Brain, Briefcase, Calendar, MessageCircle, Building, Code, Plug } from "lucide-react"

const categoryIcons: Record<string, React.ReactNode> = {
  all: <Plug className="w-3.5 h-3.5" />,
  ai_models: <Brain className="w-3.5 h-3.5" />,
  ats: <Briefcase className="w-3.5 h-3.5" />,
  calendar: <Calendar className="w-3.5 h-3.5" />,
  communication: <MessageCircle className="w-3.5 h-3.5" />,
  crm_hris: <Building className="w-3.5 h-3.5" />,
  mcps_apis: <Code className="w-3.5 h-3.5" />,
}

export interface IntegrationGroup {
  category: IntegrationCategory | "all"
  items: Integration[]
}

export interface IntegrationGridProps {
  groups: IntegrationGroup[]
  activeCategory: IntegrationCategory | "all"
  isLoading?: boolean
  emptyState?: React.ReactNode
  onCardClick: (integration: Integration) => void
  getCategoryLabel: (id: IntegrationCategory) => string
  searchQuery?: string
}

export function IntegrationGrid({
  groups,
  activeCategory,
  isLoading,
  emptyState,
  onCardClick,
  getCategoryLabel,
  searchQuery = "",
}: IntegrationGridProps) {
  if (isLoading) return <HubLoadingState />

  const hasItems = groups.some((g) => g.items.length > 0)
  if (!hasItems) return emptyState ?? null

  return (
    <div className="space-y-8" data-testid="integrations-list">
      {groups.map((group) => (
        <section key={group.category} data-testid={`integrations-group-${group.category}`}>
          {activeCategory === "all" && (
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lia-text-tertiary">{categoryIcons[group.category]}</span>
              <h2 className={textStyles.h3}>{getCategoryLabel(group.category as IntegrationCategory)}</h2>
              <span className={textStyles.metricSmall}>{group.items.length}</span>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {group.items.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onClick={onCardClick}
                searchQuery={searchQuery}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
