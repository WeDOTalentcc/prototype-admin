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
  requireStartOfLine?: boolean
  onSelect: (item: DropdownItem) => void
}

export function useInputDropdown(options: UseInputDropdownOptions) {
  const { triggerChar, requireStartOfLine = false, onSelect } = options

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

    if (e.key === "Enter") {
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
    // Walk backward from cursor to find trigger char
    let i = selectionStart - 1
    while (i >= 0) {
      const ch = value[i]
      if (ch === triggerChar) {
        // If requireStartOfLine, trigger char must be at pos 0 or after newline
        if (requireStartOfLine) {
          if (i !== 0 && value[i - 1] !== "\n") {
            return { triggered: false, query: "", triggerStart: -1 }
          }
        } else {
          // For @, trigger must be at start or preceded by whitespace
          if (i > 0 && !/\s/.test(value[i - 1])) {
            return { triggered: false, query: "", triggerStart: -1 }
          }
        }
        const query = value.slice(i + 1, selectionStart)
        // No spaces allowed in query for slash commands
        if (requireStartOfLine && query.includes(" ")) {
          return { triggered: false, query: "", triggerStart: -1 }
        }
        return { triggered: true, query, triggerStart: i }
      }
      // Stop scanning on whitespace for @ mentions
      if (!requireStartOfLine && /\s/.test(ch)) break
      // Stop scanning on newline for slash commands
      if (requireStartOfLine && ch === "\n") break
      i--
    }
    return { triggered: false, query: "", triggerStart: -1 }
  }, [triggerChar, requireStartOfLine])

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
