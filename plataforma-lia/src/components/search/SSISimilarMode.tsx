"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Brain, FileText, Globe, HelpCircle, Home, Lightbulb, Linkedin, Loader2,
  Mail, Phone, Search, Upload, Wand2, X, Zap
} from "lucide-react"
import { MAX_SIMILAR_URLS, MAX_CV_FILES } from "./hooks/smartSearchConstants"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface SSISimilarModeProps {
  similarUrls: string[]
  updateSimilarUrl: (index: number, value: string) => void
  handleKeyDown: (e: React.KeyboardEvent) => void
  removeSimilarUrl: (index: number) => void
  addSimilarUrl: () => void
  cvFileInputRef: React.RefObject<HTMLInputElement | null>
  handleCvUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  similarCvFiles: File[]
  removeCvFile: (index: number) => void
  isLoading: boolean
  hasMultipleSources: () => boolean
  showCombinedSuggestions: boolean
  analyzeProfiles: () => void
  isAnalyzingProfiles: boolean
  combinedSuggestions: string[]
  removeSuggestion: (keyword: string) => void
  similarSearchPrompt: string
  setSimilarSearchPrompt: (value: string) => void
  onSearchSourceChange?: (source: string) => void
  searchSource: string
  handleSourceChange: (source: string) => void
  showGlobalSearchOptions: boolean
  onRequireEmailsChange?: (value: boolean) => void
  onRequirePhoneNumbersChange?: (value: boolean) => void
  requireEmails: boolean
  requirePhoneNumbers: boolean
  handleSubmit: () => void
  canSubmit: () => boolean
}

