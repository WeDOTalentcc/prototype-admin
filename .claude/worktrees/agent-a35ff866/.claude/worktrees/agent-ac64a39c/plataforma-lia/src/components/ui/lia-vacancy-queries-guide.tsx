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
              "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full border transition-all",
              "hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50",
              isOpen && "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50",
              className
            )}
            style={{ 
              borderColor: isOpen ? '#111827' : '#E0E0E0', 
              fontFamily: '"Open Sans", sans-serif', 
              fontWeight: 500
            }}
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Mais ideias</span>
          </button>
        </PopoverTrigger>
      )}
      <PopoverContent 
        className="w-[340px] p-0 border-0" 
        align="start" 
        sideOffset={6}
        style={{ 
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06)',
          border: '1px solid #E8E8E8'
        }}
      >
        <div className="px-3 py-2.5 border-b" style={{ borderColor: '#EEEEEE' }}>
          <div 
            className="flex items-center gap-2 px-2.5 py-2 rounded-md"
            style={{ 
              backgroundColor: '#F8F8F8',
              border: '1px solid #E8E8E8'
            }}
          >
            <Search className="w-3.5 h-3.5 text-[#999999] flex-shrink-0" />
            <input
              type="text"
              placeholder="Buscar sugestão..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-transparent text-[11px] outline-none placeholder:text-[#AAAAAA]"
              style={{ fontFamily: '"Open Sans", sans-serif', color: '#2D2D2D' }}
              autoFocus
            />
            {searchTerm && (
              <button 
                onClick={() => setSearchTerm('')} 
                className="p-0.5 rounded-full hover:bg-[#EEEEEE] transition-colors"
              >
                <X className="w-3 h-3 text-[#999999]" />
              </button>
            )}
          </div>
        </div>

        <div className="px-3 py-2 border-b flex gap-1.5 overflow-x-auto" style={{ borderColor: '#EEEEEE' }}>
          <button
            onClick={() => setActiveCategory(null)}
            className={cn(
              "px-2 py-1 rounded-full text-[10px] font-medium transition-all whitespace-nowrap",
              !activeCategory 
                ? "bg-gray-900 dark:bg-gray-50 text-white" 
                : "bg-[#F5F5F5] text-[#666666] hover:bg-[#EEEEEE] border border-[#E8E8E8]"
            )}
            style={{ fontFamily: '"Open Sans", sans-serif' }}
          >
            Todas
          </button>
          {Object.entries(CATEGORY_INFO).map(([key, { label, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveCategory(activeCategory === key ? null : key)}
              className={cn(
                "inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium transition-all whitespace-nowrap",
                activeCategory === key 
                  ? "bg-gray-900 dark:bg-gray-50 text-white" 
                  : "bg-[#F5F5F5] text-[#666666] hover:bg-[#EEEEEE] border border-[#E8E8E8]"
              )}
              style={{ fontFamily: '"Open Sans", sans-serif' }}
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
                className="w-full px-2.5 py-2 text-left transition-all rounded-md group flex items-center gap-2"
                style={{ 
                  backgroundColor: '#FAFAFA',
                  border: '1px solid #EEEEEE'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#F0FAFB'
                  e.currentTarget.style.borderColor = '#D1D5DB'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#FAFAFA'
                  e.currentTarget.style.borderColor = '#EEEEEE'
                }}
              >
                <div 
                  className="p-1.5 rounded-md flex-shrink-0"
                  className="bg-gray-900/[0.08]"
                >
                  <query.icon className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                </div>
                <span 
                  className="text-[11px] leading-snug"
                  style={{ 
                    fontFamily: '"Open Sans", sans-serif',
                    color: '#444444'
                  }}
                >
                  {query.question}
                </span>
              </button>
            ))}

            {filteredQueries.length === 0 && (
              <div className="py-8 text-center">
                <div 
                  className="w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: '#F5F5F5' }}
                >
                  <Search className="w-3.5 h-3.5 text-[#CCCCCC]" />
                </div>
                <p 
                  className="text-[11px]"
                  style={{ 
                    fontFamily: '"Open Sans", sans-serif',
                    color: '#999999'
                  }}
                >
                  Nenhuma sugestão encontrada
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div 
          className="px-3 py-2 border-t rounded-b-xl"
          style={{ 
            borderColor: '#EEEEEE',
            backgroundColor: '#FAFAFA'
          }}
        >
          <p 
            className="text-[10px] text-center"
            style={{ 
              fontFamily: '"Open Sans", sans-serif',
              color: '#999999'
            }}
          >
            Clique para inserir no prompt
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
