"use client"

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

/**
 * Sprint 8 (2026-05-26): confirmation dialog antes do grant can_view_sensitive_pii.
 *
 * Cobre CPF + DoB + endereço + secondary contacts (LGPD Art. 5 II categorias sensíveis).
 * Espelha SalaryGrantConfirmDialog (Sprint 5.5) — distinção semântica entre
 * financial (salary) e identity (sensitive PII) per LGPD.
 *
 * Default Sprint 8: grant=true (zero-quebra, opt-out). Revogação é mais comum
 * que concessão neste pattern.
 */
export interface SensitivePiiGrantConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  granting: boolean
  target: string
  targetDetail?: string
  onConfirm: () => void | Promise<void>
}

export function SensitivePiiGrantConfirmDialog({
  open,
  onOpenChange,
  granting,
  target,
  targetDetail,
  onConfirm,
}: SensitivePiiGrantConfirmDialogProps) {
  const titleGrant = "Conceder acesso a dados pessoais sensíveis?"
  const titleRevoke = "Revogar acesso a dados pessoais sensíveis?"

  const bodyGrant = (
    <>
      <p className="mb-2">
        <strong>{target}</strong>
        {targetDetail && <span className="text-lia-text-secondary"> · {targetDetail}</span>}
      </p>
      <p>
        Esta pessoa poderá <strong>ver CPF, data de nascimento, endereço e
        contatos secundários</strong> dos candidatos. A ação será registrada
        no log de auditoria (LGPD Art. 5 II + Art. 37 V, retenção 7 anos).
      </p>
    </>
  )

  const bodyRevoke = (
    <>
      <p className="mb-2">
        <strong>{target}</strong>
        {targetDetail && <span className="text-lia-text-secondary"> · {targetDetail}</span>}
      </p>
      <p>
        Esta pessoa <strong>deixará de ver dados pessoais sensíveis</strong>
        {" "}(CPF, endereço, contatos secundários). Nome, email primário e telefone
        primário continuam visíveis para workflow. A revogação será registrada
        no log de auditoria.
      </p>
    </>
  )

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {granting ? titleGrant : titleRevoke}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="text-sm text-lia-text-secondary">
              {granting ? bodyGrant : bodyRevoke}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="sensitive-pii-grant-cancel">
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="sensitive-pii-grant-confirm"
            onClick={(e) => {
              e.preventDefault()
              void onConfirm()
            }}
            className={granting ? "" : "bg-status-error hover:bg-status-error/90"}
          >
            {granting ? "Conceder acesso" : "Revogar acesso"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
