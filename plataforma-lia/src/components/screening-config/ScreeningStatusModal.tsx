"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { 
  BrainCircuit, 
  Play, 
  Pause, 
  CheckCircle2, 
  Clock, 
  ExternalLink,
  Loader2,
  AlertCircle,
  Calendar,
  BarChart3,
  Users
} from "lucide-react"
import { toast } from "sonner"
import { type ScreeningStatus, SCREENING_STATUS_LABELS } from "@/types/screening"

interface ScreeningStatusModalProps {
  isOpen: boolean
  onClose: () => void
  jobId: string
  jobTitle: string
  screeningStatus: ScreeningStatus
  screeningConfig?: {
    status?: {
      enabled?: boolean
      paused_at?: string | null
      paused_by?: string | null
      pause_reason?: string | null
      scheduled_end_date?: string | null
      activated_at?: string | null
      completed_at?: string | null
    }
    metrics?: {
      screened_count?: number
      completion_rate?: number
      average_rating?: number
    }
  }
  onStatusChange: (newStatus: ScreeningStatus, extraData?: { pause_reason?: string; scheduled_end_date?: string }) => Promise<boolean>
  onNavigateToJob?: () => void
}

const STATUS_CONFIG: Record<ScreeningStatus, { label: string; color: string; bgColor: string; darkBgColor: string; icon: React.ElementType }> = {
  not_configured: { label: SCREENING_STATUS_LABELS.not_configured, color: 'lia-text-base', bgColor: 'bg-gray-100', darkBgColor: 'dark:bg-lia-bg-secondary', icon: AlertCircle },
  not_started: { label: SCREENING_STATUS_LABELS.not_started, color: 'lia-text-base', bgColor: 'bg-gray-200', darkBgColor: 'dark:bg-lia-bg-elevated', icon: Clock },
  active: { label: SCREENING_STATUS_LABELS.active, color: 'text-status-success', bgColor: 'bg-status-success/15', darkBgColor: 'dark:bg-status-success/30', icon: Play },
  paused: { label: SCREENING_STATUS_LABELS.paused, color: 'text-status-warning', bgColor: 'bg-status-warning/15', darkBgColor: 'dark:bg-status-warning/30', icon: Pause },
  completed: { label: SCREENING_STATUS_LABELS.completed, color: 'text-wedo-cyan-dark', bgColor: 'bg-wedo-cyan/15', darkBgColor: 'dark:bg-wedo-cyan/10/30', icon: CheckCircle2 },
}

