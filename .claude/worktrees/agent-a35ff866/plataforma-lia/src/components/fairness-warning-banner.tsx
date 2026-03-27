'use client'

/**
 * FairnessWarningBanner — FAR-2/C
 *
 * Exibe soft warnings de viés implícito detectados pelo FairnessGuard Layer 2.
 * Aparece no float chat quando o agente detecta linguagem potencialmente tendenciosa
 * mas não bloqueante (ex: "bairros nobres", "zona rural", "disponibilidade total").
 *
 * Compatível com Vue/Nuxt: props mapeiam para defineProps(), onDismiss → emit('dismiss').
 */

import { AlertTriangle, X } from 'lucide-react'

interface Props {
  warnings: string[]
  onDismiss: () => void
}

export function FairnessWarningBanner({ warnings, onDismiss }: Props) {
  if (warnings.length === 0) return null

  return (
    <div className="mx-3 mb-2 rounded-md border border-amber-200 bg-amber-50 p-3">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-amber-800 mb-1">
            Atenção: possível viés implícito detectado
          </p>
          <ul className="space-y-0.5">
            {warnings.map((warning, i) => (
              <li key={i} className="text-xs text-amber-700 leading-snug">
                • {warning}
              </li>
            ))}
          </ul>
        </div>
        <button
          onClick={onDismiss}
          aria-label="Dispensar aviso de viés"
          className="shrink-0 rounded p-0.5 text-amber-500 hover:bg-amber-100 hover:text-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
