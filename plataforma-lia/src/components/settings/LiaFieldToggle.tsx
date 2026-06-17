'use client'

import React, { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { Bot, Info, Save, X, Loader2, Check } from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { LIA_FIELD_DEFINITIONS, LiaFieldKey } from '@/hooks/company/use-company-lia-instructions'
import { useAiPersona } from '@/hooks/company/use-ai-persona'

interface LiaFieldToggleProps {
  fieldKey: LiaFieldKey
  isActive: boolean
  currentInstruction?: string
  examples?: string[]
  onToggleChange: (fieldKey: string, isActive: boolean) => void
  onInstructionSave: (fieldKey: string, instruction: string) => void
  className?: string
  showLabel?: boolean
  compact?: boolean
}

export function LiaFieldToggle({
  fieldKey,
  isActive,
  currentInstruction = '',
  examples = [],
  onToggleChange,
  onInstructionSave,
  className,
  showLabel = false,
  compact = false,
}: LiaFieldToggleProps) {
  const t = useTranslations('settings.liaField')
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? 'IA'
  const [isPopoverOpen, setIsPopoverOpen] = useState(false)
  const [instruction, setInstruction] = useState(currentInstruction)
  const [isSaving, setIsSaving] = useState(false)
  const [localIsActive, setLocalIsActive] = useState(isActive)

  const fieldDef = LIA_FIELD_DEFINITIONS[fieldKey]

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

  if (compact) {
    return (
      <div className={cn("inline-flex items-center gap-2", className)}>
        <Switch
          checked={localIsActive}
          onCheckedChange={handleToggle}
          className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-secondary"
        />
        <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={!localIsActive}
              className={cn(
                "inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors",
                !localIsActive && "opacity-40 cursor-not-allowed",
                localIsActive && hasInstruction
 ? "text-lia-text-primary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated"
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active hover:text-lia-text-primary"
              )}
              title={localIsActive ? (hasInstruction ? t("editInstruction") : t("addInstruction")) : t("fieldDisabled")}
            >
              <Bot className="w-3 h-3" />
            </button>
          </PopoverTrigger>
          <PopoverContent 
            className="w-80 bg-lia-bg-primary border-lia-border-subtle p-0"
            side="right"
            align="start"
          >
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-wedo-cyan" />
                  <span className="text-sm font-semibold text-lia-text-primary">{`Instrução para ${personaName}`}</span>
                </div>
                <button
                  onClick={() => setIsPopoverOpen(false)}
                  className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="text-xs text-lia-text-secondary">
                Campo: <span className="text-lia-text-primary font-medium">{fieldDef?.label || fieldKey}</span>
              </div>

              <Textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder={t("instructionPlaceholder")}
                className="min-h-[100px] text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium resize-none"
              />

              {examples.length > 0 && (
                <div className="space-y-2 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                  <div className="flex items-center gap-1 text-xs font-medium uppercase text-lia-text-secondary">
                    <Info className="w-3 h-3" />
                    <span>Exemplos</span>
                  </div>
                  <div className="space-y-1">
                    {examples.map((example, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInstruction(example)}
                        className="block w-full text-left text-xs text-lia-text-secondary hover:text-lia-text-primary p-1.5 rounded-xl hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none"
                      >
                        "{example}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-lia-border-subtle">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPopoverOpen(false)}
                  className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveInstruction}
                  disabled={isSaving}
                  className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-hover hover:bg-lia-btn-primary-bg text-lia-btn-primary-text"
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
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="flex items-center gap-2">
        <Switch
          checked={localIsActive}
          onCheckedChange={handleToggle}
          className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-secondary"
        />
        {showLabel && (
          <span className="text-xs text-lia-text-primary">
            {localIsActive ? 'Ativo' : 'Inativo'}
          </span>
        )}
      </div>
      
      <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            disabled={!localIsActive}
            className={cn(
              "inline-flex items-center gap-1.5 px-2 py-1 rounded-full transition-colors text-xs",
              !localIsActive && "opacity-40 cursor-not-allowed",
              localIsActive && hasInstruction
 ? "text-lia-text-primary hover:bg-lia-bg-tertiary"
                : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active"
            )}
            title={localIsActive ? (hasInstruction ? t("editInstruction") : t("addInstruction")) : t("fieldDisabled")}
          >
            <Bot className="w-3 h-3" />
            {hasInstruction ? (
              <>
                <Check className="w-3 h-3" />
                <span>Instrução</span>
              </>
            ) : (
              <span>Adicionar</span>
            )}
          </button>
        </PopoverTrigger>
        <PopoverContent 
          className="w-80 bg-lia-bg-primary border-lia-border-subtle p-0"
          side="right"
          align="start"
        >
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-wedo-cyan" />
                <span className="text-sm font-semibold text-lia-text-primary">{`Instrução para ${personaName}`}</span>
              </div>
              <button
                onClick={() => setIsPopoverOpen(false)}
                className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs text-lia-text-secondary">
              Campo: <span className="text-lia-text-primary font-medium">{fieldDef?.label || fieldKey}</span>
            </div>

            <Textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder={t("instructionPlaceholder")}
              className="min-h-[100px] text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium resize-none"
            />

            {examples.length > 0 && (
              <div className="space-y-2 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-1 text-xs font-medium uppercase text-lia-text-secondary">
                  <Info className="w-3 h-3" />
                  <span>Exemplos</span>
                </div>
                <div className="space-y-1">
                  {examples.map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInstruction(example)}
                      className="block w-full text-left text-xs text-lia-text-secondary hover:text-lia-text-primary p-1.5 rounded-xl hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none"
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-lia-border-subtle">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPopoverOpen(false)}
                className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary"
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleSaveInstruction}
                disabled={isSaving}
                className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-hover hover:bg-lia-btn-primary-bg text-lia-btn-primary-text"
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
    </div>
  )
}

export const defaultLiaFieldExamples: Record<LiaFieldKey, string[]> = {
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
  engineering_culture: [
    "Valorizamos code review rigoroso e pair programming. TDD é prática padrão.",
    "Cultura de experimentação - incentivamos POCs e inovação em 20% do tempo.",
  ],
  default_languages: [
    "Português nativo obrigatório. Inglês intermediário para leitura de docs técnicos.",
    "Espanhol é diferencial para vagas com interface LATAM.",
  ],
  company_big_five: [
    "Buscamos candidatos com alta abertura a novas ideias e conscienciosidade.",
    "Perfil ideal tem equilíbrio entre extroversão para colaboração e foco individual.",
  ],
  departments: [
    "Engenharia é o maior departamento. Produto trabalha junto com squads multidisciplinares.",
    "Cada departamento tem autonomia para definir processos internos.",
  ],
  values: [
    "Transparência e ownership são valores fundamentais na avaliação de candidatos.",
    "Candidatos devem demonstrar alinhamento com pelo menos 3 dos 5 valores.",
  ],
  evp_bullets: [
    "Destacar flexibilidade e crescimento acelerado como principais diferenciais.",
    "Mencionar cultura de feedback contínuo e desenvolvimento pessoal.",
  ],
  pipeline: [
    "Funil padrão tem 5 etapas. Vagas urgentes podem pular teste técnico se sênior+.",
    "Assessment comportamental é obrigatório para cargos de liderança.",
  ],
  eligibility_questions: [
    "Perguntas de elegibilidade são eliminatórias. Candidato que não atende é desqualificado.",
    "Disponibilidade para viagens e inglês fluente são requisitos comuns.",
  ],
  headcount_planning: [
    "Planejamento é trimestral. Vagas extras precisam de aprovação do C-level.",
    "Budget por departamento define limite de contratações.",
  ],
  leadership_style: [
    "Liderança participativa - gestores são coaches, não microgerenciadores.",
    "Autonomia com accountability é o modelo de liderança.",
  ],
  team_dynamics: [
    "Times pequenos (5-8 pessoas) com rituais ágeis semanais.",
    "Cultura de feedback 360° e retrospectivas mensais.",
  ],
  trade_name: [
    "Use o nome fantasia para referências públicas e comunicação com candidatos.",
    "Em vagas confidenciais, pode-se omitir o nome fantasia até etapas finais.",
  ],
  industry: [
    "Destaque o setor nas descrições de vaga para atrair candidatos com experiência relevante.",
    "Mencione transição de carreira aceita para candidatos de setores correlatos.",
  ],
  website: [
    "Link do site deve ser incluído nas vagas para candidatos conhecerem mais sobre a empresa.",
    "Referência principal para informações oficiais da empresa.",
  ],
  linkedin_url: [
    "LinkedIn deve ser usado para validar cultura e tamanho da empresa com candidatos.",
    "Perfil LinkedIn é referência para candidatos pesquisarem sobre a empresa.",
  ],
  mission: [
    "Missão deve ser usada para contextualizar o propósito das vagas.",
    "Mencione a missão nas descrições para candidatos alinhados com propósito.",
  ],
  vision: [
    "Visão ajuda a transmitir ambições de longo prazo da empresa.",
    "Use visão para atrair candidatos que buscam crescimento junto com a empresa.",
  ],
  core_competencies: [
    "Competências essenciais são base para avaliação comportamental de candidatos.",
    "Priorize candidatos que demonstrem ao menos 3 das competências listadas.",
  ],
  dei_initiatives: [
    "Destaque iniciativas de D&I nas vagas para atrair candidatos diversos.",
    "Mencione programas específicos de inclusão quando relevante.",
  ],
  sustainability: [
    "Sustentabilidade é diferencial para candidatos da geração Z e millennials.",
    "Práticas ambientais podem ser destaque em vagas de ESG e compliance.",
  ],
  social_impact: [
    "Impacto social atrai candidatos motivados por propósito além do salário.",
    "Projetos sociais podem ser mencionados na proposta de valor ao colaborador.",
  ],
  hybrid_days_onsite: [
    "Candidatos podem negociar dias presenciais após período de experiência.",
    "Dias presenciais podem variar conforme projeto ou sprint.",
  ],
  company_size: [
    "Porte da empresa contextualiza expectativas de estrutura e processos.",
    "Startups oferecem mais agilidade, empresas maiores mais estabilidade.",
  ],
  employee_count: [
    "Número de funcionários ajuda candidatos a entender escala da operação.",
    "Times menores significam mais responsabilidade individual.",
  ],
  founded_year: [
    "Ano de fundação demonstra maturidade e estabilidade da empresa.",
    "Empresas mais novas podem oferecer mais oportunidades de crescimento.",
  ],
  growth_opportunities: [
    "Destaque plano de carreira e oportunidades de promoção.",
    "Mencione programas de desenvolvimento e treinamento disponíveis.",
  ],
}