export function SSISimilarMode(props: SSISimilarModeProps) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const {
    similarUrls, updateSimilarUrl, handleKeyDown, removeSimilarUrl, addSimilarUrl,
    cvFileInputRef, handleCvUpload, similarCvFiles, removeCvFile,
    isLoading, hasMultipleSources, showCombinedSuggestions, analyzeProfiles, isAnalyzingProfiles,
    combinedSuggestions, removeSuggestion, similarSearchPrompt, setSimilarSearchPrompt,
    onSearchSourceChange, searchSource, handleSourceChange, showGlobalSearchOptions,
    onRequireEmailsChange, onRequirePhoneNumbersChange, requireEmails, requirePhoneNumbers,
    handleSubmit, canSubmit,
  } = props

  return (
  <div className="space-y-3">
    {similarUrls.map((url, index) => (
      <div key={`url-${index}`} className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <Linkedin className="w-3.5 h-3.5 text-lia-text-secondary" />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => updateSimilarUrl(index, e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={index === 0 ? "Cole a URL do LinkedIn ou ID do candidato..." : "Cole outra URL para combinar perfis..."}
          className="w-full rounded-xl pl-9 pr-20 py-2.5 text-base-ui focus:outline-none transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] text-lia-text-primary"
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--lia-border-default)"
            e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)"
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--lia-border-subtle)"
            e.currentTarget.style.boxShadow = "none"
          }}
          disabled={isLoading}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {index > 0 && (
            <button
              onClick={() => removeSimilarUrl(index)}
              className="p-1 rounded-md hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
            >
              <X className="w-3 h-3 text-status-error" />
            </button>
          )}
          {index === similarUrls.length - 1 && similarUrls.length < MAX_SIMILAR_URLS && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={addSimilarUrl}
                    className="px-2 py-1 rounded-full text-xs font-medium hover:bg-lia-btn-primary-bg hover:text-white dark:hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none bg-lia-interactive-active/30"
                  >
                    + URL
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs max-w-sidebar-content !animate-none !duration-0">
                  Adicione até 3 perfis para {personaName} criar um perfil ideal combinado
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>
    ))}

    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-lia-interactive-active" />
      <span className="text-micro text-lia-text-tertiary uppercase tracking-wider">ou</span>
      <div className="flex-1 h-px bg-lia-interactive-active" />
    </div>

    <div className="relative">
      <input
        ref={cvFileInputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        multiple
        onChange={handleCvUpload}
        className="hidden"
      />
      {similarCvFiles.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {similarCvFiles.map((file, index) => (
            <div key={file.name} className="flex items-center gap-2 px-2.5 py-1.5 rounded-full text-xs bg-lia-bg-secondary">
              <FileText className="w-3 h-3 text-lia-text-secondary" />
              <span className="max-w-[150px] truncate text-lia-text-primary">{file.name}</span>
              <button onClick={() => removeCvFile(index)} className="hover:text-status-error">
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
          {similarCvFiles.length < MAX_CV_FILES && (
            <button
              onClick={() => cvFileInputRef.current?.click()}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)]"
            >
              <Upload className="w-3 h-3" />
              + CV
            </button>
          )}
        </div>
      ) : (
        <button
          onClick={() => cvFileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none border border-dashed"
        >
          <Upload className="w-3.5 h-3.5" />
          Arraste CVs aqui ou clique para upload (máx. 2)
        </button>
      )}
    </div>

    {hasMultipleSources() && !showCombinedSuggestions && (
      <Button onClick={analyzeProfiles} disabled={isAnalyzingProfiles} className="w-full text-xs h-9 bg-lia-btn-primary-bg">
        {isAnalyzingProfiles ? (<><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin motion-reduce:animate-none" />Analisando perfis...</>) : (<><Wand2 className="w-3.5 h-3.5 mr-2" />{`Analisar e combinar perfis com ${personaName}`}</>)}
      </Button>
    )}

    {showCombinedSuggestions && combinedSuggestions.length > 0 && (
      <div className="p-3 rounded-xl space-y-2 border border-lia-border-subtle bg-lia-bg-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-primary">{`Perfil Ideal sugerido por ${personaName}`}</span>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger><HelpCircle className="w-3.5 h-3.5 text-lia-text-secondary" /></TooltipTrigger>
              <TooltipContent side="top" className="text-xs max-w-[280px]">{`${personaName} analisou os perfis e combinou`} skills, experiências e senioridade em comum. Edite ou remova tags antes de buscar.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {combinedSuggestions.map((keyword) => (
            <div key={keyword} className="flex items-center gap-1 px-2 py-1 rounded-xl text-xs font-medium group border border-lia-border-subtle bg-lia-bg-primary">
              <span className="text-lia-text-primary">{keyword}</span>
              <button onClick={() => removeSuggestion(keyword)} className="opacity-50 group-hover:opacity-100 hover:text-status-error transition-opacity motion-reduce:transition-none">
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs text-lia-text-primary">
          Baseado em {similarUrls.filter(u => u.trim()).length + similarCvFiles.length} perfis: skills em comum e pontos fortes combinados.
        </p>
      </div>
    )}

    {combinedSuggestions.length > 0 && (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
            <span className="text-xs font-medium">Preview do prompt de busca</span>
          </div>
          <span className="text-micro text-lia-text-tertiary">editável</span>
        </div>
        <div className="relative">
          <textarea
            value={similarSearchPrompt}
            onChange={(e) => setSimilarSearchPrompt(e.target.value)}
            placeholder="Descreva o perfil que deseja buscar..."
            className="w-full resize-none rounded-xl px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] text-lia-text-primary"
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--lia-border-default)"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--lia-border-subtle)"; e.currentTarget.style.boxShadow = "none" }}
            rows={2}
          />
          {onSearchSourceChange && (
            <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10">
              <div className="flex items-center gap-1">
                <ScopeButton icon={Home} active={searchSource === 'local'} activeColor="wedo-green" onClick={() => onSearchSourceChange('local')} label="Seu banco de talentos" sublabel="Gratuito • Local" />
                {showGlobalSearchOptions && <ScopeButton icon={Zap} active={searchSource === 'hybrid'} activeColor="wedo-orange" onClick={() => handleSourceChange('hybrid')} label="Expanda sua busca" sublabel="Local + Global • 1 cred + $0.01 Apify/cand" />}
                {showGlobalSearchOptions && <ScopeButton icon={Globe} active={searchSource === 'global'} activeColor="wedo-cyan" onClick={() => handleSourceChange('global')} label="Alcance global" sublabel="800M+ candidatos • 1 cred + $0.01 Apify/cand" />}
                {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                  <>
                    <ScopeButton icon={Mail} active={requireEmails} activeColor="wedo-green" onClick={() => onRequireEmailsChange(!requireEmails)} label="Apenas com Email" sublabel={requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'} small />
                    <ScopeButton icon={Phone} active={requirePhoneNumbers} activeColor="wedo-green" onClick={() => onRequirePhoneNumbersChange(!requirePhoneNumbers)} label="Apenas com Telefone" sublabel={requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'} small />
                  </>
                )}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button type="button" onClick={handleSubmit} disabled={!canSubmit() || isLoading}
                        className={cn("flex items-center justify-center p-1.5 rounded-md transition-colors motion-reduce:transition-none", canSubmit() ? "hover:bg-lia-bg-tertiary text-lia-text-tertiary" : "opacity-50 cursor-not-allowed text-lia-text-disabled")}>
                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : <Search className="w-4 h-4" />}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Buscar Similares</p>
                      <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">Encontra candidatos com perfil similar</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <span className="text-micro text-lia-text-tertiary italic">buscar similares</span>
            </div>
          )}
        </div>
      </div>
    )}

    {combinedSuggestions.length === 0 && (
      <div className="relative">
        <textarea
          value={similarSearchPrompt}
          onChange={(e) => setSimilarSearchPrompt(e.target.value)}
          placeholder="Edite o prompt de busca ou adicione perfis acima..."
          className="w-full resize-none rounded-xl px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-14 transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] text-lia-text-primary"
          onFocus={(e) => { e.currentTarget.style.borderColor = "var(--lia-border-default)"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)" }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "var(--lia-border-subtle)"; e.currentTarget.style.boxShadow = "none" }}
          rows={2}
        />
        {onSearchSourceChange && (
          <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10">
            <div className="flex items-center gap-1">
              <ScopeButton icon={Home} active={searchSource === 'local'} activeColor="wedo-green" onClick={() => onSearchSourceChange('local')} label="Seu banco de talentos" sublabel="Gratuito • Local" />
              {showGlobalSearchOptions && <ScopeButton icon={Zap} active={searchSource === 'hybrid'} activeColor="wedo-orange" onClick={() => handleSourceChange('hybrid')} label="Expanda sua busca" sublabel="Local + Global • 1 cred + $0.01 Apify/cand" />}
              {showGlobalSearchOptions && <ScopeButton icon={Globe} active={searchSource === 'global'} activeColor="wedo-cyan" onClick={() => handleSourceChange('global')} label="Alcance global" sublabel="800M+ candidatos • 1 cred + $0.01 Apify/cand" />}
              {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                <>
                  <ScopeButton icon={Mail} active={requireEmails} activeColor="wedo-green" onClick={() => onRequireEmailsChange(!requireEmails)} label="Apenas com Email" sublabel={requireEmails ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'} small />
                  <ScopeButton icon={Phone} active={requirePhoneNumbers} activeColor="wedo-green" onClick={() => onRequirePhoneNumbersChange(!requirePhoneNumbers)} label="Apenas com Telefone" sublabel={requirePhoneNumbers ? 'Ativo ($0.01/cand)' : 'Clique para ativar ($0.01/cand)'} small />
                </>
              )}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" onClick={handleSubmit} disabled={!canSubmit() || isLoading}
                      className={cn("flex items-center justify-center p-1.5 rounded-md transition-colors motion-reduce:transition-none", canSubmit() ? "hover:bg-lia-bg-tertiary text-lia-text-tertiary" : "opacity-50 cursor-not-allowed text-lia-text-disabled")}>
                      {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : <Search className="w-4 h-4" />}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Buscar Similares</p>
                    <p className="text-xs text-lia-text-muted" aria-live="polite" aria-atomic="true">Encontra candidatos com perfil similar</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <span className="text-micro text-lia-text-tertiary italic">buscar similares</span>
          </div>
        )}
      </div>
    )}

    <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
        <p className="text-xs text-lia-text-secondary">
          <strong>Dica:</strong> Cole 1 a 3 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, `${personaName} combina as melhores características` e sugere palavras-chave para encontrar candidatos similares.
        </p>
      </div>
    </div>
  </div>
  )
}

function ScopeButton({ icon: Icon, active, activeColor, onClick, label, sublabel, small }: {
  icon: React.ElementType; active: boolean; activeColor: string; onClick: () => void; label: string; sublabel: string; small?: boolean
}) {
  const size = small ? "w-3.5 h-3.5" : "w-4 h-4"
  const ringClass = activeColor === 'wedo-green' ? 'bg-wedo-green/15 ring-1 ring-wedo-green' 
    : activeColor === 'wedo-orange' ? 'bg-wedo-orange/15 ring-1 ring-wedo-orange'
    : activeColor === 'wedo-cyan' ? 'bg-wedo-cyan/15 ring-1 ring-lia-btn-primary-bg/20'
    : ''
  const textClass = activeColor === 'wedo-green' ? 'text-wedo-green-text'
    : activeColor === 'wedo-orange' ? 'text-wedo-orange-text'
    : activeColor === 'wedo-cyan' ? 'text-lia-text-primary'
    : ''
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onClick() }}
            className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none", active ? ringClass : "hover:bg-lia-bg-tertiary", active ? textClass : "text-lia-text-tertiary")}>
            <Icon className={size} />
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="!animate-none !duration-0">
          <p className="text-xs font-medium">{label}</p>
          <p className="text-xs text-lia-text-muted">{sublabel}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
