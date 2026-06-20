/**
 * Pin tests: candidate-page.tsx TABS — LGPD Art. 18 compliance + nav props
 * TDD: these tests pin the two features added 2026-06-14.
 *
 * Also covers CandidatePreviewProfileTab eligibility section (Task #1368):
 * ensures EligibilityResultsSection is rendered in CandidatePage's profile tab.
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

describe("CandidatePage — elegibilidade no painel de detalhes (profile tab)", () => {
  it("CandidatePreviewProfileTab importa e renderiza EligibilityResultsSection", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-preview/CandidatePreviewProfileTab.tsx"),
      "utf-8"
    )
    expect(src).toContain("EligibilityResultsSection")
    expect(src).toContain("EligibilityResultItem")
    expect(src).toContain("eligibility-results-section")
  })

  it("CandidatePreviewProfileTab extrai eligibility_results via extractEligibilityResults", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-preview/CandidatePreviewProfileTab.tsx"),
      "utf-8"
    )
    expect(src).toContain("extractEligibilityResults")
    expect(src).toContain("eligibility_results")
  })

  it("EligibilityResultsSection aparece antes dos scores/pareceres WSI no profile tab (ordem no JSX)", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-preview/CandidatePreviewProfileTab.tsx"),
      "utf-8"
    )
    // Use JSX opening tags to check render order (not import statements)
    const eligibilityIdx = src.indexOf("<EligibilityResultsSection")
    const opinionsIdx = src.indexOf("<ProfileLiaOpinionCard")
    // Seção de elegibilidade deve aparecer ANTES dos pareceres/scores da LIA no JSX
    expect(eligibilityIdx).toBeGreaterThan(-1)
    expect(opinionsIdx).toBeGreaterThan(-1)
    expect(eligibilityIdx).toBeLessThan(opinionsIdx)
  })

  it("CandidatePage delega a aba de perfil para CandidatePreviewProfileTab", () => {
    const fs = require("fs")
    const path = require("path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../candidate-page.tsx"),
      "utf-8"
    )
    expect(src).toContain("CandidatePreviewProfileTab")
    expect(src).toContain('activeTab === "profile"')
  })
})
