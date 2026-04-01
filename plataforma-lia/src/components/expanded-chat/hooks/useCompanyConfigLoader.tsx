"use client"

import { useEffect } from "react"
import type { TechnicalSkill } from '..'
import type { Benefit } from '../stages/SalaryStage'

interface UseCompanyConfigLoaderCtx {
  isOpen: boolean
  isInJobCreationMode: boolean
  configLoaded: boolean
  basicInfoFields: {
    area: string
    modeloTrabalho: string
    localidade: string
  }
  companyEligibilityQuestions: Array<{
    id: string
    question_text: string
    is_active: boolean
  }>
  isLoadingEligibilityQuestions: boolean
  isLoadingStages: boolean
  sla: {
    calculateDeadline: (sla: number) => string
    screeningSLA: number
    shortlistSLA: number
    totalSLA: number
  } | null | undefined
  technicalSkills: TechnicalSkill[]
  setBasicInfoFields: (fn: (prev: any) => any) => void
  setDetectedCriteria: (fn: (prev: any) => any) => void
  setFieldOrigins: (fn: (prev: any) => any) => void
  setFieldsFromConfig: (fields: Set<string>) => void
  setJobConfig: (fn: (prev: any) => any) => void
  setCompanyConfig: (config: any) => void
  setCompanyMembersMap: (map: Map<string, string>) => void
  setCompanyDefaultQuestions: (questions: any[]) => void
  setConfigLoaded: (val: boolean) => void
  setTechnicalSkills: (fn: (prev: TechnicalSkill[]) => TechnicalSkill[]) => void
  setSalaryInfo: (fn: (prev: any) => any) => void
  setWizardGreeting: (data: any) => void
  setWizardGreetingLoaded: (val: boolean) => void
}

