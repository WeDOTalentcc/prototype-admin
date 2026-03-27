"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, Brain, CheckCircle, AlertCircle, Clock, User,
  MessageSquare, Star, Target, Heart, Zap, Award, TrendingUp,
  FileText, Copy, Edit, Download, Share2, ChevronRight,
  Phone, Video, Mail, Calendar, Globe, Users, Briefcase,
  GraduationCap, Code, Palette, Building, MapPin, DollarSign
} from "lucide-react"

interface LiaScreeningGuideProps {
  isOpen: boolean
  onClose: () => void
  job: any
  candidate?: any
}

export function LiaScreeningGuide({ isOpen, onClose, job, candidate }: LiaScreeningGuideProps) {
  const [activeSection, setActiveSection] = useState<'overview' | 'approach' | 'questions' | 'presentation' | 'feedback' | 'timeline'>('overview')
  const [copiedSection, setCopiedSection] = useState<string | null>(null)

  if (!isOpen || !job) return null

  const copyToClipboard = (text: string, section: string) => {
    navigator.clipboard.writeText(text)
    setCopiedSection(section)
    setTimeout(() => setCopiedSection(null), 2000)
  }

  const sections = [
    { id: 'overview', label: 'Visão Geral', icon: Brain },
    { id: 'approach', label: 'Abordagem', icon: MessageSquare },
    { id: 'questions', label: 'Perguntas', icon: Target },
    { id: 'presentation', label: 'Apresentação', icon: Star },
    { id: 'feedback', label: 'Estratégia de Feedback', icon: Heart },
    { id: 'timeline', label: 'Timeline', icon: Clock }
  ]

  // Usar perguntas salvas da vaga ou gerar perguntas default
  const getScreeningQuestions = () => {
    // Se a vaga tem perguntas de triagem salvas, usar elas
    const savedQuestions = job?.screening_questions || job?.screeningQuestions
    
    if (savedQuestions && Array.isArray(savedQuestions) && savedQuestions.length > 0) {
      // Agrupar perguntas salvas por categoria
      const technicalQuestions = savedQuestions.filter((q: any) => 
        q.category === 'technical' || q.type === 'micro_case' || q.type === 'situacional'
      )
      const behavioralQuestions = savedQuestions.filter((q: any) => 
        q.category === 'behavioral' || q.type === 'autodeclaracao_contexto'
      )
      const otherQuestions = savedQuestions.filter((q: any) => 
        !['technical', 'behavioral'].includes(q.category) && 
        !['micro_case', 'situacional', 'autodeclaracao_contexto'].includes(q.type)
      )
      
      const result = []
      
      // Sempre incluir perguntas de apresentação
      result.push({
        category: "Apresentação Pessoal",
        questions: [
          "Conte-me um pouco sobre você e sua trajetória profissional",
          "O que te motivou a se candidatar para esta posição?",
          "Como você ficou sabendo desta oportunidade?"
        ],
        purpose: "Quebrar o gelo e entender motivação inicial"
      })
      
      // Perguntas técnicas/WSI salvas
      if (technicalQuestions.length > 0) {
        result.push({
          category: "Perguntas Técnicas (WSI)",
          questions: technicalQuestions.map((q: any) => q.question || q.text),
          purpose: "Avaliar competências técnicas através de situações reais",
          isWSI: true
        })
      }
      
      // Perguntas comportamentais salvas
      if (behavioralQuestions.length > 0) {
        result.push({
          category: "Perguntas Comportamentais",
          questions: behavioralQuestions.map((q: any) => q.question || q.text),
          purpose: "Avaliar competências comportamentais e soft skills",
          isWSI: true
        })
      }
      
      // Outras perguntas salvas
      if (otherQuestions.length > 0) {
        result.push({
          category: "Perguntas Adicionais",
          questions: otherQuestions.map((q: any) => q.question || q.text),
          purpose: "Perguntas complementares definidas para a vaga"
        })
      }
      
      // Sempre incluir perguntas de logística
      result.push({
        category: "Expectativas e Logística",
        questions: [
          `Esta vaga é ${job?.work_model || job?.workModel || 'híbrida'} em ${job?.location}. Como você se sente em relação a isso?`,
          "Qual sua expectativa salarial para esta posição?",
          "Quando você poderia começar, caso seja selecionado?",
          "Tem alguma dúvida sobre a vaga ou empresa?"
        ],
        purpose: "Alinhar expectativas práticas e logísticas"
      })
      
      return result
    }
    
    // Fallback: perguntas genéricas se não houver perguntas salvas
    return [
      {
        category: "Apresentação Pessoal",
        questions: [
          "Conte-me um pouco sobre você e sua trajetória profissional",
          "O que te motivou a se candidatar para esta posição?",
          "Como você ficou sabendo desta oportunidade?"
        ],
        purpose: "Quebrar o gelo e entender motivação inicial"
      },
      {
        category: "Experiência Técnica",
        questions: job?.requirements?.slice(0, 3).map((req: string) =>
          `Fale sobre sua experiência com ${req}`
        ) || [
          "Descreva um projeto desafiador que você trabalhou recentemente",
          "Como você se mantém atualizado com as tecnologias da área?",
          "Qual foi sua maior conquista profissional?"
        ],
        purpose: "Validar competências técnicas específicas da vaga"
      },
      {
        category: "Fit Cultural",
        questions: [
          "Como você se adapta a ambientes de trabalho dinâmicos?",
          "Descreva como você lida com feedback construtivo",
          "O que você valoriza mais em uma equipe de trabalho?"
        ],
        purpose: "Avaliar alinhamento com cultura organizacional"
      },
      {
        category: "Expectativas e Logística",
        questions: [
          `Esta vaga é ${job?.work_model || job?.workModel || 'híbrida'} em ${job?.location}. Como você se sente em relação a isso?`,
          "Qual sua expectativa salarial para esta posição?",
          "Quando você poderia começar, caso seja selecionado?",
          "Tem alguma dúvida sobre a vaga ou empresa?"
        ],
        purpose: "Alinhar expectativas práticas e logísticas"
      }
    ]
  }

  const screeningQuestions = getScreeningQuestions()

  const approachStrategy = {
    tone: "Profissional, mas acolhedor",
    duration: "20-30 minutos",
    structure: [
      "Apresentação pessoal (2-3 min)",
      "Contexto da vaga (3-5 min)",
      "Perguntas de triagem (15-20 min)",
      "Esclarecimento de dúvidas (3-5 min)",
      "Próximos passos (2 min)"
    ],
    tips: [
      "Mantenha um ritmo conversacional, não interrogatório",
      "Faça anotações discretas durante a conversa",
      "Dê espaço para o candidato fazer perguntas",
      "Observe não apenas as respostas, mas a forma de comunicação"
    ]
  }

  const jobPresentation = {
    company: "Nossa empresa é líder em inovação tecnológica, focada em criar soluções que impactam positivamente a vida das pessoas.",
    role: job?.description || "Buscamos um profissional que se junte ao nosso time para contribuir com projetos desafiadores e de grande impacto.",
    team: "Você fará parte de uma equipe multidisciplinar, colaborativa e sempre em busca da excelência.",
    growth: "Oferecemos um ambiente de crescimento contínuo, com oportunidades de desenvolvimento e aprendizado.",
    benefits: job?.benefits || [
      "Salário competitivo",
      "Benefícios completos",
      "Ambiente colaborativo",
      "Crescimento profissional"
    ]
  }

  const feedbackStrategy = {
    timing: {
      approved: "Feedback positivo em até 24h",
      rejected: "Feedback construtivo em até 48h"
    },
    approvedTemplate: {
      subject: `Próximos passos - ${job?.title}`,
      message: `Olá {NOME},\n\nFicamos muito satisfeitos com nossa conversa sobre a posição de ${job?.title}!\n\nSeu perfil está alinhado com o que buscamos e gostaríamos de dar continuidade ao processo.\n\nPróximo passo: [DEFINIR PRÓXIMA ETAPA]\n\nEm breve entraremos em contato para agendar.\n\nParabéns e até logo!\n\nEquipe de Recrutamento`
    },
    rejectedTemplate: {
      subject: `Feedback sobre processo seletivo - ${job?.title}`,
      message: `Olá {NOME},\n\nObrigado pelo seu interesse na posição de ${job?.title} e pelo tempo dedicado em nossa conversa.\n\nApós análise cuidadosa, decidimos seguir com candidatos cujo perfil está mais alinhado com as necessidades específicas desta vaga no momento.\n\n✨ Pontos fortes identificados:\n{PONTOS_FORTES}\n\n🎯 Áreas de desenvolvimento sugeridas:\n{AREAS_DESENVOLVIMENTO}\n\nSeu perfil ficará em nosso radar para futuras oportunidades que possam ser um match ainda melhor!\n\nDesejamos muito sucesso em sua jornada profissional.\n\nCom carinho,\nEquipe de Recrutamento`
    },
    feedbackGuidelines: [
      "Seja sempre construtivo e respeitoso",
      "Destaque pelo menos 2 pontos fortes do candidato",
      "Ofereça sugestões específicas de desenvolvimento",
      "Mantenha a porta aberta para futuras oportunidades",
      "Use tom empático, mas profissional"
    ]
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-md w-full max-w-6xl max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-status-success/10 dark:bg-status-success/20">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-status-success/15 dark:bg-status-success/20 rounded-md flex items-center justify-center">
              <Brain className="w-6 h-6 text-wedo-cyan" />
            </div>
            <div>
              <h3 className="text-xl font-semibold font-sans text-gray-950 dark:text-gray-50 flex items-center gap-2">
                <Brain className="w-5 h-5 text-status-success" />
                Roteiro de Triagem LIA
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Guia completo para triagem da vaga: {job?.title}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              Exportar PDF
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Share2 className="w-4 h-4" />
              Compartilhar
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex">
          {/* Sidebar Navigation */}
          <div className="w-64 bg-white dark:bg-gray-800 p-4">
            <div className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id as any)}
                  className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors ${
                    activeSection === section.id
                      ? 'bg-status-success/15 dark:bg-status-success/20 text-status-success dark:text-status-success'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  <section.icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{section.label}</span>
                </button>
              ))}
            </div>

            {/* Quick Stats */}
            <div className="mt-6 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <h4 className="text-sm font-medium font-sans text-gray-950 dark:text-gray-50 mb-2">Informações da Vaga</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-800 dark:text-gray-200">Nível:</span>
                  <Badge variant="outline">{job?.level}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-800 dark:text-gray-200">Modalidade:</span>
                  <Badge variant="outline">{job?.workModel}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-800 dark:text-gray-200">Urgência:</span>
                  <div className="flex items-center gap-1">
                    {Array.from({length: 5}).map((_, i) => (
                      <div key={i} className={`w-2 h-2 rounded-full ${
                        i < (job?.urgencyLevel || 3) ? 'bg-status-error' : 'bg-gray-300'
                      }`} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6">
            {/* Overview Section */}
            {activeSection === 'overview' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50 mb-4">Visão Geral do Processo</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card className="">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          Objetivo da Triagem
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-800 dark:text-gray-200">
                          Validar fit inicial do candidato com a vaga, avaliar competências básicas e motivação,
                          além de esclarecer expectativas mútuas antes de avançar no processo.
                        </p>
                      </CardContent>
                    </Card>

                    <Card className="">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <Clock className="w-4 h-4 text-status-success" />
                          Duração Sugerida
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-800 dark:text-gray-200">
                          20-30 minutos para uma conversa completa, incluindo apresentação da empresa,
                          perguntas de triagem e esclarecimento de dúvidas.
                        </p>
                      </CardContent>
                    </Card>

                    <Card className="">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <Users className="w-4 h-4 text-wedo-purple" />
                          Critérios de Avaliação
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between">
                            <span>Competências Técnicas</span>
                            <Badge variant="outline">40%</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Fit Cultural</span>
                            <Badge variant="outline">30%</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Motivação</span>
                            <Badge variant="outline">20%</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Expectativas</span>
                            <Badge variant="outline">10%</Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <CheckCircle className="w-4 h-4 text-wedo-orange" />
                          Resultado Esperado
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-800 dark:text-gray-200">
                          Decisão clara sobre prosseguir com o candidato, com feedback estruturado
                          e próximos passos bem definidos.
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Key Requirements Checklist */}
                <div>
                  <h5 className="font-medium font-sans text-gray-950 dark:text-gray-50 mb-3">Checklist de Requisitos Essenciais</h5>
                  <div className="space-y-2">
                    {job?.requirements?.map((requirement: string, index: number) => (
                      <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <input type="checkbox" className="rounded" />
                        <span className="text-sm text-gray-800 dark:text-gray-200">{requirement}</span>
                      </div>
                    )) || (
                      <div className="text-sm text-gray-600">Nenhum requisito específico definido</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Approach Section */}
            {activeSection === 'approach' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50 mb-4">Estratégia de Abordagem</h4>

                  <Card className="mb-6">
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2 font-sans">
                        <MessageSquare className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        Tom e Postura
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
 <div className="text-sm font-medium text-gray-600">Tom</div>
 <div className="text-xs text-gray-600">{approachStrategy.tone}</div>
                        </div>
                        <div className="text-center p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                          <div className="text-sm font-medium text-status-success dark:text-status-success">Duração</div>
                          <div className="text-xs text-status-success dark:text-status-success">{approachStrategy.duration}</div>
                        </div>
                        <div className="text-center p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                          <div className="text-sm font-medium text-wedo-purple dark:text-wedo-purple">Formato</div>
                          <div className="text-xs text-wedo-purple dark:text-wedo-purple">Conversa estruturada</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="">
                      <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <Target className="w-4 h-4 text-status-success" />
                          Estrutura da Conversa
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {approachStrategy.structure.map((step, index) => (
                            <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded">
                              <div className="w-6 h-6 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center text-status-success text-xs font-bold">
                                {index + 1}
                              </div>
                              <span className="text-sm text-gray-800 dark:text-gray-200">{step}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="">
                      <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2 font-sans">
                          <Zap className="w-4 h-4 text-status-warning" />
                          Dicas Importantes
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {approachStrategy.tips.map((tip, index) => (
                            <div key={index} className="flex items-start gap-2">
                              <Star className="w-3 h-3 text-status-warning mt-1 flex-shrink-0" />
                              <span className="text-sm text-gray-800 dark:text-gray-200">{tip}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Script de Abertura */}
                <Card className="">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2 font-sans">
                      <MessageSquare className="w-4 h-4 text-status-success" />
                      Script de Abertura
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(
                        `Olá ${candidate?.name || '[Nome]'}! Como está? Muito obrigado pelo interesse na nossa vaga de ${job?.title}.\n\nSou [SEU NOME] da equipe de recrutamento. Esta é uma conversa inicial para nos conhecermos melhor e eu te contar mais sobre a oportunidade.\n\nTem cerca de 20-30 minutos para conversarmos? Perfeito!`,
                        'opening'
                      )}
                      className="gap-2"
                    >
                      <Copy className="w-3 h-3" />
                      {copiedSection === 'opening' ? 'Copiado!' : 'Copiar'}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                      <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                        "Olá <strong>{candidate?.name || '[Nome]'}</strong>! Como está? Muito obrigado pelo interesse na nossa vaga de <strong>{job?.title}</strong>.
                        <br /><br />
                        Sou <strong>[SEU NOME]</strong> da equipe de recrutamento. Esta é uma conversa inicial para nos conhecermos melhor e eu te contar mais sobre a oportunidade.
                        <br /><br />
                        Tem cerca de 20-30 minutos para conversarmos? Perfeito!"
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Questions Section */}
            {activeSection === 'questions' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold text-gray-950 dark:text-gray-50">Perguntas de Triagem</h4>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Edit className="w-3 h-3" />
                    Personalizar
                  </Button>
                </div>

                <div className="space-y-6">
                  {screeningQuestions.map((section, sectionIndex) => (
                    <Card key={sectionIndex}>
                      <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          {section.category}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {section.questions.length} perguntas
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyToClipboard(
                              section.questions.join('\n'),
                              `questions-${sectionIndex}`
                            )}
                            className="gap-1"
                          >
                            <Copy className="w-3 h-3" />
                            {copiedSection === `questions-${sectionIndex}` ? 'Copiado!' : 'Copiar'}
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
 <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600">
                            <strong>Objetivo:</strong> {section.purpose}
                          </div>
                          <div className="space-y-2">
                            {section.questions.map((question: string, questionIndex: number) => (
                              <div key={questionIndex} className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-md">
                                <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-400 text-xs font-bold flex-shrink-0">
                                  {questionIndex + 1}
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm text-gray-800 dark:text-gray-200">{question}</p>
                                  <textarea
                                    placeholder="Anotações da resposta..."
                                    className="w-full mt-2 p-2 border border-gray-200 dark:border-gray-600 rounded text-xs bg-gray-50 dark:bg-gray-800"
                                    rows={2}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Avaliação Final */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-status-success" />
                      Avaliação Final
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                          Recomendação Geral
                        </label>
                        <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded text-sm">
                          <option value="">Selecione...</option>
                          <option value="aprovado">✅ Aprovado - Prosseguir</option>
                          <option value="condicional">⚠️ Aprovado com ressalvas</option>
                          <option value="reprovado">❌ Não aprovado</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                          Nível de Confiança
                        </label>
                        <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded text-sm">
                          <option value="">Selecione...</option>
                          <option value="alta">🔥 Alta confiança</option>
                          <option value="media">🎯 Média confiança</option>
                          <option value="baixa">⚡ Baixa confiança</option>
                        </select>
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                        Observações e Próximos Passos
                      </label>
                      <textarea
                        placeholder="Resumo da conversa, pontos de atenção, recomendações para próximas etapas..."
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded text-sm"
                        rows={4}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Presentation Section */}
            {activeSection === 'presentation' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold text-gray-950 dark:text-gray-50">Apresentação da Vaga e Empresa</h4>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(
                      `${jobPresentation.company}\n\n${jobPresentation.role}\n\n${jobPresentation.team}\n\n${jobPresentation.growth}`,
                      'presentation'
                    )}
                    className="gap-2"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedSection === 'presentation' ? 'Copiado!' : 'Copiar Apresentação'}
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Building className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        Sobre a Empresa
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {jobPresentation.company}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-status-success" />
                        Sobre a Vaga
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {jobPresentation.role}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Users className="w-4 h-4 text-wedo-purple" />
                        Sobre o Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {jobPresentation.team}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-wedo-orange" />
                        Crescimento
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {jobPresentation.growth}
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Job Details */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Star className="w-4 h-4 text-status-warning" />
                      Detalhes da Posição
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                        <MapPin className="w-5 h-5 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
 <div className="text-sm font-medium text-gray-600">Local</div>
 <div className="text-xs text-gray-600">{job?.location}</div>
                      </div>
                      <div className="text-center p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                        <Globe className="w-5 h-5 text-status-success mx-auto mb-1" />
                        <div className="text-sm font-medium text-status-success dark:text-status-success">Modalidade</div>
                        <div className="text-xs text-status-success dark:text-status-success">{job?.workModel}</div>
                      </div>
                      <div className="text-center p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                        <Award className="w-5 h-5 text-wedo-purple mx-auto mb-1" />
                        <div className="text-sm font-medium text-wedo-purple dark:text-wedo-purple">Nível</div>
                        <div className="text-xs text-wedo-purple dark:text-wedo-purple">{job?.level}</div>
                      </div>
                      <div className="text-center p-3 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md">
                        <DollarSign className="w-5 h-5 text-wedo-orange mx-auto mb-1" />
                        <div className="text-sm font-medium text-wedo-orange dark:text-wedo-orange">Salário</div>
                        <div className="text-xs text-wedo-orange dark:text-wedo-orange">{job?.salary}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Benefits */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Heart className="w-4 h-4 text-wedo-magenta" />
                      Benefícios e Vantagens
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {jobPresentation.benefits.map((benefit: string, index: number) => (
                        <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <CheckCircle className="w-4 h-4 text-status-success" />
                          <span className="text-sm text-gray-800 dark:text-gray-200">{benefit}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Script de Apresentação */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-status-success" />
                      Script de Apresentação
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(
                        `Deixe eu te contar um pouco sobre nós e sobre esta oportunidade.\n\n${jobPresentation.company}\n\nPara esta posição de ${job?.title}, ${jobPresentation.role}\n\n${jobPresentation.team}\n\n${jobPresentation.growth}\n\nO que mais te chama atenção nesta oportunidade?`,
                        'presentation-script'
                      )}
                      className="gap-2"
                    >
                      <Copy className="w-3 h-3" />
                      {copiedSection === 'presentation-script' ? 'Copiado!' : 'Copiar'}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
                      <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                        "Deixe eu te contar um pouco sobre nós e sobre esta oportunidade.
                        <br /><br />
                        <strong>{jobPresentation.company}</strong>
                        <br /><br />
                        Para esta posição de <strong>{job?.title}</strong>, {jobPresentation.role}
                        <br /><br />
                        <strong>{jobPresentation.team}</strong>
                        <br /><br />
                        <strong>{jobPresentation.growth}</strong>
                        <br /><br />
                        O que mais te chama atenção nesta oportunidade?"
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Feedback Strategy Section */}
            {activeSection === 'feedback' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-950 dark:text-gray-50 mb-4">Estratégia de Feedback</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    Diretrizes para fornecer feedback construtivo e manter relacionamento positivo com todos os candidatos
                  </p>
                </div>

                {/* Timing */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Timeline de Feedback
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md border border-status-success/30">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-4 h-4 text-status-success" />
                          <span className="font-medium text-status-success dark:text-status-success">Candidatos Aprovados</span>
                        </div>
                        <p className="text-sm text-status-success dark:text-status-success">
                          {feedbackStrategy.timing.approved}
                        </p>
                      </div>
                      <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md border border-wedo-orange/30">
                        <div className="flex items-center gap-2 mb-2">
                          <Heart className="w-4 h-4 text-wedo-orange" />
                          <span className="font-medium text-wedo-orange dark:text-wedo-orange">Candidatos Não Selecionados</span>
                        </div>
                        <p className="text-sm text-wedo-orange dark:text-wedo-orange">
                          {feedbackStrategy.timing.rejected}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Approved Template */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-status-success" />
                      Template - Candidatos Aprovados
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(
                        `Assunto: ${feedbackStrategy.approvedTemplate.subject}\n\n${feedbackStrategy.approvedTemplate.message}`,
                        'approved-template'
                      )}
                      className="gap-2"
                    >
                      <Copy className="w-3 h-3" />
                      {copiedSection === 'approved-template' ? 'Copiado!' : 'Copiar'}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Assunto:</label>
                        <div className="p-2 bg-status-success/10 dark:bg-status-success/20 rounded text-sm text-status-success dark:text-status-success">
                          {feedbackStrategy.approvedTemplate.subject}
                        </div>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Mensagem:</label>
                        <div className="p-3 bg-status-success/10 dark:bg-status-success/20 rounded text-sm text-status-success dark:text-status-success whitespace-pre-line">
                          {feedbackStrategy.approvedTemplate.message}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Rejected Template */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Heart className="w-4 h-4 text-wedo-orange" />
                      Template - Feedback Construtivo
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(
                        `Assunto: ${feedbackStrategy.rejectedTemplate.subject}\n\n${feedbackStrategy.rejectedTemplate.message}`,
                        'rejected-template'
                      )}
                      className="gap-2"
                    >
                      <Copy className="w-3 h-3" />
                      {copiedSection === 'rejected-template' ? 'Copiado!' : 'Copiar'}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Assunto:</label>
                        <div className="p-2 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded text-sm text-wedo-orange dark:text-wedo-orange">
                          {feedbackStrategy.rejectedTemplate.subject}
                        </div>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Mensagem:</label>
                        <div className="p-3 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded text-sm text-wedo-orange dark:text-wedo-orange whitespace-pre-line">
                          {feedbackStrategy.rejectedTemplate.message}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Guidelines */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Star className="w-4 h-4 text-status-warning" />
                      Diretrizes para Feedback Construtivo
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {feedbackStrategy.feedbackGuidelines.map((guideline, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-status-warning/10 rounded-md">
                          <Star className="w-4 h-4 text-status-warning mt-0.5" />
                          <span className="text-sm text-status-warning dark:text-status-warning">{guideline}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Feedback Form */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Edit className="w-4 h-4 text-wedo-purple" />
                      Formulário de Feedback Personalizado
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                          Pontos Fortes Identificados
                        </label>
                        <textarea
                          placeholder="Ex: Excelente comunicação, conhecimento técnico sólido em React..."
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded text-sm"
                          rows={3}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                          Áreas de Desenvolvimento Sugeridas
                        </label>
                        <textarea
                          placeholder="Ex: Aprofundar conhecimentos em TypeScript, ganhar experiência em liderança..."
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded text-sm"
                          rows={3}
                        />
                      </div>
                      <div className="flex gap-3">
                        <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
                          Gerar Feedback Personalizado
                        </Button>
                        <Button variant="outline" className="gap-2">
                          <Brain className="w-4 h-4 text-wedo-cyan" />
                          LIA Sugerir
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Timeline Section */}
            {activeSection === 'timeline' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-950 dark:text-gray-50 mb-4">Timeline do Processo</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    Cronograma sugerido para execução eficiente da triagem e próximos passos
                  </p>
                </div>

                {/* Process Timeline */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Cronograma de Execução
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-400 text-sm font-bold">
                          1
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-950 dark:text-gray-50">Preparação (5 min antes)</div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Revisar currículo, preparar perguntas específicas, configurar ambiente</p>
                        </div>
                        <Badge variant="outline" className="text-xs">5 min</Badge>
                      </div>

                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center text-status-success text-sm font-bold">
                          2
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-950 dark:text-gray-50">Triagem (20-30 min)</div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Execução da conversa seguindo roteiro estruturado</p>
                        </div>
                        <Badge variant="outline" className="text-xs">25 min</Badge>
                      </div>

                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 bg-wedo-purple/15 dark:bg-wedo-purple/20 rounded-full flex items-center justify-center text-wedo-purple text-sm font-bold">
                          3
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-950 dark:text-gray-50">Avaliação (5-10 min após)</div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Análise das respostas, decisão e anotações</p>
                        </div>
                        <Badge variant="outline" className="text-xs">10 min</Badge>
                      </div>

                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 bg-wedo-orange/15 dark:bg-wedo-orange/10/20 rounded-full flex items-center justify-center text-wedo-orange text-sm font-bold">
                          4
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-950 dark:text-gray-50">Feedback (24-48h após)</div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Envio de retorno personalizado ao candidato</p>
                        </div>
                        <Badge variant="outline" className="text-xs">1-2 dias</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Next Steps */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <ChevronRight className="w-4 h-4 text-status-success" />
                      Próximos Passos Possíveis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md border border-status-success/30">
                        <div className="font-medium text-status-success dark:text-status-success mb-2">Se Aprovado</div>
                        <div className="space-y-1 text-sm text-status-success dark:text-status-success">
                          <div>• Entrevista técnica detalhada</div>
                          <div>• Apresentação de case/portfolio</div>
                          <div>• Conversa com futuro gestor</div>
                          <div>• Verificação de referências</div>
                        </div>
                      </div>
                      <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md border border-wedo-orange/30">
                        <div className="font-medium text-wedo-orange dark:text-wedo-orange mb-2">Se Não Aprovado</div>
                        <div className="space-y-1 text-sm text-wedo-orange dark:text-wedo-orange">
                          <div>• Feedback construtivo personalizado</div>
                          <div>• Inclusão no banco de talentos</div>
                          <div>• Convite para vagas futuras</div>
                          <div>• Manutenção do relacionamento</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Checklist */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-wedo-purple" />
                      Checklist Pós-Triagem
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        "Preencher avaliação na plataforma",
                        "Atualizar status do candidato",
                        "Enviar feedback personalizado",
                        "Agendar próxima etapa (se aprovado)",
                        "Documentar insights para equipe",
                        "Atualizar pipeline de candidatos"
                      ].map((item, index) => (
                        <div key={index} className="flex items-center gap-3">
                          <input type="checkbox" className="rounded border-gray-300" />
                          <span className="text-sm text-gray-800 dark:text-gray-200">{item}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-status-success/15 text-status-success">
                Roteiro Personalizado para {job?.title}
              </Badge>
              <Badge variant="outline" className="text-xs">
                Gerado pela LIA
              </Badge>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <FileText className="w-4 h-4" />
                Salvar Roteiro
              </Button>
              <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Iniciar Triagem
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
