# Vaga · Workstream 1 — Job Metadata + Step 1 (General) Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Destravar o form de edição de vaga (aba "Informações Gerais") com autocompletes vindos do backend Rails, atingindo paridade funcional com o legado Nuxt para o Step 1 do spec `2026-04-19-vaga-cadastro-edicao-paridade-legacy-design.md`.

**Architecture:**
- Proxy routes Next → Rails via `createProxyHandlers` helper existente em `@/lib/api/proxy-handler`.
- Service module tipado `job-metadata.service.ts` encapsulando 8 endpoints de metadata.
- Hook `useJobMetadata` com SWR (já no projeto) oferecendo cache compartilhado por recurso.
- Componente genérico `RemoteCombobox` baseado no `cmdk` (já instalado via `components/ui/command`) para reuso em múltiplos steps.
- Patch cirúrgico em `JobInfoGeralSection.tsx` substituindo selects estáticos por `RemoteCombobox` sem mudar layout.

**Tech Stack:** Next.js 15 App Router · TypeScript · SWR · Radix/Popover · cmdk · Tailwind · Vitest · React Testing Library.

**Spec de referência:** `docs/superpowers/specs/2026-04-19-vaga-cadastro-edicao-paridade-legacy-design.md` §4.1 (camada de serviços), §4.2 (hooks), §4.3 (proxies), §11.2 (Step General do legado).

**Branch:** trabalhar em `develop` (padrão do projeto).

---

## File Structure

Arquivos a criar:

```
plataforma-lia/src/app/api/backend-proxy/
├── departments/route.ts                      ← GET /v1/users/departments
├── cities/route.ts                           ← GET /v1/users/cities
├── job-priorities/route.ts                   ← GET /v1/users/jobs/priorities
├── job-urgency-levels/route.ts               ← GET /v1/users/jobs/urgency_levels
├── job-workplace-types/route.ts              ← GET /v1/users/jobs/workplace_types
├── job-employment-types/route.ts             ← GET /v1/users/jobs/employment_types
├── job-seniorities/route.ts                  ← GET /v1/users/jobs/seniorities
└── user-search/route.ts                      ← GET /v1/users/search

plataforma-lia/src/services/jobs/
├── job-metadata.service.ts                   ← funções fetchXxx tipadas
└── __tests__/job-metadata.service.test.ts

plataforma-lia/src/hooks/jobs/
├── use-job-metadata.ts                       ← hook SWR único com subfunções
└── __tests__/use-job-metadata.test.tsx

plataforma-lia/src/components/ui/
└── remote-combobox.tsx                       ← Combobox genérico com remote data
```

Arquivos a modificar:

```
plataforma-lia/src/components/jobs/job-edit-tab/
├── JobInfoGeralSection.tsx                   ← trocar 7 selects por RemoteCombobox
├── job-edit-tab.constants.ts                 ← adicionar 'city' aos fields
└── useJobEditTab.ts                          ← aceitar objetos `*_attributes` em updateField
```

---

## Premissas técnicas validadas

1. **Proxy helper existe** (`createProxyHandlers`, `src/lib/api/proxy-handler.ts`). Passar `backendTarget: "rails"` para direcionar ao Rails (`RAILS_BACKEND_URL`).
2. **`/backend-proxy/job_statuses`** já existe (mesmo padrão a seguir).
3. **`cmdk`** já instalado via `components/ui/command`.
4. **SWR** já é dependência; padrão no projeto em outros hooks (ex: `useJobFiltersPersistence`).
5. **`JobInfoGeralSection.tsx`** recebe `updateField(name, value)` do hook pai (`useJobEditTab`) — interface estável; só o valor muda (string → object onde aplicável).

## Open questions do spec (§14)

Resolvidas para este workstream:
- `job-seniorities` retorna array de `{ id, name, level? }` (padrão JSON:API). Service assume esse shape; teste mock valida.
- `departments` e `cities` aceitam `?search=` (padrão Rails). Service passa como query param.

Não afetam este workstream:
- Criar vaga com só título+depto+cidade → Workstream 2.
- `jd_dimensions` populado → Workstream 6.

---

## Tasks

### Task 1: Proxy route — `departments`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/departments/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/departments",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Lint passa**

Run: `npx eslint plataforma-lia/src/app/api/backend-proxy/departments/route.ts`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/departments/route.ts
git commit -m "feat(proxy): rota /backend-proxy/departments → Rails /users/departments"
```

---

### Task 2: Proxy route — `cities`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/cities/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/cities",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/cities/route.ts
git commit -m "feat(proxy): rota /backend-proxy/cities → Rails /users/cities"
```

---

### Task 3: Proxy route — `job-priorities`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/job-priorities/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/jobs/priorities",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/job-priorities/route.ts
git commit -m "feat(proxy): rota /backend-proxy/job-priorities → Rails /users/jobs/priorities"
```

---

### Task 4: Proxy route — `job-urgency-levels`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/job-urgency-levels/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/jobs/urgency_levels",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/job-urgency-levels/route.ts
git commit -m "feat(proxy): rota /backend-proxy/job-urgency-levels → Rails /users/jobs/urgency_levels"
```

