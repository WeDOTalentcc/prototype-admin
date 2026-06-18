"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import {
  Share2,
  Loader2,
  Check,
  AlertTriangle,
  Linkedin,
  Globe,
  Building2,
  Calendar,
  Clock,
  Search,
  Briefcase,
  X,
  ExternalLink,
  Coins,
  Brain,
  Info,
} from "lucide-react"

interface JobPublishModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    is_published?: boolean
    published_channels?: string[]
    has_wsi_questions?: boolean
    wsi_question_count?: number
    screeningStatus?: string
  }>
  onPublish: (jobIds: string[], channels: string[], options: Record<string, unknown>) => void
  onUnpublish?: (jobIds: string[], options: Record<string, unknown>) => void
  onOpenCommunicationModal?: (jobIds: string[], templateCategory?: string) => void
}

interface ChannelConfig {
  id: string
  name: string
  icon: React.ReactNode
  connected: boolean
  configUrl?: string
  notConfiguredMessage?: string
}

const BASE_CHANNELS: Omit<ChannelConfig, 'connected'>[] = [
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: <Linkedin className="w-3.5 h-3.5" />,
    configUrl: '/configuracoes?section=integrations',
    notConfiguredMessage: 'A integração com LinkedIn requer credenciais OAuth configuradas (LINKEDIN_CLIENT_ID e LINKEDIN_CLIENT_SECRET). Configure em Integrações para habilitar a publicação automática de vagas.',
  },
  {
    id: 'indeed',
    name: 'Indeed',
    icon: <Globe className="w-3.5 h-3.5" />,
    configUrl: '/configuracoes?section=integrations',
  },
  {
    id: 'gupy',
    name: 'Gupy',
    icon: <Building2 className="w-3.5 h-3.5" />,
    configUrl: '/configuracoes?section=integrations',
  },
  {
    id: 'portal',
    name: 'Portal Carreiras',
    icon: <ExternalLink className="w-3.5 h-3.5" />,
  },
]

