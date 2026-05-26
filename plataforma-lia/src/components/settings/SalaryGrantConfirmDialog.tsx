"use client"

import { useTranslations } from "next-intl"
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
  const t = useTranslations('settings.users')
  const titleGrant = t("salaryGrantConfirmTitleGrant")
  const titleRevoke = t("salaryGrantConfirmTitleRevoke")

  const bodyGrant = (
    <>
      <p className="mb-2">
        <strong>{target}</strong>
        {targetDetail && <span className="text-lia-text-secondary"> · {targetDetail}</span>}
      </p>
      <p>
        {t('salaryGrantConfirmBodyGrant')}
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
        {t('salaryGrantConfirmBodyRevoke')}
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
            {t('salaryGrantConfirmCancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="salary-grant-confirm"
            onClick={(e) => {
              e.preventDefault()
              void onConfirm()
            }}
            className={granting ? "" : "bg-status-error hover:bg-status-error/90"}
          >
            {granting ? t('salaryGrantConfirmActionGrant') : t('salaryGrantConfirmActionRevoke')}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