---

### Task 5: Proxy route — `job-workplace-types`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/job-workplace-types/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/jobs/workplace_types",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/job-workplace-types/route.ts
git commit -m "feat(proxy): rota /backend-proxy/job-workplace-types → Rails /users/jobs/workplace_types"
```

---

### Task 6: Proxy route — `job-employment-types`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/job-employment-types/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/jobs/employment_types",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/job-employment-types/route.ts
git commit -m "feat(proxy): rota /backend-proxy/job-employment-types → Rails /users/jobs/employment_types"
```

---

### Task 7: Proxy route — `job-seniorities`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/job-seniorities/route.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/jobs/seniorities",
  backendTarget: "rails",
  methods: ["GET"],
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/job-seniorities/route.ts
git commit -m "feat(proxy): rota /backend-proxy/job-seniorities → Rails /users/jobs/seniorities"
```

---

### Task 8: Proxy route — `user-search`

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/user-search/route.ts`

Rails usa `/v1/users/search?q=...`. Usamos `queryParamMap` para aceitar `?search=` do frontend e mapear para `?q=`.

- [ ] **Step 1: Criar o arquivo**

```ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/v1/users/search",
  backendTarget: "rails",
  methods: ["GET"],
  queryParamMap: { search: "q" },
})
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/app/api/backend-proxy/user-search/route.ts
git commit -m "feat(proxy): rota /backend-proxy/user-search → Rails /users/search (search→q)"
```

---

### Task 9: Types compartilhados do metadata

**Files:**
- Create: `plataforma-lia/src/services/jobs/job-metadata.types.ts`

Define shapes JSON:API que o Rails retorna para cada endpoint.

- [ ] **Step 1: Criar o arquivo**

```ts
export interface RemoteOption {
  id: string | number
  name: string
  description?: string
  code?: string
}

export interface SeniorityOption extends RemoteOption {
  level?: number
}

export interface UserSearchHit {
  id: string | number
  name: string
  email: string
  role?: string | null
  avatar?: string | null
}

export interface JsonApiList<T> {
  data: T[]
  meta?: { total?: number }
}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/services/jobs/job-metadata.types.ts
git commit -m "feat(services): tipos compartilhados de metadata de vaga"
```

---

### Task 10: Service — `job-metadata.service.ts`

**Files:**
- Create: `plataforma-lia/src/services/jobs/job-metadata.service.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
import type { JsonApiList, RemoteOption, SeniorityOption, UserSearchHit } from "./job-metadata.types"

const PROXY_BASE = "/api/backend-proxy"

async function getJson<T>(path: string, search?: Record<string, string>): Promise<T> {
  const url = new URL(path, typeof window === "undefined" ? "http://localhost" : window.location.origin)
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
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/departments`, search ? { search } : undefined)
  return unwrap(raw)
}

export async function fetchCities(search?: string): Promise<RemoteOption[]> {
  const raw = await getJson<JsonApiList<RemoteOption> | RemoteOption[]>(`${PROXY_BASE}/cities`, search ? { search } : undefined)
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
  const raw = await getJson<JsonApiList<UserSearchHit> | UserSearchHit[]>(`${PROXY_BASE}/user-search`, { search: query })
  return unwrap(raw)
}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/services/jobs/job-metadata.service.ts
git commit -m "feat(services): job-metadata.service — 9 fetchers tipados"
```

---

### Task 11: Testes do service

**Files:**
- Create: `plataforma-lia/src/services/jobs/__tests__/job-metadata.service.test.ts`

- [ ] **Step 1: Escrever os testes (mock fetch)**

```ts
import { describe, it, expect, beforeEach, vi } from "vitest"
import {
  fetchDepartments, fetchCities, fetchJobPriorities, fetchJobWorkplaceTypes,
  fetchJobEmploymentTypes, fetchJobSeniorities, searchUsers,
} from "../job-metadata.service"

const mockJson = (data: unknown) => ({
  ok: true, status: 200, json: () => Promise.resolve(data),
}) as unknown as Response

