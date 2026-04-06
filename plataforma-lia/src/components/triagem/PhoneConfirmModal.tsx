"use client"

import React, { useState, useCallback } from "react"
import { Phone, X, Loader2 } from "lucide-react"

interface PhoneConfirmModalProps {
  open: boolean
  onClose: () => void
  onConfirm: (phone: string) => void
  isLoading?: boolean
  error?: string | null
}

function formatPhoneInput(raw: string): string {
  const digits = raw.replace(/\D/g, "")
  if (digits.length <= 2) return digits
  if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  if (digits.length <= 11)
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`
}

function toE164(raw: string): string {
  const digits = raw.replace(/\D/g, "")
  if (digits.startsWith("55")) return `+${digits}`
  return `+55${digits}`
}

function isValidBRPhone(raw: string): boolean {
  const digits = raw.replace(/\D/g, "")
  return digits.length === 10 || digits.length === 11
}

export function PhoneConfirmModal({
  open,
  onClose,
  onConfirm,
  isLoading = false,
  error = null,
}: PhoneConfirmModalProps) {
  const [phone, setPhone] = useState("")

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const formatted = formatPhoneInput(e.target.value)
      setPhone(formatted)
    },
    []
  )

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (!isValidBRPhone(phone)) return
      onConfirm(toE164(phone))
    },
    [phone, onConfirm]
  )

  if (!open) return null

  const valid = isValidBRPhone(phone)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Solicitar ligação"
    >
      <div className="w-full max-w-sm bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl shadow-lia-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
            Receber Ligação
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="p-1 rounded-md text-lia-text-tertiary hover:text-lia-text-primary transition-colors"
            aria-label="Fechar"
            data-dismiss="true"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-lia-text-secondary font-['Open_Sans',sans-serif] leading-relaxed">
          Informe seu telefone para receber uma ligação da LIA. A triagem sera conduzida por voz.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="phone-input"
              className="block text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif] mb-1.5"
            >
              Telefone (com DDD)
            </label>
            <div className="flex items-center gap-2 px-3 py-2.5 border border-lia-border-subtle rounded-lg bg-lia-bg-primary dark:bg-lia-bg-elevated focus-within:ring-2 focus-within:ring-lia-btn-primary-bg/20">
              <Phone className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
              <input
                id="phone-input"
                type="tel"
                value={phone}
                onChange={handleChange}
                placeholder="(11) 99999-9999"
                autoFocus
                disabled={isLoading}
                className="flex-1 bg-transparent text-sm text-lia-text-primary placeholder:text-lia-text-disabled outline-none font-['Inter',sans-serif]"
                maxLength={16}
              />
            </div>
          </div>

          {error && (
            <p className="text-xs text-status-error font-['Open_Sans',sans-serif]">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!valid || isLoading}
            className="w-full h-11 flex items-center justify-center gap-2 rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text text-sm font-medium hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-['Open_Sans',sans-serif]"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Ligando...
              </>
            ) : (
              <>
                <Phone className="w-4 h-4" />
                Solicitar Ligação
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
