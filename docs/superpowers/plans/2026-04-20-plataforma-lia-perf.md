# plataforma-lia Performance Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir cold start, HMR e tempo de compilação de rotas no `plataforma-lia/` via medição reprodutível e quick wins em ordem de impacto.

**Architecture:** Três fases em sequência. Fase 0 estabelece baseline numérico antes de qualquer mudança. Fase 1 aplica quick wins isolados (um PR por item) — cada um medido contra baseline. Fase 2 (prod / RSC) fica fora deste plano — spec separado.

**Tech Stack:** Next.js 15 (App Router, Turbopack), React 19, TypeScript, Vitest, npm, biome.

**Spec base:** `docs/superpowers/specs/2026-04-20-plataforma-lia-perf-design.md`

---

## Convenções globais

- Working directory: `/home/victhor/ats_mercado/wedotalent02202026/plataforma-lia` (comandos assumem `cd` para lá).
- Branch de trabalho: a branch atual (não fazer merge em `main`, commitar direto na branch de desenvolvimento).
- Commits pequenos: um commit por task (não por step); steps intermediários não commitam.
- Sem comentários em código novo (regra do projeto). Código deve se auto-explicar pelos nomes.
- Nunca adicionar `// TODO`, `// FIXME`, `// removed`, `// added for X`.
- Após cada task, rodar `npm run lint` e corrigir violações criadas pela task antes de commitar.
- Verificações manuais: navegar `/login`, `/dashboard`, `/jobs`, `/candidates`, `/configuracoes` após tasks que alterem rotas/imports.

---

## Task 1: Fase 0 — Script de baseline reprodutível

**Files:**
- Create: `plataforma-lia/scripts/perf-baseline.sh`
- Create: `plataforma-lia/PERF_BASELINE.md`
- Modify: `plataforma-lia/package.json` (adicionar script `perf:baseline`)

- [ ] **Step 1: Criar o script de medição**

Arquivo: `plataforma-lia/scripts/perf-baseline.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUT="${1:-PERF_BASELINE.md}"
COMMIT="$(git rev-parse --short HEAD)"
NODE_VER="$(node --version)"
DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

echo "# Perf baseline" > "$OUT"
echo "" >> "$OUT"
echo "- Date: $DATE" >> "$OUT"
echo "- Commit: $COMMIT" >> "$OUT"
echo "- Node: $NODE_VER" >> "$OUT"
echo "- Machine: $(uname -sr)" >> "$OUT"
echo "" >> "$OUT"

echo "## File counts" >> "$OUT"
echo "- src total: $(find src -type f \( -name '*.ts' -o -name '*.tsx' \) | wc -l)" >> "$OUT"
echo "- app routes (page.tsx): $(find src/app -name 'page.tsx' | wc -l)" >> "$OUT"
echo "- app api routes (route.ts): $(find src/app/api -name 'route.ts' | wc -l)" >> "$OUT"
echo "- backend-proxy routes: $(find src/app/api/backend-proxy -name 'route.ts' | wc -l)" >> "$OUT"
echo "" >> "$OUT"

echo "## Cold start (3 runs)" >> "$OUT"
for i in 1 2 3; do
  rm -rf .next
  START=$(date +%s%N)
  timeout 90 npm run dev > /tmp/dev-run-$i.log 2>&1 &
  PID=$!
  while ! grep -q "Ready in" /tmp/dev-run-$i.log 2>/dev/null; do
    sleep 0.2
    if ! kill -0 $PID 2>/dev/null; then break; fi
  done
  END=$(date +%s%N)
  kill $PID 2>/dev/null || true
  wait $PID 2>/dev/null || true
  MS=$(( (END - START) / 1000000 ))
  echo "- run $i: ${MS}ms" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Production build" >> "$OUT"
rm -rf .next
START=$(date +%s%N)
npm run build > /tmp/build.log 2>&1 || echo "(build had errors — see /tmp/build.log)" >> "$OUT"
END=$(date +%s%N)
MS=$(( (END - START) / 1000000 ))
echo "- total: ${MS}ms" >> "$OUT"
echo "" >> "$OUT"
echo "### First Load JS por rota (top 15)" >> "$OUT"
echo '```' >> "$OUT"
grep -E '^\s*(┌|├|└|│).*kB' /tmp/build.log | head -15 >> "$OUT" || true
echo '```' >> "$OUT"
echo "" >> "$OUT"

echo "Baseline written to $OUT"
```

- [ ] **Step 2: Tornar executável**

Run: `chmod +x plataforma-lia/scripts/perf-baseline.sh`

- [ ] **Step 3: Adicionar script no package.json**

Em `plataforma-lia/package.json`, na seção `"scripts"`, adicionar após `"analyze"`:

```json
    "perf:baseline": "bash scripts/perf-baseline.sh",
