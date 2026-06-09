"use client"

import { useState } from "react"
import { Mail, Phone, CreditCard, Loader2 } from "lucide-react"
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

// Canonical per-reveal credit cost — mirrors the single-candidate
// RevealCreditsModal (email = 2, phone = 14). Keep in sync if pricing changes.
const CREDITS_PER_EMAIL = 2
const CREDITS_PER_PHONE = 14

export interface BulkRevealModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (types: Array<"email" | "phone">) => void | Promise<void>
  candidateCount: number
  isRevealing: boolean
  /** Called when user cancels during an active reveal. If provided, Cancel button stays enabled while isRevealing. */
  onCancel?: () => void
}

export function BulkRevealModal({
  isOpen,
  onClose,
  onConfirm,
  candidateCount,
  isRevealing,
  onCancel,
}: BulkRevealModalProps) {
  const [revealEmail, setRevealEmail] = useState(true)
  const [revealPhone, setRevealPhone] = useState(false)

  const types: Array<"email" | "phone"> = [
    ...(revealEmail ? (["email"] as const) : []),
    ...(revealPhone ? (["phone"] as const) : []),
  ]
  const maxCredits =
    candidateCount *
    ((revealEmail ? CREDITS_PER_EMAIL : 0) + (revealPhone ? CREDITS_PER_PHONE : 0))

  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => {
      if (!open) {
        if (isRevealing) {
          onCancel?.()
        } else {
          onClose()
        }
      }
    }}>
      <AlertDialogContent
        data-testid="bulk-reveal-modal"
        className="max-w-md bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle"
      >
        <AlertDialogHeader>
          <AlertDialogTitle className="text-base-ui font-semibold text-lia-text-primary">
            Revelar contatos de {candidateCount} candidato{candidateCount === 1 ? "" : "s"}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-lia-text-secondary">
                Escolha o que revelar. A cobrança ocorre apenas pelos contatos efetivamente disponíveis.
              </p>

              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 rounded-xl border border-lia-border-subtle cursor-pointer hover:bg-lia-bg-tertiary/50 transition-colors motion-reduce:transition-none">
                  <input
                    type="checkbox"
                    checked={revealEmail}
                    onChange={(e) => setRevealEmail(e.target.checked)}
                    className="w-4 h-4 accent-lia-btn-primary-bg"
                  />
                  <Mail className="w-4 h-4 text-lia-text-secondary" />
                  <span className="flex-1 text-sm text-lia-text-primary">Email</span>
                  <span className="text-xs text-lia-text-tertiary">{CREDITS_PER_EMAIL} créd./candidato</span>
                </label>
                <label className="flex items-center gap-3 p-3 rounded-xl border border-lia-border-subtle cursor-pointer hover:bg-lia-bg-tertiary/50 transition-colors motion-reduce:transition-none">
                  <input
                    type="checkbox"
                    checked={revealPhone}
                    onChange={(e) => setRevealPhone(e.target.checked)}
                    className="w-4 h-4 accent-lia-btn-primary-bg"
                  />
                  <Phone className="w-4 h-4 text-lia-text-secondary" />
                  <span className="flex-1 text-sm text-lia-text-primary">Telefone</span>
                  <span className="text-xs text-lia-text-tertiary">{CREDITS_PER_PHONE} créd./candidato</span>
                </label>
              </div>

              <div className="p-4 rounded-xl bg-status-warning/10 border border-status-warning/30 flex items-start gap-3">
                <CreditCard className="w-5 h-5 text-status-warning mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-status-warning" aria-live="polite" aria-atomic="true">
                    Custo máximo: {maxCredits} créditos
                  </p>
                  <p className="text-sm text-status-warning mt-1">
                    Candidatos sem o contato escolhido não consomem créditos.
                  </p>
                </div>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <Button
            variant="outline"
            onClick={isRevealing ? onCancel : onClose}
            disabled={isRevealing && !onCancel}
          >
            Cancelar
          </Button>
          <Button onClick={() => onConfirm(types)} disabled={isRevealing || types.length === 0}>
            {isRevealing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Revelando…
              </>
            ) : (
              `Revelar (${candidateCount})`
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
