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
import { useScreeningConfig, limitToApprovalPreset, approvalPresetToLimit } from '@/hooks/useScreeningConfig'
import { CompanyBankQuestions } from './CompanyBankQuestions'
import { CustomQuestions } from './CustomQuestions'
import type { CustomQuestion } from './CustomQuestions'
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getBloomComplexity, getEstimatedTime, getBloomLabelPTBR, getDreyfusLabelPTBR } from '@/components/jobs/jobsPageConstants'
import { JDEvaluationPanel } from '@/components/wsi'
import { Badge } from '@/components/ui/badge'
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
  job: any
  onJobUpdate?: (updatedJob: any) => void
  onFormUpdate?: (updates: any) => void
}

interface ScreeningConfigContentProps {
  job: any
  onJobUpdate?: (updatedJob: any) => void
  onFormUpdate?: (updates: any) => void
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
    <div className="border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="font-['Open_Sans',sans-serif] text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-gray-400">
            Padrão da Empresa
          </span>
          {questions.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {activeCount}/{questions.length} ativas
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {questions.length === 0 ? (
            <p className="text-xs font-['Open_Sans',sans-serif] text-gray-400 dark:text-gray-500 text-center py-4 italic">
              Nenhuma pergunta padrão configurada. Acesse <strong>Configurações → Perguntas Padrão</strong>.
            </p>
          ) : (
            questions.map(q => {
              const enabled = !disabledIds.has(q.id)
              return (
                <div
                  key={q.id}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    enabled
                      ? 'bg-white dark:bg-gray-900'
                      : 'bg-gray-50 dark:bg-gray-800/50 opacity-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={enabled}
                    disabled={!isEditing}
                    onChange={e => onToggle(q.id, e.target.checked)}
                    className="w-3.5 h-3.5 rounded border-gray-300 accent-gray-900 cursor-pointer disabled:cursor-default"
                  />
                  <span className="font-['Open_Sans',sans-serif] text-xs text-gray-700 dark:text-gray-300 flex-1">
                    {q.question}
                  </span>
                  {q.is_eliminatory && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400">
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

function ScreeningConfigManager({ job, onJobUpdate, onFormUpdate, _externalActiveSection, _hideOwnSidebar }: ScreeningConfigManagerProps & { _externalActiveSection?: string; _hideOwnSidebar?: boolean }) {
  const { config: screeningConfig, updateConfig: updateScreeningConfig } = useScreeningConfig(job?.backendId || job?.jobId || null)

  const [internalActiveSection, setInternalActiveSection] = useState("configuracoes")
  const activeSection = _externalActiveSection || internalActiveSection
  const setActiveSection = setInternalActiveSection
  const [isEditingScreeningConfig, setIsEditingScreeningConfig] = useState(false)
  const [editChannels, setEditChannels] = useState({
    whatsapp: true, chat_web: true, phone: false
  })
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
        const items: any[] = data?.items ?? (Array.isArray(data) ? data : [])
        setCompanyQuestions(items.map((q: any) => ({
          id: q.id,
          question: q.question_text || q.question,
          is_eliminatory: q.is_eliminatory ?? false,
          expected_answer: q.expected_answer || undefined,
        })))
      })
      .catch(() => {})
  }, [])

  // Load opt-out list from job
  useEffect(() => {
    const ids: string[] = job?.disabled_eligibility_question_ids || []
    setDisabledCompanyQIds(new Set(ids))
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

    const techSkills = (job.technicalRequirements || []).map((r: any) => r.technology || r.skill || r).filter(Boolean)
    const behavComp = (job.behavioralCompetencies || []).map((c: any) => c.competency || c.name || c).filter(Boolean)
    const responsibilities = (job.requirements || []).map((r: any) => typeof r === 'string' ? r : r.requirement || r.text || r.name || r).filter(Boolean)
    setWsiGenerationContext({
      title: job.title || '',
      seniority: job.level || (job as any).seniority || null,
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
          seniority: job.level || (job as any).seniority || null,
          description: job.description || null
        })
      })
      const data = await res.json()
      if (data.success && data.questions) {
        const grouped: Record<number, any[]> = {}
        data.questions.forEach((q: any) => {
          const bid = q.block_id || 2
          if (!grouped[bid]) grouped[bid] = []
          grouped[bid].push({ ...q, id: q.id || `q_gen_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`, generated: true })
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
          breakdown[Number(bid)] = (questions as any[]).length
          ;(questions as any[]).forEach((q: any) => {
            const fw = q.framework || (q.category === 'behavioral' ? 'BigFive' : 'CBI')
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
    } catch {
      const perBlock = mode === 'compact' ? 4 : 7
      const mockTemplates: Record<number, string[]> = {
        2: [
          'Você possui experiência mínima de 3 anos na área?',
          'Você tem disponibilidade para início imediato?',
          'Possui formação superior completa na área ou correlata?',
          'Está disponível para trabalho presencial conforme necessário?',
          'Possui registro profissional ativo na categoria exigida?'
        ],
        3: [
          'Descreva sua experiência com as tecnologias principais desta vaga.',
          'Como você abordaria a resolução de um problema técnico complexo em produção?',
          'Qual foi o projeto mais desafiador tecnicamente que você liderou?',
          'Como você garante a qualidade do código em projetos de grande escala?',
          'Descreva sua experiência com metodologias ágeis e entrega contínua.',
          'Como você avalia e decide entre diferentes abordagens técnicas para resolver um problema?',
          'Descreva como você estrutura a documentação técnica de um projeto.',
          'Como você realiza code review e garante padrões de qualidade no time?',
          'Qual sua experiência com arquitetura de sistemas escaláveis?'
        ],
        4: [
          'Como você lida com conflitos em equipe?',
          'Descreva uma situação em que precisou se adaptar rapidamente a mudanças.',
          'Como você prioriza demandas concorrentes de diferentes stakeholders?',
          'Conte sobre uma experiência onde precisou dar feedback difícil a um colega.',
          'Como você mantém a motivação da equipe em períodos de alta pressão?'
        ],
        5: [
          'Descreva uma situação profissional em que precisou lidar com um conflito ético.',
          'Como você reagiria se percebesse que uma decisão do seu gestor poderia impactar negativamente a equipe?',
          'Conte sobre uma vez em que precisou adaptar seu estilo de comunicação para influenciar um resultado.',
          'Descreva como você lidaria com uma mudança significativa nos processos da sua área.',
          'Como você equilibra suas metas individuais com os objetivos do time?'
        ]
      }
      const generated: Record<number, any[]> = {}
      ;[2, 3, 4].forEach(bid => {
        const templates = mockTemplates[bid] || mockTemplates[2]
        generated[bid] = templates.slice(0, perBlock).map((text, i) => ({
          id: `q_gen_${Date.now()}_${bid}_${i}`,
          question: text,
          text: text,
          type: bid === 2 ? 'eliminatory' : 'classificatory',
          category: bid === 2 ? 'company' : bid === 3 ? 'technical' : 'behavioral',
          framework: bid === 2 ? 'Company' : bid === 4 ? 'BigFive' : 'CBI',
          block_id: bid,
          skill_targeted: '',
          generated: true
        }))
      })
      setGeneratedQuestions(generated)
      const totalCount = Object.values(generated).reduce((sum, arr) => sum + arr.length, 0)
      setWsiGeneratedCount(totalCount)

      const elapsed = Date.now() - startTime
      if (elapsed < 14000) {
        await new Promise(resolve => setTimeout(resolve, 14000 - elapsed))
      }

      const breakdown: Record<number, number> = {}
      Object.entries(generated).forEach(([bid, questions]) => {
        breakdown[Number(bid)] = (questions as any[]).length
      })
      setWsiGenerationContext(prev => prev ? { ...prev, blockBreakdown: breakdown } : prev)
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

  const configDone = !!(screeningConfig && (screeningConfig.channels || screeningConfig.settings || screeningConfig.scheduling)) || !!(job.screeningConfig && (job.screeningConfig.channels || job.screeningConfig.settings || job.screeningConfig.scheduling))
  const jdDone = !!(job.description && job.description.trim().length > 0)
  const questionsDone = (job.screeningQuestions && job.screeningQuestions.length > 0) || (isEditingScreening && acceptedQuestions.size > 0)
  const progressCount = [configDone, jdDone, questionsDone].filter(Boolean).length

  const currentSection = SCREENING_SECTIONS.find(s => s.id === activeSection) || SCREENING_SECTIONS[0]
  const SectionIcon = currentSection.icon

  const getConfigStatusInfo = () => {
    const enabledChannels: string[] = []
    if (screeningConfig?.channels?.whatsapp?.enabled ?? true) enabledChannels.push('WhatsApp')
    if (screeningConfig?.channels?.chat_web?.enabled ?? true) enabledChannels.push('Chat Web')
    if (screeningConfig?.channels?.phone?.enabled ?? false) enabledChannels.push('Ligação')
    return enabledChannels.join(', ') || 'Nenhum canal'
  }

  return (
    <div className={_hideOwnSidebar ? "" : "flex gap-6"}>
      {!_hideOwnSidebar && (
      <div className="flex-shrink-0" style={{ width: '220px' }}>
        <Card className="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-md overflow-hidden">
          <nav className="space-y-1 p-3 h-full overflow-y-auto">
            {SCREENING_SECTIONS.map((section) => {
              const sectionDone = section.id === 'configuracoes' ? configDone : section.id === 'descricao' ? jdDone : questionsDone
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans ${
                    activeSection === section.id
                      ? 'bg-gray-50 dark:bg-gray-800 border border-gray-900 dark:border-gray-200 text-wedo-cyan-dark dark:text-gray-300'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200 border border-transparent'
                  }`}
                  style={{ fontSize: '0.6875rem', lineHeight: '1.125rem', fontWeight: '500' }}
                >
                  <section.icon className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                    <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                  </div>
                  {sectionDone && (
                    <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  )}
                </button>
              )
            })}
          </nav>
        </Card>
      </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-md p-4">
            <div className="flex items-center gap-3">
              <SectionIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              <div>
                <h2 className={textStyles.h3}>{currentSection.title}</h2>
                <p className={textStyles.description}>{currentSection.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {activeSection === 'configuracoes' && (
                <>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 font-['Open_Sans',sans-serif]">
                    {getConfigStatusInfo()}
                  </span>
                  {!isEditingScreeningConfig ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs rounded-md"
                      onClick={() => setIsEditingScreeningConfig(true)}
                    >
                      <Edit className="w-3.5 h-3.5" />
                      Editar Configurações
                    </Button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" className="text-xs rounded-md" onClick={() => {
                        setIsEditingScreeningConfig(false)
                        if (screeningConfig) {
                          setEditChannels({
                            whatsapp: screeningConfig.channels?.whatsapp?.enabled ?? true,
                            chat_web: screeningConfig.channels?.chat_web?.enabled ?? true,
                            phone: screeningConfig.channels?.phone?.enabled ?? false
                          })
                          setEditMinScorePreset(screeningConfig.settings?.min_score_preset ?? 'recommended')
                          setEditTimeoutHours(screeningConfig.settings?.response_timeout_hours ?? 48)
                          setEditMaxRetries(screeningConfig.settings?.max_retries ?? 2)
                          setEditSchedulingEnabled(screeningConfig.scheduling?.auto_enabled ?? true)
                          setEditSchedulingMinScorePreset(screeningConfig.scheduling?.min_score_for_auto_preset ?? 'recommended')
                          setEditCalendarProvider(screeningConfig.scheduling?.calendar_provider ?? 'Microsoft')
                          setEditAvailableHours(screeningConfig.scheduling?.available_hours ?? '9h-18h')
                          setEditAvailableHoursInherited(screeningConfig.scheduling?.available_hours_inherited ?? true)
                          setEditInterviewDuration(screeningConfig.scheduling?.interview_duration_min ?? 60)
                          setEditAutoApprovalPreset(screeningConfig.settings?.auto_approval_preset ?? limitToApprovalPreset(screeningConfig.settings?.auto_approval_limit))
                        }
                      }}>
                        Cancelar
                      </Button>
                      <Button size="sm" className="gap-1.5 text-xs rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200" onClick={async () => {
                        try {
                          const presetToScore = (preset: string) => {
                            switch(preset) {
                              case 'rigorous': return 4.2
                              case 'flexible': return 3.0
                              default: return 3.8
                            }
                          }
                          const success = await updateScreeningConfig({
                            channels: {
                              whatsapp: { enabled: editChannels.whatsapp, label: 'WhatsApp' },
                              chat_web: { enabled: editChannels.chat_web, label: 'Chat Web' },
                              phone: { enabled: editChannels.phone, label: 'Ligação' }
                            },
                            settings: {
                              min_score: presetToScore(editMinScorePreset),
                              min_score_preset: editMinScorePreset,
                              response_timeout_hours: editTimeoutHours,
                              max_retries: editMaxRetries,
                              auto_approval_limit: approvalPresetToLimit(editAutoApprovalPreset),
                              auto_approval_preset: editAutoApprovalPreset,
                              auto_approvals_count: screeningConfig?.settings?.auto_approvals_count ?? 0,
                              auto_approval_paused: screeningConfig?.settings?.auto_approval_paused ?? false
                            },
                            scheduling: {
                              auto_enabled: editSchedulingEnabled,
                              min_score_for_auto: presetToScore(editSchedulingMinScorePreset),
                              min_score_for_auto_preset: editSchedulingMinScorePreset,
                              calendar_provider: editCalendarProvider,
                              available_hours: editAvailableHours,
                              available_hours_inherited: editAvailableHoursInherited,
                              interview_duration_min: editInterviewDuration
                            }
                          })
                          if (success) {
                            setIsEditingScreeningConfig(false)
                            toast.success('Configurações salvas com sucesso!')
                          } else {
                            toast.error('Erro ao salvar configurações. Tente novamente.')
                          }
                        } catch {
                          toast.error('Erro ao salvar configurações. Tente novamente.')
                        }
                      }}>
                        <Save className="w-3.5 h-3.5" />
                        Salvar
                      </Button>
                    </div>
                  )}
                </>
              )}
              {activeSection === 'descricao' && (
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 font-['Open_Sans',sans-serif]">
                  {jdDone ? 'Descrição preenchida' : 'Descrição pendente'}
                </span>
              )}
              {activeSection === 'perguntas' && (
                <>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 font-['Open_Sans',sans-serif]">
                    {job.screeningQuestions?.length || 0} WSI
                    {((companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length) > 0 && (
                      <> · {(companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length} extras</>
                    )}
                  </span>
                  <div className="flex items-center gap-2 border-l border-gray-200 dark:border-gray-700 pl-3 ml-1">
                    <span className="text-micro text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Inter', sans-serif" }}>
                      Triagem
                    </span>
                    {(job.screeningStatus === 'not_configured' || !job.screeningStatus) ? (
                      <button
                        onClick={() => {
                          const hasQuestions = (job.screeningQuestions?.length || 0) > 0
                          if (!hasQuestions) {
                            toast.error('Configure pelo menos 3 perguntas antes de ativar a triagem.')
                            return
                          }
                          setShowScreeningToggleConfirm('activate')
                        }}
                        className="relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 bg-gray-300 dark:bg-gray-600"
                      >
                        <span
                          className="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform duration-200"
                          style={{ transform: 'translateX(2px)' }}
                        />
                      </button>
                    ) : job.screeningStatus === 'completed' ? (
                      <span className="text-micro font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        Concluída
                      </span>
                    ) : (
                      <button
                        onClick={() => {
                          if (job.screeningStatus === 'active') {
                            setShowScreeningToggleConfirm('pause')
                          } else {
                            const hasQuestions = (job.screeningQuestions?.length || 0) > 0
                            if (!hasQuestions) {
                              toast.error('Configure pelo menos 3 perguntas antes de ativar a triagem.')
                              return
                            }
                            setShowScreeningToggleConfirm('activate')
                          }
                        }}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 ${
                          job.screeningStatus === 'active' ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                        }`}
                      >
                        <span
                          className="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform duration-200"
                          style={{ transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)' }}
                        />
                      </button>
                    )}
                  </div>
                  {!isEditingScreening ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs rounded-md"
                      onClick={() => setIsEditingScreening(true)}
                    >
                      <Edit className="w-3.5 h-3.5" />
                      Editar Perguntas
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="gap-1.5 text-xs rounded-md" onClick={() => resetScreeningEditing()}>
                      <X className="w-3.5 h-3.5" />
                      Cancelar Edição
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>

          {showScreeningToggleConfirm && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 w-[380px] p-5 animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-100 dark:bg-gray-800">
                    {showScreeningToggleConfirm === 'activate'
                      ? <Play className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      : <Pause className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    }
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {showScreeningToggleConfirm === 'activate' ? 'Ativar Triagem' : 'Pausar Triagem'}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {job.title}
                    </p>
                  </div>
                </div>
                <div className="rounded-md p-3 mb-4 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                  <div className="flex items-start gap-2.5">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                      showScreeningToggleConfirm === 'activate' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-amber-100 dark:bg-amber-900/30'
                    }`}>
                      {showScreeningToggleConfirm === 'activate'
                        ? <Play className="w-3 h-3 text-green-600" />
                        : <Pause className="w-3 h-3 text-amber-600" />
                      }
                    </div>
                    <p className="text-xs leading-relaxed text-gray-600 dark:text-gray-400" style={{ fontFamily: "'Inter', sans-serif" }}>
                      {showScreeningToggleConfirm === 'activate'
                        ? 'A LIA começará a avaliar candidatos automaticamente conforme as configurações definidas neste roteiro.'
                        : 'Candidatos em avaliação serão mantidos no estado atual até a reativação. Nenhum novo candidato será triado enquanto a triagem estiver pausada.'
                      }
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-end gap-2 pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-md px-4 border-gray-200 dark:border-gray-700"
                    onClick={() => setShowScreeningToggleConfirm(null)}
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    className="text-xs rounded-md px-4 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:hover:bg-gray-200 dark:text-gray-900"
                    onClick={() => {
                      const newStatus = showScreeningToggleConfirm === 'activate' ? 'active' : 'paused'
                      onJobUpdate?.({ ...job, screeningStatus: newStatus })
                      toast.success(newStatus === 'active' ? 'Triagem ativada com sucesso!' : 'Triagem pausada.')
                      setShowScreeningToggleConfirm(null)
                    }}
                  >
                    {showScreeningToggleConfirm === 'activate' ? 'Ativar' : 'Pausar'}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'configuracoes' && (
            <>
            <Card className="border border-gray-200 dark:border-gray-700">
            {!isEditingScreeningConfig && (
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div className="px-3 py-3 rounded-md border border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                          (job.screeningStatus || 'not_configured') === 'active' ? 'bg-green-100 dark:bg-green-900/30' :
                          (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-amber-100 dark:bg-amber-900/30' :
                          (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-blue-100 dark:bg-blue-900/30' :
                          'bg-gray-100 dark:bg-gray-800'
                        }`}>
                          {(job.screeningStatus || 'not_configured') === 'active' && <Play className="w-3.5 h-3.5 text-green-600" />}
                          {(job.screeningStatus || 'not_configured') === 'paused' && <Pause className="w-3.5 h-3.5 text-amber-600" />}
                          {(job.screeningStatus || 'not_configured') === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-blue-600" />}
                          {(job.screeningStatus || 'not_configured') === 'not_started' && <Clock className="w-3.5 h-3.5 text-gray-500" />}
                          {(job.screeningStatus || 'not_configured') === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 text-gray-400" />}
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">Status da Triagem</span>
                          <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
                            (job.screeningStatus || 'not_configured') === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                            (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                            (job.screeningStatus || 'not_configured') === 'not_started' ? 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300' :
                            'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
                          }`}>
                            {(job.screeningStatus || 'not_configured') === 'active' ? 'Ativa' :
                             (job.screeningStatus || 'not_configured') === 'paused' ? 'Pausada' :
                             (job.screeningStatus || 'not_configured') === 'completed' ? 'Concluída' :
                             (job.screeningStatus || 'not_configured') === 'not_started' ? 'Não Iniciada' :
                             'Não Configurada'}
                          </span>
                        </div>
                      </div>
                      {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
                        <div className="flex items-center gap-2.5 opacity-50 cursor-not-allowed" title="Clique em Editar Configurações para alterar">
                          <span className="text-micro text-gray-400 dark:text-gray-500" style={{ fontFamily: "'Inter', sans-serif" }}>
                            {job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}
                          </span>
                          <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${
                            job.screeningStatus === 'active' ? 'bg-green-400' : 'bg-gray-200 dark:bg-gray-700'
                          }`}>
                            <span
                              className="inline-block h-3.5 w-3.5 transform rounded-full bg-white"
                              style={{ transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)' }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Canais</h3>
                    <div className="border border-gray-100 dark:border-gray-700 rounded-md divide-y divide-gray-100 dark:divide-gray-700">
                      {[
                        { key: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, enabled: screeningConfig?.channels?.whatsapp?.enabled ?? true },
                        { key: 'chat_web', label: 'Chat Web', icon: Globe, enabled: screeningConfig?.channels?.chat_web?.enabled ?? true },
                        { key: 'phone', label: 'Ligação', icon: Phone, enabled: screeningConfig?.channels?.phone?.enabled ?? false },
                      ].map((ch) => {
                        const ChIcon = ch.icon
                        return (
                          <div key={ch.key} className="flex items-center justify-between px-3 py-2">
                            <div className="flex items-center gap-2">
                              <ChIcon className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                              <span className="text-xs font-medium text-gray-600 dark:text-gray-400" style={{ fontFamily: "'Inter', sans-serif" }}>{ch.label}</span>
                              {ch.key === 'phone' && !ch.enabled && (
                                <span className="text-micro text-gray-300 dark:text-gray-600">(Integração pendente)</span>
                              )}
                            </div>
                            <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${ch.enabled ? 'bg-gray-400' : 'bg-gray-200 dark:bg-gray-700'}`}>
                              <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-gray-900 ${ch.enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Configurações</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Score Mínimo Aprovação (WSI)</label>
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { key: 'rigorous', label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                            { key: 'recommended', label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                            { key: 'flexible', label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                          ].map((preset) => {
                            const isSelected = (screeningConfig?.settings?.min_score_preset ?? 'recommended') === preset.key
                            return (
                              <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-gray-300 bg-gray-50/50' : 'border-gray-100 bg-white dark:border-gray-700 dark:bg-gray-800/50'}`}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className={`text-micro font-semibold ${isSelected ? 'text-gray-700' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                  {isSelected && <CheckCircle className="w-3 h-3 text-gray-400 dark:text-gray-500" />}
                                </div>
                                <span className={`text-micro font-medium block ${isSelected ? 'text-gray-600' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.score}</span>
                                <span className="text-micro text-gray-400 dark:text-gray-500 block mt-0.5">{preset.desc}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Timeout Resposta</label>
                          <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                            {screeningConfig?.settings?.response_timeout_hours ?? 48}h
                          </div>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Re-tentativas</label>
                          <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                            {screeningConfig?.settings?.max_retries ?? 2}x
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Prazo da Triagem</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Data Limite</label>
                        <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                          {job.deadlineScreening ? new Date(job.deadlineScreening).toLocaleDateString('pt-BR') : 'Não definido'}
                        </div>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Dias Restantes</label>
                        <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                          {job.deadlineScreening ? (() => { const days = Math.ceil((new Date(job.deadlineScreening).getTime() - Date.now()) / (1000*60*60*24)); return days > 0 ? `${days} dias` : days === 0 ? 'Hoje' : 'Expirado' })() : '—'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Controle de Paralização preview */}
                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldAlert className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Controle de Paralização</span>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Limite de aprovações automáticas</label>
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                            { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                            { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                          ].map((preset) => {
                            const currentPreset = screeningConfig?.settings?.auto_approval_preset ?? 'recommended'
                            const isSelected = currentPreset === preset.key
                            return (
                              <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-gray-300 bg-gray-50/50' : 'border-gray-100 bg-white dark:border-gray-700 dark:bg-gray-800/50'}`}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className={`text-micro font-semibold ${isSelected ? 'text-gray-700' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                  {isSelected && <CheckCircle className="w-3 h-3 text-gray-400 dark:text-gray-500" />}
                                </div>
                                <span className={`text-micro font-medium block ${isSelected ? 'text-gray-600' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.limit}</span>
                                <span className="text-micro text-gray-400 dark:text-gray-500 block mt-0.5">{preset.desc}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                      {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
                        <div className="border border-gray-100 dark:border-gray-700 rounded-md p-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-400 dark:text-gray-500">Progresso atual</span>
                            <span className="text-micro font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Inter', sans-serif" }}>
                              {screeningConfig?.settings?.auto_approvals_count ?? 0}/{screeningConfig?.settings?.auto_approval_limit ?? 10} aprovações
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full mt-1">
                            <div
                              className={`h-1.5 rounded-full transition-all ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= (screeningConfig?.settings?.auto_approval_limit ?? 10) ? 'bg-amber-400' : 'bg-gray-300 dark:bg-gray-600'}`}
                              style={{ width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / (screeningConfig?.settings?.auto_approval_limit ?? 10)) * 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      {screeningConfig?.settings?.auto_approval_paused && (
                        <div className="flex items-center gap-1.5 px-2 py-1.5 bg-amber-50/50 dark:bg-amber-900/10 rounded text-amber-600 dark:text-amber-500">
                          <AlertTriangle className="w-3 h-3" />
                          <span className="text-micro font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Triagem pausada — limite atingido, aguardando revisão humana</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Agendamento Automático preview */}
                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <CalendarCheck className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Agendamento Automático</span>
                      </div>
                      <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-gray-400' : 'bg-gray-200 dark:bg-gray-700'}`}>
                        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-gray-900 ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </div>
                    </div>
                    {(screeningConfig?.scheduling?.auto_enabled ?? true) && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Score Mínimo para Agendamento (WSI)</label>
                          <div className="grid grid-cols-3 gap-2">
                            {[
                              { key: 'rigorous', label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                              { key: 'recommended', label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                              { key: 'flexible', label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                            ].map((preset) => {
                              const isSelected = (screeningConfig?.scheduling?.min_score_for_auto_preset ?? 'recommended') === preset.key
                              return (
                                <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-gray-300 bg-gray-50/50' : 'border-gray-100 bg-white dark:border-gray-700 dark:bg-gray-800/50'}`}>
                                  <div className="flex items-center justify-between mb-0.5">
                                    <span className={`text-micro font-semibold ${isSelected ? 'text-gray-700' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                    {isSelected && <CheckCircle className="w-3 h-3 text-gray-400 dark:text-gray-500" />}
                                  </div>
                                  <span className={`text-micro font-medium block ${isSelected ? 'text-gray-600' : 'text-gray-400 dark:text-gray-500'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.score}</span>
                                  <span className="text-micro text-gray-400 dark:text-gray-500 block mt-0.5">{preset.desc}</span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Calendário</label>
                            <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                              {screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}
                            </div>
                          </div>
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Horários</label>
                            <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                              {screeningConfig?.scheduling?.available_hours || '9h-18h'}
                            </div>
                            {(screeningConfig?.scheduling?.available_hours_inherited ?? true) && (
                              <span className="text-micro text-gray-300 dark:text-gray-600 mt-0.5 block">Conforme config. da empresa</span>
                            )}
                          </div>
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Duração</label>
                            <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 opacity-60">
                              {screeningConfig?.scheduling?.interview_duration_min ?? 60}min
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            )}

            {isEditingScreeningConfig && (
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div className="px-3 py-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                          (job.screeningStatus || 'not_configured') === 'active' ? 'bg-green-100 dark:bg-green-900/30' :
                          (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-amber-100 dark:bg-amber-900/30' :
                          (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-blue-100 dark:bg-blue-900/30' :
                          'bg-gray-100 dark:bg-gray-800'
                        }`}>
                          {(job.screeningStatus || 'not_configured') === 'active' && <Play className="w-3.5 h-3.5 text-green-600" />}
                          {(job.screeningStatus || 'not_configured') === 'paused' && <Pause className="w-3.5 h-3.5 text-amber-600" />}
                          {(job.screeningStatus || 'not_configured') === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-blue-600" />}
                          {(job.screeningStatus || 'not_configured') === 'not_started' && <Clock className="w-3.5 h-3.5 text-gray-500" />}
                          {(job.screeningStatus || 'not_configured') === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 text-gray-400" />}
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">Status da Triagem</span>
                          <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
                            (job.screeningStatus || 'not_configured') === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                            (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                            (job.screeningStatus || 'not_configured') === 'not_started' ? 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300' :
                            'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
                          }`}>
                            {(job.screeningStatus || 'not_configured') === 'active' ? 'Ativa' :
                             (job.screeningStatus || 'not_configured') === 'paused' ? 'Pausada' :
                             (job.screeningStatus || 'not_configured') === 'completed' ? 'Concluída' :
                             (job.screeningStatus || 'not_configured') === 'not_started' ? 'Não Iniciada' :
                             'Não Configurada'}
                          </span>
                        </div>
                      </div>
                      {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
                        <div className="flex items-center gap-2.5">
                          <span className="text-micro text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Inter', sans-serif" }}>
                            {job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}
                          </span>
                          <button
                            onClick={() => {
                              if (job.screeningStatus === 'active') {
                                setShowScreeningToggleConfirm('pause')
                              } else {
                                setShowScreeningToggleConfirm('activate')
                              }
                            }}
                            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 ${
                              job.screeningStatus === 'active' ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                            }`}
                          >
                            <span
                              className="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform duration-200"
                              style={{ transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)' }}
                            />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Canais</h3>
                    <div className="border border-gray-200 dark:border-gray-600 rounded-md divide-y divide-gray-200 dark:divide-gray-600">
                      {[
                        { key: 'whatsapp' as const, label: 'WhatsApp', icon: MessageSquare },
                        { key: 'chat_web' as const, label: 'Chat Web', icon: Globe },
                        { key: 'phone' as const, label: 'Ligação', icon: Phone },
                      ].map((ch) => {
                        const ChIcon = ch.icon
                        const enabled = editChannels[ch.key]
                        return (
                          <div key={ch.key} className="flex items-center justify-between px-3 py-2">
                            <div className="flex items-center gap-2">
                              <ChIcon className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                              <span className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Inter', sans-serif" }}>{ch.label}</span>
                              {ch.key === 'phone' && !enabled && (
                                <span className="text-micro text-gray-400 dark:text-gray-500">(Integração pendente)</span>
                              )}
                            </div>
                            <button
                              onClick={() => setEditChannels(prev => ({ ...prev, [ch.key]: !prev[ch.key] }))}
                              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${enabled ? 'bg-gray-900' : 'bg-gray-300 dark:bg-gray-600'}`}
                            >
                              <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-gray-900 transition-transform ${enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Configurações</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Score Mínimo Aprovação (WSI)</label>
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                            { key: 'recommended' as const, label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                            { key: 'flexible' as const, label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                          ].map((preset) => {
                            const isSelected = editMinScorePreset === preset.key
                            return (
                              <button key={preset.key} onClick={() => setEditMinScorePreset(preset.key)} className={`p-2 rounded-md border text-left transition-all ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:hover:border-gray-500'}`}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className={`text-micro font-semibold ${isSelected ? 'text-gray-900' : 'text-gray-600 dark:text-gray-400'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                  {isSelected && <CheckCircle className="w-3 h-3 text-gray-900 dark:text-gray-300" />}
                                </div>
                                <span className="text-micro font-medium text-gray-800 dark:text-gray-200 block" style={{ fontFamily: "'Inter', sans-serif" }}>{preset.score}</span>
                                <span className="text-micro text-gray-500 dark:text-gray-400 block mt-0.5">{preset.desc}</span>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Timeout Resposta</label>
                          <select value={editTimeoutHours} onChange={(e) => setEditTimeoutHours(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                            {[12, 24, 48, 72].map(h => (<option key={h} value={h}>{h}h</option>))}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Re-tentativas</label>
                          <select value={editMaxRetries} onChange={(e) => setEditMaxRetries(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                            {[1, 2, 3, 4, 5].map(n => (<option key={n} value={n}>{n}x</option>))}
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Controle de Paralização editing */}
                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldAlert className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Controle de Paralização</span>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Limite de aprovações automáticas</label>
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                            { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                            { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                          ].map((preset) => {
                            const isSelected = editAutoApprovalPreset === preset.key
                            return (
                              <button key={preset.key} onClick={() => setEditAutoApprovalPreset(preset.key)} className={`p-2 rounded-md border text-left transition-all ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:hover:border-gray-500'}`}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className={`text-micro font-semibold ${isSelected ? 'text-gray-900' : 'text-gray-600 dark:text-gray-400'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                  {isSelected && <CheckCircle className="w-3 h-3 text-gray-900 dark:text-gray-300" />}
                                </div>
                                <span className="text-micro font-medium text-gray-800 dark:text-gray-200 block" style={{ fontFamily: "'Inter', sans-serif" }}>{preset.limit}</span>
                                <span className="text-micro text-gray-500 dark:text-gray-400 block mt-0.5">{preset.desc}</span>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                      {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
                        <div className="border border-gray-200 dark:border-gray-600 rounded-md p-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500 dark:text-gray-400">Progresso atual</span>
                            <span className="text-micro font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: "'Inter', sans-serif" }}>
                              {screeningConfig?.settings?.auto_approvals_count ?? 0}/{approvalPresetToLimit(editAutoApprovalPreset)} aprovações
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full mt-1">
                            <div
                              className={`h-1.5 rounded-full transition-all ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= approvalPresetToLimit(editAutoApprovalPreset) ? 'bg-amber-500' : 'bg-gray-400 dark:bg-gray-500'}`}
                              style={{ width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / approvalPresetToLimit(editAutoApprovalPreset)) * 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      {screeningConfig?.settings?.auto_approval_paused && (
                        <div className="flex items-center gap-1.5 px-2 py-1.5 bg-amber-50 dark:bg-amber-900/20 rounded text-amber-700 dark:text-amber-400">
                          <AlertTriangle className="w-3 h-3" />
                          <span className="text-micro font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Triagem pausada — limite atingido</span>
                          <button onClick={() => {}} className="ml-auto text-micro font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 underline" style={{ fontFamily: "'Inter', sans-serif" }}>
                            Retomar
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Prazo da Triagem</span>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Data Limite</label>
                      <input
                        type="date"
                        value={job.deadlineScreening ? new Date(job.deadlineScreening).toISOString().split('T')[0] : ''}
                        onChange={(e) => onJobUpdate?.({ ...job, deadlineScreening: e.target.value || null })}
                        className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
                      />
                    </div>
                  </div>

                  {/* Agendamento editing */}
                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <CalendarCheck className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif]">Agendamento Automático</span>
                      </div>
                      <button
                        onClick={() => setEditSchedulingEnabled(!editSchedulingEnabled)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${editSchedulingEnabled ? 'bg-gray-900' : 'bg-gray-300 dark:bg-gray-600'}`}
                      >
                        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-gray-900 transition-transform ${editSchedulingEnabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </button>
                    </div>
                    {editSchedulingEnabled && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Score Mínimo para Agendamento (WSI)</label>
                          <div className="grid grid-cols-3 gap-2">
                            {[
                              { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                              { key: 'recommended' as const, label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                              { key: 'flexible' as const, label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                            ].map((preset) => {
                              const isSelected = editSchedulingMinScorePreset === preset.key
                              return (
                                <button key={preset.key} onClick={() => setEditSchedulingMinScorePreset(preset.key)} className={`p-2 rounded-md border text-left transition-all ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:hover:border-gray-500'}`}>
                                  <div className="flex items-center justify-between mb-0.5">
                                    <span className={`text-micro font-semibold ${isSelected ? 'text-gray-900' : 'text-gray-600 dark:text-gray-400'}`} style={{ fontFamily: "'Inter', sans-serif" }}>{preset.label}</span>
                                    {isSelected && <CheckCircle className="w-3 h-3 text-gray-900 dark:text-gray-300" />}
                                  </div>
                                  <span className="text-micro font-medium text-gray-800 dark:text-gray-200 block" style={{ fontFamily: "'Inter', sans-serif" }}>{preset.score}</span>
                                  <span className="text-micro text-gray-500 dark:text-gray-400 block mt-0.5">{preset.desc}</span>
                                </button>
                              )
                            })}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Calendário</label>
                            <select value={editCalendarProvider} onChange={(e) => setEditCalendarProvider(e.target.value)} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                              <option value="Microsoft">Microsoft</option>
                              <option value="Google">Google</option>
                              <option value="Outlook">Outlook</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Horários</label>
                            <div className="flex items-center gap-2">
                              <input type="text" value={editAvailableHours} onChange={(e) => { setEditAvailableHours(e.target.value); setEditAvailableHoursInherited(false) }} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors" />
                            </div>
                            {editAvailableHoursInherited && (
                              <span className="text-micro text-gray-400 dark:text-gray-500 mt-0.5 block">Conforme config. da empresa</span>
                            )}
                          </div>
                          <div>
                            <label className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block mb-2">Duração</label>
                            <select value={editInterviewDuration} onChange={(e) => setEditInterviewDuration(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                              {[30, 45, 60, 90].map(d => (<option key={d} value={d}>{d}min</option>))}
                            </select>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                </div>
              </CardContent>
            )}
            </Card>
            </>
          )}

          {activeSection === 'descricao' && (
            <div>
              <div className="flex-1 min-w-0">
            <JDEvaluationPanel
              className="!mx-0 !mt-0"
              jobTitle={job.title}
              responsibilities={job.requirements || []}
              technicalSkills={(job.technicalRequirements || []).map((r: any) => r.technology || r.skill || r.name || (typeof r === 'string' ? r : '')).filter(Boolean)}
              behavioralCompetencies={(job.behavioralCompetencies || []).map((c: any) => c.competency || c.name || (typeof c === 'string' ? c : '')).filter(Boolean)}
              seniority={job.level || job.seniority}
              department={job.department}
              description={job.description}
              hasQuestions={(job.screeningQuestions?.length || 0) > 0}
              onGenerateQuestions={async () => {
                setActiveSection('perguntas')
                toast.success('Acesse "Perguntas de Triagem" para gerar as perguntas WSI e escolher o modo (Compacto ou Completo).')
              }}
              enrichedJd={job.enrichedJd}
              onSaveEnrichedJD={async (enrichedData) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                try {
                  await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enriched_jd: enrichedData })
                  })
                  onJobUpdate?.({ ...job, enrichedJd: enrichedData })
                } catch (error) {
                  console.error('Error saving enriched JD:', error)
                  throw error
                }
              }}
              onUpdateOfficialJD={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                try {
                  await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      description: updates.description,
                      requirements: updates.requirements,
                      technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })),
                      behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })),
                    })
                  })
                  onJobUpdate?.({
                    ...job,
                    description: updates.description || job.description,
                    requirements: updates.requirements || job.requirements,
                    technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements,
                    behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies,
                  })
                } catch (error) {
                  console.error('Error updating official JD:', error)
                  throw error
                }
              }}
              onSaveJDInline={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                try {
                  await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      description: updates.description,
                      requirements: updates.requirements,
                      technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })),
                      behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })),
                    })
                  })
                  onJobUpdate?.({
                    ...job,
                    description: updates.description || job.description,
                    requirements: updates.requirements || job.requirements,
                    technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements,
                    behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies,
                  })
                } catch (error) {
                  console.error('Error saving JD inline:', error)
                  throw error
                }
              }}
              isGenerating={isGeneratingWSI}
              companyId={(job as any).companyId || 'default'}
              companyName={(job as any).companyName || undefined}
              companyDescription={undefined}
              companyIndustry={(job as any).industry || undefined}
              benefits={job.benefits || []}
              interviewStages={((job as any).interviewStages || []).map((s: any) => typeof s === 'string' ? s : s.stageName || s.name || '')}
              onUpdateJobDescription={async (jdText) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                try {
                  await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: jdText })
                  })
                  onJobUpdate?.({ ...job, description: jdText })
                } catch (error) {
                  console.error('Error updating job description:', error)
                  throw error
                }
              }}
            />
              </div>
            </div>
          )}

          {activeSection === 'perguntas' && (
            <Card className="border border-gray-200 dark:border-gray-700">
            {!isEditingScreening && (
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider font-['Open_Sans',sans-serif] mb-3">Blocos WSI</h4>
                    <div className="flex items-center gap-3 text-micro text-gray-600 dark:text-gray-400 flex-wrap mb-3">
                      <span>Total: {job.screeningQuestions?.length || 0} perguntas WSI</span>
                      <span>•</span>
                      <span>{(job.screeningQuestions || []).filter((q: any) => q.type === 'eliminatory' || q.required).length} eliminatórias</span>
                      <span>•</span>
                      <span>{(job.screeningQuestions || []).filter((q: any) => q.type !== 'eliminatory' && !q.required).length} informativas</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {WSI_BLOCKS.map((block) => {
                      const blockQuestions = (job.screeningQuestions || []).filter((q: any) => q.block_id === block.id)
                      const isAutomatic = !block.editable
                      const block2Count = block.id === 2 ? (companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length : 0
                      const totalBlockCount = block.id === 2 ? block2Count + blockQuestions.length : blockQuestions.length
                      return (
                        <div key={block.id} className={`px-3 py-2 rounded-md ${isAutomatic ? 'bg-gray-50/50 border border-gray-100' : totalBlockCount > 0 ? 'bg-white border border-gray-100' : 'bg-white border border-gray-200 border-dashed/50 dark:border-gray-600'}`}>
                          <div className="flex items-center gap-2">
                            <span className={`text-micro font-semibold rounded-full w-5 h-5 flex items-center justify-center shrink-0 ${isAutomatic ? 'bg-gray-100' : 'text-gray-400 dark:text-gray-400 dark:bg-gray-700'}`}>{block.id}</span>
                            <span className={`text-xs font-medium ${isAutomatic ? 'text-gray-500' : 'text-gray-800 dark:text-gray-200'}`}>{block.name}</span>
                            {isAutomatic ? (
                              <span className="text-micro px-1.5 py-0.5 bg-gray-100 text-gray-400 rounded-full font-medium uppercase tracking-wide dark:bg-gray-700 dark:text-gray-500">Automático</span>
                            ) : totalBlockCount > 0 ? (
                              <span className="text-micro text-gray-500 dark:text-gray-400">({totalBlockCount} {totalBlockCount === 1 ? 'pergunta' : 'perguntas'})</span>
                            ) : (
                              <span className="text-micro text-gray-400 italic dark:text-gray-500">Nenhuma pergunta</span>
                            )}
                          </div>
                          {block.id === 2 && (
                            <div className="mt-2 ml-7 space-y-3">
                              {companyQuestions.length > 0 && (
                                <CompanyDefaultQuestions
                                  questions={companyQuestions}
                                  disabledIds={disabledCompanyQIds}
                                  isEditing={false}
                                  onToggle={handleToggleCompanyDefault}
                                />
                              )}
                              {selectedBankQuestions.length > 0 && (
                                <>
                                  <div className="border-t border-gray-100 dark:border-gray-800" />
                                  <CompanyBankQuestions
                                    isEditing={false}
                                    selectedQuestions={selectedBankQuestions}
                                    questionOverrides={bankQuestionOverrides}
                                    onToggleQuestion={handleToggleBankQuestion}
                                  />
                                </>
                              )}
                              {customQuestions.length > 0 && (
                                <>
                                  <div className="border-t border-gray-100 dark:border-gray-800" />
                                  <CustomQuestions
                                    isEditing={false}
                                    questions={customQuestions}
                                    onAddQuestion={handleAddCustomQuestion}
                                    onRemoveQuestion={handleRemoveCustomQuestion}
                                    onUpdateQuestion={handleUpdateCustomQuestion}
                                  />
                                </>
                              )}
                            </div>
                          )}
                          {!isAutomatic && block.id !== 2 && blockQuestions.length > 0 && (
                            <div className="space-y-1 ml-7 mt-1.5">
                              {blockQuestions.map((q: any, idx: number) => (
                                <p key={q.id || idx} className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed truncate">
                                  • {q.question || q.text}
                                </p>
                              ))}
                            </div>
                          )}
                          {isAutomatic && WSI_AUTOMATIC_MESSAGES[block.id] && (
                            <div className="ml-7 mt-1.5">
                              <p className="text-micro font-medium text-gray-500 dark:text-gray-400 mb-1">{WSI_AUTOMATIC_MESSAGES[block.id].title}</p>
                              <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg px-2.5 py-2">
                                <p className="text-micro text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}</p>
                              </div>
                              <p className="text-micro text-gray-400 dark:text-gray-500 mt-1 italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                            </div>
                          )}
                          {isAutomatic && !WSI_AUTOMATIC_MESSAGES[block.id] && (
                            <p className="text-micro text-gray-400 dark:text-gray-500 ml-7 mt-0.5">{block.description}</p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </CardContent>
            )}

            {/* Editing Mode */}
            {isEditingScreening && (
              <>
                <div className="px-5 py-3 border-t border-gray-200 bg-gray-50/30">
                  {(() => {
                    const techSkillsCount = (job?.technicalRequirements || []).filter(Boolean).length
                    const behavCompCount = (job?.behavioralCompetencies || []).filter(Boolean).length
                    const showTechWarning = techSkillsCount < 9
                    const showBehavWarning = behavCompCount < 5
                    const showFullDisabled = techSkillsCount < 5
                    if (showTechWarning || showBehavWarning) {
                      return (
                        <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800 px-3 py-2.5">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                            <div className="space-y-1">
                              {showTechWarning && (
                                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                                  {techSkillsCount === 0
                                    ? 'Nenhuma competência técnica cadastrada — adicione competências na seção Job Description para gerar perguntas de triagem.'
                                    : `Apenas ${techSkillsCount} competência${techSkillsCount === 1 ? '' : 's'} técnica${techSkillsCount === 1 ? '' : 's'} cadastrada${techSkillsCount === 1 ? '' : 's'}. Para triagem completa, recomendamos pelo menos 9.`
                                  }
                                </p>
                              )}
                              {showBehavWarning && (
                                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                                  {behavCompCount === 0
                                    ? 'Nenhuma competência comportamental cadastrada — a triagem usará avaliação padrão.'
                                    : `${behavCompCount} competência${behavCompCount === 1 ? '' : 's'} comportamental${behavCompCount === 1 ? '' : 's'} (recomendado: 5 para cobertura completa).`
                                  }
                                </p>
                              )}
                              {showFullDisabled && (
                                <p className="text-micro text-amber-600 dark:text-amber-500 italic">
                                  Modo Completo requer pelo menos 5 competências técnicas.
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}
                  <div className="flex items-center gap-2">
                    <button onClick={handleGenerateWSI('compact')} disabled={isGeneratingWSI} className={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-all disabled:opacity-50 ${wsiGenerationMode === 'compact' ? 'bg-gray-900 text-white border-gray-900 ring-2 ring-gray-900/20 ring-offset-1 dark:ring-gray-100/20' : 'bg-white text-gray-900 border-gray-300 hover:bg-gray-50 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-700'}`}>
                      {isGeneratingWSI && wsiGenerationMode === 'compact' ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <>
                          <span className="text-xs font-semibold">Gerar WSI Compacto</span>
                          <span className={`text-micro ${wsiGenerationMode === 'compact' ? 'text-gray-400' : 'text-gray-500'}`}>~7 perguntas · 12 min</span>
                        </>
                      )}
                    </button>
                    <div className="relative flex-1 group/full">
                      <button onClick={handleGenerateWSI('full')} disabled={isGeneratingWSI || (job?.technicalRequirements || []).filter(Boolean).length < 5} className={`w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-all disabled:opacity-50 ${wsiGenerationMode === 'full' ? 'bg-gray-900 text-white border-gray-900 ring-2 ring-gray-900/20 ring-offset-1 dark:ring-gray-100/20' : 'bg-white text-gray-900 border-gray-300 hover:bg-gray-50 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-700'}`}>
                        {isGeneratingWSI && wsiGenerationMode === 'full' ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <>
                            <span className="text-xs font-semibold">Gerar WSI Completo</span>
                            <span className={`text-micro ${wsiGenerationMode === 'full' ? 'text-gray-400' : 'text-gray-500'}`}>~12 perguntas · 22 min</span>
                          </>
                        )}
                      </button>
                      {(job?.technicalRequirements || []).filter(Boolean).length < 5 && (
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-52 p-2 bg-gray-900 text-white text-micro rounded-md opacity-0 invisible group-hover/full:opacity-100 group-hover/full:visible transition-all z-50 text-center">
                          <p className="leading-relaxed">Adicione pelo menos 5 competências técnicas na seção Job Description para habilitar o modo Completo.</p>
                          <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
                        </div>
                      )}
                    </div>
                    <div className="relative group">
                      <Brain className="w-5 h-5 cursor-help text-wedo-cyan" />
                      <div className="absolute right-full mr-2 top-1/2 -translate-y-1/2 w-64 p-3 bg-gray-900 text-white text-xs rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                        <p className="leading-relaxed">A LIA gera perguntas seguindo a metodologia WeDoTalent Skill Index, calibrando complexidade conforme senioridade e skills da vaga.</p>
                        <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
                      </div>
                    </div>
                  </div>

                  {/* WSI Generation Progress */}
                  {(isGeneratingWSI || wsiGenerationCompleted) && wsiGenerationStep > 0 && (
                    <div className="mt-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
                      <div className="flex items-center gap-3 px-5 py-3 cursor-pointer" onClick={() => setWsiProgressCollapsed(!wsiProgressCollapsed)}>
                        <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0">
                          {wsiGenerationStep < 4 ? (
                            <Loader2 className="w-5 h-5 text-gray-900 dark:text-gray-100 animate-spin" />
                          ) : (
                            <Brain className="w-5 h-5 text-wedo-cyan" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-base-ui font-semibold text-gray-800">
                            {wsiGenerationStep < 4 ? 'Gerando Roteiro e Perguntas de Triagem...' : 'Roteiro e Perguntas de Triagem'}
                          </p>
                          <p className="text-xs text-gray-600 mt-0.5">
                            {wsiGenerationStep < 4
                              ? `Analisando ${wsiGenerationMode === 'compact' ? 'modo compacto' : 'modo completo'}`
                              : `Status: ${wsiGeneratedCount} perguntas geradas · Metodologia WeDoTalent Skill Index (WSI) Completa`
                            }
                          </p>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {wsiGenerationStep >= 4 && (
                            <button onClick={(e) => { e.stopPropagation(); setWsiGenerationCompleted(false); setWsiGenerationStep(0); setWsiDynamicMessage(''); setWsiGenerationContext(null) }} className="p-1 hover:bg-gray-100 rounded transition-colors">
                              <X className="w-3.5 h-3.5 text-gray-400" />
                            </button>
                          )}
                          {wsiProgressCollapsed ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronUp className="w-4 h-4 text-gray-400" />}
                        </div>
                      </div>

                      <div className="px-5 py-4">
                        <div className="flex items-start">
                          {[
                            { num: 1, label: 'Análise' },
                            { num: 2, label: 'Critérios' },
                            { num: 3, label: 'Metodologias' },
                            { num: 4, label: 'Resultado' },
                          ].map((step, idx, arr) => (
                            <React.Fragment key={step.num}>
                              <div className="flex flex-col items-center" style={{ minWidth: '56px' }}>
                                <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 ${
                                  (wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted))
                                    ? 'text-white'
                                    : wsiGenerationStep === step.num
                                      ? 'border-2 bg-white'
                                      : 'border border-gray-300 bg-white'
                                } ${(wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted)) ? 'bg-wedo-cyan' : wsiGenerationStep === step.num ? 'border-wedo-cyan' : ''}`}>
                                  {(wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted)) ? (
                                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                  ) : wsiGenerationStep === step.num ? (
                                    <Loader2 className="w-3 h-3 animate-spin text-wedo-cyan" />
                                  ) : (
                                    <span className="text-micro font-semibold text-gray-400">{step.num}</span>
                                  )}
                                </div>
                                <span className={`text-micro mt-1.5 font-medium whitespace-nowrap transition-colors duration-300 ${wsiGenerationStep >= step.num ? 'text-wedo-cyan-dark' : 'text-gray-400'}`}>
                                  {step.label}
                                </span>
                              </div>
                              {idx < arr.length - 1 && (
                                <div className="flex-1 flex items-center" style={{ marginTop: '11px' }}>
                                  <div className={`w-full h-0.5 rounded-full transition-all duration-700 ${wsiGenerationStep > step.num ? 'bg-wedo-cyan' : 'bg-gray-200'}`} />
                                </div>
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>

                      {wsiGenerationStep < 4 && wsiTypedMessage && (
                        <div className="px-5 pb-3 flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-gray-900 dark:bg-gray-100 animate-pulse" />
                          <p className="text-base-ui text-gray-800">
                            {wsiTypedMessage}
                            {wsiTypedMessage.length < wsiDynamicMessage.length && (
                              <span className="inline-block w-[2px] h-[14px] bg-gray-900 dark:bg-gray-100 ml-0.5 align-middle animate-pulse" />
                            )}
                          </p>
                        </div>
                      )}

                      {!wsiProgressCollapsed && (
                        <div className="px-5 pb-4 pt-1 space-y-3 border-t border-gray-100 dark:border-gray-700">
                          {wsiGenerationStep >= 1 && wsiGenerationContext && (
                            <div className="pt-2">
                              <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-0.5">Cargo analisado</p>
                              <p className="text-xs text-gray-800">
                                {wsiGenerationContext.title}{wsiGenerationContext.seniority ? <span className="text-gray-600 dark:text-gray-400"> · {wsiGenerationContext.seniority}</span> : ''}
                              </p>
                            </div>
                          )}

                          {wsiGenerationStep >= 2 && wsiGenerationContext && (
                            <div className="space-y-2">
                              {wsiGenerationContext.responsibilities.length > 0 && (
                                <div>
                                  <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Responsabilidades Chave</p>
                                  <div className="flex flex-wrap gap-1">
                                    {wsiGenerationContext.responsibilities.map((resp: string, i: number) => (
                                      <span key={`resp-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">
                                        {resp.length > 35 ? resp.slice(0, 35) + '...' : resp}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {wsiGenerationContext.technicalSkills.length > 0 && (
                                <div>
                                  <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Competências Técnicas</p>
                                  <div className="flex flex-wrap gap-1">
                                    {wsiGenerationContext.technicalSkills.map((skill: string, i: number) => (
                                      <span key={`tech-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">{skill}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {wsiGenerationContext.behavioralCompetencies.length > 0 && (
                                <div>
                                  <p className="text-micro font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Competências Comportamentais</p>
                                  <div className="flex flex-wrap gap-1">
                                    {wsiGenerationContext.behavioralCompetencies.map((comp: string, i: number) => (
                                      <span key={`behav-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">{comp}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {wsiGenerationStep >= 3 && (
                            <div>
                              <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Metodologias Utilizadas para Gerar Perguntas</p>
                              {wsiGenerationStep >= 4 && wsiGenerationContext?.methodologyBreakdown && Object.keys(wsiGenerationContext.methodologyBreakdown).length > 0 ? (
                                <p className="text-xs text-gray-700">
                                  {Object.entries(wsiGenerationContext.methodologyBreakdown)
                                    .filter(([key]) => key !== 'Dreyfus')
                                    .map(([method, count]) => {
                                      const labels: Record<string, string> = { 'CBI': 'CBI', 'Bloom': 'Bloom', 'BigFive': 'Big Five' }
                                      return `${labels[method] || method} (${count as number})`
                                    }).join(' · ')}
                                  {wsiGenerationContext.methodologyBreakdown['Dreyfus'] ? ' · Dreyfus (calibração)' : ''}
                                </p>
                              ) : (
                                <div className="flex flex-wrap gap-1.5">
                                  {['CBI', 'Bloom', 'Big Five', 'Dreyfus'].map(m => (
                                    <span key={m} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-full">{m}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {wsiGenerationStep >= 4 && wsiGenerationContext && (
                            <div className="space-y-4 pt-1">
                              <div>
                                <p className="text-base-ui text-gray-800">
                                  {wsiSummaryTypedText}
                                  {!wsiSummaryTypingDone && (
                                    <span className="inline-block w-[2px] h-[14px] bg-gray-900 dark:bg-gray-100 ml-0.5 align-middle animate-pulse" />
                                  )}
                                </p>
                              </div>

                              {wsiSummaryTypingDone && (<>
                                <div className="space-y-1.5 pl-1">
                                  {(wsiGenerationContext.blockBreakdown?.[2] || 0) > 0 && (
                                    <div className="flex items-start gap-2">
                                      <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                                      <p className="text-base-ui text-gray-800">
                                        <span className="font-semibold">{wsiGenerationContext.blockBreakdown[2]} perguntas de elegibilidade</span>, para validar aderência mínima ao cargo
                                      </p>
                                    </div>
                                  )}
                                  {(wsiGenerationContext.blockBreakdown?.[3] || 0) > 0 && (
                                    <div className="flex items-start gap-2">
                                      <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                                      <p className="text-base-ui text-gray-800">
                                        <span className="font-semibold">{wsiGenerationContext.blockBreakdown[3]} perguntas técnicas</span>, para investigar o nível de conhecimento e experiência prática
                                      </p>
                                    </div>
                                  )}
                                  {(wsiGenerationContext.blockBreakdown?.[4] || 0) > 0 && (
                                    <div className="flex items-start gap-2">
                                      <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                                      <p className="text-base-ui text-gray-800">
                                        <span className="font-semibold">{wsiGenerationContext.blockBreakdown[4]} perguntas comportamentais</span>, para explorar as competências exigidas para a vaga
                                      </p>
                                    </div>
                                  )}
                                </div>

                                <div className="space-y-1">
                                  <p className="text-base-ui text-gray-800">
                                    Ao todo, a triagem será composta por <span className="font-semibold">{wsiGeneratedCount} perguntas</span>.
                                  </p>
                                  <p className="text-base-ui text-gray-800">
                                    O tempo médio estimado de triagem é de <span className="font-semibold">15 a 20 minutos</span>, considerando o tempo de leitura e resposta do candidato.
                                  </p>
                                </div>

                                {!wsiSummaryExpanded ? (
                                  <button onClick={() => setWsiSummaryExpanded(true)} className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 transition-colors">
                                    <ChevronDown className="w-3.5 h-3.5" />
                                    Ver detalhes completos
                                  </button>
                                ) : (
                                  <>
                                    <div>
                                      <p className="text-base-ui font-semibold text-gray-900 mb-1">Próximo passo</p>
                                      <p className="text-base-ui text-gray-800">Selecione as perguntas em cada um dos blocos abaixo.</p>
                                    </div>
                                    <div className="space-y-1.5">
                                      <p className="text-base-ui text-gray-800">
                                        As perguntas foram geradas com base na metodologia <span className="font-semibold text-gray-900 dark:text-gray-50">WeDoTalent Skill Index</span>, considerando:
                                      </p>
                                      <div className="space-y-0.5 pl-1">
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Senioridade do cargo</p></div>
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Responsabilidades e competências mapeadas</p></div>
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Metodologias de avaliação (CBI, Bloom, Big Five e Dreyfus)</p></div>
                                      </div>
                                    </div>
                                    <p className="text-base-ui text-gray-700">
                                      As perguntas estão organizadas em ordem de prioridade, mas você pode escolher aquelas que julgar mais adequadas ao contexto da vaga.
                                    </p>
                                    <p className="text-base-ui text-gray-800 font-semibold">
                                      Caso deseje perguntas adicionais, utilize a opção de adicionar perguntas personalizadas manualmente em cada bloco.
                                    </p>
                                    <div className="border-t border-gray-100 pt-3">
                                      <p className="text-base-ui font-semibold text-gray-900 mb-1.5">Finalização</p>
                                      <p className="text-base-ui text-gray-800 mb-1">Após concluir a seleção das perguntas:</p>
                                      <div className="space-y-0.5 pl-1">
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">1.</span><p className="text-base-ui text-gray-700">Salve as alterações</p></div>
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">2.</span><p className="text-base-ui text-gray-700">Inicie o disparo da triagem</p></div>
                                        <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">3.</span><p className="text-base-ui text-gray-700">A LIA realizará a avaliação inicial e sinalizará os candidatos aprovados para a próxima etapa</p></div>
                                      </div>
                                    </div>
                                    {wsiGenerationContext.companyStandardFound && (
                                      <div className="flex items-center gap-1.5 pt-1">
                                        <CheckCircle2 className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                                        <span className="text-xs text-gray-600">Perguntas padrão da empresa incluídas</span>
                                      </div>
                                    )}
                                    <button onClick={() => setWsiSummaryExpanded(false)} className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 transition-colors pt-1">
                                      <ChevronUp className="w-3.5 h-3.5" />
                                      Recolher detalhes
                                    </button>
                                  </>
                                )}
                              </>)}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* WSI Blocks Accordion */}
                <div className="px-5 py-5 overflow-y-auto">
                  <div className="space-y-3">
                    {WSI_BLOCKS.map((block) => {
                      const isExpanded = expandedBlocks.includes(block.id)
                      const allQuestions = job.screeningQuestions || []
                      const cat = (q: any) => (q.category || '').toLowerCase()
                      const typ = (q: any) => (q.type || '').toLowerCase()

                      const isBlock2 = (q: any) => {
                        if (typ(q) === 'eliminatory' || q.required) return true
                        if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
                        if (cat(q).includes('fit') && cat(q).includes('básico')) return true
                        if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
                        if (cat(q).includes('experiência') || cat(q).includes('experiencia')) return true
                        return false
                      }
                      const isBlock3 = (q: any) => {
                        if (isBlock2(q)) return false
                        return cat(q).includes('tecn') || cat(q).includes('tech') || cat(q).includes('skill') || cat(q).includes('técnica') || typ(q).includes('tech')
                      }
                      const isBlock4 = (q: any) => {
                        if (isBlock2(q) || isBlock3(q)) return false
                        return true
                      }

                      const blockQuestions = allQuestions.filter((q: any) => {
                        if (q.block_id !== undefined && q.block_id !== null) return q.block_id === block.id
                        if (block.id === 2) return isBlock2(q)
                        if (block.id === 3) return isBlock3(q)
                        if (block.id === 4) return isBlock4(q)
                        return false
                      })

                      const blockGenerated = generatedQuestions[block.id] || []
                      const acceptedCountForBlock = blockGenerated.filter((q: any) => acceptedQuestions.has(q.id)).length
                      const eliminatoryCount = blockQuestions.filter((q: any) => q.type === 'eliminatory' || q.required).length
                      const informativeCount = blockQuestions.length - eliminatoryCount

                      return (
                        <div key={block.id} className={`border rounded-md overflow-hidden ${block.editable ? 'border-gray-200' : 'border-gray-100 bg-gray-50/50 dark:bg-gray-800/30'}`}>
                          <div className={`flex items-center justify-between p-3 cursor-pointer transition-colors ${block.editable ? 'bg-gray-50 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700' : 'bg-gray-100/80 dark:bg-gray-800/50'}`} onClick={() => {
                            if (isExpanded) {
                              setExpandedBlocks(prev => prev.filter(id => id !== block.id))
                            } else {
                              setExpandedBlocks(prev => [...prev, block.id])
                            }
                          }}>
                            <div className="flex items-center gap-2">
                              <span className={`w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center ${block.editable ? 'bg-gray-700' : 'bg-gray-400 dark:bg-gray-600'}`}>{block.id}</span>
                              <div>
                                <span className={`text-xs font-semibold ${block.editable ? 'text-gray-950' : 'text-gray-800 dark:text-gray-200'}`}>{block.name}</span>
                                <span className="text-micro text-gray-600 ml-2">({block.duration})</span>
                              </div>
                              {!block.editable && <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-200 text-gray-600 ml-1">Automático</Badge>}
                            </div>
                            <div className="flex items-center gap-2">
                              {block.editable && blockQuestions.length > 0 && (
                                <>
                                  {eliminatoryCount > 0 && <Badge className="text-micro px-2 py-0.5 bg-red-50 text-red-600 border border-red-200">{eliminatoryCount} Eliminatória{eliminatoryCount > 1 ? 's' : ''}</Badge>}
                                  {informativeCount > 0 && <Badge className="text-micro px-2 py-0.5 bg-gray-100 text-gray-800">{informativeCount} Informativa{informativeCount > 1 ? 's' : ''}</Badge>}
                                </>
                              )}
                              {blockGenerated.length > 0 && (
                                <>
                                  <Badge className="text-micro px-2 py-0.5 bg-gray-100 text-gray-700 border border-gray-200">{acceptedCountForBlock}/{blockGenerated.length} aceitas</Badge>
                                  {acceptedCountForBlock < blockGenerated.length && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>}
                                </>
                              )}
                              {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-600" /> : <ChevronDown className="w-4 h-4 text-gray-600" />}
                            </div>
                          </div>

                          {isExpanded && (
                            <div className={`p-3 space-y-2 ${!block.editable ? 'bg-gray-50/30' : ''}`}>
                              {!block.editable ? (
                                WSI_AUTOMATIC_MESSAGES[block.id] ? (
                                  <div className="rounded-md border border-gray-300 bg-gray-50 dark:bg-gray-800/50 overflow-hidden">
                                    <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-600 bg-gray-100 dark:bg-gray-800">
                                      <p className="text-xs font-medium text-gray-950 dark:text-gray-100">{WSI_AUTOMATIC_MESSAGES[block.id].title}</p>
                                    </div>
                                    <div className="p-3">
                                      <div className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}</div>
                                    </div>
                                    <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50">
                                      <p className="text-micro text-gray-600 dark:text-gray-400 italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="p-3 bg-white/60 border border-gray-100 rounded-md">
                                    <p className="text-xs text-gray-800 italic">{block.description}</p>
                                    <p className="text-micro text-gray-600 mt-1">Este bloco é gerenciado automaticamente pela LIA</p>
                                  </div>
                                )
                              ) : (
                                <>
                                  {block.id === 2 && (
                                    <div className="space-y-4 mb-3">
                                      <CompanyDefaultQuestions
                                        questions={companyQuestions}
                                        disabledIds={disabledCompanyQIds}
                                        isEditing={true}
                                        onToggle={handleToggleCompanyDefault}
                                      />
                                      <div className="border-t border-gray-100 dark:border-gray-800" />
                                      <CompanyBankQuestions
                                        isEditing={true}
                                        selectedQuestions={selectedBankQuestions}
                                        questionOverrides={bankQuestionOverrides}
                                        onToggleQuestion={handleToggleBankQuestion}
                                        onUpdateSelectedQuestion={handleUpdateBankQuestion}
                                        excludeIds={companyQuestions.map(q => q.id)}
                                      />
                                      <div className="border-t border-gray-100 dark:border-gray-800" />
                                      <CustomQuestions
                                        isEditing={true}
                                        questions={customQuestions}
                                        onAddQuestion={handleAddCustomQuestion}
                                        onRemoveQuestion={handleRemoveCustomQuestion}
                                        onUpdateQuestion={handleUpdateCustomQuestion}
                                      />
                                    </div>
                                  )}
                                  {blockQuestions.length === 0 && blockGenerated.length === 0 && block.id !== 2 ? (
                                    <div className="p-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-600 border-dashed rounded-md text-center">
                                      <p className="text-xs text-gray-500">Nenhuma pergunta neste bloco</p>
                                    </div>
                                  ) : block.id !== 2 || blockQuestions.length > 0 || blockGenerated.length > 0 ? (
                                    <>
                                      {blockQuestions.map((item: any, idx: number) => {
                                        const isDeactivated = deactivatedQuestions.has(item.id)
                                        const isDetailsExpanded = expandedQuestionDetails.has(item.id)
                                        const complexity = getBloomComplexity(item.bloom_level || 3)
                                        const estTime = getEstimatedTime(item.question_type || 'open')
                                        return (
                                          <div key={item.id || idx} className={`p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md group hover:border-gray-300 dark:hover:border-gray-600 transition-colors ${isDeactivated ? 'opacity-50' : ''}`}>
                                            <div className="flex items-start gap-3">
                                              <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                                                  <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full ${item.category === 'behavioral' || item.category === 'Comportamental' ? 'bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800' : item.category === 'technical' || item.category === 'Técnica' ? 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800' : 'bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800'}`}>
                                                    {item.category === 'behavioral' ? 'Comportamental' : item.category === 'technical' ? 'Técnica' : item.category === 'cultural' ? 'Cultural' : item.category || 'Geral'}
                                                  </Badge>
                                                  {(item.type === 'eliminatory' || item.required) && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">Eliminatória</Badge>
                                                  )}
                                                  <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full border ${complexity.color}`}>
                                                    <Gauge className="w-3 h-3 mr-0.5" />{complexity.label}
                                                  </Badge>
                                                  {item.bloom_level && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-900/20 dark:text-sky-400 dark:border-sky-800">
                                                      <GraduationCap className="w-3 h-3 mr-0.5" />{getBloomLabelPTBR(item.bloom_level) || item.bloom_label}
                                                    </Badge>
                                                  )}
                                                  {item.dreyfus_level && item.block_id !== 2 && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-900/20 dark:text-violet-400 dark:border-violet-800">
                                                      {getDreyfusLabelPTBR(item.dreyfus_level) || item.dreyfus_label}
                                                    </Badge>
                                                  )}
                                                  {item.big_five_trait && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-900/20 dark:text-pink-400 dark:border-pink-800">
                                                      {getBigFiveLabelPTBR(item.big_five_trait)}
                                                    </Badge>
                                                  )}
                                                  {(item.weight || 0) >= 1.5 && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">
                                                      <ShieldAlert className="w-3 h-3 mr-0.5" />Crítica
                                                    </Badge>
                                                  )}
                                                  {isDeactivated ? (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-gray-100 text-gray-500 border border-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600">Inativa</Badge>
                                                  ) : (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-green-50 text-green-600 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
                                                      <CheckCircle className="w-3 h-3 mr-1" />Aceita
                                                    </Badge>
                                                  )}
                                                </div>
                                                <p className="text-xs text-gray-950 dark:text-gray-50 leading-relaxed">{item.question}</p>
                                                <div className="flex items-center gap-3 mt-2 text-micro text-gray-500 dark:text-gray-400">
                                                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{estTime}</span>
                                                  {item.bloom_label && !item.bloom_level && <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" />Bloom: {item.bloom_label}</span>}
                                                  {(item.trait || item.skill) && <span className="flex items-center gap-1"><Target className="w-3 h-3" />Avalia: {item.trait || item.skill}</span>}
                                                  <span className="flex items-center gap-1"><Scale className="w-3 h-3" />Peso: {((item.weight || 1) * 100).toFixed(0)}%</span>
                                                </div>
                                                <button className="mt-1.5 text-micro text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" onClick={() => setExpandedQuestionDetails(prev => { const next = new Set(prev); next.has(item.id) ? next.delete(item.id) : next.add(item.id); return next })}>
                                                  {isDetailsExpanded ? '▲ Ocultar detalhes' : '▼ Ver detalhes'}
                                                </button>
                                                {isDetailsExpanded && (
                                                  <div className="mt-2 p-2.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700 rounded-lg space-y-1.5 text-micro">
                                                    <div className="flex gap-4">
                                                      <div><span className="text-gray-400">Framework:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.framework === 'Company' ? 'Empresa' : (item.block_id === 2 ? 'Empresa' : (item.framework || 'CBI'))}</span></div>
                                                      <div><span className="text-gray-400">Dreyfus:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.block_id === 2 ? 'Padrão' : (item.dreyfus_label || '—')}</span></div>
                                                      <div><span className="text-gray-400">Tipo:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.question_type === 'yes_no' ? 'Sim/Não' : item.question_type === 'open' ? 'Aberta' : item.question_type || 'Aberta'}</span></div>
                                                    </div>
                                                    {(item.expected_answer || (item.expected_signals && item.expected_signals.length > 0)) && (
                                                      <div><span className="text-gray-400">Resposta esperada:</span><p className="text-gray-700 dark:text-gray-300 mt-0.5">{item.expected_answer || item.expected_signals?.join(', ')}</p></div>
                                                    )}
                                                    {(item.scoring_criteria || item.scoring_rubric) && Object.keys(item.scoring_criteria || item.scoring_rubric).length > 0 && (
                                                      <div><span className="text-gray-400">Critérios de pontuação:</span><div className="mt-0.5 space-y-0.5">{Object.entries(item.scoring_criteria || item.scoring_rubric).map(([level, desc]: [string, any]) => (<div key={level} className="flex gap-1"><span className="text-gray-500 font-medium shrink-0">{level}:</span><span className="text-gray-700 dark:text-gray-300">{desc}</span></div>))}</div></div>
                                                    )}
                                                  </div>
                                                )}
                                              </div>
                                              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button className={`p-1.5 rounded transition-colors ${isDeactivated ? 'hover:bg-green-50' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`} onClick={() => {
                                                  setDeactivatedQuestions(prev => {
                                                    const next = new Set(prev)
                                                    if (next.has(item.id)) { next.delete(item.id); toast.success('Pergunta reativada') } else { next.add(item.id); toast.success('Pergunta arquivada') }
                                                    return next
                                                  })
                                                }} title={isDeactivated ? 'Reativar pergunta' : 'Arquivar pergunta'}>
                                                  <Archive className={`w-3.5 h-3.5 ${isDeactivated ? 'text-green-500' : 'text-gray-400'}`} />
                                                </button>
                                              </div>
                                            </div>
                                          </div>
                                        )
                                      })}

                                      {blockGenerated.map((item: any, idx: number) => {
                                        const isAccepted = acceptedQuestions.has(item.id)
                                        const genComplexity = getBloomComplexity(item.bloom_level || 3)
                                        const genEstTime = getEstimatedTime(item.question_type || 'open')
                                        const genDetailsExpanded = expandedQuestionDetails.has(item.id)
                                        return (
                                          <div key={item.id || `gen-${idx}`} className={`p-3 rounded-md transition-colors ${isAccepted ? 'bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-600' : 'bg-white dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-600'}`}>
                                            <div className="flex items-start gap-3">
                                              <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                                                  <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full ${item.category === 'behavioral' || item.category === 'comportamental' ? 'bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800' : item.category === 'technical' || item.category === 'técnica' ? 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800' : item.category === 'cultural' || item.category === 'fit_cultural' ? 'bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-900/20 dark:text-teal-400 dark:border-teal-800' : 'bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600'}`}>
                                                    {item.category === 'behavioral' || item.category === 'comportamental' ? 'Comportamental' : item.category === 'technical' || item.category === 'técnica' ? 'Técnica' : item.category === 'cultural' || item.category === 'fit_cultural' ? 'Fit Cultural' : item.category || 'Geral'}
                                                  </Badge>
                                                  {(item.type === 'eliminatory' || item.is_eliminatory) && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">Eliminatória</Badge>
                                                  )}
                                                  <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full border ${genComplexity.color}`}>
                                                    <Gauge className="w-3 h-3 mr-0.5" />{genComplexity.label}
                                                  </Badge>
                                                  {item.bloom_level && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-900/20 dark:text-sky-400 dark:border-sky-800">
                                                      <GraduationCap className="w-3 h-3 mr-0.5" />{getBloomLabelPTBR(item.bloom_level) || item.bloom_label}
                                                    </Badge>
                                                  )}
                                                  {item.dreyfus_level && item.block_id !== 2 && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-900/20 dark:text-violet-400 dark:border-violet-800">
                                                      {getDreyfusLabelPTBR(item.dreyfus_level) || item.dreyfus_label}
                                                    </Badge>
                                                  )}
                                                  {item.big_five_trait && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-900/20 dark:text-pink-400 dark:border-pink-800">
                                                      {getBigFiveLabelPTBR(item.big_five_trait)}
                                                    </Badge>
                                                  )}
                                                  {(item.weight || 0) >= 1.5 && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">
                                                      <ShieldAlert className="w-3 h-3 mr-0.5" />Crítica
                                                    </Badge>
                                                  )}
                                                  {isAccepted && (
                                                    <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-green-50 text-green-600 border border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800">
                                                      <CheckCircle className="w-3 h-3 mr-1" />Aceita
                                                    </Badge>
                                                  )}
                                                </div>
                                                <p className="text-xs text-gray-950 dark:text-gray-50 leading-relaxed">{item.question || item.text}</p>
                                                <div className="flex items-center gap-3 mt-2 text-micro text-gray-500 dark:text-gray-400">
                                                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{genEstTime}</span>
                                                  {item.bloom_label && !item.bloom_level && <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" />Bloom: {item.bloom_label}</span>}
                                                  {(item.trait || item.skill) && <span className="flex items-center gap-1"><Target className="w-3 h-3" />Avalia: {item.trait || item.skill}</span>}
                                                  <span className="flex items-center gap-1"><Scale className="w-3 h-3" />Peso: {((item.weight || 1) * 100).toFixed(0)}%</span>
                                                </div>
                                                <button className="mt-1.5 text-micro text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" onClick={() => setExpandedQuestionDetails(prev => { const next = new Set(prev); next.has(item.id) ? next.delete(item.id) : next.add(item.id); return next })}>
                                                  {genDetailsExpanded ? '▲ Ocultar detalhes' : '▼ Ver detalhes'}
                                                </button>
                                                {genDetailsExpanded && (
                                                  <div className="mt-2 p-2.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700 rounded-lg space-y-1.5 text-micro">
                                                    <div className="flex gap-4 flex-wrap">
                                                      <div><span className="text-gray-400">Framework:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.framework === 'Company' ? 'Empresa' : (item.block_id === 2 ? 'Empresa' : (item.framework || 'CBI'))}</span></div>
                                                      <div><span className="text-gray-400">Dreyfus:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.block_id === 2 ? 'Padrão' : (item.dreyfus_label || '—')}</span></div>
                                                      <div><span className="text-gray-400">Tipo:</span><span className="ml-1 text-gray-700 dark:text-gray-300 font-medium">{item.question_type === 'yes_no' ? 'Sim/Não' : item.question_type === 'open' ? 'Aberta' : item.question_type || 'Aberta'}</span></div>
                                                    </div>
                                                    {(item.expected_answer || (item.expected_signals && item.expected_signals.length > 0)) && (
                                                      <div><span className="text-gray-400">Resposta esperada:</span><p className="text-gray-700 dark:text-gray-300 mt-0.5">{item.expected_answer || item.expected_signals?.join(', ')}</p></div>
                                                    )}
                                                    {(item.scoring_criteria || item.scoring_rubric) && Object.keys(item.scoring_criteria || item.scoring_rubric).length > 0 && (
                                                      <div><span className="text-gray-400">Critérios de pontuação:</span><div className="mt-0.5 space-y-0.5">{Object.entries(item.scoring_criteria || item.scoring_rubric).map(([level, desc]: [string, any]) => (<div key={level} className="flex gap-1"><span className="text-gray-500 font-medium shrink-0">{level}:</span><span className="text-gray-700 dark:text-gray-300">{desc}</span></div>))}</div></div>
                                                    )}
                                                  </div>
                                                )}
                                              </div>
                                              <div className="flex items-center gap-1.5 shrink-0">
                                                {isAccepted ? (
                                                  <button className="border border-gray-200 text-gray-500 text-micro px-2 py-1 rounded-full hover:bg-red-50 transition-colors" onClick={() => {
                                                    if (confirm('Remover pergunta aceita?')) {
                                                      setAcceptedQuestions(prev => { const next = new Set(prev); next.delete(item.id); return next })
                                                      setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id] || []).filter((q: any) => q.id !== item.id) }))
                                                    }
                                                  }}>Remover</button>
                                                ) : (
                                                  <>
                                                    <button className="bg-gray-900 text-white text-micro px-2 py-1 rounded-full hover:bg-gray-800 transition-colors" onClick={() => setAcceptedQuestions(prev => new Set(prev).add(item.id))}>Aceitar</button>
                                                    <button className="border border-gray-200 text-gray-500 text-micro px-2 py-1 rounded-full hover:bg-red-50 transition-colors" onClick={() => setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id] || []).filter((q: any) => q.id !== item.id) }))}>Descartar</button>
                                                  </>
                                                )}
                                              </div>
                                            </div>
                                          </div>
                                        )
                                      })}
                                    </>
                                  ) : null}


                                </>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Save/Cancel buttons */}
                <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200 dark:border-gray-700">
                  <Button variant="outline" size="sm" className="h-7 text-micro px-3 border-gray-200 text-gray-600 dark:border-gray-600 dark:text-gray-300" onClick={resetScreeningEditing}>
                    Cancelar
                  </Button>
                  <div className="flex items-center gap-2">
                    <Button size="sm" className="h-7 text-micro px-4 bg-gray-900 hover:bg-gray-800 text-white" onClick={async () => {
                      const existingCount = (job.screeningQuestions || []).length
                      const acceptedCount = Object.values(generatedQuestions).flat().filter((q: any) => acceptedQuestions.has(q.id)).length
                      const totalQuestions = existingCount + acceptedCount

                      if (totalQuestions === 0) {
                        toast.error('Selecione pelo menos uma pergunta antes de salvar o roteiro.')
                        return
                      }
                      if (totalQuestions < 3) {
                        toast.error('O roteiro precisa ter no mínimo 3 perguntas. Atualmente: ' + totalQuestions)
                        return
                      }

                      try {
                        const jobId = job.backendId || job.jobId || String(job.id)
                        const existingQuestions = (job.screeningQuestions || []).map((q: any) => ({
                          id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id
                        }))
                        const acceptedGenerated: any[] = []
                        Object.values(generatedQuestions).forEach((blockQs: any[]) => {
                          blockQs.forEach((q: any) => {
                            if (acceptedQuestions.has(q.id)) {
                              acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id })
                            }
                          })
                        })
                        const allQuestions = [...existingQuestions, ...acceptedGenerated]
                        const response = await fetch('/api/backend-proxy/wsi/questions/save', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' })
                        })
                        if (response.ok) {
                          const newScreeningQuestions = [
                            ...(job.screeningQuestions || []),
                            ...Object.values(generatedQuestions).flat().filter((q: any) => acceptedQuestions.has(q.id)).map((q: any) => ({
                              ...q, question: q.question || q.text, generated: undefined
                            }))
                          ]
                          onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions })
                          toast.success(`Roteiro salvo com sucesso! ${allQuestions.length} perguntas salvas.`)
                          resetScreeningEditing()
                        } else {
                          toast.error('Erro ao salvar roteiro. Tente novamente.')
                        }
                      } catch (error) {
                        console.error('Error saving screening questions:', error)
                        toast.error('Erro ao salvar roteiro. Tente novamente.')
                      }
                    }}>
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Salvar Alterações
                    </Button>
                    {(job.screeningStatus !== 'active') && (
                      <Button size="sm" className="h-7 text-micro px-4 bg-green-600 hover:bg-green-700 text-white" onClick={async () => {
                        const existingCount = (job.screeningQuestions || []).length
                        const acceptedCount = Object.values(generatedQuestions).flat().filter((q: any) => acceptedQuestions.has(q.id)).length
                        const totalQuestions = existingCount + acceptedCount

                        if (totalQuestions === 0) {
                          toast.error('Selecione pelo menos uma pergunta antes de ativar a triagem.')
                          return
                        }
                        if (totalQuestions < 3) {
                          toast.error('O roteiro precisa ter no mínimo 3 perguntas para ativar. Atualmente: ' + totalQuestions)
                          return
                        }

                        try {
                          const jobId = job.backendId || job.jobId || String(job.id)
                          const existingQuestions = (job.screeningQuestions || []).map((q: any) => ({
                            id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id
                          }))
                          const acceptedGenerated: any[] = []
                          Object.values(generatedQuestions).forEach((blockQs: any[]) => {
                            blockQs.forEach((q: any) => {
                              if (acceptedQuestions.has(q.id)) {
                                acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id })
                              }
                            })
                          })
                          const allQuestions = [...existingQuestions, ...acceptedGenerated]
                          const response = await fetch('/api/backend-proxy/wsi/questions/save', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' })
                          })
                          if (response.ok) {
                            const newScreeningQuestions = [
                              ...(job.screeningQuestions || []),
                              ...Object.values(generatedQuestions).flat().filter((q: any) => acceptedQuestions.has(q.id)).map((q: any) => ({
                                ...q, question: q.question || q.text, generated: undefined
                              }))
                            ]
                            onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions, screeningStatus: 'active' })
                            toast.success(`Roteiro salvo e triagem ativada! ${allQuestions.length} perguntas configuradas.`)
                            resetScreeningEditing()
                          } else {
                            toast.error('Erro ao salvar roteiro. Tente novamente.')
                          }
                        } catch (error) {
                          console.error('Error saving and activating screening:', error)
                          toast.error('Erro ao salvar roteiro. Tente novamente.')
                        }
                      }}>
                        <Play className="w-3 h-3 mr-1" />
                        Salvar e Ativar
                      </Button>
                    )}
                  </div>
                </div>
              </>
            )}
            </Card>
          )}

          {(job.liaMetrics?.triagens_realizadas ?? 0) > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-md dark:bg-amber-900/10 dark:border-amber-800">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
              <p className="text-xs text-amber-700 dark:text-amber-300">
                <span className="font-bold">Triagem em andamento</span> — <span className="font-semibold">{job.liaMetrics?.triagens_realizadas} candidatos</span> já triados. Alterar perguntas pode afetar a comparabilidade entre candidatos.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function ScreeningConfigContent({ job, onJobUpdate, onFormUpdate, activeSection }: ScreeningConfigContentProps) {
  return (
    <ScreeningConfigManager
      job={job}
      onJobUpdate={onJobUpdate}
      onFormUpdate={onFormUpdate}
      _externalActiveSection={activeSection}
      _hideOwnSidebar={true}
    />
  )
}

export default ScreeningConfigManager