```

- [ ] **Step 4: Rodar o baseline**

Run: `cd plataforma-lia && npm run perf:baseline`
Expected: script termina sem erro, arquivo `PERF_BASELINE.md` criado com seções preenchidas. Se `npm run build` falhar (dado que `ignoreBuildErrors: true`), a seção anota "build had errors" e o script continua.

- [ ] **Step 5: Rodar o bundle analyzer**

Run: `cd plataforma-lia && npm run analyze`
Expected: abre relatório HTML em `.next/analyze/` (ou logs no terminal).

Copiar manualmente os top 20 módulos para `PERF_BASELINE.md` sob nova seção `## Bundle analyzer — top 20 modules`, com linhas no formato:

```markdown
## Bundle analyzer — top 20 modules

| # | Module | Size (gzip) |
|---|--------|-------------|
| 1 | ... | ... |
```

- [ ] **Step 6: HMR manual (medir com cronômetro)**

Fazer `npm run dev`, abrir `http://localhost:3000/dashboard`, editar `src/components/ui/button.tsx` (trocar um texto qualquer em propriedade `className`), cronometrar do `Ctrl+S` até o update visível. 5 iterações. Registrar em `PERF_BASELINE.md`:

```markdown
## HMR (button.tsx — 5 edições)

| Run | Tempo (ms) |
|-----|------------|
| 1   | ... |
| 2   | ... |
| 3   | ... |
| 4   | ... |
| 5   | ... |
| **Mediana** | ... |
```

- [ ] **Step 7: Tempo de primeira compilação de rota**

Com `npm run dev` rodando (fresco, `rm -rf .next`), acessar em ordem: `/login`, `/dashboard`, `/jobs`, `/candidates`, `/configuracoes`. Capturar do log do terminal as linhas `compiled /<rota> in Xs` e registrar em `PERF_BASELINE.md`:

```markdown
## First route compile

| Rota | Tempo |
|------|-------|
| /login | ... |
| /dashboard | ... |
| /jobs | ... |
| /candidates | ... |
| /configuracoes | ... |
```

Se alguma rota não existir exatamente com esse path, substituir pelo equivalente mais próximo e anotar.

- [ ] **Step 8: Commit**

```bash
cd plataforma-lia
git add scripts/perf-baseline.sh package.json PERF_BASELINE.md
git commit -m "perf(baseline): medição inicial + script reprodutível"
```

---

## Task 2: Limpar lixo na raiz do plataforma-lia

**Files:**
- Delete: `plataforma-lia/a.out`
- Delete: `plataforma-lia/tsc_output.txt`
- Delete: `plataforma-lia/full_tsc_output.txt`
- Delete: `plataforma-lia/nohup.out`
- Modify: `plataforma-lia/.gitignore`

- [ ] **Step 1: Confirmar arquivos existem e estão trackeados**

Run: `cd plataforma-lia && git ls-files | grep -E '^(a\.out|tsc_output\.txt|full_tsc_output\.txt|nohup\.out)$'`
Expected: lista com os arquivos trackeados. Se algum não estiver no git, ajustar próximo step.

- [ ] **Step 2: Remover arquivos**

Run: `cd plataforma-lia && git rm -f a.out tsc_output.txt full_tsc_output.txt nohup.out 2>/dev/null || true; rm -f a.out tsc_output.txt full_tsc_output.txt nohup.out`
Expected: arquivos deletados do disco e index.

- [ ] **Step 3: Adicionar patterns ao .gitignore**

Em `plataforma-lia/.gitignore`, adicionar ao final:

```
# build/run artifacts
a.out
nohup.out
tsc_output*.txt
*.tsbuildinfo
```

(Nota: `*.tsbuildinfo` cobre `tsconfig.tsbuildinfo` que já existe no disco.)

- [ ] **Step 4: Verificar tsconfig.tsbuildinfo**

