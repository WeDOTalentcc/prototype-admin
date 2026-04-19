/**
 * Helper canônico de senioridade de vaga (audit rev. 23 — G23-01).
 *
 * Contexto: o campo `seniority` é o SSOT (canônico em `lib/schemas/job.schema.ts`),
 * mas durante a migração o monolito ainda tem 12+ consumidores lendo
 * `job.level` direto (legacy DTO). Esta função é o ponto único de leitura
 * para senioridade — substitua `job.level` por `getJobSeniority(job)` em
 * leituras / filtros / search nos seguintes arquivos:
 *
 *   - `components/jobs/JobFilters.tsx`
 *   - `components/jobs/JobPipelineSection.tsx`
 *   - `components/jobs/JobPreviewHeader.tsx`
 *   - `components/jobs/JobPreviewAnalytics.tsx`
 *   - `components/jobs/job-edit-tab/JobInfoGeralSection.tsx` (form: leia E escreva ambos)
 *   - `components/pages/jobs/utils/jobsPageUtils.ts`
 *   - `components/pages/jobs/hooks/useJobsFilters.ts`
 *   - `components/pages/jobs/TableFiltersPanel.tsx`
 *   - `components/modals/edit-job/useEditJob.ts`
 *
 * NÃO substituir em:
 *   - `lang.level` (proficiência de idioma — campo distinto, ver `JobInfoGeralSection.tsx:302`).
 *   - `JobPreviewTab.tsx:202` (também `lang.level`, idioma).
 */

export interface JobSeniorityShape {
  seniority?: string | null
  /** @deprecated leia via `getJobSeniority(job)` */
  level?: string | null
}

/**
 * Retorna a senioridade canônica da vaga.
 *
 * Precedência: `seniority` (canônico) → `level` (legacy) → string vazia.
 * Nunca retorna `null`/`undefined` — escolha intencional para consumidores
 * que filtram/buscam (ex: `.toLowerCase().includes(...)`).
 */
export function getJobSeniority(job: JobSeniorityShape | null | undefined): string {
  if (!job) return ""
  const v = job.seniority ?? job.level ?? ""
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
  const v = job.seniority ?? job.level ?? null
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
