"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  X,
  Briefcase,
  Users,
  Calendar,
  FileText,
  DollarSign,
  Layers,
  Settings,
  Plus,
  Trash2,
  GripVertical,
  Building,
  Save,
  Shield,
  Globe,
  Lock,
  AlertTriangle,
  Heart,
  Linkedin,
  ExternalLink,
  CheckCircle,
  Target,
  Languages,
  UserPlus,
  Code,
  Brain,
  HelpCircle,
  Download,
  Check,
  Loader2,
  ClipboardList,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"
import { liaApi, type JobVacancy } from "@/services/lia-api"
import type { CompanyBenefit } from '@/types/benefits'
import { toCompanyBenefit } from '@/types/benefits'

interface InterviewStage {
  stageName: string
  order: number
  sla: number
  type: 'automated' | 'manual' | 'hybrid'
}

interface PipelineTemplate {
  id: string
  company_id: string
  name: string
  description: string | null
  stages: { name: string; order: number; type: string; sla_days: number; instructions?: string }[]
  is_default: boolean
  is_active: boolean
  usage_count: number
}

interface Job {
  id: number
  jobId: string
  backendId: string
  title: string
  department: string
  location: string
  workModel: "presencial" | "híbrido" | "remoto"
  type: string
  level: string
  salary: string
  benefits: string[]
  status: string
  stage: string
  openDate: string
  deadline?: string
  deadlineScreening?: string
  deadlineShortlist?: string
  deadlineClosing?: string
  description: string
  requirements: string[]
  manager: string
  managerEmail: string
  recruiter: string
  recruiterEmail: string
  funnel: { total: number; screening: number; interview: number; final: number; hired: number }
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  publishedIndeed?: boolean
  isConfidential: boolean
  isAffirmative?: boolean
  affirmativeType?: 'pcd' | 'racial' | 'gender' | 'age' | 'lgbtqia+'
  nps: number
  budget?: number
  budgetUsed?: number
  nextActions: string[]
  urgencyLevel: 1 | 2 | 3 | 4 | 5
  hiringProcess?: string[]
  targetAudience?: string
  interviewStages?: InterviewStage[]
  visibility?: "public" | "internal" | "confidential" | "hidden"
  accessList?: string[]
  maskedCompanyName?: string
  salaryRange?: { min: number; max: number; currency: string }
  salaryMin?: number
  salaryMax?: number
  bonusMin?: number
  bonusMax?: number
  targetSector?: string
  targetSegment?: string
  languages?: { language: string; level: string; required?: boolean }[]
  technicalRequirements?: { category: string; technology: string; level: string; required: boolean }[]
  behavioralCompetencies?: { competency: string; weight: string }[]
  screeningQuestions?: { id?: string; text: string; category: string; type?: string; weight?: number; is_eliminatory?: boolean; expected_answer?: string }[]
  eligibilityQuestions?: { id?: string; question: string; type?: string; category?: string; enabled?: boolean }[]
  confidentialityConfig?: {
    can_reveal_company_name?: boolean
    can_discuss_salary?: boolean
    can_discuss_benefits?: boolean
    can_discuss_location?: boolean
  }
  createdBy?: string
  createdByEmail?: string
  createdAt?: string
  publicSlug?: string
}

interface EditJobModalProps {
  isOpen: boolean
  onClose: () => void
  job: Job | null
  onSave: (jobId: string, updates: Partial<JobVacancy>) => Promise<void>
}

const WORK_MODELS = [
  { value: 'presencial', label: 'Presencial' },
  { value: 'híbrido', label: 'Híbrido' },
  { value: 'remoto', label: 'Remoto' },
]

const CONTRACT_TYPES = [
  { value: 'CLT', label: 'CLT' },
  { value: 'PJ', label: 'PJ' },
  { value: 'Estágio', label: 'Estágio' },
  { value: 'Freelancer', label: 'Freelancer' },
  { value: 'Temporário', label: 'Temporário' },
]

const SENIORITY_LEVELS = [
  { value: 'Estágio', label: 'Estágio' },
  { value: 'Júnior', label: 'Júnior' },
  { value: 'Pleno', label: 'Pleno' },
  { value: 'Sênior', label: 'Sênior' },
  { value: 'Especialista', label: 'Especialista' },
  { value: 'Coordenador', label: 'Coordenador' },
  { value: 'Gerente', label: 'Gerente' },
  { value: 'Diretor', label: 'Diretor' },
]

const STATUS_OPTIONS = [
  { value: 'Ativa', label: 'Ativa' },
  { value: 'Rascunho', label: 'Rascunho' },
  { value: 'Paralisada', label: 'Paralisada' },
  { value: 'Aguardando aprovação', label: 'Aguardando aprovação' },
  { value: 'Aprovada', label: 'Aprovada' },
  { value: 'Reaberta', label: 'Reaberta' },
  { value: 'Interna', label: 'Interna' },
  { value: 'Fechada (preenchida)', label: 'Fechada (preenchida)' },
  { value: 'Fechada (expirada)', label: 'Fechada (expirada)' },
  { value: 'Cancelada', label: 'Cancelada' },
  { value: 'Arquivada', label: 'Arquivada' },
  { value: 'Concluída', label: 'Concluída' },
]

const STAGE_OPTIONS = [
  { value: 'Planejamento', label: 'Planejamento' },
  { value: 'Aprovação', label: 'Aprovação' },
  { value: 'Publicada', label: 'Publicada' },
  { value: 'Triagem', label: 'Triagem' },
  { value: 'Entrevistas', label: 'Entrevistas' },
  { value: 'Finalização', label: 'Finalização' },
  { value: 'Encerrada', label: 'Encerrada' },
]

const VISIBILITY_OPTIONS = [
  { value: 'public', label: 'Pública', icon: <Globe className="w-3.5 h-3.5" /> },
  { value: 'internal', label: 'Interna', icon: <Building className="w-3.5 h-3.5" /> },
  { value: 'confidential', label: 'Confidencial', icon: <Shield className="w-3.5 h-3.5" /> },
  { value: 'hidden', label: 'Oculta', icon: <Lock className="w-3.5 h-3.5" /> },
]

const TECH_CATEGORIES = [
  { value: 'Linguagens', label: 'Linguagens' },
  { value: 'Frameworks', label: 'Frameworks' },
  { value: 'Banco de Dados', label: 'Banco de Dados' },
  { value: 'Cloud', label: 'Cloud' },
  { value: 'Containers', label: 'Containers' },
  { value: 'CI/CD', label: 'CI/CD' },
  { value: 'Outros', label: 'Outros' },
]

const SKILL_LEVELS = [
  { value: 'Básico', label: 'Básico' },
  { value: 'Intermediário', label: 'Intermediário' },
  { value: 'Avançado', label: 'Avançado' },
]

const COMPETENCY_WEIGHTS = [
  { value: 'Essencial', label: 'Essencial' },
  { value: 'Importante', label: 'Importante' },
  { value: 'Desejável', label: 'Desejável' },
]

