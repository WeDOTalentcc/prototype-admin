/**
 * Niveis de senioridade — ESPELHO TS da fonte unica canonica.
 *
 * DEVE permanecer identico a lia-agent-system/app/shared/seniority_levels.py
 * (mesmos ids, mesma ordem). Sensor: scripts/check_seniority_levels_sync.py.
 *
 * Antes a lista vivia hardcoded em compensation-policies-types.ts (SENIORITY_LEVEL_OPTIONS)
 * e em benefits-types.ts (SENIORITY_OPTIONS), divergentes. Esta e a fonte unica:
 * faixas salariais (SalaryBand.level), escopo de verba (seniority_levels[]) e a UI
 * de bandas referenciam estes ids.
 */
export interface SeniorityLevel {
  id: string
  label: string
}

export const CANONICAL_SENIORITY_LEVELS: readonly SeniorityLevel[] = [
  { id: "junior", label: "Júnior" },
  { id: "pleno", label: "Pleno" },
  { id: "senior", label: "Sênior" },
  { id: "staff", label: "Staff" },
  { id: "principal", label: "Principal" },
  { id: "coordinator", label: "Coordenador" },
  { id: "manager", label: "Gerente" },
  { id: "director", label: "Diretor" },
  { id: "c-level", label: "C-Level" },
] as const

export const SENIORITY_LEVEL_IDS: readonly string[] = CANONICAL_SENIORITY_LEVELS.map((l) => l.id)

/** Opcoes p/ ChipMultiSelect de escopo (com curinga "all" = aplica a todos). */
export const SENIORITY_SCOPE_OPTIONS: readonly SeniorityLevel[] = [
  { id: "all", label: "Todos" },
  ...CANONICAL_SENIORITY_LEVELS,
]

export function seniorityLabel(id: string): string {
  return CANONICAL_SENIORITY_LEVELS.find((l) => l.id === id)?.label ?? id
}

/** Tipos de contrato canonicos (escopo de verba/beneficio). */
export const CONTRACT_TYPE_OPTIONS: readonly SeniorityLevel[] = [
  { id: "clt", label: "CLT" },
  { id: "pj", label: "PJ" },
  { id: "estagio", label: "Estágio" },
  { id: "temporario", label: "Temporário" },
  { id: "freelancer", label: "Freelancer" },
  { id: "trainee", label: "Trainee" },
] as const
