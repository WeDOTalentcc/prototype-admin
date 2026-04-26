"use client"

import React from "react"
import { Shield, X } from "lucide-react"
import { useTranslations } from 'next-intl'

interface Props {
  isOpen: boolean
  fileName: string
  onConfirm: () => void
  onCancel: () => void
}

export function LgpdConsentDialog({ isOpen, fileName, onConfirm, onCancel }: Props) {
  const t = useTranslations('chat.lgpd')

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-lia-bg-primary rounded-md border border-lia-border-subtle w-[400px] max-w-[90vw] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2">
            <Shield className="w-4.5 h-4.5 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-lia-text-primary">
              {t('title')}
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          <p className="text-sm text-lia-text-primary leading-relaxed">
            {t('fileIdentified', { fileName })}
          </p>
          <p className="text-xs text-lia-text-secondary leading-relaxed">
            {t('legalBasis')}
          </p>
          <ul className="space-y-1.5 ml-4">
            <li className="text-xs text-lia-text-secondary list-disc">
              {t('consent1')}
            </li>
            <li className="text-xs text-lia-text-secondary list-disc">
              {t('consent2')}
            </li>
            <li className="text-xs text-lia-text-secondary list-disc">
              {t('consent3')}
            </li>
          </ul>

          <div className="p-2.5 rounded-md bg-wedo-cyan/5 border border-wedo-cyan/20">
            <p className="text-[10px] text-wedo-cyan">
              {t('retentionNote')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-5 py-3 border-t border-lia-border-subtle">
          <button
            onClick={onCancel}
            className="flex-1 px-3 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            {t('cancel')}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-3 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none"
          >
            {t('confirmProcess')}
          </button>
        </div>
      </div>
    </div>
  )
}
