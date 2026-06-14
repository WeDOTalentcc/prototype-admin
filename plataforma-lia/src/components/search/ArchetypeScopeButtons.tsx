"use client"

import {
  Search, Loader2,
  Home, Zap, Globe, Mail, Phone
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ArchetypeVacancy, SearchSource } from "./smart-search-input"

export interface ArchetypeScopeButtonsProps {
  searchSource?: SearchSource
  onSearchSourceChange: (source: SearchSource) => void
  onHandleSourceChange?: (source: "hybrid" | "global") => void
  showGlobalSearchOptions: boolean
  requireEmails?: boolean
  onRequireEmailsChange?: (v: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (v: boolean) => void
  selectedArchetype: ArchetypeVacancy | null
  isLoading: boolean
  onSubmit: () => void
}

export function ArchetypeScopeButtons({
  searchSource,
  onSearchSourceChange,
  onHandleSourceChange,
  showGlobalSearchOptions,
  requireEmails,
  onRequireEmailsChange,
  requirePhoneNumbers,
  onRequirePhoneNumbersChange,
  selectedArchetype,
  isLoading,
  onSubmit,
}: ArchetypeScopeButtonsProps) {
  return (
    <>
      <div className="flex items-center gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onSearchSourceChange("local")
                }}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                  searchSource === "local"
                    ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                    : "hover:bg-lia-bg-tertiary"
                , searchSource === "local" ? "text-wedo-green-text" : "text-lia-text-tertiary"
                )}
              >
                <Home className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="bottom"
              className="!animate-none !duration-0"
            >
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
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onHandleSourceChange?.("hybrid")
                  }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                    searchSource === "hybrid"
                      ? "bg-wedo-orange/15 ring-1 ring-wedo-orange"
                      : "hover:bg-lia-bg-tertiary"
                  , searchSource === "hybrid" ? "text-wedo-orange-text" : "text-lia-text-tertiary"
                  )}
                >
                  <Zap className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent
                side="bottom"
                className="!animate-none !duration-0"
              >
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
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onHandleSourceChange?.("global")
                  }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                    searchSource === "global"
                      ? "bg-wedo-cyan/15 ring-1 ring-lia-btn-primary-bg/20"
                      : "hover:bg-lia-bg-tertiary"
                  , searchSource === "global" ? "text-lia-text-primary" : "text-lia-text-tertiary"
                  )}
                >
                  <Globe className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent
                side="bottom"
                className="!animate-none !duration-0"
              >
                <p className="text-xs font-medium">Alcance global</p>
                <p className="text-xs text-lia-text-disabled" aria-live="polite" aria-atomic="true">800M+ candidatos • 1 cred + $0.01 Apify/cand</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {(searchSource === "global" || searchSource === "hybrid") &&
          onRequireEmailsChange &&
          onRequirePhoneNumbersChange && (
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onRequireEmailsChange(!requireEmails)
                      }}
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
                  <TooltipContent
                    side="bottom"
                    className="!animate-none !duration-0"
                  >
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-xs text-lia-text-disabled">
                      {requireEmails ? "Ativo ($0.01/cand)" : "Clique para ativar ($0.01/cand)"}
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onRequirePhoneNumbersChange(!requirePhoneNumbers)
                      }}
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
                  <TooltipContent
                    side="bottom"
                    className="!animate-none !duration-0"
                  >
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-xs text-lia-text-disabled">
                      {requirePhoneNumbers ? "Ativo ($0.01/cand)" : "Clique para ativar ($0.01/cand)"}
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={onSubmit}
                disabled={!selectedArchetype || isLoading}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md transition-colors",
                  selectedArchetype ? "hover:bg-lia-bg-tertiary" : "opacity-50 cursor-not-allowed"
                , selectedArchetype ? "text-lia-text-tertiary" : "text-lia-text-disabled"
                )}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="bottom"
              className="!animate-none !duration-0"
            >
              <p className="text-xs font-medium">Buscar Arquétipo</p>
              <p className="text-xs text-lia-text-disabled">Encontra perfis similares ao arquétipo</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <span className="text-micro text-lia-text-tertiary italic">buscar arquétipo</span>
    </>
  )
}
