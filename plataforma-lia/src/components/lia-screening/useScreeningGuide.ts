"use client"

import { useState, useCallback } from "react"
import { safeData } from "@/lib/safe-data"
import { Brain, MessageSquare, Target, Star, Heart, Clock } from "lucide-react"

interface ScreeningQuestion {
  category: string
  questions: unknown[]
  purpose: string
  isWSI?: boolean
}

interface ApproachStrategy {
  tone: string
  duration: string
  structure: string[]
  tips: string[]
}

interface JobPresentation {
  company: string
  role: string
  team: string
  growth: string
  benefits: string[]
}

interface FeedbackStrategy {
  timing: {
    approved: string
    rejected: string
  }
  approvedTemplate: {
    subject: string
    message: string
  }
  rejectedTemplate: {
    subject: string
    message: string
  }
  feedbackGuidelines: string[]
}

type ActiveSection = "overview" | "approach" | "questions" | "presentation" | "feedback" | "timeline"

const SECTIONS = [
  { id: "overview" as const, label: "Visão Geral", icon: Brain },
  { id: "approach" as const, label: "Abordagem", icon: MessageSquare },
  { id: "questions" as const, label: "Perguntas", icon: Target },
  { id: "presentation" as const, label: "Apresentação", icon: Star },
  { id: "feedback" as const, label: "Estratégia de Feedback", icon: Heart },
  { id: "timeline" as const, label: "Timeline", icon: Clock },
]

