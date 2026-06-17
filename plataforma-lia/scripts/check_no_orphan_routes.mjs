#!/usr/bin/env node
/**
 * check_no_orphan_routes.mjs  (F6 canonical sensor)
 * Detecta imports de 'funil-de-talentos/candidato/[id]/components/' em arquivos
 * fora dessa pasta (indica componentes que nao foram absorvidos corretamente em F3).
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join, resolve, dirname } from "path"

const ROOT_SRC = "src"
const ORPHAN_IMPORT = /funil-de-talentos\/candidato\/\[id\]\/components\//
const violations = []

function walkDir(dir) {
  let entries
  try { entries = readdirSync(dir) } catch { return }
  for (const entry of entries) {
    const full = join(dir, entry)
    const stat = statSync(full)
    if (stat.isDirectory()) {
      if (entry === "node_modules" || entry === ".next") continue
      walkDir(full)
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      // Skip the route folder itself
      if (full.includes("funil-de-talentos/candidato/")) continue
      const lines = readFileSync(full, "utf8").split("\n")
      lines.forEach((line, i) => {
        if (ORPHAN_IMPORT.test(line)) {
          violations.push(full + ":" + (i + 1) + ": " + line.trim())
        }
      })
    }
  }
}

walkDir(ROOT_SRC)

if (violations.length === 0) {
  console.log("check_no_orphan_routes: 0 violations")
  process.exit(0)
} else {
  console.error("check_no_orphan_routes: " + violations.length + " violation(s) — imports de componentes de rota obsoletos:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: mover logica para candidate-page/ ou candidate-profile/ building blocks.")
  process.exit(1)
}
