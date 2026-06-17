"use client"

import React, { useState, useEffect } from "react"
import { Sparkles } from "lucide-react"

/**
 * OnboardingSettingsToggle — toggle LIA onboarding on/off.
 *
 * Place inside: settings/RecruitmentHub.tsx or HiringPoliciesHub.tsx
 * Follows existing toggle pattern from HiringPoliciesHub.
 */

interface Props {
  accountId: number
}

export function OnboardingSettingsToggle({ accountId }: Props) {
  const [enabled, setEnabled] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Load current setting
    fetch("/api/backend-proxy/onboarding/settings", { credentials: "include" })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.onboarding_lia_enabled != null) {
          setEnabled(data.onboarding_lia_enabled)
        }
      })
      .catch(() => {})
  }, [])

  const handleToggle = async () => {
    const newValue = !enabled
    setSaving(true)
    try {
      await fetch("/api/backend-proxy/onboarding/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ onboarding_lia_enabled: newValue }),
        credentials: "include",
      })
      setEnabled(newValue)
    } catch { /* ignore */ }
    setSaving(false)
  }

  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-lia-border-subtle bg-lia-bg-primary">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-wedo-cyan/10 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-wedo-cyan" />
        </div>
        <div>
          <p className="text-sm font-medium text-lia-text-primary font-['Open_Sans',sans-serif]">
            Onboarding com LIA
          </p>
          <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
            Novos recrutadores recebem apresentacao conversacional da LIA via WhatsApp e chat
          </p>
        </div>
      </div>

      <button
        onClick={handleToggle}
        disabled={saving}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          enabled ? "bg-wedo-cyan" : "bg-lia-bg-tertiary"
        } ${saving ? "opacity-50" : ""}`}
        role="switch"
        aria-checked={enabled}
        aria-label="Ativar onboarding com LIA"
      >
        <span
          className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
            enabled ? "left-[22px]" : "left-0.5"
          }`}
        />
      </button>
    </div>
  )
}
