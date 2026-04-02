"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  FileText,
  Brain,
  CheckCircle, XCircle,
  Code, Users,
  Loader2,
  CheckCircle2,
  Plus,
  Check, Copy, ArrowRight, Save, X,
  ListChecks,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { JDEvaluationHeader } from "./jd-evaluation/JDEvaluationHeader"
import { JDArrayEditor } from "./jd-evaluation/JDArrayEditor"
import { JDGenerationSection } from "./jd-evaluation/JDGenerationSection"
import { FALLBACK_TECH_SKILLS, FALLBACK_BEHAV_COMPETENCIES } from "./jd-evaluation/jdFallbackConstants"

interface JDIndicator {
  label: string
  count?: number
  status: "sufficient" | "partial" | "insufficient"
  minimum?: number
  dimension?: string
  weight?: number
  earned?: number
  detail?: string
}

interface JDEvaluationData {
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

interface EnrichedJD {
  description?: string
  responsibilities?: string[]
  technical_skills?: string[]
  behavioral_competencies?: string[]
  generated_jd_text?: string
  updated_at?: string
}

interface JDEvaluationPanelProps {
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

export function JDEvaluationPanel({
  jobTitle,
  responsibilities,
  technicalSkills,
  behavioralCompetencies,
  seniority,
  department,
  description,
  hasQuestions,
  onGenerateQuestions,
  onEditJD,
  onSaveJDInline,
  onSaveEnrichedJD,
  onUpdateOfficialJD,
  onUpdateJobDescription,
  enrichedJd,
  isGenerating = false,
  className,
  companyId,
  companyName,
  companyDescription,
  companyIndustry,
  benefits = [],
  interviewStages = []
}: JDEvaluationPanelProps) {
  const [isExpanded, setIsExpanded] = useState(!hasQuestions)
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

  useEffect(() => {
    fetchEvaluation()
  }, [jobTitle, responsibilities.length, technicalSkills.length, behavioralCompetencies.length])

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
    setIsExpanded(!hasQuestions)
  }, [hasQuestions])

