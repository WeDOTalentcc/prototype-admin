"use client"

import { useState, useEffect, useCallback } from "react"
import type { TechnicalSkill, BasicInfoFields, SalaryInfo, DetectedCriteria, Benefit } from '../ExpandedChatContext'
import type { FieldOrigin } from '../../job-creation/field-origin-badge'
import type { JobConfig } from './usePublishingState'

export interface CompanyConfig {
  workModel?: string
  hybridDaysOnsite?: number
  employmentTypes?: string[]
  techStack?: string[]
  values?: string[]
  coreCompetencies?: string[]
  departments?: { id: string; name: string }[]
  benefits?: { name: string; category: string; value?: number; is_active: boolean }[]
  evpBullets?: string[]
  headquarters?: string
  locations?: string[]
}

export interface WizardGreetingData {
  greeting_message: string
  catalog_status: {
    company_id: string
    maturity_score: number
    maturity_level: 'complete' | 'partial' | 'minimal'
    maturity_factors: string[]
    smart_start_enabled: boolean
    required_fields_for_wizard: string[]
    available_data_summary: string[]
    counts: Record<string, number>
    recommendations: string[]
  }
  prefill_data: Record<string, unknown>
}

export interface UseCompanyConfigFetchOptions {
  isOpen: boolean
  isInJobCreationMode: boolean
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>
  setFieldOrigins: React.Dispatch<React.SetStateAction<Record<string, { source: FieldOrigin; confidence: number }>>>
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  setCompanyMembersMap: (map: Map<string, string>) => void
  basicInfoFields: BasicInfoFields
}

export interface UseCompanyConfigFetchReturn {
  companyConfig: CompanyConfig | null
  configLoaded: boolean
  fieldsFromConfig: Set<string>
  wizardGreeting: WizardGreetingData | null
  wizardGreetingLoaded: boolean
}

