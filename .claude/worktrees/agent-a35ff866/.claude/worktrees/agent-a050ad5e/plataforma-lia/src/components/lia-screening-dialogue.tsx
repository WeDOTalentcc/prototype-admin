"use client"

import React, { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, Brain, CheckCircle, AlertCircle, Clock, User,
  MessageSquare, Star, Target, Heart, Zap, Award, TrendingUp,
  FileText, Copy, Edit, Download, Share2, ChevronRight,
  Phone, Video, Mail, Calendar, Globe, Users, Briefcase,
  GraduationCap, Code, Palette, Building, MapPin, DollarSign,
  Send, Loader2, ArrowRight, Settings, Plus, Trash2
} from "lucide-react"

interface LiaScreeningDialogueProps {
  isOpen: boolean
  onClose: () => void
  jobData: any
  onComplete: (screeningData: any) => void
}

interface Message {
  id: string
  sender: 'user' | 'lia'
  content: string
  timestamp: Date
  type?: 'text' | 'options' | 'confirmation'
  options?: string[]
  data?: any
}

interface ScreeningData {
  overview: {
    objective: string
    duration: string
    criteria: { name: string; weight: number }[]
  }
  approach: {
    tone: string
    structure: string[]
    guidelines: string[]
  }
  questions: {
    category: string
    questions: string[]
    purpose: string
  }[]
  presentation: {
    company: string
    role: string
    team: string
    benefits: string[]
  }
  feedback: {
    approvedTiming: string
    rejectedTiming: string
    approvedTemplate: string
    rejectedTemplate: string
    guidelines: string[]
  }
  timeline: {
    preparation: string
    screening: string
    evaluation: string
    feedback: string
  }
}

