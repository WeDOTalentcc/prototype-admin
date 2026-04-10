import { useCallback, useEffect } from "react"
import { Briefcase, Search, BarChart2, FileText, HelpCircle, Plus } from "lucide-react"
import { useInputDropdown, type DropdownItem } from "./useInputDropdown"

const COMMANDS: DropdownItem[] = [
  { id: "criar-vaga", label: "Criar vaga", subtitle: "Iniciar wizard de criacao de vaga", icon: Briefcase },
  { id: "buscar", label: "Buscar candidatos", subtitle: "Pesquisar candidatos por criterios", icon: Search },
  { id: "pipeline", label: "Ver pipeline", subtitle: "Status do funil de candidatos", icon: BarChart2 },
  { id: "relatorio", label: "Gerar relatorio", subtitle: "Relatorios de recrutamento", icon: FileText },
  { id: "ajuda", label: "O que posso fazer?", subtitle: "Ver todas as capacidades da LIA", icon: HelpCircle },
  { id: "nova-conversa", label: "Nova conversa", subtitle: "Iniciar conversa limpa", icon: Plus },
]

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

    // Map command to expanded prompt
    const prompts: Record<string, string> = {
      "criar-vaga": "Quero criar uma nova vaga de emprego. ",
      "buscar": "Buscar candidatos que ",
      "pipeline": "Mostrar o status do pipeline de candidatos",
      "relatorio": "Gerar um relatorio de recrutamento ",
      "ajuda": "O que voce pode fazer? Liste todas as suas capacidades.",
    }

    const prompt = prompts[item.id] || item.label
    onPrefillInput(prompt)
  }, [onExecuteCommand, onPrefillInput])

  const dropdown = useInputDropdown({
    triggerChar: "/",
    requireStartOfLine: true,
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
