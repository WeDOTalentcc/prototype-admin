"use client"

import { useState, useEffect } from "react"
import { useCompanyCulture } from "@/hooks/company/use-company-culture"
import { FALLBACK_TECH_SKILLS, FALLBACK_BEHAV_COMPETENCIES } from "./jdFallbackConstants"
import {
  mapJDGenerateErrorMessage,
  mapJDEvaluationErrorMessage,
} from "./jdErrorMessages"

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
  onSaveJDInline?: (updates: { description?: string; responsibilities?: string[]; requirements?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[] }) => Promise<void>
  onSaveEnrichedJD?: (enrichedJd: EnrichedJD) => Promise<void>
  onUpdateOfficialJD?: (updates: { description?: string; responsibilities?: string[]; requirements?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[] }) => Promise<void>
  onUpdateJobDescription?: (jdText: string) => Promise<void>
  onSaveDefinitiva?: (enrichedJd: EnrichedJD, updates: { description?: string; responsibilities?: string[]; requirements?: string[]; technicalSkills?: string[]; behavioralCompetencies?: string[] }) => Promise<void>
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
  onSaveDefinitiva?: JDEvaluationPanelProps['onSaveDefinitiva']
}) {
  const { jobTitle, responsibilities, technicalSkills, behavioralCompetencies, seniority, department, description, hasQuestions, enrichedJd, companyId, companyName, companyDescription, companyIndustry, benefits = [], interviewStages = [], onSaveJDInline, onSaveEnrichedJD, onUpdateOfficialJD, onUpdateJobDescription, onSaveDefinitiva } = props

  // Cultura & EVP --- carrega dados da empresa para enriquecer o JD gerado
  const { culture } = useCompanyCulture()

  const [isExpanded, setIsExpanded] = useState(true)
  const [evaluation, setEvaluation] = useState<JDEvaluationData | null>(null)
  // Bug A (Task #1165 canonical-fix): expõe motivo real do erro de avaliação
  // para o painel mostrar mensagem específica (auth/rede/servidor) em vez de
  // ficar mudo quando evaluation=null.
  const [evaluationError, setEvaluationError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)  // start loading immediately to prevent JDEvalResultsPanel flash before fetchEvaluation runs
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
  const [aiRespSuggestions, setAiRespSuggestions] = useState<string[]>([])
  const [isLoadingRespSuggestions, setIsLoadingRespSuggestions] = useState(false)
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
      setAiTechSuggestions([]); setAiBehavSuggestions([]); setAiRespSuggestions([]); setGeneratedJD(null)
      setIsLoadingTechSuggestions(false); setIsLoadingBehavSuggestions(false); setIsLoadingRespSuggestions(false)
      setIsGeneratingJD(false); setCopiedJD(false)
    }
  }, [isEditing])

  // T-1167 (Bug #1) — limpa erro "stale" de geração assim que o usuário
  // começa a corrigir os dados faltantes. Antes, a mensagem só era zerada
  // no início da próxima tentativa de generateJD, levando o recrutador a
  // pensar que ainda há erro mesmo depois de preencher resp/skills/comp.
  useEffect(() => {
    if (jdGenerationError) setJdGenerationError(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editDescription, editResponsibilities, editTechSkills, editBehavCompetencies])

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
        body: JSON.stringify({ job_title: jobTitle, seniority: seniority || undefined, department: department || undefined, include_company_catalog: true, limit: 10 })
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
        body: JSON.stringify({ job_title: jobTitle, seniority: seniority || undefined, department: department || undefined, include_company_catalog: true, limit: 10 })
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


  const fetchResponsibilitiesSuggestions = async () => {
    setIsLoadingRespSuggestions(true)
    try {
      const response = await fetch("/api/backend-proxy/jd/suggest-responsibilities", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobTitle,
          seniority: seniority || undefined,
          department: department || undefined,
          description: editDescription || undefined,
          existing_responsibilities: editResponsibilities,
        })
      })
      const data = await response.json() as { success?: boolean; responsibilities?: string[] }
      if (data.responsibilities && data.responsibilities.length > 0) {
        const existing = new Set(editResponsibilities.map(r => r.toLowerCase().trim()))
        setAiRespSuggestions(data.responsibilities.filter(r => !existing.has(r.toLowerCase().trim())))
      } else {
        setAiRespSuggestions([])
      }
    } catch { setAiRespSuggestions([]) }
    finally { setIsLoadingRespSuggestions(false) }
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
        body: JSON.stringify({ job_title: jobTitle, department: department || undefined, seniority: seniority || undefined, description: editDescription || undefined, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, company_name: companyName || undefined, company_description: companyDescription || undefined, company_industry: companyIndustry || undefined, benefits: benefits.length > 0 ? benefits : undefined, interview_stages: interviewStages.length > 0 ? interviewStages : undefined, // Cultura & EVP --- injetados quando disponíveis, campos opcionais no backend
        mission: culture?.mission || undefined, vision: culture?.vision || undefined, evp_bullets: culture?.evpBullets && culture.evpBullets.length > 0 ? culture.evpBullets : undefined })
      })
      if (!response.ok) {
        // Bug B (Task #1165 canonical-fix): preserva mensagem real do backend
        // (FairnessGuard, Pydantic) em vez de mascarar todo 422 como "faltam dados".
        const errPayload = await response.json().catch(() => null)
        const msg = mapJDGenerateErrorMessage(response.status, errPayload)
        console.error('[generateJD] backend error', response.status, errPayload)
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

  // T-1167 (Bug #3) — extrai responsabilidades/skills/comp.comp. do texto colado
  // em DESCRIÇÃO/SUMÁRIO usando JDParserService no backend. Antes, o recrutador
  // tinha que digitar tudo manualmente mesmo já tendo o JD completo em mãos.
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractError, setExtractError] = useState<string | null>(null)
  const extractFromText = async () => {
    if (!editDescription || editDescription.trim().length < 50) {
      setExtractError('Cole um JD com pelo menos 50 caracteres em DESCRIÇÃO / SUMÁRIO.')
      return
    }
    setIsExtracting(true); setExtractError(null)
    try {
      const response = await fetch('/api/backend-proxy/jd/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: editDescription }),
      })
      if (!response.ok) {
        const errPayload = await response.json().catch(() => null) as { detail?: { message?: string } | string; message?: string } | null
        const detail = errPayload?.detail
        const msg = typeof detail === 'string' ? detail
          : (detail && typeof detail === 'object' && typeof detail.message === 'string') ? detail.message
          : typeof errPayload?.message === 'string' ? errPayload.message
          : `Falha ao extrair (status ${response.status}).`
        setExtractError(msg)
        return
      }
      const data = await response.json() as { responsibilities?: string[]; technical_skills?: string[]; behavioral_competencies?: string[] }
      // Merge sem duplicar — preserva o que o recrutador já tinha digitado.
      const mergeUnique = (current: string[], incoming: string[] | undefined) => {
        if (!incoming || incoming.length === 0) return current
        const seen = new Set(current.map(s => s.toLowerCase().trim()))
        const merged = [...current]
        for (const item of incoming) {
          const k = item.toLowerCase().trim()
          if (k && !seen.has(k)) { seen.add(k); merged.push(item) }
        }
        return merged
      }
      setEditResponsibilities(prev => mergeUnique(prev, data.responsibilities))
      setEditTechSkills(prev => mergeUnique(prev, data.technical_skills))
      setEditBehavCompetencies(prev => mergeUnique(prev, data.behavioral_competencies))
    } catch (err) {
      console.error('[extractFromText] network error:', err)
      setExtractError('Falha de conexão ao extrair os campos.')
    } finally { setIsExtracting(false) }
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
    if (!jobTitle) { setIsLoading(false); return }
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
        // Bug A (Task #1165 canonical-fix): discrimina auth (401/403) vs servidor (5xx)
        // em vez de colapsar tudo num setEvaluation(null) silencioso.
        const errBody = await response.text().catch(() => '')
        const msg = mapJDEvaluationErrorMessage(response.status)
        console.error('[fetchEvaluation] backend error', response.status, errBody.slice(0, 300))
        setEvaluationError(msg)
        setEvaluation(null)
        return
      }

      const data = await response.json()
      if (data.success) {
        setEvaluationError(null)
        setEvaluation(data)
      } else {
        console.error('[fetchEvaluation] backend returned success=false', data)
        setEvaluationError('Não foi possível avaliar a descrição agora. Tente novamente.')
        setEvaluation(null)
      }
    } catch (err) {
      console.error('[fetchEvaluation] network/proxy error:', err)
      setEvaluationError(mapJDEvaluationErrorMessage("network"))
      setEvaluation(null)
    } finally { setIsLoading(false) }
  }

  const handleSaveRascunho = async () => {
    setIsSavingInline(true); setSaveError(false)
    try {
      const enrichedData: EnrichedJD = { description: editDescription, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, generated_jd_text: generatedJD?.full_description ?? enrichedJd?.generated_jd_text ?? undefined, updated_at: new Date().toISOString() }
      if (onSaveEnrichedJD) { await onSaveEnrichedJD(enrichedData) }
      else if (onSaveJDInline) { await onSaveJDInline({ description: editDescription, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }) }
      setIsEditing(false)
    } catch { setSaveError(true) } finally { setIsSavingInline(false) }
  }

  const handleSaveDefinitiva = async () => {
    setIsSavingDefinitive(true); setSaveError(false)
    try {
      const enrichedData: EnrichedJD = { description: editDescription, responsibilities: editResponsibilities, technical_skills: editTechSkills, behavioral_competencies: editBehavCompetencies, generated_jd_text: generatedJD?.full_description ?? enrichedJd?.generated_jd_text ?? undefined, updated_at: new Date().toISOString() }
      const officialUpdates = { description: editDescription, responsibilities: editResponsibilities, requirements: editResponsibilities, technicalSkills: editTechSkills, behavioralCompetencies: editBehavCompetencies }
      if (onSaveDefinitiva) {
        // P1-1: 1 PUT atômico com enriched_jd + campos canônicos
        await onSaveDefinitiva(enrichedData, officialUpdates)
      } else {
        // Fallback: 2 PUTs independentes (legado)
        if (onSaveEnrichedJD) { await onSaveEnrichedJD(enrichedData) }
        if (onUpdateOfficialJD) { await onUpdateOfficialJD(officialUpdates) }
        else if (onSaveJDInline) { await onSaveJDInline(officialUpdates) }
      }
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
    isExpanded, setIsExpanded, evaluation, evaluationError, isLoading, isEditing, setIsEditing,
    editDescription, setEditDescription, editResponsibilities, setEditResponsibilities,
    editTechSkills, setEditTechSkills, editBehavCompetencies, setEditBehavCompetencies,
    isSavingInline, newItem, setNewItem, editingField, setEditingField, saveError,
    aiTechSuggestions, setAiTechSuggestions, aiBehavSuggestions, setAiBehavSuggestions,
    isLoadingTechSuggestions, isLoadingBehavSuggestions, aiRespSuggestions, setAiRespSuggestions, isLoadingRespSuggestions,
    generatedJD, isGeneratingJD, copiedJD, isSavingDefinitive, isSavingWithJD,
    showFullDescription, setShowFullDescription,
    jdTypedMessage, jdDynamicMessage, jdGenerationStep, jdGenerationError,
    fetchTechSuggestions, fetchBehavSuggestions, fetchResponsibilitiesSuggestions, generateJD, handleCopyJD,
    fetchEvaluation, handleSaveRascunho, handleSaveDefinitiva, handleSaveAndUpdateJD, handleCancel,
    // T-1167 (Bug #3) — extração de campos do JD colado
    isExtracting, extractError, extractFromText,
  }
}
