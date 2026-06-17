"use client"

/**
 * AllowedStartDaysPicker — seleciona os dias do mês permitidos para início de contrato.
 *
 * Primitive purely presentational + controlled. Sem hooks, sem fetch.
 * Regra settings _shared/REGRA 6: apenas props + JSX + className.
 *
 * Dias 29-31 excluídos: fevereiro tem apenas 28 dias — seria impossível agendar
 * start_date em meses curtos se 29/30/31 fossem permitidos.
 */

interface AllowedStartDaysPickerProps {
  value: number[]
  onChange: (days: number[]) => void
  disabled?: boolean
}

export function AllowedStartDaysPicker({ value, onChange, disabled }: AllowedStartDaysPickerProps) {
  const selected = new Set(value)

  function toggle(day: number) {
    if (disabled) return
    const next = new Set(selected)
    if (next.has(day)) {
      next.delete(day)
    } else {
      next.add(day)
    }
    onChange(Array.from(next).sort((a, b) => a - b))
  }

  return (
    <div className="flex flex-wrap gap-1.5" aria-label="Dias de início permitidos">
      {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => {
        const isSelected = selected.has(day)
        return (
          <button
            key={day}
            type="button"
            onClick={() => toggle(day)}
            disabled={disabled}
            aria-pressed={isSelected}
            aria-label={`Dia ${day}${isSelected ? " (selecionado)" : ""}`}
            className={[
              "w-8 h-8 rounded-md text-xs font-medium transition-colors",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-lia-primary",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              isSelected
                ? "bg-lia-primary text-white"
                : "bg-lia-surface-secondary text-lia-text-secondary hover:bg-lia-surface-tertiary",
            ].join(" ")}
          >
            {day}
          </button>
        )
      })}
    </div>
  )
}
