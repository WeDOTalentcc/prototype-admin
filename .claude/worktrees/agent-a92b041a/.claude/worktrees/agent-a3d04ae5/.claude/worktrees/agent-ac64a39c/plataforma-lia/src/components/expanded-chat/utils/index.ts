/**
 * Expanded Chat Utilities Module
 * 
 * Exports utility functions for command parsing and field updates
 */

export {
  parseCommand,
  isNavigationCommand,
  isEditCommand,
  isLocalCommand,
  getStageLabel,
  getStageAliases,
  type CommandType,
  type EditAction,
  type ParsedNavigationCommand,
  type ParsedEditCommand,
  type NoCommand,
  type ParsedCommand,
} from './command-parser'

export {
  parseSalaryValue,
  applySalaryUpdate,
  findSkillByName,
  findCompetencyByName,
  createTechnicalSkill,
  addSkillIfNotExists,
  removeSkillByName,
  generateUpdateConfirmation,
  containsSkillKeywords,
  extractPotentialSkills,
  type SalaryParseResult,
  type FieldUpdateResult,
} from './field-updater'
