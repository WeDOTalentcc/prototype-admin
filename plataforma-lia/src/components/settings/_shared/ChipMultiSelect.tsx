/**
 * ChipMultiSelect — chips toggleáveis para arrays de string.
 *
 * Componente canonical extraído de BenefitFormModal + CompensationPolicyFormModal.
 * Single source of truth para seleção múltipla via chips.
 *
 * Extração: 2026-05-26 (canonical-fix DRY enforcement).
 * Dois consumers antes: BenefitFormModal, CompensationPolicyFormModal (inline duplicados).
 */

interface ChipMultiSelectProps {
  options: readonly { id: string; label: string }[]
  /** IDs selecionados */
  value: string[]
  onChange: (next: string[]) => void
  /** Acessibilidade: aria-label do grupo */
  ariaLabel?: string
  /** Habilita lógica "all" — selecionar "all" deseleciona os demais */
  allOptionId?: string
}

export function ChipMultiSelect({
  options,
  value,
  onChange,
  ariaLabel,
  allOptionId,
}: ChipMultiSelectProps) {
  const toggle = (id: string) => {
    if (value.includes(id)) {
      onChange(value.filter((s) => s !== id))
    } else if (allOptionId && id === allOptionId) {
      onChange([allOptionId])
    } else {
      const next = allOptionId
        ? [...value.filter((s) => s !== allOptionId), id]
        : [...value, id]
      onChange(next)
    }
  }

  return (
    <div
      className="flex flex-wrap gap-2"
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((opt) => {
        const isSel = value.includes(opt.id)
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => toggle(opt.id)}
            aria-pressed={isSel}
            className={[
              "rounded-full border px-3 py-1 text-xs transition-all",
              isSel
                ? "border-wedo-cyan bg-wedo-cyan/10 text-wedo-cyan-text"
                : "border-lia-border-default bg-lia-bg-elevated text-lia-text-secondary hover:border-wedo-cyan/50",
            ].join(" ")}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
