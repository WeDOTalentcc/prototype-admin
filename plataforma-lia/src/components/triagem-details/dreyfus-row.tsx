"use client"

import { dreyfusLabel } from "./useTriagemDetailsState"

interface DreyfusRowProps {
  dreyfusEsperado: number
  dreyfusDemonstrado: number
  senioridade?: string
}

export function DreyfusRow({ dreyfusEsperado, dreyfusDemonstrado, senioridade }: DreyfusRowProps) {
  const delta = dreyfusDemonstrado - dreyfusEsperado
  const isCritical = delta <= -2
  const isAtencao  = delta === -1
  const isAcima    = delta > 0
  const color = isCritical ? "text-status-error" : isAtencao ? "text-status-warning" : isAcima ? "text-wedo-cyan-text" : "text-status-success"
  const bg    = isCritical ? "bg-status-error/10 border-status-error/30" : isAtencao ? "bg-status-warning/10 border-status-warning/30" : isAcima ? "bg-wedo-cyan/10 border-wedo-cyan/30" : "bg-status-success/10 border-status-success/30"
  const lbl   = isCritical ? "Gap crítico" : isAtencao ? "Atenção" : isAcima ? "Acima" : "Alinhado"
  return (
    <div className={`flex items-center justify-between text-micro rounded-md border px-2.5 py-1.5 mt-1 ${bg}`}>
      <span className="lia-text-secondary">Maturidade comportamental</span>
      <div className="flex items-center gap-2">
        <span className="lia-text-secondary">
          Esperado{senioridade ? ` para ${senioridade}` : ""}: <span className="font-medium text-lia-text-secondary">{dreyfusLabel(dreyfusEsperado)}</span>
        </span>
        <span className="lia-text-muted">·</span>
        <span className="lia-text-secondary">
          Demonstrado: <span className={`font-semibold ${color}`}>{dreyfusLabel(dreyfusDemonstrado)}</span>
        </span>
        <span className={`text-micro font-bold px-1.5 py-0.5 rounded-full border ${bg} ${color}`}>{lbl}</span>
      </div>
    </div>
  )
}
