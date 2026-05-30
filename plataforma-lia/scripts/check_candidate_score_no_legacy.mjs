#!/usr/bin/env node
/**
 * check_candidate_score_no_legacy.mjs
 * Sensor F1 canonical: detecta padrão "/100" em arquivos candidate-* (exceto comentários e testes).
 * Exit 1 se encontrar. Exit 0 se limpo.
 * 
 * Uso: node scripts/check_candidate_score_no_legacy.mjs
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join, extname } from "path"

const SEARCH_DIR = "src/components/candidate-profile"
const PATTERN = /\/100/
const COMMENT_LINE = /^\s*(\/\/|\/\*|\*)/

let violations = []

function walkDir(dir) {
  const entries = readdirSync(dir)
  for (const entry of entries) {
    const fullPath = join(dir, entry)
    const stat = statSync(fullPath)
    if (stat.isDirectory()) {
      // Skip test directories
      if (entry === "__tests__" || entry === "node_modules") continue
      walkDir(fullPath)
    } else if (stat.isFile()) {
      const ext = extname(entry)
      if (![".ts", ".tsx"].includes(ext)) continue
      // Skip test files
      if (entry.endsWith(".test.tsx") || entry.endsWith(".test.ts")) continue
      
      const content = readFileSync(fullPath, "utf-8")
      const lines = content.split("\n")
      lines.forEach((line, idx) => {
        if (COMMENT_LINE.test(line)) return // skip comment lines
        if (PATTERN.test(line)) {
          violations.push({ file: fullPath, line: idx + 1, text: line.trim() })
        }
      })
    }
  }
}

try {
  walkDir(SEARCH_DIR)
} catch (e) {
  console.error("Error scanning directory:", e.message)
  process.exit(2)
}

if (violations.length === 0) {
  console.log("✓ check_candidate_score_no_legacy: 0 violations — no /100 pattern found in candidate-* components")
  process.exit(0)
} else {
  console.error(`✗ check_candidate_score_no_legacy: ${violations.length} violation(s) found!`)
  console.error('  Pattern "/100" is FORBIDDEN in candidate-profile components (use 0-10 WSI scale).')
  for (const v of violations) {
    console.error(`  ${v.file}:${v.line} → ${v.text}`)
  }
  console.error('  Fix: use format="wsi" (renders X.X/10) or format="decimal". Never /100.')
  process.exit(1)
}
