"use client"

import { cn } from "@/lib/utils"
import { textStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { SearchModeArchetypes } from "./SearchModeArchetypes"
import {
  AlertCircle, AlertTriangle, Award, Binary, Brain, Briefcase, Building2,
  CheckCircle2, ChevronRight, Code, DollarSign, FileText, Globe, GraduationCap,
  HelpCircle, Home, Info, Lightbulb, Linkedin, Loader2, Mail, MapPin,
  Phone, Search, Star, Target, TrendingUp, Upload, Users, Wand2, X, Zap
} from "lucide-react"
import type { useSmartSearchCore } from "./hooks/useSmartSearchCore"
import { SSISimilarMode } from "./SSISimilarMode"

const SEARCH_SUGGESTIONS = [
  'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
  'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis'
]

type SSIModeContentProps = ReturnType<typeof useSmartSearchCore>

export function SSIModeContent(props: SSIModeContentProps) {
  const {
    addSimilarUrl, analyzeProfiles, archetypeCreateMode, archetypeDescription, archetypeSearch, archetypeSearchPrompt, archetypeTab, archetypeVacancies,
    autocompleteEnabled, autocompleteItems, booleanError, buildArchetypePrompt, canSubmit, className, clearSelectedVacancy, combinedSuggestions,
    createArchetypeFromDescription, cvFileInputRef, deleteArchetype, expandedArchetypeId, fileInputRef, filteredArchetypes, formatDate, getPlaceholder,
    ghostOverlayRef, ghostTextInfo, ghostTextSuffix, handleAcceptEnhancement, handleAutocompleteSelect, handleCvUpload, handleDismissEnhancement, handleFileUpload,
    handleKeyDown, handleSelectVacancy, handleSourceChange, handleSubmit, hasMultipleSources, isAnalyzingProfiles, isCreatingArchetype, isDeletingArchetype,
    isLoading, isLoadingArchetypes, isParsingEntities, isSearchingJobs, isSearchingVacancies, jdContent, jdSearchPrompt, jdVacancyResults,
    jdVacancySearch, jobSearchQuery, jobSearchResults, mode, onChange, onRequireEmailsChange, onRequirePhoneNumbersChange, onSearchSourceChange,
    onSubmit, openArchetypeFromJob, openEditArchetype, placeholder, removeCvFile, removeSimilarUrl, removeSuggestion, requireEmails,
    requirePhoneNumbers, searchAnalysis, searchJobsForArchetype, searchSource, selectedArchetype, selectedAutocompleteIndex, selectedVacancy, setArchetypeCreateMode,
    setArchetypeDescription, setArchetypeSearch, setArchetypeSearchPrompt, setArchetypeTab, setAutocompleteEnabled, setAutocompleteItems, setExpandedArchetypeId, setJdContent,
    setJdSearchPrompt, setJdVacancySearch, setJobSearchQuery, setSelectedArchetype, setSelectedAutocompleteIndex, setSelectedVacancy, setShowAutocomplete, setSimilarSearchPrompt,
    showAutocomplete, showCombinedSuggestions, showGlobalSearchOptions, showVacancyResults, similarCvFiles, similarSearchPrompt, similarUrls, tags,
    textareaRef, updateSimilarUrl, value
  } = props

  return (
    <>
{/* Natural search mode */}
{mode === "natural" && (
  <div className="space-y-3">
    <div className="relative">
      {/* Ghost Text Overlay - positioned over textarea */}
      {ghostTextSuffix && !showAutocomplete && (
        <div 
          ref={ghostOverlayRef}
          className="absolute inset-0 pointer-events-none rounded-md px-4 py-3 pr-28 text-base-ui min-h-14 overflow-hidden whitespace-pre-wrap break-words z-[1]"
          aria-hidden="true"
        >
          <span className="text-transparent">{value}</span>
          <span className="text-gray-400">{ghostTextSuffix}</span>
        </div>
      )}
      {/* Actual textarea - fully functional for editing */}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onScroll={(e) => {
          if (ghostOverlayRef.current) {
            ghostOverlayRef.current.scrollTop = e.currentTarget.scrollTop
          }
        }}
        placeholder={getPlaceholder()}
        className={cn("w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-14 transition-all border relative text-gray-950 caret-gray-950 z-[2]", ghostTextSuffix && !showAutocomplete ? "bg-transparent" : "bg-white")}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "var(--gray-300)"
          e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = "var(--gray-200)"
          e.currentTarget.style.boxShadow = "none"
          setTimeout(() => setShowAutocomplete(false), 200)
        }}
        rows={2}
        disabled={isLoading}
      />
      {/* Seletor de Origem de Busca + Filtros de Contato - Próximo ao search */}
      {onSearchSourceChange && (
        <div className="absolute right-12 bottom-2.5 flex items-center gap-1 flex-shrink-0 z-10">
          {/* Source selectors: Local, Hybrid, Global */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                    searchSource === 'local' 
                      ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                      : "hover:bg-gray-100"
                  , searchSource === 'local' ? "text-wedo-green" : "text-gray-400"
                  )}
                >
                  <Home className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="!animate-none !duration-0">
                <p className="text-xs font-medium">Seu banco de talentos</p>
                <p className="text-xs text-gray-300">Gratuito • Local</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {showGlobalSearchOptions && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                      searchSource === 'hybrid' 
                        ? "bg-wedo-orange/15 ring-1 ring-wedo-orange" 
                        : "hover:bg-gray-100"
                    , searchSource === 'hybrid' ? "text-wedo-orange" : "text-gray-400"
                    )}
                  >
                    <Zap className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Expanda sua busca</p>
                  <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                      searchSource === 'global' 
                        ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                        : "hover:bg-gray-100"
                    , searchSource === 'global' ? "text-gray-950" : "text-gray-400"
                    )}
                  >
                    <Globe className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Alcance global</p>
                  <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}

          {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
          {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
            <>
              <div className="w-px h-4 bg-gray-200 mx-0.5" />
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        requireEmails 
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                          : "hover:bg-gray-100"
                      , requireEmails ? "text-wedo-green" : "text-gray-400"
                      )}
                    >
                      <Mail className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        requirePhoneNumbers 
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                          : "hover:bg-gray-100"
                      , requirePhoneNumbers ? "text-wedo-green" : "text-gray-400"
                      )}
                    >
                      <Phone className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}

          {/* Separador visual */}
          <div className="w-px h-5 bg-gray-200 mx-1" />

          {/* Botão Microfone */}
          <AudioRecordButton
            onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
            className="p-1.5 rounded-md hover:bg-gray-100"
          />
        </div>
      )}

      {/* Microfone quando não há seletor de origem */}
      {!onSearchSourceChange && (
        <div className="absolute right-12 bottom-2.5 flex items-center z-10">
          <AudioRecordButton
            onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
            className="p-1.5 rounded-md hover:bg-gray-100"
          />
        </div>
      )}

      <Button
        onClick={handleSubmit}
        disabled={!canSubmit()}
        size="sm"
        className={cn("absolute right-2.5 bottom-2.5 h-8 w-8 p-0 rounded-md transition-all hover:scale-105 z-10", canSubmit() ? "bg-gray-950 text-white" : "bg-gray-100 text-gray-500")}
      >
        <Search className="w-4 h-4" />
      </Button>

      {/* Autocomplete inline - lista vertical compacta */}
      {showAutocomplete && autocompleteItems.length > 0 && (
      <div 
        className="absolute top-full left-0 right-0 mt-0.5 rounded-md border border-gray-200 flex flex-col gap-0 z-10 max-h-52 overflow-hidden bg-[var(--lia-bg-primary)]"
      >
        {/* Header com toggle e botão fechar */}
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span className="text-micro font-medium text-gray-500">Sugestões</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutocompleteEnabled(false)}
              className="text-micro text-gray-400 hover:text-gray-600 transition-colors"
              title="Desativar sugestões"
            >
              Desativar
            </button>
            <button
              onClick={() => {
                setShowAutocomplete(false)
                setAutocompleteItems([])
              }}
              className="p-0.5 rounded-md hover:bg-gray-100 transition-colors"
              title="Fechar lista"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>
          </div>
        </div>
        <div className="py-1 overflow-y-auto max-h-40">
        {autocompleteItems.slice(0, 6).map((item, index) => {
          const IconComponent = 
            item.icon === "code" ? Code :
            item.icon === "briefcase" ? Briefcase :
            item.icon === "map-pin" ? MapPin :
            item.icon === "building" ? Building2 :
            item.icon === "award" ? Award :
            item.icon === "home" ? Building2 :
            item.icon === "globe" ? Globe :
            item.icon === "target" ? Target :
            item.icon === "users" ? Users :
            item.icon === "layers" ? Building2 :
            item.icon === "zap" ? TrendingUp :
            item.icon === "brain" ? Brain :
            item.icon === "database" ? Binary :
            item.icon === "bar-chart" ? TrendingUp :
            item.icon === "layout" ? FileText :
            item.icon === "smartphone" ? Binary :
            item.icon === "cloud" ? Globe :
            item.icon === "settings" ? Code :
            item.icon === "box" ? Binary :
            item.icon === "coffee" ? Code :
            item.icon === "file-code" ? Code :
            item.icon === "clipboard" ? FileText :
            item.icon === "pen-tool" ? Star :
            item.icon === "dollar-sign" ? DollarSign :
            item.icon === "credit-card" ? DollarSign :
            item.icon === "message-circle" ? Globe :
            item.icon === "book" ? GraduationCap :
            Brain

          const getCategoryColor = (category: string) => {
            const cat = category.toLowerCase()
            if (cat.includes('cargo') || cat.includes('título') || cat.includes('job')) 
              return { bg: 'var(--gray-50)', accent: 'var(--gray-600)' }
            if (cat.includes('local') || cat.includes('cidade') || cat.includes('região')) 
              return { bg: 'var(--gray-100)', accent: 'var(--wedo-purple)' }
            if (cat.includes('skill') || cat.includes('tecnologia') || cat.includes('ferramenta')) 
              return { bg: 'var(--gray-50)', accent: 'var(--wedo-green)' }
            if (cat.includes('experiência') || cat.includes('senioridade') || cat.includes('anos')) 
              return { bg: 'var(--status-warning-bg)', accent: 'var(--wedo-orange)' }
            if (cat.includes('setor') || cat.includes('indústria') || cat.includes('área')) 
              return { bg: 'var(--gray-100)', accent: 'var(--gray-600)' }
            return { bg: 'var(--gray-50)', accent: 'var(--gray-600)' }
          }
          const catColor = getCategoryColor(item.category)
          const isSelected = selectedAutocompleteIndex === index

          return (
            <button
              key={`${item.text}-${index}`}
              onClick={() => handleAutocompleteSelect(item)}
              onMouseEnter={() => setSelectedAutocompleteIndex(index)}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-left transition-colors w-full",
                isSelected ? "bg-gray-50" : "hover:bg-gray-50"
              )}
            >
              <IconComponent 
                className="w-3.5 h-3.5 flex-shrink-0" 
                style={{color: catColor.accent}}
              />
              <span 
                className="text-xs font-medium flex-1 truncate text-gray-950 dark:text-gray-50"
              >
                {item.text}
              </span>
              <span 
                className="text-micro text-gray-500 flex-shrink-0"
              >
                {item.category}
              </span>
            </button>
          )
        })}
        </div>
      </div>
      )}

      {/* Ghost Text Tab hint */}
      {ghostTextSuffix && !showAutocomplete && (
        <div 
          className="absolute -bottom-5 right-3 flex items-center gap-1 text-micro text-gray-400"
        >
          <kbd className="px-1 py-0.5 rounded-full bg-gray-100 text-micro font-mono">Tab</kbd>
          <span>para aceitar</span>
        </div>
      )}

    </div>

    {/* Fallback Suggestion Card - shown BELOW the textarea container when enhanced query doesn't start with user text */}
    {ghostTextInfo.showFallbackCard && ghostTextInfo.fullEnhancement && !showAutocomplete && (
      <div 
        className="rounded-md border px-3 py-2 flex items-center gap-2 bg-gray-200/20" style={{ borderColor: 'var(--wedo-cyan-border)' }}
      >
        <Wand2 className="w-3.5 h-3.5 flex-shrink-0 text-gray-700" />
        <div className="flex-1 min-w-0">
          <span className={textStyles.description}>Sugestão: </span>
          <span className="text-xs text-gray-800">{ghostTextInfo.fullEnhancement}</span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={handleAcceptEnhancement}
            className="flex items-center gap-1 px-2 py-1 rounded-full text-micro font-medium hover:bg-wedo-cyan/15 transition-colors text-gray-700"
          >
            <kbd className="px-1 py-0.5 rounded-full bg-gray-100 text-micro font-mono">Tab</kbd>
            <span>Aceitar</span>
          </button>
          <button
            onClick={handleDismissEnhancement}
            className="flex items-center justify-center w-5 h-5 rounded-md hover:bg-gray-100 transition-colors text-gray-400"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>
    )}

    {/* Tags de critérios extraídos - Cores ElevenLabs/WedoTalent */}
    <div className="flex flex-wrap items-center gap-1.5">
      {tags.map((tag) => {
        const getTagColors = (key: string, filled: boolean) => {
          if (!filled) return { bg: 'var(--gray-50)', text: 'var(--gray-800)', iconBg: 'var(--gray-400)', iconBgLight: 'var(--gray-bg-10)' }
          switch (key) {
            case 'job_title':
              return { bg: 'var(--gray-50)', text: 'var(--gray-600)', iconBg: 'var(--gray-600)', iconBgLight: 'var(--gray-600-bg-10)' }
            case 'location':
              return { bg: 'var(--gray-100)', text: 'var(--wedo-purple)', iconBg: 'var(--wedo-purple)', iconBgLight: 'var(--wedo-purple-bg-10)' }
            case 'skills':
              return { bg: 'var(--gray-50)', text: 'var(--status-success)', iconBg: 'var(--wedo-green)', iconBgLight: 'var(--wedo-green-bg-10)' }
            case 'years_experience':
              return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', iconBg: 'var(--wedo-orange)', iconBgLight: 'var(--wedo-orange-bg-15)' }
            case 'industry':
              return { bg: 'var(--gray-100)', text: 'var(--gray-700)', iconBg: 'var(--gray-600)', iconBgLight: 'var(--gray-600-bg-10)' }
            default:
              return { bg: 'var(--gray-50)', text: 'var(--gray-600)', iconBg: 'var(--gray-600)', iconBgLight: 'var(--gray-600-bg-10)' }
          }
        }
        const colors = getTagColors(tag.key, tag.filled)

        return (
          <div
            key={tag.key}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs transition-all"
            style={{backgroundColor: colors.bg,
              color: colors.text}}
            title={tag.value}
          >
            <div 
              className="flex items-center justify-center w-4 h-4 rounded-md"
              style={{backgroundColor: tag.filled ? colors.iconBgLight : 'transparent'}}
            >
              <tag.icon className="w-3 h-3" style={{color: tag.filled ? colors.iconBg : colors.text}} />
            </div>
            <span className="font-medium">{tag.label}</span>
            {tag.filled && tag.value && (
              <>
                <span className="opacity-50">·</span>
                <span className="max-w-20 truncate font-normal opacity-[0.85]">{tag.value}</span>
              </>
            )}
          </div>
        )
      })}

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
          <TooltipContent 
            side="bottom" 
            className="max-w-panel-sm p-3 bg-white border-gray-300 dark:border-gray-600"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <span className={cn("font-semibold text-sm", autocompleteEnabled ? "text-status-success" : "text-status-error")}>
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
              <p className="text-xs text-gray-800 dark:text-gray-200">
                Enquanto você descreve o perfil, a LIA analisa e sugere melhorias:
              </p>
              <ul className="text-xs space-y-1 text-gray-800 dark:text-gray-200">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                  <span>Indica critérios faltantes</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                  <span>Sugere sinônimos e termos relacionados</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                  <span>Alerta sobre buscas muito amplas ou restritivas</span>
                </li>
              </ul>
              <p className="text-micro pt-1 border-t text-gray-500 border-gray-300 dark:border-gray-600">
                {autocompleteEnabled ? 'Clique para desativar' : 'Clique para ativar'}
              </p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Indicador de análise - aparece depois do assistente */}
      {isParsingEntities && (
        <div 
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-200/30"
        >
          <div 
            className="w-3 h-3 border-2 border-t-transparent rounded-full animate-spin"
          />
          <span>Analisando...</span>
        </div>
      )}
    </div>

    {/* Assistente de Busca - Barra de completude e alertas */}
    {value && searchAnalysis && (
      <div className="space-y-2 pt-2 border-t border-gray-300 dark:border-gray-600">
        {/* Barra de completude */}
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
                Qualidade da busca
              </span>
              <span 
                className="text-xs font-bold"
                style={{color: searchAnalysis.completeness_score >= 60 
                    ? "var(--status-success)" 
                    : searchAnalysis.completeness_score >= 40 
                      ? "var(--status-warning)" 
                      : "var(--status-error)"}}
              >
                {searchAnalysis.completeness_score}%
              </span>
            </div>
            <div 
              className="h-1.5 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800"
            >
              <div 
                className="h-full rounded-full transition-all duration-500"
                style={{width: `${searchAnalysis.completeness_score}%`,
                  backgroundColor: searchAnalysis.completeness_score >= 60 
                    ? "var(--status-success)" 
                    : searchAnalysis.completeness_score >= 40 
                      ? "var(--status-warning)" 
                      : "var(--status-error)"}}
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
                className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs"
                style={{backgroundColor: alert.severity === "warning" 
                    ? "var(--status-warning-bg-08)" 
                    : "var(--wedo-cyan-bg-08)",
                  color: 'var(--gray-500)'}}
              >
                {alert.severity === "warning" ? (
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
                ) : (
                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                )}
                <div className="flex-1 min-w-0">
                  <span>{alert.message}</span>
                  {alert.suggestion && (
                    <button
                      onClick={() => {
                        if (alert.action_value) {
                          onChange(value + ", " + alert.action_value)
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

        {/* Sugestões de enriquecimento - Inline scroll se necessário */}
        {Object.keys(searchAnalysis.enrichment_suggestions).length > 0 && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            <span className="text-xs text-gray-950 dark:text-gray-50 font-medium whitespace-nowrap">
              Adicionar:
            </span>
            <div className="flex gap-1.5 flex-nowrap">
              {Object.entries(searchAnalysis.enrichment_suggestions).flatMap(([category, items]) =>
                items.slice(0, 5).map((item) => (
                  <button
                    key={`${category}-${item}`}
                    onClick={() => onChange(value + ", " + item)}
                    className="px-2 py-0.5 rounded-full text-xs font-medium transition-all hover:scale-105 border border-gray-200 whitespace-nowrap flex-shrink-0 bg-[var(--lia-bg-primary)]"
                  >
                    + {item}
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    )}

    {/* Sugestões de busca - Horizontal lado a lado */}
    {!value && (
      <div className="pt-1 w-full flex items-start gap-2">
        <span className="text-xs text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap mt-0.5">
          Sugestões:
        </span>
        <div className="flex items-center gap-2 flex-nowrap overflow-x-auto">
          {SEARCH_SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => onChange(suggestion)}
              className="px-2.5 py-0.5 text-xs text-gray-800 dark:text-gray-200 hover:text-gray-900 dark:hover:text-gray-50 bg-gray-50 hover:bg-gray-100 rounded-full border border-gray-200 transition-all whitespace-nowrap flex-shrink-0"

              title={suggestion}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    )}
  </div>
)}

{/* Similar profile mode - Combined Profile Feature */}
{mode === "similar" && (
  <SSISimilarMode
    similarUrls={similarUrls} updateSimilarUrl={updateSimilarUrl} handleKeyDown={handleKeyDown}
    removeSimilarUrl={removeSimilarUrl} addSimilarUrl={addSimilarUrl} cvFileInputRef={cvFileInputRef}
    handleCvUpload={handleCvUpload} similarCvFiles={similarCvFiles} removeCvFile={removeCvFile}
    isLoading={isLoading || false} hasMultipleSources={hasMultipleSources}
    showCombinedSuggestions={showCombinedSuggestions} analyzeProfiles={analyzeProfiles}
    isAnalyzingProfiles={isAnalyzingProfiles || false} combinedSuggestions={combinedSuggestions}
    removeSuggestion={removeSuggestion} similarSearchPrompt={similarSearchPrompt}
    setSimilarSearchPrompt={setSimilarSearchPrompt} onSearchSourceChange={onSearchSourceChange}
    searchSource={searchSource || "local"} handleSourceChange={handleSourceChange}
    showGlobalSearchOptions={showGlobalSearchOptions} onRequireEmailsChange={onRequireEmailsChange}
    onRequirePhoneNumbersChange={onRequirePhoneNumbersChange} requireEmails={requireEmails || false}
    requirePhoneNumbers={requirePhoneNumbers || false} handleSubmit={handleSubmit}
    canSubmit={canSubmit}
  />
)}


{/* Job Description mode */}
{mode === "jd" && (
  <div className="space-y-3">
    {/* Buscar vaga existente */}
    <div className="relative">
      <div className="flex items-center justify-between mb-1.5">
        <span 
          className="text-xs font-medium"

        >
          Buscar vaga existente
        </span>
        <span className="text-micro text-gray-400">opcional</span>
      </div>

      {selectedVacancy ? (
        <div 
          className="flex items-center justify-between p-2.5 rounded-md border bg-wedo-cyan/[0.08]"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-6 h-6 rounded-full flex items-center justify-center bg-gray-200"
            >
              <Briefcase className="w-3 h-3 text-gray-600" />
            </div>
            <div>
              <p className="text-base-ui font-medium text-gray-800">{selectedVacancy.title}</p>
              {selectedVacancy.job_id && (
                <p className="text-micro text-gray-500">ID: {selectedVacancy.job_id}</p>
              )}
            </div>
          </div>
          <button
            onClick={clearSelectedVacancy}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
          >
            <X className="w-3.5 h-3.5 text-gray-400" />
          </button>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2">
            {isSearchingVacancies ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />
            ) : (
              <Search className="w-3.5 h-3.5 text-gray-400" />
            )}
          </div>
          <input
            type="text"
            value={jdVacancySearch}
            onChange={(e) => setJdVacancySearch(e.target.value)}
            placeholder="Digite o nome ou ID da vaga..."
            className="w-full pl-9 pr-4 py-2.5 text-base-ui rounded-md border focus:outline-none transition-all bg-gray-50 text-gray-950"
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--gray-300)"
              e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--gray-200)"
              e.currentTarget.style.boxShadow = "none"
            }}
          />

          {/* Resultados da busca */}
          {showVacancyResults && jdVacancyResults.length > 0 && (
            <div 
              className="absolute z-50 top-full left-0 right-0 mt-1 rounded-md border overflow-hidden"
              style={{backgroundColor: 'var(--gray-50)'}}
            >
              {jdVacancyResults.map((vacancy) => (
                <button
                  key={vacancy.id}
                  onClick={() => handleSelectVacancy(vacancy)}
                  className="w-full p-2.5 text-left hover:bg-gray-50 transition-colors border-b last:border-b-0 border border-gray-200"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-base-ui font-medium text-gray-800 truncate">{vacancy.title}</p>
                        <Badge 
                          variant="outline" 
                          className="text-micro px-1.5 py-0 h-4 flex-shrink-0"
                          style={{borderColor: vacancy.status === 'Ativa' ? 'var(--status-success)' : 'var(--gray-400)',
                            color: vacancy.status === 'Ativa' ? 'var(--status-success)' : 'var(--gray-500)'}}
                        >
                          {vacancy.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {vacancy.job_id && (
                          <span className="text-micro text-gray-500">ID: {vacancy.job_id}</span>
                        )}
                        <span className="text-micro text-gray-400">{formatDate(vacancy.created_at)}</span>
                      </div>
                      {vacancy.description_preview && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {vacancy.description_preview}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0 mt-0.5" />
                  </div>
                </button>
              ))}
            </div>
          )}

          {showVacancyResults && jdVacancySearch.length >= 2 && jdVacancyResults.length === 0 && !isSearchingVacancies && (
            <div 
              className="absolute z-50 top-full left-0 right-0 mt-1 p-2.5 rounded-md border text-center"
              style={{backgroundColor: 'var(--gray-50)'}}
            >
              <p className="text-base-ui text-gray-500">Nenhuma vaga encontrada</p>
            </div>
          )}
        </div>
      )}
    </div>

    {/* Divisor */}
    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-micro text-gray-400 uppercase tracking-wider">ou</span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>

    {/* Cole a descrição da vaga */}
    <div className="flex items-center justify-between mb-1.5">
      <span 
        className="text-xs font-medium"

      >
        Cole a descrição da vaga
      </span>
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.doc,.docx,.pdf"
        onChange={handleFileUpload}
        className="hidden"
      />
      <Button
        variant="outline"
        size="sm"
        onClick={() => fileInputRef.current?.click()}
        className="text-xs h-6 px-2"

      >
        <Upload className="w-3 h-3 mr-1" />
        Upload
      </Button>
    </div>

    {/* Textarea com ícones de escopo posicionados absolutamente (como Natural e Boolean) */}
    <div className="relative">
      <textarea
        value={jdContent}
        onChange={(e) => {
          setJdContent(e.target.value)
          if (e.target.value !== jdContent) {
            setSelectedVacancy(null)
          }
        }}
        placeholder={getPlaceholder()}
        className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[100px] transition-all border bg-lia-bg-primary"
        style={{color: "var(--gray-950)"}}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "var(--gray-300)"
          e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = "var(--gray-200)"
          e.currentTarget.style.boxShadow = "none"
        }}
        disabled={isLoading}
      />
      {/* Ícones de escopo + botão de busca posicionados absolutamente dentro do textarea */}
      {onSearchSourceChange && (
        <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10">
          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                      searchSource === 'local' 
                        ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                        : "hover:bg-gray-100"
                    , searchSource === 'local' ? "text-wedo-green" : "text-gray-400"
                    )}
                  >
                    <Home className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Seu banco de talentos</p>
                  <p className="text-xs text-gray-300">Gratuito • Local</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {showGlobalSearchOptions && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        searchSource === 'hybrid' 
                          ? "bg-wedo-orange/15 ring-1 ring-wedo-orange" 
                          : "hover:bg-gray-100"
                      , searchSource === 'hybrid' ? "text-wedo-orange" : "text-gray-400"
                      )}
                    >
                      <Zap className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Expanda sua busca</p>
                    <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        searchSource === 'global' 
                          ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                          : "hover:bg-gray-100"
                      , searchSource === 'global' ? "text-gray-950" : "text-gray-400"
                      )}
                    >
                      <Globe className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Alcance global</p>
                    <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}

            {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
            {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
              <>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                        className={cn(
                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                          requireEmails 
                            ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                            : "hover:bg-gray-100"
                        , requireEmails ? "text-wedo-green" : "text-gray-400"
                        )}
                      >
                        <Mail className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Apenas com Email</p>
                      <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                        className={cn(
                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                          requirePhoneNumbers 
                            ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                            : "hover:bg-gray-100"
                        , requirePhoneNumbers ? "text-wedo-green" : "text-gray-400"
                        )}
                      >
                        <Phone className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Apenas com Telefone</p>
                      <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </>
            )}

            {/* Botão de busca com hint */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!canSubmit() || isLoading}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md transition-all",
                      canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                    , canSubmit() ? "text-gray-400" : "text-gray-200"
                    )}
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4" />
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Extrair e Buscar</p>
                  <p className="text-xs text-gray-300">Extrai requisitos e busca candidatos</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          {/* Hint abaixo dos ícones */}
          <span className="text-micro text-gray-400 italic">extrair e buscar</span>
        </div>
      )}
    </div>

    {/* Preview/Edit do Prompt - JD Mode */}
    {jdContent.trim().length > 0 && (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-gray-700" />
            <span className="text-xs font-medium text-gray-800 dark:text-gray-100">
              Preview do prompt de busca
            </span>
          </div>
          <span className="text-micro text-gray-400">editável</span>
        </div>
        <textarea
          value={jdSearchPrompt}
          onChange={(e) => setJdSearchPrompt(e.target.value)}
          placeholder="O prompt será gerado a partir da descrição da vaga..."
          className="w-full resize-none rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 min-h-[60px]"
          style={{border: "1px solid var(--gray-300)",
            backgroundColor: "var(--gray-50)",
            color: 'var(--gray-800)'}}
          rows={2}
        />
      </div>
    )}

    {/* Dica contextual padronizada */}
    <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
        <p className="text-xs text-gray-800 dark:text-gray-200">
          <strong>Dica:</strong> Selecione uma vaga existente ou cole a JD completa para extrair automaticamente requisitos técnicos e comportamentais.
        </p>
      </div>
    </div>
  </div>
)}

