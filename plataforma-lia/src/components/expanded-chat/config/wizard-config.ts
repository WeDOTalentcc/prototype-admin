/**
 * Wizard Configuration Module
 * 
 * Contains all stage and phase configurations for the job creation wizard.
 * Extracted from expanded-chat-modal.tsx for better modularity and maintainability.
 */

/**
 * Wizard stage identifiers
 */
export type WizardStage = 'input-evaluation' | 'jd-enrichment' | 'salary' | 'competencies' | 'wsi-questions' | 'review-publish' | 'search-calibration'

/**
 * Wizard phase identifiers for visual display groupings
 */
export type WizardPhase = 'construction' | 'activation' | 'selection'

/**
 * Configuration for a wizard phase grouping
 */
export interface WizardPhaseConfig {
  id: WizardPhase
  label: string
  stages: WizardStage[]
}

/**
 * Base configuration for a wizard stage
 */
export interface WizardStageConfig {
  id: WizardStage
  title: string
  subtitle: string
  panelTitle: string
  liaMessage: string
}

/**
 * Stage transition configuration for intelligent, conversational flow
 */
export interface StageTransitionConfig {
  congratsMessage: string
  nextStepExplanation: string
  whyItMatters: string
  proactiveTips?: string[]
}

/**
 * Critical fields per stage for validation and suggestions
 */
export interface StageCriticalFields {
  required: string[]
  recommended: string[]
  autoFillable: string[]
}

/**
 * Extended wizard stage configuration with consultative behaviors
 */
export interface ExtendedWizardStageConfig extends WizardStageConfig {
  transition?: StageTransitionConfig
  criticalFields?: StageCriticalFields
  consultiveBehaviors?: string[]
  responseTemplate?: {
    summaryPrefix: string
    confirmationStyle: 'list' | 'inline' | 'card'
    showSources: boolean
    showConfidence: boolean
  }
}

/**
 * Wizard phases - groupings of stages for visual display
 */
export const WIZARD_PHASES: WizardPhaseConfig[] = [
  { id: 'construction', label: 'Construção', stages: ['input-evaluation', 'jd-enrichment', 'salary', 'competencies', 'wsi-questions'] },
  { id: 'activation', label: 'Ativação', stages: ['review-publish'] },
  { id: 'selection', label: 'Seleção', stages: ['search-calibration'] }
]

/**
 * Complete wizard stage configurations with messages, transitions, and behaviors
 */
