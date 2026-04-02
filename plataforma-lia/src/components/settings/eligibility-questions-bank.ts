export type QuestionCategory = 
  | 'general'
  | 'eligibility'
  | 'availability'
  | 'education'
  | 'experience'
  | 'languages'
  | 'compensation'
  | 'work_model'
  | 'compliance'
  | 'system_default'

export interface TriggerCondition {
  field: string
  operator: 'equals' | 'contains' | 'greater_than'
  value: string | number | boolean
}

export interface EligibilityQuestionTemplate {
  id: string
  question: string
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  category: QuestionCategory
  contextHint: string
  options?: string[]
  triggerCondition?: TriggerCondition
  linkedField?: string  // job field that triggers this question (e.g., 'workModel', 'languages', 'type', 'location', 'isAffirmative')
  isSystemDefault?: boolean
  eliminatory?: boolean
  eliminatoryAnswer?: string | boolean
}

/** @deprecated Use EligibilityQuestionTemplate instead */
export type ScreeningQuestionTemplate = EligibilityQuestionTemplate

export const QUESTION_CATEGORIES: Record<QuestionCategory, { label: string; icon: string; color: string }> = {
  general: { label: 'Gerais', icon: '📋', color: 'bg-gray-100 text-lia-text-primary' },
  eligibility: { label: 'Elegibilidade e Requisitos Legais', icon: '📋', color: 'bg-wedo-cyan/15 text-wedo-cyan-dark' },
  availability: { label: 'Disponibilidade e Mobilidade', icon: '✈️', color: 'bg-status-success/15 text-status-success' },
  education: { label: 'Formação e Certificações', icon: '🎓', color: 'bg-wedo-purple/15 text-wedo-purple' },
  experience: { label: 'Experiência Específica', icon: '💼', color: 'bg-wedo-orange/15 text-wedo-orange' },
  languages: { label: 'Idiomas', icon: '🌍', color: 'bg-wedo-cyan/20 text-wedo-cyan-dark' },
  compensation: { label: 'Remuneração e Contrato', icon: '💰', color: 'bg-status-warning/15 text-status-warning' },
  work_model: { label: 'Modelo de Trabalho', icon: '🏠', color: 'bg-wedo-purple/15 text-wedo-purple' },
  compliance: { label: 'Compliance e Conflito de Interesses', icon: '⚠️', color: 'bg-status-error/15 text-status-error' },
  system_default: { label: 'Perguntas Padrão do Sistema', icon: '⚙️', color: 'bg-gray-100 text-lia-text-primary' },
}

