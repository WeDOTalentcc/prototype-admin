"use client"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { AdvancedFiltersModal, type SearchFilters } from "@/components/search/advanced-filters-modal"
import {
  AlertTriangle, Brain, Building2, Check, CheckCircle2, Code, FileText,
  Filter, Globe, Home, Info, Lightbulb, Linkedin, Loader2, Mail, MapPin,
  Pencil, Phone, Plus, Search, TagIcon, Target, Trash2, TrendingUp, Upload, Wand2, X, Zap
} from "lucide-react"
import { useExpandableAIPromptCore } from "./useExpandableAIPromptCore"

type EAPTabContentProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'activeSearchTab' | 'naturalSearchValue' | 'setNaturalSearchValue' | 'searchTags' |
  'suggestions' | 'advancedFilters' | 'setAdvancedFilters' | 'analyzeProfiles' |
  'archetypeSearchFilter' | 'archetypes' | 'autocompleteEnabled' | 'autocompleteSuggestions' |
  'booleanSearchValue' | 'canSaveAsArchetype' | 'combinedSuggestions' |
  'createArchetypeFromActiveSearch' | 'createArchetypeFromDescription' |
  'cvFileInputRef' | 'executeSearchWithCriteria' | 'extractionTimeoutRef' |
  'fetchAutocomplete' | 'filteredArchetypes' | 'getTagColors' |
  'handleAcceptEnhancement' | 'handleAutocompleteKeyDown' | 'handleCvUpload' |
  'handleDismissEnhancement' | 'handlePremiumAutocompleteSelect' | 'handleSourceChange' |
  'hasMultipleSources' | 'hasParsedEntities' | 'isAnalyzingProfiles' |
  'isCreatingArchetype' | 'isCreatingFromSearch' | 'isDeletingArchetype' |
  'isEnhancingPrompt' | 'isParsingEntities' | 'jobDescriptionText' |
  'newArchetypeDescription' | 'onClose' | 'onCommand' |
  'openDeleteArchetypeDialog' | 'openEditArchetype' | 'parseEntitiesFromQuery' |
  'parsedEntities' | 'promptEnhancement' | 'removeCvFile' | 'removeSimilarUrl' |
  'removeSuggestion' | 'requireEmails' | 'requirePhoneNumbers' | 'searchAnalysis' |
  'searchSource' | 'selectedAutocompleteIndex' | 'setArchetypeSearchFilter' |
  'setAutocompleteEnabled' | 'setBooleanSearchValue' | 'setJobDescriptionText' |
  'setNewArchetypeDescription' | 'setRequireEmails' | 'setRequirePhoneNumbers' |
  'setSearchSource' | 'setSelectedArquetipo' | 'setShowAdvancedFiltersModal' |
  'setShowAutocomplete' | 'setShowPremiumAutocomplete' | 'setShowSaveArchetypeModal' |
  'showAutocomplete' | 'showCombinedSuggestions' | 'showGlobalSearchOptions' |
  'showPremiumAutocomplete' | 'similarCvFiles' | 'similarUrls' | 'updateSimilarUrl' |
  'addSimilarUrl'
>

export function EAPTabContent(props: EAPTabContentProps) {
  const {
    activeSearchTab, naturalSearchValue, setNaturalSearchValue, searchTags,
    suggestions, advancedFilters, setAdvancedFilters, analyzeProfiles,
    archetypeSearchFilter, archetypes, autocompleteEnabled, autocompleteSuggestions,
    booleanSearchValue, canSaveAsArchetype, combinedSuggestions,
    createArchetypeFromActiveSearch, createArchetypeFromDescription,
    cvFileInputRef, executeSearchWithCriteria, extractionTimeoutRef,
    fetchAutocomplete, filteredArchetypes, getTagColors,
    handleAcceptEnhancement, handleAutocompleteKeyDown, handleCvUpload,
    handleDismissEnhancement, handlePremiumAutocompleteSelect, handleSourceChange,
    hasMultipleSources, hasParsedEntities, isAnalyzingProfiles,
    isCreatingArchetype, isCreatingFromSearch, isDeletingArchetype,
    isEnhancingPrompt, isParsingEntities, jobDescriptionText,
    newArchetypeDescription, onClose, onCommand,
    openDeleteArchetypeDialog, openEditArchetype, parseEntitiesFromQuery,
    parsedEntities, promptEnhancement, removeCvFile, removeSimilarUrl,
    removeSuggestion, requireEmails, requirePhoneNumbers, searchAnalysis,
    searchSource, selectedAutocompleteIndex, setArchetypeSearchFilter,
    setAutocompleteEnabled, setBooleanSearchValue, setJobDescriptionText,
    setNewArchetypeDescription, setRequireEmails, setRequirePhoneNumbers,
    setSearchSource, setSelectedArquetipo, setShowAdvancedFiltersModal,
    setShowAutocomplete, setShowPremiumAutocomplete, setShowSaveArchetypeModal,
    showAutocomplete, showCombinedSuggestions, showGlobalSearchOptions,
    showPremiumAutocomplete, similarCvFiles, similarUrls, updateSimilarUrl,
    addSimilarUrl
  } = props

  return (
    <>
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
                const query = arch.query || arch.criteria?.query || arch.description || ""
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
                  {arch.emoji || "🎯"}
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
    </>
  )
}
