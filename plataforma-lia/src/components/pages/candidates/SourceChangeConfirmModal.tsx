"use client"

import { useTranslations } from "next-intl"
import { Globe, AlertCircle, Zap } from "lucide-react"
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from "@/components/ui/alert-dialog"
import { textStyles } from "@/lib/design-tokens"

interface SourceChangeConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  onCancel: () => void
  onConfirm: () => void
}

export function SourceChangeConfirmModal({
  open,
  onOpenChange,
  pendingSourceChange,
  onCancel,
  onConfirm,
}: SourceChangeConfirmModalProps) {
  const t = useTranslations('candidates.modals')
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="source-change-confirm-modal" className="sm:max-w-[320px] w-[85vw] p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
        <AlertDialogTitle className="sr-only">
          {pendingSourceChange === 'hybrid' ? t('activateHybridSearch') : t('activateGlobalSearch')}
        </AlertDialogTitle>
        <AlertDialogDescription className="sr-only">
          {t('confirmSourceChangeDescription')}
        </AlertDialogDescription>
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${pendingSourceChange === 'hybrid' ? 'bg-wedo-cyan/15' : 'bg-status-warning/15'}`}>
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-4 h-4 text-lia-text-secondary" />
              ) : (
                <Globe className="w-4 h-4 text-status-warning" />
              )}
            </div>
            <div>
              <h3 className={textStyles.title}>
                {pendingSourceChange === 'hybrid' ? t('hybridSearch') : t('globalSearch')}
              </h3>
              <p className={textStyles.caption}>
                {pendingSourceChange === 'hybrid'
                  ? t('hybridDescription')
                  : t('globalDescription')}
              </p>
            </div>
          </div>

          <div className="bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl p-3 space-y-2 border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex justify-between items-center text-xs">
              <span className={textStyles.bodySmall}>{t('searchType')}</span>
              <span className={`${textStyles.label} text-lia-text-primary`}>{pendingSourceChange === 'hybrid' ? t('hybrid') : t('global')}</span>
            </div>
            <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className={`${textStyles.label} text-lia-text-primary`}>{t('costPerCandidateLabel')}</span>
                <span className="font-semibold text-lia-text-secondary">
                  {t('creditCostApify')}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-micro text-status-info bg-status-info/10 p-2 rounded-md">
            <AlertCircle className="w-3 h-3 flex-shrink-0" />
            <span>{t('creditCostInfo')}</span>
          </div>
        </div>

        <div className="flex gap-2.5 pt-3">
          <button
            onClick={onCancel}
            className="flex-1 h-8 text-xs px-3 rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse font-medium transition-colors motion-reduce:transition-none"
          >
            {t('cancel')}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors motion-reduce:transition-none hover:opacity-90 bg-lia-btn-primary-bg"
          >
            {pendingSourceChange === 'hybrid' ? (
              <>
                <Zap className="w-3.5 h-3.5" />
                {t('activate')}
              </>
            ) : (
              <>
                <Globe className="w-3.5 h-3.5" />
                {t('activate')}
              </>
            )}
          </button>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  )
}
