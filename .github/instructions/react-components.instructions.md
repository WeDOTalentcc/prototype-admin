---
applyTo: "plataforma-lia/src/components/**/*.tsx"
---

# React Components — WeDO Talent

## Organização de pastas

```
src/components/
├── ui/                    ← shadcn primitives + variantes WeDO (button, card, dialog, ...)
├── pages/                 ← componentes de página (JobsListContent.tsx, ...)
├── dashboard-app.tsx      ← shell principal autenticada
├── <feature>/             ← agrupados por domínio: jobs/, candidates/, kanban/, etc.
├── screening-config/      ← componentes compostos de uma feature
└── charts/                ← componentes de visualização (recharts, chart.js)
```

Regra prática:

- **`ui/`** — primitivos reutilizáveis sem regra de negócio. Não importar stores, hooks de domínio ou `next-intl` aqui.
- **`<feature>/`** — pode acessar hooks/stores do domínio. Pode compor `ui/*`.
- **`pages/`** — recebe muitos props; orquestra subcomponentes. Tipicamente client component.

Não crie pastas de profundidade > 2 sob `components/<feature>/`. Se precisar mais, provavelmente é uma feature separada.

## `'use client'`

Componente client quando usa hooks de estado, efeitos, browser APIs ou SWR/Zustand. Componente server é a exceção em `components/` — quase tudo aqui é interativo.

```tsx
// ✅ ui/button.tsx — server-friendly (só composição)
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

// ...
```

```tsx
// ✅ screening-config/ScreeningStatusModal.tsx
'use client'

import { useState } from 'react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
// ...
```

## Anatomia de um componente

Ordem dentro do arquivo:

```tsx
'use client'                  // 1. directive (se client)

import { useState } from 'react'        // 2. externos
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'  // 3. @/
import { useJobFiltersStore } from '@/stores/job-filters-store'

import type { Job } from '@/types/jobs'  // 4. tipos

// 5. constantes / helpers locais
const MAX_TAGS = 5

function formatTag(value: string): string {
  return value.toLowerCase().trim()
}

// 6. interface Props
interface JobCardProps {
  job: Job
  selected?: boolean
  onSelect?: (job: Job) => void
  onRemove?: (id: number) => void
}

// 7. componente
export function JobCard({ job, selected = false, onSelect, onRemove }: JobCardProps) {
  // ...
}
```

- **Export nomeado** preferido (`export function X`). `default export` só em `page.tsx`, `layout.tsx`, `error.tsx`, `loading.tsx`, `not-found.tsx`, que o Next exige.
- **`interface Props`**, nunca `type Props = { ... }` inline. Nome padrão: `<NomeDoComponente>Props`.

## Tipagem de props

```tsx
// ✅
interface JobCardProps {
  job: Job
  selected?: boolean
  onSelect?: (job: Job) => void
  className?: string
}

// ❌
export function JobCard({ job, selected, onSelect, className }: {
  job: Job; selected?: boolean; onSelect?: (j: Job) => void; className?: string
}) {}

// ❌
export function JobCard(props: any) {}
```

Para props que estendem atributos HTML, use intersecção:

```tsx
// ✅ ui/badge.tsx
interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning'
}
```

## Callbacks

Sempre prefixo `on*` (`onClick`, `onSelect`, `onRemove`). Nunca `*Handler`, `*Clicked`.

```tsx
// ✅
interface Props {
  onSelect: (job: Job) => void
  onRemove?: (id: number) => void
}

// ❌
interface Props {
  selectHandler: (job: Job) => void
  onClickRemove: (id: number) => void
}
```

## Variantes com CVA

Componentes primitivos com múltiplas aparências usam `class-variance-authority`. Padrão estabelecido em `ui/button.tsx`:

```tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-lia-bg-tertiary text-lia-text-primary',
        success: 'bg-status-success/15 text-status-success',
        warning: 'bg-status-warning/15 text-status-warning',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>,
  VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />
}
```

## `forwardRef`

Só para primitivos `ui/*` que precisam de ref externa (Radix pede em vários). Não use em componentes de domínio.

```tsx
// ✅ ui/input.tsx
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn('...', className)} {...props} />
  )
)
Input.displayName = 'Input'
```

