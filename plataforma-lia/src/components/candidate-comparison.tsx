"use client"

import React, { useState, useEffect, useCallback } from"react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  X, Brain, RefreshCw, TrendingUp, TrendingDown, Target,
  CheckCircle, AlertCircle, Star, Zap, Users, Clock,
  Award, Shield, Lightbulb, BarChart3, Eye, ChevronRight,
  Mail, Phone, Calendar, MapPin, Briefcase, GraduationCap,
  Code, Palette, MessageSquare, Heart, Rocket, Building,
  ArrowRight, Crown, Trophy, Flame, ThumbsUp, ThumbsDown
} from"lucide-react"

interface Candidate {
  id: string
  name: string
  role: string
  email: string
  phone: string
  location: string
  avatar?: string
  score: number
  status: string
  matchPercentage: number
  riskLevel: string
  culturalFit: number
  technicalMatch: number
  experience: string
  seniority: string
  availability: string
  expectedSalary: string
  skills: string[]
  lastActivity: string
  source: string
}

interface CandidateComparisonProps {
  isOpen: boolean
  onClose: () => void
  candidates: Candidate[]
  onSelectCandidate: (candidateId: string) => void
  onScheduleInterview: (candidateId: string) => void
  onContactCandidate: (candidateId: string) => void
}

interface LiaComparison {
  winner: string
  confidence: number
  summary: string
  comparison: {
    [key: string]: {
      technical: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
      behavioral: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
      cultural: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
      experience: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
      potential: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
      risk: { score: number; verdict: 'winner' | 'close' | 'lower'; insights: string[] }
    }
  }
  scenarios: {
    shortTerm: { best: string; reason: string }
    longTerm: { best: string; reason: string }
    leadership: { best: string; reason: string }
    innovation: { best: string; reason: string }
    stability: { best: string; reason: string }
  }
  recommendations: {
    primary: string
    secondary: string
    reasoning: string[]
    actionPlan: string[]
  }
}

