# Settings Shared Primitives

Componentes reutilizáveis para o módulo de Configurações. Todos os novos hubs DEVEM usar estas primitivas em vez de recriar os padrões inline.

## Primitivas disponíveis

### `<HubHeader>`

Cabeçalho padrão de cada hub. Inclui título, descrição opcional, subsection breadcrumb e slot de ações.

```tsx
import { HubHeader } from "@/components/settings/_shared"

<HubHeader
  title="Integrações"
  description="Configure as integrações com serviços externos."
  subsection="Configurações"   // opcional — rótulo acima do título
>
  <Button size="sm">Adicionar</Button>  // children = slot de ações (opcional)
</HubHeader>
```

### `<HubLoadingState>`

Estado de loading acessível (`aria-live="polite"`, `role="status"`). Disponível em variantes `"full"` (centralizado na área) e `"inline"`.

```tsx
import { HubLoadingState } from "@/components/settings/_shared"

// Hub inteiro carregando
if (isLoading) return <HubLoadingState />
if (isLoading) return <HubLoadingState message="Carregando integrações..." />

// Loader compacto dentro de card
{isLoading && <HubLoadingState variant="inline" />}
```

Também é o fallback canônico para `<Suspense>` em `settings-page-enhanced.tsx`:

```tsx
<Suspense fallback={<HubLoadingState />}>
  <MinhaEmpresaHub activeSubsection={activeSubsection} />
</Suspense>
```

### `<HubErrorState>`

Estado de erro acessível (`role="alert"`). Disponível em variantes `"full"` e `"banner"`. Suporta callback de retry.

```tsx
import { HubErrorState } from "@/components/settings/_shared"

if (error) return <HubErrorState message="Erro ao carregar dados." onRetry={refetch} />
{error && <HubErrorState variant="banner" message={String(error)} onRetry={refetch} />}
```

## Padrão de Suspense por hub

`settings-page-enhanced.tsx` envolve cada hub dinâmico com:

```tsx
<ErrorBoundarySection>
  <Suspense fallback={<HubLoadingState />}>
    <MeuHub activeSubsection={activeSubsection} />
  </Suspense>
</ErrorBoundarySection>
```

`ErrorBoundarySection` captura erros de runtime (JS throw). `Suspense` captura a promise de lazy-load do `dynamic()` — garante skeleton visível em < 200 ms na troca de hub, mesmo em conexão lenta.

## Convenções de fetching (React Query)

Todo fetch em hooks de settings usa `SETTINGS_QUERY_KEYS` de `@/hooks/settings/useSettingsBroadcast`:

```ts
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"
import { useQuery } from "@tanstack/react-query"

const { data, isLoading, error, refetch } = useQuery({
  queryKey: SETTINGS_QUERY_KEYS.companyProfile(),
  queryFn: () => fetch("/api/backend-proxy/company-profile").then(r => r.json()),
  staleTime: 30_000,
})
```

Keys canônicas disponíveis:

| Key helper | Cache key |
|---|---|
| `SETTINGS_QUERY_KEYS.companyProfile()` | `["company-profile"]` |
| `SETTINGS_QUERY_KEYS.cultureProfile(companyId)` | `["culture-profile", companyId]` |
| `SETTINGS_QUERY_KEYS.benefits(companyId)` | `["company-benefits", companyId]` |
| `SETTINGS_QUERY_KEYS.hiringPolicy()` | `["hiring-policy"]` |
| `SETTINGS_QUERY_KEYS.settingsProgress()` | `["settings-progress"]` |

## Broadcast events (`lia:settings-updated`)

Quando uma seção é salva com sucesso, despachar o evento canônico:

```ts
import { dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"

// no onSuccess da mutation (os 4 campos sao obrigatorios):
dispatchSettingsUpdate({
  actionId: "configure_culture", // id da acao (string descritiva)
  section: "culture",            // secao canonica salva
  source: "ui",                  // "ui" impede o proprio listener de reagir
  ts: Date.now(),
})
```

O chat da LIA escuta esse evento para atualizar seu contexto automaticamente.

## Template mínimo de hub novo

```tsx
"use client"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { useQuery } from "@tanstack/react-query"

interface Props {
  companyId: string
  activeSubsection?: string
}

export function MeuNovoHub({ companyId, activeSubsection }: Props) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["meu-recurso", companyId],
    queryFn: () =>
      fetch(`/api/backend-proxy/meu-recurso/${companyId}`).then(r => r.json()),
    staleTime: 30_000,
    enabled: !!companyId,
  })

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  return (
    <div>
      <HubHeader title="Meu Hub" description="Descrição do hub." />
      {/* conteúdo */}
    </div>
  )
}
```

## Checklist ao adicionar um novo hub

1. Criar `src/components/settings/MeuNovoHub.tsx` seguindo o template acima.
2. Adicionar dynamic import em `settings-page-enhanced.tsx`:
   ```ts
   const MeuNovoHub = dynamic(
     () => import("@/components/settings/MeuNovoHub").then(m => ({ default: m.MeuNovoHub })),
     { ssr: false, loading: () => <I18nLoadingFallback tKey="loading" /> }
   )
   ```
3. Adicionar case em `renderSectionContent()` com `<Suspense fallback={<HubLoadingState />}>`.
4. Adicionar entrada em `getDefaultSections()` com `id`, `title`, `description`, `icon`.
5. Adicionar testes smoke em `src/components/settings/__tests__/MeuNovoHub.test.tsx`.
6. Rodar `npx eslint src/components/settings/MeuNovoHub.tsx` — zero erros antes de commitar.
