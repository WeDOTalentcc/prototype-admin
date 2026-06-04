"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"

/**
 * FormField — campo de formulário canônico (Fundação DS).
 *
 * Combina <Label> + controle (Input/Textarea/Select já são `rounded-md`) +
 * hint + mensagem de erro num único wrapper com espaçamento e estados padrão.
 *
 * Resolve o desvio recorrente nos hubs de Configurações: labels sem `htmlFor`,
 * hints/erros com tipografia/cor ad-hoc e ausência de `aria-invalid`/
 * `aria-describedby`.
 *
 * O controle filho recebe automaticamente `id`, `aria-invalid` e
 * `aria-describedby` (quando há hint/erro) via clone — basta passar um único
 * elemento de controle como children.
 *
 * Uso:
 *   <FormField label="Nome da empresa" hint="Como aparece nos relatórios">
 *     <Input placeholder="Ex.: WeDo Talent" />
 *   </FormField>
 *
 *   <FormField label="E-mail" error="E-mail inválido" required>
 *     <Input type="email" />
 *   </FormField>
 */
export interface FormFieldProps {
  /** Texto do label. Renderiza um <Label htmlFor> ligado ao controle. */
  label?: React.ReactNode
  /** Texto auxiliar abaixo do controle (cinza secundário). */
  hint?: React.ReactNode
  /** Mensagem de erro. Quando presente, ativa estados de erro/aria-invalid. */
  error?: React.ReactNode
  /** Marca o campo como obrigatório (asterisco + aria-required no controle). */
  required?: boolean
  /** id explícito do controle. Quando omitido, é gerado via useId(). */
  id?: string
  className?: string
  labelClassName?: string
  children: React.ReactElement
}

export const FormField = React.forwardRef<HTMLDivElement, FormFieldProps>(
  function FormField(
    { label, hint, error, required, id, className, labelClassName, children },
    ref,
  ) {
    const generatedId = React.useId()
    const controlId = id ?? (children.props as { id?: string }).id ?? generatedId
    const hintId = hint ? `${controlId}-hint` : undefined
    const errorId = error ? `${controlId}-error` : undefined
    const describedBy =
      [errorId, hintId].filter(Boolean).join(" ") || undefined

    const control = React.cloneElement(children, {
      id: controlId,
      "aria-invalid": error ? true : (children.props as Record<string, unknown>)["aria-invalid"],
      "aria-describedby":
        [
          describedBy,
          (children.props as Record<string, string | undefined>)["aria-describedby"],
        ]
          .filter(Boolean)
          .join(" ") || undefined,
      "aria-required": required || undefined,
    } as Record<string, unknown>)

    return (
      <div ref={ref} className={cn("space-y-1.5", className)}>
        {label ? (
          <Label
            htmlFor={controlId}
            className={cn("text-lia-text-primary", labelClassName)}
          >
            {label}
            {required ? (
              <span className="ml-0.5 text-status-error" aria-hidden="true">
                *
              </span>
            ) : null}
          </Label>
        ) : null}
        {control}
        {error ? (
          <p id={errorId} className="text-xs text-status-error" role="alert">
            {error}
          </p>
        ) : null}
        {hint && !error ? (
          <p id={hintId} className="text-xs text-lia-text-secondary">
            {hint}
          </p>
        ) : null}
      </div>
    )
  },
)

FormField.displayName = "FormField"

export default FormField