describe("job-metadata.service", () => {
  beforeEach(() => {
    global.fetch = vi.fn() as unknown as typeof fetch
  })

  it("unwraps JSON:API {data:[]} para departments", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [{ id: 1, name: "Eng" }] }))
    const out = await fetchDepartments()
    expect(out).toEqual([{ id: 1, name: "Eng" }])
  })

  it("aceita array cru (sem envelope data)", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson([{ id: 2, name: "RH" }]))
    const out = await fetchDepartments()
    expect(out).toEqual([{ id: 2, name: "RH" }])
  })

  it("passa ?search quando fornecido em cities", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [] }))
    await fetchCities("são paulo")
    const url = vi.mocked(global.fetch).mock.calls[0][0] as string
    expect(url).toContain("search=s%C3%A3o+paulo")
  })

  it("priorities sem search param", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [] }))
    await fetchJobPriorities()
    const url = vi.mocked(global.fetch).mock.calls[0][0] as string
    expect(url).not.toContain("search=")
  })

  it("workplace/employment/seniorities retornam array", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [{ id: 1, name: "Remoto" }] }))
    expect(await fetchJobWorkplaceTypes()).toHaveLength(1)
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [{ id: 1, name: "CLT" }] }))
    expect(await fetchJobEmploymentTypes()).toHaveLength(1)
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [{ id: 1, name: "Pleno", level: 3 }] }))
    expect(await fetchJobSeniorities()).toEqual([{ id: 1, name: "Pleno", level: 3 }])
  })

  it("searchUsers faz nada se query tem <2 chars", async () => {
    const out = await searchUsers("a")
    expect(out).toEqual([])
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it("searchUsers passa ?search com query válida", async () => {
    vi.mocked(global.fetch).mockResolvedValue(mockJson({ data: [{ id: "u1", name: "Ana", email: "a@a.com" }] }))
    const out = await searchUsers("ana")
    expect(out).toHaveLength(1)
    const url = vi.mocked(global.fetch).mock.calls[0][0] as string
    expect(url).toContain("search=ana")
  })

  it("propaga erro HTTP", async () => {
    vi.mocked(global.fetch).mockResolvedValue({ ok: false, status: 500, json: () => Promise.resolve({}) } as unknown as Response)
    await expect(fetchDepartments()).rejects.toThrow(/HTTP 500/)
  })
})
```

- [ ] **Step 2: Rodar e ver todos passarem**

Run: `npx vitest run plataforma-lia/src/services/jobs/__tests__/job-metadata.service.test.ts`
Expected: 8 passed.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/services/jobs/__tests__/job-metadata.service.test.ts
git commit -m "test(services): job-metadata.service — 8 cenários (envelope, search, erros)"
```

---

### Task 12: Hook `useJobMetadata`

**Files:**
- Create: `plataforma-lia/src/hooks/jobs/use-job-metadata.ts`

- [ ] **Step 1: Criar o arquivo**

```ts
"use client"

import useSWR from "swr"
import {
  fetchDepartments, fetchCities, fetchJobPriorities, fetchJobUrgencyLevels,
  fetchJobWorkplaceTypes, fetchJobEmploymentTypes, fetchJobSeniorities,
  fetchJobStatuses, searchUsers,
} from "@/services/jobs/job-metadata.service"
import type { RemoteOption, SeniorityOption, UserSearchHit } from "@/services/jobs/job-metadata.types"

const SHARED_CONFIG = {
  revalidateOnFocus: false,
  dedupingInterval: 60_000,
  shouldRetryOnError: false,
} as const

export function useJobStatuses() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-statuses", fetchJobStatuses, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobPriorities() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-priorities", fetchJobPriorities, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobUrgencyLevels() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-urgency-levels", fetchJobUrgencyLevels, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobWorkplaceTypes() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-workplace-types", fetchJobWorkplaceTypes, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobEmploymentTypes() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-employment-types", fetchJobEmploymentTypes, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobSeniorities() {
  const { data, error, isLoading } = useSWR<SeniorityOption[]>("job-seniorities", fetchJobSeniorities, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useDepartmentsSearch(query: string) {
  const key = query.length >= 0 ? ["departments", query] : null
  const { data, error, isLoading } = useSWR<RemoteOption[]>(
    key, ([, q]) => fetchDepartments(q as string), SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}

export function useCitiesSearch(query: string) {
  const key = query.length >= 0 ? ["cities", query] : null
  const { data, error, isLoading } = useSWR<RemoteOption[]>(
    key, ([, q]) => fetchCities(q as string), SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}

export function useUserSearch(query: string) {
  const key = query.length >= 2 ? ["user-search", query] : null
  const { data, error, isLoading } = useSWR<UserSearchHit[]>(
    key, ([, q]) => searchUsers(q as string), SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/hooks/jobs/use-job-metadata.ts
git commit -m "feat(hooks): use-job-metadata — 9 sub-hooks SWR (dedupe 60s)"
```

---

### Task 13: Componente `RemoteCombobox`

**Files:**
- Create: `plataforma-lia/src/components/ui/remote-combobox.tsx`

Componente reusável. Aceita `options` externas (do hook), `value`, `onChange`, opcional `onSearchChange` para busca remota.

- [ ] **Step 1: Criar o arquivo**

