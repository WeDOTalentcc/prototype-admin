/**
 * candidates-mock-data.ts — Sprint 4.11
 *
 * Re-exports mock-data helpers originally duplicated in candidates-page.tsx.
 * The canonical implementations live in candidate-transforms.ts (extracted Sprint G4).
 *
 * Portabilidade Vue: funções puras, sem dependências de hooks React.
 */

export {
  getSalaryByExperience,
  generateWorkHistory,
  generateEducation,
} from "@/lib/transforms/candidate-transforms"
