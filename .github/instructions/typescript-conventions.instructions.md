---
applyTo: "plataforma-lia/src/**/*.{ts,tsx}"
---

# TypeScript Conventions — WeDO Talent

## Estado atual do projeto

- `tsconfig.json` tem `"strict": true` **mas** `"noImplicitAny": false` (legado).
- `next.config.js` tem `typescript.ignoreBuildErrors: true` — **dívida**, não use como licença.
- `lint-staged` roda `tsc --noEmit --skipLibCheck` nos arquivos tocados. Se você tocou o arquivo, ele **tem** que passar localmente.

## Regra pragmática

```
Código NOVO      → strict pleno. Sem `any`. Props tipadas. Retornos tipados.
Código LEGADO    → ok manter `any` implícito ATÉ ser tocado.
Código TOCADO    → upgrade obrigatório para strict.
```

Se por algum motivo não dá pra corrigir tudo ao tocar (escopo do PR explodiria), marque com:

```ts
// TODO: ts-strict — refatorar tipo dos filtros quando reescrever filtersState
const filters = getFilters() as any
```

E abra issue. Não deixe `any` sem comentário ou sem issue.

## `any` vs `unknown`

**`any` é proibido** em código novo. Use `unknown` quando o valor é genuinamente desconhecido e faça narrowing antes de usar.

```ts
// ✅ unknown + narrowing
function parseResponse(raw: unknown): Job | null {
  if (!raw || typeof raw !== 'object') return null
  const obj = raw as Record<string, unknown>
  if (typeof obj.id !== 'string' || typeof obj.title !== 'string') return null
  return { id: obj.id, title: obj.title, status: String(obj.status ?? 'draft') as Job['status'] }
}

// ❌ any
function parseResponse(raw: any): Job { return raw }

// ❌ cast direto sem checar
return raw as Job
```

Quando a resposta é de API e você quer delegar a validação para Zod, use o schema como fonte única (ver `forms-and-validation`):

```ts
// ✅
const job = jobSchema.parse(raw)  // throws se inválido
```

## `interface` vs `type`

Escolha simples:

- **`interface`** para shapes de objeto (props, modelos, stores).
- **`type`** para unions, tuples, mapped types, intersecções, aliases utilitários.

```ts
// ✅
interface Job {
  id: string
  title: string
  status: JobStatus
}

type JobStatus = 'open' | 'closed' | 'draft' | 'paused'

type JobWithMetrics = Job & { metrics: JobMetrics }
```

```ts
// ❌ type para shape — atrapalha extends
type Props = { id: string; title: string }  // use interface
```

## Props de componentes

**Sempre** `interface <Nome>Props` exportada ou local. Ver `react-components.instructions.md`.

```tsx
// ✅
interface JobCardProps {
  job: Job
  onSelect?: (job: Job) => void
  className?: string
}
export function JobCard({ job, onSelect, className }: JobCardProps) { ... }

// ❌
export function JobCard(props: { job: Job; onSelect?: any }) { ... }
```

Extensão de atributos HTML:

```tsx
// ✅
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  errorMessage?: string
}
```

## Retornos explícitos

- Hooks públicos (`src/hooks/**`) **devem** ter interface de retorno explícita.
- Componentes: retorno inferido é ok (TSX sabe `JSX.Element | null`).
- Utilitários: explicitar retorno quando não-trivial.

```ts
// ✅ hook com contrato claro
interface UseJobsReturn {
  jobs: Job[]
  total: number
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useJobs(filters: JobFilters = {}): UseJobsReturn { ... }

// ❌ retorno inferido opaco
export function useJobs(filters = {}) {
  const { data, error, isLoading, mutate } = useSWR(...)
  return { data, error, isLoading, mutate }  // qual shape? o consumidor que adivinhe
}
```

## Respostas de API — discriminated unions

Respostas com "sucesso vs falha" → union discriminada. Facilita narrowing e documenta o contrato.

```ts
// ✅ do auth-service.ts real do projeto
interface MfaRequiredResponse {
  mfa_required: true
  mfa_token: string
  message?: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

type LoginResponse = TokenResponse | MfaRequiredResponse

function isMfaRequired(r: LoginResponse): r is MfaRequiredResponse {
  return (r as MfaRequiredResponse).mfa_required === true
}
```

```ts
// ❌ "tipo de tudo" com tudo opcional
interface LoginResponse {
  access_token?: string
  refresh_token?: string
  mfa_required?: boolean
  mfa_token?: string
}
```

## Inferência via Zod

Quando o schema existe, **sempre** infira o tipo — nunca duplique:

```ts
// ✅ src/lib/schemas/job.schema.ts
export const jobCreateSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
})
export type JobCreateInput = z.infer<typeof jobCreateSchema>
```

## Enums e literal unions

Prefira **literal unions** a `enum`. Mais leve, compatível com serialização, sem runtime code.

