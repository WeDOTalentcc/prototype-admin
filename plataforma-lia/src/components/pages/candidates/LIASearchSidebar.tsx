"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Brain, X, Maximize2, PanelLeftClose } from "lucide-react"
import {
  LIASearchSidebarChat,
  LIASearchSidebarInput,
  TabJobDescription,
  TabSimilar,
  TabBoolean,
  TabFiltros,
  type ChatMessage,
  type SearchResults,
} from './lia-sidebar'

type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

interface LIASearchSidebarProps {
  isLiaSuperChat: boolean
  setIsLiaSuperChat: (v: boolean) => void
  liaWidth: number
  setLiaWidth: (v: number) => void
  isResizingLIA: boolean
  setIsResizingLIA: (v: boolean) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (tab: SearchTab) => void
  liaPromptValue: string
  setLiaPromptValue: React.Dispatch<React.SetStateAction<string>>
  chatMessages: ChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  searchResults: SearchResults
  setSearchResults: React.Dispatch<React.SetStateAction<SearchResults>>
  currentSearchSource: string
  searchSource: string
  pearchSearchOptions: { searchType: string }
  activeSearchFilters: Record<string, Record<string, unknown>>
  setActiveSearchFilters: (v: Record<string, Record<string, unknown>>) => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (v: boolean) => void
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (v: boolean) => void
  archetypeCreationStep: string
  setArchetypeCreationStep: (v: string) => void
  setNewArchetypeData: (v: { name: string; description: string; query: string; emoji: string }) => void
  setShowSaveAsArchetypeModal: (v: boolean) => void
  setShowGlobalExpansionConfirm: (v: boolean) => void
  selectedCandidatesForBatch: Set<string>
  setCandidates: (v: unknown[]) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  onLIAChatMessage: (message: string) => void
  onAICommand: (command: string) => void
  onQuickAction: (actionId: string, actionType: string) => void
  onCalibrationLike: (candidateId: string) => void
  onCalibrationDislike: (candidateId: string, reason?: string) => void
  onClose: () => void
  chatScrollRef: React.RefObject<HTMLDivElement>
}

