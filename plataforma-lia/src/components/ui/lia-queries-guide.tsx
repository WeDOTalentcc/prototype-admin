"use client"

import React, { useState } from "react"
import { 
  Lightbulb, Search, Users, BarChart3, Calendar,
  TrendingUp, Target, FileText, Briefcase, Building,
  Clock, AlertCircle, CheckCircle, Star, Filter,
  MessageSquare, Globe, Zap, X, Brain
} from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface QueryExample {
  id: string
  icon: React.ElementType
  question: string
  description?: string
  category: 'metricas' | 'candidatos' | 'vagas' | 'pipeline' | 'analise' | 'previsao' | 'comparacao'
}

interface LiaQueriesGuideProps {
  onSelectQuery?: (query: string) => void
  className?: string
}

const CATEGORY_INFO = {
  metricas: { 
    label: 'Métricas', 
    icon: BarChart3,
  },
  candidatos: { 
    label: 'Candidatos', 
    icon: Users,
  },
  vagas: { 
    label: 'Vagas', 
    icon: Briefcase,
  },
  pipeline: { 
    label: 'Pipeline', 
    icon: Filter,
  },
  analise: { 
    label: 'Análise', 
    icon: Brain,
  },
  previsao: { 
    label: 'Previsões', 
    icon: TrendingUp,
  },
  comparacao: { 
    label: 'Comparar', 
    icon: Target,
  }
}

const QUERY_EXAMPLES: QueryExample[] = [
  { id: 'q1', icon: BarChart3, question: 'Quantos candidatos estão ativos no pipeline?', category: 'metricas' },
  { id: 'q2', icon: TrendingUp, question: 'Qual é a taxa de conversão do meu funil este mês?', category: 'metricas' },
  { id: 'q3', icon: Clock, question: 'Qual o tempo médio para fechar uma vaga?', category: 'metricas' },
  { id: 'q4', icon: BarChart3, question: 'Quantas contratações fizemos este trimestre?', category: 'metricas' },
  { id: 'q5', icon: AlertCircle, question: 'Quantas vagas estão atrasadas no SLA?', category: 'metricas' },
  { id: 'q6', icon: Star, question: 'Quem são os melhores candidatos para a vaga de Desenvolvedor?', category: 'candidatos' },
  { id: 'q7', icon: Users, question: 'Quantos candidatos aguardam entrevista?', category: 'candidatos' },
  { id: 'q8', icon: CheckCircle, question: 'Quais candidatos têm nota LIA acima de 80?', category: 'candidatos' },
  { id: 'q9', icon: Search, question: 'Encontre candidatos com experiência em React e Node.js', category: 'candidatos' },
  { id: 'q10', icon: Users, question: 'Quais candidatos têm perfil de liderança?', category: 'candidatos' },
  { id: 'q11', icon: Globe, question: 'Buscar candidatos na Busca Global para a vaga de Data Analyst', category: 'candidatos' },
  { id: 'q12', icon: Briefcase, question: 'Quais vagas estão abertas há mais de 30 dias?', category: 'vagas' },
  { id: 'q13', icon: AlertCircle, question: 'Quais vagas estão sem candidatos?', category: 'vagas' },
  { id: 'q14', icon: Building, question: 'Quantas vagas temos por departamento?', category: 'vagas' },
  { id: 'q15', icon: Target, question: 'Qual vaga tem a melhor taxa de conversão?', category: 'vagas' },
  { id: 'q16', icon: Clock, question: 'Quais vagas precisam de atenção urgente?', category: 'vagas' },
  { id: 'q17', icon: Filter, question: 'Quantos candidatos temos em cada etapa do funil?', category: 'pipeline' },
  { id: 'q18', icon: AlertCircle, question: 'Onde está o gargalo do meu processo seletivo?', category: 'pipeline' },
  { id: 'q19', icon: TrendingUp, question: 'Como está a progressão dos candidatos esta semana?', category: 'pipeline' },
  { id: 'q20', icon: Clock, question: 'Quais candidatos estão parados há mais de 5 dias?', category: 'pipeline' },
  { id: 'q21', icon: Brain, question: 'Quais são as principais recomendações para hoje?', category: 'analise' },
  { id: 'q22', icon: FileText, question: 'Analise o perfil de personalidade ideal para esta vaga', category: 'analise' },
  { id: 'q23', icon: MessageSquare, question: 'Resuma os feedbacks das últimas entrevistas', category: 'analise' },
  { id: 'q24', icon: FileText, question: 'Qual o perfil mais comum entre candidatos aprovados?', category: 'analise' },
  { id: 'q25', icon: Zap, question: 'Sugira melhorias para o processo de triagem', category: 'analise' },
  { id: 'q26', icon: TrendingUp, question: 'Quando devo fechar a vaga de Product Manager?', category: 'previsao' },
  { id: 'q27', icon: Calendar, question: 'Quantas contratações vamos fazer este mês?', category: 'previsao' },
  { id: 'q28', icon: Target, question: 'Qual a probabilidade de sucesso do candidato João Silva?', category: 'previsao' },
  { id: 'q29', icon: Clock, question: 'Estimativa de tempo para preencher as vagas abertas', category: 'previsao' },
  { id: 'q30', icon: Users, question: 'Compare os 3 finalistas da vaga de UX Designer', category: 'comparacao' },
  { id: 'q31', icon: BarChart3, question: 'Compare o desempenho deste mês com o anterior', category: 'comparacao' },
  { id: 'q32', icon: Building, question: 'Qual departamento contrata mais rápido?', category: 'comparacao' },
  { id: 'q33', icon: Target, question: 'Compare a qualidade dos candidatos entre fontes', category: 'comparacao' }
]

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
        {/* Header com busca */}
        <div className="px-3 py-2.5 border-b">
          <div 
            className="flex items-center gap-2 px-2.5 py-2 rounded-md bg-lia-bg-tertiary border border-lia-border-subtle"
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

        {/* Lista de consultas */}
        <ScrollArea className="h-[220px]">
          <div className="p-2 space-y-1">
            {filteredQueries.map((query) => (
              <button
                key={query.id}
                onClick={() => handleSelectQuery(query.question)}
                className="w-full px-2.5 py-2 text-left transition-colors motion-reduce:transition-none rounded-md group flex items-center gap-2 bg-lia-bg-secondary border border-lia-bg-tertiary hover:border-lia-border-subtle"
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

        {/* Footer */}
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
