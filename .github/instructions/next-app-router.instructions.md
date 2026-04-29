---
applyTo: "plataforma-lia/src/app/**/*.{ts,tsx}"
---

# Next.js App Router — WeDO Talent

Projeto em Next.js 15 com App Router. **Server Components por padrão**; `'use client'` apenas quando estritamente necessário.

## Estrutura de rotas

```
src/app/
├── layout.tsx              ← root layout: fonts, Sentry, <html>/<body>
├── error.tsx               ← error boundary global (client)
├── not-found.tsx           ← 404 global
├── loading.tsx             ← loading global (opcional)
├── globals.css             ← Tailwind + variáveis do DS
├── [locale]/               ← i18n via next-intl
│   ├── layout.tsx          ← provider de traduções, shell autenticada
│   ├── page.tsx            ← home
│   ├── jobs/
│   │   ├── layout.tsx      ← metadata da seção
│   │   ├── loading.tsx     ← skeleton da lista
│   │   ├── page.tsx        ← server component delegando a client
│   │   └── [id]/page.tsx   ← detalhe
│   └── login/
└── api/
    ├── auth/               ← WorkOS SSO + sessão Next
    └── backend-proxy/      ← proxy p/ FastAPI/Rails (ver data-fetching)
```

## Server Components por padrão

Toda rota (`page.tsx`, `layout.tsx`) é **Server Component** — sem `'use client'`. Use `'use client'` só quando precisar de:

- `useState`, `useEffect`, `useRef`, `useMemo`, `useCallback`
- Handlers de evento (`onClick`, `onChange`, formulários controlados)
- Browser APIs (`window`, `document`, `localStorage`, `IntersectionObserver`)
- Libs que dependem de cliente (`swr`, `zustand`, `framer`, Radix controlado, `sonner`)
- Context consumer (`useAuthStore`, `useTranslations` em alguns casos)

```tsx
// ✅ src/app/[locale]/jobs/page.tsx — server component
import type { Metadata } from 'next'
import { DashboardApp } from '@/components/dashboard-app'

export const metadata: Metadata = {
  title: 'Vagas | LIA — WeDo Talent',
  description: 'Gerencie vagas com triagem inteligente por IA.',
}

export default function JobsListPage() {
  return <DashboardApp initialPage="Vagas" />
}
```

```tsx
// ✅ DashboardApp é client component (interatividade)
'use client'

export function DashboardApp({ initialPage }: { initialPage: string }) {
  const [page, setPage] = useState(initialPage)
  // ...
}
```

```tsx
// ❌ Não marque a página como client só pra simplificar
'use client'
export default function JobsListPage() { ... }
```

## Layouts

Layout é **server** por padrão. Mantenha enxuto — só metadata, providers e shell.

```tsx
// ✅ src/app/[locale]/jobs/layout.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Vagas',
  description: 'Gerencie e acompanhe vagas de emprego com IA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
```

`{ children }` **sempre tipado**: `{ children: React.ReactNode }`.

## Metadata

Sempre exporte `metadata` (ou `generateMetadata` para conteúdo dinâmico) em `page.tsx` e `layout.tsx`. Title e description são obrigatórios em páginas indexáveis.

```tsx
// ✅ Estático
export const metadata: Metadata = {
  title: 'Candidatos',
  description: 'Banco de talentos da sua empresa',
}

// ✅ Dinâmico
export async function generateMetadata(
  { params }: { params: Promise<{ id: string }> }
): Promise<Metadata> {
  const { id } = await params
  const job = await getJob(id)
  return { title: `${job.title} | Vagas` }
}
```

## Loading e Error

Cada seção grande deve ter `loading.tsx`. Use o `LoadingFallback` padrão:

```tsx
// ✅ src/app/[locale]/jobs/loading.tsx
import { LoadingFallback } from '@/components/ui/loading'

export default function JobsLoading() {
  return <LoadingFallback height="h-screen" text="Carregando vagas..." />
}
```

`error.tsx` é **client** (precisa de `reset`). Capture no Sentry e ofereça retry:

