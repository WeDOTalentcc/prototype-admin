import { useEffect } from "react"

/**
 * Avisa o usuario ao tentar sair com alteracoes nao salvas.
 *
 * Uso:
 *   const { isDirty } = useForm()
 *   useUnsavedChanges(isDirty)
 *
 * Nota: O browser moderno ignora a mensagem customizada e exibe a sua propria.
 * O comportamento de bloquear a navegacao ainda funciona corretamente.
 */
export function useUnsavedChanges(hasChanges: boolean) {
  useEffect(() => {
    if (!hasChanges) return

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = "Voce tem alteracoes nao salvas. Deseja sair mesmo assim?"
    }

    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [hasChanges])
}
