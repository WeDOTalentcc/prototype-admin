import { useState, useRef, useEffect, useCallback } from "react"

interface JobData {
  title?: string
  department?: string
  seniority?: string
  description?: string
  workModel?: string
  location?: string
  requirements?: string[]
  benefits?: string[]
  [key: string]: unknown
}

export interface Message {
  id: string
  sender: 'user' | 'lia'
  content: string
  timestamp: Date
  type?: 'text' | 'options' | 'confirmation'
  options?: string[]
  data?: Record<string, unknown>
}

export interface ScreeningData {
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

export type ScreeningStep = 'overview' | 'approach' | 'questions' | 'presentation' | 'feedback' | 'timeline' | 'review'

export function useLiaScreeningDialogue(isOpen: boolean, jobData: JobData, onComplete: (screeningData: ScreeningData) => void) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentInput, setCurrentInput] = useState("")
  const [isLiaTyping, setIsLiaTyping] = useState(false)
  const [currentStep, setCurrentStep] = useState<ScreeningStep>('overview')
  const [screeningData, setScreeningData] = useState<ScreeningData>({
    overview: {
      objective: "Validar fit inicial do candidato com a vaga, avaliar competências básicas e motivação",
      duration: "25-30 minutos",
      criteria: [
        { name: "Competências Técnicas", weight: 40 },
        { name: "Aderência Cultural", weight: 30 },
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

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  const addMessage = useCallback((content: string, sender: 'user' | 'lia', type: 'text' | 'options' | 'confirmation' = 'text', options?: string[], data?: Record<string, unknown>) => {
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
  }, [])

  const processLiaResponse = useCallback((userInput: string) => {
    switch (currentStep) {
      case 'overview':
        if (userInput.includes('configurações da empresa')) {
          addMessage(
            `Perfeito! Vou usar as configurações padrão da empresa como base e personalizá-las para esta vaga.\n\n**Objetivo da Triagem:**\nValidar fit inicial do candidato com a vaga, avaliar competências básicas e motivação, além de esclarecer expectativas mútuas.\n\n**Duração Sugerida:** 25-30 minutos\n\n**Critérios de Avaliação:**\n• Competências Técnicas (40%)\n• Fit Cultural (30%)\n• Motivação (20%)\n• Expectativas (10%)\n\nQuer ajustar alguma dessas configurações ou podemos prosseguir?`,
            'lia', 'options',
            ['Ajustar objetivo', 'Ajustar duração', 'Ajustar critérios', 'Prosseguir']
          )
        } else if (userInput.includes('Criar do zero')) {
          addMessage(
            `Ótimo! Vamos criar um roteiro completamente personalizado.\n\nPrimeiro, me conte: **qual é o principal objetivo desta triagem?**\n\nPor exemplo:\n• Validar conhecimentos técnicos específicos\n• Avaliar aderência cultural e comportamental\n• Triagem rápida para alto volume\n• Avaliação aprofundada para posição crítica`,
            'lia'
          )
        } else if (userInput.includes('Ver configurações')) {
          setShowCompanySettings(true)
          addMessage(
            `Vou abrir as configurações da empresa para você. Depois que revisar, me diga como quer prosseguir.`,
            'lia', 'options',
            ['Usar configurações', 'Personalizar', 'Criar do zero']
          )
        } else if (userInput.includes('Prosseguir')) {
          setCurrentStep('approach')
          addMessage(
            `Excelente! Agora vamos definir a **abordagem e tom** da conversa.\n\nCom base na vaga de ${jobData?.title}, sugiro:\n\n**Tom:** Profissional, mas acolhedor\n**Duração:** 25-30 minutos\n\n**Estrutura sugerida:**\n1. Apresentação pessoal (2-3 min)\n2. Contexto da vaga (3-5 min)\n3. Perguntas de triagem (15-20 min)\n4. Esclarecimento de dúvidas (3-5 min)\n5. Próximos passos (2 min)\n\nEsta estrutura funciona para você?`,
            'lia', 'options',
            ['Perfeita!', 'Ajustar tom', 'Ajustar estrutura', 'Personalizar']
          )
        }
        break
      case 'approach':
        if (userInput.includes('Perfeita')) {
          setCurrentStep('questions')
          addMessage(
            `Ótimo! Agora vamos criar as **perguntas de triagem**.\n\nBaseado nos requisitos da vaga (${((jobData as Record<string, unknown>)?.requirements as string[])?.slice(0, 3).join(', ') || 'requisitos técnicos'}), sugiro organizar em 4 categorias:\n\n**1. Apresentação Pessoal**\n• Conte-me sobre sua trajetória profissional\n• O que te motivou a se candidatar?\n\n**2. Experiência Técnica**\n• Fale sobre sua experiência com ${jobData?.requirements?.[0] || 'tecnologias relevantes'}\n• Descreva um projeto desafiador recente\n\n**3. Fit Cultural**\n• Como você se adapta a ambientes dinâmicos?\n• Como lida com feedback?\n\n**4. Expectativas**\n• Esta vaga é ${jobData?.workModel || 'híbrida'} em ${jobData?.location || 'localização'}. Como se sente?\n• Qual sua expectativa salarial?\n\nQuer personalizar alguma categoria?`,
            'lia', 'options',
            ['Adicionar categoria', 'Editar perguntas', 'Personalizar por categoria', 'Prosseguir']
          )
        }
        break
      case 'questions':
        if (userInput.includes('Prosseguir')) {
          setCurrentStep('presentation')
          addMessage(
            `Perfeito! Agora vamos preparar a **apresentação da vaga e empresa**.\n\n**Sobre a Empresa:**\nNossa empresa é líder em inovação tecnológica, focada em criar soluções que impactam positivamente a vida das pessoas.\n\n**Sobre a Vaga:**\nPara a posição de ${jobData?.title}, buscamos um profissional que se junte ao nosso time para contribuir com projetos desafiadores e de grande impacto.\n\n**Sobre o Time:**\nVocê fará parte de uma equipe multidisciplinar, colaborativa e sempre em busca da excelência.\n\n**Benefícios:**\n${((jobData as Record<string, unknown>)?.benefits as string[])?.join(', ') || 'Benefícios competitivos'}\n\nQuer personalizar alguma dessas seções?`,
            'lia', 'options',
            ['Editar empresa', 'Editar vaga', 'Editar benefícios', 'Prosseguir'] as string[]
          )
        }
        break
      case 'presentation':
        if (userInput.includes('Prosseguir')) {
          setCurrentStep('feedback')
          addMessage(
            `Excelente! Agora a parte mais importante: **estratégia de feedback**.\n\n**Para candidatos APROVADOS:**\n• Timing: 24 horas\n• Tom: Positivo e entusiasmado\n• Próximos passos claros\n\n**Para candidatos NÃO SELECIONADOS:**\n• Timing: 48 horas\n• Feedback construtivo incluindo:\n  - Pontos fortes identificados\n  - Áreas de desenvolvimento sugeridas\n  - Manter porta aberta para futuras oportunidades\n\n**Diretrizes:**\n• Sempre construtivo e respeitoso\n• Destacar pelo menos 2 pontos fortes\n• Oferecer sugestões específicas\n• Manter relacionamento positivo\n\nEsta abordagem está alinhada com a cultura da empresa?`,
            'lia', 'options',
            ['Perfeita!', 'Ajustar timing', 'Personalizar templates', 'Adicionar diretrizes']
          )
        }
        break
      case 'feedback':
        if (userInput.includes('Perfeita')) {
          setCurrentStep('timeline')
          addMessage(
            `Ótimo! Por último, vamos definir o **timeline de execução**:\n\n**1. Preparação (5 min antes)**\n• Revisar currículo do candidato\n• Preparar perguntas específicas\n• Configurar ambiente (presencial/online)\n\n**2. Triagem (25-30 min)**\n• Executar conversa seguindo roteiro\n• Fazer anotações durante conversa\n\n**3. Avaliação (10 min após)**\n• Análise das respostas\n• Decisão e documentação\n• Preenchimento da avaliação\n\n**4. Feedback (24-48h após)**\n• Envio de retorno personalizado\n• Atualização do status no sistema\n\nEste cronograma funciona para sua rotina?`,
            'lia', 'options',
            ['Perfeito!', 'Ajustar tempos', 'Adicionar etapa', 'Finalizar roteiro']
          )
        }
        break
      case 'timeline':
        if (userInput.includes('Perfeito') || userInput.includes('Finalizar')) {
          setCurrentStep('review')
          addMessage(
            `🎉 **Roteiro de Triagem Criado com Sucesso!**\n\nSeu roteiro personalizado para a vaga de **${jobData?.title}** está pronto!\n\n**Resumo:**\n✅ Objetivo definido e critérios estabelecidos\n✅ Abordagem e estrutura personalizadas\n✅ Perguntas organizadas por categoria\n✅ Apresentação da empresa e vaga\n✅ Estratégia de feedback construtivo\n✅ Timeline de execução estruturada\n\nO roteiro está sendo gerado no painel ao lado. Você pode:\n• Revisar e editar qualquer seção\n• Exportar como PDF\n• Salvar como template\n• Iniciar triagem imediatamente\n\nEstá satisfeito com o resultado?`,
            'lia', 'options',
            ['Perfeito! Salvar', 'Revisar seções', 'Criar template', 'Exportar PDF']
          )
        }
        break
      case 'review':
        if (userInput.includes('Salvar')) {
          addMessage(
            `✅ **Roteiro salvo com sucesso!**\n\nO roteiro está agora disponível para esta vaga e pode ser acessado a qualquer momento.\n\nQuando estiver pronto para fazer triagens, o roteiro completo aparecerá automaticamente com:\n• Scripts prontos para usar\n• Perguntas personalizadas\n• Templates de feedback\n• Checklist de execução\n\nBoa sorte com as triagens! 🚀`,
            'lia'
          )
          setTimeout(() => {
            onComplete(screeningData)
          }, 2000)
        }
        break
    }
  }, [currentStep, addMessage, jobData, onComplete, screeningData])

  const initializeConversation = useCallback(() => {
    addMessage(
      `Olá! Vou te ajudar a criar um roteiro de triagem personalizado para a vaga de **${jobData?.title || 'Nova Vaga'}**.\n\nAntes de começarmos, você gostaria de usar as configurações padrão da empresa como base?`,
      'lia', 'options',
      ['Usar configurações da empresa', 'Criar do zero', 'Ver configurações']
    )
  }, [addMessage, jobData?.title])

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      initializeConversation()
    }
  }, [isOpen, messages.length, initializeConversation])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSendMessage = useCallback(async () => {
    if (!currentInput.trim()) return
    const userMessage = currentInput
    addMessage(userMessage, 'user')
    setCurrentInput("")
    setIsLiaTyping(true)
    setTimeout(() => {
      processLiaResponse(userMessage)
      setIsLiaTyping(false)
    }, 1500)
  }, [currentInput, addMessage, processLiaResponse])

  const handleOptionSelect = useCallback(async (option: string) => {
    addMessage(option, 'user')
    setIsLiaTyping(true)
    setTimeout(() => {
      processLiaResponse(option)
      setIsLiaTyping(false)
    }, 1000)
  }, [addMessage, processLiaResponse])

  return {
    messages,
    currentInput,
    setCurrentInput,
    isLiaTyping,
    currentStep,
    screeningData,
    showCompanySettings,
    setShowCompanySettings,
    messagesEndRef,
    inputRef,
    handleSendMessage,
    handleOptionSelect,
  }
}
