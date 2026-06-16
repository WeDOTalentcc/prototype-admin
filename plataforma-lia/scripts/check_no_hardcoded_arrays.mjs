#!/usr/bin/env node
/**
 * check_no_hardcoded_arrays.mjs  (F6 canonical sensor)
 * Detecta arrays literais com objetos {name, type, size} ou {user, timestamp}
 * hardcoded em candidate-* components (exceto testes).
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]

// Pattern: array literal [...] with objects containing file-like or activity-like shapes
// Matches e.g.: [{ name: "...", type: "...", size: ... }] or [{ user: "...", timestamp: "..." }]
const FILE_OBJ = /\[\s*\{[^}]*\bname\s*:[^}]*\btype\s*:[^}]*\bsize\s*:/s
const ACTIVITY_OBJ = /\[\s*\{[^}]*\buser\s*:[^}]*\btimestamp\s*:/s

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
      const content = readFileSync(full, "utf8")
      if (FILE_OBJ.test(content) || ACTIVITY_OBJ.test(content)) {
        violations.push(full)
      }
    }
  }
}

for (const dir of SEARCH_DIRS) walkDir(dir)

if (violations.length === 0) {
  console.log("check_no_hardcoded_arrays: 0 violations")
  process.exit(0)
} else {
  console.error("check_no_hardcoded_arrays: " + violations.length + " violation(s) — remove hardcoded object arrays:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: substituir arrays hardcoded por dados reais do backend via hooks.")
  process.exit(1)
}
