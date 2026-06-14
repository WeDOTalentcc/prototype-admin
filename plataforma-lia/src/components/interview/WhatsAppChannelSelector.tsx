"use client"

/**
 * WhatsAppChannelSelector — phone capture and WhatsApp screening initiation.
 *
 * Used by InterviewLobby when candidate picks the WhatsApp channel.
 * Flow:
 *   1. If existingPhone is provided: show masked number + confirm / use other.
 *   2. If not: show BR phone input, validate, POST to save-phone + start-whatsapp.
 *   3. On success: show confirmation with deep-link to WhatsApp.
 *
 * Rules of Hooks: ALL hooks at top before any conditional return.
 * Design tokens only — no hardcoded colors or spacing.
 *
 * Phase 1a LGPD Consent (2026-06-11).
 */

import React, { useCallback, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { CheckCircle, ArrowLeft, Smartphone } from "lucide-react"
import { cn } from "@/lib/utils"

// ── BR phone E.164 pattern ────────────────────────────────────────────────────
const E164_BR_PATTERN = /^\+55\d{10,11}$/

/** Strip non-digits and normalise to E.164 (+55...) if possible. */
function normalisePhone(raw: string): string | null {
  const digits = raw.replace(/\D/g, "")
  let e164 = raw.trim()
  if (!e164.startsWith("+")) {
    if (digits.length === 10 || digits.length === 11) {
      e164 = `+55${digits}`
    } else if (digits.length === 12 || digits.length === 13) {
      e164 = `+${digits}`
    } else {
      return null
    }
  }
  return E164_BR_PATTERN.test(e164) ? e164 : null
}

/** Mask phone for display: +55 11 9●●●●-5678 */
function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, "")
  if (digits.length >= 12) {
    // international: e.g. 5511987651234
    const country = digits.slice(0, 2)  // 55
    const ddd = digits.slice(2, 4)       // 11
    const rest = digits.slice(4)
    const masked = rest.slice(0, 1) + "●●●●" + rest.slice(-4)
    return `+${country} (${ddd}) ${masked}`
  }
  // fallback
  return phone.slice(0, 4) + "●●●●" + phone.slice(-4)
}

// ── Component ─────────────────────────────────────────────────────────────────

export interface WhatsAppChannelSelectorProps {
  /** Session token — used for proxy calls. */
  token: string
  /** Candidate's phone already on file (from session). null if unknown. */
  existingPhone?: string | null
  /** Called when WhatsApp flow is successfully initiated. */
  onSuccess: () => void
  /** Called when user clicks "back". */
  onBack: () => void
  className?: string
}

type Step = "confirm_existing" | "enter_phone" | "sending" | "done" | "error"