```ts
// ✅
type JobStatus = 'open' | 'closed' | 'draft' | 'paused'

const JOB_STATUS = ['open', 'closed', 'draft', 'paused'] as const
type JobStatus2 = (typeof JOB_STATUS)[number]

// ❌ enum TS — gera código em runtime, conflita com `tsc --isolatedModules`
enum JobStatus { Open = 'open', Closed = 'closed' }
```

Enums numéricos só quando fazendo interop com backend que usa int (ex. Rails `enum status: { pending: 0, sent: 1 }`).

## Nullability

- Prefira `undefined` (omissão) a `null` em código TS puro.
- Backend devolve `null` — normalize na fronteira (hook/fetcher).

```ts
// ✅ na fronteira
return {
  company: data ?? null,        // expose null só quando contratual
  isLoading,
}
```

Evite opcionalidade excessiva: se um campo *sempre* existe no sucesso, o tipo não deve dizer `?`.

```ts
// ❌
interface Job {
  id?: string
  title?: string
  status?: string
}

// ✅
interface Job {
  id: string
  title: string
  status: JobStatus
}
```

## Narrowing seguro

Use type guards em vez de `as` quando o tipo é runtime.

```ts
// ✅ type guard
function isJob(value: unknown): value is Job {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return typeof v.id === 'string' && typeof v.title === 'string'
}

// ❌ assert cego
const job = data as Job
```

Para arrays, prefira `Array.isArray` antes de acessar.

## Utility types

Use os da std quando couber: `Partial`, `Required`, `Pick`, `Omit`, `Record`, `ReturnType`, `Awaited`.

```ts
// ✅
type JobUpdate = Partial<JobCreateInput>
type JobSummary = Pick<Job, 'id' | 'title' | 'status'>
type HookReturn = ReturnType<typeof useJobs>
```

Tipos utilitários customizados vivem em `src/types/utility.ts`. Não duplique.

## Nome de tipos e arquivos

- **PascalCase** para tipos e interfaces: `Job`, `JobFilters`, `UseJobsReturn`.
- **Sufixo `Props`** para props de componente.
- **Sufixo `Input`** para dados de entrada de mutation (`JobCreateInput`).
- **Sufixo `Return`** para retorno de hook.
- **Sem prefixo `I`**: `IJob` é C#, não TS.

Arquivos de tipos:

- Por domínio: `src/types/job.ts`, `src/types/candidate.ts`.
- Gerados: `src/types/api.generated.ts` (via `npm run generate:api-types`) — não edite à mão.

## Imports de tipo

Use `import type` quando o import é puramente de tipo. Ajuda o bundler a remover:

```ts
// ✅
import type { Job } from '@/types/jobs'
import { useJobs } from '@/hooks/jobs/use-jobs'

// ✅ inline
import { useJobs, type UseJobsReturn } from '@/hooks/jobs/use-jobs'
```

## Tipos de eventos

Use os eventos do React, não do DOM direto:

```tsx
// ✅
const onClick = (e: React.MouseEvent<HTMLButtonElement>) => { ... }
const onChange = (e: React.ChangeEvent<HTMLInputElement>) => { ... }
const onSubmit = (e: React.FormEvent<HTMLFormElement>) => { ... }

// ❌ DOM puro
const onClick = (e: MouseEvent) => { ... }
```

## `// @ts-expect-error` vs `// @ts-ignore`

- **`@ts-expect-error`** sempre que conscientemente suprimir — com **motivo** no comentário. Ele avisa se o erro sumir (limpeza fica fácil).
- **`@ts-ignore`** proibido.

```ts
// ✅
// @ts-expect-error — lib `jira.js` não exporta tipo public em build esm
import { Version3Client } from 'jira.js/out/version3'

// ❌
// @ts-ignore
import { foo } from 'bar'
```

## `as const`

Tupla/array literal que não deve ser mutado:

```ts
// ✅
const STATUS_ORDER = ['draft', 'open', 'paused', 'closed'] as const
type JobStatus = (typeof STATUS_ORDER)[number]

const config = { retries: 3, timeout: 5000 } as const
```

## Rules

- **Código novo: strict pleno**. Código legado tocado: upgrade obrigatório.
- **Sem `any`** em código novo; use `unknown` + narrow ou schema Zod.
- **`interface` para shapes**, `type` para unions/intersecções.
- **Props sempre `interface <Nome>Props`**.
- **Hooks públicos têm interface de retorno** explícita.
- **Respostas com sucesso/falha** → discriminated union.
- **Tipos via `z.infer`** quando há schema.
- **Literal unions > enum**.
- **`import type`** em imports de tipo puro.
- **`// @ts-expect-error` com motivo**; `@ts-ignore` proibido.
- **Sem prefixo `I` em interfaces**.
- **Nullability: prefira `undefined`**; `null` só na fronteira de API.
- **`// TODO: ts-strict`** em `any` temporário, com issue aberta.
