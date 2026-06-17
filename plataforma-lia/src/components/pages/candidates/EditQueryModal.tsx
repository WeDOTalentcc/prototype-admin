"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { Search } from "lucide-react"
import dynamic from "next/dynamic"

const SmartSearchInput = dynamic(
  () => import("@/components/search/smart-search-input").then(m => ({ default: m.SmartSearchInput })).catch(() => {
    return import("@/components/search/smart-search-input").then(m => ({ default: m.default }))
  }),
  { ssr: false }
)

import type { ModalPearchSearchOptions } from "./CandidatesPageModals.types"

interface EditQueryModalProps {
  isOpen: boolean
  onClose: () => void
  initialValue: string
  activeFiltersCount: number
  searchSource: string
  onSearchSourceChange: (source: string) => void
  pearchSearchOptions: ModalPearchSearchOptions
  onPearchOptionsChange: (options: ModalPearchSearchOptions) => void
  onOpenFilters: () => void
  onSubmitNatural: (query: string, entities: unknown, mode: string, metadata: unknown) => Promise<void>
  onSubmitAI: (query: string) => Promise<void>
}

export function EditQueryModal({
  isOpen,
  onClose,
  initialValue,
  activeFiltersCount,
  searchSource,
  onSearchSourceChange,
  pearchSearchOptions,
  onPearchOptionsChange,
  onOpenFilters,
  onSubmitNatural,
  onSubmitAI,
}: EditQueryModalProps) {
  const t = useTranslations('candidates.modals')
  const [value, setValue] = useState(initialValue)

  useEffect(() => {
    if (isOpen) setValue(initialValue)
  }, [isOpen, initialValue])

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }

  const handleSaveAndSearch = async () => {
    if (value.trim()) {
      onClose()
      await onSubmitAI(value.trim())
    }
  }

  return (
    <div
      data-testid="edit-query-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-6 pb-4">
          <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Search className="w-4 h-4 text-lia-text-secondary" />
            {t('editYourSearch')}
          </h2>
          <p className="text-xs text-lia-text-tertiary mt-1">
            {t('editSearchDescription')}
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 px-6 pb-4 overflow-auto">
          <SmartSearchInput
            value={value}
            onChange={setValue}
            onSubmit={async (query, entities, mode, metadata) => {
              if (query.trim()) {
                onClose()
                await onSubmitNatural(query.trim(), entities, mode || 'natural', metadata)
              }
            }}
            onCancel={onClose}
            onOpenFilters={() => {
              onClose()
              onOpenFilters()
            }}
            placeholder={t('searchPlaceholder')}
            activeFiltersCount={activeFiltersCount}
            searchSource={searchSource as any}
            onSearchSourceChange={onSearchSourceChange}
            requireEmails={pearchSearchOptions.requireEmails}
            onRequireEmailsChange={(v) => onPearchOptionsChange({ ...pearchSearchOptions, requireEmails: v })}
            requirePhoneNumbers={pearchSearchOptions.requirePhoneNumbers}
            onRequirePhoneNumbersChange={(v) => onPearchOptionsChange({ ...pearchSearchOptions, requirePhoneNumbers: v })}
          />
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 border-t border-lia-border-subtle dark:border-lia-border-subtle p-6 pt-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl transition-colors motion-reduce:transition-none border border-lia-border-subtle dark:border-lia-border-subtle"
          >
            {t('cancel')}
          </button>
          <button
            onClick={handleSaveAndSearch}
            className="px-4 py-2 text-sm text-white rounded-xl transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
          >
            {t('saveAndSearch')}
          </button>
        </div>
      </div>
    </div>
  )
}
