'use client'

import React, { useState, useMemo } from 'react'
import { 
  Code, Brain, Plus, Trash2, Star, Lightbulb, CheckCircle2 
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import { 
  SKILLS_CATALOG, 
  ROLE_AREA_MAPPING, 
  CORE_SKILLS_BY_ROLE, 
  LEADERSHIP_KEYWORDS, 
  COMMERCIAL_KEYWORDS, 
  TECHNICAL_KEYWORDS, 
  SENIORITY_LEVELS 
} from '../constants'
import type { TechnicalSkill, BehavioralCompetency, SkillWeightInference } from '../types'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const detectSeniorityLevel = (cargo: string, senioridade?: string): number => {
  const text = `${cargo} ${senioridade || ''}`.toLowerCase()
  for (const [keyword, level] of Object.entries(SENIORITY_LEVELS)) {
    if (text.includes(keyword)) {
      return level
    }
  }
  return 2
}

const isLeadershipRole = (cargo: string): boolean => {
  const cargoLower = cargo.toLowerCase()
  return LEADERSHIP_KEYWORDS.some(kw => cargoLower.includes(kw))
}

const isCommercialRole = (cargo: string): boolean => {
  const cargoLower = cargo.toLowerCase()
  return COMMERCIAL_KEYWORDS.some(kw => cargoLower.includes(kw))
}

const isTechnicalRole = (cargo: string): boolean => {
  const cargoLower = cargo.toLowerCase()
  return TECHNICAL_KEYWORDS.some(kw => cargoLower.includes(kw))
}

const getCoreSkillsForRole = (cargo: string): string[] => {
  const cargoLower = cargo.toLowerCase()
  const coreSkills: string[] = []
  
  for (const [roleKey, skills] of Object.entries(CORE_SKILLS_BY_ROLE)) {
    if (cargoLower.includes(roleKey)) {
      coreSkills.push(...skills)
    }
  }
  
  return [...new Set(coreSkills)]
}

const inferTechnicalSkillWeight = (
  skill: string, 
  cargo: string, 
  senioridade: string, 
  area: string
): SkillWeightInference => {
  const skillLower = skill.toLowerCase()
  const seniorityLevel = detectSeniorityLevel(cargo, senioridade)
  const coreSkills = getCoreSkillsForRole(cargo)
  
  const isCore = coreSkills.some(cs => 
    cs.toLowerCase() === skillLower || 
    skillLower.includes(cs.toLowerCase()) || 
    cs.toLowerCase().includes(skillLower)
  )
  
  if (isCore) {
    const baseWeight = 4
    const seniorityBoost = seniorityLevel >= 3 ? 1 : 0
    const finalWeight = Math.min(5, baseWeight + seniorityBoost)
    
    return {
      weight: finalWeight,
      justificativa: `${skill} é competência core para ${cargo || 'esta posição'}`
    }
  }
  
  const areaLower = area.toLowerCase()
  const areaSkills = SKILLS_CATALOG[areaLower]?.technical || []
  const isAreaRelated = areaSkills.some(as => 
    as.toLowerCase() === skillLower || skillLower.includes(as.toLowerCase())
  )
  
  if (isAreaRelated) {
    const weight = seniorityLevel >= 3 ? 4 : 3
    return {
      weight,
      justificativa: `${skill} é relevante para profissionais da área de ${area || 'tecnologia'}`
    }
  }
  
  const commonTools = ['git', 'docker', 'linux', 'sql', 'excel', 'power bi', 'jira']
  if (commonTools.some(tool => skillLower.includes(tool))) {
    return { weight: 3, justificativa: `${skill} é ferramenta padrão utilizada no mercado` }
  }
  
  return { weight: 2, justificativa: `${skill} é competência desejável para complementar o perfil` }
}

const inferBehavioralSkillWeight = (
  skill: string, 
  cargo: string, 
  senioridade: string
): SkillWeightInference => {
  const skillLower = skill.toLowerCase()
  const isLeadership = isLeadershipRole(cargo)
  const isCommercial = isCommercialRole(cargo)
  const isTechnical = isTechnicalRole(cargo)
  const seniorityLevel = detectSeniorityLevel(cargo, senioridade)
  
  if (isLeadership) {
    if (skillLower.includes('liderança')) return { weight: 5, justificativa: 'Liderança é essencial para cargos de gestão' }
    if (skillLower.includes('comunicação')) return { weight: 5, justificativa: 'Comunicação é fundamental para gestão de equipes' }
    if (skillLower.includes('gestão de pessoas')) return { weight: 5, justificativa: 'Gestão de pessoas é competência core para líderes' }
  }
  
  if (isCommercial) {
    if (skillLower.includes('negociação')) return { weight: 5, justificativa: 'Negociação é competência core para área comercial' }
    if (skillLower.includes('orientação a resultados')) return { weight: 5, justificativa: 'Orientação a resultados é fundamental para metas comerciais' }
  }
  
  if (isTechnical) {
    if (skillLower.includes('resolução de problemas')) return { weight: 5, justificativa: 'Resolução de problemas é competência core para cargos técnicos' }
    if (skillLower.includes('pensamento analítico')) return { weight: 5, justificativa: 'Pensamento analítico é essencial para desenvolvimento' }
  }
  
  if (skillLower.includes('comunicação')) {
    return { weight: seniorityLevel >= 3 ? 5 : 4, justificativa: 'Comunicação é essencial para colaboração' }
  }
  
  if (skillLower.includes('trabalho em equipe')) {
    return { weight: 4, justificativa: 'Trabalho em equipe é fundamental para projetos colaborativos' }
  }
  
  return { weight: 3, justificativa: `${skill} é competência comportamental relevante para o perfil` }
}

export function CompetenciesStage() {
  const {
    technicalSkills,
    setTechnicalSkills,
    behavioralCompetencies,
    setBehavioralCompetencies,
    basicInfoFields,
    detectedCriteria,
    companyConfig,
    competenciesTab,
    setCompetenciesTab
  } = useWizardContext()

  const [showAddSkillModal, setShowAddSkillModal] = useState(false)
  const [newSkillName, setNewSkillName] = useState('')
  const [newSkillCategory, setNewSkillCategory] = useState<'language' | 'framework' | 'database' | 'tool'>('language')
  
  const cargo = basicInfoFields.cargo || detectedCriteria.cargo || ''
  const senioridade = detectedCriteria.senioridadeIdiomas || ''
  const area = basicInfoFields.area || detectedCriteria.departamento || ''

  const isSkillFromConfig = (skillName: string) => 
    companyConfig?.techStack?.some(tech => tech.toLowerCase() === skillName.toLowerCase())

  const getSkillInference = (skillName: string, type: 'technical' | 'behavioral') => {
    if (type === 'technical') {
      return inferTechnicalSkillWeight(skillName, cargo, senioridade, area)
    }
    return inferBehavioralSkillWeight(skillName, cargo, senioridade)
  }

  const addTechnicalSkill = () => {
    if (!newSkillName.trim()) return
    
    const inference = inferTechnicalSkillWeight(newSkillName, cargo, senioridade, area)
    const newSkill: TechnicalSkill = {
      id: `skill-${Date.now()}`,
      name: newSkillName.trim(),
      level: 'Intermediário',
      required: inference.weight >= 4,
      category: newSkillCategory,
      weight: inference.weight,
      weightJustification: inference.justificativa,
      isWeightInferred: true
    }
    
    setTechnicalSkills(prev => [...prev, newSkill])
    setNewSkillName('')
    setShowAddSkillModal(false)
  }

  const removeTechnicalSkill = (id: string) => {
    setTechnicalSkills(prev => prev.filter(s => s.id !== id))
  }

  const updateSkillWeight = (id: string, weight: number) => {
    setTechnicalSkills(prev => prev.map(s => 
      s.id === id ? { ...s, weight, isWeightInferred: false } : s
    ))
  }

  const updateSkillLevel = (id: string, level: 'Básico' | 'Intermediário' | 'Avançado') => {
    setTechnicalSkills(prev => prev.map(s => 
      s.id === id ? { ...s, level } : s
    ))
  }

  const toggleSkillRequired = (id: string) => {
    setTechnicalSkills(prev => prev.map(s => {
      if (s.id === id) {
        const newRequired = !s.required
        return { ...s, required: newRequired, weight: newRequired ? 3 : 2, isWeightInferred: false }
      }
      return s
    }))
  }

  const toggleBehavioralCompetency = (id: string) => {
    setBehavioralCompetencies(prev => prev.map(c => 
      c.id === id ? { ...c, enabled: !c.enabled } : c
    ))
  }

  const updateBehavioralWeight = (id: string, weight: number) => {
    setBehavioralCompetencies(prev => prev.map(c => 
      c.id === id ? { ...c, weight, isWeightInferred: false } : c
    ))
  }

  const enabledBehavioralCount = behavioralCompetencies.filter(c => c.enabled).length

  const renderTechnicalSkill = (skill: TechnicalSkill) => {
    const inference = getSkillInference(skill.name, 'technical')
    const showInferenceIndicator = skill.isWeightInferred || skill.weight === inference.weight
    
    return (
      <div key={skill.id} className="flex flex-col gap-1.5 p-2 bg-white rounded-md border border-gray-200">
        <div className="flex items-center gap-2">
          <span className="flex-1 text-xs font-medium text-gray-800 flex items-center gap-1.5">
            {skill.name}
            {isSkillFromConfig(skill.name) && (
              <span className="w-1.5 h-1.5 rounded-full bg-gray-900 dark:bg-gray-50 flex-shrink-0" title="Pré-preenchido das Configurações" />
            )}
          </span>
          <select 
            value={skill.level}
            onChange={(e) => updateSkillLevel(skill.id, e.target.value as any)}
            className="px-1.5 py-0.5 text-micro border border-gray-200 rounded-full bg-white"
          >
            <option value="Básico">Básico</option>
            <option value="Intermediário">Intermediário</option>
            <option value="Avançado">Avançado</option>
          </select>
          <button
            onClick={() => toggleSkillRequired(skill.id)}
            className={cn(
              "px-1.5 py-0.5 text-micro rounded-full transition-all",
              skill.required ? "bg-gray-900 dark:bg-gray-50 text-white" : "bg-gray-200 text-gray-500"
            )}
          >
            {skill.required ? 'Obrig.' : 'Desej.'}
          </button>
          <button 
            onClick={() => removeTechnicalSkill(skill.id)}
            className="p-0.5 text-gray-400 hover:text-status-error transition-colors"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
        <div className="flex items-center gap-1 ml-0.5">
          <span className="text-micro text-gray-400 mr-1">Peso:</span>
          {[1, 2, 3, 4, 5].map((w) => (
            <button key={w} onClick={() => updateSkillWeight(skill.id, w)} className="transition-all">
              <Star className={cn(
                "w-3.5 h-3.5 transition-colors",
                w <= skill.weight ? "fill-gray-700 dark:fill-gray-300 text-gray-600 dark:text-gray-400" : "text-gray-200"
              )} />
            </button>
          ))}
          {showInferenceIndicator && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="ml-1 p-0.5 text-status-warning">
                    <Lightbulb className="w-3.5 h-3.5 fill-amber-100" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-sidebar-content text-xs bg-white border">
                  <div className="flex items-start gap-1.5">
                    <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium text-gray-600 dark:text-gray-400">Sugerido por LIA</span>
                      <p className="text-gray-500 mt-0.5">{skill.weightJustification || inference.justificativa}</p>
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

  const renderBehavioralCompetency = (comp: BehavioralCompetency) => (
    <div key={comp.id} className={cn(
      "flex flex-col gap-1.5 p-2 rounded-md border transition-all",
      comp.enabled ? "bg-white border-gray-200" : "bg-gray-50 border-gray-200 opacity-60"
    )}>
      <div className="flex items-center gap-2">
        <button
          onClick={() => toggleBehavioralCompetency(comp.id)}
          className={cn(
            "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-all",
            comp.enabled ? "bg-status-success" : "border border-gray-300"
          )}
        >
          {comp.enabled && <CheckCircle2 className="w-2.5 h-2.5 text-white" strokeWidth={3} />}
        </button>
        <span className="flex-1 text-xs font-medium text-gray-800">
          {comp.name}
        </span>
      </div>
      {comp.enabled && (
        <>
          <p className="text-micro text-gray-500 ml-6">{comp.justification}</p>
          <div className="flex items-center gap-1 ml-6">
            <span className="text-micro text-gray-400 mr-1">Peso:</span>
            {[1, 2, 3, 4, 5].map((w) => (
              <button key={w} onClick={() => updateBehavioralWeight(comp.id, w)} className="transition-all">
                <Star className={cn(
                  "w-3.5 h-3.5 transition-colors",
                  w <= comp.weight ? "fill-gray-700 dark:fill-gray-300 text-gray-600 dark:text-gray-400" : "text-gray-200"
                )} />
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Progress Indicator */}
      <div className="p-2.5 bg-gray-50 rounded-md border border-gray-200 mb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              <span className="text-micro text-gray-500">Técnicas:</span>
              <span className={`text-xs font-medium ${technicalSkills.length >= 3 ? 'text-status-success' : 'text-status-warning'}`}>
                {technicalSkills.length}/3
              </span>
              {technicalSkills.length >= 3 && <CheckCircle2 className="w-3 h-3 text-status-success" />}
            </div>
            <div className="w-px h-4 bg-gray-200" />
            <div className="flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-micro text-gray-500">Comportamentais:</span>
              <span className={`text-xs font-medium ${enabledBehavioralCount >= 3 ? 'text-status-success' : 'text-status-warning'}`}>
                {enabledBehavioralCount}/3
              </span>
              {enabledBehavioralCount >= 3 && <CheckCircle2 className="w-3 h-3 text-status-success" />}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setCompetenciesTab('technical')}
          className={cn(
            "flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5",
            competenciesTab === 'technical' ? "bg-gray-900 dark:bg-gray-50 text-white" : "border border-gray-200 text-gray-500"
          )}
        >
          <Code className="w-3.5 h-3.5" />
          Técnicas ({technicalSkills.length})
        </button>
        <button
          onClick={() => setCompetenciesTab('behavioral')}
          className={cn(
            "flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5",
            competenciesTab === 'behavioral' ? "bg-gray-900 dark:bg-gray-50 text-white" : "border border-gray-200 text-gray-500"
          )}
        >
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Comportamentais ({enabledBehavioralCount})
        </button>
      </div>

      {/* Technical Skills Tab */}
      {competenciesTab === 'technical' && (
        <div className="space-y-2">
          {technicalSkills.map(renderTechnicalSkill)}
          
          {/* Add Skill Button */}
          <button
            onClick={() => setShowAddSkillModal(true)}
            className="w-full py-2 px-3 rounded-md border border-dashed border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400 text-xs font-medium hover:bg-gray-50 dark:bg-gray-800/50 transition-all flex items-center justify-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            Adicionar Competência Técnica
          </button>
          
          {/* Add Skill Modal */}
          {showAddSkillModal && (
            <div className="p-3 bg-gray-50 rounded-md border border-gray-200 space-y-2">
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="Nome da competência..."
                className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs"
                autoFocus
              />
              <select
                value={newSkillCategory}
                onChange={(e) => setNewSkillCategory(e.target.value as any)}
                className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs bg-white"
              >
                <option value="language">Linguagem</option>
                <option value="framework">Framework</option>
                <option value="database">Banco de Dados</option>
                <option value="tool">Ferramenta</option>
              </select>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAddSkillModal(false)}
                  className="flex-1 py-1.5 px-3 rounded-md border border-gray-200 text-xs text-gray-500"
                >
                  Cancelar
                </button>
                <button
                  onClick={addTechnicalSkill}
                  disabled={!newSkillName.trim()}
                  className="flex-1 py-1.5 px-3 rounded-md bg-gray-900 dark:bg-gray-50 text-white text-xs disabled:opacity-50"
                >
                  Adicionar
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Behavioral Competencies Tab */}
      {competenciesTab === 'behavioral' && (
        <div className="space-y-2">
          {behavioralCompetencies.map(renderBehavioralCompetency)}
        </div>
      )}
    </div>
  )
}

export default CompetenciesStage
