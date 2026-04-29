---
applyTo: "plataforma-lia/src/**/*.{ts,tsx}"
---

# Frontend Overview — WeDO Talent (plataforma-lia)

O frontend alvo destas regras é **`plataforma-lia/`** — Next.js 15 App Router gerado inicialmente pelo Replit. Tudo aqui assume esse projeto.

Conviventes no monorepo: `ats_api/` (Rails, fonte das instruções `rails-*.instructions.md`) e `lia-agent-system/` (FastAPI). O FE hoje fala com FastAPI via proxy; migração gradual para Rails está em curso (ver `src/lib/api/proxy-handler.ts` — flag `backendTarget: "rails"`).

## Stack (congelada)

| Camada | Ferramenta | Notas |
|---|---|---|
| Framework | Next.js 15 + React 19 | App Router, Server Components por padrão |
| Linguagem | TypeScript 5.8 | `strict: true`, porém `noImplicitAny: false` (legado) |
| Styling | Tailwind v3.4 + shadcn/ui + Radix | `cn()` de `@/lib/utils` |
| Ícones | `lucide-react` | `w-4 h-4` inline, `w-5 h-5` standalone |
| Forms | React Hook Form + Zod + `@hookform/resolvers` | — |
| Server state | **SWR 2** | 60+ hooks existentes, não trocar |
| Global state | Zustand 5 | `devtools` sempre, `persist` quando UI-only |
| HTTP | `fetch` via rotas `/api/backend-proxy/*` | **não** usar axios |
| Toast | `sonner` | `toast.success/error` |
| i18n | `next-intl` | rotas sob `[locale]` |
| Observabilidade | `@sentry/nextjs` | captura em `app/error.tsx` |

Novas dependências exigem justificativa escrita e aprovação. Não introduza axios, tanstack-query, redux, mobx ou equivalentes.

## Layout de pastas

```
plataforma-lia/src/
├── app/                 ← App Router
│   ├── [locale]/        ← rotas traduzidas (pt, en, es)
│   ├── api/backend-proxy/*/route.ts  ← proxy p/ backend
│   ├── layout.tsx       ← root layout (fonts + Sentry)
│   ├── error.tsx        ← error boundary global
│   └── not-found.tsx    ← 404
├── components/
│   ├── ui/              ← shadcn + variantes WeDO (Button, Card, ...)
│   ├── pages/           ← componentes de página (JobsListContent, etc.)
│   └── <feature>/       ← agrupado por domínio
├── hooks/
│   └── <feature>/       ← ex. jobs/, candidates/, agents/
├── stores/              ← Zustand stores (um por domínio)
├── lib/
│   ├── api/             ← proxy-fetch, jsonapi, extract-error-message, schemas
│   ├── auth/            ← clients SSO, microsoft-login
│   ├── schemas/         ← Zod schemas compartilhados
│   └── utils.ts         ← `cn()`
├── services/            ← clients tipados (auth-service, lia-api, ...)
├── stores/              ← Zustand
├── contexts/            ← 3 contexts apenas (auth, lia-float, teams-sso)
└── types/               ← tipos compartilhados e `api.generated.ts`
```

## Regras transversais

### Português

Strings voltadas ao usuário ficam em `src/i18n/messages/*.json` via `next-intl`. Nunca hardcodar PT-BR em componentes — use `useTranslations('namespace')`.

```tsx
// ✅
const t = useTranslations('jobs')
return <h1>{t('title')}</h1>

// ❌
return <h1>Vagas</h1>
```

Comentários em código: PT-BR ou EN, tanto faz — mas **não comente o óbvio** (ver `CLAUDE.md` global). Comente o *porquê* quando não-trivial.

### Imports

- Alias `@/*` → `./src/*` (configurado em `tsconfig.json`). **Nunca** use `../../../` além de 2 níveis.
- Ordem: externos → `@/*` → relativos → tipos.

