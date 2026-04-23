# Docker dev — perf + observabilidade (plataforma-lia)

> 2026-04-20 · escopo: `plataforma-lia/` rodando em container.

## Problema

Rodando `plataforma-lia` em Docker, o dev está lento em todas as frentes:

1. **Build/cold start** demorado.
2. **Transições entre páginas** travam.
3. **Tela preta com modal de loading** fica visível por muitos segundos antes de renderizar.
4. **Sem observabilidade** — impossível identificar o gargalo real.

## Causas suspeitas (confirmadas por leitura de config)

| Sintoma | Causa | Evidência |
|---|---|---|
| CPU alta + HMR lento | `CHOKIDAR_USEPOLLING=true` + `WATCHPACK_POLLING=true` no override | `docker-compose.override.yml` — polling só é necessário em Docker Desktop Mac/Win; **ambiente atual é Linux nativo** |
| Cold compile lento | `next dev` com Webpack (sem Turbopack) em projeto grande | `package.json`: script `dev` usa webpack padrão |
| `.next` recria a cada `docker-compose up` | Volume anônimo `/app/.next` no override | override.yml linha 16 |
| Overhead por request em dev | CSP gigante + 6+ headers adicionados em **toda** request, inclusive assets | `next.config.js` `async headers()` — roda em dev também |
| Black screen no login | `middleware.ts` faz `jwtVerify` + `verifyAndDecodeSession` + `intlMiddleware` em cadeia; sem timing | middleware.ts 162+ |
| Sem dados de navegação | Nenhum log client-side de `performance.getEntriesByType()` | — |

## Design

### Princípios

- **Observabilidade opt-in via env var** (`DEBUG_PERF=1`) — ligada por default em dev Docker, desligada em produção.
- **Logs estruturados, prefixo `[perf]`** — fácil de `grep`.
- **Zero runtime cost em produção** — todo o código de perf é condicional.
- **Fixes baseados em causa conhecida** — polling em Linux, CSP em dev, etc.

### Componentes

**1. `docker-compose.override.yml` (modificado)**
- Remover `CHOKIDAR_USEPOLLING` e `WATCHPACK_POLLING`.
- Trocar volume anônimo `/app/.next` por volume nomeado `next_cache` (persiste entre `down/up`).
- Adicionar `DEBUG_PERF=1`, `NEXT_LOG_FETCHES=1`, `BACKEND_URL=http://api:8000`.
- Expor portas explicitamente (5000:3000).
- Command roda `npm run dev:turbo` (novo script).

**2. `package.json` (modificado)**
- Adicionar `"dev:turbo": "NODE_OPTIONS='--max-old-space-size=4096' next dev --turbopack -H 0.0.0.0 -p 3000"`.
- Manter `dev` antigo (fallback webpack).

**3. `Dockerfile.dev` (modificado)**
- `CMD` muda para `npm run dev:turbo`.
- Adicionar `ENV DEBUG_PERF=1` (pode ser overridden pelo compose).

**4. `next.config.js` (modificado)**
- `async headers()` só retorna CSP/Permissions-Policy/HSTS em produção. Em dev, retorna só Cache-Control para estáticos.
- Mantém `logging.fetches` + `incomingRequests`.

**5. `src/middleware.ts` (modificado)**
- No início: `const start = performance.now()`.
- No final (antes de cada return): calcular duração, logar `[perf] {method} {path} {status} {durationMs}ms` se `process.env.DEBUG_PERF === '1'`.
- Helper `logRequestTiming(request, response, start)` reutilizável.

**6. `src/hooks/useDevPerf.ts` (novo)**
- Hook dev-only. Ligado quando `process.env.NODE_ENV === 'development'` **e** `process.env.NEXT_PUBLIC_DEBUG_PERF === '1'`.
- Usa `PerformanceObserver` para LCP, FCP, navigation timing.
- Loga no console `[perf][client] route={pathname} lcp={ms} fcp={ms} ttfb={ms}`.

**7. Wire-up client-side**
- Importar `useDevPerf` em `src/app/[locale]/layout.tsx` (Client Component) — só ativo em dev.

### Data flow de log

```
request → middleware.ts (timing) → console
        → Next handler → console (logging.fetches)
        → page render → useDevPerf (client) → browser console
```

### Não-goals

- Não adicionar Sentry dev (já está no projeto, custoso).
- Não adicionar tela de debug UI.
- Não trocar Webpack pra Turbopack em produção (só dev).
- Não tentar resolver o "black screen modal" sem medir primeiro — os logs vão mostrar qual é.

### Como testar

1. `docker-compose up frontend`
2. Abrir `http://localhost:5000`
3. Ver no terminal do container:
   - `[perf] GET /pt-BR 200 123ms` em cada request
   - `next:*` logs de compilação
4. Abrir DevTools console no browser — ver `[perf][client]` com LCP/FCP.
5. Navegar entre páginas — timing deve ficar mais rápido após 1ª compilação (cache `.next` persistido).

### Rollback

Cada mudança é isolada e reversível via `git revert`. Remover `DEBUG_PERF=1` desliga todos os logs sem redeploy de código.
