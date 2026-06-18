"use client"

import { useTranslations } from "next-intl"
import { Mail, Phone, CheckCircle } from "lucide-react"
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
import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

interface ContactFilterConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pendingContactFilter: 'email' | 'phone' | null
  onCancel: () => void
  onConfirm: () => void
}

export function ContactFilterConfirmModal({
  open,
  onOpenChange,
  pendingContactFilter,
  onCancel,
  onConfirm,
}: ContactFilterConfirmModalProps) {
  const t = useTranslations('candidates.modals')
  useLiaModalTracking('contact-filter-confirm', open)
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="contact-filter-modal" className="max-w-md border border-lia-border-subtle dark:border-lia-border-subtle">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-status-success/15">
              {pendingContactFilter === 'email' ? (
                <Mail className="w-4 h-4 text-wedo-green" />
              ) : (
                <Phone className="w-4 h-4 text-wedo-green" />
              )}
            </div>
            {pendingContactFilter === 'email' ? t('filterByEmail') : t('filterByPhone')}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary">
              {pendingContactFilter === 'email'
                ? t('emailFilterDescription')
                : t('phoneFilterDescription')}
            </p>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl p-4 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary">{t('filterLabel')}</span>
                <span className="font-medium">{pendingContactFilter === 'email' ? t('emailOnly') : t('phoneOnly')}</span>
              </div>
              <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{t('apifyEnrichment')}</span>
                  <span className="font-semibold text-lg text-lia-text-secondary">
                    {t('costPerCandidate')}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 p-2 rounded-md">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>{t('autoEnrichmentInfo')}</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="contact-filter-cancel-btn" onClick={onCancel}>
            {t('cancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="contact-filter-confirm-btn"
            onClick={onConfirm}
            className="text-white gap-2 bg-wedo-green hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            {pendingContactFilter === 'email' ? (
              <>
                <Mail className="w-4 h-4" />
                {t('activateEmailFilter')}
              </>
            ) : (
              <>
                <Phone className="w-4 h-4" />
                {t('activatePhoneFilter')}
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
