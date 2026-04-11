"use client"

import React, { useState } from "react"
import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { QUERY_EXAMPLES, CATEGORY_INFO } from "./chat-suggestions-data"

interface ChatSuggestionsPanelProps {
  isOpen: boolean
  onClose: () => void
  onSelectQuery: (query: string) => void
  mode: "sidebar" | "floating" | "fullscreen" | "minimized"
}

export function ChatSuggestionsPanel({
  isOpen,
  onClose,
  onSelectQuery,
  mode,
}: ChatSuggestionsPanelProps) {
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredQueries = QUERY_EXAMPLES.filter(query => {
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

  const handleSelectQuery = (query: string) => {
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
      "bg-lia-bg-primary border border-lia-border-subtle rounded-xl overflow-hidden",
      "animate-in slide-in-from-bottom-2 duration-200",
      panelHeight
    )}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-lia-border-subtle">
        <span className="text-xs font-medium text-lia-text-primary">Sugestões de consulta</span>
        <button
          onClick={handleClose}
          className="p-1 rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          aria-label="Fechar sugestões"
        >
          <X className="w-3.5 h-3.5 text-lia-text-secondary" />
        </button>
      </div>

      <div className="px-3 py-2 border-b border-lia-border-subtle">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle">
          <Search className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
          <input
            type="text"
            placeholder="Buscar consulta..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-transparent text-xs outline-none placeholder:text-lia-text-tertiary text-lia-text-primary"
            autoFocus
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="p-0.5 rounded-full hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              aria-label="Limpar busca"
            >
              <X className="w-3 h-3 text-lia-text-secondary" />
            </button>
          )}
        </div>
      </div>

      <div className="px-3 py-1.5 border-b border-lia-border-subtle flex gap-1 overflow-x-auto">
        <button
          onClick={() => setActiveCategory(null)}
          className={cn(
            "px-2 py-1 rounded-lg text-[10px] font-medium transition-colors whitespace-nowrap",
            !activeCategory
              ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
              : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-hover border border-lia-border-subtle"
          )}
        >
          Todas
        </button>
        {Object.entries(CATEGORY_INFO).map(([key, { label, icon: Icon }]) => (
          <button
            key={key}
            onClick={() => setActiveCategory(activeCategory === key ? null : key)}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-colors whitespace-nowrap",
              activeCategory === key
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-hover border border-lia-border-subtle"
            )}
          >
            <Icon className="w-2.5 h-2.5" />
            {label}
          </button>
        ))}
      </div>

      <ScrollArea className={cn(
        mode === "fullscreen" ? "h-[260px]" : "h-[180px]"
      )}>
        <div className="p-2 space-y-1">
          {filteredQueries.map((query) => (
            <button
              key={query.id}
              onClick={() => handleSelectQuery(query.question)}
              className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-lg group flex items-center gap-2 hover:bg-lia-bg-secondary border border-transparent hover:border-lia-border-subtle"
            >
              <div className="p-1 rounded-md flex-shrink-0 bg-lia-btn-primary-bg/[0.08]">
                <query.icon className="w-3 h-3 text-lia-text-secondary" />
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
                Nenhuma consulta encontrada
              </p>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="px-3 py-1.5 border-t border-lia-border-subtle bg-lia-bg-secondary">
        <p className="text-[10px] text-lia-text-tertiary text-center">
          Clique para inserir no prompt
        </p>
      </div>
    </div>
  )
}
