"use client"
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Code, Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button"

export const TabBoolean = React.memo(function TabBoolean() {
  const t = useTranslations('candidates.liaSidebar')
  const [booleanSearchValue, setBooleanSearchValue] = useState("")

  return (
    <div data-testid="tab-boolean" className="space-y-4 overflow-y-auto flex-1 p-4">
      <p className="text-xs text-lia-text-tertiary">
        {t('booleanDescription')}
      </p>
      <div className="flex flex-wrap gap-1 mb-2">
        {['AND', 'OR', 'NOT', '"..."', '(...)'].map((op) => (
          <button
            key={op}
            onClick={() => setBooleanSearchValue(prev => prev + ' ' + op)}
            className="px-2 py-1 text-xs rounded-full bg-lia-bg-tertiary hover:bg-lia-interactive-active text-lia-text-primary font-mono transition-colors motion-reduce:transition-none"
          >
            {op}
          </button>
        ))}
      </div>
      <textarea
        value={booleanSearchValue}
        onChange={(e) => setBooleanSearchValue(e.target.value)}
        placeholder={t('booleanPlaceholder')}
        className="w-full h-32 p-3 text-xs rounded-xl border focus:outline-none transition-colors motion-reduce:transition-none resize-none bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary font-mono border border-lia-border-subtle"
      />
      <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>{t('booleanTipLabel')}</strong> {t('booleanTip')}
          </p>
        </div>
      </div>
      <Button
        className="w-full h-11 !text-sm font-semibold bg-wedo-cyan-dark text-white font-open-sans"
        onClick={() => { if (booleanSearchValue.trim()) {} }}
        disabled={!booleanSearchValue.trim()}
      >
        <Code className="w-4 h-4 mr-2" />
        {t('searchBoolean')}
      </Button>
    </div>
  )
})

TabBoolean.displayName = "TabBoolean"
