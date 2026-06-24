/**
 * Query keys canônicas para as superfícies de IA do candidato (resumo de
 * experiência, matriz de qualificação, match por critérios de busca, pareceres).
 *
 * Espelha o padrão de SETTINGS_QUERY_KEYS em
 * `@/hooks/settings/useSettingsBroadcast` — fonte única de chaves para evitar
 * keys ad-hoc divergentes entre os componentes que consomem essas APIs.
 */
export const CANDIDATE_AI_QUERY_KEYS = {
  experienceHighlight: (candidateId: string, companyId: string) =>
    ['experience-highlight', candidateId, companyId] as const,
  qualificationMatrix: (candidateId: string, jobId: string, companyId: string) =>
    ['qualification-matrix', candidateId, jobId, companyId] as const,
  criteriaMatch: (candidateId: string, criteriaHash: string, companyId: string) =>
    ['criteria-match', candidateId, criteriaHash, companyId] as const,
  pareceres: (candidateId: string, companyId: string) =>
    ['candidate-pareceres', candidateId, companyId] as const,
} as const
