"use client"

import { useState, useCallback, useRef } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { DataRequirement, validateCandidateDataForOpinion } from "@/components/modals/insufficient-data-modal"
import type { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import { toast } from "sonner"
import { useCurrentCompany } from '@/hooks/company/use-current-company'

interface LiaChatMessage {
  role: 'user' | 'lia'
  content: string
  timestamp: Date
}

export function useCandidatePreviewCore(candidate: Record<string, unknown> | null, jobId?: string) {
  const { companyId } = useCurrentCompany()
  const t = useTranslations('candidatePreview')
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<'profile' | 'activities' | 'files' | 'opinions' | 'consent'>('profile')
  const [showLiaModal, setShowLiaModal] = useState(false)
  const [liaConversation, setLiaConversation] = useState("")

  const [selectedFile, setSelectedFile] = useState<Record<string, unknown> | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewType, setPreviewType] = useState<'pdf' | 'image' | 'video' | 'audio' | null>(null)
  const [isAnalyzingWithLia, setIsAnalyzingWithLia] = useState(false)
  const [lastAnalysisDate, setLastAnalysisDate] = useState<Date | null>(
    (candidate as Record<string, unknown>)?.lastLiaAnalysis
      ? new Date(String((candidate as Record<string, unknown>).lastLiaAnalysis))
      : new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
  )

  const [liaChatMessages, setLiaChatMessages] = useState<LiaChatMessage[]>([])
  const [isLiaChatLoading, setIsLiaChatLoading] = useState(false)
  const [liaConversationId, setLiaConversationId] = useState<string | null>(null)

  const [expandedOpinionId, setExpandedOpinionId] = useState<string | null>(null)

  const [showUpdateOpinionAlert, setShowUpdateOpinionAlert] = useState(false)
  const [showInsufficientDataModal, setShowInsufficientDataModal] = useState(false)
  const [dataRequirements, setDataRequirements] = useState<DataRequirement[]>([])
  const [lastOpinionDate, setLastOpinionDate] = useState<Date | null>(null)

  const [screeningModalOpen, setScreeningModalOpen] = useState(false)
  const [screeningModalData, setScreeningModalData] = useState<{
    type: 'audio' | 'video'
    title: string
    duration: string
    mediaUrl?: string
    questions: ScreeningQuestion[]
    transcription?: TranscriptionSegment[]
    highlights?: string[]
  } | null>(null)

  const [discModalOpen, setDiscModalOpen] = useState(false)
  const [discModalData, setDiscModalData] = useState<Record<string, unknown> | null>(null)
  const [bigFiveModalOpen, setBigFiveModalOpen] = useState(false)
  const [bigFiveModalCandidate, setBigFiveModalCandidate] = useState<Record<string, unknown> | null>(null)

  const [copiedItemId, setCopiedItemId] = useState<string | null>(null)

  const lastFetchedHistoryCandidateRef = useRef<string | null>(null)
  const candidateId = candidate?.id as string | undefined
  // Pearch candidates have non-UUID ids. Opinions endpoints expect internal DB UUIDs.
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  const candidateIsLocal = !!candidateId && UUID_RE.test(candidateId)

  // Fix 1: React Query v5 — opinions summary
  const {
    data: opinionsData,
    isLoading: isLoadingOpinions,
    refetch: refetchOpinionsSummary,
  } = useQuery({
    queryKey: ['candidate-opinions-summary', candidateId],
    queryFn: () =>
      fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/summary`)
        .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() }),
    enabled: candidateIsLocal,
    staleTime: 60_000,
  })

  // Fix 1: React Query v5 — opinions history (only load when tab is active)
  const {
    data: opinionsHistoryData,
    isLoading: isLoadingHistory,
    isError: isErrorHistory,
    refetch: refetchOpinionsHistory,
  } = useQuery({
    queryKey: ['candidate-opinions-history', candidateId],
    queryFn: () =>
      fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/history`)
        .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() }),
    enabled: candidateIsLocal && activeTab === opinions,
    staleTime: 60_000,
  })

  const opinionsHistory = opinionsHistoryData ?? ([] as Record<string, unknown>[])

  const fetchOpinionsSummary = useCallback(async () => {
    await refetchOpinionsSummary()
  }, [refetchOpinionsSummary])

  const retryOpinionsHistory = useCallback(() => {
    lastFetchedHistoryCandidateRef.current = null
    refetchOpinionsHistory()
  }, [refetchOpinionsHistory])

  const sendLiaMessage = async (message: string) => {
    if (!message.trim()) return

    setLiaChatMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date()
    }])

    setLiaConversation("")
    setIsLiaChatLoading(true)

    try {
      const response = await fetch('/api/backend-proxy/lia/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          context: {
            candidate_id: candidateId,
            candidate_name: (candidate as Record<string, unknown>)?.name,
            conversation_id: liaConversationId
          }
        })
      })

      if (!response.ok) {
        throw new Error(`${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        setLiaChatMessages(prev => [...prev, {
          role: 'lia',
          content: data.response,
          timestamp: new Date()
        }])

        if (data.conversation_id) {
          setLiaConversationId(data.conversation_id)
        }
      } else {
        throw new Error(data.error || t('errorUnknown'))
      }
    } catch (error) {
      toast.error(t('errorSendMessage'), { description: error instanceof Error ? error.message : t('errorSendMessageDesc') })
    } finally {
      setIsLiaChatLoading(false)
    }
  }

  const generateNewOpinion = async () => {
    if (!candidate || !companyId) return
    setShowUpdateOpinionAlert(false)
    setIsAnalyzingWithLia(true)

    try {
      // Vaga em contexto -> parecer job-directed (gera + persiste a matriz de qualificacao).
      if (jobId) {
        // Fix 2: company_id removed — resolved server-side from JWT
        const parecerRes = await fetch(
          `/api/backend-proxy/opinions/candidate/${candidateId}/parecer`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_vacancy_id: jobId }),
          }
        )
        if (!parecerRes.ok) throw new Error(t('errorGenerateParecer'))
        setLastAnalysisDate(new Date())
        await fetchOpinionsSummary()
        // Invalidate history cache so it refreshes on next tab visit
        queryClient.invalidateQueries({ queryKey: ['candidate-opinions-history', candidateId] })
        toast.success(t('parecerGenerated'), { description: t('parecerGeneratedDesc') })
        return
      }

      const c = candidate as Record<string, unknown>
      const candidateInput = {
        id: c.id,
        name: c.name || 'Candidato',
        position: c.currentPosition || c.position || c.headline || '',
        location: c.location || c.city || '',
        company: c.current_company || c.company || '',
        cv_text: c.cv_text || c.cvText || c.resumeText || '',
        skills: c.skills || [],
        experience_years: c.experienceYears || c.experience_years || null,
        education: Array.isArray(c.education) && (c.education as unknown[]).length > 0
          ? (c.education as Record<string, unknown>[])[0]?.degree || (c.education as Record<string, unknown>[])[0]?.institution || ''
          : '',
        seniority_level: c.seniorityLevel || c.seniority_level || ''
      }

      // Fix 2: company_id removed — resolved server-side from JWT
      const analysisResponse = await fetch(`/api/backend-proxy/analysis/candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidates: [candidateInput],
          analysis_type: 'general'
        })
      })

      if (!analysisResponse.ok) {
        throw new Error(t('errorAnalysisFailed'))
      }

      const analysisData = await analysisResponse.json()
      const result = analysisData.results?.[0]

      if (!result) {
        throw new Error(t('errorAnalysisEmpty'))
      }

      let recommendation = 'pending_review'
      if (result.lia_score >= 70) {
        recommendation = 'approved'
      } else if (result.lia_score < 50) {
        recommendation = 'not_approved'
      }

      const opinionPayload = {
        candidate_id: c.id,
        opinion_type: 'general',
        source: 'cv_analysis',
        score: result.lia_score || 0,
        archetype: result.archetype || 'Não Identificado',
        recommendation: recommendation,
        summary: result.explanation || 'Análise realizada pela IA',
        score_breakdown: result.score_breakdown ? {
          skills_match: result.score_breakdown.match_tecnico || null,
          personality_fit: result.score_breakdown.fit_personalidade || null,
          experience_match: result.score_breakdown.relevancia_experiencia || null,
          cultural_fit: result.score_breakdown.alinhamento_cultural || null
        } : {},
        strengths: result.strengths || [],
        concerns: [],
        gaps: result.gaps || [],
        matched_skills: [],
        missing_skills: [],
        next_steps: result.potential_roles ? `Cargos potenciais: ${result.potential_roles.join(', ')}` : 'Validar perfil em entrevista'
      }

      // Fix 2: company_id and user_id removed from query string — resolved server-side from JWT
      const opinionResponse = await fetch(`/api/backend-proxy/opinions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(opinionPayload)
      })

      if (!opinionResponse.ok) {
        await opinionResponse.json().catch(() => ({}))
        throw new Error(t('errorSaveParecer'))
      }

      setLastAnalysisDate(new Date())

      await fetchOpinionsSummary()
      queryClient.invalidateQueries({ queryKey: ['candidate-opinions-history', candidateId] })

      toast.success(t('parecerGenerated'), { description: t('parecerGeneratedDesc') })
    } catch {
      toast.error(t('errorGenerateParecerTitle'), { description: t('errorGenerateParecerDesc') })
    } finally {
      setIsAnalyzingWithLia(false)
    }
  }

  const handleAnalyzeWithLia = async () => {
    if (!candidateId || !candidate || !companyId) return

    const validation = validateCandidateDataForOpinion(candidate)

    if (!validation.isValid) {
      setDataRequirements(validation.requirements)
      setShowInsufficientDataModal(true)
      return
    }

    if (validation.canProceedWithWarning) {
      setDataRequirements(validation.requirements)
      setShowInsufficientDataModal(true)
      return
    }

    try {
      // Fix 2: company_id removed — resolved server-side from JWT
      const summaryResponse = await fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/summary`)
      if (summaryResponse.ok) {
        const data = await summaryResponse.json()
        if (data.current_general_opinion?.created_at) {
          const lastDate = new Date(data.current_general_opinion.created_at)
          const daysSince = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
          if (daysSince < 30) {
            setLastOpinionDate(lastDate)
            setShowUpdateOpinionAlert(true)
            return
          }
        }
      }
    } catch {
    }

    await generateNewOpinion()
  }

  const handleProceedWithLimitedData = async () => {
    setShowInsufficientDataModal(false)
    if (!companyId) return

    try {
      // Fix 2: company_id removed — resolved server-side from JWT
      const summaryResponse = await fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/summary`)
      if (summaryResponse.ok) {
        const data = await summaryResponse.json()
        if (data.current_general_opinion?.created_at) {
          const lastDate = new Date(data.current_general_opinion.created_at)
          const daysSince = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
          if (daysSince < 30) {
            setLastOpinionDate(lastDate)
            setShowUpdateOpinionAlert(true)
            return
          }
        }
      }
    } catch {
    }

    await generateNewOpinion()
  }

  // Fix 3: i18n — formatAnalysisDate uses t() for all PT-BR strings
  const formatAnalysisDate = (date: Date | null) => {
    if (!date) return t('neverAnalyzed')

    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return t('justNow')
    if (diffMins < 60) return t('minutesAgo', { count: diffMins })
    if (diffHours < 24) return t('hoursAgo', { count: diffHours })
    if (diffDays === 1) return t('yesterday')
    if (diffDays < 7) return t('daysAgo', { count: diffDays })

    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const generateShortId = (name: string, id: string | number | null | undefined): string => {
    const letters = (name || 'XX').replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'XX'
    const idStr = String(id || '')
    const digits = idStr.replace(/[^0-9]/g, '')
    const lastFourDigits = digits.length >= 4
      ? digits.slice(-4)
      : digits.padStart(4, '0').slice(-4) || String(Math.floor(1000 + Math.random() * 9000))
    return `${letters}${lastFourDigits}`
  }

  const cleanTextForCopy = (text: string): string => {
    return text
      .replace(/^#+\s*/gm, '')
      .replace(/^\*+\s*/gm, '• ')
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/^-\s+/gm, '• ')
      .trim()
  }

  const handleCopyOpinion = async (opinion: Record<string, unknown>, type: 'general' | 'wsi') => {
    const c = candidate as Record<string, unknown>
    const isWsiOpinion = type === 'wsi' || opinion.opinion_type === 'wsi'
    const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score

    let textToCopy = `PARECER IA - ${c.name || c.nome}\n`
    textToCopy += `Tipo: ${isWsiOpinion ? 'Parecer WSI' : (opinion.job_vacancy_id ? 'Parecer de Vaga' : 'Parecer Geral')}\n`
    if (opinion.job_vacancy_title) {
      textToCopy += `Vaga: ${opinion.job_vacancy_title}\n`
    }
    if (displayScore !== null && displayScore !== undefined) {
      // @canonical-allow-100 fallback for non-WSI legacy opinion in copy-to-clipboard text
      textToCopy += `Nota: ${isWsiOpinion ? `${(displayScore as number).toFixed(1)}/10` : `${Math.round(displayScore as number)}/100`}\n`
    }
    textToCopy += `\n`

    if (opinion.summary) {
      textToCopy += `${cleanTextForCopy(String(opinion.summary))}\n\n`
    }
    if ((opinion.strengths as string[])?.length > 0) {
      textToCopy += `PONTOS FORTES:\n${(opinion.strengths as string[]).map((s: string) => `• ${cleanTextForCopy(s)}`).join('\n')}\n\n`
    }
    if ((opinion.concerns as string[])?.length > 0) {
      textToCopy += `PONTOS DE ATENÇÃO:\n${(opinion.concerns as string[]).map((c: string) => `• ${cleanTextForCopy(c)}`).join('\n')}\n\n`
    }
    if ((opinion.gaps as string[])?.length > 0) {
      textToCopy += `GAPS IDENTIFICADOS:\n${(opinion.gaps as string[]).map((g: string) => `• ${cleanTextForCopy(g)}`).join('\n')}\n\n`
    }
    if (opinion.next_steps) {
      textToCopy += `PRÓXIMOS PASSOS:\n${cleanTextForCopy(String(opinion.next_steps))}\n`
    }

    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopiedItemId(`opinion-${opinion.id}`)
      setTimeout(() => setCopiedItemId(null), 2000)
    } catch {
    }
  }

  const formatCurrency = (value: number | string | null | undefined, currency: string = 'BRL'): string => {
    if (value === null || value === undefined || value === '') return 'Não informado'
    const numValue = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(numValue)) return 'Não informado'
    return numValue.toLocaleString('pt-BR', { style: 'currency', currency })
  }

  const getLanguagesData = (): Array<{language: string, proficiency: string}> => {
    const c = candidate as Record<string, unknown>
    const langs = c?.languages
    if (!langs) return []
    if (Array.isArray(langs)) {
      return langs.map((l: Record<string, unknown> | string) => {
        if (typeof l === 'string') return { language: l, proficiency: '' }
        return { language: String(l.language || l.name || ''), proficiency: String(l.proficiency || l.level || '') }
      }).filter((l) => l.language)
    }
    if (typeof langs === 'object') {
      return Object.entries(langs as Record<string, unknown>).map(([language, proficiency]) => ({
        language,
        proficiency: String(proficiency)
      }))
    }
    return []
  }

  const hasSalaryData = (): boolean => {
    const c = candidate as Record<string, unknown>
    return !!(
      c?.current_salary || c?.currentSalary ||
      c?.desired_salary_min || c?.desiredSalaryMin ||
      c?.desired_salary_max || c?.desiredSalaryMax ||
      c?.salary_expectation_clt || c?.salaryExpectationClt ||
      c?.salary_expectation_pj || c?.salaryExpectationPj
    )
  }

  const hasAddressData = (): boolean => {
    const c = candidate as Record<string, unknown>
    return !!(
      c?.address_street || c?.addressStreet ||
      c?.address_district || c?.addressDistrict ||
      c?.location_city || c?.locationCity ||
      c?.location_state || c?.locationState ||
      c?.address_zip || c?.addressZip ||
      c?.location
    )
  }

  const getAddressString = (): string => {
    const c = candidate as Record<string, unknown>
    const parts: string[] = []
    const street = c?.address_street || c?.addressStreet
    const number = c?.address_number || c?.addressNumber
    const complement = c?.address_complement || c?.addressComplement
    const district = c?.address_district || c?.addressDistrict
    const city = c?.location_city || c?.locationCity
    const state = c?.location_state || c?.locationState
    const zip = c?.address_zip || c?.addressZip

    if (street) {
      let line = String(street)
      if (number) line += `, ${number}`
      if (complement) line += ` - ${complement}`
      parts.push(line)
    }
    if (district) parts.push(String(district))
    if (city && state) {
      parts.push(`${city} - ${state}`)
    } else if (city) {
      parts.push(String(city))
    } else if (state) {
      parts.push(String(state))
    }
    if (zip) parts.push(`CEP: ${zip}`)

    if (parts.length === 0 && c?.location) {
      return String(c.location)
    }
    return parts.join('\n')
  }

  const hasAdditionalDetails = (): boolean => {
    const c = candidate as Record<string, unknown>
    return !!(
      c?.work_model_preference || c?.workModelPreference ||
      c?.contract_type_preference || c?.contractTypePreference ||
      c?.willing_to_relocate !== undefined || c?.willingToRelocate !== undefined ||
      c?.mobility
    )
  }

  return {
    activeTab, setActiveTab,
    showLiaModal, setShowLiaModal,
    liaConversation, setLiaConversation,
    selectedFile, setSelectedFile,
    showPreview, setShowPreview,
    previewType, setPreviewType,
    isAnalyzingWithLia,
    lastAnalysisDate,
    liaChatMessages,
    isLiaChatLoading,
    opinionsData,
    isLoadingOpinions,
    expandedOpinionId, setExpandedOpinionId,
    opinionsHistory,
    isLoadingHistory,
    isErrorHistory, retryOpinionsHistory,
    showUpdateOpinionAlert, setShowUpdateOpinionAlert,
    showInsufficientDataModal, setShowInsufficientDataModal,
    dataRequirements,
    lastOpinionDate,
    screeningModalOpen, setScreeningModalOpen,
    screeningModalData, setScreeningModalData,
    discModalOpen, setDiscModalOpen,
    discModalData, setDiscModalData,
    bigFiveModalOpen, setBigFiveModalOpen,
    bigFiveModalCandidate, setBigFiveModalCandidate,
    copiedItemId, setCopiedItemId,
    sendLiaMessage,
    generateNewOpinion,
    handleAnalyzeWithLia,
    handleProceedWithLimitedData,
    formatAnalysisDate,
    generateShortId,
    cleanTextForCopy,
    handleCopyOpinion,
    formatCurrency,
    getLanguagesData,
    hasSalaryData,
    hasAddressData,
    getAddressString,
    hasAdditionalDetails,
    fetchOpinionsSummary,
  }
}
