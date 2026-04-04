"use client"

import React from "react"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  FileText, MessageSquare, Send, CheckCircle, Info
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { CollectionMode } from "@/hooks/use-data-request-config"

interface DataRequestCollectionSectionProps {
  isEditing: boolean
  config: {
    collectionMode: CollectionMode
    collectionMessages: {
      initialRequest: string
      choicePrompt: string
      chatStartMessage: string
      documentReceived: string
      pendingReminder: string
      allComplete: string
    }
  }
  updateGeneralConfig: (updates: Record<string, unknown>) => void
  updateCollectionMessages: (updates: Partial<DataRequestCollectionSectionProps['config']['collectionMessages']>) => void
}

export function DataRequestCollectionSection({
  isEditing,
  config,
  updateGeneralConfig,
  updateCollectionMessages,
}: DataRequestCollectionSectionProps) {
  return (
    <div className="space-y-4">
      <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
        <Label className="text-xs font-medium text-lia-text-primary mb-2 block">
          Como o candidato responde?
        </Label>
        {isEditing ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {[
              { value: 'portal_only' as CollectionMode, label: 'Apenas Portal', desc: 'Link direto para formulário', icon: FileText },
              { value: 'chat_only' as CollectionMode, label: 'Apenas Chat', desc: 'Conversa pergunta por pergunta', icon: MessageSquare },
              { value: 'candidate_choice' as CollectionMode, label: 'Candidato Escolhe', desc: 'LIA pergunta preferência', icon: CheckCircle },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => updateGeneralConfig({ collectionMode: option.value })}
                className={cn(
                  "p-3 rounded-md border-2 text-left transition-colors",
                  config.collectionMode === option.value
                    ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:border-lia-border-subtle dark:bg-lia-bg-secondary"
                    : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <option.icon className={cn(
                    "w-4 h-4",
                    config.collectionMode === option.value ? "text-lia-text-primary" : "text-lia-text-tertiary"
                  )} />
                  <span className={cn(
                    "text-xs font-medium",
                    config.collectionMode === option.value ? "text-lia-text-primary" : "text-lia-text-primary"
                  )}>
                    {option.label}
                  </span>
                </div>
                <p className="text-micro text-lia-text-secondary">{option.desc}</p>
                {option.value === 'candidate_choice' && (
                  <Badge className="mt-1 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated text-micro h-4">Recomendado</Badge>
                )}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated text-micro">
              {config.collectionMode === 'portal_only' && 'Apenas Portal'}
              {config.collectionMode === 'chat_only' && 'Apenas Chat'}
              {config.collectionMode === 'candidate_choice' && 'Candidato Escolhe'}
            </Badge>
            <span className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              {config.collectionMode === 'portal_only' && '- Envia link direto para formulário'}
              {config.collectionMode === 'chat_only' && '- Coleta via conversa no WhatsApp'}
              {config.collectionMode === 'candidate_choice' && '- LIA pergunta preferência ao candidato'}
            </span>
          </div>
        )}
      </div>

      <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-4">
        <h4 className="text-xs font-medium text-lia-text-primary mb-3 flex items-center gap-2">
          <Send className="w-3.5 h-3.5 text-lia-text-primary" />
          Mensagens do WhatsApp
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="w-3 h-3 text-lia-text-tertiary" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-micro">
                  Use variáveis: {'{{nome}}'}, {'{{empresa}}'}, {'{{campo}}'}, {'{{proximo_campo}}'}, {'{{campos_pendentes}}'}, {'{{dias_restantes}}'}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </h4>
        <div className="space-y-3">
          <div>
            <Label className="text-micro text-lia-text-secondary mb-1 block">Solicitação Inicial</Label>
            {isEditing ? (
              <textarea
                value={config.collectionMessages.initialRequest}
                onChange={(e) => updateCollectionMessages({ initialRequest: e.target.value })}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
              />
            ) : (
              <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                {config.collectionMessages.initialRequest}
              </p>
            )}
          </div>

          {(config.collectionMode === 'candidate_choice') && (
            <div>
              <Label className="text-micro text-lia-text-secondary mb-1 block">Mensagem de Escolha</Label>
              {isEditing ? (
                <textarea
                  value={config.collectionMessages.choicePrompt}
                  onChange={(e) => updateCollectionMessages({ choicePrompt: e.target.value })}
                  rows={3}
                  className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                />
              ) : (
                <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                  {config.collectionMessages.choicePrompt}
                </p>
              )}
            </div>
          )}

          {(config.collectionMode === 'chat_only' || config.collectionMode === 'candidate_choice') && (
            <>
              <div>
                <Label className="text-micro text-lia-text-secondary mb-1 block">Início da Coleta via Chat</Label>
                {isEditing ? (
                  <textarea
                    value={config.collectionMessages.chatStartMessage}
                    onChange={(e) => updateCollectionMessages({ chatStartMessage: e.target.value })}
                    rows={2}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                    {config.collectionMessages.chatStartMessage}
                  </p>
                )}
              </div>

              <div>
                <Label className="text-micro text-lia-text-secondary mb-1 block">Confirmação de Documento</Label>
                {isEditing ? (
                  <textarea
                    value={config.collectionMessages.documentReceived}
                    onChange={(e) => updateCollectionMessages({ documentReceived: e.target.value })}
                    rows={1}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                    {config.collectionMessages.documentReceived}
                  </p>
                )}
              </div>
            </>
          )}

          <div>
            <Label className="text-micro text-lia-text-secondary mb-1 block">Lembrete de Pendência</Label>
            {isEditing ? (
              <textarea
                value={config.collectionMessages.pendingReminder}
                onChange={(e) => updateCollectionMessages({ pendingReminder: e.target.value })}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
              />
            ) : (
              <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                {config.collectionMessages.pendingReminder}
              </p>
            )}
          </div>

          <div>
            <Label className="text-micro text-lia-text-secondary mb-1 block">Confirmação Final</Label>
            {isEditing ? (
              <textarea
                value={config.collectionMessages.allComplete}
                onChange={(e) => updateCollectionMessages({ allComplete: e.target.value })}
                rows={1}
                className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
              />
            ) : (
              <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                {config.collectionMessages.allComplete}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
