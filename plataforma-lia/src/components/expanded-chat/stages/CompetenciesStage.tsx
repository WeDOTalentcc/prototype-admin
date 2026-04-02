'use client'

import React from 'react'
import { Code, Laptop, Database, Wrench, Brain, Plus, Check, Trash2, Edit2, Star, Lightbulb, ChevronDown, Settings, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useCompanySkillsCatalog } from '@/hooks/useCompanySkillsCatalog'
import { useCompanyTechStack, TechCategory } from '@/hooks/use-company-tech-stack'

export interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'general'
  weight: number
  weightJustification?: string
  isWeightInferred?: boolean
  source?: string
}

export interface BehavioralCompetency {
  id: string
  name: string
  weight: number
  justification: string
  enabled: boolean
  weightJustification?: string
  isWeightInferred?: boolean
}

export interface SkillWeightInference {
  weight: number
  justificativa: string
}

export interface BasicInfoFields {
  cargo: string
  area: string
  gestor: string
  localidade: string
  modeloTrabalho: string
  tipoContrato: string
}

export interface DetectedCriteria {
  cargo: string | null
  senioridadeIdiomas: string | null
  departamento: string | null
  [key: string]: unknown
}

export interface CompanyConfig {
  techStack?: string[]
  [key: string]: unknown
}

export interface CompetenciesStageProps {
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  onSetTechnicalSkills: (skills: TechnicalSkill[]) => void
  onSetBehavioralCompetencies: (comps: BehavioralCompetency[]) => void
  basicInfoFields: BasicInfoFields
  detectedCriteria: DetectedCriteria
  companyConfig?: CompanyConfig | null
  inferSkillWeight: (skill: string, cargo: string, senioridade: string, area: string, type: 'technical' | 'behavioral') => SkillWeightInference
  isCollapsed?: boolean
  onExpandEdit?: () => void
  isFieldRequired?: boolean
  onShowAddSkillModal?: (category: 'language' | 'framework' | 'database' | 'tool' | 'general') => void
  onShowAddCompetencyModal?: () => void
  onEditCompetency?: (comp: BehavioralCompetency) => void
  highlightedFields?: Set<string>
}

const TECH_KEYWORDS = ['desenvolvedor', 'developer', 'programador', 'analista de sistemas', 'engenheiro de software', 'software engineer', 'devops', 'sre', 'backend', 'frontend', 'fullstack', 'full-stack', 'full stack', 'data engineer', 'data scientist', 'cientista de dados', 'engenheiro de dados', 'arquiteto de software', 'tech lead', 'líder técnico', 'mobile developer', 'ios developer', 'android developer', 'qa engineer', 'quality assurance', 'sysadmin', 'dba', 'cloud engineer', 'security engineer', 'machine learning', 'ml engineer', 'ai engineer']
const TECH_AREAS = ['tecnologia', 'ti', 'dados', 'bi', 'data', 'engineering', 'engenharia de software', 'desenvolvimento', 'infraestrutura']