export function useScreeningGuide(job: Record<string, unknown>, candidate?: Record<string, unknown>) {
  const [activeSection, setActiveSection] = useState<ActiveSection>("overview")
  const [copiedSection, setCopiedSection] = useState<string | null>(null)

  const j = safeData(job)
  const c = candidate ? safeData(candidate) : null

  const copyToClipboard = useCallback((text: string, section: string) => {
    navigator.clipboard.writeText(text)
    setCopiedSection(section)
    setTimeout(() => setCopiedSection(null), 2000)
  }, [])

  const getScreeningQuestions = (): ScreeningQuestion[] => {
    const savedQuestions = job?.screening_questions || job?.screeningQuestions

    if (savedQuestions && Array.isArray(savedQuestions) && savedQuestions.length > 0) {
      const technicalQuestions = savedQuestions.filter((q: Record<string, unknown>) =>
        q.category === "technical" || q.type === "micro_case" || q.type === "situacional"
      )
      const behavioralQuestions = savedQuestions.filter((q: Record<string, unknown>) =>
        q.category === "behavioral" || q.type === "autodeclaracao_contexto"
      )
      const otherQuestions = savedQuestions.filter((q: Record<string, unknown>) =>
        !["technical", "behavioral"].includes(q.category as string) &&
        !["micro_case", "situacional", "autodeclaracao_contexto"].includes(q.type as string)
      )

      const result: ScreeningQuestion[] = []

      result.push({
        category: "Apresentação Pessoal",
        questions: [
          "Conte-me um pouco sobre você e sua trajetória profissional",
          "O que te motivou a se candidatar para esta posição?",
          "Como você ficou sabendo desta oportunidade?",
        ],
        purpose: "Quebrar o gelo e entender motivação inicial",
      })

      if (technicalQuestions.length > 0) {
        result.push({
          category: "Perguntas Técnicas (WSI)",
          questions: technicalQuestions.map((q: Record<string, unknown>) => q.question || q.text),
          purpose: "Avaliar competências técnicas através de situações reais",
          isWSI: true,
        })
      }

      if (behavioralQuestions.length > 0) {
        result.push({
          category: "Perguntas Comportamentais",
          questions: behavioralQuestions.map((q: Record<string, unknown>) => q.question || q.text),
          purpose: "Avaliar competências comportamentais e soft skills",
          isWSI: true,
        })
      }

      if (otherQuestions.length > 0) {
        result.push({
          category: "Perguntas Adicionais",
          questions: otherQuestions.map((q: Record<string, unknown>) => q.question || q.text),
          purpose: "Perguntas complementares definidas para a vaga",
        })
      }

      result.push({
        category: "Expectativas e Logística",
        questions: [
          `Esta vaga é ${j.str("work_model") || j.str("workModel") || "híbrida"} em ${j.str("location")}. Como você se sente em relação a isso?`,
          "Qual sua expectativa salarial para esta posição?",
          "Quando você poderia começar, caso seja selecionado?",
          "Tem alguma dúvida sobre a vaga ou empresa?",
        ],
        purpose: "Alinhar expectativas práticas e logísticas",
      })

      return result
    }

    const jobRequirements = j.arr<string>("requirements")
    return [
      {
        category: "Apresentação Pessoal",
        questions: [
          "Conte-me um pouco sobre você e sua trajetória profissional",
          "O que te motivou a se candidatar para esta posição?",
          "Como você ficou sabendo desta oportunidade?",
        ],
        purpose: "Quebrar o gelo e entender motivação inicial",
      },
      {
        category: "Experiência Técnica",
        questions:
          jobRequirements.length > 0
            ? jobRequirements.slice(0, 3).map((req: string) => `Fale sobre sua experiência com ${req}`)
            : [
                "Descreva um projeto desafiador que você trabalhou recentemente",
                "Como você se mantém atualizado com as tecnologias da área?",
                "Qual foi sua maior conquista profissional?",
              ],
        purpose: "Validar competências técnicas específicas da vaga",
      },
      {
        category: "Aderência Cultural",
        questions: [
          "Como você se adapta a ambientes de trabalho dinâmicos?",
          "Descreva como você lida com feedback construtivo",
          "O que você valoriza mais em uma equipe de trabalho?",
        ],
        purpose: "Avaliar alinhamento com cultura organizacional",
      },
      {
        category: "Expectativas e Logística",
        questions: [
          `Esta vaga é ${j.str("work_model") || j.str("workModel") || "híbrida"} em ${j.str("location")}. Como você se sente em relação a isso?`,
          "Qual sua expectativa salarial para esta posição?",
          "Quando você poderia começar, caso seja selecionado?",
          "Tem alguma dúvida sobre a vaga ou empresa?",
        ],
        purpose: "Alinhar expectativas práticas e logísticas",
      },
    ]
  }

  const screeningQuestions = getScreeningQuestions()

  const approachStrategy: ApproachStrategy = {
    tone: "Profissional, mas acolhedor",
    duration: "20-30 minutos",
    structure: [
      "Apresentação pessoal (2-3 min)",
      "Contexto da vaga (3-5 min)",
      "Perguntas de triagem (15-20 min)",
      "Esclarecimento de dúvidas (3-5 min)",
      "Próximos passos (2 min)",
    ],
    tips: [
      "Mantenha um ritmo conversacional, não interrogatório",
      "Faça anotações discretas durante a conversa",
      "Dê espaço para o candidato fazer perguntas",
      "Observe não apenas as respostas, mas a forma de comunicação",
    ],
  }

  const jobBenefits = j.arr<string>("benefits")
  const jobPresentation: JobPresentation = {
    company:
      "Nossa empresa é líder em inovação tecnológica, focada em criar soluções que impactam positivamente a vida das pessoas.",
    role:
      j.str("description") ||
      "Buscamos um profissional que se junte ao nosso time para contribuir com projetos desafiadores e de grande impacto.",
    team: "Você fará parte de uma equipe multidisciplinar, colaborativa e sempre em busca da excelência.",
    growth:
      "Oferecemos um ambiente de crescimento contínuo, com oportunidades de desenvolvimento e aprendizado.",
    benefits:
      jobBenefits.length > 0
        ? jobBenefits
        : ["Salário competitivo", "Benefícios completos", "Ambiente colaborativo", "Crescimento profissional"],
  }

  const feedbackStrategy: FeedbackStrategy = {
    timing: {
      approved: "Feedback positivo em até 24h",
      rejected: "Feedback construtivo em até 48h",
    },
    approvedTemplate: {
      subject: `Próximos passos - ${j.str("title")}`,
      message: `Olá {NOME},\n\nFicamos muito satisfeitos com nossa conversa sobre a posição de ${j.str("title")}!\n\nSeu perfil está alinhado com o que buscamos e gostaríamos de dar continuidade ao processo.\n\nPróximo passo: [DEFINIR PRÓXIMA ETAPA]\n\nEm breve entraremos em contato para agendar.\n\nParabéns e até logo!\n\nEquipe de Recrutamento`,
    },
    rejectedTemplate: {
      subject: `Feedback sobre processo seletivo - ${j.str("title")}`,
      message: `Olá {NOME},\n\nObrigado pelo seu interesse na posição de ${j.str("title")} e pelo tempo dedicado em nossa conversa.\n\nApós análise cuidadosa, decidimos seguir com candidatos cujo perfil está mais alinhado com as necessidades específicas desta vaga no momento.\n\n✨ Pontos fortes identificados:\n{PONTOS_FORTES}\n\n🎯 Áreas de desenvolvimento sugeridas:\n{AREAS_DESENVOLVIMENTO}\n\nSeu perfil ficará em nosso radar para futuras oportunidades que possam ser um match ainda melhor!\n\nDesejamos muito sucesso em sua jornada profissional.\n\nCom carinho,\nEquipe de Recrutamento`,
    },
    feedbackGuidelines: [
      "Seja sempre construtivo e respeitoso",
      "Destaque pelo menos 2 pontos fortes do candidato",
      "Ofereça sugestões específicas de desenvolvimento",
      "Mantenha a porta aberta para futuras oportunidades",
      "Use tom empático, mas profissional",
    ],
  }

  return {
    activeSection,
    setActiveSection,
    copiedSection,
    copyToClipboard,
    j,
    c,
    sections: SECTIONS,
    screeningQuestions,
    approachStrategy,
    jobPresentation,
    feedbackStrategy,
  }
}
