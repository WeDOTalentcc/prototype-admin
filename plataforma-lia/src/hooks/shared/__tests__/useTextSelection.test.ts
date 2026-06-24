import { renderHook, act } from "@testing-library/react"
import { fireEvent } from "@testing-library/react"
import { MIN_SELECTION_CHARS, useTextSelection } from "../use-text-selection"

// Helper to simulate a text selection with a given text
function simulateSelection(text: string, container: Element | null = document.body) {
  const range = document.createRange()
  const textNode = document.createTextNode(text)
  container!.appendChild(textNode)
  range.selectNode(textNode)
  const sel = window.getSelection()!
  sel.removeAllRanges()
  sel.addRange(range)
  return () => {
    sel.removeAllRanges()
    container!.removeChild(textNode)
  }
}

describe("useTextSelection — harness sensor: computacional", () => {
  beforeEach(() => {
    window.getSelection()?.removeAllRanges()
  })

  it("ignores selection shorter than MIN_SELECTION_CHARS", async () => {
    const { result } = renderHook(() => useTextSelection())
    const cleanup = simulateSelection("short")  // < 10 chars
    await act(async () => {
      fireEvent.mouseUp(document)
      await new Promise((r) => setTimeout(r, 250))
    })
    expect(result.current.selection.isActive).toBe(false)
    cleanup()
  })

  it("activates for a long enough selection", async () => {
    const { result } = renderHook(() => useTextSelection())
    const text = "This is a long enough text selection"
    const cleanup = simulateSelection(text)
    await act(async () => {
      fireEvent.mouseUp(document)
      await new Promise((r) => setTimeout(r, 250))
    })
    expect(result.current.selection.isActive).toBe(true)
    expect(result.current.selection.text).toBe(text)
    cleanup()
  })

  it("clears on Escape key", async () => {
    const { result } = renderHook(() => useTextSelection())
    const text = "This is a long enough text selection"
    const cleanup = simulateSelection(text)
    await act(async () => {
      fireEvent.mouseUp(document)
      await new Promise((r) => setTimeout(r, 250))
    })
    expect(result.current.selection.isActive).toBe(true)

    act(() => {
      fireEvent.keyDown(document, { key: "Escape" })
    })
    expect(result.current.selection.isActive).toBe(false)
    cleanup()
  })

  it("ignores selection inside INPUT element", async () => {
    const { result } = renderHook(() => useTextSelection())
    const input = document.createElement("input")
    input.value = "This value is long enough for selection"
    document.body.appendChild(input)

    // Simulate selection anchored at an INPUT
    const mockSel = {
      isCollapsed: false,
      toString: () => "This value is long enough",
      anchorNode: { parentElement: input },
      getRangeAt: () => ({ getBoundingClientRect: () => new DOMRect() }),
    }
    const origGet = window.getSelection
    window.getSelection = () => mockSel as unknown as Selection

    await act(async () => {
      fireEvent.mouseUp(document)
      await new Promise((r) => setTimeout(r, 250))
    })
    expect(result.current.selection.isActive).toBe(false)

    window.getSelection = origGet
    document.body.removeChild(input)
  })

  it("exports MIN_SELECTION_CHARS as 10", () => {
    expect(MIN_SELECTION_CHARS).toBe(10)
  })

  it("clear() resets the selection", async () => {
    const { result } = renderHook(() => useTextSelection())
    const cleanup = simulateSelection("This is a long enough selection text")
    await act(async () => {
      fireEvent.mouseUp(document)
      await new Promise((r) => setTimeout(r, 250))
    })
    expect(result.current.selection.isActive).toBe(true)
    act(() => result.current.clear())
    expect(result.current.selection.isActive).toBe(false)
    cleanup()
  })
})
