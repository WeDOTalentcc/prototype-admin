"use client"

import { useState } from "react"
import { Database, Globe, Loader2, Search, Zap, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface SearchPreviewData {
  query: string
  localCount: number
  pearchEstimate: number
  pearchCredits: number
  isSearchingLocal?: boolean
  isEstimatingPearch?: boolean
}

export interface SearchPreviewCardProps {
  data: SearchPreviewData
  onConfirmHybrid: () => void
  onProceedLocalOnly: () => void
  onCancel: () => void
  availableCredits: number
}

export function SearchPreviewCard({
  data,
  onConfirmHybrid,
  onProceedLocalOnly,
  onCancel,
  availableCredits
}: SearchPreviewCardProps) {
  const [selectedOption, setSelectedOption] = useState<"hybrid" | "local" | null>(null)
  
  const hasLocalResults = data.localCount > 0
  const hasPearchResults = data.pearchEstimate > 0
  const canAffordPearch = availableCredits >= data.pearchCredits
  const isStillSearching = data.isSearchingLocal || data.isEstimatingPearch

  return (
    <Card 
      className="border overflow-hidden"
      style={{backgroundColor: 'var(--white)',
        borderColor: 'var(--lia-border-subtle)'}}
    >
      <CardContent className="p-0">
        <div 
          className="px-4 py-3 border-b flex items-center gap-2"
          style={{backgroundColor: 'var(--lia-bg-secondary)',
            borderColor: 'var(--lia-border-subtle)'}}
        >
          <Search className="w-4 h-4 text-lia-text-primary" />
          <span 
            className="text-sm font-medium text-lia-text-primary"
          >
            Preview da Busca
          </span>
          {isStillSearching && (
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none ml-auto text-lia-text-primary" />
          )}
        </div>

        <div className="p-4 space-y-4">
          <p 
            className="text-sm text-lia-text-secondary"
          >
            Busca: <span className="font-medium text-lia-text-primary">"{data.query}"</span>
          </p>

          <div className="grid gap-3">
            <button
              onClick={() => {
                setSelectedOption("local")
                if (hasLocalResults) {
                  onProceedLocalOnly()
                }
              }}
              disabled={!hasLocalResults && !data.isSearchingLocal}
              className={cn(
                "flex items-start gap-3 p-3 rounded-md border text-left transition-colors",
                selectedOption === "local" && "ring-2",
                !hasLocalResults && !data.isSearchingLocal && "opacity-50 cursor-not-allowed"
              )}
              style={{backgroundColor: selectedOption === "local" ? "var(--lia-bg-secondary)" : 'var(--lia-bg-secondary)',
                borderColor: selectedOption === "local" ? "var(--lia-border-default)" : 'var(--lia-border-subtle)'}}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{backgroundColor: "var(--wedo-green-light, #f0fdf4)"}}
              >
                <Database className="w-4 h-4 text-lia-text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium text-lia-text-primary"
                  >
                    Banco Proprietário
                  </span>
                  {data.isSearchingLocal ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-primary" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{backgroundColor: hasLocalResults ? "var(--status-success-bg)" : "var(--status-error-bg)",
                        color: hasLocalResults ? "var(--status-success)" : "var(--status-error)"}}
                     aria-live="polite" aria-atomic="true">
                      {data.localCount} encontrados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1 text-lia-text-tertiary"
                 aria-live="polite" aria-atomic="true">
                  Candidatos já cadastrados na sua base - sem custo
                </p>
              </div>
            </button>

            <button
              onClick={() => {
                setSelectedOption("hybrid")
              }}
              disabled={!hasPearchResults && !data.isEstimatingPearch}
              className={cn(
                "flex items-start gap-3 p-3 rounded-md border text-left transition-colors",
                selectedOption === "hybrid" && "ring-2",
                !hasPearchResults && !data.isEstimatingPearch && "opacity-50 cursor-not-allowed"
              )}
              style={{backgroundColor: selectedOption === "hybrid" ? "var(--lia-bg-secondary)" : 'var(--lia-bg-secondary)',
                borderColor: selectedOption === "hybrid" ? "var(--lia-border-default)" : 'var(--lia-border-subtle)'}}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{backgroundColor: 'var(--lia-bg-secondary)'}}
              >
                <Globe className="w-4 h-4 text-lia-text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium text-lia-text-primary"
                  >
                    Busca Híbrida (Local + Global)
                  </span>
                  {data.isEstimatingPearch ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-primary" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full bg-lia-bg-tertiary text-lia-text-primary"
                    >
                      ~{data.pearchEstimate} estimados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1 text-lia-text-tertiary"
                >
                  Inclui acesso a 800M+ perfis do banco global
                </p>
                {hasPearchResults && (
                  <div 
                    className="flex items-center gap-1 mt-2 text-xs"
                    style={{color: canAffordPearch ? "var(--lia-btn-primary-bg)" : "var(--status-error)"}}
                  >
                    <Zap className="w-3 h-3" />
                    <span>
                      {data.pearchCredits} créditos 
                      {!canAffordPearch && " (saldo insuficiente)"}
                    </span>
                  </div>
                )}
              </div>
            </button>
          </div>

          {selectedOption === "hybrid" && (
            <div 
              className="p-3 rounded-md text-sm"
              style={{backgroundColor: "var(--wedo-green-light, #f0fdf4)",
                color: 'var(--lia-text-primary)'}}
            >
              <div className="flex items-center justify-between mb-2">
                <span>Custo estimado:</span>
                <span className="font-semibold text-lia-text-primary">
                  {data.pearchCredits} créditos
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-lia-text-secondary">
                <span>Saldo após busca:</span>
                <span>{Math.max(0, availableCredits - data.pearchCredits)} créditos</span>
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onCancel}
              className="flex-1"
              style={{color: 'var(--lia-text-secondary)',
                borderColor: 'var(--lia-border-subtle)'}}
            >
              <X className="w-4 h-4 mr-1" />
              Cancelar
            </Button>
            
            {selectedOption === "hybrid" ? (
              <Button
                size="sm"
                onClick={onConfirmHybrid}
                disabled={!canAffordPearch || isStillSearching}
                className="flex-1 bg-lia-btn-primary-bg text-lia-btn-primary-text"
              >
                <Check className="w-4 h-4 mr-1" />
                Confirmar Busca
              </Button>
            ) : selectedOption === "local" && hasLocalResults ? (
              <Button
                size="sm"
                onClick={onProceedLocalOnly}
                className="flex-1 bg-lia-btn-primary-bg text-lia-btn-primary-text"
              >
                <Check className="w-4 h-4 mr-1" />
                Ver {data.localCount} Candidatos
              </Button>
            ) : (
              <Button
                size="sm"
                disabled
                className="flex-1"
                style={{backgroundColor: 'var(--lia-bg-tertiary)',
                  color: 'var(--lia-text-secondary)'}}
              >
                Selecione uma opção
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default SearchPreviewCard