export const WIZARD_STAGES: ExtendedWizardStageConfig[] = [
  // FASE 1: CONSTRUÇÃO
  {
    id: 'input-evaluation',
    title: 'Avaliação',
    subtitle: 'Construção',
    panelTitle: 'Critérios Detectados',
    liaMessage: `Vou guiar você na criação desta vaga de forma conversacional.

**Como funciona:**
1. Você descreve a vaga (texto livre ou cole um JD)
2. Eu analiso e extraio automaticamente os campos
3. Juntos refinamos cada etapa

**O que eu detecto automaticamente:**
- Cargo, senioridade e área
- Competências técnicas e comportamentais
- Modelo de trabalho e localização
- Indicadores de vaga afirmativa

💡 **Dica:** Quanto mais detalhes você fornecer, mais precisa será minha análise!

Vamos começar? Descreva a vaga ou cole a descrição do cargo.`,
    transition: {
      congratsMessage: "Excelente! Capturei os dados fundamentais da vaga. 🎉",
      nextStepExplanation: "Vou preparar uma proposta estruturada com base nas informações detectadas.",
      whyItMatters: "A proposta consolida responsabilidades, competências e expectativas salariais em um único resumo.",
      proactiveTips: [
        "Gerando resumo das responsabilidades do cargo",
        "Preparando sugestões de competências e faixa salarial"
      ]
    },
    criticalFields: {
      required: ['cargo', 'senioridadeIdiomas'],
      recommended: ['gestorArea', 'modeloTrabalho', 'localizacao'],
      autoFillable: ['departamento', 'tipoContrato']
    },
    consultiveBehaviors: [
      'detect_affirmative_action',
      'suggest_missing_fields',
      'validate_job_title_format',
      'auto_detect_seniority'
    ],
    responseTemplate: {
      summaryPrefix: "📋 **Campos detectados:**",
      confirmationStyle: 'card',
      showSources: true,
      showConfidence: true
    }
  },
  {
    id: 'jd-enrichment',
    title: 'Enriquecimento',
    subtitle: 'Construção',
    panelTitle: 'JD Enriquecida',
    liaMessage: `Analisei os dados coletados e preparei uma proposta **enriquecida** com sugestões baseadas em dados de mercado e histórico da sua empresa. 📋

**O que eu fiz:**
• Comparei com vagas similares no mercado
• Analisei o histórico de contratações da empresa
• Identifiquei competências que melhoram a triagem WSI

**Sugestões Inteligentes:**
No painel ao lado você vai encontrar sugestões organizadas por seção:
• **Responsabilidades** - atividades típicas do cargo
• **Competências Técnicas** - skills com % de mercado
• **Competências Comportamentais** - soft skills recomendadas
• **Remuneração** - comparativo com benchmark

**Como funciona:**
Me diga no chat quais sugestões você quer aceitar. Exemplos:
• "Aceito todas as sugestões"
• "Aceito Python e Docker, mas não quero AWS"
• "Pode avançar"

Quando estiver satisfeito, podemos seguir para a confirmação de remuneração.`,
    transition: {
      congratsMessage: "Proposta enriquecida aprovada! Vamos confirmar a remuneração. 💰",
      nextStepExplanation: "Com as sugestões aceitas, vou preparar a confirmação final de remuneração.",
      whyItMatters: "As sugestões aceitas serão usadas para gerar perguntas de triagem WSI de alta qualidade.",
      proactiveTips: [
        "As competências aceitas influenciam diretamente as perguntas de triagem",
        "Vagas com mais detalhes fecham até 40% mais rápido"
      ]
    },
    criticalFields: {
      required: ['cargo', 'senioridade'],
      recommended: ['responsabilidades', 'competenciasTecnicas', 'competenciasComportamentais'],
      autoFillable: ['faixaSalarial', 'perfilIdeal']
    },
    consultiveBehaviors: [
      'generate_enriched_jd',
      'suggest_responsibilities_with_justification',
      'suggest_skills_with_market_data',
      'suggest_behavioral_competencies',
      'compare_salary_benchmark',
      'calculate_wsi_quality_score'
    ],
    responseTemplate: {
      summaryPrefix: "📋 **Proposta Enriquecida:**",
      confirmationStyle: 'card',
      showSources: true,
      showConfidence: true
    }
  },
  {
    id: 'salary',
    title: 'Remuneração',
    subtitle: 'Construção',
    panelTitle: 'Salário e Benefícios',
    liaMessage: `Analisei as informações fornecidas e preparei uma proposta de remuneração com base em dados de mercado.

Preparei as seguintes informações:
• **Salário Base** - faixa sugerida baseada em vagas similares
• **Bônus Anual** - valores e critérios de elegibilidade
• **Benefícios** - pacote pré-selecionado da empresa

Parte das informações já foram preenchidas com base nos dados cadastrados da sua empresa.

Revise os campos no painel ao lado e me diga aqui no chat se precisar ajustar algo. Exemplos:
• "O salário deve ser entre 8 e 12 mil"
• "Adicionar vale alimentação"
• "Pode avançar" ou "Está bom, vamos seguir"

*Quando estiver satisfeito, é só me confirmar aqui no chat!*`,
    transition: {
      congratsMessage: "Remuneração confirmada! ✅",
      nextStepExplanation: "Agora vou preparar as sugestões de competências.",
      whyItMatters: "",
      proactiveTips: []
    },
    criticalFields: {
      required: ['salarioMin', 'salarioMax'],
      recommended: ['bonus', 'beneficios'],
      autoFillable: ['moeda', 'periodicidade']
    },
    consultiveBehaviors: [
      'compare_market_benchmark',
      'alert_below_market',
      'suggest_competitive_range',
      'calculate_total_compensation'
    ],
    responseTemplate: {
      summaryPrefix: "💰 **Análise de Remuneração:**",
      confirmationStyle: 'card',
      showSources: true,
      showConfidence: true
    }
  },
  {
    id: 'competencies',
    title: 'Competências',
    subtitle: 'Construção',
    panelTitle: 'Competências da Vaga',
    liaMessage: `Com base no cargo e senioridade, preparei sugestões de competências técnicas e comportamentais.

Revise as sugestões no painel ao lado e me diga aqui no chat se precisar ajustar algo. Exemplos:
• "Adicionar Python nível avançado"
• "Remover AWS, não usamos"
• "Mudar peso de liderança para 5"
• "Pode avançar" ou "Tudo certo"

*Quando estiver satisfeito, é só me confirmar aqui no chat!*`,
    transition: {
      congratsMessage: "Competências confirmadas! 🎯",
      nextStepExplanation: "Agora vou preparar as perguntas de triagem.",
      whyItMatters: "",
      proactiveTips: []
    },
    criticalFields: {
      required: ['competenciasTecnicas'],
      recommended: ['competenciasComportamentais', 'pesos'],
      autoFillable: ['niveisDefault']
    },
    consultiveBehaviors: [
      'deduplicate_skills',
      'suggest_missing_core_skills',
      'balance_technical_behavioral',
      'warn_too_many_skills',
      'infer_weights_from_role'
    ],
    responseTemplate: {
      summaryPrefix: "🎯 **Competências Selecionadas:**",
      confirmationStyle: 'list',
      showSources: true,
      showConfidence: true
    }
  },
  {
    id: 'wsi-questions',
    title: 'Triagem WSI',
    subtitle: 'Construção',
    panelTitle: 'Perguntas de Triagem WSI',
    liaMessage: `Gerando perguntas de triagem inteligentes! 📝

🎯 **Metodologia WSI aplicada:**
• **Taxonomia de Bloom** - níveis cognitivos adequados
• **Modelo Dreyfus** - proficiência técnica
• **Big Five** - traços comportamentais

📋 **Tipos de perguntas geradas:**
• **Autodeclaração** - experiência prévia quantificável
• **Contextual** - situações específicas do cargo
• **Situacional** - como o candidato reagiria

💡 **Recomendação:** Selecione 4-6 perguntas para um formulário objetivo (3-5 min de resposta).

As perguntas estão listadas abaixo. Me diga aqui no chat se deseja gerar mais opções ou ajustar alguma.`,
    transition: {
      congratsMessage: "Triagem WSI configurada! Suas perguntas estão prontas. ✅",
      nextStepExplanation: "Vamos para a **Revisão Final** - você verá tudo consolidado antes de publicar.",
      whyItMatters: "A revisão garante que nenhum detalhe importante ficou de fora.",
      proactiveTips: [
        "Vou gerar uma prévia da descrição da vaga",
        "Você poderá escolher onde publicar (LinkedIn, Indeed, etc.)"
      ]
    },
    criticalFields: {
      required: ['perguntasTriagem'],
      recommended: ['pesosPorPergunta'],
      autoFillable: ['ordemPerguntas']
    },
    consultiveBehaviors: [
      'generate_role_specific_questions',
      'balance_question_types',
      'estimate_response_time',
      'suggest_knockout_questions'
    ],
    responseTemplate: {
      summaryPrefix: "📝 **Perguntas de Triagem:**",
      confirmationStyle: 'list',
      showSources: false,
      showConfidence: true
    }
  },
  // FASE 2: ATIVAÇÃO
  {
    id: 'review-publish',
    title: 'Revisão e Publicação',
    subtitle: 'Ativação',
    panelTitle: 'Resumo e Publicação',
    liaMessage: `Quase lá! Vamos revisar tudo antes de publicar. 📋

✅ **Checklist de Qualidade:**
A vaga inclui automaticamente:
• Apresentação da empresa (sobre, missão, visão)
• EVP (Employee Value Proposition)
• Valores e cultura organizacional
• Desafios e oportunidades da posição

📊 **Qualidade da Vaga:**
Vou analisar a completude e sugerir melhorias se necessário.

🚀 **Próximos passos:**
1. Revise o resumo no painel
2. Escolha as plataformas de publicação
3. Confirme para ativar o recrutamento

Tudo pronto para publicar?`,
    transition: {
      congratsMessage: "Vaga publicada com sucesso! 🎉🚀",
      nextStepExplanation: "Agora vou começar a **buscar candidatos** compatíveis automaticamente.",
      whyItMatters: "A calibração inicial me ajuda a entender melhor o perfil ideal.",
      proactiveTips: [
        "Vou apresentar os primeiros candidatos para você avaliar",
        "Seu feedback calibra minha busca para resultados mais precisos"
      ]
    },
    criticalFields: {
      required: ['descricaoCompleta', 'canaisPublicacao'],
      recommended: ['dataLimite', 'quantidadeVagas'],
      autoFillable: ['templateDescricao', 'evp']
    },
    consultiveBehaviors: [
      'validate_completeness',
      'check_compliance',
      'suggest_improvements',
      'estimate_time_to_fill'
    ],
    responseTemplate: {
      summaryPrefix: "📋 **Resumo da Vaga:**",
      confirmationStyle: 'card',
      showSources: false,
      showConfidence: true
    }
  },
  // FASE 3: SELEÇÃO
  {
    id: 'search-calibration',
    title: 'Busca e Calibração',
    subtitle: 'Seleção',
    panelTitle: 'Busca e Calibração',
    liaMessage: `A vaga está no ar! Agora vou buscar candidatos compatíveis. 🔍

**Como funciona a calibração:**
1. Apresento candidatos para você avaliar
2. Você indica se são aderentes ou não
3. Minha IA aprende com seu feedback
4. As próximas sugestões ficam mais precisas

📊 **Métricas iniciais:**
Após a calibração, o kanban será populado com candidatos ranqueados pela Nota LIA.

Vou começar a busca. Em breve apresentarei os primeiros perfis!`,
    transition: {
      congratsMessage: "Calibração concluída! Agora conheço melhor o perfil ideal. 🎯",
      nextStepExplanation: "Os candidatos qualificados já estão no kanban da vaga.",
      whyItMatters: "A calibração melhora a precisão da triagem automática em até 60%.",
      proactiveTips: [
        "Você pode continuar avaliando candidatos a qualquer momento",
        "Quanto mais feedback, mais precisa fica a seleção"
      ]
    },
    criticalFields: {
      required: [],
      recommended: ['feedbackCalibracao'],
      autoFillable: []
    },
    consultiveBehaviors: [
      'search_candidates_proactively',
      'rank_by_lia_score',
      'learn_from_feedback',
      'suggest_sourcing_channels'
    ],
    responseTemplate: {
      summaryPrefix: "🔍 **Candidatos Encontrados:**",
      confirmationStyle: 'card',
      showSources: true,
      showConfidence: true
    }
  }
]

