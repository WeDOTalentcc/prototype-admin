"use client"

import React from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Code, Globe, Home, Lightbulb, Mail, Phone, Search, Zap } from "lucide-react"
import { useExpandableAIPromptCore } from "../useExpandableAIPromptCore"

type EAPTabBooleanProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'booleanSearchValue' | 'setBooleanSearchValue' | 'searchSource' | 'setSearchSource' |
  'showGlobalSearchOptions' | 'handleSourceChange' | 'requireEmails' | 'setRequireEmails' |
  'requirePhoneNumbers' | 'setRequirePhoneNumbers' | 'onCommand'
>

export const EAPTabBoolean = React.memo(function EAPTabBoolean(props: EAPTabBooleanProps) {
  const {
    booleanSearchValue, setBooleanSearchValue, searchSource, setSearchSource,
    showGlobalSearchOptions, handleSourceChange, requireEmails, setRequireEmails,
    requirePhoneNumbers, setRequirePhoneNumbers, onCommand,
  } = props

  return (
    <div className="space-y-3">
      <p className="text-xs lia-body">Use operadores booleanos para buscas precisas</p>
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <Code className="w-4 h-4 lia-text-base" />
        </div>
        <input
          type="text"
          value={booleanSearchValue}
          onChange={(e) => setBooleanSearchValue(e.target.value)}
          placeholder='(Python OR Java) AND "São Paulo" NOT junior'
          className="border border-input bg-background rounded-lg text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-full pl-10 pr-44 py-2.5 text-sm font-mono"
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
                      ? 'bg-gray-200'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'lia-text-base' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Base Local</p>
                <p className="text-micro lia-text-secondary">Gratuito</p>
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
                        ? 'bg-gray-200'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'lia-text-base' : 'lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                  <p className="text-micro lia-text-secondary" aria-live="polite" aria-atomic="true">1 crédito/candidato</p>
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
                        ? 'bg-gray-200'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'lia-text-base' : 'lia-text-secondary'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-xs font-medium">Base Global</p>
                  <p className="text-micro lia-text-secondary" aria-live="polite" aria-atomic="true">1 crédito/candidato</p>
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
                  className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                    requireEmails
                      ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Apenas com Email</p>
                <p className="text-micro lia-text-secondary">{requireEmails ? 'Ativo' : '+1 crédito se ativo'}</p>
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
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'lia-text-secondary'}`} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Apenas com Telefone</p>
                <p className="text-micro lia-text-secondary">{requirePhoneNumbers ? 'Ativo' : '+1 crédito se ativo'}</p>
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
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 lia-text-base" />
          <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">
            <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND &quot;São Paulo&quot;
          </p>
        </div>
      </div>
    </div>
  )
})
EAPTabBoolean.displayName = 'EAPTabBoolean'
