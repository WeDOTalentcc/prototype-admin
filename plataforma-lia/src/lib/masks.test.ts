import { describe, it, expect } from "vitest"
import { maskCPF, maskCNPJ, maskPhone, maskCEP, maskCurrency, isValidCPF, isValidCNPJ } from "./masks"

describe("maskCPF", () => {
  it("formats a full 11-digit CPF", () => {
    expect(maskCPF("12345678901")).toBe("123.456.789-01")
  })

  it("formats partial input", () => {
    expect(maskCPF("123")).toBe("123")
    expect(maskCPF("123456")).toBe("123.456")
    expect(maskCPF("123456789")).toBe("123.456.789")
  })

  it("strips non-digits before formatting", () => {
    expect(maskCPF("123.456.789-01")).toBe("123.456.789-01")
  })
})

describe("maskCNPJ", () => {
  it("formats a full 14-digit CNPJ", () => {
    expect(maskCNPJ("12345678000195")).toBe("12.345.678/0001-95")
  })

  it("formats partial input", () => {
    expect(maskCNPJ("12")).toBe("12")
    expect(maskCNPJ("12345")).toBe("12.345")
  })
})

describe("maskPhone", () => {
  it("formats an 11-digit mobile phone", () => {
    expect(maskPhone("11987654321")).toBe("(11) 98765-4321")
  })

  it("formats a 10-digit landline", () => {
    expect(maskPhone("1134567890")).toBe("(11) 3456-7890")
  })

  it("formats partial input", () => {
    expect(maskPhone("11")).toBe("(11")
  })
})

describe("maskCEP", () => {
  it("formats full 8-digit CEP", () => {
    expect(maskCEP("12345678")).toBe("12345-678")
  })

  it("formats partial CEP", () => {
    expect(maskCEP("123")).toBe("123")
  })
})

describe("isValidCPF", () => {
  it("returns true for a valid CPF", () => {
    expect(isValidCPF("529.982.247-25")).toBe(true)
  })

  it("returns false for all-same-digit CPF", () => {
    expect(isValidCPF("111.111.111-11")).toBe(false)
  })

  it("returns false for wrong CPF", () => {
    expect(isValidCPF("123.456.789-00")).toBe(false)
  })
})

describe("isValidCNPJ", () => {
  it("returns true for a valid CNPJ", () => {
    expect(isValidCNPJ("11.222.333/0001-81")).toBe(true)
  })

  it("returns false for all-same-digit CNPJ", () => {
    expect(isValidCNPJ("11.111.111/1111-11")).toBe(false)
  })
})
