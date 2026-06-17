"use client"

import { CreditCard, FileText, Settings } from "lucide-react"
import { Chip } from "@/components/ui/chip"

function ComingSoonSection({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType
  title: string
  description: string
}) {
  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-lia-bg-tertiary p-2 mt-0.5 flex-shrink-0">
            <Icon className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-medium text-lia-text-primary">{title}</p>
            <p className="text-xs text-lia-text-tertiary mt-0.5">{description}</p>
          </div>
        </div>
        <Chip variant="neutral" muted className="text-[10px] flex-shrink-0">
          Em breve
        </Chip>
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-3 rounded-md bg-lia-bg-tertiary w-3/4" />
        <div className="h-3 rounded-md bg-lia-bg-tertiary w-1/2" />
      </div>
    </div>
  )
}

export function BillingTab() {
  return (
    <div className="space-y-3 max-w-2xl">
      <ComingSoonSection
        icon={CreditCard}
        title="Plano atual"
        description="Detalhes do plano contratado, limites e data de renovação."
      />
      <ComingSoonSection
        icon={FileText}
        title="Histórico de faturas"
        description="Faturas emitidas, valores e status de pagamento."
      />
      <ComingSoonSection
        icon={Settings}
        title="Método de pagamento"
        description="Cartão cadastrado e configurações de cobrança."
      />
    </div>
  )
}
