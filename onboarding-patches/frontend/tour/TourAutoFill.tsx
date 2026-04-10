"use client"

import { useCallback, useRef } from "react"

interface AutoFillOptions {
  /** CSS selector of the input/textarea */
  selector: string
  /** Text to type */
  value: string
  /** Milliseconds per character */
  typeSpeed?: number
  /** Callback when typing completes */
  onComplete?: () => void
}

/**
 * useTourAutoFill — hook that simulates typing into an input field.
 *
 * Creates a "LIA is typing" effect by filling the input character by character.
 * Dispatches React-compatible input events so controlled components update.
 */
export function useTourAutoFill() {
  const cancelRef = useRef<(() => void) | null>(null)

  const startAutoFill = useCallback(({ selector, value, typeSpeed = 50, onComplete }: AutoFillOptions) => {
    // Cancel any running autofill
    cancelRef.current?.()

    const el = document.querySelector(selector) as HTMLInputElement | HTMLTextAreaElement | null
    if (!el) {
      onComplete?.()
      return
    }

    // Focus the element
    el.focus()
    el.scrollIntoView({ behavior: "smooth", block: "center" })

    let index = 0
    let cancelled = false

    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype,
      "value"
    )?.set

    const typeNext = () => {
      if (cancelled || index > value.length) return

      if (index === value.length) {
        onComplete?.()
        return
      }

      // Set value using native setter (works with React controlled inputs)
      const nextValue = value.slice(0, index + 1)
      if (nativeInputValueSetter) {
        nativeInputValueSetter.call(el, nextValue)
      } else {
        el.value = nextValue
      }

      // Dispatch input event (React listens to this)
      el.dispatchEvent(new Event("input", { bubbles: true }))

      index++
      setTimeout(typeNext, typeSpeed)
    }

    cancelRef.current = () => {
      cancelled = true
    }

    // Start typing after brief delay
    setTimeout(typeNext, 300)
  }, [])

  const cancelAutoFill = useCallback(() => {
    cancelRef.current?.()
  }, [])

  return { startAutoFill, cancelAutoFill }
}
