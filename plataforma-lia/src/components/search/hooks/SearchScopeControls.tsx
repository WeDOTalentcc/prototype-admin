"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Globe, Home, Loader2, Mail, Phone, Search, Zap } from "lucide-react"
import type { SearchSource } from "./smartSearchConstants"

interface SearchScopeControlsProps {
  showSearchButton?: boolean
  onSearch?: () => void
  searchSource: SearchSource
  onSearchSourceChange?: (source: SearchSource) => void
  handleSourceChange: (source: SearchSource) => void
  showGlobalSearchOptions: boolean
  onRequireEmailsChange?: (value: boolean) => void
  onRequirePhoneNumbersChange?: (value: boolean) => void
  requireEmails: boolean
  requirePhoneNumbers: boolean
  canSubmit: () => boolean
  isLoading: boolean
}

export function SearchScopeControls({
  showSearchButton = false,
  onSearch,
  searchSource,
  onSearchSourceChange,
  handleSourceChange,
  showGlobalSearchOptions,
  onRequireEmailsChange,
  onRequirePhoneNumbersChange,
  requireEmails,
  requirePhoneNumbers,
  canSubmit,
  isLoading,
}: SearchScopeControlsProps) {
  return (
    <div className="flex items-center gap-1 flex-shrink-0">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange?.('local'); }}
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
              <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">800M+ candidatos • 1 cred + $0.01 Apify/cand</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
      
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
      
      {showSearchButton && onSearch && (
        <>
          <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />
          <Button
            onClick={onSearch}
            disabled={!canSubmit() || isLoading}
            size="sm"
            className={cn("h-8 w-8 p-0 rounded-md transition-transform motion-reduce:transition-none hover:scale-105", canSubmit() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-bg-tertiary text-lia-text-secondary")}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : <Search className="w-4 h-4" />}
          </Button>
        </>
      )}
    </div>
  )
}
