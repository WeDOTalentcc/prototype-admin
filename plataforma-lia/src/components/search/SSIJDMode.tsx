"use client"

import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import {
  Briefcase, ChevronRight, FileText, Globe, Home, Lightbulb,
  Loader2, Mail, Phone, Search, Upload, X, Zap
} from"lucide-react"
import type { useSmartSearchCore } from"./hooks/useSmartSearchCore"

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

         aria-live="polite" aria-atomic="true">
          Buscar vaga existente
        </span>
        <span className="text-micro text-lia-text-tertiary">opcional</span>
      </div>

      {selectedVacancy ? (
        <div 
          className="flex items-center justify-between p-2.5 rounded-xl border bg-wedo-cyan/[0.08]"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-6 h-6 rounded-full flex items-center justify-center bg-lia-interactive-active"
            >
              <Briefcase className="w-3 h-3 text-lia-text-secondary" />
            </div>
            <div>
              <p className="text-base-ui font-medium text-lia-text-primary">{selectedVacancy.title}</p>
              {selectedVacancy.job_id && (
                <p className="text-micro text-lia-text-secondary">ID: {selectedVacancy.job_id}</p>
              )}
            </div>
          </div>
          <button
            onClick={clearSelectedVacancy}
            className="p-1 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
          >
            <X className="w-3.5 h-3.5 text-lia-text-tertiary" />
          </button>
        </div>
      ) : (
        <div className="relative" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="absolute left-3 top-1/2 -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
            {isSearchingVacancies ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
            ) : (
              <Search className="w-3.5 h-3.5 text-lia-text-tertiary" />
            )}
          </div>
          <input
            type="text"
            value={jdVacancySearch}
            onChange={(e) => setJdVacancySearch(e.target.value)}
            placeholder="Digite o nome ou ID da vaga..."
            className="w-full pl-9 pr-4 py-2.5 text-base-ui rounded-xl border focus:outline-none transition-colors motion-reduce:transition-none bg-lia-bg-secondary text-lia-text-primary"
            onFocus={(e) => {
              e.currentTarget.style.borderColor ="var(--lia-border-default)"
              e.currentTarget.style.boxShadow ="0 0 0 2px var(--wedo-cyan-bg-12)"
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor ="var(--lia-border-subtle)"
              e.currentTarget.style.boxShadow ="none"
            }}
          />

          {showVacancyResults && jdVacancyResults.length > 0 && (
            <div 
              className="absolute z-50 top-full left-0 right-0 mt-1 rounded-xl border overflow-hidden"
             
            >
              {jdVacancyResults.map((vacancy) => (
                <button
                  key={vacancy.id}
                  onClick={() => handleSelectVacancy(vacancy)}
                  className="w-full p-2.5 text-left hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none border-b last:border-b-0 border border-lia-border-subtle"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-base-ui font-medium text-lia-text-primary truncate">{vacancy.title}</p>
                        <Chip 
                          variant="neutral" 
                          className={`text-micro px-1.5 py-0 h-4 flex-shrink-0 ${vacancy.status === 'Ativa' ? 'border-status-success text-status-success' : 'border-lia-text-tertiary text-lia-text-secondary'}`}
                        >
                          {vacancy.status}
                        </Chip>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {vacancy.job_id && (
                          <span className="text-micro text-lia-text-secondary">ID: {vacancy.job_id}</span>
                        )}
                        <span className="text-micro text-lia-text-tertiary">{formatDate(vacancy.created_at)}</span>
                      </div>
                      {vacancy.description_preview && (
                        <p className="text-xs text-lia-text-secondary mt-1 line-clamp-2">
                          {vacancy.description_preview}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-lia-text-muted flex-shrink-0 mt-0.5" />
                  </div>
                </button>
              ))}
            </div>
          )}

          {showVacancyResults && jdVacancySearch.length >= 2 && jdVacancyResults.length === 0 && !isSearchingVacancies && (
            <div 
              className="absolute z-50 top-full left-0 right-0 mt-1 p-2.5 rounded-xl border text-center"
             
            >
              <p className="text-base-ui text-lia-text-secondary" aria-live="polite" aria-atomic="true">Nenhuma vaga encontrada</p>
            </div>
          )}
        </div>
      )}
    </div>

    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-lia-interactive-active" />
      <span className="text-micro text-lia-text-tertiary uppercase tracking-wider">ou</span>
      <div className="flex-1 h-px bg-lia-interactive-active" />
    </div>

    <div className="flex items-center justify-between mb-1.5">
      <span 
        className="text-xs font-medium"

       aria-live="polite" aria-atomic="true">
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
        className="w-full resize-none rounded-xl px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[100px] transition-colors motion-reduce:transition-none border bg-lia-bg-primary"
       
        onFocus={(e) => {
          e.currentTarget.style.borderColor ="var(--lia-border-default)"
          e.currentTarget.style.boxShadow ="0 0 0 2px var(--wedo-cyan-bg-12)"
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor ="var(--lia-border-subtle)"
          e.currentTarget.style.boxShadow ="none"
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
                    className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                      searchSource === 'local' 
                        ?"bg-wedo-green/15 ring-1 ring-wedo-green" 
                        :"hover:bg-lia-bg-tertiary"
                    , searchSource === 'local' ?"text-wedo-green-text" :"text-lia-text-tertiary"
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
                      className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        searchSource === 'hybrid' 
                          ?"bg-wedo-orange/15 ring-1 ring-wedo-orange" 
                          :"hover:bg-lia-bg-tertiary"
                      , searchSource === 'hybrid' ?"text-wedo-orange-text" :"text-lia-text-tertiary"
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
                      className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        searchSource === 'global' 
                          ?"bg-wedo-cyan/15 ring-1 ring-lia-btn-primary-bg/20" 
                          :"hover:bg-lia-bg-tertiary"
                      , searchSource === 'global' ?"text-lia-text-primary" :"text-lia-text-tertiary"
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
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                        className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                          requireEmails 
                            ?"bg-wedo-green/15 ring-1 ring-wedo-green" 
                            :"hover:bg-lia-bg-tertiary"
                        , requireEmails ?"text-wedo-green-text" :"text-lia-text-tertiary"
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
                        className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                          requirePhoneNumbers 
                            ?"bg-wedo-green/15 ring-1 ring-wedo-green" 
                            :"hover:bg-lia-bg-tertiary"
                        , requirePhoneNumbers ?"text-wedo-green-text" :"text-lia-text-tertiary"
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

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!canSubmit() || isLoading}
                    className={cn("flex items-center justify-center p-1.5 rounded-md transition-colors",
                      canSubmit() ?"hover:bg-lia-bg-tertiary" :"opacity-50 cursor-not-allowed"
                    , canSubmit() ?"text-lia-text-tertiary" :"text-lia-text-disabled"
                    )}
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Search className="w-4 h-4" />
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none !duration-0">
                  <p className="text-xs font-medium">Extrair e Buscar</p>
                  <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">Extrai requisitos e busca candidatos</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <span className="text-micro text-lia-text-tertiary italic">extrair e buscar</span>
        </div>
      )}
    </div>

    {jdContent.trim().length > 0 && (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
            <span className="text-xs font-medium text-lia-text-primary">
              Preview do prompt de busca
            </span>
          </div>
          <span className="text-micro text-lia-text-tertiary">editável</span>
        </div>
        <textarea
          value={jdSearchPrompt}
          onChange={(e) => setJdSearchPrompt(e.target.value)}
          placeholder="O prompt será gerado a partir da descrição da vaga..."
          className="w-full resize-none rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 min-h-[60px] border border-lia-border-default bg-lia-bg-secondary text-lia-text-primary"
          rows={2}
        />
      </div>
    )}

    <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
        <p className="text-xs text-lia-text-secondary">
          <strong>Dica:</strong> Selecione uma vaga existente ou cole a JD completa para extrair automaticamente requisitos técnicos e comportamentais.
        </p>
      </div>
    </div>
  </div>
  )
}
