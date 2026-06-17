---
applyTo: "plataforma-lia/src/{lib/api,hooks,services,app/api}/**/*.ts,plataforma-lia/src/hooks/**/*.tsx"
---

# Data Fetching — WeDO Talent

Arquitetura em três camadas:

```
Client (hooks SWR, 'use client')
    ↓ fetch('/api/backend-proxy/...')
Next.js Route Handler (createProxyHandlers)
    ↓ fetch(BACKEND_URL + '/...', { Authorization: Bearer })
Backend (FastAPI hoje; Rails gradualmente)
```

- **Sem axios.** `fetch` nativo em todos os lugares.
- **JWT nunca vai para o browser.** O token está em cookie httpOnly e só o route handler o injeta em `Authorization`.
- **Toda chamada client passa por `/api/backend-proxy/*`.** Não chame `BACKEND_URL` direto.

## Camada 1 — Route Handler (server)

Use `createProxyHandlers` de `src/lib/api/proxy-handler.ts`. Ele já faz: leitura de cookies → header `Authorization`, timeout 30s, mapeamento de 4xx/5xx, unwrap do envelope `{ok, data}` do FastAPI, validação opcional com Zod.

### GET simples

```ts
// ✅ src/app/api/backend-proxy/jobs/route.ts
import { createProxyHandlers } from '@/lib/api/proxy-handler'

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: '/api/v1/jobs',
  methods: ['GET', 'POST'],
})
```

### Com path param

```ts
// ✅ src/app/api/backend-proxy/jobs/[id]/route.ts
export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: '/api/v1/jobs/:id',
  methods: ['GET', 'PUT', 'DELETE'],
})
```

O App Router passa `context.params` → resolvido pela template `:id`. Nome da variável em `params` **deve** bater com `:nome` no template.

### Rails target (migração gradual)

```ts
// ✅ src/app/api/backend-proxy/ats/candidates/route.ts
export const { dynamic, GET } = createProxyHandlers({
  backendPath: '/v1/users/candidates',
  backendTarget: 'rails',                  // usa RAILS_BACKEND_URL
  queryParamMap: { query: 'text' },        // renomeia ?query= → ?text=
})
```

### Validação de body com Zod

```ts
// ✅
import { jobCreateSchema } from '@/lib/schemas/job.schema'

export const { dynamic, POST } = createProxyHandlers({
  backendPath: '/api/v1/jobs',
  methods: ['POST'],
  bodySchema: jobCreateSchema,   // 400 automático se inválido
})
```

### Anti-padrões

```ts
// ❌ fetch cru repetido
export async function GET(req: NextRequest) {
  const auth = req.headers.get('authorization')
  const res = await fetch(`${process.env.BACKEND_URL}/api/v1/jobs`, {
    headers: { Authorization: auth ?? '' },
  })
  return new NextResponse(await res.text(), { status: res.status })
}

// ❌ endpoint especial que "faz várias coisas"
// route.ts que chama 3 endpoints do backend e agrega
```

Se precisar agregar, faça no backend. Se genuinamente não dá, documente o porquê e use `proxyFetchWithRetry` direto (ver abaixo).

### `proxyFetchWithRetry` — uso pontual

Quando um handler precisa de lógica customizada (streaming, upload, forwarding de múltiplos endpoints), use `proxyFetchWithRetry` de `src/lib/api/proxy-fetch-with-retry.ts`. Ele lida com auth headers + 401 retry.

```ts
// ✅ caso especial — streaming do chat
import { proxyFetchWithRetry } from '@/lib/api/proxy-fetch-with-retry'

export async function POST(request: NextRequest) {
  const body = await request.text()
  const res = await proxyFetchWithRetry(request, '/v1/chat/stream', {
    method: 'POST',
    body,
  })
  return new Response(res.body, { status: res.status, headers: res.headers })
}
```

## Camada 2 — Hooks de fetching (client, SWR)

**SWR é o padrão**. Não importe `useSWR` dentro de componentes de página — crie um hook em `src/hooks/<feature>/use-*.ts`.

### Fetcher compartilhado

Cada feature pode ter um fetcher local com `extractErrorMessage`:

