"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  Mail,
  MessageSquare,
  ChevronRight,
  AlertCircle,
  Brain,
  Check,
} from"lucide-react"
import { textStyles, badgeStyles } from"@/lib/design-tokens"
import { cn } from"@/lib/utils"
import type { CommunicationTemplate } from"@/hooks/chat/use-communication-templates"
import {
  COLOR_CLASSES,
  getStageDisplayName,
  getWsiClassificationColor,
  type Candidate,
  type JobVacancy,
  type WsiData,
  type TransitionAction,
  type TransitionActionType,
} from"./stage-transition-utils"

interface StageTransitionLeftPanelProps {
  candidate: Candidate
  job: JobVacancy | null
  currentStage: string
  newStage: string
  wsiData?: WsiData
  headerColor: 'red' | 'gray'
  suggestedActions: TransitionAction[]
  selectedAction: TransitionActionType | null
  setSelectedAction: (action: TransitionActionType) => void
  channel: 'email' | 'whatsapp' | 'both'
  setChannel: (channel: 'email' | 'whatsapp' | 'both') => void
  needsMessageComposition: TransitionActionType | boolean | null
  filteredTemplates: CommunicationTemplate[]
  selectedTemplateId: string
  handleTemplateSelect: (template: CommunicationTemplate) => void
}

