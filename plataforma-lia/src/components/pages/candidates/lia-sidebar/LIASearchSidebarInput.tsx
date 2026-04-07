"use client"

import React from "react"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { LiaSearchQueriesGuide } from "@/components/ui/lia-search-queries-guide"
import {
  X, Target, Send, Star, FileText
} from "lucide-react"

type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

interface LIASearchSidebarInputProps {
  liaPromptValue: string
  setLiaPromptValue: React.Dispatch<React.SetStateAction<string>>
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (v: boolean) => void
  archetypeCreationStep: string
  setArchetypeCreationStep: (v: string) => void
  setNewArchetypeData: (v: { name: string; description: string; query: string; emoji: string }) => void
  setShowSaveAsArchetypeModal: (v: boolean) => void
  searchResults: { isLoading: boolean }
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  selectedCandidatesForBatch: Set<string>
  onLIAChatMessage: (message: string) => void
  onAICommand: (command: string) => void
}

export function LIASearchSidebarInput({
  liaPromptValue,
  setLiaPromptValue,
  isCreatingArchetype,
  setIsCreatingArchetype,
  archetypeCreationStep,
  setArchetypeCreationStep,
  setNewArchetypeData,
  setShowSaveAsArchetypeModal,
  searchResults,
  setChatMessages,
  selectedCandidatesForBatch,
  onLIAChatMessage,
  onAICommand,
}: LIASearchSidebarInputProps) {
  const handleSend = () => {
    if (!liaPromptValue.trim()) return

    if (isCreatingArchetype) {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: liaPromptValue.trim(),
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, userMessage])

      setTimeout(() => {
        const extractedName = liaPromptValue.length > 50
          ? liaPromptValue.substring(0, 50).split(' ').slice(0, 5).join(' ')
          : liaPromptValue.trim()

        const liaResponse: ChatMessage = {
          id: `lia-extraction-${Date.now()}`,
          type: 'lia',
          content: `✅ Analisei sua descrição e identifiquei os critérios principais.\n\n**Arquétipo sugerido:** ${extractedName}\n\nClique em "Salvar Arquétipo" abaixo para confirmar, ou continue descrevendo para refinar.`,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, liaResponse])

        setNewArchetypeData({
          name: extractedName,
          description: liaPromptValue.trim(),
          query: liaPromptValue.trim(),
          emoji: '🎯'
        })
        setArchetypeCreationStep('review')
        setShowSaveAsArchetypeModal(true)
      }, 1000)

      setLiaPromptValue('')
    } else {
      onLIAChatMessage(liaPromptValue.trim())
    }
  }

  return (
    <div className="flex-shrink-0 p-3 bg-lia-bg-primary rounded-md">
      {/* Banner de criação de arquétipo */}
      {isCreatingArchetype && (
        <div className="mb-2 p-2 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-lia-text-secondary" />
            <span className="text-xs font-medium text-lia-text-secondary">
              Criando novo arquétipo...
            </span>
          </div>
          <button
            onClick={() => {
              setIsCreatingArchetype(false)
              setArchetypeCreationStep('initial')
            }}
            className="p-1 hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md"
            aria-label="Cancelar criação de arquétipo"
          >
            <X className="w-3 h-3 text-lia-text-secondary" aria-hidden="true" />
          </button>
        </div>
      )}
      {/* Input Inline Padronizado - Design Specs v3.1 */}
      <div data-testid="lia-sidebar-input-area" className="flex items-center gap-2 p-2 rounded-md bg-lia-bg-primary border border-lia-border-subtle">
        <input
          type="text"
          placeholder={isCreatingArchetype
            ? "Cole a descrição da vaga ou descreva o perfil ideal..."
            : "Envie mensagem para a LIA..."
          }
          aria-label={isCreatingArchetype ? "Descrição do perfil ideal para arquétipo" : "Mensagem para a LIA"}
          value={liaPromptValue}
          onChange={(e) => setLiaPromptValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && liaPromptValue.trim()) {
              handleSend()
            }
          }}
          className="flex-1 text-xs bg-transparent focus:outline-none text-lia-text-primary"
        />
        <AudioRecordButton
          onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
          className="p-1.5"
        />
        <button
          data-testid="lia-sidebar-send-btn"
          type="button"
          onClick={handleSend}
          disabled={!liaPromptValue.trim() || searchResults.isLoading}
          className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none disabled:opacity-50 bg-lia-btn-primary-bg"
        >
          <Send className="w-3.5 h-3.5 text-white" />
        </button>
      </div>

      {/* Sugestões - abaixo do input conforme design specs */}
      <div className="flex items-center gap-1.5 mt-1.5">
        <span className="text-micro font-medium text-lia-text-tertiary">Sugestões:</span>
        <button
          onClick={() => onAICommand('Top 5 candidatos')}
          className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none dark:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse"
        >
          <Star className="w-2.5 h-2.5 text-lia-text-tertiary" />
          Top 5
        </button>
        <button
          onClick={() => onAICommand('Resumir esta busca')}
          className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none dark:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse"
        >
          <FileText className="w-2.5 h-2.5 text-lia-text-tertiary" />
          Resumir busca
        </button>
        <LiaSearchQueriesGuide
          onSelectQuery={(query) => onAICommand(query)}
          selectedCount={selectedCandidatesForBatch.size}
        />
      </div>
    </div>
  )
}
