"use client"

import React from"react"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import { LIAIcon } from"@/components/ui/lia-icon"
import { Chip } from "@/components/ui/chip"
import { Users } from"lucide-react"
import type { QuickAction } from"@/components/ui/quick-action-chips"

interface ContextPillData {
  icon: React.ReactNode
  primaryText: string
  secondaryText: string
  onDismiss?: () => void
}

interface JobContext {
  id?: string
  title?: string
  status?: string
}

interface ExpandableAIPromptProps {
  selectedCandidates: Record<string, unknown>[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: Record<string, unknown>
  onClose?: () => void
  contextPill?: ContextPillData
  quickActions?: QuickAction[]
  jobContext?: JobContext
  pageContext?: 'candidates' | 'jobs'
}

import { useExpandableAIPromptCore } from './expandable-ai-prompt/useExpandableAIPromptCore'
import { EAPInputBar } from './expandable-ai-prompt/EAPInputBar'
import { EAPExpandedSection } from './expandable-ai-prompt/EAPExpandedSection'
import { EAPTabContent } from './expandable-ai-prompt/EAPTabContent'
import { EAPModals } from './expandable-ai-prompt/EAPModals'

export function ExpandableAIPrompt(props: ExpandableAIPromptProps) {
  const core = useExpandableAIPromptCore(props as Parameters<typeof useExpandableAIPromptCore>[0])
  const {
    candidateContext, selectedCandidates, statusInfo,
    isExpanded, isProcessing, isListening,
    inputValue, setInputValue, setIsExpanded,
    handleSubmit, getPlaceholder, handleFileAnalyzed, handleAudioTranscription,
    searchSource, setSearchSource, handleSourceChange, showGlobalSearchOptions,
    requireEmails, setRequireEmails, requirePhoneNumbers, setRequirePhoneNumbers,
    jobContext, pageContext, onClose, onCommand,
    contextPill, quickActions, creditEstimate, pearchSearchType, candidateLimit,
    filledTagsCount, activeSearchTab, setActiveSearchTab,
    suggestions, commandHistory, showHistory, setShowHistory,
    handleHistoryCommand, handleSuggestionClick, lastCommand,
    suggestionQueue, templateSuggestions,
    showAdvancedFiltersModal, setShowAdvancedFiltersModal,
    advancedFilters, setAdvancedFilters,
    editingArchetype, closeEditArchetype,
    editArchetypeEmoji, setEditArchetypeEmoji,
    editArchetypeName, setEditArchetypeName,
    editArchetypeQuery, setEditArchetypeQuery,
    editArchetypeDescription, setEditArchetypeDescription,
    editArchetypeTags, setEditArchetypeTags,
    newTagInput, setNewTagInput,
    saveArchetype, isSavingArchetype,
    showDeleteArchetypeDialog, setShowDeleteArchetypeDialog,
    archetypeToDelete, setArchetypeToDelete,
    confirmDeleteArchetype,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    confirmSourceChange,
    showSaveArchetypeModal, setShowSaveArchetypeModal,
    buildSearchSpecFromEntities, naturalSearchValue, handleArchetypeSaved,
    searchTags,
  } = core

  return (
    <div className="space-y-3">

      {candidateContext && (
        <div className="bg-wedo-green-light/5 rounded-xl p-3 border border-wedo-green-light/20">
          <div className="flex items-center gap-2 mb-2">
            <LIAIcon size="sm" />
            <span className="text-base-ui font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              Análise LIA para candidato específico
            </span>
          </div>
          <div className="flex items-center gap-3 bg-lia-bg-primary rounded-xl px-3 py-2 border border-lia-border-subtle">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-wedo-green-light/10 text-lia-text-muted-light text-sm">
                {(candidateContext.name as string)?.split(' ').map((n: string) => n[0]).join('') || 'C'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-medium text-lia-text-primary text-base-ui">
                {(candidateContext.name as React.ReactNode)}
              </div>
              <div className="text-xs text-lia-text-primary">
                {candidateContext.position} • Score: {(candidateContext as any).liaAnalysis?.score || candidateContext.score}%
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
            <span className="text-base-ui font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {selectedCandidates.length} candidato{selectedCandidates.length > 1 ? 's' : ''} selecionado{selectedCandidates.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCandidates.slice(0, 3).map((candidate, index) => (
              <div key={(candidate as Record<string, unknown>).name as string || index} className="flex items-center gap-1 bg-lia-bg-primary rounded-md px-2 py-1 border border-lia-border-subtle">
                <Avatar className="w-4 h-4">
                  <AvatarFallback className="bg-lia-interactive-active text-lia-text-secondary text-xs">
                    {(candidate.name as string)?.charAt(0) || 'C'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
                  {((candidate.name || `Candidato ${index + 1}`) as React.ReactNode)}
                </span>
              </div>
            ))}
            {selectedCandidates.length > 3 && (
              <div className="px-2 py-1 bg-lia-bg-tertiary rounded-full text-xs text-lia-text-primary">
                +{selectedCandidates.length - 3} mais
              </div>
            )}
          </div>
        </div>
      )}

      <div className={`transition-colors motion-reduce:transition-none duration-300 ${statusInfo.bgColor} rounded-md border ${statusInfo.bgColor.includes('border') ? '' : 'border-lia-border-subtle'} overflow-hidden`}>

        <EAPInputBar
          inputValue={inputValue}
          setInputValue={setInputValue}
          isProcessing={isProcessing}
          isExpanded={isExpanded}
          setIsExpanded={setIsExpanded}
          handleSubmit={handleSubmit}
          getPlaceholder={getPlaceholder}
          handleFileAnalyzed={handleFileAnalyzed}
          handleAudioTranscription={handleAudioTranscription}
          searchSource={searchSource}
          setSearchSource={setSearchSource}
          handleSourceChange={handleSourceChange}
          showGlobalSearchOptions={showGlobalSearchOptions}
          requireEmails={requireEmails}
          setRequireEmails={setRequireEmails}
          requirePhoneNumbers={requirePhoneNumbers}
          setRequirePhoneNumbers={setRequirePhoneNumbers}
          statusInfo={statusInfo}
          jobContext={jobContext}
          pageContext={pageContext}
          selectedCandidates={selectedCandidates}
          onClose={onClose}
          candidateContext={candidateContext}
        />

        {isExpanded && (
          <EAPExpandedSection
            contextPill={contextPill}
            quickActions={quickActions as Array<{ id: string; label: string; icon?: React.ReactNode; action?: string }>}
            searchSource={searchSource}
            setSearchSource={setSearchSource}
            handleSourceChange={handleSourceChange}
            creditEstimate={creditEstimate}
            pearchSearchType={pearchSearchType}
            candidateLimit={candidateLimit}
            filledTagsCount={filledTagsCount}
            activeSearchTab={activeSearchTab}
            setActiveSearchTab={(v: string) => setActiveSearchTab(v as Parameters<typeof setActiveSearchTab>[0])}
            suggestions={suggestions}
            commandHistory={commandHistory}
            showHistory={showHistory}
            setShowHistory={setShowHistory}
            handleHistoryCommand={handleHistoryCommand}
            handleSuggestionClick={handleSuggestionClick}
            isProcessing={isProcessing}
            isListening={isListening}
            lastCommand={lastCommand}
            core={core}
          />
        )}
      </div>

      <EAPModals
        suggestionQueue={suggestionQueue}
        templateSuggestions={templateSuggestions}
        showAdvancedFiltersModal={showAdvancedFiltersModal}
        setShowAdvancedFiltersModal={setShowAdvancedFiltersModal}
        advancedFilters={advancedFilters}
        setAdvancedFilters={setAdvancedFilters}
        onCommand={onCommand}
        editingArchetype={editingArchetype}
        closeEditArchetype={closeEditArchetype}
        editArchetypeEmoji={editArchetypeEmoji}
        setEditArchetypeEmoji={setEditArchetypeEmoji}
        editArchetypeName={editArchetypeName}
        setEditArchetypeName={setEditArchetypeName}
        editArchetypeQuery={editArchetypeQuery}
        setEditArchetypeQuery={setEditArchetypeQuery}
        editArchetypeDescription={editArchetypeDescription}
        setEditArchetypeDescription={setEditArchetypeDescription}
        editArchetypeTags={editArchetypeTags}
        setEditArchetypeTags={setEditArchetypeTags}
        newTagInput={newTagInput}
        setNewTagInput={setNewTagInput}
        saveArchetype={saveArchetype}
        isSavingArchetype={isSavingArchetype}
        showDeleteArchetypeDialog={showDeleteArchetypeDialog}
        setShowDeleteArchetypeDialog={setShowDeleteArchetypeDialog}
        archetypeToDelete={archetypeToDelete}
        setArchetypeToDelete={setArchetypeToDelete}
        confirmDeleteArchetype={confirmDeleteArchetype}
        showSourceChangeModal={showSourceChangeModal}
        setShowSourceChangeModal={setShowSourceChangeModal}
        pendingSourceChange={pendingSourceChange}
        setPendingSourceChange={setPendingSourceChange as (v: string | null) => void}
        confirmSourceChange={confirmSourceChange}
        showSaveArchetypeModal={showSaveArchetypeModal}
        setShowSaveArchetypeModal={setShowSaveArchetypeModal}
        buildSearchSpecFromEntities={buildSearchSpecFromEntities as unknown as import('@/lib/api/candidate-search').SearchSpec}
        naturalSearchValue={naturalSearchValue}
        handleArchetypeSaved={handleArchetypeSaved as () => void}
      />
    </div>
  )
}
