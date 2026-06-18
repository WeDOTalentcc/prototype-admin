"use client"

import React from "react"
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
import { cn } from "@/lib/utils"
import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

/**
 * Canonical confirm dialog helper for Agent Studio.
 *
 * UX-Sprint-B QW#4 audit 2026-05-22: substitui 3 native confirm() em
 * CustomAgentsTab/VersionHistoryPanel/MarketplaceTab. WCAG 3.3.4 + DS canonical.
 *
 * Pattern de uso:
 *   const [confirmOpen, setConfirmOpen] = useState(false)
 *   const [target, setTarget] = useState<string | null>(null)
 *
 *   <ConfirmAlertDialog
 *     open={confirmOpen}
 *     onOpenChange={setConfirmOpen}
 *     title="Confirmar exclusão"
 *     description="..."
 *     onConfirm={async () => { await doAction(target); setTarget(null) }}
 *     confirmLabel="Excluir"
 *     destructive
 *   />
 */
export interface ConfirmAlertDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  onConfirm: () => void | Promise<void>
  confirmLabel?: string
  cancelLabel?: string
  /** Ação destrutiva (vermelho) vs ação positiva (preto/primary) */
  destructive?: boolean
}

export function ConfirmAlertDialog({
  useLiaModalTracking('confirm-alert-dialog', open)
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  destructive = false,
}: ConfirmAlertDialogProps) {
  const [isConfirming, setIsConfirming] = React.useState(false)

  const handleConfirm = async () => {
    try {
      setIsConfirming(true)
      await onConfirm()
      onOpenChange(false)
    } finally {
      setIsConfirming(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isConfirming}>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isConfirming}
            className={cn(
              destructive
                ? "bg-status-error text-white hover:bg-status-error/90 focus-visible:ring-status-error/30"
                : "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover focus-visible:ring-lia-btn-primary-bg/30",
              "focus-visible:outline-none focus-visible:ring-2",
            )}
          >
            {isConfirming ? "Aguarde..." : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
