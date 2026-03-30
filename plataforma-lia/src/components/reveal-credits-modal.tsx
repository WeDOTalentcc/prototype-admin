"use client"

import { useState } from "react"
import { Mail, Phone, AlertTriangle, CreditCard, Loader2, Check, X } from "lucide-react"
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

interface RevealCreditsModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  revealType: "email" | "phone"
  candidateName: string
  creditsRequired: number
}

export function RevealCreditsModal({
  isOpen,
  onClose,
  onConfirm,
  revealType,
  candidateName,
  creditsRequired
}: RevealCreditsModalProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      await onConfirm()
    } finally {
      setIsLoading(false)
    }
  }

  const Icon = revealType === "email" ? Mail : Phone
  const typeLabel = revealType === "email" ? "email" : "telefone"

  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <AlertDialogContent 
        className="max-w-md bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
       
      >
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-md bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary">
              <Icon className="w-5 h-5" />
            </div>
            <AlertDialogTitle className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary">
              Revelar {typeLabel}
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                Deseja revelar o {typeLabel} de <strong className="text-lia-text-primary">{candidateName}</strong>?
              </p>
              
              <div className="p-4 rounded-md bg-status-warning/10 border border-status-warning/30">
                <div className="flex items-start gap-3">
                  <CreditCard className="w-5 h-5 text-status-warning mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-status-warning">
                      Custo: {creditsRequired} créditos
                    </p>
                    <p className="text-sm text-status-warning mt-1">
                      {revealType === "email" 
                        ? "O custo será cobrado apenas se o candidato tiver email disponível."
                        : "O custo será cobrado apenas se o candidato tiver telefone disponível."}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2 text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">
                <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                <span>Esta ação consumirá créditos da sua conta.</span>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2">
          <AlertDialogCancel asChild>
            <Button 
              variant="outline" 
              disabled={isLoading} 
              className="gap-2 bg-white border border-lia-border-default hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 text-lia-text-primary dark:text-lia-text-primary"
            >
              <X className="w-4 h-4" />
              Cancelar
            </Button>
          </AlertDialogCancel>
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Revelando...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Confirmar ({creditsRequired} créditos)
              </>
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
