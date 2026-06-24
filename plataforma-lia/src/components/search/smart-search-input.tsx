"use client"

import { useState, useEffect, useCallback, useRef } from"react"
import { 
  Check, MapPin, Briefcase, Clock, Building2, Code, X, Search, 
  FileText, Binary, Users, Upload, Filter, AlertCircle,
  Globe, GraduationCap, DollarSign, Star, Target, ChevronRight,
  User, Award, Loader2, GripVertical, Lightbulb, Linkedin, Info,
  AlertTriangle, CheckCircle2, HelpCircle, Wand2, TrendingUp, Plus, Brain,
  Pencil, Trash2, MoreHorizontal, Home, Zap, Mail, Phone, Table2,
  ChevronUp, ChevronDown, Tag
} from"lucide-react"
import { cn } from"@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from"@/components/ui/tooltip"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from"@/components/ui/alert-dialog"
import { useGlobalSearchSettings } from"@/hooks/search/useGlobalSearchSettings"
import { INDUSTRIES, INDUSTRY_CATEGORIES, type Industry } from"@/lib/industry-constants"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"
import { AudioRecordButton } from"@/components/ui/audio-record-button"
import { EditArchetypeModal } from"./EditArchetypeModal"
import { SearchModeArchetypes } from"./SearchModeArchetypes"

export interface ParsedEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
  work_model?: string
}

export type SearchSource ="local" |"global" |"hybrid"

export interface SmartSearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => void
  onCancel: () => void
  onOpenFilters?: () => void
  onGoToResults?: () => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  activeFiltersCount?: number
  searchSource?: SearchSource
  onSearchSourceChange?: (source: SearchSource) => void
  requireEmails?: boolean
  onRequireEmailsChange?: (value: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (value: boolean) => void
  initialJdContent?: string
}

export type SearchMode ="natural" |"similar" |"jd" |"boolean" |"archetypes"

export interface ArchetypeCandidate {
  id: string
  name: string
  current_title?: string
  years_experience?: number
  skills?: string[]
  hired_at?: string
}

export interface ArchetypeVacancy {
  id: string
  title: string
  name?: string
  emoji?: string
  is_default?: boolean
  description?: string
  query?: string
  tags?: string[]
  seniority?: string
  industry?: string
  filters?: Record<string, unknown>
  department?: string
  closed_at?: string
  hired_candidate?: ArchetypeCandidate
}

export interface SearchMetadata {
  mode: SearchMode
  booleanQuery?: string
  jobDescription?: string
  similarProfileUrl?: string
  similarProfileUrls?: string[]
  combinedProfile?: CombinedProfileSuggestion
  archetypeVacancyId?: string
  archetypeCandidateId?: string
  archetypeProfile?: ArchetypeCandidate
  filters?: Record<string, unknown>
  searchText?: string
}

export interface CombinedProfileSuggestion {
  keywords: string[]
  title?: string
  seniority?: string
  skills_technical?: string[]
  skills_soft?: string[]
  industries?: string[]
  location?: string
  summary?: string
}

interface SearchTag {
  key: keyof ParsedEntities
  label: string
  icon: React.ElementType
  filled: boolean
  value?: string
}

interface SearchAlert {
  type: string
  severity:"info" |"warning" |"error"
  message: string
  suggestion?: string
  action_label?: string
  action_value?: string
}

interface SearchAnalysis {
  completeness_score: number
  filled_criteria: string[]
  missing_criteria: string[]
  alerts: SearchAlert[]
  enrichment_suggestions: Record<string, string[]>
  next_recommended_action?: string
}

interface AutocompleteItem {
  text: string
  category: string
  icon: string
  description?: string
  insert_text: string
}

interface AutocompleteResponse {
  items: AutocompleteItem[]
  context_hint?: string
}

const API_BASE =""

// Sugestões cobrindo os 5 critérios: Location, Job Title, Experience, Industry, Skills
export const SEARCH_SUGGESTIONS = [
  'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
  'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis'
]

