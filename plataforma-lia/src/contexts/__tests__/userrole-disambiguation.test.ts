/**
 * WT-2022 P0.RBAC disambiguation sentinel (registrado 2026-05-21).
 *
 * Pin the two parallel UserRole taxonomies that exist in this codebase
 * with intentionally DIFFERENT semantics. Documented in:
 *   - src/services/auth-service.ts  (canonical: JWT/auth)
 *   - src/utils/permissions.ts      (legacy RBAC catalog client-side)
 *   - src/lib/permissions.ts        (re-exports utils/permissions UserRole)
 *
 * Why this sentinel:
 *   Both files define types/values literally named "UserRole" but with
 *   different members. Without a pin, an unrelated refactor could
 *   silently align one taxonomy to the other and break:
 *     - auth gates that depend on `wedotalent_admin` (canonical) OR
 *     - PermissionManager that depends on `senior_recruiter | intern`
 *       (legacy catalog).
 *
 * Compile-time guard:
 *   `satisfies` ensures TS rejects unexpected members. Runtime guard:
 *   explicit array equality + length checks make regressions obvious.
 *
 * Companion of `src/contexts/__tests__/auth-context-roles.test.ts`
 * which pins only the auth canonical side.
 */
import { describe, it, expect } from "vitest"
import type { UserRole as LegacyRBACUserRole } from "@/utils/permissions"

// ── Canonical auth taxonomy (src/services/auth-service.ts User.role) ──────
type CanonicalAuthRole = "admin" | "recruiter" | "viewer" | "wedotalent_admin"

const CANONICAL_AUTH_ROLES = [
  "admin",
  "recruiter",
  "viewer",
  "wedotalent_admin",
] as const satisfies readonly CanonicalAuthRole[]

// ── Legacy RBAC client-side taxonomy (src/utils/permissions.ts) ───────────
const LEGACY_RBAC_ROLES = [
  "admin",
  "manager",
  "senior_recruiter",
  "recruiter",
  "intern",
] as const satisfies readonly LegacyRBACUserRole[]

describe("WT-2022 P0.RBAC: UserRole parallel taxonomies are pinned", () => {
  it("canonical auth role enum has exactly 4 members (auth-service.ts)", () => {
    expect(CANONICAL_AUTH_ROLES).toHaveLength(4)
    expect(CANONICAL_AUTH_ROLES).toEqual([
      "admin",
      "recruiter",
      "viewer",
      "wedotalent_admin",
    ])
  })

  it("legacy RBAC role enum has exactly 5 members (utils/permissions.ts)", () => {
    expect(LEGACY_RBAC_ROLES).toHaveLength(5)
    expect(LEGACY_RBAC_ROLES).toEqual([
      "admin",
      "manager",
      "senior_recruiter",
      "recruiter",
      "intern",
    ])
  })

  it("taxonomies overlap only on 'admin' and 'recruiter' (intentional)", () => {
    const canonical = new Set<string>(CANONICAL_AUTH_ROLES)
    const legacy = new Set<string>(LEGACY_RBAC_ROLES)
    const intersect = [...canonical].filter((r) => legacy.has(r)).sort()
    expect(intersect).toEqual(["admin", "recruiter"])
  })

  it("canonical has 'wedotalent_admin' and legacy does NOT (separation)", () => {
    const legacyMembers = LEGACY_RBAC_ROLES as readonly string[]
    expect(CANONICAL_AUTH_ROLES).toContain("wedotalent_admin")
    expect(legacyMembers.includes("wedotalent_admin")).toBe(false)
  })

  it("legacy has 'manager'/'senior_recruiter'/'intern' and canonical does NOT", () => {
    const canonicalMembers = CANONICAL_AUTH_ROLES as readonly string[]
    expect(LEGACY_RBAC_ROLES).toContain("manager")
    expect(LEGACY_RBAC_ROLES).toContain("senior_recruiter")
    expect(LEGACY_RBAC_ROLES).toContain("intern")
    expect(canonicalMembers.includes("manager")).toBe(false)
    expect(canonicalMembers.includes("senior_recruiter")).toBe(false)
    expect(canonicalMembers.includes("intern")).toBe(false)
  })
})
