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
 ? "text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:bg-gray-700"
              : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700",
            className
          )}
          title={hasInstruction ? "Editar instrução para LIA" : "Adicionar instrução para LIA"}
        >
          <Brain className="w-3 h-3" />
        </button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 p-0 rounded-md"
        side="right"
        align="start"
      >
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-chat-cyan" />
              <span className="text-sm font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>Instrução para LIA</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="text-xs text-gray-600 dark:text-gray-400">
            Campo: <span className="text-gray-800 dark:text-gray-200 font-medium">{fieldLabel}</span>
          </div>

          <Textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Adicione instruções que ajudarão a LIA a interpretar melhor este campo..."
            className="min-h-[100px] text-xs border-gray-200 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none"
          />

          {examples.length > 0 && (
            <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-1 text-xs font-medium uppercase text-gray-600">
                <Info className="w-3 h-3" />
                <span>Exemplos de instruções</span>
              </div>
              <div className="space-y-1">
                {examples.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInstruction(example)}
                    className="block w-full text-left text-xs text-gray-600 hover:text-gray-700 dark:hover:text-gray-300 p-1.5 rounded hover:bg-white transition-colors"
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
              onClick={() => setIsOpen(false)}
              className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
              className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              {isSaving ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
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