{/* Boolean mode */}
{mode === "boolean" && (
  <div className="space-y-3">
    {/* Container principal com textarea e controles posicionados absolutamente (como Natural) */}
    <div className="relative">
      <div className="absolute left-3 top-3">
        <Binary className="w-4 h-4 text-gray-700" />
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={getPlaceholder()}
        className={cn(
          "w-full resize-none rounded-md pl-10 pr-28 py-3 text-sm font-mono focus:outline-none min-h-14 transition-all border",
          booleanError && "ring-2 ring-red-300"
        )}
        style={{borderColor: booleanError ? "var(--status-error)" : "var(--gray-200)",
          backgroundColor: "var(--lia-bg-primary)",
          color: "var(--gray-950)"}}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "var(--gray-300)"
          e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = booleanError ? "var(--status-error)" : "var(--gray-200)"
          e.currentTarget.style.boxShadow = "none"
        }}
        rows={2}
        disabled={isLoading}
      />
      {/* Ícones de escopo posicionados absolutamente dentro do textarea (como Natural) */}
      {onSearchSourceChange && (
        <div className="absolute right-3 bottom-2.5 flex items-center gap-1 flex-shrink-0 z-10">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                    searchSource === 'local' 
                      ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                      : "hover:bg-gray-100"
                  , searchSource === 'local' ? "text-wedo-green" : "text-gray-400"
                  )}
                >
                  <Home className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="!animate-none !duration-0">
                <p className="text-xs font-medium">Seu banco de talentos</p>
                <p className="text-xs text-gray-300">Gratuito • Local</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {showGlobalSearchOptions && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                      searchSource === 'hybrid' 
                        ? "bg-wedo-orange/15 ring-1 ring-wedo-orange" 
                        : "hover:bg-gray-100"
                    , searchSource === 'hybrid' ? "text-wedo-orange" : "text-gray-400"
                    )}
                  >
                    <Zap className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Expanda sua busca</p>
                  <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                    className={cn(
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                      searchSource === 'global' 
                        ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                        : "hover:bg-gray-100"
                    , searchSource === 'global' ? "text-gray-950" : "text-gray-400"
                    )}
                  >
                    <Globe className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Alcance global</p>
                  <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}

          {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
          {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        requireEmails 
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                          : "hover:bg-gray-100"
                      , requireEmails ? "text-wedo-green" : "text-gray-400"
                      )}
                    >
                      <Mail className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                        requirePhoneNumbers 
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green" 
                          : "hover:bg-gray-100"
                      , requirePhoneNumbers ? "text-wedo-green" : "text-gray-400"
                      )}
                    >
                      <Phone className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}

          {/* Botão de busca */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit() || isLoading}
            className={cn(
              "flex items-center justify-center p-1.5 rounded-md transition-all",
              canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
            , canSubmit() ? "text-gray-400" : "text-gray-200"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
          </button>
        </div>
      )}
    </div>

    {booleanError && (
      <div className="flex items-center gap-2 text-xs text-status-error">
        <AlertCircle className="w-3.5 h-3.5" />
        {booleanError}
      </div>
    )}

    <div className="flex flex-wrap gap-2">
      <span className="text-xs text-gray-500 dark:text-gray-400">Operadores:</span>
      {["AND", "OR", "NOT", "(", ")"].map((op) => (
        <button
          key={op}
          onClick={() => onChange(value + (value ? " " : "") + op + " ")}
          className="px-2 py-0.5 rounded-md text-xs font-mono hover:bg-gray-100 transition-colors"
          style={{backgroundColor: 'var(--gray-100)',
            color: 'var(--gray-500)'}}
        >
          {op}
        </button>
      ))}
    </div>

    {/* Dica contextual padronizada */}
    <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
        <p className="text-xs text-gray-800 dark:text-gray-200">
          <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND "São Paulo"
        </p>
      </div>
    </div>
  </div>
)}

