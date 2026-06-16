import type { JsonApiList, RemoteOption, SeniorityOption, UserSearchHit } from "./job-metadata.types"

const PROXY_BASE = "/api/backend-proxy"

async function getJson<T>(path: string, search?: Record<string, string>): Promise<T> {
  const origin = typeof window === "undefined" ? "http://localhost" : window.location.origin
  const url = new URL(path, origin)
  if (search) {
    for (const [k, v] of Object.entries(search)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v)
    }
  }
  const res = await fetch(url.toString(), { credentials: "include" })
  if (!res.ok) throw new Error(`HTTP ${res.status} ao buscar ${path}`)
  return res.json() as Promise<T>
}

function unwrap<T>(payload: JsonApiList<T> | T[] | { items?: T[] }): T[] {
  if (Array.isArray(payload)) return payload
  const p = payload as { data?: T[]; items?: T[] }
  return p?.data ?? p?.items ?? []
}

// ── Canonical options bundle ────────────────────────────────────────────────
// Onda 1 (audit 2026-06-06): FastAPI é a fonte única (Rails fora do fluxo).
// GET /job-vacancies/options serve os 6 vocabulários estáticos num único payload.
// Cacheado em módulo: 1 request, 6 consumidores. Em falha, limpa o cache p/ retry.
interface VacancyOptions {
  statuses: RemoteOption[]
  priorities: RemoteOption[]
  urgency_levels: RemoteOption[]
  work_models: RemoteOption[]
  employment_types: RemoteOption[]
  seniority_levels: RemoteOption[]
}

let optionsPromise: Promise<VacancyOptions> | undefined

function getVacancyOptions(): Promise<VacancyOptions> {
  if (!optionsPromise) {
    optionsPromise = getJson<VacancyOptions>(`${PROXY_BASE}/job-vacancies/options`).catch((e) => {
      optionsPromise = undefined
      throw e
    })
  }
  return optionsPromise
}

export async function fetchJobStatuses(): Promise<RemoteOption[]> {
  return (await getVacancyOptions()).statuses ?? []
}

export async function fetchJobPriorities(): Promise<RemoteOption[]> {
  return (await getVacancyOptions()).priorities ?? []
}

export async function fetchJobUrgencyLevels(): Promise<RemoteOption[]> {
  return (await getVacancyOptions()).urgency_levels ?? []
}

export async function fetchJobWorkplaceTypes(): Promise<RemoteOption[]> {
  return (await getVacancyOptions()).work_models ?? []
}

export async function fetchJobEmploymentTypes(): Promise<RemoteOption[]> {
  return (await getVacancyOptions()).employment_types ?? []
}

export async function fetchJobSeniorities(): Promise<SeniorityOption[]> {
  return ((await getVacancyOptions()).seniority_levels ?? []) as SeniorityOption[]
}

// ── Departments ─────────────────────────────────────────────────────────────
// Reusa o proxy canônico /company/departments (FastAPI, tenant-scoped) — o mesmo
// que o menu Configurações → Departamentos usa. NÃO existe /departments (era Rails).
export async function fetchDepartments(_search?: string): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(
    `${PROXY_BASE}/company/departments`,
  )
  return unwrap(raw)
}

// ── Cities ──────────────────────────────────────────────
// Onda 2B (audit 2026-06-06): dataset global IBGE (5.571 municipios) servido pelo
// FastAPI em /api/v1/cities, via proxy. Substitui a lista temporaria da Onda 1.
export async function fetchCities(search?: string): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(
    `${PROXY_BASE}/cities`,
    search ? { search } : undefined,
  )
  return unwrap(raw)
}

// ── User search (recruiter/manager picker — aba Pessoas) ─────────────────────
export async function searchUsers(query: string): Promise<UserSearchHit[]> {
  if (!query || query.length < 2) return []
  const raw = await getJson<JsonApiList<UserSearchHit> | UserSearchHit[]>(
    `${PROXY_BASE}/user-search`,
    { search: query },
  )
  return unwrap(raw)
}
