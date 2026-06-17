"use client"

import React from "react"
import { Progress } from "@/components/ui/progress"
import { Brain, Loader2, CheckCircle } from "lucide-react"
import type { InputTab } from "./new-candidate-unified-types"

interface ProcessingStepProps {
  isEnriching: boolean
  activeTab: InputTab
  uploadProgress: number
}

export function ProcessingStep({ isEnriching, activeTab, uploadProgress }: ProcessingStepProps) {
  return (
    <div className="py-8 text-center" role="status" aria-live="polite" aria-label="Carregando...">
      <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-4" role="status" aria-live="polite" aria-label="Carregando...">
        {isEnriching ? (
          <Brain className="w-6 h-6 text-wedo-cyan animate-pulse motion-reduce:animate-none" />
        ) : (
          <Loader2 className="w-6 h-6 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
        )}
      </div>
      <h3 className="text-sm font-semibold text-lia-text-primary mb-2">
        {isEnriching ? 'Enriquecendo perfil...' : 'Processando...'}
      </h3>
      <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
        {isEnriching
          ? 'Buscando dados adicionais via LinkedIn...'
          : activeTab === 'cv'
            ? 'Extraindo dados do CV com IA...'
            : 'Verificando e cadastrando candidato...'
        }
      </p>
      {uploadProgress > 0 && !isEnriching && (
        <Progress value={uploadProgress} className="max-w-sidebar-content mx-auto h-1.5 mt-4" />
      )}
    </div>
  )
}

export function SuccessStep() {
  return (
    <div className="py-8 text-center">
      <div className="w-12 h-12 rounded-full bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center mx-auto mb-4">
        <CheckCircle className="w-6 h-6 text-status-success" />
      </div>
      <h3 className="text-sm font-semibold text-lia-text-primary mb-2">
        Candidato cadastrado!
      </h3>
      <p className="text-xs text-lia-text-secondary">
        Abrindo perfil completo...
      </p>
    </div>
  )
}
