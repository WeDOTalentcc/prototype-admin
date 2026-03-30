"use client"

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
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
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
  Brain
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
  onPublish: (jobIds: string[], channels: string[], options: any) => void
  onUnpublish?: (jobIds: string[], options: any) => void
  onOpenCommunicationModal?: (jobIds: string[], templateCategory?: string) => void
}

interface ChannelConfig {
  id: string
  name: string
  icon: React.ReactNode
  connected: boolean
  configUrl?: string
}

const PUBLICATION_CHANNELS: ChannelConfig[] = [
  { id: 'linkedin', name: 'LinkedIn', icon: <Linkedin className="w-3.5 h-3.5" />, connected: true },
  { id: 'indeed', name: 'Indeed', icon: <Globe className="w-3.5 h-3.5" />, connected: true },
  { id: 'gupy', name: 'Gupy', icon: <Building2 className="w-3.5 h-3.5" />, connected: false, configUrl: '/configuracoes/integracoes' },
  { id: 'portal', name: 'Portal Carreiras', icon: <ExternalLink className="w-3.5 h-3.5" />, connected: true },
]

export function JobPublishModal({
  isOpen,
  onClose,
  jobs,
  onPublish,
  onUnpublish,
  onOpenCommunicationModal
}: JobPublishModalProps) {
  const [selectedChannels, setSelectedChannels] = useState<Set<string>>(new Set())
  const [scheduleType, setScheduleType] = useState<'now' | 'scheduled'>('now')
  const [scheduleDate, setScheduleDate] = useState('')
  const [scheduleTime, setScheduleTime] = useState('')
  const [autoSearchInternal, setAutoSearchInternal] = useState(false)
  const [autoSearchGlobal, setAutoSearchGlobal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
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
    }
  }, [isOpen])

  const toggleChannel = (channelId: string) => {
    const newSelected = new Set(selectedChannels)
    if (newSelected.has(channelId)) {
      newSelected.delete(channelId)
    } else {
      newSelected.add(channelId)
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
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-3 border-b border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 flex items-center justify-center">
              <Share2 className="w-4 h-4 text-gray-600" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                {getModalTitle()}
              </DialogTitle>
              <p className="text-xs text-gray-600 mt-0.5">
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
                <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 font-['Open_Sans',sans-serif]">
                  Vagas Selecionadas
                </h4>
                <div className={cn(
                  "overflow-y-auto space-y-1 bg-gray-50 rounded-md p-2 border border-lia-border-subtle",
                  mode === 'unpublish' ? "max-h-[120px]" : "max-h-[100px]"
                )}>
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <Briefcase className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                        <div className="flex items-center gap-1.5 min-w-0 flex-1">
                          {job.code && <span className="text-micro font-medium text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                          <span className="text-xs font-medium text-gray-950 truncate">{job.title}</span>
                        </div>
                      </div>
                      {job.is_published ? (
                        <span className="text-micro font-medium text-status-success flex items-center gap-0.5 flex-shrink-0 ml-2">
                          <Check className="w-2.5 h-2.5" />
                          Publicada
                        </span>
                      ) : (
                        <span className="text-micro font-medium text-gray-600 flex-shrink-0 ml-2">Não publicada</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {(mode === 'publish' || mode === 'mixed') && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1 font-['Open_Sans',sans-serif]">
                    <Calendar className="w-3 h-3" />
                    Agendamento
                  </h4>
                  <RadioGroup
                    value={scheduleType}
                    onValueChange={(value) => setScheduleType(value as 'now' | 'scheduled')}
                    className="space-y-1.5"
                  >
                    <div className="flex items-center gap-2 p-2 rounded-md border border-lia-border-subtle bg-lia-bg-primary">
                      <RadioGroupItem
                        value="now"
                        id="schedule-now"
                        className="border-lia-border-default text-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <Label htmlFor="schedule-now" className="text-xs text-gray-800 cursor-pointer">
                        Publicar agora
                      </Label>
                    </div>
                    
                    <div className="space-y-2 p-2 rounded-md border border-lia-border-subtle bg-lia-bg-primary">
                      <div className="flex items-center gap-2">
                        <RadioGroupItem
                          value="scheduled"
                          id="schedule-later"
                          className="border-lia-border-default text-gray-900 data-[state=checked]:border-gray-900"
                        />
                        <Label htmlFor="schedule-later" className="text-xs text-gray-800 cursor-pointer">
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
                <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
                  <div className="flex items-center gap-2 text-gray-800 mb-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
                    <span className="text-xs font-semibold text-gray-950">Opções ao despublicar</span>
                  </div>
                  
                  {/* Congelar vaga */}
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <Checkbox
                        id="freezeJob"
                        checked={freezeJob}
                        onCheckedChange={(checked) => setFreezeJob(!!checked)}
                        className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <div className="flex-1">
                        <Label htmlFor="freezeJob" className="text-xs font-medium text-gray-950 cursor-pointer">
                          Congelar vaga
                        </Label>
                        <p className="text-micro text-gray-600">Pausar temporariamente o processo seletivo</p>
                      </div>
                    </div>
                    
                    {freezeJob && (
                      <div className="ml-6 space-y-2 pt-1">
                        <div>
                          <Label className="text-micro text-gray-600 mb-1 block">Motivo do congelamento</Label>
                          <select
                            value={freezeReason}
                            onChange={(e) => setFreezeReason(e.target.value)}
                            className="w-full h-8 px-2 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary text-gray-800 focus:outline-none focus:ring-1 focus:ring-gray-900/20"
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
                          <Label className="text-micro text-gray-600 mb-1 block">
                            Previsão de descongelamento
                            <span className="text-gray-400 ml-1">(LIA irá notificá-lo)</span>
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
                        className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <div className="flex-1">
                        <Label htmlFor="notifyApplicants" className="text-xs font-medium text-gray-950 cursor-pointer">
                          Notificar candidatos
                        </Label>
                        <p className="text-micro text-gray-600">
                          Todos os candidatos do processo receberão uma mensagem
                        </p>
                        {notifyApplicants && (
                          <div className="mt-1.5 flex items-center gap-1.5 text-micro text-gray-600 dark:text-lia-text-tertiary bg-gray-50 dark:bg-lia-bg-secondary/50 px-2 py-1 rounded-full">
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            <span>LIA abrirá o modal de envio por email/WhatsApp com template sugerido</span>
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
                <div className="rounded-md border border-lia-border-subtle bg-gray-50 p-3 space-y-2">
                  <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide font-['Open_Sans',sans-serif]">
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
                      <span className={cn("text-micro", jobsWithoutWSI.length === 0 ? "text-status-success" : "text-status-warning")}>
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
                      <span className={cn("text-micro", jobsWithoutScreening.length === 0 ? "text-status-success" : "text-status-warning")}>
                        {jobsWithoutScreening.length === 0 ? '— todas as vagas' : `— ${jobsWithoutScreening.length} pendente${jobsWithoutScreening.length > 1 ? 's' : ''}`}
                      </span>
                    </div>
                  </div>
                  {needsWSIWarning && (
                    <div className="mt-2 pt-2 border-t border-status-warning/30 bg-status-warning/10 -mx-3 -mb-3 px-3 pb-3 rounded-b-md">
                      <p className="text-micro text-status-warning leading-relaxed mb-2">
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
                    <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 font-['Open_Sans',sans-serif]">
                      Canais de Publicação
                    </h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {PUBLICATION_CHANNELS.map((channel) => (
                        <div
                          key={channel.id}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded-md border transition-colors cursor-pointer",
                            selectedChannels.has(channel.id) && channel.connected
                              ? "border-gray-900 bg-gray-50"
                              : "border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default"
                          )}
                          onClick={() => channel.connected && toggleChannel(channel.id)}
                        >
                          <Checkbox
                            checked={selectedChannels.has(channel.id)}
                            disabled={!channel.connected}
                            className="data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                          />
                          <div className="flex items-center gap-1.5">
                            <div className="w-5 h-5 rounded-md bg-gray-100 flex items-center justify-center text-gray-600">
                              {channel.icon}
                            </div>
                            <span className="text-xs font-medium text-gray-800">{channel.name}</span>
                          </div>
                          {!channel.connected && (
                            <a
                              href={channel.configUrl}
                              className="text-micro font-medium text-gray-600 hover:text-gray-900 ml-auto"
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
                    <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1 font-['Open_Sans',sans-serif]">
                      <Search className="w-3 h-3" />
                      Busca Automática
                    </h4>
                    <div className="space-y-2 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
                      <div className="flex items-start gap-2">
                        <Checkbox
                          id="autoSearchInternal"
                          checked={autoSearchInternal}
                          onCheckedChange={(checked) => setAutoSearchInternal(!!checked)}
                          className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                        />
                        <div>
                          <Label htmlFor="autoSearchInternal" className="text-xs font-medium text-gray-950 cursor-pointer">
                            Busca na base interna
                          </Label>
                          <p className="text-micro text-gray-600">LIA encontra candidatos no banco de talentos</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2">
                        <Checkbox
                          id="autoSearchGlobal"
                          checked={autoSearchGlobal}
                          onCheckedChange={(checked) => setAutoSearchGlobal(!!checked)}
                          className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                        />
                        <div className="flex-1">
                          <Label htmlFor="autoSearchGlobal" className="text-xs font-medium text-gray-950 cursor-pointer flex items-center gap-1">
                            Busca Global
                            <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full text-micro font-medium bg-gray-100 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary">
                              <Brain className="w-2 h-2 text-wedo-cyan" />
                              IA
                            </span>
                          </Label>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <p className="text-micro text-gray-600">Fontes externas</p>
                            <span className="inline-flex items-center gap-0.5 text-micro font-medium text-gray-700 bg-gray-100 px-1 py-0.5 rounded-full">
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
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </Button>
          
          {mode === 'mixed' && onUnpublish && (
            <Button
              variant="outline"
              onClick={handleUnpublish}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle bg-gray-50 text-gray-700 hover:bg-gray-100"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <X className="w-3.5 h-3.5 mr-1.5" />}
              Despublicar ({publishedCount})
            </Button>
          )}
          
          {mode === 'unpublish' && onUnpublish ? (
            <Button
              onClick={handleUnpublish}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <X className="w-3.5 h-3.5 mr-1.5" />}
              Despublicar Vagas
            </Button>
          ) : (
            <Button
              onClick={handlePublish}
              disabled={isSubmitting || (selectedChannels.size === 0 && (mode === 'publish' || mode === 'mixed')) || (needsWSIWarning && !wsiWarningConfirmed)}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Share2 className="w-3.5 h-3.5 mr-1.5" />}
              {mode === 'mixed' ? `Publicar (${unpublishedCount})` : 'Publicar Vagas'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
