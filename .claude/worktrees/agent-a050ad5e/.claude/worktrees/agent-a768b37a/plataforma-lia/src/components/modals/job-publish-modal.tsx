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

  const publishedCount = useMemo(() => jobs.filter(j => j.is_published).length, [jobs])
  const unpublishedCount = useMemo(() => jobs.filter(j => !j.is_published).length, [jobs])
  
  const mode = useMemo(() => {
    if (publishedCount === jobs.length) return 'unpublish'
    if (unpublishedCount === jobs.length) return 'publish'
    return 'mixed'
  }, [publishedCount, unpublishedCount, jobs.length])

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
      console.error('Error publishing jobs:', error)
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
      console.error('Error unpublishing jobs:', error)
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
      <DialogContent className="max-w-2xl bg-white border border-gray-200">
        <DialogHeader className="pb-3 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 flex items-center justify-center">
              <Share2 className="w-4 h-4 text-gray-600" />
            </div>
            <div>
              <DialogTitle className="text-[14px] font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif]">
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
                <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 font-['Open_Sans',sans-serif]">
                  Vagas Selecionadas
                </h4>
                <div className={cn(
                  "overflow-y-auto space-y-1 bg-gray-50 rounded-md p-2 border border-gray-200",
                  mode === 'unpublish' ? "max-h-[120px]" : "max-h-[100px]"
                )}>
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between py-1.5 px-2 bg-white rounded-md border border-gray-200"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <Briefcase className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                        <div className="flex items-center gap-1.5 min-w-0 flex-1">
                          {job.code && <span className="text-[10px] font-medium text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                          <span className="text-xs font-medium text-gray-950 truncate">{job.title}</span>
                        </div>
                      </div>
                      {job.is_published ? (
                        <span className="text-[10px] font-medium text-green-600 flex items-center gap-0.5 flex-shrink-0 ml-2">
                          <Check className="w-2.5 h-2.5" />
                          Publicada
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium text-gray-600 flex-shrink-0 ml-2">Não publicada</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {(mode === 'publish' || mode === 'mixed') && (
                <div>
                  <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1 font-['Open_Sans',sans-serif]">
                    <Calendar className="w-3 h-3" />
                    Agendamento
                  </h4>
                  <RadioGroup
                    value={scheduleType}
                    onValueChange={(value) => setScheduleType(value as 'now' | 'scheduled')}
                    className="space-y-1.5"
                  >
                    <div className="flex items-center gap-2 p-2 rounded-md border border-gray-200 bg-white">
                      <RadioGroupItem
                        value="now"
                        id="schedule-now"
                        className="border-gray-300 text-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <Label htmlFor="schedule-now" className="text-[11px] text-gray-800 cursor-pointer">
                        Publicar agora
                      </Label>
                    </div>
                    
                    <div className="space-y-2 p-2 rounded-md border border-gray-200 bg-white">
                      <div className="flex items-center gap-2">
                        <RadioGroupItem
                          value="scheduled"
                          id="schedule-later"
                          className="border-gray-300 text-gray-900 data-[state=checked]:border-gray-900"
                        />
                        <Label htmlFor="schedule-later" className="text-[11px] text-gray-800 cursor-pointer">
                          Agendar para:
                        </Label>
                      </div>
                      
                      {scheduleType === 'scheduled' && (
                        <div className="flex items-center gap-2 pl-6">
                          <Input
                            type="date"
                            value={scheduleDate}
                            onChange={(e) => setScheduleDate(e.target.value)}
                            className="w-32 h-7 text-[11px] border-gray-200"
                          />
                          <Input
                            type="time"
                            value={scheduleTime}
                            onChange={(e) => setScheduleTime(e.target.value)}
                            className="w-24 h-7 text-[11px] border-gray-200"
                          />
                        </div>
                      )}
                    </div>
                  </RadioGroup>
                </div>
              )}

              {(mode === 'unpublish' || mode === 'mixed') && (
                <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-gray-200">
                  <div className="flex items-center gap-2 text-gray-800 mb-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                    <span className="text-[11px] font-semibold text-gray-950">Opções ao despublicar</span>
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
                        <Label htmlFor="freezeJob" className="text-[11px] font-medium text-gray-950 cursor-pointer">
                          Congelar vaga
                        </Label>
                        <p className="text-[10px] text-gray-600">Pausar temporariamente o processo seletivo</p>
                      </div>
                    </div>
                    
                    {freezeJob && (
                      <div className="ml-6 space-y-2 pt-1">
                        <div>
                          <Label className="text-[10px] text-gray-600 mb-1 block">Motivo do congelamento</Label>
                          <select
                            value={freezeReason}
                            onChange={(e) => setFreezeReason(e.target.value)}
                            className="w-full h-8 px-2 text-[11px] border border-gray-200 rounded-md bg-white text-gray-800 focus:outline-none focus:ring-1 focus:ring-gray-900/20"
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
                          <Label className="text-[10px] text-gray-600 mb-1 block">
                            Previsão de descongelamento
                            <span className="text-gray-400 ml-1">(LIA irá notificá-lo)</span>
                          </Label>
                          <Input
                            type="date"
                            value={unfreezeDate}
                            onChange={(e) => setUnfreezeDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                            className="h-8 text-[11px] border-gray-200"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="border-t border-gray-200 pt-2">
                    <div className="flex items-start gap-2">
                      <Checkbox
                        id="notifyApplicants"
                        checked={notifyApplicants}
                        onCheckedChange={(checked) => setNotifyApplicants(!!checked)}
                        className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <div className="flex-1">
                        <Label htmlFor="notifyApplicants" className="text-[11px] font-medium text-gray-950 cursor-pointer">
                          Notificar candidatos
                        </Label>
                        <p className="text-[10px] text-gray-600">
                          Todos os candidatos do processo receberão uma mensagem
                        </p>
                        {notifyApplicants && (
                          <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 px-2 py-1 rounded-full">
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
                <>
                  <div>
                    <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 font-['Open_Sans',sans-serif]">
                      Canais de Publicação
                    </h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {PUBLICATION_CHANNELS.map((channel) => (
                        <div
                          key={channel.id}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded-md border transition-all cursor-pointer",
                            selectedChannels.has(channel.id) && channel.connected
                              ? "border-gray-900 bg-gray-50"
                              : "border-gray-200 bg-white hover:border-gray-300"
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
                            <span className="text-[11px] font-medium text-gray-800">{channel.name}</span>
                          </div>
                          {!channel.connected && (
                            <a
                              href={channel.configUrl}
                              className="text-[10px] font-medium text-gray-600 hover:text-gray-900 ml-auto"
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
                    <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1 font-['Open_Sans',sans-serif]">
                      <Search className="w-3 h-3" />
                      Busca Automática
                    </h4>
                    <div className="space-y-2 bg-gray-50 rounded-md p-3 border border-gray-200">
                      <div className="flex items-start gap-2">
                        <Checkbox
                          id="autoSearchInternal"
                          checked={autoSearchInternal}
                          onCheckedChange={(checked) => setAutoSearchInternal(!!checked)}
                          className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                        />
                        <div>
                          <Label htmlFor="autoSearchInternal" className="text-[11px] font-medium text-gray-950 cursor-pointer">
                            Busca na base interna
                          </Label>
                          <p className="text-[10px] text-gray-600">LIA encontra candidatos no banco de talentos</p>
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
                          <Label htmlFor="autoSearchGlobal" className="text-[11px] font-medium text-gray-950 cursor-pointer flex items-center gap-1">
                            Busca Global
                            <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                              <Brain className="w-2 h-2 text-wedo-cyan" />
                              IA
                            </span>
                          </Label>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <p className="text-[10px] text-gray-600">Fontes externas</p>
                            <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-gray-700 bg-gray-100 px-1 py-0.5 rounded-full">
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

        <DialogFooter className="border-t border-gray-200 pt-3 gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </Button>
          
          {mode === 'mixed' && onUnpublish && (
            <Button
              variant="outline"
              onClick={handleUnpublish}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100"
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
              disabled={isSubmitting || (selectedChannels.size === 0 && (mode === 'publish' || mode === 'mixed'))}
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
