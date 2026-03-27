'use client'

import React, { useState, useEffect, ReactNode } from 'react'
import { Bot, Info, Save, X, Loader2 } from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'
import { LiaFieldKey } from '@/hooks/use-company-lia-instructions'
import { defaultLiaFieldExamples } from './LiaFieldToggle'

interface CompanyDataCardProps {
  fieldKey: LiaFieldKey
  label: string
  category?: string
  isActive: boolean
  currentInstruction?: string
  isEditing: boolean
  onToggleChange: (fieldKey: string, isActive: boolean) => void
  onInstructionSave: (fieldKey: string, instruction: string) => void
  children: ReactNode
  className?: string
  fullWidth?: boolean
}

export function CompanyDataCard({
  fieldKey,
  label,
  category,
  isActive,
  currentInstruction = '',
  isEditing,
  onToggleChange,
  onInstructionSave,
  children,
  className,
  fullWidth = false,
}: CompanyDataCardProps) {
  const [isPopoverOpen, setIsPopoverOpen] = useState(false)
  const [instruction, setInstruction] = useState(currentInstruction)
  const [isSaving, setIsSaving] = useState(false)
  const [localIsActive, setLocalIsActive] = useState(isActive)

  const examples = defaultLiaFieldExamples[fieldKey] || []

  useEffect(() => {
    setInstruction(currentInstruction)
  }, [currentInstruction])

  useEffect(() => {
    setLocalIsActive(isActive)
  }, [isActive])

  const handleToggle = (checked: boolean) => {
    setLocalIsActive(checked)
    onToggleChange(fieldKey, checked)
  }

  const handleSaveInstruction = async () => {
    setIsSaving(true)
    try {
      await onInstructionSave(fieldKey, instruction)
      setIsPopoverOpen(false)
    } finally {
      setIsSaving(false)
    }
  }

  const hasInstruction = currentInstruction && currentInstruction.trim().length > 0

  return (
    <div 
      className={cn(
        "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-4 py-3 transition-all",
        localIsActive ? "border-l-[3px] border-l-gray-900 dark:border-l-gray-50" : "border-l-[3px] border-l-gray-200 dark:border-l-gray-700",
        !localIsActive && "opacity-60",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 flex-shrink-0 min-w-[140px]">
          <span className={textStyles.label}>
            {label}
          </span>
          {category && (
            <span className={cn(textStyles.caption, "bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full")}>
              {category}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          {children}
        </div>

        <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={!localIsActive || !isEditing}
              className={cn(
                "inline-flex items-center justify-center w-7 h-7 rounded-md transition-colors flex-shrink-0",
                (!localIsActive || !isEditing) && "opacity-40 cursor-not-allowed",
                localIsActive && isEditing && hasInstruction
 ? "text-gray-600 dark:text-gray-400 hover:bg-gray-100"
                  : "bg-gray-50 text-gray-500 hover:bg-gray-100 hover:text-gray-600 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600"
              )}
            >
              <Bot className="w-4 h-4" />
            </button>
          </PopoverTrigger>
          <PopoverContent 
            className="w-80 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 p-0"
            side="left"
            align="start"
          >
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className={textStyles.h4}>Instrução para LIA</span>
                </div>
                <button
                  onClick={() => setIsPopoverOpen(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className={textStyles.description}>
                Campo: <span className="text-gray-800 dark:text-gray-200 font-medium">{label}</span>
              </div>

              <Textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Adicione instruções que ajudarão a LIA a interpretar melhor este campo..."
                className="min-h-[100px] text-xs border-gray-200 dark:border-gray-600 focus:ring-gray-900 focus:border-gray-900 dark:focus:ring-gray-50 dark:focus:border-gray-50 resize-none"
              />

              {examples.length > 0 && (
                <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-1 text-xs font-medium uppercase text-gray-600 dark:text-gray-400">
                    <Info className="w-3 h-3" />
                    <span>Exemplos</span>
                  </div>
                  <div className="space-y-1">
                    {examples.map((example, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInstruction(example)}
                        className="block w-full text-left text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-50 p-1.5 rounded hover:bg-white dark:hover:bg-gray-800 transition-colors"
                      >
                        "{example}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPopoverOpen(false)}
                  className="text-xs h-8"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveInstruction}
                  disabled={isSaving}
                  className="text-xs h-8 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  {isSaving ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                  ) : (
                    <Save className="w-3.5 h-3.5 mr-1" />
                  )}
                  Salvar
                </Button>
              </div>
            </div>
          </PopoverContent>
        </Popover>

        <Switch
          checked={localIsActive}
          onCheckedChange={handleToggle}
          disabled={!isEditing}
          className="data-[state=checked]:bg-gray-900 dark:data-[state=checked]:bg-gray-50 flex-shrink-0"
        />
      </div>

      {hasInstruction && (
        <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-600 rounded-md">
          <div className="flex items-start gap-2">
            <Bot className="w-3 h-3 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
            <p className={cn(textStyles.caption, "leading-relaxed")}>
              {currentInstruction}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

interface SimpleDataCardProps {
  label: string
  category?: string
  isEditing: boolean
  children: ReactNode
  className?: string
  fullWidth?: boolean
}

export function SimpleDataCard({
  label,
  category,
  isEditing,
  children,
  className,
  fullWidth = false,
}: SimpleDataCardProps) {
  return (
    <div 
      className={cn(
        "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-4 py-3 transition-all",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 flex-shrink-0 min-w-[140px]">
          <span className={textStyles.label}>
            {label}
          </span>
          {category && (
            <span className={cn(textStyles.caption, "bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full")}>
              {category}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          {children}
        </div>
      </div>
    </div>
  )
}
