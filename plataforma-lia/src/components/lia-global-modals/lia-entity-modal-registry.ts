/**
 * Fase B3 (2026-06-06): registry puro modal_id → tipo de entidade a resolver.
 * Separado do LiaEntityModalHost (que importa componentes pesados) para ser
 * testável isoladamente. Adicionar modal entidade-acoplável = 1 entrada aqui +
 * 1 case no switch do host.
 */
export type LiaEntityKind = "candidate" | "job"

export const ENTITY_MODAL_REGISTRY: Record<string, LiaEntityKind> = {
  general_score: "candidate",
  big_five: "candidate",
  job_report: "job",
}
