import type { DetectedCriteria } from ".."
import {
  extractCargoFromText,
  extractAreaFromText,
  extractGestorFromText,
  extractSkillsFromText,
  extractIdiomasFromText,
  extractSeniorityFromText,
  extractWorkModelFromText,
} from './criteriaExtractorPrimary'
import {
  extractLocationFromText,
  extractContractFromText,
  extractResponsibilitiesFromText,
  extractSalaryFromText,
  extractAffirmativeFromText,
  extractExperienceFromText,
  extractFormacaoFromText,
  extractCertificacoesFromText,
  extractFerramentasFromText,
} from './criteriaExtractorSecondary'
import {
  extractHybridDaysFromText,
  extractBeneficiosFromText,
  extractBonusFromText,
  extractViagensFromText,
  extractDisponibilidadeFromText,
  extractCNHFromText,
  extractHorarioFromText,
} from './criteriaExtractorTertiary'

export function extractCriteriaFromText(text: string, currentCriteria: DetectedCriteria): DetectedCriteria {
  const lowerText = text.toLowerCase()
  const newCriteria = { ...currentCriteria }

  extractCargoFromText(text, newCriteria)
  extractAreaFromText(text, newCriteria)
  extractGestorFromText(text, newCriteria)
  extractSkillsFromText(text, lowerText, newCriteria)
  extractIdiomasFromText(text, newCriteria)
  extractSeniorityFromText(text, newCriteria)
  extractWorkModelFromText(text, newCriteria)
  extractLocationFromText(text, lowerText, newCriteria)
  extractContractFromText(text, newCriteria)
  extractResponsibilitiesFromText(text, newCriteria)
  extractSalaryFromText(text, lowerText, newCriteria)
  extractAffirmativeFromText(text, newCriteria)
  extractExperienceFromText(text, newCriteria)
  extractFormacaoFromText(text, newCriteria)
  extractCertificacoesFromText(text, lowerText, newCriteria)
  extractFerramentasFromText(lowerText, newCriteria)
  extractHybridDaysFromText(text, newCriteria)
  extractBeneficiosFromText(text, newCriteria)
  extractBonusFromText(text, newCriteria)
  extractViagensFromText(text, newCriteria)
  extractDisponibilidadeFromText(text, newCriteria)
  extractCNHFromText(text, newCriteria)
  extractHorarioFromText(text, newCriteria)

  return newCriteria
}
