#!/usr/bin/env node
/**
 * check_no_fake_ai_analysis.mjs  (F6 canonical sensor)
 * Detecta objetos literais de analise AI fake em candidate-* components (exceto testes).
 * Padrao: presenca de 3+ campos {confidence, communication, clarity, enthusiasm} como literal.
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]
const FAKE_AI_KEYS = ["confidence", "communication", "clarity", "enthusiasm"]
const violations = []

function hasFakeAiBlock(content) {
  let count = 0
  for (const key of FAKE_AI_KEYS) {
    // Simple check: key followed by colon as object property literal
    if (content.includes(key + ":") || content.includes('"' + key + '"' + ":") || content.includes("'" + key + "'" + ":")) {
      count++
    }
  }
  return count >= 3
}

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
      const content = readFileSync(full, "utf8")
      if (hasFakeAiBlock(content)) {
        violations.push(full)
      }
    }
  }
}

for (const dir of SEARCH_DIRS) walkDir(dir)

if (violations.length === 0) {
  console.log("check_no_fake_ai_analysis: 0 violations")
  process.exit(0)
} else {
  console.error("check_no_fake_ai_analysis: " + violations.length + " violation(s) — remove fake AI analysis literals:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: substituir objetos fake por dados reais do endpoint /lia/profile-analysis/candidate/{id}")
  process.exit(1)
}
