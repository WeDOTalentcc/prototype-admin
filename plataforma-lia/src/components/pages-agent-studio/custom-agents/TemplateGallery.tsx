"use client"

import React from "react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { buttonStyles, textStyles } from "@/lib/design-tokens"
import { AGENT_TEMPLATES, TEMPLATE_CATEGORIES } from "@/lib/agent-templates-data"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import { TemplateCard } from "./TemplateCard"
import type { AgentTemplate, AgentCategory } from "./types"

interface TemplateGalleryProps {
  onTemplateSelect: (template: AgentTemplate) => void
  onCreateManual: () => void
}

export function TemplateGallery({ onTemplateSelect, onCreateManual }: TemplateGalleryProps) {
  const t = useTranslations('agents.customAgents')
  const { activeCategory, setActiveCategory } = useAgentStudioStore()

  const filtered = activeCategory === "all"
    ? AGENT_TEMPLATES
    : AGENT_TEMPLATES.filter((t) => t.category === activeCategory)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={cn(textStyles.title, "text-lg")}>{t('startWithTemplate')}</h3>
          <p className={cn(textStyles.caption, "mt-0.5")}>
            {t('templateHint')}
          </p>
        </div>
        <button
          type="button"
          onClick={onCreateManual}
          className={cn(buttonStyles.outline, "text-xs px-3 py-1.5")}
        >
          <Icons.Plus className="w-3.5 h-3.5 mr-1.5" />
          {t('createFromScratch')}
        </button>
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-1.5">
        {TEMPLATE_CATEGORIES.map((cat) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const CatIcon = ((Icons as any)[cat.icon] || Icons.LayoutGrid) as React.ComponentType<{ className?: string }>
          const isActive = activeCategory === cat.id
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => setActiveCategory(cat.id as AgentCategory | "all")}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary"
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-secondary dark:text-lia-text-secondary"
              )}
            >
              <CatIcon className="w-3.5 h-3.5" />
              {cat.label}
            </button>
          )
        })}
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onSelect={onTemplateSelect}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-10">
          <Icons.SearchX className="w-8 h-8 mx-auto text-lia-text-disabled mb-2" />
          <p className={textStyles.caption}>{t('noTemplateInCategory')}</p>
        </div>
      )}
    </div>
  )
}