import { useSmartSearchCore } from './hooks/useSmartSearchCore'
import { SSIModeContent } from './SSIModeContent'

export function SmartSearchInput(props: SmartSearchInputProps) {
  const core = useSmartSearchCore(props)
  const {
    activeFiltersCount, canSubmit, className, confirmSourceChange, containerRef,
    editingArchetype, closeEditArchetype, entities, filledCount, formatDate, getPlaceholder,
    ghostOverlayRef, ghostTextInfo, ghostTextSuffix, handleKeyDown, handleSubmit,
    hasMultipleSources, isLoading, isLoadingArchetypes, isParsingEntities,
    mode, onChange, onGoToResults, onOpenFilters,
    onSubmit, panelWidth, pendingSourceChange, placeholder,
    requireEmails, requirePhoneNumbers, searchSource,
    setMode, setPendingSourceChange, setShowSourceChangeModal,
    showSourceChangeModal, textareaRef, modes, tags, value,
    fileInputRef, handleFileUpload, handleSourceChange, onRequireEmailsChange,
    onRequirePhoneNumbersChange, onSearchSourceChange,
    saveArchetype, isSavingArchetype,
    editArchetypeDescription, editArchetypeEmoji, editArchetypeEmploymentType, editArchetypeExperienceMin,
    editArchetypeIndustry, editArchetypeLanguages, editArchetypeLocation, editArchetypeName,
    editArchetypeQuery, editArchetypeSeniority, editArchetypeSkills, editArchetypeTags, editArchetypeWorkModel,
    setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeEmploymentType, setEditArchetypeExperienceMin,
    setEditArchetypeIndustry, setEditArchetypeLanguages, setEditArchetypeLocation, setEditArchetypeName,
    setEditArchetypeQuery, setEditArchetypeSeniority, setEditArchetypeSkills, setEditArchetypeTags, setEditArchetypeWorkModel,
    newLanguageInput, setNewLanguageInput, newSkillInput, setNewSkillInput, newTagInput, setNewTagInput,
    aiSuggestedSkills, setAiSuggestedSkills, selectedAiSkills, setSelectedAiSkills,
    isFindingSimilarSkills, setIsFindingSimilarSkills, showSkillSuggestions, setShowSkillSuggestions,
    aiSuggestedTags, setAiSuggestedTags, selectedAiTags, setSelectedAiTags,
    isFindingSimilarTags, setIsFindingSimilarTags, showTagSuggestions, setShowTagSuggestions,
    industrySearchQuery, setIndustrySearchQuery, isIndustryDropdownOpen, setIsIndustryDropdownOpen,
    showGlobalSearchOptions,
  } = core

    return (
    <div 
      ref={containerRef}
      className={cn("space-y-4 relative", className)}
      style={{width: panelWidth}}
    >
      <div 
        className="rounded-md overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary"
      >
        {/* Mode tabs - Estilo pill/tag elegante */}
        <div 
          className="flex items-center gap-2 px-4 py-3 overflow-x-auto bg-lia-bg-primary"
        >
          {modes.map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors border",
                mode === m.key 
                  ?"border-lia-btn-primary-bg bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                  :"border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary dark:hover:bg-lia-btn-primary-hover"
              )}
            >
              <m.icon className="w-3.5 h-3.5" />
              {m.label}
            </button>
          ))}

          {/* Filters button - ao lado de Arquétipos - shows dynamic count from parsed entities */}
          {onOpenFilters && (
            <button
              onClick={onOpenFilters}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors border border-lia-border-subtle hover:bg-lia-bg-tertiary hover:text-lia-text-primary dark:hover:bg-lia-btn-primary-hover",
                (activeFiltersCount > 0 || filledCount > 0) &&"ring-1 ring-lia-btn-primary-bg/20",
                (activeFiltersCount > 0 || filledCount > 0) ?"text-lia-text-primary bg-lia-interactive-active" :"text-lia-text-secondary bg-transparent"
              )}
            >
              <Filter className="w-3.5 h-3.5" />
              Filtros
              {(activeFiltersCount > 0 || filledCount > 0) && (
                <Chip variant="neutral" muted
                  className="ml-1 h-4 min-w-4 px-1 flex items-center justify-center text-xs"
                >
                  {Math.max(activeFiltersCount, filledCount)}
                </Chip>
              )}
            </button>
          )}

          {/* Botão para ir direto para página de resultados */}
          {onGoToResults && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={onGoToResults}
                    className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-lia-bg-tertiary transition-[width,height] text-lia-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
                    aria-label="Ir para Resultados"
                  >
                    <Table2 className="w-4 h-4" aria-hidden="true" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium" aria-live="polite" aria-atomic="true">Ir para Resultados</p>
                  <p className="text-xs text-lia-text-muted">Buscar direto na tabela expandida</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Content area - changes based on mode */}
        <div className="p-4 bg-[var(--lia-bg-primary)]">
          {/* Natural search mode */}
          <SSIModeContent {...core} />
        </div>
      </div>


      {mode ==="natural" && filledCount === 0 && value.length > 0 && (
        <p 
          className="text-xs px-1 text-lia-text-secondary"
         aria-live="polite" aria-atomic="true">
          Dica: Inclua cargo, localização e skills para melhores resultados
        </p>
      )}

      {/* Modal de Edição de Arquétipo — extraído para EditArchetypeModal.tsx */}
      {editingArchetype && (
        <EditArchetypeModal
          editingArchetype={editingArchetype}
          editArchetypeName={editArchetypeName}
          onEditArchetypeNameChange={setEditArchetypeName}
          editArchetypeQuery={editArchetypeQuery}
          onEditArchetypeQueryChange={setEditArchetypeQuery}
          editArchetypeDescription={editArchetypeDescription}
          onEditArchetypeDescriptionChange={setEditArchetypeDescription}
          editArchetypeEmoji={editArchetypeEmoji}
          onEditArchetypeEmojiChange={setEditArchetypeEmoji}
          editArchetypeTags={editArchetypeTags}
          onEditArchetypeTagsChange={setEditArchetypeTags}
          editArchetypeSkills={editArchetypeSkills}
          onEditArchetypeSkillsChange={setEditArchetypeSkills}
          editArchetypeSeniority={editArchetypeSeniority}
          onEditArchetypeSeniorityChange={setEditArchetypeSeniority}
          editArchetypeIndustry={editArchetypeIndustry}
          onEditArchetypeIndustryChange={setEditArchetypeIndustry}
          editArchetypeExperienceMin={editArchetypeExperienceMin}
          onEditArchetypeExperienceMinChange={setEditArchetypeExperienceMin}
          editArchetypeLocation={editArchetypeLocation}
          onEditArchetypeLocationChange={setEditArchetypeLocation}
          editArchetypeWorkModel={editArchetypeWorkModel}
          onEditArchetypeWorkModelChange={setEditArchetypeWorkModel}
          editArchetypeLanguages={editArchetypeLanguages}
          onEditArchetypeLanguagesChange={setEditArchetypeLanguages}
          editArchetypeEmploymentType={editArchetypeEmploymentType}
          onEditArchetypeEmploymentTypeChange={setEditArchetypeEmploymentType}
          newLanguageInput={newLanguageInput}
          onNewLanguageInputChange={setNewLanguageInput}
          newTagInput={newTagInput}
          onNewTagInputChange={setNewTagInput}
          newSkillInput={newSkillInput}
          onNewSkillInputChange={setNewSkillInput}
          isSavingArchetype={isSavingArchetype}
          aiSuggestedSkills={aiSuggestedSkills}
          onAiSuggestedSkillsChange={setAiSuggestedSkills}
          selectedAiSkills={selectedAiSkills}
          onSelectedAiSkillsChange={setSelectedAiSkills}
          isFindingSimilarSkills={isFindingSimilarSkills}
          onIsFindingSimilarSkillsChange={setIsFindingSimilarSkills}
          showSkillSuggestions={showSkillSuggestions}
          onShowSkillSuggestionsChange={setShowSkillSuggestions}
          aiSuggestedTags={aiSuggestedTags}
          onAiSuggestedTagsChange={setAiSuggestedTags}
          selectedAiTags={selectedAiTags}
          onSelectedAiTagsChange={setSelectedAiTags}
          isFindingSimilarTags={isFindingSimilarTags}
          onIsFindingSimilarTagsChange={setIsFindingSimilarTags}
          showTagSuggestions={showTagSuggestions}
          onShowTagSuggestionsChange={setShowTagSuggestions}
          industrySearchQuery={industrySearchQuery}
          onIndustrySearchQueryChange={setIndustrySearchQuery}
          isIndustryDropdownOpen={isIndustryDropdownOpen}
          onIsIndustryDropdownOpenChange={setIsIndustryDropdownOpen}
          onClose={closeEditArchetype}
          onSave={saveArchetype}
        />
      )}
      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent 
          className="sm:max-w-[320px] w-[85vw] p-4 rounded-xl border" 
         
        >
          <AlertDialogTitle className="sr-only">
            {pendingSourceChange === 'hybrid' ? 'Ativar Busca Híbrida' : 'Ativar Busca Global'}
          </AlertDialogTitle>
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center ${pendingSourceChange === 'hybrid' ? 'bg-wedo-cyan-bg-15' : 'bg-status-warning-bg-15'}`}
              >
                {pendingSourceChange === 'hybrid' ? (
                  <Zap className="w-4 h-4 text-lia-text-secondary" />
                ) : (
                  <Globe className="w-4 h-4 text-status-warning" />
                )}
              </div>
              <div>
                <h3 className="font-semibold text-base-ui text-lia-text-primary">
                  {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
                </h3>
                <p className="text-micro text-lia-text-secondary">
                  {pendingSourceChange === 'hybrid' 
                    ? 'Combina base local + global (800M+ perfis).'
                    : 'Acessa 800M+ perfis profissionais.'}
                </p>
              </div>
            </div>
            
            <div className="bg-lia-bg-secondary rounded-xl p-3 space-y-2 border border-lia-border-subtle">
              {pendingSourceChange === 'hybrid' && (
                <div className="flex justify-between text-xs">
                  <span className="text-lia-text-secondary">Local:</span>
                  <span className="font-medium text-status-success">Grátis</span>
                </div>
              )}
              <div className="flex justify-between text-xs">
                <span className="text-lia-text-secondary">Global:</span>
                <span className="font-medium text-status-warning" aria-live="polite" aria-atomic="true">1 cr/candidato</span>
              </div>
              <div className="flex justify-between text-xs pt-2 border-t border-lia-border-subtle">
                <span className="font-medium text-lia-text-primary">Total estimado:</span>
                <span className="font-semibold text-status-warning" aria-live="polite" aria-atomic="true">1 cr/candidato</span>
              </div>
            </div>
            
            <div className="flex gap-2.5 pt-1">
              <button
                onClick={() => {
                  setShowSourceChangeModal(false)
                  setPendingSourceChange(null)
                }}
                className="flex-1 h-8 text-xs px-3 rounded-xl bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary font-medium transition-colors motion-reduce:transition-none"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSourceChange}
                className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors motion-reduce:transition-none hover:opacity-90 bg-lia-btn-primary-bg"
              >
                {pendingSourceChange === 'hybrid' ? (
                  <>
                    <Zap className="w-3.5 h-3.5" />
                    Ativar
                  </>
                ) : (
                  <>
                    <Globe className="w-3.5 h-3.5" />
                    Ativar
                  </>
                )}
              </button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default SmartSearchInput

