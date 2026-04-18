"use client"

import React, { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Settings2, ChevronDown, ChevronUp, Edit2, MessageSquare, Globe, Phone,
  CheckCircle, CheckCircle2, BarChart3, Clock, RotateCcw, CalendarClock,
  Shield, ShieldAlert, ShieldCheck, CalendarCheck, AlertTriangle, Save, ListChecks,
  Layers, Info, Brain, Loader2, X, Archive, Gauge, GraduationCap, Target,
  Scale, ClipboardList, FileText, Edit, Calendar, Play, Pause, AlertCircle
} from 'lucide-react'
import { useScreeningConfig, limitToApprovalPreset, approvalPresetToLimit, type ScreeningChannelKey } from '@/hooks/recruitment/useScreeningConfig'
import { CompanyBankQuestions } from '../CompanyBankQuestions'
import { CustomQuestions } from '../CustomQuestions'
import type { CustomQuestion } from '../CustomQuestions'
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getBloomComplexity, getEstimatedTime, getBloomLabelPTBR, getDreyfusLabelPTBR } from '@/components/jobs/jobsPageConstants'
import { JDEvaluationPanel } from '@/components/wsi'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'

const BIG_FIVE_PT_BR: Record<string, string> = {
  openness: 'Abertura a mudanças',
  conscientiousness: 'Organização e disciplina',
  extraversion: 'Sociabilidade',
  agreeableness: 'Cooperação',
  neuroticism: 'Estabilidade emocional',
}


function getBigFiveLabelPTBR(trait: string | null | undefined): string {
  if (!trait) return ''
  const key = trait.toLowerCase().replace(/\s+/g, '_')
  return BIG_FIVE_PT_BR[key] || trait
}

interface ScreeningConfigManagerProps {
  job: Record<string, unknown>
  onJobUpdate?: (updatedJob: Record<string, unknown>) => void
  onFormUpdate?: (updates: Record<string, unknown>) => void
}

interface ScreeningConfigContentProps {
  job: Record<string, unknown>
  onJobUpdate?: (updatedJob: Record<string, unknown>) => void
  onFormUpdate?: (updates: Record<string, unknown>) => void
  activeSection: 'configuracoes' | 'descricao' | 'perguntas'
}

