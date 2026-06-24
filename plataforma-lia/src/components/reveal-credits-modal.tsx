"use client"

import { useState } from "react"
import { Mail, Phone, CreditCard, Loader2, Check, X, Info } from "lucide-react"
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
        className="max-w-md bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle"
       
      >
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">
              <Icon className="w-5 h-5" />
            </div>
            <AlertDialogTitle className="text-base-ui font-semibold text-lia-text-primary">
              Revelar {typeLabel}
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-lia-text-secondary">
                Deseja revelar o {typeLabel} de <strong className="text-lia-text-primary">{candidateName}</strong>?
              </p>
              
              <div className="p-4 rounded-xl bg-status-warning/10 border border-status-warning/30">
                <div className="flex items-start gap-3">
                  <CreditCard className="w-5 h-5 text-status-warning mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-status-warning">
                      Custo: {creditsRequired} créditos
                    </p>
                    <p className="text-sm text-status-warning mt-1" aria-live="polite" aria-atomic="true">
                      {revealType === "email" 
                        ? "O custo será cobrado apenas se o candidato tiver email disponível."
                        : "O custo será cobrado apenas se o candidato tiver telefone disponível."}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2 p-3 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-subtle">
                <Info className="w-4 h-4 mt-0.5 flex-shrink-0 text-wedo-cyan" aria-hidden="true" />
                <p className="text-xs text-lia-text-secondary leading-relaxed">
                  Se o contato não estiver disponível nas bases consultadas,{" "}
                  <strong className="text-lia-text-primary font-medium">não há cobrança de créditos.</strong>
                </p>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2">
          <AlertDialogCancel asChild>
            <Button 
              variant="outline" 
              disabled={isLoading} 
              className="gap-2 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary"
            >
              <X className="w-4 h-4" />
              Cancelar
            </Button>
          </AlertDialogCancel>
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
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
