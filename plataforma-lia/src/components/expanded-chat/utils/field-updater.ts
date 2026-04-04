/**
 * Field Updater Utilities
 * 
 * Parses field update values from natural language and applies updates
 * Handles salary parsing (15k → 15000) and skill detection
 */

import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"
import type { TechnicalSkill, BehavioralCompetency, SalaryInfo } from '../ExpandedChatContext'

export interface SalaryParseResult {
  type: 'single' | 'range'
  min: number
  max: number
  isValid: boolean
  formatted: string
}

export interface FieldUpdateResult {
  success: boolean
  field: string
  action: 'set' | 'add' | 'remove'
  oldValue?: unknown
  newValue?: unknown
  message: string
}

const SALARY_PATTERNS = {
  kNotation: /(\d+(?:[.,]\d+)?)\s*k/i,
  rangeK: /(\d+(?:[.,]\d+)?)\s*k?\s*(?:a|até|to|-)\s*(\d+(?:[.,]\d+)?)\s*k/i,
  currency: /R?\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)/i,
  rangeCurrency: /R?\$?\s*(\d{1,3}(?:[.,]\d{3})*)\s*(?:a|até|to|-)\s*R?\$?\s*(\d{1,3}(?:[.,]\d{3})*)/i,
  simpleNumber: /^(\d+(?:[.,]\d+)?)$/,
}

function normalizeNumber(value: string): number {
  let normalized = value.replace(/\s/g, '')
  
  if (normalized.includes('.') && normalized.includes(',')) {
    if (normalized.lastIndexOf('.') < normalized.lastIndexOf(',')) {
      normalized = normalized.replace(/\./g, '').replace(',', '.')
    } else {
      normalized = normalized.replace(/,/g, '')
    }
  } else if (normalized.includes(',')) {
    const parts = normalized.split(',')
    if (parts[1] && parts[1].length <= 2) {
      normalized = normalized.replace(',', '.')
    } else {
      normalized = normalized.replace(/,/g, '')
    }
  }
  
  return parseFloat(normalized)
}

/**
 * Parse salary value from natural language text
 * Handles formats like: "15k", `${CURRENCY_SYMBOL} 15.000`, "10k a 15k", etc.
 */
export function parseSalaryValue(text: string): SalaryParseResult {
  const trimmed = text.trim().toLowerCase()
  
  const rangeKMatch = trimmed.match(SALARY_PATTERNS.rangeK)
  if (rangeKMatch) {
    const min = normalizeNumber(rangeKMatch[1]) * 1000
    const max = normalizeNumber(rangeKMatch[2]) * 1000
    return {
      type: 'range',
      min,
      max,
      isValid: min > 0 && max >= min,
      formatted: `${formatBRL(min)} - ${formatBRL(max)}`,
    }
  }
  
  const rangeCurrencyMatch = trimmed.match(SALARY_PATTERNS.rangeCurrency)
  if (rangeCurrencyMatch) {
    const min = normalizeNumber(rangeCurrencyMatch[1])
    const max = normalizeNumber(rangeCurrencyMatch[2])
    return {
      type: 'range',
      min,
      max,
      isValid: min > 0 && max >= min,
      formatted: `${formatBRL(min)} - ${formatBRL(max)}`,
    }
  }
  
  const kMatch = trimmed.match(SALARY_PATTERNS.kNotation)
  if (kMatch) {
    const value = normalizeNumber(kMatch[1]) * 1000
    return {
      type: 'single',
      min: value,
      max: value,
      isValid: value > 0,
      formatted: `${formatBRL(value)}`,
    }
  }
  
  const currencyMatch = trimmed.match(SALARY_PATTERNS.currency)
  if (currencyMatch) {
    const value = normalizeNumber(currencyMatch[1])
    return {
      type: 'single',
      min: value,
      max: value,
      isValid: value > 0,
      formatted: `${formatBRL(value)}`,
    }
  }
  
  const simpleMatch = trimmed.match(SALARY_PATTERNS.simpleNumber)
  if (simpleMatch) {
    const value = normalizeNumber(simpleMatch[1])
    const adjustedValue = value < 1000 ? value * 1000 : value
    return {
      type: 'single',
      min: adjustedValue,
      max: adjustedValue,
      isValid: adjustedValue > 0,
      formatted: `${formatBRL(adjustedValue)}`,
    }
  }
  
  return {
    type: 'single',
    min: 0,
    max: 0,
    isValid: false,
    formatted: '',
  }
}

/**
 * Apply salary update to salary info state
 */
export function applySalaryUpdate(
  currentSalary: SalaryInfo,
  parsedValue: SalaryParseResult,
  updateType: 'min' | 'max' | 'both' = 'both'
): { updated: SalaryInfo; changes: string[] } {
  const changes: string[] = []
  const updated = { ...currentSalary }
  
  if (!parsedValue.isValid) {
    return { updated: currentSalary, changes: [] }
  }
  
  if (updateType === 'min' || updateType === 'both') {
    const oldMin = updated.minSalary
    updated.minSalary = parsedValue.min.toString()
    if (oldMin !== updated.minSalary) {
      changes.push(`Salário mínimo: ${oldMin || 'não definido'} → ${formatBRL(parsedValue.min)}`)
    }
  }
  
  if (updateType === 'max' || updateType === 'both') {
    const newMax = parsedValue.type === 'range' ? parsedValue.max : parsedValue.min
    const oldMax = updated.maxSalary
    updated.maxSalary = newMax.toString()
    if (oldMax !== updated.maxSalary) {
      changes.push(`Salário máximo: ${oldMax || 'não definido'} → ${formatBRL(newMax)}`)
    }
  }
  
  return { updated, changes }
}

