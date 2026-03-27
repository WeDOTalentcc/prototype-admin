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

type ScreeningStatus = 'not_configured' | 'not_started' | 'active' | 'paused' | 'completed'

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
  not_configured: { label: 'Não Configurada', color: 'text-gray-600', bgColor: 'bg-gray-100', darkBgColor: 'dark:bg-gray-800', icon: AlertCircle },
  not_started: { label: 'Não Iniciada', color: 'text-gray-700', bgColor: 'bg-gray-200', darkBgColor: 'dark:bg-gray-700', icon: Clock },
  active: { label: 'Ativa', color: 'text-green-700', bgColor: 'bg-green-100', darkBgColor: 'dark:bg-green-900/30', icon: Play },
  paused: { label: 'Pausada', color: 'text-amber-700', bgColor: 'bg-amber-100', darkBgColor: 'dark:bg-amber-900/30', icon: Pause },
  completed: { label: 'Concluída', color: 'text-blue-700', bgColor: 'bg-blue-100', darkBgColor: 'dark:bg-blue-900/30', icon: CheckCircle2 },
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
      <DialogContent className="max-w-md rounded-md bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
        <DialogHeader className="pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-100 dark:bg-gray-800">
              <BrainCircuit className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                Status da Triagem
              </DialogTitle>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
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
              <AlertCircle className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-base-ui text-gray-600 dark:text-gray-400 mb-1">
                Triagem não configurada
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                Configure as perguntas de triagem na aba &quot;Roteiro de Triagem&quot; da vaga para poder iniciar.
              </p>
            </div>
          )}

          {screeningStatus === 'not_started' && !showPauseForm && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
                <p className="text-xs text-gray-700 dark:text-gray-300 mb-3">
                  A triagem está configurada mas ainda não foi iniciada. Ao ativar, candidatos poderão ser triados automaticamente.
                </p>
                
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    <Calendar className="w-3 h-3 inline mr-1" />
                    Data de término (opcional)
                  </Label>
                  <Input
                    type="date"
                    value={scheduledEndDate}
                    onChange={(e) => setScheduledEndDate(e.target.value)}
                    className="h-8 text-xs border-gray-200 dark:border-gray-600 dark:bg-gray-700"
                  />
                  <p className="text-micro text-gray-400">
                    A triagem será concluída automaticamente nesta data
                  </p>
                </div>
              </div>

              <Button
                onClick={() => handleStatusChange('active')}
                disabled={isUpdating}
                className="w-full h-10 text-base-ui font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-2"
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
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <Users className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.screened_count || 0}</p>
                    <p className="text-micro text-gray-500">Triados</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <BarChart3 className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.completion_rate || 0}%</p>
                    <p className="text-micro text-gray-500">Conclusão</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <CheckCircle2 className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.average_rating?.toFixed(1) || '—'}</p>
                    <p className="text-micro text-gray-500">Nota Média</p>
                  </div>
                </div>
              )}

              {screeningConfig?.status?.scheduled_end_date && (
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Término previsto: {new Date(screeningConfig.status.scheduled_end_date).toLocaleDateString('pt-BR')}</span>
                </div>
              )}

              {screeningConfig?.status?.activated_at && (
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <Clock className="w-3 h-3" />
                  <span>Ativa desde {new Date(screeningConfig.status.activated_at).toLocaleDateString('pt-BR')}</span>
                </div>
              )}
            </div>
          )}

          {screeningStatus === 'paused' && !showPauseForm && (
            <div className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-4">
                <div className="flex items-start gap-2">
                  <Pause className="w-4 h-4 text-amber-600 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-amber-800 dark:text-amber-200">Triagem Pausada</p>
                    {screeningConfig?.status?.pause_reason && (
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                        Motivo: {screeningConfig.status.pause_reason}
                      </p>
                    )}
                    {screeningConfig?.status?.paused_at && (
                      <p className="text-micro text-amber-500 dark:text-amber-500 mt-1">
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
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-blue-800 dark:text-blue-200">Triagem Concluída</p>
                    {screeningConfig?.status?.completed_at && (
                      <p className="text-micro text-blue-500 mt-1">
                        Concluída em {new Date(screeningConfig.status.completed_at).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {metrics && (metrics.screened_count || 0) > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.screened_count || 0}</p>
                    <p className="text-micro text-gray-500">Triados</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.completion_rate || 0}%</p>
                    <p className="text-micro text-gray-500">Conclusão</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-center">
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-50">{metrics.average_rating?.toFixed(1) || '—'}</p>
                    <p className="text-micro text-gray-500">Nota Média</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {showPauseForm && (
            <div className="space-y-3 bg-gray-50 dark:bg-gray-800 rounded-md p-4">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Pausar Triagem</p>
              <div className="space-y-2">
                <Label className="text-xs text-gray-600 dark:text-gray-400">Motivo (opcional)</Label>
                <Textarea
                  value={pauseReason}
                  onChange={(e) => setPauseReason(e.target.value)}
                  placeholder="Ex: Aguardando aprovação do gestor..."
                  className="h-20 text-xs resize-none border-gray-200 dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => { setShowPauseForm(false); setPauseReason('') }}
                  className="flex-1 h-8 text-xs border-gray-300 dark:border-gray-600"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handlePauseConfirm}
                  disabled={isUpdating}
                  className="flex-1 h-8 text-xs bg-amber-600 hover:bg-amber-700 text-white"
                >
                  {isUpdating ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Confirmar Pausa'}
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="pt-4 border-t border-gray-200 dark:border-gray-700 flex flex-col gap-2">
          {screeningStatus === 'active' && !showPauseForm && (
            <div className="flex gap-2 w-full">
              <Button
                variant="outline"
                onClick={() => handleStatusChange('paused')}
                disabled={isUpdating}
                className="flex-1 h-9 text-xs font-medium border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-900/20 gap-1.5"
              >
                <Pause className="w-3.5 h-3.5" />
                Pausar
              </Button>
              <Button
                variant="outline"
                onClick={() => handleStatusChange('completed')}
                disabled={isUpdating}
                className="flex-1 h-9 text-xs font-medium border-blue-300 text-blue-700 hover:bg-blue-50 dark:border-blue-700 dark:text-blue-400 dark:hover:bg-blue-900/20 gap-1.5"
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
              className="w-full h-9 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-1.5"
            >
              {isUpdating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Retomar Triagem
            </Button>
          )}

          {(screeningStatus === 'active' || screeningStatus === 'paused' || screeningStatus === 'completed') && !showPauseForm && onNavigateToJob && (
            <Button
              variant="outline"
              onClick={() => { onNavigateToJob(); onClose() }}
              className="w-full h-9 text-xs font-medium border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Ir para Vaga
            </Button>
          )}

          {screeningStatus === 'not_configured' && onNavigateToJob && (
            <Button
              onClick={() => { onNavigateToJob(); onClose() }}
              className="w-full h-9 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-1.5"
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