export function LiaScreeningDialogue({ isOpen, onClose, jobData, onComplete }: LiaScreeningDialogueProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentInput, setCurrentInput] = useState("")
  const [isLiaTyping, setIsLiaTyping] = useState(false)
  const [currentStep, setCurrentStep] = useState<'overview' | 'approach' | 'questions' | 'presentation' | 'feedback' | 'timeline' | 'review'>('overview')
  const [screeningData, setScreeningData] = useState<ScreeningData>({
    overview: {
      objective: "Validar fit inicial do candidato com a vaga, avaliar competências básicas e motivação",
      duration: "25-30 minutos",
      criteria: [
        { name: "Competências Técnicas", weight: 40 },
        { name: "Fit Cultural", weight: 30 },
        { name: "Motivação", weight: 20 },
        { name: "Expectativas", weight: 10 }
      ]
    },
    approach: {
      tone: "Profissional, mas acolhedor",
      structure: [
        "Apresentação pessoal (2-3 min)",
        "Contexto da vaga (3-5 min)",
        "Perguntas de triagem (15-20 min)",
        "Esclarecimento de dúvidas (3-5 min)",
        "Próximos passos (2 min)"
      ],
      guidelines: [
        "Mantenha um ritmo conversacional, não interrogatório",
        "Faça anotações discretas durante a conversa",
        "Dê espaço para o candidato fazer perguntas",
        "Observe não apenas as respostas, mas a forma de comunicação"
      ]
    },
    questions: [],
    presentation: {
      company: "",
      role: "",
      team: "",
      benefits: []
    },
    feedback: {
      approvedTiming: "24 horas",
      rejectedTiming: "48 horas",
      approvedTemplate: "",
      rejectedTemplate: "",
      guidelines: []
    },
    timeline: {
      preparation: "5 min antes",
      screening: "25-30 min",
      evaluation: "10 min após",
      feedback: "24-48h após"
    }
  })
  const [showCompanySettings, setShowCompanySettings] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      initializeConversation()
    }
  }, [isOpen, messages.length])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const addMessage = (content: string, sender: 'user' | 'lia', type: 'text' | 'options' | 'confirmation' = 'text', options?: string[], data?: any) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      content,
      timestamp: new Date(),
      type,
      options,
      data
    }
    setMessages(prev => [...prev, newMessage])
  }

  const initializeConversation = () => {
    addMessage(
      `Olá! Vou te ajudar a criar um roteiro de triagem personalizado para a vaga de **${jobData?.title || 'Nova Vaga'}**.

Antes de começarmos, você gostaria de usar as configurações padrão da empresa como base?`,
      'lia',
      'options',
      ['Usar configurações da empresa', 'Criar do zero', 'Ver configurações']
    )
  }

  const handleSendMessage = async () => {
    if (!currentInput.trim()) return

    const userMessage = currentInput
    addMessage(userMessage, 'user')
    setCurrentInput("")
    setIsLiaTyping(true)

    // Simulate LIA processing time
    setTimeout(() => {
      processLiaResponse(userMessage)
      setIsLiaTyping(false)
    }, 1500)
  }

  const handleOptionSelect = async (option: string) => {
    addMessage(option, 'user')
    setIsLiaTyping(true)

    setTimeout(() => {
      processLiaResponse(option)
      setIsLiaTyping(false)
    }, 1000)
  }

  const processLiaResponse = (userInput: string) => {
    switch (currentStep) {
      case 'overview':
        if (userInput.includes('configurações da empresa')) {
          addMessage(
            `Perfeito! Vou usar as configurações padrão da empresa como base e personalizá-las para esta vaga.

**Objetivo da Triagem:**
Validar fit inicial do candidato com a vaga, avaliar competências básicas e motivação, além de esclarecer expectativas mútuas.

**Duração Sugerida:** 25-30 minutos

**Critérios de Avaliação:**
• Competências Técnicas (40%)
• Fit Cultural (30%)
• Motivação (20%)
• Expectativas (10%)

Quer ajustar alguma dessas configurações ou podemos prosseguir?`,
            'lia',
            'options',
            ['Ajustar objetivo', 'Ajustar duração', 'Ajustar critérios', 'Prosseguir']
          )
        } else if (userInput.includes('Criar do zero')) {
          addMessage(
            `Ótimo! Vamos criar um roteiro completamente personalizado.

Primeiro, me conte: **qual é o principal objetivo desta triagem?**

Por exemplo:
• Validar conhecimentos técnicos específicos
• Avaliar fit cultural e comportamental
• Triagem rápida para alto volume
• Avaliação aprofundada para posição crítica`,
            'lia'
          )
        } else if (userInput.includes('Ver configurações')) {
          setShowCompanySettings(true)
          addMessage(
            `Vou abrir as configurações da empresa para você. Depois que revisar, me diga como quer prosseguir.`,
            'lia',
            'options',
            ['Usar configurações', 'Personalizar', 'Criar do zero']
          )
        } else if (userInput.includes('Prosseguir')) {
          setCurrentStep('approach')
          addMessage(
            `Excelente! Agora vamos definir a **abordagem e tom** da conversa.

Com base na vaga de ${jobData?.title}, sugiro:

**Tom:** Profissional, mas acolhedor
**Duração:** 25-30 minutos

**Estrutura sugerida:**
1. Apresentação pessoal (2-3 min)
2. Contexto da vaga (3-5 min)
3. Perguntas de triagem (15-20 min)
4. Esclarecimento de dúvidas (3-5 min)
5. Próximos passos (2 min)

Esta estrutura funciona para você?`,
            'lia',
            'options',
            ['Perfeita!', 'Ajustar tom', 'Ajustar estrutura', 'Personalizar']
          )
        }
        break

      case 'approach':
        if (userInput.includes('Perfeita')) {
          setCurrentStep('questions')
          addMessage(
            `Ótimo! Agora vamos criar as **perguntas de triagem**.

Baseado nos requisitos da vaga (${jobData?.requirements?.slice(0, 3).join(', ') || 'requisitos técnicos'}), sugiro organizar em 4 categorias:

**1. Apresentação Pessoal**
• Conte-me sobre sua trajetória profissional
• O que te motivou a se candidatar?

**2. Experiência Técnica**
• Fale sobre sua experiência com ${jobData?.requirements?.[0] || 'tecnologias relevantes'}
• Descreva um projeto desafiador recente

**3. Fit Cultural**
• Como você se adapta a ambientes dinâmicos?
• Como lida com feedback?

**4. Expectativas**
• Esta vaga é ${jobData?.workModel || 'híbrida'} em ${jobData?.location || 'localização'}. Como se sente?
• Qual sua expectativa salarial?

Quer personalizar alguma categoria?`,
            'lia',
            'options',
            ['Adicionar categoria', 'Editar perguntas', 'Personalizar por categoria', 'Prosseguir']
          )
        }
        break

      case 'questions':
        if (userInput.includes('Prosseguir')) {
          setCurrentStep('presentation')
          addMessage(
            `Perfeito! Agora vamos preparar a **apresentação da vaga e empresa**.

**Sobre a Empresa:**
Nossa empresa é líder em inovação tecnológica, focada em criar soluções que impactam positivamente a vida das pessoas.

**Sobre a Vaga:**
Para a posição de ${jobData?.title}, buscamos um profissional que se junte ao nosso time para contribuir com projetos desafiadores e de grande impacto.

**Sobre o Time:**
Você fará parte de uma equipe multidisciplinar, colaborativa e sempre em busca da excelência.

**Benefícios:**
${jobData?.benefits?.join(', ') || 'Benefícios competitivos'}

Quer personalizar alguma dessas seções?`,
            'lia',
            'options',
            ['Editar empresa', 'Editar vaga', 'Editar benefícios', 'Prosseguir']
          )
        }
        break

      case 'presentation':
        if (userInput.includes('Prosseguir')) {
          setCurrentStep('feedback')
          addMessage(
            `Excelente! Agora a parte mais importante: **estratégia de feedback**.

**Para candidatos APROVADOS:**
• Timing: 24 horas
• Tom: Positivo e entusiasmado
• Próximos passos claros

**Para candidatos NÃO SELECIONADOS:**
• Timing: 48 horas
• Feedback construtivo incluindo:
  - Pontos fortes identificados
  - Áreas de desenvolvimento sugeridas
  - Manter porta aberta para futuras oportunidades

**Diretrizes:**
• Sempre construtivo e respeitoso
• Destacar pelo menos 2 pontos fortes
• Oferecer sugestões específicas
• Manter relacionamento positivo

Esta abordagem está alinhada com a cultura da empresa?`,
            'lia',
            'options',
            ['Perfeita!', 'Ajustar timing', 'Personalizar templates', 'Adicionar diretrizes']
          )
        }
        break

      case 'feedback':
        if (userInput.includes('Perfeita')) {
          setCurrentStep('timeline')
          addMessage(
            `Ótimo! Por último, vamos definir o **timeline de execução**:

**1. Preparação (5 min antes)**
• Revisar currículo do candidato
• Preparar perguntas específicas
• Configurar ambiente (presencial/online)

**2. Triagem (25-30 min)**
• Executar conversa seguindo roteiro
• Fazer anotações durante conversa

**3. Avaliação (10 min após)**
• Análise das respostas
• Decisão e documentação
• Preenchimento da avaliação

**4. Feedback (24-48h após)**
• Envio de retorno personalizado
• Atualização do status no sistema

Este cronograma funciona para sua rotina?`,
            'lia',
            'options',
            ['Perfeito!', 'Ajustar tempos', 'Adicionar etapa', 'Finalizar roteiro']
          )
        }
        break

      case 'timeline':
        if (userInput.includes('Perfeito') || userInput.includes('Finalizar')) {
          setCurrentStep('review')
          addMessage(
            `🎉 **Roteiro de Triagem Criado com Sucesso!**

Seu roteiro personalizado para a vaga de **${jobData?.title}** está pronto!

**Resumo:**
✅ Objetivo definido e critérios estabelecidos
✅ Abordagem e estrutura personalizadas
✅ Perguntas organizadas por categoria
✅ Apresentação da empresa e vaga
✅ Estratégia de feedback construtivo
✅ Timeline de execução estruturada

O roteiro está sendo gerado no painel ao lado. Você pode:
• Revisar e editar qualquer seção
• Exportar como PDF
• Salvar como template
• Iniciar triagem imediatamente

Está satisfeito com o resultado?`,
            'lia',
            'options',
            ['Perfeito! Salvar', 'Revisar seções', 'Criar template', 'Exportar PDF']
          )
        }
        break

      case 'review':
        if (userInput.includes('Salvar')) {
          addMessage(
            `✅ **Roteiro salvo com sucesso!**

O roteiro está agora disponível para esta vaga e pode ser acessado a qualquer momento.

Quando estiver pronto para fazer triagens, o roteiro completo aparecerá automaticamente com:
• Scripts prontos para usar
• Perguntas personalizadas
• Templates de feedback
• Checklist de execução

Boa sorte com as triagens! 🚀`,
            'lia'
          )

          // Complete the process
          setTimeout(() => {
            onComplete(screeningData)
          }, 2000)
        }
        break
    }
  }

  const renderRightPanel = () => {
    switch (currentStep) {
      case 'overview':
        return (
          <div className="space-y-4">
            <Card className="">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2 font-sans">
                  <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Visão Geral da Triagem
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Objetivo:</label>
                    <p className="text-sm text-gray-800 dark:text-gray-200 bg-gray-50 p-2 rounded">
                      {screeningData.overview.objective}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Duração:</label>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{screeningData.overview.duration}</p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Critérios de Avaliação:</label>
                    <div className="space-y-1">
                      {screeningData.overview.criteria.map((criterion, index) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span>{criterion.name}</span>
                          <Badge variant="outline">{criterion.weight}%</Badge>
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
            <Card className="">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2 font-sans">
                  <MessageSquare className="w-4 h-4 text-green-600" />
                  Abordagem e Estrutura
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Tom da Conversa:</label>
                    <p className="text-sm text-green-700 font-medium">{screeningData.approach.tone}</p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Estrutura:</label>
                    <div className="space-y-2">
                      {screeningData.approach.structure.map((step, index) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                          <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-xs font-bold">
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
            <Card className="">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2 font-sans">
                  <Target className="w-4 h-4 text-purple-600" />
                  Perguntas de Triagem
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    {
                      category: "Apresentação Pessoal",
                      questions: [
                        "Conte-me sobre sua trajetória profissional",
                        "O que te motivou a se candidatar?"
                      ]
                    },
                    {
                      category: "Experiência Técnica",
                      questions: [
                        `Experiência com ${jobData?.requirements?.[0] || 'tecnologias'}`,
                        "Projeto desafiador recente"
                      ]
                    },
                    {
                      category: "Fit Cultural",
                      questions: [
                        "Adaptação a ambientes dinâmicos",
                        "Como lida com feedback"
                      ]
                    },
                    {
                      category: "Expectativas",
                      questions: [
                        `Vaga ${jobData?.workModel || 'híbrida'} em ${jobData?.location}`,
                        "Expectativa salarial"
                      ]
                    }
                  ].map((section, index) => (
                    <div key={index} className="border border-purple-200 rounded-md p-3">
                      <h4 className="font-medium text-purple-800 text-sm mb-2">{section.category}</h4>
                      <div className="space-y-1">
                        {section.questions.map((question, qIndex) => (
                          <div key={qIndex} className="text-xs text-gray-600">• {question}</div>
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
                  <Star className="w-4 h-4 text-yellow-600" />
                  Apresentação da Vaga
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-gray-600">Empresa:</label>
                    <p className="text-sm text-gray-800 dark:text-gray-200 bg-yellow-50 p-2 rounded">
                      Líder em inovação tecnológica, focada em soluções impactantes
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Vaga:</label>
                    <p className="text-sm text-gray-800 dark:text-gray-200 bg-yellow-50 p-2 rounded">
                      {jobData?.title} - Projetos desafiadores e de grande impacto
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Time:</label>
                    <p className="text-sm text-gray-800 dark:text-gray-200 bg-yellow-50 p-2 rounded">
                      Equipe multidisciplinar, colaborativa e de excelência
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Benefícios:</label>
                    <div className="flex flex-wrap gap-1">
                      {(jobData?.benefits || ['Benefícios competitivos']).map((benefit: string, index: number) => (
                        <Badge key={index} variant="secondary" className="text-xs">{benefit}</Badge>
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
                  <Heart className="w-4 h-4 text-pink-600" />
                  Estratégia de Feedback
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-green-50 rounded-md">
                      <div className="text-xs font-medium text-green-800 mb-1">Aprovados</div>
                      <div className="text-xs text-green-600">24 horas</div>
                      <div className="text-xs text-green-700 mt-1">Tom positivo e próximos passos</div>
                    </div>
                    <div className="p-3 bg-orange-50 rounded-md">
                      <div className="text-xs font-medium text-orange-800 mb-1">Não Selecionados</div>
                      <div className="text-xs text-orange-600">48 horas</div>
                      <div className="text-xs text-orange-700 mt-1">Feedback construtivo</div>
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Diretrizes:</label>
                    <div className="space-y-1 mt-1">
                      {[
                        "Sempre construtivo e respeitoso",
                        "Destacar pontos fortes",
                        "Sugerir desenvolvimento",
                        "Manter relacionamento positivo"
                      ].map((guideline, index) => (
                        <div key={index} className="text-xs text-gray-600 flex items-center gap-1">
                          <Star className="w-3 h-3 text-pink-500" />
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
                  <Clock className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Timeline de Execução
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { step: "Preparação", time: "5 min antes", desc: "Revisar currículo e preparar ambiente" },
                    { step: "Triagem", time: "25-30 min", desc: "Conversa estruturada com candidato" },
                    { step: "Avaliação", time: "10 min após", desc: "Análise e decisão" },
                    { step: "Feedback", time: "24-48h após", desc: "Retorno personalizado" }
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3 p-2 bg-gray-100 dark:bg-gray-800 rounded">
                      <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-400 text-xs font-bold">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-wedo-cyan-dark">{item.step}</div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">{item.time}</div>
                        <div className="text-xs text-gray-600">{item.desc}</div>
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
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Roteiro Completo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="text-center p-4 bg-green-50 rounded-md">
                    <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <div className="text-sm font-medium text-green-800">Roteiro Criado!</div>
                    <div className="text-xs text-green-600">Para {jobData?.title}</div>
                  </div>
                  <div className="space-y-2">
                    {[
                      "✅ Objetivo e critérios definidos",
                      "✅ Abordagem personalizada",
                      "✅ Perguntas organizadas",
                      "✅ Apresentação da vaga",
                      "✅ Estratégia de feedback",
                      "✅ Timeline estruturada"
                    ].map((item, index) => (
                      <div key={index} className="text-xs text-gray-600">{item}</div>
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-md w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-600 rounded-md flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">
                Construção de Roteiro de Triagem
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                {jobData?.title} • Criando roteiro personalizado
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowCompanySettings(true)}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${
                    message.sender === 'user'
                      ? 'bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 rounded-l-2xl rounded-tr-2xl'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-950 dark:text-gray-50 rounded-r-2xl rounded-tl-2xl'
                  } p-3`}>
                    <div className="text-sm whitespace-pre-line">{message.content}</div>

                    {message.type === 'options' && message.options && (
                      <div className="mt-3 space-y-2">
                        {message.options.map((option, index) => (
                          <button
                            key={index}
                            onClick={() => handleOptionSelect(option)}
                            className="block w-full text-left p-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm transition-colors"
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLiaTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-r-2xl rounded-tl-2xl p-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-green-600" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">LIA está digitando...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={currentInput}
                    onChange={(e) => setCurrentInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Digite sua resposta..."
                    className="w-full p-3 pr-12 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 bg-white dark:bg-gray-700 text-gray-950 dark:text-gray-50"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!currentInput.trim() || isLiaTyping}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel */}
          <div className="w-96 bg-gray-50 dark:bg-gray-800 p-4 overflow-y-auto">
            <div className="mb-4">
              <h4 className="font-medium font-sans text-gray-950 dark:text-gray-50 mb-2">
                {currentStep === 'overview' && '📋 Configurando Visão Geral'}
                {currentStep === 'approach' && '🗣️ Definindo Abordagem'}
                {currentStep === 'questions' && '❓ Criando Perguntas'}
                {currentStep === 'presentation' && '⭐ Preparando Apresentação'}
                {currentStep === 'feedback' && '💌 Estratégia de Feedback'}
                {currentStep === 'timeline' && '⏰ Timeline de Execução'}
                {currentStep === 'review' && '✅ Roteiro Finalizado'}
              </h4>
              <div className="text-xs text-gray-600">
                Etapa {['overview', 'approach', 'questions', 'presentation', 'feedback', 'timeline', 'review'].indexOf(currentStep) + 1} de 7
              </div>
            </div>
            {renderRightPanel()}
          </div>
        </div>
      </div>

      {/* Company Settings Modal */}
      {showCompanySettings && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-60 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-md max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Configurações da Empresa</h4>
                <Button variant="ghost" size="sm" onClick={() => setShowCompanySettings(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="p-4">
              <div className="space-y-4 text-sm">
                <div className="p-3 border rounded">
                  <div className="font-medium">Template Padrão</div>
                  <div className="text-xs text-gray-600 mt-1">Duração: 25-30 min • Foco: Técnico + Cultural</div>
                </div>
                <div className="p-3 border rounded">
                  <div className="font-medium">Abordagem</div>
                  <div className="text-xs text-gray-600 mt-1">Tom: Profissional, mas acolhedor</div>
                </div>
                <div className="p-3 border rounded">
                  <div className="font-medium">Feedback</div>
                  <div className="text-xs text-gray-600 mt-1">Aprovados: 24h • Reprovados: 48h</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