  useEffect(() => {
    if (!isEditing) {
      setAiTechSuggestions([])
      setAiBehavSuggestions([])
      setGeneratedJD(null)
      setIsLoadingTechSuggestions(false)
      setIsLoadingBehavSuggestions(false)
      setIsGeneratingJD(false)
      setCopiedJD(false)
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
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId || "default",
          job_title: jobTitle,
          seniority: seniority || undefined,
          department: department || undefined,
          include_company_catalog: true,
          limit: 10
        })
      })
      const data = await response.json()
      if (data.technical_skills && data.technical_skills.length > 0) {
        const filtered = data.technical_skills
          .map((s: {skill: string; confidence: number}) => ({ skill: s.skill, confidence: s.confidence }))
          .filter((s: {skill: string}) => !editTechSkills.includes(s.skill))
        setAiTechSuggestions(filtered)
      } else {
        const filtered = FALLBACK_TECH_SKILLS
          .filter(s => !editTechSkills.includes(s))
          .map(s => ({ skill: s, confidence: 0.7 }))
        setAiTechSuggestions(filtered)
      }
    } catch (error) {
      const filtered = FALLBACK_TECH_SKILLS
        .filter(s => !editTechSkills.includes(s))
        .map(s => ({ skill: s, confidence: 0.7 }))
      setAiTechSuggestions(filtered)
    } finally {
      setIsLoadingTechSuggestions(false)
    }
  }

  const fetchBehavSuggestions = async () => {
    setIsLoadingBehavSuggestions(true)
    try {
      const response = await fetch("/api/backend-proxy/skills-catalog/wizard/suggest-skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId || "default",
          job_title: jobTitle,
          seniority: seniority || undefined,
          department: department || undefined,
          include_company_catalog: true,
          limit: 10
        })
      })
      const data = await response.json()
      if (data.behavioral_competencies && data.behavioral_competencies.length > 0) {
        const filtered = data.behavioral_competencies
          .map((c: {name: string; key: string}) => ({ name: c.name, key: c.key }))
          .filter((c: {name: string}) => !editBehavCompetencies.includes(c.name))
        setAiBehavSuggestions(filtered)
      } else {
        const filtered = FALLBACK_BEHAV_COMPETENCIES
          .filter(c => !editBehavCompetencies.includes(c.name))
        setAiBehavSuggestions(filtered)
      }
    } catch (error) {
      const filtered = FALLBACK_BEHAV_COMPETENCIES
        .filter(c => !editBehavCompetencies.includes(c.name))
      setAiBehavSuggestions(filtered)
    } finally {
      setIsLoadingBehavSuggestions(false)
    }
  }

  const generateJD = async () => {
    setIsGeneratingJD(true)
    setJdGenerationStep(1)
    setJdDynamicMessage('Analisando dados da vaga e competências mapeadas...')

    try {
      await new Promise(r => setTimeout(r, 1500))
      setJdGenerationStep(2)
      setJdDynamicMessage('Estruturando seções da descrição do cargo...')

      await new Promise(r => setTimeout(r, 1200))
      setJdGenerationStep(3)
      setJdDynamicMessage('Gerando descrição com base na metodologia WSI...')

      const response = await fetch("/api/backend-proxy/jd/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobTitle,
          department: department || undefined,
          seniority: seniority || undefined,
          description: editDescription || undefined,
          responsibilities: editResponsibilities,
          technical_skills: editTechSkills,
          behavioral_competencies: editBehavCompetencies,
          company_id: companyId || "default",
          company_name: companyName || undefined,
          company_description: companyDescription || undefined,
          company_industry: companyIndustry || undefined,
          benefits: benefits.length > 0 ? benefits : undefined,
          interview_stages: interviewStages.length > 0 ? interviewStages : undefined
        })
      })
      const data = await response.json()
      if (data.success || data.full_description) {
        setJdGenerationStep(4)
        setJdDynamicMessage('Descrição gerada com sucesso!')
        setGeneratedJD({
          full_description: data.full_description || '',
          sections: data.sections || {},
          summary: '',
          tags: data.tags || []
        })
      }
    } catch (error) {
      setJdDynamicMessage('Erro ao gerar descrição. Tente novamente.')
    } finally {
      setIsGeneratingJD(false)
    }
  }

  const handleCopyJD = async () => {
    if (generatedJD?.full_description) {
      try {
        await navigator.clipboard.writeText(generatedJD.full_description)
        setCopiedJD(true)
        setTimeout(() => setCopiedJD(false), 2000)
      } catch {
      }
    }
  }

  const fetchEvaluation = async (overrides?: {
    responsibilities?: string[]
    technicalSkills?: string[]
    behavioralCompetencies?: string[]
    description?: string
  }) => {
    const evalResponsibilities = overrides?.responsibilities ?? responsibilities
    const evalTechSkills = overrides?.technicalSkills ?? technicalSkills
    const evalBehavCompetencies = overrides?.behavioralCompetencies ?? behavioralCompetencies
    const evalDescription = overrides?.description ?? description

    if (!jobTitle) return
    setIsLoading(true)
    try {
      const response = await fetch("/api/backend-proxy/wsi/jd-evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobTitle,
          responsibilities: evalResponsibilities,
          technical_skills: evalTechSkills,
          behavioral_competencies: evalBehavCompetencies,
          seniority: seniority || null,
          department: department || null,
          description: evalDescription || null
        })
      })
      const data = await response.json()
      if (data.success) {
        setEvaluation(data)
      }
    } catch (error) {
      const respCount = evalResponsibilities.length
      const techCount = evalTechSkills.length
      const behavCount = evalBehavCompetencies.length
      let score = 0
      const indicators: JDIndicator[] = []

      if (respCount >= 3) { score += 30; indicators.push({ label: "Responsabilidades", count: respCount, status: "sufficient", minimum: 3 }) }
      else if (respCount >= 1) { score += 15; indicators.push({ label: "Responsabilidades", count: respCount, status: "partial", minimum: 3 }) }
      else { indicators.push({ label: "Responsabilidades", count: 0, status: "insufficient", minimum: 3 }) }

      if (techCount >= 9) { score += 30; indicators.push({ label: "Comp. Técnicas", count: techCount, status: "sufficient", minimum: 9 }) }
      else if (techCount >= 3) { score += 15; indicators.push({ label: "Comp. Técnicas", count: techCount, status: "partial", minimum: 9 }) }
      else { indicators.push({ label: "Comp. Técnicas", count: 0, status: "insufficient", minimum: 9 }) }

      if (behavCount >= 5) { score += 30; indicators.push({ label: "Comp. Comportamentais", count: behavCount, status: "sufficient", minimum: 5 }) }
      else if (behavCount >= 2) { score += 15; indicators.push({ label: "Comp. Comportamentais", count: behavCount, status: "partial", minimum: 5 }) }
      else { indicators.push({ label: "Comp. Comportamentais", count: 0, status: "insufficient", minimum: 5 }) }

      if (seniority) { score += 10; indicators.push({ label: "Senioridade", count: 1, status: "sufficient", minimum: 1 }) }
      else { indicators.push({ label: "Senioridade", count: 0, status: "insufficient", minimum: 1 }) }

      setEvaluation({
        score,
        max_score: 100,
        indicators,
        lia_suggestion: score >= 70 ? "Descrição do cargo bem estruturada para geração de perguntas WSI." : "Adicione mais informações à descrição do cargo para melhorar a qualidade das perguntas.",
        can_generate: score >= 50,
        details: {
          responsibilities_count: respCount,
          technical_skills_count: techCount,
          behavioral_competencies_count: behavCount,
          seniority_defined: !!seniority,
          has_description: !!evalDescription
        }
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveRascunho = async () => {
    setIsSavingInline(true)
    setSaveError(false)
    try {
      const enrichedData: EnrichedJD = {
        description: editDescription,
        responsibilities: editResponsibilities,
        technical_skills: editTechSkills,
        behavioral_competencies: editBehavCompetencies,
        generated_jd_text: generatedJD?.full_description || undefined,
        updated_at: new Date().toISOString(),
      }
      if (onSaveEnrichedJD) {
        await onSaveEnrichedJD(enrichedData)
      } else if (onSaveJDInline) {
        await onSaveJDInline({
          description: editDescription,
          requirements: editResponsibilities,
          technicalSkills: editTechSkills,
          behavioralCompetencies: editBehavCompetencies,
        })
      }
      setIsEditing(false)
    } catch {
      setSaveError(true)
    } finally {
      setIsSavingInline(false)
    }
  }

  const handleSaveDefinitiva = async () => {
    setIsSavingDefinitive(true)
    setSaveError(false)
    try {
      const enrichedData: EnrichedJD = {
        description: editDescription,
        responsibilities: editResponsibilities,
        technical_skills: editTechSkills,
        behavioral_competencies: editBehavCompetencies,
        generated_jd_text: generatedJD?.full_description || undefined,
        updated_at: new Date().toISOString(),
      }
      if (onSaveEnrichedJD) {
        await onSaveEnrichedJD(enrichedData)
      }
      if (onUpdateOfficialJD) {
        await onUpdateOfficialJD({
          description: editDescription,
          requirements: editResponsibilities,
          technicalSkills: editTechSkills,
          behavioralCompetencies: editBehavCompetencies,
        })
      } else if (onSaveJDInline) {
        await onSaveJDInline({
          description: editDescription,
          requirements: editResponsibilities,
          technicalSkills: editTechSkills,
          behavioralCompetencies: editBehavCompetencies,
        })
      }
      setIsEditing(false)
      await fetchEvaluation({
        responsibilities: editResponsibilities,
        technicalSkills: editTechSkills,
        behavioralCompetencies: editBehavCompetencies,
        description: editDescription,
      })
    } catch {
      setSaveError(true)
    } finally {
      setIsSavingDefinitive(false)
    }
  }

  const handleSaveAndUpdateJD = async () => {
    if (!generatedJD?.full_description) return
    setIsSavingWithJD(true)
    setSaveError(false)
    try {
      const enrichedData: EnrichedJD = {
        description: editDescription,
        responsibilities: editResponsibilities,
        technical_skills: editTechSkills,
        behavioral_competencies: editBehavCompetencies,
        generated_jd_text: generatedJD.full_description,
        updated_at: new Date().toISOString(),
      }
      if (onSaveEnrichedJD) {
        await onSaveEnrichedJD(enrichedData)
      }
      if (onUpdateOfficialJD) {
        await onUpdateOfficialJD({
          description: editDescription,
          requirements: editResponsibilities,
          technicalSkills: editTechSkills,
          behavioralCompetencies: editBehavCompetencies,
        })
      }
      if (onUpdateJobDescription) {
        await onUpdateJobDescription(generatedJD.full_description)
      }
      setIsEditing(false)
      await fetchEvaluation({
        responsibilities: editResponsibilities,
        technicalSkills: editTechSkills,
        behavioralCompetencies: editBehavCompetencies,
        description: editDescription,
      })
    } catch {
      setSaveError(true)
    } finally {
      setIsSavingWithJD(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
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
    setSaveError(false)
  }

  const score = evaluation?.score ?? 0

  // Collapsed state
  if (!isExpanded) {
    return (
      <div className={cn("mx-5 mt-4", className)}>
        <div className="border border-lia-border-subtle rounded-md overflow-hidden">
          <JDEvaluationHeader
            jobTitle={jobTitle}
            hasQuestions={hasQuestions}
            isExpanded={false}
            isEditing={isEditing}
            evaluation={evaluation}
            onToggleExpand={() => setIsExpanded(true)}
            onStartEdit={() => {
              setIsExpanded(true)
              setIsEditing(true)
            }}
            onEditJD={onEditJD}
            canEdit={!!(onSaveJDInline || onEditJD)}
            responsibilities={responsibilities}
            technicalSkills={technicalSkills}
            behavioralCompetencies={behavioralCompetencies}
            description={description}
          />
          <div className="px-4 py-2.5 border-t border-lia-border-subtle bg-lia-bg-primary">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <ListChecks className="w-3 h-3 text-lia-text-disabled" />
                Responsabilidades: {responsibilities.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Code className="w-3 h-3 text-lia-text-disabled" />
                Comp. Técnicas: {technicalSkills.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Users className="w-3 h-3 text-lia-text-disabled" />
                Comp. Comportamentais: {behavioralCompetencies.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <FileText className="w-3 h-3 text-lia-text-disabled" />
                JD: {description ? 'Sim' : 'Não'}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("mx-5 mt-4", className)}>
      <div className="border border-lia-border-subtle rounded-md overflow-hidden">
        <JDEvaluationHeader
          jobTitle={jobTitle}
          hasQuestions={hasQuestions}
          isExpanded={true}
          isEditing={isEditing}
          evaluation={null}
          onToggleExpand={() => hasQuestions && setIsExpanded(false)}
          onStartEdit={() => setIsEditing(true)}
          onEditJD={onEditJD}
          canEdit={!!(onSaveJDInline || onEditJD)}
          responsibilities={responsibilities}
          technicalSkills={technicalSkills}
          behavioralCompetencies={behavioralCompetencies}
          description={description}
        />

        <div className="p-3" role="status" aria-live="polite" aria-label="Carregando...">
          {isLoading ? (
            <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none lia-text-secondary" />
              <span className="ml-2 text-xs lia-text-secondary">Avaliando Descrição do Cargo...</span>
            </div>
          ) : evaluation ? (
            <div className="space-y-3">
              {/* Score + indicators rendered inline (already inside JDEvaluationHeader when expanded) */}
              {/* Re-render evaluation inline here since header only shows them in collapsed mode */}
              {/* BAND BADGE + SCORE ROW */}
              {(() => {
                const band = evaluation.band || (evaluation.score >= 90 ? 'excelente' : evaluation.score >= 70 ? 'bom' : evaluation.score >= 50 ? 'adequado' : evaluation.score >= 30 ? 'insuficiente' : 'critico')
                const bandLabel = evaluation.band_label || (band === 'excelente' ? 'Excelente' : band === 'bom' ? 'Bom' : band === 'adequado' ? 'Adequado' : band === 'insuficiente' ? 'Insuficiente' : 'Crítico')
                const bandColors: Record<string, string> = {
                  excelente: 'bg-status-success/10 text-status-success border-status-success/30',
                  bom: 'bg-status-success/10 text-status-success border-status-success/30',
                  adequado: 'bg-status-warning/10 text-status-warning border-status-warning/30',
                  insuficiente: 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30',
                  critico: 'bg-status-error/10 text-status-error border-status-error/30',
                }
                return (
                  <div className="flex items-center gap-3 pb-2 border-b border-lia-border-subtle">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-lia-text-primary">{evaluation.score}</span>
                      <span className="text-micro lia-text-secondary">/100</span>
                    </div>
                    <span className={cn("text-micro font-semibold px-2 py-0.5 rounded-full border", bandColors[band] || bandColors.adequado)}>
                      {bandLabel}
                    </span>
                    {band === 'critico' && (
                      <span className="text-micro text-status-error font-medium flex items-center gap-1">
                        <XCircle className="w-3 h-3" />
                        JD bloqueado — geração de perguntas desabilitada
                      </span>
                    )}
                  </div>
                )
              })()}

              {/* 9-DIMENSION GRID */}
              {evaluation.indicators.some(i => i.dimension) && (
                <div className="grid grid-cols-3 gap-1.5 pb-2 border-b border-lia-border-subtle">
                  {evaluation.indicators.map((indicator) => (
                    <div key={indicator.label} className={cn(
                      "flex items-center gap-1.5 px-2 py-1.5 rounded-md border text-micro",
                      indicator.status === 'sufficient' ? 'bg-status-success/10 border-status-success/30 dark:bg-status-success/10 dark:border-status-success/30' :
                      indicator.status === 'partial' ? 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/10 dark:border-status-warning/30' :
                      'bg-status-error/10 border-status-error/30 dark:bg-status-error/10 dark:border-status-error/30'
                    )}>
                      {indicator.status === 'sufficient' ? (
                        <CheckCircle className="w-3 h-3 text-status-success shrink-0" />
                      ) : indicator.status === 'partial' ? (
                        <Brain className="w-3 h-3 text-status-warning shrink-0" />
                      ) : (
                        <XCircle className="w-3 h-3 text-status-error shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="text-micro font-semibold lia-text-secondary uppercase tracking-wide block">{indicator.dimension}</span>
                        <span className={cn(
                          "truncate block font-medium",
                          indicator.status === 'sufficient' ? 'text-status-success' :
                          indicator.status === 'partial' ? 'text-status-warning' :
                          'text-status-error dark:text-status-error'
                        )}>{indicator.label}</span>
                      </div>
                      <span className="text-micro font-semibold text-lia-text-secondary shrink-0">
                        {indicator.earned ?? 0}/{indicator.weight ?? 0}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* COMPACT ROW (fallback) */}
              {!evaluation.indicators.some(i => i.dimension) && (
                <div className="flex items-center gap-3 pb-2 border-b border-lia-border-subtle flex-wrap">
                  {evaluation.indicators.map((indicator) => (
                    <div key={indicator.label} className="flex items-center gap-1.5">
                      <FileText className="h-3 w-3 lia-text-secondary" />
                      <span className="text-micro text-lia-text-secondary">{indicator.label}:</span>
                      <span className="text-xs font-semibold text-lia-text-primary">{indicator.count ?? 0}</span>
                      <span className={cn("w-1.5 h-1.5 rounded-full",
                        indicator.status === 'sufficient' ? 'bg-status-success' :
                        indicator.status === 'partial' ? 'bg-status-warning' : 'bg-status-error'
                      )} />
                    </div>
                  ))}
                </div>
              )}

              {/* SUGGESTION */}
              {evaluation.lia_suggestion && (
                <div className={cn(
                  "text-micro px-2.5 py-2 rounded-md border leading-relaxed",
                  evaluation.can_generate
                    ? "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary/50"
                    : "bg-status-error/10 border-status-error/30 text-status-error dark:bg-status-error/10 dark:border-status-error/30 dark:text-status-error"
                )}>
                  {evaluation.lia_suggestion}
                </div>
              )}

              {/* READ-ONLY 2-COLUMN PREVIEW */}
              {!isEditing && (
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="space-y-3">
                    <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide block">DESCRIÇÃO DO CLIENTE</span>
                    <div className="border border-lia-border-subtle rounded-md p-3 bg-lia-bg-secondary/30/30 space-y-3">

                    {description && (
                      <div>
                        <p
                          className={cn(
                            "text-xs text-lia-text-secondary leading-relaxed",
                            !showFullDescription && "line-clamp-4"
                          )}
                        >
                          {description}
                        </p>
                        {description.length > 200 && (
                          <button
                            onClick={() => setShowFullDescription(!showFullDescription)}
                            className="text-micro text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-inverse mt-1 underline"
                          >
                            {showFullDescription ? "ver menos" : "ver mais"}
                          </button>
                        )}
                      </div>
                    )}

                    {responsibilities.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Responsabilidades</span>
                        <ul className="space-y-0.5">
                          {responsibilities.map((item, idx) => (
                            <li key={`resp-${idx}`} className="flex items-start gap-1.5">
                              <span className="text-xs lia-text-secondary mt-0.5 shrink-0">•</span>
                              <span className="text-xs text-lia-text-secondary leading-relaxed">{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {technicalSkills.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Competências Técnicas</span>
                        <div className="flex flex-wrap gap-1.5">
                          {technicalSkills.map((skill) => (
                            <span key={skill} className="px-2.5 py-0.5 text-xs rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {behavioralCompetencies.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Competências Comportamentais</span>
                        <div className="flex flex-wrap gap-1.5">
                          {behavioralCompetencies.map((comp) => (
                            <span key={comp} className="px-2.5 py-0.5 text-xs rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                              {comp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    </div>
                  </div>

                  <div className="space-y-3">
                    <span className="text-xs font-semibold uppercase tracking-wide block">DESCRIÇÃO ENRIQUECIDA (LIA)</span>

                    {enrichedJd && (enrichedJd.generated_jd_text || enrichedJd.description) ? (
                      <div className="border rounded-md p-3 space-y-3/30 border-wedo-cyan/20 bg-wedo-cyan/[.02]">
                        <p className="text-xs text-lia-text-secondary leading-relaxed whitespace-pre-wrap">
                          {enrichedJd.generated_jd_text || enrichedJd.description}
                        </p>

                        {enrichedJd.updated_at && (
                          <span className="inline-block px-2.5 py-0.5 text-micro rounded-full bg-wedo-cyan/[.08]">
                            Gerado em {new Date(enrichedJd.updated_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
                          </span>
                        )}

                        {enrichedJd.responsibilities && enrichedJd.responsibilities.length > 0 && (
                          <div>
                            <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Responsabilidades</span>
                            <ul className="space-y-0.5">
                              {enrichedJd.responsibilities.map((item, idx) => (
                                <li key={`resp-${idx}`} className="flex items-start gap-1.5">
                                  <span className="text-xs mt-0.5 shrink-0 text-lia-text-secondary">•</span>
                                  <span className="text-xs text-lia-text-secondary leading-relaxed">{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {enrichedJd.technical_skills && enrichedJd.technical_skills.length > 0 && (
                          <div>
                            <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Competências Técnicas</span>
                            <div className="flex flex-wrap gap-1.5">
                              {enrichedJd.technical_skills.map((skill) => (
                                <span key={skill} className="px-2.5 py-0.5 text-xs rounded-full bg-wedo-cyan/10">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {enrichedJd.behavioral_competencies && enrichedJd.behavioral_competencies.length > 0 && (
                          <div>
                            <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Competências Comportamentais</span>
                            <div className="flex flex-wrap gap-1.5">
                              {enrichedJd.behavioral_competencies.map((comp) => (
                                <span key={comp} className="px-2.5 py-0.5 text-xs rounded-full bg-wedo-cyan/10">
                                  {comp}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="border rounded-md p-3/30 border-wedo-cyan/15 bg-wedo-cyan/[.02]">
                        <div className="flex flex-col items-center justify-center py-6">
                          <Brain className="h-8 w-8 mb-2 text-wedo-cyan opacity-40" />
                          <p className="text-xs text-lia-text-disabled text-center leading-relaxed">
                            Nenhum JD enriquecido gerado ainda.<br />
                            Clique em Editar Descrição para gerar.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* EDITING SECTION */}
              {isEditing && (
                <div className="space-y-0">
                  <div className="grid grid-cols-2 gap-4">
                    {/* LEFT COLUMN */}
                    <div className="space-y-4">
                      {/* Description textarea */}
                      <div>
                        <label className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide mb-2 block">Descrição / Sumário</label>
                        <div className="bg-lia-bg-primary rounded-md border border-lia-border-subtle p-3">
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full h-40 text-xs text-lia-text-primary border border-lia-border-subtle rounded-md p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium bg-lia-bg-secondary"
                            placeholder="Forneça uma visão geral da vaga, incluindo propósito e como contribui para a organização..."
                          />
                        </div>
                      </div>

                      {/* Responsibilities */}
                      <JDArrayEditor
                        label="Responsabilidades"
                        items={editResponsibilities}
                        onChange={setEditResponsibilities}
                        variant="list"
                        placeholder="Adicionar responsabilidade..."
                        fieldKey="responsibilities"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                      />

                      {/* Technical Skills */}
                      <JDArrayEditor
                        label="Competências Técnicas"
                        items={editTechSkills}
                        onChange={setEditTechSkills}
                        variant="tags"
                        placeholder="Adicionar competência técnica..."
                        fieldKey="techSkills"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                        aiSuggestions={aiTechSuggestions.map(s => ({ label: s.skill, key: s.skill }))}
                        isLoadingAI={isLoadingTechSuggestions}
                        onFetchAI={fetchTechSuggestions}
                        onAcceptSuggestion={(key) => {
                          if (!editTechSkills.includes(key)) {
                            setEditTechSkills(prev => [...prev, key])
                          }
                          setAiTechSuggestions(prev => prev.filter(x => x.skill !== key))
                        }}
                      />

                      {/* Behavioural Competencies */}
                      <JDArrayEditor
                        label="Competências Comportamentais"
                        items={editBehavCompetencies}
                        onChange={setEditBehavCompetencies}
                        variant="tags"
                        placeholder="Adicionar competência comportamental..."
                        fieldKey="behavCompetencies"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                        aiSuggestions={aiBehavSuggestions.map(c => ({ label: c.name, key: c.key }))}
                        isLoadingAI={isLoadingBehavSuggestions}
                        onFetchAI={fetchBehavSuggestions}
                        onAcceptSuggestion={(key) => {
                          const found = aiBehavSuggestions.find(c => c.key === key)
                          if (found && !editBehavCompetencies.includes(found.name)) {
                            setEditBehavCompetencies(prev => [...prev, found.name])
                          }
                          setAiBehavSuggestions(prev => prev.filter(x => x.key !== key))
                        }}
                      />
                    </div>

                    {/* RIGHT COLUMN — JD Generation */}
                    <JDGenerationSection
                      generatedJD={generatedJD}
                      isGeneratingJD={isGeneratingJD}
                      jdGenerationStep={jdGenerationStep}
                      jdTypedMessage={jdTypedMessage}
                      jdDynamicMessage={jdDynamicMessage}
                      copiedJD={copiedJD}
                      isSavingWithJD={isSavingWithJD}
                      onGenerate={generateJD}
                      onCopy={handleCopyJD}
                      onSaveAndUpdateJD={handleSaveAndUpdateJD}
                      showSaveAndUpdate={!!(generatedJD && onUpdateJobDescription)}
                    />
                  </div>

                  {/* BOTTOM ACTION BAR */}
                  <div className="flex items-center justify-between pt-4 mt-4 border-t border-lia-border-subtle">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
                      onClick={handleCancel}
                    >
                      Cancelar
                    </Button>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary"
                        onClick={handleSaveRascunho}
                        disabled={isSavingInline}
                      >
                        {isSavingInline ? <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" /> : <Save className="h-3 w-3 mr-1" />}
                        Salvar Rascunho
                      </Button>
                      <Button
                        size="sm"
                        className="h-7 text-micro px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={handleSaveDefinitiva}
                        disabled={isSavingDefinitive}
                      >
                        {isSavingDefinitive ? <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
                        Salvar Versão Definitiva
                      </Button>
                    </div>
                  </div>

                  {saveError && (
                    <p className="text-micro text-status-error mt-2">Erro ao salvar. Tente novamente.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-xs lia-text-secondary">Não foi possível avaliar o JD.</p>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs mt-2"
                onClick={() => fetchEvaluation()}
              >
                Tentar novamente
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default JDEvaluationPanel
