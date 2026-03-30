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
          <div className="px-4 pt-4 pb-4 border-b border-b-gray-200">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => {
                  onSetActiveFilter('todas')
                  setTimeout(() => onOpenJobCreationChat('Criar nova vaga'), 100)
                }}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
              >
                <Plus className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                Criar nova vaga
              </button>
              <button
                onClick={() => onSetActiveFilter('ativas')}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
              >
                <Briefcase className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                Ver minhas vagas
              </button>
              <button
                onClick={() => onSetActiveFilter('todas')}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
              >
                <Building2 className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                Ver todas as vagas
              </button>
              <button
                onClick={() => {
                  onSetActiveFilter('todas')
                  setTimeout(() => onOpenGeneralChat('Resumo das minhas vagas ativas'), 100)
                }}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
              >
                <BarChart3 className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
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
            <div className="flex items-center gap-3 px-4 py-3 bg-lia-bg-primary rounded-md border border-lia-border-subtle transition-colors focus-within:border-gray-400 focus-within:ring-1 focus-within:ring-gray-900/20">
              <input
                type="text"
                placeholder="Como posso te ajudar com suas vagas hoje?"
                value={liaPromptValue}
                onChange={(e) => onSetLiaPromptValue(e.target.value)}
               
                className="flex-1 bg-transparent placeholder-gray-400 text-sm focus:outline-none text-gray-950 dark:text-gray-50"
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
                  className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors"
                />
              </div>
              
              <button
                className="flex items-center justify-center hover:opacity-70 transition-opacity"
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
                <Search className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>

          <div className="px-4 pb-4">
            <div className="flex flex-wrap items-start gap-2 pt-3">
              <span className="text-xs text-gray-800 font-medium mt-0.5">Sugestões:</span>
              {(orchestratorSuggestions.length > 0 ? orchestratorSuggestions : getContextualSuggestions()).slice(0, 4).map((suggestion, index) => (
                <button
                  key={`suggestion-${index}`}
                  onClick={() => {
                    onSetActiveFilter('todas')
                    setTimeout(() => onOpenGeneralChat(suggestion), 100)
                  }}
                  className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-full transition-[width,height] bg-gray-50 text-gray-800 border border-lia-border-subtle hover:text-gray-900 hover:bg-gray-100"
                 
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
