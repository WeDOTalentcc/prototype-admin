"use client"

import React, { useState } from"react"
import { 
  Lightbulb, Brain, Search, Users, Mail, Calendar, 
  FileText, Target, Zap, BarChart3, MessageSquare,
  UserCheck, Send, Plus, RefreshCcw, Building,
  Globe, Briefcase, X, ChevronRight
} from"lucide-react"
import { Button } from"@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"

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
  vagas: { label: 'Vagas', color: '' },
  candidatos: { label: 'Candidatos', color: '' },
  comunicacao: { label: 'Comunicação', color: '' },
  analytics: { label: 'Analytics', color: '' },
  automacao: { label: 'Automação', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary' }
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
      finalCommand = command.replace('esta vaga', `a vaga"${context.jobTitle}"`)
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
          className={cn("h-7 px-2 gap-1.5 text-xs font-medium transition-colors","hover:bg-lia-interactive-hover hover:text-lia-text-primary","border border-transparent hover:border-lia-border-default",
            isOpen &&"bg-lia-interactive-hover text-lia-text-secondary border-lia-border-default",
            className
          )}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          <span>Sugestões</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0 border bg-lia-bg-primary border-lia-border-default"
        align="start"
        sideOffset={8}
      >
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h3 className="text-xs font-semibold text-lia-text-primary">
                Ações Sugeridas
              </h3>
            </div>
            <Chip density="relaxed" variant="neutral" muted className="px-1.5 py-0.5">
              {filteredSuggestions.length} disponíveis
            </Chip>
          </div>
          
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveCategory(null)}
              className={cn("px-2 py-0.5 rounded-md text-xs font-medium transition-colors",
                !activeCategory 
                  ?"bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                  :"bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated"
              )}
            >
              Todas
            </button>
            {Object.entries(CATEGORY_LABELS).map(([key, { label }]) => (
              <button
                key={key}
                onClick={() => setActiveCategory(activeCategory === key ? null : key)}
                className={cn("px-2 py-0.5 rounded-md text-xs font-medium transition-colors",
                  activeCategory === key 
                    ?"bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                    :"bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated"
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
              <Lightbulb className="w-8 h-8 mx-auto mb-2 text-lia-text-tertiary" />
              <p className="text-xs text-lia-text-primary">
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
                  className="w-full p-2 rounded-xl text-left transition-colors motion-reduce:transition-none group hover:bg-lia-interactive-hover border border-transparent hover:border-lia-border-default"
                >
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0 group-hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none">
                      <Icon className="w-3.5 h-3.5 text-lia-text-secondary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-tertiary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <h4 className="text-xs font-medium truncate text-lia-text-primary">
                          {suggestion.title}
                        </h4>
                        <ChevronRight className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none" />
                      </div>
                      <p className="text-xs text-lia-text-primary line-clamp-1">
                        {suggestion.description}
                      </p>
                    </div>
                    <Chip 
                      variant="neutral" muted 
                      className={cn("text-xs px-1 py-0 flex-shrink-0", categoryInfo.color)}
                    >
                      {categoryInfo.label}
                    </Chip>
                  </div>
                </button>
              )
            })
          )}
        </div>

        <div className="p-2 border-t border-lia-border-subtle">
          <p className="text-xs text-lia-text-secondary text-center">
            Dica: Selecione candidatos ou abra uma vaga para mais ações
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
