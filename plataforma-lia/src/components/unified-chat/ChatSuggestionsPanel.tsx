"use client"

import React, { useEffect, useState } from "react"
import { Briefcase, Clock, FileText, Plus, Search, Sparkles, TrendingUp, Users, X, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from 'next-intl'
import { ScrollArea } from "@/components/ui/scroll-area"
import { QUERY_EXAMPLES, CATEGORY_INFO } from "./chat-suggestions-data"
import {
  fetchDynamicSuggestions,
  type SuggestionCard as DynamicSuggestionCard,
} from "@/services/lia-api/suggestions-api"

interface ChatSuggestionsPanelProps {
  isOpen: boolean
  onClose: () => void
  onSelectQuery: (query: string) => void
  mode: "sidebar" | "floating" | "fullscreen" | "minimized"
}

// P1-3 (Fase B 2026-05-23): mapeia icon string do backend pra LucideIcon
// component. Default = Sparkles (fallback visual gentil quando backend
// retorna icon name desconhecido — sem quebrar a UI).
const DYNAMIC_ICON_MAP: Record<string, LucideIcon> = {
  Briefcase,
  Clock,
  FileText,
  Plus,
  Search,
  Sparkles,
  TrendingUp,
  Users,
}

function getDynamicIcon(iconName: string): LucideIcon {
  return DYNAMIC_ICON_MAP[iconName] ?? Sparkles
}

export function ChatSuggestionsPanel({
  isOpen,
  onClose,
  onSelectQuery,
  mode,
}: ChatSuggestionsPanelProps) {
  const t = useTranslations('chat.suggestionsPanel')
  const tq = useTranslations('chat.queries')
  const tc = useTranslations('chat.queryCategories')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  // P1-3 (Fase B 2026-05-23): sugestoes dinamicas via GET /lia/suggestions.
  // Fallback gracioso: se API falhar OU retornar lista vazia, panel mostra
  // SO os QUERY_EXAMPLES estaticos (comportamento pre-P1-3).
  const [dynamicSuggestions, setDynamicSuggestions] = useState<DynamicSuggestionCard[]>([])
  const [isLoadingDynamic, setIsLoadingDynamic] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    let cancelled = false
    setIsLoadingDynamic(true)
    fetchDynamicSuggestions(6)
      .then((res) => {
        if (cancelled) return
        setDynamicSuggestions(res.suggestions ?? [])
      })
      .catch((err) => {
        // Fail-quiet — panel ainda funciona com estaticos.
        // Log pra debugging mas NAO toast (UX nao precisa ver erro de panel).
        if (!cancelled) {
          // eslint-disable-next-line no-console
          console.warn("[ChatSuggestionsPanel] dynamic suggestions failed:", err)
          setDynamicSuggestions([])
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoadingDynamic(false)
      })
    return () => {
      cancelled = true
    }
  }, [isOpen])

  const translatedQueries = QUERY_EXAMPLES.map(q => ({
    ...q,
    question: tq(q.id as `q${number}`),
  }))

  const filteredQueries = translatedQueries.filter(query => {
    const matchesCategory = !activeCategory || query.category === activeCategory
    const searchLower = searchTerm.toLowerCase()
    const matchesSearch = !searchTerm ||
      query.question.toLowerCase().includes(searchLower)
    return matchesCategory && matchesSearch
  })

  const resetState = () => {
    setSearchTerm('')
    setActiveCategory(null)
  }

  /**
   * Onda 4-Fase8 P1-3 Fase 2 (2026-05-24): canonical click logging.
   * Fire-and-forget POST /lia/suggestions/click — NÃO bloqueia UX em caso
   * de erro de rede/backend. Pipeline de aprendizado consome esses eventos
   * para ranqueamento personalizado (Fase 3, próxima sprint).
   */
  const logSuggestionClick = (
    suggestionId: string,
    suggestionText: string,
    source: "panel_static" | "panel_dynamic",
  ) => {
    // Fire-and-forget: erro de rede NÃO crasha UX
    fetch("/api/backend-proxy/lia/suggestions/click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        suggestion_id: suggestionId,
        suggestion_text: suggestionText.slice(0, 500),
        suggestion_source: source,
        page_context: typeof window !== "undefined" ? window.location.pathname : null,
        chat_mode: null, // ChatSuggestionsPanel não conhece mode; UnifiedChat propaga
        click_metadata: {},
      }),
    }).catch(() => {
      // Silent fail-open per REGRA harness — logging não deve degradar UX.
      // Backend já logou via REGRA 4 fail-loud server-side.
    })
  }

  const handleSelectQuery = (
    query: string,
    opts?: { suggestionId?: string; source?: "panel_static" | "panel_dynamic" },
  ) => {
    // Onda 4-Fase8: log click antes de dispatch (fire-and-forget)
    if (opts?.suggestionId) {
      logSuggestionClick(opts.suggestionId, query, opts.source ?? "panel_static")
    }
    onSelectQuery(query)
    resetState()
    onClose()
  }

  const handleClose = () => {
    resetState()
    onClose()
  }

  if (!isOpen) return null

  const panelHeight = mode === "fullscreen" ? "max-h-[420px]" : "max-h-[320px]"

  return (
    <div className={cn(
      "absolute bottom-full left-0 right-0 z-30 mb-1",
      "bg-lia-bg-primary border border-lia-border-subtle rounded-md overflow-hidden shadow-lia-lg",
      panelHeight
    )}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-lia-border-subtle">
        <span className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide">{t('title')}</span>
        <button
          onClick={handleClose}
          className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
          aria-label={t('closeLabel')}
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="px-3 py-2 border-b border-lia-border-subtle">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
          <Search className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0" />
          <input
            type="text"
            placeholder={t('searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-transparent text-xs outline-none placeholder:text-lia-text-tertiary text-lia-text-primary"
            autoFocus
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="p-0.5 rounded-full hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              aria-label={t('clearSearch')}
            >
              <X className="w-3 h-3 text-lia-text-tertiary" />
            </button>
          )}
        </div>
      </div>

      <div className="px-3 py-1.5 border-b border-lia-border-subtle flex gap-1 overflow-x-auto">
        <button
          onClick={() => setActiveCategory(null)}
          className={cn(
            "px-2 py-1 rounded-md text-[10px] font-medium transition-colors whitespace-nowrap",
            !activeCategory
              ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
              : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-hover border border-lia-border-subtle"
          )}
        >
          {t('all')}
        </button>
        {(Object.keys(CATEGORY_INFO) as Array<'metricas' | 'candidatos' | 'vagas' | 'pipeline' | 'analise' | 'previsao' | 'comparacao'>).map((key) => {
          const { icon: Icon } = CATEGORY_INFO[key]
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(activeCategory === key ? null : key)}
              className={cn(
                "inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-colors whitespace-nowrap",
                activeCategory === key
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-hover border border-lia-border-subtle"
              )}
            >
              <Icon className="w-2.5 h-2.5" />
              {tc(key)}
            </button>
          )
        })}
      </div>

      <ScrollArea className={cn(
        mode === "fullscreen" ? "h-[260px]" : "h-[180px]"
      )}>
        <div className="p-2 space-y-1">
          {/* P1-3 (Fase B): sugestoes dinamicas baseadas no estado real
              da empresa. Aparece SO se backend retornou cards + nao filtrado
              por categoria/search (mantem context original quando user esta
              refinando). */}
          {dynamicSuggestions.length > 0 && !activeCategory && !searchTerm && (
            <div className="mb-2">
              <div className="flex items-center gap-1.5 px-1 pb-1.5">
                <Sparkles className="w-3 h-3 text-wedo-cyan" />
                <span className="text-[10px] font-medium uppercase tracking-wide text-lia-text-secondary">
                  {t('dynamicTitle')}
                </span>
              </div>
              {dynamicSuggestions.map((card) => {
                const Icon = getDynamicIcon(card.icon)
                return (
                  <button
                    key={`dyn-${card.id}`}
                    onClick={() => handleSelectQuery(card.title, { suggestionId: card.id, source: "panel_dynamic" })}
                    className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-md group flex items-center gap-2 hover:bg-lia-bg-secondary border border-transparent hover:border-wedo-cyan/30"
                  >
                    <div
                      className={cn(
                        "p-1 rounded-md flex-shrink-0",
                        card.priority === "high"
                          ? "bg-wedo-cyan/10 text-wedo-cyan-text"
                          : "bg-lia-bg-tertiary text-lia-text-tertiary",
                      )}
                    >
                      <Icon className="w-3 h-3" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="block text-xs leading-snug text-lia-text-primary truncate">
                        {card.title}
                      </span>
                      <span className="block text-[10px] leading-tight text-lia-text-tertiary truncate">
                        {card.description}
                      </span>
                    </div>
                  </button>
                )
              })}
              <div className="mt-1 mb-1 mx-1 border-t border-lia-border-subtle" />
            </div>
          )}

          {isLoadingDynamic && dynamicSuggestions.length === 0 && !activeCategory && !searchTerm && (
            <div className="mb-2 px-1 pb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-lia-text-tertiary animate-pulse" />
              <span className="text-[10px] text-lia-text-tertiary">
                {t('dynamicLoading')}
              </span>
            </div>
          )}

          {filteredQueries.map((query) => (
            <button
              key={query.id}
              onClick={() => handleSelectQuery(query.question, { suggestionId: query.id, source: "panel_static" })}
              className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-md group flex items-center gap-2 hover:bg-lia-bg-secondary border border-transparent hover:border-lia-border-subtle"
            >
              <div className="p-1 rounded-md flex-shrink-0 bg-lia-bg-tertiary">
                <query.icon className="w-3 h-3 text-lia-text-tertiary" />
              </div>
              <span className="text-xs leading-snug text-lia-text-primary">
                {query.question}
              </span>
            </button>
          ))}

          {filteredQueries.length === 0 && (
            <div className="py-6 text-center">
              <div className="w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center bg-lia-bg-secondary">
                <Search className="w-3.5 h-3.5 text-lia-text-tertiary" />
              </div>
              <p className="text-xs text-lia-text-tertiary">
                {t('noResults')}
              </p>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="px-3 py-1.5 border-t border-lia-border-subtle bg-lia-bg-secondary">
        <p className="text-[10px] text-lia-text-tertiary text-center">
          {t('hint')}
        </p>
      </div>
    </div>
  )
}
