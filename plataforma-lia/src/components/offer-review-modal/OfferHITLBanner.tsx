"use client"
import { Loader2, AlertTriangle, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

export type ConfirmState = "idle" | "confirming" | "success" | "error"

interface OfferHITLBannerProps {
  confirmState: ConfirmState
  errorMessage: string
  isSending: boolean
  candidateName: string
  onCancelConfirm: () => void
  onConfirmSend: () => void
  onClearError: () => void
}

export function OfferHITLBanner({
  confirmState,
  errorMessage,
  isSending,
  candidateName,
  onCancelConfirm,
  onConfirmSend,
  onClearError,
}: OfferHITLBannerProps) {
  if (confirmState === "confirming") {
    return (
      <>
        <Separator className="border-lia-border-subtle dark:border-gray-700" />
        <div className="rounded-xl border border-status-warning/40 bg-status-warning/5 px-4 py-3 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-status-warning mt-0.5" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
              Confirmar envio para{" "}
              <span className="font-semibold">{candidateName}</span>?
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Esta ação envia a proposta ao candidato. Não será possível cancelar após o envio.
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={onCancelConfirm}
              disabled={isSending}
              className="rounded-lg h-8 text-xs border-lia-border-subtle dark:border-gray-700 transition-colors"
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={onConfirmSend}
              disabled={isSending}
              className="rounded-lg h-8 text-xs bg-wedo-coral text-white hover:bg-wedo-coral/90 transition-colors"
            >
              {isSending && (
                <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" aria-hidden="true" />
              )}
              {isSending ? "Enviando..." : "Confirmar envio"}
            </Button>
          </div>
        </div>
      </>
    )
  }

  if (confirmState === "error" && errorMessage) {
    return (
      <>
        <Separator className="border-lia-border-subtle dark:border-gray-700" />
        <div role="alert" className="rounded-xl border border-status-error/40 bg-status-error/5 px-4 py-3 flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 text-status-error" aria-hidden="true" />
          <p className="text-sm text-status-error flex-1">{errorMessage}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearError}
            className="h-8 text-xs rounded-lg transition-colors"
          >
            Tentar novamente
          </Button>
        </div>
      </>
    )
  }

  if (confirmState === "success") {
    return (
      <>
        <Separator className="border-lia-border-subtle dark:border-gray-700" />
        <div className="rounded-xl border border-status-success/40 bg-status-success/5 px-4 py-3 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 shrink-0 text-status-success" aria-hidden="true" />
          <p className="text-sm font-medium text-status-success">Proposta enviada com sucesso!</p>
        </div>
      </>
    )
  }

  return null
}
