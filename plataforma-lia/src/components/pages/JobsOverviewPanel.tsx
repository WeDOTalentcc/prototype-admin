"use client"

import React from "react"
import { Plus, Briefcase, Building2, BarChart3, Search } from "lucide-react"
import { LiaPromptHeader } from "@/components/ui/lia-prompt-header"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { AudioRecordButton } from "@/components/ui/audio-record-button"

interface JobsOverviewPanelProps {
  liaPromptValue: string
  setLiaPromptValue: any
  setActiveFilter: (filter: string) => void
  openJobCreationChat: (msg?: string) => void
  openGeneralChat: (msg?: string) => void
  orchestratorSuggestions: string[]
  getContextualSuggestions: () => string[]
}

export function JobsOverviewPanel({
  liaPromptValue,
  setLiaPromptValue,
  setActiveFilter,
  openJobCreationChat,
  openGeneralChat,
  orchestratorSuggestions,
  getContextualSuggestions,
}: JobsOverviewPanelProps) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center py-8">
      <div className="w-full max-w-[780px] mx-auto px-4 flex flex-col">
        <LiaPromptHeader title="Posso te ajudar com análises de vagas?" />
        <div className="rounded-xl overflow-hidden bg-lia-bg-primary border border-lia-border-subtle">
          <div className="px-4 pt-4 pb-4 border-b border-b-lia-border-subtle">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => {
                  setActiveFilter('todas')
                  setTimeout(() => openJobCreationChat('Criar nova vaga'), 100)
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary font-open-sans"
              >
                <Plus className="w-3 h-3" />
                Criar nova vaga
              </button>
              <button
                onClick={() => setActiveFilter('ativas')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary font-open-sans"
              >
                <Briefcase className="w-3 h-3" />
                Ver minhas vagas
              </button>
              <button
                onClick={() => setActiveFilter('todas')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary font-open-sans"
              >
                <Building2 className="w-3 h-3" />
                Ver todas as vagas
              </button>
              <button
                onClick={() => {
                  setActiveFilter('todas')
                  setTimeout(() => openGeneralChat('Resumo das minhas vagas ativas'), 100)
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary font-open-sans"
              >
                <BarChart3 className="w-3 h-3" />
                Resumo das vagas
              </button>
              <LiaVacancyQueriesGuide
                onSelectQuery={(query) => {
                  setActiveFilter('todas')
                  setTimeout(() => openGeneralChat(query), 100)
                }}
              />
            </div>
          </div>

          <div className="px-4 pt-4 pb-4">
            <div className="flex items-center gap-3 px-4 py-3 bg-lia-bg-primary rounded-md border border-lia-border-subtle transition-colors motion-reduce:transition-none focus-within:border-lia-border-medium focus-within:ring-1 focus-within:ring-lia-btn-primary-bg/20">
              <input
                type="text"
                placeholder="Como posso te ajudar com suas vagas hoje?"
                value={liaPromptValue}
                onChange={(e) => setLiaPromptValue(e.target.value)}
                className="flex-1 bg-transparent placeholder-lia-text-tertiary text-sm focus:outline-none text-lia-text-primary"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && liaPromptValue.trim()) {
                    setActiveFilter('todas')
                    setTimeout(() => {
                      openGeneralChat(liaPromptValue.trim())
                      setLiaPromptValue('')
                    }, 100)
                  }
                }}
              />
              <div className="flex items-center gap-1">
                <AudioRecordButton
                  onTranscription={(text: string) => setLiaPromptValue((prev: string) => prev ? `${prev} ${text}` : text) as any}
                  className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                />
              </div>
              <button
                className="flex items-center justify-center hover:opacity-70 transition-opacity motion-reduce:transition-none"
                onClick={() => {
                  if (liaPromptValue.trim()) {
                    setActiveFilter('todas')
                    setTimeout(() => {
                      openGeneralChat(liaPromptValue.trim())
                      setLiaPromptValue('')
                    }, 100)
                  } else {
                    setActiveFilter('todas')
                    setTimeout(() => openGeneralChat(), 100)
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
                    setActiveFilter('todas')
                    setTimeout(() => openGeneralChat(suggestion), 100)
                  }}
                  className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-lg transition-colors motion-reduce:transition-none bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle hover:text-lia-text-primary hover:bg-lia-bg-tertiary"
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
