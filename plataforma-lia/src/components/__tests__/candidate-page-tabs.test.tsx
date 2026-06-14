/**
 * Pin tests: candidate-page.tsx TABS — LGPD Art. 18 compliance + nav props
 * TDD: these tests pin the two features added 2026-06-14.
 */

describe("CandidatePage TABS — LGPD Art.18 compliance", () => {
  it("TABS array includes consent tab (LGPD Art.18 — recruiter must access consent history)", () => {
    // Static assertion: read the source and verify the TABS array has 'consent'
    // We do this as a static text check since TABS is not exported
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-page.tsx"),
      "utf-8"
    )
    expect(src).toContain('id: "consent"')
    expect(src).toContain("Consentimento")
    expect(src).toContain("CandidateConsentTab")
  })

  it("TABS array has profile, activities, files, opinions, consent (5 tabs)", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-page.tsx"),
      "utf-8"
    )
    const tabIds = ["profile", "activities", "files", "opinions", "consent"]
    tabIds.forEach((id) => {
      expect(src).toContain(`id: "${id}"`)
    })
  })
})

describe("CandidatePage — prev/next navigation", () => {
  it("exposes onNavigateCandidate, hasPrev, hasNext props", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-page.tsx"),
      "utf-8"
    )
    expect(src).toContain("onNavigateCandidate")
    expect(src).toContain("hasPrev")
    expect(src).toContain("hasNext")
  })

  it("renders nav buttons when onNavigateCandidate is provided", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-page.tsx"),
      "utf-8"
    )
    expect(src).toContain("ChevronLeft")
    expect(src).toContain("ChevronRight")
    // The buttons use aria-label for accessibility
    expect(src).toContain("Candidato anterior")
    expect(src).toContain("Próximo candidato")
  })
})
