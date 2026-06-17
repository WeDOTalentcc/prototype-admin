"use client"

import React from "react"
import { Search, Plus, Briefcase, Building2, BarChart3 } from "lucide-react"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { LiaPromptHeader } from "@/components/ui/lia-prompt-header"

interface JobsDashboardViewProps {
  liaPromptValue: string
  onSetLiaPromptValue: (value: string) => void
  onSetActiveFilter: (filter: string) => void
  onOpenGeneralChat: (msg?: string) => void
  onOpenJobCreationChat: (msg?: string) => void
  orchestratorSuggestions: string[]
  getContextualSuggestions: () => string[]
}

export function JobsDashboardView({
  liaPromptValue,
  onSetLiaPromptValue,
  onSetActiveFilter,
  onOpenGeneralChat,
  onOpenJobCreationChat,
  orchestratorSuggestions,
  getContextualSuggestions,
}: JobsDashboardViewProps) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center py-8">
      <div className="w-full max-w-[780px] mx-auto px-4 flex flex-col">
        <LiaPromptHeader title="Posso te ajudar com análises de vagas?" />
        <div className="rounded-xl overflow-hidden bg-lia-bg-primary border border-lia-border-subtle">
          <div className="px-4 py-3 bg-[var(--lia-bg-primary)]">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => {
                  onSetActiveFilter('todas')
                  setTimeout(() => onOpenJobCreationChat('Criar nova vaga'), 100)
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
              >
                <Plus className="w-3 h-3" />
                Criar nova vaga
              </button>
              <button
                onClick={() => onSetActiveFilter('ativas')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
              >
                <Briefcase className="w-3 h-3" />
                Ver minhas vagas
              </button>
              <button
                onClick={() => onSetActiveFilter('todas')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
              >
                <Building2 className="w-3 h-3" />
                Ver todas as vagas
              </button>
              <button
                onClick={() => {
                  onSetActiveFilter('todas')
                  setTimeout(() => onOpenGeneralChat('Resumo das minhas vagas ativas'), 100)
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
              >
                <BarChart3 className="w-3 h-3" />
                Resumo das vagas
              </button>
              <LiaVacancyQueriesGuide
                onSelectQuery={(query) => {
                  onSetActiveFilter('todas')
                  setTimeout(() => onOpenGeneralChat(query), 100)
                }}
              />
            </div>
          </div>

          <div className="px-4 pt-4 pb-4">
            <div className="flex items-center gap-3 px-4 py-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle transition-colors motion-reduce:transition-none focus-within:border-lia-border-medium focus-within:ring-1 focus-within:ring-lia-btn-primary-bg/20">
              <input
                type="text"
                placeholder="Como posso te ajudar com suas vagas hoje?"
                value={liaPromptValue}
                onChange={(e) => onSetLiaPromptValue(e.target.value)}
               
                className="flex-1 bg-transparent placeholder-lia-text-tertiary text-sm focus:outline-none text-lia-text-primary"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && liaPromptValue.trim()) {
                    onSetActiveFilter('todas')
                    setTimeout(() => {
                      onOpenGeneralChat(liaPromptValue.trim())
                      onSetLiaPromptValue('')
                    }, 100)
                  }
                }}
              />
              
              <div className="flex items-center gap-1">
                <AudioRecordButton
                  onTranscription={(text) => onSetLiaPromptValue(liaPromptValue ? `${liaPromptValue} ${text}` : text)}
                  className="w-7 h-7 rounded-xl flex items-center justify-center hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                />
              </div>
              
              <button
                className="flex items-center justify-center hover:opacity-70 transition-opacity motion-reduce:transition-none"
                onClick={() => {
                  if (liaPromptValue.trim()) {
                    onSetActiveFilter('todas')
                    setTimeout(() => {
                      onOpenGeneralChat(liaPromptValue.trim())
                      onSetLiaPromptValue('')
                    }, 100)
                  } else {
                    onSetActiveFilter('todas')
                    setTimeout(() => onOpenGeneralChat(), 100)
                  }
                }}
                title="Buscar"
              >
                <Search className="w-4 h-4 text-lia-text-secondary" />
              </button>
            </div>
          </div>

          <div className="px-4 pb-4">
            <div className="flex flex-wrap items-start gap-2 pt-3">
              <span className="text-xs text-lia-text-primary font-medium mt-0.5">Sugestões:</span>
              {(orchestratorSuggestions.length > 0 ? orchestratorSuggestions : getContextualSuggestions()).slice(0, 4).map((suggestion, index) => (
                <button
                  key={`suggestion-${index}`}
                  onClick={() => {
                    onSetActiveFilter('todas')
                    setTimeout(() => onOpenGeneralChat(suggestion), 100)
                  }}
                  className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-lg transition-colors bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle hover:text-lia-text-primary hover:bg-lia-bg-tertiary"
                 
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