```ts
// ✅ fetcher simples JSON
const jsonFetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = new Error(extractErrorMessage(body, res.status)) as Error & { status: number }
    err.status = res.status
    throw err
  }
  return res.json()
}
```

Quando a resposta é JSON:API (Rails), unwrap no fetcher:

```ts
// ✅
import { unwrapCollection, unwrapResource } from '@/lib/api/jsonapi'

const jsonApiListFetcher = async <T>(url: string) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const envelope = await res.json()
  return {
    items: unwrapCollection<T>(envelope),
    total: (envelope.meta?.total as number) ?? envelope.data.length,
  }
}
```

### Query keys — convenção de URL

A **URL completa com query string** é a chave SWR. Construa com `URLSearchParams`. Keys hierárquicas:

```
'/api/backend-proxy/jobs'                              ← list base
'/api/backend-proxy/jobs?status=open&page=1'           ← list filtrada
'/api/backend-proxy/jobs/42'                           ← detail
'/api/backend-proxy/jobs/42/candidates?stage=screen'   ← nested
```

```ts
// ✅
function buildJobsKey(filters: JobFilters): string {
  const qs = new URLSearchParams()
  if (filters.status) qs.set('status', filters.status)
  if (filters.search) qs.set('search', filters.search)
  qs.set('page', String(filters.page ?? 1))
  const s = qs.toString()
  return `/api/backend-proxy/jobs${s ? '?' + s : ''}`
}
```

Passe `null` para **desabilitar** o fetch (ex: falta um id):

```ts
const { data } = useSWR(jobId ? `/api/backend-proxy/jobs/${jobId}` : null, jsonFetcher)
```

### Hook padrão — list

```ts
// ✅ src/hooks/jobs/use-jobs.ts
'use client'

import useSWR from 'swr'
import { extractErrorMessage } from '@/lib/api/extract-error-message'

export interface Job {
  id: string
  title: string
  status: 'open' | 'closed' | 'draft'
  created_at: string
}

export interface JobFilters {
  status?: string
  search?: string
  page?: number
  per_page?: number
}

interface UseJobsReturn {
  jobs: Job[]
  total: number
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
}

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(extractErrorMessage(body, res.status))
  }
  return res.json() as Promise<{ data: Job[]; meta: { total: number } }>
}

export function useJobs(filters: JobFilters = {}): UseJobsReturn {
  const qs = new URLSearchParams()
  if (filters.status) qs.set('status', filters.status)
  if (filters.search) qs.set('search', filters.search)
  qs.set('page', String(filters.page ?? 1))
  qs.set('per_page', String(filters.per_page ?? 20))

  const { data, error, isLoading, mutate } = useSWR(
    `/api/backend-proxy/jobs?${qs}`,
    fetcher,
    { revalidateOnFocus: false },
  )

  return {
    jobs: data?.data ?? [],
    total: data?.meta?.total ?? 0,
    isLoading,
    error: (error as Error | undefined)?.message ?? null,
    refresh: async () => { await mutate() },
  }
}
```

### Hook padrão — detail

```ts
// ✅ src/hooks/jobs/use-job.ts
export function useJob(id: string | null) {
  const { data, error, isLoading, mutate } = useSWR<Job>(
    id ? `/api/backend-proxy/jobs/${id}` : null,
    fetcher,
  )
  return {
    job: data ?? null,
    isLoading,
    error: (error as Error | undefined)?.message ?? null,
    refresh: async () => { await mutate() },
  }
}
```

### Invalidação entre hooks

Use a versão global de `mutate` com predicate de chave para invalidar múltiplas queries após uma mutation:

```ts
// ✅ src/hooks/jobs/use-create-job.ts
'use client'

import { useState } from 'react'
import { mutate } from 'swr'
import { extractErrorMessage } from '@/lib/api/extract-error-message'

export function useCreateJob() {
  const [isCreating, setIsCreating] = useState(false)

  const createJob = async (input: JobCreateInput): Promise<Job | null> => {
    setIsCreating(true)
    try {
      const res = await fetch('/api/backend-proxy/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(body, res.status))
      }
      const job: Job = await res.json()

      // Invalida qualquer key que comece com '/api/backend-proxy/jobs'
      await mutate(
        (key) => typeof key === 'string' && key.startsWith('/api/backend-proxy/jobs'),
        undefined,
        { revalidate: true },
      )

      return job
    } finally {
      setIsCreating(false)
    }
  }

  return { createJob, isCreating }
}
```

