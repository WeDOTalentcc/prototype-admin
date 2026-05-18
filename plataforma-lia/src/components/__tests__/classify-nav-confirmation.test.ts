/**
 * Task #1165 — testes do classificador PT-BR de confirmação livre.
 *
 * Cobre as variações enumeradas em `replit.md > User Preferences`
 * ("A LIA deve entender variações naturais de confirmação em português")
 * e os edge-cases onde um token positivo aparece dentro de uma negativa
 * ("agora não", "pode esperar").
 */

import { classifyNavConfirmation } from "../dashboard-app"

describe("classifyNavConfirmation (Task #1165)", () => {
  describe("positivos", () => {
    test.each([
      "sim",
      "Sim!",
      "vamos",
      "vamos lá",
      "bora",
      "pode",
      "pode ir",
      "me leva",
      "leva",
      "claro",
      "com certeza",
      "ok",
      "okay",
      "manda",
      "fechou",
      "certo",
      "isso",
      "yes",
      "y",
    ])("'%s' → yes", (input) => {
      expect(classifyNavConfirmation(input)).toBe("yes")
    })
  })

  describe("negativos (têm precedência sobre tokens positivos)", () => {
    test.each([
      "não",
      "nao",
      "Não",
      "agora não",
      "agora nao",
      "depois",
      "mais tarde",
      "deixa pra lá",
      "deixa",
      "cancela",
      "esquece",
      "pode esperar",
      "nope",
    ])("'%s' → no", (input) => {
      expect(classifyNavConfirmation(input)).toBe("no")
    })
  })

  describe("ambíguos", () => {
    test.each([
      "",
      "   ",
      "talvez",
      "preciso pensar",
      "vou avaliar o JD primeiro",
      "qual o salário sugerido?",
    ])("'%s' → ambiguous", (input) => {
      expect(classifyNavConfirmation(input)).toBe("ambiguous")
    })
  })
})
