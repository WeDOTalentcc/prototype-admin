'use client'

import { CreditCard } from 'lucide-react'

export function BillingTab() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="rounded-full bg-lia-bg-tertiary p-4 mb-4">
        <CreditCard className="h-8 w-8 text-lia-text-disabled" aria-hidden="true" />
      </div>
      <h3 className="text-base font-medium text-lia-text-primary mb-2">Em breve</h3>
      <p className="text-sm text-lia-text-tertiary max-w-sm">
        Histórico de faturas, plano atual e configuração de pagamento estarão disponíveis em breve.
      </p>
    </div>
  )
}
