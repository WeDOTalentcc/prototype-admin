#!/usr/bin/env node
/**
 * check_chip_overrides.mjs
 *
 * Sensor (lint custom) que detecta overrides anti-canonical em <Chip>.
 *
 * Auditoria 2026-05-22 (relatório /tmp/badges-audit-2026-05-22.md) identificou
 * 5 buckets de violação. Buckets A/C/E + DS density="relaxed" + codemod B
 * fecharam ~157 sites. Este sensor PREVINE regressão.
 *
 * Regras (todas com mensagem otimizada pra LLM consumer em PT-BR):
 *
 *   chip-cta-bg               (error)   Bucket A — bg-(lia-btn-primary|black)
 *   chip-padding-excess       (error)   Bucket C — px-[3-9]
 *   chip-text-size-override   (error)   Override text-(sm|base|lg|xl)
 *   chip-text-xs-override     (warn)    Bucket B — text-xs (use density="relaxed")
 *   chip-font-weight-override (warn)    Bucket E — font-(bold|semibold)
 *
 * Uso:
 *   node scripts/check_chip_overrides.mjs              # Print all violations + exit code
 *   node scripts/check_chip_overrides.mjs --baseline   # Show baseline summary
 *   node scripts/check_chip_overrides.mjs --files <list>  # Check specific files (lint-staged)
 *
 * Exit codes:
 *   0  No errors (warns OK)
 *   1  At least one error found
 *
 * Integration:
 *   - Adicionado em "scripts" do package.json como "lint:chips"
 *   - Adicionado em lint-staged pra src/**\/*.{ts,tsx}
 *   - Pode ser elevado para CI blocking no GitHub Actions futuro
 */

import { readdirSync, readFileSync, statSync } from "node:fs"
import { resolve, join, relative } from "node:path"

const SRC_ROOT = resolve(process.cwd(), "src")

const RULES = [
  {
    id: "chip-cta-bg",
    severity: "error",
    pattern: /bg-(lia-btn-primary-bg|lia-btn-primary-hover|black)\b/,
    msg:
      "Chip com bg-lia-btn-primary-bg ou bg-black vira CTA-pill (preto sólido). " +
      "Chips são para informar estado, não para CTA.\n" +
      'Fix: use variant="success" (verde), variant="info" (cyan), ou variant="neutral" muted.\n' +
      "Bucket A do audit 2026-05-22 — Commit 36cb22fa4 fechou os 17 sites originais.",
  },
  {
    id: "chip-text-size-override",
    severity: "error",
    pattern: /\btext-(sm|base|lg|xl|2xl)\b/,
    msg:
      "Chip não pode ter text-sm/base/lg/xl — quebra hierarquia tipográfica.\n" +
      'Fix: use density="comfortable" (10px), density="compact" (10px tight), ou density="relaxed" (12px).\n' +
      "Se realmente precisa de >12px, considere usar <h*> ou <p> em vez de <Chip>.",
  },
  {
    id: "chip-padding-excess",
    severity: "error",
    pattern: /\bpx-(?:[3-9]|1[0-9])\b/,
    msg:
      "Chip com px-3+ é grande demais — canonical é px-1.5 (comfortable) ou px-1 (compact).\n" +
      'Fix: remover override de padding. Se precisa de mais espaço, use density="relaxed".\n' +
      "Bucket C do audit 2026-05-22 — Commit 82e92d7dc fechou os 3 sites originais.",
  },
  {
    id: "chip-text-xs-override",
    severity: "warn",
    pattern: /\btext-xs\b/,
    msg:
      "Chip com text-xs (12px) em vez do canonical. Override do className não é a forma correta.\n" +
      'Fix: trocar className "...text-xs..." por atributo density="relaxed".\n' +
      "Bucket B do audit 2026-05-22 — Commit 65e65084e migrou 121 sites via codemod (44 multi-line restantes em backlog).",
  },
  {
    id: "chip-font-weight-override",
    severity: "warn",
    pattern: /\bfont-(bold|semibold)\b/,
    msg:
      "Chip com font-bold/semibold quebra hierarquia (canonical = font-medium do design system).\n" +
      "Fix: remover override. Se precisa de destaque, use o variant semântico apropriado (warning, danger, etc.).\n" +
      "Bucket E do audit 2026-05-22 — Commit 82e92d7dc fechou os 16 sites originais.",
  },
]

// Match Chip JSX tags (single-line) — captures attribute area
// Permitimos qualquer atributo, mas precisamos extrair só o conteúdo entre <Chip e > de uma JSX tag
// Para multi-line, processamos cada arquivo como string e usamos uma regex multi-line
const CHIP_TAG_RE = /<Chip\b([^>]*?)\/?>/gs