export const ELIGIBILITY_QUESTIONS_BANK: EligibilityQuestionTemplate[] = [
  // === PERGUNTAS PADRÃO DO SISTEMA (vinculadas a campos da vaga) ===
  {
    id: 'sys-workmodel',
    question: 'Você tem disponibilidade para trabalhar no modelo {modeloTrabalho}?',
    type: 'yesno',
    category: 'system_default',
    contextHint: 'Vinculada ao campo Modelo de Trabalho da vaga',
    linkedField: 'workModel',
    isSystemDefault: true,
    eliminatory: true,
    eliminatoryAnswer: 'Sim'
  },
  {
    id: 'sys-contract-type',
    question: 'Você aceita contratação no regime {tipoContratação}?',
    type: 'yesno',
    category: 'system_default',
    contextHint: 'Vinculada ao campo Tipo de Contratação da vaga',
    linkedField: 'type',
    isSystemDefault: true,
    eliminatory: true,
    eliminatoryAnswer: 'Sim'
  },
  {
    id: 'sys-location',
    question: 'Você reside ou tem disponibilidade para trabalhar em {localização}?',
    type: 'yesno',
    category: 'system_default',
    contextHint: 'Vinculada ao campo Localização da vaga',
    linkedField: 'location',
    isSystemDefault: true,
    eliminatory: false,
  },
  {
    id: 'sys-language',
    question: 'Qual seu nível de proficiência em {idioma}? (Mínimo: {nível})',
    type: 'text',
    category: 'system_default',
    contextHint: 'Vinculada ao campo Idiomas da vaga. Uma pergunta gerada por idioma obrigatório.',
    linkedField: 'languages',
    isSystemDefault: true,
    eliminatory: true,
  },
  {
    id: 'sys-affirmative',
    question: 'Você se enquadra nos critérios afirmativos desta vaga?',
    type: 'yesno',
    category: 'system_default',
    contextHint: 'Vinculada ao campo Ações Afirmativas da vaga',
    linkedField: 'isAffirmative',
    isSystemDefault: true,
    eliminatory: false,
  },

  // === ELEGIBILIDADE E REQUISITOS LEGAIS ===
  {
    id: 'bank-elig-1',
    question: 'Esta vaga é afirmativa. Você se identifica com o grupo elegível?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vagas afirmativas (PCD, negros, mulheres, LGBTQIA+, 50+)',
    triggerCondition: { field: 'is_affirmative', operator: 'equals', value: true },
    eliminatory: true,
    eliminatoryAnswer: false
  },
  {
    id: 'bank-elig-2',
    question: 'Qual grupo você se identifica? (PCD, Negro(a), Mulher, LGBTQIA+, 50+)',
    type: 'multiple',
    category: 'eligibility',
    contextHint: 'Seguimento da pergunta de vaga afirmativa',
    options: ['PCD', 'Negro(a)', 'Mulher', 'LGBTQIA+', '50+', 'Outro']
  },
  {
    id: 'bank-elig-3',
    question: 'Você possui laudo/CID que comprove a deficiência?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vagas PCD',
    triggerCondition: { field: 'is_pcd', operator: 'equals', value: true }
  },
  {
    id: 'bank-elig-4',
    question: 'Você possui CNH válida?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vagas que exigem habilitação'
  },
  {
    id: 'bank-elig-5',
    question: 'Qual categoria da sua CNH?',
    type: 'multiple',
    category: 'eligibility',
    contextHint: 'Motoristas, vendedores externos',
    options: ['A', 'B', 'C', 'D', 'E', 'AB', 'Não possuo']
  },
  {
    id: 'bank-elig-6',
    question: 'Você possui veículo próprio para uso no trabalho?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vendas externas, representantes'
  },
  {
    id: 'bank-elig-7',
    question: 'Você possui passaporte válido?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vagas com viagens internacionais'
  },
  {
    id: 'bank-elig-8',
    question: 'Você possui visto de trabalho válido para o país da vaga?',
    type: 'yesno',
    category: 'eligibility',
    contextHint: 'Vagas internacionais'
  },

  // === DISPONIBILIDADE E MOBILIDADE ===
  {
    id: 'bank-avail-1',
    question: 'Você tem disponibilidade para viagens frequentes?',
    type: 'yesno',
    category: 'availability',
    contextHint: 'Comercial, consultoria, auditoria',
    triggerCondition: { field: 'travel_required', operator: 'equals', value: true }
  },
  {
    id: 'bank-avail-2',
    question: 'Qual percentual do tempo você aceitaria viajar? (0-100%)',
    type: 'scale',
    category: 'availability',
    contextHint: 'Seguimento - definir frequência de viagens'
  },
  {
    id: 'bank-avail-3',
    question: 'Você tem disponibilidade para mudança de cidade/estado?',
    type: 'yesno',
    category: 'availability',
    contextHint: 'Vagas em outras localidades',
    triggerCondition: { field: 'requires_relocation', operator: 'equals', value: true }
  },
  {
    id: 'bank-avail-4',
    question: 'Você aceitaria trabalhar em turnos/escalas?',
    type: 'yesno',
    category: 'availability',
    contextHint: 'Operações, indústria, varejo'
  },
  {
    id: 'bank-avail-5',
    question: 'Você tem disponibilidade para trabalhar aos finais de semana?',
    type: 'yesno',
    category: 'availability',
    contextHint: 'Varejo, operações, suporte'
  },
  {
    id: 'bank-avail-6',
    question: 'Você tem disponibilidade para trabalhar em horário noturno?',
    type: 'yesno',
    category: 'availability',
    contextHint: 'Operações, suporte 24h'
  },
  {
    id: 'bank-avail-7',
    question: 'Você pode iniciar imediatamente ou está cumprindo aviso prévio?',
    type: 'text',
    category: 'availability',
    contextHint: 'Urgência da contratação'
  },

  // === FORMAÇÃO E CERTIFICAÇÕES ===
  {
    id: 'bank-edu-1',
    question: 'Você possui formação superior completa?',
    type: 'yesno',
    category: 'education',
    contextHint: 'Vagas que exigem diploma'
  },
  {
    id: 'bank-edu-2',
    question: 'Qual sua área de formação?',
    type: 'text',
    category: 'education',
    contextHint: 'Seguimento - identificar área de estudo'
  },
  {
    id: 'bank-edu-3',
    question: 'Você possui pós-graduação, MBA ou mestrado?',
    type: 'yesno',
    category: 'education',
    contextHint: 'Cargos de liderança e especialistas'
  },
  {
    id: 'bank-edu-4',
    question: 'Você possui alguma certificação relevante para a área? Qual?',
    type: 'text',
    category: 'education',
    contextHint: 'PMP, AWS, CPA, ITIL, Six Sigma, etc.'
  },
  {
    id: 'bank-edu-5',
    question: 'Você está cursando faculdade atualmente?',
    type: 'yesno',
    category: 'education',
    contextHint: 'Vagas de estágio'
  },
  {
    id: 'bank-edu-6',
    question: 'Qual semestre você está cursando?',
    type: 'text',
    category: 'education',
    contextHint: 'Seguimento para estágio'
  },
  {
    id: 'bank-edu-7',
    question: 'Você possui registro ativo no conselho de classe? (CRM, CRC, CREA, OAB, etc.)',
    type: 'text',
    category: 'education',
    contextHint: 'Profissões regulamentadas'
  },

  // === EXPERIÊNCIA ESPECÍFICA ===
  {
    id: 'bank-exp-1',
    question: 'Você já trabalhou com SAP, Oracle ou outro ERP? Qual?',
    type: 'text',
    category: 'experience',
    contextHint: 'Vagas que exigem conhecimento em ERP'
  },
  {
    id: 'bank-exp-2',
    question: 'Quantos anos de experiência você tem com a tecnologia principal da vaga?',
    type: 'text',
    category: 'experience',
    contextHint: 'Tech, engenharia, especialistas'
  },
  {
    id: 'bank-exp-3',
    question: 'Você já liderou equipes? Se sim, de quantas pessoas?',
    type: 'text',
    category: 'experience',
    contextHint: 'Cargos de gestão'
  },
  {
    id: 'bank-exp-4',
    question: 'Você já atuou no segmento/indústria desta vaga?',
    type: 'yesno',
    category: 'experience',
    contextHint: 'Experiência setorial específica'
  },
  {
    id: 'bank-exp-5',
    question: 'Você tem experiência com vendas B2B ou B2C?',
    type: 'multiple',
    category: 'experience',
    contextHint: 'Comercial, vendas',
    options: ['B2B', 'B2C', 'Ambos', 'Nenhum']
  },
  {
    id: 'bank-exp-6',
    question: 'Qual foi seu ticket médio ou meta atingida no último ano?',
    type: 'text',
    category: 'experience',
    contextHint: 'Vendas, comercial'
  },

  // === IDIOMAS ===
  {
    id: 'bank-lang-1',
    question: 'Qual seu nível de inglês?',
    type: 'multiple',
    category: 'languages',
    contextHint: 'Multinacionais, tech, exportação',
    options: ['Básico', 'Intermediário', 'Avançado', 'Fluente', 'Nativo']
  },
  {
    id: 'bank-lang-2',
    question: 'Você possui certificação de inglês? (TOEFL, IELTS, Cambridge)',
    type: 'text',
    category: 'languages',
    contextHint: 'Vagas que exigem comprovação'
  },
  {
    id: 'bank-lang-3',
    question: 'Qual seu nível de espanhol?',
    type: 'multiple',
    category: 'languages',
    contextHint: 'Empresas latam',
    options: ['Básico', 'Intermediário', 'Avançado', 'Fluente', 'Nativo', 'Não falo']
  },
  {
    id: 'bank-lang-4',
    question: 'Você é fluente em outros idiomas? Quais?',
    type: 'text',
    category: 'languages',
    contextHint: 'Multinacionais'
  },

  // === REMUNERAÇÃO E CONTRATO ===
  {
    id: 'bank-comp-1',
    question: 'Você aceita contratação PJ?',
    type: 'yesno',
    category: 'compensation',
    contextHint: 'Vagas PJ',
    triggerCondition: { field: 'contract_type', operator: 'equals', value: 'pj' }
  },
  {
    id: 'bank-comp-2',
    question: 'Você aceita contrato temporário?',
    type: 'yesno',
    category: 'compensation',
    contextHint: 'Projetos, sazonais',
    triggerCondition: { field: 'contract_type', operator: 'equals', value: 'temporario' }
  },
  {
    id: 'bank-comp-3',
    question: 'A faixa salarial informada está alinhada com sua expectativa?',
    type: 'yesno',
    category: 'compensation',
    contextHint: 'Alinhamento de expectativas salariais'
  },
  {
    id: 'bank-comp-4',
    question: 'Você tem CNPJ ativo ou disponibilidade para abrir?',
    type: 'yesno',
    category: 'compensation',
    contextHint: 'Vagas PJ'
  },

  // === MODELO DE TRABALHO ===
  {
    id: 'bank-work-1',
    question: 'Você tem estrutura para home office? (internet estável, espaço adequado)',
    type: 'yesno',
    category: 'work_model',
    contextHint: 'Vagas remotas',
    triggerCondition: { field: 'work_model', operator: 'equals', value: 'remote' }
  },
  {
    id: 'bank-work-2',
    question: 'Você mora na região metropolitana da localidade da vaga?',
    type: 'yesno',
    category: 'work_model',
    contextHint: 'Vagas híbridas/presenciais'
  },
  {
    id: 'bank-work-3',
    question: 'Qual a distância aproximada da sua casa até o local de trabalho?',
    type: 'text',
    category: 'work_model',
    contextHint: 'Logística, tempo de deslocamento'
  },

  // === COMPLIANCE E CONFLITO DE INTERESSES ===
  {
    id: 'bank-compl-1',
    question: 'Você possui cláusula de não-competição com seu empregador atual?',
    type: 'yesno',
    category: 'compliance',
    contextHint: 'Cargos estratégicos, concorrentes'
  },
  {
    id: 'bank-compl-2',
    question: 'Você tem parentes trabalhando nesta empresa?',
    type: 'yesno',
    category: 'compliance',
    contextHint: 'Política de nepotismo'
  },
  {
    id: 'bank-compl-3',
    question: 'Você já trabalhou nesta empresa anteriormente?',
    type: 'yesno',
    category: 'compliance',
    contextHint: 'Recontratação'
  },
  {
    id: 'bank-compl-4',
    question: 'Você possui alguma pendência trabalhista com esta empresa?',
    type: 'yesno',
    category: 'compliance',
    contextHint: 'Histórico judicial'
  },
]

/** @deprecated Use ELIGIBILITY_QUESTIONS_BANK instead */
export const SCREENING_QUESTIONS_BANK = ELIGIBILITY_QUESTIONS_BANK

export function getQuestionsByCategory(category: QuestionCategory): EligibilityQuestionTemplate[] {
  return ELIGIBILITY_QUESTIONS_BANK.filter(q => q.category === category)
}

export function getAllCategories(): QuestionCategory[] {
  return Object.keys(QUESTION_CATEGORIES) as QuestionCategory[]
}

export function getSystemDefaultQuestions(): EligibilityQuestionTemplate[] {
  return ELIGIBILITY_QUESTIONS_BANK.filter(q => q.isSystemDefault === true)
}
