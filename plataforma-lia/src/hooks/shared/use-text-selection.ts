"use client"

import { useState, useEffect, useCallback, useRef } from "react"

/** Minimum chars to activate the selection toolbar. Guide: computacional. */
export const MIN_SELECTION_CHARS = 10
const MAX_SELECTION_CHARS = 2000
/** Tags where selection should be ignored (form editing). Guide: computacional. */
const BLOCKED_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT", "OPTION"])

export interface TextSelectionState {
  text: string
  rect: DOMRect | null
  isActive: boolean
}

export function useTextSelection() {
  const [selection, setSelection] = useState<TextSelectionState>({
    text: "",
    rect: null,
    isActive: false,
  })
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  const clear = useCallback(() => {
    setSelection({ text: "", rect: null, isActive: false })
  }, [])

  useEffect(() => {
    const handleMouseUp = () => {
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        const sel = window.getSelection()
        if (!sel || sel.isCollapsed) { clear(); return }

        const text = sel.toString().trim()
        if (text.length < MIN_SELECTION_CHARS || text.length > MAX_SELECTION_CHARS) {
          clear(); return
        }

        // Block form elements and contenteditable at any depth
        const anchor = sel.anchorNode?.parentElement
        if (anchor) {
          if (BLOCKED_TAGS.has(anchor.tagName)) { clear(); return }
          if (anchor.closest('[contenteditable="true"], input, textarea, select')) {
            clear(); return
          }
        }

        const range = sel.getRangeAt(0)
        setSelection({ text, rect: range.getBoundingClientRect(), isActive: true })
      }, 180)
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") clear()
    }

    document.addEventListener("mouseup", handleMouseUp)
    document.addEventListener("keydown", handleKeyDown)
    return () => {
      clearTimeout(timerRef.current)
      document.removeEventListener("mouseup", handleMouseUp)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [clear])

  return { selection, clear }
}
