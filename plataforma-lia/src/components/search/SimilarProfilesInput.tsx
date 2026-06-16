"use client"

/**
 * SimilarProfilesInput — Aba de busca por perfis similares (LinkedIn URLs + CVs).
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Portabilidade Vue: mapeia para componente SimilarProfilesInput.vue.
 */

import React, { useRef } from "react"
import {
  Linkedin, X, Upload, Wand2, Brain, Info, Loader2, Search, Lightbulb,
  FileText,
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { MAX_SIMILAR_URLS, MAX_CV_FILES } from "@/components/search/expandable-ai-prompt.types"

interface SimilarProfilesInputProps {
  similarUrls: string[]
  similarCvFiles: File[]
  isAnalyzingProfiles: boolean
  combinedSuggestions: string[]
  showCombinedSuggestions: boolean
  onUpdateSimilarUrl: (index: number, value: string) => void
  onRemoveSimilarUrl: (index: number) => void
  onAddSimilarUrl: () => void
  onCvFilesSelected: (files: FileList) => void
  onRemoveCvFile: (index: number) => void
  onRemoveSuggestion: (keyword: string) => void
  hasMultipleSources: () => boolean
  onAnalyzeProfiles: () => void
  onSearch: (validUrls: string[]) => void
}

export function SimilarProfilesInput({
  similarUrls,
  similarCvFiles,
  isAnalyzingProfiles,
  combinedSuggestions,
  showCombinedSuggestions,
  onUpdateSimilarUrl,
  onRemoveSimilarUrl,
  onAddSimilarUrl,
  onCvFilesSelected,
  onRemoveCvFile,
  onRemoveSuggestion,
  hasMultipleSources,
  onAnalyzeProfiles,
  onSearch,
}: SimilarProfilesInputProps) {
  const cvFileInputRef = useRef<HTMLInputElement>(null)
  const validUrls = similarUrls.filter(u => u.trim())
  const hasSource = validUrls.length > 0 || similarCvFiles.length > 0

  return (
    <div className="space-y-3">
      {/* URL inputs — up to 2 */}
      {similarUrls.map((url, index) => (
        <div key={`url-${index}`} className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2">
            <Linkedin className="w-4 h-4 text-lia-text-secondary" />
          </div>
          <input
            type="text"
            value={url}
            onChange={(e) => onUpdateSimilarUrl(index, e.target.value)}
            placeholder={
              index === 0
                ? "Cole a URL do LinkedIn ou ID do candidato..."
                : "Cole outra URL para combinar perfis..."
            }
            className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg text-lia-text-primary focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-400/20 w-full pl-10 pr-20 py-2.5 text-sm"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {index > 0 && (
              <button
                onClick={() => onRemoveSimilarUrl(index)}
                className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
              >
                <X className="w-3.5 h-3.5 text-status-error" />
              </button>
            )}
            {index === similarUrls.length - 1 && similarUrls.length < MAX_SIMILAR_URLS && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={onAddSimilarUrl}
                      className="h-8 px-3 rounded-xl text-sm font-bold hover:bg-lia-btn-primary-hover hover:text-white transition-colors motion-reduce:transition-none text-lia-text-primary bg-lia-bg-tertiary"
                    >
                      + URL
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs max-w-sidebar-content">
                    Adicione até 2 perfis para a IA criar um perfil ideal combinado
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>
      ))}

      {/* Separador CV */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-px bg-lia-interactive-active" />
        <span className="text-xs text-lia-text-secondary px-2">ou</span>
        <div className="flex-1 h-px bg-lia-interactive-active" />
      </div>

      {/* CV Upload */}
      <div className="relative">
        <input
          ref={cvFileInputRef}
          type="file"
          accept=".pdf,.doc,.docx"
          multiple
          onChange={(e) => { if (e.target.files) onCvFilesSelected(e.target.files) }}
          className="hidden"
        />
        {similarCvFiles.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {similarCvFiles.map((file, index) => (
              <div
                key={file.name}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs"
               
              >
                <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
                <span className="max-w-[150px] truncate">{file.name}</span>
                <button onClick={() => onRemoveCvFile(index)} className="hover:text-status-error">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
            {similarCvFiles.length < MAX_CV_FILES && (
              <button
                onClick={() => cvFileInputRef.current?.click()}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none border border-lia-border-subtle"
               
              >
                <Upload className="w-3 h-3" />
                + CV
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={() => cvFileInputRef.current?.click()}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs text-lia-text-primary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none border border-lia-border-subtle"
           
          >
            <Upload className="w-3.5 h-3.5" />
            Arraste CVs aqui ou clique para upload (máx. 2)
          </button>
        )}
      </div>

      {/* Botão Analisar */}
      {hasMultipleSources() && !showCombinedSuggestions && (
        <button
          onClick={onAnalyzeProfiles}
          disabled={isAnalyzingProfiles}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-medium text-white disabled:opacity-50 bg-lia-btn-primary-bg"
        >
          {isAnalyzingProfiles ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              Analisando perfis...
            </>
          ) : (
            <>
              <Wand2 className="w-3.5 h-3.5" />
              Analisar e combinar perfis com IA
            </>
          )}
        </button>
      )}

      {/* Perfil Ideal Combinado */}
      {showCombinedSuggestions && combinedSuggestions.length > 0 && (
        <div className="p-3 rounded-xl space-y-2 border border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-xs font-medium text-lia-text-primary">Perfil Ideal sugerido pela IA</span>
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-3.5 h-3.5 text-lia-text-secondary" />
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs max-w-[280px]">
                  A IA analisou os perfis e combinou skills, experiências e senioridade em comum. Edite ou remova tags antes de buscar.
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {combinedSuggestions.map((keyword) => (
              <div
                key={keyword}
                className="flex items-center gap-1 px-2 py-1 rounded-xl text-xs font-medium group border border-lia-border-subtle bg-lia-bg-primary"
              >
                <span className="text-lia-text-primary">{keyword}</span>
                <button
                  onClick={() => onRemoveSuggestion(keyword)}
                  className="opacity-50 group-hover:opacity-100 hover:text-status-error transition-opacity motion-reduce:transition-none"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          <p className="text-xs text-lia-text-primary">
            Baseado em {validUrls.length + similarCvFiles.length} perfis: skills em comum e pontos fortes combinados.
          </p>
        </div>
      )}

      {/* Botão Buscar */}
      <button
        onClick={() => onSearch(validUrls)}
        disabled={!hasSource}
        className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed ${hasSource ? 'bg-lia-btn-primary-bg text-white' : 'bg-lia-border-subtle text-lia-text-tertiary'}`}
      >
        <Search className="w-4 h-4" />
        {hasMultipleSources() ? "Buscar com perfil combinado" : "Buscar candidatos similares"}
      </button>

      {/* Dica */}
      <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>Dica:</strong> Cole 1 a 2 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, a IA combina as melhores características e sugere palavras-chave para encontrar candidatos similares.
          </p>
        </div>
      </div>
    </div>
  )
}