/**
 * Normalize skill name for comparison
 */
function normalizeSkillName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * Find a skill by name in the skills list (case-insensitive)
 */
export function findSkillByName(
  skills: TechnicalSkill[],
  name: string
): TechnicalSkill | undefined {
  const normalizedName = normalizeSkillName(name)
  return skills.find(s => normalizeSkillName(s.name) === normalizedName)
}

/**
 * Find a competency by name in the competencies list (case-insensitive)
 */
export function findCompetencyByName(
  competencies: BehavioralCompetency[],
  name: string
): BehavioralCompetency | undefined {
  const normalizedName = normalizeSkillName(name)
  return competencies.find(c => normalizeSkillName(c.name) === normalizedName)
}

/**
 * Create a new technical skill with default values
 */
export function createTechnicalSkill(
  name: string,
  options: Partial<TechnicalSkill> = {}
): TechnicalSkill {
  return {
    id: `skill-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    name: name.trim(),
    level: options.level || 'Intermediário',
    required: options.required ?? true,
    category: options.category || detectSkillCategory(name),
    weight: options.weight ?? 3,
    weightJustification: options.weightJustification,
    isWeightInferred: options.isWeightInferred ?? true,
  }
}

/**
 * Detect skill category based on name
 */
function detectSkillCategory(name: string): TechnicalSkill['category'] {
  const nameLower = name.toLowerCase()
  
  const languages = ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'sql']
  const frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'fastapi', 'rails', 'laravel', 'next.js', 'nest.js', '.net']
  const databases = ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sql server', 'dynamodb', 'cassandra', 'neo4j']
  
  if (languages.some(l => nameLower.includes(l))) return 'language'
  if (frameworks.some(f => nameLower.includes(f))) return 'framework'
  if (databases.some(d => nameLower.includes(d))) return 'database'
  
  return 'tool'
}

/**
 * Add a technical skill if it doesn't exist
 */
export function addSkillIfNotExists(
  skills: TechnicalSkill[],
  name: string,
  options: Partial<TechnicalSkill> = {}
): { skills: TechnicalSkill[]; added: boolean; message: string } {
  const existing = findSkillByName(skills, name)
  
  if (existing) {
    return {
      skills,
      added: false,
      message: `A skill "${existing.name}" já está na lista.`,
    }
  }
  
  const newSkill = createTechnicalSkill(name, options)
  return {
    skills: [...skills, newSkill],
    added: true,
    message: `Skill "${newSkill.name}" adicionada com sucesso.`,
  }
}

/**
 * Remove a technical skill by name
 */
export function removeSkillByName(
  skills: TechnicalSkill[],
  name: string
): { skills: TechnicalSkill[]; removed: boolean; message: string } {
  const existing = findSkillByName(skills, name)
  
  if (!existing) {
    return {
      skills,
      removed: false,
      message: `Skill "${name}" não encontrada na lista.`,
    }
  }
  
  return {
    skills: skills.filter(s => s.id !== existing.id),
    removed: true,
    message: `Skill "${existing.name}" removida com sucesso.`,
  }
}

/**
 * Generate confirmation message for field update
 */
export function generateUpdateConfirmation(
  field: string,
  action: 'set' | 'add' | 'remove',
  value: string,
  success: boolean
): string {
  if (!success) {
    return `Não foi possível ${action === 'add' ? 'adicionar' : action === 'remove' ? 'remover' : 'atualizar'} "${value}".`
  }
  
  const actionVerbs: Record<string, string> = {
    set: 'atualizado',
    add: 'adicionado',
    remove: 'removido',
  }
  
  const fieldLabels: Record<string, string> = {
    salary: 'Salário',
    skill: 'Skill',
    competency: 'Competência',
    question: 'Pergunta',
  }
  
  const fieldLabel = fieldLabels[field] || field
  const actionVerb = actionVerbs[action] || action
  
  return `✅ ${fieldLabel} ${actionVerb}: ${value}`
}

/**
 * Detect if text contains skill-related keywords
 */
export function containsSkillKeywords(text: string): boolean {
  const keywords = [
    'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
    'kubernetes', 'git', 'linux', 'excel', 'power bi', 'sap', 'salesforce',
    'comunicação', 'liderança', 'trabalho em equipe', 'resolução de problemas',
    'organização', 'proatividade', 'criatividade', 'adaptabilidade',
  ]
  
  const textLower = text.toLowerCase()
  return keywords.some(kw => textLower.includes(kw))
}

/**
 * Extract potential skill names from text
 */
export function extractPotentialSkills(text: string): string[] {
  const commonSkills = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
    'Node.js', 'Django', 'Flask', 'Spring', 'SQL', 'PostgreSQL', 'MySQL',
    'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
    'Git', 'Linux', 'CI/CD', 'REST API', 'GraphQL', 'Microservices',
    'Machine Learning', 'Data Science', 'Power BI', 'Excel', 'SAP',
  ]
  
  const textLower = text.toLowerCase()
  return commonSkills.filter(skill => 
    textLower.includes(skill.toLowerCase())
  )
}
