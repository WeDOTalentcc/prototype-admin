# plataforma-lia — Performance Overhaul

> Data: 2026-04-20
> Autor: Victhor + Claude
> Escopo: `plataforma-lia/` (Next.js 15 + React 19 App Router)
> Fora de escopo: segurança (CSP, auth hardening, proxy consolidation por motivos de segurança) — fica para outro ciclo.

## Problema

Dev mode percebido como lento ("tudo uma bosta"). Comparação baseline na cabeça do usuário: Nuxt + Vite, que tem HMR < 300ms e cold start < 3s. Hoje `plataforma-lia/` roda com `NODE_OPTIONS='--max-old-space-size=4096'` (sintoma de pressão de memória), tem 156 rotas em `src/app/api/backend-proxy/` compiladas sob demanda, e importa libs pesadas (`@tiptap`, `html2canvas`, `jspdf`, `chart.js` + `recharts`, `@twilio/voice-sdk`, `@microsoft/teams-js`, `jira.js`) estaticamente.

Sem medir, não dá para saber quanto cada fator contribui. Mexer sem baseline = otimização às cegas.

## Objetivo

Entregar melhorias **medíveis** de performance dev e produção, em fases incrementais, sem alterar UI/comportamento visível.

**Critérios de sucesso**:
- Cold start `npm run dev` < 10s (target stretch: < 5s)
- HMR em arquivo leve (`.tsx` de componente folha) < 1s
- Primeira compilação de rota "hot" < 3s após o primeiro hit
- `next build` conclui sem `ignoreBuildErrors` e `ignoreDuringBuilds` ligados
- Bundle do cliente na rota inicial < 500KB gzip (medido via `npm run analyze`)

## Princípios

1. **Medir antes, medir depois.** Cada PR reporta antes/após para as métricas acima. Sem melhora mensurável = rollback.
2. **Uma mudança por PR.** Nada de big-bang. Isolamento para permitir bisect se degradar algo.
3. **Não mexer em UI/comportamento.** Esse ciclo é exclusivamente perf.
4. **Preferir primitivas do Next sobre ginástica custom** (`next/dynamic`, `loading.tsx`, `optimizePackageImports`, RSC onde fizer sentido).
5. **Reversibilidade.** Cada fase deixa um ponto de retorno claro no git.

## Arquitetura em fases

### Fase 0 — Baseline (sem mudança funcional)

**Entregável**: `plataforma-lia/PERF_BASELINE.md` com números reprodutíveis.

Conteúdo obrigatório do arquivo:
- Data, commit hash, Node version, machine specs
- **Cold start**: 3 rodadas de `time npm run dev` após `rm -rf .next` — min/med/max
- **HMR**: 5 edições triviais em `src/components/ui/button.tsx` (ou equivalente leve) cronometradas via DevTools Network → "Turbopack update" ou log do console
- **First route compile**: tempo até "compiled /<rota>" no log, para 5 rotas representativas (login, dashboard, jobs, candidates, configurações)
- **`next build`**: tempo total + output de rotas (First Load JS por rota)
- **Bundle analyzer**: top 20 módulos por tamanho, total client JS, total server JS
- **Contagem**: arquivos em `src/`, rotas em `src/app/`, rotas em `src/app/api/backend-proxy/`

Script auxiliar: `plataforma-lia/scripts/perf-baseline.sh` para automatizar as medições reprodutíveis.

Nenhum código de produção é alterado nessa fase.

### Fase 1 — Quick wins (onde deve vir ~70% do ganho)

Ordem de ataque (cada item = 1 PR independente):

1. **Limpar lixo na raiz** — remover `a.out`, `tsc_output.txt`, `full_tsc_output.txt`, `nohup.out`. Adicionar padrões ao `.gitignore`. Esforço mínimo, higiene.

2. **Dynamic imports de libs pesadas** — auditar uso de `@tiptap/*`, `html2canvas`, `jspdf`, `chart.js`, `recharts`, `@twilio/voice-sdk`, `@microsoft/teams-js`, `jira.js`, `canvg`, `marked`. Cada ocorrência que não seja crítica para o first paint da rota → `next/dynamic` com `{ ssr: false, loading: () => <Skeleton /> }`. Um PR por lib (ou por conjunto coeso).

