"use client"

import React, { useState } from "react"
import { 
  Lightbulb, Brain, Search, Users, Mail, Calendar, 
  FileText, Target, Zap, BarChart3, MessageSquare,
  UserCheck, Send, Plus, RefreshCcw, Building,
  Globe, Briefcase, X, ChevronRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export interface PromptSuggestion {
  id: string
  icon: React.ElementType
  title: string
  description: string
  command: string
  category: 'vagas' | 'candidatos' | 'comunicacao' | 'analytics' | 'automacao'
  contextRequired?: ('job' | 'candidates' | 'none')[]
}

interface PromptSuggestionsPopoverProps {
  onSelect: (command: string) => void
  context?: {
    hasJob?: boolean
    jobTitle?: string
    selectedCandidatesCount?: number
    currentPage?: string
  }
  className?: string
}

const CATEGORY_LABELS = {
  vagas: { label: 'Vagas', color: 'bg-wedo-cyan/15 text-wedo-cyan-dark' },
  candidatos: { label: 'Candidatos', color: 'bg-green-100 text-green-700' },
  comunicacao: { label: 'Comunicação', color: 'bg-purple-100 text-purple-700' },
  analytics: { label: 'Analytics', color: 'bg-orange-100 text-orange-700' },
  automacao: { label: 'Automação', color: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50' }
}

const BASE_SUGGESTIONS: PromptSuggestion[] = [
  {
    id: 'create-job',
    icon: Plus,
    title: 'Criar nova vaga',
    description: 'Crie uma vaga com descrição detalhada e requisitos',
    command: 'Criar uma nova vaga',
    category: 'vagas',
    contextRequired: ['none']
  },
  {
    id: 'find-candidates',
    icon: Search,
    title: 'Buscar candidatos ideais',
    description: 'Encontre candidatos que combinem com o perfil da vaga',
    command: 'Buscar candidatos ideais para esta vaga',
    category: 'candidatos',
    contextRequired: ['job']
  },
  {
    id: 'generate-jd',
    icon: FileText,
    title: 'Gerar descrição de vaga',
    description: 'Crie uma JD profissional baseada nos requisitos',
    command: 'Gerar descrição profissional para a vaga',
    category: 'vagas',
    contextRequired: ['job']
  },
  {
    id: 'screening-questions',
    icon: Target,
    title: 'Criar roteiro de triagem',
    description: 'Perguntas de triagem baseadas em WSI e competências',
    command: 'Criar roteiro de triagem WSI para esta vaga',
    category: 'vagas',
    contextRequired: ['job']
  },
  {
    id: 'send-invite',
    icon: Mail,
    title: 'Enviar convite aos candidatos',
    description: 'Email personalizado para candidatos selecionados',
    command: 'Enviar convite personalizado para os candidatos selecionados',
    category: 'comunicacao',
    contextRequired: ['candidates']
  },
  {
    id: 'schedule-interview',
    icon: Calendar,
    title: 'Agendar entrevistas',
    description: 'Organize entrevistas com disponibilidade automática',
    command: 'Agendar entrevistas para os candidatos selecionados',
    category: 'comunicacao',
    contextRequired: ['candidates']
  },
  {
    id: 'whatsapp-outreach',
    icon: MessageSquare,
    title: 'Enviar WhatsApp',
    description: 'Mensagem de contato via WhatsApp',
    command: 'Enviar mensagem WhatsApp para os candidatos',
    category: 'comunicacao',
    contextRequired: ['candidates']
  },
  {
    id: 'analyze-pipeline',
    icon: BarChart3,
    title: 'Analisar funil da vaga',
    description: 'Métricas e insights sobre o processo seletivo',
    command: 'Analisar métricas do funil desta vaga',
    category: 'analytics',
    contextRequired: ['job']
  },
  {
    id: 'compare-candidates',
    icon: Users,
    title: 'Comparar candidatos',
    description: 'Análise comparativa dos candidatos selecionados',
    command: 'Comparar perfis dos candidatos selecionados',
    category: 'candidatos',
    contextRequired: ['candidates']
  },
  {
    id: 'update-status',
    icon: RefreshCcw,
    title: 'Atualizar status',
    description: 'Mover candidatos para próxima etapa',
    command: 'Atualizar status dos candidatos selecionados',
    category: 'candidatos',
    contextRequired: ['candidates']
  },
  {
    id: 'share-manager',
    icon: UserCheck,
    title: 'Compartilhar com gestor',
    description: 'Envie shortlist para aprovação do gestor',
    command: 'Compartilhar candidatos selecionados com o gestor da vaga',
    category: 'comunicacao',
    contextRequired: ['job', 'candidates']
  },
  {
    id: 'pearch-search',
    icon: Globe,
    title: 'Busca Global',
    description: 'Encontre talentos no banco global de candidatos',
    command: 'Buscar candidatos na Busca Global para esta vaga',
    category: 'candidatos',
    contextRequired: ['job']
  },
  {
    id: 'suggest-salary',
    icon: Briefcase,
    title: 'Sugerir faixa salarial',
    description: 'Benchmark de mercado para a posição',
    command: 'Sugerir faixa salarial baseada no mercado',
    category: 'analytics',
    contextRequired: ['job']
  },
  {
    id: 'interview-prep',
    icon: Target,
    title: 'Preparar roteiro de entrevista',
    description: 'Perguntas personalizadas para os candidatos',
    command: 'Preparar roteiro de entrevista para os candidatos selecionados',
    category: 'automacao',
    contextRequired: ['candidates']
  },
  {
    id: 'automate-followup',
    icon: Zap,
    title: 'Automatizar follow-up',
    description: 'Configure lembretes e acompanhamentos automáticos',
    command: 'Configurar automação de follow-up para esta vaga',
    category: 'automacao',
    contextRequired: ['job']
  }
]

export function PromptSuggestionsPopover({ 
  onSelect, 
  context = {},
  className 
}: PromptSuggestionsPopoverProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const filteredSuggestions = BASE_SUGGESTIONS.filter(suggestion => {
    if (!suggestion.contextRequired || suggestion.contextRequired.includes('none')) {
      return true
    }
    if (suggestion.contextRequired.includes('job') && !context.hasJob) {
      return false
    }
    if (suggestion.contextRequired.includes('candidates') && (!context.selectedCandidatesCount || context.selectedCandidatesCount === 0)) {
      return false
    }
    return true
  })

  const groupedSuggestions = filteredSuggestions.reduce((acc, suggestion) => {
    if (!acc[suggestion.category]) {
      acc[suggestion.category] = []
    }
    acc[suggestion.category].push(suggestion)
    return acc
  }, {} as Record<string, PromptSuggestion[]>)

  const handleSelect = (command: string) => {
    let finalCommand = command
    if (context.jobTitle) {
      finalCommand = command.replace('esta vaga', `a vaga "${context.jobTitle}"`)
    }
    onSelect(finalCommand)
    setIsOpen(false)
  }

  const displaySuggestions = activeCategory 
    ? groupedSuggestions[activeCategory] || []
    : filteredSuggestions.slice(0, 8)

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 px-2 gap-1.5 text-xs font-medium transition-all",
            "hover:bg-gray-100 dark:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50",
            "border border-transparent hover:border-gray-300 dark:border-gray-600",
            isOpen && "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600",
            className
          )}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          <span>Sugestões</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0 border"
        style={{ 
          backgroundColor: 'var(--eleven-bg-card)',
          borderColor: 'var(--eleven-border)'
        }}
        align="start"
        sideOffset={8}
      >
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h3 className="text-xs font-semibold" style={{ color: 'var(--eleven-text-primary)', fontFamily: 'Open Sans, sans-serif' }}>
                Ações Sugeridas
              </h3>
            </div>
            <Badge variant="secondary" className="text-xs px-1.5 py-0.5">
              {filteredSuggestions.length} disponíveis
            </Badge>
          </div>
          
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveCategory(null)}
              className={cn(
                "px-2 py-0.5 rounded text-xs font-medium transition-all",
                !activeCategory 
                  ? "bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              )}
            >
              Todas
            </button>
            {Object.entries(CATEGORY_LABELS).map(([key, { label }]) => (
              <button
                key={key}
                onClick={() => setActiveCategory(activeCategory === key ? null : key)}
                className={cn(
                  "px-2 py-0.5 rounded text-xs font-medium transition-all",
                  activeCategory === key 
                    ? "bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900" 
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-h-[280px] overflow-y-auto p-2 space-y-1">
          {displaySuggestions.length === 0 ? (
            <div className="py-6 text-center">
              <Lightbulb className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-xs text-gray-800 dark:text-gray-200">
                Selecione candidatos ou uma vaga para ver sugestões contextuais
              </p>
            </div>
          ) : (
            displaySuggestions.map((suggestion) => {
              const Icon = suggestion.icon
              const categoryInfo = CATEGORY_LABELS[suggestion.category]
              
              return (
                <button
                  key={suggestion.id}
                  onClick={() => handleSelect(suggestion.command)}
                  className="w-full p-2 rounded-md text-left transition-all group hover:bg-gray-50 dark:bg-gray-800/50 border border-transparent hover:border-gray-300 dark:border-gray-600"
                >
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-md bg-gray-100 flex items-center justify-center flex-shrink-0 group-hover:bg-gray-100 dark:bg-gray-800 transition-colors">
                      <Icon className="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-900 dark:group-hover:text-gray-50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <h4 className="text-xs font-medium truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                          {suggestion.title}
                        </h4>
                        <ChevronRight className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <p className="text-xs text-gray-800 dark:text-gray-200 line-clamp-1">
                        {suggestion.description}
                      </p>
                    </div>
                    <Badge 
                      variant="secondary" 
                      className={cn("text-xs px-1 py-0 flex-shrink-0", categoryInfo.color)}
                    >
                      {categoryInfo.label}
                    </Badge>
                  </div>
                </button>
              )
            })
          )}
        </div>

        <div className="p-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
            Dica: Selecione candidatos ou abra uma vaga para mais ações
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
