#!/usr/bin/env node
/**
 * Sensor harness: bana citações de concorrentes + marketing copy hardcoded
 * em componentes React e em messages/*.json.
 *
 * Contexto (registrado 2026-05-26):
 * Página Gêmeos Digitais shippou em produção citando "Eightfold Andromeda" +
 * "DIFERENCIAL WEDOTALENT" + "Unico no mercado HR-tech" + "globalmente" +
 * "built-in" — risco legal + viola "Quiet Operator" (DESIGN.md).
 *
 * Padrão canonical: produto operacional NÃO menciona competidores. Material
 * de venda/marketing vive em site institucional separado (wedotalent.cc),
 * NÃO em components UI/CRUD.
 *
 * Allowlist: comentário `// COMPETITOR-MENTION-ALLOW: <reason>` na linha
 * imediatamente acima (para casos legítimos como referência factual a um
 * pattern compliance — ex: NYC LL144 HireVue/Eightfold pattern em fairness
 * docs internos).
 *
 * Modo atual: warn-only (baseline 0 pós-fix 2026-05-26).
 * Promover para BLOCKING quando estabilizar 7 dias.
 */
import { readFileSync, readdirSync, statSync } from "node:fs"
import { join, relative } from "node:path"
import { fileURLToPath } from "node:url"

const ROOT = join(fileURLToPath(import.meta.url), "..", "..")

const TARGETS = [
  { dir: "src/components", exts: [".tsx", ".ts"] },
  { dir: "messages", exts: [".json"] },
]

// Competitor names that have NEVER been factually integrated and that previously
// appeared only in marketing copy comparisons. Keep strict (any mention = violation
// unless explicitly allowlisted).
const COMPETITOR_NAMES_STRICT = [
  "Andromeda", // Eightfold product line — only ever appeared in marketing copy
]

// Marketing-copy claims that don't belong in product UI
const MARKETING_CLAIMS = [
  "DIFERENCIAL WEDOTALENT",
  "Unico no mercado",
  "Único no mercado",
  "Clone o raciocinio do seu melhor entrevistador",
  "Clone o raciocínio do seu melhor entrevistador",
  "pacote diferenciador unico",
  "diferenciador único",
]

// Competitor names that DO have legitimate factual uses (integration partners,
// compliance benchmark references). Only flag when context looks like marketing
// (adjacent to "Diferente do", "vs", "concorrente", "competitor", "Unlike").
const COMPETITOR_NAMES_CONTEXTUAL = [
  "Eightfold",
  "Workday",
  "Greenhouse",
  "Lever",
  "Gupy",
  "Kenoby",
  "SmartRecruiters",
]

// Marketing context = explicit comparison/disparagement language.
// Excludes pure positioning ("líder no mercado") which is factual.
const MARKETING_CONTEXT = /\b(Diferente do|Diferentemente|Unlike|vs\.|concorrente|competitor|melhor que|superior a|único no mercado|unico no mercado|globalmente)\b/i

// Allowlist marker (must be on the line immediately above OR on same line)
const ALLOW_MARKER = /COMPETITOR-MENTION-ALLOW:/

function walk(dir, exts, out = []) {
  let entries
  try {
    entries = readdirSync(dir)
  } catch {
    return out
  }
  for (const name of entries) {
    if (name === "node_modules" || name === ".next" || name === "__tests__")
      continue
    const full = join(dir, name)
    let st
    try {
      st = statSync(full)
    } catch {
      continue
    }
    if (st.isDirectory()) {
      walk(full, exts, out)
    } else if (exts.some((e) => name.endsWith(e))) {
      out.push(full)
    }
  }
  return out
}

const violations = []
const strictTerms = [...COMPETITOR_NAMES_STRICT, ...MARKETING_CLAIMS]

function checkLine(file, lineIdx, line, lines) {
  // Allowlist marker on line itself or line above
  if (ALLOW_MARKER.test(line)) return
  if (lineIdx > 0 && ALLOW_MARKER.test(lines[lineIdx - 1])) return

  const stripped = line.trim()
  // Skip code comments documenting REMOVAL of these strings (the rewrite history).
  // Check current line + 2 lines above for "REMOV" keyword in a comment block.
  if (stripped.startsWith("//") || stripped.startsWith("*")) {
    const commentBlock =
      (lines[lineIdx - 2] || "") + "\n" + (lines[lineIdx - 1] || "") + "\n" + line
    if (/REMOV|EXEMPT|NÃO usar|deprecat|legacy|NEVER appeared/i.test(commentBlock)) {
      return
    }
  }

  // STRICT terms: any occurrence is a violation
  for (const term of strictTerms) {
    const re = new RegExp(
      term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
      "i"
    )
    if (re.test(line)) {
      violations.push({
        file: relative(ROOT, file),
        line: lineIdx + 1,
        term,
        text: line.trim().slice(0, 120),
        severity: "strict",
      })
    }
  }

  // CONTEXTUAL terms: violation only when accompanied by marketing context
  for (const term of COMPETITOR_NAMES_CONTEXTUAL) {
    const re = new RegExp(
      `\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
      "i"
    )
    if (!re.test(line)) continue
    // Check current line + neighboring lines for marketing context
    const neighborhood =
      (lines[lineIdx - 1] || "") + "\n" + line + "\n" + (lines[lineIdx + 1] || "")
    if (MARKETING_CONTEXT.test(neighborhood)) {
      violations.push({
        file: relative(ROOT, file),
        line: lineIdx + 1,
        term,
        text: line.trim().slice(0, 120),
        severity: "contextual",
      })
    }
  }
}

for (const { dir, exts } of TARGETS) {
  const abs = join(ROOT, dir)
  const files = walk(abs, exts)
  for (const file of files) {
    if (file.endsWith("check_no_competitor_mentions.mjs")) continue
    let content
    try {
      content = readFileSync(file, "utf8")
    } catch {
      continue
    }
    const lines = content.split("\n")
    for (let i = 0; i < lines.length; i++) {
      checkLine(file, i, lines[i], lines)
    }
  }
}

const BLOCKING = process.argv.includes("--blocking")

if (violations.length === 0) {
  console.log(
    `[no-competitor-mentions] OK: 0 violations across ${TARGETS.length} target trees`
  )
  process.exit(0)
}

console.log(
  `[no-competitor-mentions] ${violations.length} violation(s) found:\n`
)
for (const v of violations) {
  console.log(`  [${v.file}:${v.line}] term="${v.term}"`)
  console.log(`    → ${v.text}`)
  console.log(
    `    → Fix: remova citação. Se for referência factual legítima (compliance pattern), adicione na linha acima: // COMPETITOR-MENTION-ALLOW: <motivo>`
  )
}

if (BLOCKING) {
  console.log("\nModo: BLOCKING (exit 1)")
  process.exit(1)
} else {
  console.log("\nModo: WARN-ONLY (use --blocking para CI gate)")
  process.exit(0)
}