```tsx
// ✅ src/app/error.tsx
'use client'
import { useEffect } from 'react'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    import('@sentry/nextjs').then(s => s.captureException(error)).catch(() => {})
  }, [error])
  return <div>...<button onClick={reset}>Tentar novamente</button></div>
}
```

## Route Groups

Use `(grupo)` para agrupar sem afetar URL:

```
app/[locale]/
├── (dashboard)/            ← requer auth, shell com sidebar
│   ├── layout.tsx
│   ├── vagas/page.tsx
│   └── candidatos/page.tsx
└── (public)/               ← sem shell
    ├── login/page.tsx
    └── register/page.tsx
```

## Dynamic params

No App Router 15, `params` e `searchParams` são **Promise**. Sempre `await`.

```tsx
// ✅
export default async function JobDetail({
  params,
}: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <JobDetailClient id={id} />
}

// ❌ Next 14 style — não compila no 15
export default function JobDetail({ params }: { params: { id: string } }) {
  return <JobDetailClient id={params.id} />
}
```

## API Routes (`app/api/**/route.ts`)

Todas as rotas `/api/backend-proxy/*` devem usar `createProxyHandlers` (ver `data-fetching.instructions.md`). Não duplique `fetch` + `getAuthHeaders` em cada rota.

```ts
// ✅ src/app/api/backend-proxy/jobs/route.ts
import { createProxyHandlers } from '@/lib/api/proxy-handler'

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: '/api/v1/jobs',
  methods: ['GET', 'POST'],
})
```

```ts
// ✅ Com Rails target + validação de body
import { createProxyHandlers } from '@/lib/api/proxy-handler'
import { jobCreateSchema } from '@/lib/schemas/job.schema'

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: '/v1/users/jobs',
  backendTarget: 'rails',
  methods: ['GET', 'POST'],
  bodySchema: jobCreateSchema,
})
```

```ts
// ❌ fetch cru na rota
export async function GET(req: NextRequest) {
  const res = await fetch(process.env.BACKEND_URL + '/api/v1/jobs')
  return NextResponse.json(await res.json())
}
```

## Server Actions

Proibidas por padrão — conflitam com o padrão de proxy + JWT em cookies httpOnly e com a separação FE/BE. Use `createProxyHandlers` ou chamada client-side via SWR/mutation.

> ⚠️ Exceção tolerada: ações puramente internas ao Next (gerar um token CSRF, trocar um cookie). Nesses casos, documente com comentário e nunca acesse o backend direto.

## Internacionalização (next-intl)

- Todas as rotas de usuário vivem sob `app/[locale]/*`.
- Use `useTranslations('namespace')` (client) ou `getTranslations()` (server).
- Mensagens em `src/i18n/messages/{pt,en,es}.json`, mesmo shape em todas as línguas.

```tsx
// ✅ client
'use client'
import { useTranslations } from 'next-intl'

export function JobsHeader() {
  const t = useTranslations('jobs')
  return <h1>{t('title')}</h1>
}
```

```tsx
// ✅ server
import { getTranslations } from 'next-intl/server'

export default async function Page() {
  const t = await getTranslations('jobs')
  return <h1>{t('title')}</h1>
}
```

## Fonts

Declare em `app/layout.tsx` via `next/font/google`. **Nunca** `@import` de Google Fonts no CSS.

```tsx
// ✅ já em src/app/layout.tsx
import { Inter, Open_Sans } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' })
```

## Rules

- **Server Component por padrão** — `'use client'` exige justificativa (hook/event/browser API).
- **`{ children }: { children: React.ReactNode }`** sempre tipado.
- **`metadata` obrigatória** em `page.tsx` e `layout.tsx` indexáveis.
- **`params` e `searchParams` são Promise** — `await` sempre.
- **Proxy via `createProxyHandlers`** — não escreva `fetch` cru em `route.ts`.
- **Sem Server Actions** sem justificativa.
- **Rotas de usuário sob `[locale]`** — copy via `next-intl`.
- **`loading.tsx` em cada seção**; `error.tsx` global reporta ao Sentry.
- **Fonts via `next/font`** — sem `@import` de Google Fonts.
- **Nunca exponha `BACKEND_URL`**, secrets ou tokens em Server/Client Components renderizados.