**Regra**: toda mutation invalida as queries afetadas. Nunca "atualizar à mão" o estado retornando dados manualmente sem revalidate.

### Config SWR por hook

Defaults sensatos do projeto:

| Opção | Valor padrão | Quando mudar |
|---|---|---|
| `revalidateOnFocus` | `false` | mudar só se o dado muda com frequência fora da app |
| `revalidateIfStale` | `true` | manter |
| `dedupingInterval` | `5000` (5s) | aumentar para lists pesadas |
| `keepPreviousData` | `false` | usar em paginação para evitar flicker |

```ts
// ✅ list paginada
const { data, isLoading } = useSWR(key, fetcher, {
  revalidateOnFocus: false,
  keepPreviousData: true,
})
```

### Request cancel

SWR já desduplica e cancela queries antigas ao mudar a key. Se precisar cancelamento manual (ex: search com debounce), faça debounce **antes** de compor a key — não `AbortController` dentro do fetcher.

## JSON:API helpers

`src/lib/api/jsonapi.ts` tem:

- `unwrapCollection<T>(envelope)` → `Array<T & { id }>`
- `unwrapResource<T>(envelope)` → `T & { id }`
- `isJsonApiEnvelope(value)` — type guard

Use quando falar com Rails:

```ts
const res = await fetch('/api/backend-proxy/ats/jobs')
const envelope = await res.json()
const jobs = unwrapCollection<JobAttrs>(envelope)
// jobs[0].id, jobs[0].title, ...
```

## Tratamento de erro — padrão único

**Sempre** via `extractErrorMessage`. Ele cobre: FastAPI `{ detail }`, Rails `{ errors }`, proxy `{ error, details }`, fallback `HTTP <status>`.

```ts
// ✅
if (!res.ok) {
  const body = await res.json().catch(() => ({}))
  throw new Error(extractErrorMessage(body, res.status))
}

// ❌
if (!res.ok) throw new Error('Erro ao buscar vagas')  // genérico, perde info
if (!res.ok) throw new Error(await res.text())        // pode dar HTML inteiro
```

Classifique `err.status` quando precisar roteamento de UX (401 → relogin, 403 → forbidden):

```ts
const err = new Error(message) as Error & { status: number }
err.status = res.status
throw err
```

## Three states — sempre

Todo componente que consome um hook de fetch mostra:

```tsx
const { jobs, isLoading, error, refresh } = useJobs()

if (isLoading) return <Skeleton />
if (error)     return <ErrorState message={error} onRetry={refresh} />
if (jobs.length === 0) return <EmptyState title="Sem vagas" />

return <JobsList jobs={jobs} />
```

Ver `react-components.instructions.md` para padrão.

## Paginação

Server-side via query params (`page`, `per_page`). Use `keepPreviousData` no SWR para evitar piscadas.

```ts
const { data, isLoading } = useSWR(
  buildJobsKey({ ...filters, page }),
  fetcher,
  { keepPreviousData: true },
)
```

## Rules

- **Hooks de fetch vivem em `src/hooks/<feature>/`** — um por query/mutation.
- **SWR key = URL completa** (`/api/backend-proxy/...?qs`).
- **`null` key desabilita** o fetch.
- **`createProxyHandlers`** no route handler — não escreva `fetch` cru.
- **`extractErrorMessage`** no tratamento de erro.
- **`mutate(predicate)`** após mutation que afete múltiplas keys.
- **Três estados**: loading, error, empty — obrigatórios.
- **JWT nunca no browser** — `localStorage` de token é dívida.
- **Sem axios**. Sem tanstack-query.
- **Sem fetch direto para `BACKEND_URL`** de código client.
- **JSON:API** unwrapped via helpers em `src/lib/api/jsonapi.ts` quando vier do Rails.