export function CandidateComparison({
  isOpen,
  onClose,
  candidates,
  onSelectCandidate,
  onScheduleInterview,
  onContactCandidate
}: CandidateComparisonProps) {
  const [liaAnalysis, setLiaAnalysis] = useState<LiaComparison | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedScenario, setSelectedScenario] = useState<'shortTerm' | 'longTerm' | 'leadership' | 'innovation' | 'stability'>('shortTerm')

  // Gerar análise comparativa da LIA
  const generateLiaComparison = useCallback(async () => {
    setIsAnalyzing(true)

    // Simular análise da LIA
    await new Promise(resolve => setTimeout(resolve, 3000))

    const analysis = analyzeCandidatesComparison(candidates)
    setLiaAnalysis(analysis)
    setIsAnalyzing(false)
  }, [candidates])

  const analyzeCandidatesComparison = (candidates: Candidate[]): LiaComparison => {
    if (candidates.length < 2) {
      throw new Error("Pelo menos 2 candidatos são necessários para comparação")
    }

    // Ordenar candidatos por score para facilitar análise
    const sortedCandidates = [...candidates].sort((a, b) => b.matchPercentage - a.matchPercentage)
    const topCandidate = sortedCandidates[0]
    const secondCandidate = sortedCandidates[1]

    // Gerar análise comparativa detalhada
    const comparison: Record<string, Record<string, { verdict: string; score: number; insights: string[] }>> = {}

    candidates.forEach(candidate => {
      const isTop = candidate.id === topCandidate.id
      const score = candidate.matchPercentage
      const seniority = candidate.seniority || 'Pleno'
      const experienceYears = parseInt(candidate.experience?.replace(/\D/g, '') || '3')

      comparison[candidate.id] = {
        technical: {
          score: candidate.technicalMatch || score,
          verdict: isTop ? 'winner' : score >= topCandidate.matchPercentage - 5 ? 'close' : 'lower',
          insights: isTop ? [
            `Expertise superior em ${candidate.skills[0]}`,
            'Experiência técnica mais robusta',
            'Capacidade de resolver problemas complexos'
          ] : [
            'Conhecimento técnico sólido',
            'Potencial para desenvolvimento',
            'Base técnica adequada para a função'
          ]
        },
        behavioral: {
          score: candidate.culturalFit || Math.floor(Math.random() * 20) + 75,
          verdict: seniority.toLowerCase().includes('senior') ? 'winner' : 'close',
          insights: seniority.toLowerCase().includes('senior') ? [
            'Experiência em liderança de equipes',
            'Comunicação efetiva comprovada',
            'Maturidade profissional'
          ] : [
            'Boa capacidade de adaptação',
            'Motivado para aprender',
            'Trabalha bem em equipe'
          ]
        },
        cultural: {
          score: candidate.culturalFit || Math.floor(Math.random() * 20) + 80,
          verdict: candidate.culturalFit > 85 ? 'winner' : 'close',
          insights: [
            'Alinhamento com valores da empresa',
            'Fit com metodologias ágeis',
            'Perfil colaborativo'
          ]
        },
        experience: {
          score: experienceYears * 10,
          verdict: experienceYears > 5 ? 'winner' : experienceYears > 3 ? 'close' : 'lower',
          insights: experienceYears > 5 ? [
            `${experienceYears} anos de experiência sólida`,
            'Passou por diferentes cenários',
            'Experiência em projetos complexos'
          ] : [
            'Experiência adequada para a posição',
            'Crescimento consistente na carreira',
            'Potencial de desenvolvimento'
          ]
        },
        potential: {
          score: Math.max(100 - (experienceYears * 2), 70) + (score - 80),
          verdict: experienceYears < 4 ? 'winner' : 'close',
          insights: experienceYears < 4 ? [
            'Alto potencial de crescimento',
            'Ambição e energia para aprender',
            'ROI excelente a longo prazo'
          ] : [
            'Experiência estabilizada',
            'Crescimento consistente',
            'Maturidade profissional'
          ]
        },
        risk: {
          score: Math.max(100 - (score - 70), 20),
          verdict: score > 90 ? 'winner' : score > 80 ? 'close' : 'lower',
          insights: score > 90 ? [
            'Risco baixo de turnover',
            'Perfil estável e confiável',
            'Expectativas alinhadas'
          ] : [
            'Risco moderado identificado',
            'Necessita validação adicional',
            'Monitoramento recomendado'
          ]
        }
      }
    })

    // Determinar vencedor geral
    const winner = topCandidate.id
    const confidence = Math.min(95, Math.max(60, (topCandidate.matchPercentage - secondCandidate.matchPercentage) * 2 + 75))

    // Análise de cenários
    const scenarios = {
      shortTerm: {
        best: sortedCandidates.find(c => (c.seniority?.toLowerCase().includes('senior') || parseInt(c.experience?.replace(/\D/g, '') || '3') > 4))?.id || topCandidate.id,
        reason: 'Experiência sênior permite contribuição imediata'
      },
      longTerm: {
        best: sortedCandidates.find(c => !c.seniority?.toLowerCase().includes('senior') && parseInt(c.experience?.replace(/\D/g, '') || '3') < 5)?.id || topCandidate.id,
        reason: 'Alto potencial de crescimento e desenvolvimento'
      },
      leadership: {
        best: sortedCandidates.find(c => c.seniority?.toLowerCase().includes('senior'))?.id || topCandidate.id,
        reason: 'Experiência em liderança e mentoria'
      },
      innovation: {
        best: sortedCandidates.find(c => c.skills.some(skill => skill.toLowerCase().includes('react') || skill.toLowerCase().includes('typescript')))?.id || topCandidate.id,
        reason: 'Stack tecnológico moderno e inovador'
      },
      stability: {
        best: sortedCandidates.find(c => parseInt(c.experience?.replace(/\D/g, '') || '3') > 5)?.id || topCandidate.id,
        reason: 'Histórico de estabilidade e maturidade'
      }
    }

    return {
      winner,
      confidence,
      summary: `Baseado na análise de ${candidates.length} candidatos, ${topCandidate.name} apresenta o melhor fit geral com ${confidence}% de confiança. Score técnico de ${topCandidate.matchPercentage}% e experiência em ${topCandidate.skills.slice(0, 2).join(', ')}.`,
      comparison: comparison as any,
      scenarios,
      recommendations: {
        primary: winner,
        secondary: secondCandidate.id,
        reasoning: [
          `${topCandidate.name} tem score ${topCandidate.matchPercentage}% vs ${secondCandidate.matchPercentage}%`,
          `Experiência superior em ${topCandidate.skills[0]}`,
          'Melhor alinhamento com requisitos técnicos',
          'Risco menor de turnover'
        ],
        actionPlan: [
          `Priorizar ${topCandidate.name} para próxima etapa`,
          `Agendar entrevista técnica avançada`,
          `Manter ${secondCandidate.name} como backup`,
          'Verificar disponibilidade e expectativas'
        ]
      }
    }
  }

  // Executar análise quando componente abrir
  useEffect(() => {
    if (isOpen && candidates.length >= 2 && !liaAnalysis) {
      generateLiaComparison()
    }
  }, [isOpen, candidates, liaAnalysis, generateLiaComparison])

  const getVerdictIcon = (verdict: 'winner' | 'close' | 'lower') => {
    switch (verdict) {
      case 'winner': return <Trophy className="w-4 h-4 text-status-warning" />
      case 'close': return <Star className="w-4 h-4 text-lia-text-secondary" />
      case 'lower': return <Flame className="w-4 h-4 text-lia-text-primary" />
    }
  }

  const getVerdictColor = (verdict: 'winner' | 'close' | 'lower') => {
    switch (verdict) {
      case 'winner': return 'bg-status-warning/10 border-status-warning/30 text-status-warning'
      case 'close': return 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default text-lia-text-secondary'
      case 'lower': return 'bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-secondary'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl w-full max-w-7xl max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 dark:border-lia-border-subtle">
          <div>
            <h3 className="text-xl font-semibold text-lia-text-primary flex items-center gap-2">
              <Users className="w-5 h-5 text-lia-text-secondary" />
              Comparação Inteligente de Candidatos
            </h3>
            <p className="text-sm text-lia-text-secondary">
              Análise comparativa com insights de IA • {candidates.length} candidatos
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-6">
          {/* LIA Analysis Section */}
          <div className="mb-6 border border-status-success/30 dark:border-status-success/30 rounded-xl p-6 bg-status-success/10 dark:bg-status-success/10">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-5 h-5 text-status-success" />
              <h4 className="text-lg font-semibold text-status-success dark:text-status-success">
                Análise Comparativa IA
              </h4>
              {isAnalyzing && <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none text-status-success" />}
            </div>

            {isAnalyzing ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <RefreshCw className="w-12 h-12 animate-spin motion-reduce:animate-none text-status-success mx-auto mb-4" />
                  <h5 className="text-lg font-medium text-status-success dark:text-status-success mb-2">
                    IA analisando candidatos...
                  </h5>
                  <p className="text-status-success dark:text-status-success">
                    Comparando perfis, experiências e aderência cultural
                  </p>
                  <div className="flex items-center justify-center gap-4 mt-4 text-sm text-status-success">
                    <span>⚡ Análise técnica</span>
                    <span>🧠 Avaliação comportamental</span>
                    <span>🎯 Fit cultural</span>
                    <span>📊 Métricas comparativas</span>
                  </div>
                </div>
              </div>
            ) : liaAnalysis && (
              <div className="space-y-6">
                {/* Executive Summary */}
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-4 border border-status-success/30">
                  <h5 className="font-semibold text-status-success dark:text-status-success mb-2 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Recomendação Final IA
                  </h5>
                  <p className="text-status-success dark:text-status-success mb-3">
                    {liaAnalysis.summary}
                  </p>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Crown className="w-4 h-4 text-status-warning" />
                      <span className="font-medium text-status-success dark:text-status-success">
                        Candidato Recomendado: {candidates.find(c => c.id === liaAnalysis.winner)?.name}
                      </span>
                    </div>
                    <Chip variant="neutral" muted >
                      {liaAnalysis.confidence}% de confiança
                    </Chip>
                  </div>
                </div>

                {/* Scenario Analysis */}
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-4 border border-status-success/30">
                  <h5 className="font-semibold text-status-success dark:text-status-success mb-4 flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Análise por Cenário
                  </h5>

                  <div className="flex gap-2 mb-4">
                    {Object.entries(liaAnalysis.scenarios).map(([key, scenario]) => (
                      <button
                        key={key}
                        onClick={() => setSelectedScenario(key as 'shortTerm' | 'longTerm' | 'leadership' | 'innovation' | 'stability')}
                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
 selectedScenario === key
                            ? ' border border-status-success/30'
                            : 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary hover:bg-lia-interactive-active dark:hover:bg-lia-border-medium'
                        }`}
                      >
                        {key === 'shortTerm' ? 'Curto Prazo' :
                         key === 'longTerm' ? 'Longo Prazo' :
                         key === 'leadership' ? 'Liderança' :
                         key === 'innovation' ? 'Inovação' : 'Estabilidade'}
                      </button>
                    ))}
                  </div>

                  <div className="bg-status-success/10 dark:bg-status-success/20 p-3 rounded-md">
                    <div className="flex items-center gap-2 mb-2">
                      <ThumbsUp className="w-4 h-4 text-status-success" />
                      <span className="font-medium text-status-success dark:text-status-success">
                        Melhor para {selectedScenario === 'shortTerm' ? 'Curto Prazo' :
                                   selectedScenario === 'longTerm' ? 'Longo Prazo' :
                                   selectedScenario === 'leadership' ? 'Liderança' :
                                   selectedScenario === 'innovation' ? 'Inovação' : 'Estabilidade'}:
                      </span>
                      <span className="font-semibold text-status-success">
                        {candidates.find(c => c.id === liaAnalysis.scenarios[selectedScenario].best)?.name}
                      </span>
                    </div>
                    <p className="text-sm text-status-success dark:text-status-success">
                      {liaAnalysis.scenarios[selectedScenario].reason}
                    </p>
                  </div>
                </div>

                {/* Action Plan */}
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-4 border border-status-success/30">
                  <h5 className="font-semibold text-status-success dark:text-status-success mb-3 flex items-center gap-2">
                    <Rocket className="w-4 h-4" />
                    Plano de Ação Recomendado
                  </h5>
                  <div className="space-y-2">
                    {liaAnalysis.recommendations.actionPlan.map((action, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm text-status-success dark:text-status-success">
                        <ChevronRight className="w-3 h-3" />
                        {action}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Candidates Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {candidates.map((candidate, index) => (
              <Card key={candidate.id} className="relative overflow-hidden">
                {/* Winner Badge */}
                {liaAnalysis && candidate.id === liaAnalysis.winner && (
                  <div className="absolute top-3 right-3 z-10">
                    <Chip variant="warning" muted className="gap-1">
                      <Crown className="w-3 h-3" />
                      IA Recomenda
                    </Chip>
                  </div>
                )}

                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <Avatar className="h-14 w-14">
                      <AvatarImage src={candidate.avatar} />
                      <AvatarFallback className="text-lg">
                        {candidate.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h4 className="font-semibold text-lia-text-primary mb-1">
                        {candidate.name}
                      </h4>
                      <p className="text-sm text-lia-text-secondary mb-2">
                        {candidate.role} • {candidate.seniority}
                      </p>
                      <div className="flex items-center gap-2">
                        <Chip variant="neutral" className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">
                          {candidate.matchPercentage}% Match
                        </Chip>
                        <Chip variant="neutral" className={
 candidate.riskLevel === 'Baixo' ? 'text-status-success border-status-success/30' :
                          candidate.riskLevel === 'Médio' ? 'text-status-warning border-status-warning/30' :
                          'text-status-error border-status-error/30'
                        }>
                          {candidate.riskLevel} Risco
                        </Chip>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Quick Info */}
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-lia-text-secondary">
                      <MapPin className="w-3 h-3" />
                      {candidate.location}
                    </div>
                    <div className="flex items-center gap-2 text-lia-text-secondary">
                      <Briefcase className="w-3 h-3" />
                      {candidate.experience}
                    </div>
                    <div className="flex items-center gap-2 text-lia-text-secondary">
                      <Clock className="w-3 h-3" />
                      {candidate.availability}
                    </div>
                  </div>

                  {/* Skills */}
                  <div>
                    <h6 className="text-xs font-medium text-lia-text-primary mb-2">
                      Principais Skills
                    </h6>
                    <div className="flex flex-wrap gap-1">
                      {candidate.skills.slice(0, 4).map((skill, idx) => (
                        <Chip density="relaxed" key={idx} variant="neutral" muted >
                          {skill}
                        </Chip>
                      ))}
                      {candidate.skills.length > 4 && (
                        <Chip density="relaxed" variant="neutral" >
                          +{candidate.skills.length - 4}
                        </Chip>
                      )}
                    </div>
                  </div>

                  {/* LIA Analysis for this candidate */}
                  {liaAnalysis && liaAnalysis.comparison[candidate.id] && (
                    <div className="space-y-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                      <h6 className="text-xs font-medium text-status-success dark:text-status-success flex items-center gap-1">
                        <Brain className="w-3 h-3 text-wedo-cyan" />
                        Análise IA
                      </h6>

                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(liaAnalysis.comparison[candidate.id]).map(([metric, data]: [string, any]) => (
                          <div key={metric} className={`p-2 rounded-md border text-center ${getVerdictColor(data.verdict)}`}>
                            <div className="flex items-center justify-center gap-1 mb-1">
                              {getVerdictIcon(data.verdict)}
                              <span className="text-xs font-medium capitalize">
                                {metric === 'technical' ? 'Técnico' :
                                 metric === 'behavioral' ? 'Comportamental' :
                                 metric === 'cultural' ? 'Cultural' :
                                 metric === 'experience' ? 'Experiência' :
                                 metric === 'potential' ? 'Potencial' : 'Risco'}
                              </span>
                            </div>
                            <div className="text-xs font-bold">
                              {data.score}%
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Top insights */}
                      <div className="space-y-1">
                        {Object.values(liaAnalysis.comparison[candidate.id])
                          .filter((data: { verdict: string; insights: string[]; score: number }) => data.verdict === 'winner')
                          .slice(0, 2)
                          .map((data: { verdict: string; insights: string[]; score: number }, idx: number) => (
                          <div key={idx} className="text-xs text-status-success dark:text-status-success flex items-start gap-1">
                            <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                            {data.insights[0]}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSelectCandidate(candidate.id)}
                      className="flex-1 gap-1"
                    >
                      <Eye className="w-3 h-3" />
                      Ver Perfil
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onContactCandidate(candidate.id)}
                      className="gap-1"
                    >
                      <Mail className="w-3 h-3" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onScheduleInterview(candidate.id)}
                      className="gap-1"
                    >
                      <Calendar className="w-3 h-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Final Actions */}
          <div className="flex justify-center gap-4 mt-8 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <Button variant="outline" onClick={onClose}>
              Fechar Comparação
            </Button>
            {liaAnalysis && (
              <Button
                onClick={() => onSelectCandidate(liaAnalysis.winner)}
                className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                <Crown className="w-4 h-4" />
                Ver Candidato Recomendado
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
