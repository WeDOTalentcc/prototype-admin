#!/usr/bin/env node
/**
 * check_no_legacy_useSourcingAgents.mjs — Sensor harness #9 Sprint 7B-1.
 *
 * Bane uso do hook legacy `useSourcingAgents` e imports do type `SourcingAgent`,
 * em prep da unification Sprint 7B-2/7B-3 (sourcing_agents → custom_agents M2M).
 *
 * Modo: BLOCKING por default (Sprint 7B-3b Part 3a — baseline 0 mantido pos Part 2 v2
 * frontend swap cc622d4c9). Opt-out via --warn-only para diagnosticos locais.
 *
 * Honra marker `// SOURCING-LEGACY-EXEMPT: <reason>` (mesma linha ou linha
 * imediatamente anterior).
 *
 * Usage:
 *   node scripts/check_no_legacy_useSourcingAgents.mjs              # BLOCKING (default)
 *   node scripts/check_no_legacy_useSourcingAgents.mjs --warn-only  # exit 0 sempre
 *   node scripts/check_no_legacy_useSourcingAgents.mjs --json
 *   node scripts/check_no_legacy_useSourcingAgents.mjs --max-violations=N --blocking
 *
 * Baseline registrado 2026-05-25 (Sprint 7B-1 commit): 0 violations.
 *
 * Ref:
 *  - AGENT_STUDIO_SPRINT7_PLAN.md §3.5 (sensor spec)
 *  - Sprint 7A commit 26a6b8dbb (backend canonical CustomAgent M2M)
 */

import { readFileSync, readdirSync, statSync } from 'fs'
import { join, extname, relative } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const ROOT = join(__dirname, '..')

// Padrões legacy banidos
const LEGACY_PATTERNS = [
  {
    // import { useSourcingAgents } from "..." OU const x = useSourcingAgents(...)
    pattern: /\buseSourcingAgents\b/g,
    name: 'useSourcingAgents',
    canonical: 'usePoolAgents (src/hooks/talent-pools/use-pool-agents.ts)',
    fix: "import { usePoolAgents } from '@/hooks/talent-pools/use-pool-agents'",
  },
  {
    // import { SourcingAgent } / SourcingAgent type usage
    // Exclui SourcingAgentStatusConfig e variantes que NÃO são o type entity
    pattern: /\bSourcingAgent\b(?!StatusConfig|Status\b|StateMachine|Catalog)/g,
    name: 'SourcingAgent',
    canonical: 'CustomAgent (src/components/pages-agent-studio/custom-agents/types.ts) + PoolAgentAssignment (src/types/pool-agent-assignment.ts)',
    fix: "import type { CustomAgent } from '@/components/pages-agent-studio/custom-agents/types' + PoolAgentAssignment",
  },
]

// Dirs/files a ignorar
const EXCLUDE_DIRS = new Set([
  'node_modules', '.next', 'dist', '__tests__', '.impeccable', '.git',
])
const EXCLUDE_FILES = new Set([
  'check_no_legacy_useSourcingAgents.mjs',
])

// Allowlist: arquivos onde o nome legado é referenciado por motivo legítimo
// (config helper que mapeia status, não importa o hook/type).
const ALLOW_FILES = new Set([
  // status-config helper canonical — mapeia visual config dos statuses,
  // nada a ver com o hook/type a serem deletados. Sobrevive ao 7B-3.
  'src/lib/agent-studio/status-config.ts',
])

function* walkFiles(dir) {
  let entries
  try { entries = readdirSync(dir) } catch { return }
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry)) continue
    const full = join(dir, entry)
    let stat
    try { stat = statSync(full) } catch { continue }
    if (stat.isDirectory()) {
      yield* walkFiles(full)
    } else if (['.ts', '.tsx'].includes(extname(entry)) && !EXCLUDE_FILES.has(entry)) {
      yield full
    }
  }
}

function isExempt(lines, idx, lineText) {
  // Marker na mesma linha
  if (lineText.includes('SOURCING-LEGACY-EXEMPT:')) return true
  // Marker na linha anterior
  if (idx > 0 && lines[idx - 1].includes('SOURCING-LEGACY-EXEMPT:')) return true
  return false
}

const args = process.argv.slice(2)
const blocking = !args.includes('--warn-only')  // Sprint 7B-3b Part 3a: default BLOCKING; opt-out via --warn-only
const jsonOutput = args.includes('--json')
const maxArg = args.find(a => a.startsWith('--max-violations='))
const maxViolations = maxArg ? parseInt(maxArg.split('=')[1], 10) : 0

const srcDir = join(ROOT, 'src')
const violations = []

for (const file of walkFiles(srcDir)) {
  const rel = relative(ROOT, file)
  if (ALLOW_FILES.has(rel)) continue

  let content
  try { content = readFileSync(file, 'utf8') } catch { continue }
  const lines = content.split('\n')

  for (const token of LEGACY_PATTERNS) {
    lines.forEach((line, idx) => {
      token.pattern.lastIndex = 0
      let match
      while ((match = token.pattern.exec(line)) !== null) {
        if (isExempt(lines, idx, line)) continue
        violations.push({
          file: rel,
          line: idx + 1,
          col: match.index + 1,
          token: token.name,
          canonical: token.canonical,
          fix: token.fix,
          context: line.trim().slice(0, 120),
        })
      }
    })
  }
}

if (jsonOutput) {
  process.stdout.write(JSON.stringify({ total: violations.length, violations }, null, 2) + '\n')
} else {
  const RESET = '\x1b[0m'
  const YELLOW = '\x1b[33m'
  const RED = '\x1b[31m'
  const GREEN = '\x1b[32m'
  const DIM = '\x1b[2m'

  if (violations.length === 0) {
    console.log(`${GREEN}✓${RESET} check_no_legacy_useSourcingAgents: 0 violations (baseline canonical Sprint 7B-1)`)
  } else {
    const icon = blocking ? `${RED}✗${RESET}` : `${YELLOW}⚠${RESET}`
    console.log(`\n${icon} check_no_legacy_useSourcingAgents: ${violations.length} violation(s) — legacy SourcingAgent/useSourcingAgents\n`)

    const byFile = {}
    for (const v of violations) {
      if (!byFile[v.file]) byFile[v.file] = []
      byFile[v.file].push(v)
    }

    for (const [file, vs] of Object.entries(byFile)) {
      console.log(`  ${YELLOW}${file}${RESET} (${vs.length})`)
      for (const v of vs) {
        console.log(`    ${DIM}[${v.line}:${v.col}]${RESET} ${RED}${v.token}${RESET}`)
        console.log(`      ${DIM}Canonical:${RESET} ${v.canonical}`)
        console.log(`      ${DIM}Fix:${RESET} ${v.fix}`)
        if (v.context) console.log(`      ${DIM}→ ${v.context}${RESET}`)
      }
      console.log('')
    }

    console.log(`  ${DIM}Total: ${violations.length} violation(s)${RESET}`)
    console.log(`  ${DIM}Modo: ${blocking ? 'BLOCKING (Sprint 7B-3b Part 3a default)' : 'WARN-ONLY (--warn-only opt-out)'}${RESET}`)
    console.log(`  ${DIM}Sprint 7B-3b Part 3a: BLOCKING default; opt-out via --warn-only.${RESET}`)
    console.log(`  ${DIM}Exempt marker: // SOURCING-LEGACY-EXEMPT: <reason>${RESET}`)
  }
}

const shouldFail = blocking && violations.length > maxViolations
process.exit(shouldFail ? 1 : 0)