{/* Archetypes mode */}
{mode === "archetypes" && (
  <SearchModeArchetypes
    archetypeTab={archetypeTab}
    onArchetypeTabChange={setArchetypeTab}
    archetypeSearch={archetypeSearch}
    onArchetypeSearchChange={setArchetypeSearch}
    isLoadingArchetypes={isLoadingArchetypes}
    filteredArchetypes={filteredArchetypes}
    archetypeVacancies={archetypeVacancies}
    selectedArchetype={selectedArchetype}
    onSelectArchetype={setSelectedArchetype}
    expandedArchetypeId={expandedArchetypeId}
    onExpandedArchetypeIdChange={setExpandedArchetypeId}
    isDeletingArchetype={isDeletingArchetype}
    archetypeSearchPrompt={archetypeSearchPrompt}
    onArchetypeSearchPromptChange={setArchetypeSearchPrompt}
    onOpenEditArchetype={openEditArchetype}
    onDeleteArchetype={deleteArchetype}
    buildArchetypePrompt={buildArchetypePrompt}
    onSubmit={handleSubmit}
    isLoading={isLoading}
    searchSource={searchSource}
    onSearchSourceChange={onSearchSourceChange}
    onHandleSourceChange={handleSourceChange}
    showGlobalSearchOptions={showGlobalSearchOptions}
    requireEmails={requireEmails}
    onRequireEmailsChange={onRequireEmailsChange}
    requirePhoneNumbers={requirePhoneNumbers}
    onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
    archetypeCreateMode={archetypeCreateMode}
    onArchetypeCreateModeChange={setArchetypeCreateMode}
    jobSearchQuery={jobSearchQuery}
    onJobSearchQueryChange={setJobSearchQuery}
    isSearchingJobs={isSearchingJobs}
    jobSearchResults={jobSearchResults}
    onOpenArchetypeFromJob={openArchetypeFromJob}
    archetypeDescription={archetypeDescription}
    onArchetypeDescriptionChange={setArchetypeDescription}
    isCreatingArchetype={isCreatingArchetype}
    onCreateArchetypeFromDescription={createArchetypeFromDescription}
    onSearchJobsForArchetype={searchJobsForArchetype}
  />
)}
    </>
  )
}
