import { create } from "zustand"

// Guard de navegacao para mudancas nao-salvas em rota (estilo useBlocker do
// react-router). NAO persistido — guarda uma funcao `proceed`. A pagina ativa
// (ex.: Funil de Talentos com candidatos globais nao salvos) registra `active`
// via setActive. O handler central de navegacao (dashboard-app handleNavigate)
// consulta `active`; se true, chama requestLeave(proceed) em vez de navegar.
// A pagina reage a `pendingProceed` mostrando seu modal de confirmacao e chama
// proceed() (ou clear()) conforme a escolha do usuario.
interface NavGuardState {
  active: boolean
  pendingProceed: (() => void) | null
  setActive: (v: boolean) => void
  requestLeave: (proceed: () => void) => void
  clear: () => void
}

export const useNavGuardStore = create<NavGuardState>((set) => ({
  active: false,
  pendingProceed: null,
  setActive: (v) => set({ active: v }),
  requestLeave: (proceed) => set({ pendingProceed: proceed }),
  clear: () => set({ pendingProceed: null }),
}))
