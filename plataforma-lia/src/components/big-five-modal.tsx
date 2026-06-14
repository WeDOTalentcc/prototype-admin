"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from"@/components/ui/dialog"
import { TrendingUp, TrendingDown, Minus, BrainCircuit } from"lucide-react"

interface BigFiveModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

const traitDescriptions = {"Abertura": {
    icon:"🎨",
    color:"bg-wedo-purple",
    bgColor:"bg-wedo-purple/10 dark:bg-wedo-purple/20",
    textColor:"text-wedo-purple-text dark:text-wedo-purple",
    high: {
      label:"Alto",
      description:"Pessoas criativas, curiosas e abertas a novas experiências. Tendem a ser imaginativas, aventureiras e dispostas a explorar novas ideias.",
      traits: ["Criatividade","Curiosidade intelectual","Pensamento abstrato","Apreciação por arte","Aventureiro"]
    },
    medium: {
      label:"Moderado",
      description:"Equilíbrio entre abertura a experiências novas e preferência pelo familiar. Adaptável quando necessário.",
      traits: ["Flexível","Pragmático","Equilibrado","Seletivo"]
    },
    low: {
      label:"Baixo",
      description:"Preferência por rotinas estabelecidas e métodos tradicionais. Valoriza praticidade e consistência.",
      traits: ["Prático","Convencional","Focado no concreto","Preferência por rotina"]
    }
  },"Conscienciosidade": {
    icon:"✅",
    color:"bg-lia-btn-primary-bg",
    bgColor:"bg-wedo-cyan/10",
    textColor:"text-wedo-cyan-text dark:text-wedo-cyan-dark",
    high: {
      label:"Alto",
      description:"Pessoas organizadas, disciplinadas e orientadas a objetivos. Altamente confiáveis e responsáveis.",
      traits: ["Organização","Autodisciplina","Pontualidade","Orientado a metas","Planejamento detalhado"]
    },
    medium: {
      label:"Moderado",
      description:"Consegue ser organizado quando necessário, mas também flexível. Equilíbrio entre estrutura e espontaneidade.",
      traits: ["Responsável","Adaptável","Equilibrado","Pragmático"]
    },
    low: {
      label:"Baixo",
      description:"Mais espontâneo e flexível. Pode ser menos focado em detalhes e prazos rígidos.",
      traits: ["Espontâneo","Flexível","Adaptável","Despreocupado"]
    }
  },"Extroversão": {
    icon:"🎉",
    color:"bg-status-warning",
    bgColor:"bg-status-warning/10 dark:bg-status-warning/20",
    textColor:"text-status-warning dark:text-status-warning",
    high: {
      label:"Alto",
      description:"Energético, sociável e comunicativo. Gosta de interagir com pessoas e é estimulado por ambientes sociais.",
      traits: ["Sociabilidade","Assertividade","Energia alta","Entusiasmo","Comunicativo"]
    },
    medium: {
      label:"Moderado",
      description:"Ambivertido - confortável tanto sozinho quanto com outros. Adapta-se bem a diferentes situações sociais.",
      traits: ["Versátil","Equilibrado","Adaptável socialmente","Seletivo"]
    },
    low: {
      label:"Baixo",
      description:"Mais reservado e introspectivo. Prefere interações mais profundas com menos pessoas.",
      traits: ["Reservado","Reflexivo","Independente","Observador","Pensativo"]
    }
  },"Amabilidade": {
    icon:"🤝",
    color:"bg-status-success",
    bgColor:"bg-status-success/10 dark:bg-status-success/20",
    textColor:"text-status-success dark:text-status-success",
    high: {
      label:"Alto",
      description:"Empático, cooperativo e preocupado com o bem-estar dos outros. Valoriza harmonia nos relacionamentos.",
      traits: ["Empatia","Cooperação","Confiança","Altruísmo","Gentileza"]
    },
    medium: {
      label:"Moderado",
      description:"Equilibrado entre ser solícito e assertivo. Consegue ser compassivo mantendo limites saudáveis.",
      traits: ["Diplomático","Justo","Equilibrado","Respeitoso"]
    },
    low: {
      label:"Baixo",
      description:"Mais direto e objetivo nas interações. Prioriza honestidade e eficiência sobre diplomacia.",
      traits: ["Direto","Objetivo","Competitivo","Cético","Independente"]
    }
  },"Neuroticismo": {
    icon:"⚡",
    color:"bg-wedo-magenta",
    bgColor:"bg-wedo-magenta/10 dark:bg-wedo-magenta/20",
    textColor:"text-wedo-magenta-text dark:text-wedo-magenta",
    high: {
      label:"Alto",
      description:"Mais sensível emocionalmente e propenso a estresse. Pode ser mais cauteloso e vigilante.",
      traits: ["Sensível","Cauteloso","Preocupado","Emotivo","Vigilante"]
    },
    medium: {
      label:"Moderado",
      description:"Equilíbrio emocional razoável. Experimenta emoções normais sem ser excessivamente reativo.",
      traits: ["Equilibrado","Resiliente","Consciente","Adaptável"]
    },
    low: {
      label:"Baixo",
      description:"Emocionalmente estável e resiliente. Lida bem com estresse e mantém a calma em situações desafiadoras.",
      traits: ["Estabilidade emocional","Resiliência","Calma","Segurança","Otimismo"]
    }
  }
}

