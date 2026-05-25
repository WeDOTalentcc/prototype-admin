"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Target, MessageSquare, Star, Heart, Clock, CheckCircle,
  Download, Copy
} from"lucide-react"
import type { ScreeningData, ScreeningStep } from"@/hooks/ai/use-lia-screening-dialogue"

interface JobData {
  title?: string
  [key: string]: unknown
}

interface LiaScreeningRightPanelProps {
  currentStep: ScreeningStep
  screeningData: ScreeningData
  jobData: JobData
}

export function LiaScreeningRightPanel({ currentStep, screeningData, jobData }: LiaScreeningRightPanelProps) {
  switch (currentStep) {
    case 'overview':
      return (
        <div className="space-y-4">
          <Card >
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Target className="w-4 h-4 text-lia-text-secondary" />
                Visão Geral da Triagem
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary">Objetivo:</label>
                  <p className="text-sm text-lia-text-primary bg-lia-bg-secondary p-2 rounded-xl">
                    {screeningData.overview.objective}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary">Duração:</label>
                  <p className="text-sm font-medium text-lia-text-secondary">{screeningData.overview.duration}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary">Critérios de Avaliação:</label>
                  <div className="space-y-1">
                    {screeningData.overview.criteria.map((criterion) => (
                      <div key={criterion.name} className="flex items-center justify-between text-sm">
                        <span>{criterion.name}</span>
                        <Chip variant="neutral">{criterion.weight}%</Chip>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'approach':
      return (
        <div className="space-y-4">
          <Card >
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <MessageSquare className="w-4 h-4 text-status-success" />
                Abordagem e Estrutura
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary">Tom da Conversa:</label>
                  <p className="text-sm text-status-success font-medium">{screeningData.approach.tone}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary">Estrutura:</label>
                  <div className="space-y-2">
                    {screeningData.approach.structure.map((step, index) => (
                      <div key={`step-${index}`} className="flex items-center gap-2 text-sm">
                        <div className="w-5 h-5 bg-status-success/15 rounded-full flex items-center justify-center text-status-success text-xs font-bold">
                          {index + 1}
                        </div>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'questions':
      return (
        <div className="space-y-4">
          <Card >
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Target className="w-4 h-4 text-wedo-purple" />
                Perguntas de Triagem
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    category:"Apresentação Pessoal",
                    questions: ["Conte-me sobre sua trajetória profissional","O que te motivou a se candidatar?"
                    ]
                  },
                  {
                    category:"Experiência Técnica",
                    questions: [
                      `Experiência com ${((jobData as Record<string, unknown>)?.requirements as unknown[])?.[0] || 'tecnologias'}`,"Projeto desafiador recente"
                    ]
                  },
                  {
                    category:"Aderência Cultural",
                    questions: ["Adaptação a ambientes dinâmicos","Como lida com feedback"
                    ]
                  },
                  {
                    category:"Expectativas",
                    questions: [
                      `Vaga ${(jobData as Record<string, unknown>)?.workModel || 'híbrida'} em ${(jobData as Record<string, unknown>)?.location}`,"Expectativa salarial"
                    ]
                  }
                ].map((section) => (
                  <div key={section.category} className="border border-wedo-purple/30 rounded-xl p-3">
                    <h4 className="font-medium text-wedo-purple text-sm mb-2">{section.category}</h4>
                    <div className="space-y-1">
                      {section.questions.map((question, qIndex) => (
                        <div key={qIndex} className="text-xs text-lia-text-secondary">• {question}</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'presentation':
      return (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Star className="w-4 h-4 text-status-warning" />
                Apresentação da Vaga
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-secondary">Empresa:</label>
                  <p className="text-sm text-lia-text-primary bg-status-warning/10 p-2 rounded-md">
                    Líder em inovação tecnológica, focada em soluções impactantes
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-secondary">Vaga:</label>
                  <p className="text-sm text-lia-text-primary bg-status-warning/10 p-2 rounded-md">
                    {jobData?.title} - Projetos desafiadores e de grande impacto
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-secondary">Time:</label>
                  <p className="text-sm text-lia-text-primary bg-status-warning/10 p-2 rounded-md">
                    Equipe multidisciplinar, colaborativa e de excelência
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-secondary">Benefícios:</label>

                  <div className="flex flex-wrap gap-1">
                    {((jobData?.benefits as string[]) || ['Benefícios competitivos']).map((benefit: string) => (
                      <Chip density="relaxed" key={benefit} variant="neutral" muted >{benefit}</Chip>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'feedback':
      return (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Heart className="w-4 h-4 text-wedo-magenta" />
                Estratégia de Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-status-success/10 rounded-md">
                    <div className="text-xs font-medium text-status-success mb-1">Aprovados</div>
                    <div className="text-xs text-status-success">24 horas</div>
                    <div className="text-xs text-status-success mt-1">Tom positivo e próximos passos</div>
                  </div>
                  <div className="p-3 bg-wedo-orange/10 rounded-md">
                    <div className="text-xs font-medium text-wedo-orange mb-1">Não Selecionados</div>
                    <div className="text-xs text-wedo-orange">48 horas</div>
                    <div className="text-xs text-wedo-orange mt-1">Feedback construtivo</div>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-secondary">Diretrizes:</label>
                  <div className="space-y-1 mt-1">
                    {["Sempre construtivo e respeitoso","Destacar pontos fortes","Sugerir desenvolvimento","Manter relacionamento positivo"
                    ].map((guideline, index) => (
                      <div key={`gl-${index}`} className="text-xs text-lia-text-secondary flex items-center gap-1">
                        <Star className="w-3 h-3 text-wedo-magenta" />
                        {guideline}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'timeline':
      return (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-lia-text-secondary" />
                Timeline de Execução
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { step:"Preparação", time:"5 min antes", desc:"Revisar currículo e preparar ambiente" },
                  { step:"Triagem", time:"25-30 min", desc:"Conversa estruturada com candidato" },
                  { step:"Avaliação", time:"10 min após", desc:"Análise e decisão" },
                  { step:"Feedback", time:"24-48h após", desc:"Retorno personalizado" }

                ].map((item, index) => (
                  <div key={item.step} className="flex items-start gap-3 p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">

                    <div className="w-6 h-6 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center text-lia-text-secondary text-xs font-bold">
                      {(index + 1 as React.ReactNode)}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-wedo-cyan-dark">{item.step}</div>
                      <div className="text-xs text-lia-text-secondary">{item.time}</div>
                      <div className="text-xs text-lia-text-secondary">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )

    case 'review':
      return (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-status-success" />
                Roteiro Completo
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center p-4 bg-status-success/10 rounded-xl">
                  <CheckCircle className="w-8 h-8 text-status-success mx-auto mb-2" />
                  <div className="text-sm font-medium text-status-success">Roteiro Criado!</div>
                  <div className="text-xs text-status-success">Para {jobData?.title}</div>
                </div>
                <div className="space-y-2">
                  {["✅ Objetivo e critérios definidos","✅ Abordagem personalizada","✅ Perguntas organizadas","✅ Apresentação da vaga","✅ Estratégia de feedback","✅ Timeline estruturada"
                  ].map((item, index) => (
                    <div key={`ci-${index}`} className="text-xs text-lia-text-secondary">{item}</div>
                  ))}
                </div>
                <div className="pt-3 border-t">
                  <div className="grid grid-cols-2 gap-2">
                    <Button size="sm" variant="outline" className="text-xs">
                      <Download className="w-3 h-3 mr-1" />
                      PDF
                    </Button>
                    <Button size="sm" variant="outline" className="text-xs">
                      <Copy className="w-3 h-3 mr-1" />
                      Template
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )

    default:
      return null
  }
}
