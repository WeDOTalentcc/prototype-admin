"use client"

import React, { memo } from "react"
import { useTranslations } from "next-intl"
import {
  Search,
  ArrowLeft,
  Edit,
  ChevronRight,
  Briefcase,
  MapPin,
  Clock,
  Code,
  Building2,
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { ParsedEntities } from "@/components/search/smart-search-input"

export interface SearchResultsHeaderProps {
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  onBack: () => void
  onOpenEditQueryModal: (currentValue: string) => void
  onOpenAdvancedSearch: () => void
}

const SearchResultsHeader = memo(function SearchResultsHeader({
  lastSearchQuery,
  lastSearchEntities,
  onBack,
  onOpenEditQueryModal,
  onOpenAdvancedSearch,
}: SearchResultsHeaderProps) {
  const t = useTranslations('candidates')
  // DS v4.2.1: Tailwind tokens — sem hex hardcoded
  const pillStyles: Record<string, { pill: string; icon: string }> = {
    job_title:        { pill: 'bg-lia-bg-tertiary text-lia-text-secondary',      icon: 'text-lia-text-secondary' },
    location:         { pill: 'bg-wedo-purple/10 text-wedo-purple',   icon: 'text-wedo-purple' },
    years_experience: { pill: 'bg-status-warning/10 text-status-warning',     icon: 'text-status-warning' },
    skill:            { pill: 'bg-status-success/10 text-status-success', icon: 'text-status-success' },
    industry:         { pill: 'bg-wedo-cyan/10 text-wedo-cyan-dark',       icon: 'text-wedo-cyan-dark' },
  }

  const getIcon = (type: string, iconClass: string) => {
    switch (type) {
      case 'job_title': return <Briefcase className={`w-3 h-3 ${iconClass}`} />
      case 'location': return <MapPin className={`w-3 h-3 ${iconClass}`} />
      case 'years_experience': return <Clock className={`w-3 h-3 ${iconClass}`} />
      case 'skill': return <Code className={`w-3 h-3 ${iconClass}`} />
      case 'industry': return <Building2 className={`w-3 h-3 ${iconClass}`} />
      default: return null
    }
  }

  const renderQueryWithPills = () => {
    const query = lastSearchQuery || t('searchResultsHeader.searchPerformed')

    if (
      !lastSearchEntities ||
      (
        !lastSearchEntities.job_title &&
        !lastSearchEntities.location &&
        !lastSearchEntities.years_experience &&
        (!lastSearchEntities.skills || lastSearchEntities.skills.length === 0) &&
        !lastSearchEntities.industry
      )
    ) {
      return <span>{query}</span>
    }

    type EntitySpan = { start: number; end: number; type: string; matchedText: string }
    const spans: EntitySpan[] = []

    const isLetterOrDigit = (char: string | undefined): boolean => {
      if (!char) return false
      return /[\p{L}\p{N}]/u.test(char)
    }

    const findEntityMatches = (entityValue: string, entityType: string) => {
      if (!entityValue) return

      const escaped = entityValue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

      try {
        const regex = new RegExp(`(?<![\\p{L}\\p{N}])${escaped}(?![\\p{L}\\p{N}])`, 'giu')
        let match
        while ((match = regex.exec(query)) !== null) {
          const matchedText = query.slice(match.index, match.index + match[0].length)
          spans.push({
            start: match.index,
            end: match.index + match[0].length,
            type: entityType,
            matchedText,
          })
        }
      } catch {
        const lowerQuery = query.toLowerCase()
        const lowerEntity = entityValue.toLowerCase()
        let searchStart = 0

        while (searchStart < lowerQuery.length) {
          const idx = lowerQuery.indexOf(lowerEntity, searchStart)
          if (idx === -1) break

          const endIdx = idx + entityValue.length
          const charBefore = idx > 0 ? query[idx - 1] : undefined
          const charAfter = endIdx < query.length ? query[endIdx] : undefined

          const validStart = !isLetterOrDigit(charBefore)
          const validEnd = !isLetterOrDigit(charAfter)

          if (validStart && validEnd) {
            spans.push({
              start: idx,
              end: endIdx,
              type: entityType,
              matchedText: query.slice(idx, endIdx),
            })
          }

          searchStart = idx + 1
        }
      }
    }

    if (lastSearchEntities.job_title) findEntityMatches(lastSearchEntities.job_title, 'job_title')
    if (lastSearchEntities.location) findEntityMatches(lastSearchEntities.location, 'location')
    if (lastSearchEntities.years_experience) findEntityMatches(lastSearchEntities.years_experience, 'years_experience')
    if (lastSearchEntities.skills) lastSearchEntities.skills.forEach((s: string) => findEntityMatches(s, 'skill'))
    if (lastSearchEntities.industry) findEntityMatches(lastSearchEntities.industry, 'industry')

    if (spans.length === 0) {
      return <span>{query}</span>
    }

    spans.sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start))

    const nonOverlapping: EntitySpan[] = []
    let cursor = 0
    for (const span of spans) {
      if (span.start >= cursor) {
        nonOverlapping.push(span)
        cursor = span.end
      }
    }

    const result: React.ReactNode[] = []
    let pos = 0

    nonOverlapping.forEach((span, idx) => {
      if (span.start > pos) {
        result.push(<span key={`t${idx}`}>{query.substring(pos, span.start)}</span>)
      }

      const style = pillStyles[span.type] || { pill: 'bg-lia-interactive-active text-lia-text-secondary', icon: 'text-lia-text-tertiary' }
      result.push(
        <span
          key={`p${idx}`}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium whitespace-nowrap ${style.pill}`}
        >
          {getIcon(span.type, style.icon)}
          {span.matchedText}
        </span>
      )

      pos = span.end
    })

    if (pos < query.length) {
      result.push(<span key="tf">{query.substring(pos)}</span>)
    }

    return result
  }

  return (
    <div data-testid="search-results-header" className="flex-1 flex items-center gap-3 -mt-1 bg-lia-bg-primary rounded-xl px-3 py-2">
      {/* Botão Voltar - apenas ícone em azul negrito */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={onBack}
              className="flex items-center justify-center hover:opacity-70 transition-opacity motion-reduce:transition-none flex-shrink-0"
            >
              <ArrowLeft className="w-5 h-5 text-lia-text-secondary" strokeWidth={2.5} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="left" className="!animate-none">
            <p className="text-xs font-bold">{t('searchResultsHeader.backToSearch')}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Query da busca - PRIMEIRO */}
      <div className="flex-1 flex items-center gap-3 min-w-0">
        {/* Ícone de Search + Frase completa com pills inline */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {/* Ícone de Search para identificar prompt de busca */}
          <Search className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />

          {/* Frase completa com pills coloridos nas palavras-chave */}
          <div className="flex items-center flex-wrap text-sm text-lia-text-primary font-sans leading-loose">
            {renderQueryWithPills()}

            {/* Ações de edição - Logo após os termos de busca */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onOpenEditQueryModal(lastSearchQuery || '')}
                    className="inline-flex items-center justify-center w-6 h-6 rounded-full hover:bg-lia-interactive-active transition-[width,height] ml-1"
                  >
                    <Edit className="w-3 h-3 text-lia-text-secondary" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none">
                  <p className="text-xs font-bold">{t('searchResultsHeader.editQuery')}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <button
              onClick={onOpenAdvancedSearch}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse font-bold inline-flex items-center gap-1 transition-colors motion-reduce:transition-none ml-2 font-sans"
            >
              {t('searchResultsHeader.editFilters')}
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})
SearchResultsHeader.displayName = 'SearchResultsHeader'

export { SearchResultsHeader }