export function LIASearchSidebar({
  isLiaSuperChat, setIsLiaSuperChat, liaWidth, setLiaWidth,
  isResizingLIA, setIsResizingLIA, activeSearchTab,
  liaPromptValue, setLiaPromptValue, chatMessages, setChatMessages,
  searchResults, setSearchResults, currentSearchSource, searchSource,
  pearchSearchOptions, activeSearchFilters, setActiveSearchFilters,
  showTableFiltersPanel, setShowTableFiltersPanel,
  isCreatingArchetype, setIsCreatingArchetype,
  archetypeCreationStep, setArchetypeCreationStep,
  setNewArchetypeData, setShowSaveAsArchetypeModal, setShowGlobalExpansionConfirm,
  selectedCandidatesForBatch, setCandidates, setHasSearchResults,
  setSearchResultsCount, setLocalResultsCount, setPearchResultsCount,
  setShowSearchResults, setDisplayedResultsCount,
  onLIAChatMessage, onAICommand, onQuickAction,
  onCalibrationLike, onCalibrationDislike, onClose, chatScrollRef,
}: LIASearchSidebarProps) {
  const [superChatWidth, setSuperChatWidth] = useState(600)

  const sharedSearchProps = {
    searchSource, pearchSearchOptions, setChatMessages, setSearchResults,
    setCandidates, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount, setShowSearchResults, setDisplayedResultsCount,
  }

  return (
    <div
      className={`transition-colors motion-reduce:transition-none duration-300 relative group ${isLiaSuperChat ? 'flex-1 z-10' : 'flex-shrink-0'}`}
      style={{width: isLiaSuperChat ? 'auto' : `${liaWidth}px`, maxWidth: isLiaSuperChat ? 'none' : `${liaWidth}px`}}
    >
      <Card className="h-full flex flex-col overflow-hidden border border-lia-border-default bg-white dark:bg-lia-bg-secondary">
        {/* Header */}
        <div className="flex-shrink-0 px-4 py-3 bg-white dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 bg-gray-50 dark:bg-lia-bg-primary">
                <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold leading-tight truncate text-lia-text-primary dark:text-lia-text-primary">Ol&aacute;! Sou a Lia.</h3>
                <p className="text-xs leading-tight truncate mt-0.5 text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                  Posso criar vagas, buscar candidatos, analisar m&eacute;tricas e muito mais!
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost" size="sm"
                      onClick={() => { isLiaSuperChat ? setIsLiaSuperChat(false) : (setIsLiaSuperChat(true), setSuperChatWidth(Math.max(superChatWidth, 600))) }}
                      className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex-shrink-0"
                    >
                      {isLiaSuperChat ? <PanelLeftClose className="w-4 h-4 text-lia-text-secondary" /> : <Maximize2 className="w-4 h-4 text-lia-text-tertiary" />}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent><p className="text-xs">{isLiaSuperChat ? 'Retrair chat' : 'Expandir para Superchat'}</p></TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex-shrink-0">
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 flex flex-col overflow-hidden mx-3 mb-3">
          {activeSearchTab === 'ia-natural' && (
            <div className="flex flex-col flex-1 min-h-0">
              <LIASearchSidebarChat
                chatScrollRef={chatScrollRef} searchResults={searchResults} setSearchResults={setSearchResults}
                currentSearchSource={currentSearchSource} chatMessages={chatMessages}
                setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
                setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
                onQuickAction={onQuickAction} onCalibrationLike={onCalibrationLike} onCalibrationDislike={onCalibrationDislike}
              />
              <LIASearchSidebarInput
                liaPromptValue={liaPromptValue} setLiaPromptValue={setLiaPromptValue}
                isCreatingArchetype={isCreatingArchetype} setIsCreatingArchetype={setIsCreatingArchetype}
                archetypeCreationStep={archetypeCreationStep} setArchetypeCreationStep={setArchetypeCreationStep}
                setNewArchetypeData={setNewArchetypeData} setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
                searchResults={searchResults} setChatMessages={setChatMessages}
                selectedCandidatesForBatch={selectedCandidatesForBatch}
                onLIAChatMessage={onLIAChatMessage} onAICommand={onAICommand}
              />
            </div>
          )}
          {activeSearchTab === 'job-description' && <TabJobDescription {...sharedSearchProps} />}
          {activeSearchTab === 'similar' && <TabSimilar {...sharedSearchProps} />}
          {activeSearchTab === 'boolean' && <TabBoolean />}
          {activeSearchTab === 'filtros' && (
            <TabFiltros
              activeSearchFilters={activeSearchFilters} setActiveSearchFilters={setActiveSearchFilters}
              showTableFiltersPanel={showTableFiltersPanel} setShowTableFiltersPanel={setShowTableFiltersPanel}
            />
          )}
        </div>
      </Card>

      {/* Resize Handle */}
      <div
        className={`absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 cursor-ew-resize hover:scale-125 transition-transform motion-reduce:transition-none z-10 flex items-center justify-center ${isLiaSuperChat ? 'h-full' : 'h-12'}`}
        title="Arraste para ajustar a largura"
        onMouseDown={(e) => {
          e.preventDefault()
          setIsResizingLIA(true)
          const startX = e.clientX
          const startWidth = isLiaSuperChat ? superChatWidth : liaWidth
          const handleMouseMove = (e: MouseEvent) => {
            const deltaX = e.clientX - startX
            if (isLiaSuperChat) {
              setSuperChatWidth(Math.max(500, Math.min(Math.floor(window.innerWidth * 0.8), startWidth + deltaX)))
            } else {
              setLiaWidth(Math.max(400, Math.min(800, startWidth + deltaX)))
            }
          }
          const handleMouseUp = () => {
            setIsResizingLIA(false)
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
          }
          document.addEventListener('mousemove', handleMouseMove)
          document.addEventListener('mouseup', handleMouseUp)
        }}
      >
        <div className={`w-1 rounded-full transition-colors motion-reduce:transition-none ${isLiaSuperChat ? 'h-24 bg-gray-900' : 'h-8 dark:bg-lia-bg-elevated hover:dark:hover:bg-gray-800'}`} />
      </div>
    </div>
  )
}