/**
 * Mapping from frontend stage IDs to backend stage numbers
 * Backend expects: 1=description, 2=basic-info, 3=competencies, 4=salary, 5=wsi, 6=review, 7=pre-publish, 8=candidate-search
 */
export const FRONTEND_TO_BACKEND_STAGE: Record<string, number> = {
  'input-evaluation': 1,     // description
  'jd-enrichment': 2,        // jd-enrichment (backend stage 2 - formerly job-summary)
  'salary': 4,               // salary (backend stage 4)
  'competencies': 3,         // competencies (backend stage 3)
  'wsi-questions': 5,        // wsi-questions (backend stage 5)
  'review-publish': 6,       // review (backend stage 6)
  'search-calibration': 8    // candidate-search (backend stage 8)
}

/**
 * Mapping from backend stage names to frontend stage IDs
 * The smart-orchestrate endpoint returns stage names like 'initial', 'title_department', 'salary', etc.
 */
export const BACKEND_TO_FRONTEND_STAGE: Record<string, string> = {
  'initial': 'input-evaluation',
  'title_department': 'input-evaluation',
  'description': 'input-evaluation',
  'basic_info': 'jd-enrichment',
  'job_summary': 'jd-enrichment',
  'job-summary': 'jd-enrichment',
  'jd-enrichment': 'jd-enrichment',
  'salary': 'salary',
  'compensation': 'salary',
  'competencies': 'competencies',
  'skills': 'competencies',
  'screening': 'wsi-questions',
  'wsi_questions': 'wsi-questions',
  'wsi': 'wsi-questions',
  'review': 'review-publish',
  'review_publish': 'review-publish',
  'pre_publish': 'review-publish',
  'complete': 'review-publish',
  'candidate_search': 'search-calibration',
  'calibration': 'search-calibration'
}

