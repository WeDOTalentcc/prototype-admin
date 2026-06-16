"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import {
  Mail,
  MessageSquare,
  ArrowRight,
  Loader2,
  Brain,
  Edit3,
  RefreshCw,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

interface StageTransitionPreviewPanelProps {
  needsMessageComposition: boolean
  selectedAction: string | null
  channel: 'email' | 'whatsapp' | 'both'
  subject: string
  setSubject: (value: string) => void
  message: string
  handleMessageChange: (value: string) => void
  isRegenerating: boolean
  isLoadingTemplates: boolean
  isMessageEdited: boolean
  showPulse: boolean
  regenerateMessage: () => void
}

export function StageTransitionPreviewPanel({
  needsMessageComposition,
  selectedAction,
  channel,
  subject,
  setSubject,
  message,
  handleMessageChange,
  isRegenerating,
  isLoadingTemplates,
  isMessageEdited,
  showPulse,
  regenerateMessage,
}: StageTransitionPreviewPanelProps) {
  return (
    <div className="w-1/2 bg-lia-bg-secondary/50 overflow-y-auto">
      <div className="p-5 space-y-4">
        {needsMessageComposition ? (
          <>
            <div className="flex items-start gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-default">
              <Brain className="w-4 h-4 text-wedo-cyan mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-lia-text-primary font-medium">
                  Mensagem personalizada por IA considerando:
                </p>
                <p className="text-micro text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                  nome, cargo, vaga e contexto do candidato
                </p>
                {isMessageEdited && (
                  <p className="text-micro text-lia-text-secondary mt-1 flex items-center gap-1">
                    <Edit3 className="w-3 h-3" />
                    (mensagem editada por você)
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <p className={cn(textStyles.label, "flex items-center gap-2")}>
                {channel === 'both' ? (
                  <span className="flex items-center -space-x-1">
                    <Mail className="h-4 w-4 text-lia-text-tertiary" />
                    <MessageSquare className="h-4 w-4 text-status-success" />
                  </span>
                ) : channel === 'email' ? <Mail className="h-4 w-4 text-lia-text-tertiary" /> : <MessageSquare className="h-4 w-4 text-status-success" />}
                Preview da Mensagem
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={regenerateMessage}
                disabled={isRegenerating}
                className="h-7 text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              >
                <RefreshCw className={cn("h-3 w-3 mr-1", isRegenerating && "animate-spin motion-reduce:animate-none")} />
                Regenerar
              </Button>
            </div>

            {isLoadingTemplates ? (
              <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-muted" />
              </div>
            ) : (
              <div className="relative" role="status" aria-live="polite" aria-label="Carregando...">
                {isRegenerating && (
                  <div className="absolute inset-0 bg-lia-bg-primary/80 rounded-xl flex items-center justify-center z-10" role="status" aria-live="polite" aria-label="Carregando...">
                    <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                      <span className="text-xs text-lia-text-secondary font-medium">Regenerando mensagem...</span>
                    </div>
                  </div>
                )}

                <div className={cn(
                  "space-y-3 transition-colors",
                  showPulse && "animate-pulse motion-reduce:animate-none"
                )}>
                  {(channel === 'email' || channel === 'both' || selectedAction === 'triagem_wsi' || selectedAction === 'agendar_entrevista') && (
                    <div>
                      <label className={textStyles.caption}>Assunto</label>
                      <Input
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        placeholder="Assunto do email"
                        className="text-xs mt-1"
                      />
                    </div>
                  )}
                  <div>
                    <label className={textStyles.caption}>Mensagem</label>
                    <Textarea
                      value={message}
                      onChange={(e) => handleMessageChange(e.target.value)}
                      placeholder="Escreva sua mensagem..."
                      className="min-h-[250px] text-xs resize-y mt-1"
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-12 h-12 bg-lia-bg-tertiary rounded-full flex items-center justify-center mb-3">
              <ArrowRight className="w-6 h-6 text-lia-text-muted" />
            </div>
            <p className={textStyles.subtitle} aria-live="polite" aria-atomic="true">Apenas mover candidato</p>
            <p className={cn(textStyles.caption, "mt-1 max-w-[250px]")} aria-live="polite" aria-atomic="true">
              O candidato será movido para a nova etapa sem envio de comunicação
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
