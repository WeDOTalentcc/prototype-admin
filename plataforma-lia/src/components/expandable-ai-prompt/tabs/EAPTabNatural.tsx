"use client"

import React from 'react'
import { PremiumAutocomplete } from "@/components/ui/premium-autocomplete"
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  AlertTriangle, Brain, Check, CheckCircle2, Globe, Home, Info,
  Loader2, Mail, Phone, Search, Target, TrendingUp, Wand2, X, Zap
} from "lucide-react"
import { useExpandableAIPromptCore } from "../useExpandableAIPromptCore"

type EAPTabNaturalProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'naturalSearchValue' | 'setNaturalSearchValue' | 'searchTags' |
  'advancedFilters' | 'autocompleteEnabled' | 'autocompleteSuggestions' |
  'canSaveAsArchetype' | 'executeSearchWithCriteria' | 'extractionTimeoutRef' |
  'fetchAutocomplete' | 'getTagColors' |
  'handleAcceptEnhancement' | 'handleAutocompleteKeyDown' |
  'handleDismissEnhancement' | 'handlePremiumAutocompleteSelect' | 'handleSourceChange' |
  'isEnhancingPrompt' | 'isParsingEntities' |
  'parseEntitiesFromQuery' | 'promptEnhancement' | 'requireEmails' | 'requirePhoneNumbers' |
  'searchAnalysis' | 'searchSource' | 'selectedAutocompleteIndex' |
  'setAutocompleteEnabled' | 'setRequireEmails' | 'setRequirePhoneNumbers' |
  'setSearchSource' | 'setShowPremiumAutocomplete' | 'setShowSaveArchetypeModal' |
  'setShowAutocomplete' | 'showAutocomplete' | 'showGlobalSearchOptions' |
  'showPremiumAutocomplete'
>

