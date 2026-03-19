export { SalaryStage } from './SalaryStage'
export type { SalaryStageProps, SalaryInfo, Benefit, SalaryBenchmark, CompanyConfig as SalaryCompanyConfig } from './SalaryStage'

export { CompetenciesStage } from './CompetenciesStage'
export type {
  CompetenciesStageProps,
  TechnicalSkill,
  BehavioralCompetency,
  SkillWeightInference,
  BasicInfoFields,
  DetectedCriteria as CompetenciesDetectedCriteria,
  CompanyConfig as CompetenciesCompanyConfig
} from './CompetenciesStage'

export { WSIQuestionsStage } from './WSIQuestionsStage'
export type {
  WSIQuestionsStageProps,
  WSIQuestionCandidate,
  CompanyDefaultQuestion
} from './WSIQuestionsStage'

export { EnrichedJDStage } from './EnrichedJDStage'
export type {
  EnrichedJDStageProps,
  EnrichedJDData,
  EnrichedSuggestion,
  SectionSuggestions,
  CompensationSuggestions,
  SuggestionSource,
  SuggestionImpact,
  SuggestionCategory
} from './EnrichedJDStage'