/**
 * Get frontend stage ID from backend stage name
 */
export const getFrontendStageFromBackend = (backendStage: string): string => {
  return BACKEND_TO_FRONTEND_STAGE[backendStage] || backendStage
}

/**
 * Get backend stage number from frontend stage ID
 */
export const getBackendStageNumber = (frontendStageId: string): number => {
  return FRONTEND_TO_BACKEND_STAGE[frontendStageId] || 1
}

/**
 * Get transition message between stages
 */
export const getStageTransitionMessage = (currentStageId: string, detectedFields: Record<string, unknown>): string => {
  const stage = WIZARD_STAGES.find(s => s.id === currentStageId) as ExtendedWizardStageConfig
  if (!stage?.transition) return ""
  
  const { congratsMessage, nextStepExplanation, whyItMatters, proactiveTips } = stage.transition
  
  let message = `\n\n---\n\n${congratsMessage}\n\n`
  message += `**Próximo:** ${nextStepExplanation}\n\n`
  message += `💡 *${whyItMatters}*`
  
  if (proactiveTips && proactiveTips.length > 0) {
    message += `\n\n**O que vou fazer:**\n`
    proactiveTips.forEach(tip => {
      message += `• ${tip}\n`
    })
  }
  
  return message
}

/**
 * Field name mapping for display
 */