const getScoreLevel = (score: number): 'high' | 'medium' | 'low' => {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

const getScoreIcon = (score: number) => {
  if (score >= 70) return <TrendingUp className="w-3.5 h-3.5" />
  if (score >= 40) return <Minus className="w-3.5 h-3.5" />
  return <TrendingDown className="w-3.5 h-3.5" />
}

const getArchetype = (scores: Record<string, number>): { name: string; description: string; icon: string } => {
  const o = scores.openness || scores.Abertura || 50
  const c = scores.conscientiousness || scores.Conscienciosidade || 50
  const e = scores.extraversion || scores.Extroversão || 50
  const a = scores.agreeableness || scores.Amabilidade || 50
  // NEW-2 fix (audit rev. 15) — backend canonizou em `stability` (Big Five spec).
  // Mantém leitura legacy `neuroticism` como fallback até PR de schema/types unificado.
  const stab = scores.stability ?? scores.Estabilidade
  const n = stab !== undefined ? (100 - stab) : (scores.neuroticism || scores.Neuroticismo || 50)
  
  if (o >= 70 && c >= 70) return { name:"Inovador Estratégico", description:"Combina criatividade com organização", icon:"🎯" }
  if (e >= 70 && a >= 70) return { name:"Líder Empático", description:"Liderança natural com foco em pessoas", icon:"🌟" }
  if (c >= 70 && n <= 30) return { name:"Executor Confiável", description:"Alta confiabilidade e estabilidade", icon:"🛡️" }
  if (o >= 70 && e <= 40) return { name:"Pensador Criativo", description:"Pensador independente e inovador", icon:"💡" }
  if (c >= 70 && a >= 70) return { name:"Colaborador Organizado", description:"Trabalho em equipe com excelência", icon:"🤝" }
  if (e >= 70 && c >= 60) return { name:"Líder Dinâmico", description:"Energia e foco em resultados", icon:"⚡" }
  if (a >= 70 && n <= 40) return { name:"Mediador Estável", description:"Harmonia e equilíbrio emocional", icon:"☯️" }
  if (o >= 60 && e >= 60) return { name:"Comunicador Criativo", description:"Expressivo e inovador", icon:"🎨" }
  return { name:"Perfil Equilibrado", description:"Versatilidade em diferentes contextos", icon:"⚖️" }
}

const calculateFitScore = (candidateScores: Record<string, number>, jobProfile?: Record<string, number>): number => {
  if (!jobProfile) {
    const idealProfile = { openness: 65, conscientiousness: 70, extraversion: 55, agreeableness: 60, neuroticism: 40 }
    jobProfile = idealProfile
  }
  
  let totalDiff = 0
  let count = 0
  
  Object.keys(jobProfile).forEach(key => {
    const candidateValue = candidateScores[key] || candidateScores[key.charAt(0).toUpperCase() + key.slice(1)] || 50
    const jobValue = jobProfile![key]
    totalDiff += Math.abs(candidateValue - jobValue)
    count++
  })
  
  const avgDiff = totalDiff / count
  return Math.max(0, Math.round(100 - avgDiff))
}

export function BigFiveModal({ isOpen, onClose, candidate }: BigFiveModalProps) {
  const hasData = candidate?.bigFiveScores && Object.keys(candidate.bigFiveScores as Record<string, unknown>).length > 0
  const scores = (hasData ? candidate.bigFiveScores : {}) as Record<string, number>
  const traits = Object.keys(scores)

  const averageScore = hasData ? Math.round(
    Object.values(scores).reduce((a: number, b: number) => a + b, 0) / traits.length
  ) : 0
  
  const archetype = hasData ? getArchetype(scores) : { name:"Não avaliado", description:"Assessment pendente", icon:"❓" }
  const fitScore = hasData ? calculateFitScore(scores) : 0

  if (!hasData) {
    return (
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-lg bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
          <DialogHeader className="pb-3 dark:border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10 ring-2 ring-white">
                <AvatarImage src={candidate?.avatar as string | undefined} />
                <AvatarFallback className="text-xs bg-lia-bg-tertiary text-lia-text-secondary">
                  {(((candidate?.name as string | undefined)?.split(' ').map((n: string) => n[0]).join('') || '?'))}
                </AvatarFallback>
              </Avatar>
              <div>
                <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                  Relatório Big Five
                </DialogTitle>
                <DialogDescription className="text-xs text-lia-text-secondary mt-0.5">
                  {String(candidate?.name || 'Candidato')} • Assessment de Personalidade
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="py-8 flex flex-col items-center justify-center text-center">
            <div className="w-14 h-14 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full flex items-center justify-center mb-4">
              <BrainCircuit className="w-7 h-7 text-lia-text-secondary" />
            </div>
            <h3 className="text-base-ui font-medium text-lia-text-primary mb-2">
              Assessment não realizado
            </h3>
            <p className="text-xs text-lia-text-secondary max-w-xs">
              Este candidato ainda não completou o assessment de personalidade Big Five. O relatório será gerado automaticamente após a conclusão.
            </p>
          </div>

          <DialogFooter className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-4">
            <Button
              onClick={onClose}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active h-9 px-4 text-xs font-medium"
            >
              Entendido
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle max-h-[90vh] overflow-hidden flex flex-col p-0 rounded-xl">
        <DialogHeader className="px-6 py-4 dark:border-lia-border-subtle flex-shrink-0">
          <div className="flex items-center gap-3">
            <Avatar className="w-10 h-10 ring-2 ring-white">
              <AvatarImage src={candidate.avatar as string | undefined} />
              <AvatarFallback className="text-xs bg-lia-bg-tertiary text-lia-text-secondary">
                {String(candidate.name || '').split(' ').map((n: string) => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Relatório Big Five
              </DialogTitle>
              <DialogDescription className="text-xs text-lia-text-secondary mt-0.5">
                {String(candidate.name || '')} • Assessment de Personalidade
              </DialogDescription>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-4 gap-3">
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-lia-text-secondary" />
                  <span className="text-xs font-medium text-lia-text-secondary">
                    Score B5
                  </span>
                </div>
                <div className="text-lg font-semibold text-wedo-purple-text">
                  {averageScore}
                </div>
              </div>
            </div>
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-lia-text-secondary" />
                  <span className="text-xs font-medium text-lia-text-secondary">
                    Aderência
                  </span>
                </div>
                <div 
                  className={`text-lg font-semibold ${fitScore >= 70 ? 'text-status-success' : fitScore >= 50 ? 'text-lia-btn-primary-bg' : 'text-status-warning'}`}
                >
                  {fitScore}%
                </div>
              </div>
            </div>
            <div className="col-span-2 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-3 border border-wedo-purple/30">
              <div className="flex items-center gap-3">
                <span className="text-xl">{archetype.icon}</span>
                <div>
                  <div className="text-base-ui font-medium text-wedo-purple-text">
                    {archetype.name}
                  </div>
                  <div className="text-xs text-wedo-purple-text">
                    {archetype.description}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2 lg:col-span-1">
              <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl p-4 h-full border border-lia-border-subtle dark:border-lia-border-subtle">
                <h3 className="text-xs font-medium uppercase tracking-wide text-lia-text-primary mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 bg-wedo-purple rounded-full"></div>
                  Perfil de Personalidade
                </h3>

                <div className="relative w-full aspect-square max-w-sm mx-auto">
                  <svg className="w-full h-full" viewBox="0 0 200 200">
                    {[100, 75, 50, 25].map((r) => (
                      <circle
                        key={r}
                        cx="100"
                        cy="100"
                        r={r}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="0.5"
                        className="lia-text-muted"
                        opacity={0.3}
                      />
                    ))}

                    {traits.map((_, index) => {
                      const angle = (index * 2 * Math.PI) / traits.length - Math.PI / 2
                      const x = 100 + 100 * Math.cos(angle)
                      const y = 100 + 100 * Math.sin(angle)
                      return (
                        <line
                          key={`trait-${index}`}
                          x1="100"
                          y1="100"
                          x2={x}
                          y2={y}
                          stroke="currentColor"
                          strokeWidth="0.5"
                          className="lia-text-muted"
                          opacity={0.3}
                        />
                      )
                    })}

                    <polygon
                      points={traits.map((trait, index) => {
                        const score = scores[trait]
                        const angle = (index * 2 * Math.PI) / traits.length - Math.PI / 2
                        const distance = score
                        const x = 100 + distance * Math.cos(angle)
                        const y = 100 + distance * Math.sin(angle)
                        return `${x},${y}`
                      }).join(' ')}
                      fill="var(--wedo-purple)"
                      fillOpacity="0.3"
                      stroke="var(--wedo-purple)"
                      strokeWidth="2"
                    />

                    {traits.map((trait, index) => {
                      const score = scores[trait]
                      const angle = (index * 2 * Math.PI) / traits.length - Math.PI / 2
                      const distance = score
                      const x = 100 + distance * Math.cos(angle)
                      const y = 100 + distance * Math.sin(angle)
                      return (
                        <circle
                          key={trait}
                          cx={x}
                          cy={y}
                          r="4"
                          fill="white"
                          stroke="var(--wedo-purple)"
                          strokeWidth="2"
                        />
                      )
                    })}

                    {traits.map((trait, index) => {
                      const angle = (index * 2 * Math.PI) / traits.length - Math.PI / 2
                      const x = 100 + 115 * Math.cos(angle)
                      const y = 100 + 115 * Math.sin(angle)
                      const info = traitDescriptions[trait as keyof typeof traitDescriptions]
                      return (
                        <text
                          key={trait}
                          x={x}
                          y={y}
                          textAnchor="middle"
                          className="text-micro font-medium fill-current text-lia-text-primary"
                        >
                          <tspan>{info?.icon}</tspan>
                          <tspan x={x} dy="10">{trait}</tspan>
                        </text>
                      )
                    })}
                  </svg>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className="w-full h-1 bg-wedo-magenta rounded-md mb-1"></div>
                    <span className="text-micro text-lia-text-secondary">0-39 Baixo</span>
                  </div>
                  <div>
                    <div className="w-full h-1 bg-status-warning rounded-md mb-1"></div>
                    <span className="text-micro text-lia-text-secondary">40-69 Moderado</span>
                  </div>
                  <div>
                    <div className="w-full h-1 bg-status-success rounded-md mb-1"></div>
                    <span className="text-micro text-lia-text-secondary">70-100 Alto</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-span-2 lg:col-span-1 space-y-3">
              <h3 className="text-xs font-medium uppercase tracking-wide text-lia-text-primary mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-lia-btn-primary-bg rounded-full"></div>
                Scores por Traço
              </h3>
              {traits.map((trait) => {
                const score = scores[trait]
                const info = traitDescriptions[trait as keyof typeof traitDescriptions]
                const level = getScoreLevel(score)

                return (
                  <div
                    key={trait}
                    className={`${info.bgColor} rounded-md p-3 transition-colors motion-reduce:transition-none hover:border border-lia-border-subtle dark:border-lia-border-subtle`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{info.icon}</span>
                        <span className="text-base-ui font-medium text-lia-text-primary">
                          {trait}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Chip variant="neutral" muted className={`${info.color} text-white text-micro px-1.5 py-0.5`}>
                          {score}
                        </Chip>
                        {getScoreIcon(score)}
                      </div>
                    </div>

                    <div className="w-full h-1.5 bg-lia-interactive-active rounded-full overflow-hidden mb-2">
                      <div
                        className={`h-full ${info.color} transition-[width,height] duration-500`}
                        style={{width: `${score}%`}}
                      />
                    </div>

                    <div className={`text-xs ${info.textColor} font-medium`}>
                      {info[level].label}: {score >= 70 ? 'Alto' : score >= 40 ? 'Moderado' : 'Baixo'}
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="col-span-2 space-y-3 mt-2">
              <h3 className="text-xs font-medium uppercase tracking-wide text-lia-text-primary mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-status-success rounded-full"></div>
                Análise Detalhada
              </h3>
              {traits.map((trait) => {
                const score = scores[trait]
                const info = traitDescriptions[trait as keyof typeof traitDescriptions]
                const level = getScoreLevel(score)
                const details = info[level]

                return (
                  <div
                    key={trait}
                    className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 rounded-md ${info.color} flex items-center justify-center text-lg flex-shrink-0`}>
                        {info.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-base-ui font-medium text-lia-text-primary">
                            {trait}
                          </h4>
                          <Chip variant="neutral" muted className={`${info.color} text-white text-micro px-1.5 py-0.5`}>
                            {score} - {details.label}
                          </Chip>
                        </div>
                        <p className="text-xs text-lia-text-secondary mb-3">
                          {details.description}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {details.traits.map((t: string) => (
                            <Chip
                              key={t}
                              variant="neutral"
                              className="text-micro px-1.5 py-0.5 border-lia-border-subtle text-lia-text-secondary"
                            >
                              {t}
                            </Chip>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <DialogFooter className="px-6 py-4 bg-lia-bg-secondary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle flex-shrink-0">
          <div className="flex items-center justify-between w-full">
            <div className="text-xs text-lia-text-secondary">
              Assessment realizado em {new Date().toLocaleDateString('pt-BR')}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={onClose}
                className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-secondary"
              >
                Fechar
              </Button>
              <Button 
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active h-9 px-4 text-xs font-medium"
              >
                Exportar Relatório
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
