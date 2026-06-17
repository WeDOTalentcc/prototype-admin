import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

// Mock next/navigation
const mockPush = vi.fn()
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Mock TalentPoolsTab to expose onSelectPool easily
vi.mock("@/components/pages-candidates/TalentPoolsTab", () => ({
  default: ({
    onSelectPool,
    openPoolId,
    onClosePool,
  }: {
    onSelectPool: (id: string, name: string) => void
    openPoolId?: string | null
    onClosePool?: () => void
  }) => (
    <div data-testid="talent-pools-tab">
      <button
        data-testid="select-pool-btn"
        onClick={() => onSelectPool("pool-123", "Banco Teste")}
      >
        Selecionar pool
      </button>
      {openPoolId && (
        <div data-testid="pool-detail">
          pool aberto: {openPoolId}
          <button data-testid="close-pool-btn" onClick={onClosePool}>
            Fechar
          </button>
        </div>
      )}
    </div>
  ),
}))

import BancosClient from "../BancosClient"

describe("BancosClient", () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it("não faz router.push ao selecionar pool — abre inline", () => {
    render(<BancosClient />)
    fireEvent.click(screen.getByTestId("select-pool-btn"))
    expect(mockPush).not.toHaveBeenCalledWith(
      expect.stringContaining("/bancos-de-talentos/pool-123"),
    )
  })

  it("exibe detalhe inline quando pool é selecionado", () => {
    render(<BancosClient />)
    fireEvent.click(screen.getByTestId("select-pool-btn"))
    expect(screen.getByTestId("pool-detail")).toBeInTheDocument()
    expect(screen.getByText("pool aberto: pool-123")).toBeInTheDocument()
  })

  it("fecha detalhe inline ao clicar onClosePool", () => {
    render(<BancosClient />)
    fireEvent.click(screen.getByTestId("select-pool-btn"))
    expect(screen.getByTestId("pool-detail")).toBeInTheDocument()
    fireEvent.click(screen.getByTestId("close-pool-btn"))
    expect(screen.queryByTestId("pool-detail")).not.toBeInTheDocument()
  })
})