export function useCompanyConfigLoader(ctx: UseCompanyConfigLoaderCtx) {
  const {
    isOpen, isInJobCreationMode, configLoaded,
    basicInfoFields, companyEligibilityQuestions, isLoadingEligibilityQuestions,
    isLoadingStages, sla, technicalSkills,
    setBasicInfoFields, setDetectedCriteria, setFieldOrigins, setFieldsFromConfig,
    setJobConfig, setCompanyConfig, setCompanyMembersMap, setCompanyDefaultQuestions,
    setConfigLoaded, setTechnicalSkills, setSalaryInfo, setWizardGreeting, setWizardGreetingLoaded,
  } = ctx

  // Fetch company configuration when modal opens in job creation mode
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

        const config: Record<string, any> = {}
        const newFieldsFromConfig = new Set<string>()

        if (profileRes.ok) {
          const profileData = await profileRes.json()
          if (profileData.work_model) config.workModel = profileData.work_model
          if (profileData.hybrid_days_onsite) config.hybridDaysOnsite = profileData.hybrid_days_onsite
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
            config.departments = departmentsData.map((d: Record<string, unknown>) => ({
              id: d.id,
              name: d.name
            }))

            const membersMap = new Map<string, string>()
            try {
              const memberPromises = departmentsData.map(async (dept: Record<string, unknown>) => {
                try {
                  const membersRes = await fetch(`/api/backend-proxy/company/departments/${dept.id}/members`)
                  if (membersRes.ok) {
                    const members = await membersRes.json()
                    if (Array.isArray(members)) {
                      members.forEach((m: Record<string, unknown>) => {
                        if (m.name && m.email) {
                          const mName = String(m.name)
                          const mEmail = String(m.email)
                          membersMap.set(mName.trim().toLowerCase(), mEmail)
                          membersMap.set(mName.trim(), mEmail)
                        }
                      })
                    }
                  }
                } catch (_err) {}
              })
              await Promise.all(memberPromises)
              setCompanyMembersMap(membersMap)
            } catch (_err) {}
          }
        }

        if (benefitsRes.ok) {
          const benefitsData = await benefitsRes.json()
          const benefitsList = Array.isArray(benefitsData) ? benefitsData : benefitsData.items || []
          config.benefits = benefitsList.filter((b: Record<string, unknown>) => b.is_active)
        }

        if (greetingRes.ok) {
          const greetingData = await greetingRes.json()
          if (greetingData.greeting_message && greetingData.catalog_status) {
            setWizardGreeting(greetingData)

            const prefillData = greetingData.prefill_data || {}

            if (prefillData.departments && Array.isArray(prefillData.departments) && prefillData.departments.length > 0) {
              if (!config.departments || config.departments.length === 0) {
                config.departments = prefillData.departments.map((d: Record<string, unknown>, idx: number) => ({
                  id: d.id || `prefill-dept-${idx}`,
                  name: d.name || d
                }))
              }
            }

            if (prefillData.benefits && Array.isArray(prefillData.benefits) && prefillData.benefits.length > 0) {
              if (!config.benefits || config.benefits.length === 0) {
                config.benefits = prefillData.benefits.map((b: Record<string, unknown>) => ({
                  id: b.id,
                  name: b.name,
                  value: b.value,
                  is_active: b.is_active ?? true
                }))
              }
            }

            if (prefillData.tech_stack && Array.isArray(prefillData.tech_stack) && prefillData.tech_stack.length > 0) {
              const existingTechStack = config.techStack || []
              const prefillTechStack = prefillData.tech_stack.map((t: string) => {
                const parts = t.split(':')
                return parts.length > 1 ? parts[1] : t
              })
              config.techStack = [...new Set([...existingTechStack, ...prefillTechStack])]
            }
          }
        }

        setWizardGreetingLoaded(true)
        setCompanyConfig(config)

        if (config.workModel) {
          const workModelMap: Record<string, string> = {
            'remote': 'Remoto', 'hybrid': 'Híbrido', 'onsite': 'Presencial',
            'remoto': 'Remoto', 'híbrido': 'Híbrido', 'presencial': 'Presencial'
          }
          const mappedModel = workModelMap[config.workModel.toLowerCase()] || config.workModel
          setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          newFieldsFromConfig.add('modeloTrabalho')
          setFieldOrigins(prev => ({ ...prev, work_model: { source: 'default', confidence: 0.85 } }))
        }

        if (config.employmentTypes && config.employmentTypes.length > 0) {
          setBasicInfoFields(prev => ({ ...prev, tipoContrato: config.employmentTypes[0] }))
          newFieldsFromConfig.add('tipoContrato')
          setFieldOrigins(prev => ({ ...prev, employment_type: { source: 'default', confidence: 0.85 } }))
        }

        if (config.hybridDaysOnsite) {
          setJobConfig(prev => ({ ...prev, hybridDaysOnsite: config.hybridDaysOnsite }))
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
          setBasicInfoFields(prev => ({ ...prev, area: config.departments[0].name }))
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

          const configSkills: TechnicalSkill[] = config.techStack.slice(0, 5).map((tech: string, idx: number) => ({
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

          if (configSkills.length > 0) newFieldsFromConfig.add('competenciasTecnicas')
        }

        if (config.benefits && config.benefits.length > 0) {
          const configBenefits: Benefit[] = config.benefits.map((b: any, idx: number) => ({
            id: `config-benefit-${idx}`,
            name: b.name,
            value: b.value ? `R$ ${b.value}` : undefined,
            enabled: true
          }))

          setSalaryInfo(prev => {
            const existingNames = prev.benefits.map((b: any) => b.name.toLowerCase())
            const newBenefits = configBenefits.filter(b => !existingNames.includes(b.name.toLowerCase()))
            return { ...prev, benefits: [...prev.benefits, ...newBenefits] }
          })

          if (configBenefits.length > 0) newFieldsFromConfig.add('benefits')
        }

        setFieldsFromConfig(newFieldsFromConfig)
        setConfigLoaded(true)

      } catch (_error) {
        setConfigLoaded(true)
        setWizardGreetingLoaded(true)
      }
    }

    fetchCompanyConfig()
  }, [isOpen, isInJobCreationMode, configLoaded, basicInfoFields.modeloTrabalho, basicInfoFields.localidade])

  // Sync company screening questions from settings with companyDefaultQuestions state
  useEffect(() => {
    if (!isLoadingEligibilityQuestions) {
      const mappedQuestions = companyEligibilityQuestions.map(q => ({
        id: q.id,
        question: q.question_text,
        type: 'open' as const,
        enabled: q.is_active,
        fromConfig: true
      }))
      setCompanyDefaultQuestions(mappedQuestions)
    }
  }, [companyEligibilityQuestions, isLoadingEligibilityQuestions])

  // Sync deadlines with SLAs from recruitment stages configuration
  useEffect(() => {
    if (!isLoadingStages && sla) {
      setJobConfig(prev => ({
        ...prev,
        deadlineScreening: sla.calculateDeadline(sla.screeningSLA),
        deadlineShortlist: sla.calculateDeadline(sla.shortlistSLA),
        deadline: sla.calculateDeadline(sla.totalSLA)
      }))
    }
  }, [isLoadingStages, sla])
}
