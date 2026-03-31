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
    if (typeof window === 'undefined') return

    const handleKeyDown = (event: KeyboardEvent) => {
      const isInInputField = (event.target as HTMLElement)?.tagName?.toLowerCase() === 'input' ||
                            (event.target as HTMLElement)?.tagName?.toLowerCase() === 'textarea' ||
                            (event.target as HTMLElement)?.contentEditable === 'true'

      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        const searchInputs = document.querySelectorAll('input[placeholder*="Buscar"], input[placeholder*="buscar"]')
        const searchToggleButtons = document.querySelectorAll('[title*="busca com IA"], [title*="Usar busca com IA"]')
        if (searchToggleButtons.length > 0) {
          const button = searchToggleButtons[0] as HTMLButtonElement
          button.click()
        } else if (searchInputs.length > 0) {
          const input = searchInputs[0] as HTMLInputElement
          input.focus()
        }
        onAIActivate?.()
        return
      }

      if ((event.ctrlKey || event.metaKey) && event.key === ';') {
        event.preventDefault()
        const voiceButtons = document.querySelectorAll('[title*="voz"], [title*="Buscar por voz"]')
        if (voiceButtons.length > 0) {
          const button = voiceButtons[0] as HTMLButtonElement
          if (!button.disabled) button.click()
        }
        onVoiceActivate?.()
        return
      }

      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'L') {
        event.preventDefault()
        onLibraryOpen?.()
        return
      }

      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault()
        onChatOpen?.()
        return
      }

      if (event.key === 'Escape' && !isInInputField) {
        const closeButtons = document.querySelectorAll('[aria-label="Close"], [title="Fechar"], button[type="button"]:has(svg)')
        closeButtons.forEach(button => {
          const buttonEl = button as HTMLButtonElement
          if (buttonEl.offsetParent !== null) {
            const rect = buttonEl.getBoundingClientRect()
            if (rect.width > 0 && rect.height > 0) buttonEl.click()
          }
        })
      }

      if (event.key === 'F1') {
        event.preventDefault()
        showKeyboardShortcutsHelp()
        return
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => { document.removeEventListener('keydown', handleKeyDown) }
  }, [onAIActivate, onVoiceActivate, onLibraryOpen, onChatOpen])

  const showKeyboardShortcutsHelp = () => {
    const helpModal = document.createElement('div')
    helpModal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-toast'
    helpModal.innerHTML = `
      <div class="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-6 max-w-md w-full mx-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-lia-text-primary">Atalhos de Teclado</h3>
          <button id="close-help" class="text-lia-text-tertiary hover:text-lia-text-secondary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between"><span class="text-lia-text-secondary">Ativar IA Copilot</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">Ctrl+K</kbd></div>
          <div class="flex justify-between"><span class="text-lia-text-secondary">Busca por Voz</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">Ctrl+;</kbd></div>
          <div class="flex justify-between"><span class="text-lia-text-secondary">Biblioteca LIA</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">Ctrl+Shift+L</kbd></div>
          <div class="flex justify-between"><span class="text-lia-text-secondary">Chat com LIA</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">Ctrl+Shift+C</kbd></div>
          <div class="flex justify-between"><span class="text-lia-text-secondary">Fechar Modal</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">Esc</kbd></div>
          <div class="flex justify-between"><span class="text-lia-text-secondary">Esta Ajuda</span><kbd class="px-2 py-1 bg-gray-100 rounded-md text-xs font-mono">F1</kbd></div>
        </div>
      </div>
    `
    document.body.appendChild(helpModal)
    const closeHelp = () => { document.body.removeChild(helpModal) }
    helpModal.querySelector('#close-help')?.addEventListener('click', closeHelp)
    helpModal.addEventListener('click', (e) => { if (e.target === helpModal) closeHelp() })
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { closeHelp(); document.removeEventListener('keydown', handleEscape) }
    }
    document.addEventListener('keydown', handleEscape)
  }
}