3. **Consolidar `backend-proxy/`** — substituir as 156 rotas individuais por um catch-all `src/app/api/backend-proxy/[...path]/route.ts` que encaminha com a mesma lógica (auth header injection, tenant, erros). Manter rotas específicas só onde há lógica diferente do passthrough. Esperado: redução drástica de tempo de primeira visita a qualquer rota do app (cada proxy vira um chunk compilado sob demanda hoje).

4. **Auditar barrel files** — `grep` por `export \* from` e `index.ts` em `src/components/`, `src/lib/`, `src/hooks/`. Substituir re-exports de tudo por imports diretos nos consumidores (ou usar `modularizeImports` no `next.config.js`). Barrel files quebram tree-shaking.

5. **Expandir `optimizePackageImports` e adicionar `modularizeImports`** — incluir `date-fns`, `lodash` (se existir), `sonner`, `cmdk`, `react-hook-form` (se suportar), e outras libs que aparecem no top do bundle analyzer. Para libs sem suporte nativo, usar `modularizeImports` com regex.

6. **Ligar build gates** — remover `eslint.ignoreDuringBuilds: true` e `typescript.ignoreBuildErrors: true` do `next.config.js`. Fixar os erros que aparecerem (esperado: alguns centenas; orçamento: manter como Fase 1 só se forem < ~50, senão quebra em sub-spec próprio).

Critério de "fim da Fase 1": nova medição contra baseline. Se cold start caiu < 50% ou HMR não melhorou visivelmente, investigar antes de seguir para Fase 2.

### Fase 2 — Produção (Core Web Vitals + RSC)

Só começa depois de Fase 1 ter entregue os números. Escopo provisório (será refinado em novo spec):

- Páginas 100%-leitura migradas para Server Components (identificar candidatas via `"use client"` na árvore de rotas)
- `loading.tsx` por rota onde houver fetch no servidor — habilita streaming
- Auditoria de `next/image` vs `<img>` — padronizar no primeiro
- Fonte: confirmar que `next/font` está sendo usado em todos os lugares (CLAUDE.md já proíbe `@import` Google Fonts — validar)
- Prefetch review: `<Link prefetch={false}>` onde não faz sentido, e vice-versa

Essa fase ganha em produção mas pouco no dev-day-to-day.

## Estrutura de arquivos

Nenhum arquivo novo de produção. Arquivos auxiliares:

```
plataforma-lia/
├── PERF_BASELINE.md         ← Fase 0
├── PERF_PROGRESS.md         ← atualizado a cada PR da Fase 1
└── scripts/
    └── perf-baseline.sh     ← medições reprodutíveis
```

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Dynamic import quebra SSR em rota que dependia | `{ ssr: false }` explícito + teste manual da rota |
| Catch-all de proxy rouba rotas específicas existentes | Manter rotas específicas que tenham lógica própria; ordem de matching do Next resolve |
| Ligar build gates revela dívida gigante de TS | Se > 50 erros, abortar esse PR e criar spec próprio para limpar em lote |
| Remover barrel files quebra imports escondidos | Rodar `npm run build` + navegação manual antes de merge |
| Medições variam por máquina | Sempre rodar na mesma máquina, mesmo commit, 3x, reportar mediana |

## Não-objetivos (explicitamente fora desse spec)

- Segurança (CSP `unsafe-inline`, headers, audit de auth) — próximo ciclo
- Reescrita para outra framework (Vite, Remix, etc.)
- Refactor estético de componentes
- Upgrade de dependências (exceto se necessário para perf)
- Testes de performance automatizados no CI (pode virar Fase 3)

## Definition of Done

- `PERF_BASELINE.md` commitado com números iniciais
- Fase 1: pelo menos 4 dos 6 PRs mergeados, cada um com antes/depois mensurável
- `PERF_PROGRESS.md` mostra número final vs baseline
- Cold start e HMR atingem os targets (ou justificativa técnica registrada se não atingirem)
- Sem regressão visual/funcional (checada manualmente em 5 rotas representativas)
