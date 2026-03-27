"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  BarChart3, Info, Brain, Heart, Users, Target, Zap,
  Eye, BookOpen, Shield, Lightbulb, CheckCircle, AlertTriangle
} from "lucide-react"

interface BigFiveScore {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

interface BigFiveProfileProps {
  scores: BigFiveScore
  compact?: boolean
  showInsights?: boolean
}

export function BigFiveProfile({ scores, compact = false, showInsights = true }: BigFiveProfileProps) {
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null)

  // Definições detalhadas de cada dimensão - Cores WeDo Talent
  const dimensions = [
    {
      key: 'openness' as keyof BigFiveScore,
      name: 'Abertura à Experiência',
      shortName: 'Abertura',
      icon: Lightbulb,
      color: '#DC143C', // Vermelho vibrante
      colorName: 'red-600',
      bgColor: 'bg-red-50',
      barColor: 'bg-red-500',
      description: 'Pessoas criativas, apreciadoras da arte e da beleza e que gostam do novo.',
      detailedDescription: 'Disposição para novas experiências, criatividade, curiosidade intelectual e pensamento abstrato.',
      traits: {
        high: ['Criativo', 'Curioso', 'Imaginativo', 'Artístico', 'Aventureiro', 'Original'],
        low: ['Prático', 'Convencional', 'Cauteloso', 'Tradicional', 'Conservador', 'Realista']
      },
      labels: {
        low: 'Corrente, cauteloso',
        high: 'Criativo, curioso'
      },
      workBehavior: {
        high: 'Busca constantemente novas soluções, adapta-se bem a mudanças, gosta de desafios complexos',
        low: 'Prefere métodos testados, trabalha bem com processos estabelecidos, foca na execução'
      }
    },
    {
      key: 'neuroticism' as keyof BigFiveScore,
      name: 'Neuroticismo',
      shortName: 'Neuroticismo',
      icon: Shield,
      color: '#4169E1', // Azul royal
      colorName: 'gray',
      bgColor: 'bg-gray-100 dark:bg-gray-800',
      barColor: 'bg-gray-700 dark:bg-gray-300',
      description: 'Neuroticismo: tendência a sentir emoções negativas.',
      detailedDescription: 'Estabilidade emocional, resiliência ao estresse e capacidade de lidar com pressão.',
      traits: {
        high: ['Sensível', 'Emotivo', 'Ansioso', 'Intenso', 'Reativo', 'Temperamental'],
        low: ['Estável', 'Calmo', 'Resiliente', 'Equilibrado', 'Seguro', 'Tranquilo']
      },
      labels: {
        low: 'Estável, sangue frio',
        high: 'Instável, impulsivo'
      },
      workBehavior: {
        high: 'Altamente perceptivo a riscos, cuidadoso com detalhes, motivado a evitar erros',
        low: 'Mantém calma sob pressão, toma decisões equilibradas, transmite confiança'
      }
    },
    {
      key: 'extraversion' as keyof BigFiveScore,
      name: 'Extroversão',
      shortName: 'Extroversão',
      icon: Users,
      color: '#FFA500', // Laranja
      colorName: 'orange-600',
      bgColor: 'bg-orange-50',
      barColor: 'bg-orange-500',
      description: 'A extroversão é marcada pela sociabilidade, engajamento com o mundo externo.',
      detailedDescription: 'Nível de energia social, assertividade, busca por estímulos e emoções positivas.',
      traits: {
        high: ['Sociável', 'Assertivo', 'Energético', 'Entusiasmado', 'Falante', 'Otimista'],
        low: ['Reservado', 'Reflexivo', 'Quieto', 'Independente', 'Introspectivo', 'Solitário']
      },
      labels: {
        low: 'Introvertido, reservado',
        high: 'Extrovertido, energético'
      },
      workBehavior: {
        high: 'Lidera naturalmente, motiva equipes, comunica-se efetivamente, trabalha bem em grupos',
        low: 'Trabalha melhor individualmente, pensa antes de falar, foca profundamente nas tarefas'
      }
    },
    {
      key: 'agreeableness' as keyof BigFiveScore,
      name: 'Afabilidade',
      shortName: 'Afabilidade',
      icon: Heart,
      color: '#8B4B8C', // Roxo
      colorName: 'purple-600',
      bgColor: 'bg-purple-50',
      barColor: 'bg-purple-500',
      description: 'Pessoas agradáveis são outras, simpáticas. Se preocupam com a cooperação e a harmonia social e facilitam se dão bem com outras pessoas.',
      detailedDescription: 'Cooperação, confiança, empatia, altruísmo e consideração pelos outros.',
      traits: {
        high: ['Empático', 'Cooperativo', 'Confiável', 'Altruísta', 'Compreensivo', 'Compassivo'],
        low: ['Competitivo', 'Direto', 'Cético', 'Crítico', 'Objetivo', 'Racional']
      },
      labels: {
        low: 'Retraído, crítico',
        high: 'Amistoso, compassivo'
      },
      workBehavior: {
        high: 'Colabora facilmente, resolve conflitos, apoia colegas, cria ambiente positivo',
        low: 'Negocia efetivamente, toma decisões difíceis, foca em resultados, questiona ideias'
      }
    },
    {
      key: 'conscientiousness' as keyof BigFiveScore,
      name: 'Consciência',
      shortName: 'Consciência',
      icon: Target,
      color: '#2E8B57', // Verde mar
      colorName: 'green-600',
      bgColor: 'bg-green-50',
      barColor: 'bg-green-500',
      description: 'Diz respeito à forma como controlamos, conduzimos e direcionamos nossos impulsos.',
      detailedDescription: 'Organização, disciplina, responsabilidade, persistência e orientação para objetivos.',
      traits: {
        high: ['Organizado', 'Responsável', 'Disciplinado', 'Meticuloso', 'Pontual', 'Eficiente'],
        low: ['Espontâneo', 'Flexível', 'Descontraído', 'Improvisador', 'Casual', 'Adaptável']
      },
      labels: {
        low: 'Espontâneo, maleável',
        high: 'Eficiente, organizado'
      },
      workBehavior: {
        high: 'Cumpre prazos rigorosamente, planeja antecipadamente, mantém alta qualidade',
        low: 'Trabalha melhor sob pressão, adapta-se rapidamente, é mais criativo sem estrutura'
      }
    }
  ]

