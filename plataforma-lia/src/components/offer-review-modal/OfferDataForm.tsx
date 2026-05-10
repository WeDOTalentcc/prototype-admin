"use client"

import { useCallback } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import type { OfferDraft, OfferDraftUpdate, SalaryWarning } from "@/types/offer"

interface OfferDataFormProps {
  draft: OfferDraft
  isSaving: boolean
  salaryWarnings: SalaryWarning[]
  onChange: (updates: OfferDraftUpdate) => void
}

export function OfferDataForm({ draft, isSaving, salaryWarnings, onChange }: OfferDataFormProps) {
  const handleSalary = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseFloat(e.target.value)
      if (!isNaN(val)) onChange({ offered_salary: val })
    },
    [onChange],
  )

  const handleBonus = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseFloat(e.target.value)
      if (!isNaN(val)) onChange({ offered_bonus_admission: val })
      else onChange({ offered_bonus_admission: undefined })
    },
    [onChange],
  )

  const handleStartDate = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ offered_start_date: e.target.value || undefined })
    },
    [onChange],
  )

  const handleValidity = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseInt(e.target.value)
      if (!isNaN(val) && val >= 1) onChange({ validity_days: val })
    },
    [onChange],
  )

  const handleNotes = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange({ recruiter_notes: e.target.value || undefined })
    },
    [onChange],
  )

  const salaryOverBudget = salaryWarnings.some(w => w.level === "warning")

  return (
    <div className="flex flex-col gap-4 p-4 h-full overflow-y-auto">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Carta-Oferta
      </p>

      {/* Salary warnings */}
      {salaryWarnings.map((w, i) => (
        <div
          key={i}
          className={`text-xs px-3 py-2 rounded-md ${
            w.level === "warning"
              ? "bg-yellow-50 text-yellow-800 border border-yellow-200"
              : "bg-blue-50 text-blue-800 border border-blue-200"
          }`}
        >
          {w.message}
        </div>
      ))}

      {/* Salary */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="offer-salary" className="text-xs text-muted-foreground">
          Salário (R$) *
        </Label>
        <Input
          id="offer-salary"
          type="number"
          min={0}
          step={100}
          value={draft.offered_salary ?? ""}
          onChange={handleSalary}
          disabled={isSaving}
          placeholder="Ex: 10000"
          className="h-9"
          aria-invalid={salaryOverBudget}
        />
      </div>

      {/* Bonus */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="offer-bonus" className="text-xs text-muted-foreground">
          Bônus de admissão (R$)
        </Label>
        <Input
          id="offer-bonus"
          type="number"
          min={0}
          step={100}
          value={draft.offered_bonus_admission ?? ""}
          onChange={handleBonus}
          disabled={isSaving}
          placeholder="Opcional"
          className="h-9"
        />
      </div>

      {/* Start date */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="offer-start" className="text-xs text-muted-foreground">
          Data de início
        </Label>
        <Input
          id="offer-start"
          type="date"
          value={draft.offered_start_date ?? ""}
          onChange={handleStartDate}
          disabled={isSaving}
          className="h-9"
        />
      </div>

      {/* Validity */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="offer-validity" className="text-xs text-muted-foreground">
          Validade (dias)
        </Label>
        <Input
          id="offer-validity"
          type="number"
          min={1}
          max={90}
          value={draft.validity_days ?? 7}
          onChange={handleValidity}
          disabled={isSaving}
          className="h-9 w-24"
        />
      </div>

      {/* Notes */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="offer-notes" className="text-xs text-muted-foreground">
          Notas internas (não enviadas ao candidato)
        </Label>
        <Textarea
          id="offer-notes"
          value={draft.recruiter_notes ?? ""}
          onChange={handleNotes}
          disabled={isSaving}
          placeholder="Observações para você mesmo..."
          className="resize-none h-20 text-sm"
        />
      </div>

      {isSaving && (
        <p className="text-xs text-muted-foreground animate-pulse">Salvando...</p>
      )}
    </div>
  )
}
