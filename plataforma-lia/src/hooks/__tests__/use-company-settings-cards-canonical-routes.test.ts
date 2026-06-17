/**
 * T3 (#990) — Canonical route sentinel for `useCompanySettingsCards.saveField`.
 *
 * This is a SOURCE-LEVEL sentinel (grep-style) modelled on the T-F pattern
 * used in `lia-agent-system/tests/integration/agents/test_non_react_tenant_helper_t_f.py`.
 * It guards against silent regressions of the "persistencia fantasma" bug
 * (cards salvando em paths errados) by reading the saveField source and
 * asserting each block dispatcher uses the canonical backend route.
 *
 * If a future PR moves a block to the wrong endpoint (e.g. workforce →
 * additional_data again, or tech_stack → culture-profile) this test fails
 * BEFORE the wrong path reaches production.
 *
 * Why source-grep instead of unit invocation: saveField lives inside a
 * useCallback in a hook and exercising it requires a full React render
 * tree with chat-context + watchdog mocks. A grep sentinel is faster, more
 * deterministic, and explicit about the invariants we care about.
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "node:fs"
import path from "node:path"

const SRC = readFileSync(
  path.resolve(__dirname, "../settings/use-company-settings-cards.ts"),
  "utf8",
)

describe("useCompanySettingsCards.saveField — canonical route sentinel (T3 #990)", () => {
  it("basic block writes to /company/profile/{id} via PUT", () => {
    expect(SRC).toMatch(/saveBasicField[\s\S]*?\/api\/backend-proxy\/company\/profile\/\$\{companyId\}/)
    expect(SRC).toMatch(/saveBasicField[\s\S]*?method:\s*"PUT"/)
  })

  it("culture and tech-profile fields write to /company/culture-profile/{id} via PUT", () => {
    expect(SRC).toMatch(
      /saveCultureOrTechProfileField[\s\S]*?\/api\/backend-proxy\/company\/culture-profile\/\$\{encodeURIComponent\(companyId\)\}/,
    )
  })

  it("tech_stack writes to /skills-catalog/company/skills-catalog/sync via POST", () => {
    expect(SRC).toMatch(
      /saveTechStackField[\s\S]*?\/api\/backend-proxy\/skills-catalog\/company\/skills-catalog\/sync/,
    )
    expect(SRC).toMatch(/saveTechStackField[\s\S]*?method:\s*"POST"/)
  })

  it("policy block writes to /hiring-policy/block via PATCH (proxy-translates to canonical)", () => {
    expect(SRC).toMatch(/savePolicyField[\s\S]*?\/api\/backend-proxy\/hiring-policy\/block/)
    expect(SRC).toMatch(/savePolicyField[\s\S]*?method:\s*"PATCH"/)
  })

  it("workforce field-list throws clear error (canonical write goes through WorkforceHubContent)", () => {
    expect(SRC).toMatch(
      /block === "workforce"[\s\S]*?throw new Error\(\s*"Edite o planejamento de workforce/,
    )
  })

  it("benefits field-list throws clear error pointing to BenefitsListSection", () => {
    expect(SRC).toMatch(
      /block === "benefits"[\s\S]*?throw new Error\(\s*"Use a lista de benef[ií]cios/,
    )
  })

  it("documents block writes to /company/profile/{id} additional_data (intentional — onboarding metadata)", () => {
    expect(SRC).toMatch(
      /saveDocumentsField[\s\S]*?\/api\/backend-proxy\/company\/profile\/\$\{companyId\}/,
    )
    expect(SRC).toMatch(/saveDocumentsField[\s\S]*?additional_data:\s*nextAdditional/)
  })

  it("origin guard for lia:settings-updated listener prevents double-fetch (loading dedup)", () => {
    expect(SRC).toMatch(/lastSelfDispatchRef/)
    expect(SRC).toMatch(/detail\?\.source === "ui"[\s\S]*?Date\.now\(\) - lastSelfDispatchRef\.current/)
  })

  it("headquarters parsing is robust against cities with embedded commas", () => {
    expect(SRC).toMatch(/lastIndexOf\(","\)/)
  })

  it("anti-pattern: workforce block must NOT silently write to additional_data", () => {
    // Workforce should never reach saveDocumentsField. The only legal place
    // a workforce-tagged additional_data write may appear is *outside* the
    // workforce branch. Assert there is no `block === "workforce"` followed
    // by a fetch to /company/profile.
    const workforceBranch = SRC.match(/block === "workforce"[\s\S]{0,400}/)?.[0] || ""
    expect(workforceBranch).not.toMatch(/\/api\/backend-proxy\/company\/profile/)
  })
})
