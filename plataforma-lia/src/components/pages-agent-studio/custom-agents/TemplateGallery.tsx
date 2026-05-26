"use client"

import React from "react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { buttonStyles, textStyles } from "@/lib/design-tokens"
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { useAgentCategories } from "@/hooks/agents/use-agent-template-catalog"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import { TemplateCard } from "./TemplateCard"
import type { AgentTemplate, AgentCategory, AgentVertical } from "./types"

// T5b UX Transformação 5: filtros verticais canonical.
// Tipo intermediário para o filtro ("all" = todos, ou um vertical específico
// ou "generic" = templates sem vertical).
type VerticalFilter = "all" | "tech" | "health" | "education" | "retail" | "generic"

const VERTICAL_FILTERS: ReadonlyArray<{ id: VerticalFilter; labelKey: string; icon: string }> = [
  { id: "all", labelKey: "verticalAll", icon: "Layers" },
  { id: "tech", labelKey: "verticalTech", icon: "Code2" },
  { id: "health", labelKey: "verticalHealth", icon: "HeartPulse" },
  { id: "education", labelKey: "verticalEducation", icon: "GraduationCap" },
  { id: "retail", labelKey: "verticalRetail", icon: "ShoppingBag" },
  { id: "generic", labelKey: "verticalGeneric", icon: "LayoutGrid" },
]

function matchesVerticalFilter(
  templateVertical: AgentVertical | undefined,
  filter: VerticalFilter,
): boolean {
  if (filter === "all") return true
  if (filter === "generic") {
    return templateVertical === null || templateVertical === undefined
  }
  return templateVertical === filter
}

interface TemplateGalleryProps {
  onTemplateSelect: (template: AgentTemplate) => void
  onCreateManual: () => void
}

export function TemplateGallery({ onTemplateSelect, onCreateManual }: TemplateGalleryProps) {
  const t = useTranslations('agents.customAgents')
  const { activeCategory, setActiveCategory } = useAgentStudioStore()
  // UX-Sprint-A QW#20 Batch 5 (audit 2026-05-21): free-text search local
  const [searchQuery, setSearchQuery] = React.useState("")
  // T5b UX Transformação 5: vertical industry filter local (não persistido em store)
  const [verticalFilter, setVerticalFilter] = React.useState<VerticalFilter>("all")

  const { templates: AGENT_TEMPLATES, isLoading: templatesLoading, error: templatesError } = useLegacyAgentTemplates()
  const { data: catalogCategories } = useAgentCategories()
  const t_cat = useTranslations("agents.customAgents.templateCategories")

  // Categorias canonical com label via i18n + fallback "Todos"
  const TEMPLATE_CATEGORIES = React.useMemo(() => ([
    { id: "all" as const, label: t_cat("all"), icon: "LayoutGrid" },
    ...catalogCategories
      .filter(c => c.is_active)
      .map(c => ({ id: c.id, label: t_cat(c.id) === c.id ? c.label_pt : t_cat(c.id), icon: c.icon ?? "LayoutGrid" })),
  ]), [catalogCategories, t_cat])

  // UX-Sprint-A QW#20: filter combinado category + search + vertical (T5b)
  const filtered = AGENT_TEMPLATES.filter((tmpl) => {
    const matchesCategory = activeCategory === "all" || tmpl.category === activeCategory
    const matchesVertical = matchesVerticalFilter(tmpl.vertical, verticalFilter)
    const q = searchQuery.trim().toLowerCase()
    const matchesSearch = !q ||
      tmpl.name.toLowerCase().includes(q) ||

      (tmpl.description || "").toLowerCase().includes(q)
    return matchesCategory && matchesVertical && matchesSearch
  })

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

      {/* UX-Sprint-A QW#20 Batch 5 (audit 2026-05-21): search input para filtrar 15 templates */}
      <div className="relative">
        <Icons.Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-disabled pointer-events-none" aria-hidden="true" />
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('searchPlaceholder')}
          aria-label={t('searchPlaceholder')}
          className="w-full pl-9 pr-3 py-2 text-sm border border-lia-border-subtle rounded-lg bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20"
        />
      </div>

      {/* Category Filters — Studio Restructure Fase 1: label visível 'Tipo:' antes das pills */}
      <span className="text-sm font-medium text-lia-text-secondary" data-testid="template-category-label">Tipo:</span>
      <div className="flex flex-wrap items-center gap-1.5" data-testid="template-category-filter">
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

      {/* T5b UX Transformação 5: Vertical Industry Filters */}
      <span className="text-sm font-medium text-lia-text-secondary" data-testid="template-vertical-label">Vertical:</span>
      <div
        className="flex flex-wrap items-center gap-1.5"
        role="group"
        aria-label={t('verticalFilterAriaLabel') || 'Filtrar templates por vertical de mercado'}
        data-testid="template-vertical-filter"
      >
        {VERTICAL_FILTERS.map((vf) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const VfIcon = ((Icons as any)[vf.icon] || Icons.Layers) as React.ComponentType<{ className?: string }>
          const isActive = verticalFilter === vf.id
          return (
            <button
              key={vf.id}
              type="button"
              onClick={() => setVerticalFilter(vf.id)}
              aria-pressed={isActive}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive
                  ? "bg-powder text-graphite border border-pebble"
                  : "bg-lia-bg-primary text-lia-text-secondary border border-lia-border-subtle hover:bg-lia-bg-tertiary"
              )}
              data-testid={`vertical-filter-${vf.id}`}
            >
              <VfIcon className="w-3.5 h-3.5" />
              {t(vf.labelKey) || vf.id}
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

      {templatesError && (
        <div className="text-center py-6" role="alert">
          <p className={cn(textStyles.caption, "text-red-600")}>
            {t('templateLoadError') || 'Erro ao carregar templates. Tente novamente.'}
          </p>
        </div>
      )}
      {!templatesError && templatesLoading && filtered.length === 0 && (
        <div className="text-center py-10" aria-busy="true">
          <Icons.Loader2 className="w-6 h-6 mx-auto text-lia-text-disabled mb-2 animate-spin" />
          <p className={textStyles.caption}>{t('templateLoading') || 'Carregando templates...'}</p>
        </div>
      )}
      {!templatesError && !templatesLoading && filtered.length === 0 && (
        <div className="text-center py-10">
          <Icons.SearchX className="w-8 h-8 mx-auto text-lia-text-disabled mb-2" />
          <p className={textStyles.caption}>{t('noTemplateInCategory')}</p>
        </div>
      )}
    </div>
  )
}