Run: `cd plataforma-lia && git ls-files | grep tsbuildinfo`
Se aparecer, rodar: `cd plataforma-lia && git rm --cached tsconfig.tsbuildinfo`

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add .gitignore
git commit -m "chore(cleanup): remover artefatos de build da raiz e ignorar"
```

---

## Task 3: Dynamic import — html2canvas + jspdf (geração de PDF)

**Files:**
- Modify: `plataforma-lia/src/components/modals/job-compare/generateComparePDF.ts`
- Modify: `plataforma-lia/src/components/modals/job-compare/useJobCompare.ts`
- Modify: `plataforma-lia/src/components/job-report-modal.tsx`

- [ ] **Step 1: Identificar todos os consumidores**

Run: `cd plataforma-lia && grep -rn "from 'html2canvas'\|from 'jspdf'\|from \"html2canvas\"\|from \"jspdf\"" src/`
Expected: ≤ 5 arquivos. Se aparecer algum não listado acima, tratar no mesmo PR.

- [ ] **Step 2: Converter imports estáticos → dinâmicos em `generateComparePDF.ts`**

Ler o arquivo antes de editar. O padrão é: trocar o import de topo por `await import(...)` dentro da função que gera o PDF.

Substituir o bloco `import html2canvas from 'html2canvas'` (e similar para jspdf) e qualquer uso, por:

```ts
export async function generateComparePDF(/* assinatura existente */) {
  const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
    import('html2canvas'),
    import('jspdf'),
  ])

  // restante do corpo da função permanece igual,
  // pois html2canvas e jsPDF continuam disponíveis com os mesmos nomes
}
```

Se a função não for `async`, torná-la `async` e atualizar callers (caller típico: `useJobCompare.ts`).

- [ ] **Step 3: Atualizar `useJobCompare.ts` se assinatura virou async**

Garantir que o hook aguarde o resultado: `await generateComparePDF(...)`. Ler o arquivo antes de editar.

- [ ] **Step 4: Aplicar mesmo padrão em `job-report-modal.tsx`**

Mover imports `html2canvas`/`jspdf` para dentro do handler que dispara a exportação (ex.: `handleExportPDF`) como `await import(...)`, removendo do topo do arquivo.

- [ ] **Step 5: Verificar build**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`
Expected: build conclui. Erros pré-existentes (antes do PR) permanecem, mas nenhum erro novo introduzido.

- [ ] **Step 6: Verificação manual**

Rodar `npm run dev`, entrar numa tela com botão de exportar PDF (comparar vagas ou relatório de vaga), acionar exportação, confirmar que o arquivo gera normalmente.

- [ ] **Step 7: Re-medir bundle**

Run: `cd plataforma-lia && npm run analyze`
Confirmar que `html2canvas` e `jspdf` não aparecem mais no First Load JS das rotas iniciais — aparecem apenas como chunks separados carregados on-demand. Anotar delta em `PERF_PROGRESS.md` (criar na Task 12 se ainda não existe).

- [ ] **Step 8: Commit**

```bash
cd plataforma-lia
git add src/components/modals/job-compare/ src/components/job-report-modal.tsx
git commit -m "perf(bundle): dynamic import de html2canvas e jspdf"
```

---

## Task 4: Dynamic import — recharts + chart.js

**Files:**
- Modify: `plataforma-lia/src/components/charts/interactive-charts.tsx`
- Modify: `plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`
- Modify: `plataforma-lia/src/components/pages/ai-credits-page.tsx`
- Modify: `plataforma-lia/src/components/pages/indicators-page.tsx`

- [ ] **Step 1: Mapear consumidores**

Run: `cd plataforma-lia && grep -rn "from 'recharts'\|from \"recharts\"\|from 'chart.js'\|from \"chart.js\"\|from 'react-chartjs-2'\|from \"react-chartjs-2\"" src/`
Expected: lista de arquivos que importam essas libs.

- [ ] **Step 2: Decidir estratégia de dynamic per-component**

Para **componentes de gráfico** (`interactive-charts.tsx`, `advanced-interactive-charts.tsx`): transformar em default export, e consumers importam via `next/dynamic`. Evita mudar internos.

Em cada arquivo de página que consome esses charts (`ai-credits-page.tsx`, `indicators-page.tsx`, etc.), trocar:

```tsx
import { InteractiveCharts } from '@/components/charts/interactive-charts'
```

por:

```tsx
import dynamic from 'next/dynamic'

const InteractiveCharts = dynamic(
  () => import('@/components/charts/interactive-charts').then(m => m.InteractiveCharts),
  { ssr: false, loading: () => <div className="h-chart-sm animate-pulse bg-muted rounded-lg" /> }
)
```

- [ ] **Step 3: Aplicar a cada consumer listado no Step 1**

Ler cada arquivo, substituir o import e manter o restante do JSX intacto.

- [ ] **Step 4: Verificar uso direto de `recharts`/`chart.js` em componentes não-chart**

Se `grep` no Step 1 listar arquivos fora de `src/components/charts/`, tratá-los: envolver o componente que usa o gráfico num wrapper lazy ou mover o import para dentro do componente que é dynamic.

