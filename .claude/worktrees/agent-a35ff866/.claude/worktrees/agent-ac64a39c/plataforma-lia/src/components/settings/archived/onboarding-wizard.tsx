"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  X, ChevronRight, ChevronLeft, Building2, Briefcase, MessageSquare, UserCircle,
  CheckCircle2, Clock, Upload, Globe, Users, Phone, Mail, MessageCircle,
  Zap, Target, Brain, AlertCircle, FileCheck, TrendingUp, Settings2,
  Lightbulb, BarChart3, ShieldCheck, Linkedin
} from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { CultureAnalyzer } from "./CultureAnalyzer"
import { CultureProfile } from "./CultureProfilePreview"
import { RecruitmentJourneyConfig, DEFAULT_STAGES, RecruitmentStage } from "./RecruitmentJourneyConfig"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { IndustrySingleSelect } from "@/components/search/IndustrySingleSelect"

interface OnboardingData {
  companyName: string
  tradeName: string
  cnpj: string
  address: string
  workModel: string
  logoUrl: string
  sector: string
  employeeCount: string
  companySize: string
  foundedYear: string
  techStack: string[]
  website: string
  linkedinUrl: string
  companyEmail: string
  companyPhone: string
  growthOpportunities: string
  teamDynamics: string
  leadershipStyle: string
  deiInitiatives: string
  sustainability: string
  socialImpact: string
  engineeringCulture: string
  hiringVolume: number
  jobTypes: string[]
  currentAts: string
  mainChallenges: string[]
  mainPriority: string
  platformExpectations: string
  communicationChannels: string[]
  allowLiaContact: boolean
  additionalNotes: string
  responsibleName: string
  responsibleEmail: string
  responsiblePhone: string
  responsiblePosition: string
  preferredContactTime: string
  cultureProfile?: CultureProfile | null
  recruitmentStages: RecruitmentStage[]
}

interface OnboardingWizardProps {
  onClose: () => void
  onComplete: (data: OnboardingData) => void
  currentSection?: string
  initialData?: Partial<OnboardingData>
}


const EMPLOYEE_RANGES = [
  { value: "1-50", label: "1-50 funcionários" },
  { value: "51-200", label: "51-200 funcionários" },
  { value: "201-500", label: "201-500 funcionários" },
  { value: "501-1000", label: "501-1000 funcionários" },
  { value: "1001-5000", label: "1001-5000 funcionários" },
  { value: "5000+", label: "Mais de 5000 funcionários" }
]

const JOB_TYPES = [
  { value: "operacionais", label: "Operacionais" },
  { value: "tecnicos", label: "Técnicos" },
  { value: "gestao", label: "Gestão" },
  { value: "c-level", label: "C-Level" }
]

const ATS_OPTIONS = [
  // ATS Brasileiros
  { value: "gupy", label: "Gupy" },
  { value: "pandape", label: "Pandapé" },
  { value: "inhire", label: "Inhire" },
  { value: "abler", label: "Abler" },
  { value: "kenoby", label: "Kenoby" },
  { value: "solides", label: "Sólides" },
  { value: "recrutei", label: "Recrutei" },
  { value: "senior", label: "Senior Sistemas" },
  { value: "vagas", label: "Vagas.com" },
  // ATS Globais
  { value: "greenhouse", label: "Greenhouse" },
  { value: "workday", label: "Workday" },
  { value: "lever", label: "Lever" },
  { value: "icims", label: "iCIMS" },
  { value: "smartrecruiters", label: "SmartRecruiters" },
  { value: "taleo", label: "Oracle Taleo" },
  { value: "successfactors", label: "SAP SuccessFactors" },
  { value: "bamboohr", label: "BambooHR" },
  { value: "jazzhr", label: "JazzHR" },
  { value: "bullhorn", label: "Bullhorn" },
  { value: "linkedin", label: "LinkedIn Recruiter" },
  { value: "outro", label: "Outro" },
  { value: "nenhum", label: "Nenhum" }
]

const CHALLENGES = [
  { value: "volume", label: "Volume de candidatos" },
  { value: "qualidade", label: "Qualidade dos candidatos" },
  { value: "tempo", label: "Tempo de contratação" },
  { value: "custo", label: "Custo por contratação" },
  { value: "diversidade", label: "Diversidade e inclusão" }
]

const PRIORITIES = [
  { value: "velocidade", label: "Velocidade", icon: Zap },
  { value: "qualidade", label: "Qualidade", icon: Target },
  { value: "custo", label: "Custo", icon: Brain },
  { value: "diversidade", label: "Diversidade", icon: Users }
]

const COMMUNICATION_CHANNELS = [
  { value: "email", label: "Email" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "telefone", label: "Telefone" }
]

const CONTACT_TIMES = [
  { value: "manha", label: "Manhã (8h - 12h)" },
  { value: "tarde", label: "Tarde (12h - 18h)" },
  { value: "qualquer", label: "Qualquer horário" }
]

const COMPANY_SIZES = [
  { value: "startup", label: "Startup" },
  { value: "pequena", label: "Pequena Empresa" },
  { value: "media", label: "Média Empresa" },
  { value: "grande", label: "Grande Empresa" },
  { value: "multinacional", label: "Multinacional" }
]

const PLATFORM_SUGGESTIONS = [
  "Agilizar o processo de triagem de candidatos",
  "Melhorar a qualidade das contratações",
  "Reduzir tempo de preenchimento de vagas",
  "Automatizar comunicação com candidatos",
  "Ter mais dados e insights sobre recrutamento"
]

const STORAGE_KEY = "wedotalent_onboarding_data"

