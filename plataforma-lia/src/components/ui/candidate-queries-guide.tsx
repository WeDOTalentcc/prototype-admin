"use client"

import React, { useState } from "react"
import { 
  Lightbulb, Search, Users, BarChart3, 
  TrendingUp, Target, Brain, Globe,
  Filter, MessageSquare, X, Star,
  UserCheck, Zap, RefreshCw, Eye,
  Send, Clock, Database
} from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface CandidateQueryExample {
  id: string
  icon: React.ElementType
  question: string
  description?: string
  category: 'analise' | 'refinamento' | 'sourcing' | 'acoes' | 'insights' | 'comparacao'
}

interface CandidateQueriesGuideProps {
  onSelectQuery?: (query: string) => void
  className?: string
}

const CATEGORY_INFO = {
  analise: { 
    label: 'Análise', 
    icon: BarChart3,
  },
  refinamento: { 
    label: 'Refinar', 
    icon: Filter,
  },
  sourcing: { 
    label: 'Sourcing', 
    icon: Globe,
  },
  acoes: { 
    label: 'Ações', 
    icon: Zap,
  },
  insights: { 
    label: 'Insights', 
    icon: Brain,
  },
  comparacao: { 
    label: 'Comparar', 
    icon: Target,
  }
}

const CANDIDATE_QUERY_EXAMPLES: CandidateQueryExample[] = [
  { id: 'c1', icon: Star, question: 'Comparar os 5 melhores candidatos desta busca', category: 'analise' },
  { id: 'c2', icon: Target, question: 'Qual candidato tem melhor fit para esta vaga?', category: 'analise' },
  { id: 'c3', icon: BarChart3, question: 'Analisar pontos fortes e fracos dos candidatos selecionados', category: 'analise' },
  { id: 'c4', icon: Eye, question: 'Resumir experiência dos candidatos com score > 80', category: 'analise' },
  { id: 'c5', icon: UserCheck, question: 'Qual o perfil médio dos candidatos desta busca?', category: 'analise' },
  { id: 'c31', icon: Star, question: 'Listar candidatos com nota acima de 85', category: 'analise' },
  { id: 'c32', icon: UserCheck, question: 'Qual candidato tem melhor perfil de liderança?', category: 'analise' },
  
  { id: 'c6', icon: Filter, question: 'Mostrar apenas candidatos sênior', category: 'refinamento' },
  { id: 'c7', icon: TrendingUp, question: 'Filtrar por experiência em startup', category: 'refinamento' },
  { id: 'c8', icon: Globe, question: 'Candidatos com inglês fluente', category: 'refinamento' },
  { id: 'c9', icon: Star, question: 'Apenas candidatos abertos a novas oportunidades', category: 'refinamento' },
  { id: 'c10', icon: Clock, question: 'Candidatos disponíveis para início imediato', category: 'refinamento' },
  
  { id: 'c11', icon: Users, question: 'Buscar perfis similares ao melhor candidato', category: 'sourcing' },
  { id: 'c12', icon: Globe, question: 'Expandir busca para base global', category: 'sourcing' },
  { id: 'c13', icon: Database, question: 'Buscar mais candidatos na base local', category: 'sourcing' },
  { id: 'c14', icon: Target, question: 'Encontrar candidatos de empresas referência do setor', category: 'sourcing' },
  { id: 'c15', icon: RefreshCw, question: 'Ampliar critérios de busca para mais resultados', category: 'sourcing' },
  
  { id: 'c16', icon: MessageSquare, question: 'Sugerir mensagem de abordagem para os selecionados', category: 'acoes' },
  { id: 'c17', icon: Send, question: 'Agendar entrevistas com os 3 melhores', category: 'acoes' },
  { id: 'c18', icon: Zap, question: 'Mover candidatos aprovados para próxima etapa', category: 'acoes' },
  { id: 'c19', icon: Star, question: 'Adicionar candidatos selecionados aos favoritos', category: 'acoes' },
  { id: 'c20', icon: Eye, question: 'Exportar lista de candidatos', category: 'acoes' },
  { id: 'c33', icon: MessageSquare, question: 'Enviar feedback para candidatos reprovados', category: 'acoes' },
  { id: 'c34', icon: Send, question: 'Enviar convite para os candidatos selecionados', category: 'acoes' },
  
  { id: 'c21', icon: BarChart3, question: 'Qual a média de experiência dos candidatos?', category: 'insights' },
  { id: 'c22', icon: TrendingUp, question: 'Distribuição de senioridade nesta busca', category: 'insights' },
  { id: 'c23', icon: Target, question: 'Candidatos mais difíceis de contratar (alta demanda)', category: 'insights' },
  { id: 'c24', icon: Brain, question: 'O que os candidatos têm em comum?', category: 'insights' },
  { id: 'c25', icon: Clock, question: 'Tempo médio de experiência na área', category: 'insights' },
  { id: 'c35', icon: Clock, question: 'Candidatos parados há mais de 5 dias', category: 'insights' },
  { id: 'c36', icon: TrendingUp, question: 'Como está a progressão dos candidatos?', category: 'insights' },
  { id: 'c37', icon: Users, question: 'Quantos candidatos temos em cada etapa?', category: 'insights' },
  { id: 'c38', icon: BarChart3, question: 'Quais candidatos estão aguardando ação?', category: 'insights' },
  
  { id: 'c26', icon: Users, question: 'Comparar os 3 finalistas lado a lado', category: 'comparacao' },
  { id: 'c27', icon: Target, question: 'Quem tem experiência mais relevante para a vaga?', category: 'comparacao' },
  { id: 'c28', icon: Star, question: 'Comparar aderência cultural dos candidatos', category: 'comparacao' },
  { id: 'c29', icon: BarChart3, question: 'Comparar candidatos locais vs globais', category: 'comparacao' },
  { id: 'c30', icon: TrendingUp, question: 'Ranking de candidatos por adequação', category: 'comparacao' }
]