- [ ] **Step 5: Build + verificação**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`
Expected: build conclui sem erros novos.

- [ ] **Step 6: Verificação manual**

Rodar `npm run dev`, abrir páginas com gráficos (`/ai-credits`, `/indicators` ou equivalentes), confirmar que gráficos renderizam após skeleton.

- [ ] **Step 7: Commit**

```bash
cd plataforma-lia
git add src/components/charts/ src/components/pages/
git commit -m "perf(bundle): dynamic import de charts (recharts + chart.js)"
```

---

## Task 5: Dynamic import — @tiptap (editor rico)

**Files:**
- Modify: `plataforma-lia/src/components/ui/lia-editor.tsx`
- Modify: consumers de `lia-editor` (descobrir via grep)

- [ ] **Step 1: Mapear consumers**

Run: `cd plataforma-lia && grep -rn "from '@/components/ui/lia-editor'\|from \"@/components/ui/lia-editor\"" src/`
Expected: lista de componentes que importam o editor.

- [ ] **Step 2: Transformar `lia-editor.tsx` em módulo dynamic-friendly**

Manter o componente como está, mas confirmar que exporta um componente React (default ou nomeado). Ler o arquivo primeiro.

- [ ] **Step 3: Converter cada consumer para `next/dynamic`**

Em cada arquivo listado no Step 1, substituir o import por:

```tsx
import dynamic from 'next/dynamic'

const LiaEditor = dynamic(
  () => import('@/components/ui/lia-editor').then(m => m.LiaEditor),
  { ssr: false, loading: () => <div className="min-h-[120px] animate-pulse bg-muted rounded-lg" /> }
)
```

Ajustar o nome da export (`LiaEditor` vs `default`) conforme o arquivo.

- [ ] **Step 4: Build**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`
Expected: sem erros novos.

- [ ] **Step 5: Verificação manual**

Rodar `npm run dev`, abrir formulário/tela que usa o editor (ex.: criação de vaga, comentários), confirmar que digitação + formatação funcionam.

- [ ] **Step 6: Commit**

```bash
cd plataforma-lia
git add src/
git commit -m "perf(bundle): dynamic import de @tiptap via lia-editor"
```

---

## Task 6: Dynamic import — @twilio/voice-sdk

**Files:**
- Modify: consumers descobertos via grep

- [ ] **Step 1: Mapear consumers**

Run: `cd plataforma-lia && grep -rn "from '@twilio/voice-sdk'\|from \"@twilio/voice-sdk\"" src/`
Expected: 1–3 arquivos (provavelmente relacionados a voice/call).

- [ ] **Step 2: Aplicar padrão await import**

Em cada consumer, mover o import para dentro da função que inicializa o device (ex.: `connectCall`, `initDevice`):

```ts
async function initDevice() {
  const { Device } = await import('@twilio/voice-sdk')
  const device = new Device(token, options)
  return device
}
```

Remover o import de topo.

- [ ] **Step 3: Ajustar callers se ficaram síncronos**

Se a função pública virou async, atualizar os callers com `await`.

- [ ] **Step 4: Build + verificação manual**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`

Verificação manual: se possível, testar inicialização de call na UI. Se não houver acesso fácil, confirmar pelo menos que a rota/tela de voice abre sem erro de console.

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add src/
git commit -m "perf(bundle): dynamic import de @twilio/voice-sdk"
```

---

## Task 7: Dynamic import — @microsoft/teams-js

**Files:**
- Modify: `plataforma-lia/src/hooks/company/use-teams-sso.ts`
- Modify: outros consumers descobertos via grep

- [ ] **Step 1: Mapear consumers**

Run: `cd plataforma-lia && grep -rn "from '@microsoft/teams-js'\|from \"@microsoft/teams-js\"" src/`

- [ ] **Step 2: Converter hook `use-teams-sso.ts`**

Ler o arquivo primeiro. Converter o import de topo para `await import` dentro do efeito/função que usa o SDK. Exemplo:

```ts
useEffect(() => {
  let cancelled = false
  async function init() {
    const teamsJs = await import('@microsoft/teams-js')
    if (cancelled) return
    teamsJs.app.initialize()
  }
  init()
  return () => { cancelled = true }
}, [])
```

Remover `import * as microsoftTeams from '@microsoft/teams-js'` (ou equivalente) do topo.

- [ ] **Step 3: Aplicar o mesmo padrão em outros consumers**

- [ ] **Step 4: Build + verificação**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`

Verificação: rota que depende de Teams SSO abre sem erro para usuário fora do Teams (fallback deve funcionar).

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add src/
git commit -m "perf(bundle): dynamic import de @microsoft/teams-js"
```

---

## Task 8: Auditar jira.js, canvg, marked

**Files:**
- Verify: `plataforma-lia/src/lib/api/jira-service.ts`
- Verify: `plataforma-lia/src/lib/render-markdown.ts`
- Modify (if client-side): conforme achado

- [ ] **Step 1: Identificar se cada lib chega no bundle do client**

