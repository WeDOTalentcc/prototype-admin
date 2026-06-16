#!/usr/bin/env node
/**
 * Sensor: collision-prone chat message ids.
 *
 * `Date.now()` is NOT a safe React key. Two messages minted in the same
 * millisecond — a turn that emits a text reply + an action/candidate card in
 * one synchronous tick, or a loop of cards — produce the SAME id, which makes
 * React throw "Encountered two children with the same key" and crashes the
 * message list (the UnifiedMessageList P0, 2026-06-04).
 *
 * Canonical fix: mint ids via `createMessageId(prefix)` from
 * `@/hooks/chat/lia-chat-connection-types` (monotonic counter, collision-safe),
 * or append via `dedupeAppend`.
 *
 * This flags any object `id:` whose ONLY dynamic part is `${Date.now()}`
 * (i.e. a literal with exactly one interpolation, and it is Date.now()).
 * Literals that add extra entropy (`${Math.random()...}`) are NOT flagged.
 *
 * Modes: default warn-only (exit 0). `--blocking` exits 1 when count exceeds
 * `--max=<n>` (default 0).
 */
import { readFileSync, readdirSync, statSync } from "node:fs"
import { join } from "node:path"

const ROOT = "src"
const args = process.argv.slice(2)
const BLOCKING = args.includes("--blocking")
const MAX = Number((args.find((a) => a.startsWith("--max=")) || "--max=0").split("=")[1])

/** id: `...${...}...` capture of the whole template literal. */
const ID_TEMPLATE = /\bid:\s*`([^`]*\$\{[^`]*)`/g

/**
 * Scope guard: only chat-message objects matter for the React-key crash.
 * We flag a collision-prone id only when the surrounding object literal looks
 * like a chat message — has a `sender:`/`role:` field, or `type: "lia"`. This
 * excludes entity ids (filters, departments, column views) that share the
 * `${Date.now()}` pattern but are not rendered as keyed message lists.
 */
const CHAT_SHAPE = /\bsender:\s*['"]?(lia|user|system|assistant)|\brole:\s*['"](assistant|user|system)|\btype:\s*['"]lia['"]/
const WINDOW = 6

function looksLikeChatMessage(lines, idx) {
  const from = Math.max(0, idx - WINDOW)
  const to = Math.min(lines.length, idx + WINDOW + 1)
  return CHAT_SHAPE.test(lines.slice(from, to).join("\n"))
}

function walk(dir, out) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    const st = statSync(p)
    if (st.isDirectory()) {
      if (name === "node_modules" || name === ".next" || name === "__tests__") continue
      walk(p, out)
    } else if (/\.(ts|tsx)$/.test(name)) {
      out.push(p)
    }
  }
}

const files = []
walk(ROOT, files)

const violations = []
for (const file of files) {
  const text = readFileSync(file, "utf-8")
  const lines = text.split("\n")
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    ID_TEMPLATE.lastIndex = 0
    let m
    while ((m = ID_TEMPLATE.exec(line)) !== null) {
      const literal = m[1]
      const interps = literal.match(/\$\{/g) || []
      const hasDateNow = /\$\{\s*Date\.now\(\)\s*\}/.test(literal)
      // Collision-prone iff Date.now() is the SOLE source of dynamism AND the
      // object is a chat message (scope guard against entity-id false positives).
      if (hasDateNow && interps.length === 1 && looksLikeChatMessage(lines, i)) {
        violations.push({ file, line: i + 1, snippet: line.trim().slice(0, 120) })
      }
    }
  }
}

if (violations.length === 0) {
  console.log("✅ check_no_collision_message_ids: 0 collision-prone message ids")
  process.exit(0)
}

console.log(`⚠️  check_no_collision_message_ids: ${violations.length} collision-prone message id(s)\n`)
for (const v of violations) {
  console.log(`  ${v.file}:${v.line}`)
  console.log(`    ${v.snippet}`)
  console.log(`    → Fix: use createMessageId("<prefix>") de @/hooks/chat/lia-chat-connection-types`)
  console.log(`           (Date.now() sozinho colide no mesmo ms → React duplicate key).`)
}

if (BLOCKING && violations.length > MAX) {
  console.error(`\n❌ ${violations.length} > max ${MAX} (modo --blocking).`)
  process.exit(1)
}
process.exit(0)
