"use client"

/**
 * QuickRepliesDemo — P2-2 Sprint B.5 standalone preview.
 *
 * Monta o componente QuickReplies em isolamento pra preview/QA visual,
 * sem tocar no chat panel renderer (que fica deferred pra próxima sprint).
 *
 * Uso típico: rota interna de QA ou storybook-like preview.
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.5
 */

import { useState } from "react"
import { QuickReplies, type QuickReplyPreset } from "@/components/onboarding/QuickReplies"

const PRESETS: QuickReplyPreset[] = [
  "boolean",
  "work_model",
  "autonomy",
  "channel",
  "experience_policy",
  "ai_tone",
]

export function QuickRepliesDemo() {
  const [lastSelection, setLastSelection] = useState<{
    preset: QuickReplyPreset
    value: string
  } | null>(null)

  return (
    <div className="space-y-6 p-6">
      <header>
        <h2 className="text-lg font-semibold">QuickReplies — Preview</h2>
        <p className="text-sm text-lia-text-secondary">
          Preview standalone de cada preset. Selecione um botão pra ver o valor.
        </p>
      </header>

      {lastSelection && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-md border border-wedo-cyan/30 bg-wedo-cyan/5 px-3 py-2 text-sm"
        >
          Último: <code>{lastSelection.preset}</code> →{" "}
          <code>{lastSelection.value}</code>
        </div>
      )}

      <div className="space-y-4">
        {PRESETS.map((preset) => (
          <section key={preset} className="space-y-2">
            <h3 className="text-sm font-medium uppercase tracking-tight text-lia-text-secondary">
              {preset}
            </h3>
            <QuickReplies
              preset={preset}
              onSelect={(value) => setLastSelection({ preset, value })}
            />
          </section>
        ))}
      </div>
    </div>
  )
}
