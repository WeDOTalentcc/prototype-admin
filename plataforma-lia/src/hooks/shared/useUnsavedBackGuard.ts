import { useEffect } from "react"
import { useNavGuardStore } from "@/stores/nav-guard-store"

/**
 * Guarda o botao "voltar" do browser (popstate) quando ha alteracoes nao
 * salvas. Complementa useUnsavedChanges (beforeunload: fechar/recarregar) e o
 * nav-guard-store (navegacao in-app via handleNavigate). So roda quando
 * `active` — zero impacto na navegacao normal do app quando nao ha pendencia.
 *
 * Mecanica: ao ativar, empurra UM sentinel no history. Quando o usuario aperta
 * voltar, o popstate dispara; re-empurramos um sentinel (o usuario PERMANECE na
 * pagina) e roteamos pelo nav-guard-store.requestLeave, que abre o MESMO modal
 * de confirmacao usado pela navegacao in-app. Confirmar -> proceed() faz
 * history.go(-2), pulando os dois niveis de sentinel ate a entrada real
 * anterior. Invariante mantida a cada back: a pilha fica sempre
 * [prev, page, sentinel] na posicao do sentinel, entao go(-2) sempre chega em
 * `prev`. (pushState apos um back descarta as entradas "forward", mantendo a
 * invariante mesmo com multiplos backs.)
 */
export function useUnsavedBackGuard(active: boolean) {
  const requestLeave = useNavGuardStore((s) => s.requestLeave)

  useEffect(() => {
    if (!active) return

    // Sentinel inicial: garante que o primeiro "voltar" dispare popstate
    // sobre esta pagina, em vez de sair direto.
    window.history.pushState({ navGuard: true }, "")

    const onPopState = () => {
      // Usuario apertou voltar. Re-empurra o sentinel (mantem na pagina) e
      // roteia pelo guard -> abre o modal de confirmacao.
      window.history.pushState({ navGuard: true }, "")
      requestLeave(() => {
        // Confirmado: pula os dois sentinels ate a entrada real anterior.
        window.history.go(-2)
      })
    }

    window.addEventListener("popstate", onPopState)
    return () => window.removeEventListener("popstate", onPopState)
  }, [active, requestLeave])
}
