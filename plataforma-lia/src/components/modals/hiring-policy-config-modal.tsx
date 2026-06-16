"use client"

/**
 * Fase 1 Nível 1 — B3b (2026-06-09): HiringPolicyConfigModal
 *
 * Abre as configurações de personalização da LIA (Persona + Instruções por Campo +
 * Learning Loops) em um Dialog, evitando navegação full-page quando acionado
 * pelo chat via open_ui tool (modal_id=hiring_policy_config).
 *
 * Wraps LiaPersonalizacaoHub lazy-loaded para não inflacionar o bundle do host.
 * O usuário pode fechar o Dialog a qualquer momento sem perder o contexto do chat.
 */
import dynamic from "next/dynamic"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Settings2 } from "lucide-react"

const LiaPersonalizacaoHub = dynamic(
  () =>
    import("@/components/settings/LiaPersonalizacaoHub").then(
      (m) => ({ default: m.LiaPersonalizacaoHub }),
    ),
  { ssr: false, loading: () => null },
)

interface HiringPolicyConfigModalProps {
  isOpen: boolean
  onClose: () => void
}

export function HiringPolicyConfigModal({ isOpen, onClose }: HiringPolicyConfigModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="max-w-3xl max-h-[90vh] overflow-y-auto bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
        data-testid="hiring-policy-config-modal"
      >
        <DialogHeader className="pb-4 border-b border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
              <Settings2 className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <DialogTitle className="text-sm font-semibold text-lia-text-primary">
              Configurações de IA
            </DialogTitle>
          </div>
        </DialogHeader>
        <div className="pt-4">
          <LiaPersonalizacaoHub />
        </div>
      </DialogContent>
    </Dialog>
  )
}
