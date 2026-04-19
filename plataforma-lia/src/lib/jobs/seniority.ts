/**
 * Helper canônico de senioridade de vaga.
 *
 * O campo `seniority` é o SSOT (canônico em `lib/schemas/job.schema.ts`).
 * O campo legacy `level` foi removido na Task #539 (após Task #531 ter
 * unificado leitura/escrita). Esta função permanece como ponto único de
 * leitura — útil para tolerar payloads parciais (ex.: `null`/`undefined`
 * vindos de mappers ou DTOs incompletos).
 *
 * NÃO substituir em:
 *   - `lang.level` (proficiência de idioma — campo distinto).
 *   - `member.level`, `skill.level` (campos distintos).
 */

export interface JobSeniorityShape {
  seniority?: string | null
}

/**
 * Retorna a senioridade canônica da vaga.
 *
 * Nunca retorna `null`/`undefined` — escolha intencional para consumidores
 * que filtram/buscam (ex: `.toLowerCase().includes(...)`).
 */
export function getJobSeniority(job: JobSeniorityShape | null | undefined): string {
  if (!job) return ""
  const v = job.seniority ?? ""
  return typeof v === "string" ? v : ""
}

/**
 * Versão que devolve `null` quando ausente — para casos onde "não definido"
 * deve ser distinguível de "string vazia" (ex: badges condicionais).
 */
export function getJobSeniorityOrNull(
  job: JobSeniorityShape | null | undefined,
): string | null {
  if (!job) return null
  const v = job.seniority ?? null
  if (v === null || v === undefined) return null
  const s = String(v).trim()
  return s.length > 0 ? s : null
}

/**
 * Compara senioridade case-insensitive com substring — padrão usado em
 * `useJobsFilters.ts` e `jobsPageUtils.ts` para filtro inline.
 */
export function jobSeniorityMatches(
  job: JobSeniorityShape | null | undefined,
  needle: string,
): boolean {
  const value = getJobSeniority(job).toLowerCase()
  return value.includes(needle.toLowerCase())
}
