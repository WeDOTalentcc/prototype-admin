#!/usr/bin/env node
/**
 * check_company_id_from_jwt.mjs  (F6 canonical sensor)
 * Detecta 'company_id' no body de POST/PUT fetch em candidate-* components.
 * company_id deve vir do JWT (header Authorization), nunca do body.
 * Query params em GET sao aceitos (nao eh violacao de seguranca).
 * Exit 1 se encontrar. Exit 0 se limpo.
 */

import { readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

const SEARCH_DIRS = [
  "src/components/candidate-profile",
  "src/components/candidate-preview",
  "src/components/candidate-page",
]

// Detect: formData.append('company_id', ...) or body: JSON.stringify({... company_id ...})
// near a POST/PUT fetch call
const FORM_DATA_COMPANY = /formData\.append\(['"]company_id['"]/
const JSON_BODY_COMPANY = /JSON\.stringify\([^)]*company_id/s

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
      const lines = content.split("\n")
      // Check formData.append with company_id
      lines.forEach((line, i) => {
        if (FORM_DATA_COMPANY.test(line)) {
          violations.push(full + ":" + (i + 1) + " [formData] " + line.trim())
        }
      })
      // Check JSON.stringify body with company_id
      if (JSON_BODY_COMPANY.test(content)) {
        violations.push(full + ": company_id in JSON.stringify body (POST/PUT)")
      }
    }
  }
}

for (const dir of SEARCH_DIRS) walkDir(dir)

if (violations.length === 0) {
  console.log("check_company_id_from_jwt: 0 violations")
  process.exit(0)
} else {
  console.error("check_company_id_from_jwt: " + violations.length + " violation(s) — company_id nao deve ir no body de POST/PUT:")
  violations.forEach(v => console.error("  " + v))
  console.error("Fix: remover company_id do body — o backend le do JWT via Depends(require_company_id).")
  process.exit(1)
}
