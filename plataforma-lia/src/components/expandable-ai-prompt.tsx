"use client"

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useTemplateSuggestions } from "@/hooks/use-template-suggestions"
import { TemplateSuggestionToast, useTemplateSuggestionQueue } from "@/components/template-suggestion-toast"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LIAIcon } from "@/components/ui/lia-icon"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from "@/components/ui/quick-action-chips"
import { Card, CardContent } from "@/components/ui/card"
import { useCreditEstimator, formatCreditCost, getCostLevel, getCostColor, CREDIT_COSTS } from "@/hooks/useCreditEstimator"
import { AdvancedFiltersModal, type SearchFilters } from "@/components/search/advanced-filters-modal"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Brain, Mic, Send, ChevronDown, ChevronUp, X,
  Users, Mail, MessageSquare, Calendar, Target, Phone,
  Search, Filter, Star, Plus, Zap,
  FileText, Code, Check, Lightbulb, Globe, Home, Coins, AlertCircle,
  Briefcase, Linkedin, TrendingUp, AlertTriangle, Info, Wand2, 
  CheckCircle2, Upload, MapPin, Clock, Building2,
  Pencil, Trash2, Loader2, Table2
} from "lucide-react"
import { PromptSuggestionsPopover } from "@/components/ui/prompt-suggestions-popover"
import { LiaQueriesGuide } from "@/components/ui/lia-queries-guide"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { FileUploadButton, type FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { PremiumAutocomplete } from "@/components/ui/premium-autocomplete"
import { useToast } from "@/hooks/use-toast"
import { SaveArchetypeModal } from "@/components/search/save-archetype-modal"
import type { SearchSpec } from "@/lib/api/candidate-search"

interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

const ENTITY_LABELS: Record<string, string> = {
  job_title: 'Cargo',
  location: 'Localização',
  years_experience: 'Experiência',
  industry: 'Setor',
  skills: 'Habilidades',
  seniority: 'Senioridade',
  company: 'Empresa'
}

const CRITERIA_TYPE_MAP: Record<string, string> = {
  'Cargo': 'job_title',
  'Localização': 'location',
  'Experiência': 'years_experience',
  'Setor': 'industry',
  'Habilidades': 'skills',
  'Habilidade': 'skills',
  'Senioridade': 'seniority',
  'Empresa': 'company'
}

// Cores padronizadas por contexto - Paleta Pastel
const CONTEXT_COLORS: Record<string, {
  border: string
  bg: string
  headerText: string
  headerBg: string
}> = {
  candidates: {
    border: 'var(--wedo-green-light)',
    bg: 'var(--wedo-green-bg-10)',
    headerText: 'var(--status-success)',
    headerBg: 'var(--wedo-green-bg-15)'
  },
  jobs: {
    border: 'var(--gray-400)',
    bg: 'var(--gray-bg-05)',
    headerText: 'var(--gray-600)',
    headerBg: 'var(--gray-bg-10)'
  }
}

interface AutocompleteSuggestion {
  text: string
  category: string
  icon?: string
  description?: string
  insert_text?: string
}

interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: any
}

interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

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
  selectedCandidates: any[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: any
  onClose?: () => void
  // AI-First props
  contextPill?: ContextPillData
  quickActions?: QuickAction[]
  // Job context for suggestions
  jobContext?: JobContext
  // Page context for showing appropriate queries guide
  pageContext?: 'candidates' | 'jobs'
}

import { useExpandableAIPromptCore } from './expandable-ai-prompt/useExpandableAIPromptCore'