```tsx
"use client"

import * as React from "react"
import { Check, ChevronsUpDown, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

export interface RemoteComboboxOption {
  id: string | number
  name: string
  description?: string
}

interface RemoteComboboxProps {
  value: RemoteComboboxOption | null
  onChange: (value: RemoteComboboxOption | null) => void
  options: RemoteComboboxOption[]
  isLoading?: boolean
  onSearchChange?: (query: string) => void
  placeholder?: string
  emptyText?: string
  disabled?: boolean
  className?: string
  triggerClassName?: string
  /** Se true, `value` é só exibição e não salva. */
  readOnly?: boolean
}

export function RemoteCombobox({
  value, onChange, options, isLoading, onSearchChange,
  placeholder = "Selecionar…", emptyText = "Nenhum resultado",
  disabled = false, className, triggerClassName, readOnly = false,
}: RemoteComboboxProps) {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState("")

  React.useEffect(() => {
    if (!onSearchChange) return
    const t = setTimeout(() => onSearchChange(query), 250)
    return () => clearTimeout(t)
  }, [query, onSearchChange])

  const label = value?.name ?? placeholder
  const buttonDisabled = disabled || readOnly

  return (
    <div className={className}>
      <Popover open={open} onOpenChange={buttonDisabled ? undefined : setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={buttonDisabled}
            className={cn(
              "w-full justify-between h-9 text-xs font-normal",
              !value && "text-lia-text-tertiary",
              triggerClassName,
            )}
          >
            <span className="truncate">{label}</span>
            <ChevronsUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0 w-[var(--radix-popover-trigger-width)]" align="start">
          <Command shouldFilter={!onSearchChange}>
            <CommandInput
              value={query}
              onValueChange={setQuery}
              placeholder="Buscar…"
              className="h-9"
            />
            <CommandList>
              {isLoading && (
                <div className="flex items-center justify-center py-4 text-lia-text-tertiary">
                  <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
                </div>
              )}
              {!isLoading && options.length === 0 && (
                <CommandEmpty>{emptyText}</CommandEmpty>
              )}
              {!isLoading && options.length > 0 && (
                <CommandGroup>
                  {options.map((option) => (
                    <CommandItem
                      key={`${option.id}`}
                      value={option.name}
                      onSelect={() => {
                        onChange(option)
                        setOpen(false)
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          value?.id === option.id ? "opacity-100" : "opacity-0",
                        )}
                      />
                      <span className="truncate">{option.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
```

- [ ] **Step 2: Verificar `Popover` existe**

Run: `ls plataforma-lia/src/components/ui/popover.tsx`
Expected: arquivo existe.

- [ ] **Step 3: Lint + type-check**

Run: `npx tsc --noEmit -p plataforma-lia/tsconfig.json 2>&1 | grep -E "remote-combobox" || echo OK`
Expected: "OK".

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/components/ui/remote-combobox.tsx
git commit -m "feat(ui): RemoteCombobox genérico (cmdk + popover + loading)"
```

---

### Task 14: Teste básico do `RemoteCombobox`

**Files:**
- Create: `plataforma-lia/src/components/ui/__tests__/remote-combobox.test.tsx`

- [ ] **Step 1: Escrever o teste**

```tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { RemoteCombobox } from "../remote-combobox"

const opts = [{ id: 1, name: "Eng" }, { id: 2, name: "RH" }]

describe("RemoteCombobox", () => {
  it("mostra placeholder quando value é null", () => {
    render(<RemoteCombobox value={null} onChange={() => {}} options={[]} placeholder="Dept" />)
    expect(screen.getByRole("combobox")).toHaveTextContent("Dept")
  })

  it("mostra name quando value é preenchido", () => {
    render(<RemoteCombobox value={{ id: 1, name: "Eng" }} onChange={() => {}} options={opts} />)
    expect(screen.getByRole("combobox")).toHaveTextContent("Eng")
  })

  it("chama onChange ao selecionar", async () => {
    const spy = vi.fn()
    render(<RemoteCombobox value={null} onChange={spy} options={opts} />)
    fireEvent.click(screen.getByRole("combobox"))
    const item = await screen.findByText("Eng")
    fireEvent.click(item)
    expect(spy).toHaveBeenCalledWith({ id: 1, name: "Eng" })
  })

  it("dispara onSearchChange com debounce", async () => {
    vi.useFakeTimers()
    const spy = vi.fn()
    render(<RemoteCombobox value={null} onChange={() => {}} options={opts} onSearchChange={spy} />)
    fireEvent.click(screen.getByRole("combobox"))
    const input = screen.getByPlaceholderText("Buscar…")
    fireEvent.change(input, { target: { value: "eng" } })
    expect(spy).not.toHaveBeenCalled()
    vi.advanceTimersByTime(260)
    expect(spy).toHaveBeenCalledWith("eng")
    vi.useRealTimers()
  })

  it("não abre quando disabled", () => {
    render(<RemoteCombobox value={null} onChange={() => {}} options={opts} disabled />)
    const btn = screen.getByRole("combobox") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })
})
```

- [ ] **Step 2: Rodar**

Run: `npx vitest run plataforma-lia/src/components/ui/__tests__/remote-combobox.test.tsx`
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/ui/__tests__/remote-combobox.test.tsx
git commit -m "test(ui): RemoteCombobox — placeholder, onChange, debounced search"
```

---