export function StageTransitionLeftPanel({
  candidate,
  job,
  currentStage,
  newStage,
  wsiData,
  headerColor,
  suggestedActions,
  selectedAction,
  setSelectedAction,
  channel,
  setChannel,
  needsMessageComposition,
  filteredTemplates,
  selectedTemplateId,
  handleTemplateSelect,
}: StageTransitionLeftPanelProps) {
  return (
    <div className="w-1/2 border-r border-lia-border-subtle overflow-y-auto">
      <div className="p-5 space-y-5">
        <div className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-secondary text-xs">
                {candidate.name?.charAt(0) || '?'}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className={textStyles.subtitle}>{candidate.name}</p>
              <p className={textStyles.caption}>
                {candidate.current_title}
                {candidate.current_company && ` @ ${candidate.current_company}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" muted className={badgeStyles.default}>
              {getStageDisplayName(currentStage)}
            </Chip>
            <ChevronRight className="h-4 w-4 text-lia-text-muted" />
            <Chip variant={headerColor === 'red' ? 'danger' : 'neutral'}>
              {getStageDisplayName(newStage)}
            </Chip>
          </div>
        </div>

        {wsiData && (
          <div className="flex items-center gap-2 mt-2">
            <Chip variant="neutral" muted className={cn("text-xs px-2 py-0.5 font-medium",
              getWsiClassificationColor(wsiData.classification).bg,
              getWsiClassificationColor(wsiData.classification).text
            )}>
              WSI: {wsiData.overall_wsi}% ({wsiData.classification})
            </Chip>
          </div>
        )}

        {job && (
          <div className="flex items-center gap-2 text-lia-text-secondary">
            <span className={textStyles.caption} aria-live="polite" aria-atomic="true">Vaga:</span>
            <span className={textStyles.label}>{job.title}</span>
            {job.department && (
              <span className={textStyles.caption}>• {job.department}</span>
            )}
          </div>
        )}

        <div className="space-y-3">
          <p className={cn(textStyles.label,"mb-2")}>Selecione uma ação:</p>
          <div className="grid gap-2">
            {suggestedActions.map((action) => {
              const colors = COLOR_CLASSES[action.color]
              const isSelected = selectedAction === action.id

              return (
                <button
                  key={action.id}
                  onClick={() => setSelectedAction(action.id)}
                  className={cn("flex items-center gap-3 p-3 rounded-md border transition-colors text-left",
                    isSelected
                      ? cn(colors.selectedBg, colors.selectedBorder,"ring-1", action.color === 'cyan' ?"ring-lia-btn-primary-bg/20" : action.color === 'red' ?"ring-red-300" : action.color === 'green' ?"ring-emerald-300" :"ring-lia-border-default")
                      : cn(colors.bg, colors.border,"hover:border-lia-border-default")
                  )}
                >
                  <div className={cn("flex items-center justify-center w-8 h-8 rounded-full",
                    isSelected ? colors.selectedBg : colors.bg
                  )}>
                    <span className={colors.icon}>{action.icon}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={cn(textStyles.subtitle, colors.text)}>
                        {action.name}
                      </span>
                      {action.recommended && (
                        <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary text-micro px-1.5 py-0">
                          <Brain className="h-3 w-3 mr-0.5 text-wedo-cyan" />
                          Recomendado
                        </Chip>
                      )}
                    </div>
                    <p className={textStyles.caption}>{action.description}</p>
                  </div>
                  {isSelected && (
                    <Check className={cn("h-5 w-5", colors.icon)} />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {needsMessageComposition && selectedAction !== 'triagem_wsi' && selectedAction !== 'agendar_entrevista' && (
          <div className="space-y-2">
            <p className={textStyles.label}>Canal de Envio</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setChannel('email')}
                className={cn("flex items-center gap-2 p-3 rounded-md border transition-colors",
                  channel === 'email'
                    ? 'border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary'
                    : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
                )}
              >
                <Mail className="w-4 h-4" />
                <div className="text-left">
                  <div className="text-xs font-medium">Email</div>
                  <div className="text-micro opacity-70 truncate max-w-[120px]">{candidate.email || 'Não informado'}</div>
                </div>
              </button>
              <button
                onClick={() => setChannel('whatsapp')}
                className={cn("flex items-center gap-2 p-3 rounded-md border transition-colors",
                  channel === 'whatsapp'
                    ? 'border-status-success/30 '
                    : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
                )}
              >
                <MessageSquare className="w-4 h-4" />
                <div className="text-left">
                  <div className="text-xs font-medium">WhatsApp</div>
                  <div className="text-micro opacity-70">{candidate.phone || 'Não informado'}</div>
                </div>
              </button>
              <button
                onClick={() => setChannel('both')}
                className={cn("flex items-center gap-2 p-3 rounded-md border transition-colors",
                  channel === 'both'
                    ? 'border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary'
                    : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
                )}
              >
                <div className="flex items-center -space-x-1">
                  <Mail className="w-3.5 h-3.5" />
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>
                <div className="text-left">
                  <div className="text-xs font-medium">Ambos</div>
                  <div className="text-micro opacity-70">Email + WA</div>
                </div>
              </button>
            </div>
          </div>
        )}

        {needsMessageComposition && filteredTemplates.length > 0 && (
          <div className="space-y-2">
            <p className={textStyles.label}>Template (opcional)</p>
            <Select
              value={selectedTemplateId}
              onValueChange={(value) => {
                const template = filteredTemplates.find(t => t.id === value)
                if (template) handleTemplateSelect(template)
              }}
            >
              <SelectTrigger className="text-xs">
                <SelectValue placeholder="Selecionar modelo..." />
              </SelectTrigger>
              <SelectContent>
                {filteredTemplates.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {needsMessageComposition && (
          <div className="flex items-center gap-2 p-2 bg-status-warning/10 rounded-xl border border-status-warning/30">
            <AlertCircle className="h-4 w-4 text-status-warning shrink-0" />
            <p className="text-xs text-status-warning" aria-live="polite" aria-atomic="true">
              {channel === 'both' && candidate.email && candidate.phone
                ? `Email para: ${candidate.email} + WhatsApp para: ${candidate.phone}`
                : channel === 'both'
                ? 'Verifique se o candidato possui email e telefone cadastrados'
                : channel === 'email' && candidate.email
                ? `Email será enviado para: ${candidate.email}`
                : channel === 'whatsapp' && candidate.phone
                ? `WhatsApp será enviado para: ${candidate.phone}`
                : 'Verifique se o candidato possui email/telefone cadastrado'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