export function CandidateQueriesGuide({
  onSelectQuery,
  className
}: CandidateQueriesGuideProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredQueries = CANDIDATE_QUERY_EXAMPLES.filter(query => {
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
 "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full border transition-[width,height] font-medium",
            "hover:border-lia-text-primary hover:bg-lia-bg-secondary",
            isOpen ? "border-lia-text-primary bg-lia-bg-secondary" : "border-lia-border-subtle",
            className
          )}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          <span>Mais ideias</span>
        </button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-[420px] p-0 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg" 
        align="start" 
        sideOffset={8}
      >
        <div className="px-5 py-4">
          <div 
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle"
          >
            <Search className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
            <input
              type="text"
              placeholder="Buscar consulta..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-transparent text-sm outline-none placeholder:lia-text-secondary"
             
              autoFocus
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="p-1 rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
                aria-label="Limpar busca"
              >
                <X className="w-3.5 h-3.5 text-lia-text-secondary" />
              </button>
            )}
          </div>
        </div>

        <div className="px-5 py-3 border-b flex gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveCategory(null)}
            className={cn(
 "px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] whitespace-nowrap",
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
 "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] whitespace-nowrap",
                activeCategory === key 
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active border border-lia-border-subtle"
              )}
             
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>

        <ScrollArea className="h-[280px]">
          <div className="p-3 space-y-2">
            {filteredQueries.map((query) => (
              <button
                key={query.id}
                onClick={() => handleSelectQuery(query.question)}
                className="w-full px-4 py-3 text-left transition-colors motion-reduce:transition-none rounded-xl group flex items-start gap-3 bg-lia-bg-secondary border border-lia-bg-tertiary hover:border-lia-border-subtle"
              >
                <div className="p-2 rounded-md flex-shrink-0 bg-lia-btn-primary-bg/[0.08]">
                  <query.icon className="w-4 h-4 text-lia-text-secondary" />
                </div>
                <span
                  className="text-sm leading-relaxed pt-1"
                 
                >
                  {query.question}
                </span>
              </button>
            ))}

            {filteredQueries.length === 0 && (
              <div className="py-12 text-center">
                <div 
                  className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
                 
                >
                  <Search className="w-5 h-5 text-lia-text-tertiary" />
                </div>
                <p
                  className="text-sm"
                 
                >
                  Nenhuma consulta encontrada
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div 
          className="px-5 py-3 border-t border-lia-border-subtle rounded-b-md bg-lia-bg-secondary"
        >
          <p
            className="text-xs text-center"
           
          >
            Clique para inserir no prompt
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