export const EAPTabNatural = React.memo(function EAPTabNatural(props: EAPTabNaturalProps) {
  const {
    naturalSearchValue, setNaturalSearchValue, searchTags,
    autocompleteEnabled, autocompleteSuggestions,
    canSaveAsArchetype, executeSearchWithCriteria, extractionTimeoutRef,
    fetchAutocomplete, getTagColors,
    handleAcceptEnhancement, handleAutocompleteKeyDown,
    handleDismissEnhancement, handlePremiumAutocompleteSelect, handleSourceChange,
    isEnhancingPrompt, isParsingEntities,
    parseEntitiesFromQuery, promptEnhancement, requireEmails, requirePhoneNumbers,
    searchAnalysis, searchSource, selectedAutocompleteIndex,
    setAutocompleteEnabled, setRequireEmails, setRequirePhoneNumbers,
    setSearchSource, setShowPremiumAutocomplete, setShowSaveArchetypeModal,
    setShowAutocomplete, showAutocomplete, showGlobalSearchOptions,
    showPremiumAutocomplete,
  } = props

  return (
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
          className="border border-input bg-lia-bg-primary rounded-lg text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-full px-4 py-2.5 text-sm pr-44"
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
                  className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                    searchSource === 'local'
                      ? 'bg-lia-interactive-active'
                      : 'hover:bg-lia-bg-tertiary'
                  }`}
                >
                  <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-lia-text-secondary' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Base Local</p>
                <p className="text-micro text-lia-text-secondary">Gratuito</p>
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
                    <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-lia-text-secondary' : 'lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                  <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">1 cred + $0.01 Apify/cand</p>
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
                    <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-lia-text-secondary' : 'lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs font-medium">Base Global</p>
                  <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">1 cred + $0.01 Apify/cand</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}

          {/* Separador */}
          <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />

          {/* Contato: Email / Telefone */}
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
                <p className="text-micro text-lia-text-secondary">{requireEmails ? 'Ativo' : '$0.01/cand se ativo'}</p>
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
                <p className="text-micro text-lia-text-secondary">{requirePhoneNumbers ? 'Ativo' : '$0.01/cand se ativo'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Separador */}
          <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />

          {/* Botão de Buscar */}
          <button
            className="w-7 h-7 lia-btn-primary flex items-center justify-center"
            onClick={() => executeSearchWithCriteria()}
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </div>

        

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
          className="mt-2 p-3 rounded-xl border transition-colors motion-reduce:transition-none bg-lia-interactive-active/20"
        >
          <div className="flex items-start gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <Wand2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
            <div className="flex-1 min-w-0" role="status" aria-live="polite" aria-label="Carregando...">
              <div className="flex items-center gap-1.5 mb-1" role="status" aria-live="polite" aria-label="Carregando...">
                <span className="text-xs font-medium text-lia-text-secondary">Sugestão da IA</span>
                {isEnhancingPrompt && (
                  <div className="w-3 h-3 border-2 border-lia-btn-primary-bg border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                )}
              </div>
              <p className="text-sm text-lia-text-primary mb-2">{promptEnhancement.enhanced_query}</p>
              {promptEnhancement.explanation && (
                <p className="text-xs text-lia-text-secondary mb-2">{promptEnhancement.explanation}</p>
              )}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleAcceptEnhancement}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg text-lia-btn-primary-text"
                >
                  <Check className="w-3 h-3" />
                  Usar sugestão
                </button>
                <button
                  onClick={handleDismissEnhancement}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-medium text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
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
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium bg-[var(--wedo-cyan-bg-08)] border border-[var(--wedo-cyan-bg-20)]"
          >
            <Home className="w-3 h-3" />
            <span>Base Local</span>
          </div>
          <span className="text-xs text-lia-text-secondary">
            Busca apenas na sua base de dados
          </span>
        </div>
      )}

      {showAutocomplete && autocompleteSuggestions.length > 0 && (
        <div className="mt-2 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-48 overflow-y-auto shadow-md" data-testid="autocomplete-dropdown">
          {autocompleteSuggestions.map((suggestion, index) => (
            <button
              key={`sug-${index}`}
              data-testid="autocomplete-item"
              role="option"
              aria-selected={selectedAutocompleteIndex === index}
              onClick={() => {
                setNaturalSearchValue(prev => {
                  const words = prev.split(' ')
                  words.pop()
                  const insertValue = suggestion.insert_text || suggestion.text
                  return [...words, insertValue].join(' ') + ' '
                })
                setShowAutocomplete(false)
              }}
              className={`w-full px-3 py-2 text-left text-xs flex items-center justify-between transition-colors motion-reduce:transition-none ${
                selectedAutocompleteIndex === index
                  ? 'bg-lia-bg-tertiary'
                  : 'hover:bg-lia-bg-secondary'
              }`}
            >
              <span>{suggestion.text}</span>
              <span className="text-micro text-lia-text-secondary">{suggestion.category}</span>
            </button>
          ))}
          <div className="px-3 py-1.5 text-micro flex items-center justify-between text-lia-text-secondary">
            <span>Use ↑↓ para navegar, Tab para selecionar</span>
            <span>Esc para fechar</span>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-1.5 mt-2">
        {searchTags.map((tag) => {
          const colors = getTagColors(tag.key, tag.filled)
          const TagIcon = tag.icon

          return (
            <div
              key={tag.key}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none"
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
                  <span className="opacity-50">·</span>
                  <span className="max-w-20 truncate font-normal opacity-85">{tag.value}</span>
                </>
              )}
            </div>
          )
        })}

        {isParsingEntities && (
          <div className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-lia-text-secondary" role="status" aria-live="polite" aria-label="Carregando...">
            <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
            Analisando...
          </div>
        )}

        {/* Botão Assistente de Busca */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setAutocompleteEnabled(!autocompleteEnabled)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] hover:opacity-90",
                  autocompleteEnabled
                    ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                    : "bg-lia-bg-tertiary text-lia-text-secondary"
                )}
              >
                <Brain className={`w-3.5 h-3.5 ${autocompleteEnabled ? 'text-wedo-cyan' : 'lia-text-secondary'}`} />
                <span className="font-medium text-xs">
                  Assistente de Busca
                </span>
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-panel-sm p-3 border-lia-border-default dark:border-lia-border-default">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className={`font-semibold text-xs ${autocompleteEnabled ? 'text-status-success' : 'text-status-error'}`}>
                      {autocompleteEnabled ? 'Ativado' : 'Desativado'}
                    </span>
                  </div>
                  <span className={`text-micro px-2 py-0.5 rounded-full ${autocompleteEnabled ? 'bg-status-success-bg text-status-success' : 'bg-status-error-bg text-status-error'}`}>
                    {autocompleteEnabled ? 'ON' : 'OFF'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-xs text-lia-text-primary">
                    Assistente de Busca Inteligente
                  </span>
                </div>
                <p className="text-micro text-lia-text-tertiary">
                  Enquanto você descreve o perfil, a IA analisa e sugere melhorias:
                </p>
                <ul className="text-micro space-y-1 text-lia-text-tertiary">
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                    <span>Indica critérios faltantes</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                    <span>Sugere sinônimos e termos relacionados</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                    <span>Alerta sobre buscas muito amplas ou restritivas</span>
                  </li>
                </ul>
                <p className="text-micro pt-1 border-t text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default">
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
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium transition-[width,height] hover:opacity-90 bg-lia-interactive-active/30"
                >
                  <Target className="w-3 h-3" />
                  <span className="font-medium">Salvar Arquétipo</span>
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="!animate-none !duration-0">
                <p className="text-xs font-medium">Salvar busca como arquétipo</p>
                <p className="text-xs text-lia-text-tertiary">Reutilize esta busca no futuro</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {naturalSearchValue && searchAnalysis && (
        <div className="space-y-2 pt-2 mt-2 border-t border-lia-border-default dark:border-lia-border-default">
          {/* Barra de completude */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-lia-text-tertiary">
                  Qualidade da busca
                </span>
                <span
                  className={`text-xs font-bold ${searchAnalysis.completeness_score >= 60 ? 'text-status-success' : searchAnalysis.completeness_score >= 40 ? 'text-status-warning' : 'text-status-error'}`}
                >
                  {searchAnalysis.completeness_score}%
                </span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                <div
                  className={`h-full rounded-full transition-[width,height] duration-500 ${searchAnalysis.completeness_score >= 60 ? 'bg-status-success' : searchAnalysis.completeness_score >= 40 ? 'bg-status-warning' : 'bg-status-error'}`}
                  style={{width: `${searchAnalysis.completeness_score}%`}}
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
                  key={`alert-${index}`}
                  className={`flex items-start gap-2 px-2.5 py-2 rounded-full text-xs text-lia-text-tertiary ${alert.severity === 'warning' ? 'bg-status-warning-bg-08' : 'bg-wedo-cyan-bg-08'}`}
                >
                  {alert.severity === 'warning' ? (
                    <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
                  ) : (
                    <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
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
                        className="ml-1 font-medium hover:underline text-lia-text-secondary"
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

      {/* Sugestões */}
      <div className="mt-3">
        <p className="text-xs text-lia-text-primary mb-1.5">Sugestões:</p>
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
              className="px-2.5 py-1.5 text-xs rounded-full border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-medium hover:text-lia-text-primary transition-colors motion-reduce:transition-none text-left"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
})
EAPTabNatural.displayName = 'EAPTabNatural'
