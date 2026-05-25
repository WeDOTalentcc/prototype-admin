"use client"

/**
 * usePoolAgents + mutations canonical Sprint 7B-1.
 *
 * Hook canonical pra consumir e mutar `pool_agent_assignments` (M2M
 * custom_agents × talent_pools). Backend Sprint 7A endpoints:
 *
 *   GET    /api/backend-proxy/talent-pools/:id/agents
 *   POST   /api/backend-proxy/talent-pools/:id/agents
 *   PATCH  /api/backend-proxy/talent-pools/:id/agents/:assignmentId
 *   DELETE /api/backend-proxy/talent-pools/:id/agents/:assignmentId
 *   POST   /api/backend-proxy/talent-pools/:id/agents/:assignmentId/run
 *
 * Patterns canonical aplicados:
 * - Envelope `{ok, data, meta}` desempacotado em jsonFetcher (lição hotfix P0 —
 *   espelha `use-agent-template-catalog.ts:62-72`).
 * - Loading + error explícitos (REGRA 4 anti-silent-fallback CLAUDE.md).
 * - Invalidation via `mutate(key)` SWR canonical após cada mutation.
 * - `poolId=null` → SWR key nulo → não dispara fetch (defensive — espelha
 *   `use-ideal-profile.ts`).
 */
import useSWR, { mutate as globalMutate } from "swr"

import type {
  DispatchOnDemandResponse,
  PoolAgentAssignment,
  PoolAgentAssignmentCreatePayload,
  PoolAgentAssignmentUpdatePayload,
} from "@/types/pool-agent-assignment"

interface UsePoolAgentsReturn {
  data: PoolAgentAssignment[]
  isLoading: boolean
  error: string | null
  mutate: () => Promise<unknown>
}

/**
 * Helper canonical: monta a chave SWR pra um pool específico.
 * Exportado pra que mutations externas possam invalidar a mesma chave.
 */
export function poolAgentsKey(poolId: string): string {
  return `/api/backend-proxy/talent-pools/${poolId}/agents`
}

/**
 * Fetcher canonical: desempacota envelope `{ok, data, meta}` quando presente.
 * Tolerante a backend retornando array direto (sem envelope).
 *
 * Pattern espelhado de `src/hooks/agents/use-agent-template-catalog.ts:62-72`.
 */
const jsonFetcher = async (url: string): Promise<PoolAgentAssignment[]> => {
  const r = await fetch(url)
  if (!r.ok) {
    throw new Error(`HTTP ${r.status}`)
  }
  const payload = await r.json()
  if (
    payload &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    "data" in payload &&
    Array.isArray((payload as { data: unknown }).data)
  ) {
    return (payload as { data: PoolAgentAssignment[] }).data
  }
  if (Array.isArray(payload)) {
    return payload as PoolAgentAssignment[]
  }
  // Fail-loud: estrutura inesperada — REGRA 4 anti-silent-fallback.
  throw new Error("Resposta inesperada do servidor (esperado array ou envelope)")
}

/**
 * Hook canonical: lista assignments do pool.
 *
 * `poolId=null` → não dispara fetch (defensive). Retorna `data=[]` sempre que
 * loading/error pra simplificar consumo em componentes.
 */
export function usePoolAgents(poolId: string | null): UsePoolAgentsReturn {
  const { data, error, isLoading, mutate } = useSWR<PoolAgentAssignment[]>(
    poolId ? poolAgentsKey(poolId) : null,
    jsonFetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  )

  return {
    data: data ?? [],
    isLoading,
    error: error ? (error as Error).message : null,
    mutate,
  }
}

/* ------------------------------------------------------------------------ */
/* Mutations canonical                                                       */
/* ------------------------------------------------------------------------ */

interface MutationOptions {
  /** Pool id usado pra invalidar a key SWR após sucesso. */
  poolId: string
}

/**
 * Mutation canonical: assign agent ao pool (POST).
 *
 * Retorna o `PoolAgentAssignment` criado. Invalida a key SWR do pool em sucesso.
 */
export async function assignAgentToPool(
  poolId: string,
  payload: PoolAgentAssignmentCreatePayload,
): Promise<PoolAgentAssignment> {
  const res = await fetch(poolAgentsKey(poolId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`Falha ao assign agent: HTTP ${res.status} ${text}`)
  }
  const body = await res.json()
  await globalMutate(poolAgentsKey(poolId))
  return (body && typeof body === "object" && "data" in body
    ? (body as { data: PoolAgentAssignment }).data
    : (body as PoolAgentAssignment))
}

/**
 * Mutation canonical: update assignment (PATCH).
 */
export async function updateAssignment(
  poolId: string,
  assignmentId: string,
  payload: PoolAgentAssignmentUpdatePayload,
): Promise<PoolAgentAssignment> {
  const res = await fetch(`${poolAgentsKey(poolId)}/${assignmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`Falha ao atualizar assignment: HTTP ${res.status} ${text}`)
  }
  const body = await res.json()
  await globalMutate(poolAgentsKey(poolId))
  return (body && typeof body === "object" && "data" in body
    ? (body as { data: PoolAgentAssignment }).data
    : (body as PoolAgentAssignment))
}

/**
 * Mutation canonical: unassign agent (DELETE).
 *
 * Backend devolve 204 sem body.
 */
export async function unassignAgent(
  poolId: string,
  assignmentId: string,
): Promise<void> {
  const res = await fetch(`${poolAgentsKey(poolId)}/${assignmentId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`Falha ao remover assignment: HTTP ${res.status} ${text}`)
  }
  await globalMutate(poolAgentsKey(poolId))
}

/**
 * Mutation canonical: dispatch on-demand (POST /run).
 *
 * Backend devolve 202 Accepted (stub Sprint 7A — full Celery em 7C).
 * Não invalida key (runtime_metrics atualiza assíncrono).
 */
export async function dispatchAgent(
  poolId: string,
  assignmentId: string,
): Promise<DispatchOnDemandResponse> {
  const res = await fetch(`${poolAgentsKey(poolId)}/${assignmentId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`Falha ao dispatch: HTTP ${res.status} ${text}`)
  }
  const body = await res.json()
  return body as DispatchOnDemandResponse
}

/* ------------------------------------------------------------------------ */
/* Hooks wrappers para uso ergonômico em componentes                         */
/* ------------------------------------------------------------------------ */

/**
 * Hook ergonômico canonical: retorna função de assign + nada mais.
 * Componente decide quando chamar; invalidation é automática.
 */
export function useAssignAgent({ poolId }: MutationOptions) {
  return (payload: PoolAgentAssignmentCreatePayload) =>
    assignAgentToPool(poolId, payload)
}

export function useUpdateAssignment({ poolId }: MutationOptions) {
  return (assignmentId: string, payload: PoolAgentAssignmentUpdatePayload) =>
    updateAssignment(poolId, assignmentId, payload)
}

export function useUnassignAgent({ poolId }: MutationOptions) {
  return (assignmentId: string) => unassignAgent(poolId, assignmentId)
}

export function useDispatchAgent({ poolId }: MutationOptions) {
  return (assignmentId: string) => dispatchAgent(poolId, assignmentId)
}