// Inline component — company default questions with opt-out toggle
function CompanyDefaultQuestions({
  questions,
  disabledIds,
  isEditing,
  onToggle,
}: {
  questions: Array<{ id: string; question: string; is_eliminatory: boolean; expected_answer?: string }>
  disabledIds: Set<string>
  isEditing: boolean
  onToggle: (id: string, enabled: boolean) => void
}) {
  const [isExpanded, setIsExpanded] = useState(true)
  const activeCount = questions.filter(q => !disabledIds.has(q.id)).length

  return (
    <div className="border border-lia-border-subtle rounded-xl bg-lia-bg-primary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-lia-text-tertiary" />
          <span className="text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
            Padrão da Empresa
          </span>
          {questions.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
              {activeCount}/{questions.length} ativas
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-disabled" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-disabled" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {questions.length === 0 ? (
            <p className="text-xs text-lia-text-disabled text-center py-4 italic">
              Nenhuma pergunta padrão configurada. Acesse <strong>Configurações → Perguntas Padrão</strong>.
            </p>
          ) : (
            questions.map(q => {
              const enabled = !disabledIds.has(q.id)
              return (
                <div
                  key={q.id}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors motion-reduce:transition-none ${
 enabled
                      ? 'bg-lia-bg-primary'
                      : 'bg-lia-bg-secondary/50 opacity-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={enabled}
                    disabled={!isEditing}
                    onChange={e => onToggle(q.id, e.target.checked)}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default accent-lia-btn-primary-bg cursor-pointer disabled:cursor-default"
                  />
                  <span className="text-xs text-lia-text-secondary flex-1">
                    {q.question}
                  </span>
                  {q.is_eliminatory && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error">
                      eliminatória
                    </span>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}

export const SCREENING_SECTIONS = [
  {
    id: "configuracoes",
    title: "Configurações do Roteiro",
    icon: Settings2,
    description: "Formato e duração da triagem",
  },
  {
    id: "descricao",
    title: "Descrição do Cargo",
    icon: FileText,
    description: "Informações da vaga para a LIA",
  },
  {
    id: "perguntas",
    title: "Perguntas de Triagem",
    icon: ListChecks,
    description: "Blocos WSI de avaliação",
  },
]


export function useScreeningConfigManagerCore({ job, onJobUpdate, onFormUpdate, _externalActiveSection, _hideOwnSidebar }: ScreeningConfigManagerProps & { _externalActiveSection?: string; _hideOwnSidebar?: boolean }) {
  const { config: screeningConfig, updateConfig: updateScreeningConfig, isLoading: isLoadingScreeningConfig, loadError: screeningConfigLoadError, mutate: retryScreeningConfig } = useScreeningConfig((job?.backendId || job?.jobId || null) as string | number | null)

  const [blockPromptOpen, setBlockPromptOpen] = useState<string | null>(null)
  const [blockPromptText, setBlockPromptText] = useState("")
  const [blockGenerationFeedback, setBlockGenerationFeedback] = useState<Record<string, unknown>>({})
  const [internalActiveSection, setInternalActiveSection] = useState("configuracoes")
  const activeSection = _externalActiveSection || internalActiveSection
  const setActiveSection = setInternalActiveSection
  const [isEditingScreeningConfig, setIsEditingScreeningConfig] = useState(false)
  const [editChannels, setEditChannels] = useState({
    whatsapp: true, chat_web: true, phone_pstn: false, voice_web: true
  })
  // Task #425 — editable master toggle for channels (default ON for back-compat).
  const [editChannelsMasterEnabled, setEditChannelsMasterEnabled] = useState<boolean>(true)
  // Task #425 — WhatsApp delivery mode picker: 'wa_link' (legacy), 'twilio_direct', or 'both'.
  const [editWhatsappMode, setEditWhatsappMode] = useState<'wa_link' | 'twilio_direct' | 'both'>('wa_link')
  // Sync master toggle + whatsapp mode with server value when config loads or changes outside edit mode.
  useEffect(() => {
    if (!isEditingScreeningConfig) {
      setEditChannelsMasterEnabled(screeningConfig?.channels_master_enabled !== false)
      const m = (screeningConfig?.channels?.whatsapp as { mode?: string } | undefined)?.mode
      setEditWhatsappMode(m === 'twilio_direct' || m === 'both' ? m : 'wa_link')
    }
  }, [screeningConfig?.channels_master_enabled, screeningConfig?.channels?.whatsapp, isEditingScreeningConfig])
  const [editPrimaryChannel, setEditPrimaryChannel] = useState<ScreeningChannelKey>('chat_web')
  const [editFallbackOrder, setEditFallbackOrder] = useState<ScreeningChannelKey[]>(['whatsapp'])
  const [editMinScorePreset, setEditMinScorePreset] = useState<'rigorous' | 'recommended' | 'flexible'>('recommended')
  const [editTimeoutHours, setEditTimeoutHours] = useState(48)
  const [editMaxRetries, setEditMaxRetries] = useState(2)
  const [editSchedulingEnabled, setEditSchedulingEnabled] = useState(true)
  const [editSchedulingMinScorePreset, setEditSchedulingMinScorePreset] = useState<'rigorous' | 'recommended' | 'flexible'>('recommended')
  const [editCalendarProvider, setEditCalendarProvider] = useState('Microsoft')
  const [editAvailableHours, setEditAvailableHours] = useState('9h-18h')
  const [editAvailableHoursInherited, setEditAvailableHoursInherited] = useState(true)
  const [editInterviewDuration, setEditInterviewDuration] = useState(60)
  const [editAutoApprovalPreset, setEditAutoApprovalPreset] = useState<'conservative' | 'recommended' | 'autonomous'>('recommended')
  const [showScreeningToggleConfirm, setShowScreeningToggleConfirm] = useState<'activate' | 'pause' | null>(null)

  const [companyQuestions, setCompanyQuestions] = useState<Array<{ id: string; question: string; is_eliminatory: boolean; expected_answer?: string }>>([])
  const [disabledCompanyQIds, setDisabledCompanyQIds] = useState<Set<string>>(new Set())
  const [selectedBankQuestions, setSelectedBankQuestions] = useState<string[]>([])
  const [bankQuestionOverrides, setBankQuestionOverrides] = useState<Record<string, { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string }>>({})
  const [customQuestions, setCustomQuestions] = useState<CustomQuestion[]>([])

  // Load company default questions
  useEffect(() => {
    fetch('/api/backend-proxy/company/screening-questions')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        const items: Array<Record<string, unknown>> = data?.items ?? (Array.isArray(data) ? data : [])
        setCompanyQuestions(items.map((q) => ({
          id: q.id as string,
          question: (q.question_text || q.question) as string,
          is_eliminatory: (q.is_eliminatory ?? false) as boolean,
          expected_answer: (q.expected_answer || undefined) as string | undefined,
        })))
      })
      .catch((err) => { console.error('[useScreeningConfigManagerCore] eligibility questions fetch failed', err) })
  }, [])

  useEffect(() => {
    const ids: string[] = (job?.disabled_eligibility_question_ids as string[] | undefined) || []
    setDisabledCompanyQIds(new Set(ids))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.id])

  const handleToggleCompanyDefault = async (questionId: string, enabled: boolean) => {
    // Compute new set once and use it for both state update and API call
    const newDisabled = new Set(disabledCompanyQIds)
    if (enabled) newDisabled.delete(questionId)
    else newDisabled.add(questionId)
    setDisabledCompanyQIds(newDisabled)
    const jobId = job?.backendId || job?.jobId || String(job?.id)
    try {
      await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disabled_eligibility_question_ids: [...newDisabled] }),
      })
      onJobUpdate?.({ ...job, disabled_eligibility_question_ids: [...newDisabled] })
    } catch {
      // silent — local state already updated optimistically
    }
  }

  const handleToggleBankQuestion = (questionId: string, selected: boolean) => {
    setSelectedBankQuestions(prev =>
      selected ? [...prev, questionId] : prev.filter(id => id !== questionId)
    )
  }

  const handleUpdateBankQuestion = (questionId: string, updates: { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string }) => {
    setBankQuestionOverrides(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], ...updates }
    }))
  }

  const handleAddCustomQuestion = (question: CustomQuestion) => {
    setCustomQuestions(prev => [...prev, question])
  }

  const handleRemoveCustomQuestion = (questionId: string) => {
    setCustomQuestions(prev => prev.filter(q => q.id !== questionId))
  }

  const handleUpdateCustomQuestion = (questionId: string, updates: Partial<CustomQuestion>) => {
    setCustomQuestions(prev => prev.map(q => q.id === questionId ? { ...q, ...updates } : q))
  }

  const [screeningBlockExpanded, setScreeningBlockExpanded] = useState(true)
  const [isEditingScreening, setIsEditingScreening] = useState(false)
  const [generatedQuestions, setGeneratedQuestions] = useState<Record<number, any[]>>({})
  const [acceptedQuestions, setAcceptedQuestions] = useState<Set<string>>(new Set())
  const [deactivatedQuestions, setDeactivatedQuestions] = useState<Set<string>>(new Set())
  const [expandedQuestionDetails, setExpandedQuestionDetails] = useState<Set<string>>(new Set())
  const [isGeneratingWSI, setIsGeneratingWSI] = useState(false)
  const [wsiGenerationMode, setWsiGenerationMode] = useState<'compact' | 'full' | null>(null)
  const [wsiGenerationStep, setWsiGenerationStep] = useState(0)
  const [wsiGeneratedCount, setWsiGeneratedCount] = useState(0)
  const [wsiGenerationCompleted, setWsiGenerationCompleted] = useState(false)
  const [wsiDynamicMessage, setWsiDynamicMessage] = useState('')
  const [wsiTypedMessage, setWsiTypedMessage] = useState('')
  const [wsiProgressCollapsed, setWsiProgressCollapsed] = useState(false)
  const [wsiSummaryExpanded, setWsiSummaryExpanded] = useState(false)
  const [wsiSummaryTypedText, setWsiSummaryTypedText] = useState('')
  const [wsiSummaryTypingDone, setWsiSummaryTypingDone] = useState(false)
  const [wsiGenerationContext, setWsiGenerationContext] = useState<{
    title: string
    seniority: string | null
    responsibilities: string[]
    technicalSkills: string[]
    behavioralCompetencies: string[]
    blockBreakdown: Record<number, number>
    methodologyBreakdown: Record<string, number>
    companyStandardFound: boolean
  } | null>(null)
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([0, 1, 2, 3, 4, 6])
  const [editingQuestion, setEditingQuestion] = useState<any | null>(null)
  const [suggestedQuestion, setSuggestedQuestion] = useState<any | null>(null)
  const [questionPrompt, setQuestionPrompt] = useState("")

  useEffect(() => {
    if (!wsiDynamicMessage) {
      setWsiTypedMessage('')
      return
    }
    setWsiTypedMessage('')
    let i = 0
    const interval = setInterval(() => {
      i++
      setWsiTypedMessage(wsiDynamicMessage.slice(0, i))
      if (i >= wsiDynamicMessage.length) clearInterval(interval)
    }, 25)
    return () => clearInterval(interval)
  }, [wsiDynamicMessage])

  useEffect(() => {
    if (wsiGenerationStep < 4 || !wsiGenerationCompleted) {
      setWsiSummaryTypedText('')
      setWsiSummaryTypingDone(false)
      return
    }
    const modeLabel = wsiGenerationMode === 'compact' ? 'triagem compacta' : 'triagem completa'
    const fullText = `Você escolheu o modo de ${modeLabel}, que contempla:`
    setWsiSummaryTypedText('')
    setWsiSummaryTypingDone(false)
    let i = 0
    const interval = setInterval(() => {
      i++
      setWsiSummaryTypedText(fullText.slice(0, i))
      if (i >= fullText.length) {
        clearInterval(interval)
        setWsiSummaryTypingDone(true)
      }
    }, 35)
    return () => clearInterval(interval)
  }, [wsiGenerationStep, wsiGenerationCompleted, wsiGenerationMode])

  const handleGenerateWSI = (mode: 'compact' | 'full') => async () => {
    if (!job || isGeneratingWSI) return
    setIsGeneratingWSI(true)
    setWsiGenerationMode(mode)
    setWsiGenerationCompleted(false)
    setWsiSummaryExpanded(false)

    const techReqs = (job.technicalRequirements || []) as Record<string, unknown>[]
    const techSkills = (techReqs.map((r) => r.technology || r.skill || r).filter(Boolean) as string[])
    const behavComps = (job.behavioralCompetencies || []) as Record<string, unknown>[]
    const behavComp = (behavComps.map((c) => c.competency || c.name || c).filter(Boolean) as string[])
    const reqs = (job.requirements || []) as Array<string | Record<string, unknown>>
    const responsibilities = (reqs.map((r) => typeof r === 'string' ? r : (r as Record<string, unknown>).requirement || (r as Record<string, unknown>).text || (r as Record<string, unknown>).name || r).filter(Boolean) as string[])
    setWsiGenerationContext({
      title: (job.title as string) || '',
      seniority: (job.level as string) || (job.seniority as string) || null,
      responsibilities: responsibilities.slice(0, 5),
      technicalSkills: techSkills.slice(0, 6),
      behavioralCompetencies: behavComp.slice(0, 6),
      blockBreakdown: {},
      methodologyBreakdown: {},
      companyStandardFound: false
    })

    setWsiGenerationStep(1)
    setWsiDynamicMessage('Analisando job description...')
    const startTime = Date.now()
    const msg1 = setTimeout(() => setWsiDynamicMessage('Extraindo informações do cargo...'), 1200)
    const msg2 = setTimeout(() => setWsiDynamicMessage('Identificando requisitos-chave...'), 2400)
    const stepTimer2 = setTimeout(() => {
      setWsiGenerationStep(2)
      setWsiDynamicMessage('Buscando critérios de avaliação...')
    }, 3500)
    const msg3 = setTimeout(() => setWsiDynamicMessage('Mapeando competências técnicas...'), 5000)
    const msg4 = setTimeout(() => setWsiDynamicMessage('Identificando competências comportamentais...'), 6500)
    const stepTimer3 = setTimeout(() => {
      setWsiGenerationStep(3)
      setWsiDynamicMessage('Aplicando framework CBI...')
    }, 8000)
    const msg5 = setTimeout(() => setWsiDynamicMessage('Calibrando taxonomia de Bloom...'), 9500)
    const msg6 = setTimeout(() => setWsiDynamicMessage('Integrando modelo Big Five...'), 11000)
    const msg7 = setTimeout(() => setWsiDynamicMessage('Ajustando nível Dreyfus...'), 12500)

    try {
      const jobId = job.backendId || job.jobId || String(job.id)
      const res = await fetch('/api/backend-proxy/wsi/generate-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          job_title: job.title,
          mode,
          technical_skills: techSkills,
          behavioral_competencies: behavComp,
          seniority: job.level || (job as Record<string, unknown>).seniority || null,
          description: job.description || null
        })
      })
      const data = await res.json()
      if (data.success && data.questions) {
        const grouped: Record<number, any[]> = {}
        data.questions.forEach((q: Record<string, unknown>) => {
          const bid = q.block_id || 2
          if (!grouped[bid as number]) grouped[bid as number] = []
          grouped[bid as number].push({ ...q, id: q.id || `q_gen_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`, generated: true })
        })
        setGeneratedQuestions(grouped)
        const totalCount = Object.values(grouped).reduce((sum, arr) => sum + arr.length, 0)
        setWsiGeneratedCount(totalCount)

        const elapsed = Date.now() - startTime
        if (elapsed < 14000) {
          await new Promise(resolve => setTimeout(resolve, 14000 - elapsed))
        }

        const breakdown: Record<number, number> = {}
        const methodBreakdown: Record<string, number> = {}
        let hasCompanyStandard = false
        Object.entries(grouped).forEach(([bid, questions]) => {
          breakdown[Number(bid)] = (questions as Array<Record<string, unknown>>).length
          ;(questions as Array<Record<string, unknown>>).forEach((q: Record<string, unknown>) => {
            const fw = (q.framework || (q.category === 'behavioral' ? 'BigFive' : 'CBI')) as string
            methodBreakdown[fw] = (methodBreakdown[fw] || 0) + 1
            if (q.source === 'company_standard' || q.is_company_standard) hasCompanyStandard = true
          })
        })
        if (Object.keys(methodBreakdown).length === 0) {
          const eligCount = breakdown[2] || 0
          const techCount = breakdown[3] || 0
          const behavCount = (breakdown[4] || 0) + (breakdown[5] || 0)
          if (eligCount > 0) methodBreakdown['CBI'] = (methodBreakdown['CBI'] || 0) + eligCount
          if (techCount > 0) {
            const bloomCount = Math.max(1, Math.floor(techCount * 0.4))
            methodBreakdown['Bloom'] = bloomCount
            methodBreakdown['CBI'] = (methodBreakdown['CBI'] || 0) + (techCount - bloomCount)
          }
          if (behavCount > 0) methodBreakdown['BigFive'] = behavCount
          methodBreakdown['Dreyfus'] = totalCount
        }
        setWsiGenerationContext(prev => prev ? { ...prev, blockBreakdown: breakdown, methodologyBreakdown: methodBreakdown, companyStandardFound: hasCompanyStandard } : prev)
        setWsiDynamicMessage('Finalizando roteiro de triagem...')
        setWsiGenerationStep(4)
        setWsiGenerationCompleted(true)
        setExpandedBlocks(prev => {
          const newBlocks = [...prev]
          ;[2, 3, 4, 5].forEach(id => {
            if (!newBlocks.includes(id)) newBlocks.push(id)
          })
          return newBlocks
        })
      } else {
        throw new Error('Invalid response')
      }
    } catch (err) {
      // Task #425 — Silent mock fallback removed. WSI generation must succeed
      // against the real backend; on failure, surface the error to the user
      // and reset the wizard so they can retry. Never invent questions.
      const message = err instanceof Error ? err.message : String(err)
      console.error('[WSI generation] backend call failed:', message)
      toast.error('Falha ao gerar roteiro WSI', {
        description: 'Não foi possível gerar as perguntas no backend. Verifique a conexão e tente novamente.',
      })
      setGeneratedQuestions({})
      setWsiGeneratedCount(0)
      setWsiGenerationContext(prev => prev ? { ...prev, blockBreakdown: {}, methodologyBreakdown: {}, companyStandardFound: false } : prev)
      setWsiDynamicMessage('')
      setWsiGenerationStep(0)
      setWsiGenerationCompleted(false)
      setWsiGenerationMode(null)
    } finally {
      setIsGeneratingWSI(false)
      clearTimeout(stepTimer2)
      clearTimeout(stepTimer3)
      clearTimeout(msg1)
      clearTimeout(msg2)
      clearTimeout(msg3)
      clearTimeout(msg4)
      clearTimeout(msg5)
      clearTimeout(msg6)
      clearTimeout(msg7)
    }
  }

  const resetScreeningEditing = () => {
    setIsEditingScreening(false)
    setEditingQuestion(null)
    setSuggestedQuestion(null)
    setQuestionPrompt("")
    setGeneratedQuestions({})
    setAcceptedQuestions(new Set())
    setBlockPromptOpen(null)
    setBlockPromptText("")
    setWsiGenerationMode(null)
    setWsiGenerationCompleted(false)
    setWsiGeneratedCount(0)
    setBlockGenerationFeedback({})
    setWsiGenerationStep(0)
    setWsiDynamicMessage('')
    setWsiGenerationContext(null)
  }

  const scConfig = job.screeningConfig as Record<string, unknown> | undefined
  const configDone = !!(screeningConfig && ((screeningConfig as Record<string, unknown>).channels || (screeningConfig as Record<string, unknown>).settings || (screeningConfig as Record<string, unknown>).scheduling)) || !!(scConfig && (scConfig.channels || scConfig.settings || scConfig.scheduling))
  const jdDone = !!(job.description && (job.description as string).trim().length > 0)
  const questionsDone = ((job.screeningQuestions as unknown[] | undefined)?.length ?? 0) > 0 || (isEditingScreening && acceptedQuestions.size > 0)
  const progressCount = [configDone, jdDone, questionsDone].filter(Boolean).length

  const currentSection = SCREENING_SECTIONS.find(s => s.id === activeSection) || SCREENING_SECTIONS[0]
  const SectionIcon = currentSection.icon

  const CHANNEL_LABELS: Record<ScreeningChannelKey, string> = {
    chat_web: 'Chat Web',
    whatsapp: 'WhatsApp',
    phone_pstn: 'Ligação (PSTN)',
    voice_web: 'Voz no Navegador',
  }

  const getConfigStatusInfo = () => {
    if (screeningConfig?.channels_master_enabled === false) return 'Triagem desabilitada'
    const primary = screeningConfig?.screening_channels?.primary_channel
    if (primary) return `Canal: ${CHANNEL_LABELS[primary] ?? primary}`
    const enabledChannels: string[] = []
    if (screeningConfig?.channels?.chat_web?.enabled ?? true) enabledChannels.push('Chat Web')
    if (screeningConfig?.channels?.whatsapp?.enabled ?? true) enabledChannels.push('WhatsApp')
    if (screeningConfig?.channels?.phone_pstn?.enabled ?? false) enabledChannels.push('Ligação')
    if (screeningConfig?.channels?.voice_web?.enabled ?? true) enabledChannels.push('Voz')
    return enabledChannels.join(', ') || 'Nenhum canal'
  }


  return {
    job,
    onJobUpdate,
    SectionIcon,
    acceptedQuestions,
    activeSection,
    bankQuestionOverrides,
    companyQuestions,
    screeningConfig,
    updateScreeningConfig,
    isLoadingScreeningConfig,
    screeningConfigLoadError,
    retryScreeningConfig,
    configDone,
    currentSection,
    customQuestions,
    deactivatedQuestions,
    disabledCompanyQIds,
    editAutoApprovalPreset,
    editAvailableHours,
    editAvailableHoursInherited,
    editCalendarProvider,
    editChannels,
    editChannelsMasterEnabled,
    editWhatsappMode,
    editFallbackOrder,
    editInterviewDuration,
    editMaxRetries,
    editMinScorePreset,
    editPrimaryChannel,
    editSchedulingEnabled,
    editSchedulingMinScorePreset,
    editTimeoutHours,
    expandedBlocks,
    expandedQuestionDetails,
    generatedQuestions,
    getConfigStatusInfo,
    handleAddCustomQuestion,
    handleGenerateWSI,
    handleRemoveCustomQuestion,
    handleToggleBankQuestion,
    handleToggleCompanyDefault,
    handleUpdateBankQuestion,
    handleUpdateCustomQuestion,
    isEditingScreening,
    isEditingScreeningConfig,
    isGeneratingWSI,
    jdDone,
    questionsDone,
    resetScreeningEditing,
    selectedBankQuestions,
    setAcceptedQuestions,
    setActiveSection,
    setDeactivatedQuestions,
    setEditAutoApprovalPreset,
    setEditAvailableHours,
    setEditAvailableHoursInherited,
    setEditCalendarProvider,
    setEditChannels,
    setEditChannelsMasterEnabled,
    setEditWhatsappMode,
    setEditFallbackOrder,
    setEditInterviewDuration,
    setEditMaxRetries,
    setEditMinScorePreset,
    setEditPrimaryChannel,
    setEditSchedulingEnabled,
    setEditSchedulingMinScorePreset,
    setEditTimeoutHours,
    setExpandedBlocks,
    setExpandedQuestionDetails,
    setGeneratedQuestions,
    setIsEditingScreening,
    setIsEditingScreeningConfig,
    setShowScreeningToggleConfirm,
    setWsiDynamicMessage,
    setWsiGenerationCompleted,
    setWsiGenerationContext,
    setWsiGenerationStep,
    setWsiProgressCollapsed,
    setWsiSummaryExpanded,
    showScreeningToggleConfirm,
    wsiDynamicMessage,
    wsiGeneratedCount,
    wsiGenerationCompleted,
    wsiGenerationContext,
    wsiGenerationMode,
    wsiGenerationStep,
    wsiProgressCollapsed,
    wsiSummaryExpanded,
    wsiSummaryTypedText,
    wsiSummaryTypingDone,
    wsiTypedMessage
  }
}
