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
    <div className="mx-3 mb-2 rounded-md border border-status-warning/30 bg-status-warning/10 p-3">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-status-warning" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-status-warning mb-1">
            Atenção: possível viés implícito detectado
          </p>
          <ul className="space-y-0.5">
            {warnings.map((warning, i) => (
              <li key={i} className="text-xs text-status-warning leading-snug">
                • {warning}
              </li>
            ))}
          </ul>
        </div>
        <button
          onClick={onDismiss}
          aria-label="Dispensar aviso de viés"
          className="shrink-0 rounded p-0.5 text-status-warning hover:bg-status-warning/15 hover:text-status-warning focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