Run: `cd plataforma-lia && grep -rn "from 'jira.js'\|from \"jira.js\"\|from 'canvg'\|from \"canvg\"\|from 'marked'\|from \"marked\"" src/`

Para cada arquivo na lista:

Run: `cd plataforma-lia && grep -l "\"use client\"\|'use client'" <arquivo>`

Se o arquivo NÃO tem `'use client'` E é usado apenas via API routes (`src/app/api/**`), ele roda server-side → bundle do client não é afetado → pular.

Se é usado em componente client, aplicar dynamic import.

- [ ] **Step 2: `jira-service.ts` — decidir**

Ler `src/lib/api/jira-service.ts`. Se só é consumido por route handlers em `src/app/api/backend-proxy/` (provavelmente o caso), marcar como "server-only, sem mudança" no commit de Task 12. Senão, aplicar dynamic.

- [ ] **Step 3: `render-markdown.ts` (marked)**

Provavelmente usado em client (chat, previews). Aplicar dynamic no consumer:

Ler `src/lib/render-markdown.ts`. Se exporta uma função `renderMarkdown(text)`, converter para:

```ts
export async function renderMarkdown(text: string): Promise<string> {
  const { marked } = await import('marked')
  return marked.parse(text, { async: false }) as string
}
```

Atualizar callers para `await renderMarkdown(...)`. Se callers são componentes, usar state + `useEffect`.

- [ ] **Step 4: canvg**

Run: `cd plataforma-lia && grep -rn "from 'canvg'\|from \"canvg\"" src/`

Aplicar dynamic import no consumer.

- [ ] **Step 5: Build + verificação**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`

Verificação manual: markdown renderiza (ex.: mensagens de chat), SVG export (se usado), jira sync não quebrou.

- [ ] **Step 6: Commit**

```bash
cd plataforma-lia
git add src/
git commit -m "perf(bundle): dynamic imports para jira/canvg/marked quando client-side"
```

---

## Task 9: Consolidar backend-proxy via catch-all passthrough

**Files:**
- Create: `plataforma-lia/src/app/api/backend-proxy/[...path]/route.ts`
- Create: `plataforma-lia/src/app/api/backend-proxy/[...path]/__tests__/route.test.ts`
- Delete (seleção conservadora): rotas 100% passthrough listadas abaixo

- [ ] **Step 1: Escrever teste que falha (TDD)**

Arquivo: `plataforma-lia/src/app/api/backend-proxy/[...path]/__tests__/route.test.ts`

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

beforeEach(() => {
  fetchMock.mockReset()
  process.env.BACKEND_URL = 'http://backend.test'
})

describe('backend-proxy catch-all', () => {
  it('forwards GET with auth header and path', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    )

    const { GET } = await import('../route')
    const req = new NextRequest('http://localhost:3000/api/backend-proxy/analytics/ml-predictions?q=1', {
      headers: { authorization: 'Bearer xyz' },
    })
    const res = await GET(req, { params: Promise.resolve({ path: ['analytics', 'ml-predictions'] }) })

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://backend.test/api/v1/analytics/ml-predictions?q=1')
    expect((init as RequestInit).method).toBe('GET')
    expect((init as RequestInit).headers).toMatchObject({ Authorization: 'Bearer xyz' })
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true })
  })

  it('forwards POST body and content-type', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ created: true }), { status: 201 }),
    )

    const { POST } = await import('../route')
    const req = new NextRequest('http://localhost:3000/api/backend-proxy/foo/bar', {
      method: 'POST',
      headers: { authorization: 'Bearer xyz', 'content-type': 'application/json' },
      body: JSON.stringify({ x: 1 }),
    })
    const res = await POST(req, { params: Promise.resolve({ path: ['foo', 'bar'] }) })

    const [, init] = fetchMock.mock.calls[0]
    expect((init as RequestInit).method).toBe('POST')
    expect(await res.json()).toEqual({ created: true })
    expect(res.status).toBe(201)
  })

  it('propagates backend error status', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: 'not found' }), { status: 404 }),
    )

    const { GET } = await import('../route')
    const req = new NextRequest('http://localhost:3000/api/backend-proxy/missing', {
      headers: { authorization: 'Bearer xyz' },
    })
    const res = await GET(req, { params: Promise.resolve({ path: ['missing'] }) })

    expect(res.status).toBe(404)
  })
})
```

- [ ] **Step 2: Rodar teste — deve falhar (arquivo `route.ts` não existe)**

Run: `cd plataforma-lia && npx vitest run src/app/api/backend-proxy/[...path]/__tests__/route.test.ts --project=unit`
Expected: FAIL — "Cannot find module '../route'".

