"use client"

import React, { useState, useEffect, useCallback, useRef } from"react"
import { createPortal } from"react-dom"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Textarea } from"@/components/ui/textarea"
import {
  Mail, Phone, MessageSquare, Send, 
  X, Eye, ChevronDown, ChevronUp,
  Info, Loader2,
  ClipboardList, ListChecks, Briefcase
} from"lucide-react"
import { Switch } from"@/components/ui/switch"
import { textStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"
import { MessageComposer } from"@/components/communication"
import { sanitizeHtml } from"@/lib/sanitize"
import { toast } from"sonner"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import type { ScreeningChannelConfig, ScreeningChannelKey, ScreeningConfig } from"@/hooks/recruitment/useScreeningConfig"

/** Subset of ScreeningConfig the invite modal needs to filter channels. */
type InviteChannelsContext = ScreeningChannelConfig & {
  channels?: ScreeningConfig['channels']
  channels_master_enabled?: boolean
}

type ContactChannel = 'email' | 'whatsapp' | 'telefone' | 'voz_web' | 'both'

/**
 * Task #425 — derive list of allowed invite channels strictly from the job's
 * canonical screening channel config. Only enabled channels (and only when
 * the master toggle is on) appear in the picker.
 */
function buildAvailableChannels(cfg?: InviteChannelsContext): ContactChannel[] {
  if (!cfg) return ['email', 'whatsapp', 'telefone', 'voz_web']
  const masterOn = cfg.channels_master_enabled !== false
  if (!masterOn) return []
  const ch = cfg.channels ?? {}
  const out: ContactChannel[] = []
  if (ch.chat_web?.enabled !== false) out.push('email')
  if (ch.whatsapp?.enabled) out.push('whatsapp')
  const pstn = ch.phone_pstn?.enabled ?? ch.phone?.enabled ?? false
  if (pstn) out.push('telefone')
  const voz = ch.voice_web?.enabled ?? ch.voip_web?.enabled ?? true
  if (voz) out.push('voz_web')
  return out
}

/**
 * Task #425 — map canonical screening channel to invite contact channel.
 * The 4 canonical channels (chat_web, whatsapp, phone_pstn, voice_web) each
 * surface as a distinct invite channel — no longer collapsing PSTN with VoIP.
 * Legacy keys (`phone`, `voip_web`) are accepted for backward compat.
 */
function screeningChannelToContact(key: ScreeningChannelKey | 'phone' | 'voip_web'): ContactChannel {
  switch (key) {
    case 'chat_web': return 'email'
    case 'whatsapp': return 'whatsapp'
    case 'phone_pstn':
    case 'phone': return 'telefone'
    case 'voice_web':
    case 'voip_web': return 'voz_web'
    default: return 'email'
  }
}

interface Candidate {
  id: string
  name: string
  role?: string
  email?: string
  phone?: string
  location?: string
  avatar?: string
}

interface ScreeningQuestion {
  id: string
  question: string
  category?: string
  bloomLevel?: number
}

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
}

function usePipelineStages() {
  const t = useTranslations('screening.wsi')
  return [
    { value: 'novo', label: t('invite.stageNew') },
    { value: 'triagem', label: t('invite.stageScreening') },
    { value: 'entrevista', label: t('invite.stageInterview') },
    { value: 'avaliacao', label: t('invite.stageEvaluation') },
    { value: 'oferta', label: t('invite.stageOffer') }
  ]
}

interface WSITriagemInviteModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  jobTitle?: string
  jobId?: string
  screeningQuestions?: ScreeningQuestion[]
  onSend?: (data: Record<string, unknown>) => void
  companyId?: string
  screeningChannels?: InviteChannelsContext
}

