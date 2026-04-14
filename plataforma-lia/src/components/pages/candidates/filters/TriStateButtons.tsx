"use client"

import React from "react"
import { useTranslations } from "next-intl"

export interface TriStateButtonsProps {
  value: boolean | null
  onChange: (value: boolean | null) => void
}

export function TriStateButtons({ value, onChange }: TriStateButtonsProps) {
  const t = useTranslations('candidates.filters')

  const options = [
    { value: null, label: t('all') },
    { value: true, label: t('yes') },
    { value: false, label: t('no') },
  ]
  return (
    <div data-testid="tri-state-buttons" className="flex gap-1.5">
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          data-testid={`tri-state-${String(opt.value)}`}
          onClick={() => onChange(opt.value)}
          className={`flex-1 px-2 py-1.5 text-micro rounded-md transition-colors motion-reduce:transition-none ${value === opt.value ? 'bg-lia-btn-primary-bg text-white border-none' : 'bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle'}`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
