"use client"

import { useTranslations } from "next-intl"
import { Globe, AlertCircle, Loader2 } from "lucide-react"
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

interface GlobalExpansionConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  lastSuccessfulQuery: string | null
  lastSearchQuery: string | null
  localResultsCount: number
  isExpandingToGlobal: boolean
  onConfirm: () => void
}

export function GlobalExpansionConfirmModal({
  open,
  onOpenChange,
  lastSuccessfulQuery,
  lastSearchQuery,
  localResultsCount,
  isExpandingToGlobal,
  onConfirm,
}: GlobalExpansionConfirmModalProps) {
  const t = useTranslations('candidates.modals')
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="global-expansion-confirm-modal" className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-wedo-cyan/15">
              <Globe className="w-4 h-4 text-lia-text-secondary" />
            </div>
            {t('expandToGlobalSearch')}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {t('globalSearchDescription')}
            </p>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary">{t('currentSearch')}</span>
                <span className="font-medium text-xs max-w-sidebar-content truncate">{lastSuccessfulQuery || lastSearchQuery || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">{t('localResults')}</span>
                <span className="font-medium" aria-live="polite" aria-atomic="true">{t('candidateCount', { count: localResultsCount })}</span>
              </div>
              <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium" aria-live="polite" aria-atomic="true">{t('costPerCandidateLabel')}</span>
                  <span className="font-semibold text-lg text-lia-text-secondary">
                    {t('creditCostApify')}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-status-warning dark:text-status-warning bg-status-warning/10 dark:bg-status-warning/20 p-2 rounded-md">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span aria-live="polite" aria-atomic="true">{t('chargeOnlyViewed')}</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => onOpenChange(false)}>
            {t('cancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isExpandingToGlobal}
            className="text-white gap-2 bg-lia-btn-primary-bg hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            {isExpandingToGlobal ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                {t('expanding')}
              </>
            ) : (
              <>
                <Globe className="w-4 h-4" />
                {t('expandSearchBtn')}
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
