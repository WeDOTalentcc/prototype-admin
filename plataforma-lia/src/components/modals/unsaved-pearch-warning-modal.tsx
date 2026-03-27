"use client"

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
  const candidatesWithEmail = unsavedCandidates.filter(c => 
    c.email || c.best_personal_email || c.best_business_email || 
    (c.personal_emails && c.personal_emails.length > 0) || 
    (c.business_emails && c.business_emails.length > 0)
  ).length
  
  const candidatesWithPhone = unsavedCandidates.filter(c => c.phone).length
  
  const creditsConsumed = unsavedCount
  
  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <AlertDialogContent className="max-w-md rounded-md dark:bg-gray-800 dark:border-gray-700">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-md bg-amber-100 text-amber-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold">
              Candidatos não salvos
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-gray-800 dark:text-gray-200">
                Você tem <strong className="text-gray-950 dark:text-gray-50">{unsavedCount} candidato{unsavedCount > 1 ? 's' : ''}</strong> de busca global que ainda não foram salvos na base local.
              </p>
              
              {unsavedCandidates.length > 0 && (
                <div className="flex items-center gap-4 p-3 rounded-md bg-gray-50 border border-gray-200 dark:bg-gray-700 dark:border-gray-600">
                  <div className="flex items-center gap-1.5">
                    <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">
                      <strong>{candidatesWithEmail}</strong> com email
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">
                      <strong>{candidatesWithPhone}</strong> com telefone
                    </span>
                  </div>
                </div>
              )}
              
              <div className="p-4 rounded-md bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <div className="flex items-start gap-3">
                  <Database className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-amber-800 dark:text-amber-200">
                      Você já pagou por esses dados
                    </p>
                    <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                      Salvar na base evita pagar novamente em futuras buscas.
                    </p>
                    <div className="flex items-center gap-1.5 mt-2">
                      <Coins className="w-4 h-4 text-amber-600" />
                      <span className="text-xs font-medium text-amber-700">
                        {creditsConsumed} crédito{creditsConsumed > 1 ? 's' : ''} consumido{creditsConsumed > 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-600 dark:text-gray-400">
                LIA recomenda salvar os candidatos relevantes antes de sair.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2 flex-col sm:flex-row">
          <Button 
            variant="outline" 
            onClick={onExitWithoutSaving}
            className="gap-2 order-3 sm:order-1 bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
            disabled={isSaving}
          >
            <X className="w-4 h-4" />
            Sair sem salvar
          </Button>
          <Button
            onClick={onSaveAndExit}
            className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 order-1 sm:order-2"
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
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