export function useCompanyConfigFetch(options: UseCompanyConfigFetchOptions): UseCompanyConfigFetchReturn {
  const {
    isOpen, isInJobCreationMode,
    setBasicInfoFields, setDetectedCriteria, setTechnicalSkills,
    setSalaryInfo, setFieldOrigins, setJobConfig, setCompanyMembersMap,
    basicInfoFields,
  } = options

  const [companyConfig, setCompanyConfig] = useState<CompanyConfig | null>(null)
  const [configLoaded, setConfigLoaded] = useState(false)
  const [fieldsFromConfig, setFieldsFromConfig] = useState<Set<string>>(new Set())
  const [wizardGreeting, setWizardGreeting] = useState<WizardGreetingData | null>(null)
  const [wizardGreetingLoaded, setWizardGreetingLoaded] = useState(false)

  useEffect(() => {
    const fetchCompanyConfig = async () => {
      if (!isOpen || !isInJobCreationMode || configLoaded) return

      try {
        const [profileRes, departmentsRes, benefitsRes, greetingRes] = await Promise.all([
          fetch('/api/backend-proxy/company/profile'),
          fetch('/api/backend-proxy/company/departments'),
          fetch('/api/backend-proxy/company/benefits/?company_id=default'),
          fetch('/api/backend-proxy/company/smart-wizard-greeting?company_id=default')
        ])

        const config: CompanyConfig = {}
        const newFieldsFromConfig = new Set<string>()

        if (profileRes.ok) {
          const profileData = await profileRes.json()
          if (profileData.work_model) {
            config.workModel = profileData.work_model
          }
          if (profileData.hybrid_days_onsite) {
            config.hybridDaysOnsite = profileData.hybrid_days_onsite
          }
          if (profileData.employment_types && Array.isArray(profileData.employment_types)) {
            config.employmentTypes = profileData.employment_types
          }
          if (profileData.tech_stack && Array.isArray(profileData.tech_stack)) {
            config.techStack = profileData.tech_stack.map((t: string) => {
              const parts = t.split(':')
              return parts.length > 1 ? parts[1] : t
            })
          }
          if (profileData.values) config.values = profileData.values
          if (profileData.coreCompetencies) config.coreCompetencies = profileData.coreCompetencies
          if (profileData.evp_bullets) config.evpBullets = profileData.evp_bullets
          if (profileData.headquarters) config.headquarters = profileData.headquarters
          if (profileData.locations) config.locations = profileData.locations
        }

        if (departmentsRes.ok) {
          const departmentsData = await departmentsRes.json()
          if (Array.isArray(departmentsData)) {
            config.departments = (departmentsData as { id: string; name: string }[]).map((d) => ({
              id: d.id,
              name: d.name
            }))

            const membersMap = new Map<string, string>()
            try {
              const memberPromises = (departmentsData as { id: string }[]).map(async (dept) => {
                try {
                  const membersRes = await fetch(`/api/backend-proxy/company/departments/${dept.id}/members`)
                  if (membersRes.ok) {
                    const members = await membersRes.json()
                    if (Array.isArray(members)) {
                      (members as { name?: string; email?: string }[]).forEach((m) => {
                        if (m.name && m.email) {
                          membersMap.set(m.name.trim().toLowerCase(), m.email)
                          membersMap.set(m.name.trim(), m.email)
                        }
                      })
                    }
                  }
                } catch (err) {
                }
              })
              await Promise.all(memberPromises)
              setCompanyMembersMap(membersMap)
            } catch (err) {
            }
          }
        }

        if (benefitsRes.ok) {
          const benefitsData = await benefitsRes.json()
          const benefitsList = Array.isArray(benefitsData) ? benefitsData : benefitsData.items || []
          config.benefits = (benefitsList as { name: string; category: string; value?: number; is_active: boolean }[]).filter((b) => b.is_active)
        }

        if (greetingRes.ok) {
          const greetingData = await greetingRes.json()
          if (greetingData.greeting_message && greetingData.catalog_status) {
            setWizardGreeting(greetingData)

            const prefillData = greetingData.prefill_data || {}

            if (prefillData.departments && Array.isArray(prefillData.departments) && prefillData.departments.length > 0) {
              if (!config.departments || config.departments.length === 0) {
                config.departments = (prefillData.departments as ({ id?: string; name?: string } | string)[]).map((d, idx) => ({
                  id: (typeof d === 'object' ? d.id : undefined) || `prefill-dept-${idx}`,
                  name: (typeof d === 'object' ? d.name : d) || ''
                }))
              }
            }

            if (prefillData.benefits && Array.isArray(prefillData.benefits) && prefillData.benefits.length > 0) {
              if (!config.benefits || config.benefits.length === 0) {                // @ts-ignore // TODO: fix type
                config.benefits = (prefillData.benefits as { id?: string; name: string; value?: number; is_active?: boolean }[]).map((b) => ({
                  id: b.id,
                  name: b.name,
                  value: b.value,
                  is_active: b.is_active ?? true
                }))
              }
            }

            if (prefillData.tech_stack && Array.isArray(prefillData.tech_stack) && prefillData.tech_stack.length > 0) {
              const existingTechStack = config.techStack || []
              const prefillTechStack = (prefillData.tech_stack as string[]).map((t) => {
                const parts = t.split(':')
                return parts.length > 1 ? parts[1] : t
              })
              const mergedTechStack = [...new Set([...existingTechStack, ...prefillTechStack])]
              config.techStack = mergedTechStack
            }
          }
        }

        setWizardGreetingLoaded(true)

        setCompanyConfig(config)

        if (config.workModel) {
          const workModelMap: Record<string, string> = {
            'remote': 'Remoto',
            'hybrid': 'Híbrido',
            'onsite': 'Presencial',
            'remoto': 'Remoto',
            'híbrido': 'Híbrido',
            'presencial': 'Presencial'
          }
          const mappedModel = workModelMap[config.workModel.toLowerCase()] || config.workModel
          setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          newFieldsFromConfig.add('modeloTrabalho')
          setFieldOrigins(prev => ({ ...prev, work_model: { source: 'default', confidence: 0.85 } }))
        }

        if (config.employmentTypes && config.employmentTypes.length > 0) {
          setBasicInfoFields(prev => ({ ...prev, tipoContrato: config.employmentTypes![0] }))
          newFieldsFromConfig.add('tipoContrato')
          setFieldOrigins(prev => ({ ...prev, employment_type: { source: 'default', confidence: 0.85 } }))
        }

        if (config.hybridDaysOnsite) {
          setJobConfig((prev) => ({ ...prev, hybridDaysOnsite: config.hybridDaysOnsite }))
        }

        if (config.headquarters || (config.locations && config.locations.length > 0)) {
          const location = config.headquarters || config.locations?.[0] || ''
          if (location) {
            setBasicInfoFields(prev => ({ ...prev, localidade: location }))
            setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
            setFieldOrigins(prev => ({ ...prev, location: { source: 'default', confidence: 0.85 } }))
            newFieldsFromConfig.add('localizacao')
          }
        }

        if (config.departments && config.departments.length > 0 && !basicInfoFields.area) {
          setBasicInfoFields(prev => ({ ...prev, area: config.departments![0].name }))
          newFieldsFromConfig.add('area')
        }

        if (config.techStack && config.techStack.length > 0) {
          const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
            'Python': 'language', 'JavaScript': 'language', 'TypeScript': 'language', 'Java': 'language',
            'Go': 'language', 'Rust': 'language', 'C#': 'language', 'Ruby': 'language', 'PHP': 'language',
            'Node.js': 'framework', 'React': 'framework', 'Angular': 'framework', 'Vue.js': 'framework',
            'Django': 'framework', 'FastAPI': 'framework', 'Flask': 'framework', 'Spring': 'framework',
            'Next.js': 'framework', 'Express': 'framework', 'React Native': 'framework', 'Flutter': 'framework',
            'PostgreSQL': 'database', 'MySQL': 'database', 'MongoDB': 'database', 'Redis': 'database',
            'Elasticsearch': 'database', 'SQL': 'database', 'Oracle': 'database',
            'Docker': 'tool', 'Kubernetes': 'tool', 'AWS': 'tool', 'Azure': 'tool', 'GCP': 'tool',
            'Git': 'tool', 'Jenkins': 'tool', 'Terraform': 'tool', 'Linux': 'tool',
          }

          const configSkills: TechnicalSkill[] = config.techStack.slice(0, 5).map((tech, idx) => ({
            id: `config-skill-${idx}`,
            name: tech,
            level: 'Intermediário' as const,
            required: false,
            category: skillCategories[tech] || 'tool',
            weight: 2
          }))

          setTechnicalSkills(prev => {
            const existingNames = prev.map(s => s.name.toLowerCase())
            const newSkills = configSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
            return [...prev, ...newSkills]
          })

          if (configSkills.length > 0) {
            newFieldsFromConfig.add('competenciasTecnicas')
          }
        }

        if (config.benefits && config.benefits.length > 0) {
          const configBenefits: Benefit[] = config.benefits.map((b, idx) => ({
            id: `config-benefit-${idx}`,
            name: b.name,
            value: b.value ? `R$ ${b.value}` : undefined,
            enabled: true
          }))

          setSalaryInfo(prev => {
            const existingNames = prev.benefits.map(b => b.name.toLowerCase())
            const newBenefits = configBenefits.filter(b => !existingNames.includes(b.name.toLowerCase()))
            return {
              ...prev,
              benefits: [...prev.benefits, ...newBenefits]
            }
          })

          if (configBenefits.length > 0) {
            newFieldsFromConfig.add('benefits')
          }
        }

        setFieldsFromConfig(newFieldsFromConfig)
        setConfigLoaded(true)

      } catch (error) {
        setConfigLoaded(true)
        setWizardGreetingLoaded(true)
      }
    }

    fetchCompanyConfig()
  }, [isOpen, isInJobCreationMode, configLoaded, basicInfoFields.modeloTrabalho, basicInfoFields.localidade, basicInfoFields.area, setBasicInfoFields, setCompanyMembersMap, setDetectedCriteria, setFieldOrigins, setJobConfig, setSalaryInfo, setTechnicalSkills])

  return {
    companyConfig,
    configLoaded,
    fieldsFromConfig,
    wizardGreeting,
    wizardGreetingLoaded,
  }
}
