"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  FileText, ChevronUp, ChevronDown, Brain,
  CheckCircle, AlertTriangle, XCircle,
  ClipboardList, Code, Heart, Briefcase,
  Loader2, Pencil, Plus,
  Check, Copy, ArrowRight, Save, X,
  ListChecks, Users, CheckCircle2
} from "lucide-react"
import { cn } from "@/lib/utils"

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

function formatJDText(text: string): React.ReactNode {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let i = 0
  
  while (i < lines.length) {
    const line = lines[i].trim()
    
    if (!line) {
      elements.push(<div key={i} className="h-2" />)
      i++
      continue
    }
    
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={i} className="text-xs font-bold text-gray-800 dark:text-gray-200 mt-3 mb-1">
          {line.replace('### ', '')}
        </h4>
      )
    } else if (line.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="text-base-ui font-bold text-gray-900 dark:text-gray-100 mt-4 mb-1.5">
          {line.replace('## ', '')}
        </h3>
      )
    } else if (line.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">
          {line.replace('# ', '')}
        </h2>
      )
    } else if (line.startsWith('- ')) {
      elements.push(
        <div key={i} className="flex items-start gap-2 ml-1 mb-0.5">
          <span className="text-micro text-gray-400 mt-1">•</span>
          <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
            {line.replace('- ', '')}
          </span>
        </div>
      )
    } else {
      elements.push(
        <p key={i} className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed mb-1">
          {line}
        </p>
      )
    }
    i++
  }
  
  return elements
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

  const FALLBACK_TECH_SKILLS = ["JavaScript", "TypeScript", "React", "Node.js", "Python", "SQL", "Git", "Docker", "AWS", "REST APIs"]
  const FALLBACK_BEHAV_COMPETENCIES: {name: string, key: string}[] = [
    {name: "Comunicação", key: "comunicacao"},
    {name: "Trabalho em equipe", key: "trabalho_equipe"},
    {name: "Resolução de problemas", key: "resolucao_problemas"},
    {name: "Adaptabilidade", key: "adaptabilidade"},
    {name: "Liderança", key: "lideranca"},
    {name: "Pensamento crítico", key: "pensamento_critico"},
    {name: "Proatividade", key: "proatividade"},
    {name: "Organização", key: "organizacao"}
  ]

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

      // D3: mínimo ideal = 9 skills técnicas (spec WSI F8)
      if (techCount >= 9) { score += 30; indicators.push({ label: "Comp. Técnicas", count: techCount, status: "sufficient", minimum: 9 }) }
      else if (techCount >= 3) { score += 15; indicators.push({ label: "Comp. Técnicas", count: techCount, status: "partial", minimum: 9 }) }
      else { indicators.push({ label: "Comp. Técnicas", count: 0, status: "insufficient", minimum: 9 }) }

      // D4: mínimo ideal = 5 competências comportamentais (spec WSI F8)
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

  const getStatusDotColor = (status: string) => {
    switch (status) {
      case "sufficient": return "bg-status-success"
      case "partial": return "bg-status-warning"
      case "insufficient": return "bg-status-error"
      default: return "bg-gray-400"
    }
  }

  const getIndicatorIcon = (label: string) => {
    if (label.includes("Responsab")) return <ClipboardList className="h-3 w-3 text-gray-500" />
    if (label.includes("Técnica")) return <Code className="h-3 w-3 text-gray-500" />
    if (label.includes("Comportam")) return <Heart className="h-3 w-3 text-gray-500" />
    if (label.includes("Senior")) return <Briefcase className="h-3 w-3 text-gray-500" />
    return <FileText className="h-3 w-3 text-gray-500" />
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return { text: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" }
    if (score >= 70) return { text: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" }
    if (score >= 50) return { text: "text-status-warning", bg: "bg-status-warning/10", border: "border-status-warning/30" }
    if (score >= 30) return { text: "text-wedo-orange", bg: "bg-wedo-orange/10", border: "border-wedo-orange/30" }
    return { text: "text-status-error", bg: "bg-status-error/10", border: "border-status-error/30" }
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

  if (!isExpanded) {
    return (
      <div className={cn("mx-5 mt-4", className)}>
        <div className="border border-gray-200 rounded-md overflow-hidden dark:border-gray-700">
          <div
            className="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors dark:bg-gray-800 dark:hover:bg-gray-700"
            onClick={() => setIsExpanded(true)}
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              <span className="text-base-ui font-semibold text-gray-900 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                Descrição do Cargo
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                — {jobTitle}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {(onSaveJDInline || onEditJD) && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs px-3 border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  style={{minWidth: '160px'}}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (onSaveJDInline) {
                      setIsExpanded(true)
                      setIsEditing(true)
                    } else if (onEditJD) {
                      onEditJD()
                    }
                  }}
                >
                  <Pencil className="h-3 w-3 mr-1.5" />
                  Editar Descrição
                </Button>
              )}
              <ChevronDown className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            </div>
          </div>
          <div className="px-4 py-2.5 border-t border-gray-100 bg-white dark:bg-gray-800 dark:border-gray-700">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 bg-gray-50 text-micro text-gray-600 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300">
                <ListChecks className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                Responsabilidades: {responsibilities.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 bg-gray-50 text-micro text-gray-600 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300">
                <Code className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                Comp. Técnicas: {technicalSkills.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 bg-gray-50 text-micro text-gray-600 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300">
                <Users className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                Comp. Comportamentais: {behavioralCompetencies.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 bg-gray-50 text-micro text-gray-600 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300">
                <FileText className="w-3 h-3 text-gray-400 dark:text-gray-500" />
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
      <div className="border border-gray-200 rounded-md overflow-hidden dark:bg-gray-800 dark:border-gray-700">
        <div
          className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          onClick={() => hasQuestions && setIsExpanded(false)}
        >
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-gray-600" />
            <span className="text-base-ui font-semibold text-gray-900 dark:text-gray-50 font-['Open_Sans',sans-serif]">Descrição do Cargo</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">— {jobTitle}</span>
          </div>
          <div className="flex items-center gap-2">
            {!isEditing && (onSaveJDInline || onEditJD) && (
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs px-3 border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                style={{minWidth: '160px'}}
                onClick={(e) => {
                  e.stopPropagation()
                  if (onSaveJDInline) {
                    setIsEditing(true)
                  } else if (onEditJD) {
                    onEditJD()
                  }
                }}
              >
                <Pencil className="h-3 w-3 mr-1.5" />
                Editar Descrição
              </Button>
            )}
            {hasQuestions && <ChevronUp className="h-4 w-4 text-gray-500" />}
          </div>
        </div>

        <div className="p-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
              <span className="ml-2 text-xs text-gray-500">Avaliando Descrição do Cargo...</span>
            </div>
          ) : evaluation ? (
            <div className="space-y-3">
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
                  <div className="flex items-center gap-3 pb-2 border-b border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">{evaluation.score}</span>
                      <span className="text-micro text-gray-500">/100</span>
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
                <div className="grid grid-cols-3 gap-1.5 pb-2 border-b border-gray-100 dark:border-gray-700">
                  {evaluation.indicators.map((indicator, idx) => (
                    <div key={idx} className={cn(
                      "flex items-center gap-1.5 px-2 py-1.5 rounded-md border text-micro",
                      indicator.status === 'sufficient' ? 'bg-status-success/10 border-status-success/30 dark:bg-status-success/10 dark:border-status-success/30' :
                      indicator.status === 'partial' ? 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/10 dark:border-status-warning/30' :
                      'bg-status-error/10 border-status-error/30 dark:bg-status-error/10 dark:border-status-error/30'
                    )}>
                      {indicator.status === 'sufficient' ? (
                        <CheckCircle className="w-3 h-3 text-status-success shrink-0" />
                      ) : indicator.status === 'partial' ? (
                        <AlertTriangle className="w-3 h-3 text-status-warning shrink-0" />
                      ) : (
                        <XCircle className="w-3 h-3 text-status-error shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="text-micro font-semibold text-gray-500 uppercase tracking-wide block">{indicator.dimension}</span>
                        <span className={cn(
                          "truncate block font-medium",
                          indicator.status === 'sufficient' ? 'text-status-success dark:text-status-success' :
                          indicator.status === 'partial' ? 'text-status-warning dark:text-status-warning' :
                          'text-status-error dark:text-status-error'
                        )}>{indicator.label}</span>
                      </div>
                      <span className="text-micro font-semibold text-gray-600 shrink-0">
                        {indicator.earned ?? 0}/{indicator.weight ?? 0}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* COMPACT ROW (fallback for old-format indicators without dimension) */}
              {!evaluation.indicators.some(i => i.dimension) && (
                <div className="flex items-center gap-3 pb-2 border-b border-gray-100 dark:border-gray-700 flex-wrap">
                  {evaluation.indicators.map((indicator, idx) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      {getIndicatorIcon(indicator.label)}
                      <span className="text-micro text-gray-600 dark:text-gray-400">{indicator.label}:</span>
                      <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">{indicator.count ?? 0}</span>
                      <span className={cn("w-1.5 h-1.5 rounded-full", getStatusDotColor(indicator.status))} />
                    </div>
                  ))}
                </div>
              )}

              {/* SUGGESTION */}
              {evaluation.lia_suggestion && (
                <div className={cn(
                  "text-micro px-2.5 py-2 rounded-md border leading-relaxed",
                  evaluation.can_generate
                    ? "bg-gray-50 border-gray-100 text-gray-600 dark:bg-gray-800/50 dark:border-gray-700 dark:text-gray-400"
                    : "bg-status-error/10 border-status-error/30 text-status-error dark:bg-status-error/10 dark:border-status-error/30 dark:text-status-error"
                )}>
                  {evaluation.lia_suggestion}
                </div>
              )}


              {/* 2.5. READ-ONLY 2-COLUMN PREVIEW */}
              {!isEditing && (
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="space-y-3">
                    <span className="text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide block">DESCRIÇÃO DO CLIENTE</span>
                    <div className="border border-gray-100 dark:border-gray-700 rounded-md p-3 bg-gray-50/30 dark:bg-gray-800/30 space-y-3">

                    {description && (
                      <div>
                        <p
                          className={cn(
                            "text-xs text-gray-700 dark:text-gray-300 leading-relaxed",
                            !showFullDescription && "line-clamp-4"
                          )}
                          
                        >
                          {description}
                        </p>
                        {description.length > 200 && (
                          <button
                            onClick={() => setShowFullDescription(!showFullDescription)}
                            className="text-micro text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mt-1 underline"
                            
                          >
                            {showFullDescription ? "ver menos" : "ver mais"}
                          </button>
                        )}
                      </div>
                    )}

                    {responsibilities.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wide block mb-1">Responsabilidades</span>
                        <ul className="space-y-0.5">
                          {responsibilities.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-xs text-gray-400 mt-0.5 shrink-0">•</span>
                              <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed" >{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {technicalSkills.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wide block mb-1">Competências Técnicas</span>
                        <div className="flex flex-wrap gap-1.5">
                          {technicalSkills.map((skill, idx) => (
                            <span key={idx} className="px-2.5 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300" >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {behavioralCompetencies.length > 0 && (
                      <div>
                        <span className="text-micro font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wide block mb-1">Competências Comportamentais</span>
                        <div className="flex flex-wrap gap-1.5">
                          {behavioralCompetencies.map((comp, idx) => (
                            <span key={idx} className="px-2.5 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300" >
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
                      <div className="border rounded-md p-3 space-y-3 dark:bg-gray-800/30 border-wedo-cyan/20 bg-wedo-cyan/[.02]">
                        <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap" >
                          {enrichedJd.generated_jd_text || enrichedJd.description}
                        </p>

                        {enrichedJd.updated_at && (
                          <span className="inline-block px-2.5 py-0.5 text-micro rounded-full bg-wedo-cyan/[.08]" >
                            Gerado em {new Date(enrichedJd.updated_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
                          </span>
                        )}

                        {enrichedJd.responsibilities && enrichedJd.responsibilities.length > 0 && (
                          <div>
                            <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Responsabilidades</span>
                            <ul className="space-y-0.5">
                              {enrichedJd.responsibilities.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-xs mt-0.5 shrink-0 text-gray-700">•</span>
                                  <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed" >{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {enrichedJd.technical_skills && enrichedJd.technical_skills.length > 0 && (
                          <div>
                            <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Competências Técnicas</span>
                            <div className="flex flex-wrap gap-1.5">
                              {enrichedJd.technical_skills.map((skill, idx) => (
                                <span key={idx} className="px-2.5 py-0.5 text-xs rounded-full dark:text-gray-300 bg-wedo-cyan/10" >
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
                              {enrichedJd.behavioral_competencies.map((comp, idx) => (
                                <span key={idx} className="px-2.5 py-0.5 text-xs rounded-full dark:text-gray-300 bg-wedo-cyan/10" >
                                  {comp}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="border rounded-md p-3 dark:bg-gray-800/30 border-wedo-cyan/15 bg-wedo-cyan/[.02]">
                        <div className="flex flex-col items-center justify-center py-6">
                          <Brain className="h-8 w-8 mb-2 text-wedo-cyan opacity-40" />
                          <p className="text-xs text-gray-400 dark:text-gray-500 text-center leading-relaxed" >
                            Nenhum JD enriquecido gerado ainda.<br />
                            Clique em Editar Descrição para gerar.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 3. EDITING SECTION */}
              {isEditing && (
                <div className="space-y-0">
                  <div className="grid grid-cols-2 gap-4">
                    {/* LEFT COLUMN */}
                    <div className="space-y-4">
                      {/* Section 1 - Descrição / Sumário */}
                      <div>
                        <label className="text-xs font-semibold text-gray-900 uppercase tracking-wide mb-2 block dark:text-gray-100">Descrição / Sumário</label>
                        <div className="bg-white rounded-md border border-gray-200 dark:border-gray-700 dark:bg-gray-900 p-3">
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full h-40 text-xs text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-md p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-gray-900/20 focus:border-gray-400 bg-gray-50 dark:bg-gray-800"
                            placeholder="Forneça uma visão geral da vaga, incluindo propósito e como contribui para a organização..."
                            
                          />
                        </div>
                      </div>

                      {/* Section 2 - Responsabilidades */}
                      <div>
                        <label className="text-xs font-semibold text-gray-900 uppercase tracking-wide mb-2 block dark:text-gray-100">Responsabilidades</label>
                        <div className="bg-white rounded-md border border-gray-200 dark:border-gray-700 dark:bg-gray-900 p-3">
                          <div className="space-y-0.5">
                            {editResponsibilities.map((item, idx) => (
                              <div key={idx} className="group flex items-start gap-2 py-1 px-1 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800">
                                <span className="text-xs text-gray-400 mt-0.5 shrink-0">•</span>
                                <span className="text-xs text-gray-700 dark:text-gray-300 flex-1 leading-relaxed" >{item}</span>
                                <button
                                  onClick={() => setEditResponsibilities(prev => prev.filter((_, i) => i !== idx))}
                                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-status-error shrink-0 transition-opacity"
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              </div>
                            ))}
                          </div>
                          {editingField === 'responsibilities' ? (
                            <div className="flex gap-1.5 mt-2">
                              <input
                                value={newItem}
                                onChange={(e) => setNewItem(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter' && newItem.trim()) { setEditResponsibilities(prev => [...prev, newItem.trim()]); setNewItem(''); }}}
                                className="flex-1 h-7 text-xs border border-gray-200 dark:border-gray-700 rounded-md px-2.5 focus:outline-none focus:ring-1 focus:ring-gray-900/20 bg-gray-50 dark:bg-gray-800 dark:text-gray-200"
                                placeholder="Adicionar responsabilidade..."
                                autoFocus
                                
                              />
                              <button onClick={() => { if (newItem.trim()) { setEditResponsibilities(prev => [...prev, newItem.trim()]); setNewItem(''); } setEditingField(null); }} className="text-xs text-gray-600 hover:text-gray-900 px-2">OK</button>
                            </div>
                          ) : (
                            <button onClick={() => { setNewItem(''); setEditingField('responsibilities') }} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1 mt-2">
                              <Plus className="h-3 w-3" /> Adicionar
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Section 3 - Competências Técnicas */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <label className="text-xs font-semibold text-gray-900 uppercase tracking-wide dark:text-gray-100">Competências Técnicas</label>
                          <button
                            onClick={fetchTechSuggestions}
                            disabled={isLoadingTechSuggestions}
                            className="flex items-center gap-1 text-micro px-2 py-0.5 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/[.06] transition-colors hover:opacity-80 disabled:opacity-50"
                          >
                            {isLoadingTechSuggestions ? <Loader2 className="h-3 w-3 animate-spin" /> : <Brain className="h-3 w-3 text-wedo-cyan" />}
                            Sugerir com IA
                          </button>
                        </div>
                        <div className="bg-white rounded-md border border-gray-200 dark:border-gray-700 dark:bg-gray-900 p-3">
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {editTechSkills.map((item, idx) => (
                              <span key={idx} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
                                {item}
                                <button onClick={() => setEditTechSkills(prev => prev.filter((_, i) => i !== idx))} className="text-gray-400 hover:text-status-error">
                                  <XCircle className="h-3 w-3" />
                                </button>
                              </span>
                            ))}
                            {aiTechSuggestions.map((s) => (
                              <button
                                key={s.skill}
                                onClick={() => {
                                  if (!editTechSkills.includes(s.skill)) {
                                    setEditTechSkills(prev => [...prev, s.skill])
                                  }
                                  setAiTechSuggestions(prev => prev.filter(x => x.skill !== s.skill))
                                }}
                                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-colors hover:opacity-80 border-wedo-cyan/40 text-wedo-cyan-dark bg-wedo-cyan/[0.08]"
                              >
                                <Plus className="h-3 w-3 text-gray-700" />
                                {s.skill}
                              </button>
                            ))}
                          </div>
                          {editingField === 'techSkills' ? (
                            <div className="flex gap-1.5">
                              <input
                                value={newItem}
                                onChange={(e) => setNewItem(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter' && newItem.trim()) { setEditTechSkills(prev => [...prev, newItem.trim()]); setNewItem(''); }}}
                                className="flex-1 h-7 text-xs border border-gray-200 dark:border-gray-700 rounded-md px-2.5 focus:outline-none focus:ring-1 focus:ring-gray-900/20 bg-gray-50 dark:bg-gray-800 dark:text-gray-200"
                                placeholder="Adicionar competência técnica..."
                                autoFocus
                                
                              />
                              <button onClick={() => { if (newItem.trim()) { setEditTechSkills(prev => [...prev, newItem.trim()]); setNewItem(''); } setEditingField(null); }} className="text-xs text-gray-600 hover:text-gray-900 px-2">OK</button>
                            </div>
                          ) : (
                            <button onClick={() => { setNewItem(''); setEditingField('techSkills') }} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
                              <Plus className="h-3 w-3" /> Adicionar
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Section 4 - Competências Comportamentais */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <label className="text-xs font-semibold text-gray-900 uppercase tracking-wide dark:text-gray-100">Competências Comportamentais</label>
                          <button
                            onClick={fetchBehavSuggestions}
                            disabled={isLoadingBehavSuggestions}
                            className="flex items-center gap-1 text-micro px-2 py-0.5 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/[.06] transition-colors hover:opacity-80 disabled:opacity-50"
                          >
                            {isLoadingBehavSuggestions ? <Loader2 className="h-3 w-3 animate-spin" /> : <Brain className="h-3 w-3 text-wedo-cyan" />}
                            Sugerir com IA
                          </button>
                        </div>
                        <div className="bg-white rounded-md border border-gray-200 dark:border-gray-700 dark:bg-gray-900 p-3">
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {editBehavCompetencies.map((item, idx) => (
                              <span key={idx} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
                                {item}
                                <button onClick={() => setEditBehavCompetencies(prev => prev.filter((_, i) => i !== idx))} className="text-gray-400 hover:text-status-error">
                                  <XCircle className="h-3 w-3" />
                                </button>
                              </span>
                            ))}
                            {aiBehavSuggestions.map((c) => (
                              <button
                                key={c.key}
                                onClick={() => {
                                  if (!editBehavCompetencies.includes(c.name)) {
                                    setEditBehavCompetencies(prev => [...prev, c.name])
                                  }
                                  setAiBehavSuggestions(prev => prev.filter(x => x.key !== c.key))
                                }}
                                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-colors hover:opacity-80 border-wedo-cyan/40 text-wedo-cyan-dark bg-wedo-cyan/[0.08]"
                              >
                                <Plus className="h-3 w-3 text-gray-700" />
                                {c.name}
                              </button>
                            ))}
                          </div>
                          {editingField === 'behavCompetencies' ? (
                            <div className="flex gap-1.5">
                              <input
                                value={newItem}
                                onChange={(e) => setNewItem(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter' && newItem.trim()) { setEditBehavCompetencies(prev => [...prev, newItem.trim()]); setNewItem(''); }}}
                                className="flex-1 h-7 text-xs border border-gray-200 dark:border-gray-700 rounded-md px-2.5 focus:outline-none focus:ring-1 focus:ring-gray-900/20 bg-gray-50 dark:bg-gray-800 dark:text-gray-200"
                                placeholder="Adicionar competência comportamental..."
                                autoFocus
                                
                              />
                              <button onClick={() => { if (newItem.trim()) { setEditBehavCompetencies(prev => [...prev, newItem.trim()]); setNewItem(''); } setEditingField(null); }} className="text-xs text-gray-600 hover:text-gray-900 px-2">OK</button>
                            </div>
                          ) : (
                            <button onClick={() => { setNewItem(''); setEditingField('behavCompetencies') }} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
                              <Plus className="h-3 w-3" /> Adicionar
                            </button>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 4. RIGHT COLUMN - empty state or generated JD */}
                    <div className="sticky top-0 self-start">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-xs font-semibold text-gray-900 uppercase tracking-wide dark:text-gray-100">Descrição Gerada pela LIA</label>
                        <Button
                          variant="outline"
                          size="sm"
                          className={cn(
                            "h-7 text-xs px-3 transition-all",
                            isGeneratingJD 
                              ? "bg-gray-900 dark:bg-gray-50 text-white border-gray-900 dark:border-gray-50" 
                              : "bg-gray-900 text-white border-gray-900 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:border-gray-100"
                          )}
                          onClick={generateJD}
                          disabled={isGeneratingJD}
                        >
                          {isGeneratingJD ? (
                            <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                          ) : (
                            <Brain className="h-3 w-3 mr-1.5 text-wedo-cyan" />
                          )}
                          {isGeneratingJD ? 'Gerando...' : 'Gerar Descrição'}
                        </Button>
                      </div>
                      <div className="bg-white rounded-md border border-gray-200 dark:border-gray-700 dark:bg-gray-900 overflow-hidden min-h-[200px]">
                        {isGeneratingJD && (
                          <div className="p-4 space-y-3">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-gray-100 dark:bg-gray-800">
                                <Loader2 className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-spin" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                  Gerando Descrição do Cargo...
                                </p>
                                <p className="text-micro text-gray-500 mt-0.5">
                                  Etapa {jdGenerationStep} de 4
                                </p>
                              </div>
                            </div>
                            {jdTypedMessage && (
                              <div className="flex items-center gap-2 pl-1">
                                <div className="w-1.5 h-1.5 rounded-full bg-gray-900 dark:bg-gray-50 animate-pulse" />
                                <p className="text-xs text-gray-700 dark:text-gray-300">
                                  {jdTypedMessage}
                                  {jdTypedMessage.length < jdDynamicMessage.length && (
                                    <span className="inline-block w-[2px] h-[13px] bg-gray-900 dark:bg-gray-50 ml-0.5 align-middle animate-pulse" />
                                  )}
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {generatedJD && !isGeneratingJD && (
                          <div className="max-h-[400px] overflow-y-auto p-4">
                            {formatJDText(generatedJD.full_description)}

                            {generatedJD.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 pt-4 mt-3 border-t border-gray-100 dark:border-gray-700">
                                {generatedJD.tags.map((tag, idx) => (
                                  <span key={idx} className="text-micro px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full dark:bg-gray-800 dark:text-gray-400">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}

                            <div className="pt-3">
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full h-7 text-xs border-gray-200 text-gray-700 dark:border-gray-600 dark:text-gray-300"
                                onClick={handleCopyJD}
                              >
                                {copiedJD ? (
                                  <>
                                    <Check className="h-3 w-3 mr-1" />
                                    Copiado!
                                  </>
                                ) : (
                                  <>
                                    <Copy className="h-3 w-3 mr-1" />
                                    Copiar Descrição
                                  </>
                                )}
                              </Button>
                            </div>
                          </div>
                        )}

                        {!generatedJD && !isGeneratingJD && (
                          <div className="flex flex-col items-center justify-center py-16 px-4">
                            <Brain className="h-6 w-6 mb-2 text-wedo-cyan" />
                            <p className="text-xs text-gray-400 dark:text-gray-500 text-center" >Descrição gerada pela LIA aparecerá aqui</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 5. BOTTOM ACTION BAR */}
                  <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-micro px-3 border-gray-200 text-gray-600 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                      onClick={handleCancel}
                    >
                      Cancelar
                    </Button>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-micro px-3 border-gray-200 text-gray-700 dark:border-gray-600 dark:text-gray-300"
                        onClick={handleSaveRascunho}
                        disabled={isSavingInline}
                      >
                        {isSavingInline ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Save className="h-3 w-3 mr-1" />}
                        Salvar Rascunho
                      </Button>
                      <Button
                        size="sm"
                        className="h-7 text-micro px-4 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                        onClick={handleSaveDefinitiva}
                        disabled={isSavingDefinitive}
                      >
                        {isSavingDefinitive ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
                        Salvar Versão Definitiva
                      </Button>
                      {generatedJD && onUpdateJobDescription && (
                        <Button
                          size="sm"
                          className="h-7 text-micro px-4 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                          onClick={handleSaveAndUpdateJD}
                          disabled={isSavingWithJD}
                        >
                          {isSavingWithJD ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <FileText className="h-3 w-3 mr-1" />}
                          Salvar e Atualizar JD
                        </Button>
                      )}
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
              <p className="text-xs text-gray-500">Não foi possível avaliar o JD.</p>
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
