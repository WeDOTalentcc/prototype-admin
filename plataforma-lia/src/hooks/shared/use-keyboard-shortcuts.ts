import { useEffect } from 'react'

interface KeyboardShortcutsOptions {
  onAIActivate?: () => void
  onVoiceActivate?: () => void
  onLibraryOpen?: () => void
  onChatOpen?: () => void
}

export function useKeyboardShortcuts({
  onAIActivate,
  onVoiceActivate,
  onLibraryOpen,
  onChatOpen
}: KeyboardShortcutsOptions) {

  useEffect(() => {
    // Aguardar hidratação antes de registrar listeners
    if (typeof window === 'undefined') return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Verificar se está em um campo de input/textarea para evitar conflitos
      const isInInputField = (event.target as HTMLElement)?.tagName?.toLowerCase() === 'input' ||
                            (event.target as HTMLElement)?.tagName?.toLowerCase() === 'textarea' ||
                            (event.target as HTMLElement)?.contentEditable === 'true'

      // Ctrl+K - Ativar IA copilot em qualquer campo de busca
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()

        // Procurar pelo campo de busca mais próximo ou ativo
        const searchInputs = document.querySelectorAll('input[placeholder*="Buscar"], input[placeholder*="buscar"]')
        const searchToggleButtons = document.querySelectorAll('[title*="busca com IA"], [title*="Usar busca com IA"]')

        if (searchToggleButtons.length > 0) {
          // Ativar IA mode no primeiro campo encontrado
          const button = searchToggleButtons[0] as HTMLButtonElement
          button.click()
        } else if (searchInputs.length > 0) {
          // Focar no primeiro campo de busca
          const input = searchInputs[0] as HTMLInputElement
          input.focus()
        }

        onAIActivate?.()
        return
      }

      // Ctrl+; - Ativar reconhecimento de voz
      if ((event.ctrlKey || event.metaKey) && event.key === ';') {
        event.preventDefault()

        // Procurar botão de voz ativo
        const voiceButtons = document.querySelectorAll('[title*="voz"], [title*="Buscar por voz"]')
        if (voiceButtons.length > 0) {
          const button = voiceButtons[0] as HTMLButtonElement
          if (!button.disabled) {
            button.click()
          }
        }

        onVoiceActivate?.()
        return
      }

      // Ctrl+Shift+L - Abrir biblioteca da LIA
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'L') {
        event.preventDefault()
        onLibraryOpen?.()
        return
      }

      // Ctrl+Shift+C - Abrir chat com LIA
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault()
        onChatOpen?.()
        return
      }

      // Escape - Sair de modais/overlays
      if (event.key === 'Escape' && !isInInputField) {
        // Fechar apenas botões marcados com data-dismiss="true" (contrato de dismiss)
        // Usa o último elemento visível no DOM como heurística de sobreposição
        const dismissButtons = Array.from(
          document.querySelectorAll<HTMLButtonElement>('[data-dismiss="true"]')
        ).filter(btn => {
          if (btn.offsetParent === null) return false
          const rect = btn.getBoundingClientRect()
          return rect.width > 0 && rect.height > 0
        })

        if (dismissButtons.length > 0) {
          // Clica apenas no último botão de fechar visível no DOM
          dismissButtons[dismissButtons.length - 1].click()
        }
      }

      // F1 - Mostrar ajuda de atalhos
      if (event.key === 'F1') {
        event.preventDefault()
        showKeyboardShortcutsHelp()
        return
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onAIActivate, onVoiceActivate, onLibraryOpen, onChatOpen])

  // Mostrar modal de ajuda com atalhos
  const showKeyboardShortcutsHelp = () => {
    const helpModal = document.createElement('div')
    helpModal.className = 'fixed inset-0 bg-lia-overlay flex items-center justify-center z-toast'
    helpModal.innerHTML = `
      <div class="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-6 max-w-md w-full mx-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-lia-text-primary">Atalhos de Teclado</h3>
          <button id="close-help" class="text-lia-text-tertiary hover:text-lia-text-secondary dark:text-lia-text-tertiary dark:hover:text-lia-text-inverse">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Ativar IA Copilot</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">Ctrl+K</kbd>
          </div>
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Busca por Voz</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">Ctrl+;</kbd>
          </div>
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Biblioteca LIA</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">Ctrl+Shift+L</kbd>
          </div>
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Chat com LIA</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">Ctrl+Shift+C</kbd>
          </div>
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Fechar Modal</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">Esc</kbd>
          </div>
          <div class="flex justify-between">
            <span class="text-lia-text-secondary dark:text-lia-text-tertiary">Esta Ajuda</span>
            <kbd class="px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md text-xs font-mono">F1</kbd>
          </div>
        </div>

        <div class="mt-4 p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
          <p class="text-xs text-wedo-cyan-text dark:text-lia-text-tertiary">
            💡 Dica: Use Ctrl+K em qualquer página para ativar rapidamente a busca com IA
          </p>
        </div>
      </div>
    `

    document.body.appendChild(helpModal)

    // Fechar modal
    const closeHelp = () => {
      document.body.removeChild(helpModal)
    }

    helpModal.querySelector('#close-help')?.addEventListener('click', closeHelp)
    helpModal.addEventListener('click', (e) => {
      if (e.target === helpModal) closeHelp()
    })

    // Fechar com Escape
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeHelp()
        document.removeEventListener('keydown', handleEscape)
      }
    }
    document.addEventListener('keydown', handleEscape)
  }
}