function getDefaultScreeningQuestions(t: (key: string) => string): ScreeningQuestion[] {
  return [
    { id: '1', question: t('invite.defaultQuestions.q1'), category: t('invite.defaultQuestions.cat1'), bloomLevel: 4 },
    { id: '2', question: t('invite.defaultQuestions.q2'), category: t('invite.defaultQuestions.cat2'), bloomLevel: 3 },
    { id: '3', question: t('invite.defaultQuestions.q3'), category: t('invite.defaultQuestions.cat3'), bloomLevel: 5 },
    { id: '4', question: t('invite.defaultQuestions.q4'), category: t('invite.defaultQuestions.cat4'), bloomLevel: 3 },
    { id: '5', question: t('invite.defaultQuestions.q5'), category: t('invite.defaultQuestions.cat5'), bloomLevel: 2 },
  ]
}

export function WSITriagemInviteModal({
  isOpen,
  onClose,
  candidate,
  jobTitle: jobTitleProp,
  jobId,
  screeningQuestions: screeningQuestionsProp,
  onSend,
  companyId,
  screeningChannels,
}: WSITriagemInviteModalProps) {
  const t = useTranslations('screening.wsi')
  const screeningQuestions = screeningQuestionsProp ?? getDefaultScreeningQuestions(t)
  const locale = useLocale()
  const PIPELINE_STAGES = usePipelineStages()
  const jobTitle = jobTitleProp || t('invite.jobDefault')
  const availableChannels = buildAvailableChannels(screeningChannels)
  const primaryFromConfig: ContactChannel = screeningChannels?.primary_channel
    ? screeningChannelToContact(screeningChannels.primary_channel)
    : 'email'
  const defaultChannel: ContactChannel =
    availableChannels.includes(primaryFromConfig)
      ? primaryFromConfig
      : (availableChannels[0] ?? 'email')
  const [channel, setChannel] = useState<ContactChannel>(defaultChannel)
  const [showPhoneScript, setShowPhoneScript] = useState(false)
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [showQuestions, setShowQuestions] = useState(true)
  const [mounted, setMounted] = useState(false)
  const messageTextareaRef = useRef<HTMLTextAreaElement>(null)
  
  const [linkToVacancy, setLinkToVacancy] = useState(false)
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null)
  const [selectedStage, setSelectedStage] = useState('triagem')
  const [vacancies, setVacancies] = useState<JobVacancy[]>([])
  const [isLoadingVacancies, setIsLoadingVacancies] = useState(false)
useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  const loadVacancies = useCallback(async () => {
    if (vacancies.length > 0) return
    setIsLoadingVacancies(true)
    try {
      const response = await fetch('/api/backend-proxy/job-vacancies/')
      const data = await response.json()
      const vacancyList = data.vacancies || data.items || data || []
      setVacancies(Array.isArray(vacancyList) ? vacancyList : [])
    } catch (error) {
      setVacancies([])
    } finally {
      setIsLoadingVacancies(false)
    }
  }, [vacancies.length])

  useEffect(() => {
    if (linkToVacancy) {
      loadVacancies()
    }
  }, [linkToVacancy, loadVacancies])

  useEffect(() => {
    if (isOpen && jobId && vacancies.length > 0) {
      const exists = vacancies.some(v => v.id === jobId)
      if (exists) {
        setSelectedVacancyId(jobId)
        setLinkToVacancy(true)
      }
    }
  }, [isOpen, jobId, vacancies])

  const generatePhoneScript = useCallback(() => {
    if (!candidate) return ''
    return t('invite.phoneScriptTemplate', { name: candidate.name, job: jobTitle })
  }, [candidate, jobTitle, t])

  useEffect(() => {
    if (isOpen && candidate && channel === 'telefone' && showPhoneScript) {
      setMessage(generatePhoneScript())
      setSubject('')
    }
  }, [isOpen, channel, candidate, generatePhoneScript, showPhoneScript])

  useEffect(() => {
    if (!isOpen) {
      setChannel(defaultChannel)
      setMessage('')
      setSubject('')
      setShowQuestions(true)
      setLinkToVacancy(false)
      setSelectedVacancyId(null)
      setSelectedStage('triagem')
      setShowPhoneScript(false)
    }
  }, [isOpen, defaultChannel])

  const handleSend = async () => {
    if (!candidate) return
    
    if (linkToVacancy && !selectedVacancyId) {
      toast.error(t('invite.toasts.selectJob'), { description: t('invite.toasts.selectJobDesc') })
      return
    }
    
    if ((channel === 'email' || channel === 'voz_web') && !candidate.email) {
      toast.error(t('invite.toasts.emailNotInformed'), { description: t('invite.toasts.emailNotInformedDesc') })
      return
    }
    
    if ((channel === 'whatsapp' || channel === 'telefone') && !candidate.phone) {
      toast.error(t('invite.toasts.phoneNotInformed'), { description: t('invite.toasts.phoneNotInformedDesc') })
      return
    }
    
    setIsSending(true)
    
    try {
      if (linkToVacancy && selectedVacancyId) {
        try {
          const response = await fetch(`/api/backend-proxy/search/vacancy/${selectedVacancyId}/add-candidates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              candidate_ids: [candidate.id],
              stage: selectedStage
            })
          })
          
          if (!response.ok) {
          } else {
            const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)
            toast.success(t('invite.toasts.candidateLinked'), { description: t('invite.toasts.candidateLinkedDesc', { name: candidate.name, job: selectedVacancy?.title || '' }) })
          }
        } catch (error) {
        }
      }

      const selectedVacancy = linkToVacancy ? vacancies.find(v => v.id === selectedVacancyId) : null
      const effectiveJobId = (linkToVacancy ? selectedVacancyId : jobId) || ''
      const effectiveJobTitle = selectedVacancy?.title || jobTitle || ''

      // Task #425 — Telefone (PSTN) is dispatched directly via Twilio voice
      // initiate. It is NOT a generic "invite"; it triggers an outbound call
      // immediately. Other channels still use send-screening-invite.
      if (channel === 'telefone') {
        if (!companyId) {
          toast.error('Empresa não identificada', { description: 'Não foi possível identificar a empresa para iniciar a ligação.' })
          return
        }
        const callResponse = await fetch('/api/backend-proxy/twilio-voice/initiate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: candidate.id,
            candidate_name: candidate.name,
            phone_number: candidate.phone,
            job_title: effectiveJobTitle,
            company_id: companyId,
            job_id: effectiveJobId,
            language: 'pt-BR',
          })
        })
        const callData = await callResponse.json().catch(() => ({}))
        if (!callResponse.ok || callData?.success === false) {
          toast.error('Falha ao iniciar ligação', { description: callData?.error || callData?.detail || 'Tente novamente em instantes.' })
          return
        }
        toast.success('Ligação iniciada', { description: `A LIA está discando para ${candidate.name}.` })
        onSend?.({
          channel: 'telefone',
          candidateId: candidate.id,
          candidateName: candidate.name,
          jobTitle: effectiveJobTitle,
          vacancyId: effectiveJobId,
        } as never)
        onClose()
        return
      }

      // voz_web is delivered via email (link to /voip-start), but the modality
      // is tracked separately in the onSend callback. Backend expects one of
      // email|whatsapp|telefone for send-screening-invite.
      const sendChannel: 'email' | 'whatsapp' =
        channel === 'voz_web' ? 'email' : (channel as 'email' | 'whatsapp')

      const inviteResponse = await fetch('/api/backend-proxy/communication/send-screening-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: sendChannel,
          candidate_id: candidate.id,
          candidate_name: candidate.name,
          candidate_email: candidate.email,
          candidate_phone: candidate.phone,
          subject: (channel === 'email' || channel === 'voz_web') ? subject : undefined,
          message,
          vacancy_id: linkToVacancy ? selectedVacancyId : jobId,
          vacancy_title: selectedVacancy?.title || jobTitle,
          screening_question_ids: screeningQuestions.map(q => q.id),
          stage: linkToVacancy ? selectedStage : 'triagem',
        })
      })
      
      const inviteData = await inviteResponse.json()
      
      if (!inviteResponse.ok || !inviteData.success) {
        toast.error(t('invite.toasts.inviteError'), { description: inviteData.error || t('invite.toasts.inviteErrorGeneric') })
        return
      }
      
      if (channel === 'whatsapp' && candidate.phone) {
        const whatsappUrl = `https://wa.me/${candidate.phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`
        window.open(whatsappUrl, '_blank')
      }
      
      const mockSuffix = inviteData.mock ? t('invite.toasts.devMode') : ''
      const successMessages: Record<string, { title: string; description: string }> = {
        email: {
          title: t('invite.toasts.emailSuccess'),
          description: t('invite.toasts.emailSuccessDesc', { name: candidate.name, mock: mockSuffix })
        },
        whatsapp: {
          title: t('invite.toasts.whatsappSuccess'),
          description: t('invite.toasts.whatsappSuccessDesc', { name: candidate.name })
        },
        telefone: {
          title: t('invite.toasts.phoneSuccess'),
          description: t('invite.toasts.phoneSuccessDesc', { name: candidate.name })
        },
        voz_web: {
          title: 'Convite de Voz Web enviado',
          description: `Link de Voz no Navegador (Gemini Live) enviado para ${candidate.name}.`
        }
      }
      
      const successMsg = successMessages[channel] || successMessages.email
      toast.success(successMsg.title, { description: successMsg.description })
      
      onSend?.({
        channel,
        subject: (channel === 'email' || channel === 'voz_web') ? subject : undefined,
        message,
        candidateId: candidate.id,
        screeningQuestions: screeningQuestions.map(q => q.id),
        vacancyId: linkToVacancy ? selectedVacancyId : undefined,
        stage: linkToVacancy ? selectedStage : undefined,
        messageId: inviteData.message_id,
        communicationLogged: inviteData.communication_logged,
      })
      
      onClose()
    } catch (error) {
      toast.error(t('invite.toasts.sendError'), { description: t('invite.toasts.sendErrorDesc') })
    } finally {
      setIsSending(false)
    }
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
  }

  const formatPreviewMessage = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]/g, '<span class="text-lia-text-secondary underline cursor-pointer">$1</span>')
      .replace(/•/g, '&bull;')
      .replace(/\n/g, '<br>')
  }

  if (!isOpen || !candidate || !mounted) return null

  const modalContent = (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-modal flex items-center justify-center p-4">
      <div 
        className={`${cardStyles.elevated} w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col rounded-md`}
       
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-lia-bg-secondary/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-lia-bg-tertiary rounded-full flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-lia-text-secondary" />
            </div>
            <div>
              <h2 className={textStyles.titleLarge}>
                {t('invite.title')}
              </h2>
              <p className={textStyles.description}>
                {candidate.name} • {candidate.role || jobTitle}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4 text-lia-text-secondary" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Left Panel - Form */}
          <div className="w-1/2 border-r border-lia-border-subtle overflow-y-auto p-5 space-y-5">
            {/* Canal de Contato */}
            <div>
              <label className={`${textStyles.subtitle} mb-2 block`}>
                {t('invite.contactChannel')}
              </label>
              <div className="flex flex-col gap-2">
                {availableChannels.length === 0 && (
                  <div className="text-xs text-status-warning bg-status-warning/10 border border-status-warning/20 rounded-md p-3">
                    {t.has('invite.noChannelsEnabled')
                      ? t('invite.noChannelsEnabled')
                      : 'Nenhum canal habilitado nesta vaga. Habilite ao menos um canal nas configurações de triagem.'}
                  </div>
                )}
                {availableChannels.includes('email') && (
                  <button
                    onClick={() => setChannel('email')}
                    className={`flex items-center gap-3 p-3 rounded-md border transition-colors motion-reduce:transition-none text-left ${
                      channel === 'email'
                        ? 'border-lia-btn-primary-bg bg-lia-bg-secondary/50'
                        : 'border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                  >
                    <Mail className={`w-4 h-4 ${channel === 'email' ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
                    <div className="flex-1">
                      <div className={textStyles.subtitle}>Chat Web (link por email)</div>
                      <div className={textStyles.caption}>{candidate.email || t('invite.notInformed')}</div>
                    </div>
                  </button>
                )}

                {availableChannels.includes('whatsapp') && (
                  <button
                    onClick={() => setChannel('whatsapp')}
                    className={`flex items-center gap-3 p-3 rounded-md border transition-colors motion-reduce:transition-none text-left ${
                      channel === 'whatsapp'
                        ? 'border-lia-btn-primary-bg bg-lia-bg-secondary/50'
                        : 'border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                  >
                    <MessageSquare className={`w-4 h-4 ${channel === 'whatsapp' ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
                    <div className="flex-1">
                      <div className={textStyles.subtitle}>{t('invite.whatsapp')}</div>
                      <div className={textStyles.caption}>{candidate.phone || t('invite.notInformed')}</div>
                    </div>
                  </button>
                )}

                {availableChannels.includes('telefone') && (
                  <button
                    onClick={() => setChannel('telefone')}
                    className={`flex items-center gap-3 p-3 rounded-md border transition-colors motion-reduce:transition-none text-left ${
                      channel === 'telefone'
                        ? 'border-lia-btn-primary-bg bg-lia-bg-secondary/50'
                        : 'border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                  >
                    <Phone className={`w-4 h-4 ${channel === 'telefone' ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
                    <div className="flex-1">
                      <div className={textStyles.subtitle}>Ligação automática (PSTN)</div>
                      <div className={textStyles.caption}>{candidate.phone || t('invite.notInformed')}</div>
                    </div>
                  </button>
                )}

                {availableChannels.includes('voz_web') && (
                  <button
                    onClick={() => setChannel('voz_web')}
                    className={`flex items-center gap-3 p-3 rounded-md border transition-colors motion-reduce:transition-none text-left ${
                      channel === 'voz_web'
                        ? 'border-lia-btn-primary-bg bg-lia-bg-secondary/50'
                        : 'border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                  >
                    <Phone className={`w-4 h-4 ${channel === 'voz_web' ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
                    <div className="flex-1">
                      <div className={textStyles.subtitle}>Voz no Navegador (Gemini Live)</div>
                      <div className={textStyles.caption}>Link enviado por email — candidato fala pelo navegador</div>
                    </div>
                  </button>
                )}
              </div>
            </div>

            {/* Channel-specific composer */}
            {channel === 'telefone' ? (
              <div className="border border-lia-border-subtle rounded-md p-3 bg-lia-bg-secondary/40">
                <div className="flex items-center gap-2 mb-1">
                  <Phone className="w-4 h-4 text-wedo-orange" />
                  <span className={textStyles.subtitle}>Ligação automática (Twilio PSTN)</span>
                </div>
                <p className="text-micro text-lia-text-tertiary">
                  Ao confirmar, a LIA disca imediatamente para <strong className="text-lia-text-primary">{candidate.phone || '—'}</strong> e conduz a triagem por voz.
                </p>
              </div>
            ) : (
              <MessageComposer
                channel={(channel === 'voz_web' ? 'email' : channel) as 'email' | 'whatsapp'}
                situation="triagem"
                initialSubject={subject}
                initialMessage={message}
                onSubjectChange={setSubject}
                onMessageChange={setMessage}
                showTemplateSelector={true}
                showLiaAdjust={true}
                showVariableSelector={true}
                candidateContext={{
                  name: candidate.name,
                  role: candidate.role,
                  location: candidate.location
                }}
                jobContext={{
                  title: jobTitle
                }}
              />
            )}

            {/* Vincular à Vaga */}
            <div className="border border-lia-border-subtle rounded-xl overflow-hidden">
              <div className="flex items-center justify-between p-3 bg-lia-bg-secondary">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-lia-text-secondary" />
                  <div>
                    <span className={textStyles.subtitle} aria-live="polite" aria-atomic="true">{t('invite.linkToJob')}</span>
                    <span className={`${textStyles.description} ml-2`}>{t('invite.optional')}</span>
                  </div>
                </div>
                <Switch
                  checked={linkToVacancy}
                  onCheckedChange={setLinkToVacancy}
                />
              </div>
              
              {linkToVacancy && (
                <div className="p-3 space-y-3 border-t border-lia-border-subtle">
                  <div role="status" aria-live="polite" aria-label={t('invite.loadingJobs')}>
                    <label className={`${textStyles.subtitle} mb-1.5 block`}>
                      {t('invite.selectJob')}
                    </label>
                    {isLoadingVacancies ? (
                      <div className="flex items-center gap-2 text-xs text-lia-text-secondary py-2" role="status" aria-live="polite" aria-label={t('invite.loadingJobs')}>
                        <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                        {t('invite.loadingJobs')}
                      </div>
                    ) : vacancies.length === 0 ? (
                      <div className="text-xs text-lia-text-secondary py-2">
                        {t('invite.noJobsAvailable')}
                      </div>
                    ) : (
                      <select
                        value={selectedVacancyId || ''}
                        onChange={(e) => setSelectedVacancyId(e.target.value || null)}
                        className="w-full text-xs border border-lia-border-subtle rounded-xl px-3 py-2 bg-lia-bg-primary focus:ring-1 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                      >
                        <option value="">{t('invite.selectAJob')}</option>
                        {vacancies.map((vacancy) => (
                          <option key={vacancy.id} value={vacancy.id}>
                            {vacancy.title}
                            {vacancy.department ? ` - ${vacancy.department}` : ''}
                            {vacancy.location ? ` (${vacancy.location})` : ''}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                  
                  <div>
                    <label className={`${textStyles.subtitle} mb-1.5 block`}>
                      {t('invite.pipelineStage')}
                    </label>
                    <select
                      value={selectedStage}
                      onChange={(e) => setSelectedStage(e.target.value)}
                      className="w-full text-xs border border-lia-border-subtle rounded-xl px-3 py-2 bg-lia-bg-primary focus:ring-1 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                    >
                      {PIPELINE_STAGES.map((stage) => (
                        <option key={stage.value} value={stage.value}>
                          {stage.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {selectedVacancyId && (
                    <div className="p-2 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-default">
                      <p className="text-xs text-lia-text-secondary" dangerouslySetInnerHTML={{ __html: sanitizeHtml(t('invite.addToJobOnSend', { stage: PIPELINE_STAGES.find(s => s.value === selectedStage)?.label || '' })) }} />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Perguntas de Triagem */}
            <div className="border border-lia-border-subtle rounded-xl overflow-hidden">
              <button
                onClick={() => setShowQuestions(!showQuestions)}
                className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              >
                <div className="flex items-center gap-2">
                  <ListChecks className="w-4 h-4 text-lia-text-secondary" />
                  <span className={textStyles.subtitle}>
                    {t('invite.screeningScript', { count: screeningQuestions.length })}
                  </span>
                </div>
                {showQuestions ? (
                  <ChevronUp className="w-4 h-4 text-lia-text-secondary" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
                )}
              </button>
              
              {showQuestions && (
                <div className="p-3 space-y-2 max-h-chart-sm overflow-y-auto">
                  {screeningQuestions.map((q, idx) => (
                    <div 
                      key={q.id} 
                      className={cardStyles.compact}
                    >
                      <div className="flex items-start gap-2">
                        <span className={badgeStyles.primary}>
                          {idx + 1}
                        </span>
                        <div className="flex-1">
                          <p className={textStyles.bodySmall}>{q.question}</p>
                          {q.category && (
                            <span className={`${textStyles.caption} mt-1 block`}>
                              {q.category}
                              {q.bloomLevel && ` • Bloom ${q.bloomLevel}`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Preview */}
          <div className="w-1/2 bg-lia-bg-secondary p-5 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-lia-text-secondary" />
                <span className={textStyles.subtitle}>{t('invite.messagePreview')}</span>
              </div>
              <Chip variant="neutral" className="text-micro">
                {channel === 'email' ? t('invite.email') : channel === 'whatsapp' ? t('invite.whatsapp') : channel === 'both' ? t('invite.both') : t('invite.phone')}
              </Chip>
            </div>

            {/* Preview Card - Different styles per channel */}
            <div className={`rounded-md overflow-hidden ${
 channel === 'whatsapp' ? 'bg-whatsapp-bg' : 'bg-lia-bg-primary border border-lia-border-subtle'
            }`}>
              {(channel === 'email' || channel === 'both') ? (
                <>
                  {/* Email Preview Header */}
                  <div className="p-4 bg-lia-bg-secondary/50">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="text-micro bg-lia-btn-primary-bg text-lia-btn-primary-text">
                          RH
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className={textStyles.subtitle}>{t('invite.recruitmentTeam')}</div>
                        <div className={textStyles.caption}>recrutamento@empresa.com</div>
                      </div>
                    </div>
                    <div className={`mt-2 ${textStyles.bodySmall}`}>
                      {t('invite.to')}: {candidate.email || 'email@candidate.com'}
                    </div>
                  </div>
                  {/* Email Subject */}
                  {subject && (
                    <div className="px-4 py-2">
                      <div className={textStyles.subtitle}>
                        {subject}
                      </div>
                    </div>
                  )}
                  {/* Email Body */}
                  <div className="p-4">
                    <div 
                      className={`${textStyles.body} leading-relaxed`}
                      dangerouslySetInnerHTML={{ __html: sanitizeHtml(formatPreviewMessage(message) || `<span class="lia-text-secondary">${t('invite.messageWillAppear')}</span>`) }}
                    />
                  </div>
                </>
              ) : channel === 'whatsapp' ? (
                <div className="p-3">
                  {/* WhatsApp Chat Bubble */}
                  <div className="flex justify-end mb-2">
                    <div className="bg-whatsapp-bubble rounded-md p-3 max-w-[85%]">
                      <div 
                        className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{ __html: sanitizeHtml(formatPreviewMessage(message) || `<span class="lia-text-secondary">${t('invite.messageWillAppear')}</span>`) }}
                      />
                      <div className="text-micro text-lia-text-secondary text-right mt-1">
                        {new Date().toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })} ✓✓
                      </div>
                    </div>
                  </div>
                  {/* WhatsApp Info */}
                  <div className="text-center mt-3">
                    <span className="text-micro text-lia-text-secondary bg-lia-bg-primary/60 rounded-full py-1 px-3">
                      {t('invite.whatsappWebWillOpen')}
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  {/* Telefone/Script Preview */}
                  <div className="p-4 bg-status-warning/10/50">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-status-warning/15 rounded-full flex items-center justify-center">
                        <Phone className="w-4 h-4 text-status-warning" />
                      </div>
                      <div>
                        <div className={textStyles.subtitle}>{t('invite.callScript')}</div>
                        <div className={textStyles.caption}>{t('invite.liaWillCall')}</div>
                      </div>
                    </div>
                  </div>
                  {/* Script Content */}
                  <div className="p-4">
                    <div 
                      className="text-xs text-lia-text-primary leading-relaxed font-mono bg-lia-bg-secondary p-3 rounded-xl border border-lia-border-subtle"
                      dangerouslySetInnerHTML={{ __html: sanitizeHtml(formatPreviewMessage(message) || `<span class="lia-text-secondary">${t('invite.scriptWillAppear')}</span>`) }}
                    />
                  </div>
                </>
              )}
            </div>

            {/* Info Box - Different per channel */}
            {(channel === 'email' || channel === 'both') && (
              <div className={`mt-4 p-3 ${badgeStyles.info} rounded-md border border-lia-border-default bg-lia-bg-secondary/50`}>
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-lia-text-secondary mt-0.5" />
                  <div>
                    <div className={textStyles.label}>{channel === 'both' ? t('invite.simultaneousSending') : t('invite.afterConfirmation')}</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      {channel === 'both' && <li>• {t('invite.infoEmailBoth.emailSentPlusWA')}</li>}
                      <li>• {t('invite.infoEmailBoth.candidateChoosesChannel')}</li>
                      <li>• {t('invite.infoEmailBoth.receivesLGPD')}</li>
                      <li>• {t('invite.infoEmailBoth.liaStartsScreening')}</li>
                      <li>• {t('invite.infoEmailBoth.youGetNotified')}</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {channel === 'whatsapp' && (
              <div className={`mt-4 p-3 ${badgeStyles.success} rounded-md border border-status-success/30 bg-status-success/10`}>
                <div className="flex items-start gap-2">
                  <MessageSquare className="w-4 h-4 text-status-success mt-0.5" />
                  <div>
                    <div className={textStyles.label}>{t('invite.infoWhatsapp.title')}</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      <li>• {t('invite.infoWhatsapp.candidateRepliesYes')}</li>
                      <li>• {t('invite.infoWhatsapp.liaPresentsLGPD')}</li>
                      <li>• {t('invite.infoWhatsapp.wsiStartsAuto')}</li>
                      <li>• {t('invite.infoWhatsapp.youGetNotified')}</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {channel === 'telefone' && (
              <div className={`mt-4 p-3 ${badgeStyles.warning} rounded-md border border-status-warning/30 bg-status-warning/10`}>
                <div className="flex items-start gap-2">
                  <Phone className="w-4 h-4 text-status-warning mt-0.5" />
                  <div>
                    <div className={textStyles.label}>{t('invite.infoPhone.title')}</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      <li>• {t('invite.infoPhone.liaWillCallScheduled')}</li>
                      <li>• {t('invite.infoPhone.conversationRecorded')}</li>
                      <li>• {t('invite.infoPhone.transcriptionAvailable')}</li>
                      <li>• {t('invite.infoPhone.wsiAutoCalculated')}</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className={`flex items-center gap-2 ${textStyles.description}`}>
            <Mail className="w-3.5 h-3.5" />
            {channel === 'email' 
              ? t('invite.emailSentViaSystem') 
              : channel === 'whatsapp'
              ? t('invite.whatsappOpenInBrowser')
              : channel === 'both'
              ? t('invite.emailPlusWhatsapp')
              : t('invite.scriptForLiaCall')}
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={onClose}
              variant="outline"
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
            >
              {t('invite.cancel')}
            </Button>
            <Button
              onClick={handleSend}
              disabled={(() => {
                if (isSending) return true
                const needsEmail = channel === 'email' || channel === 'voz_web' || channel === 'both'
                const needsPhone = channel === 'whatsapp' || channel === 'telefone' || channel === 'both'
                if (needsEmail && !candidate.email) return true
                if (needsPhone && !candidate.phone) return true
                // Task #425 — only channels that actually compose text require a
                // message body. Direct phone (Twilio PSTN) initiates a call
                // without any composer, so message must NOT gate the CTA.
                const requiresMessage = channel === 'email' || channel === 'whatsapp' || channel === 'voz_web' || channel === 'both'
                if (requiresMessage && !message.trim()) return true
                return false
              })()}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              {isSending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin motion-reduce:animate-none" />
                  {t('invite.sending')}
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5 mr-2" />
                  {channel === 'email' ? t('invite.sendEmail') : 
                   channel === 'whatsapp' ? t('invite.sendWhatsapp') : 
                   channel === 'both' ? t('invite.sendBoth') :
                   t('invite.startCall')}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
