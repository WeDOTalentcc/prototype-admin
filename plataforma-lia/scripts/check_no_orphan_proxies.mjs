#!/usr/bin/env node
/**
 * check_no_orphan_proxies.mjs  (F6 canonical sensor)
 * Detecta fetch de /api/backend-proxy/data_files em candidate-* components.
 * Esse endpoint foi depreciado em favor do canonical files endpoint.
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]
const ORPHAN_PATTERN = /backend-proxy\/data_files/
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
        if (ORPHAN_PATTERN.test(line)) {
          violations.push(full + ":" + (i + 1) + ": " + line.trim())
        }
      })
    }
  }
}

for (const dir of SEARCH_DIRS) walkDir(dir)

if (violations.length === 0) {
  console.log("check_no_orphan_proxies: 0 violations")
  process.exit(0)
} else {
  console.error("check_no_orphan_proxies: " + violations.length + " violation(s) — remove orphan data_files proxy calls:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: usar /api/backend-proxy/candidates/{id}/files (canonical)")
  process.exit(1)
}
