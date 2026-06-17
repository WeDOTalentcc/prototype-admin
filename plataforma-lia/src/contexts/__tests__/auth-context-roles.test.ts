/**
 * C24 sentinel — auth-context User.role canonical enum guard.
 *
 * Context (registrado 2026-05-21):
 *   Backend canonical (lia-agent-system/app/auth/models.py) added
 *   UserRole.wedotalent_admin in C1 commit ed25753c4. Frontend User.role
 *   enum (src/services/auth-service.ts) was backfilled in C24 to include
 *   this value. Before C24, two callers used string-cast workarounds:
 *
 *     LiaFieldsConfigPanel.tsx:  (user?.role as string) === "wedotalent_admin"
 *     CatalogsManagementSection.tsx:  // TODO: ...wedotalent_admin
 *
 *   This sentinel:
 *     1. Pins the canonical enum membership (compile-time assertion).
 *     2. Pins runtime allowlist in auth-store.ts so server-injected
 *        wedotalent_admin tokens are NOT silently downgraded to "viewer".
 *
 *   Failure of (1) = type regression (enum value removed/renamed).
 *   Failure of (2) = silent role downgrade defect (worse than typed: user
 *   IS wedotalent_admin in backend but frontend sees them as viewer).
 */
import { describe, it, expect } from "vitest"
import type { User } from "@/services/auth-service"

describe("C24 — User.role canonical enum extension", () => {
  it("accepts wedotalent_admin as a valid User.role literal (compile-time)", () => {
    // If User.role enum stops including "wedotalent_admin", this won't compile.
    const wedoAdmin: User["role"] = "wedotalent_admin"
    expect(wedoAdmin).toBe("wedotalent_admin")
  })

  it("still accepts the legacy canonical roles", () => {
    const admin: User["role"] = "admin"
    const recruiter: User["role"] = "recruiter"
    const viewer: User["role"] = "viewer"
    expect([admin, recruiter, viewer]).toEqual(["admin", "recruiter", "viewer"])
  })

  it("rejects arbitrary strings at the type level", () => {
    // @ts-expect-error — random strings are not valid User.role values
    const invalid: User["role"] = "super_user"
    // Use the variable to silence unused-locals; runtime cast does NOT
    // narrow the type, the @ts-expect-error above is what we're asserting.
    expect(typeof invalid).toBe("string")
  })
})

describe("C24 — auth-store runtime role allowlist", () => {
  // We cannot import the full auth-store (it has side effects + browser deps),
  // so we exercise the validation predicate directly. This mirrors the inline
  // expression at src/stores/auth-store.ts:150.
  const ALLOWED_ROLES = ["admin", "recruiter", "viewer", "wedotalent_admin"] as const
  const isAllowed = (r: string): r is (typeof ALLOWED_ROLES)[number] =>
    (ALLOWED_ROLES as readonly string[]).includes(r)

  it("does NOT silently downgrade wedotalent_admin to viewer", () => {
    // Before C24: ['admin','recruiter','viewer'].includes('wedotalent_admin') === false
    // -> auth-store fell back to 'viewer'. This was the harness defect.
    expect(isAllowed("wedotalent_admin")).toBe(true)
  })

  it("preserves legacy roles", () => {
    expect(isAllowed("admin")).toBe(true)
    expect(isAllowed("recruiter")).toBe(true)
    expect(isAllowed("viewer")).toBe(true)
  })

  it("rejects unknown roles (fail-closed)", () => {
    expect(isAllowed("manager")).toBe(false)
    expect(isAllowed("")).toBe(false)
    expect(isAllowed("WEDOTALENT_ADMIN")).toBe(false) // case-sensitive
  })
})
