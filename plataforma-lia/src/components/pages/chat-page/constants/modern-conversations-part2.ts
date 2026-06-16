import { CURRENCY_SYMBOL } from "@/lib/pricing"
import {
  BarChart3, Brain, Calendar, ClipboardList, Copy, Download,
  FileText, Filter, Phone, Settings, Target, Users, Workflow, Zap
} from "lucide-react"
import type { Message } from "../types"

const modernConversationPart2: Message[] = [
  {
    id: 18,
    sender: "user",
    content: "Ótimo! Pode publicar em todos os canais e iniciar o sourcing ativo. Vamos acelerar este processo.",
    timestamp: "09:35",
    type: "text"
  },
  {
    id: 19,
    sender: "lia",
    content: "🚀 Sourcing ativo iniciado! Publiquei a vaga em todos os 5 canais principais. Já identifiquei 47 candidatos potenciais através do meu algoritmo de matching avançado. Iniciando outreach personalizado... ⚡ Update em tempo real: 12 aplicações recebidas nas primeiras 3 horas! Vou começar a triagem automática?",
    timestamp: "09:38",
    type: "action",
    actions: [
      { label: "Ver Funil de Candidatos", icon: Users, variant: "secondary" },
      { label: "Iniciar Triagem Automática", icon: Filter, variant: "secondary" },
      { label: "Agendar Primeiras Entrevistas", icon: Calendar, variant: "secondary" }
    ],
    contextData: {
      type: "interview-scheduling",
      title: "Agendamento de Entrevistas - Candidatos Top",
      data: {
        candidates_to_schedule: [
          {
            name: "Carlos Mendonça",
            score: 94,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Manhã", "Tarde"]
          },
          {
            name: "Patricia Santos",
            score: 91,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Tarde", "Noite"]
          },
          {
            name: "Ricardo Alves",
            score: 88,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Manhã"]
          }
        ],
        available_slots: {
          "23/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: true },
            { time: "11:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true },
            { time: "16:00", duration: "30 min", available: true }
          ],
          "24/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: false },
            { time: "11:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true },
            { time: "16:30", duration: "30 min", available: true }
          ],
          "25/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true }
          ]
        },
        interviewer: "Ana Silva - Senior Recruiter",
        auto_confirmation: true,
        calendar_integration: "Google Calendar"
      }
    }
  },
  {
    id: 20,
    sender: "user",
    content: "Excelente progresso! Por favor inicie a triagem automática e agende as primeiras entrevistas com os candidatos top.",
    timestamp: "09:42",
    type: "text"
  },
  {
    id: 21,
    sender: "lia",
    content: "✅ Triagem automática ativada! Processei os 12 candidatos aplicados - 8 avançaram automaticamente e 4 foram filtrados. Agendei 5 screening calls para amanhã e after-tomorrow. Também configurei o processo de entrevistas estruturadas. Quer revisar o cronograma de entrevistas?",
    timestamp: "09:45",
    type: "action",
    actions: [
      { label: "Ver Cronograma de Entrevistas", icon: Calendar, variant: "secondary" },
      { label: "Configurar Avaliações", icon: ClipboardList, variant: "secondary" },
      { label: "Preparar Interview Kits", icon: FileText, variant: "secondary" }
    ],
    contextData: {
      type: "interview-management",
      title: "Gestão de Entrevistas - Sistema Integrado",
      data: {
        screening_schedule: [
          {
            candidate: "Carlos Mendonça",
            date: "23/02/2024",
            time: "14:00-14:30",
            interviewer: "Ana Silva",
            type: "Screening Call",
            status: "Confirmed"
          },
          {
            candidate: "Patricia Santos",
            date: "23/02/2024",
            time: "15:00-15:30",
            interviewer: "Ana Silva",
            type: "Screening Call",
            status: "Confirmed"
          }
        ],
        interview_structure: {
          stage_1_screening: {
            duration: "30 minutes",
            interviewer: "Ana Silva (Recruiter)",
            focus: ["Aderência cultural", "Habilidades de comunicação", "Expectativa salarial"],
            success_criteria: "Nota ≥ 7/10 para avançar"
          },
          stage_2_technical: {
            duration: "90 minutes",
            interviewer: "CTO + Senior Tech Lead",
            focus: ["Technical leadership", "Architecture decisions", "Team management"],
            success_criteria: "Nota ≥ 8/10 para avançar"
          }
        }
      }
    }
  },
  {
    id: 22,
    sender: "user",
    content: "Perfeito! O processo de entrevistas está bem estruturado. Agora vamos para a próxima fase - assumindo que encontramos o candidato ideal, preciso que você prepare todo o processo de seleção final e proposta.",
    timestamp: "09:50",
    type: "text"
  },
  {
    id: 23,
    sender: "lia",
    content: "Excelente! Vou preparar todo o workflow de seleção final, negociação e proposta. Assumindo que Carlos Mendonça seja nosso candidato escolhido (score 94), já preparei a proposta completa, processo de referências, due diligence e documentação para aprovação do C-Level. Tudo pronto para execução!",
    timestamp: "09:53",
    type: "action",
    actions: [
      { label: "Ver Proposta Final", icon: FileText, variant: "secondary" },
      { label: "Iniciar Referências", icon: Phone, variant: "secondary" },
      { label: "Preparar Documentos", icon: Download, variant: "secondary" }
    ],
    contextData: {
      type: "offer-letter",
      title: "Carta Oferta - Carlos Mendonça",
      data: {
        candidate_info: {
          name: "Carlos Mendonça",
          email: "carlos.mendonca@email.com",
          phone: "+55 11 98765-4321",
          current_company: "iFood"
        },
        position_details: {
          title: "Diretor de Tecnologia da Informação",
          department: "Tecnologia e Inovação",
          reports_to: "CEO - Roberto Costa",
          start_date: "15 de Março de 2024",
          location: "São Paulo, SP - Modelo Híbrido"
        },
        compensation: {
          base_salary: `${CURRENCY_SYMBOL} 47.500,00/mês`,
          variable_bonus: "Até 50% do salário base (target: 30%)",
          sign_on_bonus: `${CURRENCY_SYMBOL} 30.000,00 (pagamento único)`,
          stock_options: "0.15% equity - 4 anos vesting",
          total_annual: `${CURRENCY_SYMBOL} 807.000,00`
        },
        benefits: {
          health_insurance: "Plano de saúde premium (titular + dependentes)",
          dental: "Plano odontológico completo",
          life_insurance: "Seguro de vida em grupo",
          meal_voucher: `${CURRENCY_SYMBOL} 1.200/mês (Flash)`,
          transport: "Vale-transporte ou estacionamento",
          gym: "Gympass premium",
          home_office: `Auxílio home office ${CURRENCY_SYMBOL} 500/mês`,
          education: `Budget anual de ${CURRENCY_SYMBOL} 15.000 para cursos e certificações`,
          vacation: "30 dias de férias anuais",
          pto: "15 dias de PTO (Paid Time Off) adicionais"
        },
        letter_template: `São Paulo, 14 de Fevereiro de 2024

Prezado Carlos Mendonça,

É com grande satisfação que apresentamos nossa proposta formal para você integrar nossa equipe como **Diretor de Tecnologia da Informação**.

**DETALHES DA POSIÇÃO:**
Cargo: Diretor de Tecnologia da Informação
Departamento: Tecnologia e Inovação
Reporta-se a: CEO - Roberto Costa
Data de início: 15 de Março de 2024
Localização: São Paulo, SP - Modelo Híbrido (3 dias presencial)

**COMPENSAÇÃO:**
• Salário base: ${CURRENCY_SYMBOL} 47.500,00 mensais (CLT)
• Bônus variável: Até 50% do salário base anual (target: 30%)
• Sign-on bonus: ${CURRENCY_SYMBOL} 30.000,00 (pagamento único no primeiro mês)
• Stock Options: 0.15% equity com vesting de 4 anos
• Total anual estimado: ${CURRENCY_SYMBOL} 807.000,00

**PACOTE DE BENEFÍCIOS:**
• Plano de saúde premium (titular + dependentes) - Bradesco Saúde Top
• Plano odontológico completo
• Seguro de vida em grupo
• Vale-refeição: ${CURRENCY_SYMBOL} 1.200/mês (Flash)
• Vale-transporte ou estacionamento
• Gympass premium
• Auxílio home office: ${CURRENCY_SYMBOL} 500/mês
• Budget educacional: ${CURRENCY_SYMBOL} 15.000/ano para cursos, certificações e conferências
• 30 dias de férias anuais
• 15 dias de PTO (Paid Time Off) adicionais

**RESPONSABILIDADES PRINCIPAIS:**
Liderar a transformação digital da empresa, gerenciar equipe de 45+ profissionais de TI, modernizar infraestrutura tecnológica e implementar estratégias de inovação alinhadas aos objetivos de negócio.

Esta proposta é válida até 28 de Fevereiro de 2024. Estamos entusiasmados com a possibilidade de tê-lo em nossa equipe!

Atenciosamente,

Roberto Costa
CEO
WeDo Talent Solutions`
      }
    }
  },
  {
    id: 24,
    sender: "user",
    content: "Excelente trabalho! A proposta está bem estruturada. Assumindo que ele aceite, agora preciso que você prepare todo o processo de onboarding e integração dele à empresa.",
    timestamp: "09:58",
    type: "text"
  },
  {
    id: 25,
    sender: "lia",
    content: "🎉 Perfeito! Vou criar um plano de onboarding de classe mundial para Carlos. Preparei um programa de 90 dias estruturado, com integração técnica, cultural e estratégica. Incluí automação completa no HRIS, preparação da equipe, e acompanhamento contínuo. O onboarding está desenhado para maximizar o sucesso dele nos primeiros meses!",
    timestamp: "10:02",
    type: "action",
    actions: [
      { label: "Ver Plano de Onboarding", icon: Workflow, variant: "secondary" },
      { label: "Configurar Automações", icon: Settings, variant: "secondary" },
      { label: "Preparar Equipe", icon: Users, variant: "secondary" }
    ],
    contextData: {
      type: "onboarding-plan",
      title: "Plano de Onboarding - 90 Dias",
      data: {
        program: "Programa de 90 Dias",
        description: "Integração estratégica e cultural personalizada",
        first_30_days: [
          "Imersão na cultura e processos da empresa",
          "Reuniões 1:1 com stakeholders principais",
          "Análise do estado atual da infraestrutura TI"
        ],
        days_60_90: [
          "Apresentação do plano estratégico de transformação digital",
          "Início das primeiras iniciativas de melhoria"
        ]
      }
    }
  },
  {
    id: 26,
    sender: "user",
    content: "Fantástico! O plano de onboarding está muito bem estruturado. Agora preciso que você configure o acompanhamento de 90 dias e prepare um sistema de avaliação de performance para o primeiro ano dele.",
    timestamp: "10:08",
    type: "text"
  },
  {
    id: 27,
    sender: "lia",
    content: "Excelente! Vou criar um sistema completo de acompanhamento pós-90 dias e avaliação de performance anual. Preparei um framework de performance management integrado, com OKRs estratégicos, métricas de sucesso, 360-feedback contínuo, e planejamento de carreira. Tudo automatizado no sistema para garantir o sucesso de longo prazo!",
    timestamp: "10:12",
    type: "action",
    actions: [
      { label: "Ver Framework de Performance", icon: Target, variant: "secondary" },
      { label: "Configurar OKRs", icon: BarChart3, variant: "secondary" },
      { label: "Agendar Reviews", icon: Calendar, variant: "secondary" }
    ],
    contextData: {
      type: "performance-management",
      title: "Framework de Performance Management",
      data: {
        framework: "Framework de Avaliação Anual",
        description: "OKRs + 360-feedback + desenvolvimento contínuo",
        first_year_okrs: [
          { objective: "Transformação Digital", description: "Migrar 80% dos sistemas para cloud em 12 meses" },
          { objective: "Crescimento da Equipe", description: "Escalar equipe de 45 para 75 pessoas com 95% de retenção" },
          { objective: "Excelência Operacional", description: "Reduzir downtime em 50% e implementar monitoramento avançado" }
        ],
        review_schedule: [
          { period: "30 dias", type: "Check-in inicial" },
          { period: "90 dias", type: "Avaliação onboarding" },
          { period: "12 meses", type: "Review anual" }
        ]
      }
    }
  },
  {
    id: 28,
    sender: "user",
    content: "Perfeito! O sistema de performance management está extremamente bem estruturado. Agora temos uma jornada completa desde a abertura da vaga até o acompanhamento de performance do primeiro ano. Muito bom trabalho!",
    timestamp: "10:18",
    type: "text"
  },
  {
    id: 29,
    sender: "lia",
    content: "🎉 Obrigada! Criamos uma jornada de recrutamento verdadeiramente completa e integrada! Do mapeamento organizacional inicial até o performance management de primeiro ano - tudo conectado, automatizado e otimizado. Agora quero gerar um relatório executivo final consolidando toda esta jornada para documentação e futuras replicações. Posso criar?",
    timestamp: "10:20",
    type: "action",
    actions: [
      { label: "Gerar Relatório Executivo", icon: FileText, variant: "secondary" },
      { label: "Criar Template Replicável", icon: Copy, variant: "secondary" },
      { label: "Configurar Dashboard", icon: BarChart3, variant: "secondary" }
    ],
    contextData: {
      type: "journey-summary",
      title: "Relatório Executivo - Jornada Completa de Recrutamento",
      data: {
        executive_summary: {
          position: "Diretor de Tecnologia da Informação",
          journey_duration: "Planejamento: 2 semanas | Execução: 6 semanas | Onboarding: 12 semanas",
          total_investment: `${CURRENCY_SYMBOL} 127.500 (recrutamento) + ${CURRENCY_SYMBOL} 807.000 (compensação anual)`,
          roi_projection: `${CURRENCY_SYMBOL} 3.2M em valor gerado no primeiro ano`,
          success_probability: "94% baseado em assessment completo e cultural fit"
        },
        journey_phases: {
          phase_1_strategic_planning: {
            duration: "1 semana",
            activities: [
              "Análise estrutura organizacional",
              "Definição hierarquia e escopo",
              "Mapeamento competências técnicas/comportamentais",
              "Estruturação pacote compensação"
            ],
            outcomes: [
              "Job description completo e atrativo",
              "Compensação top 25% do mercado",
              "Aprovação unânime do C-Level",
              "Framework de avaliação estruturado"
            ]
          },
          phase_2_sourcing_selection: {
            duration: "4 semanas",
            activities: [
              "Publicação em 5 canais premium",
              "Sourcing ativo de 150+ candidatos",
              "Processo estruturado de 4 etapas",
              "Avaliação com IA e 360-feedback"
            ],
            outcomes: [
              "200+ aplicações de qualidade",
              "59 candidatos no funil",
              "Seleção final com 94% de score",
              "Proposta aceita em primeira rodada"
            ]
          }
        },
        key_innovations: {
          ai_integration: [
            "Sourcing automatizado com ML matching",
            "Análise sentimento em entrevistas",
            "Predictive success modeling",
            "Automated performance tracking"
          ],
          ats_automation: [
            "Workday integration completa",
            "Workflows automatizados end-to-end",
            "Real-time dashboards e analytics",
            "Cross-system data synchronization"
          ]
        },
        measurable_results: {
          time_to_hire: "45 dias (vs 65 dias industry average)",
          cost_per_hire: `${CURRENCY_SYMBOL} 127.500 (vs ${CURRENCY_SYMBOL} 180.000 executive search)`,
          candidate_quality: "94/100 final score (vs 78 average)",
          hiring_manager_satisfaction: "9.8/10 NPS"
        }
      }
    }
  },
  {
    id: 30,
    sender: "lia",
    content: "💡 Com base na análise preditiva dos dados históricos, identifiquei 3 oportunidades de otimização para futuras jornadas similares. Minha IA analisou 500+ processos anteriores e sugere melhorias que podem reduzir o time-to-hire em 15% e aumentar a qualidade dos candidatos em 12%.",
    timestamp: "10:25",
    type: "action",
    actions: [
      { label: "Ver Sugestões Preditivas", icon: Brain, variant: "secondary" },
      { label: "Aplicar Otimizações", icon: Zap, variant: "secondary" },
      { label: "Configurar IA Preditiva", icon: Settings, variant: "secondary" }
    ],
    contextData: {
      type: "predictive-insights",
      title: "Inteligência Preditiva - Sugestões de Otimização",
      data: {
        analysis_base: {
          historical_processes: 500,
          success_rate_current: 87,
          avg_time_current: 45,
          data_points: 15000
        },
        predictions: [
          {
            category: "Tempo de Contratação",
            current_performance: "45 dias médios",
            predicted_improvement: "38 dias (-15%)",
            confidence: 94,
            actions: [
              "Automatizar triagem inicial com scoring IA",
              "Implementar agendamento inteligente de entrevistas",
              "Priorizar candidatos com maior probabilidade de aceite"
            ]
          },
          {
            category: "Qualidade dos Candidatos",
            current_performance: "Nota média 78/100",
            predicted_improvement: "Nota média 87/100 (+12%)",
            confidence: 89,
            actions: [
              "Refinar critérios de sourcing com ML",
              "Implementar análise preditiva de aderência cultural",
              "Otimizar job descriptions com NLP"
            ]
          },
          {
            category: "Taxa de Conversão",
            current_performance: "67% de conversão",
            predicted_improvement: "79% de conversão (+18%)",
            confidence: 91,
            actions: [
              "Personalizar approach por perfil candidato",
              "Implementar follow-up inteligente",
              "Otimizar processo de negociação"
            ]
          }
        ],
        implementation_roadmap: {
          phase_1: "Implementar scoring IA (2 semanas)",
          phase_2: "Deploy agendamento inteligente (3 semanas)",
          phase_3: "Ativar análise preditiva completa (4 semanas)"
        }
      }
    }
  },
  {
    id: 30,
    sender: "user",
    content: "Perfeito! Agora quero que você analise os candidatos do último processo e me ajude a identificar padrões de sucesso para futuras contratações.",
    timestamp: "10:22",
    type: "text"
  },
  {
    id: 31,
    sender: "lia",
    content: "",
    timestamp: "10:23",
    type: "thinking",
    thinkingMessage: "Analisando dados dos candidatos e identificando padrões de performance..."
  },
  {
    id: 32,
    sender: "lia",
    content: "Vou realizar uma análise completa dos dados de candidatos para identificar padrões de sucesso. Deixe-me processar todas as informações.",
    timestamp: "10:23",
    type: "progress",
    progressSteps: [
      {
        id: "step1",
        label: "Coletando dados dos candidatos",
        status: "completed",
        details: "150 candidatos analisados",
        icon: Users
      },
      {
        id: "step2",
        label: "Analisando performance histórica",
        status: "processing",
        details: "Correlacionando dados com performance",
        icon: BarChart3
      },
      {
        id: "step3",
        label: "Identificando padrões de sucesso",
        status: "pending",
        details: "Algoritmos de ML em processamento",
        icon: Brain
      },
      {
        id: "step4",
        label: "Gerando insights preditivos",
        status: "pending",
        details: "Criando modelo de predição",
        icon: Target
      }
    ],
    currentStep: "step2"
  },
  {
    id: 33,
    sender: "lia",
    content: "Executando análise de dados avançada...",
    timestamp: "10:24",
    type: "command",
    command: {
      text: "python analyze_candidates.py --model=success_pattern --data=last_12_months",
      status: "executing",
      output: "Processando 150 candidatos...\nCorrelação encontrada: 0.89\nPadrões identificados: 12"
    }
  },
  {
    id: 34,
    sender: "lia",
    content: "Criando relatório de análise...",
    timestamp: "10:25",
    type: "file-creation",
    fileCreation: {
      fileName: "candidate_success_patterns_2024.pdf",
      fileType: "Relatório de Análise Preditiva",
      status: "creating"
    }
  },
  {
    id: 35,
    sender: "lia",
    content: "🎯 Análise concluída com sucesso! Identifiquei 5 padrões principais que correlacionam com alta performance:\n\n• **Experiência em transformação digital** (correlação: 0.92)\n• **Liderança em equipes multidisciplinares** (correlação: 0.87)\n• **Background em metodologias ágeis** (correlação: 0.84)\n• **Formação continuada em tecnologia** (correlação: 0.79)\n• **Experiência internacional** (correlação: 0.71)\n\nCom base nesses padrões, posso prever com 89% de precisão o sucesso de futuros candidatos para posições similares.",
    timestamp: "10:26",
    type: "completion",
    completion: {
      message: "Análise de padrões de sucesso concluída com precisão de 89%",
      allowRating: true,
      allowFollowUp: true
    },
    contextData: {
      type: "predictive-insights",
      title: "Padrões de Sucesso - Análise Preditiva",
      data: {
        analysis_summary: {
          candidates_analyzed: 150,
          success_correlation: 0.89,
          prediction_accuracy: "89%",
          patterns_identified: 5,
          model_confidence: "Alta"
        },
        success_patterns: [
          {
            pattern: "Experiência em Transformação Digital",
            correlation: 0.92,
            description: "Candidatos com experiência comprovada em projetos de transformação digital apresentam 92% maior probabilidade de sucesso",
            examples: ["Migração cloud", "Implementação de DevOps", "Digitalização de processos"]
          },
          {
            pattern: "Liderança Multidisciplinar",
            correlation: 0.87,
            description: "Liderança de equipes diversas indica melhor adaptação ao ambiente organizacional",
            examples: ["Gestão de times técnicos e negócio", "Coordenação de stakeholders", "Projetos cross-funcionais"]
          }
        ],
        predictive_model: {
          accuracy: "89%",
          confidence_interval: "85-93%",
          validation_method: "Cross-validation com dados de 24 meses",
          next_calibration: "Trimestral"
        },
        recommendations: [
          "Priorizar candidatos com score > 85% no modelo preditivo",
          "Incluir perguntas específicas sobre transformação digital",
          "Avaliar experiência em gestão de mudanças organizacionais",
          "Verificar histórico de projetos multidisciplinares"
        ]
      }
    }
  }
]

export { modernConversationPart2 }
