"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  CheckCircle, Activity, Bell, Mail, Download, Share2,
} from "lucide-react"
import type { BatchResults } from "@/hooks/candidates/use-batch-approval"

interface BatchProcessingStepProps {
  selectedCount: number
}

export function BatchProcessingStep({ selectedCount }: BatchProcessingStepProps) {
  return (
    <div className="p-6 h-full flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-lia-btn-primary-bg border-t-transparent rounded-full animate-spin motion-reduce:animate-none mx-auto mb-4"></div>
        <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
          Processando Aprovação em Lote
        </h3>
        <p className="text-lia-text-secondary mb-4">
          Aplicando ações para {selectedCount} candidatos...
        </p>
        <div className="space-y-2 text-sm text-lia-text-secondary">
          <div className="flex items-center justify-center gap-2">
            <Activity className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
            Atualizando status dos candidatos
          </div>
          <div className="flex items-center justify-center gap-2">
            <Bell className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
            Enviando notificações
          </div>
          <div className="flex items-center justify-center gap-2">
            <Mail className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
            Enviando emails automáticos
          </div>
        </div>
      </div>
    </div>
  )
}

interface BatchCompleteStepProps {
  results: BatchResults
  onApprovalComplete: (results: Record<string, unknown>) => void
  onClose: () => void
}

export function BatchCompleteStep({ results, onApprovalComplete, onClose }: BatchCompleteStepProps) {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto text-center">
        <div className="w-16 h-16 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-status-success" />
        </div>

        <h3 className="text-xl font-semibold text-lia-text-primary mb-2">
          Aprovação em Lote Concluída!
        </h3>

        <p className="text-lia-text-secondary mb-8">
          {results.total} candidatos foram processados com sucesso
        </p>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-semibold text-lia-text-primary mb-2">{results.total}</div>
              <div className="text-sm text-lia-text-secondary">Total Processados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-semibold text-status-success mb-2">{results.approved}</div>
              <div className="text-sm text-lia-text-secondary">Aprovados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-semibold text-status-error mb-2">{results.rejected}</div>
              <div className="text-sm text-lia-text-secondary">Rejeitados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-semibold text-lia-text-primary mb-2">{results.moved}</div>
              <div className="text-sm text-lia-text-secondary">Movidos</div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-center gap-4">
          <Button
            onClick={() => onApprovalComplete(results as unknown as Record<string, unknown>)}
            className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            <Download className="w-4 h-4" />
            Baixar Relatório
          </Button>

          <Button
            variant="outline"
            className="gap-2"
          >
            <Share2 className="w-4 h-4" />
            Compartilhar Resultados
          </Button>

          <Button
            variant="outline"
            onClick={onClose}
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
