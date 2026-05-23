/**
 * Tests — ProfileExperienceSection canonical building block.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { ProfileExperienceSection } from "../ProfileExperienceSection"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) =>
    vars && vars.years ? key + " " + String(vars.years) : key,
}))

const fmt = (d: string | null | undefined) => d || ""

describe("ProfileExperienceSection", () => {
  it("renders empty state when experiences empty", () => {
    render(<ProfileExperienceSection experiences={[]} formatDateShort={fmt} />)
    expect(screen.getByText("notProvided")).toBeInTheDocument()
  })

  it("renders entry title + company + dates", () => {
    render(
      <ProfileExperienceSection
        experiences={[{ title: "Tech Lead", company: "Acme Co", start_date: "2020", end_date: "2024" }]}
        formatDateShort={fmt}
      />
    )
    expect(screen.getByText("Tech Lead")).toBeInTheDocument()
    expect(screen.getByText(/Acme Co/)).toBeInTheDocument()
    expect(screen.getByText(/2020/)).toBeInTheDocument()
  })

  it("renders current entry (is_current true)", () => {
    render(
      <ProfileExperienceSection
        experiences={[{ title: "Senior Dev", company: "X", start_date: "2022", is_current: true }]}
        formatDateShort={fmt}
      />
    )
    const found = screen.getAllByText((_, el) => Boolean(el && el.textContent && el.textContent.includes("current"))); expect(found.length).toBeGreaterThan(0)
  })

  it("renders technologies chip with limit 6", () => {
    render(
      <ProfileExperienceSection
        experiences={[{ title: "X", company: "Y", technologies: ["a", "b", "c", "d", "e", "f", "g", "h"] }]}
        formatDateShort={fmt}
      />
    )
    expect(screen.getByText("a")).toBeInTheDocument()
    expect(screen.getByText("f")).toBeInTheDocument()
    expect(screen.getByText("+2")).toBeInTheDocument()
  })

  it("renders startup chip when is_startup true", () => {
    render(
      <ProfileExperienceSection
        experiences={[{ title: "X", company: "Y", is_startup: true }]}
        formatDateShort={fmt}
      />
    )
    expect(screen.getByText(/Startup/i)).toBeInTheDocument()
  })

  it("renders industries (limit 2)", () => {
    render(
      <ProfileExperienceSection
        experiences={[{ title: "X", company: "Y", industries: ["Tech", "Finance", "Health"] }]}
        formatDateShort={fmt}
      />
    )
    expect(screen.getByText("Tech")).toBeInTheDocument()
    expect(screen.getByText("Finance")).toBeInTheDocument()
    expect(screen.queryByText("Health")).toBeNull()
  })

  it("renders fallback for missing title/company", () => {
    render(<ProfileExperienceSection experiences={[{}]} formatDateShort={fmt} />)
    expect(screen.getByText("positionNotProvided")).toBeInTheDocument()
    expect(screen.getByText(/companyNotProvided/)).toBeInTheDocument()
  })
})
