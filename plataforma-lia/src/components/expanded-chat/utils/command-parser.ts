/**
 * Command Parser for Natural Language Navigation and Edit Commands
 * 
 * Parses user messages to detect navigation commands (e.g., "voltar para salário")
 * and edit commands (e.g., "alterar salário para 15k", "adicionar Python")
 */

import type { WizardStage } from '../config'

export type CommandType = 'navigate' | 'edit' | 'none'

export type EditAction = 'set' | 'add' | 'remove'

export interface ParsedNavigationCommand {
  type: 'navigate'
  target: WizardStage
  originalText: string
}

export interface ParsedEditCommand {
  type: 'edit'
  field: 'salary' | 'skill' | 'competency' | 'question'
  action: EditAction
  value: string | number | null
  originalText: string
}

export interface NoCommand {
  type: 'none'
}

export type ParsedCommand = ParsedNavigationCommand | ParsedEditCommand | NoCommand

const STAGE_ALIASES: Record<string, WizardStage> = {
  'salário': 'salary',
  'salario': 'salary',
  'remuneração': 'salary',
  'remuneracao': 'salary',
  'salary': 'salary',
  'competências': 'competencies',
  'competencias': 'competencies',
  'habilidades': 'competencies',
  'skills': 'competencies',
  'competencies': 'competencies',
  'triagem': 'wsi-questions',
  'perguntas': 'wsi-questions',
  'wsi': 'wsi-questions',
  'wsi-questions': 'wsi-questions',
  'revisão': 'review-publish',
  'revisao': 'review-publish',
  'publicar': 'review-publish',
  'review': 'review-publish',
  'review-publish': 'review-publish',
  'avaliação': 'input-evaluation',
  'avaliacao': 'input-evaluation',
  'início': 'input-evaluation',
  'inicio': 'input-evaluation',
  'input-evaluation': 'input-evaluation',
  'calibração': 'search-calibration',
  'calibracao': 'search-calibration',
  'busca': 'search-calibration',
  'search-calibration': 'search-calibration',
}

const NAVIGATION_PATTERNS = [
  /(?:voltar?\s+(?:para|ao?|à)?)\s+(.+)/i,
  /(?:ir\s+(?:para|ao?|à)?)\s+(.+)/i,
  /(?:quero\s+(?:editar|ir\s+para|voltar\s+para))\s+(.+)/i,
  /(?:mudar\s+para)\s+(.+)/i,
  /(?:navegar\s+(?:para|ao?|à)?)\s+(.+)/i,
  /(?:abrir\s+(?:o?\s*stage\s*de)?)\s+(.+)/i,
  /(?:etapa\s+(?:de)?)\s+(.+)/i,
]

const SALARY_EDIT_PATTERNS = [
  /(?:alterar|mudar|definir|colocar)\s+(?:o?\s*)?salário\s+(?:para|em|como)\s+(.+)/i,
  /(?:alterar|mudar|definir|colocar)\s+(?:o?\s*)?salario\s+(?:para|em|como)\s+(.+)/i,
  /salário\s+(?:para|de|em)\s+(.+)/i,
  /salario\s+(?:para|de|em)\s+(.+)/i,
  /(?:faixa\s+salarial\s+(?:de|para|em))\s+(.+)/i,
  /(?:remuneração\s+(?:de|para|em))\s+(.+)/i,
]

const SKILL_ADD_PATTERNS = [
  /(?:adicionar|incluir|add)\s+(?:a?\s*skill\s*)?(.+)/i,
  /(?:quero\s+)?(?:adicionar|incluir)\s+(.+?)\s+(?:como\s+skill|nas?\s+competências?|nas?\s+habilidades?)/i,
  /(?:inclui(?:r|a)?|adiciona(?:r)?)\s+(.+)/i,
]

const SKILL_REMOVE_PATTERNS = [
  /(?:remover|excluir|tirar|deletar|remove)\s+(?:a?\s*skill\s*)?(.+)/i,
  /(?:quero\s+)?(?:remover|tirar)\s+(.+?)\s+(?:da\s+lista|das?\s+competências?|das?\s+habilidades?)/i,
  /(?:não\s+precisa\s+de)\s+(.+)/i,
]

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
}

function extractStageFromAlias(text: string): WizardStage | null {
  const normalized = normalizeText(text)
  
  for (const [alias, stage] of Object.entries(STAGE_ALIASES)) {
    const normalizedAlias = normalizeText(alias)
    if (normalized.includes(normalizedAlias) || normalizedAlias.includes(normalized)) {
      return stage
    }
  }
  
  return null
}