```ts
// ✅
import { useState } from 'react'
import useSWR from 'swr'

import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'

import { localHelper } from './helpers'

import type { Job } from '@/types/jobs'
```

### Tipagem

- Código novo: **strict**. Sem `any`. Props sempre `interface Props`. Retornos de hooks/serviços tipados.
- Código legado: tolerado até ser tocado. Ao editar, corrija a tipagem ou adicione `// TODO: ts-strict` explicando o pendente.
- `ignoreBuildErrors: true` em `next.config.js` é **dívida técnica** — não usar como desculpa para ignorar erros de TS localmente.

Detalhes em `typescript-conventions.instructions.md`.

### Portabilidade futura (Vue)

O projeto prevê migração para Vue/Nuxt no longo prazo. Consequências práticas:

- Lógica em hooks (`use-*`), componente só template+binding.
- Callbacks `on*` nas props (`onSelect`, não `selectHandler`).
- Evite React-only: `cloneElement`, `Children.map`, HOCs, `forwardRef` sem necessidade (exceção: primitivos `ui/*` com Radix).
- Stores Zustand com `interface State` + `interface Actions` — mapeiam limpo para Pinia.

Ver `plataforma-lia/CLAUDE.md` (Design System v4.2.1) para padrões de UI.

### Acessibilidade mínima

- `<label>` ou `aria-label` em todo input/botão sem texto visível.
- Ícones decorativos: `aria-hidden="true"`.
- `focus-visible:ring-2` preservado no `Button` — não sobrescrever.

### Segurança

- JWT vive em **cookie httpOnly** (`lia_access_token`). Nunca em `localStorage` para código novo.
  > ⚠️ Há hooks legados lendo `localStorage.getItem("auth_token")` (ex. `use-custom-agents.ts`) — migrar gradualmente.
- Toda chamada a backend passa por `/api/backend-proxy/*`. Rotas do App Router usam `createProxyHandlers` (`src/lib/api/proxy-handler.ts`).
- Nunca envie `BACKEND_URL` ou tokens diretos para o browser.
- Sanitize HTML vindo de backend com `dompurify` (helper em `src/lib/sanitize.ts`).

### Scripts

```bash
cd plataforma-lia
npm run dev                    # localhost:3000, turbopack
npm run lint                   # tsc --noEmit && next lint
npm run test                   # vitest (unit + hooks + components)
npm run test:e2e               # playwright
npm run build                  # next build
```

## Arquivos-referência (leia antes de criar similares)

| Preciso criar… | Olhe primeiro |
|---|---|
| Hook de fetch (SWR) | `src/hooks/ai/use-ai-credits.ts`, `src/hooks/company/use-current-company.ts` |
| Rota proxy | `src/app/api/backend-proxy/*/route.ts` via `createProxyHandlers` |
| Store Zustand | `src/stores/job-filters-store.ts`, `src/stores/auth-store.ts` |
| Componente `ui/*` | `src/components/ui/button.tsx` (padrão cva + forwardRef) |
| Página App Router | `src/app/[locale]/jobs/page.tsx` (delegação a client component) |
| Form | `forms-and-validation.instructions.md` (RHF + Zod) |

## Rules

- **Um hook = um concern**. Se o nome tem "And", quebre.
- **Sem axios**. Fetch + proxy Next.js é o padrão.
- **Sem localStorage para tokens novos** — cookies httpOnly.
- **Sem hex hardcoded** em JSX (`#60BED1`) — use tokens Tailwind (`bg-wedo-cyan`, `text-lia-text-primary`).
- **Sem `useContext` para estado mutável** — use Zustand. Context só para dependency injection estática (auth provider, tema).
- **Sem dependência nova sem aprovação**.
- **Respeitar `plataforma-lia/CLAUDE.md`** para design tokens, tipografia, sombras, z-index e animações.
- **Todo arquivo tocado fica melhor do que estava** — atualize tipagem, remova `any`, remova comentários obsoletos.
