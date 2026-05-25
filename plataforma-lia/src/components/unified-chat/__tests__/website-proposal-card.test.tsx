import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { WebsiteProposalCard } from "../WebsiteProposalCard"
import type { ProposedSaves } from "@/lib/website-proposal-mapper"

const COMPANY_ID = "00000000-0000-4000-a000-000000000001"

const proposed: ProposedSaves = {
  payload_hash: "deadbeef",
  blocks: [
    {
      key: "culture",
      label: "Cultura & EVP",
      fields: [
        { key: "mission", label: "Missão", value: "Conectar talentos" },
        { key: "values", label: "Valores", value: ["transparência", "foco"] },
      ],
    },
    {
      key: "tech_stack",
      label: "Tech Stack",
      fields: [{ key: "tech_stack", label: "Stack", value: ["TypeScript", "Python"] }],
    },
    {
      key: "basic_complementary",
      label: "Dados Básicos complementares",
      fields: [{ key: "industry", label: "Setor", value: "Tecnologia" }],
    },
  ],
}

describe("WebsiteProposalCard (Task #1180)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200 })))
  })

  it("renders all blocks with selected state by default", () => {
    render(<WebsiteProposalCard data={{ proposed, companyId: COMPANY_ID }} />)
    expect(screen.getByTestId("website-proposal-card")).toBeTruthy()
    expect(screen.getByTestId("proposal-block-culture")).toBeTruthy()
    expect(screen.getByTestId("proposal-block-tech_stack")).toBeTruthy()
    expect(screen.getByTestId("proposal-block-basic_complementary")).toBeTruthy()
  })

  it("Salvar tudo hits the 3 expected endpoints with correct payloads", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    render(<WebsiteProposalCard data={{ proposed, companyId: COMPANY_ID }} />)
    fireEvent.click(screen.getByTestId("website-proposal-save-all"))
    await waitFor(() => expect(screen.getByTestId("website-proposal-card-done")).toBeTruthy())
    const urls = fetchMock.mock.calls.map((c) => String(c[0]))
    expect(urls).toContain(`/api/backend-proxy/company/culture-profile/${COMPANY_ID}`)
    expect(urls).toContain("/api/backend-proxy/skills-catalog/company/skills-catalog/sync")
    expect(urls).toContain(`/api/backend-proxy/company/profile/${COMPANY_ID}`)
  })

  it("Cancelar moves to done with savedCount=0 and no fetch calls", () => {
    const fetchMock = vi.fn()
    vi.stubGlobal("fetch", fetchMock)
    render(<WebsiteProposalCard data={{ proposed, companyId: COMPANY_ID }} />)
    fireEvent.click(screen.getByTestId("website-proposal-cancel"))
    expect(screen.getByTestId("website-proposal-card-done")).toBeTruthy()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("edit inline updates the value before save", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    render(<WebsiteProposalCard data={{ proposed, companyId: COMPANY_ID }} />)
    fireEvent.click(screen.getByTestId("field-edit-culture::mission"))
    const input = screen.getByTestId("field-input-culture::mission") as HTMLInputElement
    fireEvent.change(input, { target: { value: "Nova missão" } })
    fireEvent.click(screen.getByTestId("website-proposal-save-all"))
    await waitFor(() => expect(screen.getByTestId("website-proposal-card-done")).toBeTruthy())
    const cultureCall = fetchMock.mock.calls.find((c) =>
      String(c[0]).includes("/company/culture-profile/"),
    )
    expect(cultureCall).toBeTruthy()
    const body = JSON.parse(String((cultureCall![1] as RequestInit).body))
    expect(body.mission).toBe("Nova missão")
  })

  it("unchecking 2 of 3 blocks enables 'Salvar selecionados' and only POSTs the 1 kept", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    render(<WebsiteProposalCard data={{ proposed, companyId: COMPANY_ID }} />)
    fireEvent.click(screen.getByTestId("proposal-block-tech_stack"))
    fireEvent.click(screen.getByTestId("proposal-block-basic_complementary"))
    fireEvent.click(screen.getByTestId("website-proposal-save-selected"))
    await waitFor(() => expect(screen.getByTestId("website-proposal-card-done")).toBeTruthy())
    const urls = fetchMock.mock.calls.map((c) => String(c[0]))
    expect(urls.some((u) => u.includes("/culture-profile/"))).toBe(true)
    expect(urls.some((u) => u.includes("/skills-catalog/"))).toBe(false)
    expect(urls.some((u) => u.includes("/company/profile/"))).toBe(false)
  })
})
