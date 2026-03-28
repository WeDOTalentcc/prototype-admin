"use client"

import { useState, useEffect } from "react"
import { Search } from "lucide-react"
import dynamic from "next/dynamic"

const SmartSearchInput = dynamic(
  () => import("@/components/search/smart-search-input").then(m => ({ default: m.SmartSearchInput })).catch(() => {
    return import("@/components/search/smart-search-input").then(m => ({ default: m.default }))
  }),
  { ssr: false }
)

interface PearchSearchOptions {
  requireEmails: boolean
  requirePhoneNumbers: boolean
}

interface EditQueryModalProps {
  isOpen: boolean
  onClose: () => void
  initialValue: string
  activeFiltersCount: number
  searchSource: string
  onSearchSourceChange: (source: string) => void
  pearchSearchOptions: PearchSearchOptions
  onPearchOptionsChange: (options: PearchSearchOptions) => void
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
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)', backdropFilter: 'blur(1px)' }}
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-md border border-gray-100 dark:border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-6 pb-4">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <Search className="w-4 h-4 text-gray-700 dark:text-gray-300" />
            Editar sua busca
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Refine sua busca com linguagem natural. A LIA irá analisar e sugerir melhorias.
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
            placeholder="Ex: desenvolvedor python com 5 anos de experiência em machine learning"
            activeFiltersCount={activeFiltersCount}
            searchSource={searchSource}
            onSearchSourceChange={onSearchSourceChange}
            requireEmails={pearchSearchOptions.requireEmails}
            onRequireEmailsChange={(v) => onPearchOptionsChange({ ...pearchSearchOptions, requireEmails: v })}
            requirePhoneNumbers={pearchSearchOptions.requirePhoneNumbers}
            onRequirePhoneNumbersChange={(v) => onPearchOptionsChange({ ...pearchSearchOptions, requirePhoneNumbers: v })}
          />
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 border-t border-gray-100 dark:border-gray-700 p-6 pt-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors border border-gray-200 dark:border-gray-700"
          >
            Cancelar
          </button>
          <button
            onClick={handleSaveAndSearch}
            className="px-4 py-2 text-sm text-white rounded-md transition-colors bg-gray-900 hover:bg-gray-800"
          >
            Salvar e Buscar
          </button>
        </div>
      </div>
    </div>
  )
}