function isExcluded(filePath) {
  const rel = relative(SRC_ROOT, filePath)
  return (
    rel.startsWith("../") || // outside src
    rel.includes("node_modules/") ||
    rel.includes(".next/") ||
    rel.includes("__tests__/") ||
    rel.includes(".test.") ||
    rel.includes(".stories.")
  )
}

function* walk(dir) {
  let entries
  try {
    entries = readdirSync(dir, { withFileTypes: true })
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry.name.startsWith(".") || entry.name === "node_modules") continue
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      yield* walk(full)
    } else if (
      entry.isFile() &&
      (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts"))
    ) {
      yield full
    }
  }
}

function checkFile(filePath) {
  const violations = []
  let source
  try {
    source = readFileSync(filePath, "utf-8")
  } catch {
    return violations
  }
  // Compute line offsets for line number lookup
  const lineStarts = [0]
  for (let i = 0; i < source.length; i++) {
    if (source[i] === "\n") lineStarts.push(i + 1)
  }
  function lineOf(idx) {
    // Binary-search the line
    let lo = 0,
      hi = lineStarts.length - 1
    while (lo < hi) {
      const mid = ((lo + hi + 1) / 2) | 0
      if (lineStarts[mid] <= idx) lo = mid
      else hi = mid - 1
    }
    return lo + 1
  }

  // Find each <Chip ...> tag (single or multi-line)
  CHIP_TAG_RE.lastIndex = 0
  let m
  while ((m = CHIP_TAG_RE.exec(source))) {
    const attrs = m[1]
    const tagStart = m.index
    const line = lineOf(tagStart)
    // Skip if this Chip has a density attr already (codemod already handled / future-proof)
    // Note: text-xs WARN still fires even with density, since user shouldn't have both
    const hasDensity = /\bdensity\s*=/.test(attrs)
    for (const rule of RULES) {
      // text-xs warn skip if density is "relaxed" (canonical case)
      if (
        rule.id === "chip-text-xs-override" &&
        hasDensity &&
        /density\s*=\s*["']relaxed["']/.test(attrs)
      ) {
        // Override + density="relaxed" is redundant but harmless — skip warning
        continue
      }
      if (rule.pattern.test(attrs)) {
        violations.push({
          file: filePath,
          line,
          rule: rule.id,
          severity: rule.severity,
          msg: rule.msg,
          snippet: attrs.replace(/\s+/g, " ").trim().slice(0, 120),
        })
      }
    }
  }
  return violations
}

function format(violations) {
  const errors = violations.filter((v) => v.severity === "error")
  const warns = violations.filter((v) => v.severity === "warn")

  const RED = "\x1b[31m"
  const YELLOW = "\x1b[33m"
  const DIM = "\x1b[2m"
  const RESET = "\x1b[0m"

  for (const v of [...errors, ...warns]) {
    const icon = v.severity === "error" ? `${RED}✗${RESET}` : `${YELLOW}⚠${RESET}`
    const sev = v.severity === "error" ? `${RED}error${RESET}` : `${YELLOW}warn${RESET}`
    const rel = relative(process.cwd(), v.file)
    console.log(`${icon} ${rel}:${v.line}  [${v.rule}] ${sev}`)
    console.log(`  ${DIM}<Chip ${v.snippet}>${RESET}`)
    console.log(`  ${v.msg.split("\n").join("\n  ")}\n`)
  }

  console.log(`──`)
  console.log(`${errors.length} errors · ${warns.length} warnings · ${violations.length} total`)
  return errors.length
}

function summary(violations) {
  const byRule = new Map()
  for (const v of violations) {
    const key = `${v.severity}:${v.rule}`
    byRule.set(key, (byRule.get(key) || 0) + 1)
  }
  console.log("Baseline summary:")
  for (const [k, n] of [...byRule.entries()].sort()) {
    console.log(`  ${k}: ${n}`)
  }
}

// CLI
const args = process.argv.slice(2)
const isBaseline = args.includes("--baseline")
const noFail = args.includes("--no-fail")
const filesIdx = args.indexOf("--files")
const explicitFiles = filesIdx >= 0 ? args.slice(filesIdx + 1) : null

let files
if (explicitFiles) {
  files = explicitFiles.filter((f) => f.endsWith(".tsx") || f.endsWith(".ts"))
} else {
  files = []
  for (const f of walk(SRC_ROOT)) {
    if (!isExcluded(f)) files.push(f)
  }
}

const allViolations = []
for (const f of files) {
  allViolations.push(...checkFile(f))
}

if (isBaseline) {
  summary(allViolations)
  process.exit(0)
}

const errorCount = format(allViolations)
process.exit(errorCount > 0 && !noFail ? 1 : 0)
