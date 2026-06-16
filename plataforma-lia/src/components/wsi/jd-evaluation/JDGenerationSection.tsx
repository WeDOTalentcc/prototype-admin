"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Brain, Check, Copy, FileText, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface GeneratedJD {
  full_description: string
  sections: Record<string, string>
  summary: string
  tags: string[]
}

interface JDGenerationSectionProps {
  generatedJD: GeneratedJD | null
  isGeneratingJD: boolean
  jdGenerationStep: number
  jdTypedMessage: string
  jdDynamicMessage: string
  jdGenerationError?: string | null
  copiedJD: boolean
  isSavingWithJD: boolean
  onGenerate: () => void
  onCopy: () => void
  onSaveAndUpdateJD: () => void
  showSaveAndUpdate: boolean
}

function formatJDText(text: string): React.ReactNode {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i].trim()

    if (!line) {
      elements.push(<div key={i} className="h-2" />)
      i++
      continue
    }

    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={i} className="text-xs font-semibold text-lia-text-primary mt-3 mb-1">
          {line.replace('### ', '')}
        </h4>
      )
    } else if (line.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="text-base-ui font-semibold text-lia-text-primary mt-4 mb-1.5">
          {line.replace('## ', '')}
        </h3>
      )
    } else if (line.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="text-sm font-semibold text-lia-text-primary mb-2">
          {line.replace('# ', '')}
        </h2>
      )
    } else if (line.startsWith('- ')) {
      elements.push(
        <div key={i} className="flex items-start gap-2 ml-1 mb-0.5">
          <span className="text-micro text-lia-text-secondary mt-1">•</span>
          <span className="text-xs text-lia-text-secondary leading-relaxed">
            {line.replace('- ', '')}
          </span>
        </div>
      )
    } else {
      elements.push(
        <p key={i} className="text-xs text-lia-text-secondary leading-relaxed mb-1">
          {line}
        </p>
      )
    }
    i++
  }

  return elements
}

export const JDGenerationSection = React.memo(function JDGenerationSection({
  generatedJD,
  isGeneratingJD,
  jdGenerationStep,
  jdTypedMessage,
  jdDynamicMessage,
  jdGenerationError,
  copiedJD,
  isSavingWithJD,
  onGenerate,
  onCopy,
  onSaveAndUpdateJD,
  showSaveAndUpdate,
}: JDGenerationSectionProps) {
  return (
    <div className="sticky top-0 self-start">
      <div className="flex items-center justify-between mb-2">
        <label className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">
          Descrição Gerada pela IA
        </label>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "h-7 text-xs px-3 transition-colors",
            isGeneratingJD
              ? "bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg"
              : "bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
          )}
          onClick={onGenerate}
          disabled={isGeneratingJD}
        >
          {isGeneratingJD ? (
            <Loader2 className="h-3 w-3 mr-1.5 animate-spin motion-reduce:animate-none" />
          ) : (
            <Brain className="h-3 w-3 mr-1.5 text-wedo-cyan" />
          )}
          {isGeneratingJD ? 'Gerando...' : 'Gerar Descrição'}
        </Button>
      </div>

      <div
        className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle overflow-hidden min-h-chart-sm"
        role="status"
        aria-live="polite"
        aria-label="Carregando..."
      >
        {/* Loading state */}
        {isGeneratingJD && (
          <div className="p-4 space-y-3" role="status" aria-live="polite" aria-label="Carregando...">
            <div className="flex items-center gap-3" role="status" aria-live="polite" aria-label="Carregando...">
              <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-lia-bg-tertiary">
                <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-lia-text-primary">
                  Gerando Descrição do Cargo...
                </p>
                <p className="text-micro text-lia-text-secondary mt-0.5">
                  Etapa {jdGenerationStep} de 4
                </p>
              </div>
            </div>
            {jdTypedMessage && (
              <div className="flex items-center gap-2 pl-1">
                <div className="w-1.5 h-1.5 rounded-full bg-lia-btn-primary-bg animate-pulse motion-reduce:animate-none" />
                <p className="text-xs text-lia-text-secondary">
                  {jdTypedMessage}
                  {jdTypedMessage.length < jdDynamicMessage.length && (
                    <span className="inline-block w-[2px] h-[13px] bg-lia-btn-primary-bg ml-0.5 align-middle animate-pulse motion-reduce:animate-none" />
                  )}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Generated content */}
        {generatedJD && !isGeneratingJD && (
          <div className="max-h-content-lg overflow-y-auto p-4">
            {jdGenerationError && (
              <p
                role="alert"
                className="text-xs text-destructive mb-3 p-2 rounded-md bg-destructive/10"
              >
                {jdGenerationError}
              </p>
            )}
            {formatJDText(generatedJD.full_description)}

            {generatedJD.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-4 mt-3 border-t border-lia-border-subtle">
                {generatedJD.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="pt-3 space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full h-7 text-xs border-lia-border-subtle text-lia-text-secondary"
                onClick={onCopy}
              >
                {copiedJD ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copiado!
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copiar Descrição
                  </>
                )}
              </Button>

              {showSaveAndUpdate && (
                <Button
                  size="sm"
                  className="w-full h-7 text-micro px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                  onClick={onSaveAndUpdateJD}
                  disabled={isSavingWithJD}
                >
                  {isSavingWithJD ? (
                    <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" />
                  ) : (
                    <FileText className="h-3 w-3 mr-1" />
                  )}
                  Salvar e Atualizar JD
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!generatedJD && !isGeneratingJD && (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <Brain className="h-6 w-6 mb-2 text-wedo-cyan" />
            {jdGenerationError ? (
              <p
                role="alert"
                className="text-xs text-destructive text-center max-w-prose"
              >
                {jdGenerationError}
              </p>
            ) : (
              <p className="text-xs text-lia-text-muted text-center">
                Descrição gerada pela IA aparecerá aqui
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
})

export default JDGenerationSection