export function ScreeningStatusModal({
  isOpen,
  onClose,
  jobId,
  jobTitle,
  screeningStatus,
  screeningConfig,
  onStatusChange,
  onNavigateToJob,
}: ScreeningStatusModalProps) {
  const [isUpdating, setIsUpdating] = useState(false)
  const [showPauseForm, setShowPauseForm] = useState(false)
  const [pauseReason, setPauseReason] = useState('')
  const [scheduledEndDate, setScheduledEndDate] = useState(
    screeningConfig?.status?.scheduled_end_date || ''
  )

  const statusConfig = STATUS_CONFIG[screeningStatus] || STATUS_CONFIG.not_configured
  const StatusIcon = statusConfig.icon

  const handleStatusChange = async (newStatus: ScreeningStatus) => {
    if (newStatus === 'paused') {
      setShowPauseForm(true)
      return
    }
    
    setIsUpdating(true)
    try {
      const extraData: { scheduled_end_date?: string } = {}
      if (scheduledEndDate) {
        extraData.scheduled_end_date = scheduledEndDate
      }
      const success = await onStatusChange(newStatus, extraData)
      if (success) {
        const labels: Record<string, string> = {
          active: 'Triagem ativada com sucesso!',
          completed: 'Triagem concluída com sucesso!',
          not_started: 'Triagem resetada com sucesso!',
        }
        toast.success(labels[newStatus] || 'Status atualizado!')
      }
    } catch {
      toast.error('Erro ao atualizar status da triagem')
    } finally {
      setIsUpdating(false)
    }
  }

  const handlePauseConfirm = async () => {
    setIsUpdating(true)
    try {
      const success = await onStatusChange('paused', { 
        pause_reason: pauseReason || 'Pausado manualmente',
        scheduled_end_date: scheduledEndDate || undefined
      })
      if (success) {
        toast.success('Triagem pausada com sucesso!')
        setShowPauseForm(false)
        setPauseReason('')
      }
    } catch {
      toast.error('Erro ao pausar triagem')
    } finally {
      setIsUpdating(false)
    }
  }

  const metrics = screeningConfig?.metrics

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md rounded-md bg-white border border-lia-border-subtle dark:bg-lia-bg-primary dark:border-lia-border-subtle">
        <DialogHeader className="pb-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
              <BrainCircuit className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
            </div>
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-sm font-semibold text-gray-950 font-['Open_Sans',sans-serif]">
                Status da Triagem
              </DialogTitle>
              <p className="text-xs text-gray-500 dark:text-lia-text-tertiary truncate mt-0.5">
                {jobTitle}
              </p>
            </div>
            <Badge className={`${statusConfig.bgColor} ${statusConfig.darkBgColor} ${statusConfig.color} border-0 text-micro px-2 py-0.5 flex items-center gap-1`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </Badge>
          </div>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {screeningStatus === 'not_configured' && (
            <div className="text-center py-6">
              <AlertCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-base-ui text-gray-600 dark:text-lia-text-tertiary mb-1">
                Triagem não configurada
              </p>
              <p className="text-xs text-gray-400">
                Configure as perguntas de triagem na aba &quot;Roteiro de Triagem&quot; da vaga para poder iniciar.
              </p>
            </div>
          )}

          {screeningStatus === 'not_started' && !showPauseForm && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4">
                <p className="text-xs text-gray-700 dark:text-lia-text-secondary mb-3">
                  A triagem está configurada mas ainda não foi iniciada. Ao ativar, candidatos poderão ser triados automaticamente.
                </p>
                
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-gray-600 dark:text-lia-text-tertiary">
                    <Calendar className="w-3 h-3 inline mr-1" />
                    Data de término (opcional)
                  </Label>
                  <Input
                    type="date"
                    value={scheduledEndDate}
                    onChange={(e) => setScheduledEndDate(e.target.value)}
                    className="h-8 text-xs border-lia-border-subtle dark:border-lia-border-default dark:bg-lia-bg-elevated"
                  />
                  <p className="text-micro lia-text-secondary">
                    A triagem será concluída automaticamente nesta data
                  </p>
                </div>
              </div>

              <Button
                onClick={() => handleStatusChange('active')}
                disabled={isUpdating}
                className="w-full h-10 text-base-ui font-medium bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 gap-2"
              >
                {isUpdating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Iniciar Triagem
              </Button>
            </div>
          )}

          {screeningStatus === 'active' && !showPauseForm && (
            <div className="space-y-4">
              {metrics && (metrics.screened_count || 0) > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <Users className="w-4 h-4 lia-text-secondary mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900">{metrics.screened_count || 0}</p>
                    <p className="text-micro lia-text-secondary">Triados</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <BarChart3 className="w-4 h-4 lia-text-secondary mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900">{metrics.completion_rate || 0}%</p>
                    <p className="text-micro lia-text-secondary">Conclusão</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <CheckCircle2 className="w-4 h-4 lia-text-secondary mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900">{metrics.average_rating?.toFixed(1) || '—'}</p>
                    <p className="text-micro lia-text-secondary">Nota Média</p>
                  </div>
                </div>
              )}

              {screeningConfig?.status?.scheduled_end_date && (
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-lia-text-tertiary bg-gray-50 dark:bg-lia-bg-secondary rounded-lg px-3 py-2">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Término previsto: {new Date(screeningConfig.status.scheduled_end_date).toLocaleDateString('pt-BR')}</span>
                </div>
              )}

              {screeningConfig?.status?.activated_at && (
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-lia-text-tertiary">
                  <Clock className="w-3 h-3" />
                  <span>Ativa desde {new Date(screeningConfig.status.activated_at).toLocaleDateString('pt-BR')}</span>
                </div>
              )}
            </div>
          )}

          {screeningStatus === 'paused' && !showPauseForm && (
            <div className="space-y-4">
              <div className="bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md p-4">
                <div className="flex items-start gap-2">
                  <Pause className="w-4 h-4 text-status-warning mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-status-warning dark:text-status-warning">Triagem Pausada</p>
                    {screeningConfig?.status?.pause_reason && (
                      <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                        Motivo: {screeningConfig.status.pause_reason}
                      </p>
                    )}
                    {screeningConfig?.status?.paused_at && (
                      <p className="text-micro text-status-warning dark:text-status-warning mt-1">
                        Pausada em {new Date(screeningConfig.status.paused_at).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {screeningStatus === 'completed' && (
            <div className="space-y-4">
              <div className="bg-wedo-cyan/10 border border-wedo-cyan/30 dark:border-wedo-cyan/30 rounded-md p-4">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-wedo-cyan-dark mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-wedo-cyan-dark dark:text-wedo-cyan-dark">Triagem Concluída</p>
                    {screeningConfig?.status?.completed_at && (
                      <p className="text-micro text-wedo-cyan-dark mt-1">
                        Concluída em {new Date(screeningConfig.status.completed_at).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {metrics && (metrics.screened_count || 0) > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900">{metrics.screened_count || 0}</p>
                    <p className="text-micro lia-text-secondary">Triados</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900">{metrics.completion_rate || 0}%</p>
                    <p className="text-micro lia-text-secondary">Conclusão</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900">{metrics.average_rating?.toFixed(1) || '—'}</p>
                    <p className="text-micro lia-text-secondary">Nota Média</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {showPauseForm && (
            <div className="space-y-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4">
              <p className="text-xs font-medium text-gray-700 dark:text-lia-text-secondary">Pausar Triagem</p>
              <div className="space-y-2">
                <Label className="text-xs text-gray-600 dark:text-lia-text-tertiary">Motivo (opcional)</Label>
                <Textarea
                  value={pauseReason}
                  onChange={(e) => setPauseReason(e.target.value)}
                  placeholder="Ex: Aguardando aprovação do gestor..."
                  className="h-20 text-xs resize-none border-lia-border-subtle dark:border-lia-border-default dark:bg-lia-bg-elevated"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => { setShowPauseForm(false); setPauseReason('') }}
                  className="flex-1 h-8 text-xs border-lia-border-default dark:border-lia-border-default"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handlePauseConfirm}
                  disabled={isUpdating}
                  className="flex-1 h-8 text-xs bg-status-warning hover:bg-status-warning text-white"
                >
                  {isUpdating ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Confirmar Pausa'}
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle flex flex-col gap-2">
          {screeningStatus === 'active' && !showPauseForm && (
            <div className="flex gap-2 w-full">
              <Button
                variant="outline"
                onClick={() => handleStatusChange('paused')}
                disabled={isUpdating}
                className="flex-1 h-9 text-xs font-medium border-status-warning/30 text-status-warning hover:bg-status-warning/10 dark:border-status-warning/30 dark:text-status-warning dark:hover:bg-status-warning/20 gap-1.5"
              >
                <Pause className="w-3.5 h-3.5" />
                Pausar
              </Button>
              <Button
                variant="outline"
                onClick={() => handleStatusChange('completed')}
                disabled={isUpdating}
                className="flex-1 h-9 text-xs font-medium border-wedo-cyan/30 text-wedo-cyan-dark hover:bg-wedo-cyan/10 dark:border-wedo-cyan/30 dark:text-wedo-cyan-dark dark:hover:bg-wedo-cyan/10/20 gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Concluir
              </Button>
            </div>
          )}

          {screeningStatus === 'paused' && !showPauseForm && (
            <Button
              onClick={() => handleStatusChange('active')}
              disabled={isUpdating}
              className="w-full h-9 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 gap-1.5"
            >
              {isUpdating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Retomar Triagem
            </Button>
          )}

          {(screeningStatus === 'active' || screeningStatus === 'paused' || screeningStatus === 'completed') && !showPauseForm && onNavigateToJob && (
            <Button
              variant="outline"
              onClick={() => { onNavigateToJob(); onClose() }}
              className="w-full h-9 text-xs font-medium border-lia-border-default text-gray-700 hover:bg-gray-50 dark:border-lia-border-default dark:text-lia-text-secondary dark:hover:bg-gray-800 gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Ir para Vaga
            </Button>
          )}

          {screeningStatus === 'not_configured' && onNavigateToJob && (
            <Button
              onClick={() => { onNavigateToJob(); onClose() }}
              className="w-full h-9 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Ir para Vaga
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export { STATUS_CONFIG }
export type { ScreeningStatus, ScreeningStatusModalProps }
