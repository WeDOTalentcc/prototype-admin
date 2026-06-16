"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent } from"@/components/ui/card"
import {
  AlertCircle, ExternalLink, Building, MapPin, Loader2
} from"lucide-react"
import type { DuplicateCheckResult } from '@/services/duplicate-detection-service'

interface DuplicateFoundStepProps {
  duplicateResult: DuplicateCheckResult | null
  isProcessing: boolean
  onOpenExisting: () => void
  onCreateAnyway: () => Promise<void>
  onBack: () => void
}

export function DuplicateFoundStep({
  duplicateResult,
  isProcessing,
  onOpenExisting,
  onCreateAnyway,
  onBack,
}: DuplicateFoundStepProps) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <div className="w-12 h-12 rounded-full bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center mx-auto mb-3">
          <AlertCircle className="w-6 h-6 text-status-warning" />
        </div>
        <h3 className="text-sm font-semibold text-lia-text-primary">
          Candidato já existe
        </h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          {duplicateResult?.message}
        </p>
      </div>

      {duplicateResult?.candidate && (
        <Card className="border-status-warning/30 dark:border-status-warning/30 bg-status-warning/10/50 dark:bg-status-warning/20 rounded-md">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-lia-btn-primary-bg flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
                {duplicateResult.candidate.name?.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary">
                  {duplicateResult.candidate.name}
                </p>
                {duplicateResult.candidate.current_title && (
                  <p className="text-xs text-lia-text-secondary mt-0.5">
                    {duplicateResult.candidate.current_title}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {duplicateResult.candidate.current_company && (
                    <Chip variant="neutral" className="text-micro py-0 px-1.5">
                      <Building className="w-2.5 h-2.5 mr-1" />
                      {duplicateResult.candidate.current_company}
                    </Chip>
                  )}
                  {duplicateResult.candidate.location_city && (
                    <Chip variant="neutral" className="text-micro py-0 px-1.5">
                      <MapPin className="w-2.5 h-2.5 mr-1" />
                      {duplicateResult.candidate.location_city}
                    </Chip>
                  )}
                </div>
                {duplicateResult.matchType && (
                  <p className="text-micro text-status-warning mt-2">
                    Encontrado por: {
                      duplicateResult.matchType === 'email' ? 'E-mail' :
                      duplicateResult.matchType === 'phone' ? 'Telefone' :
                      duplicateResult.matchType === 'linkedin' ? 'LinkedIn' :
                      duplicateResult.matchType === 'name_similarity' ? 'Nome similar' :
                      duplicateResult.matchType
                    }
                    {duplicateResult.confidence < 1 && ` (${Math.round(duplicateResult.confidence * 100)}% similar)`}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-2">
        <Button
          onClick={onOpenExisting}
          className="w-full h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
        >
          <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
          Abrir Perfil Existente
        </Button>
        <Button
          onClick={onCreateAnyway}
          variant="outline"
          className="w-full h-9 text-xs"
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
              Cadastrando...
            </>
          ) : ("Cadastrar Mesmo Assim"
          )}
        </Button>
        <Button
          onClick={onBack}
          variant="ghost"
          className="w-full h-9 text-xs text-lia-text-tertiary"
        >
          Voltar
        </Button>
      </div>
    </div>
  )
}
