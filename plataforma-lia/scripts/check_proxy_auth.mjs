#!/usr/bin/env node
// Sensor (harness, computacional): detecta proxies em backend-proxy "bespoke"
// que chamam o backend (BACKEND_URL + fetch) sem NENHUM sinal de auth — nem o
// helper canonico getAuthHeaders, nem forward manual do header Authorization,
// nem createProxyHandlers (que injeta auth por default).
//
// Raiz do bug do reveal (2026-06-05): search/reveal/route.ts era proxy bespoke
// e nao injetava o Bearer -> backend respondia "No Bearer token" -> reveal
// falhava com "Erro ao revelar contato". Aquele arquivo nao tinha getAuthHeaders
// NEM forward de Authorization (sinal forte de bug, nao de endpoint publico).
//
// Excecao: comentario "// proxy-auth-exempt: <motivo>" para endpoints publicos
// legitimos (ex.: health checks).
//
// Uso:
//   node scripts/check_proxy_auth.mjs            (warn-only)
//   node scripts/check_proxy_auth.mjs --blocking (exit 1 se violacao)
import { readdirSync, readFileSync, statSync } from "node:fs"
import { join } from "node:path"

const ROOT = "src/app/api/backend-proxy"
const blocking = process.argv.includes("--blocking")

function walk(dir, acc) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) walk(p, acc)
    else if (name === "route.ts") acc.push(p)
  }
  return acc
}

const violations = []
for (const file of walk(ROOT, [])) {
  const src = readFileSync(file, "utf8")
  if (src.includes("proxy-auth-exempt")) continue
  if (src.includes("createProxyHandlers")) continue
  const callsBackend = src.includes("BACKEND_URL") && src.includes("fetch(")
  if (!callsBackend) continue
  const hasAuth = src.includes("getAuthHeaders") || src.includes("Authorization")
  if (!hasAuth) violations.push(file)
}

if (violations.length === 0) {
  console.log("OK check_proxy_auth: 0 violacoes")
  process.exit(0)
}
console.log("check_proxy_auth: " + violations.length + " proxy(s) bespoke chamam o backend SEM nenhum sinal de auth:")
for (const f of violations) console.log("  [" + f + "]")
console.log("  -> Fix: createProxyHandlers({...auth:true}) OU headers: getAuthHeaders(request).")
console.log("     Modelo: search/feedback/route.ts. Publico de proposito? // proxy-auth-exempt: <motivo>")
process.exit(blocking ? 1 : 0)
