"use client"

import React, { useState, useCallback, useEffect } from"react"
import { useModalA11y } from"@/hooks/ui/use-modal-a11y"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Brain, RefreshCw, Eye, X, Mail, Phone, MapPin, Linkedin, Globe, CheckCircle, AlertCircle, Calendar, Heart, ChevronRight } from"lucide-react"
import { textStyles } from"@/lib/design-tokens"

interface Candidate {
  id: string; name: string; role: string; email: string; phone: string
  location: string; avatar?: string; score: number; status: string
  matchPercentage: number; riskLevel: string; culturalFit: number
  technicalMatch: number; experience: string; seniority: string
  availability: string; expectedSalary: string; preferredLocation: string
  linkedin?: string; portfolio?: string; skills: string[]
  lastActivity: string; source: string
}

interface QuickViewModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  onNavigateToFull: (candidateId: string) => void
}

export function QuickViewModal({ isOpen, onClose, candidate, onNavigateToFull }: QuickViewModalProps) {
  const [showLiaInsights, setShowLiaInsights] = useState(true)
  interface LiaInsights {
    executiveSummary?: string
    candidateStatus?: { priority?: string; readiness?: string; timeline?: string }
    nextSteps?: Array<{ action?: string; priority?: string; timeframe?: string }>
    analysis?: { strengths?: string[]; concerns?: string[]; redFlags?: string[] }
    approachStrategy?: { primary?: string; timing?: string; talking_points?: string[]; tone?: string; focus?: string; urgency?: string }
    dataInsights?: { matchStrength?: string; topSkillsMatch?: string[]; experienceLevel?: string; salaryAlignment?: string; locationFit?: string; availabilityScore?: string; compatibilityScore?: number; riskLevel?: string; successProbability?: string; keySkills?: string[] }
  }
  const [liaInsights, setLiaInsights] = useState<LiaInsights | null>(null)
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false)

  // Gerar insights da LIA quando o modal abrir
  const generateLiaInsights = useCallback(async () => {
    setIsLiaAnalyzing(true)

    // Simular análise da LIA
    await new Promise(resolve => setTimeout(resolve, 1500))

    const insights = analyzeCandidateQuickInsights(candidate)
    setLiaInsights(insights as unknown as LiaInsights)
    setIsLiaAnalyzing(false)
  }, [candidate])

  const analyzeCandidateQuickInsights = (candidate: Candidate | null) => {
    if (!candidate) return null
    const score = candidate.matchPercentage || candidate.score || 85
    const skills = candidate.skills || []
    const experience = candidate.experience || ''
    const seniority = candidate.seniority || (candidate as Candidate & { level?: string }).level || 'Pleno'
    const role = candidate.role || (candidate as Candidate & { position?: string }).position || ''

    return {
      // Resumo executivo da LIA
      executiveSummary: score >= 90
        ? `Candidato excepcional com ${score}% de match. Profile ideal para a posição com experiência sólida em ${skills.slice(0, 2).join(' e ')}.`
        : score >= 80
        ? `Candidato qualificado com ${score}% de match. Atende a maioria dos requisitos com potencial de crescimento.`
        : `Candidato promissor com ${score}% de match. Alguns gaps identificados que podem ser desenvolvidos.`,

      // Status da candidatura
      candidateStatus: {
        priority: score >= 90 ? 'alta' : score >= 80 ? 'média' : 'baixa',
        readiness: score >= 85 ? 'Pronto para próxima etapa' : 'Necessita avaliação adicional',
        timeline: score >= 90 ? 'Fast-track recomendado' : 'Timeline normal'
      },

      // Próximos passos recomendados
      nextSteps: score >= 90 ? [
        { action: 'Agendar entrevista técnica', priority: 'alta', timeframe: '2-3 dias' },
        { action: 'Verificar disponibilidade imediata', priority: 'alta', timeframe: '24h' },
        { action: 'Preparar proposta competitiva', priority: 'média', timeframe: '1 semana' }
      ] : score >= 80 ? [
        { action: 'Entrevista comportamental', priority: 'alta', timeframe: '3-5 dias' },
        { action: 'Teste técnico complementar', priority: 'média', timeframe: '1 semana' },
        { action: 'Verificação de referências', priority: 'baixa', timeframe: '2 semanas' }
      ] : [
        { action: 'Triagem detalhada', priority: 'alta', timeframe: '2-3 dias' },
        { action: 'Assessment de skills', priority: 'alta', timeframe: '1 semana' },
        { action: 'Mentoria/desenvolvimento', priority: 'baixa', timeframe: '1 mês' }
      ],

      // Análise de strengths e concerns
      analysis: {
        strengths: score >= 90 ? [
          `Expertise avançada em ${skills[0]}`,
          'Profile senior com liderança',
          'Match cultural excelente'
        ] : score >= 80 ? [
          `Sólida experiência em ${skills[0]}`,
          'Perfil equilibrado técnico/comportamental',
          'Boa adequação à vaga'
        ] : [
          'Potencial de crescimento',
          'Motivação para aprender',
          'Disponibilidade para desenvolvimento'
        ],

        concerns: score >= 90 ? [
          'Possível overqualification',
          'Expectativas salariais altas',
          'Risco de recusa por outras ofertas'
        ] : score >= 80 ? [
          'Alguns gaps técnicos menores',
          'Necessita validação comportamental',
          'Confirmar interesse real'
        ] : [
          'Gaps significativos identificados',
          'Necessita desenvolvimento intensivo',
          'Risco de baixa performance inicial'
        ],

        redFlags: [
          'Verificar estabilidade no emprego atual',
          'Confirmar motivação para mudança',
          'Validar expectativas realistas'
        ]
      },

      // Estratégia de abordagem
      approachStrategy: {
        tone: score >= 90 ? 'Competitivo e direto' : score >= 80 ? 'Profissional e atrativo' : 'Desenvolvimentista e acolhedor',
        focus: score >= 90 ? 'Benefícios e oportunidades únicas' : score >= 80 ? 'Crescimento e aprendizado' : 'Mentoria e desenvolvimento',
        urgency: score >= 90 ? 'Alta - agir rapidamente' : score >= 80 ? 'Média - processar normalmente' : 'Baixa - avaliar com cuidado'
      },

      // Insights baseados em dados
      dataInsights: {
        compatibilityScore: score,
        experienceLevel: seniority,
        keySkills: skills.slice(0, 3),
        riskLevel: score >= 85 ? 'Baixo' : score >= 70 ? 'Médio' : 'Alto',
        successProbability: score >= 90 ? '95%' : score >= 80 ? '85%' : '70%'
      }
    }
  }

  // Executar análise quando o modal abrir
  useEffect(() => {
    if (isOpen && candidate && !liaInsights) {
      generateLiaInsights()
    }
  }, [isOpen, candidate, liaInsights, generateLiaInsights])

  const dialogRef = useModalA11y(isOpen, onClose)
  if (!isOpen || !candidate) return null

  return (
    <div className="fixed inset-0 bg-lia-overlay/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="quick-view-modal-title" className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle w-full max-w-4xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 dark:border-lia-border-subtle">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback className="text-lg">{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 id="quick-view-modal-title" className="text-xl font-semibold text-lia-text-primary">
                {candidate.name}
              </h3>
              <p className="text-sm text-lia-text-secondary">
                {candidate.role} • {candidate.experience} • {candidate.location}
              </p>
              <div className="flex items-center gap-3 mt-2">
                <Chip variant="neutral" >
                  {candidate.matchPercentage}% Match
                </Chip>
                <Chip variant="neutral">
                  {candidate.status}
                </Chip>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToFull(candidate.id)}
              className="gap-2"
            >
              <Eye className="w-4 h-4" />
              Ver Perfil Completo
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose} aria-label="Fechar visualização rápida" data-dismiss="true">
              <X className="w-4 h-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* LIA Insights Section */}
          <div className="mb-6 border border-status-success/30 rounded-xl p-4 bg-status-success/10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-status-success flex items-center gap-2">
                <Brain className="w-4 h-4 text-status-success" />
                Insights Instantâneos de IA
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowLiaInsights(!showLiaInsights)}
                className="text-xs text-status-success hover:bg-status-success/15"
              >
                {showLiaInsights ? 'Ocultar' : 'Mostrar'}
              </Button>
            </div>

            {showLiaInsights && (
              <div>
                {isLiaAnalyzing ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="text-center">
                      <RefreshCw className="w-6 h-6 animate-spin motion-reduce:animate-none text-status-success mx-auto mb-2" />
                      <p className="text-xs text-status-success">IA analisando perfil...</p>
                    </div>
                  </div>
                ) : liaInsights && (
                  <div className="space-y-4">
                    {/* Executive Summary */}
                    <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Resumo Executivo:</h5>
                      <p className="text-xs text-status-success">{liaInsights.executiveSummary}</p>
                    </div>

                    {/* Status and Next Steps */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2">Status:</h5>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span>Prioridade:</span>
                            <Chip variant="neutral" muted className={`text-xs ${
 liaInsights.candidateStatus?.priority === 'alta' ? '' :
                              liaInsights.candidateStatus?.priority === 'média' ? '' :
                              'bg-lia-bg-tertiary text-lia-text-primary'
                            }`}>
                              {liaInsights.candidateStatus?.priority?.toUpperCase()}
                            </Chip>
                          </div>
                          <div className="text-xs text-status-success">{liaInsights.candidateStatus?.readiness}</div>
                        </div>
                      </div>

                      <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2">Estratégia:</h5>
                        <div className="space-y-1 text-xs text-status-success">
                          <div><strong>Tom:</strong> {liaInsights.approachStrategy?.tone}</div>
                          <div><strong>Urgência:</strong> {liaInsights.approachStrategy?.urgency}</div>
                        </div>
                      </div>
                    </div>

                    {/* Next Steps */}
                    <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Próximos Passos Recomendados:</h5>
                      <div className="space-y-2">
                        {liaInsights.nextSteps?.slice(0, 3).map((step, idx: number) => (
                          <div key={`step-${idx}`} className="flex items-center justify-between">
                            <div className="flex-1">
                              <span className="text-xs text-status-success">{step.action}</span>
                              <div className="flex items-center gap-2 mt-1">
                                <Chip variant="neutral" muted className={`text-xs ${
 step.priority === 'alta' ? '' :
                                  step.priority === 'média' ? '' :
                                  'bg-lia-bg-tertiary text-lia-text-primary'
                                }`}>
                                  {step.priority}
                                </Chip>
                                <span className="text-xs text-status-success">{step.timeframe}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Analysis Summary */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-status-success" />
                          Pontos Fortes:
                        </h5>
                        <ul className="text-xs text-status-success space-y-1">
                          {liaInsights.analysis?.strengths?.slice(0, 3).map((strength: string, idx: number) => (
                            <li key={`str-${idx}`}>• {strength}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-lia-bg-primary rounded-xl p-3 border border-wedo-orange/30">
                        <h5 className="text-xs font-medium text-wedo-orange-text mb-2 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3 text-wedo-orange" />
                          Pontos de Atenção:
                        </h5>
                        <ul className="text-xs text-wedo-orange-text space-y-1">
                          {liaInsights.analysis?.concerns?.slice(0, 3).map((concern: string, idx: number) => (
                            <li key={`con-${idx}`}>• {concern}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Quick Data Insights */}
                    <div className="bg-lia-bg-primary rounded-xl p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Métricas:</h5>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="text-center">
                          <div className="font-semibold text-status-success">{liaInsights.dataInsights?.compatibilityScore}%</div>
                          <div className="text-status-success">Match</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-status-success">{liaInsights.dataInsights?.successProbability}</div>
                          <div className="text-status-success">Sucesso</div>
                        </div>
                        <div className="text-center">
                          <div className={`font-semibold ${
 liaInsights.dataInsights?.riskLevel === 'Baixo' ? 'text-status-success' :
                            liaInsights.dataInsights?.riskLevel === 'Médio' ? 'text-status-warning' :
                            'text-status-error'
                          }`}>
                            {liaInsights.dataInsights?.riskLevel}
                          </div>
                          <div className="text-status-success">Risco</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-6">
            {/* Coluna 1: Informações Básicas */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Contato</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">{candidate.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">{candidate.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">{candidate.location}</span>
                  </div>
                  {candidate.linkedin && (
                    <div className="flex items-center gap-2">
                      <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                      <a href={candidate.linkedin} target="_blank" className="text-sm text-lia-text-secondary hover:underline">
                        LinkedIn
                      </a>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Disponibilidade</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm">
                    <span className="text-lia-text-primary">Disponibilidade:</span>
                    <span className="ml-2 font-medium">{candidate.availability}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-lia-text-primary">Salário esperado:</span>
                    <span className="ml-2 font-medium">{candidate.expectedSalary}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-lia-text-primary">Local preferido:</span>
                    <span className="ml-2 font-medium">{candidate.preferredLocation}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coluna 2: Métricas e Skills */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Métricas</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-lia-text-secondary">Match Técnico</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-lia-interactive-active rounded-full h-2">
                        <div
                          className="bg-status-success h-2 rounded-full"
                          style={{width: `${candidate.technicalMatch}%`}}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{candidate.technicalMatch}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-lia-text-secondary">Fit Cultural</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-lia-interactive-active rounded-full h-2">
                        <div
                          className="bg-lia-btn-primary-bg h-2 rounded-full"
                          style={{width: `${candidate.culturalFit}%`}}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{candidate.culturalFit}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-lia-text-secondary">Nível de Risco</span>
                    <Chip
                      variant={
                        candidate.riskLevel === 'Baixo' ? 'success' :
                        candidate.riskLevel === 'Médio' ? 'warning' :
                        'danger'
                      }
                    >
                      {candidate.riskLevel}
                    </Chip>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Principais Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {candidate.skills.slice(0, 8).map((skill) => (
                      <Chip density="relaxed" key={skill} variant="neutral" muted >
                        {skill}
                      </Chip>
                    ))}
                    {candidate.skills.length > 8 && (
                      <Chip density="relaxed" variant="neutral" >
                        +{candidate.skills.length - 8} mais
                      </Chip>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coluna 3: Histórico */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Histórico Recente</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-status-success rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Candidatura enviada</div>
                      <div className="text-xs text-lia-text-primary">{candidate.lastActivity}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-lia-btn-primary-bg rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Análise concluída</div>
                      <div className="text-xs text-lia-text-primary">Há 2 horas</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-lia-border-medium rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Perfil visualizado</div>
                      <div className="text-xs text-lia-text-primary">Há 1 dia</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Origem</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
                      <Globe className="w-4 h-4 text-lia-text-secondary" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{candidate.source}</div>
                      <div className="text-xs text-lia-text-primary">Fonte de candidatura</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex justify-center gap-3 mt-6 pt-6 border-t border-lia-border-subtle">
            <Button variant="outline" className="gap-2">
              <Mail className="w-4 h-4" />
              Enviar Email
            </Button>
            <Button variant="outline" className="gap-2">
              <Calendar className="w-4 h-4" />
              Agendar Entrevista
            </Button>
            <Button variant="outline" className="gap-2">
              <Heart className="w-4 h-4" />
              Favoritar
            </Button>
            <Button
              onClick={() => onNavigateToFull(candidate.id)}
              className="gap-2"
            >
              <ChevronRight className="w-4 h-4" />
              Ver Perfil Completo
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

