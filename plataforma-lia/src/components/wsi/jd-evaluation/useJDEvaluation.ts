"use client"

import { useState, useEffect } from "react"
import { FALLBACK_TECH_SKILLS, FALLBACK_BEHAV_COMPETENCIES } from "./jdFallbackConstants"

export interface JDIndicator {
  label: string
  count?: number
  status: "sufficient" | "partial" | "insufficient"
  minimum?: number
  dimension?: string
  weight?: number
  earned?: number
  detail?: string
}

export interface JDEvaluationData {
  score: number
  max_score: number
  band?: string
  band_label?: string
  indicators: JDIndicator[]
  lia_suggestion: string
  can_generate: boolean
  details: {
    responsibilities_count: number
    technical_skills_count: number
    behavioral_competencies_count: number
    seniority_defined: boolean
    has_description: boolean
  }
}

export interface EnrichedJD {
  description?: string
  responsibilities?: string[]
  technical_skills?: string[]
  behavioral_competencies?: string[]
  generated_jd_text?: string
  updated_at?: string
}

export interface JDEvaluationPanelProps {
  jobTitle: string
  responsibilities: string[]
  technicalSkills: string[]
  behavioralCompetencies: string[]
  seniority?: string
  department?: string
  description?: string
  hasQuestions: boolean
  onGenerateQuestions?: () => void
  onEditJD?: () => void
  onSaveJDInline?: (updates: { description?: string; requirements?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[] }) => Promise<void>
  onSaveEnrichedJD?: (enrichedJd: EnrichedJD) => Promise<void>
  onUpdateOfficialJD?: (updates: { description?: string; requirements?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[] }) => Promise<void>
  onUpdateJobDescription?: (jdText: string) => Promise<void>
  enrichedJd?: EnrichedJD
  isGenerating?: boolean
  className?: string
  companyId?: string
  companyName?: string
  companyDescription?: string
  companyIndustry?: string
  benefits?: string[]
  interviewStages?: string[]
}

