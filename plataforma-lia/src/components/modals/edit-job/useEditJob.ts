"use client"

import { useState, useEffect } from "react"
import { toast } from "sonner"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { useCompanyLiaInstructions } from "@/hooks/company/use-company-lia-instructions"
import { liaApi, type JobVacancy } from "@/services/lia-api"
import type { CompanyBenefit } from "@/types/benefits"
import { toCompanyBenefit } from "@/types/benefits"
import {
  type Job,
  type InterviewStage,
  type PipelineTemplate,
  type CompanyDefaultQuestion,
} from "./edit-job.types"
import { applyPipelineTemplateCore } from "./apply-pipeline-template"
import type { Job as PageJob } from "@/components/jobs/jobsPageTypes"

interface UseEditJobProps {
  isOpen: boolean
  job: PageJob | null
  onSave: (jobId: string, updates: Partial<JobVacancy>) => Promise<void>
  onClose: () => void
}

export function useEditJob({ isOpen, job: rawJob, onSave, onClose }: UseEditJobProps) {
  const job = rawJob as Job | null
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
  const [activeCompensationPolicies, setActiveCompensationPolicies] = useState<{id: string; name: string; policy_type?: string}[]>([])

  useEffect(() => {
    if (isOpen) {
      liaApi.listDepartments().then(setCompanyDepartments).catch(() => setCompanyDepartments([]))
      liaApi.listBenefits().then(setCompanyBenefits).catch(() => setCompanyBenefits([]))
      fetch('/api/backend-proxy/company/compensation-policies/')
        .then(r => r.ok ? r.json() : { items: [] })
        .then(d => setActiveCompensationPolicies((d.items || []).filter((p: {is_active: boolean}) => p.is_active)))
        .catch(() => setActiveCompensationPolicies([]))
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
        seniority: job.seniority,
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
        compensation_policy_id: job.compensation_policy_id || undefined,
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
        screeningQuestions: job.screeningQuestions ? job.screeningQuestions.map((q: { id?: string; text?: string; question?: string; category?: string; type?: string; weight?: number; is_eliminatory?: boolean; expected_answer?: string }) => ({
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


  // 3.4: pre-select highlighted company benefits when job has no existing benefits
  useEffect(() => {
    if (companyBenefits.length > 0 && isOpen && job && !(job.benefits && (job.benefits as unknown[]).length > 0)) {
      const preSelected = companyBenefits
        .filter(b => b.is_highlighted)
        .map(b => ({ id: b.id, name: b.name }))
      if (preSelected.length > 0) {
        setFormData(prev =>
          !prev.benefits?.length ? { ...prev, benefits: preSelected } : prev
        )
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyBenefits, isOpen])

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
    } finally {
      setIsLoadingTemplates(false)
    }
  }

  const applyPipelineTemplate = async (templateId: string): Promise<void> => {
    const template = pipelineTemplates.find(t => t.id === templateId)
    const vacancyId = job?.backendId || job?.jobId
    const result = await applyPipelineTemplateCore(
      { vacancyId, template },
      templateId,
    )
    if (result.mode === 'error') {
      toast.error(result.message)
      return
    }
    setFormData(prev => ({ ...prev, interviewStages: result.stages }))
    setSelectedTemplateId(templateId)
    if (result.mode === 'persisted') {
      toast.success(`Template "${result.templateName}" aplicado e salvo`)
    } else {
      toast.success(`Template "${result.templateName}" aplicado — salve a vaga para confirmar`)
    }
  }


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

  const updateInterviewStage = (index: number, field: string, value: string | number | boolean) => {
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
        seniority_level: formData.seniority,
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
        compensation_policy_id: formData.compensation_policy_id || undefined,
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
          ? formData.interviewStages.map(s => s.stageName).filter((s): s is string => s !== undefined)
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
        })) as JobVacancy['screening_questions'],
        eligibility_questions: formData.eligibilityQuestions as JobVacancy['eligibility_questions'],
        confidentiality_config: formData.confidentialityConfig as JobVacancy['confidentiality_config'],
      }

      Object.keys(updates).forEach(key => {
        if (updates[key as keyof typeof updates] === undefined) {
          delete updates[key as keyof typeof updates]
        }
      })

      await onSave(job!.backendId || job!.jobId, updates)

      // Sync wsi_skills with screening_config for interview question generation
      const wsiSkillsToSync: string[] = []

      // Add technical requirements to wsi_skills
      if (formData.technicalRequirements && formData.technicalRequirements.length > 0) {
        formData.technicalRequirements.forEach(req => {
          if (req.technology) wsiSkillsToSync.push(req.technology as string)
        })
      }

      // Add behavioral competencies to wsi_skills
      if (formData.behavioralCompetencies && formData.behavioralCompetencies.length > 0) {
        formData.behavioralCompetencies.forEach(comp => {
          if (comp.competency) wsiSkillsToSync.push(comp.competency as string)
        })
      }

      // Always sync wsi_skills with screening_config (even if empty to clear stale data)
      try {
        await fetch(`/api/backend-proxy/jobs/${job!.backendId || job!.jobId}/screening-config`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            wsi_skills: wsiSkillsToSync
          }),
        })
      } catch (syncError) {
        // Don't fail the save operation if sync fails
      }

      toast.success('Vaga atualizada com sucesso!')
      onClose()
    } catch (error) {
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
      'Containers': 'bg-lia-bg-secondary text-lia-text-primary border-lia-border-default',
      'CI/CD': 'bg-wedo-magenta/10 text-wedo-magenta border-wedo-magenta/30',
      'Outros': 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle',
    }
    return colors[category] || colors['Outros']
  }

  const getWeightColor = (weight: string) => {
    const colors: Record<string, string> = {
      'Essencial': 'bg-status-error/10 text-status-error border-status-error/30',
      'Importante': 'bg-status-warning/10 text-status-warning border-status-warning/30',
      'Desejável': 'bg-status-success/10 text-status-success border-status-success/30',
    }
    return colors[weight] || 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle'
  }

  return {
    formData,
    setFormData,
    isSaving,
    newRequirement,
    setNewRequirement,
    newBenefit,
    setNewBenefit,
    newStage,
    newAccessEmail,
    setNewAccessEmail,
    newLanguage,
    setNewLanguage,
    newLanguageLevel,
    setNewLanguageLevel,
    newTechSkill,
    newTechCategory,
    newTechLevel,
    newBehavioralSkill,
    newBehavioralWeight,
    newQuestion,
    newQuestionCategory,
    newInterviewStageName,
    setNewInterviewStageName,
    newInterviewStageSLA,
    setNewInterviewStageSLA,
    newInterviewStageType,
    setNewInterviewStageType,
    companyDepartments,
    companyBenefits,
    showImportQuestionsModal,
    setShowImportQuestionsModal,
    companyDefaultQuestions,
    selectedDefaultQuestions,
    isLoadingDefaultQuestions,
    pipelineTemplates,
    isLoadingTemplates,
    selectedTemplateId,
    updateField,
    addRequirement,
    removeRequirement,
    addBenefit,
    removeBenefit,
    addStage,
    removeStage,
    addInterviewStage,
    removeInterviewStage,
    updateInterviewStage,
    addAccessEmail,
    removeAccessEmail,
    addLanguage,
    removeLanguage,
    addTechnicalSkill,
    removeTechnicalSkill,
    addBehavioralSkill,
    removeBehavioralSkill,
    addScreeningQuestion,
    removeScreeningQuestion,
    fetchCompanyDefaultQuestions,
    openImportQuestionsModal,
    toggleQuestionSelection,
    importSelectedQuestions,
    getCategoryLabel,
    getCategoryColor,
    getWeightColor,
    handleSave,
    activeCompensationPolicies,
    applyPipelineTemplate,
    fetchPipelineTemplates,
  }
}
