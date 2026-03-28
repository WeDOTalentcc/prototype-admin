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
  { id: 'sq2', icon: Star, question: 'Qual o score LIA médio dos resultados?', category: 'analise_busca' },
  { id: 'sq3', icon: Briefcase, question: 'Quais skills são mais comuns nesta busca?', category: 'analise_busca' },
  { id: 'sq4', icon: Clock, question: 'Qual a experiência média dos candidatos?', category: 'analise_busca' },
  { id: 'sq5', icon: TrendingUp, question: 'Quantos candidatos têm nota LIA acima de 70?', category: 'analise_busca' },
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
  
  // Comparações (3 ideias - removido fit cultural)
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
        {/* Header com busca */}
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
              placeholder="Buscar análise..."
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

        {/* Filtros de categoria */}
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

        {/* Indicador de selecionados */}
        {selectedCount > 0 && (
          <div 
            className="px-3 py-2 border-b flex items-center gap-2"
            style={{ borderColor: '#EEEEEE', backgroundColor: '#F0FAFB' }}
          >
            <UserCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            <span 
              className="text-[10px]"
              style={{ fontFamily: '"Open Sans", sans-serif' }}
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
                  className="text-[11px] leading-snug font-medium"
                  style={{ 
                    fontFamily: '"Open Sans", sans-serif',
                    color: '#2D2D2D'
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
                  Nenhuma análise encontrada
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
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
