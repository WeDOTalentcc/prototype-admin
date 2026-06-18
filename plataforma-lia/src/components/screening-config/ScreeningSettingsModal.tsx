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
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, Target, Clock, RefreshCw, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { TOAST_MESSAGES } from "@/constants/toast-messages"
import type { ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"

interface ScreeningSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  config: ScreeningConfig
  updateConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>
}

export function ScreeningSettingsModal({
  isOpen,
  onClose,
  config,
  updateConfig,
}: ScreeningSettingsModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('screening-settings', isOpen)

  const [minScore, setMinScore] = useState(config?.settings?.min_score ?? 70)
  const [responseTimeout, setResponseTimeout] = useState(config?.settings?.response_timeout_hours ?? 48)
  const [maxRetries, setMaxRetries] = useState(config?.settings?.max_retries ?? 2)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setMinScore(config?.settings?.min_score ?? 70)
      setResponseTimeout(config?.settings?.response_timeout_hours ?? 48)
      setMaxRetries(config?.settings?.max_retries ?? 2)
    }
  }, [isOpen, config])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const success = await updateConfig({
        settings: {
          min_score: minScore,
          response_timeout_hours: responseTimeout,
          max_retries: maxRetries,
        }
      })
      
      if (success) {
        toast.success("Configurações de triagem atualizadas com sucesso")
        onClose()
      } else {
        toast.error(TOAST_MESSAGES.SCREENING_CONFIG.UPDATE_SETTINGS_ERROR)
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
              <Settings className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Configurações de Triagem
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                Defina os parâmetros para aprovação e timeout
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-lia-text-secondary" />
                <Label className="text-xs font-medium text-lia-text-primary">Score Mínimo para Aprovação</Label>
              </div>
              <span className="text-micro font-semibold text-lia-text-primary bg-lia-bg-tertiary px-2 py-0.5 rounded-full">
                {minScore}%
              </span>
            </div>
            <Slider
              value={[minScore]}
              onValueChange={(value) => setMinScore(value[0])}
              min={0}
              max={100}
              step={5}
              className="w-full"
            />
            <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              Candidatos com nota abaixo de {minScore}% serão reprovados automaticamente
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-lia-text-secondary" />
              <Label className="text-xs font-medium text-lia-text-primary">Tempo de Resposta</Label>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={responseTimeout}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 1
                  setResponseTimeout(Math.min(168, Math.max(1, value)))
                }}
                min={1}
                max={168}
                className="w-24 h-9 text-xs border-lia-border-subtle"
              />
              <span className="text-xs text-lia-text-tertiary">horas</span>
            </div>
            <p className="text-micro text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
              Tempo máximo de espera para resposta do candidato (1-168h)
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
              <Label className="text-xs font-medium text-lia-text-primary">Máximo de Retentativas</Label>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={maxRetries}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0
                  setMaxRetries(Math.min(5, Math.max(0, value)))
                }}
                min={0}
                max={5}
                className="w-24 h-9 text-xs border-lia-border-subtle"
              />
              <span className="text-xs text-lia-text-secondary">tentativas</span>
            </div>
            <p className="text-micro text-lia-text-secondary">
              Número de tentativas de recontato antes de descartar (0-5)
            </p>
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
