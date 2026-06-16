"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { X, TrendingUp, Download, Brain, Users, Target, Zap, Shield } from"lucide-react"

interface DISCModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
  assessmentData?: DISCAssessmentData
}

interface DISCScores {
  dominance: number
  influence: number
  steadiness: number
  conscientiousness: number
}

interface DISCAssessmentData {
  discScores: DISCScores
  profile: string
  profileDescription: string
  assessmentType?: string
  assessmentProvider?: string
  completedAt?: string
  duration?: string
  culturalFitScore?: number
  leadershipScore?: number
  leadershipStyle?: string
  teamworkScore?: number
  adaptabilityScore?: number
  stressResilienceScore?: number
  primaryTraits?: Array<{ trait: string; score: number; description?: string }>
  leadershipStrengths?: string[]
  developmentAreas?: string[]
  recommendation?: string
  comparisonToRole?: {
    idealProfile: string
    candidateProfile: string
    matchPercentage: number
  }
  reportUrl?: string
}

const discDimensions = {
  dominance: {
    letter:"D",
    name:"Dominância",
    icon: Target,
    bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
    borderColor:"border-lia-border-default dark:border-lia-border-default",
    high: {
      label:"Alto",
      keywords: ["Direto","Decisivo","Competitivo","Assertivo"],
      description:"Pessoas com alta Dominância são orientadas a resultados, assumem riscos, tomam decisões rápidas e preferem liderar. São motivadas por desafios e autoridade.",
      strengths: ["Toma decisões rápidas","Foco em resultados","Aceita desafios","Assume responsabilidades"],
      challenges: ["Pode parecer impaciente","Tende a dominar discussões","Pode ser insensível às necessidades dos outros"]
    },
    medium: {
      label:"Moderado",
      keywords: ["Equilibrado","Flexível","Adaptável"],
      description:"Equilíbrio entre assertividade e cooperação. Consegue liderar quando necessário, mas também trabalha bem em equipe.",
      strengths: ["Adaptabilidade situacional","Equilíbrio entre liderar e colaborar"],
      challenges: ["Pode hesitar em situações que exigem decisão rápida"]
    },
    low: {
      label:"Baixo",
      keywords: ["Colaborativo","Consensual","Cauteloso","Apoiador"],
      description:"Prefere trabalhar em equipe e buscar consenso. Evita conflitos e valoriza harmonia nas relações.",
      strengths: ["Excelente colaborador","Busca consenso","Evita conflitos desnecessários"],
      challenges: ["Pode evitar tomar decisões difíceis","Pode ser visto como passivo"]
    }
  },
  influence: {
    letter:"I",
    name:"Influência",
    icon: Users,
    bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
    borderColor:"border-lia-btn-primary-bg/25",
    high: {
      label:"Alto",
      keywords: ["Entusiasta","Otimista","Comunicativo","Persuasivo"],
      description:"Pessoas com alta Influência são comunicativas, entusiastas e motivadoras. Gostam de interagir com outros e são hábeis em persuadir e inspirar.",
      strengths: ["Excelente comunicador","Motiva equipes","Cria ambiente positivo","Networking natural"],
      challenges: ["Pode ser desorganizado","Tende a evitar detalhes","Pode prometer demais"]
    },
    medium: {
      label:"Moderado",
      keywords: ["Sociável","Equilibrado","Adaptável"],
      description:"Consegue ser persuasivo quando necessário, mas também valoriza reflexão e análise antes de agir.",
      strengths: ["Comunicação equilibrada","Sociável sem excessos"],
      challenges: ["Pode ter dificuldade em ambientes extremamente sociais ou reservados"]
    },
    low: {
      label:"Baixo",
      keywords: ["Reservado","Reflexivo","Analítico","Factual"],
      description:"Prefere comunicação direta e factual. Mais reservado em interações sociais, valoriza dados e lógica.",
      strengths: ["Focado em fatos","Reflexivo","Evita exageros"],
      challenges: ["Pode parecer frio ou distante","Pode ter dificuldade em networking"]
    }
  },
  steadiness: {
    letter:"S",
    name:"Estabilidade",
    icon: Shield,
    bgColor:"bg-lia-bg-tertiary",
    borderColor:"border-lia-border-subtle",
    high: {
      label:"Alto",
      keywords: ["Paciente","Confiável","Leal","Previsível"],
      description:"Pessoas com alta Estabilidade são pacientes, confiáveis e valorizam segurança. São excelentes ouvintes e mantêm ambientes calmos.",
      strengths: ["Altamente confiável","Excelente ouvinte","Estabiliza equipes","Leal e consistente"],
      challenges: ["Resistência a mudanças","Pode evitar confrontos necessários","Demora para se adaptar"]
    },
    medium: {
      label:"Moderado",
      keywords: ["Equilibrado","Adaptável","Flexível"],
      description:"Equilíbrio entre estabilidade e adaptabilidade. Consegue lidar com mudanças mantendo certa consistência.",
      strengths: ["Adaptável a mudanças graduais","Equilíbrio emocional"],
      challenges: ["Pode ter dificuldade com mudanças muito rápidas ou ambientes muito estáveis"]
    },
    low: {
      label:"Baixo",
      keywords: ["Dinâmico","Multitarefa","Inquieto","Espontâneo"],
      description:"Prefere ambientes dinâmicos e mudanças frequentes. Gosta de variedade e pode ter dificuldade com rotinas.",
      strengths: ["Abraça mudanças","Multitarefa","Energia alta"],
      challenges: ["Pode parecer impaciente","Pode ter dificuldade com rotinas","Pode buscar mudanças desnecessárias"]
    }
  },
  conscientiousness: {
    letter:"C",
    name:"Conformidade",
    icon: Zap,
    color:"var(--lia-text-tertiary)",
    bgColor:"bg-lia-bg-secondary",
    borderColor:"border-lia-border-subtle",
    high: {
      label:"Alto",
      keywords: ["Analítico","Preciso","Metódico","Perfeccionista"],
      description:"Pessoas com alta Conformidade são precisas, analíticas e orientadas a qualidade. Valorizam regras, procedimentos e excelência.",
      strengths: ["Alta qualidade de trabalho","Análise detalhada","Segue procedimentos","Metódico"],
      challenges: ["Pode ser perfeccionista demais","Análise excessiva pode atrasar decisões","Pode ser crítico demais"]
    },
    medium: {
      label:"Moderado",
      keywords: ["Equilibrado","Prático","Flexível"],
      description:"Equilíbrio entre atenção aos detalhes e visão geral. Consegue ser preciso sem perder produtividade.",
      strengths: ["Equilíbrio entre qualidade e velocidade","Pragmático"],
      challenges: ["Pode subestimar ou superestimar detalhes dependendo da situação"]
    },
    low: {
      label:"Baixo",
      keywords: ["Independente","Generalista","Intuitivo","Flexível"],
      description:"Prefere visão geral e flexibilidade. Menos focado em regras e detalhes, mais intuitivo na tomada de decisões.",
      strengths: ["Pensamento criativo","Flexível com regras","Decisões rápidas"],
      challenges: ["Pode ignorar detalhes importantes","Pode não seguir procedimentos","Pode cometer erros por falta de revisão"]
    }
  }
}

