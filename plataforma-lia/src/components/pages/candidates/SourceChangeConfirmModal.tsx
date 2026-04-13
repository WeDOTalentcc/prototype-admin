"use client"

import { Globe, AlertCircle, Zap } from "lucide-react"
import { AlertDialog, AlertDialogContent } from "@/components/ui/alert-dialog"
import { textStyles } from "@/lib/design-tokens"

interface SourceChangeConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  onCancel: () => void
  onConfirm: () => void
}

export function SourceChangeConfirmModal({
  open,
  onOpenChange,
  pendingSourceChange,
  onCancel,
  onConfirm,
}: SourceChangeConfirmModalProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="source-change-confirm-modal" className="sm:max-w-[320px] w-[85vw] p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${pendingSourceChange === 'hybrid' ? 'bg-wedo-cyan/15' : 'bg-status-warning/15'}`}>
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-4 h-4 text-lia-text-secondary" />
              ) : (
                <Globe className="w-4 h-4 text-status-warning" />
              )}
            </div>
            <div>
              <h3 className={textStyles.title}>
                {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
              </h3>
              <p className={textStyles.caption}>
                {pendingSourceChange === 'hybrid'
                  ? 'Combina base local + global (800M+ perfis).'
                  : 'Acessa 800M+ perfis profissionais.'}
              </p>
            </div>
          </div>

          <div className="bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl p-3 space-y-2 border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex justify-between items-center text-xs">
              <span className={textStyles.bodySmall}>Tipo de busca:</span>
              <span className={`${textStyles.label} text-lia-text-primary`}>{pendingSourceChange === 'hybrid' ? 'Híbrido' : 'Global'}</span>
            </div>
            <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className={`${textStyles.label} text-lia-text-primary`}>Custo por candidato:</span>
                <span className="font-semibold text-lia-text-secondary">
                  1 cred + $0.01 Apify
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-micro text-status-info bg-status-info/10 p-2 rounded-md">
            <AlertCircle className="w-3 h-3 flex-shrink-0" />
            <span>Cada candidato custa 1 crédito base + $0.01 de enriquecimento Apify.</span>
          </div>
        </div>

        <div className="flex gap-2.5 pt-3">
          <button
            onClick={onCancel}
            className="flex-1 h-8 text-xs px-3 rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse font-medium transition-colors motion-reduce:transition-none"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors motion-reduce:transition-none hover:opacity-90 bg-lia-btn-primary-bg"
          >
            {pendingSourceChange === 'hybrid' ? (
              <>
                <Zap className="w-3.5 h-3.5" />
                Ativar
              </>
            ) : (
              <>
                <Globe className="w-3.5 h-3.5" />
                Ativar
              </>
            )}
          </button>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  )
}
