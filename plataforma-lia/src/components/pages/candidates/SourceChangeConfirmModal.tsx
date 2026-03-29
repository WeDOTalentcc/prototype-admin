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
      <AlertDialogContent className="sm:max-w-[320px] w-[85vw] p-4 border border-gray-100 dark:border-gray-700" style={{borderRadius: '10px'}}>
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${pendingSourceChange === 'hybrid' ? 'bg-wedo-cyan/15' : 'bg-status-warning/15'}`}>
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-4 h-4 text-gray-700" />
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

          <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-3 space-y-2 border border-gray-100 dark:border-gray-700">
            <div className="flex justify-between items-center text-xs">
              <span className={textStyles.bodySmall}>Tipo de busca:</span>
              <span className={`${textStyles.label} text-gray-800 dark:text-gray-200`}>{pendingSourceChange === 'hybrid' ? 'Híbrido' : 'Global'}</span>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className={`${textStyles.label} text-gray-800 dark:text-gray-200`}>Custo por candidato:</span>
                <span className="font-semibold text-gray-700 dark:text-gray-300">
                  1 crédito
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-micro text-status-warning bg-status-warning/10 p-2 rounded-md">
            <AlertCircle className="w-3 h-3 flex-shrink-0" />
            <span>Cada candidato da base global consumirá 1 crédito.</span>
          </div>
        </div>

        <div className="flex gap-2.5 pt-3">
          <button
            onClick={onCancel}
            className="flex-1 h-8 text-xs px-3 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors hover:opacity-90 bg-gray-900"
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
