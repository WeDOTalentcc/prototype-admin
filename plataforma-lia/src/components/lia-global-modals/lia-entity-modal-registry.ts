/**
 * Fase B3 (2026-06-06): registry puro modal_id → tipo de entidade a resolver.
 * Separado do LiaEntityModalHost (que importa componentes pesados) para ser
 * testável isoladamente. Adicionar modal entidade-acoplável = 1 entrada aqui +
 * 1 case no switch do host.
 *
 * Fase B3b (2026-06-09): adiciona kind "jobs" (plural) para modais multi-vaga.
 */
export type LiaEntityKind = "candidate" | "job" | "jobs"

export const ENTITY_MODAL_REGISTRY: Record<string, LiaEntityKind> = {
  general_score: "candidate",
  big_five: "candidate",
  job_report: "job",
  job_compare: "jobs",  // B3b: multi-job comparison (job_ids[] no evento data)
}