- [ ] **Step 3: Implementar o catch-all**

Arquivo: `plataforma-lia/src/app/api/backend-proxy/[...path]/route.ts`

```ts
export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

type Params = { params: Promise<{ path: string[] }> }

async function forward(request: NextRequest, params: Params['params']) {
  const { path } = await params
  const target = `${BACKEND_URL}/api/v1/${path.join('/')}${new URL(request.url).search}`

  const headers = new Headers()
  const auth = request.headers.get('authorization')
  if (auth) headers.set('Authorization', auth)
  const contentType = request.headers.get('content-type')
  if (contentType) headers.set('Content-Type', contentType)
  const authMethod = request.headers.get('x-auth-method')
  if (authMethod) headers.set('X-Auth-Method', authMethod)

  const method = request.method
  const hasBody = method !== 'GET' && method !== 'HEAD' && method !== 'DELETE'
  const body = hasBody ? await request.text() : undefined

  const response = await fetch(target, { method, headers, body })
  const responseBody = await response.text()
  const responseHeaders = new Headers()
  const responseContentType = response.headers.get('content-type')
  if (responseContentType) responseHeaders.set('Content-Type', responseContentType)

  return new NextResponse(responseBody, {
    status: response.status,
    headers: responseHeaders,
  })
}

export async function GET(request: NextRequest, ctx: Params) { return forward(request, ctx.params) }
export async function POST(request: NextRequest, ctx: Params) { return forward(request, ctx.params) }
export async function PUT(request: NextRequest, ctx: Params) { return forward(request, ctx.params) }
export async function PATCH(request: NextRequest, ctx: Params) { return forward(request, ctx.params) }
export async function DELETE(request: NextRequest, ctx: Params) { return forward(request, ctx.params) }
```

- [ ] **Step 4: Rodar teste — deve passar**

Run: `cd plataforma-lia && npx vitest run "src/app/api/backend-proxy/[...path]/__tests__/route.test.ts" --project=unit`
Expected: 3 passed.

- [ ] **Step 5: Identificar rotas 100% passthrough para deletar**

Run: `cd plataforma-lia && for f in $(find src/app/api/backend-proxy -name 'route.ts' -not -path '*/\[*'); do lines=$(wc -l < "$f"); if [ "$lines" -lt 40 ] && ! grep -q "validateBody\|z\.\|zod\|schema" "$f"; then echo "$f"; fi; done | head -30`

Expected: lista de rotas curtas e sem validação — candidatas a deletar.

- [ ] **Step 6: Deletar primeiro lote (máximo 20 rotas nesse PR)**

Para cada arquivo listado no Step 5 (até 20), ler o arquivo para confirmar que é realmente passthrough puro (só fetch + forward). Se tem qualquer transformação de URL (ex.: URL diferente, path rewrite para não-padrão), **pular**.

Run (para cada confirmada): `cd plataforma-lia && git rm <caminho>`

Registrar em `PERF_PROGRESS.md` a lista de rotas removidas.

- [ ] **Step 7: Build**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`
Expected: build conclui, número de rotas diminuiu no output.

- [ ] **Step 8: Verificação manual**

Rodar `npm run dev`, abrir app, navegar por 5 telas diferentes que consomem endpoints removidos (ex.: analytics, alertas), conferir que requests funcionam — Network tab mostra 200/201.

- [ ] **Step 9: Commit**

```bash
cd plataforma-lia
git add src/app/api/backend-proxy/ PERF_PROGRESS.md
git commit -m "perf(proxy): catch-all + remoção de 20 rotas passthrough"
```

---

## Task 10: Auditar barrel files

**Files:**
- Modify: `index.ts` encontrados que re-exportem tudo sem necessidade

- [ ] **Step 1: Identificar barrel files com re-export amplo**

Run: `cd plataforma-lia && grep -rn "export \* from" src/ --include="*.ts" --include="*.tsx" | head -50`

Run: `cd plataforma-lia && find src -name 'index.ts' -o -name 'index.tsx' | xargs wc -l | sort -rn | head -20`

Barrel file problemático = `index.ts` com muitos `export * from './...'` E consumido via `import { X } from '@/folder'` sem path completo.

- [ ] **Step 2: Para cada barrel file na lista, decidir**

Para cada arquivo:

a) Se é um `index.ts` de pasta `ui/` com poucos re-exports (< 10) e tree-shaking já funciona porque cada export usa `export { X } from './x'` explícito (não `export *`): **manter**.

b) Se usa `export * from '.../'` e lista > 5 módulos: **mudar o padrão** — substituir `export *` por re-exports nomeados:

Antes:
```ts
export * from './foo'
export * from './bar'
```

Depois:
```ts
export { Foo } from './foo'
export { Bar } from './bar'
```

c) Se o arquivo for puramente conveniência e podemos mudar os consumers em pouco tempo: **deletar o barrel** e ajustar imports para path direto:

```bash
cd plataforma-lia
grep -rn "from '@/components/ui'" src/ | head -20
```

Depois substituir `from '@/components/ui'` por `from '@/components/ui/<componente-especifico>'` nos consumers.

Escopo desse PR: **apenas os 3 barrel files com maior contagem de linhas**. Os demais ficam para follow-up se o baseline mostrar que ainda há problema.

- [ ] **Step 3: Build**

Run: `cd plataforma-lia && npm run lint && npx next build 2>&1 | tail -30`
Expected: sem erros novos.

- [ ] **Step 4: Verificação manual**

Navegar por 5 rotas principais. Qualquer import quebrado aparece imediatamente no console.

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add src/
git commit -m "perf(bundle): eliminar export * em barrel files para melhorar tree-shaking"
```

