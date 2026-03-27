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
      style={{ 
        backgroundColor: "var(--eleven-bg-card)",
        borderColor: "var(--eleven-border)"
      }}
    >
      <CardContent className="p-0">
        <div 
          className="px-4 py-3 border-b flex items-center gap-2"
          style={{ 
            backgroundColor: "var(--eleven-sepia-light)",
            borderColor: "var(--eleven-border)"
          }}
        >
          <Search className="w-4 h-4 text-gray-700" />
          <span 
            className="text-sm font-medium"
            style={{ color: "var(--eleven-text-primary)" }}
          >
            Preview da Busca
          </span>
          {isStillSearching && (
            <Loader2 className="w-4 h-4 animate-spin ml-auto text-gray-700" />
          )}
        </div>

        <div className="p-4 space-y-4">
          <p 
            className="text-sm"
            style={{ color: "var(--eleven-text-secondary)" }}
          >
            Busca: <span className="font-medium" style={{ color: "var(--eleven-text-primary)" }}>"{data.query}"</span>
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
                "flex items-start gap-3 p-3 rounded-md border text-left transition-all",
                selectedOption === "local" && "ring-2",
                !hasLocalResults && !data.isSearchingLocal && "opacity-50 cursor-not-allowed"
              )}
              style={{ 
                backgroundColor: selectedOption === "local" ? "rgb(249, 250, 251)" : "var(--eleven-bg-main)",
                borderColor: selectedOption === "local" ? "rgb(209, 213, 219)" : "var(--eleven-border)"
              }}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{ backgroundColor: "var(--eleven-sepia-mint)" }}
              >
                <Database className="w-4 h-4 text-gray-700" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium"
                    style={{ color: "var(--eleven-text-primary)" }}
                  >
                    Banco Proprietário
                  </span>
                  {data.isSearchingLocal ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-700" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ 
                        backgroundColor: hasLocalResults ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                        color: hasLocalResults ? "var(--status-success)" : "var(--status-error)"
                      }}
                    >
                      {data.localCount} encontrados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1"
                  style={{ color: "var(--eleven-text-tertiary)" }}
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
                "flex items-start gap-3 p-3 rounded-md border text-left transition-all",
                selectedOption === "hybrid" && "ring-2",
                !hasPearchResults && !data.isEstimatingPearch && "opacity-50 cursor-not-allowed"
              )}
              style={{ 
                backgroundColor: selectedOption === "hybrid" ? "rgb(249, 250, 251)" : "var(--eleven-bg-main)",
                borderColor: selectedOption === "hybrid" ? "rgb(209, 213, 219)" : "var(--eleven-border)"
              }}
            >
              <div 
                className="p-2 rounded-md shrink-0"
                style={{ backgroundColor: "var(--eleven-sepia-light)" }}
              >
                <Globe className="w-4 h-4 text-gray-700" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span 
                    className="text-sm font-medium"
                    style={{ color: "var(--eleven-text-primary)" }}
                  >
                    Busca Híbrida (Local + Global)
                  </span>
                  {data.isEstimatingPearch ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-700" />
                  ) : (
                    <span 
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ 
                        backgroundColor: "rgb(243, 244, 246)",
                        color: "rgb(55, 65, 81)"
                      }}
                    >
                      ~{data.pearchEstimate} estimados
                    </span>
                  )}
                </div>
                <p 
                  className="text-xs mt-1"
                  style={{ color: "var(--eleven-text-tertiary)" }}
                >
                  Inclui acesso a 800M+ perfis do banco global
                </p>
                {hasPearchResults && (
                  <div 
                    className="flex items-center gap-1 mt-2 text-xs"
                    style={{ color: canAffordPearch ? "var(--gray-950)" : "var(--status-error)" }}
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
              style={{ 
                backgroundColor: "var(--eleven-sepia-mint)",
                color: "var(--eleven-text-primary)"
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span>Custo estimado:</span>
                <span className="font-semibold text-gray-700">
                  {data.pearchCredits} créditos
                </span>
              </div>
              <div className="flex items-center justify-between text-xs" style={{ color: "var(--eleven-text-secondary)" }}>
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
              style={{ 
                color: "var(--eleven-text-secondary)",
                borderColor: "var(--eleven-border)"
              }}
            >
              <X className="w-4 h-4 mr-1" />
              Cancelar
            </Button>
            
            {selectedOption === "hybrid" ? (
              <Button
                size="sm"
                onClick={onConfirmHybrid}
                disabled={!canAffordPearch || isStillSearching}
                className="flex-1 bg-gray-900" style={{ color: "white" }}
              >
                <Check className="w-4 h-4 mr-1" />
                Confirmar Busca
              </Button>
            ) : selectedOption === "local" && hasLocalResults ? (
              <Button
                size="sm"
                onClick={onProceedLocalOnly}
                className="flex-1 bg-gray-900" style={{ color: "white" }}
              >
                <Check className="w-4 h-4 mr-1" />
                Ver {data.localCount} Candidatos
              </Button>
            ) : (
              <Button
                size="sm"
                disabled
                className="flex-1"
                style={{ 
                  backgroundColor: "var(--eleven-bg-tertiary)",
                  color: "var(--eleven-text-secondary)"
                }}
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