export function useJDEvaluation(props: {
  jobTitle: string
  responsibilities: string[]
  technicalSkills: string[]
  behavioralCompetencies: string[]
  seniority?: string
  department?: string
  description?: string
  hasQuestions: boolean
  enrichedJd?: EnrichedJD
  companyId?: string
  companyName?: string
  companyDescription?: string
  companyIndustry?: string
  benefits?: string[]
  interviewStages?: string[]
  onSaveJDInline?: JDEvaluationPanelProps['onSaveJDInline']
  onSaveEnrichedJD?: JDEvaluationPanelProps['onSaveEnrichedJD']
  onUpdateOfficialJD?: JDEvaluationPanelProps['onUpdateOfficialJD']
  onUpdateJobDescription?: JDEvaluationPanelProps['onUpdateJobDescription']
}) {
  const { jobTitle, responsibilities, technicalSkills, behavioralCompetencies, seniority, department, description, hasQuestions, enrichedJd, companyId, companyName, companyDescription, companyIndustry, benefits = [], interviewStages = [], onSaveJDInline, onSaveEnrichedJD, onUpdateOfficialJD, onUpdateJobDescription } = props

  const [isExpanded, setIsExpanded] = useState(true)
  const [evaluation, setEvaluation] = useState<JDEvaluationData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editDescription, setEditDescription] = useState(description || '')
  const [editResponsibilities, setEditResponsibilities] = useState<string[]>(responsibilities)
  const [editTechSkills, setEditTechSkills] = useState<string[]>(technicalSkills)
  const [editBehavCompetencies, setEditBehavCompetencies] = useState<string[]>(behavioralCompetencies)
  const [isSavingInline, setIsSavingInline] = useState(false)
  const [newItem, setNewItem] = useState('')
  const [editingField, setEditingField] = useState<string | null>(null)
  const [saveError, setSaveError] = useState(false)
  const [aiTechSuggestions, setAiTechSuggestions] = useState<{skill: string, confidence: number}[]>([])
  const [aiBehavSuggestions, setAiBehavSuggestions] = useState<{name: string, key: string}[]>([])
  const [isLoadingTechSuggestions, setIsLoadingTechSuggestions] = useState(false)
  const [isLoadingBehavSuggestions, setIsLoadingBehavSuggestions] = useState(false)
  const [generatedJD, setGeneratedJD] = useState<{full_description: string, sections: Record<string, string>, summary: string, tags: string[]} | null>(null)
  const [isGeneratingJD, setIsGeneratingJD] = useState(false)
  const [copiedJD, setCopiedJD] = useState(false)
  const [isSavingDefinitive, setIsSavingDefinitive] = useState(false)
  const [isSavingWithJD, setIsSavingWithJD] = useState(false)
  const [showFullDescription, setShowFullDescription] = useState(false)
  const [jdTypedMessage, setJdTypedMessage] = useState('')
  const [jdDynamicMessage, setJdDynamicMessage] = useState('')
  const [jdGenerationStep, setJdGenerationStep] = useState(0)
  const [jdGenerationError, setJdGenerationError] = useState<string | null>(null)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchEvaluation() }, [jobTitle, responsibilities.length, technicalSkills.length, behavioralCompetencies.length])

  useEffect(() => {
    if (!isEditing) {
      if (enrichedJd) {
        setEditDescription(enrichedJd.description || description || '')
        setEditResponsibilities(enrichedJd.responsibilities || responsibilities)
        setEditTechSkills(enrichedJd.technical_skills || technicalSkills)
        setEditBehavCompetencies(enrichedJd.behavioral_competencies || behavioralCompetencies)
      } else {
        setEditDescription(description || '')
        setEditResponsibilities(responsibilities)
        setEditTechSkills(technicalSkills)
        setEditBehavCompetencies(behavioralCompetencies)
      }
    }
  }, [description, responsibilities, technicalSkills, behavioralCompetencies, isEditing, enrichedJd])

  useEffect(() => {
    if (!isEditing) {
      setAiTechSuggestions([]); setAiBehavSuggestions([]); setGeneratedJD(null)
      setIsLoadingTechSuggestions(false); setIsLoadingBehavSuggestions(false)
      setIsGeneratingJD(false); setCopiedJD(false)
    }
  }, [isEditing])

  useEffect(() => {
    if (!jdDynamicMessage) return
    let i = 0
    setJdTypedMessage('')
    const interval = setInterval(() => {
      setJdTypedMessage(jdDynamicMessage.slice(0, i + 1))
      i++
      if (i >= jdDynamicMessage.length) clearInterval(interval)
    }, 25)
    return () => clearInterval(interval)
  }, [jdDynamicMessage])

  const fetchTechSuggestions = async () => {
    setIsLoadingTechSuggestions(true)
    try {
      const response = await fetch("/api/backend-proxy/skills-catalog/wizard/suggest-skills", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId || "", job_title: jobTitle, seniority: seniority || undefined, department: department || undefined, include_company_catalog: true, limit: 10 })
      })
      const data = await response.json()
      if (data.technical_skills && data.technical_skills.length > 0) {
        setAiTechSuggestions(data.technical_skills.map((s: {skill: string; confidence: number}) => ({ skill: s.skill, confidence: s.confidence })).filter((s: {skill: string}) => !editTechSkills.includes(s.skill)))
      } else {
        setAiTechSuggestions(FALLBACK_TECH_SKILLS.filter(s => !editTechSkills.includes(s)).map(s => ({ skill: s, confidence: 0.7 })))
      }
    } catch { setAiTechSuggestions(FALLBACK_TECH_SKILLS.filter(s => !editTechSkills.includes(s)).map(s => ({ skill: s, confidence: 0.7 }))) }
    finally { setIsLoadingTechSuggestions(false) }
  }

  const fetchBehavSuggestions = async () => {
    setIsLoadingBehavSuggestions(true)
    try {
      const response = await fetch("/api/backend-proxy/skills-catalog/wizard/suggest-skills", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId || "", job_title: jobTitle, seniority: seniority || undefined, department: department || undefined, include_company_catalog: true, limit: 10 })
      })
      const data = await response.json()
      if (data.behavioral_competencies && data.behavioral_competencies.length > 0) {
        setAiBehavSuggestions(data.behavioral_competencies.map((c: {name: string; key: string}) => ({ name: c.name, key: c.key })).filter((c: {name: string}) => !editBehavCompetencies.includes(c.name)))
      } else {
        setAiBehavSuggestions(FALLBACK_BEHAV_COMPETENCIES.filter(c => !editBehavCompetencies.includes(c.name)))
      }
    } catch { setAiBehavSuggestions(FALLBACK_BEHAV_COMPETENCIES.filter(c => !editBehavCompetencies.includes(c.name))) }
    finally { setIsLoadingBehavSuggestions(false) }
  }

  const generateJD = async () => {
    setIsGeneratingJD(true); setJdGenerationStep(1)
    setJdGenerationError(null)
    setJdDynamicMessage('Analisando dados da vaga e competências mapeadas...')
    try {
      await new Promise(r => setTimeout(r, 1500)); setJdGenerationStep(2)
      setJdDynamicMessage('Estruturando seções da descrição do cargo...')
      await new Promise(r => setTimeout(r, 1200)); setJdGenerationStep(3)
      setJdDynamicMessage('Gerando descrição com base na metodologia WSI...')
      const response = await fetch("/api/backend-proxy/jd/generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_title: jobTitle, department: department || undefined, seniority: seniority || undefined, description: editDescription || undefined, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, company_id: companyId || "", company_name: companyName || undefined, company_description: companyDescription || undefined, company_industry: companyIndustry || undefined, benefits: benefits.length > 0 ? benefits : undefined, interview_stages: interviewStages.length > 0 ? interviewStages : undefined })
      })
      if (!response.ok) {
        let msg = 'Não consegui gerar a descrição agora. Tente novamente em instantes.'
        if (response.status === 401 || response.status === 403) {
          msg = 'Sua sessão expirou. Recarregue a página e tente novamente.'
        } else if (response.status === 422) {
          msg = 'Faltam dados na vaga para gerar a descrição. Preencha responsabilidades e competências antes de tentar novamente.'
        }
        setJdGenerationError(msg)
        setJdDynamicMessage('')
        return
      }
      const data = await response.json().catch(() => null) as { success?: boolean; full_description?: string; sections?: Record<string, string>; tags?: string[] } | null
      if (data && (data.success || data.full_description)) {
        setJdGenerationStep(4); setJdDynamicMessage('Descrição gerada com sucesso!')
        setGeneratedJD({ full_description: data.full_description || '', sections: data.sections || {}, summary: '', tags: data.tags || [] })
      } else {
        setJdGenerationError('Não consegui gerar a descrição agora. Tente novamente em instantes.')
        setJdDynamicMessage('')
      }
    } catch {
      setJdGenerationError('Falha de conexão ao gerar a descrição. Verifique sua internet e tente novamente.')
      setJdDynamicMessage('')
    }
    finally { setIsGeneratingJD(false) }
  }

  const handleCopyJD = async () => {
    if (generatedJD?.full_description) {
      try { await navigator.clipboard.writeText(generatedJD.full_description); setCopiedJD(true); setTimeout(() => setCopiedJD(false), 2000) } catch {}
    }
  }

  const fetchEvaluation = async (overrides?: { responsibilities?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[]; description?: string }) => {
    const evalResp = overrides?.responsibilities ?? responsibilities
    const evalTech = overrides?.technicalSkills ?? technicalSkills
    const evalBehav = overrides?.behavioralCompetencies ?? behavioralCompetencies
    const evalDesc = overrides?.description ?? description
    if (!jobTitle) return
    setIsLoading(true)
    try {
      const response = await fetch("/api/backend-proxy/wsi/jd-evaluate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_title: jobTitle, responsibilities: evalResp, technical_skills: evalTech, behavioral_competencies: evalBehav, seniority: seniority || null, department: department || null, description: evalDesc || null }) })

      if (response.status === 422) {
        const detail = await response.json()
        // Proxy normalizes FastAPI { detail: {...} } → flat shape; guard against edge cases
        // Backend may surface the suggestion as lia_suggestion or message field
        const suggestion = (typeof detail.lia_suggestion === 'string' && detail.lia_suggestion)
          ? detail.lia_suggestion
          : (typeof detail.message === 'string' && detail.message)
            ? detail.message
            : 'JD com qualidade insuficiente para geração de perguntas WSI.'
        setEvaluation({
          score: typeof detail.score === 'number' ? detail.score : 0,
          max_score: typeof detail.max_score === 'number' ? detail.max_score : 100,
          band: typeof detail.band === 'string' ? detail.band : 'critico',
          band_label: typeof detail.band_label === 'string' ? detail.band_label : 'Crítico',
          indicators: Array.isArray(detail.indicators) ? detail.indicators : [],
          lia_suggestion: suggestion,
          can_generate: false,
          details: detail.details ?? { responsibilities_count: evalResp.length, technical_skills_count: evalTech.length, behavioral_competencies_count: evalBehav.length, seniority_defined: !!seniority, has_description: !!evalDesc },
        })
        return
      }

      if (!response.ok) {
        console.error('[fetchEvaluation] backend error:', response.status)
        setEvaluation(null)
        return
      }

      const data = await response.json()
      if (data.success) {
        setEvaluation(data)
      } else {
        setEvaluation(null)
      }
    } catch (err) {
      console.error('[fetchEvaluation] network/proxy error:', err)
      setEvaluation(null)
    } finally { setIsLoading(false) }
  }

  const handleSaveRascunho = async () => {
    setIsSavingInline(true); setSaveError(false)
    try {
      const enrichedData: EnrichedJD = { description: editDescription, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, generated_jd_text: generatedJD?.full_description || undefined, updated_at: new Date().toISOString() }
      if (onSaveEnrichedJD) { await onSaveEnrichedJD(enrichedData) }
      else if (onSaveJDInline) { await onSaveJDInline({ description: editDescription, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }) }
      setIsEditing(false)
    } catch { setSaveError(true) } finally { setIsSavingInline(false) }
  }

  const handleSaveDefinitiva = async () => {
    setIsSavingDefinitive(true); setSaveError(false)
    try {
      const enrichedData: EnrichedJD = { description: editDescription, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, generated_jd_text: generatedJD?.full_description || undefined, updated_at: new Date().toISOString() }
      if (onSaveEnrichedJD) { await onSaveEnrichedJD(enrichedData) }
      if (onUpdateOfficialJD) { await onUpdateOfficialJD({ description: editDescription, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }) }
      else if (onSaveJDInline) { await onSaveJDInline({ description: editDescription, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }) }
      setIsEditing(false)
      await fetchEvaluation({ responsibilities: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies, description: editDescription })
    } catch { setSaveError(true) } finally { setIsSavingDefinitive(false) }
  }

  const handleSaveAndUpdateJD = async () => {
    if (!generatedJD?.full_description) return
    setIsSavingWithJD(true); setSaveError(false)
    try {
      const enrichedData: EnrichedJD = { description: editDescription, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, generated_jd_text: generatedJD.full_description, updated_at: new Date().toISOString() }
      if (onSaveEnrichedJD) { await onSaveEnrichedJD(enrichedData) }
      if (onUpdateOfficialJD) { await onUpdateOfficialJD({ description: editDescription, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }) }
      if (onUpdateJobDescription) { await onUpdateJobDescription(generatedJD.full_description) }
      setIsEditing(false)
      await fetchEvaluation({ responsibilities: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies, description: editDescription })
    } catch { setSaveError(true) } finally { setIsSavingWithJD(false) }
  }

  const handleCancel = () => {
    setIsEditing(false)
    if (enrichedJd) {
      setEditDescription(enrichedJd.description || description || ''); setEditResponsibilities(enrichedJd.responsibilities || responsibilities)
      setEditTechSkills(enrichedJd.technical_skills || technicalSkills); setEditBehavCompetencies(enrichedJd.behavioral_competencies || behavioralCompetencies)
    } else {
      setEditDescription(description || ''); setEditResponsibilities(responsibilities)
      setEditTechSkills(technicalSkills); setEditBehavCompetencies(behavioralCompetencies)
    }
    setSaveError(false)
  }

  return {
    isExpanded, setIsExpanded, evaluation, isLoading, isEditing, setIsEditing,
    editDescription, setEditDescription, editResponsibilities, setEditResponsibilities,
    editTechSkills, setEditTechSkills, editBehavCompetencies, setEditBehavCompetencies,
    isSavingInline, newItem, setNewItem, editingField, setEditingField, saveError,
    aiTechSuggestions, setAiTechSuggestions, aiBehavSuggestions, setAiBehavSuggestions,
    isLoadingTechSuggestions, isLoadingBehavSuggestions,
    generatedJD, isGeneratingJD, copiedJD, isSavingDefinitive, isSavingWithJD,
    showFullDescription, setShowFullDescription,
    jdTypedMessage, jdDynamicMessage, jdGenerationStep, jdGenerationError,
    fetchTechSuggestions, fetchBehavSuggestions, generateJD, handleCopyJD,
    fetchEvaluation, handleSaveRascunho, handleSaveDefinitiva, handleSaveAndUpdateJD, handleCancel,
  }
}
