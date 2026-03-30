"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Brain, FileText, Globe, HelpCircle, Home, Linkedin, Loader2,
  Mail, Phone, Search, Upload, Wand2, X, Zap
} from "lucide-react"
import { MAX_SIMILAR_URLS, MAX_CV_FILES } from "./hooks/smartSearchConstants"

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
          <Linkedin className="w-3.5 h-3.5 lia-text-600" />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => updateSimilarUrl(index, e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={index === 0 ? "Cole a URL do LinkedIn ou ID do candidato..." : "Cole outra URL para combinar perfis..."}
          className="w-full rounded-md pl-9 pr-20 py-2.5 text-base-ui focus:outline-none transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] lia-text-950"
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
                    className="px-2 py-1 rounded-full text-xs font-medium hover:bg-gray-900 hover:text-white dark:hover:bg-gray-100 dark:hover:lia-text-900 transition-colors motion-reduce:transition-none bg-gray-200/30"
                  >
                    + URL
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs max-w-sidebar-content !animate-none !duration-0">
                  Adicione até 3 perfis para a LIA criar um perfil ideal combinado
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>
    ))}

    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-micro lia-text-400 uppercase tracking-wider">ou</span>
      <div className="flex-1 h-px bg-gray-200" />
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
            <div key={file.name} className="flex items-center gap-2 px-2.5 py-1.5 rounded-full text-xs bg-gray-50">
              <FileText className="w-3 h-3 lia-text-500" />
              <span className="max-w-[150px] truncate lia-text-800 dark:text-lia-text-primary">{file.name}</span>
              <button onClick={() => removeCvFile(index)} className="hover:text-status-error">
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
          {similarCvFiles.length < MAX_CV_FILES && (
            <button
              onClick={() => cvFileInputRef.current?.click()}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium hover:bg-gray-100 transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)]"
            >
              <Upload className="w-3 h-3" />
              + CV
            </button>
          )}
        </div>
      ) : (
        <button
          onClick={() => cvFileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-md text-xs lia-text-500 hover:lia-text-700 hover:bg-gray-50 transition-colors motion-reduce:transition-none border border-dashed"
        >
          <Upload className="w-3.5 h-3.5" />
          Arraste CVs aqui ou clique para upload (máx. 2)
        </button>
      )}
    </div>

    {hasMultipleSources() && !showCombinedSuggestions && (
      <Button onClick={analyzeProfiles} disabled={isAnalyzingProfiles} className="w-full text-xs h-9 bg-gray-900">
        {isAnalyzingProfiles ? (<><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin motion-reduce:animate-none" />Analisando perfis...</>) : (<><Wand2 className="w-3.5 h-3.5 mr-2" />Analisar e combinar perfis com LIA</>)}
      </Button>
    )}

    {showCombinedSuggestions && combinedSuggestions.length > 0 && (
      <div className="p-3 rounded-md space-y-2 border border-lia-border-subtle bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            <span className="text-xs font-medium lia-text-800 dark:text-lia-text-primary">Perfil Ideal sugerido pela LIA</span>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger><HelpCircle className="w-3.5 h-3.5 lia-text-600" /></TooltipTrigger>
              <TooltipContent side="top" className="text-xs max-w-[280px]">A LIA analisou os perfis e combinou skills, experiências e senioridade em comum. Edite ou remova tags antes de buscar.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {combinedSuggestions.map((keyword) => (
            <div key={keyword} className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium group border border-lia-border-subtle bg-lia-bg-primary">
              <span className="lia-text-700">{keyword}</span>
              <button onClick={() => removeSuggestion(keyword)} className="opacity-50 group-hover:opacity-100 hover:text-status-error transition-opacity motion-reduce:transition-none">
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs lia-text-800 dark:text-lia-text-primary">
          Baseado em {similarUrls.filter(u => u.trim()).length + similarCvFiles.length} perfis: skills em comum e pontos fortes combinados.
        </p>
      </div>
    )}

    {combinedSuggestions.length > 0 && (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 lia-text-700" />
            <span className="text-xs font-medium">Preview do prompt de busca</span>
          </div>
          <span className="text-micro lia-text-400">editável</span>
        </div>
        <div className="relative">
          <textarea
            value={similarSearchPrompt}
            onChange={(e) => setSimilarSearchPrompt(e.target.value)}
            placeholder="Descreva o perfil que deseja buscar..."
            className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] lia-text-950"
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--gray-300)"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--gray-200)"; e.currentTarget.style.boxShadow = "none" }}
            rows={2}
          />
          {onSearchSourceChange && (
            <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10">
              <div className="flex items-center gap-1">
                <ScopeButton icon={Home} active={searchSource === 'local'} activeColor="wedo-green" onClick={() => onSearchSourceChange('local')} label="Seu banco de talentos" sublabel="Gratuito • Local" />
                {showGlobalSearchOptions && <ScopeButton icon={Zap} active={searchSource === 'hybrid'} activeColor="wedo-orange" onClick={() => handleSourceChange('hybrid')} label="Expanda sua busca" sublabel="Local + Global • 1 crédito/candidato" />}
                {showGlobalSearchOptions && <ScopeButton icon={Globe} active={searchSource === 'global'} activeColor="wedo-cyan" onClick={() => handleSourceChange('global')} label="Alcance global" sublabel="800M+ candidatos • 1 crédito/candidato" />}
                {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                  <>
                    <ScopeButton icon={Mail} active={requireEmails} activeColor="wedo-green" onClick={() => onRequireEmailsChange(!requireEmails)} label="Apenas com Email" sublabel={requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'} small />
                    <ScopeButton icon={Phone} active={requirePhoneNumbers} activeColor="wedo-green" onClick={() => onRequirePhoneNumbersChange(!requirePhoneNumbers)} label="Apenas com Telefone" sublabel={requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'} small />
                  </>
                )}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button type="button" onClick={handleSubmit} disabled={!canSubmit() || isLoading}
                        className={cn("flex items-center justify-center p-1.5 rounded-md transition-colors motion-reduce:transition-none", canSubmit() ? "hover:bg-gray-100 lia-text-400" : "opacity-50 cursor-not-allowed lia-text-200")}>
                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : <Search className="w-4 h-4" />}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="!animate-none !duration-0">
                      <p className="text-xs font-medium">Buscar Similares</p>
                      <p className="text-xs lia-text-300" aria-live="polite" aria-atomic="true">Encontra candidatos com perfil similar</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <span className="text-micro lia-text-400 italic">buscar similares</span>
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
          className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-14 transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] lia-text-950"
          onFocus={(e) => { e.currentTarget.style.borderColor = "var(--gray-300)"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--wedo-cyan-bg-12)" }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "var(--gray-200)"; e.currentTarget.style.boxShadow = "none" }}
          rows={2}
        />
        {onSearchSourceChange && (
          <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10">
            <div className="flex items-center gap-1">
              <ScopeButton icon={Home} active={searchSource === 'local'} activeColor="wedo-green" onClick={() => onSearchSourceChange('local')} label="Seu banco de talentos" sublabel="Gratuito • Local" />
              {showGlobalSearchOptions && <ScopeButton icon={Zap} active={searchSource === 'hybrid'} activeColor="wedo-orange" onClick={() => handleSourceChange('hybrid')} label="Expanda sua busca" sublabel="Local + Global • 1 crédito/candidato" />}
              {showGlobalSearchOptions && <ScopeButton icon={Globe} active={searchSource === 'global'} activeColor="wedo-cyan" onClick={() => handleSourceChange('global')} label="Alcance global" sublabel="800M+ candidatos • 1 crédito/candidato" />}
              {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                <>
                  <ScopeButton icon={Mail} active={requireEmails} activeColor="wedo-green" onClick={() => onRequireEmailsChange(!requireEmails)} label="Apenas com Email" sublabel={requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'} small />
                  <ScopeButton icon={Phone} active={requirePhoneNumbers} activeColor="wedo-green" onClick={() => onRequirePhoneNumbersChange(!requirePhoneNumbers)} label="Apenas com Telefone" sublabel={requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'} small />
                </>
              )}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" onClick={handleSubmit} disabled={!canSubmit() || isLoading}
                      className={cn("flex items-center justify-center p-1.5 rounded-md transition-colors motion-reduce:transition-none", canSubmit() ? "hover:bg-gray-100 lia-text-400" : "opacity-50 cursor-not-allowed lia-text-200")}>
                      {isLoading ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" /> : <Search className="w-4 h-4" />}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="!animate-none !duration-0">
                    <p className="text-xs font-medium">Buscar Similares</p>
                    <p className="text-xs lia-text-300" aria-live="polite" aria-atomic="true">Encontra candidatos com perfil similar</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <span className="text-micro lia-text-400 italic">buscar similares</span>
          </div>
        )}
      </div>
    )}

    <div className="p-2 rounded-md border border-lia-border-subtle bg-gray-50/50">
      <div className="flex items-start gap-2">
        <Wand2 className="w-3 h-3 text-wedo-cyan mt-0.5 flex-shrink-0" />
        <p className="text-xs lia-text-800 dark:text-lia-text-primary">
          <strong>Dica:</strong> Cole 1 a 3 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, a LIA combina as melhores características e sugere palavras-chave para encontrar candidatos similares.
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
    : activeColor === 'wedo-cyan' ? 'bg-wedo-cyan/15 ring-1 ring-gray-900/20'
    : ''
  const textClass = activeColor === 'wedo-green' ? 'text-wedo-green'
    : activeColor === 'wedo-orange' ? 'text-wedo-orange'
    : activeColor === 'wedo-cyan' ? 'lia-text-950'
    : ''
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onClick() }}
            className={cn("flex items-center justify-center p-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none", active ? ringClass : "hover:bg-gray-100", active ? textClass : "lia-text-400")}>
            <Icon className={size} />
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="!animate-none !duration-0">
          <p className="text-xs font-medium">{label}</p>
          <p className="text-xs lia-text-300">{sublabel}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