### Task 15: Expor `city` no SECTIONS do form

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts`

- [ ] **Step 1: Ler o array SECTIONS atual**

Run: `sed -n '17,28p' plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts`
Expected: array com `"title", "department", "location", ...`.

- [ ] **Step 2: Adicionar `city` ao fields de `info-geral`**

Edit: em `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts`, substituir:

```ts
    fields: [
      "title", "department", "location", "workModel", "type", "level",
```

por:

```ts
    fields: [
      "title", "department", "location", "city", "workModel", "type", "level",
```

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts
git commit -m "feat(jobs): adiciona campo city ao fields de info-geral"
```

---

### Task 16: Importar hooks e combobox em `JobInfoGeralSection`

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar imports no topo do arquivo (após imports existentes)**

No início do arquivo, após a última linha `import`, adicionar:

```tsx
import { RemoteCombobox, type RemoteComboboxOption } from "@/components/ui/remote-combobox"
import {
  useJobStatuses, useJobPriorities, useJobUrgencyLevels,
  useJobWorkplaceTypes, useJobEmploymentTypes, useJobSeniorities,
  useDepartmentsSearch, useCitiesSearch,
} from "@/hooks/jobs/use-job-metadata"
```

- [ ] **Step 2: Commit (imports isoladamente, fácil de reverter)**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "chore(jobs): importa hooks de metadata + RemoteCombobox em InfoGeral"
```

---

### Task 17: Substituir select de `department` por RemoteCombobox

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Identificar o JSX atual do campo department**

Run: `grep -n "department" plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`
Expected: linhas do input `value={(jobEditForm.department as string) || ""}`.

- [ ] **Step 2: Adicionar state de query no topo do componente**

No início do body da função `JobInfoGeralSection`, logo após os hooks/props existentes, adicionar:

```tsx
  const [departmentQuery, setDepartmentQuery] = React.useState("")
  const { options: departmentOptions, isLoading: departmentLoading } = useDepartmentsSearch(departmentQuery)
```

- [ ] **Step 3: Substituir o input de department pelo combobox**

Localizar o `<input ... value={(jobEditForm.department as string) || ""} ...>` (~linha 142 conforme gap analysis) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.department && typeof jobEditForm.department === "object"
        ? (jobEditForm.department as RemoteComboboxOption)
        : jobEditForm.department
          ? { id: String(jobEditForm.department), name: String(jobEditForm.department) }
          : null
    }
    onChange={(opt) => updateField("department", opt)}
    options={departmentOptions}
    isLoading={departmentLoading}
    onSearchChange={setDepartmentQuery}
    placeholder="Selecione um departamento"
    disabled={!isEditing}
  />
```

- [ ] **Step 4: Rodar type-check**

Run: `npx tsc --noEmit -p plataforma-lia/tsconfig.json 2>&1 | grep -E "JobInfoGeralSection" || echo OK`
Expected: "OK".

- [ ] **Step 5: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): department agora é RemoteCombobox (autocomplete backend)"
```

---

### Task 18: Adicionar campo `city` (antes de workModel)

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: State de query de city**

Após o state de `departmentQuery`, adicionar:

```tsx
  const [cityQuery, setCityQuery] = React.useState("")
  const { options: cityOptions, isLoading: cityLoading } = useCitiesSearch(cityQuery)
```

- [ ] **Step 2: Adicionar bloco JSX do campo `city` logo após `location`**

Depois do bloco do campo `location` (~linha 146), antes do bloco de `workModel`, inserir:

```tsx
  <div>
    <label className={labelClass}>Cidade</label>
    <RemoteCombobox
      value={
        jobEditForm.city && typeof jobEditForm.city === "object"
          ? (jobEditForm.city as RemoteComboboxOption)
          : jobEditForm.city
            ? { id: String(jobEditForm.city), name: String(jobEditForm.city) }
            : null
      }
      onChange={(opt) => updateField("city", opt)}
      options={cityOptions}
      isLoading={cityLoading}
      onSearchChange={setCityQuery}
      placeholder="Busque uma cidade"
      disabled={!isEditing}
    />
  </div>
```

- [ ] **Step 3: Type-check**

Run: `npx tsc --noEmit -p plataforma-lia/tsconfig.json 2>&1 | grep -E "JobInfoGeralSection" || echo OK`
Expected: "OK".

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): adiciona campo city com autocomplete"
```

---

### Task 19: Substituir select de `workModel` por backend

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

No topo do componente:

```tsx
  const { options: workplaceOptions, isLoading: workplaceLoading } = useJobWorkplaceTypes()
```

- [ ] **Step 2: Substituir o select atual**

Localizar o `<select ... value={(jobEditForm.workModel as string) || ""} ...>` (~linha 165) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.workModel && typeof jobEditForm.workModel === "object"
        ? (jobEditForm.workModel as RemoteComboboxOption)
        : jobEditForm.workModel
          ? { id: String(jobEditForm.workModel), name: String(jobEditForm.workModel) }
          : null
    }
    onChange={(opt) => updateField("workModel", opt?.name ?? null)}
    options={workplaceOptions}
    isLoading={workplaceLoading}
    placeholder="Selecione o modelo de trabalho"
    disabled={!isEditing}
  />
