'use client'

import { useState, useEffect, useCallback } from 'react'
import { useCompanyId } from './useCompanyId'

export interface LiaInstructions {
  [fieldKey: string]: string
}

export interface LiaFieldToggles {
  [fieldKey: string]: boolean
}

export interface CompanyConfigForLia {
  seniority_levels: string[]
  default_behavioral_competencies: Array<{
    competency: string
    weight: 'Essencial' | 'Importante' | 'Desejável'
  }>
  default_salary_ranges: Array<{
    department?: string
    level: string
    min: number
    max: number
    currency: string
  }>
  lia_instructions: LiaInstructions
  lia_field_toggles: LiaFieldToggles
  work_model?: string
  hybrid_days_onsite?: number
  employment_types?: string[]
  locations?: string[]
  tech_stack?: Record<string, string[]>
  departments?: Array<{
    id: string
    name: string
    manager_name?: string
    headcount?: number
  }>
  benefits?: Array<{
    name: string
    category: string
    value?: number
  }>
  engineering_culture?: string
  default_languages?: string[]
  company_big_five?: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    stability: number
  }
  values?: string[]
  mission?: string
  vision?: string
  evp_bullets?: string[]
  leadership_style?: string
  team_dynamics?: string
  pipeline_stages?: Array<{
    name: string
    sla: number
  }>
  eligibility_questions?: Array<{
    question: string
    type: string
  }>
  headcount_planning?: Record<string, number>
}

