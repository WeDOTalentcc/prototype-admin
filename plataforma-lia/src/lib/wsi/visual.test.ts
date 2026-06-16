/**
 * Task #512 (PR3 do issue #497) — Testes do helper canônico WSI 0-10.
 * Cobre cores 3-tier nas fronteiras (>=7.5 verde, >=6.0 amarelo, <6.0 vermelho)
 * e mapeamento snake_case <-> camelCase para chaves i18n.
 */
import { describe, expect, it } from "vitest"
import {
  WSI_DISPLAY_SCALE,
  WSI_VISUAL_3TIER,
  formatWsiScore,
  getWsiClassification,
  getWsiScoreColor,
  getWsiVisualState,
  wsiClassificationI18nKey,
  wsiPercent,
} from "@/lib/wsi/visual"

describe("WSI visual helper — escala 0-10", () => {
  it("expõe escala de display 10", () => {
    expect(WSI_DISPLAY_SCALE).toBe(10)
    expect(WSI_VISUAL_3TIER.green).toBe(7.5)
    expect(WSI_VISUAL_3TIER.yellow).toBe(6.0)
  })

  describe("getWsiScoreColor (3-tier)", () => {
    it("retorna verde para score na fronteira superior (>=7.5)", () => {
      expect(getWsiScoreColor(7.5)).toBe("text-status-success")
      expect(getWsiScoreColor(8.5)).toBe("text-status-success")
      expect(getWsiScoreColor(9.5)).toBe("text-status-success")
      expect(getWsiScoreColor(10)).toBe("text-status-success")
    })

    it("retorna amarelo na faixa intermediária (>=6.0 e <7.5)", () => {
      expect(getWsiScoreColor(6.0)).toBe("text-status-warning")
      expect(getWsiScoreColor(6.5)).toBe("text-status-warning")
      expect(getWsiScoreColor(7.49)).toBe("text-status-warning")
    })

    it("retorna vermelho abaixo de 6.0", () => {
      expect(getWsiScoreColor(5.99)).toBe("text-status-error")
      expect(getWsiScoreColor(4.0)).toBe("text-status-error")
      expect(getWsiScoreColor(0)).toBe("text-status-error")
    })

    it("retorna placeholder cinza para null/undefined", () => {
      expect(getWsiScoreColor(null)).toBe("text-lia-text-secondary")
      expect(getWsiScoreColor(undefined)).toBe("text-lia-text-secondary")
    })
  })

  describe("getWsiVisualState — todas as classificações usam apenas 3 cores", () => {
    it("score 9.5 -> excepcional + verde", () => {
      const v = getWsiVisualState(9.5)
      expect(v.classification).toBe("excepcional")
      expect(v.text).toBe("text-status-success")
    })

    it("score 8.0 -> excelente + verde", () => {
      const v = getWsiVisualState(8.0)
      expect(v.classification).toBe("excelente")
      expect(v.text).toBe("text-status-success")
    })

    it("score 7.5 -> alto + verde (mesma cor do excelente)", () => {
      const v = getWsiVisualState(7.5)
      expect(v.classification).toBe("alto")
      expect(v.text).toBe("text-status-success")
    })

    it("score 6.5 -> medio + amarelo", () => {
      const v = getWsiVisualState(6.5)
      expect(v.classification).toBe("medio")
      expect(v.text).toBe("text-status-warning")
    })

    it("score 4.0 -> regular + vermelho", () => {
      const v = getWsiVisualState(4.0)
      expect(v.classification).toBe("regular")
      expect(v.text).toBe("text-status-error")
    })
  })

  describe("getWsiClassification cutoffs", () => {
    it.each([
      [10, "excepcional"],
      [9.0, "excepcional"],
      [8.99, "excelente"],
      [8.0, "excelente"],
      [7.5, "alto"],
      [6.5, "medio"],
      [6.0, "medio"],
      [5.0, "abaixo_da_media"],
      [3.0, "regular"],
      [0, "regular"],
    ])("score %f -> %s", (score, expected) => {
      expect(getWsiClassification(score)).toBe(expected)
    })
  })

  describe("wsiClassificationI18nKey — snake_case → camelCase", () => {
    it("mapeia abaixo_da_media para abaixoDaMedia (chave i18n)", () => {
      expect(wsiClassificationI18nKey("abaixo_da_media")).toBe("abaixoDaMedia")
    })

    it("preserva chaves single-word", () => {
      expect(wsiClassificationI18nKey("excepcional")).toBe("excepcional")
      expect(wsiClassificationI18nKey("excelente")).toBe("excelente")
      expect(wsiClassificationI18nKey("alto")).toBe("alto")
      expect(wsiClassificationI18nKey("medio")).toBe("medio")
      expect(wsiClassificationI18nKey("regular")).toBe("regular")
    })

    it("aceita classificação desconhecida sem quebrar (fallback medio)", () => {
      expect(wsiClassificationI18nKey("inexistente")).toBe("medio")
    })
  })

  describe("formatação", () => {
    it("formatWsiScore exibe X.X/10.0", () => {
      expect(formatWsiScore(8.5)).toBe("8.5/10.0")
      expect(formatWsiScore(10)).toBe("10.0/10.0")
    })

    it("wsiPercent converte 0-10 para 0-100", () => {
      expect(wsiPercent(7.5)).toBe(75)
      expect(wsiPercent(10)).toBe(100)
      expect(wsiPercent(0)).toBe(0)
      expect(wsiPercent(15)).toBe(100) // clamp
      expect(wsiPercent(-1)).toBe(0)   // clamp
    })
  })
})