export function CompetenciesStage({
  technicalSkills,
  behavioralCompetencies,
  onSetTechnicalSkills,
  onSetBehavioralCompetencies,
  basicInfoFields,
  detectedCriteria,
  companyConfig,
  inferSkillWeight,
  isCollapsed = false,
  onExpandEdit,
  isFieldRequired = true,
  onShowAddSkillModal,
  onShowAddCompetencyModal,
  onEditCompetency,
  highlightedFields,
}: CompetenciesStageProps) {
  const [isExpanded, setIsExpanded] = React.useState(!isCollapsed)

  const isFieldHighlighted = (fieldId: string) => highlightedFields?.has(fieldId) ?? false

  const areaLower = (basicInfoFields.area || '').toLowerCase()
  const cargoLower = (detectedCriteria.cargo || '').toLowerCase()

  const isTechJob = TECH_AREAS.some(area => areaLower.includes(area)) ||
                    TECH_KEYWORDS.some(keyword => cargoLower.includes(keyword))

  const { catalog, isLoading: catalogLoading } = useCompanySkillsCatalog('default')
  const { techStackByCategory, isLoading: techStackLoading } = useCompanyTechStack()
  const hasAutoFilledRef = React.useRef(false)

  const mapTechStackCategoryToWizard = (category: string): 'language' | 'framework' | 'database' | 'tool' | 'general' => {
    const mapping: Record<string, 'language' | 'framework' | 'database' | 'tool' | 'general'> = {
      backend: 'language',
      frontend: 'framework',
      dados: 'database',
      cloud: 'tool',
      devops: 'tool',
      ia_ml: 'tool',
      erps: 'tool',
      design: 'tool',
      mobile: 'framework',
      outros: 'tool',
    }
    return mapping[category] || 'tool'
  }

  React.useEffect(() => {
    if (technicalSkills.length > 0 || hasAutoFilledRef.current || !isTechJob) {
      return
    }

    const bothLoaded = !catalogLoading && !techStackLoading

    if (!bothLoaded) {
      return
    }

    const catalogHasSkills = catalog && (
      catalog.technical_skills.language.length > 0 ||
      catalog.technical_skills.framework.length > 0 ||
      catalog.technical_skills.database.length > 0 ||
      catalog.technical_skills.tool.length > 0 ||
      catalog.technical_skills.infrastructure.length > 0 ||
      catalog.technical_skills.general.length > 0
    )

    if (catalogHasSkills) {
      const prefilledSkills: TechnicalSkill[] = [
        ...catalog.technical_skills.language,
        ...catalog.technical_skills.framework,
        ...catalog.technical_skills.database,
        ...catalog.technical_skills.tool,
        ...catalog.technical_skills.infrastructure,
        ...catalog.technical_skills.general,
      ]
        .slice(0, 8)
        .map((skill, index) => ({
          id: `catalog-${skill.id}-${index}`,
          name: skill.name,
          category: (skill.category as 'language' | 'framework' | 'database' | 'tool' | 'general') || 'tool',
          weight: skill.default_weight,
          level: (skill.default_level as 'Básico' | 'Intermediário' | 'Avançado') || 'Intermediário',
          required: false,
          source: 'company_catalog',
        }))

      if (prefilledSkills.length > 0) {
        onSetTechnicalSkills(prefilledSkills)
        hasAutoFilledRef.current = true
        return
      }
    }

    const hasTechStack = Object.values(techStackByCategory).some(arr => arr.length > 0)
    if (hasTechStack) {
      const prefilledSkills: TechnicalSkill[] = []
      let skillIndex = 0

      for (const [category, skills] of Object.entries(techStackByCategory)) {
        for (const skillName of skills) {
          if (prefilledSkills.length >= 8) break
          prefilledSkills.push({
            id: `techstack-${category}-${skillIndex++}`,
            name: skillName,
            category: mapTechStackCategoryToWizard(category),
            weight: 3,
            level: 'Intermediário',
            required: false,
            source: 'tech_stack',
          })
        }
        if (prefilledSkills.length >= 8) break
      }

      if (prefilledSkills.length > 0) {
        onSetTechnicalSkills(prefilledSkills)
        hasAutoFilledRef.current = true
      }
    }
  }, [catalog, catalogLoading, techStackByCategory, techStackLoading, isTechJob, technicalSkills.length, onSetTechnicalSkills])

  const hasSkillsFromCatalog = technicalSkills.some(s => s.source === 'company_catalog')
  const hasSkillsFromTechStack = technicalSkills.some(s => s.source === 'tech_stack')

  const isSkillFromConfig = (skillName: string) =>
    companyConfig?.techStack?.some(tech => tech.toLowerCase() === skillName.toLowerCase())

  const getSkillInference = (skillName: string) => {
    const cargo = basicInfoFields.cargo || detectedCriteria.cargo || ''
    const senioridade = detectedCriteria.senioridadeIdiomas || ''
    const area = basicInfoFields.area || detectedCriteria.departamento || ''
    return inferSkillWeight(skillName, cargo, senioridade, area, 'technical')
  }

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded)
    onExpandEdit?.()
  }

  const renderSkillItem = (skill: TechnicalSkill) => {
    const inference = getSkillInference(skill.name)
    const showInferenceIndicator = skill.isWeightInferred || skill.weight === inference.weight
    const justificationText = skill.weightJustification || inference.justificativa

    return (
      <div key={skill.id} className="flex flex-col gap-1.5 p-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <span className="flex-1 text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
            {skill.name}
            {skill.source === 'company_catalog' && (
              <span
                className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0"
                title="Pré-preenchido do catálogo de competências da empresa"
              />
            )}
            {skill.source === 'tech_stack' && (
              <span
                className="w-1.5 h-1.5 rounded-full bg-wedo-purple flex-shrink-0"
                title="Pré-preenchido do Tech Stack da empresa"
              />
            )}
            {isSkillFromConfig(skill.name) && skill.source !== 'company_catalog' && skill.source !== 'tech_stack' && (
              <span
                className="w-1.5 h-1.5 rounded-full bg-lia-btn-primary-bg flex-shrink-0"
                title="Pré-preenchido das Configurações da empresa"
              />
            )}
          </span>
          <select
            value={skill.level}
            onChange={(e) => onSetTechnicalSkills(technicalSkills.map(s => s.id === skill.id ? { ...s, level: e.target.value as TechnicalSkill['level'] } : s))}
            className="px-1.5 py-0.5 text-micro border border-lia-border-subtle rounded-full bg-lia-bg-primary"
          >
            <option value="Básico">Básico</option>
            <option value="Intermediário">Intermediário</option>
            <option value="Avançado">Avançado</option>
          </select>
          <button
            onClick={() => {
              const newRequired = !skill.required
              const newWeight = newRequired ? 3 : 2
              onSetTechnicalSkills(technicalSkills.map(s => s.id === skill.id ? { ...s, required: newRequired, weight: newWeight, isWeightInferred: false } : s))
            }}
            className={cn(
 "px-1.5 py-0.5 text-micro rounded-full transition-[width,height]",
              skill.required
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                : "bg-lia-interactive-active text-lia-text-secondary"
            )}
            aria-label={skill.required ? 'Marcar como desejável' : 'Marcar como obrigatório'}
          >
            {skill.required ? 'Obrig.' : 'Desej.'}
          </button>
          <button
            onClick={() => onSetTechnicalSkills(technicalSkills.filter(s => s.id !== skill.id))}
            className="p-0.5 text-lia-text-secondary hover:text-status-error transition-colors motion-reduce:transition-none"
            aria-label={`Remover competência: ${skill.name}`}
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
        <div className="flex items-center gap-1 ml-0.5">
          <span className="text-micro text-lia-text-secondary mr-1">Peso:</span>
          {[1, 2, 3, 4, 5].map((w) => (
            <button
              key={w}
              onClick={() => onSetTechnicalSkills(
                technicalSkills.map(s => s.id === skill.id ? { ...s, weight: w, isWeightInferred: false } : s)
              )}
              className="transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md"
              aria-label={`Definir peso ${w}`}
            >
              <Star
                className={cn(
 "w-3.5 h-3.5 transition-colors",
                  w <= skill.weight
                    ? "fill-lia-text-primary text-lia-text-secondary"
                    : "lia-text-muted"
                )}
              />
            </button>
          ))}
          {showInferenceIndicator && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="ml-1 p-0.5 text-status-warning hover:text-status-warning transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md" aria-label="Ver sugestão de peso da LIA">
                    <Lightbulb className="w-3.5 h-3.5 fill-amber-100" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-sidebar-content text-xs bg-lia-bg-elevated border border-lia-border-subtle">
                  <div className="flex items-start gap-1.5">
                    <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium text-lia-text-secondary">Sugerido por LIA</span>
                      <p className="lia-text-secondary mt-0.5">{justificationText}</p>
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {!isFieldRequired && (
        <div className="p-3 bg-gradient-to-r from-green-500/10 to-lia-bg-tertiary dark:to-lia-bg-primary rounded-md border border-status-success/30/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-status-success/20 flex items-center justify-center flex-shrink-0">
              <Brain className="w-3.5 h-3.5 text-status-success" />
            </div>
            <div className="flex-1">
              <span className="text-xs font-medium text-status-success">
                Competências pré-configuradas
              </span>
              <p className="text-micro text-lia-text-secondary mt-0.5">
                Baseadas nas políticas e histórico da empresa.
                <button
                  onClick={handleToggleExpand}
                  className="ml-1 text-lia-text-secondary hover:underline font-medium"
                >
                  {isExpanded ? 'Ocultar detalhes' : 'Editar manualmente'}
                </button>
              </p>
            </div>
            <button
              onClick={handleToggleExpand}
              className="p-1.5 hover:bg-lia-bg-primary/50 rounded-md transition-colors motion-reduce:transition-none"
              aria-label={isExpanded ? 'Recolher painel de competências' : 'Expandir painel de competências'}
            >
              <ChevronDown className={cn(
 "w-4 h-4 text-lia-text-secondary transition-transform",
                isExpanded && "rotate-180"
              )} />
            </button>
          </div>
        </div>
      )}

      {hasSkillsFromCatalog && (
        <div className="p-3 bg-gradient-to-r from-blue-500/10 to-lia-bg-tertiary dark:to-lia-bg-primary rounded-md border border-wedo-cyan/30/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-wedo-cyan/20 flex items-center justify-center flex-shrink-0">
              <Settings className="w-3.5 h-3.5 text-wedo-cyan-dark" />
            </div>
            <div className="flex-1">
              <span className="text-xs font-medium text-wedo-cyan-dark flex items-center gap-1.5">
                Competências pré-preenchidas do catálogo da empresa
                <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
              </span>
              <p className="text-micro text-lia-text-secondary mt-0.5">
                Essas competências foram automaticamente sugeridas com base no catálogo de habilidades da sua empresa.
              </p>
            </div>
          </div>
        </div>
      )}

      {hasSkillsFromTechStack && !hasSkillsFromCatalog && (
        <div className="p-3 bg-gradient-to-r from-violet-500/10 to-lia-bg-tertiary dark:to-lia-bg-primary rounded-md border border-wedo-purple/30/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-wedo-purple/20 flex items-center justify-center flex-shrink-0">
              <Laptop className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="flex-1">
              <span className="text-xs font-medium text-wedo-purple flex items-center gap-1.5">
                Competências pré-preenchidas do Tech Stack
                <span className="w-1.5 h-1.5 rounded-full bg-wedo-purple flex-shrink-0" />
              </span>
              <p className="text-micro text-lia-text-secondary mt-0.5">
                Essas competências foram automaticamente sugeridas com base no perfil tecnológico da sua empresa.
              </p>
            </div>
          </div>
        </div>
      )}

      {(isFieldRequired || isExpanded) && (
        <>
          <div className="flex items-center gap-4 mb-4">
            <div className={cn(
 "px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5",
              technicalSkills.length >= 3
                ? "bg-status-success/10 text-status-success border border-status-success/30/30"
                : "bg-status-warning/15 text-status-warning border border-status-warning/30"
            )}>
              <span className="font-semibold">{technicalSkills.length}/3</span>
              <span>Técnicas</span>
              {technicalSkills.length >= 3 && <Check className="w-3 h-3" />}
            </div>
            <div className={cn(
 "px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5",
              behavioralCompetencies.filter(c => c.enabled).length >= 3
                ? "bg-status-success/10 text-status-success border border-status-success/30/30"
                : "bg-status-warning/15 text-status-warning border border-status-warning/30"
            )}>
              <span className="font-semibold">{behavioralCompetencies.filter(c => c.enabled).length}/3</span>
              <span>Comportamentais</span>
              {behavioralCompetencies.filter(c => c.enabled).length >= 3 && <Check className="w-3 h-3" />}
            </div>
          </div>

          {(technicalSkills.length < 3 || behavioralCompetencies.filter(c => c.enabled).length < 3) && (
            <div className="text-xs text-lia-text-secondary mb-3 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" />
              <span>Selecione pelo menos 3 competências técnicas e 3 comportamentais para uma triagem WSI eficaz</span>
            </div>
          )}

          <div className={cn(
 "flex items-center gap-2 p-2.5 bg-lia-bg-secondary rounded-md transition-colors duration-300",
            (isFieldHighlighted('technicalSkill') || isFieldHighlighted('skills') || isFieldHighlighted('competencias') || isFieldHighlighted('competencias_tecnicas')) && "field-highlight field-pulse"
          )}>
            <Code className="w-4 h-4 text-lia-text-secondary" />
            <span className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              Competências Técnicas
              {companyConfig?.techStack && companyConfig.techStack.length > 0 && (
                <Settings className="w-3 h-3 text-lia-text-secondary" />
              )}
            </span>
            <span className="ml-auto text-micro bg-lia-bg-tertiary text-lia-text-secondary px-1.5 py-0.5 rounded-full">
              {technicalSkills.length}
            </span>
          </div>

          <div className="space-y-3">
            {isTechJob ? (
              <>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Code className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className={`${textStyles.label} text-lia-text-secondary uppercase tracking-wide`}>
                      Linguagens de Programação
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {technicalSkills.filter(s => s.category === 'language').map(renderSkillItem)}
                    <button
                      onClick={() => onShowAddSkillModal?.('language')}
                      className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                      aria-label="Adicionar linguagem de programação"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar linguagem
                    </button>
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Laptop className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className={`${textStyles.label} text-lia-text-secondary uppercase tracking-wide`}>
                      Frameworks
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {technicalSkills.filter(s => s.category === 'framework').map(renderSkillItem)}
                    <button
                      onClick={() => onShowAddSkillModal?.('framework')}
                      className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                      aria-label="Adicionar framework"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar framework
                    </button>
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                      Bancos de Dados
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {technicalSkills.filter(s => s.category === 'database').map(renderSkillItem)}
                    <button
                      onClick={() => onShowAddSkillModal?.('database')}
                      className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                      aria-label="Adicionar banco de dados"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar banco
                    </button>
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Wrench className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                      Ferramentas e Plataformas
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {technicalSkills.filter(s => s.category === 'tool').map(renderSkillItem)}
                    <button
                      onClick={() => onShowAddSkillModal?.('tool')}
                      className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                      aria-label="Adicionar ferramenta ou plataforma"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar ferramenta
                    </button>
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                      Competências Técnicas Gerais
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {technicalSkills.filter(s => s.category === 'general').map(renderSkillItem)}
                    <button
                      onClick={() => onShowAddSkillModal?.('general')}
                      className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                      aria-label="Adicionar competência técnica geral"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar competência geral
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Wrench className="w-3.5 h-3.5 text-lia-text-secondary" />
                  <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                    Conhecimentos Específicos da Área
                  </span>
                </div>
                <div className="space-y-1.5">
                  {technicalSkills.map(renderSkillItem)}
                  <button
                    onClick={() => onShowAddSkillModal?.('tool')}
                    className="w-full py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                    aria-label="Adicionar conhecimento técnico específico"
                  >
                    <Plus className="w-3.5 h-3.5" /> Adicionar conhecimento técnico
                  </button>
                </div>
              </div>
            )}

            <div className="p-2 bg-lia-bg-secondary rounded-md border border-lia-border-default">
              <div className="flex items-center justify-between text-xs">
                <span className="lia-text-secondary">Total de competências técnicas:</span>
                <span className="font-semibold text-lia-text-primary">{technicalSkills.length}</span>
              </div>
              <div className="flex items-center justify-between text-micro mt-1">
                <span className="lia-text-secondary">Obrigatórias: {technicalSkills.filter(s => s.required).length}</span>
                <span className="lia-text-secondary">Desejáveis: {technicalSkills.filter(s => !s.required).length}</span>
              </div>
            </div>
          </div>

          <div className={cn(
 "flex items-center gap-2 p-2.5 bg-lia-bg-secondary rounded-md mt-4 transition-colors duration-300",
            (isFieldHighlighted('behavioralCompetency') || isFieldHighlighted('competencias_comportamentais') || isFieldHighlighted('behavioral')) && "field-highlight field-pulse"
          )}>
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-semibold text-lia-text-primary">
              Competências Comportamentais
            </span>
            <span className="ml-auto text-micro bg-lia-bg-tertiary text-lia-text-secondary px-1.5 py-0.5 rounded-full">
              {behavioralCompetencies.filter(c => c.enabled).length}
            </span>
          </div>

          <div className="space-y-2">
            {behavioralCompetencies.map((comp) => {
              const cargo = basicInfoFields.cargo || detectedCriteria.cargo || ''
              const senioridade = detectedCriteria.senioridadeIdiomas || ''
              const area = basicInfoFields.area || detectedCriteria.departamento || ''
              const behavioralInference = inferSkillWeight(comp.name, cargo, senioridade, area, 'behavioral')
              const showBehavioralInference = comp.isWeightInferred || comp.weight === behavioralInference.weight
              const behavioralJustification = comp.weightJustification || behavioralInference.justificativa

              return (
                <div
                  key={comp.id}
                  className={cn(
 "p-2.5 rounded-md border transition-colors",
                    comp.enabled
                      ? "bg-lia-bg-primary border-lia-border-subtle"
                      : "bg-lia-bg-secondary border-lia-border-subtle opacity-60"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSetBehavioralCompetencies(
                        behavioralCompetencies.map(c => c.id === comp.id ? { ...c, enabled: !c.enabled } : c)
                      )}
                      className={cn(
 "w-4 h-4 rounded-md flex-shrink-0 flex items-center justify-center transition-colors",
                        comp.enabled
                          ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                          : "border border-lia-border-subtle"
                      )}
                    >
                      {comp.enabled && <Check className="w-2.5 h-2.5" />}
                    </button>
                    <span className="text-xs font-medium text-lia-text-primary flex-1">
                      {comp.name}
                    </span>
                    <div className="flex items-center gap-0.5">
                      {[1, 2, 3, 4, 5].map((w) => (
                        <button
                          key={w}
                          onClick={() => onSetBehavioralCompetencies(
                            behavioralCompetencies.map(c => c.id === comp.id ? { ...c, weight: w, isWeightInferred: false } : c)
                          )}
                          className="transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md"
                          aria-label={`Definir peso ${w}`}
                        >
                          <Star
                            className={cn(
 "w-3.5 h-3.5 transition-colors",
                              w <= comp.weight
                                ? "fill-lia-text-primary text-lia-text-secondary"
                                : "lia-text-muted"
                            )}
                          />
                        </button>
                      ))}
                      {showBehavioralInference && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="ml-0.5 p-0.5 text-status-warning hover:text-status-warning transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md" aria-label="Ver sugestão de peso da LIA">
                                <Lightbulb className="w-3.5 h-3.5 fill-amber-100" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="max-w-sidebar-content text-xs bg-lia-bg-elevated border border-lia-border-subtle">
                              <div className="flex items-start gap-1.5">
                                <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0 mt-0.5" />
                                <div>
                                  <span className="font-medium text-lia-text-secondary">Sugerido por LIA</span>
                                  <p className="lia-text-secondary mt-0.5">{behavioralJustification}</p>
                                </div>
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                    <button
                      onClick={() => onEditCompetency?.(comp)}
                      className="p-1 text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
                      aria-label={`Editar competência: ${comp.name}`}
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onSetBehavioralCompetencies(behavioralCompetencies.filter(c => c.id !== comp.id))}
                      className="p-1 text-lia-text-secondary hover:text-status-error transition-colors motion-reduce:transition-none"
                      aria-label={`Remover competência: ${comp.name}`}
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  <p className="text-micro text-lia-text-secondary mt-1 ml-6">
                    {comp.justification}
                  </p>
                </div>
              )
            })}

            <button
              onClick={onShowAddCompetencyModal}
              className="w-full py-2 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
              aria-label="Adicionar competência comportamental"
            >
              <Plus className="w-3.5 h-3.5" /> Adicionar competência
            </button>

            <div className="p-2 bg-lia-bg-secondary rounded-md border border-lia-border-default mt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="lia-text-secondary">Competências ativas:</span>
                <span className="font-semibold text-lia-text-primary">{behavioralCompetencies.filter(c => c.enabled).length}</span>
              </div>
              <div className={`${textStyles.description} mt-1`}>
                O peso total influencia a Nota LIA de cada candidato
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