> ⚠️ Quando abandonarmos React < 19 forwardRef vira opcional (ref é prop). Por ora mantenha o padrão para consistência com shadcn.

## Composição

Prefira composição a "God components" com 20 props booleanos.

```tsx
// ❌ prop explosion
<JobCard
  job={job}
  showActions
  showMetrics
  showCandidateCount
  variant="compact"
  onActionClick={...}
  onMetricsClick={...}
/>

// ✅ composição
<JobCard job={job}>
  <JobCard.Metrics />
  <JobCard.Actions onClick={...} />
</JobCard>
```

Quando não couber composição, extraia em `JobCardCompact`, `JobCardDetailed`.

## Quando dividir

- **> 200 linhas** — considere extrair subcomponentes.
- **> 5 `useState` no mesmo componente** — extraia um hook `use<Feature>State`.
- **Lógica de fetch + render na mesma função** — sempre extraia o fetch para um hook em `src/hooks/<feature>/`.
- **JSX aninhado > 4 níveis** — extraia.

```tsx
// ❌ fetch + render juntos
export function JobsList() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => { fetch('/api/backend-proxy/jobs').then(...) }, [])
  return <div>...</div>
}

// ✅ hook + componente enxuto
export function JobsList() {
  const { jobs, isLoading, error } = useJobs()
  if (isLoading) return <Skeleton />
  if (error) return <ErrorState message={error} />
  if (jobs.length === 0) return <EmptyState />
  return <ul>{jobs.map(j => <JobCard key={j.id} job={j} />)}</ul>
}
```

## Loading / Error / Empty state

Toda lista ou detalhe que carrega dados remotos deve mostrar **três estados** explicitamente:

```tsx
export function CandidatesList() {
  const { candidates, isLoading, error, refresh } = useCandidatesList()

  if (isLoading) return <LoadingFallback text="Carregando candidatos..." />
  if (error) return <ErrorState message={error} onRetry={refresh} />
  if (candidates.length === 0) return <EmptyState title="Sem candidatos" />

  return <CandidatesGrid candidates={candidates} />
}
```

## Nomenclatura de arquivos

- Componentes: **kebab-case** ou **PascalCase** — a codebase é mista. **Novos arquivos use kebab-case** (`job-card.tsx`), exceto quando substituem um legado em PascalCase (mantenha consistência local).
- Um componente público por arquivo. Subcomponentes privados ok no mesmo arquivo.

```tsx
// ✅ job-card.tsx
export function JobCard(...) {}
function JobCardHeader(...) {}  // privado, mesmo arquivo
function JobCardBody(...) {}
```

## Acessibilidade

- Ícones decorativos: `aria-hidden="true"`.
- Botões só com ícone: `aria-label` obrigatório.
- `<label htmlFor>` ou `<Label>` do shadcn em todo input.
- Diálogos: `DialogTitle` obrigatório (Radix exige); se visual não precisar, use `<VisuallyHidden>`.

```tsx
// ✅
<button aria-label="Fechar modal" onClick={onClose}>
  <X className="w-4 h-4" aria-hidden="true" />
</button>
```

## `React.memo`, `useMemo`, `useCallback`

Não use por default. Introduza **quando medido** (React DevTools Profiler ou renders visíveis). Memoização prematura é bug em potencial.

```tsx
// ❌ memoização cargo-cult
const handleClick = useCallback(() => onSelect(job), [onSelect, job])

// ✅ sem memoização — componente já re-renderiza pouco
const handleClick = () => onSelect(job)
```

## Rules

- **Export nomeado** (default apenas em arquivos exigidos pelo Next).
- **`interface <Nome>Props`** explícita; nunca `any` em props.
- **Callbacks `on*`**.
- **Sem lógica de fetch em componente** — extrai para hook.
- **3 estados sempre**: loading, error, empty.
- **Sem prop boolean explosion** — composição ou variantes nomeadas.
- **`forwardRef` só em `ui/*`** quando Radix exigir.
- **`React.memo`/`useMemo`/`useCallback` só quando medido**.
- **Acessibilidade mínima**: `aria-label` em botões-ícone, `aria-hidden` em ícones decorativos.
- **Sem hex hardcoded** em className — tokens do DS.
- **Componentes `> 200 linhas`** viram candidatos a refactor.
