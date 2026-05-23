/**
 * Tests — ProfileEducationSection canonical building block.
 * Covers: empty state, multiple entries, missing-field tolerance.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { ProfileEducationSection } from "../ProfileEducationSection"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("ProfileEducationSection", () => {
  it("renders empty state with italic notProvided text when education empty", () => {
    render(<ProfileEducationSection education={[]} />)
    expect(screen.getByText("notProvided")).toBeInTheDocument()
  })

  it("renders entry with degree + field_of_study + institution", () => {
    render(
      <ProfileEducationSection
        education={[{ degree: "Bacharel", field_of_study: "Engenharia", institution: "USP", start_date: "2010", end_date: "2014" }]}
      />
    )
    expect(screen.getByText(/Bacharel/)).toBeInTheDocument()
    expect(screen.getByText("USP")).toBeInTheDocument()
    expect(screen.getByText(/2010/)).toBeInTheDocument()
    expect(screen.getByText(/2014/)).toBeInTheDocument()
  })

  it("renders multiple entries", () => {
    render(
      <ProfileEducationSection
        education={[
          { degree: "Bacharel", institution: "USP" },
          { degree: "Mestrado", institution: "Unicamp" },
        ]}
      />
    )
    expect(screen.getByText(/Bacharel/)).toBeInTheDocument()
    expect(screen.getByText(/Mestrado/)).toBeInTheDocument()
    expect(screen.getByText("USP")).toBeInTheDocument()
    expect(screen.getByText("Unicamp")).toBeInTheDocument()
  })

  it("falls back to i18n keys when entry fields missing", () => {
    render(<ProfileEducationSection education={[{}]} />)
    expect(screen.getByText("educationDegreeDefault")).toBeInTheDocument()
    expect(screen.getByText("institutionNotProvided")).toBeInTheDocument()
  })

  it("supports camelCase aliases (startDate/endDate)", () => {
    render(<ProfileEducationSection education={[{ degree: "X", institution: "Y", startDate: "2020", endDate: "2024" }]} />)
    expect(screen.getByText(/2020/)).toBeInTheDocument()
    expect(screen.getByText(/2024/)).toBeInTheDocument()
  })
})