export function OnboardingWizard({ onClose, onComplete, initialData }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [showSuccessScreen, setShowSuccessScreen] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showCultureIncompleteAlert, setShowCultureIncompleteAlert] = useState(false)

  const [companyId, setCompanyId] = useState<string | null>(null)
  const [formData, setFormData] = useState<OnboardingData>({
    companyName: initialData?.companyName || "",
    tradeName: "",
    cnpj: "",
    address: "",
    workModel: "",
    logoUrl: "",
    sector: "",
    employeeCount: "",
    companySize: "",
    foundedYear: "",
    techStack: [],
    website: "",
    linkedinUrl: "",
    companyEmail: "",
    companyPhone: "",
    growthOpportunities: "",
    teamDynamics: "",
    leadershipStyle: "",
    deiInitiatives: "",
    sustainability: "",
    socialImpact: "",
    engineeringCulture: "",
    hiringVolume: 10,
    jobTypes: [],
    currentAts: "",
    mainChallenges: [],
    mainPriority: "",
    platformExpectations: "",
    communicationChannels: ["email", "whatsapp", "telefone"],
    allowLiaContact: true,
    additionalNotes: "",
    responsibleName: "",
    responsibleEmail: "",
    responsiblePhone: "",
    responsiblePosition: "",
    preferredContactTime: "",
    cultureProfile: null,
    recruitmentStages: DEFAULT_STAGES
  })
  const [showCultureAnalyzer, setShowCultureAnalyzer] = useState(false)
  const [tempCompanyId] = useState(() => crypto.randomUUID())

  useEffect(() => {
    async function loadSavedData() {
      try {
        const companyRes = await fetch('/api/backend-proxy/company/profile')
        if (companyRes.ok) {
          const company = await companyRes.json()
          if (company && company.id) {
            const sectorMap: Record<string, string> = {
              'Tecnologia': 'tecnologia',
              'Serviços Financeiros': 'financeiro',
              'Saúde': 'saude',
              'Varejo': 'varejo',
              'Indústria': 'industria',
              'Educação': 'educacao',
              'Serviços': 'servicos',
              'Logística': 'logistica'
            }
            
            setCompanyId(company.id)
            setFormData(prev => ({
              ...prev,
              companyName: company.name || prev.companyName,
              tradeName: company.trading_name || company.trade_name || prev.tradeName,
              cnpj: company.cnpj || prev.cnpj,
              address: company.address || prev.address,
              workModel: company.additional_data?.work_model || prev.workModel,
              logoUrl: company.logo_url || prev.logoUrl,
              sector: sectorMap[company.industry] || company.industry?.toLowerCase() || prev.sector,
              employeeCount: company.size || company.company_size || company.employee_count || prev.employeeCount,
              companySize: company.company_size || company.additional_data?.company_size || prev.companySize,
              foundedYear: company.founded_year || company.additional_data?.founded_year || prev.foundedYear,
              techStack: company.additional_data?.tech_stack || prev.techStack,
              website: company.website || prev.website,
              linkedinUrl: company.linkedin_url || prev.linkedinUrl,
              companyEmail: company.hr_email || company.email || prev.companyEmail,
              companyPhone: company.hr_phone || company.phone || prev.companyPhone,
              responsibleName: company.additional_data?.responsible_name || prev.responsibleName,
              responsibleEmail: company.hr_email || company.email || prev.responsibleEmail,
              responsiblePhone: company.hr_phone || company.phone || prev.responsiblePhone
            }))
            
            const cultureRes = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${company.id}`)
            if (cultureRes.ok) {
              const culture = await cultureRes.json()
              if (culture && !culture.notFound) {
                setFormData(prev => ({
                  ...prev,
                  growthOpportunities: culture.growth_opportunities || prev.growthOpportunities,
                  teamDynamics: culture.team_dynamics || prev.teamDynamics,
                  leadershipStyle: culture.leadership_style || prev.leadershipStyle,
                  deiInitiatives: culture.dei_initiatives || prev.deiInitiatives,
                  sustainability: culture.sustainability || prev.sustainability,
                  socialImpact: culture.social_impact || prev.socialImpact,
                  engineeringCulture: culture.engineering_culture || prev.engineeringCulture,
                  cultureProfile: {
                    id: culture.id,
                    company_id: culture.company_id,
                    mission: culture.mission,
                    vision: culture.vision,
                    values: culture.values || [],
                    evp_bullets: culture.evp_bullets || [],
                    core_competencies: culture.core_competencies || [],
                    culture_description: culture.culture_description,
                    openness_score: culture.openness_score || 50,
                    conscientiousness_score: culture.conscientiousness_score || 50,
                    extraversion_score: culture.extraversion_score || 50,
                    agreeableness_score: culture.agreeableness_score || 50,
                    stability_score: culture.stability_score || 50,
                    website_url: culture.website_url,
                    linkedin_url: culture.linkedin_url,
                    analyzed_pages: culture.analyzed_pages || [],
                    confidence_score: culture.confidence_score,
                    source: culture.source,
                    last_analysis_at: culture.last_analysis_at
                  }
                }))
              }
            }
            
            try {
              const stagesRes = await fetch(`/api/backend-proxy/recruitment-journey/templates?company_id=${company.id}`)
              if (stagesRes.ok) {
                const data = await stagesRes.json()
                if (data.templates && data.templates.length > 0) {
                  const template = data.templates[0]
                  
                  const stagesData = template.stages_config || template.stages
                  if (stagesData && stagesData.length > 0) {
                    setFormData(prev => ({
                      ...prev,
                      recruitmentStages: stagesData
                    }))
                  }
                }
              }
            } catch (stagesError) {
              console.error('Error loading recruitment stages:', stagesError)
            }
          }
        }
      } catch (error) {
        console.error("Error loading from backend:", error)
      }
      
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          setFormData(prev => ({ ...prev, ...parsed }))
        } catch (e) {
          console.error("Error loading saved onboarding data:", e)
        }
      }
    }
    
    loadSavedData()
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(formData))
  }, [formData])

  const updateField = <K extends keyof OnboardingData>(field: K, value: OnboardingData[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const toggleArrayItem = (field: keyof OnboardingData, value: string) => {
    const currentArray = formData[field] as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateField(field, newArray as OnboardingData[typeof field])
  }

  const steps = [
    { id: "company", title: "Dados da Empresa", icon: Building2, time: 3 },
    { id: "recruitment", title: "Jornada de Recrutamento", icon: Briefcase, time: 5 },
    { id: "expectations", title: "Expectativas", icon: MessageSquare, time: 3 },
    { id: "responsible", title: "Responsável", icon: UserCircle, time: 2 },
    { id: "summary", title: "Resumo e Insights", icon: FileCheck, time: 2 }
  ]

  const validateStep = (stepIndex: number): boolean => {
    const newErrors: Record<string, string> = {}

    if (stepIndex === 0) {
      if (!formData.companyName.trim()) newErrors.companyName = "Nome da empresa é obrigatório"
      if (!formData.sector) newErrors.sector = "Setor é obrigatório"
      if (!formData.employeeCount) newErrors.employeeCount = "Número de funcionários é obrigatório"
      if (!formData.workModel) newErrors.workModel = "Modelo de trabalho é obrigatório"
    }

    if (stepIndex === 1) {
      if (formData.jobTypes.length === 0) newErrors.jobTypes = "Selecione pelo menos um tipo de vaga"
      if (!formData.currentAts) newErrors.currentAts = "Selecione seu ATS atual"
      if (!formData.mainPriority) newErrors.mainPriority = "Selecione sua prioridade principal"
    }

    if (stepIndex === 2) {
      if (!formData.platformExpectations.trim()) newErrors.platformExpectations = "Descreva suas expectativas"
      if (formData.communicationChannels.length === 0) newErrors.communicationChannels = "Selecione pelo menos um canal"
    }

    if (stepIndex === 3) {
      if (!formData.responsibleName.trim()) newErrors.responsibleName = "Nome é obrigatório"
      if (!formData.responsibleEmail.trim()) newErrors.responsibleEmail = "Email é obrigatório"
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.responsibleEmail)) newErrors.responsibleEmail = "Email inválido"
      if (!formData.responsiblePhone.trim()) newErrors.responsiblePhone = "Telefone é obrigatório"
      if (!formData.responsiblePosition.trim()) newErrors.responsiblePosition = "Cargo é obrigatório"
      if (!formData.preferredContactTime) newErrors.preferredContactTime = "Selecione um horário preferido"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const isCultureProfileIncomplete = () => {
    if (!formData.cultureProfile) return false
    const profile = formData.cultureProfile
    return (
      !profile.mission ||
      !profile.vision ||
      profile.values.length === 0 ||
      profile.evp_bullets.length === 0
    )
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep === 0 && (formData.website || formData.linkedinUrl) && !formData.cultureProfile) {
        setShowCultureIncompleteAlert(true)
        return
      }
      if (currentStep === 0 && isCultureProfileIncomplete()) {
        setShowCultureIncompleteAlert(true)
        return
      }
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1)
      } else {
        handleSubmit()
      }
    } else {
      const firstErrorField = document.querySelector('[data-error="true"]')
      if (firstErrorField) {
        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }

  const proceedWithoutCulture = () => {
    setShowCultureIncompleteAlert(false)
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleSubmit()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    let returnedCompanyId: string | null = null
    
    try {
      const response = await fetch('/api/backend-proxy/onboarding/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          company_name: formData.companyName,
          trade_name: formData.tradeName,
          cnpj: formData.cnpj,
          address: formData.address,
          work_model: formData.workModel,
          logo_url: formData.logoUrl,
          sector: formData.sector,
          employee_count: formData.employeeCount,
          company_size: formData.companySize,
          founded_year: formData.foundedYear,
          tech_stack: formData.techStack,
          website: formData.website,
          linkedin_url: formData.linkedinUrl,
          company_email: formData.companyEmail,
          company_phone: formData.companyPhone,
          growth_opportunities: formData.growthOpportunities,
          team_dynamics: formData.teamDynamics,
          leadership_style: formData.leadershipStyle,
          dei_initiatives: formData.deiInitiatives,
          sustainability: formData.sustainability,
          social_impact: formData.socialImpact,
          engineering_culture: formData.engineeringCulture,
          hiring_volume: formData.hiringVolume,
          job_types: formData.jobTypes,
          current_ats: formData.currentAts,
          main_challenges: formData.mainChallenges,
          main_priority: formData.mainPriority,
          platform_expectations: formData.platformExpectations,
          communication_channels: formData.communicationChannels,
          allow_lia_contact: formData.allowLiaContact,
          additional_notes: formData.additionalNotes,
          responsible_name: formData.responsibleName,
          responsible_email: formData.responsibleEmail,
          responsible_phone: formData.responsiblePhone,
          responsible_position: formData.responsiblePosition,
          preferred_contact_time: formData.preferredContactTime,
          culture_profile: formData.cultureProfile ? {
            mission: formData.cultureProfile.mission,
            vision: formData.cultureProfile.vision,
            values: formData.cultureProfile.values,
            evp_bullets: formData.cultureProfile.evp_bullets,
            core_competencies: formData.cultureProfile.core_competencies || [],
            openness_score: formData.cultureProfile.openness_score,
            conscientiousness_score: formData.cultureProfile.conscientiousness_score,
            extraversion_score: formData.cultureProfile.extraversion_score,
            agreeableness_score: formData.cultureProfile.agreeableness_score,
            stability_score: formData.cultureProfile.stability_score
          } : null
        })
      })
      
      if (response.ok) {
        try {
          const onboardingData = await response.json()
          returnedCompanyId = onboardingData?.company_id || null
        } catch {
          console.warn('Could not parse onboarding response as JSON')
        }
      } else {
        console.error('Failed to submit onboarding data:', response.status)
      }
    } catch (err) {
      console.error('Error submitting onboarding data:', err)
    }

    const effectiveCompanyId = returnedCompanyId || companyId || tempCompanyId
    
    if (effectiveCompanyId && formData.recruitmentStages && formData.recruitmentStages.length > 0) {
      try {
        const templateResponse = await fetch(`/api/backend-proxy/recruitment-journey/templates?company_id=${effectiveCompanyId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'Pipeline Principal',
            description: 'Jornada de recrutamento da empresa',
            stages_config: formData.recruitmentStages,
            is_default: true
          })
        })

        if (!templateResponse.ok) {
          console.error('Failed to save recruitment journey template:', templateResponse.status)
        }
      } catch (templateErr) {
        console.error('Error saving recruitment journey template:', templateErr)
      }
    }
    
    if (companyId) {
      try {
        const enrichResponse = await fetch(`/api/backend-proxy/company/auto-enrich/${companyId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
        
        if (enrichResponse.ok) {
          const enrichData = await enrichResponse.json()
          console.log('Auto-enrich completed:', enrichData.fields_updated?.length || 0, 'fields updated')
        } else {
          console.warn('Auto-enrich failed, will retry later')
        }
      } catch (enrichErr) {
        console.warn('Error during auto-enrich (non-blocking):', enrichErr)
      }
    }
    
    localStorage.removeItem(STORAGE_KEY)
    setShowSuccessScreen(true)
    onComplete(formData)
  }

  const handleClose = () => {
    setShowSuccessScreen(false)
    onClose()
  }

  if (showSuccessScreen) {
    return (
      <div className="fixed inset-0 bg-gray-900/20 z-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md rounded-2xl border border-gray-100 bg-white overflow-hidden">
          <CardContent className="p-0">
            <div className="p-6 text-center bg-gray-900">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-9 h-9 text-gray-700" />
              </div>
              <h2 className="text-lg font-semibold text-white mb-1">Recebemos suas informações!</h2>
              <p className="text-gray-400 dark:text-gray-500 text-sm" style={{ fontFamily: 'Open Sans, sans-serif' }}>Agora é com a gente. Vamos preparar tudo para você.</p>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <h3 className={`${textStyles.subtitle} dark:text-gray-100 mb-3`}>Próximos passos</h3>
                <div className="space-y-2">
                  {[
                    { status: "done", text: "Dados coletados", subtitle: "Concluído agora" },
                    { status: "pending", text: "Análise pelo nosso time", subtitle: "1-2 dias úteis" },
                    { status: "pending", text: "Configuração personalizada", subtitle: "Baseada nas suas necessidades" },
                    { status: "pending", text: "Treinamento e liberação", subtitle: "Agendaremos com você" }
                  ].map((step, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <div 
                        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                          step.status === "done" 
                            ? "" 
                            : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                        }`}
                        style={step.status === "done" ? { backgroundColor: 'rgba(96, 190, 209, 0.15)' } : {}}
                      >
                        {step.status === "done" ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <Clock className="w-3 h-3" />
                        )}
                      </div>
                      <div>
                        <p className={`text-xs font-medium ${
                          step.status === "done" 
                            ? "text-gray-950 dark:text-gray-50" 
                            : "text-gray-600 dark:text-gray-400"
                        }`} style={{ fontFamily: 'Open Sans, sans-serif' }}>{step.text}</p>
                        <p className={`${textStyles.description} dark:text-gray-400`}>{step.subtitle}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <Card className="rounded-md bg-gray-50/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm">
                <CardContent className="p-3">
                  <div className="flex items-center gap-3">
                    <Avatar className="w-9 h-9 border-2 border-white">
                      <AvatarImage src="" />
                      <AvatarFallback className="text-xs bg-gray-900" style={{ color: 'white', fontWeight: 600 }}>CS</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className={`${textStyles.subtitle} dark:text-gray-100`}>Seu consultor de sucesso</p>
                      <p className={`${textStyles.description} dark:text-gray-400 flex items-center gap-1`}>
                        <Mail className="w-2.5 h-2.5" />
                        cs@wedotalent.com
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
 className="gap-1.5 text-xs py-1 px-2 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 hover:border-gray-300 text-gray-700"
                      onClick={() => window.open("https://wa.me/5511999999999", "_blank")}
                    >
                      <MessageCircle className="w-3 h-3" />
                      WhatsApp
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <div className="rounded-md p-3 text-center border backdrop-blur-sm" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', borderColor: 'rgba(96, 190, 209, 0.2)' }}>
                <p className="text-xs" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  <span className="font-semibold">Prazo estimado:</span> Entraremos em contato em até 2 dias úteis
                </p>
              </div>

              <Button
                onClick={handleClose}
                className="w-full h-9 text-sm font-medium rounded-md text-white transition-all hover:opacity-90 bg-gray-900" style={{ fontFamily: 'Open Sans, sans-serif' }}
              >
                Entendido
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <>
      <AlertDialog open={showCultureIncompleteAlert} onOpenChange={setShowCultureIncompleteAlert}>
        <AlertDialogContent className="rounded-2xl max-w-md">
          <AlertDialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <AlertDialogTitle className="text-base font-semibold">
                Dados de cultura incompletos
              </AlertDialogTitle>
            </div>
            <AlertDialogDescription className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              {!formData.cultureProfile ? (
                <>
                  Você informou o site da empresa, mas ainda não realizou a análise de cultura com IA. 
                  Esta análise ajuda a encontrar candidatos com melhor fit cultural.
                </>
              ) : (
                <>
                  O perfil de cultura da sua empresa está incompleto. Campos como missão, visão, valores 
                  ou diferenciais estão vazios. Completar esses dados melhora a qualidade das recomendações.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex gap-2 sm:gap-2">
            <AlertDialogCancel 
              onClick={proceedWithoutCulture}
              className="flex-1 rounded-md text-sm"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              Completar depois
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setShowCultureIncompleteAlert(false)
                if (!formData.cultureProfile) {
                  setShowCultureAnalyzer(true)
                }
              }}
              className="flex-1 rounded-md text-sm text-white bg-gray-900" style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              {!formData.cultureProfile ? 'Analisar agora' : 'Completar dados'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="fixed inset-0 bg-gray-900/20 z-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-5xl max-h-[90vh] rounded-2xl border border-gray-100 bg-white overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-white">
            <div>
              <h2 className="text-base font-semibold text-gray-950">Bem-vindo(a) ao WeDOTalent</h2>
              <p className="text-sm text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>Configure sua jornada de recrutamento</p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full hover:bg-gray-50 w-8 h-8 text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </Button>
          </div>

        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            {steps.map((step, index) => {
              const StepIcon = step.icon
              const isActive = index === currentStep
              const isCompleted = index < currentStep

              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div 
                      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                        !isCompleted && !isActive ? "bg-gray-100 text-gray-400" : ""
                      }`}
                      style={
                        isCompleted
                          ? { backgroundColor: 'rgba(96, 190, 209, 0.15)' }
                          : isActive
                            ? { backgroundColor: '#111827', color: 'white', boxShadow: '0 0 0 3px rgba(96, 190, 209, 0.2)' }
                            : {}
                      }
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                        <StepIcon className="w-4 h-4" />
                      )}
                    </div>
                    <span 
                      className={`text-xs mt-1.5 font-medium text-center leading-tight ${!isActive ? "text-gray-500" : ""}`}
                      style={isActive ? { fontFamily: 'Open Sans, sans-serif' } : { fontFamily: 'Open Sans, sans-serif' }}
                    >
                      {step.title}
                    </span>
                    <span className="text-[10px] text-gray-400" style={{ fontFamily: 'Open Sans, sans-serif' }}>~{step.time} min</span>
                  </div>
                  {index < steps.length - 1 && (
                    <div 
                      className={`w-full h-0.5 mx-2 rounded transition-colors duration-300 ${!isCompleted ? "bg-gray-200" : ""}`}
                      style={isCompleted ? { backgroundColor: '#111827' } : {}}
                    />
                  )}
                </div>
              )
            })}
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1">
            <div
              className="h-1 rounded-full transition-all duration-500 bg-gray-900" style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {currentStep === 0 && (
            <div className="space-y-4">
              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Nome da Empresa *</Label>
                <input
                  type="text"
                  value={formData.companyName}
                  onChange={(e) => updateField("companyName", e.target.value)}
                  className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                    errors.companyName ? "border-red-300 bg-red-50/50" : "border-gray-200 dark:border-gray-700"
                  }`}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                  onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                  onBlur={(e) => { e.target.style.borderColor = errors.companyName ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  placeholder="Ex: Empresa ABC"
                />
                {errors.companyName && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.companyName}</p>}
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Nome Fantasia <span className="text-gray-400 font-normal">(opcional)</span></Label>
                <input
                  type="text"
                  value={formData.tradeName}
                  onChange={(e) => updateField("tradeName", e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-2xl border transition-all bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                  onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  placeholder="Nome comercial da empresa"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>CNPJ <span className="text-gray-400 font-normal">(opcional)</span></Label>
                  <input
                    type="text"
                    value={formData.cnpj}
                    onChange={(e) => updateField("cnpj", e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-2xl border transition-all bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="00.000.000/0000-00"
                  />
                </div>

                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Endereço <span className="text-gray-400 font-normal">(opcional)</span></Label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => updateField("address", e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-2xl border transition-all bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="Av. Paulista, 1000 - São Paulo, SP"
                  />
                </div>
              </div>

              <div data-error={errors.workModel ? "true" : undefined}>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-2 block`}>Modelo de Trabalho *</Label>
                <RadioGroup
                  value={formData.workModel}
                  onValueChange={(value) => updateField("workModel", value)}
                  className="flex flex-wrap gap-2"
                >
                  {[
                    { value: "remoto", label: "Remoto" },
                    { value: "hibrido", label: "Híbrido" },
                    { value: "presencial", label: "Presencial" }
                  ].map(option => {
                    const isSelected = formData.workModel === option.value
                    return (
                      <Label
                        key={option.value}
                        htmlFor={`workModel-${option.value}`}
                        className={`flex items-center gap-2 px-4 py-2 rounded-2xl border cursor-pointer transition-all ${
                          !isSelected ? "bg-white border-gray-200 hover:border-gray-300 dark:bg-gray-900 dark:border-gray-700" : ""
                        } ${errors.workModel ? "border-red-300" : ""}`}
                        style={isSelected ? {
                          backgroundColor: 'rgba(229, 231, 235, 0.3)'
                        } : {}}
                      >
                        <RadioGroupItem 
                          value={option.value} 
                          id={`workModel-${option.value}`} 
                          className="w-3.5 h-3.5" 
                          style={{ borderColor: isSelected ? '#111827' : undefined, color: isSelected ? '#111827' : undefined }} 
                        />
                        <span 
                          className={`text-sm font-medium ${!isSelected ? "text-gray-600 dark:text-gray-400" : ""}`}
                          style={isSelected ? { fontFamily: 'Open Sans, sans-serif' } : { fontFamily: 'Open Sans, sans-serif' }}
                        >
                          {option.label}
                        </span>
                      </Label>
                    )
                  })}
                </RadioGroup>
                {errors.workModel && <p className={`${textStyles.caption} text-red-500 mt-1`}>{errors.workModel}</p>}
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Logo da Empresa</Label>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-md border-2 border-dashed border-gray-200 dark:border-gray-700 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                    {formData.logoUrl ? (
                      <img src={formData.logoUrl} alt="Logo" className="w-full h-full object-contain rounded-md" />
                    ) : (
                      <Upload className="w-4 h-4 text-gray-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <input
                      type="url"
                      value={formData.logoUrl}
                      onChange={(e) => updateField("logoUrl", e.target.value)}
                      className="w-full px-3 py-1.5 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="URL do logo (ex: https://...)"
                    />
                    <p className={`${textStyles.description} mt-0.5`}>Cole a URL do logo ou deixe em branco</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Setor de Atuação *</Label>
                  <IndustrySingleSelect
                    value={formData.sector}
                    onChange={(value) => updateField("sector", value)}
                    placeholder="Digite para buscar setor..."
                    error={!!errors.sector}
                  />
                  {errors.sector && <p className="text-[10px] text-red-500 mt-0.5">{errors.sector}</p>}
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Número de Funcionários *</Label>
                  <select
                    value={formData.employeeCount}
                    onChange={(e) => updateField("employeeCount", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white ${
                      errors.employeeCount ? "border-red-300" : "border-gray-200"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.employeeCount ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  >
                    <option value="">Selecione...</option>
                    {EMPLOYEE_RANGES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                  {errors.employeeCount && <p className="text-[10px] text-red-500 mt-0.5">{errors.employeeCount}</p>}
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Porte da Empresa</Label>
                  <select
                    value={formData.companySize}
                    onChange={(e) => updateField("companySize", e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-md border transition-all bg-white border-gray-200"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  >
                    <option value="">Selecione...</option>
                    {COMPANY_SIZES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Ano de Fundação</Label>
                  <input
                    type="text"
                    value={formData.foundedYear}
                    onChange={(e) => updateField("foundedYear", e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-md border transition-all bg-white border-gray-200"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="Ex: 2020"
                  />
                </div>
                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Tech Stack (opcional)</Label>
                  <div className="relative">
                    <input
                      type="text"
                      className="w-full px-3 py-2 text-sm rounded-md border transition-all bg-white border-gray-200"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="Digite e pressione Enter"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          const input = e.target as HTMLInputElement
                          const value = input.value.trim()
                          if (value && !formData.techStack.includes(value)) {
                            updateField("techStack", [...formData.techStack, value])
                            input.value = ''
                          }
                        }
                      }}
                    />
                  </div>
                  {formData.techStack.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {formData.techStack.map((tech, idx) => (
                        <span 
                          key={idx} 
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full"
                          style={{ 
                            backgroundColor: 'rgba(96, 190, 209, 0.15)', 
                            color: '#0e7490',
                            fontFamily: 'Open Sans, sans-serif'
                          }}
                        >
                          {tech}
                          <button
                            type="button"
                            onClick={() => updateField("techStack", formData.techStack.filter((_, i) => i !== idx))}
                            className="ml-0.5 hover:text-red-500 transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-gradient-to-r from-gray-100 dark:from-gray-800 to-gray-50 dark:to-gray-900 rounded-md border border-gray-300 dark:border-gray-600">
                  <p className="text-xs text-gray-900 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    <strong>Dica:</strong> Preencha o Site e o LinkedIn para que a LIA analise sua empresa de forma mais completa, 
                    extraindo informações de ambas as fontes para montar o perfil cultural.
                  </p>
                </div>
                
                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block flex items-center gap-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    <Globe className="w-3 h-3 text-gray-700" />
                    Site (opcional)
                  </Label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => {
                      updateField("website", e.target.value)
                      if (!e.target.value && !formData.linkedinUrl) {
                        setShowCultureAnalyzer(false)
                      }
                    }}
                    className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="https://www.empresa.com.br"
                  />
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block flex items-center gap-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    <Linkedin className="w-3 h-3" style={{ color: '#0A66C2' }} />
                    LinkedIn da Empresa (opcional)
                  </Label>
                  <input
                    type="url"
                    value={formData.linkedinUrl}
                    onChange={(e) => {
                      updateField("linkedinUrl", e.target.value)
                      if (!e.target.value && !formData.website) {
                        setShowCultureAnalyzer(false)
                      }
                    }}
                    className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#0A66C2'; e.target.style.boxShadow = '0 0 0 2px rgba(10, 102, 194, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="https://www.linkedin.com/company/sua-empresa"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block flex items-center gap-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      <Mail className="w-3 h-3 text-gray-700" />
                      Email da Empresa (opcional)
                    </Label>
                    <input
                      type="email"
                      value={formData.companyEmail}
                      onChange={(e) => updateField("companyEmail", e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="contato@empresa.com.br"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block flex items-center gap-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      <Phone className="w-3 h-3 text-gray-700" />
                      Telefone da Empresa (opcional)
                    </Label>
                    <input
                      type="tel"
                      value={formData.companyPhone}
                      onChange={(e) => updateField("companyPhone", e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="+55 11 99999-9999"
                    />
                  </div>
                </div>

                {(formData.website || formData.linkedinUrl) && !showCultureAnalyzer && !formData.cultureProfile && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowCultureAnalyzer(true)}
                    className="mt-2 gap-2 py-2 px-4 text-sm font-medium rounded-md border-2 hover:bg-gray-100 dark:bg-gray-800 transition-all"
                    style={{ 
                      fontFamily: 'Open Sans, sans-serif' 
                    }}
                  >
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Analisar Empresa com IA
                  </Button>
                )}
              </div>

              {(showCultureAnalyzer || formData.cultureProfile) && (
                <div className="pt-2">
                  <CultureAnalyzer
                    websiteUrl={formData.website}
                    linkedinUrl={formData.linkedinUrl}
                    companyId={tempCompanyId}
                    existingProfile={formData.cultureProfile}
                    onAnalysisComplete={(profile) => {
                      updateField("cultureProfile", profile)
                    }}
                    onManualEdit={() => {
                      const emptyProfile = {
                        id: crypto.randomUUID(),
                        company_id: tempCompanyId,
                        mission: '',
                        vision: '',
                        values: [],
                        evp_bullets: [],
                        culture_description: '',
                        core_competencies: [],
                        openness_score: 50,
                        conscientiousness_score: 50,
                        extraversion_score: 50,
                        agreeableness_score: 50,
                        stability_score: 50,
                        website_url: formData.website,
                        linkedin_url: formData.linkedinUrl,
                        analyzed_pages: [],
                        confidence_score: 0,
                        source: 'manual',
                        last_analysis_at: new Date().toISOString()
                      }
                      updateField("cultureProfile", emptyProfile)
                    }}
                  />
                </div>
              )}

              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}
                  >
                    <TrendingUp className="w-4 h-4 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-950">
                      Proposta de Valor (EVP)
                    </h3>
                    <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Descreva o que sua empresa oferece aos colaboradores
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Oportunidades de Crescimento (opcional)
                    </Label>
                    <textarea
                      value={formData.growthOpportunities}
                      onChange={(e) => updateField("growthOpportunities", e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white resize-none"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="Ex: Plano de carreira estruturado, treinamentos, mentoria..."
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                        Dinâmica do Time (opcional)
                      </Label>
                      <input
                        type="text"
                        value={formData.teamDynamics}
                        onChange={(e) => updateField("teamDynamics", e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                        onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                        onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                        placeholder="Ex: Colaborativo, ágil, autogerenciado"
                      />
                    </div>
                    <div>
                      <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                        Estilo de Liderança (opcional)
                      </Label>
                      <input
                        type="text"
                        value={formData.leadershipStyle}
                        onChange={(e) => updateField("leadershipStyle", e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                        onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                        onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                        placeholder="Ex: Inspirador, hands-on, coach"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}
                  >
                    <ShieldCheck className="w-4 h-4 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-950">
                      Responsabilidade Social
                    </h3>
                    <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Iniciativas de impacto social e ambiental
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Iniciativas de D&I (opcional)
                    </Label>
                    <textarea
                      value={formData.deiInitiatives}
                      onChange={(e) => updateField("deiInitiatives", e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white resize-none"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                      placeholder="Descreva suas iniciativas de Diversidade, Equidade e Inclusão..."
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                        Sustentabilidade (opcional)
                      </Label>
                      <textarea
                        value={formData.sustainability}
                        onChange={(e) => updateField("sustainability", e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white resize-none"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                        onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                        onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                        placeholder="Práticas sustentáveis..."
                      />
                    </div>
                    <div>
                      <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                        Impacto Social (opcional)
                      </Label>
                      <textarea
                        value={formData.socialImpact}
                        onChange={(e) => updateField("socialImpact", e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white resize-none"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                        onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                        onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                        placeholder="Projetos de impacto social..."
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}
                  >
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-950">
                      Tecnologia
                    </h3>
                    <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Cultura e práticas de engenharia
                    </p>
                  </div>
                </div>
                
                <div>
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    Cultura de Engenharia (opcional)
                  </Label>
                  <textarea
                    value={formData.engineeringCulture}
                    onChange={(e) => updateField("engineeringCulture", e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 bg-white resize-none"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="Ex: Code reviews, pair programming, TDD, DevOps, hackathons..."
                  />
                </div>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1 block`}>
                  Volume médio de contratações por mês
                </Label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  Arraste o controle para indicar quantas contratações sua empresa realiza mensalmente
                </p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-gray-800 dark:text-gray-200 min-w-[24px] text-center" style={{ fontFamily: 'Open Sans, sans-serif' }}>1</span>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={formData.hiringVolume}
                      onChange={(e) => updateField("hiringVolume", parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-md appearance-none cursor-pointer"
                      className="accent-gray-700"
                    />
                    <span className="text-sm font-bold text-gray-800 dark:text-gray-200 min-w-[32px] text-center" style={{ fontFamily: 'Open Sans, sans-serif' }}>100</span>
                  </div>
                  <div className="flex justify-center">
                    <div className="px-4 py-2 rounded-md border border-gray-900 dark:border-gray-50 bg-gray-900">
                      <span className="text-sm font-bold text-white" style={{ fontFamily: 'Open Sans, sans-serif' }}>{formData.hiringVolume} contratações/mês</span>
                    </div>
                  </div>
                </div>
              </div>

              <div data-error={errors.jobTypes ? "true" : undefined}>
                <Label className={`text-xs font-medium mb-2 block ${errors.jobTypes ? 'text-red-500' : 'text-gray-800 dark:text-gray-200'}`} style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  Tipos de vaga mais comuns *
                </Label>
                <div className={`grid grid-cols-2 gap-1.5 p-2 rounded-md ${errors.jobTypes ? 'bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800' : ''}`}>
                  {JOB_TYPES.map(type => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => toggleArrayItem("jobTypes", type.value)}
                      className={`px-3 py-2 rounded-md border text-xs font-medium transition-all ${
                        !formData.jobTypes.includes(type.value)
                          ? "bg-white border-gray-200 text-gray-600 hover:border-gray-300 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400"
                          : ""
                      }`}
                      style={formData.jobTypes.includes(type.value) ? {
                        backgroundColor: 'rgba(229, 231, 235, 0.3)',
                        fontFamily: 'Open Sans, sans-serif'
                      } : { fontFamily: 'Open Sans, sans-serif' }}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
                {errors.jobTypes && <p className={`${textStyles.caption} text-red-500 mt-1 font-medium`}>{errors.jobTypes}</p>}
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>ATS atual em uso *</Label>
                <select
                  value={formData.currentAts}
                  onChange={(e) => updateField("currentAts", e.target.value)}
                  className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                    errors.currentAts ? "border-red-300" : "border-gray-200 dark:border-gray-700"
                  }`}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                  onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                  onBlur={(e) => { e.target.style.borderColor = errors.currentAts ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                >
                  <option value="">Selecione...</option>
                  {ATS_OPTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                </select>
                {errors.currentAts && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.currentAts}</p>}
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-2 block`}>Principais desafios</Label>
                <div className="flex flex-wrap gap-1.5">
                  {CHALLENGES.map(c => (
                    <button
                      key={c.value}
                      type="button"
                      onClick={() => toggleArrayItem("mainChallenges", c.value)}
                      className={`px-2.5 py-1.5 rounded-md border text-xs transition-all ${
                        !formData.mainChallenges.includes(c.value)
                          ? "bg-white border-gray-200 text-gray-600 hover:border-gray-300 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400"
                          : ""
                      }`}
                      style={formData.mainChallenges.includes(c.value) ? {
                        backgroundColor: 'rgba(229, 231, 235, 0.3)',
                        fontFamily: 'Open Sans, sans-serif'
                      } : { fontFamily: 'Open Sans, sans-serif' }}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-2 block`}>Prioridade principal *</Label>
                <RadioGroup
                  value={formData.mainPriority}
                  onValueChange={(value) => updateField("mainPriority", value)}
                  className="grid grid-cols-2 gap-2"
                >
                  {PRIORITIES.map(p => {
                    const PriorityIcon = p.icon
                    const isSelected = formData.mainPriority === p.value
                    return (
                      <Label
                        key={p.value}
                        htmlFor={p.value}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md border cursor-pointer transition-all ${
                          !isSelected ? "bg-white border-gray-200 hover:border-gray-300 dark:bg-gray-900 dark:border-gray-700" : ""
                        }`}
                        style={isSelected ? {
                          backgroundColor: 'rgba(229, 231, 235, 0.3)'
                        } : {}}
                      >
                        <RadioGroupItem value={p.value} id={p.value} className="w-3.5 h-3.5" style={{ borderColor: isSelected ? '#111827' : undefined, color: isSelected ? '#111827' : undefined }} />
                        <PriorityIcon className="w-3.5 h-3.5" style={{ color: isSelected ? '#111827' : '#9ca3af' }} />
                        <span 
                          className={`text-xs font-medium ${!isSelected ? "text-gray-600 dark:text-gray-400" : ""}`}
                          style={isSelected ? { fontFamily: 'Open Sans, sans-serif' } : { fontFamily: 'Open Sans, sans-serif' }}
                        >
                          {p.label}
                        </span>
                      </Label>
                    )
                  })}
                </RadioGroup>
                {errors.mainPriority && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.mainPriority}</p>}
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}
                  >
                    <Settings2 className="w-4 h-4 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                      Etapas do Processo Seletivo
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      Configure as etapas e automações do seu processo de recrutamento
                    </p>
                  </div>
                </div>
                <RecruitmentJourneyConfig
                  stages={formData.recruitmentStages}
                  onChange={(stages) => updateField("recruitmentStages", stages)}
                />
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>O que você espera da plataforma? *</Label>
                <div className="mb-1.5 flex flex-wrap gap-1">
                  {PLATFORM_SUGGESTIONS.map((suggestion, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        const current = formData.platformExpectations
                        const newValue = current ? `${current}\n• ${suggestion}` : `• ${suggestion}`
                        updateField("platformExpectations", newValue)
                      }}
                      className={`px-2 py-0.5 rounded-md bg-gray-100 hover:bg-gray-200 ${textStyles.description} transition-colors dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-400`}
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                    >
                      + {suggestion}
                    </button>
                  ))}
                </div>
                <textarea
                  value={formData.platformExpectations}
                  onChange={(e) => updateField("platformExpectations", e.target.value)}
                  rows={3}
                  className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 resize-none ${
                    errors.platformExpectations ? "border-red-300" : "border-gray-200 dark:border-gray-700"
                  }`}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                  onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                  onBlur={(e) => { e.target.style.borderColor = errors.platformExpectations ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  placeholder="Descreva o que você espera alcançar com a plataforma..."
                />
                {errors.platformExpectations && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.platformExpectations}</p>}
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-2 block`}>
                  Como prefere se comunicar com candidatos? *
                </Label>
                <div className="grid grid-cols-2 gap-1.5">
                  {COMMUNICATION_CHANNELS.map(ch => {
                    const isSelected = formData.communicationChannels.includes(ch.value)
                    return (
                      <button
                        key={ch.value}
                        type="button"
                        onClick={() => toggleArrayItem("communicationChannels", ch.value)}
                        className={`px-3 py-2 rounded-md border text-xs font-medium transition-all flex items-center gap-1.5 ${
                          !isSelected
                            ? "bg-white border-gray-200 text-gray-600 hover:border-gray-300 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400"
                            : ""
                        }`}
                        style={isSelected ? {
                          backgroundColor: 'rgba(229, 231, 235, 0.3)',
                          fontFamily: 'Open Sans, sans-serif'
                        } : { fontFamily: 'Open Sans, sans-serif' }}
                      >
                        {ch.value === "email" && <Mail className="w-3.5 h-3.5" />}
                        {ch.value === "whatsapp" && <MessageCircle className="w-3.5 h-3.5" />}
                        {ch.value === "teams" && <Users className="w-3.5 h-3.5" />}
                        {ch.value === "telefone" && <Phone className="w-3.5 h-3.5" />}
                        {ch.label}
                      </button>
                    )
                  })}
                </div>
                {errors.communicationChannels && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.communicationChannels}</p>}
              </div>

              <div 
                className="flex items-center justify-between p-3 rounded-md backdrop-blur-sm"
                style={{ 
                  backgroundColor: 'rgba(96, 190, 209, 0.08)'
                }}
              >
                <div className="flex items-center gap-2">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-900"
                  >
                    <Brain className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-950 dark:text-gray-50">Assistente Virtual LIA</p>
                    <p className={`${textStyles.description} dark:text-gray-400`}>Permitir que a LIA entre em contato com candidatos</p>
                  </div>
                </div>
                <Switch
                  checked={formData.allowLiaContact}
                  onCheckedChange={(checked: boolean) => updateField("allowLiaContact", checked)}
                  className="scale-90"
                />
              </div>

              <div>
                <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Notas adicionais (opcional)</Label>
                <textarea
                  value={formData.additionalNotes}
                  onChange={(e) => updateField("additionalNotes", e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 resize-none"
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                  onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                  onBlur={(e) => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  placeholder="Algo mais que devemos saber sobre sua operação de recrutamento?"
                />
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-4">
              <div 
                className="rounded-md p-3 mb-4 backdrop-blur-sm"
                style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', border: '1px solid rgba(96, 190, 209, 0.2)' }}
              >
                <p className="text-xs" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  Estas informações serão usadas pelo nosso time de Customer Success para entrar em contato com você.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Nome Completo *</Label>
                  <input
                    type="text"
                    value={formData.responsibleName}
                    onChange={(e) => updateField("responsibleName", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                      errors.responsibleName ? "border-red-300 bg-red-50/50" : "border-gray-200 dark:border-gray-700"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.responsibleName ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="Seu nome completo"
                  />
                  {errors.responsibleName && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.responsibleName}</p>}
                </div>

                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block flex items-center gap-1`}>
                    <Mail className="w-3 h-3 text-gray-700" />
                    Email *
                  </Label>
                  <input
                    type="email"
                    value={formData.responsibleEmail}
                    onChange={(e) => updateField("responsibleEmail", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                      errors.responsibleEmail ? "border-red-300 bg-red-50/50" : "border-gray-200 dark:border-gray-700"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.responsibleEmail ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="seu@email.com"
                  />
                  {errors.responsibleEmail && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.responsibleEmail}</p>}
                </div>

                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block flex items-center gap-1`}>
                    <Phone className="w-3 h-3 text-gray-700" />
                    Telefone *
                  </Label>
                  <input
                    type="tel"
                    value={formData.responsiblePhone}
                    onChange={(e) => updateField("responsiblePhone", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                      errors.responsiblePhone ? "border-red-300 bg-red-50/50" : "border-gray-200 dark:border-gray-700"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.responsiblePhone ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="(11) 99999-9999"
                  />
                  {errors.responsiblePhone && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.responsiblePhone}</p>}
                </div>

                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Cargo *</Label>
                  <input
                    type="text"
                    value={formData.responsiblePosition}
                    onChange={(e) => updateField("responsiblePosition", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                      errors.responsiblePosition ? "border-red-300 bg-red-50/50" : "border-gray-200 dark:border-gray-700"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.responsiblePosition ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                    placeholder="Ex: Gerente de RH"
                  />
                  {errors.responsiblePosition && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.responsiblePosition}</p>}
                </div>

                <div>
                  <Label className={`${textStyles.label} dark:text-gray-300 mb-1.5 block`}>Horário preferido *</Label>
                  <select
                    value={formData.preferredContactTime}
                    onChange={(e) => updateField("preferredContactTime", e.target.value)}
                    className={`w-full px-3 py-2 text-sm rounded-md border transition-all bg-white dark:bg-gray-900 ${
                      errors.preferredContactTime ? "border-red-300" : "border-gray-200 dark:border-gray-700"
                    }`}
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                    onFocus={(e) => { e.target.style.borderColor = '#D1D5DB'; e.target.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.15)'; }}
                    onBlur={(e) => { e.target.style.borderColor = errors.preferredContactTime ? '#fca5a5' : '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                  >
                    <option value="">Selecione...</option>
                    {CONTACT_TIMES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  {errors.preferredContactTime && <p className={`${textStyles.caption} text-red-500 mt-0.5`}>{errors.preferredContactTime}</p>}
                </div>
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-4">
              <div className="rounded-md p-3 border backdrop-blur-sm" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', borderColor: 'rgba(96, 190, 209, 0.2)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                    Resumo da Configuração
                  </h4>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  Revise os dados coletados e entenda como a LIA vai utilizá-los para personalizar sua experiência de recrutamento.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Card className="rounded-md border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Building2 className="w-3.5 h-3.5 text-gray-700" />
                      <span className="text-[11px] font-semibold text-gray-800 dark:text-gray-200">Empresa</span>
                    </div>
                    <p className="text-xs font-medium text-gray-950 dark:text-gray-50">{formData.companyName || "—"}</p>
                    <p className="text-[10px] text-gray-500">{formData.sector || "—"} • {formData.employeeCount || "—"}</p>
                  </CardContent>
                </Card>

                <Card className="rounded-md border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Briefcase className="w-3.5 h-3.5 text-gray-600" />
                      <span className="text-[11px] font-semibold text-gray-800 dark:text-gray-200">Recrutamento</span>
                    </div>
                    <p className="text-xs font-medium text-gray-950 dark:text-gray-50">~{formData.hiringVolume} vagas/ano</p>
                    <p className="text-[10px] text-gray-500">{formData.jobTypes.map(t => JOB_TYPES.find(j => j.value === t)?.label).join(", ") || "—"}</p>
                  </CardContent>
                </Card>

                {formData.cultureProfile && (
                  <Card className="col-span-2 rounded-md border border-teal-100 dark:border-teal-800 bg-teal-50/30 dark:bg-teal-900/20">
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        <span className="text-[11px] font-semibold text-teal-700 dark:text-teal-300">Perfil Cultural Identificado</span>
                      </div>
                      <div className="grid grid-cols-5 gap-2 text-center">
                        {[
                          { label: "Abertura", score: formData.cultureProfile.openness_score },
                          { label: "Conscienc.", score: formData.cultureProfile.conscientiousness_score },
                          { label: "Extroversão", score: formData.cultureProfile.extraversion_score },
                          { label: "Amabilidade", score: formData.cultureProfile.agreeableness_score },
                          { label: "Estabilidade", score: formData.cultureProfile.stability_score }
                        ].map(trait => (
                          <div key={trait.label}>
                            <div className="text-sm font-bold text-gray-700">{trait.score}</div>
                            <div className="text-[9px] text-gray-500">{trait.label}</div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              <Card className="rounded-md border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-3">
 <Settings2 className="w-4 h-4 text-gray-600" />
 <h4 className="text-xs font-semibold text-wedo-cyan-dark dark:text-gray-400">
                      Como a LIA vai usar seus dados
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {[
                      { icon: TrendingUp, title: "Calibração de Busca", desc: "Ajuste automático dos critérios de match com base no perfil cultural e tipos de vaga" },
                      { icon: Brain, title: "Parecer Personalizado", desc: "Análise de candidatos considerando valores, cultura e competências da sua empresa" },
                      { icon: BarChart3, title: "Scoring Adaptativo", desc: "Ponderação de scores técnicos e comportamentais conforme sua prioridade" },
                      { icon: Target, title: "Triagem Inteligente", desc: "Perguntas de screening personalizadas para o perfil da empresa" }
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <item.icon className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">{item.title}: </span>
                          <span className="text-[11px] text-gray-600 dark:text-gray-400">{item.desc}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-md border border-amber-100 dark:border-amber-800 bg-amber-50/30 dark:bg-amber-900/20">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    <h4 className="text-xs font-semibold text-amber-800 dark:text-amber-200">
                      Recomendações da LIA
                    </h4>
                  </div>
                  <div className="space-y-2 text-[11px] text-gray-800 dark:text-gray-200">
                    {formData.mainPriority === "velocidade" && (
                      <p>• <strong>Foco em velocidade:</strong> Habilitaremos triagem automática e fast-track para candidatos com alto match.</p>
                    )}
                    {formData.mainPriority === "qualidade" && (
                      <p>• <strong>Foco em qualidade:</strong> Aumentaremos critérios de match e incluiremos mais etapas de validação comportamental.</p>
                    )}
                    {formData.mainPriority === "diversidade" && (
                      <p>• <strong>Foco em diversidade:</strong> Aplicaremos filtros de viés inconsciente e ampliaremos fontes de sourcing.</p>
                    )}
                    {formData.hiringVolume > 50 && (
                      <p>• <strong>Alto volume:</strong> Recomendamos automação de comunicação e bulk actions para otimizar seu tempo.</p>
                    )}
                    {!formData.cultureProfile && (
                      <p>• <strong>Perfil cultural:</strong> Considere completar a análise de cultura para melhorar a precisão do match cultural.</p>
                    )}
                    {formData.cultureProfile && (
                      <p>• <strong>Match cultural ativo:</strong> Candidatos serão avaliados também por compatibilidade com seu perfil Big Five.</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <div className="rounded-md p-3 border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
                <div className="flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-[11px] font-medium text-gray-800 dark:text-gray-200 mb-1">Sobre a calibração contínua</h5>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-relaxed">
                      A LIA aprende com suas interações. Conforme você avalia candidatos, aceita ou rejeita recomendações, 
                      o sistema refina automaticamente os critérios de busca e scoring para se alinhar cada vez mais às suas preferências reais.
                      Seus dados são tratados com segurança conforme LGPD.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {Object.keys(errors).length > 0 && (
          <div className="mx-6 mb-2 p-3 rounded-md bg-red-50 border border-red-100">
            <p className="text-xs text-red-600 font-medium" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              Por favor, preencha os campos obrigatórios destacados acima.
            </p>
          </div>
        )}

        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50">
          <Button
            variant="ghost"
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="gap-2 rounded-md text-sm py-2 px-4 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            style={{ fontFamily: 'Open Sans, sans-serif' }}
          >
            <ChevronLeft className="w-4 h-4" />
            Anterior
          </Button>

          <span className="text-sm text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Etapa {currentStep + 1} de {steps.length}
          </span>

          <Button
            onClick={handleNext}
            className="gap-2 rounded-md text-sm py-2 px-5 text-white transition-all hover:opacity-90 bg-gray-900" style={{ fontFamily: 'Open Sans, sans-serif' }}
          >
            {currentStep === steps.length - 1 ? "Finalizar" : "Próximo"}
            {currentStep === steps.length - 1 ? (
              <CheckCircle2 className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </Button>
        </div>
      </Card>
      </div>
    </>
  )
}