export function JobPublishModal({
  isOpen,
  onClose,
  jobs,
  onPublish,
  onUnpublish,
  onOpenCommunicationModal
}: JobPublishModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('job-publish', isOpen)
  useLiaModalTracking('job-publish-channel-info', channelInfoModal)

  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [selectedChannels, setSelectedChannels] = useState<Set<string>>(new Set())
  const [scheduleType, setScheduleType] = useState<'now' | 'scheduled'>('now')
  const [scheduleDate, setScheduleDate] = useState('')
  const [scheduleTime, setScheduleTime] = useState('')
  const [autoSearchInternal, setAutoSearchInternal] = useState(false)
  const [autoSearchGlobal, setAutoSearchGlobal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [channelInfoModal, setChannelInfoModal] = useState<{ name: string; message: string; configUrl?: string } | null>(null)
  const [integrationHealth, setIntegrationHealth] = useState<Record<string, { configured: boolean }>>({})

  const PUBLICATION_CHANNELS: ChannelConfig[] = BASE_CHANNELS.map((ch) => {
    if (ch.id === 'linkedin') {
      return { ...ch, connected: integrationHealth['linkedin']?.configured ?? false }
    }
    if (ch.id === 'indeed') {
      const indeedHealth = integrationHealth['indeed']
      const apiConfigured = indeedHealth?.configured ?? false
      return {
        ...ch,
        connected: true,
        notConfiguredMessage: !apiConfigured
          ? 'INDEED_API_KEY não configurado — vagas publicadas via feed XML automaticamente. Para publicação direta via API, configure a chave em Integrações.'
          : undefined,
      }
    }
    if (ch.id === 'portal') {
      return { ...ch, connected: true }
    }
    return { ...ch, connected: false }
  })
  
  const [freezeJob, setFreezeJob] = useState(false)
  const [freezeReason, setFreezeReason] = useState('')
  const [unfreezeDate, setUnfreezeDate] = useState('')
  const [notifyApplicants, setNotifyApplicants] = useState(false)
  const [wsiWarningConfirmed, setWsiWarningConfirmed] = useState(false)

  const publishedCount = useMemo(() => jobs.filter(j => j.is_published).length, [jobs])
  const unpublishedCount = useMemo(() => jobs.filter(j => !j.is_published).length, [jobs])
  
  const mode = useMemo(() => {
    if (publishedCount === jobs.length) return 'unpublish'
    if (unpublishedCount === jobs.length) return 'publish'
    return 'mixed'
  }, [publishedCount, unpublishedCount, jobs.length])

  const jobsWithoutWSI = useMemo(() => jobs.filter(j => !j.is_published && j.has_wsi_questions === false), [jobs])
  const jobsWithoutScreening = useMemo(() => jobs.filter(j => !j.is_published && (!j.screeningStatus || j.screeningStatus === 'not_configured')), [jobs])
  const needsWSIWarning = useMemo(() => jobsWithoutWSI.length > 0 && (mode === 'publish' || mode === 'mixed'), [jobsWithoutWSI, mode])

  const globalSearchCredits = useMemo(() => {
    return jobs.length * 50
  }, [jobs.length])

  useEffect(() => {
    if (isOpen) {
      setSelectedChannels(new Set())
      setScheduleType('now')
      setScheduleDate('')
      setScheduleTime('')
      setAutoSearchInternal(false)
      setAutoSearchGlobal(false)
      setFreezeJob(false)
      setFreezeReason('')
      setUnfreezeDate('')
      setNotifyApplicants(false)
      setWsiWarningConfirmed(false)
      setChannelInfoModal(null)

      fetch('/api/backend-proxy/integrations/health', { credentials: 'include' })
        .then((r) => r.ok ? r.json() : null)
        .then((data) => {
          if (data?.integrations) {
            setIntegrationHealth(data.integrations as Record<string, { configured: boolean }>)
          }
        })
        .catch((err) => { console.error('[job-publish-modal] integration health fetch failed', err) })
    }
  }, [isOpen])

  const toggleChannel = (channel: ChannelConfig) => {
    if (!channel.connected) {
      if (channel.notConfiguredMessage) {
        setChannelInfoModal({ name: channel.name, message: channel.notConfiguredMessage, configUrl: channel.configUrl })
      }
      return
    }
    const newSelected = new Set(selectedChannels)
    if (newSelected.has(channel.id)) {
      newSelected.delete(channel.id)
    } else {
      newSelected.add(channel.id)
      if (channel.notConfiguredMessage) {
        setChannelInfoModal({ name: channel.name, message: channel.notConfiguredMessage, configUrl: channel.configUrl })
      }
    }
    setSelectedChannels(newSelected)
  }

  const handlePublish = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)
    
    try {
      const options = {
        scheduleType,
        scheduledAt: scheduleType === 'scheduled' ? `${scheduleDate}T${scheduleTime}` : null,
        autoSearchInternal,
        autoSearchGlobal
      }
      
      await onPublish(
        jobs.filter(j => !j.is_published).map(j => j.id),
        Array.from(selectedChannels),
        options
      )
      onClose()
    } catch (error) {
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUnpublish = async () => {
    if (isSubmitting || !onUnpublish) return
    setIsSubmitting(true)
    
    try {
      const jobIds = jobs.filter(j => j.is_published).map(j => j.id)
      
      const options = {
        freezeJob,
        freezeReason: freezeJob ? freezeReason : null,
        unfreezeDate: freezeJob && unfreezeDate ? unfreezeDate : null,
        notifyApplicants
      }
      
      await onUnpublish(jobIds, options)
      onClose()
      
      // Se notificar candidatos está marcado, abre o modal de comunicação
      if (notifyApplicants && onOpenCommunicationModal) {
        // Aguarda um momento para o modal fechar antes de abrir o próximo
        setTimeout(() => {
          onOpenCommunicationModal(jobIds, 'vaga_congelada')
        }, 300)
      }
    } catch (error) {
    } finally {
      setIsSubmitting(false)
    }
  }

  const getModalTitle = () => {
    if (mode === 'unpublish') return 'Despublicar Vagas'
    if (mode === 'publish') return 'Publicar Vagas'
    return 'Gerenciar Publicação'
  }

  return (
    <>
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="job-publish-modal" className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <Share2 className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                {getModalTitle()}
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <div className={cn(
            "gap-4",
            mode === 'unpublish' ? "space-y-3" : "grid grid-cols-2"
          )}>
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Vagas Selecionadas
                </h4>
                <div className={cn(
                  "overflow-y-auto space-y-1 bg-lia-bg-secondary rounded-md p-2 border border-lia-border-subtle",
                  mode === 'unpublish' ? "max-h-[120px]" : "max-h-[100px]"
                )}>
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                        <div className="flex items-center gap-1.5 min-w-0 flex-1">
                          {job.code && <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                          <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                        </div>
                      </div>
                      {job.is_published ? (
                        <span className="text-micro font-medium text-status-success flex items-center gap-0.5 flex-shrink-0 ml-2">
                          <Check className="w-2.5 h-2.5" />
                          Publicada
                        </span>
                      ) : (
                        <span className="text-micro font-medium text-lia-text-secondary flex-shrink-0 ml-2">Não publicada</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {(mode === 'publish' || mode === 'mixed') && (
                <div>
                  <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Agendamento
                  </h4>
                  <RadioGroup
                    value={scheduleType}
                    onValueChange={(value) => setScheduleType(value as 'now' | 'scheduled')}
                    className="space-y-1.5"
                  >
                    <div className="flex items-center gap-2 p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-primary">
                      <RadioGroupItem
                        value="now"
                        id="schedule-now"
                        className="border-lia-border-default text-lia-text-primary data-[state=checked]:border-lia-btn-primary-bg"
                      />
                      <Label htmlFor="schedule-now" className="text-xs text-lia-text-primary cursor-pointer">
                        Publicar agora
                      </Label>
                    </div>
                    
                    <div className="space-y-2 p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-primary">
                      <div className="flex items-center gap-2">
                        <RadioGroupItem
                          value="scheduled"
                          id="schedule-later"
                          className="border-lia-border-default text-lia-text-primary data-[state=checked]:border-lia-btn-primary-bg"
                        />
                        <Label htmlFor="schedule-later" className="text-xs text-lia-text-primary cursor-pointer">
                          Agendar para:
                        </Label>
                      </div>
                      
                      {scheduleType === 'scheduled' && (
                        <div className="flex items-center gap-2 pl-6">
                          <Input
                            type="date"
                            value={scheduleDate}
                            onChange={(e) => setScheduleDate(e.target.value)}
                            className="w-32 h-7 text-xs border-lia-border-subtle"
                          />
                          <Input
                            type="time"
                            value={scheduleTime}
                            onChange={(e) => setScheduleTime(e.target.value)}
                            className="w-24 h-7 text-xs border-lia-border-subtle"
                          />
                        </div>
                      )}
                    </div>
                  </RadioGroup>
                </div>
              )}

              {(mode === 'unpublish' || mode === 'mixed') && (
                <div className="space-y-3 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
                  <div className="flex items-center gap-2 text-lia-text-primary mb-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
                    <span className="text-xs font-semibold text-lia-text-primary">Opções ao despublicar</span>
                  </div>
                  
                  {/* Congelar vaga */}
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <Checkbox
                        id="freezeJob"
                        checked={freezeJob}
                        onCheckedChange={(checked) => setFreezeJob(!!checked)}
                        className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                      />
                      <div className="flex-1">
                        <Label htmlFor="freezeJob" className="text-xs font-medium text-lia-text-primary cursor-pointer">
                          Congelar vaga
                        </Label>
                        <p className="text-micro text-lia-text-secondary">Pausar temporariamente o processo seletivo</p>
                      </div>
                    </div>
                    
                    {freezeJob && (
                      <div className="ml-6 space-y-2 pt-1">
                        <div>
                          <Label className="text-micro text-lia-text-secondary mb-1 block">Motivo do congelamento</Label>
                          <select
                            value={freezeReason}
                            onChange={(e) => setFreezeReason(e.target.value)}
                            className="w-full h-8 px-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
                          >
                            <option value="">Selecione um motivo...</option>
                            <option value="budget_review">Revisão orçamentária</option>
                            <option value="headcount_freeze">Congelamento de headcount</option>
                            <option value="restructuring">Reestruturação da área</option>
                            <option value="position_redefinition">Redefinição do perfil</option>
                            <option value="internal_transfer">Possível transferência interna</option>
                            <option value="vacation_period">Período de férias do gestor</option>
                            <option value="other">Outro motivo</option>
                          </select>
                        </div>
                        
                        <div>
                          <Label className="text-micro text-lia-text-secondary mb-1 block">
                            Previsão de descongelamento
                            <span className="text-lia-text-disabled ml-1">{`(${personaName} irá notificá-lo)`}</span>
                          </Label>
                          <Input
                            type="date"
                            value={unfreezeDate}
                            onChange={(e) => setUnfreezeDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                            className="h-8 text-xs border-lia-border-subtle"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="border-t border-lia-border-subtle pt-2">
                    <div className="flex items-start gap-2">
                      <Checkbox
                        id="notifyApplicants"
                        checked={notifyApplicants}
                        onCheckedChange={(checked) => setNotifyApplicants(!!checked)}
                        className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                      />
                      <div className="flex-1">
                        <Label htmlFor="notifyApplicants" className="text-xs font-medium text-lia-text-primary cursor-pointer">
                          Notificar candidatos
                        </Label>
                        <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                          Todos os candidatos do processo receberão uma mensagem
                        </p>
                        {notifyApplicants && (
                          <div className="mt-1.5 flex items-center gap-1.5 text-micro text-lia-text-secondary bg-lia-bg-secondary/50 px-2 py-1 rounded-full">
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            <span>{`${personaName} abrirá o modal`} de envio por email/WhatsApp com template sugerido</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-3">
              {(mode === 'publish' || mode === 'mixed') && (
                <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-3 space-y-2">
                  <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide">
                    Checklist de Publicação
                  </h4>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-xs">
                      {jobsWithoutWSI.length === 0 ? (
                        <Check className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                      )}
                      <span className={cn("font-medium", jobsWithoutWSI.length === 0 ? "text-status-success" : "text-status-warning")}>
                        Perguntas WSI geradas
                      </span>
                      <span className={cn("text-micro", jobsWithoutWSI.length === 0 ? "text-status-success" : "text-status-warning")} aria-live="polite" aria-atomic="true">
                        {jobsWithoutWSI.length === 0 ? '— todas as vagas' : `— ${jobsWithoutWSI.length} pendente${jobsWithoutWSI.length > 1 ? 's' : ''}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      {jobsWithoutScreening.length === 0 ? (
                        <Check className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                      )}
                      <span className={cn("font-medium", jobsWithoutScreening.length === 0 ? "text-status-success" : "text-status-warning")}>
                        Triagem WSI configurada
                      </span>
                      <span className={cn("text-micro", jobsWithoutScreening.length === 0 ? "text-status-success" : "text-status-warning")} aria-live="polite" aria-atomic="true">
                        {jobsWithoutScreening.length === 0 ? '— todas as vagas' : `— ${jobsWithoutScreening.length} pendente${jobsWithoutScreening.length > 1 ? 's' : ''}`}
                      </span>
                    </div>
                  </div>
                  {needsWSIWarning && (
                    <div className="mt-2 pt-2 border-t border-status-warning/30 bg-status-warning/10 -mx-3 -mb-3 px-3 pb-3 rounded-b-md">
                      <p className="text-micro text-status-warning leading-relaxed mb-2" aria-live="polite" aria-atomic="true">
                        {jobsWithoutWSI.length === 1
                          ? `A vaga "${jobsWithoutWSI[0].title}" não tem perguntas WSI geradas. Candidatos serão recebidos sem triagem automática.`
                          : `${jobsWithoutWSI.length} vagas não têm perguntas WSI geradas. Candidatos serão recebidos sem triagem automática.`
                        }
                      </p>
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id="wsiWarningConfirmed"
                          checked={wsiWarningConfirmed}
                          onCheckedChange={(checked) => setWsiWarningConfirmed(!!checked)}
                          className="data-[state=checked]:bg-status-warning data-[state=checked]:border-status-warning/30"
                        />
                        <Label htmlFor="wsiWarningConfirmed" className="text-micro font-medium text-status-warning cursor-pointer">
                          Entendo — publicar mesmo assim
                        </Label>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {(mode === 'publish' || mode === 'mixed') && (
                <>
                  <div>
                    <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                      Canais de Publicação
                    </h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {PUBLICATION_CHANNELS.map((channel) => (
                        <div
                          key={channel.id}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded-md border transition-colors cursor-pointer",
                            selectedChannels.has(channel.id) && channel.connected
                              ? "border-lia-btn-primary-bg bg-lia-bg-secondary"
                              : "border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default"
                          )}
                          onClick={() => toggleChannel(channel)}
                        >
                          <Checkbox
                            checked={selectedChannels.has(channel.id)}
                            disabled={!channel.connected}
                            className="data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                          />
                          <div className="flex items-center gap-1.5 min-w-0 flex-1">
                            <div className="w-5 h-5 rounded-xl bg-lia-bg-tertiary flex items-center justify-center text-lia-text-secondary flex-shrink-0">
                              {channel.icon}
                            </div>
                            <span className="text-xs font-medium text-lia-text-primary truncate">{channel.name}</span>
                          </div>
                          {!channel.connected && channel.notConfiguredMessage && (
                            <span title="Clique para saber como configurar">
                              <Info className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 ml-auto" />
                            </span>
                          )}
                          {!channel.connected && !channel.notConfiguredMessage && (
                            <a
                              href={channel.configUrl}
                              className="text-micro font-medium text-lia-text-secondary hover:text-lia-text-primary ml-auto flex-shrink-0"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Config
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1">
                      <Search className="w-3 h-3" />
                      Busca Automática
                    </h4>
                    <div className="space-y-2 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
                      <div className="flex items-start gap-2">
                        <Checkbox
                          id="autoSearchInternal"
                          checked={autoSearchInternal}
                          onCheckedChange={(checked) => setAutoSearchInternal(!!checked)}
                          className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                        />
                        <div>
                          <Label htmlFor="autoSearchInternal" className="text-xs font-medium text-lia-text-primary cursor-pointer">
                            Busca na base interna
                          </Label>
                          <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">{`${personaName} encontra candidatos no banco de talentos`}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2">
                        <Checkbox
                          id="autoSearchGlobal"
                          checked={autoSearchGlobal}
                          onCheckedChange={(checked) => setAutoSearchGlobal(!!checked)}
                          className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                        />
                        <div className="flex-1">
                          <Label htmlFor="autoSearchGlobal" className="text-xs font-medium text-lia-text-primary cursor-pointer flex items-center gap-1">
                            Busca Global
                            <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
                              <Brain className="w-2 h-2 text-wedo-cyan" />
                              IA
                            </span>
                          </Label>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <p className="text-micro text-lia-text-secondary">Fontes externas</p>
                            <span className="inline-flex items-center gap-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1 py-0.5 rounded-full">
                              <Coins className="w-2 h-2" />
                              {globalSearchCredits} créd.
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="border-t border-lia-border-subtle pt-3 gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            Cancelar
          </Button>
          
          {mode === 'mixed' && onUnpublish && (
            <Button
              variant="outline"
              onClick={handleUnpublish}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" /> : <X className="w-3.5 h-3.5 mr-1.5" />}
              Despublicar ({publishedCount})
            </Button>
          )}
          
          {mode === 'unpublish' && onUnpublish ? (
            <Button
              onClick={handleUnpublish}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" /> : <X className="w-3.5 h-3.5 mr-1.5" />}
              Despublicar Vagas
            </Button>
          ) : (
            <Button
              onClick={handlePublish}
              disabled={isSubmitting || (selectedChannels.size === 0 && (mode === 'publish' || mode === 'mixed')) || (needsWSIWarning && !wsiWarningConfirmed)}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" /> : <Share2 className="w-3.5 h-3.5 mr-1.5" />}
              {mode === 'mixed' ? `Publicar (${unpublishedCount})` : 'Publicar Vagas'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Informative modal for unconfigured channels (LinkedIn/Indeed) */}
    <Dialog open={channelInfoModal !== null} onOpenChange={(open) => !open && setChannelInfoModal(null)}>
      <DialogContent className="max-w-md bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <Info className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <DialogTitle className="text-sm font-semibold text-lia-text-primary">
              {channelInfoModal?.name} — Integração não configurada
            </DialogTitle>
          </div>
          <DialogDescription className="sr-only">
            Informações sobre como configurar a integração com {channelInfoModal?.name}
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <div className="flex items-start gap-2 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <AlertTriangle className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
            <p className="text-xs text-lia-text-primary leading-relaxed">
              {channelInfoModal?.message}
            </p>
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => setChannelInfoModal(null)}
            className="h-8 px-3 text-xs border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            Fechar
          </Button>
          {channelInfoModal?.configUrl && (
            <Button
              asChild
              className="h-8 px-3 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              <a href={channelInfoModal.configUrl} onClick={() => setChannelInfoModal(null)}>
                <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                Ir para Integrações
              </a>
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  )
}
