import { describe, expect, it } from "vitest"

import { formatJobLocation } from "./location"

describe("formatJobLocation", () => {
  it("passa string simples intacta", () => {
    expect(formatJobLocation("São Paulo, SP")).toBe("São Paulo, SP")
  })

  it("faz trim de string simples", () => {
    expect(formatJobLocation("  Remoto  ")).toBe("Remoto")
  })

  it("retorna undefined para JSON com todos os campos nulos", () => {
    expect(
      formatJobLocation('{"city": null, "state": null, "country": null}'),
    ).toBeUndefined()
  })

  it("retorna só o país quando é o único campo presente", () => {
    expect(
      formatJobLocation('{"city": null, "state": null, "country": "Brasil"}'),
    ).toBe("Brasil")
  })

  it("une cidade, estado e país por vírgula", () => {
    expect(
      formatJobLocation('{"city": "São Paulo", "state": "SP", "country": "Brasil"}'),
    ).toBe("São Paulo, SP, Brasil")
  })

  it("ignora strings vazias dentro do objeto", () => {
    expect(
      formatJobLocation('{"city": "  ", "state": "RJ", "country": ""}'),
    ).toBe("RJ")
  })

  it("cai de volta para a string original em JSON malformado", () => {
    const malformed = '{"city": "São Paulo", "state":'
    expect(formatJobLocation(malformed)).toBe(malformed)
  })

  it("aceita objeto já parseado", () => {
    expect(
      formatJobLocation({ city: "Recife", state: "PE", country: "Brasil" }),
    ).toBe("Recife, PE, Brasil")
  })

  it("retorna undefined para objeto sem campos úteis", () => {
    expect(formatJobLocation({ city: null, state: null, country: null })).toBeUndefined()
  })

  it("retorna undefined para null/undefined/string vazia", () => {
    expect(formatJobLocation(null)).toBeUndefined()
    expect(formatJobLocation(undefined)).toBeUndefined()
    expect(formatJobLocation("   ")).toBeUndefined()
  })
})
