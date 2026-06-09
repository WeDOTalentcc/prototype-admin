"use client"

/**
 * Fase B3 (2026-06-06): camada de fetch id→objeto para modais globais da LIA.
 *
 * Vários modais (general-score, big-five, job-insights, job-report) esperam o
 * OBJETO completo de candidato/vaga, mas a tool `open_ui` (backend) só carrega
 * os IDS (a LLM não tem o objeto). Estes hooks resolvem id→objeto via os
 * proxies company-scoped (`/api/backend-proxy/candidates/[id]` e
 * `/job-vacancies/[id]`, que já desembrulham o envelope FastAPI), permitindo
 * que o LiaEntityModalHost monte o modal a partir de um id.
 *
 * Multi-tenancy: o proxy encaminha o JWT server-side; o backend escopa por
 * company. O cliente nunca manda company_id.
 *
 * Fase B3b (2026-06-09): adiciona `useLiaJobs(ids[])` para modais multi-vaga
 * (job_compare). Usa useQueries para fetch paralelo; never mutates order.
 */
import { useQuery, useQueries } from "@tanstack/react-query"

async function fetchEntity<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`fetch ${url} falhou: HTTP ${res.status}`)
  }
  const json = await res.json()
  // O proxy (createProxyHandlers) já desembrulha {ok,data}. Defensivo: se ainda
  // vier um wrapper { data: {...} } sem campos próprios, desce um nível.
  if (
    json &&
    typeof json === "object" &&
    "data" in json &&
    !("id" in json) &&
    json.data &&
    typeof json.data === "object"
  ) {
    return json.data as T
  }
  return json as T
}

/** Candidato por id (company-scoped). enabled só quando há id. */
export function useLiaCandidate<T = Record<string, unknown>>(id?: string | null) {
  return useQuery<T>({
    queryKey: ["lia-entity", "candidate", id],
    queryFn: () => fetchEntity<T>(`/api/backend-proxy/candidates/${id}`),
    enabled: !!id,
    staleTime: 30_000,
  })
}

/** Vaga por id (company-scoped). enabled só quando há id. */
export function useLiaJob<T = Record<string, unknown>>(id?: string | null) {
  return useQuery<T>({
    queryKey: ["lia-entity", "job", id],
    queryFn: () => fetchEntity<T>(`/api/backend-proxy/job-vacancies/${id}`),
    enabled: !!id,
    staleTime: 30_000,
  })
}

/**
 * Múltiplas vagas em paralelo — para o modal job_compare.
 * Garante a mesma ordem de ids na saída.
 * Com ids=[] todos os queries ficam disabled; sem fetch.
 */
export function useLiaJobs<T = Record<string, unknown>>(ids: string[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: ["lia-entity", "job", id] as const,
      queryFn: () => fetchEntity<T>(`/api/backend-proxy/job-vacancies/${id}`),
      enabled: ids.length > 0,
      staleTime: 30_000,
    })),
  })
}
