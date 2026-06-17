'use client'

import React from 'react'
import { getPercentageScoreVar } from '@/lib/score-utils'
import { cn } from "@/lib/utils"
import { textStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import {
  AlertTriangle, Award, Binary, Brain, Briefcase, Building2,
  CheckCircle2, Code, DollarSign, FileText, Globe,
  GraduationCap, Home, Info, MapPin,
  Phone, Mail, Search, Star, Target, TrendingUp,
  Users, Wand2, X, Zap
} from "lucide-react"
import type { useSmartSearchCore } from "../hooks/useSmartSearchCore"
import { useSearchSuggestions } from "../hooks/useSearchSuggestions"
import { usePersonaName } from "@/hooks/company/usePersonaName"

const SEARCH_SUGGESTIONS = [
  'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
  'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis'
]

type CoreProps = ReturnType<typeof useSmartSearchCore>

interface SSIModeNaturalProps {
  value: CoreProps['value']
  onChange: CoreProps['onChange']
  handleKeyDown: CoreProps['handleKeyDown']
  handleSubmit: CoreProps['handleSubmit']
  canSubmit: CoreProps['canSubmit']
  isLoading: CoreProps['isLoading']
  getPlaceholder: CoreProps['getPlaceholder']
  textareaRef: CoreProps['textareaRef']
  ghostOverlayRef: CoreProps['ghostOverlayRef']
  ghostTextInfo: CoreProps['ghostTextInfo']
  ghostTextSuffix: CoreProps['ghostTextSuffix']
  handleAcceptEnhancement: CoreProps['handleAcceptEnhancement']
  handleDismissEnhancement: CoreProps['handleDismissEnhancement']
  showAutocomplete: CoreProps['showAutocomplete']
  setShowAutocomplete: CoreProps['setShowAutocomplete']
  autocompleteItems: CoreProps['autocompleteItems']
  setAutocompleteItems: CoreProps['setAutocompleteItems']
  autocompleteEnabled: CoreProps['autocompleteEnabled']
  setAutocompleteEnabled: CoreProps['setAutocompleteEnabled']
  selectedAutocompleteIndex: CoreProps['selectedAutocompleteIndex']
  setSelectedAutocompleteIndex: CoreProps['setSelectedAutocompleteIndex']
  handleAutocompleteSelect: CoreProps['handleAutocompleteSelect']
  tags: CoreProps['tags']
  isParsingEntities: CoreProps['isParsingEntities']
  searchAnalysis: CoreProps['searchAnalysis']
  searchSource: CoreProps['searchSource']
  onSearchSourceChange: CoreProps['onSearchSourceChange']
  handleSourceChange: CoreProps['handleSourceChange']
  showGlobalSearchOptions: CoreProps['showGlobalSearchOptions']
  requireEmails: CoreProps['requireEmails']
  onRequireEmailsChange: CoreProps['onRequireEmailsChange']
  requirePhoneNumbers: CoreProps['requirePhoneNumbers']
  onRequirePhoneNumbersChange: CoreProps['onRequirePhoneNumbersChange']
}

export const SSIModeNatural = React.memo(function SSIModeNatural(props: SSIModeNaturalProps) {
  const {
    value, onChange, handleKeyDown, handleSubmit, canSubmit, isLoading, getPlaceholder,
    textareaRef, ghostOverlayRef, ghostTextInfo, ghostTextSuffix,
    handleAcceptEnhancement, handleDismissEnhancement,
    showAutocomplete, setShowAutocomplete, autocompleteItems, setAutocompleteItems,
    autocompleteEnabled, setAutocompleteEnabled,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex, handleAutocompleteSelect,
    tags, isParsingEntities, searchAnalysis,
    searchSource, onSearchSourceChange, handleSourceChange, showGlobalSearchOptions,
    requireEmails, onRequireEmailsChange, requirePhoneNumbers, onRequirePhoneNumbersChange,
  } = props

  const { suggestions: dynamicSuggestions } = useSearchSuggestions()
  const personaName = usePersonaName()
  const displaySuggestions = dynamicSuggestions.length > 0 ? dynamicSuggestions : SEARCH_SUGGESTIONS

  return (
    <div className="space-y-3">
      <div className="relative">
        {/* Ghost Text Overlay - positioned over textarea */}
        {ghostTextSuffix && !showAutocomplete && (
          <div
            ref={ghostOverlayRef}
            className="absolute inset-0 pointer-events-none rounded-xl px-4 py-3 pr-28 text-xs min-h-14 overflow-hidden whitespace-pre-wrap break-words z-[1]"
            aria-hidden="true"
          >
            <span className="text-transparent">{value}</span>
            <span className="text-lia-text-tertiary">{ghostTextSuffix}</span>
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
          className={cn("w-full resize-none rounded-md px-4 py-3 pr-28 text-xs focus:outline-none min-h-14 transition-colors motion-reduce:transition-none border relative text-lia-text-primary caret-lia-text-primary z-[2]", ghostTextSuffix && !showAutocomplete ? "bg-transparent" : "bg-lia-bg-primary")}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--lia-border-default)"
            e.currentTarget.style.boxShadow = "0 0 0 2px rgba(0, 0, 0, 0.06)"
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--lia-border-subtle)"
            e.currentTarget.style.boxShadow = "none"
            setTimeout(() => setShowAutocomplete(false), 200)
          }}
          rows={2}
          disabled={isLoading}
        />
        {/* Seletor de Origem de Busca + Filtros de Contato - Próximo ao search */}
        {onSearchSourceChange && (
          <div className="absolute right-12 bottom-2.5 flex items-center gap-0.5 flex-shrink-0 z-10">
            {/* Source selectors: Local, Hybrid, Global */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                    className={cn(
                      "flex items-center justify-center p-1 rounded-md text-xs transition-colors",
                      searchSource === 'local'
                        ? "bg-wedo-green/15 text-wedo-green-text"
                        : "text-lia-border-default hover:text-lia-text-tertiary"
                    )}
                  >
                    <Home className="w-3.5 h-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Seu banco de talentos</p>
                  <p className="text-xs text-lia-text-muted">Gratuito • Local</p>
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
                        "flex items-center justify-center p-1 rounded-md text-xs transition-colors",
                        searchSource === 'hybrid'
                          ? "bg-wedo-orange/15 text-wedo-orange-text"
                          : "text-lia-border-default hover:text-lia-text-tertiary"
                      )}
                    >
                      <Zap className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Expanda sua busca</p>
                    <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">Local + Global • 1 cred + $0.01 Apify/cand</p>
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
                        "flex items-center justify-center p-1 rounded-md text-xs transition-colors",
                        searchSource === 'global'
                          ? "bg-wedo-cyan/15 text-lia-text-primary"
                          : "text-lia-border-default hover:text-lia-text-tertiary"
                      )}
                    >
                      <Globe className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Alcance global</p>
                    <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">800M+ candidatos • 1 cred + $0.01 Apify/cand</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}

            {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
            {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
              <>
                <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                        className={cn(
                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                          requireEmails
                            ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                            : "hover:bg-lia-bg-tertiary"
                        , requireEmails ? "text-wedo-green-text" : "text-lia-text-tertiary"
                        )}
                      >
                        <Mail className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Apenas com Email</p>
                      <p className="text-xs text-lia-text-muted">{requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
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
                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                          requirePhoneNumbers
                            ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                            : "hover:bg-lia-bg-tertiary"
                        , requirePhoneNumbers ? "text-wedo-green-text" : "text-lia-text-tertiary"
                        )}
                      >
                        <Phone className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Apenas com Telefone</p>
                      <p className="text-xs text-lia-text-muted">{requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </>
            )}

            {/* Separador visual */}
            <div className="w-px h-5 bg-lia-interactive-active mx-1" />

            {/* Botão Microfone */}
            <AudioRecordButton
              onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
              className="p-1.5 rounded-xl hover:bg-lia-bg-tertiary"
            />
          </div>
        )}

        {/* Microfone quando não há seletor de origem */}
        {!onSearchSourceChange && (
          <div className="absolute right-12 bottom-2.5 flex items-center z-10">
            <AudioRecordButton
              onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
              className="p-1.5 rounded-xl hover:bg-lia-bg-tertiary"
            />
          </div>
        )}

        <Button
          onClick={handleSubmit}
          disabled={!canSubmit()}
          size="sm"
          className={cn("absolute right-2.5 bottom-2.5 h-8 w-8 p-0 rounded-md transition-transform motion-reduce:transition-none hover:scale-105 z-10", canSubmit() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-bg-tertiary text-lia-text-secondary")}
        >
          <Search className="w-4 h-4" />
        </Button>

        {/* Ghost Text Tab hint */}
        {ghostTextSuffix && !showAutocomplete && (
          <div
            className="absolute bottom-2 right-3 flex items-center gap-1 text-micro text-lia-text-secondary data-[state=open]:animate-in data-[state=open]:fade-in-0 animate-in fade-in-0 duration-150"
          >
            <kbd className="px-1.5 py-0.5 rounded bg-lia-bg-tertiary border border-lia-border-subtle text-micro font-mono text-lia-text-primary">Tab</kbd>
            <span>para aceitar</span>
          </div>
        )}

      </div>

      {/* Fallback Suggestion Card - shown BELOW the textarea container when enhanced query doesn't start with user text */}
      {ghostTextInfo.showFallbackCard && ghostTextInfo.fullEnhancement && !showAutocomplete && (
        <div
          className="rounded-xl border px-3 py-2 flex items-center gap-2 bg-lia-interactive-active/20"
        >
          <Wand2 className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-primary" />
          <div className="flex-1 min-w-0">
            <span className={textStyles.description}>Sugestão: </span>
            <span className="text-xs text-lia-text-primary">{ghostTextInfo.fullEnhancement}</span>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={handleAcceptEnhancement}
              className="flex items-center gap-1 px-2 py-1 rounded-full text-micro font-medium hover:bg-wedo-cyan/15 transition-colors motion-reduce:transition-none text-lia-text-primary"
            >
              <kbd className="px-1 py-0.5 rounded-full bg-lia-bg-tertiary text-micro font-mono">Tab</kbd>
              <span>Aceitar</span>
            </button>
            <button
              onClick={handleDismissEnhancement}
              className="flex items-center justify-center w-5 h-5 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-tertiary"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      {showAutocomplete && autocompleteItems.length > 0 && (
        <div
          className="rounded-xl border border-lia-border-subtle flex flex-col gap-0 max-h-52 overflow-hidden bg-[var(--lia-bg-primary)] shadow-md"
          data-testid="autocomplete-dropdown"
        >
          <div className="flex items-center justify-between px-3 py-1.5">
            <div className="flex items-center gap-2">
              <Brain className="w-3 h-3 text-wedo-cyan" />
              <span className="text-micro font-medium text-lia-text-secondary">Sugestões</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutocompleteEnabled(false)}
                className="text-micro text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                title="Desativar sugestões"
              >
                Desativar
              </button>
              <button
                onClick={() => {
                  setShowAutocomplete(false)
                  setAutocompleteItems([])
                }}
                className="p-0.5 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                title="Fechar lista"
              >
                <X className="w-3 h-3 text-lia-text-tertiary" />
              </button>
            </div>
          </div>
          <div className="py-1 overflow-y-auto max-h-40">
            {autocompleteItems.slice(0, 6).map((item, index) => {
              const IconComponent =
                item.icon === "code" ? Code :
                item.icon === "briefcase" ? Briefcase :
                item.icon === "map-pin" ? MapPin :
                item.icon === "map" ? MapPin :
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
                  return { bg: 'var(--lia-bg-secondary)', accent: 'var(--lia-text-secondary)' }
                if (cat.includes('local') || cat.includes('cidade') || cat.includes('região'))
                  return { bg: 'var(--lia-bg-tertiary)', accent: 'var(--wedo-purple)' }
                if (cat.includes('skill') || cat.includes('tecnologia') || cat.includes('ferramenta'))
                  return { bg: 'var(--lia-bg-secondary)', accent: 'var(--wedo-green)' }
                if (cat.includes('experiência') || cat.includes('senioridade') || cat.includes('anos'))
                  return { bg: 'var(--status-warning-bg)', accent: 'var(--wedo-orange)' }
                if (cat.includes('setor') || cat.includes('indústria') || cat.includes('área'))
                  return { bg: 'var(--lia-bg-tertiary)', accent: 'var(--lia-text-secondary)' }
                return { bg: 'var(--lia-bg-secondary)', accent: 'var(--lia-text-secondary)' }
              }
              const catColor = getCategoryColor(item.category)
              const isSelected = selectedAutocompleteIndex === index

              return (
                <button
                  key={`${item.text}-${index}`}
                  data-testid="autocomplete-item"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => handleAutocompleteSelect(item)}
                  onMouseEnter={() => setSelectedAutocompleteIndex(index)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 text-left transition-colors w-full",
                    isSelected ? "bg-lia-bg-secondary" : "hover:bg-lia-bg-secondary"
                  )}
                >
                  <IconComponent
                    className="w-3.5 h-3.5 flex-shrink-0"
                    style={{color: catColor.accent}}
                  />
                  <span
                    className="text-xs font-medium flex-1 truncate text-lia-text-primary"
                  >
                    {item.text}
                  </span>
                  <span
                    className="text-micro text-lia-text-secondary flex-shrink-0"
                  >
                    {item.category}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-1.5">
        {tags.map((tag) => {
          const getTagColors = (key: string, filled: boolean) => {
            if (!filled) return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-primary)', iconBg: 'var(--lia-text-tertiary)', iconBgLight: 'var(--lia-bg-secondary)' }
            switch (key) {
              case 'job_title':
                return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-secondary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
              case 'location':
                return { bg: 'var(--lia-bg-tertiary)', text: 'var(--wedo-purple)', iconBg: 'var(--wedo-purple)', iconBgLight: 'var(--wedo-purple-bg-10)' }
              case 'skills':
                return { bg: 'var(--lia-bg-secondary)', text: 'var(--status-success)', iconBg: 'var(--wedo-green)', iconBgLight: 'var(--wedo-green-bg-10)' }
              case 'years_experience':
                return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', iconBg: 'var(--wedo-orange)', iconBgLight: 'var(--wedo-orange-bg-15)' }
              case 'industry':
                return { bg: 'var(--lia-bg-tertiary)', text: 'var(--lia-text-primary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
              default:
                return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-secondary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
            }
          }
          const colors = getTagColors(tag.key, tag.filled)

          return (
            <div
              key={tag.key}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors border border-lia-border-subtle"
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
                  <span className="max-w-20 truncate font-normal opacity-85">{tag.value}</span>
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
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border hover:opacity-90",
                  autocompleteEnabled
                    ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg text-lia-btn-primary-text"
                    : "border-lia-border-subtle bg-transparent text-lia-text-secondary"
                )}
              >
                <Brain className={`w-3.5 h-3.5 ${autocompleteEnabled ? 'text-wedo-cyan' : 'text-lia-text-tertiary'}`} />
                <span className="font-medium text-xs">
                  Assistente de Busca
                </span>
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="bottom"
              className="max-w-panel-sm p-3 bg-lia-bg-primary border-lia-border-default dark:border-lia-border-default"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className={cn("font-semibold text-xs", autocompleteEnabled ? "text-status-success" : "text-status-error")}>
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
                <p className="text-micro text-lia-text-primary">
                  Enquanto você descreve o perfil, {`${personaName} analisa e sugere melhorias:`}
                </p>
                <ul className="text-micro space-y-1 text-lia-text-primary">
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                    <span>Indica critérios faltantes</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                    <span>Sugere sinônimos e termos relacionados</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-2.5 h-2.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                    <span>Alerta sobre buscas muito amplas ou restritivas</span>
                  </li>
                </ul>
                <p className="text-micro pt-1 border-t text-lia-text-secondary border-lia-border-default dark:border-lia-border-default">
                  {autocompleteEnabled ? 'Clique para desativar' : 'Clique para ativar'}
                </p>
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Indicador de análise - aparece depois do assistente */}
        {isParsingEntities && (
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-interactive-active/30"
          >
            <div
              className="w-3 h-3 border-2 border-t-transparent rounded-full animate-spin motion-reduce:animate-none"
            />
            <span>Analisando...</span>
          </div>
        )}
      </div>

      {value && searchAnalysis && (
        <div className="space-y-2 pt-2 border-t border-lia-border-default dark:border-lia-border-default">
          {/* Barra de completude */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-lia-text-primary">
                  Qualidade da busca
                </span>
                <span
                  className="text-xs font-bold"
                  style={{color: getPercentageScoreVar(searchAnalysis.completeness_score)}}
                >
                  {searchAnalysis.completeness_score}%
                </span>
              </div>
              <div
                className="h-1.5 rounded-full overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
              >
                <div
                  className="h-full rounded-full transition-[width,height] duration-500"
                  style={{width: `${searchAnalysis.completeness_score}%`,
                    backgroundColor: getPercentageScoreVar(searchAnalysis.completeness_score)}}
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
                  className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs"
                  style={{backgroundColor: alert.severity === "warning"
                      ? "var(--status-warning-bg-08)"
                      : "var(--wedo-cyan-bg-08)",
                    color: 'var(--lia-text-secondary)'}}
                >
                  {alert.severity === "warning" ? (
                    <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
                  ) : (
                    <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
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
                        className="ml-1 font-medium hover:underline text-lia-text-primary"
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
              <span className="text-xs text-lia-text-primary font-medium whitespace-nowrap">
                Adicionar:
              </span>
              <div className="flex gap-1.5 flex-nowrap">
                {Object.entries(searchAnalysis.enrichment_suggestions).flatMap(([category, items]) =>
                  items.slice(0, 5).map((item) => (
                    <button
                      key={`${category}-${item}`}
                      onClick={() => onChange(value + ", " + item)}
                      className="px-2 py-0.5 rounded-lg text-xs font-medium transition-colors hover:scale-105 border border-lia-border-subtle whitespace-nowrap flex-shrink-0 bg-[var(--lia-bg-primary)]"
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
          <span className="text-xs text-lia-text-primary font-medium whitespace-nowrap mt-0.5">
            Sugestões:
          </span>
          <div className="flex items-center gap-2 flex-nowrap overflow-x-auto">
            {displaySuggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => onChange(suggestion)}
                className="px-2.5 py-0.5 text-xs text-lia-text-primary hover:text-lia-text-primary bg-lia-bg-secondary hover:bg-lia-bg-tertiary rounded-lg border border-lia-border-subtle transition-colors whitespace-nowrap flex-shrink-0"
                title={suggestion}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
})
SSIModeNatural.displayName = 'SSIModeNatural'