const FIELD_MAPPING: Record<string, string> = {
  'cargo': 'Cargo/Título',
  'senioridadeIdiomas': 'Senioridade',
  'gestorArea': 'Gestor/Área',
  'modeloTrabalho': 'Modelo de Trabalho',
  'localizacao': 'Localização',
  'salarioMin': 'Salário Mínimo',
  'salarioMax': 'Salário Máximo',
  'competenciasTecnicas': 'Competências Técnicas',
  'competenciasComportamentais': 'Competências Comportamentais'
}

/**
 * Check missing critical fields for a stage
 */
export const getMissingCriticalFields = (stageId: string, detectedCriteria: Record<string, unknown>): { required: string[], recommended: string[] } => {
  const stage = WIZARD_STAGES.find(s => s.id === stageId) as ExtendedWizardStageConfig
  if (!stage?.criticalFields) return { required: [], recommended: [] }
  
  const missingRequired: string[] = []
  const missingRecommended: string[] = []
  
  stage.criticalFields.required.forEach(field => {
    if (!detectedCriteria[field]) {
      missingRequired.push(FIELD_MAPPING[field] || field)
    }
  })
  
  stage.criticalFields.recommended.forEach(field => {
    if (!detectedCriteria[field]) {
      missingRecommended.push(FIELD_MAPPING[field] || field)
    }
  })
  
  return { required: missingRequired, recommended: missingRecommended }
}