const profileDescriptions: Record<string, { title: string; description: string; icon: string; strengths: string[]; environment: string }> = {"D": {
    title:"Dominante Puro",
    description:"Líder nato orientado a resultados e desafios. Toma decisões rápidas e busca controle.",
    icon:"🎯",
    strengths: ["Liderança assertiva","Foco em resultados","Tomada de decisão"],
    environment:"Ambientes competitivos com autonomia e desafios"
  },"I": {
    title:"Influenciador Puro",
    description:"Comunicador entusiasta que inspira e motiva. Excelente em relacionamentos e networking.",
    icon:"⭐",
    strengths: ["Comunicação","Motivação de equipes","Networking"],
    environment:"Ambientes colaborativos com interação social"
  },"S": {
    title:"Estável Puro",
    description:"Profissional confiável que traz estabilidade. Excelente ouvinte e apoiador de equipes.",
    icon:"🛡️",
    strengths: ["Confiabilidade","Paciência","Suporte a equipes"],
    environment:"Ambientes estáveis com rotinas claras"
  },"C": {
    title:"Conforme Puro",
    description:"Analista metódico focado em qualidade e precisão. Valoriza dados e procedimentos.",
    icon:"📊",
    strengths: ["Análise detalhada","Qualidade","Precisão"],
    environment:"Ambientes estruturados com padrões claros"
  },"DI": {
    title:"Dominância + Influência",
    description:"Líder carismático que combina assertividade com capacidade de inspirar. Excelente para vendas e gestão.",
    icon:"🚀",
    strengths: ["Liderança inspiradora","Persuasão","Visão estratégica"],
    environment:"Ambientes dinâmicos que requerem liderança e comunicação"
  },"DC": {
    title:"Dominância + Conformidade",
    description:"Líder técnico que busca excelência. Combina assertividade com atenção a detalhes e qualidade.",
    icon:"🎖️",
    strengths: ["Liderança técnica","Padrões de qualidade","Resultados mensuráveis"],
    environment:"Ambientes que exigem expertise técnica e liderança"
  },"DS": {
    title:"Dominância + Estabilidade",
    description:"Líder consistente que equilibra assertividade com paciência. Confiável e orientado a metas.",
    icon:"⚓",
    strengths: ["Liderança estável","Persistência","Confiabilidade"],
    environment:"Ambientes que requerem liderança constante"
  },"ID": {
    title:"Influência + Dominância",
    description:"Comunicador assertivo que lidera através de entusiasmo. Excelente para vendas e apresentações.",
    icon:"💫",
    strengths: ["Apresentações","Vendas","Motivação"],
    environment:"Ambientes de alta energia com metas claras"
  },"IS": {
    title:"Influência + Estabilidade",
    description:"Relacionador empático que constrói conexões duradouras. Excelente para atendimento e RH.",
    icon:"🤝",
    strengths: ["Relacionamento","Empatia","Suporte"],
    environment:"Ambientes colaborativos focados em pessoas"
  },"IC": {
    title:"Influência + Conformidade",
    description:"Comunicador preciso que equilibra entusiasmo com atenção a detalhes.",
    icon:"📢",
    strengths: ["Comunicação clara","Apresentação de dados","Treinamento"],
    environment:"Ambientes que requerem comunicação técnica"
  },"SD": {
    title:"Estabilidade + Dominância",
    description:"Profissional persistente que combina paciência com orientação a resultados.",
    icon:"🏔️",
    strengths: ["Persistência","Resiliência","Execução consistente"],
    environment:"Projetos de longo prazo com metas definidas"
  },"SI": {
    title:"Estabilidade + Influência",
    description:"Facilitador de equipes que cria ambientes harmoniosos. Excelente para RH e suporte.",
    icon:"🌱",
    strengths: ["Facilitação","Harmonia","Desenvolvimento de pessoas"],
    environment:"Ambientes colaborativos e estáveis"
  },"SC": {
    title:"Estabilidade + Conformidade",
    description:"Profissional metódico que valoriza qualidade e consistência. Excelente para operações.",
    icon:"📋",
    strengths: ["Qualidade","Procedimentos","Confiabilidade"],
    environment:"Ambientes estruturados com processos claros"
  },"CD": {
    title:"Conformidade + Dominância",
    description:"Especialista assertivo que combina expertise técnica com determinação.",
    icon:"🔬",
    strengths: ["Expertise técnica","Padrões elevados","Determinação"],
    environment:"Ambientes técnicos com autonomia"
  },"CI": {
    title:"Conformidade + Influência",
    description:"Analista comunicativo que traduz dados complexos para linguagem acessível.",
    icon:"📈",
    strengths: ["Análise de dados","Apresentação","Treinamento técnico"],
    environment:"Ambientes que requerem comunicação técnica"
  },"CS": {
    title:"Conformidade + Estabilidade",
    description:"Especialista confiável focado em qualidade e consistência a longo prazo.",
    icon:"🔧",
    strengths: ["Qualidade consistente","Processos","Confiabilidade técnica"],
    environment:"Ambientes técnicos estáveis"
  }
}