---

## Task 11: Expandir optimizePackageImports + modularizeImports

**Files:**
- Modify: `plataforma-lia/next.config.js`

- [ ] **Step 1: Identificar libs candidatas**

Do `PERF_BASELINE.md`, olhar a seção "Bundle analyzer — top 20 modules". Para cada lib que não está no `optimizePackageImports` atual, avaliar.

Libs atuais no `optimizePackageImports` (do `next.config.js`):
```
lucide-react
@radix-ui/react-accordion ... (todos radix)
recharts
```

Candidatas a adicionar:
- `date-fns` (se aparecer no bundle)
- `sonner`
- `cmdk`
- `@tanstack/react-virtual`
- Qualquer `@radix-ui/*` ainda não listado (ex.: `react-slot`, `react-switch`, `react-progress`, etc.)

- [ ] **Step 2: Atualizar `next.config.js`**

Ler o arquivo e substituir o bloco `experimental.optimizePackageImports` pela lista expandida:

```js
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      'date-fns',
      'sonner',
      'cmdk',
      '@tanstack/react-virtual',
      '@radix-ui/react-accordion',
      '@radix-ui/react-alert-dialog',
      '@radix-ui/react-avatar',
      '@radix-ui/react-checkbox',
      '@radix-ui/react-collapsible',
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-label',
      '@radix-ui/react-popover',
      '@radix-ui/react-progress',
      '@radix-ui/react-radio-group',
      '@radix-ui/react-scroll-area',
      '@radix-ui/react-select',
      '@radix-ui/react-separator',
      '@radix-ui/react-slider',
      '@radix-ui/react-slot',
      '@radix-ui/react-switch',
      '@radix-ui/react-tabs',
      '@radix-ui/react-toast',
      '@radix-ui/react-tooltip',
      'recharts',
    ],
  },
```

- [ ] **Step 3: Adicionar `modularizeImports` para `date-fns` (se necessário)**

Se `date-fns` aparece no bundle analyzer com > 50KB, adicionar ao mesmo arquivo `next.config.js`, dentro do objeto `nextConfig` (fora de `experimental`):

```js
  modularizeImports: {
    'date-fns': {
      transform: 'date-fns/{{member}}',
    },
  },
```

- [ ] **Step 4: Build + medir**

Run: `cd plataforma-lia && npx next build 2>&1 | tail -30`
Expected: build conclui. Sem erros novos.

Run: `cd plataforma-lia && npm run analyze`
Anotar novo top 20 em `PERF_PROGRESS.md` para comparação.

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add next.config.js PERF_PROGRESS.md
git commit -m "perf(bundle): expandir optimizePackageImports + modularizeImports date-fns"
```

---

## Task 12: Re-medir baseline + relatório final

**Files:**
- Create (ou atualizar): `plataforma-lia/PERF_PROGRESS.md`

- [ ] **Step 1: Rodar script novamente**

Run: `cd plataforma-lia && npm run perf:baseline PERF_AFTER.md`
Expected: novo arquivo `PERF_AFTER.md` gerado.

- [ ] **Step 2: HMR + first-route-compile manual**

Repetir Steps 6 e 7 da Task 1, exatamente os mesmos procedimentos, anotando os novos números. Registrar em `PERF_AFTER.md`.

- [ ] **Step 3: Consolidar em PERF_PROGRESS.md**

Criar (ou atualizar se já existia nas tasks anteriores) `plataforma-lia/PERF_PROGRESS.md`:

```markdown
# Perf progress — Fase 1

## Antes vs depois