export function ExpandableAIPrompt(props: ExpandableAIPromptProps) {
  const {
    MAX_CV_FILES, MAX_SIMILAR_URLS, searchTags, suggestions, activeSearchTab, addSimilarUrl, advancedFilters, analyzeProfiles, archetypeSearchFilter, archetypeToDelete,
    archetypes, autocompleteEnabled, autocompleteSuggestions, booleanSearchValue, buildSearchSpecFromEntities, canSaveAsArchetype, candidateContext, candidateLimit,
    closeEditArchetype, combinedSuggestions, commandHistory, confirmDeleteArchetype, confirmSourceChange, contextPill, createArchetypeFromActiveSearch, createArchetypeFromDescription,
    creditEstimate, cvFileInputRef, editArchetypeDescription, editArchetypeEmoji, editArchetypeName, editArchetypeQuery, editArchetypeTags, editingArchetype,
    executeSearchWithCriteria, extractionTimeoutRef, fetchAutocomplete, filledTagsCount, filteredArchetypes, getPlaceholder, getTagColors, handleAcceptEnhancement,
    handleArchetypeSaved, handleAudioTranscription, handleAutocompleteKeyDown, handleCvUpload, handleDismissEnhancement, handleFileAnalyzed, handleHistoryCommand, handlePremiumAutocompleteSelect,
    handleSourceChange, handleSubmit, handleSuggestionClick, hasMultipleSources, hasParsedEntities, inputValue, isAnalyzingProfiles, isCreatingArchetype,
    isCreatingFromSearch, isDeletingArchetype, isEnhancingPrompt, isExpanded, isListening, isParsingEntities, isProcessing, isSavingArchetype,
    jobContext, jobDescriptionText, lastCommand, naturalSearchValue, newArchetypeDescription, newTagInput, onClose, onCommand,
    openDeleteArchetypeDialog, openEditArchetype, pageContext, parseEntitiesFromQuery, parsedEntities, pearchSearchType, pendingSourceChange, promptEnhancement,
    quickActions, removeCvFile, removeSimilarUrl, removeSuggestion, requireEmails, requirePhoneNumbers, saveArchetype, searchAnalysis,
    searchSource, selectedAutocompleteIndex, selectedCandidates, setActiveSearchTab, setAdvancedFilters, setArchetypeSearchFilter, setArchetypeToDelete, setAutocompleteEnabled,
    setBooleanSearchValue, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeTags, setInputValue, setIsExpanded,
    setJobDescriptionText, setNaturalSearchValue, setNewArchetypeDescription, setNewTagInput, setPendingSourceChange, setRequireEmails, setRequirePhoneNumbers, setSearchSource,
    setSelectedArquetipo, setShowAdvancedFiltersModal, setShowAutocomplete, setShowDeleteArchetypeDialog, setShowHistory, setShowPremiumAutocomplete, setShowSaveArchetypeModal, setShowSourceChangeModal,
    showAdvancedFiltersModal, showAutocomplete, showCombinedSuggestions, showDeleteArchetypeDialog, showGlobalSearchOptions, showHistory, showPremiumAutocomplete, showSaveArchetypeModal,
    showSourceChangeModal, similarCvFiles, similarUrls, statusInfo, suggestionQueue, templateSuggestions, updateSimilarUrl,
  } = useExpandableAIPromptCore(props)

    return (
    <div className="space-y-3">

      {/* Candidato Específico Preview */}
      {candidateContext && (
        <div className="bg-wedo-green-light/5 rounded-md p-3 border border-wedo-green-light/20">
          <div className="flex items-center gap-2 mb-2">
            <LIAIcon size="sm" />
            <span className="text-base-ui font-semibold text-gray-800">
              Análise LIA para candidato específico
            </span>
          </div>
          <div className="flex items-center gap-3 bg-white rounded-md px-3 py-2 border border-gray-100">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-wedo-green-light/10 text-wedo-green-light text-sm">
                {candidateContext.name?.split(' ').map((n: string) => n[0]).join('') || 'C'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-medium text-gray-800 text-base-ui">
                {candidateContext.name}
              </div>
              <div className="text-xs text-gray-800 dark:text-gray-200">
                {candidateContext.position} • Score: {candidateContext.liaAnalysis?.score || candidateContext.score}%
              </div>
            </div>
            <Badge className="bg-wedo-green-light/10 text-wedo-green-light border-0 text-micro">
              Foco Individual
            </Badge>
          </div>
        </div>
      )}

      {/* Candidatos Selecionados Preview */}
      {!candidateContext && selectedCandidates.length > 0 && (
        <div className="bg-gray-50 rounded-md p-3 border border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-gray-600" />
            <span className="text-base-ui font-semibold text-gray-800">
              {selectedCandidates.length} candidato{selectedCandidates.length > 1 ? 's' : ''} selecionado{selectedCandidates.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCandidates.slice(0, 3).map((candidate, index) => (
              <div key={index} className="flex items-center gap-1 bg-white rounded-md px-2 py-1 border border-gray-100">
                <Avatar className="w-4 h-4">
                  <AvatarFallback className="bg-gray-200 text-gray-700 text-xs">
                    {candidate.name?.charAt(0) || 'C'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-xs text-gray-800 dark:text-gray-200">
                  {candidate.name || `Candidato ${index + 1}`}
                </span>
              </div>
            ))}
            {selectedCandidates.length > 3 && (
              <div className="px-2 py-1 bg-gray-100 rounded-full text-xs text-gray-800 dark:text-gray-200">
                +{selectedCandidates.length - 3} mais
              </div>
            )}
          </div>
        </div>
      )}

      {/* Prompt Principal */}
      <div className={`transition-all duration-300 ${statusInfo.bgColor} rounded-md border ${statusInfo.bgColor.includes('border') ? '' : 'border-gray-100'} overflow-hidden`}>

        {/* Campo de input compacto */}
        <div className="p-3">
          <form onSubmit={handleSubmit} className="flex items-center gap-3">

            {/* LIA Icon */}
            <LIAIcon
              size="lg"
              animate={isProcessing}
              className={`flex-shrink-0 transition-all duration-300 ${isProcessing ? 'scale-110' : ''}`}
            />

            {/* Input Field */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => !isProcessing && setIsExpanded(true)}
              placeholder={isProcessing ? "LIA processando..." : getPlaceholder()}
              disabled={isProcessing}
              className={`flex-1 bg-transparent text-gray-950 dark:text-gray-50 placeholder-gray-500 text-xs focus:outline-none ${
                isProcessing ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />

            {/* Seletor de Origem de Busca - Sempre Visível (Compacto) */}
            <div className="flex items-center gap-0.5 mr-1.5">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                      className={`p-1.5 rounded-md transition-all ${
                        searchSource === 'local' 
                          ? 'bg-gray-200' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-600'}`} />
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
                        className={`p-1.5 rounded-md transition-all ${
                          searchSource === 'hybrid' 
                            ? 'bg-gray-200' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-600'}`} />
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
                        className={`p-1.5 rounded-md transition-all ${
                          searchSource === 'global' 
                            ? 'bg-gray-200' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-600'}`} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs">Busca Global (1 créd/cand)</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              
              {/* Separador visual */}
              <div className="w-px h-4 bg-gray-200 mx-1" />
              
              {/* Toggle Email */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                      className={`p-1.5 rounded-md transition-all ${
                        requireEmails 
                          ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-micro text-gray-400">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              {/* Toggle Telefone */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                      className={`p-1.5 rounded-md transition-all ${
                        requirePhoneNumbers 
                          ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            {/* Status Info */}
            <div className={`text-xs ${statusInfo.color} flex items-center gap-1`}>
              <span>●</span>
              {statusInfo.text}
            </div>

            {/* Suggestions & Queries Guide Buttons */}
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

            {/* File Upload Button */}
            <FileUploadButton
              onFilesSelected={() => {}}
              onFileAnalyzed={handleFileAnalyzed}
              maxFiles={2}
              acceptedTypes=".pdf,.doc,.docx,.txt"
              showPreview={false}
              autoAnalyze={true}
            />

            {/* Audio Record Button */}
            <AudioRecordButton
              onTranscription={handleAudioTranscription}
              maxDuration={60}
            />

            {/* Close/Expand/Send Button */}
            {candidateContext && onClose ? (
              <button
                type="button"
                onClick={onClose}
                className="w-8 h-8 lia-btn-secondary rounded-md flex items-center justify-center transition-colors bg-gray-800 text-white" 
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

        {/* Área Expandida - REORGANIZADA SEM DUPLICAÇÃO */}
        {isExpanded && (
          <div className="lia-prompt-expanded space-y-4" style={{backgroundColor: 'var(--gray-100)'}}>

            {/* AI-First Context Pills + Quick Actions */}
            {(contextPill || quickActions.length > 0) && (
              <div className="p-4 pb-0 border-b border-b-gray-200">
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
            )}

            {/* 🧠 PESQUISA AVANÇADA - Sistema de 6 Abas */}
            <div className="p-4 pb-0">
              {/* Header com LIA Icon e Controles de Fonte/Créditos */}
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <LIAIcon size="sm" />
                  <span className="text-sm lia-heading">Pesquisa Avançada</span>
                </div>
                
                <div className="flex items-center gap-3">
                  {/* Seletor de Fonte de Busca */}
                  <div className="lia-tabs-container flex items-center gap-1">
                    <button
                      onClick={() => setSearchSource('local')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'local' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar apenas na base local (sem consumo de créditos)"
                    >
                      <Home className="w-3 h-3" />
                      <span className="hidden sm:inline">Local</span>
                    </button>
                    <button
                      onClick={() => handleSourceChange('hybrid')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'hybrid' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar na base local + Base Global (consome créditos para resultados externos)"
                    >
                      <Zap className="w-3 h-3" />
                      <span className="hidden sm:inline">Híbrido</span>
                    </button>
                    <button
                      onClick={() => handleSourceChange('global')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'global' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar apenas na Base Global (800M+ perfis, consome créditos)"
                    >
                      <Globe className="w-3 h-3" />
                      <span className="hidden sm:inline">Global</span>
                    </button>
                  </div>
                  
                  {/* Estimativa de Créditos em Tempo Real */}
                  <div className="relative group">
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs ${
                      creditEstimate.isLocal 
                        ? 'bg-status-success/10 text-status-success' 
                        : !creditEstimate.canAfford
                          ? 'bg-status-error/10 text-status-error'
                          : getCostLevel(creditEstimate.total) === 'low' 
                            ? 'bg-status-success/10 text-status-success'
                            : getCostLevel(creditEstimate.total) === 'medium'
                              ? 'bg-status-warning/10 text-status-warning'
                              : 'bg-status-error/10 text-status-error'
                    }`}>
                      <Coins className="w-3 h-3" />
                      <span className="font-medium">
                        {creditEstimate.isLoading ? (
                          '...'
                        ) : creditEstimate.isLocal ? (
                          'Gratuito'
                        ) : (
                          `~${creditEstimate.total} créditos`
                        )}
                      </span>
                      {!creditEstimate.isLocal && !creditEstimate.canAfford && (
                        <AlertCircle className="w-3 h-3 text-status-error" />
                      )}
                    </div>
                    
                    {/* Tooltip de Detalhes de Créditos */}
                    <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block z-50">
                      <div className="bg-gray-900 text-white px-3 py-2 rounded-md text-xs min-w-[220px]">
                        <div className="font-semibold mb-2 flex items-center gap-1.5">
                          <Coins className="w-3.5 h-3.5 text-status-warning" />
                          Estimativa de Custo
                        </div>
                        {creditEstimate.isLocal ? (
                          <div className="text-status-success">
                            Busca local gratuita - sem consumo de créditos
                          </div>
                        ) : (
                          <div className="space-y-1.5">
                            {/* Saldo disponível */}
                            {creditEstimate.availableCredits !== undefined && (
                              <div className="flex justify-between pb-1.5 border-b border-gray-700">
                                <span className="text-gray-300">Saldo disponível:</span>
                                <span className={`font-medium ${
                                  creditEstimate.canAfford ? 'text-status-success' : 'text-status-error'
                                }`}>
                                  {creditEstimate.availableCredits} créditos
                                </span>
                              </div>
                            )}
                            <div className="flex justify-between">
                              <span className="text-gray-300">Tipo de busca:</span>
                              <span className="font-medium">{pearchSearchType === 'fast' ? 'Rápida' : 'Profissional'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-300">Por candidato:</span>
                              <span className="font-medium">{creditEstimate.perCandidate} créditos</span>
                            </div>
                            <div className="flex justify-between pt-1.5 border-t border-gray-700">
                              <span className="text-gray-300">Total ({candidateLimit} cand.):</span>
                              <span className={`font-bold ${getCostColor(getCostLevel(creditEstimate.total))}`}>
                                {creditEstimate.total} créditos
                              </span>
                            </div>
                            {!creditEstimate.canAfford && (
                              <div className="text-xs text-status-error mt-1.5 pt-1.5 border-t border-gray-700 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                Saldo insuficiente para esta busca
                              </div>
                            )}
                          </div>
                        )}
                        <div className="absolute bottom-full right-4 border-4 border-transparent border-b-gray-900"></div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Contador de critérios */}
                  <span className="text-xs text-gray-600 hidden md:inline">
                    {filledTagsCount}/5 critérios
                  </span>
                </div>
              </div>
              
              {/* 6 Abas de Pesquisa */}
              <div className="flex items-center gap-1.5 mb-3 overflow-x-auto pb-1">
                <button
                  onClick={() => setActiveSearchTab('natural')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'natural'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  IA Natural
                </button>
                <button
                  onClick={() => setActiveSearchTab('similar')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'similar'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Users className="w-3 h-3" />
                  Similar
                </button>
                <button
                  onClick={() => setActiveSearchTab('job-description')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'job-description'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <FileText className="w-3 h-3" />
                  D. Cargo
                </button>
                <button
                  onClick={() => setActiveSearchTab('boolean')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'boolean'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Code className="w-3 h-3" />
                  Boleana
                </button>
                <button
                  onClick={() => setActiveSearchTab('filtros')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'filtros'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Filter className="w-3 h-3" />
                  Filtros
                </button>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href="/funil?expandedSearch=true"
                        className="ml-1 p-1.5 rounded-md hover:bg-gray-100 transition-all border border-gray-200"
                      >
                        <Table2 className="w-3.5 h-3.5 text-gray-500" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs font-medium">Abrir em Tabela</p>
                      <p className="text-micro text-gray-400">Ir para resultados de busca</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Conteúdo da Aba Ativa */}
              <div className="mb-3">
                {/* Aba: Quem você procura? (IA Natural) */}
                {activeSearchTab === 'natural' && (
                  <div>
                    <div className="relative">
                      <input
                        type="text"
                        value={naturalSearchValue}
                        onChange={(e) => {
                          const value = e.target.value
                          setNaturalSearchValue(value)
                          
                          if (value.length >= 2) {
                            setShowPremiumAutocomplete(true)
                          } else {
                            setShowPremiumAutocomplete(false)
                          }
                          
                          if (extractionTimeoutRef.current) {
                            clearTimeout(extractionTimeoutRef.current)
                          }
                          
                          extractionTimeoutRef.current = setTimeout(() => {
                            parseEntitiesFromQuery(value)
                            if (autocompleteEnabled) {
                              fetchAutocomplete(value)
                            }
                          }, 400)
                        }}
                        onKeyDown={handleAutocompleteKeyDown}
                        onFocus={() => {
                          if (naturalSearchValue.length >= 2) {
                            setShowPremiumAutocomplete(true)
                          }
                        }}
                        onBlur={() => setTimeout(() => {
                          setShowAutocomplete(false)
                          setShowPremiumAutocomplete(false)
                        }, 200)}
                        placeholder="Descreva o candidato ideal em linguagem natural..."
                        className="lia-input w-full px-4 py-2.5 text-sm pr-[180px]"
                      />
                      
                      {/* Ícones de Fonte e Contato dentro do input */}
                      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                        {/* Fonte de busca: Local / Híbrido / Global */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  searchSource === 'local' 
                                    ? 'bg-gray-200' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-500'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Base Local</p>
                              <p className="text-micro text-gray-400">Gratuito</p>
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
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'hybrid' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
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
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'global' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Base Global</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Contato: Email / Telefone */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requireEmails 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-micro text-gray-400">{requireEmails ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requirePhoneNumbers 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Botão de Buscar */}
                        <button 
                          className="w-7 h-7 lia-btn-primary flex items-center justify-center"
                          onClick={() => executeSearchWithCriteria()}
                        >
                          <Search className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      
                      {/* Autocomplete Dropdown */}
                      {showAutocomplete && autocompleteSuggestions.length > 0 && (
                        <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-100 rounded-md z-50 max-h-48 overflow-y-auto">
                          {autocompleteSuggestions.map((suggestion, index) => (
                            <button
                              key={index}
                              onClick={() => {
                                setNaturalSearchValue(prev => {
                                  const words = prev.split(' ')
                                  words.pop()
                                  const insertValue = suggestion.insert_text || suggestion.text
                                  return [...words, insertValue].join(' ') + ' '
                                })
                                setShowAutocomplete(false)
                              }}
                              className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between transition-colors ${
                                selectedAutocompleteIndex === index 
                                  ? 'bg-gray-100' 
                                  : 'hover:bg-gray-50'
                              }`}
                            >
                              <span style={{color: 'var(--gray-950)'}}>{suggestion.text}</span>
                              <span className="text-xs text-gray-400">{suggestion.category}</span>
                            </button>
                          ))}
                          <div className="px-3 py-1.5 text-xs flex items-center justify-between text-gray-400" style={{borderTop: '1px solid var(--overlay-05)'}}>
                            <span>Use ↑↓ para navegar, Tab para selecionar</span>
                            <span>Esc para fechar</span>
                          </div>
                        </div>
                      )}
                      
                      {/* Premium Autocomplete - Company-based suggestions */}
                      <PremiumAutocomplete
                        query={naturalSearchValue}
                        onSelect={handlePremiumAutocompleteSelect}
                        isOpen={showPremiumAutocomplete && naturalSearchValue.length >= 2 && !showAutocomplete}
                        onClose={() => setShowPremiumAutocomplete(false)}
                      />
                    </div>
                    
                    {/* Prompt Enhancement Card */}
                    {promptEnhancement && !showAutocomplete && (
                      <div 
                        className="mt-2 p-3 rounded-md border transition-all bg-gray-200/20" style={{ borderColor: 'var(--wedo-cyan-border)' }}
                      >
                        <div className="flex items-start gap-2">
                          <Wand2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="text-xs font-medium text-gray-700">Sugestão da LIA</span>
                              {isEnhancingPrompt && (
                                <div className="w-3 h-3 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" />
                              )}
                            </div>
                            <p className="text-sm text-gray-800 dark:text-gray-200 mb-2">{promptEnhancement.enhanced_query}</p>
                            {promptEnhancement.explanation && (
                              <p className="text-xs text-gray-500 mb-2">{promptEnhancement.explanation}</p>
                            )}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={handleAcceptEnhancement}
                                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors bg-gray-900 text-white" 
                              >
                                <Check className="w-3 h-3" />
                                Usar sugestão
                              </button>
                              <button
                                onClick={handleDismissEnhancement}
                                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                              >
                                <X className="w-3 h-3" />
                                Ignorar
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Indicador de Fonte de Busca */}
                    {searchSource === 'local' && (
                      <div className="flex items-center gap-1.5 mt-2 mb-1">
                        <div 
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                          style={{backgroundColor: 'var(--wedo-cyan-bg-08)', 
                            border: '1px solid var(--wedo-cyan-bg-20)'}}
                        >
                          <Home className="w-3 h-3" />
                          <span>Base Local</span>
                        </div>
                        <span className="text-xs text-gray-400">
                          Busca apenas na sua base de dados
                        </span>
                      </div>
                    )}
                    
                    {/* Tags de Critérios - Sempre Visíveis (5 critérios como SmartSearchInput) */}
                    <div className="flex flex-wrap items-center gap-1.5 mt-2">
                      {searchTags.map((tag) => {
                        const colors = getTagColors(tag.key, tag.filled)
                        const TagIcon = tag.icon
                        
                        return (
                          <div
                            key={tag.key}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-all"
                            style={{backgroundColor: colors.bg,
                              color: colors.text}}
                            title={tag.value}
                          >
                            <div 
                              className="flex items-center justify-center w-4 h-4 rounded-md"
                              style={{backgroundColor: tag.filled ? colors.iconBgLight : 'transparent'}}
                            >
                              <TagIcon className="w-3 h-3" style={{color: tag.filled ? colors.iconBg : colors.text}} />
                            </div>
                            <span className="font-medium">{tag.label}</span>
                            {tag.filled && tag.value && (
                              <>
                                <span style={{opacity: 0.5}}>·</span>
                                <span className="max-w-20 truncate font-normal" style={{opacity: 0.85}}>{tag.value}</span>
                              </>
                            )}
                          </div>
                        )
                      })}
                      
                      {isParsingEntities && (
                        <div className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-400">
                          <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                          Analisando...
                        </div>
                      )}
                      
                      {/* Botão Assistente de Busca - Consolidado com toggle */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() => setAutocompleteEnabled(!autocompleteEnabled)}
                              className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:opacity-90",
                                autocompleteEnabled 
                                  ? "bg-gray-900 text-white" 
                                  : "bg-gray-100 text-gray-500"
                              )}
                             
                            >
                              <Brain className={`w-3.5 h-3.5 ${autocompleteEnabled ? 'text-wedo-cyan' : 'text-gray-400'}`} />
                              <span className="font-medium text-xs">
                                Assistente de Busca
                              </span>
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="max-w-panel-sm p-3 max-w-panel-sm p-3 border-gray-300 dark:border-gray-600">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Brain className="w-4 h-4 text-wedo-cyan" />
                                  <span className="font-semibold text-sm" style={{color: autocompleteEnabled ? 'var(--status-success)' : 'var(--status-error)'}}>
                                    {autocompleteEnabled ? 'Ativado' : 'Desativado'}
                                  </span>
                                </div>
                                <span className="text-micro px-2 py-0.5 rounded-full" style={{backgroundColor: autocompleteEnabled ? 'var(--status-success-bg)' : 'var(--status-error-bg)',
                                  color: autocompleteEnabled ? 'var(--status-success)' : 'var(--status-error)'}}>
                                  {autocompleteEnabled ? 'ON' : 'OFF'}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium text-sm text-gray-800 dark:text-gray-100">
                                  Assistente de Busca Inteligente
                                </span>
                              </div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Enquanto você descreve o perfil, a LIA analisa e sugere melhorias:
                              </p>
                              <ul className="text-xs space-y-1 text-gray-500 dark:text-gray-400">
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Indica critérios faltantes</span>
                                </li>
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Sugere sinônimos e termos relacionados</span>
                                </li>
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Alerta sobre buscas muito amplas ou restritivas</span>
                                </li>
                              </ul>
                              <p className="text-micro pt-1 border-t text-gray-500 dark:text-gray-400 border-gray-300 dark:border-gray-600">
                                {autocompleteEnabled ? 'Clique para desativar' : 'Clique para ativar'}
                              </p>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      {/* Botão Salvar como Arquétipo */}
                      {canSaveAsArchetype && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => setShowSaveArchetypeModal(true)}
                                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all hover:opacity-90 bg-gray-200/30" style={{ border: '1px solid var(--wedo-cyan-border)' }}
                              >
                                <Target className="w-3 h-3" />
                                <span className="font-medium">Salvar Arquétipo</span>
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none !duration-0">
                              <p className="text-xs font-medium">Salvar busca como arquétipo</p>
                              <p className="text-xs text-gray-300">Reutilize esta busca no futuro</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                    
                    {/* Análise de Qualidade da Busca */}
                    {naturalSearchValue && searchAnalysis && (
                      <div className="space-y-2 pt-2 mt-2 border-t border-gray-300 dark:border-gray-600">
                        {/* Barra de completude */}
                        <div className="flex items-center gap-3">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                                Qualidade da busca
                              </span>
                              <span 
                                className="text-xs font-bold"
                                style={{color: searchAnalysis.completeness_score >= 60 
                                    ? 'var(--status-success)' 
                                    : searchAnalysis.completeness_score >= 40 
                                      ? 'var(--status-warning)' 
                                      : 'var(--status-error)'}}
                              >
                                {searchAnalysis.completeness_score}%
                              </span>
                            </div>
                            <div className="h-1.5 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800">
                              <div 
                                className="h-full rounded-full transition-all duration-500"
                                style={{width: `${searchAnalysis.completeness_score}%`,
                                  backgroundColor: searchAnalysis.completeness_score >= 60 
                                    ? 'var(--status-success)' 
                                    : searchAnalysis.completeness_score >= 40 
                                      ? 'var(--status-warning)' 
                                      : 'var(--status-error)'}}
                              />
                            </div>
                          </div>
                          {searchAnalysis.next_recommended_action && (
                            <div 
                              className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs bg-wedo-cyan/[0.08]"
                            >
                              <TrendingUp className="w-3 h-3" />
                              <span>{searchAnalysis.next_recommended_action}</span>
                            </div>
                          )}
                        </div>
                        
                        {/* Alertas inteligentes */}
                        {searchAnalysis.alerts.length > 0 && (
                          <div className="space-y-1.5">
                            {searchAnalysis.alerts.slice(0, 2).map((alert, index) => (
                              <div 
                                key={index}
                                className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs text-gray-500 dark:text-gray-400"
                                style={{backgroundColor: alert.severity === 'warning'
                                    ? 'var(--status-warning-bg-08)'
                                    : 'var(--wedo-cyan-bg-08)'}}
                              >
                                {alert.severity === 'warning' ? (
                                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
                                ) : (
                                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                                )}
                                <div className="flex-1 min-w-0">
                                  <span>{alert.message}</span>
                                  {alert.suggestion && (
                                    <button
                                      onClick={() => {
                                        if (alert.action_value) {
                                          setNaturalSearchValue(naturalSearchValue + ', ' + alert.action_value)
                                        }
                                      }}
                                      className="ml-1 font-medium hover:underline text-gray-700"
                                    >
                                      {alert.suggestion}
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Sugestões (cobrindo: Location, Job Title, Experience, Industry, Skills) */}
                    <div className="mt-3">
                      <p className="text-xs text-gray-800 mb-1.5">Sugestões:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {[
                          'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
                          'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis',
                          'Data Scientist Sênior híbrido, 4+ anos em e-commerce, Python e ML',
                          'Tech Lead em Campinas, 7+ anos em startups, React e liderança de times'
                        ].map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => {
                              setNaturalSearchValue(suggestion)
                              parseEntitiesFromQuery(suggestion)
                            }}
                            className="px-2.5 py-1.5 text-xs rounded-full border border-gray-100 bg-white text-gray-600 hover:border-gray-400 hover:text-gray-800 hover:transition-all text-left"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Similar - Pattern like SmartSearchInput */}
                {activeSearchTab === 'similar' && (
                  <div className="space-y-3">
                    {/* URL inputs - up to 2 URLs */}
                    {similarUrls.map((url, index) => (
                      <div key={index} className="relative">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2">
                          <Linkedin className="w-4 h-4 text-gray-600" />
                        </div>
                        <input
                          type="text"
                          value={url}
                          onChange={(e) => updateSimilarUrl(index, e.target.value)}
                          placeholder={index === 0 ? "Cole a URL do LinkedIn ou ID do candidato..." : "Cole outra URL para combinar perfis..."}
                          className="lia-input w-full pl-10 pr-20 py-2.5 text-sm"
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                          {index > 0 && (
                            <button
                              onClick={() => removeSimilarUrl(index)}
                              className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-status-error/10 transition-colors"
                            >
                              <X className="w-3.5 h-3.5 text-status-error" />
                            </button>
                          )}
                          {index === similarUrls.length - 1 && similarUrls.length < MAX_SIMILAR_URLS && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    onClick={addSimilarUrl}
                                    className="h-8 px-3 rounded-md text-sm font-bold hover:bg-gray-800 hover:text-white transition-colors text-gray-700 bg-gray-100"
                                  >
                                    + URL
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="text-xs max-w-sidebar-content">
                                  Adicione até 2 perfis para a LIA criar um perfil ideal combinado
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* CV Upload section with separator */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-200" />
                      <span className="text-xs text-gray-600 px-2">ou</span>
                      <div className="flex-1 h-px bg-gray-200" />
                    </div>

                    <div className="relative">
                      <input
                        ref={cvFileInputRef}
                        type="file"
                        accept=".pdf,.doc,.docx"
                        multiple
                        onChange={handleCvUpload}
                        className="hidden"
                      />
                      {similarCvFiles.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {similarCvFiles.map((file, index) => (
                            <div 
                              key={index}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs"
                              style={{backgroundColor: 'var(--gray-100)'}}
                            >
                              <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                              <span className="max-w-[150px] truncate">{file.name}</span>
                              <button onClick={() => removeCvFile(index)} className="hover:text-status-error">
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                          {similarCvFiles.length < MAX_CV_FILES && (
                            <button
                              onClick={() => cvFileInputRef.current?.click()}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium hover:bg-gray-100 transition-colors border border-gray-200"
                              style={{backgroundColor: 'var(--gray-100)'}}
                            >
                              <Upload className="w-3 h-3" />
                              + CV
                            </button>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => cvFileInputRef.current?.click()}
                          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-100 transition-colors border border-gray-200"
                          style={{backgroundColor: 'var(--gray-100)'}}
                        >
                          <Upload className="w-3.5 h-3.5" />
                          Arraste CVs aqui ou clique para upload (máx. 2)
                        </button>
                      )}
                    </div>

                    {/* Analyze button - Shows when 2+ sources */}
                    {hasMultipleSources() && !showCombinedSuggestions && (
                      <button
                        onClick={analyzeProfiles}
                        disabled={isAnalyzingProfiles}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-medium text-white disabled:opacity-50 bg-gray-900"
                      >
                        {isAnalyzingProfiles ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Analisando perfis...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-3.5 h-3.5" />
                            Analisar e combinar perfis com LIA
                          </>
                        )}
                      </button>
                    )}

                    {/* Combined Suggestions Box */}
                    {showCombinedSuggestions && combinedSuggestions.length > 0 && (
                      <div className="p-3 rounded-md space-y-2 border border-gray-200" style={{backgroundColor: "var(--gray-50)"}}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            <span className="text-xs font-medium text-gray-800">
                              Perfil Ideal sugerido pela LIA
                            </span>
                          </div>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="w-3.5 h-3.5 text-gray-600" />
                              </TooltipTrigger>
                              <TooltipContent side="top" className="text-xs max-w-[280px]">
                                A LIA analisou os perfis e combinou skills, experiências e senioridade em comum. Edite ou remova tags antes de buscar.
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {combinedSuggestions.map((keyword) => (
                            <div
                              key={keyword}
                              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium group border border-gray-200 bg-white"
                            >
                              <span className="text-gray-700">{keyword}</span>
                              <button
                                onClick={() => removeSuggestion(keyword)}
                                className="opacity-50 group-hover:opacity-100 hover:text-status-error transition-opacity"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          Baseado em {similarUrls.filter(u => u.trim()).length + similarCvFiles.length} perfis: skills em comum e pontos fortes combinados.
                        </p>
                      </div>
                    )}

                    {/* Search Button */}
                    <button
                      onClick={() => {
                        const validUrls = similarUrls.filter(u => u.trim())
                        if (validUrls.length > 0 || similarCvFiles.length > 0) {
                          const query = validUrls.join(', ')
                          onCommand(query, 'find_similar')
                        }
                      }}
                      disabled={similarUrls.filter(u => u.trim()).length === 0 && similarCvFiles.length === 0}
                      className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{backgroundColor: (similarUrls.filter(u => u.trim()).length > 0 || similarCvFiles.length > 0) ? "var(--gray-950)" : "var(--gray-200)",
                        color: (similarUrls.filter(u => u.trim()).length > 0 || similarCvFiles.length > 0) ? "var(--white)" : "var(--gray-400)"}}
                    >
                      <Search className="w-4 h-4" />
                      {hasMultipleSources() ? "Buscar com perfil combinado" : "Buscar candidatos similares"}
                    </button>

                    {/* Dica contextual padronizada */}
                    <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          <strong>Dica:</strong> Cole 1 a 2 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, a LIA combina as melhores características e sugere palavras-chave para encontrar candidatos similares.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Job Description */}
                {activeSearchTab === 'job-description' && (
                  <div className="space-y-3">
                    <p className="text-xs text-gray-800 dark:text-gray-200">Cole a descrição da vaga para extrair requisitos automaticamente</p>
                    <textarea
                      value={jobDescriptionText}
                      onChange={(e) => setJobDescriptionText(e.target.value)}
                      placeholder="Cole aqui a descrição completa da vaga..."
                      className="lia-input w-full px-4 py-2.5 text-sm resize-none"
                      rows={3}
                    />
                    <div className="flex justify-between items-center">
                      {/* Dica contextual */}
                      <div className="flex items-start gap-2 flex-1">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs lia-body">
                          <strong>Dica:</strong> Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.
                        </p>
                      </div>
                      <button 
                        className="ml-3 px-3 py-1.5 lia-btn-primary text-xs disabled:opacity-50"
                        onClick={() => jobDescriptionText.trim() && onCommand(jobDescriptionText, 'extract_from_jd')}
                        disabled={!jobDescriptionText.trim()}
                      >
                        <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
                        Extrair Requisitos
                      </button>
                    </div>
                  </div>
                )}

                {/* Aba: Boolean */}
                {activeSearchTab === 'boolean' && (
                  <div className="space-y-3">
                    <p className="text-xs lia-body">Use operadores booleanos para buscas precisas</p>
                    <div className="relative">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2">
                        <Code className="w-4 h-4 text-gray-600" />
                      </div>
                      <input
                        type="text"
                        value={booleanSearchValue}
                        onChange={(e) => setBooleanSearchValue(e.target.value)}
                        placeholder='(Python OR Java) AND "São Paulo" NOT junior'
                        className="lia-input w-full pl-10 pr-[180px] py-2.5 text-sm font-mono"
                      />
                      
                      {/* Ícones de Fonte e Contato dentro do input */}
                      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                        {/* Fonte de busca: Local / Híbrido / Global */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  searchSource === 'local' 
                                    ? 'bg-gray-200' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-500'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Base Local</p>
                              <p className="text-micro text-gray-400">Gratuito</p>
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
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'hybrid' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
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
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'global' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Base Global</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Contato: Email / Telefone */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requireEmails 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-micro text-gray-400">{requireEmails ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requirePhoneNumbers 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Botão de Buscar */}
                        <button 
                          className="w-7 h-7 lia-btn-primary flex items-center justify-center disabled:opacity-50"
                          onClick={() => booleanSearchValue.trim() && onCommand(booleanSearchValue, 'boolean_search')}
                          disabled={!booleanSearchValue.trim()}
                        >
                          <Search className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      <span className="text-xs" style={{color: 'var(--gray-400)'}}>Operadores:</span>
                      {['AND', 'OR', 'NOT', '( )', '" "'].map((op) => (
                        <button
                          key={op}
                          onClick={() => setBooleanSearchValue(prev => prev + ' ' + op + ' ')}
                          className="lia-pill font-mono"
                          style={{padding: '2px 8px'}}
                        >
                          {op}
                        </button>
                      ))}
                    </div>
                    {/* Dica contextual */}
                    <div className="p-2.5 rounded-md" style={{backgroundColor: 'var(--wedo-cyan-bg-06)'}}>
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND "São Paulo"
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Filtros */}
                {activeSearchTab === 'filtros' && (
                  <div className="space-y-3">
                    <p className="text-xs lia-body">Configure filtros avançados para refinar sua busca</p>
                    
                    {/* Resumo de filtros ativos */}
                    {(() => {
                      const activeCount = [
                        advancedFilters.locations?.locations?.length || 0,
                        advancedFilters.job?.titles?.length || 0,
                        advancedFilters.job?.levels?.length || 0,
                        advancedFilters.company?.companyItems?.length || 0,
                        advancedFilters.skills?.skillItems?.length || 0,
                        advancedFilters.education?.degrees?.length || 0,
                        advancedFilters.languages?.languages?.length || 0,
                        advancedFilters.general?.minExperience ? 1 : 0,
                        advancedFilters.general?.maxExperience ? 1 : 0
                      ].reduce((a, b) => a + b, 0)
                      
                      return activeCount > 0 ? (
                        <div className="p-2.5 rounded-md bg-gray-50 border border-gray-100">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                              {activeCount} filtro{activeCount > 1 ? 's' : ''} ativo{activeCount > 1 ? 's' : ''}
                            </span>
                            <button
                              onClick={() => setAdvancedFilters({
                                ppiOptions: {},
                                general: {},
                                locations: {},
                                job: {},
                                company: {},
                                skills: {},
                                education: {},
                                languages: {}
                              })}
                              className="text-xs text-gray-800 dark:text-gray-200 hover:text-status-error"
                            >
                              Limpar
                            </button>
                          </div>
                        </div>
                      ) : null
                    })()}
                    
                    {/* Botão para abrir modal completo */}
                    <button 
                      className="w-full px-4 py-3 bg-white border-2 border-dashed border-gray-100 rounded-md hover:border-gray-300 hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                      onClick={() => setShowAdvancedFiltersModal(true)}
                    >
                      <Filter className="w-4 h-4 text-gray-800" />
                      <span className="text-xs text-gray-800">Abrir Filtros Avançados</span>
                    </button>
                    
                    {/* Botão de aplicar filtros */}
                    <button 
                      className="w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs rounded-md transition-colors flex items-center justify-center gap-2"
                      onClick={() => {
                        onCommand(JSON.stringify(advancedFilters), 'apply_filters')
                      }}
                    >
                      <Search className="w-3.5 h-3.5" />
                      Buscar com Filtros
                    </button>
                  </div>
                )}

                {/* Aba: Arquétipos */}
                {activeSearchTab === 'arquetipos' && (
                  <div className="space-y-4">
                    {/* Seção: Criar Arquétipo com contexto de busca */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Criar Novo Arquétipo</span>
                        {naturalSearchValue && (
                          <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-gray-600 dark:text-gray-400 border-gray-900 dark:border-gray-50">
                            Busca ativa detectada
                          </Badge>
                        )}
                      </div>
                      
                      {/* Pré-preenchimento com contexto de busca */}
                      {naturalSearchValue && (
                        <div className="p-3 rounded-md border border-wedo-cyan/30 bg-wedo-cyan/5">
                          <div className="flex items-start gap-2 mb-2">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan mt-0.5" />
                            <span className="text-xs text-gray-600">Contexto da busca atual:</span>
                          </div>
                          <p className="text-sm text-gray-800 mb-2">{naturalSearchValue}</p>
                          
                          {/* Tags de entidades extraídas */}
                          {Object.keys(parsedEntities).length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              {parsedEntities.job_title && (
                                <Badge variant="secondary" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-gray-300 dark:border-gray-600">
                                  {parsedEntities.job_title}
                                </Badge>
                              )}
                              {parsedEntities.location && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  <MapPin className="w-2.5 h-2.5 mr-0.5" />
                                  {parsedEntities.location}
                                </Badge>
                              )}
                              {parsedEntities.seniority && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  {parsedEntities.seniority}
                                </Badge>
                              )}
                              {parsedEntities.industry && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  <Building2 className="w-2.5 h-2.5 mr-0.5" />
                                  {parsedEntities.industry}
                                </Badge>
                              )}
                              {parsedEntities.skills && parsedEntities.skills.map((skill, idx) => (
                                <Badge key={idx} variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          )}
                          
                          {/* Botão primário: Salvar busca como arquétipo (quando há entidades) */}
                          {hasParsedEntities() ? (
                            <button
                              onClick={createArchetypeFromActiveSearch}
                              disabled={isCreatingFromSearch}
                              className="mt-3 w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs rounded-md transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isCreatingFromSearch ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  Salvando arquétipo...
                                </>
                              ) : (
                                <>
                                  <Target className="w-3.5 h-3.5" />
                                  Salvar Busca como Arquétipo
                                </>
                              )}
                            </button>
                          ) : (
                            <button
                              onClick={() => {
                                setNewArchetypeDescription(naturalSearchValue)
                              }}
                              className="mt-3 w-full px-3 py-1.5 bg-gray-100 text-gray-800 dark:text-gray-200 text-xs rounded-md hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5"
                            >
                              <Plus className="w-3 h-3" />
                              Usar como base para novo arquétipo
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* Divisor quando há busca ativa */}
                      {naturalSearchValue && hasParsedEntities() && (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-px bg-gray-200" />
                          <span className="text-micro text-gray-400">ou crie do zero com LIA</span>
                          <div className="flex-1 h-px bg-gray-200" />
                        </div>
                      )}
                      
                      {/* Campo de descrição para criar arquétipo (opção secundária) */}
                      <div className="relative">
                        <textarea
                          value={newArchetypeDescription}
                          onChange={(e) => setNewArchetypeDescription(e.target.value)}
                          placeholder="Descreva o perfil ideal: cargo, habilidades, experiência..."
                          className="lia-input w-full px-3 py-2.5 text-sm resize-none"
                          rows={2}
                        />
                      </div>
                      
                      <button
                        onClick={() => createArchetypeFromDescription(newArchetypeDescription)}
                        disabled={isCreatingArchetype || !newArchetypeDescription.trim()}
                        className="w-full px-3 py-2 bg-gray-900 text-white text-xs rounded-md hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isCreatingArchetype ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Criando arquétipo...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-3.5 h-3.5" />
                            Criar Arquétipo com LIA
                          </>
                        )}
                      </button>
                    </div>
                    
                    {/* Divisor */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-200" />
                      <span className="text-xs text-gray-500">ou selecione um existente</span>
                      <div className="flex-1 h-px bg-gray-200" />
                    </div>
                    
                    {/* Lista de Arquétipos Existentes */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Meus Arquétipos</span>
                        <Badge variant="outline" className="text-micro">
                          {filteredArchetypes.length} {filteredArchetypes.length === 1 ? 'arquétipo' : 'arquétipos'}
                        </Badge>
                      </div>
                      
                      {/* Campo de busca */}
                      {archetypes.length > 3 && (
                        <div className="relative">
                          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                          <input
                            type="text"
                            value={archetypeSearchFilter}
                            onChange={(e) => setArchetypeSearchFilter(e.target.value)}
                            placeholder="Buscar arquétipos..."
                            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                          />
                        </div>
                      )}
                      
                      {/* Cards de Arquétipos */}
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {filteredArchetypes.length === 0 ? (
                          <div className="text-center py-6 text-gray-500">
                            <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
                            <p className="text-xs">Nenhum arquétipo encontrado</p>
                            <p className="text-micro text-gray-400 mt-1">Crie um novo acima para começar</p>
                          </div>
                        ) : (
                          filteredArchetypes.map((arch) => (
                            <div
                              key={arch.id}
                              className="group relative p-3 rounded-md border border-gray-100 bg-white hover:border-gray-400 hover:transition-all cursor-pointer"
                              onClick={() => {
                                setSelectedArquetipo(arch.id)
                                const query = (arch as any).query || arch.criteria?.query || arch.description || ""
                                if (query) {
                                  onCommand(query, 'archetype_search')
                                }
                              }}
                            >
                              {/* Edit/Delete buttons */}
                              <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={(e) => openEditArchetype(arch, e)}
                                  className="p-1 rounded-md hover:bg-gray-100 transition-colors"
                                  title="Editar arquétipo"
                                >
                                  <Pencil className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                                </button>
                                <button
                                  onClick={(e) => openDeleteArchetypeDialog(arch, e)}
                                  disabled={isDeletingArchetype === arch.id}
                                  className="p-1 rounded-md hover:bg-status-error/10 transition-colors"
                                  title="Excluir arquétipo"
                                >
                                  {isDeletingArchetype === arch.id ? (
                                    <Loader2 className="w-3.5 h-3.5 text-gray-400 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-status-error" />
                                  )}
                                </button>
                              </div>
                              
                              <div className="flex items-start gap-2.5 pr-16">
                                <span className="text-lg flex-shrink-0">
                                  {(arch as any).emoji || "🎯"}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-gray-800 truncate">
                                    {arch.name}
                                  </div>
                                  {arch.description && (
                                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                                      {arch.description}
                                    </p>
                                  )}
                                  {arch.department && (
                                    <Badge variant="outline" className="mt-1.5 text-micro">
                                      {arch.department}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Dica contextual */}
              <div className="flex items-start gap-2 p-2 bg-gray-50 rounded-md mb-3 border border-gray-100">
                <Lightbulb className="w-3.5 h-3.5 text-gray-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-800 dark:text-gray-200">
                  {activeSearchTab === 'natural' && 'Dica: Para melhores resultados, seja específico sobre skills, senioridade e localização.'}
                  {activeSearchTab === 'similar' && 'Dica: Cole o link do LinkedIn de um candidato que você considera ideal.'}
                  {activeSearchTab === 'job-description' && 'Dica: Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.'}
                  {activeSearchTab === 'boolean' && 'Dica: Use aspas para termos exatos e parênteses para agrupar condições.'}
                  {activeSearchTab === 'filtros' && 'Dica: Combine filtros para refinar sua busca de forma precisa.'}
                  {activeSearchTab === 'arquetipos' && 'Dica: Use arquétipos para salvar perfis ideais e reutilizar em buscas futuras.'}
                </p>
              </div>
            </div>

            {/* 💡 SUGESTÕES CONTEXTUAIS EXPANDIDAS - Seção Principal */}
            <div className="px-4 pb-0">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <LIAIcon size="sm" />
                  <span className="text-sm font-medium text-gray-950 dark:text-gray-50">💡 Sugestões Inteligentes</span>
                  <Badge variant="outline" className="text-xs">
                    {suggestions.length} disponíveis
                  </Badge>
                </div>

                {commandHistory.length > 0 && (
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    className="text-xs text-gray-600 hover:text-gray-700 flex items-center gap-1 transition-colors"
                  >
                    📜 Histórico ({commandHistory.length})
                  </button>
                )}
              </div>

              {/* Histórico de Comandos */}
              {showHistory && commandHistory.length > 0 && (
                <div className="mb-4 p-3 bg-gray-50 rounded-md border">
                  <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Comandos Recentes</h4>
                  <div className="space-y-1">
                    {commandHistory.map((command, index) => (
                      <button
                        key={index}
                        onClick={() => handleHistoryCommand(command)}
                        disabled={isProcessing}
                        className={`w-full text-left text-xs p-2 rounded-md hover:bg-white transition-colors ${
                          isProcessing ? 'opacity-50' : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        📝 {command}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Grid de Sugestões Inteligentes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isProcessing}
                    className={`flex items-start gap-3 p-3 text-left rounded-md border border-gray-100 bg-white transition-all group ${
                      isProcessing
                        ? 'opacity-50 cursor-not-allowed'
                        : 'hover:border-gray-400 hover:'
                    }`}
                  >
                    <span className="text-lg flex-shrink-0">{suggestion.icon}</span>
                    <div className="flex-1">
                      <div className="text-base-ui font-semibold text-gray-800 group-hover:text-gray-700">
                        {suggestion.label}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {suggestion.description}
                      </div>
                      {suggestion.category && (
                        <Badge className="mt-2 text-micro bg-gray-100 text-gray-800 dark:text-gray-200 border-0">
                          {suggestion.category}
                        </Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 💬 ENTRADA DE TEXTO - Seção Inferior */}
            <div className="px-4 pb-4">
              {/* Voice Listening Indicator */}
              {isListening && (
                <div className="flex items-center gap-2 text-sm text-status-error bg-status-error/10 p-2 rounded-md mb-3">
                  <div className="w-2 h-2 bg-status-error rounded-full animate-pulse"></div>
                  <span>🎙️ Ouvindo... Fale seu comando</span>
                </div>
              )}

              {/* Processing Indicator */}
              {isProcessing && (
                <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 p-2 rounded-md mb-3 border border-gray-100">
                  <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full animate-pulse"></div>
                  <span>🧠 LIA processando: "{lastCommand}"</span>
                </div>
              )}

              <div className="text-xs text-gray-800 dark:text-gray-200 text-center pt-2 space-y-1">
                <div>💡 LIA aprende com seus padrões para sugerir ações mais precisas</div>
                <div className="flex justify-center gap-4">
                  <span>⌨️ Esc para fechar</span>
                  <span>Ctrl+K para focar</span>
                  {commandHistory.length > 0 && <span>Ctrl+H para histórico</span>}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast de Sugestão de Template */}
      <TemplateSuggestionToast
        suggestion={suggestionQueue.currentSuggestion}
        onCreateTemplate={(suggestion) => {
          // Abrir página de templates com dados pre-populados
          const templateData = {
            name: `Template: ${suggestion.command.substring(0, 30)}...`,
            command: suggestion.command,
            complexity: suggestion.complexity,
            estimatedTime: suggestion.estimatedTime
          }
          sessionStorage.setItem('lia-create-template', JSON.stringify(templateData))
          window.location.href = '/?page=templates'
          suggestionQueue.clearCurrentSuggestion()
        }}
        onDismiss={(suggestionId) => {
          templateSuggestions.dismissSuggestion(suggestionId)
          suggestionQueue.clearCurrentSuggestion()
        }}
        onNotAskAgain={() => {
          templateSuggestions.updateSettings({ enabled: false })
          suggestionQueue.clearCurrentSuggestion()
        }}
      />

      {/* Modal de Filtros Avançados */}
      <AdvancedFiltersModal
        isOpen={showAdvancedFiltersModal}
        onClose={() => setShowAdvancedFiltersModal(false)}
        initialFilters={advancedFilters}
        onApply={(filters) => {
          setAdvancedFilters(filters)
          setShowAdvancedFiltersModal(false)
          onCommand(JSON.stringify(filters), 'apply_filters')
        }}
      />

      {/* Modal de Edição de Arquétipo */}
      {editingArchetype && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={closeEditArchetype}
        >
          <div 
            className="bg-white rounded-md p-5 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
            className="border border-gray-200"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{color: "var(--gray-950)"}}>
                Editar Arquétipo
              </h3>
              <button
                onClick={closeEditArchetype}
                className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4" style={{color: "var(--gray-400)"}} />
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="w-16">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Emoji</label>
                  <input
                    type="text"
                    value={editArchetypeEmoji}
                    onChange={(e) => setEditArchetypeEmoji(e.target.value)}
                    maxLength={4}
                    className="w-full rounded-md px-2 py-2 text-center text-lg focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Nome</label>
                  <input
                    type="text"
                    value={editArchetypeName}
                    onChange={(e) => setEditArchetypeName(e.target.value)}
                    placeholder="Nome do arquétipo"
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Query de Busca</label>
                <textarea
                  value={editArchetypeQuery}
                  onChange={(e) => setEditArchetypeQuery(e.target.value)}
                  placeholder="Ex: Desenvolvedor Python Sênior São Paulo"
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-gray-200"
                />
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Descrição (opcional)</label>
                <textarea
                  value={editArchetypeDescription}
                  onChange={(e) => setEditArchetypeDescription(e.target.value)}
                  placeholder="Breve descrição do perfil ideal..."
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-gray-200"
                />
              </div>

              {/* Tags Section */}
              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Tags</label>
                
                {/* Existing tags as removable chips */}
                {editArchetypeTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {editArchetypeTags.map((tag, index) => (
                      <Badge 
                        key={index} 
                        variant="secondary" 
                        className="text-xs bg-gray-100 text-gray-800 dark:text-gray-200 pr-1 flex items-center gap-1"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => setEditArchetypeTags(prev => prev.filter((_, i) => i !== index))}
                          className="ml-0.5 rounded-full hover:bg-gray-200 p-0.5 transition-colors"
                        >
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
                
                {/* Input to add new tags */}
                <div className="relative">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newTagInput.trim()) {
                        e.preventDefault()
                        if (!editArchetypeTags.includes(newTagInput.trim())) {
                          setEditArchetypeTags(prev => [...prev, newTagInput.trim()])
                        }
                        setNewTagInput("")
                      }
                    }}
                    placeholder="Digite e pressione Enter para adicionar..."
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-micro text-gray-400">
                    Enter ↵
                  </span>
                </div>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <Button
                onClick={closeEditArchetype}
                variant="outline"
                className="flex-1"
                style={{color: "var(--gray-400)"}}
              >
                Cancelar
              </Button>
              <Button
                onClick={saveArchetype}
                disabled={isSavingArchetype || !editArchetypeName}
                className="flex-1"
                style={{backgroundColor: editArchetypeName ? "var(--gray-950)" : "var(--gray-200)",
                  color: editArchetypeName ? "white" : "var(--gray-400)"}}
              >
                {isSavingArchetype ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-1.5" />
                    Salvar
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação para Exclusão de Arquétipo */}
      <AlertDialog open={showDeleteArchetypeDialog} onOpenChange={setShowDeleteArchetypeDialog}>
        <AlertDialogContent 
          className="sm:max-w-[320px] w-[85vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-4 rounded-md border" 
          style={{backgroundColor: 'var(--gray-50)'}}
        >
          <AlertDialogHeader>
            <AlertDialogTitle className="text-base font-semibold text-gray-800 flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-status-error" />
              Excluir Arquétipo
            </AlertDialogTitle>
            <AlertDialogDescription className="text-sm text-gray-600">
              Tem certeza que deseja excluir o arquétipo{' '}
              <span className="font-medium text-gray-800">"{archetypeToDelete?.name}"</span>?
              <br />
              <span className="text-xs text-gray-500 mt-1 block">
                Esta ação não pode ser desfeita.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 mt-4">
            <AlertDialogCancel 
              onClick={() => {
                setShowDeleteArchetypeDialog(false)
                setArchetypeToDelete(null)
              }}
              className="flex-1 h-9 text-sm px-3 rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteArchetype}
              className="flex-1 h-9 text-sm px-3 rounded-md text-white flex items-center justify-center gap-1.5"
              style={{backgroundColor: 'var(--status-error)'}}
            >
              <Trash2 className="w-3.5 h-3.5" />
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent 
          className="sm:max-w-sidebar-content w-[80vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-3 rounded-md border" 
          style={{backgroundColor: 'var(--gray-100)'}}
        >
          <div className="space-y-2 text-[10px] leading-snug" >
            <div className="flex items-center gap-1.5">
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-3 h-3 text-gray-600" />
              ) : (
                <Globe className="w-3 h-3 text-status-warning" />
              )}
              <h3 className="font-semibold text-xs text-gray-800">
                {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
              </h3>
            </div>
            
            <p className="text-micro text-gray-500">
              {pendingSourceChange === 'hybrid' 
                ? 'Combina base local + global (800M+ perfis).'
                : 'Acessa 800M+ perfis profissionais.'}
            </p>
            
            <div className="bg-white rounded-md p-2 space-y-1 border border-gray-100">
              {pendingSourceChange === 'hybrid' && (
                <div className="flex justify-between text-micro">
                  <span className="text-gray-600">Local:</span>
                  <span className="font-medium text-wedo-green-light">Grátis</span>
                </div>
              )}
              <div className="flex justify-between text-micro">
                <span className="text-gray-600">Global:</span>
                <span className="font-medium text-status-warning">1 cr/candidato</span>
              </div>
              <div className="flex justify-between text-micro pt-1 border-t border-gray-100">
                <span className="font-medium text-gray-800 dark:text-gray-200">Total estimado:</span>
                <span className="font-semibold text-status-warning">1 cr/candidato</span>
              </div>
            </div>
            
            <div className="flex gap-1.5 pt-1">
              <button
                onClick={() => {
                  setShowSourceChangeModal(false)
                  setPendingSourceChange(null)
                }}
                className="flex-1 h-6 text-micro px-2 rounded-full bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSourceChange}
                className="flex-1 h-6 text-micro px-2 rounded-full text-white flex items-center justify-center gap-1 bg-gray-900"
              >
                {pendingSourceChange === 'hybrid' ? (
                  <>
                    <Zap className="w-2.5 h-2.5" />
                    Ativar
                  </>
                ) : (
                  <>
                    <Globe className="w-2.5 h-2.5" />
                    Ativar
                  </>
                )}
              </button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Save Archetype Modal */}
      <SaveArchetypeModal
        open={showSaveArchetypeModal}
        onClose={() => setShowSaveArchetypeModal(false)}
        searchSpec={buildSearchSpecFromEntities}
        query={naturalSearchValue}
        onSuccess={handleArchetypeSaved}
      />
    </div>
  )
}

