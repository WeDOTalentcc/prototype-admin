"use client"

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
import { Label } from "@/components/ui/label"
import { MessageSquare, Globe, Phone, Mic, Loader2, Power } from "lucide-react"
import { toast } from "sonner"
import { TOAST_MESSAGES } from "@/constants/toast-messages"
import type { ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"

interface ScreeningChannelsModalProps {
  isOpen: boolean
  onClose: () => void
  config: ScreeningConfig
  updateConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>
}

export function ScreeningChannelsModal({
  isOpen,
  onClose,
  config,
  updateConfig,
}: ScreeningChannelsModalProps) {
  const [masterEnabled, setMasterEnabled] = useState(config?.channels_master_enabled ?? true)
  const [whatsappEnabled, setWhatsappEnabled] = useState(config?.channels?.whatsapp?.enabled ?? true)
  const [chatWebEnabled, setChatWebEnabled] = useState(config?.channels?.chat_web?.enabled ?? true)
  const [phonePstnEnabled, setPhonePstnEnabled] = useState(config?.channels?.phone_pstn?.enabled ?? false)
  const [voiceWebEnabled, setVoiceWebEnabled] = useState(config?.channels?.voice_web?.enabled ?? true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setMasterEnabled(config?.channels_master_enabled ?? true)
      setWhatsappEnabled(config?.channels?.whatsapp?.enabled ?? true)
      setChatWebEnabled(config?.channels?.chat_web?.enabled ?? true)
      setPhonePstnEnabled(config?.channels?.phone_pstn?.enabled ?? false)
      setVoiceWebEnabled(config?.channels?.voice_web?.enabled ?? true)
    }
  }, [isOpen, config])

  const handleMasterToggle = (next: boolean) => {
    setMasterEnabled(next)
    setWhatsappEnabled(next)
    setChatWebEnabled(next)
    setPhonePstnEnabled(next)
    setVoiceWebEnabled(next)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const success = await updateConfig({
        channels_master_enabled: masterEnabled,
        channels: {
          whatsapp: { enabled: whatsappEnabled, label: 'WhatsApp' },
          chat_web: { enabled: chatWebEnabled, label: 'Chat Web' },
          phone_pstn: { enabled: phonePstnEnabled, label: 'Ligação (PSTN)' },
          voice_web: { enabled: voiceWebEnabled, label: 'Voz no Navegador' },
        }
      })

      if (success) {
        toast.success("Canais de comunicação atualizados com sucesso")
        onClose()
      } else {
        toast.error(TOAST_MESSAGES.SCREENING_CONFIG.UPDATE_CHANNELS_ERROR)
      }
    } catch (_error) {
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
              <MessageSquare className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Canais de Comunicação
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                Defina por onde a LIA pode contatar candidatos
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {/* Master toggle */}
          <div className={`flex items-center justify-between p-3 rounded-xl border ${masterEnabled ? 'bg-lia-bg-secondary border-lia-border-subtle' : 'bg-lia-bg-tertiary border-lia-border-default'}`}>
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-md flex items-center justify-center ${masterEnabled ? 'bg-lia-btn-primary-bg/15' : 'bg-lia-bg-tertiary'}`}>
                <Power className={`w-4 h-4 ${masterEnabled ? 'text-lia-btn-primary-bg' : 'text-lia-text-muted'}`} />
              </div>
              <div>
                <Label className="text-xs font-semibold text-lia-text-primary">Triagem Habilitada</Label>
                <p className="text-micro text-lia-text-tertiary">Desligue para suspender todos os canais</p>
              </div>
            </div>
            <Switch checked={masterEnabled} onCheckedChange={handleMasterToggle} />
          </div>

          <div className={`space-y-2 ${masterEnabled ? '' : 'opacity-50 pointer-events-none'}`}>
            <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
                  <Globe className="w-4 h-4 text-wedo-cyan-dark" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-lia-text-primary">Chat Web</Label>
                  <p className="text-micro text-lia-text-tertiary">Triagem por chat de texto no navegador</p>
                </div>
              </div>
              <Switch checked={chatWebEnabled} onCheckedChange={setChatWebEnabled} disabled={!masterEnabled} />
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-md bg-status-success/10 flex items-center justify-center">
                  <MessageSquare className="w-4 h-4 text-status-success" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-lia-text-primary">WhatsApp</Label>
                  <p className="text-micro text-lia-text-tertiary">Triagem por mensagem assíncrona</p>
                </div>
              </div>
              <Switch checked={whatsappEnabled} onCheckedChange={setWhatsappEnabled} disabled={!masterEnabled} />
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-md bg-wedo-orange/10 flex items-center justify-center">
                  <Phone className="w-4 h-4 text-wedo-orange" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-lia-text-primary">Ligação (PSTN)</Label>
                  <p className="text-micro text-lia-text-tertiary">Chamada telefônica via Twilio Voice</p>
                </div>
              </div>
              <Switch checked={phonePstnEnabled} onCheckedChange={setPhonePstnEnabled} disabled={!masterEnabled} />
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-md bg-wedo-blue/10 flex items-center justify-center">
                  <Mic className="w-4 h-4 text-wedo-blue" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-lia-text-primary">Voz no Navegador</Label>
                  <p className="text-micro text-lia-text-tertiary">Conversa por voz via Gemini Live</p>
                </div>
              </div>
              <Switch checked={voiceWebEnabled} onCheckedChange={setVoiceWebEnabled} disabled={!masterEnabled} />
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