```

> Observação: `workModel` é string no backend legacy (§11.2 do spec, "não objeto"). Usamos `opt?.name` no onChange.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): workModel agora puxa workplace_types do backend"
```

---

### Task 20: Substituir select de `type` (employment_type)

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

```tsx
  const { options: employmentOptions, isLoading: employmentLoading } = useJobEmploymentTypes()
```

- [ ] **Step 2: Substituir o select de `type`**

Localizar `<select ... value={(jobEditForm.type as string) || ""}` (~linha 184) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.type && typeof jobEditForm.type === "object"
        ? (jobEditForm.type as RemoteComboboxOption)
        : jobEditForm.type
          ? { id: String(jobEditForm.type), name: String(jobEditForm.type) }
          : null
    }
    onChange={(opt) => updateField("type", opt)}
    options={employmentOptions}
    isLoading={employmentLoading}
    placeholder="Tipo de contrato"
    disabled={!isEditing}
  />
```

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): type (employment_type) agora vem do backend"
```

---

### Task 21: Substituir select de `level` (seniority)

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

```tsx
  const { options: seniorityOptions, isLoading: seniorityLoading } = useJobSeniorities()
```

- [ ] **Step 2: Substituir o select de `level`**

Localizar `<select ... value={(jobEditForm.level as string) || ""}` (~linha 195) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.level && typeof jobEditForm.level === "object"
        ? (jobEditForm.level as RemoteComboboxOption)
        : jobEditForm.level
          ? { id: String(jobEditForm.level), name: String(jobEditForm.level) }
          : null
    }
    onChange={(opt) => updateField("level", opt)}
    options={seniorityOptions}
    isLoading={seniorityLoading}
    placeholder="Senioridade"
    disabled={!isEditing}
  />
```

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): level (seniority) agora vem do backend"
```

---

### Task 22: Substituir select de `priority`

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

```tsx
  const { options: priorityOptions, isLoading: priorityLoading } = useJobPriorities()
```

- [ ] **Step 2: Substituir o select de `priority`**

Localizar `<select ... value={(jobEditForm.priority as string) || ""}` (~linha 84) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.priority && typeof jobEditForm.priority === "object"
        ? (jobEditForm.priority as RemoteComboboxOption)
        : jobEditForm.priority
          ? { id: String(jobEditForm.priority), name: String(jobEditForm.priority) }
          : null
    }
    onChange={(opt) => updateField("priority", opt)}
    options={priorityOptions}
    isLoading={priorityLoading}
    placeholder="Prioridade"
    disabled={!isEditing}
  />
```

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): priority agora vem do backend"
```

---

### Task 23: Substituir select de `urgencyLevel`

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

```tsx
  const { options: urgencyOptions, isLoading: urgencyLoading } = useJobUrgencyLevels()
```

- [ ] **Step 2: Substituir o select de `urgencyLevel`**

Localizar `<select ... value={(jobEditForm.urgencyLevel as string)` (~linha 93) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.urgencyLevel && typeof jobEditForm.urgencyLevel === "object"
        ? (jobEditForm.urgencyLevel as RemoteComboboxOption)
        : jobEditForm.urgencyLevel
          ? { id: String(jobEditForm.urgencyLevel), name: String(jobEditForm.urgencyLevel) }
          : null
    }
    onChange={(opt) => updateField("urgencyLevel", opt)}
    options={urgencyOptions}
    isLoading={urgencyLoading}
    placeholder="Urgência"
    disabled={!isEditing}
  />
```

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): urgencyLevel agora vem do backend"
```

---

### Task 24: Substituir select de `status`

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`

- [ ] **Step 1: Adicionar hook**

```tsx
  const { options: statusOptions, isLoading: statusLoading } = useJobStatuses()
