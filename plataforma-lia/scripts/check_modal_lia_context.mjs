#!/usr/bin/env node
/**
 * check_modal_lia_context.mjs — P0-2 sensor (2026-06-18)
 *
 * Harness sensor: finds TSX components that render a Dialog/Sheet with
 * open={...} or isOpen={...} prop but do NOT call setLiaModal() anywhere
 * in the same file. These modals are invisible to LIA (she won't know
 * they're open when a message is sent).
 *
 * Computacional sensor (determinístico, regex-based).
 * Exit 0 = no violations (or --warn-only). Exit 1 = violations found.
 *
 * Usage:
 *   node scripts/check_modal_lia_context.mjs
 *   node scripts/check_modal_lia_context.mjs --blocking
 *
 * LLM-optimized error output: includes fix instructions in Portuguese.
 */
import { readFileSync, readdirSync, statSync } from 'fs'
import { join, relative } from 'path'
import process from 'process'

const BLOCKING = process.argv.includes('--blocking')
const ROOT = new URL('..', import.meta.url).pathname

// Files that ARE exempted — lia-context-store itself + test files
const EXEMPT_PATTERNS = [
  'lia-context-store',
  'lia-context-utils',
  '__tests__',
  '.test.',
  '.spec.',
  'node_modules',
  '.next',
  'check_modal_lia_context',
]

// Regex: any Dialog/Sheet/AlertDialog rendered with an open={} or isOpen={} prop
const HAS_MODAL_OPEN = /(?:Dialog|Sheet|AlertDialog)\s+[^>]*(?:open=\{|isOpen=\{)/
// Regex: import of setLiaModal from lia-context-store
const HAS_LIA_MODAL = /(?:import[^;]*setLiaModal[^;]*lia-context-store|\/\/ lia-context:)/

function walkTsx(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    try {
      const stat = statSync(full)
      if (stat.isDirectory()) {
        if (!EXEMPT_PATTERNS.some(p => entry.includes(p))) walkTsx(full, files)
      } else if (entry.endsWith('.tsx') || entry.endsWith('.ts')) {
        files.push(full)
      }
    } catch {}
  }
  return files
}

const srcDir = join(ROOT, 'src')
const allFiles = walkTsx(srcDir)

const violations = []

for (const file of allFiles) {
  if (EXEMPT_PATTERNS.some(p => file.includes(p))) continue
  const content = readFileSync(file, 'utf8')
  if (!HAS_MODAL_OPEN.test(content)) continue
  if (HAS_LIA_MODAL.test(content)) continue

  const rel = relative(ROOT, file)
  violations.push(rel)
}

if (violations.length === 0) {
  console.log('✅ check_modal_lia_context: 0 violations — all modal components call setLiaModal()')
  process.exit(0)
}

console.log(`\n⚠️  check_modal_lia_context: ${violations.length} componente(s) com Dialog/Sheet open={} SEM setLiaModal()`)
console.log()
console.log('Estes modais são INVISÍVEIS para a LIA — ela não sabe que estão abertos.')
console.log()
for (const v of violations) {
  console.log(`  [${v}]`)
}
console.log()
console.log('→ Fix: adicione import { setLiaModal } from "@/lib/lia-context-store"')
console.log('       e chame setLiaModal("nome-do-modal") no onOpenChange quando open=true,')
console.log('       e setLiaModal(null) quando open=false.')
console.log()
console.log('Exemplo canônico: useUniversalTransitionModal.tsx')
console.log()

if (BLOCKING) {
  process.exit(1)
}
process.exit(0)