const getScoreLevel = (score: number): 'high' | 'medium' | 'low' => {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

const getProfileType = (scores: DISCScores): string => {
  const sorted = [
    { key: 'D', value: scores.dominance },
    { key: 'I', value: scores.influence },
    { key: 'S', value: scores.steadiness },
    { key: 'C', value: scores.conscientiousness }
  ].sort((a, b) => b.value - a.value)

  if (sorted[0].value >= 70 && sorted[1].value >= 50) {
    return sorted[0].key + sorted[1].key
  }
  if (sorted[0].value >= 60) {
    return sorted[0].key
  }
  return sorted[0].key + sorted[1].key
}

export function DISCAssessmentModal({ isOpen, onClose, candidate, assessmentData }: DISCModalProps) {
  if (!isOpen) return null

  const data = assessmentData || (candidate?.discAssessment as DISCAssessmentData | undefined)
  if (!data?.discScores) return null

  const { discScores } = data
  const profileType = getProfileType(discScores)
  const profileInfo = profileDescriptions[profileType] || profileDescriptions["DI"]

  const dimensions = [
    { key: 'dominance', score: discScores.dominance },
    { key: 'influence', score: discScores.influence },
    { key: 'steadiness', score: discScores.steadiness },
    { key: 'conscientiousness', score: discScores.conscientiousness }
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-lia-overlay backdrop-blur-sm p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl max-w-4xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        <div className="p-6 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 dark:border-lia-border-subtle">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <Avatar className="w-14 h-14 ring-4 ring-white dark:ring-lia-border-strong">
                <AvatarImage src={candidate?.avatar as string} />
                <AvatarFallback className="text-lg bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">
                  {String(candidate?.name || '')} • {data.assessmentProvider || 'Assessment Comportamental'}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Relatório DISC
                </h2>
                <p className="text-lia-text-secondary text-xs">
                  {String(candidate?.name || '')} • {data.assessmentProvider || 'Assessment Comportamental'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {data.reportUrl && (
                <Button variant="outline" size="sm" className="text-xs bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
                  <Download className="w-3 h-3 mr-1" />
                  PDF
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-4 gap-3">
            <div className="col-span-2 bg-gradient-to-r from-lia-bg-tertiary dark:from-lia-btn-primary-hover to-lia-bg-secondary rounded-xl p-4 border border-lia-border-default dark:border-lia-border-default">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{profileInfo.icon}</span>
                <div>
                  <div className="text-lg font-semibold text-lia-text-primary">
                    {data.profile || profileType}
                  </div>
                  <div className="text-sm text-lia-text-secondary">
                    {profileInfo.title}
                  </div>
                </div>
              </div>
            </div>
            {data.comparisonToRole && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-xs font-medium text-lia-text-secondary">Match</span>
                  </div>
                  <div className="text-xl font-semibold text-lia-text-primary">
                    {data.comparisonToRole.matchPercentage}%
                  </div>
                </div>
              </div>
            )}
            {data.culturalFitScore && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-xs font-medium text-lia-text-secondary">Fit Cultural</span>
                  </div>
                  <div className="text-xl font-semibold text-lia-text-primary">
                    {data.culturalFitScore}%
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
                <div className="w-2 h-2 bg-lia-btn-primary-bg rounded-full"></div>
                Dimensões DISC
              </h3>

              {dimensions.map(({ key, score }) => {
                const dim = discDimensions[key as keyof typeof discDimensions]
                const level = getScoreLevel(score)
                const levelData = dim[level]
                const Icon = dim.icon

                return (
                  <div key={key} className={`${dim.bgColor} ${dim.borderColor} border rounded-md p-4`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-md flex items-center justify-center font-semibold text-lg`} style={{backgroundColor: dim.bgColor + '20', color: dim.bgColor}}>
                          {dim.letter}
                        </div>
                        <div>
                          <div className="font-semibold text-lia-text-primary">{dim.name}</div>
                          <div className="text-xs text-lia-text-secondary">{levelData.label}</div>
                        </div>
                      </div>
                      <div className="text-2xl font-semibold" style={{color: dim.bgColor}}>
                        {score}%
                      </div>
                    </div>

                    <div className="h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden mb-3">
                      <div 
                        className="h-full rounded-full transition-[width,height] duration-500"
                        style={{width: `${score}%`, backgroundColor: dim.bgColor}}
                      />
                    </div>

                    <p className="text-xs text-lia-text-secondary mb-2">{levelData.description}</p>

                    <div className="flex flex-wrap gap-1">
                      {levelData.keywords.map((kw, i) => (
                        <Chip key={i} variant="neutral" className="text-micro px-1.5 py-0 bg-lia-bg-primary/50">
                          {kw}
                        </Chip>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="space-y-4">
              <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
                <h3 className="text-sm font-semibold text-lia-text-primary mb-3 flex items-center gap-2">
                  <span className="text-lg">{profileInfo.icon}</span>
                  Perfil: {profileInfo.title}
                </h3>
                <p className="text-sm text-lia-text-secondary mb-4">{profileInfo.description}</p>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-xs font-semibold text-lia-text-primary mb-1">Pontos Fortes</p>
                    <div className="flex flex-wrap gap-1">
                      {profileInfo.strengths.map((s, i) => (
                        <Chip variant="neutral" muted key={i} className="text-micro bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default">
                          ✓ {s}
                        </Chip>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-lia-text-primary mb-1">Ambiente Ideal</p>
                    <p className="text-xs text-lia-text-secondary">{profileInfo.environment}</p>
                  </div>
                </div>
              </div>

              {data.leadershipStyle && (
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-3">Estilo de Liderança</h3>
                  <div className="flex items-center gap-3 mb-3">
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default">
                      {data.leadershipStyle}
                    </Chip>
                    {data.leadershipScore && (
                      <span className="text-lg font-semibold text-lia-text-primary">{data.leadershipScore}%</span>
                    )}
                  </div>
                  {data.leadershipStrengths && data.leadershipStrengths.length > 0 && (
                    <ul className="space-y-1">
                      {data.leadershipStrengths.map((s: string, i: number) => (
                        <li key={i} className="text-xs text-lia-text-secondary flex items-start gap-2">
                          <span className="text-lia-text-secondary">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {data.developmentAreas && data.developmentAreas.length > 0 && (
                <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-3">Áreas de Desenvolvimento</h3>
                  <ul className="space-y-1">
                    {data.developmentAreas.map((a: string, i: number) => (
                      <li key={i} className="text-xs text-lia-text-secondary flex items-start gap-2">
                        <span className="lia-text-secondary">•</span> {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.recommendation && (
                <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-default dark:border-lia-border-default">
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-2">Recomendação</h3>
                  <p className="text-xs text-lia-text-secondary">{data.recommendation}</p>
                </div>
              )}

              <div className="grid grid-cols-3 gap-2">
                {data.teamworkScore && (
                  <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle text-center">
                    <p className="text-lg font-semibold text-lia-text-primary">{data.teamworkScore}%</p>
                    <p className="text-micro text-lia-text-secondary">Trabalho em Equipe</p>
                  </div>
                )}
                {data.adaptabilityScore && (
                  <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle text-center">
                    <p className="text-lg font-semibold text-lia-text-primary">{data.adaptabilityScore}%</p>
                    <p className="text-micro text-lia-text-secondary">Adaptabilidade</p>
                  </div>
                )}
                {data.stressResilienceScore && (
                  <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle dark:border-lia-border-subtle text-center">
                    <p className="text-lg font-semibold text-lia-text-primary">{data.stressResilienceScore}%</p>
                    <p className="text-micro text-lia-text-secondary">Resiliência</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-lia-bg-secondary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle flex justify-between items-center">
          <p className="text-xs text-lia-text-secondary">
            {data.completedAt && `Realizado em ${data.completedAt}`}
            {data.duration && ` • Duração: ${data.duration}`}
          </p>
          <Button onClick={onClose} className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active">
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}

export default DISCAssessmentModal