function parseNavigationIntent(message: string): ParsedNavigationCommand | null {
  const trimmed = message.trim()
  
  for (const pattern of NAVIGATION_PATTERNS) {
    const match = trimmed.match(pattern)
    if (match && match[1]) {
      const targetText = match[1].trim()
      const stage = extractStageFromAlias(targetText)
      
      if (stage) {
        return {
          type: 'navigate',
          target: stage,
          originalText: trimmed,
        }
      }
    }
  }
  
  return null
}

function parseSalaryEdit(message: string): ParsedEditCommand | null {
  const trimmed = message.trim()
  
  for (const pattern of SALARY_EDIT_PATTERNS) {
    const match = trimmed.match(pattern)
    if (match && match[1]) {
      const valueText = match[1].trim()
      return {
        type: 'edit',
        field: 'salary',
        action: 'set',
        value: valueText,
        originalText: trimmed,
      }
    }
  }
  
  return null
}

function parseSkillAdd(message: string): ParsedEditCommand | null {
  const trimmed = message.trim()
  
  for (const pattern of SKILL_ADD_PATTERNS) {
    const match = trimmed.match(pattern)
    if (match && match[1]) {
      const skillName = match[1].trim()
      if (skillName.length > 0 && skillName.length < 100) {
        return {
          type: 'edit',
          field: 'skill',
          action: 'add',
          value: skillName,
          originalText: trimmed,
        }
      }
    }
  }
  
  return null
}

function parseSkillRemove(message: string): ParsedEditCommand | null {
  const trimmed = message.trim()
  
  for (const pattern of SKILL_REMOVE_PATTERNS) {
    const match = trimmed.match(pattern)
    if (match && match[1]) {
      const skillName = match[1].trim()
      if (skillName.length > 0 && skillName.length < 100) {
        return {
          type: 'edit',
          field: 'skill',
          action: 'remove',
          value: skillName,
          originalText: trimmed,
        }
      }
    }
  }
  
  return null
}

/**
 * Main command parser function
 * Parses a user message and returns the detected command type with details
 */
export function parseCommand(message: string): ParsedCommand {
  if (!message || typeof message !== 'string') {
    return { type: 'none' }
  }

  const trimmed = message.trim()
  
  if (trimmed.length < 3 || trimmed.length > 500) {
    return { type: 'none' }
  }

  const navigationCommand = parseNavigationIntent(trimmed)
  if (navigationCommand) {
    return navigationCommand
  }

  const salaryEdit = parseSalaryEdit(trimmed)
  if (salaryEdit) {
    return salaryEdit
  }

  const skillAdd = parseSkillAdd(trimmed)
  if (skillAdd) {
    return skillAdd
  }

  const skillRemove = parseSkillRemove(trimmed)
  if (skillRemove) {
    return skillRemove
  }

  return { type: 'none' }
}

/**
 * Check if a message is a navigation command
 */
export function isNavigationCommand(message: string): boolean {
  const parsed = parseCommand(message)
  return parsed.type === 'navigate'
}

/**
 * Check if a message is an edit command
 */
export function isEditCommand(message: string): boolean {
  const parsed = parseCommand(message)
  return parsed.type === 'edit'
}

/**
 * Check if a message is a local command (navigation or edit)
 * that can be handled without calling the backend
 */
export function isLocalCommand(message: string): boolean {
  const parsed = parseCommand(message)
  return parsed.type !== 'none'
}

/**
 * Get stage label in Portuguese for display
 */
export function getStageLabel(stage: WizardStage): string {
  const labels: Partial<Record<WizardStage, string>> = {
    'input-evaluation': 'Avaliação',
    'salary': 'Remuneração',
    'competencies': 'Competências',
    'wsi-questions': 'Triagem WSI',
    'review-publish': 'Revisão e Publicação',
    'search-calibration': 'Busca e Calibração',
  }
  return labels[stage] || stage
}

/**
 * Get all valid stage aliases for documentation/help
 */
export function getStageAliases(): Partial<Record<WizardStage, string[]>> {
  const aliasesByStage: Partial<Record<WizardStage, string[]>> = {
    'input-evaluation': [],
    'salary': [],
    'competencies': [],
    'wsi-questions': [],
    'review-publish': [],
    'search-calibration': [],
  }

  for (const [alias, stage] of Object.entries(STAGE_ALIASES)) {
    if (!aliasesByStage[stage]) {
      aliasesByStage[stage] = []
    }
    if (!aliasesByStage[stage]!.includes(alias)) {
      aliasesByStage[stage]!.push(alias)
    }
  }

  return aliasesByStage
}