/**
 * Generate missing fields message for display
 */
export const generateMissingFieldsMessage = (missing: { required: string[], recommended: string[] }): string => {
  let message = ""
  
  if (missing.required.length > 0) {
    message += `\n\n⚠️ **Campos obrigatórios faltando:**\n`
    missing.required.forEach(field => {
      message += `• ${field}\n`
    })
  }
  
  if (missing.recommended.length > 0) {
    message += `\n💡 **Campos recomendados (opcional):**\n`
    missing.recommended.forEach(field => {
      message += `• ${field}\n`
    })
  }
  
  return message
}

/**
 * Pre-wizard message shown before wizard mode selection
 */
export const PRE_WIZARD_MESSAGE = `Vou ajudar você a criar uma nova vaga.

**Como quer começar?**

**Aproveitar vaga anterior** (Fast Track)
Busco uma vaga passada similar e você só confirma ou ajusta detalhes. Ideal para vagas recorrentes.

**Criar do zero** (Wizard completo)
Construímos a vaga passo a passo. Ideal para novas posições ou perfis diferentes.

Digite "usar vaga anterior" ou "criar do zero".`

/**
 * Message shown when a draft is detected - user must choose to continue or start fresh
 */
export const DRAFT_DETECTED_MESSAGE = (stageName: string) => `Olá! Encontrei uma vaga em construção. 📋

Você estava na etapa de **${stageName}**.

**O que deseja fazer?**

📝 **Continuar de onde parou** - retomo o progresso salvo
🔄 **Começar do zero** - descarto o rascunho e inicio uma nova vaga

Digite "continuar" ou "começar do zero".`

/**
 * Initial message for job creation wizard
 * Stage: input-evaluation (criteria detection)
 */
export const INITIAL_JOB_CREATION_MESSAGE = `**Como você gostaria de começar?**

**Criar vaga do zero** — Me conte sobre a posição que você precisa preencher

**Usar vaga existente** — Posso duplicar e adaptar uma vaga anterior

**Usar template** — Escolha entre nossos modelos prontos por área/cargo

Você também pode descrever a vaga em linguagem natural que eu extraio as informações automaticamente.`

/**
 * Orientation message when user chooses to create from scratch
 * This message guides the user on how to describe the job and mentions the criteria panel
 */
export const FROM_SCRATCH_ORIENTATION_MESSAGE = `Ótimo! Vamos criar sua vaga do zero. 🎯

📋 **Veja o painel de Critérios Detectados ao lado** — ele será preenchido automaticamente enquanto você descreve a vaga.

**Para eu detectar todos os critérios, me conte:**

• **Cargo e Senioridade** — Ex: "Gerente de Tecnologia Sênior"
• **Gestor/Área** — Quem será o gestor e qual área/departamento
• **Principais Responsabilidades** — O que essa pessoa vai fazer no dia-a-dia
• **Competências Técnicas (min. 3)** — Skills técnicos necessários
• **Competências Comportamentais (min. 3)** — Comp. Comportamentais desejadas
• **Faixa Salarial** — Se já tiver em mente
• **Vaga Afirmativa?** — Se for exclusiva para algum grupo

💡 **Exemplo de descrição completa:**
"Preciso de um Desenvolvedor Python Sênior para a área de Dados, reportando ao CTO. Vai trabalhar com pipelines de dados, AWS e Spark. Precisa ter liderança técnica e boa comunicação. Salário entre 18k-25k. Não é vaga afirmativa."

**Quanto mais detalhes, melhor eu detecto os critérios!** Pode começar descrevendo...`

/**
 * Initial general assistant message
 */
export const INITIAL_GENERAL_MESSAGE = `Como posso ajudar você? Posso analisar vagas, buscar candidatos, gerar scripts de entrevista ou responder dúvidas sobre o processo.`
