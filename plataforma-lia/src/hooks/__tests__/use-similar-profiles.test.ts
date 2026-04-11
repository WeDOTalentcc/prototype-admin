/**
 * P1-E — Testes unitários: useSimilarProfiles
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. Estado inicial (1 URL vazia, sem CVs)
 * 2. addSimilarUrl: adiciona URL até MAX_SIMILAR_URLS
 * 3. addSimilarUrl: não adiciona além do limite
 * 4. removeSimilarUrl: remove e limpa combinedSuggestions
 * 5. updateSimilarUrl: atualiza valor no índice correto
 * 6. handleCvUpload: adiciona arquivos até MAX_CV_FILES
 * 7. removeCvFile: remove arquivo e limpa combinedSuggestions
 * 8. addSimilarProfile: respeita limite de 3 perfis
 * 9. removeSimilarProfile: remove por URL
 * 10. hasMultipleSources: false quando tudo vazio, true com 1+ fonte
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect } from "vitest"
import { useSimilarProfiles } from "../candidates/use-similar-profiles"

const mockOnChange = vi.fn()

const makeFile = (name: string) => new File(["content"], name, { type: "application/pdf" })

describe("P1-E — useSimilarProfiles", () => {
  it("1. estado inicial: 1 URL vazia, sem CVs", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    expect(result.current.similarUrls).toEqual([""])
    expect(result.current.similarCvFiles).toEqual([])
    expect(result.current.isAnalyzingProfiles).toBe(false)
    expect(result.current.showCombinedSuggestions).toBe(false)
  })

  it("2. addSimilarUrl: adiciona até MAX_SIMILAR_URLS", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.addSimilarUrl() })
    expect(result.current.similarUrls).toHaveLength(2)
  })

  it("3. addSimilarUrl: não adiciona além do limite (2)", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.addSimilarUrl() })
    act(() => { result.current.addSimilarUrl() }) // tentativa além do limite
    expect(result.current.similarUrls).toHaveLength(2)
  })

  it("4. removeSimilarUrl: remove índice e limpa combinedSuggestions", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.addSimilarUrl() })
    act(() => { result.current.removeSimilarUrl(1) })
    expect(result.current.similarUrls).toHaveLength(1)
    expect(result.current.showCombinedSuggestions).toBe(false)
  })

  it("5. updateSimilarUrl: atualiza valor no índice correto", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.updateSimilarUrl(0, "https://linkedin.com/in/user") })
    expect(result.current.similarUrls[0]).toBe("https://linkedin.com/in/user")
  })

  it("6. handleCvUpload: adiciona arquivos via FileList", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    const file = makeFile("cv.pdf")
    const mockFileList = { 0: file, length: 1, item: (i: number) => file, [Symbol.iterator]: function* () { yield file } } as unknown as FileList

    const mockEvent = { target: { files: mockFileList } } as React.ChangeEvent<HTMLInputElement>
    act(() => { result.current.handleCvUpload(mockEvent) })
    expect(result.current.similarCvFiles).toHaveLength(1)
  })

  it("7. removeCvFile: remove arquivo e limpa combinedSuggestions", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    const file = makeFile("cv.pdf")
    const mockFileList = { 0: file, length: 1, item: (i: number) => file, [Symbol.iterator]: function* () { yield file } } as unknown as FileList
    act(() => { result.current.handleCvUpload({ target: { files: mockFileList } } as React.ChangeEvent<HTMLInputElement>) })
    act(() => { result.current.removeCvFile(0) })
    expect(result.current.similarCvFiles).toHaveLength(0)
    expect(result.current.showCombinedSuggestions).toBe(false)
  })

  it("8. addSimilarProfile: respeita limite de 3 e deduplicação", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.addSimilarProfile("url1") })
    act(() => { result.current.addSimilarProfile("url2") })
    act(() => { result.current.addSimilarProfile("url3") })
    act(() => { result.current.addSimilarProfile("url4") }) // além do limite
    expect(result.current.similarProfiles).toHaveLength(3)

    // deduplicação
    act(() => { result.current.addSimilarProfile("url1") })
    expect(result.current.similarProfiles).toHaveLength(3)
  })

  it("9. removeSimilarProfile: remove por URL", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    act(() => { result.current.addSimilarProfile("url1") })
    act(() => { result.current.removeSimilarProfile("url1") })
    expect(result.current.similarProfiles).toHaveLength(0)
  })

  it("10. hasMultipleSources: false quando tudo vazio, true com URL preenchida", () => {
    const { result } = renderHook(() => useSimilarProfiles({ onNaturalSearchValueChange: mockOnChange }))
    expect(result.current.hasMultipleSources()).toBe(false)
    act(() => { result.current.updateSimilarUrl(0, "https://linkedin.com/in/alguem") })
    expect(result.current.hasMultipleSources()).toBe(true)
  })
})
