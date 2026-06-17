#!/usr/bin/env node
/**
 * check_no_hardcoded_candidate_mocks.mjs  (F6 canonical sensor)
 * Detecta nomes fake de candidatos hardcoded em candidate-* components (exceto testes).
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]
const MOCK_NAMES = /Maria Oliveira|Carlos Mendes|Ana Silva|Roberto Silva/
const violations = []

function walkDir(dir) {
  let entries
  try { entries = readdirSync(dir) } catch { return }
  for (const entry of entries) {
    const full = join(dir, entry)
    const stat = statSync(full)
    if (stat.isDirectory()) {
      if (entry === "__tests__" || entry === "node_modules") continue
      walkDir(full)
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      const lines = readFileSync(full, "utf8").split("\n")
      lines.forEach((line, i) => {
        if (MOCK_NAMES.test(line)) {
          violations.push(`${full}:${i + 1}: ${line.trim()}`)
        }
      })
    }
  }
}

for (const dir of SEARCH_DIRS) walkDir(dir)

if (violations.length === 0) {
  console.log("check_no_hardcoded_candidate_mocks: 0 violations")
  process.exit(0)
} else {
  console.error("check_no_hardcoded_candidate_mocks: " + violations.length + " violation(s) — remove hardcoded fake names:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: substituir nomes hardcoded por dados reais do candidato via hook.")
  process.exit(1)
}
