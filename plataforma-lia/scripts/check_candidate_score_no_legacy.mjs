#!/usr/bin/env node
/**
 * check_candidate_score_no_legacy.mjs  (v2.1 — F2 canonical update)
 * Sensor canonical: detecta padrão "/100" em arquivos candidate-* (exceto comentários e testes).
 * Exit 1 se encontrar. Exit 0 se limpo.
 *
 * v2.1 changes:
 * - Escaneia candidate-profile, candidate-preview e candidate-page
 * - Honra marker @canonical-allow-100 na mesma linha OU na linha anterior
 *   (suporta JSX block comment prev-line @canonical-allow-100 acima da linha)
 *
 * Uso: node scripts/check_candidate_score_no_legacy.mjs
 */

import { readFileSync, readdirSync, statSync, existsSync } from "fs"
import { join, extname } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]
const PATTERN = /\/100/
const COMMENT_LINE = /^\s*(\/\/|\/\*|\*)/
const EXEMPTION_MARKER = /@canonical-allow-100/

let violations = []

function walkDir(dir) {
  const entries = readdirSync(dir)
  for (const entry of entries) {
    const fullPath = join(dir, entry)
    const stat = statSync(fullPath)
    if (stat.isDirectory()) {
      if (entry === "__tests__" || entry === "node_modules") continue
      walkDir(fullPath)
    } else if (stat.isFile()) {
      const ext = extname(entry)
      if (![".ts", ".tsx"].includes(ext)) continue
      if (entry.endsWith(".test.tsx") || entry.endsWith(".test.ts")) continue

      const content = readFileSync(fullPath, "utf-8")
      const lines = content.split("\n")
      lines.forEach((line, idx) => {
        if (COMMENT_LINE.test(line)) return // skip pure comment lines
        if (EXEMPTION_MARKER.test(line)) return // inline @canonical-allow-100 exemption
        // Also check prev line for JSX block comment exemption: {/* @canonical-allow-100 ... */}
        const prevLine = idx > 0 ? lines[idx - 1] : ""
        if (EXEMPTION_MARKER.test(prevLine)) return // prev-line exemption (JSX comments)
        if (PATTERN.test(line)) {
          violations.push({ file: fullPath, line: idx + 1, text: line.trim() })
        }
      })
    }
  }
}

for (const dir of SEARCH_DIRS) {
  if (!existsSync(dir)) continue
  try {
    walkDir(dir)
  } catch (e) {
    console.error("Error scanning directory:", e.message)
    process.exit(2)
  }
}

if (violations.length === 0) {
  console.log("✓ check_candidate_score_no_legacy v2.1: 0 violations — no unexempted /100 pattern in candidate-* components")
  process.exit(0)
} else {
  console.error(`✗ check_candidate_score_no_legacy v2.1: ${violations.length} violation(s) found!`)
  console.error('  Pattern "/100" is FORBIDDEN in candidate-* components (use 0-10 WSI scale).')
  console.error('  If this is a LEGACY non-WSI opinion display (intentional), add exemption:')
  console.error('    Option A — inline: ... // @canonical-allow-100 <reason>')
  console.error('    Option B — JSX prev line: {/* @canonical-allow-100 <reason> */}')
  for (const v of violations) {
    console.error(`  ${v.file}:${v.line} → ${v.text}`)
  }
  console.error('  Fix: use format="wsi" (renders X.X/10) or add exemption marker.')
  process.exit(1)
}
