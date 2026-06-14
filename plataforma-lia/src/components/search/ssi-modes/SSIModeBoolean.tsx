'use client'

import React from 'react'
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  AlertCircle, Binary, Globe, Home, Lightbulb, Loader2, Mail, Phone, Search, Zap
} from "lucide-react"
import type { useSmartSearchCore } from "../hooks/useSmartSearchCore"

type CoreProps = ReturnType<typeof useSmartSearchCore>

interface SSIModeBooleanProps {
  value: CoreProps['value']
  onChange: CoreProps['onChange']
  handleKeyDown: CoreProps['handleKeyDown']
  handleSubmit: CoreProps['handleSubmit']
  canSubmit: CoreProps['canSubmit']
  isLoading: CoreProps['isLoading']
  getPlaceholder: CoreProps['getPlaceholder']
  textareaRef: CoreProps['textareaRef']
  booleanError: CoreProps['booleanError']
  searchSource: CoreProps['searchSource']
  onSearchSourceChange: CoreProps['onSearchSourceChange']
  handleSourceChange: CoreProps['handleSourceChange']
  showGlobalSearchOptions: CoreProps['showGlobalSearchOptions']
  requireEmails: CoreProps['requireEmails']
  onRequireEmailsChange: CoreProps['onRequireEmailsChange']
  requirePhoneNumbers: CoreProps['requirePhoneNumbers']
  onRequirePhoneNumbersChange: CoreProps['onRequirePhoneNumbersChange']
}

export const SSIModeBoolean = React.memo(function SSIModeBoolean(props: SSIModeBooleanProps) {
  const {
    value, onChange, handleKeyDown, handleSubmit, canSubmit, isLoading, getPlaceholder,
    textareaRef, booleanError,
    searchSource, onSearchSourceChange, handleSourceChange, showGlobalSearchOptions,
    requireEmails, onRequireEmailsChange, requirePhoneNumbers, onRequirePhoneNumbersChange,
  } = props

  return (
    <div className="space-y-3">
      {/* Container principal com textarea e controles posicionados absolutamente (como Natural) */}
      <div className="relative">
        <div className="absolute left-3 top-3">
          <Binary className="w-4 h-4 text-lia-text-primary" />
        </div>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder()}
          className={cn(
            "w-full resize-none rounded-md pl-10 pr-28 py-3 text-sm font-mono focus:outline-none min-h-14 transition-colors border bg-lia-bg-primary",
            booleanError && "ring-2 ring-red-300"
          )}
          style={{borderColor: booleanError ? "var(--status-error)" : "var(--lia-border-subtle)",
            color: "var(--lia-btn-primary-bg)"}}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--lia-border-default)"
            e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = booleanError ? "var(--status-error)" : "var(--lia-border-subtle)"
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
                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                      searchSource === 'local'
                        ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                        : "hover:bg-lia-bg-tertiary"
                    , searchSource === 'local' ? "text-wedo-green-text" : "text-lia-text-tertiary"
                    )}
                  >
                    <Home className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Seu banco de talentos</p>
                  <p className="text-xs text-lia-text-disabled">Gratuito • Local</p>
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
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        searchSource === 'hybrid'
                          ? "bg-wedo-orange/15 ring-1 ring-wedo-orange"
                          : "hover:bg-lia-bg-tertiary"
                      , searchSource === 'hybrid' ? "text-wedo-orange-text" : "text-lia-text-tertiary"
                      )}
                    >
                      <Zap className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Expanda sua busca</p>
                    <p className="text-xs text-lia-text-disabled" aria-live="polite" aria-atomic="true">Local + Global • 1 cred + $0.01 Apify/cand</p>
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
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        searchSource === 'global'
                          ? "bg-wedo-cyan/15 ring-1 ring-lia-btn-primary-bg/20"
                          : "hover:bg-lia-bg-tertiary"
                      , searchSource === 'global' ? "text-lia-text-primary" : "text-lia-text-tertiary"
                      )}
                    >
                      <Globe className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Alcance global</p>
                    <p className="text-xs text-lia-text-disabled" aria-live="polite" aria-atomic="true">800M+ candidatos • 1 cred + $0.01 Apify/cand</p>
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
                      <p className="text-xs text-lia-text-disabled">{requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
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
                      <p className="text-xs text-lia-text-disabled">{requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
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
                "flex items-center justify-center p-1.5 rounded-md transition-colors",
                canSubmit() ? "hover:bg-lia-bg-tertiary" : "opacity-50 cursor-not-allowed"
              , canSubmit() ? "text-lia-text-tertiary" : "text-lia-text-disabled"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
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
        <span className="text-xs text-lia-text-secondary">Operadores:</span>
        {["AND", "OR", "NOT", "(", ")"].map((op) => (
          <button
            key={op}
            onClick={() => onChange(value + (value ? " " : "") + op + " ")}
            className="px-2 py-0.5 rounded-xl text-xs font-mono hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none bg-lia-bg-tertiary text-lia-text-secondary"
          >
            {op}
          </button>
        ))}
      </div>

      {/* Dica contextual padronizada */}
      <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND &quot;São Paulo&quot;
          </p>
        </div>
      </div>
    </div>
  )
})
SSIModeBoolean.displayName = 'SSIModeBoolean'