| Métrica | Baseline | Depois | Delta |
|---------|----------|--------|-------|
| Cold start (mediana de 3) | ... ms | ... ms | ... % |
| HMR (mediana de 5) | ... ms | ... ms | ... % |
| First compile /dashboard | ... ms | ... ms | ... % |
| First compile /jobs | ... ms | ... ms | ... % |
| First compile /candidates | ... ms | ... ms | ... % |
| `next build` total | ... ms | ... ms | ... % |
| First Load JS (rota raiz) | ... kB | ... kB | ... % |
| Backend-proxy routes | 156 | ... | ... |

## Targets atingidos

- [ ] Cold start < 10s
- [ ] HMR < 1s (arquivo leve)
- [ ] First route compile < 3s

## PRs aplicados nessa fase

- Task 2: cleanup root
- Task 3: dynamic html2canvas + jspdf
- Task 4: dynamic charts
- Task 5: dynamic @tiptap
- Task 6: dynamic @twilio/voice-sdk
- Task 7: dynamic @microsoft/teams-js
- Task 8: dynamic jira/canvg/marked (client-only)
- Task 9: catch-all + remoção de proxies
- Task 10: barrel files
- Task 11: optimizePackageImports expandido

## Próximos passos

- Se algum target não foi atingido, documentar causa aqui e criar spec específica (ex.: Task 13 build gates, Fase 2 RSC).
```

Preencher com os números reais.

- [ ] **Step 4: Commit**

```bash
cd plataforma-lia
git add PERF_AFTER.md PERF_PROGRESS.md
git commit -m "perf(baseline): medição pós-Fase 1 e resumo de ganhos"
```

---

## Task 13 (condicional) — Build gates

Executar **apenas se** `next build` do PERF_AFTER mostrar < 50 erros de TS quando `ignoreBuildErrors` for removido. Senão, abortar e criar spec separado para limpeza de dívida de tipos.

**Files:**
- Modify: `plataforma-lia/next.config.js`

- [ ] **Step 1: Contar erros escondidos**

Em `plataforma-lia/next.config.js`, temporariamente trocar:
```js
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
```
por:
```js
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: false },
```

Run: `cd plataforma-lia && npx next build 2>&1 | tee /tmp/build-gates.log | tail -100`

Contar erros de TS: `grep -c "error TS" /tmp/build-gates.log`
Contar erros de ESLint: `grep -c "Error:" /tmp/build-gates.log` (ajustar padrão conforme output real)

- [ ] **Step 2: Decisão**

Se TS errors + ESLint errors > 50 → reverter `next.config.js` para o original, registrar em `PERF_PROGRESS.md`:

```markdown
## Build gates — deferido

Contagem atual: X erros de TS, Y erros de ESLint. > 50 total → criar spec dedicado em `docs/superpowers/specs/YYYY-MM-DD-build-gates-cleanup-design.md` para limpeza incremental.
```

Commitar o `PERF_PROGRESS.md` atualizado, sem o patch em `next.config.js`. Terminar aqui.

Se ≤ 50 → prosseguir Step 3.

- [ ] **Step 3: Corrigir erros restantes**

Para cada erro listado em `/tmp/build-gates.log`, aplicar fix mínimo no arquivo e linha apontados. **Não** fazer refactor maior; só o mínimo para compilar/lint passar.

Re-rodar `npx next build` após cada ~10 fixes.

- [ ] **Step 4: Build limpo**

Run: `cd plataforma-lia && npx next build`
Expected: termina sem erros de TS/ESLint.

- [ ] **Step 5: Commit**

```bash
cd plataforma-lia
git add next.config.js src/ PERF_PROGRESS.md
git commit -m "perf(gates): ligar typecheck e lint no build"
```

---

## Self-review do plano

**Spec coverage:**
- Fase 0 (baseline + script) → Task 1 ✓
- Fase 1 item 1 (cleanup) → Task 2 ✓
- Fase 1 item 2 (dynamic imports) → Tasks 3, 4, 5, 6, 7, 8 ✓
- Fase 1 item 3 (consolidar backend-proxy) → Task 9 ✓
- Fase 1 item 4 (barrel files) → Task 10 ✓
- Fase 1 item 5 (optimizePackageImports + modularizeImports) → Task 11 ✓
- Fase 1 item 6 (build gates) → Task 13 (condicional) ✓
- "Fim da fase 1: medição vs baseline" → Task 12 ✓
- Fase 2 (prod / RSC) → explicitamente fora desse plano (spec separado) ✓

**Placeholders:** nenhum "TBD" / "TODO" / "implementar depois" nas tasks executáveis.

**Type/signature consistency:** o catch-all route usa `Params = { params: Promise<{ path: string[] }> }` consistente entre implementação e teste.

**Paths explícitos:** sim.

**Código completo:** sim — cada task que altera código inclui o bloco exato ou instrução precisa de transformação.
