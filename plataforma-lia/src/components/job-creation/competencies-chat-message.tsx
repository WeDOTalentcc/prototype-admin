"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { cn } from"@/lib/utils"
import { 
  Check,
  Loader2,
  PenLine,
  Brain,
  Code,
  Star,
  Building2,
  BarChart3,
  Settings
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"

export interface TechnicalSkillSuggestion {
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  weight: number
  weightJustification: string
  source: 'market_benchmark' | 'company_history' | 'platform_config'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool'
}

export interface BehavioralCompetencySuggestion {
  name: string
  weight: number
  justification: string
  weightJustification: string
  source: 'market_benchmark' | 'company_history' | 'platform_config'
}

export interface CompetenciesChatMessageProps {
  technicalSkills: TechnicalSkillSuggestion[]
  behavioralCompetencies: BehavioralCompetencySuggestion[]
  isLoading?: boolean
  onAccept: () => void
  onAdjust: () => void
}

const SOURCE_CONFIG: Record<'market_benchmark' | 'company_history' | 'platform_config', {
  icon: React.ElementType
  label: string
  className: string
}> = {
  market_benchmark: {
    icon: BarChart3,
    label: '📊 benchmark de mercado',
    className: 'text-wedo-cyan-text'
  },
  company_history: {
    icon: Building2,
    label: '🏢 histórico da empresa',
    className: 'text-wedo-purple-text dark:text-wedo-purple'
  },
  platform_config: {
    icon: Settings,
    label: '⚙️ configurações da plataforma',
    className: 'text-lia-text-secondary'
  }
}

const LEVEL_CONFIG: Record<'Básico' | 'Intermediário' | 'Avançado', {
  label: string
  className: string
  bgClassName: string
}> = {
  'Básico': {
    label: 'Básico',
    className: 'text-status-success',
    bgClassName: 'bg-status-success/10 dark:bg-status-success/30 border-status-success/30 dark:border-status-success/30'
  },
  'Intermediário': {
    label: 'Intermediário',
    className: 'text-status-warning',
    bgClassName: 'bg-status-warning/10 dark:bg-status-warning/30 border-status-warning/30 dark:border-status-warning/30'
  },
  'Avançado': {
    label: 'Avançado',
    className: 'text-status-error dark:text-status-error',
    bgClassName: 'bg-status-error/10 dark:bg-status-error/30 border-status-error/30 dark:border-status-error/30'
  }
}

function WeightStars({ weight }: { weight: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={cn("h-3 w-3",
            i <= weight 
              ?"fill-amber-400 text-status-warning" 
              :"text-lia-text-disabled"
          )}
        />
      ))}
    </div>
  )
}

function TechnicalSkillCard({ skill }: { skill: TechnicalSkillSuggestion }) {
  const levelConfig = LEVEL_CONFIG[skill.level]
  const sourceConfig = SOURCE_CONFIG[skill.source]

  return (
    <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Code className="h-3.5 w-3.5 text-lia-text-secondary flex-shrink-0" />
          <span className="text-xs font-medium truncate">{skill.name}</span>
          {skill.required && (
            <Chip variant="danger" className="text-micro h-4 px-1.5 dark:bg-status-error/30">
              Obrigatório
            </Chip>
          )}
        </div>
        <Chip 
          variant="neutral" 
          className={cn("text-micro h-4 px-1.5 border", levelConfig.bgClassName, levelConfig.className)}
        >
          {levelConfig.label}
        </Chip>
      </div>
      
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="text-micro text-lia-text-tertiary">Peso:</span>
          <WeightStars weight={skill.weight} />
        </div>
        <span className={cn("text-micro", sourceConfig.className)}>
          {sourceConfig.label}
        </span>
      </div>
      
      {skill.weightJustification && (
        <p className="text-micro text-lia-text-tertiary italic pl-1 border-l-2 border-lia-border-default">
          {skill.weightJustification}
        </p>
      )}
    </div>
  )
}

function BehavioralCompetencyCard({ competency }: { competency: BehavioralCompetencySuggestion }) {
  const sourceConfig = SOURCE_CONFIG[competency.source]

  return (
    <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Brain className="h-3.5 w-3.5 text-wedo-purple flex-shrink-0" />
          <span className="text-xs font-medium truncate">{competency.name}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-micro text-lia-text-tertiary">Peso:</span>
          <WeightStars weight={competency.weight} />
        </div>
      </div>
      
      {competency.justification && (
        <p className="text-micro text-lia-text-tertiary">
          {competency.justification}
        </p>
      )}
      
      <div className="flex items-center justify-between gap-2">
        {competency.weightJustification && (
          <p className="text-micro text-lia-text-tertiary italic pl-1 border-l-2 border-wedo-purple/30/50 flex-1">
            {competency.weightJustification}
          </p>
        )}
        <span className={cn("text-micro flex-shrink-0", sourceConfig.className)}>
          {sourceConfig.label}
        </span>
      </div>
    </div>
  )
}

export function CompetenciesChatMessage({
  technicalSkills,
  behavioralCompetencies,
  isLoading = false,
  onAccept,
  onAdjust
}: CompetenciesChatMessageProps) {
  if (isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            <span className="text-sm text-lia-text-tertiary">Analisando competências...</span>
          </div>
        </div>
      </div>
    )
  }

  if (technicalSkills.length === 0 && behavioralCompetencies.length === 0) {
    return null
  }

  return (
    <div className="flex items-start gap-3 max-w-[90%]">
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4 space-y-4">
          <p className="text-xs text-lia-text-tertiary">
            Com base em benchmark de mercado, histórico da empresa e configurações de competências, sugiro as seguintes competências com pesos atribuídos:
          </p>

          {technicalSkills.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-medium">
                <Code className="h-3.5 w-3.5 text-lia-text-secondary" />
                <span>Competências Técnicas</span>
                <Chip variant="neutral" muted className="text-micro h-4 px-1.5">
                  {technicalSkills.length}
                </Chip>
              </div>
              <div className="space-y-2 max-h-chart-sm overflow-y-auto pr-1">
                {technicalSkills.map((skill, index) => (
                  <TechnicalSkillCard key={`tech-${index}`} skill={skill} />
                ))}
              </div>
            </div>
          )}

          {behavioralCompetencies.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-medium">
                <Brain className="h-3.5 w-3.5 text-wedo-purple" />
                <span>Competências Comportamentais</span>
                <Chip variant="neutral" muted className="text-micro h-4 px-1.5">
                  {behavioralCompetencies.length}
                </Chip>
              </div>
              <div className="space-y-2 max-h-chart-sm overflow-y-auto pr-1">
                {behavioralCompetencies.map((competency, index) => (
                  <BehavioralCompetencyCard key={`behavioral-${index}`} competency={competency} />
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <Button 
              size="sm" 
              className="h-8 text-xs bg-gradient-to-r from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark hover:from-wedo-cyan-dark hover:to-wedo-cyan text-white"
              onClick={onAccept}
            >
              <Check className="h-3.5 w-3.5 mr-1.5" />
              Aceitar Sugestões
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="h-8 text-xs"
              onClick={onAdjust}
            >
              <PenLine className="h-3.5 w-3.5 mr-1.5" />
              Ajustar Competências
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CompetenciesChatMessage
