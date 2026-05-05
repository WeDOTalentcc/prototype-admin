import { useCallback, useEffect } from "react"
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

  useEffect(() => {
    const { triggered, query, triggerStart } = dropdown.checkTrigger(inputText, selectionStart)

    if (!triggered) {
      if (dropdown.isOpen) dropdown.close()
      return
    }

    const filtered = COMMANDS.filter(cmd =>
      cmd.label.toLowerCase().includes(query.toLowerCase())
    )

    if (!dropdown.isOpen) {
      dropdown.open(filtered, triggerStart, query)
    } else {
      dropdown.setItems(filtered)
    }
  }, [inputText, selectionStart, dropdown])

  return {
    isOpen: dropdown.isOpen,
    selectedIndex: dropdown.selectedIndex,
    items: dropdown.items,
    handleKeyDown: dropdown.handleKeyDown,
    close: dropdown.close,
    selectItem: dropdown.selectItem,
  }
}
