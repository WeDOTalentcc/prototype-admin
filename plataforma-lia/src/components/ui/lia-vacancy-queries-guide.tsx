"use client"

import React, { useState } from "react"
import { 
  Lightbulb, Search, Users, BarChart3,
  TrendingUp, Target, Clock,
  Brain, X, Filter, AlertCircle
} from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface VacancyQueryExample {
  id: string
  icon: React.ElementType
  question: string
  description?: string
  category: 'analise' | 'metricas' | 'funil'
}

interface LiaVacancyQueriesGuideProps {
  onSelectQuery?: (query: string) => void
  className?: string
  trigger?: 'button' | 'custom'
  isOpen?: boolean
  onOpenChange?: (open: boolean) => void
}

const CATEGORY_INFO = {
  analise: { 
    label: 'Análise', 
    icon: Brain,
  },
  metricas: { 
    label: 'Métricas', 
    icon: BarChart3,
  },
  funil: { 
    label: 'Funil', 
    icon: TrendingUp,
  }
}

const VACANCY_QUERY_EXAMPLES: VacancyQueryExample[] = [
  { id: 'vq0', icon: Search, question: 'Listar vagas abertas', category: 'analise' },
  { id: 'vq1', icon: Brain, question: 'Quais vagas precisam de atenção urgente?', category: 'analise' },
  { id: 'vq2', icon: Target, question: 'Qual vaga tem a melhor taxa de conversão?', category: 'analise' },
  { id: 'vq3', icon: TrendingUp, question: 'Comparar performance das vagas ativas', category: 'analise' },
  { id: 'vq4', icon: Brain, question: 'Sugerir melhorias para minhas vagas', category: 'analise' },
  { id: 'vq5', icon: Target, question: 'Quais vagas estão sem candidatos?', category: 'analise' },
  { id: 'vq6', icon: AlertCircle, question: 'Vagas abertas há mais de 30 dias', category: 'analise' },
  { id: 'vq17', icon: Users, question: 'Buscar candidatos para vaga de...', category: 'analise' },
  
  { id: 'vq7', icon: BarChart3, question: 'Qual é a taxa de conversão geral do funil?', category: 'metricas' },
  { id: 'vq8', icon: Clock, question: 'Tempo médio para fechar uma vaga', category: 'metricas' },
  { id: 'vq9', icon: TrendingUp, question: 'Performance das vagas este mês vs anterior', category: 'metricas' },
  { id: 'vq10', icon: BarChart3, question: 'Quantas contratações fizemos este trimestre?', category: 'metricas' },
  { id: 'vq11', icon: Clock, question: 'Quantas vagas estão atrasadas no SLA?', category: 'metricas' },
  { id: 'vq12', icon: Users, question: 'Quantas vagas temos por departamento?', category: 'metricas' },
  
  { id: 'vq13', icon: Filter, question: 'Onde está o gargalo do processo seletivo?', category: 'funil' },
  { id: 'vq14', icon: TrendingUp, question: 'Qual etapa tem maior taxa de rejeição?', category: 'funil' },
  { id: 'vq15', icon: AlertCircle, question: 'Vagas com deadline próximo', category: 'funil' },
  { id: 'vq16', icon: Clock, question: 'Performance dos últimos 30 dias', category: 'funil' }
]

export function LiaVacancyQueriesGuide({ 
  onSelectQuery, 
  className,
  trigger = 'button',
  isOpen: controlledIsOpen,
  onOpenChange
}: LiaVacancyQueriesGuideProps) {
  const [internalIsOpen, setInternalIsOpen] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen
  const setIsOpen = onOpenChange || setInternalIsOpen

  const filteredQueries = VACANCY_QUERY_EXAMPLES.filter(query => {
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
      {trigger === 'button' && (
        <PopoverTrigger asChild>
          <button
            className={cn(
              "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active hover:bg-lia-interactive-hover",
              isOpen && "bg-lia-interactive-active text-lia-text-primary",
              className
            )}
          >
            <Lightbulb className="w-2.5 h-2.5 text-lia-text-secondary" />
            <span>Mais ideias</span>
          </button>
        </PopoverTrigger>
      )}
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
              placeholder="Buscar sugestão..."
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
                  Nenhuma sugestão encontrada
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
