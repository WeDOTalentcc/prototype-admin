"use client"

import React, { useState } from "react"
import { 
  Lightbulb, Search, Users, BarChart3,
  TrendingUp, Target, FileText, MapPin,
  Clock, Globe, Star, Filter,
  Briefcase, GraduationCap, DollarSign,
  Building, UserCheck, Accessibility, X, Brain, Zap
} from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface SearchQueryExample {
  id: string
  icon: React.ElementType
  question: string
  description?: string
  category: 'analise_busca' | 'candidatos_selecionados' | 'comparacoes' | 'acoes' | 'refinamento'
}

interface LiaSearchQueriesGuideProps {
  onSelectQuery?: (query: string) => void
  className?: string
  selectedCount?: number
}

const CATEGORY_INFO = {
  analise_busca: { 
    label: 'Análise', 
    icon: BarChart3,
  },
  candidatos_selecionados: { 
    label: 'Selecionados', 
    icon: UserCheck,
  },
  comparacoes: { 
    label: 'Comparar', 
    icon: Target,
  },
  acoes: { 
    label: 'Ações', 
    icon: Zap,
  },
  refinamento: { 
    label: 'Refinar', 
    icon: Filter,
  }
}

const SEARCH_QUERY_EXAMPLES: SearchQueryExample[] = [
  // Análise da Busca (14 ideias)
  { id: 'sq1', icon: Users, question: 'Quantos candidatos encontrei nesta busca?', category: 'analise_busca' },
  { id: 'sq2', icon: Star, question: 'Qual o score médio dos resultados?', category: 'analise_busca' },
  { id: 'sq3', icon: Briefcase, question: 'Quais skills são mais comuns nesta busca?', category: 'analise_busca' },
  { id: 'sq4', icon: Clock, question: 'Qual a experiência média dos candidatos?', category: 'analise_busca' },
  { id: 'sq5', icon: TrendingUp, question: 'Quantos candidatos têm nota acima de 70?', category: 'analise_busca' },
  { id: 'sq6', icon: Globe, question: 'Qual o nível de inglês dos candidatos?', category: 'analise_busca' },
  { id: 'sq7', icon: GraduationCap, question: 'Qual a origem de formação dos candidatos?', category: 'analise_busca' },
  { id: 'sq8', icon: MapPin, question: 'Onde estão localizados os candidatos?', category: 'analise_busca' },
  { id: 'sq9', icon: Users, question: 'Qual a distribuição por gênero?', category: 'analise_busca' },
  { id: 'sq10', icon: DollarSign, question: 'Qual a média de pretensão salarial?', category: 'analise_busca' },
  { id: 'sq11', icon: Building, question: 'Quantos aceitam trabalho híbrido?', category: 'analise_busca' },
  { id: 'sq12', icon: Building, question: 'Quantos aceitam somente remoto?', category: 'analise_busca' },
  { id: 'sq13', icon: Building, question: 'Quantos aceitam trabalho presencial?', category: 'analise_busca' },
  { id: 'sq14', icon: Accessibility, question: 'Análise de diversidade e inclusão (raça, PCDs)', category: 'analise_busca' },
  
  // Candidatos Selecionados (4 ideias)
  { id: 'sq15', icon: FileText, question: 'Resuma o perfil dos candidatos selecionados', category: 'candidatos_selecionados' },
  { id: 'sq16', icon: Star, question: 'Quais pontos fortes eles têm em comum?', category: 'candidatos_selecionados' },
  { id: 'sq17', icon: Target, question: 'Quais gaps de competência posso identificar?', category: 'candidatos_selecionados' },
  { id: 'sq18', icon: UserCheck, question: 'Compare os selecionados com o perfil ideal da vaga', category: 'candidatos_selecionados' },
  
  // Comparações (3 ideias - removido aderência cultural)
  { id: 'sq19', icon: Target, question: 'Compare os 3 melhores candidatos', category: 'comparacoes' },
  { id: 'sq20', icon: Clock, question: 'Quem tem mais experiência relevante?', category: 'comparacoes' },
  { id: 'sq21', icon: Briefcase, question: 'Compare as habilidades técnicas dos top candidatos', category: 'comparacoes' },
  
  // Ações Sugeridas (3 ideias - removido contatar primeiro)
  { id: 'sq22', icon: Users, question: 'Quais candidatos devo descartar desta busca?', category: 'acoes' },
  { id: 'sq23', icon: Filter, question: 'Quem precisa de triagem adicional?', category: 'acoes' },
  { id: 'sq24', icon: TrendingUp, question: 'Organize os candidatos por prioridade', category: 'acoes' },
  
  // Refinamento (3 ideias)
  { id: 'sq25', icon: Brain, question: 'Como posso melhorar esta busca?', category: 'refinamento' },
  { id: 'sq26', icon: Filter, question: 'Sugira filtros adicionais para refinar', category: 'refinamento' },
  { id: 'sq27', icon: Search, question: 'Buscar perfis similares ao top candidato', category: 'refinamento' }
]

export function LiaSearchQueriesGuide({ 
  onSelectQuery, 
  className,
  selectedCount = 0
}: LiaSearchQueriesGuideProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredQueries = SEARCH_QUERY_EXAMPLES.filter(query => {
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
        className="w-[340px] p-0 border border-lia-border-subtle bg-lia-bg-secondary rounded-xl" 
        align="start" 
        sideOffset={6}
      >
        {/* Header com busca */}
        <div className="px-3 py-2.5 border-b">
          <div 
            className="flex items-center gap-2 px-2.5 py-2 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle"
          >
            <Search className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
            <input
              type="text"
              placeholder="Buscar análise..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-transparent text-xs outline-none placeholder:lia-text-secondary"
             
              autoFocus
            />
            {searchTerm && (
              <button 
                onClick={() => setSearchTerm('')} 
                className="p-0.5 rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
              >
                <X className="w-3 h-3 text-lia-text-secondary" />
              </button>
            )}
          </div>
        </div>

        {/* Filtros de categoria */}
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

        {/* Indicador de selecionados */}
        {selectedCount > 0 && (
          <div 
            className="px-3 py-2 bg-lia-bg-secondary flex items-center gap-2"
          >
            <UserCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
            <span 
              className="text-micro"
             
            >
              {selectedCount} candidato{selectedCount > 1 ? 's' : ''} selecionado{selectedCount > 1 ? 's' : ''}
            </span>
          </div>
        )}

        {/* Lista de consultas */}
        <ScrollArea className="h-[220px]">
          <div className="p-2 space-y-1">
            {filteredQueries.map((query) => (
              <button
                key={query.id}
                onClick={() => handleSelectQuery(query.question)}
                className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-xl group flex items-center gap-2 bg-lia-bg-secondary border border-lia-bg-tertiary hover:border-lia-border-subtle"
              >
                <div 
                  className="p-1.5 rounded-md flex-shrink-0 bg-lia-btn-primary-bg/[0.08]"
                >
                  <query.icon className="w-3 h-3 text-lia-text-secondary" />
                </div>
                <span 
                  className="text-xs leading-snug font-medium"
                 
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
                  Nenhuma análise encontrada
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div 
          className="px-3 py-2 border-t border-lia-border-subtle rounded-b-xl bg-lia-bg-secondary"
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
