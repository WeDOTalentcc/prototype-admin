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

function unwrap<T>(payload: JsonApiList<T> | T[]): T[] {
  if (Array.isArray(payload)) return payload
  return payload.data ?? []
}

export async function fetchDepartments(search?: string): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(
    `${PROXY_BASE}/departments`,
    search ? { search } : undefined,
  )
  return unwrap(raw)
}

export async function fetchCities(search?: string): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(
    `${PROXY_BASE}/cities`,
    search ? { search } : undefined,
  )
  return unwrap(raw)
}

export async function fetchJobPriorities(): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/job-priorities`)
  return unwrap(raw)
}

export async function fetchJobUrgencyLevels(): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/job-urgency-levels`)
  return unwrap(raw)
}

export async function fetchJobWorkplaceTypes(): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/job-workplace-types`)
  return unwrap(raw)
}

export async function fetchJobEmploymentTypes(): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/job-employment-types`)
  return unwrap(raw)
}

export async function fetchJobSeniorities(): Promise<SeniorityOption[]> {
  const raw = await getJson<JsonApiList<SeniorityOption> | SeniorityOption[]>(`${PROXY_BASE}/job-seniorities`)
  return unwrap(raw)
}

export async function fetchJobStatuses(): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/job_statuses`)
  return unwrap(raw)
}

export async function searchUsers(query: string): Promise<UserSearchHit[]> {
  if (!query || query.length < 2) return []
  const raw = await getJson<JsonApiList<UserSearchHit> | UserSearchHit[]>(
    `${PROXY_BASE}/user-search`,
    { search: query },
  )
  return unwrap(raw)
}
