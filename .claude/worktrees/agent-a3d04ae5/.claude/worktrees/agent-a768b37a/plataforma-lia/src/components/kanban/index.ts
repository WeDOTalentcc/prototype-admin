export * from "./types"
export * from "./constants"

export * from "./utils"

export * from "./hooks"
export * from "./components"

export { 
  generateWorkHistory, 
  generateEducation,
  seededRandom,
  getSalaryByExperience,
  TECH_COMPANIES,
  STARTUPS,
  CONSULTANCIES,
  TOP_UNIVERSITIES,
  OTHER_UNIVERSITIES,
  MBA_SCHOOLS,
  SALARY_RANGES as DATA_GENERATOR_SALARY_RANGES
} from "./mock/data-generators"
export type { 
  CandidateForDataGeneration, 
  WorkHistoryEntry, 
  EducationEntry 
} from "./mock/data-generators"

export { mockJobData, mockCandidates } from "./mock/candidates"
