"use client"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Briefcase, ChevronRight, FileText, Globe, Home, Lightbulb,
  Loader2, Mail, Phone, Search, Upload, X, Zap
} from "lucide-react"
import type { useSmartSearchCore } from "./hooks/useSmartSearchCore"

type SSIJDModeProps = ReturnType<typeof useSmartSearchCore>

export function SSIJDMode(props: SSIJDModeProps) {
  const {
    canSubmit, clearSelectedVacancy, fileInputRef, formatDate,
    getPlaceholder, handleFileUpload, handleSelectVacancy,
    handleSourceChange, handleSubmit, isLoading, isSearchingVacancies,
    jdContent, jdSearchPrompt, jdVacancyResults, jdVacancySearch,
    onRequireEmailsChange, onRequirePhoneNumbersChange, onSearchSourceChange,
    requireEmails, requirePhoneNumbers, searchSource, selectedVacancy,
    setJdContent, setJdSearchPrompt, setJdVacancySearch, setSelectedVacancy,
    showGlobalSearchOptions, showVacancyResults
  } = props

  return (
  <div className="space-y-3">
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

    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-micro text-gray-400 uppercase tracking-wider">ou</span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>

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
        className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[100px] transition-all border"
        style={{backgroundColor: "var(--lia-bg-primary)",
          color: "var(--gray-950)"}}
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
          <span className="text-micro text-gray-400 italic">extrair e buscar</span>
        </div>
      )}
    </div>

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

    <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
        <p className="text-xs text-gray-800 dark:text-gray-200">
          <strong>Dica:</strong> Selecione uma vaga existente ou cole a JD completa para extrair automaticamente requisitos técnicos e comportamentais.
        </p>
      </div>
    </div>
  </div>
  )
}
