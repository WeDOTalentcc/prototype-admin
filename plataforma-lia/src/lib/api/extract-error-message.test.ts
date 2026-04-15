import { describe, it, expect } from "vitest"
import { extractErrorMessage } from "./extract-error-message"

// Testes do helper introduzido no BUG-03 do QA 2026-04-15.
// Garante que mensagens de erro detalhadas do backend (via createProxyHandlers)
// são extraídas corretamente em vez de mostrar "Error 403".

describe("extractErrorMessage", () => {
  it("extrai details.message do envelope do proxy (formato FastAPI + details)", () => {
    const body = {
      error: "Backend error on POST /api/v1/sourcing-agents",
      details: {
        error: true,
        status_code: 403,
        message: "Quota exceeded for sourcing agents: current usage 2/1. Upgrade your plan or contact admin to increase quota.",
      },
    }
    expect(extractErrorMessage(body, 403)).toBe(
      "Quota exceeded for sourcing agents: current usage 2/1. Upgrade your plan or contact admin to increase quota."
    )
  })

  it("extrai detail string direto do FastAPI", () => {
    const body = { detail: "Usuário sem empresa associada." }
    expect(extractErrorMessage(body, 400)).toBe("Usuário sem empresa associada.")
  })

  it("extrai detail.message quando detail é objeto", () => {
    const body = { detail: { message: "Rate limit exceeded", retry_after: 60 } }
    expect(extractErrorMessage(body, 429)).toBe("Rate limit exceeded")
  })

  it("extrai message direto", () => {
    expect(extractErrorMessage({ message: "Ops" }, 500)).toBe("Ops")
  })

  it("extrai error direto quando é string", () => {
    expect(extractErrorMessage({ error: "Something went wrong" }, 500)).toBe(
      "Something went wrong"
    )
  })

  it("cai no fallback 'Erro {status}' quando nada legível disponível", () => {
    expect(extractErrorMessage({}, 502)).toBe("Erro 502")
  })

  it("cai no fallback genérico quando sem body E sem status", () => {
    expect(extractErrorMessage(null)).toBe("Erro desconhecido")
    expect(extractErrorMessage(undefined)).toBe("Erro desconhecido")
    expect(extractErrorMessage("string cruista")).toBe("Erro desconhecido")
  })

  it("prioriza details.message sobre outros campos", () => {
    const body = {
      error: "generic-error",
      message: "another-message",
      details: { message: "priority-message" },
    }
    expect(extractErrorMessage(body)).toBe("priority-message")
  })

  it("ignora campos vazios/falsy e segue para o próximo", () => {
    const body = {
      details: { message: "" },
      detail: "real-detail",
    }
    expect(extractErrorMessage(body)).toBe("real-detail")
  })
})
