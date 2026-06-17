/**
 * Centralised handler for HTTP 402 Payment Required responses.
 *
 * Called from API utilities and key service methods when the backend
 * returns 402 (trial expired or plan limit reached).
 * Redirects the user to /upgrade and returns a structured error so
 * the caller can bail out cleanly.
 */

export interface PaymentRequiredError {
  code: string
  message: string
  upgrade_url: string
}

export function isPaymentRequired(status: number): boolean {
  return status === 402
}

/**
 * Parse the 402 body and redirect to /upgrade.
 * Returns the error payload so callers can surface it in the UI if needed.
 */
export async function handlePaymentRequired(response: Response): Promise<never> {
  let detail: PaymentRequiredError = {
    code: "PAYMENT_REQUIRED",
    message: "Seu acesso expirou. Faça upgrade para continuar.",
    upgrade_url: "/upgrade",
  }

  try {
    const body = await response.json()
    if (body?.detail) {
      detail = { ...detail, ...body.detail }
    }
  } catch {
    // ignore parse errors — use defaults
  }

  if (typeof window !== "undefined") {
    const safeUrl = detail.upgrade_url.startsWith("/") ? detail.upgrade_url : "/upgrade"
    window.location.href = safeUrl
  }

  throw new Error(detail.message)
}

/**
 * Wraps a fetch Response: throws on 402 (with redirect), otherwise returns as-is.
 * Use in API service methods around critical endpoints (job creation, etc.).
 *
 * Usage:
 *   const response = await fetch(url, options)
 *   await checkPaymentRequired(response)
 *   // ... handle normal errors and success
 */
export async function checkPaymentRequired(response: Response): Promise<void> {
  if (isPaymentRequired(response.status)) {
    await handlePaymentRequired(response)
  }
}
