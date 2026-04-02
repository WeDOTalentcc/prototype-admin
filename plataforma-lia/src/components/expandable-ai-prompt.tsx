"use client"

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useTemplateSuggestions } from "@/hooks/use-template-suggestions"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LIAIcon } from "@/components/ui/lia-icon"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from "@/components/ui/quick-action-chips"
import { Card, CardContent } from "@/components/ui/card"
import { useCreditEstimator, formatCreditCost, getCostLevel, getCostColor, CREDIT_COSTS } from "@/hooks/useCreditEstimator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
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
    border: 'var(--lia-text-tertiary)',
    bg: 'var(--lia-bg-secondary)',
    headerText: 'var(--lia-text-secondary)',
    headerBg: 'var(--lia-bg-secondary)'
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
  criteria?: Record<string, unknown>
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
  selectedCandidates: Record<string, unknown>[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: Record<string, unknown>
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
import { EAPTabContent } from './expandable-ai-prompt/EAPTabContent'
import { EAPModals } from './expandable-ai-prompt/EAPModals'
import { toast } from "sonner"

export function ExpandableAIPrompt(props: ExpandableAIPromptProps) {
  // @ts-ignore TODO: fix type — Argument of type 'ExpandableAIPromptProps' is not assignable to parameter of typ
  const core = useExpandableAIPromptCore(props)
  const {
    MAX_CV_FILES, MAX_SIMILAR_URLS, activeSearchTab, advancedFilters, archetypeToDelete,
    buildSearchSpecFromEntities, candidateContext, candidateLimit,
    closeEditArchetype, commandHistory, confirmDeleteArchetype, confirmSourceChange, contextPill,
    creditEstimate, editArchetypeDescription, editArchetypeEmoji, editArchetypeName, editArchetypeQuery, editArchetypeTags, editingArchetype,
    filledTagsCount, getPlaceholder,
    handleArchetypeSaved, handleAudioTranscription, handleFileAnalyzed, handleHistoryCommand,
    handleSourceChange, handleSubmit, handleSuggestionClick, inputValue, isExpanded, isListening, isProcessing, isSavingArchetype,
    jobContext, lastCommand, naturalSearchValue, newTagInput, onClose, onCommand,
    pageContext, pearchSearchType, pendingSourceChange,
    quickActions, requireEmails, requirePhoneNumbers, saveArchetype,
    searchSource, selectedCandidates, setActiveSearchTab, setAdvancedFilters, setArchetypeToDelete,
    setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeTags, setInputValue, setIsExpanded,
    setNewTagInput, setPendingSourceChange, setRequireEmails, setRequirePhoneNumbers, setSearchSource,
    setShowAdvancedFiltersModal, setShowDeleteArchetypeDialog, setShowHistory, setShowSaveArchetypeModal, setShowSourceChangeModal,
    showAdvancedFiltersModal, showDeleteArchetypeDialog, showGlobalSearchOptions, showHistory, showSaveArchetypeModal,
    showSourceChangeModal, statusInfo, suggestionQueue, suggestions, templateSuggestions, searchTags,
  } = core

    return (
    <div className="space-y-3">

      {/* Candidato Específico Preview */}
      {candidateContext && (
        <div className="bg-wedo-green-light/5 rounded-md p-3 border border-wedo-green-light/20">
          <div className="flex items-center gap-2 mb-2">
            <LIAIcon size="sm" />
            <span className="text-base-ui font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              Análise LIA para candidato específico
            </span>
          </div>
          <div className="flex items-center gap-3 bg-lia-bg-primary rounded-md px-3 py-2 border border-lia-border-subtle">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-wedo-green-light/10 text-wedo-green-light text-sm">
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
            <Badge className="bg-wedo-green-light/10 text-wedo-green-light border-0 text-micro">
              Foco Individual
            </Badge>
          </div>
        </div>
      )}

      {/* Candidatos Selecionados Preview */}
      {!candidateContext && selectedCandidates.length > 0 && (
        <div className="bg-lia-bg-secondary rounded-md p-3 border border-lia-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-lia-text-secondary" />
            <span className="text-base-ui font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {selectedCandidates.length} candidato{selectedCandidates.length > 1 ? 's' : ''} selecionado{selectedCandidates.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCandidates.slice(0, 3).map((candidate, index) => (
              // @ts-ignore TODO: fix type — Type '{}' is not assignable to type 'Key | null | undefined'.
              <div key={candidate.name || index} className="flex items-center gap-1 bg-lia-bg-primary rounded-md px-2 py-1 border border-lia-border-subtle">
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

      {/* Prompt Principal */}
      <div className={`transition-colors motion-reduce:transition-none duration-300 ${statusInfo.bgColor} rounded-md border ${statusInfo.bgColor.includes('border') ? '' : 'border-lia-border-subtle'} overflow-hidden`}>

        {/* Campo de input compacto */}
        <div className="p-3">
          <form onSubmit={handleSubmit} className="flex items-center gap-3">

            {/* LIA Icon */}
            <LIAIcon
              size="lg"
              animate={isProcessing}
              className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 ${isProcessing ? 'scale-110' : ''}`}
            />

            {/* Input Field */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => !isProcessing && setIsExpanded(true)}
              placeholder={isProcessing ? "LIA processando..." : getPlaceholder()}
              disabled={isProcessing}
              className={`flex-1 bg-transparent text-lia-text-primary placeholder-lia-text-tertiary text-xs focus:outline-none ${
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
              
              {/* Separador visual */}
              <div className="w-px h-4 bg-lia-interactive-active mx-1" />
              
              {/* Toggle Email */}
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
                    <p className="text-micro text-lia-text-secondary">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
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
                    <p className="text-micro text-lia-text-secondary">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
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

        {/* Área Expandida - REORGANIZADA SEM DUPLICAÇÃO */}
        {isExpanded && (
          <div className="lia-prompt-expanded space-y-4" style={{backgroundColor: 'var(--lia-bg-tertiary)'}}>

            {/* AI-First Context Pills + Quick Actions */}
            {(contextPill || quickActions.length > 0) && (
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
                    <QuickActionChips actions={quickActions as unknown as QuickAction[]} />
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
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
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
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
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
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
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
                      <div className="bg-lia-btn-primary-bg text-lia-btn-primary-text px-3 py-2 rounded-md text-xs min-w-[220px]">
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
                              <div className="flex justify-between pb-1.5 border-b border-lia-border-strong">
                                <span className="lia-text-muted">Saldo disponível:</span>
                                <span className={`font-medium ${
 creditEstimate.canAfford ? 'text-status-success' : 'text-status-error'
                                }`}>
                                  {creditEstimate.availableCredits} créditos
                                </span>
                              </div>
                            )}
                            <div className="flex justify-between">
                              <span className="lia-text-muted">Tipo de busca:</span>
                              <span className="font-medium">{pearchSearchType === 'fast' ? 'Rápida' : 'Profissional'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="lia-text-muted" aria-live="polite" aria-atomic="true">Por candidato:</span>
                              <span className="font-medium">{creditEstimate.perCandidate} créditos</span>
                            </div>
                            <div className="flex justify-between pt-1.5 border-t border-lia-border-strong">
                              <span className="lia-text-muted">Total ({candidateLimit} cand.):</span>
                              <span className={`font-bold ${getCostColor(getCostLevel(creditEstimate.total))}`}>
                                {creditEstimate.total} créditos
                              </span>
                            </div>
                            {!creditEstimate.canAfford && (
                              <div className="text-xs text-status-error mt-1.5 pt-1.5 border-t border-lia-border-strong flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                Saldo insuficiente para esta busca
                              </div>
                            )}
                          </div>
                        )}
                        <div className="absolute bottom-full right-4 border-4 border-transparent border-b-lia-btn-primary-bg"></div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Contador de critérios */}
                  <span className="text-xs text-lia-text-secondary hidden md:inline">
                    {filledTagsCount}/5 critérios
                  </span>
                </div>
              </div>
              
              {/* 6 Abas de Pesquisa */}
              <div className="flex items-center gap-1.5 mb-3 overflow-x-auto pb-1">
                <button
                  onClick={() => setActiveSearchTab('natural')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
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
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
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
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
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
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
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
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
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
                        className="ml-1 p-1.5 rounded-md hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none border border-lia-border-subtle"
                      >
                        <Table2 className="w-3.5 h-3.5 text-lia-text-secondary" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs font-medium">Abrir em Tabela</p>
                      <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Ir para resultados de busca</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Conteúdo da Aba Ativa */}
              <div className="mb-3">
                <EAPTabContent {...core} />
              </div>

              
              {/* Dica contextual */}
              <div className="flex items-start gap-2 p-2 bg-lia-bg-secondary rounded-md mb-3 border border-lia-border-subtle">
                <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary mt-0.5 flex-shrink-0" />
                <p className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
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
                  <span className="text-sm font-medium text-lia-text-primary">💡 Sugestões Inteligentes</span>
                  <Badge variant="outline" className="text-xs">
                    {suggestions.length} disponíveis
                  </Badge>
                </div>

                {commandHistory.length > 0 && (
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    className="text-xs text-lia-text-secondary hover:text-lia-text-secondary flex items-center gap-1 transition-colors motion-reduce:transition-none"
                  >
                    📜 Histórico ({commandHistory.length})
                  </button>
                )}
              </div>

              {/* Histórico de Comandos */}
              {showHistory && commandHistory.length > 0 && (
                <div className="mb-4 p-3 bg-lia-bg-secondary rounded-md border">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-2">Comandos Recentes</h4>
                  <div className="space-y-1">
                    {commandHistory.map((command, index) => (
                      <button
                        key={`hist-${index}`}
                        onClick={() => handleHistoryCommand(command)}
                        disabled={isProcessing}
                        className={`w-full text-left text-xs p-2 rounded-md hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none ${
 isProcessing ? 'opacity-50' : 'text-lia-text-secondary hover:text-lia-text-primary'
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
                    // @ts-ignore TODO: fix type — Type 'unknown' is not assignable to type 'Key | null | undefined'.
                    key={suggestion.id}
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isProcessing}
                    // @ts-ignore TODO: fix type — Type 'unknown' is not assignable to type 'ReactNode'.
                    className={`flex items-start gap-3 p-3 text-left rounded-md border border-lia-border-subtle bg-lia-bg-primary transition-colors motion-reduce:transition-none group ${
 isProcessing
                        ? 'opacity-50 cursor-not-allowed'
                        // @ts-ignore TODO: fix type — Type 'unknown' is not assignable to type 'ReactNode'.
                        : 'hover:border-lia-border-medium hover:'
                    }`}
                  >
                    <span className="text-lg flex-shrink-0">{suggestion.icon as React.ReactNode}</span>
                    <div className="flex-1">
                      <div className="text-base-ui font-semibold text-lia-text-primary group-hover:text-lia-text-secondary">
                        {suggestion.label as React.ReactNode}
                      </div>
                      <div className="text-xs text-lia-text-secondary mt-1">
                        {(suggestion.description as React.ReactNode)}
                      </div>
                      {!!(suggestion.category) && (
                        <Badge className="mt-2 text-micro bg-lia-bg-tertiary text-lia-text-primary border-0">
                          {(suggestion.category as React.ReactNode)}
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
                  <div className="w-2 h-2 bg-status-error rounded-full animate-pulse motion-reduce:animate-none"></div>
                  <span>🎙️ Ouvindo... Fale seu comando</span>
                </div>
              )}

              {/* Processing Indicator */}
              {isProcessing && (
                <div className="flex items-center gap-2 text-xs text-lia-text-secondary bg-lia-bg-secondary p-2 rounded-md mb-3 border border-lia-border-subtle">
                  <div className="w-2 h-2 bg-lia-btn-primary-bg rounded-full animate-pulse motion-reduce:animate-none"></div>
                  <span>🧠 LIA processando: "{lastCommand}"</span>
                </div>
              )}

              <div className="text-xs text-lia-text-primary text-center pt-2 space-y-1">
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
        // @ts-ignore TODO: fix type — Type 'Dispatch<SetStateAction<"hybrid" | "global" | null>>' is not assignable to
        setPendingSourceChange={setPendingSourceChange}
        confirmSourceChange={confirmSourceChange}
        showSaveArchetypeModal={showSaveArchetypeModal}
        setShowSaveArchetypeModal={setShowSaveArchetypeModal}
        // @ts-ignore TODO: fix type — Type 'SearchSpec | null' is not assignable to type 'SearchSpec'.
        buildSearchSpecFromEntities={buildSearchSpecFromEntities}
        naturalSearchValue={naturalSearchValue}
        // @ts-ignore TODO: fix type — Type '(newArchetype: ArchetypeData) => void' is not assignable to type '() => vo
        handleArchetypeSaved={handleArchetypeSaved}
      />
    </div>
  )
}

