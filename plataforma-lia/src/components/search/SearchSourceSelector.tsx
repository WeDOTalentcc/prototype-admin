"use client"

/**
 * SearchSourceSelector — Botões compactos de seleção de fonte de busca (local/híbrida/global)
 * + toggles de email e telefone.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Portabilidade Vue: mapeia para componente SearchSourceSelector.vue.
 */

import React from "react"
import { Home, Zap, Globe, Mail, Phone } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { SearchSource } from "@/components/search/expandable-ai-prompt.types"

interface SearchSourceSelectorProps {
  searchSource: SearchSource
  showGlobalSearchOptions: boolean
  requireEmails: boolean
  requirePhoneNumbers: boolean
  onLocalClick: () => void
  onHybridClick: () => void
  onGlobalClick: () => void
  onToggleEmails: () => void
  onTogglePhones: () => void
}

export function SearchSourceSelector({
  searchSource,
  showGlobalSearchOptions,
  requireEmails,
  requirePhoneNumbers,
  onLocalClick,
  onHybridClick,
  onGlobalClick,
  onToggleEmails,
  onTogglePhones,
}: SearchSourceSelectorProps) {
  return (
    <div className="flex items-center gap-0.5 mr-1.5">
      {/* Local */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onLocalClick() }}
              className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                searchSource === 'local' ? 'bg-lia-interactive-active' : 'hover:bg-lia-bg-tertiary'
              }`}
            >
              <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs">Base Local (Gratuito)</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Hybrid */}
      {showGlobalSearchOptions && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onHybridClick() }}
                className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                  searchSource === 'hybrid' ? 'bg-lia-interactive-active' : 'hover:bg-lia-bg-tertiary'
                }`}
              >
                <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="text-xs">Local + Global (1 cred + $0.01 Apify/cand)</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}

      {/* Global */}
      {showGlobalSearchOptions && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onGlobalClick() }}
                className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                  searchSource === 'global' ? 'bg-lia-interactive-active' : 'hover:bg-lia-bg-tertiary'
                }`}
              >
                <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="text-xs">Busca Global (1 cred + $0.01 Apify/cand)</p>
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
              onClick={(e) => { e.stopPropagation(); onToggleEmails() }}
              className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                requireEmails
                  ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light'
                  : 'hover:bg-lia-bg-tertiary'
              }`}
            >
              <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-lia-text-tertiary'}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs font-medium">Apenas com Email</p>
            <p className="text-micro text-lia-text-tertiary">{requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Toggle Telefone */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onTogglePhones() }}
              className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                requirePhoneNumbers
                  ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light'
                  : 'hover:bg-lia-bg-tertiary'
              }`}
            >
              <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-lia-text-tertiary'}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs font-medium">Apenas com Telefone</p>
            <p className="text-micro text-lia-text-tertiary">{requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
