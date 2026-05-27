"use client"

import React, { useState } from "react"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Send, ChevronDown, ChevronUp, X,
  Mail, Phone, Home, Zap, Globe,
} from "lucide-react"
import { PromptSuggestionsPopover } from "@/components/ui/prompt-suggestions-popover"
import { LiaQueriesGuide } from "@/components/ui/lia-queries-guide"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { FileUploadButton, type FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ContextBadge, PAGE_ROUTE_TO_CONTEXT_LABEL } from "@/components/lia-float/ContextBadge"

interface EAPInputBarProps {
  inputValue: string
  setInputValue: (v: string) => void
  isProcessing: boolean
  isExpanded: boolean
  setIsExpanded: (v: boolean) => void
  handleSubmit: (e: React.FormEvent) => void
  getPlaceholder: () => string
  handleFileAnalyzed: (file: File, analysis: FileAnalysisResult) => void
  handleAudioTranscription: (text: string) => void
  searchSource: string
  setSearchSource: (v: 'local' | 'global' | 'hybrid') => void
  handleSourceChange: (v: 'local' | 'hybrid' | 'global') => void
  showGlobalSearchOptions: boolean
  requireEmails: boolean
  setRequireEmails: (v: boolean) => void
  requirePhoneNumbers: boolean
  setRequirePhoneNumbers: (v: boolean) => void
  statusInfo: { color: string; text: string; bgColor: string }
  jobContext?: { id?: string; title?: string; status?: string }
  pageContext: string
  selectedCandidates: Record<string, unknown>[]
  onClose?: () => void
  candidateContext: Record<string, unknown> | null
  onContextDismiss?: () => void
}

export function EAPInputBar(props: EAPInputBarProps) {
  const {
    inputValue, setInputValue, isProcessing, isExpanded, setIsExpanded,
    handleSubmit, getPlaceholder, handleFileAnalyzed, handleAudioTranscription,
    searchSource, setSearchSource, handleSourceChange, showGlobalSearchOptions,
    requireEmails, setRequireEmails, requirePhoneNumbers, setRequirePhoneNumbers,
    statusInfo, jobContext, pageContext, selectedCandidates, onClose, candidateContext,
    onContextDismiss,
  } = props

  const [contextDismissed, setContextDismissed] = useState(false)
  const contextBadgeLabel = PAGE_ROUTE_TO_CONTEXT_LABEL[pageContext] ?? null

  return (
    <div className="p-3">
      <form onSubmit={handleSubmit} className="flex items-center gap-3">

        <LIAIcon
          size="lg"
          animate={isProcessing}
          className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 ${isProcessing ? 'scale-110' : ''}`}
        />

        {!contextDismissed && contextBadgeLabel && (
          <ContextBadge
            contextPage={contextBadgeLabel}
            onRemove={() => { setContextDismissed(true); onContextDismiss?.() }}
          />
        )}

        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={() => !isProcessing && setIsExpanded(true)}
          placeholder={isProcessing ? "IA processando..." : getPlaceholder()}
          disabled={isProcessing}
          className={`flex-1 bg-transparent text-lia-text-primary placeholder-lia-text-tertiary text-xs focus:outline-none ${
isProcessing ? 'opacity-60 cursor-not-allowed' : ''
          }`}
        />

        <div className="flex items-center gap-0.5 mr-1.5">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                  className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
searchSource === 'local' 
                      ? 'bg-lia-interactive-active' 
                      : 'hover:bg-lia-bg-tertiary'
                  }`}
                >
                  <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-lia-text-secondary' : 'text-lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs">Base Local (Gratuito)</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          {showGlobalSearchOptions && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleSourceChange('hybrid'); }}
                    className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
searchSource === 'hybrid' 
                        ? 'bg-lia-interactive-active' 
                        : 'hover:bg-lia-bg-tertiary'
                    }`}
                  >
                    <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-lia-text-secondary' : 'text-lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs">Local + Global (1 créd/cand)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          {showGlobalSearchOptions && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleSourceChange('global'); }}
                    className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
searchSource === 'global' 
                        ? 'bg-lia-interactive-active' 
                        : 'hover:bg-lia-bg-tertiary'
                    }`}
                  >
                    <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-lia-text-secondary' : 'text-lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs">Busca Global (1 créd/cand)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          <div className="w-px h-4 bg-lia-interactive-active mx-1" />
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                  className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
requireEmails 
                      ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                      : 'hover:bg-lia-bg-tertiary'
                  }`}
                >
                  <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Apenas com Email</p>
                <p className="text-micro text-lia-text-secondary">{requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                  className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
requirePhoneNumbers 
                      ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                      : 'hover:bg-lia-bg-tertiary'
                  }`}
                >
                  <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Apenas com Telefone</p>
                <p className="text-micro text-lia-text-secondary">{requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className={`text-xs ${statusInfo.color} flex items-center gap-1`}>
          <span>●</span>
          {statusInfo.text}
        </div>

        <div className="flex items-center gap-0.5">
          <PromptSuggestionsPopover
            onSelect={(command) => {
              setInputValue(command)
              setIsExpanded(true)
            }}
            context={{
              hasJob: !!jobContext?.id,
              jobTitle: jobContext?.title,
              selectedCandidatesCount: selectedCandidates.length,
              currentPage: pageContext
            }}
          />
          
          {pageContext === 'candidates' ? (
            <CandidateQueriesGuide
              onSelectQuery={(query) => {
                setInputValue(query)
                setIsExpanded(true)
              }}
            />
          ) : (
            <LiaQueriesGuide
              onSelectQuery={(query) => {
                setInputValue(query)
                setIsExpanded(true)
              }}
            />
          )}
        </div>

        <FileUploadButton
          onFilesSelected={() => {}}
          onFileAnalyzed={handleFileAnalyzed}
          maxFiles={2}
          acceptedTypes=".pdf,.doc,.docx,.txt"
          showPreview={false}
          autoAnalyze={true}
        />

        <AudioRecordButton
          onTranscription={handleAudioTranscription}
          maxDuration={60}
        />

        {candidateContext && onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 lia-btn-secondary rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none bg-lia-btn-primary-hover text-white" 
            title="Fechar análise do candidato"
          >
            <X className="w-4 h-4" />
          </button>
        ) : (
          <button
            type={inputValue.trim() ? "submit" : "button"}
            onClick={inputValue.trim() ? undefined : () => setIsExpanded(!isExpanded)}
            className="w-8 h-8 lia-btn-primary flex items-center justify-center"
          >
            {inputValue.trim() ? <Send className="w-4 h-4" /> :
             isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        )}
      </form>
    </div>
  )
}
