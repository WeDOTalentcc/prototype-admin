import type { TableFilters } from "./types"

/**
 * Fase 3b — converte os filtros do painel (TableFilters + advancedFilters) no
 * search_spec estruturado que o backend ja consome (SearchSpec -> Pearch via
 * to_pearch_custom_filters). Usado pelo "Refazer busca com estes filtros":
 * empurra os filtros pra QUERY da fonte (Pearch re-consulta) em vez de so
 * estreitar a lista no cliente.
 *
 * Mapeia apenas campos que definem a REFERENCIA da busca (skills, location,
 * cargo, senioridade, industrias, empresas, idiomas, experiencia, modelo de
 * trabalho, salario). Filtros utilitarios (hasEmail, datas) ficam de fora.
 * Retorna so chaves com valor (objeto enxuto), pra nao poluir o fingerprint.
 */
const WORK_MODEL_MAP: Record<string, string> = {
  remoto: "remote",
  "híbrido": "hybrid",
  hibrido: "hybrid",
  presencial: "onsite",
}

export function tableFiltersToSearchSpec(
  tableFilters: TableFilters,
  advancedFilters: Record<string, string[]> = {},
): Record<string, unknown> {
  const spec: Record<string, unknown> = {}

  const skills = [
    ...(tableFilters.skills || []),
    ...(advancedFilters.skills || []),
  ].filter(Boolean)
  if (skills.length) spec.skills = Array.from(new Set(skills))

  const locations = [
    ...(tableFilters.locations || []),
    ...(advancedFilters.locations || []),
  ].filter(Boolean)
  if (locations.length) spec.location = locations[0]

  const jobTitles = [
    ...(tableFilters.jobTitles || []),
    ...(advancedFilters.job_titles || []),
  ].filter(Boolean)
  if (jobTitles.length) spec.job_title = jobTitles[0]

  if (tableFilters.seniorityLevels?.length) spec.seniority = tableFilters.seniorityLevels[0]

  const companies = [
    ...(tableFilters.companies || []),
    ...(advancedFilters.companies || []),
  ].filter(Boolean)
  if (companies.length) spec.companies = Array.from(new Set(companies))

  if (tableFilters.industries?.length) spec.industries = tableFilters.industries
  if (tableFilters.languages?.length) spec.languages = tableFilters.languages

  if (typeof tableFilters.minExperience === "number") spec.years_experience_min = tableFilters.minExperience
  if (typeof tableFilters.maxExperience === "number") spec.years_experience_max = tableFilters.maxExperience
  if (typeof tableFilters.minSalary === "number") spec.salary_min = tableFilters.minSalary
  if (typeof tableFilters.maxSalary === "number") spec.salary_max = tableFilters.maxSalary

  if (tableFilters.workModels?.length) {
    const wm = tableFilters.workModels[0].toLowerCase()
    spec.work_model = WORK_MODEL_MAP[wm] || wm
  }

  if (tableFilters.isOpenToWork) spec.is_open_to_work = true

  return spec
}
