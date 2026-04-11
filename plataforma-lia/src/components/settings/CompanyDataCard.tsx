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
  grouped?: boolean
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
  grouped = false,
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
        "bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md px-4 py-3 transition-colors",
        localIsActive ? "border-l-[3px] border-l-lia-btn-primary-bg dark:border-l-lia-border-subtle" : "border-l-[3px] border-l-lia-border-subtle dark:border-l-lia-border-strong",
        !localIsActive && "opacity-60",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 flex-shrink-0 min-w-[140px]">
          {grouped ? (
            <span role="group" aria-label={label} className={textStyles.label}>
              {label}
            </span>
          ) : (
            <label htmlFor={`field-${fieldKey}`} className={textStyles.label}>
              {label}
            </label>
          )}
          {category && (
            <span className={cn(textStyles.caption, "bg-lia-bg-tertiary dark:bg-lia-bg-elevated px-1.5 py-0.5 rounded-full")}>
              {category}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0" role={grouped ? "group" : undefined} aria-label={grouped ? label : undefined}>
          {children}
        </div>

        <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={!localIsActive || !isEditing}
              aria-label={`Configurar instrução LIA para ${label}`}
              className={cn(
                "inline-flex items-center justify-center w-7 h-7 rounded-md transition-colors flex-shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan",
                (!localIsActive || !isEditing) && "opacity-40 cursor-not-allowed",
                localIsActive && isEditing && hasInstruction
 ? "text-lia-text-secondary hover:bg-lia-bg-tertiary"
                  : "bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-secondary dark:bg-lia-bg-elevated dark:hover:bg-lia-border-medium"
              )}
            >
              <Bot className="w-4 h-4" aria-hidden="true" />
            </button>
          </PopoverTrigger>
          <PopoverContent 
            className="w-80 bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle p-0"
            side="left"
            align="start"
          >
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-lia-text-secondary" />
                  <span className={textStyles.h4}>Instrução para LIA</span>
                </div>
                <button
                  onClick={() => setIsPopoverOpen(false)}
                  className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan rounded-sm"
                  aria-label="Fechar instrução LIA"
                  data-dismiss="true"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>

              <div className={textStyles.description}>
                Campo: <span className="text-lia-text-primary font-medium">{label}</span>
              </div>

              <Textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Adicione instruções que ajudarão a LIA a interpretar melhor este campo..."
                className="min-h-[100px] text-xs border-lia-border-subtle dark:border-lia-border-default focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle dark:focus:border-lia-border-subtle resize-none"
              />

              {examples.length > 0 && (
                <div className="space-y-2 p-3 bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center gap-1 text-xs font-medium uppercase text-lia-text-secondary">
                    <Info className="w-3 h-3" />
                    <span>Exemplos</span>
                  </div>
                  <div className="space-y-1">
                    {examples.map((example, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInstruction(example)}
                        className="block w-full text-left text-xs text-lia-text-secondary hover:text-lia-text-primary p-1.5 rounded-xl hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
                      >
                        "{example}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
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
                  className="text-xs h-8 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  {isSaving ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1" />
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
          className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-secondary flex-shrink-0"
        />
      </div>

      {hasInstruction && (
        <div className="mt-2 p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default rounded-xl">
          <div className="flex items-start gap-2">
            <Bot className="w-3 h-3 text-lia-text-secondary mt-0.5 flex-shrink-0" />
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
  fieldId?: string
  category?: string
  isEditing: boolean
  children: ReactNode
  className?: string
  fullWidth?: boolean
}

export function SimpleDataCard({
  label,
  fieldId,
  category,
  isEditing,
  children,
  className,
  fullWidth = false,
}: SimpleDataCardProps) {
  const resolvedId = fieldId ?? `field-${label.toLowerCase().replace(/\s+/g, '-')}`
  return (
    <div 
      className={cn(
        "bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md px-4 py-3 transition-colors",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 flex-shrink-0 min-w-[140px]">
          <label htmlFor={resolvedId} className={textStyles.label}>
            {label}
          </label>
          {category && (
            <span className={cn(textStyles.caption, "bg-lia-bg-tertiary dark:bg-lia-bg-elevated px-1.5 py-0.5 rounded-full")}>
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
