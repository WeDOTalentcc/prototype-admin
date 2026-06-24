#!/usr/bin/env node
/**
 * Sensor computacional — proxies backend-proxy sem unwrap do envelope FastAPI.
 *
 * Contexto: o ResponseEnvelopeMiddleware (lia-agent-system) embrulha TODA
 * resposta 2xx JSON em {ok, data, meta}. O factory canonical createProxyHandlers
 * (src/lib/api/proxy-handler.ts:265) desembrulha no caminho de sucesso. Proxies
 * "hand-rolled" que fazem `res.text()` / `response.text()` passthrough devolvem
 * o envelope INTACTO → o FE le `data.data` aninhado em vez de `data`. Classe de
 * bug recorrente (Task #1167 jd/wsi; bug "Banco criado mas nao foi possivel
 * abrir" em talent-pools).
 *
 * Heuristica: route.ts dentro de backend-proxy/ que usa res/response.text() E
 * NAO importa createProxyHandlers nem unwrapEnvelopeSuccess/Error.
 *
 * Ratchet: bloqueia AUMENTO da baseline. Migrar gradualmente reduz o teto.
 *   node scripts/check_proxy_unwrap.mjs               # warn-only
 *   node scripts/check_proxy_unwrap.mjs --max 76      # falha se > 76
 *   node scripts/check_proxy_unwrap.mjs --json
 */
import { readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"

const ROOT = "src/app/api/backend-proxy"

function walk(dir) {
  const out = []
  for (const ent of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, ent.name)
    if (ent.isDirectory()) out.push(...walk(p))
    else if (ent.name === "route.ts") out.push(p)
  }
  return out
}

const HANDROLLED = /\b(res|response)\.text\(\)/
const CANONICAL = /createProxyHandlers|unwrapEnvelopeSuccess|unwrapEnvelopeError/

const offenders = []
for (const file of walk(ROOT)) {
  const src = readFileSync(file, "utf8")
  if (HANDROLLED.test(src) && !CANONICAL.test(src)) offenders.push(file)
}

const argv = process.argv.slice(2)
const json = argv.includes("--json")
const maxIdx = argv.indexOf("--max")
const max = maxIdx >= 0 ? Number(argv[maxIdx + 1]) : Infinity

if (json) {
  console.log(JSON.stringify({ count: offenders.length, max, offenders }, null, 2))
} else if (offenders.length) {
  console.error(`proxy-unwrap: ${offenders.length} proxy(s) hand-rolled sem unwrap do envelope FastAPI:`)
  for (const f of offenders) console.error(`  - ${f}`)
  console.error(
    "\n→ Fix: migrar para createProxyHandlers({ backendPath, methods }) de " +
    "@/lib/api/proxy-handler (desembrulha {ok,data,meta} no sucesso), OU chamar " +
    "unwrapEnvelopeSuccess(data) antes de NextResponse.json. Sem isso o FE recebe " +
    "data.data aninhado e leituras como `data.data.id` resolvem undefined."
  )
} else {
  console.log("✓ proxy-unwrap: 0 proxies hand-rolled sem unwrap")
}

if (offenders.length > max) {
  console.error(`\n❌ ${offenders.length} > limite ${max} — nova rota proxy precisa usar createProxyHandlers/unwrapEnvelope.`)
  process.exit(1)
}
