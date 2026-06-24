"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CalendarCheck, Target, Calendar, Clock, Timer, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { TOAST_MESSAGES } from "@/constants/toast-messages"
import type { ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"

interface ScreeningSchedulingModalProps {
  isOpen: boolean
  onClose: () => void
  config: ScreeningConfig
  updateConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>
}

export function ScreeningSchedulingModal({
  isOpen,
  onClose,
  config,
  updateConfig,
}: ScreeningSchedulingModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('screening-scheduling', isOpen)

  const [autoEnabled, setAutoEnabled] = useState(config?.scheduling?.auto_enabled ?? true)
  const [minScoreForAuto, setMinScoreForAuto] = useState(config?.scheduling?.min_score_for_auto ?? 75)
  const [calendarProvider, setCalendarProvider] = useState(config?.scheduling?.calendar_provider || 'Microsoft')
  const [availableHours, setAvailableHours] = useState(config?.scheduling?.available_hours || '9h-18h')
  const [interviewDuration, setInterviewDuration] = useState(config?.scheduling?.interview_duration_min ?? 45)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setAutoEnabled(config?.scheduling?.auto_enabled ?? true)
      setMinScoreForAuto(config?.scheduling?.min_score_for_auto ?? 75)
      setCalendarProvider(config?.scheduling?.calendar_provider || 'Microsoft')
      setAvailableHours(config?.scheduling?.available_hours || '9h-18h')
      setInterviewDuration(config?.scheduling?.interview_duration_min ?? 45)
    }
  }, [isOpen, config])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const success = await updateConfig({
        scheduling: {
          auto_enabled: autoEnabled,
          min_score_for_auto: minScoreForAuto,
          calendar_provider: calendarProvider,
          available_hours: availableHours,
          interview_duration_min: interviewDuration,
        }
      })
      
      if (success) {
        toast.success("Configurações de agendamento atualizadas com sucesso")
        onClose()
      } else {
        toast.error(TOAST_MESSAGES.SCREENING_CONFIG.UPDATE_SCHEDULING_ERROR)
      }
    } catch (error) {
      toast.error(TOAST_MESSAGES.SCREENING_CONFIG.SAVE_ERROR)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md rounded-xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-lia-bg-tertiary">
              <CalendarCheck className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Agendamento Automático
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                Configure o agendamento automático de entrevistas
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <CalendarCheck className="w-4 h-4 text-lia-text-secondary" />
              <div>
                <Label className="text-xs font-medium text-lia-text-primary">Agendamento Automático</Label>
                <p className="text-micro text-lia-text-secondary">Agendar entrevistas automaticamente</p>
              </div>
            </div>
            <Switch
              checked={autoEnabled}
              onCheckedChange={setAutoEnabled}
            />
          </div>

          <div className={`space-y-3 ${!autoEnabled ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-lia-text-secondary" />
                  <Label className="text-xs font-medium text-lia-text-primary">Score Mínimo para Auto-agendar</Label>
                </div>
                <span className="text-micro font-semibold text-lia-text-primary bg-lia-bg-tertiary px-2 py-0.5 rounded-full">
                  {minScoreForAuto}%
                </span>
              </div>
              <Slider
                value={[minScoreForAuto]}
                onValueChange={(value) => setMinScoreForAuto(value[0])}
                min={0}
                max={100}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-lia-text-secondary" />
                <Label className="text-xs font-medium text-lia-text-primary">Provedor de Calendário</Label>
              </div>
              <Select value={calendarProvider} onValueChange={setCalendarProvider}>
                <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
                  <SelectValue placeholder="Selecione o provedor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Microsoft" className="text-xs">Microsoft (Outlook/Teams)</SelectItem>
                  <SelectItem value="Google" className="text-xs">Google (Calendar/Meet)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-lia-text-secondary" />
                <Label className="text-xs font-medium text-lia-text-primary">Horários Disponíveis</Label>
              </div>
              <Input
                value={availableHours}
                onChange={(e) => setAvailableHours(e.target.value)}
                placeholder="Ex: 9h-18h"
                className="h-9 text-xs border-lia-border-subtle"
              />
              <p className="text-micro text-lia-text-secondary">
                Janela de horários para agendamento (ex: 9h-12h, 14h-18h)
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Timer className="w-4 h-4 text-lia-text-secondary" />
                <Label className="text-xs font-medium text-lia-text-primary">Duração da Entrevista</Label>
              </div>
              <Select value={String(interviewDuration)} onValueChange={(v) => setInterviewDuration(Number(v))}>
                <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
                  <SelectValue placeholder="Selecione a duração" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15" className="text-xs">15 minutos</SelectItem>
                  <SelectItem value="30" className="text-xs">30 minutos</SelectItem>
                  <SelectItem value="45" className="text-xs">45 minutos</SelectItem>
                  <SelectItem value="60" className="text-xs">60 minutos</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter className="pt-4 border-t border-lia-border-subtle bg-lia-bg-secondary gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover text-lia-text-secondary dark:hover:bg-lia-btn-primary-bg"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                Salvando...
              </>
            ) : (
              'Salvar Alterações'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
