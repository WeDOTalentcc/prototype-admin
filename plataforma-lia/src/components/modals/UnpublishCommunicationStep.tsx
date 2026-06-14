"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Checkbox } from"@/components/ui/checkbox"
import { Label } from"@/components/ui/label"
import { Textarea } from"@/components/ui/textarea"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import { cn } from"@/lib/utils"
import { Loader2, Mail, MessageSquare, Users } from"lucide-react"
import type { UseJobUnpublishReturn } from"./useJobUnpublish"

type NotificationChannel = 'email' | 'whatsapp' | 'both'

export interface UnpublishCommunicationStepProps {
  notificationChannel: NotificationChannel
  setNotificationChannel: (v: NotificationChannel) => void
  selectedTemplateId: string
  handleTemplateChange: (templateId: string) => void
  availableTemplates: Array<{ id: string; name: string }>
  notificationSubject: string
  setNotificationSubject: (v: string) => void
  notificationMessage: string
  setNotificationMessage: (v: string) => void
  selectedCandidateIds: Set<string>
  jobCandidates: Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
  }>
  candidatesInProposal: Array<{ id: string }>
  loadingCandidates: boolean
  toggleCandidateSelection: (candidateId: string) => void
  selectAllCandidates: () => void
  deselectAllCandidates: () => void
}

interface StepProps {
  hook: UseJobUnpublishReturn
}

