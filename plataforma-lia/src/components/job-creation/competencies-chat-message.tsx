"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
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
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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
    className: 'text-blue-600 dark:text-blue-400'
  },
  company_history: {
    icon: Building2,
    label: '🏢 histórico da empresa',
    className: 'text-purple-600 dark:text-purple-400'
  },
  platform_config: {
    icon: Settings,
    label: '⚙️ configurações da plataforma',
    className: 'text-gray-600 dark:text-gray-400'
  }
}

const LEVEL_CONFIG: Record<'Básico' | 'Intermediário' | 'Avançado', {
  label: string
  className: string
  bgClassName: string
}> = {
  'Básico': {
    label: 'Básico',
    className: 'text-green-700 dark:text-green-400',
    bgClassName: 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800'
  },
  'Intermediário': {
    label: 'Intermediário',
    className: 'text-amber-700 dark:text-amber-400',
    bgClassName: 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800'
  },
  'Avançado': {
    label: 'Avançado',
    className: 'text-red-700 dark:text-red-400',
    bgClassName: 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800'
  }
}

function WeightStars({ weight }: { weight: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={cn(
            "h-3 w-3",
            i <= weight 
              ? "fill-amber-400 text-amber-400" 
              : "text-gray-300 dark:text-gray-600"
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
    <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Code className="h-3.5 w-3.5 text-gray-600 dark:text-gray-400 flex-shrink-0" />
          <span className="text-xs font-medium truncate">{skill.name}</span>
          {skill.required && (
            <Badge variant="outline" className="text-micro h-4 px-1.5 border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-400">
              Obrigatório
            </Badge>
          )}
        </div>
        <Badge 
          variant="outline" 
          className={cn("text-micro h-4 px-1.5 border", levelConfig.bgClassName, levelConfig.className)}
        >
          {levelConfig.label}
        </Badge>
      </div>
      
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="text-micro text-muted-foreground">Peso:</span>
          <WeightStars weight={skill.weight} />
        </div>
        <span className={cn("text-micro", sourceConfig.className)}>
          {sourceConfig.label}
        </span>
      </div>
      
      {skill.weightJustification && (
        <p className="text-micro text-muted-foreground italic pl-1 border-l-2 border-gray-300 dark:border-gray-600">
          {skill.weightJustification}
        </p>
      )}
    </div>
  )
}

function BehavioralCompetencyCard({ competency }: { competency: BehavioralCompetencySuggestion }) {
  const sourceConfig = SOURCE_CONFIG[competency.source]

  return (
    <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Brain className="h-3.5 w-3.5 text-purple-500 flex-shrink-0" />
          <span className="text-xs font-medium truncate">{competency.name}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-micro text-muted-foreground">Peso:</span>
          <WeightStars weight={competency.weight} />
        </div>
      </div>
      
      {competency.justification && (
        <p className="text-micro text-muted-foreground">
          {competency.justification}
        </p>
      )}
      
      <div className="flex items-center justify-between gap-2">
        {competency.weightJustification && (
          <p className="text-micro text-muted-foreground italic pl-1 border-l-2 border-purple-300/50 flex-1">
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
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-gray-600 dark:text-gray-400" />
            <span className="text-sm text-muted-foreground">Analisando competências...</span>
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
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 space-y-4">
          <p className="text-xs text-muted-foreground">
            Com base em benchmark de mercado, histórico da empresa e configurações de competências, sugiro as seguintes competências com pesos atribuídos:
          </p>

          {technicalSkills.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-medium">
                <Code className="h-3.5 w-3.5 text-gray-600 dark:text-gray-400" />
                <span>Competências Técnicas</span>
                <Badge variant="secondary" className="text-micro h-4 px-1.5">
                  {technicalSkills.length}
                </Badge>
              </div>
              <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                {technicalSkills.map((skill, index) => (
                  <TechnicalSkillCard key={`tech-${index}`} skill={skill} />
                ))}
              </div>
            </div>
          )}

          {behavioralCompetencies.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-medium">
                <Brain className="h-3.5 w-3.5 text-purple-500" />
                <span>Competências Comportamentais</span>
                <Badge variant="secondary" className="text-micro h-4 px-1.5">
                  {behavioralCompetencies.length}
                </Badge>
              </div>
              <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                {behavioralCompetencies.map((competency, index) => (
                  <BehavioralCompetencyCard key={`behavioral-${index}`} competency={competency} />
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <Button 
              size="sm" 
              className="h-8 text-xs bg-gradient-to-r from-gray-100 dark:from-gray-800 to-[#4FA3B4] hover:from-[#4FA3B4] hover:to-[#3E8F9F] text-white"
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
