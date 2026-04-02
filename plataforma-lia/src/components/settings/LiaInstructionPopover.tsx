'use client'

import React, { useState, useEffect } from 'react'
import { Brain, Info, Save, X, Loader2 } from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

export interface LiaInstruction {
  fieldKey: string
  fieldLabel: string
  instruction: string
  category: 'company' | 'recruitment' | 'benefits' | 'culture' | 'tech'
  examples?: string[]
}

interface LiaInstructionPopoverProps {
  fieldKey: string
  fieldLabel: string
  category: LiaInstruction['category']
  currentInstruction?: string
  examples?: string[]
  onSave: (instruction: string) => void
  className?: string
}

export function LiaInstructionPopover({
  fieldKey,
  fieldLabel,
  category,
  currentInstruction = '',
  examples = [],
  onSave,
  className,
}: LiaInstructionPopoverProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [instruction, setInstruction] = useState(currentInstruction)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    setInstruction(currentInstruction)
  }, [currentInstruction])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(instruction)
      setIsOpen(false)
    } finally {
      setIsSaving(false)
    }
  }

  const hasInstruction = currentInstruction && currentInstruction.trim().length > 0

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors",
            hasInstruction
 ? "text-lia-text-primary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated"
              : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active hover:text-lia-text-primary",
            className
          )}
          title={hasInstruction ? "Editar instrução para LIA" : "Adicionar instrução para LIA"}
        >
          <Brain className="w-3 h-3" />
        </button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle p-0 rounded-md"
        side="right"
        align="start"
      >
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-chat-cyan" />
              <span className="text-sm font-semibold text-lia-text-primary">Instrução para LIA</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="text-xs text-lia-text-secondary">
            Campo: <span className="text-lia-text-primary font-medium">{fieldLabel}</span>
          </div>

          <Textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Adicione instruções que ajudarão a LIA a interpretar melhor este campo..."
            className="min-h-[100px] text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium resize-none"
          />

          {examples.length > 0 && (
            <div className="space-y-2 p-3 bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center gap-1 text-xs font-medium uppercase text-lia-text-secondary">
                <Info className="w-3 h-3" />
                <span>Exemplos de instruções</span>
              </div>
              <div className="space-y-1">
                {examples.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInstruction(example)}
                    className="block w-full text-left text-xs text-lia-text-secondary hover:text-lia-text-primary p-1.5 rounded-md hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none"
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
              onClick={() => setIsOpen(false)}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary"
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isSaving ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                  Salvando...
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <Save className="w-3.5 h-3.5" />
                  Salvar
                </span>
              )}
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

export const defaultLiaInstructionExamples: Record<string, string[]> = {
  work_model: [
    "Híbrido com preferência para 3 dias presenciais. Cargos júnior devem ter mais dias no escritório.",
    "Remoto apenas para cargos sênior+ com experiência comprovada em trabalho remoto.",
  ],
  seniority_levels: [
    "Júnior: 1-2 anos de experiência. Pleno: 3-5 anos. Sênior: 6+ anos com liderança técnica.",
    "Para vagas de tecnologia, considerar certificações como equivalente a 1 ano de experiência.",
  ],
  salary_ranges: [
    "Faixas são negociáveis em até 15% para candidatos excepcionais. Bônus não incluído.",
    "CLT inclui 13º e férias. PJ tem adicional de 30% sobre CLT equivalente.",
  ],
  benefits: [
    "Destaque VR e plano de saúde como principais atrativos. Home office setup disponível para sênior+.",
    "Benefícios flexíveis: candidato pode escolher entre vale cultura ou auxílio educação.",
  ],
  tech_stack: [
    "React é obrigatório. TypeScript altamente desejável. Experiência com testes é diferencial.",
    "Aceitar frameworks similares: Vue ou Angular como equivalentes a React para candidatos experientes.",
  ],
  behavioral_competencies: [
    "Comunicação é crítica para cargos com interface cliente. Autonomia mais importante para sênior.",
    "Trabalho em equipe é essencial - equipe é muito colaborativa e dinâmica.",
  ],
  locations: [
    "São Paulo é preferencial. Rio de Janeiro apenas para vagas específicas. Nordeste aceita remoto.",
    "Candidatos de outras cidades podem ser considerados se aceitarem relocação.",
  ],
  employment_types: [
    "CLT preferencial para cargos permanentes. PJ apenas para projetos ou consultoria.",
    "Temporário pode converter para CLT após 6 meses de desempenho satisfatório.",
  ],
}
