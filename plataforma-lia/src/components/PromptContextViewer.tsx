"use client"

import React from"react"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { LIAIcon } from"@/components/ui/lia-icon"
import { Users } from"lucide-react"
import { ContextPill } from"@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from"@/components/ui/quick-action-chips"

interface ContextPillData {
  icon: React.ReactNode
  primaryText: string
  secondaryText: string
  onDismiss?: () => void
}

interface PromptContextViewerProps {
  candidateContext: Record<string, unknown>
  selectedCandidates: Record<string, unknown>[]
  contextPill?: ContextPillData
  quickActions?: QuickAction[]
}

export function PromptContextViewer({
  candidateContext,
  selectedCandidates,
  contextPill,
  quickActions = []
}: PromptContextViewerProps) {
  // TODO: fix type - cast to any for dynamic data access
  const ctx = candidateContext as any
  return (
    <>
      {candidateContext && (
        <div className="bg-wedo-green-light/5 rounded-xl p-3 border border-wedo-green-light/20">
          <div className="flex items-center gap-2 mb-2">
            <LIAIcon size="sm" />
            <span className="text-base-ui font-semibold text-lia-text-primary">
              Análise LIA para candidato específico
            </span>
          </div>
          <div className="flex items-center gap-3 bg-lia-bg-primary rounded-xl px-3 py-2 border border-lia-border-subtle">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-wedo-green-light/10 text-lia-text-muted-light text-sm">
                {ctx.name?.split(' ').map((n: string) => n[0]).join('') || 'C'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-medium text-lia-text-primary text-base-ui">
                {ctx.name}
              </div>
              <div className="text-xs text-lia-text-primary">
                {ctx.position} • Score: {ctx.liaAnalysis?.score || ctx.score}%
              </div>
            </div>
            <Chip variant="neutral" muted className="bg-wedo-green-light/10 text-lia-text-muted-light border-0 text-micro">
              Foco Individual
            </Chip>
          </div>
        </div>
      )}

      {!candidateContext && selectedCandidates.length > 0 && (
        <div className="bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-lia-text-secondary" />
            <span className="text-base-ui font-semibold text-lia-text-primary">
              {selectedCandidates.length} candidato{selectedCandidates.length > 1 ? 's' : ''} selecionado{selectedCandidates.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCandidates.slice(0, 3).map((candidate, index) => {
              const c = candidate as any // TODO: fix type
              return (
                <div key={c.name || index} className="flex items-center gap-1 bg-lia-bg-primary rounded-md px-2 py-1 border border-lia-border-subtle">
                  <Avatar className="w-4 h-4">
                    <AvatarFallback className="bg-lia-interactive-active text-lia-text-secondary text-xs">
                      {c.name?.charAt(0) || 'C'}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-xs text-lia-text-primary">
                    {c.name || `Candidato ${index + 1}`}
                  </span>
                </div>
              )
            })}
            {selectedCandidates.length > 3 && (
              <div className="px-2 py-1 bg-lia-bg-tertiary rounded-full text-xs text-lia-text-primary">
                +{selectedCandidates.length - 3} mais
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export function PromptContextPills({
  contextPill,
  quickActions = []
}: { contextPill?: ContextPillData; quickActions?: QuickAction[] }) {
  if (!contextPill && quickActions.length === 0) return null

  return (
    <div className="p-4 pb-0 border-b border-b-lia-border-subtle">
      {contextPill && (
        <div className="mb-3">
          <ContextPill
            icon={contextPill.icon}
            primaryText={contextPill.primaryText}
            secondaryText={contextPill.secondaryText}
            onDismiss={contextPill.onDismiss}
          />
        </div>
      )}

      {quickActions.length > 0 && (
        <div>
          <div className="text-xs mb-2 lia-body">
            Ações rápidas:
          </div>
          <QuickActionChips actions={quickActions} />
        </div>
      )}
    </div>
  )
}
