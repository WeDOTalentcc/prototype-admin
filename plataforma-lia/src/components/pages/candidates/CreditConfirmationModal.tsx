"use client"

import { useTranslations } from "next-intl"
import { Zap, Mail, AlertCircle } from "lucide-react"
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
import type { ModalPearchSearchOptions, ModalCreditEstimate } from "./CandidatesPageModals.types"
import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

interface CreditConfirmationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  creditEstimate: ModalCreditEstimate | null
  pearchSearchOptions: ModalPearchSearchOptions
  onSearchOptionsChange: (options: ModalPearchSearchOptions) => void
  onCancel: () => void
  onConfirm: () => void
}

export function CreditConfirmationModal({
  open,
  onOpenChange,
  creditEstimate,
  pearchSearchOptions,
  onSearchOptionsChange,
  onCancel,
  onConfirm,
}: CreditConfirmationModalProps) {
  const t = useTranslations('candidates.modals')
  useLiaModalTracking('credit-confirmation', open)
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="credit-confirmation-modal" className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-wedo-cyan/15">
              <Zap className="w-4 h-4 text-lia-text-secondary" />
            </div>
            {t('confirmGlobalSearch')}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary">
              {t('creditUsageDescription')}
            </p>

            {creditEstimate && (
              <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">{t('searchType')}</span>
                  <span className="font-medium">{t('quickSearchType')}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">{t('resultsLimit')}</span>
                  <span className="font-medium">{pearchSearchOptions.limit ?? 20}</span>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">{t('baseCostCredits')}</span>
                  <span className="font-medium">{t('credits', { count: creditEstimate.base_cost })}</span>
                </div>

                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 space-y-2">
                  <span className="text-xs font-medium text-lia-text-tertiary uppercase tracking-wide">{t('contactEnrichment')}</span>
                  <p className="text-xs text-lia-text-primary">
                    {t('enrichmentDescription')}
                  </p>
                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-lia-text-tertiary" />
                      <span className="text-lia-text-primary">{t('apifyEmailPhone')}</span>
                    </div>
                    <span className="font-medium text-status-success">{t('costPerCandidateApify')}</span>
                  </div>
                  <p className="text-xs text-status-info dark:text-status-info bg-status-info/10 dark:bg-status-info/20 p-2 rounded-md">
                    {t('noContactFilteredInfo')}
                  </p>
                </div>
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{t('estimatedTotal')}</span>
                    <span className="text-base-ui font-semibold text-lia-text-secondary">
                      {t('totalEstimatedValue', { count: creditEstimate.total_estimated })}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-status-warning dark:text-status-warning bg-status-warning/10 dark:bg-status-warning/20 p-2 rounded-md">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{t('costMayVary')}</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>
            {t('cancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="text-white bg-lia-btn-primary-bg hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            {t('confirmSearch')}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
