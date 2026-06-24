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


describe("WebsiteProposalCard — campo objeto Big Five editavel (P2)", () => {
  const withBigFive: ProposedSaves = {
    payload_hash: "bf01",
    blocks: [
      {
        key: "culture",
        label: "Cultura & EVP",
        fields: [
          { key: "culture_description", label: "Descricao da cultura", value: "Foco em pessoas" },
          { key: "big_five", label: "Big Five", value: { openness: 50, conscientiousness: 50 } },
        ],
      },
    ],
  }

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200 })))
  })

  it("renderiza objeto como resumo legivel (nao [object Object]) e expoe editor por chave", () => {
    render(<WebsiteProposalCard data={{ proposed: withBigFive, companyId: COMPANY_ID }} />)
    const summary = screen.getByTestId("field-value-culture::big_five")
    expect(summary.textContent).toContain("openness: 50")
    fireEvent.click(screen.getByTestId("field-edit-culture::big_five"))
    const input = screen.getByTestId("field-obj-input-culture::big_five-openness") as HTMLInputElement
    expect(input.value).toBe("50")
  })

  it("editar Big Five persiste o objeto atualizado no save (nao corrompe para string)", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    render(<WebsiteProposalCard data={{ proposed: withBigFive, companyId: COMPANY_ID }} />)
    fireEvent.click(screen.getByTestId("field-edit-culture::big_five"))
    fireEvent.change(screen.getByTestId("field-obj-input-culture::big_five-openness"), {
      target: { value: "80" },
    })
    fireEvent.click(screen.getByTestId("website-proposal-save-all"))
    await waitFor(() => expect(screen.getByTestId("website-proposal-card-done")).toBeTruthy())
    const cultureCall = fetchMock.mock.calls.find((c) => String(c[0]).includes("culture-profile"))
    expect(cultureCall).toBeTruthy()
    const body = JSON.parse(String((cultureCall![1] as RequestInit).body))
    expect(body.big_five).toEqual({ openness: 80, conscientiousness: 50 })
  })
})

