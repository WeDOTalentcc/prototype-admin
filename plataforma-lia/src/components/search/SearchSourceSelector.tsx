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
                searchSource === 'local' ? 'bg-gray-200' : 'hover:bg-gray-100'
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
                  searchSource === 'hybrid' ? 'bg-gray-200' : 'hover:bg-gray-100'
                }`}
              >
                <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="text-xs">Local + Global (1 créd/cand)</p>
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
                  searchSource === 'global' ? 'bg-gray-200' : 'hover:bg-gray-100'
                }`}
              >
                <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
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
              onClick={(e) => { e.stopPropagation(); onToggleEmails() }}
              className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                requireEmails
                  ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light'
                  : 'hover:bg-gray-100'
              }`}
            >
              <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-lia-text-tertiary'}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs font-medium">Apenas com Email</p>
            <p className="text-micro text-lia-text-tertiary">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
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
                  : 'hover:bg-gray-100'
              }`}
            >
              <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-lia-text-tertiary'}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs font-medium">Apenas com Telefone</p>
            <p className="text-micro text-lia-text-tertiary">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