const inputStyle = "h-9 text-xs text-gray-800 bg-gray-50 border-gray-200 focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"
const selectTriggerStyle = "h-9 text-xs text-gray-800 bg-gray-50 border-gray-200 focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"

export function EditJobModal({ isOpen, onClose, job, onSave }: EditJobModalProps) {
  const { interviewStages: companyStages, sla, isLoading: isLoadingStages } = useRecruitmentStages()
  const { buildContextPrompt, isFieldActive, getActiveFields } = useCompanyLiaInstructions()
  // Use buildContextPrompt() when calling AI services for suggestions
  // Example: const context = buildContextPrompt() to get company-specific context for AI
  // Use isFieldActive(fieldKey) to check if a specific field is enabled
  // Use getActiveFields() to get list of all active field keys
  
  const [isSaving, setIsSaving] = useState(false)
  const [formData, setFormData] = useState<Partial<Job>>({
    accessList: [],
    languages: [],
    targetSector: '',
    targetSegment: '',
    maskedCompanyName: '',
    technicalRequirements: [],
    behavioralCompetencies: [],
    screeningQuestions: [],
  })
  const [newRequirement, setNewRequirement] = useState('')
  const [newBenefit, setNewBenefit] = useState('')
  const [newStage, setNewStage] = useState('')
  const [newAccessEmail, setNewAccessEmail] = useState('')
  const [newLanguage, setNewLanguage] = useState('')
  const [newLanguageLevel, setNewLanguageLevel] = useState('Intermediário')
  const [newTechSkill, setNewTechSkill] = useState('')
  const [newTechCategory, setNewTechCategory] = useState('Linguagens')
  const [newTechLevel, setNewTechLevel] = useState('Intermediário')
  const [newBehavioralSkill, setNewBehavioralSkill] = useState('')
  const [newBehavioralWeight, setNewBehavioralWeight] = useState('Importante')
  const [newQuestion, setNewQuestion] = useState('')
  const [newQuestionCategory, setNewQuestionCategory] = useState('vaga')
  const [newInterviewStageName, setNewInterviewStageName] = useState('')
  const [newInterviewStageSLA, setNewInterviewStageSLA] = useState('3')
  const [newInterviewStageType, setNewInterviewStageType] = useState('manual')
  const [companyDepartments, setCompanyDepartments] = useState<{ id: string; name: string; description?: string }[]>([])
  const [companyBenefits, setCompanyBenefits] = useState<CompanyBenefit[]>([])
  const [showImportQuestionsModal, setShowImportQuestionsModal] = useState(false)
  const [companyDefaultQuestions, setCompanyDefaultQuestions] = useState<{
    id: string
    question_text: string
    question_type: string
    options?: string[]
    category?: string
    is_required: boolean
    is_eliminatory: boolean
  }[]>([])
  const [selectedDefaultQuestions, setSelectedDefaultQuestions] = useState<Set<string>>(new Set())
  const [isLoadingDefaultQuestions, setIsLoadingDefaultQuestions] = useState(false)
  const [pipelineTemplates, setPipelineTemplates] = useState<PipelineTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  

  useEffect(() => {
    if (isOpen) {
      liaApi.listDepartments().then(setCompanyDepartments).catch(() => setCompanyDepartments([]))
      liaApi.listBenefits().then(setCompanyBenefits).catch(() => setCompanyBenefits([]))
      fetchPipelineTemplates()
    }
  }, [isOpen])

  useEffect(() => {
    if (isOpen && job) {
      setFormData({
        title: job.title,
        department: job.department,
        location: job.location,
        workModel: job.workModel,
        type: job.type,
        level: job.level,
        recruiter: job.recruiter,
        recruiterEmail: job.recruiterEmail,
        manager: job.manager,
        managerEmail: job.managerEmail,
        openDate: job.openDate,
        deadline: job.deadline || job.deadlineClosing || (sla ? sla.calculateDeadline(sla.totalSLA) : undefined),
        deadlineScreening: job.deadlineScreening || (sla ? sla.calculateDeadline(sla.screeningSLA) : undefined),
        deadlineShortlist: job.deadlineShortlist || (sla ? sla.calculateDeadline(sla.shortlistSLA) : undefined),
        description: job.description,
        requirements: [...(job.requirements || [])],
        salary: job.salary,
        salaryRange: job.salaryRange ? { ...job.salaryRange } : undefined,
        salaryMin: job.salaryRange?.min || job.salaryMin,
        salaryMax: job.salaryRange?.max || job.salaryMax,
        bonusMin: job.bonusMin,
        bonusMax: job.bonusMax,
        benefits: [...(job.benefits || [])],
        interviewStages: job.interviewStages && job.interviewStages.length > 0 
          ? [...job.interviewStages] 
          : companyStages.length > 0 
            ? companyStages.map((stage, index) => ({
                stageName: stage.name,
                order: index + 1,
                type: 'manual' as const,
                sla: stage.sla
              }))
            : [],
        hiringProcess: job.hiringProcess ? [...job.hiringProcess] : [],
        status: job.status,
        stage: job.stage,
        urgencyLevel: job.urgencyLevel,
        visibility: job.visibility || 'public',
        targetAudience: job.targetAudience,
        isConfidential: job.isConfidential,
        isAffirmative: job.isAffirmative,
        affirmativeType: job.affirmativeType,
        publishedLinkedIn: job.publishedLinkedIn,
        publishedWebsite: job.publishedWebsite,
        publishedIndeed: job.publishedIndeed,
        targetSector: job.targetSector,
        targetSegment: job.targetSegment,
        maskedCompanyName: job.maskedCompanyName,
        accessList: job.accessList ? [...job.accessList] : [],
        languages: job.languages ? [...job.languages] : [],
        technicalRequirements: job.technicalRequirements ? [...job.technicalRequirements] : [],
        behavioralCompetencies: job.behavioralCompetencies ? [...job.behavioralCompetencies] : [],
        screeningQuestions: job.screeningQuestions ? job.screeningQuestions.map((q: any) => ({
          id: q.id,
          text: q.text || q.question || '',
          category: q.category || 'custom',
          type: q.type,
          weight: q.weight,
          is_eliminatory: q.is_eliminatory || false,
          expected_answer: q.expected_answer || ''
        })) : [],
        eligibilityQuestions: job.eligibilityQuestions ? [...job.eligibilityQuestions] : [],
        confidentialityConfig: job.confidentialityConfig || {
          can_reveal_company_name: true,
          can_discuss_salary: true,
          can_discuss_benefits: true,
          can_discuss_location: true,
        },
      })
    }
  }, [isOpen, job, companyStages, sla])

  const fetchPipelineTemplates = async () => {
    setIsLoadingTemplates(true)
    try {
      const response = await fetch('/api/backend-proxy/company/pipeline-templates/')
      if (response.ok) {
        const data = await response.json()
        setPipelineTemplates(data.items || [])
        if (data.items?.length === 0) {
          await fetch('/api/backend-proxy/company/pipeline-templates/seed-defaults', { method: 'POST' })
          const retryResponse = await fetch('/api/backend-proxy/company/pipeline-templates/')
          if (retryResponse.ok) {
            const retryData = await retryResponse.json()
            setPipelineTemplates(retryData.items || [])
          }
        }
      }
    } catch (error) {
      console.error('Error fetching pipeline templates:', error)
    } finally {
      setIsLoadingTemplates(false)
    }
  }

  const applyPipelineTemplate = (templateId: string) => {
    const template = pipelineTemplates.find(t => t.id === templateId)
    if (!template) return
    
    const stages: InterviewStage[] = template.stages.map((s, idx) => ({
      stageName: s.name,
      order: s.order || idx + 1,
      sla: s.sla_days,
      type: s.type === 'automatic' ? 'automated' : s.type as 'automated' | 'manual' | 'hybrid'
    }))
    
    setFormData(prev => ({ ...prev, interviewStages: stages }))
    setSelectedTemplateId(templateId)
    toast.success(`Template "${template.name}" aplicado com sucesso`)
    
    fetch(`/api/backend-proxy/company/pipeline-templates/${templateId}/increment-usage`, { method: 'POST' }).catch(() => {})
  }

  if (!isOpen || !job) return null

  const updateField = <K extends keyof Job>(field: K, value: Job[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const addRequirement = () => {
    if (newRequirement.trim()) {
      setFormData(prev => ({
        ...prev,
        requirements: [...(prev.requirements || []), newRequirement.trim()]
      }))
      setNewRequirement('')
    }
  }

  const removeRequirement = (index: number) => {
    setFormData(prev => ({
      ...prev,
      requirements: (prev.requirements || []).filter((_, i) => i !== index)
    }))
  }

  const addBenefit = () => {
    if (newBenefit.trim()) {
      setFormData(prev => ({
        ...prev,
        benefits: [...(prev.benefits || []), newBenefit.trim()]
      }))
      setNewBenefit('')
    }
  }

  const removeBenefit = (index: number) => {
    setFormData(prev => ({
      ...prev,
      benefits: (prev.benefits || []).filter((_, i) => i !== index)
    }))
  }

  const addStage = () => {
    if (newStage.trim()) {
      setFormData(prev => ({
        ...prev,
        hiringProcess: [...(prev.hiringProcess || []), newStage.trim()]
      }))
      setNewStage('')
    }
  }

  const removeStage = (index: number) => {
    setFormData(prev => ({
      ...prev,
      hiringProcess: (prev.hiringProcess || []).filter((_, i) => i !== index)
    }))
  }

  const addInterviewStage = () => {
    if (newInterviewStageName.trim()) {
      const currentStages = formData.interviewStages || []
      const newStage: InterviewStage = {
        stageName: newInterviewStageName.trim(),
        order: currentStages.length + 1,
        sla: parseInt(newInterviewStageSLA) || 3,
        type: newInterviewStageType as 'automated' | 'manual' | 'hybrid'
      }
      setFormData(prev => ({
        ...prev,
        interviewStages: [...currentStages, newStage]
      }))
      setNewInterviewStageName('')
      setNewInterviewStageSLA('3')
      setNewInterviewStageType('manual')
    }
  }

  const removeInterviewStage = (index: number) => {
    setFormData(prev => ({
      ...prev,
      interviewStages: (prev.interviewStages || [])
        .filter((_, i) => i !== index)
        .map((stage, i) => ({ ...stage, order: i + 1 }))
    }))
  }

  const updateInterviewStage = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      interviewStages: (prev.interviewStages || []).map((stage, i) => 
        i === index ? { ...stage, [field]: value } : stage
      )
    }))
  }

  const addAccessEmail = () => {
    if (newAccessEmail.trim() && newAccessEmail.includes('@')) {
      setFormData(prev => ({
        ...prev,
        accessList: [...(prev.accessList || []), newAccessEmail.trim()]
      }))
      setNewAccessEmail('')
    }
  }

  const removeAccessEmail = (index: number) => {
    setFormData(prev => ({
      ...prev,
      accessList: (prev.accessList || []).filter((_, i) => i !== index)
    }))
  }

  const addLanguage = () => {
    if (newLanguage.trim()) {
      setFormData(prev => ({
        ...prev,
        languages: [...(prev.languages || []), { language: newLanguage.trim(), level: newLanguageLevel, required: false }]
      }))
      setNewLanguage('')
      setNewLanguageLevel('Intermediário')
    }
  }

  const removeLanguage = (index: number) => {
    setFormData(prev => ({
      ...prev,
      languages: (prev.languages || []).filter((_, i) => i !== index)
    }))
  }

  const addTechnicalSkill = () => {
    if (newTechSkill.trim()) {
      setFormData(prev => ({
        ...prev,
        technicalRequirements: [...(prev.technicalRequirements || []), { 
          category: newTechCategory, 
          technology: newTechSkill.trim(), 
          level: newTechLevel, 
          required: true 
        }]
      }))
      setNewTechSkill('')
    }
  }

  const removeTechnicalSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      technicalRequirements: (prev.technicalRequirements || []).filter((_, i) => i !== index)
    }))
  }

  const addBehavioralSkill = () => {
    if (newBehavioralSkill.trim()) {
      setFormData(prev => ({
        ...prev,
        behavioralCompetencies: [...(prev.behavioralCompetencies || []), { 
          competency: newBehavioralSkill.trim(), 
          weight: newBehavioralWeight 
        }]
      }))
      setNewBehavioralSkill('')
    }
  }

  const removeBehavioralSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      behavioralCompetencies: (prev.behavioralCompetencies || []).filter((_, i) => i !== index)
    }))
  }

  const addScreeningQuestion = () => {
    if (newQuestion.trim()) {
      setFormData(prev => ({
        ...prev,
        screeningQuestions: [...(prev.screeningQuestions || []), {
          id: `q-${Date.now()}`,
          text: newQuestion.trim(),
          category: newQuestionCategory,
          weight: 5
        }]
      }))
      setNewQuestion('')
    }
  }

  const removeScreeningQuestion = (index: number) => {
    setFormData(prev => ({
      ...prev,
      screeningQuestions: (prev.screeningQuestions || []).filter((_, i) => i !== index)
    }))
  }

  const fetchCompanyDefaultQuestions = async () => {
    setIsLoadingDefaultQuestions(true)
    try {
      const response = await fetch('/api/backend-proxy/company/screening-questions')
      if (response.ok) {
        const data = await response.json()
        setCompanyDefaultQuestions(data.items || [])
      } else {
        toast.error('Erro ao carregar perguntas padrão')
      }
    } catch (error) {
      console.error('Error fetching default questions:', error)
      toast.error('Erro ao carregar perguntas padrão')
    } finally {
      setIsLoadingDefaultQuestions(false)
    }
  }

  const openImportQuestionsModal = () => {
    setShowImportQuestionsModal(true)
    setSelectedDefaultQuestions(new Set())
    fetchCompanyDefaultQuestions()
  }

  const toggleQuestionSelection = (questionId: string) => {
    setSelectedDefaultQuestions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(questionId)) {
        newSet.delete(questionId)
      } else {
        newSet.add(questionId)
      }
      return newSet
    })
  }

  const importSelectedQuestions = () => {
    const questionsToImport = companyDefaultQuestions.filter(q => selectedDefaultQuestions.has(q.id))
    const newQuestions = questionsToImport.map(q => ({
      id: `imported-${q.id}`,
      text: q.question_text,
      category: q.category || 'custom',
      type: q.question_type,
      weight: 5
    }))
    
    setFormData(prev => ({
      ...prev,
      screeningQuestions: [...(prev.screeningQuestions || []), ...newQuestions]
    }))
    
    setShowImportQuestionsModal(false)
    toast.success(`${questionsToImport.length} pergunta(s) importada(s)`)
  }

  const getCategoryLabel = (category: string | undefined) => {
    const labels: Record<string, string> = {
      availability: 'Disponibilidade',
      salary: 'Salário',
      work_model: 'Modelo de Trabalho',
      logistics: 'Logística',
      legal: 'Legal/Documentação',
      experience: 'Experiência',
      language: 'Idiomas',
      custom: 'Personalizada'
    }
    return labels[category || 'custom'] || category || 'Custom'
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      
      let salaryMin: number | undefined = formData.salaryMin
      let salaryMax: number | undefined = formData.salaryMax

      // Fallback to parsing salary string if new fields are empty
      if (!salaryMin && !salaryMax && formData.salary) {
        const salaryNumbers = formData.salary.match(/[\d.,]+/g)
        if (salaryNumbers && salaryNumbers.length > 0) {
          const parseNumber = (s: string) => Number(s.replace(/\./g, '').replace(',', '.'))
          salaryMin = parseNumber(salaryNumbers[0])
          salaryMax = salaryNumbers.length > 1 ? parseNumber(salaryNumbers[1]) : salaryMin
        }
      }
      
      const updates: Partial<JobVacancy> = {
        title: formData.title,
        department: formData.department,
        location: formData.location,
        work_model: formData.workModel,
        employment_type: formData.type,
        seniority_level: formData.level,
        recruiter: formData.recruiter,
        recruiter_email: formData.recruiterEmail,
        manager: formData.manager,
        manager_email: formData.managerEmail,
        open_date: formData.openDate,
        deadline: formData.deadline,
        deadline_screening: formData.deadlineScreening,
        deadline_shortlist: formData.deadlineShortlist,
        description: formData.description,
        requirements: formData.requirements,
        salary: formData.salary,
        salary_range: salaryMin ? {
          min: salaryMin,
          max: salaryMax || salaryMin,
          currency: 'BRL'
        } : undefined,
        bonus_range: (formData.bonusMin || formData.bonusMax) ? {
          min: formData.bonusMin || 0,
          max: formData.bonusMax || formData.bonusMin || 0,
          currency: 'BRL'
        } : undefined,
        benefits: formData.benefits,
        interview_stages: (formData.interviewStages || []).filter(
          (stage): stage is InterviewStage => 
            !!stage.stageName && typeof stage.order === 'number' && typeof stage.sla === 'number'
        ).map(stage => ({
          stageName: stage.stageName,
          order: stage.order,
          sla: stage.sla,
          type: stage.type || 'manual'
        })),
        hiring_process: (formData.interviewStages && formData.interviewStages.length > 0)
          ? formData.interviewStages.map(s => s.stageName)
          : formData.hiringProcess,
        status: formData.status,
        stage: formData.stage,
        urgency_level: formData.urgencyLevel,
        visibility: formData.visibility,
        target_audience: formData.targetAudience,
        is_confidential: formData.isConfidential,
        is_affirmative: formData.isAffirmative,
        affirmative_type: formData.affirmativeType,
        published_linkedin: formData.publishedLinkedIn,
        published_website: formData.publishedWebsite,
        published_indeed: formData.publishedIndeed,
        target_sector: formData.targetSector,
        target_segment: formData.targetSegment,
        masked_company_name: formData.maskedCompanyName,
        access_list: formData.accessList,
        languages: formData.languages,
        technical_requirements: formData.technicalRequirements,
        behavioral_competencies: formData.behavioralCompetencies,
        screening_questions: formData.screeningQuestions?.map(q => ({
          id: q.id || `q-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          question: q.text,
          type: q.type,
          category: q.category,
          weight: q.weight,
          is_eliminatory: q.is_eliminatory || false,
          expected_answer: q.expected_answer || ''
        })) as any,
        eligibility_questions: formData.eligibilityQuestions as any,
        confidentiality_config: formData.confidentialityConfig as any,
      }

      Object.keys(updates).forEach(key => {
        if (updates[key as keyof typeof updates] === undefined) {
          delete updates[key as keyof typeof updates]
        }
      })

      await onSave(job.backendId || job.jobId, updates)

      // Sync wsi_skills with screening_config for interview question generation
      const wsiSkillsToSync: string[] = []

      // Add technical requirements to wsi_skills
      if (formData.technicalRequirements && formData.technicalRequirements.length > 0) {
        formData.technicalRequirements.forEach(req => {
          if (req.technology) wsiSkillsToSync.push(req.technology)
        })
      }

      // Add behavioral competencies to wsi_skills
      if (formData.behavioralCompetencies && formData.behavioralCompetencies.length > 0) {
        formData.behavioralCompetencies.forEach(comp => {
          if (comp.competency) wsiSkillsToSync.push(comp.competency)
        })
      }

      // Always sync wsi_skills with screening_config (even if empty to clear stale data)
      try {
        await fetch(`/api/backend-proxy/jobs/${job.backendId || job.jobId}/screening-config`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            wsi_skills: wsiSkillsToSync
          }),
        })
      } catch (syncError) {
        console.warn('Failed to sync wsi_skills with screening config:', syncError)
        // Don't fail the save operation if sync fails
      }

      toast.success('Vaga atualizada com sucesso!')
      onClose()
    } catch (error) {
      console.error('Error saving job:', error)
      toast.error('Erro ao salvar alterações')
    } finally {
      setIsSaving(false)
    }
  }

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Linguagens': 'bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30',
      'Frameworks': 'bg-status-success/10 text-status-success border-status-success/30',
      'Banco de Dados': 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30',
      'Cloud': 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30',
      'Containers': 'bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600',
      'CI/CD': 'bg-wedo-magenta/10 text-wedo-magenta border-wedo-magenta/30',
      'Outros': 'bg-gray-50 text-gray-700 border-gray-200',
    }
    return colors[category] || colors['Outros']
  }

  const getWeightColor = (weight: string) => {
    const colors: Record<string, string> = {
      'Essencial': 'bg-status-error/10 text-status-error border-status-error/30',
      'Importante': 'bg-status-warning/10 text-status-warning border-status-warning/30',
      'Desejável': 'bg-status-success/10 text-status-success border-status-success/30',
    }
    return colors[weight] || 'bg-gray-50 text-gray-700 border-gray-200'
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-[2px]"
        onClick={onClose}
      />
      
      <div className="relative bg-white dark:bg-gray-800 rounded-md w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-50">Editar Vaga</h2>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                <span className="text-gray-600 font-medium mr-1.5">{job.jobId}</span>
                {job.title}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 rounded-md hover:bg-gray-100"
            onClick={onClose}
          >
            <X className="w-4 h-4 text-gray-500" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
              <div className="space-y-6">
                
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Briefcase className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Informações Básicas</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs font-medium text-gray-800 mb-1 block">Título da Vaga</Label>
                      <Input
                        value={formData.title || ''}
                        onChange={(e) => updateField('title', e.target.value)}
                        className={inputStyle}
                        placeholder="Ex: Desenvolvedor Full Stack"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Departamento</Label>
                        {companyDepartments.length > 0 ? (
                          <Select 
                            value={formData.department || ''} 
                            onValueChange={(v) => updateField('department', v)}
                          >
                            <SelectTrigger className={selectTriggerStyle}>
                              <SelectValue placeholder="Selecione um departamento" />
                            </SelectTrigger>
                            <SelectContent>
                              {companyDepartments.map(dept => (
                                <SelectItem key={dept.id} value={dept.name} className="text-sm">
                                  {dept.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={formData.department || ''}
                            onChange={(e) => updateField('department', e.target.value)}
                            className={inputStyle}
                            placeholder="Ex: Tecnologia"
                          />
                        )}
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Localização</Label>
                        <Input
                          value={formData.location || ''}
                          onChange={(e) => updateField('location', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: São Paulo, SP"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Modelo de Trabalho</Label>
                        <Select value={formData.workModel} onValueChange={(v) => updateField('workModel', v as any)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {WORK_MODELS.map(m => (
                              <SelectItem key={m.value} value={m.value} className="text-sm">{m.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Tipo de Contrato</Label>
                        <Select value={formData.type} onValueChange={(v) => updateField('type', v)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CONTRACT_TYPES.map(t => (
                              <SelectItem key={t.value} value={t.value} className="text-sm">{t.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Senioridade</Label>
                        <Select value={formData.level} onValueChange={(v) => updateField('level', v)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SENIORITY_LEVELS.map(l => (
                              <SelectItem key={l.value} value={l.value} className="text-sm">{l.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Pessoas Responsáveis</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="p-3 bg-gray-50 rounded-md border border-gray-100">
                      <p className="text-xs font-medium uppercase text-gray-600 mb-2">Recrutador(a)</p>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">Nome</Label>
                          <Input
                            value={formData.recruiter || ''}
                            onChange={(e) => updateField('recruiter', e.target.value)}
                            className={`${inputStyle} bg-white`}
                            placeholder="Nome do recrutador"
                          />
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">E-mail</Label>
                          <Input
                            value={formData.recruiterEmail || ''}
                            onChange={(e) => updateField('recruiterEmail', e.target.value)}
                            className={`${inputStyle} bg-white`}
                            placeholder="email@empresa.com"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="p-3 bg-gray-50 rounded-md border border-gray-100">
                      <p className="text-xs font-medium uppercase text-gray-600 mb-2">Gestor(a) Solicitante</p>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">Nome</Label>
                          <Input
                            value={formData.manager || ''}
                            onChange={(e) => updateField('manager', e.target.value)}
                            className={`${inputStyle} bg-white`}
                            placeholder="Nome do gestor"
                          />
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">E-mail</Label>
                          <Input
                            value={formData.managerEmail || ''}
                            onChange={(e) => updateField('managerEmail', e.target.value)}
                            className={`${inputStyle} bg-white`}
                            placeholder="email@empresa.com"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Calendar className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Timeline do Processo</h3>
                  </div>
                  
                  <div className="relative pl-4 border-l-2 border-gray-300 space-y-4">
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-status-success border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-gray-800 mb-1 block flex items-center gap-1.5">
                          <span className="text-status-success font-medium">1.</span> Data de Abertura
                        </Label>
                        <Input
                          type="date"
                          value={formData.openDate || ''}
                          onChange={(e) => updateField('openDate' as keyof Job, e.target.value as any)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-cyan border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-gray-800 mb-1 block flex items-center gap-1.5">
                          <span className="text-wedo-cyan-dark font-medium">2.</span> Prazo Screening
                          <span className="text-micro text-gray-400">(triagem inicial)</span>
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadlineScreening || ''}
                          onChange={(e) => updateField('deadlineScreening' as keyof Job, e.target.value as any)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-purple border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-gray-800 mb-1 block flex items-center gap-1.5">
                          <span className="text-wedo-purple font-medium">3.</span> Prazo Shortlist
                          <span className="text-micro text-gray-400">(lista curta)</span>
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadlineShortlist || ''}
                          onChange={(e) => updateField('deadlineShortlist' as keyof Job, e.target.value as any)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-orange border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-gray-800 mb-1 block flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-wedo-orange" />
                          <span className="text-wedo-orange font-medium">4.</span> Prazo Final
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadline || ''}
                          onChange={(e) => updateField('deadline' as keyof Job, e.target.value as any)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Descrição</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs font-medium text-gray-800 mb-1 block">Descrição da Vaga</Label>
                      <Textarea
                        value={formData.description || ''}
                        onChange={(e) => updateField('description', e.target.value)}
                        className="min-h-[100px] text-sm resize-none bg-gray-50 border-gray-200 focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"
                        placeholder="Descreva as responsabilidades, objetivos e contexto da vaga..."
                      />
                    </div>

                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <DollarSign className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Remuneração</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs font-medium text-gray-800 mb-1 block">Faixa Salarial</Label>
                      <div className="flex gap-3">
                        <div className="flex-1">
                          <span className="text-micro text-gray-500 mb-1 block">De</span>
                          <Input
                            type="number"
                            value={formData.salaryMin || ''}
                            onChange={(e) => updateField('salaryMin' as keyof Job, Number(e.target.value) as any)}
                            className={inputStyle}
                            placeholder="12.000"
                          />
                        </div>
                        <div className="flex-1">
                          <span className="text-micro text-gray-500 mb-1 block">Até</span>
                          <Input
                            type="number"
                            value={formData.salaryMax || ''}
                            onChange={(e) => updateField('salaryMax' as keyof Job, Number(e.target.value) as any)}
                            className={inputStyle}
                            placeholder="18.000"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs font-medium text-gray-800 mb-1 block">Bônus Anual (opcional)</Label>
                      <div className="flex gap-3">
                        <div className="flex-1">
                          <span className="text-micro text-gray-500 mb-1 block">De</span>
                          <Input
                            type="number"
                            value={formData.bonusMin || ''}
                            onChange={(e) => updateField('bonusMin' as keyof Job, Number(e.target.value) as any)}
                            className={inputStyle}
                            placeholder="2.000"
                          />
                        </div>
                        <div className="flex-1">
                          <span className="text-micro text-gray-500 mb-1 block">Até</span>
                          <Input
                            type="number"
                            value={formData.bonusMax || ''}
                            onChange={(e) => updateField('bonusMax' as keyof Job, Number(e.target.value) as any)}
                            className={inputStyle}
                            placeholder="6.000"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs text-gray-600 mb-2 block">Benefícios</Label>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {(formData.benefits || []).map((benefit, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="flex items-center gap-1 py-0.5 px-2 text-xs bg-white dark:bg-gray-900"
                          >
                            <button
                              onClick={() => removeBenefit(idx)}
                              className="text-gray-600 dark:text-gray-400 hover:text-status-error dark:hover:text-status-error mr-0.5"
                              type="button"
                            >
                              ×
                            </button>
                            {benefit}
                            {companyBenefits.find(cb => cb.name === benefit)?.is_highlighted && (
                              <Heart className="w-3 h-3 text-wedo-magenta fill-pink-500" />
                            )}
                          </Badge>
                        ))}
                      </div>
                      {companyBenefits.length > 0 && (
                        <div className="mb-3">
                          <Label className="text-xs text-gray-500 mb-1.5 block">Sugestões da empresa</Label>
                          <div className="flex flex-wrap gap-1.5">
                            {companyBenefits.map((benefit) => {
                              const isAdded = (formData.benefits || []).includes(benefit.name)
                              return (
                                <Badge
                                  key={benefit.id}
                                  variant="outline"
                                  className={`text-xs px-2 py-0.5 cursor-pointer transition-colors ${
                                    isAdded 
                                      ? 'bg-gray-100 border-gray-900 text-gray-900' 
                                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100 hover:border-gray-400 hover:text-gray-800'
                                  }`}
                                  onClick={() => {
                                    if (!isAdded) {
                                      setFormData(prev => ({
                                        ...prev,
                                        benefits: [...(prev.benefits || []), benefit.name]
                                      }))
                                    }
                                  }}
                                >
                                  {isAdded && <CheckCircle className="w-3 h-3 mr-1" />}
                                  {benefit.is_highlighted && <Heart className="w-3 h-3 mr-1 text-wedo-magenta" />}
                                  {benefit.name}
                                  {!isAdded && <Plus className="w-3 h-3 ml-1" />}
                                </Badge>
                              )
                            })}
                          </div>
                        </div>
                      )}
                      <div className="flex gap-2">
                        <Input
                          value={newBenefit}
                          onChange={(e) => setNewBenefit(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addBenefit())}
                          className={`${inputStyle} flex-1`}
                          placeholder="Ex: Vale Refeição, Plano de Saúde..."
                        />
                        <Button
                          variant="outline"
                          className="h-10 px-4 text-sm border-gray-900 text-gray-900 hover:bg-gray-100"
                          onClick={addBenefit}
                        >
                          <Plus className="w-4 h-4 mr-1.5" />
                          Adicionar
                        </Button>
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-gray-600" />
                      <h3 className="text-base-ui font-semibold text-gray-950">Etapas do Processo Seletivo</h3>
                      {(formData.interviewStages || []).length > 0 && (
                        <Badge variant="outline" className="text-xs bg-gray-100 border-gray-300 text-gray-700">
                          {(formData.interviewStages || []).length} etapas
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <ClipboardList className="w-3.5 h-3.5 text-gray-400" />
                      <Select 
                        value={selectedTemplateId} 
                        onValueChange={(value) => {
                          if (value && value !== 'none') {
                            applyPipelineTemplate(value)
                          }
                        }}
                      >
                        <SelectTrigger className="h-8 w-[180px] text-xs bg-white border-gray-200">
                          {isLoadingTemplates ? (
                            <span className="flex items-center gap-1.5">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Carregando...
                            </span>
                          ) : (
                            <SelectValue placeholder="Usar template" />
                          )}
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none" className="text-xs text-gray-400">Selecionar template...</SelectItem>
                          {pipelineTemplates.map(template => (
                            <SelectItem key={template.id} value={template.id} className="text-xs">
                              <div className="flex items-center gap-2">
                                {template.is_default && <Badge variant="outline" className="text-micro px-1 py-0 h-4">Padrão</Badge>}
                                {template.name}
                                <span className="text-gray-400">({template.stages.length} etapas)</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    {(formData.interviewStages || []).map((stage: InterviewStage, idx: number) => (
                      <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-md border border-gray-100">
                        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 text-gray-700 text-sm font-semibold shrink-0">
                          {stage.order || idx + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <Input
                            value={stage.stageName || ''}
                            onChange={(e) => updateInterviewStage(idx, 'stageName', e.target.value)}
                            className="h-8 text-sm bg-white border-gray-200 focus:border-gray-400"
                            placeholder="Nome da etapa"
                          />
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-gray-500">SLA:</span>
                            <Select 
                              value={String(stage.sla || 3)} 
                              onValueChange={(v) => updateInterviewStage(idx, 'sla', parseInt(v))}
                            >
                              <SelectTrigger className="h-8 w-16 text-xs bg-white border-gray-200">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {[1, 2, 3, 5, 7, 10, 14].map(d => (
                                  <SelectItem key={d} value={String(d)} className="text-xs">{d}d</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <Select 
                            value={stage.type || 'manual'} 
                            onValueChange={(v) => updateInterviewStage(idx, 'type', v)}
                          >
                            <SelectTrigger className="h-8 w-24 text-xs bg-white border-gray-200">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="automated" className="text-xs">Auto</SelectItem>
                              <SelectItem value="manual" className="text-xs">Manual</SelectItem>
                              <SelectItem value="hybrid" className="text-xs">Híbrido</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 hover:bg-status-error/10"
                            onClick={() => removeInterviewStage(idx)}
                          >
                            <Trash2 className="w-3.5 h-3.5 text-status-error" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Input
                        value={newInterviewStageName}
                        onChange={(e) => setNewInterviewStageName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addInterviewStage())}
                        className={`${inputStyle}`}
                        placeholder="Nova etapa (ex: Entrevista Técnica)"
                      />
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-gray-500">SLA:</span>
                      <Select value={newInterviewStageSLA} onValueChange={setNewInterviewStageSLA}>
                        <SelectTrigger className="h-10 w-16 text-xs bg-gray-50 border-gray-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 5, 7, 10, 14].map(d => (
                            <SelectItem key={d} value={String(d)} className="text-xs">{d}d</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Select value={newInterviewStageType} onValueChange={setNewInterviewStageType}>
                      <SelectTrigger className="h-10 w-24 text-xs bg-gray-50 border-gray-200">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="automated" className="text-xs">Auto</SelectItem>
                        <SelectItem value="manual" className="text-xs">Manual</SelectItem>
                        <SelectItem value="hybrid" className="text-xs">Híbrido</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="outline"
                      className="h-10 px-4 text-sm border-gray-900 text-gray-900 hover:bg-gray-100"
                      onClick={addInterviewStage}
                    >
                      <Plus className="w-4 h-4 mr-1.5" />
                      Adicionar
                    </Button>
                  </div>
                </section>

                <hr className="border-gray-100" />

                {/* NEW: Configuração de Confidencialidade para LIA */}
                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Shield className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Configuração de Confidencialidade para LIA</h3>
                  </div>
                  
                  <p className="text-xs text-gray-500 mb-3">
                    Configure o que a LIA pode ou não revelar durante conversas com candidatos.
                  </p>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <Building className="w-3.5 h-3.5 text-gray-500" />
                        <span className="text-xs text-gray-700">LIA pode revelar o nome da empresa?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as any)?.can_reveal_company_name ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig as any) || {}),
                            can_reveal_company_name: checked
                          } as any)
                        }}
                      />
                    </div>

                    {!(formData.confidentialityConfig as any)?.can_reveal_company_name && (
                      <div className="ml-4 p-2 bg-status-warning/10 rounded-md border border-status-warning/30">
                        <Label className="text-xs text-status-warning mb-1.5 block">
                          Apresentação mascarada para candidatos:
                        </Label>
                        <Input
                          value={(formData.confidentialityConfig as any)?.masked_intro || ''}
                          onChange={(e) => {
                            updateField('confidentialityConfig', {
                              ...((formData.confidentialityConfig as any) || {}),
                              masked_intro: e.target.value
                            } as any)
                          }}
                          className="h-8 text-xs bg-white border-status-warning/30"
                          placeholder="Uma empresa líder no segmento de pagamentos"
                        />
                      </div>
                    )}

                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-3.5 h-3.5 text-gray-500" />
                        <span className="text-xs text-gray-700">LIA pode discutir faixa salarial?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as any)?.can_discuss_salary ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig as any) || {}),
                            can_discuss_salary: checked
                          } as any)
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <Heart className="w-3.5 h-3.5 text-gray-500" />
                        <span className="text-xs text-gray-700">LIA pode discutir benefícios?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as any)?.can_discuss_benefits ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig as any) || {}),
                            can_discuss_benefits: checked
                          } as any)
                        }}
                      />
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Settings className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Status e Configurações</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Status</Label>
                        <Select value={formData.status} onValueChange={(v) => updateField('status', v as any)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {STATUS_OPTIONS.map(s => (
                              <SelectItem key={s.value} value={s.value} className="text-sm">{s.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Urgência</Label>
                        <Select 
                          value={String(formData.urgencyLevel)} 
                          onValueChange={(v) => updateField('urgencyLevel', parseInt(v) as any)}
                        >
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {[1, 2, 3, 4, 5].map(n => (
                              <SelectItem key={n} value={String(n)} className="text-sm">
                                {n} - {n === 1 ? 'Baixa' : n === 2 ? 'Normal' : n === 3 ? 'Média' : n === 4 ? 'Alta' : 'Crítica'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs font-medium text-gray-800 mb-1 block">Visibilidade</Label>
                      <Select value={formData.visibility} onValueChange={(v) => updateField('visibility', v as any)}>
                        <SelectTrigger className={selectTriggerStyle}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {VISIBILITY_OPTIONS.map(v => (
                            <SelectItem key={v.value} value={v.value} className="text-sm">
                              <div className="flex items-center gap-2">
                                {v.icon}
                                {v.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-md border border-gray-100 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-wedo-orange" />
                          <span className="text-sm text-gray-700">Vaga Confidencial</span>
                        </div>
                        <Switch
                          checked={formData.isConfidential || false}
                          onCheckedChange={(checked: boolean) => updateField('isConfidential', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-wedo-magenta" />
                          <span className="text-sm text-gray-700">Vaga Afirmativa</span>
                        </div>
                        <Switch
                          checked={formData.isAffirmative || false}
                          onCheckedChange={(checked: boolean) => { updateField('isAffirmative', checked); if (!checked) updateField('affirmativeType', undefined); }}
                        />
                      </div>
                      {formData.isAffirmative && (
                        <div className="space-y-3 mt-3 p-4 bg-wedo-purple/10 rounded-md border border-wedo-purple/30">
                          <div>
                            <Label className="text-xs font-medium text-gray-800 mb-2 block">Tipo de Ação Afirmativa</Label>
                            <div className="grid grid-cols-2 gap-2">
                              {[
                                { value: 'pcd', label: 'PCD', desc: 'Pessoas com Deficiência' },
                                { value: 'racial', label: 'Racial', desc: 'Pessoas negras (pretas e pardas)' },
                                { value: 'gender', label: 'Gênero', desc: 'Mulheres' },
                                { value: 'age', label: '50+', desc: 'Profissionais 50+' },
                                { value: 'lgbtqia+', label: 'LGBTQIA+', desc: 'Pessoas LGBTQIA+' },
                              ].map((option) => (
                                <div
                                  key={option.value}
                                  className={cn(
                                    "p-2.5 rounded-md border cursor-pointer transition-all",
                                    formData.affirmativeType === option.value
                                      ? "border-wedo-purple/30 bg-wedo-purple/15"
                                      : "border-wedo-purple/30 bg-white hover:border-wedo-purple/30"
                                  )}
                                  onClick={() => updateField('affirmativeType', formData.affirmativeType === option.value ? undefined : option.value as Job['affirmativeType'])}
                                >
                                  <span className="text-xs font-medium text-gray-800 block">{option.label}</span>
                                  <span className="text-micro text-gray-500">{option.desc}</span>
                                </div>
                              ))}
                            </div>
                            <p className="text-micro text-gray-500 mt-2">A LIA incluirá uma pergunta de autodeclaração na triagem WSI</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {formData.isConfidential && (
                      <div className="space-y-4 mt-4 p-4 bg-wedo-orange/10 rounded-md border border-wedo-orange/30">
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">Nome Mascarado da Empresa</Label>
                          <Input
                            value={formData.maskedCompanyName || ''}
                            onChange={(e) => updateField('maskedCompanyName', e.target.value)}
                            className={inputStyle}
                            placeholder="Ex: Empresa líder no segmento de tecnologia"
                          />
                          <p className="text-xs text-gray-500 mt-1">Nome exibido em publicações anônimas</p>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-gray-800 mb-1 block">Lista de Acesso</Label>
                          <div className="flex gap-2 mb-2">
                            <Input
                              value={newAccessEmail}
                              onChange={(e) => setNewAccessEmail(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAccessEmail())}
                              className={inputStyle + " flex-1"}
                              placeholder="email@empresa.com"
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={addAccessEmail}
                              className="h-9 px-3"
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {(formData.accessList || []).map((email, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs py-1 px-2 bg-white border border-gray-200">
                                <UserPlus className="w-3 h-3 mr-1 text-gray-400" />
                                {email}
                                <button
                                  onClick={() => removeAccessEmail(idx)}
                                  className="ml-1.5 text-gray-400 hover:text-status-error"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </Badge>
                            ))}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">Usuários com acesso à vaga confidencial</p>
                        </div>
                      </div>
                    )}
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Globe className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Publicação</h3>
                  </div>
                  
                  <div className="p-4 bg-gray-50 rounded-md border border-gray-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Linkedin className="w-4 h-4 text-gray-600" />
                        <span className="text-sm text-gray-700">LinkedIn</span>
                      </div>
                      <Switch
                        checked={formData.publishedLinkedIn || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedLinkedIn', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-status-success" />
                        <span className="text-sm text-gray-700">Website Corporativo</span>
                      </div>
                      <Switch
                        checked={formData.publishedWebsite || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedWebsite', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-4 h-4 text-wedo-purple" />
                        <span className="text-sm text-gray-700">Indeed</span>
                      </div>
                      <Switch
                        checked={formData.publishedIndeed || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedIndeed', checked)}
                      />
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                {/* Informações do Registro (Read-only) */}
                {(job?.createdBy || job?.createdAt) && (
                  <section>
                    <div className="flex items-center gap-2 mb-4">
                      <Users className="w-4 h-4 text-gray-400" />
                      <h3 className="text-xs font-semibold text-gray-500">Informações do Registro</h3>
                      <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-400 border-gray-200">
                        Somente leitura
                      </Badge>
                    </div>
                    
                    <div className="p-4 bg-gray-50 rounded-md border border-gray-100">
                      <div className="grid grid-cols-2 gap-4">
                        {job?.createdBy && (
                          <div>
                            <Label className="text-xs text-gray-500 mb-1 block">Criado por</Label>
                            <div className="text-sm text-gray-700 font-medium">{job.createdBy}</div>
                            {job?.createdByEmail && (
                              <div className="text-xs text-gray-500">{job.createdByEmail}</div>
                            )}
                          </div>
                        )}
                        {job?.createdAt && (
                          <div>
                            <Label className="text-xs text-gray-500 mb-1 block">Data de Criação</Label>
                            <div className="text-sm text-gray-700">
                              {new Date(job.createdAt).toLocaleDateString('pt-BR', { 
                                day: '2-digit', 
                                month: 'long', 
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </section>
                )}

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Público-Alvo & Segmentação</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <Textarea
                      value={formData.targetAudience || ''}
                      onChange={(e) => updateField('targetAudience', e.target.value)}
                      className="min-h-20 text-sm resize-none bg-gray-50 border-gray-200 focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"
                      placeholder="Descreva o perfil ideal de candidato para esta vaga..."
                    />
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Setor-Alvo</Label>
                        <Input
                          value={formData.targetSector || ''}
                          onChange={(e) => updateField('targetSector', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: Fintechs, Bancos Digitais"
                        />
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-gray-800 mb-1 block">Segmento-Alvo</Label>
                        <Input
                          value={formData.targetSegment || ''}
                          onChange={(e) => updateField('targetSegment', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: Meios de Pagamento"
                        />
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-gray-100" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Languages className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base-ui font-semibold text-gray-950">Idiomas Requeridos</h3>
                    <span className="inline-flex items-center gap-1 text-xs text-gray-500" title="Idiomas padrão vindos das configurações">
                      <Settings className="w-3 h-3" />
                      Settings
                    </span>
                  </div>
                  
                  <div className="flex gap-2 mb-2">
                    <Input
                      value={newLanguage}
                      onChange={(e) => setNewLanguage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addLanguage())}
                      className={inputStyle + " flex-1"}
                      placeholder="Ex: Inglês"
                    />
                    <Select value={newLanguageLevel} onValueChange={setNewLanguageLevel}>
                      <SelectTrigger className="w-32 h-9 text-xs bg-gray-50 border-gray-200">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Básico">Básico</SelectItem>
                        <SelectItem value="Intermediário">Intermediário</SelectItem>
                        <SelectItem value="Avançado">Avançado</SelectItem>
                        <SelectItem value="Fluente">Fluente</SelectItem>
                        <SelectItem value="Nativo">Nativo</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addLanguage}
                      className="h-9 px-3"
                    >
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(formData.languages || []).map((lang, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs py-1 px-2 bg-wedo-purple/10 text-wedo-purple border border-wedo-purple/30">
                        {lang.language} ({lang.level})
                        <button
                          onClick={() => removeLanguage(idx)}
                          className="ml-1.5 text-wedo-purple hover:text-status-error"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </section>

              </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700 shrink-0">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar Alterações
              </>
            )}
          </Button>
        </div>
      </div>

      {showImportQuestionsModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 flex items-center justify-center z-[60] p-4">
          <div className="bg-white dark:bg-gray-800 rounded-md max-w-lg w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4 text-status-warning" />
                <h3 className="text-base-ui font-semibold text-gray-950">Importar Perguntas Padrão</h3>
              </div>
              <button
                onClick={() => setShowImportQuestionsModal(false)}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5">
              {isLoadingDefaultQuestions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-status-warning" />
                  <span className="ml-2 text-sm text-gray-600">Carregando perguntas...</span>
                </div>
              ) : companyDefaultQuestions.length === 0 ? (
                <div className="text-center py-8">
                  <HelpCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">Nenhuma pergunta padrão encontrada.</p>
                  <p className="text-xs text-gray-400 mt-1">Configure perguntas padrão nas Configurações da empresa.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {companyDefaultQuestions.map((q) => (
                    <label
                      key={q.id}
                      className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                        selectedDefaultQuestions.has(q.id)
                          ? 'bg-status-warning/10 border-status-warning/30'
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="mt-0.5">
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                          selectedDefaultQuestions.has(q.id)
                            ? 'bg-status-warning border-status-warning/30'
                            : 'border-gray-300'
                        }`}>
                          {selectedDefaultQuestions.has(q.id) && (
                            <Check className="w-3.5 h-3.5 text-white" />
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={selectedDefaultQuestions.has(q.id)}
                          onChange={() => toggleQuestionSelection(q.id)}
                          className="sr-only"
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-800">{q.question_text}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <Badge variant="outline" className="text-micro bg-gray-50 text-gray-600 border-gray-200">
                            {getCategoryLabel(q.category)}
                          </Badge>
                          <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30">
                            {q.question_type === 'yes_no' ? 'Sim/Não' : 
                             q.question_type === 'single_choice' ? 'Escolha única' : 
                             q.question_type === 'multiple_choice' ? 'Múltipla escolha' : 
                             q.question_type === 'scale' ? 'Escala' : 'Texto'}
                          </Badge>
                          {q.is_required && (
                            <Badge variant="outline" className="text-micro bg-status-error/10 text-status-error border-status-error/30">
                              Obrigatória
                            </Badge>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-between px-5 py-4 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
              <p className="text-xs text-gray-500">
                {selectedDefaultQuestions.size} pergunta(s) selecionada(s)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowImportQuestionsModal(false)}
                  className="h-9 px-4"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={importSelectedQuestions}
                  disabled={selectedDefaultQuestions.size === 0}
                  className="h-9 px-4 bg-status-warning hover:bg-status-warning text-white"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  Importar ({selectedDefaultQuestions.size})
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