export const LIA_FIELD_DEFINITIONS = {
  seniority_levels: { label: 'Níveis de Senioridade', category: 'Trabalho & Contratação', location: 'Dados da Empresa → Equipe' },
  work_model: { label: 'Modelo de Trabalho', category: 'Trabalho & Contratação', location: 'Dados da Empresa → Equipe' },
  hybrid_days_onsite: { label: 'Dias Presenciais (Híbrido)', category: 'Trabalho & Contratação', location: 'Dados da Empresa → Equipe' },
  employment_types: { label: 'Modelo de Contratação', category: 'Trabalho & Contratação', location: 'Dados da Empresa → Equipe' },
  salary_ranges: { label: 'Faixas Salariais', category: 'Trabalho & Contratação', location: 'Dados da Empresa → Equipe' },
  trade_name: { label: 'Nome Fantasia', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  industry: { label: 'Setor/Indústria', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  website: { label: 'Website', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  linkedin_url: { label: 'LinkedIn', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  company_size: { label: 'Tamanho da Empresa', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  employee_count: { label: 'Número de Funcionários', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  founded_year: { label: 'Ano de Fundação', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  mission: { label: 'Missão', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  vision: { label: 'Visão', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  values: { label: 'Valores', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  core_competencies: { label: 'Competências Essenciais', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  engineering_culture: { label: 'Cultura de Engenharia', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  default_languages: { label: 'Idiomas Padrão', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  company_big_five: { label: 'Perfil Big Five', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  departments: { label: 'Departamentos', category: 'Estrutura Organizacional', location: 'Dados da Empresa → Organização' },
  behavioral_competencies: { label: 'Competências Comportamentais', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  growth_opportunities: { label: 'Oportunidades de Crescimento', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  dei_initiatives: { label: 'Iniciativas DEI', category: 'ESG & Impacto', location: 'Dados da Empresa → Cultura' },
  sustainability: { label: 'Sustentabilidade', category: 'ESG & Impacto', location: 'Dados da Empresa → Cultura' },
  social_impact: { label: 'Impacto Social', category: 'ESG & Impacto', location: 'Dados da Empresa → Cultura' },
  evp_bullets: { label: 'EVP (Proposta de Valor)', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  tech_stack: { label: 'Tech Stack', category: 'Tecnologia', location: 'Dados da Empresa → Tecnologia' },
  benefits: { label: 'Benefícios', category: 'Remuneração e Benefícios', location: 'Dados da Empresa → Benefícios' },
  locations: { label: 'Localizações', category: 'Estrutura Organizacional', location: 'Dados da Empresa → Geral' },
  pipeline: { label: 'Pipeline', category: 'Recrutamento', location: 'Recrutamento → Pipeline' },
  eligibility_questions: { label: 'Perguntas de Elegibilidade', category: 'Recrutamento', location: 'Recrutamento → Elegibilidade' },
  headcount_planning: { label: 'Planejamento Headcount', category: 'Planejamento', location: 'Planejamento → Workforce' },
  leadership_style: { label: 'Estilo de Liderança', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  team_dynamics: { label: 'Dinâmica de Equipe', category: 'Cultura & Identidade', location: 'Dados da Empresa → Cultura' },
  variable_compensation: { label: 'Remuneração Variável', category: 'Remuneração e Benefícios', location: 'Dados da Empresa → Remuneração' },
  compensation_policies: { label: 'Políticas de Remuneração', category: 'Remuneração e Benefícios', location: 'Dados da Empresa → Remuneração' },
  company_description: { label: 'Descrição da Empresa', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  headquarters: { label: 'Sede da Empresa', category: 'Informações da Empresa', location: 'Dados da Empresa → Geral' },
  policy_instructions: { label: 'Instruções de Política', category: 'Recrutamento', location: 'Configurações → Políticas' },
  // Per-channel screening AI toggles — control whether IA triagem is active per channel
  screening_channel_chat_web: { label: 'IA via Chat Web', category: 'Triagem por Canal', location: 'Configurações → Triagem' },
  screening_channel_whatsapp: { label: 'IA via WhatsApp', category: 'Triagem por Canal', location: 'Configurações → Triagem' },
  screening_channel_phone_pstn: { label: 'IA via Ligação (PSTN)', category: 'Triagem por Canal', location: 'Configurações → Triagem' },
  screening_channel_voice_web: { label: 'IA via Voz no Navegador', category: 'Triagem por Canal', location: 'Configurações → Triagem' },
} as const

export type LiaFieldKey = keyof typeof LIA_FIELD_DEFINITIONS

interface UseCompanyLiaInstructionsResult {
  config: CompanyConfigForLia | null
  instructions: LiaInstructions
  toggles: LiaFieldToggles
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getInstructionForField: (fieldKey: string) => string | undefined
  isFieldActive: (fieldKey: string) => boolean
  getActiveFields: () => LiaFieldKey[]
  getInactiveFields: () => LiaFieldKey[]
  getSeniorityLevels: () => string[]
  getBehavioralCompetencies: () => CompanyConfigForLia['default_behavioral_competencies']
  getSalaryRangeForLevel: (level: string, department?: string) => CompanyConfigForLia['default_salary_ranges'][0] | undefined
  buildContextPrompt: () => string
  getFieldDefinition: (fieldKey: string) => typeof LIA_FIELD_DEFINITIONS[LiaFieldKey] | undefined
}

const DEFAULT_TOGGLES: LiaFieldToggles = {
  seniority_levels: true,
  work_model: true,
  hybrid_days_onsite: true,
  employment_types: true,
  salary_ranges: true,
  trade_name: true,
  industry: true,
  website: true,
  linkedin_url: true,
  company_size: true,
  employee_count: true,
  founded_year: true,
  mission: true,
  vision: true,
  values: true,
  core_competencies: true,
  engineering_culture: true,
  default_languages: true,
  company_big_five: true,
  departments: true,
  behavioral_competencies: true,
  growth_opportunities: true,
  dei_initiatives: true,
  sustainability: true,
  social_impact: true,
  evp_bullets: true,
  tech_stack: true,
  benefits: true,
  locations: true,
  pipeline: true,
  eligibility_questions: true,
  headcount_planning: true,
  leadership_style: true,
  team_dynamics: true,
}

const DEFAULT_CONFIG: CompanyConfigForLia = {
  seniority_levels: ['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'],
  default_behavioral_competencies: [],
  default_salary_ranges: [],
  lia_instructions: {},
  lia_field_toggles: DEFAULT_TOGGLES,
  work_model: '',
  hybrid_days_onsite: 3,
  employment_types: ['CLT'],
  locations: [],
  tech_stack: {}
}

export function useCompanyLiaInstructions(): UseCompanyLiaInstructionsResult {
  const [config, setConfig] = useState<CompanyConfigForLia | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()

  const fetchConfig = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`)
      
      if (!response.ok) {
        // 404 = not found, 422 = invalid company_id format (e.g., "default" instead of UUID)
        if (response.status === 404 || response.status === 422) {
          setConfig(DEFAULT_CONFIG)
          return
        }
        throw new Error(`Failed to fetch company config: ${response.status}`)
      }

      const data = await response.json()
      
      setConfig({
        seniority_levels: data.seniority_levels || DEFAULT_CONFIG.seniority_levels,
        default_behavioral_competencies: data.default_behavioral_competencies || [],
        default_salary_ranges: data.default_salary_ranges || [],
        lia_instructions: data.lia_instructions || {},
        lia_field_toggles: { ...DEFAULT_TOGGLES, ...(data.lia_field_toggles || {}) },
        work_model: data.work_model || '',
        hybrid_days_onsite: data.hybrid_days_onsite || 3,
        employment_types: data.employment_types || ['CLT'],
        locations: data.locations || [],
        tech_stack: data.tech_stack || {},
        departments: data.departments || [],
        benefits: data.benefits || [],
        engineering_culture: data.engineering_culture || '',
        default_languages: data.default_languages || [],
        company_big_five: data.company_big_five || null,
        values: data.values || [],
        mission: data.mission || '',
        vision: data.vision || '',
        evp_bullets: data.evp_bullets || [],
        leadership_style: data.leadership_style || '',
        team_dynamics: data.team_dynamics || '',
        pipeline_stages: data.pipeline_stages || [],
        eligibility_questions: data.eligibility_questions || [],
        headcount_planning: data.headcount_planning || {}
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load company config')
      setConfig(DEFAULT_CONFIG)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    if (!isLoadingCompany && companyId) {
      fetchConfig()
    } else if (!isLoadingCompany && !companyId) {
      setConfig(DEFAULT_CONFIG)
      setIsLoading(false)
    }
  }, [fetchConfig, isLoadingCompany, companyId])

  const getInstructionForField = useCallback((fieldKey: string): string | undefined => {
    return config?.lia_instructions?.[fieldKey]
  }, [config])

  const isFieldActive = useCallback((fieldKey: string): boolean => {
    return config?.lia_field_toggles?.[fieldKey] ?? DEFAULT_TOGGLES[fieldKey as LiaFieldKey] ?? false
  }, [config])

  const getActiveFields = useCallback((): LiaFieldKey[] => {
    const toggles = config?.lia_field_toggles || DEFAULT_TOGGLES
    return (Object.keys(LIA_FIELD_DEFINITIONS) as LiaFieldKey[]).filter(key => toggles[key])
  }, [config])

  const getInactiveFields = useCallback((): LiaFieldKey[] => {
    const toggles = config?.lia_field_toggles || DEFAULT_TOGGLES
    return (Object.keys(LIA_FIELD_DEFINITIONS) as LiaFieldKey[]).filter(key => !toggles[key])
  }, [config])

  const getSeniorityLevels = useCallback((): string[] => {
    return config?.seniority_levels || DEFAULT_CONFIG.seniority_levels
  }, [config])

  const getBehavioralCompetencies = useCallback(() => {
    return config?.default_behavioral_competencies || []
  }, [config])

  const getSalaryRangeForLevel = useCallback((level: string, department?: string) => {
    const ranges = config?.default_salary_ranges || []
    return ranges.find(r => 
      r.level === level && 
      (department ? r.department === department : true)
    )
  }, [config])

  const getFieldDefinition = useCallback((fieldKey: string) => {
    return LIA_FIELD_DEFINITIONS[fieldKey as LiaFieldKey]
  }, [])

  const buildContextPrompt = useCallback((): string => {
    if (!config) return ''

    const parts: string[] = []
    const toggles = config.lia_field_toggles || DEFAULT_TOGGLES

    // Only include fields that are active (toggled on)
    if (config.lia_instructions) {
      const instructionParts: string[] = []
      
      Object.entries(config.lia_instructions).forEach(([key, value]) => {
        // Only include if field is active AND has instruction
        if (toggles[key] && value && value.trim()) {
          const fieldDef = LIA_FIELD_DEFINITIONS[key as LiaFieldKey]
          const label = fieldDef?.label || key
          instructionParts.push(`- ${label}: ${value}`)
        }
      })

      if (instructionParts.length > 0) {
        parts.push('**Instruções específicas do recrutador:**')
        parts.push(instructionParts.join('\n'))
      }
    }

    // Seniority levels (if active)
    if (toggles.seniority_levels && config.seniority_levels.length > 0) {
      parts.push(`**Níveis de senioridade usados:** ${config.seniority_levels.join(', ')}`)
    }

    // Behavioral competencies (if active)
    if (toggles.behavioral_competencies && config.default_behavioral_competencies.length > 0) {
      const competencies = config.default_behavioral_competencies
        .map(c => `${c.competency} (${c.weight})`)
        .join(', ')
      parts.push(`**Competências comportamentais padrão:** ${competencies}`)
    }

    // Work model (if active)
    if (toggles.work_model && config.work_model) {
      const workModelLabels: Record<string, string> = {
        remote: '100% Remoto',
        hybrid: `Híbrido (${config.hybrid_days_onsite} dias presenciais)`,
        onsite: 'Presencial',
        flexible: 'Flexível'
      }
      parts.push(`**Modelo de trabalho preferido:** ${workModelLabels[config.work_model] || config.work_model}`)
    }

    // Employment types (if active)
    if (toggles.employment_types && config.employment_types && config.employment_types.length > 0) {
      parts.push(`**Tipos de contratação:** ${config.employment_types.join(', ')}`)
    }

    // Locations (if active)
    if (toggles.locations && config.locations && config.locations.length > 0) {
      parts.push(`**Localizações:** ${config.locations.join(', ')}`)
    }

    // Tech stack (if active)
    if (toggles.tech_stack && config.tech_stack) {
      const allTechs = Object.values(config.tech_stack).flat()
      if (allTechs.length > 0) {
        parts.push(`**Stack tecnológico:** ${allTechs.slice(0, 15).join(', ')}${allTechs.length > 15 ? '...' : ''}`)
      }
    }

    // Benefits (if active)
    if (toggles.benefits && config.benefits && config.benefits.length > 0) {
      const benefitNames = config.benefits.slice(0, 10).map(b => b.name)
      parts.push(`**Benefícios principais:** ${benefitNames.join(', ')}`)
    }

    // Departments (if active)
    if (toggles.departments && config.departments && config.departments.length > 0) {
      const deptNames = config.departments.map(d => d.name)
      parts.push(`**Departamentos:** ${deptNames.join(', ')}`)
    }

    // Engineering culture (if active)
    if (toggles.engineering_culture && config.engineering_culture) {
      parts.push(`**Cultura de engenharia:** ${config.engineering_culture}`)
    }

    // Languages (if active)
    if (toggles.default_languages && config.default_languages && config.default_languages.length > 0) {
      parts.push(`**Idiomas padrão:** ${config.default_languages.join(', ')}`)
    }

    // Values (if active)
    if (toggles.values && config.values && config.values.length > 0) {
      parts.push(`**Valores da empresa:** ${config.values.join(', ')}`)
    }

    // EVP (if active)
    if (toggles.evp_bullets && config.evp_bullets && config.evp_bullets.length > 0) {
      parts.push(`**Proposta de valor (EVP):** ${config.evp_bullets.join('; ')}`)
    }

    // Leadership style (if active)
    if (toggles.leadership_style && config.leadership_style) {
      parts.push(`**Estilo de liderança:** ${config.leadership_style}`)
    }

    // Team dynamics (if active)
    if (toggles.team_dynamics && config.team_dynamics) {
      parts.push(`**Dinâmica de equipe:** ${config.team_dynamics}`)
    }

    // Big Five (if active)
    if (toggles.company_big_five && config.company_big_five) {
      const bf = config.company_big_five
      parts.push(`**Perfil comportamental (Big Five):** Abertura: ${bf.openness}, Conscienciosidade: ${bf.conscientiousness}, Extroversão: ${bf.extraversion}, Amabilidade: ${bf.agreeableness}, Estabilidade: ${bf.stability}`)
    }

    // Salary ranges (if active)
    if (toggles.salary_ranges && config.default_salary_ranges.length > 0) {
      const ranges = config.default_salary_ranges.slice(0, 5).map(r => 
        `${r.level}: ${r.currency} ${r.min.toLocaleString()}-${r.max.toLocaleString()}`
      )
      parts.push(`**Faixas salariais:** ${ranges.join(', ')}`)
    }

    return parts.join('\n\n')
  }, [config])

  return {
    config,
    instructions: config?.lia_instructions || {},
    toggles: config?.lia_field_toggles || DEFAULT_TOGGLES,
    isLoading,
    error,
    refetch: fetchConfig,
    getInstructionForField,
    isFieldActive,
    getActiveFields,
    getInactiveFields,
    getSeniorityLevels,
    getBehavioralCompetencies,
    getSalaryRangeForLevel,
    buildContextPrompt,
    getFieldDefinition
  }
}
