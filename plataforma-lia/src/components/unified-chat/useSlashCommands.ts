import { useCallback, useEffect, useRef } from "react"
import { useInputDropdown, type DropdownItem } from "./useInputDropdown"
import { SLASH_COMMANDS } from "./slash-commands"

const COMMANDS: DropdownItem[] = SLASH_COMMANDS.filter((cmd) => cmd.showInDropdown).map((cmd) => ({
  id: cmd.id,
  // Show the canonical token (e.g. /criar vaga) so the dropdown
  // works as a Claude-Code-style command palette.
  label: cmd.primary,
  subtitle: cmd.subtitle,
}))

interface UseSlashCommandsOptions {
  inputText: string
  selectionStart: number
  onExecuteCommand: (commandId: string) => void
  onPrefillInput: (text: string) => void
}

export function useSlashCommands(options: UseSlashCommandsOptions) {
  const { inputText, selectionStart, onExecuteCommand, onPrefillInput } = options

  const handleSelect = useCallback((item: DropdownItem) => {
    if (item.id === "nova-conversa") {
      onExecuteCommand("nova-conversa")
      return
    }

    const cmd = SLASH_COMMANDS.find((c) => c.id === item.id)
    const prompt = cmd?.dropdownPrefill ?? item.label
    onPrefillInput(prompt)
  }, [onExecuteCommand, onPrefillInput])

  const dropdown = useInputDropdown({
    triggerChar: "/",
    singleWordQuery: true,
    onSelect: handleSelect,
  })

  // Destructure stable callbacks (memoized via useCallback inside
  // useInputDropdown) plus the current isOpen flag. Depending on the
  // whole `dropdown` object would loop infinitely because the hook
  // returns a fresh object literal on every render.
  const { checkTrigger, open, close, setItems, isOpen } = dropdown

  // Once the user dismisses the dropdown (Escape) the trigger char is
  // still in the input, so the effect would immediately reopen it.
  // Track which triggerStart was dismissed and suppress reopen until
  // that trigger session ends (cursor leaves, char deleted, etc.).
  const dismissedAtRef = useRef<number | null>(null)
  const prevIsOpenRef = useRef(isOpen)

  useEffect(() => {
    const { triggered, query, triggerStart } = checkTrigger(inputText, selectionStart)

    // Detect external dismissal: open last render, closed now, while
    // the trigger is still present → user explicitly closed it.
    if (prevIsOpenRef.current && !isOpen && triggered) {
      dismissedAtRef.current = triggerStart
    }
    prevIsOpenRef.current = isOpen

    if (!triggered) {
      dismissedAtRef.current = null
      if (isOpen) close()
      return
    }

    // Reset suppression when the trigger position moved.
    if (dismissedAtRef.current !== null && dismissedAtRef.current !== triggerStart) {
      dismissedAtRef.current = null
    }

    if (dismissedAtRef.current === triggerStart) return

    const filtered = COMMANDS.filter(cmd =>
      cmd.label.toLowerCase().includes(query.toLowerCase())
    )

    if (!isOpen) {
      open(filtered, triggerStart, query)
    } else {
      setItems(filtered)
    }
  }, [inputText, selectionStart, checkTrigger, open, close, setItems, isOpen])

  return {
    isOpen: dropdown.isOpen,
    selectedIndex: dropdown.selectedIndex,
    items: dropdown.items,
    handleKeyDown: dropdown.handleKeyDown,
    close: dropdown.close,
    selectItem: dropdown.selectItem,
  }
}
