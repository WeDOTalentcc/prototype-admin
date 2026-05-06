#!/usr/bin/env ts-node
/**
 * AST sensor — every lifecycle stage must have a branch in getVacancyAction.
 *
 * Background: pipeline-overview-page.tsx defines a discriminated union
 * `VacancyAction` and a switch statement `getVacancyAction(stageKey, t)`
 * that maps each stage to the appropriate action. The TypeScript
 * `assertNeverAction` already protects against missing `kind` branches —
 * but a developer adding a new lifecycle stage in the BACKEND
 * (analytics.py:JOB_LIFECYCLE_ORDER) won't get a TypeScript error from
 * the frontend; the new stage just falls through to the default branch
 * silently.
 *
 * This sensor compares:
 *   - The stages registered in the BACKEND classifier
 *     (lia-agent-system/app/api/v1/job_vacancies/analytics.py:JOB_LIFECYCLE_ORDER)
 *   - The case branches in the FRONTEND switch
 *     (plataforma-lia/src/components/pages/pipeline-overview-page.tsx)
 *
 * Fails if backend has a stage not handled by frontend (or vice versa).
 *
 * Run: npx tsx scripts/check-vacancy-action-coverage.ts
 */
import { readFileSync, existsSync } from "node:fs"
import { resolve } from "node:path"

const ROOT = resolve(__dirname, "..", "..")
const BACKEND = resolve(ROOT, "lia-agent-system", "app", "api", "v1", "job_vacancies", "analytics.py")
const FRONTEND = resolve(
  ROOT,
  "plataforma-lia",
  "src",
  "components",
  "pages",
  "pipeline-overview-page.tsx",
)

if (!existsSync(BACKEND)) {
  console.error(`FAIL — backend file not found: ${BACKEND}`)
  process.exit(1)
}
if (!existsSync(FRONTEND)) {
  console.error(`FAIL — frontend file not found: ${FRONTEND}`)
  process.exit(1)
}

const backendSrc = readFileSync(BACKEND, "utf-8")
const frontendSrc = readFileSync(FRONTEND, "utf-8")

// Extract JOB_LIFECYCLE_ORDER list members.
const orderMatch = backendSrc.match(/JOB_LIFECYCLE_ORDER\s*=\s*\[([\s\S]*?)\]/)
if (!orderMatch) {
  console.error("FAIL — could not find JOB_LIFECYCLE_ORDER in backend file")
  process.exit(1)
}
const backendStages = new Set(
  Array.from(orderMatch[1].matchAll(/"([^"]+)"/g)).map((m) => m[1]),
)

// Extract `case "<stage>":` from getVacancyAction switch.
const fnMatch = frontendSrc.match(/function getVacancyAction[\s\S]*?\n\}/m)
if (!fnMatch) {
  console.error("FAIL — could not find getVacancyAction in frontend file")
  process.exit(1)
}
const frontendCases = new Set(
  Array.from(fnMatch[0].matchAll(/case\s+"([^"]+)":/g)).map((m) => m[1]),
)

console.log(`Backend stages (${backendStages.size}):`, [...backendStages].join(", "))
console.log(`Frontend case branches (${frontendCases.size}):`, [...frontendCases].join(", "))

const missingInFrontend = [...backendStages].filter((s) => !frontendCases.has(s))
const extraInFrontend = [...frontendCases].filter((s) => !backendStages.has(s))

let failed = false
if (missingInFrontend.length > 0) {
  console.error(
    "\nFAIL — Backend lifecycle stages NOT handled in getVacancyAction:",
  )
  for (const s of missingInFrontend) {
    console.error(`  ${s} — add a case branch with the right VacancyAction kind.`)
  }
  failed = true
}
if (extraInFrontend.length > 0) {
  console.error(
    "\nFAIL — Frontend case branches that don't match any backend stage:",
  )
  for (const s of extraInFrontend) {
    console.error(`  ${s} — remove the dead branch or add the stage to JOB_LIFECYCLE_ORDER.`)
  }
  failed = true
}

if (failed) {
  process.exit(1)
}
console.log("\nOK — all lifecycle stages have a frontend branch.")
process.exit(0)
