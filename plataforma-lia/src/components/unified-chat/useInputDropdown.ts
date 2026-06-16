import { useState, useCallback, useRef, useEffect } from "react"

export interface DropdownItem {
  id: string
  label: string
  subtitle?: string
  category?: string
  icon?: React.ComponentType<{ className?: string }>
}

export interface InputDropdownState {
  isOpen: boolean
  selectedIndex: number
  items: DropdownItem[]
  triggerStart: number
  query: string
}

interface UseInputDropdownOptions {
  triggerChar: string
  /**
   * When true, the query (text after the trigger char) must be a single
   * "word" — a space ends the dropdown. Used by `/`-style commands so
   * that typing `/criar ` (with trailing space) closes the menu.
   *
   * The trigger char itself can appear anywhere as long as it sits at
   * the start of the input or is preceded by whitespace — same rule as
   * `@` mentions. This mirrors the Claude-Code-style command palette
   * (mid-text triggering allowed).
   */
  singleWordQuery?: boolean
  onSelect: (item: DropdownItem) => void
}

export function useInputDropdown(options: UseInputDropdownOptions) {
  const { triggerChar, singleWordQuery = false, onSelect } = options

  const [state, setState] = useState<InputDropdownState>({
    isOpen: false,
    selectedIndex: 0,
    items: [],
    triggerStart: -1,
    query: "",
  })

  const stateRef = useRef(state)
  stateRef.current = state

  const open = useCallback((items: DropdownItem[], triggerStart: number, query: string) => {
    setState({
      isOpen: true,
      selectedIndex: 0,
      items,
      triggerStart,
      query,
    })
  }, [])

  const close = useCallback(() => {
    setState({
      isOpen: false,
      selectedIndex: 0,
      items: [],
      triggerStart: -1,
      query: "",
    })
  }, [])

  const setItems = useCallback((items: DropdownItem[]) => {
    setState(prev => ({ ...prev, items, selectedIndex: 0 }))
  }, [])

  const selectItem = useCallback((item: DropdownItem) => {
    onSelect(item)
    close()
  }, [onSelect, close])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>): boolean => {
    const s = stateRef.current
    if (!s.isOpen || s.items.length === 0) return false

    if (e.key === "ArrowDown") {
      e.preventDefault()
      setState(prev => ({
        ...prev,
        selectedIndex: (prev.selectedIndex + 1) % prev.items.length,
      }))
      return true
    }

    if (e.key === "ArrowUp") {
      e.preventDefault()
      setState(prev => ({
        ...prev,
        selectedIndex: (prev.selectedIndex - 1 + prev.items.length) % prev.items.length,
      }))
      return true
    }

    // Tab and Enter both confirm the highlighted item — matches the
    // Claude Code command palette where Tab is the canonical "accept"
    // key. Shift+Tab keeps default browser focus behaviour so the user
    // can still escape the textarea if no item is highlighted.
    if (e.key === "Enter" || (e.key === "Tab" && !e.shiftKey)) {
      e.preventDefault()
      const item = s.items[s.selectedIndex]
      if (item) selectItem(item)
      return true
    }

    if (e.key === "Escape") {
      e.preventDefault()
      close()
      return true
    }

    return false
  }, [selectItem, close])

  const checkTrigger = useCallback((
    value: string,
    selectionStart: number
  ): { triggered: boolean; query: string; triggerStart: number } => {
    // Walk backward from cursor looking for the trigger char.
    let i = selectionStart - 1
    while (i >= 0) {
      const ch = value[i]
      if (ch === triggerChar) {
        // Position rule (uniform for `/` and `@`): trigger char must be
        // at the start of the input or preceded by whitespace. This is
        // what enables "type / mid-sentence" — the Claude-Code command
        // palette behaviour.
        if (i > 0 && !/\s/.test(value[i - 1])) {
          return { triggered: false, query: "", triggerStart: -1 }
        }
        const query = value.slice(i + 1, selectionStart)
        // For `/`-style commands the query is a single word; a space
        // closes the dropdown. `@` mentions allow spaces (candidate
        // names like "Maria Silva").
        if (singleWordQuery && query.includes(" ")) {
          return { triggered: false, query: "", triggerStart: -1 }
        }
        return { triggered: true, query, triggerStart: i }
      }
      // Stop scanning when we hit whitespace before finding the trigger.
      // Same rule for both modes — keeps the lookback bounded so we
      // don't return a stale trigger from earlier in the line.
      if (/\s/.test(ch)) {
        // For slash commands we tolerate spaces inside the query (the
        // space-in-query rule above closes the dropdown), but the
        // trigger lookback stops at any whitespace.
        if (singleWordQuery) {
          // Slash commands: query is single-word; if we hit any
          // whitespace before the trigger, abort.
          break
        }
        // Mentions: candidate names can include spaces. Keep walking
        // backward — the trigger char must still be preceded by
        // whitespace (handled by the position rule above).
        break
      }
      i--
    }
    return { triggered: false, query: "", triggerStart: -1 }
  }, [triggerChar, singleWordQuery])

  return {
    isOpen: state.isOpen,
    selectedIndex: state.selectedIndex,
    items: state.items,
    triggerStart: state.triggerStart,
    query: state.query,
    open,
    close,
    setItems,
    selectItem,
    handleKeyDown,
    checkTrigger,
  }
}
