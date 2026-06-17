/**
 * Sensor: no synthetic /jobs/<id> URLs across the codebase.
 *
 * Post-mortem 2026-04-29 wizard-domain-hint-leak:
 *   The /jobs/<id> Next.js route was deleted on commit f7627f1bf without
 *   updating producers. Multiple callsites (useJobsPageCore.ts:270,
 *   useJobsModalHandlers.ts:238, use-lists-tab.ts:236, wizard-plan-card.ts:172)
 *   each synthesized URLs independently, all of them landing on 404.
 *
 *   Fix routed all callsites through `navigateToJobDetail` /
 *   `navigateToNewJobFromCandidates` helpers in `lib/navigation/job-navigation.ts`.
 *   This sensor prevents regression: any new `router.push('/jobs/...')` or
 *   `window.location.href = '/jobs/...'` outside the canonical helper
 *   triggers a test failure with a "use the helper" message.
 *
 * Guards:
 *   1. No `router.push('/jobs/...')` outside the helper file.
 *   2. No `window.location.href = '/jobs/...'` outside the helper file.
 *   3. The helper file exists at the canonical path.
 *
 * Fix se falhar:
 *   Substituir o `router.push(...)` ou `window.location.href = ...` por
 *   uma chamada ao helper canônico:
 *     import { navigateToJobDetail } from "@/lib/navigation/job-navigation"
 *     navigateToJobDetail(router, jobId, jobTitle)
 *   Quando product decidir o destino canônico, atualize APENAS o helper.
 *
 * Skill canônica: harness-engineering [sensor computacional] +
 *                 canonical-fix (single navigation source).
 */
import { execSync } from "node:child_process"
import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const REPO_ROOT = (() => {
  // Walk up to find the repo root (where package.json with "name" lives).
  let dir = __dirname
  while (dir !== "/") {
    if (existsSync(join(dir, "package.json"))) {
      try {
        const pkg = JSON.parse(readFileSync(join(dir, "package.json"), "utf-8"))
        if (pkg.name) return dir
      } catch {
        // ignore
      }
    }
    dir = join(dir, "..")
  }
  throw new Error("Could not locate repo root from " + __dirname)
})()

const HELPER_PATH = join(
  REPO_ROOT,
  "src/lib/navigation/job-navigation.ts",
)

function ripgrep(pattern: string, opts: { excludeFile?: string } = {}): string[] {
  // Use ripgrep if available (vitest envs usually have it), fall back to grep.
  const tool = (() => {
    try {
      execSync("which rg", { stdio: "ignore" })
      return "rg"
    } catch {
      return "grep"
    }
  })()

  const target = join(REPO_ROOT, "src")
  let cmd: string
  if (tool === "rg") {
    const exclude = opts.excludeFile
      ? ` --glob '!${opts.excludeFile}' --glob '!**/__tests__/**' --glob '!**/*.test.ts'`
      : " --glob '!**/__tests__/**' --glob '!**/*.test.ts'"
    cmd = `rg --no-heading -n "${pattern}" ${target}${exclude} || true`
  } else {
    const exclude = opts.excludeFile
      ? ` | grep -v '${opts.excludeFile}'`
      : ""
    cmd = (
      `grep -rn "${pattern}" ${target} ` +
      `--include="*.ts" --include="*.tsx" 2>/dev/null` +
      ` | grep -v "/__tests__/" | grep -v ".test.ts"` +
      exclude
    )
  }
  try {
    const out = execSync(cmd, { encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] })
    return out.split("\n").filter((line) => line.trim() !== "")
  } catch {
    return []
  }
}

describe("Sensor: canonical job navigation (post-mortem 2026-04-29)", () => {
  test("Guard 1: helper exists at canonical path", () => {
    expect(existsSync(HELPER_PATH)).toBe(true)
  })

  test("Guard 2: no router.push to /jobs outside the helper", () => {
    const hits = ripgrep(
      'router\\.push\\(.*[\'"\\\\`]/jobs',
      { excludeFile: "job-navigation.ts" },
    )
    expect(
      hits,
      "Found `router.push('/jobs/...')` outside the canonical helper. " +
        "Use `navigateToJobDetail(router, jobId, ...)` from " +
        "`@/lib/navigation/job-navigation` instead. Hits:\n" +
        hits.join("\n"),
    ).toEqual([])
  })

  test("Guard 3: no window.location.href to /jobs outside the helper", () => {
    const hits = ripgrep(
      'window\\.location\\.href.*=.*[\'"\\\\`]/jobs',
      { excludeFile: "job-navigation.ts" },
    )
    expect(
      hits,
      "Found `window.location.href = '/jobs/...'` outside the canonical helper. " +
        "Use `navigateToJobDetail` or `navigateToNewJobFromCandidates` from " +
        "`@/lib/navigation/job-navigation` instead. Hits:\n" +
        hits.join("\n"),
    ).toEqual([])
  })
})
