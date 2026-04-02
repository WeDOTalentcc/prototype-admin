"use client"

import { Globe, AlertCircle, Loader2 } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface GlobalExpansionConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  lastSuccessfulQuery: string | null
  lastSearchQuery: string | null
  localResultsCount: number
  isExpandingToGlobal: boolean
  onConfirm: () => void
}

export function GlobalExpansionConfirmModal({
  open,
  onOpenChange,
  lastSuccessfulQuery,
  lastSearchQuery,
  localResultsCount,
  isExpandingToGlobal,
  onConfirm,
}: GlobalExpansionConfirmModalProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-wedo-cyan/15">
              <Globe className="w-4 h-4 text-lia-text-secondary" />
            </div>
            Expandir para Busca Global
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary" aria-live="polite" aria-atomic="true">
              A Busca Global encontra candidatos além da sua base local em um pool de mais de 800 milhões de perfis profissionais.
            </p>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md p-4 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary">Busca atual:</span>
                <span className="font-medium text-xs max-w-sidebar-content truncate">{lastSuccessfulQuery || lastSearchQuery || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">Resultados locais:</span>
                <span className="font-medium" aria-live="polite" aria-atomic="true">{localResultsCount} candidatos</span>
              </div>
              <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium" aria-live="polite" aria-atomic="true">Custo por candidato:</span>
                  <span className="font-bold text-lg text-lia-text-secondary">
                    1 crédito
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-status-warning dark:text-status-warning bg-status-warning/10 dark:bg-status-warning/20 p-2 rounded-md">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span aria-live="polite" aria-atomic="true">Você será cobrado apenas pelos candidatos que visualizar/revelar contatos.</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => onOpenChange(false)}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isExpandingToGlobal}
            className="text-white gap-2 bg-lia-btn-primary-bg"
          >
            {isExpandingToGlobal ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                Expandindo...
              </>
            ) : (
              <>
                <Globe className="w-4 h-4" />
                Expandir Busca
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
