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
import { MessageSquare, Globe, Phone, Loader2 } from "lucide-react"
import { toast } from "sonner"
import type { ScreeningConfig } from "@/hooks/useScreeningConfig"

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
  const [whatsappEnabled, setWhatsappEnabled] = useState(config?.channels?.whatsapp?.enabled ?? true)
  const [chatWebEnabled, setChatWebEnabled] = useState(config?.channels?.chat_web?.enabled ?? true)
  const [phoneEnabled, setPhoneEnabled] = useState(config?.channels?.phone?.enabled ?? false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setWhatsappEnabled(config?.channels?.whatsapp?.enabled ?? true)
      setChatWebEnabled(config?.channels?.chat_web?.enabled ?? true)
      setPhoneEnabled(config?.channels?.phone?.enabled ?? false)
    }
  }, [isOpen, config])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const success = await updateConfig({
        channels: {
          whatsapp: { enabled: whatsappEnabled, label: 'WhatsApp' },
          chat_web: { enabled: chatWebEnabled, label: 'Chat Web' },
          phone: { enabled: phoneEnabled, label: 'Ligação' },
        }
      })
      
      if (success) {
        toast.success("Canais de comunicação atualizados com sucesso")
        onClose()
      } else {
        toast.error("Erro ao atualizar canais de comunicação")
      }
    } catch (error) {
      toast.error("Erro ao salvar configurações")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md rounded-md bg-white border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <DialogHeader className="pb-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
              <MessageSquare className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
                Canais de Comunicação
              </DialogTitle>
              <p className="text-xs lia-text-base mt-0.5" aria-live="polite" aria-atomic="true">
                Defina por onde a LIA pode contatar candidatos
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="flex items-center justify-between p-3 rounded-md bg-gray-50 border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-status-success/10 flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-status-success" />
              </div>
              <div>
                <Label className="text-xs font-medium text-lia-text-primary">WhatsApp</Label>
                <p className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">Canal principal de triagem</p>
              </div>
            </div>
            <Switch
              checked={whatsappEnabled}
              onCheckedChange={setWhatsappEnabled}
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-md bg-gray-50 border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
                <Globe className="w-4 h-4 text-wedo-cyan-dark" />
              </div>
              <div>
                <Label className="text-xs font-medium text-lia-text-primary">Chat Web</Label>
                <p className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">Widget integrado no site</p>
              </div>
            </div>
            <Switch
              checked={chatWebEnabled}
              onCheckedChange={setChatWebEnabled}
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-md bg-gray-50 border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-wedo-orange/10 flex items-center justify-center">
                <Phone className="w-4 h-4 text-wedo-orange" />
              </div>
              <div>
                <Label className="text-xs font-medium text-lia-text-primary">Ligação</Label>
                <p className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">Chamada de voz automatizada</p>
              </div>
            </div>
            <Switch
              checked={phoneEnabled}
              onCheckedChange={setPhoneEnabled}
            />
          </div>
        </div>

        <DialogFooter className="pt-4 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-white border border-lia-border-default hover:bg-gray-50 lia-text-base dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 dark:text-lia-text-primary"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
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