```

- [ ] **Step 2: Substituir o select de `status`**

Localizar `<select ... value={(jobEditForm.status as string)` (~linha 59) e trocar por:

```tsx
  <RemoteCombobox
    value={
      jobEditForm.status && typeof jobEditForm.status === "object"
        ? (jobEditForm.status as RemoteComboboxOption)
        : jobEditForm.status
          ? { id: String(jobEditForm.status), name: String(jobEditForm.status) }
          : null
    }
    onChange={(opt) => updateField("status", opt?.name ?? null)}
    options={statusOptions}
    isLoading={statusLoading}
    placeholder="Status"
    disabled={!isEditing}
  />
```

> `status` no legado é string (nome), então extraímos `opt?.name`.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx
git commit -m "feat(jobs): status agora vem de job_statuses do backend"
```

---

### Task 25: Helper `toAttributesPayload` (utilitário puro + testes)

**Files:**
- Create: `plataforma-lia/src/services/jobs/job-payload.ts`
- Create: `plataforma-lia/src/services/jobs/__tests__/job-payload.test.ts`

Cria um utilitário puro que transforma `jobEditForm` no shape esperado pelo backend legado (`*_attributes` para objects + renomes `workModel→workplace_type`, `status→job_status`, `level→seniority_attributes`, `type→employment_type_attributes`, `urgencyLevel→urgency_level_attributes`). A **integração** deste helper na cadeia de save fica a cargo da Task 27 (smoke manual) — quem executar identifica no Network onde o body é montado e injeta a chamada. Isolar o utilitário permite testá-lo sem mexer no fluxo de save ainda desconhecido.

- [ ] **Step 1: Criar o helper**

```ts
export type JobFormObjectField = { id: string | number; name: string } | null | undefined

const OBJECT_TO_ATTRIBUTES: Record<string, string> = {
  department: "department_attributes",
  city: "city_attributes",
  priority: "priority_attributes",
  urgencyLevel: "urgency_level_attributes",
  type: "employment_type_attributes",
  level: "seniority_attributes",
}

const RENAMES: Record<string, string> = {
  workModel: "workplace_type",
  status: "job_status",
}

export function toAttributesPayload(
  form: Record<string, unknown>,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(form)) {
    if (key in OBJECT_TO_ATTRIBUTES && value && typeof value === "object") {
      payload[OBJECT_TO_ATTRIBUTES[key]] = value
      continue
    }
    if (key in RENAMES) {
      payload[RENAMES[key]] = value
      continue
    }
    payload[key] = value
  }

  return payload
}
```

- [ ] **Step 2: Criar os testes**

```ts
import { describe, it, expect } from "vitest"
import { toAttributesPayload } from "../job-payload"

describe("toAttributesPayload", () => {
  it("mapeia department object → department_attributes", () => {
    const out = toAttributesPayload({ department: { id: 1, name: "Eng" } })
    expect(out).toEqual({ department_attributes: { id: 1, name: "Eng" } })
  })

  it("mapeia urgencyLevel → urgency_level_attributes", () => {
    const out = toAttributesPayload({ urgencyLevel: { id: 4, name: "Alta" } })
    expect(out).toEqual({ urgency_level_attributes: { id: 4, name: "Alta" } })
  })

  it("renomeia workModel → workplace_type (string)", () => {
    const out = toAttributesPayload({ workModel: "Remoto" })
    expect(out).toEqual({ workplace_type: "Remoto" })
  })

  it("renomeia status → job_status", () => {
    const out = toAttributesPayload({ status: "Ativa" })
    expect(out).toEqual({ job_status: "Ativa" })
  })

  it("preserva campos não mapeados", () => {
    const out = toAttributesPayload({ title: "Dev", description: "x" })
    expect(out).toEqual({ title: "Dev", description: "x" })
  })

  it("ignora object em chave não listada", () => {
    const v = { id: 1, name: "x" }
    const out = toAttributesPayload({ randomObj: v })
    expect(out).toEqual({ randomObj: v })
  })

  it("mix completo", () => {
    const out = toAttributesPayload({
      title: "Dev",
      department: { id: 2, name: "RH" },
      workModel: "Híbrido",
      status: "Rascunho",
      randomBool: true,
    })
    expect(out).toEqual({
      title: "Dev",
      department_attributes: { id: 2, name: "RH" },
      workplace_type: "Híbrido",
      job_status: "Rascunho",
      randomBool: true,
    })
  })
})
```

- [ ] **Step 3: Rodar**

Run: `npx vitest run plataforma-lia/src/services/jobs/__tests__/job-payload.test.ts`
Expected: 7 passed.

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/services/jobs/job-payload.ts plataforma-lia/src/services/jobs/__tests__/job-payload.test.ts
git commit -m "feat(services): helper toAttributesPayload com testes (paridade legacy)"
```

> **Follow-up (Task 27 smoke):** após o smoke do fluxo de save, identificar no código-cliente onde o PUT é montado (provavelmente em `useJobEditTab` via `onSaveSection` chamado pelo pai de `JobEditTab`), importar `toAttributesPayload` e aplicar ao body. Se o smoke mostrar que o backend já aceita o shape atual, deixar este helper disponível para workstreams posteriores.

---

### Task 26: Atualizar `countFilledFields` para reconhecer objetos

**Files:**
- Modify: `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts`

O `countFilledFields` atual considera objetos truthy como preenchidos (padrão `val !== undefined && val !== null && val !== ""`), então já funciona. Mas vamos confirmar com um teste explícito para evitar regressão futura.

- [ ] **Step 1: Criar teste**

Create: `plataforma-lia/src/components/jobs/job-edit-tab/__tests__/constants.test.ts`

```ts
import { describe, it, expect } from "vitest"
import { countFilledFields } from "../job-edit-tab.constants"

describe("countFilledFields", () => {
  it("conta campos preenchidos com string", () => {
    expect(countFilledFields({ title: "Dev" }, ["title", "dept"])).toBe(1)
  })

  it("conta objetos `*_attributes` como preenchidos", () => {
    expect(countFilledFields({ department: { id: 1, name: "Eng" } }, ["department"])).toBe(1)
  })

  it("ignora null e undefined e string vazia", () => {
    expect(countFilledFields({ a: null, b: undefined, c: "" }, ["a", "b", "c"])).toBe(0)
  })

  it("conta arrays não-vazios", () => {
    expect(countFilledFields({ arr: ["x"] }, ["arr"])).toBe(1)
    expect(countFilledFields({ arr: [] }, ["arr"])).toBe(0)
  })
})
```

- [ ] **Step 2: Rodar**

Run: `npx vitest run plataforma-lia/src/components/jobs/job-edit-tab/__tests__/constants.test.ts`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add plataforma-lia/src/components/jobs/job-edit-tab/__tests__/constants.test.ts
git commit -m "test(jobs): countFilledFields cobre objetos _attributes"
```

---

### Task 27: Smoke manual + lint final

- [ ] **Step 1: Dev server**

Run: `cd plataforma-lia && npm run dev`
Abrir `http://localhost:3000/pt/jobs/[ID-de-uma-vaga-existente]?tab=edit` — **Obs:** substituir ID.

- [ ] **Step 2: Checklist manual**

- Abrir a seção "Informações Gerais" em modo edição.
- Clicar em Departamento → combobox abre, digita, lista vem do Rails.
- Selecionar valor → label do botão atualiza.
- Idem para Cidade, Modelo de Trabalho, Tipo de Contrato, Senioridade, Prioridade, Urgência, Status.
- Clicar em "Salvar" → Network mostra PUT com `department_attributes`, `priority_attributes`, `workplace_type: <string>`, etc.
- Vaga recarrega preenchida (não "volta ao default").

- [ ] **Step 3: Lint e type-check limpos**

```bash
npx eslint plataforma-lia/src/components/jobs/job-edit-tab/ plataforma-lia/src/components/ui/remote-combobox.tsx plataforma-lia/src/services/jobs/ plataforma-lia/src/hooks/jobs/use-job-metadata.ts
npx tsc --noEmit -p plataforma-lia/tsconfig.json 2>&1 | grep -E "(job-metadata|remote-combobox|JobInfoGeralSection|useJobEditTab)" || echo OK
```
Expected: silêncio + "OK".

- [ ] **Step 4: Rodar suite de testes da área**

```bash
npx vitest run plataforma-lia/src/services/jobs plataforma-lia/src/components/ui/__tests__/remote-combobox.test.tsx plataforma-lia/src/components/jobs/job-edit-tab/__tests__
```
Expected: tudo passa.

- [ ] **Step 5: Commit final (se houver ajustes pontuais)**

Se precisar de fixes pós-smoke, commitar separadamente com `fix(jobs): ajuste pós-smoke em <ponto>`.

---

## Critérios de aceite

- [ ] Todos os 8 proxies existem, retornam 200 quando Rails tem o recurso.
- [ ] Service cobre os 9 fetchers com shape JSON:API desembrulhado.
- [ ] Hook `useJobMetadata` tem 9 sub-hooks com cache SWR de 60s.
- [ ] `RemoteCombobox` reutilizável com busca debounced e loading state.
- [ ] `JobInfoGeralSection` trocou 7 selects estáticos pelos combos dinâmicos sem mudar layout.
- [ ] Campo `city` adicionado e salva.
- [ ] Save usa `*_attributes` para objetos (paridade legacy).
- [ ] Suite de testes da área passando (~17 testes novos).
- [ ] Smoke manual OK: abrir vaga → editar todos os campos → salvar → recarregar → valores permanecem.

## Dependências para próximos planos

Este workstream entrega a fundação (proxies + service + hook + combobox) que os workstreams 2–7 vão reusar. Em particular:
- Workstream 2 (Step 2 People) reusa `useUserSearch` + `RemoteCombobox`.
- Workstream 6 (Step Description) reusa `RemoteCombobox` para skills/behavioral/languages.
- Workstream 3 (Step Selective Processes) reusa o padrão de service + hook.

---

## Roadmap dos próximos planos (escopo deste spec)

Para referência — não executar aqui.

| # | Plano | Depende de |
|---|---|---|
| 2 | Step 2 (People) + rota `/jobs/new` | Este |
| 3 | Step 3 (Selective Processes) CRUD + drag-drop reorder | Este |
| 4 | Step 4 (Remuneration) polimórfico + bulk_upsert | Este |
| 5 | Step 5 (Screening configs) canais voice/ligacao + is_screening_active persistido | Este |
| 6 | Step 6 (Description) skill/behavioral/language relationships + JD dims + suggest responsibilities | Este + cmdk patterns |
| 7 | Step 7 (Questions/WSI) evaluations CRUD + generate_wsi async | Este |
| 8 | Publish flow com validação pré-publish | Todos acima |
