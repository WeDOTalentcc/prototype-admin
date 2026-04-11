"use client"

import React, { useState } from "react"
import { Lightbulb, Search, X } from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { QUERY_EXAMPLES, CATEGORY_INFO } from "@/components/unified-chat/chat-suggestions-data"

export type { QueryExample } from "@/components/unified-chat/chat-suggestions-data"

interface LiaQueriesGuideProps {
  onSelectQuery?: (query: string) => void
  className?: string
}

export function LiaQueriesGuide({ 
  onSelectQuery, 
  className 
}: LiaQueriesGuideProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredQueries = QUERY_EXAMPLES.filter(query => {
    const matchesCategory = !activeCategory || query.category === activeCategory
    const searchLower = searchTerm.toLowerCase()
    const matchesSearch = !searchTerm || 
      query.question.toLowerCase().includes(searchLower) ||
      (query.description && query.description.toLowerCase().includes(searchLower))
    return matchesCategory && matchesSearch
  })

  const handleSelectQuery = (query: string) => {
    if (onSelectQuery) {
      onSelectQuery(query)
    }
    setIsOpen(false)
    setSearchTerm('')
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary",
            "hover:bg-lia-bg-tertiary hover:text-lia-text-primary",
            isOpen && "border-lia-text-primary bg-lia-bg-tertiary text-lia-text-primary",
            className
          )}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          <span>Mais ideias</span>
        </button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-[340px] p-0 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg" 
        align="start" 
        sideOffset={6}
      >
        <div className="px-3 py-2.5 border-b">
          <div 
            className="flex items-center gap-2 px-2.5 py-2 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle"
          >
            <Search className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
            <input
              type="text"
              placeholder="Buscar consulta..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-transparent text-xs outline-none placeholder:lia-text-secondary"
             
              autoFocus
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="p-0.5 rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
                aria-label="Limpar busca"
              >
                <X className="w-3 h-3 text-lia-text-secondary" />
              </button>
            )}
          </div>
        </div>

        <div className="px-3 py-2 border-b flex gap-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveCategory(null)}
            className={cn(
 "px-2 py-1 rounded-lg text-micro font-medium transition-colors whitespace-nowrap",
              !activeCategory 
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active border border-lia-border-subtle"
            )}
           
          >
            Todas
          </button>
          {Object.entries(CATEGORY_INFO).map(([key, { label, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveCategory(activeCategory === key ? null : key)}
              className={cn(
 "inline-flex items-center gap-1 px-2 py-1 rounded-lg text-micro font-medium transition-colors whitespace-nowrap",
                activeCategory === key 
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active border border-lia-border-subtle"
              )}
             
            >
              <Icon className="w-2.5 h-2.5" />
              {label}
            </button>
          ))}
        </div>

        <ScrollArea className="h-[220px]">
          <div className="p-2 space-y-1">
            {filteredQueries.map((query) => (
              <button
                key={query.id}
                onClick={() => handleSelectQuery(query.question)}
                className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-xl group flex items-center gap-2 bg-lia-bg-secondary border border-lia-bg-tertiary hover:border-lia-border-subtle"
              >
                <div className="p-1.5 rounded-md flex-shrink-0 bg-lia-btn-primary-bg/[0.08]">
                  <query.icon className="w-3 h-3 text-lia-text-secondary" />
                </div>
                <span
                  className="text-xs leading-snug"
                 
                >
                  {query.question}
                </span>
              </button>
            ))}

            {filteredQueries.length === 0 && (
              <div className="py-8 text-center">
                <div 
                  className="w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center"
                 
                >
                  <Search className="w-3.5 h-3.5 text-lia-text-tertiary" />
                </div>
                <p
                  className="text-xs"
                 
                >
                  Nenhuma consulta encontrada
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div 
          className="px-3 py-2 border-t border-lia-border-subtle rounded-b-md bg-lia-bg-secondary"
        >
          <p
            className="text-micro text-center"
           
          >
            Clique para inserir no prompt
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