export function CommunicationStep({ hook }: StepProps) {
  const {
    notificationChannel, setNotificationChannel,
    selectedTemplateId,
    notificationSubject, setNotificationSubject,
    notificationMessage, setNotificationMessage,
    selectedCandidateIds,
    loadingCandidates,
    jobCandidates, candidatesInProposal,
    availableTemplates,
    handleTemplateChange,
    toggleCandidateSelection,
    selectAllCandidates, deselectAllCandidates,
  } = hook
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'email' || notificationChannel === 'both' ? 'primary' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'whatsapp' ? 'email' : notificationChannel === 'email' ? 'both' : 'email')}
            className={cn("h-7 px-2.5 text-micro",
              (notificationChannel === 'email' || notificationChannel === 'both')
                ?"bg-lia-btn-primary-bg text-lia-btn-primary-text"
                :"border-lia-border-subtle text-lia-text-secondary"
            )}
          >
            <Mail className="w-3 h-3 mr-1" />
            Email
          </Button>
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'whatsapp' || notificationChannel === 'both' ? 'primary' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'email' ? 'whatsapp' : notificationChannel === 'whatsapp' ? 'both' : 'whatsapp')}
            className={cn("h-7 px-2.5 text-micro",
              (notificationChannel === 'whatsapp' || notificationChannel === 'both')
                ?"bg-status-success text-white hover:bg-status-success"
                :"border-lia-border-subtle text-lia-text-secondary"
            )}
          >
            <MessageSquare className="w-3 h-3 mr-1" />
            WhatsApp
          </Button>
        </div>
      </div>

      <div>
        <Label className="text-micro text-lia-text-secondary mb-1 block">Template de mensagem</Label>
        <Select value={selectedTemplateId} onValueChange={handleTemplateChange}>
          <SelectTrigger className="h-8 text-xs border-lia-border-subtle">
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
      </div>

      {notificationChannel !== 'whatsapp' && (
        <div>
          <Label className="text-micro text-lia-text-secondary mb-1 block">Assunto</Label>
          <Input
            value={notificationSubject}
            onChange={(e) => setNotificationSubject(e.target.value)}
            placeholder="Assunto do email..."
            className="h-8 text-xs border-lia-border-subtle"
          />
        </div>
      )}

      <div>
        <Label className="text-micro text-lia-text-secondary mb-1 block">Mensagem</Label>
        <Textarea
          value={notificationMessage}
          onChange={(e) => setNotificationMessage(e.target.value)}
          placeholder="Conteúdo da mensagem..."
          className="min-h-[100px] text-xs border-lia-border-subtle resize-none"
        />
        <p className="text-micro text-lia-text-tertiary mt-1" aria-live="polite" aria-atomic="true">
          Variáveis disponíveis: {'{{candidato_nome}}'}, {'{{vaga}}'}, {'{{empresa_nome}}'}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-micro text-lia-text-secondary">
            Candidatos selecionados ({selectedCandidateIds.size}/{jobCandidates.length - candidatesInProposal.length})
          </Label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllCandidates}
              className="text-micro text-lia-text-secondary hover:underline"
            >
              Selecionar todos
            </button>
            <button
              type="button"
              onClick={deselectAllCandidates}
              className="text-micro text-lia-text-tertiary hover:underline"
            >
              Limpar
            </button>
          </div>
        </div>
        <ScrollArea className="h-[120px] border border-lia-border-subtle rounded-xl p-2">
          {loadingCandidates ? (
            <div className="flex items-center justify-center h-full py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Carregando candidatos...</span>
            </div>
          ) : jobCandidates.length === 0 ? (
            <div className="flex items-center justify-center h-full py-8">
              <Users className="w-4 h-4 text-lia-text-muted mr-2" />
              <span className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Nenhum candidato encontrado</span>
            </div>
          ) : (
            <div className="space-y-1">
              {jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id)).map((candidate) => (
                <div
                  key={candidate.id}
                  className={cn("flex items-center gap-2 p-1.5 rounded-md cursor-pointer transition-colors",
                    selectedCandidateIds.has(candidate.id)
                      ?"bg-lia-bg-tertiary border border-lia-btn-primary-bg"
                      :"bg-lia-bg-primary border border-lia-border-subtle hover:border-lia-border-default"
                  )}
                  onClick={() => toggleCandidateSelection(candidate.id)}
                >
                  <Checkbox
                    checked={selectedCandidateIds.has(candidate.id)}
                    className="data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-lia-text-primary truncate">{candidate.name}</p>
                    <p className="text-micro text-lia-text-tertiary">{candidate.email || candidate.phone || 'Sem contato'}</p>
                  </div>
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary font-normal">
                    {candidate.stage}
                  </Chip>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}

export function UnpublishCommunicationStep({
  notificationChannel,
  setNotificationChannel,
  selectedTemplateId,
  handleTemplateChange,
  availableTemplates,
  notificationSubject,
  setNotificationSubject,
  notificationMessage,
  setNotificationMessage,
  selectedCandidateIds,
  jobCandidates,
  candidatesInProposal,
  loadingCandidates,
  toggleCandidateSelection,
  selectAllCandidates,
  deselectAllCandidates,
}: UnpublishCommunicationStepProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'email' || notificationChannel === 'both' ? 'primary' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'whatsapp' ? 'email' : notificationChannel === 'email' ? 'both' : 'email')}
            className={cn("h-7 px-2.5 text-micro",
              (notificationChannel === 'email' || notificationChannel === 'both')
                ?"bg-lia-btn-primary-bg text-lia-btn-primary-text"
                :"border-lia-border-subtle text-lia-text-secondary"
            )}
          >
            <Mail className="w-3 h-3 mr-1" />
            Email
          </Button>
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'whatsapp' || notificationChannel === 'both' ? 'primary' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'email' ? 'whatsapp' : notificationChannel === 'whatsapp' ? 'both' : 'whatsapp')}
            className={cn("h-7 px-2.5 text-micro",
              (notificationChannel === 'whatsapp' || notificationChannel === 'both')
                ?"bg-status-success text-white hover:bg-status-success"
                :"border-lia-border-subtle text-lia-text-secondary"
            )}
          >
            <MessageSquare className="w-3 h-3 mr-1" />
            WhatsApp
          </Button>
        </div>
      </div>

      <div>
        <Label className="text-micro text-lia-text-secondary mb-1 block">Template de mensagem</Label>
        <Select value={selectedTemplateId} onValueChange={handleTemplateChange}>
          <SelectTrigger className="h-8 text-xs border-lia-border-subtle">
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
      </div>

      {notificationChannel !== 'whatsapp' && (
        <div>
          <Label className="text-micro text-lia-text-secondary mb-1 block">Assunto</Label>
          <Input
            value={notificationSubject}
            onChange={(e) => setNotificationSubject(e.target.value)}
            placeholder="Assunto do email..."
            className="h-8 text-xs border-lia-border-subtle"
          />
        </div>
      )}

      <div>
        <Label className="text-micro text-lia-text-secondary mb-1 block">Mensagem</Label>
        <Textarea
          value={notificationMessage}
          onChange={(e) => setNotificationMessage(e.target.value)}
          placeholder="Conteúdo da mensagem..."
          className="min-h-[100px] text-xs border-lia-border-subtle resize-none"
        />
        <p className="text-micro text-lia-text-tertiary mt-1" aria-live="polite" aria-atomic="true">
          Variáveis disponíveis: {'{{candidato_nome}}'}, {'{{vaga}}'}, {'{{empresa_nome}}'}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-micro text-lia-text-secondary">
            Candidatos selecionados ({selectedCandidateIds.size}/{jobCandidates.length - candidatesInProposal.length})
          </Label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllCandidates}
              className="text-micro text-lia-text-secondary hover:underline"
            >
              Selecionar todos
            </button>
            <button
              type="button"
              onClick={deselectAllCandidates}
              className="text-micro text-lia-text-tertiary hover:underline"
            >
              Limpar
            </button>
          </div>
        </div>
        <ScrollArea className="h-[120px] border border-lia-border-subtle rounded-xl p-2">
          {loadingCandidates ? (
            <div className="flex items-center justify-center h-full py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Carregando candidatos...</span>
            </div>
          ) : jobCandidates.length === 0 ? (
            <div className="flex items-center justify-center h-full py-8">
              <Users className="w-4 h-4 text-lia-text-muted mr-2" />
              <span className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Nenhum candidato encontrado</span>
            </div>
          ) : (
            <div className="space-y-1">
              {jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id)).map((candidate) => (
                <div
                  key={candidate.id}
                  className={cn("flex items-center gap-2 p-1.5 rounded-md cursor-pointer transition-colors",
                    selectedCandidateIds.has(candidate.id)
                      ?"bg-lia-bg-tertiary border border-lia-btn-primary-bg"
                      :"bg-lia-bg-primary border border-lia-border-subtle hover:border-lia-border-default"
                  )}
                  onClick={() => toggleCandidateSelection(candidate.id)}
                >
                  <Checkbox
                    checked={selectedCandidateIds.has(candidate.id)}
                    className="data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-lia-text-primary truncate">{candidate.name}</p>
                    <p className="text-micro text-lia-text-tertiary">{candidate.email || candidate.phone || 'Sem contato'}</p>
                  </div>
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary font-normal">
                    {candidate.stage}
                  </Chip>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
