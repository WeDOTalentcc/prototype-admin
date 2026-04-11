'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { maskCPF, maskCNPJ, maskPhone, maskCEP, maskCurrency } from '@/lib/masks'

type MaskType = 'cpf' | 'cnpj' | 'phone' | 'cep' | 'currency' | 'none'

const MASK_FN: Record<MaskType, (v: string) => string> = {
  cpf: maskCPF,
  cnpj: maskCNPJ,
  phone: maskPhone,
  cep: maskCEP,
  currency: maskCurrency,
  none: (v) => v,
}

interface MaskedInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  mask: MaskType
  onChange?: (value: string, maskedValue: string) => void
  error?: string
  label?: string
}

const MaskedInput = React.forwardRef<HTMLInputElement, MaskedInputProps>(
  ({ mask, onChange, error, label, className, id, ...props }, ref) => {
    const inputId = id || `masked-${mask}-${Math.random().toString(36).slice(2)}`
    const errorId = `${inputId}-error`

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value
      const masked = MASK_FN[mask](raw)
      // Atualiza o valor visual
      e.target.value = masked
      onChange?.(raw.replace(/\D/g, ''), masked)
    }

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-lia-text-primary">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          onChange={handleChange}
          className={cn(
            'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm',
            'shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium',
            'placeholder:text-lia-text-tertiary focus-visible:outline-none focus-visible:ring-1',
            'focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
          {...props}
        />
        {error && (
          <p id={errorId} role="alert" className="text-xs text-red-500 flex items-center gap-1">
            <span aria-hidden="true">⚠</span>
            {error}
          </p>
        )}
      </div>
    )
  }
)
MaskedInput.displayName = 'MaskedInput'

export { MaskedInput, type MaskedInputProps, type MaskType }
