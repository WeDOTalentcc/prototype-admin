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
 * Sprint 5.5 B2 (2026-05-25): confirmation dialog antes do grant can_view_salary.
 *
 * Por quê: toggle 1-click ou checkbox podem causar grants acidentais. PII grant
 * é decisão consciente do controlador (LGPD Art. 5 V/VI) e fica auditada
 * via SOXAuditLog action=pii_grant_change (Art. 37 V, 7-year retention).
 *
 * Reutilizado em:
 *   - user-list.tsx (inline toggle)
 *   - user-form.tsx (checkbox no formulário)
 *   - B3 bulk grant (toolbar quando 1+ users selecionados)
 */
export interface SalaryGrantConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Direction of the change being confirmed */
  granting: boolean
  /** Display name or descriptor (e.g. "Ana Paula Santos" or "3 usuários selecionados") */
  target: string
  /** Optional: candidate email or detail line under name */
  targetDetail?: string
  onConfirm: () => void | Promise<void>
}

export function SalaryGrantConfirmDialog({
  open,
  onOpenChange,
  granting,
  target,
  targetDetail,
  onConfirm,
}: SalaryGrantConfirmDialogProps) {
  const titleGrant = "Conceder acesso a salários?"
  const titleRevoke = "Revogar acesso a salários?"

  const bodyGrant = (
    <>
      <p className="mb-2">
        <strong>{target}</strong>
        {targetDetail && <span className="text-lia-text-secondary"> · {targetDetail}</span>}
      </p>
      <p>
        Esta pessoa poderá <strong>ver salários de candidatos</strong> ao acessar
        a plataforma. A ação será registrada no log de auditoria
        (LGPD Art. 37 V, retenção 7 anos).
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
        Esta pessoa <strong>deixará de ver salários</strong> dos candidatos.
        Acessos futuros virão mascarados como restritos. A revogação será
        registrada no log de auditoria.
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
          <AlertDialogCancel data-testid="salary-grant-cancel">
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="salary-grant-confirm"
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
