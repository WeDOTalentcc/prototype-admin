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
        borderColor: 'var(--gray-300)'}}
    >
      <CardContent className="p-0">
        <div 
          className="px-4 py-3 border-b flex items-center gap-2"
          style={{backgroundColor: 'var(--gray-50)',
            borderColor: 'var(--gray-300)'}}
        >
          <Search className="w-4 h-4 lia-text-700" />
          <span 
            className="text-sm font-medium lia-text-800 dark:text-lia-text-primary"
          >
            Preview da Busca
          </span>
          {isStillSearching && (
            <Loader2 className="w-4 h-4 animate-spin ml-auto lia-text-700" />
          )}
        </div>

        <div className="p-4 space-y-4">
          <p 
            className="text-sm lia-text-500 dark:text-lia-text-tertiary"
          >
            Busca: <span className="font-medium lia-text-800 dark:text-lia-text-primary">"{data.query}"</span>
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
              style={{backgroundColor: selectedOption === "local" ? "rgb(249, 250, 251)" : 'var(--gray-50)',
                borderColor: selectedOption === "local" ? "rgb(209, 213, 219)" : 'var(--gray-300)'}}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{backgroundColor: "var(--green-50, #f0fdf4)"}}
              >
                <Database className="w-4 h-4 lia-text-700" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium lia-text-800 dark:text-lia-text-primary"
                  >
                    Banco Proprietário
                  </span>
                  {data.isSearchingLocal ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin lia-text-700" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{backgroundColor: hasLocalResults ? "var(--status-success-bg)" : "var(--status-error-bg)",
                        color: hasLocalResults ? "var(--status-success)" : "var(--status-error)"}}
                    >
                      {data.localCount} encontrados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1 lia-text-400 dark:lia-text-500"
                >
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
              style={{backgroundColor: selectedOption === "hybrid" ? "rgb(249, 250, 251)" : 'var(--gray-50)',
                borderColor: selectedOption === "hybrid" ? "rgb(209, 213, 219)" : 'var(--gray-300)'}}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{backgroundColor: 'var(--gray-50)'}}
              >
                <Globe className="w-4 h-4 lia-text-700" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium lia-text-800 dark:text-lia-text-primary"
                  >
                    Busca Híbrida (Local + Global)
                  </span>
                  {data.isEstimatingPearch ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin lia-text-700" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 lia-text-700"
                    >
                      ~{data.pearchEstimate} estimados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1 lia-text-400 dark:lia-text-500"
                >
                  Inclui acesso a 800M+ perfis do banco global
                </p>
                {hasPearchResults && (
                  <div 
                    className="flex items-center gap-1 mt-2 text-xs"
                    style={{color: canAffordPearch ? "var(--gray-950)" : "var(--status-error)"}}
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
              style={{backgroundColor: "var(--green-50, #f0fdf4)",
                color: 'var(--gray-800)'}}
            >
              <div className="flex items-center justify-between mb-2">
                <span>Custo estimado:</span>
                <span className="font-semibold lia-text-700">
                  {data.pearchCredits} créditos
                </span>
              </div>
              <div className="flex items-center justify-between text-xs lia-text-500 dark:text-lia-text-tertiary">
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
              style={{color: 'var(--gray-500)',
                borderColor: 'var(--gray-300)'}}
            >
              <X className="w-4 h-4 mr-1" />
              Cancelar
            </Button>
            
            {selectedOption === "hybrid" ? (
              <Button
                size="sm"
                onClick={onConfirmHybrid}
                disabled={!canAffordPearch || isStillSearching}
                className="flex-1 bg-gray-900 text-white"
              >
                <Check className="w-4 h-4 mr-1" />
                Confirmar Busca
              </Button>
            ) : selectedOption === "local" && hasLocalResults ? (
              <Button
                size="sm"
                onClick={onProceedLocalOnly}
                className="flex-1 bg-gray-900 text-white"
              >
                <Check className="w-4 h-4 mr-1" />
                Ver {data.localCount} Candidatos
              </Button>
            ) : (
              <Button
                size="sm"
                disabled
                className="flex-1"
                style={{backgroundColor: 'var(--gray-100)',
                  color: 'var(--gray-500)'}}
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