export function WhatsAppChannelSelector({
  token,
  existingPhone,
  onSuccess,
  onBack,
  className,
}: WhatsAppChannelSelectorProps) {
  // ── All hooks at top — Rules of Hooks canonical ──────────────────────────
  const initialStep: Step = existingPhone ? "confirm_existing" : "enter_phone"
  const [step, setStep] = useState<Step>(initialStep)
  const [phoneInput, setPhoneInput] = useState("")
  const [phoneError, setPhoneError] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resolvedPhone, setResolvedPhone] = useState<string | null>(existingPhone ?? null)

  const startWhatsApp = useCallback(
    async (phone: string) => {
      setStep("sending")
      setErrorMessage(null)
      try {
        const res = await fetch(
          `/api/backend-proxy/interview/${token}/start-whatsapp`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate_phone: phone }),
          }
        )
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(
            (body as Record<string, unknown>)["detail"] as string ||
              "Não foi possível enviar. Tente novamente."
          )
        }
        setResolvedPhone(phone)
        setStep("done")
        // Notify parent after short delay so user sees confirmation
        setTimeout(() => onSuccess(), 4000)
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "Erro inesperado.")
        setStep("error")
      }
    },
    [token, onSuccess]
  )

  const handleConfirmExisting = useCallback(() => {
    if (existingPhone) {
      void startWhatsApp(existingPhone)
    }
  }, [existingPhone, startWhatsApp])

  const handleUseOtherPhone = useCallback(() => {
    setStep("enter_phone")
    setPhoneInput("")
    setPhoneError(null)
  }, [])

  const handleSubmitPhone = useCallback(() => {
    const normalised = normalisePhone(phoneInput)
    if (!normalised) {
      setPhoneError(
        "Telefone inválido. Use formato (DDD) + número, ex: (11) 99999-9999"
      )
      return
    }
    setPhoneError(null)
    void startWhatsApp(normalised)
  }, [phoneInput, startWhatsApp])

  const handleRetry = useCallback(() => {
    setStep(existingPhone ? "confirm_existing" : "enter_phone")
    setErrorMessage(null)
  }, [existingPhone])

  // ── Render ────────────────────────────────────────────────────────────────

  const waLink = resolvedPhone
    ? `https://wa.me/${resolvedPhone.replace(/\D/g, "")}`
    : "https://wa.me"

  return (
    <div className={cn("flex flex-col gap-6 p-4", className)}>
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="text-lia-text-secondary hover:text-lia-text-primary transition-colors"
          aria-label="Voltar"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <Smartphone className="w-5 h-5 text-lia-primary" />
          <h2 className="text-base font-semibold text-lia-text-primary">
            Triagem via WhatsApp
          </h2>
        </div>
      </div>

      {/* Step: Confirm existing phone */}
      {step === "confirm_existing" && existingPhone && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-lia-text-secondary">
            Enviaremos a triagem para o número cadastrado:
          </p>
          <div className="rounded-lg border border-lia-border bg-lia-surface-subtle px-4 py-3 font-mono text-sm text-lia-text-primary">
            {maskPhone(existingPhone)}
          </div>
          <div className="flex flex-col gap-2">
            <Button
              onClick={handleConfirmExisting}
              className="w-full"
              variant="primary"
            >
              Confirmar e enviar
            </Button>
            <Button
              onClick={handleUseOtherPhone}
              variant="ghost"
              className="w-full text-lia-text-secondary"
            >
              Usar outro número
            </Button>
          </div>
        </div>
      )}

      {/* Step: Enter phone */}
      {step === "enter_phone" && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-lia-text-secondary">
            Informe seu número de WhatsApp para receber a triagem:
          </p>
          <div className="flex flex-col gap-1">
            <Input
              type="tel"
              placeholder="(11) 99999-9999"
              value={phoneInput}
              onChange={(e) => {
                setPhoneInput(e.target.value)
                if (phoneError) setPhoneError(null)
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSubmitPhone()
              }}
              aria-label="Número de WhatsApp"
              aria-invalid={phoneError != null}
              aria-describedby={phoneError ? "phone-error" : undefined}
              className={cn(phoneError && "border-lia-error")}
              autoFocus
            />
            {phoneError && (
              <p id="phone-error" className="text-xs text-lia-error" role="alert">
                {phoneError}
              </p>
            )}
          </div>
          <Button onClick={handleSubmitPhone} className="w-full" variant="primary">
            Enviar para este número
          </Button>
        </div>
      )}

      {/* Step: Sending */}
      {step === "sending" && (
        <div className="flex flex-col items-center gap-3 py-6">
          <div
            className="h-8 w-8 animate-spin rounded-full border-2 border-lia-primary border-t-transparent"
            role="status"
            aria-label="Enviando"
          />
          <p className="text-sm text-lia-text-secondary">
            Enviando mensagem WhatsApp…
          </p>
        </div>
      )}

      {/* Step: Done */}
      {step === "done" && resolvedPhone && (
        <div className="flex flex-col items-center gap-4 py-4 text-center">
          <CheckCircle className="h-10 w-10 text-lia-success" aria-hidden />
          <p className="text-base font-medium text-lia-text-primary">
            Mensagem enviada!
          </p>
          <p className="text-sm text-lia-text-secondary">
            Enviamos uma mensagem para seu WhatsApp.
            <br />
            Acesse o app para responder e iniciar a triagem.
          </p>
          <a
            href={waLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[#25D366] px-5 py-2 text-sm font-semibold text-white shadow hover:brightness-110 transition-colors"
          >
            <Smartphone className="h-4 w-4" />
            Abrir WhatsApp
          </a>
        </div>
      )}

      {/* Step: Error */}
      {step === "error" && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-lia-error" role="alert">
            {errorMessage ?? "Ocorreu um erro. Tente novamente."}
          </p>
          <div className="flex flex-col gap-2">
            <Button onClick={handleRetry} variant="primary" className="w-full">
              Tentar novamente
            </Button>
            <Button
              onClick={onBack}
              variant="ghost"
              className="w-full text-lia-text-secondary"
            >
              Voltar
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