  const getScoreColor = (score: number, baseColor: string) => {
    // Retorna a cor diretamente (hex) com opacidade baseada no score
    const opacity = score > 70 ? '1' : score > 50 ? '0.8' : score > 30 ? '0.6' : '0.4'
    return { backgroundColor: baseColor, opacity }
  }

  const getScoreInterpretation = (score: number) => {
    if (score >= 80) return { level: 'Muito Alto', icon: CheckCircle, color: 'green' }
    if (score >= 65) return { level: 'Alto', icon: CheckCircle, color: 'blue' }
    if (score >= 35) return { level: 'Moderado', icon: Info, color: 'yellow' }
    if (score >= 20) return { level: 'Baixo', icon: AlertTriangle, color: 'orange' }
    return { level: 'Muito Baixo', icon: AlertTriangle, color: 'red' }
  }

  const generatePersonalityInsight = () => {
    const insights = []

    // Análise combinada de dimensões
    if (scores.conscientiousness > 70 && scores.openness > 70) {
      insights.push('Combina organização com criatividade - ideal para liderar projetos inovadores')
    }

    if (scores.extraversion > 70 && scores.agreeableness > 70) {
      insights.push('Liderança natural com foco em pessoas - excelente para gestão de equipes')
    }

    if (scores.conscientiousness > 70 && scores.neuroticism < 30) {
      insights.push('Alta confiabilidade e estabilidade - perfeito para posições de responsabilidade')
    }

    if (scores.openness > 70 && scores.extraversion < 40) {
      insights.push('Pensador criativo e independente - ideal para trabalho conceitual e pesquisa')
    }

    if (insights.length === 0) {
      insights.push('Perfil equilibrado com potencial para diversas funções')
    }

    return insights[0]
  }

  return (
    <TooltipProvider>
      <div className="space-y-2">
        {/* Layout compacto e criativo em duas colunas */}
        <div className="grid grid-cols-2 gap-2">
          {dimensions.map((dimension) => {
            const score = scores[dimension.key]
            const interpretation = getScoreInterpretation(score)
            const isHigh = score >= 60
            const relevantTraits = isHigh ? dimension.traits.high : dimension.traits.low

            return (
              <div key={dimension.key} className="space-y-1">
                {/* Header compacto com nome e percentual */}
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
                    {dimension.shortName}
                  </span>
                  <span className="text-xs font-bold" style={{ color: dimension.color }}>
                    {score}%
                  </span>
                </div>

                {/* Barra ultra compacta */}
                <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-500 rounded-full"
                    style={{
                      width: `${score}%`,
                      backgroundColor: dimension.color
                    }}
                  />
                </div>

                {/* Labels minimalistas */}
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {dimension.labels.low.split(',')[0]}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 text-right">
                    {dimension.labels.high.split(',')[0]}
                  </span>
                </div>

                {/* Traits compactos */}
                <div className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1">
                  {relevantTraits.slice(0, 3).join(', ')}
                </div>
              </div>
            )
          })}
        </div>

        {/* Insights super compactos */}
        {showInsights && (
          <div className="space-y-2">
            {/* Insight comportamental minimalista */}
            <div className="p-2 bg-purple-50 dark:bg-purple-900/10 rounded-md border border-purple-200 dark:border-purple-800">
              <div className="flex items-start gap-1.5">
                <Brain className="w-3 h-3 mt-0.5 flex-shrink-0 text-wedo-cyan" />
                <div className="space-y-1">
                  <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    Insight Comportamental
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                    {generatePersonalityInsight()}
                  </div>
                </div>
              </div>
            </div>

            {/* Fit para funções super compacto */}
            <div className="flex flex-wrap gap-1">
              <span className="text-xs text-gray-500 dark:text-gray-400">Fit:</span>
              {scores.conscientiousness > 70 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0 h-4" style={{ borderColor: '#B8E6D3', color: '#2E8B57' }}>
                  Gestão
                </Badge>
              )}
              {scores.openness > 70 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0 h-4" style={{ borderColor: '#F8B4B4', color: '#DC143C' }}>
                  Inovação
                </Badge>
              )}
              {scores.extraversion > 70 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0 h-4" style={{ borderColor: '#FFD700', color: '#FFA500' }}>
                  Liderança
                </Badge>
              )}
              {scores.agreeableness > 70 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0 h-4" style={{ borderColor: '#D8BFD8', color: '#8B4B8C' }}>
                  Atendimento
                </Badge>
              )}
              {scores.neuroticism < 30 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0 h-4" style={{ borderColor: '#87CEEB', color: '#4169E1' }}>
                  Alta Pressão
                </Badge>
              )}
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
