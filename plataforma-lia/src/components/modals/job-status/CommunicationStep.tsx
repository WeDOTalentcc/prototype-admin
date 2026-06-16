"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { Mail, MessageSquare, Send, Loader2 } from "lucide-react"
import type { NotificationChannel } from "./types"

interface CommunicationStepProps {
  jobCandidatesCount: number
  candidatesInProposalCount: number
  notificationChannel: NotificationChannel
  onNotificationChannelChange: (channel: NotificationChannel) => void
  templatesLoading: boolean
  selectedTemplateId: string
  onTemplateChange: (templateId: string) => void
  availableTemplates: Array<{ id: string; name: string }>
  notificationSubject: string
  onNotificationSubjectChange: (value: string) => void
  notificationMessage: string
  onNotificationMessageChange: (value: string) => void
}

export function CommunicationStep({
  jobCandidatesCount,
  candidatesInProposalCount,
  notificationChannel,
  onNotificationChannelChange,
  templatesLoading,
  selectedTemplateId,
  onTemplateChange,
  availableTemplates,
  notificationSubject,
  onNotificationSubjectChange,
  notificationMessage,
  onNotificationMessageChange,
}: CommunicationStepProps) {
  return (
    <div data-testid="communication-step" className="space-y-4">
      <div className="flex items-center gap-2 p-2.5 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle">
        <Mail className="w-4 h-4 text-lia-text-secondary" />
        <span className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
          Configure a mensagem para {jobCandidatesCount - candidatesInProposalCount} candidato(s)
        </span>
      </div>

      <div>
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Canal de Comunicação
        </Label>
        <div className="flex gap-2">
          {(['email', 'whatsapp', 'both'] as NotificationChannel[]).map((channel) => (
            <Button
              key={channel}
              type="button"
              variant={notificationChannel === channel ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onNotificationChannelChange(channel)}
              className={cn(
                "h-8 px-3 text-xs gap-1.5",
                notificationChannel === channel
                  ? "bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                  : "border border-lia-border-default text-lia-text-secondary"
              )}
            >
              {channel === 'email' && <Mail className="w-3.5 h-3.5" />}
              {channel === 'whatsapp' && <MessageSquare className="w-3.5 h-3.5" />}
              {channel === 'both' && <Send className="w-3.5 h-3.5" />}
              {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : 'Ambos'}
            </Button>
          ))}
        </div>
      </div>

      <div role="status" aria-live="polite" aria-label="Carregando...">
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Template
        </Label>
        {templatesLoading ? (
          <div className="flex items-center gap-2 p-3 bg-lia-bg-secondary rounded-xl" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-muted" />
            <span className="text-xs text-lia-text-tertiary">Carregando templates...</span>
          </div>
        ) : (
          <Select value={selectedTemplateId} onValueChange={onTemplateChange}>
            <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecione um modelo..." />
            </SelectTrigger>
            <SelectContent>
              {availableTemplates.map((template) => (
                <SelectItem key={template.id} value={template.id} className="text-xs">
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {notificationChannel !== 'whatsapp' && (
        <div>
          <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
            Assunto do Email
          </Label>
          <Input
            value={notificationSubject}
            onChange={(e) => onNotificationSubjectChange(e.target.value)}
            placeholder="Assunto do email..."
            className="h-9 text-xs border-lia-border-subtle"
          />
        </div>
      )}

      <div>
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Mensagem
        </Label>
        <Textarea
          value={notificationMessage}
          onChange={(e) => onNotificationMessageChange(e.target.value)}
          placeholder="Mensagem para os candidatos..."
          className="h-32 text-xs border-lia-border-subtle resize-none"
        />
      </div>
    </div>
  )
}
