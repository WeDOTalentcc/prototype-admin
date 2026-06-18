"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { AlertTriangle, Database, X, Mail, Phone, Coins, CheckCircle2 } from "lucide-react"
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
import { Button } from "@/components/ui/button"

interface UnsavedCandidate {
  id: string
  name: string
  email?: string | null
  phone?: string | null
  best_personal_email?: string | null
  best_business_email?: string | null
  personal_emails?: string[]
  business_emails?: string[]
}

interface UnsavedPearchWarningModalProps {
  isOpen: boolean
  onClose: () => void
  onSaveAndExit: () => void
  onExitWithoutSaving: () => void
  unsavedCount: number
  unsavedCandidates?: UnsavedCandidate[]
  isSaving?: boolean
}

export function UnsavedPearchWarningModal({
  isOpen,
  onClose,
  onSaveAndExit,
  onExitWithoutSaving,
  unsavedCount,
  unsavedCandidates = [],
  isSaving = false
}: UnsavedPearchWarningModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('unsaved-search-warning', isOpen)

  const candidatesWithEmail = unsavedCandidates.filter(c => 
    c.email || c.best_personal_email || c.best_business_email || 
    (c.personal_emails && c.personal_emails.length > 0) || 
    (c.business_emails && c.business_emails.length > 0)
  ).length
  
  const candidatesWithPhone = unsavedCandidates.filter(c => c.phone).length
  
  const creditsConsumed = unsavedCount
  
  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <AlertDialogContent className="max-w-md rounded-md" data-testid="unsaved-search-warning-modal">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-md bg-status-warning/15 text-status-warning">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold">
              Candidatos não salvos
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-lia-text-primary">
                Você tem <strong className="text-lia-text-primary">{unsavedCount} candidato{unsavedCount > 1 ? 's' : ''}</strong> de busca global que ainda não foram salvos na base local.
              </p>
              
              {unsavedCandidates.length > 0 && (
                <div className="flex items-center gap-4 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                  <div className="flex items-center gap-1.5">
                    <Mail className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-xs text-lia-text-primary">
                      <strong>{candidatesWithEmail}</strong> com email
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-xs text-lia-text-primary">
                      <strong>{candidatesWithPhone}</strong> com telefone
                    </span>
                  </div>
                </div>
              )}
              
              <div className="p-4 rounded-xl bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30">
                <div className="flex items-start gap-3">
                  <Database className="w-5 h-5 text-status-warning mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-status-warning">
                      Você já pagou por esses dados
                    </p>
                    <p className="text-sm text-status-warning mt-1">
                      Salvar na base evita pagar novamente em futuras buscas.
                    </p>
                    <div className="flex items-center gap-1.5 mt-2">
                      <Coins className="w-4 h-4 text-status-warning" />
                      <span className="text-xs font-medium text-status-warning">
                        {creditsConsumed} crédito{creditsConsumed > 1 ? 's' : ''} consumido{creditsConsumed > 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-xs text-lia-text-secondary">
                Recomendamos salvar os candidatos relevantes antes de sair.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2 flex-col sm:flex-row">
          <Button 
            variant="outline" 
            onClick={onExitWithoutSaving}
            className="gap-2 order-3 sm:order-1 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg"
            disabled={isSaving}
          >
            <X className="w-4 h-4" />
            Sair sem salvar
          </Button>
          <Button
            onClick={onSaveAndExit}
            className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active order-1 sm:order-2"
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                Salvando...
              </>
            ) : (
              <>
                <Database className="w-4 h-4" />
                Salvar todos e sair
              </>
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
