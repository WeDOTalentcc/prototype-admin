/**
 * useAudioConsentLog — records LGPD consent for a triagem session.
 *
 * Calls POST /api/backend-proxy/interview/[token]/consent which proxies to
 * POST /api/v1/interview/{session_token}/consent in lia-agent-system.
 *
 * Fail-closed (RN-04): throws on any failure — never swallows errors.
 * The caller is responsible for showing the user-visible error (e.g. toast).
 *
 * Phase 1a LGPD Consent (2026-06-11).
 */

/** Canonical disclaimer version — bump when the consent text changes. */
export const DISCLAIMER_VERSION = "1.0.0"

export interface ConsentLogResult {
  ok: boolean
  consent_id: string
}

export function useAudioConsentLog(token: string) {
  async function logConsent(
    canal: "chat_web" | "whatsapp" | "chamada_online" | "chamada_telefonica",
    consentType = "ai_screening",
  ): Promise<ConsentLogResult> {
    const response = await fetch(
      `/api/backend-proxy/interview/${encodeURIComponent(token)}/consent`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consent_type: consentType,
          canal,
          versao_disclaimer: DISCLAIMER_VERSION,
          user_agent: typeof navigator !== "undefined" ? navigator.userAgent : null,
        }),
      },
    )

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      // RN-04: fail-closed — throw, never swallow
      throw new Error(
        data?.detail ||
          `Falha ao registrar consentimento (HTTP ${response.status}). Tente novamente.`,
      )
    }

    const data: ConsentLogResult = await response.json()
    return data
  }

  return { logConsent }
}
